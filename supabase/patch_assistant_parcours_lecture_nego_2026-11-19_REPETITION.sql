-- Répétition de patch_assistant_parcours_lecture_nego_2026-11-19.sql SANS RIEN GARDER : pose, contrôle, rejoue
-- l'INVERSE et vérifie que l'auteur relit, puis ANNULE. Le dernier contrôle lève « TOUT EST VERT » EXPRÈS.
-- ⚠ L'auteur est un numéro tiré au hasard ; le négociateur et l'admin sont réels, seule leur LECTURE est jouée.
begin;
set local lock_timeout = '3s';

-- ═══════════════ (le corps du patch, sans son begin/commit)
do $garde$
begin
  -- la règle et la fonction sont-elles bien celles posées le 19/11 (patch_assistant_parcours_memoire) ?
  if (select replace(qual, chr(13), '') from pg_policies where schemaname = 'public' and tablename = 'app_assistant_parcours'
       and policyname = 'app_assistant_parcours_select')
     is distinct from '((user_id = ( SELECT auth.uid() AS uid)) OR ( SELECT is_app_admin() AS is_app_admin) OR app_assistant_parcours_du_negociateur(app_dossier_id))' then
    raise exception 'ARRET : la regle de lecture n''est pas celle du 19/11 -- quelqu''un est passe avant ?';
  end if;
  if md5(replace(pg_get_functiondef('public.app_assistant_mandant_prendre(uuid)'::regprocedure), chr(13), '')) <> '1be5c94ead90dbe712c12fef5367a986' then
    raise exception 'ARRET : app_assistant_mandant_prendre n''est pas celle du 19/11';
  end if;
end
$garde$;

drop policy app_assistant_parcours_select on public.app_assistant_parcours;
create policy app_assistant_parcours_select on public.app_assistant_parcours
  for select to authenticated
  using ((user_id = (select auth.uid()) and app_dossier_id is null)
         or (select public.is_app_admin())
         or public.app_assistant_parcours_du_negociateur(app_dossier_id));

create or replace function public.app_assistant_mandant_prendre(p_parcours_id uuid) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_user  uuid := auth.uid();
  v_coord jsonb;
begin
  -- P3 (19/11/2026). Rend les coordonnées ET LES EFFACE : la fenêtre les a reçues (règle du 19/11).
  -- P3 bis (19/11) : l'auteur AVANT la création seulement ; l'admin toujours. Un second appel rend null.
  -- Un parcours d'un autre : refus sans rien dire de plus.
  if v_user is null then raise exception '%', 'Connexion requise.'; end if;
  if not exists (select 1 from public.app_assistant_parcours t
                  where t.id = p_parcours_id
                    and ((t.user_id = v_user and t.app_dossier_id is null) or public.is_app_admin())) then
    raise exception '%', 'Parcours introuvable.';
  end if;
  delete from assistant_prive.mandant_coordonnees where parcours_id = p_parcours_id returning coordonnees into v_coord;
  return v_coord;
end
$function$;

do $verif$
begin
  if (select count(*) from pg_policies where schemaname = 'public' and tablename = 'app_assistant_parcours') <> 1 then
    raise exception 'ARRET : il faut exactement 1 regle de lecture';
  end if;
  if (select qual from pg_policies where tablename = 'app_assistant_parcours') not like '%app_dossier_id IS NULL%' then
    raise exception 'ARRET : la nouvelle regle n''est pas en place';
  end if;
  if has_function_privilege('service_role', 'public.app_assistant_mandant_prendre(uuid)', 'execute')
     or has_function_privilege('anon', 'public.app_assistant_mandant_prendre(uuid)', 'execute')
     or not has_function_privilege('authenticated', 'public.app_assistant_mandant_prendre(uuid)', 'execute') then
    raise exception 'ARRET : les droits de la prise ont bouge';
  end if;
end
$verif$;

create function pg_temp.comme(p_uid uuid, p_role text, p_sql text) returns text
language plpgsql as $f$
declare
  r text;
begin
  perform set_config('request.jwt.claims', json_build_object('sub', p_uid, 'role', p_role)::text, true);
  begin
    execute format('set local role %I', p_role);
    execute p_sql into r;
    execute 'reset role';
  exception when others then
    execute 'reset role';
    r := 'ERREUR: ' || sqlerrm;
  end;
  return r;
end
$f$;

do $controle$
declare
  v_admin   uuid;
  v_nego    uuid;
  v_dossier bigint;
  v_auteur  uuid := gen_random_uuid();   -- un auteur qui n'est PAS le négociateur (crée pour un autre)
  v_p       uuid;
  lire      text;
  r         text;
  ok        integer := 0;
begin
  select id into v_admin from public.app_user_profile where is_active and role::text = 'admin' limit 1;
  select p.id, d.app_dossier_id into v_nego, v_dossier
    from public.app_user_profile p
    join public.app_dossier_current d on lower(btrim(d.negociateur_email)) = lower(btrim(p.email))
   where p.is_active and p.role::text <> 'admin' and nullif(btrim(p.email), '') is not null
   order by d.app_dossier_id limit 1;
  if v_admin is null or v_nego is null then raise exception 'PAS PU MESURER : il faut un admin actif et un négociateur actif non admin'; end if;

  insert into public.app_assistant_parcours (user_id, genre, etape) values (v_auteur, 'creation_estimation', 'q3') returning id into v_p;
  lire := format('select count(*)::text from public.app_assistant_parcours where id = %L', v_p);

  -- ① AVANT la création : l'auteur lit (§85), le négociateur pas encore, l'admin oui
  if pg_temp.comme(v_auteur, 'authenticated', lire) <> '1' then raise exception 'ROUGE ① : l''auteur ne lit pas avant la création'; end if;
  if pg_temp.comme(v_nego, 'authenticated', lire) <> '0' then raise exception 'ROUGE ① : le négociateur lit trop tôt'; end if;
  if pg_temp.comme(v_admin, 'authenticated', lire) <> '1' then raise exception 'ROUGE ① : l''admin ne lit pas'; end if;
  ok := ok + 3;

  -- ② l'auteur peut prendre ses coordonnées AVANT la création (la fenêtre s'ouvre avant)
  perform pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_deposer(%L, %L)::text', v_p, '{"nom":"Essai"}'));
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r is null or (r::jsonb) ->> 'nom' <> 'Essai' then raise exception 'ROUGE ② : l''auteur ne prend pas avant la création (%)', r; end if;
  ok := ok + 1;

  -- ③ APRÈS la création : SA DÉCISION -- l'auteur ne lit plus ; le négociateur et l'admin lisent
  update public.app_assistant_parcours set app_dossier_id = v_dossier where id = v_p;
  if pg_temp.comme(v_auteur, 'authenticated', lire) <> '0' then raise exception 'ROUGE ③ : l''auteur lit encore après la création'; end if;
  if pg_temp.comme(v_nego, 'authenticated', lire) <> '1' then raise exception 'ROUGE ③ : le négociateur ne lit pas'; end if;
  if pg_temp.comme(v_admin, 'authenticated', lire) <> '1' then raise exception 'ROUGE ③ : l''admin ne lit pas'; end if;
  ok := ok + 3;

  -- ④ après la création, l'auteur ne prend plus ; l'admin si
  insert into assistant_prive.mandant_coordonnees (parcours_id, user_id, coordonnees) values (v_p, v_auteur, '{"nom":"Tard"}');
  r := pg_temp.comme(v_auteur, 'authenticated', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r not like 'ERREUR: Parcours introuvable%' then raise exception 'ROUGE ④ : l''auteur prend après la création (%)', r; end if;
  if not exists (select 1 from assistant_prive.mandant_coordonnees where parcours_id = v_p) then raise exception 'ROUGE ④ : le refus a effacé'; end if;
  r := pg_temp.comme(v_admin, 'authenticated', format('select public.app_assistant_mandant_prendre(%L)::text', v_p));
  if r is null or (r::jsonb) ->> 'nom' <> 'Tard' then raise exception 'ROUGE ④ : l''admin ne prend pas (%)', r; end if;
  ok := ok + 3;

  -- ⑤ les droits de la prise n'ont pas bougé (create or replace garde les droits)
  if pg_temp.comme(null, 'service_role', format('select public.app_assistant_mandant_prendre(%L)::text', v_p)) not like 'ERREUR:%' then
    raise exception 'ROUGE ⑤ : la clé de service a la prise';
  end if;
  ok := ok + 1;

  perform set_config('repetition.ok', ok::text, true);
  perform set_config('repetition.parcours', v_p::text, true);
  perform set_config('repetition.auteur', v_auteur::text, true);
end
$controle$;

-- ═══════════════ (le corps de l'INVERSE, sans son begin/commit)
drop policy app_assistant_parcours_select on public.app_assistant_parcours;
create policy app_assistant_parcours_select on public.app_assistant_parcours
  for select to authenticated
  using (user_id = (select auth.uid())
         or (select public.is_app_admin())
         or public.app_assistant_parcours_du_negociateur(app_dossier_id));

create or replace function public.app_assistant_mandant_prendre(p_parcours_id uuid) returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  v_user  uuid := auth.uid();
  v_coord jsonb;
begin
  -- P3 (19/11/2026). Rend les coordonnées ET LES EFFACE : la fenêtre les a reçues (règle du 19/11). Auteur ou admin.
  -- Un second appel rend null. Un parcours d'un autre : refus sans rien dire de plus.
  if v_user is null then raise exception '%', 'Connexion requise.'; end if;
  if not exists (select 1 from public.app_assistant_parcours t
                  where t.id = p_parcours_id and (t.user_id = v_user or public.is_app_admin())) then
    raise exception '%', 'Parcours introuvable.';
  end if;
  delete from assistant_prive.mandant_coordonnees where parcours_id = p_parcours_id returning coordonnees into v_coord;
  return v_coord;
end
$function$;

do $controle$
begin
  if (select replace(qual, chr(13), '') from pg_policies where tablename = 'app_assistant_parcours')
     is distinct from '((user_id = ( SELECT auth.uid() AS uid)) OR ( SELECT is_app_admin() AS is_app_admin) OR app_assistant_parcours_du_negociateur(app_dossier_id))' then
    raise exception 'contrôle : la règle du 19/11 matin n''est pas revenue';
  end if;
  if md5(replace(pg_get_functiondef('public.app_assistant_mandant_prendre(uuid)'::regprocedure), chr(13), '')) <> '1be5c94ead90dbe712c12fef5367a986' then
    raise exception 'contrôle : la prise du 19/11 matin n''est pas revenue';
  end if;
  if to_regclass('assistant_prive.mandant_coordonnees') is null or not exists (select 1 from cron.job where jobname = 'assistant-parcours-purge') then
    raise exception 'contrôle : une pièce sœur a disparu !';
  end if;
end
$controle$;

do $fin$
declare
  n text;
begin
  -- témoin inverse : avec la règle d'avant, l'auteur relit son parcours après la création
  n := pg_temp.comme(current_setting('repetition.auteur')::uuid, 'authenticated',
         format('select count(*)::text from public.app_assistant_parcours where id = %L', current_setting('repetition.parcours')));
  if n <> '1' then raise exception 'ROUGE inverse : l''auteur ne relit pas avec la règle d''avant (%)', n; end if;
  raise exception 'TOUT EST VERT (% contrôles + le témoin inverse) -- rien ne reste : annulé', current_setting('repetition.ok');
end
$fin$;
rollback;
