"""LE REMEDE DE 8016 (SXJDHXKF) -- LE PATCH, SON ESSAI A BLANC, SON INVERSE, SA REPETITION (son mot du 25/11).

SON MOT : « ⭐ (a) FABRIQUE LE REMEDE DE 8016 MAINTENANT, avec son essai a blanc, et montre-le-moi avant de poser. [...] une fois
les parts du classeur reposees, elles seront PROTEGEES : le remede est definitif, pas un pansement. »

LE CONSTAT (vague_mesure_apres_2026-11-25.py) : la chaine 8016 (compromis 8016 + VENTE REGLEE 8019, 27/03/2019) porte la ligne
SXJDHXKF (ROMERA 100 au Sheet). Apres A2 elle portait ROMERA 50/50 en SUPPOSITION (hektor_partage_suppose) : juste mais NON
protegee ; l'etape 8 l'a recalculee -> SORTIE ROMERA 50 seule. Les parts du CLASSEUR de 8019 (ROMERA entree 50 + sortie 50,
classeur_reconstitue) sont dans la mise de cote (A2, « les memes parts y vivent deja » -- ma regle SANS L'ORIGINE).

LE GESTE (une seule chaine, ⛔ chaque garde porte l'ORIGINE -- la lecon) :
  G0 ne se rejoue pas ; G1 8016 porte EXACTEMENT les membres 8016 et 8019 ; G2 8016 porte EXACTEMENT la part de la nuit (sortie,
  rang 1, 195, Solange ROMERA, 50, hektor_partage_suppose, conversion) ; G3 la mise de cote d'A2 porte EXACTEMENT les deux parts
  du classeur de 8019 (entree et sortie, 195, SOLANGE ROMERA, 50, classeur_reconstitue).
  -> la sauvegarde datee de 8016 ; le journal (lot remede_8016_2026-11-25, ligne d'origine SXJDHXKF) ; la part de la nuit MISE DE
  COTE (regle 6), puis retiree ; les deux parts du classeur RECOPIEES depuis la mise de cote (elles y restent : la trace d'A2).
  CONTROLES : 8016 = ROMERA entree 50 + sortie 50, classeur_reconstitue, somme 100, PROTEGEE (le verrou de la nuit : une part
  hors hektor%) ; la part de la nuit est dans la mise de cote, ENTIERE ; 0 orpheline ; 0 vente reglee sans part ; les parts hors
  de 8016 INTACTES ; l'empreinte d'apres (exigee au patch reel : elle sort de l'essai a blanc).
USAGE : python -X utf8 phase2/checks/remede_8016_generer_patch_2026-11-25.py [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--empreinte-apres", default="")
arg = ap.parse_args()
LOT, TAB, MDC = "remede_8016_2026-11-25", "app_affaire_repartition_avant_remede8016_20261125", "patch_remede_8016_2026-11-25"
OUT = Path(__file__).resolve().parents[2] / "supabase"
EXPR = ("md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, "
        "origine, ecrit_par), ';' order by app_chaine_id, cote, rang), ''))")
VR = ("(select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
      "coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from "
      "public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id))")
ORPH = ("(select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l "
        "where l.app_chaine_id = r.app_chaine_id))")

# LECTURE SEULE : l'etat exact que les gardes exigeront
cn, cu = P.pooler()
cu.execute("select string_agg(app_affaire_id::text, ',' order by app_affaire_id) from public.app_affaire_ledger where app_chaine_id = 8016")
membres = cu.fetchone()[0]
cu.execute("select cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par from public.app_affaire_repartition "
           "where app_chaine_id = 8016 order by cote, rang")
nuit = cu.fetchall()
cu.execute("select id, cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine from public.app_affaire_repartition_mise_de_cote "
           "where ancien_app_chaine_id = 8019 and mise_de_cote_par = 'patch_a2_vague_2026-11-25' order by cote, rang")
classeur = cu.fetchall()
cu.execute("select count(*), %s from public.app_affaire_repartition" % EXPR)
n_rep, e_rep = cu.fetchone()
cn.rollback()
cn.close()
print("8016 : membres %s ; parts %s" % (membres, nuit))
print("mise de cote d'A2 (classeur de 8019) : %s" % classeur)
assert membres == "8016,8019", membres
assert nuit == [("sortie", 1, "195", "Solange ROMERA", "50.000", "hektor_partage_suppose", "conversion")], nuit
assert [(c[1], c[2], c[3], c[4], c[5], c[6]) for c in classeur] == [
    ("entree", 1, "195", "SOLANGE ROMERA", "50.000", "classeur_reconstitue"),
    ("sortie", 1, "195", "SOLANGE ROMERA", "50.000", "classeur_reconstitue")], classeur
ids_cl = ", ".join(str(c[0]) for c in classeur)
D = {"lot": LOT, "tab": TAB, "mdc": MDC, "ids": ids_cl, "expr": EXPR, "vr": VR, "orph": ORPH, "n_rep": n_rep, "e_rep": e_rep}

CORPS = """
-- ─── LES GARDES (chacune porte l'ORIGINE) ─────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.%(tab)s') is not null then raise exception '⛔ G0 : la sauvegarde existe deja'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ G0 : %% ligne(s) du lot deja au journal', n; end if;
  select string_agg(app_affaire_id::text, ',' order by app_affaire_id) into e from public.app_affaire_ledger where app_chaine_id = 8016;
  if e is distinct from '8016,8019' then raise exception '⛔ G1 : 8016 porte les membres %% au lieu de 8016,8019', e; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 8016;
  if n <> 1 then raise exception '⛔ G2 : 8016 porte %% part(s) au lieu de la seule part de la nuit', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 8016 and cote = 'sortie' and rang = 1
     and hektor_user_id = '195' and nom_au_moment = 'Solange ROMERA' and pourcentage = 50
     and origine = 'hektor_partage_suppose' and ecrit_par = 'conversion';
  if n <> 1 then raise exception '⛔ G2 : la part de 8016 n''est pas celle de la nuit (sortie ROMERA 50, hektor_partage_suppose)'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote where id in (%(ids)s) and ancien_app_chaine_id = 8019
     and mise_de_cote_par = 'patch_a2_vague_2026-11-25' and hektor_user_id = '195' and nom_au_moment = 'SOLANGE ROMERA'
     and pourcentage = 50 and origine = 'classeur_reconstitue' and cote in ('entree', 'sortie') and rang = 1;
  if n <> 2 then raise exception '⛔ G3 : la mise de cote ne porte pas les deux parts du classeur de 8019 (%% sur 2)', n; end if;
  raise notice '✅ gardes : 8016 = 8016+8019, sa seule part = la nuit (hektor_partage_suppose), le classeur de 8019 en mise de cote';
end $$;
-- ─── LA SAUVEGARDE DATEE, LE JOURNAL, LE GESTE ────────────────────────────────────────────────────────────────────
create table public.%(tab)s as select * from public.app_affaire_repartition where app_chaine_id = 8016;
revoke all on public.%(tab)s from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_app_chaine_id, vers_app_affaire_id, vers_app_chaine_id, valeur,
   ancienne_valeur, ligne_origine, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', n, 'repartition', colonne, geste, de_a, de_c, 8016, 8016, valeur, ancienne, 'SXJDHXKF',
       'la vague du 25/11, etape 8 (mesure d''apres)', pourquoi, 'patch_remede_8016'
  from (values
    (1, 'app_affaire_repartition (sortie, rang 1)', 'METTRE DE COTE (regle 6 : la part de la nuit, une SUPPOSITION)', 8016, 8016,
     null::text, '195 Solange ROMERA 50 (hektor_partage_suppose, conversion 25/11 09:07)',
     'SON MOT du 25/11 : l''etape 8 a recalcule 8016 (la vague y a mis la vente 8019) -> sortie ROMERA 50 seule ; SXJDHXKF (ROMERA 100) etait fausse a moitie'),
    (2, 'app_affaire_repartition (entree, rang 1)', 'RECOPIER (le classeur de 8019, depuis la mise de cote d''A2)', 8019, 8019,
     '195 SOLANGE ROMERA 50 (classeur_reconstitue)', null,
     'SON MOT du 25/11 : le remede definitif -- les parts du classeur, PROTEGEES par leur origine (ma regle A2 « memes parts » comparait sans l''origine)'),
    (3, 'app_affaire_repartition (sortie, rang 1)', 'RECOPIER (le classeur de 8019, depuis la mise de cote d''A2)', 8019, 8019,
     '195 SOLANGE ROMERA 50 (classeur_reconstitue)', null,
     'SON MOT du 25/11 : le remede definitif -- les parts du classeur, PROTEGEES par leur origine (ma regle A2 « memes parts » comparait sans l''origine)')
  ) v(n, colonne, geste, de_a, de_c, valeur, ancienne, pourquoi);
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select app_chaine_id, 8016, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
       ecrit_le, ecrit_par, '%(mdc)s',
       'le remede de 8016 (son mot du 25/11) : la part de la nuit, une supposition, remplacee par le classeur de 8019 (SXJDHXKF)'
  from public.app_affaire_repartition where app_chaine_id = 8016;
delete from public.app_affaire_repartition where app_chaine_id = 8016;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select 8016, (select app_dossier_id from public.app_affaire_ledger where app_affaire_id = 8016), m.cote, m.rang, m.hektor_user_id,
       m.nom_au_moment, m.pourcentage, m.origine, now(), '%(lot)s:SXJDHXKF'
  from public.app_affaire_repartition_mise_de_cote m where m.id in (%(ids)s);
-- ─── LES CONTROLES ────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 8016 and rang = 1 and hektor_user_id = '195'
     and pourcentage = 50 and origine = 'classeur_reconstitue' and cote in ('entree', 'sortie');
  if n <> 2 or (select count(*) from public.app_affaire_repartition where app_chaine_id = 8016) <> 2 then
    raise exception '⛔ controle : 8016 ne porte pas exactement ROMERA entree 50 + sortie 50 du classeur'; end if;
  if (select sum(pourcentage) from public.app_affaire_repartition where app_chaine_id = 8016) <> 100 then
    raise exception '⛔ controle : la somme de 8016 n''est pas 100'; end if;
  -- LE VERROU DE LA NUIT : une part hors hektor%% -> l'absorbeur n'y touchera plus
  if not exists (select 1 from public.app_affaire_repartition where app_chaine_id = 8016 and coalesce(origine, '') not like 'hektor%%') then
    raise exception '⛔ controle : 8016 n''est pas protegee'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m join public.%(tab)s s
    on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
   and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
   and s.ecrit_par is not distinct from m.ecrit_par and s.nom_au_moment is not distinct from m.nom_au_moment
   where m.mise_de_cote_par = '%(mdc)s';
  if n <> 1 then raise exception '⛔ controle : la part de la nuit n''est pas mise de cote entiere (%% sur 1)', n; end if;
  if %(orph)s <> 0 then raise exception '⛔ controle : des parts orphelines'; end if;
  if %(vr)s <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  if (select count(*) from public.app_affaire_repartition) <> %(n_rep)s + 1 then
    raise exception '⛔ controle : %% parts au lieu de %(n_rep)s + 1', (select count(*) from public.app_affaire_repartition); end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s' and ligne_origine = 'SXJDHXKF';
  if n <> 3 then raise exception '⛔ controle : %% ligne(s) au journal sur 3', n; end if;
  e := (select %(expr)s from public.app_affaire_repartition);
  %(apres)s
  raise notice '✅ 8016 : ROMERA entree 50 + sortie 50 du classeur, protegee ; la part de la nuit mise de cote ; 0 orpheline ; 0 vente reglee sans part ; empreinte apres %%', e;
end $$;
"""
INVERSE = """
-- ─── L'INVERSE : les parts du classeur retirees de 8016, la part de la nuit remise, le journal du lot retire ─────────
delete from public.app_affaire_repartition where app_chaine_id = 8016 and ecrit_par = '%(lot)s:SXJDHXKF';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s';
delete from public.app_classeur_realignement_journal where lot = '%(lot)s';
do $$
begin
  if (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition where app_chaine_id = 8016
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.%(tab)s) z) <> 0 or (select count(*) from public.app_affaire_repartition where app_chaine_id = 8016) <> 1 then
    raise exception '⛔ inverse : 8016 n''est pas revenue a la sauvegarde'; end if;
  raise notice '✅ inverse : 8016 est revenue a la part de la nuit, la mise de cote et le journal du lot sont vides';
end $$;
"""
ent = "-- %s -- genere par phase2/checks/remede_8016_generer_patch_2026-11-25.py (son mot du 25/11)\n"
reel_apres = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc (--empreinte-apres)';")
fichiers = {
    "patch_remede_8016_2026-11-25.sql": ent % "patch_remede_8016_2026-11-25" + "\nbegin;\n" + (CORPS % dict(D, apres=reel_apres))
    + "\ncommit;\n",
    "patch_remede_8016_2026-11-25_A_BLANC.sql": ent % "A BLANC -- ⛔ aucun commit, une erreur VOULUE annule tout" + "\nbegin;\n"
    + "create temporary table r_avant on commit drop as select count(*) n, %s e from public.app_affaire_repartition;\n" % EXPR
    + (CORPS % dict(D, apres="null;")) + "\ncreate temporary table r_milieu on commit drop as select count(*) n, %s e, "
    "(select string_agg(cote || ' ' || nom_au_moment || ' ' || pourcentage || ' ' || origine, ' + ' order by cote) from "
    "public.app_affaire_repartition where app_chaine_id = 8016) p from public.app_affaire_repartition;\n" % EXPR
    + (INVERSE % D) + """
do $$
declare a record; m record; n int; e text;
begin
  select * into a from r_avant; select * into m from r_milieu;
  select count(*), %s into n, e from public.app_affaire_repartition;
  if n <> a.n or e <> a.e then raise exception '⛔ A BLANC : l''inverse n''a pas tout rendu'; end if;
  raise exception 'A BLANC REMEDE 8016 VERT -- RIEN N''EST ECRIT. Avant : %% parts (%%). Apres le remede : %% parts, 8016 = %%, empreinte apres %%. Apres l''inverse : = avant.', a.n, left(a.e, 8), m.n, m.p, m.e;
end $$;
""" % EXPR,
    "patch_remede_8016_2026-11-25_INVERSE.sql": ent % "INVERSE" + "\nbegin;\n" + (INVERSE % D) + "\ncommit;\n",
    "patch_remede_8016_2026-11-25_REPETITION.sql": ent % "REPETITION (lecture seule)" + """select
  (select string_agg(cote || ' ' || nom_au_moment || ' ' || pourcentage || ' ' || origine, ' + ' order by cote)
     from public.app_affaire_repartition where app_chaine_id = 8016) as parts_8016_attendu_romera_50_50_classeur,
  (select count(*) from public.app_classeur_realignement_journal where lot = '%(lot)s') as journal_attendu_3,
  (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = '%(mdc)s') as mise_de_cote_attendu_1,
  %(orph)s as orphelines_attendu_0, %(vr)s as ventes_reglees_sans_part_attendu_0,
  (select %(expr)s from public.app_affaire_repartition) as empreinte_apres;
""" % D,
}
for nom, txt in fichiers.items():
    p_ = OUT / nom
    p_.write_text(txt, encoding="utf-8")
    print("-> supabase/%s (%d octets, md5 %s)" % (nom, p_.stat().st_size, hashlib.md5(p_.read_bytes()).hexdigest()[:8]))
print("avant : %d parts, %s" % (n_rep, e_rep))
