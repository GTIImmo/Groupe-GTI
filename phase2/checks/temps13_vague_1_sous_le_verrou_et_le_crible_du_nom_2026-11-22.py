"""Chantier classeur, ⑲ (22/11/2026) -- LA VAGUE 1 SOUS SON VERROU, ET LE CRIBLE DU NOM.     LECTURE SEULE.

Son mot du 22/11, point 6 : « 2. Le controle du defaut du nom sur la vague 1, en lecture seule. Tu l'as annonce deux
fois et il n'est pas fait. Tant qu'il n'est pas fait, la vague 1 n'existe pas pour moi. 3. Le classement recalcule,
pour sortir mes 9 lignes de la vague 1 : tu dis que les 8 dossiers encore partages apres la V3 en sortiront, mais tu
ne l'as pas refait. »

CE QUE CE SCRIPT FAIT -- il n'ecrit RIEN, ni dans le Sheet (un GET), ni en base (mode=ro, et le pooler en read only) :
  1. relit le Sheet EN DIRECT et le compare a la photo du 19/11 (celle d'« ou ca tombe ») sur les colonnes de preuve ;
  2. REFAIT LE CLASSEMENT du 19/11 (temps5_q8, meme ordre de raisons) avec DEUX changements, et rien d'autre :
       a. SON VERROU AVANT TOUT (son point 3 du 21/11) : une ligne dont le dossier porte une autre de ses lignes n'entre
          jamais dans une vague -- sauf une EXCEPTION NOMMEE (son mot du 22/11, point 3), sautee EN LA NOMMANT ;
       b. LE CRIBLE DU NOM (§ 18.2 a) : chaque transaction Hektor que le gel donne a la ligne est jugee par la PREUVE
          INTERNE (coupe_preuve_interne : la date au jour exact, ou le prix + les honoraires ; le nom JAMAIS) ;
     sur deux etats : AUJOURD'HUI (gel vivant, chaines de production) et APRES LA V3 (le gel V3 et les chaines du rejeu
     V3 -- celles de temps12, refaites ce matin) ;
  3. dit ou tombent SES 9 LIGNES (son verrou du 21/11), et compare a la vague 1 que l'ecrivain lit aujourd'hui (le
     classement du 19/11, case VAGUE_1, moins la decision B et les 19).

Sorties : notice/TEMPS13_VAGUE_1_SOUS_LE_VERROU_ET_LE_CRIBLE_DU_NOM_2026-11-22.csv, et le journal du chantier.
Codes : 0 mesure faite . 2 un temoin a echoue . 3 une lecture a rate (jamais un vert).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import coupe_preuve_interne as K  # noqa: E402


def _module(nom: str, fichier: str):
    spec = importlib.util.spec_from_file_location(nom, Path(__file__).resolve().parent / fichier)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V3 = _module("t12", "temps12_v3_fabriquer_2026-11-22.py")          # pooler, EXCEPTIONS_NOMMEES, le cache
JUGE = _module("juge_q5", "temps5_q5_les_48_a_juger_par_le_classeur_2026-11-19.py")
CACHE = K.CACHE
BASE = RACINE / "phase2" / "phase2.sqlite"
NOTICE = RACINE / "notice"
SORTIE = NOTICE / "TEMPS13_VAGUE_1_SOUS_LE_VERROU_ET_LE_CRIBLE_DU_NOM_2026-11-22.csv"
CLASSEMENT_19_11 = NOTICE / "TEMPS5_Q8_LES_LIGNES_DU_SHEET_ET_LEUR_VAGUE_2026-11-19.csv"
DECISION_B = NOTICE / "TEMPS6_DECISION_B_LIGNES_REPORTEES_EN_VAGUE_2_PAR_G2_2026-11-20.csv"
DECISION_19 = NOTICE / "TEMPS7_DECISION_DU_20_11_LES_19_HORS_DE_LA_VAGUE_1_2026-11-20.csv"
VERDICTS = NOTICE / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"
OPERATIONS = NOTICE / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv"
SES_9 = ["86ad8c0f", "SC58GWXX", "205f62be", "XBGMB7XP", "WO5IQTLW", "C6XFV1E5", "ccbbf3c8", "5f47de79", "beeaf847"]
NON_ECRITES = {"SBH4QWDW", "XHITO8HE", "SHN6RKDI", "d2108609", "ea6a28a7", "HUY49KEC"}   # « ou ca tombe », 6
COLS_PREUVE = ["Mandat", "Prix", "Commission TTC", "Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée",
               "Vente Réglée", "Signée", "Annulée", "Lien CRM", "Acquéreur", "product_ref"]
ORDRE = ["A_DEJA_REMPLIE", "SANS_LIEN", "VERROU_DEUX_LIGNES", "PLUSIEURS_DOSSIERS", "EN_ATTENTE", "DECISION_B",
         "DECISION_19", "NON_ECRITE_OU_CA_TOMBE", "LIEN_A_VALIDER", "AUDIT_NON_JUSTE", "C5_SEULE", "GEL_SEUL",
         "NOM_CONTREDITE", "NOM_CONFLIT", "NOM_SANS_PREUVE", "VAGUE_1"]


def dire(s: str = "") -> None:
    V3.dire(s)


def ids_csv(p: Path, col: str = "id_unique") -> set:
    with p.open(encoding="utf-8-sig") as f:
        t = f.read()
    sep = ";" if t.splitlines()[0].count(";") > t.splitlines()[0].count(",") else ","
    return {r[col].strip() for r in csv.DictReader(t.splitlines(), delimiter=sep) if r.get(col, "").strip()}


def main() -> int:
    t0 = datetime.now()
    dire("VAGUE 1 SOUS LE VERROU + CRIBLE DU NOM (lecture seule) : debut")
    # ── 1. LE SHEET EN DIRECT (un GET), contre la photo du 19/11 ───────────────────────────────────────────────────
    JUGE.ac.MORCEAUX_DE_NOM = True
    JUGE.ac.load_env_file(RACINE / ".env")
    try:
        entete, lignes = JUGE.ac.lire_classeur()
    except Exception as e:  # noqa: BLE001
        dire("⛔ le Sheet n'a pas pu etre lu (%s) -- PAS de mesure (code 3)" % str(e).splitlines()[0][:120])
        return 3
    P = json.loads((CACHE / "t6_photo.json").read_text(encoding="utf-8"))
    if entete != P["entete"]:
        dire("⛔ l'en-tete du Sheet a bouge depuis la photo -- PAS de mesure (code 3)")
        return 3
    k_al, k_a = entete.index("ID Unique"), 0
    vivant, doublons, col_a = {}, Counter(), {}
    for num, l in lignes:
        l = list(l) + [""] * (len(entete) - len(l))
        i = str(l[k_al]).strip()
        if not i:
            continue
        doublons[i] += 1
        if i not in vivant:
            vivant[i] = {"num": num, "row": l}
            col_a[i] = str(l[k_a]).strip()
    dbl = sorted(i for i, n in doublons.items() if n > 1)
    idx = [entete.index(c) for c in COLS_PREUVE]
    bouge = sorted(i for i in vivant if i in P["lignes"] and
                   [str(vivant[i]["row"][k]).strip() for k in idx] !=
                   [str((P["lignes"][i]["row"] + [""] * 40)[k] or "").strip() for k in idx])
    neuves, parties = sorted(set(vivant) - set(P["lignes"])), sorted(set(P["lignes"]) - set(vivant))
    dire("   Sheet lu en direct : %d lignes (ID Unique en double : %d %s) ; contre la photo du %s : colonnes de preuve "
         "changees sur %d lignes, %d neuves, %d parties ; colonne A deja remplie : %d"
         % (len(vivant), len(dbl), dbl[:5], P.get("lu_le"), len(bouge), len(neuves), len(parties),
            sum(1 for v in col_a.values() if v)))
    # la photo DU JOUR (le crible juge le Sheet tel qu'il est), dans un dossier temporaire -- la photo du 19/11 reste
    vive = {"lu_le": datetime.now().isoformat(timespec="seconds"), "entete": entete,
            "lignes": {i: {"num": v["num"], "row": v["row"]} for i, v in vivant.items()}, "tx": P["tx"], "gel": []}
    tmp = Path(tempfile.mkdtemp(prefix="t13_"))
    (tmp / "t6_photo.json").write_text(json.dumps(vive, ensure_ascii=False), encoding="utf-8")

    # ── 2. LE GEL (vivant, et apres la V3), LES CHAINES, LES ETIQUETTES ───────────────────────────────────────────
    cn, cu = V3.pooler()
    cu.execute("select id_unique, app_affaire_id, confiance from app_classeur_lien")
    gel_l = [(i, int(a), c) for i, a, c in cu.fetchall()]
    cn.rollback()
    cn.close()
    g = json.load((CACHE / "v3_gestes.json").open(encoding="utf-8"))
    if len(gel_l) != g["gel_n"]:
        dire("⛔ le gel a bouge depuis les gestes V3 (%d contre %d) -- refaire temps12 (code 3)" % (len(gel_l), g["gel_n"]))
        return 3
    d = json.load((CACHE / "v3_calcul.json").open(encoding="utf-8"))
    convention = {a for a, _c in d["par_chaine"]} | {a for a, _o in d["par_renego"]}
    gel0, conf0 = defaultdict(set), {}
    for i, a, c in gel_l:
        gel0[i].add(a)
        conf0[(i, a)] = c
    gel1 = defaultdict(set, {i: set(s) for i, s in g["gel_apres"].items()})
    conf1 = {}
    for i, s in gel1.items():
        for a in s:
            conf1[(i, a)] = conf0.get((i, a)) or ("bonne" if a in convention else "sûre")   # la confiance du patch V3
    con = sqlite3.connect("file:%s?mode=ro" % BASE.as_posix(), uri=True)
    ch0, lab0, C5 = {}, {}, set()
    for a, c, u, o, num in con.execute("select app_affaire_id, app_chaine_id, app_dossier_uuid, transaction_origine, "
                                       "hektor_affaire_id from app_affaire_ledger"):
        ch0[int(a)], lab0[int(a)] = c, u
        if K.PC.est_copie(a, o, num):           # LA fonction unique (22/11), par l'outil de coupe qui l'importe
            C5.add(int(a))
    con.close()
    rj = json.load((CACHE / "v3_rejeu_maisons.json").open(encoding="utf-8"))
    ch1 = {int(a): c for a, c in rj["ch"].items()}
    lab1 = {int(a): u for a, u in rj["lab1"].items()}
    # TEMOIN : une etiquette par dossier sur la base (comme le 19/11)
    par = defaultdict(set)
    for a, c in ch0.items():
        par[c].add(lab0[a])
    mauvais = sum(1 for v in par.values() if len(v) != 1 or None in v)
    dire("   gel vivant %d liens ; gel apres la V3 %d ; dossiers aujourd'hui %d, apres la V3 %d ; TEMOIN une etiquette "
         "par dossier : %d ecart(s) (attendu 0)" % (len(gel_l), sum(len(s) for s in gel1.values()), len(set(ch0.values())),
                                                    len(set(ch1.values())), mauvais))
    if mauvais:
        return 2

    # ── 3. CE QUI ATTEND UNE DECISION (les memes listes que le 19/11, et les decisions venues depuis) ──────────────
    verdicts = {}
    with VERDICTS.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            verdicts[r["id_unique"]] = r
    en_attente = {i for i, r in verdicts.items() if r["question_pour_frederic"].strip()
                  or "INCERTAIN" in (r["verdict"] + r["correction_contre_expert"]).upper()} | {"SHN6RKDI"}
    with OPERATIONS.open(encoding="utf-8-sig") as f:
        en_attente |= {r["id_unique"] for r in csv.DictReader(f, delimiter=";") if r["decision_v2"] != "GARDEE"}
    dec_b, dec_19 = ids_csv(DECISION_B), ids_csv(DECISION_19)
    dire("   en attente (listes du 19/11) %d ; decision B %d ; les 19 %d ; non ecrites d'« ou ca tombe » %d"
         % (len(en_attente), len(dec_b), len(dec_19), len(NON_ECRITES)))

    # le juge du 19/11 (GEL_SEUL), sur le Sheet DEJA LU (pas de second GET)
    JUGE.ac.lire_classeur = lambda: (entete, lignes)
    J = JUGE.preparer_juge()
    designe = J["designe"]
    vue_ids = {rec["id"] for rec in J["vue"].values()}

    # le crible du nom : la photo du jour
    K.CACHE = tmp
    D0 = K.Donnees([(i, a) for i, a, _c in gel_l])
    D1 = K.Donnees([(i, a) for i, s in gel1.items() for a in s])

    def crible(D, i: str, ts: set) -> tuple[str, list]:
        detail, vus = [], Counter()
        for a in sorted(ts):
            # seules les copies C5 (nees du Sheet) ne se jugent pas : elles sont circulaires par construction. Une piece
            #   de la PLAGE APP (>= 1 000 000, transaction_origine vide) est une vraie piece Hektor : elle se juge.
            if a in C5:
                continue
            v, pourquoi = K.juger(D, a, {i})
            vus[v] += 1
            detail.append("%d %s : %s" % (a, v, pourquoi))
        if vus[K.CONTREDITE]:
            return "NOM_CONTREDITE", detail
        if vus[K.CONFLIT]:
            return "NOM_CONFLIT", detail
        if vus[K.PROUVEE_DATE] or vus[K.PROUVEE_PH]:
            return "PROUVEE", detail
        return ("NOM_SANS_PREUVE" if vus else "SANS_PIECE_A_JUGER"), detail

    def ranger(gel: dict, conf: dict, ch: dict, D) -> dict:
        lignes_du_dossier = defaultdict(set)
        for i, ts in gel.items():
            for a in ts:
                if a in ch:
                    lignes_du_dossier[ch[a]].add(i)
        out = {}
        for i, v in vivant.items():
            ts = {a for a in gel.get(i, set()) if a in ch}
            dossiers = {ch[a] for a in ts}
            autres = set().union(*(lignes_du_dossier[c] for c in dossiers)) - {i} if dossiers else set()
            exc = V3.exception_du_verrou(autres | {i}) if autres else None
            nom, detail = crible(D, i, ts) if ts else ("", [])
            if col_a.get(i):
                r = "A_DEJA_REMPLIE"
            elif not ts:
                r = "SANS_LIEN"
            elif autres and not exc:
                r = "VERROU_DEUX_LIGNES"
            elif len(dossiers) > 1:
                r = "PLUSIEURS_DOSSIERS"
            elif i in en_attente:
                r = "EN_ATTENTE"
            elif i in dec_b:
                r = "DECISION_B"
            elif i in dec_19:
                r = "DECISION_19"
            elif i in NON_ECRITES:
                r = "NON_ECRITE_OU_CA_TOMBE"
            elif {conf.get((i, a)) for a in ts} - {"sûre"}:
                r = "LIEN_A_VALIDER"
            elif i in verdicts and verdicts[i]["verdict"] not in ("JUSTE", "JUSTE_SANS_PREUVE_FORTE"):
                r = "AUDIT_NON_JUSTE"
            elif all(a in C5 for a in ts):
                r = "C5_SEULE"
            elif not any(i in {x["id"] for x in designe(a)[0]} for a in ts):
                r = "GEL_SEUL"
            elif nom in ("NOM_CONTREDITE", "NOM_CONFLIT", "NOM_SANS_PREUVE"):
                r = nom
            else:
                r = "VAGUE_1"
            out[i] = {"case": r, "num": v["num"], "dossiers": sorted(dossiers), "ts": sorted(ts), "autres": sorted(autres),
                      "exception": exc or "", "nom": nom, "detail": detail}
        return out

    avant = ranger(gel0, conf0, ch0, D0)
    apres = ranger(gel1, conf1, ch1, D1)
    ca, cb = Counter(r["case"] for r in avant.values()), Counter(r["case"] for r in apres.values())
    dire("   LE CLASSEMENT RECALCULE, son verrou d'abord (%d lignes du Sheet) :" % len(vivant))
    dire("      %-24s %12s %12s" % ("", "AUJOURD'HUI", "APRES LA V3"))
    for k in ORDRE:
        dire("      %-24s %12d %12d" % (k, ca[k], cb[k]))

    # ── 4. CONTRE LA VAGUE 1 QUE L'ECRIVAIN LIT AUJOURD'HUI ────────────────────────────────────────────────────────
    with CLASSEMENT_19_11.open(encoding="utf-8") as f:
        c19 = {r["id_unique"]: r for r in csv.DictReader(f)}
    v1_ecrivain = {i for i, r in c19.items() if r["case_aujourd_hui"] == "VAGUE_1"} - dec_b - dec_19
    v1_apres = {i for i, r in apres.items() if r["case"] == "VAGUE_1"}
    sortent = Counter(apres[i]["case"] if i in apres else "PARTIE DU SHEET" for i in v1_ecrivain - v1_apres)
    entrent = Counter(c19[i]["case_aujourd_hui"] if i in c19 else "NEUVE" for i in v1_apres - v1_ecrivain)
    dire("   la vague 1 de l'ecrivain (19/11 - B - 19) : %d ; recalculee apres la V3 : %d ; en commun %d"
         % (len(v1_ecrivain), len(v1_apres), len(v1_ecrivain & v1_apres)))
    dire("      SORTENT %d, et pourquoi : %s" % (sum(sortent.values()), dict(sortent.most_common())))
    dire("      ENTRENT %d, d'ou : %s" % (sum(entrent.values()), dict(entrent.most_common())))
    # le crible, sur la vague 1 de l'ecrivain : ce qu'il trouve, seul (independamment des autres raisons)
    cr = Counter(apres[i]["nom"] for i in v1_ecrivain if i in apres)
    dire("   ⭐ LE CRIBLE DU NOM sur les %d lignes de la vague 1 de l'ecrivain (apres la V3) : %s"
         % (len(v1_ecrivain), dict(cr.most_common())))
    # ses 9 lignes
    for i in SES_9:
        a0, a1 = avant.get(i, {}), apres.get(i, {})
        dire("   ses 9 : %s (ligne %s) -- 19/11 %s ; aujourd'hui %s ; apres la V3 %s %s"
             % (i, a1.get("num"), c19.get(i, {}).get("case_aujourd_hui"), a0.get("case"), a1.get("case"),
                ("avec " + " ".join(a1.get("autres", []))) if a1.get("autres") else ""))
    sortis_9 = [i for i in SES_9 if apres.get(i, {}).get("case") != "VAGUE_1"]
    # les exceptions nommees : toujours dites
    for i in sorted(r for r in apres if apres[r]["exception"]):
        dire("   ⭐ EXCEPTION NOMMEE, sautee par le verrou EN LA NOMMANT : %s (ligne %s) -- %s ; case %s"
             % (i, apres[i]["num"], apres[i]["exception"], apres[i]["case"]))
    # TEMOIN POSITIF du verrou : le recalcul doit retrouver les 38 lignes / 19 dossiers de temps12 apres la V3
    v_apres = {i for i, r in apres.items() if r["case"] == "VERROU_DEUX_LIGNES"}
    v_g = set().union(*map(set, g["partagees_apres"].values())) if g["partagees_apres"] else set()
    dire("   TEMOIN : lignes au verrou apres la V3 %d, contre %d dans les gestes V3 (les memes : %s)"
         % (len(v_apres), len(v_g), v_apres == v_g))
    # ── 5. LE CSV ──────────────────────────────────────────────────────────────────────────────────────────────────
    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "numero de ligne", "case le 19/11", "dans la vague 1 de l'ecrivain", "case aujourd'hui",
                    "case apres la V3", "crible du nom (apres la V3)", "le detail du crible (piece : verdict : preuve)",
                    "son dossier apres la V3", "les autres lignes de ce dossier", "exception nommee",
                    "etiquette apres la V3 (NEUVE = posee par la nuit)"])
        for i, r in sorted(apres.items(), key=lambda kv: kv[1]["num"]):
            w.writerow([i, r["num"], c19.get(i, {}).get("case_aujourd_hui", "(neuve)"), "OUI" if i in v1_ecrivain else "",
                        avant[i]["case"], r["case"], r["nom"], " | ".join(r["detail"]),
                        " ".join(map(str, r["dossiers"])), " ".join(r["autres"]), r["exception"],
                        (lab1.get(r["ts"][0]) or "") if r["ts"] else ""])
    dire("   CSV : %s" % SORTIE.name)
    json.dump({"avant": avant, "apres": apres, "v1_ecrivain": sorted(v1_ecrivain), "v1_apres": sorted(v1_apres),
               "bouge": bouge, "neuves": neuves, "parties": parties, "doublons": dbl},
              (CACHE / "t13_vague1.json").open("w", encoding="utf-8"), ensure_ascii=False)
    ok = v_apres == v_g and len(sortis_9) >= 8
    dire("VAGUE 1 SOUS LE VERROU : FIN (%.0f s) -- %s ; ses 9 hors de la vague 1 apres la V3 : %d %s"
         % ((datetime.now() - t0).total_seconds(), "VERT" if ok else "⛔ A REGARDER", len(sortis_9), sortis_9))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
