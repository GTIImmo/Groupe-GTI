#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""QUESTION 5 -- LES 48 DOSSIERS « A JUGER » DU TEMPS 3, TRANCHES PAR LE CLASSEUR.      19/11/2026

    .venv\Scripts\python.exe -X utf8 phase2\checks\temps5_q5_les_48_a_juger_par_le_classeur_2026-11-19.py

⛔ CE SCRIPT N'ECRIT RIEN : phase2.sqlite en mode=ro, le Sheet en LECTURE (un GET), deux CSV dans notice/.

LA QUESTION. Nos gestes d'etat (11-12/11) ont coupe 79 dossiers ; 48 se « jugent » : deux transactions
separees par le geste, a moins d'un mois, au meme montant, mais sous deux noms differents (ou un cote sans
acquereur, ou deux montants). Le registre seul ne sait pas dire si c'est UNE affaire dont Hektor a change
le contact, ou DEUX acheteurs au meme prix. Le classeur le sait : UNE LIGNE = UNE AFFAIRE.

⛔⛔ L'ACCORD CIRCULAIRE. 15 211 valeurs du Sheet sont deja posees dans notre base. Le juge ne lit donc
QUE des colonnes du Sheet dont la valeur n'a JAMAIS ete recopiee dans les colonnes qu'il compare :
    S  « Offre Achat »    contre la PREMIERE PROPOSITION de l'offre (propositions_json, le journal de Hektor)
    T  « Compromis »      contre la date du compromis chez Hektor (`date`)
    V W X  « Vente Prevue / Fixee / Signee »   contre la date de la vente chez Hektor
    AB « Acquereur »      contre les noms des acquereurs chez Hektor (acquereurs_json)
    AF « Prix »           contre le montant chez Hektor
  Nous n'avons JAMAIS ecrit ces colonnes de Hektor depuis le Sheet. Ce que nous avons pose va dans des
  colonnes A NOUS (`*_app`, notes, avis) -- Y « Vente Reglee », Z « Annulee », AA, P, Q, F, G, AH-AJ --
  et le juge NE LES LIT PAS. Toute date >= 11/11/2026 est un de nos gestes : ignoree. Les 190
  transactions creees depuis le Sheet (transaction_origine = 'classeur') sont ignorees.
  ⛔ Le gel (app_classeur_lien) n'est lu qu'APRES le verdict, pour comparer -- jamais pour choisir.

UNE LIGNE DESIGNE UNE TRANSACTION quand DEUX colonnes independantes s'accordent :
    sa DATE (la colonne du genre, a un jour pres) ET (le NOM de l'acquereur OU le PRIX a 1 % pres).

LE VERDICT D'UNE PAIRE
    MEME LIGNE    une ligne designe les deux      -> une seule affaire : la separation est une CASSE
    DEUX LIGNES   chacune a sa ligne, aucune n'a les deux -> deux affaires : une CORRECTION
    UNE SEULE     une seule des deux est au Sheet -> NON TRANCHE
    AUCUNE        aucune n'est au Sheet           -> NON TRANCHE

LE TEMOIN DU JUGE (semé) : les memes regles passees sur les 5 CASSES sures du temps 3 (meme numero
d'acquereur des deux cotes) et sur les 16 CORRECTIONS (deux acheteurs a plus d'un mois). Le juge ne doit
dire DEUX LIGNES sur aucune casse, ni MEME LIGNE sur aucune correction.

Sortie : 0 mesure faite . 2 le temoin du juge a echoue.
"""
from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
import apparier_classeur as ac                                         # noqa: E402
from rapport_gel_tous_les_champs import date_du_classeur_tolerante     # noqa: E402
from phase2.sync.affaire_ledger import _date_de_tri                    # noqa: E402

BASE = RACINE / "phase2" / "phase2.sqlite"
PAIRES = RACINE / "notice" / "TEMPS3_PAIRES_CHANGEES_2026-11-19.csv"
SORTIE_PAIRES = RACINE / "notice" / "TEMPS5_Q5_PAIRES_JUGEES_PAR_LE_CLASSEUR_2026-11-19.csv"
SORTIE_DOSSIERS = RACINE / "notice" / "TEMPS5_Q5_LES_48_DOSSIERS_VERDICT_2026-11-19.csv"
NOS_GESTES = date(2026, 11, 11)
# colonnes du Sheet (0 = A)
C, R, S, T, V, W, X, AB, AF, AL = 2, 17, 18, 19, 21, 22, 23, 27, 31, 37


def jour_hektor(v) -> date | None:
    try:
        d = date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return None
    return d if d < NOS_GESTES else None


def noms(blob) -> set[str]:
    return ac.mots_propres(ac.noms_du_blob(blob))


def montant(v) -> float | None:
    return ac.nombre(v)


def rang_classement(c: str) -> int:
    for i, o in enumerate(("CASSE (", "CASSE PROBABLE", "A JUGER", "CORRECTION")):
        if c.startswith(o):
            return i
    return 9


def preparer_juge() -> dict:
    """Lit le Sheet (GET) et le registre (mode=ro), et rend le juge -- voir l'en-tete."""
    ac.MORCEAUX_DE_NOM = True
    for f in (RACINE / ".env",):
        if f.exists():
            ac.load_env_file(f)
    entete, lignes = ac.lire_classeur()
    print("SHEET lu en direct : %d lignes, %d colonnes" % (len(lignes), len(entete)))
    assert entete[S] == "Offre Achat" and entete[T] == "Compromis" and entete[AB] == "Acquéreur" \
        and entete[AF] == "Prix" and entete[AL] == "ID Unique", "l'en-tete du Sheet a bouge"

    # le Sheet, indexe par DATE (colonne du genre) -- une ligne = (numero, valeurs)
    par_date = {"offre": defaultdict(list), "compromis": defaultdict(list), "vente": defaultdict(list)}
    vue = {}
    for num, l in lignes:
        l = list(l) + [""] * (38 - len(l))
        rec = {"num": num, "id": l[AL].strip(), "etat": l[R].strip(), "acq": l[AB].strip(),
               "noms": ac.mots_propres(l[AB]), "prix": montant(l[AF]), "mandat": l[C].strip(),
               "S": date_du_classeur_tolerante(l[S]), "T": date_du_classeur_tolerante(l[T]),
               "ventes": {d for d in (date_du_classeur_tolerante(l[k]) for k in (V, W, X)) if d}}
        vue[num] = rec
        if rec["S"]:
            par_date["offre"][rec["S"]].append(rec)
        if rec["T"]:
            par_date["compromis"][rec["T"]].append(rec)
        for d in rec["ventes"]:
            par_date["vente"][d].append(rec)

    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    tx = {}
    for a, bien, k, s, d, pj, acq, mt, orig, ch, u, nm in src.execute(
            "SELECT app_affaire_id, hektor_annonce_id, kind, state, date, propositions_json, acquereurs_json, "
            "montant, transaction_origine, app_chaine_id, app_dossier_uuid, numero_mandat FROM app_affaire_ledger"):
        cles = set()
        if k == "offre":
            # ⭐ la proposition ET l'acceptation (journal de Hektor) : le Sheet note l'une ou l'autre
            #   (lu a la main le 19/11, bien 50165 : S = 13/11/2025, proposition du 04/11).
            for jj in ac.dates_des_propositions(pj):
                dd = date_du_classeur_tolerante(jj)
                if dd and dd < NOS_GESTES:
                    cles.add(dd)
            if not cles and jour_hektor(_date_de_tri(k, d, pj)):
                cles.add(jour_hektor(_date_de_tri(k, d, pj)))
        elif jour_hektor(d):
            cles.add(jour_hektor(d))
        tx[a] = {"bien": str(bien), "genre": k, "etat": s, "dates": cles, "noms": noms(acq),
                 "montant": montant(mt), "classeur": orig == "classeur", "chaine": ch, "uuid": u,
                 "mandat": "".join(ch_ for ch_ in str(nm or "") if ch_.isdigit())}
    par_mandat = defaultdict(list)
    for rec in vue.values():
        m = "".join(ch_ for ch_ in rec["mandat"] if ch_.isdigit())
        if m:
            par_mandat[m].append(rec)
    gel = defaultdict(set)
    for ligne, a, ident in src.execute("SELECT ligne_classeur, app_affaire_id, id_unique FROM app_classeur_lien"):
        gel[a].add(ident or ("ligne %s" % ligne))

    def designe(a: int) -> tuple[list, str]:
        """Les lignes du Sheet qui designent la transaction a, et par quelles colonnes.

        DEUX FACONS, chacune avec au moins DEUX colonnes independantes :
          DATEE    la date du genre (S / T / V-W-X, a un jour pres) ET l'une de : le NOM (AB), le PRIX
                   (AF a 1 %), le MANDAT (C = numero_mandat de Hektor)
                   ⭐ le mandat est ajoute apres lecture a la main (biens 36794, 43114) : quand Hektor a
                     laisse le contact de l'acheteur PRECEDENT sur le compromis, ni le nom ni le prix
                     (AF est souvent le prix affiche, pas le montant) ne repondent -- la date et le
                     mandat, si.
          SANS DATE  la case du genre est VIDE au Sheet : MANDAT + NOM + PRIX ensemble
                   (lu a la main, bien 1950 : T vide, le compromis EL FAQRAOUI a 66 000 sur le mandat
                    17685 est pourtant sur la ligne)
        """
        t = tx.get(a)
        if not t or t["classeur"] or t["genre"] not in par_date:
            return [], ("creee depuis le Sheet" if t and t["classeur"] else "genre hors champ")
        col = {"offre": "S", "compromis": "T", "vente": "V/W/X"}[t["genre"]]
        trouvees, pourquoi = [], set()

        def prix_ok(rec):
            return bool(rec["prix"] and t["montant"] and abs(rec["prix"] - t["montant"]) <= 0.01 * t["montant"])

        def mandat_ok(rec):
            return bool(t["mandat"]) and "".join(c_ for c_ in rec["mandat"] if c_.isdigit()) == t["mandat"]

        for jour_t in t["dates"]:
            for delta in (0, -1, 1):
                for rec in par_date[t["genre"]].get(jour_t + timedelta(days=delta), []):
                    preuves = [n for n, ok in (("AB", bool(rec["noms"] & t["noms"])), ("AF", prix_ok(rec)),
                                               ("C", mandat_ok(rec))) if ok]
                    if preuves:
                        if rec not in trouvees:
                            trouvees.append(rec)
                        pourquoi.add("%s+%s" % (col, "+".join(preuves)))
        if t["mandat"]:
            for rec in par_mandat.get(t["mandat"], []):
                vide = {"offre": rec["S"] is None, "compromis": rec["T"] is None,
                        "vente": not rec["ventes"]}[t["genre"]]
                if vide and rec["noms"] & t["noms"] and prix_ok(rec) and rec not in trouvees:
                    trouvees.append(rec)
                    pourquoi.add("(%s vide)+C+AB+AF" % col)
        if not trouvees and not t["dates"]:
            return [], "pas de date a nous comparer, et pas de ligne mandat+nom+prix"
        return trouvees, ",".join(sorted(pourquoi))

    # ⛔ L'AMBIGUITE, trouvee par le temoin le 19/11 (bien 47815) : deux offres LE MEME JOUR AU MEME
    #   PRIX (24159 FAISANDIER, 24160 FAUDON) sont designees toutes les deux par la meme ligne -- or une
    #   ligne ne porte qu'UNE offre. Une ligne qui designe DEUX transactions du meme genre sur le meme
    #   bien ne prouve rien pour l'une ni pour l'autre : elle est AMBIGUE, et ne fait pas « meme ligne ».
    par_bien = defaultdict(list)
    for x, t in tx.items():
        par_bien[t["bien"]].append(x)
    _cache: dict[int, tuple] = {}

    def designe_c(a: int) -> tuple[list, str]:
        if a not in _cache:
            _cache[a] = designe(a)
        return _cache[a]

    def ambigues_pour(a: int) -> set:
        t = tx[a]
        rivaux = [x for x in par_bien[t["bien"]] if x != a and tx[x]["genre"] == t["genre"]]
        mes_lignes = {r["num"] for r in designe_c(a)[0]}
        return {n for x in rivaux for n in (r["num"] for r in designe_c(x)[0]) if n in mes_lignes}

    def juger(a: int, b: int) -> dict:
        la, pa = designe_c(a)
        lb, pb = designe_c(b)
        ids_a, ids_b = {r["num"] for r in la}, {r["num"] for r in lb}
        communes_brutes = ids_a & ids_b
        communes = communes_brutes - ambigues_pour(a) - ambigues_pour(b)
        # ⚠ une transaction designee par PLUSIEURS lignes ne peut appartenir qu'a une : la commune
        #   ne prouve alors rien (bien 12728 : deux lignes portent T = 30/04/2021 sur le meme mandat)
        if len(ids_a) > 1 or len(ids_b) > 1:
            communes = set()
        if communes:
            v = "MEME LIGNE"
        elif communes_brutes:
            v = "AMBIGU"
        elif ids_a and ids_b:
            v = "DEUX LIGNES"
        elif ids_a or ids_b:
            v = "UNE SEULE"
        else:
            v = "AUCUNE"
        ga, gb = gel.get(a, set()), gel.get(b, set())
        g = ("meme ligne" if ga & gb else "deux lignes" if ga and gb else
             "une seule" if ga or gb else "aucune")
        montre = [vue[n] for n in sorted(communes or (ids_a | ids_b))]
        return {"verdict": v, "colonnes_a": pa, "colonnes_b": pb,
                "lignes_a": " ".join(vue[n]["id"] or str(n) for n in sorted(ids_a)),
                "lignes_b": " ".join(vue[n]["id"] or str(n) for n in sorted(ids_b)),
                "le_sheet_nomme": " | ".join("%s : %s (%s)" % (r["id"] or r["num"], r["acq"], r["etat"])
                                             for r in montre[:3]),
                "le_gel_dit": g}

    # ⭐ LE JUGE SERT AUSSI A ⑥ (temps5_q6_...) : on le rend tel quel, sans rien recalculer
    return {"tx": tx, "vue": vue, "gel": gel, "designe": designe_c, "juger": juger, "src": src}


def main() -> int:
    J = preparer_juge()
    tx, juger = J["tx"], J["juger"]

    # LES PAIRES DU TEMPS 3, regroupees par dossier d'avant
    brut = list(csv.DictReader(PAIRES.open(encoding="utf-8")))
    dossiers = defaultdict(list)
    for p in brut:
        if p["geste"].startswith("etat") and p["sens"].startswith("SEPAREES"):
            dossiers[(p["bien"], p["dossier_avant_a"])].append(p)
    pire = {k: min(v, key=lambda x: rang_classement(x["classement"]))["classement"] for k, v in dossiers.items()}

    # LE TEMOIN DU JUGE -- des paires dont la verite est connue SANS le juge :
    #   . les 10 menages, valides par Frederic le 19/11 sur les faits : jamais DEUX LIGNES
    #   . lues A LA MAIN sur le Sheet le 19/11 : 10374 (VUNYM8UV porte l'offre VIALLE du 04/07/2020 ET le
    #     compromis du 25/09/2020) et 28673 (EC977D21 porte l'offre CHARLES du 23/08/2021 ET le compromis
    #     du 30/09/2021 ; 6D1WSAK8 porte l'offre LYONNET du 19/04/2021, seule) ;
    #   . l'ambiguite de 47815 : deux offres le 09/09/2022 a 139 700, une seule ligne.
    #   ⚠ La famille CORRECTION du temps 3 N'EST PAS un temoin : elle a ete classee sur les NOMS, et le
    #     Sheet en renverse une partie (c'est un resultat, imprime plus bas, pas un echec du juge).
    echecs = []
    menages = [(5356, 5355), (5408, 5407), (13056, 13055), (16866, 16865), (17278, 17277),
               (20196, 20195), (21339, 21337), (22069, 22068), (26825, 26824), (28328, 28327)]
    #   . ⭐ INDEPENDANT DE MON JUGE : la ligne 8Q3LHGZ4 est jugee FAUSSE par l'audit V2 (19/11) -- une
    #     affaire CHEVALIER de 2023, mandat 16239, que le gel a reliee au compromis 8321 et a l'offre 8322
    #     de 2014 (mandat 6732). Le juge ne doit PAS dire « meme ligne » pour 8321-8322.
    #   ⚠ Les autres cas lus a la main (36794, 43114, 1950, 12728) ont SERVI a construire le juge : ils
    #     sont rejoues pour qu'il ne regresse pas, mais ils ne prouvent pas son independance.
    exiges = {(4906, 4907): {"MEME LIGNE"}, (14141, 14142): {"MEME LIGNE"},
              (14143, 14142): {"DEUX LIGNES"}, (14143, 14141): {"DEUX LIGNES"}, (24159, 24158): {"AMBIGU"},
              (8321, 8322): {"AUCUNE", "UNE SEULE", "DEUX LIGNES"},
              (17322, 17320): {"MEME LIGNE"}, (21586, 21585): {"MEME LIGNE"}, (987, 988): {"MEME LIGNE"},
              (6554, 6556): {"AMBIGU", "UNE SEULE", "DEUX LIGNES"}}
    print("\nLE TEMOIN DU JUGE :")
    vm = Counter(juger(a, b)["verdict"] for a, b in menages)
    print("   les 10 menages (jamais DEUX LIGNES) : %s" % dict(vm))
    for a, b in menages:
        j = juger(a, b)
        if j["verdict"] not in ("MEME LIGNE", "AUCUNE"):
            print("      %s-%s : %s . offre %s [%s] . compromis %s [%s] . %s"
                  % (a, b, j["verdict"], j["lignes_a"] or "-", j["colonnes_a"], j["lignes_b"] or "-",
                     j["colonnes_b"], j["le_sheet_nomme"]))
    if vm.get("DEUX LIGNES"):
        echecs.append("menages")
    for (a, b), attendu in exiges.items():
        j = juger(a, b)["verdict"]
        print("   %-6s - %-6s attendu %-34s obtenu %-12s %s" % (a, b, "/".join(sorted(attendu)), j,
                                                              "ok" if j in attendu else "⛔"))
        if j not in attendu:
            echecs.append("%s-%s %s" % (a, b, j))

    # CE QUE LE SHEET DIT DES AUTRES FAMILLES DU TEMPS 3 (un resultat, pas un temoin)
    familles = Counter()
    renverses = []
    for k, v in dossiers.items():
        famille = pire[k].split("(")[0].strip()
        if famille.startswith("A JUGER"):
            continue
        for p in v:
            if p["classement"] != pire[k]:
                continue
            j = juger(int(p["a"]), int(p["b"]))["verdict"]
            familles[(famille, j)] += 1
            if (famille, j) in (("CORRECTION", "MEME LIGNE"), ("CASSE", "DEUX LIGNES"),
                                ("CASSE PROBABLE", "DEUX LIGNES")):
                renverses.append((famille, k[0], p["a"], p["b"]))
    print("\nLES AUTRES FAMILLES DU TEMPS 3, JUGEES PAR LE SHEET (paire par paire) :")
    for (f, j), n in sorted(familles.items()):
        print("   %-15s -> %-12s %4d" % (f, j, n))
    print("   ⚠ RENVERSEES par le Sheet (famille, bien, a, b) :")
    for r_ in renverses:
        print("      %s" % (r_,))

    # LES 48
    sorties_p, sorties_d, verdicts_d, verdicts_p = [], [], Counter(), Counter()
    accord_gel = Counter()
    for k in sorted(dossiers, key=lambda x: (int(x[0]), int(x[1]))):
        if not pire[k].startswith("A JUGER"):
            continue
        bien, avant = k
        juges = []
        for p in dossiers[k]:
            if not p["classement"].startswith("A JUGER"):
                continue
            j = juger(int(p["a"]), int(p["b"]))
            juges.append((p, j))
            verdicts_p[j["verdict"]] += 1
            accord_gel[(j["verdict"], j["le_gel_dit"])] += 1
            ta, tb = tx[int(p["a"])], tx[int(p["b"])]
            sorties_p.append({"bien": bien, "dossier_avant": avant, "classement": p["classement"],
                              "a": p["a"], "genre_a": p["genre_a"], "date_a": p["date_a"],
                              "noms_a": " ".join(sorted(ta["noms"])), "dossier_aujourd_hui_a": ta["chaine"],
                              "b": p["b"], "genre_b": p["genre_b"], "date_b": p["date_b"],
                              "noms_b": " ".join(sorted(tb["noms"])), "dossier_aujourd_hui_b": tb["chaine"],
                              **j})
        vs = {j["verdict"] for _, j in juges}
        if "MEME LIGNE" in vs and "DEUX LIGNES" in vs:
            vd = "MIXTE -- a lire"
        elif "MEME LIGNE" in vs:
            vd = "CASSE CONFIRMEE PAR LE SHEET"
        elif "DEUX LIGNES" in vs:
            vd = "CORRECTION CONFIRMEE PAR LE SHEET"
        else:
            vd = "NON TRANCHE PAR LE SHEET"
        verdicts_d[vd] += 1
        sorties_d.append({"bien": bien, "dossier_avant": avant, "pire_paire": pire[k], "verdict": vd,
                          "paires_jugees": len(juges),
                          "paires": " ; ".join("%s-%s %s" % (p["a"], p["b"], j["verdict"]) for p, j in juges),
                          "le_sheet_nomme": " || ".join(sorted({j["le_sheet_nomme"] for _, j in juges
                                                                if j["le_sheet_nomme"]}))[:400]})

    print("\nLES 48 DOSSIERS « A JUGER » -- %d dossiers, %d paires jugees" % (len(sorties_d), len(sorties_p)))
    print("PAR PAIRE :")
    for k, n in verdicts_p.most_common():
        print("   %-14s %4d" % (k, n))
    print("PAR DOSSIER :")
    for k, n in verdicts_d.most_common():
        print("   %-40s %4d" % (k, n))
    print("APRES COUP, LE GEL (il ne sert pas a choisir) -- verdict du juge / ce que dit le gel :")
    for (v, g), n in sorted(accord_gel.items()):
        print("   %-14s / %-12s %4d" % (v, g, n))
    for chemin, rangs in ((SORTIE_PAIRES, sorties_p), (SORTIE_DOSSIERS, sorties_d)):
        with chemin.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rangs[0].keys()))
            w.writeheader()
            w.writerows(rangs)
        print("CSV : %s" % chemin)
    if echecs:
        print("⛔ LE TEMOIN DU JUGE A ECHOUE (code 2) : %s" % echecs[:10])
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
