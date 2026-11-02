"""COUPLES · P2 (31/10/2026) — LA PREMIERE FICHE CONNAIT SON CONJOINT.

Note : notice/COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md §21 et §23.

LE DEFAUT. L'annuaire est pagine cote serveur : l'ecran ne peut pas regrouper les
deux fiches d'un couple, la seconde peut tomber sur une autre page. Et 621 secondes
fiches NOMMEES ne partent meme pas vers l'app (pas de lien propre, donc pas
eligibles). Seule la nuit connait chaque couple en entier.

CE QUE FAIT CETTE ETAPE, sur la couche locale `app_contact_current` (rien d'autre) :
  1. pose `couple_json` sur chaque PREMIERE fiche (celle qui se designe elle-meme) :
       {"etat": "nomme" | "vide" | "aucun", "autres": n,
        "conjoint": {"id", "hektor_id", "civilite", "prenom", "nom",
                     "telephone", "email", "archive", "envoye"}}
     · « nomme »  : au moins une seconde fiche porte un nom ; on montre la PREMIERE
                    nommee (plus petit numero), `autres` compte les autres
                    secondes fiches (decision de Frederic du 31/10, question 3) ;
     · « vide »   : des secondes fiches, aucune nommee (le conjoint est la premiere) ;
     · « aucun »  : aucune seconde fiche.
  2. marque `couple_role = 'conjoint'` la seconde fiche NOMMEE montree, quand sa
     premiere part vers l'app et n'est pas archivee, et la rend eligible avec la
     raison « conjoint_d_un_contact_envoye ». Les fiches vides gardent leur role
     (« menage_resolu » / « menage_orphelin ») : rien ne change pour elles.
  3. ne touche ni Hektor, ni Supabase. Le push qui suit envoie le resultat.

⛔ INTERRUPTEUR : APP_COUPLE_CONJOINT=1 dans .env. Eteint (par defaut), l'etape ne
   fait RIEN et le push n'envoie pas `couple_json` -- la colonne n'existe chez
   Supabase qu'apres le patch supabase/patch_couple_p2_conjoint_connu_2026-10-31.sql.
   ⚠ ALLUMER APRES LE PATCH, JAMAIS AVANT : sinon le push des contacts echoue.

⚠ PLACE DANS LE RUN : APRES tout ce qui decide l'eligibilite (build, seconde passe,
  perimetre console), AVANT le push des contacts. La couche est videe puis remplie
  chaque nuit par build_contacts_layer : cette etape repart donc d'une page blanche,
  et elle remet d'abord tout a zero (idempotente).
⚠ ETAPE NON BLOQUANTE : si elle echoue, le push envoie des `couple_json` vides et
  l'ecran ne voit pas les conjoints UNE nuit -- genant, pas grave.

Usage :
    python phase2/contacts/conjoints_des_couples.py              (toute la couche)
    python phase2/contacts/conjoints_des_couples.py --a-blanc    (compte, n'ecrit rien)
    python phase2/contacts/conjoints_des_couples.py --contact-id N
        (relecture d'une seule fiche : recalcule SON couple ; ne leve jamais)
Sortie : 0 = fait (ou eteint) · 1 = echec.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

try:  # lancé comme script (run, worker) ou importé comme module (essais)
    from notaires_registre import notaires_hektor
except ImportError:  # pragma: no cover
    from phase2.contacts.notaires_registre import notaires_hektor

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
RAISON = "conjoint_d_un_contact_envoye"
ROLE = "conjoint"


def charger_env() -> None:
    """Le meme .env que le push (meme fonction) : un seul endroit pour l'interrupteur."""
    sys.path.insert(0, str(ROOT / "phase2" / "sync"))
    try:
        from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: E402
        for chemin in DEFAULT_ENV_FILES:
            load_env_file(chemin)
    except Exception:  # noqa: BLE001 -- sans .env, l'interrupteur reste eteint
        pass


def allume() -> bool:
    return (os.environ.get("APP_COUPLE_CONJOINT") or "").strip().lower() in {"1", "on", "true", "oui"}


def _texte(valeur: Any) -> str:
    return str(valeur or "").strip()


def _archive(valeur: Any) -> bool:
    return _texte(valeur).lower() in {"1", "true"}


def _numero(valeur: Any) -> int:
    texte = _texte(valeur)
    return int(texte) if texte.isdigit() else 1 << 62


def _raisons(valeur: Any) -> list[str]:
    try:
        lues = json.loads(valeur or "[]")
    except (TypeError, ValueError):
        return []
    return [r for r in lues if isinstance(r, str)] if isinstance(lues, list) else []


def resumer(premiere: dict[str, Any], secondes: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Le resume d'un couple, et la seconde fiche nommee montree (ou None).

    Fonction PURE : elle ne lit ni n'ecrit rien, c'est elle que les essais visent.
    """
    secondes = sorted(secondes, key=lambda s: _numero(s.get("hektor_contact_id")))
    nommees = [s for s in secondes if _texte(s.get("nom")) or _texte(s.get("prenom"))]
    if not secondes:
        return {"etat": "aucun", "autres": 0, "conjoint": None}, None
    montree = nommees[0] if nommees else secondes[0]
    # Envoyee POUR UNE AUTRE RAISON que la notre : notre propre marque de la veille
    # ne compte pas (sinon l'etape ne serait pas idempotente -- trouve par l'essai).
    envoyee_avant = bool([r for r in _raisons(montree.get("eligibility_reasons_json")) if r != RAISON])
    premiere_envoyee = (_texte(premiere.get("supabase_sync_eligible")) in {"1", "True", "true"}
                        and not _archive(premiere.get("archive")))
    conjoint = {
        "id": _texte(montree.get("hektor_contact_id")),
        "hektor_id": _texte(montree.get("hektor_target_id")) or None,
        "civilite": _texte(montree.get("civilite")) or None,
        "prenom": _texte(montree.get("prenom")) or None,
        "nom": _texte(montree.get("nom")) or None,
        "telephone": _texte(montree.get("phone_primary")) or None,
        "email": _texte(montree.get("email")) or None,
        "archive": _archive(montree.get("archive")),
        "envoye": envoyee_avant or bool(nommees and premiere_envoyee),
    }
    resume = {"etat": "nomme" if nommees else "vide", "autres": len(secondes) - 1, "conjoint": conjoint}
    return resume, (montree if nommees and premiere_envoyee else None)


COLONNES = ("hektor_contact_id, hektor_target_id, hektor_couple_contact_id, civilite, prenom, nom, "
            "phone_primary, email, archive, supabase_sync_eligible, eligibility_reasons_json, couple_role")


def _lire(conn: sqlite3.Connection, couples: Iterable[str] | None) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    if couples is None:
        sql = (f"SELECT {COLONNES} FROM app_contact_current "
               "WHERE NULLIF(TRIM(hektor_couple_contact_id), '') IS NOT NULL")
        return [dict(r) for r in conn.execute(sql)]
    couples = sorted({c for c in couples if c})
    if not couples:
        return []
    marques = ",".join("?" for _ in couples)
    sql = (f"SELECT {COLONNES} FROM app_contact_current "
           f"WHERE CAST(hektor_couple_contact_id AS TEXT) IN ({marques})")
    return [dict(r) for r in conn.execute(sql, couples)]


def calculer(lignes: list[dict[str, Any]], notaires: set[str] | None = None) -> tuple[dict[str, str], set[str]]:
    """{numero de la premiere: couple_json}, {numeros des conjoints a marquer}.

    ⛔ 02/11 (règle de Frédéric) : UNE FICHE NOTAIRE N'EST JAMAIS UN COUPLE. La première fiche d'un notaire
    du registre des ventes (numéro HEKTOR dans `notaires`) n'a ni résumé ni conjoint marqué ; `ecrire`
    remet à zéro ce qui est lu, donc un résumé déjà posé s'efface à la nuit suivante.
    """
    premieres: dict[str, dict[str, Any]] = {}
    secondes: dict[str, list[dict[str, Any]]] = {}
    for ligne in lignes:
        numero = _texte(ligne.get("hektor_contact_id"))
        lien = _texte(ligne.get("hektor_couple_contact_id"))
        if numero == lien:
            premieres[numero] = ligne
        else:
            secondes.setdefault(lien, []).append(ligne)
    resumes: dict[str, str] = {}
    conjoints: set[str] = set()
    for numero, premiere in premieres.items():
        if notaires and _texte(premiere.get("hektor_target_id")) in notaires:
            continue
        resume, montree = resumer(premiere, secondes.get(numero, []))
        resumes[numero] = json.dumps(resume, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if montree is not None:
            conjoints.add(_texte(montree.get("hektor_contact_id")))
    return resumes, conjoints


def ecrire(conn: sqlite3.Connection, lignes: list[dict[str, Any]], resumes: dict[str, str],
           conjoints: set[str]) -> dict[str, int]:
    """Remet a zero CE QUI EST LU, puis pose. Une seule transaction."""
    remis = marques = 0
    with conn:
        for ligne in lignes:
            numero = _texte(ligne.get("hektor_contact_id"))
            raisons = _raisons(ligne.get("eligibility_reasons_json"))
            etait_conjoint = _texte(ligne.get("couple_role")) == ROLE or RAISON in raisons
            if numero in conjoints:
                raisons = [r for r in raisons if r != RAISON] + [RAISON]
                conn.execute(
                    "UPDATE app_contact_current SET couple_role = ?, supabase_sync_eligible = 1, "
                    "eligibility_reasons_json = ? WHERE hektor_contact_id = ?",
                    (ROLE, json.dumps(raisons, ensure_ascii=False), numero))
                marques += 1
            elif etait_conjoint:
                raisons = [r for r in raisons if r != RAISON]
                role = None if _texte(ligne.get("couple_role")) == ROLE else ligne.get("couple_role")
                conn.execute(
                    "UPDATE app_contact_current SET couple_role = ?, supabase_sync_eligible = ?, "
                    "eligibility_reasons_json = ? WHERE hektor_contact_id = ?",
                    (role, int(bool(raisons)), json.dumps(raisons, ensure_ascii=False), numero))
                remis += 1
            conn.execute("UPDATE app_contact_current SET couple_json = ? WHERE hektor_contact_id = ?",
                         (resumes.get(numero), numero))
    return {"conjoints_marques": marques, "conjoints_retires": remis}


def assurer_colonne(conn: sqlite3.Connection) -> None:
    colonnes = {r[1] for r in conn.execute("PRAGMA table_info(app_contact_current)")}
    if "couple_json" not in colonnes:
        conn.execute("ALTER TABLE app_contact_current ADD COLUMN couple_json TEXT")
        conn.commit()


def couple_du_contact(conn: sqlite3.Connection, numero: str) -> str | None:
    ligne = conn.execute("SELECT hektor_couple_contact_id FROM app_contact_current WHERE hektor_contact_id = ?",
                         (numero,)).fetchone()
    return _texte(ligne[0]) or None if ligne else None


def executer(conn: sqlite3.Connection, a_blanc: bool = False, contact_id: str | None = None) -> int:
    assurer_colonne(conn)
    couples = None
    if contact_id:
        couple = couple_du_contact(conn, contact_id)
        if not couple:
            print(f"[conjoints] le contact {contact_id} n'est pas dans un couple : rien a faire")
            return 0
        couples = [couple]
    lignes = _lire(conn, couples)
    notaires = notaires_hektor(conn)
    resumes, conjoints = calculer(lignes, notaires)
    etats: dict[str, int] = {}
    for texte in resumes.values():
        etat = json.loads(texte)["etat"]
        etats[etat] = etats.get(etat, 0) + 1
    print(f"[conjoints] {len(lignes)} fiche(s) de couple lue(s), {len(resumes)} premiere(s) : "
          + ", ".join(f"{k} {v}" for k, v in sorted(etats.items()))
          + f" ; {len(conjoints)} conjoint(s) nomme(s) a envoyer")
    if a_blanc:
        print("[conjoints] A BLANC : rien n'est ecrit")
        return 0
    bilan = ecrire(conn, lignes, resumes, conjoints)
    print(f"[conjoints] ecrit : {bilan['conjoints_marques']} conjoint(s) marque(s), "
          f"{bilan['conjoints_retires']} retire(s), {len(resumes)} resume(s) pose(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase2-db", type=Path, default=DEFAULT_PHASE2_DB)
    ap.add_argument("--a-blanc", action="store_true")
    ap.add_argument("--contact-id")
    args = ap.parse_args()
    charger_env()
    if not allume():
        print("[conjoints] interrupteur APP_COUPLE_CONJOINT eteint : rien a faire")
        return 0
    conn = sqlite3.connect(args.phase2_db, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        return executer(conn, args.a_blanc, (args.contact_id or "").strip() or None)
    except Exception as erreur:  # noqa: BLE001
        print(f"[conjoints] ECHEC : {erreur}", file=sys.stderr)
        # La relecture d'une fiche ne doit JAMAIS echouer a cause du couple :
        # le couple sera recalcule la nuit.
        return 0 if args.contact_id else 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
