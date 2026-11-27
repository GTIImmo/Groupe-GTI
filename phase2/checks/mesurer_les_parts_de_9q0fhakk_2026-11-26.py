#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LES PARTS DE LA CHAINE DE 9Q0FHAKK (3647) ET DE SA VOISINE (3646) -- LECTURE SEULE, ⛔ RIEN N'EST ECRIT.

    python -X utf8 -u phase2\checks\mesurer_les_parts_de_9q0fhakk_2026-11-26.py

SON MOT (26/11 au matin) : « Le run a pose cette nuit 50 % en entree et 50 % en sortie pour GENTES sur la chaine 3647,
celle de 9Q0FHAKK, en partage suppose. Or mon classeur dit DECHAUD 50 et GENTES 50 sur cette ligne [...] 9Q0FHAKK passe
donc en premier » ; « ses deux parts doivent porter DECHAUD 50 et GENTES 50, comme mon classeur, et plus une
supposition. Dis-moi comment tu t'y prendrais, sans rien ecrire. »

CE QU'IL LIT (Supabase, apres la descente) : les parts des chaines 3646 et 3647 (cote, rang, negociateur, pourcentage,
ORIGINE -- le verrou -- ecrit_le, ecrit_par) ; les memes chaines dans les sauvegardes d'avant la vague du 25/11 ; ce qui en a
ete mis de cote ; les pieces des deux chaines ; ce que la nuit a ecrit dans tout le registre des parts aujourd'hui.
"""
from __future__ import annotations

import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

CHAINES = (3646, 3647)
COLS = "app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_le::text, ecrit_par"


def main() -> int:
    cn, cu = P.pooler()

    def q(s, a=()):
        cu.execute(s, a)
        return cu.fetchall()
    print("① LES PIECES DES DEUX CHAINES (aujourd'hui)")
    for r in q("select app_affaire_id, kind, state, left(date, 10), app_chaine_id, app_dossier_numero, "
               "coalesce(vente_reglee_app, ''), honoraires_entree from public.app_affaire_ledger "
               "where app_chaine_id in %s or app_affaire_id between 3646 and 3650 order by 1", (CHAINES,)):
        print("   ", r)
    print("\n② LES PARTS D'AUJOURD'HUI (app_affaire_repartition)")
    for r in q("select %s from public.app_affaire_repartition where app_chaine_id in %%s order by 1, 2, 3" % COLS, (CHAINES,)):
        print("   ", r)
    print("\n③ LES MEMES CHAINES AVANT LA VAGUE DU 25/11 (les sauvegardes datees)")
    for t in [x[0] for x in q("select table_name from information_schema.tables where table_schema = 'public' and "
                               "table_name like 'app_affaire_repartition%%' order by 1")]:
        if t == "app_affaire_repartition":
            continue
        cols = {x[0] for x in q("select column_name from information_schema.columns where table_schema = 'public' and "
                                 "table_name = %s", (t,))}
        cle = "app_chaine_id" if "app_chaine_id" in cols else None
        if not cle:
            continue
        extra = " or ancien_app_chaine_id in %s" if "ancien_app_chaine_id" in cols else ""
        args = (CHAINES, CHAINES) if extra else (CHAINES,)
        rs = q("select * from public.%s where app_chaine_id in %%s%s" % (t, extra), args)
        if rs:
            print("   %s : %d ligne(s)" % (t, len(rs)))
            for r in rs:
                print("       ", tuple(str(x)[:60] for x in r))
    print("\n④ CE QUE LA NUIT A ECRIT AUJOURD'HUI dans le registre des parts")
    for r in q("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, "
               "ecrit_le::text, ecrit_par from public.app_affaire_repartition where ecrit_le >= '2026-11-26' "
               "order by ecrit_le, 1, 2, 3"):
        print("   ", r)
    print("\n⑤ L'ANNUAIRE : DECHAUD et GENTES")
    for t in ("app_negociateur", "app_hektor_user", "app_negociateur_registre"):
        if q("select to_regclass(%s)", ("public." + t,))[0][0]:
            cols = [x[0] for x in q("select column_name from information_schema.columns where table_schema='public' and "
                                     "table_name=%s order by ordinal_position", (t,))]
            print("   %s : %s" % (t, cols[:12]))
    for r in q("select distinct hektor_user_id, nom_au_moment from public.app_affaire_repartition where "
               "upper(nom_au_moment) like '%%DECHAUD%%' or upper(nom_au_moment) like '%%GENTES%%' order by 1"):
        print("   dans les parts :", r)
    cn.rollback()
    cn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
