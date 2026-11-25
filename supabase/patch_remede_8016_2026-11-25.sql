-- patch_remede_8016_2026-11-25 -- genere par phase2/checks/remede_8016_generer_patch_2026-11-25.py (son mot du 25/11)

begin;

-- ─── LES GARDES (chacune porte l'ORIGINE) ─────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_repartition_avant_remede8016_20261125') is not null then raise exception '⛔ G0 : la sauvegarde existe deja'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'remede_8016_2026-11-25';
  if n <> 0 then raise exception '⛔ G0 : % ligne(s) du lot deja au journal', n; end if;
  select string_agg(app_affaire_id::text, ',' order by app_affaire_id) into e from public.app_affaire_ledger where app_chaine_id = 8016;
  if e is distinct from '8016,8019' then raise exception '⛔ G1 : 8016 porte les membres % au lieu de 8016,8019', e; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 8016;
  if n <> 1 then raise exception '⛔ G2 : 8016 porte % part(s) au lieu de la seule part de la nuit', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 8016 and cote = 'sortie' and rang = 1
     and hektor_user_id = '195' and nom_au_moment = 'Solange ROMERA' and pourcentage = 50
     and origine = 'hektor_partage_suppose' and ecrit_par = 'conversion';
  if n <> 1 then raise exception '⛔ G2 : la part de 8016 n''est pas celle de la nuit (sortie ROMERA 50, hektor_partage_suppose)'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote where id in (645, 644) and ancien_app_chaine_id = 8019
     and mise_de_cote_par = 'patch_a2_vague_2026-11-25' and hektor_user_id = '195' and nom_au_moment = 'SOLANGE ROMERA'
     and pourcentage = 50 and origine = 'classeur_reconstitue' and cote in ('entree', 'sortie') and rang = 1;
  if n <> 2 then raise exception '⛔ G3 : la mise de cote ne porte pas les deux parts du classeur de 8019 (% sur 2)', n; end if;
  raise notice '✅ gardes : 8016 = 8016+8019, sa seule part = la nuit (hektor_partage_suppose), le classeur de 8019 en mise de cote';
end $$;
-- ─── LA SAUVEGARDE DATEE, LE JOURNAL, LE GESTE ────────────────────────────────────────────────────────────────────
create table public.app_affaire_repartition_avant_remede8016_20261125 as select * from public.app_affaire_repartition where app_chaine_id = 8016;
revoke all on public.app_affaire_repartition_avant_remede8016_20261125 from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_app_chaine_id, vers_app_affaire_id, vers_app_chaine_id, valeur,
   ancienne_valeur, ligne_origine, lot_origine, pourquoi, ecrit_par)
select 'remede_8016_2026-11-25', n, 'repartition', colonne, geste, de_a, de_c, 8016, 8016, valeur, ancienne, 'SXJDHXKF',
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
       ecrit_le, ecrit_par, 'patch_remede_8016_2026-11-25',
       'le remede de 8016 (son mot du 25/11) : la part de la nuit, une supposition, remplacee par le classeur de 8019 (SXJDHXKF)'
  from public.app_affaire_repartition where app_chaine_id = 8016;
delete from public.app_affaire_repartition where app_chaine_id = 8016;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select 8016, (select app_dossier_id from public.app_affaire_ledger where app_affaire_id = 8016), m.cote, m.rang, m.hektor_user_id,
       m.nom_au_moment, m.pourcentage, m.origine, now(), 'remede_8016_2026-11-25:SXJDHXKF'
  from public.app_affaire_repartition_mise_de_cote m where m.id in (645, 644);
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
  -- LE VERROU DE LA NUIT : une part hors hektor% -> l'absorbeur n'y touchera plus
  if not exists (select 1 from public.app_affaire_repartition where app_chaine_id = 8016 and coalesce(origine, '') not like 'hektor%') then
    raise exception '⛔ controle : 8016 n''est pas protegee'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m join public.app_affaire_repartition_avant_remede8016_20261125 s
    on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
   and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
   and s.ecrit_par is not distinct from m.ecrit_par and s.nom_au_moment is not distinct from m.nom_au_moment
   where m.mise_de_cote_par = 'patch_remede_8016_2026-11-25';
  if n <> 1 then raise exception '⛔ controle : la part de la nuit n''est pas mise de cote entiere (% sur 1)', n; end if;
  if (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) <> 0 then raise exception '⛔ controle : des parts orphelines'; end if;
  if (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  if (select count(*) from public.app_affaire_repartition) <> 17967 + 1 then
    raise exception '⛔ controle : % parts au lieu de 17967 + 1', (select count(*) from public.app_affaire_repartition); end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'remede_8016_2026-11-25' and ligne_origine = 'SXJDHXKF';
  if n <> 3 then raise exception '⛔ controle : % ligne(s) au journal sur 3', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition);
  if e <> '1dccc51297c54a99e38294756d790fc3' then raise exception '⛔ controle : empreinte apres % au lieu de 1dccc51297c54a99e38294756d790fc3', e; end if;
  raise notice '✅ 8016 : ROMERA entree 50 + sortie 50 du classeur, protegee ; la part de la nuit mise de cote ; 0 orpheline ; 0 vente reglee sans part ; empreinte apres %', e;
end $$;

commit;
