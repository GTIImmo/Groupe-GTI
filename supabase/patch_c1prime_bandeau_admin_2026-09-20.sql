-- ═══════════════════════════════════════════════════════════════════════════
-- C.1' — LE NEGOCIATEUR N'A PLUS DE DECISION A PRENDRE            20/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Frederic, 20/09 : « ce n'est pas l'utilisateur qui doit etre prevenu, son
-- ecriture doit etre saisie donc protegee. C'est moi qui dois etre prevenu,
-- puisque ce serait un bug entre Hektor et l'app. Lui ne peut rien y faire. »
--
-- CE QUE LE BANDEAU FAISAIT : il posait au negociateur une question a laquelle il
-- ne pouvait pas repondre (« j'ai refait » / « abandonner cette saisie »), pour un
-- incident dont il n'est pas responsable et qu'il ne peut pas reparer.
--
-- CE QU'ON CHANGE : le statut porte desormais la CAUSE et le droit de trancher.
-- L'ecran montrera au negociateur « c'est enregistre, la mise a jour de Hektor
-- attend » -- sans bouton -- et gardera les deux boutons pour l'admin.
--
-- Le controle d'acces ne change pas : c'est le meme app_console_can_request_job
-- qu'avant, et app_annonce_pending_resolve continue de le verifier de son cote.
-- Ici on ne fait qu'AFFICHER ou non les boutons.
--
-- RETOUR ARRIERE : la definition d'avant est dans le commit precedent de ce
-- fichier ; deux champs de plus dans un objet JSON ne cassent aucun appelant.
-- ═══════════════════════════════════════════════════════════════════════════

create or replace function public.app_annonce_edit_status(target_dossier_id bigint)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  d app_dossier_current%rowtype;
  p app_annonce_pending%rowtype;
  v_admin boolean;
begin
  select * into d from app_dossier_current where app_dossier_id = target_dossier_id;
  if not found then raise exception 'dossier_not_found' using errcode='22023'; end if;
  if not public.app_console_can_request_job('update_hektor_annonce_fields', target_dossier_id, d.hektor_annonce_id::text) then
    raise exception 'forbidden_annonce_status' using errcode='42501'; end if;

  select * into p from app_annonce_pending where app_dossier_id = target_dossier_id;
  if not found then
    return jsonb_build_object('pending', false);
  end if;

  select coalesce(bool_or(up.role = 'admin'), false) into v_admin
    from public.app_user_profile up
   where up.id = auth.uid();

  return jsonb_build_object(
    'pending',        true,
    'conflict',       coalesce(p.conflict, false),
    'partial',        coalesce(p.partial, false),
    'skipped_fields', coalesce(p.skipped_fields, '[]'::jsonb),
    'push_attempts',  coalesce(p.push_attempts, 0),
    'dirty_at',       p.dirty_at,
    'push_after',     p.push_after,
    -- 20/09 : la cause est portee par la ligne, elle n'est plus devinee.
    'cause',          p.cause,
    -- 20/09 : seul un admin se voit proposer de trancher.
    'peut_trancher',  coalesce(v_admin, false)
  );
end
$function$;
