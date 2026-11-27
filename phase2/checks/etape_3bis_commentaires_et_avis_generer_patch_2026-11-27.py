#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""ETAPE 3 BIS, LOT A -- LES COMMENTAIRES (G) ET LES TROIS AVIS, CHEZ NOUS SEULEMENT.          27/11/2026

    python -X utf8 -u phase2\checks\etape_3bis_commentaires_et_avis_generer_patch_2026-11-27.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il lit le Sheet (l'image du passage officiel 84), le verdict du 84 (socle, lecture
   seule) et la base (lecture seule), et il GENERE les quatre fichiers habituels : le patch, son A_BLANC, son INVERSE, sa
   REPETITION (supabase/patch_3bis_commentaires_avis_2026-11-27*.sql).

SON MOT DU 27/11 AU SOIR : « Mets-les en etape 3 bis, juste apres les dates d'annulation, par le meme patron : script,
patch, inverse, repetition. Ma regle s'y applique telle quelle, et pour les notes jamais d'ecrasement -- une note neuve
datee. » Et : « Le 84 est pose, les notes tomberont sur les bonnes pieces. »

SA REGLE : case vide chez nous -> le Sheet ; case remplie qui differe -> le Sheet gagne (valeur d'avant gardee).

⭐ « UNE NOTE NEUVE DATEE » ET LA CLE DE LA TABLE : app_affaire_note a pour cle app_affaire_id SEUL (une note par
   transaction -- verifie le 27/11, et c'est ce que le lot 1 du 17/11 a rencontre). Une note neuve sur une piece qui en
   porte deja une est donc un PARAGRAPHE DATE AJOUTE (« [classeur G, relu le 26/11/2026] ... »), le texte d'avant reste
   intact au-dessus, et une SAUVEGARDE DATEE (app_affaire_note_avant_3bis_20261127) permet a l'inverse de le rendre a
   l'octet. Rien n'est jamais remplace.
⭐ LA PIECE : celle qui porte deja la note G de la ligne (un ecart : on complete la meme note) ; sinon, comme le 17/11,
   la plus avancee des pieces que le passage 84 donne a la ligne (vente, puis compromis, puis offre).
⛔ JAMAIS une note « saisie » (ecrite par un humain dans l'app) : la ligne est SIGNALEE, rien n'est pose.
⭐ LE TEXTE : « tels quels, sans aucune interpretation » (sa consigne du 31/10, repetee le 17/11) -- le texte du Sheet,
   sans le nettoyage du 17/11 (qui avait mange des « + » et des « € »).
⭐ LES AVIS : app_classeur_avis, une ligne par ID Unique. Une case vide prend le Sheet ; une case qui differe prend le
   Sheet, et la ligne d'avant va dans app_classeur_avis_avant_3bis_20261127.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

PASSAGE = 84
MARQUE = "classeur:3bis:2026-11-27"
SAUVE_NOTE = "app_affaire_note_avant_3bis_20261127"
SAUVE_AVIS = "app_classeur_avis_avant_3bis_20261127"
BASE = P.RACINE / "supabase" / "patch_3bis_commentaires_avis_2026-11-27"
RAPPORT = P.NOTICE / "ETAPE_3BIS_LOT_A_COMMENTAIRES_AVIS_2026-11-27.csv"
RANG = {"vente": 3, "compromis": 2, "offre": 1}
AVIS = {"Avis à envoyer (oui / non)": "avis_a_envoyer", "Commentaire Avis": "commentaire_avis", "Avis envoyé": "avis_envoye"}


def q(s) -> str:
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"


def main() -> int:
    so = sqlite3.connect("file:%s?mode=ro" % P.SOCLE.as_posix(), uri=True)
    image = so.execute("select image from passage where id=?", (PASSAGE,)).fetchone()[0]
    V = {i: (v, e, json.loads(ps) if ps else []) for i, v, e, ps in
         so.execute("select id_unique, verdict, etiquette, pieces from verdict where passage=?", (PASSAGE,))}
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
    cu.execute("select app_affaire_id, origine, texte from public.app_affaire_note")
    N = {int(a): (o, t or "") for a, o, t in cu.fetchall()}
    cu.execute("select id_unique, avis_a_envoyer, commentaire_avis, avis_envoye from public.app_classeur_avis")
    AV = {i: {"avis_a_envoyer": a or "", "commentaire_avis": c or "", "avis_envoye": e or ""} for i, a, c, e in cu.fetchall()}
    cn.close()

    inserts, ajouts, signaux, rapport = [], [], [], []
    avis_ins, avis_upd = [], []
    cpt = Counter()
    for i, (v, etq, ps) in sorted(V.items()):
        if v != "TRANCHEE" or i not in ROW:
            continue
        g = case(i, "COMMENTAIRES")
        if g:
            ps_ = [int(a) for a in ps if int(a) in L]
            notes_g = [a for a in ps_ if a in N and N[a][0] in ("classeur:G", "classeur:F+G")]
            deja = any(g in N[a][1] for a in ps_ if a in N)
            if deja:
                cpt["G deja chez nous (le texte du Sheet est dans une note de la ligne)"] += 1
            else:
                cible = notes_g[0] if notes_g else (max(ps_, key=lambda a: (RANG.get(L[a][0], 0), a)) if ps_ else None)
                if cible is None:
                    cpt["G : la ligne n'a aucune piece"] += 1
                    signaux.append((i, "aucune piece"))
                elif cible in N and N[cible][0] == "saisie":
                    cpt["⛔ G : la piece porte une note SAISIE par un humain -- signalee, rien pose"] += 1
                    signaux.append((i, "note saisie sur %d" % cible))
                elif cible in N:
                    cpt["G : paragraphe date ajoute a la note de la piece"] += 1
                    ajouts.append((cible, "[classeur G, relu le 26/11/2026] " + g))
                    rapport.append(("COMMENTAIRES", i, cible, "paragraphe ajoute", g[:120]))
                else:
                    cpt["G : note neuve sur la piece"] += 1
                    k, d, c = L[cible]
                    inserts.append((cible, d, c, "classeur:G", "G : COMMENTAIRES du classeur, relu le 26/11/2026 -- " + g))
                    rapport.append(("COMMENTAIRES", i, cible, "note neuve", g[:120]))
        for col, champ in AVIS.items():
            val = case(i, col)
            if not val:
                continue
            nous = AV.get(i, {}).get(champ, "")
            if nous == val:
                cpt["avis deja chez nous"] += 1
                continue
            if i not in AV:
                cpt["avis : ligne neuve dans app_classeur_avis"] += 1
                AV[i] = {"avis_a_envoyer": "", "commentaire_avis": "", "avis_envoye": ""}
                avis_ins.append(i)
            elif nous:
                cpt["avis : case remplie qui differe -> le Sheet gagne (valeur d'avant sauvee)"] += 1
            else:
                cpt["avis : case vide -> le Sheet"] += 1
            AV[i][champ] = val
            avis_upd.append((i, champ, val, nous, etq))
            rapport.append((col, i, "", "avis", "%s -> %s" % (nous or "(vide)", val)))
    # plusieurs paragraphes sur la meme piece : on les concatene dans l'ordre
    par_piece = {}
    for a, t in ajouts:
        par_piece.setdefault(a, []).append(t)
    cibles_ins = {x[0] for x in inserts}
    assert not (cibles_ins & set(par_piece)), "une piece recevrait une note neuve ET un paragraphe"
    assert len(cibles_ins) == len(inserts), "deux notes neuves sur la meme piece : %s" % [
        a for a, n in Counter(x[0] for x in inserts).items() if n > 1]
    for k, n in sorted(cpt.items()):
        print("   %5d  %s" % (n, k))
    print("   signaux : %s" % signaux[:10])

    avis_touches = sorted({x[0] for x in avis_upd})
    corps = []
    corps.append("-- 1. LA GARDE : rien de ce lot n'est deja pose, et les sauvegardes n'existent pas")
    corps.append("do $$ begin\n  if exists (select 1 from public.app_affaire_note where ecrit_par = %s)\n"
                 "     or to_regclass('public.%s') is not null or to_regclass('public.%s') is not null then\n"
                 "    raise exception '⛔ garde : le lot 3 bis A est deja (en partie) pose -- ce patch ne se rejoue pas'; end if;\n"
                 "end $$;" % (q(MARQUE), SAUVE_NOTE, SAUVE_AVIS))
    corps.append("-- 2. LES SAUVEGARDES DATEES (ce que l'inverse rendra a l'octet), RLS allumee, aucun droit ouvert")
    corps.append("create table public.%s as select * from public.app_affaire_note where app_affaire_id in (%s);"
                 % (SAUVE_NOTE, ", ".join(str(a) for a in sorted(par_piece)) or "NULL"))
    corps.append("create table public.%s as select * from public.app_classeur_avis where id_unique in (%s);"
                 % (SAUVE_AVIS, ", ".join(q(i) for i in avis_touches) or "NULL"))
    for t in (SAUVE_NOTE, SAUVE_AVIS):
        corps.append("alter table public.%s enable row level security; revoke all on public.%s from public, anon, authenticated;"
                     % (t, t))
    corps.append("-- 3. LES NOTES NEUVES (%d)" % len(inserts))
    if inserts:
        corps.append("insert into public.app_affaire_note (app_affaire_id, app_dossier_id, app_chaine_id, origine, texte, ecrit_par)\n"
                     "values\n" + ",\n".join("  (%d, %s, %s, %s, %s, %s)" % (a, d if d is not None else "NULL",
                                                                              c if c is not None else "NULL", q(o), q(t), q(MARQUE))
                                             for a, d, c, o, t in inserts) + ";")
    corps.append("-- 4. LES PARAGRAPHES DATES AJOUTES (%d pieces) -- le texte d'avant reste intact au-dessus" % len(par_piece))
    for a, ts in sorted(par_piece.items()):
        corps.append("update public.app_affaire_note set texte = texte || E'\\n\\n' || %s where app_affaire_id = %d;"
                     % (q("\n\n".join(ts)), a))
    corps.append("-- 5. LES AVIS (%d cases, %d lignes neuves)" % (len(avis_upd), len(avis_ins)))
    etq_de = {x[0]: x[4] for x in avis_upd}
    for i in avis_ins:
        corps.append("insert into public.app_classeur_avis (id_unique, origine, ecrit_par, app_dossier_uuid) values (%s, 'classeur', %s, %s);"
                     % (q(i), q(MARQUE), q(etq_de.get(i)) + "::uuid" if etq_de.get(i) else "NULL"))
    for i, champ, val, _avant, _e in avis_upd:
        corps.append("update public.app_classeur_avis set %s = %s, ecrit_par = %s, ecrit_le = now() where id_unique = %s;"
                     % (champ, q(val), q(MARQUE), q(i)))
    n_notes_apres = len(N) + len(inserts)
    corps.append("-- 6. LES CONTROLES")
    corps.append("do $$ declare n int; begin\n"
                 "  select count(*) into n from public.app_affaire_note where ecrit_par = %s;\n"
                 "  if n <> %d then raise exception '⛔ controle : %% notes neuves (attendu %d)', n; end if;\n"
                 "  select count(*) into n from public.app_affaire_note where texte like '%%[classeur G, relu le 26/11/2026]%%';\n"
                 "  if n <> %d then raise exception '⛔ controle : %% notes portent le paragraphe (attendu %d)', n; end if;\n"
                 "  select count(*) into n from public.app_affaire_note;\n"
                 "  if n <> %d then raise exception '⛔ controle : %% notes en tout (attendu %d)', n; end if;\n"
                 "  select count(*) into n from public.app_affaire_note a join public.%s s using (app_affaire_id)\n"
                 "   where left(a.texte, length(s.texte)) <> s.texte;\n"
                 "  if n <> 0 then raise exception '⛔ controle : %% note(s) dont le texte d''avant n''est plus intact', n; end if;\n"
                 "  select count(*) into n from public.app_classeur_avis where ecrit_par = %s;\n"
                 "  if n <> %d then raise exception '⛔ controle : %% lignes d''avis marquees (attendu %d)', n; end if;\n"
                 "  raise notice '✅ lot 3 bis A : %d notes neuves, %d paragraphes, %d lignes d''avis touchees';\n"
                 "end $$;" % (q(MARQUE), len(inserts), len(inserts), len(par_piece), len(par_piece), n_notes_apres, n_notes_apres,
                              SAUVE_NOTE, q(MARQUE), len(avis_touches), len(avis_touches), len(inserts), len(par_piece),
                              len(avis_touches)))
    tete = ("-- %s -- ETAPE 3 BIS, LOT A (COMMENTAIRES + AVIS), chez nous seulement, jamais chez Hektor\n"
            "-- Genere par phase2/checks/etape_3bis_commentaires_et_avis_generer_patch_2026-11-27.py (passage officiel %d, image %s)\n"
            "-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql\n")
    corps_txt = "\n".join(corps) + "\n"
    (BASE.parent / (BASE.name + ".sql")).write_text(tete % (BASE.name, PASSAGE, image) + "\nbegin;\n" + corps_txt + "commit;\n",
                                                    encoding="utf-8")
    (BASE.parent / (BASE.name + "_A_BLANC.sql")).write_text(
        tete % ("A BLANC de " + BASE.name, PASSAGE, image) + "-- ⛔ SANS commit : il finit par une erreur VOULUE, tout est annule.\n"
        "\nbegin;\n" + corps_txt + "do $$ begin raise exception 'A BLANC LOT 3 BIS A VERT -- RIEN N''EST ECRIT'; end $$;\n",
        encoding="utf-8")
    (BASE.parent / (BASE.name + "_INVERSE.sql")).write_text(
        "-- INVERSE de %s : retire les notes neuves du lot, rend les notes et les avis d'avant a l'octet (sauvegardes datees).\n"
        "-- Il ne juge que SA part (lecon 31).\n\nbegin;\n"
        "delete from public.app_affaire_note where ecrit_par = %s;\n"
        "update public.app_affaire_note a set texte = s.texte from public.%s s where s.app_affaire_id = a.app_affaire_id;\n"
        "delete from public.app_classeur_avis where ecrit_par = %s and id_unique not in (select id_unique from public.%s);\n"
        "update public.app_classeur_avis a set avis_a_envoyer = s.avis_a_envoyer, commentaire_avis = s.commentaire_avis,\n"
        "       avis_envoye = s.avis_envoye, ecrit_par = s.ecrit_par, ecrit_le = s.ecrit_le\n"
        "  from public.%s s where s.id_unique = a.id_unique;\n"
        "do $$ declare n int; begin\n"
        "  select count(*) into n from public.app_affaire_note where ecrit_par = %s or texte like '%%[classeur G, relu le 26/11/2026]%%';\n"
        "  if n <> 0 then raise exception '⛔ inverse : %% trace(s) du lot restent', n; end if;\n"
        "  select count(*) into n from public.app_classeur_avis where ecrit_par = %s;\n"
        "  if n <> 0 then raise exception '⛔ inverse : %% avis marques restent', n; end if;\n"
        "  raise notice '✅ inverse : le lot 3 bis A est retire, les sauvegardes restent (elles se gardent)';\nend $$;\ncommit;\n"
        % (BASE.name, q(MARQUE), SAUVE_NOTE, q(MARQUE), SAUVE_AVIS, SAUVE_AVIS, q(MARQUE), q(MARQUE)), encoding="utf-8")
    (BASE.parent / (BASE.name + "_REPETITION.sql")).write_text(
        "-- REPETITION de %s (lecture seule) -- attendu : %d notes neuves, %d paragraphes, %d lignes d'avis, %d notes en tout\n"
        "select (select count(*) from public.app_affaire_note where ecrit_par = %s) notes_neuves,\n"
        "       (select count(*) from public.app_affaire_note where texte like '%%[classeur G, relu le 26/11/2026]%%') paragraphes,\n"
        "       (select count(*) from public.app_classeur_avis where ecrit_par = %s) avis,\n"
        "       (select count(*) from public.app_affaire_note) notes_en_tout,\n"
        "       (select count(*) from public.app_affaire_note a join public.%s s using (app_affaire_id)\n"
        "         where left(a.texte, length(s.texte)) <> s.texte) textes_d_avant_abimes;\n"
        % (BASE.name, len(inserts), len(par_piece), len(avis_touches), n_notes_apres, q(MARQUE), q(MARQUE), SAUVE_NOTE),
        encoding="utf-8")
    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["colonne", "id_unique", "piece", "geste", "texte_ou_valeur"])
        w.writerows(rapport)
        w.writerows([("SIGNAL", i, "", why, "") for i, why in signaux])
    for f in sorted(BASE.parent.glob(BASE.name + "*.sql")):
        print("   %s  md5 %s  %d octets" % (f.name, hashlib.md5(f.read_bytes()).hexdigest()[:8], f.stat().st_size))
    print("   rapport : %s" % RAPPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
