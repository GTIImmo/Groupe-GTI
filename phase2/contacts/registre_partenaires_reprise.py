#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LE REGISTRE DES PARTENAIRES, REMPLI DEPUIS CE QUE LE SERVEUR SAIT.          04/11/2026

Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md (§13 syndic lu chaque nuit, §14 registre, §15 cette reprise).

CE QUE FAIT CE SCRIPT (lot 2, pièce 2). Il lit, EN LOCAL :
  - `contact_metier_netty` (phase2.sqlite) : le métier des professionnels de Netty, par NOTRE numéro de contact ;
  - `hektor_diag_contacts_choix` (hektor.sqlite) : les contacts de métier Syndic / Diagnostiqueur chez Hektor ;
  - `hektor_contact_metier` (hektor.sqlite, s'il existe) : le métier lu dans le formulaire des partenaires créés
    chez Hektor depuis la migration (metier_hektor_contacts.py, §16) ;
  - `hektor_annonce_diag_contacts_detail` (hektor.sqlite) : le syndic et le diagnostiqueur posés sur chaque annonce ;
et complète chez Supabase le registre posé le 04/11 (`app_partenaire_metier`, `app_partenaire_lien`).

LES RÈGLES (décisions de Frédéric du 04/11, §6 bis) :
  - rien ne part chez Hektor ; les numéros de Hektor sont traduits en NOS numéros (`hektor_target_id` → `hektor_contact_id`) ;
  - les notaires sont laissés de côté (ils ont leur fiche, 28/10) -- SAUF interrupteur des notaires allumé (voir plus bas) ;
  - un métier n'est AJOUTÉ que s'il manque ; une ligne existante n'est jamais modifiée ; aucun métier n'est retiré par la nuit ;
  - un lien syndic / diagnostiqueur de Hektor est ajouté s'il manque. Si Hektor CHANGE ou RETIRE le syndic d'une annonce
    qu'il vient de relire, le lien d'origine « hektor » est retiré (daté), jamais effacé. Un lien posé dans l'APP n'est
    jamais touché : en cas d'écart, l'app gagne et l'écart est COMPTÉ dans le compte rendu (Q3).
  - (05/11, §23) un contact SUPPRIMÉ depuis l'app (journal `app_console_deleted_contact_log`) n'a plus aucune ligne :
    la suppression les efface (décision « Effacer »), et la nuit ne les recrée jamais.
  - (05/11, §25) un métier RETIRÉ par quelqu'un (à l'écran, `retire_par` rempli) n'est jamais rajouté : le retrait fait foi.

LE NOTAIRE (décision « A » de Frédéric, 04/11 au soir, §17) : il entre au registre comme les autres métiers, de trois
sources — Netty (« notaire »), le formulaire Hektor (code 2) et la table des parties chez Supabase (rôles notaire_vendeur /
notaire_acquereur, source « transactions »). ⛔ Second interrupteur APP_REGISTRE_PARTENAIRES_NOTAIRES : tant qu'il est
éteint, les notaires restent de côté comme avant (le contrôle du métier refuserait « notaire » sans le patch
patch_registre_partenaires_notaire_2026-11-04.sql — et un lot refusé ferait échouer TOUT le lot).

⛔ INTERRUPTEUR APP_REGISTRE_PARTENAIRES (.env) : absent = éteint, rien n'est écrit (le script le dit et sort en 0).
⚠ PAR DÉFAUT À BLANC : rien n'est écrit sans --ecrire.

    python phase2/contacts/registre_partenaires_reprise.py            (compte, n'écrit rien)
    python phase2/contacts/registre_partenaires_reprise.py --ecrire   (écrit, si l'interrupteur est allumé)
Sortie : 0 = fait (ou éteint) · 1 = échec.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE_PHASE2 = RACINE / "phase2" / "phase2.sqlite"
BASE_HEKTOR = RACINE / "data" / "hektor.sqlite"
FICHIERS_ENV = (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env")

# Le métier de Netty (contact_metier_netty.metiers_json) → la liste fermée du registre.
# Notaire : laissé de côté. Lotisseur, gestionnaire : pas de case à eux → « autre ».
METIER_NETTY = {
    "apporteur": "apporteur", "courtier": "courtier", "diagnostiqueur": "diagnostiqueur", "parrain": "parrain",
    "banque": "banque", "administration": "administration", "societe": "societe", "mandataire": "mandataire",
    "investisseur": "investisseur", "agent_immobilier": "agent_immobilier", "technicien": "technicien",
    "marchand_de_biens": "marchand_de_biens", "lotisseur": "autre", "gestionnaire": "autre",
}
LISTE_HEKTOR = {"syndic": "syndic", "diagnostiqueur": "diagnostiqueur"}
# Le métier lu dans le formulaire Hektor (hektor_contact_metier, metier_hektor_contacts.py) → le registre.
# Laissés de côté : 2 Notaire (sa fiche existe), 6 Autre et '' (rien ne dit un métier), 7 Collaborateur (nos salariés),
# 16 « A supprimer ». 3 Confrère = une autre agence → agent immobilier. 21 Lotisseur → autre.
METIER_HEKTOR = {
    "1": "promoteur", "3": "agent_immobilier", "4": "diagnostiqueur", "5": "syndic", "8": "societe", "15": "apporteur",
    "17": "administration", "18": "societe", "19": "banque", "20": "mandataire", "21": "autre", "22": "agent_immobilier",
    "23": "technicien",
}


def charger_env() -> None:
    for chemin in FICHIERS_ENV:
        if not chemin.exists():
            continue
        for ligne in chemin.read_text(encoding="utf-8", errors="ignore").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, valeur = ligne.split("=", 1)
            cle = cle.strip()
            if cle and cle not in os.environ:
                os.environ[cle] = valeur.strip().strip('"').strip("'")


def interrupteur_allume(nom: str = "APP_REGISTRE_PARTENAIRES") -> bool:
    return (os.environ.get(nom) or "").strip().lower() in {"1", "on", "true", "oui"}


def lecture_seule(chemin: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{chemin.resolve().as_posix()}?mode=ro", uri=True, timeout=30)


# ── Supabase (REST, clé de service) ──────────────────────────────────────────
def _supabase() -> tuple[str, str]:
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip().rstrip("/")
    cle = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or not cle:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis")
    return url, cle


def _requete(methode: str, chemin: str, query: dict[str, str] | None = None, corps: object = None) -> object:
    url, cle = _supabase()
    adresse = f"{url}/rest/v1/{chemin}"
    if query:
        adresse += "?" + urllib.parse.urlencode(query)
    donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
    req = urllib.request.Request(adresse, data=donnees, method=methode, headers={
        "apikey": cle, "Authorization": f"Bearer {cle}", "Content-Type": "application/json",
        "Prefer": "return=representation",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as rep:
            brut = rep.read().decode("utf-8")
            return json.loads(brut) if brut else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Supabase {methode} {chemin} : {exc.code} {exc.read().decode('utf-8', 'replace')[:300]}") from exc


def lire_tout(table: str, select: str, filtres: dict[str, str]) -> list[dict]:
    lignes: list[dict] = []
    debut = 0
    while True:
        page = _requete("GET", table, {"select": select, **filtres, "order": "id.asc", "limit": "1000", "offset": str(debut)})
        page = page if isinstance(page, list) else []
        lignes.extend(page)
        if len(page) < 1000:
            return lignes
        debut += 1000


# ── Ce que le serveur sait ───────────────────────────────────────────────────
def notaires_des_transactions() -> set[str]:
    """Nos numéros des contacts qui tiennent un rôle de notaire dans la table des parties (Supabase)."""
    numeros: set[str] = set()
    debut = 0
    while True:
        page = _requete("GET", "app_affaire_partie", {"select": "app_contact_id",
                        "role": "in.(notaire_vendeur,notaire_acquereur)", "app_contact_id": "not.is.null",
                        "order": "app_contact_id.asc", "limit": "1000", "offset": str(debut)})
        page = page if isinstance(page, list) else []
        numeros |= {str(l["app_contact_id"]) for l in page}
        if len(page) < 1000:
            return numeros
        debut += 1000


def metiers_voulus(avec_notaires: bool = False) -> tuple[dict[tuple[str, str], str], Counter]:
    """{(notre numéro, métier): source} et les comptes."""
    voulus: dict[tuple[str, str], str] = {}
    comptes: Counter = Counter()
    metier_netty_de = {**METIER_NETTY, **({"notaire": "notaire"} if avec_notaires else {})}
    metier_hektor_de = {**METIER_HEKTOR, **({"2": "notaire"} if avec_notaires else {})}
    p2 = lecture_seule(BASE_PHASE2)
    try:
        for contact_id, metiers_json in p2.execute("SELECT hektor_contact_id, metiers_json FROM contact_metier_netty"):
            for metier_netty in json.loads(metiers_json or "[]"):
                metier = metier_netty_de.get(str(metier_netty))
                if not metier:
                    comptes[f"netty_ecarte_{metier_netty}"] += 1
                    continue
                voulus.setdefault((str(contact_id), metier), "netty")
                comptes["netty"] += 1
        traduction = {str(t): str(i) for t, i in p2.execute(
            "SELECT hektor_target_id, hektor_contact_id FROM app_contact_current WHERE hektor_target_id IS NOT NULL")}
    finally:
        p2.close()
    hk = lecture_seule(BASE_HEKTOR)
    try:
        for liste, numero_hektor in hk.execute("SELECT liste, hektor_contact_id FROM hektor_diag_contacts_choix"):
            notre = traduction.get(str(numero_hektor))
            if not notre:
                comptes["hektor_numero_inconnu"] += 1
                continue
            voulus.setdefault((notre, LISTE_HEKTOR[str(liste)]), "hektor")
            comptes["hektor"] += 1
        if hk.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='hektor_contact_metier'").fetchone():
            for numero_hektor, code in hk.execute(
                    "SELECT hektor_contact_id, metier_code FROM hektor_contact_metier WHERE statut = 'done'"):
                metier = metier_hektor_de.get(str(code or ""))
                if not metier:
                    comptes[f"hektor_formulaire_ecarte_{code or 'vide'}"] += 1
                    continue
                notre = traduction.get(str(numero_hektor))
                if not notre:
                    comptes["hektor_numero_inconnu"] += 1
                    continue
                voulus.setdefault((notre, metier), "hektor")
                comptes["hektor_formulaire"] += 1
    finally:
        hk.close()
    if avec_notaires:
        for notre in sorted(notaires_des_transactions()):
            voulus.setdefault((notre, "notaire"), "transactions")
            comptes["transactions_notaire"] += 1
    return voulus, comptes


def liens_voulus() -> tuple[dict[tuple[int, str], dict], Counter, set[int]]:
    """{(annonce, rôle): {partenaire, dossier}} pour les annonces RELUES ('done'), et l'ensemble de ces annonces."""
    comptes: Counter = Counter()
    p2 = lecture_seule(BASE_PHASE2)
    try:
        traduction = {str(t): str(i) for t, i in p2.execute(
            "SELECT hektor_target_id, hektor_contact_id FROM app_contact_current WHERE hektor_target_id IS NOT NULL")}
        dossier_de = {int(a): int(d) for a, d in p2.execute(
            "SELECT hektor_annonce_id, app_dossier_id FROM app_dossier_current "
            "WHERE hektor_annonce_id IS NOT NULL AND app_dossier_id IS NOT NULL")}
    finally:
        p2.close()
    voulus: dict[tuple[int, str], dict] = {}
    relues: set[int] = set()
    hk = lecture_seule(BASE_HEKTOR)
    try:
        for annonce, statut, brut in hk.execute(
                "SELECT hektor_annonce_id, status, diag_contacts_json FROM hektor_annonce_diag_contacts_detail"):
            if statut != "done":
                comptes["annonce_non_relue"] += 1
                continue
            annonce = int(annonce)
            relues.add(annonce)
            champs = json.loads(brut or "{}")
            for role in ("syndic", "diagnostiqueur"):
                numero_hektor = str(((champs.get(role) or {}).get("value")) or "").strip()
                if not numero_hektor:
                    continue
                notre = traduction.get(numero_hektor)
                if not notre:
                    comptes[f"{role}_numero_inconnu"] += 1
                    continue
                voulus[(annonce, role)] = {"partenaire": notre, "dossier": dossier_de.get(annonce)}
                comptes[f"{role}_pose_chez_hektor"] += 1
    finally:
        hk.close()
    return voulus, comptes, relues


# ── La reprise ───────────────────────────────────────────────────────────────
def contacts_supprimes() -> set[str]:
    """NOS numéros des contacts supprimés depuis l'app (journal des suppressions, chez Supabase)."""
    numeros: set[str] = set()
    for ligne in lire_tout("app_console_deleted_contact_log", "id,app_contact_id,identite:before_json->>hektor_contact_id", {}):
        for cle in ("app_contact_id", "identite"):
            if ligne.get(cle) not in (None, ""):
                numeros.add(str(ligne[cle]))
    return numeros


def ecarter_les_supprimes(metiers: dict[tuple[str, str], str], liens: dict[tuple[int, str], dict],
                          supprimes: set[str]) -> tuple[dict[tuple[str, str], str], dict[tuple[int, str], dict], int]:
    """§23 (05/11) : la suppression d'un contact EFFACE ses lignes du registre (décision de Frédéric, « Effacer ») ;
    la nuit ne doit pas les recréer depuis une source qui le connaît encore (la table des parties, par exemple)."""
    gardes_m = {cle: source for cle, source in metiers.items() if cle[0] not in supprimes}
    gardes_l = {cle: voulu for cle, voulu in liens.items() if str(voulu.get("partenaire")) not in supprimes}
    return gardes_m, gardes_l, (len(metiers) - len(gardes_m)) + (len(liens) - len(gardes_l))


def metiers_retires_par_quelquun() -> set[tuple[str, str]]:
    """(notre numéro, métier) dont une ligne a été RETIRÉE par quelqu'un (`retire_par` rempli) -- §25, pièce 3.2."""
    return {(str(l["contact_id"]), str(l["metier"])) for l in lire_tout(
        "app_partenaire_metier", "id,contact_id,metier", {"retire_le": "not.is.null", "retire_par": "not.is.null"})}


def ecarter_les_retires(metiers: dict[tuple[str, str], str], retires: set[tuple[str, str]],
                        actifs: set[tuple[str, str]]) -> tuple[dict[tuple[str, str], str], int]:
    """§25 (05/11) : un métier retiré à l'écran fait foi -- la nuit ne le rajoute JAMAIS. S'il a été remis à l'écran
    (une ligne active existe), il reste voulu comme les autres."""
    gardes = {cle: source for cle, source in metiers.items() if cle not in retires or cle in actifs}
    return gardes, len(metiers) - len(gardes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remplit le registre des partenaires depuis le serveur (à blanc par défaut).")
    parser.add_argument("--ecrire", action="store_true", help="écrire chez Supabase (sinon : compter seulement)")
    parser.add_argument("--notaires-a-blanc", action="store_true",
                        help="compter aussi les notaires, interrupteur éteint (sans effet avec --ecrire)")
    args = parser.parse_args()
    charger_env()

    if args.ecrire and not interrupteur_allume():
        print(json.dumps({"statut": "eteint", "raison": "APP_REGISTRE_PARTENAIRES absent ou faux dans .env : rien n'est écrit"}, ensure_ascii=False))
        return 0

    avec_notaires = interrupteur_allume("APP_REGISTRE_PARTENAIRES_NOTAIRES") or args.notaires_a_blanc
    if avec_notaires and args.ecrire and not interrupteur_allume("APP_REGISTRE_PARTENAIRES_NOTAIRES"):
        avec_notaires = False   # --notaires-a-blanc ne sert qu'à compter : jamais d'écriture de notaire sans l'interrupteur
    metiers, c_metiers = metiers_voulus(avec_notaires)
    liens, c_liens, relues = liens_voulus()
    # §23 (05/11) : jamais une ligne pour un contact supprimé depuis l'app (retiré de ce qui est VOULU, pas seulement de
    # ce qui est ajouté : la vérification finale compare à tout ce qui est voulu).
    metiers, liens, ecartes_supprimes = ecarter_les_supprimes(metiers, liens, contacts_supprimes())

    existants_metier = {(r["contact_id"], r["metier"]) for r in lire_tout(
        "app_partenaire_metier", "id,contact_id,metier", {"retire_le": "is.null"})}
    # §25 (05/11) : un métier retiré par quelqu'un n'est plus voulu (sinon la vérification finale le réclamerait).
    metiers, ecartes_retires = ecarter_les_retires(metiers, metiers_retires_par_quelquun(), existants_metier)
    existants_lien = lire_tout("app_partenaire_lien", "id,partenaire_id,role,hektor_annonce_id,origine",
                               {"retire_le": "is.null", "objet": "eq.bien"})
    actif_par_cle: dict[tuple[int, str], list[dict]] = {}
    for lien in existants_lien:
        if lien.get("hektor_annonce_id") is None:
            continue
        actif_par_cle.setdefault((int(lien["hektor_annonce_id"]), lien["role"]), []).append(lien)

    a_ajouter_metier = [{"contact_id": c, "metier": m, "source": s} for (c, m), s in sorted(metiers.items())
                        if (c, m) not in existants_metier]
    a_ajouter_lien: list[dict] = []
    a_retirer_lien: list[int] = []
    ecarts_app = 0
    for (annonce, role), voulu in sorted(liens.items()):
        actifs = actif_par_cle.get((annonce, role), [])
        if any(l["partenaire_id"] == voulu["partenaire"] for l in actifs):
            continue
        if any(l["origine"] == "app" for l in actifs):
            ecarts_app += 1          # l'app a posé un autre partenaire : l'app gagne, on compte l'écart
            continue
        a_retirer_lien.extend(l["id"] for l in actifs if l["origine"] == "hektor")   # Hektor a changé de syndic
        ligne = {"partenaire_id": voulu["partenaire"], "role": role, "objet": "bien",
                 "hektor_annonce_id": annonce, "origine": "hektor"}
        if voulu.get("dossier") is not None:
            ligne["app_dossier_id"] = voulu["dossier"]
        a_ajouter_lien.append(ligne)
    # Hektor a RETIRÉ le syndic d'une annonce qu'il vient de relire : le lien « hektor » est retiré (daté).
    for (annonce, role), actifs in actif_par_cle.items():
        if annonce in relues and (annonce, role) not in liens:
            a_retirer_lien.extend(l["id"] for l in actifs if l["origine"] == "hektor")

    compte_rendu = {
        "statut": "a_blanc" if not args.ecrire else "ecrit", "notaires": avec_notaires,
        "metiers_voulus": len(metiers), "metiers_deja_la": len(metiers) - len(a_ajouter_metier),
        "metiers_a_ajouter": len(a_ajouter_metier),
        "metiers_par_source_et_metier": Counter(f"{l['source']}:{l['metier']}" for l in a_ajouter_metier),
        "liens_voulus": len(liens), "liens_a_ajouter": len(a_ajouter_lien), "liens_a_retirer": len(set(a_retirer_lien)),
        "ecarts_app_gagne": ecarts_app,
        "contacts_supprimes_ecartes": ecartes_supprimes,
        "metiers_retires_ecartes": ecartes_retires,
        "comptes_sources": {**c_metiers, **c_liens},
    }

    if args.ecrire:
        for debut in range(0, len(a_ajouter_metier), 500):
            _requete("POST", "app_partenaire_metier", corps=a_ajouter_metier[debut:debut + 500])
        maintenant = datetime.now(timezone.utc).isoformat()
        for identifiant in sorted(set(a_retirer_lien)):
            _requete("PATCH", "app_partenaire_lien", {"id": f"eq.{identifiant}", "retire_le": "is.null"},
                     {"retire_le": maintenant})
        for debut in range(0, len(a_ajouter_lien), 500):
            _requete("POST", "app_partenaire_lien", corps=a_ajouter_lien[debut:debut + 500])
        # Vérification : ce qui devait être là y est.
        apres_metier = {(r["contact_id"], r["metier"]) for r in lire_tout(
            "app_partenaire_metier", "id,contact_id,metier", {"retire_le": "is.null"})}
        manquants = [k for k in metiers if k not in apres_metier]
        compte_rendu["verification_metiers_manquants"] = len(manquants)
        if manquants:
            print(json.dumps(compte_rendu, ensure_ascii=False, default=dict))
            return 1

    print(json.dumps(compte_rendu, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # une lecture ratée n'est jamais un vert
        print(json.dumps({"statut": "echec", "erreur": str(exc)[:500]}, ensure_ascii=False))
        sys.exit(1)
