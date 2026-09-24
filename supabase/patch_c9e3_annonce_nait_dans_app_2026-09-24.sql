-- ═══════════════════════════════════════════════════════════════════════════
-- C.9-e (e3) — L'ANNONCE NAIT DANS L'APP, DERRIERE UN INTERRUPTEUR ETEINT
--                                                                 24/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Audit : notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md
--
-- AUJOURD'HUI : la creation pose une ligne PROVISOIRE (jeton) puis un travail ; le
-- numero de l'annonce n'existe qu'une fois Hektor passe par la.
--
-- CE PATCH, INTERRUPTEUR ALLUME : l'annonce recoit son numero A NOUS (distributeur
-- app_dossier_id_app_seq, depart 10 000 000) et sa VRAIE ligne dans
-- app_dossier_current, tout de suite. Le numero part avec le travail
-- (payload.app_dossier_id) : le worker y posera le numero Hektor (e2), et le
-- rafraichissement la retrouvera sous son numero au lieu d'en fabriquer un (e1).
--
-- INTERRUPTEUR ETEINT (etat pose par ce patch) : le code d'avant, a l'identique.
--
-- ⚠ PAS DE LIGNE PROVISOIRE quand l'interrupteur est allume : l'ecran n'ecarte une
--   provisoire que si une vraie ligne porte le MEME numero Hektor -- vide des deux
--   cotes, l'annonce s'afficherait en double (prependProvisionalRows, api.ts).
-- ⚠ type_bien N'EST PAS ECRIT : la colonne porte un CODE ('1', '2'...) et l'ecran
--   envoie un LIBELLE. La vraie valeur arrive de Hektor une minute plus tard.
-- ⚠ negociateur_email EST ECRIT : c'est lui qui rend la ligne VISIBLE au negociateur
--   (politique app_dossier_current_select_scoped_users).
-- ⚠ MEME TRANSACTION : si la creation du travail est refusee (role, agence), la
--   ligne d'annonce est annulee avec elle -- pas d'annonce fantome. Le numero tire
--   est perdu (une sequence ne revient pas en arriere) : un trou dans la serie, rien
--   de plus.
-- ⚠ MEME SIGNATURE, MEMES NOMS DE PARAMETRES : l'appel se fait par NOM depuis le
--   front ; en changer un casserait la creation sans un message.
--
-- ALLUMER  : update public.app_setting set value = 'on',  updated_at = now() where key = 'c9_annonce_nait_dans_app';
-- ETEINDRE : update public.app_setting set value = 'off', updated_at = now() where key = 'c9_annonce_nait_dans_app';
-- ═══════════════════════════════════════════════════════════════════════════

insert into public.app_setting (key, value, description, updated_at)
values ('c9_annonce_nait_dans_app', 'off',
        'C.9-e3 24/09/2026 : on = une annonce creee dans l''app recoit son numero a nous tout de suite (voir supabase/patch_c9e3_annonce_nait_dans_app_2026-09-24.sql). off = comportement d''avant.',
        now())
on conflict (key) do nothing;

create or replace function public.app_create_annonce_job_optimistic(
    p_token uuid, p_fields jsonb, draft_payload jsonb, draft_priority integer default null::integer)
 returns public.app_console_job
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
  created_job public.app_console_job;
  v_allume    boolean;
  v_champs    jsonb := coalesce(p_fields, '{}'::jsonb);
  v_id        bigint;
  v_prix      numeric;
begin
  select lower(trim(coalesce(s.value, ''))) in ('on', '1', 'true', 'oui')
    into v_allume
    from public.app_setting s
   where s.key = 'c9_annonce_nait_dans_app';

  if not coalesce(v_allume, false) then
    -- ── INTERRUPTEUR ETEINT : le code d'avant, a l'identique ────────────────
    -- 1. CHEZ NOUS D'ABORD -- best-effort : une provisoire ratee ne doit pas
    --    empecher la creation. On avale l'echec et on continue.
    begin
      perform public.app_create_annonce_provisional(p_token, v_champs);
    exception when others then
      null;
    end;
    -- 2. PUIS le travail, MEME TRANSACTION. S'il leve, la provisoire posee juste
    --    au-dessus est annulee avec lui : plus de bien fantome.
    created_job := public.app_console_create_draft_annonce_job(
      coalesce(draft_payload, '{}'::jsonb) || jsonb_build_object('creation_token', p_token::text),
      draft_priority);
    return created_job;
  end if;

  -- ── INTERRUPTEUR ALLUME : L'ANNONCE NAIT DANS L'APP ───────────────────────
  v_id := nextval('public.app_dossier_id_app_seq');

  if nullif(trim(v_champs->>'prix'), '') is not null then
    begin
      v_prix := replace(replace(v_champs->>'prix', ' ', ''), ',', '.')::numeric;
    exception when others then
      v_prix := null;   -- un prix illisible ne doit pas empecher la creation
    end;
  end if;

  insert into public.app_dossier_current (
      app_dossier_id, hektor_annonce_id, titre_bien, prix, ville, code_postal,
      statut_annonce, archive, commercial_nom, negociateur_email, agence_nom,
      source_hash, refreshed_at)
  values (
      v_id, null,
      coalesce(nullif(trim(v_champs->>'titre_bien'), ''), 'Annonce en création'),
      v_prix,
      nullif(trim(v_champs->>'ville'), ''),
      nullif(trim(v_champs->>'code_postal'), ''),
      coalesce(nullif(trim(v_champs->>'statut_annonce'), ''), 'Actif'),
      '0',
      nullif(trim(v_champs->>'commercial_nom'), ''),
      nullif(trim(v_champs->>'negociateur_email'), ''),
      nullif(trim(v_champs->>'agence_nom'), ''),
      'c9e3:' || p_token::text,
      now());

  created_job := public.app_console_create_draft_annonce_job(
    coalesce(draft_payload, '{}'::jsonb)
      || jsonb_build_object('creation_token', p_token::text, 'app_dossier_id', v_id),
    draft_priority);
  return created_job;
end;
$function$;

-- ═══════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE — la version en production avant ce patch, relue le 24/09 :
--
-- create or replace function public.app_create_annonce_job_optimistic(
--     p_token uuid, p_fields jsonb, draft_payload jsonb, draft_priority integer default null::integer)
--  returns app_console_job language plpgsql security definer set search_path to 'public'
-- as $function$
-- declare
--   created_job public.app_console_job;
-- begin
--   begin
--     perform public.app_create_annonce_provisional(p_token, coalesce(p_fields, '{}'::jsonb));
--   exception when others then
--     null;
--   end;
--   created_job := public.app_console_create_draft_annonce_job(
--     coalesce(draft_payload, '{}'::jsonb) || jsonb_build_object('creation_token', p_token::text),
--     draft_priority);
--   return created_job;
-- end;
-- $function$;
--
-- puis : delete from public.app_setting where key = 'c9_annonce_nait_dans_app';
-- ═══════════════════════════════════════════════════════════════════════════
