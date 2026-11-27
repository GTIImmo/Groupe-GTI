-- patch_corrections_2026-11-24 -- genere par phase2/checks/repartition_4_5_generer_patchs_2026-11-24.py (« rien ne s'ecrit sans mon accord sur le patch »)
-- Retour arriere : patch_corrections_2026-11-24_INVERSE.sql . Controle : patch_corrections_2026-11-24_REPETITION.sql

begin;

-- ─── ① LES GARDES : chaque part a remplacer est EXACTEMENT celle mesuree, et chaque chaine porte 4 parts en tout ──
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_repartition_avant_corrections_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'corrections_2026-11-24';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_repartition r join (values
    (27196, 'entree', 1, '81', '50', 'classeur_reconstitue'),
    (27195, 'entree', 1, '82', '50', 'classeur_reconstitue')) v(ch, cote, rang, uid, pct, origine)
      on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.pourcentage = v.pct::numeric and r.origine = v.origine;
  if n <> 2 then raise exception '⛔ garde : % part(s) telles que mesurees sur 2', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (27195, 27196);
  if n <> 4 then raise exception '⛔ garde : les 2 chaines portent % part(s) au lieu de 4', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (27195, 27196));
  if e <> 'e6fc6ff49909d3a5592bd30d6d1f4fb8' then raise exception '⛔ garde : empreinte % au lieu de e6fc6ff49909d3a5592bd30d6d1f4fb8', e; end if;
  raise notice '✅ gardes : 2 parts telles que mesurees sur 2 chaines ; empreinte %', e;
end $$;

-- ─── ② LA SAUVEGARDE DATEE : les parts ENTIERES des 2 chaines ──────────────────────────────────────────────────────
create table public.app_affaire_repartition_avant_corrections_20261124 as
  select * from public.app_affaire_repartition where app_chaine_id in (27195, 27196);
revoke all on public.app_affaire_repartition_avant_corrections_20261124 from public, anon, authenticated;

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
select 'corrections_2026-11-24', v.n, 'repartition', 'app_affaire_repartition (' || v.cote || ', rang ' || v.rang || ')',
       'REMPLACER (le classeur fait foi ; l''ancienne mise de cote)', v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       v.uid || ' ' || v.nom || ' ' || v.pct, v.ancienne, v.ligne, v.num,
       'Sheet (Negociateurs / Pourcentages, regles du 13/11)', v.pourquoi, 'patch_corrections_2026-11-24'
  from (values
    (1, '739a0db1', 4668, 27196, 1, 'entree', '82', 'CELINE HERITIER', '50', '81 NICOLAS COUDERT 50 (classeur_reconstitue)', '⑤ SA DECISION du 24/11 (5e mot ⑤) : la moitie fausse remplacee par le nom du Sheet, l''ancienne part mise de cote avec son ancien numero (regle 6) ; COUDERT et HERITIER melanges sur le meme bien ; JRE23R1G n''est PAS touchee'),
    (2, 'TR42PT5H', 173, 27195, 1, 'entree', '81', 'NICOLAS COUDERT', '50', '82 CELINE HERITIER 50 (classeur_reconstitue)', '⑤ SA DECISION du 24/11 (5e mot ⑤) : la moitie fausse remplacee par le nom du Sheet, l''ancienne part mise de cote avec son ancien numero (regle 6) ; COUDERT et HERITIER melanges sur le meme bien ; JRE23R1G n''est PAS touchee')
  ) v(n, ligne, num, ch, rang, cote, uid, nom, pct, ancienne, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.ch;

-- ─── ⑤ LE GESTE : l'ancienne part MISE DE COTE (entiere, avec son numero de chaine), puis la nouvelle posee ──────────────
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, r.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'patch_corrections_2026-11-24', j.pourquoi || ' -- remplacee par ' || j.valeur || ' (ligne ' || j.ligne_origine || ')'
  from public.app_affaire_repartition r
  join public.app_classeur_realignement_journal j
    on j.lot = 'corrections_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = 'corrections_2026-11-24' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, v.uid, v.nom, v.pct::numeric, 'classeur_reconstitue', now(),
       'classeur:' || v.ligne
  from (values
    (27196, 'entree', 1, '82', 'CELINE HERITIER', '50', '739a0db1'),
    (27195, 'entree', 1, '81', 'NICOLAS COUDERT', '50', 'TR42PT5H')
  ) v(ch, cote, rang, uid, nom, pct, ligne)
  join public.app_affaire_repartition_mise_de_cote m
    on m.mise_de_cote_par = 'patch_corrections_2026-11-24' and m.app_chaine_id = v.ch and m.cote = v.cote and m.rang = v.rang;

-- ─── ⑥ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  -- chaque chaine porte EXACTEMENT la repartition voulue
  select count(*) into n from public.app_affaire_repartition r join (values
    (27195, 'entree', 1, '81', '50'),
    (27196, 'entree', 1, '82', '50')) v(ch, cote, rang, uid, pct)
      on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.pourcentage = v.pct::numeric and r.origine = 'classeur_reconstitue';
  if n <> 2 then raise exception '⛔ controle : % part(s) voulue(s) sur 2', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (27195, 27196);
  if n <> 4 then raise exception '⛔ controle : % part(s) sur les chaines au lieu de 4', n; end if;
  select count(*) into n from (select app_chaine_id from public.app_affaire_repartition where app_chaine_id in (27195, 27196)
                                group by 1 having sum(pourcentage) <> 100) x;
  if n <> 0 then raise exception '⛔ controle : % chaine(s) dont la somme n''est pas 100', n; end if;
  -- la regle 6 : chaque ancienne part est dans la mise de cote, ENTIERE (sa sauvegarde le prouve)
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m
    join public.app_affaire_repartition_avant_corrections_20261124 s
      on s.app_chaine_id = m.app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
     and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
     and s.ecrit_par is not distinct from m.ecrit_par and m.ancien_app_chaine_id = s.app_chaine_id
   where m.mise_de_cote_par = 'patch_corrections_2026-11-24';
  if n <> 2 then raise exception '⛔ controle : % ancienne(s) part(s) mise(s) de cote, entiere(s), sur 2', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal
   where lot = 'corrections_2026-11-24' and ligne_origine is not null and ancienne_valeur is not null;
  if n <> 2 then raise exception '⛔ controle : % ligne(s) au journal, avec ligne d''origine et ancienne valeur, sur 2', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id in (27195, 27196));
  if e <> 'adb3c8f86656a03da199a56ca9af6d15' then raise exception '⛔ controle : empreinte apres % au lieu de adb3c8f86656a03da199a56ca9af6d15', e; end if;
  raise notice '✅ 2 parts remplacees, 2 mises de cote entieres, sommes a 100, journal ; empreinte apres %', e;
end $$;

commit;
