export type DashboardSummary = {
  total_dossiers: number
  total_demandes: number
  total_sans_mandat: number
  total_bloques: number
  total_valides_diffusion: number
  total_visibles: number
}

export type DossierDetailPayload = {
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
  honoraires_json?: string | null
  notes_json?: string | null
  zones_json?: string | null
  particularites_json?: string | null
  pieces_json?: string | null
  images_json?: string | null
  textes_json?: string | null
  terrain_json?: string | null
  copropriete_json?: string | null
  detail_raw_json?: string | null
  annonce_list_raw_json?: string | null
  code_postal_detail?: string | null
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
  type_bien: string | null
  prix: number | null
  commercial_id: string | null
  commercial_nom: string | null
  negociateur_email?: string | null
  agence_nom?: string | null
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
}

export type DossierDetail = {
  app_dossier_id: number
  hektor_annonce_id: number
  detail_payload_json: string
}

export type DetailedDossier = Dossier & {
  detail_payload_json: string | null
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

export type UserProfile = {
  id: string
  email: string | null
  role: 'admin' | 'manager' | 'commercial' | 'lecture'
  first_name?: string | null
  last_name?: string | null
  display_name: string | null
  is_active: boolean
}

export type UserNegotiatorContext = {
  commercial_nom: string | null
  negociateur_email: string | null
  agence_nom: string | null
}

export type MandatRecord = {
  register_row_id?: string | null
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
  mandat_montant?: number | string | null
  mandants_texte?: string | null
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
