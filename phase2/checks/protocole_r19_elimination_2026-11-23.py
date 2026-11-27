"""R19, L'ELIMINATION -- son temoin positif (23/11). LECTURE SEULE : l'image du 23/11 08:02, le socle en lecture.

Son message du 23/11 : « Tranche par ton raisonnement tout ce que tu peux trancher. Pour chaque paquet, construis ta regle,
porte son temoin, verifie qu'aucun verdict rendu ne bouge, et avance. [...] mesure l'elimination maintenant ».

LA REGLE : une vraie piece A PART dont le prix + honoraires designent PLUSIEURS lignes (critere 1) va a la SEULE d'entre
elles qui ne tient AUCUNE vraie piece de son genre, quand TOUTES les autres tiennent deja une vraie piece de son genre AU
MEME prix + honoraires (une affaire n'a qu'un compromis -- ou qu'une offre -- a ce prix).

LE TEMOIN : chaque vraie piece TENUE par une ligne tranchee (passage 58, v9) dont le prix + honoraires designent au moins
deux lignes du bien -- on la fait comme si elle etait a part, et on rejoue l'elimination sur ce que les AUTRES lignes
tiennent : designe-t-elle la ligne qui la tient ? (la bonne / une autre / s'abstient)
"""
import sys, sqlite3, json
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC
sys.stdout.reconfigure(encoding="utf-8")
PASSAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 58
I = P.Image(P.IMAGES / "2026-11-23_080234"); D = I.D
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
V = {i: (v, json.loads(p or "[]")) for i, v, p in c.execute("select id_unique, verdict, pieces from verdict where passage=?",
                                                              (PASSAGE,))}
tient = defaultdict(set)
for i, (v, ps) in V.items():
    if v == "TRANCHEE":
        for q in ps:
            tient[q].add(i)


def vraies_de(i, sauf):
    return [q for q in (V[i][1] if V.get(i, ("", []))[0] == "TRANCHEE" else []) if q != sauf and I.nature.get(q) == PC.VRAIE]


def eliminer(a, sauf=None):
    """Rend (ligne | None, raison) sur ce que les lignes tranchees tiennent (sans `sauf`)."""
    r = D.REG[a]
    b = r["bien"]
    cands = sorted(i for i in D.lignes_bien.get(b, set()) if D.touche_ph(a, i) and not D.contre_dates(a, {i}))
    if len(cands) < 2:
        return None, "moins de deux candidates"
    pourvue = {i: [q for q in vraies_de(i, sauf) if D.REG[q]["genre"] == r["genre"] and D.REG[q]["montant"] == r["montant"]
                   and D.REG[q]["hon"] == r["hon"]] for i in cands}
    libre = [i for i in cands if not [q for q in vraies_de(i, sauf) if D.REG[q]["genre"] == r["genre"]]]
    if len(libre) == 1 and all(pourvue[i] for i in cands if i != libre[0]):
        return libre[0], "elimination"
    return None, "s'abstient (%d libre(s), %d pourvue(s) sur %d)" % (len(libre), sum(1 for i in cands if pourvue[i]), len(cands))


print("=== LE TEMOIN DE R19 (passage %d)" % PASSAGE)
t = Counter(); ex = defaultdict(list)
for a in sorted(tient):
    if a not in D.REG or I.nature.get(a) != PC.VRAIE:
        continue
    L_, raison = eliminer(a, sauf=a)
    if raison == "moins de deux candidates":
        continue
    k = ("DONNE, et c'est la BONNE ligne" if L_ and L_ in tient[a] else "DONNE, et c'est une AUTRE ligne" if L_
         else "s'abstient")
    t[k] += 1
    ex[k].append((a, D.REG[a]["genre"], D.REG[a]["bien"], L_, sorted(tient[a]), raison))
for k, n in t.most_common():
    print("   %5d  %s  ex. %s" % (n, k, ex[k][:4]))
print("\n   LES ECARTS, TOUS :")
for x in ex["DONNE, et c'est une AUTRE ligne"]:
    print("     ", x)
print("\n=== CE QU'ELLE DIT DES PIECES DU VERROU (a part au passage %d)" % PASSAGE)
for i, v in sorted(V.items()):
    pass
for a in (3689, 4720, 7903, 11103, 11579, 11708, 17203, 19815):
    print("   %d -> %s" % (a, eliminer(a)))

print("\n=== LE MEME TEMOIN, SUR LA BASE QUE LA REGLE LIRA : les pieces PROUVEES de chaque bien (r['va'] de la coupe)")
import coupe_preuve_interne as K
R = {}
_o = K.couper_le_bien


def _cap(D_, b, *x, **k):
    r = _o(D_, b, *x, **k)
    R[b] = r
    return r


K.couper_le_bien = _cap
P.K.couper_le_bien = _cap
par_bien = defaultdict(set)
for i, vs in sorted(I.sheet["par_id"].items()):
    if P.juger_ligne(I, i, vs[0]) is None:
        par_bien[P.r_bien(I, i)].add(i)
for b in par_bien:
    P.juger_bien(I, b, par_bien[b], "bien")


def eliminer_va(a, va):
    r = D.REG[a]
    b = r["bien"]
    cands = sorted(i for i in D.lignes_bien.get(b, set()) if D.touche_ph(a, i) and not D.contre_dates(a, {i}))
    if len(cands) < 2:
        return None, "moins de deux candidates"

    def du_genre(i):
        return [q for q, ls in va.items() if i in ls and q != a and I.nature.get(q) == PC.VRAIE
                and D.REG[q]["genre"] == r["genre"]]
    pourvue = {i: [q for q in du_genre(i) if D.REG[q]["montant"] == r["montant"] and D.REG[q]["hon"] == r["hon"]]
               for i in cands}
    libre = [i for i in cands if not du_genre(i)]
    if len(libre) == 1 and all(pourvue[i] for i in cands if i != libre[0]):
        return libre[0], "elimination"
    return None, "s'abstient (%d libre(s), %d pourvue(s) sur %d)" % (len(libre), sum(1 for i in cands if pourvue[i]),
                                                                     len(cands))


t2 = Counter(); ex2 = defaultdict(list)
for b, r in R.items():
    for a, ls in r["va"].items():
        if len(ls) != 1 or I.nature.get(a) != PC.VRAIE:
            continue
        L_, raison = eliminer_va(a, r["va"])
        if raison == "moins de deux candidates":
            continue
        k = ("DONNE, et c'est la BONNE ligne" if L_ and L_ in ls else "DONNE, et c'est une AUTRE ligne" if L_
             else "s'abstient")
        t2[k] += 1
        ex2[k].append((a, D.REG[a]["genre"], b, L_, sorted(ls), raison))
for k, n in t2.most_common():
    print("   %5d  %s  ex. %s" % (n, k, ex2[k][:3]))
print("   LES ECARTS, TOUS :", ex2["DONNE, et c'est une AUTRE ligne"])
print("\n   les pieces a part du verrou, sur cette base :")
for a in (3689, 4720, 7903, 11103, 11579, 11708, 17203, 19815):
    print("     %d -> %s" % (a, eliminer_va(a, R[D.REG[a]["bien"]]["va"])))

print("\n=== R25, L'ELIMINATION PAR LES HONORAIRES SEULS (le prix ne colle a aucune ligne) -- son temoin sur la meme base")


def eliminer_hon(a, va):
    r = D.REG[a]
    b = r["bien"]
    if r["hon"] is None:
        return None, "honoraires inconnus"
    cands = sorted(i for i in D.lignes_bien.get(b, set()) if P.nombre_case(D.case(i, "Commission TTC")) is not None
                   and abs(r["hon"] - P.nombre_case(D.case(i, "Commission TTC"))) <= 1 and not D.contre_dates(a, {i}))
    if len(cands) < 2:
        return None, "moins de deux candidates"

    def du_genre(i):
        return [q for q, ls in va.items() if i in ls and q != a and I.nature.get(q) == PC.VRAIE
                and D.REG[q]["genre"] == r["genre"]]
    pourvue = {i: [q for q in du_genre(i) if D.REG[q]["hon"] is not None and abs(D.REG[q]["hon"] - r["hon"]) <= 1]
               for i in cands}
    libre = [i for i in cands if not du_genre(i)]
    if len(libre) == 1 and all(pourvue[i] for i in cands if i != libre[0]):
        return libre[0], "elimination par les honoraires"
    return None, "s'abstient"


t3 = Counter(); ex3 = defaultdict(list)
for b, r in R.items():
    for a, ls in r["va"].items():
        if len(ls) != 1 or I.nature.get(a) != PC.VRAIE:
            continue
        L_, raison = eliminer_hon(a, r["va"])
        if raison in ("moins de deux candidates", "honoraires inconnus"):
            continue
        k = ("DONNE, et c'est la BONNE ligne" if L_ and L_ in ls else "DONNE, et c'est une AUTRE ligne" if L_
             else "s'abstient")
        t3[k] += 1
        ex3[k].append((a, D.REG[a]["genre"], b, L_, sorted(ls)))
for k, n in t3.most_common():
    print("   %5d  %s  ex. %s" % (n, k, ex3[k][:3]))
print("   LES ECARTS, TOUS :", ex3["DONNE, et c'est une AUTRE ligne"])
print("   7499 (SYA8MH79) ->", eliminer_hon(7499, R["15220"]["va"]))
