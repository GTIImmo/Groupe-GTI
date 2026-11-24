"""LE CONTROLE DU § 7 (24/11) : CHAQUE ECRITURE RAPATRIEE EST-ELLE TOUJOURS SUR LA BONNE LIGNE DE SON REGISTRE ?
LECTURE SEULE : l'image du 23/11 08:02 (le Sheet, le registre des transactions), le passage P du socle (les pieces de
chaque ligne tranchee -- « une fois le chainage corrige »), le registre local en lecture (app_affaire_repartition,
app_affaire_note). Rien en base, rien dans le Sheet, rien chez Hektor.

Son mot : « tu compares COLONNE PAR COLONNE le Sheet et mon registre des transactions, et tu me dis ou ca ne colle pas.
Pas un total : une liste de lignes NOMMEES. [...] UN FICHIER, une ligne par ecart : l'ID Unique, la colonne, ce que dit le
Sheet, ce que dit le registre, et la piece concernee ; RANGE PAR GRAVITE : d'abord l'argent (repartition, commission,
facture), puis les dates, puis les textes ; ⛔ ET UN TEMOIN INVERSE : combien de lignes sont EN ACCORD sur chaque colonne
[...] ⚠ les 237 lignes a plusieurs chaines sont a part, declarees, pas melangees. »

LES PIECES D'UNE LIGNE : celles du protocole (passage P) si elle est TRANCHEE ; une ligne EN ATTENTE n'a pas de pieces sures
-> elle est DECLAREE a part (ses cases remplies sont comptees, jamais comparees). LES 237 : les lignes dont les pieces
GELEES sont dans plusieurs chaines (sa mesure : 4 723 lignes gelees, 4 486 a une chaine, 237 a plusieurs -- le temoin du
decoupage) -- comparees, mais rangees a part.

LES COLONNES (son § 7), dans l'ordre de gravite :
  1 REPARTITION  Negociateur 1/2/3 + Pourcentage 1/2/3, decomposes par LA regle du 13/11 (rapatrier_repartition_classeur :
                 la tete prend l'entree pour 50, le reste va a la sortie) -- contre app_affaire_repartition de la chaine de
                 sa piece la plus avancee (vente, compromis, offre), ENTREE et SORTIE comparees SEPAREMENT
  2 COMMISSION   « Commission TTC » contre les honoraires de son compromis (montant - prix net vendeur) et contre la
                 commission_agence de sa vente (HT x 1,2, ou TTC) ; « Charge Commission » contre charge_commission_app
  3 FACTURE      « Numero de facture » (ses codes GGTI / AVR) contre numero_facture_app de sa vente
  4 REGLEMENT    « Vente Reglee » contre vente_reglee_app de sa vente
  5 ANNULATION   « Annulee » contre date_annulation_app de son compromis (le motif n'a pas de colonne au Sheet)
  6 DATES        « Offre Achat », « Compromis », « Vente Fixee » contre la date de ses pieces (une offre : sa 1re proposition)
  7 TEXTES       « En attente de » (F) et « COMMENTAIRES » (G) contre app_affaire_note (classeur:F, classeur:G, F+G)
LA CAUSE D'UNE CASE REMPLIE AU SHEET ET VIDE AU REGISTRE : sa ligne n'a pas de piece du genre ; ou ⛔ la valeur a ete
rapatriee PAR LE GEL sur une piece que le protocole donne a une AUTRE ligne (ou a personne) -- l'ecriture n'est pas sur la
bonne ligne ; ou sa piece existe et la valeur n'y a jamais ete rapatriee.

USAGE : python -u -X utf8 phase2/checks/protocole_controle_sheet_contre_registre_2026-11-24.py --passage P
"""
import sys, json, sqlite3, csv, re, argparse
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks"); sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P, piece_copie_ou_vraie as PC, coupe_preuve_interne as K
import rapatrier_repartition_classeur as RR
import protocole_portes as PO
sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--passage", type=int, required=True)
arg = ap.parse_args()


def dire(s=""):
    print(s, flush=True)


con = P.socle()
image, version = con.execute("select image, version from passage where id=?", (arg.passage,)).fetchone()
V = {}
for i, num, v, ps, m in con.execute("select id_unique, num, verdict, pieces, motif from verdict where passage=?",
                                    (arg.passage,)):
    V[i] = {"num": num, "verdict": v, "pieces": json.loads(ps) if ps else [], "motif": m}
con.close()
I = P.Image(P.IMAGES / image)
D = I.D
PI = I.pieces
gel = defaultdict(set)
gel_p = defaultdict(set)
for i, a, *_r in I.gel:
    gel[i].add(int(a))
    gel_p[int(a)].add(i)
# L'ARRIVEE (le rejeu E du passage, en cache) : une valeur posee sur une piece que le protocole ne donne a PERSONNE reste-t-
#   elle DANS le dossier de sa ligne a l'arrivee (une piece neutre, a part sans effet : sans danger) ou en SORT-elle ?
_br = P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % arg.passage)
CHE, _r = PO.rejeu_en_cache("E", image, _br, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)


def a_l_arrivee(i, a):
    cs = {CHE.get(q) for q in V[i]["pieces"]}
    return ("DANS son dossier a l'arrivee (piece neutre : sans danger)" if CHE.get(a) in cs
            else "⛔ HORS de son dossier a l'arrivee")


def qui_tient(i, a):
    qui = "+".join(sorted(TIENT.get(a, set())))
    return ("PERSONNE -- " + a_l_arrivee(i, a)) if not qui else "UNE AUTRE LIGNE (%s)" % qui


TIENT = defaultdict(set)
for i, v in V.items():
    if v["verdict"] == "TRANCHEE":
        for a in v["pieces"]:
            TIENT[a].add(i)
chaines_gel = {i: {PI[a]["app_chaine_id"] for a in gel[i] if a in PI} for i in D.LIG if gel.get(i)}
A_PART_237 = {i for i, cs in chaines_gel.items() if len(cs) > 1}
dire("LE CONTROLE DU § 7 -- passage %d (%s), image %s" % (arg.passage, version, image))
dire("   TEMOIN DU DECOUPAGE (sa mesure) : %d lignes ont une piece gelee ; %d a une seule chaine ; %d a PLUSIEURS (attendu "
     "4 723 / 4 486 / 237)" % (len(chaines_gel), sum(1 for c in chaines_gel.values() if len(c) == 1), len(A_PART_237)))
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
loc.row_factory = sqlite3.Row
# ⛔ SA REGLE (06/11) : l'identite d'un ADMIN n'est jamais ecrite sur un document -- les comptes admin sont reperes par
#   leur NUMERO (jamais par un nom ecrit ici) et leur nom est remplace dans le fichier
COMPTES_ADMIN = {"46"}
REP = defaultdict(list)
for r in loc.execute("select app_chaine_id, cote, rang, hektor_user_id, "
                     "case when cast(hektor_user_id as text) in (%s) then '[compte admin]' else nom_au_moment end "
                     "as nom_au_moment, pourcentage, origine from app_affaire_repartition"
                     % ",".join("'%s'" % x for x in COMPTES_ADMIN)):
    REP[int(r["app_chaine_id"])].append(dict(r))
# ⭐ LA RESOLUTION DES NOMS DU 13/11 (rapatrier_repartition_classeur.resoudre) : l'annuaire des negociateurs (ici la copie
#   locale de app_hektor_negotiator_agency_directory), ses deux alias (GIRAUD -> Aline VALETTE, ALVES MENDES -> Lucie
#   DECHANDON : la table app_classeur_alias_negociateur en porte 2, le repli code les memes), les initiales (« VALLA A »),
#   et ses levees d'ambiguite (CHAMPAGNAC, REYNAUD, MARTINEZ, BOUCHET) -- on compare LA PERSONNE (hektor_user_id)
RR.RAP.ALIAS_NEGOCIATEUR = dict(RR.RAP.ALIAS_REPLI)
_gens = defaultdict(list)
for r in loc.execute("select hektor_user_id, nom, prenom, is_active from app_hektor_negotiator_agency_directory"):
    nom_ = " ".join(sorted(RR.mots_du_nom(r["nom"])))
    pre_ = " ".join(sorted(RR.mots_du_nom(r["prenom"])))
    if nom_:
        _gens[(nom_, pre_)].append(dict(r))
PAR_NOM = defaultdict(list)
for (nom_, pre_), fiches in _gens.items():
    act = [f_ for f_ in fiches if f_.get("is_active") in (1, "1", True, "true", "True")]
    choix = sorted(act or fiches, key=lambda f_: int(str(f_["hektor_user_id"])))[0]
    PAR_NOM[nom_].append({"nom": nom_, "prenom": pre_, "hektor_user_id": str(choix["hektor_user_id"]),
                          "fiches": len(fiches)})


def signature_sheet(i, sur_la_chaine):
    """La repartition que le rapatriement du 13/11 tirerait de la ligne : ({(cote, personne, part)}, refus)."""
    noms = [D.case(i, "Négociateur %d" % k) for k in (1, 2, 3)]
    pcts = [K.nombre(D.case(i, "Pourcentage %d" % k)) for k in (1, 2, 3)]
    parts, pq = RR.nettoyer(noms, pcts)
    if pq:
        return None, "nettoyage : " + pq
    qui = {}
    for nom, _p in parts:
        q, motif = RR.resoudre(nom, PAR_NOM, None, sur_la_chaine)
        if motif:
            return None, "resolution : %s -> %s" % (nom, motif)
        qui[nom] = q["hektor_user_id"]
    cotes, pq = RR.decomposer(parts)
    if pq:
        return None, "decomposition : " + pq
    return {(c, qui[n], round(pc, 2)) for c, _r, n, pc in cotes}, ""


def signature_rows(rows, cote=None):
    return {(r["cote"], str(r["hektor_user_id"]), round(float(r["pourcentage"] or 0), 2)) for r in rows
            if cote is None or r["cote"] == cote}


NOTES = defaultdict(list)
for a_, o_, t_ in loc.execute("select app_affaire_id, origine, texte from app_affaire_note"):
    NOTES[int(a_)].append((o_, t_ or ""))


def norm(s):
    return re.sub(r"[^0-9a-zà-ÿ]", "", (s or "").lower())


def textes_note(a):
    """{'F': {textes}, 'G': {textes}} rapatries sur la piece (normalises)."""
    out = defaultdict(set)
    for o_, t_ in NOTES.get(a, []):
        for m in re.finditer(r"(?:^|\n)([FG]) : [^\n]*? -- (.*?)(?=\n[FG] : |\Z)", t_, re.S):
            out[m.group(1)].add(norm(m.group(2)))
    return out


ECARTS = []
ACCORD = Counter()
COMPAREES = Counter()
CAUSES = defaultdict(Counter)
GRAVITE = {"repartition entree": 1, "repartition sortie": 1, "repartition": 1, "commission (honoraires du compromis)": 2,
           "commission (commission_agence de la vente)": 2, "charge commission": 2, "facture": 3, "reglement": 4,
           "annulation": 5, "date offre": 6, "date compromis": 6, "date vente fixee": 6, "texte F (en attente de)": 7,
           "texte G (commentaires)": 7}


def ecart(i, col, sheet, reg, piece, cause):
    ECARTS.append({"gravite": GRAVITE[col], "colonne": col, "id_unique": i, "ligne_du_sheet": V[i]["num"],
                   "verdict": V[i]["verdict"], "a_part_237": "oui" if i in A_PART_237 else "",
                   "sheet": sheet, "registre": reg, "piece": piece, "cause": cause})
    CAUSES[col][re.sub(r"\s*\((?=[^)]*\d)[^)]*\)", "", re.sub(r"\d{3,}", "N", cause))[:120]] += 1


def accord(i, col):
    ACCORD[(col, i in A_PART_237)] += 1


def pieces_de(i, genre):
    return sorted(a for a in V[i]["pieces"] if a in PI and PI[a]["kind"] == genre)


def ailleurs(i, champ, genre):
    """La valeur du champ portee par une piece GELEE de la ligne que le protocole ne lui donne pas : (piece, a qui)."""
    out = []
    for a in sorted(gel.get(i, set())):
        if a in PI and PI[a]["kind"] == genre and str(PI[a].get(champ) or "").strip() and a not in V[i]["pieces"]:
            out.append("%d (le protocole la donne a %s)" % (a, "+".join(sorted(TIENT.get(a, set()))) or "PERSONNE"))
    return out


# ⭐ LES LOTS DU 16/11 QUI ONT ECRIT CES VALEURS (leurs rapports, ligne par ligne) : C8 (vente reglee + facture, 3 730
#   « nette » posees, 72 « aucune_vente ») et C3 (dates d'annulation, SA REGLE : 450 « nette » posees ; 273 offre seule, 107
#   date anterieure, 63 aucune transaction, 4 compromis pas annule ecartes). La CAUSE ECRITE d'une case vide est la leur.
LOT = {}
for nom_, f_ in (("C8", "C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv"), ("C3", "C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv")):
    LOT[nom_] = {}
    for x in csv.DictReader(open(P.NOTICE / f_, encoding="utf-8-sig"), delimiter=";"):
        LOT[nom_][x["id_unique"]] = (x["verdict"], int(x["app_affaire_id"]) if str(x.get("app_affaire_id") or "").isdigit() else None)
LOT_DE = {"vente_reglee_app": "C8", "numero_facture_app": "C8", "date_annulation_app": "C3"}


def cause_absente(i, champ, genre):
    lot = LOT_DE.get(champ)
    if lot:
        v_, a_ = LOT[lot].get(i, (None, None))
        if v_ is None:
            return "absente du lot %s du 16/11 : la case a ete remplie, ou la ligne est nee, APRES le rapatriement" % lot
        if v_ != "nette":
            return "ecartee le 16/11 par %s (son perimetre) : %s" % (lot, v_)
        if a_ is not None and a_ not in V[i]["pieces"]:
            return "⛔ POSEE LE 16/11 SUR UNE PIECE QUE LE PROTOCOLE DONNE A %s : %d" % (qui_tient(i, a_), a_)
        if a_ is not None:
            return "posee le 16/11 sur sa piece %d, et ABSENTE aujourd'hui" % a_
    if not pieces_de(i, genre):
        return "pas de %s dans ses pieces" % genre
    al = ailleurs(i, champ, genre)
    if al:
        return "⛔ RAPATRIEE PAR LE GEL SUR UNE PIECE D'UNE AUTRE LIGNE : %s" % " ; ".join(al)
    return "jamais rapatriee : sa %s %s existe, la valeur n'y est pas" % (genre, " ".join(map(str, pieces_de(i, genre))))


T = [i for i in V if V[i]["verdict"] == "TRANCHEE"]
# LES NOTES QUE C4 A POSEES (son rapport du 17/11, 4 325) : la regle de C4 n'a pas tout pris -- ni les « V » seuls, ni les
#   six motifs d'annulation (ils vont dans motif_annulation_app), ni les 86 affaires EN COURS -> les cases F / G hors du
#   rapport sont DECLAREES (comptees), pas comparees
C4 = defaultdict(list)
for x in csv.DictReader(open(P.NOTICE / "C4_LES_NOTES_A_POSER_2026-11-17.csv", encoding="utf-8-sig"), delimiter=";"):
    C4[x["id_unique"]].append(x)
ATT = [i for i in V if V[i]["verdict"] != "TRANCHEE"]
dire("   lignes tranchees comparees : %d (dont %d des 237, rangees a part) ; lignes EN ATTENTE declarees a part : %d" % (
    len(T), sum(1 for i in T if i in A_PART_237), len(ATT)))
RANG = {"vente": 0, "compromis": 1, "offre": 2}
SOURCE = defaultdict(set)
for i_ in V:
    g_ = sorted((a for a in gel.get(i_, set()) if a in PI), key=lambda a: (RANG.get(PI[a]["kind"], 3), a))
    if g_:
        SOURCE[PI[g_[0]]["app_chaine_id"]].add(i_)
for i in sorted(T):
    # ── 1 LA REPARTITION (la personne, la part, le cote -- entree et sortie SEPAREMENT) ──
    noms = [D.case(i, "Négociateur %d" % k) for k in (1, 2, 3)]
    if any(n.strip() for n in noms):
        ps_ = sorted(V[i]["pieces"], key=lambda a: (RANG.get(PI[a]["kind"], 3), a) if a in PI else (9, a))
        ch = next((PI[a]["app_chaine_id"] for a in ps_ if a in PI and PI[a]["app_chaine_id"] in REP), None)
        rows = REP.get(ch, [])
        sig, refus = signature_sheet(i, {str(r["hektor_user_id"]) for r in rows})
        sheet_txt = " | ".join("%s %s" % (n.strip(), D.case(i, "Pourcentage %d" % k).strip())
                               for k, n in zip((1, 2, 3), noms) if n.strip())
        for cote in ("entree", "sortie"):
            COMPAREES[("repartition " + cote, i in A_PART_237)] += 1
            reg_txt = " + ".join("%s %g%% (%s)" % (r["nom_au_moment"], r["pourcentage"] or 0, r["origine"])
                                 for r in sorted(rows, key=lambda r: r["rang"]) if r["cote"] == cote) or "AUCUNE"
            if refus:
                ecart(i, "repartition " + cote, sheet_txt, reg_txt, "chaine %s" % ch,
                      "le 13/11 n'a pas pu lire la ligne (%s) : sa chaine garde ce qu'elle avait" % refus.split(" :")[0])
                continue
            att = {x for x in sig if x[0] == cote}
            if not rows:
                ecart(i, "repartition " + cote, sheet_txt, "AUCUNE", " ".join(map(str, V[i]["pieces"])),
                      "aucune repartition sur la chaine de ses pieces")
            elif att == signature_rows(rows, cote):
                accord(i, "repartition " + cote)
            else:
                # deux lignes sur une chaine le 13/11 : « la ligne dont le dernier mouvement est le plus recent porte la
                #   repartition de la chaine » (regle du 14/11) -- l'autre n'a jamais ete ecrite
                autres = [j for j in SOURCE.get(ch, set()) if j != i
                          and (signature_sheet(j, {str(r["hektor_user_id"]) for r in rows})[0] or set())
                          == signature_rows(rows)]
                origine = ",".join(sorted({r["origine"] for r in rows if r["cote"] == cote})) or "-"
                if autres:
                    cause = ("sa chaine porte la repartition d'une AUTRE ligne : %s (la plus recente, regle du 14/11 -- la "
                             "sienne n'a jamais ete ecrite)" % "+".join(sorted(autres)))
                elif origine == "hektor_partage_suppose":
                    cause = "une SUPPOSITION de Hektor (hektor_partage_suppose), jamais remplacee par le classeur"
                else:
                    cause = "⛔ la PERSONNE ou la PART differe (%s)" % origine
                ecart(i, "repartition " + cote, " + ".join("%s %g%%" % (u, pc) for c_, u, pc in sorted(att)) or "-",
                      reg_txt, "chaine %s" % ch, cause)
    # ── 2 LA COMMISSION ──
    com = K.nombre(D.case(i, "Commission TTC"))
    if com is not None:
        hons = {a: D.REG[a]["hon"] for a in pieces_de(i, "compromis") if a in D.REG and D.REG[a]["hon"] is not None}
        COMPAREES[("commission (honoraires du compromis)", i in A_PART_237)] += 1
        if not hons:
            ecart(i, "commission (honoraires du compromis)", "%g" % com, "-", "-",
                  "pas de compromis avec ses honoraires dans ses pieces" if not pieces_de(i, "compromis")
                  else "son compromis n'a pas de prix net vendeur")
        elif any(abs(h - com) <= 1 for h in hons.values()):
            accord(i, "commission (honoraires du compromis)")
        else:
            ecart(i, "commission (honoraires du compromis)", "%g" % com, " ; ".join("%d : %g" % kv for kv in hons.items()),
                  " ".join(map(str, hons)), "les honoraires du compromis different de la commission")
        cas = {a: K.nombre(PI[a]["commission_agence"]) for a in pieces_de(i, "vente") if K.nombre(PI[a]["commission_agence"]) is not None}
        if pieces_de(i, "vente"):
            COMPAREES[("commission (commission_agence de la vente)", i in A_PART_237)] += 1
            if not cas:
                ecart(i, "commission (commission_agence de la vente)", "%g" % com, "-", " ".join(map(str, pieces_de(i, "vente"))),
                      "sa vente n'a pas de commission_agence")
            elif any(abs(c * 1.2 - com) <= 1.5 or abs(c - com) <= 1 for c in cas.values()):
                accord(i, "commission (commission_agence de la vente)")
            elif any(abs(c * 1.2 * 2 - com) <= 2 for c in cas.values()):
                ecart(i, "commission (commission_agence de la vente)", "%g" % com,
                      " ; ".join("%d : %g HT (%g TTC)" % (a, c, c * 1.2) for a, c in cas.items()), " ".join(map(str, cas)),
                      "la commission_agence vaut la MOITIE de la commission (HT) -- une part, pas le total : a lui")
            else:
                ecart(i, "commission (commission_agence de la vente)", "%g" % com,
                      " ; ".join("%d : %g HT (%g TTC)" % (a, c, c * 1.2) for a, c in cas.items()), " ".join(map(str, cas)),
                      "la commission_agence de la vente differe (ni HT x 1,2, ni TTC)")
    chg = D.case(i, "Charge Commission").strip()
    regc = {a: PI[a]["charge_commission_app"] for a in V[i]["pieces"] if a in PI and PI[a]["charge_commission_app"]}
    if chg or regc:
        COMPAREES[("charge commission", i in A_PART_237)] += 1
        if chg and regc and all(norm(x) == norm(chg) for x in regc.values()):
            accord(i, "charge commission")
        elif chg and not regc:
            ecart(i, "charge commission", chg, "-", "-", "jamais rapatriee : la colonne n'a ete rapatriee que sur 7 pieces")
        else:
            ecart(i, "charge commission", chg or "-", " ; ".join("%d : %s" % kv for kv in regc.items()),
                  " ".join(map(str, regc)), "differe" if chg else "le registre porte une charge, le Sheet est vide")
    # ── 3 LA FACTURE ──
    fac_s = set(re.findall(r"[A-Z]{3}\d{5,}", D.case(i, "Numéro de facture").upper()))
    fac_r = {a: str(PI[a]["numero_facture_app"]).strip().upper() for a in pieces_de(i, "vente")
             if str(PI[a].get("numero_facture_app") or "").strip()}
    if fac_s or fac_r or D.case(i, "Numéro de facture").strip():
        COMPAREES[("facture", i in A_PART_237)] += 1
        reg_codes = {c for v in fac_r.values() for c in re.findall(r"[A-Z]{3}\d{5,}", v)}
        if fac_s and reg_codes and fac_s & reg_codes:
            accord(i, "facture")
        elif fac_s and not fac_r:
            ecart(i, "facture", " ".join(sorted(fac_s)), "-", "-", cause_absente(i, "numero_facture_app", "vente"))
        elif not fac_s and fac_r:
            ecart(i, "facture", D.case(i, "Numéro de facture").strip()[:40] or "-", " ; ".join(fac_r.values()),
                  " ".join(map(str, fac_r)), "le registre porte une facture, le Sheet n'a pas de code GGTI/AVR")
        elif not fac_s and not fac_r:
            ecart(i, "facture", D.case(i, "Numéro de facture").strip()[:60], "-", "-",
                  "la case du Sheet ne porte aucun code GGTI/AVR (texte libre)")
        else:
            ecart(i, "facture", " ".join(sorted(fac_s)), " ; ".join(fac_r.values()), " ".join(map(str, fac_r)),
                  "le numero differe")
    # ── 4 LE REGLEMENT ──
    reg_s = K.d_sheet(D.case(i, "Vente Réglée"))
    regs = {a: K.d_sheet(PI[a]["vente_reglee_app"]) for a in pieces_de(i, "vente") if str(PI[a].get("vente_reglee_app") or "").strip()}
    if D.case(i, "Vente Réglée").strip() or regs:
        COMPAREES[("reglement", i in A_PART_237)] += 1
        if reg_s and reg_s in regs.values():
            accord(i, "reglement")
        elif D.case(i, "Vente Réglée").strip() and not regs:
            ecart(i, "reglement", D.case(i, "Vente Réglée").strip(), "-", "-", cause_absente(i, "vente_reglee_app", "vente"))
        elif not D.case(i, "Vente Réglée").strip():
            ecart(i, "reglement", "-", " ; ".join("%d : %s" % kv for kv in regs.items()), " ".join(map(str, regs)),
                  "le registre porte un reglement, le Sheet est vide")
        else:
            ecart(i, "reglement", D.case(i, "Vente Réglée").strip(), " ; ".join("%d : %s" % kv for kv in regs.items()),
                  " ".join(map(str, regs)), "la date differe")
    # ── 5 L'ANNULATION ──
    ann_s = K.d_sheet(D.case(i, "Annulée"))
    anns = {a: K.d_reg(PI[a]["date_annulation_app"]) for a in pieces_de(i, "compromis") if PI[a].get("date_annulation_app")}
    if D.case(i, "Annulée").strip() or anns:
        COMPAREES[("annulation", i in A_PART_237)] += 1
        if ann_s and ann_s in anns.values():
            accord(i, "annulation")
        elif D.case(i, "Annulée").strip() and not anns:
            ecart(i, "annulation", D.case(i, "Annulée").strip(), "-", "-", cause_absente(i, "date_annulation_app", "compromis"))
        elif not D.case(i, "Annulée").strip():
            ecart(i, "annulation", "-", " ; ".join("%d : %s" % kv for kv in anns.items()), " ".join(map(str, anns)),
                  "le registre porte une annulation, le Sheet est vide")
        else:
            ecart(i, "annulation", D.case(i, "Annulée").strip(), " ; ".join("%d : %s" % kv for kv in anns.items()),
                  " ".join(map(str, anns)), "la date differe")
    # ── 6 LES DATES ──
    for col, genre, cle in (("Offre Achat", "offre", "date offre"), ("Compromis", "compromis", "date compromis"),
                            ("Vente Fixée", "vente", "date vente fixee")):
        s_ = D.case(i, col).strip()
        if not s_:
            continue
        COMPAREES[(cle, i in A_PART_237)] += 1
        d_ = K.d_sheet(s_)
        ps = {a: D.REG[a]["date"] for a in pieces_de(i, genre) if a in D.REG}
        if d_ and d_ in ps.values():
            accord(i, cle)
        elif not ps:
            ecart(i, cle, s_, "-", "-", "pas de %s dans ses pieces" % genre)
        elif not d_:
            ecart(i, cle, s_, " ; ".join("%d : %s" % kv for kv in ps.items()), " ".join(map(str, ps)),
                  "la case du Sheet n'est pas une date lisible")
        else:
            ecart(i, cle, s_, " ; ".join("%d : %s" % kv for kv in ps.items()), " ".join(map(str, ps)),
                  "aucune de ses pieces n'est datee de ce jour" + (" (une offre : sa 1re proposition)" if genre == "offre" else ""))
    # ── 7 LES TEXTES : la note que C4 a posee pour la ligne (17/11) est-elle sur une piece DE la ligne ? ──
    for x in C4.get(i, []):
        cle = {"classeur:F": "texte F (en attente de)", "classeur:G": "texte G (commentaires)"}.get(
            x["origine"], "texte G (commentaires)")
        COMPAREES[(cle, i in A_PART_237)] += 1
        a = int(x["app_affaire_id"])
        presente = any(o_ == x["origine"] for o_, _t in NOTES.get(a, []))
        if a in V[i]["pieces"] and presente:
            accord(i, cle)
        elif not presente:
            ecart(i, cle, x["texte"][:80].replace("\n", " / "), "-", str(a), "la note de C4 n'est PAS en base sur sa piece")
        else:
            ecart(i, cle, x["texte"][:80].replace("\n", " / "), "sur la piece %d" % a, str(a),
                  "⛔ POSEE PAR LE GEL SUR UNE PIECE QUE LE PROTOCOLE DONNE A %s" % qui_tient(i, a))

# ── LES CASES F / G HORS DU RAPPORT DE C4, DECLAREES ─────────────────────────────────────────────────────────────
hors_c4 = Counter()
for i in T:
    if i in C4:
        continue
    if D.case(i, "En attente de").strip():
        hors_c4["F hors du rapport de C4 (« V » seul, un des six motifs, une affaire en cours, ...)"] += 1
    if D.case(i, "COMMENTAIRES").strip():
        hors_c4["G hors du rapport de C4 (ligne sans gel le 17/11, ou ecartee)"] += 1
# ── LES LIGNES EN ATTENTE, DECLAREES ──────────────────────────────────────────────────────────────────────────────
att_rempli = Counter()
for i in ATT:
    for col in ("Négociateur 1", "Commission TTC", "Numéro de facture", "Vente Réglée", "Annulée", "Offre Achat", "Compromis",
                "Vente Fixée", "En attente de", "COMMENTAIRES"):
        if D.case(i, col).strip():
            att_rempli[col] += 1

# ── LE COMPTE, colonne par colonne, avec son TEMOIN INVERSE ────────────────────────────────────────────────────────
dire()
dire("COLONNE PAR COLONNE (lignes tranchees hors des 237 | les 237 a part) : comparees, EN ACCORD (le temoin inverse), "
     "ecarts")
nb_ec = Counter((e["colonne"], e["a_part_237"] == "oui") for e in ECARTS)
for col in sorted(GRAVITE, key=lambda c: (GRAVITE[c], c)):
    c0, c1 = COMPAREES[(col, False)], COMPAREES[(col, True)]
    if not (c0 or c1):
        continue
    dire("   %d %-44s %5d comparees : %5d en accord, %4d ecarts   |   237 : %3d comparees, %3d en accord, %3d ecarts" % (
        GRAVITE[col], col, c0, ACCORD[(col, False)], nb_ec[(col, False)], c1, ACCORD[(col, True)], nb_ec[(col, True)]))
    for k, n in CAUSES[col].most_common():
        dire("        %5d  %s" % (n, k[:110]))
dire("   cases F / G des lignes tranchees HORS du rapport de C4 (declarees, pas comparees) : %s" % (
    " . ".join("%s %d" % kv for kv in hors_c4.most_common())))
dire()
dire("LES LIGNES EN ATTENTE (%d) -- DECLAREES, JAMAIS COMPAREES (pas de pieces sures) ; leurs cases remplies : %s" % (
    len(ATT), " . ".join("%s %d" % kv for kv in att_rempli.most_common())))

# ── SES TROIS ECARTS : 31 reglements, 81 factures, 447 annulations -- chacun sa CAUSE ECRITE ─────────────────────────
dire()
dire("SES TROIS ECARTS, LIGNE PAR LIGNE (cases remplies au Sheet contre valeurs au registre, sur TOUT le classeur)")
for col, champ, genre, cle in (("Vente Réglée", "vente_reglee_app", "vente", "reglement"),
                               ("Numéro de facture", "numero_facture_app", "vente", "facture"),
                               ("Annulée", "date_annulation_app", "compromis", "annulation")):
    n_s = sum(1 for i in D.LIG if D.case(i, col).strip())
    n_r = sum(1 for a in PI if str(PI[a].get(champ) or "").strip())
    porte_par = defaultdict(set)      # piece qui porte la valeur -> ses lignes (protocole)
    sans_ligne = [a for a in PI if str(PI[a].get(champ) or "").strip() and not TIENT.get(a)]
    c = Counter()
    for i in D.LIG:
        if not D.case(i, col).strip():
            continue
        if V[i]["verdict"] != "TRANCHEE":
            c["ligne EN ATTENTE (%s) : declaree, pas comparee" % V[i]["motif"]] += 1
            continue
        a_val = [a for a in pieces_de(i, genre) if str(PI[a].get(champ) or "").strip()]
        if a_val:
            c["porte par sa propre piece"] += 1
        else:
            c[re.sub(r"\d{3,}", "N", cause_absente(i, champ, genre))[:120]] += 1
    dire("   %s : %d cases au Sheet, %d valeurs au registre (ecart brut %d)" % (col, n_s, n_r, n_s - n_r))
    for k, n in c.most_common():
        dire("        %5d  %s" % (n, k))
    dire("        valeurs du registre sur une piece qu'aucune ligne tranchee ne tient : %d" % len(sans_ligne))
    lot = LOT_DE[champ]
    mal = []
    for i_, (v_, a_) in LOT[lot].items():
        if v_ == "nette" and a_ is not None and i_ in V and a_ not in V[i_]["pieces"]:
            mal.append((i_, a_, V[i_]["verdict"], qui_tient(i_, a_) if V[i_]["verdict"] == "TRANCHEE"
                        else ("+".join(sorted(TIENT.get(a_, set()))) or "PERSONNE")))
    dire("        ⛔ valeurs posees le 16/11 (%s) sur une piece que le protocole NE DONNE PAS a leur ligne : %d" % (lot, len(mal)))
    cm = Counter("ligne %s, piece a %s" % ("TRANCHEE" if x[2] == "TRANCHEE" else "EN ATTENTE",
                                            re.sub(r" \(.*\)$", "", x[3]) if x[3].startswith(("PERSONNE --", "UNE AUTRE"))
                                            else ("PERSONNE" if x[3] == "PERSONNE" else "une AUTRE ligne")) for x in mal)
    for k, n in cm.most_common():
        dire("             %4d  %s" % (n, k))
    for x in sorted(mal)[:12]:
        dire("             %s piece %d (%s ; le protocole la donne a %s)" % x)

# ── LE FICHIER ─────────────────────────────────────────────────────────────────────────────────────────────────────
f = P.NOTICE / ("PROTOCOLE_CONTROLE_SHEET_CONTRE_REGISTRE_PASSAGE_%d_2026-11-24.csv" % arg.passage)
ECARTS.sort(key=lambda e: (e["a_part_237"] == "oui", e["gravite"], e["colonne"], e["ligne_du_sheet"] or 0))
with f.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["gravite", "colonne", "id_unique", "ligne_du_sheet", "verdict", "a_part_237", "sheet",
                                       "registre", "piece", "cause"], delimiter=";")
    w.writeheader()
    for e in ECARTS:
        w.writerow(e)
ft = P.NOTICE / ("PROTOCOLE_CONTROLE_SHEET_CONTRE_REGISTRE_PASSAGE_%d_TEMOIN_INVERSE_2026-11-24.csv" % arg.passage)
with ft.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["gravite", "colonne", "comparees_hors_237", "en_accord_hors_237", "ecarts_hors_237", "comparees_237",
                "en_accord_237", "ecarts_237"])
    for col in sorted(GRAVITE, key=lambda c: (GRAVITE[c], c)):
        w.writerow([GRAVITE[col], col, COMPAREES[(col, False)], ACCORD[(col, False)], nb_ec[(col, False)],
                    COMPAREES[(col, True)], ACCORD[(col, True)], nb_ec[(col, True)]])
dire()
dire("-> %s (%d ecarts, ranges par gravite ; les 237 a la fin)" % (f, len(ECARTS)))
dire("-> %s" % ft)
