"""L hypothese des avoirs (23/11) : BR8ZTN5F et JZ9693S0 ont-elles un motif commun ? LECTURE SEULE.

Sa consigne : « Hypothese, pas conclusion : mesure-la. » La forme de la suite comptable (facture / avoir / refacture),
le temoin inverse (les « Annulee » qui portent une facture), et les pieces aux honoraires negatifs. Carnet : 20.29.
"""
import sys, sqlite3, json, re
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, coupe_preuve_interne as K
I = P.Image(P.IMAGES / "2026-11-23_080234"); D = I.D
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
V = {i: (v, m, json.loads(pc) if pc else []) for i, v, m, pc in c.execute("select id_unique, verdict, motif, pieces from verdict where passage=47")}
def suite(f):
    return [("AVR" if t.upper().startswith("AVR") else "FAC") for t in re.findall(r"(?i)(?:GGTI|AVR)\d{5,}", f)]
cpt = Counter(); ex = defaultdict(list)
for i in D.LIG:
    f = D.case(i, "Numéro de facture")
    s = suite(f)
    if "AVR" not in s: continue
    forme = "facture puis avoir, SANS refacture" if s[-1] == "AVR" else "facture, avoir, puis REFACTURE"
    k = (forme, D.case(i, "Etat Actuel"), V[i][0], V[i][1] or "")
    cpt[k] += 1; ex[k].append((i, f[:45]))
print("=== LES 260 LIGNES A AVOIR, PAR LA FORME DE LEUR SUITE DE PIECES COMPTABLES")
for k, n in sorted(cpt.items(), key=lambda kv: -kv[1]):
    print("   %4d  %s | ex. %s" % (n, k, ex[k][:3]))
print("\n=== TEMOIN INVERSE : les lignes « Annulee » qui portent une FACTURE (GGTI) sans avoir")
ann_fac = [i for i in D.LIG if D.case(i, "Etat Actuel") == "Annulée" and "FAC" in suite(D.case(i, "Numéro de facture")) and "AVR" not in suite(D.case(i, "Numéro de facture"))]
print("   ", len(ann_fac), [(i, D.case(i, "Numéro de facture")[:40], V[i][:2]) for i in ann_fac[:12]])
print("\n=== Les deux lignes rapprochees")
for i in ("BR8ZTN5F", "JZ9693S0", "75EZY5GJ"):
    print("   %s : Etat %s | facture %r | Prix %s | Commission %s | Offre %s | Compromis %s | verdict %s | pieces %s" % (
        i, D.case(i, "Etat Actuel"), D.case(i, "Numéro de facture"), D.case(i, "Prix"), D.case(i, "Commission TTC"),
        D.case(i, "Offre Achat"), D.case(i, "Compromis"), V[i][:2], [(a, D.REG[a]["genre"], D.REG[a]["etat"], D.REG[a]["montant"], D.REG[a]["hon"]) for a in V[i][2] if a in D.REG]))
for a in (7176, 16806):
    r = D.REG[a]; print("   piece %s : bien %s %s %s du %s montant %s honoraires calcules %s" % (a, r["bien"], r["genre"], r["etat"], r["date"], r["montant"], r["hon"]))
