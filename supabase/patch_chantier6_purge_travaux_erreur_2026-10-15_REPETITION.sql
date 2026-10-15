-- ═══════════════════════════════════════════════════════════════════════════════
-- REPETITION — purge des travaux documents en erreur        15/10/2026, chantier 6
-- ═══════════════════════════════════════════════════════════════════════════════
-- Demande de Frederic (15/10) : « si ce n'est pas deja fait, annule et efface les
-- travaux en erreur ».
--
-- ⚠ CE N'EST PAS UN CAPRICE DE PROPRETE, et la regle du projet l'autorise :
--   check_gti_health.py, sentinelle `data.travaux_en_erreur` (seuil 0, critical) :
--   « Une erreur qui reste est une erreur qu'on a decide de ne pas traiter. SOIT ON
--   REJOUE, SOIT ON PURGE EN ECRIVANT POURQUOI. »  -> on purge, et voici pourquoi.
--
-- ⭐ ET EFFACER LA LIGNE NE FAIT PAS QUE TAIRE L'ALERTE : le composeur de lot exclut
--   « pour toujours » toute annonce portant un travail en erreur (« on ne rejoue
--   jamais »). Retirer la ligne REND donc l'annonce a nouveau eligible. C'est le but.
--
-- LES TROIS, ET LEURS TROIS CAUSES DIFFERENTES :
--   47824  14/10 21:22  « Unexpected token '<', "<!DOCTYPE "... »
--                       -> Hektor a rendu une page HTML : SESSION EXPIREE. Passager :
--                          le worker s'est relogue seul, les 997 suivants ont passe.
--   62899  15/10 12:06  « fetch failed »
--                       -> accroc reseau. Passager.
--   61439  15/10 09:48  « Supabase Storage 400 ... /.67-carnetentretien4 »
--                       -> ⚠ PAS PASSAGER : le document s'appelle « .67-carnetentretien4 »,
--                          un nom qui COMMENCE PAR UN POINT, et Supabase refuse cette cle.
--                          Corrige dans storageSafeFilename le 15/10 (le point de tete
--                          devient « _ »), MAIS LE CORRECTIF N'EST ACTIF QU'APRES LE
--                          REDEMARRAGE DES 4 SERVICES.
--   ➡ A COLLER APRES LE REDEMARRAGE, sinon 61439 retombera en erreur au prochain
--     passage et l'alerte reviendra.
--
-- A COLLER DANS https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
-- Cette repetition N'ECRIT RIEN : elle joue le patch, puis son inverse, puis annule
-- tout par une erreur volontaire. Recopiez-moi le message.
--
-- MESSAGE ATTENDU (les chiffres doivent etre EXACTEMENT ceux-la) :
--   ESSAI ANNULE -- 1 avant: en erreur = 3 | 2 sauvegarde: lignes gardees = 3 |
--   3 apres le patch: en erreur = 0 | 4 apres l inverse: en erreur = 3
-- ═══════════════════════════════════════════════════════════════════════════════
begin;
set local statement_timeout = '30s';

create temporary table _mesure(etape text, n bigint) on commit drop;

insert into _mesure
select '1 avant: en erreur', count(*) from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

-- ── LE VRAI PATCH ────────────────────────────────────────────────────────────────
-- ⚠ LA SAUVEGARDE DATEE D'ABORD, patron du projet : on ne detruit jamais sans garder
--   une copie nommee, qu'on nettoiera plus tard.
create table if not exists public.app_console_job_erreurs_avant_purge_2026_10_15 as
select * from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

insert into _mesure
select '2 sauvegarde: lignes gardees', count(*)
  from public.app_console_job_erreurs_avant_purge_2026_10_15;

delete from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

insert into _mesure
select '3 apres le patch: en erreur', count(*) from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

-- ── LE VRAI INVERSE ─────────────────────────────────────────────────────────────
insert into public.app_console_job
select * from public.app_console_job_erreurs_avant_purge_2026_10_15;

insert into _mesure
select '4 apres l inverse: en erreur', count(*) from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

-- ── L'ERREUR VOLONTAIRE QUI ANNULE TOUT ─────────────────────────────────────────
do $$
declare r record; msg text := '';
begin
  for r in select etape, n from _mesure order by etape loop
    msg := msg || r.etape || ' = ' || r.n || ' | ';
  end loop;
  raise exception 'ESSAI ANNULE -- %', msg;
end $$;

commit;
