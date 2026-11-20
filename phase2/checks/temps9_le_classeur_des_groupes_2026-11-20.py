"""Chantier classeur, ⑮ -- LE CLASSEUR DES GROUPES : ce qui attend une DECISION de Frederic, UNE LIGNE PAR GROUPE.

Lecture seule (la photo du 19/11 20:09, l'export de temps6, le registre local en mode=ro, les CSV de notice/).
Sortie : notice/TEMPS9_LE_CLASSEUR_DES_GROUPES_2026-11-20.xlsx (a ouvrir) et .csv (suivi par git).

Ce qui N'Y EST PLUS, parce que regle le 20/11 : les 110 liens « a valider » et les 28 « audit non juste » (V2 et le
patch « confiance » joues) ; les 132 coupes datees (VALIDEES) ; M2G1Z1K8 (on ne l'ecrit pas).
Ce qui reste, par section, dans l'ordre ou ca DEBLOQUE LE PLUS de lignes :
  1 les 29 coupes « nom seul / case vide »      (ma relecture faite)
  2 les 13 coupes disputees et les 8 a completer (ma relecture faite)
  3 tes questions ouvertes                        (la proposition de l'audit, contre-expertisee)
  4 la reparation des 19                          (la piece que la date de ton classeur designe)
  5 les 8 lignes « pures » de 5.6
  6 les 7 reunions (couche 7)
  7 la relecture du gel (couche 6) et 8 « gel seul » : MA relecture d'abord -- listees pour que tu voies le volume.

Usage : python -u phase2/checks/temps9_le_classeur_des_groupes_2026-11-20.py
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_simple import ecrire_xlsx  # noqa: E402

CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache")
N = RACINE / "notice"
SORTIE_XLSX = N / "TEMPS9_LE_CLASSEUR_DES_GROUPES_2026-11-20.xlsx"
SORTIE_CSV = N / "TEMPS9_LE_CLASSEUR_DES_GROUPES_2026-11-20.csv"

# ── MA RELECTURE, groupe par groupe (20/11 apres-midi) : (recommandation, pourquoi) ──
RECO = {
    # 1 -- les 29 coupes « nom seul / case vide »
    "D:1059": ("OUI", "1059 (annule) porte ZOUNIB et 195 000 = son offre. G2 fait la meme coupe."),
    "D:15095": ("OUI", "15096 sans date porte MORELA et 60 000 = son offre. G2 fait la meme coupe."),
    "D:16015": ("NON -- prendre la coupe de G2",
                "Le compromis actif 16015 (10/03/2025) et la vente 16019 (10/06/2025), a 11 000 = le prix de "
                "WENDLINGER, viennent APRES son offre du 09/12/2024 : ils sont a WENDLINGER, le nom AZOUGUI y est "
                "reste (le defaut de Hektor). AZOUGUI ne garde que son offre 16017 (15 000). G2 coupe deja ainsi."),
    "D:16113": ("OUI", "16114 sans date porte BERTHET et 200 000 = son offre. G2 fait la meme coupe."),
    "D:16336": ("OUI", "16336 sans date porte LAMI et 150 000 = son offre. G2 fait la meme coupe."),
    "D:16382": ("A TOI",
                "Le compromis annule 16378 du 13/02/2021 (244 000) porte DU PELOUX, mais il precede de deux mois "
                "l'offre de DU PELOUX (23/04/2021) et son montant tombe entre DUPONT-PIPPIA (249 000) et DU PELOUX "
                "(237 000). Ma lecture : DUPONT-PIPPIA, apres renegociation. Ton classeur sait-il ?"),
    "D:17131": ("OUI (faible)", "17131 sans date porte GALLONET ; 47 500 ne colle a personne (GALLONET 38 000, "
                                "MASSARDIER 37 000) mais aucune autre ligne ne peut le prendre. G2 fait la meme coupe."),
    "D:17422": ("OUI", "17422 sans date porte DESCOURS et 230 000 = son offre. G2 fait la meme coupe."),
    "D:19071": ("OUI", "19070 sans date porte POCHELON et 159 000 = son offre ; 19069 (15/03/2024, 160 000) a la date "
                       "et l'offre de FANGET. G2 ne coupe pas ce groupe : c'est l'outil."),
    "D:20264": ("ATTENDRE -- lie aux 19",
                "Le compromis 20264 (15/04/2024, 324 000) porte PINET, mais la DATE de ton classeur le donne a "
                "EO8MXFE9 (MARTIN COTTIER), une des 19 lignes sorties de la vague 1 : il se tranche avec elle (section 4)."),
    "D:21615": ("OUI", "21616 (24/06/2020) porte TOURON et 50 000 = son offre. G2 fait la meme coupe."),
    "D:23475": ("OUI", "23475 sans date porte BRUNON et 60 000 = son offre. G2 fait la meme coupe."),
    "D:24588": ("OUI", "L'offre 24591 de DENAUX (29/08/2019 ; ton classeur : 29/09, un mois d'ecart) est a 19 200 = son "
                       "compromis. G2 fait la meme coupe."),
    "D:26033": ("OUI", "26034 sans date porte BELIBI et 55 500 = son offre. G2 fait la meme coupe."),
    "D:27100": ("OUI", "27100 (25/04/2025, 225 000) = l'offre de CHEREAU ; 27101 (21/01/2025) = la date du compromis de "
                       "LACHAL. G2 ne coupe pas : c'est l'outil."),
    "D:27133": ("A TOI", "La 15e du tirage : deux compromis annules SANS date (94 000, 90 000) au nom ALONSO. Ma lecture : "
                         "ALONSO, qui a offert 98 000 puis renegocie, avant DE MATOS a 89 000. Plausible, pas prouve."),
    "D:27554": ("OUI", "L'offre 27556 de GARRY (23/05/2020 ; ton classeur : 25/05) a 118 000 = ton prix. G2 fait la meme coupe."),
    "D:28268": ("OUI", "28269 sans date porte OZEL et 24 000 = son offre. G2 fait la meme coupe."),
    "D:4177": ("OUI", "4178 sans date porte RUFFO et 105 400 = son offre. G2 fait la meme coupe."),
    "D:4480": ("ATTENDRE -- une question ouverte", "Les pieces de VIALLARD sont l'objet de tes questions 3308P0UX et "
                                                   "9WQ204HP (VIALLARD saisie deux fois) : la coupe attend leur reponse."),
    "D:4500": ("OUI", "4500 sans date porte SANLAVILLE et 31 000 = son offre. G2 fait la meme coupe."),
    "D:4533": ("OUI", "4533 sans date porte COULON ; meme prix (99 000) des deux cotes, le nom departage. G2 fait la meme coupe."),
    "D:4541": ("ATTENDRE -- une question ouverte", "Le compromis 4542 est l'objet de ta question RGCEC677 (section 3)."),
    "D:4621": ("NON -- 4621 va a PLE",
               "Le compromis annule 4621 (sans date) est a 50 000 = le prix de PLE ; SASSI a offert 53 000, et son nom "
               "est aussi sur le compromis actif de PLE (le defaut de Hektor). Ma lecture : une premiere signature de "
               "PLE. Dis-moi si ton classeur dit autre chose."),
    "D:4649": ("A TOI", "Deux compromis annules au nom DUVET : 4649 (22/01/2021, 32 000) et 4651 (sans date, 31 000). Ils "
                        "precedent l'offre d'OSTRE-OLIVIERI (11/03/2021, 32 000) ; DUVET avait offert 36 200. Ma lecture : "
                        "DUVET apres renegociation."),
    "D:4660": ("OUI", "4661 sans date porte THIBAULT et 10 000 = son offre. G2 fait la meme coupe."),
    "D:4857": ("OUI", "4858 sans date porte MONTEILHET et 22 000 = son offre. G2 fait la meme coupe."),
    "D:7448": ("OUI", "7449 (11/06/2020) = la date du compromis de GUERIN ; 7450 sans date et 7453 au meme montant "
                      "(143 000), meme nom. G2 fait la meme coupe."),
    "D:7710": ("OUI", "7710 sans date porte GRATALOUP ; meme prix (135 000) des deux cotes, le nom departage. G2 fait la meme coupe."),
    # 2 -- les 13 disputees
    "D:14109": ("OUI", "La vente 14115 (113 000) va a BLANC-MOURETTE, la ligne « Vente reglee » ; 14110 sans date, au nom "
                       "GENOUX, meme prix, va a GENOUX. G2 ne coupe pas : c'est l'outil."),
    "D:17408": ("OUI", "La vente 17412 va a GOURLET, la ligne « Vente reglee » (65 000)."),
    "D:19094": ("OUI", "La vente 19098 va a RAULT-BOUE, la ligne « Vente reglee »."),
    "D:19140": ("OUI", "Le compromis 19140 (07/09/2020) et la vente 19143 vont a JIBERT-VALLA, la ligne « Vente reglee »."),
    "D:22207": ("OUI", "La vente 22211 va a LOUVAT-COUCHOUD, la ligne « Vente reglee » (132 000)."),
    "D:23995": ("OUI", "La vente 23997 va a MARTINEZ, la ligne « Vente reglee » ; V2 a deja rendu l'offre 23995 a MARTINEZ."),
    "D:24281": ("OUI", "La vente 24285 va a BUFFERNE, la ligne « Vente reglee »."),
    "D:24319": ("OUI", "La vente 24323 va a FIARD, la ligne « Vente reglee » ; l'offre acceptee 24321 porte son nom."),
    "D:24399": ("OUI", "La vente 24402 va a CONTE, la ligne « Vente reglee »."),
    "D:24494": ("OUI", "La vente 24498 va a PESTRE, la ligne « Vente reglee »."),
    "D:27426": ("OUI", "La vente 27429 va a BARBRY, la ligne « Vente reglee »."),
    "D:4560": ("OUI", "La vente 4564 va a KUZNIAR KROLL-RABOTIN, la ligne « Vente reglee » ; 4560 sans date, au nom LOUIS "
                      "ET DJIKSTRA, va a DJIKSTRA."),
    "D:6556": ("OUI", "Deux compromis le meme jour (30/04/2021) : 6555 a 87 000 = le prix de GLAZIOU (« Vente reglee »), "
                      "6554 a 90 000 = l'offre de BARDY. C'est ce que V2 a deja pose au gel."),
    # 2 -- les 8 a completer
    "D:11515": ("OUI", "Le compromis annule 11516 (14/03/2023, 260 000, contact DELORME) va a NHF INVEST-DELORME : son nom "
                       "et le montant de son offre."),
    "D:17435": ("OUI", "L'offre 17436 du 17/04/2024 (THOMAS) va a THOMAS : le jour meme de son compromis."),
    "D:24123": ("OUI", "L'offre acceptee 24124 (17/04/2023, 11 800) va a COLAVITTI, l'acheteur (« Vente reglee »)."),
    "D:24445": ("OUI", "L'offre acceptee 24446 (30/11/2020, COLLART) va a COLLARD (« Vente reglee »)."),
    "D:24511": ("OUI", "L'offre acceptee 24513 (15/07/2020, 129 000 = le prix de CHABROT, contact LAPRET) va a CHABROT "
                       "(« Vente reglee »)."),
    "D:24598": ("OUI -- un 3e dossier", "L'offre et le compromis d'ISSARTEL de 2019 (39 000) n'ont AUCUNE ligne dans ton "
                                        "classeur : ils forment leur propre dossier, ni PENY ni CRISCOLO."),
    "D:27239": ("OUI", "27240 sans date porte LAURENT et 160 000 = son offre."),
    "D:4669": ("OUI", "4670 (05/09/2022) = le compromis de REID (ton classeur : 05/09/2021, une faute d'annee) ; 4669 sans "
                      "date, au nom ELMAROUFI, va a EL MAROUFI."),
}

LES_8 = [  # notice/CHANTIER_CLASSEUR_TEMPS4_5_FINIR_2026-11-19.md § 5.6
    ("566d1a48", "988 -> 987", "EL FAQRAOUI : offre (sans acquereur chez Hektor) du 27/06/2025 et compromis, 66 000"),
    ("VUNYM8UV", "4907 -> 4906", "VIALLE : offre du 04/07/2020 et compromis du 25/09/2020 (au nom de MEYRAND), 16 000"),
    ("NTLQIZLO", "4932 -> 4931", "URBAIN : offre du 15/06/2019 et compromis du 01/08/2019 (au nom de PLAY), 119 000"),
    ("7PBRZJD8", "7600 -> 7599", "GASMI : offre (sans acquereur) du 05/06/2023 et compromis du 17/07/2023, 330 000"),
    ("05e8ddb5", "14928 -> 14927", "BEZIER GUILLEMIN : offre (sans acquereur) et compromis sans date, 120 000"),
    ("80OY9IUH", "16879 -> 16878", "BOUCHARD : offre du 29/11/2019 et compromis du 18/05/2020 (au nom de CHARRA MEILLER), 58 000"),
    ("26283bf9", "21799 -> 21798", "BESSET : offre (sans acquereur) et compromis du 10/11/2025, 56 000"),
    ("600f4e1c", "25992 -> 25991", "MAGAND : offre (sans acquereur) et compromis du 10/12/2025, 153 000"),
]


def lire(p: Path, sep=";"):
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=sep))


def main() -> int:
    P = json.loads((CACHE / "t6_photo.json").read_text(encoding="utf-8"))
    LIG, TX = P["lignes"], {int(a): v for a, v in P["tx"].items()}
    E = json.loads((CACHE / "t7_export_coupes.json").read_text(encoding="utf-8"))
    G = E["groupes"]
    S3 = {int(a): c for a, c in json.loads((CACHE / "chaines_s3.json").read_text(encoding="utf-8")).items()}
    G2 = {int(a): c for a, c in json.loads((CACHE / "chaines_g2.json").read_text(encoding="utf-8")).items()}
    par_dossier = defaultdict(list)
    for a, d in S3.items():
        par_dossier[d].append(a)
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    les803 = {r["id_unique"]: r for r in lire(N / "TEMPS6_LES_803_LIGNES_NON_ECRITES_ET_CE_QUI_LES_DEBLOQUE_2026-11-19.csv")}
    V18 = {r["id_unique"]: r for r in lire(N / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv")}
    les19 = lire(N / "TEMPS7_DECISION_DU_20_11_LES_19_HORS_DE_LA_VAGUE_1_2026-11-20.csv")
    t7 = {r["id_unique"]: r for r in lire(N / "TEMPS7_EFFET_DES_COUPES_SUR_LA_VAGUE_1_2026-11-20.csv") if r["etat"] == "reference"}

    def tx_txt(a):
        r = con.execute("select kind, state, date, montant, acquereur_json, transaction_origine from app_affaire_ledger "
                        "where app_affaire_id=?", (a,)).fetchone()
        if not r:
            return "%d (absente du registre)" % a
        try:
            nom = (json.loads(r[4] or "{}") or {}).get("nom") or "sans contact"
        except ValueError:
            nom = "?"
        date = (r[2] or "")[:10]
        date = "sans date" if date in ("", "0000-00-00") else "%s/%s/%s" % (date[8:10], date[5:7], date[:4])
        m = (r[3] or "").split(".")[0]
        return "%d %s %s du %s, %s EUR, contact %s%s" % (a, r[0], {"cancelled": "annule", "refused": "refusee",
                                                                    "accepted": "acceptee", "active": "actif"}.get(r[1], r[1] or ""),
                                                          date, m or "?", nom, " (copie C5)" if r[5] == "classeur" else "")

    def ligne_txt(i):
        if i not in LIG:
            return i
        r = LIG[i]["row"]
        return "%s (n° %s) %s · offre %s · compromis %s · %s · prix %s" % (
            i, LIG[i]["num"], r[17], r[18] or "-", r[19] or "-", (r[27] or "").replace("nan ", "").strip(), r[31] or "-")

    groupes = []   # dict par groupe

    def ajouter(section, cle, lignes, txs, ce_qui_est_propose, reco, pourquoi, qui_apres, g2=""):
        groupes.append({"section": section, "groupe": cle, "lignes": lignes, "n": len(lignes),
                        "lignes_txt": "\n".join(ligne_txt(i) for i in lignes),
                        "tx_txt": "\n".join(tx_txt(a) for a in sorted(txs)),
                        "proposition": ce_qui_est_propose, "g2": g2, "reco": reco, "pourquoi": pourquoi,
                        "qui": qui_apres})

    def g2_meme(g):
        txs = sorted({a for d in g["dossiers"] for a in par_dossier[d]})
        part = defaultdict(set)
        for a in txs:
            part[G2.get(a)].add(a)
        cl = defaultdict(set)
        for a, i in g["proprio"].items():
            cl[i].add(int(a))
        attr = {int(a) for a in g["proprio"]}
        return (sorted(map(sorted, cl.values())) ==
                sorted(map(sorted, [v & attr for v in part.values() if v & attr]))), txs

    # 1 et 2 -- les coupes faibles, disputees, a completer
    for cle, g in sorted(G.items()):
        if g["verdict"] != 9:
            continue
        faible = g["coupe_etat"] == "NETTE" and ("[nom seul]" in (g["coupe"] or "") or "[case vide]" in (g["coupe"] or ""))
        if not (faible or g["coupe_etat"] in ("DISPUTEE", "A COMPLETER")):
            continue
        meme, txs = g2_meme(g)
        sec = "1 COUPE A PIECE « NOM SEUL / CASE VIDE »" if faible else "2 COUPE %s" % g["coupe_etat"]
        reco, pq = RECO[cle]
        ajouter(sec, cle, sorted(g["lignes"]), txs, "%s -- famille %s" % (g["coupe"], g["famille"]), reco, pq,
                "l'outil de coupe (ton allumage)" if not meme else "G2 (ton allumage) -- elle fait la meme coupe",
                "oui" if meme else "non")

    # 3 -- tes questions ouvertes
    for i, r in sorted(les803.items()):
        t = r["ce_qui_la_debloque"]
        if r["qui"] != "toi" or not ("ta question" in t or "en attente de ta reponse" in t or "sortie du patch" in t):
            continue
        v = V18.get(i, {})
        prop = (v.get("correction_contre_expert") or v.get("conclusion_contre_expert") or "").strip()
        if i in ("P252U1JH", "XC761R8Z"):
            reco, pq = ("REGLEE PAR LA PIECE 4126/4496", "Ton « oui sur le fond » du 20/11 (4496 -> BISCH, la preuve "
                        "155 000 contre 159 000 ; 4126 -> GAIGA) : elle s'ecrira apres la nuit de la piece.")
        elif i in ("3308P0UX", "9WQ204HP"):
            reco, pq = ("A TOI", "VIALLARD saisie deux fois : ta reponse regle aussi la coupe D:4480 (section 1).")
        elif i == "RGCEC677":
            reco, pq = ("A TOI", "Ta reponse sur 4542 regle aussi la coupe D:4541 (section 1).")
        else:
            reco, pq = ("A TOI", "La proposition de l'audit, contre-expertisee, est a cote.")
        ajouter("3 TES QUESTIONS OUVERTES", i, [i], [int(a) for a in re.findall(r"(\d+)\(", r["transactions_et_genre"])],
                re.sub(r"^.*?(ta question : |en attente de ta reponse[^:]*: |sortie du patch V2 \(SORTIE\) : )", "", t)[:900]
                + ("\n-- L'AUDIT PROPOSE : " + prop[:700] if prop else ""), reco, pq, "toi, puis moi (la ligne du fichier)")

    # 4 -- la reparation des 19
    paires = {}
    for r in les19:
        i = r["id_unique"]
        cle = "19:" + "/".join(sorted([i] + ([r["paire"].replace("avec ", "")] if r["paire"] else [])))
        paires.setdefault(cle, []).append(r)
    for cle, rs in sorted(paires.items()):
        ids = sorted(r["id_unique"] for r in rs)
        txs = set()
        props = []
        for r in rs:
            x = t7.get(r["id_unique"], {})
            txs |= {int(a) for a in x.get("transactions_du_dossier", "").split()}
            txs |= {int(a) for a in re.findall(r"(\d+)\(", x.get("entrantes", "") + " " + x.get("sortantes", ""))}
            if x.get("entrantes"):
                props.append("%s : y RATTACHER %s" % (r["id_unique"], x["entrantes"]))
            if x.get("sortantes"):
                props.append("%s : en SORTIR %s" % (r["id_unique"], x["sortantes"]))
        nat = rs[0]["nature"]
        pq = rs[0]["la_piece_en_cause"]
        if "EO8MXFE9" in ids:
            pq += " -- c'est elle qui regle aussi la coupe D:20264 (section 1)."
        reco = "OUI" if nat.startswith("a") else "OUI (a toi de confirmer)"
        ajouter("4 LA REPARATION DES 19", cle, ids, txs, "%s -- %s" % (nat, " ; ".join(props)), reco,
                pq + {"a": " La date de ton classeur et le montant designent la piece.",
                      "b": " La date de ton classeur designe la piece.",
                      "c": " La date de ton classeur designe la piece ; le contact differe (deux fiches)."}[nat[0]],
                "moi (un rattachement ou une coupe), ton allumage")

    # 5 -- les 8 lignes « pures »
    for i, paire, txt in LES_8:
        a, b = paire.split(" -> ")
        ajouter("5 LES 8 LIGNES « PURES » (§ 5.6)", i, [i], {int(a), int(b)}, "rattacher %s a %s : %s" % (a, b, txt),
                "OUI", "Rejouees le 19/11 avec E : les 8 reunissent bien 8 dossiers (11 546 -> 11 538), pas un de plus.",
                "moi (le fichier des rattachements), ton allumage")

    # 6 -- les 7 reunions
    for cle, g in sorted(G.items()):
        if g["verdict"] != 7:
            continue
        txs = sorted({a for d in g["dossiers"] for a in par_dossier[d]})
        autres = sorted({j for a in txs for j in TX.get(a, {}).get("designe", []) if j not in g["lignes"]})
        reco = "OUI" if not autres else "A TOI"
        pq = ("Toutes les pieces de ces dossiers sont designees par cette ligne seule (ou par personne) : une meme "
              "affaire, coupee en deux dossiers chez nous." if not autres else
              "D'autres lignes designent aussi ces pieces : %s." % " ".join(autres))
        ajouter("6 LES 7 REUNIONS (couche 7)", cle, sorted(g["lignes"]), txs,
                "reunir les dossiers %s" % " + ".join(map(str, g["dossiers"])), reco, pq,
                "moi (le fichier des rattachements), ton allumage")

    # 7 et 8 -- MA relecture d'abord
    for i, r in sorted(les803.items()):
        if r["qui"] == "moi (relecture) puis toi":
            sec = "7 LA RELECTURE DU GEL (couche 6) -- MOI D'ABORD"
        elif r["case_au_bout_1_a_5"] == "GEL_SEUL" and i != "d2108609":
            sec = "8 « GEL SEUL » -- MOI D'ABORD"
        else:
            continue
        ajouter(sec, i, [i], [int(a) for a in re.findall(r"(\d+)\(", r["transactions_et_genre"])],
                r["ce_qui_la_debloque"][:600], "MA RELECTURE D'ABORD", "Je te les rends relues, avec une recommandation.",
                "moi, puis toi (un patch du gel V3)")

    # ── le compte, et l'ordre ──
    par_sec = defaultdict(lambda: [0, 0, Counter()])
    for g in groupes:
        s = par_sec[g["section"]]
        s[0] += 1
        s[1] += g["n"]
        s[2][g["reco"].split(" --")[0].split(" (")[0]] += 1
    entete = ["ordre", "section", "groupe", "lignes du Sheet", "nb de lignes", "ce que dit ton classeur (les lignes)",
              "nos transactions (genre, etat, date, montant, contact chez Hektor)", "ce qui est propose",
              "G2 fait la meme coupe", "MA RECOMMANDATION", "pourquoi", "qui agit apres", "TA DECISION (OUI / NON / un mot)"]
    lignes = [entete]
    for k, g in enumerate(sorted(groupes, key=lambda g: (g["section"], -g["n"], g["groupe"])), 1):
        lignes.append([k, g["section"], g["groupe"], " ".join(g["lignes"]), g["n"], g["lignes_txt"], g["tx_txt"],
                       g["proposition"], g["g2"], g["reco"], g["pourquoi"], g["qui"], ""])
    resume = [["section", "groupes", "lignes debloquees", "mes recommandations", "qui decide", "par ou commencer"]]
    resume.append(["DEJA DECIDE, A ALLUMER : G2", "98 groupes", "198 + les 9 de B", "-", "ton « vas-y » d'allumage",
                   "le plus gros paquet : un mot, avec son compte avant"])
    resume.append(["DEJA DECIDE, A ALLUMER : l'outil de coupe avec les 132 coupes datees", "132 coupes", 274, "-",
                   "ton « vas-y » d'allumage", "avec G2 (60 de ces coupes, G2 les fait seule)"])
    for s in sorted(par_sec):
        n_g, n_l, rc = par_sec[s]
        resume.append([s, n_g, n_l, " ; ".join("%s %d" % kv for kv in rc.most_common()),
                       "MOI d'abord" if "MOI D'ABORD" in s else "toi", ""])
    ordre = sorted((r for r in resume[3:] if r[4] == "toi"), key=lambda r: -r[2])
    for k, r in enumerate(ordre, 1):
        r[5] = "%d%s" % (k, " -- ⭐ le plus de lignes" if k == 1 else "")
    resume.append(["", "", "", "", "", ""])
    resume.append(["UN MOT PAR SECTION SUFFIT", "", "", "« OUI a tes recommandations de la section N, sauf X et Y » "
                   "-- je relis tes reponses par un script : elles deviennent les lignes des fichiers, sans retaper.", "", ""])
    ecrire_xlsx(SORTIE_XLSX, [("PAR OU COMMENCER", resume, [62, 14, 16, 46, 22, 30]),
                              ("LES GROUPES", lignes, [6, 30, 20, 22, 8, 60, 70, 70, 10, 26, 70, 28, 26])])
    with SORTIE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        for l in lignes:
            w.writerow([str(x).replace("\n", " | ") for x in l])
    for r in resume:
        print(" | ".join(str(x) for x in r), flush=True)
    print("ECRIT : %s et %s (%d groupes)" % (SORTIE_XLSX.name, SORTIE_CSV.name, len(groupes)), flush=True)
    manque = [k for k in RECO if k not in {g["groupe"] for g in groupes}]
    if manque:
        print("⛔ recommandations sans groupe : %s" % manque, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
