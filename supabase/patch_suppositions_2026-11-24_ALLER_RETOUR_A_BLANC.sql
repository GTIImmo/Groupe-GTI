-- patch_suppositions_2026-11-24 -- genere par phase2/checks/repartition_4_5_generer_patchs_2026-11-24.py (« rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_suppositions_2026-11-24_INVERSE.sql . Controle : patch_suppositions_2026-11-24_REPETITION.sql
-- ⛔ A BLANC : le patch PUIS son inverse dans la MEME transaction ; aucun commit ; erreur voulue a la fin.

begin;

-- ─── ① LES GARDES : chaque part a remplacer est EXACTEMENT celle mesuree, et chaque chaine porte 12 parts en tout ──
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_repartition_avant_suppositions_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'suppositions_2026-11-24';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_repartition r join (values
    (1875, 'entree', 1, '32', '50', 'hektor_partage_suppose'),
    (1875, 'sortie', 1, '32', '50', 'hektor_partage_suppose'),
    (9370, 'entree', 1, '0', '50', 'hektor_partage_suppose'),
    (9370, 'sortie', 1, '0', '50', 'hektor_partage_suppose'),
    (6391, 'entree', 1, '0', '50', 'hektor_partage_suppose'),
    (6391, 'sortie', 1, '0', '50', 'hektor_partage_suppose'),
    (4234, 'entree', 1, '45', '50', 'hektor_partage_suppose'),
    (4234, 'sortie', 1, '45', '50', 'hektor_partage_suppose'),
    (1027, 'entree', 1, '168', '50', 'hektor_partage_suppose'),
    (1027, 'sortie', 1, '168', '50', 'hektor_partage_suppose'),
    (27984, 'entree', 1, '237', '50', 'hektor_partage_suppose'),
    (27984, 'sortie', 1, '237', '50', 'hektor_partage_suppose')) v(ch, cote, rang, uid, pct, origine)
      on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.pourcentage = v.pct::numeric and r.origine = v.origine;
  if n <> 12 then raise exception '⛔ garde : % part(s) telles que mesurees sur 12', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984);
  if n <> 12 then raise exception '⛔ garde : les 6 chaines portent % part(s) au lieu de 12', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984));
  if e <> '1c741e0f96bb4a55c672d4e0cd37407d' then raise exception '⛔ garde : empreinte % au lieu de 1c741e0f96bb4a55c672d4e0cd37407d', e; end if;
  raise notice '✅ gardes : 12 parts telles que mesurees sur 6 chaines ; empreinte %', e;
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les parts ENTIERES des 6 chaines ──────────────────────────────────────────────────────
create table public.app_affaire_repartition_avant_suppositions_20261124 as
  select * from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984);
revoke all on public.app_affaire_repartition_avant_suppositions_20261124 from public, anon, authenticated;

-- ─── ③ LA TABLE DE LA REGLE 6 (dessinee le 22/11, telle quelle) : une part n'est jamais supprimee, elle est mise de cote ──
create table if not exists public.app_affaire_repartition_mise_de_cote (
  id                     bigint generated always as identity primary key,
  ancien_app_chaine_id   bigint      not null,
  dossier_ou_elle_vit    bigint,
  app_chaine_id          bigint      not null,
  app_dossier_id         bigint,
  cote                   text        not null,
  rang                   smallint    not null,
  hektor_user_id         text        not null,
  nom_au_moment          text,
  pourcentage            numeric     not null,
  origine                text,
  ecrit_le               timestamptz not null,
  ecrit_par              text,
  mise_de_cote_le        timestamptz not null default now(),
  mise_de_cote_par       text        not null,
  pourquoi               text        not null
);
revoke all on public.app_affaire_repartition_mise_de_cote from public, anon, authenticated;
alter table public.app_affaire_repartition_mise_de_cote enable row level security;

-- ─── ④ LE JOURNAL : chaque part remplacee, avec SA LIGNE D'ORIGINE et SA PLACE (la chaine, le cote, le rang) ──────────────
alter table public.app_classeur_realignement_journal add column if not exists ancienne_valeur text;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'suppositions_2026-11-24', v.n, 'repartition', 'app_affaire_repartition (' || v.cote || ', rang ' || v.rang || ')',
       'REMPLACER (le classeur fait foi ; l''ancienne mise de cote)', v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       v.uid || ' ' || v.nom || ' ' || v.pct, v.ancienne, v.ligne, v.num,
       'Sheet (Negociateurs / Pourcentages, regles du 13/11)', v.pourquoi, 'patch_suppositions_2026-11-24'
  from (values
    (1, 'A07EC3DH', 535, 1875, 1, 'entree', '31', 'SIMON DECHAUD', '50', '32 Christèle GENTES 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (2, 'A07EC3DH', 535, 1875, 1, 'sortie', '32', 'CHRISTELE GENTES', '50', '32 Christèle GENTES 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (3, 'DHXRAK9O', 566, 9370, 1, 'entree', '146', 'SABRINA NICOLOSI', '50', '0 Cet utilisateur a été supprimé 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (4, 'DHXRAK9O', 566, 9370, 1, 'sortie', '146', 'SABRINA NICOLOSI', '50', '0 Cet utilisateur a été supprimé 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (5, '72GQRHVB', 579, 6391, 1, 'entree', '149', 'LAURE CAVARD', '50', '0 Cet utilisateur a été supprimé 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (6, '72GQRHVB', 579, 6391, 1, 'sortie', '149', 'LAURE CAVARD', '50', '0 Cet utilisateur a été supprimé 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (7, '7IHI7YTJ', 692, 4234, 1, 'entree', '238', 'Joel CHAMPAGNAC', '50', '45 Delphine BLANCHARD 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (8, '7IHI7YTJ', 692, 4234, 1, 'sortie', '238', 'Joel CHAMPAGNAC', '50', '45 Delphine BLANCHARD 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (9, 'QXDW8EQA', 2559, 1027, 1, 'entree', '190', 'MAGALI DIMARIA MARIA', '50', '168 M. Benjamin TRIOLLIER 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (10, 'QXDW8EQA', 2559, 1027, 1, 'sortie', '168', 'BENJAMIN TRIOLLIER', '50', '168 M. Benjamin TRIOLLIER 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (11, 'CS38OO8R', 3263, 27984, 1, 'entree', '238', 'Joel CHAMPAGNAC', '50', '237 Michel BALMAYER 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place'),
    (12, 'CS38OO8R', 3263, 27984, 1, 'sortie', '238', 'Joel CHAMPAGNAC', '50', '237 Michel BALMAYER 50 (hektor_partage_suppose)', '④ SA DECISION du 24/11 (3e mot ④, 5e mot ④ « Applique ») : le classeur fait foi ; une supposition de Hektor n''est pas une donnee -- l''ancienne mise de cote avec sa place')
  ) v(n, ligne, num, ch, rang, cote, uid, nom, pct, ancienne, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.ch;

-- ─── ⑤ LE GESTE : l'ancienne part MISE DE COTE (entiere, avec son numero de chaine), puis la nouvelle posee ──────────────
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, r.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'patch_suppositions_2026-11-24', j.pourquoi || ' -- remplacee par ' || j.valeur || ' (ligne ' || j.ligne_origine || ')'
  from public.app_affaire_repartition r
  join public.app_classeur_realignement_journal j
    on j.lot = 'suppositions_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = 'suppositions_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, v.uid, v.nom, v.pct::numeric, 'classeur_reconstitue', now(),
       'classeur:' || v.ligne
  from (values
    (1875, 'entree', 1, '31', 'SIMON DECHAUD', '50', 'A07EC3DH'),
    (1875, 'sortie', 1, '32', 'CHRISTELE GENTES', '50', 'A07EC3DH'),
    (9370, 'entree', 1, '146', 'SABRINA NICOLOSI', '50', 'DHXRAK9O'),
    (9370, 'sortie', 1, '146', 'SABRINA NICOLOSI', '50', 'DHXRAK9O'),
    (6391, 'entree', 1, '149', 'LAURE CAVARD', '50', '72GQRHVB'),
    (6391, 'sortie', 1, '149', 'LAURE CAVARD', '50', '72GQRHVB'),
    (4234, 'entree', 1, '238', 'Joel CHAMPAGNAC', '50', '7IHI7YTJ'),
    (4234, 'sortie', 1, '238', 'Joel CHAMPAGNAC', '50', '7IHI7YTJ'),
    (1027, 'entree', 1, '190', 'MAGALI DIMARIA MARIA', '50', 'QXDW8EQA'),
    (1027, 'sortie', 1, '168', 'BENJAMIN TRIOLLIER', '50', 'QXDW8EQA'),
    (27984, 'entree', 1, '238', 'Joel CHAMPAGNAC', '50', 'CS38OO8R'),
    (27984, 'sortie', 1, '238', 'Joel CHAMPAGNAC', '50', 'CS38OO8R')
  ) v(ch, cote, rang, uid, nom, pct, ligne)
  join public.app_affaire_repartition_mise_de_cote m
    on m.mise_de_cote_par = 'patch_suppositions_2026-11-24' and m.app_chaine_id = v.ch and m.cote = v.cote and m.rang = v.rang;

-- ─── ⑥ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  -- chaque chaine porte EXACTEMENT la repartition voulue
  select count(*) into n from public.app_affaire_repartition r join (values
    (1027, 'entree', 1, '190', '50'),
    (1027, 'sortie', 1, '168', '50'),
    (1875, 'entree', 1, '31', '50'),
    (1875, 'sortie', 1, '32', '50'),
    (4234, 'entree', 1, '238', '50'),
    (4234, 'sortie', 1, '238', '50'),
    (6391, 'entree', 1, '149', '50'),
    (6391, 'sortie', 1, '149', '50'),
    (9370, 'entree', 1, '146', '50'),
    (9370, 'sortie', 1, '146', '50'),
    (27984, 'entree', 1, '238', '50'),
    (27984, 'sortie', 1, '238', '50')) v(ch, cote, rang, uid, pct)
      on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.pourcentage = v.pct::numeric and r.origine = 'classeur_reconstitue';
  if n <> 12 then raise exception '⛔ controle : % part(s) voulue(s) sur 12', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984);
  if n <> 12 then raise exception '⛔ controle : % part(s) sur les chaines au lieu de 12', n; end if;
  select count(*) into n from (select app_chaine_id from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984)
                                group by 1 having sum(pourcentage) <> 100) x;
  if n <> 0 then raise exception '⛔ controle : % chaine(s) dont la somme n''est pas 100', n; end if;
  -- la regle 6 : chaque ancienne part est dans la mise de cote, ENTIERE (sa sauvegarde le prouve)
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m
    join public.app_affaire_repartition_avant_suppositions_20261124 s
      on s.app_chaine_id = m.app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
     and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
     and s.ecrit_par is not distinct from m.ecrit_par and m.ancien_app_chaine_id = s.app_chaine_id
   where m.mise_de_cote_par = 'patch_suppositions_2026-11-24';
  if n <> 12 then raise exception '⛔ controle : % ancienne(s) part(s) mise(s) de cote, entiere(s), sur 12', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal
   where lot = 'suppositions_2026-11-24' and ligne_origine is not null and ancienne_valeur is not null;
  if n <> 12 then raise exception '⛔ controle : % ligne(s) au journal, avec ligne d''origine et ancienne valeur, sur 12', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984));
  if e <> '91a61e04b6d5507cd49c95b4af7d5f89' then raise exception '⛔ controle : empreinte apres % au lieu de 91a61e04b6d5507cd49c95b4af7d5f89', e; end if;
  raise notice '✅ 12 parts remplacees, 12 mises de cote entieres, sommes a 100, journal ; empreinte apres %', e;
end $$;

do $$ declare e text; begin e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984)); perform set_config('ar.apres', e, true); end $$;

-- ─── LE RETOUR : retirer ce que le lot a pose, reposer chaque ancienne part depuis la mise de cote, a l'identique ─────────
do $$
declare n int;
begin
  select count(*) into n from public.app_affaire_repartition r join public.app_classeur_realignement_journal j
      on j.lot = 'suppositions_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')'
   where r.origine = 'classeur_reconstitue' and r.ecrit_par = 'classeur:' || j.ligne_origine;
  if n <> 12 then raise exception '⛔ garde du retour : % part(s) du lot retrouvee(s) sur 12 (une saisie est passee ?)', n; end if;
end $$;
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = 'suppositions_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')'
   and r.origine = 'classeur_reconstitue' and r.ecrit_par = 'classeur:' || j.ligne_origine;
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, m.hektor_user_id, m.nom_au_moment, m.pourcentage, m.origine,
       m.ecrit_le, m.ecrit_par
  from public.app_affaire_repartition_mise_de_cote m where m.mise_de_cote_par = 'patch_suppositions_2026-11-24';
delete from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_suppositions_2026-11-24';
do $$
declare n int; e text;
begin
  select count(*) into n from (
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984)
     except select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_suppositions_20261124)
    union all
    (select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition_avant_suppositions_20261124
     except select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
       from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984))) d;
  if n <> 0 then raise exception '⛔ controle du retour : % part(s) differente(s) de la sauvegarde', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984));
  if e <> '1c741e0f96bb4a55c672d4e0cd37407d' then raise exception '⛔ controle du retour : empreinte % au lieu de 1c741e0f96bb4a55c672d4e0cd37407d (celle d''AVANT)', e; end if;
end $$;

do $$ declare e text; begin e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984)); raise exception 'ALLER-RETOUR A BLANC VERT : apres = % ; retour = % -- RIEN N''EST ECRIT (erreur voulue)', current_setting('ar.apres'), e; end $$;
