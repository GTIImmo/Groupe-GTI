-- Répétition de patch_ged_m10_jugement_2026-11-16.sql SANS RIEN GARDER : pose, contrôle, et ANNULE (rollback).
-- ⛔ Ce fichier ne porte AUCUN « commit » (leçon du 13/11 : un patch joué « à blanc » avec son commit s'est commité).
-- À coller tel quel ; chaque contrôle lève une exception s'il est ROUGE ; la dernière ligne dit « RÉPÉTITION VERTE ».
begin;
set local lock_timeout = '3s';

-- (le corps du patch, recopié sans son begin/commit)
create table public.app_ged_jugement (
  id uuid primary key default gen_random_uuid(), hektor_annonce_id text not null, regle text not null, cle text not null,
  texte text not null, niveau text not null, verdict text not null, commentaire text, juge_par uuid not null,
  juge_le timestamptz not null default now(),
  constraint app_ged_jugement_verdict check (verdict in ('vrai', 'faux', 'deja_su')),
  constraint app_ged_jugement_niveau check (niveau in ('alerte', 'piece', 'info')),
  constraint app_ged_jugement_annonce_non_vide check (btrim(hektor_annonce_id) <> ''),
  constraint app_ged_jugement_cle_non_vide check (btrim(cle) <> ''),
  constraint app_ged_jugement_regle_non_vide check (btrim(regle) <> ''),
  constraint app_ged_jugement_commentaire_court check (commentaire is null or length(commentaire) <= 500));
alter table public.app_ged_jugement enable row level security;
revoke all on table public.app_ged_jugement from public, anon, authenticated;
grant select on table public.app_ged_jugement to authenticated;

do $controle$
declare n int;
begin
  -- ① la contrainte refuse un verdict inconnu
  begin
    insert into public.app_ged_jugement (hektor_annonce_id, regle, cle, texte, niveau, verdict, juge_par)
    values ('63331', 'P9', 'P9|x', 'x', 'alerte', 'peut_etre', gen_random_uuid());
    raise exception 'ROUGE ① : un verdict inconnu est passé';
  exception when check_violation then null;
  end;
  -- ② la contrainte refuse un niveau inconnu
  begin
    insert into public.app_ged_jugement (hektor_annonce_id, regle, cle, texte, niveau, verdict, juge_par)
    values ('63331', 'P9', 'P9|x', 'x', 'urgent', 'vrai', gen_random_uuid());
    raise exception 'ROUGE ② : un niveau inconnu est passé';
  exception when check_violation then null;
  end;
  -- ③ un jugement correct passe
  insert into public.app_ged_jugement (hektor_annonce_id, regle, cle, texte, niveau, verdict, juge_par)
  values ('63331', 'P9', 'P9|x', 'x', 'alerte', 'vrai', gen_random_uuid());
  -- ④ authenticated ne peut QUE lire
  select count(*) into n from information_schema.role_table_grants
   where table_name = 'app_ged_jugement' and grantee in ('authenticated', 'anon', 'PUBLIC') and privilege_type <> 'SELECT';
  if n <> 0 then raise exception 'ROUGE ④ : % droit(s) d''écriture', n; end if;
  -- ⑤ anon n'a rien
  select count(*) into n from information_schema.role_table_grants where table_name = 'app_ged_jugement' and grantee = 'anon';
  if n <> 0 then raise exception 'ROUGE ⑤ : anon a % droit(s)', n; end if;
  raise notice 'RÉPÉTITION VERTE (5 contrôles) -- rien ne reste : rollback';
end
$controle$;
rollback;
