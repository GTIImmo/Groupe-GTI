#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""ETAPE 3 BIS, LOT C -- LES REPARTITIONS QUI MANQUENT (les 6 colonnes des negociateurs), CHEZ NOUS SEULEMENT.  27/11/2026

    python -X utf8 -u phase2\checks\etape_3bis_lot_c_repartitions_generer_patch_2026-11-27.py

⛔ N'ECRIT RIEN EN BASE : il lit l'image du passage officiel 84, son verdict (socle, lecture seule), l'annuaire local
   (phase2.sqlite, lecture seule) et la base (lecture seule), et GENERE patch + A_BLANC + INVERSE + REPETITION.

LA REGLE DU 13/11, TELLE QUELLE (le meme calcul que le rapatriement du 13/11 et que l'audit des 18) : RR.nettoyer, puis
RR.resoudre chaque nom dans l'annuaire, puis RR.decomposer en parts DU TOTAL, cote entree et cote sortie.
⭐ SEULEMENT les lignes dont AUCUNE chaine ne porte de part (« 3 manque » de l'audit) : on pose, on ne remplace rien.
⭐ LA CHAINE : celle de la piece la plus avancee de la ligne au passage 84 (vente, puis compromis, puis offre).
⭐ L'ORIGINE « classeur_reconstitue », celle du 13/11 -- et c'est elle qui protege la chaine LA NUIT : la RPC
   app_repartition_absorber saute toute chaine qui porte une part dont l'origine ne commence pas par « hektor » (lu le
   27/11 au soir dans la base). ⛔ La phrase « la nuit ne touche pas les repartitions » du plan etait trop large : la nuit
   reecrit les parts d'origine hektor ; elle ne touche pas une chaine qui porte une part classeur.
⛔ LA PART QUI DIFFERE (1 ligne) N'EST PAS DANS CE LOT : sa regle 6, « on ne supprime pas une part, on la met de cote » --
   elle lui est presentee a part.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import coupe_preuve_interne as K  # noqa: E402
import rapatrier_repartition_classeur as RR  # noqa: E402

PASSAGE = 84
MARQUE = "classeur:3bisC:2026-11-27"
BASE = P.RACINE / "supabase" / "patch_3bis_lot_c_repartitions_2026-11-27"
RANG = {"vente": 0, "compromis": 1, "offre": 2}


def q(s) -> str:
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"


def main() -> int:
    so = sqlite3.connect("file:%s?mode=ro" % P.SOCLE.as_posix(), uri=True)
    image = so.execute("select image from passage where id=?", (PASSAGE,)).fetchone()[0]
    V = {i: json.loads(ps) if ps else [] for i, v, ps in
         so.execute("select id_unique, verdict, pieces from verdict where passage=?", (PASSAGE,)) if v == "TRANCHEE"}
    so.close()
    S = json.loads((P.IMAGES / image / "sheet.json").read_text(encoding="utf-8"))
    COL = {c: k for k, c in enumerate(S["entete"])}
    ROW = {i: e[0]["row"] for i, e in S["par_id"].items()}

    def case(i, c):
        r = ROW.get(i) or []
        k = COL[c]
        return (str(r[k]) if k < len(r) and r[k] is not None else "").strip()

    cn, cu = P.pooler()
    cu.execute("select app_affaire_id, kind, app_dossier_id, app_chaine_id from public.app_affaire_ledger")
    L = {int(a): (k, d, c) for a, k, d, c in cu.fetchall()}
    cu.execute("select distinct app_chaine_id from public.app_affaire_repartition")
    AVEC_PARTS = {int(r[0]) for r in cu.fetchall()}
    cn.close()
    # l'annuaire, exactement comme l'audit des 18 (la regle du 13/11)
    RR.RAP.ALIAS_NEGOCIATEUR = dict(RR.RAP.ALIAS_REPLI)
    loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
    loc.row_factory = sqlite3.Row
    gens = defaultdict(list)
    for r in loc.execute("select hektor_user_id, nom, prenom, is_active from app_hektor_negotiator_agency_directory"):
        nom_ = " ".join(sorted(RR.mots_du_nom(r["nom"])))
        pre_ = " ".join(sorted(RR.mots_du_nom(r["prenom"])))
        if nom_:
            gens[(nom_, pre_)].append(dict(r))
    PAR_NOM = defaultdict(list)
    for (nom_, pre_), fiches in gens.items():
        act = [f_ for f_ in fiches if f_.get("is_active") in (1, "1", True, "true", "True")]
        choix = sorted(act or fiches, key=lambda f_: int(str(f_["hektor_user_id"])))[0]
        PAR_NOM[nom_].append({"nom": nom_, "prenom": pre_, "hektor_user_id": str(choix["hektor_user_id"]),
                              "fiches": len(fiches), "nom_vrai": (str(choix.get("prenom") or "") + " " +
                                                                  str(choix.get("nom") or "")).strip().upper()})
    loc.close()

    cpt = Counter()
    lignes = []
    chaines_vues = {}
    for i in sorted(V):
        noms = [case(i, "Négociateur %d" % k) for k in (1, 2, 3)]
        if not any(noms) or i not in ROW:
            continue
        ps_ = sorted((a for a in V[i] if a in L), key=lambda a: (RANG.get(L[a][0], 3), a))
        if not ps_:
            cpt["sans piece chez nous"] += 1
            continue
        if any(L[a][2] is not None and int(L[a][2]) in AVEC_PARTS for a in ps_):
            cpt["deja une part sur une de ses chaines (pas ce lot)"] += 1
            continue
        pcts = [K.nombre(case(i, "Pourcentage %d" % k)) for k in (1, 2, 3)]
        parts, pq = RR.nettoyer(noms, pcts)
        if pq:
            cpt["⛔ je ne sais pas lire la ligne (regle du 13/11) : nettoyage"] += 1
            continue
        qui, refus = {}, ""
        for nom, _p in parts:
            qq, motif = RR.resoudre(nom, PAR_NOM, None, set())
            if motif:
                refus = motif
                break
            qui[nom] = qq
        if refus:
            cpt["⛔ je ne sais pas lire la ligne (regle du 13/11) : resolution"] += 1
            continue
        cotes, pq = RR.decomposer(parts)
        if pq:
            cpt["⛔ je ne sais pas lire la ligne (regle du 13/11) : decomposition"] += 1
            continue
        cible = ps_[0]
        k, dossier, chaine = L[cible]
        if chaine is None:
            cpt["⛔ la piece la plus avancee n'a pas de chaine"] += 1
            continue
        if int(chaine) in chaines_vues:
            cpt["⛔ deux lignes sur la meme chaine (signalee, rien pose) : %s" % chaines_vues[int(chaine)]] += 1
            continue
        chaines_vues[int(chaine)] = i
        cpt["POSEE : la chaine de sa piece la plus avancee (%s)" % k] += 1
        for c_, r_, n_, pc_ in cotes:
            lignes.append((int(chaine), dossier, c_, int(r_), qui[n_]["hektor_user_id"],
                           qui[n_].get("nom_vrai") or n_.upper(), round(float(pc_), 3), i))
    for k_, n in sorted(cpt.items()):
        print("   %5d  %s" % (n, k_))
    ch = sorted({x[0] for x in lignes})
    print("   parts a poser : %d sur %d chaines" % (len(lignes), len(ch)))
    tot = defaultdict(float)
    for x in lignes:
        tot[x[0]] += x[6]
    assert all(t <= 100.001 for t in tot.values()), "une chaine depasserait 100 %"

    corps = ["-- 1. LA GARDE : aucune de ces %d chaines ne porte de part, et rien du lot n'est pose" % len(ch),
             "do $$ begin\n  if exists (select 1 from public.app_affaire_repartition where app_chaine_id in (%s))\n"
             "     or exists (select 1 from public.app_affaire_repartition where ecrit_par = %s) then\n"
             "    raise exception '⛔ garde : une de ces chaines porte deja une part (ou le lot est pose) -- rien n''est ecrit';\n"
             "  end if;\nend $$;" % (", ".join(map(str, ch)) or "NULL", q(MARQUE)),
             "-- 2. LES PARTS (%d), origine classeur_reconstitue (celle du 13/11 : elle protege la chaine la nuit)" % len(lignes),
             "insert into public.app_affaire_repartition (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id,\n"
             "       nom_au_moment, pourcentage, origine, ecrit_par)\nvalues\n" + "\n".join(
                 # ⚠ 27/11 : la virgule AVANT le commentaire -- en fin de ligne, le commentaire l'avalait (l'a blanc l'a vu)
                 "  (%d, %s, %s, %d, %s, %s, %s, 'classeur_reconstitue', %s)%s  -- %s" % (
                     c, d if d is not None else "NULL", q(co), r, q(u), q(nm), pc, q(MARQUE),
                     "," if k_ < len(lignes) - 1 else ";", i)
                 for k_, (c, d, co, r, u, nm, pc, i) in enumerate(lignes)),
             "-- 3. LES CONTROLES",
             "do $$ declare n int; begin\n"
             "  select count(*) into n from public.app_affaire_repartition where ecrit_par = %s;\n"
             "  if n <> %d then raise exception '⛔ controle : %% parts posees (attendu %d)', n; end if;\n"
             "  select count(distinct app_chaine_id) into n from public.app_affaire_repartition where ecrit_par = %s;\n"
             "  if n <> %d then raise exception '⛔ controle : %% chaines (attendu %d)', n; end if;\n"
             "  select count(*) into n from (select app_chaine_id from public.app_affaire_repartition where ecrit_par = %s\n"
             "   group by 1 having sum(pourcentage) > 100.001) x;\n"
             "  if n <> 0 then raise exception '⛔ controle : %% chaine(s) au-dela de 100 %%%%', n; end if;\n"
             "  raise notice '✅ lot 3 bis C : %d parts sur %d chaines, origine classeur_reconstitue';\n"
             "end $$;" % (q(MARQUE), len(lignes), len(lignes), q(MARQUE), len(ch), len(ch), q(MARQUE), len(lignes), len(ch))]
    tete = ("-- %s -- ETAPE 3 BIS, LOT C (les repartitions qui manquent), chez nous seulement, jamais chez Hektor\n"
            "-- Genere par phase2/checks/etape_3bis_lot_c_repartitions_generer_patch_2026-11-27.py (passage officiel %d, image %s)\n")
    txt = "\n".join(corps) + "\n"
    (BASE.parent / (BASE.name + ".sql")).write_text(tete % (BASE.name, PASSAGE, image) + "\nbegin;\n" + txt + "commit;\n",
                                                    encoding="utf-8")
    (BASE.parent / (BASE.name + "_A_BLANC.sql")).write_text(
        tete % ("A BLANC de " + BASE.name, PASSAGE, image) + "-- ⛔ SANS commit : il finit par une erreur VOULUE.\n\nbegin;\n"
        + txt + "do $$ begin raise exception 'A BLANC LOT 3 BIS C VERT -- RIEN N''EST ECRIT'; end $$;\n", encoding="utf-8")
    (BASE.parent / (BASE.name + "_INVERSE.sql")).write_text(
        "-- INVERSE de %s : retire SES parts (ecrit_par = %s), rien d'autre (lecon 31).\n\nbegin;\n"
        "delete from public.app_affaire_repartition where ecrit_par = %s;\n"
        "do $$ begin if exists (select 1 from public.app_affaire_repartition where ecrit_par = %s) then\n"
        "  raise exception '⛔ inverse : une part du lot reste'; end if;\n  raise notice '✅ inverse : le lot 3 bis C est retire';\n"
        "end $$;\ncommit;\n" % (BASE.name, MARQUE, q(MARQUE), q(MARQUE)), encoding="utf-8")
    (BASE.parent / (BASE.name + "_REPETITION.sql")).write_text(
        "-- REPETITION de %s (lecture seule) -- attendu : %d parts sur %d chaines, aucune au-dela de 100 %%\n"
        "select (select count(*) from public.app_affaire_repartition where ecrit_par = %s) parts,\n"
        "       (select count(distinct app_chaine_id) from public.app_affaire_repartition where ecrit_par = %s) chaines,\n"
        "       (select count(*) from (select app_chaine_id from public.app_affaire_repartition group by 1\n"
        "         having sum(pourcentage) > 100.001) x) chaines_au_dela_de_100;\n"
        % (BASE.name, len(lignes), len(ch), q(MARQUE), q(MARQUE)), encoding="utf-8")
    for f in sorted(BASE.parent.glob(BASE.name + "*.sql")):
        print("   %s  md5 %s  %d octets" % (f.name, hashlib.md5(f.read_bytes()).hexdigest()[:8], f.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
