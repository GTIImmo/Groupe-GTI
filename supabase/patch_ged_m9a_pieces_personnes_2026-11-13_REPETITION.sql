-- Répétition de patch_ged_m9a_pieces_personnes_2026-11-13.sql SANS RIEN GARDER : pose, contrôle, et ANNULE (rollback).
-- À coller tel quel (ou : node Console/apply_sql_patch.js <ce fichier>) ; chaque contrôle lève une exception s'il est
-- ROUGE, et le dernier lève « TOUT EST VERT » EXPRÈS pour que rien ne reste, même par un outil qui commite.
begin;
set local lock_timeout = '3s';

-- (le corps du patch, recopié sans son begin/commit)
-- ─────────────────────────────────────────────────────── ① LE SCHÉMA ET LA TABLE
create schema ged_prive;
revoke all on schema ged_prive from public, anon, authenticated;
comment on schema ged_prive is
  'GED morceau 9 (13/11/2026) : données personnelles à accès restreint. NON exposé par l''API : accès par les '
  'fonctions public.app_ged_piece_privee_* seulement. Non recopié par la descente.';

create table ged_prive.piece_identite (
  id                 bigint generated always as identity primary key,
  lecture_id         uuid not null references public.app_ged_lecture (id) on delete cascade,
  hektor_annonce_id  text not null,
  rang               integer not null default 0,
  cle                text not null,
  valeur             text,
  valeur_date        date,
  page               integer,
  etat               text not null,
  cree_le            timestamptz not null default now(),
  a_effacer_le       date not null default ((now() + interval '5 years')::date),
  constraint piece_identite_cle check (cle in ('pieces.numero', 'pieces.date_delivrance', 'pieces.autorite_delivrance')),
  constraint piece_identite_etat check (etat in ('lu', 'incertain')),
  constraint piece_identite_une_valeur check (valeur is not null or valeur_date is not null)
);
create index piece_identite_lecture_idx on ged_prive.piece_identite (lecture_id);
create index piece_identite_annonce_idx on ged_prive.piece_identite (hektor_annonce_id);
alter table ged_prive.piece_identite enable row level security;
revoke all on table ged_prive.piece_identite from public, anon, authenticated;
comment on table ged_prive.piece_identite is
  'GED morceau 9 (13/11/2026) : numéro, date et autorité de délivrance des pièces d''identité lues (registre '
  'anti-blanchiment). Écrite par app_ged_piece_privee_ecrire (clé de service seule), lue par app_ged_piece_privee_lire.';

-- ─────────────────────────────────────────────────────── ② LA PORTE D'ÉCRITURE (CLÉ DE SERVICE)
create function public.app_ged_piece_privee_ecrire(p_lecture_id uuid, p_lignes jsonb) returns integer
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_annonce text;
  v_type    text;
  v_n       integer;
begin
  -- GED morceau 9 (13/11/2026). Appelée par le serveur Render APRÈS avoir écrit la lecture. N'écrit que dans ged_prive.
  select l.hektor_annonce_id, l.type_code into v_annonce, v_type from public.app_ged_lecture l where l.id = p_lecture_id;
  if v_annonce is null then raise exception '%', 'Lecture introuvable.'; end if;
  if v_type <> 'justif.identite' then raise exception '%', 'Seule une pièce d''identité a un registre.'; end if;
  if jsonb_typeof(p_lignes) <> 'array' then raise exception '%', 'Lignes attendues en liste.'; end if;
  insert into ged_prive.piece_identite (lecture_id, hektor_annonce_id, rang, cle, valeur, valeur_date, page, etat)
  select p_lecture_id, v_annonce, coalesce((x ->> 'rang')::integer, 0), x ->> 'cle', x ->> 'valeur',
         (x ->> 'valeur_date')::date, (x ->> 'page')::integer, x ->> 'etat'
    from jsonb_array_elements(p_lignes) x;
  get diagnostics v_n = row_count;
  return v_n;
end
$function$;
comment on function public.app_ged_piece_privee_ecrire(uuid, jsonb) is
  'GED morceau 9 (13/11/2026) : écrit le registre d''une pièce d''identité lue (numéro, délivrance). Clé de service seule.';
revoke all on function public.app_ged_piece_privee_ecrire(uuid, jsonb) from public, anon, authenticated;
grant execute on function public.app_ged_piece_privee_ecrire(uuid, jsonb) to service_role;

-- ─────────────────────────────────────────────────────── ③ LA PORTE DE LECTURE
create function public.app_ged_piece_privee_lire(p_lecture_id uuid)
returns table (rang integer, cle text, valeur text, valeur_date date, page integer, etat text)
language plpgsql
stable
security definer
set search_path to 'public'
as $function$
declare
  v_annonce text;
begin
  -- GED morceau 9 (13/11/2026) : admin ou manager ACTIF, ou bien du portefeuille. Sinon : rien (pas d'erreur bavarde).
  select l.hektor_annonce_id into v_annonce from public.app_ged_lecture l where l.id = p_lecture_id;
  if v_annonce is null then return; end if;
  if not (exists (select 1 from public.app_user_profile p where p.id = auth.uid() and p.is_active and p.role in ('admin', 'manager'))
          or v_annonce in (select m.hid from public.app_mes_biens_portefeuille() m(id, hid))) then
    return;
  end if;
  return query
    select t.rang, t.cle, t.valeur, t.valeur_date, t.page, t.etat
      from ged_prive.piece_identite t where t.lecture_id = p_lecture_id order by t.rang, t.cle;
end
$function$;
comment on function public.app_ged_piece_privee_lire(uuid) is
  'GED morceau 9 (13/11/2026) : lit le registre d''une pièce d''identité : admin ou manager actif, ou bien du portefeuille.';
revoke all on function public.app_ged_piece_privee_lire(uuid) from public, anon, authenticated;
grant execute on function public.app_ged_piece_privee_lire(uuid) to authenticated;

-- ─────────────────────────────────────────────────────── ④ L'INTERRUPTEUR (ÉTEINT)
insert into public.app_setting (key, value, description, updated_at) values
  ('ged_lecture_personnes', 'off',
   'GED morceau 9 (13/11/2026) : lire par l''IA la pièce d''identité et la fiche de renseignements (le numéro de la '
   'pièce va au registre ged_prive). off / admin / on. Éteint = ces pièces ne sont pas lues.',
   now());

do $controle$
declare
  v_classement uuid;
  v_lecture    uuid;
  v_autre      uuid;
  n            integer;
  d            date;
begin
  -- ① la table refuse une clé hors du registre
  begin
    insert into ged_prive.piece_identite (lecture_id, hektor_annonce_id, cle, valeur, etat)
    values (gen_random_uuid(), '63331', 'pieces.nom', 'X', 'lu');
    raise exception 'ROUGE : une clé hors registre est passée';
  exception when check_violation then null;
  end;
  -- ② les rôles de l'app n'entrent pas
  if has_schema_privilege('authenticated', 'ged_prive', 'usage') or has_schema_privilege('anon', 'ged_prive', 'usage') then raise exception 'ROUGE : le schéma est ouvert'; end if;
  if has_function_privilege('authenticated', 'public.app_ged_piece_privee_ecrire(uuid, jsonb)', 'execute') then raise exception 'ROUGE : authenticated peut écrire le registre'; end if;
  if has_function_privilege('anon', 'public.app_ged_piece_privee_lire(uuid)', 'execute') then raise exception 'ROUGE : anon peut lire le registre'; end if;
  -- ③ une lecture inconnue : refusée à l'écriture, rien à la lecture
  begin
    perform public.app_ged_piece_privee_ecrire(gen_random_uuid(), '[]'::jsonb);
    raise exception 'ROUGE : lecture inconnue acceptée';
  exception when raise_exception then
    if sqlerrm not like 'Lecture introuvable%' then raise; end if;
  end;
  select count(*) into n from public.app_ged_piece_privee_lire(gen_random_uuid());
  if n <> 0 then raise exception 'ROUGE : lecture inconnue rend des lignes'; end if;
  -- ④ TÉMOIN POSITIF : une lecture de pièce d'identité (posée puis annulée) reçoit ses 3 valeurs, effacement à 5 ans
  select id into v_classement from public.app_ged_classement where type_code = 'justif.identite' limit 1;
  if v_classement is null then raise exception 'PAS PU MESURER : aucun classement de pièce d''identité'; end if;
  insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, modele, etat)
  values (v_classement, '62774', 'justif.identite', 'justif.identite/1', 'repetition', 'lu') returning id into v_lecture;
  n := public.app_ged_piece_privee_ecrire(v_lecture, '[{"cle":"pieces.numero","rang":0,"valeur":"SPECIMEN01","etat":"lu","page":1},
    {"cle":"pieces.date_delivrance","rang":0,"valeur_date":"2012-06-14","etat":"lu","page":1},
    {"cle":"pieces.autorite_delivrance","rang":0,"valeur":"Préfecture","etat":"incertain","page":1}]'::jsonb);
  if n <> 3 then raise exception 'ROUGE : % lignes écrites au lieu de 3', n; end if;
  select min(a_effacer_le) into d from ged_prive.piece_identite where lecture_id = v_lecture;
  if d <> (now() + interval '5 years')::date then raise exception 'ROUGE : effacement au %', d; end if;
  -- ⑤ une lecture d'un AUTRE type n'a pas de registre
  insert into public.app_ged_lecture (classement_id, hektor_annonce_id, type_code, fiche, modele, etat)
  values (v_classement, '62774', 'diag.erp', 'diag.erp/1', 'repetition', 'lu') returning id into v_autre;
  begin
    perform public.app_ged_piece_privee_ecrire(v_autre, '[{"cle":"pieces.numero","valeur":"X1234567","etat":"lu"}]'::jsonb);
    raise exception 'ROUGE : un état des risques a reçu un registre';
  exception when raise_exception then
    if sqlerrm not like 'Seule une pièce%' then raise; end if;
  end;
  -- ⑥ l'interrupteur est éteint
  if not exists (select 1 from public.app_setting where key = 'ged_lecture_personnes' and value = 'off') then raise exception 'ROUGE : interrupteur'; end if;
  raise exception 'TOUT EST VERT (6 contrôles) -- rien ne reste : annulé';
end
$controle$;
rollback;
