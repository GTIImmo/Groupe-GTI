"""Chantier classeur, ⑭ -- LES 110 LIENS « A VALIDER » CONTRE L'AUDIT DU 18/11 (et celui du 19/11).

LECTURE SEULE. Rien dans le Sheet, rien chez Hektor, rien en base : tout se joue sur des COPIES en memoire de la
photo du 19/11 20:09 (t6_photo.json), des chaines de l'etat 5 (chaines_s3.json) et du gel apres le patch V2.

Les trois questions de Frederic (20/11, fin de matinee), avant tout code :
  Q1  les 87 lignes que l'audit du 18/11 juge JUSTES peuvent-elles passer de « a valider » a « sure » ? sinon,
      pourquoi ?
  Q2  le patch V2 corrige-t-il les 2 FAUX, ou autre chose ?
  Q3  si on rebranchait cet audit sur le gel, combien de lignes de la vague 1 changeraient d'etiquette ?
Puis : les lignes qui restent VRAIMENT a lui montrer.

LA METHODE
  . le classement est celui de temps6 (`ranger`), recopie ici a l'identique ; TEMOIN 0 : il redonne l'etat 5 exporte
    par temps6 (t7_export_coupes.json) pour CHAQUE ligne du Sheet -- 0 ecart attendu ;
  . la confiance est lue LIEN PAR LIEN (pas l'union par ligne de temps6, qui garde la confiance d'un lien retire par
    V2) ; TEMOIN 1 : les deux lectures donnent le meme classement ;
  . deux avis INDEPENDANTS du gel par ligne : l'audit du 18/11 (verdict, confiance, et pour chaque transaction GARDER /
    RETIRER / DEPLACER) et l'audit V2 du 19/11 (mon propre appariement, sans le gel : verdict et certitude) ;
  . Q3 se joue en trois variantes de plus en plus larges ; pour chacune, chaque ligne de la vague 1 est comparee
    (case ET etiquette) avant / apres ; TEMOIN POSITIF : une variante semee qui DOIT faire sortir une ligne de la
    vague 1 la fait sortir.

Usage :  python -u phase2/checks/temps8_les_110_liens_et_l_audit_du_18_2026-11-20.py
Sortie : notice/TEMPS8_LES_110_LIENS_A_VALIDER_2026-11-20.md et .csv ; code 0 si les temoins sont verts, 1 sinon.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache")
PHOTO = CACHE / "t6_photo.json"
EXPORT = CACHE / "t7_export_coupes.json"
VERDICTS_18 = RACINE / "notice" / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"
GEL_CONTRE_MOI_19 = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_GEL_CONTRE_MOI_2026-11-19.csv"
MON_APPARIEMENT_19 = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_MON_APPARIEMENT_2026-11-19.csv"
OPERATIONS_V2 = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv"
DECISION_B = RACINE / "notice" / "TEMPS6_DECISION_B_LIGNES_REPORTEES_EN_VAGUE_2_PAR_G2_2026-11-20.csv"
LES_19 = RACINE / "notice" / "TEMPS7_EFFET_DES_COUPES_SUR_LA_VAGUE_1_2026-11-20.csv"
SORTIE_MD = RACINE / "notice" / "TEMPS8_LES_110_LIENS_A_VALIDER_2026-11-20.md"
SORTIE_CSV = RACINE / "notice" / "TEMPS8_LES_110_LIENS_A_VALIDER_2026-11-20.csv"
LISTE_CONFIANCE = RACINE / "notice" / "TEMPS8_LES_137_LIGNES_DU_PATCH_CONFIANCE_2026-11-20.csv"

SURE = "sûre"


def charger_temps6():
    spec = importlib.util.spec_from_file_location(
        "t6", RACINE / "phase2" / "checks" / "temps6_les_803_lignes_et_ce_qui_les_debloque_2026-11-19.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def lire_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def decisions_audit_18(r: dict) -> dict:
    """La colonne `liens` de l'audit du 18/11 : {transaction: GARDER | RETIRER | DOUTEUX | DEPLACER->x}."""
    d = {}
    for part in r["liens"].split("|"):
        m = re.match(r"\s*(\w+)\s+(\d+)\s+(GARDER|RETIRER|DOUTEUX|DEPLACER\s*->\s*(\d+))", part)
        if m:
            d[int(m.group(2))] = ("DEPLACER", int(m.group(4))) if m.group(4) else (m.group(3), None)
    return d


def a_rattacher_18(r: dict) -> set[int]:
    return {int(x) for x in re.findall(r"\b(\d{2,7})\b", r["a_rattacher"])}


def main() -> int:
    out: list[str] = []

    def dire(s=""):
        print(s, flush=True)
        out.append(s)

    echecs = []
    t6 = charger_temps6()
    P = json.loads(PHOTO.read_text(encoding="utf-8"))
    E = json.loads(EXPORT.read_text(encoding="utf-8"))
    LIG = P["lignes"]
    TX = {int(a): v for a, v in P["tx"].items()}
    S3 = {int(a): c for a, c in json.loads((CACHE / "chaines_s3.json").read_text(encoding="utf-8")).items()}
    lab3 = {int(a): v for a, v in E["lab3"].items()}
    dire("photo du Sheet et du registre : %s ; export temps6 : %s" % (P["lu_le"], E["photo_du"]))

    # ── le gel apres V2, LIEN PAR LIEN ──
    retraits, ajouts = t6.lire_patch_v2()
    lien = {(i, a): c for i, a, c in P["gel"]}
    lien_v2 = dict(lien)
    for i, a in retraits:
        lien_v2.pop((i, a), None)
    for i, a, c in ajouts:
        lien_v2[(i, a)] = c
    ops_v2 = defaultdict(list)
    for i, a in retraits:
        ops_v2[i].append("retire %d" % a)
    for i, a, c in ajouts:
        ops_v2[i].append("ajoute %d (%s)" % (a, c))

    # ── en attente : la meme regle que temps6 ──
    V18 = {r["id_unique"]: r for r in lire_csv(VERDICTS_18)}
    raison_attente = {}
    for i, r in V18.items():
        if r["question_pour_frederic"].strip():
            raison_attente[i] = "question"
        elif "INCERTAIN" in (r["verdict"] + r["correction_contre_expert"]).upper():
            raison_attente[i] = "incertain"
    raison_attente.setdefault("SHN6RKDI", "muette")
    for r in lire_csv(OPERATIONS_V2):
        if r["decision_v2"] != "GARDEE":
            raison_attente.setdefault(r["id_unique"], "sortie de V2")
    en_attente = set(raison_attente)
    V19 = {r["id_unique"]: r for r in lire_csv(GEL_CONTRE_MOI_19)}

    def gel_de(liens: dict):
        g, cf = defaultdict(set), defaultdict(set)
        for (i, a), c in liens.items():
            g[i].add(a)
            cf[i].add(c)
        return g, cf

    def liens_c5(g, i):
        ts = {a for a in g.get(i, set()) if a in S3}
        hk = {a for a in ts if not TX[a]["classeur"]}
        return hk or ts

    admis_sans_juge: set = set()     # variante E seulement : deux audits valent la designation du juge

    def ranger(g, cf) -> dict:
        """temps6.ranger(g, cf, S[3], v2_joue=True, nuit_jouee=True, c5=True), recopie a l'identique."""
        par_dossier = defaultdict(set)
        for i in g:
            for a in liens_c5(g, i):
                par_dossier[S3[a]].add(i)
        rangs = {}
        for i in LIG:
            ts = liens_c5(g, i)
            dossiers = {S3[a] for a in ts}
            if LIG[i]["row"][0].strip():
                r = "A_DEJA_REMPLIE"
            elif not ts:
                r = "SANS_LIEN"
            elif i in en_attente:
                r = "EN_ATTENTE"
            elif len(dossiers) > 1:
                r = "PLUSIEURS_DOSSIERS"
            elif par_dossier[next(iter(dossiers))] - {i}:
                r = "ETIQUETTE_PARTAGEE"
            elif cf.get(i, set()) - {SURE}:
                r = "LIEN_A_VALIDER"
            elif i in V18 and V18[i]["verdict"] not in ("JUSTE", "JUSTE_SANS_PREUVE_FORTE"):
                r = "AUDIT_NON_JUSTE"
            elif all(TX[a]["classeur"] for a in ts):
                r = "C5_SEULE"
            elif i not in admis_sans_juge and not any(i in TX[a]["designe"] for a in ts):
                r = "GEL_SEUL"
            else:
                r = "VAGUE_1"
            rangs[i] = (r, sorted(dossiers), sorted(ts))
        return rangs

    # ── TEMOIN 0 : l'etat 5 de temps6, avec l'union des confiances comme temps6 ──
    g_t6 = defaultdict(set, {k: set() for k in []})
    cf_t6 = defaultdict(set)
    for i, a, c in P["gel"]:
        g_t6[i].add(a)
        cf_t6[i].add(c)
    for i, a in retraits:
        g_t6[i].discard(a)
    for i, a, c in ajouts:
        g_t6[i].add(a)
        cf_t6[i].add(c)
    e5_t6 = ranger(g_t6, cf_t6)
    ecarts0 = [i for i in LIG if E["etat5"][i][0] != e5_t6[i][0] or E["etat5"][i][2] != e5_t6[i][2]]
    dire("TEMOIN 0 -- le classement recopie redonne l'etat 5 de temps6 : %d ecart(s) sur %d lignes (attendu 0) %s"
         % (len(ecarts0), len(LIG), ecarts0[:8]))
    if ecarts0:
        echecs.append("temoin 0")
    g_v2, cf_v2 = gel_de(lien_v2)
    e5 = ranger(g_v2, cf_v2)
    ecarts1 = [i for i in LIG if e5[i][0] != e5_t6[i][0]]
    dire("TEMOIN 1 -- la confiance lue LIEN PAR LIEN donne le meme classement : %d ecart(s) (attendu 0) %s"
         % (len(ecarts1), ecarts1[:8]))
    if ecarts1:
        echecs.append("temoin 1")

    # la vague 1 de reference : etat 5, sans les 9 de B ni les 19 du 20/11
    b9 = {r["id_unique"] for r in lire_csv(DECISION_B)}
    les19 = {r["id_unique"] for r in lire_csv(LES_19) if r["etat"] == "reference" and r["l_etiquette_changerait"] == "OUI"}
    v1 = sorted(i for i in LIG if e5[i][0] == "VAGUE_1")
    dire("VAGUE 1 -- etat 5 : %d lignes ; moins les 9 de B (%d) et les 19 du 20/11 (%d lues dans le CSV de temps7) : %d"
         % (len(v1), len(b9 & set(v1)), len(les19 & set(v1)), len(set(v1) - b9 - les19)))
    v1_ref = sorted(set(v1) - b9 - les19)

    # ── LES 110 ──
    lav = sorted(i for i in LIG if e5[i][0] == "LIEN_A_VALIDER")
    dire()
    dire("LES LIGNES « LIEN A VALIDER » a l'etat 5 : %d (attendu 110)" % len(lav))
    if len(lav) != 110:
        echecs.append("110 : %d" % len(lav))
    conf_ligne = {}
    for i in lav:
        conf_ligne[i] = Counter(c for (j, a), c in lien_v2.items() if j == i and a in S3)
    dire("   la confiance de leurs liens : %s"
         % dict(Counter(" + ".join(sorted(c)) for c in conf_ligne.values())))
    dire("   ⚠ « bonne » = un lien AJOUTE par le patch V2 (il ecrit « bonne », pas « sure ») -- la case le compte comme"
         " « a valider »")

    rows = []
    for i in lav:
        r18, r19 = V18.get(i), V19.get(i)
        ts = set(e5[i][2])
        tous = {a for (j, a) in lien_v2 if j == i}
        d18 = decisions_audit_18(r18) if r18 else {}
        garder = {a for a, (k, _) in d18.items() if k == "GARDER"}
        autres = {a: k for a, (k, _) in d18.items() if k != "GARDER"}
        rows.append({
            "id_unique": i, "ts": ts, "tous": tous,
            "conf": dict(Counter(c for (j, a), c in lien_v2.items() if j == i)),
            "v18": r18["verdict"] if r18 else "JAMAIS_VUE", "c18": r18["confiance"] if r18 else "",
            "garder18": garder, "autres18": autres, "rattacher18": a_rattacher_18(r18) if r18 else set(),
            "raison18": (r18["raison"] if r18 else "")[:400], "preuve18": (r18["preuve"] if r18 else "")[:400],
            "v19": r19["mon_verdict_sur_le_gel"] if r19 else "", "c19": r19["ma_certitude"] if r19 else "",
            "drap19": r19["mes_drapeaux"] if r19 else "", "etage": r19["etage_gel"] if r19 else "",
            "ops_v2": ops_v2.get(i, []),
        })

    # ── Q1 : les JUSTES ──
    dire()
    dire("Q1 -- LES LIGNES QUE L'AUDIT DU 18/11 JUGE « JUSTE »")
    justes = [x for x in rows if x["v18"] == "JUSTE"]
    dire("   %d lignes ; confiance de l'audit : %s" % (len(justes), dict(Counter(x["c18"] for x in justes))))
    for x in justes:
        pb = []
        if x["autres18"]:
            pb.append("l'audit RETIRE ou DEPLACE une piece : %s" % x["autres18"])
        hk = {a for a in x["tous"] if a in TX and not TX[a]["classeur"]}
        if x["garder18"] != hk:
            pb.append("les liens d'aujourd'hui (%s) != ceux que l'audit garde (%s)" % (sorted(hk), sorted(x["garder18"])))
        if x["v19"] != "JUSTE":
            pb.append("l'audit du 19/11 dit %s (%s)" % (x["v19"] or "rien", x["c19"]))
        elif x["c19"] != "CERTAINE":
            pb.append("l'audit du 19/11 dit JUSTE mais %s" % x["c19"])
        if x["ops_v2"]:
            pb.append("le patch V2 touche la ligne : %s" % x["ops_v2"])
        x["pb"] = pb
    nets = [x for x in justes if not x["pb"]]
    dire("   ⭐ CONFIRMEES PAR LES DEUX AUDITS, liens identiques a ceux que le 18/11 garde, rien dans V2 : %d" % len(nets))
    dire("      dont confiance du 18/11 « certaine » : %d, « forte » : %d"
         % (sum(x["c18"] == "certaine" for x in nets), sum(x["c18"] == "forte" for x in nets)))
    dire("      l'etage du gel qui les avait trouvees : %s" % dict(Counter(x["etage"] for x in nets)))
    for x in justes:
        if x["pb"]:
            dire("   ⚠ %s (%s/%s) : %s" % (x["id_unique"], x["v18"], x["c18"], " ; ".join(x["pb"])))

    # ── Q2 : les 2 FAUX, et ce que fait le patch V2 ──
    dire()
    dire("Q2 -- LES FAUX, ET CE QUE FAIT LE PATCH V2")
    for x in rows:
        if x["v18"] == "FAUX":
            dire("   %s : liens d'aujourd'hui %s (%s) ; audit 18/11 : %s, a rattacher %s ; audit 19/11 : %s (%s) ;"
                 " V2 : %s" % (x["id_unique"], sorted(x["tous"]), x["conf"], {a: k for a, k in x["autres18"].items()},
                               sorted(x["rattacher18"]), x["v19"], x["c19"], x["ops_v2"] or "RIEN"))
            dire("      raison 18/11 : %s" % x["raison18"][:300])
    lignes_v2 = sorted(ops_v2)
    par_v = Counter(V18[i]["verdict"] if i in V18 else "hors audit du 18/11" for i in lignes_v2)
    dire("   le patch V2 touche %d lignes ; leur verdict du 18/11 : %s" % (len(lignes_v2), dict(par_v)))
    dire("   leur case a l'etat 5 : %s" % dict(Counter(e5[i][0] for i in lignes_v2)))
    faux_v18_tous = sorted(i for i, r in V18.items() if r["verdict"] == "FAUX")
    dire("   les %d FAUX de tout l'audit du 18/11 : V2 en touche %d ; case a l'etat 5 : %s"
         % (len(faux_v18_tous), sum(1 for i in faux_v18_tous if i in ops_v2),
            dict(Counter(e5[i][0] if i in e5 else "?" for i in faux_v18_tous))))

    # ── Q3 : rebrancher l'audit sur le gel, sur copie ──
    dire()
    dire("Q3 -- REBRANCHER L'AUDIT SUR LE GEL (copie) : la vague 1 de reference = %d lignes" % len(v1_ref))

    def comparer(nom, liens_mod):
        g, cf = gel_de(liens_mod)
        rr = ranger(g, cf)
        change_lab, sortent = [], []
        for i in v1_ref:
            if rr[i][0] != "VAGUE_1":
                sortent.append((i, rr[i][0]))
            elif {lab3.get(a) for a in rr[i][2]} != {lab3.get(a) for a in e5[i][2]}:
                change_lab.append(i)
        entrent = sorted(i for i in LIG if rr[i][0] == "VAGUE_1" and e5[i][0] != "VAGUE_1")
        dire("   %s" % nom)
        dire("      lignes de la vague 1 dont l'ETIQUETTE changerait : %d %s" % (len(change_lab), change_lab[:10]))
        dire("      lignes de la vague 1 qui en SORTIRAIENT : %d %s" % (len(sortent), sortent[:10]))
        dire("      lignes qui ENTRERAIENT en vague 1 : %d" % len(entrent))
        dire("      les 110 apres : %s" % dict(Counter(rr[i][0] for i in lav)))
        return rr, change_lab, sortent, entrent

    va = dict(lien_v2)
    for x in nets:
        for (j, a) in list(va):
            if j == x["id_unique"]:
                va[(j, a)] = SURE
    rr_a, cl_a, so_a, en_a = comparer("A  les %d JUSTES confirmees passent « sure »" % len(nets), va)

    vb = dict(va)
    for x in justes:
        if x["pb"] and not x["autres18"]:
            for (j, a) in list(vb):
                if j == x["id_unique"]:
                    vb[(j, a)] = SURE
    rr_b, cl_b, so_b, en_b = comparer("B  + les %d autres JUSTES (celles qui ont une reserve)" % sum(1 for x in justes if x["pb"]), vb)

    vc = dict(vb)
    for x in rows:
        if x["v18"] in ("FAUX", "A_RATTACHER", "PARTIEL", "JUSTE_SANS_PREUVE_FORTE") or x["autres18"]:
            i = x["id_unique"]
            d18 = decisions_audit_18(V18[i])
            for a, (k, cible) in d18.items():
                if k == "RETIRER":
                    vc.pop((i, a), None)
                elif k == "DEPLACER":
                    vc.pop((i, a), None)
                    vc[(i, cible)] = SURE
                elif k == "GARDER" and (i, a) in vc:
                    vc[(i, a)] = SURE
            for a in x["rattacher18"]:
                if a in TX:
                    vc[(i, a)] = SURE
    rr_c, cl_c, so_c, en_c = comparer("C  + TOUT ce que l'audit du 18/11 dit des autres (retirer, deplacer, rattacher)", vc)

    # D : la plus large -- partout ou les DEUX audits disent la meme chose que le gel apres V2
    MA = {r["id_unique"]: r for r in lire_csv(MON_APPARIEMENT_19)}

    def moi_19(i):
        r = MA.get(i)
        if not r:
            return None
        return {int(x) for k in ("offre", "compromis", "vente") for x in re.findall(r"\d+", r[k])}

    def corrige_18(i):
        r = V18.get(i)
        if not r:
            return None
        d = decisions_audit_18(r)
        s_ = ({a for a, (k, _) in d.items() if k == "GARDER"} | {c for a, (k, c) in d.items() if k == "DEPLACER"}
              | a_rattacher_18(r))
        return {a for a in s_ if a in TX and not TX[a]["classeur"]}

    accord = {}
    for i in LIG:
        if e5[i][0] not in ("LIEN_A_VALIDER", "AUDIT_NON_JUSTE"):
            continue
        hk = {a for (j, a) in lien_v2 if j == i and a in TX and not TX[a]["classeur"]}
        m, c18 = moi_19(i), corrige_18(i)
        cert = V19.get(i, {}).get("ma_certitude", "")
        if m is not None and m == hk and (c18 is None or c18 == hk) and hk:
            accord[i] = "les deux audits" if c18 is not None else "l'audit du 19/11 seul (%s)" % cert
    dire("   D  la plus large : les lignes « a valider » ou « audit non juste » dont les liens apres V2 sont EXACTEMENT"
         " ceux des deux audits : %d (%s)" % (len(accord), dict(Counter(accord.values()))))
    dire("      leur case a l'etat 5 : %s" % dict(Counter(e5[i][0] for i in accord)))
    vd = dict(lien_v2)
    for (j, a) in list(vd):
        if j in accord:
            vd[(j, a)] = SURE
    V18_sauve = {i: V18[i] for i in accord if i in V18}
    for i in V18_sauve:
        V18[i] = dict(V18[i], verdict="JUSTE")
    rr_d, cl_d, so_d, en_d = comparer("D  (le verdict du 18/11 compte comme JUSTE quand V2 l'a deja corrige a l'identique)", vd)
    for i, r in V18_sauve.items():
        V18[i] = r
    dire("      ⚠ « audit du 19/11 seul » = jamais vue le 18/11 : UN avis independant, pas deux")
    for i in sorted(accord, key=lambda i: (rr_d[i][0], i)):
        if rr_d[i][0] != "VAGUE_1":
            dire("      reste hors vague 1 : %s (etat 5 %s) -> %s ; liens %s ; juge : %s"
                 % (i, e5[i][0], rr_d[i][0], rr_d[i][2],
                    " | ".join("%d:%s" % (a, " ".join(TX[a]["designe"]) or "personne") for a in rr_d[i][2])))

    # E : D + « gel seul » leve quand les deux audits retrouvent la ligne (le juge du Sheet s'appuie sur le mandat,
    #     que Hektor recycle : il ne designe pas ces lignes, les audits les retrouvent par les dates au jour pres)
    for i in V18_sauve:
        V18[i] = dict(V18[i], verdict="JUSTE")
    admis_sans_juge |= set(accord)
    rr_e, cl_e, so_e, en_e = comparer("E  D + « gel seul » leve pour ces %d lignes (deux audits valent le juge)" % len(accord), vd)
    admis_sans_juge.clear()
    for i, r in V18_sauve.items():
        V18[i] = r

    # TEMOIN POSITIF : semer dans le dossier d'une ligne de la vague 1 un lien d'une des 110
    cible = v1_ref[0]
    a_cible = e5[cible][2][0]
    vt = dict(vc)
    vt[(lav[0], a_cible)] = SURE
    g, cf = gel_de(vt)
    rt = ranger(g, cf)
    vu = rt[cible][0] != "VAGUE_1"
    dire("   TEMOIN POSITIF -- un lien seme de %s vers la transaction %d de %s (vague 1) : %s devient %s -> %s"
         % (lav[0], a_cible, cible, cible, rt[cible][0], "VU" if vu else "⛔ PAS VU"))
    if not vu:
        echecs.append("temoin positif Q3")

    # ── LE RESTE : ce qu'il faut VRAIMENT lui montrer ──
    dire()
    reste = [x for x in rows if x not in nets]
    dire("LE RESTE -- %d lignes sur %d (les autres sont confirmees par deux audits independants)" % (len(reste), len(rows)))
    dire("   par verdict du 18/11 : %s" % dict(Counter(x["v18"] for x in reste)))
    for x in reste:
        dire("   %s %-24s 18/11 %s/%s · 19/11 %s/%s · liens %s %s · V2 %s · apres C : %s"
             % (x["id_unique"], LIG[x["id_unique"]]["row"][27][:24],
                x["v18"], x["c18"], x["v19"], x["c19"], sorted(x["tous"]), x["conf"], x["ops_v2"] or "-",
                rr_c[x["id_unique"]][0]))

    # ── LA LISTE DU PATCH « CONFIANCE » (accorde le 20/11 : « les 97 : OUI, colle-les ; les 40 autres apres V2 » ;
    #    « NKDC0I1M : garde-la ») -- A = n'attend rien ; B = ses liens n'existent qu'apres V2 ──
    patch = sorted(set(accord) | {"NKDC0I1M"})
    with LISTE_CONFIANCE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "partie", "case_etat_5", "avis", "liens_hektor_attendus_apres_v2", "tous_les_liens_apres_v2"])
        for i in patch:
            hk = sorted(a for (j, a) in lien_v2 if j == i and a in TX and not TX[a]["classeur"])
            tous = sorted(a for (j, a) in lien_v2 if j == i)
            w.writerow([i, "B" if i in ops_v2 else "A", e5[i][0], accord.get(i, "les deux audits, sauf l'offre sans date 27741 (garde-la, 20/11)"),
                        " ".join(map(str, hk)), " ".join(map(str, tous))])
    dire("   LISTE DU PATCH « CONFIANCE » : %d lignes (A %d, B %d) -> %s"
         % (len(patch), sum(1 for i in patch if i not in ops_v2), sum(1 for i in patch if i in ops_v2), LISTE_CONFIANCE.name))

    # ── LE CSV ──
    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "ligne_du_sheet", "acquereur", "etat_actuel", "nos_liens", "confiance_des_liens",
                    "audit_18_11", "confiance_18_11", "audit_18_11_garde", "audit_18_11_autre", "audit_18_11_a_rattacher",
                    "audit_19_11", "certitude_19_11", "drapeaux_19_11", "etage_du_gel", "patch_v2",
                    "confirmee_par_les_deux_audits", "reserve", "case_apres_A", "case_apres_C", "case_apres_D", "raison_18_11"])
        for x in rows:
            i = x["id_unique"]
            row = LIG[i]["row"]
            w.writerow([i, LIG[i]["num"], row[27] if len(row) > 27 else "", row[17] if len(row) > 17 else "",
                        " ".join(map(str, sorted(x["tous"]))), " ".join("%s:%d" % kv for kv in sorted(x["conf"].items())),
                        x["v18"], x["c18"], " ".join(map(str, sorted(x["garder18"]))),
                        " ".join("%d:%s" % kv for kv in sorted(x["autres18"].items())),
                        " ".join(map(str, sorted(x["rattacher18"]))), x["v19"], x["c19"], x["drap19"], x["etage"],
                        " | ".join(x["ops_v2"]), "oui" if x in nets else "non", " ; ".join(x.get("pb", [])),
                        rr_a[i][0], rr_c[i][0], rr_d[i][0], x["raison18"]])
    dire()
    dire("CSV : %s (%d lignes)" % (SORTIE_CSV.name, len(rows)))
    dire("VERDICT DES TEMOINS : %s" % ("VERTS" if not echecs else "⛔ " + " ; ".join(echecs)))
    SORTIE_MD.write_text("# Les 110 liens « a valider » contre l'audit du 18/11 (genere par %s, %s)\n\n```\n%s\n```\n"
                         % (Path(__file__).name, datetime.now().isoformat(timespec="minutes"), "\n".join(out)),
                         encoding="utf-8")
    return 0 if not echecs else 1


if __name__ == "__main__":
    sys.exit(main())
