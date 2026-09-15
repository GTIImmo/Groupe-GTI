#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LA REPARTITION DE COMMISSION, A LA FORME DU PROJET.        15/09/2026

Chantier C.19-d, tache 3.2e, lot 5 -- etape 4 du plan de sortie.

POURQUOI CE FICHIER REMPLACE `phase2/identite/convertir_repartition_commission.py`
---------------------------------------------------------------------------------
Question de Frederic, 15/09 : « comment fonctionnait le rattrapage des notaires ? ».
La comparaison est sans appel.

    sync_hektor_compromis_console.py  lit phase2.sqlite en LECTURE SEULE pour
        choisir ses cibles, lit le miroir pour savoir ce qui a bouge, et ne va
        chercher DEHORS que ce qu'il ne peut pas connaitre -- l'etat chez Hektor.
    affaire_ledger.py / export_app_payload.py  calculent dans phase2.sqlite et ne
        se servent de Supabase que pour POUSSER.
    l'ancien convertisseur  N'OUVRAIT JAMAIS phase2.sqlite. Pas une fois. Sa
        matiere est ENTIEREMENT en local et il allait la chercher par le reseau.

CE QUE CETTE FORME A COUTE EN UNE SEULE JOURNEE -- et chacun disparait ici :
    une pagination REST refaite a la main -> 4 lignes sautees sur 13 309
    un POST entier refuse pour UNE valeur a 100,001 -> ecriture arretee a 10 822
    le serveur local qui n'a rien et attend la descente
    et une etape PARALYSEE pendant la panne Supabase du matin, alors que toute sa
    matiere dormait sur le disque

⭐ ET C'EST CE QUI SURVIT A LA COUPURE. `intervenants_json` est un bloc recopie du
  formulaire de Hektor : le front ne le lit pas, et le jour ou l'on coupe, plus
  personne ne saura le relire ni le regenerer. Ce programme le transforme en
  donnee A NOUS -- un nom, un pourcentage, un dossier.

LES DEUX TEMPS, comme affaire_ledger.py
---------------------------------------
    --calculer   lit phase2.sqlite, calcule, ECRIT LA TABLE LOCALE. Aucun reseau :
                 tourne meme quand Supabase est en panne.
    --pousser    envoie a Supabase par la RPC `app_repartition_absorber`.

⚠ ET LA PROTECTION NE VIENT PAS D'ICI. C'est la BASE qui refuse d'ecraser un
  dossier que l'app a pose (patch_repartition_garde_2026-09-15.sql). L'ancien
  convertisseur tenait cette regle par politesse, et il a eu un defaut pendant
  quelques heures ce matin : il ne reconnaissait que `origine = 'saisie'` alors
  que la modale inscrit `'defaut'` quand on ACCEPTE les noms proposes.
  ➡ ON NE PEUT PAS LIRE LA LISTE DES PROTEGES EN LOCAL : la descente passe a
    07:30 et le run a 05:00, donc la copie locale peut avoir 21 h de retard sur
    une saisie. Seule la base sait, a la seconde.

LE CALCUL, INCHANGE. Hektor coupe la commission en deux moities
(`unites_*_percent`, 50/50 partout ou il les rend) puis donne a chaque personne
sa part DE SA MOITIE. Notre table stocke la part DU TOTAL :

    part du total = (unites du cote / 100) x (part de la personne / 100) x 100

    python phase2/sync/repartition_commission.py                 # a blanc
    python phase2/sync/repartition_commission.py --calculer
    python phase2/sync/repartition_commission.py --calculer --pousser
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)

PHASE2_DB = RACINE / "phase2" / "phase2.sqlite"
CIBLE = "app_affaire_repartition"
# Le plus avance gagne quand deux transactions d'un meme dossier se contredisent.
# Mesure du 14/09 : 16 biens portant compromis ET vente, 16 fois identiques. Quand
# ils different, c'est la VENTE qui paie.
RANG_GENRE = {"offre": 0, "compromis": 1, "vente": 2}
# ⚠ 100,001 ET PAS 100. Hektor ecrit `percent = 200.001` la ou il veut dire 200 --
#   sa facon d'exprimer « cette personne prend tout, y compris l'autre cote »
#   (vente 23208, montant sortie a 0). 12 dossiers sur 6 655 depassent ainsi, d'un
#   millieme. Refuser a 100 pile rejetterait de la donnee juste.
TOLERANCE = Decimal("100.001")

DDL = f"""
CREATE TABLE IF NOT EXISTS {CIBLE} (
    app_chaine_id   INTEGER NOT NULL,
    app_dossier_id  INTEGER,
    cote            TEXT    NOT NULL,
    rang            INTEGER NOT NULL,
    hektor_user_id  TEXT    NOT NULL,
    nom_au_moment   TEXT,
    pourcentage     REAL    NOT NULL DEFAULT 0,
    origine         TEXT,
    ecrit_le        TEXT,
    ecrit_par       TEXT,
    PRIMARY KEY (app_chaine_id, cote, rang)
)
"""


def nombre(v) -> Decimal | None:
    t = str(v if v is not None else "").strip().replace(",", ".")
    if not t:
        return None
    try:
        return Decimal(t)
    except Exception:  # noqa: BLE001
        return None


def trois_decimales(v: Decimal) -> float:
    return float(v.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def calculer(con: sqlite3.Connection) -> tuple[list[dict], dict]:
    """Le calcul, entierement en local. Rend (lignes, compteurs)."""
    compte: dict[str, int] = defaultdict(int)
    nommes: list[str] = []

    # ── 1. LE DOSSIER DE CHAQUE TRANSACTION ──
    # ⚠ CE QUE HEKTOR N'A PLUS NE PRODUIT PAS DE REPARTITION. Une transaction
    #   supprimee garde son releve chez nous -- le registre est delete-never --
    #   mais en tirer une commission crediterait quelqu'un pour une vente qui
    #   n'existe plus. Meme regle qu'aux quatre autres endroits du projet.
    info: dict[int, tuple] = {}
    for r in con.execute(
        "SELECT app_affaire_id, app_chaine_id, app_dossier_id, hektor_affaire_id, "
        "       present_in_hektor "
        "  FROM app_affaire_ledger WHERE app_chaine_id IS NOT NULL"
    ):
        efface = (str(r[3] or "").strip() != ""
                  and str(r[4]) in ("0", "false", "False"))
        info[int(r[0])] = (int(r[1]), r[2], efface)

    # ── 2. UN DOSSIER, UNE SOURCE : LA PLUS AVANCEE ──
    meilleure: dict[int, dict] = {}
    for r in con.execute(
        "SELECT app_affaire_id, kind, intervenants_json, "
        "       unites_entree_percent, unites_sortie_percent "
        "  FROM app_affaire_console "
        " WHERE intervenants_json IS NOT NULL AND intervenants_json NOT IN ('', '[]')"
    ):
        ref = info.get(int(r[0]))
        if ref is None:
            compte["sans dossier rattachable"] += 1
            continue
        chaine, dossier, efface = ref
        if efface:
            compte["effacee chez Hektor"] += 1
            continue
        rang = RANG_GENRE.get(str(r[1] or ""), -1)
        courant = meilleure.get(chaine)
        if courant is None or rang > courant["_rang"]:
            meilleure[chaine] = {"_rang": rang, "_dossier": dossier,
                                 "gens": r[2], "e": r[3], "s": r[4]}

    # ── 3. LA CONVERSION ──
    lignes: list[dict] = []
    for chaine, src in sorted(meilleure.items()):
        gens = src["gens"]
        if isinstance(gens, str):
            try:
                gens = json.loads(gens)
            except Exception:  # noqa: BLE001
                gens = []
        par_cote: dict[str, list[dict]] = defaultdict(list)
        for g in gens or []:
            sens = str((g or {}).get("sens") or "").strip().lower()
            if sens in ("entree", "sortie") and str((g or {}).get("id") or "").strip():
                par_cote[sens].append(g)
        if not par_cote:
            compte["releve vide"] += 1
            continue
        # ⚠ PLUS DE DEUX PERSONNES D'UN COTE : ON NE CONVERTIT PAS. La table n'a
        #   que deux emplacements par cote ; garder « les deux premieres » serait
        #   effacer de l'argent en silence. On nomme et on passe.
        if any(len(v) > 2 for v in par_cote.values()):
            compte["plus de deux personnes d'un cote -- NON CONVERTI"] += 1
            if len(nommes) < 5:
                nommes.append("dossier %s : %s" % (
                    chaine, " · ".join(f"{k}={len(v)}" for k, v in par_cote.items())))
            continue

        suppose = False
        bloc: list[dict] = []
        for cote, gens_du_cote in par_cote.items():
            unites = nombre(src["e"] if cote == "entree" else src["s"])
            if unites is None:
                # ⚠ 50/50 EST LA VALEUR QUE HEKTOR REND PARTOUT AILLEURS, et la
                #   supposition est JUSTE dans 205 cas sur 209 la ou elle est
                #   verifiable. Mais on ne la cache pas : l'etiquette le dit.
                unites = Decimal("50")
                suppose = True
            for rang, g in enumerate(sorted(gens_du_cote, key=lambda z: str(z.get("id"))), 1):
                part = nombre(g.get("percent"))
                if part is None:
                    part = Decimal("100")
                    suppose = True
                valeur = unites * part / Decimal("100")
                if valeur > Decimal("100"):
                    compte["plafonnee a 100 (arrondi de Hektor)"] += 1
                    valeur = Decimal("100")
                elif valeur < 0:
                    compte["negative -- NON CONVERTIE"] += 1
                    continue
                bloc.append({
                    "app_chaine_id": chaine,
                    "app_dossier_id": src["_dossier"],
                    "cote": cote,
                    "rang": rang,
                    "hektor_user_id": str(g.get("id")).strip(),
                    "nom_au_moment": (str(g.get("nom") or "").strip() or None),
                    "pourcentage": trois_decimales(valeur),
                })
        total = sum(Decimal(str(b["pourcentage"])) for b in bloc)
        if total > TOLERANCE:
            compte["total impossible -- NON CONVERTI"] += 1
            if len(nommes) < 5:
                nommes.append("dossier %s : total %s %%" % (chaine, total))
            continue
        etiquette = "hektor_partage_suppose" if suppose else "hektor"
        for b in bloc:
            b["origine"] = etiquette
        lignes.extend(bloc)
        compte[etiquette] += 1

    compte["_nommes"] = nommes  # type: ignore[assignment]
    return lignes, compte


def ecrire_local(con: sqlite3.Connection, lignes: list[dict]) -> int:
    """Remplace la table LOCALE, en une transaction.

    ⚠ UNE SEULE TRANSACTION, ET C'EST TOUT L'INTERET DU LOCAL. L'ancien
      convertisseur envoyait 67 paquets HTTP : le 15/09, le 54e a ete refuse pour
      UNE valeur a 100,001 et l'ecriture s'est arretee a 10 822 lignes sur 13 307,
      laissant la base a moitie convertie. Ici, c'est tout ou rien.
    """
    con.execute(DDL)
    con.execute("BEGIN")
    try:
        con.execute(f"DELETE FROM {CIBLE} WHERE COALESCE(origine,'') LIKE 'hektor%'")
        con.executemany(
            f"INSERT OR REPLACE INTO {CIBLE} (app_chaine_id, app_dossier_id, cote, rang, "
            "hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par) "
            "VALUES (?,?,?,?,?,?,?,?,datetime('now'),'conversion')",
            [(l["app_chaine_id"], l["app_dossier_id"], l["cote"], l["rang"],
              l["hektor_user_id"], l["nom_au_moment"], l["pourcentage"], l["origine"])
             for l in lignes])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return len(lignes)


def client() -> SupabaseRestClient | None:
    for f in DEFAULT_ENV_FILES:
        load_env_file(f)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("!! SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents", file=sys.stderr)
        return None
    return SupabaseRestClient(base_url=url, service_role_key=cle)


def pousser(cl: SupabaseRestClient, lignes: list[dict], paquet: int = 400) -> dict:
    """Envoie par la RPC, qui porte la garde. Par dossiers ENTIERS.

    ⚠ ON NE COUPE JAMAIS UN DOSSIER EN DEUX PAQUETS : la RPC remplace le dossier
      qu'elle recoit, donc un dossier arrive a moitie perdrait l'autre moitie.
    """
    par_dossier: dict[int, list[dict]] = defaultdict(list)
    for l in lignes:
        par_dossier[l["app_chaine_id"]].append(l)
    total = defaultdict(int)
    lot: list[dict] = []
    for bloc in par_dossier.values():
        if lot and len(lot) + len(bloc) > paquet:
            r = cl.request(method="POST", path="rpc/app_repartition_absorber",
                           payload={"lignes": lot})
            for k, v in (r or {}).items():
                total[k] += int(v or 0)
            lot = []
        lot.extend(bloc)
    if lot:
        r = cl.request(method="POST", path="rpc/app_repartition_absorber",
                       payload={"lignes": lot})
        for k, v in (r or {}).items():
            total[k] += int(v or 0)
    return dict(total)


def main() -> int:
    ap = argparse.ArgumentParser(description="Repartition de commission (lot 5).")
    ap.add_argument("--calculer", action="store_true", help="Ecrire la table LOCALE.")
    ap.add_argument("--pousser", action="store_true", help="Envoyer a Supabase (RPC).")
    ap.add_argument("--purger-orphelines", action="store_true",
                    help="Supprimer les lignes DERIVEES dont le dossier n'existe plus.")
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{PHASE2_DB.as_posix()}?mode=ro", uri=True)
    try:
        lignes, compte = calculer(con)
    finally:
        con.close()

    nommes = compte.pop("_nommes", [])  # type: ignore[arg-type]
    print("-- CE QUE LE CALCUL LOCAL DONNE --")
    for k, v in sorted(compte.items(), key=lambda x: -x[1]):
        print("   %-44s %6d" % (k, v))
    print("   %-44s %6d" % ("LIGNES au total", len(lignes)))
    if nommes:
        print("")
        print("-- LES DOSSIERS NON CONVERTIS, NOMMES --")
        for e in nommes:
            print("   " + e)

    if not (args.calculer or args.pousser or args.purger_orphelines):
        print("")
        print("a blanc : RIEN n'a ete ecrit. Ajouter --calculer [--pousser].")
        return 0

    if args.calculer:
        ecriture = sqlite3.connect(PHASE2_DB)
        try:
            n = ecrire_local(ecriture, lignes)
        finally:
            ecriture.close()
        print("")
        print("   table LOCALE remplacee : %d lignes" % n)

    if args.pousser or args.purger_orphelines:
        cl = client()
        if cl is None:
            return 1
        if args.purger_orphelines:
            r = cl.request(method="POST", path="rpc/app_repartition_purger_orphelines",
                           payload={})
            print("   purge des orphelines   : %s" % json.dumps(r, ensure_ascii=False))
        if args.pousser:
            r = pousser(cl, lignes)
            print("   pousse vers Supabase   : %s" % json.dumps(r, ensure_ascii=False))
            print("   ⚠ `proteges_app` compte les dossiers que l'APP possede : la base")
            print("     a refuse d'y toucher, et c'est le comportement voulu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
