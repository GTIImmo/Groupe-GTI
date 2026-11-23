#!/usr/bin/env python
"""LES 26 REPARTITIONS ORPHELINES DE L'ALERTE data.repartition_orpheline -- MA MESURE, INDEPENDANTE.     23/11/2026

    python -u -X utf8 phase2/checks/mesurer_les_26_orphelines_2026-11-23.py

SON MOT DU 23/11 (8), repris a son compte par Frederic, § 4 point 2 : « UNE MESURE, EN LECTURE SEULE, sur les 26 : pour
chaque paire ancien -> nouveau, les deux cotes, le nom, le pourcentage et l'origine, et le verdict « doublon de notre
copie » / « les deux copies divergent ». FAIS LA TIENNE SANS REGARDER LA MIENNE. »

CE QU'IL FAIT -- LECTURE SEULE (REPEATABLE READ, READ ONLY), rien n'est ecrit en base :
  1. les orphelines : les parts de app_affaire_repartition dont l'app_chaine_id ne porte plus AUCUNE transaction (la
     definition meme de la vue app_v_repartition_orpheline, relue le 23/11) ;
  2. pour chaque dossier disparu X, LE DOSSIER D'ARRIVEE comme la purge de nuit (app_repartition_purger_orphelines) le
     trouve : X est le numero de sa plus petite transaction -> la transaction X vit-elle, et dans quel dossier ;
  3. les parts du dossier d'arrivee, et la comparaison COTE PAR COTE, RANG PAR RANG, sur (numero du negociateur, nom,
     pourcentage). L'ORIGINE EST MONTREE, PAS COMPAREE -- la meme forme que sa regle du 22/11 (regle 6, carnet § 19.5) ;
  4. le journal des etiquettes : ce que la nuit a fait au dossier d'arrivee (fusion, combien d'etiquettes absorbees, et
     leurs ANCIENS NUMEROS -- la colonne du patch de cette nuit).
CODES : 0 mesure faite . 2 pas pu lire.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
SORTIE = RACINE / "notice" / "LES_26_ORPHELINES_MA_MESURE_2026-11-23.csv"


def dire(s: str = "") -> None:
    print(s, flush=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    import sauvegarde_datee_classeur as S
    try:
        cn, cu = S.connexion()
    except Exception as e:  # noqa: BLE001
        dire("⛔ pas pu se connecter (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    try:
        cu.execute("select r.app_chaine_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment, r.pourcentage, r.origine, "
                   "to_char(r.ecrit_le at time zone 'Europe/Paris', 'DD/MM/YYYY HH24:MI'), r.ecrit_par "
                   "from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l "
                   "where l.app_chaine_id = r.app_chaine_id) order by 1, 2, 3")
        orph = cu.fetchall()
        cu.execute("select count(*) from public.app_v_repartition_orpheline")
        vue = cu.fetchone()[0]
        xs = sorted({r[0] for r in orph})
        arrivee = {}
        if xs:
            cu.execute("select app_affaire_id, app_chaine_id, app_dossier_numero, app_dossier_uuid::text, kind "
                       "from public.app_affaire_ledger where app_affaire_id = any(%s)", (xs,))
            arrivee = {a: (c, n, u, k) for a, c, n, u, k in cu.fetchall()}
        chaines_arr = sorted({v[0] for v in arrivee.values()})
        parts_arr = defaultdict(list)
        membres = defaultdict(list)
        if chaines_arr:
            cu.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, "
                       "to_char(ecrit_le at time zone 'Europe/Paris', 'DD/MM/YYYY HH24:MI') "
                       "from public.app_affaire_repartition where app_chaine_id = any(%s) order by 1, 2, 3", (chaines_arr,))
            for r in cu.fetchall():
                parts_arr[r[0]].append(r)
            cu.execute("select app_chaine_id, app_affaire_id, kind from public.app_affaire_ledger "
                       "where app_chaine_id = any(%s) order by 1, 2", (chaines_arr,))
            for c, a, k in cu.fetchall():
                membres[c].append("%s %s" % (a, k))
        uuids = sorted({v[2] for v in arrivee.values() if v[2]})
        journal = defaultdict(list)
        if uuids:
            cu.execute("select dossier_uuid::text, id, to_char(quand at time zone 'Europe/Paris', 'DD/MM HH24:MI'), "
                       "evenement, dossier_numero, ancien_numero from public.app_dossier_etiquette_journal "
                       "where dossier_uuid::text = any(%s) or autre_uuid::text = any(%s) order by id", (uuids, uuids))
            for u, i, q, ev, n, an in cu.fetchall():
                journal[u].append((i, q, ev, n, an))
        cn.rollback()
    finally:
        cn.close()

    par_x = defaultdict(list)
    for r in orph:
        par_x[r[0]].append(r)
    dire("LES ORPHELINES (lecture seule) : %d parts sur %d dossiers disparus ; la vue app_v_repartition_orpheline en "
         "compte %d" % (len(orph), len(par_x), vue))
    dire("   origines : %s" % dict(sorted(defaultdict(int, {o: sum(1 for r in orph if r[6] == o)
                                                           for o in {r[6] for r in orph}}).items())))
    dire("   ecrites : %s" % sorted({r[7][:10] for r in orph}))
    lignes_csv, verdicts = [], defaultdict(list)
    for x in xs:
        ps = par_x[x]
        a = arrivee.get(x)
        if not a:
            v = "PERDUE -- la transaction %s n'existe plus" % x
            verdicts["perdue"].append(x)
            dire("\n%s : %s" % (x, v))
            continue
        c_arr, num, uuid, kind = a
        pa = [p for p in parts_arr.get(c_arr, []) if not str(p[6] or "").startswith("hektor")]
        cle = lambda p: (p[1], p[2], p[3], p[4], float(p[5]))   # noqa: E731
        identiques = sorted(map(cle, ps)) == sorted(map(cle, pa))
        if not pa:
            v = "RAMENABLE -- le dossier d'arrivee n'a aucune part non Hektor (la purge aurait du la ramener)"
            verdicts["ramenable"].append(x)
        elif identiques:
            v = "DOUBLON DE NOTRE COPIE -- les memes parts des deux cotes"
            verdicts["doublon"].append(x)
        else:
            v = "LES DEUX COPIES DIVERGENT"
            verdicts["divergent"].append(x)
        fus = [j for j in journal.get(uuid, []) if j[2] == "fusion"]
        dire("\n%s -> dossier d'arrivee %s (etiquette %s, transaction %s = %s) : %s" % (
            x, c_arr, num, x, kind, v))
        dire("   membres du dossier d'arrivee : %s" % ", ".join(membres.get(c_arr, [])))
        for p in ps:
            dire("   ORPHELINE  %-7s rang %s  %-30s %6s %%  origine %-22s ecrite %s" % (
                p[1], p[2], "%s (%s)" % (p[4], p[3]), p[5], p[6], p[7]))
        for p in parts_arr.get(c_arr, []):
            dire("   EN PLACE   %-7s rang %s  %-30s %6s %%  origine %-22s ecrite %s" % (
                p[1], p[2], "%s (%s)" % (p[4], p[3]), p[5], p[6], p[7]))
        for j in fus:
            dire("   journal : ligne %s du %s, fusion -> %s, ANCIEN NUMERO %s" % (j[0], j[1], j[3], j[4]))
        for p in ps:
            lignes_csv.append({"dossier_disparu": x, "dossier_arrivee": c_arr, "etiquette_arrivee": num,
                               "cote": p[1], "rang": p[2], "orpheline_nego": p[3], "orpheline_nom": p[4],
                               "orpheline_pct": p[5], "orpheline_origine": p[6], "orpheline_ecrite": p[7],
                               "en_place": " | ".join("%s r%s %s (%s) %s%% %s" % (q[1], q[2], q[4], q[3], q[5], q[6])
                                                      for q in parts_arr.get(c_arr, [])),
                               "verdict": v.split(" --")[0],
                               "fusions_au_journal": " | ".join("%s %s -> %s ancien %s" % (j[1], j[2], j[3], j[4])
                                                                for j in fus)})
    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes_csv[0].keys()) if lignes_csv else ["vide"], delimiter=";")
        w.writeheader()
        w.writerows(lignes_csv)
    dire("\nVERDICT : %d dossier(s) disparu(s) -- doublon de notre copie %d %s ; les deux copies divergent %d %s ; "
         "ramenable %d %s ; perdue %d %s" % (len(xs), len(verdicts["doublon"]), verdicts["doublon"],
                                            len(verdicts["divergent"]), verdicts["divergent"],
                                            len(verdicts["ramenable"]), verdicts["ramenable"],
                                            len(verdicts["perdue"]), verdicts["perdue"]))
    dire("   parts : %d orphelines, dont %d dans les doublons" % (
        len(orph), sum(len(par_x[x]) for x in verdicts["doublon"])))
    dire("-> %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
