-- ═══════════════════════════════════════════════════════════════════════════════
-- ASSISTANT IA — P3 bis : APRÈS LA CRÉATION, SEULS LE NÉGOCIATEUR ET L'ADMIN LISENT     19/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- Note : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §92. Sa réponse du 19/11 : « que le négo et admin ».
--
-- ─── CE QUE CE PATCH CHANGE ───
--   ① la règle de lecture de app_assistant_parcours : l'AUTEUR ne lit son parcours QUE tant qu'aucune annonce n'y est
--      attachée (avant la création, c'est le §85) ; dès que l'annonce existe : son négociateur et l'admin seulement.
--   ② app_assistant_mandant_prendre : même règle pour l'auteur (avant la création seulement) ; l'admin toujours.
--   Rien d'autre : la table, le schéma privé, le dépôt et la purge sont inchangés.
--
-- ─── CE QUE ÇA POURRAIT TOUCHER AILLEURS ───
--   · rien ne lit encore cette table (0 ligne) ;
--   · en pratique un commercial crée pour LUI-MÊME (la fenêtre le force sur lui, D2) : il reste le négociateur, donc
--     il garde la lecture ; seul l'auteur qui crée POUR un autre la perd après la création.
--
-- ─── RETOUR ARRIÈRE ───
-- supabase/patch_assistant_parcours_lecture_nego_2026-11-19_INVERSE.sql (remet la règle du 19/11 matin).
-- Répétition sans rien garder : …_REPETITION.sql.
-- ═══════════════════════════════════════════════════════════════════════════════

begin;
set local lock_timeout = '3s';

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

commit;
