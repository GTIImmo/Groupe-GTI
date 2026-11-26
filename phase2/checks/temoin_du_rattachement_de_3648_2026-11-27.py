#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE TEMOIN DU RATTACHEMENT 3648 -> 3647 -- MESURE DANS LE REGISTRE, JAMAIS LU DANS LE COMPTE RENDU. LECTURE SEULE.

    python -X utf8 -u phase2\checks\temoin_du_rattachement_de_3648_2026-11-27.py

SON MOT (26/11) : « demain matin, ne me donne pas le compte rendu de la nuit : donne-moi le temoin. Ton propre module porte
cette note, ecrite apres un echec : indexes par un entier au lieu d'un texte, les rattachements etaient ignores en silence
[...] le compte rendu disait « 6 lignes » et rien n'etait fait [...] Alors demain : 3648 est-elle reellement dans la chaine
3647, et D2024-0306 a-t-il bien fusionne ? Mesure, pas rapporte. »

⏰ A LANCER APRES 07:30 (son mot : ni le run ni la descente ne doivent tourner). Lancé AVANT la nuit qui pose la ligne, il
DOIT repondre « PAS REUNIE » -- c'est son temoin inverse, pris le 26/11.

CE QU'IL MESURE, aux deux endroits ou vit le dossier :
  ① phase2.sqlite (mode=ro), le registre MAITRE : la chaine de 3646, 3647, 3648, 3649, 3650 ;
  ② Supabase : la meme chose + l'etiquette (uuid, numero) de chaque piece ; qui porte encore D2024-0306 ; le journal des
     etiquettes (une fusion de 445c3170 dans 42dd4d66, nommant 3648) ; le compteur ;
  ③ le temoin POSITIF du mecanisme : les 16 autres rattachements du fichier sont-ils reunis, eux aussi ?
Sortie : 0 reunie et fusionnee . 1 pas (encore) reunie . 2 pas pu mesurer.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import phase2.sync.affaire_ledger as al  # noqa: E402

PIECES = (3646, 3647, 3648, 3649, 3650)
U_0511, U_0306 = "42dd4d66-eb07-47b6-85d6-8db1e7000090", "445c3170"


def main() -> int:
    ok = True
    print("① LE REGISTRE LOCAL (maitre), phase2.sqlite en lecture seule")
    lo = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    L = {int(a): int(c) for a, c in lo.execute("select app_affaire_id, app_chaine_id from app_affaire_ledger where "
                                               "app_affaire_id in (%s)" % ",".join(map(str, PIECES)))}
    print("   chaines : %s" % L)
    reunie_local = L.get(3648) == L.get(3647) == L.get(3650) == 3647 and L.get(3646) == L.get(3649) == 3646
    print("   3648 dans la chaine 3647 (et 427UDDSF sur 3646) : %s" % ("OUI" if reunie_local else "⛔ NON"))
    ok &= reunie_local
    try:
        cn, cu = P.pooler()
    except Exception as e:  # noqa: BLE001
        print("⛔ Supabase illisible (%s) -- pas de verdict (code 2)" % str(e)[:120])
        return 2
    print("\n② SUPABASE")
    cu.execute("select app_affaire_id, kind, state, app_chaine_id, app_dossier_uuid::text, app_dossier_numero "
               "from public.app_affaire_ledger where app_affaire_id = any(%s) order by 1", (list(PIECES),))
    S = {r[0]: r[1:] for r in cu.fetchall()}
    for a, r in S.items():
        print("   %s %-9s %-9s chaine %s  %s %s" % (a, r[0], r[1], r[2], r[3][:8], r[4]))
    reunie_sb = (S[3648][2] == S[3647][2] == 3647 and S[3648][3] == S[3647][3] == S[3650][3] == U_0511
                 and S[3646][3] == S[3649][3] and S[3646][3] != U_0511)
    print("   3648 en chaine 3647 ET sur D2024-0511 (42dd4d66) ; 427UDDSF a part : %s" % ("OUI" if reunie_sb else "⛔ NON"))
    ok &= reunie_sb
    cu.execute("select count(*), array_agg(app_affaire_id) from public.app_affaire_ledger where app_dossier_numero = 'D2024-0306'")
    n0306, qui = cu.fetchone()
    print("   pieces qui portent encore D2024-0306 : %d %s" % (n0306, qui or []))
    ok &= n0306 == 0
    cu.execute("select quand, evenement, dossier_numero, ancien_numero, transactions, pourquoi from "
               "public.app_dossier_etiquette_journal where (autre_uuid::text like %s or 3648 = any(transactions)) "
               "and quand > '2026-11-26' order by quand", (U_0306 + "%",))
    J = cu.fetchall()
    for r in J:
        print("   journal : %s %s %s <- %s %s (%s)" % (str(r[0])[:19], r[1], r[2], r[3], r[4], (r[5] or "")[:60]))
    fus = [r for r in J if r[1] == "fusion" and r[2] == "D2024-0511" and r[3] == "D2024-0306"]
    print("   une FUSION de D2024-0306 dans D2024-0511 au journal depuis le 26/11 : %s" % ("OUI" if fus else "⛔ NON"))
    ok &= bool(fus)
    print("\n③ LE TEMOIN POSITIF DU MECANISME : les autres rattachements du fichier, reunis dans Supabase ?")
    dec = [d for d in al.lire_rattachements_manuels() if d[0] != 3648]
    ids = sorted({x for s, c, _b, _p in dec for x in (s, c)})
    cu.execute("select app_affaire_id, app_chaine_id from public.app_affaire_ledger where app_affaire_id = any(%s)", (ids,))
    ch = dict(cu.fetchall())
    pas = [(s, c) for s, c, _b, _p in dec if ch.get(s) is None or ch.get(s) != ch.get(c)]
    print("   %d decision(s) hors 3648 : %d reunies, %d pas %s" % (len(dec), len(dec) - len(pas), len(pas), pas))
    cn.rollback()
    cn.close()
    print("\n⇒ %s" % ("✅ 3648 EST REUNIE A 3647, ET D2024-0306 A FUSIONNE DANS D2024-0511 -- mesure" if ok
                      else "⛔ PAS (ENCORE) REUNIE / FUSIONNEE -- voir ci-dessus"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
