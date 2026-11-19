#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LES LIGNES DU SHEET QUI N'ENTRENT PAS EN VAGUE 1 -- et CE QUI DEBLOQUE CHACUNE.   19/11/2026 (soir)

Deux questions de Frederic (19/11, soir) :
  2. « Avant la vague 1b je veux la liste des 803 non ecrites avec leur case, dans un fichier que je
     peux ouvrir. »
  3. « Sur les 296 etiquette partagee et les 224 plusieurs dossiers : combien se regleraient sans
     scission ? Je veux savoir combien restent vraiment bloquees sur une decision de ma part. »

DECOUPE EN DEUX ETAPES (sa regle du 19/11 : jamais plus de dix minutes d'un bloc, chaque etape ecrit
son resultat sur le disque, dans C:\Hektor\chantier_classeur_q6_cache\, hors du depot) :

    .venv\Scripts\python.exe -X utf8 -u phase2\checks\temps6_les_803_lignes_et_ce_qui_les_debloque_2026-11-19.py photo
    .venv\Scripts\python.exe -X utf8 -u phase2\checks\temps6_les_803_lignes_et_ce_qui_les_debloque_2026-11-19.py classer

    photo    lit le Sheet (un GET) et le registre (mode=ro), fait tourner le juge de ⑤ sur chaque
             transaction, et ecrit t6_photo.json
    classer  local, sans reseau : relit la photo, les chaines des scenarios de ⑥ (chaines_s1/2/3.json)
             et le patch V2 ; ecrit le CSV, le classeur .xlsx et le compte

⛔ N'ECRIT RIEN, NI DANS LE SHEET, NI EN BASE, NI CHEZ HEKTOR.

TEMOIN : la photo, rangee comme le fait le script de ⑧, doit redonner EXACTEMENT les cases du CSV de ⑧
(aujourd'hui ET apres) -- sinon le Sheet ou la base ont bouge depuis, et chaque ligne qui differe est
nommee.

LES COUCHES, dans l'ordre -- une ligne bloquee prend la PREMIERE qui la libere :
  1 la nuit des 10 menages           decidee le 19/11, joue cette nuit
  2 + le patch V2 du gel             relu (⑦), attend ton « vas-y »
  3 + la regle E                     codee eteinte, attend ton allumage
  4 + les 8 lignes de 5.6            tu les lis
  5 + le choix C5 « a l'export »     deja pose (⑥) : une creation du Sheet ne decide jamais de
                                     l'etiquette d'une ligne ; on prend celle des transactions de Hektor
  -- au-dela, sur l'etat 5, le juge de ⑤ (colonnes independantes S, T, V/W/X, AB, AF, C) regarde
     chaque GROUPE (les lignes et les dossiers relies entre eux) :
  6 RELECTURE DU GEL                 les liens que le juge ne voit pas tombent, et la ligne se retrouve
                                     seule sur un seul dossier -> un patch du gel (sans scission)
  7 REUNIR                           une ligne SEULE tient plusieurs dossiers -> des lignes de
                                     rattachement (ta decision, ligne a ligne ; sans scission)
  8 MEME AFFAIRE, PLUSIEURS LIGNES   toutes les lignes du groupe designent la meme transaction ou le
                                     meme acquereur : un doublon du classeur. Sans scission -- MAIS le
                                     point ⑤ du critere de fin (0 UUID sur deux lignes) l'interdit
  9 MELANGE -> SCISSION              des lignes d'acquereurs DIFFERENTS designent des transactions
                                     differentes du groupe : il faut couper un dossier
 10 NON TRANCHE                      le juge ne voit pas une des lignes du groupe

Sortie : 0 fait . 2 un temoin a echoue . 3 une etape manque.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
CACHE = RACINE.parent / "chantier_classeur_q6_cache"
PHOTO = CACHE / "t6_photo.json"
PATCH_V2 = RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19.sql"
VERDICTS = RACINE / "notice" / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"
OPERATIONS = RACINE / "notice" / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv"
Q8 = RACINE / "notice" / "TEMPS5_Q8_LES_LIGNES_DU_SHEET_ET_LEUR_VAGUE_2026-11-19.csv"
SORTIE_CSV = RACINE / "notice" / "TEMPS6_LES_803_LIGNES_NON_ECRITES_ET_CE_QUI_LES_DEBLOQUE_2026-11-19.csv"
SORTIE_XLSX = SORTIE_CSV.with_suffix(".xlsx")
SORTIE_MD = RACINE / "notice" / "TEMPS6_SANS_SCISSION_LE_COMPTE_2026-11-19.md"
AL, AB = 37, 27

COUCHES = {
    1: "1 la nuit des 10 menages (decidee, joue cette nuit)",
    2: "2 le patch V2 du gel (ton « vas-y »)",
    3: "3 la regle E (ton allumage)",
    4: "4 les 8 lignes de 5.6 (ta lecture)",
    5: "5 le choix C5 « a l'export » (question posee en ⑥, attend ta reponse)",
    6: "6 relecture du gel (un patch a valider, sans scission)",
    7: "7 reunir (lignes de rattachement, ta decision ligne a ligne, sans scission)",
    8: "8 meme affaire sur plusieurs lignes (doublon du classeur ; contre le point ⑤)",
    9: "9 melange -> SCISSION",
    10: "10 non tranche (le juge ne voit pas une des lignes)",
}


def ecrire_json(chemin: Path, obj) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(chemin.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(chemin)


def lire_json(chemin: Path):
    return json.loads(chemin.read_text(encoding="utf-8"))


def charger_juge():
    spec = importlib.util.spec_from_file_location(
        "juge_q5", RACINE / "phase2" / "checks" / "temps5_q5_les_48_a_juger_par_le_classeur_2026-11-19.py")
    juge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(juge)
    return juge


# ─────────────────────────────────────────── ETAPE 1 : LA PHOTO ───────────────────────────────────────────
def etape_photo() -> int:
    t0 = time.time()
    juge = charger_juge()
    J = juge.preparer_juge()                       # lit le Sheet (GET) et le registre (mode=ro)
    tx, designe, src = J["tx"], J["designe"], J["src"]
    entete, lignes = juge.ac.lire_classeur()       # la colonne A et les colonnes lisibles
    print("le juge est pret (%.0f s) ; Sheet relu : %d lignes" % (time.time() - t0, len(lignes)), flush=True)
    assert entete[0] == "affair_uuid" and entete[AL] == "ID Unique", "l'en-tete du Sheet a bouge"
    rows = {}
    for num, l in lignes:
        l = [str(x) for x in list(l)] + [""] * (len(entete) - len(l))
        rows[l[AL].strip()] = {"num": num, "row": l[:len(entete)],
                               "noms_ab": sorted(juge.ac.mots_propres(l[AB]))}
    sortie = {}
    for k, (a, t) in enumerate(tx.items()):
        ids, pourquoi = designe(a)
        sortie[str(a)] = {"bien": t["bien"], "genre": t["genre"], "etat": t["etat"], "classeur": t["classeur"],
                          "noms": sorted(t["noms"]), "montant": t["montant"], "chaine": t["chaine"],
                          "uuid": t["uuid"], "designe": [r["id"] for r in ids], "pourquoi": pourquoi}
        if k % 5000 == 0:
            print("   juge : %d / %d transactions (%.0f s)" % (k, len(tx), time.time() - t0), flush=True)
    gel = [[i, a, c] for i, a, c in src.execute("SELECT id_unique, app_affaire_id, confiance FROM app_classeur_lien")]
    ecrire_json(PHOTO, {"lu_le": datetime.now().isoformat(timespec="seconds"), "entete": entete,
                        "lignes": rows, "tx": sortie, "gel": gel})
    print("ECRIT : %s -- %d lignes du Sheet, %d transactions, %d liens du gel (%.0f s)"
          % (PHOTO, len(rows), len(sortie), len(gel), time.time() - t0), flush=True)
    return 0


# ────────────────────────────────────────── ETAPE 2 : LE CLASSEMENT ──────────────────────────────────────────
def lire_patch_v2():
    texte = PATCH_V2.read_text(encoding="utf-8")
    b3 = texte.split("-- ── ③ RETIRER")[1].split("-- ── ④ AJOUTER")[0]
    b4 = texte.split("-- ── ④ AJOUTER")[1].split("-- ── ⑤ LE CONTROLE")[0]
    retraits = {(i, int(a)) for i, a in re.findall(r"\('([^']+)',\s*(\d+),\s*'\w+'\)", b3)}
    ajouts = [(i, int(a), c) for a, c, i in re.findall(r"\(\d+,\s*(\d+),\s*'\w+',\s*'([^']+)',.*?'([^']+)'\)", b4)]
    return retraits, ajouts


def etape_classer() -> int:
    if not PHOTO.exists():
        print("⛔ la photo manque : lancer d'abord « photo » (code 3)", flush=True)
        return 3
    for n in (1, 2, 3):
        if not (CACHE / ("chaines_s%d.json" % n)).exists():
            print("⛔ chaines_s%d.json manque : lancer « rejeu %d » de temps5_q6 (code 3)" % (n, n), flush=True)
            return 3
    echecs = []
    P = lire_json(PHOTO)
    print("photo du %s : %d lignes, %d transactions, %d liens" % (P["lu_le"], len(P["lignes"]), len(P["tx"]),
                                                                    len(P["gel"])), flush=True)
    entete, LIG = P["entete"], P["lignes"]
    TX = {int(a): v for a, v in P["tx"].items()}
    gel, conf = defaultdict(set), defaultdict(set)
    for i, a, c in P["gel"]:
        gel[i].add(a)
        conf[i].add(c)
    retraits, ajouts = lire_patch_v2()
    touchees_v2 = {i for i, _ in retraits} | {i for i, _, _ in ajouts}
    gel_v2 = defaultdict(set, {k: set(v) for k, v in gel.items()})
    conf_v2 = defaultdict(set, {k: set(v) for k, v in conf.items()})
    for i, a in retraits:
        gel_v2[i].discard(a)
    for i, a, c in ajouts:
        gel_v2[i].add(a)
        conf_v2[i].add(c)
    print("patch V2 : %d retraits, %d ajouts, %d lignes touchees (attendu 45 / 78 / 65)"
          % (len(retraits), len(ajouts), len(touchees_v2)), flush=True)
    if (len(retraits), len(ajouts), len(touchees_v2)) != (45, 78, 65):
        echecs.append("lecture du patch V2")

    # les lignes en attente de decision, et POURQUOI
    verdicts, raison_attente = {}, {}
    with VERDICTS.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            verdicts[r["id_unique"]] = r
            if r["question_pour_frederic"].strip():
                raison_attente[r["id_unique"]] = "ta question : " + r["question_pour_frederic"].strip()
            elif "INCERTAIN" in (r["verdict"] + r["correction_contre_expert"]).upper():
                raison_attente[r["id_unique"]] = "audit du 18/11 INCERTAIN : " + r["verdict"]
    raison_attente.setdefault("SHN6RKDI", "la muette SHN6RKDI (compromis annule sans date, 26613)")
    with OPERATIONS.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["decision_v2"] != "GARDEE":
                raison_attente.setdefault(r["id_unique"], "operation sortie du patch V2 (%s) : %s"
                                          % (r["decision_v2"], r["raison"][:160]))
    en_attente = set(raison_attente)

    base = {a: t["chaine"] for a, t in TX.items()}
    S = {n: {int(a): c for a, c in lire_json(CACHE / ("chaines_s%d.json" % n)).items()} for n in (1, 2, 3)}
    cette_nuit = {a for a in base if S[1].get(a) != base[a]}
    print("transactions qui changent de dossier cette nuit : %d (attendu 10)" % len(cette_nuit), flush=True)
    if len(cette_nuit) != 10:
        echecs.append("cette nuit : %d" % len(cette_nuit))
    designe_par_ligne = defaultdict(set)
    for a, t in TX.items():
        for i in t["designe"]:
            designe_par_ligne[i].add(a)

    def liens(g, ch, i, c5):
        ts = {a for a in g.get(i, set()) if a in ch}
        if c5:
            hk = {a for a in ts if not TX[a]["classeur"]}
            if hk:
                ts = hk
        return ts

    def ranger(g, cf, ch, v2_joue, nuit_jouee, c5=False) -> dict:
        """La meme regle que ⑧ (temps5_q8, ranger), avec l'option C5 « a l'export »."""
        lignes_du_dossier = defaultdict(set)
        for i in g:
            for a in liens(g, ch, i, c5):
                lignes_du_dossier[ch[a]].add(i)
        rangs = {}
        for i in LIG:
            ts = liens(g, ch, i, c5)
            dossiers = {ch[a] for a in ts}
            if LIG[i]["row"][0].strip():
                r = "A_DEJA_REMPLIE"
            elif not ts:
                r = "SANS_LIEN"
            elif i in en_attente:
                r = "EN_ATTENTE"
            elif not v2_joue and i in touchees_v2:
                r = "PATCH_V2"
            elif not nuit_jouee and ts & cette_nuit:
                r = "CETTE_NUIT"
            elif len(dossiers) > 1:
                r = "PLUSIEURS_DOSSIERS"
            elif lignes_du_dossier[next(iter(dossiers))] - {i}:
                r = "ETIQUETTE_PARTAGEE"
            elif cf.get(i, set()) - {"sûre"}:
                r = "LIEN_A_VALIDER"
            elif i in verdicts and verdicts[i]["verdict"] not in ("JUSTE", "JUSTE_SANS_PREUVE_FORTE"):
                r = "AUDIT_NON_JUSTE"
            elif all(TX[a]["classeur"] for a in ts):
                r = "C5_SEULE"
            elif not any(i in TX[a]["designe"] for a in ts):
                r = "GEL_SEUL"
            else:
                r = "VAGUE_1"
            rangs[i] = (r, sorted(dossiers), sorted(ts))
        return rangs

    # ── TEMOIN : la photo redonne les cases de ⑧ ──
    q8 = {}
    with Q8.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            q8[r["id_unique"]] = r
    auj = ranger(gel, conf, base, False, False)
    apr = ranger(gel_v2, conf_v2, S[1], True, True)
    diff = [i for i in set(q8) | set(auj) if i not in q8 or i not in auj
            or q8[i]["case_aujourd_hui"] != auj[i][0] or q8[i]["case_apres"] != apr[i][0]]
    print("TEMOIN : la photo rangee comme ⑧ -- %d ligne(s) differente(s) du CSV de ⑧ (attendu 0) %s"
          % (len(diff), sorted(diff)[:10]), flush=True)
    if diff:
        echecs.append("photo != ⑧ : %d lignes" % len(diff))

    # ── LES COUCHES 1 a 5 ──
    etats = {
        1: ranger(gel, conf, S[1], False, True),
        2: ranger(gel_v2, conf_v2, S[1], True, True),
        3: ranger(gel_v2, conf_v2, S[2], True, True),
        4: ranger(gel_v2, conf_v2, S[3], True, True),
        5: ranger(gel_v2, conf_v2, S[3], True, True, c5=True),
    }

    def structure(g, ch, c5):
        lignes_du_dossier = defaultdict(set)
        for i in g:
            for a in liens(g, ch, i, c5):
                lignes_du_dossier[ch[a]].add(i)
        st = {}
        for i in LIG:
            ds = {ch[a] for a in liens(g, ch, i, c5)}
            st[i] = ("VIDE" if not ds else "MULTI" if len(ds) > 1 else
                     "PARTAGEE" if lignes_du_dossier[next(iter(ds))] - {i} else "SEULE")
        return st

    structs = {0: structure(gel, base, False), 1: structure(gel, S[1], False), 2: structure(gel_v2, S[1], False),
               3: structure(gel_v2, S[2], False), 4: structure(gel_v2, S[3], False),
               5: structure(gel_v2, S[3], True)}

    # ── AU-DELA DE 5 : le juge regarde chaque GROUPE sur l'etat 5 ──
    g5, ch5 = gel_v2, S[3]
    membres = defaultdict(set)
    for a, c in ch5.items():
        membres[c].add(a)
    E = {}
    for i in set(g5) | set(LIG):
        E[i] = defaultdict(set)
        for a in liens(g5, ch5, i, True):
            E[i][ch5[a]].add(a)

    def designees_sures(i):
        """Les transactions que la ligne designe, SANS les ambigues : deux transactions du meme genre sur le
        meme bien, d'acheteurs DIFFERENTS, designees par la meme ligne ne prouvent rien ni pour l'une ni pour
        l'autre (lu a la main le 19/11 au soir : 9CQ325R6 RIVATON designe les offres FAISANDIER et FAUDON,
        le meme jour au meme prix). Deux compromis successifs du MEME acheteur (MACHABERT) restent."""
        par_bg = defaultdict(set)
        for a in designe_par_ligne.get(i, set()):
            par_bg[(TX[a]["bien"], TX[a]["genre"])].add(a)
        sures = set()
        for aa in par_bg.values():
            if len(aa) == 1 or set.intersection(*(set(TX[a]["noms"]) for a in aa)):
                sures |= aa
        return sures

    DS = {i: designees_sures(i) for i in set(g5) | set(LIG)}

    def tient(i, d):
        return any(ch5.get(a) == d and not TX[a]["classeur"] for a in DS[i])

    E2, aucun_tenu = {}, set()
    for i, ds in E.items():
        tenus = {d for d in ds if tient(i, d)}
        if ds and not tenus:
            aucun_tenu.add(i)
        E2[i] = tenus or set(ds)
    # les groupes : lignes et dossiers relies par les liens que le juge voit
    parent = {}

    def trouve(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def unir(x, y):
        parent[trouve(x)] = trouve(y)

    for i, ds in E2.items():
        for d in ds:
            unir(("L", i), ("D", d))
    groupes = defaultdict(lambda: {"lignes": set(), "dossiers": set()})
    for i, ds in E2.items():
        if ds:
            k = trouve(("L", i))
            groupes[k]["lignes"].add(i)
            groupes[k]["dossiers"] |= ds

    def noms_ligne(i):
        return set(LIG[i]["noms_ab"]) if i in LIG else set()

    verdict_groupe = {}
    for k, gr in groupes.items():
        ls, ds = gr["lignes"], gr["dossiers"]
        if len(ls) == 1:
            seule = next(iter(ls))
            verdict_groupe[k] = 6 if len(ds) == 1 else (10 if seule in aucun_tenu else 7)
            continue
        # ⚠ LA MEME AFFAIRE SE JUGE PAR L'ACQUEREUR DU SHEET (colonne AB), PAS par une transaction designee
        #   en commun : le defaut de Hektor (le compromis du suivant au nom du PRECEDENT) fait designer CE
        #   compromis par les deux lignes -- l'une par sa date, l'autre par le nom (lu a la main le 19/11 au
        #   soir : N1CUULMN MARCHEPOIL et 3308P0UX VIALLARD, 50G3GV2U COUCHOUD et Z624CX4D PARADISUS).
        p2 = {i: i for i in ls}

        def t2(x):
            while p2[x] != x:
                x = p2[x]
            return x
        lst = sorted(ls)
        for x_i, x in enumerate(lst):
            for y in lst[x_i + 1:]:
                if noms_ligne(x) & noms_ligne(y):
                    p2[t2(x)] = t2(y)
        connues_vues = {t2(i) for i in ls if i not in aucun_tenu and noms_ligne(i)}
        if len({t2(i) for i in ls}) == 1:
            verdict_groupe[k] = 8
        elif len(connues_vues) >= 2:
            verdict_groupe[k] = 9
        else:
            verdict_groupe[k] = 10

    # ── LES MELANGES : combien portent la SIGNATURE du defaut de Hektor ? ──
    #   une ligne « Annulee » (l'acheteur qui a renonce) + une ligne VIVANTE, et une transaction NON annulee
    #   du groupe (compromis actif, offre acceptee, vente) au nom de l'annulee SANS celui de la vivante :
    #   le contact de l'acheteur precedent reste sur le compromis du suivant, et la regle D colle tout.
    i_etat = entete.index("Etat Actuel")
    signature = {}
    for k, gr in groupes.items():
        if verdict_groupe.get(k) != 9:
            continue
        annulees = [i for i in gr["lignes"] if i in LIG and LIG[i]["row"][i_etat].strip().lower().startswith("annul")]
        vivantes = [i for i in gr["lignes"] if i in LIG and i not in annulees]
        n_ann = set().union(*(noms_ligne(i) for i in annulees)) if annulees else set()
        n_viv = set().union(*(noms_ligne(i) for i in vivantes)) if vivantes else set()
        porte = [a for d in gr["dossiers"] for a in membres[d]
                 if TX[a]["etat"] not in ("cancelled", "refused") and set(TX[a]["noms"]) & n_ann
                 and not set(TX[a]["noms"]) & n_viv]
        signature[k] = ("SIGNATURE DU DEFAUT" if annulees and vivantes and porte else
                        "annulee + vivante, sans transaction au nom de l'annulee" if annulees and vivantes else
                        "que des lignes annulees" if annulees else "que des lignes vivantes")

    # ── LA COUCHE DE CHAQUE LIGNE ──
    def couche(i):
        """La premiere couche qui sort la ligne de PLUSIEURS DOSSIERS / ETIQUETTE PARTAGEE."""
        for n in (1, 2, 3, 4, 5):
            if structs[n][i] in ("SEULE", "VIDE"):
                return n, structs[n][i]
        k = trouve(("L", i))
        if k not in verdict_groupe:
            return 10, "?"
        return verdict_groupe[k], structs[5][i]

    les_520 = [i for i in LIG if auj[i][0] in ("PLUSIEURS_DOSSIERS", "ETIQUETTE_PARTAGEE")]
    res = {i: couche(i) for i in les_520}
    compte = defaultdict(Counter)
    for i in les_520:
        compte[auj[i][0]][res[i][0]] += 1
    lignes_md = ["LES %d LIGNES « PLUSIEURS DOSSIERS » ET « ETIQUETTE PARTAGEE » D'AUJOURD'HUI -- CE QUI LES"
                 " LIBERE (la premiere couche qui les sort de ces deux cases)" % len(les_520),
                 "   %-82s %9s %9s %6s" % ("", "PLUSIEURS", "PARTAGEE", "TOTAL")]
    for n in range(1, 11):
        a_, b_ = compte["PLUSIEURS_DOSSIERS"][n], compte["ETIQUETTE_PARTAGEE"][n]
        lignes_md.append("   %-82s %9d %9d %6d" % (COUCHES[n], a_, b_, a_ + b_))
    lignes_md.append("   %-82s %9d %9d %6d" % ("TOTAL", sum(compte["PLUSIEURS_DOSSIERS"].values()),
                                               sum(compte["ETIQUETTE_PARTAGEE"].values()), len(les_520)))
    # ce que les lignes liberees par 1-5 deviennent (leur case dans l'etat qui les libere)
    devenir = Counter()
    for i in les_520:
        n, st = res[i]
        if n <= 5:
            devenir[(n, etats[n][i][0])] += 1
    lignes_md.append("")
    lignes_md.append("CE QUE DEVIENNENT LES LIGNES LIBEREES PAR LES COUCHES 1 A 5 (leur case dans cet etat) :")
    for (n, c), v in sorted(devenir.items()):
        lignes_md.append("   couche %d -> %-22s %4d" % (n, c, v))
    # les groupes au-dela de 5 : combien de gestes
    g_par = defaultdict(set)
    for i in les_520:
        n, _ = res[i]
        if n >= 6:
            g_par[n].add(trouve(("L", i)))
    lignes_md.append("")
    lignes_md.append("AU-DELA DE 5 -- LES GROUPES (lignes + dossiers relies) que ces lignes forment :")
    for n in range(6, 11):
        gs = g_par[n]
        nl = sum(len(groupes[k]["lignes"]) for k in gs)
        nd = sum(len(groupes[k]["dossiers"]) for k in gs)
        lignes_md.append("   %-82s %4d groupes, %4d lignes, %4d dossiers" % (COUCHES[n], len(gs), nl, nd))
    sig = Counter()
    for k in g_par[9]:
        sig[signature[k]] += 1
    sig_l = Counter()
    for i in les_520:
        if res[i][0] == 9:
            sig_l[signature[trouve(("L", i))]] += 1
    lignes_md.append("")
    lignes_md.append("LES MELANGES (couche 9) -- leur forme :")
    for s_, v in sig.most_common():
        lignes_md.append("   %-62s %4d groupes, %4d de nos lignes" % (s_, v, sig_l[s_]))
    # et celles qui y ENTRENT apres la nuit et le patch (elles n'y sont pas aujourd'hui)
    entrent = [i for i in LIG if apr[i][0] in ("PLUSIEURS_DOSSIERS", "ETIQUETTE_PARTAGEE")
               and auj[i][0] not in ("PLUSIEURS_DOSSIERS", "ETIQUETTE_PARTAGEE")]
    lignes_md.append("")
    lignes_md.append("ET %d LIGNES Y ENTRENT apres la nuit et le patch V2 (elles sont ailleurs aujourd'hui) : %s"
                     % (len(entrent), dict(Counter(auj[i][0] for i in entrent))))
    for l in lignes_md:
        print(l, flush=True)

    # ── ⚠ LES LIGNES DE LA VAGUE 1 DONT L'ETIQUETTE CHANGERAIT si un geste du registre joue APRES l'ecriture ──
    #   La pose de nuit (app_poser_etiquettes_dossier) garde, quand deux dossiers etiquetes se reunissent,
    #   l'etiquette de la PLUS PETITE transaction -- l'autre est « absorbee ». Une ligne deja ecrite dont le
    #   dossier perd ainsi son etiquette porterait au Sheet un UUID qui ne designe plus rien.
    lignes_md.append("")
    lignes_md.append("LES LIGNES DE LA VAGUE 1 D'AUJOURD'HUI DONT L'ETIQUETTE CHANGERAIT (la pose garde celle de la plus"
                     " petite transaction) :")
    absorbees = {}
    for n, nom in ((1, "la nuit des 10"), (2, "+ la regle E"), (3, "+ les 8 lignes")):
        mem = defaultdict(list)
        for a, c in S[n].items():
            mem[c].append(a)
        garde = {c: TX[min(a for a in ms if TX[a]["uuid"])]["uuid"] for c, ms in mem.items()
                 if any(TX[a]["uuid"] for a in ms)}
        chg = sorted(i for i in LIG if auj[i][0] == "VAGUE_1"
                     and {garde.get(S[n][a]) for a in auj[i][2]} != {TX[auj[i][2][0]]["uuid"]})
        absorbees[n] = chg
        lignes_md.append("   apres %-16s : %3d ligne(s) %s" % (nom, len(chg), " ".join(chg)))
    lignes_md.append("")
    lignes_md.append("LES %d LIGNES DU SHEET, CASE PAR CASE, a chaque etat :" % len(LIG))
    for n in (1, 2, 3, 4, 5):
        cpt = Counter(r[0] for r in etats[n].values())
        lignes_md.append("   etat %d : %s" % (n, " . ".join("%s %d" % (k, v) for k, v in cpt.most_common())))
    # ⚠ CE QUE LA REGLE E FAIT AUX LIGNES DU SHEET : celles qu'elle fait SORTIR de la vague 1, et pourquoi
    i_ab = entete.index("Acquéreur")
    i_et = entete.index("Etat Actuel")
    par_d3 = defaultdict(set)
    for i in LIG:
        for d in etats[3][i][1]:
            par_d3[d].add(i)
    sortent = sorted(i for i in LIG if etats[2][i][0] == "VAGUE_1" and etats[3][i][0] != "VAGUE_1")
    lignes_md.append("")
    lignes_md.append("LA REGLE E FAIT SORTIR %d LIGNE(S) DE LA VAGUE 1 (etat 2 -> etat 3) :" % len(sortent))
    for i in sortent:
        autres = sorted({j for d in etats[3][i][1] for j in par_d3[d]} - {i})
        meme = all(noms_ligne(i) & noms_ligne(j) for j in autres) if autres else False
        lignes_md.append("   %s (%s, %s) -> %s ; avec %s ; %s" % (
            i, LIG[i]["row"][i_et][:14], LIG[i]["row"][i_ab][:30], etats[3][i][0],
            ", ".join("%s (%s, %s)" % (j, LIG[j]["row"][i_et][:14], LIG[j]["row"][i_ab][:30]) for j in autres),
            "MEME ACHETEUR" if meme else "acheteurs DIFFERENTS"))
    # ⭐ LE SHEET JUGE LA REGLE E : chaque transaction que E deplace (etat 1 -> etat 2), contre le dossier
    #   qu'elle rejoint -- les acquereurs (colonne AB) des lignes de l'une et de l'autre.
    lignes_de_tx = defaultdict(set)
    for i, ts in gel_v2.items():
        for a in ts:
            lignes_de_tx[a].add(i)
    # UNE REUNION = un dossier de l'etat 2 qui rassemble des transactions de PLUSIEURS dossiers de l'etat 1
    morceaux = defaultdict(lambda: defaultdict(list))
    for a, c2 in S[2].items():
        morceaux[c2][S[1].get(a)].append(a)
    reunions = {c2: m for c2, m in morceaux.items() if len(m) > 1}
    verdict_e = Counter()
    detail_e = []
    for c2, m in sorted(reunions.items()):
        cotes = []
        for c1, ts in sorted(m.items(), key=lambda x: str(x[0])):
            ls = {i for a in ts for i in lignes_de_tx.get(a, set()) if i in LIG}
            cotes.append((c1, ts, ls))
        vus = [(c1, ts, ls) for c1, ts, ls in cotes if ls]
        noms_cotes = [set().union(*(noms_ligne(i) for i in ls)) for _, _, ls in vus]
        if len(vus) < 2:
            v = "le Sheet ne voit qu'un cote (ou aucun)"
        elif not all(noms_cotes):
            v = "acquereur illisible d'un cote"
        elif set.intersection(*noms_cotes):
            v = "MEME ACHETEUR des deux cotes"
        else:
            # ⚠ LU A LA MAIN LE 19/11 AU SOIR, ET MA PREMIERE LECTURE ETAIT FAUSSE : la comparaison des AB
            #   passe par les liens du GEL. Le cote « annule » (que des compromis annules / offres refusees)
            #   est relie a une ligne « Annulee » ; si cette ligne n'a AUCUNE date de compromis (colonne T
            #   vide), le Sheet dit lui-meme que cet acheteur n'a jamais signe : le compromis annule, au nom
            #   de l'acheteur SUIVANT et au meme prix, est le sien -- c'est le LIEN DU GEL qui est suspect,
            #   et E qui a probablement raison (14033 : l'audit du 18/11 avait deja juge ce lien FAUX).
            i_t = entete.index("Compromis")
            cotes_annules = [ls for c1, ts, ls in vus
                             if all(TX[a]["etat"] in ("cancelled", "refused") for a in ts)]
            lignes_annulees = {i for ls in cotes_annules for i in ls}
            if lignes_annulees and all(not LIG[i]["row"][i_t].strip() for i in lignes_annulees):
                v = "LIEN DU GEL SUSPECT (la ligne annulee n'a pas de compromis au Sheet) -- E probablement juste"
            else:
                v = "ACHETEURS DIFFERENTS, la ligne annulee DATE un compromis -- E douteuse"
        verdict_e[v] += 1
        detail_e.append("      dossier %s : %s -- %s" % (c2, v, " || ".join(
            "%s [%s] lignes %s" % (c1, ", ".join("%s %s/%s %s" % (a, TX[a]["genre"], TX[a]["etat"], "/".join(TX[a]["noms"][:2]))
                                                  for a in sorted(ts)),
                                   " ".join("%s(%s)" % (i, " ".join(sorted(noms_ligne(i)))) for i in sorted(ls)) or "-")
            for c1, ts, ls in cotes)))
    lignes_md.append("")
    lignes_md.append("LE SHEET JUGE LA REGLE E -- ses %d reunions, cote par cote (les acquereurs AB des lignes"
                     " reliees par le gel) :" % len(reunions))
    for v, n_ in verdict_e.most_common():
        lignes_md.append("   %-56s %3d" % (v, n_))
    lignes_md.extend(detail_e)
    a_exclure = sorted(set(absorbees[2]) | set(absorbees[3]))
    lignes_md.append("   ➡ tant que la regle E et les 8 lignes ne sont pas jouees, ces %d lignes SORTENT de la vague 1"
                     % len(a_exclure))

    # ── LE FICHIER DES LIGNES NON ECRITES ──
    def debloque(i):
        c0 = auj[i][0]
        for n in (1, 2, 3, 4, 5):
            if etats[n][i][0] == "VAGUE_1":
                return "entre en vague 1 apres la couche " + COUCHES[n], "toi" if n >= 2 else "la nuit"
        c5_ = etats[5][i][0]
        pp = ("PLUSIEURS_DOSSIERS", "ETIQUETTE_PARTAGEE")

        def qui(n):
            return "toi : une scission" if n == 9 else "moi (relecture) puis toi" if n in (6, 10) else "toi"
        if c0 in pp:
            n, st = couche(i)
            if n <= 5:
                return ("sort de %s par la couche %s, puis reste en %s" % (c0, COUCHES[n], etats[n][i][0]),
                        "toi" if n >= 2 else "la nuit")
            return COUCHES[n], qui(n)
        # une ligne qui n'est pas dans ces deux cases AUJOURD'HUI mais y tombe au bout des couches 1-5
        pre = "" if c5_ == c0 else "au bout des couches 1-5 elle passe en %s ; " % c5_
        if c5_ in pp:
            n = verdict_groupe.get(trouve(("L", i)), 10)
            return pre + COUCHES[n], qui(n)
        if c5_ == "SANS_LIEN":
            return pre + "rien a ecrire : aucune transaction reliee (la ligne reste vide)", "personne"
        if c5_ == "EN_ATTENTE":
            return pre + raison_attente.get(i, "en attente"), "toi"
        if c5_ == "LIEN_A_VALIDER":
            return (pre + "ta validation des liens du gel de confiance %s"
                    % "/".join(sorted(conf_v2.get(i, set()) - {"sûre"}))), "toi"
        if c5_ == "AUDIT_NON_JUSTE":
            return pre + "l'audit du 18/11 l'a jugee « %s » : apres ses corrections" % verdicts[i]["verdict"], "toi"
        if c5_ == "GEL_SEUL":
            return pre + "relecture a la main : le juge ne retrouve aucune de ses transactions sur la ligne", "moi"
        return pre + "case %s" % c5_, "?"

    def col(nom):
        return entete.index(nom) if nom in entete else None

    lisibles = [n for n in ("Mandat", "Etat Actuel", "Offre Achat", "Compromis", "Acquéreur", "Prix")
                if col(n) is not None]
    non_ecrites = [i for i in LIG if auj[i][0] != "VAGUE_1"]
    print("\nLIGNES NON ECRITES (pas en vague 1 aujourd'hui) : %d (attendu 803)" % len(non_ecrites), flush=True)
    if len(non_ecrites) != 803:
        echecs.append("non ecrites : %d" % len(non_ecrites))
    sorties = []
    for i in sorted(non_ecrites, key=lambda x: LIG[x]["num"]):
        quoi, qui = debloque(i)
        r, ds, ts = auj[i]
        sorties.append({
            "ligne_au_19_11": LIG[i]["num"], "id_unique": i, "case_aujourd_hui": r,
            "case_apres_nuit_et_patch": apr[i][0], "case_au_bout_1_a_5": etats[5][i][0],
            "ce_qui_la_debloque": quoi, "qui": qui,
            **{n: LIG[i]["row"][col(n)] for n in lisibles},
            "dossiers_aujourd_hui": " ".join(map(str, ds)),
            "transactions_et_genre": " ".join("%s(%s%s)" % (a, TX[a]["genre"], ",C5" if TX[a]["classeur"] else "")
                                              for a in ts),
        })
    # les AUTRES lignes qui partagent un dossier (pour lire une « etiquette partagee » sans chercher)
    par_dossier = defaultdict(set)
    for i in LIG:
        for d in auj[i][1]:
            par_dossier[d].add(i)
    for s in sorties:
        ds = [int(x) for x in s["dossiers_aujourd_hui"].split()] if s["dossiers_aujourd_hui"] else []
        s["autres_lignes_du_meme_dossier"] = " ".join(sorted({j for d in ds for j in par_dossier[d]} - {s["id_unique"]}))
    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sorties[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(sorties)
    print("CSV : %s (%d lignes, separateur ;)" % (SORTIE_CSV, len(sorties)), flush=True)

    # le classeur .xlsx (a ouvrir) : une feuille de lignes, une feuille de compte
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
        wb = Workbook()
        ws = wb.active
        ws.title = "Les lignes non ecrites"
        cles = list(sorties[0].keys())
        ws.append(cles)
        for c in ws[1]:
            c.font = Font(bold=True)
        for s in sorties:
            ws.append([s[k] for k in cles])
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = ws.dimensions
        larg = {"ce_qui_la_debloque": 70, "transactions_et_genre": 40, "autres_lignes_du_meme_dossier": 30,
                "Acquéreur": 30}
        for k, c in zip(cles, ws[1]):
            ws.column_dimensions[c.column_letter].width = larg.get(k, 16)
        ws2 = wb.create_sheet("Le compte")
        for l in lignes_md:
            ws2.append([l])
        ws3 = wb.create_sheet("Par case")
        ws3.append(["case aujourd'hui", "lignes"])
        for k, v in Counter(s["case_aujourd_hui"] for s in sorties).most_common():
            ws3.append([k, v])
        wb.save(SORTIE_XLSX)
        print("XLSX : %s" % SORTIE_XLSX, flush=True)
    except ImportError:
        print("⚠ openpyxl absent : pas de .xlsx (le CSV suffit)", flush=True)
    SORTIE_MD.write_text("# Le compte de la question 3 du 19/11 au soir (genere par %s)\n\n```\n%s\n```\n"
                         % (Path(__file__).name, "\n".join(lignes_md)), encoding="utf-8")
    print("MD : %s" % SORTIE_MD, flush=True)
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs, flush=True)
        return 2
    return 0


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "photo":
        return etape_photo()
    if len(sys.argv) >= 2 and sys.argv[1] == "classer":
        return etape_classer()
    print(__doc__)
    return 3


if __name__ == "__main__":
    sys.exit(main())
