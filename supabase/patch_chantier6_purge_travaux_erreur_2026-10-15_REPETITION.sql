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
-- ═══ LE COMPTE A CHANGE, ET LA CAUSE N'EST PAS CELLE QUE J'AVAIS ECRITE ═══════════
-- La premiere version de ce fichier parlait de 3 travaux et accusait un NOM DE FICHIER
-- (« .67-carnetentretien4 », point en tete). FAUX. Le corps des reponses, relu dans
-- app_console_job, donne la vraie cause :
--   {"statusCode":"415","error":"invalid_mime_type","code":"InvalidMimeType"}
--   {"statusCode":"413","error":"Payload too large","code":"EntityTooLarge"}
-- Le coffre `hektor-console-documents` porte une LISTE BLANCHE de 10 types et refuse
-- tout le reste, ainsi que tout fichier de plus de 50 Mo.
--
-- ETAT MESURE LE 15/10 a 14:00 — 33 travaux en erreur, TROIS familles :
--   27  415 invalid_mime_type  -> 23 .odt, 1 .ods, 2 .html, 1 sans extension
--    4  413 payload too large  -> des PDF de plus de 50 Mo
--    1  session Hektor expiree (page HTML au lieu de JSON) — PASSAGER (47824, 14/10)
--    1  « fetch failed » — PASSAGER (62899, 15/10)
-- 30 des 33 ont ete poses par ma passe a la main de ce matin : ils etaient deja la,
-- dormants, et c'est la relecture qui les a reveles.
--
-- ⛔⛔ CE PATCH NE SE COLLE QU'APRES LE REDEMARRAGE DES 4 SERVICES WORKER.
--   Sans le correctif du 15/10 (refusDefinitifDuCoffre + la tolerance de la boucle de
--   synchro), les 31 refus RETOMBERONT en erreur au prochain passage et l'alerte
--   reviendra des cette nuit. Avec lui : le document refuse reste sur notre serveur,
--   sa ligne est marquee (metadata_json.cloud_refuse), ses VOISINS sont enfin
--   telecharges et l'annonce va au bout.
--
-- A COLLER DANS https://supabase.com/dashboard/project/dwaqxfrinihnychuoptk/sql/new
-- Cette repetition N'ECRIT RIEN : elle joue le patch, puis son inverse, puis annule
-- tout par une erreur volontaire. Recopiez-moi le message.
--
-- CE QUE LE MESSAGE DOIT MONTRER (le nombre peut avoir bouge depuis 14:00 — c'est la
-- FORME qui compte, pas le chiffre) :
--   · « 1 avant », « 2 sauvegarde » et « 4 apres l inverse » = LE MEME nombre
--   · « 3 apres le patch » = 0
--   Exemple avec l'etat de 14:00 :
--   ESSAI ANNULE -- 1 avant: en erreur = 33 | 2 sauvegarde: lignes gardees = 33 |
--   3 apres le patch: en erreur = 0 | 4 apres l inverse: en erreur = 33 |
--   5 refus definitifs dedans (415/413) = 31
-- ═══════════════════════════════════════════════════════════════════════════════
begin;
set local statement_timeout = '30s';

create temporary table _mesure(etape text, n bigint) on commit drop;

insert into _mesure
select '1 avant: en erreur', count(*) from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error';

-- Combien, parmi eux, sont des refus DEFINITIFS du coffre ? (le reste est passager)
insert into _mesure
select '5 refus definitifs dedans (415/413)', count(*) from public.app_console_job
 where job_type = 'sync_console_documents' and status = 'error'
   and (error_message like '%InvalidMimeType%' or error_message like '%EntityTooLarge%');

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
