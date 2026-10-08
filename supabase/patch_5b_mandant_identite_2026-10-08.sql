-- =====================================================================
-- CHANTIER ⑤ · POINT 5b -- MODIFIER UN MANDANT ECRIT ENFIN CHEZ NOUS
-- Date : 2026-10-08 · Detail : notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md
--
-- LE PROBLEME. Le crayon « Modifier » d'une carte de mandant envoie le NUMERO DE
-- HEKTOR (`hektor_target_id`, App.tsx:7272 -- et c'est le bon numero pour detacher un
-- mandant). Mais app_edit_contact_optimistic cherche le contact par
-- `hektor_contact_id`, qui porte NOTRE numero depuis la bascule du 23/09. Mesure du
-- 08/10 : sur 62 162 contacts, les deux numeros different pour 62 162 d'entre eux --
-- zero coincidence. L'appel levait donc `contact_not_found` A TOUS LES COUPS, et le
-- `exception when others then null` l'effacait. Resultat : ni valeur chez nous, ni
-- ligne d'attente, ni nouvel essai -- et l'ecran disait que c'etait parti.
--
-- LE CORRECTIF, ADDITIF : on TRADUIT la cible en identite, une fois, juste avant
-- l'ecriture. Le travail envoye a Hektor garde la cible et ne change pas.
--
-- CE QUI NE CHANGE PAS (verifie) :
--   · le travail pour Hektor : meme fonction, meme numero -- le worker ne voit rien,
--     AUCUN redemarrage necessaire ;
--   · le front : AUCUNE ligne, AUCUN deploiement (une seule appelante, api.ts:9271) ;
--   · app_edit_contact_optimistic : pas modifiee -- la fiche contact, qui passe deja
--     l'identite, garde exactement son comportement ;
--   · les registres : ni app_relation, ni le registre des mandats. Le registre des
--     liens ne porte pas l'identite (ni nom, ni telephone), et le registre des mandats
--     refabrique ses mandants depuis les liens vivants a chaque push ;
--   · le chantier ① : `create or replace` CONSERVE l'ACL (anon reste ferme). Ce patch
--     ne fait JAMAIS `drop function`.
--
-- CE QUE CA REPARE EN PLUS, sans une ligne de code de plus : l'etape 3 de la fonction
-- (designer le travail au balayage) etait DANS le meme bloc et n'etait donc jamais
-- atteinte. Elle protege du DOUBLE ENVOI et fait REESSAYER au bout de 30 min, 5 fois.
--
-- CE QUI RESTE, ET QUI N'EST PAS DE CE CHANTIER : le `exception when others then null`
-- continue d'effacer la trace d'un echec. C'est le chantier ④ (aucun echec silencieux).
--
-- RETOUR ARRIERE : supabase/patch_5b_mandant_identite_2026-10-08_INVERSE.sql
-- =====================================================================

BEGIN;
SET LOCAL statement_timeout='60s';

-- ---------------------------------------------------------------------
-- 0. GARDE-FOU D'ENTREE : la base est bien celle qu'on a mesuree.
-- ---------------------------------------------------------------------
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_attribute
   WHERE attrelid='public.app_contact_current'::regclass
     AND attname IN ('hektor_contact_id','hektor_target_id') AND NOT attisdropped;
  IF n <> 2 THEN RAISE EXCEPTION 'STOP : app_contact_current n''a pas ses deux colonnes de numero (%)', n; END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_proc
                  WHERE oid='public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)'::regprocedure) THEN
    RAISE EXCEPTION 'STOP : la fonction a corriger n''existe pas sous cette signature';
  END IF;

  IF md5(replace(pg_get_functiondef('public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)'::regprocedure), chr(13), ''))
     <> 'b8a89ff72095acb00dccbf3c857e90ab' THEN
    RAISE EXCEPTION 'STOP : la fonction a change depuis la mesure du 08/10 -- me prevenir avant d''appliquer';
  END IF;
END $$;

-- ---------------------------------------------------------------------
-- 1. LA FONCTION
-- ---------------------------------------------------------------------
create or replace function public.app_update_mandant_contact_optimistic(
  target_app_dossier_id   bigint,
  target_hektor_annonce_id text,
  target_contact_id       text,
  contact_payload         jsonb,
  job_priority            integer default 16
)
returns app_console_job
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  created_job public.app_console_job;
  champs      jsonb := '{}'::jsonb;
  cle         text;
  v_identite  text;
  -- Seules ces cles sont des CHAMPS du contact. Le reste du payload
  -- (identifiants, contexte negociateur) n'a rien a faire dans une edition :
  -- il partirait dans push_fields et polluerait l'envoi.
  connues     text[] := array['civilite','last_name','first_name','email',
                              'phone','address','postal_code','city'];
begin
  -- ── 1. LE TRAVAIL, avec ses garde-fous d'origine (par recouvrement) ──
  created_job := public.app_console_create_update_mandant_contact_job(
      target_app_dossier_id, target_hektor_annonce_id,
      target_contact_id, contact_payload, job_priority);

  -- ── 2. PUIS l'ecriture chez nous, best effort ──
  begin
    foreach cle in array connues loop
      if nullif(trim(coalesce(contact_payload->>cle, '')), '') is not null then
        champs := champs || jsonb_build_object(cle, contact_payload->>cle);
      end if;
    end loop;

    if champs <> '{}'::jsonb then
      -- ── 2bis. TRADUIRE LA CIBLE EN IDENTITE ── 5b, 08/10/2026 ───────────────
      --   L'ecran envoie `hektor_target_id`, LE NUMERO DE HEKTOR (App.tsx:7272,
      --   et c'est lui qu'il faut pour detacher un mandant). Or
      --   app_edit_contact_optimistic cherche par `hektor_contact_id`, qui porte
      --   NOTRE numero depuis la bascule du 23/09. Mesure du 08/10 : sur 62 162
      --   contacts, les deux numeros different pour 62 162 d'entre eux -- l'appel
      --   levait donc `contact_not_found` A TOUS LES COUPS, et le `exception when
      --   others` ci-dessous l'effacait. Ni valeur chez nous, ni ligne d'attente,
      --   ni nouvel essai. On traduit ici, une fois, au seul endroit qui en a besoin.
      select c.hektor_contact_id into v_identite
        from public.app_contact_current c
       where c.hektor_target_id = target_contact_id
       limit 1;

      if v_identite is null then
        -- Repli : l'appelant a peut-etre deja envoye l'identite.
        select c.hektor_contact_id into v_identite
          from public.app_contact_current c
         where c.hektor_contact_id = target_contact_id
         limit 1;
      end if;

      if v_identite is null then
        raise exception 'contact_not_found' using errcode = '22023';
      end if;

      perform public.app_edit_contact_optimistic(v_identite, champs);

      -- ── 3. UN SEUL ENVOI : on designe NOTRE travail au balayage ──
      update public.app_contact_pending
         set push_job_id = created_job.id, updated_at = now()
       where hektor_contact_id = v_identite;
    end if;
  exception when others then
    -- Le geste part quand meme chez Hektor. L'app n'aura simplement pas la
    -- valeur d'avance -- c'est le comportement d'avant, pas une regression.
    null;
  end;

  return created_job;
end;
$function$;

-- ---------------------------------------------------------------------
-- 9. CONTROLE DE SORTIE : un seul point faux -> exception -> rien n'est applique.
-- ---------------------------------------------------------------------
DO $$
DECLARE e text; anon_peut boolean; auth_peut boolean; svc_peut boolean;
BEGIN
  anon_peut := has_function_privilege('anon',          'public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)', 'EXECUTE');
  auth_peut := has_function_privilege('authenticated', 'public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)', 'EXECUTE');
  svc_peut  := has_function_privilege('service_role',  'public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)', 'EXECUTE');
  IF anon_peut THEN RAISE EXCEPTION 'CONTROLE : anon peut executer la fonction -- chantier ① casse'; END IF;
  IF NOT auth_peut THEN RAISE EXCEPTION 'CONTROLE : authenticated a PERDU le droit d''executer la fonction'; END IF;
  IF NOT svc_peut THEN RAISE EXCEPTION 'CONTROLE : service_role a PERDU le droit d''executer la fonction'; END IF;

  e := md5(replace(pg_get_functiondef('public.app_update_mandant_contact_optimistic(bigint,text,text,jsonb,integer)'::regprocedure), chr(13), ''));
  RAISE NOTICE 'droits apres patch : anon=non authenticated=oui service_role=oui';
  RAISE NOTICE 'empreinte de la fonction posee : % (attendu c0fe0f30a3dc1b2d4cdceea156800092)', e;
END $$;

COMMIT;
