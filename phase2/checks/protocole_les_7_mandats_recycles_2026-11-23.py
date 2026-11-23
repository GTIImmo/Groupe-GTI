"""Les 7 mandats recycles (23/11) -- le bien de leurs PIECES, le numero du Sheet IGNORE. LECTURE SEULE.

Sa consigne : « utilise la methode qui a retrouve tes 5 ventes : le montant, la date, le vendeur -- en ignorant le
numero du Sheet. Cherche le bien de leurs PIECES, pas le bien de leur mandat. »
1 le temoin positif : la meme recherche sur les lignes tranchees « Annulee » qui tiennent une offre vraie ;
2 les 7, a 7 / 60 / 365 jours, et les pieces SANS DATE des biens du vendeur ;
3 les ratees du temoin, une par une ; 4 le temoin de la partie qui DONNE un bien (non proposee : 9 ecarts).
Lit le registre local en lecture seule (mandants_texte, absent de l image). Carnet : section 20.29.
"""
import sys, sqlite3, json, re
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, coupe_preuve_interne as K, piece_copie_ou_vraie as PC
I = P.Image(P.IMAGES / "2026-11-23_080234"); D = I.D
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
V = {i: (v, m, json.loads(pc) if pc else []) for i, v, m, pc in c.execute("select id_unique, verdict, motif, pieces from verdict where passage=47")}
qui = defaultdict(list)
for i, (v, m, pcs) in V.items():
    for a in pcs: qui[a].append(i)
con = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
MANDB = defaultdict(str)
for b, mt in con.execute("select hektor_annonce_id, mandants_texte from app_mandat_register_current"):
    MANDB[str(b)] += " " + (mt or "").upper()
for a in D.REG:   # les mandants portes par les pieces completent ceux du registre
    MANDB[D.REG[a]["bien"]] += " " + str(I.pieces[a].get("mandants_json") or "").upper()
STOP = P.STOP_VENDEUR | {"SAS", "SARL", "EURL", "SOCIETE", "SOCIÉTÉ"}
def noms(i):
    return {x for x in re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", D.case(i, "Vendeur").upper()) if x not in STOP}
PAR_NOM = defaultdict(set)
for b, t in MANDB.items():
    for x in set(re.findall(r"[A-ZÀ-Ü][A-ZÀ-Ü'\-]{2,}", t)): PAR_NOM[x].add(b)
def biens_du_vendeur(i):
    ns = noms(i)
    return set().union(*(PAR_NOM.get(n, set()) for n in ns)) if ns else set()
def pieces_proches(i, biens, fen):
    d0 = K.d_sheet(D.case(i, "Offre Achat")); d1 = K.d_sheet(D.case(i, "Compromis"))
    out = []
    for b in biens:
        for a in D.par_bien.get(b, []):
            r = D.REG[a]
            if I.nature[a] != PC.VRAIE or r["genre"] not in ("offre", "compromis") or not r["date"]: continue
            ref = d0 if r["genre"] == "offre" else (d1 or d0)
            if ref and abs((r["date"] - ref).days) <= fen: out.append(a)
    return out
an = lambda i: (K.d_sheet(D.case(i, "Offre Achat")) or K.d_sheet(D.case(i, "Compromis")) or type("x", (), {"year": None})).year
L = [i for i, (v, m, pc) in V.items() if v == "TRANCHEE" and D.case(i, "Etat Actuel") == "Annulée"
     and any(a in D.REG and D.REG[a]["genre"] == "offre" and I.nature[a] == PC.VRAIE for a in pc)]
print("=== TEMOIN : « les biens dont les mandants portent le vendeur (TOUS les biens, numero du Sheet ignore) + une offre ou un compromis a N jours »")
print("    sur les %d lignes tranchees « Annulee » qui tiennent une offre vraie : retrouve-t-on LEUR piece ?" % len(L))
for fen in (7, 30, 60):
    cpt = Counter(); rate = []
    for i in L:
        siennes = set(V[i][2]); t = set(pieces_proches(i, biens_du_vendeur(i), fen))
        k = "sa piece retrouvee" if t & siennes else ("aucun bien au nom du vendeur" if not biens_du_vendeur(i) else "sa piece NON retrouvee")
        cpt[k] += 1
        if k != "sa piece retrouvee": rate.append(i)
    print("   a %2d jours : %s | ex. ratees : %s" % (fen, dict(cpt), rate[:6]))
SEPT = ["87RH87SM", "QMIXZW44", "NEFHS7JI", "0BLBDVV8", "IJF2BRQJ", "UL12H3AQ", "ZZ5WKMWM"]
print("\n=== LES 7, MEME RECHERCHE (numero du Sheet ignore)")
for i in SEPT:
    bv = biens_du_vendeur(i)
    print("\n%s : %d biens au nom du vendeur %s" % (i, len(bv), sorted(noms(i))))
    for fen in (7, 60, 365):
        ps = pieces_proches(i, bv, fen)
        print("   a %3d j : %s" % (fen, "rien" if not ps else "; ".join("%s %s du %s %s %s hon %s (bien %s) tenue par %s" % (
            a, D.REG[a]["genre"], D.REG[a]["date"], D.REG[a]["etat"], D.REG[a]["montant"], D.REG[a]["hon"], D.REG[a]["bien"], qui.get(a) or "PERSONNE") for a in ps[:5])))
    sans_date = [a for b in bv for a in D.par_bien.get(b, []) if not D.REG[a]["date"] and D.REG[a]["genre"] in ("offre", "compromis") and I.nature[a] == PC.VRAIE]
    print("   pieces SANS DATE sur ces biens : %s" % ([(a, D.REG[a]["genre"], D.REG[a]["etat"], D.REG[a]["montant"], D.REG[a]["hon"], D.REG[a]["bien"], qui.get(a) or "PERSONNE") for a in sans_date][:6] or "aucune"))

print("\n=== LES 36 RATEES DU TEMOIN (a 7 jours), une par une : pourquoi")
for i in L:
    siennes = [a for a in V[i][2] if a in D.REG]
    bv = biens_du_vendeur(i); t = set(pieces_proches(i, bv, 7))
    if t & set(siennes): continue
    b0 = {D.REG[a]["bien"] for a in siennes}
    off = [a for a in siennes if D.REG[a]["genre"] == "offre" and I.nature[a] == PC.VRAIE]
    d0 = K.d_sheet(D.case(i, "Offre Achat"))
    ecart = [(D.REG[a]["date"] - d0).days if (d0 and D.REG[a]["date"]) else None for a in off]
    vend_sur_bien = any(n in MANDB[b] for b in b0 for n in noms(i))
    print("   %s Vendeur %r | bien %s | vendeur dans ses mandants : %s | ecart de date de son offre : %s | case Offre %r" % (
        i, D.case(i, "Vendeur")[:28], sorted(b0), "oui" if vend_sur_bien else "NON", ecart, D.case(i, "Offre Achat")))
print("\n=== TEMOIN de la partie (a) : bien du vendeur + offre a 7 j + compromis du MEME montant dont honoraires = Commission")
cpt = Counter(); autres = []
for i, (v, m, pc) in V.items():
    if v != "TRANCHEE": continue
    com = None
    try: com = round(float(D.case(i, "Commission TTC").replace(" ", "").replace(",", ".")))
    except Exception: pass
    if not com: continue
    d0 = K.d_sheet(D.case(i, "Offre Achat"))
    if not d0: continue
    desig = set()
    for b in biens_du_vendeur(i):
        offs = [a for a in D.par_bien.get(b, []) if D.REG[a]["genre"] == "offre" and I.nature[a] == PC.VRAIE and D.REG[a]["date"] and abs((D.REG[a]["date"] - d0).days) <= 7]
        for a in offs:
            for x in D.par_bien.get(b, []):
                r = D.REG[x]
                if r["genre"] == "compromis" and I.nature[x] == PC.VRAIE and r["montant"] == D.REG[a]["montant"] and r["hon"] is not None and round(r["hon"]) == com:
                    desig.add(b)
    if not desig: cpt["ne joue pas"] += 1; continue
    siens = {D.REG[a]["bien"] for a in pc if a in D.REG}
    k = "son bien, seul" if desig <= siens else ("son bien ET un autre" if desig & siens else "UN AUTRE bien")
    cpt[k] += 1
    if k != "son bien, seul": autres.append((i, sorted(desig), sorted(siens)))
print("   ", dict(cpt))
for x in autres[:20]: print("    ecart :", x)
