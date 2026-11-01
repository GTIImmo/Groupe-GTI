"""COUPLES · PHASE 1 (01/11/2026) — LA NATURE DE CHAQUE FICHE, ET LA CIVILITE RENDUE.

Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §1, §3 (T1-T4), §4 étape 2.
Les definitions sont celles de notice/AUDIT_NATURE_DES_FICHES_CONTACT_2026-11-01.md.

CE QUE FAIT CETTE ETAPE : elle remplit la table locale `contact_nature_current` de
phase2.sqlite, une ligne par fiche de `app_contact_current` (meme numero), et RIEN
d'autre. Personne ne lit cette table aujourd'hui : ni le push, ni l'ecran, ni le
worker. Elle n'ecrit ni chez Hektor, ni chez Supabase.

    nature_fiche   T1  personne_seule · couple · conjoint · conjoint_sans_prenom ·
                       case_conjoint_vide · case_vide_orpheline
    couple_deuxieme    pour un couple seulement : conjoint_avec_prenom · nom_recopie ·
                       case_vide · aucune_deuxieme_fiche · aucun_lien
    civilite_app   T2  « Mme. » quand Hektor n'a RIEN et que l'ancien logiciel disait
                       Madame (table `ancien_logiciel_contact`) ; NULL sinon
                       -> l'ecran affichera civilite_app, et a defaut `civilite`
    civilite_source    'ancien_logiciel' quand civilite_app est posee
    suit_principale_archivee  T3  case de conjoint vide, active, dont la principale
                       est archivee (elle suivra sa principale a l'ecran)
    supprimee_chez_hektor     T4  fiche sans agence : supprimee chez Hektor, gardee
                       chez nous parce qu'une annonce ou une offre la cite

⛔ POURQUOI UNE TABLE A PART et pas des colonnes de `app_contact_current` : le push
   des contacts lit cette table en `SELECT *` -- une colonne de plus partirait chez
   Supabase, ou elle n'existe pas, et ferait echouer tout le push. La phase 2 (accord
   requis) creera les colonnes chez Supabase et les ajoutera a l'envoi.
⛔ POURQUOI `civilite` N'EST PAS TOUCHEE (decision « A » du 01/11) : c'est le miroir de
   Hektor, la nuit suivante la remettrait a vide. Une civilite confirmee par un agent
   passe par le chemin normal (saisie -> Hektor) et rend civilite_app inutile : on ne la
   pose que si Hektor n'a RIEN.

⚠ PLACE DANS LE RUN : apres la construction de la couche (elle est videe et remplie
  chaque nuit). Etape NON BLOQUANTE : ratee, la table garde la nuit precedente --
  sans lecteur, rien ne change pour personne.
⚠ PAS DE BATTEMENT pour l'instant : une cle de battement s'enregistre chez Supabase
  (ecriture en production). Elle viendra avec la phase 2.

Usage :
    python phase2/contacts/nature_des_fiches.py            (remplace la table)
    python phase2/contacts/nature_des_fiches.py --a-blanc  (compte, n'ecrit rien)
Sortie : 0 = fait · 1 = echec.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
TABLE = "contact_nature_current"
TABLE_ANCIEN = "ancien_logiciel_contact"

# Les signes d'un couple sur une premiere fiche (audit du 01/11, §1).
CIVILITES_COUPLE = {"Mr./Mme", "M_Mme", "Mme_M", "Mme_Mme", "M_M"}
DEUX_PRENOMS = re.compile(r"(\bet\b|&|/|\+|\bepoux\b|\bm\.? et mme\b)")
DEUX_NOMS = re.compile(r"\b(et|epoux)\b|&")
MADAME_ANCIEN = 2          # `gender` de l'ancien logiciel : 2 = Madame
MADAME_HEKTOR = "Mme."     # la forme que Hektor ecrit (1 514 fiches)


def normaliser(valeur: Any) -> str:
    return unicodedata.normalize("NFKD", str(valeur or "").strip().lower()).encode("ascii", "ignore").decode()


def _texte(valeur: Any) -> str:
    return str(valeur or "").strip()


def nommee(fiche: dict[str, Any]) -> bool:
    return bool(normaliser(fiche.get("nom")) or normaliser(fiche.get("prenom")))


def archivee(fiche: dict[str, Any]) -> bool:
    return _texte(fiche.get("archive")).lower() in {"1", "true"}


def secondes_par_principale(fiches: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    secondes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in fiches.values():
        lien = _texte(f.get("hektor_couple_contact_id"))
        if lien and lien != _texte(f.get("hektor_contact_id")):
            secondes[lien].append(f)
    return secondes


def nature(fiche: dict[str, Any], fiches: dict[str, dict[str, Any]],
           secondes: dict[str, list[dict[str, Any]]]) -> str:
    """La nature d'une fiche. Fonction PURE (elle ne lit que ce qu'on lui donne)."""
    numero = _texte(fiche.get("hektor_contact_id"))
    lien = _texte(fiche.get("hektor_couple_contact_id"))
    if lien and lien != numero:                          # une deuxieme fiche
        if not nommee(fiche):
            return "case_conjoint_vide" if lien in fiches else "case_vide_orpheline"
        return "conjoint" if normaliser(fiche.get("prenom")) else "conjoint_sans_prenom"
    if not nommee(fiche):
        return "case_vide_orpheline"
    signe = (_texte(fiche.get("civilite")) in CIVILITES_COUPLE
             or bool(DEUX_PRENOMS.search(normaliser(fiche.get("prenom"))))
             or bool(DEUX_NOMS.search(normaliser(fiche.get("nom"))))
             or any(normaliser(s.get("prenom")) for s in secondes.get(numero, [])))
    return "couple" if signe else "personne_seule"


def couple_deuxieme(fiche: dict[str, Any], secondes: dict[str, list[dict[str, Any]]]) -> str:
    """Ce qu'est la deuxieme fiche d'un COUPLE (cas a-e de l'audit, §2 et §2 bis)."""
    numero = _texte(fiche.get("hektor_contact_id"))
    if _texte(fiche.get("hektor_couple_contact_id")) != numero:
        return "aucun_lien"                              # e
    siennes = secondes.get(numero, [])
    if any(normaliser(s.get("prenom")) for s in siennes):
        return "conjoint_avec_prenom"                    # a
    if any(nommee(s) for s in siennes):
        return "nom_recopie"                             # b
    if siennes:
        return "case_vide"                               # c
    return "aucune_deuxieme_fiche"                       # d


def madames_de_l_ancien_logiciel(conn: sqlite3.Connection) -> set[str] | None:
    """Les numeros HEKTOR que l'ancien logiciel disait « Madame », sans contradiction.

    None si la table n'a pas ete chargee (charger_ancien_logiciel.py) : on ne rend
    alors aucune civilite, sans echouer.
    """
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE_ANCIEN,)).fetchone():
        return None
    genres: dict[str, set[Any]] = defaultdict(set)
    for hid, genre in conn.execute(f"SELECT hektor_contact_id, gender FROM {TABLE_ANCIEN} "
                                   "WHERE hektor_contact_id IS NOT NULL"):
        genres[str(hid)].add(genre)
    # une fiche Hektor visee par plusieurs anciennes fiches : seulement si TOUTES disent Madame
    return {hid for hid, g in genres.items() if g == {MADAME_ANCIEN}}


def calculer(fiches: dict[str, dict[str, Any]], madames: set[str] | None) -> list[dict[str, Any]]:
    secondes = secondes_par_principale(fiches)
    lignes = []
    for numero, f in fiches.items():
        nat = nature(f, fiches, secondes)
        lien = _texte(f.get("hektor_couple_contact_id"))
        principale = fiches.get(lien) if lien and lien != numero else None
        civilite_app = None
        if (madames is not None and not _texte(f.get("civilite")) and nommee(f)
                and _texte(f.get("hektor_target_id")) in madames):
            civilite_app = MADAME_HEKTOR
        lignes.append({
            "hektor_contact_id": numero,
            "nature_fiche": nat,
            "couple_deuxieme": couple_deuxieme(f, secondes) if nat == "couple" else None,
            "civilite_app": civilite_app,
            "civilite_source": "ancien_logiciel" if civilite_app else None,
            "suit_principale_archivee": int(nat == "case_conjoint_vide" and not archivee(f)
                                            and principale is not None and archivee(principale)),
            "supprimee_chez_hektor": int(not _texte(f.get("hektor_agence_id"))),
        })
    return lignes


COLONNES = ("hektor_contact_id, hektor_target_id, hektor_couple_contact_id, hektor_agence_id, "
            "civilite, nom, prenom, archive, supabase_sync_eligible")


def lire(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    fiches = {_texte(r["hektor_contact_id"]): dict(r) for r in conn.execute(f"SELECT {COLONNES} FROM app_contact_current")}
    conn.row_factory = None
    return fiches


def ecrire(conn: sqlite3.Connection, lignes: list[dict[str, Any]]) -> None:
    """Remplace la table en une seule transaction (idempotente)."""
    calcule_le = datetime.now().isoformat(timespec="seconds")
    with conn:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE}")
        conn.execute(f"""
            CREATE TABLE {TABLE} (
                hektor_contact_id TEXT PRIMARY KEY,
                nature_fiche TEXT NOT NULL,
                couple_deuxieme TEXT,
                civilite_app TEXT,
                civilite_source TEXT,
                suit_principale_archivee INTEGER NOT NULL,
                supprimee_chez_hektor INTEGER NOT NULL,
                calcule_le TEXT NOT NULL
            )""")
        conn.executemany(
            f"INSERT INTO {TABLE} VALUES (:hektor_contact_id, :nature_fiche, :couple_deuxieme, :civilite_app, "
            ":civilite_source, :suit_principale_archivee, :supprimee_chez_hektor, :calcule_le)",
            [{**l, "calcule_le": calcule_le} for l in lignes])


def bilan(fiches: dict[str, dict[str, Any]], lignes: list[dict[str, Any]]) -> list[str]:
    """Les comptes, serveur · actives · dans l'app : ceux de l'audit doivent ressortir."""
    tot, act, app = Counter(), Counter(), Counter()
    for l in lignes:
        f = fiches[l["hektor_contact_id"]]
        cles = [l["nature_fiche"]]
        if l["couple_deuxieme"]:
            cles.append("couple:" + l["couple_deuxieme"])
        if l["civilite_app"]:
            cles.append("T2 civilite Mme rendue")
        if l["suit_principale_archivee"]:
            cles.append("T3 case active, principale archivee")
        if l["supprimee_chez_hektor"]:
            cles.append("T4 supprimee chez Hektor")
        for cle in cles:
            tot[cle] += 1
            if not archivee(f):
                act[cle] += 1
            if _texte(f.get("supabase_sync_eligible")) in {"1", "True", "true"}:
                app[cle] += 1
    return [f"  {cle:40} serveur {tot[cle]:7}  actives {act[cle]:7}  app {app[cle]:6}" for cle in sorted(tot)]


def executer(conn: sqlite3.Connection, a_blanc: bool = False) -> int:
    fiches = lire(conn)
    madames = madames_de_l_ancien_logiciel(conn)
    if madames is None:
        print(f"[nature] table {TABLE_ANCIEN} absente : aucune civilite rendue (charger_ancien_logiciel.py)")
    lignes = calculer(fiches, madames)
    print(f"[nature] {len(lignes)} fiche(s) :")
    for ligne in bilan(fiches, lignes):
        print(ligne)
    if a_blanc:
        print("[nature] A BLANC : rien n'est ecrit")
        return 0
    ecrire(conn, lignes)
    print(f"[nature] table {TABLE} remplie : {len(lignes)} ligne(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase2-db", type=Path, default=DEFAULT_PHASE2_DB)
    ap.add_argument("--a-blanc", action="store_true")
    args = ap.parse_args()
    conn = sqlite3.connect(args.phase2_db, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        return executer(conn, args.a_blanc)
    except Exception as erreur:  # noqa: BLE001
        print(f"[nature] ECHEC : {erreur}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
