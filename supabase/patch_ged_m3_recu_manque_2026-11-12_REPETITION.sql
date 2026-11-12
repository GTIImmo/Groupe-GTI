-- RÉPÉTITION — patch_ged_m3_recu_manque_2026-11-12.sql (CHANTIER GED, morceau 3).
-- Pose la règle de lecture et l'interrupteur DANS une transaction, lit le classement à la place d'un admin puis d'un
-- négociateur, puis lève une erreur VOLONTAIRE qui porte les verdicts : RIEN n'est gardé. Attendu : « 5 OK, 0 KO ».
-- ⚠ Le 12/11, aucun négociateur n'avait de classement sur ses biens : le ② compare à ce qu'il DOIT voir (0), pas à un
--   témoin positif. À rejouer quand un négociateur aura déposé avec l'outil.
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_ged_classement') is null then raise exception 'ARRET : morceau 1 absent'; end if;
  if exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'app_ged_classement') then raise exception 'ARRET : politique deja la'; end if;
  if exists (select 1 from public.app_setting where key = 'ged_recu_manque') then raise exception 'ARRET : interrupteur deja la'; end if;
end
$garde$;
grant select on table public.app_ged_classement to authenticated;
create policy app_ged_classement_select_scope on public.app_ged_classement
  for select to authenticated
  using (
    (select public.is_app_global_reader())
    or hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))
  );
insert into public.app_setting (key, value, description, updated_at) values
  ('ged_recu_manque', 'off', 'GED (12/11/2026) : le bloc « Reçu / Manque ». off / admin / on.', now());

do $essai$
declare v_admin uuid; v_nego uuid; n_admin int; n_nego int; n_total int; n_nego_attendu int; ok int := 0; ko int := 0; j text := ''; v_refus text := 'non refuse';
begin
  select count(*) into n_total from public.app_ged_classement;
  select id into v_admin from public.app_user_profile where is_active and role = 'admin' order by id limit 1;
  select id into v_nego from public.app_user_profile where is_active and role = 'commercial' order by id limit 1;

  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_admin from public.app_ged_classement;
  reset role;

  perform set_config('request.jwt.claims', json_build_object('sub', v_nego, 'role', 'authenticated')::text, true);
  select count(*) into n_nego_attendu from public.app_ged_classement c
   where c.hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid));
  set local role authenticated;
  select count(*) into n_nego from public.app_ged_classement;
  begin update public.app_ged_classement set type_code = type_code; exception when insufficient_privilege then v_refus := 'refuse'; end;
  reset role;

  if n_admin = n_total and n_total > 0 then ok := ok + 1; j := j || E'\nOK  ① un admin voit tous les classements : ' || n_admin; else ko := ko + 1; j := j || E'\nKO  ① admin voit ' || n_admin || ' sur ' || n_total; end if;
  if n_nego = n_nego_attendu then ok := ok + 1; j := j || E'\nOK  ② un négociateur ne voit que ceux de ses biens : ' || n_nego || ' (attendu ' || n_nego_attendu || ')'; else ko := ko + 1; j := j || E'\nKO  ② négo voit ' || n_nego; end if;
  if v_refus = 'refuse' then ok := ok + 1; j := j || E'\nOK  ③ l''écriture directe reste refusée'; else ko := ko + 1; j := j || E'\nKO  ③ écriture acceptée'; end if;
  if (select count(*) from public.app_setting where key = 'ged_recu_manque' and value = 'off') = 1 then ok := ok + 1; j := j || E'\nOK  ④ interrupteur éteint'; else ko := ko + 1; j := j || E'\nKO  ④'; end if;
  if (select count(*) from pg_policies where schemaname='public' and tablename in ('app_ged_rattachement','app_ged_journal')) = 0 then ok := ok + 1; j := j || E'\nOK  ⑤ rattachements et journal toujours illisibles'; else ko := ko + 1; j := j || E'\nKO  ⑤'; end if;
  raise exception 'RÉPÉTITION GED morceau 3 (rien n''est gardé) : % OK, % KO%', ok, ko, j;
end
$essai$;
rollback;
