#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LA REGLE E -- LE COMPTE DEFINITIF, SUR LA BASE DU MATIN DU 20/11, REUNION PAR REUNION.     20/11/2026

    .venv\Scripts\python.exe -u -X utf8 phase2\checks\regle_e_compte_definitif_2026-11-20.py

LA DEMANDE (Frederic, 20/11 au matin, apres le controle des 10) : avant tout allumage,
    - combien de reunions, combien de transactions, et la LISTE nom par nom ;
    - pour chacune : ce que E reunit, quelle etiquette est GARDEE, laquelle est ABSORBEE ;
    - lesquelles touchent une ligne du classeur, et laquelle ;
    - les 5 exclusions declarees, rappelees, pour voir qu'elles sont dehors.

⛔ CE SCRIPT N'ECRIT RIEN, NULLE PART SAUF SES DEUX FICHIERS DE SORTIE :
  phase2.sqlite en mode=ro, copie en memoire ; l'interrupteur APP_CHAINAGE_SANS_DATE_VISIBLE n'est pose
  QUE dans ce processus, jamais dans .env ; le Sheet est LU (GET), jamais ecrit ; rien chez Hektor.

LA METHODE -- la meme que temps4 (qui donne les chiffres) :
    N   la vraie fonction, regle E ETEINTE  -> doit redonner la base a 0 ecart (temoin)
    E   la vraie fonction, regle E ALLUMEE
    une REUNION = un dossier de E qui rassemble plusieurs dossiers de N.
L'ETIQUETTE -- la RPC app_poser_etiquettes_dossier garde, dans un groupe a plusieurs etiquettes, celle de la
    transaction au PLUS PETIT NUMERO (prouve cette nuit sur les 10 menages : 10 fusions sur 10 comme predit).
LE CLASSEUR -- les lignes reliees par le GEL d'aujourd'hui (app_classeur_lien, le patch V2 n'est PAS joue),
    lues dans le Sheet en direct.

Sorties : notice/CHANTIER_CLASSEUR_REGLE_E_COMPTE_DEFINITIF_2026-11-20.md et .csv
Code : 0 compte fait, temoins verts . 2 un temoin a echoue.
"""
from __future__ import annotations

import contextlib
import csv
import io
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
from phase2.sync.affaire_ledger import (                                    # noqa: E402
    EXCLUES_DE_LA_REGLE_E, LEDGER_TABLE, _acquereurs, _date_de_tri, recalculer_les_chaines)

BASE = RACINE / "phase2" / "phase2.sqlite"
SORTIE_MD = RACINE / "notice" / "CHANTIER_CLASSEUR_REGLE_E_COMPTE_DEFINITIF_2026-11-20.md"
SORTIE_CSV = SORTIE_MD.with_suffix(".csv")
#: la prediction d'hier soir (base d'AVANT la nuit des 10), figee a 00:40 par « regle_e reference »
PREDICTION_HIER = RACINE.parent / "chantier_classeur_q6_cache" / "controles_nuit" / "regle_e_prediction_2026-11-20_0040.csv"
INTERRUPTEUR = "APP_CHAINAGE_SANS_DATE_VISIBLE"
LES_10 = {5356, 5408, 13056, 16866, 17278, 20196, 21339, 22069, 26825, 28328}
# colonnes du Sheet (0 = A)
A, R, S, T, AB, AF, AL = 0, 17, 18, 19, 27, 31, 37
GENRE = {"offre": "offre", "compromis": "compromis", "vente": "vente"}
ETAT = {"cancelled": "annule", "annule": "annule", "refused": "refusee", "accepted": "acceptee",
        "active": "actif", "proposed": "proposee", "": ""}


def copie() -> sqlite3.Connection:
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    mem = sqlite3.connect(":memory:")
    src.backup(mem)
    src.close()
    return mem


def rejouer(allumee: bool) -> tuple[dict, dict]:
    os.environ[INTERRUPTEUR] = "1" if allumee else "0"
    con = copie()
    with contextlib.redirect_stdout(io.StringIO()):
        compte = recalculer_les_chaines(con)
    chaines = dict(con.execute(f"SELECT app_affaire_id, app_chaine_id FROM {LEDGER_TABLE}"))
    con.close()
    os.environ[INTERRUPTEUR] = "0"
    return chaines, compte


def euros(v) -> str:
    try:
        return "{:,.0f}".format(float(v)).replace(",", " ") + " €"
    except (TypeError, ValueError):
        return "montant ?"


def main() -> int:
    t0 = time.time()
    echecs: list[str] = []
    src = sqlite3.connect(f"file:{BASE}?mode=ro", uri=True)
    info, en_base = {}, {}
    import apparier_classeur as ac                                          # noqa: E402
    for a, bien, k, s, d, acq, pj, ch, u, num, pres, mt in src.execute(
            f"SELECT app_affaire_id, hektor_annonce_id, kind, state, date, acquereurs_json, propositions_json, "
            f"app_chaine_id, app_dossier_uuid, hektor_affaire_id, present_in_hektor, montant FROM {LEDGER_TABLE}"):
        tri = _date_de_tri(k, d, pj)
        info[a] = {"bien": str(bien), "genre": k, "etat": (s or "").lower(), "tri": tri,
                   "acqs": _acquereurs(acq), "noms": ac.noms_du_blob(acq).strip() or "(sans nom)",
                   "uuid": u, "hektor": str(num or ""), "montant": mt,
                   "effacee": bool(str(num or "").strip()) and str(pres) in ("0", "false", "False")}
        en_base[a] = ch
    gel = defaultdict(set)
    for i, a in src.execute("SELECT id_unique, app_affaire_id FROM app_classeur_lien"):
        if i and a is not None:
            gel[int(a)].add(str(i).strip())
    src.close()
    print("base lue : %d transactions, %d dossiers, %d etiquettes, %d sans etiquette (%.0f s)" % (
        len(info), len(set(en_base.values())), len({x["uuid"] for x in info.values() if x["uuid"]}),
        sum(1 for x in info.values() if not x["uuid"]), time.time() - t0), flush=True)

    n, compte_n = rejouer(False)
    print("N rejoue (%.0f s)" % (time.time() - t0), flush=True)
    e, compte_e = rejouer(True)
    print("E rejoue (%.0f s)" % (time.time() - t0), flush=True)
    ecarts = sorted(a for a in n if n[a] != en_base[a])
    print("TEMOIN N = la base : %d ecart(s) (attendu 0) %s" % (len(ecarts), ecarts[:10]))
    if ecarts:
        echecs.append("N != base")

    par_n, par_e = defaultdict(set), defaultdict(set)
    for a, c in n.items():
        par_n[c].add(a)
    for a, c in e.items():
        par_e[c].add(a)
    coupes = sum(1 for m in par_n.values() if len({e[x] for x in m}) > 1)
    if coupes:
        echecs.append("E coupe %d dossier(s)" % coupes)

    # ── LES REUNIONS ──
    reunions = []
    for c, membres in par_e.items():
        venus = defaultdict(set)
        for m in membres:
            venus[n[m]].add(m)
        if len(venus) < 2:
            continue
        seuls = sorted(next(iter(v)) for v in venus.values() if len(v) == 1 and info[next(iter(v))]["tri"] is None)
        garde_tx = min(membres)
        gardee = info[garde_tx]["uuid"]
        uuids = {}
        for cn, ms in venus.items():
            for m in ms:
                uuids.setdefault(info[m]["uuid"], set()).add(m)
        absorbees = sorted(u for u in uuids if u != gardee)
        reunions.append({"chaine_e": c, "membres": membres, "venus": venus, "seuls": seuls,
                         "garde_tx": garde_tx, "gardee": gardee, "absorbees": absorbees, "uuids": uuids})
    reunions.sort(key=lambda r: (int(info[r["garde_tx"]]["bien"]) if info[r["garde_tx"]]["bien"].isdigit() else 0))
    n_tx = sum(len(r["seuls"]) for r in reunions)
    biens = {info[r["garde_tx"]]["bien"] for r in reunions}
    print("REUNIONS : %d . transactions sans date rattachees : %d . biens : %d . dossiers %d -> %d . coupes %d" % (
        len(reunions), n_tx, len(biens), len(par_n), len(par_e), coupes), flush=True)

    # ── LES EXCLUSIONS ──
    excl = []
    for t, pourquoi in EXCLUES_DE_LA_REGLE_E.items():
        if t not in info:
            excl.append((t, None, "⛔ ABSENTE DU REGISTRE", pourquoi))
            echecs.append("exclusion %s absente" % t)
            continue
        seule = len(par_e[e[t]]) == 1
        excl.append((t, info[t], "RESTE SEULE" if seule else "⛔ REUNIE MALGRE L'EXCLUSION", pourquoi))
        if not seule:
            echecs.append("exclusion %s reunie" % t)
        if any(t in r["membres"] for r in reunions):
            echecs.append("exclusion %s dans une reunion" % t)
    dites = compte_e.get("[E] exclusion declaree -- laissee seule (EXCLUES_DE_LA_REGLE_E)", 0)
    if dites != len(EXCLUES_DE_LA_REGLE_E):
        echecs.append("exclusions dites %s / %d" % (dites, len(EXCLUES_DE_LA_REGLE_E)))
    # les 10 menages de cette nuit : aucune reunion de E ne doit les defaire
    for t in LES_10:
        if len({e[x] for x in par_n[n[t]]}) > 1:
            echecs.append("le menage %s coupe par E" % t)

    # ── LE SHEET (GET) ──
    ac.MORCEAUX_DE_NOM = True
    ac.load_env_file(RACINE / ".env")
    entete, lignes = ac.lire_classeur()
    assert entete[A] == "affair_uuid" and entete[AL] == "ID Unique" and entete[AB] == "Acquéreur" \
        and entete[S] == "Offre Achat" and entete[T] == "Compromis" and entete[AF] == "Prix", "l'en-tete du Sheet a bouge"
    lig = {}
    for num, l in lignes:
        l = [str(x) for x in list(l)] + [""] * (len(entete) - len(l))
        lig[l[AL].strip()] = {"num": num, "A": l[A].strip(), "etat": l[R].strip(), "S": l[S].strip(),
                              "T": l[T].strip(), "acq": l[AB].strip(), "prix": l[AF].strip()}
    col_a_remplie = sum(1 for x in lig.values() if x["A"])
    print("SHEET lu en direct : %d lignes, colonne A remplie sur %d (%.0f s)" % (len(lig), col_a_remplie,
                                                                                  time.time() - t0), flush=True)

    def lignes_de(ms):
        return sorted({i for m in ms for i in gel.get(m, set()) if i in lig})

    def court_ligne(i):
        x = lig[i]
        return "%s (ligne %d, %s, « %s », offre %s, compromis %s, %s%s)" % (
            i, x["num"], x["etat"] or "etat ?", x["acq"] or "acquereur vide", x["S"] or "-", x["T"] or "-",
            x["prix"] or "prix ?", ", COLONNE A DEJA REMPLIE : %s" % x["A"][:8] if x["A"] else "")

    def court_tx(a):
        x = info[a]
        etat_ = ETAT.get(x["etat"], x["etat"])
        return "%s %s%s (Hektor %s, %s, %s, %s)" % (
            GENRE.get(x["genre"], x["genre"]), a, " " + etat_ if etat_ else "", x["hektor"] or "-",
            x["noms"], euros(x["montant"]), (x["tri"] or "SANS DATE")[:10])

    # ── LA PREDICTION D'HIER SOIR ──
    hier = {}
    if PREDICTION_HIER.exists():
        with PREDICTION_HIER.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                hier[int(r["transaction"])] = r
    auj = {t: r for r in reunions for t in r["seuls"]}
    nouvelles = sorted(set(auj) - set(hier))
    disparues = sorted(set(hier) - set(auj))
    etiq_changee = sorted(t for t in set(auj) & set(hier) if hier[t]["etiquette_gardee"] != auj[t]["gardee"])

    # ── LES SORTIES ──
    md, rows, sommaire, lignes_changent = [], [], [], set()
    verdicts, touche = Counter(), Counter()
    for k, r in enumerate(reunions, 1):
        seuls = r["seuls"]
        cible = sorted(r["membres"] - set(seuls))
        cotes_lignes = {"seule": lignes_de(seuls), "cible": lignes_de(cible)}
        l_abs = sorted({i for u in r["absorbees"] for i in lignes_de(r["uuids"][u])})
        l_gar = lignes_de(r["uuids"].get(r["gardee"], set()))
        perd_cible = r["gardee"] in {info[t]["uuid"] for t in seuls}
        # le Sheet juge : les acquereurs (AB) des lignes de chaque cote
        mots = {c: set().union(*(ac.mots_propres(lig[i]["acq"]) for i in ls)) if ls else set()
                for c, ls in cotes_lignes.items()}
        if cotes_lignes["seule"] and cotes_lignes["cible"]:
            if mots["seule"] & mots["cible"]:
                sheet = "MEME ACHETEUR des deux cotes"
            elif not (mots["seule"] and mots["cible"]):
                sheet = "acquereur illisible d'un cote"
            else:
                # la lecture de temps6 (19/11 au soir, § 10.4) : le cote « annule » (que des compromis annules /
                #   offres refusees) est relie par le GEL a une ligne « Annulee » ; si AUCUNE de ces lignes ne date
                #   un compromis (colonne T vide), le Sheet dit lui-meme que cet acheteur n'a jamais signe -- le
                #   compromis annule sans date n'est pas le sien : c'est le LIEN DU GEL qui est suspect.
                cotes_annules = [cotes_lignes[c] for c, ts in (("seule", seuls), ("cible", cible))
                                 if all(info[a]["etat"] in ("cancelled", "refused") for a in ts)]
                l_ann = {i for ls in cotes_annules for i in ls}
                sheet = ("ACHETEURS DIFFERENTS, mais la ligne annulee ne date AUCUN compromis : LIEN DU GEL SUSPECT"
                         " -- E probablement juste" if l_ann and all(not lig[i]["T"] for i in l_ann)
                         else "ACHETEURS DIFFERENTS, la ligne annulee DATE un compromis -- E DOUTEUSE")
        elif cotes_lignes["seule"] or cotes_lignes["cible"]:
            sheet = "le Sheet ne voit qu'un cote"
        else:
            sheet = "aucune ligne du classeur"
        verdicts[sheet] += 1
        touche["touche le classeur" if (cotes_lignes["seule"] or cotes_lignes["cible"]) else "ne touche pas"] += 1
        b = info[r["garde_tx"]]["bien"]
        sommaire.append("%d. bien %s · %s → dossier %s · gardée `%s` (%s) · absorbée %s · classeur : %s · %s" % (
            k, b, " + ".join("%s %s %s" % (GENRE.get(info[t]["genre"]), t, info[t]["noms"]) for t in seuls),
            " / ".join(sorted({info[x]["noms"] for x in cible})), r["gardee"][:8],
            "celle de la transaction sans date" if perd_cible else "celle du dossier",
            " ".join("`%s`" % u[:8] for u in r["absorbees"]),
            ("%s ; étiquette changée sur %s" % (" ".join(sorted(set(cotes_lignes["seule"] + cotes_lignes["cible"]))),
                                                " ".join(l_abs) or "aucune"))
            if cotes_lignes["seule"] or cotes_lignes["cible"] else "aucune ligne", sheet))
        lignes_changent.update(l_abs)
        md.append("")
        md.append("### %d. Bien %s -- %s" % (k, b, " / ".join(sorted({info[t]["noms"] for t in seuls}))))
        for t in seuls:
            md.append("- **E rattache** : %s" % court_tx(t))
        md.append("- **au dossier** (chaine %s aujourd'hui) : %s" % (
            ", ".join(str(c_) for c_ in sorted({n[x] for x in cible})),
            " ; ".join(court_tx(x) for x in cible)))
        md.append("- **etiquette GARDEE** : `%s` -- celle %s (la transaction %s a le plus petit numero)" % (
            r["gardee"], "de la transaction SANS DATE : l'etiquette du dossier cible disparait" if perd_cible
            else "du dossier cible (cas normal)", r["garde_tx"]))
        for u in r["absorbees"]:
            md.append("- **etiquette ABSORBEE** : `%s` -- portee par %s" % (
                u, ", ".join(str(x) for x in sorted(r["uuids"][u]))))
        if cotes_lignes["seule"] or cotes_lignes["cible"]:
            for c, nom in (("seule", "cote de la transaction sans date"), ("cible", "cote du dossier cible")):
                md.append("- **classeur, %s** : %s" % (nom, " ; ".join(court_ligne(i) for i in cotes_lignes[c]) or "aucune ligne"))
            md.append("- **ligne(s) dont l'etiquette CHANGE** (elles portaient l'absorbee) : %s" % (
                " ".join(l_abs) or "aucune"))
        else:
            md.append("- **classeur** : aucune ligne reliee")
        md.append("- **le Sheet** : %s" % sheet)
        if any(t in nouvelles for t in seuls):
            md.append("- ⚠ **NOUVELLE depuis hier soir**")
        if any(t in etiq_changee for t in seuls):
            md.append("- ⚠ **l'etiquette gardee a change depuis hier soir** (hier : %s)" % ", ".join(
                hier[t]["etiquette_gardee"] for t in seuls if t in etiq_changee))
        for t in seuls:
            rows.append({"n": k, "bien": b, "transaction_sans_date": t, "genre": info[t]["genre"],
                         "etat": info[t]["etat"], "hektor": info[t]["hektor"], "acquereur": info[t]["noms"],
                         "montant": info[t]["montant"], "dossier_cible": " ".join(str(x) for x in cible),
                         "dossier_cible_detail": " ; ".join(court_tx(x) for x in cible),
                         "etiquette_gardee": r["gardee"], "gardee_par_transaction": r["garde_tx"],
                         "etiquette_du_dossier_cible_absorbee": perd_cible,
                         "etiquettes_absorbees": " ".join(r["absorbees"]),
                         "lignes_classeur_cote_sans_date": " ".join(cotes_lignes["seule"]),
                         "lignes_classeur_cote_cible": " ".join(cotes_lignes["cible"]),
                         "lignes_dont_l_etiquette_change": " ".join(l_abs),
                         "lignes_qui_gardent_leur_etiquette": " ".join(l_gar),
                         "le_sheet": sheet, "nouvelle_depuis_hier": t in nouvelles,
                         "etiquette_changee_depuis_hier": t in etiq_changee})

    tete = []
    tete.append("# La règle E — le compte DÉFINITIF, sur la base du 20/11 au matin")
    tete.append("")
    tete.append("> Produit par `phase2/checks/regle_e_compte_definitif_2026-11-20.py` le %s, en lecture seule "
                "(base en mode=ro, copie en mémoire ; l'interrupteur posé dans ce seul processus ; le Sheet lu, "
                "jamais écrit). ⛔ **E n'est PAS allumée.** La liste ligne par ligne est dans le CSV voisin."
                % datetime.now().strftime("%d/%m/%Y à %H:%M"))
    tete.append("")
    tete.append("## Le compte")
    tete.append("")
    tete.append("- **%d réunions de dossiers**, **%d transactions sans date rattachées**, sur **%d biens**."
                % (len(reunions), n_tx, len(biens)))
    tete.append("- Dossiers : **%d → %d** ; dossiers coupés par E : **%d**." % (len(par_n), len(par_e), coupes))
    tete.append("- Étiquettes absorbées : **%d**, dans %d réunions : dans **%d** réunions c'est l'étiquette du "
                "DOSSIER CIBLE qui disparaît (la transaction sans date a le plus petit numéro), dans **%d** c'est celle "
                "de la transaction sans date (cas normal)."
                % (sum(len(r["absorbees"]) for r in reunions), len(reunions),
                   sum(1 for r in reunions if r["gardee"] in {info[t]["uuid"] for t in r["seuls"]}),
                   sum(1 for r in reunions if r["gardee"] not in {info[t]["uuid"] for t in r["seuls"]})))
    tete.append("- Fusions que la pose fera en une nuit : **%d à %d** (une par réunion, ou une par étiquette absorbée ; "
                "le cri « ATTENTION ETIQUETTES » sonne à 10 : **il sonnera, c'est attendu**)."
                % (len(reunions), sum(len(r["absorbees"]) for r in reunions)))
    tete.append("- Lignes du classeur dont l'étiquette future CHANGE (elles sont reliées au côté absorbé) : **%d** — "
                "%s. ⭐ La colonne A n'étant remplie sur aucune ligne, **aucune étiquette déjà écrite n'est "
                "démentie** : la vague 0 et la vague 1 se calculent après E." % (
                    len(lignes_changent), " ".join(sorted(lignes_changent)) or "aucune"))
    tete.append("- Témoins : N = la base à **%d** écart ; les 10 ménages de cette nuit **%s** ; "
                "exclusions dites par le compte rendu **%s / %d**."
                % (len(ecarts), "intacts" if not any("menage" in x for x in echecs) else "⛔ TOUCHÉS",
                   dites, len(EXCLUES_DE_LA_REGLE_E)))
    tete.append("- Le classeur : **%d** réunions touchent au moins une ligne, **%d** n'en touchent aucune. "
                "Le Sheet : %s." % (touche["touche le classeur"], touche["ne touche pas"],
                                    " · ".join("%s %d" % (k_, v_) for k_, v_ in verdicts.most_common())))
    tete.append("- Comparé à la prédiction d'hier soir (base d'avant la nuit des 10, figée à 00:40) : "
                "**%d** nouvelle(s), **%d** disparue(s), **%d** étiquette(s) gardée(s) changée(s)%s."
                % (len(nouvelles), len(disparues), len(etiq_changee),
                   (" — " + " ".join(str(x) for x in nouvelles + disparues + etiq_changee))
                   if nouvelles or disparues or etiq_changee else ""))
    tete.append("- Sheet lu en direct : %d lignes ; colonne A déjà remplie sur **%d** ligne(s)." % (len(lig), col_a_remplie))
    tete.append("")
    tete.append("## Les 5 exclusions déclarées — dehors")
    tete.append("")
    for t, x, etat_, pourquoi in excl:
        if x is None:
            tete.append("- **%s** : %s" % (t, etat_))
            continue
        tete.append("- **%s** — bien %s, %s — **%s** dans le rejeu. *%s*" % (
            t, x["bien"], court_tx(t), etat_, " ".join(pourquoi.split())))
    tete.append("")
    tete.append("## La liste, une ligne par réunion")
    tete.append("")
    tete.extend(sommaire)
    tete.append("")
    tete.append("## Les %d réunions, en détail" % len(reunions))
    sortie = "\n".join(tete + md) + "\n\n## Ce qui n'est pas mesuré ici\n\n" + "\n".join([
        "- Le lien vers le classeur passe par le **gel d'aujourd'hui** (`app_classeur_lien`) : le patch V2 du gel "
        "n'est pas joué, et une ligne que le gel ne relie pas n'apparaît pas.",
        "- La simulation de l'étiquette suit la règle de la RPC (le plus petit numéro) ; elle a été prouvée cette nuit "
        "sur les 10 ménages, pas sur ces 29.",
        "- Ce compte vaut pour la base de ce matin : une nuit de Hektor peut ajouter ou changer une transaction "
        "d'ici l'allumage ; le contrôle de samedi compare la nuit réelle à la référence figée.",
    ]) + "\n"
    if echecs:
        sortie += "\n⛔ **TÉMOIN(S) EN ÉCHEC** : %s\n" % "; ".join(echecs)
    SORTIE_MD.write_bytes(sortie.encode("utf-8"))
    with SORTIE_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["vide"])
        w.writeheader()
        w.writerows(rows)
    print("comparaison a hier soir : nouvelles %s . disparues %s . etiquette gardee changee %s" % (
        nouvelles, disparues, etiq_changee))
    print("le Sheet : %s" % dict(verdicts))
    print("le classeur : %s" % dict(touche))
    print("exclusions : %s" % [(t, et) for t, _, et, _ in excl])
    print("ECRIT : %s\n        %s (%.0f s)" % (SORTIE_MD, SORTIE_CSV, time.time() - t0))
    if echecs:
        print("⛔ TEMOIN(S) EN ECHEC : %s (code 2)" % echecs)
        return 2
    print("VERDICT : temoins verts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
