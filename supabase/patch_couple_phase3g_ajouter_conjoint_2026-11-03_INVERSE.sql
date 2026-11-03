-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · PIÈCE G — RETOUR ARRIÈRE                                         03/11/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Défait supabase/patch_couple_phase3g_ajouter_conjoint_2026-11-03.sql, et SEULEMENT lui (leçon 31) :
--   · solde d'abord les travaux `link_hektor_conjoint` encore en attente (status error, message dit) -- un
--     travail en cours (running) ARRÊTE le retour : attendre sa fin ;
--   · retire les trois fonctions neuves, le cran ;
--   · remet la distribution, les droits et la contrainte comme avant (les lignes déjà écrites avec ce type
--     restent lisibles : la contrainte est NOT VALID, elle ne juge que les nouvelles lignes).
-- ⚠ Il ne défait PAS un couple déjà rattaché chez Hektor : ça, c'est « Dissocier le couple » chez Hektor.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;
SET LOCAL lock_timeout = '5s';

DO $garde$
BEGIN
  IF EXISTS (SELECT 1 FROM public.app_console_job WHERE job_type = 'link_hektor_conjoint' AND status = 'running') THEN
    RAISE EXCEPTION 'ARRET : un travail link_hektor_conjoint tourne. Attendre sa fin. Rien n''est ecrit.';
  END IF;
END
$garde$;

update public.app_console_job
   set status = 'error', finished_at = now(), updated_at = now(),
       error_message = 'Annule : le geste « Ajouter un conjoint » a ete retire (retour arriere du ' || to_char(now(), 'DD/MM/YYYY') || ').'
 where job_type = 'link_hektor_conjoint' and status = 'pending';

drop function if exists public.app_ajouter_conjoint_optimistic(text, text, integer);
drop function if exists public.app_conjoint_relier_biens(uuid);
drop function if exists public.app_conjoint_annuler_optimiste(uuid);
delete from public.app_setting where key = 'contacts_couples_ajout';

DO $distribution$
DECLARE
  porte text := 'public.app_console_claim_next_job(text,text)';
  ancre text := $a$'unlink_hektor_mandant','archive_hektor_contact',
                    -- COUPLES 03/11/2026 : « Ajouter un conjoint ». Sans cette ligne, le travail reste « pending » a vie.
                    'link_hektor_conjoint'))$a$;
  ancien text := $n$'unlink_hektor_mandant','archive_hektor_contact'))$n$;
  src   text;
BEGIN
  src := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
  ancre := replace(ancre, chr(13), '');
  IF (length(src) - length(replace(src, ancre, ''))) / length(ancre) <> 1 THEN
    RAISE EXCEPTION 'ARRET : la ligne de la piece G est introuvable dans la distribution. Rien n''est ecrit.';
  END IF;
  EXECUTE replace(src, ancre, ancien);
END
$distribution$;

DO $droits$
DECLARE
  porte text := 'public.app_console_can_request_contact_job(text,text,text)';
  ancre text := $a$'delete_hektor_contact_search','archive_hektor_contact','link_hektor_conjoint')$a$;
  ancien text := $n$'delete_hektor_contact_search','archive_hektor_contact')$n$;
  src   text;
BEGIN
  src := replace(pg_get_functiondef(porte::regprocedure), chr(13), '');
  IF (length(src) - length(replace(src, ancre, ''))) / length(ancre) <> 1 THEN
    RAISE EXCEPTION 'ARRET : le type de la piece G est introuvable dans les droits. Rien n''est ecrit.';
  END IF;
  EXECUTE replace(src, ancre, ancien);
END
$droits$;

DO $contrainte$
DECLARE
  def   text := (SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'app_console_job_job_type_check');
  ancre text := '''youtrust_signing_link''::text, ''link_hektor_conjoint''::text]';
BEGIN
  IF (length(def) - length(replace(def, ancre, ''))) / length(ancre) <> 1 THEN
    RAISE EXCEPTION 'ARRET : le type de la piece G est introuvable dans la contrainte. Rien n''est ecrit.';
  END IF;
  def := replace(def, ancre, '''youtrust_signing_link''::text]');
  EXECUTE 'alter table public.app_console_job drop constraint app_console_job_job_type_check, add constraint app_console_job_job_type_check ' || def;
END
$contrainte$;

-- LE RETOUR NE JUGE QUE SA PART : les trois empreintes d'avant la pièce G doivent revenir.
SELECT 1 AS "#", 'distribution : empreinte d''avant' AS controle,
       CASE WHEN md5(replace(pg_get_functiondef('public.app_console_claim_next_job(text,text)'::regprocedure), chr(13), '')) = 'ce7d7a76dc307b2e4e72801133b525c8' THEN 'OK' ELSE '⛔ ECHEC' END AS verdict
UNION ALL SELECT 2, 'droits : empreinte d''avant',
       CASE WHEN md5(replace(pg_get_functiondef('public.app_console_can_request_contact_job(text,text,text)'::regprocedure), chr(13), '')) = '19d0fc0b1f4f22b0a91a05809ebe94bb' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 3, 'contrainte : empreinte d''avant',
       CASE WHEN md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'app_console_job_job_type_check')) = 'fe19373481b1a68edc273d3a276643c7' THEN 'OK' ELSE '⛔ ECHEC' END
UNION ALL SELECT 4, 'fonctions et cran retires',
       CASE WHEN to_regprocedure('public.app_ajouter_conjoint_optimistic(text,text,integer)') IS NULL
             AND to_regprocedure('public.app_conjoint_relier_biens(uuid)') IS NULL
             AND to_regprocedure('public.app_conjoint_annuler_optimiste(uuid)') IS NULL
             AND NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'contacts_couples_ajout') THEN 'OK' ELSE '⛔ ECHEC' END
ORDER BY 1;

COMMIT;
