# -*- coding: utf-8 -*-
"""A.3 PIECE 5 — LE MANDAT DANS LA CARTE RECHERCHE DU CONTACT.    16/10/2026

Produit `app_contact_mandat_recherche_current` : pour chaque mandat de recherche
de notre registre, LA recherche du contact qu'il couvre -- quand on peut la
designer sans deviner.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI UNE TABLE A PART, ET PAS UNE COLONNE SUR LES RECHERCHES
═══════════════════════════════════════════════════════════════════════════════
Une colonne sur `app_contact_search_current` paraissait plus simple : le front la
lit en `select('*')`, elle serait arrivee seule. DEUX MESURES L'ONT ECARTEE.

⚠⚠ ① CETTE TABLE EST REMPLACEE EN ENTIER CHAQUE NUIT.
   `build_contacts_layer.py` fait `replace_table_rows(..., search_rows, ...)` :
   tout ce qui n'est pas refabrique par le constructeur DISPARAIT. Notre colonne
   serait donc vide chaque matin, a moins d'aller remplir le constructeur des
   contacts lui-meme -- 2 300 lignes dans le chemin de nuit, pour un affichage.
   ⭐ C'EST EXACTEMENT LE PRINCIPE DE A.3 : notre donnee ne vit pas dans une
     table que la descente de Hektor reecrit. Elle vit chez nous.

⚠ ② L'EMPREINTE DE POUSSEE AURAIT CHANGE POUR TOUTES LES LIGNES.
   `stable_payload_hash` hache TOUTES les colonnes sauf `refreshed_at` : ajouter
   une colonne, meme NULL partout, change l'empreinte des 77 195 recherches et
   les fait TOUTES repartir (~3 min). Ici on pousse 21 lignes.

PRECEDENT SUIVI : `app_contact_stats_current` -- une table satellite, poussee a
part, lue par le front sous son propre nom. On n'invente pas un patron.

═══════════════════════════════════════════════════════════════════════════════
CE QU'ON NE FAIT PAS
═══════════════════════════════════════════════════════════════════════════════
⛔ ON N'INVENTE AUCUN RATTACHEMENT. La regle est celle deja eprouvee le 15/10
   dans `registre_mandats_sans_bien._choisir_recherche`, et elle est IMPORTEE,
   pas recopiee : une seule recherche -> c'est elle ; plusieurs -> seule la
   commune du registre legal tranche, et seulement si elle en designe UNE ;
   sinon AUCUNE, et la ligne porte alors `contact_search_key = NULL`.
   Mesure du 15/10 sur les 38 : 19 tranchees seules, 2 par la commune,
   11 sans recherche, 6 sans contact.

⛔ ON NE CREE AUCUNE RECHERCHE. Une recherche ne peut pas naitre chez nous (sa
   cle est un hache de la recherche DESCENDUE de Hektor) : la creer voudrait
   dire ECRIRE CHEZ HEKTOR. Decision du 16/10, mesuree -- voir la memoire
   `creer-une-recherche-passe-par-hektor`.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2.sync.registre_mandats_sans_bien import (  # noqa: E402
    _choisir_recherche,
    _liste_json,
    _types_json,
)

PHASE2_DB = ROOT / "phase2" / "phase2.sqlite"
TABLE = "app_contact_mandat_recherche_current"

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    hektor_contact_id   TEXT NOT NULL,
    numero_mandat       TEXT NOT NULL,
    -- La recherche que ce mandat couvre. NULL quand on ne peut pas la designer
    -- sans deviner : la carte du contact le dira, elle ne mentira pas.
    contact_search_key  TEXT,
    search_index        INTEGER,
    type                TEXT,
    date_debut          TEXT,
    date_fin            TEXT,
    date_cloture        TEXT,
    famille             TEXT,
    source_app          TEXT,
    designation         TEXT,
    refreshed_at        TEXT NOT NULL,
    PRIMARY KEY (hektor_contact_id, numero_mandat)
);
"""
INDEX = (
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_contact"
    f"  ON {TABLE}(hektor_contact_id);",
    f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_search"
    f"  ON {TABLE}(contact_search_key);",
)

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _recherches_par_contact(con: sqlite3.Connection) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for ligne in con.execute(
            "SELECT hektor_contact_id, search_index, is_active, villes_json,"
            "       types_json, prix_min, prix_max, contact_search_key"
            "  FROM app_contact_search_current"):
        out.setdefault(str(ligne[0]), []).append({
            "search_index": ligne[1], "is_active": ligne[2],
            "villes_json": ligne[3], "types_json": ligne[4],
            "prix_min": ligne[5], "prix_max": ligne[6],
            "contact_search_key": ligne[7],
        })
    return out


def construire(con: sqlite3.Connection) -> list[dict]:
    """Les lignes a poser. Ne touche a rien : rend seulement la liste."""
    recherches = _recherches_par_contact(con)
    lignes: list[dict] = []
    for (numero, contact_id, type_mandat, debut, fin, cloture, famille,
         source_app, payload_json) in con.execute(
            "SELECT numero_mandat, app_contact_id, type, date_debut, date_fin,"
            "       date_cloture, famille, source_app, payload_json"
            "  FROM app_mandat"
            " WHERE hektor_annonce_id = '' AND app_contact_id IS NOT NULL"
            " ORDER BY numero_mandat"):
        numero = str(numero or "").strip()
        contact = str(contact_id or "").strip()
        if not (numero and contact):
            continue
        try:
            payload = json.loads(payload_json or "{}")
        except Exception:
            payload = {}
        commune = None
        situation = str((payload or {}).get("situation") or "")
        if situation:
            from phase2.sync.importer_mandats_recherche import commune_cherchee
            commune = commune_cherchee(situation)
        rech = _choisir_recherche(recherches.get(contact, []), commune)
        lignes.append({
            "hektor_contact_id": contact,
            "numero_mandat": numero,
            "contact_search_key": (rech or {}).get("contact_search_key"),
            "search_index": (rech or {}).get("search_index"),
            "type": (type_mandat or None),
            "date_debut": debut or None,
            "date_fin": fin or None,
            "date_cloture": cloture or None,
            "famille": famille or None,
            "source_app": source_app or None,
            # ⭐ La phrase qui dit ce que le mandat couvre (posee le 16/10).
            #   Sur un mandat qui DESIGNE un bien, c'est la seule chose vraie a
            #   montrer : il n'y a pas de criteres a afficher.
            "designation": (str((payload or {}).get("designation") or "").strip()
                            or situation or None),
        })
    return lignes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pose le lien mandat de recherche <-> recherche du contact.")
    parser.add_argument("--ecrire", action="store_true",
                        help="Ecrit vraiment. Sans lui, on ne fait que compter.")
    parser.add_argument("--pousser", action="store_true",
                        help="Envoie la table locale a Supabase (UPSERT, puis"
                             " retrait des lignes qui n'existent plus). Implique"
                             " --ecrire.")
    args = parser.parse_args()
    if args.pousser:
        args.ecrire = True

    con = sqlite3.connect(PHASE2_DB)
    con.execute("PRAGMA busy_timeout=30000")
    lignes = construire(con)

    avec = sum(1 for x in lignes if x["contact_search_key"])
    print(f"lignes a poser : {len(lignes)}")
    print(f"   rattachees a UNE recherche : {avec}")
    print(f"   sans recherche designee    : {len(lignes) - avec}"
          f"   (la carte le dira)")
    print()
    print(f"{'contact':>12}  {'mandat':>7}  {'recherche':<10} designation")
    for x in lignes:
        cle = (x["contact_search_key"] or "")[:8] or "—"
        print(f"{x['hektor_contact_id']:>12}  {x['numero_mandat']:>7}  "
              f"{cle:<10} {str(x['designation'] or '')[:58]}")

    if not args.ecrire:
        print("\nA BLANC — rien n'a ete ecrit. Relancer avec --ecrire.")
        con.close()
        return 0

    vu = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.executescript(SCHEMA)
    for ordre in INDEX:
        con.execute(ordre)
    # ⚠ REMPLACEMENT COMPLET, et c'est VOULU : cette table est un CALCUL, pas un
    #   registre. Le registre, c'est `app_mandat` -- lui ne perd jamais rien.
    #   Un rattachement qui change doit donc pouvoir DISPARAITRE d'ici.
    con.execute(f"DELETE FROM {TABLE}")
    con.executemany(
        f"INSERT INTO {TABLE}(hektor_contact_id, numero_mandat,"
        f"  contact_search_key, search_index, type, date_debut, date_fin,"
        f"  date_cloture, famille, source_app, designation, refreshed_at)"
        f" VALUES(:hektor_contact_id, :numero_mandat, :contact_search_key,"
        f"        :search_index, :type, :date_debut, :date_fin, :date_cloture,"
        f"        :famille, :source_app, :designation, :refreshed_at)",
        [dict(x, refreshed_at=vu) for x in lignes])
    con.commit()
    n = con.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
    print(f"\nECRIT : {n} ligne(s) dans {TABLE}.")
    con.close()

    if not args.pousser:
        return 0

    # ───────────────────────────────────────────────────────────────────────
    # LA POUSSEE
    # ⚠ UPSERT, PUIS RETRAIT DES LIGNES DISPARUES -- dans CET ordre.
    #   Cette table est un CALCUL : un rattachement qui change doit pouvoir
    #   s'effacer. Mais on ne VIDE jamais d'abord : a aucun instant la carte
    #   d'un contact ne doit se retrouver sans son mandat (lecon du projet :
    #   la fenetre delete/reinsert).
    # ───────────────────────────────────────────────────────────────────────
    sys.path.insert(0, str(ROOT / "phase2" / "sync"))
    from push_upgrade_to_supabase import (  # noqa: E402
        DEFAULT_ENV_FILES, SupabaseRestClient, load_env_files)
    import os

    load_env_files(DEFAULT_ENV_FILES)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis")
    client = SupabaseRestClient(base_url=url, service_role_key=cle)

    a_pousser = [{c: x[c] for c in (
        "hektor_contact_id", "numero_mandat", "contact_search_key",
        "search_index", "type", "date_debut", "date_fin", "date_cloture",
        "famille", "source_app", "designation")} for x in lignes]
    client.upsert_rows(path=TABLE, rows=a_pousser, batch_size=100)
    print(f"POUSSE : {len(a_pousser)} ligne(s) en UPSERT.")

    # ── le retrait : ce qui est la-haut et plus ici
    gardees = {(x["hektor_contact_id"], x["numero_mandat"]) for x in lignes}
    distantes = client.fetch_all_rows(
        path=TABLE, select="hektor_contact_id,numero_mandat",
        order="hektor_contact_id")
    a_retirer = [r for r in distantes
                 if (str(r["hektor_contact_id"]), str(r["numero_mandat"]))
                 not in gardees]
    for r in a_retirer:
        # delete_all_rows prend un FILTRE : ici il ne vise que CETTE ligne.
        client.delete_all_rows(
            path=TABLE,
            filter_expr=("hektor_contact_id=eq.%s&numero_mandat=eq.%s"
                         % (r["hektor_contact_id"], r["numero_mandat"])))
    print(f"RETIRE : {len(a_retirer)} ligne(s) qui n'ont plus de raison d'etre.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
