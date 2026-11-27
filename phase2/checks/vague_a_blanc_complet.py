"""L'ESSAI A BLANC COMPLET DE LA VAGUE -- ce que la base vivra entre l'etape 5 et la fin de l'etape 7, dans UNE transaction
qui S'ANNULE (son mot du 25/11 : « A1 et A3 avec la vague, a l'etape 7 [...] chiffre-le-moi : combien la vague rend faux,
et combien A1 et A3 en reparent »).

LE FICHIER COMPOSE (supabase/vague_du_soir_<jour>_A_BLANC_COMPLET.sql), dans l'ordre :
  0. l'etat d'AVANT (parts, mise de cote, journal, avis, notes, conditions, etiquettes, compteur) et les reflets faux AVANT ;
  1. LES CHAINES DE LA VAGUE posees comme le rejeu les prevoit (le numero de chaine n'a aucun declencheur) ;
  2. LA VRAIE POSE DES ETIQUETTES : app_poser_etiquettes_dossier(), celle que la poussee appelle (son compteur est une TABLE :
     annulee avec le reste, aucun numero n'est consomme) -- ses quatre gestes sont rendus ;
  3. les reflets faux APRES LA VAGUE, SANS REMEDE ; les orphelines ; les ventes reglees sans part ;
  4. A2, puis A1, puis A3 -- leurs gardes, leur geste, leurs controles, tels qu'au patch ;
  5. l'etat du MILIEU (tout a 0) ;
  6. les inverses (A3 et A1, puis A2) ; l'etat d'AVANT doit revenir A L'IDENTIQUE ;
  7. ⛔ une erreur VOULUE : TOUT est annule. Le message de l'erreur porte les chiffres.
⛔ Ce fichier ne porte AUCUN commit (la commande le verifie avant de l'envoyer).

USAGE : python -X utf8 phase2/checks/vague_a_blanc_complet.py --date J
        puis : python -X utf8 phase2/checks/vague_du_soir.py --a-blanc-sql supabase/vague_du_soir_J_A_BLANC_COMPLET.sql
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--date", required=True)
arg = ap.parse_args()
VDS = Path(r"C:\Hektor\chantier_classeur_q6_cache\vague_du_soir")
A2 = json.loads((VDS / ("corps_a2_%s.json" % arg.date)).read_text(encoding="utf-8"))
A13 = json.loads((VDS / ("corps_a1_a3_%s.json" % arg.date)).read_text(encoding="utf-8"))
OUT = Path(r"C:\Hektor\Projet\supabase") / ("vague_du_soir_%s_A_BLANC_COMPLET.sql" % arg.date)

E_REP = A2["expr_parts"]
VR = A2["sql_vr"]
E_AV = "md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by id_unique), ''))"
E_NO = "md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), ''))"
E_CO = "md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by app_affaire_id, rang), ''))"
NO_FAUX = ("(select count(*) from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id "
           "where n.app_chaine_id is distinct from l.app_chaine_id)")
CO_FAUX = ("(select count(*) from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id "
           "where c.app_chaine_id is distinct from l.app_chaine_id)")
ORPH = ("(select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l "
        "where l.app_chaine_id = r.app_chaine_id))")


def etat(nom: str) -> str:
    return """create temporary table %s on commit drop as select
  (select count(*) from public.app_affaire_repartition) n_rep, (select %s from public.app_affaire_repartition) e_rep,
  (select count(*) from public.app_affaire_repartition_mise_de_cote) n_mdc,
  (select count(*) from public.app_classeur_realignement_journal) n_j,
  (select %s from public.app_classeur_avis) e_av, (select %s from public.app_affaire_note) e_no,
  (select %s from public.app_affaire_condition) e_co,
  %s no_faux, %s co_faux, %s orph, (%s) vr,
  (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero), ';'
           order by app_affaire_id), '')) from public.app_affaire_ledger) e_lab,
  (select md5(coalesce(string_agg(concat_ws('|', annee, dernier), ';' order by annee), '')) from public.app_dossier_numero_compteur) e_cpt;
""" % (nom, E_REP, E_AV, E_NO, E_CO, NO_FAUX, CO_FAUX, ORPH, VR)


sql = """-- vague_du_soir_%(d)s_A_BLANC_COMPLET -- genere par phase2/checks/vague_a_blanc_complet.py
-- ⛔ N'ECRIT RIEN : la derniere instruction ANNULE toute la transaction (erreur voulue). AUCUN commit dans ce fichier.
-- Les chaines de la vague (%(n_sim)s pieces), la VRAIE pose des etiquettes, A2, A1, A3, leurs controles, leurs inverses.
begin;
%(avant)s
-- ─── 1. LES CHAINES DE LA VAGUE ───────────────────────────────────────────────────────────────────────────────────
%(sim)s
-- ─── 2. LA VRAIE POSE DES ETIQUETTES (celle que la poussee appelle) ───────────────────────────────────────────────
create temporary table vab_pose on commit drop as select * from public.app_poser_etiquettes_dossier();
%(vague)s
-- ─── 4. A2, A1, A3 ────────────────────────────────────────────────────────────────────────────────────────────────
%(a2)s
%(a1)s
%(a3)s
%(milieu)s
create temporary table vab_lots on commit drop as
  select lot, count(*) n from public.app_classeur_realignement_journal
   where lot in ('%(lot2)s', 'a1_vague_%(d)s', 'a3_vague_%(d)s') group by lot;
-- ─── 6. LES INVERSES ──────────────────────────────────────────────────────────────────────────────────────────────
%(inv13)s
%(inv2)s
-- ─── 7. TOUT EST-IL REVENU ? puis l'erreur VOULUE, qui annule tout ────────────────────────────────────────────────
%(apres)s
do $$
declare a record; v record; m record; f record; p text; l text;
begin
  select * into a from vab_avant;
  select * into v from vab_vague;
  select * into m from vab_milieu;
  select * into f from vab_fin;
  select string_agg(geste || ' ' || dossiers || ' dossiers / ' || lignes || ' lignes', ' ; ') into p from vab_pose;
  select string_agg(lot || ' ' || n, ' ; ' order by lot) into l from vab_lots;
  if f.n_rep <> a.n_rep or f.e_rep <> a.e_rep or f.n_mdc <> a.n_mdc or f.n_j <> a.n_j or f.e_av <> a.e_av
     or f.e_no <> a.e_no or f.e_co <> a.e_co then
    raise exception '⛔ A BLANC COMPLET : les inverses n''ont pas tout rendu (parts %%/%%, mise de cote %%/%%, journal %%/%%, avis %%, notes %%, conditions %%)',
      f.n_rep, a.n_rep, f.n_mdc, a.n_mdc, f.n_j, a.n_j, f.e_av = a.e_av, f.e_no = a.e_no, f.e_co = a.e_co;
  end if;
  raise exception 'A BLANC COMPLET VERT -- RIEN N''EST ECRIT (annulation voulue). AVANT : %% parts (%%), mise de cote %%, journal %%, notes fausses %%, conditions fausses %%, orphelines %%. LA POSE DES ETIQUETTES : %%. APRES LA VAGUE SANS REMEDE : notes fausses %%, conditions fausses %%, orphelines %%, ventes reglees sans part [%%]. APRES A2+A1+A3 : %% parts, empreinte des parts %%, notes fausses %%, conditions fausses %%, orphelines %%, ventes reglees sans part [%%], mise de cote %%, journal %% (%%). APRES LES INVERSES : = AVANT (parts, mise de cote, journal, avis, notes, conditions).',
    a.n_rep, left(a.e_rep, 8), a.n_mdc, a.n_j, a.no_faux, a.co_faux, a.orph, p, v.no_faux, v.co_faux, v.orph, v.vr,
    m.n_rep, m.e_rep, m.no_faux, m.co_faux, m.orph, m.vr, m.n_mdc, m.n_j, l;
end $$;
""" % {"d": arg.date, "n_sim": A2["n_sim"], "avant": etat("vab_avant"), "sim": A2["sim"], "vague": etat("vab_vague"),
       "a2": A2["corps"], "a1": A13["a1"], "a3": A13["a3"], "milieu": etat("vab_milieu"), "lot2": A2["lot"],
       "inv13": A13["inverse"], "inv2": A2["inverse"], "apres": etat("vab_fin")}
# les %% du gabarit (raise) sont deja rendus en % par l'operateur % ci-dessus
import re
assert not re.search(r"^\s*commit\s*;", sql, re.I | re.M), "un commit dans l'essai a blanc"
OUT.write_text(sql, encoding="utf-8")
print("-> %s (%d octets, md5 %s) ; chiffrage prevu : %s" % (OUT, OUT.stat().st_size, hashlib.md5(OUT.read_bytes()).hexdigest()[:8],
                                                            A13["chiffrage_prevu"]))
