#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SI NOTRE REGISTRE NOMME QUELQU'UN, L'APP DOIT POUVOIR OUVRIR SA FICHE.   04/11/2026

Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §61-70 ;
       notice/AUDIT_INDEX_GLOBAL_CONTACTS_2026-11-04.md §12-16.
Patron : elargir_perimetre_console.py (11/09) -- meme place, meme verification.

LE TROU. Un contact ne monte vers l'app que s'il est lie a une annonce NON ARCHIVEE, s'il a
une recherche active, ou s'il est nomme dans une transaction (11/09). Or notre registre des
relations (`app_relation`, « un lien ne se perd jamais ») nomme aussi les proprietaires des
biens ARCHIVES : l'historique d'un bien cite des personnes dont l'app n'a pas la fiche.
Mesure du 04/11 : 31 295 vraies personnes (21 873 actives, 9 422 archivees). Et les vrais
professionnels de Netty (table `contact_metier_netty`, metier_netty.py) : 238 de plus.

DEUX RAISONS NEUVES, posees sur des contacts NON eligibles seulement :
    registre_relation   nomme par app_relation (lien vivant : present chez Hektor, ou pose par
                        l'app et pas absent ; jamais retire), sur au moins un bien qui n'est
                        PAS une location (decision du 26/08 : les locations restent au serveur)
    partenaire_netty    un code professionnel de Netty (contact_metier_netty)
    partenaire_hektor   (ajoutee le 04/11 soir, chantier partenaires, lot 1) un contact que Hektor range
                        en metier Syndic ou Diagnostiqueur : les choix des deux listes de l'annonce
                        (`hektor_diag_contacts_choix`, data/hektor.sqlite, lue par
                        sync_hektor_contacts_diagnostics.py). Note : CHANTIER_ANNUAIRE_PARTENAIRES §16.
⛔ JAMAIS une case vide : une fiche sans nom ni prenom reste dehors (ce sont les places de
   conjoint de la migration, que la nature reconnait de la meme facon).
   ⚠ Sauf pour partenaire_hektor : un syndic est souvent une SOCIETE, sans nom ni prenom mais avec sa
   raison sociale (`display_name`) -- 9 des 96 au 04/11. Pour cette raison seule, la raison sociale vaut nom.
⚠ A REJOUER CHAQUE NUIT, APRES build_contacts_layer et elargir_perimetre_console (la couche
  est refaite par DELETE + INSERT), AVANT le push. Lit la base LOCALE seulement.
⛔ INTERRUPTEUR APP_PERIMETRE_REGISTRE (.env) : absent = eteint, rien n'est fait.
IDEMPOTENT. RETOUR ARRIERE : eteindre ; la nuit suivante remet le perimetre d'avant (et le
remede du 04/11, APP_GARDER_CONTACTS_DEJA_POUSSES, garde a jour ceux deja envoyes).

    python phase2/contacts/elargir_perimetre_registre.py [--dry-run]
Sortie : 0 = fait (ou eteint) · 1 = verification ratee · 2 = table source absente.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

BASE = RACINE / "phase2" / "phase2.sqlite"
MIROIR = RACINE / "data" / "hektor.sqlite"
CIBLE = "app_contact_current"
RAISON_REGISTRE = "registre_relation"
RAISON_PARTENAIRE = "partenaire_netty"
RAISON_PARTENAIRE_HEKTOR = "partenaire_hektor"
LOCATIONS = {"2", "8", "11"}   # offre_type de Hektor : location, location saisonniere, immobilier pro en location


def allume() -> bool:
    try:
        from push_contacts_to_supabase import DEFAULT_ENV_FILES, load_env_file  # noqa: PLC0415
        for fichier in DEFAULT_ENV_FILES:
            load_env_file(fichier)
    except Exception:  # noqa: BLE001 -- sans .env, l'interrupteur reste eteint
        pass
    return (os.environ.get("APP_PERIMETRE_REGISTRE") or "").strip().lower() in {"1", "on", "true", "oui"}


def table_existe(conn: sqlite3.Connection, nom: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom,)).fetchone() is not None


def types_d_offre(miroir: Path) -> dict[str, str]:
    if not miroir.exists():
        return {}
    m = sqlite3.connect(f"file:{miroir}?mode=ro", uri=True, timeout=30)
    try:
        return {str(a): str(o) for a, o in m.execute("SELECT hektor_annonce_id, offre_type FROM hektor_annonce")}
    finally:
        m.close()


def nommes_par_le_registre(conn: sqlite3.Connection, offre: dict[str, str]) -> set[str]:
    """Les contacts que le registre nomme sur au moins un bien qui n'est pas une location."""
    hors_location: set[str] = set()
    for cid, annonce in conn.execute(
            "SELECT app_contact_id, hektor_annonce_id FROM app_relation "
            "WHERE app_contact_id IS NOT NULL AND retire_le IS NULL "
            "AND (present_in_hektor = 1 OR (source = 'app' AND absent_depuis IS NULL))"):
        # Un type inconnu (bien absent du miroir) n'est PAS une location prouvee : il compte.
        if offre.get(str(annonce), "") not in LOCATIONS:
            hors_location.add(str(cid))
    return hors_location


def partenaires_netty(conn: sqlite3.Connection) -> set[str]:
    if not table_existe(conn, "contact_metier_netty"):
        return set()
    return {str(r[0]) for r in conn.execute("SELECT hektor_contact_id FROM contact_metier_netty")}


def choix_hektor(miroir: Path) -> set[str]:
    """Les numeros HEKTOR des contacts de metier Syndic / Diagnostiqueur (choix des listes de l'annonce)."""
    if not miroir.exists():
        return set()
    m = sqlite3.connect(f"file:{miroir}?mode=ro", uri=True, timeout=30)
    try:
        numeros: set[str] = set()
        if table_existe(m, "hektor_diag_contacts_choix"):
            numeros |= {str(r[0]) for r in m.execute("SELECT hektor_contact_id FROM hektor_diag_contacts_choix")}
        # Et le metier lu dans le formulaire des partenaires crees depuis la migration (metier_hektor_contacts.py).
        # Ecartes : '' non defini, 2 Notaire (sa fiche existe), 6 Autre, 7 Collaborateur (nos salaries), 16 A supprimer.
        if table_existe(m, "hektor_contact_metier"):
            numeros |= {str(r[0]) for r in m.execute(
                "SELECT hektor_contact_id FROM hektor_contact_metier WHERE statut = 'done' "
                "AND COALESCE(metier_code, '') NOT IN ('', '2', '6', '7', '16')")}
        return numeros
    finally:
        m.close()


def colonnes(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})")}


def partenaires_hektor(conn: sqlite3.Connection, numeros_hektor: set[str]) -> set[str]:
    """Nos numeros des contacts que Hektor range en Syndic / Diagnostiqueur (traduits par hektor_target_id)."""
    if not numeros_hektor or "hektor_target_id" not in colonnes(conn, CIBLE):
        return set()
    return {str(cid) for cid, cible in conn.execute(f"SELECT hektor_contact_id, hektor_target_id FROM {CIBLE} "
                                                    "WHERE hektor_target_id IS NOT NULL")
            if str(cible) in numeros_hektor}


def a_faire_entrer(conn: sqlite3.Connection, registre: set[str], pros: set[str],
                   pros_hektor: set[str] | None = None) -> list[tuple[str, str]]:
    pros_hektor = pros_hektor or set()
    avec_affichage = "display_name" in colonnes(conn, CIBLE)
    conn.row_factory = sqlite3.Row
    try:
        sortie = []
        for ligne in conn.execute(
                f"SELECT hektor_contact_id, nom, prenom, eligibility_reasons_json"
                f"{', display_name' if avec_affichage else ''} FROM {CIBLE} "
                f"WHERE COALESCE(supabase_sync_eligible, 0) = 0"):
            cid = str(ligne["hektor_contact_id"])
            neuves = (([RAISON_REGISTRE] if cid in registre else []) + ([RAISON_PARTENAIRE] if cid in pros else [])
                      + ([RAISON_PARTENAIRE_HEKTOR] if cid in pros_hektor else []))
            if not neuves:
                continue
            a_un_nom = bool(str(ligne["nom"] or "").strip() or str(ligne["prenom"] or "").strip())
            if not a_un_nom and RAISON_PARTENAIRE_HEKTOR in neuves and avec_affichage:
                a_un_nom = bool(str(ligne["display_name"] or "").strip())   # la raison sociale d'une societe
                neuves = [RAISON_PARTENAIRE_HEKTOR] if a_un_nom else neuves  # les autres raisons gardent leur garde
            if not a_un_nom:
                continue  # une case vide reste dehors
            try:
                raisons = json.loads(ligne["eligibility_reasons_json"] or "[]")
            except (TypeError, ValueError):
                raisons = []
            if not isinstance(raisons, list):
                raisons = []
            raisons += [r for r in neuves if r not in raisons]
            sortie.append((json.dumps(raisons, ensure_ascii=False), cid))
        return sortie
    finally:
        conn.row_factory = None


def executer(conn: sqlite3.Connection, offre: dict[str, str], dry_run: bool,
             numeros_hektor: set[str] | None = None) -> int:
    if not table_existe(conn, "app_relation"):
        print("[perimetre registre] REFUS : app_relation absente en local -- rien n'est modifie")
        return 2
    registre = nommes_par_le_registre(conn, offre)
    pros = partenaires_netty(conn)
    pros_hektor = partenaires_hektor(conn, numeros_hektor or set())
    avant = conn.execute(f"SELECT COUNT(*) FROM {CIBLE} WHERE supabase_sync_eligible = 1").fetchone()[0]
    entrants = a_faire_entrer(conn, registre, pros, pros_hektor)
    par_raison = {RAISON_REGISTRE: 0, RAISON_PARTENAIRE: 0, RAISON_PARTENAIRE_HEKTOR: 0}
    for raisons, _ in entrants:
        for r in par_raison:
            par_raison[r] += int(r in raisons)
    print("[perimetre registre] nommes par le registre (hors locations) %7d" % len(registre))
    print("[perimetre registre] partenaires Netty                      %7d" % len(pros))
    print("[perimetre registre] partenaires Hektor (syndic, diag.)     %7d" % len(pros_hektor))
    print("[perimetre registre] annuaire avant                         %7d" % avant)
    print("[perimetre registre] a faire entrer                         %7d   (registre %d, partenaires %d, Hektor %d)"
          % (len(entrants), par_raison[RAISON_REGISTRE], par_raison[RAISON_PARTENAIRE], par_raison[RAISON_PARTENAIRE_HEKTOR]))
    if dry_run:
        print("[perimetre registre] --dry-run : rien n'a ete ecrit.")
        return 0
    if entrants:
        with conn:  # une seule transaction : ou tout le monde entre, ou personne
            conn.executemany(f"UPDATE {CIBLE} SET supabase_sync_eligible = 1, eligibility_reasons_json = ? "
                             f"WHERE hektor_contact_id = ?", entrants)
    apres = conn.execute(f"SELECT COUNT(*) FROM {CIBLE} WHERE supabase_sync_eligible = 1").fetchone()[0]
    sans_raison = conn.execute(f"SELECT COUNT(*) FROM {CIBLE} WHERE supabase_sync_eligible = 1 "
                               "AND COALESCE(eligibility_reasons_json, '') IN ('', '[]')").fetchone()[0]
    print("[perimetre registre] annuaire apres                         %7d   (+%d)" % (apres, apres - avant))
    print("[perimetre registre] eligibles sans aucune raison           %7d   %s"
          % (sans_raison, "OK" if sans_raison == 0 else "A REGARDER"))
    return 0 if sans_raison == 0 and apres == avant + len(entrants) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase2-db", type=Path, default=BASE)
    ap.add_argument("--miroir", type=Path, default=MIROIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not allume():
        print("[perimetre registre] interrupteur APP_PERIMETRE_REGISTRE eteint : rien a faire")
        return 0
    conn = sqlite3.connect(args.phase2_db, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        return executer(conn, types_d_offre(args.miroir), args.dry_run, choix_hektor(args.miroir))
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
