-- 17/11/2026 -- UN DOCUMENT SIGNÉ OU EN COURS DE SIGNATURE NE SE SUPPRIME PAS (le verrou de la BASE)
-- ---------------------------------------------------------------------------------------------------------
-- Note : notice/BLOCAGE_SUPPRESSION_DOCUMENT_SIGNE_2026-11-17.md. Règle GED §5.3 (« un document signé ou en cours de
-- signature ne peut être ni supprimé ni remplacé »), jusqu'ici appliquée NULLE PART : le bouton « Supprimer » insère
-- directement le travail `delete_document_from_hektor`, et la seule règle (insertion des travaux) ne regarde que les droits.
-- 544 documents engagés le 17/11 (485 signés ImmoSign, 57 ImmoSign en attente, 1 signé Youtrust, 1 Youtrust annulé).
--
-- Ce que pose ce patch (ADDITIF, rien d'existant n'est remplacé) :
--   1. `app_document_signature_engagee(metadata jsonb)` — la règle, la MÊME que l'écran (lib/choixSignature.ts) et le
--      worker (documentSignatureEngagee) : copie signée rapatriée, statut « signed », marque « à la main », ou statut
--      en cours (pending / ongoing / approval). « À envoyer », « annulé », « refusé » restent supprimables.
--   2. un garde AVANT l'insertion d'un travail `delete_document_from_hektor` : refus `document_signe_non_supprimable`
--      si le document visé est engagé. Il vaut pour TOUT appelant (écran, script, clé de service).
-- Retour arrière : patch_suppression_document_signe_garde_2026-11-17_INVERSE.sql. Contrôle : …_REPETITION.sql.

do $$
begin
  if exists (select 1 from pg_trigger where tgrelid = 'public.app_console_job'::regclass
               and tgname = 'app_console_job_refus_suppression_signe_trg') then
    raise exception 'DEJA POSE : le garde existe deja -- rien a faire.';
  end if;
  if to_regprocedure('public.app_document_signature_engagee(jsonb)') is not null then
    raise exception 'VERSION INATTENDUE : app_document_signature_engagee existe deja sans le garde -- on ne remplace pas a l''aveugle.';
  end if;
end $$;

create function public.app_document_signature_engagee(metadata jsonb)
returns boolean
language sql
immutable
as $$
  select coalesce(metadata ? 'signed_document', false)
      or coalesce(metadata -> 'signature' ->> 'status', '') in ('signed', 'pending', 'ongoing', 'approval')
      or coalesce(metadata -> 'signature' ->> 'source', '') = 'manuscrite'
$$;

comment on function public.app_document_signature_engagee(jsonb) is
  '17/11/2026 : document signé ou en cours de signature -> ne se supprime pas. Même règle que lib/choixSignature.ts et le worker.';

create function public.app_console_job_refus_suppression_signe()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id   text := nullif(trim(coalesce(new.payload_json ->> 'document_id', '')), '');
  v_nom  text;
  v_md   jsonb;
begin
  -- Un numéro illisible n'est pas notre affaire : le worker le refusera (« Document introuvable »).
  if v_id is null or v_id !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' then
    return new;
  end if;
  -- Par la clé, sans conversion de la colonne (l'index reste utilisé).
  select d.document_name, d.metadata_json into v_nom, v_md
    from public.app_console_document d
   where d.id = v_id::uuid;
  if found and public.app_document_signature_engagee(coalesce(v_md, '{}'::jsonb)) then
    raise exception 'document_signe_non_supprimable : un document signé ou en cours de signature ne se supprime pas (%)', coalesce(v_nom, v_id)
      using errcode = 'P0001', detail = 'document_signe_non_supprimable';
  end if;
  return new;
end
$$;

revoke all on function public.app_console_job_refus_suppression_signe() from public;

create trigger app_console_job_refus_suppression_signe_trg
  before insert on public.app_console_job
  for each row
  when (new.job_type = 'delete_document_from_hektor')
  execute function public.app_console_job_refus_suppression_signe();
