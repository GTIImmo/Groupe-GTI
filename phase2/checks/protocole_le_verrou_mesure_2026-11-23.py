"""LE VERROU (E7) MESURE : ses 56 lignes, ses familles, et les deux temoins que son mot du 23/11 (20) me laisse. LECTURE
SEULE -- l'image figee 2026-11-23_080234, le socle en lecture ; aucun passage n'est ecrit ici.

Son mot : C:\\Hektor\\mot_du_23_11_le_verrou_mesure_trois_familles.md
0 le rejeu : juger_bien() sur les biens du verrou redonne-t-il le passage 51, ligne par ligne ? (sinon rien ne vaut)
1 la decomposition des 56 par la raison de la piece qui retient (46 / 6 / 4 selon lui)
2 FAMILLE A (« prix + honoraires de plusieurs acheteurs ») : pour chaque piece qui retient, ses candidates, l'etat de
  chacune au passage 51, et si chaque autre candidate TIENT DEJA une vraie piece du MEME GENRE au meme prix + honoraires
  (l'elimination : une affaire n'a qu'une piece de chaque genre) -- et le peigne des numeros
3 FAMILLE B (la piece qui retient est d'une affaire tombee) : sa soeur au meme montant (compromis annule <-> offre
  refusee), le montant est-il celui d'une ligne du bien ?
4 LE TEMOIN INVERSE DE B, sur toute l'image : chaque affaire tombee COMPLETE (un compromis annule et une offre refusee au
  meme montant, sur le meme bien) -- son montant est-il celui d'une ligne ? et qui tient ses pieces au passage 51 ?
5 LA SOEUR DE CHAINE (la regle que la mesure propose, R17) : son temoin positif -- les paires compromis annule / offre
  refusee, meme chaine, meme montant, tenues au passage 51 : la meme ligne ? (300 / 2, les 2 nommees au carnet § 20.32)
6 la meme, AVEC SES GARDES, rejouee dans les deux sens sur chaque paire tenue : 581 la bonne ligne, 0 une autre.
Carnet : § 20.32. Les passages 52, 53, 54 (variante R17) sont au socle.
"""
import sys, sqlite3, json
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K
sys.stdout.reconfigure(encoding="utf-8")
I = P.Image(P.IMAGES / "2026-11-23_080234"); D = I.D
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
V51 = {i: {"verdict": v, "motif": m, "texte": t, "pieces": json.loads(p or "null"), "biens": json.loads(b or "[]"),
           "etiquette": e}
       for i, v, m, t, p, b, e in c.execute("select id_unique, verdict, motif, motif_texte, pieces, biens, etiquette "
                                             "from verdict where passage=51")}
VER = sorted(i for i, x in V51.items() if x["motif"] == "VERROU_PIECE_PLUS_PETITE")
print("=== 0 LE REJEU des biens du verrou (passage 51 : %d lignes au verrou)" % len(VER))
# le meme regroupement que etape_passage : les lignes que juger_ligne ne tranche pas vont a leur bien
par_bien = defaultdict(set)
for i, vs in sorted(I.sheet["par_id"].items()):
    if P.juger_ligne(I, i, vs[0]) is None:
        par_bien[P.r_bien(I, i)].add(i)
biens_v = sorted({V51[i]["biens"][0] for i in VER}, key=int)
R = {}
_orig = K.couper_le_bien
def _capture(D_, b, *a, **k):
    r = _orig(D_, b, *a, **k)
    R[b] = r
    return r
K.couper_le_bien = _capture
P.K.couper_le_bien = _capture
OUT = {}
for b in biens_v:
    for o in P.juger_bien(I, b, par_bien[b], "bien"):
        OUT[o["id_unique"]] = o
diff = [i for i, o in OUT.items() if (o["verdict"], o.get("motif"), o.get("etiquette"), o.get("pieces"))
        != (V51[i]["verdict"], V51[i]["motif"], V51[i]["etiquette"], V51[i]["pieces"])]
print("   %d biens, %d lignes rejugees ; ecarts avec le passage 51 : %d %s" % (len(biens_v), len(OUT), len(diff), diff[:5]))
L = lambda a: I.pieces[a]


def piece(a):
    r = D.REG[a]
    return "%d %s %s %s %s+%s ch.%s dos.%s%s" % (a, r["genre"], r["etat"] or "-", r["date"] or "SANS DATE",
                                                 r["montant"], r["hon"], L(a)["app_chaine_id"], L(a)["app_dossier_numero"],
                                                 "" if I.nature[a] == PC.VRAIE else " (COPIE)")


def ligne(i):
    return "%s [%s] Prix %s Com %s | Offre %s Compromis %s Signee %s Annulee %s" % (
        i, D.case(i, "Etat Actuel"), D.case(i, "Prix"), D.case(i, "Commission TTC"), D.case(i, "Offre Achat"),
        D.case(i, "Compromis"), D.case(i, "Signée"), D.case(i, "Annulée"))


print("\n=== 1 LA DECOMPOSITION : la raison de la piece qui retient")
raison = {}
for i in VER:
    t = V51[i]["texte"]
    raison[i] = ("A plusieurs acheteurs" if "plusieurs acheteurs" in t else
                 "B sans date, prix+hon d'aucune ligne" if "sans date" in t else
                 "B date sur aucune case, hon inconnus" if "aucune case" in t else "?")
print("   ", dict(Counter(raison.values())))
# les pieces qui retiennent, par ligne (le texte du motif les nomme) -- et la meme lue dans r
bloque = {}
for i in VER:
    b = V51[i]["biens"][0]
    r = R[b]
    gl = [g for g in r["morceaux"] if i in g][0]
    m = min(a for a in r["morceaux"][gl] if I.nature[a] == PC.VRAIE)
    bloque[i] = sorted(a for a in r["apart"] if I.nature[a] == PC.VRAIE and a < m and gl in r["possibles"][a])
print("   pieces qui retiennent : %d distinctes pour %d lignes ; lignes retenues par PLUSIEURS pieces : %s"
      % (len({a for v in bloque.values() for a in v}), len(bloque), [i for i, v in bloque.items() if len(v) > 1]))

print("\n=== 2 FAMILLE A -- prix + honoraires de plusieurs acheteurs")
famA = [i for i in VER if raison[i].startswith("A")]
pieces_A = sorted({a for i in famA for a in bloque[i]})
elim = {}
for a in pieces_A:
    b = D.REG[a]["bien"]
    r = R[b]
    lignes_b = set(D.lignes_bien.get(b, set()))
    cand = sorted(i for i in lignes_b if D.touche_ph(a, i) and not D.contre_dates(a, {i}))
    retenues = sorted(i for i in famA if a in bloque[i])
    print("\n   PIECE %s  (bien %s)" % (piece(a), b))
    print("     candidates par prix + honoraires : %s ; lignes qu'elle retient : %s" % (cand, retenues))
    etat = {}
    for i in sorted(lignes_b):
        v = V51.get(i, {})
        gl = [g for g in r["morceaux"] if i in g]
        ids = r["morceaux"][gl[0]] if gl else []
        meme = [q for q in ids if I.nature[q] == PC.VRAIE and D.REG[q]["genre"] == D.REG[a]["genre"]]
        meme_ph = [q for q in meme if D.REG[q]["montant"] == D.REG[a]["montant"] and D.REG[q]["hon"] == D.REG[a]["hon"]]
        etat[i] = (v.get("verdict"), meme, meme_ph)
        print("       %s %-9s %-26s morceau %s | meme genre %s (dont meme prix+hon %s)%s" % (
            "*" if i in cand else " ", v.get("verdict"), v.get("motif") or "", ids, meme, meme_ph,
            "" if i in cand else "  [pas candidate]"))
    autres = [i for i in cand if i not in retenues or True]
    # L'ELIMINATION : toutes les candidates SAUF UNE tiennent deja une vraie piece du meme genre au meme prix+hon, et
    #   celle-la n'en tient aucune -> la piece ne peut etre qu'a elle
    libres = [i for i in cand if not etat[i][2]]
    prises = [i for i in cand if etat[i][2]]
    tranchees_prises = [i for i in prises if etat[i][0] == "TRANCHEE"]
    elim[a] = {"cand": cand, "libres": libres, "prises": prises, "tranchees_prises": tranchees_prises,
               "retenues": retenues}
    print("     -> candidates qui TIENNENT DEJA une piece de ce genre a ce prix+hon : %s (tranchees : %s) ; LIBRES : %s"
          % (prises, tranchees_prises, libres))
print("\n   BILAN A (par piece) :")
k = Counter()
for a, e in elim.items():
    if len(e["libres"]) == 1 and e["prises"] and set(e["prises"]) == set(e["tranchees_prises"]):
        k["une seule libre, les autres TRANCHEES et deja pourvues -> elimination"] += 1
    elif len(e["libres"]) == 1 and e["prises"]:
        k["une seule libre, une autre pourvue mais EN ATTENTE"] += 1
    elif len(e["libres"]) == 1:
        k["une seule libre, aucune pourvue (?)"] += 1
    elif not e["libres"]:
        k["AUCUNE libre : toutes deja pourvues"] += 1
    else:
        k["plusieurs libres (%d)" % len(e["libres"])] += 1
for x, n in k.most_common():
    print("     %3d  %s" % (n, x))

print("\n=== 3 FAMILLE B -- la piece qui retient est-elle d'une affaire tombee ?")
famB = [i for i in VER if raison[i].startswith("B")]
for a in sorted({a for i in famB for a in bloque[i]}):
    b = D.REG[a]["bien"]
    g = D.REG[a]["genre"]
    soeur_g = {"compromis": "offre", "offre": "compromis"}.get(g)
    soeurs = [q for q in D.par_bien[b] if q != a and D.REG[q]["genre"] == soeur_g
              and D.REG[q]["montant"] is not None and D.REG[q]["montant"] == D.REG[a]["montant"]]
    prix_l = {i: (D.case(i, "Prix"), sorted(D.offres_de_la_ligne(i, b))) for i in D.lignes_bien.get(b, set())}
    est_ligne = [i for i, (_p, offs) in prix_l.items() if D.REG[a]["montant"] is not None
                 and any(abs(D.REG[a]["montant"] - x) <= 1 for x in offs)]
    print("\n   PIECE %s  (bien %s) retient %s" % (piece(a), b, [i for i in famB if a in bloque[i]]))
    print("     soeur(s) %s au meme montant : %s" % (soeur_g, [piece(q) for q in soeurs] or "AUCUNE"))
    print("     le montant est celui d'une ligne du bien (Prix ou offre prouvee) : %s" % (est_ligne or "AUCUNE"))
    for i in sorted(D.lignes_bien.get(b, set())):
        print("       %s -> %s %s" % (ligne(i), V51.get(i, {}).get("verdict"), V51.get(i, {}).get("pieces")))
    print("     toutes les pieces du bien :")
    for q in sorted(D.par_bien[b]):
        print("       %s%s" % (piece(q), "   <- A PART" if q in R[b]["apart"] else ""))

print("\n=== 4 LE TEMOIN INVERSE DE B : les affaires tombees COMPLETES de toute l'image")
tient = {}
for i, x in V51.items():
    if x["verdict"] == "TRANCHEE":
        for q in x["pieces"] or []:
            tient.setdefault(q, set()).add(i)
paires = []
for b, ids in D.par_bien.items():
    cps = [q for q in ids if D.REG[q]["genre"] == "compromis" and D.REG[q]["etat"] == "cancelled" and I.nature[q] == PC.VRAIE]
    ofs = [q for q in ids if D.REG[q]["genre"] == "offre" and D.REG[q]["etat"] == "refused" and I.nature[q] == PC.VRAIE]
    for cp in cps:
        for of in ofs:
            if D.REG[cp]["montant"] is not None and D.REG[cp]["montant"] == D.REG[of]["montant"]:
                paires.append((b, cp, of))
print("   paires (compromis annule, offre refusee) au meme montant sur le meme bien : %d, sur %d biens"
      % (len(paires), len({p[0] for p in paires})))
cl = Counter(); ex = defaultdict(list)
for b, cp, of in paires:
    mt = D.REG[cp]["montant"]
    ls = D.lignes_bien.get(b, set())
    de_ligne = [i for i in ls if any(abs(mt - x) <= 1 for x in D.offres_de_la_ligne(i, b))]
    t_cp, t_of = tient.get(cp, set()), tient.get(of, set())
    k1 = "montant D'UNE LIGNE" if de_ligne else ("bien SANS LIGNE" if not ls else "montant d'AUCUNE ligne")
    if t_cp or t_of:
        bonne = (t_cp | t_of) <= set(de_ligne)
        k2 = "tenue par une ligne tranchee" + (" (celle du montant)" if de_ligne and bonne else
                                               " (une AUTRE que celle du montant)" if de_ligne else "")
    else:
        k2 = "tenue par aucune ligne tranchee"
    cl[(k1, k2)] += 1
    ex[(k1, k2)].append((b, cp, of, sorted(t_cp | t_of), sorted(de_ligne)))
for (k1, k2), n in sorted(cl.items()):
    print("   %4d  %-22s | %s  ex. %s" % (n, k1, k2, ex[(k1, k2)][:3]))

print("\n=== 5 LA SOEUR DE CHAINE (la regle que la mesure propose) -- son TEMOIN POSITIF sur toute l'image")
# une affaire tombee laisse deux pieces dans la MEME chaine Hektor : son compromis ANNULE et son offre REFUSEE, au meme
#   montant. Quand les DEUX sont tenues au passage 51, le sont-elles par la MEME ligne ?
AUTRE = {("compromis", "cancelled"): ("offre", "refused"), ("offre", "refused"): ("compromis", "cancelled")}
par_ch = defaultdict(list)
for a, p in I.pieces.items():
    if a in D.REG and I.nature[a] == PC.VRAIE:
        par_ch[p["app_chaine_id"]].append(a)


def soeurs(a):
    r = D.REG[a]
    k = AUTRE.get((r["genre"], r["etat"]))
    if not k or r["montant"] is None:
        return []
    return [q for q in par_ch[I.pieces[a]["app_chaine_id"]] if q != a and (D.REG[q]["genre"], D.REG[q]["etat"]) == k
            and D.REG[q]["montant"] is not None and abs(D.REG[q]["montant"] - r["montant"]) <= 1]


tp = Counter(); ex_tp = defaultdict(list)
vus = set()
for a in sorted(D.REG):
    if I.nature.get(a) != PC.VRAIE or D.REG[a]["genre"] != "compromis":
        continue
    s = soeurs(a)
    if len(s) != 1 or len(soeurs(s[0])) != 1:
        if s:
            tp["soeur NON UNIQUE dans la chaine (la regle s'abstient)"] += 1
        continue
    q = s[0]
    ta, tq = tient.get(a, set()), tient.get(q, set())
    if ta and tq:
        k = "les deux tenues : MEME ligne" if ta == tq else "les deux tenues : lignes DIFFERENTES"
    elif ta or tq:
        k = "une seule des deux tenue"
    else:
        k = "aucune des deux tenue"
    tp[k] += 1
    ex_tp[k].append((a, q, sorted(ta), sorted(tq)))
for k, n in tp.most_common():
    print("   %5d  %s  ex. %s" % (n, k, ex_tp[k][:4]))
print("\n   les lignes DIFFERENTES, toutes :", ex_tp["les deux tenues : lignes DIFFERENTES"])
print("\n   ce que la regle donnerait au passage 51 (piece tenue par personne, soeur unique tenue par UNE ligne) :")
pr = Counter()
for a, q, ta, tq in ex_tp["une seule des deux tenue"]:
    libre, tenue, L_ = (a, q, tq) if not ta else (q, a, ta)
    if len(L_) != 1:
        pr["soeur tenue par plusieurs lignes"] += 1
        continue
    L1 = L_[0]
    deja = [x for x in (V51[L1]["pieces"] or []) if I.nature[x] == PC.VRAIE and D.REG[x]["genre"] == D.REG[libre]["genre"]]
    au_verrou = [i for i in VER if libre in bloque[i]]
    pr[("GARDE : la ligne tient deja ce genre" if deja else "donnee a " + V51[L1]["verdict"],
        "retient %d ligne(s) du verrou" % len(au_verrou) if au_verrou else "ne retient aucune ligne du verrou")] += 1
    if au_verrou:
        print("      %d -> %s (%s, soeur %d) ; debloque %s%s" % (libre, L1, V51[L1]["verdict"], tenue, au_verrou,
                                                              "  ⛔ GARDE %s" % deja if deja else ""))
for k, n in sorted(pr.items(), key=str):
    print("   %5d  %s" % (n, k))

print("\n=== 6 LA SOEUR DE CHAINE AVEC SES GARDES -- le temoin rejoue la regle dans les DEUX sens sur chaque paire tenue")
# la regle : P (a part) suit Q (sa soeur unique de chaine) a la ligne L qui tient Q, SI
#   g1 les dates ne contredisent pas P sur L (contre_dates : apres l'annulation + 15 j, compromis avant l'offre)
#   g2 offre et compromis dates tous deux : l'offre n'est pas APRES le compromis
#   g3 L ne tient deja AUCUNE vraie piece du genre de P (une affaire tombee n'a qu'une offre refusee et qu'un compromis
#      annule a ce montant -- une renegociation fait une 2e offre : la regle s'abstient alors)


def garde(P_, Q_, L1, pieces_L):
    if D.contre_dates(P_, {L1}):
        return "g1 dates"
    o, cp = (P_, Q_) if D.REG[P_]["genre"] == "offre" else (Q_, P_)
    if D.REG[o]["date"] and D.REG[cp]["date"] and D.REG[o]["date"] > D.REG[cp]["date"]:
        return "g2 offre apres compromis"
    if [x for x in pieces_L if x != P_ and I.nature[x] == PC.VRAIE and D.REG[x]["genre"] == D.REG[P_]["genre"]]:
        return "g3 la ligne tient deja ce genre"
    return None


t6 = Counter(); ex6 = defaultdict(list)
multi = Counter()
for a, q, ta, tq in ex_tp["les deux tenues : MEME ligne"] + ex_tp["les deux tenues : lignes DIFFERENTES"]:
    b = D.REG[a]["bien"]
    nb = sum(1 for i in D.lignes_bien.get(b, set()) if any(abs(D.REG[a]["montant"] - x) <= 1 for x in D.offres_de_la_ligne(i, b)))
    regime = "bien a %s ligne(s) a ce montant" % ("1" if nb <= 1 else "2+")
    multi[(regime, "meme" if ta == tq else "DIFFERENTES")] += 1
    for P_, Q_, vraie, tenueQ in ((a, q, ta, tq), (q, a, tq, ta)):
        if len(tenueQ) != 1:
            t6["soeur tenue par plusieurs lignes"] += 1
            continue
        L1 = tenueQ[0]
        g = garde(P_, Q_, L1, V51[L1]["pieces"] or [])
        if g:
            k = "s'abstient (%s) -- la vraie ligne %s" % (g, "est L" if vraie == [L1] else "est une AUTRE")
        else:
            k = "DONNE a L, et c'est JUSTE" if vraie == [L1] else "DONNE a L, et c'est FAUX"
        t6[(regime, k)] += 1
        ex6[(regime, k)].append((P_, Q_, L1, vraie))
for k, n in sorted(multi.items()):
    print("   paires tenues : %-34s %-11s %5d" % (k[0], k[1], n))
for k, n in sorted(t6.items(), key=str):
    print("   %5d  %s  ex. %s" % (n, k, ex6[k][:3]))
