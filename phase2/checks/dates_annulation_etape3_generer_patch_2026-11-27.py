#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ETAPE 3 DU PLAN -- LES DATES D'ANNULATION ELARGIES : LE PATCH, SON A BLANC, SON INVERSE, SA REPETITION (27/11 au soir).

Patron : dates_annulation_famille3_generer_patch_2026-11-27.py (memes gardes, meme sauvegarde datee, meme journal de
realignement, meme empreinte d'apres exigee). N'ECRIT RIEN EN BASE.

SA REGLE DU 27/11 : « s'il n'y a aucun compromis et seulement une offre refusee, la date va sur l'offre -- 249 lignes. Plus
les 6 ou mon Sheet dit annule et ou nos pieces sont vivantes : la date, jamais l'etat. Et les 109 anterieures restent
dehors, comme decide. »
LES LIGNES : l'audit des 18 refait sur le passage officiel 84 (categories « seulement une offre (refused) » 249,
« (accepted) » 3, « son compromis n'est pas annule chez nous (active) » 3). La piece visee est celle de la ligne au 84.
LES GARDES AJOUTEES :
  - la date d'annulation n'est jamais AVANT la 1re proposition de l'offre, ni avant le compromis (sa regle du 16/11) ;
  - le Sheet du jour (un GET) porte la MEME date a la MEME ligne que l'image du 84 -- sinon la ligne est signalee ;
  - R27 remesuree : une ligne qui a une jumelle (meme Mandat, Acquereur, Commission TTC) est signalee, pas posee ;
  - une ligne qui porte DEUX pieces du genre vise est signalee (on ne choisit pas).
⛔ L'ETAT DES PIECES N'EST JAMAIS TOUCHE (son interdit) : seule la case date_annulation_app, si elle est VIDE.
USAGE : python -X utf8 phase2/checks/dates_annulation_etape3_generer_patch_2026-11-27.py [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import coupe_preuve_interne as K  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--empreinte-apres", default="")
ap.add_argument("--audit", default=r"C:\Users\admin\AppData\Local\Temp\claude\b84fec2a77c3fd2b\c287df45-a790-42bb-91b2-1c06a57f9c3a\scratchpad\AUDIT_18_PASSAGE_84.csv")
arg = ap.parse_args()
LOT, TAB = "dates_annulation_etape3_2026-11-27", "app_affaire_ledger_avant_dates_e3_20261127"
OUT = RACINE / "supabase"
RAPPORT = RACINE / "notice" / "ETAPE_3_DATES_ANNULATION_ELARGIES_2026-11-27.csv"
PASSAGE = 84
CATS = {"4 sans compromis chez nous : seulement une offre (refused)": ("offre", "refused", "sa regle du 27/11 : aucun compromis, seulement une offre refusee -> la date sur l'offre"),
        "4 sans compromis chez nous : seulement une offre (accepted)": ("offre", "accepted", "ses 6 : le Sheet dit annule, la piece est vivante -> la date, JAMAIS l'etat"),
        "3 manque : son compromis n'est pas annule chez nous (active)": ("compromis", "active", "ses 6 : le Sheet dit annule, la piece est vivante -> la date, JAMAIS l'etat")}

# ─── 1. LES LIGNES, et le verdict du 84 ──────────────────────────────────────────────────────────────────────
with open(arg.audit, encoding="utf-8-sig") as h:
    rows = [r for r in csv.DictReader(h, delimiter=";") if r["colonne"] == "Annulée" and r["etat"] in CATS]
con = sqlite3.connect("file:%s?mode=ro" % P.SOCLE.as_posix(), uri=True)
image = con.execute("select image from passage where id=?", (PASSAGE,)).fetchone()[0]
V = {i: (v, json.loads(ps) if ps else []) for i, v, ps in con.execute("select id_unique, verdict, pieces from verdict where passage=?", (PASSAGE,))}
con.close()
I = P.Image(P.IMAGES / image)
D = I.D
cn, cu = P.pooler()
cu.execute("select app_affaire_id, kind, state, coalesce(date_annulation_app, ''), date::text, propositions_json from public.app_affaire_ledger")
REG = {int(a): (k, s, da, d, pj) for a, k, s, da, d, pj in cu.fetchall()}
cn.rollback()
cn.close()


def premiere_proposition(pj, d):
    j = pj if isinstance(pj, list) else (json.loads(pj) if pj else [])
    for e in j or []:
        if isinstance(e, dict) and e.get("type") == "proposition" and e.get("date"):
            return K.d_reg(str(e["date"]))
    return K.d_reg(str(d or ""))


LIGNES, SIGNAUX = [], []
for r in rows:
    i = r["id_unique"]
    kind, state, pourquoi = CATS[r["etat"]]
    v, ps = V.get(i, ("?", []))
    if v != "TRANCHEE":
        SIGNAUX.append((i, "pas tranchee au 84"))
        continue
    cand = [int(a) for a in ps if int(a) in REG and REG[int(a)][0] == kind and REG[int(a)][1] == state]
    if len(cand) != 1:
        SIGNAUX.append((i, "%d piece(s) %s %s sur la ligne : on ne choisit pas" % (len(cand), kind, state)))
        continue
    b = D.case(i, "Annulée").strip()
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", b):
        SIGNAUX.append((i, "date illisible au Sheet : %r" % b))
        continue
    val = "%s-%s-%s" % (b[6:10], b[3:5], b[0:2])
    a = cand[0]
    k_, s_, da, dpiece, pj = REG[a]
    if da:
        SIGNAUX.append((i, "la piece %d porte deja une date (%s)" % (a, da)))
        continue
    borne = premiere_proposition(pj, dpiece) if kind == "offre" else K.d_reg(str(dpiece or ""))
    if borne and K.d_reg(val) < borne:
        SIGNAUX.append((i, "annulation %s AVANT %s de la piece %d (%s) : ecartee, comme les 109" % (
            val, "la 1re proposition" if kind == "offre" else "le compromis", a, borne)))
        continue
    LIGNES.append((i, int(D.num(i)) if hasattr(D, "num") else int(r["ligne_du_sheet"]), a, val, b, kind, state, pourquoi))

# ─── 2. R27 remesuree, et le Sheet du jour ──────────────────────────────────────────────────────────────────
sheet = json.loads((P.IMAGES / image / "sheet.json").read_text(encoding="utf-8"))
cle = {j: (D.case(j, "Mandat").strip(), frozenset(P.noms_texte(D.case(j, "Acquéreur"))), P.nombre_case(D.case(j, "Commission TTC")))
       for j in sheet["par_id"]}
par_cle = defaultdict(list)
for j, k in cle.items():
    if k[0] and k[1] and k[2] is not None:
        par_cle[k].append(j)
import apparier_classeur as ac  # noqa: E402

ac.load_env_file(RACINE / ".env")
entete, lignes_jour = ac.lire_classeur()
kA = entete.index("Annulée")
du_jour = defaultdict(list)
for num, l in lignes_jour:
    l = [("" if x is None else str(x)) for x in list(l)] + [""] * 40
    du_jour[l[37].strip()].append((num, l[kA].strip()))
garde = []
for x in LIGNES:
    i, num, a, val, b = x[:5]
    if [j for j in par_cle.get(cle[i], []) if j != i]:
        SIGNAUX.append((i, "R27 : une jumelle (meme Mandat, Acquereur, Commission) -- pas posee"))
        continue
    if len(du_jour[i]) != 1 or du_jour[i][0][1] != b:
        SIGNAUX.append((i, "le Sheet du jour differe de l'image du 84 : %s" % du_jour.get(i)))
        continue
    garde.append(x)
LIGNES = sorted(garde, key=lambda x: x[1])
N = len(LIGNES)
print("LIGNES POSABLES : %d (offres refusees %d, offres acceptees %d, compromis actifs %d) ; signalees : %d" % (
    N, sum(1 for x in LIGNES if x[6] == "refused"), sum(1 for x in LIGNES if x[6] == "accepted"),
    sum(1 for x in LIGNES if x[6] == "active"), len(SIGNAUX)))
for s in SIGNAUX:
    print("   SIGNAL", s)
assert N > 0

# ─── 3. SUPABASE, LECTURE SEULE : l'etat exact que les gardes exigeront ──────────────────────────────────────
ids = ", ".join(str(x[2]) for x in LIGNES)
EMP = ("md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, "
       "coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(vente_reglee_app, '-'), "
       "coalesce(numero_facture_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) "
       "from public.app_affaire_ledger where app_affaire_id in (%s)" % ids)
N_DA = "(select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '')"
cn, cu = P.pooler()
cu.execute("select %s, (select %s)" % (N_DA, EMP))
n_da, e_avant = cu.fetchone()
cu.execute("select count(*) from public.app_classeur_realignement_journal where lot = %s", (LOT,))
au_journal = cu.fetchone()[0]
cu.execute("select to_regclass(%s) is not null", ("public." + TAB,))
tab_existe = cu.fetchone()[0]
cn.rollback()
cn.close()
assert au_journal == 0 and not tab_existe, (au_journal, tab_existe)


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


VALEURS = ",\n    ".join("(%d, %s, %d, %d, %s, %s)" % (n, q(i), num, a, q(val), q("%s ; Sheet « %s »" % (pq, b)))
                         for n, (i, num, a, val, b, _k, _s, pq) in enumerate(LIGNES, 1))
ATTENDUS = " or ".join("(app_affaire_id = %d and kind = '%s' and state = '%s')" % (a, k, s) for _i, _n, a, _v, _b, k, s, _p in LIGNES)
D_ = {"lot": LOT, "tab": TAB, "ids": ids, "emp": EMP, "e_avant": e_avant, "valeurs": VALEURS, "n_da": n_da, "image": image, "n": N,
      "attendus": ATTENDUS}
CORPS = """
-- ─── ① LES GARDES : %(n)d pieces SANS date, de l'etat attendu, telles que lues ──────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.%(tab)s') is not null then raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ garde : %%%% ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (%(ids)s) and coalesce(date_annulation_app, '') = ''
     and (%(attendus)s);
  if n <> %(n)d then raise exception '⛔ garde : %%%% piece(s) sans date de l''etat attendu sur %(n)d', n; end if;
  e := (select %(emp)s);
  if e <> '%(e_avant)s' then raise exception '⛔ garde : les %(n)d lignes ont change depuis la fabrication (%%%%)', e; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '') <> %(n_da)s then
    raise exception '⛔ garde : le nombre de dates d''annulation a change depuis la fabrication'; end if;
  raise notice '✅ gardes : %(n)d pieces sans date, de l''etat attendu, telles que lues';
end $$;

-- ─── ② LA SAUVEGARDE DATEE, AVEC la cle primaire et la RLS ─────────────────────────────────────────────────
create table public.%(tab)s as select * from public.app_affaire_ledger where app_affaire_id in (%(ids)s);
alter table public.%(tab)s add primary key (app_affaire_id);
revoke all on public.%(tab)s from public, anon, authenticated;
alter table public.%(tab)s enable row level security;

-- ─── ③ LE JOURNAL : chaque date, sa ligne d'origine et son numero ─────────────────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, 'date_annulation_app', 'date_annulation_app', 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, 'VIDE',
       v.ligne, v.num, 'Sheet, image %(image)s (passage 84, colonne Annulee) = le Sheet du 27/11', v.pourquoi,
       'patch_dates_annulation_etape3'
  from (values
    %(valeurs)s
  ) v(n, ligne, num, piece, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : seulement des cases VIDES ; l'ETAT n'est jamais touche ────────────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and l.app_affaire_id = j.de_app_affaire_id and coalesce(l.date_annulation_app, '') = '';

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l
    on l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur where j.lot = '%(lot)s';
  if n <> %(n)d then raise exception '⛔ controle : %%%% date(s) posee(s) sur %(n)d', n; end if;
  select count(*) into n from public.app_affaire_ledger l join public.%(tab)s s using (app_affaire_id)
   where (l.kind, l.state, l.app_chaine_id, l.app_dossier_numero, l.motif_annulation_app, l.vente_reglee_app,
          l.numero_facture_app, l.honoraires_entree_app, l.date)
         is distinct from (s.kind, s.state, s.app_chaine_id, s.app_dossier_numero, s.motif_annulation_app, s.vente_reglee_app,
                           s.numero_facture_app, s.honoraires_entree_app, s.date);
  if n <> 0 then raise exception '⛔ controle : %%%% ligne(s) ont bouge hors de leur date (l''etat compris)', n; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(date_annulation_app, '') <> '') <> %(n_da)s + %(n)d then
    raise exception '⛔ controle : le nombre de dates d''annulation n''est pas %(n_da)s + %(n)d'; end if;
  e := (select %(emp)s);
  %(apres)s
  raise notice '✅ %(n)d dates posees ; l''etat et le reste des lignes intacts ; empreinte apres %%%%', e;
end $$;
"""
INVERSE = """
-- ─── L'INVERSE : les dates retirees (seulement si elles portent encore la valeur du lot), le journal retire ─────────
update public.app_affaire_ledger l set date_annulation_app = s.date_annulation_app
  from public.%(tab)s s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = '%(lot)s' and j.de_app_affaire_id = l.app_affaire_id
   and l.date_annulation_app = j.valeur;
delete from public.app_classeur_realignement_journal where lot = '%(lot)s';
do $$
begin
  if (select count(*) from public.app_affaire_ledger l join public.%(tab)s s using (app_affaire_id)
       where l.date_annulation_app is distinct from s.date_annulation_app) <> 0 then
    raise exception '⛔ inverse : les dates ne sont pas revenues a la sauvegarde'; end if;
  raise notice '✅ inverse : les dates retirees, le journal du lot vide';
end $$;
"""
reel = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %%%% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc (--empreinte-apres)';")
ent = "-- %s -- genere par phase2/checks/dates_annulation_etape3_generer_patch_2026-11-27.py (son mot du 27/11 au soir)\n"
BLANC_FIN = ("\ndo $$ declare e text; begin\n  e := (select %s);\n"
             "  raise exception 'A BLANC DATES ETAPE 3 VERT -- RIEN N''EST ECRIT. %d dates posees, empreinte apres %%', e;\nend $$;\n"
             % (EMP, N))
F = {
    "patch_dates_annulation_etape3_2026-11-27.sql": ent % "patch_dates_annulation_etape3_2026-11-27"
    + "-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql\n\nbegin;\n" + (CORPS % dict(D_, apres=reel)).replace("%%", "%")
    + "\ncommit;\n",
    "patch_dates_annulation_etape3_2026-11-27_A_BLANC.sql": ent % "A BLANC -- ⛔ aucun commit, une erreur VOULUE annule tout"
    + "\nbegin;\n" + (CORPS % dict(D_, apres="null;")).replace("%%", "%") + BLANC_FIN,
    "patch_dates_annulation_etape3_2026-11-27_INVERSE.sql": ent % "INVERSE" + "\nbegin;\n" + INVERSE % D_ + "\ncommit;\n",
    "patch_dates_annulation_etape3_2026-11-27_REPETITION.sql": ent % "REPETITION (lecture seule)" + (
        "select (select count(*) from public.app_classeur_realignement_journal where lot = '%s') as journal_attendu_%d,\n"
        "  %s as dates_posees_attendu_%d,\n  (select %s) as empreinte_apres;\n" % (LOT, N, N_DA, n_da + N, EMP)),
}
for nom, txt in F.items():
    p_ = OUT / nom
    p_.write_bytes(txt.encode("utf-8"))
    print("-> supabase/%s (%d octets, md5 %s)" % (nom, p_.stat().st_size, hashlib.md5(p_.read_bytes()).hexdigest()[:8]))
with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["id_unique", "ligne_du_sheet", "piece", "genre", "etat", "date_annulation", "case_du_sheet", "pourquoi"])
    w.writerows((i, num, a, k, s, val, b, pq) for i, num, a, val, b, k, s, pq in LIGNES)
    w.writerows((i, "", "", "SIGNAL", "", "", "", why) for i, why in SIGNAUX)
print("empreinte d'avant des %d lignes : %s ; dates posees %d ; rapport %s" % (N, e_avant, n_da, RAPPORT))
