-- 2026-07-09 : fiabiliser l'extraction du type de bien (propertyType) par le scan OCR.
--
-- Symptome : le type ecrit librement (ex. "Longere") remontait ~1 fois sur 3 seulement
-- (extraction non-deterministe), le reste du temps propertyType=null -> le front tombait
-- sur "Appartement" par defaut. Le mapping front (draftAnnoncePropertyTypeIdFromLabel)
-- etait sain ; le trou etait en amont : le scan ne renvoyait pas le type.
--
-- Correctif de FOND (le plus efficace, 1/3 -> 7/7 mesure) = description au niveau du champ
-- dans le schema OCR : backend/app/services/openai_listing_sheet_service.py (FIELD_DESCRIPTIONS).
-- Ce patch = le renfort COMPLEMENTAIRE cote prompt (registre app_agent_prompt, cache 60s,
-- sans redeploiement). Deja applique en prod le 2026-07-09 ; ce fichier le trace dans Git.
--
-- Idempotent : n'ajoute la consigne que si elle est absente.

UPDATE app_agent_prompt
SET instructions = instructions || ' IMPERATIF propertyType : renseigne TOUJOURS le champ propertyType avec le type de bien inscrit dans le champ "Type de bien" (section Le bien), en recopiant le mot EXACT tel qu ecrit meme s il est atypique ou hors liste (ex. longere, mas, corps de ferme, bastide, gite, pavillon, fermette, chalet, loft, immeuble, terrain, parking, studio). Ne laisse jamais propertyType vide des qu un type est ecrit sur la fiche.'
WHERE agent_key = 'scan_fiche'
  AND instructions NOT ILIKE '%IMPERATIF propertyType%';
