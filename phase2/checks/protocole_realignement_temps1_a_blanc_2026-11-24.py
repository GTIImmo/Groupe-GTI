"""TEMPS 1 DU REALIGNEMENT (24/11, son mot « REALIGNER les ecritures rapatriees -- en deux temps ») : CE QUI NE BOUGERA
PLUS. LECTURE SEULE : rien en base, rien dans le Sheet, rien chez Hektor -- ce script DIT ce que le geste ferait.

SON BUT : « A la fin, CHAQUE ECRITURE RAPATRIEE DU CLASSEUR DOIT ETRE SUR LA LIGNE DU CLASSEUR D'OU ELLE VIENT -- et on doit
pouvoir le PROUVER par un controle qui tombe a zero, avec son temoin inverse. »

LES QUATRE PAS DU TEMPS 1 (dans son ordre) :
  ① L'AUDIT, colonne par colonne, ECRITURE PAR ECRITURE (jamais un compte global) : Vente Reglee, Numero de facture, Annulee,
     le motif, Commission TTC (honoraires_entree, ⛔ commission_agence SORTIE du controle, declare), Charge Commission (⛔ sur
     LE MANDAT), les COMMENTAIRES et « En attente de » (les notes, PREFIXEES), la colonne F (les conditions), les trois Avis.
     Pour chaque ecriture : la ligne D'OU ELLE VIENT (le rapport du lot qui l'a posee -- pas une devinette), sa valeur
     contre le Sheet de cette ligne, et SA PLACE -- trois cles cote a cote : la ligne que LE GEL designe (sa definition),
     celle que LE PROTOCOLE donne (le chainage corrige), et la ligne dont elle porte LE CONTENU.
     ⛔ TEMOIN INVERSE a chaque colonne : les lignes du classeur qui portent la valeur sans qu'AUCUNE piece ne l'ait chez nous.
  ② POUR CHAQUE ANOMALIE, LA DECISION PROPOSEE : DEPLACER (vers quelle piece), LAISSER, ou REMONTE -- avec sa raison.
  ③ LE GESTE, A BLANC : ce que le realignement deplace (l'ancienne place MISE DE COTE au journal, regle 6), et SON INVERSE,
     rejoue sur l'etat d'arrivee, qui doit reposer l'etat de depart A L'IDENTIQUE (empreinte).
  ④ LE TEMOIN DE FIN : le meme controle, rejoue apres le geste : ZERO ecriture mal placee hors des anomalies NOMMEES qu'il
     laisse ou fait remonter ; et son inverse : ce que le controle trouve SANS le geste.

LES SOURCES (« lis ce qui existe deja ; cite tes sources ») -- les rapports des lots, qui disent la LIGNE de chaque ecriture :
  C8  notice/C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv            vente_reglee_app, numero_facture_app (sur la VENTE)
  C3  notice/C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv  date_annulation_app (sur le COMPROMIS annule)
  C4  notice/C4_LES_MOTIFS_RETENUS_2026-11-17.csv                 motif_annulation_app (TRADUIT : « refuse » -> Pret refuse)
  C4  notice/C4_LES_NOTES_A_POSER_2026-11-17.csv                  app_affaire_note F / G / F+G (PREFIXEES « G : ... -- »)
  C4  notice/C4_LOTS_1_ET_2_2026-11-17.csv                        lot 1 : 80 notes COMPLETEES ; lot 2 : 28 conditions
  C5  phase2/checks/poser_offres_annulees_classeur_2026-11-16.py  les notes « classeur » (la ligne est ECRITE dans le texte)
  C2  notice/C2_LES_COMMISSIONS_A_POSER_2026-11-17.csv            honoraires_entree_app (« Les 62 seules », 17/11)
  C9  notice/C9_LES_AVIS_DU_CLASSEUR_2026-11-16.csv               app_classeur_avis (cle = la LIGNE elle-meme)
  C1  phase2/checks/poser_charge_classeur_2026-11-04.py           le carnet des mandats, origine « classeur » (cle = le MANDAT)
  la colonne « Commission TTC » se lit par honoraires_entree : notice/LES_38_COLONNES_CONSOLIDE_2026-10-28.md l. 120 et
  l'artefact « Classeur, les 38 choix » (colonne P) -- « le classeur note une PART, nous le total » (09/11).

USAGE : python -u -X utf8 phase2/checks/protocole_realignement_temps1_a_blanc_2026-11-24.py --passage P [--csv]
"""
import argparse
import copy
import csv
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import coupe_preuve_interne as K  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402
import rapatrier_repartition_classeur as RR  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--passage", type=int, required=True)
ap.add_argument("--csv", action="store_true")
ap.add_argument("--r26", action="store_true", help="l'etat d'arrivee avec R26 a blanc")
arg = ap.parse_args()


def dire(s=""):
    print(s, flush=True)


# ═══════════════════════════════════════════ LES TROIS CLES ═══════════════════════════════════════════════════════
con = P.socle()
image, version = con.execute("select image, version from passage where id=?", (arg.passage,)).fetchone()
V = {}
for i, num, v, ps in con.execute("select id_unique, num, verdict, pieces from verdict where passage=?", (arg.passage,)):
    V[i] = {"num": num, "verdict": v, "pieces": set(json.loads(ps)) if ps else set()}
con.close()
T = {i for i, v in V.items() if v["verdict"] == "TRANCHEE"}
I = P.Image(P.IMAGES / image)
D = I.D
PI = I.pieces
GEL_L, GEL_P = defaultdict(set), defaultdict(set)
for i, a, *_r in I.gel:
    GEL_L[i].add(int(a))
    GEL_P[int(a)].add(i)
TIENT = defaultdict(set)
for i in T:
    for a in V[i]["pieces"]:
        TIENT[a].add(i)
# --r26 : l'etat d'arrivee AVEC R26 a blanc (protocole_r26_vente_emportee_a_blanc : son brouillon et son rejeu E, dans
#   le dossier a part protocole_a_blanc_r26) -- sinon le rejeu E du passage tel qu'il est
_DOS_E = (P.DOSSIER.parent / "protocole_a_blanc_r26") if arg.r26 else P.DOSSIER
brouillon = _DOS_E / ("brouillon_detachements_protocole_passage_%d.csv" % arg.passage)
_d0, P.DOSSIER = P.DOSSIER, _DOS_E
chE, _ = PO.rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
P.DOSSIER = _d0
BIEN_L = defaultdict(set)       # le bien -> les lignes qui y ont une piece (gel ou protocole)
for i in D.LIG:
    for a in GEL_L.get(i, set()) | V.get(i, {}).get("pieces", set()):
        if a in PI:
            BIEN_L[str(PI[a]["hektor_annonce_id"])].add(i)
RANG = {"vente": 3, "compromis": 2, "offre": 1}
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
loc.row_factory = sqlite3.Row
dire("TEMPS 1 DU REALIGNEMENT -- passage %d (%s), image %s ; registre : phase2.sqlite (descente du jour)" % (
    arg.passage, version, image))

# ⛔ SA REGLE (06/11) : l'identite d'un ADMIN n'est jamais ecrite sur un document -- reperee par son NUMERO dans l'annuaire,
#   remplacee dans tout texte qui sortirait
COMPTES_ADMIN = {"46"}
_MOTS_ADMIN = set()
for nom_, in loc.execute("select nom from app_hektor_negotiator_agency_directory where cast(hektor_user_id as text) in "
                         "(%s)" % ",".join("'%s'" % x for x in COMPTES_ADMIN)):
    _MOTS_ADMIN |= set(RR.mots_du_nom(nom_ or ""))


def masque(s):
    s = (s or "").replace("\n", " / ")
    for m in _MOTS_ADMIN:
        if len(m) >= 3:
            s = re.sub(r"(?i)\b%s\b" % re.escape(m), "[compte admin]", s)
    return s


def norm(s):
    return re.sub(r"[^0-9a-zà-ÿ]", "", (s or "").lower())


def sa(s):
    return "".join(c for c in unicodedata.normalize("NFD", norm(s)) if unicodedata.category(c) != "Mn")


def case(i, col):
    return D.case(i, col).strip() if i in D.LIG else ""


def codes(s):
    return set(re.findall(r"[A-Z]{3}\d{5,}", (s or "").upper()))


# ═══════════════════════════════════════════ L'ETAT DU REGISTRE (S0) ══════════════════════════════════════════════
COLS = ("vente_reglee_app", "numero_facture_app", "date_annulation_app", "motif_annulation_app", "honoraires_entree_app")
S0 = {c: {} for c in COLS}
S0["note"], S0["condition"], S0["avis"], S0["charge"] = {}, {}, {}, {}
for r in loc.execute("select app_affaire_id, %s from app_affaire_ledger" % ", ".join(COLS)):
    for c in COLS:
        if str(r[c] or "").strip():
            S0[c][int(r["app_affaire_id"])] = str(r[c]).strip()
for r in loc.execute("select app_affaire_id, origine, texte from app_affaire_note"):
    S0["note"][int(r["app_affaire_id"])] = (r["origine"], r["texte"] or "")
for r in loc.execute("select app_affaire_id, rang, libelle, note, origine from app_affaire_condition"):
    S0["condition"][(int(r["app_affaire_id"]), int(r["rang"]))] = (r["origine"], r["libelle"] or "", r["note"] or "")
for r in loc.execute("select id_unique, avis_a_envoyer, commentaire_avis, avis_envoye, origine from app_classeur_avis"):
    S0["avis"][r["id_unique"]] = (r["origine"], r["avis_a_envoyer"] or "", r["commentaire_avis"] or "", r["avis_envoye"] or "")
for r in loc.execute("select hektor_annonce_id, numero_mandat, valeur_app, origine from app_mandat_champ_app__sb "
                     "where champ = 'charge_commission'"):
    S0["charge"][(str(r["hektor_annonce_id"]), str(r["numero_mandat"]))] = (r["valeur_app"] or "", r["origine"])
HON = {a: K.nombre(PI[a]["honoraires_entree"]) for a in PI}      # la valeur de HEKTOR (classe C), pour le temoin
S0["_src"] = {}     # (famille, cle) -> (la ligne d'ou elle vient, la valeur du rapport, le lot) : rempli plus bas, et
#                     ⭐ il SUIT l'ecriture quand le geste la deplace (sinon le temoin de fin perdrait sa ligne)

# ═══════════════════════════════════════════ LES RAPPORTS DES LOTS ════════════════════════════════════════════════


def lire(f):
    return list(csv.DictReader(open(P.NOTICE / f, encoding="utf-8-sig"), delimiter=";"))


SRC = defaultdict(list)        # (famille, cle) -> [(id_unique, valeur du rapport, lot)]
for x in lire("C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv"):
    if x["verdict"] == "nette" and x["app_affaire_id"].isdigit():
        a = int(x["app_affaire_id"])
        if x["vente_reglee"].strip():
            SRC[("vente_reglee_app", a)].append((x["id_unique"], x["vente_reglee"].strip(), "C8"))
        if x["numero_facture"].strip():
            SRC[("numero_facture_app", a)].append((x["id_unique"], x["numero_facture"].strip(), "C8"))
LOT_C8 = {x["id_unique"]: x["verdict"] for x in lire("C8_VENTE_REGLEE_ET_FACTURE_2026-11-16.csv")}
for x in lire("C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv"):
    if x["verdict"] == "nette" and x["app_affaire_id"].isdigit():
        SRC[("date_annulation_app", int(x["app_affaire_id"]))].append((x["id_unique"], x["date_annulation_classeur"], "C3"))
LOT_C3 = {x["id_unique"]: x["verdict"] for x in lire("C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv")}
MOTIF_ORIG = {}
for x in lire("C4_LES_MOTIFS_RETENUS_2026-11-17.csv"):
    SRC[("motif_annulation_app", int(x["app_affaire_id"]))].append((x["id_unique"], x["motif"], "C4 motifs"))
    MOTIF_ORIG[(int(x["app_affaire_id"]), x["id_unique"])] = x["texte_origine"]
LOT_MOTIF = {x["id_unique"] for x in lire("C4_LES_MOTIFS_RETENUS_2026-11-17.csv")}
for x in lire("C2_LES_COMMISSIONS_A_POSER_2026-11-17.csv"):
    if x["lot"] in ("1_aboutie", "2_en_cours") and x["app_affaire_id"].isdigit():
        SRC[("honoraires_entree_app", int(x["app_affaire_id"]))].append((x["id_unique"], x["montant"], "C2 " + x["lot"]))
LOT_C2 = {x["id_unique"]: x["lot"] for x in lire("C2_LES_COMMISSIONS_A_POSER_2026-11-17.csv")}
NOTE_C4 = {}
for x in lire("C4_LES_NOTES_A_POSER_2026-11-17.csv"):
    SRC[("note", int(x["app_affaire_id"]))].append((x["id_unique"], x["texte"], "C4 " + x["origine"]))
    NOTE_C4[x["id_unique"]] = int(x["app_affaire_id"])
LOT1 = {}
for x in lire("C4_LOTS_1_ET_2_2026-11-17.csv"):
    if x["lot"] == "1 note":
        LOT1[int(x["app_affaire_id"])] = (x["id_unique"], x["valeur"])
    else:
        SRC[("condition", int(x["app_affaire_id"]))].append((x["id_unique"], x["valeur"], "C4 lot 2"))
AVIS_C9 = {x["id_unique"]: x for x in lire("C9_LES_AVIS_DU_CLASSEUR_2026-11-16.csv")}
F_NON_POSE = {x["id_unique"] for x in lire("C4_TEXTE_DE_F_NON_POSE_2026-11-17.csv")}
# les montants SAISIS dans l'app a la creation d'une offre (carnet app_affaire_champ_app, origine creation_app) : une
#   saisie humaine, hors du realignement
SAISIE_HON = {int(a_) for a_, in loc.execute("select app_affaire_id from app_affaire_champ_app where champ = 'honoraires'")}
dire("   les rapports des lots : %s" % " . ".join("%s %d" % kv for kv in sorted(Counter(
    s[2].split(" ")[0] + ("" if not s[2].startswith("C4") else " " + s[2].split(" ")[1]) for v in SRC.values()
    for s in v).items())))


# ═══════════════════════════════════════════ LE CONTENU : la valeur colle-t-elle a une ligne ? ════════════════════
def segments(texte):
    """Une note C4 : « F : <libelle> -- <texte> » / « G : le commentaire -- <texte> » ; plus la suite du lot 1
    (« [classeur F, suivi en cours au 17/11/2026] <F> »). Une note C5 : l'acquereur et la ligne ecrite dedans."""
    t = texte or ""
    out = []
    m1 = re.search(r"\n?\[classeur F, suivi en cours au [^\]]*\] (.*)\Z", t, re.S)
    if m1:
        out.append(("En attente de", m1.group(1)))
        t = t[:m1.start()]
    for m in re.finditer(r"(?:^|\n)([FG]) : [^\n]*? -- (.*?)(?=\n[FG] : |\Z)", t, re.S):
        out.append(({"F": "En attente de", "G": "COMMENTAIRES"}[m.group(1)], m.group(2)))
    m5 = re.match(r"Acquereur au classeur : (.*?)\. Reprise de l historique \(ligne (\w+), mandat", t)
    if m5:
        out.append(("Acquéreur", m5.group(1)))
    return out


def ligne_ecrite(texte):
    m5 = re.search(r"\(ligne (\w+), mandat", texte or "")
    return m5.group(1) if m5 else None


def niveau_note(val, i):
    """« egal » : chaque morceau est la case du Sheet ; « grandi » : chaque morceau est DANS la case (le Sheet s'est
    allonge depuis le lot -- ses journaux dates, recents en haut) ; None : un morceau n'y est pas."""
    seg = segments(val[1])
    if not seg or i not in D.LIG:
        return None
    niv = "egal"
    for col, txt in seg:
        n_, s_ = norm(txt), norm(case(i, col))
        if not (n_ and s_):
            return None
        if n_ == s_:
            continue
        if n_ in s_ or (col == "Acquéreur" and s_ in n_):
            niv = "grandi" if col != "Acquéreur" else niv
            continue
        return None
    return niv


def colle(fam, val, i):
    """La valeur du registre est-elle celle du Sheet de la ligne i (l'image) ?"""
    if i not in D.LIG:
        return False
    if fam == "vente_reglee_app":
        s = case(i, "Vente Réglée")
        return bool(s) and (norm(s) == norm(val) or (K.d_sheet(s) is not None and K.d_sheet(s) == K.d_sheet(val)))
    if fam == "numero_facture_app":
        s = case(i, "Numéro de facture")
        return bool(s) and (norm(s) == norm(val) or bool(codes(s) & codes(val)))
    if fam == "date_annulation_app":
        s = case(i, "Annulée")
        return bool(s) and K.d_sheet(s) is not None and K.d_sheet(s) == K.d_reg(val)
    if fam == "honoraires_entree_app":
        c_ = K.nombre(case(i, "Commission TTC"))
        return c_ is not None and abs(c_ - float(val)) <= 1
    if fam == "note":
        return niveau_note(val, i) is not None
    if fam == "condition":
        n_, s_ = norm(val[2]), norm(case(i, "En attente de"))
        return bool(n_ and s_ and (n_ == s_ or n_ in s_))
    if fam == "avis":
        return (sa(val[1]) == sa(case(i, "Avis à envoyer (oui / non)")) and sa(val[2]) == sa(case(i, "Commentaire Avis"))
                and sa(val[3]) == sa(case(i, "Avis envoyé")))
    if fam == "charge":
        return bool(case(i, "Charge Commission")) and sa(val[0]) == sa(case(i, "Charge Commission"))
    return False


def colle_motif(a, val, i):
    """Le motif est TRADUIT (« refuse » -> Pret refuse) : sa source est le texte d'origine de C4, lu dans la colonne F."""
    orig = MOTIF_ORIG.get((a, i))
    s_ = norm(case(i, "En attente de"))
    return bool(orig is not None and s_ and norm(orig) and norm(orig) in s_)


def colle_fam(fam, a, val, i):
    return colle_motif(a, val, i) if fam == "motif_annulation_app" else colle(fam, val, i)


# l'index du contenu, pour nommer LA LIGNE dont une valeur porte le contenu (notes : partout ; le reste : sur le meme bien)
IDX = defaultdict(set)
for i in D.LIG:
    for col in ("COMMENTAIRES", "En attente de"):
        n_ = norm(case(i, col))
        if n_:
            IDX[(col, n_)].add(i)


def proprietaires(fam, a, val):
    """Les lignes dont le Sheet porte CETTE valeur (la note : son texte exact ; une date, une facture : sur le meme bien)."""
    if fam == "note":
        seg = [(c_, norm(t_)) for c_, t_ in segments(val[1]) if c_ != "Acquéreur"]
        cand = None
        for c_, n_ in seg:
            s_ = IDX.get((c_, n_), set())
            cand = s_ if cand is None else cand & s_
        if seg and cand:
            return cand
        scope = GEL_P.get(a, set()) | TIENT.get(a, set()) | (BIEN_L.get(str(PI[a]["hektor_annonce_id"]), set()) if a in PI else set())
        return {i for i in scope if colle(fam, val, i)}
    scope = GEL_P.get(a, set()) | TIENT.get(a, set()) | (BIEN_L.get(str(PI[a]["hektor_annonce_id"]), set()) if a in PI else set())
    return {i for i in scope if colle_fam(fam, a, val, i)}


# ═══════════════════════════════════════════ LA CIBLE : la piece de la ligne, par la regle du lot ═══════════════════
def cible(fam, L, a, etat):
    """La piece que le PROTOCOLE donne a la ligne L, choisie par la regle du lot qui avait pose la valeur."""
    ps = [b for b in V[L]["pieces"] if b in PI and I.nature.get(b) == PC.VRAIE]
    if fam in ("vente_reglee_app", "numero_facture_app"):
        c_ = [b for b in ps if PI[b]["kind"] == "vente"]
    elif fam == "date_annulation_app":
        c_ = [b for b in ps if PI[b]["kind"] == "compromis" and PI[b]["state"] == "cancelled"]
    elif fam == "motif_annulation_app":
        c_ = ([b for b in ps if PI[b]["kind"] == "compromis" and PI[b]["state"] == "cancelled"]
              or [b for b in ps if PI[b]["kind"] == "offre" and PI[b]["state"] == "refused"])
    elif fam == "condition":
        c_ = [b for b in ps if PI[b]["kind"] == (PI[a]["kind"] if a in PI else "compromis")]
    elif fam == "note":
        libres = [b for b in ps if b not in etat["note"] or ("note", b) in VACANTES]
        if not libres:
            return None, "toutes les pieces de sa ligne portent deja une note"
        top = max(RANG.get(PI[b]["kind"], 0) for b in libres)
        c_ = [b for b in libres if RANG.get(PI[b]["kind"], 0) == top]
    else:   # honoraires : la plus avancee (C2)
        if not ps:
            return None, "sa ligne n'a pas de piece vraie"
        top = max(RANG.get(PI[b]["kind"], 0) for b in ps)
        c_ = [b for b in ps if RANG.get(PI[b]["kind"], 0) == top]
    if len(c_) == 1:
        return c_[0], ""
    return None, ("sa ligne n'a pas de piece de ce genre" if not c_ else "plusieurs cibles possibles : %s"
                  % " ".join(map(str, sorted(c_))))


# ═══════════════════════════════════════════ LE JUGE D'UNE ECRITURE ══════════════════════════════════════════════
def source(fam, a, val):
    """(ligne d'ou elle vient, valeur du rapport, lot) -- par le rapport du lot ; sinon par le texte (C5) ; sinon None."""
    if fam == "note" and val[0] == "classeur":
        return ligne_ecrite(val[1]), val[1], "C5 lot B"
    if fam == "note" and val[0] == "saisie":
        return None, None, "saisie humaine"
    if fam == "condition" and val[0] == "saisie":
        return None, None, "saisie humaine"
    if fam == "honoraires_entree_app" and not SRC.get((fam, a)) and (a in SAISIE_HON or (
            a >= 1000000 and a in PI and not PI[a].get("transaction_origine"))):
        return None, None, "saisie humaine"
    srcs = SRC.get((fam, a), [])
    if not srcs:
        return None, None, "aucun rapport de lot"
    for i, v_, lot in srcs:
        if fam == "note" and val[1].startswith(v_):
            return i, v_, lot
        if fam != "note" and fam != "condition" and norm(v_) == norm(val):
            return i, v_, lot
        if fam == "honoraires_entree_app" and K.nombre(v_) is not None and abs(K.nombre(v_) - float(val)) <= 1:
            return i, v_, lot
        if fam == "date_annulation_app" and K.d_reg(v_) == K.d_reg(val):
            return i, v_, lot
        if fam == "condition" and norm(v_.split(" echeance")[0]) == norm(val[1]):
            return i, v_, lot
    i, v_, lot = srcs[0]
    return i, v_, lot + " (⚠ la valeur en base n'est pas celle du rapport)"


def juger(fam, cle, val, etat):
    """-> dict : la ligne source, le contenu, les trois cles, la classe, la decision et sa raison."""
    a = cle if isinstance(cle, int) else (cle[0] if fam == "condition" else None)
    L, v_rap, lot = etat["_src"].get((fam, cle)) or source(fam, a, val)
    if fam == "condition" and a is not None:
        pass
    e = {"famille": fam, "cle": cle, "piece": a, "valeur": val, "source": L, "lot": lot, "contenu": "-",
         "gel": "+".join(sorted(GEL_P.get(a, set()))) or "-", "protocole": "+".join(sorted(TIENT.get(a, set()))) or "PERSONNE",
         "contenu_d_une_autre_ligne": "-", "sa_deplacee": False}
    if L is None:
        e["sa_deplacee"] = bool(fam != "note" or val[0] != "saisie") and not any(
            colle_fam(fam, a, val, j) for j in GEL_P.get(a, set())) and bool(proprietaires(fam, a, val) - GEL_P.get(a, set()))
        e["classe"], e["decision"] = "SOURCE INCONNUE", "LAISSER" if lot == "saisie humaine" else "REMONTE"
        e["raison"] = ("une saisie humaine : hors du realignement" if lot == "saisie humaine"
                       else "aucun lot ne dit d'ou elle vient")
        return e
    ok_sheet = colle_fam(fam, a, val, L)
    if v_rap is None:
        ok_rap = False
    elif fam == "note":
        ok_rap = val[1].startswith(v_rap)
    elif fam == "honoraires_entree_app":
        ok_rap = K.nombre(v_rap) is not None and abs(K.nombre(v_rap) - float(val)) <= 1
    elif fam == "condition":
        ok_rap = norm(v_rap.split(" echeance")[0]) == norm(val[1])
    else:
        ok_rap = norm(v_rap) == norm(val)
    e["contenu"] = ("= le Sheet de sa ligne" if ok_sheet else
                    ("= le rapport du lot, ⚠ PAS le Sheet d'aujourd'hui (la case a change depuis le lot)" if ok_rap
                     else "⛔ ni le Sheet ni le rapport"))
    gel_l = GEL_P.get(a, set())
    e["gel"] = "+".join(sorted(gel_l)) or "-"
    e["protocole"] = "+".join(sorted(TIENT.get(a, set()))) or "PERSONNE"
    # SA DEFINITION (le gel) : la valeur colle-t-elle a une ligne que le gel designe ? sinon, a QUELLE autre ligne ?
    ok_gel = any(colle_fam(fam, a, val, j) for j in gel_l)
    proprio = set() if ok_gel else proprietaires(fam, a, val) - gel_l
    e["contenu_d_une_autre_ligne"] = "+".join(sorted(proprio)) or "-"
    e["sa_deplacee"] = bool(gel_l and not ok_gel and proprio)
    niv = niveau_note(val, L) if fam == "note" else None
    tenants = TIENT.get(a, set()) - {L}
    if a in PI and PI[a].get("transaction_origine") == "classeur" and fam == "note" and ligne_ecrite(val[1]) == L:
        e["classe"], e["decision"], e["raison"] = (
            "SUR LA PIECE CREEE POUR SA LIGNE (lot C5)", "LAISSER",
            "la transaction a ete CREEE le 16/11 pour cette ligne (transaction_origine classeur) et la note le dit ; "
            "⚠ ni le gel ni le protocole ne la connaissent")
        return e
    if L not in T:
        if tenants:
            e["classe"] = "SUR LA PIECE D'UNE AUTRE LIGNE (%s), SA LIGNE EN ATTENTE" % "+".join(sorted(tenants))
            e["decision"], e["raison"] = "REMONTE", ("sa ligne %s est EN ATTENTE au protocole (%s) : aucune piece pour la "
                                                    "recevoir -- proposition : la METTRE DE COTE" % (
                                                        L, "sans aucun lien au gel" if not GEL_L.get(L) else "non jugee"))
        else:
            e["classe"], e["decision"], e["raison"] = "LIGNE NON TRANCHEE", "LAISSER", (
                "sa ligne est EN ATTENTE au protocole, et aucune ligne tranchee ne tient sa piece")
        return e
    if a in V[L]["pieces"]:
        if ok_sheet and niv == "grandi":
            e["classe"], e["decision"], e["raison"] = ("JUSTE, LE SHEET S'EST ALLONGE", "LAISSER",
                                                       "son texte est TOUJOURS dans la case, qui a grandi depuis le lot")
        elif ok_sheet:
            e["classe"], e["decision"], e["raison"] = "JUSTE", "-", ""
        elif ok_rap:
            e["classe"], e["decision"], e["raison"] = ("JUSTE, LE SHEET A CHANGE", "REMONTE",
                                                       "bien placee ; la case a change depuis le lot : a confirmer, pas a corriger")
        else:
            e["classe"], e["decision"], e["raison"] = "CONTENU ETRANGER", "REMONTE", "sur sa piece, mais sa valeur ne colle a rien"
        return e
    dossier = {chE.get(q) for q in V[L]["pieces"]}
    if tenants and any(colle_fam(fam, a, val, M) for M in tenants):
        e["classe"], e["decision"], e["raison"] = ("JUSTE POUR LA LIGNE QUI TIENT LA PIECE", "LAISSER",
                                                   "la valeur est AUSSI celle de %s, qui tient la piece au protocole" %
                                                   "+".join(sorted(M for M in tenants if colle_fam(fam, a, val, M))))
        return e
    if not tenants and chE.get(a) in dossier and GEL_P.get(a, set()) <= {L}:
        e["classe"], e["decision"], e["raison"] = (
            "SUR UNE PIECE NEUTRE DE SA LIGNE", "LAISSER",
            "la piece est a SA ligne au gel, seule, dans SON dossier a l'arrivee ; le protocole ne l'a pas prouvee "
            "(sa date n'est pas celle du Sheet) mais ne la donne a personne")
        return e
    # ⛔ MAL PLACEE : la piece est a une autre ligne, ou elle sortira du dossier de sa ligne a la vague
    aujourd_hui = a in PI and PI[a]["app_chaine_id"] in {PI[q]["app_chaine_id"] for q in V[L]["pieces"] if q in PI}
    e["classe"] = ("SUR LA PIECE D'UNE AUTRE LIGNE (%s)" % "+".join(sorted(tenants)) if tenants else
                   "SUR UNE PIECE QU'AUCUNE LIGNE NE TIENT (%s)" % (
                       "dans son dossier a l'arrivee, partagee au gel avec %s" % "+".join(sorted(GEL_P.get(a, set()) - {L}))
                       if chE.get(a) in dossier else
                       "⛔ HORS de son dossier a l'arrivee ; DANS aujourd'hui : c'est LA VAGUE qui l'en sortirait"
                       if aujourd_hui else "⛔ HORS de son dossier, aujourd'hui deja et a l'arrivee"))
    if (not tenants and aujourd_hui and chE.get(a) not in dossier and a in PI and PI[a]["kind"] == "vente"
            and fam in ("vente_reglee_app", "numero_facture_app")):
        e["cible"] = None
        e["decision"], e["raison"] = "REMONTE", (
            "⛔ LA VAGUE DETACHERAIT CETTE VENTE REGLEE DE SA LIGNE (la seule vente de son dossier ; le protocole ne la "
            "prouve pas par sa date) : la question est au PROTOCOLE, pas a l'ecriture -- et a la garde du temps 2")
        return e
    b, pq = cible(fam, L, a, etat)
    e["cible"] = b
    if b is not None and (fam, b) in INTERDITES:
        b, pq = None, "sa cible %d est visee par DEUX ecritures du meme geste" % b
        e["cible"] = None
    if b is None and tenants and fam == "date_annulation_app":
        # ⭐ SA REGLE (24/11, 3e mot, ②) : « Pour chacune, dis-moi d'abord si LA BONNE PIECE EXISTE chez nous. si oui -> tu
        #   la DEPLACES vers elle [...] ; si non -> tu la METS DE COTE avec son ancienne place (regle 6), tu ne la supprimes
        #   pas. ⛔ Je ne veux pas qu'une date d'annulation reste affichee sur le compromis d'une autre affaire : a l'ecran,
        #   ca ment. »
        e["decision"], e["raison"] = "METTRE DE COTE", (
            "sa regle du 24/11 : la bonne piece n'existe pas (%s) -- mise de cote avec son ancienne place ; elle ne reste "
            "pas sur le compromis de %s" % (pq, "+".join(sorted(tenants))))
        return e
    if b is None:
        e["decision"], e["raison"] = "REMONTE", pq + " -- proposition : la METTRE DE COTE" if tenants else pq
        return e
    tab = etat[fam] if fam != "condition" else {k[0]: v for k, v in etat["condition"].items()}
    occ = (fam, b) in VACANTES
    if b not in tab or occ:
        e["decision"], e["raison"] = "DEPLACER", "vers %d (%s de sa ligne), %s" % (
            b, PI[b]["kind"], "libre" if b not in tab else "liberee par le meme geste (echange)")
    elif (fam == "note" and tab[b][1] == val[1]) or (fam != "note" and tab[b] == val):
        e["decision"], e["raison"] = "DOUBLON", "%d porte deja la meme valeur : celle-ci se met de cote" % b
    else:
        e["decision"], e["raison"] = "REMONTE", "%d (%s de sa ligne) porte deja AUTRE CHOSE" % (b, PI[b]["kind"])
    return e


def juger_charge(cle, val, etat):
    """La charge vit sur LE MANDAT (cle fixe) : de quelles lignes vient-elle, et la disent-elles ?"""
    e = {"famille": "charge", "cle": cle, "piece": None, "valeur": val, "lot": "C1 (04/11)", "gel": "-",
         "contenu_d_une_autre_ligne": "-", "sa_deplacee": False}
    lp = {i for i in T if any(a in PI and (str(PI[a]["hektor_annonce_id"]), str(PI[a]["numero_mandat"])) == cle
                              for a in V[i]["pieces"])}
    lg = {i for i in D.LIG if any(a in PI and (str(PI[a]["hektor_annonce_id"]), str(PI[a]["numero_mandat"])) == cle
                                  for a in GEL_L.get(i, set()))}
    e["protocole"], e["gel"] = "+".join(sorted(lp)) or "PERSONNE", "+".join(sorted(lg)) or "-"
    ok_p = [i for i in lp if colle("charge", val, i)]
    ok_g = [i for i in lg if colle("charge", val, i)]
    if not ok_p and ok_g and all(i not in T for i in ok_g):
        e["source"], e["contenu"] = ok_g[0], "= le Sheet de sa ligne"
        e["classe"], e["decision"], e["raison"] = ("LIGNE NON TRANCHEE", "LAISSER",
                                                   "sa ligne %s est EN ATTENTE au protocole : la charge vit sur le mandat "
                                                   "(cle fixe), elle attend que la ligne soit jugee" % "+".join(ok_g))
        return e
    e["source"] = (ok_p or ok_g or sorted(lp | lg) or [None])[0]
    e["contenu"] = "= le Sheet d'une de ses lignes" if ok_p or ok_g else "⛔ aucune de ses lignes ne dit cette charge"
    if ok_p:
        e["classe"], e["decision"], e["raison"] = "JUSTE", "-", ""
    elif ok_g:
        e["classe"], e["decision"], e["raison"] = ("MANDAT QUE LE PROTOCOLE NE DONNE PLUS A SA LIGNE", "REMONTE",
                                                   "la ligne du gel %s ne cite plus ce mandat au protocole" % "+".join(ok_g))
    elif lp | lg:
        e["classe"], e["decision"], e["raison"] = ("CONTENU ETRANGER", "REMONTE",
                                                   "les lignes de ce mandat ne disent pas cette charge (Sheet change ?)")
    else:
        e["classe"], e["decision"], e["raison"] = ("SANS LIGNE", "LAISSER",
                                                   "aucune ligne (gel ni protocole) ne cite ce mandat : origine 04/11 "
                                                   "par un lien gele depuis retire")
    return e


def juger_avis(cle, val, etat):
    e = {"famille": "avis", "cle": cle, "piece": None, "valeur": val, "source": cle, "lot": "C9 (16/11)", "gel": "-",
         "protocole": "-", "contenu_d_une_autre_ligne": "-", "sa_deplacee": False}
    if cle not in D.LIG:
        e["contenu"], e["classe"], e["decision"], e["raison"] = "-", "LIGNE ABSENTE DU SHEET", "REMONTE", "la ligne n'existe plus"
        return e
    ok = colle("avis", val, cle)
    r9 = AVIS_C9.get(cle)
    ok_rap = r9 is not None and (sa(r9["avis_a_envoyer"]), sa(r9["commentaire_avis"]), sa(r9["avis_envoye"])) == (
        sa(val[1]), sa(val[2]), sa(val[3]))
    e["contenu"] = "= le Sheet de sa ligne" if ok else ("= le rapport C9, ⚠ PAS le Sheet d'aujourd'hui" if ok_rap
                                                         else "⛔ ni le Sheet ni le rapport")
    if ok:
        e["classe"], e["decision"], e["raison"] = "JUSTE", "-", ""
    else:
        e["classe"], e["decision"], e["raison"] = ("JUSTE, LE SHEET A CHANGE" if ok_rap else "CONTENU ETRANGER", "REMONTE",
                                                   "cle = la ligne elle-meme (ne peut pas etre deplacee) ; le Sheet a "
                                                   "change depuis le 16/11 : a confirmer, pas a corriger")
    return e


def controle(etat):
    out = []
    for fam in COLS + ("note",):
        for a, val in sorted(etat[fam].items()):
            out.append(juger(fam, a, val, etat))
    for cle, val in sorted(etat["condition"].items()):
        out.append(juger("condition", cle, val, etat))
    for cle, val in sorted(etat["charge"].items()):
        if val[1] == "classeur":
            out.append(juger_charge(cle, val, etat))
    for cle, val in sorted(etat["avis"].items()):
        out.append(juger_avis(cle, val, etat))
    return out


def empreinte(etat):
    return hashlib.md5(json.dumps({k: sorted((str(k2), v2) for k2, v2 in v.items()) for k, v in etat.items()},
                                  sort_keys=True, ensure_ascii=False).encode()).hexdigest()


MAL = ("SUR LA PIECE D'UNE AUTRE", "SUR UNE PIECE QU'AUCUNE")


def mal_placee(e):
    return e["classe"].startswith(MAL)


# ═══════════════════════════════════════════ ① L'AUDIT ════════════════════════════════════════════════════════════
dire()
dire("① L'AUDIT, ECRITURE PAR ECRITURE")
for _f in COLS + ("note", "condition"):
    for _k, _v in S0[_f].items():
        S0["_src"][(_f, _k)] = source(_f, _k if _f != "condition" else _k[0], _v)
VACANTES, INTERDITES = set(), set()
E0 = controle(S0)
for _tour in range(8):       # le point fixe : une cible occupee par une ecriture QUI PART est libre (l'echange) ; une
    #                          cible visee par deux ecritures est INTERDITE aux deux (aucune ne part)
    _d = Counter((e["famille"], e["cible"]) for e in E0 if mal_placee(e) and e["decision"] == "DEPLACER")
    _i = INTERDITES | {k for k, n in _d.items() if n > 1}
    _v = {(e["famille"], e["piece"]) for e in E0 if mal_placee(e) and e["decision"] in ("DEPLACER", "DOUBLON", "METTRE DE COTE")
          and (e["famille"], e.get("cible")) not in _i}
    if _tour == 0:
        _v |= {(e["famille"], e["piece"]) for e in E0 if mal_placee(e) and e["decision"] == "REMONTE"
               and "portent deja une note" in e["raison"]}
    if _v == VACANTES and _i == INTERDITES:
        break
    VACANTES, INTERDITES = _v, _i
    E0 = controle(S0)
dire("   (point fixe des echanges atteint en %d tours ; %d places liberees par le geste lui-meme)" % (_tour + 1, len(VACANTES)))
NOMS = {"vente_reglee_app": "Vente Reglee", "numero_facture_app": "Numero de facture", "date_annulation_app": "Annulee",
        "motif_annulation_app": "le motif (F)", "honoraires_entree_app": "Commission TTC (honoraires_entree_app)",
        "note": "les notes (F / G)", "condition": "les conditions (F)", "avis": "les trois Avis", "charge": "Charge (mandat)"}
for fam in COLS + ("note", "condition", "charge", "avis"):
    ee = [e for e in E0 if e["famille"] == fam]
    dire("   %-42s %5d ecritures : %s" % (NOMS[fam], len(ee), " . ".join("%s %d" % kv for kv in Counter(
        e["classe"] for e in ee).most_common())))
    dec = Counter(e["decision"] for e in ee if e["classe"] != "JUSTE")
    if dec:
        dire("   %-42s       decisions proposees : %s" % ("", " . ".join("%s %d" % kv for kv in dec.most_common())))
        for k_, n_ in Counter("%s : %s" % (e["decision"], re.sub(r"\d{4,}", "N", e["raison"])[:90]) for e in ee
                              if e["classe"] != "JUSTE").most_common():
            dire("   %-42s          %4d  %s" % ("", n_, k_))

# ⭐ SA MESURE (le gel, par le contenu) contre la mienne : ses 8, nommes
dire()
dire("   SA DEFINITION (la valeur ne colle a AUCUNE ligne que le gel designe, et colle a une AUTRE) -- ses 8 :")
for e in E0:
    if e["sa_deplacee"]:
        dire("      %-20s piece %-7s gel %-18s contenu de %-18s source (lot) %-10s protocole %-18s -> %s / %s" % (
            e["famille"], e["piece"], e["gel"], e["contenu_d_une_autre_ligne"], e["source"], e["protocole"],
            e["classe"][:40], e["decision"]))
dire("   les siennes : notes 6555 14111 16377 21551 23050 27196 ; dates d'annulation 16377 27195")

# ═══════════════════════════════════════════ LE TEMOIN INVERSE, LIGNE PAR LIGNE ═══════════════════════════════════
TROUS = []


CREEES = defaultdict(set)      # les transactions CREEES par le lot C5 pour une ligne (la ligne est ecrite dans la note)
for a_, (o_, t_) in S0["note"].items():
    if o_ == "classeur" and ligne_ecrite(t_):
        CREEES[ligne_ecrite(t_)].add(a_)


def propres(i):
    """Les pieces de la ligne : celles du protocole ; ses pieces NEUTRES (a elle seule au gel, dans son dossier a
    l'arrivee, que le protocole ne donne a personne) ; et celles que le lot C5 a creees pour elle."""
    ps = set(V[i]["pieces"])
    dossier = {chE.get(q) for q in ps}
    for a in GEL_L.get(i, set()) - ps:
        if not TIENT.get(a) and GEL_P.get(a, set()) <= {i} and chE.get(a) in dossier:
            ps.add(a)
    return ps | CREEES.get(i, set())


def voisines(i):
    """Les pieces HORS de la ligne ou sa valeur pourrait etre partie : son gel, et les pieces des lignes de ses biens."""
    ps = V[i]["pieces"] | GEL_L.get(i, set())
    out = set(GEL_L.get(i, set()))
    for b in {str(PI[a]["hektor_annonce_id"]) for a in ps if a in PI}:
        for j in BIEN_L.get(b, set()):
            out |= V.get(j, {}).get("pieces", set()) | GEL_L.get(j, set())
    return out - propres(i)


def temoin_inverse(etat):
    """Les lignes TRANCHEES dont le Sheet porte la valeur : portee par une de LEURS pieces ? ailleurs ? nulle part ?"""
    c = defaultdict(Counter)
    trous = []
    porteurs = defaultdict(set)    # (famille) -> pieces porteuses
    for fam in COLS:
        porteurs[fam] = set(etat[fam])
    notes_de = defaultdict(set)
    for a, val in etat["note"].items():
        L, _v, _l = etat["_src"].get(("note", a)) or source("note", a, val)
        if L:
            notes_de[L].add(a)
    for i in sorted(T):
        for col, fam, lot, verdict_lot in (("Vente Réglée", "vente_reglee_app", "C8", LOT_C8.get(i)),
                                           ("Numéro de facture", "numero_facture_app", "C8", LOT_C8.get(i)),
                                           ("Annulée", "date_annulation_app", "C3", LOT_C3.get(i)),
                                           ("Commission TTC", "honoraires_entree", "C2", LOT_C2.get(i)),
                                           ("COMMENTAIRES", "note", "C4", "nette" if i in NOTE_C4 else None),
                                           ("En attente de", "note", "C4", "nette" if i in NOTE_C4 else None)):
            s = case(i, col)
            if not s:
                continue
            ps = propres(i)
            if fam == "honoraires_entree":
                ok = [a for a in ps if a in PI and (
                    (etat["honoraires_entree_app"].get(a) and colle("honoraires_entree_app", etat["honoraires_entree_app"][a], i))
                    or (HON.get(a) is not None and K.nombre(s) is not None and abs(HON[a] - K.nombre(s)) <= 1))]
                part = [a for a in ps if a in PI and HON.get(a) and K.nombre(s) and abs(HON[a] - 2 * K.nombre(s)) <= 2]
                porte = [a for a in ps if a in PI and (HON.get(a) or etat["honoraires_entree_app"].get(a))]
            elif fam == "note":
                ok = [a for a in notes_de.get(i, set()) if a in ps and any(c_ == col for c_, _t in segments(etat["note"][a][1]))]
                part, porte = [], [a for a in ps if a in etat["note"]]
            else:
                ok = [a for a in ps if a in etat[fam] and colle(fam, etat[fam][a], i)]
                part, porte = [], [a for a in ps if a in etat[fam]]
            if ok:
                c[col]["portee par une de ses pieces"] += 1
                continue
            ailleurs = sorted(a for a in voisines(i) if (
                (fam == "note" and a in etat["note"] and colle("note", etat["note"][a], i))
                or (fam not in ("note", "honoraires_entree") and a in etat[fam] and colle(fam, etat[fam][a], i))))
            f_ = s if col == "En attente de" else ""
            if ailleurs:
                cause = "⛔ PORTEE AILLEURS : %s (l'ecriture mal placee, nommee au ①)" % " ".join(map(str, ailleurs))
            elif col == "En attente de" and re.fullmatch(r"(?i)v(\s+\S+)?", f_):
                cause = "DECISION DEJA PRISE : C4 (16/11) ecarte « V » seul et « V prenom » (= VENDU, deja connu)"
            elif col == "En attente de" and not re.search(r"[0-9A-Za-zÀ-ÿ]", f_):
                cause = "DECISION DEJA PRISE : C4 (16/11) ecarte le pictogramme seul"
            elif col == "En attente de" and i in LOT_MOTIF:
                cause = "portee par motif_annulation_app (le motif TRADUIT, C4) : voir la colonne du motif"
            elif col == "En attente de" and i in F_NON_POSE:
                cause = "DECISION DEJA PRISE : C4 (17/11) texte de F non pose (affaire en cours, hors du lot 1)"
            elif fam == "honoraires_entree" and not porte and verdict_lot is None:
                g_ = [a for a in GEL_L.get(i, set()) if a in PI and HON.get(a)]
                cause = ("C2 la voyait sur une piece du GEL que le protocole ne lui donne pas (%s) : honoraires_entree de "
                         "HEKTOR, pas une ecriture rapatriee" % " ".join(map(str, sorted(g_))) if g_ else
                         "aucune piece, ni au gel ni au protocole, ne porte de commission, et C2 ne l'a pas listee : TROU")
            elif fam == "honoraires_entree" and part:
                cause = "le classeur note une PART, Hektor le total (facteur 2, 09/11) : pas une erreur"
            elif fam == "honoraires_entree" and porte:
                cause = "sa piece porte un AUTRE montant (conflit, choix « prendre les vides » du 09/11 : on ne corrige pas)"
            elif porte and fam != "note":
                cause = "sa piece porte une AUTRE valeur"
            elif verdict_lot is None:
                cause = "absente du lot %s : la case a ete remplie (ou la ligne est nee) APRES le lot" % lot
            elif verdict_lot not in ("nette", "1_aboutie", "2_en_cours"):
                cause = "DECISION DEJA PRISE : ecartee par le lot %s (%s)" % (lot, verdict_lot)
            elif fam == "note":
                cause = ("sa note C4 est sur une piece que le protocole ne lui donne pas (nommee au ①)" if NOTE_C4.get(i) not in ps
                         else "sa note C4 ne porte pas ce morceau (%s)" % col)
            else:
                cause = "posee par le lot %s, et sa piece ne l'a plus : TROU" % lot
            c[col][re.sub(r"\d{4,}", "N", cause)[:90]] += 1
            trous.append({"colonne": col, "id_unique": i, "ligne_du_sheet": V[i]["num"], "sheet": masque(s)[:80],
                          "cause": cause, "ses_pieces": " ".join(map(str, sorted(ps)))})
    return c, trous


dire()
dire("   ⛔ LE TEMOIN INVERSE, colonne par colonne (lignes TRANCHEES dont le Sheet porte la valeur) :")
TI0, TROUS = temoin_inverse(S0)
for col, cc in TI0.items():
    n = sum(cc.values())
    dire("      %-18s %5d lignes : %s" % (col, n, " . ".join("%s %d" % kv for kv in cc.most_common())))
# la charge (le mandat) et les avis (la ligne) : leurs temoins
n_ch = Counter()
for i in sorted(T):
    s = case(i, "Charge Commission")
    if not s:
        continue
    ms = {(str(PI[a]["hektor_annonce_id"]), str(PI[a]["numero_mandat"])) for a in V[i]["pieces"]
          if a in PI and str(PI[a].get("numero_mandat") or "").strip()}
    vals = [S0["charge"][m] for m in ms if m in S0["charge"]]
    if any(sa(v[0]) == sa(s) for v in vals):
        n_ch["portee par le carnet de son mandat"] += 1
    else:
        k_ = ("ses pieces ne citent aucun mandat" if not ms else "le carnet de son mandat ne porte aucune charge" if not vals
              else "le carnet de son mandat porte une AUTRE charge (%s)" % "+".join(sorted({v[1] for v in vals})))
        n_ch[k_] += 1
        TROUS.append({"colonne": "Charge Commission", "id_unique": i, "ligne_du_sheet": V[i]["num"], "sheet": s, "cause": k_,
                      "ses_pieces": " ".join(map(str, sorted(V[i]["pieces"])))})
dire("      %-18s %5d lignes : %s" % ("Charge Commission", sum(n_ch.values()), " . ".join("%s %d" % kv for kv in n_ch.most_common())))
n_av = Counter()
for i in sorted(D.LIG):
    if any(case(i, c_) for c_ in ("Avis à envoyer (oui / non)", "Commentaire Avis", "Avis envoyé")):
        if i in S0["avis"]:
            n_av["portee par sa ligne"] += 1
        else:
            k_ = "absente de C9 : remplie APRES le 16/11" if i not in AVIS_C9 else "dans C9, ABSENTE en base : TROU"
            n_av[k_] += 1
            TROUS.append({"colonne": "Avis", "id_unique": i, "ligne_du_sheet": V.get(i, {}).get("num"), "sheet": masque(
                " | ".join(case(i, c_) for c_ in ("Avis à envoyer (oui / non)", "Commentaire Avis", "Avis envoyé")))[:80],
                "cause": k_, "ses_pieces": "-"})
dire("      %-18s %5d lignes (toutes, la cle est la ligne) : %s" % ("Avis", sum(n_av.values()), " . ".join(
    "%s %d" % kv for kv in n_av.most_common())))
dire("      ⛔ commission_agence SORTIE du controle (son ③ du 24/11 : elle ne retrouve la Commission TTC qu'une fois sur "
     "4 789 ; c'est honoraires_entree qui la porte, 38 choix colonne P)")

# ═══════════════════════════════════════════ ③ LE GESTE A BLANC ET SON INVERSE ═════════════════════════════════════
dire()
dire("③ LE GESTE, A BLANC (copie en memoire de l'etat du registre)")
S1 = copy.deepcopy(S0)
JOURNAL = []
# LES GESTES SONT SIMULTANES (un echange, comme la paire croisee, libere sa cible en meme temps qu'il la prend) : on
#   retire d'abord toutes les ecritures qui partent, puis on pose ; deux ecritures vers la meme cible -> aucune ne part
GESTES = [e for e in E0 if e["decision"] in ("DEPLACER", "DOUBLON", "METTRE DE COTE") and mal_placee(e)]
vers_ = Counter((e["famille"], e["cible"]) for e in GESTES if e["decision"] == "DEPLACER")
for e in GESTES:
    if e["decision"] == "DEPLACER" and vers_[(e["famille"], e["cible"])] > 1:
        e["decision"], e["raison"] = "REMONTE", "%d visee par DEUX ecritures du meme geste" % e["cible"]
GESTES = [e for e in GESTES if e["decision"] in ("DEPLACER", "DOUBLON", "METTRE DE COTE")]


def cle_de(e, vers=False):
    if e["famille"] == "condition":
        return (e["cible"], e["cle"][1]) if vers else e["cle"]
    return e["cible"] if vers else e["piece"]


PARTIS = {}
for e in GESTES:
    PARTIS[id(e)] = (S1[e["famille"]].pop(cle_de(e)), S1["_src"].pop((e["famille"], cle_de(e))))
for e in GESTES:
    fam, (val, src_) = e["famille"], PARTIS[id(e)]
    if e["decision"] == "DEPLACER":
        if cle_de(e, True) in S1[fam]:
            raise SystemExit("⛔ le geste marcherait sur %s %s : arrete" % (fam, cle_de(e, True)))
        S1[fam][cle_de(e, True)] = val
        S1["_src"][(fam, cle_de(e, True))] = src_
        JOURNAL.append((fam, cle_de(e), cle_de(e, True), (val, src_), "DEPLACER"))
    else:
        JOURNAL.append((fam, cle_de(e), None, (val, src_), e["decision"]))
dire("   %d ecritures touchees : %s ; l'ancienne place de chacune est MISE DE COTE au journal (regle 6)" % (
    len(JOURNAL), " . ".join("%s %d" % kv for kv in Counter("%s %s" % (j[4], j[0]) for j in JOURNAL).most_common())))
# L'INVERSE : rejoue le journal sur l'etat d'arrivee -- il retire d'abord tout ce que le geste a pose, puis remet chaque
#   ecriture a son ancienne place (simultane, comme le geste)
S2 = copy.deepcopy(S1)
_rendus = []
for fam, de, vers, val, geste in JOURNAL:
    if vers is not None:
        _rendus.append((fam, de, (S2[fam].pop(vers), S2["_src"].pop((fam, vers)))))
    else:
        _rendus.append((fam, de, val))
for fam, de, (val, src_) in _rendus:
    S2[fam][de] = val
    S2["_src"][(fam, de)] = src_
e0, e1, e2 = empreinte(S0), empreinte(S1), empreinte(S2)
dire("   empreinte de depart %s ; apres le geste %s ; apres l'INVERSE %s -> %s" % (
    e0[:8], e1[:8], e2[:8], "⭐ IDENTIQUE au depart" if e0 == e2 else "⛔ DIFFERENTE"))

# ═══════════════════════════════════════════ ④ LE TEMOIN DE FIN ═══════════════════════════════════════════════════
dire()
dire("④ LE TEMOIN DE FIN : le meme controle, rejoue")
VACANTES, INTERDITES = set(), set()
E1 = controle(S1)
m0 = [e for e in E0 if mal_placee(e)]
m1 = [e for e in E1 if mal_placee(e)]
nommees = {(e["famille"], str(e["cle"])) for e in E0 if mal_placee(e)
           and e["decision"] not in ("DEPLACER", "DOUBLON", "METTRE DE COTE")}
hors = [e for e in m1 if (e["famille"], str(e["cle"])) not in nommees]
dire("   SANS le geste (l'inverse) : %d ecritures mal placees" % len(m0))
dire("   APRES le geste            : %d mal placees, dont %d NOMMEES (laissees ou remontees, decision proposee) et "
     "⭐ %d HORS DES NOMMEES (attendu 0)" % (len(m1), len(m1) - len(hors), len(hors)))
for e in hors[:20]:
    dire("      ⛔ %s %s %s" % (e["famille"], e["cle"], e["classe"]))
TI1, _t1 = temoin_inverse(S1)
for col in TI0:
    a0 = TI0[col]["portee par une de ses pieces"]
    a1 = TI1[col]["portee par une de ses pieces"]
    if a0 != a1:
        dire("   temoin inverse %-18s : portees par leur propre piece %d -> %d" % (col, a0, a1))
# la conservation : rien ne se perd (une ecriture deplacee ou mise de cote reste au journal)
n0 = sum(len(S0[f]) for f in S0 if f != "_src")
n1 = sum(len(S1[f]) for f in S1 if f != "_src")
n_cote = sum(1 for j in JOURNAL if j[2] is None)
dire("   conservation : %d ecritures au depart = %d apres + %d mises de cote au journal -> %s" % (
    n0, n1, n_cote, "BOUCLE" if n0 == n1 + n_cote else "⛔ NE BOUCLE PAS"))

# ═══════════════════════════════════════════ LES FICHIERS ═════════════════════════════════════════════════════════
if arg.csv:
    def val_txt(e):
        v = e["valeur"]
        if isinstance(v, tuple):
            v = " | ".join(str(x) for x in v[1:]) if e["famille"] != "charge" else v[0]
        return masque(str(v))[:100]
    f1 = P.NOTICE / ("PROTOCOLE_REALIGNEMENT_TEMPS1_LES_ANOMALIES_PASSAGE_%d%s_2026-11-24.csv" % (arg.passage, "_AVEC_R26" if arg.r26 else ""))
    with f1.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["colonne", "cle (piece / ligne / mandat)", "valeur au registre", "ligne d'ou elle vient (lot)", "lot",
                    "contenu", "ligne(s) du GEL", "ligne(s) du PROTOCOLE", "contenu d'une AUTRE ligne", "classe",
                    "decision proposee", "raison", "cible"])
        for e in sorted(E0, key=lambda e: (e["decision"] == "LAISSER", e["famille"], str(e["cle"]))):
            if e["classe"] == "JUSTE":
                continue
            w.writerow([NOMS[e["famille"]], e["cle"], val_txt(e), e.get("source") or "-", e["lot"], e.get("contenu", "-"),
                        e["gel"], e.get("protocole", "-"), e["contenu_d_une_autre_ligne"], e["classe"], e["decision"],
                        e["raison"], e.get("cible") or ""])
    f2 = P.NOTICE / ("PROTOCOLE_REALIGNEMENT_TEMPS1_LES_TROUS_PASSAGE_%d%s_2026-11-24.csv" % (arg.passage, "_AVEC_R26" if arg.r26 else ""))
    with f2.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["colonne", "id_unique", "ligne_du_sheet", "sheet", "cause", "ses_pieces"],
                           delimiter=";")
        w.writeheader()
        for t in sorted(TROUS, key=lambda t: (t["colonne"], t["cause"], t["ligne_du_sheet"] or 0)):
            w.writerow(t)
    f3 = P.NOTICE / ("PROTOCOLE_REALIGNEMENT_TEMPS1_LE_GESTE_A_BLANC_PASSAGE_%d%s_2026-11-24.csv" % (arg.passage, "_AVEC_R26" if arg.r26 else ""))
    with f3.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["colonne", "de (ancienne place, mise de cote au journal)", "vers", "geste", "valeur",
                    "l'inverse : remet", "a"])
        for fam, de, vers, val, geste in JOURNAL:
            w.writerow([NOMS[fam], de, vers if vers is not None else "- (mise de cote)", geste,
                        masque(str(val[0] if not isinstance(val[0], tuple) else val[0][1]))[:100], "la valeur", de])
    dire()
    dire("-> %s" % f1)
    dire("-> %s" % f2)
    dire("-> %s" % f3)
