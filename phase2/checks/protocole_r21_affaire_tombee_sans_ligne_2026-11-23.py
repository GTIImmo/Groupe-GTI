"""R21, L'AFFAIRE TOMBEE SANS LIGNE -- son temoin (23/11). LECTURE SEULE : l'image du 23/11 08:02, le socle en lecture.

Son mot (20) proposait « complete + montant d'aucune ligne » ; son temoin inverse (§ 20.32) l'a refute : 6 des 48 paires au
montant d'aucune ligne sont TENUES par une ligne tranchee. Je cherche un critere SANS contre-exemple.

UNE AFFAIRE TOMBEE COMPLETE : un compromis ANNULE et une offre REFUSEE au meme montant, sur le meme bien, chacun l'unique
partenaire de l'autre a ce montant.
LE CRITERE STRICT « SANS AUCUN LIEN » avec les lignes du bien :
  l1 son montant n'est ni le Prix ni une offre prouvee d'aucune ligne (a 1 EUR) ;
  l2 les honoraires du compromis ne sont la Commission d'aucune ligne ;
  l3 la date de l'offre est a plus de 30 jours de toute case « Offre Achat » ; celle du compromis (si datee) n'est sur
     aucune case « Compromis » ;
  l4 aucune ligne du bien ne les tient au gel du 16/11.
LE TEMOIN : sur toute l'image, les paires au critere strict, sur un bien QUI A des lignes -- combien sont tenues par une
ligne tranchee (passage de reference) ? Il doit etre ZERO, avec son temoin positif : les paires AVEC un lien, tenues par
la ligne du lien.
"""
import sys, sqlite3, json
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K
sys.stdout.reconfigure(encoding="utf-8")
PASSAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 62
I = P.Image(P.IMAGES / "2026-11-23_080234"); D = I.D
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
V = {i: (v, json.loads(p or "[]")) for i, v, p in c.execute("select id_unique, verdict, pieces from verdict where passage=?",
                                                              (PASSAGE,))}
tient = defaultdict(set)
for i, (v, ps) in V.items():
    if v == "TRANCHEE":
        for q in ps:
            tient[q].add(i)
paires = []
for b, ids in D.par_bien.items():
    cps = [q for q in ids if D.REG[q]["genre"] == "compromis" and D.REG[q]["etat"] == "cancelled" and I.nature[q] == PC.VRAIE
           and D.REG[q]["montant"] is not None]
    ofs = [q for q in ids if D.REG[q]["genre"] == "offre" and D.REG[q]["etat"] == "refused" and I.nature[q] == PC.VRAIE
           and D.REG[q]["montant"] is not None]
    for cp in cps:
        o_ = [o for o in ofs if abs(D.REG[o]["montant"] - D.REG[cp]["montant"]) <= 1]
        if len(o_) == 1 and len([x for x in cps if abs(D.REG[x]["montant"] - D.REG[o_[0]]["montant"]) <= 1]) == 1:
            paires.append((b, cp, o_[0]))


def liens(b, cp, o):
    ls = D.lignes_bien.get(b, set())
    mt = D.REG[cp]["montant"]
    out = []
    for i in ls:
        if any(abs(mt - x) <= 1 for x in D.offres_de_la_ligne(i, b)):
            out.append("l1 montant de %s" % i)
        com = P.nombre_case(D.case(i, "Commission TTC"))
        if D.REG[cp]["hon"] is not None and com is not None and abs(D.REG[cp]["hon"] - com) <= 1:
            out.append("l2 honoraires = Commission de %s" % i)
        do = K.d_sheet(D.case(i, "Offre Achat"))
        if do and D.REG[o]["date"] and abs((D.REG[o]["date"] - do).days) <= 30:
            out.append("l3 offre a %d j de %s" % (abs((D.REG[o]["date"] - do).days), i))
        dc = K.d_sheet(D.case(i, "Compromis"))
        if dc and D.REG[cp]["date"] and D.REG[cp]["date"] == dc:
            out.append("l3 compromis sur la case de %s" % i)
    for q in (cp, o):
        for i in I.gel_par_piece.get(q, []):
            if i in ls:
                out.append("l4 gel %d -> %s" % (q, i))
    return out


print("=== R21 : %d affaires tombees completes (paire unique au montant) ; passage de reference %d" % (len(paires), PASSAGE))
k = Counter(); ex = defaultdict(list)
for b, cp, o in paires:
    if not D.lignes_bien.get(b):
        k["bien SANS ligne"] += 1
        continue
    li = liens(b, cp, o)
    t = tient.get(cp, set()) | tient.get(o, set())
    cle = ("AVEC un lien" if li else "SANS AUCUN LIEN (le critere strict)",
           "tenue par une ligne tranchee" if t else "tenue par aucune")
    k[cle] += 1
    ex[cle].append((b, cp, o, sorted(t), li[:3]))
for cle, n in sorted(k.items(), key=str):
    print("   %5d  %s" % (n, cle))
print("\n   LE ZERO ET SES RATEES -- sans aucun lien MAIS tenues :", ex[("SANS AUCUN LIEN (le critere strict)",
                                                                       "tenue par une ligne tranchee")])
print("   sans aucun lien, tenues par aucune (ce que la regle mettrait de cote si elles retiennent une ligne) :",
      [(b, cp, o) for b, cp, o, _t, _l in ex[("SANS AUCUN LIEN (le critere strict)", "tenue par aucune")]])
print("   ex. AVEC un lien et tenues :", ex[("AVEC un lien", "tenue par une ligne tranchee")][:4])
print("\n   les deux affaires du verrou :")
for b, cp, o in paires:
    if cp in (11204, 24649):
        print("     bien %s : %d + %d -> liens %s" % (b, cp, o, liens(b, cp, o) or "AUCUN"))
