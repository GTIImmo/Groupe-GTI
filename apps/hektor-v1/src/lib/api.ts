import { mockDiffusionRequestEvents, mockDiffusionRequests, mockDiffusionTargets, mockDossiers, mockMandatBroadcasts, mockMandats, mockSummary, mockUserProfile, mockWorkItems } from './mockData'
import { hasSupabaseEnv, supabase, supabaseAnonKey, supabaseUrl } from './supabase'
import type { DashboardSummary, DetailedDossier, DiffusionRequest, DiffusionRequestEvent, DiffusionTarget, Dossier, DossierDetail, MandatBroadcast, MandatRecord, UserNegotiatorContext, UserProfile, WorkItem } from '../types'

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
  commercial: string
  agency: string
  archive: string
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

const allFilterValue = '__all__'
const activeArchiveFilterValue = '__active__'
const archivedFilterValue = '__archived__'
const withMandatFilterValue = '__with_mandat__'
const withoutMandatFilterValue = '__without_mandat__'
const withoutCommercialFilterValue = '__without_commercial__'
const requestStatuses = ['pending', 'in_progress', 'waiting_commercial', 'accepted', 'refused']
const localDiffusionTargetsKey = 'hektor-v1-diffusion-targets'
const localDiffusionRequestsKey = 'hektor-v1-diffusion-requests'
const localDiffusionRequestEventsKey = 'hektor-v1-diffusion-request-events'
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

function canUseLocalDiffusionDevApi() {
  if (typeof window === 'undefined') return true
  const host = window.location.hostname.toLowerCase()
  return host === 'localhost' || host === '127.0.0.1'
}

function isInvalidDiffusionRequestEventIdTypeError(message: string | undefined) {
  const text = (message ?? '').toLowerCase()
  return text.includes('invalid input syntax for type bigint')
}

async function invokeSupabaseFunction<T>(name: string, body: Record<string, unknown>) {
  if (!supabase || !supabaseUrl || !supabaseAnonKey) {
    throw new Error('Supabase function is not available')
  }
  const { data } = await supabase.auth.getSession()
  const accessToken = data.session?.access_token
  if (!accessToken) {
    throw new Error('Session Supabase introuvable')
  }
  const response = await fetch(`${supabaseUrl}/functions/v1/${name}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      apikey: supabaseAnonKey,
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(body),
  })
  const text = await response.text()
  const payload = text ? JSON.parse(text) : {}
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.error ?? `Supabase function ${name} failed`)
  }
  return payload as T
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
}

function isValidationApproved(value: string | null | undefined) {
  const normalized = normalizeValidationState(value)
  return normalized === 'oui' || normalized === 'valide' || normalized === 'validee' || normalized === 'validation_ok' || normalized === 'ok'
}

function normalizeOfferPropositionType(value: string | null | undefined) {
  const state = normalizeBusinessState(value)
  if (state === 'accepted') return 'accepte'
  if (state === 'proposed') return 'proposition'
  if (state === 'refused' || state === 'cancelled') return 'refus'
  return state
}

function isCompromisCancelledState(value: string | null | undefined) {
  return normalizeBusinessState(value) === 'cancelled'
}

function getOfferLastPropositionType(item: { offre_last_proposition_type?: string | null; offre_state?: string | null }) {
  const derived = normalizeOfferPropositionType(item.offre_last_proposition_type)
  if (derived) return derived
  return normalizeOfferPropositionType(item.offre_state)
}

function hasOffreAchatEnCours(item: { offre_id?: string | number | null; offre_last_proposition_type?: string | null; offre_state?: string | null }) {
  const lastType = getOfferLastPropositionType(item)
  return item.offre_id != null && (lastType === 'proposition' || lastType === 'accepte')
}

function hasOffreAchatRefusee(item: { offre_id?: string | number | null; offre_last_proposition_type?: string | null; offre_state?: string | null }) {
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
  return true
}

function buildLatestRequestStatusMap(rows: Array<{ app_dossier_id: number; request_status: string | null; request_type?: string | null; requested_at?: string | null; created_at?: string | null }>) {
  const latestByDossier = new Map<number, { request_status: string | null; request_type?: string | null; requested_at?: string | null; created_at?: string | null }>()
  for (const row of rows) {
    const current = latestByDossier.get(row.app_dossier_id)
    const nextDate = new Date(row.requested_at ?? row.created_at ?? 0).getTime()
    const currentDate = current ? new Date(current.requested_at ?? current.created_at ?? 0).getTime() : 0
    if (!current || nextDate >= currentDate) latestByDossier.set(row.app_dossier_id, row)
  }
  return latestByDossier
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
    const latestByDossier = buildLatestRequestStatusMap(readLocalDiffusionRequests())
    return baseRows
      .filter((item) => {
        const latest = latestByDossier.get(item.app_dossier_id)
        return matchesRequestScope(latest?.request_status, requestScope) && matchesRequestType(latest?.request_type ?? null, requestType)
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

  const latestByDossier = buildLatestRequestStatusMap(requestRows)
  return baseIds.filter((appDossierId) => {
    const latest = latestByDossier.get(appDossierId)
    return matchesRequestScope(latest?.request_status, requestScope) && matchesRequestType(latest?.request_type ?? null, requestType)
  })
}

function hasActiveFilters(filters: AppFilters) {
  return Boolean(
    filters.query.trim() ||
      normalizeFilterValue(filters.commercial) ||
      normalizeFilterValue(filters.agency) ||
      filters.archive !== allFilterValue ||
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

function applyLocalDossierFilters(rows: Dossier[], filters: AppFilters) {
  const query = filters.query.trim().toLowerCase()
  const commercial = normalizeFilterValue(filters.commercial)
  const agency = normalizeFilterValue(filters.agency)
  const archive = filters.archive
  const mandat = filters.mandat
  const affaire = normalizeFilterValue(filters.affaire)
  const offreStatus = normalizeFilterValue(filters.offreStatus)
  const compromisStatus = normalizeFilterValue(filters.compromisStatus)
  const requestScope = normalizeFilterValue(filters.requestScope)
  const requestType = normalizeFilterValue(filters.requestType)
  const statut = normalizeFilterValue(filters.statut)
  const validationDiffusion = normalizeFilterValue(filters.validationDiffusion)
  const diffusable = normalizeFilterValue(filters.diffusable)
  const passerelle = normalizeFilterValue(filters.passerelle)
  const erreurDiffusion = normalizeFilterValue(filters.erreurDiffusion)
  const priority = normalizeFilterValue(filters.priority)
  const latestByDossier = requestScope || requestType ? buildLatestRequestStatusMap(readLocalDiffusionRequests()) : null

  return rows.filter((item) => {
    const text = `${item.titre_bien} ${item.numero_dossier ?? ''} ${item.numero_mandat ?? ''} ${item.commercial_nom ?? ''} ${item.agence_nom ?? ''} ${item.ville ?? ''}`.toLowerCase()
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
      (!requestScope || matchesRequestScope(latestByDossier?.get(item.app_dossier_id)?.request_status, requestScope)) &&
      (!requestType || matchesRequestType(latestByDossier?.get(item.app_dossier_id)?.request_type, requestType)) &&
      (!statut || (item.statut_annonce ?? '') === statut) &&
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
  const mandat = filters.mandat
  const affaire = normalizeFilterValue(filters.affaire)
  const offreStatus = normalizeFilterValue(filters.offreStatus)
  const compromisStatus = normalizeFilterValue(filters.compromisStatus)
  const statut = normalizeFilterValue(filters.statut)
  const validationDiffusion = normalizeFilterValue(filters.validationDiffusion)
  const diffusable = normalizeFilterValue(filters.diffusable)
  const passerelle = normalizeFilterValue(filters.passerelle)
  const erreurDiffusion = normalizeFilterValue(filters.erreurDiffusion)
  const priority = normalizeFilterValue(filters.priority)

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
  if (mandat === withMandatFilterValue) query = query.not('numero_mandat', 'is', null).neq('numero_mandat', '')
  if (mandat === withoutMandatFilterValue) query = query.or('numero_mandat.is.null,numero_mandat.eq.')
  if (affaire === 'offre_achat') query = query.not('offre_id', 'is', null)
  if (affaire === 'compromis') query = query.not('compromis_id', 'is', null)
  if (offreStatus === 'en_cours') {
    query = query.or(['and(offre_id.not.is.null,offre_last_proposition_type.eq.proposition)', 'and(offre_id.not.is.null,offre_last_proposition_type.eq.accepte)'].join(','))
  }
  if (offreStatus === 'refusee') query = query.or('and(offre_id.not.is.null,offre_last_proposition_type.eq.refus)')
  if (compromisStatus === 'en_cours') query = query.or('and(compromis_id.not.is.null,compromis_state.eq.active)')
  if (compromisStatus === 'annule') query = query.or('and(compromis_id.not.is.null,compromis_state.eq.cancelled)')
  if (statut) query = query.eq('statut_annonce', statut)
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
  if (diffusable === 'diffusable') query = query.eq('diffusable', '1')
  if (diffusable === 'non_diffusable') query = query.or('diffusable.is.null,diffusable.eq.0')
  if (passerelle) query = query.ilike('portails_resume', `%${passerelle}%`)
  if (erreurDiffusion === 'avec_erreur') query = query.eq('has_diffusion_error', true)
  if (erreurDiffusion === 'sans_erreur') query = query.or('has_diffusion_error.is.null,has_diffusion_error.eq.false,has_diffusion_error.eq.0')
  if (priority) query = query.eq('priority', priority)

  const search = normalizeSearchTerm(filters.query)
  if (search) {
    const ilike = `%${search}%`
    query = query.or(
      [
        `titre_bien.ilike.${ilike}`,
        `numero_dossier.ilike.${ilike}`,
        `numero_mandat.ilike.${ilike}`,
        `commercial_nom.ilike.${ilike}`,
        `ville.ilike.${ilike}`,
      ].join(','),
    )
  }

  return query
}

function applyNegotiatorScopeToQuery(baseQuery: any, scope?: DataScope | null) {
  const { negotiatorEmail } = normalizeScope(scope)
  if (!negotiatorEmail) return baseQuery
  return baseQuery.eq('negociateur_email', negotiatorEmail)
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

  const requestScopedIds = await resolveRequestScopedDossierIds(filters, scope)
  const from = (page - 1) * pageSize
  const to = from + pageSize - 1
  const countMode: 'exact' = 'exact'
  let query = applyDossierFiltersToQuery(
    applyNegotiatorScopeToQuery(supabase.from('app_dossiers_current').select('*', { count: countMode }), scope),
    filters,
  )
    .order('has_open_blocker', { ascending: false })
    .order('priority', { ascending: true })
    .order('app_dossier_id', { ascending: true })
  if (requestScopedIds) {
    query = requestScopedIds.length > 0 ? query.in('app_dossier_id', requestScopedIds) : query.eq('app_dossier_id', -1)
  }
  query = query.range(from, to)

  const { data, error, count } = await query
  if (error || !data) throw new Error(error?.message ?? 'Unable to load dossiers')
  return {
    rows: data as Dossier[],
    total: count ?? 0,
    page,
    pageSize,
  }
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
  const countMode: 'exact' = 'exact'
  const query = applyWorkItemFiltersToQuery(
    applyNegotiatorScopeToQuery(supabase.from('app_work_items_current').select('*', { count: countMode }), scope),
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
    .from('app_dossiers_current')
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

  return {
    ...(dossierData as Dossier),
    detail_payload_json: (detailData as DossierDetail | null)?.detail_payload_json ?? null,
  }
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
          .from('app_dossiers_current')
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
          .select('app_dossier_id,commercial_nom,agence_nom,validation_diffusion_state,priority,work_status,internal_status,negociateur_email')
          .order('app_dossier_id', { ascending: true })
          .range(from, from + batchSize - 1),
        scope,
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
    const scopedMandats = filterByNegotiatorEmail(mockMandats, scope)
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
      .from('app_dossiers_current')
      .select('app_dossier_id,commercial_nom,agence_nom,statut_annonce,validation_diffusion_state,portails_resume,diffusable,numero_mandat')
      .not('numero_mandat', 'is', null)
      .neq('numero_mandat', '')
      .order('app_dossier_id', { ascending: true })
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
        }
      : null
  }

  const { data, error } = await supabase
    .from('app_dossiers_current')
    .select('commercial_nom,negociateur_email,agence_nom')
    .eq('negociateur_email', normalized)
    .limit(1)
    .maybeSingle()

  if (error) {
    const message = (error.message ?? '').toLowerCase()
    if (message.includes('negociateur_email') && (message.includes('does not exist') || message.includes('schema cache'))) {
      return null
    }
    throw new Error(error.message)
  }

  return (data as UserNegotiatorContext | null) ?? null
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
  let query = applyDossierFiltersToQuery(
    applyNegotiatorScopeToQuery(supabase.from('app_dossiers_current').select('*', { count: countMode }), scope),
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
      mandatValide: rows.filter((item) => isValidationApproved(item.validation_diffusion_state)).length,
      mandatNonValide: rows.filter((item) => !isValidationApproved(item.validation_diffusion_state)).length,
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
          .from('app_dossiers_current')
          .select('app_dossier_id,numero_mandat,diffusable,validation_diffusion_state,offre_id,offre_state,offre_last_proposition_type,compromis_id,compromis_state,vente_id,portails_resume,has_diffusion_error')
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

  return {
    total: rows.length,
    withoutMandat: rows.filter((item) => !(item.numero_mandat ?? '').trim()).length,
    mandatNonDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') !== '1').length,
    mandatDiffuse: rows.filter((item) => Boolean((item.numero_mandat ?? '').trim()) && (item.diffusable ?? '0') === '1').length,
    mandatValide: rows.filter((item) => isValidationApproved(item.validation_diffusion_state)).length,
    mandatNonValide: rows.filter((item) => !isValidationApproved(item.validation_diffusion_state)).length,
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
  const requestType = normalizeBusinessState(input.requestType) === 'demande_baisse_prix' ? 'demande_baisse_prix' : 'demande_diffusion'
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
      eventLabel: requestType === 'demande_baisse_prix' ? 'Demande de baisse de prix envoyee' : 'Demande envoyee',
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
    eventLabel: requestType === 'demande_baisse_prix' ? 'Demande de baisse de prix envoyee' : 'Demande envoyee',
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
      eventLabel: input.status === 'accepted' ? (isPriceDrop ? 'Baisse de prix acceptee' : 'Demande acceptee') : input.status === 'refused' ? (isPriceDrop ? 'Baisse de prix refusee' : 'Demande refusee') : 'Demande mise a jour',
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
  await insertDiffusionRequestEvent(buildDiffusionRequestEvent({
    requestId: input.id,
    eventType: input.status === 'accepted' ? 'accepted' : input.status === 'refused' ? 'refused' : 'request_updated',
    eventLabel: input.status === 'accepted' ? (isPriceDrop ? 'Baisse de prix acceptee' : 'Demande acceptee') : input.status === 'refused' ? (isPriceDrop ? 'Baisse de prix refusee' : 'Demande refusee') : 'Demande mise a jour',
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
      eventLabel: isPriceDrop ? 'Correction baisse de prix envoyee' : 'Correction envoyee',
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
    eventLabel: isPriceDrop ? 'Correction baisse de prix envoyee' : 'Correction envoyee',
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
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    const payload = await invokeSupabaseFunction<{
      ok: true
      payload: {
        app_dossier_id: number
        hektor_annonce_id: string
        dry_run: boolean
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
  if (!canUseLocalDiffusionDevApi() && hasSupabaseEnv && supabase) {
    const payload = await invokeSupabaseFunction<{
      ok: true
      payload: {
        app_dossier_id: number
        hektor_annonce_id: string
        dry_run: boolean
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
  const response = await fetch('/api/admin/users/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok || payload?.ok === false) {
    throw new Error(payload?.error ?? 'Unable to create user')
  }
  return payload as { ok: true; userId: string; email: string }
}

export async function loadAppUsers() {
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
