"""Les offres dont la colonne `date` porte NOTRE geste du 11/11 (ou la reparation du 12/11) -- 23/11. LECTURE SEULE.

Son mot du 23/11 (18) : « parmi les 97 lignes qui restent, combien ont au moins UNE piece dont la colonne `date` tombe le
11 ou le 12/11/2026 ? [...] Temoin positif : 11206, dont tu SAIS que la vraie date est le 02/12/2019. »
1 dans l'image : les pieces a la colonne `date` du 11-12/11/2026, par genre ; propositions_json rempli ?
2 LE LECTEUR DU PROTOCOLE (coupe_preuve_interne.Donnees.REG) : quelle date lit-il pour elles ? (temoin 11206)
3 les lignes du reste (passage 47 : 97 ; passage 51 : 91) qui touchent une telle piece -- par leur gel ou par leur bien
4 les lignes TRANCHEES qui en tiennent une, et par quelle preuve. Carnet : section 20.31.
"""
import sys, sqlite3, json
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC
I = P.Image(P.IMAGES / "2026-11-23_080234"); D = I.D
JOURS = ("2026-11-11", "2026-11-12")
print("=== 1 L'IMAGE : les pieces dont la colonne `date` porte le 11 ou le 12/11/2026")
touchees = {a: p for a, p in I.pieces.items() if str(p.get("date") or "")[:10] in JOURS}
print("   par genre et jour :", dict(Counter((p["kind"], str(p["date"])[:10]) for p in touchees.values())))
print("   biens distincts :", len({p["hektor_annonce_id"] for p in touchees.values()}),
      "| etats :", dict(Counter(p["state"] for p in touchees.values())))
def props(p):
    try:
        pp = json.loads(p.get("propositions_json") or "[]")
    except ValueError:
        return []
    return [x for x in (pp if isinstance(pp, list) else [pp]) if isinstance(x, dict) and x.get("type") == "proposition"]
print("   propositions_json avec une proposition :", sum(1 for p in touchees.values() if props(p)), "sur", len(touchees))
print("\n=== 2 CE QUE LIT LE PROTOCOLE (D.REG, coupe_preuve_interne : « la date d'une offre = sa 1re proposition »)")
lu = Counter()
for a, p in touchees.items():
    d = D.REG[a]["date"]
    lu["le 11-12/11/2026 (la date du geste)" if d and str(d) in JOURS else ("aucune date" if not d else "une autre date (la proposition)")] += 1
print("   ", dict(lu))
p = I.pieces[11206]
print("   TEMOIN 11206 : colonne `date` %s | 1re proposition %s | le protocole lit %s" % (
    p["date"], props(p)[0]["date"] if props(p) else None, D.REG[11206]["date"]))
autres_genres = [a for a, p in touchees.items() if p["kind"] != "offre"]
print("   pieces touchees qui ne sont PAS des offres (le lecteur ne les corrige pas) :", len(autres_genres),
      [(a, I.pieces[a]["kind"], I.pieces[a]["date"]) for a in autres_genres[:8]])
print("\n=== 3 LE RESTE A VIDER : les lignes qui touchent une telle piece")
c = sqlite3.connect("file:C:/Hektor/chantier_classeur_q6_cache/protocole/socle.sqlite?mode=ro", uri=True)
for pid in (47, 51):
    V = {i: (v, m, json.loads(b or "[]")) for i, v, m, b in c.execute("select id_unique, verdict, motif, biens from verdict where passage=?", (pid,))}
    reste = [i for i, (v, m, b) in V.items() if v == "ATTENTE" and m != "RIEN_A_ETIQUETER"]
    par_gel, par_bien, motifs = set(), set(), Counter()
    for i in reste:
        g = {x["piece"] for x in I.gel_par_ligne.get(i, [])} & set(touchees)
        bb = {a for b in V[i][2] for a in D.par_bien.get(b, [])} & set(touchees)
        if g: par_gel.add(i)
        if g or bb:
            par_bien.add(i); motifs[V[i][1]] += 1
    print("   passage %d : reste %d lignes -> %d touchent une telle piece par leur GEL, %d par leur gel OU leur bien %s"
          % (pid, len(reste), len(par_gel), len(par_bien), dict(motifs)))
    if pid == 51:
        for i in sorted(par_bien):
            pcs = sorted(({x["piece"] for x in I.gel_par_ligne.get(i, [])} | {a for b in V[i][2] for a in D.par_bien.get(b, [])}) & set(touchees))
            print("      %s (%s) : %s" % (i, V[i][1], "; ".join("%d %s %s col. %s -> lu %s" % (a, I.pieces[a]["kind"], I.pieces[a]["state"],
                  str(I.pieces[a]["date"])[:10], D.REG[a]["date"]) for a in pcs)))
print("\n=== 4 LES LIGNES TRANCHEES (passage 51) qui tiennent une telle piece, et la preuve de cette piece")
cpt = Counter(); ex = []
for i, pcs, pr in c.execute("select id_unique, pieces, preuves from verdict where passage=51 and verdict='TRANCHEE'"):
    pcs = json.loads(pcs or "[]"); prv = json.loads(pr or "[]") if pr else []
    for a in pcs:
        if a in touchees:
            t = " ".join(x for x in prv if isinstance(x, str) and x.startswith("%d " % a))
            if any(j in t for j in JOURS):
                k = "cite la date du geste (11-12/11/2026)"
            elif "= colonne" in t and D.REG[a]["date"] and str(D.REG[a]["date"]) in t:
                k = "prouvee par SA VRAIE DATE (la 1re proposition) au jour exact"
            elif not t:
                k = "sans preuve propre (suit sa ligne : regle, sa decision)"
            else:
                k = "autre preuve (prix, honoraires, regle)"
            cpt[k] += 1
            if len(ex) < 3 and "VRAIE" in k: ex.append((i, t[:110]))
print("   ", dict(cpt), "| ex.", ex)
