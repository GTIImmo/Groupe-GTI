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
    garde X  (19/11 au soir) UN SEUL rejeu par appel, X = temoin | g1 | g2 | g12 : la garde « la date bat
             le nom » inseree dans une COPIE de affaire_ledger.py hors du depot (l'original n'est pas
             touche), rejouee sur le scenario 3 ; chaque etape ecrite AU FIL dans garde_journal.txt
             (~15 s par rejeu). Le temoin : la copie SANS garde redonne le scenario 3 a 0 ecart.
    classer  local, sans reseau : relit la photo, les chaines des scenarios de ⑥ (chaines_s1/2/3.json),
             celles de la garde (chaines_g*.json) et le patch V2 ; ecrit le CSV, le classeur .xlsx et le
             compte

SES DECISIONS DU 19/11 AU SOIR, APPLIQUEES ICI : la regle C5 « a l'export » (couche 5) ; les 9 « meme
acheteur » -> l'etiquette sur la SEULE ligne vivante, la tentative annulee reste vide (couche 8) ; 21520
exclue de E comme 26613 (couche 11, « en attente de ta reponse »). Et ses demandes : aller AU BOUT des
melanges (la famille, la coupe que le Sheet propose, ce que fait la garde, qui agit) et des 16 non
tranchees ; les lignes 2025-2026 avec les deux formats de date du Sheet.

SES DECISIONS DU 20/11 (nuit), APPLIQUEES ICI : 4126, 4496, 4720 exclues de E comme 21520 (affaire_ledger.py ;
rejouer « rejeu 2 », « rejeu 3 » de temps5_q6 puis « garde temoin|g1|g2|g12 » avant « classer ») ; la DECISION B :
les lignes de la vague 1 dont G2 changerait l'etiquette passent en VAGUE 2 -- recalculees a chaque classement,
comparees aux 10 du 19/11, ecrites dans TEMPS6_DECISION_B_LIGNES_REPORTEES_EN_VAGUE_2_PAR_G2_2026-11-20.csv.

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
#: DECISION B de Frederic (20/11) : les lignes de la vague 1 dont G2 changerait l'etiquette passent en vague 2
SORTIE_B = RACINE / "notice" / "TEMPS6_DECISION_B_LIGNES_REPORTEES_EN_VAGUE_2_PAR_G2_2026-11-20.csv"
#: les 10 lignes mesurees le 19/11 au soir (§ 11.3) -- la liste recalculee leur est comparee, chaque ecart NOMME
LES_10_DU_19_11 = ("A6OS2TTJ", "ANHQ1PK7", "JBCC1KBT", "MFMR0U6A", "QL70KV8I", "R9ANL92S", "SA7DWYEZ", "SUVPN4BH",
                   "V5NJER40", "WG8CG5T2")
AL, AB = 37, 27

COUCHES = {
    1: "1 la nuit des 10 menages (decidee, joue cette nuit)",
    2: "2 le patch V2 du gel (ton « vas-y »)",
    3: "3 la regle E (allumage vendredi 20/11 ; 5 exclusions declarees : 26613, 21520, 4126, 4496, 4720)",
    4: "4 les 8 lignes de 5.6 (ta lecture)",
    5: "5 la regle C5 « a l'export » (DECIDEE le 19/11 au soir : une regle de l'outil d'ecriture)",
    6: "6 relecture du gel (un patch a valider, sans scission)",
    7: "7 reunir (lignes de rattachement, ta decision ligne a ligne, sans scission)",
    8: "8 meme acheteur sur deux lignes (DECIDE : l'etiquette sur la seule ligne vivante)",
    9: "9 melange -> SCISSION",
    10: "10 non tranche (le juge ne voit pas une des lignes)",
    11: "11 en attente de ta reponse (une transaction EXCLUE de la regle E)",
}
#: la variante de la garde qui decide de la colonne « qui » (choisie sur la mesure du 19/11 au soir, voir ⑪)
GARDE_RETENUE = "g2"


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

    # ⭐ 19/11 au soir, LES 16 NON TRANCHEES RELUES A LA MAIN : 12 sont des melanges que le juge ne voyait pas,
    #   parce que mots_propres ecarte comme PRENOMS des noms de famille (LAURENT, ROBERT, VINCENT, PLE, LY,
    #   KNIGHT...). Quand mots_propres ne rend RIEN, on lit les mots bruts de AB, sans les civilites.
    MOTS_VIDES = {"NAN", "M", "MME", "MR", "MLLE", "MM", "MMES", "MRS", "MONSIEUR", "MADAME", "ET", "DE", "DU",
                  "LA", "LE", "DES", "EPOUX", "CONSORTS", "INDIVISION", "SCI"}

    def noms_bruts(i):
        brut = re.sub(r"[^A-ZÀ-ÖØ-Þ]+", " ", LIG[i]["row"][AB].upper())
        return {w for w in brut.split() if len(w) >= 2 and w not in MOTS_VIDES}

    def noms_ligne(i):
        if i not in LIG:
            return set()
        return set(LIG[i]["noms_ab"]) or noms_bruts(i)

    verdict_groupe = {}
    for k, gr in groupes.items():
        ls, ds = gr["lignes"], gr["dossiers"]
        if len(ls) == 1:
            seule = next(iter(ls))
            # ⭐ 19/11 au soir : une ligne SEULE reliee a plusieurs dossiers dont AUCUN n'est designe par elle
            #   (lu a la main : caea1510, 5a4371b5, 1f3d536a -- une ligne « Annulee » SANS date de compromis,
            #   reliee par le gel a un compromis annule sans date de l'acheteur SUIVANT et a sa creation C5)
            #   n'est pas « non tranchee » : c'est un lien du gel a relire, comme la couche 6.
            verdict_groupe[k] = 6 if len(ds) == 1 or seule in aucun_tenu else 7
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
        # ⭐ 19/11 au soir, relu a la main : une ligne qui ne designe RIEN du groupe mais dont l'acquereur AB
        #   est le nom d'une de ses transactions la TIENT quand meme (XHITO8HE GARRY : son offre 27556 est a
        #   2 jours de la date du Sheet, hors de la tolerance du juge ; le nom GARRY est dessus).
        tient_nom = {i for i in ls if i in aucun_tenu
                     and any(set(TX[a]["noms"]) & noms_ligne(i) for d_ in E[i] for a in E[i][d_])}
        connues_vues = {t2(i) for i in ls if (i not in aucun_tenu or i in tient_nom) and noms_ligne(i)}
        muettes = [i for i in ls if i in aucun_tenu and i not in tient_nom]
        if len({t2(i) for i in ls}) == 1:
            verdict_groupe[k] = 8
        elif len(connues_vues) >= 2:
            verdict_groupe[k] = 9
        elif muettes:
            # une ligne qui ne designe rien et ne porte aucun nom du groupe : son LIEN DU GEL est suspect (lu a la
            #   main : caea1510 LAFFONT -> 3669 RUAULT, 5a4371b5 MORAINES -> 28178 ESCAILLET, 1f3d536a PALLANDRE
            #   -> 24010 GRANGEON -- les liens du gel que le Sheet accuse en § 10.4)
            verdict_groupe[k] = 6
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

    # ══ 19/11 AU SOIR, SES DEMANDES : FINIR LES 351 ET LES 16, ET MESURER LA GARDE ══════════════════════════════
    import phase2.sync.affaire_ledger as al_
    exclues_e = set(al_.EXCLUES_DE_LA_REGLE_E)
    for k, gr in groupes.items():
        if any(a in exclues_e for d in gr["dossiers"] for a in membres[d]):
            verdict_groupe[k] = 11
    cols_vente = ["Vente Prévue", "Vente Fixée", "Signée"]
    for c_ in ["Offre Achat", "Compromis"] + cols_vente:
        assert c_ in entete, "colonne absente du Sheet : %s" % c_
    col_genre = {"offre": [entete.index("Offre Achat")], "compromis": [entete.index("Compromis")],
                 "vente": [entete.index(c_) for c_ in cols_vente]}

    def par_la_date(i, a):
        """La ligne i designe-t-elle a PAR LA DATE (sa case du genre est remplie) ? Sinon c'est par la voie
        « case vide » du juge (mandat + nom + prix) -- et LA DATE BAT LE NOM."""
        return any(LIG[i]["row"][c_].strip() for c_ in col_genre.get(TX[a]["genre"], []))

    def est_annulee(i):
        return i in LIG and LIG[i]["row"][i_etat].strip().lower().startswith("annul")

    def classes_acheteurs(ls):
        p = {i: i for i in ls}

        def t(x):
            while p[x] != x:
                x = p[x]
            return x
        lst = sorted(ls)
        for xi, x in enumerate(lst):
            for y in lst[xi + 1:]:
                if noms_ligne(x) & noms_ligne(y):
                    p[t(x)] = t(y)
        return {i: t(i) for i in ls}

    def court(i):
        return "%s %s" % (i, "/".join(sorted(noms_ligne(i)))[:24])

    def tx_court(a):
        return "%s %s%s" % (a, TX[a]["genre"][:4], "" if not TX[a]["etat"] else "(%s)" % TX[a]["etat"][:6])

    FAMILLES = {
        "F1": "F1 le nom de l'ANCIEN acheteur sur une piece VIVANTE du nouveau (le defaut de Hektor)",
        "F2": "F2 le nom du NOUVEL acheteur sur la piece de l'ancien (la date du Sheet le dement)",
        "F3": "F3 annulee + vivante, la piece porte un autre nom ou aucun",
        "F4": "F4 que des lignes annulees",
        "F5": "F5 que des lignes vivantes",
    }
    famille, coupe, coupe_etat, proprio = {}, {}, {}, {}
    for k, gr in groupes.items():
        if verdict_groupe.get(k) != 9:
            continue
        ls = sorted(gr["lignes"])
        cls = classes_acheteurs(ls)
        ann = [i for i in ls if est_annulee(i)]
        viv = [i for i in ls if not est_annulee(i)]
        n_ann = set().union(*(noms_ligne(i) for i in ann)) if ann else set()
        n_viv = set().union(*(noms_ligne(i) for i in viv)) if viv else set()
        txs = sorted({a for d in gr["dossiers"] for a in membres[d]})
        part, reste, dispute, c5_ = defaultdict(list), [], [], []
        for a in txs:
            if TX[a]["classeur"]:
                c5_.append(a)
                continue
            des = [i for i in ls if a in DS[i]]
            dat = [i for i in des if par_la_date(i, a)]
            cs = {cls[i] for i in (dat or des)}
            if len(cs) == 1:
                part[cs.pop()].append((a, "date" if dat else "case vide"))
            elif cs:
                dispute.append(a)
            else:
                # ⛔ 20/11 AU SOIR -- LE DEFAUT EST ICI, ET IL EST RETIRE : on donnait la piece au NOM qu'elle porte
                #   (« [nom seul] »). Or Hektor recopie le nom du premier acheteur sur TOUS les compromis du bien : 3
                #   lectures fausses et 5 des 67 « OUI » valides etaient de ce type. Une piece sans ligne qui la designe
                #   reste desormais SANS LIGNE ; l'outil corrige est `coupe_preuve_interne.py` (date au jour exact,
                #   puis prix + honoraires, sur TOUTES les lignes du bien -- jamais le nom). ⚠ « date » ci-dessus veut
                #   seulement dire « la case est remplie », pas « la date est egale » : ne plus s'en servir pour couper.
                reste.append(a)
        proprio[k] = {a: c for c, xs in part.items() for a, _ in xs}
        sans_piece = sorted({cls[i] for i in ls} - set(part))
        coupe_etat[k] = ("DISPUTEE" if dispute else "A COMPLETER" if reste or sans_piece else
                         "NETTE" if len(part) >= 2 else "PAS DE COUPE")
        morceaux = []
        for c, xs in sorted(part.items(), key=lambda kv: min(a for a, _ in kv[1])):
            morceaux.append("%s -> %s" % ("+".join(tx_court(a) + ("" if how == "date" else "[%s]" % how)
                                                   for a, how in sorted(xs)),
                                          " & ".join(court(i) for i in ls if cls[i] == c)))
        if reste:
            morceaux.append("SANS LIGNE : " + "+".join(tx_court(a) for a in reste))
        if dispute:
            morceaux.append("DISPUTEES : " + "+".join(tx_court(a) for a in dispute))
        if sans_piece:
            morceaux.append("LIGNE SANS PIECE : " + " & ".join(court(i) for i in ls if cls[i] in sans_piece))
        if c5_:
            morceaux.append("C5 (ne decident pas) : " + "+".join(str(a) for a in c5_))
        gardes_ = []
        for d in sorted(gr["dossiers"]):
            m0 = min(membres[d])
            gardes_.append("dossier %s garde son etiquette avec %s" % (d, m0))
        coupe[k] = " | ".join(morceaux) + " || " + " ; ".join(gardes_)
        vivante_ancien = [a for a in txs if not TX[a]["classeur"] and TX[a]["etat"] not in ("cancelled", "refused")
                          and set(TX[a]["noms"]) & n_ann and not set(TX[a]["noms"]) & n_viv]
        morte_nouveau = [a for a in txs if not TX[a]["classeur"] and TX[a]["etat"] in ("cancelled", "refused")
                         and set(TX[a]["noms"]) & n_viv and not set(TX[a]["noms"]) & n_ann
                         and proprio[k].get(a) in {cls[i] for i in ann}]
        famille[k] = ("F1" if ann and viv and vivante_ancien else "F2" if ann and viv and morte_nouveau else
                      "F3" if ann and viv else "F4" if ann else "F5")

    # ── LA GARDE « LA DATE BAT LE NOM » : chaque variante rejouee (etape garde), jugee par le Sheet ──
    def etiquettes(lab_prec, ch_new):
        """Ce que ferait app_poser_etiquettes_dossier : la FUSION garde l'etiquette de la plus petite
        transaction ; puis la SCISSION laisse l'etiquette au groupe de la plus petite transaction qui la porte,
        et en donne une NEUVE aux autres groupes."""
        mem = defaultdict(list)
        for a, c in ch_new.items():
            mem[c].append(a)
        lab1 = {}
        for c, ms in mem.items():
            labs = {lab_prec[a] for a in ms if lab_prec.get(a)}
            g_ = (lab_prec[min(a for a in ms if lab_prec.get(a))] if labs else "NEUVE:%s" % c)
            for a in ms:
                lab1[a] = g_
        tete, chaines_du_lab = {}, defaultdict(set)
        for a in sorted(lab1):
            tete.setdefault(lab1[a], ch_new[a])
            chaines_du_lab[lab1[a]].add(ch_new[a])
        return {a: (l_ if len(chaines_du_lab[l_]) == 1 or ch_new[a] == tete[l_] else "NEUVE:%s" % ch_new[a])
                for a, l_ in lab1.items()}

    lab = {0: {a: t["uuid"] for a, t in TX.items() if t["uuid"]}}
    lab[1] = etiquettes(lab[0], S[1])
    lab[2] = etiquettes(lab[1], S[2])
    lab[3] = etiquettes(lab[2], S[3])
    # TEMOIN de la simulation : elle doit redonner les lignes « absorbees par E » de l'ancienne methode
    v1_auj = [i for i in LIG if auj[i][0] == "VAGUE_1"]
    absorbees_sim = sorted(i for i in v1_auj if {lab[2].get(a) for a in auj[i][2]} != {TX[auj[i][2][0]]["uuid"]})
    gardes_mesurees = {}
    for nom in GARDE_VARIANTES:
        f = CACHE / ("chaines_%s.json" % nom)
        if f.exists():
            gardes_mesurees[nom] = {int(a): c for a, c in lire_json(f).items()}
    if not gardes_mesurees:
        print("⚠ aucune variante de la garde rejouee (etape « garde ») : la mesure de la garde est SAUTEE", flush=True)
    v1_5 = [i for i in LIG if etats[5][i][0] == "VAGUE_1"]
    # ⭐ 20/11 (⑬), LA QUESTION DE FREDERIC : « si on faisait ces coupes, combien de lignes de la vague 1
    #   changeraient d'etiquette ? » -- on EXPORTE tout ce que la coupe connait, pour la mesure a part
    #   (temps7_effet_des_coupes_sur_la_vague_1_2026-11-20.py). Avec T6_EXPORT_COUPES=1 l'etape s'arrete
    #   APRES l'export : aucun fichier de notice/ n'est reecrit. Sans la variable : RIEN ne change.
    if os.environ.get("T6_EXPORT_COUPES") == "1":
        mardi = ranger(gel, conf, S[2], False, True, c5=True)
        ecrire_json(CACHE / "t7_export_coupes.json", {
            "photo_du": P["lu_le"],
            "groupes": {"%s:%s" % k: {"lignes": sorted(g_["lignes"]), "dossiers": sorted(g_["dossiers"]),
                                      "verdict": verdict_groupe.get(k), "famille": famille.get(k),
                                      "coupe_etat": coupe_etat.get(k), "coupe": coupe.get(k),
                                      "proprio": {str(a): c for a, c in proprio.get(k, {}).items()}}
                        for k, g_ in groupes.items()},
            "etat5": {i: [etats[5][i][0], list(etats[5][i][1]), list(etats[5][i][2])] for i in LIG},
            "mardi": {i: [mardi[i][0], list(mardi[i][1]), list(mardi[i][2])] for i in LIG},
            "ds_date": {i: sorted(a for a in v if par_la_date(i, a)) for i, v in DS.items() if v and i in LIG},
            "ds": {i: sorted(v) for i, v in DS.items() if v and i in LIG},
            "lab2": {str(a): l_ for a, l_ in lab[2].items()},
            "lab3": {str(a): l_ for a, l_ in lab[3].items()},
        })
        print("EXPORT pour la mesure des coupes : %s -- l'etape s'arrete ici (rien de reecrit dans notice/)"
              % (CACHE / "t7_export_coupes.json"), flush=True)
        return 0
    les_9 = [i for i in LIG if verdict_groupe.get(trouve(("L", i))) == 9 and i in E2 and E2[i]]
    lignes_tx_v2 = defaultdict(set)
    for i, ts in gel_v2.items():
        for a in ts:
            if i in LIG:
                lignes_tx_v2[a].add(i)
    mesure_garde, resout, lab_par_garde = {}, {}, {}
    src_g = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite"), uri=True)
    an_tx_g = {a: int(str(d)[:4]) for a, d in src_g.execute("SELECT app_affaire_id, date FROM app_affaire_ledger")
               if re.match(r"\d{4}-", str(d or "")) and not str(d).startswith("0000")}
    src_g.close()
    for nom, chg in gardes_mesurees.items():
        par_s3 = defaultdict(set)
        for a, c in S[3].items():
            par_s3[c].add(chg.get(a))
        coupes_ = {c for c, gs in par_s3.items() if len(gs) > 1}
        par_g = defaultdict(set)
        for a, c in chg.items():
            par_g[c].add(S[3].get(a))
        reunis_ = {c for c, ss in par_g.items() if len(ss) > 1}
        mem3 = defaultdict(set)
        for a, c in S[3].items():
            mem3[c].add(a)
        vus = {c for c in coupes_ if any(lignes_tx_v2.get(a) for a in mem3[c])}
        lab_g = etiquettes(lab[3], chg)
        lab_par_garde[nom] = lab_g
        rg = ranger(gel_v2, conf_v2, chg, True, True, c5=True)
        sg = structure(gel_v2, chg, True)
        chg_lab = sorted(i for i in v1_5 if {lab_g.get(a) for a in etats[5][i][2]} != {lab[3].get(etats[5][i][2][0])})
        sortent_v1 = sorted(i for i in v1_5 if rg[i][0] != "VAGUE_1")
        liberees = sorted(i for i in les_9 if sg[i] in ("SEULE", "VIDE"))
        gr_9 = {trouve(("L", i)) for i in les_9}
        gr_ok = {k for k in gr_9 if all(sg[i] in ("SEULE", "VIDE") for i in groupes[k]["lignes"])}
        conforme = set()
        for k in gr_ok:
            pr = proprio.get(k, {})
            ch_par_classe = defaultdict(set)
            for a, c in pr.items():
                ch_par_classe[c].add(chg.get(a))
            if all(len(v) == 1 for v in ch_par_classe.values()) and \
                    len({next(iter(v)) for v in ch_par_classe.values()}) == len(ch_par_classe):
                conforme.add(k)
        empirees = sorted(i for i in LIG if structs[5][i] == "SEULE" and sg[i] in ("MULTI", "PARTAGEE"))
        # chaque dossier COUPE, juge par le Sheet : les lignes de chaque morceau (liens du gel apres le patch V2)
        jug, ans_inv, detache_inv, exemples = Counter(), Counter(), Counter(), defaultdict(list)
        for c in sorted(coupes_):
            parts_ = defaultdict(set)
            for a in mem3[c]:
                parts_[chg[a]].add(a)
            lp = {g_: {i for a in xs for i in lignes_tx_v2.get(a, ())} for g_, xs in parts_.items()}
            toutes_l = set().union(*lp.values())
            if not toutes_l:
                v_ = "INVISIBLE (aucune ligne du Sheet)"
                ys = [an_tx_g.get(a) for a in mem3[c] if an_tx_g.get(a)]
                ans_inv[min(ys) if ys else None] += 1
                tete_ = chg[min(mem3[c])]
                detache_inv["+".join(sorted("%s(%s)" % (TX[a]["genre"], TX[a]["etat"] or "-")
                                            for g_, xs in parts_.items() if g_ != tete_ for a in xs))] += 1
            elif any(sum(1 for g_ in lp if i in lp[g_]) > 1 for i in toutes_l):
                v_ = "DEMENTIE (une ligne sur deux morceaux)"
            elif sum(1 for g_ in lp if lp[g_]) == 1:
                v_ = "NEUTRE (un seul morceau a des lignes)"
            else:
                cl_ = [set().union(*(noms_ligne(i) for i in lp[g_])) for g_ in lp if lp[g_]]
                v_ = ("CONFIRMEE (acheteurs differents)" if not set.intersection(*cl_)
                      else "DEMENTIE (le meme acheteur des deux cotes)")
            jug[v_] += 1
            exemples[v_].append(c)
        par_fam = Counter(famille[k] for k in gr_ok)
        resout[nom] = gr_ok
        mesure_garde[nom] = {"coupes": len(coupes_), "coupes_vus": len(vus), "reunis": len(reunis_),
                             "v1_etiquette_change": chg_lab, "v1_sortent": sortent_v1,
                             "melanges_liberees": len(liberees), "groupes_resolus": len(gr_ok),
                             "groupes_conformes": len(conforme), "empirees": empirees, "par_famille": par_fam,
                             "vague1_apres": sum(1 for i in LIG if rg[i][0] == "VAGUE_1"),
                             "cases": Counter(r[0] for r in rg.values()),
                             "cases_sortie": {i: rg[i][0] for i in sortent_v1},
                             "jugement": jug, "annees_invisibles": ans_inv, "detache_invisibles": detache_inv,
                             "exemples": {k_: v[:12] for k_, v in exemples.items()}}

    # ── LA COUCHE DE CHAQUE LIGNE ──
    def couche(i):
        """La premiere couche qui sort la ligne de PLUSIEURS DOSSIERS / ETIQUETTE PARTAGEE."""
        if any(a in exclues_e for a in gel_v2.get(i, set())):
            return 11, "?"
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
    for n in range(1, 12):
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
    for n in range(6, 12):
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
    print("TEMOIN : la simulation fusion+scission redonne les lignes absorbees par E -- %s (ancienne methode %d,"
          " simulation %d)" % ("OUI" if absorbees_sim == absorbees[2] else "⛔ NON", len(absorbees[2]),
                                len(absorbees_sim)), flush=True)
    if absorbees_sim != absorbees[2]:
        echecs.append("simulation des etiquettes")

    # ── ⭐ LA GARDE « LA DATE BAT LE NOM » -- ce qu'elle couperait, et la VAGUE 1 ──
    lignes_md.append("")
    lignes_md.append("LA GARDE « LA DATE BAT LE NOM » DANS LA REGLE D -- MESUREE SEULEMENT (copie du code hors du depot,"
                     " rejouee sur le scenario 3 : la nuit des 10 + E + les 8 lignes)")
    lignes_md.append("   G1 = un cote a un COMPROMIS VIVANT dont l'acquereur n'est pas dans l'autre cote -> pas de reunion")
    lignes_md.append("   G2 = un cote a une OFFRE ACCEPTEE DATEE dont l'acquereur n'est pas dans l'autre cote -> pas de"
                     " reunion ; G12 = l'une OU l'autre")
    lignes_md.append("   la vague 1 de reference = l'etat 5 (patch V2 + E + 8 lignes + C5) : %d lignes" % len(v1_5))
    for nom, m in mesure_garde.items():
        lignes_md.append("   %-4s dossiers coupes %4d (dont %4d que le Sheet voit) . reunions nouvelles %3d ."
                         " VAGUE 1 : %3d etiquette(s) changee(s), %3d ligne(s) qui en sortent -> vague 1 = %d"
                         % (nom.upper(), m["coupes"], m["coupes_vus"], m["reunis"], len(m["v1_etiquette_change"]),
                            len(m["v1_sortent"]), m["vague1_apres"]))
        lignes_md.append("        melanges (couche 9, etat 5) : %d ligne(s) liberee(s), %d groupe(s) resolu(s) dont %d"
                         " coupes EXACTEMENT comme le Sheet le propose ; par famille %s"
                         % (m["melanges_liberees"], m["groupes_resolus"], m["groupes_conformes"],
                            dict(sorted(m["par_famille"].items()))))
        lignes_md.append("        lignes SEULES a l'etat 5 qui deviennent PLUSIEURS / PARTAGEE : %d %s"
                         % (len(m["empirees"]), " ".join(m["empirees"][:30])))
        lignes_md.append("        vague 1 -- etiquette changee : %s" % " ".join(m["v1_etiquette_change"][:60]))
        lignes_md.append("        vague 1 -- en sortent : %s" % " ".join(
            "%s(%s)" % (i, m["cases_sortie"][i]) for i in m["v1_sortent"][:60]))
        lignes_md.append("        LES %d DOSSIERS COUPES, JUGES PAR LE SHEET : %s" % (
            m["coupes"], " . ".join("%s %d" % kv for kv in m["jugement"].most_common())))
        for v_, ex in sorted(m["exemples"].items()):
            lignes_md.append("           ex. %-42s %s" % (v_, " ".join(map(str, ex))))
        lignes_md.append("        les INVISIBLES par annee (la plus ancienne transaction du dossier) : %s" % " . ".join(
            "%s %d" % (y or "?", n_) for y, n_ in sorted(m["annees_invisibles"].items(), key=lambda kv: kv[0] or 0)))
        lignes_md.append("        les INVISIBLES -- ce qui se DETACHE (le morceau sans la plus petite transaction) : %s"
                         % " . ".join("%s %d" % kv for kv in m["detache_invisibles"].most_common(12)))

    # ── ⭐ DECISION B DE FREDERIC (20/11) : les lignes de la vague 1 dont G2 changerait l'etiquette -> VAGUE 2 ──
    #   « LA GARDE G2 : je prends B. Les 10 lignes sortent de la vague 1 et passent en vague 2. G2 se code APRES
    #   l'ecriture, et pas avant d'avoir relu ses 281 coupes invisibles. »
    #   La liste n'est PAS figee a la main : elle se RECALCULE a chaque classement (les exclusions de E, le patch,
    #   la nuit la font bouger), et elle est comparee aux 10 du 19/11 -- chaque ecart est NOMME.
    reportees_b = list(mesure_garde.get(GARDE_RETENUE, {}).get("v1_etiquette_change", []))
    lignes_md.append("")
    lignes_md.append("⭐ DECISION B (20/11) : LES LIGNES DE LA VAGUE 1 DONT LA GARDE %s CHANGERAIT L'ETIQUETTE PASSENT EN"
                     " VAGUE 2 (G2 se code apres l'ecriture)" % GARDE_RETENUE.upper())
    if GARDE_RETENUE not in mesure_garde:
        lignes_md.append("   ⛔ la garde %s n'est pas rejouee : la liste ne peut pas etre faite" % GARDE_RETENUE)
        echecs.append("decision B : garde %s non rejouee" % GARDE_RETENUE)
    else:
        chg_b, lab_b = gardes_mesurees[GARDE_RETENUE], lab_par_garde[GARDE_RETENUE]
        sortis_b = sorted(set(LES_10_DU_19_11) - set(reportees_b))
        neufs_b = sorted(set(reportees_b) - set(LES_10_DU_19_11))
        lignes_md.append("   %d ligne(s) : %s" % (len(reportees_b), " ".join(reportees_b)))
        lignes_md.append("   contre les 10 du 19/11 au soir -- sortent de la liste : %s . nouvelles : %s"
                         % (" ".join("%s (etat 5 : %s)" % (i, etats[5][i][0]) for i in sortis_b) or "aucune",
                            " ".join(neufs_b) or "aucune"))
        lignes_md.append("   ➡ la vague 1 de reference (etat 5) : %d - %d = %d lignes"
                         % (len(v1_5), len(reportees_b), len(v1_5) - len(reportees_b)))
        src_b = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite"), uri=True)
        nom_b = {}
        for a, aj in src_b.execute("SELECT app_affaire_id, acquereurs_json FROM app_affaire_ledger"):
            try:
                v = json.loads(aj or "null")
                v = v[0] if isinstance(v, list) and v else v
                nom_b[a] = (v or {}).get("nom", "") if isinstance(v, dict) else ""
            except (ValueError, TypeError):
                nom_b[a] = ""
        src_b.close()
        mem3_b = defaultdict(set)
        for a, c in S[3].items():
            mem3_b[c].add(a)
        sorties_b = []
        for i in sorted(reportees_b, key=lambda x: LIG[x]["num"]):
            ts_ = etats[5][i][2]
            dossier = mem3_b[S[3][ts_[0]]]
            parts_b = defaultdict(list)
            for a in sorted(dossier):
                parts_b[chg_b[a]].append(a)
            tete_b = chg_b[min(dossier)]
            def piece(xs):
                return " + ".join("%s %s(%s) %s" % (a, TX[a]["genre"][:5], (TX[a]["etat"] or "-")[:6], nom_b.get(a, ""))
                                  for a in xs)
            coupe_b = " || ".join(("[garde l'etiquette] " if g_ == tete_b else "[etiquette NEUVE] ") + piece(xs)
                                  for g_, xs in sorted(parts_b.items(), key=lambda kv: min(kv[1])))
            sorties_b.append({
                "ligne_au_19_11": LIG[i]["num"], "id_unique": i,
                **{n: LIG[i]["row"][entete.index(n)] for n in ("Acquéreur", "Etat Actuel", "Offre Achat", "Compromis",
                                                                "Prix") if n in entete},
                "transactions_de_la_ligne": " ".join(map(str, ts_)),
                "etiquette_avant_g2": lab[3].get(ts_[0], ""),
                "etiquette_apres_g2": " ".join(sorted({str(lab_b.get(a, "")) for a in ts_})),
                "le_dossier_coupe_par_g2": coupe_b,
                "pourquoi": "la tentative ratee d'un acheteur precedent (le plus petit numero du dossier) GARDERAIT "
                            "l'etiquette ; la ligne en recevrait une NEUVE -- ecrite avant G2, elle designerait la "
                            "mauvaise affaire. DECISION B du 20/11 : vague 2, apres G2.",
            })
            lignes_md.append("   %s %-28s %s" % (i, LIG[i]["row"][entete.index("Acquéreur")][:28] if "Acquéreur" in entete
                                                  else "", coupe_b[:220]))
        if sorties_b:
            with SORTIE_B.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(sorties_b[0].keys()), delimiter=";")
                w.writeheader()
                w.writerows(sorties_b)
            lignes_md.append("   le fichier (que l'outil d'ecriture lira comme une EXCLUSION de la vague 1) : %s"
                             % SORTIE_B.name)
            print("CSV decision B : %s (%d lignes)" % (SORTIE_B, len(sorties_b)), flush=True)
    reportees_b_set = set(reportees_b)

    # ── LES MELANGES PAR FAMILLE, et la coupe que le Sheet propose ──
    lignes_md.append("")
    lignes_md.append("LES MELANGES (couche 9) PAR FAMILLE -- groupes, lignes, et l'etat de la coupe que le Sheet propose :")
    lignes_9_par_g = defaultdict(list)
    for i in les_520:
        if res[i][0] == 9:
            lignes_9_par_g[trouve(("L", i))].append(i)
    for f_, lib in FAMILLES.items():
        gs = [k for k in lignes_9_par_g if famille.get(k) == f_]
        if not gs:
            continue
        nl = sum(len(lignes_9_par_g[k]) for k in gs)
        et_ = Counter(coupe_etat[k] for k in gs)
        ga = {nom: sum(1 for k in gs if k in resout.get(nom, set())) for nom in mesure_garde}
        lignes_md.append("   %-92s %3d groupes %3d lignes . coupe %s . resolus par la garde %s"
                         % (lib, len(gs), nl, dict(sorted(et_.items())), ga))
    lignes_md.append("   (le detail, groupe par groupe, est dans la colonne « ce_qui_la_debloque » du fichier)")

    # ── LES DEUX CHIFFRES DU 19/11 AU SOIR : les lignes « sans date », et les lignes 2025-2026 ──
    #   ⚠ « Sans date » etait FAUX : ces lignes ont une date d'offre dans l'AUTRE FORMAT du Sheet (« 20 fevrier25 »).
    #   On lit les deux formats avec le lecteur du juge de ⑤ (date_du_classeur_tolerante), et on donne aussi l'annee
    #   de NOS transactions (celles que le gel relie a la ligne) -- une source independante du Sheet.
    lire_d = charger_juge().date_du_classeur_tolerante
    src_ = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite"), uri=True)
    an_tx = {}
    for a, d in src_.execute("SELECT app_affaire_id, date FROM app_affaire_ledger"):
        m_ = re.match(r"(\d{4})-", str(d or ""))
        if m_ and m_.group(1) != "0000":
            an_tx[a] = int(m_.group(1))
    src_.close()
    i_s, i_t = entete.index("Offre Achat"), entete.index("Compromis")
    jjmm = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")

    def an_offre(i):
        d = lire_d(LIG[i]["row"][i_s])
        return d.year if d else None

    def an_nos_tx(i):
        ys = [an_tx[a] for a in gel.get(i, set()) if a in an_tx]
        return min(ys) if ys else None
    ne_ = [i for i in LIG if auj[i][0] != "VAGUE_1"]
    forme = Counter("jj/mm/aaaa" if jjmm.search(LIG[i]["row"][i_s]) else "VIDE" if not LIG[i]["row"][i_s].strip()
                    else "jj mois aa" for i in ne_)
    autres = [i for i in ne_ if not jjmm.search(LIG[i]["row"][i_s])]
    lignes_md.append("")
    lignes_md.append("LES LIGNES « SANS DATE » -- elles ont une date, dans l'AUTRE format du Sheet (« 20 fevrier25 »)")
    lignes_md.append("   les %d non ecrites, par forme de la date d'offre : %s" % (len(ne_), dict(forme)))
    lignes_md.append("   les %d qui ne sont pas en jj/mm/aaaa (dont %d en etiquette partagee), par ANNEE :"
                     % (len(autres), sum(1 for i in autres if auj[i][0] == "ETIQUETTE_PARTAGEE")))
    lignes_md.append("      %-6s %14s %22s %26s" % ("annee", "par le Sheet", "par nos transactions",
                                                     "dont etiquette partagee"))
    ans = sorted({an_offre(i) for i in autres} | {an_nos_tx(i) for i in autres}, key=lambda y: (y is None, y or 0))
    for y in ans:
        lignes_md.append("      %-6s %14d %22d %26d" % (
            y or "aucune", sum(1 for i in autres if an_offre(i) == y), sum(1 for i in autres if an_nos_tx(i) == y),
            sum(1 for i in autres if an_offre(i) == y and auj[i][0] == "ETIQUETTE_PARTAGEE")))
    accord = sum(1 for i in autres if an_offre(i) and an_nos_tx(i) and an_offre(i) == an_nos_tx(i))
    deux = sum(1 for i in autres if an_offre(i) and an_nos_tx(i))
    lignes_md.append("      les deux sources donnent la MEME annee pour %d des %d lignes ou elles existent toutes les deux"
                     % (accord, deux))
    tout_jj = sum(1 for i in LIG if LIG[i]["row"][i_s].strip() and not jjmm.search(LIG[i]["row"][i_s]))
    lignes_md.append("   sur TOUT le Sheet : %d dates d'offre dans l'autre format, %d vides, %d en jj/mm/aaaa"
                     % (tout_jj, sum(1 for i in LIG if not LIG[i]["row"][i_s].strip()),
                        sum(1 for i in LIG if jjmm.search(LIG[i]["row"][i_s]))))
    lignes_md.append("")
    lignes_md.append("LES LIGNES DU SHEET PAR ANNEE DE L'OFFRE (les deux formats) -- toutes, et les non ecrites :")
    lignes_md.append("      %-6s %8s %10s %10s %8s" % ("annee", "total", "vague 1", "non ecrites", "part"))
    for y in sorted({an_offre(i) for i in LIG}, key=lambda y: (y is None, y or 0)):
        tot = sum(1 for i in LIG if an_offre(i) == y)
        nn = sum(1 for i in ne_ if an_offre(i) == y)
        lignes_md.append("      %-6s %8d %10d %10d %7.0f %%" % (y or "aucune", tot, tot - nn, nn, 100.0 * nn / tot))
    deux_ans = [i for i in LIG if an_offre(i) in (2025, 2026)]
    ne_2 = [i for i in ne_ if an_offre(i) in (2025, 2026)]
    filtre_texte = [i for i in ne_ if "2025" in LIG[i]["row"][i_s] or "2026" in LIG[i]["row"][i_s]]
    tot_texte = [i for i in LIG if "2025" in LIG[i]["row"][i_s] or "2026" in LIG[i]["row"][i_s]]
    lignes_md.append("   2025 + 2026 : %d lignes au Sheet, dont %d NON ECRITES (%d en 2025, %d en 2026)"
                     % (len(deux_ans), len(ne_2), sum(1 for i in ne_2 if an_offre(i) == 2025),
                        sum(1 for i in ne_2 if an_offre(i) == 2026)))
    lignes_md.append("      ton filtre (le texte « 2025 » ou « 2026 » dans la date d'offre) : %d non ecrites sur %d"
                     " -- il manque les %d ecrites « jj mois aa »" % (len(filtre_texte), len(tot_texte),
                                                                       len(ne_2) - len(filtre_texte)))
    lignes_md.append("      les %d non ecrites 2025-2026, par case : %s"
                     % (len(ne_2), " . ".join("%s %d" % kv for kv in Counter(auj[i][0] for i in ne_2).most_common())))

    # ── LE FICHIER DES LIGNES NON ECRITES ──
    def apres_couche(i, n):
        """Ce qu'il faut, et qui agit, pour une ligne d'un groupe de couche n >= 6 -- ALLER AU BOUT (19/11 au soir :
        « pour les 351 qui demandent une scission, et les 16 non tranchees, elle s'arrete a il faudrait couper »)."""
        k = trouve(("L", i))
        if n == 6:
            if i in aucun_tenu:
                return COUCHES[6] + " : le gel relie CETTE ligne a un dossier qu'elle ne designe pas -> je relis, un"                     " patch du gel « V3 » retire le lien (ton accord)", "moi (relecture) puis toi"
            autres_ = sorted(j for j in groupes[k]["lignes"] if j != i and j in aucun_tenu)
            return COUCHES[6] + " : son dossier est partage par un lien SUSPECT du gel (%s) -> quand le patch « V3 »"                 " le retire, elle entre en vague 1" % " ".join(autres_), "moi (relecture) puis toi"
        if n == 7:
            return COUCHES[7], "toi"
        if n == 8:
            ls = sorted(groupes[k]["lignes"])
            viv = [j for j in ls if not est_annulee(j)]
            if len(viv) == 1 and i == viv[0]:
                return COUCHES[8] + " : l'etiquette s'ecrit sur CETTE ligne", "l'outil d'ecriture (decide)"
            if len(viv) == 1:
                return COUCHES[8] + " : cette tentative annulee RESTE VIDE (l'etiquette va sur %s)" % viv[0],                     "personne (decide)"
            return COUCHES[8] + " : %d lignes vivantes dans le groupe -- a relire" % len(viv), "moi (relecture) puis toi"
        if n == 9:
            f_ = famille.get(k, "?")
            g_ = GARDE_RETENUE in mesure_garde and k in resout.get(GARDE_RETENUE, set())
            et_ = coupe_etat.get(k, "?")
            quoi = "%s -- %s -- coupe %s : %s" % (COUCHES[9], FAMILLES.get(f_, f_), et_, coupe.get(k, ""))
            if g_:
                return quoi + " -- ⭐ la garde %s la coupe seule" % GARDE_RETENUE.upper(),                     "la garde %s (ton allumage)" % GARDE_RETENUE.upper()
            if et_ == "NETTE":
                return quoi, "toi : valider la coupe (outil de scission, apres l'ecriture)"
            return quoi, "moi (relecture de la coupe) puis toi"
        if n == 11:
            ex = sorted(a for d in groupes[k]["dossiers"] for a in membres[d] if a in exclues_e)
            return COUCHES[11] + " : %s" % "; ".join("%s -- %s" % (a, al_.EXCLUES_DE_LA_REGLE_E[a][:120])
                                                     for a in ex), "toi"
        return COUCHES[n], "moi (relecture) puis toi"

    def debloque(i):
        if i in reportees_b_set:
            return ("DECISION B du 20/11 : SORT DE LA VAGUE 1 -> VAGUE 2. La garde G2 changerait son etiquette (la "
                    "tentative ratee d'un acheteur precedent, au plus petit numero, garderait celle du dossier) ; G2 se "
                    "code APRES l'ecriture, apres la relecture de ses 281 coupes invisibles (%s)" % SORTIE_B.name,
                    "la garde G2 (apres l'ecriture), puis la vague 2")
        c0 = auj[i][0]
        ex_ =sorted(a for a in gel_v2.get(i, set()) if a in exclues_e)
        if ex_ and all(etats[n][i][0] != "VAGUE_1" for n in (1, 2, 3, 4, 5)):
            return (COUCHES[11] + " : %s" % "; ".join("%s -- %s" % (a, al_.EXCLUES_DE_LA_REGLE_E[a][:140]) for a in ex_),
                    "toi")
        for n in (1, 2, 3, 4, 5):
            if etats[n][i][0] == "VAGUE_1":
                return ("entre en vague 1 apres la couche " + COUCHES[n],
                        "la nuit" if n == 1 else "l'outil d'ecriture (decide)" if n == 5 else "toi")
        c5_ = etats[5][i][0]
        pp = ("PLUSIEURS_DOSSIERS", "ETIQUETTE_PARTAGEE")
        if c0 in pp:
            n, st = couche(i)
            if n <= 5:
                return ("sort de %s par la couche %s, puis reste en %s" % (c0, COUCHES[n], etats[n][i][0]),
                        "toi" if n >= 2 else "la nuit")
            return apres_couche(i, n)
        # une ligne qui n'est pas dans ces deux cases AUJOURD'HUI mais y tombe au bout des couches 1-5
        pre = "" if c5_ == c0 else "au bout des couches 1-5 elle passe en %s ; " % c5_
        if c5_ in pp:
            n = verdict_groupe.get(trouve(("L", i)), 10)
            q_, w_ = apres_couche(i, n)
            return pre + q_, w_
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
    # DECISION B (20/11) : les lignes de la vague 1 d'aujourd'hui que G2 reporte en vague 2 entrent dans le fichier
    en_plus_b = sorted(i for i in reportees_b_set if auj[i][0] == "VAGUE_1")
    print("   + %d ligne(s) de la vague 1 d'aujourd'hui reportee(s) en vague 2 par la decision B (et %d qui n'y etaient"
          " pas encore)" % (len(en_plus_b), len(reportees_b_set) - len(en_plus_b)), flush=True)
    sorties = []
    for i in sorted(non_ecrites + en_plus_b, key=lambda x: LIG[x]["num"]):
        quoi, qui = debloque(i)
        r, ds, ts = auj[i]
        sorties.append({
            "ligne_au_19_11": LIG[i]["num"], "id_unique": i, "case_aujourd_hui": r,
            "case_apres_nuit_et_patch": apr[i][0], "case_au_bout_1_a_5": etats[5][i][0],
            "decision_b_vague_2": "oui" if i in reportees_b_set else "",
            "ce_qui_la_debloque": quoi, "qui": qui,
            **{n: LIG[i]["row"][col(n)] for n in lisibles},
            "dossiers_aujourd_hui": " ".join(map(str, ds)),
            "famille": FAMILLES.get(famille.get(trouve(("L", i)), ""), "") if verdict_groupe.get(trouve(("L", i))) == 9
            else "",
            "la_garde_%s_la_coupe" % GARDE_RETENUE: ("oui" if trouve(("L", i)) in resout.get(GARDE_RETENUE, set()) else "non")
            if verdict_groupe.get(trouve(("L", i))) == 9 else "",
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


# ─────────────────────────── ETAPE 1 bis : LA GARDE « LA DATE BAT LE NOM » (MESURE SEULEMENT) ───────────────────────────
#   Demande de Frederic, 19/11 au soir : « LA GARDE DES 104 : ce qu'elle couperait, et combien de lignes de la
#   VAGUE 1 changeraient d'etiquette si elle jouait. Si elle en touche, elle passe avant l'ecriture comme E. »
#   ⛔ « PAS UNE LIGNE DE CODE DE SCISSION tant que l'ecriture n'est pas finie. La mesure ne casse rien. »
#   -> phase2/sync/affaire_ledger.py N'EST PAS TOUCHE. On en fait une COPIE hors du depot (dans le cache), on y
#      insere la garde a un seul endroit (la regle D, juste avant la reunion), et on rejoue le scenario 3 de ⑥
#      (la nuit des 10 + E avec ses exclusions + les 8 lignes) avec cette copie, sur une base en memoire.
GARDE_ANCRE = "                            # la cible garde le plus petit numero, comme la\n"
GARDE_CODE = '''                            # ─── MESURE SEULEMENT (temps 6, 19/11 au soir) -- LA GARDE « LA DATE BAT LE NOM »
                            #     G1 : un cote a un COMPROMIS VIVANT dont l'acquereur n'est pas dans l'autre cote
                            #     G2 : un cote a une OFFRE ACCEPTEE DATEE dont l'acquereur n'est pas dans l'autre
                            #     Le defaut de Hektor : le contact de l'acheteur precedent reste sur une piece du
                            #     suivant ; la piece est dans le bon dossier PAR SA DATE, et D la recolle PAR LE NOM.
                            if _T6_GARDE:
                                _bloque = False
                                for _x, _y in ((a, b), (b, a)):
                                    _nx = acqs_reels(_x)
                                    _cp, _oa = set(), set()
                                    for _m in membres_de(_y):
                                        if _m[1] == "compromis" and _m[2] not in ETATS_COMPROMIS_MORTS:
                                            _cp |= _m[4]
                                        if _m[1] == "offre" and _m[2] in ETATS_OFFRE_ACCEPTEE and _m[3] is not None:
                                            _oa |= _m[4]
                                    if "G1" in _T6_GARDE and _cp and not (_nx & _cp):
                                        _bloque = True
                                    if "G2" in _T6_GARDE and _oa and not (_nx & _oa):
                                        _bloque = True
                                if _bloque:
                                    signale("[G] garde la date bat le nom -- abstention (MESURE)")
                                    continue
'''
GARDE_VARIANTES = {"g1": "G1", "g2": "G2", "g12": "G1G2"}


def module_avec_la_garde():
    """La copie de affaire_ledger.py avec la garde, chargee comme un module a part. L'original n'est pas touche."""
    source = (RACINE / "phase2" / "sync" / "affaire_ledger.py").read_text(encoding="utf-8")
    n = source.count(GARDE_ANCRE)
    assert n == 1, "l'ancre de la regle D est trouvee %d fois (attendu 1) : le code a bouge" % n
    source = source.replace(GARDE_ANCRE, GARDE_CODE + GARDE_ANCRE)
    for avant, apres in (("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(RACINE)),
                         ('FICHIER_RATTACHEMENTS = Path(__file__).resolve().parent / "rattachements_manuels.csv"',
                          "FICHIER_RATTACHEMENTS = Path(%r)" % str(RACINE / "phase2" / "sync" / "rattachements_manuels.csv"))):
        assert source.count(avant) == 1, "ancre absente : %s" % avant
        source = source.replace(avant, apres)
    ancre_os = "\nimport os  # noqa: E402\n"
    assert source.count(ancre_os) == 1, "import os introuvable"
    source = source.replace(ancre_os, ancre_os + "_T6_GARDE = os.environ.get('T6_GARDE', '')\n", 1)
    copie = CACHE / "affaire_ledger_AVEC_GARDE_mesure_seulement.py"
    copie.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("affaire_ledger_avec_garde", copie)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


JOURNAL_GARDE = CACHE / "garde_journal.txt"


def journal(texte: str) -> None:
    """Chaque ligne va a l'ecran ET dans le journal sur le disque, AU FIL (regle du 19/11 : une mesure longue
    ecrit ses resultats au fil, jamais gardes en memoire jusqu'a la fin -- trois sessions coupees ce soir)."""
    print(texte, flush=True)
    with JOURNAL_GARDE.open("a", encoding="utf-8") as f:
        f.write("%s  %s\n" % (datetime.now().strftime("%H:%M:%S"), texte))


def etape_garde(nom: str) -> int:
    """UN SEUL rejeu par appel : temoin (la copie sans garde = le scenario 3), g1, g2 ou g12."""
    import contextlib
    import io
    import tempfile
    if nom != "temoin" and nom not in GARDE_VARIANTES:
        print("⛔ variante inconnue %r : temoin, %s (code 3)" % (nom, ", ".join(GARDE_VARIANTES)), flush=True)
        return 3
    variante = "" if nom == "temoin" else GARDE_VARIANTES[nom]
    t0 = time.time()
    journal("GARDE %s (%s) : debut" % (nom, variante or "sans garde"))
    if not (CACHE / "chaines_s3.json").exists():
        journal("⛔ chaines_s3.json manque : lancer « rejeu 3 » de temps5_q6 (code 3)")
        return 3
    spec = importlib.util.spec_from_file_location(
        "q6", RACINE / "phase2" / "checks" / "temps5_q6_les_lignes_a_plusieurs_etiquettes_2026-11-19.py")
    q6 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q6)
    alg = module_avec_la_garde()
    journal("   copie de affaire_ledger.py avec la garde chargee (%.0f s)" % (time.time() - t0))
    with tempfile.TemporaryDirectory() as tmp:
        fichier = Path(tmp) / "rattachements_avec_les_huit.csv"
        fichier.write_text(alg.FICHIER_RATTACHEMENTS.read_text(encoding="utf-8-sig") + q6.LES_HUIT, encoding="utf-8")
        alg.FICHIER_RATTACHEMENTS = fichier
        os.environ["APP_CHAINAGE_SANS_DATE_VISIBLE"] = "1"
        alg._T6_GARDE = variante
        try:
            con = q6.copie()
            journal("   base copiee en memoire (%.0f s) -- rejeu du chainage..." % (time.time() - t0))
            with contextlib.redirect_stdout(io.StringIO()):
                res = alg.recalculer_les_chaines(con)
            ch = {str(a): c for a, c in con.execute("SELECT app_affaire_id, app_chaine_id FROM %s" % alg.LEDGER_TABLE)}
        finally:
            os.environ.pop("APP_CHAINAGE_SANS_DATE_VISIBLE", None)
    # ⚠ « abstentions » compte des PASSAGES (la boucle de D repart a zero apres chaque reunion) : le vrai compte
    #   des dossiers coupes se fait dans « classer », en comparant les chaines.
    compte = {"dossiers": len(set(ch.values())),
              "abstentions_g": res.get("[G] garde la date bat le nom -- abstention (MESURE)", 0),
              "reunions_d": res.get("[D] meme acheteur, meme bien -- dossiers reunis", 0),
              "le": datetime.now().isoformat(timespec="seconds")}
    if nom == "temoin":
        s3 = lire_json(CACHE / "chaines_s3.json")
        compte["ecart_avec_s3"] = sum(1 for a in s3 if s3[a] != ch.get(a))
        journal("   TEMOIN : la copie SANS garde redonne le scenario 3 -- %d transaction(s) differente(s) (attendu 0)"
                % compte["ecart_avec_s3"])
    else:
        ecrire_json(CACHE / ("chaines_%s.json" % nom), ch)
    comptes = lire_json(CACHE / "garde_comptes.json") if (CACHE / "garde_comptes.json").exists() else {}
    comptes[nom] = compte
    ecrire_json(CACHE / "garde_comptes.json", comptes)
    journal("GARDE %s : %d dossiers ; reunions D %s ; passages bloques %s -- FIN en %.0f s"
            % (nom, compte["dossiers"], compte["reunions_d"], compte["abstentions_g"], time.time() - t0))
    if nom == "temoin" and compte["ecart_avec_s3"]:
        journal("⛔ la copie ne rejoue pas comme l'original (code 2)")
        return 2
    return 0


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "photo":
        return etape_photo()
    if len(sys.argv) >= 3 and sys.argv[1] == "garde":
        return etape_garde(sys.argv[2])
    if len(sys.argv) >= 2 and sys.argv[1] == "classer":
        return etape_classer()
    print(__doc__)
    return 3


if __name__ == "__main__":
    sys.exit(main())
