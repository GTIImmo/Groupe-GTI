export type DashboardSummary = {
  total_dossiers: number
  total_demandes: number
  total_sans_mandat: number
  total_bloques: number
  total_valides_diffusion: number
  total_visibles: number
}

export type DossierDetailPayload = {
  matterport_groups_json?: string | null
  // G.15-d (27/09/2026) : le blob de detail vient de l'export du serveur et porte encore
  // les adresses Hektor (13 439 payloads sur 13 439, mesure du 27/09). api.ts y depose
  // NOTRE galerie, lue sur la colonne soeur de l'index, pour que l'ecran la voie.
  images_preview_json_app?: unknown
  appointment_public_token?: string | null
  appointment_public_url?: string | null
  appointment_negociateur_id?: string | number | null
  appointment_negociateur_email?: string | null
  appointment_requests_json?: string | null
  appointment_request_events_json?: string | null
  code_postal?: string | null
  surface?: number | string | null
  date_maj?: string | null
  date_enregistrement_annonce?: string | null
  photo_url_listing?: string | null
  corps_listing_html?: string | null
  ville_publique_listing?: string | null
  code_postal_public_listing?: string | null
  adresse_privee_listing?: string | null
  agence_nom?: string | null
  responsable_affichage?: string | null
  responsable_type?: string | null
  archive?: boolean | number | string | null
  diffusable?: boolean | number | string | null
  valide?: boolean | number | string | null
  mandat_type?: string | null
  mandat_date_debut?: string | null
  mandat_date_fin?: string | null
  mandat_date_cloture?: string | null
  mandat_numero_source?: string | null
  mandat_type_source?: string | null
  mandat_date_enregistrement?: string | null
  mandat_montant?: number | string | null
  mandants_texte?: string | null
  mandat_note?: string | null
  price_change_event_count?: number | null
  price_change_last_source_kind?: string | null
  price_change_last_old_value?: number | string | null
  price_change_last_new_value?: number | string | null
  price_change_last_detected_at?: string | null
  price_change_last_source_updated_at?: string | null
  price_change_events_json?: string | null
  nb_portails_actifs?: number | null
  has_diffusion_error?: boolean | number | null
  portails_resume?: string | null
  offre_id?: string | number | null
  offre_state?: string | null
  offre_last_proposition_type?: string | null
  offre_event_date?: string | null
  offre_raw_status?: string | null
  offre_montant?: number | string | null
  offre_acquereur_nom?: string | null
  offre_acquereur_portable?: string | null
  offre_acquereur_email?: string | null
  compromis_id?: string | number | null
  compromis_state?: string | null
  compromis_date_start?: string | null
  compromis_date_end?: string | null
  date_signature_acte?: string | null
  prix_net_vendeur?: number | string | null
  prix_publique?: number | string | null
  compromis_part_admin?: string | null
  compromis_sequestre?: number | string | null
  compromis_acquereurs_resume?: string | null
  vente_id?: string | number | null
  vente_date?: string | null
  vente_prix?: number | string | null
  vente_honoraires?: number | string | null
  vente_part_admin?: string | null
  vente_commission_agence?: number | string | null
  vente_acquereurs_resume?: string | null
  vente_notaires_resume?: string | null
  detail_statut_name?: string | null
  localite_json?: string | null
  mandats_json?: string | null
  proprietaires_json?: string | null
  /** ③c (02/10/2026) -- les mandants vus par NOTRE registre, poses par
   *  loadDossierDetail. ABSENT = repli sur `proprietaires_json` (interrupteur
   *  eteint, ou registre muet). Une liste VIDE n'est pas une absence : elle dit
   *  « ce bien n'a aucun mandant au registre », et l'ecran la respecte. */
  mandants_registre_json?: string | null
  honoraires_json?: string | null
  notes_json?: string | null
  zones_json?: string | null
  particularites_json?: string | null
  pieces_json?: string | null
  images_json?: string | null
  textes_json?: string | null
  ag_interieur_json?: string | null
  ag_exterieur_json?: string | null
  equipements_json?: string | null
  diagnostiques_json?: string | null
  terrain_json?: string | null
  copropriete_json?: string | null
  mandat_infofi_json?: string | null
  mandat_mandatdispo_json?: string | null
  organiser_visite_json?: string | null
  console_missing_fields_json?: string | null
  console_missing_fields_extracted_at?: string | null
  console_missing_fields_status?: string | null
  secteur_console_json?: string | null
  chauffage_console_json?: string | null
  chauffage_console_status?: string | null
  chauffage_console_extracted_at?: string | null
  diagnostics_contacts_console_json?: string | null
  honoraires_detail_console_json?: string | null
  location_rendement_console_json?: string | null
  pieces_detail_console_json?: string | null
  dpe_image_url?: string | null
  ges_image_url?: string | null
  dpe_image_urls_json?: string | null
  detail_raw_json?: string | null
  // Tier 2 — calque d'édition optimiste : valeurs éditées (clés Hektor brutes) écrites par
  // le RPC app_edit_annonce_optimistic, lues EN PRIORITÉ par rawDetailProp pour un affichage
  // instantané. Effacé automatiquement quand le read-through reconstruit detail_payload_json.
  app_optimistic_overlay?: Record<string, unknown> | string | null
  annonce_list_raw_json?: string | null
  code_postal_detail?: string | null
  ville_publique_detail?: string | null
  latitude_detail?: number | string | null
  longitude_detail?: number | string | null
  adresse_detail?: string | null
  ville_privee_detail?: string | null
  code_postal_prive_detail?: string | null
  nb_images?: number | null
  nb_textes?: number | null
  nb_notes_hektor?: number | null
  nb_proprietaires?: number | null
  images_preview_json?: string | null
  texte_principal_titre?: string | null
  texte_principal_html?: string | null
  nb_pieces?: number | null
  nb_chambres?: number | null
  surface_habitable_detail?: number | string | null
  etage_detail?: string | null
  terrasse_detail?: string | null
  garage_box_detail?: string | null
  surface_terrain_detail?: number | string | null
  copropriete_detail?: string | null
  ascenseur_detail?: string | null
  proprietaires_resume?: string | null
  proprietaires_contacts?: string | null
  honoraires_resume?: string | null
  note_hektor_principale?: string | null
  etat_transaction?: string | null
  internal_status?: string | null
  motif_blocage?: string | null
  next_action?: string | null
  date_entree_file?: string | null
  date_derniere_action?: string | null
  is_blocked?: boolean | number | null
  is_followup_needed?: boolean | number | null
}

export type Dossier = {
  app_dossier_id: number
  hektor_annonce_id: number
  // G.15-d (27/09/2026) -- LES ADRESSES DE PHOTOS CHEZ NOUS.
  // photo_url_listing et images_preview_json portent desormais NOS adresses des que nos
  // derives existent ; les adresses Hektor descendent dans les deux champs _hektor.
  // La substitution se fait dans api.ts, une seule fois, au plus pres de la base --
  // les vignettes et les galeries de l'ecran n'ont rien a savoir.
  photo_url_listing_app?: string | null
  images_preview_json_app?: unknown
  photo_url_listing_hektor?: string | null
  images_preview_json_hektor?: string | null
  // La famille d'offre Hektor : '0' vente, '10' vente immo pro, '6' neuf.
  // L'app ne detient que ces trois-la (les locations sont hors perimetre).
  offre_type?: string | null
  // C.15 27/08 -- LE BLOC COMMERCIAL (immobilier professionnel).
  // L'API REST de Hektor ecrase les huit sous-types en un seul code (idtype 23,
  // "Commerce") : elle disait la meme chose d'un entrepot et d'une pizzeria.
  // Ces champs viennent de GraphQL et ne sont remplis QUE pour l'immo pro.
  commerce_sous_type?: string | null
  commerce_famille?: string | null
  commerce_activite?: string | null
  commerce_loyer?: string | null
  commerce_charges?: string | null
  commerce_taxe_fonciere?: string | null
  commerce_bail_duree?: string | null
  commerce_bail_echeance?: string | null
  commerce_etat?: string | null
  commerce_zone?: string | null
  // Le bloc COMPLET, brut : CA et EBE sur trois exercices, lineaire de vitrine,
  // hauteur sous plafond, quai de chargement, PMR, divisibilite.
  commerce_json?: string | null
  photo_url_listing?: string | null
  images_preview_json?: string | null
  archive?: string | null
  diffusable?: string | null
  nb_portails_actifs?: number | null
  has_diffusion_error?: boolean | number | null
  portails_resume?: string | null
  offre_id?: string | number | null
  offre_state?: string | null
  offre_last_proposition_type?: string | null
  compromis_id?: string | number | null
  compromis_state?: string | null
  vente_id?: string | number | null
  numero_dossier: string | null
  numero_mandat: string | null
  titre_bien: string
  ville: string | null
  code_postal?: string | null
  date_maj?: string | null
  type_bien: string | null
  prix: number | null
  commercial_id: string | null
  commercial_nom: string | null
  negociateur_email?: string | null
  agence_nom?: string | null
  mandants_texte?: string | null
  // Champs mandat portes par app_dossiers_current. Ils etaient lus dans le cockpit
  // via un cast (dossierRec['mandat_montant']), donc hors controle du compilateur :
  // rien ne signalait qu'ils n'etaient jamais recopies depuis l'index leger.
  mandat_type?: string | null
  mandat_date_debut?: string | null
  mandat_date_fin?: string | null
  mandat_montant?: number | string | null
  statut_annonce: string | null
  validation_diffusion_state?: string | null
  price_change_event_count?: number | null
  price_change_last_source_kind?: string | null
  price_change_last_old_value?: number | string | null
  price_change_last_new_value?: number | string | null
  price_change_last_detected_at?: string | null
  price_change_last_source_updated_at?: string | null
  etat_visibilite: string | null
  alerte_principale: string | null
  priority: string | null
  has_open_blocker: boolean
  commentaire_resume: string | null
  date_relance_prevue: string | null
  dernier_event_type: string | null
  dernier_work_status: string | null
  has_local_detail?: boolean | number | string | null
  local_detail_updated_at?: string | null
  has_detail_cache?: boolean | number | string | null
  detail_cache_expires_at?: string | null
  is_brouillon?: boolean
}

export type DossierDetail = {
  app_dossier_id: number
  hektor_annonce_id: number
  detail_payload_json: string
}

export type DetailedDossier = Dossier & {
  detail_payload_json: string | null
}

export type MatterportModelLink = {
  id?: string | null
  matterport_model_id: string
  matterport_url: string
  matterport_name: string | null
  matterport_internal_id: string | null
  label: string | null
  display_order: number | null
  is_primary: boolean | null
  state: string | null
  visibility: string | null
  created_at_matterport: string | null
  modified_at_matterport: string | null
}

export type MatterportGroup = {
  id: string
  hektor_annonce_id: number
  numero_mandat: string | null
  group_label: string | null
  group_state: string | null
  group_visibility: string | null
  match_status: string | null
  is_validated: boolean | null
  synced_at: string | null
  models: MatterportModelLink[]
}

export type WorkItem = {
  app_dossier_id: number
  hektor_annonce_id: number
  photo_url_listing?: string | null
  images_preview_json?: string | null
  archive?: string | null
  numero_dossier: string | null
  numero_mandat: string | null
  titre_bien: string
  commercial_nom: string | null
  negociateur_email?: string | null
  agence_nom?: string | null
  type_demande_label: string | null
  work_status: string | null
  internal_status: string | null
  priority: string | null
  validation_diffusion_state: string | null
  etat_visibilite: string | null
  motif_blocage: string | null
  has_open_blocker: boolean
  next_action: string | null
  date_relance_prevue: string | null
  date_entree_file: string | null
  date_derniere_action: string | null
  age_jours: number | null
}

// PERIMETRE d'un compte (pose le 12/10/2026, chantier 2) : jusqu'ou il voit.
//   portefeuille  ses biens et ses contacts seulement
//   agence        toute son agence
//   reseau        tout le reseau  -- LE DEFAUT
// Il ne remplace PAS le role : un negociateur reste « commercial », on regle
// seulement jusqu'ou il voit (decision R2 de Frederic, pour eviter une 5e valeur
// de role : une valeur d'enum PostgreSQL ne peut jamais etre retiree).
export type UserPerimetre = 'portefeuille' | 'agence' | 'reseau'

export const USER_PERIMETRES: ReadonlyArray<{ valeur: UserPerimetre; libelle: string; aide: string }> = [
  { valeur: 'reseau', libelle: 'Tout le réseau', aide: 'Il voit les annonces, les contacts et les photos de toutes les agences. C’est le réglage normal d’un négociateur.' },
  { valeur: 'agence', libelle: 'Son agence', aide: 'Il ne voit que les biens et les contacts de son agence.' },
  { valeur: 'portefeuille', libelle: 'Ses biens seulement', aide: 'Il ne voit que ses propres biens et contacts. ⚠ L’écran Rapprochement lui est alors masqué, et il perd les archives qui ne portent pas son adresse.' },
]

export type UserProfile = {
  id: string
  email: string | null
  role: 'admin' | 'manager' | 'commercial' | 'lecture'
  first_name?: string | null
  last_name?: string | null
  display_name: string | null
  is_active: boolean
  // absent des comptes lus avant le 12/10 : on lit donc toujours avec un repli
  // sur « reseau », jamais en supposant que la cle existe.
  perimetre?: UserPerimetre | null
}

export type GoogleWorkspaceIdentity = {
  id: string
  app_user_id: string
  google_email: string
  workspace_domain: string
  hektor_user_id?: string | null
  hektor_negociateur_id?: string | null
  negociateur_email?: string | null
  link_status: 'pending' | 'linked' | 'conflict' | 'disabled'
  is_active: boolean
  last_login_at?: string | null
  last_checked_at?: string | null
  metadata_json?: Record<string, unknown> | null
}

export type UserNegotiatorContext = {
  commercial_nom: string | null
  negociateur_email: string | null
  agence_nom: string | null
  hektor_user_id?: string | null
}

export type HektorNegotiatorOption = {
  idUser: string
  label: string
  email: string | null
  agenceNom: string | null
  commercialId: string | null
  hektorNegociateurId?: string | null
  hektorAgenceId?: string | null
  agenceIdUser?: string | null
}

export type HektorAgencyOption = {
  idAgence: string
  idUser: string | null
  label: string
  email: string | null
}

export type MandatRecord = {
  // G.15-d (27/09/2026) -- LES ADRESSES DE PHOTOS CHEZ NOUS.
  // photo_url_listing et images_preview_json portent desormais NOS adresses des que nos
  // derives existent ; les adresses Hektor descendent dans les deux champs _hektor.
  // La substitution se fait dans api.ts, une seule fois, au plus pres de la base --
  // les vignettes et les galeries de l'ecran n'ont rien a savoir.
  photo_url_listing_app?: string | null
  images_preview_json_app?: unknown
  photo_url_listing_hektor?: string | null
  images_preview_json_hektor?: string | null
  register_row_id?: string | null
  // C.15 : le vrai sous-type immo pro (Hektor renvoie "Commerce" pour les huit).
  commerce_sous_type?: string | null
  app_dossier_id: number
  hektor_annonce_id: number
  photo_url_listing?: string | null
  images_preview_json?: string | null
  adresse_privee_listing?: string | null
  adresse_detail?: string | null
  code_postal?: string | null
  code_postal_prive_detail?: string | null
  ville_privee_detail?: string | null
  archive: string | null
  diffusable: string | null
  nb_portails_actifs: number | null
  has_diffusion_error: boolean | null
  portails_resume: string | null
  numero_dossier: string | null
  numero_mandat: string | null
  register_sort_group?: number | null
  register_sort_num?: number | null
  titre_bien: string
  ville: string | null
  type_bien: string | null
  prix: number | null
  commercial_id: string | null
  commercial_nom: string | null
  negociateur_email?: string | null
  agence_nom: string | null
  statut_annonce: string | null
  validation_diffusion_state?: string | null
  mandat_type?: string | null
  mandat_type_source?: string | null
  mandat_date_debut?: string | null
  mandat_date_fin?: string | null
  mandat_date_cloture?: string | null
  mandat_montant?: number | string | null
  mandants_texte?: string | null
  // 05/10/2026 : la LISTE des mandants, avec nos deux numeros par personne
  // (app_contact_id / hektor_contact_id) et "muet":true pour une fiche sans nom.
  mandants_json?: string | null
  price_change_event_count?: number | null
  price_change_last_source_kind?: string | null
  price_change_last_old_value?: number | string | null
  price_change_last_new_value?: number | string | null
  price_change_last_detected_at?: string | null
  price_change_last_source_updated_at?: string | null
  priority: string | null
  offre_id: string | null
  offre_state?: string | null
  offre_last_proposition_type?: string | null
  compromis_id: string | null
  compromis_state?: string | null
  vente_id: string | null
  source_updated_at: string | null
  refreshed_at: string | null
  mandat_source_id?: string | null
  mandat_numero_reference?: string | null
  mandat_note?: string | null
  register_source_kind?: string | null
  register_detail_available?: boolean | number | null
  register_version_count?: number | null
  register_embedded_avenant_count?: number | null
  register_history_json?: string | null
  register_avenants_json?: string | null
  register_detail_payload_json?: string | null
  affaires_detail_json?: string | null
  has_local_detail?: boolean | number | string | null
  local_detail_updated_at?: string | null
  has_detail_cache?: boolean | number | string | null
  detail_cache_expires_at?: string | null
  is_brouillon?: boolean
  // Calque création optimiste : ligne provisoire (bien pas encore créé dans Hektor)
  is_provisional?: boolean
  creation_token?: string | null
  provisional_status?: 'creating' | 'error'
}

export type ContactDuplicateSeverity = 'low' | 'medium' | 'high' | 'critical'

export type AppContact = {
  hektor_contact_id: string
  /** L4-c ③ 22/09 : LE numéro pour viser Hektor.
   *  `hektor_contact_id` est l'IDENTITÉ chez nous et peut valoir un numéro
   *  d'app (≥ 10 000 000) que Hektor ne connaît pas. Tout lien ou envoi vers
   *  Hektor doit passer par celui-ci. */
  hektor_target_id?: string | null
  hektor_agence_id?: string | null
  hektor_negociateur_id?: string | null
  negociateur_email?: string | null
  commercial_nom?: string | null
  agence_nom?: string | null
  civilite?: string | null
  nom?: string | null
  prenom?: string | null
  display_name: string
  archive: boolean | number | string | null
  date_enregistrement?: string | null
  date_maj?: string | null
  email?: string | null
  phone_primary?: string | null
  phone_secondary?: string | null
  ville?: string | null
  code_postal?: string | null
  adresse?: string | null
  birth_date?: string | null
  birth_place?: string | null
  marital_status?: string | null
  typologies_json?: string[] | string | null
  relation_roles_json?: string[] | string | null
  linked_annonce_count: number | null
  active_search_count: number | null
  total_search_count: number | null
  has_contact_detail?: boolean | number | string | null
  contact_detail_synced_at?: string | null
  supabase_sync_eligible?: boolean | number | string | null
  eligibility_reasons_json?: string[] | string | null
  duplicate_group_count: number | null
  duplicate_max_severity?: ContactDuplicateSeverity | null
  duplicate_primary_candidate_id?: string | null
  completeness_score?: number | null
  search_text?: string | null
  source_hash?: string | null
  refreshed_at?: string | null
}

export type AppContactRelation = {
  hektor_contact_id: string
  hektor_annonce_id: string
  app_dossier_id?: number | null
  numero_dossier?: string | null
  numero_mandat?: string | null
  titre_bien?: string | null
  role_contact: string
  photo_url_listing?: string | null
  contact_date_maj?: string | null
  relation_source?: string | null
  transaction_type?: string | null
  transaction_id?: string | null
  transaction_state?: string | null
  transaction_date?: string | null
  transaction_amount?: string | null
  is_active_annonce?: boolean | number | string | null
  statut_annonce?: string | null
  last_seen_at?: string | null
  refreshed_at?: string | null
}

export type AppContactSearch = {
  contact_search_key: string
  hektor_contact_id: string
  search_index: number
  archive: boolean | number | string | null
  is_active: boolean | number | string | null
  offre?: string | null
  villes_json?: string[] | string | null
  types_json?: Record<string, unknown> | string | null
  criteres_json?: Array<Record<string, unknown>> | string | null
  prix_min?: string | null
  prix_max?: string | null
  surface_min?: string | null
  surface_max?: string | null
  pieces_min?: string | null
  pieces_max?: string | null
  chambre_min?: string | null
  chambre_max?: string | null
  surface_terrain_min?: string | null
  surface_terrain_max?: string | null
  contact_date_maj?: string | null
  refreshed_at?: string | null
  // A.3 piece 5 (16/10/2026) : le MANDAT DE RECHERCHE que cette recherche
  // honore, quand notre registre peut le designer sans deviner. Il n'est pas
  // dans la table des recherches -- la descente Hektor la refait en entier
  // chaque nuit -- mais accroche a la volee par loadContactSearches.
  mandat_recherche?: AppContactMandatRecherche | null
}

// Une ligne de app_contact_mandat_recherche_current. `contact_search_key`
// vaut null quand aucune recherche ne peut etre designee sans deviner.
export type AppContactMandatRecherche = {
  hektor_contact_id: string
  numero_mandat: string
  contact_search_key: string | null
  search_index: number | null
  type: string | null
  date_debut: string | null
  date_fin: string | null
  date_cloture: string | null
  famille: string | null
  source_app: string | null
  designation: string | null
}

export type ContactStats = {
  total: number
  active: number
  archived: number
  duplicates: number
  highRiskDuplicates: number
  linked: number
  searchContacts: number
  activeSearchContacts: number
  eligible: number
}

export type MandatBroadcast = {
  app_dossier_id: number
  hektor_annonce_id: number
  passerelle_key: string
  commercial_key: string
  commercial_id: string | null
  commercial_nom: string | null
  commercial_prenom: string | null
  current_state: string | null
  export_status: string | null
  is_success: boolean
  is_error: boolean
  refreshed_at: string | null
}

export type DiffusionRequest = {
  id: string
  app_dossier_id: number
  hektor_annonce_id: number
  numero_dossier: string | null
  numero_mandat: string | null
  titre_bien: string
  commercial_nom: string | null
  request_type: string | null
  requested_by: string
  requested_by_label: string | null
  requested_by_name: string | null
  requested_at: string
  request_status: string
  request_comment: string | null
  request_reason: string | null
  admin_response: string | null
  refusal_reason: string | null
  follow_up_needed: boolean | null
  follow_up_at: string | null
  relaunch_count: number | null
  processed_by: string | null
  processed_by_label: string | null
  processed_by_name: string | null
  processed_at: string | null
  processing_comment: string | null
}

export type DiffusionRequestEvent = {
  id: string
  diffusion_request_id: string
  event_type: string
  event_label: string
  event_at: string
  actor_user_id: string | null
  actor_name: string | null
  actor_role: string | null
  payload_json: string | null
  created_at: string | null
}

export type DiffusionTarget = {
  app_dossier_id: number
  hektor_annonce_id: number
  hektor_broadcast_id: string
  portal_key: string | null
  target_state: 'enabled' | 'disabled'
  source_ref: string | null
  note: string | null
  requested_by_role: string | null
  requested_by_name: string | null
  requested_at: string | null
  last_applied_at: string | null
  last_apply_status: string | null
  last_apply_error: string | null
}

export type ConsoleDocumentStorageStatus =
  | 'cloud_available'
  | 'local_only'
  | 'pending_upload'
  | 'uploading'
  | 'archived_cloud_removed'
  | 'missing'
  | 'error'

export type ConsoleDocumentVisibility = 'private' | 'shared' | 'unknown'

export type ConsoleDocument = {
  id: string
  app_dossier_id: number | null
  hektor_annonce_id: string
  hektor_document_id: string | null
  document_type: string | null
  document_name: string
  source: string | null
  visibility: ConsoleDocumentVisibility
  storage_bucket: string | null
  storage_path: string | null
  storage_status: ConsoleDocumentStorageStatus
  // 3e (13/10/2026) : false = Hektor ne l'a plus, NOUS SI. La ligne et les fichiers
  // sont conservés (décision de Frédéric : « on garde dans l'app avec mention
  // supprimé chez Hektor »). Mêmes noms que app_console_photo (G.10bis).
  present_in_hektor?: boolean | null
  absent_depuis?: string | null
  // 3d / lot 2c (14/10/2026). storage_status existait deja (et connait deja
  // 'pending_upload') ; il manquait l'etat de l'ENVOI, qui est la seule chose capable
  // de dire qu'un depot a ECHOUE -- le repreneur n'etant pas encore branche, un echec
  // reste sinon totalement muet.
  envoi_hektor_statut?: string | null
  file_size: number | null
  sha256: string | null
  mime_type: string | null
  created_at_hektor: string | null
  synced_at: string | null
  last_accessed_at: string | null
  archive_policy: string | null
  metadata_json: Record<string, unknown> | null
  created_at: string | null
  updated_at: string | null
}

export type ConsolePhoto = {
  id: string
  app_dossier_id: number | null
  hektor_annonce_id: string
  // ⚠ 3d / lot 2c (14/10/2026) : DESORMAIS NULLABLE, et il l'etait deja en base.
  //   Une photo creee par l'app existe AVANT que Hektor lui donne un numero. Le type
  //   disait le contraire. (L'index UNIQUE tient : en Postgres les NULL y sont
  //   distincts, donc plusieurs photos en attente cohabitent.)
  hektor_photo_id: string | null
  filename: string | null
  url_preview: string | null
  url_hd: string | null
  visible: boolean
  legend: string | null
  sort_order: number | null
  source: string | null
  source_json: Record<string, unknown> | null
  synced_at: string | null
  created_at: string | null
  updated_at: string | null
  // G.15-d (27/09/2026) -- LE RECOUVREMENT DES PHOTOS.
  // url_preview et url_hd ci-dessus portent desormais NOS adresses des que les derives
  // existent ; les adresses Hektor d'origine ne sont pas perdues, elles descendent dans
  // les deux champs _hektor. C'est loadConsolePhotos qui fait la substitution, une fois,
  // pour que les dix points d'affichage n'aient rien a savoir.
  derives_json: Record<string, { chemin?: string; largeur?: number; octets?: number }> | null
  url_preview_hektor?: string | null
  url_hd_hektor?: string | null
  // 3d / lot 2c (14/10/2026) -- CE QUI PERMET A L'ECRAN DE DIRE « envoi en cours ».
  // ⚠ Sans ces deux champs, une photo deposee mais pas encore rangee par le worker
  //   s'afficherait en TUILE MUETTE, sans la moindre explication : elle n'a ni URL ni
  //   derives tant que le worker n'a pas tourne. (Elle atterrit en FIN de galerie, un
  //   sort_order vide passant apres tous les autres -- mesure : 1 -> 5 -> NULL.)
  storage_status?: ConsoleDocumentStorageStatus | null
  envoi_hektor_statut?: string | null
}

export type ConsoleJobStatus = 'pending' | 'running' | 'done' | 'error'

export type ConsoleJobType =
  | 'sync_console_documents'
  | 'prepare_document_cloud'
  | 'generate_estimation_pdf'
  | 'generate_mandat_document'
  | 'relance_signature'
  | 'cancel_signature_procedure'
  | 'upload_document_to_hektor'
  | 'delete_document_from_hektor'
  | 'sync_hektor_photos'
  | 'upload_hektor_photo'
  // 3 bloc 2 (14/10/2026) : la suppression d'une photo, jumelle de delete_document_from_hektor.
  | 'delete_hektor_photo'
  | 'link_hektor_mandant'
  | 'create_hektor_contact'
  | 'update_hektor_contact'
  // ⑦-1 (16/10/2026) : l'interrupteur de la fiche contact. UN SEUL type pour les deux
  // sens -- la charge porte `archive: true|false` -- comme chez Hektor.
  | 'archive_hektor_contact'
  | 'add_hektor_contact_search'
  | 'update_hektor_contact_search'
  | 'delete_hektor_contact_search'
  | 'delete_hektor_contact'
  | 'create_hektor_mandant_contact'
  | 'update_hektor_mandant_contact'
  | 'update_hektor_annonce_fields'
  | 'create_hektor_mandat_auto_number'
  | 'delete_hektor_annonce'
  | 'archive_hektor_annonce'
  | 'restore_hektor_annonce'
  | 'change_hektor_annonce_status'
  | 'assign_hektor_annonce_negotiator'
  | 'create_hektor_draft_annonce'
  | 'matterport_online'
  | 'matterport_offline'
  | 'matterport_archive'
  | 'matterport_reactivate'
  | 'refresh_console_data'
  | 'refresh_console_contact_data'
  | 'archive_cloud_documents'
  | 'prepare_archived_annonce_detail'
  | 'prepare_historical_annonce_detail'

export type ConsoleJob = {
  id: string
  job_type: ConsoleJobType
  app_dossier_id: number | null
  hektor_annonce_id: string | null
  payload_json: Record<string, unknown> | null
  status: ConsoleJobStatus
  priority: number
  requested_by: string | null
  requested_at: string
  started_at: string | null
  finished_at: string | null
  worker_id: string | null
  attempt_count: number
  error_message: string | null
  result_json: Record<string, unknown> | null
  created_at: string | null
  updated_at: string | null
}

export type ConsoleJobLog = {
  id: string
  job_id: string | null
  step: string | null
  status: string | null
  message: string | null
  payload_preview: string | null
  created_at: string
}
