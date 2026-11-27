"""JUGER UN PASSAGE CONTRE SA BASE (23/11) -- LECTURE SEULE sur le socle. Le critere de son message du 23/11 : « construis
ta regle, porte son temoin, verifie qu'aucun verdict rendu ne bouge, et avance ».

  python protocole_juger_un_passage_2026-11-23.py <base> <nouveau>

Dit, sans rien moyenner :
  1 les lignes RENDUES dans la base (TRANCHEE) dont l'etiquette, les pieces ou les preuves changent -- nommees une a une ;
  2 les temoins, ligne par ligne : ce qui change, ecart par ecart ;
  3 les verdicts qui changent (motif -> motif) et les nouvelles tranchees, avec le numero qu'elles prendraient et leur
    numero du 16/11 quand elles sont dans les 2 560 (le CSV de la sentinelle du passage 54 -- les numeros du 16/11 ne
    dependent pas du passage).
Sortie 0 = aucun verdict rendu ne bouge (etiquette, pieces) et aucun ecart de temoin nouveau ; 1 sinon.
"""
import sys, sqlite3, json, csv
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
p1, p2 = int(sys.argv[1]), int(sys.argv[2])
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
r2 = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/images/2026-11-23_080234/registre.sqlite?mode=ro",
                     uri=True)
num = {u: n for u, n in r2.execute("select distinct app_dossier_uuid, app_dossier_numero from app_affaire_ledger")}
av = {r["id_unique"]: r["numero_du_16_11"] for r in csv.DictReader(open(
    r"C:/Hektor/Projet/notice/PROTOCOLE_TEMOIN_AVIS_LES_2560_NUMEROS_PASSAGE_54_2026-11-22.csv", encoding="utf-8-sig"),
    delimiter=";")}
q = "select id_unique, verdict, etiquette, pieces, preuves, motif, motif_texte from verdict where passage=?"
A = {r[0]: r[1:] for r in c.execute(q, (p1,))}
B = {r[0]: r[1:] for r in c.execute(q, (p2,))}
mauvais = 0
print("JUGER %d -> %d : %d / %d lignes" % (p1, p2, len(A), len(B)))
rendues = [i for i in A if A[i][0] == "TRANCHEE"]
ch_et = [i for i in rendues if B[i][0] != "TRANCHEE" or A[i][1] != B[i][1]]
ch_pc = [i for i in rendues if A[i][2] != B[i][2]]
ch_pr = [i for i in rendues if A[i][3] != B[i][3] and i not in ch_pc]
print("1 RENDUES (%d) : verdict ou etiquette change %d ; pieces changent %d ; seules les preuves changent %d"
      % (len(rendues), len(ch_et), len(ch_pc), len(ch_pr)))
for i in ch_et + ch_pc:
    mauvais += 1
    print("   ⛔ %s : %s %s %s -> %s %s %s" % (i, A[i][0], A[i][1], A[i][2], B[i][0], B[i][1], B[i][2]))
for i in ch_pr:
    a_, b_ = json.loads(A[i][3] or "[]"), json.loads(B[i][3] or "[]")
    print("   preuve %s : %s -> %s" % (i, [x[:110] for x in a_ if x not in b_], [x[:110] for x in b_ if x not in a_]))
ta = {(t, i): (x, y, e) for t, i, x, y, e in c.execute("select temoin, id_unique, attendu, obtenu, ecart from temoin "
                                                       "where passage=?", (p1,))}
tb = {(t, i): (x, y, e) for t, i, x, y, e in c.execute("select temoin, id_unique, attendu, obtenu, ecart from temoin "
                                                       "where passage=?", (p2,))}
diff = sorted(k for k in set(ta) | set(tb) if ta.get(k) != tb.get(k))
nouv_ec = [k for k in diff if (tb.get(k) or (0, 0, 0))[2] == 1]
print("2 TEMOINS : %d lignes, %d changent ; ecarts %d -> %d ; ECARTS NOUVEAUX %d"
      % (len(tb), len(diff), sum(1 for v in ta.values() if v[2] == 1), sum(1 for v in tb.values() if v[2] == 1), len(nouv_ec)))
for k in diff:
    print("   %s %s : %s -> %s" % ("⛔" if k in nouv_ec else " ", k, ta.get(k), tb.get(k)))
mauvais += len(nouv_ec)
chg = [i for i in A if (A[i][0], A[i][4]) != (B[i][0], B[i][4])]
print("3 VERDICTS QUI CHANGENT : %d" % len(chg))
for k, n in Counter((A[i][4] or A[i][0], B[i][4] or B[i][0]) for i in chg).most_common():
    print("   %-26s -> %-26s %4d" % (k[0], k[1], n))
for i in sorted(i for i in chg if B[i][0] == "TRANCHEE"):
    e = B[i][1]
    print("   + %-9s %-24s -> %-14s 16/11 : %s" % (i, json.loads(B[i][2] or "[]"), num.get(e, e), av.get(i, "-")))
for i in sorted(i for i in chg if B[i][0] != "TRANCHEE"):
    print("   ~ %-9s %s -> %s : %s" % (i, A[i][4] or A[i][0], B[i][4], (B[i][5] or "")[:120]))
n1 = c.execute("select tranchees, en_attente from passage where id=?", (p1,)).fetchone()
n2 = c.execute("select tranchees, en_attente from passage where id=?", (p2,)).fetchone()
r1 = sum(1 for v in A.values() if v[0] == "ATTENTE" and v[4] != "RIEN_A_ETIQUETER")
r2_ = sum(1 for v in B.values() if v[0] == "ATTENTE" and v[4] != "RIEN_A_ETIQUETER")
print("4 TRANCHEES %s -> %s ; RESTE A VIDER %d -> %d" % (n1[0], n2[0], r1, r2_))
print("VERDICT DU JUGE :", "AUCUN verdict rendu ne bouge, aucun ecart de temoin nouveau" if not mauvais else
      "⛔ %d probleme(s) -- voir ci-dessus" % mauvais)
sys.exit(0 if not mauvais else 1)
