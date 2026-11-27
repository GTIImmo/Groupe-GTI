#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE CONTROLE D'UNE NUIT DU CHANTIER CLASSEUR -- ce que la nuit a fait au chainage, prouve.     20/11/2026

Deux nuits, une meme methode :
    dix       la nuit du 19 au 20/11 : les 10 rattachements « menage » (§ 2.7)
    regle_e   la nuit du 20 au 21/11 : la regle E allumee, avec ses 5 exclusions declarees (§ 11 et ⑫)

UNE ETAPE PAR APPEL (regle de Frederic du 19/11 : un rejeu par appel, chacun sous dix minutes, le resultat
ECRIT AU FIL dans un fichier ; ~10-15 s chacune) :

    .venv\Scripts\python.exe -X utf8 -u phase2\checks\controle_nuit_chainage_classeur_2026-11-20.py <nuit> <etape>

    reference       (regle_e seulement, LA VEILLE, avant l'allumage) : fige l'etat de la base (dossier et
                    etiquette de chaque transaction) et la prediction de E (le CSV de temps4, regenere le matin)
    journal         lit le journal du run du jour (logs\scheduled\quotidien_<date>_*.log) : fini en code 0 ?
                    les compteurs du chainage et de la pose des etiquettes
    rejeu_tel_quel  la vraie fonction sur une copie en memoire, REGLEE COMME LA NUIT -> doit redonner la base
    rejeu_sans      la meme, SANS le geste de la nuit (sans les 10 lignes / E eteinte) -> la difference avec la
                    base est l'effet du geste, et de rien d'autre
    juger           relit tout, juge, ecrit notice\CONTROLE_NUIT_<NUIT>_<date>.md

⛔ CE SCRIPT N'ECRIT RIEN NI EN BASE, NI CHEZ HEKTOR, NI DANS LE SHEET : phase2.sqlite en mode=ro, les rejeux
  sur une copie en memoire, les interrupteurs poses DANS CE PROCESSUS seulement. Ses fichiers vont dans
  C:\Hektor\chantier_classeur_q6_cache\controles_nuit\ (hors du depot) et le compte rendu dans notice\.
⚠ CE QU'IL NE MESURE PAS : le journal des etiquettes chez Supabase (app_dossier_etiquette_journal) -- a lire a
  part, en lecture seule ; il le RAPPELLE dans son compte rendu.

Sortie : 0 vert . 1 un rouge (nomme) . 2 pas pu mesurer (etape ou journal manquant).
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import date as Date, datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
import phase2.sync.affaire_ledger as al                             # noqa: E402

BASE = RACINE / "phase2" / "phase2.sqlite"
LOGS = RACINE / "logs" / "scheduled"
Q6 = RACINE.parent / "chantier_classeur_q6_cache"
CACHE = Q6 / "controles_nuit"
JOURNAL = CACHE / "journal.txt"
PHOTO_19_11 = Q6 / "t6_photo.json"                   # la photo du 19/11 20:09 : l'etat AVANT la nuit des 10
REUNIONS_E = RACINE / "notice" / "TEMPS4_REGLE_E_REUNIONS_2026-11-19.csv"
INTERRUPTEUR_E = "APP_CHAINAGE_SANS_DATE_VISIBLE"

#: offre -> (compromis cible, bien) -- les 10 du 19/11 (§ 2.6 / 2.7)
LES_DIX = {5356: (5355, 10955), 5408: (5407, 11014), 13056: (13055, 27037), 16866: (16865, 35702),
           17278: (17277, 36712), 20196: (20195, 41584), 21339: (21337, 42883), 22069: (22068, 44276),
           26825: (26824, 52724), 28328: (28327, 55040)}
DECISIONS_ATTENDUES = 16
#: les 5 exclusions declarees de E (affaire_ledger.EXCLUES_DE_LA_REGLE_E) -- chacune doit RESTER SEULE
EXCLUSIONS_ATTENDUES = {26613, 21520, 4126, 4496, 4720}
CLE_E_VISIBLE = "[E] transaction sans date restee seule -- rendue visible"
CLE_E_EXCLUE = "[E] exclusion declaree -- laissee seule (EXCLUES_DE_LA_REGLE_E)"
CLE_E_GARDE = "[E] garde : le compromis vivant est a un autre acheteur -- abstention"
CLE_M = "[M] rattachement decide a la main"


def journal(texte: str) -> None:
    """A l'ecran ET dans le journal sur le disque, au fil."""
    print(texte, flush=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write("%s  %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), texte))


def ecrire_json(chemin: Path, obj) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(chemin.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(chemin)


def lire_json(chemin: Path):
    if not chemin.exists():
        journal("⛔ etape precedente absente : %s (code 2)" % chemin.name)
        sys.exit(2)
    return json.loads(chemin.read_text(encoding="utf-8"))


def fichier(nuit: str, etape: str) -> Path:
    return CACHE / ("%s_%s_%s.json" % (nuit, Date.today().isoformat(), etape))


def lire_base() -> dict:
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    info = {}
    for a, bien, k, s, d, pj, ch, u, num, pres in src.execute(
            f"SELECT app_affaire_id, hektor_annonce_id, kind, state, date, propositions_json, app_chaine_id, "
            f"app_dossier_uuid, hektor_affaire_id, present_in_hektor FROM {al.LEDGER_TABLE}"):
        # « sans date » au sens de la regle E : la date de TRI du chainage (comme temps4)
        info[a] = {"bien": str(bien), "genre": k, "etat": (s or "").lower(), "tri": al._date_de_tri(k, d, pj),
                   "chaine": ch, "uuid": u,
                   "effacee": bool(str(num or "").strip()) and str(pres) in ("0", "false", "False")}
    src.close()
    return info


def rejouer(regle_e: bool, fichier_ratt: Path | None = None) -> tuple[dict, dict]:
    """La vraie fonction, sur une copie en memoire. L'interrupteur E est pose EXPLICITEMENT (« 0 » ou « 1 ») :
    le chargement de .env n'ecrase pas une variable deja posee -- donc la nuit allumee ne fausse pas le rejeu
    « sans »."""
    d_origine = al.FICHIER_RATTACHEMENTS
    if fichier_ratt is not None:
        al.FICHIER_RATTACHEMENTS = fichier_ratt
    avant_e = os.environ.get(INTERRUPTEUR_E)
    os.environ[INTERRUPTEUR_E] = "1" if regle_e else "0"
    try:
        src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
        con = sqlite3.connect(":memory:")
        src.backup(con)
        src.close()
        with contextlib.redirect_stdout(io.StringIO()):
            compte = al.recalculer_les_chaines(con)
        chaines = {str(a): c for a, c in con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {al.LEDGER_TABLE}")}
    finally:
        al.FICHIER_RATTACHEMENTS = d_origine
        if avant_e is None:
            os.environ.pop(INTERRUPTEUR_E, None)
        else:
            os.environ[INTERRUPTEUR_E] = avant_e
    return chaines, {k: v for k, v in compte.items() if isinstance(v, (int, bool, str))}


# ─────────────────────────────────────────────── LES ETAPES ───────────────────────────────────────────────
def etape_reference(nuit: str) -> int:
    if nuit != "regle_e":
        journal("⛔ « reference » ne sert qu'a la nuit regle_e (la nuit des 10 a sa photo du 19/11) (code 2)")
        return 2
    if not REUNIONS_E.exists():
        journal("⛔ %s absent : lancer temps4_regle_e_sans_date_visible d'abord (code 2)" % REUNIONS_E.name)
        return 2
    info = lire_base()
    with REUNIONS_E.open(encoding="utf-8") as f:
        prediction = list(csv.DictReader(f))
    gele = CACHE / ("regle_e_prediction_%s.csv" % datetime.now().strftime("%Y-%m-%d_%H%M"))
    CACHE.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REUNIONS_E, gele)
    ecrire_json(CACHE / "regle_e_reference.json", {
        "le": datetime.now().isoformat(timespec="seconds"),
        "base": {str(a): [x["chaine"], x["uuid"]] for a, x in info.items()},
        "prediction": prediction, "prediction_figee": gele.name,
        "exclusions_du_code": sorted(al.EXCLUES_DE_LA_REGLE_E)})
    journal("REFERENCE regle_e : %d transactions figees, %d reunions predites (%s), exclusions du code %s"
            % (len(info), len({p["etiquette_gardee"] for p in prediction}), gele.name,
               sorted(al.EXCLUES_DE_LA_REGLE_E)))
    return 0


def etape_journal(nuit: str, jour: str) -> int:
    logs = sorted(LOGS.glob("quotidien_%s_*.log" % jour))
    if not logs:
        journal("⛔ aucun journal du run pour le %s dans %s (code 2)" % (jour, LOGS))
        return 2
    texte = logs[-1].read_text(encoding="utf-8", errors="replace")
    # la transcription coupe les longues lignes : on recolle tout avant de chercher une cle
    plat = texte.replace("\r", "").replace("\n", "")
    fin = re.search(r"=== Run quotidien termine (\S+ \S+) \(exit (\d+)\) ===", texte)

    def nombre(cle: str):
        m = re.search(re.escape('"%s"' % cle) + r":\s*(\d+|true|false)", plat)
        return None if not m else (m.group(1) == "true" if m.group(1) in ("true", "false") else int(m.group(1)))

    etiq = {}
    m = re.search(r'"etiquettes":\s*\{(.*?)\}', plat)
    if m:
        for k, v in re.findall(r'"(\w+)":\s*(\d+)', m.group(1)):
            etiq[k] = int(v)
    res = {"fichier": logs[-1].name, "fini": bool(fin), "fin": fin.group(1) if fin else None,
           "code": int(fin.group(2)) if fin else None,
           "chainage_ligne": (re.search(r"\[ledger\] chainage : ([^\[]*?\))", plat) or [None, None])[1],
           "manuels": nombre("chainage_rattachements_manuels"), "M": nombre(CLE_M),
           "e_actif": nombre("chainage_sans_date_visible"), "e_visibles": nombre(CLE_E_VISIBLE),
           "e_exclues": nombre(CLE_E_EXCLUE), "e_garde": nombre(CLE_E_GARDE),
           "D": nombre("[D] meme acheteur, meme bien -- dossiers reunis"), "chaines": nombre("chaines"),
           "etiquettes": etiq, "cri": bool(re.search(r"ATTENTION ETIQUETTES : (\d+) FUSION", plat)),
           "echec_pose": "la pose a echoue" in plat}
    ecrire_json(fichier(nuit, "journal"), res)
    journal("JOURNAL %s : fini %s (code %s, %s) . rattachements a la main %s . E %s (visibles %s, exclues %s, "
            "garde %s) . D %s . etiquettes %s . cri %s"
            % (res["fichier"], res["fini"], res["code"], res["fin"], res["manuels"], res["e_actif"],
               res["e_visibles"], res["e_exclues"], res["e_garde"], res["D"], etiq, res["cri"]))
    return 0


def fichier_sans_les_dix(tmp: Path) -> Path:
    garde = []
    for brut in al.FICHIER_RATTACHEMENTS.read_text(encoding="utf-8-sig").splitlines():
        p = brut.strip().split(";")
        if p and p[0].strip().isdigit() and int(p[0]) in LES_DIX:
            continue
        garde.append(brut)
    f = tmp / "rattachements_sans_les_dix.csv"
    f.write_text("\n".join(garde) + "\n", encoding="utf-8")
    return f


def etape_rejeu(nuit: str, sans: bool) -> int:
    t0 = time.time()
    nom = "rejeu_sans" if sans else "rejeu_tel_quel"
    journal("%s %s : debut" % (nuit.upper(), nom))
    with tempfile.TemporaryDirectory() as tmp:
        if nuit == "dix":
            ch, compte = rejouer(False, fichier_sans_les_dix(Path(tmp)) if sans else None)
        else:
            ch, compte = rejouer(not sans)
    ecrire_json(fichier(nuit, nom), {"chaines": ch, "compte": compte, "le": datetime.now().isoformat(timespec="seconds")})
    journal("%s %s : %d transactions, %d dossiers -- FIN en %.0f s"
            % (nuit.upper(), nom, len(ch), len(set(ch.values())), time.time() - t0))
    return 0


# ─────────────────────────────────────────────── LE JUGE ───────────────────────────────────────────────
def groupes(ch: dict) -> dict:
    g = defaultdict(set)
    for a, c in ch.items():
        g[c].add(a)
    return g


def gardes(info: dict, ch: dict) -> tuple[int, int]:
    par = defaultdict(list)
    for a, c in ch.items():
        if not info[a]["effacee"]:
            par[c].append(info[a])
    v = sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "vente") >= 2)
    cp = sum(1 for m in par.values() if sum(1 for x in m if x["genre"] == "compromis"
                                            and x["etat"] not in al.ETATS_COMPROMIS_MORTS) >= 2)
    return v, cp


def etape_juger(nuit: str, jour: str, simuler: bool = False) -> int:
    J = lire_json(fichier(nuit, "journal"))
    T = lire_json(fichier(nuit, "rejeu_tel_quel"))
    S = lire_json(fichier(nuit, "rejeu_sans"))
    info = lire_base()
    tel = {int(a): c for a, c in T["chaines"].items()}
    sans = {int(a): c for a, c in S["chaines"].items()}
    if simuler:
        # ESSAI DU JUGE LUI-MEME (temoin positif) : on fait comme si la nuit avait reussi -- la base prend les
        # chaines du rejeu « tel quel », et la pose est SIMULEE (fusion : le groupe garde l'etiquette de sa plus
        # petite transaction etiquetee). Le compte rendu va dans le cache, jamais dans notice\.
        par = groupes(tel)
        for c, membres in par.items():
            et = [a for a in sorted(membres) if info[a]["uuid"]]
            for a in membres:
                info[a]["chaine"] = c
                if et:
                    info[a]["uuid"] = info[et[0]]["uuid"]
        J = dict(J, fini=True, code=0, manuels=DECISIONS_ATTENDUES, M=DECISIONS_ATTENDUES, echec_pose=False,
                 e_actif=(nuit == "regle_e"), e_exclues=len(EXCLUSIONS_ATTENDUES),
                 etiquettes={"fusion": 10 if nuit == "dix" else 40}, cri=True)
    base = {a: x["chaine"] for a, x in info.items()}
    rouges, lignes = [], []

    def dire(t: str) -> None:
        lignes.append(t)
        journal(t)

    def rouge(t: str) -> None:
        rouges.append(t)
        dire("   ⛔ " + t)

    dire("CONTROLE DE LA NUIT « %s » -- journal %s, base lue le %s"
         % (nuit, J["fichier"], datetime.now().isoformat(timespec="minutes")))
    # 1. LE RUN
    dire("1  LE RUN : fini %s, code %s, a %s" % (J["fini"], J["code"], J["fin"]))
    if not J["fini"] or J["code"] != 0:
        rouge("le run n'est pas fini en code 0")
    if J["echec_pose"]:
        rouge("la pose des etiquettes a ECHOUE cette nuit (journal du run)")
    # 2. LA BASE EST LE RESULTAT DE LA FONCTION
    ecart = sorted(a for a in tel if tel[a] != base.get(a))
    dire("2  LA BASE = la fonction reglee comme la nuit : %d ecart(s) (attendu 0) %s" % (len(ecart), ecart[:15]))
    if ecart:
        rouge("la base n'est pas le resultat du chainage de la nuit : %s" % ecart[:15])
    v, cp = gardes(info, base)
    dire("   gardes : deux ventes %d . deux compromis vivants %d (attendu 0 / 0)" % (v, cp))
    if (v, cp) != (0, 0):
        rouge("gardes : %d / %d" % (v, cp))
    gb = groupes(base)
    dire("   dossiers dans la base : %d . transactions sans etiquette : %d"
         % (len(gb), sum(1 for x in info.values() if not x["uuid"])))
    etiq = J["etiquettes"]
    dire("   la pose de la nuit : pose %s . propagation %s . fusion %s . scission %s . le cri %s"
         % (etiq.get("pose"), etiq.get("propagation"), etiq.get("fusion"), etiq.get("scission"),
            "A SONNE" if J["cri"] else "muet"))

    # 3. L'EFFET DU GESTE = la difference entre « sans » et la base
    bougent = sorted(a for a in sans if sans[a] != base.get(a))
    if nuit == "dix":
        dire("3  LES 10 RATTACHEMENTS : journal « %s » rattachement(s) a la main, compteur [M] %s (attendu %d / %d)"
             % (J["manuels"], J["M"], DECISIONS_ATTENDUES, DECISIONS_ATTENDUES))
        if J["manuels"] != DECISIONS_ATTENDUES or J["M"] != DECISIONS_ATTENDUES:
            rouge("le run n'a pas lu les 16 decisions")
        hors = [a for a in bougent if a not in LES_DIX]
        dire("   sans les 10 lignes, la base differe sur %d transaction(s) (attendu 10, les 10 offres) ; hors des 10 : %d %s"
             % (len(bougent), len(hors), hors[:15]))
        if hors or len(bougent) != 10:
            rouge("l'effet des 10 lignes n'est pas EXACTEMENT les 10 offres : %s" % hors[:15])
        photo = json.loads(PHOTO_19_11.read_text(encoding="utf-8"))["tx"] if PHOTO_19_11.exists() else {}
        if not photo:
            dire("   ⚠ la photo du 19/11 manque : l'etiquette du compromis n'est pas comparee a la veille")
        for s, (c, b) in LES_DIX.items():
            ok_d = base[s] == base[c]
            ok_u = info[s]["uuid"] == info[c]["uuid"] and info[s]["uuid"]
            avant = (photo.get(str(c)) or {}).get("uuid")
            ok_v = (not photo) or avant == info[c]["uuid"]
            avant_offre = (photo.get(str(s)) or {}).get("uuid")
            dire("   bien %-6s offre %-6s -> dossier du compromis %-6s : %s . etiquette %s . celle du compromis "
                 "AVANT la nuit %s . celle de l'offre (absorbee) %s"
                 % (b, s, c, "REUNIE" if ok_d else "⛔ PAS REUNIE", "COMMUNE" if ok_u else "⛔ DIFFERENTE",
                    "GARDEE" if ok_v else "⛔ CHANGEE (%s -> %s)" % (avant, info[c]["uuid"]),
                    (avant_offre or "?")[:8]))
            if not (ok_d and ok_u and ok_v):
                rouge("offre %s" % s)
        if J["cri"] != (etiq.get("fusion", 0) >= al.SEUIL_FUSIONS_QUI_INQUIETE):
            rouge("le cri ne correspond pas au nombre de fusions")
        dire("   fusions de la nuit : %s (dont 10 attendues des menages ; au-dela, les mouvements ordinaires de la nuit)"
             % etiq.get("fusion"))
        if (etiq.get("fusion") or 0) < 10:
            rouge("moins de 10 fusions a la pose : une offre n'a pas pris l'etiquette de son compromis ?")
    else:
        R = lire_json(CACHE / "regle_e_reference.json")
        pred = R["prediction"]
        dire("3  LA REGLE E : journal -- allumee %s . rendues visibles %s . exclusions dites %s (attendu %d) . "
             "garde %s . D %s" % (J["e_actif"], J["e_visibles"], J["e_exclues"], len(EXCLUSIONS_ATTENDUES),
                                  J["e_garde"], J["D"]))
        if J["e_actif"] is not True:
            rouge("la regle E n'a PAS joue cette nuit (chainage_sans_date_visible n'est pas vrai)")
        if J["e_exclues"] != len(EXCLUSIONS_ATTENDUES):
            rouge("les exclusions dites par le run : %s (attendu %d)" % (J["e_exclues"], len(EXCLUSIONS_ATTENDUES)))
        if set(R["exclusions_du_code"]) != EXCLUSIONS_ATTENDUES:
            rouge("les exclusions du code ont change depuis la reference : %s" % R["exclusions_du_code"])
        # les reunions REELLES : un dossier de la base qui reunit plusieurs dossiers « sans E »
        gs = groupes(sans)
        reelles = {}
        for c, membres in gb.items():
            venus = {sans[a] for a in membres if a in sans}
            if len(venus) > 1:
                seuls = sorted(a for a in membres if len(gs[sans[a]]) == 1 and info[a]["tri"] is None)
                reelles[c] = seuls
        coupes = sum(1 for c, m in gs.items() if len({base.get(a) for a in m}) > 1)
        predites = {int(p["transaction"]): p for p in pred}
        vues = {a for s_ in reelles.values() for a in s_}
        dire("   reunions : %d reelles (transactions sans date rattachees : %d) . predites la veille : %d "
             "(transactions %d) . dossiers coupes par E : %d (attendu 0)"
             % (len(reelles), len(vues), len({p["etiquette_gardee"] for p in pred}), len(predites), coupes))
        if coupes:
            rouge("E a coupe %d dossier(s)" % coupes)
        manquent, en_plus = sorted(set(predites) - vues), sorted(vues - set(predites))
        dire("   predites mais PAS faites : %s . faites mais PAS predites : %s" % (manquent or "aucune", en_plus or "aucune"))
        if manquent or en_plus:
            rouge("la nuit ne fait pas EXACTEMENT ce qui etait predit (a lire une par une, la nuit a pu apporter "
                  "du neuf de Hektor)")
        for a in sorted(EXCLUSIONS_ATTENDUES):
            seule = a in info and len(gb[base[a]]) == 1
            dire("   exclusion %-6s : %s" % (a, "RESTE SEULE" if seule else "⛔ REUNIE MALGRE L'EXCLUSION"))
            if not seule:
                rouge("exclusion %s" % a)
        # les etiquettes : chaque reunion porte UNE etiquette, celle predite (le plus petit numero du groupe)
        mal = []
        for a, p in predites.items():
            if a not in info:
                continue
            uu = {info[m]["uuid"] for m in gb[base[a]]}
            if uu != {p["etiquette_gardee"]}:
                mal.append((a, sorted(x or "-" for x in uu)[:3], p["etiquette_gardee"]))
        dire("   etiquettes : %d transaction(s) rattachee(s) sur %d sont dans un dossier qui porte EXACTEMENT "
             "l'etiquette predite" % (len(predites) - len(mal), len(predites)))
        for a, uu, attendu in mal[:15]:
            rouge("etiquette du dossier de %s : %s (attendu %s)" % (a, uu, attendu))
        dire("   fusions de la nuit : %s (attendu au moins %d, une par reunion) ; le cri %s"
             % (etiq.get("fusion"), len(reelles), "A SONNE (attendu)" if J["cri"] else "MUET"))
        if (etiq.get("fusion") or 0) < len(reelles):
            rouge("moins de fusions que de reunions")
        # les 10 du 19/11 tiennent toujours
        tiennent = sum(1 for s, (c, _) in LES_DIX.items() if base[s] == base[c] and info[s]["uuid"] == info[c]["uuid"])
        dire("   les 10 rattachements du 19/11 : %d sur 10 tiennent toujours" % tiennent)
        if tiennent != 10:
            rouge("un des 10 rattachements du 19/11 ne tient plus")

    dire("")
    dire("⚠ NON MESURE ICI : le journal des etiquettes chez Supabase (app_dossier_etiquette_journal) -- a lire a part.")
    dire("VERDICT : %s" % ("VERT" if not rouges else "%d ROUGE(S) : %s" % (len(rouges), " | ".join(rouges)[:600])))
    sortie = RACINE / "notice" / ("CONTROLE_NUIT_%s_%s.md" % (nuit.upper(), Date.today().isoformat()))
    if simuler:
        sortie = CACHE / ("SIMULATION_DU_JUGE_%s_%s.md" % (nuit.upper(), Date.today().isoformat()))
    sortie.write_bytes(("# Controle de la nuit « %s » (genere par %s)\n\n```\n%s\n```\n"
                        % (nuit, Path(__file__).name, "\n".join(lignes))).encode("utf-8"))
    journal("compte rendu : %s" % sortie)
    return 1 if rouges else 0


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in ("dix", "regle_e"):
        print(__doc__)
        return 2
    nuit, etape = sys.argv[1], sys.argv[2]
    jour = sys.argv[3] if len(sys.argv) > 3 else Date.today().isoformat()
    if etape == "reference":
        return etape_reference(nuit)
    if etape == "journal":
        return etape_journal(nuit, jour)
    if etape in ("rejeu_tel_quel", "rejeu_sans"):
        return etape_rejeu(nuit, etape == "rejeu_sans")
    if etape == "juger":
        return etape_juger(nuit, jour)
    if etape == "simuler":                  # essai du juge : « la nuit a reussi » (temoin positif)
        return etape_juger(nuit, jour, simuler=True)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
