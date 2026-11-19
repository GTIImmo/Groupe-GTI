-- Retour arrière de patch_assistant_parcours_lecture_nego_2026-11-19.sql : remet la règle de lecture et la prise du
-- 19/11 matin (l'auteur lit son parcours même après la création). Sa part seulement : table, schéma, dépôt, purge intacts.
begin;
set local lock_timeout = '3s';
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
commit;
