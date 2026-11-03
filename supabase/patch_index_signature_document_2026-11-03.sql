-- Pilotage (03/11/2026) — la lecture des signatures tombe en « statement timeout ».
-- Mesure sous le compte de Frédéric, transaction annulée : le filtre
--   metadata_json->'signature'->>'status' = any('{signed,pending}')
-- parcourt les 192 685 documents par la clé primaire pour en garder 512 : 15,5 s, la base coupe.
-- Remède : un index sur l'expression EXACTE que la lecture de l'écran envoie (lib/pilotage.ts, lireSignatures).
-- Additif : il ne change aucune donnée et aucune lecture existante. Retour arrière :
-- patch_index_signature_document_2026-11-03_INVERSE.sql.

create index if not exists idx_app_console_document_signature_statut
  on public.app_console_document (((metadata_json -> 'signature') ->> 'status'));

analyze public.app_console_document;

-- Contrôle : l'index existe, et la lecture de l'écran l'emprunte (à lancer sous le rôle authenticated
-- pour mesurer avec les droits de l'écran ; on doit lire « idx_app_console_document_signature_statut »).
select indexname from pg_indexes where indexname = 'idx_app_console_document_signature_statut';
explain select id from public.app_console_document
 where ((metadata_json -> 'signature') ->> 'status') = any (array['signed', 'pending']) order by id;
