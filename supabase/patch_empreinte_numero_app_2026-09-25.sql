-- L'EMPREINTE DOCUMENTAIRE GAGNE SON NUMERO D'APP
--                                                                     25/09/2026
-- app_console_document_fingerprint est le CARNET DU RATTRAPAGE : c'est elle qui dit
-- quelles annonces ont deja ete regardees. Or elle etait la seule table de la chaine
-- documents a n'avoir AUCUN numero de l'app -- sa cle primaire EST hektor_annonce_id --
-- et elle ne figurait pas dans REPOINT_TABLES, contrairement a app_console_document,
-- app_console_photo et app_console_job.
--
-- ⚠⚠ ON N'ENLEVE RIEN. La cle primaire reste hektor_annonce_id, et tous les points
--    d'appel existants continuent d'interroger par ce numero :
--      Console/console_job_worker.js:1113      saveDocumentContentFingerprint
--      Console/enqueue_console_sync_jobs.js:225 loadFingerprints
--      Console/enqueue_console_sync_jobs.js:265 touchFingerprintChecked
--      Console/enqueue_empreinte_lot.js:70      le composeur de lots
--    Les workers ont BESOIN du numero Hektor : c'est lui qui designe la fiche chez
--    Hektor. On ajoute une colonne A COTE, on ne substitue pas.
--
-- Mesure prealable (25/09) : 58 140 numeros Hektor distincts, chacun vers UN SEUL
-- numero d'app. 0 empreinte ambigue, 0 sans correspondance -> le remplissage est sur.
--
-- Reversible :
--   alter table public.app_console_document_fingerprint drop column app_dossier_id;

begin;

alter table public.app_console_document_fingerprint
    add column if not exists app_dossier_id bigint;

comment on column public.app_console_document_fingerprint.app_dossier_id is
    'Notre numero de bien (25/09/2026). ADDITIF : la cle primaire reste hektor_annonce_id, '
    'dont les workers ont besoin pour designer la fiche chez Hektor. Cette colonne rend la '
    'table repointable (REPOINT_TABLES) et lisible apres la coupure.';

-- Remplissage depuis les QUATRE index -- une annonce ne vit pas que dans app_dossier_current.
update public.app_console_document_fingerprint f
   set app_dossier_id = p.id
  from (
        select hektor_annonce_id::text as h, app_dossier_id   as id from public.app_dossier_current
  union select hektor_annonce_id::text,      app_archive_id        from public.app_archive_annonce_index_current
  union select hektor_annonce_id::text,      app_historical_id     from public.app_historical_annonce_index_current
  union select hektor_annonce_id::text,      app_brouillon_id      from public.app_brouillon_annonce_index_current
       ) p
 where p.h = f.hektor_annonce_id::text
   and f.app_dossier_id is distinct from p.id;

create index if not exists idx_app_console_document_fingerprint_dossier
    on public.app_console_document_fingerprint (app_dossier_id);

-- GARDE-FOU : on refuse de valider si le remplissage n'est pas complet.
-- Une empreinte sans numero d'app resterait invisible au repointage -- exactement le
-- defaut qu'on corrige ici. Mieux vaut ne rien poser que poser a moitie.
do $$
declare
    v_total bigint;
    v_sans  bigint;
begin
    select count(*), count(*) filter (where app_dossier_id is null)
      into v_total, v_sans
      from public.app_console_document_fingerprint;

    raise notice 'empreintes = %, sans numero app = %', v_total, v_sans;

    if v_sans > 0 then
        raise exception 'REFUS : % empreinte(s) sur % sans numero app', v_sans, v_total;
    end if;
end $$;

commit;
