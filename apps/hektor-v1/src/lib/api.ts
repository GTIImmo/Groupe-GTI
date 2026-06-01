import { FunctionsFetchError, FunctionsHttpError, FunctionsRelayError } from '@supabase/supabase-js'
import { mockDiffusionRequestEvents, mockDiffusionRequests, mockDiffusionTargets, mockDossiers, mockMandatBroadcasts, mockMandats, mockSummary, mockUserProfile, mockWorkItems } from './mockData'
import { hasSupabaseEnv, supabase } from './supabase'
import type { AppContact, AppContactRelation, AppContactSearch, ConsoleDocument, ConsoleDocumentVisibility, ConsoleJob, ConsoleJobType, ConsolePhoto, ContactStats, DashboardSummary, DetailedDossier, DiffusionRequest, DiffusionRequestEvent, DiffusionTarget, Dossier, DossierDetail, GoogleWorkspaceIdentity, HektorAgencyOption, HektorNegotiatorOption, MandatBroadcast, MandatRecord, MatterportGroup, MatterportModelLink, UserNegotiatorContext, UserProfile, WorkItem } from '../types'

export type FilterCatalog = {
  commercials: string[]
  agencies: string[]
  statuts: string[]
  validationDiffusions: string[]
  diffusions: string[]
  passerelles: string[]
  erreursDiffusion: string[]
  priorities: string[]
  workStatuses: string[]
  internalStatuses: string[]
}

export type AppFilters = {
  query: string
  mandatNumber: string
  mandantName: string
  mandateState: string
  commercial: string
  agency: string
  archive: string
  detailAvailability: string
  mandat: string
  affaire: string
  offreStatus: string
  compromisStatus: string
  requestScope: string
  requestType: string
  statut: string
  validationDiffusion: string
  diffusable: string
  passerelle: string
  erreurDiffusion: string
  priority: string
  workStatus: string
  internalStatus: string
  contactRole: string
  contactSearchScope: string
}

function normalizeMandateStatusValue(value: string | null | undefined) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
}

function isMandateEndDateStillValid(value: string | null | undefined) {
  if (!value) return true
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return true
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  date.setHours(0, 0, 0, 0)
  return date.getTime() >= today.getTime()
}

function mandateLifecycleState(item: Pick<MandatRecord, 'statut_annonce' | 'mandat_date_fin'>) {
  const status = normalizeMandateStatusValue(item.statut_annonce)
  if (status.includes('vendu') || status.includes('vente') || status.includes('clos') || status.includes('clotur')) return 'Annulé'
  if (status.includes('offre') || status.includes('compromis')) return 'En cours'
  if (status === 'actif' && isMandateEndDateStillValid(item.mandat_date_fin)) return 'En cours'
  return 'Annulé'
}

function applyMandateLifecycleFilter<T extends Pick<MandatRecord, 'statut_annonce' | 'mandat_date_fin'>>(rows: T[], filters: AppFilters) {
  const wantedState = normalizeFilterValue(filters.mandateState)
  if (!wantedState) return rows
  return rows.filter((item) => mandateLifecycleState(item) === wantedState)
}

export type PageResult<T> = {
  rows: T[]
  total: number
  page: number
  pageSize: number
}

export type MandatStats = {
  total: number
  withoutMandat: number
  mandatNonDiffuse: number
  mandatDiffuse: number
  mandatValide: number
  mandatNonValide: number
  offresEnCours: number
  offresRefusees: number
  compromisEnCours: number
  compromisAnnules: number
  affairesEnCours: number
  affairesAnnulees: number
  leboncoin: number
  bienici: number
  withErrors: number
}

export type SuiviRequestStats = {
  pendingOrInProgress: number
  refused: number
  accepted: number
  acceptedHistorical: number
}

export type CommercialRequestStats = {
  sent: number
  waitingCorrection: number
}

export type DataScope = {
  negotiatorEmail?: string | null
}

type AppointmentSummaryResponse = {
  ok?: boolean
  context?: {
    token?: string | null
    publicUrl?: string | null
    commercialId?: string | number | null
    negociateurEmail?: string | null
  } | null
  requests?: unknown[]
  events?: unknown[]
}

const allFilterValue = '__all__'
const activeArchiveFilterValue = '__active__'
const archivedFilterValue = '__archived__'
const withMandatFilterValue = '__with_mandat__'
const withoutMandatFilterValue = '__without_mandat__'
const withoutCommercialFilterValue = '__without_commercial__'
const activeListingsFilterValue = '__active_listings__'
const annonceSearchListingsFilterValue = '__annonce_search_listings__'
const activeListingStatuses = ['Actif', 'Sous offre', 'Sous compromis']
const historicalListingStatuses = ['Vendu', 'Clos']
const compromisCancelledQuery = 'compromis_state.in.("cancelled","annule","annulé","annuled")'
const noCancelledCompromisQuery = 'compromis_id.is.null,compromis_state.is.null,compromis_state.not.in.("cancelled","annule","annulé","annuled")'
const dossiersCurrentView = 'app_dossiers_current'
const contactsCurrentView = 'app_contacts_current'
const contactStatsCurrentTable = 'app_contact_stats_current'
const contactRelationsCurrentView = 'app_contact_relations_current'
const contactSearchesCurrentView = 'app_contact_searches_current'
const contactsListingSelect = [
  'hektor_contact_id',
  'hektor_agence_id',
  'hektor_negociateur_id',
  'negociateur_email',
  'commercial_nom',
  'agence_nom',
  'civilite',
  'nom',
  'prenom',
  'display_name',
  'archive',
  'date_enregistrement',
  'date_maj',
  'email',
  'phone_primary',
  'phone_secondary',
  'ville',
  'code_postal',
  'typologies_json',
  'relation_roles_json',
  'linked_annonce_count',
  'active_search_count',
  'total_search_count',
  'has_contact_detail',
  'contact_detail_synced_at',
  'supabase_sync_eligible',
  'eligibility_reasons_json',
  'duplicate_group_count',
  'duplicate_max_severity',
  'duplicate_primary_candidate_id',
  'completeness_score',
  'refreshed_at',
].join(',')
const activeContactSearchFilterValue = '__active_search__'
const withContactSearchFilterValue = '__with_search__'
const withoutContactSearchFilterValue = '__without_search__'
const requestStatuses = ['pending', 'in_progress', 'waiting_commercial', 'accepted', 'refused']
const localDiffusionTargetsKey = 'hektor-v1-diffusion-targets'
const localDiffusionRequestsKey = 'hektor-v1-diffusion-requests'
const localDiffusionRequestEventsKey = 'hektor-v1-diffusion-request-events'
const backendApiBaseUrl = (
  import.meta.env.VITE_BACKEND_API_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8010' : '')
).trim().replace(/\/+$/, '')
const defaultDiffusionAgencyTargets = [
  { agence_nom: 'Groupe GTI Ambert', portal_key: 'bienicidirect', hektor_broadcast_id: '2' },
  { agence_nom: 'Groupe GTI Ambert', portal_key: 'leboncoinDirect', hektor_broadcast_id: '35' },
  { agence_nom: 'Groupe GTI ANNONAY', portal_key: 'bienicidirect', hektor_broadcast_id: '3' },
  { agence_nom: 'Groupe GTI ANNONAY', portal_key: 'leboncoinDirect', hektor_broadcast_id: '36' },
  { agence_nom: 'Groupe GTI BRIOUDE', portal_key: 'bienicidirect', hektor_broadcast_id: '4' },
  { agence_nom: 'Groupe GTI BRIOUDE', portal_key: 'leboncoinDirect', hektor_broadcast_id: '41' },
  { agence_nom: 'Groupe GTI Craponne-sur-Arzon', portal_key: 'bienicidirect', hektor_broadcast_id: '5' },
  { agence_nom: 'Groupe GTI Craponne-sur-Arzon', portal_key: 'leboncoinDirect', hektor_broadcast_id: '42' },
  { agence_nom: 'Groupe GTI Yssingeaux', portal_key: 'bienicidirect', hektor_broadcast_id: '6' },
  { agence_nom: 'Groupe GTI Yssingeaux', portal_key: 'leboncoinDirect', hektor_broadcast_id: '38' },
  { agence_nom: 'Groupe GTI Montbrison', portal_key: 'bienicidirect', hektor_broadcast_id: '7' },
  { agence_nom: 'Groupe GTI Montbrison', portal_key: 'leboncoinDirect', hektor_broadcast_id: '37' },
  { agence_nom: 'Groupe GTI Saint-Just-Saint-Rambert', portal_key: 'bienicidirect', hektor_broadcast_id: '8' },
  { agence_nom: 'Groupe GTI Saint-Just-Saint-Rambert', portal_key: 'leboncoinDirect', hektor_broadcast_id: '37' },
  { agence_nom: 'Groupe GTI Issoire', portal_key: 'bienicidirect', hektor_broadcast_id: '9' },
  { agence_nom: 'Groupe GTI Issoire', portal_key: 'leboncoinDirect', hektor_broadcast_id: '41' },
  { agence_nom: 'Groupe GTI Saint-Bonnet-le-Château', portal_key: 'bienicidirect', hektor_broadcast_id: '10' },
  { agence_nom: 'Groupe GTI Saint-Bonnet-le-Château', portal_key: 'leboncoinDirect', hektor_broadcast_id: '42' },
  { agence_nom: 'Groupe GTI COURPIERE', portal_key: 'bienicidirect', hektor_broadcast_id: '11' },
  { agence_nom: 'Groupe GTI COURPIERE', portal_key: 'leboncoinDirect', hektor_broadcast_id: '35' },
  { agence_nom: 'Groupe GTI Monistrol sur Loire', portal_key: 'bienicidirect', hektor_broadcast_id: '13' },
  { agence_nom: 'Groupe GTI Monistrol sur Loire', portal_key: 'leboncoinDirect', hektor_broadcast_id: '40' },
  { agence_nom: 'Groupe GTI Saint-Didier-en-Velay', portal_key: 'bienicidirect', hektor_broadcast_id: '14' },
  { agence_nom: 'Groupe GTI Saint-Didier-en-Velay', portal_key: 'leboncoinDirect', hektor_broadcast_id: '40' },
  { agence_nom: 'Groupe GTI Firminy', portal_key: 'bienicidirect', hektor_broadcast_id: '15' },
  { agence_nom: 'Groupe GTI Firminy', portal_key: 'leboncoinDirect', hektor_broadcast_id: '39' },
  { agence_nom: 'Groupe GTI Saint-Etienne', portal_key: 'bienicidirect', hektor_broadcast_id: '16' },
  { agence_nom: 'Groupe GTI Saint-Etienne', portal_key: 'leboncoinDirect', hektor_broadcast_id: '39' },
  { agence_nom: 'Groupe GTI Dunières', portal_key: 'bienicidirect', hektor_broadcast_id: '17' },
  { agence_nom: 'Groupe GTI Dunières', portal_key: 'leboncoinDirect', hektor_broadcast_id: '43' },
  { agence_nom: 'Groupe GTI Tence', portal_key: 'bienicidirect', hektor_broadcast_id: '22' },
  { agence_nom: 'Groupe GTI Tence', portal_key: 'leboncoinDirect', hektor_broadcast_id: '43' },
  { agence_nom: 'Groupe Gti Le Puy en Velay', portal_key: 'bienicidirect', hektor_broadcast_id: '23' },
  { agence_nom: 'Groupe Gti Le Puy en Velay', portal_key: 'leboncoinDirect', hektor_broadcast_id: '38' },
] as const

function displayCommercialLabel(value: { commercial_nom?: string | null; agence_nom?: string | null }) {
  return (value.commercial_nom ?? '').trim() || (value.agence_nom ?? '').trim()
}

function displayAgencyLabel(value: { agence_nom?: string | null }) {
  return (value.agence_nom ?? '').trim()
}

function quoteFilterLiteral(value: string) {
  return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
}

function normalizeEmail(value: string | null | undefined) {
  return (value ?? '').trim().toLowerCase()
}

function normalizeAgencyName(value: string | null | undefined) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ')
}

function normalizeScope(scope?: DataScope | null) {
  return {
    negotiatorEmail: normalizeEmail(scope?.negotiatorEmail),
  }
}

function filterByNegotiatorEmail<T extends { negociateur_email?: string | null }>(rows: T[], scope?: DataScope | null) {
  const { negotiatorEmail } = normalizeScope(scope)
  if (!negotiatorEmail) return rows
  return rows.filter((item) => normalizeEmail(item.negociateur_email) === negotiatorEmail)
}

function isMissingDiffusionTargetTableError(message: string | undefined) {
  const text = (message ?? '').toLowerCase()
  return text.includes('app_diffusion_target') && (text.includes('schema cache') || text.includes('could not find the table') || text.includes('does not exist'))
}

function isMissingDiffusionRequestEventTableError(message: string | undefined) {
  const text = (message ?? '').toLowerCase()
  return text.includes('app_diffusion_request_event') && (text.includes('schema cache') || text.includes('could not find the table') || text.includes('does not exist'))
}

function isMissingDiffusionAgencyTargetTableError(message: string | undefined) {
  const text = (message ?? '').toLowerCase()
  return text.includes('app_diffusion_agency_target') && (text.includes('schema cache') || text.includes('could not find the table') || text.includes('does not exist'))
}

export function canUseLocalDiffusionDevApi() {
  if (typeof window === 'undefined') return true
  const host = window.location.hostname.toLowerCase()
  return host === 'localhost' || host === '127.0.0.1'
}

function canUseBackendApi() {
  return !canUseLocalDiffusionDevApi() && Boolean(backendApiBaseUrl)
}

if (typeof window !== 'undefined') {
  ;(window as typeof window & { __gtiBackendDebug?: Record<string, unknown> }).__gtiBackendDebug = {
    host: window.location.hostname,
    backendApiBaseUrl,
    canUseLocalDiffusionDevApi: canUseLocalDiffusionDevApi(),
    canUseBackendApi: canUseBackendApi(),
  }
}

function assertBackendApiConfigured() {
  if (!canUseLocalDiffusionDevApi() && !backendApiBaseUrl) {
    throw new Error("Backend Python non configure en production. Verifie VITE_BACKEND_API_URL dans Vercel puis redeploie l'application.")
  }
}

function isInvalidDiffusionRequestEventIdTypeError(message: string | undefined) {
  const text = (message ?? '').toLowerCase()
  return text.includes('invalid input syntax for type bigint')
}

async function invokeSupabaseFunction<T>(name: string, body: Record<string, unknown>) {
  if (!supabase) {
    throw new Error('Supabase function is not available')
  }
  const currentSession = await supabase.auth.getSession()
  if (!currentSession.data.session) {
    throw new Error('Session Supabase introuvable')
  }

  const { data, error } = await supabase.functions.invoke(name, {
    body,
  })

  if (error) {
    if (error instanceof FunctionsHttpError) {
      const response = error.context
      const text = await response.text().catch(() => '')
      const payload = text
        ? (() => {
            try {
              return JSON.parse(text)
            } catch {
              return { error: text }
            }
          })()
        : {}
      throw new Error((payload as { error?: string })?.error ?? `Supabase function ${name} failed`)
    }
    if (error instanceof FunctionsRelayError || error instanceof FunctionsFetchError) {
      throw new Error(error.message || `Supabase function ${name} failed`)
    }
    throw new Error(`Supabase function ${name} failed`)
  }

  const payload = (data ?? {}) as { ok?: boolean; error?: string }
  if (payload?.ok === false) {
    throw new Error(payload.error ?? `Supabase function ${name} failed`)
  }
  return data as T
}

async function getFreshSupabaseAccessToken() {
  if (!supabase) {
    throw new Error('Supabase session is not available')
  }
  const currentSession = await supabase.auth.getSession()
  const accessToken = currentSession.data.session?.access_token ?? null
  if (!accessToken) {
    throw new Error('Session Supabase introuvable')
  }
  return accessToken
}

async function invokeBackendApi<T>(path: string, init?: { method?: 'GET' | 'POST'; body?: Record<string, unknown> }) {
  if (!backendApiBaseUrl) {
    throw new Error('Backend API is not configured')
  }
  const headers: Record<string, string> = {}
  if (hasSupabaseEnv && supabase) {
    const accessToken = await getFreshSupabaseAccessToken()
    headers.Authorization = `Bearer ${accessToken}`
  }
  if (init?.body) {
    headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(`${backendApiBaseUrl}${path}`, {
    method: init?.method ?? 'POST',
    headers,
    body: init?.body ? JSON.stringify(init.body) : undefined,
  })
  const text = await response.text().catch(() => '')
  const payload = text
    ? (() => {
        try {
          return JSON.parse(text)
        } catch {
          return { error: text }
        }
      })()
    : {}
  if (!response.ok || payload?.ok === false) {
    let message = `Backend API failed: ${path}`
    if (typeof payload === 'string' && payload.trim()) {
      message = payload.trim()
    } else if (payload && typeof payload === 'object') {
      const record = payload as Record<string, unknown>
      if (typeof record.detail === 'string' && record.detail.trim()) {
        message = record.detail.trim()
      } else if (record.detail && typeof record.detail === 'object') {
        const nested = record.detail as Record<string, unknown>
        if (typeof nested.error === 'string' && nested.error.trim()) {
          message = nested.error.trim()
        } else if (typeof nested.message === 'string' && nested.message.trim()) {
          message = nested.message.trim()
        } else {
          message = JSON.stringify(record.detail)
        }
      } else if (typeof record.error === 'string' && record.error.trim()) {
        message = record.error.trim()
      } else if (typeof record.message === 'string' && record.message.trim()) {
        message = record.message.trim()
      } else {
        message = JSON.stringify(payload)
      }
    }
    throw new Error(message)
  }
  return payload as T
}

export type DraftAnnonceSheetScanFieldKey =
  | 'title'
  | 'propertyType'
  | 'agency'
  | 'negotiatorName'
  | 'address'
  | 'postalCode'
  | 'city'
  | 'price'
  | 'netSellerPrice'
  | 'surface'
  | 'carrezSurface'
  | 'livingSurface'
  | 'roomCount'
  | 'bedroomCount'
  | 'bathroomCount'
  | 'showerRoomCount'
  | 'wcCount'
  | 'kitchen'
  | 'exposure'
  | 'view'
  | 'interiorState'
  | 'exteriorState'
  | 'landSurface'
  | 'terraceCount'
  | 'garageCount'
  | 'parkingInsideCount'
  | 'parkingOutsideCount'
  | 'constructionYear'
  | 'dpeValue'
  | 'gesValue'
  | 'coproLots'
  | 'coproCharges'
  | 'coproQuotePart'
  | 'coproWorksFund'
  | 'description'
  | 'note'
  | 'mandantCivility'
  | 'mandantLastName'
  | 'mandantFirstName'
  | 'mandantEmail'
  | 'mandantPhone'

export type DraftAnnonceSheetScanField = {
  value: string | null
  confidence: number | null
  rawText: string | null
}

export type DraftAnnonceSheetScanPayload = {
  model?: string | null
  summaryConfidence: number | null
  fields: Record<DraftAnnonceSheetScanFieldKey, DraftAnnonceSheetScanField>
  warnings: string[]
  missingFields: string[]
  rawNotes: string | null
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error ?? new Error('Lecture du fichier impossible'))
    reader.readAsDataURL(file)
  })
}

export async function scanDraftAnnonceSheet(file: File): Promise<DraftAnnonceSheetScanPayload> {
  if (!backendApiBaseUrl) {
    throw new Error('Backend Python non configure pour le scan OCR.')
  }
  if (!/^image\/(jpeg|jpg|png|webp)$/i.test(file.type)) {
    throw new Error('Choisis une photo JPG, PNG ou WebP.')
  }
  if (file.size > 12 * 1024 * 1024) {
    throw new Error('Photo trop lourde pour le scan OCR. Reprends une photo moins lourde.')
  }
  const accessToken = hasSupabaseEnv && supabase ? await getFreshSupabaseAccessToken() : null
  const imageBase64 = await readFileAsDataUrl(file)
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`
  const response = await fetch(`${backendApiBaseUrl}/annonces/scan-fiche`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      imageBase64,
      mimeType: file.type || null,
      filename: file.name || null,
      formVersion: 'draft_annonce_v1',
    }),
  })
  const text = await response.text().catch(() => '')
  const payload = text
    ? (() => {
        try {
          return JSON.parse(text)
        } catch {
          return { error: text }
        }
      })()
    : {}
  if (!response.ok || payload?.ok === false) {
    throw new Error(extractApiErrorMessage(payload) || 'Scan OCR impossible')
  }
  return (payload?.payload ?? payload) as DraftAnnonceSheetScanPayload
}

function extractApiErrorMessage(payload: unknown) {
  if (typeof payload === 'string' && payload.trim()) return payload.trim()
  if (!payload || typeof payload !== 'object') return ''
  const record = payload as Record<string, unknown>
  if (typeof record.detail === 'string' && record.detail.trim()) return record.detail.trim()
  if (record.detail && typeof record.detail === 'object') {
    const nested = record.detail as Record<string, unknown>
    if (typeof nested.error === 'string' && nested.error.trim()) return nested.error.trim()
    if (typeof nested.message === 'string' && nested.message.trim()) return nested.message.trim()
  }
  if (typeof record.error === 'string' && record.error.trim()) return record.error.trim()
  if (typeof record.message === 'string' && record.message.trim()) return record.message.trim()
  try {
    return JSON.stringify(payload)
  } catch {
    return ''
  }
}

function parseJsonObject(value: string | null | undefined) {
  if (!value) return {}
  try {
    const parsed = JSON.parse(value)
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {}
  } catch {
    return {}
  }
}

type MatterportGroupRow = Omit<MatterportGroup, 'models'> & {
  app_matterport_group_model?: MatterportModelLink[] | null
}

function normalizeMatterportGroups(rows: MatterportGroupRow[] | null | undefined): MatterportGroup[] {
  return (rows ?? [])
    .map((row) => ({
      id: row.id,
      hektor_annonce_id: row.hektor_annonce_id,
      numero_mandat: row.numero_mandat ?? null,
      group_label: row.group_label ?? null,
      group_state: row.group_state ?? null,
      group_visibility: row.group_visibility ?? null,
      match_status: row.match_status ?? null,
      is_validated: row.is_validated ?? null,
      synced_at: row.synced_at ?? null,
      models: (row.app_matterport_group_model ?? [])
        .slice()
        .sort((a, b) => (a.display_order ?? 999) - (b.display_order ?? 999) || String(a.matterport_name ?? '').localeCompare(String(b.matterport_name ?? ''), 'fr')),
    }))
    .sort((a, b) => String(a.numero_mandat ?? '').localeCompare(String(b.numero_mandat ?? ''), 'fr'))
}

async function loadMatterportGroupsForAnnonce(hektorAnnonceId: number | string | null | undefined) {
  if (!hasSupabaseEnv || !supabase || hektorAnnonceId == null) return []
  try {
    const { data, error } = await supabase
      .from('app_matterport_group')
      .select(`
        id,
        hektor_annonce_id,
        numero_mandat,
        group_label,
        group_state,
        group_visibility,
        match_status,
        is_validated,
        synced_at,
        app_matterport_group_model (
          id,
          matterport_model_id,
          matterport_url,
          matterport_name,
          matterport_internal_id,
          label,
          display_order,
          is_primary,
          state,
          visibility,
          created_at_matterport,
          modified_at_matterport
        )
      `)
      .eq('hektor_annonce_id', hektorAnnonceId)
      .order('numero_mandat', { ascending: true })
    if (error) return []
    return normalizeMatterportGroups(data as MatterportGroupRow[])
  } catch {
    return []
  }
}

function normalizeHektorApplyMessage(message: string | undefined) {
  return (message ?? '').replace(/Â/g, ' ').replace(/\s+/g, ' ').trim()
}

function isPendingHektorValidationMessage(message: string | undefined) {
  const text = normalizeHektorApplyMessage(message).toLowerCase()
  return (
    text.includes('unable to send listing') ||
    text.includes("n'a pas été validée") ||
    text.includes('na pas été validée') ||
    text.includes('responsable réseau') ||
    text.includes('responsable reseau')
  )
}

function uniqSorted(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.map((value) => (value ?? '').trim()).filter(Boolean))).sort((a, b) =>
    a.localeCompare(b, 'fr'),
  )
}

function normalizeFilterValue(value: string) {
  return value === allFilterValue ? '' : value
}

function normalizeBusinessState(value: string | null | undefined) {
  return (value ?? '').trim().toLowerCase()
}

function normalizeValidationState(value: string | null | undefined) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ')
}

function isValidationApproved(value: string | null | undefined) {
  const normalized = normalizeValidationState(value)
  return normalized === '1' || normalized === 'true' || normalized === 'oui' || normalized === 'valide' || normalized === 'validee' || normalized === 'validation ok' || normalized === 'validation_ok' || normalized === 'ok'
}

function hasMandatNumber(value: string | null | undefined) {
  return Boolean((value ?? '').trim())
}

function normalizeOfferPropositionType(value: string | null | undefined) {
  const state = normalizeBusinessState(value)
  if (state === 'accepted') return 'accepte'
  if (state === 'proposed') return 'proposition'
  if (state === 'refused' || state === 'cancelled') return 'refus'
  return state
}

function isCompromisCancelledState(value: string | null | undefined) {
  const state = normalizeBusinessState(value)
  return state === 'cancelled' || state === 'annule' || state === 'annulé' || state === 'annuled'
}

function getOfferLastPropositionType(item: { offre_last_proposition_type?: string | null; offre_state?: string | null }) {
  const derived = normalizeOfferPropositionType(item.offre_last_proposition_type)
  if (derived) return derived
  return normalizeOfferPropositionType(item.offre_state)
}

function hasOffreAchatEnCours(item: {
  offre_id?: string | number | null
  offre_last_proposition_type?: string | null
  offre_state?: string | null
  compromis_id?: string | number | null
  compromis_state?: string | null
}) {
  if (hasCompromisAnnule(item)) return false
  const lastType = getOfferLastPropositionType(item)
  return item.offre_id != null && (lastType === 'proposition' || lastType === 'accepte')
}

function hasOffreAchatRefusee(item: {
  offre_id?: string | number | null
  offre_last_proposition_type?: string | null
  offre_state?: string | null
  compromis_id?: string | number | null
  compromis_state?: string | null
}) {
  if (hasCompromisAnnule(item)) return false
  return item.offre_id != null && getOfferLastPropositionType(item) === 'refus'
}

function hasCompromisEnCours(item: { compromis_id?: string | number | null; compromis_state?: string | null }) {
  const hasCompromisState = Object.prototype.hasOwnProperty.call(item, 'compromis_state')
  return item.compromis_id != null && (hasCompromisState ? !isCompromisCancelledState(item.compromis_state) : true)
}

function hasCompromisAnnule(item: { compromis_id?: string | number | null; compromis_state?: string | null }) {
  const hasCompromisState = Object.prototype.hasOwnProperty.call(item, 'compromis_state')
  if (!hasCompromisState) return false
  return item.compromis_id != null && isCompromisCancelledState(item.compromis_state)
}

function hasAffaireEnCours(item: { offre_id?: string | number | null; offre_last_proposition_type?: string | null; offre_state?: string | null; compromis_id?: string | number | null; compromis_state?: string | null }) {
  return hasOffreAchatEnCours(item) || hasCompromisEnCours(item)
}

function hasAffaireAnnulee(item: { offre_id?: string | number | null; offre_last_proposition_type?: string | null; offre_state?: string | null; compromis_id?: string | number | null; compromis_state?: string | null }) {
  return hasOffreAchatRefusee(item) || hasCompromisAnnule(item)
}

function normalizeSearchTerm(value: string) {
  return value.trim().replace(/[%_,()]/g, ' ')
}

function normalizeListingSearchTerm(value: string) {
  const search = normalizeSearchTerm(value).replace(/\s+/g, ' ').trim()
  return search.length >= 3 ? search : ''
}

function listingSearchColumns(search: string) {
  return /^\d+$/.test(search) ? ['numero_dossier', 'numero_mandat', 'code_postal', 'search_text'] : ['search_text']
}

function matchesRequestScope(requestStatus: string | null | undefined, requestScope: string) {
  const status = normalizeBusinessState(requestStatus)
  if (!requestScope) return true
  if (requestScope === 'pending_or_in_progress') return status === 'pending' || status === 'in_progress'
  if (requestScope === 'waiting_correction') return status === 'waiting_commercial' || status === 'refused'
  if (requestScope === 'accepted') return status === 'accepted'
  if (requestScope === 'refused') return status === 'refused'
  return true
}

function matchesRequestType(requestType: string | null | undefined, filterValue: string) {
  const normalized = normalizeBusinessState(requestType)
  if (!filterValue) return true
  if (filterValue === 'demande_diffusion') return normalized === 'demande_diffusion' || normalized === ''
  if (filterValue === 'demande_baisse_prix') return normalized === 'demande_baisse_prix'
  if (filterValue === 'demande_annulation_mandat') return normalized === 'demande_annulation_mandat'
  return true
}

function buildLatestRequestRowsByDossierAndType<T extends { app_dossier_id: number; request_type?: string | null; requested_at?: string | null; created_at?: string | null }>(rows: T[]) {
  const latestByDossier = new Map<number, Map<string, T>>()
  for (const row of rows) {
    const normalizedType = normalizeBusinessState(row.request_type) || 'demande_diffusion'
    const byType = latestByDossier.get(row.app_dossier_id) ?? new Map<string, T>()
    const current = byType.get(normalizedType)
    const nextDate = new Date(row.requested_at ?? row.created_at ?? 0).getTime()
    const currentDate = current ? new Date(current.requested_at ?? current.created_at ?? 0).getTime() : 0
    if (!current || nextDate >= currentDate) byType.set(normalizedType, row)
    latestByDossier.set(row.app_dossier_id, byType)
  }
  return latestByDossier
}

function latestRequestRowsMatchScope(
  rows: Array<{ request_status: string | null; request_type?: string | null }>,
  requestScope: string,
  requestType: string,
) {
  const scopedRows = requestType ? rows.filter((row) => matchesRequestType(row.request_type ?? null, requestType)) : rows
  if (!requestScope && !requestType) return true
  if (scopedRows.length === 0) return false
  return scopedRows.some((row) => matchesRequestScope(row.request_status, requestScope))
}

function latestRequestRowsByDossierAndType<T extends { app_dossier_id: number; request_type?: string | null; requested_at?: string | null; created_at?: string | null }>(
  rows: T[],
  requestTypeFilter: string,
) {
  const normalizedFilter = normalizeFilterValue(requestTypeFilter)
  const latest = new Map<string, T>()
  for (const row of rows) {
    const normalizedType = normalizeBusinessState(row.request_type) || 'demande_diffusion'
    if (normalizedFilter && !matchesRequestType(row.request_type, normalizedFilter)) continue
    const key = normalizedFilter ? String(row.app_dossier_id) : `${row.app_dossier_id}:${normalizedType}`
    const current = latest.get(key)
    const nextDate = new Date(row.requested_at ?? row.created_at ?? 0).getTime()
    const currentDate = current ? new Date(current.requested_at ?? current.created_at ?? 0).getTime() : 0
    if (!current || nextDate >= currentDate) latest.set(key, row)
  }
  return Array.from(latest.values())
}

function latestAcceptedRequestRowsByDossierAndType<T extends { app_dossier_id: number; request_status?: string | null; request_type?: string | null; requested_at?: string | null; created_at?: string | null }>(
  rows: T[],
  requestTypeFilter: string,
) {
  return latestRequestRowsByDossierAndType(
    rows.filter((row) => normalizeBusinessState(row.request_status) === 'accepted'),
    requestTypeFilter,
  )
}

async function resolveRequestScopedDossierIds(filters: AppFilters, scope?: DataScope | null) {
  const requestScope = normalizeFilterValue(filters.requestScope)
  const requestType = normalizeFilterValue(filters.requestType)
  if (!requestScope && !requestType) return null

  if (!hasSupabaseEnv || !supabase) {
    const baseRows = applyLocalDossierFilters(filterByNegotiatorEmail(mockDossiers, scope), { ...filters, requestScope: allFilterValue })
    const latestByDossierAndType = buildLatestRequestRowsByDossierAndType(readLocalDiffusionRequests())
    return baseRows
      .filter((item) => {
        const latestRows = Array.from(latestByDossierAndType.get(item.app_dossier_id)?.values() ?? [])
        return latestRequestRowsMatchScope(latestRows, requestScope, requestType)
      })
      .map((item) => item.app_dossier_id)
  }

  const baseIds: number[] = []
  const batchSize = 1000
  let from = 0
  while (true) {
    const { data, error } = await applyDossierFiltersToQuery(
      applyNegotiatorScopeToQuery(
        supabase
          .from('app_dossiers_current')
          .select('app_dossier_id')
          .order('app_dossier_id', { ascending: true })
          .range(from, from + batchSize - 1),
        scope,
      ),
      { ...filters, requestScope: allFilterValue },
    )
    if (error || !data) throw new Error(error?.message ?? 'Unable to load request scoped dossiers')
    baseIds.push(...(data as Array<{ app_dossier_id: number }>).map((item) => item.app_dossier_id))
    if (data.length < batchSize) break
    from += batchSize
  }

  if (baseIds.length === 0) return []

  const requestRows: Array<{ app_dossier_id: number; request_status: string | null; request_type?: string | null; requested_at?: string | null; created_at?: string | null }> = []
  for (let index = 0; index < baseIds.length; index += 200) {
    const chunk = baseIds.slice(index, index + 200)
    const { data, error } = await supabase
      .from('app_diffusion_requests_current')
      .select('app_dossier_id,request_status,request_type,requested_at,created_at')
      .in('app_dossier_id', chunk)
    if (error || !data) throw new Error(error?.message ?? 'Unable to load request scoped statuses')
    requestRows.push(...(data as typeof requestRows))
  }

  const latestByDossierAndType = buildLatestRequestRowsByDossierAndType(requestRows)
  return baseIds.filter((appDossierId) => {
    const latestRows = Array.from(latestByDossierAndType.get(appDossierId)?.values() ?? [])
    return latestRequestRowsMatchScope(latestRows, requestScope, requestType)
  })
}

function hasActiveFilters(filters: AppFilters) {
  return Boolean(
    filters.query.trim() ||
      normalizeFilterValue(filters.commercial) ||
      normalizeFilterValue(filters.agency) ||
      filters.archive !== allFilterValue ||
      normalizeFilterValue(filters.detailAvailability) ||
      filters.mandat !== allFilterValue ||
      normalizeFilterValue(filters.affaire) ||
      normalizeFilterValue(filters.offreStatus) ||
      normalizeFilterValue(filters.compromisStatus) ||
      normalizeFilterValue(filters.requestScope) ||
      normalizeFilterValue(filters.requestType) ||
      normalizeFilterValue(filters.statut) ||
      normalizeFilterValue(filters.validationDiffusion) ||
      normalizeFilterValue(filters.diffusable) ||
      normalizeFilterValue(filters.passerelle) ||
      normalizeFilterValue(filters.erreurDiffusion) ||
      normalizeFilterValue(filters.priority) ||
      normalizeFilterValue(filters.workStatus) ||
      normalizeFilterValue(filters.internalStatus),
  )
}

function paginate<T>(rows: T[], page: number, pageSize: number): PageResult<T> {
  const total = rows.length
  const safePage = Math.max(1, page)
  const from = (safePage - 1) * pageSize
  return {
    rows: rows.slice(from, from + pageSize),
    total,
    page: safePage,
    pageSize,
  }
}

function readLocalDiffusionTargets(): DiffusionTarget[] {
  if (typeof window === 'undefined') return mockDiffusionTargets
  try {
    const raw = window.localStorage.getItem(localDiffusionTargetsKey)
    if (!raw) return mockDiffusionTargets
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as DiffusionTarget[]) : mockDiffusionTargets
  } catch {
    return mockDiffusionTargets
  }
}

function writeLocalDiffusionTargets(rows: DiffusionTarget[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(localDiffusionTargetsKey, JSON.stringify(rows))
}

function readLocalDiffusionRequests(): DiffusionRequest[] {
  if (typeof window === 'undefined') return mockDiffusionRequests
  try {
    const raw = window.localStorage.getItem(localDiffusionRequestsKey)
    if (!raw) return mockDiffusionRequests
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as DiffusionRequest[]) : mockDiffusionRequests
  } catch {
    return mockDiffusionRequests
  }
}

function writeLocalDiffusionRequests(rows: DiffusionRequest[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(localDiffusionRequestsKey, JSON.stringify(rows))
}

function readLocalDiffusionRequestEvents(): DiffusionRequestEvent[] {
  if (typeof window === 'undefined') return mockDiffusionRequestEvents
  try {
    const raw = window.localStorage.getItem(localDiffusionRequestEventsKey)
    if (!raw) return mockDiffusionRequestEvents
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as DiffusionRequestEvent[]) : mockDiffusionRequestEvents
  } catch {
    return mockDiffusionRequestEvents
  }
}

function writeLocalDiffusionRequestEvents(rows: DiffusionRequestEvent[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(localDiffusionRequestEventsKey, JSON.stringify(rows))
}

function buildDiffusionRequestEvent(input: {
  requestId: string
  eventType: string
  eventLabel: string
  actorUserId?: string | null
  actorName?: string | null
  actorRole?: string | null
  message?: string | null
}) {
  const now = new Date().toISOString()
  return {
    id: `event-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    diffusion_request_id: input.requestId,
    event_type: input.eventType,
    event_label: input.eventLabel,
    event_at: now,
    actor_user_id: input.actorUserId ?? null,
    actor_name: input.actorName ?? null,
    actor_role: input.actorRole ?? null,
    payload_json: input.message ? JSON.stringify({ message: input.message }) : null,
    created_at: now,
  } satisfies DiffusionRequestEvent
}

function applyLocalDossierFilters<T extends Dossier & { mandants_texte?: string | null }>(rows: T[], filters: AppFilters) {
  const query = normalizeListingSearchTerm(filters.query).toLowerCase()
  const mandatNumber = filters.mandatNumber.trim().toLowerCase()
  const mandantName = filters.mandantName.trim().toLowerCase()
  const commercial = normalizeFilterValue(filters.commercial)
  const agency = normalizeFilterValue(filters.agency)
  const archive = filters.archive
  const detailAvailability = normalizeFilterValue(filters.detailAvailability)
  const mandat = filters.mandat
  const affaire = normalizeFilterValue(filters.affaire)
  const offreStatus = normalizeFilterValue(filters.offreStatus)
  const compromisStatus = normalizeFilterValue(filters.compromisStatus)
  const requestScope = normalizeFilterValue(filters.requestScope)
  const requestType = normalizeFilterValue(filters.requestType)
  const statut = archive === archivedFilterValue ? '' : normalizeFilterValue(filters.statut)
  const validationDiffusion = normalizeFilterValue(filters.validationDiffusion)
  const diffusable = normalizeFilterValue(filters.diffusable)
  const passerelle = normalizeFilterValue(filters.passerelle)
  const erreurDiffusion = normalizeFilterValue(filters.erreurDiffusion)
  const priority = normalizeFilterValue(filters.priority)
  const latestByDossierAndType = requestScope || requestType ? buildLatestRequestRowsByDossierAndType(readLocalDiffusionRequests()) : null

  return rows.filter((item) => {
    const text = `${item.titre_bien} ${item.numero_dossier ?? ''} ${item.numero_mandat ?? ''} ${item.commercial_nom ?? ''} ${item.agence_nom ?? ''} ${item.ville ?? ''} ${item.code_postal ?? ''} ${item.mandants_texte ?? ''}`.toLowerCase()
    const isArchived = (item.archive ?? '0') === '1'
    const hasMandat = Boolean((item.numero_mandat ?? '').trim())
    const isDiffusable = (item.diffusable ?? '0') === '1'
    const hasErreurDiffusion = Boolean(item.has_diffusion_error)
    const portails = (item.portails_resume ?? '').split(',').map((value) => value.trim()).filter(Boolean)
    const hasAffaire =
      (affaire === 'offre_achat' && item.offre_id != null) ||
      (affaire === 'compromis' && item.compromis_id != null) ||
      !affaire
    return (
      (!query || text.includes(query)) &&
      (!mandatNumber || (item.numero_mandat ?? '').toLowerCase().includes(mandatNumber)) &&
      (!mandantName || (item.mandants_texte ?? '').toLowerCase().includes(mandantName)) &&
      (!commercial ||
        (commercial === withoutCommercialFilterValue
          ? !(item.commercial_nom ?? '').trim()
          : (item.commercial_nom ?? '').trim() === commercial)) &&
      (!agency || displayAgencyLabel(item) === agency) &&
      (archive === allFilterValue || (archive === archivedFilterValue ? isArchived : !isArchived)) &&
      (mandat === allFilterValue || (mandat === withMandatFilterValue ? hasMandat : !hasMandat)) &&
      hasAffaire &&
      (!offreStatus || (offreStatus === 'en_cours' ? hasOffreAchatEnCours(item) : hasOffreAchatRefusee(item))) &&
      (!compromisStatus || (compromisStatus === 'en_cours' ? hasCompromisEnCours(item) : hasCompromisAnnule(item))) &&
      (!(requestScope || requestType) || latestRequestRowsMatchScope(Array.from(latestByDossierAndType?.get(item.app_dossier_id)?.values() ?? []), requestScope, requestType)) &&
      (!statut ||
        (statut === activeListingsFilterValue
          ? activeListingStatuses.includes(item.statut_annonce ?? '')
          : statut === annonceSearchListingsFilterValue
            ? (item.statut_annonce ?? '') !== 'Estimation'
            : (item.statut_annonce ?? '') === statut)) &&
      (!validationDiffusion ||
        (validationDiffusion === '__validated__'
          ? isValidationApproved(item.validation_diffusion_state)
          : validationDiffusion === '__not_validated__'
            ? !isValidationApproved(item.validation_diffusion_state)
            : (item.validation_diffusion_state ?? '') === validationDiffusion)) &&
      (!diffusable || (diffusable === 'diffusable' ? isDiffusable : !isDiffusable)) &&
      (!passerelle || portails.includes(passerelle)) &&
      (!erreurDiffusion || (erreurDiffusion === 'avec_erreur' ? hasErreurDiffusion : !hasErreurDiffusion)) &&
      (!priority || (item.priority ?? '') === priority)
    )
  })
}

function applyLocalWorkItemFilters(rows: WorkItem[], filters: AppFilters) {
  const query = filters.query.trim().toLowerCase()
  const commercial = normalizeFilterValue(filters.commercial)
  const archive = filters.archive
  const mandat = filters.mandat
  const priority = normalizeFilterValue(filters.priority)
  const mandatNumber = normalizeSearchTerm(filters.mandatNumber)
  const mandantName = normalizeSearchTerm(filters.mandantName)
  const workStatus = normalizeFilterValue(filters.workStatus)
  const internalStatus = normalizeFilterValue(filters.internalStatus)
  const validationDiffusion = normalizeFilterValue(filters.validationDiffusion)

  return rows.filter((item) => {
    const text = `${item.titre_bien} ${item.numero_dossier ?? ''} ${item.numero_mandat ?? ''} ${item.commercial_nom ?? ''} ${item.type_demande_label ?? ''}`.toLowerCase()
    const isArchived = (item.archive ?? '0') === '1'
    const hasMandat = Boolean((item.numero_mandat ?? '').trim())
    return (
      (!query || text.includes(query)) &&
      (!commercial ||
        (commercial === withoutCommercialFilterValue
          ? !(item.commercial_nom ?? '').trim()
          : item.commercial_nom === commercial)) &&
      (archive === allFilterValue || (archive === archivedFilterValue ? isArchived : !isArchived)) &&
      (mandat === allFilterValue || (mandat === withMandatFilterValue ? hasMandat : !hasMandat)) &&
      (!validationDiffusion ||
        (validationDiffusion === '__validated__'
          ? isValidationApproved(item.validation_diffusion_state)
          : validationDiffusion === '__not_validated__'
            ? !isValidationApproved(item.validation_diffusion_state)
            : (item.validation_diffusion_state ?? '') === validationDiffusion)) &&
      (!priority || (item.priority ?? '') === priority) &&
      (!workStatus || (item.work_status ?? '') === workStatus) &&
      (!internalStatus || (item.internal_status ?? '') === internalStatus)
    )
  })
}

function applyDossierFiltersToQuery(baseQuery: any, filters: AppFilters) {
  let query = baseQuery
  const commercial = normalizeFilterValue(filters.commercial)
  const agency = normalizeFilterValue(filters.agency)
  const archive = filters.archive
  const detailAvailability = normalizeFilterValue(filters.detailAvailability)
  const mandat = filters.mandat
  const affaire = normalizeFilterValue(filters.affaire)
  const offreStatus = normalizeFilterValue(filters.offreStatus)
  const compromisStatus = normalizeFilterValue(filters.compromisStatus)
  const statut = archive === archivedFilterValue ? '' : normalizeFilterValue(filters.statut)
  const validationDiffusion = normalizeFilterValue(filters.validationDiffusion)
  const diffusable = normalizeFilterValue(filters.diffusable)
  const passerelle = normalizeFilterValue(filters.passerelle)
  const erreurDiffusion = normalizeFilterValue(filters.erreurDiffusion)
  const priority = normalizeFilterValue(filters.priority)
  const mandatNumber = normalizeSearchTerm(filters.mandatNumber)
  const mandantName = normalizeSearchTerm(filters.mandantName)

  if (commercial) {
    if (commercial === withoutCommercialFilterValue) {
      query = query.or('commercial_nom.is.null,commercial_nom.eq.')
    } else {
      const literal = quoteFilterLiteral(commercial)
      query = query.eq('commercial_nom', commercial).or(`commercial_nom.eq.${literal}`)
    }
  }
  if (agency) query = query.eq('agence_nom', agency)
  if (archive === activeArchiveFilterValue) query = query.eq('archive', '0')
  if (archive === archivedFilterValue) query = query.eq('archive', '1')
  if (detailAvailability === 'to_load') query = query.eq('app_dossier_id', -1)
  if (mandat === withMandatFilterValue) query = query.not('numero_mandat', 'is', null).neq('numero_mandat', '')
  if (mandat === withoutMandatFilterValue) query = query.or('numero_mandat.is.null,numero_mandat.eq.')
  if (affaire === 'offre_achat') query = query.not('offre_id', 'is', null)
  if (affaire === 'compromis') query = query.not('compromis_id', 'is', null)
  if (offreStatus === 'en_cours') {
    query = query.or(['and(offre_id.not.is.null,offre_last_proposition_type.eq.proposition)', 'and(offre_id.not.is.null,offre_last_proposition_type.eq.accepte)'].join(','))
    query = query.or(noCancelledCompromisQuery)
  }
  if (offreStatus === 'refusee') {
    query = query.or('and(offre_id.not.is.null,offre_last_proposition_type.eq.refus)')
    query = query.or(noCancelledCompromisQuery)
  }
  if (compromisStatus === 'en_cours') query = query.or('and(compromis_id.not.is.null,compromis_state.eq.active)')
  if (compromisStatus === 'annule') query = query.not('compromis_id', 'is', null).or(compromisCancelledQuery)
  if (statut === activeListingsFilterValue) query = query.in('statut_annonce', activeListingStatuses)
  else if (statut === annonceSearchListingsFilterValue) query = query.neq('statut_annonce', 'Estimation')
  else if (statut) query = query.eq('statut_annonce', statut)
  else query = query.neq('statut_annonce', 'Estimation')
  if (validationDiffusion === '__validated__') {
    query = query.or(
      [
        'validation_diffusion_state.eq.1',
        'validation_diffusion_state.eq.true',
        'validation_diffusion_state.eq.oui',
        'validation_diffusion_state.eq.valide',
        'validation_diffusion_state.eq.validee',
        'validation_diffusion_state.eq.validation ok',
        'validation_diffusion_state.eq.validation_ok',
        'validation_diffusion_state.eq.ok',
      ].join(','),
    )
  } else if (validationDiffusion === '__not_validated__') {
    query = query.or('validation_diffusion_state.is.null,validation_diffusion_state.eq.,validation_diffusion_state.not.in.("1","true","oui","valide","validee","validation ok","validation_ok","ok")')
  } else if (validationDiffusion) {
    query = query.eq('validation_diffusion_state', validationDiffusion)
  }
  if (diffusable === 'diffusable') query = query.eq('diffusable', '1')
  if (diffusable === 'non_diffusable') query = query.or('diffusable.is.null,diffusable.eq.0')
  if (passerelle) query = query.ilike('portails_resume', `%${passerelle}%`)
  if (erreurDiffusion === 'avec_erreur') query = query.eq('has_diffusion_error', true)
  if (erreurDiffusion === 'sans_erreur') query = query.or('has_diffusion_error.is.null,has_diffusion_error.eq.false,has_diffusion_error.eq.0')
  if (priority) query = query.eq('priority', priority)
  if (mandatNumber) query = query.ilike('numero_mandat', `%${mandatNumber}%`)
  if (mandantName) query = query.ilike('mandants_texte', `%${mandantName}%`)

  const search = normalizeListingSearchTerm(filters.query)
  if (search) {
    const ilike = `%${search}%`
    query = query.or(
      listingSearchColumns(search).map((column) => `${column}.ilike.${ilike}`).join(','),
    )
  }

  return query
}

function applyNegotiatorScopeToQuery(baseQuery: any, scope?: DataScope | null) {
  const { negotiatorEmail } = normalizeScope(scope)
  if (!negotiatorEmail) return baseQuery
  return baseQuery.eq('negociateur_email', negotiatorEmail)
}

function contactRoleFilterValues(role: string) {
  if (role === 'acquereur') return ['acquereur', 'acquereur_offre', 'acquereur_compromis', 'acquereur_vente']
  return [role]
}

function applyContactRoleFilter(baseQuery: any, role: string) {
  const roles = contactRoleFilterValues(role)
  if (roles.length === 1) return baseQuery.contains('relation_roles_json', JSON.stringify([roles[0]]))
  return baseQuery.or(roles.map((value) => `relation_roles_json.cs.${JSON.stringify([value])}`).join(','))
}

function applyContactFiltersToQuery(baseQuery: any, filters: AppFilters) {
  let query = baseQuery
  const search = normalizeSearchTerm(filters.query).replace(/\s+/g, ' ').trim()
  const commercial = normalizeFilterValue(filters.commercial)
  const agency = normalizeFilterValue(filters.agency)
  const archive = filters.archive
  const role = normalizeFilterValue(filters.contactRole)
  const contactSearchScope = normalizeFilterValue(filters.contactSearchScope)

  if (archive === activeArchiveFilterValue) query = query.eq('archive', false)
  if (archive === archivedFilterValue) query = query.eq('archive', true)
  if (commercial) {
    if (commercial === withoutCommercialFilterValue) query = query.or('commercial_nom.is.null,commercial_nom.eq.')
    else query = query.eq('commercial_nom', commercial)
  }
  if (agency) query = query.eq('agence_nom', agency)
  if (role) query = applyContactRoleFilter(query, role)
  if (contactSearchScope === activeContactSearchFilterValue) query = query.gt('active_search_count', 0)
  if (contactSearchScope === withContactSearchFilterValue) query = query.gt('total_search_count', 0)
  if (contactSearchScope === withoutContactSearchFilterValue) query = query.eq('total_search_count', 0)
  if (search.length >= 3) {
    const ilike = `%${search}%`
    query = /^\d+$/.test(search)
      ? query.or(`hektor_contact_id.eq.${search},search_text.ilike.${ilike}`)
      : query.ilike('search_text', ilike)
  }
  return query
}

function normalizeContactRow(row: AppContact): AppContact {
  return {
    ...row,
    linked_annonce_count: Number(row.linked_annonce_count ?? 0),
    active_search_count: Number(row.active_search_count ?? 0),
    total_search_count: Number(row.total_search_count ?? 0),
    has_contact_detail: row.has_contact_detail === true || row.has_contact_detail === 1 || row.has_contact_detail === '1',
    supabase_sync_eligible: row.supabase_sync_eligible === true || row.supabase_sync_eligible === 1 || row.supabase_sync_eligible === '1',
    duplicate_group_count: Number(row.duplicate_group_count ?? 0),
    completeness_score: Number(row.completeness_score ?? 0),
  }
}

function normalizeContactSearchRow(row: AppContactSearch): AppContactSearch {
  return {
    ...row,
    archive: row.archive === true || row.archive === 1 || row.archive === '1',
    is_active: row.is_active === true || row.is_active === 1 || row.is_active === '1',
    search_index: Number(row.search_index ?? 0),
  }
}

type LightweightAnnonceIndexRow = {
  hektor_annonce_id: number
  app_archive_id: number | null
  app_historical_id?: number | null
  numero_dossier: string | null
  numero_mandat: string | null
  titre_bien: string | null
  ville: string | null
  code_postal: string | null
  date_maj: string | null
  type_bien: string | null
  prix: number | null
  commercial_id: string | null
  commercial_nom: string | null
  negociateur_email: string | null
  agence_nom: string | null
  statut_annonce: string | null
  archive: string | null
  diffusable: string | null
  mandat_type: string | null
  mandat_date_debut: string | null
  mandat_date_fin: string | null
  mandat_montant: number | null
  mandants_texte: string | null
  has_local_detail: boolean | number | string | null
  local_detail_updated_at: string | null
}

type LightweightDetailCacheRow = {
  hektor_annonce_id: number | string
  expires_at: string | null
}

async function attachLightweightDetailCacheState<T extends Dossier>(
  rows: T[],
  cacheTable: 'app_archive_annonce_detail_cache' | 'app_historical_annonce_detail_cache',
): Promise<T[]> {
  if (!hasSupabaseEnv || !supabase || rows.length === 0) return rows
  const ids = Array.from(new Set(rows.map((row) => String(row.hektor_annonce_id)).filter(Boolean)))
  if (ids.length === 0) return rows
  const { data, error } = await supabase
    .from(cacheTable)
    .select('hektor_annonce_id,expires_at')
    .in('hektor_annonce_id', ids)
    .gt('expires_at', new Date().toISOString())
  if (error) throw new Error(error.message)
  const cacheByAnnonceId = new Map(
    ((data ?? []) as LightweightDetailCacheRow[]).map((row) => [String(row.hektor_annonce_id), row.expires_at ?? null]),
  )
  return rows.map((row) => {
    const expiresAt = cacheByAnnonceId.get(String(row.hektor_annonce_id)) ?? null
    return {
      ...row,
      has_detail_cache: Boolean(expiresAt),
      detail_cache_expires_at: expiresAt,
    }
  })
}

function lightweightIndexRowToDossier(row: LightweightAnnonceIndexRow): Dossier & { mandants_texte?: string | null } {
  return {
    app_dossier_id: Number(row.app_archive_id ?? row.app_historical_id ?? row.hektor_annonce_id),
    hektor_annonce_id: Number(row.hektor_annonce_id),
    photo_url_listing: null,
    images_preview_json: null,
    archive: row.archive ?? '1',
    diffusable: row.diffusable ?? null,
    nb_portails_actifs: 0,
    has_diffusion_error: false,
    portails_resume: null,
    offre_id: null,
    offre_state: null,
    offre_last_proposition_type: null,
    compromis_id: null,
    compromis_state: null,
    vente_id: null,
    numero_dossier: row.numero_dossier ?? null,
    numero_mandat: row.numero_mandat ?? null,
    titre_bien: row.titre_bien ?? '[Sans titre]',
    ville: row.ville ?? null,
    code_postal: row.code_postal ?? null,
    date_maj: row.date_maj ?? null,
    type_bien: row.type_bien ?? null,
    prix: row.prix ?? null,
    commercial_id: row.commercial_id ?? null,
    commercial_nom: row.commercial_nom ?? null,
    negociateur_email: row.negociateur_email ?? null,
    agence_nom: row.agence_nom ?? null,
    statut_annonce: row.statut_annonce ?? null,
    validation_diffusion_state: null,
    price_change_event_count: 0,
    price_change_last_source_kind: null,
    price_change_last_old_value: null,
    price_change_last_new_value: null,
    price_change_last_detected_at: null,
    price_change_last_source_updated_at: null,
    etat_visibilite: null,
    alerte_principale: null,
    priority: 'normal',
    has_open_blocker: false,
    commentaire_resume: null,
    date_relance_prevue: null,
    dernier_event_type: null,
    dernier_work_status: null,
    has_local_detail: row.has_local_detail,
    local_detail_updated_at: row.local_detail_updated_at ?? null,
    has_detail_cache: false,
    detail_cache_expires_at: null,
    mandants_texte: row.mandants_texte ?? null,
  }
}

function dossierToMandatRecord(row: Dossier & { mandants_texte?: string | null }): MandatRecord {
  return {
    ...row,
    archive: row.archive ?? null,
    diffusable: row.diffusable ?? null,
    nb_portails_actifs: row.nb_portails_actifs ?? 0,
    has_diffusion_error: Boolean(row.has_diffusion_error),
    portails_resume: row.portails_resume ?? null,
    agence_nom: row.agence_nom ?? null,
    validation_diffusion_state: row.validation_diffusion_state ?? null,
    mandat_type: null,
    mandat_date_debut: null,
    mandat_date_fin: null,
    mandat_montant: null,
    mandants_texte: row.mandants_texte ?? null,
    priority: row.priority ?? 'normal',
    offre_id: row.offre_id == null ? null : String(row.offre_id),
    compromis_id: row.compromis_id == null ? null : String(row.compromis_id),
    vente_id: row.vente_id == null ? null : String(row.vente_id),
    source_updated_at: null,
    refreshed_at: null,
    has_local_detail: row.has_local_detail ?? null,
    local_detail_updated_at: row.local_detail_updated_at ?? null,
    has_detail_cache: row.has_detail_cache ?? null,
    detail_cache_expires_at: row.detail_cache_expires_at ?? null,
  }
}

function applyArchiveIndexFiltersToQuery(baseQuery: any, filters: AppFilters, scope?: DataScope | null) {
  let query = applyNegotiatorScopeToQuery(baseQuery, scope)
  const commercial = normalizeFilterValue(filters.commercial)
  const agency = normalizeFilterValue(filters.agency)
  const mandat = filters.mandat
  const detailAvailability = normalizeFilterValue(filters.detailAvailability)
  const statut = normalizeFilterValue(filters.statut)
  const diffusable = normalizeFilterValue(filters.diffusable)
  const mandatNumber = normalizeSearchTerm(filters.mandatNumber)
  const mandantName = normalizeSearchTerm(filters.mandantName)

  if (commercial) {
    if (commercial === withoutCommercialFilterValue) {
      query = query.or('commercial_nom.is.null,commercial_nom.eq.')
    } else {
      query = query.eq('commercial_nom', commercial)
    }
  }
  if (agency) query = query.eq('agence_nom', agency)
  if (mandat === withMandatFilterValue) query = query.not('numero_mandat', 'is', null).neq('numero_mandat', '')
  if (mandat === withoutMandatFilterValue) query = query.or('numero_mandat.is.null,numero_mandat.eq.')
  if (detailAvailability === 'available') query = query.eq('has_local_detail', true)
  if (detailAvailability === 'to_load') query = query.or('has_local_detail.is.null,has_local_detail.eq.false,has_local_detail.eq.0')
  if (diffusable === 'diffusable') query = query.eq('diffusable', '1')
  if (diffusable === 'non_diffusable') query = query.or('diffusable.is.null,diffusable.eq.0')
  if (statut === activeListingsFilterValue) query = query.in('statut_annonce', activeListingStatuses)
  else if (statut === annonceSearchListingsFilterValue) query = query.neq('statut_annonce', 'Estimation')
  else if (statut) query = query.eq('statut_annonce', statut)
  else query = query.neq('statut_annonce', 'Estimation')
  if (mandatNumber) query = query.ilike('numero_mandat', `%${mandatNumber}%`)
  if (mandantName) query = query.ilike('mandants_texte', `%${mandantName}%`)

  const search = normalizeListingSearchTerm(filters.query)
  if (search) {
    const ilike = `%${search}%`
    query = query.or(
      listingSearchColumns(search).map((column) => `${column}.ilike.${ilike}`).join(','),
    )
  }

  return query
}

function canUseLightweightAnnonceIndexesForFilters(filters: AppFilters) {
  const affaire = normalizeFilterValue(filters.affaire)
  const offreStatus = normalizeFilterValue(filters.offreStatus)
  const compromisStatus = normalizeFilterValue(filters.compromisStatus)
  const validationDiffusion = normalizeFilterValue(filters.validationDiffusion)
  const passerelle = normalizeFilterValue(filters.passerelle)
  const erreurDiffusion = normalizeFilterValue(filters.erreurDiffusion)
  return (
    !affaire &&
    !offreStatus &&
    !compromisStatus &&
    !passerelle &&
    !erreurDiffusion &&
    (!validationDiffusion || validationDiffusion === '__not_validated__')
  )
}

function applyHistoricalIndexFiltersToQuery(baseQuery: any, filters: AppFilters, scope?: DataScope | null) {
  let query = applyArchiveIndexFiltersToQuery(baseQuery, filters, scope)
  const statut = normalizeFilterValue(filters.statut)
  if (historicalListingStatuses.includes(statut)) query = query.eq('statut_annonce', statut)
  return query
}

function dossierUpdatedAtValue(item: Dossier) {
  const raw = (item as Dossier & { source_updated_at?: string | null }).date_maj ?? (item as Dossier & { source_updated_at?: string | null }).source_updated_at ?? item.local_detail_updated_at
  if (!raw) return 0
  const parsed = new Date(raw).getTime()
  return Number.isFinite(parsed) ? parsed : 0
}

function mergeDossierPageResults(results: Array<PageResult<Dossier>>, page: number, pageSize: number): PageResult<Dossier> {
  const from = (page - 1) * pageSize
  const to = from + pageSize
  const rows = results
    .flatMap((result) => result.rows)
    .sort((a, b) => {
      const byDate = dossierUpdatedAtValue(b) - dossierUpdatedAtValue(a)
      if (byDate !== 0) return byDate
      return Number(b.hektor_annonce_id ?? 0) - Number(a.hektor_annonce_id ?? 0)
    })
    .slice(from, to)
  return {
    rows,
    total: results.reduce((sum, result) => sum + result.total, 0),
    page,
    pageSize,
  }
}

function applyWorkItemFiltersToQuery(baseQuery: any, filters: AppFilters) {
  let query = baseQuery
  const commercial = normalizeFilterValue(filters.commercial)
  const archive = filters.archive
  const mandat = filters.mandat
  const priority = normalizeFilterValue(filters.priority)
  const workStatus = normalizeFilterValue(filters.workStatus)
  const internalStatus = normalizeFilterValue(filters.internalStatus)
  const validationDiffusion = normalizeFilterValue(filters.validationDiffusion)

  if (commercial) {
    if (commercial === withoutCommercialFilterValue) query = query.or('commercial_nom.is.null,commercial_nom.eq.')
    else query = query.eq('commercial_nom', commercial)
  }
  if (archive === activeArchiveFilterValue) query = query.eq('archive', '0')
  if (archive === archivedFilterValue) query = query.eq('archive', '1')
  if (mandat === withMandatFilterValue) query = query.not('numero_mandat', 'is', null).neq('numero_mandat', '')
  if (mandat === withoutMandatFilterValue) query = query.or('numero_mandat.is.null,numero_mandat.eq.')
  if (validationDiffusion === '__validated__') {
    query = query.or(
      [
        'validation_diffusion_state.eq.oui',
        'validation_diffusion_state.eq.valide',
        'validation_diffusion_state.eq.validee',
        'validation_diffusion_state.eq.validation_ok',
        'validation_diffusion_state.eq.ok',
      ].join(','),
    )
  } else if (validationDiffusion === '__not_validated__') {
    query = query.not('validation_diffusion_state', 'in', '("oui","valide","validee","validation_ok","ok")')
  } else if (validationDiffusion) {
    query = query.eq('validation_diffusion_state', validationDiffusion)
  }
  if (priority) query = query.eq('priority', priority)
  if (workStatus) query = query.eq('work_status', workStatus)
  if (internalStatus) query = query.eq('internal_status', internalStatus)

  const search = normalizeSearchTerm(filters.query)
  if (search) {
    const ilike = `%${search}%`
    query = query.or(
      [
        `titre_bien.ilike.${ilike}`,
        `numero_dossier.ilike.${ilike}`,
        `numero_mandat.ilike.${ilike}`,
        `commercial_nom.ilike.${ilike}`,
        `type_demande_label.ilike.${ilike}`,
      ].join(','),
    )
  }

  return query
}

export async function loadDashboardSummary(): Promise<DashboardSummary> {
  if (!hasSupabaseEnv || !supabase) return mockSummary
  const { data, error } = await supabase.from('app_dashboard_v1').select('*').single()
  if (error || !data) throw new Error(error?.message ?? 'Unable to load dashboard summary')
  return data as DashboardSummary
}

type ContactStatsSnapshotRow = {
  total?: number | string | null
  active?: number | string | null
  archived?: number | string | null
  duplicates?: number | string | null
  high_risk_duplicates?: number | string | null
  linked?: number | string | null
  search_contacts?: number | string | null
  active_search_contacts?: number | string | null
  eligible?: number | string | null
}

function emptyContactStats(): ContactStats {
  return { total: 0, active: 0, archived: 0, duplicates: 0, highRiskDuplicates: 0, linked: 0, searchContacts: 0, activeSearchContacts: 0, eligible: 0 }
}

function contactStatsNumber(value: number | string | null | undefined) {
  const parsed = Number(value ?? 0)
  return Number.isFinite(parsed) ? parsed : 0
}

function contactStatsFromSnapshot(row: ContactStatsSnapshotRow): ContactStats {
  return {
    total: contactStatsNumber(row.total),
    active: contactStatsNumber(row.active),
    archived: contactStatsNumber(row.archived),
    duplicates: contactStatsNumber(row.duplicates),
    highRiskDuplicates: contactStatsNumber(row.high_risk_duplicates),
    linked: contactStatsNumber(row.linked),
    searchContacts: contactStatsNumber(row.search_contacts),
    activeSearchContacts: contactStatsNumber(row.active_search_contacts),
    eligible: contactStatsNumber(row.eligible),
  }
}

function canUseContactStatsSnapshot(filters: AppFilters) {
  return (
    normalizeSearchTerm(filters.query).replace(/\s+/g, ' ').trim().length === 0 &&
    !normalizeFilterValue(filters.commercial) &&
    !normalizeFilterValue(filters.agency) &&
    !normalizeFilterValue(filters.contactRole) &&
    !normalizeFilterValue(filters.contactSearchScope)
  )
}

async function loadContactStatsSnapshot(): Promise<ContactStats | null> {
  if (!hasSupabaseEnv || !supabase) return null
  const { data, error } = await supabase
    .from(contactStatsCurrentTable)
    .select('total,active,archived,duplicates,high_risk_duplicates,linked,search_contacts,active_search_contacts,eligible')
    .eq('scope', 'active_or_eligible')
    .maybeSingle()
  if (error || !data) return null
  return contactStatsFromSnapshot(data as ContactStatsSnapshotRow)
}

function contactSummaryTotalForFilters(filters: AppFilters, stats: ContactStats | null) {
  if (!stats || !canUseContactStatsSnapshot(filters)) return null
  if (filters.archive === activeArchiveFilterValue) return stats.active
  if (filters.archive === archivedFilterValue) return stats.archived
  if (filters.archive === allFilterValue) return stats.total
  return null
}

export async function loadContactsPage({
  filters,
  page,
  pageSize,
}: {
  filters: AppFilters
  page: number
  pageSize: number
  scope?: DataScope | null
}): Promise<PageResult<AppContact>> {
  if (!hasSupabaseEnv || !supabase) return { rows: [], total: 0, page, pageSize }

  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  // Contacts is a high-volume listing; exact counts can hit Supabase statement timeout under RLS.
  const countMode: 'planned' = 'planned'
  const statsSnapshot = canUseContactStatsSnapshot(filters) ? await loadContactStatsSnapshot() : null
  const { data, error, count } = await applyContactFiltersToQuery(
    supabase
      .from(contactsCurrentView)
      .select(contactsListingSelect, { count: countMode }),
    filters,
  )
    .order('duplicate_group_count', { ascending: false, nullsFirst: false })
    .order('date_maj', { ascending: false, nullsFirst: false })
    .order('display_name', { ascending: true })
    .range(from, to)

  if (error || !data) throw new Error(error?.message ?? 'Unable to load contacts')
  const minimumTotal = from + data.length + (data.length === pageSize ? 1 : 0)
  const exactSummaryTotal = contactSummaryTotalForFilters(filters, statsSnapshot)
  return {
    rows: (data as AppContact[]).map(normalizeContactRow),
    total: Math.max(exactSummaryTotal ?? count ?? 0, minimumTotal),
    page,
    pageSize,
  }
}

async function countContacts(filters: AppFilters, patch: Partial<AppFilters> = {}, extra?: (query: any) => any) {
  if (!hasSupabaseEnv || !supabase) return 0
  let query = applyContactFiltersToQuery(
    supabase.from(contactsCurrentView).select('hektor_contact_id', { count: 'planned', head: true }),
    { ...filters, ...patch },
  )
  if (extra) query = extra(query)
  const { error, count } = await query
  if (error) throw new Error(error.message)
  return count ?? 0
}

export async function loadContactStats(filters: AppFilters): Promise<ContactStats> {
  if (!hasSupabaseEnv || !supabase) return emptyContactStats()
  const snapshot = canUseContactStatsSnapshot(filters) ? await loadContactStatsSnapshot() : null
  if (snapshot) return snapshot
  const baseFilters = { ...filters, archive: allFilterValue }
  const [total, active, archived, duplicates, highRiskDuplicates, linked, searchContacts, activeSearchContacts, eligible] = await Promise.all([
    countContacts(baseFilters),
    countContacts(baseFilters, { archive: activeArchiveFilterValue }),
    countContacts(baseFilters, { archive: archivedFilterValue }),
    countContacts(baseFilters, {}, (query) => query.gt('duplicate_group_count', 0)),
    countContacts(baseFilters, {}, (query) => query.in('duplicate_max_severity', ['high', 'critical'])),
    countContacts(baseFilters, {}, (query) => query.gt('linked_annonce_count', 0)),
    countContacts(baseFilters, {}, (query) => query.gt('total_search_count', 0)),
    countContacts(baseFilters, {}, (query) => query.gt('active_search_count', 0)),
    countContacts(baseFilters, {}, (query) => query.eq('supabase_sync_eligible', true)),
  ])
  return { total, active, archived, duplicates, highRiskDuplicates, linked, searchContacts, activeSearchContacts, eligible }
}

export async function loadContactRelations(contactId: string): Promise<AppContactRelation[]> {
  if (!hasSupabaseEnv || !supabase || !contactId.trim()) return []
  const { data, error } = await supabase
    .from(contactRelationsCurrentView)
    .select('*')
    .eq('hektor_contact_id', contactId.trim())
    .order('last_seen_at', { ascending: false, nullsFirst: false })
  if (error || !data) throw new Error(error?.message ?? 'Unable to load contact relations')
  return data as AppContactRelation[]
}

export async function loadContactSearches(contactId: string): Promise<AppContactSearch[]> {
  if (!hasSupabaseEnv || !supabase || !contactId.trim()) return []
  const { data, error } = await supabase
    .from(contactSearchesCurrentView)
    .select('*')
    .eq('hektor_contact_id', contactId.trim())
    .order('is_active', { ascending: false, nullsFirst: false })
    .order('contact_date_maj', { ascending: false, nullsFirst: false })
    .order('search_index', { ascending: true })
  if (error || !data) throw new Error(error?.message ?? 'Unable to load contact searches')
  return (data as AppContactSearch[]).map(normalizeContactSearchRow)
}

export async function loadDossiersPage({
  filters,
  page,
  pageSize,
  scope,
}: {
  filters: AppFilters
  page: number
  pageSize: number
  scope?: DataScope | null
}): Promise<PageResult<Dossier>> {
  if (!hasSupabaseEnv || !supabase) {
    return paginate(applyLocalDossierFilters(filterByNegotiatorEmail(mockDossiers, scope), filters), page, pageSize)
  }

  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  const countMode: 'exact' = 'exact'
  const statut = normalizeFilterValue(filters.statut)
  const requestScope = normalizeFilterValue(filters.requestScope)
  const requestType = normalizeFilterValue(filters.requestType)
  const canUseLightweightIndexes = !requestScope && !requestType && canUseLightweightAnnonceIndexesForFilters(filters)
  const archiveIndexSelect = 'hektor_annonce_id,app_archive_id,numero_dossier,numero_mandat,titre_bien,ville,code_postal,date_maj,type_bien,prix,commercial_id,commercial_nom,negociateur_email,agence_nom,statut_annonce,archive,diffusable,mandat_type,mandat_date_debut,mandat_date_fin,mandat_montant,mandants_texte,has_local_detail,local_detail_updated_at'
  const historicalIndexSelect = 'hektor_annonce_id,app_historical_id,numero_dossier,numero_mandat,titre_bien,ville,code_postal,date_maj,type_bien,prix,commercial_id,commercial_nom,negociateur_email,agence_nom,statut_annonce,archive,diffusable,mandat_type,mandat_date_debut,mandat_date_fin,mandat_montant,mandants_texte,has_local_detail,local_detail_updated_at'
  if (filters.archive === archivedFilterValue) {
    if (!canUseLightweightIndexes) {
      return { rows: [], total: 0, page, pageSize }
    }
    const archiveQuery = applyArchiveIndexFiltersToQuery(
      supabase
        .from('app_archive_annonce_index_current')
        .select(archiveIndexSelect, { count: countMode }),
      filters,
      scope,
    )
      .order('date_maj', { ascending: false, nullsFirst: false })
      .order('hektor_annonce_id', { ascending: false })
      .range(from, to)

    const { data, error, count } = await archiveQuery
    if (error || !data) throw new Error(error?.message ?? 'Unable to load archived annonces')
    const rows = await attachLightweightDetailCacheState(
      (data as LightweightAnnonceIndexRow[]).map(lightweightIndexRowToDossier),
      'app_archive_annonce_detail_cache',
    )
    return {
      rows,
      total: count ?? 0,
      page,
      pageSize,
    }
  }
  if (historicalListingStatuses.includes(statut)) {
    if (!canUseLightweightIndexes) {
      return { rows: [], total: 0, page, pageSize }
    }
    const historicalRangeFrom = filters.archive === allFilterValue ? 0 : from
    const historicalRangeTo = to
    const historicalQuery = applyHistoricalIndexFiltersToQuery(
      supabase
        .from('app_historical_annonce_index_current')
        .select(historicalIndexSelect, { count: countMode }),
      filters,
      scope,
    )
      .order('date_maj', { ascending: false, nullsFirst: false })
      .order('hektor_annonce_id', { ascending: false })
      .range(historicalRangeFrom, historicalRangeTo)

    const { data, error, count } = await historicalQuery
    if (error || !data) throw new Error(error?.message ?? 'Unable to load historical annonces')
    const historicalResult: PageResult<Dossier> = {
      rows: await attachLightweightDetailCacheState(
        (data as LightweightAnnonceIndexRow[]).map(lightweightIndexRowToDossier),
        'app_historical_annonce_detail_cache',
      ),
      total: count ?? 0,
      page,
      pageSize,
    }
    if (filters.archive === allFilterValue) {
      const archiveQuery = applyArchiveIndexFiltersToQuery(
        supabase
          .from('app_archive_annonce_index_current')
          .select(archiveIndexSelect, { count: countMode }),
        filters,
        scope,
      )
        .order('date_maj', { ascending: false, nullsFirst: false })
        .order('hektor_annonce_id', { ascending: false })
        .range(0, historicalRangeTo)

      const { data: archiveData, error: archiveError, count: archiveCount } = await archiveQuery
      if (archiveError || !archiveData) throw new Error(archiveError?.message ?? 'Unable to load archived historical annonces')
      return mergeDossierPageResults([
        historicalResult,
        {
          rows: await attachLightweightDetailCacheState(
            (archiveData as LightweightAnnonceIndexRow[]).map(lightweightIndexRowToDossier),
            'app_archive_annonce_detail_cache',
          ),
          total: archiveCount ?? 0,
          page,
          pageSize,
        },
      ], page, pageSize)
    }
    return {
      rows: historicalResult.rows,
      total: historicalResult.total,
      page,
      pageSize,
    }
  }

  const requestScopedIds = await resolveRequestScopedDossierIds(filters, scope)
  let query = applyDossierFiltersToQuery(
    applyNegotiatorScopeToQuery(supabase.from(dossiersCurrentView).select('*', { count: countMode }), scope),
    filters,
  )
    .order('has_open_blocker', { ascending: false })
    .order('priority', { ascending: true })
    .order('app_dossier_id', { ascending: true })
  if (requestScopedIds) {
    query = requestScopedIds.length > 0 ? query.in('app_dossier_id', requestScopedIds) : query.eq('app_dossier_id', -1)
  }
  const shouldMergeArchiveIndex = filters.archive === allFilterValue && canUseLightweightIndexes
  const shouldMergeHistoricalIndex =
    canUseLightweightIndexes &&
    (filters.archive === allFilterValue || filters.archive === activeArchiveFilterValue) &&
    (!statut || statut === annonceSearchListingsFilterValue)
  const shouldMergeLightweightIndexes = shouldMergeArchiveIndex || shouldMergeHistoricalIndex
  query = query.range(shouldMergeLightweightIndexes ? 0 : from, to)

  const { data, error, count } = await query
  if (error || !data) throw new Error(error?.message ?? 'Unable to load dossiers')
  const primaryResult: PageResult<Dossier> = {
    rows: data as Dossier[],
    total: count ?? 0,
    page,
    pageSize,
  }
  if (shouldMergeLightweightIndexes) {
    const mixedRangeTo = to
    const mergedResults: Array<PageResult<Dossier>> = [primaryResult]
    if (shouldMergeArchiveIndex) {
      const archiveQuery = applyArchiveIndexFiltersToQuery(
        supabase
          .from('app_archive_annonce_index_current')
          .select(archiveIndexSelect, { count: countMode }),
        filters,
        scope,
      )
        .order('date_maj', { ascending: false, nullsFirst: false })
        .order('hektor_annonce_id', { ascending: false })
        .range(0, mixedRangeTo)

      const { data: archiveData, error: archiveError, count: archiveCount } = await archiveQuery
      if (archiveError || !archiveData) throw new Error(archiveError?.message ?? 'Unable to load archived annonces')
      mergedResults.push({
        rows: await attachLightweightDetailCacheState(
          (archiveData as LightweightAnnonceIndexRow[]).map(lightweightIndexRowToDossier),
          'app_archive_annonce_detail_cache',
        ),
        total: archiveCount ?? 0,
        page,
        pageSize,
      })
    }
    if (shouldMergeHistoricalIndex) {
      const historicalQuery = applyHistoricalIndexFiltersToQuery(
        supabase
          .from('app_historical_annonce_index_current')
          .select(historicalIndexSelect, { count: countMode }),
        filters,
        scope,
      )
        .order('date_maj', { ascending: false, nullsFirst: false })
        .order('hektor_annonce_id', { ascending: false })
        .range(0, mixedRangeTo)

      const { data: historicalData, error: historicalError, count: historicalCount } = await historicalQuery
      if (historicalError || !historicalData) throw new Error(historicalError?.message ?? 'Unable to load historical annonces')
      mergedResults.push({
        rows: await attachLightweightDetailCacheState(
          (historicalData as LightweightAnnonceIndexRow[]).map(lightweightIndexRowToDossier),
          'app_historical_annonce_detail_cache',
        ),
        total: historicalCount ?? 0,
        page,
        pageSize,
      })
    }
    return mergeDossierPageResults(mergedResults, page, pageSize)
  }
  return primaryResult
}

export async function loadWorkItemsPage({
  filters,
  page,
  pageSize,
  scope,
}: {
  filters: AppFilters
  page: number
  pageSize: number
  scope?: DataScope | null
}): Promise<PageResult<WorkItem>> {
  if (!hasSupabaseEnv || !supabase) {
    return paginate(applyLocalWorkItemFilters(filterByNegotiatorEmail(mockWorkItems, scope), filters), page, pageSize)
  }

  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  const countMode: 'planned' = 'planned'
  const query = applyWorkItemFiltersToQuery(
    supabase
      .from('app_work_items_current')
      .select('app_dossier_id,hektor_annonce_id,archive,numero_dossier,numero_mandat,titre_bien,commercial_nom,type_demande_label,work_status,internal_status,priority,validation_diffusion_state,etat_visibilite,motif_blocage,has_open_blocker,next_action,date_relance_prevue,date_entree_file,date_derniere_action,age_jours', { count: countMode }),
    filters,
  )
    .order('has_open_blocker', { ascending: false })
    .order('priority', { ascending: true })
    .order('date_entree_file', { ascending: false })
    .range(from, to)

  const { data, error, count } = await query
  if (error || !data) throw new Error(error?.message ?? 'Unable to load work items')
  return {
    rows: data as WorkItem[],
    total: count ?? 0,
    page,
    pageSize,
  }
}

export async function loadDossierDetail(appDossierId: number): Promise<DetailedDossier | null> {
  if (!hasSupabaseEnv || !supabase) {
    const dossier = mockDossiers.find((item) => item.app_dossier_id === appDossierId)
    return dossier ? { ...dossier, detail_payload_json: null } : null
  }

  const { data: dossierData, error: dossierError } = await supabase
    .from(dossiersCurrentView)
    .select('*')
    .eq('app_dossier_id', appDossierId)
    .maybeSingle()

  if (dossierError) throw new Error(dossierError.message)
  if (!dossierData) return null

  const { data: detailData, error: detailError } = await supabase
    .from('app_dossier_details_current')
    .select('app_dossier_id,hektor_annonce_id,detail_payload_json')
    .eq('app_dossier_id', appDossierId)
    .maybeSingle()

  if (detailError && detailError.code !== 'PGRST116') throw new Error(detailError.message)

  const detailPayload = parseJsonObject((detailData as DossierDetail | null)?.detail_payload_json ?? null)

  detailPayload.matterport_groups_json = JSON.stringify(await loadMatterportGroupsForAnnonce(dossierData.hektor_annonce_id))

  if (canUseBackendApi()) {
    try {
      const appointmentSummary = await invokeBackendApi<AppointmentSummaryResponse>(`/public/appointments/annonce/${encodeURIComponent(String(dossierData.hektor_annonce_id))}/summary`, {
        method: 'GET',
      })
      const context = appointmentSummary.context ?? {}
      detailPayload.appointment_public_token = context.token ?? detailPayload.appointment_public_token ?? null
      detailPayload.appointment_public_url = context.publicUrl ?? detailPayload.appointment_public_url ?? null
      detailPayload.appointment_negociateur_id = context.commercialId ?? detailPayload.appointment_negociateur_id ?? null
      detailPayload.appointment_negociateur_email = context.negociateurEmail ?? detailPayload.appointment_negociateur_email ?? null
      detailPayload.appointment_requests_json = JSON.stringify(Array.isArray(appointmentSummary.requests) ? appointmentSummary.requests : [])
      detailPayload.appointment_request_events_json = JSON.stringify(Array.isArray(appointmentSummary.events) ? appointmentSummary.events : [])
    } catch {
      // Ne bloque pas la fiche annonce si le module RDV n'est pas encore joignable.
    }
  }

  return {
    ...(dossierData as Dossier),
    detail_payload_json: JSON.stringify(detailPayload),
  }
}

function stringifyJsonPayloadFields(source: Record<string, unknown>) {
  const result: Record<string, unknown> = { ...source }
  for (const [key, value] of Object.entries(result)) {
    if (!key.endsWith('_json')) continue
    if (value == null || typeof value === 'string') continue
    result[key] = JSON.stringify(value)
  }
  return result
}

async function loadLightweightAnnonceDetailCache(
  table: 'app_archive_annonce_detail_cache' | 'app_historical_annonce_detail_cache',
  indexTable: 'app_archive_annonce_index_current' | 'app_historical_annonce_index_current',
  payloadIdKey: 'app_archive_id' | 'app_historical_id',
  indexIdKey: 'app_archive_id' | 'app_historical_id',
  defaultArchive: '0' | '1',
  hektorAnnonceId: number | string,
): Promise<DetailedDossier | null> {
  if (!hasSupabaseEnv || !supabase) return null
  const cleanId = String(hektorAnnonceId).trim()
  if (!cleanId) return null

  const { data, error } = await supabase
    .from(table)
    .select('detail_payload_json,expires_at')
    .eq('hektor_annonce_id', cleanId)
    .maybeSingle()

  if (error && error.code !== 'PGRST116') throw new Error(error.message)
  if (!data) return null

  const expiresAt = typeof data.expires_at === 'string' ? new Date(data.expires_at).getTime() : 0
  if (expiresAt && expiresAt < Date.now()) return null

  const payload = typeof data.detail_payload_json === 'string'
    ? parseJsonObject(data.detail_payload_json)
    : ((data.detail_payload_json ?? {}) as Record<string, unknown>)
  const listing = (payload.listing && typeof payload.listing === 'object' ? payload.listing : {}) as Record<string, unknown>
  const payloadIndex = (payload.index && typeof payload.index === 'object' ? payload.index : {}) as Record<string, unknown>
  let currentIndex: Record<string, unknown> = {}
  const indexSelect = `hektor_annonce_id,${indexIdKey},numero_dossier,numero_mandat,titre_bien,ville,code_postal,date_maj,type_bien,prix,commercial_id,commercial_nom,negociateur_email,agence_nom,statut_annonce,archive,diffusable,mandat_type,mandat_date_debut,mandat_date_fin,mandat_montant,mandants_texte,has_local_detail,local_detail_updated_at`
  const { data: indexData, error: indexError } = await supabase
    .from(indexTable)
    .select(indexSelect)
    .eq('hektor_annonce_id', cleanId)
    .maybeSingle()
  if (indexError && indexError.code !== 'PGRST116') throw new Error(indexError.message)
  if (indexData && typeof indexData === 'object') currentIndex = indexData as Record<string, unknown>
  const index = { ...payloadIndex, ...currentIndex }
  const rawDetail = (payload.detail && typeof payload.detail === 'object' ? payload.detail : {}) as Record<string, unknown>
  const detail = stringifyJsonPayloadFields({ ...index, ...listing, ...rawDetail })
  const detailRaw = parseJsonObject((detail.detail_raw_json ?? detail.raw_json ?? null) as string | null)
  if (!detail.detail_raw_json && detail.raw_json) detail.detail_raw_json = detail.raw_json
  if (!detail.surface && (index.surface || listing.surface)) detail.surface = index.surface ?? listing.surface
  if (!detail.surface_habitable_detail) {
    detail.surface_habitable_detail = index.surface_habitable_detail
      ?? (((detailRaw.ag_interieur as Record<string, unknown> | undefined)?.props as Record<string, { value?: unknown }> | undefined)?.surfappart?.value)
      ?? detail.surface
  }
  if (!detail.surface_terrain_detail) {
    detail.surface_terrain_detail = index.surface_terrain_detail
      ?? (((detailRaw.terrain as Record<string, unknown> | undefined)?.props as Record<string, { value?: unknown }> | undefined)?.surfterrain?.value)
  }
  if (!detail.nb_pieces) {
    detail.nb_pieces = index.nb_pieces
      ?? (((detailRaw.ag_interieur as Record<string, unknown> | undefined)?.props as Record<string, { value?: unknown }> | undefined)?.nbpieces?.value)
  }
  if (!detail.nb_chambres) {
    detail.nb_chambres = index.nb_chambres
      ?? (((detailRaw.ag_interieur as Record<string, unknown> | undefined)?.props as Record<string, { value?: unknown }> | undefined)?.NB_CHAMBRES?.value)
  }
  let textBlocks: Array<Record<string, unknown>> = []
  if (typeof detail.textes_json === 'string') {
    try {
      const parsed = JSON.parse(detail.textes_json)
      if (Array.isArray(parsed)) textBlocks = parsed as Array<Record<string, unknown>>
    } catch {
      textBlocks = []
    }
  }
  const firstText = textBlocks.find((item: Record<string, unknown>) => item && (item.html || item.text))
  if (!detail.texte_principal_titre && firstText?.titre) detail.texte_principal_titre = firstText.titre
  if (!detail.texte_principal_html && firstText) detail.texte_principal_html = firstText.html ?? firstText.text
  detail.matterport_groups_json = JSON.stringify(await loadMatterportGroupsForAnnonce(hektorAnnonceId))
  const appDossierId = Number(index.app_dossier_id ?? index[indexIdKey] ?? payload[payloadIdKey] ?? listing.hektor_annonce_id ?? hektorAnnonceId)
  const priceValue = index.prix ?? listing.prix
  const dossier: DetailedDossier = {
    app_dossier_id: Number.isFinite(appDossierId) ? appDossierId : Number(hektorAnnonceId),
    hektor_annonce_id: Number(hektorAnnonceId),
    photo_url_listing: (detail.photo_url_listing ?? index.photo_url_listing ?? listing.photo ?? null) as string | null,
    images_preview_json: (detail.images_preview_json ?? index.images_preview_json ?? null) as string | null,
    archive: String(index.archive ?? listing.archive ?? defaultArchive),
    diffusable: index.diffusable == null ? (listing.diffusable == null ? null : String(listing.diffusable)) : String(index.diffusable),
    nb_portails_actifs: Number(index.nb_portails_actifs ?? 0),
    has_diffusion_error: Boolean(index.has_diffusion_error ?? false),
    portails_resume: (index.portails_resume ?? null) as string | null,
    offre_id: (index.offre_id ?? null) as string | number | null,
    offre_state: (index.offre_state ?? null) as string | null,
    offre_last_proposition_type: (index.offre_last_proposition_type ?? null) as string | null,
    compromis_id: (index.compromis_id ?? null) as string | number | null,
    compromis_state: (index.compromis_state ?? null) as string | null,
    vente_id: (index.vente_id ?? null) as string | number | null,
    numero_dossier: (index.numero_dossier ?? listing.numero_dossier ?? listing.no_dossier ?? listing.NO_DOSSIER ?? null) as string | null,
    numero_mandat: (index.numero_mandat ?? listing.numero_mandat ?? listing.no_mandat ?? listing.NO_MANDAT ?? null) as string | null,
    titre_bien: String(index.titre_bien ?? listing.titre_bien ?? listing.titre ?? '[Sans titre]'),
    ville: (index.ville ?? listing.ville ?? null) as string | null,
    code_postal: (index.code_postal ?? listing.code_postal ?? null) as string | null,
    type_bien: index.type_bien == null ? (listing.idtype == null ? null : String(listing.idtype)) : String(index.type_bien),
    prix: priceValue == null ? null : Number(priceValue),
    commercial_id: index.commercial_id == null ? null : String(index.commercial_id),
    commercial_nom: (index.commercial_nom ?? null) as string | null,
    negociateur_email: (index.negociateur_email ?? null) as string | null,
    agence_nom: (index.agence_nom ?? null) as string | null,
    statut_annonce: (index.statut_annonce ?? detail.statut_name ?? null) as string | null,
    validation_diffusion_state: (index.validation_diffusion_state ?? null) as string | null,
    etat_visibilite: (index.etat_visibilite ?? null) as string | null,
    alerte_principale: (index.alerte_principale ?? null) as string | null,
    priority: (index.priority ?? 'normal') as string | null,
    has_open_blocker: Boolean(index.has_open_blocker ?? false),
    commentaire_resume: (index.commentaire_resume ?? null) as string | null,
    date_relance_prevue: (index.date_relance_prevue ?? null) as string | null,
    dernier_event_type: (index.dernier_event_type ?? null) as string | null,
    dernier_work_status: (index.dernier_work_status ?? null) as string | null,
    has_local_detail: true,
    local_detail_updated_at: (payload.prepared_locally_at ?? null) as string | null,
    has_detail_cache: true,
    detail_cache_expires_at: data.expires_at ?? null,
    detail_payload_json: JSON.stringify(detail),
  }
  return dossier
}

export async function loadArchivedAnnonceDetailCache(hektorAnnonceId: number | string): Promise<DetailedDossier | null> {
  return loadLightweightAnnonceDetailCache('app_archive_annonce_detail_cache', 'app_archive_annonce_index_current', 'app_archive_id', 'app_archive_id', '1', hektorAnnonceId)
}

export async function loadHistoricalAnnonceDetailCache(hektorAnnonceId: number | string): Promise<DetailedDossier | null> {
  return loadLightweightAnnonceDetailCache('app_historical_annonce_detail_cache', 'app_historical_annonce_index_current', 'app_historical_id', 'app_historical_id', '0', hektorAnnonceId)
}

export async function loadDossierByHektorAnnonceId(hektorAnnonceId: string | number, scope?: DataScope | null): Promise<Dossier | null> {
  if (!hasSupabaseEnv || !supabase) {
    return filterByNegotiatorEmail(mockDossiers, scope).find((item) => String(item.hektor_annonce_id) === String(hektorAnnonceId)) ?? null
  }

  const { data, error } = await applyNegotiatorScopeToQuery(
    supabase
      .from('app_dossiers_current')
      .select('*')
      .eq('hektor_annonce_id', hektorAnnonceId)
      .limit(1),
    scope,
  )
  if (error) throw new Error(error.message)
  return ((data ?? [])[0] as Dossier | undefined) ?? null
}

export async function setDossierDiffusable(appDossierId: number, diffusable: boolean): Promise<void> {
  if (!hasSupabaseEnv || !supabase) return
  const now = new Date().toISOString()
  const { error } = await supabase
    .from('app_dossier_current')
    .update({
      diffusable: diffusable ? '1' : '0',
      refreshed_at: now,
    })
    .eq('app_dossier_id', appDossierId)
  if (error) throw new Error(error.message)
}

export async function setDossierHektorState(
  appDossierId: number,
  input: { validationDiffusionState?: string | null; diffusable?: boolean | null; portailsResume?: string | null; nbPortailsActifs?: number | null },
): Promise<void> {
  if (canUseBackendApi()) {
    await invokeBackendApi<{ ok: true; payload: { app_dossier_id: number } }>('/hektor-diffusion/persist-state', {
      body: {
        appDossierId,
        validationDiffusionState: typeof input.validationDiffusionState !== 'undefined' ? input.validationDiffusionState : undefined,
        diffusable: typeof input.diffusable !== 'undefined' ? input.diffusable : undefined,
        portailsResume: typeof input.portailsResume !== 'undefined' ? input.portailsResume : undefined,
        nbPortailsActifs: typeof input.nbPortailsActifs !== 'undefined' ? input.nbPortailsActifs : undefined,
      },
    })
    return
  }
  if (!hasSupabaseEnv || !supabase) return
  const now = new Date().toISOString()
  const patch: Record<string, string> = {
    refreshed_at: now,
  }
  if (typeof input.validationDiffusionState !== 'undefined') {
    patch.validation_diffusion_state = input.validationDiffusionState ?? ''
  }
  if (typeof input.diffusable !== 'undefined' && input.diffusable !== null) {
    patch.diffusable = input.diffusable ? '1' : '0'
  }
  if (typeof input.portailsResume !== 'undefined') {
    patch.portails_resume = input.portailsResume ?? ''
  }
  if (typeof input.nbPortailsActifs !== 'undefined' && input.nbPortailsActifs !== null) {
    patch.nb_portails_actifs = String(input.nbPortailsActifs)
  }
  const { error } = await supabase
    .from('app_dossier_current')
    .update(patch)
    .eq('app_dossier_id', appDossierId)
  if (error) throw new Error(error.message)
}

export type HektorDiffusableResult = {
  app_dossier_id: number
  hektor_annonce_id: string
  dry_run: boolean
  requested_diffusable: boolean
  changed: boolean
  result: string
  observed_diffusable?: string | null
  error?: string | null
}

export async function setDossierDiffusableOnHektor(input: { appDossierId: number; diffusable: boolean; dryRun?: boolean }): Promise<HektorDiffusableResult> {
  if (canUseLocalDiffusionDevApi()) {
    const response = await fetch('/api/hektor-diffusion/set-diffusable', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || payload?.ok === false) {
      throw new Error(extractApiErrorMessage(payload) || 'Erreur de mise a jour diffusable Hektor')
    }
    const result = payload?.payload as HektorDiffusableResult
    if (result?.error) throw new Error(result.error)
    return result
  }
  if (canUseBackendApi()) {
    const payload = await invokeBackendApi<{ ok: true; payload: HektorDiffusableResult }>('/hektor-diffusion/diffusable', {
      method: 'POST',
      body: {
        appDossierId: input.appDossierId,
        diffusable: input.diffusable,
        dryRun: Boolean(input.dryRun),
      },
    })
    if (payload.payload?.error) throw new Error(payload.payload.error)
    return payload.payload
  }
  throw new Error("Le passage diffusable Hektor reel nécessite le backend Render.")
}

export type HektorValidationResult = {
  app_dossier_id: number
  hektor_annonce_id: string
  dry_run: boolean
  requested_state: 0 | 1
  validation_result: string
  response_status?: number
  response_payload?: unknown
  response_preview?: string
  error?: string | null
  observed_validation_before?: string | null
  observed_validation?: string | null
  observed_diffusable_before?: string | null
  observed_diffusable?: string | null
  refresh_single_annonce?: unknown
}

export type HektorPriceDropCheckResult = {
  app_dossier_id: number
  hektor_annonce_id: string
  requested_price: number
  observed_price: number | null
  matches: boolean
  message: string
  price_candidates?: Array<Record<string, unknown>>
  read_error?: string | null
}

export async function verifyPriceDropOnHektor(input: { appDossierId: number; requestedPrice?: string | number | null; requestText?: string | null }): Promise<HektorPriceDropCheckResult> {
  if (canUseLocalDiffusionDevApi()) {
    const response = await fetch('/api/hektor-diffusion/price-drop-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        appDossierId: input.appDossierId,
        requestedPrice: input.requestedPrice ?? null,
        requestText: input.requestText ?? null,
      }),
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || payload?.ok === false) {
      throw new Error(extractApiErrorMessage(payload) || 'Controle du prix Hektor impossible')
    }
    return payload.payload as HektorPriceDropCheckResult
  }
  if (backendApiBaseUrl) {
    const payload = await invokeBackendApi<{ ok: true; payload: HektorPriceDropCheckResult }>('/hektor-diffusion/price-drop-check', {
      method: 'POST',
      body: {
        appDossierId: input.appDossierId,
        requestedPrice: input.requestedPrice ?? null,
        requestText: input.requestText ?? null,
      },
    })
    return payload.payload
  }
  assertBackendApiConfigured()
  throw new Error('Controle du prix Hektor indisponible')
}

export async function setDossierValidationOnHektor(input: { appDossierId: number; state: 0 | 1; dryRun?: boolean }): Promise<HektorValidationResult> {
  if (canUseLocalDiffusionDevApi()) {
    const response = await fetch('/api/hektor-diffusion/set-validation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    })
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || payload?.ok === false) {
      throw new Error(extractApiErrorMessage(payload) || 'Erreur de mise a jour validation Hektor')
    }
    const result = payload?.payload as HektorValidationResult
    if (result?.error) {
      throw new Error(result.error)
    }
    return result
  }
  if (canUseBackendApi()) {
    const payload = await invokeBackendApi<{ ok: true; payload: HektorValidationResult }>('/hektor-diffusion/validation', {
      method: 'POST',
      body: {
        appDossierId: input.appDossierId,
        state: input.state,
        dryRun: Boolean(input.dryRun),
      },
    })
    if (payload.payload?.error) throw new Error(payload.payload.error)
    return payload.payload
  }
  throw new Error("Le pilotage Validation Oui/Non necessite le backend Render.")
}

export async function loadFilterCatalog(scope?: DataScope | null): Promise<FilterCatalog> {
  if (!hasSupabaseEnv || !supabase) {
    const scopedDossiers = filterByNegotiatorEmail(mockDossiers, scope)
    const scopedWorkItems = filterByNegotiatorEmail(mockWorkItems, scope)
    return {
      commercials: uniqSorted([...scopedDossiers.map((item) => item.commercial_nom), ...scopedWorkItems.map((item) => item.commercial_nom)]),
      agencies: uniqSorted([...scopedDossiers.map((item) => item.agence_nom), ...scopedWorkItems.map((item) => (item as WorkItem & { agence_nom?: string | null }).agence_nom)]),
      statuts: uniqSorted(scopedDossiers.map((item) => item.statut_annonce)),
      validationDiffusions: uniqSorted([...scopedDossiers.map((item) => item.validation_diffusion_state), ...scopedWorkItems.map((item) => item.validation_diffusion_state)]),
      diffusions: ['diffusable', 'non_diffusable'],
      passerelles: uniqSorted(scopedDossiers.flatMap((item) => (item.portails_resume ?? '').split(',').map((value) => value.trim()))),
      erreursDiffusion: ['avec_erreur', 'sans_erreur'],
      priorities: uniqSorted([...scopedDossiers.map((item) => item.priority), ...scopedWorkItems.map((item) => item.priority)]),
      workStatuses: uniqSorted(scopedWorkItems.map((item) => item.work_status)),
      internalStatuses: uniqSorted(scopedWorkItems.map((item) => item.internal_status)),
    }
  }

  const { negotiatorEmail } = normalizeScope(scope)
  if (negotiatorEmail) {
    const batchSize = 1000
    let from = 0
    const dossiers: Dossier[] = []
    const workItems: WorkItem[] = []

    while (true) {
      const { data, error } = await applyNegotiatorScopeToQuery(
        supabase
          .from(dossiersCurrentView)
          .select('app_dossier_id,commercial_nom,agence_nom,statut_annonce,validation_diffusion_state,portails_resume,diffusable,priority,negociateur_email')
          .order('app_dossier_id', { ascending: true })
          .range(from, from + batchSize - 1),
        scope,
      )
      if (error || !data) throw new Error(error?.message ?? 'Unable to load scoped filter catalog dossiers')
      dossiers.push(...(data as Dossier[]))
      if (data.length < batchSize) break
      from += batchSize
    }

    from = 0
    while (true) {
      const { data, error } = await applyNegotiatorScopeToQuery(
        supabase
          .from('app_work_items_current')
          .select('app_dossier_id,commercial_nom,validation_diffusion_state,priority,work_status,internal_status')
          .order('app_dossier_id', { ascending: true })
          .range(from, from + batchSize - 1),
        null,
      )
      if (error || !data) throw new Error(error?.message ?? 'Unable to load scoped filter catalog work items')
      workItems.push(...(data as WorkItem[]))
      if (data.length < batchSize) break
      from += batchSize
    }

    return {
      commercials: uniqSorted(dossiers.map((item) => item.commercial_nom).concat(workItems.map((item) => item.commercial_nom))),
      agencies: uniqSorted(dossiers.map((item) => item.agence_nom).concat(workItems.map((item) => item.agence_nom))),
      statuts: uniqSorted(dossiers.map((item) => item.statut_annonce)),
      validationDiffusions: uniqSorted(dossiers.map((item) => item.validation_diffusion_state).concat(workItems.map((item) => item.validation_diffusion_state))),
      diffusions: uniqSorted(dossiers.map((item) => ((item.diffusable ?? '0') === '1' ? 'diffusable' : 'non_diffusable'))),
      passerelles: uniqSorted(dossiers.flatMap((item) => (item.portails_resume ?? '').split(',').map((value) => value.trim()))),
      erreursDiffusion: ['avec_erreur', 'sans_erreur'],
      priorities: uniqSorted(dossiers.map((item) => item.priority).concat(workItems.map((item) => item.priority))),
      workStatuses: uniqSorted(workItems.map((item) => item.work_status)),
      internalStatuses: uniqSorted(workItems.map((item) => item.internal_status)),
    }
  }

  const { data, error } = await supabase
    .from('app_filter_catalog_current')
    .select('filter_type,filter_value,sort_order')
    .order('filter_type', { ascending: true })
    .order('sort_order', { ascending: true })
    .order('filter_value', { ascending: true })

  if (error || !data) throw new Error(error?.message ?? 'Unable to load filter catalog')

  const grouped: Record<string, string[]> = {
    commercial: [],
    agence: [],
    validation_diffusion_state: [],
    diffusable: [],
    passerelle: [],
    erreur_diffusion: [],
    priority: [],
    work_status: [],
    internal_status: [],
  }

  for (const row of data as Array<{ filter_type: string; filter_value: string }>) {
    if (grouped[row.filter_type]) grouped[row.filter_type].push(row.filter_value)
  }

  return {
    commercials: uniqSorted(grouped.commercial),
    agencies: uniqSorted(grouped.agence),
    statuts: [],
    validationDiffusions: uniqSorted(grouped.validation_diffusion_state),
    diffusions: uniqSorted(grouped.diffusable),
    passerelles: uniqSorted(grouped.passerelle),
    erreursDiffusion: uniqSorted(grouped.erreur_diffusion),
    priorities: uniqSorted(grouped.priority),
    workStatuses: uniqSorted(grouped.work_status),
    internalStatuses: uniqSorted(grouped.internal_status),
  }
}

export async function loadMandatFilterCatalog(scope?: DataScope | null): Promise<Pick<FilterCatalog, 'commercials' | 'agencies' | 'statuts' | 'validationDiffusions' | 'passerelles' | 'diffusions' | 'erreursDiffusion'>> {
  if (!hasSupabaseEnv || !supabase) {
    const scopedMandats = withRegisterRowId(filterByNegotiatorEmail(mockMandats, scope))
    return {
      commercials: uniqSorted(scopedMandats.map((item) => item.commercial_nom)),
      agencies: uniqSorted(scopedMandats.map((item) => item.agence_nom)),
      statuts: uniqSorted(scopedMandats.map((item) => item.statut_annonce)),
      validationDiffusions: uniqSorted(scopedMandats.map((item) => item.validation_diffusion_state)),
      diffusions: uniqSorted(scopedMandats.map((item) => ((item.diffusable ?? '0') === '1' ? 'diffusable' : 'non_diffusable'))),
      passerelles: uniqSorted(scopedMandats.flatMap((item) => (item.portails_resume ?? '').split(',').map((value) => value.trim()))),
      erreursDiffusion: ['avec_erreur', 'sans_erreur'],
    }
  }

  const batchSize = 1000
  let from = 0
  const commercials: string[] = []
  const agencies: string[] = []
  const statuts: string[] = []
  const validationDiffusions: string[] = []
  const passerelles: string[] = []
  const diffusions: string[] = []

  while (true) {
    const { data, error } = await applyNegotiatorScopeToQuery(
      supabase
      .from('app_registre_mandats_current')
      .select('register_row_id,commercial_nom,agence_nom,statut_annonce,validation_diffusion_state,portails_resume,diffusable,numero_mandat')
      .not('numero_mandat', 'is', null)
      .neq('numero_mandat', '')
      .order('register_row_id', { ascending: true })
      .range(from, from + batchSize - 1),
      scope,
    )

    if (error || !data) throw new Error(error?.message ?? 'Unable to load mandat filter catalog')
    if (data.length === 0) break

    for (const row of data as Array<{ commercial_nom: string | null; agence_nom: string | null; statut_annonce: string | null; validation_diffusion_state: string | null; portails_resume: string | null; diffusable: string | null }>) {
      commercials.push((row.commercial_nom ?? '').trim())
      agencies.push((row.agence_nom ?? '').trim())
      statuts.push(row.statut_annonce ?? '')
      validationDiffusions.push(row.validation_diffusion_state ?? '')
      diffusions.push((row.diffusable ?? '0') === '1' ? 'diffusable' : 'non_diffusable')
      passerelles.push(...(row.portails_resume ?? '').split(',').map((value) => value.trim()))
    }

    if (data.length < batchSize) break
    from += batchSize
  }

  return {
    commercials: uniqSorted(commercials),
    agencies: uniqSorted(agencies),
    statuts: uniqSorted(statuts),
    validationDiffusions: uniqSorted(validationDiffusions),
    diffusions: uniqSorted(diffusions),
    passerelles: uniqSorted(passerelles),
    erreursDiffusion: ['avec_erreur', 'sans_erreur'],
  }
}

export async function loadUserProfile(userId: string): Promise<UserProfile | null> {
  if (!hasSupabaseEnv || !supabase) return mockUserProfile
  const { data, error } = await supabase.from('app_user_profile').select('*').eq('id', userId).maybeSingle()
  if (error) throw new Error(error.message)
  return (data as UserProfile | null) ?? null
}

export async function loadGoogleWorkspaceIdentity(userId: string): Promise<GoogleWorkspaceIdentity | null> {
  if (!hasSupabaseEnv || !supabase) return null
  const { data, error } = await supabase
    .from('app_google_workspace_identity')
    .select('id,app_user_id,google_email,workspace_domain,hektor_user_id,hektor_negociateur_id,negociateur_email,link_status,is_active,last_login_at,last_checked_at,metadata_json')
    .eq('app_user_id', userId)
    .maybeSingle()
  if (error) throw new Error(error.message)
  return (data as GoogleWorkspaceIdentity | null) ?? null
}

export async function loadUserNegotiatorContext(email: string | null | undefined): Promise<UserNegotiatorContext | null> {
  const normalized = normalizeEmail(email)
  if (!normalized) return null

  if (!hasSupabaseEnv || !supabase) {
    const row =
      mockMandats.find((item) => normalizeEmail(item.negociateur_email) === normalized) ??
      mockDossiers.find((item) => normalizeEmail(item.negociateur_email) === normalized)
    return row
      ? {
          commercial_nom: row.commercial_nom ?? null,
          negociateur_email: row.negociateur_email ?? null,
          agence_nom: row.agence_nom ?? null,
          hektor_user_id: row.commercial_id == null ? null : String(row.commercial_id),
        }
      : null
  }

  const { data: userData, error: userError } = await supabase
    .from('app_user_directory')
    .select('id_user,display_name,email')
    .eq('user_type', 'NEGO')
    .ilike('email', normalized)
    .limit(1)
    .maybeSingle()

  if (userError) throw new Error(userError.message)

  const activeUser = userData as { id_user?: string | number | null; display_name?: string | null; email?: string | null } | null
  if (activeUser?.id_user) {
    const activeUserId = String(activeUser.id_user)
    const { data: directoryData, error: directoryError } = await supabase
      .from('app_hektor_negotiator_agency_directory')
      .select('hektor_user_id,display_name,email,agence_nom')
      .eq('hektor_user_id', activeUserId)
      .limit(1)
      .maybeSingle()

    if (directoryError) {
      const message = (directoryError.message ?? '').toLowerCase()
      if (!(message.includes('app_hektor_negotiator_agency_directory') && (message.includes('does not exist') || message.includes('schema cache')))) {
        throw new Error(directoryError.message)
      }
    }

    const directoryContext = directoryData as { hektor_user_id?: string | number | null; display_name?: string | null; email?: string | null; agence_nom?: string | null } | null
    return {
      commercial_nom: directoryContext?.display_name ?? activeUser.display_name ?? null,
      negociateur_email: directoryContext?.email ?? activeUser.email ?? normalized,
      agence_nom: directoryContext?.agence_nom ?? null,
      hektor_user_id: activeUserId,
    }
  }

  return null
}

export async function loadHektorNegotiatorOptions(scope?: DataScope | null): Promise<HektorNegotiatorOption[]> {
  if (!hasSupabaseEnv || !supabase) {
    return uniqSorted(mockDossiers.map((item) => item.negociateur_email))
      .map<HektorNegotiatorOption | null>((email) => {
        const row = mockDossiers.find((item) => item.negociateur_email === email)
        return row && row.commercial_id
          ? {
              idUser: String(row.commercial_id),
              label: row.commercial_nom ?? email ?? String(row.commercial_id),
              email: email ?? null,
              agenceNom: row.agence_nom ?? null,
              commercialId: row.commercial_id == null ? null : String(row.commercial_id),
            }
          : null
      })
      .filter((item): item is HektorNegotiatorOption => Boolean(item))
  }

  const [directoryResult, activeUsersResult, dossierResult] = await Promise.all([
    supabase
      .from('app_hektor_negotiator_agency_directory')
      .select('hektor_negociateur_id,hektor_user_id,hektor_agence_id,agence_id_user,agence_nom,display_name,email')
      .order('agence_nom', { ascending: true })
      .order('display_name', { ascending: true })
      .limit(500),
    supabase
      .from('app_user_directory')
      .select('id_user')
      .eq('user_type', 'NEGO')
      .limit(1000),
    supabase
      .from('app_dossiers_current')
      .select('commercial_id,commercial_nom,negociateur_email,agence_nom')
      .limit(4000),
  ])

  if (directoryResult.error) throw new Error(directoryResult.error.message)
  if (activeUsersResult.error) throw new Error(activeUsersResult.error.message)
  if (dossierResult.error) throw new Error(dossierResult.error.message)

  const activeHektorUserIds = new Set(
    ((activeUsersResult.data ?? []) as Array<{ id_user?: string | number | null }>)
      .map((row) => (row.id_user == null ? '' : String(row.id_user).trim()))
      .filter(Boolean),
  )

  const dossierByEmail = new Map<string, { commercial_id?: string | null; commercial_nom?: string | null; negociateur_email?: string | null; agence_nom?: string | null }>()
  for (const row of (dossierResult.data ?? []) as Array<{ commercial_id?: string | null; commercial_nom?: string | null; negociateur_email?: string | null; agence_nom?: string | null }>) {
    const email = normalizeEmail(row.negociateur_email)
    if (!email || dossierByEmail.has(email)) continue
    dossierByEmail.set(email, row)
  }

  const wantedEmail = normalizeEmail(scope?.negotiatorEmail)
  return ((directoryResult.data ?? []) as Array<{ hektor_negociateur_id?: string | number | null; hektor_user_id?: string | number | null; hektor_agence_id?: string | number | null; agence_id_user?: string | number | null; agence_nom?: string | null; display_name?: string | null; email?: string | null }>)
    .map<HektorNegotiatorOption | null>((row) => {
      const idUser = row.hektor_user_id == null ? '' : String(row.hektor_user_id).trim()
      if (!idUser) return null
      if (!activeHektorUserIds.has(idUser)) return null
      const email = normalizeEmail(row.email)
      if (wantedEmail && email !== wantedEmail) return null
      const dossier = email ? dossierByEmail.get(email) : undefined
      const label = (row.display_name ?? dossier?.commercial_nom ?? row.email ?? idUser).trim()
      return {
        idUser,
        label: label || idUser,
        email: row.email ?? dossier?.negociateur_email ?? null,
        agenceNom: row.agence_nom ?? dossier?.agence_nom ?? null,
        commercialId: dossier?.commercial_id == null ? null : String(dossier.commercial_id),
        hektorNegociateurId: row.hektor_negociateur_id == null ? null : String(row.hektor_negociateur_id),
        hektorAgenceId: row.hektor_agence_id == null ? null : String(row.hektor_agence_id),
        agenceIdUser: row.agence_id_user == null ? null : String(row.agence_id_user),
      }
    })
    .filter((item): item is HektorNegotiatorOption => Boolean(item))
}

export async function loadHektorAgencyOptions(): Promise<HektorAgencyOption[]> {
  if (!hasSupabaseEnv || !supabase) return []
  const { data, error } = await supabase
    .from('app_agence_directory')
    .select('id_agence,id_user,nom,mail')
    .order('nom', { ascending: true })
    .limit(200)
  if (error) throw new Error(error.message)
  return ((data ?? []) as Array<{ id_agence?: string | number | null; id_user?: string | number | null; nom?: string | null; mail?: string | null }>)
    .map((row) => {
      const idAgence = row.id_agence == null ? '' : String(row.id_agence).trim()
      if (!idAgence) return null
      return {
        idAgence,
        idUser: row.id_user == null ? null : String(row.id_user),
        label: row.nom ?? idAgence,
        email: row.mail ?? null,
      }
    })
    .filter((item): item is HektorAgencyOption => Boolean(item))
}

export async function loadMandatsPage({
  filters,
  page,
  pageSize,
  scope,
}: {
  filters: AppFilters
  page: number
  pageSize: number
  scope?: DataScope | null
}): Promise<PageResult<MandatRecord>> {
  if (!hasSupabaseEnv || !supabase) {
    return paginate(
      applyLocalDossierFilters(
        filterByNegotiatorEmail(mockMandats, scope).map((item) => ({
          ...item,
          etat_visibilite: null,
          alerte_principale: null,
          has_open_blocker: false,
          commentaire_resume: null,
          date_relance_prevue: null,
          dernier_event_type: null,
          dernier_work_status: null,
        })),
        filters,
      ) as unknown as MandatRecord[],
      page,
      pageSize,
    )
  }

  const requestScopedIds = await resolveRequestScopedDossierIds(filters, scope)
  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  const countMode: 'exact' = 'exact'
  const statut = normalizeFilterValue(filters.statut)
  const shouldUseMergedAnnonceListing =
    filters.archive === archivedFilterValue ||
    filters.archive === allFilterValue ||
    historicalListingStatuses.includes(statut) ||
    (filters.archive === activeArchiveFilterValue && (!statut || statut === annonceSearchListingsFilterValue))
  if (shouldUseMergedAnnonceListing) {
    const listingPage = await loadDossiersPage({ filters, page, pageSize, scope })
    return {
      ...listingPage,
      rows: listingPage.rows.map(dossierToMandatRecord),
    }
  }
  let query = applyDossierFiltersToQuery(
    applyNegotiatorScopeToQuery(supabase.from(dossiersCurrentView).select('*', { count: countMode }), scope),
    filters,
  )
    .order('has_diffusion_error', { ascending: false })
    .order('nb_portails_actifs', { ascending: false })
    .order('app_dossier_id', { ascending: true })
  if (requestScopedIds) {
    query = requestScopedIds.length > 0 ? query.in('app_dossier_id', requestScopedIds) : query.eq('app_dossier_id', -1)
  }
  query = query.range(from, to)

  const { data, error, count } = await query
  if (error || !data) throw new Error(error?.message ?? 'Unable to load mandats')
  return {
    rows: data as MandatRecord[],
    total: count ?? 0,
    page,
    pageSize,
  }
}

function mandatNumberSortValue(value: string | null | undefined) {
  const normalized = (value ?? '').trim()
  if (!normalized) return Number.NEGATIVE_INFINITY
  const digits = normalized.replace(/\D+/g, '')
  if (!digits) return Number.NEGATIVE_INFINITY
  const parsed = Number(digits)
  return Number.isFinite(parsed) ? parsed : Number.NEGATIVE_INFINITY
}

function withRegisterRowId<T extends MandatRecord>(rows: T[]) {
  return rows.map((item) => ({
    ...item,
    register_row_id: item.register_row_id ?? `${item.hektor_annonce_id ?? 'na'}:${item.numero_mandat ?? item.app_dossier_id ?? 'na'}`,
  }))
}

function sortMandatRegisterRows(rows: MandatRecord[]) {
  return rows.slice().sort((a, b) => {
    const byNumber = mandatNumberSortValue(b.numero_mandat) - mandatNumberSortValue(a.numero_mandat)
    if (byNumber !== 0) return byNumber
    const byLabel = String(b.numero_mandat ?? '').localeCompare(String(a.numero_mandat ?? ''), 'fr')
    if (byLabel !== 0) return byLabel
    return String(b.register_row_id ?? b.app_dossier_id ?? '').localeCompare(String(a.register_row_id ?? a.app_dossier_id ?? ''), 'fr')
  })
}

export async function loadMandatRegisterPage({
  filters,
  page,
  pageSize,
  scope,
}: {
  filters: AppFilters
  page: number
  pageSize: number
  scope?: DataScope | null
}): Promise<PageResult<MandatRecord>> {
  if (!hasSupabaseEnv || !supabase) {
    const rows = sortMandatRegisterRows(
      applyMandateLifecycleFilter(
        (applyLocalDossierFilters(
          withRegisterRowId(filterByNegotiatorEmail(mockMandats, scope))
            .filter((item) => Boolean((item.numero_mandat ?? '').trim()))
            .map((item) => ({
              ...item,
              etat_visibilite: null,
              alerte_principale: null,
              has_open_blocker: false,
              commentaire_resume: null,
              date_relance_prevue: null,
              dernier_event_type: null,
              dernier_work_status: null,
            })),
          filters,
        ) as unknown as MandatRecord[]),
        filters,
      ),
    )
    return paginate(rows, page, pageSize)
  }

  const requestScopedIds = await resolveRequestScopedDossierIds(filters, scope)
  const mandateState = normalizeFilterValue(filters.mandateState)
  if (mandateState) {
    const batchSize = 1000
    let batchFrom = 0
    const rows: MandatRecord[] = []

    while (true) {
      let query = applyDossierFiltersToQuery(
        applyNegotiatorScopeToQuery(
          supabase
            .from('app_registre_mandats_current')
            .select('*')
            .not('numero_mandat', 'is', null)
            .neq('numero_mandat', ''),
          scope,
        ),
        filters,
      )
        .order('register_sort_group', { ascending: true })
        .order('register_sort_num', { ascending: false })
        .order('hektor_annonce_id', { ascending: false })
        .order('register_row_id', { ascending: false })
        .range(batchFrom, batchFrom + batchSize - 1)

      if (requestScopedIds) {
        query = requestScopedIds.length > 0 ? query.in('app_dossier_id', requestScopedIds) : query.eq('app_dossier_id', -1)
      }

      const { data, error } = await query
      if (error || !data) throw new Error(error?.message ?? 'Unable to load mandat register')
      rows.push(...withRegisterRowId(data as MandatRecord[]))
      if (data.length < batchSize) break
      batchFrom += batchSize
    }

    return paginate(sortMandatRegisterRows(applyMandateLifecycleFilter(rows, filters)), page, pageSize)
  }

  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  const countMode: 'exact' = 'exact'
  let query = applyDossierFiltersToQuery(
    applyNegotiatorScopeToQuery(
      supabase
        .from('app_registre_mandats_current')
        .select('*', { count: countMode })
        .not('numero_mandat', 'is', null)
        .neq('numero_mandat', ''),
      scope,
    ),
    filters,
  )
    .order('register_sort_group', { ascending: true })
    .order('register_sort_num', { ascending: false })
    .order('hektor_annonce_id', { ascending: false })
    .order('register_row_id', { ascending: false })
    .range(from, to)

  if (requestScopedIds) {
    query = requestScopedIds.length > 0 ? query.in('app_dossier_id', requestScopedIds) : query.eq('app_dossier_id', -1)
  }

  const { data, error, count } = await query
  if (error || !data) throw new Error(error?.message ?? 'Unable to load mandat register')
  return {
    rows: withRegisterRowId(data as MandatRecord[]),
    total: count ?? 0,
    page,
    pageSize,
  }
}

export async function loadMandatRegisterStats(filters: AppFilters, scope?: DataScope | null): Promise<MandatStats> {
  if (!hasSupabaseEnv || !supabase) {
    const rows = applyMandateLifecycleFilter(
      applyLocalDossierFilters(
        withRegisterRowId(filterByNegotiatorEmail(mockMandats, scope)).map((item) => ({
          ...item,
          etat_visibilite: null,
          alerte_principale: null,
          has_open_blocker: false,
          commentaire_resume: null,
          date_relance_prevue: null,
          dernier_event_type: null,
          dernier_work_status: null,
        })),
        filters,
      ) as unknown as MandatRecord[],
      filters,
    )
    return {
      total: rows.length,
      withoutMandat: rows.filter((item) => !(item.numero_mandat ?? '').trim()).length,
      mandatNonDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') !== '1').length,
      mandatDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') === '1').length,
      mandatValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && isValidationApproved(item.validation_diffusion_state)).length,
      mandatNonValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && !isValidationApproved(item.validation_diffusion_state)).length,
      offresEnCours: rows.filter((item) => hasOffreAchatEnCours(item)).length,
      offresRefusees: rows.filter((item) => hasOffreAchatRefusee(item)).length,
      compromisEnCours: rows.filter((item) => hasCompromisEnCours(item)).length,
      compromisAnnules: rows.filter((item) => hasCompromisAnnule(item)).length,
      affairesEnCours: rows.filter((item) => hasAffaireEnCours(item)).length,
      affairesAnnulees: rows.filter((item) => hasAffaireAnnulee(item)).length,
      leboncoin: rows.filter((item) => (item.portails_resume ?? '').toLowerCase().includes('leboncoin')).length,
      bienici: rows.filter((item) => {
        const normalized = (item.portails_resume ?? '')
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase()
        return normalized.includes('bienici')
      }).length,
      withErrors: rows.filter((item) => Boolean(item.has_diffusion_error)).length,
    }
  }

  const batchSize = 1000
  let from = 0
  const rows: MandatRecord[] = []

  while (true) {
    const { data, error } = await applyDossierFiltersToQuery(
      applyNegotiatorScopeToQuery(
        supabase
          .from('app_registre_mandats_current')
          .select('register_row_id,app_dossier_id,numero_mandat,diffusable,validation_diffusion_state,offre_id,offre_state,offre_last_proposition_type,compromis_id,compromis_state,vente_id,portails_resume,has_diffusion_error,statut_annonce,mandat_date_fin')
          .order('register_row_id', { ascending: true })
          .range(from, from + batchSize - 1),
        scope,
      ),
      filters,
    )

    if (error || !data) throw new Error(error?.message ?? 'Unable to load register stats')
    rows.push(...applyMandateLifecycleFilter(withRegisterRowId(data as MandatRecord[]), filters))
    if (data.length < batchSize) break
    from += batchSize
  }

  return {
    total: rows.length,
    withoutMandat: rows.filter((item) => !(item.numero_mandat ?? '').trim()).length,
    mandatNonDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') !== '1').length,
    mandatDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') === '1').length,
    mandatValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && isValidationApproved(item.validation_diffusion_state)).length,
    mandatNonValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && !isValidationApproved(item.validation_diffusion_state)).length,
    offresEnCours: rows.filter((item) => hasOffreAchatEnCours(item)).length,
    offresRefusees: rows.filter((item) => hasOffreAchatRefusee(item)).length,
    compromisEnCours: rows.filter((item) => hasCompromisEnCours(item)).length,
    compromisAnnules: rows.filter((item) => hasCompromisAnnule(item)).length,
    affairesEnCours: rows.filter((item) => hasAffaireEnCours(item)).length,
    affairesAnnulees: rows.filter((item) => hasAffaireAnnulee(item)).length,
    leboncoin: rows.filter((item) => (item.portails_resume ?? '').toLowerCase().includes('leboncoin')).length,
    bienici: rows.filter((item) => {
      const normalized = (item.portails_resume ?? '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
      return normalized.includes('bienici')
    }).length,
    withErrors: rows.filter((item) => Boolean(item.has_diffusion_error)).length,
  }
}

export async function loadMandatStats(filters: AppFilters, scope?: DataScope | null): Promise<MandatStats> {
  if (!hasSupabaseEnv || !supabase) {
    const rows = applyLocalDossierFilters(
      filterByNegotiatorEmail(mockMandats, scope).map((item) => ({
        ...item,
        etat_visibilite: null,
        alerte_principale: null,
        has_open_blocker: false,
        commentaire_resume: null,
        date_relance_prevue: null,
        dernier_event_type: null,
        dernier_work_status: null,
      })),
      filters,
    ) as unknown as MandatRecord[]
    return {
      total: rows.length,
      withoutMandat: rows.filter((item) => !(item.numero_mandat ?? '').trim()).length,
      mandatNonDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') !== '1').length,
      mandatDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') === '1').length,
      mandatValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && isValidationApproved(item.validation_diffusion_state)).length,
      mandatNonValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && !isValidationApproved(item.validation_diffusion_state)).length,
      offresEnCours: rows.filter((item) => hasOffreAchatEnCours(item)).length,
      offresRefusees: rows.filter((item) => hasOffreAchatRefusee(item)).length,
      compromisEnCours: rows.filter((item) => hasCompromisEnCours(item)).length,
      compromisAnnules: rows.filter((item) => hasCompromisAnnule(item)).length,
      affairesEnCours: rows.filter((item) => hasAffaireEnCours(item)).length,
      affairesAnnulees: rows.filter((item) => hasAffaireAnnulee(item)).length,
      leboncoin: rows.filter((item) => (item.portails_resume ?? '').toLowerCase().includes('leboncoin')).length,
      bienici: rows.filter((item) => {
        const normalized = (item.portails_resume ?? '')
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase()
        return normalized.includes('bienici')
      }).length,
      withErrors: rows.filter((item) => Boolean(item.has_diffusion_error)).length,
    }
  }

  const buildStats = (rows: MandatRecord[]): MandatStats => ({
    total: rows.length,
    withoutMandat: rows.filter((item) => !(item.numero_mandat ?? '').trim()).length,
    mandatNonDiffuse: rows.filter((item) => hasMandatNumber(item.numero_mandat) && (item.diffusable ?? '0') !== '1').length,
    mandatDiffuse: rows.filter((item) => hasMandatNumber(item.numero_mandat) && (item.diffusable ?? '0') === '1').length,
    mandatValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && isValidationApproved(item.validation_diffusion_state)).length,
    mandatNonValide: rows.filter((item) => hasMandatNumber(item.numero_mandat) && !isValidationApproved(item.validation_diffusion_state)).length,
    offresEnCours: rows.filter((item) => hasOffreAchatEnCours(item)).length,
    offresRefusees: rows.filter((item) => hasOffreAchatRefusee(item)).length,
    compromisEnCours: rows.filter((item) => hasCompromisEnCours(item)).length,
    compromisAnnules: rows.filter((item) => hasCompromisAnnule(item)).length,
    affairesEnCours: rows.filter((item) => hasAffaireEnCours(item)).length,
    affairesAnnulees: rows.filter((item) => hasAffaireAnnulee(item)).length,
    leboncoin: rows.filter((item) => (item.portails_resume ?? '').toLowerCase().includes('leboncoin')).length,
    bienici: rows.filter((item) => {
      const normalized = (item.portails_resume ?? '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
      return normalized.includes('bienici')
    }).length,
    withErrors: rows.filter((item) => Boolean(item.has_diffusion_error)).length,
  })

  const batchSize = 1000
  const rows: MandatRecord[] = []
  const statut = normalizeFilterValue(filters.statut)
  const requestScope = normalizeFilterValue(filters.requestScope)
  const requestType = normalizeFilterValue(filters.requestType)
  const canUseLightweightIndexes = !requestScope && !requestType && canUseLightweightAnnonceIndexesForFilters(filters)
  const includePrimary = filters.archive !== archivedFilterValue && !historicalListingStatuses.includes(statut)
  const includeArchiveIndex = canUseLightweightIndexes && (filters.archive === archivedFilterValue || filters.archive === allFilterValue)
  const includeHistoricalIndex =
    canUseLightweightIndexes &&
    (historicalListingStatuses.includes(statut) ||
      ((filters.archive === allFilterValue || filters.archive === activeArchiveFilterValue) && (!statut || statut === annonceSearchListingsFilterValue)))
  const primaryStatsSelect = 'app_dossier_id,numero_dossier,numero_mandat,titre_bien,ville,code_postal,commercial_nom,negociateur_email,agence_nom,archive,statut_annonce,diffusable,validation_diffusion_state,offre_id,offre_state,offre_last_proposition_type,compromis_id,compromis_state,vente_id,portails_resume,has_diffusion_error,mandants_texte'
  const archiveStatsSelect = 'hektor_annonce_id,app_archive_id,numero_dossier,numero_mandat,titre_bien,ville,code_postal,commercial_nom,negociateur_email,agence_nom,archive,statut_annonce,diffusable,mandants_texte'
  const historicalStatsSelect = 'hektor_annonce_id,app_historical_id,numero_dossier,numero_mandat,titre_bien,ville,code_postal,commercial_nom,negociateur_email,agence_nom,archive,statut_annonce,diffusable,mandants_texte'

  if (includePrimary) {
    let from = 0
    while (true) {
      const { data, error } = await applyDossierFiltersToQuery(
        applyNegotiatorScopeToQuery(
          supabase
            .from(dossiersCurrentView)
            .select(primaryStatsSelect)
            .order('app_dossier_id', { ascending: true })
            .range(from, from + batchSize - 1),
          scope,
        ),
        filters,
      )

      if (error || !data) throw new Error(error?.message ?? 'Unable to load mandat stats')
      rows.push(...(data as MandatRecord[]))
      if (data.length < batchSize) break
      from += batchSize
    }
  }

  if (includeArchiveIndex) {
    let from = 0
    while (true) {
      const { data, error } = await applyArchiveIndexFiltersToQuery(
        supabase
          .from('app_archive_annonce_index_current')
          .select(archiveStatsSelect)
          .order('hektor_annonce_id', { ascending: true })
          .range(from, from + batchSize - 1),
        filters,
        scope,
      )

      if (error || !data) throw new Error(error?.message ?? 'Unable to load archived mandat stats')
      const mapped = (data as LightweightAnnonceIndexRow[]).map(lightweightIndexRowToDossier) as unknown as MandatRecord[]
      rows.push(...mapped)
      if (data.length < batchSize) break
      from += batchSize
    }
  }

  if (includeHistoricalIndex) {
    let from = 0
    while (true) {
      const { data, error } = await applyHistoricalIndexFiltersToQuery(
        supabase
          .from('app_historical_annonce_index_current')
          .select(historicalStatsSelect)
          .order('hektor_annonce_id', { ascending: true })
          .range(from, from + batchSize - 1),
        filters,
        scope,
      )

      if (error || !data) throw new Error(error?.message ?? 'Unable to load historical mandat stats')
      const mapped = (data as LightweightAnnonceIndexRow[]).map(lightweightIndexRowToDossier) as unknown as MandatRecord[]
      rows.push(...mapped)
      if (data.length < batchSize) break
      from += batchSize
    }
  }

  return buildStats(rows)
}

export async function loadSuiviRequestStats(filters: AppFilters, scope?: DataScope | null): Promise<SuiviRequestStats> {
  const mandatFilters: AppFilters = { ...filters, mandat: withMandatFilterValue }

  if (!hasSupabaseEnv || !supabase) {
    const mandatIds = new Set(
      applyLocalDossierFilters(
        filterByNegotiatorEmail(mockMandats, scope).map((item) => ({
          ...item,
          etat_visibilite: null,
          alerte_principale: null,
          has_open_blocker: false,
          commentaire_resume: null,
          date_relance_prevue: null,
          dernier_event_type: null,
          dernier_work_status: null,
        })),
        mandatFilters,
      ).map((item) => item.app_dossier_id),
    )
    const requestType = normalizeFilterValue(filters.requestType)
    const allRows = readLocalDiffusionRequests().filter((item) => mandatIds.has(item.app_dossier_id))
    const rows = latestRequestRowsByDossierAndType(allRows, requestType)
    const acceptedHistoricalRows = latestAcceptedRequestRowsByDossierAndType(allRows, requestType)
    return {
      pendingOrInProgress: rows.filter((item) => item.request_status === 'pending' || item.request_status === 'in_progress').length,
      refused: rows.filter((item) => item.request_status === 'refused').length,
      accepted: rows.filter((item) => item.request_status === 'accepted').length,
      acceptedHistorical: acceptedHistoricalRows.length,
    }
  }

  const batchSize = 1000
  let from = 0
  const mandatIds = new Set<number>()

  while (true) {
    const { data, error } = await applyDossierFiltersToQuery(
      applyNegotiatorScopeToQuery(
        supabase
          .from('app_dossiers_current')
          .select('app_dossier_id')
          .order('app_dossier_id', { ascending: true })
          .range(from, from + batchSize - 1),
        scope,
      ),
      mandatFilters,
    )

    if (error || !data) throw new Error(error?.message ?? 'Unable to load suivi request stats dossiers')
    for (const row of data as Array<{ app_dossier_id: number }>) mandatIds.add(row.app_dossier_id)
    if (data.length < batchSize) break
    from += batchSize
  }

  if (mandatIds.size === 0) {
    return { pendingOrInProgress: 0, refused: 0, accepted: 0, acceptedHistorical: 0 }
  }

  const { data, error } = await supabase
    .from('app_diffusion_requests_current')
    .select('app_dossier_id,request_status,request_type')

  if (error || !data) throw new Error(error?.message ?? 'Unable to load suivi request stats requests')

  const requestType = normalizeFilterValue(filters.requestType)
  const allRows = (data as Array<{ app_dossier_id: number; request_status: string | null; request_type?: string | null; requested_at?: string | null; created_at?: string | null }>).filter((item) => mandatIds.has(item.app_dossier_id))
  const rows = latestRequestRowsByDossierAndType(allRows, requestType)
  const acceptedHistoricalRows = latestAcceptedRequestRowsByDossierAndType(allRows, requestType)
  return {
    pendingOrInProgress: rows.filter((item) => item.request_status === 'pending' || item.request_status === 'in_progress').length,
    refused: rows.filter((item) => item.request_status === 'refused').length,
    accepted: rows.filter((item) => item.request_status === 'accepted').length,
    acceptedHistorical: acceptedHistoricalRows.length,
  }
}

export async function loadCommercialRequestStats(filters: AppFilters, scope?: DataScope | null): Promise<CommercialRequestStats> {
  const mandatFilters: AppFilters = { ...filters, mandat: withMandatFilterValue }

  if (!hasSupabaseEnv || !supabase) {
    const mandatIds = new Set(
      applyLocalDossierFilters(
        filterByNegotiatorEmail(mockMandats, scope).map((item) => ({
          ...item,
          etat_visibilite: null,
          alerte_principale: null,
          has_open_blocker: false,
          commentaire_resume: null,
          date_relance_prevue: null,
          dernier_event_type: null,
          dernier_work_status: null,
        })),
        mandatFilters,
      ).map((item) => item.app_dossier_id),
    )
    const requestType = normalizeFilterValue(filters.requestType)
    const rows = latestRequestRowsByDossierAndType(
      readLocalDiffusionRequests().filter((item) => mandatIds.has(item.app_dossier_id)),
      requestType,
    )
    return {
      sent: rows.filter((item) => item.request_status === 'pending' || item.request_status === 'in_progress').length,
      waitingCorrection: rows.filter((item) => item.request_status === 'waiting_commercial' || item.request_status === 'refused').length,
    }
  }

  const batchSize = 1000
  let from = 0
  const mandatIds = new Set<number>()

  while (true) {
    const { data, error } = await applyDossierFiltersToQuery(
      applyNegotiatorScopeToQuery(
        supabase
          .from('app_dossiers_current')
          .select('app_dossier_id')
          .order('app_dossier_id', { ascending: true })
          .range(from, from + batchSize - 1),
        scope,
      ),
      mandatFilters,
    )

    if (error || !data) throw new Error(error?.message ?? 'Unable to load commercial request stats dossiers')
    for (const row of data as Array<{ app_dossier_id: number }>) mandatIds.add(row.app_dossier_id)
    if (data.length < batchSize) break
    from += batchSize
  }

  if (mandatIds.size === 0) {
    return { sent: 0, waitingCorrection: 0 }
  }

  const { data, error } = await supabase
    .from('app_diffusion_requests_current')
    .select('app_dossier_id,request_status,request_type')

  if (error || !data) throw new Error(error?.message ?? 'Unable to load commercial request stats requests')

  const requestType = normalizeFilterValue(filters.requestType)
  const rows = latestRequestRowsByDossierAndType(
    (data as Array<{ app_dossier_id: number; request_status: string | null; request_type?: string | null; requested_at?: string | null; created_at?: string | null }>).filter((item) => mandatIds.has(item.app_dossier_id)),
    requestType,
  )
  return {
    sent: rows.filter((item) => item.request_status === 'pending' || item.request_status === 'in_progress').length,
    waitingCorrection: rows.filter((item) => item.request_status === 'waiting_commercial' || item.request_status === 'refused').length,
  }
}

export async function loadMandatBroadcasts(appDossierId: number): Promise<MandatBroadcast[]> {
  const loadViaLocalDevApi = async () => {
    const response = await fetch(`/api/hektor-diffusion/broadcasts?appDossierId=${encodeURIComponent(String(appDossierId))}`)
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || payload?.ok === false) {
      return mockMandatBroadcasts.filter((item) => item.app_dossier_id === appDossierId)
    }
    return (payload?.payload?.broadcasts ?? []) as MandatBroadcast[]
  }
  if (!hasSupabaseEnv || !supabase) {
    return loadViaLocalDevApi()
  }
  const { data, error } = await supabase
    .from('app_mandat_broadcasts_current')
    .select('*')
    .eq('app_dossier_id', appDossierId)
    .order('passerelle_key', { ascending: true })
  if (error?.message) {
    return loadViaLocalDevApi()
  }
  if (error || !data) throw new Error(error?.message ?? 'Unable to load mandat broadcasts')
  return data as MandatBroadcast[]
}

export async function loadDiffusionRequests(): Promise<DiffusionRequest[]> {
  if (!hasSupabaseEnv || !supabase) return readLocalDiffusionRequests()
  const { data, error } = await supabase
    .from('app_diffusion_requests_current')
    .select('*')
    .order('requested_at', { ascending: false })
  if (error || !data) throw new Error(error?.message ?? 'Unable to load diffusion requests')
  return data as DiffusionRequest[]
}

export async function loadDiffusionRequestEvents(): Promise<DiffusionRequestEvent[]> {
  if (!hasSupabaseEnv || !supabase) return readLocalDiffusionRequestEvents()
  const { data, error } = await supabase
    .from('app_diffusion_request_event')
    .select('*')
    .order('event_at', { ascending: false })
  if (error && isMissingDiffusionRequestEventTableError(error.message)) {
    return readLocalDiffusionRequestEvents()
  }
  if (error || !data) throw new Error(error?.message ?? 'Unable to load diffusion request events')
  return data as DiffusionRequestEvent[]
}

async function insertDiffusionRequestEvent(event: DiffusionRequestEvent) {
  if (!hasSupabaseEnv || !supabase) {
    writeLocalDiffusionRequestEvents([event, ...readLocalDiffusionRequestEvents()])
    return
  }
  const { error } = await supabase.from('app_diffusion_request_event').insert({
    diffusion_request_id: event.diffusion_request_id,
    event_type: event.event_type,
    event_label: event.event_label,
    event_at: event.event_at,
    actor_user_id: event.actor_user_id,
    actor_name: event.actor_name,
    actor_role: event.actor_role,
    payload_json: event.payload_json,
  })
  if (error && (isMissingDiffusionRequestEventTableError(error.message) || isInvalidDiffusionRequestEventIdTypeError(error.message))) {
    writeLocalDiffusionRequestEvents([event, ...readLocalDiffusionRequestEvents()])
    return
  }
  if (error) throw new Error(error.message)
}

export async function createDiffusionRequest(input: {
  dossier: MandatRecord
  comment: string
  requestType?: string | null
  requesterId: string
  requesterLabel: string | null
}): Promise<DiffusionRequest | null> {
  const normalizedType = normalizeBusinessState(input.requestType)
  const requestType = normalizedType === 'demande_baisse_prix'
    ? 'demande_baisse_prix'
    : normalizedType === 'demande_annulation_mandat'
      ? 'demande_annulation_mandat'
      : 'demande_diffusion'
  const createdEventLabel =
    requestType === 'demande_baisse_prix'
      ? 'Demande de baisse de prix envoyee'
      : requestType === 'demande_annulation_mandat'
        ? 'Demande d annulation de mandat envoyee'
        : 'Demande envoyee'
  if (!hasSupabaseEnv || !supabase) {
    const created = {
      id: `local-${Date.now()}`,
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: input.dossier.hektor_annonce_id,
      numero_dossier: input.dossier.numero_dossier,
      numero_mandat: input.dossier.numero_mandat,
      titre_bien: input.dossier.titre_bien,
      commercial_nom: input.dossier.commercial_nom,
      request_type: requestType,
      requested_by: input.requesterId,
      requested_by_label: input.requesterLabel,
      requested_by_name: input.requesterLabel,
      requested_at: new Date().toISOString(),
      request_status: 'pending',
      request_comment: input.comment,
      request_reason: input.comment,
      admin_response: null,
      refusal_reason: null,
      follow_up_needed: false,
      follow_up_at: null,
      relaunch_count: 0,
      processed_by: null,
      processed_by_label: null,
      processed_by_name: null,
      processed_at: null,
      processing_comment: null,
    }
    writeLocalDiffusionRequests([created, ...readLocalDiffusionRequests()])
    await insertDiffusionRequestEvent(buildDiffusionRequestEvent({
      requestId: created.id,
      eventType: 'request_created',
      eventLabel: createdEventLabel,
      actorUserId: input.requesterId,
      actorName: input.requesterLabel,
      actorRole: 'nego',
      message: input.comment.trim() || null,
    }))
    return created
  }

  const payload = {
    app_dossier_id: input.dossier.app_dossier_id,
    hektor_annonce_id: input.dossier.hektor_annonce_id,
    numero_dossier: input.dossier.numero_dossier,
    numero_mandat: input.dossier.numero_mandat,
    titre_bien: input.dossier.titre_bien,
    commercial_nom: input.dossier.commercial_nom,
    request_type: requestType,
    requested_by: input.requesterId,
    requested_by_label: input.requesterLabel,
    request_comment: input.comment.trim() || null,
    request_reason: input.comment.trim() || null,
    follow_up_needed: false,
    relaunch_count: 0,
  }
  const { data, error } = await supabase.from('app_diffusion_request').insert(payload).select('*').single()
  if (error || !data) throw new Error(error?.message ?? 'Unable to create diffusion request')
  const created = data as DiffusionRequest
  await insertDiffusionRequestEvent(buildDiffusionRequestEvent({
    requestId: created.id,
    eventType: 'request_created',
    eventLabel: createdEventLabel,
    actorUserId: input.requesterId,
    actorName: input.requesterLabel,
    actorRole: 'nego',
    message: input.comment.trim() || null,
  }))
  return created
}

export async function updateDiffusionRequest(input: {
  id: string
  status: string
  response: string
  refusalReason: string
  followUpNeeded: boolean
  followUpAt: string | null
  relaunchCount: number
  processorLabel: string | null
  processorId: string | null
}): Promise<void> {
  if (!requestStatuses.includes(input.status)) throw new Error('Invalid request status')
  if (!hasSupabaseEnv || !supabase) {
    const rows = readLocalDiffusionRequests()
    const current = rows.find((row) => row.id === input.id)
    if (!current) return
    const isPriceDrop = current.request_type === 'demande_baisse_prix'
    const isCancellation = current.request_type === 'demande_annulation_mandat'
    const decisionLabel = input.status === 'accepted'
      ? isPriceDrop ? 'Baisse de prix acceptee' : isCancellation ? 'Annulation de mandat acceptee' : 'Demande acceptee'
      : input.status === 'refused'
        ? isPriceDrop ? 'Baisse de prix refusee' : isCancellation ? 'Annulation de mandat refusee' : 'Demande refusee'
        : 'Demande mise a jour'
    const now = new Date().toISOString()
    const nextRows = rows.map((row) => row.id === input.id
      ? {
          ...row,
          request_status: input.status,
          processing_comment: input.response.trim() || null,
          admin_response: input.response.trim() || null,
          refusal_reason: input.refusalReason.trim() || null,
          follow_up_needed: input.followUpNeeded,
          follow_up_at: input.followUpAt,
          relaunch_count: input.relaunchCount,
          processed_by_label: input.processorLabel,
          processed_by: input.processorId,
          processed_at: now,
        }
      : row)
    writeLocalDiffusionRequests(nextRows)
    await insertDiffusionRequestEvent(buildDiffusionRequestEvent({
      requestId: input.id,
      eventType: input.status === 'accepted' ? 'accepted' : input.status === 'refused' ? 'refused' : 'request_updated',
      eventLabel: decisionLabel,
      actorUserId: input.processorId,
      actorName: input.processorLabel,
      actorRole: 'pauline',
      message: input.response.trim() || input.refusalReason.trim() || null,
    }))
    return
  }
  const payload = {
    request_status: input.status,
    processing_comment: input.response.trim() || null,
    admin_response: input.response.trim() || null,
    refusal_reason: input.refusalReason.trim() || null,
    follow_up_needed: input.followUpNeeded,
    follow_up_at: input.followUpAt,
    relaunch_count: input.relaunchCount,
    processed_by_label: input.processorLabel,
    processed_by: input.processorId,
    processed_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  const { error } = await supabase.from('app_diffusion_request').update(payload).eq('id', input.id)
  if (error) throw new Error(error.message)
  const currentRows = await loadDiffusionRequests().catch(() => [])
  const current = currentRows.find((row) => row.id === input.id) ?? null
  const isPriceDrop = current?.request_type === 'demande_baisse_prix'
  const isCancellation = current?.request_type === 'demande_annulation_mandat'
  const decisionLabel = input.status === 'accepted'
    ? isPriceDrop ? 'Baisse de prix acceptee' : isCancellation ? 'Annulation de mandat acceptee' : 'Demande acceptee'
    : input.status === 'refused'
      ? isPriceDrop ? 'Baisse de prix refusee' : isCancellation ? 'Annulation de mandat refusee' : 'Demande refusee'
      : 'Demande mise a jour'
  await insertDiffusionRequestEvent(buildDiffusionRequestEvent({
    requestId: input.id,
    eventType: input.status === 'accepted' ? 'accepted' : input.status === 'refused' ? 'refused' : 'request_updated',
    eventLabel: decisionLabel,
    actorUserId: input.processorId,
    actorName: input.processorLabel,
    actorRole: 'pauline',
    message: input.response.trim() || input.refusalReason.trim() || null,
  }))
}

export async function submitDiffusionCorrection(input: {
  id: string
  comment: string
  requesterLabel: string | null
}): Promise<void> {
  if (!hasSupabaseEnv || !supabase) {
    const rows = readLocalDiffusionRequests()
    const now = new Date().toISOString()
    const current = rows.find((row) => row.id === input.id)
    if (!current) return
    const isPriceDrop = current.request_type === 'demande_baisse_prix'
    const isCancellation = current.request_type === 'demande_annulation_mandat'
    const nextRows = rows.map((row) => row.id === input.id
      ? {
          ...row,
          request_status: 'pending',
          request_comment: input.comment.trim() || null,
          request_reason: input.comment.trim() || null,
          admin_response: row.admin_response,
          follow_up_needed: false,
          follow_up_at: null,
          processed_at: now,
          processing_comment: input.comment.trim() || null,
          processed_by_label: input.requesterLabel,
        }
      : row)
    writeLocalDiffusionRequests(nextRows)
    await insertDiffusionRequestEvent(buildDiffusionRequestEvent({
      requestId: input.id,
      eventType: 'correction_submitted',
      eventLabel: isPriceDrop ? 'Correction baisse de prix envoyee' : isCancellation ? 'Correction annulation mandat envoyee' : 'Correction envoyee',
      actorName: input.requesterLabel,
      actorRole: 'nego',
      message: input.comment.trim() || null,
    }))
    return
  }
  const now = new Date().toISOString()
  const currentRows = await loadDiffusionRequests().catch(() => [])
  const current = currentRows.find((row) => row.id === input.id) ?? null
  const isPriceDrop = current?.request_type === 'demande_baisse_prix'
  const isCancellation = current?.request_type === 'demande_annulation_mandat'
  const payload = {
    request_status: 'pending',
    request_comment: input.comment.trim() || null,
    request_reason: input.comment.trim() || null,
    admin_response: null,
    follow_up_needed: false,
    follow_up_at: null,
    processed_at: now,
    processing_comment: input.comment.trim() || null,
    processed_by_label: input.requesterLabel,
    updated_at: now,
  }
  const { error } = await supabase.from('app_diffusion_request').update(payload).eq('id', input.id)
  if (error) throw new Error(error.message)
  await insertDiffusionRequestEvent(buildDiffusionRequestEvent({
    requestId: input.id,
    eventType: 'correction_submitted',
    eventLabel: isPriceDrop ? 'Correction baisse de prix envoyee' : isCancellation ? 'Correction annulation mandat envoyee' : 'Correction envoyee',
    actorName: input.requesterLabel,
    actorRole: 'nego',
    message: input.comment.trim() || null,
  }))
}

export async function loadDiffusionTargets(appDossierId: number): Promise<DiffusionTarget[]> {
  const loadViaLocalDevApi = async () => {
    const response = await fetch(`/api/hektor-diffusion/targets?appDossierId=${encodeURIComponent(String(appDossierId))}`)
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || payload?.ok === false) {
      return readLocalDiffusionTargets().filter((item) => item.app_dossier_id === appDossierId)
    }
    const rows = (payload?.payload?.targets ?? []) as DiffusionTarget[]
    writeLocalDiffusionTargets([
      ...readLocalDiffusionTargets().filter((item) => item.app_dossier_id !== appDossierId),
      ...rows,
    ])
    return rows
  }
  if (!hasSupabaseEnv || !supabase) {
    return loadViaLocalDevApi()
  }
  const { data, error } = await supabase
    .from('app_diffusion_target')
    .select('*')
    .eq('app_dossier_id', appDossierId)
    .order('portal_key', { ascending: true })
  if (error && isMissingDiffusionTargetTableError(error.message)) {
    if (canUseLocalDiffusionDevApi()) return loadViaLocalDevApi()
    return readLocalDiffusionTargets().filter((item) => item.app_dossier_id === appDossierId)
  }
  if (error || !data) throw new Error(error?.message ?? 'Unable to load diffusion targets')
  return data as DiffusionTarget[]
}

export async function seedDefaultDiffusionTargetsOnHektor(input: { appDossierId: number }) {
  if (!canUseLocalDiffusionDevApi()) {
    throw new Error("Cette action Hektor n'est disponible qu'en environnement local pour l'instant.")
  }
  const response = await fetch('/api/hektor-diffusion/seed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ appDossierId: input.appDossierId }),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.error ?? payload?.stderr ?? payload?.stdout ?? 'Unable to seed diffusion targets')
  }
  return payload.payload as {
    app_dossier_id?: number
    seeded_targets?: number
    targets?: Array<{
      app_dossier_id: number
      hektor_annonce_id: string
      hektor_broadcast_id: string
      portal_key: string | null
      target_state: 'enabled' | 'disabled'
    }>
  }
}

export async function previewDefaultDiffusionTargets(input: { appDossierId: number }) {
  const loadViaLocalDevApi = async () => {
    const response = await fetch(`/api/hektor-diffusion/preview-targets?appDossierId=${encodeURIComponent(String(input.appDossierId))}`)
    const payload = await response.json().catch(() => ({}))
    if (!response.ok || payload?.ok === false) {
      throw new Error(payload?.error ?? payload?.stderr ?? payload?.stdout ?? 'Unable to preview diffusion targets')
    }
    return payload.payload as {
      app_dossier_id?: number
      targets?: Array<{
        app_dossier_id: number
        hektor_annonce_id: string
        hektor_broadcast_id: string
        portal_key: string | null
        target_state: 'enabled' | 'disabled'
      }>
    }
  }

  if (!hasSupabaseEnv || !supabase) {
    return loadViaLocalDevApi()
  }

  const { data: dossier, error: dossierError } = await supabase
    .from('app_dossiers_current')
    .select('app_dossier_id,hektor_annonce_id,agence_nom')
    .eq('app_dossier_id', input.appDossierId)
    .maybeSingle()

  if (dossierError || !dossier) {
    throw new Error(dossierError?.message ?? 'Unable to load dossier for diffusion preview')
  }

  const normalizedAgency = normalizeAgencyName(dossier.agence_nom)
  if (!normalizedAgency) {
    throw new Error(`Agence vide pour app_dossier_id=${input.appDossierId}`)
  }

  let mappingRows: Array<{ agence_nom: string; portal_key: string | null; hektor_broadcast_id: string }> = []
  const { data: agencyTargets, error: agencyError } = await supabase
    .from('app_diffusion_agency_target')
    .select('agence_nom,portal_key,hektor_broadcast_id,is_active')
    .eq('is_active', 1)

  if (agencyError && !isMissingDiffusionAgencyTargetTableError(agencyError.message)) {
    throw new Error(agencyError.message)
  }

  if (!agencyError && agencyTargets) {
    mappingRows = (agencyTargets as Array<{ agence_nom: string; portal_key: string | null; hektor_broadcast_id: string }>)
      .filter((item) => normalizeAgencyName(item.agence_nom) === normalizedAgency)
  }

  if (mappingRows.length === 0) {
    mappingRows = defaultDiffusionAgencyTargets
      .filter((item) => normalizeAgencyName(item.agence_nom) === normalizedAgency)
      .map((item) => ({
        agence_nom: item.agence_nom,
        portal_key: item.portal_key,
        hektor_broadcast_id: item.hektor_broadcast_id,
      }))
  }

  if (mappingRows.length === 0 && canUseLocalDiffusionDevApi()) {
    return loadViaLocalDevApi()
  }

  return {
    app_dossier_id: dossier.app_dossier_id,
    targets: mappingRows.map((item) => ({
      app_dossier_id: dossier.app_dossier_id,
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      hektor_broadcast_id: String(item.hektor_broadcast_id),
      portal_key: item.portal_key,
      target_state: 'disabled' as const,
    })),
  }
}

export async function saveDiffusionTargets(input: {
  mandat: MandatRecord
  targets: Array<{ hektor_broadcast_id: string; portal_key: string | null; target_state: 'enabled' | 'disabled' }>
  requestedByName: string | null
  requestedByRole?: string | null
}): Promise<DiffusionTarget[]> {
  const now = new Date().toISOString()
  const payload: DiffusionTarget[] = input.targets.map((item) => ({
    app_dossier_id: input.mandat.app_dossier_id,
    hektor_annonce_id: input.mandat.hektor_annonce_id,
    hektor_broadcast_id: item.hektor_broadcast_id,
    portal_key: item.portal_key,
    target_state: item.target_state,
    source_ref: 'console_diffusion',
    note: null,
    requested_by_role: input.requestedByRole ?? 'app',
    requested_by_name: input.requestedByName,
    requested_at: now,
    last_applied_at: null,
    last_apply_status: null,
    last_apply_error: null,
  }))

  const saveViaLocalDevApi = async () => {
    const response = await fetch('/api/hektor-diffusion/targets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        appDossierId: input.mandat.app_dossier_id,
        requestedBy: input.requestedByName,
        targets: payload.map((item) => ({
          hektor_broadcast_id: item.hektor_broadcast_id,
          portal_key: item.portal_key,
          target_state: item.target_state,
        })),
      }),
    })
    const result = await response.json().catch(() => ({}))
    if (!response.ok || result?.ok === false) {
      throw new Error(result?.error ?? result?.stderr ?? result?.stdout ?? 'Unable to save diffusion targets')
    }
    const rows = (result?.payload?.targets ?? payload) as DiffusionTarget[]
    writeLocalDiffusionTargets([
      ...readLocalDiffusionTargets().filter((item) => item.app_dossier_id !== input.mandat.app_dossier_id),
      ...rows,
    ])
    return rows
  }

  if (!hasSupabaseEnv || !supabase) {
    return saveViaLocalDevApi()
  }

  const { error: deleteError } = await supabase.from('app_diffusion_target').delete().eq('app_dossier_id', input.mandat.app_dossier_id)
  if (deleteError && isMissingDiffusionTargetTableError(deleteError.message)) {
    if (canUseLocalDiffusionDevApi()) return saveViaLocalDevApi()
    writeLocalDiffusionTargets([
      ...readLocalDiffusionTargets().filter((item) => item.app_dossier_id !== input.mandat.app_dossier_id),
      ...payload,
    ])
    return payload
  }
  if (deleteError) throw new Error(deleteError.message)
  if (payload.length === 0) return []
  const { data, error } = await supabase.from('app_diffusion_target').insert(payload).select('*')
  if (error && isMissingDiffusionTargetTableError(error.message)) {
    if (canUseLocalDiffusionDevApi()) return saveViaLocalDevApi()
    writeLocalDiffusionTargets([
      ...readLocalDiffusionTargets().filter((item) => item.app_dossier_id !== input.mandat.app_dossier_id),
      ...payload,
    ])
    return payload
  }
  if (error || !data) throw new Error(error?.message ?? 'Unable to save diffusion targets')
  return data as DiffusionTarget[]
}

export async function applyDiffusionTargetsOnHektor(input: { appDossierId: number; dryRun?: boolean; ensureDiffusable?: boolean }) {
  if (canUseBackendApi()) {
    const payload = await invokeBackendApi<{
      ok: true
      payload: {
        app_dossier_id: number
        hektor_annonce_id: string
        dry_run: boolean
        validation_result?: string | null
        observed_validation?: string | null
        diffusable_changed: boolean
        diffusable_result: string
        observed_diffusable?: string | null
        validation_state?: string | null
        validation_approved?: boolean
        waiting_on_hektor?: boolean
        waiting_message?: string | null
        current_enabled_count: number
        targets_count: number
        to_add_count: number
        to_remove_count: number
        applied: Array<Record<string, unknown>>
        failed: Array<Record<string, unknown>>
        pending?: Array<Record<string, unknown>>
      }
    }>('/hektor-diffusion/apply', {
      method: 'POST',
      body: {
        appDossierId: input.appDossierId,
        dryRun: Boolean(input.dryRun),
        ensureDiffusable: Boolean(input.ensureDiffusable),
      },
    })
    return payload.payload
  }
  assertBackendApiConfigured()
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    const payload = await invokeSupabaseFunction<{
      ok: true
      payload: {
        app_dossier_id: number
        hektor_annonce_id: string
        dry_run: boolean
        validation_result?: string | null
        observed_validation?: string | null
        diffusable_changed: boolean
        diffusable_result: string
        observed_diffusable?: string | null
        validation_state?: string | null
        validation_approved?: boolean
        waiting_on_hektor?: boolean
        waiting_message?: string | null
        current_enabled_count: number
        targets_count: number
        to_add_count: number
        to_remove_count: number
        applied: Array<Record<string, unknown>>
        failed: Array<Record<string, unknown>>
        pending?: Array<Record<string, unknown>>
      }
    }>('hektor-diffusion', {
        action: 'apply',
        appDossierId: input.appDossierId,
        dryRun: Boolean(input.dryRun),
        ensureDiffusable: Boolean(input.ensureDiffusable),
    })
    return payload.payload
  }
  if (!canUseLocalDiffusionDevApi()) {
    throw new Error("L'application Hektor n'est disponible qu'en local pour l'instant. En production, enregistre d'abord les cibles puis utilise Hektor ou le poste local pour appliquer la diffusion.")
  }
  const response = await fetch('/api/hektor-diffusion/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      appDossierId: input.appDossierId,
      dryRun: Boolean(input.dryRun),
      ensureDiffusable: Boolean(input.ensureDiffusable),
    }),
  })
  const payload = await response.json()
  if (!response.ok || payload?.ok === false) {
    const rawMessage = payload?.error ?? payload?.stderr ?? payload?.stdout ?? 'Unable to apply diffusion targets on Hektor'
    if (isPendingHektorValidationMessage(rawMessage)) {
      throw new Error("En attente de mise a jour Hektor. La demande est bien enregistree, mais Hektor n'a pas encore confirme l'annonce en diffusable.")
    }
    throw new Error(normalizeHektorApplyMessage(rawMessage) || 'Unable to apply diffusion targets on Hektor')
  }
  return payload.payload as {
    app_dossier_id: number
    hektor_annonce_id: string
    dry_run: boolean
    validation_result?: string | null
    observed_validation?: string | null
    diffusable_changed: boolean
    diffusable_result: string
    observed_diffusable?: string | null
    validation_state?: string | null
    validation_approved?: boolean
    waiting_on_hektor?: boolean
    waiting_message?: string | null
    current_enabled_count: number
    targets_count: number
    to_add_count: number
    to_remove_count: number
    applied: Array<Record<string, unknown>>
    failed: Array<Record<string, unknown>>
    pending?: Array<Record<string, unknown>>
  }
}

export async function acceptDiffusionRequestOnHektor(input: { appDossierId: number; dryRun?: boolean }) {
  if (canUseBackendApi()) {
    const payload = await invokeBackendApi<{
      ok: true
      payload: {
        app_dossier_id: number
        hektor_annonce_id: string
        dry_run: boolean
        validation_result?: string | null
        observed_validation?: string | null
        diffusable_changed: boolean
        diffusable_result: string
        observed_diffusable?: string | null
        validation_state?: string | null
        validation_approved?: boolean
        waiting_on_hektor?: boolean
        waiting_message?: string | null
        current_enabled_count: number
        targets_count: number
        to_add_count: number
        to_remove_count: number
        applied: Array<Record<string, unknown>>
        failed: Array<Record<string, unknown>>
        pending?: Array<Record<string, unknown>>
      }
    }>('/hektor-diffusion/accept', {
      method: 'POST',
      body: {
        appDossierId: input.appDossierId,
        dryRun: Boolean(input.dryRun),
      },
    })
    return payload.payload
  }
  assertBackendApiConfigured()
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    const payload = await invokeSupabaseFunction<{
      ok: true
      payload: {
        app_dossier_id: number
        hektor_annonce_id: string
        dry_run: boolean
        validation_result?: string | null
        observed_validation?: string | null
        diffusable_changed: boolean
        diffusable_result: string
        observed_diffusable?: string | null
        validation_state?: string | null
        validation_approved?: boolean
        waiting_on_hektor?: boolean
        waiting_message?: string | null
        current_enabled_count: number
        targets_count: number
        to_add_count: number
        to_remove_count: number
        applied: Array<Record<string, unknown>>
        failed: Array<Record<string, unknown>>
        pending?: Array<Record<string, unknown>>
      }
    }>('hektor-diffusion', {
        action: 'accept',
        appDossierId: input.appDossierId,
        dryRun: Boolean(input.dryRun),
    })
    return payload.payload
  }
  if (!canUseLocalDiffusionDevApi()) {
    throw new Error("L'acceptation Hektor automatique n'est disponible qu'en local pour l'instant.")
  }
  const response = await fetch('/api/hektor-diffusion/accept', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      appDossierId: input.appDossierId,
      dryRun: Boolean(input.dryRun),
    }),
  })
  const payload = await response.json()
  if (!response.ok || payload?.ok === false) {
    const rawMessage = payload?.error ?? payload?.stderr ?? payload?.stdout ?? 'Unable to accept diffusion request on Hektor'
    if (isPendingHektorValidationMessage(rawMessage)) {
      throw new Error("En attente de mise a jour Hektor. L'annonce n'a pas encore ete confirmee diffusable.")
    }
    throw new Error(normalizeHektorApplyMessage(rawMessage) || 'Unable to accept diffusion request on Hektor')
  }
  return payload.payload as {
    app_dossier_id: number
    hektor_annonce_id: string
    dry_run: boolean
    validation_result?: string | null
    observed_validation?: string | null
    diffusable_changed: boolean
    diffusable_result: string
    observed_diffusable?: string | null
    validation_state?: string | null
    validation_approved?: boolean
    waiting_on_hektor?: boolean
    waiting_message?: string | null
    current_enabled_count: number
    targets_count: number
    to_add_count: number
    to_remove_count: number
    applied: Array<Record<string, unknown>>
    failed: Array<Record<string, unknown>>
    pending?: Array<Record<string, unknown>>
  }
}

export async function sendDiffusionDecisionEmail(input: {
  to: string
  subject: string
  bodyText: string
  bodyHtml?: string | null
  fromEmail?: string | null
  fromName?: string | null
  replyTo?: string | null
}) {
  if (canUseBackendApi()) {
    return invokeBackendApi<{ ok: true; messageId?: string | null }>('/notifications/diffusion-decision', {
      method: 'POST',
      body: input,
    })
  }
  const response = await fetch('/api/notifications/diffusion-decision', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.error ?? 'Unable to send diffusion decision email')
  }
  return payload as { ok: true; messageId?: string | null }
}

export async function createAppUser(input: {
  email: string
  password: string
  role: UserProfile['role']
  firstName: string
  lastName: string
  displayName: string
  isActive: boolean
}) {
  if (input.password.trim().length < 8) {
    throw new Error('Le mot de passe temporaire doit contenir au moins 8 caracteres')
  }
  if (canUseBackendApi()) {
    return invokeBackendApi<{ ok: true; userId: string; email: string }>('/admin/users/create', {
      method: 'POST',
      body: input,
    })
  }
  assertBackendApiConfigured()
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    return invokeSupabaseFunction<{ ok: true; userId: string; email: string }>('admin-users', {
      action: 'create',
      ...input,
    })
  }
  const response = await fetch('/api/admin/users/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload?.ok === false) {
    throw new Error(formatCreateUserError(payload?.error ?? 'Unable to create user'))
  }
  return payload as { ok: true; userId: string; email: string }
}

function formatCreateUserError(message: unknown) {
  const text = typeof message === 'string' ? message : JSON.stringify(message ?? '')
  if (text.includes('string_too_short') && text.includes('password')) {
    return 'Le mot de passe temporaire doit contenir au moins 8 caracteres'
  }
  if (text.toLowerCase().includes('password') && text.includes('8')) {
    return 'Le mot de passe temporaire doit contenir au moins 8 caracteres'
  }
  return text || 'Impossible de creer l utilisateur'
}

export async function loadAppUsers() {
  if (canUseBackendApi()) {
    const payload = await invokeBackendApi<{ ok: true; users: UserProfile[] }>('/admin/users/list', {
      method: 'GET',
    })
    return payload.users ?? []
  }
  assertBackendApiConfigured()
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    const payload = await invokeSupabaseFunction<{ ok: true; users: UserProfile[] }>('admin-users', { action: 'list' })
    return payload.users ?? []
  }
  const response = await fetch('/api/admin/users/list')
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.error ?? 'Unable to load users')
  }
  return (payload.users ?? []) as UserProfile[]
}

export async function updateAppUser(input: {
  id: string
  email: string
  role: UserProfile['role']
  firstName: string
  lastName: string
  displayName: string
  isActive: boolean
}) {
  if (canUseBackendApi()) {
    return invokeBackendApi<{ ok: true }>('/admin/users/update', {
      method: 'POST',
      body: input,
    })
  }
  assertBackendApiConfigured()
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    const payload = await invokeSupabaseFunction<{ ok: true }>('admin-users', {
      action: 'update',
      ...input,
    })
    return payload
  }
  const response = await fetch('/api/admin/users/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.error ?? 'Unable to update user')
  }
  return payload as { ok: true }
}

export async function sendPasswordResetEmail(input: { email: string }) {
  if (canUseBackendApi()) {
    return invokeBackendApi<{ ok: true }>('/admin/users/send-reset', {
      method: 'POST',
      body: input,
    })
  }
  assertBackendApiConfigured()
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    const payload = await invokeSupabaseFunction<{ ok: true }>('admin-users', {
      action: 'send-reset',
      ...input,
    })
    return payload
  }
  const response = await fetch('/api/admin/users/send-reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.error ?? 'Unable to send password reset email')
  }
  return payload as { ok: true }
}

const consoleDocumentsBucket = 'hektor-console-documents'

function safeUploadFilename(name: string, fallback: string) {
  const clean = name
    .replace(/[\\/:*?"<>|]+/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
  return clean || fallback
}

function filenameExtension(name: string) {
  const match = name.match(/(\.[a-z0-9]{1,12})$/i)
  return match ? match[1] : ''
}

function filenameStem(name: string) {
  const extension = filenameExtension(name)
  return extension ? name.slice(0, -extension.length) : name
}

async function requireSupabaseUserId() {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const { data, error } = await supabase.auth.getUser()
  if (error || !data.user) throw new Error(error?.message ?? 'Utilisateur non authentifie')
  return data.user.id
}

export async function loadConsoleDocuments(appDossierId: number): Promise<ConsoleDocument[]> {
  if (!hasSupabaseEnv || !supabase) return []
  const { data, error } = await supabase
    .from('app_console_document')
    .select('id,app_dossier_id,hektor_annonce_id,hektor_document_id,document_type,document_name,source,visibility,storage_bucket,storage_path,storage_status,file_size,sha256,mime_type,created_at_hektor,synced_at,last_accessed_at,archive_policy,metadata_json,created_at,updated_at')
    .eq('app_dossier_id', appDossierId)
    .order('document_type', { ascending: true })
    .order('document_name', { ascending: true })
    .limit(300)
  if (error) throw new Error(error.message)
  return (data ?? []) as ConsoleDocument[]
}

export async function loadConsolePhotos(appDossierId: number): Promise<ConsolePhoto[]> {
  if (!hasSupabaseEnv || !supabase) return []
  const { data, error } = await supabase
    .from('app_console_photo')
    .select('id,app_dossier_id,hektor_annonce_id,hektor_photo_id,filename,url_preview,url_hd,visible,legend,sort_order,source,source_json,synced_at,created_at,updated_at')
    .eq('app_dossier_id', appDossierId)
    .order('visible', { ascending: false })
    .order('sort_order', { ascending: true })
    .limit(500)
  if (error) throw new Error(error.message)
  return (data ?? []) as ConsolePhoto[]
}

export async function createSyncHektorPhotosJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id'>
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const { data, error } = await supabase.rpc('app_console_create_sync_photos_job', {
    target_app_dossier_id: input.dossier.app_dossier_id,
    target_hektor_annonce_id: String(input.dossier.hektor_annonce_id),
    job_priority: input.priority ?? 28,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor photos sync job')
  return data as ConsoleJob
}

export async function createUploadHektorPhotoJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id'>
  file: File
  visible: boolean
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const jobId = crypto.randomUUID()
  const originalName = safeUploadFilename(input.file.name, 'photo.jpg')
  const storagePath = `temp/photos/${jobId}/${originalName}`
  const { data: jobData, error: jobError } = await supabase
    .from('app_console_job')
    .insert({
      id: jobId,
      job_type: 'upload_hektor_photo',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        visible: input.visible,
        original_filename: originalName,
        source_filename: input.file.name,
        mime_type: input.file.type || null,
        file_size: input.file.size,
        temp_storage_bucket: consoleDocumentsBucket,
        temp_storage_path: storagePath,
      },
      priority: input.priority ?? 18,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (jobError || !jobData) throw new Error(jobError?.message ?? 'Unable to create Hektor photo upload job')

  const { error: uploadError } = await supabase.storage
    .from(consoleDocumentsBucket)
    .upload(storagePath, input.file, {
      cacheControl: '3600',
      contentType: input.file.type || undefined,
      upsert: false,
    })
  if (uploadError) {
    await supabase.rpc('app_console_fail_own_pending_job', {
      target_job_id: jobData.id,
      failure_message: uploadError.message,
    })
    throw new Error(uploadError.message)
  }

  const { data: updatedJob, error: updateError } = await supabase
    .from('app_console_job')
    .select('*')
    .eq('id', jobData.id)
    .single()
  if (updateError || !updatedJob) throw new Error(updateError?.message ?? 'Unable to reload Hektor photo upload job')
  return updatedJob as ConsoleJob
}

export async function createPrepareConsoleDocumentJob(input: {
  document: Pick<ConsoleDocument, 'id' | 'app_dossier_id' | 'hektor_annonce_id' | 'document_name'>
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'prepare_document_cloud',
      app_dossier_id: input.document.app_dossier_id,
      hektor_annonce_id: input.document.hektor_annonce_id,
      payload_json: {
        document_id: input.document.id,
        document_name: input.document.document_name,
      },
      priority: input.priority ?? 50,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throw new Error(error?.message ?? 'Unable to create document preparation job')
  return data as ConsoleJob
}

export async function createUploadDocumentToHektorJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id'>
  file: File
  visibility: Exclude<ConsoleDocumentVisibility, 'unknown'>
  documentLabel?: string | null
  documentType?: string | null
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const jobId = crypto.randomUUID()
  const originalName = safeUploadFilename(input.file.name, 'document')
  const extension = filenameExtension(originalName)
  const requestedLabel = filenameStem(safeUploadFilename(input.documentLabel ?? '', ''))
  const uploadFilename = safeUploadFilename(requestedLabel ? `${requestedLabel}${extension}` : originalName, originalName)
  const storagePath = `temp/uploads/${jobId}/${uploadFilename}`
  const { data: jobData, error: jobError } = await supabase
    .from('app_console_job')
    .insert({
      id: jobId,
      job_type: 'upload_document_to_hektor',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        visibility: input.visibility,
        document_type: input.documentType ?? null,
        original_filename: uploadFilename,
        source_filename: input.file.name,
        document_label: requestedLabel || filenameStem(originalName),
        mime_type: input.file.type || null,
        file_size: input.file.size,
        temp_storage_bucket: consoleDocumentsBucket,
        temp_storage_path: storagePath,
      },
      priority: input.priority ?? 40,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (jobError || !jobData) throw new Error(jobError?.message ?? 'Unable to create Hektor upload job')

  const { error: uploadError } = await supabase.storage
    .from(consoleDocumentsBucket)
    .upload(storagePath, input.file, {
      cacheControl: '3600',
      contentType: input.file.type || undefined,
      upsert: false,
    })
  if (uploadError) {
    await supabase.rpc('app_console_fail_own_pending_job', {
      target_job_id: jobData.id,
      failure_message: uploadError.message,
    })
    throw new Error(uploadError.message)
  }

  const { data: updatedJob, error: updateError } = await supabase
    .from('app_console_job')
    .select('*')
    .eq('id', jobData.id)
    .single()
  if (updateError || !updatedJob) throw new Error(updateError?.message ?? 'Unable to reload Hektor upload job')
  return updatedJob as ConsoleJob
}

export async function createDeleteDocumentFromHektorJob(input: {
  document: Pick<ConsoleDocument, 'id' | 'app_dossier_id' | 'hektor_annonce_id' | 'document_name'>
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'delete_document_from_hektor',
      app_dossier_id: input.document.app_dossier_id,
      hektor_annonce_id: input.document.hektor_annonce_id,
      payload_json: {
        document_id: input.document.id,
        document_name: input.document.document_name,
      },
      priority: input.priority ?? 25,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor delete job')
  return data as ConsoleJob
}

export async function createPrepareArchivedAnnonceDetailJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'numero_dossier' | 'titre_bien'>
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'prepare_archived_annonce_detail',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        numero_dossier: input.dossier.numero_dossier ?? null,
        titre_bien: input.dossier.titre_bien ?? null,
        ttl_hours: 24,
      },
      priority: input.priority ?? 32,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throw new Error(error?.message ?? 'Unable to create archived annonce detail preparation job')
  return data as ConsoleJob
}

export async function createPrepareHistoricalAnnonceDetailJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'numero_dossier' | 'titre_bien'>
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'prepare_historical_annonce_detail',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        numero_dossier: input.dossier.numero_dossier ?? null,
        titre_bien: input.dossier.titre_bien ?? null,
        ttl_hours: 24,
      },
      priority: input.priority ?? 32,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throw new Error(error?.message ?? 'Unable to create historical annonce detail preparation job')
  return data as ConsoleJob
}

export async function createLinkHektorMandantJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'negociateur_email'>
  contactId: string
  contactLabel?: string | null
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const cleanContactId = input.contactId.trim()
  if (!/^\d+$/.test(cleanContactId)) throw new Error('ID contact Hektor numerique requis')
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'link_hektor_mandant',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        contact_id: cleanContactId,
        contact_label: input.contactLabel?.trim() || null,
        hektor_user_email: input.dossier.negociateur_email ?? null,
      },
      priority: input.priority ?? 18,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor mandant link job')
  return data as ConsoleJob
}

export type HektorMandantContactInput = {
  civility?: string | null
  lastName: string
  firstName?: string | null
  email: string
  phone?: string | null
  address?: string | null
  postalCode?: string | null
  city?: string | null
}

export type HektorContactIdentityInput = {
  civility?: string | null
  lastName: string
  firstName?: string | null
  companyName?: string | null
  legalForm?: string | null
  siret?: string | null
  partnerJobId?: string | null
  website?: string | null
  spouseLastName?: string | null
  spouseFirstName?: string | null
  spouseEmail?: string | null
  spousePhone?: string | null
  spouseAddress?: string | null
  spousePostalCode?: string | null
  spouseCity?: string | null
  email?: string | null
  phone?: string | null
  phoneSecondary?: string | null
  address?: string | null
  postalCode?: string | null
  city?: string | null
  birthDate?: string | null
  birthPlace?: string | null
  maritalStatus?: string | null
  contactKind?: string | null
  personType?: string | null
  sourceId?: string | null
  categoryId?: string | null
  comments?: string | null
  sendRgpdEmail?: boolean | null
  crmMandateSummaryEnabled?: boolean | null
  crmMandateExpirationEnabled?: boolean | null
  crmBirthdayEnabled?: boolean | null
  hektorUserEmail?: string | null
  hektorUserId?: string | null
  hektorUserLabel?: string | null
  hektorNegotiatorId?: string | null
  hektorAgencyId?: string | null
  hektorAgencyUserId?: string | null
  hektorAgencyLabel?: string | null
  contactNextStep?: {
    kind?: string | null
    enabled?: boolean | null
    offerCode?: string | null
    propertyTypeIds?: string[] | null
    city?: string | null
    postalCode?: string | null
    priceMin?: string | null
    priceMax?: string | null
    surfaceMin?: string | null
    surfaceMax?: string | null
    roomsMin?: string | null
    roomsMax?: string | null
    bedroomsMin?: string | null
    bedroomsMax?: string | null
    landSurfaceMin?: string | null
    landSurfaceMax?: string | null
    action?: string | null
    hektorAnnonceId?: string | null
  } | null
}

export type OwnerAnnonceSearchOption = Pick<
  Dossier,
  | 'app_dossier_id'
  | 'hektor_annonce_id'
  | 'numero_dossier'
  | 'numero_mandat'
  | 'titre_bien'
  | 'ville'
  | 'code_postal'
  | 'commercial_nom'
  | 'agence_nom'
  | 'statut_annonce'
  | 'archive'
>

function normalizeOwnerAnnonceOption(row: OwnerAnnonceSearchOption): OwnerAnnonceSearchOption {
  return {
    ...row,
    app_dossier_id: Number(row.app_dossier_id),
    hektor_annonce_id: Number(row.hektor_annonce_id),
  }
}

function matchesOwnerAnnonceSearch(item: OwnerAnnonceSearchOption, rawSearch: string) {
  const search = normalizeSearchTerm(rawSearch).replace(/\s+/g, ' ').trim().toLowerCase()
  if (!search) return true
  const haystack = [
    item.hektor_annonce_id,
    item.numero_dossier,
    item.numero_mandat,
    item.titre_bien,
    item.ville,
    item.code_postal,
    item.commercial_nom,
    item.agence_nom,
    item.statut_annonce,
  ].map((value) => String(value ?? '').toLowerCase()).join(' ')
  return haystack.includes(search)
}

export async function searchOwnerAnnonceOptions(input: {
  search?: string
  scope?: DataScope | null
  limit?: number
}): Promise<OwnerAnnonceSearchOption[]> {
  const search = normalizeSearchTerm(input.search ?? '').replace(/\s+/g, ' ').trim()
  const limit = Math.min(Math.max(input.limit ?? 12, 1), 30)
  const select = 'app_dossier_id,hektor_annonce_id,numero_dossier,numero_mandat,titre_bien,ville,code_postal,commercial_nom,agence_nom,statut_annonce,archive'

  if (!hasSupabaseEnv || !supabase) {
    return filterByNegotiatorEmail(mockDossiers, input.scope)
      .filter((item) => (item.archive ?? '0') !== '1')
      .filter((item) => matchesOwnerAnnonceSearch(item, search))
      .slice(0, limit)
      .map(normalizeOwnerAnnonceOption)
  }

  let query = applyNegotiatorScopeToQuery(
    supabase
      .from(dossiersCurrentView)
      .select(select)
      .eq('archive', '0')
      .order('date_maj', { ascending: false, nullsFirst: false })
      .order('hektor_annonce_id', { ascending: false })
      .limit(limit),
    input.scope,
  )

  if (search) {
    const ilike = `%${search}%`
    const filters = [
      /^\d+$/.test(search) ? `hektor_annonce_id.eq.${search}` : null,
      `numero_dossier.ilike.${ilike}`,
      `numero_mandat.ilike.${ilike}`,
      `titre_bien.ilike.${ilike}`,
      `ville.ilike.${ilike}`,
      `code_postal.ilike.${ilike}`,
      `commercial_nom.ilike.${ilike}`,
      `agence_nom.ilike.${ilike}`,
    ].filter(Boolean).join(',')
    query = query.or(filters)
  }

  const { data, error } = await query
  if (error || !data) throw new Error(error?.message ?? 'Unable to search annonces')
  return (data as OwnerAnnonceSearchOption[]).map(normalizeOwnerAnnonceOption)
}

export type MandantContactSearchOption = Pick<AppContact,
  | 'hektor_contact_id'
  | 'negociateur_email'
  | 'commercial_nom'
  | 'agence_nom'
  | 'civilite'
  | 'nom'
  | 'prenom'
  | 'display_name'
  | 'archive'
  | 'email'
  | 'phone_primary'
  | 'phone_secondary'
  | 'ville'
  | 'code_postal'
  | 'typologies_json'
  | 'relation_roles_json'
  | 'linked_annonce_count'
>

function normalizeMandantContactOption(row: MandantContactSearchOption): MandantContactSearchOption {
  return {
    ...row,
    hektor_contact_id: String(row.hektor_contact_id),
    linked_annonce_count: Number(row.linked_annonce_count ?? 0),
  }
}

export async function searchMandantContactOptions(input: {
  search?: string
  scope?: DataScope | null
  limit?: number
}): Promise<MandantContactSearchOption[]> {
  const search = normalizeSearchTerm(input.search ?? '').replace(/\s+/g, ' ').trim()
  const limit = Math.min(Math.max(input.limit ?? 12, 1), 30)

  if (!hasSupabaseEnv || !supabase) return []

  let query = applyNegotiatorScopeToQuery(
    supabase
      .from(contactsCurrentView)
      .select(contactsListingSelect)
      .eq('archive', false)
      .order('date_maj', { ascending: false, nullsFirst: false })
      .order('display_name', { ascending: true })
      .limit(limit),
    input.scope,
  )

  if (search) {
    const ilike = `%${search}%`
    query = /^\d+$/.test(search)
      ? query.or(`hektor_contact_id.eq.${search},search_text.ilike.${ilike}`)
      : query.ilike('search_text', ilike)
  }

  const { data, error } = await query
  if (error || !data) throw new Error(error?.message ?? 'Unable to search mandant contacts')
  return (data as MandantContactSearchOption[]).map(normalizeMandantContactOption)
}

function cleanOptionalText(value: string | null | undefined) {
  const text = value?.trim() ?? ''
  return text || null
}

function escapePostgrestFilterValue(value: string) {
  return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
}

function hContactPayload(contact: HektorContactIdentityInput) {
  const hektorUserId = cleanOptionalText(contact.hektorUserId)
  const agencyUserId = cleanOptionalText(contact.hektorAgencyUserId)
  const hektorUserEmail = cleanOptionalText(contact.hektorUserEmail)
  return {
    civilite: cleanOptionalText(contact.civility),
    last_name: contact.lastName.trim(),
    first_name: cleanOptionalText(contact.firstName),
    company_name: cleanOptionalText(contact.companyName),
    sociale: cleanOptionalText(contact.companyName),
    legal_form: cleanOptionalText(contact.legalForm),
    juridique: cleanOptionalText(contact.legalForm),
    siret: cleanOptionalText(contact.siret),
    partner_job_id: cleanOptionalText(contact.partnerJobId),
    metier: cleanOptionalText(contact.partnerJobId),
    website: cleanOptionalText(contact.website),
    url: cleanOptionalText(contact.website),
    spouse_last_name: cleanOptionalText(contact.spouseLastName),
    spouse_first_name: cleanOptionalText(contact.spouseFirstName),
    spouse_email: cleanOptionalText(contact.spouseEmail),
    spouse_phone: cleanOptionalText(contact.spousePhone),
    spouse_address: cleanOptionalText(contact.spouseAddress),
    spouse_postal_code: cleanOptionalText(contact.spousePostalCode),
    spouse_city: cleanOptionalText(contact.spouseCity),
    email: cleanOptionalText(contact.email),
    phone: cleanOptionalText(contact.phone),
    phone_secondary: cleanOptionalText(contact.phoneSecondary),
    address: cleanOptionalText(contact.address),
    postal_code: cleanOptionalText(contact.postalCode),
    city: cleanOptionalText(contact.city),
    birth_date: cleanOptionalText(contact.birthDate) ?? undefined,
    birth_place: cleanOptionalText(contact.birthPlace) ?? undefined,
    marital_status: cleanOptionalText(contact.maritalStatus) ?? undefined,
    contact_kind: cleanOptionalText(contact.contactKind) ?? 'acquereur',
    person_type: cleanOptionalText(contact.personType) ?? 'personne_seule',
    id_source: cleanOptionalText(contact.sourceId),
    category_id: cleanOptionalText(contact.categoryId),
    comments: cleanOptionalText(contact.comments),
    send_rgpd_email: contact.sendRgpdEmail === false ? false : true,
    crm_mandate_summary_enabled: typeof contact.crmMandateSummaryEnabled === 'boolean' ? contact.crmMandateSummaryEnabled : null,
    crm_mandate_expiration_enabled: typeof contact.crmMandateExpirationEnabled === 'boolean' ? contact.crmMandateExpirationEnabled : null,
    crm_birthday_enabled: typeof contact.crmBirthdayEnabled === 'boolean' ? contact.crmBirthdayEnabled : null,
    hektor_user_email: hektorUserEmail,
    hektor_user_id: hektorUserId,
    target_hektor_user_id: hektorUserId,
    target_hektor_user_label: cleanOptionalText(contact.hektorUserLabel),
    target_hektor_user_email: hektorUserEmail,
    target_hektor_negociateur_id: cleanOptionalText(contact.hektorNegotiatorId),
    target_hektor_agence_id: cleanOptionalText(contact.hektorAgencyId),
    target_agency_id_user: cleanOptionalText(contact.hektorAgencyUserId),
    target_agency_label: cleanOptionalText(contact.hektorAgencyLabel),
    contact_next_step: contact.contactNextStep ?? null,
  }
}

export async function createHektorContactJob(input: {
  contact: HektorContactIdentityInput
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const payload = hContactPayload(input.contact)
  if (!payload.last_name) throw new Error('Nom contact requis')
  if (!payload.email && !payload.phone && !payload.phone_secondary) throw new Error('Email ou telephone requis')
  if (!payload.hektor_user_id && !payload.hektor_user_email) throw new Error('Compte Hektor requis pour creer le contact')
  const { data, error } = await supabase.rpc('app_console_create_contact_job', {
    contact_payload: payload,
    job_priority: input.priority ?? 18,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor contact job')
  return data as ConsoleJob
}

export async function createUpdateHektorContactJob(input: {
  contactId: string
  contact: HektorContactIdentityInput
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const cleanContactId = input.contactId.trim()
  if (!/^\d+$/.test(cleanContactId)) throw new Error('ID contact Hektor numerique requis')
  const payload = {
    ...hContactPayload(input.contact),
    hektor_contact_id: cleanContactId,
    contact_id: cleanContactId,
  }
  if (!payload.last_name) throw new Error('Nom contact requis')
  if (!payload.hektor_user_id && !payload.hektor_user_email) throw new Error('Compte Hektor requis pour modifier le contact')
  const { data, error } = await supabase.rpc('app_console_create_update_contact_job', {
    target_contact_id: cleanContactId,
    contact_payload: payload,
    job_priority: input.priority ?? 16,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor contact update job')
  return data as ConsoleJob
}

export async function createDeleteHektorContactJob(input: {
  contactId: string
  reason?: string
  confirmText: string
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const cleanContactId = input.contactId.trim()
  if (!/^\d+$/.test(cleanContactId)) throw new Error('ID contact Hektor numerique requis')
  const { data, error } = await supabase.rpc('app_console_create_delete_contact_job', {
    target_contact_id: cleanContactId,
    delete_reason: input.reason?.trim() || null,
    confirm_text: input.confirmText.trim(),
    job_priority: input.priority ?? 6,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor contact delete job')
  return data as ConsoleJob
}

export async function findContactDuplicateCandidates(input: {
  email?: string | null
  phone?: string | null
  lastName?: string | null
  firstName?: string | null
}, limit = 6): Promise<AppContact[]> {
  if (!hasSupabaseEnv || !supabase) return []
  const email = cleanOptionalText(input.email)
  const phone = cleanOptionalText(input.phone)
  const filters = [
    email ? `email.ilike.${escapePostgrestFilterValue(email)}` : null,
    phone ? `phone_primary.eq.${escapePostgrestFilterValue(phone)}` : null,
    phone ? `phone_secondary.eq.${escapePostgrestFilterValue(phone)}` : null,
  ].filter((value): value is string => Boolean(value))
  if (filters.length === 0) return []
  const { data, error } = await supabase
    .from(contactsCurrentView)
    .select(contactsListingSelect)
    .or(filters.join(','))
    .order('archive', { ascending: true })
    .order('linked_annonce_count', { ascending: false })
    .order('date_maj', { ascending: false, nullsFirst: false })
    .limit(limit)
  if (error || !data) {
    console.warn('Contact duplicate check skipped', error?.message ?? 'Unable to search contact duplicates')
    return []
  }
  return ((data ?? []) as unknown as AppContact[]).map(normalizeContactRow)
}

export async function createHektorMandantContactJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'negociateur_email'>
  contact: HektorMandantContactInput
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const payload = {
    civilite: input.contact.civility?.trim() || null,
    last_name: input.contact.lastName.trim(),
    first_name: input.contact.firstName?.trim() || null,
    email: input.contact.email.trim(),
    phone: input.contact.phone?.trim() || null,
    address: input.contact.address?.trim() || null,
    postal_code: input.contact.postalCode?.trim() || null,
    city: input.contact.city?.trim() || null,
    hektor_user_email: input.dossier.negociateur_email ?? null,
  }
  const { data, error } = await supabase.rpc('app_console_create_mandant_contact_job', {
    target_app_dossier_id: input.dossier.app_dossier_id,
    target_hektor_annonce_id: String(input.dossier.hektor_annonce_id),
    contact_payload: payload,
    job_priority: input.priority ?? 18,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor mandant contact job')
  return data as ConsoleJob
}

export async function createUpdateHektorMandantContactJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'negociateur_email'>
  contactId: string
  contact: HektorMandantContactInput
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const cleanContactId = input.contactId.trim()
  if (!/^\d+$/.test(cleanContactId)) throw new Error('ID contact Hektor numerique requis')
  const payload = {
    hektor_contact_id: cleanContactId,
    contact_id: cleanContactId,
    civilite: input.contact.civility?.trim() || null,
    last_name: input.contact.lastName.trim(),
    first_name: input.contact.firstName?.trim() || null,
    email: input.contact.email.trim(),
    phone: input.contact.phone?.trim() || null,
    address: input.contact.address?.trim() || null,
    postal_code: input.contact.postalCode?.trim() || null,
    city: input.contact.city?.trim() || null,
    hektor_user_email: input.dossier.negociateur_email ?? null,
  }
  const { data, error } = await supabase.rpc('app_console_create_update_mandant_contact_job', {
    target_app_dossier_id: input.dossier.app_dossier_id,
    target_hektor_annonce_id: String(input.dossier.hektor_annonce_id),
    target_contact_id: cleanContactId,
    contact_payload: payload,
    job_priority: input.priority ?? 16,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor mandant update job')
  return data as ConsoleJob
}

export type HektorAnnonceUpdateFields = {
  propertyProfile?: string | null
  title?: string | null
  description?: string | null
  address?: string | null
  postalCode?: string | null
  city?: string | null
  building?: string | null
  transport?: string | null
  proximity?: string | null
  environment?: string | null
  latitude?: string | number | null
  longitude?: string | number | null
  price?: string | number | null
  netSellerPrice?: string | number | null
  surface?: string | number | null
  carrezSurface?: string | number | null
  roomCount?: string | number | null
  bedroomCount?: string | number | null
  levelCount?: string | number | null
  bathroomCount?: string | number | null
  showerRoomCount?: string | number | null
  wcCount?: string | number | null
  kitchen?: string | null
  exposure?: string | null
  view?: string | null
  interiorState?: string | null
  exteriorState?: string | null
  landSurface?: string | number | null
  gardenSurface?: string | number | null
  terraceCount?: string | number | null
  garageCount?: string | number | null
  garageSurface?: string | number | null
  parkingInsideCount?: string | number | null
  parkingOutsideCount?: string | number | null
  pool?: string | number | null
  dpeValue?: string | null
  gesValue?: string | null
  constructionYear?: string | number | null
  diagnosticRiskComment?: string | null
  diagnosticNote?: string | null
  coproLots?: string | number | null
  coproCharges?: string | number | null
  coproQuotePart?: string | number | null
  coproWorksFund?: string | number | null
  mandateNumber?: string | null
  mandateType?: string | null
  mandateStartDate?: string | null
  mandateEndDate?: string | null
  fees?: string | number | null
}

export type HektorMandatAutoNumberInput = {
  typeMandat?: string | null
  subTypeMandat?: string | null
  dateDebut?: string | null
  dureeMandat?: string | number | null
  taciteReconduction?: boolean | string | number | null
  mandantContactIds?: string[]
}

export async function createUpdateHektorAnnonceFieldsJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id'>
  fields: HektorAnnonceUpdateFields
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const cleanFields = {
    property_profile: input.fields.propertyProfile?.trim() || null,
    title: input.fields.title?.trim() || null,
    description: input.fields.description?.trim() || null,
    address: input.fields.address?.trim() || null,
    postal_code: input.fields.postalCode?.trim() || null,
    city: input.fields.city?.trim() || null,
    building: input.fields.building?.trim() || null,
    transport: input.fields.transport?.trim() || null,
    proximity: input.fields.proximity?.trim() || null,
    environment: input.fields.environment?.trim() || null,
    latitude: input.fields.latitude == null ? null : String(input.fields.latitude).trim() || null,
    longitude: input.fields.longitude == null ? null : String(input.fields.longitude).trim() || null,
    price: input.fields.price == null ? null : String(input.fields.price).trim() || null,
    net_seller_price: input.fields.netSellerPrice == null ? null : String(input.fields.netSellerPrice).trim() || null,
    surface: input.fields.surface == null ? null : String(input.fields.surface).trim() || null,
    carrez_surface: input.fields.carrezSurface == null ? null : String(input.fields.carrezSurface).trim() || null,
    room_count: input.fields.roomCount == null ? null : String(input.fields.roomCount).trim() || null,
    bedroom_count: input.fields.bedroomCount == null ? null : String(input.fields.bedroomCount).trim() || null,
    bathroom_count: input.fields.bathroomCount == null ? null : String(input.fields.bathroomCount).trim() || null,
    shower_room_count: input.fields.showerRoomCount == null ? null : String(input.fields.showerRoomCount).trim() || null,
    wc_count: input.fields.wcCount == null ? null : String(input.fields.wcCount).trim() || null,
    kitchen: input.fields.kitchen?.trim() || null,
    exposure: input.fields.exposure?.trim() || null,
    view: input.fields.view?.trim() || null,
    interior_state: input.fields.interiorState?.trim() || null,
    exterior_state: input.fields.exteriorState?.trim() || null,
    land_surface: input.fields.landSurface == null ? null : String(input.fields.landSurface).trim() || null,
    garden_surface: input.fields.gardenSurface == null ? null : String(input.fields.gardenSurface).trim() || null,
    terrace_count: input.fields.terraceCount == null ? null : String(input.fields.terraceCount).trim() || null,
    garage_count: input.fields.garageCount == null ? null : String(input.fields.garageCount).trim() || null,
    garage_surface: input.fields.garageSurface == null ? null : String(input.fields.garageSurface).trim() || null,
    parking_inside_count: input.fields.parkingInsideCount == null ? null : String(input.fields.parkingInsideCount).trim() || null,
    parking_outside_count: input.fields.parkingOutsideCount == null ? null : String(input.fields.parkingOutsideCount).trim() || null,
    pool: input.fields.pool == null ? null : String(input.fields.pool).trim() || null,
    dpe_value: input.fields.dpeValue?.trim() || null,
    ges_value: input.fields.gesValue?.trim() || null,
    construction_year: input.fields.constructionYear == null ? null : String(input.fields.constructionYear).trim() || null,
    diagnostic_risk_comment: input.fields.diagnosticRiskComment?.trim() || input.fields.diagnosticNote?.trim() || null,
    copro_lots: input.fields.coproLots == null ? null : String(input.fields.coproLots).trim() || null,
    copro_charges: input.fields.coproCharges == null ? null : String(input.fields.coproCharges).trim() || null,
    copro_quote_part: input.fields.coproQuotePart == null ? null : String(input.fields.coproQuotePart).trim() || null,
    copro_works_fund: input.fields.coproWorksFund == null ? null : String(input.fields.coproWorksFund).trim() || null,
    mandate_number: input.fields.mandateNumber?.trim() || null,
    mandate_type: input.fields.mandateType?.trim() || null,
    mandate_start_date: input.fields.mandateStartDate?.trim() || null,
    mandate_end_date: input.fields.mandateEndDate?.trim() || null,
    fees: input.fields.fees == null ? null : String(input.fields.fees).trim() || null,
  }
  const updateFields = Object.fromEntries(Object.entries(cleanFields).filter(([, value]) => value !== null))
  if (Object.keys(updateFields).length === 0) throw new Error('Aucune modification a envoyer')
  const { data, error } = await supabase.rpc('app_console_create_update_annonce_job', {
    target_app_dossier_id: input.dossier.app_dossier_id,
    target_hektor_annonce_id: String(input.dossier.hektor_annonce_id),
    update_fields: updateFields,
    update_priority: input.priority ?? 15,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor annonce update job')
  return data as ConsoleJob
}

export async function createHektorMandatAutoNumberJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'negociateur_email'>
  mandat?: HektorMandatAutoNumberInput
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const tacite = input.mandat?.taciteReconduction
  const payload = {
    type_mandat: input.mandat?.typeMandat?.trim() || 'Mandat de vente',
    sub_type_mandat: input.mandat?.subTypeMandat?.trim() || input.mandat?.typeMandat?.trim() || 'Mandat de vente',
    date_debut: input.mandat?.dateDebut?.trim() || null,
    duree_mandat: input.mandat?.dureeMandat == null ? '12' : String(input.mandat.dureeMandat).trim() || '12',
    tacite_reconduction: tacite === false || tacite === 'false' || tacite === '0' || tacite === 0 ? '0' : '1',
    mandant_contact_ids: input.mandat?.mandantContactIds ?? [],
    hektor_user_email: input.dossier.negociateur_email ?? null,
  }
  const { data, error } = await supabase.rpc('app_console_create_mandat_auto_number_job', {
    target_app_dossier_id: input.dossier.app_dossier_id,
    target_hektor_annonce_id: String(input.dossier.hektor_annonce_id),
    mandat_payload: payload,
    job_priority: input.priority ?? 12,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor mandat number job')
  return data as ConsoleJob
}

export async function createDeleteHektorAnnonceJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'numero_dossier' | 'titre_bien'>
  reason?: string
  confirmText: string
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const { data, error } = await supabase.rpc('app_console_create_delete_annonce_job', {
    target_app_dossier_id: input.dossier.app_dossier_id,
    target_hektor_annonce_id: String(input.dossier.hektor_annonce_id),
    delete_reason: input.reason?.trim() || null,
    confirm_text: input.confirmText.trim(),
    delete_priority: input.priority ?? 5,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor annonce delete job')
  return data as ConsoleJob
}

function throwConsoleAdminJobError(error: { message?: string; code?: string; details?: string } | null | undefined, fallback: string): never {
  const text = `${error?.code ?? ''} ${error?.message ?? ''} ${error?.details ?? ''}`.toLowerCase()
  if (text.includes('app_console_job_active_admin_annonce_idx') || text.includes('duplicate key')) {
    throw new Error('Une action Hektor est deja en cours pour cette annonce. Attends la fin du traitement avant de relancer.')
  }
  throw new Error(error?.message ?? fallback)
}

export async function createRestoreHektorAnnonceJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'numero_dossier' | 'titre_bien'>
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'restore_hektor_annonce',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        numero_dossier: input.dossier.numero_dossier ?? null,
        titre_bien: input.dossier.titre_bien ?? null,
        target_archive: '0',
      },
      priority: input.priority ?? 8,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throwConsoleAdminJobError(error, 'Unable to create Hektor restore job')
  return data as ConsoleJob
}

export type ArchiveHektorAnnonceMainChoice = 'choiceVendu' | 'choiceAutre'
export type ArchiveHektorAnnonceSubChoice =
  | 'agence'
  | 'confrere'
  | 'proprietaire'
  | 'concurence'
  | 'vendre_seule'
  | 'annuler_vente'
  | 'non_renouvele'
  | 'mandat_non_obtenu'
  | 'autre'

export async function createArchiveHektorAnnonceJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'numero_dossier' | 'titre_bien'>
  mainChoice: ArchiveHektorAnnonceMainChoice
  subChoice: ArchiveHektorAnnonceSubChoice
  otherText?: string
  price?: string
  confrere?: string
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'archive_hektor_annonce',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        numero_dossier: input.dossier.numero_dossier ?? null,
        titre_bien: input.dossier.titre_bien ?? null,
        target_archive: '1',
        archive_main_choice: input.mainChoice,
        archive_sub_choice: input.subChoice,
        archive_other_text: input.otherText?.trim() || null,
        archive_price: input.price?.trim() || null,
        archive_confrere: input.confrere?.trim() || null,
      },
      priority: input.priority ?? 8,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throwConsoleAdminJobError(error, 'Unable to create Hektor archive job')
  return data as ConsoleJob
}

export type HektorAnnonceStatusTarget = 'active' | 'offer' | 'compromise' | 'sold' | 'closed'

export async function createChangeHektorAnnonceStatusJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'numero_dossier' | 'titre_bien' | 'prix' | 'numero_mandat' | 'negociateur_email'>
  targetStatus: HektorAnnonceStatusTarget
  amount?: string
  salePrice?: string
  transactionDate?: string
  signatureDate?: string
  validityDays?: string
  retractionDays?: string
  selectedMandat?: string
  buyerContactId?: string
  buyerNotaryId?: string
  buyerFees?: string
  buyerFeesRate?: string
  netSellerPrice?: string
  sequestration?: string
  closeReason?: string
  closeState?: string
  closePrice?: string
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const payload = {
    numero_dossier: input.dossier.numero_dossier ?? null,
    numero_mandat: input.dossier.numero_mandat ?? null,
    titre_bien: input.dossier.titre_bien ?? null,
    negociateur_email: input.dossier.negociateur_email ?? null,
    target_status: input.targetStatus,
    amount: input.amount?.trim() || null,
    sale_price: input.salePrice?.trim() || null,
    transaction_date: input.transactionDate?.trim() || null,
    signature_date: input.signatureDate?.trim() || null,
    validity_days: input.validityDays?.trim() || null,
    retraction_days: input.retractionDays?.trim() || null,
    selected_mandat: input.selectedMandat?.trim() || null,
    buyer_contact_id: input.buyerContactId?.trim() || null,
    buyer_notary_id: input.buyerNotaryId?.trim() || null,
    buyer_fees: input.buyerFees?.trim() || null,
    buyer_fees_rate: input.buyerFeesRate?.trim() || null,
    net_seller_price: input.netSellerPrice?.trim() || null,
    sequestration: input.sequestration?.trim() || null,
    close_reason: input.closeReason?.trim() || null,
    close_state: input.closeState?.trim() || null,
    close_price: input.closePrice?.trim() || null,
  }
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'change_hektor_annonce_status',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: payload,
      priority: input.priority ?? 7,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throwConsoleAdminJobError(error, 'Unable to create Hektor status job')
  return data as ConsoleJob
}

export async function createAssignHektorAnnonceNegotiatorJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id'> & Partial<Pick<Dossier, 'numero_dossier' | 'titre_bien'>>
  agency?: Pick<HektorAgencyOption, 'idAgence' | 'idUser' | 'label'> | null
  negotiator: Pick<HektorNegotiatorOption, 'idUser' | 'label' | 'email' | 'agenceNom' | 'hektorNegociateurId' | 'hektorAgenceId' | 'agenceIdUser'>
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  const userId = await requireSupabaseUserId()
  const targetId = String(input.negotiator.idUser ?? '').trim()
  if (!/^\d+$/.test(targetId)) throw new Error('Choisis un negociateur Hektor valide.')
  const { data, error } = await supabase
    .from('app_console_job')
    .insert({
      job_type: 'assign_hektor_annonce_negotiator',
      app_dossier_id: input.dossier.app_dossier_id,
      hektor_annonce_id: String(input.dossier.hektor_annonce_id),
      payload_json: {
        numero_dossier: input.dossier.numero_dossier ?? null,
        titre_bien: input.dossier.titre_bien ?? null,
        target_hektor_user_id: targetId,
        target_hektor_user_label: input.negotiator.label ?? null,
        target_hektor_user_email: input.negotiator.email ?? null,
        target_hektor_negociateur_id: input.negotiator.hektorNegociateurId ?? null,
        target_hektor_agence_id: input.negotiator.hektorAgenceId ?? input.agency?.idAgence ?? null,
        target_agency_id_user: input.agency?.idUser ?? input.negotiator.agenceIdUser ?? null,
        target_agency_label: input.agency?.label ?? input.negotiator.agenceNom ?? null,
      },
      priority: input.priority ?? 9,
      requested_by: userId,
    })
    .select('*')
    .single()
  if (error || !data) throwConsoleAdminJobError(error, 'Unable to create Hektor negotiator assignment job')
  return data as ConsoleJob
}

export type MatterportConsoleAction = 'online' | 'offline' | 'archive' | 'reactivate'

export async function createMatterportActionJob(input: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id'>
  model: Pick<MatterportModelLink, 'matterport_model_id' | 'matterport_name' | 'matterport_url'>
  action: MatterportConsoleAction
  priority?: number
}): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const modelId = input.model.matterport_model_id.trim()
  if (!/^[A-Za-z0-9_-]+$/.test(modelId)) throw new Error('ID Matterport invalide')
  const { data, error } = await supabase.rpc('app_console_create_matterport_action_job', {
    target_app_dossier_id: input.dossier.app_dossier_id,
    target_hektor_annonce_id: String(input.dossier.hektor_annonce_id),
    target_matterport_model_id: modelId,
    matterport_action: input.action,
    job_priority: input.priority ?? 18,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Matterport action job')
  return data as ConsoleJob
}

const hektorActionJobTypes: ConsoleJobType[] = [
  'create_hektor_draft_annonce',
  'delete_hektor_annonce',
  'archive_hektor_annonce',
  'restore_hektor_annonce',
  'change_hektor_annonce_status',
  'assign_hektor_annonce_negotiator',
  'update_hektor_annonce_fields',
  'create_hektor_contact',
  'update_hektor_contact',
  'delete_hektor_contact',
  'create_hektor_mandant_contact',
  'update_hektor_mandant_contact',
  'create_hektor_mandat_auto_number',
  'link_hektor_mandant',
  'matterport_online',
  'matterport_offline',
  'matterport_archive',
  'matterport_reactivate',
  'prepare_document_cloud',
  'upload_document_to_hektor',
  'delete_document_from_hektor',
  'sync_hektor_photos',
  'upload_hektor_photo',
  'prepare_archived_annonce_detail',
  'prepare_historical_annonce_detail',
  'refresh_console_contact_data',
]

export async function loadActiveHektorActionJobs(): Promise<ConsoleJob[]> {
  if (!hasSupabaseEnv || !supabase) return []
  const { data, error } = await supabase
    .from('app_console_job')
    .select('*')
    .in('job_type', hektorActionJobTypes)
    .in('status', ['pending', 'running'])
    .order('requested_at', { ascending: false })
    .limit(25)
  if (error) throw new Error(error.message)
  return (data ?? []) as ConsoleJob[]
}

export async function loadConsoleJobsByIds(ids: string[]): Promise<ConsoleJob[]> {
  if (!hasSupabaseEnv || !supabase || ids.length === 0) return []
  const uniqueIds = Array.from(new Set(ids.filter(Boolean)))
  if (uniqueIds.length === 0) return []
  const { data, error } = await supabase
    .from('app_console_job')
    .select('*')
    .in('id', uniqueIds)
  if (error) throw new Error(error.message)
  return (data ?? []) as ConsoleJob[]
}

export type HektorDraftAnnonceJobInput = {
  title?: string | null
  description?: string | null
  agenceNom?: string | null
  hektorUserId?: string | null
  hektorNegociateurId?: string | null
  hektorUserLabel?: string | null
  hektorUserEmail?: string | null
  creationStatus?: 'active' | 'estimation'
  propertyType?: string | null
  propertyProfile?: string | null
  hektorIdType?: string | number | null
  offerType?: 'sale' | 'rental'
  address?: string | null
  postalCode?: string | null
  city?: string | null
  price?: string | number | null
  netSellerPrice?: string | number | null
  surface?: string | number | null
  carrezSurface?: string | number | null
  livingSurface?: string | number | null
  roomCount?: string | number | null
  bedroomCount?: string | number | null
  levelCount?: string | number | null
  bathroomCount?: string | number | null
  showerRoomCount?: string | number | null
  wcCount?: string | number | null
  kitchen?: string | null
  exposure?: string | null
  view?: string | null
  interiorState?: string | null
  exteriorState?: string | null
  landSurface?: string | number | null
  garden?: string | null
  terraceCount?: string | number | null
  garageCount?: string | number | null
  garageSurface?: string | number | null
  parkingInsideCount?: string | number | null
  parkingOutsideCount?: string | number | null
  pool?: string | null
  constructionYear?: string | number | null
  dpeValue?: string | number | null
  gesValue?: string | number | null
  coproLots?: string | number | null
  coproCharges?: string | number | null
  coproQuotePart?: string | number | null
  coproWorksFund?: string | number | null
  wizardFields?: Record<string, string | number | null | undefined>
  note?: string | null
  initialMandant?: HektorMandantContactInput | null
  initialMandantContactId?: string | null
  initialMandantContactLabel?: string | null
  priority?: number
}

export async function createHektorDraftAnnonceJob(input: HektorDraftAnnonceJobInput): Promise<ConsoleJob> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  await requireSupabaseUserId()
  const creationStatus = input.creationStatus === 'estimation' ? 'estimation' : 'active'
  const { data, error } = await supabase.rpc('app_console_create_draft_annonce_job', {
    draft_payload: {
      title: input.title?.trim() || null,
      description: input.description?.trim() || null,
      agence_nom: input.agenceNom?.trim() || null,
      hektor_user_id: input.hektorUserId?.trim() || null,
      hektor_negociator_form_id: input.hektorNegociateurId?.trim() || null,
      hektor_user_label: input.hektorUserLabel?.trim() || null,
      hektor_user_email: input.hektorUserEmail?.trim() || null,
      creation_status: creationStatus,
      status_label: creationStatus === 'estimation' ? 'Estimation' : 'Actif',
      statut_annonce: creationStatus === 'estimation' ? '1' : '2',
      property_type: input.propertyType?.trim() || 'Appartement',
      property_profile: input.propertyProfile?.trim() || null,
      hektor_id_type: input.hektorIdType == null ? '2' : String(input.hektorIdType).trim() || '2',
      offer_type: input.offerType ?? 'sale',
      address: input.address?.trim() || null,
      postal_code: input.postalCode?.trim() || null,
      city: input.city?.trim() || null,
      price: input.price == null ? null : String(input.price).trim() || null,
      net_seller_price: input.netSellerPrice == null ? null : String(input.netSellerPrice).trim() || null,
      surface: input.surface == null ? null : String(input.surface).trim() || null,
      carrez_surface: input.carrezSurface == null ? null : String(input.carrezSurface).trim() || null,
      living_surface: input.livingSurface == null ? null : String(input.livingSurface).trim() || null,
      room_count: input.roomCount == null ? null : String(input.roomCount).trim() || null,
      bedroom_count: input.bedroomCount == null ? null : String(input.bedroomCount).trim() || null,
      level_count: input.levelCount == null ? null : String(input.levelCount).trim() || null,
      bathroom_count: input.bathroomCount == null ? null : String(input.bathroomCount).trim() || null,
      shower_room_count: input.showerRoomCount == null ? null : String(input.showerRoomCount).trim() || null,
      wc_count: input.wcCount == null ? null : String(input.wcCount).trim() || null,
      kitchen: input.kitchen?.trim() || null,
      exposure: input.exposure?.trim() || null,
      view: input.view?.trim() || null,
      interior_state: input.interiorState?.trim() || null,
      exterior_state: input.exteriorState?.trim() || null,
      land_surface: input.landSurface == null ? null : String(input.landSurface).trim() || null,
      garden: input.garden?.trim() || null,
      terrace_count: input.terraceCount == null ? null : String(input.terraceCount).trim() || null,
      garage_count: input.garageCount == null ? null : String(input.garageCount).trim() || null,
      garage_surface: input.garageSurface == null ? null : String(input.garageSurface).trim() || null,
      parking_inside_count: input.parkingInsideCount == null ? null : String(input.parkingInsideCount).trim() || null,
      parking_outside_count: input.parkingOutsideCount == null ? null : String(input.parkingOutsideCount).trim() || null,
      pool: input.pool?.trim() || null,
      construction_year: input.constructionYear == null ? null : String(input.constructionYear).trim() || null,
      dpe_value: input.dpeValue == null ? null : String(input.dpeValue).trim() || null,
      ges_value: input.gesValue == null ? null : String(input.gesValue).trim() || null,
      copro_lots: input.coproLots == null ? null : String(input.coproLots).trim() || null,
      copro_charges: input.coproCharges == null ? null : String(input.coproCharges).trim() || null,
      copro_quote_part: input.coproQuotePart == null ? null : String(input.coproQuotePart).trim() || null,
      copro_works_fund: input.coproWorksFund == null ? null : String(input.coproWorksFund).trim() || null,
      hektor_wizard_fields: input.wizardFields
        ? Object.fromEntries(Object.entries(input.wizardFields).map(([key, value]) => [key, value == null ? null : String(value).trim() || null]))
        : null,
      note: input.note?.trim() || null,
      initial_mandant_contact_id: input.initialMandantContactId?.trim() || null,
      initial_mandant_contact_label: input.initialMandantContactLabel?.trim() || null,
      initial_mandant: input.initialMandant ? {
        civilite: input.initialMandant.civility?.trim() || null,
        last_name: input.initialMandant.lastName.trim(),
        first_name: input.initialMandant.firstName?.trim() || null,
        email: input.initialMandant.email.trim(),
        phone: input.initialMandant.phone?.trim() || null,
        address: input.initialMandant.address?.trim() || null,
        postal_code: input.initialMandant.postalCode?.trim() || null,
        city: input.initialMandant.city?.trim() || null,
      } : null,
    },
    draft_priority: input.priority ?? 20,
  })
  if (error || !data) throw new Error(error?.message ?? 'Unable to create Hektor draft annonce job')
  return data as ConsoleJob
}

export async function createConsoleDocumentSignedUrl(document: ConsoleDocument, expiresIn = 300): Promise<string> {
  if (!hasSupabaseEnv || !supabase) throw new Error('Supabase is not configured')
  if (document.storage_status !== 'cloud_available' || !document.storage_path) {
    throw new Error('Document non disponible dans le cloud')
  }
  const { data, error } = await supabase.storage
    .from(document.storage_bucket || consoleDocumentsBucket)
    .createSignedUrl(document.storage_path, expiresIn)
  if (error || !data?.signedUrl) throw new Error(error?.message ?? 'Unable to create signed URL')
  const { error: touchError } = await supabase.rpc('app_console_touch_document', { document_id: document.id })
  if (touchError) throw new Error(touchError.message)
  return data.signedUrl
}
