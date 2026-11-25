#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE CLASSEMENT DE LA COLONNE A, REFAIT SUR L'ETAT D'AUJOURD'HUI (son mot du 25/11) -- LECTURE SEULE.

    python -X utf8 -u phase2\checks\reclasser_colonne_a_apres_la_vague_2026-11-25.py

SON MOT : « ARRETE LES VAGUES [...] ELLES SONT ECARTEES PAR TON CLASSEMENT DU 19/11, QUI EST D'AVANT LA VAGUE [...]
RECLASSE SUR L'ETAT D'AUJOURD'HUI. ① refais le classement apres la vague [...] ② combien de lignes sortent de leur case
grace a la vague [...] ③ [...] les 4 VENTES REGLEES de mes trous [...] ④ puis une vague neuve, sur le classement neuf ».

⛔ N'ECRIT RIEN, NI DANS LE SHEET NI EN BASE : il lit le Sheet (deux GET), le registre et le gel chez Supabase, la copie
  du registre de l'image de 07:26 (les chaines D'AVANT la vague), et ecrit UN fichier dans notice/.

LES MEMES RAISONS ET LE MEME ORDRE QUE LE 19/11 (temps5_q8_les_vagues_d_ecriture_du_sheet_2026-11-19.py), la premiere qui
concerne la ligne la range ; deux changements, DITS :
  · PATCH_V2 et CETTE_NUIT n'existent plus : le patch V2 est JOUE (temoin ci-dessous : le gel du jour porte ses ajouts et
    aucun de ses retraits) et les 10 menages sont passes ;
  · « plusieurs dossiers » et « etiquette partagee » se lisent COMME L'OUTIL LES JUGE A L'ECRITURE (juger_paquet) : les
    pieces EFFECTIVES (sa regle C5 du 19/11 : une creation du Sheet ne decide jamais de l'etiquette ; sans piece de Hektor,
    toutes) ; le 19/11 lisait toutes les pieces. Le compte par la lecture du 19/11 est donne a cote, en temoin.
Les cases qui viennent d'une DECISION ou d'un AUDIT (EN_ATTENTE, AUDIT_NON_JUSTE) sont relues dans les MEMES fichiers que le
19/11 : je ne les leve pas, c'est a lui.

TROIS ETATS, pour isoler ce que la vague a fait :
  S0  le classement du 19/11 tel qu'ecrit (colonne case_apres = ses nombres : 3 997 en VAGUE_1, 800 ecartees) ;
  S1  les regles d'aujourd'hui sur les chaines D'AVANT la vague (image de 07:26), la colonne A vide ;
  S2  les regles d'aujourd'hui sur les etiquettes de MAINTENANT, la colonne A vide -- puis la colonne A posee dessus.
  S1 -> S2 = ce que la vague a fait, et rien d'autre (le gel est le meme : la vague n'y touche pas -- temoin).

Sortie : 0 mesure faite . 2 un temoin a echoue.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import piece_copie_ou_vraie as PC  # noqa: E402

NOTICE = RACINE / "notice"
CLASSEMENT_19_11 = NOTICE / "TEMPS5_Q8_LES_LIGNES_DU_SHEET_ET_LEUR_VAGUE_2026-11-19.csv"
PATCH_V2 = RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19.sql"
VERDICTS = NOTICE / "AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv"
OPERATIONS = NOTICE / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv"
IMAGE_AVANT = P.IMAGES / "2026-11-25_072625"
SORTIE = NOTICE / "CLASSEMENT_COLONNE_A_APRES_LA_VAGUE_2026-11-25.csv"
ORDRE = ["A_DEJA_REMPLIE", "SANS_LIEN", "EN_ATTENTE", "PATCH_V2", "CETTE_NUIT", "PLUSIEURS_DOSSIERS",
         "ETIQUETTE_PARTAGEE", "LIEN_A_VALIDER", "AUDIT_NON_JUSTE", "C5_SEULE", "GEL_SEUL", "VAGUE_1"]


def charger(nom: str, fichier: str):
    spec = importlib.util.spec_from_file_location(nom, ICI / fichier)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    # ⛔ SON MOT DU 25/11 : l'outil refuse un classement plus vieux que la derniere vague -> le classement porte sa
    #   FABRICATION (fiche <csv>.json). L'heure est prise AVANT toute lecture : une vague pendant la mesure le perime.
    debut = datetime.now(timezone.utc)
    echecs: list[str] = []
    juge = charger("juge_q5", "temps5_q5_les_48_a_juger_par_le_classeur_2026-11-19.py")
    outil = charger("outil_a", "ecrire_colonne_a_du_sheet_2026-11-20.py")
    J = juge.preparer_juge()                         # le Sheet (GET) et le registre local (mode=ro) : pour « designe »
    designe = J["designe"]
    entete, lignes = juge.ac.lire_classeur()         # la colonne A et les lignes d'aujourd'hui
    assert entete[0] == "affair_uuid" and entete[37] == "ID Unique", "l'en-tete du Sheet a bouge"
    col_a, ligne_de, en_double = {}, {}, []
    for num, l in lignes:
        l = list(l) + [""] * 38
        i = str(l[37]).strip()
        if not i:
            continue
        if i in ligne_de:
            en_double.append(i)
        ligne_de[i] = num
        col_a[i] = str(l[0] or "").strip()
    print("Sheet relu : %d lignes, %d ID Unique, %d case(s) A remplie(s), %d ID en double %s" % (
        len(lignes), len(ligne_de), sum(1 for v in col_a.values() if v), len(en_double), en_double[:5]), flush=True)

    cl = {}
    with CLASSEMENT_19_11.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            cl[r["id_unique"]] = r

    # ── Supabase : le gel, ses confiances, le registre d'aujourd'hui ──
    cn, cu = P.pooler()
    cu.execute("select id_unique, app_affaire_id, confiance from public.app_classeur_lien")
    gel, conf = defaultdict(set), defaultdict(set)
    for i, a, c in cu.fetchall():
        gel[i].add(int(a))
        conf[i].add(c)
    cu.execute("select app_affaire_id, app_chaine_id, app_dossier_uuid::text, transaction_origine, hektor_affaire_id, "
               "app_dossier_numero from public.app_affaire_ledger")
    reg = {}
    for a, ch, u, o, h, n in cu.fetchall():
        reg[int(a)] = {"chaine": ch, "uuid": u, "copie": PC.est_copie(int(a), o, h), "numero": n}
    cn.rollback()
    cn.close()
    gel_md5 = hashlib.md5(repr(sorted((i, a) for i, s in gel.items() for a in s)).encode()).hexdigest()[:8]
    print("gel : %d lignes, %d liens (%s) ; registre : %d pieces" % (len(gel), sum(map(len, gel.values())), gel_md5,
                                                                     len(reg)), flush=True)

    # TEMOIN : le patch V2 est joue (ses ajouts sont dans le gel, aucun de ses retraits)
    texte = PATCH_V2.read_text(encoding="utf-8")
    b3 = texte.split("-- ── ③ RETIRER")[1].split("-- ── ④ AJOUTER")[0]
    b4 = texte.split("-- ── ④ AJOUTER")[1].split("-- ── ⑤ LE CONTROLE")[0]
    retraits = {(i, int(a)) for i, a in re.findall(r"\('([^']+)',\s*(\d+),\s*'\w+'\)", b3)}
    ajouts = {(i, int(a)) for a, _c, i in re.findall(r"\(\d+,\s*(\d+),\s*'\w+',\s*'([^']+)',.*?'([^']+)'\)", b4)}
    r_restes = sorted(x for x in retraits if x[1] in gel.get(x[0], set()))
    a_manque = sorted(x for x in ajouts if x[1] not in gel.get(x[0], set()))
    print("TEMOIN patch V2 joue : %d retraits (encore dans le gel : %d), %d ajouts (absents du gel : %d)" % (
        len(retraits), len(r_restes), len(ajouts), len(a_manque)), flush=True)
    if not retraits or not ajouts or r_restes or a_manque:
        echecs.append("patch V2 pas joue tel quel : retraits restes %s, ajouts manquants %s" % (r_restes[:3], a_manque[:3]))

    # TEMOIN : une etiquette = un dossier, sur le registre d'aujourd'hui
    ch_u, u_ch = defaultdict(set), defaultdict(set)
    for a, x in reg.items():
        ch_u[x["chaine"]].add(x["uuid"])
        u_ch[x["uuid"]].add(x["chaine"])
    mauvais = sum(1 for k, v in ch_u.items() if k is not None and (len(v) != 1 or None in v)) + \
        sum(1 for k, v in u_ch.items() if k is not None and len(v) != 1)
    print("TEMOIN une etiquette = un dossier (aujourd'hui) : %d ecart(s) (attendu 0)" % mauvais, flush=True)
    if mauvais:
        echecs.append("etiquette != dossier : %d" % mauvais)

    # les chaines D'AVANT la vague (image de 07:26)
    con = sqlite3.connect("file:%s?mode=ro" % (IMAGE_AVANT / "registre.sqlite").as_posix(), uri=True)
    avant_ch = {int(a): c for a, c in con.execute("select app_affaire_id, app_chaine_id from app_affaire_ledger")}
    con.close()
    print("chaines d'avant la vague (image %s) : %d pieces" % (IMAGE_AVANT.name, len(avant_ch)), flush=True)

    # les decisions et l'audit : les MEMES fichiers que le 19/11
    verdicts = {}
    with VERDICTS.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            verdicts[r["id_unique"]] = r
    en_attente = {i for i, r in verdicts.items() if r["question_pour_frederic"].strip()
                  or "INCERTAIN" in (r["verdict"] + r["correction_contre_expert"]).upper()} | {"SHN6RKDI"}
    with OPERATIONS.open(encoding="utf-8-sig") as f:
        en_attente |= {r["id_unique"] for r in csv.DictReader(f, delimiter=";") if r["decision_v2"] != "GARDEE"}
    exclus_b = outil.lire_hors_vague()
    print("en attente de decision (fichiers du 19/11) : %d ; sorties par ses decisions du 20/11 (B, 19) : %d" % (
        len(en_attente), len(exclus_b)), flush=True)

    ids = sorted(ligne_de)

    def effectives(ts, dossier_de):
        connues = [a for a in ts if a in reg and dossier_de(a) is not None]
        hk = [a for a in connues if not reg[a]["copie"]]
        return hk if hk else connues

    def ranger(dossier_de) -> dict:
        """Les raisons du 19/11, dans son ordre, sur l'etat donne (dossier_de : piece -> dossier). Colonne A ignoree."""
        eff = {i: effectives(sorted(gel.get(i, set())), dossier_de) for i in ids}
        lignes_du_dossier = defaultdict(set)
        for i in ids:
            for a in eff[i]:
                lignes_du_dossier[dossier_de(a)].add(i)
        out = {}
        for i in ids:
            ts = sorted(a for a in gel.get(i, set()) if a in reg and dossier_de(a) is not None)
            dossiers = sorted({dossier_de(a) for a in eff[i]}, key=str)
            autres = []
            if not ts:
                r = "SANS_LIEN"
            elif i in en_attente:
                r = "EN_ATTENTE"
            elif len(dossiers) > 1:
                r = "PLUSIEURS_DOSSIERS"
            elif lignes_du_dossier[dossiers[0]] - {i}:
                r = "ETIQUETTE_PARTAGEE"
                autres = sorted(lignes_du_dossier[dossiers[0]] - {i})
            elif conf.get(i, set()) - {"sûre"}:
                r = "LIEN_A_VALIDER"
            elif i in verdicts and verdicts[i]["verdict"] not in ("JUSTE", "JUSTE_SANS_PREUVE_FORTE"):
                r = "AUDIT_NON_JUSTE"
            elif all(reg[a]["copie"] for a in ts):
                r = "C5_SEULE"
            elif not any(i in {x["id"] for x in designe(a)[0]} for a in ts):
                r = "GEL_SEUL"
            else:
                r = "VAGUE_1"
            out[i] = {"case": r, "dossiers": dossiers, "ts": ts, "eff": eff[i], "autres": autres}
        return out

    S1 = ranger(lambda a: avant_ch.get(a))
    S2 = ranger(lambda a: reg[a]["uuid"] if a in reg else None)
    S2c = ranger(lambda a: reg[a]["chaine"] if a in reg else None)       # temoin : par les chaines d'aujourd'hui
    d_temoin = sum(1 for i in ids if S2[i]["case"] != S2c[i]["case"])
    print("TEMOIN la meme mesure par les CHAINES d'aujourd'hui au lieu des etiquettes : %d ligne(s) differente(s) "
          "(attendu 0)" % d_temoin, flush=True)
    if d_temoin:
        echecs.append("chaines et etiquettes ne rangent pas pareil : %d" % d_temoin)

    # la lecture du 19/11 (toutes les pieces) pour « plusieurs dossiers », en temoin
    plus_19 = sum(1 for i in ids if len({reg[a]["uuid"] for a in gel.get(i, set()) if a in reg}) > 1)
    plus_eff = sum(1 for i in ids if len({reg[a]["uuid"] for a in S2[i]["eff"]}) > 1)
    print("lignes a plusieurs etiquettes aujourd'hui : %d par les pieces effectives (l'outil), %d par toutes les "
          "pieces (lecture du 19/11)" % (plus_eff, plus_19), flush=True)

    final = {}
    for i in ids:
        final[i] = "A_DEJA_REMPLIE" if col_a.get(i) else S2[i]["case"]

    # TEMOIN POSITIF : les 50 ecrites ce matin etaient ecrivables -> S2 (colonne A ignoree) les range en VAGUE_1
    ecrites = [i for i in ids if col_a.get(i)]
    pas_v1 = [(i, S2[i]["case"]) for i in ecrites if S2[i]["case"] != "VAGUE_1"]
    print("TEMOIN les %d lignes deja ecrites : rangees VAGUE_1 sans leur case A : %d (attendu %d) %s" % (
        len(ecrites), len(ecrites) - len(pas_v1), len(ecrites), pas_v1[:5]), flush=True)
    if pas_v1:
        echecs.append("des lignes ecrites ne sont pas en VAGUE_1 : %s" % pas_v1[:5])
    # TEMOIN : chaque ligne VAGUE_1 a UNE etiquette, et aucune etiquette n'est sur deux lignes VAGUE_1
    v1 = [i for i in ids if final[i] == "VAGUE_1"]
    u_v1 = Counter(reg[S2[i]["eff"][0]]["uuid"] for i in v1)
    deux = [u for u, n in u_v1.items() if n > 1]
    print("TEMOIN VAGUE_1 : %d lignes, %d etiquettes distinctes, %d etiquette(s) sur deux lignes" % (
        len(v1), len(u_v1), len(deux)), flush=True)
    if deux:
        echecs.append("une etiquette sur deux lignes de la VAGUE_1 : %s" % deux[:3])
    # TEMOIN : la colonne A deja remplie porte l'etiquette d'aujourd'hui de sa ligne
    faux_a = [i for i in ecrites if not S2[i]["eff"] or col_a[i] != reg[S2[i]["eff"][0]]["uuid"]]
    print("TEMOIN les cases A deja remplies portent l'etiquette d'aujourd'hui : %d / %d" % (
        len(ecrites) - len(faux_a), len(ecrites)), flush=True)
    if faux_a:
        echecs.append("case A differente de l'etiquette : %s" % faux_a[:5])

    # ① LE CLASSEMENT D'AUJOURD'HUI
    c0 = Counter(cl[i]["case_apres"] for i in cl)
    c1 = Counter(S1[i]["case"] for i in ids)
    c2 = Counter(S2[i]["case"] for i in ids)
    cf = Counter(final.values())
    print("\n① LES %d LIGNES (ID Unique) DU SHEET, rangees par la premiere raison :" % len(ids))
    print("   %-20s %12s %18s %18s %20s" % ("", "19/11 (S0)", "avant vague (S1)", "apres vague (S2)",
                                           "aujourd'hui, avec A"))
    for k in ORDRE:
        if c0[k] or c1[k] or c2[k] or cf[k]:
            print("   %-20s %12d %18d %18d %20d" % (k, c0[k], c1[k], c2[k], cf[k]))
    print("   %-20s %12d %18d %18d %20d" % ("TOTAL", sum(c0.values()), sum(c1.values()), sum(c2.values()),
                                           sum(cf.values())))
    neuves = [i for i in ids if i not in cl]
    parties = [i for i in cl if i not in ligne_de]
    print("   lignes nees depuis le 19/11 : %d %s ; lignes du 19/11 absentes aujourd'hui : %d %s" % (
        len(neuves), [(i, final[i]) for i in neuves], len(parties), parties[:10]))
    eb = Counter(exclus_b[i][0] for i in v1 if i in exclus_b)
    print("   dans la VAGUE_1 d'aujourd'hui, %d sont sorties par ses decisions du 20/11 (l'outil les refuse) : %s" % (
        sum(eb.values()), dict(eb)))

    # ② CE QUI SORT DE SA CASE
    print("\n② CE QUI SORT DE SA CASE (S0 = 19/11 -> maintenant, colonne A ignoree ; et la part de la VAGUE : S1 -> S2)")
    for k in ORDRE:
        if k == "VAGUE_1" or not c0[k]:
            continue
        de_k = [i for i in cl if cl[i]["case_apres"] == k and i in S2]
        vers = Counter(S2[i]["case"] for i in de_k)
        libres = [i for i in de_k if S2[i]["case"] == "VAGUE_1"]
        par_vague = [i for i in libres if S1[i]["case"] != "VAGUE_1"]
        print("   %-20s %4d le 19/11 -> en VAGUE_1 maintenant : %4d (dont par la vague : %4d) ; ailleurs : %s" % (
            k, len(de_k), len(libres), len(par_vague), dict(vers)))
    entrees_bloquees = [i for i in cl if cl[i]["case_apres"] == "VAGUE_1" and i in S2 and S2[i]["case"] != "VAGUE_1"]
    print("   et dans l'autre sens : %d ligne(s) VAGUE_1 le 19/11 sont bloquees maintenant : %s" % (
        len(entrees_bloquees), dict(Counter(S2[i]["case"] for i in entrees_bloquees))))
    vague_lib = [i for i in ids if S1[i]["case"] != "VAGUE_1" and S2[i]["case"] == "VAGUE_1"]
    vague_blo = [i for i in ids if S1[i]["case"] == "VAGUE_1" and S2[i]["case"] != "VAGUE_1"]
    print("   LA VAGUE SEULE (S1 -> S2) : %d ligne(s) liberee(s) %s ; %d bloquee(s) %s" % (
        len(vague_lib), dict(Counter(S1[i]["case"] for i in vague_lib)), len(vague_blo),
        dict(Counter(S2[i]["case"] for i in vague_blo))))
    for i in vague_blo[:20]:
        print("      bloquee par la vague : %s ligne %s -> %s %s %s" % (i, ligne_de[i], S2[i]["case"], S2[i]["dossiers"],
                                                                       S2[i]["autres"]))

    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id_unique", "ligne_au_19_11", "ligne_au_25_11", "case_19_11", "case_avant_la_vague",
                    "case_25_11", "etiquette_a_ecrire", "dossiers", "transactions", "autres_lignes_du_dossier",
                    "decision_du_20_11"])
        for i in sorted(ids, key=lambda x: ligne_de[x]):
            s = S2[i]
            u = reg[s["eff"][0]]["uuid"] if final[i] == "VAGUE_1" else ""
            w.writerow([i, cl.get(i, {}).get("ligne_au_19_11", ""), ligne_de[i], cl.get(i, {}).get("case_apres", ""),
                        S1[i]["case"], final[i], u,
                        " ".join(sorted({str(reg[a]["numero"]) for a in s["eff"]})),
                        " ".join(map(str, s["ts"])), " ".join(s["autres"]),
                        exclus_b[i][0] if i in exclus_b else ""])
    print("\nCSV : %s" % SORTIE)
    if not echecs:
        fiche = SORTIE.with_name(SORTIE.name + ".json")
        fiche.write_text(json.dumps({"fait_le": debut.isoformat(timespec="seconds"),
                                     "sha256": hashlib.sha256(SORTIE.read_bytes()).hexdigest(),
                                     "par": Path(__file__).name, "lignes": len(ids)}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print("FICHE DE FABRICATION : %s (fait le %s)" % (fiche, debut.isoformat(timespec="seconds")))
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
