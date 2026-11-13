-- Répétition de patch_ged_m8_remplir_2026-11-13.sql SANS RIEN GARDER : pose, contrôle, et ANNULE (rollback).
-- À coller tel quel ; chaque contrôle lève une exception s'il est ROUGE. Rien ne reste en base.
begin;
set local lock_timeout = '3s';

-- (le corps du patch, recopié sans son begin/commit)
create table public.app_ged_decision (
  id uuid primary key default gen_random_uuid(), hektor_annonce_id text not null,
  lecture_id uuid references public.app_ged_lecture (id) on delete set null, cle text not null, champ text not null,
  valeur text not null, decision text not null, detail jsonb, decide_par uuid not null, decide_le timestamptz not null default now(),
  constraint app_ged_decision_decision check (decision in ('remplie', 'ignoree', 'echec')),
  constraint app_ged_decision_annonce_non_vide check (btrim(hektor_annonce_id) <> ''),
  constraint app_ged_decision_cle_non_vide check (btrim(cle) <> ''));
alter table public.app_ged_decision enable row level security;
revoke all on table public.app_ged_decision from public, anon, authenticated;
grant select on table public.app_ged_decision to authenticated;
insert into public.app_setting (key, value, description, updated_at) values ('ged_remplir', 'off', 'répétition', now());

do $controle$
declare n int;
begin
  -- ① la contrainte refuse une décision inconnue
  begin
    insert into public.app_ged_decision (hektor_annonce_id, cle, champ, valeur, decision, decide_par)
    values ('63331', 'P1.dpe_cons', 'dpe_cons', '210', 'peut_etre', gen_random_uuid());
    raise exception 'ROUGE : une décision inconnue est passée';
  exception when check_violation then null;
  end;
  -- ② authenticated ne peut pas écrire directement
  if has_table_privilege('authenticated', 'public.app_ged_decision', 'insert') then raise exception 'ROUGE : authenticated peut écrire'; end if;
  if has_table_privilege('anon', 'public.app_ged_decision', 'select') then raise exception 'ROUGE : anon peut lire'; end if;
  -- ③ l'interrupteur est éteint
  select count(*) into n from public.app_setting where key = 'ged_remplir' and value = 'off';
  if n <> 1 then raise exception 'ROUGE : interrupteur'; end if;
  raise notice 'TOUT EST VERT (3 contrôles) -- rien ne reste : rollback';
end
$controle$;
rollback;
