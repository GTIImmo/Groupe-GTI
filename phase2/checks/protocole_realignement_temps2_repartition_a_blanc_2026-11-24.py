"""TEMPS 2 DU REALIGNEMENT (24/11) : LA REPARTITION, MESUREE SUR L'ETAT D'ARRIVEE (apres le rejeu de la vague).
LECTURE SEULE : rien en base, rien dans le Sheet, rien chez Hektor -- ce script DIT ce que la vague et le remede A2 feraient.

SON MOT : « Elle est la seule accrochee au numero de chaine, qui se recalcule chaque nuit. ⛔ DONC L'AUDIT D'AUJOURD'HUI NE
VAUT RIEN POUR ELLE : il faut mesurer sur L'ETAT D'ARRIVEE, apres le rejeu de l'appariement. »

  ① L'AUDIT SUR L'ETAT D'ARRIVEE : pour chaque ligne TRANCHEE, les NOMS et les POURCENTAGES du classeur se retrouvent-ils
     dans les parts de sa chaine d'arrivee (le rejeu E du passage -- la vague -- PLUS le remede A2 a blanc, avec SES DEUX
     DECISIONS : U0GQ3KTO on ne recopie rien, on laisse, en reserve ; NRZVKH85 on COMPLETE la part de sortie FERNANDEZ 50,
     sans toucher l'existante) ? Les parts EN TROP, MANQUANTES, les NOMS et les POURCENTAGES qui different, NOMMES.
     ⭐ SA REGLE DE LECTURE : « negociateur 1 a 100 % » = DEUX FOIS LA MEME PERSONNE, 50 entree + 50 sortie ; C'EST LE NOM
     qui dit le partage, JAMAIS le pourcentage. La comparaison se fait PAR PERSONNE (hektor_user_id), apres la resolution
     des noms du 13/11 (rapatrier_repartition_classeur.resoudre : l'annuaire, les alias, les initiales) -- c'est elle qui
     absorbe les variantes (« CECILE LIBOZ MOURE » / « MOUREY LIBOZ », « CHRISTELE GENTES » / « GENTES »).
  ② LA GARDE DE SA DECOUVERTE 1 : « ⛔ NE JAMAIS VIDER UNE CHAINE QUI GARDE UNE VENTE REGLEE » -- apres le rejeu, combien de
     chaines se retrouvent a ZERO PART en gardant une vente reglee ? « Si la reponse est une seule, 19131, ton remede est bon. »
  ③ LE TEMOIN DE FIN : apres le remede a blanc, zero ligne dont la repartition ne correspond pas au classeur (hors celles
     NOMMEES) -- et l'inverse, sans le remede.

USAGE : python -u -X utf8 phase2/checks/protocole_realignement_temps2_repartition_a_blanc_2026-11-24.py --passage P [--csv]
"""
import argparse
import csv
import json
from pathlib import Path
import re
import sqlite3
import sys
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
ap.add_argument("--export-a2", default="", help="ecrit A2 v3 en JSON (pour le patch par pieces de la vague du soir)")
ap.add_argument("--retrait-e", action="store_true",
                help="l'etat d'arrivee de LA VAGUE ENTIERE : R26 + le retrait de 4126 et 21520 (le dossier a blanc du "
                     "retrait : sa copie du socle, son module retouche, son brouillon et ses rejeux)")
arg = ap.parse_args()
if arg.retrait_e:
    # ⭐ 24/11 au soir : la vague pose le retrait de E DANS LA MEME NUIT (son mot) -- A2 se mesure donc sur l'arrivee avec
    #   le retrait. Le dossier a blanc du retrait porte tout : la copie du socle (passage a blanc), le module de nuit sans
    #   les deux exclusions, le brouillon, et les rejeux A et E faits avec ce module.
    _AB = P.DOSSIER.parent / "protocole_a_blanc_retrait_e"
    P.SOCLE = _AB / "socle.sqlite"
    P.DOSSIER = _AB
    PO.MODULE = _AB / "affaire_ledger_sans_4126_21520.py"


def dire(s=""):
    print(s, flush=True)


con = P.socle()
image, version = con.execute("select image, version from passage where id=?", (arg.passage,)).fetchone()
V = {}
for i, num, v, ps in con.execute("select id_unique, num, verdict, pieces from verdict where passage=?", (arg.passage,)):
    V[i] = {"num": num, "verdict": v, "pieces": set(json.loads(ps)) if ps else set()}
con.close()
T = {i for i, v in V.items() if v["verdict"] == "TRANCHEE"}
I = P.Image(P.IMAGES / image)
D, PI = I.D, I.pieces
ch_img = {a: int(PI[a]["app_chaine_id"]) for a in PI if PI[a]["app_chaine_id"] is not None}
chA, _ = PO.rejeu_en_cache("A", image, PO.FICHIER_DET_PROD, PO.ETEINTS, False)
# --r26 : l'etat d'arrivee AVEC R26 a blanc (protocole_r26_vente_emportee_a_blanc : son brouillon et son rejeu E, dans
#   le dossier a part protocole_a_blanc_r26) -- sinon le rejeu E du passage tel qu'il est
_DOS_E = (P.DOSSIER.parent / "protocole_a_blanc_r26") if arg.r26 else P.DOSSIER
brouillon = _DOS_E / ("brouillon_detachements_protocole_passage_%d.csv" % arg.passage)
_d0, P.DOSSIER = P.DOSSIER, _DOS_E
chE, _ = PO.rejeu_en_cache("E", image, brouillon, {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
P.DOSSIER = _d0
mA, mE = PO.membres(chA), PO.membres(chE)
gel_l = defaultdict(list)
for i, a, ro, *_r in I.gel:
    gel_l[i].append((int(a), ro))
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
loc.row_factory = sqlite3.Row
dire("TEMPS 2 : LA REPARTITION SUR L'ETAT D'ARRIVEE -- passage %d (%s), image %s" % (arg.passage, version, image))
dire("   temoin du rejeu A : %d pieces dans un autre dossier que l'image (attendu 0)"
     % sum(1 for a in ch_img if ch_img[a] != chA.get(a)))

COMPTES_ADMIN = {"46"}
REP = defaultdict(list)
for r in loc.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine "
                     "from app_affaire_repartition"):
    REP[int(r["app_chaine_id"])].append(dict(r))
n_rows = sum(len(v) for v in REP.values())
# l'annuaire et la resolution du 13/11 (comme le controle du § 7)
RR.RAP.ALIAS_NEGOCIATEUR = dict(RR.RAP.ALIAS_REPLI)
_gens = defaultdict(list)
NOM_DE = {}
for r in loc.execute("select hektor_user_id, nom, prenom, is_active from app_hektor_negotiator_agency_directory"):
    nom_ = " ".join(sorted(RR.mots_du_nom(r["nom"])))
    pre_ = " ".join(sorted(RR.mots_du_nom(r["prenom"])))
    NOM_DE[str(r["hektor_user_id"])] = "[compte admin]" if str(r["hektor_user_id"]) in COMPTES_ADMIN else (
        "%s %s" % (r["prenom"] or "", r["nom"] or "")).strip()
    if nom_:
        _gens[(nom_, pre_)].append(dict(r))
PAR_NOM = defaultdict(list)
for (nom_, pre_), fiches in _gens.items():
    act = [f_ for f_ in fiches if f_.get("is_active") in (1, "1", True, "true", "True")]
    choix = sorted(act or fiches, key=lambda f_: int(str(f_["hektor_user_id"])))[0]
    PAR_NOM[nom_].append({"nom": nom_, "prenom": pre_, "hektor_user_id": str(choix["hektor_user_id"]), "fiches": len(fiches)})
_MOTS_ADMIN = set()
for x in COMPTES_ADMIN:
    for nom_, in loc.execute("select nom from app_hektor_negotiator_agency_directory where cast(hektor_user_id as text)=?", (x,)):
        _MOTS_ADMIN |= set(RR.mots_du_nom(nom_ or ""))


def masque(n_):
    return "[compte admin]" if _MOTS_ADMIN and set(RR.mots_du_nom(n_ or "")) & _MOTS_ADMIN else n_


def nom(u):
    return NOM_DE.get(str(u), "user %s" % u)


def sheet_txt(i):
    return " | ".join("%s %s" % (masque(D.case(i, "Négociateur %d" % k).strip()), D.case(i, "Pourcentage %d" % k).strip())
                      for k in (1, 2, 3) if D.case(i, "Négociateur %d" % k).strip())


def sig_sheet(i, sur_la_chaine):
    """La repartition du Sheet, PAR PERSONNE : {(cote, user, part)} -- ou un refus motive (le nom ne se resout pas)."""
    noms = [D.case(i, "Négociateur %d" % k) for k in (1, 2, 3)]
    pcts = [K.nombre(D.case(i, "Pourcentage %d" % k)) for k in (1, 2, 3)]
    parts, pq = RR.nettoyer(noms, pcts)
    if pq:
        return None, "nettoyage : " + pq
    qui = {}
    for n_, _p in parts:
        q, motif = RR.resoudre(n_, PAR_NOM, None, sur_la_chaine)
        if motif:
            return None, "le nom « %s » ne se resout pas (%s)" % (masque(n_), motif)
        qui[n_] = q["hektor_user_id"]
    cotes, pq = RR.decomposer(parts)
    if pq:
        return None, "decomposition : " + pq
    return {(c, qui[n_], round(pc, 2)) for c, _r, n_, pc in cotes}, ""


def sig_rows(rows):
    return {(r["cote"], str(r["hektor_user_id"]), round(float(r["pourcentage"] or 0), 2)) for r in rows}


def lis(sig):
    return " + ".join("%s %s %g" % (c, nom(u), p) for c, u, p in sorted(sig)) or "AUCUNE"


def vraies(i):
    return sorted(a for a in V[i]["pieces"] if I.nature.get(a) == PC.VRAIE)


RANG = {"vente": 0, "compromis": 1, "offre": 2}
source = {}
for i in V:
    g = [(a, ro) for a, ro in gel_l.get(i, []) if a in PI]
    if g:
        g.sort(key=lambda t: RANG.get(t[1] or PI[t[0]]["kind"], 3))
        source[i] = ch_img.get(g[0][0])
cible_de = {i: (chE.get(vraies(i)[0]) if vraies(i) else None) for i in T}
LIGNES_DE = defaultdict(set)      # chaine d'arrivee -> les lignes tranchees qui y arrivent
for i in T:
    if cible_de[i] is not None:
        LIGNES_DE[cible_de[i]].add(i)

# ═══════════════════════════════ LE REMEDE A2 (repris de protocole_a1_a2_a3_le_remede_a_blanc) ═══════════════════════
# v1 = le remede mesure le 24/11 au matin ; v2 = v1 + LA GARDE (« ne jamais vider une chaine qui garde une vente reglee »,
#   sous sa forme la plus juste : une chaine n'est JAMAIS videe quand une ligne tranchee qui y ARRIVE reconnait ses parts --
#   elle les garde, et la ligne qui part en recoit une COPIE) + L'ECHANGE de la paire croisee (deux lignes dont chacune
#   arrive sur la repartition de l'autre : les deux parts sont mises de cote et recopiees en croix).
def sig_de(j, rows):
    return sig_sheet(j, {str(r["hektor_user_id"]) for r in rows})[0]


possede = defaultdict(set)
PAR_UNE_AUTRE_CHAINE = {}
for i in T:
    s = source.get(i)
    if s in REP and sig_de(i, REP[s]) == sig_rows(REP[s]):
        possede[s].add(i)
        continue
    # ⭐ v2 : ses parts sont sur UNE AUTRE de ses chaines d'aujourd'hui (protocole ou gel) que celle de la source du gel
    chs = sorted({ch_img.get(a) for a in V[i]["pieces"] | {a for a, _r in gel_l.get(i, [])} if ch_img.get(a) in REP} - {s})
    m_ = [c for c in chs if sig_de(i, REP[c]) == sig_rows(REP[c])]
    if len(m_) == 1:
        possede[m_[0]].add(i)
        PAR_UNE_AUTRE_CHAINE[i] = m_[0]
arrive_et_reconnait = {s: {j for j in LIGNES_DE.get(s, set()) if sig_de(j, REP[s]) == sig_rows(REP[s])} for s in REP}


# ⭐ v3 (24/11, son 3e mot, ③ et ④) : « une annulee ne porte AUCUNE part » -- « V3FO5NDA : NON, PAS DE COPIE DE LA REPARTITION
#   TEYSSONNIER » ; « les 49 annulees : ON LAISSE, aucune part ». Une recopie dont TOUTES les lignes d'arrivee sont des annulees
#   (Etat Actuel du Sheet) n'est pas faite ; les parts qui partent restent MISES DE COTE (regle 6), jamais supprimees.
ANNULEES = {i for i in T if D.case(i, "Etat Actuel").strip().lower().startswith("annul")}


def remede(garde, echange, sans_annulee=False):
    part_toutes = {s for s, L_ in possede.items() if s not in {cible_de[i] for i in L_}}
    if garde:
        gardees = {s for s in part_toutes if arrive_et_reconnait.get(s)}
        part_toutes -= gardees
    else:
        gardees = set()
    prevu = {s: [dict(r) for r in rows] for s, rows in REP.items() if s not in part_toutes}
    recopies, mises, conflits, completees, decisions = [], [], [], [], []
    refus_annulee = []
    for s in sorted(possede):
        L_ = possede[s]
        for t in sorted({cible_de[i] for i in L_} - {s, None}):
            Lt = "+".join(sorted(i for i in L_ if cible_de[i] == t))
            if sans_annulee and all(i in ANNULEES for i in Lt.split("+")):
                refus_annulee.append((s, t, Lt))
                continue
            cur = prevu.get(t, [])
            if cur and sig_rows(cur) == sig_rows(REP[s]):
                continue
            if cur:
                conflits.append((s, t, Lt, lis(sig_rows(cur))))
                continue
            for r in REP[s]:
                recopies.append(dict(r, ancienne_chaine=s, chaine_cible=t, lignes=Lt, geste="recopie"))
            prevu[t] = [dict(r, app_chaine_id=t) for r in REP[s]]
        if s in part_toutes:
            for r in REP[s]:
                mises.append(dict(r, ancienne_chaine=s, lignes="+".join(sorted(L_))))
    for s, rows in sorted(REP.items()):
        if possede.get(s) or s in mE:
            continue
        t = chE.get(s)
        cur = prevu.get(t, []) if t is not None else None
        if t is not None and cur and sig_rows(cur) == sig_rows(rows):
            mises.extend(dict(r, ancienne_chaine=s, lignes="-") for r in rows)
            prevu.pop(s, None)
        elif t is not None and not cur:
            recopies.extend(dict(r, ancienne_chaine=s, chaine_cible=t, lignes="-", geste="recopie") for r in rows)
            prevu[t] = [dict(r, app_chaine_id=t) for r in rows]
            mises.extend(dict(r, ancienne_chaine=s, lignes="-") for r in rows)
            prevu.pop(s, None)
        else:
            conflits.append((s, t, "-", "orpheline"))
    en_conflit = set()
    for s, t, Lt, porte in conflits:
        if "U0GQ3KTO" in Lt.split("+"):
            decisions.append("U0GQ3KTO : chaine %s -> %s, rien de recopie, LAISSEE EN PLACE, EN RESERVE (8RWTD0YX, meme "
                             "mandat 14065, les deux Annulee : aucun honoraire a verser)" % (s, t))
            en_conflit.add("U0GQ3KTO")
        elif "NRZVKH85" in Lt.split("+"):
            sg = sig_de("NRZVKH85", prevu.get(t, []))
            manque = sorted((sg or set()) - sig_rows(prevu.get(t, [])))
            for c_, u_, p_ in manque:
                part = {"app_chaine_id": t, "cote": c_, "rang": 1, "hektor_user_id": u_, "nom_au_moment": nom(u_),
                        "pourcentage": p_, "origine": "classeur_reconstitue", "complete_le": "a blanc 24/11"}
                prevu[t].append(part)
                completees.append(dict(part, lignes="NRZVKH85", geste="completee"))
            decisions.append("NRZVKH85 : chaine %s, COMPLETEE de %s ; la part existante (%s) intacte" % (
                t, lis(set(manque)), lis(sig_rows([r for r in prevu[t] if r.get("complete_le") is None]))))
        else:
            en_conflit |= set(Lt.split("+"))
    echanges = []
    if echange:
        faux = [i for i in sorted(T) if cible_de[i] in mE and any(D.case(i, "Négociateur %d" % k).strip() for k in (1, 2, 3))
                and sig_de(i, prevu.get(cible_de[i], [])) != sig_rows(prevu.get(cible_de[i], []))]
        for i in faux:
            ti = cible_de[i]
            for j in faux:
                tj = cible_de[j]
                if j <= i or ti == tj or not prevu.get(ti) or not prevu.get(tj):
                    continue
                if sans_annulee and (i in ANNULEES or j in ANNULEES):
                    continue
                if sig_de(j, prevu[ti]) == sig_rows(prevu[ti]) and sig_de(i, prevu[tj]) == sig_rows(prevu[tj]):
                    ri, rj = prevu[ti], prevu[tj]
                    for r in ri:
                        mises.append(dict(r, ancienne_chaine=ti, lignes=j + " (echange)"))
                        recopies.append(dict(r, ancienne_chaine=ti, chaine_cible=tj, lignes=j, geste="echange"))
                    for r in rj:
                        mises.append(dict(r, ancienne_chaine=tj, lignes=i + " (echange)"))
                        recopies.append(dict(r, ancienne_chaine=tj, chaine_cible=ti, lignes=i, geste="echange"))
                    prevu[ti] = [dict(r, app_chaine_id=ti) for r in rj]
                    prevu[tj] = [dict(r, app_chaine_id=tj) for r in ri]
                    echanges.append("%s (chaine %s) <-> %s (chaine %s)" % (i, ti, j, tj))
    return {"prevu": prevu, "recopies": recopies, "mises": mises, "conflits": conflits, "completees": completees,
            "decisions": decisions, "en_conflit": en_conflit, "gardees": gardees, "echanges": echanges,
            "refus_annulee": refus_annulee}


R1 = remede(False, False)
R2 = remede(True, True)
R3 = remede(True, True, sans_annulee=True)
dire()
for nom_r, R_ in (("v1 (le remede du matin)", R1), ("v2 (+ la garde + l'echange)", R2),
                  ("v3 (+ aucune copie vers une annulee, sa decision)", R3)):
    vivantes = sum(len(v) for v in R_["prevu"].values())
    n_ech = sum(1 for x in R_["recopies"] if x.get("geste") == "echange")
    dire("LE REMEDE A2 A BLANC %s, AVEC SES DEUX DECISIONS : %d parts recopiees (dont %d par echange) . %d mises de cote "
         "avec leur ancien numero . %d completee(s) . %d conflits ; conservation %d = %d - %d + %d + %d -> %s" % (
             nom_r, len(R_["recopies"]), n_ech, len(R_["mises"]), len(R_["completees"]), len(R_["conflits"]), vivantes,
             n_rows, len(R_["mises"]), len(R_["recopies"]), len(R_["completees"]),
             "BOUCLE" if vivantes == n_rows - len(R_["mises"]) + len(R_["recopies"]) + len(R_["completees"])
             else "⛔ NE BOUCLE PAS"))
dire("   ⭐ v3, SA DECISION « une annulee ne porte aucune part » : %d recopie(s) refusee(s) : %s" % (
    len(R3["refus_annulee"]), " ; ".join("%s -> %s (%s)" % x for x in R3["refus_annulee"])))
for d_ in R3["decisions"]:
    dire("   ⭐ " + d_)
dire("   ⭐ LA GARDE (v2) : %d chaine(s) que v1 aurait videes et qu'une ligne qui y ARRIVE reconnait : %s" % (
    len(R2["gardees"]), " ; ".join("%s (gardee par %s, copie pour %s)" % (
        s, "+".join(sorted(arrive_et_reconnait[s])), "+".join(sorted(possede[s]))) for s in sorted(R2["gardees"]))))
dire("   ⭐ L'ECHANGE (v2) : %s" % (" ; ".join(R2["echanges"]) or "aucun"))
prevu = R3["prevu"]
lignes_en_conflit = R3["en_conflit"]
recopies, mises, completees = R3["recopies"], R3["mises"], R3["completees"]

# ═══════════════════════════════ ① L'AUDIT SUR L'ETAT D'ARRIVEE ═══════════════════════════════════════════════════════


def juger_ligne(i, etat):
    noms = [D.case(i, "Négociateur %d" % k).strip() for k in (1, 2, 3)]
    if not any(noms):
        return None
    t = cible_de[i]
    rows = etat.get(t, []) if t in mE else []
    sg, refus = sig_sheet(i, {str(r["hektor_user_id"]) for r in rows})
    sr = sig_rows(rows)
    e = {"id_unique": i, "ligne_du_sheet": V[i]["num"], "sheet": sheet_txt(i), "chaine_d_arrivee": t,
         "registre": lis(sr), "origines": "+".join(sorted({r["origine"] for r in rows})) or "-",
         "autres_lignes_de_la_chaine": "+".join(sorted(LIGNES_DE.get(t, set()) - {i})) or "-"}
    if i in lignes_en_conflit:
        e["verdict"], e["detail"] = "CONFLIT NOMME (sa decision : laissee, en reserve)", ""
        return e
    if not rows:
        chs = {ch_img.get(a) for a in V[i]["pieces"] | {a for a, _r in gel_l.get(i, [])}}
        autres = sorted(c for c in chs if REP.get(c))
        if autres:
            qui_ = sorted({j for c in autres for j in possede.get(c, set())} - {i})
            det_ = ("sa chaine d'aujourd'hui %s porte la repartition d'une AUTRE ligne (%s : %s) -- la sienne n'a jamais ete "
                    "ecrite (regle du 14/11 : une repartition par chaine)" % (
                        " ".join(map(str, autres)), "+".join(qui_) or "aucune ligne tranchee", lis(sig_rows(REP[autres[0]]))))
        else:
            det_ = "TROU : aucune part, ni aujourd'hui sur ses chaines ni a l'arrivee"
        e["verdict"], e["detail"] = "⛔ AUCUNE PART sur sa chaine d'arrivee (%s)" % D.case(i, "Etat Actuel").strip(), det_
        return e
    if sg is None:
        e["verdict"], e["detail"] = "NOM NON RESOLU (variante ?)", refus
        return e
    if sg == sr:
        e["verdict"], e["detail"] = "JUSTE", ""
        return e
    # a qui ressemblent les parts ? a une AUTRE ligne de la meme chaine d'arrivee ?
    for j in sorted(LIGNES_DE.get(t, set()) - {i}):
        sj, _ = sig_sheet(j, {str(r["hektor_user_id"]) for r in rows})
        if sj == sr:
            e["verdict"], e["detail"] = "⛔ SA CHAINE PORTE LA REPARTITION D'UNE AUTRE LIGNE (%s)" % j, ""
            return e
    manq, trop = sg - sr, sr - sg
    det = []
    us_s, us_r = {u for _c, u, _p in sg}, {u for _c, u, _p in sr}
    if us_s != us_r:
        det.append("personnes : Sheet %s / registre %s" % ("+".join(sorted(nom(u) for u in us_s)),
                                                           "+".join(sorted(nom(u) for u in us_r))))
    if manq:
        det.append("MANQUANTES : %s" % lis(manq))
    if trop:
        det.append("EN TROP : %s" % lis(trop))
    if us_s == us_r:
        v_ = "⛔ LES POURCENTAGES DIFFERENT (memes personnes)"
    elif {(c, p) for c, _u, p in sg} == {(c, p) for c, _u, p in sr}:
        v_ = "⛔ LES NOMS DIFFERENT (memes parts)"
    elif len(sr) < len(sg):
        v_ = "⛔ PARTS MANQUANTES"
    elif len(sr) > len(sg):
        v_ = "⛔ PARTS EN TROP"
    else:
        v_ = "⛔ NOMS ET POURCENTAGES DIFFERENT"
    e["verdict"], e["detail"] = v_, " ; ".join(det)
    return e


def audit(etat):
    out = [x for x in (juger_ligne(i, etat) for i in sorted(T)) if x]
    return out


dire()
dire("① L'AUDIT SUR L'ETAT D'ARRIVEE (les lignes TRANCHEES qui portent un negociateur)")
APRES = audit(prevu)
lignes_en_conflit = R1["en_conflit"]
APRES_V1 = audit(R1["prevu"])
lignes_en_conflit = R2["en_conflit"]
SANS = audit({t: rows for t, rows in REP.items()})       # sans le remede : les parts restent ou elles sont
c_ap, c_v1, c_sa = (Counter(e["verdict"] for e in APRES), Counter(e["verdict"] for e in APRES_V1),
                    Counter(e["verdict"] for e in SANS))
dire("   %d lignes jugees" % len(APRES))
for k in sorted(set(c_ap) | set(c_sa) | set(c_v1), key=lambda k: -c_ap.get(k, 0)):
    dire("      %-66s remede v2 %5d  |  v1 %5d  |  sans remede %5d" % (k, c_ap.get(k, 0), c_v1.get(k, 0), c_sa.get(k, 0)))
# les parts a l'arrivee qu'AUCUNE ligne tranchee ne reconnait (sa mesure : « 22 chaines dont aucune ligne ne reconnait »)
sans_ligne = []
for t, rows in sorted(prevu.items()):
    if t not in mE or not rows:
        continue
    lg = LIGNES_DE.get(t, set())
    if not lg:
        sans_ligne.append((t, lis(sig_rows(rows)), "+".join(sorted({r["origine"] for r in rows}))))
dire("   les chaines d'arrivee qui portent des parts sans AUCUNE ligne tranchee qui y arrive : %d (%s)" % (
    len(sans_ligne), " . ".join("%s %d" % kv for kv in Counter(x[2] for x in sans_ligne).most_common())))
ab_ = [t for t, rows in prevu.items() if rows and t not in mE]
dire("   les parts vivantes sur une chaine qui n'existe plus a l'arrivee (orphelines) : %d chaine(s) %s" % (
    len(ab_), " ".join(map(str, sorted(ab_)[:20]))))

# ═══════════════════════════════ ② LA GARDE : une vente reglee sans part ════════════════════════════════════════════
dire()
dire("② LA GARDE : apres le rejeu, les chaines a ZERO PART qui gardent une VENTE REGLEE")
VR = {int(a) for a, in loc.execute("select app_affaire_id from app_affaire_ledger where coalesce(vente_reglee_app,'')<>''")}
TIENT = defaultdict(set)
for i in T:
    for a in V[i]["pieces"]:
        TIENT[a].add(i)
def la_garde(etat):
  out = []
  for t, membres_ in sorted(mE.items()):
    ventes = [a for a in membres_ if a in PI and PI[a]["kind"] == "vente" and (
        a in VR or any(D.case(j, "Etat Actuel").strip() == "Vente réglée" for j in TIENT.get(a, set())))]
    if not ventes:
        continue
    apres_ = etat.get(t, [])
    if apres_:
        continue
    avant_ = REP.get(t, [])
    lignes = sorted(LIGNES_DE.get(t, set()) | {j for a in ventes for j in TIENT.get(a, set())})
    out.append({"chaine_d_arrivee": t, "ventes_reglees": " ".join(map(str, sorted(ventes))),
                  "lignes": "+".join(lignes) or "AUCUNE LIGNE TRANCHEE",
                  "etat_des_lignes": "+".join(D.case(j, "Etat Actuel").strip() for j in lignes) or "-",
                  "negociateurs_au_sheet": " / ".join(sheet_txt(j) for j in lignes) or "-",
                  "parts_aujourd_hui_sur_ce_numero": lis(sig_rows(avant_)),
                  "pourquoi": ("VIDEE PAR LE REMEDE (ses parts partent avec leur ligne)" if avant_ else
                               "chaine NEE a la vague, sans part" if t not in mA else "deja sans part aujourd'hui"),
                  "chaine_aujourd_hui": " ".join(sorted({str(ch_img.get(a)) for a in ventes}))})
  return out


GARDE_V1 = la_garde(R1["prevu"])
garde = la_garde(prevu)
dire("   remede v1 : %d chaine(s) -- %s" % (len(GARDE_V1), " ".join(str(g["chaine_d_arrivee"]) for g in GARDE_V1)))
dire("   remede v2 : %d chaine(s) : %s" % (len(garde), " . ".join("%s %d" % kv for kv in Counter(g["pourquoi"] for g in garde).most_common())))
for g in garde:
    dire("      chaine %-7s vente(s) %-16s lignes %-20s (%s) ; aujourd'hui sur %s ; %s ; Sheet : %s" % (
        g["chaine_d_arrivee"], g["ventes_reglees"], g["lignes"], g["etat_des_lignes"], g["chaine_aujourd_hui"],
        g["pourquoi"], g["negociateurs_au_sheet"][:60]))
sans_r = []
for t, membres_ in sorted(mE.items()):
    ventes = [a for a in membres_ if a in PI and PI[a]["kind"] == "vente" and (
        a in VR or any(D.case(j, "Etat Actuel").strip() == "Vente réglée" for j in TIENT.get(a, set())))]
    if ventes and not REP.get(t):
        sans_r.append(t)
dire("   temoin : SANS le remede (les parts restent sur leur ancien numero), %d chaines d'arrivee a vente reglee n'auraient "
     "aucune part" % len(sans_r))
dire("   ⭐ 19131 (sa decouverte 1) : %s" % ("DANS LA GARDE" if any(g["chaine_d_arrivee"] == 19131 for g in garde)
                                            else "pas dans la garde -- %s" % (
                                                "la chaine 19131 a l'arrivee porte %s" % lis(sig_rows(prevu.get(19131, [])))
                                                if 19131 in mE else "19131 n'existe plus a l'arrivee")))

# ═══════════════════════════════ ③ LE TEMOIN DE FIN ═════════════════════════════════════════════════════════════════
dire()
dire("③ LE TEMOIN DE FIN (lignes TRANCHEES a negociateur dont la chaine d'arrivee ne porte pas la repartition du Sheet)")
nok_ap = [e for e in APRES if e["verdict"] != "JUSTE"]
nok_sa = [e for e in SANS if e["verdict"] != "JUSTE"]
dire("   APRES le remede : %d (toutes NOMMEES au fichier, par verdict) ; SANS le remede : %d" % (len(nok_ap), len(nok_sa)))
gagne = {e["id_unique"] for e in APRES if e["verdict"] == "JUSTE"} - {e["id_unique"] for e in SANS if e["verdict"] == "JUSTE"}
perdu = {e["id_unique"] for e in SANS if e["verdict"] == "JUSTE"} - {e["id_unique"] for e in APRES if e["verdict"] == "JUSTE"}
dire("   le remede rend juste %d lignes ; ⛔ il en rend FAUSSES %d %s" % (len(gagne), len(perdu),
                                                                     " ".join(sorted(perdu)[:20])))

if arg.export_a2:
    # ⭐ LA VAGUE DU SOIR (C, valide le 24/11) : A2 v3 exporte pour le patch PAR PIECES -- ses cibles sont des chaines
    #   d'ARRIVEE (elles n'existent qu'apres le chainage) : le patch exigera que chaque chaine touchee porte EXACTEMENT les
    #   membres que le rejeu prevoit, sinon il refuse tout
    _ch = sorted({x["ancienne_chaine"] for x in recopies + mises} | {x["chaine_cible"] for x in recopies}
                 | {x["app_chaine_id"] for x in completees})
    _vr_sql = sorted(t for t, membres_ in mE.items()
                     if any(a in VR and a in PI and PI[a]["kind"] == "vente" for a in membres_) and not prevu.get(t))
    _out = {"passage": arg.passage, "image": image,
            "recopies": [{k: x.get(k) for k in ("ancienne_chaine", "chaine_cible", "cote", "rang", "hektor_user_id",
                                                 "nom_au_moment", "pourcentage", "origine", "lignes", "geste")}
                         for x in recopies],
            "mises": [{k: x.get(k) for k in ("ancienne_chaine", "cote", "rang", "hektor_user_id", "nom_au_moment",
                                              "pourcentage", "origine", "lignes")} for x in mises],
            "completees": [{k: x.get(k) for k in ("app_chaine_id", "cote", "rang", "hektor_user_id", "nom_au_moment",
                                                   "pourcentage", "origine", "lignes")} for x in completees],
            "refus_annulee": [list(x) for x in R3["refus_annulee"]],
            "decisions": R3["decisions"],
            "membres_a_l_arrivee": {str(c): sorted(mE.get(c, [])) for c in _ch},
            "simulation_chaines": {str(a): c for a, c in chE.items() if c != ch_img.get(a)},
            "garde_vente_reglee_sql_attendue": _vr_sql,
            "parts_avant": n_rows}
    Path(arg.export_a2).write_text(json.dumps(_out, ensure_ascii=False, indent=1), encoding="utf-8")
    dire("-> %s : %d recopies, %d mises, %d completee(s), %d chaines touchees, %d pieces qui changent de chaine, garde SQL "
         "attendue %d" % (arg.export_a2, len(recopies), len(mises), len(completees), len(_ch),
                          len(_out["simulation_chaines"]), len(_vr_sql)))

if arg.csv:
    f1 = P.NOTICE / ("PROTOCOLE_REALIGNEMENT_TEMPS2_REPARTITION_A_L_ARRIVEE_PASSAGE_%d%s_2026-11-24.csv" % (arg.passage, "_AVEC_R26" if arg.r26 else ""))
    sa_ = {e["id_unique"]: e["verdict"] for e in SANS}
    with f1.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["verdict", "id_unique", "ligne_du_sheet", "sheet", "chaine_d_arrivee", "registre",
                                           "origines", "detail", "autres_lignes_de_la_chaine", "sans_le_remede"],
                           delimiter=";")
        w.writeheader()
        for e in sorted(nok_ap, key=lambda e: (e["verdict"], e["ligne_du_sheet"] or 0)):
            w.writerow(dict(e, sans_le_remede=sa_.get(e["id_unique"], "-")))
    f2 = P.NOTICE / ("PROTOCOLE_REALIGNEMENT_TEMPS2_LA_GARDE_VENTES_REGLEES_PASSAGE_%d%s_2026-11-24.csv" % (arg.passage, "_AVEC_R26" if arg.r26 else ""))
    with f2.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(garde[0].keys()) if garde else ["vide"], delimiter=";")
        w.writeheader()
        for g in garde:
            w.writerow(g)
    f3 = P.NOTICE / ("PROTOCOLE_REALIGNEMENT_TEMPS2_PARTS_SANS_LIGNE_A_L_ARRIVEE_PASSAGE_%d%s_2026-11-24.csv" % (arg.passage, "_AVEC_R26" if arg.r26 else ""))
    with f3.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["chaine_d_arrivee", "parts", "origines", "lignes dont c'est la chaine d'aujourd'hui (le gel)",
                    "leur verdict au protocole", "leur chaine d'arrivee"])
        for t, parts_, orig_ in sans_ligne:
            if "classeur" not in orig_:
                continue
            lg_ = sorted(j for j in V if source.get(j) == t)
            w.writerow([t, parts_, orig_, "+".join(lg_) or "-", "+".join(V[j]["verdict"] for j in lg_) or "-",
                        "+".join(str(cible_de.get(j)) for j in lg_) or "-"])
    dire()
    dire("-> %s" % f1)
    dire("-> %s" % f2)
    dire("-> %s" % f3)
