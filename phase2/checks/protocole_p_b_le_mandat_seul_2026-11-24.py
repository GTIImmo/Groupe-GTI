"""P-b : LES LIGNES TRANCHEES TENUES PAR LE MANDAT SEUL (24/11, son mot § 9) -- LECTURE SEULE (l'image, le socle).

Sa question, telle que je l'ai definie le 23/11 (§ 20.26) : « les lignes TRANCHEES dont la preuve cite le mandat (80 au
passage 41) : combien tiennent PAR LE MANDAT SEUL et sont RECONSTITUEES -- le mandat du Sheet est faux 55 % du temps sur
elles -- avec un TEMOIN POSITIF. » Sa mesure du passage 76 : 80 citent le mandat, 0 tenue par le mandat seul -- « ⚠ j'ai lu
le TEXTE des preuves, pas le raisonnement du code. Un 0 ne se croit pas sans temoin positif. Refais-la proprement. »

LE RAISONNEMENT DU CODE (lu, pas suppose) : le numero de mandat du Sheet n'entre qu'a UN endroit -- le BIEN de la ligne
(coupe_preuve_interne.Donnees : « les lignes du bien : gel + Mandat (unique) + numero de dossier (unique) », puis le Lien
CRM propage depuis les lignes deja rattachees) ; et dans la regle P1 (gel ET mandat contre le seul product_ref). Les preuves
des pieces (decider / trancher) ne le lisent JAMAIS : la date au jour exact, puis le prix + les honoraires.
DONC une ligne « tient par le mandat seul » quand :
  1. ce qui la met sur son bien est le Mandat SEUL (ni gel, ni product_ref, ni Lien CRM, ni sa decision) -- ou le Mandat
     et un Lien CRM qui ne vient lui-meme que de lignes rattachees par le Mandat ;
  2. ET aucune de ses vraies pieces n'est prouvee a elle INDEPENDAMMENT du mandat (date au jour exact d'une de ses
     colonnes, ou prix + honoraires) -- une telle preuve confirme le bien sans lui.
LES MESURES :
  A  le texte : les lignes tranchees dont une preuve CITE le mandat (son 80) -- et ce que dit la citation ;
  B  le raisonnement : la source du bien de chaque ligne tranchee, et la preuve independante de ses pieces ;
  C  les reconstituees (Prix « NON TROUVE » -- la marque du § 20.25, retrouvee par son temoin : 56 au passage 41) ;
  TEMOIN POSITIF : le meme classement sur TOUTES les lignes -- il doit trouver, sur le bien de leur ANCIEN mandat (perime),
     les 5 lignes de ses rattachements du 23/11 au soir (2U5QPKRC, EJN79TJ1, MQ6H8TVQ, QXDW8EQA, 91IHSGNC) : rattachees
     par le Mandat seul, sur un bien sans aucune piece -- le cas meme que P-b cherche, et que R8 a arrete.

USAGE : python -u -X utf8 phase2/checks/protocole_p_b_le_mandat_seul_2026-11-24.py --passage P
"""
import sys, json, argparse
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K
sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--passage", type=int, required=True)
arg = ap.parse_args()


def dire(s=""):
    print(s, flush=True)


con = P.socle()
image, version = con.execute("select image, version from passage where id=?", (arg.passage,)).fetchone()
V = {}
for i, v, bs, ps, pr, m in con.execute("select id_unique, verdict, biens, pieces, preuves, motif from verdict "
                                       "where passage=?", (arg.passage,)):
    V[i] = {"verdict": v, "biens": json.loads(bs) if bs else [], "pieces": json.loads(ps) if ps else [],
            "preuves": json.loads(pr) if pr else [], "motif": m}
con.close()
I = P.Image(P.IMAGES / image)
D = I.D
T = [i for i, v in V.items() if v["verdict"] == "TRANCHEE"]
dire("P-b -- passage %d (%s), image %s : %d lignes tranchees" % (arg.passage, version, image, len(T)))


def reconstituee(i):
    """La marque du § 20.25, retrouvee par son temoin : « Prix » = « NON TROUVE » -> 56 lignes tranchees au passage 41,
    exactement le chiffre du 23/11 (Prix ET Ville : 49 ; Prix + Nature « Autre » : 37 -- ce n'etait pas elles)."""
    return "NON TROUV" in D.case(i, "Prix").upper()


# ── A : LE TEXTE (sa mesure) ──────────────────────────────────────────────────────────────────────────────────────
cite = {i: [p for p in V[i]["preuves"] if "mandat" in p.lower()] for i in T}
cite = {i: ps for i, ps in cite.items() if ps}
genre_citation = Counter()
for i, ps in cite.items():
    for p in ps:
        if "REGLE P1" in p.upper() or "regle P1" in p:
            genre_citation["la regle P1 (gel + mandat contre le seul product_ref)"] += 1
        elif "perime" in p:
            genre_citation["sa decision : « son mandat au Sheet est perime »"] += 1
        else:
            genre_citation["autre : " + p[:70]] += 1
dire()
dire("A -- LE TEXTE : %d lignes tranchees dont une preuve cite le mot « mandat » (sa mesure du passage 76 : 80)" % len(cite))
for k, n in genre_citation.most_common():
    dire("      %4d  %s" % (n, k))

# ── B : LE RAISONNEMENT DU CODE ───────────────────────────────────────────────────────────────────────────────────
par_mandat_seul = defaultdict(set)      # bien -> lignes rattachees au bien par le Mandat SEUL


def sources(b, i):
    return set(D.rattache_par.get((b, i), set()))


def racines(b, i):
    """CE QUI MET VRAIMENT la ligne sur le bien : ses sources directes (gel, product_ref, mandat, sa decision) ; un Lien
    CRM ne vaut que par les lignes deja rattachees qui le portent -- LA LIGNE ELLE-MEME COMPRISE (Donnees : biens_du_lien
    est fait des rattachements gel + mandat + product_ref) -> ses racines sont les sources directes de ces lignes."""
    s = sources(b, i)
    out = s - {"lien_crm"}
    if "lien_crm" in s:
        lien = D.case(i, "Lien CRM").strip()
        for j in D.LIG:
            if D.case(j, "Lien CRM").strip() == lien:
                out |= sources(b, j) & {"gel", "product_ref", "mandat"}
    return out


def classe_source(b, i):
    s = sources(b, i)
    r = racines(b, i)
    if "sa_decision" in s:
        return "sa decision (LIGNE_SUR_LE_BIEN_PAR_DECISION)"
    if r == {"mandat"}:
        return "LE MANDAT SEUL" + (" (par le Lien CRM, qui ne vient que du mandat)" if "lien_crm" in s else "")
    if "sa_decision" in s:
        return "sa decision (LIGNE_SUR_LE_BIEN_PAR_DECISION)"
    if "gel" in s:
        return "le gel" + (" (+ " + " + ".join(sorted(s - {"gel"})) + ")" if s - {"gel"} else " seul")
    if "product_ref" in s:
        return "le product_ref" + (" (+ " + " + ".join(sorted(s - {"product_ref"})) + ")" if s - {"product_ref"} else "")
    if s == {"mandat"}:
        return "LE MANDAT SEUL"
    if s == {"lien_crm"}:
        return "le Lien CRM seul"
    if s == {"mandat", "lien_crm"}:
        return "LE MANDAT + le Lien CRM"
    return "autre : %s" % sorted(s)


def preuve_independante(i, ps):
    """Une vraie piece de la ligne prouvee a elle SANS le mandat : la date au jour exact d'une de ses colonnes, ou le prix
    + les honoraires (le critere 1). -> la liste de ces pieces."""
    return [a for a in ps if I.nature.get(a) == PC.VRAIE and a in D.REG and (D.touche_date(a, i) or D.touche_ph(a, i))]


def lien_crm_par_le_mandat(b, i):
    """Le Lien CRM de la ligne ne vient-il que de lignes rattachees au bien par le Mandat seul ?"""
    lien = D.case(i, "Lien CRM").strip()
    if not lien:
        return False
    autres = [j for j in D.lignes_bien.get(b, set()) if j != i and D.case(j, "Lien CRM").strip() == lien]
    return bool(autres) and all(sources(b, j) <= {"mandat", "lien_crm"} for j in autres)


B = Counter()
mandat_lignes = []
for i in T:
    b = V[i]["biens"][0]
    c = classe_source(b, i)
    B[c] += 1
    if c.startswith("LE MANDAT SEUL"):
        ind = preuve_independante(i, V[i]["pieces"])
        mandat_lignes.append((i, b, c, ind, reconstituee(i)))
dire()
dire("B -- LE RAISONNEMENT : ce qui met chaque ligne tranchee sur son bien (D.rattache_par -- ce que le code a lu)")
for k, n in B.most_common():
    dire("      %4d  %s" % (n, k))
tient_seul = [x for x in mandat_lignes if not x[3]]
dire("   ⭐ lignes tranchees sur leur bien par le MANDAT SEUL (ou mandat + un Lien CRM qui ne vient que du mandat) : %d"
     % len(mandat_lignes))
dire("      dont confirmees par une PREUVE INDEPENDANTE (une vraie piece au jour exact, ou prix + honoraires) : %d"
     % (len(mandat_lignes) - len(tient_seul)))
dire("      ⛔ dont TENUES PAR LE MANDAT SEUL (aucune preuve independante) : %d" % len(tient_seul))
for i, b, c, ind, rec in sorted(mandat_lignes):
    dire("         %s  bien %-6s %-24s Mandat %-7s %s  preuve independante : %s" % (
        i, b, c, D.case(i, "Mandat").strip() or "-", "RECONSTITUEE" if rec else "             ",
        " ".join("%d (%s)" % (a, "date" if D.touche_date(a, i) else "prix+hon") for a in ind) or "⛔ AUCUNE"))

# ── C : LES RECONSTITUEES ─────────────────────────────────────────────────────────────────────────────────────────
rec_T = [i for i in T if reconstituee(i)]
rec_m = [x for x in mandat_lignes if x[4]]
dire()
dire("C -- LES RECONSTITUEES (Prix « NON TROUVE ») : %d lignes tranchees (temoin du § 20.25 : 56 au passage 41)"
     % len(rec_T))
ce = Counter(classe_source(V[i]["biens"][0], i) for i in rec_T)
for k, n in ce.most_common():
    dire("      %4d  %s" % (n, k))
mandat_pieces = Counter()
for i in rec_T:
    m = D.case(i, "Mandat").strip()
    b = V[i]["biens"][0]
    if not m:
        mandat_pieces["sans Mandat au Sheet"] += 1
    elif b in D.mandats_du_bien.get(m, set()):
        mandat_pieces["le Mandat du Sheet est un mandat de son bien"] += 1
    else:
        mandat_pieces["⚠ le Mandat du Sheet est celui d'un AUTRE bien (ou d'aucun)"] += 1
dire("   le Mandat du Sheet des reconstituees tranchees : " + " . ".join("%s %d" % kv for kv in mandat_pieces.most_common()))
dire("   ⭐ reconstituees ET sur leur bien par le mandat seul : %d ; dont TENUES PAR LE MANDAT SEUL : %d" % (
    len(rec_m), sum(1 for x in rec_m if not x[3])))

# ── LE TEMOIN POSITIF : le meme classement sur TOUTES les lignes, et ses 5 rattachements ───────────────────────────
dire()
dire("TEMOIN POSITIF -- le meme classement sur toutes les lignes, sur TOUS les biens qu'elles nomment")
tout = Counter()
seul_tous = []
for i in D.LIG:
    for b in sorted(I.biens_de_ligne.get(i, set()) | {bb for bb, ls in D.lignes_bien.items() if i in ls}):
        c = classe_source(b, i)
        if c.startswith("LE MANDAT SEUL"):
            tout[(V.get(i, {}).get("verdict"), V.get(i, {}).get("motif"))] += 1
            seul_tous.append((i, b))
dire("   (ligne, bien) rattaches par le mandat seul, sur tout le Sheet : %d -- par verdict : %s" % (
    len(seul_tous), dict(tout)))
CINQ = ["2U5QPKRC", "EJN79TJ1", "MQ6H8TVQ", "QXDW8EQA", "91IHSGNC"]
trouvees = 0
for i in CINQ:
    # leur ancien bien (celui de leur mandat perime) : D.rattache_par le garde, meme apres sa decision
    anciens = sorted(b for (b, j), s in D.rattache_par.items() if j == i and "sa_decision" not in s)
    cl = {b: classe_source(b, i) for b in anciens}
    pieces_ancien = {b: len(D.par_bien.get(b, [])) for b in anciens}
    ok = any(c.startswith("LE MANDAT SEUL") for b, c in cl.items())
    trouvees += ok
    dire("   %s %s  son Mandat %s -> ancien(s) bien(s) %s (%s ; pieces : %s) ; aujourd'hui sur %s par sa decision" % (
        "✔" if ok else "⛔", i, D.case(i, "Mandat").strip(), anciens, cl, pieces_ancien,
        sorted(I.biens_de_ligne.get(i, set()))))
dire("   ⭐ TEMOIN POSITIF : %d sur 5 retrouvees par le classement (rattachees a leur ancien bien par le MANDAT SEUL)" % trouvees)
