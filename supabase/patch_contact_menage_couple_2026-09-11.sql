-- LE MENAGE, cote Supabase.                                     11/09/2026
-- Migration appliquee le 11/09 sous le nom contact_menage_couple_2026_09_11.
-- Copie versionnee, pour que le depot porte ce que la base porte.
--
-- POURQUOI. Hektor donne un numero de MENAGE a chaque contact (`refCouple`) et
-- cree une SECONDE fiche, vide, pour le second membre. Chez GTI elle n'a jamais
-- ete remplie : 133 343 fiches sans nom au miroir, dont 15 618 dans l'annuaire
-- en ligne, toutes affichees « Mr./Mme » et donc indistinguables.
--
-- L'API confirme le miroir : ContactById sur neuf de ces fiches rend `nom: ""`,
-- `prenom: ""`, `coordonnees: null`. Il n'y a rien a rattraper, il y a un LIEN a
-- suivre -- et Hektor le suit deja lui-meme a l'affichage.
--
-- `hektor_couple_contact_id` est la reference de HEKTOR, assumee comme telle.
-- `couple_role` est ce que l'ecran lit :
--     menage_resolu    fiche vide, porteuse connue    -> A MASQUER   96 877
--     menage_orphelin  porteuse disparue de Hektor    -> A GARDER    13 998
--     NULL             tout le reste
--
-- ⚠ CETTE MIGRATION EST OBLIGATOIRE AVANT LE PROCHAIN PUSH. Le pousseur envoie
--   la ligne locale entiere (`dict(row)`), donc sans ces colonnes il tomberait
--   sur « column does not exist » et le run de nuit echouerait.
--
-- RETOUR ARRIERE : ALTER TABLE app_contact_current DROP COLUMN couple_role,
-- DROP COLUMN hektor_couple_contact_id, puis recreer la vue sans les deux.

ALTER TABLE public.app_contact_current
    ADD COLUMN IF NOT EXISTS hektor_couple_contact_id text,
    ADD COLUMN IF NOT EXISTS couple_role text;

-- ⚠ CREATE OR REPLACE, PAS DROP. Postgres accepte l'ajout de colonnes EN FIN de
--   liste sans supprimer la vue, ce qui preserve les GRANT. Un DROP les aurait
--   effaces, et ils ne sont pas uniformes ici -- piege deja paye sur les RPC
--   (voir la memoire « renommer-parametre-rpc-supabase-piege »).
CREATE OR REPLACE VIEW public.app_contacts_current AS
 SELECT hektor_contact_id,
    hektor_agence_id,
    hektor_negociateur_id,
    negociateur_email,
    commercial_nom,
    agence_nom,
    civilite,
    nom,
    prenom,
    display_name,
    archive,
    date_enregistrement,
    date_maj,
    email,
    phone_primary,
    phone_secondary,
    ville,
    code_postal,
    typologies_json,
    relation_roles_json,
    linked_annonce_count,
    active_search_count,
    total_search_count,
    supabase_sync_eligible,
    eligibility_reasons_json,
    duplicate_group_count,
    duplicate_max_severity,
    duplicate_primary_candidate_id,
    completeness_score,
    search_text,
    source_hash,
    refreshed_at,
    has_contact_detail,
    contact_detail_synced_at,
    adresse,
    birth_date,
    birth_place,
    marital_status,
    hektor_couple_contact_id,
    couple_role
   FROM app_contact_current;
