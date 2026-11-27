-- A BLANC -- ⛔ aucun commit, une erreur VOULUE annule tout -- genere par phase2/checks/parts_3647_generer_patch_2026-11-27.py (son ordre du 27/11)

begin;
create temporary table r_avant on commit drop as select count(*) n, md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) e, (select string_agg(cote || ' ' || hektor_user_id || ' ' || nom_au_moment || ' ' || pourcentage || ' ' || origine, ' + ' order by cote, rang) from public.app_affaire_repartition where app_chaine_id = 3647) p from public.app_affaire_repartition;

-- ─── ① LES GARDES : la chaine, ses deux suppositions, sa voisine et le registre EXACTEMENT tels que mesures ──────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_repartition_avant_parts3647_20261127') is not null then raise exception '⛔ G0 : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'parts_3647_2026-11-27';
  if n <> 0 then raise exception '⛔ G0 : % ligne(s) du lot deja au journal', n; end if;
  select string_agg(app_affaire_id::text, ',' order by app_affaire_id) into e from public.app_affaire_ledger where app_chaine_id = 3647;
  if e is distinct from '3647,3648,3650' then raise exception '⛔ G1 : 3647 porte les membres % au lieu de 3647,3648,3650', e; end if;
  select count(*) into n from public.app_affaire_ledger where app_chaine_id = 3647 and app_dossier_uuid::text = '42dd4d66-eb07-47b6-85d6-8db1e7000090'
     and app_dossier_numero = 'D2024-0511' and app_dossier_id = 1390780;
  if n <> 3 then raise exception '⛔ G1 : % piece(s) sur 3 portent D2024-0511 (42dd4d66-eb07-47b6-85d6-8db1e7000090)', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 3647;
  if n <> 2 then raise exception '⛔ G2 : 3647 porte % part(s) au lieu des deux suppositions', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 3647 and rang = 1 and cote in ('entree', 'sortie')
     and hektor_user_id = '32' and nom_au_moment = 'Christèle GENTES' and pourcentage = 50 and origine = 'hektor_partage_suppose'
     and ecrit_par = 'conversion' and app_dossier_id = 1390780;
  if n <> 2 then raise exception '⛔ G2 : les parts de 3647 ne sont pas les deux suppositions mesurees (GENTES 50/50, hektor_partage_suppose)'; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id = 3646);
  if e <> 'b8b0db64973095395b287a37383825a8' then raise exception '⛔ G3 : 3646 (427UDDSF) a bouge : empreinte % au lieu de b8b0db64973095395b287a37383825a8', e; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition);
  if e <> '96d757a1bbde90880c711452b2bdbf2d' then raise exception '⛔ G4 : le registre des parts a bouge depuis la mesure : empreinte % au lieu de 96d757a1bbde90880c711452b2bdbf2d', e; end if;
  raise notice '✅ gardes : 3647 = 3647,3648,3650 sur D2024-0511, ses deux suppositions telles que mesurees ; 3646 et le registre inchanges';
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les parts ENTIERES de 3647, AVEC la cle primaire et la RLS ──────────────────────────────
create table public.app_affaire_repartition_avant_parts3647_20261127 (like public.app_affaire_repartition including defaults including constraints including indexes);
insert into public.app_affaire_repartition_avant_parts3647_20261127 select * from public.app_affaire_repartition where app_chaine_id = 3647;
revoke all on public.app_affaire_repartition_avant_parts3647_20261127 from public, anon, authenticated;
alter table public.app_affaire_repartition_avant_parts3647_20261127 enable row level security;

-- ─── ③ LE JOURNAL : chaque part remplacee, avec SA LIGNE D'ORIGINE (9Q0FHAKK, n° 286) et SA PLACE ─────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'parts_3647_2026-11-27', v.n, 'repartition', 'app_affaire_repartition (' || v.cote || ', rang ' || v.rang || ')',
       'REMPLACER (le classeur fait foi ; l''ancienne mise de cote)', 3647, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, 3647, d.kind, d.app_chaine_id, d.app_dossier_numero,
       v.uid || ' ' || v.nom || ' ' || v.pct, v.ancienne, '9Q0FHAKK', 286,
       'Sheet (Negociateurs / Pourcentages, regles du 13/11), ligne 286 lue en direct le 27/11', v.pourquoi, 'patch_parts_3647_2026-11-27'
  from (values
    (1, 'entree', 1, '31', 'SIMON DECHAUD', '50', '32 Christèle GENTES 50 (hektor_partage_suppose)', 'SON ORDRE du 27/11 (« 3. puis le partage DECHAUD 50 / GENTES 50 sur la chaine 3647 ») ; sa decision du 24/11 : le classeur fait foi, une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (2, 'sortie', 1, '32', 'CHRISTELE GENTES', '50', '32 Christèle GENTES 50 (hektor_partage_suppose)', 'SON ORDRE du 27/11 (« 3. puis le partage DECHAUD 50 / GENTES 50 sur la chaine 3647 ») ; sa decision du 24/11 : le classeur fait foi, une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place')
  ) v(n, cote, rang, uid, nom, pct, ancienne, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = 3647;

-- ─── ④ LE GESTE : chaque supposition MISE DE COTE (entiere, avec son numero de chaine), puis la part du classeur posee ───
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, r.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'patch_parts_3647_2026-11-27',
       j.pourquoi || ' -- remplacee par ' || j.valeur || ' (ligne ' || j.ligne_origine || ', n° ' || j.ligne_origine_num || ')'
  from public.app_affaire_repartition r
  join public.app_classeur_realignement_journal j
    on j.lot = 'parts_3647_2026-11-27' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = 'parts_3647_2026-11-27' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, v.uid, v.nom, v.pct::numeric, 'classeur_reconstitue', now(), 'classeur:9Q0FHAKK'
  from (values
    ('entree', 1, '31', 'SIMON DECHAUD', '50'),
    ('sortie', 1, '32', 'CHRISTELE GENTES', '50')
  ) v(cote, rang, uid, nom, pct)
  join public.app_affaire_repartition_mise_de_cote m
    on m.mise_de_cote_par = 'patch_parts_3647_2026-11-27' and m.app_chaine_id = 3647 and m.cote = v.cote and m.rang = v.rang;

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_repartition r join (values
    ('entree', 1, '31', 'SIMON DECHAUD', '50'),
    ('sortie', 1, '32', 'CHRISTELE GENTES', '50')
  ) v(cote, rang, uid, nom, pct) on r.cote = v.cote and r.rang = v.rang
   where r.app_chaine_id = 3647 and r.hektor_user_id = v.uid and r.nom_au_moment = v.nom and r.pourcentage = v.pct::numeric
     and r.origine = 'classeur_reconstitue' and r.ecrit_par = 'classeur:9Q0FHAKK' and r.app_dossier_id = 1390780;
  if n <> 2 or (select count(*) from public.app_affaire_repartition where app_chaine_id = 3647) <> 2 then
    raise exception '⛔ controle : 3647 ne porte pas exactement DECHAUD entree 50 + GENTES sortie 50 du classeur'; end if;
  if (select sum(pourcentage) from public.app_affaire_repartition where app_chaine_id = 3647) <> 100 then
    raise exception '⛔ controle : la somme de 3647 n''est pas 100'; end if;
  -- SON TEMOIN : plus aucune part hektor sur 3647 (le verrou de la nuit : l'absorbeur saute une chaine sans part hektor%)
  select count(*) into n from public.app_affaire_repartition where app_chaine_id = 3647 and coalesce(origine, '') like 'hektor%';
  if n <> 0 then raise exception '⛔ controle : % part(s) hektor encore sur 3647', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id = 3646);
  if e <> 'b8b0db64973095395b287a37383825a8' then raise exception '⛔ controle : 3646 a bouge (%)', e; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id <> 3647);
  if e <> '182afd218a16f66d99635d727de28794' then raise exception '⛔ controle : une part HORS de 3647 a bouge (%)', e; end if;
  if (select count(*) from public.app_affaire_repartition) <> 17970 then
    raise exception '⛔ controle : % parts au lieu de 17970', (select count(*) from public.app_affaire_repartition); end if;
  -- la regle 6 : chaque supposition est dans la mise de cote, ENTIERE (sa sauvegarde le prouve)
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m join public.app_affaire_repartition_avant_parts3647_20261127 s
    on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
   and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
   and s.ecrit_par is not distinct from m.ecrit_par and s.nom_au_moment is not distinct from m.nom_au_moment
   and s.app_dossier_id is not distinct from m.app_dossier_id
   where m.mise_de_cote_par = 'patch_parts_3647_2026-11-27';
  if n <> 2 or (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_parts_3647_2026-11-27') <> 2 then
    raise exception '⛔ controle : % supposition(s) mise(s) de cote entiere(s) sur 2', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'parts_3647_2026-11-27' and ligne_origine = '9Q0FHAKK'
     and ligne_origine_num = 286 and ancienne_valeur is not null;
  if n <> 2 then raise exception '⛔ controle : % ligne(s) au journal sur 2', n; end if;
  if (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) <> 0 then raise exception '⛔ controle : des parts orphelines'; end if;
  if (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition);
  null;
  raise notice '✅ 3647 : DECHAUD entree 50 + GENTES sortie 50 du classeur, plus aucune part hektor ; les deux suppositions mises de cote ; 3646 et le reste intacts ; empreinte apres %', e;
end $$;

-- ─── L'EPREUVE DE LA NUIT : LES VRAIES FONCTIONS, avec les lignes memes que la nuit a ecrites sur 3647 ──────────────────
create temporary table r_milieu on commit drop as select count(*) n, md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) e, (select string_agg(cote || ' ' || hektor_user_id || ' ' || nom_au_moment || ' ' || pourcentage || ' ' || origine, ' + ' order by cote, rang) from public.app_affaire_repartition where app_chaine_id = 3647) p, (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id = 3647) e_ch from public.app_affaire_repartition;
create temporary table r_absorbeur on commit drop as select public.app_repartition_absorber((select jsonb_agg(jsonb_build_object('app_chaine_id', app_chaine_id, 'app_dossier_id', app_dossier_id, 'cote', cote, 'rang', rang, 'hektor_user_id', hektor_user_id, 'nom_au_moment', nom_au_moment, 'pourcentage', pourcentage, 'origine', origine)) from public.app_affaire_repartition_avant_parts3647_20261127)) rep;
create temporary table r_purge on commit drop as select public.app_repartition_purger_orphelines() rep;
do $$
declare m record; a jsonb; p jsonb;
begin
  select * into m from r_milieu; select rep into a from r_absorbeur; select rep into p from r_purge;
  if (a->>'proteges_app')::int <> 1 or (a->>'dossiers_ecrits')::int <> 0 then
    raise exception '⛔ A BLANC : l''absorbeur n''a pas saute 3647 : %', a; end if;
  if (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id = 3647) <> m.e_ch then raise exception '⛔ A BLANC : la nuit a touche 3647'; end if;
  if (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) <> m.e then
    raise exception '⛔ A BLANC : la nuit rejouee a touche le registre des parts (purge %)', p; end if;
end $$;

-- ─── L'INVERSE : les parts du classeur retirees de 3647, les deux suppositions remises, le journal du lot retire ───────
delete from public.app_affaire_repartition where app_chaine_id = 3647 and ecrit_par = 'classeur:9Q0FHAKK' and origine = 'classeur_reconstitue';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select ancien_app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_parts_3647_2026-11-27';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_parts_3647_2026-11-27';
delete from public.app_classeur_realignement_journal where lot = 'parts_3647_2026-11-27';
do $$
begin
  if (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition where app_chaine_id = 3647
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition_avant_parts3647_20261127) z) <> 0
     or (select count(*) from (select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
        ecrit_le, ecrit_par from public.app_affaire_repartition_avant_parts3647_20261127
      except all select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le,
        ecrit_par from public.app_affaire_repartition where app_chaine_id = 3647) z) <> 0 then
    raise exception '⛔ inverse : 3647 n''est pas revenue a la sauvegarde'; end if;
  raise notice '✅ inverse : 3647 est revenue aux deux suppositions, la mise de cote et le journal du lot sont vides';
end $$;

-- ─── LE TEMOIN INVERSE : sur 3647 remise en supposition, l'absorbeur doit ECRIRE (sinon l'epreuve ne prouvait rien) ───
create temporary table r_inverse_nuit on commit drop as select public.app_repartition_absorber((select jsonb_agg(jsonb_build_object('app_chaine_id', app_chaine_id, 'app_dossier_id', app_dossier_id, 'cote', cote, 'rang', rang, 'hektor_user_id', hektor_user_id, 'nom_au_moment', nom_au_moment, 'pourcentage', pourcentage, 'origine', origine)) from public.app_affaire_repartition_avant_parts3647_20261127)) rep;
do $$
declare a record; m record; t jsonb; n int; e text; ab jsonb; pu jsonb;
begin
  select * into a from r_avant; select * into m from r_milieu; select rep into t from r_inverse_nuit;
  select rep into ab from r_absorbeur; select rep into pu from r_purge;
  if (t->>'dossiers_ecrits')::int <> 1 or (t->>'proteges_app')::int <> 0 then
    raise exception '⛔ A BLANC : le temoin inverse ne mord pas -- l''absorbeur n''ecrit pas sur 3647 en supposition : %', t; end if;
  select count(*), md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) into n, e from public.app_affaire_repartition;
  if n <> a.n or e <> a.e then raise exception '⛔ A BLANC : apres le temoin inverse, le registre n''est plus celui d''avant'; end if;
  raise exception 'A BLANC PARTS 3647 VERT -- RIEN N''EST ECRIT. Avant : % parts (%), 3647 = %. Apres le patch : % parts, 3647 = %, empreinte apres %. La nuit rejouee : absorbeur %, purge %. Apres l''inverse : = avant. Temoin inverse : %.',
    a.n, left(a.e, 8), a.p, m.n, m.p, m.e, ab, pu, t;
end $$;
