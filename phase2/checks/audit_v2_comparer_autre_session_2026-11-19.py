# -*- coding: utf-8 -*-
"""AUDIT V2, TEMPS 2 -- MON CALCUL CONTRE CELUI DE L'AUTRE SESSION. 19/11/2026.

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\audit_v2_comparer_autre_session_2026-11-19.py

⛔ LECTURE SEULE. Ouvert APRES mes commits ce2301e (calcul arrete) et 6c2979c (verdict
  sur le gel, v1.1). Lit : mon CSV, mon verdict sur le gel, le gel de Supabase verifie a
  l'empreinte, et les deux CSV de l'autre session (verdicts, operations).

Pour chacune de ses 141 operations : mon calcul la SOUTIENT, la CONTREDIT, ou n'en dit
RIEN -- et dans les deux derniers cas, la MEME regle (juger_tx) mesure les deux preuves.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
CK = RACINE / "phase2" / "checks"
N = RACINE / "notice"
_spec = importlib.util.spec_from_file_location("apparieur_v2", CK / "audit_v2_apparier_2026-11-19.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)          # rejoue mon appariement v1.1 (identique a l'octet)


def lire(nom):
    return list(csv.DictReader(open(N / nom, encoding="utf-8-sig"), delimiter=";"))


MOI = {r["id_unique"]: r for r in lire("AUDIT_INDEPENDANT_V2_MON_APPARIEMENT_2026-11-19.csv")}
MV = {r["id_unique"]: r for r in lire("AUDIT_INDEPENDANT_V2_GEL_CONTRE_MOI_2026-11-19.csv")}
SV = {r["id_unique"]: r for r in lire("AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv")}
OPS = lire("AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv")
GEL = json.loads((RACINE / ".tmp" / "audit_v2_2026-11-19" / "gel_supabase_19-11.json").read_text(encoding="utf-8"))
ROLES = ("offre", "compromis", "vente")

ma_ligne_de_tx = {}
for iu, r in MOI.items():
    for k in ROLES:
        if r[k]:
            ma_ligne_de_tx[int(r[k])] = iu


def preuve(iu, tid):
    if tid in A.C5:
        return None, "creee par C5"
    t = A.TX.get(tid)
    L = A.LIGNE_DE.get(iu)
    if not t or not L:
        return None, "inconnue"
    sc, pr = A.juger_tx(L, t)
    return sc, ", ".join(pr)


def mon_tx(iu, role):
    v = MOI.get(iu, {}).get(role)
    return int(v) if v else None


resultat = []
cpt = Counter()
for o in OPS:
    iu, role, op = o["id_unique"], o["role"], o["operation"]
    de = int(o["de"]) if o["de"] else None
    vers = int(o["vers"]) if o["vers"] else None
    m = mon_tx(iu, role)
    avis = []
    # le retrait (retirer, ou la moitie « de » d'un deplacement)
    if de is not None:
        if m == de:
            avis.append("CONTRE_LE_RETRAIT")       # je garde ce lien pour cette ligne
        elif de in A.C5:
            avis.append("pour_le_retrait(c5)")     # une copie de C5 : hors de mes candidats
        else:
            avis.append("pour_le_retrait")
    if vers is not None:
        if m == vers:
            avis.append("pour_l_ajout")
        elif ma_ligne_de_tx.get(vers) and ma_ligne_de_tx[vers] != iu:
            avis.append("CONTRE_L_AJOUT(je->%s)" % ma_ligne_de_tx[vers])
        elif m is not None:
            avis.append("CONTRE_L_AJOUT(j'ai %s)" % m)
        else:
            avis.append("silence_sur_l_ajout")     # je n'attribue cette transaction a personne
    accord = ("D_ACCORD" if all(a.startswith("pour") for a in avis)
              else "CONTRE" if any(a.startswith("CONTRE") for a in avis) else "PARTIEL_SILENCE")
    cpt[(op, accord)] += 1
    sd = preuve(iu, de) if de else (None, "")
    sv = preuve(iu, vers) if vers else (None, "")
    sm = preuve(iu, m) if m and m not in (de, vers) else (None, "")
    resultat.append({"operation": op, "id_unique": iu, "role": role, "de": de or "", "vers": vers or "",
                     "mon_choix": m or "", "mon_avis": " ".join(avis), "accord": accord,
                     "sa_confiance": o["confiance"], "son_verdict": o["verdict"],
                     "ma_certitude": MOI.get(iu, {}).get("certitude", ""),
                     "preuve_de": "%s [%s]" % (sd[1], sd[0]) if de else "",
                     "preuve_vers": "%s [%s]" % (sv[1], sv[0]) if vers else "",
                     "preuve_mon_choix": "%s [%s]" % (sm[1], sm[0]) if sm[1] else "",
                     "sa_raison": o["raison"][:300]})

with open(N / "AUDIT_INDEPENDANT_V2_SES_OPERATIONS_JUGEES_2026-11-19.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(resultat[0].keys()), delimiter=";")
    w.writeheader()
    w.writerows(resultat)

print("\nSES 141 OPERATIONS, JUGEES PAR MON CALCUL :")
for (op, acc), n in sorted(cpt.items()):
    print("  %-10s %-16s %4d" % (op, acc, n))

# ── ses 350 verdicts contre les miens
croise = Counter()
for iu, s in SV.items():
    croise[(s["verdict"], MV[iu]["mon_verdict_sur_le_gel"] if iu in MV else "(ligne inconnue de moi)")] += 1
print("\nSES 350 VERDICTS (lui) contre MON VERDICT SUR LE GEL (moi) :")
for (a, b), n in sorted(croise.items(), key=lambda x: (x[0][0], -x[1])):
    print("  %-26s %-40s %4d" % (a, b, n))

# ── ce que j'ai trouve et que son patch ne touche pas
touchees = {o["id_unique"] for o in OPS}
hors = Counter()
hors_liste = defaultdict(list)
for iu, r in MV.items():
    v = r["mon_verdict_sur_le_gel"]
    if v in ("JUSTE", "JUSTE_JUMEAU") or iu in touchees:
        continue
    jugee = "jugee_par_lui(%s)" % SV[iu]["verdict"] if iu in SV else "NON_JUGEE_PAR_LUI"
    hors[(v, jugee.split("(")[0])] += 1
    hors_liste[(v, jugee)].append(iu)
print("\nMES CONSTATS SUR DES LIGNES QUE SON PATCH NE TOUCHE PAS :")
for (v, j), n in sorted(hors.items(), key=lambda x: -x[1]):
    print("  %-40s %-20s %4d" % (v, j, n))
(RACINE / ".tmp" / "audit_v2_2026-11-19" / "hors_patch.json").write_text(
    json.dumps({"%s|%s" % k: v for k, v in hors_liste.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
print("\necrit : notice/AUDIT_INDEPENDANT_V2_SES_OPERATIONS_JUGEES_2026-11-19.csv")
