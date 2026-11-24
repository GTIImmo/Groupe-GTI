"""LA VENTILATION DES 3 051 ECARTS DU CONTROLE « SHEET CONTRE REGISTRE » (passage 79) -- son 4e mot du 24/11.

SON MOT : « Je veux TA ventilation, ecrite : sur les 3 051, combien sont un ecart de LECTURE (et lequel), combien sont HORS
PERIMETRE par une decision deja prise (laquelle, et de quand), et combien sont de VRAIES anomalies a traiter. Les trois totaux
doivent faire 3 051. » -- et « ② TES DEUX CHIFFRES DE REPARTITION NE SE RECOUPENT PAS [...] le meme ecart doit porter le meme
nom des deux cotes, ou alors dis ce que chaque mesure regarde que l'autre ne regarde pas. »

ENTREES (toutes deja ecrites, rien de remesure sauf la commission, relue par la bonne colonne) :
  . notice/PROTOCOLE_CONTROLE_SHEET_CONTRE_REGISTRE_PASSAGE_79_2026-11-24.csv (les 3 051, ligne par ligne)
  . le journal du geste des 42 (pose le 24/11) et les 4 nommees ; R26 (posee le 24/11, les 5 ventes)
  . notice/PROTOCOLE_REALIGNEMENT_TEMPS1_LES_ANOMALIES_PASSAGE_79_AVEC_R26_2026-11-24.csv (la classe de chaque ecriture)
  . notice/PROTOCOLE_REALIGNEMENT_TEMPS2_REPARTITION_A_L_ARRIVEE_PASSAGE_79_AVEC_R26_2026-11-24.csv (les 89 a l'arrivee)
  . les rapports des lots C2, C3, C8 ; l'image du passage (le Sheet, les pieces) ; la copie locale (honoraires_entree_app)
LECTURE SEULE. Sorties : notice/PROTOCOLE_VENTILATION_DES_3051_PASSAGE_79_2026-11-24.csv et
notice/PROTOCOLE_REPARTITION_172_CONTRE_89_PASSAGE_79_2026-11-24.csv

USAGE : python -X utf8 phase2/checks/protocole_ventilation_des_3051_2026-11-24.py
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import coupe_preuve_interne as K  # noqa: E402
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
N = P.NOTICE


def lire(f):
    return list(csv.DictReader(open(N / f, encoding="utf-8-sig"), delimiter=";"))


CTRL = lire("PROTOCOLE_CONTROLE_SHEET_CONTRE_REGISTRE_PASSAGE_79_2026-11-24.csv")
ANO = {(x["colonne"], x["cle (piece / ligne / mandat)"]): x
       for x in lire("PROTOCOLE_REALIGNEMENT_TEMPS1_LES_ANOMALIES_PASSAGE_79_AVEC_R26_2026-11-24.csv")}
NOMS_T1 = {"date_annulation_app": "Annulee", "numero_facture_app": "Numero de facture", "vente_reglee_app": "Vente Reglee",
           "note": "les notes (F / G)"}
assert len(CTRL) == 3051
J = json.loads((P.DOSSIER / "realignement_temps1_journal_passage_79_avec_r26_2026-11-24.json").read_text(encoding="utf-8"))
GESTE = {(g["ligne"], int(g["de"]), g["famille"]): g for g in J["gestes"]}
NOMMEE = {(n["ligne"], int(n["de"]), n["famille"]): n for n in J["nommees"]}
R26 = {"8BJKJ6XP": 21662, "8BUW2ZVH": 12182, "HPNJ32UM": 28147, "WJ8NY16C": 7126, "ZYVO6KK1": 16019}
T2 = {x["id_unique"]: x for x in lire("PROTOCOLE_REALIGNEMENT_TEMPS2_REPARTITION_A_L_ARRIVEE_PASSAGE_79_AVEC_R26_2026-11-24.csv")}
C2 = {x["id_unique"]: x["lot"] for x in lire("C2_LES_COMMISSIONS_A_POSER_2026-11-17.csv")}
C3 = defaultdict(list)
for x in lire("C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv"):
    C3[x["id_unique"]].append(x)

con = P.socle()
image, = con.execute("select image from passage where id=79").fetchone()
V = {i: {"num": num, "verdict": v, "pieces": set(json.loads(ps)) if ps else set()}
     for i, num, v, ps in con.execute("select id_unique, num, verdict, pieces from verdict where passage=79")}
con.close()
I = P.Image(P.IMAGES / image)
D, PI = I.D, I.pieces
GEL = defaultdict(set)
for i, a, *_r in I.gel:
    GEL[i].add(int(a))
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
HAPP = {int(a): K.nombre(v) for a, v in loc.execute(
    "select app_affaire_id, honoraires_entree_app from app_affaire_ledger where honoraires_entree_app is not null")}

LECTURE, HORS, TRAITER = "1 LECTURE", "2 HORS PERIMETRE (decision deja prise)", "3 A TRAITER"


def commission(i):
    """La Commission TTC relue par la BONNE colonne (son 2e mot du 24/11 : « compare la Commission TTC a
    honoraires_entree ») : honoraires_entree (Hektor) ou honoraires_entree_app (notre lot C2), sur les pieces du protocole
    ET du gel de la ligne."""
    com = K.nombre(D.case(i, "Commission TTC"))
    ps = (V[i]["pieces"] | GEL.get(i, set())) & set(PI)
    hek = {a: K.nombre(PI[a].get("honoraires_entree")) for a in ps}
    app = {a: HAPP.get(a) for a in ps}
    if com is None:
        return "illisible", com, hek, app
    if any(v is not None and abs(v - com) <= 1.5 for v in list(hek.values()) + list(app.values())):
        return "accord", com, hek, app
    if any(v for v in hek.values()):
        return "hektor_autre", com, hek, app
    return "rien", com, hek, app


OUT = []
for x in CTRL:
    i, col, cause = x["id_unique"], x["colonne"], x["cause"]
    try:
        piece = int(cause.rsplit(":", 1)[1].strip()) if ": " in cause and cause.rsplit(":", 1)[1].strip().isdigit() else (
            int(x["piece"]) if x["piece"].strip().isdigit() else None)
    except ValueError:
        piece = None
    b = sc = qui = dev = ""
    # ── LA COMMISSION ────────────────────────────────────────────────────────────────────────────────────────────────
    if col.startswith("commission (commission_agence"):
        b, sc = LECTURE, "la colonne comparee n'est pas la commission"
        qui = ("commission_agence = la part HT d'UNE personne, selon l'epoque (ma mesure du 24/11, ④) ; TA DECISION du 24/11 "
               "(2e mot) : « SORS commission_agence DE TON CONTROLE »")
        dev = "sortie du controle"
    elif col.startswith("commission (honoraires"):
        st, com, hek, app = commission(i)
        if st == "accord":
            b, sc = LECTURE, "la commission est la, sur une autre colonne ou une autre piece"
            qui = ("le controle lisait les honoraires du seul compromis (montant - prix net vendeur) ; relue par "
                   "honoraires_entree / honoraires_entree_app (ta consigne du 24/11), elle CONCORDE")
            dev = "rien a faire"
        elif st == "hektor_autre":
            b, sc = HORS, "Hektor porte une autre commission : on ne remplit que nos cases vides"
            qui = ("lot 2 « P Commission TTC : LES VIDES » (choix du 09/11, DECISIONS_CHAMP_PAR_CHAMP § lot 2) ; un conflit n'est "
                   "pas une erreur -- 44 des 83 sont un facteur 2 (le classeur note UNE part, nous le total)")
            dev = "rien a ecrire (Hektor fait foi, classe C)"
        elif C2.get(i) == "non_posee_annulee":
            b, sc = HORS, "hors du perimetre du lot C2 : affaire annulee"
            qui = ("lot C2 du 17/11, SA DECISION : les commissions des affaires annulees (prevues, jamais percues) NE SONT PAS "
                   "POSEES (270)")
            dev = "rien a ecrire"
        elif C2.get(i) is None:
            b, sc = HORS, "absente du lot C2 : nous portions deja une commission, ou aucune transaction n'y etait reliee"
            qui = ("lot 2 « P Commission TTC : LES VIDES » (choix du 09/11) applique par C2 le 17/11 : une ligne dont une "
                   "transaction porte deja une commission (honoraires ou commission_agence) n'est pas remplie")
            dev = "rien a ecrire"
        else:
            b, sc = TRAITER, "la commission du Sheet n'est nulle part chez nous"
            qui = "-"
            dev = "nommee : a lui"
    # ── LES DATES (offre, compromis, vente fixee) : JAMAIS reecrites ─────────────────────────────────────────────────
    elif col.startswith("date "):
        b = HORS
        sc = ("aucune de ses pieces n'est datee de ce jour" if cause.startswith("aucune") else
              "pas de piece de ce genre dans ses pieces" if cause.startswith("pas de") else "case du Sheet illisible")
        qui = ("lot 3 « LES DATES » (choix du 09/11) : « un ecart de date n'est pas une erreur » (reserve du 29/10 fermee le "
               "09/11 ; 265 des 413 ecarts d'offre a moins de 7 jours) ; SA REGLE : on ne corrige pas une date ; la date est "
               "une PREUVE du protocole, pas une ecriture rapatriee")
        dev = "rien a ecrire" + (" ; la vente de sa ligne est emportee par R26" if i in R26 and "vente" in col else "")
    # ── LA REPARTITION ──────────────────────────────────────────────────────────────────────────────────────────────
    elif col.startswith("repartition"):
        t2 = T2.get(i)
        if cause.startswith("le 13/11 n'a pas pu lire"):
            b, sc = HORS, "le rapatriement du 13/11 a refuse la ligne (%s)" % cause.split("(")[1].split(")")[0]
            qui = ("SES REGLES du 13/11 (rapatrier_repartition_classeur.py, « regle du classeur (Frederic 13/11) ») : un "
                   "apporteur avec une part n'est pas une personne, un nom non resolu n'est pas devine ; la chaine garde ce "
                   "qu'elle avait")
            dev = "a l'arrivee : %s" % (t2["verdict"] if t2 else "JUSTE")
        elif "SUPPOSITION" in cause:
            b, sc = TRAITER, "une supposition de Hektor, jamais remplacee par le classeur"
            qui = "TA DECISION du 24/11 (3e mot, ④) : « le classeur fait foi : tu remplaces la supposition »"
            dev = "A2 (a venir) ; a l'arrivee aujourd'hui : %s" % (t2["verdict"] if t2 else "JUSTE")
        else:
            if t2 is None:
                b, sc = TRAITER, cause.split(" :")[0].split(" (")[0]
                qui = "-"
                dev = "CORRIGEE A L'ARRIVEE par la vague + A2 (temps 2 : la ligne y est JUSTE)"
            elif t2["verdict"].startswith("CONFLIT"):
                b, sc = HORS, "le conflit nomme"
                qui = "TA DECISION du 24/11 (2e mot) : U0GQ3KTO « laisse-la en place, en reserve »"
                dev = "en reserve"
            elif "Annul" in t2["verdict"]:
                b, sc = HORS, "une annulee : aucune part"
                qui = "TA DECISION du 24/11 (3e mot, ④) : « les 49 annulees : ON LAISSE, aucune part » (meme raison que C2, 17/11)"
                dev = "a l'arrivee : " + t2["verdict"]
            else:
                b, sc = TRAITER, cause.split(" :")[0].split(" (")[0]
                qui = "-"
                dev = "a l'arrivee : " + t2["verdict"] + " (nommee au temps 2)"
    # ── LES ECRITURES RAPATRIEES (annulation, facture, reglement, textes F / G) ───────────────────────────────────────
    else:
        fam = {"annulation": "date_annulation_app", "facture": "numero_facture_app", "reglement": "vente_reglee_app"}.get(col, "note")
        if "PIECE NEUTRE" in cause.upper() or "piece neutre" in cause:
            b, sc = LECTURE, "sur une piece NEUTRE de sa ligne"
            qui = ("la cle du controle (les pieces PROUVEES seules) ne voit pas la piece neutre ; le temps 1 (24/11) l'a jugee : "
                   "a sa ligne au gel, seule, dans son dossier a l'arrivee -- A SA PLACE")
            dev = "rien a faire"
        elif cause.startswith("ecartee le 16/11 par"):
            lot = cause.split("par ")[1].split(" ")[0]
            b, sc = HORS, "ecartee par %s : %s" % (lot, cause.rsplit(": ", 1)[1])
            qui = ("lot C3 du 16/11 : SA REGLE « la date d'annulation du Sheet est celle du COMPROMIS », perimetre de 450 arrete "
                   "par lui le 16/11 (une offre refusee porte deja sa date de refus, regle du 12/11)" if lot == "C3" else
                   "lot C8 du 16/11 : vente reglee et facture sur la VENTE ; sans vente, rien n'est pose")
            dev = "rien a ecrire"
        elif cause.startswith("absente du lot"):
            b, sc = TRAITER, "case remplie (ou ligne nee) APRES le rapatriement du 16/11"
            qui = "-"
            dev = "nouveaute du Sheet : a lui (le rapatriement ne suit pas le Sheet)"
        elif cause.startswith("le registre porte une facture") or (cause.startswith("la case du Sheet") and i not in C3
                                                                    and V[i]["pieces"] and fam == "numero_facture_app"
                                                                    and x["registre"] != "-"):
            b, sc = LECTURE, "le registre porte le TEXTE du Sheet, pas un code GGTI"
            qui = "C8 (16/11) a pris la case telle quelle (sa consigne « sans interpreter ») ; le controle attendait un code"
            dev = "rien a faire"
        elif cause.startswith("la case du Sheet ne porte aucun code"):
            v8 = next((y for y in lire("C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv") if y["id_unique"] == i), {})
            if v8.get("verdict") == "aucune_vente":
                b, sc = HORS, "ecartee par C8 : aucune_vente (texte libre)"
                qui = "lot C8 du 16/11 : sans vente, rien n'est pose"
                dev = "rien a ecrire"
            else:
                b, sc = LECTURE, "un code G4..., pas GGTI, pose par C8 sur une piece neutre de sa ligne"
                qui = "C8 (16/11) l'a pose tel quel sur %s ; la piece est neutre (temps 1)" % v8.get("app_affaire_id")
                dev = "rien a faire"
        elif cause.startswith("la date differe") and fam == "vente_reglee_app":
            b, sc = LECTURE, "la valeur n'est pas une date lisible ; elle est EGALE au Sheet"
            qui = "C8 (16/11) a pris la case telle quelle ; le controle n'a pas su la lire comme une date"
            dev = "rien a faire"
        elif cause.startswith("la date differe") and fam == "date_annulation_app":
            autre = next((y for y in C3.get(i, [])), {})
            if i in ("T2GZOY5O",):
                b, sc = TRAITER, "deux lignes jumelles (T2GZOY5O, O6R10ZQA) tiennent le meme compromis 20073"
                qui = "-"
                dev = "nommee : 20073 porte la date de O6R10ZQA (21/09/2021), le Sheet de T2GZOY5O dit 21/11/2021 -- a lui"
            else:
                b, sc = TRAITER, "son compromis portait la date d'une AUTRE ligne ; la sienne n'est posee nulle part"
                qui = ("C3 (16/11) l'avait ecartee comme « offre seule » (gel du 16/11), alors que le protocole lui donne "
                       "aujourd'hui le compromis %s" % (piece or x["piece"]))
                dev = ("la date etrangere a quitte %s le 24/11 (geste des 42) ; SA date reste a poser sur son compromis : "
                       "proposition, a lui" % (piece or x["piece"]))
        elif "POSEE" in cause:
            g = GESTE.get((None, piece, fam)) or next((v for (L_, a_, f_), v in GESTE.items() if a_ == piece and f_ == fam), None)
            n_ = next((v for (L_, a_, f_), v in NOMMEE.items() if a_ == piece and f_ == fam), None)
            if g:
                b, sc = TRAITER, "sur la piece d'une autre ligne, ou hors de son dossier"
                qui = "-"
                dev = "TRAITEE le 24/11 : %s (geste des 42, journal n° %d)" % (
                    "deplacee vers %s" % g["vers"] if g["vers"] else "MISE DE COTE avec son ancienne place",
                    J["gestes"].index(g) + 1)
            elif n_:
                b, sc = TRAITER, "nommee (une des 4)"
                qui = "-"
                dev = "NOMMEE au journal le 24/11 (laissee en place) : %s" % n_["raison"][:90]
            elif ANO.get((NOMS_T1.get(fam), str(piece)), {}).get("classe", "").startswith("JUSTE POUR LA LIGNE QUI TIENT"):
                b, sc = LECTURE, "la meme valeur est celle de la ligne qui tient la piece"
                qui = "le temps 1 (24/11) : « JUSTE POUR LA LIGNE QUI TIENT LA PIECE » -- laissee"
                dev = "rien a faire"
            elif i in R26 and piece == R26[i]:
                b, sc = TRAITER, "sur la vente que la vague laissait derriere"
                qui = "-"
                dev = "TRAITEE par R26 (posee le 24/11) : la coupe emporte la vente avec sa ligne"
            else:
                b, sc = TRAITER, "non rattachee"
                qui = "-"
                dev = "⛔ A EXAMINER"
        else:
            b, sc, qui, dev = TRAITER, cause[:60], "-", "⛔ A EXAMINER"
    # la CHARGE
    if col == "charge commission":
        if cause.startswith("ses pieces ne portent aucun numero"):
            b, sc = LECTURE, "la cle du controle manque (aucun numero de mandat sur ses pieces)"
            qui = "la charge vit sur le MANDAT (carnet app_mandat_champ_app) ; sans mandat, le controle ne peut pas la lire"
            dev = "rien a conclure"
        elif cause.startswith("le carnet du mandat ne porte"):
            b, sc = TRAITER, "le carnet ne porte aucune charge pour ce mandat"
            qui = ("TA DECISION du 02/11 (§ 3) : « le classeur fait foi », completer « les lignes possibles » au rattrapage -- "
                   "le lot C1 du 14/11 ne les a pas reliees ; le controle les relie par le mandat de leurs pieces")
            dev = "a completer : a lui"
        else:
            b, sc = TRAITER, "le carnet porte une AUTRE charge, venue de Hektor"
            qui = "TA DECISION du 02/11 (§ 3) : « le classeur fait foi »"
            dev = "a corriger : a lui (jugees le 03/11, JUGE_CHARGE_CLASSEUR_HEKTOR)"
    OUT.append({"bucket": b, "colonne": col, "id_unique": i, "ligne_du_sheet": x["ligne_du_sheet"], "sous_cause": sc,
                "decision_ou_lecture": qui, "devenir": dev, "cause_du_controle": cause, "sheet": x["sheet"],
                "registre": x["registre"], "piece": x["piece"]})

assert len(OUT) == 3051
cb = Counter(o["bucket"] for o in OUT)
print("LES 3 051 : %s ; total %d" % (" . ".join("%s %d" % kv for kv in sorted(cb.items())), sum(cb.values())))
for bk in sorted(cb):
    print()
    print(bk, cb[bk])
    for (col, sc), n in sorted(Counter((o["colonne"], o["sous_cause"]) for o in OUT if o["bucket"] == bk).items(),
                               key=lambda kv: -kv[1]):
        print("   %4d  %-45s %s" % (n, col[:45], sc))
print()
print("LE DEVENIR DES « A TRAITER » :")
for d, n in Counter(o["devenir"].split(" (")[0].split(" : ")[0] for o in OUT if o["bucket"] == TRAITER).most_common():
    print("   %4d  %s" % (n, d))
ex = [o for o in OUT if "A EXAMINER" in o["devenir"]]
print("⛔ A EXAMINER (attendu 0) : %d %s" % (len(ex), [(o["colonne"], o["id_unique"], o["cause_du_controle"][:60]) for o in ex[:10]]))
with (N / "PROTOCOLE_VENTILATION_DES_3051_PASSAGE_79_2026-11-24.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(OUT[0].keys()), delimiter=";")
    w.writeheader()
    for o in sorted(OUT, key=lambda o: (o["bucket"], o["colonne"], o["sous_cause"], o["id_unique"])):
        w.writerow(o)

# ═══════════════ ② LA REPARTITION : LES 172 DU CONTROLE (aujourd'hui) CONTRE LES 89 DU TEMPS 2 (a l'arrivee) ═══════════
print()
print("② LA REPARTITION, LIGNE PAR LIGNE")
REP = defaultdict(list)
for o in OUT:
    if o["colonne"].startswith("repartition"):
        REP[o["id_unique"]].append(o)
lignes = sorted(set(REP) | set(T2))
R2 = []
for i in lignes:
    cotes = "+".join(sorted(o["colonne"].split()[1] for o in REP.get(i, [])))
    causes = " / ".join(sorted({o["cause_du_controle"].split(" :")[0].split(" (")[0] for o in REP.get(i, [])}))
    t2 = T2.get(i)
    if i in REP and t2:
        cas = "LES DEUX : le meme ecart, aujourd'hui ET a l'arrivee"
    elif i in REP:
        cas = "LE CONTROLE SEUL : faux aujourd'hui, JUSTE a l'arrivee (la vague + A2 le corrigent)"
    else:
        cas = "LE TEMPS 2 SEUL : juste aujourd'hui (ou non compare), faux a l'arrivee"
    R2.append({"cas": cas, "id_unique": i, "ligne_du_sheet": V.get(i, {}).get("num", ""), "controle_aujourd_hui": causes or "-",
               "cotes": cotes or "-", "temps2_a_l_arrivee": t2["verdict"] if t2 else "JUSTE",
               "pourquoi_le_temps2_seul": "" if i in REP else (
                   "le Sheet ne nomme aucun negociateur : le controle ne compare pas" if not any(
                       D.case(i, "Négociateur %d" % k).strip() for k in (1, 2, 3)) else
                   "aujourd'hui sa chaine porte une repartition qui lui CONCORDE (celle d'une autre tentative de la meme "
                   "chaine) ; la vague la coupe de cette chaine" if t2 and "AUCUNE PART" in t2["verdict"] else
                   "aujourd'hui sa chaine CONCORDE au Sheet ; a l'arrivee le temps 2 lit le nom par l'annuaire (RR.resoudre)")})
for (cas,), n in sorted(Counter((r["cas"],) for r in R2).items()):
    print("   %4d lignes : %s" % (n, cas))
for cas in sorted({r["cas"] for r in R2}):
    print("   -- %s" % cas)
    for (c, t), n in Counter((r["controle_aujourd_hui"][:70], r["temps2_a_l_arrivee"][:55]) for r in R2 if r["cas"] == cas).most_common():
        print("      %3d  controle : %-70s | temps 2 : %s" % (n, c, t))
    for p_, n in Counter(r["pourquoi_le_temps2_seul"][:110] for r in R2 if r["cas"] == cas and r["pourquoi_le_temps2_seul"]).most_common():
        print("      %3d  pourquoi : %s" % (n, p_))
print("   lignes du controle : %d (%d ecarts) ; lignes du temps 2 : %d ; communes : %d" % (
    len(REP), sum(len(v) for v in REP.values()), len(T2), len(set(REP) & set(T2))))
with (N / "PROTOCOLE_REPARTITION_172_CONTRE_89_PASSAGE_79_2026-11-24.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(R2[0].keys()), delimiter=";")
    w.writeheader()
    for r in sorted(R2, key=lambda r: (r["cas"], r["temps2_a_l_arrivee"], r["id_unique"])):
        w.writerow(r)
print("-> notice/PROTOCOLE_VENTILATION_DES_3051_PASSAGE_79_2026-11-24.csv")
print("-> notice/PROTOCOLE_REPARTITION_172_CONTRE_89_PASSAGE_79_2026-11-24.csv")
