-- ============================================================================
-- LES MANDANTS MANQUANTS DU REGISTRE DES MANDATS -- la colonne qui manquait
-- 05/10/2026
-- ============================================================================
-- SIGNALE PAR FREDERIC : des lignes du registre des mandats n'affichent AUCUN
-- mandant, alors que la fiche annonce et le registre des relations les ont.
--
-- MESURE : 638 lignes sans mandant sur 24 487, dont 607 que NOTRE registre des
-- liens connait parfaitement (il couvre 24 451 des 24 487 lignes, 99,9 %).
-- Les 31 restantes, personne ne les connait : elles doivent rester vides.
--
-- LA CAUSE N'EST PAS LA LIGNEE DU REGISTRE -- il est AUTONOME. Le defaut porte
-- sur UNE COLONNE SUR 25 : `mandants_texte`, la seule restee un TEXTE recopie de
-- Hektor, sans identifiant et sans chemin pour se remplir depuis chez nous.
-- Quand Hektor ne fournit plus ce texte (bien vendu, archive, fiche mandat
-- incomplete), RIEN ne prend le relais.
--
-- CE PATCH POSE LA COLONNE QUI PORTE LA LISTE, AVEC NOS DEUX IDENTIFIANTS :
--   [{"app_contact_id":10017629,"hektor_contact_id":"33233","nom":"Petra COSTE"},
--    {"app_contact_id":10017662,"hektor_contact_id":"33276","nom":"M. Guy COSTE"}]
-- C'est elle qui permettra les fiches CLIQUABLES (chantier separe) ; aujourd'hui
-- elle sert surtout de source au repli de `mandants_texte`.
--
-- ⭐ `text`, PAS `jsonb` : c'est la forme de toutes ses soeurs dans cette table
--   (`register_history_json`, `register_avenants_json`, `images_preview_json`,
--   `affaires_detail_json`). On ne cree pas une forme nouvelle.
--
-- ⚠ LA VUE ENUMERE SES COLONNES. Sans le second ordre, la colonne existerait
--   dans la table et resterait INVISIBLE au front -- le bug se deplacerait.
--   La colonne est ajoutee EN FIN de liste : `CREATE OR REPLACE VIEW` n'accepte
--   que cela, et cela preserve les droits (un DROP les perdrait). L'ordre des
--   colonnes n'a aucune importance pour PostgREST, qui les nomme.
--
-- LECTURE SEULE POUR LES DONNEES : aucune ligne n'est touchee. Le remplissage
-- vient du push (`export_app_payload.py` -> `build_mandat_register_rows`), qui
-- ne remplace JAMAIS un texte deja fourni par Hektor (controle a blanc du
-- 05/10 : 607 lignes comblees, 0 des 23 849 deja remplies modifiee).
-- ============================================================================

BEGIN;

ALTER TABLE public.app_mandat_register_current
    ADD COLUMN IF NOT EXISTS mandants_json text;

COMMENT ON COLUMN public.app_mandat_register_current.mandants_json IS
    'La LISTE des mandants du bien, avec nos deux identifiants par personne '
    '(app_contact_id, hektor_contact_id) et "muet":true quand la fiche de '
    'contact n''a pas de nom (fiche de couple). Construite depuis NOTRE registre '
    'des liens (app_relation, liens vivants seulement). 05/10/2026.';

CREATE OR REPLACE VIEW public.app_registre_mandats_current AS
 SELECT register_row_id,
    app_dossier_id,
    hektor_annonce_id,
    COALESCE(NULLIF(btrim(photo_url_listing_app), ''::text), photo_url_listing) AS photo_url_listing,
    COALESCE(images_preview_json_app::text, images_preview_json) AS images_preview_json,
    adresse_privee_listing,
    adresse_detail,
    code_postal,
    code_postal_prive_detail,
    ville_privee_detail,
    archive,
    diffusable,
    nb_portails_actifs,
    has_diffusion_error,
    portails_resume,
    numero_dossier,
    numero_mandat,
    titre_bien,
    ville,
    type_bien,
    prix,
    commercial_id,
    commercial_nom,
    negociateur_email,
    agence_nom,
    statut_annonce,
    validation_diffusion_state,
    mandat_source_id,
    mandat_numero_reference,
    mandat_type,
    mandat_type_source,
    mandat_date_debut,
    mandat_date_fin,
    mandat_montant,
    mandants_texte,
    mandat_note,
    priority,
    offre_id,
    offre_state,
    offre_last_proposition_type,
    compromis_id,
    compromis_state,
    vente_id,
    source_updated_at,
    register_source_kind,
    register_detail_available,
    register_version_count,
    register_embedded_avenant_count,
    register_history_json,
    register_avenants_json,
    register_detail_payload_json,
    source_hash,
    refreshed_at,
    register_sort_num,
    register_sort_group,
    price_change_event_count,
    price_change_last_source_kind,
    price_change_last_old_value,
    price_change_last_new_value,
    price_change_last_detected_at,
    price_change_last_source_updated_at,
    mandat_date_cloture,
    search_text,
    affaires_detail_json,
    commerce_sous_type,
    offre_type,
    photo_url_listing_app,
    images_preview_json_app,
    photo_url_listing AS photo_url_listing_hektor,
    images_preview_json AS images_preview_json_hektor,
    -- 05/10/2026 : la liste des mandants, avec nos deux identifiants.
    mandants_json
   FROM app_mandat_register_current r;

COMMIT;

-- ============================================================================
-- CE QUE LE PATCH DOIT RENDRE, TOUT DE SUITE APRES (avant tout push)
--   la colonne existe et la vue la montre :     1 ligne, valeur NULL
-- ============================================================================
-- SELECT mandants_json FROM public.app_registre_mandats_current LIMIT 1;
--
-- ET APRES LE PREMIER PUSH, la preuve du correctif :
--   lignes sans mandant : 638 -> 31
-- SELECT count(*) AS sans_mandant
--   FROM public.app_mandat_register_current
--  WHERE COALESCE(NULLIF(btrim(mandants_texte), ''), NULL) IS NULL;
-- ============================================================================
