-- RÉPÉTITION — patch_ged_m6_lecture_2026-11-12.sql (CHANTIER GED, morceau 6, lot 1).
-- Pose les deux tables DANS une transaction, écrit une lecture factice sur un classement existant, la lit à la place
-- d'un admin puis d'un négociateur, tente une écriture par l'écran, puis lève une erreur VOLONTAIRE qui porte les
-- verdicts : RIEN n'est gardé. Attendu : « 7 OK, 0 KO ».
begin;
set local lock_timeout = '3s';
do $garde$
begin
  if to_regclass('public.app_ged_lecture') is not null then raise exception 'ARRET : deja pose'; end if;
  if not exists (select 1 from public.app_ged_classement) then raise exception 'ARRET : aucun classement pour l''essai'; end if;
end
$garde$;

create table public.app_ged_lecture (
  id uuid primary key default gen_random_uuid(),
  classement_id uuid not null references public.app_ged_classement (id) on delete cascade,
  hektor_annonce_id text not null, type_code text not null references public.app_ged_type (code),
  fiche text not null, modele text, etat text not null, pages_lues integer[], par_texte boolean not null default false,
  input_tokens integer, output_tokens integer, cout_usd numeric, lu_par uuid, lu_le timestamptz not null default now(),
  constraint app_ged_lecture_etat check (etat in ('lu', 'incomplet', 'pas_ce_type')),
  constraint app_ged_lecture_annonce_non_vide check (btrim(hektor_annonce_id) <> ''),
  constraint app_ged_lecture_fiche_non_vide check (btrim(fiche) <> ''));
create table public.app_ged_valeur (
  id bigint generated always as identity primary key,
  lecture_id uuid not null references public.app_ged_lecture (id) on delete cascade,
  cle text not null, rang integer not null default 0, valeur text, valeur_num numeric, valeur_date date, page integer,
  etat text not null,
  constraint app_ged_valeur_etat check (etat in ('lu', 'incertain', 'non_vu')),
  constraint app_ged_valeur_cle_non_vide check (btrim(cle) <> ''),
  constraint app_ged_valeur_unique unique (lecture_id, cle, rang));
alter table public.app_ged_lecture enable row level security;
alter table public.app_ged_valeur  enable row level security;
revoke all on table public.app_ged_lecture from public, anon, authenticated;
revoke all on table public.app_ged_valeur  from public, anon, authenticated;
revoke all on sequence public.app_ged_valeur_id_seq from public, anon, authenticated;
grant select on table public.app_ged_lecture to authenticated;
grant select on table public.app_ged_valeur  to authenticated;
create policy app_ged_lecture_select_scope on public.app_ged_lecture for select to authenticated
  using ((select public.is_app_global_reader()) or hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid)));
create policy app_ged_valeur_select_scope on public.app_ged_valeur for select to authenticated
  using (exists (select 1 from public.app_ged_lecture l where l.id = lecture_id));

do $essai$
declare v_c record; v_lecture uuid; v_admin uuid; v_nego uuid; n_admin int; n_val_admin int; n_nego int; n_nego_attendu int;
        ok int := 0; ko int := 0; j text := ''; v_refus text := 'non refuse'; v_refus_maj text := 'non refuse'; v_fk text := 'non refuse';
begin
  select id, hektor_annonce_id, type_code into v_c from public.app_ged_classement order by cree_le limit 1;
  insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, modele, etat, pages_lues)
    values (v_c.id, v_c.hektor_annonce_id, v_c.type_code, v_c.type_code || '/1', 'essai', 'lu', array[1]) returning id into v_lecture;
  insert into public.app_ged_valeur (lecture_id, cle, valeur_date, page, etat) values (v_lecture, 'date_etablissement', date '2026-03-01', 1, 'lu');
  insert into public.app_ged_valeur (lecture_id, cle, valeur, page, etat) values (v_lecture, 'commune', 'Villefictive', 1, 'incertain');

  select id into v_admin from public.app_user_profile where is_active and role = 'admin' order by id limit 1;
  select id into v_nego  from public.app_user_profile where is_active and role = 'commercial' order by id limit 1;

  perform set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
  set local role authenticated;
  select count(*) into n_admin from public.app_ged_lecture where id = v_lecture;
  select count(*) into n_val_admin from public.app_ged_valeur where lecture_id = v_lecture;
  begin insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, etat) values (v_c.id, v_c.hektor_annonce_id, v_c.type_code, 'x', 'lu');
  exception when insufficient_privilege then v_refus := 'refuse'; end;
  begin update public.app_ged_valeur set valeur = 'x' where lecture_id = v_lecture;
  exception when insufficient_privilege then v_refus_maj := 'refuse'; end;
  reset role;

  perform set_config('request.jwt.claims', json_build_object('sub', v_nego, 'role', 'authenticated')::text, true);
  select count(*) into n_nego_attendu from public.app_ged_lecture l
   where l.hektor_annonce_id in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid));
  set local role authenticated;
  select count(*) into n_nego from public.app_ged_lecture;
  reset role;

  begin insert into public.app_ged_valeur (lecture_id, cle, etat) values (gen_random_uuid(), 'x', 'lu');
  exception when foreign_key_violation then v_fk := 'refuse'; end;

  if n_admin = 1 then ok := ok + 1; j := j || E'\nOK  ① un admin lit la lecture'; else ko := ko + 1; j := j || E'\nKO  ①'; end if;
  if n_val_admin = 2 then ok := ok + 1; j := j || E'\nOK  ② et ses 2 valeurs'; else ko := ko + 1; j := j || E'\nKO  ② ' || n_val_admin; end if;
  if n_nego = n_nego_attendu then ok := ok + 1; j := j || E'\nOK  ③ un négociateur ne lit que les biens de son portefeuille : ' || n_nego || ' (attendu ' || n_nego_attendu || ')'; else ko := ko + 1; j := j || E'\nKO  ③ ' || n_nego; end if;
  if v_refus = 'refuse' then ok := ok + 1; j := j || E'\nOK  ④ l''écran ne peut pas écrire une lecture'; else ko := ko + 1; j := j || E'\nKO  ④'; end if;
  if v_refus_maj = 'refuse' then ok := ok + 1; j := j || E'\nOK  ⑤ ni modifier une valeur'; else ko := ko + 1; j := j || E'\nKO  ⑤'; end if;
  if v_fk = 'refuse' then ok := ok + 1; j := j || E'\nOK  ⑥ une valeur sans lecture est refusée'; else ko := ko + 1; j := j || E'\nKO  ⑥'; end if;
  if (select count(*) from pg_policies where tablename in ('app_ged_rattachement', 'app_ged_journal')) = 0 then ok := ok + 1; j := j || E'\nOK  ⑦ rattachements et journal toujours illisibles'; else ko := ko + 1; j := j || E'\nKO  ⑦'; end if;
  raise exception 'RÉPÉTITION GED morceau 6 lot 1 (rien n''est gardé) : % OK, % KO%', ok, ko, j;
end
$essai$;
rollback;
