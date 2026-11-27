"""LES TEMOINS DE LA FIN (23/11) -- LECTURE SEULE, l'image du 23/11 08:02, le socle en lecture (passage de reference).

Son message du 23/11 au soir : « Tranche par ton raisonnement tout ce que tu peux trancher [...] porte son temoin ».
T1 une ligne « Annulee » tient-elle jamais une VENTE ? (une affaire annulee n'a pas de vente)
T2 une piece prouvee a une ligne tranchee est-elle jamais datee a plus d'UN AN de toutes les cases de date de sa ligne ?
T3 l'etat d'une OFFRE prouvee par sa date exacte suit-il l'etat de sa ligne ? (refusee <-> « Annulee » ; acceptee <->
   la ligne qui continue) -- quand deux lignes ont la MEME date d'offre, l'etat les departage-t-il ?
"""
import sys, sqlite3, json
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K
sys.stdout.reconfigure(encoding="utf-8")
PASSAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 64
I = P.Image(P.IMAGES / "2026-11-23_080234"); D = I.D
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
V = {i: (v, json.loads(p or "[]"), json.loads(pr or "[]")) for i, v, p, pr in c.execute(
    "select id_unique, verdict, pieces, preuves from verdict where passage=?", (PASSAGE,))}
COLS = ["Offre Achat", "Compromis", "Signé", "Vente Prévue", "Vente Fixée", "Signée", "Vente Réglée", "Annulée"]


def etat(i):
    return D.case(i, "Etat Actuel").strip()


print("=== T1 : les lignes « Annulee » tranchees qui tiennent une VENTE")
t1 = Counter(); ex1 = []
for i, (v, ps, _pr) in V.items():
    if v != "TRANCHEE":
        continue
    a_v = [q for q in ps if q in D.REG and I.nature.get(q) == PC.VRAIE and D.REG[q]["genre"] == "vente"]
    k = ("Annulee" if etat(i).startswith("Annul") else "autre etat", "tient une vente" if a_v else "aucune vente")
    t1[k] += 1
    if a_v and k[0] == "Annulee":
        ex1.append((i, a_v))
for k, n in sorted(t1.items()):
    print("   %5d  %s" % (n, k))
print("   les Annulee qui tiennent une vente :", ex1)

print("\n=== T2 : les pieces prouvees (lignes tranchees) datees a plus d'un an de TOUTES les cases de leur ligne")
t2 = Counter(); ex2 = []
for i, (v, ps, _pr) in V.items():
    if v != "TRANCHEE":
        continue
    cases = [d for d in (K.d_sheet(D.case(i, col)) for col in COLS) if d]
    for q in ps:
        if q not in D.REG or I.nature.get(q) != PC.VRAIE or not D.REG[q]["date"]:
            continue
        if not cases:
            t2["ligne sans aucune case datee"] += 1
            continue
        ecart = min(abs((D.REG[q]["date"] - d).days) for d in cases)
        k = "plus d'un an" if ecart > 365 else ("90 j a un an" if ecart > 90 else "moins de 90 j")
        t2[k] += 1
        if ecart > 365:
            ex2.append((i, q, D.REG[q]["genre"], str(D.REG[q]["date"]), ecart))
for k, n in t2.most_common():
    print("   %5d  %s" % (n, k))
print("   les pieces a plus d'un an, toutes :", ex2)

print("\n=== T3 : l'etat d'une offre prouvee par sa date exacte, contre l'etat de sa ligne")
t3 = Counter(); ex3 = defaultdict(list)
for i, (v, ps, pr) in V.items():
    if v != "TRANCHEE":
        continue
    for q in ps:
        if q not in D.REG or I.nature.get(q) != PC.VRAIE or D.REG[q]["genre"] != "offre":
            continue
        if not any(x.startswith("%d " % q) and "= colonne « Offre Achat »" in x for x in pr):
            continue
        k = (D.REG[q]["etat"], "ligne Annulee" if etat(i).startswith("Annul") else "ligne qui continue")
        t3[k] += 1
        ex3[k].append((i, q))
for k, n in sorted(t3.items(), key=str):
    print("   %5d  %s  ex. %s" % (n, k, ex3[k][:3]))
print("\n   T3b, le cas qui compte : deux lignes du bien a la MEME date d'offre, une Annulee et une qui continue ;")
print("   l'offre REFUSEE prouvee a l'Annulee, l'ACCEPTEE a celle qui continue ?")
t3b = Counter(); ex3b = []
for b, ls in D.lignes_bien.items():
    par_date = defaultdict(list)
    for i in ls:
        d = K.d_sheet(D.case(i, "Offre Achat"))
        if d:
            par_date[d].append(i)
    for d, li in par_date.items():
        if len(li) < 2:
            continue
        offres = [q for q in D.par_bien.get(b, []) if D.REG[q]["genre"] == "offre" and D.REG[q]["date"] == d
                  and I.nature.get(q) == PC.VRAIE]
        for q in offres:
            tenue = [i for i in li if V.get(i, ("", []))[0] == "TRANCHEE" and q in V[i][1]]
            if len(tenue) != 1:
                t3b["offre tenue par %d ligne(s) du jour" % len(tenue)] += 1
                ex3b.append((b, str(d), q, D.REG[q]["etat"], li, tenue))
                continue
            L_ = tenue[0]
            attendu = "Annulee" if D.REG[q]["etat"] == "refused" else "qui continue"
            ok = (etat(L_).startswith("Annul")) == (attendu == "Annulee")
            t3b["l'etat designe la BONNE ligne" if ok else "l'etat designe une AUTRE ligne"] += 1
            if not ok:
                ex3b.append((b, str(d), q, D.REG[q]["etat"], L_, etat(L_)))
for k, n in t3b.most_common():
    print("   %5d  %s" % (n, k))
print("   details :", ex3b[:12])

print("\n=== T4 : une VENTE et le compromis ACTIF de sa chaine au meme montant -- tenus par la MEME ligne ?")
t4 = Counter(); ex4 = []
tient = defaultdict(set)
for i, (v, ps, _pr) in V.items():
    if v == "TRANCHEE":
        for q in ps:
            tient[q].add(i)
for vq in sorted(q for q in tient if q in D.REG and D.REG[q]["genre"] == "vente" and I.nature.get(q) == PC.VRAIE):
    b = D.REG[vq]["bien"]
    ch = I.pieces[vq]["app_chaine_id"]
    cps = [q for q in D.par_bien[b] if I.pieces[q]["app_chaine_id"] == ch and D.REG[q]["genre"] == "compromis"
           and D.REG[q]["etat"] == "active" and I.nature.get(q) == PC.VRAIE and D.REG[q]["montant"] is not None
           and D.REG[vq]["montant"] is not None and abs(D.REG[q]["montant"] - D.REG[vq]["montant"]) <= 1]
    if len(cps) != 1 or not tient.get(cps[0]):
        t4["pas de compromis actif unique et tenu dans sa chaine"] += 1
        continue
    k = "MEME ligne" if tient[vq] == tient[cps[0]] else "lignes DIFFERENTES"
    t4[k] += 1
    if k != "MEME ligne":
        ex4.append((vq, cps[0], sorted(tient[vq]), sorted(tient[cps[0]])))
for k, n in t4.most_common():
    print("   %5d  %s" % (n, k))
print("   les DIFFERENTES, toutes :", ex4)
