import { FormEvent, Fragment, useEffect, useMemo, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import {
  type AppFilters,
  type CommercialRequestStats,
  type DataScope,
  type FilterCatalog,
  type MandatStats,
  type SuiviRequestStats,
  canUseLocalDiffusionDevApi,
  createDiffusionRequest,
  acceptDiffusionRequestOnHektor,
  applyDiffusionTargetsOnHektor,
  createAppUser,
  loadAppUsers,
  loadDiffusionRequestEvents,
  loadDiffusionRequests,
  sendDiffusionDecisionEmail,
  loadDiffusionTargets,
  previewDefaultDiffusionTargets,
  loadDossierDetail,
  loadDossiersPage,
  loadFilterCatalog,
  loadMandatFilterCatalog,
  loadMandatBroadcasts,
  loadMandatRegisterPage,
  loadMandatRegisterStats,
  setDossierHektorState,
  setDossierValidationOnHektor,
  setDossierDiffusableOnHektor,
  saveDiffusionTargets,
  loadMandatsPage,
  loadMandatStats,
  loadCommercialRequestStats,
  loadSuiviRequestStats,
  loadUserNegotiatorContext,
  loadUserProfile,
  loadWorkItemsPage,
  sendPasswordResetEmail,
  submitDiffusionCorrection,
  updateAppUser,
  updateDiffusionRequest,
} from './lib/api'
import { getCurrentSession, hasSupabaseEnv, signInWithPassword, signOut, supabase, updatePassword } from './lib/supabase'
import type { DetailedDossier, DiffusionRequest, DiffusionRequestEvent, DiffusionTarget, Dossier, DossierDetailPayload, MandatBroadcast, MandatRecord, UserNegotiatorContext, UserProfile, WorkItem } from './types'

const allFilterValue = '__all__'
const activeArchiveFilterValue = '__active__'
const archivedFilterValue = '__archived__'
const withMandatFilterValue = '__with_mandat__'
const withoutMandatFilterValue = '__without_mandat__'
const withoutCommercialFilterValue = '__without_commercial__'
const dossierPageSize = 50
const mandatPageSize = 50
const workItemPageSize = 25
const requestStatusOptions = [
  { value: 'pending', label: 'Nouvelle demande' },
  { value: 'in_progress', label: 'En cours de traitement' },
  { value: 'waiting_commercial', label: 'Retour nego demande' },
  { value: 'accepted', label: 'Acceptee' },
  { value: 'refused', label: 'Refusee' },
]
const followUpPresetOptions = [
  { value: '', label: 'Pas de relance' },
  { value: '1', label: 'Relance sous 1 jour' },
  { value: '2', label: 'Relance sous 2 jours' },
  { value: '7', label: 'Relance sous 7 jours' },
]
const refusalReasonOptions = [
  { value: 'elements_manquants', label: 'Éléments manquants' },
  { value: 'mandat_non_valide', label: 'Mandat non valide' },
  { value: 'bien_non_diffusable', label: 'Bien non diffusable' },
  { value: 'dpe_diagnostic_manquant', label: 'Diagnostic de performance énergétique manquant' },
  { value: 'justificatif_propriete_manquant', label: 'Justificatif de propriété manquant' },
  { value: 'justificatif_identite_manquant', label: "Justificatif d'identité manquant" },
  { value: 'photos_non_conformes', label: 'Photos non conformes' },
  { value: 'texte_annonce_incomplet', label: "Texte d'annonce incomplet" },
  { value: 'bareme_honoraire_non_respecte', label: "Barème d'honoraires non respecté" },
  { value: 'validation_interne_requise', label: 'Validation interne requise' },
  { value: 'correction_fiche_bien', label: 'Correction de la fiche bien' },
  { value: 'autre', label: 'Autre' },
]
const priceDropRefusalReasonOptions = [
  { value: 'avenant_signe_absent', label: 'Avenant signe absent' },
  { value: 'erreur_sur_avenant', label: "Erreur sur l'avenant" },
  { value: 'autre', label: 'Autre' },
]
const requestTypeOptions = [
  { value: 'demande_diffusion', label: 'Validation' },
  { value: 'demande_baisse_prix', label: 'Baisse de prix' },
]

function refusalReasonLabel(value: string | null | undefined) {
  const normalized = (value ?? '').trim()
  if (!normalized) return ''
  const match = [...refusalReasonOptions, ...priceDropRefusalReasonOptions].find((option) => option.value === normalized)
  return match?.label ?? normalized.replace(/_/g, ' ')
}

const emptyFilterCatalog: FilterCatalog = { commercials: [], agencies: [], statuts: [], validationDiffusions: [], diffusions: [], passerelles: [], erreursDiffusion: [], priorities: [], workStatuses: [], internalStatuses: [] }

function uniqSorted(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.map((value) => (value ?? '').trim()).filter(Boolean))).sort((a, b) =>
    a.localeCompare(b, 'fr'),
  )
}

function buildPageFilterCatalog(dossiers: Dossier[], workItems: WorkItem[], mandats: MandatRecord[]): FilterCatalog {
  return {
    commercials: uniqSorted([
      ...dossiers.map((item) => item.commercial_nom),
      ...workItems.map((item) => item.commercial_nom),
      ...mandats.map((item) => item.commercial_nom),
    ]),
    agencies: uniqSorted([
      ...dossiers.map((item) => item.agence_nom),
      ...workItems.map((item) => (item as WorkItem & { agence_nom?: string | null }).agence_nom),
      ...mandats.map((item) => item.agence_nom),
    ]),
    statuts: uniqSorted([...dossiers.map((item) => item.statut_annonce), ...mandats.map((item) => item.statut_annonce)]),
    validationDiffusions: uniqSorted([...dossiers.map((item) => item.validation_diffusion_state), ...workItems.map((item) => item.validation_diffusion_state), ...mandats.map((item) => item.validation_diffusion_state)]),
    diffusions: uniqSorted([
      ...dossiers.map((item) => ((item.diffusable ?? '0') === '1' ? 'diffusable' : 'non_diffusable')),
      ...mandats.map((item) => ((item.diffusable ?? '0') === '1' ? 'diffusable' : 'non_diffusable')),
    ]),
    passerelles: uniqSorted([
      ...dossiers.flatMap((item) => (item.portails_resume ?? '').split(',').map((value) => value.trim())),
      ...mandats.flatMap((item) => (item.portails_resume ?? '').split(',').map((value) => value.trim())),
    ]),
    erreursDiffusion: ['avec_erreur', 'sans_erreur'],
    priorities: uniqSorted([...dossiers.map((item) => item.priority), ...workItems.map((item) => item.priority)]),
    workStatuses: uniqSorted(workItems.map((item) => item.work_status)),
    internalStatuses: uniqSorted(workItems.map((item) => item.internal_status)),
  }
}

function mergeCatalog(primary: FilterCatalog, fallback: FilterCatalog): FilterCatalog {
  return {
    commercials: uniqSorted([...primary.commercials, ...fallback.commercials]),
    agencies: uniqSorted([...primary.agencies, ...fallback.agencies]),
    statuts: uniqSorted([...primary.statuts, ...fallback.statuts]),
    validationDiffusions: uniqSorted([...primary.validationDiffusions, ...fallback.validationDiffusions]),
    diffusions: uniqSorted([...primary.diffusions, ...fallback.diffusions]),
    passerelles: uniqSorted([...primary.passerelles, ...fallback.passerelles]),
    erreursDiffusion: uniqSorted([...primary.erreursDiffusion, ...fallback.erreursDiffusion]),
    priorities: uniqSorted([...primary.priorities, ...fallback.priorities]),
    workStatuses: uniqSorted([...primary.workStatuses, ...fallback.workStatuses]),
    internalStatuses: uniqSorted([...primary.internalStatuses, ...fallback.internalStatuses]),
  }
}

const emptyFilters: AppFilters = {
  query: '',
  mandatNumber: '',
  mandantName: '',
  commercial: allFilterValue,
  agency: allFilterValue,
  archive: allFilterValue,
  mandat: allFilterValue,
  affaire: allFilterValue,
  offreStatus: allFilterValue,
  compromisStatus: allFilterValue,
  requestScope: allFilterValue,
  requestType: allFilterValue,
  statut: allFilterValue,
  validationDiffusion: allFilterValue,
  diffusable: allFilterValue,
  passerelle: allFilterValue,
  erreurDiffusion: allFilterValue,
  priority: allFilterValue,
  workStatus: allFilterValue,
  internalStatus: allFilterValue,
}

function formatPrice(value: number | string | null | undefined) {
  if (value == null || value === '') return '-'
  const amount = typeof value === 'number' ? value : Number(value)
  if (Number.isNaN(amount)) return String(value)
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(amount)
}

function normalizeRequestedPriceInput(value: string | null | undefined) {
  const raw = (value ?? '').trim()
  if (!raw) return { raw: '', normalized: '', numeric: null as number | null }
  const sanitized = raw.replace(/\s+/g, '').replace(',', '.')
  const numeric = Number(sanitized)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return { raw, normalized: '', numeric: null as number | null }
  }
  const normalized = String(Math.round(numeric))
  return { raw, normalized, numeric }
}

function formatDate(value: string | null | undefined) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('fr-FR').format(date)
}

function parseJson<T>(value: string | null | undefined, fallback: T): T {
  if (!value) return fallback
  try {
    const parsed = JSON.parse(value) as T | null
    return parsed == null ? fallback : parsed
  } catch {
    return fallback
  }
}

function safeText(value: unknown) {
  return typeof value === 'string' ? value.trim() : ''
}

function normalizeHtmlFingerprint(value: string | null | undefined) {
  return (value ?? '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase()
}

function sanitizeContactComment(value: string | null | undefined) {
  const cleaned = safeText(value)
  if (!cleaned) return ''
  const blockedPatterns = [/motif\s*demande/i, /classification/i, /sous[\s-]*types?/i]
  return cleaned
    .split(/\r?\n+/)
    .map((line) => line.trim())
    .filter((line) => line && !blockedPatterns.some((pattern) => pattern.test(line)))
    .join('\n')
    .trim()
}

function boolLabel(value: boolean | number | string | null | undefined) {
  if (value === null || value === undefined || value === '') return '-'
  if (value === true || value === 1 || value === '1' || value === 'true') return 'Oui'
  if (value === false || value === 0 || value === '0' || value === 'false') return 'Non'
  return String(value)
}

function diffusableLabel(value: boolean | number | string | null | undefined) {
  return value === true || value === 1 || value === '1' || value === 'true' ? 'Diffusable' : 'Non diffusable'
}

function isDiffusableValue(value: boolean | number | string | null | undefined) {
  return value === true || value === 1 || value === '1' || value === 'true'
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

function erreurDiffusionLabel(value: boolean | number | string | null | undefined) {
  return value === true || value === 1 || value === '1' || value === 'true' ? 'Erreur diffusion' : 'Sans erreur diffusion'
}

function normalizePortalToken(value: string | null | undefined) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
}

function hasPortalEnabled(item: Pick<MandatRecord, 'portails_resume'>, aliases: string[]) {
  const portals = (item.portails_resume ?? '')
    .split(',')
    .map((value) => normalizePortalToken(value))
    .filter(Boolean)
  return aliases.some((alias) => portals.some((portal) => portal.includes(alias)))
}

function isSiteGtiEnabled(item: Pick<MandatRecord, 'statut_annonce' | 'diffusable'>) {
  return normalizePortalToken(item.statut_annonce) === 'actif' && isDiffusableValue(item.diffusable)
}

function requestStatusLabel(value: string | null | undefined) {
  if (value === 'pending') return 'Nouvelle demande'
  if (value === 'in_progress') return 'En cours de traitement'
  if (value === 'waiting_commercial') return 'Retour nego demande'
  if (value === 'accepted') return 'Acceptee'
  if (value === 'refused') return 'Refusee'
  return value ?? '-'
}

function requestStatusRank(value: string | null | undefined) {
  if (value === 'pending') return 1
  if (value === 'in_progress') return 2
  if (value === 'waiting_commercial') return 3
  if (value === 'refused') return 4
  if (value === 'accepted') return 5
  return 6
}

function requestTypeLabel(value: string | null | undefined) {
  const normalized = (value ?? '').trim().toLowerCase()
  if (normalized === 'demande_baisse_prix') return 'Demande de baisse de prix'
  if (normalized === 'demande_diffusion' || !normalized) return 'Demande de validation'
  return 'Demande'
}

function requestCreateLabel(value: string | null | undefined) {
  return isPriceDropRequest(value) ? 'Demande de baisse de prix' : 'Demande de validation'
}

function requestAcceptedLabel(value: string | null | undefined) {
  return isPriceDropRequest(value) ? 'Baisse de prix acceptée' : 'Demande acceptée'
}

function requestRefusedLabel(value: string | null | undefined) {
  return isPriceDropRequest(value) ? 'Baisse de prix refusee' : 'Demande refusee'
}

function requestPendingLabel(value: string | null | undefined) {
  return isPriceDropRequest(value) ? 'Baisse de prix envoyée' : 'Demande envoyée'
}

function normalizeRequestType(value: string | null | undefined) {
  const normalized = (value ?? '').trim().toLowerCase()
  return normalized === 'demande_baisse_prix' ? 'demande_baisse_prix' : 'demande_diffusion'
}

function isPriceDropRequest(value: string | null | undefined) {
  return normalizeRequestType(value) === 'demande_baisse_prix'
}

function requestTimelineDate(value: DiffusionRequest) {
  return value.processed_at ?? value.requested_at
}

function latestDiffusionRequest(requests: DiffusionRequest[], appDossierId: number, requestType?: string | null) {
  return requests
    .filter((item) => {
      if (item.app_dossier_id !== appDossierId) return false
      if (!requestType) return true
      return normalizeRequestType(item.request_type) === normalizeRequestType(requestType)
    })
    .sort((a, b) => {
      const left = new Date(requestTimelineDate(a)).getTime()
      const right = new Date(requestTimelineDate(b)).getTime()
      return right - left
    })[0] ?? null
}

function isRequestActiveStatus(value: string | null | undefined) {
  return value === 'pending' || value === 'in_progress' || value === 'waiting_commercial'
}

function latestActionRequest(requests: DiffusionRequest[], appDossierId: number, requestType: 'demande_diffusion' | 'demande_baisse_prix') {
  return latestDiffusionRequest(
    requests.filter((item) => {
      if (requestType === 'demande_diffusion') {
        return item.request_status === 'pending' || item.request_status === 'in_progress' || item.request_status === 'waiting_commercial' || item.request_status === 'refused'
      }
      return item.request_status === 'pending' || item.request_status === 'in_progress' || item.request_status === 'waiting_commercial' || item.request_status === 'refused'
    }),
    appDossierId,
    requestType,
  )
}

function requestActionLabel(request: DiffusionRequest | null, requestType: 'demande_diffusion' | 'demande_baisse_prix') {
  if (!request) return requestType === 'demande_baisse_prix' ? 'Demande de baisse de prix' : 'Demande de validation'
  if (request.request_status === 'waiting_commercial') return requestType === 'demande_baisse_prix' ? 'Baisse de prix a corriger' : 'A corriger'
  if (request.request_status === 'refused') return requestType === 'demande_baisse_prix' ? 'Baisse de prix a corriger' : 'A corriger'
  if (request.request_status === 'in_progress') return requestType === 'demande_baisse_prix' ? 'Baisse de prix en traitement' : 'Demande en traitement'
  if (request.request_status === 'pending') return requestPendingLabel(requestType)
  return requestType === 'demande_baisse_prix' ? 'Demande de baisse de prix' : 'Demande de validation'
}

function paulineActionLabel(request: DiffusionRequest | null) {
  if (!request) return 'Aucune demande'
  if (request.request_status === 'pending' || request.request_status === 'in_progress') return 'A traiter'
  if (request.request_status === 'waiting_commercial') return 'A corriger'
  if (request.request_status === 'refused') return isPriceDropRequest(request.request_type) ? 'Rejetee' : 'Refusee'
  if (request.request_status === 'accepted') return 'Acceptée'
  return 'A traiter'
}

function negociateurDiffusionState(mandat: Pick<MandatRecord, 'diffusable' | 'validation_diffusion_state'>, request: DiffusionRequest | null) {
  if (!isPriceDropRequest(request?.request_type) && isValidationApproved(mandat.validation_diffusion_state)) {
    return { label: 'Diffusion', tone: 'ready', opens: 'diffusion' as const }
  }
  if (request?.request_status === 'refused' || request?.request_status === 'waiting_commercial') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Baisse de prix a corriger' : 'A corriger', tone: 'warning', opens: 'request' as const }
  }
  if (request?.request_status === 'pending' || request?.request_status === 'in_progress') {
    return { label: requestPendingLabel(request?.request_type), tone: 'pending', opens: 'request' as const }
  }
  if (request?.request_status === 'accepted' && isPriceDropRequest(request?.request_type)) {
    return { label: 'Baisse de prix acceptée', tone: 'ready', opens: 'request' as const }
  }
  return { label: 'Demande de validation', tone: 'idle', opens: 'request' as const }
}

function paulineDiffusionState(mandat: Pick<MandatRecord, 'diffusable' | 'validation_diffusion_state'>, request: DiffusionRequest | null) {
  if (!isPriceDropRequest(request?.request_type) && isValidationApproved(mandat.validation_diffusion_state)) {
    return { label: 'Acceptée', tone: 'ready', opens: 'diffusion' as const }
  }
  if (request?.request_status === 'waiting_commercial') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Baisse de prix a corriger' : 'A corriger', tone: 'warning', opens: 'request' as const }
  }
  if (request?.request_status === 'refused') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Rejetee' : 'Refusee', tone: 'warning', opens: 'request' as const }
  }
  if (request?.request_status === 'pending' || request?.request_status === 'in_progress') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Baisse de prix a traiter' : 'A traiter', tone: 'pending', opens: 'request' as const }
  }
  if (request?.request_status === 'accepted' && isPriceDropRequest(request?.request_type)) {
    return { label: 'Baisse de prix acceptée', tone: 'ready', opens: 'request' as const }
  }
  return { label: 'Aucune demande', tone: 'idle', opens: 'request' as const }
}

type ActionButtonTypeTone = 'validation' | 'price-drop' | 'diffusion' | 'hektor'
type ActionButtonStateTone = 'request' | 'progress' | 'correction' | 'rejected' | 'accepted' | 'diffusion'
type ActionTriggerTone = 'neutral' | 'creation' | 'correction' | 'rejected'

function actionStateVariant(label: string) {
  const normalized = label
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
  if (normalized === 'modifier') return 'diffusion'
  if (normalized === 'diffusion') return 'diffusion'
  if (normalized.includes('corriger')) return 'correction'
  if (normalized.includes('refusee') || normalized.includes('rejetee')) return 'rejected'
  if (normalized.includes('acceptee')) return 'accepted'
  if (normalized.includes('envoyee') || normalized.includes('traiter') || normalized.includes('traitement')) return 'progress'
  return 'request'
}

function buildActionButtonParts(type: 'validation' | 'price_drop' | 'diffusion', stateLabel: string) {
  if (type === 'diffusion') {
    return {
      typeLabel: 'Diffusion',
      stateLabel: 'Modifier',
      typeTone: 'diffusion' as ActionButtonTypeTone,
      stateTone: 'diffusion' as ActionButtonStateTone,
    }
  }
  if (type === 'price_drop') {
    return {
      typeLabel: 'Baisse de prix',
      stateLabel,
      typeTone: 'price-drop' as ActionButtonTypeTone,
      stateTone: actionStateVariant(stateLabel) as ActionButtonStateTone,
    }
  }
  return {
    typeLabel: 'Valider',
    stateLabel,
    typeTone: 'validation' as ActionButtonTypeTone,
    stateTone: actionStateVariant(stateLabel) as ActionButtonStateTone,
  }
}

function ActionButton(props: {
  type: 'button' | 'submit' | 'reset'
  typeLabel: string
  stateLabel: string
  typeTone: ActionButtonTypeTone
  stateTone: ActionButtonStateTone
  helperText?: string
  onClick: (event: { stopPropagation(): void }) => void
}) {
  return (
    <button className={`action-menu-item action-menu-type-${props.typeTone} action-menu-state-${props.stateTone}`} type={props.type} onClick={props.onClick}>
      <span className="action-menu-item-main">
        <span className="action-menu-item-label">{props.typeLabel}</span>
        {props.helperText ? <span className="action-menu-item-helper">{props.helperText}</span> : null}
      </span>
      <span className="action-menu-item-state">{props.stateLabel}</span>
    </button>
  )
}

function actionMenuHelperText(typeLabel: string, stateLabel: string) {
  if (typeLabel === 'Hektor') return "Ouvre directement la fiche du bien dans Hektor"
  if (typeLabel === 'Diffusion') return 'Ouvre la console de diffusion et les passerelles'
  if (stateLabel === 'Ajouter') return 'Creer une nouvelle demande'
  if (stateLabel === 'Corriger') return 'Reprendre la demande apres retour Pauline'
  if (stateLabel === 'A traiter') return 'Ouvrir la demande a traiter dans le suivi'
  if (stateLabel === 'Envoyee' || stateLabel === 'En cours') return 'Consulter la demande deja envoyee'
  if (stateLabel === 'Modifier') return 'Ajuster les reglages et portails de diffusion'
  if (stateLabel === 'Refusee' || stateLabel === 'Rejetee') return 'Consulter le refus et le motif'
  if (stateLabel === 'Acceptée') return 'Consulter la demande acceptée'
  return 'Ouvrir cette action'
}

function actionTriggerToneFromRequest(request: DiffusionRequest | null | undefined): ActionTriggerTone {
  const status = request?.request_status ?? null
  if (status === 'pending' || status === 'in_progress') return 'creation'
  if (status === 'waiting_commercial') return 'correction'
  if (status === 'refused') return 'rejected'
  return 'neutral'
}

function requestLastMessage(request: DiffusionRequest | null) {
  if (!request) return 'Aucune demande'
  return request.processing_comment || request.admin_response || request.refusal_reason || request.request_reason || request.request_comment || 'Sans message'
}

function requestLastActionAt(request: DiffusionRequest | null) {
  return request?.processed_at ?? request?.requested_at ?? null
}

function requestNextFollowUp(request: DiffusionRequest | null) {
  return request?.follow_up_needed ? request.follow_up_at : null
}

function userFullName(profile: Pick<UserProfile, 'first_name' | 'last_name' | 'display_name' | 'email'> | null | undefined) {
  const firstName = profile?.first_name?.trim() || ''
  const lastName = profile?.last_name?.trim() || ''
  const fullName = `${firstName} ${lastName}`.trim()
  if (fullName) return fullName
  return profile?.display_name?.trim() || profile?.email?.trim() || 'Utilisateur GTI'
}

function buildHektorAnnonceUrl(hektorAnnonceId: number | string | null | undefined) {
  if (hektorAnnonceId == null || hektorAnnonceId === '') return null
  const id = String(hektorAnnonceId).trim()
  if (!id) return null
  return `https://groupe-gti-immobilier.la-boite-immo.com/admin/?page=/mes-biens/mon-bien&id=${encodeURIComponent(id)}`
}

function buildAppRequestUrl(
  appDossierId: number | null | undefined,
  role: 'nego' | 'pauline' = 'nego',
  requestType?: 'demande_diffusion' | 'demande_baisse_prix' | null,
) {
  if (typeof window === 'undefined' || appDossierId == null) return null
  const url = new URL(window.location.origin + window.location.pathname)
  url.searchParams.set('screen', 'mandats')
  url.searchParams.set('app_dossier_id', String(appDossierId))
  url.searchParams.set('open', 'request')
  url.searchParams.set('role', role)
  if (requestType) url.searchParams.set('request_type', requestType)
  return url.toString()
}

function buildDiffusionDecisionEmail(input: {
  status: string
  requestType?: string | null
  negociateurEmail: string | null | undefined
  processorLabel: string | null | undefined
  processorEmail: string | null | undefined
  appDossierId: number | null | undefined
  mandat: Pick<MandatRecord, 'numero_dossier' | 'numero_mandat' | 'titre_bien' | 'ville' | 'photo_url_listing' | 'hektor_annonce_id'> | null
  response: string
  refusalReason: string
}) {
  const email = input.negociateurEmail?.trim()
  if (!email || (input.status !== 'accepted' && input.status !== 'refused')) return null

  const isPriceDrop = input.requestType === 'demande_baisse_prix'
  const dossierLabel = input.mandat?.numero_dossier?.trim() || 'Non renseigne'
  const mandatLabel = input.mandat?.numero_mandat?.trim() || 'Non renseigne'
  const bienLabel = input.mandat?.titre_bien?.trim() || 'Bien sans titre'
  const villeLabel = input.mandat?.ville?.trim() || 'Ville non renseignee'
  const actorLabel = input.processorLabel?.trim() || 'Pauline'
  const actorEmail = input.processorEmail?.trim() || null
  const trimmedResponse = input.response.trim()
  const trimmedRefusalReason = refusalReasonLabel(input.refusalReason)
  const appRequestUrl = buildAppRequestUrl(
    input.appDossierId,
    'nego',
    isPriceDrop ? 'demande_baisse_prix' : 'demande_diffusion',
  )

  const subject = input.status === 'accepted'
    ? `${isPriceDrop ? 'Baisse de prix acceptee' : 'Validation acceptee'} · ${dossierLabel}`
    : `${isPriceDrop ? 'Baisse de prix refusee' : 'Validation refusee'} · ${dossierLabel}`

  const bodyLines = input.status === 'accepted'
    ? [
        isPriceDrop ? 'Demande de baisse de prix acceptee.' : 'Demande de validation acceptee.',
        '',
        `Dossier : ${dossierLabel}`,
        `Statut : ${isPriceDrop ? 'Baisse de prix acceptee' : 'Validation acceptee'}`,
        trimmedResponse ? `Commentaire : ${trimmedResponse}` : null,
        '',
        `Action : ${isPriceDrop ? "Ouvrir l'application pour suivre la demande de prix." : "Ouvrir l'application pour suivre la validation."}`,
        appRequestUrl ? `Application : ${appRequestUrl}` : null,
      ]
        .filter(Boolean) as string[]
    : [
        isPriceDrop ? 'Demande de baisse de prix refusée.' : 'Demande de validation refusee.',
        '',
        `Dossier : ${dossierLabel}`,
        trimmedRefusalReason ? `Motif : ${trimmedRefusalReason}` : 'Motif : non précisé',
        trimmedResponse ? `Commentaire : ${trimmedResponse}` : null,
        '',
        `Action : ${isPriceDrop ? "Completer l'avenant puis renvoyer la demande dans l'application." : "Corriger le dossier puis renvoyer la demande de validation dans l'application."}`,
        appRequestUrl ? `Application : ${appRequestUrl}` : null,
      ].filter(Boolean) as string[]

  const theme = input.status === 'accepted'
    ? {
        badge: 'Demande acceptee',
        accent: '#0f766e',
        accentSoft: '#dff7f2',
        cta: '#0f4c5c',
      }
    : {
        badge: 'Correction requise',
        accent: '#b45309',
        accentSoft: '#fff1df',
        cta: '#0f4c5c',
      }

  const summaryLabel = input.status === 'accepted'
    ? (isPriceDrop ? 'Baisse de prix acceptee' : 'Validation acceptee')
    : (trimmedRefusalReason || (isPriceDrop ? 'Baisse de prix refusee' : 'Validation refusee'))

  const commentBlock = trimmedResponse
    ? `<div style="padding:14px 16px;border-radius:14px;background:#fff;border:1px solid #eadfce;margin:0 0 16px 0;">
         <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#8b6b4a;margin-bottom:6px;">Commentaire</div>
         <div style="font-size:14px;line-height:1.55;color:#27313a;">${trimmedResponse}</div>
       </div>`
    : ''

  const actionLabel = input.status === 'accepted'
    ? (isPriceDrop ? "Ouvrir l'application pour suivre la demande de prix." : "Ouvrir l'application pour suivre la validation.")
    : (isPriceDrop ? "Completer l'avenant puis renvoyer la demande dans l'application." : "Corriger le dossier puis renvoyer la demande de validation dans l'application.")

  const appButton = appRequestUrl
    ? `<a href="${appRequestUrl}" style="display:inline-block;padding:12px 16px;border-radius:12px;background:${theme.cta};color:#fff;text-decoration:none;font-weight:700;font-size:14px;">Ouvrir dans l'application</a>`
    : ''

  const bodyHtml = `
    <div style="margin:0;padding:32px 18px;background:#f3ede3;font-family:Arial,Helvetica,sans-serif;color:#1f2937;">
      <div style="max-width:580px;margin:0 auto;background:#fffdf9;border:1px solid #e7dccd;border-radius:28px;overflow:hidden;box-shadow:0 18px 40px rgba(40,32,24,0.08);">
        <div style="height:8px;background:${theme.accent};"></div>
        <div style="padding:26px 30px 22px;background:linear-gradient(180deg,#fff8ef 0%,#fffdf9 100%);border-bottom:1px solid #efe4d4;">
          <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:#8b6b4a;margin:0 0 14px 0;font-weight:700;">GTI IMMOBILIER</div>
          <div style="display:inline-block;padding:8px 14px;border-radius:999px;background:${theme.accentSoft};color:${theme.accent};font-weight:700;font-size:12px;letter-spacing:0.02em;">${theme.badge}</div>
          <h1 style="margin:16px 0 6px 0;font-size:26px;line-height:1.1;color:#18232d;letter-spacing:-0.02em;">${summaryLabel}</h1>
          <p style="margin:0;font-size:14px;line-height:1.6;color:#6b7280;">Dossier ${dossierLabel} • Notification automatique GTI</p>
        </div>
        <div style="padding:28px 30px 30px;">
          <div style="background:#ffffff;border:1px solid #eadfce;border-radius:20px;padding:18px 18px 16px;margin:0 0 18px 0;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
              <tr>
                <td width="50%" style="padding:0 10px 12px 0;vertical-align:top;">
                  <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#8b6b4a;margin-bottom:4px;">Dossier</div>
                  <div style="font-size:15px;font-weight:700;color:#1f2937;">${dossierLabel}</div>
                </td>
                <td width="50%" style="padding:0 0 12px 10px;vertical-align:top;">
                  <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#8b6b4a;margin-bottom:4px;">Mandat</div>
                  <div style="font-size:15px;font-weight:700;color:#1f2937;">${mandatLabel}</div>
                </td>
              </tr>
              <tr>
                <td width="50%" style="padding:0 10px 0 0;vertical-align:top;">
                  <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#8b6b4a;margin-bottom:4px;">Bien</div>
                  <div style="font-size:14px;line-height:1.45;color:#334155;">${bienLabel}</div>
                </td>
                <td width="50%" style="padding:0 0 0 10px;vertical-align:top;">
                  <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#8b6b4a;margin-bottom:4px;">Ville</div>
                  <div style="font-size:14px;line-height:1.45;color:#334155;">${villeLabel}</div>
                </td>
              </tr>
            </table>
          </div>
          <div style="padding:18px 18px 18px 20px;border-radius:20px;background:${theme.accentSoft};border-left:6px solid ${theme.accent};margin:0 0 16px 0;">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:${theme.accent};margin-bottom:8px;font-weight:700;">${input.status === 'accepted' ? 'Statut' : 'Motif'}</div>
            <div style="font-size:16px;line-height:1.5;color:#1f2937;font-weight:700;">${summaryLabel}</div>
          </div>
          ${commentBlock}
          <div style="padding:18px 18px 18px 20px;border-radius:20px;background:#f8f4ed;border:1px solid #eadfce;margin:0 0 22px 0;">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#8b6b4a;margin-bottom:8px;font-weight:700;">Action attendue</div>
            <div style="font-size:14px;line-height:1.65;color:#334155;">${actionLabel}</div>
          </div>
          <div style="margin:0 0 14px 0;">
            ${appButton}
          </div>
          <div style="font-size:12px;line-height:1.6;color:#7a828c;border-top:1px solid #efe4d4;padding-top:14px;">
            Notification automatique GTI. Répondez à cet email pour contacter ${actorLabel}.
          </div>
        </div>
      </div>
    </div>
  `.trim()

  return {
    to: email,
    subject,
    bodyText: bodyLines.join('\n'),
    bodyHtml,
    fromEmail: actorEmail,
    fromName: actorLabel,
    replyTo: actorEmail,
  }
}

function buildRequestHistory(request: DiffusionRequest | null, events: DiffusionRequestEvent[]) {
  if (events.length > 0) {
    return events
      .slice()
      .sort((a, b) => new Date(b.event_at).getTime() - new Date(a.event_at).getTime())
      .map((event) => {
        const payload = parseJson<{ message?: string | null }>(event.payload_json, {})
        return {
          id: event.id,
          title: event.event_label,
          date: event.event_at,
          body: payload.message || event.actor_name || 'Sans detail',
        }
      })
  }
  if (!request) return []
  const history = [
    {
      id: `${request.id}-created`,
      title: requestPendingLabel(request.request_type),
      date: request.requested_at,
      body: request.request_reason || request.request_comment || 'Sans message initial',
    },
  ]
  if (request.request_status === 'pending' && request.refusal_reason && request.processing_comment) {
    history.push({
      id: `${request.id}-refused`,
      title: requestRefusedLabel(request.request_type),
      date: request.processed_at ?? request.requested_at,
      body: request.admin_response || request.refusal_reason,
    })
    history.push({
      id: `${request.id}-corrected`,
      title: 'Correction envoyee',
      date: request.processed_at ?? request.requested_at,
      body: request.processing_comment,
    })
  } else if (request.processed_at || request.admin_response || request.processing_comment || request.refusal_reason) {
    history.push({
      id: `${request.id}-processed`,
      title: request.request_status === 'accepted' ? requestAcceptedLabel(request.request_type) : request.request_status === 'refused' ? requestRefusedLabel(request.request_type) : request.request_status === 'waiting_commercial' ? 'Correction demandee' : 'Demande traitee',
      date: request.processed_at ?? request.requested_at,
      body: request.processing_comment || request.admin_response || request.refusal_reason || 'Sans retour detaille',
    })
  }
  if (request.follow_up_needed || request.follow_up_at || request.relaunch_count) {
    history.push({
      id: `${request.id}-followup`,
      title: 'Suivi / relance',
      date: request.follow_up_at ?? request.processed_at ?? request.requested_at,
      body: request.follow_up_needed
        ? `Relance prevue le ${formatDate(request.follow_up_at)}${request.relaunch_count ? ` - ${request.relaunch_count} relance(s)` : ''}`
        : `${request.relaunch_count ?? 0} relance(s)`,
    })
  }
  return history
}

function buildRequestHistoryForType(requests: DiffusionRequest[], events: DiffusionRequestEvent[], requestType: 'demande_diffusion' | 'demande_baisse_prix') {
  return requests
    .filter((request) => normalizeRequestType(request.request_type) === requestType)
    .slice()
    .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())
    .map((request, index) => ({
      id: request.id,
      requestId: String(request.id),
      title: requestTypeLabel(request.request_type),
      status: request.request_status,
      date: requestTimelineDate(request),
      body: request.processing_comment || request.admin_response || request.refusal_reason || request.request_reason || request.request_comment || 'Sans detail',
      cycleTone: index % 4,
    }))
}

function buildRequestMessagesForType(requests: DiffusionRequest[], events: DiffusionRequestEvent[], requestType: 'demande_diffusion' | 'demande_baisse_prix') {
  const requestsForType = requests
    .filter((request) => normalizeRequestType(request.request_type) === requestType)
    .slice()
    .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())
  const toneByRequestId = new Map(requestsForType.map((request, index) => [String(request.id), index % 4]))
  const requestIds = new Set(requestsForType.map((request) => String(request.id)))
  return events
    .filter((event) => requestIds.has(String(event.diffusion_request_id)))
    .filter((event) => parseJson<{ message?: string | null }>(event.payload_json, {}).message)
    .slice()
    .sort((a, b) => new Date(b.event_at).getTime() - new Date(a.event_at).getTime())
    .map((event) => ({
      id: `message-${event.id}`,
      requestId: String(event.diffusion_request_id),
      author: event.actor_name || event.event_label,
      date: event.event_at,
      message: parseJson<{ message?: string | null }>(event.payload_json, {}).message || '',
      cycleTone: toneByRequestId.get(String(event.diffusion_request_id)) ?? 0,
    }))
}

function addDaysIso(days: number) {
  if (!days) return null
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString()
}

function mockLocalProfile(): UserProfile {
  return {
    id: 'local-user',
    email: 'local@gti.test',
    role: 'admin',
    display_name: 'Mode local',
    is_active: true,
  }
}

function detailPayload(dossier: DetailedDossier | null): DossierDetailPayload {
  return parseJson<DossierDetailPayload>(dossier?.detail_payload_json, {})
}

function pageLabel(total: number, pageSize: number, page: number) {
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, total)
  return `${from}-${to} / ${new Intl.NumberFormat('fr-FR').format(total)}`
}

function openHektorAnnonce(hektorAnnonceId: number | string | null | undefined) {
  const url = buildHektorAnnonceUrl(hektorAnnonceId)
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}

function openHektorAnnonceCompact(hektorAnnonceId: number | string | null | undefined) {
  const url = buildHektorAnnonceUrl(hektorAnnonceId)
  if (!url || typeof window === 'undefined') return
  const width = Math.min(1280, Math.max(960, window.screen.availWidth - 120))
  const height = Math.min(860, Math.max(720, window.screen.availHeight - 120))
  const left = Math.max(0, Math.round((window.screen.availWidth - width) / 2))
  const top = Math.max(0, Math.round((window.screen.availHeight - height) / 2))
  window.open(
    url,
    '_blank',
    `popup=yes,width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`,
  )
}

function commercialDisplay(value: { commercial_nom?: string | null }) {
  return (value.commercial_nom ?? '').trim() || '-'
}

function userInitials(displayName?: string | null, email?: string | null) {
  const source = (displayName ?? '').trim() || (email ?? '').split('@')[0] || 'U'
  const parts = source.split(/[\s._-]+/).filter(Boolean)
  return parts.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? '').join('') || 'U'
}

function normalizeEmail(value?: string | null) {
  return (value ?? '').trim().toLowerCase()
}

function profileRoleLabel(role?: UserProfile['role'] | null) {
  if (role === 'admin') return 'Administrateur'
  if (role === 'manager') return 'Manager'
  if (role === 'commercial') return 'Negociateur'
  if (role === 'lecture') return 'Lecture'
  return 'Profil'
}

function screenContextLabel(screen: 'annonces' | 'mandats' | 'registre' | 'suivi') {
  if (screen === 'annonces') return 'Vue stock'
  if (screen === 'mandats') return 'Vue mandat'
  if (screen === 'registre') return 'Registre'
  return 'Vue Pauline'
}

function mandateRegisterObjectLabel(item: MandatRecord) {
  return (item.mandat_type ?? item.mandat_type_source ?? '').trim() || '-'
}

function mandateRegisterTypeInlineLabel(item: MandatRecord) {
  const value = mandateRegisterObjectLabel(item)
  if (!value || value === '-') return ''
  return value.toLocaleLowerCase('fr-FR')
}

function mandateRegisterMandantsLabel(item: MandatRecord) {
  const raw = (item.mandants_texte ?? '').replace(/\s+/g, ' ').trim()
  if (!raw) return '-'

  const cutPatterns = [
    /\b\d{5}\b/,
    /\d+\s*(?:bis|ter|quater|[a-z])?\s+(?:rue|route|avenue|av\.?|impasse|chemin|allee|all[ée]e|boulevard|bd|place|lotissement|lot|residence|r[ée]sidence|mont[ée]e|faubourg|hameau|quartier|lieu-dit|ld)\b/i,
    /(?:^|[\s,-])(?:rue|route|avenue|av\.?|impasse|chemin|allee|all[ée]e|boulevard|bd|place|lotissement|lot|residence|r[ée]sidence|mont[ée]e|faubourg|hameau|quartier|lieu-dit|ld)\b/i,
    /\s-\s/,
  ]

  let cutIndex = raw.length
  for (const pattern of cutPatterns) {
    const match = pattern.exec(raw)
    if (match && match.index > 0) {
      cutIndex = Math.min(cutIndex, match.index)
    }
  }

  const label = raw.slice(0, cutIndex).replace(/[,\-;\s]+$/g, '').trim()
  return label || raw
}

function mandateRegisterNatureLabel(item: MandatRecord) {
  const address = [
    item.adresse_privee_listing,
    item.adresse_detail,
    item.code_postal_prive_detail,
    item.code_postal,
    item.ville_privee_detail,
    item.ville,
  ]
    .map((value) => (value ?? '').trim())
    .filter(Boolean)
    .filter((value, index, values) => values.indexOf(value) === index)
    .join(', ')
  const type = propertyTypeLabel(item.type_bien)
  return [type !== '-' ? type : '', address].filter(Boolean).join(' · ') || '-'
}

function mandateRegisterRowKey(item: MandatRecord) {
  return item.register_row_id ?? `${item.hektor_annonce_id}:${item.numero_mandat ?? item.app_dossier_id ?? 'na'}`
}

function mandateRegisterSourceLabel(item: MandatRecord) {
  return (item.register_source_kind ?? '').trim().toLowerCase() === 'historique' ? 'Historique' : 'Actif'
}

function parseRegisterDetailPayload(item: MandatRecord) {
  return parseJson<Record<string, unknown>>(item.register_detail_payload_json ?? '', {})
}

function parseRegisterHistory(item: MandatRecord) {
  return parseJson<Array<Record<string, unknown>>>(item.register_history_json ?? '', [])
}

function parseRegisterAvenants(item: MandatRecord) {
  return parseJson<Array<Record<string, unknown>>>(item.register_avenants_json ?? '', [])
}

type PriceChangeEventRecord = {
  source_kind?: string | null
  old_value?: number | string | null
  new_value?: number | string | null
  source_updated_at?: string | null
  detected_at?: string | null
  numero_mandat?: string | null
}

function parsePriceChangeEventsJson(value: unknown) {
  const rows = parseJson<Array<Record<string, unknown>>>(String(value ?? ''), [])
  return rows.map((item) => ({
    source_kind: safeText(item.source_kind) || null,
    old_value: typeof item.old_value === 'number' || typeof item.old_value === 'string' ? item.old_value : null,
    new_value: typeof item.new_value === 'number' || typeof item.new_value === 'string' ? item.new_value : null,
    source_updated_at: safeText(item.source_updated_at) || null,
    detected_at: safeText(item.detected_at) || null,
    numero_mandat: safeText(item.numero_mandat) || null,
  }))
}

function normalizePriceChangeScalar(value: unknown): string | number | null {
  return typeof value === 'number' || typeof value === 'string' ? value : null
}

function readPriceChangeEvents(
  value:
    | Pick<DossierDetailPayload, 'price_change_events_json' | 'price_change_event_count' | 'price_change_last_source_kind' | 'price_change_last_old_value' | 'price_change_last_new_value' | 'price_change_last_detected_at' | 'price_change_last_source_updated_at'>
    | Pick<Dossier, 'price_change_event_count' | 'price_change_last_source_kind' | 'price_change_last_old_value' | 'price_change_last_new_value' | 'price_change_last_detected_at' | 'price_change_last_source_updated_at'>
    | Pick<MandatRecord, 'price_change_event_count' | 'price_change_last_source_kind' | 'price_change_last_old_value' | 'price_change_last_new_value' | 'price_change_last_detected_at' | 'price_change_last_source_updated_at'>
    | Record<string, unknown>,
) {
  const parsed = parsePriceChangeEventsJson((value as { price_change_events_json?: unknown }).price_change_events_json)
  if (parsed.length > 0) return parsed
  const count = Number((value as { price_change_event_count?: unknown }).price_change_event_count ?? 0)
  if (!count) return []
  return [
    {
      source_kind: safeText((value as { price_change_last_source_kind?: unknown }).price_change_last_source_kind) || null,
      old_value: normalizePriceChangeScalar((value as { price_change_last_old_value?: unknown }).price_change_last_old_value),
      new_value: normalizePriceChangeScalar((value as { price_change_last_new_value?: unknown }).price_change_last_new_value),
      source_updated_at: safeText((value as { price_change_last_source_updated_at?: unknown }).price_change_last_source_updated_at) || null,
      detected_at: safeText((value as { price_change_last_detected_at?: unknown }).price_change_last_detected_at) || null,
      numero_mandat: null,
    },
  ]
}

function priceChangeSourceLabel(value: string | null | undefined) {
  const normalized = (value ?? '').trim().toLowerCase()
  if (normalized === 'annonce_prix') return 'Prix annonce'
  if (normalized === 'mandat_montant') return 'Montant mandat'
  return 'Changement prix'
}

function priceChangeAnchorDate(entry: PriceChangeEventRecord) {
  return entry.source_updated_at ?? entry.detected_at ?? null
}

function priceChangeSummaryLine(
  value:
    | Pick<Dossier, 'price_change_event_count' | 'price_change_last_detected_at'>
    | Pick<MandatRecord, 'price_change_event_count' | 'price_change_last_detected_at'>,
) {
  const count = Number(value.price_change_event_count ?? 0)
  if (!count) return ''
  const label = `${count} modif${count > 1 ? 's' : ''} prix`
  const date = formatDate((value.price_change_last_detected_at as string | null | undefined) ?? null)
  return date && date !== '-' ? `${label} · ${date}` : label
}

function mandateRegisterValidationLabel(value: string | null | undefined) {
  return isValidationApproved(value) ? 'Oui' : 'Non'
}

function mandateRegisterDiffusableLabel(value: string | null | undefined) {
  return isDiffusableValue(value) ? 'Oui' : 'Non'
}

const hektorPropertyTypeLabels: Record<string, string> = {
  '1': 'Maison',
  '2': 'Appartement',
  '3': 'Parking / Garage',
  '4': 'Bureau',
  '5': 'Terrain',
  '6': 'Local',
  '7': 'Immeuble',
  '8': 'Divers',
  '9': 'Programme neuf',
  '10': 'Loft / Atelier',
  '11': 'Boutique',
  '12': 'Appartement meuble',
  '13': 'Maison meublee',
  '14': 'Garage',
  '15': 'Parking',
  '16': 'Local professionnel',
  '17': 'Chalet',
  '18': 'Batiment',
  '19': 'Demeure',
  '20': 'Propriete',
  '21': 'Mas',
  '22': 'Hotel particulier',
  '23': 'Commerce',
  '24': 'Immeuble',
  '25': 'Villa',
  '26': 'Studio',
  '27': 'Duplex',
  '28': 'Triplex',
  '29': 'Atelier',
  '30': 'Ferme',
}

function propertyTypeLabel(value?: string | null) {
  const normalized = safeText(value)
  if (!normalized) return '-'
  if (/^\d+$/.test(normalized)) return hektorPropertyTypeLabels[normalized] ?? `Type ${normalized}`
  return normalized
}

function uniquePortalKeys(values: Array<string | null | undefined>) {
  return Array.from(new Set(values.map((value) => safeText(value)).filter(Boolean)))
}

function buildPortalsResume(values: Array<string | null | undefined>) {
  return uniquePortalKeys(values).join(', ')
}

type HeaderMetricItem = {
  label: string
  value: string
  tone: 'volume' | 'affaires' | 'diffusion' | 'demandes' | 'warning' | 'neutral'
  action?:
    | 'all_annonces'
    | 'offres_en_cours'
    | 'offres_refusees'
    | 'compromis_en_cours'
    | 'compromis_annules'
    | 'mandat_valide'
    | 'mandat_non_valide'
    | 'mandat_diffuse'
    | 'mandat_non_diffuse'
    | 'sans_mandat'
    | 'leboncoin'
    | 'bienici'
    | 'demandes_envoyees'
    | 'correction_attente'
    | 'suivi_a_traiter'
    | 'suivi_acceptees'
    | 'suivi_rejetees'
    | null
}

function mandateAsDossier(value: MandatRecord): Dossier {
  return {
    app_dossier_id: value.app_dossier_id,
    hektor_annonce_id: value.hektor_annonce_id,
    photo_url_listing: value.photo_url_listing ?? null,
    images_preview_json: value.images_preview_json ?? null,
    archive: value.archive ?? null,
    diffusable: value.diffusable ?? null,
    nb_portails_actifs: value.nb_portails_actifs ?? null,
    has_diffusion_error: value.has_diffusion_error ?? null,
    portails_resume: value.portails_resume ?? null,
    offre_id: value.offre_id ?? null,
    compromis_id: value.compromis_id ?? null,
    vente_id: value.vente_id ?? null,
    numero_dossier: value.numero_dossier ?? null,
    numero_mandat: value.numero_mandat ?? null,
    titre_bien: value.titre_bien,
    ville: value.ville ?? null,
    type_bien: value.type_bien ?? null,
    prix: value.prix ?? null,
    commercial_id: value.commercial_id ?? null,
    commercial_nom: value.commercial_nom ?? null,
    negociateur_email: value.negociateur_email ?? null,
    agence_nom: value.agence_nom ?? null,
    statut_annonce: value.statut_annonce ?? null,
    validation_diffusion_state: value.validation_diffusion_state ?? null,
    etat_visibilite: null,
    alerte_principale: null,
    priority: value.priority ?? null,
    has_open_blocker: false,
    commentaire_resume: null,
    date_relance_prevue: null,
    dernier_event_type: null,
    dernier_work_status: null,
  }
}

function MandatActionMenu(props: {
  mandat: Pick<MandatRecord, 'app_dossier_id' | 'hektor_annonce_id' | 'diffusable' | 'validation_diffusion_state' | 'numero_mandat'>
  role: 'nego' | 'pauline'
  requests: DiffusionRequest[]
  currentRequest?: DiffusionRequest | null
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: 'demande_diffusion' | 'demande_baisse_prix') => void
  onOpenDiffusionModal: (id: number) => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const hasMandat = Boolean((props.mandat.numero_mandat ?? '').trim())
  const canOpenDiffusion = isValidationApproved(props.mandat.validation_diffusion_state)
  const canRequestPriceDrop = isValidationApproved(props.mandat.validation_diffusion_state)
  const activeDiffusionRequest = latestActionRequest(props.requests, props.mandat.app_dossier_id, 'demande_diffusion')
  const activePriceDropRequest = latestActionRequest(props.requests, props.mandat.app_dossier_id, 'demande_baisse_prix')
  const rowRequestType = normalizeRequestType(props.currentRequest?.request_type)

  if (!hasMandat) {
    return <span className="table-note">Sans mandat</span>
  }

  const paulineLabel = props.currentRequest ? paulineActionLabel(props.currentRequest) : null
  const validationLabel = (() => {
    const label = requestActionLabel(activeDiffusionRequest, 'demande_diffusion')
    if (label === 'Demande de validation') return 'Ajouter'
    if (label === 'A corriger') return 'Corriger'
    if (label === 'Demande envoyée') return 'Envoyée'
    if (label === 'Demande en traitement') return 'En cours'
    return label
  })()
  const priceDropLabel = (() => {
    const label = requestActionLabel(activePriceDropRequest, 'demande_baisse_prix')
    if (label === 'Demande de baisse de prix') return 'Ajouter'
    if (label === 'Baisse de prix a corriger') return 'Corriger'
    if (label === 'Baisse de prix envoyée') return 'Envoyée'
    if (label === 'Baisse de prix en traitement') return 'En cours'
    return label
  })()
  const paulineParts = props.currentRequest
    ? buildActionButtonParts(
        rowRequestType === 'demande_baisse_prix' ? 'price_drop' : rowRequestType === 'demande_diffusion' ? 'validation' : 'diffusion',
        paulineLabel ?? 'A traiter',
      )
    : null
  const diffusionParts = buildActionButtonParts('diffusion', 'Modifier')
  const validationParts = buildActionButtonParts('validation', validationLabel)
  const priceDropParts = buildActionButtonParts('price_drop', priceDropLabel)
  const triggerTone = props.role === 'pauline'
    ? actionTriggerToneFromRequest(props.currentRequest)
    : actionTriggerToneFromRequest(activeDiffusionRequest) !== 'neutral'
      ? actionTriggerToneFromRequest(activeDiffusionRequest)
      : actionTriggerToneFromRequest(activePriceDropRequest)
  const menuItems =
    props.role === 'pauline' && props.currentRequest
      ? [
          {
            key: `${props.currentRequest.id}-pauline`,
            ...paulineParts,
            onClick: (event: { stopPropagation(): void }) => {
              event.stopPropagation()
              setMenuOpen(false)
              props.onOpenRequestModal(props.mandat.app_dossier_id, props.role, rowRequestType)
            },
          },
          {
            key: 'open-hektor',
            typeLabel: 'Hektor',
            stateLabel: 'Ouvrir',
            typeTone: 'hektor' as ActionButtonTypeTone,
            stateTone: 'diffusion' as ActionButtonStateTone,
            onClick: (event: { stopPropagation(): void }) => {
              event.stopPropagation()
              setMenuOpen(false)
              openHektorAnnonce(props.mandat.hektor_annonce_id)
            },
          },
        ]
      : [
          ...(canOpenDiffusion
            ? [
                {
                  key: 'diffusion',
                  ...diffusionParts,
                  onClick: (event: { stopPropagation(): void }) => {
                    event.stopPropagation()
                    setMenuOpen(false)
                    props.onOpenDiffusionModal(props.mandat.app_dossier_id)
                  },
                },
              ]
            : [
                {
                  key: 'validation',
                  ...validationParts,
                  onClick: (event: { stopPropagation(): void }) => {
                    event.stopPropagation()
                    setMenuOpen(false)
                    props.onOpenRequestModal(props.mandat.app_dossier_id, props.role, 'demande_diffusion')
                  },
                },
              ]),
          ...(canRequestPriceDrop
            ? [
                {
                  key: 'price-drop',
                  ...priceDropParts,
                  onClick: (event: { stopPropagation(): void }) => {
                    event.stopPropagation()
                    setMenuOpen(false)
                    props.onOpenRequestModal(props.mandat.app_dossier_id, props.role, 'demande_baisse_prix')
                  },
                },
              ]
            : []),
          {
            key: 'open-hektor',
            typeLabel: 'Hektor',
            stateLabel: 'Ouvrir',
            typeTone: 'hektor' as ActionButtonTypeTone,
            stateTone: 'diffusion' as ActionButtonStateTone,
            onClick: (event: { stopPropagation(): void }) => {
              event.stopPropagation()
              setMenuOpen(false)
              openHektorAnnonce(props.mandat.hektor_annonce_id)
            },
          },
        ]

  return (
    <div className="action-menu-shell">
      <button
        className={`ghost-button button-subtle action-menu-trigger action-menu-trigger-${triggerTone}`}
        type="button"
        onClick={(event) => {
          event.stopPropagation()
          setMenuOpen((value) => !value)
        }}
      >
        <span className="action-menu-trigger-dot" aria-hidden="true" />
        <span>Action</span>
      </button>
      {menuOpen ? (
        <div
          className="action-menu-dialog-backdrop"
          onClick={(event) => {
            event.stopPropagation()
            setMenuOpen(false)
          }}
        >
          <div
            className="action-menu-dialog"
            onClick={(event) => {
              event.stopPropagation()
            }}
          >
            <div className="action-menu-dialog-head">
              <div>
                <p className="action-menu-dialog-eyebrow">Raccourcis dossier</p>
                <h4>Actions disponibles</h4>
              </div>
              <button
                className="ghost-button button-subtle action-menu-close"
                type="button"
                onClick={(event) => {
                  event.stopPropagation()
                  setMenuOpen(false)
                }}
              >
                Fermer
              </button>
            </div>
            <p className="action-menu-dialog-copy">
              Mandat {props.mandat.numero_mandat ?? '-'} · Choisis une action directe pour gerer la validation, la diffusion ou ouvrir Hektor.
            </p>
            <div className="action-menu-dialog-list">
              {menuItems.map((item) => (
                <ActionButton
                  key={item.key}
                  type="button"
                  typeLabel={item.typeLabel ?? 'Action'}
                  stateLabel={item.stateLabel ?? 'Ouvrir'}
                  typeTone={item.typeTone ?? 'validation'}
                  stateTone={item.stateTone ?? 'request'}
                  helperText={actionMenuHelperText(item.typeLabel ?? 'Action', item.stateLabel ?? 'Ouvrir')}
                  onClick={item.onClick}
                />
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

function totalPages(total: number, pageSize: number) {
  return Math.max(1, Math.ceil(total / pageSize))
}

function activeFilterEntries(filters: AppFilters) {
  return [
    filters.query.trim() ? ['Recherche', filters.query.trim()] : null,
    filters.mandatNumber.trim() ? ['N° mandat', filters.mandatNumber.trim()] : null,
    filters.mandantName.trim() ? ['Mandant', filters.mandantName.trim()] : null,
    filters.commercial !== allFilterValue ? ['Negociateur', filters.commercial === withoutCommercialFilterValue ? 'Sans' : filters.commercial] : null,
    filters.agency !== allFilterValue ? ['Agence', filters.agency] : null,
    filters.archive === activeArchiveFilterValue ? ['Archive', 'Actives'] : null,
    filters.archive === archivedFilterValue ? ['Archive', 'Archivees'] : null,
    filters.mandat === withMandatFilterValue ? ['Mandat', 'Avec mandat'] : null,
    filters.mandat === withoutMandatFilterValue ? ['Mandat', 'Sans mandat'] : null,
    filters.affaire === 'offre_achat' ? ['Transactions', "Offre d'achat"] : null,
    filters.affaire === 'compromis' ? ['Transactions', 'Compromis'] : null,
    filters.offreStatus === 'en_cours' ? ['Etat offre', 'En cours'] : null,
    filters.offreStatus === 'refusee' ? ['Etat offre', 'Refusee'] : null,
    filters.compromisStatus === 'en_cours' ? ['Etat compromis', 'En cours'] : null,
    filters.compromisStatus === 'annule' ? ['Etat compromis', 'Annule'] : null,
    filters.requestScope === 'pending_or_in_progress' ? ['Demandes', 'Envoyees'] : null,
    filters.requestScope === 'waiting_correction' ? ['Demandes', 'Correction en attente'] : null,
    filters.requestScope === 'accepted_history' ? ['Demandes', 'Acceptees'] : null,
    filters.requestScope === 'refused' ? ['Demandes', 'Refusees'] : null,
    filters.requestType === 'demande_diffusion' ? ['Type demande', 'Validation'] : null,
    filters.requestType === 'demande_baisse_prix' ? ['Type demande', 'Baisse de prix'] : null,
    filters.statut !== allFilterValue ? ['Statut annonce', filters.statut] : null,
    filters.validationDiffusion === '__validated__' ? ['Validation', 'Oui'] : null,
    filters.validationDiffusion === '__not_validated__' ? ['Validation', 'Non'] : null,
    filters.validationDiffusion !== allFilterValue && filters.validationDiffusion !== '__validated__' && filters.validationDiffusion !== '__not_validated__' ? ['Validation', filters.validationDiffusion] : null,
    filters.diffusable === 'diffusable' ? ['Diffusable', 'Oui'] : null,
    filters.diffusable === 'non_diffusable' ? ['Diffusable', 'Non'] : null,
    filters.passerelle !== allFilterValue ? ['Passerelle', filters.passerelle] : null,
    filters.erreurDiffusion === 'avec_erreur' ? ['Erreur diffusion', 'Oui'] : null,
    filters.erreurDiffusion === 'sans_erreur' ? ['Erreur diffusion', 'Non'] : null,
    filters.priority !== allFilterValue ? ['Priorite', filters.priority] : null,
    filters.workStatus !== allFilterValue ? ['Work status', filters.workStatus] : null,
    filters.internalStatus !== allFilterValue ? ['Interne', filters.internalStatus] : null,
  ].filter(Boolean) as Array<[string, string]>
}

export default function App() {
  const [screen, setScreen] = useState<'annonces' | 'mandats' | 'registre' | 'suivi'>('mandats')
  const [filterCatalog, setFilterCatalog] = useState<FilterCatalog>(emptyFilterCatalog)
  const [filters, setFilters] = useState<AppFilters>(emptyFilters)
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [dossiersTotal, setDossiersTotal] = useState(0)
  const [dossierPage, setDossierPage] = useState(1)
  const [mandats, setMandats] = useState<MandatRecord[]>([])
  const [mandatsTotal, setMandatsTotal] = useState(0)
  const [mandatPage, setMandatPage] = useState(1)
  const [selectedMandatId, setSelectedMandatId] = useState<number | null>(null)
  const [selectedRegisterRowId, setSelectedRegisterRowId] = useState<string | null>(null)
  const [mandatBroadcasts, setMandatBroadcasts] = useState<MandatBroadcast[]>([])
  const [diffusionRequests, setDiffusionRequests] = useState<DiffusionRequest[]>([])
  const [diffusionRequestEvents, setDiffusionRequestEvents] = useState<DiffusionRequestEvent[]>([])
  const [mandatStats, setMandatStats] = useState<MandatStats>({ total: 0, withoutMandat: 0, mandatNonDiffuse: 0, mandatDiffuse: 0, mandatValide: 0, mandatNonValide: 0, offresEnCours: 0, offresRefusees: 0, compromisEnCours: 0, compromisAnnules: 0, affairesEnCours: 0, affairesAnnulees: 0, leboncoin: 0, bienici: 0, withErrors: 0 })
  const [suiviRequestStats, setSuiviRequestStats] = useState<SuiviRequestStats>({ pendingOrInProgress: 0, refused: 0, accepted: 0, acceptedHistorical: 0 })
  const [commercialRequestStats, setCommercialRequestStats] = useState<CommercialRequestStats>({ sent: 0, waitingCorrection: 0 })
  const [workItems, setWorkItems] = useState<WorkItem[]>([])
  const [workItemsTotal, setWorkItemsTotal] = useState(0)
  const [workItemPage, setWorkItemPage] = useState(1)
  const [selectedDossierId, setSelectedDossierId] = useState<number | null>(null)
  const [selectedDossier, setSelectedDossier] = useState<DetailedDossier | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [userNegotiatorContext, setUserNegotiatorContext] = useState<UserNegotiatorContext | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  const [session, setSession] = useState<Session | null>(null)
  const [bootLoading, setBootLoading] = useState(true)
  const [pageLoading, setPageLoading] = useState(false)
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [mandatLoading, setMandatLoading] = useState(false)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [commercialMetricsExpanded, setCommercialMetricsExpanded] = useState(false)
  const [mandatDrilldownLabel, setMandatDrilldownLabel] = useState<{ eyebrow: string; title: string } | null>(null)
  const [suiviDrilldownLabel, setSuiviDrilldownLabel] = useState<{ eyebrow: string; title: string } | null>(null)
  const [suiviRequestFilter, setSuiviRequestFilter] = useState<'pending_or_in_progress' | 'accepted_history' | 'refused' | 'waiting_correction' | null>(null)
  const [requestLoading, setRequestLoading] = useState(false)
  const [requestPending, setRequestPending] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authPending, setAuthPending] = useState(false)
  const [recoveryMode, setRecoveryMode] = useState(false)
  const [recoveryPassword, setRecoveryPassword] = useState('')
  const [recoveryPasswordConfirm, setRecoveryPasswordConfirm] = useState('')
  const [recoveryPending, setRecoveryPending] = useState(false)
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false)
  const [forgotPasswordPending, setForgotPasswordPending] = useState(false)
  const [deepLinkHandled, setDeepLinkHandled] = useState(false)
  const [requestComment, setRequestComment] = useState('')
  const [requestModalOpen, setRequestModalOpen] = useState(false)
  const [requestModalMandatId, setRequestModalMandatId] = useState<number | null>(null)
  const [requestModalComment, setRequestModalComment] = useState('')
  const [requestModalType, setRequestModalType] = useState<'demande_diffusion' | 'demande_baisse_prix'>('demande_diffusion')
  const [requestModalPriceValue, setRequestModalPriceValue] = useState('')
  const [userToolOpen, setUserToolOpen] = useState(false)
  const [userToolLoading, setUserToolLoading] = useState(false)
  const [appUsers, setAppUsers] = useState<UserProfile[]>([])
  const [editingUserId, setEditingUserId] = useState<string | null>(null)
  const [newUserEmail, setNewUserEmail] = useState('')
  const [newUserPassword, setNewUserPassword] = useState('')
  const [newUserRole, setNewUserRole] = useState<UserProfile['role']>('commercial')
  const [newUserFirstName, setNewUserFirstName] = useState('')
  const [newUserLastName, setNewUserLastName] = useState('')
  const [newUserDisplayName, setNewUserDisplayName] = useState('')
  const [newUserIsActive, setNewUserIsActive] = useState(true)
  const [editUserEmail, setEditUserEmail] = useState('')
  const [editUserRole, setEditUserRole] = useState<UserProfile['role']>('commercial')
  const [editUserFirstName, setEditUserFirstName] = useState('')
  const [editUserLastName, setEditUserLastName] = useState('')
  const [editUserDisplayName, setEditUserDisplayName] = useState('')
  const [editUserIsActive, setEditUserIsActive] = useState(true)
  const [requestModalRole, setRequestModalRole] = useState<'nego' | 'pauline'>('nego')
  const [requestModalDecision, setRequestModalDecision] = useState('in_progress')
  const [requestModalRefusalReason, setRequestModalRefusalReason] = useState('')
  const [diffusionModalOpen, setDiffusionModalOpen] = useState(false)
  const [diffusionModalMandatId, setDiffusionModalMandatId] = useState<number | null>(null)
  const [diffusionDraftTargets, setDiffusionDraftTargets] = useState<Record<string, boolean>>({})
  const [diffusionTargets, setDiffusionTargets] = useState<DiffusionTarget[]>([])
  const [diffusionTargetsLoading, setDiffusionTargetsLoading] = useState(false)
  const [diffusionTargetsSaving, setDiffusionTargetsSaving] = useState(false)
  const [diffusionTargetsSavedAt, setDiffusionTargetsSavedAt] = useState<string | null>(null)
  const [diffusionApplyPending, setDiffusionApplyPending] = useState(false)
  const [detailValidationPending, setDetailValidationPending] = useState(false)
  const [detailValidationDraft, setDetailValidationDraft] = useState<string | null>(null)
  const [detailValidationObserved, setDetailValidationObserved] = useState<string | null>(null)
  const [detailValidationSaved, setDetailValidationSaved] = useState<string | null>(null)
  const [detailDiffusablePending, setDetailDiffusablePending] = useState(false)
  const [detailDiffusableDraft, setDetailDiffusableDraft] = useState<boolean | null>(null)
  const [detailDiffusableObserved, setDetailDiffusableObserved] = useState<boolean | null>(null)
  const [detailDiffusableSaved, setDetailDiffusableSaved] = useState<boolean | null>(null)
  const [detailImageModalUrl, setDetailImageModalUrl] = useState<string | null>(null)
  const [diffusionApplyResult, setDiffusionApplyResult] = useState<null | {
    dry_run: boolean
    diffusable_changed: boolean
    diffusable_result: string
    waiting_on_hektor?: boolean
    waiting_message?: string | null
    to_add_count: number
    to_remove_count: number
    applied: Array<Record<string, unknown>>
    failed: Array<Record<string, unknown>>
    pending?: Array<Record<string, unknown>>
  }>(null)
  const sessionEmail = normalizeEmail(session?.user.email ?? profile?.email ?? null)
  const dataScope = useMemo<DataScope | undefined>(() => {
    if (profile?.role !== 'commercial') return undefined
    return { negotiatorEmail: sessionEmail || null }
  }, [profile?.role, sessionEmail])

  useEffect(() => {
    if (!hasSupabaseEnv) {
      void bootstrapApp()
      return
    }

    if (typeof window !== 'undefined') {
      const hash = window.location.hash || ''
      if (hash.includes('type=recovery')) {
        setRecoveryMode(true)
      }
    }

    void getCurrentSession().then((nextSession) => {
      setSession(nextSession)
      if (nextSession) {
        void bootstrapApp()
      } else {
        setBootLoading(false)
      }
    })

    if (!supabase) return
    const { data } = supabase.auth.onAuthStateChange((event, nextSession) => {
      if (event === 'PASSWORD_RECOVERY') {
        setRecoveryMode(true)
      }
      setSession(nextSession)
      if (nextSession) {
        void bootstrapApp()
      } else {
        setBootLoading(false)
      }
    })

    return () => data.subscription.unsubscribe()
  }, [dataScope])

  async function bootstrapApp() {
    setBootLoading(true)
    setErrorMessage(null)
    try {
      setCatalogLoading(true)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement')
    } finally {
      setBootLoading(false)
    }

    Promise.all([loadFilterCatalog(dataScope), loadMandatFilterCatalog(dataScope).catch(() => null)])
      .then(([catalog, mandatCatalog]) => setFilterCatalog(mandatCatalog ? mergeCatalog(catalog, { ...emptyFilterCatalog, ...mandatCatalog }) : catalog))
      .catch(() => setFilterCatalog(emptyFilterCatalog))
      .finally(() => setCatalogLoading(false))
  }

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    Promise.all([
      session?.user?.id ? loadUserProfile(session.user.id) : Promise.resolve(mockLocalProfile()),
      loadUserNegotiatorContext(session?.user?.email ?? null).catch(() => null),
      loadDiffusionRequests().catch(() => []),
      loadDiffusionRequestEvents().catch(() => []),
    ])
      .then(([nextProfile, nextUserNegotiatorContext, rows, events]) => {
        if (cancelled) return
        setProfile(nextProfile)
        setUserNegotiatorContext(nextUserNegotiatorContext)
        setDiffusionRequests(rows)
        setDiffusionRequestEvents(events)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement profil')
      })
    return () => {
      cancelled = true
    }
  }, [session])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    const statsPromise = screen === 'registre'
      ? loadMandatRegisterStats({ ...filters, mandat: withMandatFilterValue }, dataScope)
      : loadMandatStats(filters, dataScope)
    statsPromise
      .then((stats) => {
        if (!cancelled) setMandatStats(stats)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des stats mandat')
      })
    return () => {
      cancelled = true
    }
  }, [session, filters, dataScope, screen])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    loadSuiviRequestStats(filters, dataScope)
      .then((stats) => {
        if (!cancelled) setSuiviRequestStats(stats)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des stats suivi')
      })
    return () => {
      cancelled = true
    }
  }, [session, filters, dataScope])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    loadCommercialRequestStats(filters, dataScope)
      .then((stats) => {
        if (!cancelled) setCommercialRequestStats(stats)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des stats commerciales')
      })
    return () => {
      cancelled = true
    }
  }, [session, filters, dataScope])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    setPageLoading(true)
    setMandatLoading(true)
    const nextMandatPage = screen === 'suivi' ? 1 : mandatPage
    const nextMandatPageSize = screen === 'suivi' ? 1000 : mandatPageSize
    Promise.all([
      loadDossiersPage({ filters, page: dossierPage, pageSize: dossierPageSize, scope: dataScope }),
      screen === 'registre'
        ? loadMandatRegisterPage({ filters: { ...filters, mandat: withMandatFilterValue }, page: nextMandatPage, pageSize: nextMandatPageSize, scope: dataScope })
        : loadMandatsPage({ filters, page: nextMandatPage, pageSize: nextMandatPageSize, scope: dataScope }),
      loadWorkItemsPage({ filters, page: workItemPage, pageSize: workItemPageSize, scope: dataScope }),
    ])
      .then(([nextDossiersPage, nextMandatsPage, nextWorkItemsPage]) => {
        if (cancelled) return
        setDossiers(nextDossiersPage.rows)
        setDossiersTotal(nextDossiersPage.total)
        setMandats(nextMandatsPage.rows)
        setMandatsTotal(nextMandatsPage.total)
        setWorkItems(nextWorkItemsPage.rows)
        setWorkItemsTotal(nextWorkItemsPage.total)
        setFilterCatalog((current) => mergeCatalog(current, buildPageFilterCatalog(nextDossiersPage.rows, nextWorkItemsPage.rows, nextMandatsPage.rows)))
        setSelectedDossierId((current) => current ?? nextDossiersPage.rows[0]?.app_dossier_id ?? null)
        if (screen === 'registre') {
          setSelectedRegisterRowId((current) => {
            if (current && nextMandatsPage.rows.some((item) => item.register_row_id === current)) return current
            return nextMandatsPage.rows[0]?.register_row_id ?? null
          })
        } else {
          setSelectedMandatId((current) => current ?? (nextMandatsPage.rows[0]?.app_dossier_id ?? null))
        }
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement')
      })
      .finally(() => {
        if (!cancelled) {
          setPageLoading(false)
          setMandatLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [session, filters, dossierPage, mandatPage, workItemPage, dataScope, screen])

  useEffect(() => {
    if (selectedDossierId == null || (hasSupabaseEnv && !session)) return
    let cancelled = false
    const quickBase = dossiers.find((item) => item.app_dossier_id === selectedDossierId)
    const quick = quickBase ? { ...quickBase, detail_payload_json: selectedDossier?.detail_payload_json ?? null } : selectedDossier
    if (quick) setSelectedDossier(quick)
    setDetailLoading(true)
    loadDossierDetail(selectedDossierId)
      .then((detail) => {
        if (!cancelled) setSelectedDossier(detail)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement detail')
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [selectedDossierId, session, dossiers])

  useEffect(() => {
    if (deepLinkHandled || bootLoading || (hasSupabaseEnv && !session)) return
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    const targetOpen = params.get('open')
    const dossierValue = params.get('app_dossier_id')
    if (targetOpen !== 'request' || !dossierValue) {
      setDeepLinkHandled(true)
      return
    }
    const appDossierId = Number(dossierValue)
    if (!Number.isFinite(appDossierId)) {
      setDeepLinkHandled(true)
      return
    }
    const roleParam = params.get('role')
    const modalRole: 'nego' | 'pauline' = roleParam === 'pauline' ? 'pauline' : 'nego'
    const requestTypeParam = params.get('request_type')
    const deepLinkRequestType: 'demande_diffusion' | 'demande_baisse_prix' | undefined =
      requestTypeParam === 'demande_baisse_prix'
        ? 'demande_baisse_prix'
        : requestTypeParam === 'demande_diffusion'
          ? 'demande_diffusion'
          : undefined
    setScreen('mandats')
    setSelectedMandatId(appDossierId)
    setSelectedDossierId(appDossierId)
    openRequestModal(appDossierId, modalRole, deepLinkRequestType)
    params.delete('open')
    params.delete('app_dossier_id')
    params.delete('role')
    params.delete('request_type')
    const requestedScreen = params.get('screen')
    if (requestedScreen === 'mandats') params.delete('screen')
    const nextSearch = params.toString()
    const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ''}${window.location.hash || ''}`
    window.history.replaceState({}, document.title, nextUrl)
    setDeepLinkHandled(true)
  }, [bootLoading, deepLinkHandled, hasSupabaseEnv, mandats, session])

  useEffect(() => {
    if (!detailOpen || !selectedDossier) {
      setDetailValidationDraft(null)
      setDetailValidationObserved(null)
      setDetailValidationSaved(null)
      setDetailDiffusableDraft(null)
      setDetailDiffusableObserved(null)
      setDetailDiffusableSaved(null)
      return
    }
    const observedValidation = isValidationApproved(selectedDossier.validation_diffusion_state) ? 'oui' : 'non'
    setDetailValidationDraft(observedValidation)
    setDetailValidationObserved(observedValidation)
    setDetailValidationSaved(observedValidation)
    const observed = isDiffusableValue(selectedDossier.diffusable)
    setDetailDiffusableDraft(observed)
    setDetailDiffusableObserved(observed)
    setDetailDiffusableSaved(observed)
  }, [detailOpen, selectedDossier?.app_dossier_id])

  useEffect(() => {
    if (selectedMandatId == null || (hasSupabaseEnv && !session)) return
    let cancelled = false
    loadMandatBroadcasts(selectedMandatId)
      .then((rows) => {
        if (!cancelled) setMandatBroadcasts(rows)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement passerelles')
      })
    return () => {
      cancelled = true
    }
  }, [selectedMandatId, session])

  async function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setAuthPending(true)
    setErrorMessage(null)
    try {
      await signInWithPassword(authEmail, authPassword)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Connexion impossible')
    } finally {
      setAuthPending(false)
    }
  }

  async function handleSignOut() {
    try {
      await signOut()
      setDossiers([])
      setMandats([])
      setMandatBroadcasts([])
      setDiffusionRequests([])
      setDiffusionRequestEvents([])
      setWorkItems([])
      setSelectedDossierId(null)
      setSelectedDossier(null)
      setSelectedMandatId(null)
      setProfile(null)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Deconnexion impossible')
    }
  }

  function updateFilter<K extends keyof AppFilters>(key: K, value: AppFilters[K]) {
    setFilters((current) => {
      const next = { ...current, [key]: value }
      if (key === 'affaire') {
        if (value !== 'offre_achat') next.offreStatus = allFilterValue
        if (value !== 'compromis') next.compromisStatus = allFilterValue
      }
      return next
    })
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
  }

  function resetFilters() {
    setFilters(emptyFilters)
    setMandatDrilldownLabel(null)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(null)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
  }

  function openScreen(nextScreen: 'annonces' | 'mandats' | 'registre' | 'suivi') {
    setScreen(nextScreen === 'annonces' ? 'mandats' : nextScreen)
    setMandatDrilldownLabel(null)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(null)
    setFiltersOpen(false)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
    setFilters(emptyFilters)
  }

  function openMandatDrilldown(action: HeaderMetricItem['action']) {
    if (!action) return
    if (action === 'suivi_a_traiter' || action === 'suivi_acceptees' || action === 'suivi_rejetees') {
      const nextSuiviFilter =
        action === 'suivi_a_traiter'
          ? 'pending_or_in_progress'
          : action === 'suivi_acceptees'
                ? 'accepted_history'
                : 'refused'
      const nextSuiviLabel =
        action === 'suivi_a_traiter'
          ? { eyebrow: '', title: 'Demandes à traiter' }
          : action === 'suivi_acceptees'
            ? { eyebrow: '', title: 'Demandes acceptées' }
            : { eyebrow: '', title: 'Demandes rejetées' }
      setScreen('suivi')
      setFiltersOpen(false)
      setDossierPage(1)
      setMandatPage(1)
      setWorkItemPage(1)
      setDetailOpen(false)
      setCommercialMetricsExpanded(false)
      setMandatDrilldownLabel(null)
      setSuiviDrilldownLabel(nextSuiviLabel)
      setSuiviRequestFilter(nextSuiviFilter)
      setFilters(emptyFilters)
      return
    }
    const nextFilters: AppFilters = {
      ...emptyFilters,
      affaire: action === 'offres_en_cours' || action === 'offres_refusees' ? 'offre_achat' : action === 'compromis_en_cours' || action === 'compromis_annules' ? 'compromis' : allFilterValue,
      offreStatus: action === 'offres_en_cours' ? 'en_cours' : action === 'offres_refusees' ? 'refusee' : allFilterValue,
      compromisStatus: action === 'compromis_en_cours' ? 'en_cours' : action === 'compromis_annules' ? 'annule' : allFilterValue,
      requestScope:
        action === 'demandes_envoyees'
          ? 'pending_or_in_progress'
          : action === 'correction_attente'
            ? 'waiting_correction'
            : allFilterValue,
      mandat: action === 'mandat_diffuse' || action === 'mandat_non_diffuse' || action === 'mandat_valide' || action === 'mandat_non_valide' ? withMandatFilterValue : action === 'sans_mandat' ? withoutMandatFilterValue : allFilterValue,
      validationDiffusion: action === 'mandat_valide' ? '__validated__' : action === 'mandat_non_valide' ? '__not_validated__' : allFilterValue,
      diffusable: action === 'mandat_diffuse' ? 'diffusable' : action === 'mandat_non_diffuse' ? 'non_diffusable' : allFilterValue,
      passerelle: action === 'leboncoin' ? 'leboncoin' : action === 'bienici' ? "bien'ici" : allFilterValue,
    }
    const nextLabel =
      action === 'all_annonces'
        ? null
        : action === 'offres_en_cours'
          ? { eyebrow: '', title: "Offres d'achat en cours" }
          : action === 'offres_refusees'
            ? { eyebrow: '', title: "Offres d'achat refusées" }
            : action === 'compromis_en_cours'
              ? { eyebrow: '', title: 'Compromis en cours' }
              : action === 'compromis_annules'
                ? { eyebrow: '', title: 'Compromis annulés' }
                : action === 'demandes_envoyees'
                  ? { eyebrow: '', title: 'Demandes envoyées' }
                  : action === 'correction_attente'
                    ? { eyebrow: '', title: 'Corrections en attente' }
                    : action === 'mandat_diffuse'
                      ? { eyebrow: '', title: 'Mandats diffusés' }
                      : action === 'mandat_valide'
                        ? { eyebrow: '', title: 'Mandats validés' }
                        : action === 'mandat_non_valide'
                          ? { eyebrow: '', title: 'Mandats non validés' }
                          : action === 'mandat_non_diffuse'
                            ? { eyebrow: '', title: 'Mandats non diffusés' }
                            : action === 'sans_mandat'
                              ? { eyebrow: '', title: 'Sans mandat' }
                              : action === 'leboncoin'
                                ? { eyebrow: '', title: 'Diffusées sur LeBonCoin' }
                                : action === 'bienici'
                                  ? { eyebrow: '', title: "Diffusées sur Bien'ici" }
                                  : null
    setScreen('mandats')
    setFiltersOpen(false)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
    setCommercialMetricsExpanded(false)
    setMandatDrilldownLabel(nextLabel)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(null)
    setFilters(nextFilters)
  }

  function openRegisterDrilldown(action: HeaderMetricItem['action']) {
    if (!action) return
    const nextFilters: AppFilters = {
      ...emptyFilters,
      affaire: action === 'offres_en_cours' || action === 'offres_refusees' ? 'offre_achat' : action === 'compromis_en_cours' || action === 'compromis_annules' ? 'compromis' : allFilterValue,
      offreStatus: action === 'offres_en_cours' ? 'en_cours' : action === 'offres_refusees' ? 'refusee' : allFilterValue,
      compromisStatus: action === 'compromis_en_cours' ? 'en_cours' : action === 'compromis_annules' ? 'annule' : allFilterValue,
      requestScope:
        action === 'demandes_envoyees'
          ? 'pending_or_in_progress'
          : action === 'correction_attente'
            ? 'waiting_correction'
            : allFilterValue,
      mandat: action === 'mandat_diffuse' || action === 'mandat_non_diffuse' || action === 'mandat_valide' || action === 'mandat_non_valide' ? withMandatFilterValue : action === 'sans_mandat' ? withoutMandatFilterValue : allFilterValue,
      validationDiffusion: action === 'mandat_valide' ? '__validated__' : action === 'mandat_non_valide' ? '__not_validated__' : allFilterValue,
      diffusable: action === 'mandat_diffuse' ? 'diffusable' : action === 'mandat_non_diffuse' ? 'non_diffusable' : allFilterValue,
      passerelle: action === 'leboncoin' ? 'leboncoin' : action === 'bienici' ? "bien'ici" : allFilterValue,
    }
    setScreen('registre')
    setFiltersOpen(false)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
    setCommercialMetricsExpanded(false)
    setMandatDrilldownLabel(null)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(null)
    setFilters(nextFilters)
  }

  function openDossierDetailPage(appDossierId: number) {
    setSelectedDossierId(appDossierId)
    setDetailOpen(true)
  }

  function closeDossierDetailPage() {
    setDetailOpen(false)
    setDetailImageModalUrl(null)
  }

function openRequestModal(appDossierId: number, role: 'nego' | 'pauline' = 'nego', requestType?: 'demande_diffusion' | 'demande_baisse_prix') {
    const currentRequest = latestDiffusionRequest(diffusionRequests, appDossierId, requestType)
    const nextType = requestType ?? normalizeRequestType(currentRequest?.request_type)
    setSelectedMandatId(appDossierId)
    setRequestModalMandatId(appDossierId)
    setRequestModalComment('')
    setRequestModalType(nextType)
    setRequestModalPriceValue('')
    setRequestModalRole(role)
    setRequestModalDecision(role === 'pauline' ? 'in_progress' : 'pending')
    setRequestModalRefusalReason('')
    setRequestModalOpen(true)
  }

  function closeRequestModal() {
    setRequestModalOpen(false)
    setRequestModalMandatId(null)
    setRequestModalComment('')
    setRequestModalType('demande_diffusion')
    setRequestModalPriceValue('')
    setRequestModalRole('nego')
    setRequestModalDecision('in_progress')
    setRequestModalRefusalReason('')
  }

  function openDiffusionModal(appDossierId: number) {
    setSelectedMandatId(appDossierId)
    setDiffusionModalMandatId(appDossierId)
    setDiffusionTargets([])
    setDiffusionDraftTargets({})
    setDiffusionTargetsSavedAt(null)
    setDiffusionApplyResult(null)
    setDiffusionModalOpen(true)
  }

  function closeDiffusionModal() {
    setDiffusionModalOpen(false)
    setDiffusionModalMandatId(null)
    setDiffusionTargets([])
    setDiffusionDraftTargets({})
    setDiffusionTargetsSavedAt(null)
    setDiffusionApplyResult(null)
  }

  async function handleCreateDiffusionRequest(input?: { mandatId?: number | null; comment?: string; requestType?: 'demande_diffusion' | 'demande_baisse_prix'; requestedPrice?: string | null }) {
    const mandatId = input?.mandatId ?? selectedMandatId
    if (!mandatId || !profile) return
    const mandat = mandats.find((item) => item.app_dossier_id === mandatId)
    if (!mandat) return
    const nextType = input?.requestType ?? requestModalType
    if (nextType === 'demande_baisse_prix' && !isValidationApproved(mandat.validation_diffusion_state)) {
      setErrorMessage("Baisse de prix impossible : le mandat doit etre sous validation = oui.")
      return
    }
    const priceInput = normalizeRequestedPriceInput(input?.requestedPrice ?? requestModalPriceValue)
    if (nextType === 'demande_baisse_prix' && !priceInput.numeric) {
      setErrorMessage("Le nouveau prix demande doit etre un montant numerique valide.")
      return
    }
    setRequestPending(true)
    setErrorMessage(null)
    try {
      const requestedPrice = nextType === 'demande_baisse_prix' ? priceInput.normalized : (input?.requestedPrice ?? requestModalPriceValue).trim()
      const baseComment = (input?.comment ?? requestModalComment).trim()
      const nextComment =
        nextType === 'demande_baisse_prix'
          ? [`Demande de baisse de prix`, requestedPrice ? `Nouveau prix demande : ${requestedPrice}` : null, baseComment ? `Commentaire : ${baseComment}` : null].filter(Boolean).join('\n')
          : baseComment
      const created = await createDiffusionRequest({
        dossier: mandat,
        comment: nextComment,
        requestType: nextType,
        requesterId: profile.id,
        requesterLabel: profile.display_name ?? profile.email,
      })
      setRequestComment('')
      closeRequestModal()
      setDiffusionRequests((current) => (created ? [created, ...current] : current))
      setDiffusionRequestEvents(await loadDiffusionRequestEvents().catch(() => []))
      if (hasSupabaseEnv) {
        setDiffusionRequests(await loadDiffusionRequests())
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de creation de demande')
    } finally {
      setRequestPending(false)
    }
  }

  async function handleSubmitDiffusionCorrection(input: { requestId: string; comment: string }) {
    if (!profile) return
    setRequestPending(true)
    setErrorMessage(null)
    try {
      await submitDiffusionCorrection({
        id: input.requestId,
        comment: input.comment,
        requesterLabel: profile.display_name ?? profile.email,
      })
      closeRequestModal()
      setDiffusionRequests(await loadDiffusionRequests())
      setDiffusionRequestEvents(await loadDiffusionRequestEvents().catch(() => []))
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur d envoi de correction')
    } finally {
      setRequestPending(false)
    }
  }

  async function handleUpdateDiffusionRequest(input: {
    requestId: string
    status: string
    response: string
    refusalReason: string
    followUpNeeded: boolean
    followUpDays: number
    relaunchCount: number
  }) {
    if (!profile) return
    setRequestLoading(true)
    setErrorMessage(null)
    let mutationCommitted = false
    try {
      const currentRequest = diffusionRequests.find((item) => item.id === input.requestId) ?? null
      const currentMandat = currentRequest ? mandats.find((item) => item.app_dossier_id === currentRequest.app_dossier_id) ?? null : null
      let acceptanceResult: Awaited<ReturnType<typeof acceptDiffusionRequestOnHektor>> | null = null
      let acceptanceInfoMessage: string | null = null
      if (input.status === 'accepted' && !isPriceDropRequest(currentRequest?.request_type) && currentRequest) {
        if (!isValidationApproved(currentMandat?.validation_diffusion_state ?? null)) {
          acceptanceInfoMessage = "Demande acceptee. L'app demande d'abord Validation = oui sur Hektor, puis active la diffusion et les passerelles si Hektor confirme la validation."
        }
        acceptanceResult = await acceptDiffusionRequestOnHektor({
          appDossierId: currentRequest.app_dossier_id,
        })
      }
      await updateDiffusionRequest({
        id: input.requestId,
        status: input.status,
        response: input.response,
        refusalReason: input.refusalReason,
        followUpNeeded: input.followUpNeeded,
        followUpAt: input.followUpNeeded ? addDaysIso(input.followUpDays) : null,
        relaunchCount: input.relaunchCount,
        processorId: profile.id,
        processorLabel: profile.display_name ?? profile.email,
      })
      mutationCommitted = true
      if (input.status === 'accepted' && currentRequest && acceptanceResult && !acceptanceResult.waiting_on_hektor) {
        const diffusableValue = acceptanceResult.observed_diffusable === '1' ? '1' : '0'
        const validationValue =
          acceptanceResult.observed_validation && isValidationApproved(acceptanceResult.observed_validation)
            ? acceptanceResult.observed_validation
            : acceptanceResult.validation_state && isValidationApproved(acceptanceResult.validation_state)
              ? acceptanceResult.validation_state
              : currentMandat?.validation_diffusion_state ?? null
        await setDossierHektorState(currentRequest.app_dossier_id, {
          validationDiffusionState: validationValue,
          diffusable: diffusableValue === '1',
        })
        setDossiers((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, diffusable: diffusableValue, validation_diffusion_state: validationValue } : item))
        setMandats((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, diffusable: diffusableValue, validation_diffusion_state: validationValue } : item))
        setSelectedDossier((current) => current && current.app_dossier_id === currentRequest.app_dossier_id ? { ...current, diffusable: diffusableValue, validation_diffusion_state: validationValue } : current)
        const acceptedBroadcasts = await loadMandatBroadcasts(currentRequest.app_dossier_id).catch(() => [])
        const acceptedPortailsResume = buildPortalsResume([
          ...acceptedBroadcasts.map((item) => item.passerelle_key),
          ...acceptanceResult.applied.map((item) => safeText(item.portal_key)),
        ])
        setDossiers((current) =>
          current.map((item) =>
            item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, portails_resume: acceptedPortailsResume } : item,
          ),
        )
        setMandats((current) =>
          current.map((item) =>
            item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, portails_resume: acceptedPortailsResume } : item,
          ),
        )
        setSelectedDossier((current) =>
          current && current.app_dossier_id === currentRequest.app_dossier_id ? { ...current, portails_resume: acceptedPortailsResume } : current,
        )
        await setDossierHektorState(currentRequest.app_dossier_id, {
          portailsResume: acceptedPortailsResume,
          nbPortailsActifs: uniquePortalKeys(acceptedPortailsResume.split(',')).length,
        })
        if (currentMandat && diffusionModalMandatId === currentRequest.app_dossier_id) {
          setMandatBroadcasts(acceptedBroadcasts)
          const reloadedTargets = await loadDiffusionTargets(currentRequest.app_dossier_id).catch(() => [])
          if (reloadedTargets.length > 0) {
            setDiffusionTargets(reloadedTargets)
            setDiffusionDraftTargets(
              Object.fromEntries(reloadedTargets.map((item) => [item.portal_key ?? item.hektor_broadcast_id, item.target_state === 'enabled'])),
            )
          }
        }
        if (selectedDossier?.app_dossier_id === currentRequest.app_dossier_id) {
          setDetailDiffusableDraft(diffusableValue === '1')
          setDetailDiffusableSaved(diffusableValue === '1')
          setDetailDiffusableObserved(diffusableValue === '1')
        }
      }
      if (input.status === 'accepted' && currentRequest && acceptanceResult?.waiting_on_hektor) {
        await setDossierHektorState(currentRequest.app_dossier_id, {
          validationDiffusionState: acceptanceResult.observed_validation ?? acceptanceResult.validation_state ?? currentMandat?.validation_diffusion_state ?? null,
          diffusable:
            acceptanceResult.observed_diffusable === '1'
              ? true
              : acceptanceResult.observed_diffusable === '0'
                ? false
                : null,
        })
        acceptanceInfoMessage = acceptanceResult.waiting_message ?? "Demande acceptee. Hektor n'a pas encore confirme le passage du bien en diffusable."
      }
      closeRequestModal()
      try {
        setDiffusionRequests(await loadDiffusionRequests())
      } catch (error) {
        const refreshError = error instanceof Error ? error.message : 'rafraichissement des demandes impossible'
        acceptanceInfoMessage = acceptanceInfoMessage
          ? `${acceptanceInfoMessage} Rafraichissement des demandes impossible : ${refreshError}`
          : `Decision enregistree, mais rafraichissement des demandes impossible : ${refreshError}`
      }
      try {
        setDiffusionRequestEvents(await loadDiffusionRequestEvents().catch(() => []))
      } catch (error) {
        const eventsError = error instanceof Error ? error.message : 'rafraichissement de l historique impossible'
        acceptanceInfoMessage = acceptanceInfoMessage
          ? `${acceptanceInfoMessage} Historique non recharge : ${eventsError}`
          : `Decision enregistree, mais historique non recharge : ${eventsError}`
      }
      const decisionEmail = currentRequest
        ? buildDiffusionDecisionEmail({
            status: input.status,
            requestType: currentRequest.request_type,
            negociateurEmail:
              currentMandat?.app_dossier_id === currentRequest.app_dossier_id
                ? currentMandat?.negociateur_email ?? null
                : selectedDossier?.app_dossier_id === currentRequest.app_dossier_id
                  ? selectedDossier?.negociateur_email ?? null
                  : null,
            processorLabel: userFullName(profile),
            processorEmail: profile.email,
            appDossierId: currentRequest.app_dossier_id,
            mandat:
              currentMandat?.app_dossier_id === currentRequest.app_dossier_id
                ? currentMandat
                : selectedDossier?.app_dossier_id === currentRequest.app_dossier_id
                  ? selectedDossier
                  : null,
            response: input.response,
            refusalReason: input.refusalReason,
          })
        : null
      if (!decisionEmail && currentRequest && input.status === 'accepted') {
        acceptanceInfoMessage = acceptanceInfoMessage
          ? `${acceptanceInfoMessage} Email commercial non envoye : aucun negociateur email sur ce dossier`
          : 'Decision enregistree, mais email commercial non envoye : aucun negociateur email sur ce dossier'
      }
      if (decisionEmail) {
        try {
          await sendDiffusionDecisionEmail(decisionEmail)
        } catch (error) {
          const mailError = error instanceof Error ? error.message : 'Envoi email impossible'
          acceptanceInfoMessage = acceptanceInfoMessage
            ? `${acceptanceInfoMessage} Email commercial non envoye : ${mailError}`
            : `Decision enregistree, mais email commercial non envoye : ${mailError}`
        }
      }
      if (acceptanceInfoMessage) {
        setErrorMessage(acceptanceInfoMessage)
      }
    } catch (error) {
      if (mutationCommitted) {
        const lateError = error instanceof Error ? error.message : 'Erreur reseau apres validation'
        setErrorMessage(`Decision enregistree, mais une relecture secondaire a echoue : ${lateError}`)
      } else {
        setErrorMessage(error instanceof Error ? error.message : 'Erreur de mise a jour de demande')
      }
    } finally {
      setRequestLoading(false)
    }
  }

  async function handleCreateAppUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setUserToolLoading(true)
    setErrorMessage(null)
    try {
      const displayName = newUserDisplayName.trim() || `${newUserFirstName.trim()} ${newUserLastName.trim()}`.trim()
      const result = await createAppUser({
        email: newUserEmail.trim(),
        password: newUserPassword.trim(),
        role: newUserRole,
        firstName: newUserFirstName.trim(),
        lastName: newUserLastName.trim(),
        displayName,
        isActive: newUserIsActive,
      })
      setNewUserEmail('')
      setNewUserPassword('')
      setNewUserRole('commercial')
      setNewUserFirstName('')
      setNewUserLastName('')
      setNewUserDisplayName('')
      setNewUserIsActive(true)
      setErrorMessage(`Utilisateur cree : ${result.email}`)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de creation utilisateur')
    } finally {
      setUserToolLoading(false)
    }
  }

  async function handleForgotPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const targetEmail = authEmail.trim()
    if (!targetEmail) {
      setErrorMessage('Renseigne un email pour recevoir le lien de reinitialisation')
      return
    }
    setForgotPasswordPending(true)
    setErrorMessage(null)
    try {
      await sendPasswordResetEmail({ email: targetEmail })
      setErrorMessage(`Lien de reinitialisation envoye a ${targetEmail}`)
      setForgotPasswordOpen(false)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur d envoi de reinitialisation')
    } finally {
      setForgotPasswordPending(false)
    }
  }

  async function handleResetRecoveredPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextPassword = recoveryPassword.trim()
    const confirmation = recoveryPasswordConfirm.trim()
    if (!nextPassword || !confirmation) {
      setErrorMessage('Renseigne et confirme le nouveau mot de passe')
      return
    }
    if (nextPassword !== confirmation) {
      setErrorMessage('Les mots de passe ne correspondent pas')
      return
    }
    if (nextPassword.length < 8) {
      setErrorMessage('Le mot de passe doit contenir au moins 8 caracteres')
      return
    }
    setRecoveryPending(true)
    setErrorMessage(null)
    try {
      await updatePassword(nextPassword)
      await signOut()
      setRecoveryMode(false)
      setRecoveryPassword('')
      setRecoveryPasswordConfirm('')
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, document.title, window.location.pathname)
      }
      setErrorMessage('Mot de passe mis a jour. Vous pouvez maintenant vous connecter.')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de mise a jour du mot de passe')
    } finally {
      setRecoveryPending(false)
    }
  }

  async function openUserTool() {
    setUserToolOpen(true)
    setUserToolLoading(true)
    setErrorMessage(null)
    try {
      setAppUsers(await loadAppUsers())
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des utilisateurs')
    } finally {
      setUserToolLoading(false)
    }
  }

  function startEditUser(user: UserProfile) {
    setEditingUserId(user.id)
    setEditUserEmail(user.email ?? '')
    setEditUserRole(user.role)
    setEditUserFirstName(user.first_name ?? '')
    setEditUserLastName(user.last_name ?? '')
    setEditUserDisplayName(user.display_name ?? '')
    setEditUserIsActive(Boolean(user.is_active))
  }

  function resetEditUser() {
    setEditingUserId(null)
    setEditUserEmail('')
    setEditUserRole('commercial')
    setEditUserFirstName('')
    setEditUserLastName('')
    setEditUserDisplayName('')
    setEditUserIsActive(true)
  }

  async function handleUpdateAppUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editingUserId) return
    setUserToolLoading(true)
    setErrorMessage(null)
    try {
      const displayName = editUserDisplayName.trim() || `${editUserFirstName.trim()} ${editUserLastName.trim()}`.trim()
      await updateAppUser({
        id: editingUserId,
        email: editUserEmail.trim(),
        role: editUserRole,
        firstName: editUserFirstName.trim(),
        lastName: editUserLastName.trim(),
        displayName,
        isActive: editUserIsActive,
      })
      setAppUsers(await loadAppUsers())
      resetEditUser()
      setErrorMessage('Utilisateur mis a jour')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de mise a jour utilisateur')
    } finally {
      setUserToolLoading(false)
    }
  }

  async function handleSendPasswordReset(email: string | null | undefined) {
    const targetEmail = email?.trim()
    if (!targetEmail) {
      setErrorMessage('Email utilisateur manquant')
      return
    }
    setUserToolLoading(true)
    setErrorMessage(null)
    try {
      await sendPasswordResetEmail({ email: targetEmail })
      setErrorMessage(`Lien de reinitialisation envoye a ${targetEmail}`)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur d envoi de reinitialisation')
    } finally {
      setUserToolLoading(false)
    }
  }

  async function handleSaveDiffusionTargets() {
    if (!profile || !diffusionModalMandat) return
    setDiffusionTargetsSaving(true)
    setErrorMessage(null)
    try {
      const rows = await saveDiffusionTargets({
        mandat: diffusionModalMandat,
        targets: diffusionPortalRows.map((portal) => ({
          hektor_broadcast_id: portal.hektorBroadcastId,
          portal_key: portal.portalKey,
          target_state: (diffusionDraftTargets[portal.portalKey] ?? portal.observedEnabled) ? 'enabled' : 'disabled',
        })),
        requestedByName: profile.display_name ?? profile.email,
        requestedByRole: profile.role,
      })
      setDiffusionTargets(rows)
      setDiffusionDraftTargets(Object.fromEntries(rows.map((item) => [item.portal_key ?? item.hektor_broadcast_id, item.target_state === 'enabled'])))
      setDiffusionTargetsSavedAt(new Date().toISOString())
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de sauvegarde des cibles diffusion')
    } finally {
      setDiffusionTargetsSaving(false)
    }
  }

  async function handleApplyDiffusionTargetsOnHektor(dryRun = false) {
    if (!diffusionModalMandat) return
    setDiffusionApplyPending(true)
    setErrorMessage(null)
    try {
      const result = await applyDiffusionTargetsOnHektor({
        appDossierId: diffusionModalMandat.app_dossier_id,
        dryRun,
        ensureDiffusable: true,
      })
      setDiffusionApplyResult(result)
      if (!dryRun) {
        const appliedPortalsResume = buildPortalsResume(
          result.applied
            .filter((item) => item.action === 'add')
            .map((item) => safeText(item.portal_key)),
        )
        const validationValue =
          result.observed_validation && isValidationApproved(result.observed_validation)
            ? result.observed_validation
            : result.validation_state && isValidationApproved(result.validation_state)
              ? result.validation_state
              : diffusionModalMandat.validation_diffusion_state ?? null
        const diffusableValue =
          result.observed_diffusable === '1'
            ? '1'
            : result.observed_diffusable === '0'
              ? '0'
              : diffusionModalMandat.diffusable ?? '0'
        await setDossierHektorState(diffusionModalMandat.app_dossier_id, {
          validationDiffusionState: validationValue,
          diffusable: diffusableValue === '1',
          portailsResume: appliedPortalsResume,
          nbPortailsActifs: uniquePortalKeys(appliedPortalsResume.split(',')).length,
        })
        setDossiers((current) => current.map((item) => item.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...item, validation_diffusion_state: validationValue, diffusable: diffusableValue, portails_resume: appliedPortalsResume, nb_portails_actifs: uniquePortalKeys(appliedPortalsResume.split(',')).length } : item))
        setMandats((current) => current.map((item) => item.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...item, validation_diffusion_state: validationValue, diffusable: diffusableValue, portails_resume: appliedPortalsResume, nb_portails_actifs: uniquePortalKeys(appliedPortalsResume.split(',')).length } : item))
        setSelectedDossier((current) => current && current.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...current, validation_diffusion_state: validationValue, diffusable: diffusableValue, portails_resume: appliedPortalsResume, nb_portails_actifs: uniquePortalKeys(appliedPortalsResume.split(',')).length } : current)
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur d application Hektor')
    } finally {
      setDiffusionApplyPending(false)
    }
  }

  async function handleCommitDiffusionTargets() {
    if (!profile || !diffusionModalMandat || diffusionTargetsSaving || diffusionTargetsLoading || diffusionApplyPending) return
    setDiffusionTargetsSaving(true)
    setDiffusionApplyPending(true)
    setErrorMessage(null)
    try {
      const targetPayload = diffusionPortalRows.map((portal) => ({
        hektor_broadcast_id: portal.hektorBroadcastId,
        portal_key: portal.portalKey,
        target_state: (diffusionDraftTargets[portal.portalKey] ?? portal.observedEnabled) ? 'enabled' : 'disabled' as 'enabled' | 'disabled',
      }))
      const rows = await saveDiffusionTargets({
        mandat: diffusionModalMandat,
        targets: targetPayload,
        requestedByName: profile.display_name ?? profile.email,
        requestedByRole: profile.role,
      })
      const expectedByPortal = new Map(targetPayload.map((item) => [item.portal_key ?? item.hektor_broadcast_id, item.target_state]))
      const actualByPortal = new Map(rows.map((item) => [item.portal_key ?? item.hektor_broadcast_id, item.target_state]))
      const persistedSelectionMatches = targetPayload.every((item) => actualByPortal.get(item.portal_key ?? item.hektor_broadcast_id) === item.target_state)
      setDiffusionTargets(rows)
      setDiffusionDraftTargets(Object.fromEntries(rows.map((item) => [item.portal_key ?? item.hektor_broadcast_id, item.target_state === 'enabled'])))
      setDiffusionTargetsSavedAt(new Date().toISOString())
      if (!persistedSelectionMatches) {
        const expectedEnabled = Array.from(expectedByPortal.entries()).filter(([, state]) => state === 'enabled').map(([portal]) => portal)
        const actualEnabled = Array.from(actualByPortal.entries()).filter(([, state]) => state === 'enabled').map(([portal]) => portal)
        throw new Error(`Les passerelles choisies n'ont pas ete enregistrees correctement. Attendu: ${expectedEnabled.join(', ') || 'aucune'} ; sauvegarde: ${actualEnabled.join(', ') || 'aucune'}.`)
      }
      const result = await applyDiffusionTargetsOnHektor({
        appDossierId: diffusionModalMandat.app_dossier_id,
        dryRun: false,
        ensureDiffusable: true,
      })
      setDiffusionApplyResult(result)
      const validationValue =
        result.observed_validation && isValidationApproved(result.observed_validation)
          ? result.observed_validation
          : result.validation_state && isValidationApproved(result.validation_state)
            ? result.validation_state
            : diffusionModalMandat.validation_diffusion_state ?? null
      const diffusableValue =
        result.observed_diffusable === '1'
          ? '1'
          : result.observed_diffusable === '0'
            ? '0'
            : diffusionModalMandat.diffusable ?? '0'
      const persistedPortalsResume = buildPortalsResume(
        rows
          .filter((item) => item.target_state === 'enabled')
          .map((item) => item.portal_key ?? item.hektor_broadcast_id),
      )
      await setDossierHektorState(diffusionModalMandat.app_dossier_id, {
        validationDiffusionState: validationValue,
        diffusable: diffusableValue === '1',
        portailsResume: persistedPortalsResume,
        nbPortailsActifs: uniquePortalKeys(persistedPortalsResume.split(',')).length,
      })
      setDossiers((current) => current.map((item) => item.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...item, validation_diffusion_state: validationValue, diffusable: diffusableValue, portails_resume: persistedPortalsResume, nb_portails_actifs: uniquePortalKeys(persistedPortalsResume.split(',')).length } : item))
      setMandats((current) => current.map((item) => item.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...item, validation_diffusion_state: validationValue, diffusable: diffusableValue, portails_resume: persistedPortalsResume, nb_portails_actifs: uniquePortalKeys(persistedPortalsResume.split(',')).length } : item))
      setSelectedDossier((current) => current && current.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...current, validation_diffusion_state: validationValue, diffusable: diffusableValue, portails_resume: persistedPortalsResume, nb_portails_actifs: uniquePortalKeys(persistedPortalsResume.split(',')).length } : current)
      const refreshedBroadcasts = await loadMandatBroadcasts(diffusionModalMandat.app_dossier_id).catch(() => null)
      if (refreshedBroadcasts) {
        setMandatBroadcasts(refreshedBroadcasts)
        const refreshedPortalsResume = buildPortalsResume(refreshedBroadcasts.map((item) => item.passerelle_key))
        setDossiers((current) => current.map((item) => item.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...item, portails_resume: refreshedPortalsResume } : item))
        setMandats((current) => current.map((item) => item.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...item, portails_resume: refreshedPortalsResume } : item))
        setSelectedDossier((current) => current && current.app_dossier_id === diffusionModalMandat.app_dossier_id ? { ...current, portails_resume: refreshedPortalsResume } : current)
      }
      const refreshedTargets = await loadDiffusionTargets(diffusionModalMandat.app_dossier_id).catch(() => null)
      if (refreshedTargets) {
        setDiffusionTargets(refreshedTargets)
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur d application Hektor')
    } finally {
      setDiffusionTargetsSaving(false)
      setDiffusionApplyPending(false)
    }
  }

  async function handleSetSelectedDossierDiffusable(nextValue: boolean) {
    if (!selectedDossier || detailDiffusablePending) return
    setDetailDiffusableDraft(nextValue)
    setDetailDiffusablePending(true)
    setErrorMessage(null)
    try {
      const result = await setDossierDiffusableOnHektor({
        appDossierId: selectedDossier.app_dossier_id,
        diffusable: nextValue,
      })
      const observedValue = result.observed_diffusable === '1'
      const diffusableValue = observedValue ? '1' : '0'
      await setDossierHektorState(selectedDossier.app_dossier_id, {
        diffusable: observedValue,
      })
      setDetailDiffusableDraft(observedValue)
      setDetailDiffusableObserved(observedValue)
      setDetailDiffusableSaved(observedValue)
      setSelectedDossier((current) => (current ? { ...current, diffusable: diffusableValue } : current))
      setDossiers((current) => current.map((item) => item.app_dossier_id === selectedDossier.app_dossier_id ? { ...item, diffusable: diffusableValue } : item))
      setMandats((current) => current.map((item) => item.app_dossier_id === selectedDossier.app_dossier_id ? { ...item, diffusable: diffusableValue } : item))
    } catch (error) {
      setDetailDiffusableDraft(isDiffusableValue(selectedDossier.diffusable))
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de mise a jour diffusable')
    } finally {
      setDetailDiffusablePending(false)
    }
  }

  async function handleSetSelectedDossierValidation(nextValue: boolean) {
    if (!selectedDossier || detailValidationPending) return
    setDetailValidationPending(true)
    setErrorMessage(null)
    setDetailValidationDraft(nextValue ? 'oui' : 'non')
    try {
      const result = await setDossierValidationOnHektor({
        appDossierId: selectedDossier.app_dossier_id,
        state: nextValue ? 1 : 0,
      })
      const validationValue =
        result.observed_validation && normalizeValidationState(result.observed_validation)
          ? (isValidationApproved(result.observed_validation) ? 'oui' : 'non')
          : nextValue ? 'oui' : 'non'
      const diffusableValue = result.observed_diffusable === '1' ? '1' : result.observed_diffusable === '0' ? '0' : selectedDossier.diffusable ?? null
      const patch = {
        validation_diffusion_state: validationValue,
        diffusable: diffusableValue,
      }
      await setDossierHektorState(selectedDossier.app_dossier_id, {
        validationDiffusionState: validationValue,
        diffusable: diffusableValue === '1',
      })
      setDetailValidationDraft(validationValue)
      setDetailValidationObserved(validationValue)
      setDetailValidationSaved(validationValue)
      setSelectedDossier((current) => (current ? { ...current, ...patch } : current))
      setDossiers((current) => current.map((item) => item.app_dossier_id === selectedDossier.app_dossier_id ? { ...item, ...patch } : item))
      setMandats((current) => current.map((item) => item.app_dossier_id === selectedDossier.app_dossier_id ? { ...item, ...patch } : item))
      if (typeof patch.diffusable !== 'undefined') {
        const observed = isDiffusableValue(patch.diffusable)
        setDetailDiffusableDraft(observed)
        setDetailDiffusableObserved(observed)
        setDetailDiffusableSaved(observed)
      }
      setErrorMessage(nextValue ? 'Validation Hektor demandee et relue.' : 'Invalidation Hektor demandee et relue.')
    } catch (error) {
      const currentValidation = isValidationApproved(selectedDossier.validation_diffusion_state) ? 'oui' : 'non'
      setDetailValidationDraft(currentValidation)
      setDetailValidationObserved(currentValidation)
      setDetailValidationSaved(currentValidation)
      setErrorMessage(error instanceof Error ? error.message : 'Erreur de mise a jour validation Hektor')
    } finally {
      setDetailValidationPending(false)
    }
  }

  const detail = useMemo(() => detailPayload(selectedDossier), [selectedDossier])
  const visibleDossiersCount = dossiersTotal || dossiers.length
  const dossierTotalPages = totalPages(dossiersTotal, dossierPageSize)
  const mandatTotalPages = totalPages(mandatsTotal, mandatPageSize)
  const workItemTotalPages = totalPages(workItemsTotal, workItemPageSize)
  const activeFilters = useMemo(() => activeFilterEntries(filters), [filters])
  const screenHeader = useMemo(() => {
    if (screen === 'annonces') {
      return { title: 'Annonces', copy: '' }
    }
    if (screen === 'mandats') {
      return {
        title: mandatDrilldownLabel?.title ?? 'Liste des annonces',
        copy: '',
      }
    }
    if (screen === 'registre') {
      return { title: 'Registre des mandats', copy: '' }
    }
    return { title: 'Suivi des mandats', copy: '' }
  }, [screen, mandatDrilldownLabel])
  const dossierCountLabel = activeFilters.length > 0 ? 'Dossiers apres filtres' : 'Tous les dossiers'
  const address = [detail.adresse_privee_listing || detail.adresse_detail, detail.code_postal_public_listing || detail.code_postal_prive_detail || detail.code_postal, detail.ville_publique_listing || detail.ville_privee_detail || selectedDossier?.ville]
    .filter(Boolean)
    .join(', ')
  const linkedWorkItems = useMemo(() => workItems.filter((item) => item.app_dossier_id === selectedDossier?.app_dossier_id), [workItems, selectedDossier])
  const selectedDossierRequest = useMemo(
    () => (selectedDossier ? latestDiffusionRequest(diffusionRequests, selectedDossier.app_dossier_id) : null),
    [diffusionRequests, selectedDossier],
  )
  const selectedDossierRequests = useMemo(
    () => (selectedDossier ? diffusionRequests.filter((item) => item.app_dossier_id === selectedDossier.app_dossier_id) : []),
    [diffusionRequests, selectedDossier],
  )
  const selectedDossierRequestEvents = useMemo(
    () => (selectedDossierRequest ? diffusionRequestEvents.filter((item) => String(item.diffusion_request_id) === String(selectedDossierRequest.id)) : []),
    [diffusionRequestEvents, selectedDossierRequest],
  )
  const selectedDossierAllRequestEvents = useMemo(
    () =>
      selectedDossier
        ? diffusionRequestEvents.filter((item) =>
            selectedDossierRequests.some((request) => String(request.id) === String(item.diffusion_request_id)),
          )
        : [],
    [diffusionRequestEvents, selectedDossier, selectedDossierRequests],
  )
  const selectedMandat = useMemo(
    () =>
      mandats.find((item) => item.app_dossier_id === selectedMandatId) ??
      (selectedDossier && selectedDossier.app_dossier_id === selectedMandatId ? (selectedDossier as unknown as MandatRecord) : null),
    [mandats, selectedDossier, selectedMandatId],
  )
  const selectedRegisterMandat = useMemo(
    () => mandats.find((item) => (item.register_row_id ?? null) === selectedRegisterRowId) ?? null,
    [mandats, selectedRegisterRowId],
  )
  const requestModalMandat = useMemo(
    () =>
      mandats.find((item) => item.app_dossier_id === requestModalMandatId) ??
      (selectedDossier && selectedDossier.app_dossier_id === requestModalMandatId ? (selectedDossier as unknown as MandatRecord) : null),
    [mandats, requestModalMandatId, selectedDossier],
  )
  const requestModalRequest = useMemo(() => requestModalMandatId != null ? latestDiffusionRequest(diffusionRequests, requestModalMandatId, requestModalType) : null, [diffusionRequests, requestModalMandatId, requestModalType])
  const requestModalEvents = useMemo(
    () => (requestModalRequest ? diffusionRequestEvents.filter((item) => String(item.diffusion_request_id) === String(requestModalRequest.id)) : []),
    [diffusionRequestEvents, requestModalRequest],
  )
  const diffusionModalMandat = useMemo(() => mandats.find((item) => item.app_dossier_id === diffusionModalMandatId) ?? null, [mandats, diffusionModalMandatId])
  const diffusionModalRequest = useMemo(
    () => (diffusionModalMandatId != null ? latestDiffusionRequest(diffusionRequests, diffusionModalMandatId) : null),
    [diffusionRequests, diffusionModalMandatId],
  )
  const diffusionModalRequestEvents = useMemo(
    () => (diffusionModalRequest ? diffusionRequestEvents.filter((item) => String(item.diffusion_request_id) === String(diffusionModalRequest.id)) : []),
    [diffusionModalRequest, diffusionRequestEvents],
  )
  const diffusionModalBroadcasts = useMemo(
    () => (diffusionModalMandatId != null && selectedMandatId === diffusionModalMandatId ? mandatBroadcasts : []),
    [diffusionModalMandatId, selectedMandatId, mandatBroadcasts],
  )
  const diffusionPortalRows = useMemo(() => {
    const grouped = new Map<string, { portalKey: string; hektorBroadcastId: string; observedEnabled: boolean; hasError: boolean; details: string[] }>()
    for (const target of diffusionTargets) {
      const portalKey = (target.portal_key ?? '').trim() || 'passerelle_inconnue'
      const hektorBroadcastId = (target.hektor_broadcast_id ?? '').trim() || portalKey
      const targetEnabled = target.target_state === 'enabled'
      grouped.set(portalKey, {
        portalKey,
        hektorBroadcastId,
        observedEnabled: targetEnabled,
        hasError: false,
        details: [targetEnabled ? 'Cible phase 2 · active' : 'Cible phase 2 · inactive'],
      })
    }
    for (const item of diffusionModalBroadcasts) {
      const portalKey = (item.passerelle_key ?? '').trim() || 'passerelle_inconnue'
      const hektorBroadcastId = grouped.get(portalKey)?.hektorBroadcastId ?? portalKey
      const observedEnabled = item.current_state === 'broadcasted' || item.export_status === 'exported' || item.is_success === true
      const statusDetail = [item.current_state ?? '-', item.export_status ?? '-', item.commercial_nom ?? item.commercial_key ?? '-'].join(' - ')
      const current = grouped.get(portalKey)
      if (current) {
        current.observedEnabled = current.observedEnabled || observedEnabled
        current.hasError = current.hasError || Boolean(item.is_error)
        current.details.push(statusDetail)
      } else {
        grouped.set(portalKey, {
          portalKey,
          hektorBroadcastId,
          observedEnabled,
          hasError: Boolean(item.is_error),
          details: [statusDetail],
        })
      }
    }
    return Array.from(grouped.values()).sort((a, b) => a.portalKey.localeCompare(b.portalKey, 'fr'))
  }, [diffusionModalBroadcasts, diffusionTargets])
  const visibleMandatIds = useMemo(() => new Set(mandats.map((item) => item.app_dossier_id)), [mandats])
  const visibleSuiviRequests = useMemo(() => diffusionRequests.filter((item) => visibleMandatIds.has(item.app_dossier_id)), [diffusionRequests, visibleMandatIds])
  const requestModalState = useMemo(
    () => (requestModalMandat ? negociateurDiffusionState(requestModalMandat, requestModalRequest) : null),
    [requestModalMandat, requestModalRequest],
  )
  const requestModalPaulineState = useMemo(
    () => (requestModalMandat ? paulineDiffusionState(requestModalMandat, requestModalRequest) : null),
    [requestModalMandat, requestModalRequest],
  )
  const requestModalEffectiveType = useMemo(
    () => (requestModalRequest?.request_type === 'demande_baisse_prix' || (!requestModalRequest && requestModalType === 'demande_baisse_prix') ? 'demande_baisse_prix' : 'demande_diffusion'),
    [requestModalRequest, requestModalType],
  )
  const requestModalEligibleForPriceDrop = useMemo(
    () => isValidationApproved(requestModalMandat?.validation_diffusion_state ?? null),
    [requestModalMandat],
  )
  const requestModalRefusalOptions = useMemo(
    () => (requestModalEffectiveType === 'demande_baisse_prix' ? priceDropRefusalReasonOptions : refusalReasonOptions),
    [requestModalEffectiveType],
  )

  useEffect(() => {
    if (!diffusionModalOpen || diffusionModalMandatId == null || (hasSupabaseEnv && !session)) return
    let cancelled = false
    setDiffusionTargetsLoading(true)
    loadDiffusionTargets(diffusionModalMandatId)
      .then(async (rows) => {
        if (cancelled) return
        if (rows.length === 0 && diffusionModalMandat && isValidationApproved(diffusionModalMandat.validation_diffusion_state)) {
          const preview = await previewDefaultDiffusionTargets({ appDossierId: diffusionModalMandatId }).catch(() => null)
          const previewTargets = preview?.targets ?? []
          if (previewTargets.length > 0) {
            rows = previewTargets.map((item) => ({
              app_dossier_id: item.app_dossier_id,
              hektor_annonce_id: Number(item.hektor_annonce_id),
              hektor_broadcast_id: item.hektor_broadcast_id,
              portal_key: item.portal_key,
              target_state: item.target_state,
              source_ref: 'console_preview',
              note: null,
              requested_by_role: 'app',
              requested_by_name: null,
              requested_at: null,
              last_applied_at: null,
              last_apply_status: null,
              last_apply_error: null,
            }))
          }
        }
        if (!cancelled) setDiffusionTargets(rows)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des cibles diffusion')
      })
      .finally(() => {
        if (!cancelled) setDiffusionTargetsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [diffusionModalOpen, diffusionModalMandatId, diffusionModalMandat, profile, session])

  useEffect(() => {
    if (!diffusionModalOpen || diffusionPortalRows.length === 0) return
    setDiffusionDraftTargets((current) => {
      if (Object.keys(current).length > 0) return current
      return Object.fromEntries(
        diffusionPortalRows.map((item) => [item.portalKey, item.observedEnabled]),
      )
    })
  }, [diffusionModalOpen, diffusionModalMandatId, diffusionPortalRows])
  const diffusionHasUnsavedChanges = useMemo(
    () => diffusionPortalRows.some((portal) => (diffusionDraftTargets[portal.portalKey] ?? portal.observedEnabled) !== portal.observedEnabled),
    [diffusionDraftTargets, diffusionPortalRows],
  )
  const diffusionEnabledCount = useMemo(
    () => diffusionPortalRows.filter((portal) => (diffusionDraftTargets[portal.portalKey] ?? portal.observedEnabled)).length,
    [diffusionDraftTargets, diffusionPortalRows],
  )

  const headerMetrics = useMemo<HeaderMetricItem[]>(() => {
    if (screen === 'annonces') {
      return [
        { label: 'Dossiers visibles', value: new Intl.NumberFormat('fr-FR').format(visibleDossiersCount), tone: 'volume', action: null },
        { label: 'Demandes visibles', value: new Intl.NumberFormat('fr-FR').format(workItemsTotal || workItems.length), tone: 'neutral', action: null },
      ]
    }
    if (screen === 'mandats') {
      return [
        { label: 'Annonces', value: new Intl.NumberFormat('fr-FR').format(mandatStats.total), tone: 'volume', action: 'all_annonces' },
        { label: 'Offres en cours', value: new Intl.NumberFormat('fr-FR').format(mandatStats.offresEnCours), tone: 'affaires', action: 'offres_en_cours' },
        { label: 'Offres refusées', value: new Intl.NumberFormat('fr-FR').format(mandatStats.offresRefusees), tone: 'affaires', action: 'offres_refusees' },
        { label: 'Compromis en cours', value: new Intl.NumberFormat('fr-FR').format(mandatStats.compromisEnCours), tone: 'affaires', action: 'compromis_en_cours' },
        { label: 'Compromis annulés', value: new Intl.NumberFormat('fr-FR').format(mandatStats.compromisAnnules), tone: 'affaires', action: 'compromis_annules' },
        { label: 'Mandats valides', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatValide), tone: 'diffusion', action: 'mandat_valide' },
        { label: 'Mandats non valides', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatNonValide), tone: 'diffusion', action: 'mandat_non_valide' },
        { label: 'Mandat diffusé', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatDiffuse), tone: 'diffusion', action: 'mandat_diffuse' },
        { label: 'Mandat non diffusé', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatNonDiffuse), tone: 'diffusion', action: 'mandat_non_diffuse' },
        { label: 'Sans mandat', value: new Intl.NumberFormat('fr-FR').format(mandatStats.withoutMandat), tone: 'diffusion', action: 'sans_mandat' },
        { label: 'Demande envoyée', value: new Intl.NumberFormat('fr-FR').format(commercialRequestStats.sent), tone: 'demandes', action: 'demandes_envoyees' },
        { label: 'Correction en attente', value: new Intl.NumberFormat('fr-FR').format(commercialRequestStats.waitingCorrection), tone: 'demandes', action: 'correction_attente' },
        { label: 'Diffuse sur LeBonCoin', value: new Intl.NumberFormat('fr-FR').format(mandatStats.leboncoin), tone: 'diffusion', action: 'leboncoin' },
        { label: "Diffuse sur Bien'ici", value: new Intl.NumberFormat('fr-FR').format(mandatStats.bienici), tone: 'diffusion', action: 'bienici' },
      ]
    }
    if (screen === 'registre') {
      return [
        { label: 'Mandats enregistrés', value: new Intl.NumberFormat('fr-FR').format(Math.max(0, mandatStats.total - mandatStats.withoutMandat)), tone: 'volume', action: 'all_annonces' },
        { label: 'Mandats valides', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatValide), tone: 'diffusion', action: 'mandat_valide' },
        { label: 'Mandats non validés', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatNonValide), tone: 'warning', action: 'mandat_non_valide' },
        { label: 'Mandats diffusable', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatDiffuse), tone: 'diffusion', action: 'mandat_diffuse' },
        { label: 'Mandats non diffusable', value: new Intl.NumberFormat('fr-FR').format(mandatStats.mandatNonDiffuse), tone: 'diffusion', action: 'mandat_non_diffuse' },
      ]
    }
    return [
      { label: 'Demandes à traiter', value: new Intl.NumberFormat('fr-FR').format(suiviRequestStats.pendingOrInProgress), tone: 'demandes', action: 'suivi_a_traiter' },
      { label: 'Demandes acceptées', value: new Intl.NumberFormat('fr-FR').format(suiviRequestStats.acceptedHistorical), tone: 'demandes', action: 'suivi_acceptees' },
      { label: 'Demandes rejetées', value: new Intl.NumberFormat('fr-FR').format(suiviRequestStats.refused), tone: 'demandes', action: 'suivi_rejetees' },
      { label: 'Affaires en cours', value: new Intl.NumberFormat('fr-FR').format(mandatStats.affairesEnCours), tone: 'affaires', action: null },
    ]
  }, [screen, visibleDossiersCount, workItemsTotal, workItems.length, mandatStats, commercialRequestStats, suiviRequestStats])
  const primaryCommercialMetrics = useMemo(
    () => headerMetrics.filter((item) => ['Annonces', 'Offres en cours', 'Mandats valides', 'Correction en attente'].includes(item.label)),
    [headerMetrics],
  )
  const secondaryCommercialMetrics = useMemo(
    () => headerMetrics.filter((item) => !['Annonces', 'Offres en cours', 'Mandats valides', 'Correction en attente'].includes(item.label)),
    [headerMetrics],
  )
  const isAdmin = profile?.role === 'admin'
  const inferredUserNegotiatorContext = useMemo(() => {
    if (!sessionEmail) return null
    const dossierMatch = dossiers.find((item) => normalizeEmail(item.negociateur_email) === sessionEmail)
    if (dossierMatch) {
      return {
        commercial_nom: dossierMatch.commercial_nom ?? null,
        negociateur_email: dossierMatch.negociateur_email ?? null,
        agence_nom: dossierMatch.agence_nom ?? null,
      } satisfies UserNegotiatorContext
    }
    const mandatMatch = mandats.find((item) => normalizeEmail(item.negociateur_email) === sessionEmail)
    if (mandatMatch) {
      return {
        commercial_nom: mandatMatch.commercial_nom ?? null,
        negociateur_email: mandatMatch.negociateur_email ?? null,
        agence_nom: mandatMatch.agence_nom ?? null,
      } satisfies UserNegotiatorContext
    }
    const workItemMatch = workItems.find((item) => normalizeEmail(item.negociateur_email) === sessionEmail)
    if (workItemMatch) {
      return {
        commercial_nom: workItemMatch.commercial_nom ?? null,
        negociateur_email: workItemMatch.negociateur_email ?? null,
        agence_nom: workItemMatch.agence_nom ?? null,
      } satisfies UserNegotiatorContext
    }
    return null
  }, [dossiers, mandats, sessionEmail, workItems])
  const resolvedUserNegotiatorContext = userNegotiatorContext ?? inferredUserNegotiatorContext
  useEffect(() => {
    if (screen === 'suivi' && !isAdmin) setScreen('mandats')
  }, [screen, isAdmin])
  const images = useMemo(() => {
    const rawImages = [
      ...parseJson<Array<Record<string, unknown>>>(detail.images_json, []),
      ...parseJson<Array<Record<string, unknown>>>(detail.images_preview_json, []),
    ]
    const seen = new Set<string>()
    return rawImages
      .map((item) => ({
        url: safeText(item.url) || safeText(item.full) || safeText(item.path) || safeText(item.src),
        legend: safeText(item.legend) || safeText(item.title) || safeText(item.alt),
      }))
      .filter((item) => item.url && !seen.has(item.url) && seen.add(item.url))
  }, [detail])
  const contacts = useMemo(() => {
    return parseJson<Array<Record<string, unknown>>>(detail.proprietaires_json, []).map((item, index) => {
      const coords = (item.coordonnees as Record<string, unknown> | undefined) ?? {}
      const locality = ((item.localite as Record<string, unknown> | undefined)?.localite as Record<string, unknown> | undefined) ?? {}
      return {
        id: `${index}-${safeText(item.nom)}`,
        name: [safeText(item.civilite), safeText(item.prenom), safeText(item.nom)].filter(Boolean).join(' ') || `Contact ${index + 1}`,
        role: Array.isArray(item.typologie) ? item.typologie.join(', ') : '',
        phone: safeText(coords.portable) || safeText(coords.telephone),
        email: safeText(coords.email),
        address: [safeText(locality.adresse), safeText(locality.code), safeText(locality.ville)].filter(Boolean).join(', '),
        comment: sanitizeContactComment(item.commentaires as string | null | undefined),
      }
    })
  }, [detail])
  const notes = useMemo(() => {
    const list = parseJson<Array<Record<string, unknown>>>(detail.notes_json, [])
      .map((item, index) => ({
        id: `${index}-${safeText(item.type)}`,
        title: safeText(item.type) || `Note ${index + 1}`,
        date: safeText(item.date),
        content: safeText(item.content),
      }))
      .filter((item) => item.content)
    if (detail.note_hektor_principale) {
      list.unshift({ id: 'hektor-main-note', title: 'Synthese Hektor', date: '', content: detail.note_hektor_principale })
    }
    return list
  }, [detail])
  const texts = useMemo(() => {
    const blocks: Array<{ id: string; title: string; html: string }> = []
    const seen = new Set<string>()
    const pushBlock = (id: string, title: string, html: string | null | undefined) => {
      const cleaned = safeText(html)
      if (!cleaned) return
      const fingerprint = normalizeHtmlFingerprint(cleaned)
      if (!fingerprint || seen.has(fingerprint)) return
      seen.add(fingerprint)
      blocks.push({ id, title, html: cleaned })
    }

    pushBlock('principal', detail.texte_principal_titre || 'Descriptif principal', detail.texte_principal_html)
    if (detail.corps_listing_html && normalizeHtmlFingerprint(detail.corps_listing_html) !== normalizeHtmlFingerprint(detail.texte_principal_html)) {
      pushBlock('listing', 'Complement listing', detail.corps_listing_html)
    }
    parseJson<Array<Record<string, unknown>>>(detail.textes_json, []).forEach((item, index) => {
      const text = safeText(item.text)
      if (text) {
        pushBlock(
          `extra-${index}`,
          [safeText(item.type), safeText(item.lang), safeText(item.titre)].filter(Boolean).join(' - ') || `Texte ${index + 1}`,
          text.replace(/\n/g, '<br>'),
        )
      }
    })
    return blocks.slice(0, 2)
  }, [detail])
  const mandatDetails = useMemo(() => {
    const rawMandats = parseJson<Array<Record<string, unknown>>>(detail.mandats_json, [])
    if (rawMandats.length > 0) {
      const grouped = new Map<string, Array<Record<string, unknown>>>()
      rawMandats.forEach((item, index) => {
        const numero = safeText(item.numero) || `Mandat ${index + 1}`
        grouped.set(numero, [...(grouped.get(numero) ?? []), item])
      })
      return Array.from(grouped.entries()).map(([numero, versions], index) => {
        const sortedVersions = versions
          .slice()
          .sort((a, b) => {
            const score = (entry: Record<string, unknown>) =>
              ['type', 'debut', 'fin', 'cloture', 'montant', 'mandants', 'note'].reduce((count, key) => count + (safeText(entry[key]) ? 1 : 0), 0)
            const scoreDiff = score(b) - score(a)
            if (scoreDiff !== 0) return scoreDiff
            return safeText(b.id).localeCompare(safeText(a.id), 'fr')
          })
        const current = sortedVersions[0]
        const embeddedAvenants = sortedVersions.flatMap((item) => {
          const avenants = Array.isArray(item.avenants) ? item.avenants : []
          return avenants.filter((entry): entry is Record<string, unknown> => Boolean(entry && typeof entry === 'object'))
        })
        return {
          id: `${index}-${numero}`,
          title: [numero, safeText(current.type)].filter(Boolean).join(' - ') || `Mandat ${index + 1}`,
          lines: [
            ['Enregistrement', safeText(current.dateenr) || safeText(current.date_enregistrement)] as [string, string],
            ['Debut', safeText(current.debut)] as [string, string],
            ['Fin', safeText(current.fin)] as [string, string],
            ['Cloture', safeText(current.cloture)] as [string, string],
            ['Montant', safeText(current.montant)] as [string, string],
            ['Mandants', safeText(current.mandants)] as [string, string],
            ['Versions', sortedVersions.length > 1 ? `${sortedVersions.length} versions détectées` : '1 version'] as [string, string],
            ['Avenants', embeddedAvenants.length > 0 ? embeddedAvenants.map((entry) => [safeText(entry.numero), safeText(entry.date), safeText(entry.detail)].filter(Boolean).join(' · ')).join(' | ') : ''] as [string, string],
            ['Note', safeText(current.note)] as [string, string],
          ].filter((entry) => entry[1]),
        }
      })
    }
    return [[
      ['Numero source', detail.mandat_numero_source ?? ''] as [string, string],
      ['Type source', detail.mandat_type_source ?? ''] as [string, string],
      ['Type', detail.mandat_type ?? ''] as [string, string],
      ['Enregistrement', detail.mandat_date_enregistrement ?? ''] as [string, string],
      ['Debut', detail.mandat_date_debut ?? ''] as [string, string],
      ['Fin', detail.mandat_date_fin ?? ''] as [string, string],
      ['Cloture', detail.mandat_date_cloture ?? ''] as [string, string],
      ['Montant', detail.mandat_montant == null ? '' : String(detail.mandat_montant)] as [string, string],
      ['Mandants', detail.mandants_texte ?? ''] as [string, string],
      ['Note', detail.mandat_note ?? ''] as [string, string],
    ].filter((entry) => entry[1])]
      .filter((entry) => entry.length > 0)
      .map((lines, index) => ({ id: `source-${index}`, title: 'Mandat source', lines }))
  }, [detail])

  if (hasSupabaseEnv && recoveryMode && !bootLoading) {
    return (
      <div className="login-shell">
        <section className="login-panel">
          <p className="eyebrow">Récupération</p>
          <h1>Définir un nouveau mot de passe</h1>
          <p className="hero-copy">Choisissez un nouveau mot de passe pour finaliser la récupération de votre compte.</p>
          <form className="login-form" onSubmit={handleResetRecoveredPassword}>
            <label><span>Nouveau mot de passe</span><input type="password" value={recoveryPassword} onChange={(event) => setRecoveryPassword(event.target.value)} required /></label>
            <label><span>Confirmation</span><input type="password" value={recoveryPasswordConfirm} onChange={(event) => setRecoveryPasswordConfirm(event.target.value)} required /></label>
            <button type="submit" disabled={recoveryPending}>{recoveryPending ? 'Mise à jour...' : 'Mettre à jour le mot de passe'}</button>
          </form>
          {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
        </section>
      </div>
    )
  }

  if (hasSupabaseEnv && !session && !bootLoading) {
    return (
      <div className="login-shell">
        <section className="login-panel">
          <p className="eyebrow">Accès sécurisé</p>
          <h1>Connexion à l'outil métier</h1>
          <p className="hero-copy">Les vues Supabase sont protégées par RLS. Connecte-toi avec un utilisateur actif pour lire les données.</p>
          <form className="login-form" onSubmit={handleSignIn}>
            <label><span>Email</span><input type="email" value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} required /></label>
            <label><span>Mot de passe</span><input type="password" value={authPassword} onChange={(event) => setAuthPassword(event.target.value)} required /></label>
            <button type="submit" disabled={authPending}>{authPending ? 'Connexion...' : 'Se connecter'}</button>
          </form>
          <div className="hero-actions">
            <button className="ghost-button" type="button" onClick={() => setForgotPasswordOpen((open) => !open)}>
              {forgotPasswordOpen ? 'Masquer la réinitialisation' : 'Mot de passe oublié ?'}
            </button>
          </div>
          {forgotPasswordOpen ? (
            <form className="login-form" onSubmit={handleForgotPassword}>
              <label><span>Email de connexion</span><input type="email" value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} required /></label>
              <button type="submit" disabled={forgotPasswordPending}>{forgotPasswordPending ? 'Envoi...' : 'Envoyer le lien'}</button>
            </form>
          ) : null}
          {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
        </section>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <header className="side-rail">
        <div className="brand-block">
          <p className="eyebrow">GTI Immobilier</p>
          <h1>{screenHeader.title}</h1>
          {screenHeader.copy ? <p>{screenHeader.copy}</p> : null}
        </div>
        <nav className="screen-nav">
          <button className={`nav-button ${screen === 'mandats' ? 'is-active' : ''}`} type="button" onClick={() => openScreen('mandats')}>Liste des annonces</button>
          <button className={`nav-button ${screen === 'registre' ? 'is-active' : ''}`} type="button" onClick={() => openScreen('registre')}>Registre des mandats</button>
          {isAdmin ? <button className={`nav-button ${screen === 'suivi' ? 'is-active' : ''}`} type="button" onClick={() => openScreen('suivi')}>Suivi des mandats</button> : null}
        </nav>
        <div className="header-user-stack">
          <div className="side-card user-card">
            <div className="user-card-top">
              <div className="user-avatar">{userInitials(profile?.display_name, session?.user.email ?? profile?.email ?? null)}</div>
              <div className="user-meta">
                <strong>{resolvedUserNegotiatorContext?.commercial_nom || profile?.display_name || 'Utilisateur'}</strong>
                <span className="session-label">{resolvedUserNegotiatorContext?.agence_nom || 'Agence non détectée'}</span>
              </div>
              <div className="user-card-actions">
                {isAdmin ? <button className="signout-button-inline" type="button" onClick={() => void openUserTool()}>Utilisateurs</button> : null}
                {session ? <button className="signout-button-inline" type="button" onClick={handleSignOut}>Se déconnecter</button> : null}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="content">
        <section className="hero">
          <div className="hero-stack">
            <div className="hero-top-row">
              <label className="search-box">
                <span>Recherche rapide</span>
                <input value={filters.query} onChange={(event) => updateFilter('query', event.target.value)} placeholder={screen === 'annonces' ? 'Titre, dossier, mandat, commercial, ville' : screen === 'registre' ? 'Mandat, dossier, bien, mandant, commercial, ville' : 'Dossier, mandat, commercial, ville'} />
              </label>
              <section className="result-indicator result-indicator-compact">
                <span>{screen === 'annonces' ? dossierCountLabel : screen === 'mandats' ? 'Annonces visibles' : screen === 'registre' ? 'Mandats enregistrés' : 'Demandes administratives'}</span>
                <strong>{new Intl.NumberFormat('fr-FR').format(screen === 'annonces' ? visibleDossiersCount : screen === 'mandats' || screen === 'registre' ? (mandatsTotal || mandats.length) : mandatStats.total)}</strong>
              </section>
              <div className="hero-actions">
                <button className="ghost-button" type="button" onClick={() => setFiltersOpen((open) => !open)}>{filtersOpen ? 'Masquer les filtres' : 'Filtres'}</button>
                <button className="ghost-button" type="button" onClick={resetFilters}>Réinitialiser</button>
              </div>
            </div>
            {screen === 'mandats' ? (
              <div className="header-kpi-stack">
                <div className="header-kpis">
                  {primaryCommercialMetrics.map((item) => (
                    <article
                      key={item.label}
                      className={`header-kpi-card tone-${item.tone} ${item.action ? 'is-clickable' : ''}`}
                      onClick={item.action ? () => openMandatDrilldown(item.action) : undefined}
                      role={item.action ? 'button' : undefined}
                      tabIndex={item.action ? 0 : undefined}
                      onKeyDown={item.action ? (event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault()
                          openMandatDrilldown(item.action)
                        }
                      } : undefined}
                    >
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </article>
                  ))}
                </div>
                <div className="header-kpi-secondary-toggle">
                  <button
                    className={`ghost-button kpi-toggle-button ${commercialMetricsExpanded ? 'is-open' : ''}`}
                    type="button"
                    onClick={() => setCommercialMetricsExpanded((value) => !value)}
                  >
                    <span>{commercialMetricsExpanded ? 'Masquer les stats secondaires' : 'Afficher les stats secondaires'}</span>
                    <strong>{secondaryCommercialMetrics.length}</strong>
                  </button>
                </div>
                {commercialMetricsExpanded ? (
                  <div className="header-kpis header-kpis-secondary">
                    {secondaryCommercialMetrics.map((item) => (
                      <article
                        key={item.label}
                        className={`header-kpi-card tone-${item.tone} ${item.action ? 'is-clickable' : ''}`}
                        onClick={item.action ? () => openMandatDrilldown(item.action) : undefined}
                        role={item.action ? 'button' : undefined}
                        tabIndex={item.action ? 0 : undefined}
                        onKeyDown={item.action ? (event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault()
                            openMandatDrilldown(item.action)
                          }
                        } : undefined}
                      >
                        <span>{item.label}</span>
                        <strong>{item.value}</strong>
                      </article>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : screen === 'registre' ? (
              <div className="header-kpis">
                {headerMetrics.map((item) => (
                  <article
                    key={item.label}
                    className={`header-kpi-card tone-${item.tone} ${item.action ? 'is-clickable' : ''}`}
                    onClick={item.action ? () => openRegisterDrilldown(item.action) : undefined}
                    role={item.action ? 'button' : undefined}
                    tabIndex={item.action ? 0 : undefined}
                    onKeyDown={item.action ? (event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        openRegisterDrilldown(item.action)
                      }
                    } : undefined}
                  >
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </article>
                ))}
              </div>
            ) : (
              <div className="header-kpis">
                {headerMetrics.map((item) => (
                  <article
                    key={item.label}
                    className={`header-kpi-card tone-${item.tone} ${item.action ? 'is-clickable' : ''}`}
                    onClick={item.action ? () => openMandatDrilldown(item.action) : undefined}
                    role={item.action ? 'button' : undefined}
                    tabIndex={item.action ? 0 : undefined}
                    onKeyDown={item.action ? (event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        openMandatDrilldown(item.action)
                      }
                    } : undefined}
                  >
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>

        {filtersOpen ? <div className="filters-overlay" onClick={() => setFiltersOpen(false)}>
          <section className="filters-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="filters-head">
              <div>
                <p className="eyebrow">{screen === 'annonces' ? 'Filtres annonces' : screen === 'mandats' ? 'Filtres mandats' : screen === 'registre' ? 'Filtres registre' : 'Filtres suivi administratif'}</p>
                <strong>{screen === 'annonces' ? 'Appliqués côté serveur' : screen === 'mandats' ? 'Mandats et diffusion' : screen === 'registre' ? 'Mandats avec numéro' : 'Demandes et parc mandat'}</strong>
              </div>
              <button className="ghost-button" type="button" onClick={() => setFiltersOpen(false)}>Fermer</button>
            </div>
            <div className="filter-grid">
            {screen === 'annonces' ? (
              <>
                <FilterSelect label="Negociateur" value={filters.commercial} onChange={(value) => updateFilter('commercial', value)} options={[{ value: withoutCommercialFilterValue, label: 'Sans' }, ...filterCatalog.commercials]} />
                <FilterSelect label="Agence" value={filters.agency} onChange={(value) => updateFilter('agency', value)} options={filterCatalog.agencies} />
                <FilterSelect
                  label="Archive"
                  value={filters.archive}
                  onChange={(value) => updateFilter('archive', value)}
                  options={[
                    { value: activeArchiveFilterValue, label: 'Actives' },
                    { value: archivedFilterValue, label: 'Archivees' },
                  ]}
                />
                <FilterSelect
                  label="Presence mandat"
                  value={filters.mandat}
                  onChange={(value) => updateFilter('mandat', value)}
                  options={[
                    { value: withMandatFilterValue, label: 'Avec mandat' },
                    { value: withoutMandatFilterValue, label: 'Sans mandat' },
                  ]}
                />
                <FilterSelect
                  label="Transactions"
                  value={filters.affaire}
                  onChange={(value) => updateFilter('affaire', value)}
                  options={[
                    { value: 'offre_achat', label: "Offre d'achat" },
                    { value: 'compromis', label: 'Compromis' },
                  ]}
                />
                {filters.affaire === 'offre_achat' ? (
                  <FilterSelect
                    label="Etat offre"
                    value={filters.offreStatus}
                    onChange={(value) => updateFilter('offreStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'refusee', label: 'Refusee' },
                    ]}
                  />
                ) : null}
                {filters.affaire === 'compromis' ? (
                  <FilterSelect
                    label="Etat compromis"
                    value={filters.compromisStatus}
                    onChange={(value) => updateFilter('compromisStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'annule', label: 'Annule' },
                    ]}
                  />
                ) : null}
                <FilterSelect
                  label="Mandat diffusable"
                  value={filters.diffusable}
                  onChange={(value) => updateFilter('diffusable', value)}
                  options={[
                    { value: 'diffusable', label: 'Oui' },
                    { value: 'non_diffusable', label: 'Non' },
                  ]}
                />
                <FilterSelect label="Passerelle" value={filters.passerelle} onChange={(value) => updateFilter('passerelle', value)} options={filterCatalog.passerelles} />
                <FilterSelect
                  label="Erreur passerelle"
                  value={filters.erreurDiffusion}
                  onChange={(value) => updateFilter('erreurDiffusion', value)}
                  options={[
                    { value: 'avec_erreur', label: 'Oui' },
                    { value: 'sans_erreur', label: 'Non' },
                  ]}
                />
                <FilterSelect label="Statut phase 1" value={filters.statut} onChange={(value) => updateFilter('statut', value)} options={filterCatalog.statuts} />
                <FilterSelect label="Validation" value={filters.validationDiffusion} onChange={(value) => updateFilter('validationDiffusion', value)} options={filterCatalog.validationDiffusions} />
                <FilterSelect label="Type de demande" value={filters.requestType} onChange={(value) => updateFilter('requestType', value)} options={requestTypeOptions} />
                <FilterSelect label="Priorite" value={filters.priority} onChange={(value) => updateFilter('priority', value)} options={filterCatalog.priorities} />
                <FilterSelect label="Work status" value={filters.workStatus} onChange={(value) => updateFilter('workStatus', value)} options={filterCatalog.workStatuses} />
                <FilterSelect label="Interne" value={filters.internalStatus} onChange={(value) => updateFilter('internalStatus', value)} options={filterCatalog.internalStatuses} />
              </>
            ) : screen === 'mandats' ? (
              <>
                <FilterSelect label="Negociateur" value={filters.commercial} onChange={(value) => updateFilter('commercial', value)} options={[{ value: withoutCommercialFilterValue, label: 'Sans' }, ...filterCatalog.commercials]} />
                <FilterSelect label="Agence" value={filters.agency} onChange={(value) => updateFilter('agency', value)} options={filterCatalog.agencies} />
                <FilterSelect label="Statut phase 1" value={filters.statut} onChange={(value) => updateFilter('statut', value)} options={filterCatalog.statuts} />
                <FilterSelect label="Validation" value={filters.validationDiffusion} onChange={(value) => updateFilter('validationDiffusion', value)} options={filterCatalog.validationDiffusions} />
                <FilterSelect label="Type de demande" value={filters.requestType} onChange={(value) => updateFilter('requestType', value)} options={requestTypeOptions} />
                <FilterSelect
                  label="Presence mandat"
                  value={filters.mandat}
                  onChange={(value) => updateFilter('mandat', value)}
                  options={[
                    { value: withMandatFilterValue, label: 'Avec mandat' },
                    { value: withoutMandatFilterValue, label: 'Sans mandat' },
                  ]}
                />
                <FilterSelect
                  label="Mandat diffusable"
                  value={filters.diffusable}
                  onChange={(value) => updateFilter('diffusable', value)}
                  options={[
                    { value: 'diffusable', label: 'Oui' },
                    { value: 'non_diffusable', label: 'Non' },
                  ]}
                />
                <FilterSelect label="Passerelle active" value={filters.passerelle} onChange={(value) => updateFilter('passerelle', value)} options={filterCatalog.passerelles} />
                <FilterSelect
                  label="Erreur passerelle"
                  value={filters.erreurDiffusion}
                  onChange={(value) => updateFilter('erreurDiffusion', value)}
                  options={[
                    { value: 'avec_erreur', label: 'Oui' },
                    { value: 'sans_erreur', label: 'Non' },
                  ]}
                />
                <FilterSelect
                  label="Transactions"
                  value={filters.affaire}
                  onChange={(value) => updateFilter('affaire', value)}
                  options={[
                    { value: 'offre_achat', label: "Offre d'achat" },
                    { value: 'compromis', label: 'Compromis' },
                  ]}
                />
                {filters.affaire === 'offre_achat' ? (
                  <FilterSelect
                    label="Etat offre"
                    value={filters.offreStatus}
                    onChange={(value) => updateFilter('offreStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'refusee', label: 'Refusee' },
                    ]}
                  />
                ) : null}
                {filters.affaire === 'compromis' ? (
                  <FilterSelect
                    label="Etat compromis"
                    value={filters.compromisStatus}
                    onChange={(value) => updateFilter('compromisStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'annule', label: 'Annule' },
                    ]}
                  />
                ) : null}
                <FilterSelect
                  label="Archive"
                  value={filters.archive}
                  onChange={(value) => updateFilter('archive', value)}
                  options={[
                    { value: activeArchiveFilterValue, label: 'Actifs' },
                    { value: archivedFilterValue, label: 'Archives' },
                  ]}
                />
              </>
            ) : screen === 'registre' ? (
              <>
                <label className="filter-field">
                  <span>N° de mandat</span>
                  <input
                    value={filters.mandatNumber}
                    onChange={(event) => updateFilter('mandatNumber', event.target.value)}
                    placeholder="Exemple : 18540"
                  />
                </label>
                <label className="filter-field">
                  <span>Nom mandant</span>
                  <input
                    value={filters.mandantName}
                    onChange={(event) => updateFilter('mandantName', event.target.value)}
                    placeholder="Exemple : Dupont"
                  />
                </label>
                <FilterSelect label="Negociateur" value={filters.commercial} onChange={(value) => updateFilter('commercial', value)} options={[{ value: withoutCommercialFilterValue, label: 'Sans' }, ...filterCatalog.commercials]} />
                <FilterSelect label="Agence" value={filters.agency} onChange={(value) => updateFilter('agency', value)} options={filterCatalog.agencies} />
                <FilterSelect label="Statut phase 1" value={filters.statut} onChange={(value) => updateFilter('statut', value)} options={filterCatalog.statuts} />
                <FilterSelect label="Validation" value={filters.validationDiffusion} onChange={(value) => updateFilter('validationDiffusion', value)} options={filterCatalog.validationDiffusions} />
                <FilterSelect
                  label="Mandat diffusable"
                  value={filters.diffusable}
                  onChange={(value) => updateFilter('diffusable', value)}
                  options={[
                    { value: 'diffusable', label: 'Oui' },
                    { value: 'non_diffusable', label: 'Non' },
                  ]}
                />
                <FilterSelect label="Passerelle active" value={filters.passerelle} onChange={(value) => updateFilter('passerelle', value)} options={filterCatalog.passerelles} />
                <FilterSelect
                  label="Erreur passerelle"
                  value={filters.erreurDiffusion}
                  onChange={(value) => updateFilter('erreurDiffusion', value)}
                  options={[
                    { value: 'avec_erreur', label: 'Oui' },
                    { value: 'sans_erreur', label: 'Non' },
                  ]}
                />
                <FilterSelect
                  label="Transactions"
                  value={filters.affaire}
                  onChange={(value) => updateFilter('affaire', value)}
                  options={[
                    { value: 'offre_achat', label: "Offre d'achat" },
                    { value: 'compromis', label: 'Compromis' },
                  ]}
                />
                {filters.affaire === 'offre_achat' ? (
                  <FilterSelect
                    label="Etat offre"
                    value={filters.offreStatus}
                    onChange={(value) => updateFilter('offreStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'refusee', label: 'Refusee' },
                    ]}
                  />
                ) : null}
                {filters.affaire === 'compromis' ? (
                  <FilterSelect
                    label="Etat compromis"
                    value={filters.compromisStatus}
                    onChange={(value) => updateFilter('compromisStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'annule', label: 'Annule' },
                    ]}
                  />
                ) : null}
                <FilterSelect
                  label="Archive"
                  value={filters.archive}
                  onChange={(value) => updateFilter('archive', value)}
                  options={[
                    { value: activeArchiveFilterValue, label: 'Actifs' },
                    { value: archivedFilterValue, label: 'Archives' },
                  ]}
                />
              </>
            ) : (
              <>
                <FilterSelect label="Negociateur" value={filters.commercial} onChange={(value) => updateFilter('commercial', value)} options={[{ value: withoutCommercialFilterValue, label: 'Sans' }, ...filterCatalog.commercials]} />
                <FilterSelect label="Agence" value={filters.agency} onChange={(value) => updateFilter('agency', value)} options={filterCatalog.agencies} />
                <FilterSelect
                  label="Presence mandat"
                  value={filters.mandat}
                  onChange={(value) => updateFilter('mandat', value)}
                  options={[
                    { value: withMandatFilterValue, label: 'Avec mandat' },
                    { value: withoutMandatFilterValue, label: 'Sans mandat' },
                  ]}
                />
                <FilterSelect
                  label="Mandat diffusable"
                  value={filters.diffusable}
                  onChange={(value) => updateFilter('diffusable', value)}
                  options={[
                    { value: 'diffusable', label: 'Oui' },
                    { value: 'non_diffusable', label: 'Non' },
                  ]}
                />
                <FilterSelect label="Passerelle active" value={filters.passerelle} onChange={(value) => updateFilter('passerelle', value)} options={filterCatalog.passerelles} />
                <FilterSelect
                  label="Erreur passerelle"
                  value={filters.erreurDiffusion}
                  onChange={(value) => updateFilter('erreurDiffusion', value)}
                  options={[
                    { value: 'avec_erreur', label: 'Oui' },
                    { value: 'sans_erreur', label: 'Non' },
                  ]}
                />
                <FilterSelect label="Statut phase 1" value={filters.statut} onChange={(value) => updateFilter('statut', value)} options={filterCatalog.statuts} />
                <FilterSelect label="Validation" value={filters.validationDiffusion} onChange={(value) => updateFilter('validationDiffusion', value)} options={filterCatalog.validationDiffusions} />
                <FilterSelect label="Type de demande" value={filters.requestType} onChange={(value) => updateFilter('requestType', value)} options={requestTypeOptions} />
                <FilterSelect
                  label="Transactions"
                  value={filters.affaire}
                  onChange={(value) => updateFilter('affaire', value)}
                  options={[
                    { value: 'offre_achat', label: "Offre d'achat" },
                    { value: 'compromis', label: 'Compromis' },
                  ]}
                />
                {filters.affaire === 'offre_achat' ? (
                  <FilterSelect
                    label="Etat offre"
                    value={filters.offreStatus}
                    onChange={(value) => updateFilter('offreStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'refusee', label: 'Refusee' },
                    ]}
                  />
                ) : null}
                {filters.affaire === 'compromis' ? (
                  <FilterSelect
                    label="Etat compromis"
                    value={filters.compromisStatus}
                    onChange={(value) => updateFilter('compromisStatus', value)}
                    options={[
                      { value: 'en_cours', label: 'En cours' },
                      { value: 'annule', label: 'Annule' },
                    ]}
                  />
                ) : null}
                <FilterSelect
                  label="Archive"
                  value={filters.archive}
                  onChange={(value) => updateFilter('archive', value)}
                  options={[
                    { value: activeArchiveFilterValue, label: 'Actifs' },
                    { value: archivedFilterValue, label: 'Archives' },
                  ]}
                />
              </>
            )}
          </div>
            {activeFilters.length > 0 ? (
              <div className="active-filters">
                {activeFilters.map(([label, value]) => <span key={`${label}-${value}`} className="active-filter-chip">{label}: {value}</span>)}
              </div>
            ) : null}
          </section>
        </div> : null}

        {bootLoading && dossiers.length === 0 && workItems.length === 0 ? <section className="info-banner">Chargement initial des donnees...</section> : null}
        {errorMessage ? <section className="error-banner">{errorMessage}</section> : null}

        {screen === 'annonces' && detailOpen ? (
          <AnnonceScreen selectedDossier={selectedDossier} detail={detail} address={address} images={images} texts={texts} notes={notes} contacts={contacts} mandats={mandatDetails} linkedWorkItems={linkedWorkItems} requestHistory={buildRequestHistory(selectedDossierRequest, selectedDossierRequestEvents)} requestMessages={selectedDossierRequestEvents
            .filter((event) => parseJson<{ message?: string | null }>(event.payload_json, {}).message)
            .slice()
            .sort((a, b) => new Date(b.event_at).getTime() - new Date(a.event_at).getTime())
            .map((event) => ({
              id: `detail-message-${event.id}`,
              author: event.actor_name || event.event_label,
              date: event.event_at,
              message: parseJson<{ message?: string | null }>(event.payload_json, {}).message || '',
            }))} requestHistoryDiffusion={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')} requestMessagesDiffusion={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')} requestHistoryPriceDrop={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')} requestMessagesPriceDrop={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')} detailLoading={detailLoading} onBack={closeDossierDetailPage} />
        ) : screen === 'annonces' ? (
          <StockScreen dossiers={dossiers} dossiersTotal={dossiersTotal} dossierPage={dossierPage} dossierTotalPages={dossierTotalPages} onPrevDossier={() => setDossierPage((page) => Math.max(1, page - 1))} onNextDossier={() => setDossierPage((page) => Math.min(dossierTotalPages, page + 1))} onGoToDossierPage={(page) => setDossierPage(Math.min(dossierTotalPages, Math.max(1, page)))} selectedDossier={selectedDossier} address={address} linkedWorkItems={linkedWorkItems} workItems={workItems} workItemsTotal={workItemsTotal} workItemPage={workItemPage} workItemTotalPages={workItemTotalPages} onPrevWorkItem={() => setWorkItemPage((page) => Math.max(1, page - 1))} onNextWorkItem={() => setWorkItemPage((page) => Math.min(workItemTotalPages, page + 1))} onGoToWorkItemPage={(page) => setWorkItemPage(Math.min(workItemTotalPages, Math.max(1, page)))} onSelectDossier={setSelectedDossierId} onOpenDetail={() => setDetailOpen(true)} onFocusDossier={(id) => setSelectedDossierId(id)} pageLoading={pageLoading} hasActiveFilters={activeFilters.length > 0} onResetFilters={resetFilters} />
        ) : screen === 'mandats' ? (
          <MandatsScreen
            mandats={mandats}
            mandatsTotal={mandatsTotal}
            mandatPage={mandatPage}
            mandatTotalPages={mandatTotalPages}
            onPrevMandat={() => setMandatPage((page) => Math.max(1, page - 1))}
            onNextMandat={() => setMandatPage((page) => Math.min(mandatTotalPages, page + 1))}
            onGoToMandatPage={(page) => setMandatPage(Math.min(mandatTotalPages, Math.max(1, page)))}
            selectedMandat={selectedMandat}
            mandatBroadcasts={mandatBroadcasts}
            requests={diffusionRequests}
            requestComment={requestComment}
            onRequestCommentChange={setRequestComment}
            onCreateRequest={handleCreateDiffusionRequest}
            onOpenRequestModal={openRequestModal}
            onOpenDiffusionModal={openDiffusionModal}
            onOpenDetailPage={openDossierDetailPage}
            requestPending={requestPending}
            onSelectMandat={setSelectedMandatId}
            loading={mandatLoading}
            selectedDossier={selectedDossier}
            detail={detail}
            address={address}
            images={images}
            linkedWorkItems={linkedWorkItems}
            detailLoading={detailLoading}
            eyebrow={mandatDrilldownLabel?.eyebrow ?? 'Annonces'}
            title={mandatDrilldownLabel?.title ?? 'Liste des annonces'}
          />
        ) : screen === 'registre' ? (
          <MandatRegisterScreen
            mandats={mandats}
            mandatsTotal={mandatsTotal}
            mandatPage={mandatPage}
            mandatTotalPages={mandatTotalPages}
            onPrevMandat={() => setMandatPage((page) => Math.max(1, page - 1))}
            onNextMandat={() => setMandatPage((page) => Math.min(mandatTotalPages, page + 1))}
            onGoToMandatPage={(page) => setMandatPage(Math.min(mandatTotalPages, Math.max(1, page)))}
            selectedMandat={selectedRegisterMandat}
            onSelectMandat={setSelectedRegisterRowId}
            onOpenDetailPage={openDossierDetailPage}
            loading={mandatLoading}
          />
        ) : (
          <SuiviMandatsScreenV2
            isAdmin={isAdmin}
            mandats={mandats}
            requests={diffusionRequests}
            stats={mandatStats}
            loading={requestLoading || mandatLoading}
            onUpdateRequest={handleUpdateDiffusionRequest}
            onOpenRequestModal={openRequestModal}
            onOpenDiffusionModal={openDiffusionModal}
            onOpenDetailPage={openDossierDetailPage}
            selectedDossier={selectedDossier}
            detail={detail}
            address={address}
            images={images}
            linkedWorkItems={linkedWorkItems}
            detailLoading={detailLoading}
            eyebrow={suiviDrilldownLabel?.eyebrow ?? 'Console Pauline'}
            title={suiviDrilldownLabel?.title ?? 'Parc mandat'}
            requestFilter={suiviRequestFilter}
          />
        )}
        {screen !== 'annonces' && detailOpen && selectedDossier ? (
          <div className="modal-overlay" onClick={closeDossierDetailPage}>
            <section className="modal-panel modal-panel-detail" onClick={(event) => event.stopPropagation()}>
              <DossierDetailLayout
                selectedDossier={selectedDossier}
                detail={detail}
                address={address}
                images={images}
                texts={texts}
                notes={notes}
                contacts={contacts}
                mandats={mandatDetails}
                linkedWorkItems={linkedWorkItems}
                requestHistory={buildRequestHistory(selectedDossierRequest, selectedDossierRequestEvents)}
                requestMessages={selectedDossierRequestEvents
                  .filter((event) => parseJson<{ message?: string | null }>(event.payload_json, {}).message)
                  .slice()
                  .sort((a, b) => new Date(b.event_at).getTime() - new Date(a.event_at).getTime())
                  .map((event) => ({
                    id: `detail-message-${event.id}`,
                    author: event.actor_name || event.event_label,
                    date: event.event_at,
                    message: parseJson<{ message?: string | null }>(event.payload_json, {}).message || '',
                  }))}
                requestHistoryDiffusion={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')}
                requestMessagesDiffusion={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')}
                requestHistoryPriceDrop={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')}
                requestMessagesPriceDrop={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')}
                detailLoading={detailLoading}
                eyebrow="Detail annonce"
                backLabel="Fermer"
                onBack={closeDossierDetailPage}
                allowMarkValidation={screen === 'suivi' && isAdmin}
                markValidationPending={detailValidationPending}
                validationDraft={detailValidationDraft}
                validationObserved={detailValidationObserved}
                validationSaved={detailValidationSaved}
                onSetValidation={handleSetSelectedDossierValidation}
                allowMarkDiffusable={screen === 'suivi' && isAdmin}
                markDiffusablePending={detailDiffusablePending}
                onSetDiffusable={handleSetSelectedDossierDiffusable}
                diffusableDraft={detailDiffusableDraft}
                diffusableObserved={detailDiffusableObserved}
                diffusableSaved={detailDiffusableSaved}
                onOpenImage={setDetailImageModalUrl}
              />
            </section>
          </div>
        ) : null}
        {detailImageModalUrl ? (
          <div className="modal-overlay" onClick={() => setDetailImageModalUrl(null)}>
            <section className="modal-panel modal-panel-image" onClick={(event) => event.stopPropagation()}>
              <div className="panel-head">
                <div>
                  <p className="eyebrow">Photo</p>
                  <h3>{selectedDossier?.titre_bien ?? 'Annonce'}</h3>
                </div>
                <button className="ghost-button button-subtle" type="button" onClick={() => setDetailImageModalUrl(null)}>Fermer</button>
              </div>
              <div className="detail-image-modal-body">
                <img src={detailImageModalUrl} alt={selectedDossier?.titre_bien ?? 'Annonce'} />
              </div>
            </section>
          </div>
        ) : null}
        {requestModalOpen && requestModalMandat ? (
          <div className="modal-overlay" onClick={closeRequestModal}>
            <section className="modal-panel request-modal-panel" onClick={(event) => event.stopPropagation()}>
              <div className="panel-head request-modal-head">
                <div className="request-modal-title">
                  <p className="eyebrow">Gestion des demandes</p>
                  <h3>{requestModalRole === 'pauline' ? 'Traitement Pauline' : requestModalEffectiveType === 'demande_baisse_prix' ? 'Demande de baisse de prix' : 'Demande de validation'}</h3>
                </div>
                <button className="ghost-button button-subtle request-modal-close" type="button" onClick={closeRequestModal}>Fermer</button>
              </div>
              <p className="modal-subline">{requestModalMandat.numero_dossier ?? '-'} - {requestModalMandat.numero_mandat ?? '-'} - {commercialDisplay(requestModalMandat)}</p>
              {requestModalEffectiveType !== 'demande_baisse_prix' ? (
                <section className="request-summary-card">
                  <div className="request-summary-hero">
                    <div className="request-summary-copy">
                      <p className="request-summary-kicker">Validation diffusion</p>
                      <h4 className="request-summary-heading">
                        {requestModalRole === 'pauline'
                          ? requestModalPaulineState?.label?.toLowerCase().includes('refusee')
                            ? 'Relecture avant retour'
                            : 'Decision de Pauline'
                          : requestModalState?.label?.includes('corriger')
                            ? 'Correction prete a renvoyer'
                            : requestModalState?.label?.includes('envoyee')
                              ? 'Demande deja transmise'
                              : 'Validation en preparation'}
                      </h4>
                      <p className="request-summary-note">
                        {requestModalRole === 'pauline'
                          ? requestModalPaulineState?.label?.toLowerCase().includes('refusee')
                            ? 'Relis le dernier retour puis decide si le dossier peut repartir ou non.'
                            : 'Tout le contexte utile est centralise ici pour valider rapidement le bien.'
                          : requestModalState?.label?.includes('corriger')
                            ? 'Le dossier a ete ajuste. Tu peux renvoyer une version propre a Pauline.'
                            : requestModalState?.label?.includes('envoyee')
                              ? 'La demande est partie. Il reste a suivre le retour de validation.'
                              : 'Une fois approuvee, la diffusion et les passerelles par defaut seront activees automatiquement.'}
                      </p>
                    </div>
                    <div className="request-summary-state">
                      <StatusPill value={requestModalRole === 'pauline' ? (requestModalPaulineState?.label ?? 'A traiter') : (requestModalState?.label ?? 'Demande de validation')} />
                    </div>
                  </div>
                  <div className="request-summary-metrics">
                    <article className="request-summary-metric">
                      <span className="request-summary-metric-label">Dossier</span>
                      <strong>{requestModalMandat.numero_dossier ?? '-'}</strong>
                      <small>Mandat {requestModalMandat.numero_mandat ?? '-'}</small>
                    </article>
                    <article className="request-summary-metric">
                      <span className="request-summary-metric-label">Apres accord</span>
                      <strong>Diffusion activee</strong>
                      <small>Passerelles par defaut appliquees</small>
                    </article>
                  </div>
                </section>
              ) : null}
              {requestModalRole !== 'pauline' ? (
                <div className="admin-form-grid request-form-grid">
                  <label className="filter-field">
                    <span>Type de demande</span>
                    <select
                      value={requestModalEffectiveType}
                      onChange={(event) => setRequestModalType(event.target.value as 'demande_diffusion' | 'demande_baisse_prix')}
                      disabled={Boolean(requestModalRequest && (requestModalRequest.request_status === 'pending' || requestModalRequest.request_status === 'in_progress' || requestModalRequest.request_status === 'waiting_commercial' || requestModalRequest.request_status === 'refused'))}
                    >
                      {requestTypeOptions.map((option) => (
                        <option key={option.value} value={option.value} disabled={option.value === 'demande_baisse_prix' && !requestModalEligibleForPriceDrop}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  {requestModalEffectiveType === 'demande_baisse_prix' ? (
                    <label className="filter-field">
                      <span>Nouveau prix demande</span>
                      <input value={requestModalPriceValue} onChange={(event) => setRequestModalPriceValue(event.target.value)} placeholder="Exemple : 129000" />
                    </label>
                  ) : null}
                </div>
              ) : null}
              {requestModalRequest ? (
                <section className="detail-card request-history-card">
                  <span className="detail-label">Historique et echanges</span>
                  <div className="timeline-list">
                    {buildRequestHistory(requestModalRequest, requestModalEvents).map((entry) => (
                      <article key={entry.id} className="timeline-card">
                        <strong>{entry.title}</strong>
                        <span>{formatDate(entry.date)}</span>
                        <p>{entry.body}</p>
                      </article>
                    ))}
                  </div>
                </section>
              ) : null}
              <label className="filter-field request-message-field">
                <span>{requestModalRole === 'pauline' ? 'Message Pauline' : requestModalState?.label?.includes('corriger') ? 'Message / correction pour Pauline' : requestModalEffectiveType === 'demande_baisse_prix' ? 'Contexte de la baisse de prix' : 'Contexte pour Pauline'}</span>
                <textarea
                  className="inline-textarea"
                  value={requestModalComment}
                  onChange={(event) => setRequestModalComment(event.target.value)}
                  placeholder={requestModalRole === 'pauline' ? (requestModalEffectiveType === 'demande_baisse_prix' ? "Exemple : avenant signe controle, baisse de prix validee." : 'Exemple : dossier controle, validation accordee.') : requestModalState?.label?.includes('corriger') ? (requestModalEffectiveType === 'demande_baisse_prix' ? "Exemple : avenant ajoute et corrige, merci de revoir la demande." : 'Exemple : pieces et informations corrigees, merci de revoir la demande.') : requestModalEffectiveType === 'demande_baisse_prix' ? "Exemple : avenant signe depose dans Hektor, merci de valider la baisse." : 'Exemple : le mandat est pret, merci de valider le bien.'}
                />
              </label>
              {requestModalRole === 'pauline' ? (
                <div className="admin-form-grid request-form-grid">
                  <label className="filter-field">
                    <span>Decision Pauline</span>
                    <select value={requestModalDecision} onChange={(event) => setRequestModalDecision(event.target.value)}>
                      <option value="in_progress">A traiter</option>
                      <option value="accepted">Accepter</option>
                      <option value="refused">Refuser</option>
                    </select>
                  </label>
                  <label className="filter-field">
                    <span>Motif de refus</span>
                    <select value={requestModalRefusalReason} onChange={(event) => setRequestModalRefusalReason(event.target.value)}>
                      <option value="">Choisir un motif</option>
                      {requestModalRefusalOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                  </label>
                </div>
              ) : null}
              <div className="modal-actions">
                <button className="ghost-button button-subtle" type="button" onClick={closeRequestModal}>Annuler</button>
                {requestModalRole === 'pauline' && requestModalRequest ? (
                  <button
                    className="ghost-button button-primary"
                    type="button"
                    onClick={() => handleUpdateDiffusionRequest({
                      requestId: requestModalRequest.id,
                      status: requestModalDecision,
                      response: requestModalComment,
                      refusalReason: requestModalRefusalReason,
                      followUpNeeded: requestModalDecision === 'refused',
                      followUpDays: requestModalDecision === 'refused' ? 2 : 0,
                      relaunchCount: requestModalRequest.relaunch_count ?? 0,
                    })}
                    disabled={requestLoading || (requestModalDecision === 'refused' && !requestModalRefusalReason)}
                  >
                    {requestLoading ? 'Enregistrement...' : requestModalDecision === 'accepted' ? (requestModalEffectiveType === 'demande_baisse_prix' ? 'Approuver la baisse' : 'Accepter') : requestModalDecision === 'refused' ? 'Refuser' : 'Enregistrer le traitement'}
                  </button>
                ) : (
                  <button
                    className="ghost-button button-primary"
                    type="button"
                    onClick={() => requestModalState?.label?.includes('corriger') && requestModalRequest
                      ? handleSubmitDiffusionCorrection({ requestId: requestModalRequest.id, comment: requestModalComment })
                      : handleCreateDiffusionRequest({ mandatId: requestModalMandat.app_dossier_id, comment: requestModalComment, requestType: requestModalEffectiveType, requestedPrice: requestModalPriceValue })}
                    disabled={requestPending || requestModalState?.label?.includes('envoyee') || (requestModalEffectiveType === 'demande_baisse_prix' && (!requestModalEligibleForPriceDrop || !requestModalPriceValue.trim()))}
                  >
                    {requestPending ? 'Envoi en cours...' : requestModalState?.label?.includes('corriger') ? 'Envoyer la correction' : requestModalState?.label?.includes('envoyee') ? 'Demande deja envoyee' : requestModalEffectiveType === 'demande_baisse_prix' ? 'Envoyer la demande de baisse' : 'Envoyer la demande de validation'}
                  </button>
                )}
              </div>
            </section>
          </div>
        ) : null}
        {diffusionModalOpen && diffusionModalMandat ? (
          <div className="modal-overlay" onClick={closeDiffusionModal}>
            <section className="modal-panel modal-panel-wide diffusion-modal-panel" onClick={(event) => event.stopPropagation()}>
              <div className="panel-head diffusion-modal-head">
                <div className="diffusion-modal-title">
                  <p className="eyebrow">Diffusion</p>
                  <h3>Console passerelles</h3>
                </div>
                <button className="ghost-button diffusion-close-button" type="button" onClick={closeDiffusionModal}>Fermer</button>
              </div>
              <p className="diffusion-subline">
                {diffusionModalMandat.numero_dossier ?? '-'} · {diffusionModalMandat.numero_mandat ?? '-'} · {commercialDisplay(diffusionModalMandat)}
              </p>
              <div className="diffusion-head-strip">
                <StatusPill value={diffusionModalMandat.statut_annonce} />
              </div>
              <section className="diffusion-console">
                <article className="detail-card diffusion-status-panel">
                  <span className="detail-label">Etat diffusion</span>
                  <strong className="diffusion-card-title">Vue de controle Hektor</strong>
                  <p className="diffusion-card-copy">Lis ici l'etat global du bien avant application, puis verifie le retour du lot juste apres.</p>
                  <div className="diffusion-state-grid diffusion-state-grid-compact">
                    <article className="diffusion-state-item diffusion-state-item-wide">
                      <span>Statut Hektor</span>
                      <strong>{diffusionModalMandat.statut_annonce ?? '-'}</strong>
                    </article>
                    <article className="diffusion-state-item">
                      <span>Diffusable</span>
                      <strong>{diffusableLabel(diffusionModalMandat.diffusable)}</strong>
                    </article>
                    <article className="diffusion-state-item">
                      <span>Passerelles actives</span>
                      <strong>{String(diffusionEnabledCount)}</strong>
                    </article>
                    <article className="diffusion-state-item diffusion-state-item-wide">
                      <span>Dernier enregistrement</span>
                      <strong>{diffusionTargetsSavedAt ? formatDate(diffusionTargetsSavedAt) : '-'}</strong>
                    </article>
                  </div>
                  {diffusionHasUnsavedChanges ? (
                    <div className="detail-sync-alert is-pending">Des modifications sont en attente d'enregistrement.</div>
                  ) : null}
                  {diffusionApplyResult ? (
                    <div className="diffusion-result-note">
                      <strong>{diffusionApplyResult.dry_run ? 'Simulation Hektor' : 'Application Hektor'}</strong>
                      <span>Ajouts : {diffusionApplyResult.to_add_count} · Retraits : {diffusionApplyResult.to_remove_count}</span>
                      <span>Succes : {diffusionApplyResult.applied.length} · Erreurs : {diffusionApplyResult.failed.length}</span>
                    </div>
                  ) : null}
                </article>
                <article className="detail-card diffusion-portals-panel">
                  <span className="detail-label">Passerelles</span>
                  <strong className="diffusion-card-title">Selection des portails</strong>
                  <span className="panel-note">Coche uniquement les portails a laisser actifs. La console enverra les ajouts et retraits correspondants sur Hektor.</span>
                  {diffusionTargetsLoading ? <p className="empty-state">Chargement des cibles en cours...</p> : null}
                  {diffusionPortalRows.length > 0 ? (
                    <div className="diffusion-portal-list">
                      {diffusionPortalRows.map((portal) => {
                        const targetEnabled = diffusionDraftTargets[portal.portalKey] ?? portal.observedEnabled
                        const isDirty = targetEnabled !== portal.observedEnabled
                        return (
                          <label key={portal.portalKey} className={`diffusion-portal-row ${isDirty ? 'is-dirty' : ''}`}>
                            <div className="diffusion-portal-meta">
                              <strong>{portal.portalKey}</strong>
                              <small>{portal.details[0] ?? '-'}</small>
                              {isDirty ? <div className="detail-sync-alert is-waiting">En attente de mise a jour Hektor... La modification a bien ete envoyee.</div> : null}
                            </div>
                            <div className="diffusion-portal-toggle">
                              <span>{targetEnabled ? 'Activee' : 'Inactive'}</span>
                              <input
                                type="checkbox"
                                checked={targetEnabled}
                                onChange={(event) => setDiffusionDraftTargets((current) => ({ ...current, [portal.portalKey]: event.target.checked }))}
                              />
                            </div>
                          </label>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="empty-state">
                      {isValidationApproved(diffusionModalMandat.validation_diffusion_state)
                        ? "Aucune passerelle n'est configuree pour ce mandat. Le mapping agence n'a pas ete trouve."
                        : "Aucune passerelle configuree pour ce mandat. L'app peut tenter Diffuse puis les portails meme si Hektor indique validation = non."}
                    </p>
                  )}
                </article>
                <article className="detail-card diffusion-feedback-panel">
                  <span className="detail-label">Retour d'application</span>
                  <strong className="diffusion-card-title">Execution du lot</strong>
                  {diffusionApplyResult ? (
                    <>
                      <strong>{diffusionApplyResult.dry_run ? 'Simulation executee' : 'Application executee'}</strong>
                      <span>{diffusionApplyResult.waiting_on_hektor ? (diffusionApplyResult.waiting_message ?? 'En attente de mise a jour Hektor.') : 'La console a tente diffusable puis applique les passerelles sur Hektor.'}</span>
                      <span>Ajouts vises : {diffusionApplyResult.to_add_count} - Retraits vises : {diffusionApplyResult.to_remove_count}</span>
                      <span>Actions reussies : {diffusionApplyResult.applied.length} - Actions en attente : {diffusionApplyResult.pending?.length ?? 0} - Actions en erreur : {diffusionApplyResult.failed.length}</span>
                    </>
                  ) : (
                    <span>Aucune execution Hektor sur ce lot depuis l'ouverture de la console.</span>
                  )}
                </article>
              </section>
              <div className="modal-actions">
                <button className="ghost-button button-subtle" type="button" onClick={closeDiffusionModal}>Fermer</button>
                <button
                  className="ghost-button button-accent"
                  type="button"
                  onClick={handleCommitDiffusionTargets}
                  disabled={diffusionApplyPending || diffusionTargetsSaving || diffusionTargetsLoading || !profile}
                >
                  {diffusionApplyPending || diffusionTargetsSaving ? 'Activation...' : 'Activer la diffusion et appliquer'}
                </button>
              </div>
            </section>
          </div>
        ) : null}
      </main>

      {userToolOpen && isAdmin ? (
        <div className="filters-overlay" onClick={() => setUserToolOpen(false)}>
          <section className="filters-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="filters-head">
              <div>
                <p className="eyebrow">Administration</p>
                <strong>Ajouter un utilisateur</strong>
              </div>
              <button className="ghost-button" type="button" onClick={() => setUserToolOpen(false)}>Fermer</button>
            </div>
            <div className="panel-grid">
              <section className="panel">
                <div className="panel-head"><div><p className="eyebrow">Creation</p><h3>Nouvel utilisateur</h3></div></div>
                <form className="filter-grid" onSubmit={handleCreateAppUser}>
                  <label className="filter-field">
                    <span>Prenom</span>
                    <input value={newUserFirstName} onChange={(event) => setNewUserFirstName(event.target.value)} required />
                  </label>
                  <label className="filter-field">
                    <span>Nom</span>
                    <input value={newUserLastName} onChange={(event) => setNewUserLastName(event.target.value)} required />
                  </label>
                  <label className="filter-field">
                    <span>Nom affiche</span>
                    <input value={newUserDisplayName} onChange={(event) => setNewUserDisplayName(event.target.value)} placeholder="Laisser vide pour Prenom Nom" />
                  </label>
                  <label className="filter-field">
                    <span>Email</span>
                    <input type="email" value={newUserEmail} onChange={(event) => setNewUserEmail(event.target.value)} required />
                  </label>
                  <label className="filter-field">
                    <span>Mot de passe temporaire</span>
                    <input type="text" value={newUserPassword} onChange={(event) => setNewUserPassword(event.target.value)} required />
                  </label>
                  <label className="filter-field">
                    <span>Role</span>
                    <select value={newUserRole} onChange={(event) => setNewUserRole(event.target.value as UserProfile['role'])}>
                      <option value="commercial">Negociateur</option>
                      <option value="manager">Manager</option>
                      <option value="admin">Administrateur</option>
                      <option value="lecture">Lecture</option>
                    </select>
                  </label>
                  <label className="checkbox-inline">
                    <input type="checkbox" checked={newUserIsActive} onChange={(event) => setNewUserIsActive(event.target.checked)} />
                    Utilisateur actif
                  </label>
                  <div className="hero-actions">
                    <button className="ghost-button" type="button" onClick={() => setUserToolOpen(false)}>Annuler</button>
                    <button type="submit" disabled={userToolLoading}>{userToolLoading ? 'Creation...' : 'Creer l utilisateur'}</button>
                  </div>
                </form>
              </section>
              <section className="panel">
                <div className="panel-head"><div><p className="eyebrow">Gestion</p><h3>Utilisateurs existants</h3></div></div>
                {userToolLoading ? <p className="loading-inline">Chargement...</p> : null}
                <div className="timeline-list">
                  {appUsers.map((user) => (
                    <article key={user.id} className="timeline-card">
                      <strong>{userFullName(user)}</strong>
                      <span>{user.email ?? '-'}</span>
                      <span>{profileRoleLabel(user.role)} · {user.is_active ? 'Actif' : 'Archive'}</span>
                      <div className="hero-actions">
                        <button className="ghost-button" type="button" onClick={() => startEditUser(user)}>Modifier</button>
                        <button className="ghost-button" type="button" onClick={() => void handleSendPasswordReset(user.email)}>Mot de passe perdu</button>
                      </div>
                    </article>
                  ))}
                  {appUsers.length === 0 && !userToolLoading ? <p className="empty-state">Aucun utilisateur charge.</p> : null}
                </div>
              </section>
              {editingUserId ? (
                <section className="panel">
                  <div className="panel-head"><div><p className="eyebrow">Edition</p><h3>Modifier l utilisateur</h3></div></div>
                  <form className="filter-grid" onSubmit={handleUpdateAppUser}>
                    <label className="filter-field">
                      <span>Prenom</span>
                      <input value={editUserFirstName} onChange={(event) => setEditUserFirstName(event.target.value)} required />
                    </label>
                    <label className="filter-field">
                      <span>Nom</span>
                      <input value={editUserLastName} onChange={(event) => setEditUserLastName(event.target.value)} required />
                    </label>
                    <label className="filter-field">
                      <span>Nom affiche</span>
                      <input value={editUserDisplayName} onChange={(event) => setEditUserDisplayName(event.target.value)} />
                    </label>
                    <label className="filter-field">
                      <span>Email</span>
                      <input type="email" value={editUserEmail} onChange={(event) => setEditUserEmail(event.target.value)} required />
                    </label>
                    <label className="filter-field">
                      <span>Role</span>
                      <select value={editUserRole} onChange={(event) => setEditUserRole(event.target.value as UserProfile['role'])}>
                        <option value="commercial">Negociateur</option>
                        <option value="manager">Manager</option>
                        <option value="admin">Administrateur</option>
                        <option value="lecture">Lecture</option>
                      </select>
                    </label>
                    <label className="checkbox-inline">
                      <input type="checkbox" checked={editUserIsActive} onChange={(event) => setEditUserIsActive(event.target.checked)} />
                      Utilisateur actif
                    </label>
                    <div className="hero-actions">
                      <button className="ghost-button" type="button" onClick={resetEditUser}>Annuler</button>
                      <button type="submit" disabled={userToolLoading}>{userToolLoading ? 'Enregistrement...' : 'Enregistrer'}</button>
                    </div>
                  </form>
                </section>
              ) : null}
            </div>
          </section>
        </div>
      ) : null}
    </div>
  )
}

function DashboardScreen({
  selectedDossier,
  linkedWorkItems,
  address,
  onOpenStock,
  onFocusDossier,
}: {
  selectedDossier: Dossier | null
  linkedWorkItems: WorkItem[]
  address: string
  onOpenStock: () => void
  onFocusDossier: (id: number) => void
}) {
  return (
    <section className="dashboard-grid">
      <section className="panel">
        <div className="panel-head">
          <div><p className="eyebrow">Pilotage</p><h3>Selection courante</h3></div>
          <button className="ghost-button" type="button" onClick={onOpenStock}>Aller au stock</button>
        </div>
        {selectedDossier ? (
          <div className="detail-stack">
            <article className="detail-card"><strong>{selectedDossier.titre_bien}</strong><p>{address || '-'}</p><p>{formatPrice(selectedDossier.prix)}</p></article>
            <article className="detail-card"><span className="detail-label">Lecture phase 1</span><div className="tag-row"><StatusPill value={selectedDossier.statut_annonce} /><StatusPill value={diffusableLabel(selectedDossier.diffusable)} /><StatusPill value={selectedDossier.portails_resume || 'Aucune passerelle active'} /><StatusPill value={erreurDiffusionLabel(selectedDossier.has_diffusion_error)} /></div></article>
            <article className="detail-card"><span className="detail-label">Suivi</span><strong>{selectedDossier.commentaire_resume || 'Aucun commentaire'}</strong><span>Relance : {formatDate(selectedDossier.date_relance_prevue)}</span><span>Dernier event : {selectedDossier.dernier_event_type ?? '-'}</span></article>
          </div>
        ) : <p className="hero-copy">Aucun dossier selectionne.</p>}
      </section>
      <section className="panel">
        <div className="panel-head"><div><p className="eyebrow">Demandes</p><h3>File a traiter</h3></div></div>
        <div className="stack-list compact-list">
          {linkedWorkItems.map((item) => (
            <article key={`${item.app_dossier_id}-${item.type_demande_label}-${item.date_entree_file ?? 'na'}`} className="task-card" onClick={() => onFocusDossier(item.app_dossier_id)}>
              <div className="task-head"><StatusPill value={item.priority} /><span>{item.type_demande_label ?? '-'}</span></div>
              <strong>{item.titre_bien}</strong>
              <p>{item.numero_dossier ?? '-'} - {commercialDisplay(item)}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  )
}

function StockScreen(props: {
  dossiers: Dossier[]
  dossiersTotal: number
  dossierPage: number
  dossierTotalPages: number
  onPrevDossier: () => void
  onNextDossier: () => void
  onGoToDossierPage: (page: number) => void
  selectedDossier: Dossier | null
  address: string
  linkedWorkItems: WorkItem[]
  workItems: WorkItem[]
  workItemsTotal: number
  workItemPage: number
  workItemTotalPages: number
  onPrevWorkItem: () => void
  onNextWorkItem: () => void
  onGoToWorkItemPage: (page: number) => void
  onSelectDossier: (id: number) => void
  onOpenDetail: () => void
  onFocusDossier: (id: number) => void
  pageLoading: boolean
  hasActiveFilters: boolean
  onResetFilters: () => void
}) {
  return (
    <section className="panel-grid">
      <section className="panel panel-wide">
        <div className="panel-head">
          <div><p className="eyebrow">Annonces</p><h3>Listing principal</h3></div>
          <div className="page-controls">
            {props.pageLoading ? <span className="loading-inline">Mise a jour...</span> : null}
            <span>{pageLabel(props.dossiersTotal, dossierPageSize, props.dossierPage)}</span>
            <span>Page {props.dossierPage} / {props.dossierTotalPages}</span>
            <button className="ghost-button" type="button" onClick={props.onPrevDossier} disabled={props.dossierPage === 1}>Prec</button>
            <button className="ghost-button" type="button" onClick={props.onNextDossier} disabled={props.dossierPage * dossierPageSize >= props.dossiersTotal}>Suiv</button>
            <label className="page-jump">
              <span>Aller</span>
              <input type="number" min={1} max={props.dossierTotalPages} value={props.dossierPage} onChange={(event) => props.onGoToDossierPage(Number(event.target.value || 1))} />
            </label>
          </div>
        </div>
        <p className="panel-note">La liste affiche 50 dossiers par page sur {new Intl.NumberFormat('fr-FR').format(props.dossiersTotal)} dossiers au total.</p>
        <div className="table-wrap">
          {props.dossiers.length > 0 ? (
            <table>
              <thead><tr><th>Dossier</th><th>Bien</th><th>Commercial</th><th>Statut</th><th>Diffusion</th><th>Prix</th><th>Hektor</th></tr></thead>
              <tbody>
                {props.dossiers.map((item) => (
                  <tr key={item.app_dossier_id} className={item.app_dossier_id === props.selectedDossier?.app_dossier_id ? 'is-selected' : ''} onClick={() => props.onSelectDossier(item.app_dossier_id)} onDoubleClick={props.onOpenDetail}>
                    <td><strong>{item.numero_dossier ?? '-'}</strong><span>{item.numero_mandat ?? '-'}</span></td>
                    <td><strong>{item.titre_bien}</strong><span>{item.ville ?? '-'}</span></td>
                    <td>{commercialDisplay(item)}</td>
                    <td><StatusPill value={item.statut_annonce} /><small>{item.archive === '1' ? 'Archivee' : 'Non archivee'}</small></td>
                    <td><small>{diffusableLabel(item.diffusable)}</small><small>{item.portails_resume || 'Aucune passerelle active'}</small><small>{erreurDiffusionLabel(item.has_diffusion_error)}</small></td>
                    <td>{formatPrice(item.prix)}</td>
                    <td><button className="ghost-button" type="button" onClick={(event) => { event.stopPropagation(); openHektorAnnonce(item.hektor_annonce_id) }}>Ouvrir</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-block">
              <strong>Aucun dossier pour cette combinaison de filtres.</strong>
              <p>{props.hasActiveFilters ? "Le filtre Commercial n'est pas vide, mais un autre filtre actif bloque probablement la liste." : "La page n'a retourne aucun dossier."}</p>
              {props.hasActiveFilters ? <button className="ghost-button" type="button" onClick={props.onResetFilters}>Reinitialiser les filtres</button> : null}
            </div>
          )}
        </div>
      </section>
      <div className="side-panels">
        <section className="panel detail-panel">
          <div className="panel-head"><div><p className="eyebrow">Fiche rapide</p><h3>{props.selectedDossier?.numero_dossier ?? 'Aucun dossier'}</h3></div><button className="ghost-button" type="button" onClick={props.onOpenDetail} disabled={!props.selectedDossier}>Annonce complete</button></div>
          {props.selectedDossier ? (
            <div className="detail-stack">
              <article className="detail-card"><strong>{props.selectedDossier.titre_bien}</strong><p>{props.address || '-'}</p><p>{formatPrice(props.selectedDossier.prix)}</p></article>
              <article className="detail-card"><span className="detail-label">Lecture phase 1</span><div className="tag-row"><StatusPill value={props.selectedDossier.statut_annonce} /><StatusPill value={diffusableLabel(props.selectedDossier.diffusable)} /><StatusPill value={props.selectedDossier.portails_resume || 'Aucune passerelle active'} /><StatusPill value={erreurDiffusionLabel(props.selectedDossier.has_diffusion_error)} /><StatusPill value={props.selectedDossier.archive === '1' ? 'Archivee' : 'Non archivee'} /></div></article>
              <article className="detail-card"><span className="detail-label">Situation dossier</span><strong>{props.selectedDossier.archive === '1' ? 'Annonce archivee' : 'Annonce active'}</strong><span>{props.selectedDossier.numero_mandat ? 'Mandat present' : 'Sans mandat'}</span><span>{props.selectedDossier.commentaire_resume || 'Aucun commentaire'}</span></article>
              <article className="detail-card"><span className="detail-label">Demandes liees</span>{props.linkedWorkItems.length > 0 ? <div className="detail-task-list">{props.linkedWorkItems.map((item) => <div key={`${item.app_dossier_id}-${item.type_demande_label}-${item.date_entree_file ?? 'na'}`} className="detail-task-item"><strong>{item.type_demande_label ?? '-'}</strong><span>{item.work_status ?? '-'} - {item.internal_status ?? '-'}</span><span>{item.validation_diffusion_state ?? '-'} - {item.etat_visibilite ?? '-'}</span></div>)}</div> : <p>Aucune demande visible sur la page courante.</p>}</article>
            </div>
          ) : <p className="hero-copy">Aucun dossier disponible.</p>}
        </section>
        <section className="panel">
          <div className="panel-head">
            <div><p className="eyebrow">File de travail</p><h3>Demandes mandat / diffusion</h3></div>
            <div className="page-controls">
              {props.pageLoading ? <span className="loading-inline">Mise a jour...</span> : null}
              <span>{pageLabel(props.workItemsTotal, workItemPageSize, props.workItemPage)}</span>
              <span>Page {props.workItemPage} / {props.workItemTotalPages}</span>
              <button className="ghost-button" type="button" onClick={props.onPrevWorkItem} disabled={props.workItemPage === 1}>Prec</button>
              <button className="ghost-button" type="button" onClick={props.onNextWorkItem} disabled={props.workItemPage * workItemPageSize >= props.workItemsTotal}>Suiv</button>
              <label className="page-jump">
                <span>Aller</span>
                <input type="number" min={1} max={props.workItemTotalPages} value={props.workItemPage} onChange={(event) => props.onGoToWorkItemPage(Number(event.target.value || 1))} />
              </label>
            </div>
          </div>
          <div className="stack-list">
            {props.workItems.map((item) => (
              <article key={`${item.app_dossier_id}-${item.type_demande_label}-${item.date_entree_file ?? 'na'}`} className={`task-card ${item.app_dossier_id === props.selectedDossier?.app_dossier_id ? 'is-linked' : ''}`} onClick={() => props.onFocusDossier(item.app_dossier_id)}>
                <div className="task-head"><StatusPill value={item.priority} /><span>{item.type_demande_label ?? '-'}</span></div>
                <strong>{item.titre_bien}</strong>
                <p>{item.numero_dossier ?? '-'} - {commercialDisplay(item)}</p>
                <p>{item.validation_diffusion_state ?? '-'} - {item.etat_visibilite ?? '-'}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </section>
  )
}

function MandatsScreen(props: {
  mandats: MandatRecord[]
  mandatsTotal: number
  mandatPage: number
  mandatTotalPages: number
  onPrevMandat: () => void
  onNextMandat: () => void
  onGoToMandatPage: (page: number) => void
  selectedMandat: MandatRecord | null
  mandatBroadcasts: MandatBroadcast[]
  requests: DiffusionRequest[]
  requestComment: string
  onRequestCommentChange: (value: string) => void
  onCreateRequest: () => void
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: 'demande_diffusion' | 'demande_baisse_prix') => void
  onOpenDiffusionModal: (id: number) => void
  onOpenDetailPage: (id: number) => void
  requestPending: boolean
  onSelectMandat: (id: number) => void
  loading: boolean
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  linkedWorkItems: WorkItem[]
  detailLoading: boolean
  eyebrow?: string
  title?: string
}) {
  return (
    <section className="panel-grid">
      <section className="panel panel-wide">
        <div className="panel-head">
          <div><p className="eyebrow">{props.eyebrow ?? 'Annonces'}</p><h3>{props.title ?? 'Liste des annonces'}</h3></div>
          <div className="page-controls">
            {props.loading ? <span className="loading-inline">Mise a jour...</span> : null}
            <span>{pageLabel(props.mandatsTotal, mandatPageSize, props.mandatPage)}</span>
            <span>Page {props.mandatPage} / {props.mandatTotalPages}</span>
            <button className="ghost-button" type="button" onClick={props.onPrevMandat} disabled={props.mandatPage === 1}>Prec</button>
            <button className="ghost-button" type="button" onClick={props.onNextMandat} disabled={props.mandatPage * mandatPageSize >= props.mandatsTotal}>Suiv</button>
            <label className="page-jump">
              <span>Aller</span>
              <input type="number" min={1} max={props.mandatTotalPages} value={props.mandatPage} onChange={(event) => props.onGoToMandatPage(Number(event.target.value || 1))} />
            </label>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Mandat</th><th>Bien</th><th>Negociateur</th><th>Statut</th><th className="portal-col">LBC</th><th className="portal-col">BI</th><th className="portal-col">GTI</th><th>Photo</th><th>Actions</th></tr></thead>
            <tbody>
              {props.mandats.map((item) => {
                const isSelected = item.app_dossier_id === props.selectedMandat?.app_dossier_id
                const activeRequest = latestDiffusionRequest(props.requests, item.app_dossier_id)
                const hasLeboncoin = hasPortalEnabled(item, ['leboncoin'])
                const hasBienici = hasPortalEnabled(item, ['bienici'])
                const hasSiteGti = isSiteGtiEnabled(item)
                return (
                  <Fragment key={item.app_dossier_id}>
                    <tr
                      className={isSelected ? 'is-selected' : ''}
                      onClick={() => {
                        props.onSelectMandat(item.app_dossier_id)
                        props.onOpenDetailPage(item.app_dossier_id)
                      }}
                    >
                      <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.ville ?? '-'}</span></td>
                      <td><strong>{item.titre_bien}</strong><span>{propertyTypeLabel(item.type_bien)}</span><span>{item.numero_dossier ?? '-'}</span></td>
                      <td><strong>{commercialDisplay(item)}</strong><span>{item.agence_nom ?? '-'}</span></td>
                      <td><StatusPill value={item.statut_annonce} /></td>
                      <td className="portal-cell"><PortalStatusMark enabled={hasLeboncoin} /></td>
                      <td className="portal-cell"><PortalStatusMark enabled={hasBienici} /></td>
                      <td className="portal-cell"><PortalStatusMark enabled={hasSiteGti} /></td>
                      <td><ListingThumbnail url={item.photo_url_listing} imagesPreviewJson={item.images_preview_json} title={item.titre_bien} /></td>
                      <td>
                        <div className="row-actions">
                          <MandatActionMenu mandat={item} role="nego" requests={props.requests} onOpenRequestModal={props.onOpenRequestModal} onOpenDiffusionModal={props.onOpenDiffusionModal} />
                        </div>
                      </td>
                    </tr>
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  )
}

function MandatRegisterScreen(props: {
  mandats: MandatRecord[]
  mandatsTotal: number
  mandatPage: number
  mandatTotalPages: number
  onPrevMandat: () => void
  onNextMandat: () => void
  onGoToMandatPage: (page: number) => void
  selectedMandat: MandatRecord | null
  onSelectMandat: (registerRowId: string) => void
  onOpenDetailPage: (id: number) => void
  loading: boolean
}) {
  const [expandedMandants, setExpandedMandants] = useState<Record<string, boolean>>({})
  const [detailOpen, setDetailOpen] = useState(false)
  const selectedDetail = props.selectedMandat
  const selectedDetailPayload = selectedDetail ? parseRegisterDetailPayload(selectedDetail) : {}
  const selectedHistory = selectedDetail ? parseRegisterHistory(selectedDetail) : []
  const selectedAvenants = selectedDetail ? parseRegisterAvenants(selectedDetail) : []
  const selectedImages = parseJson<Array<Record<string, unknown>>>(String(selectedDetailPayload.images_preview_json ?? selectedDetail?.images_preview_json ?? '[]'), [])
  const selectedImageUrl = selectedImages.find((item) => safeText(item.url))?.url as string | undefined

  return (
    <section className="panel-grid">
      <section className="panel panel-wide">
        <div className="panel-head">
          <div><p className="eyebrow">Registre</p><h3>Registre des mandats</h3></div>
          <div className="page-controls">
            {props.loading ? <span className="loading-inline">Mise a jour...</span> : null}
            <span>{pageLabel(props.mandatsTotal, mandatPageSize, props.mandatPage)}</span>
            <span>Page {props.mandatPage} / {props.mandatTotalPages}</span>
            <button className="ghost-button" type="button" onClick={props.onPrevMandat} disabled={props.mandatPage === 1}>Prec</button>
            <button className="ghost-button" type="button" onClick={props.onNextMandat} disabled={props.mandatPage * mandatPageSize >= props.mandatsTotal}>Suiv</button>
            <label className="page-jump">
              <span>Aller</span>
              <input type="number" min={1} max={props.mandatTotalPages} value={props.mandatPage} onChange={(event) => props.onGoToMandatPage(Number(event.target.value || 1))} />
            </label>
          </div>
        </div>
        <div className="table-wrap register-table-wrap">
          <table className="register-table">
            <thead>
              <tr>
                <th className="register-col-mandat">N° de mandat</th>
                <th className="register-col-status">Statut</th>
                <th className="register-col-flag">Valide</th>
                <th className="register-col-flag">Diffusable</th>
                <th className="register-col-date">Date de debut</th>
                <th className="register-col-date">Date de fin</th>
                <th className="register-col-amount">Montant</th>
                <th className="register-col-mandants">Mandant(s)</th>
                <th className="register-col-nature">Nature et situation</th>
              </tr>
            </thead>
            <tbody>
              {props.mandats.map((item) => {
                const rowKey = mandateRegisterRowKey(item)
                const isSelected = rowKey === (props.selectedMandat ? mandateRegisterRowKey(props.selectedMandat) : null)
                const mandantsLabel = mandateRegisterMandantsLabel(item)
                const canExpandMandants = mandantsLabel.length > 42
                const expandKey = rowKey
                const isMandantsExpanded = Boolean(expandedMandants[expandKey])
                return (
                  <tr
                    key={rowKey}
                    className={isSelected ? 'is-selected' : ''}
                    onClick={() => {
                      props.onSelectMandat(rowKey)
                      setDetailOpen(true)
                    }}
                  >
                    <td className="register-col-mandat">
                      <strong className="register-primary">{item.numero_mandat ?? '-'}</strong>
                      {mandateRegisterTypeInlineLabel(item) ? <span className="register-type-inline">{mandateRegisterTypeInlineLabel(item)}</span> : null}
                      <span className="register-secondary">{item.numero_dossier ?? '-'}</span>
                      <div className="tag-row register-tag-row">
                        <StatusPill value={mandateRegisterSourceLabel(item)} />
                        {(item.register_version_count ?? 1) > 1 ? <StatusPill value={`+${item.register_version_count} versions`} /> : null}
                        {(item.register_embedded_avenant_count ?? 0) > 0 ? <StatusPill value={`+${item.register_embedded_avenant_count} avenant${(item.register_embedded_avenant_count ?? 0) > 1 ? 's' : ''}`} /> : null}
                      </div>
                    </td>
                    <td className="register-col-status"><StatusPill value={item.statut_annonce} /></td>
                    <td className="register-col-flag"><span className={`register-bool ${isValidationApproved(item.validation_diffusion_state) ? 'is-yes' : 'is-no'}`}>{mandateRegisterValidationLabel(item.validation_diffusion_state)}</span></td>
                    <td className="register-col-flag"><span className={`register-bool ${isDiffusableValue(item.diffusable) ? 'is-yes' : 'is-no'}`}>{mandateRegisterDiffusableLabel(item.diffusable)}</span></td>
                    <td className="register-col-date"><strong className="register-date">{formatDate(item.mandat_date_debut)}</strong></td>
                    <td className="register-col-date"><strong className="register-date">{formatDate(item.mandat_date_fin)}</strong></td>
                    <td className="register-col-amount">
                      <strong className="register-amount">{formatPrice(item.mandat_montant ?? item.prix)}</strong>
                      {priceChangeSummaryLine(item) ? <span className="register-price-history">{priceChangeSummaryLine(item)}</span> : null}
                    </td>
                    <td className="register-col-mandants">
                      <strong className={`register-primary register-mandants-text ${canExpandMandants && !isMandantsExpanded ? 'is-clamped' : ''}`}>{mandantsLabel}</strong>
                      {canExpandMandants ? (
                        <button
                          className="register-more-button"
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation()
                            setExpandedMandants((current) => ({ ...current, [expandKey]: !current[expandKey] }))
                          }}
                        >
                          {isMandantsExpanded ? '−' : '+'}
                        </button>
                      ) : null}
                    </td>
                    <td className="register-col-nature"><span className="register-muted">{mandateRegisterNatureLabel(item)}</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
      {detailOpen && selectedDetail ? (
        <div className="modal-overlay" onClick={() => setDetailOpen(false)}>
          <section className="modal-panel modal-panel-detail mandate-register-modal" onClick={(event) => event.stopPropagation()}>
            <div className="panel-head">
              <div>
                <p className="eyebrow">{selectedDetail.register_source_kind === 'historique' ? 'Mandat historique' : 'Mandat'}</p>
                <h3>{selectedDetail.numero_mandat ?? '-'} · {selectedDetail.titre_bien}</h3>
              </div>
              <div className="row-actions">
                {Boolean(selectedDetail.register_detail_available) ? (
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => {
                      setDetailOpen(false)
                      props.onOpenDetailPage(Number(selectedDetail.app_dossier_id))
                    }}
                  >
                    Ouvrir fiche
                  </button>
                ) : null}
                <button className="ghost-button" type="button" onClick={() => openHektorAnnonce(selectedDetail.hektor_annonce_id)}>Hektor</button>
                <button className="ghost-button button-subtle" type="button" onClick={() => setDetailOpen(false)}>Fermer</button>
              </div>
            </div>
            <div className="detail-stack detail-stack-rich">
              <article className="detail-card detail-card-hero">
                <div className="detail-card-hero-media">
                  {selectedImageUrl ? <img src={selectedImageUrl} alt={selectedDetail.titre_bien} loading="lazy" /> : <div className="detail-card-hero-placeholder">Mandat</div>}
                </div>
                <div className="detail-card-hero-body">
                  <strong>{selectedDetail.titre_bien}</strong>
                  <p>{String(selectedDetailPayload.adresse_detail ?? selectedDetail.adresse_detail ?? selectedDetail.adresse_privee_listing ?? selectedDetail.ville ?? '-')}</p>
                  <div className="tag-row">
                    <StatusPill value={selectedDetail.statut_annonce} />
                    <StatusPill value={mandateRegisterSourceLabel(selectedDetail)} />
                    {(selectedDetail.register_version_count ?? 1) > 1 ? <StatusPill value={`${selectedDetail.register_version_count} versions`} /> : null}
                    {(selectedDetail.register_embedded_avenant_count ?? 0) > 0 ? <StatusPill value={`${selectedDetail.register_embedded_avenant_count} avenant${(selectedDetail.register_embedded_avenant_count ?? 0) > 1 ? 's' : ''}`} /> : null}
                  </div>
                </div>
              </article>
              <article className="detail-card">
                <span className="detail-label">Mandat courant</span>
                <div className="info-grid">
                  <InfoCard label="Numero" value={selectedDetail.numero_mandat} />
                  <InfoCard label="Type" value={selectedDetail.mandat_type ?? selectedDetail.mandat_type_source ?? '-'} />
                  <InfoCard label="Debut" value={formatDate(selectedDetail.mandat_date_debut)} />
                  <InfoCard label="Fin" value={formatDate(selectedDetail.mandat_date_fin)} />
                  <InfoCard label="Montant" value={formatPrice(selectedDetail.mandat_montant ?? selectedDetail.prix)} />
                  <InfoCard label="Validation" value={selectedDetail.validation_diffusion_state ?? '-'} />
                  <InfoCard label="Diffusable" value={mandateRegisterDiffusableLabel(selectedDetail.diffusable)} />
                  <InfoCard label="Commercial" value={selectedDetail.commercial_nom ?? '-'} />
                  <InfoCard label="Agence" value={selectedDetail.agence_nom ?? '-'} />
                </div>
                <div className="detail-rich-copy">
                  <strong>Mandant(s)</strong>
                  <p>{selectedDetail.mandants_texte ?? '-'}</p>
                  {selectedDetail.mandat_note ? (
                    <>
                      <strong>Note mandat</strong>
                      <p>{selectedDetail.mandat_note}</p>
                    </>
                  ) : null}
                </div>
              </article>
              <PriceChangeHistoryCard
                source={selectedDetailPayload.price_change_events_json ? selectedDetailPayload : selectedDetail}
                title="Historique des prix"
                emptyLabel="Aucun changement de prix historisé pour ce mandat."
              />
              <article className="detail-card">
                <span className="detail-label">Historique des versions</span>
                {selectedHistory.length > 0 ? (
                  <div className="timeline-list">
                    {selectedHistory.map((entry, index) => (
                      <article key={String(entry.history_id ?? index)} className="timeline-card">
                        <strong>{String(entry.label ?? `Version ${index + 1}`)}</strong>
                        <span>{String(entry.type ?? entry.type_source ?? '-')} · {formatDate(String(entry.date_debut ?? ''))} → {formatDate(String(entry.date_fin ?? ''))}</span>
                        <p>{formatPrice(String(entry.montant ?? ''))} · {String(entry.mandants_texte ?? selectedDetail.mandants_texte ?? '-')}</p>
                        {safeText(entry.note) ? <small>{String(entry.note)}</small> : null}
                      </article>
                    ))}
                  </div>
                ) : <p>Aucun historique de version disponible.</p>}
              </article>
              <article className="detail-card">
                <span className="detail-label">Avenants Hektor</span>
                {selectedAvenants.length > 0 ? (
                  <div className="timeline-list">
                    {selectedAvenants.map((entry, index) => (
                      <article key={String(entry.avenant_id ?? index)} className="timeline-card">
                        <strong>{String(entry.numero ?? 'Avenant')}</strong>
                        <span>{formatDate(String(entry.date ?? ''))}</span>
                        <p>{String(entry.detail ?? 'Sans detail')}</p>
                      </article>
                    ))}
                  </div>
                ) : <p>Aucun avenant explicite dans le brut.</p>}
              </article>
            </div>
          </section>
        </div>
      ) : null}
    </section>
  )
}

function SuiviMandatsScreen(props: {
  isAdmin: boolean
  mandats: MandatRecord[]
  requests: DiffusionRequest[]
  stats: MandatStats
  loading: boolean
  onUpdateRequest: (input: { requestId: string; status: string; response: string; refusalReason: string; followUpNeeded: boolean; followUpDays: number; relaunchCount: number }) => void
}) {
  const [comments, setComments] = useState<Record<string, string>>({})
  if (!props.isAdmin) {
    return <section className="panel"><p className="empty-state">Cette vue est reservee aux administrateurs.</p></section>
  }
  const mandatIds = new Set(props.mandats.map((item) => item.app_dossier_id))
  const visibleRequests = props.requests.filter((item) => mandatIds.has(item.app_dossier_id))
  const pending = visibleRequests.filter((item) => item.request_status === 'pending').length
  const inProgress = visibleRequests.filter((item) => item.request_status === 'in_progress').length
  const correctionRequests = visibleRequests.filter((item) => item.request_status === 'waiting_commercial' || item.request_status === 'refused')
  const pendingRequests = visibleRequests.filter((item) => item.request_status === 'pending')
  const inProgressRequests = visibleRequests.filter((item) => item.request_status === 'in_progress')
  const withErrors = props.stats.withErrors
  const attentionMandats = props.mandats
    .filter((item) =>
      ((item.diffusable ?? '0') === '1' && !item.nb_portails_actifs) ||
      ((item.diffusable ?? '0') !== '1' && Boolean(item.nb_portails_actifs)) ||
      Boolean(item.has_diffusion_error) ||
      !item.numero_mandat,
    )
    .slice(0, 50)
  const attentionHighlights = attentionMandats.slice(0, 12)
  const portfolioRows = props.mandats.slice(0, 100)

  return (
    <section className="panel-grid suivi-pauline-view">
      <section className="panel suivi-command-panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Vue Pauline</p>
            <h3>Poste de pilotage des mandats</h3>
          </div>
          {props.loading ? <span className="loading-inline">Mise a jour...</span> : null}
        </div>
        <div className="suivi-command-grid">
          <article className="suivi-command-card tone-overview">
            <span className="suivi-command-kicker">Parc</span>
            <strong>{props.stats.total}</strong>
            <p>Annonces actuellement suivies dans le portefeuille administratif.</p>
          </article>
          <article className="suivi-command-card tone-action">
            <span className="suivi-command-kicker">A traiter</span>
            <strong>{pending}</strong>
            <p>Demandes nouvelles en attente d'une action Pauline.</p>
          </article>
          <article className="suivi-command-card tone-progress">
            <span className="suivi-command-kicker">En cours</span>
            <strong>{inProgress}</strong>
            <p>Dossiers déjà pris en main avec suivi de traitement.</p>
          </article>
          <article className="suivi-command-card tone-warning">
            <span className="suivi-command-kicker">Corrections</span>
            <strong>{correctionRequests.length}</strong>
            <p>Retours négociateur ou demandes refusées à reprendre.</p>
          </article>
          <article className="suivi-command-card tone-danger">
            <span className="suivi-command-kicker">Anomalies</span>
            <strong>{attentionMandats.length}</strong>
            <p>Mandats sans diffusion, sans numéro ou avec incohérence de passerelle.</p>
          </article>
          <article className="suivi-command-card tone-success">
            <span className="suivi-command-kicker">Diffusés</span>
            <strong>{props.stats.mandatDiffuse}</strong>
            <p>Mandats actuellement visibles et conformes côté diffusion.</p>
          </article>
        </div>
      </section>

      <section className="suivi-block-grid">
        <section className="panel suivi-block suivi-block-primary">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Actions Pauline</p>
              <h3>Demandes à traiter maintenant</h3>
            </div>
          </div>
          <div className="suivi-lanes">
            {[
              { title: 'Nouvelles demandes', tone: 'action', rows: pendingRequests },
              { title: 'Demandes en cours', tone: 'progress', rows: inProgressRequests },
              { title: 'Corrections en attente', tone: 'warning', rows: correctionRequests },
            ].map((group) => (
              <section key={group.title} className={`suivi-lane tone-${group.tone}`}>
                <div className="suivi-lane-head">
                  <strong>{group.title}</strong>
                  <span>{group.rows.length}</span>
                </div>
                <div className="timeline-list suivi-request-list">
                  {group.rows.length > 0 ? group.rows.map((item) => (
                    <article key={item.id} className={`timeline-card suivi-request-card tone-${group.tone}`}>
                      <div className="suivi-request-head">
                        <div>
                          <strong>{item.numero_mandat ?? item.numero_dossier ?? item.titre_bien}</strong>
                          <span>{item.titre_bien}</span>
                        </div>
                        <StatusPill value={requestTypeLabel(item.request_type)} />
                      </div>
                      <div className="suivi-request-meta">
                        <span>{item.requested_by_name ?? item.requested_by_label ?? '-'}</span>
                        <span>{formatDate(item.requested_at)}</span>
                        <span>{requestStatusLabel(item.request_status)}</span>
                      </div>
                      <p>{item.request_reason || item.request_comment || 'Sans commentaire'}</p>
                      <div className="admin-action-row suivi-admin-action-row">
                        <select value={item.request_status} onChange={(event) => props.onUpdateRequest({ requestId: item.id, status: event.target.value, response: comments[item.id] ?? item.admin_response ?? item.processing_comment ?? '', refusalReason: item.refusal_reason ?? '', followUpNeeded: Boolean(item.follow_up_needed), followUpDays: 0, relaunchCount: item.relaunch_count ?? 0 })}>
                          {requestStatusOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                        </select>
                        <input value={comments[item.id] ?? item.processing_comment ?? ''} onChange={(event) => setComments((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Commentaire administratif ou retour au commercial" />
                        <button className="ghost-button" type="button" onClick={() => props.onUpdateRequest({ requestId: item.id, status: item.request_status, response: comments[item.id] ?? item.admin_response ?? item.processing_comment ?? '', refusalReason: item.refusal_reason ?? '', followUpNeeded: Boolean(item.follow_up_needed), followUpDays: 0, relaunchCount: item.relaunch_count ?? 0 })}>Valider</button>
                      </div>
                    </article>
                  )) : <p className="empty-state">Aucune demande dans ce bloc.</p>}
                </div>
              </section>
            ))}
          </div>
        </section>

        <section className="panel suivi-block suivi-block-alerts">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Surveillance</p>
              <h3>Anomalies diffusion et mandat</h3>
            </div>
          </div>
          <div className="suivi-alert-grid">
            {attentionHighlights.length > 0 ? attentionHighlights.map((item) => {
              const anomalies = [
                !item.numero_mandat ? 'Sans mandat' : null,
                (item.diffusable ?? '0') === '1' && !item.nb_portails_actifs ? 'Diffusable non visible' : null,
                (item.diffusable ?? '0') !== '1' && Boolean(item.nb_portails_actifs) ? 'Annonce non diffusable mais active sur passerelle' : null,
                Boolean(item.has_diffusion_error) ? 'Erreur passerelle' : null,
              ].filter(Boolean)
              return (
                <article key={item.app_dossier_id} className="suivi-alert-card">
                  <div className="suivi-alert-head">
                    <div>
                      <strong>{item.numero_mandat ?? item.numero_dossier ?? '-'}</strong>
                      <span>{item.titre_bien}</span>
                    </div>
                    <StatusPill value={item.statut_annonce} />
                  </div>
                  <div className="suivi-alert-meta">
                    <span>{commercialDisplay(item)}</span>
                    <span>{diffusableLabel(item.diffusable)}</span>
                  </div>
                  <div className="suivi-alert-tags">
                    {anomalies.map((label) => <span key={label} className="suivi-alert-tag">{label}</span>)}
                  </div>
                  <div className="suivi-alert-footer">
                    <span>{item.portails_resume || 'Aucune passerelle active'}</span>
                    <button className="ghost-button" type="button" onClick={() => openHektorAnnonce(item.hektor_annonce_id)}>Hektor</button>
                  </div>
                </article>
              )
            }) : <p className="empty-state">Aucune anomalie sur la sélection courante.</p>}
          </div>
        </section>
      </section>

      <section className="panel suivi-block suivi-block-portfolio">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Portefeuille administratif</p>
            <h3>Vue portefeuille</h3>
          </div>
          <div className="suivi-portfolio-kpis">
            <span>{props.stats.mandatNonDiffuse} non diffusés</span>
            <span>{withErrors} avec erreur</span>
          </div>
        </div>
        <div className="table-wrap suivi-portfolio-wrap">
          <table className="suivi-portfolio-table">
            <thead><tr><th>Dossier</th><th>Mandat</th><th>Negociateur</th><th>Statut</th><th>Visibilite</th><th>Affaires</th><th>Hektor</th></tr></thead>
            <tbody>
              {portfolioRows.map((item) => (
                <tr key={item.app_dossier_id}>
                  <td><strong>{item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                  <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.agence_nom ?? '-'}</span></td>
                  <td>{commercialDisplay(item)}</td>
                  <td><small>{item.statut_annonce ?? '-'}</small><small>{item.archive === '1' ? 'Archive' : 'Actif'}</small></td>
                  <td><small>{diffusableLabel(item.diffusable)}</small><small>{item.portails_resume || 'Aucune passerelle active'}</small><small>{erreurDiffusionLabel(item.has_diffusion_error)}</small></td>
                  <td><small>{item.offre_id ? 'Offre' : '-'}</small><small>{item.compromis_id ? 'Compromis' : '-'}</small><small>{item.vente_id ? 'Vente' : '-'}</small></td>
                  <td><button className="ghost-button" type="button" onClick={() => openHektorAnnonce(item.hektor_annonce_id)}>Ouvrir</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  )
}

function SuiviMandatsScreenV2Legacy(props: {
  isAdmin: boolean
  mandats: MandatRecord[]
  requests: DiffusionRequest[]
  stats: MandatStats
  loading: boolean
  onUpdateRequest: (input: { requestId: string; status: string; response: string; refusalReason: string; followUpNeeded: boolean; followUpDays: number; relaunchCount: number }) => void
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: 'demande_diffusion' | 'demande_baisse_prix') => void
  onOpenDiffusionModal: (id: number) => void
}) {
  const [comments, setComments] = useState<Record<string, string>>({})
  const [refusalReasons, setRefusalReasons] = useState<Record<string, string>>({})
  const [followUpDays, setFollowUpDays] = useState<Record<string, string>>({})
  const [followUpEnabled, setFollowUpEnabled] = useState<Record<string, boolean>>({})
  const [view, setView] = useState<'requests' | 'anomalies' | 'portfolio'>('requests')
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null)
  const [selectedMandatId, setSelectedMandatId] = useState<number | null>(null)

  if (!props.isAdmin) {
    return <section className="panel"><p className="empty-state">Cette vue est reservee aux administrateurs.</p></section>
  }

  const mandatIds = new Set(props.mandats.map((item) => item.app_dossier_id))
  const visibleRequests = props.requests.filter((item) => mandatIds.has(item.app_dossier_id))
  const pending = visibleRequests.filter((item) => item.request_status === 'pending').length
  const inProgress = visibleRequests.filter((item) => item.request_status === 'in_progress').length
  const attentionMandats = props.mandats
    .filter((item) =>
      ((item.diffusable ?? '0') === '1' && !item.nb_portails_actifs) ||
      ((item.diffusable ?? '0') !== '1' && Boolean(item.nb_portails_actifs)) ||
      Boolean(item.has_diffusion_error) ||
      !item.numero_mandat,
    )
    .slice(0, 50)
  const portfolioRows = props.mandats.slice(0, 100)
  const selectedRequest = visibleRequests.find((item) => item.id === selectedRequestId) ?? visibleRequests[0] ?? null
  const selectedAnomalyMandat = attentionMandats.find((item) => item.app_dossier_id === selectedMandatId) ?? attentionMandats[0] ?? null
  const selectedPortfolioMandat = portfolioRows.find((item) => item.app_dossier_id === selectedMandatId) ?? portfolioRows[0] ?? null
  const activeMandat =
    view === 'requests'
      ? props.mandats.find((item) => item.app_dossier_id === selectedRequest?.app_dossier_id) ?? null
      : view === 'anomalies'
        ? selectedAnomalyMandat
        : selectedPortfolioMandat
  const selectedFollowUpEnabled = selectedRequest ? (followUpEnabled[selectedRequest.id] ?? Boolean(selectedRequest.follow_up_needed)) : false
  const selectedFollowUpDays = selectedRequest ? (followUpDays[selectedRequest.id] ?? '') : ''
  const selectedRefusalReason = selectedRequest ? (refusalReasons[selectedRequest.id] ?? selectedRequest.refusal_reason ?? '') : ''

  return (
    <section className="panel-grid">
      <section className="suivi-layout">
        <section className="panel panel-wide">
          <div className="panel-head">
            <div><p className="eyebrow">Console Pauline</p><h3>Liste de travail</h3></div>
            <div className="segmented-control">
              <button className={`segment-button ${view === 'requests' ? 'is-active' : ''}`} type="button" onClick={() => setView('requests')}>Demandes</button>
              <button className={`segment-button ${view === 'anomalies' ? 'is-active' : ''}`} type="button" onClick={() => setView('anomalies')}>Anomalies</button>
              <button className={`segment-button ${view === 'portfolio' ? 'is-active' : ''}`} type="button" onClick={() => setView('portfolio')}>Parc mandat</button>
            </div>
          </div>
          <div className="table-wrap">
            {view === 'requests' ? (
              <table>
                <thead><tr><th>Demande</th><th>Negociateur</th><th>Bien</th><th>Statut</th><th>Commentaire</th><th>Hektor</th></tr></thead>
                <tbody>
                  {visibleRequests.map((item) => {
                    return (
                      <tr key={item.id} className={item.id === selectedRequest?.id ? 'is-selected' : ''} onClick={() => { setSelectedRequestId(item.id); setSelectedMandatId(item.app_dossier_id) }}>
                        <td><strong>{requestTypeLabel(item.request_type)}</strong><span>{item.numero_mandat ?? item.numero_dossier ?? '-'}</span><span>{formatDate(item.requested_at)}</span></td>
                        <td>{item.requested_by_name ?? item.requested_by_label ?? item.commercial_nom ?? '-'}</td>
                        <td><strong>{item.titre_bien}</strong><span>{item.numero_dossier ?? '-'}</span></td>
                        <td><small>{requestStatusLabel(item.request_status)}</small><small>{item.processed_by_name ?? item.processed_by_label ?? '-'}</small></td>
                        <td><small>{item.request_reason || item.request_comment || 'Sans motif'}</small></td>
                        <td><button className="ghost-button" type="button" onClick={(event) => { event.stopPropagation(); openHektorAnnonce(item.hektor_annonce_id) }}>Ouvrir</button></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            ) : view === 'anomalies' ? (
              <table>
                <thead><tr><th>Dossier</th><th>Mandat</th><th>Negociateur</th><th>Diffusion</th><th>Anomalie</th><th>Actions</th></tr></thead>
                <tbody>
                  {attentionMandats.map((item) => (
                    <tr key={item.app_dossier_id} className={item.app_dossier_id === selectedAnomalyMandat?.app_dossier_id ? 'is-selected' : ''} onClick={() => setSelectedMandatId(item.app_dossier_id)}>
                      <td><strong>{item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                      <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.statut_annonce ?? '-'}</span></td>
                      <td>{commercialDisplay(item)}</td>
                      <td><small>{diffusableLabel(item.diffusable)}</small><small>{item.portails_resume || 'Aucune passerelle active'}</small></td>
                      <td><small>{!item.numero_mandat ? 'Sans mandat' : '-'}</small><small>{(item.diffusable ?? '0') === '1' && !item.nb_portails_actifs ? 'Diffusable non visible' : '-'}</small><small>{(item.diffusable ?? '0') !== '1' && Boolean(item.nb_portails_actifs) ? 'Annonce non diffusable mais active sur passerelle' : '-'}</small><small>{Boolean(item.has_diffusion_error) ? 'Erreur passerelle' : '-'}</small></td>
                      <td>
                        <div className="row-actions">
                          <MandatActionMenu mandat={item} role="nego" requests={visibleRequests} onOpenRequestModal={props.onOpenRequestModal} onOpenDiffusionModal={props.onOpenDiffusionModal} />
                          <button className="ghost-button" type="button" onClick={(event) => { event.stopPropagation(); openHektorAnnonce(item.hektor_annonce_id) }}>Ouvrir</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <table>
                <thead><tr><th>Dossier</th><th>Mandat</th><th>Negociateur</th><th>Statut</th><th>Visibilite</th><th>Affaires</th><th>Actions</th></tr></thead>
                <tbody>
                  {portfolioRows.map((item) => (
                    <tr key={item.app_dossier_id} className={item.app_dossier_id === selectedPortfolioMandat?.app_dossier_id ? 'is-selected' : ''} onClick={() => setSelectedMandatId(item.app_dossier_id)}>
                      <td><strong>{item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                      <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.agence_nom ?? '-'}</span></td>
                      <td>{commercialDisplay(item)}</td>
                      <td><small>{item.statut_annonce ?? '-'}</small><small>{item.archive === '1' ? 'Archive' : 'Actif'}</small></td>
                      <td><small>{diffusableLabel(item.diffusable)}</small><small>{item.portails_resume || 'Aucune passerelle active'}</small><small>{erreurDiffusionLabel(item.has_diffusion_error)}</small></td>
                      <td><small>{item.offre_id ? 'Offre' : '-'}</small><small>{item.compromis_id ? 'Compromis' : '-'}</small><small>{item.vente_id ? 'Vente' : '-'}</small></td>
                      <td>
                        <div className="row-actions">
                          <MandatActionMenu mandat={item} role="nego" requests={visibleRequests} onOpenRequestModal={props.onOpenRequestModal} onOpenDiffusionModal={props.onOpenDiffusionModal} />
                          <button className="ghost-button" type="button" onClick={(event) => { event.stopPropagation(); openHektorAnnonce(item.hektor_annonce_id) }}>Ouvrir</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
        <section className="panel detail-panel">
          <div className="panel-head"><div><p className="eyebrow">Detail</p><h3>{view === 'requests' ? 'Traitement de la demande' : view === 'anomalies' ? 'Lecture de l anomalie' : 'Lecture mandat'}</h3></div></div>
          {view === 'requests' && selectedRequest && activeMandat ? (
            <div className="detail-stack">
              <article className="detail-card"><strong>{activeMandat.titre_bien}</strong><p>{activeMandat.numero_dossier ?? '-'} - {activeMandat.numero_mandat ?? '-'}</p><p>{commercialDisplay(activeMandat)}</p></article>
              <article className="detail-card"><span className="detail-label">Demande</span><strong>{requestTypeLabel(selectedRequest.request_type)}</strong><span>{requestStatusLabel(selectedRequest.request_status)}</span><span>{selectedRequest.request_reason || selectedRequest.request_comment || 'Sans motif'}</span></article>
              <article className="detail-card"><span className="detail-label">Traitement Pauline</span><div className="admin-form-grid"><label className="filter-field"><span>Decision</span><select value={selectedRequest.request_status} onChange={(event) => props.onUpdateRequest({ requestId: selectedRequest.id, status: event.target.value, response: comments[selectedRequest.id] ?? selectedRequest.admin_response ?? selectedRequest.processing_comment ?? '', refusalReason: selectedRefusalReason, followUpNeeded: selectedFollowUpEnabled, followUpDays: Number(selectedFollowUpDays || 0), relaunchCount: (selectedRequest.relaunch_count ?? 0) + (selectedFollowUpEnabled ? 1 : 0) })}>{requestStatusOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label><label className="filter-field"><span>Retour administratif</span><input value={comments[selectedRequest.id] ?? selectedRequest.admin_response ?? selectedRequest.processing_comment ?? ''} onChange={(event) => setComments((current) => ({ ...current, [selectedRequest.id]: event.target.value }))} placeholder="Reponse a transmettre au negociateur" /></label><label className="filter-field"><span>Motif de refus</span><input value={selectedRefusalReason} onChange={(event) => setRefusalReasons((current) => ({ ...current, [selectedRequest.id]: event.target.value }))} placeholder="A renseigner si la demande est refusee" /></label><label className="checkbox-inline"><input type="checkbox" checked={selectedFollowUpEnabled} onChange={(event) => setFollowUpEnabled((current) => ({ ...current, [selectedRequest.id]: event.target.checked }))} />Prevoir une relance</label><label className="filter-field"><span>Delai de relance</span><select value={selectedFollowUpDays} onChange={(event) => setFollowUpDays((current) => ({ ...current, [selectedRequest.id]: event.target.value }))}>{followUpPresetOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label></div><button className="ghost-button" type="button" onClick={() => props.onUpdateRequest({ requestId: selectedRequest.id, status: selectedRequest.request_status, response: comments[selectedRequest.id] ?? selectedRequest.admin_response ?? selectedRequest.processing_comment ?? '', refusalReason: selectedRefusalReason, followUpNeeded: selectedFollowUpEnabled, followUpDays: Number(selectedFollowUpDays || 0), relaunchCount: (selectedRequest.relaunch_count ?? 0) + (selectedFollowUpEnabled ? 1 : 0) })}>Enregistrer le traitement</button></article><article className="detail-card"><span className="detail-label">Suivi</span><span>{selectedRequest.follow_up_needed ? `Relance prevue le ${formatDate(selectedRequest.follow_up_at)}` : 'Pas de relance planifiee'}</span><span>{selectedRequest.relaunch_count ? `${selectedRequest.relaunch_count} relance(s)` : 'Aucune relance'}</span><span>{selectedRequest.refusal_reason || selectedRequest.admin_response || 'Pas encore de retour administratif'}</span></article>
              <article className="detail-card"><span className="detail-label">Situation diffusion</span><div className="tag-row"><StatusPill value={activeMandat.statut_annonce} /><StatusPill value={diffusableLabel(activeMandat.diffusable)} /><StatusPill value={activeMandat.portails_resume || 'Aucune passerelle active'} /><StatusPill value={erreurDiffusionLabel(activeMandat.has_diffusion_error)} /></div></article>
            </div>
          ) : activeMandat ? (
            <div className="detail-stack">
              <article className="detail-card"><strong>{activeMandat.titre_bien}</strong><p>{activeMandat.numero_dossier ?? '-'} - {activeMandat.numero_mandat ?? '-'}</p><p>{commercialDisplay(activeMandat)}</p></article>
              <article className="detail-card"><span className="detail-label">Situation</span><div className="tag-row"><StatusPill value={activeMandat.statut_annonce} /><StatusPill value={diffusableLabel(activeMandat.diffusable)} /><StatusPill value={activeMandat.portails_resume || 'Aucune passerelle active'} /><StatusPill value={erreurDiffusionLabel(activeMandat.has_diffusion_error)} /></div></article>
              <article className="detail-card"><span className="detail-label">Lecture Pauline</span><span>{!activeMandat.numero_mandat ? 'Sans mandat' : 'Mandat present'}</span><span>{(activeMandat.diffusable ?? '0') === '1' && !activeMandat.nb_portails_actifs ? 'Diffusable non visible' : 'Pas d anomalie de visibilite'}</span><span>{(activeMandat.diffusable ?? '0') !== '1' && Boolean(activeMandat.nb_portails_actifs) ? 'Annonce non diffusable mais active sur passerelle' : 'Pas d incoherence diffusable / passerelle'}</span><span>{Boolean(activeMandat.has_diffusion_error) ? 'Erreur passerelle detectee' : 'Aucune erreur passerelle'}</span></article>
              <article className="detail-card"><span className="detail-label">Affaires</span><span>{activeMandat.offre_id ? 'Offre en cours' : 'Aucune offre'}</span><span>{activeMandat.compromis_id ? 'Compromis en cours' : 'Aucun compromis'}</span><span>{activeMandat.vente_id ? 'Vente en cours' : 'Aucune vente'}</span></article>
            </div>
          ) : <p className="empty-state">Aucune ligne disponible dans cette vue.</p>}
        </section>
      </section>
    </section>
  )
}

function SuiviMandatsScreenV2(props: {
  isAdmin: boolean
  mandats: MandatRecord[]
  requests: DiffusionRequest[]
  stats: MandatStats
  loading: boolean
  onUpdateRequest: (input: { requestId: string; status: string; response: string; refusalReason: string; followUpNeeded: boolean; followUpDays: number; relaunchCount: number }) => void
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: 'demande_diffusion' | 'demande_baisse_prix') => void
  onOpenDiffusionModal: (id: number) => void
  onOpenDetailPage: (id: number) => void
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  linkedWorkItems: WorkItem[]
  detailLoading: boolean
  eyebrow?: string
  title?: string
  requestFilter?: 'pending_or_in_progress' | 'accepted_history' | 'refused' | 'waiting_correction' | null
}) {
  if (!props.isAdmin) {
    return <section className="panel"><p className="empty-state">Cette vue est reservee aux administrateurs.</p></section>
  }
  const requestRowsSource = props.requestFilter === 'accepted_history'
    ? props.mandats
        .filter((item) => Boolean((item.numero_mandat ?? '').trim()))
        .flatMap((item) => {
          const diffusionRequests = props.requests
            .filter((request) => request.app_dossier_id === item.app_dossier_id && normalizeRequestType(request.request_type) === 'demande_diffusion' && request.request_status === 'accepted')
            .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())[0]
          const priceDropRequests = props.requests
            .filter((request) => request.app_dossier_id === item.app_dossier_id && normalizeRequestType(request.request_type) === 'demande_baisse_prix' && request.request_status === 'accepted')
            .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())[0]
          return [diffusionRequests, priceDropRequests].filter(Boolean).map((request) => ({ mandat: item, request: request as DiffusionRequest }))
        })
    : props.mandats
    .filter((item) => Boolean((item.numero_mandat ?? '').trim()))
    .flatMap((item) => {
      const diffusionRequest = latestDiffusionRequest(props.requests, item.app_dossier_id, 'demande_diffusion')
      const priceDropRequest = latestDiffusionRequest(props.requests, item.app_dossier_id, 'demande_baisse_prix')
      return [diffusionRequest, priceDropRequest].filter(Boolean).map((request) => ({ mandat: item, request: request as DiffusionRequest }))
    })
  const suiviRequestRows = requestRowsSource
    .filter((row) => {
      if (!props.requestFilter) return isRequestActiveStatus(row.request.request_status)
      if (props.requestFilter === 'pending_or_in_progress') return row.request.request_status === 'pending' || row.request.request_status === 'in_progress'
      if (props.requestFilter === 'accepted_history') return row.request.request_status === 'accepted'
      if (props.requestFilter === 'refused') return row.request.request_status === 'refused'
      if (props.requestFilter === 'waiting_correction') return row.request.request_status === 'waiting_commercial' || row.request.request_status === 'refused'
      return true
    })
    .slice()
    .sort((a, b) => {
      const rankA = a.request.request_status === 'pending' || a.request.request_status === 'in_progress' ? 0 : 1
      const rankB = b.request.request_status === 'pending' || b.request.request_status === 'in_progress' ? 0 : 1
      if (rankA !== rankB) return rankA - rankB
      const dateA = new Date(a.request.requested_at ?? 0).getTime()
      const dateB = new Date(b.request.requested_at ?? 0).getTime()
      if (dateA !== dateB) return dateB - dateA
      return String(a.mandat.numero_mandat ?? '').localeCompare(String(b.mandat.numero_mandat ?? ''), 'fr')
    })
  const pendingRows = suiviRequestRows.filter((row) => row.request.request_status === 'pending')
  const inProgressRows = suiviRequestRows.filter((row) => row.request.request_status === 'in_progress')
  const correctionRows = suiviRequestRows.filter((row) => row.request.request_status === 'waiting_commercial' || row.request.request_status === 'refused')
  const anomalyRows = props.mandats
    .filter((item) =>
      Boolean((item.numero_mandat ?? '').trim()) && (
        ((item.diffusable ?? '0') === '1' && !item.nb_portails_actifs) ||
        ((item.diffusable ?? '0') !== '1' && Boolean(item.nb_portails_actifs)) ||
        Boolean(item.has_diffusion_error) ||
        !item.numero_mandat
      )
    )
    .slice(0, 18)
  const portfolioRows = props.mandats.slice(0, 100)
  return (
    <section className="panel-grid suivi-pauline-view">
      <section className="panel suivi-command-panel">
        <div className="panel-head">
          <div><p className="eyebrow">{props.eyebrow ?? 'Console Pauline'}</p><h3>{props.title ?? 'Parc mandat'}</h3></div>
          {props.loading ? <span className="loading-inline">Mise a jour...</span> : null}
        </div>
        <div className="suivi-command-grid">
          <article className="suivi-command-card tone-overview"><span className="suivi-command-kicker">Parc</span><strong>{props.stats.total}</strong><p>Annonces suivies dans le portefeuille administratif.</p></article>
          <article className="suivi-command-card tone-action"><span className="suivi-command-kicker">A traiter</span><strong>{pendingRows.length}</strong><p>Demandes nouvelles à traiter maintenant.</p></article>
          <article className="suivi-command-card tone-progress"><span className="suivi-command-kicker">En cours</span><strong>{inProgressRows.length}</strong><p>Dossiers déjà pris en charge par Pauline.</p></article>
          <article className="suivi-command-card tone-warning"><span className="suivi-command-kicker">Corrections</span><strong>{correctionRows.length}</strong><p>Retours à reprendre avec le négociateur.</p></article>
          <article className="suivi-command-card tone-danger"><span className="suivi-command-kicker">Anomalies</span><strong>{anomalyRows.length}</strong><p>Mandats avec incohérence diffusion ou données.</p></article>
          <article className="suivi-command-card tone-success"><span className="suivi-command-kicker">Diffusés</span><strong>{props.stats.mandatDiffuse}</strong><p>Mandats visibles et correctement diffusés.</p></article>
        </div>
      </section>

      <section className="suivi-block-grid">
        <section className="panel suivi-block suivi-block-primary">
          <div className="panel-head">
            <div><p className="eyebrow">Actions Pauline</p><h3>Demandes à traiter maintenant</h3></div>
          </div>
          <div className="suivi-lanes">
            {[
              { title: 'Nouvelles demandes', tone: 'action', rows: pendingRows },
              { title: 'Demandes en cours', tone: 'progress', rows: inProgressRows },
              { title: 'Corrections en attente', tone: 'warning', rows: correctionRows },
            ].map((group) => (
              <section key={group.title} className={`suivi-lane tone-${group.tone}`}>
                <div className="suivi-lane-head">
                  <strong>{group.title}</strong>
                  <span>{group.rows.length}</span>
                </div>
                <div className="timeline-list suivi-request-list">
                  {group.rows.length > 0 ? group.rows.map(({ mandat: item, request: activeRequest }) => (
                    <article key={`${item.app_dossier_id}-${activeRequest.id}`} className={`timeline-card suivi-request-card tone-${group.tone}`} onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>
                      <div className="suivi-request-head">
                        <div>
                          <strong>{item.numero_mandat ?? item.numero_dossier ?? '-'}</strong>
                          <span>{item.titre_bien}</span>
                        </div>
                        <StatusPill value={requestTypeLabel(activeRequest.request_type)} />
                      </div>
                      <div className="suivi-request-meta">
                        <span>{commercialDisplay(item)}</span>
                        <span>{formatDate(activeRequest.requested_at)}</span>
                        <span>{requestStatusLabel(activeRequest.request_status)}</span>
                      </div>
                      <p>{activeRequest.request_reason || activeRequest.request_comment || 'Sans motif'}</p>
                      <div className="row-actions">
                        <MandatActionMenu mandat={item} role="pauline" requests={props.requests} currentRequest={activeRequest} onOpenRequestModal={props.onOpenRequestModal} onOpenDiffusionModal={props.onOpenDiffusionModal} />
                      </div>
                    </article>
                  )) : <p className="empty-state">Aucune demande dans ce bloc.</p>}
                </div>
              </section>
            ))}
          </div>
        </section>

        <section className="panel suivi-block suivi-block-alerts">
          <div className="panel-head">
            <div><p className="eyebrow">Surveillance</p><h3>Anomalies diffusion et mandat</h3></div>
          </div>
          <div className="suivi-alert-grid">
            {anomalyRows.length > 0 ? anomalyRows.map((item) => {
              const anomalies = [
                !item.numero_mandat ? 'Sans mandat' : null,
                (item.diffusable ?? '0') === '1' && !item.nb_portails_actifs ? 'Diffusable non visible' : null,
                (item.diffusable ?? '0') !== '1' && Boolean(item.nb_portails_actifs) ? 'Annonce non diffusable mais active sur passerelle' : null,
                Boolean(item.has_diffusion_error) ? 'Erreur passerelle' : null,
              ].filter(Boolean)
              return (
                <article key={item.app_dossier_id} className="suivi-alert-card" onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>
                  <div className="suivi-alert-head">
                    <div>
                      <strong>{item.numero_mandat ?? item.numero_dossier ?? '-'}</strong>
                      <span>{item.titre_bien}</span>
                    </div>
                    <StatusPill value={item.statut_annonce} />
                  </div>
                  <div className="suivi-alert-meta">
                    <span>{commercialDisplay(item)}</span>
                    <span>{diffusableLabel(item.diffusable)}</span>
                  </div>
                  <div className="suivi-alert-tags">
                    {anomalies.map((label) => <span key={label} className="suivi-alert-tag">{label}</span>)}
                  </div>
                  <div className="suivi-alert-footer">
                    <span>{item.portails_resume || 'Aucune passerelle active'}</span>
                    <button className="ghost-button" type="button" onClick={(event) => { event.stopPropagation(); openHektorAnnonce(item.hektor_annonce_id) }}>Hektor</button>
                  </div>
                </article>
              )
            }) : <p className="empty-state">Aucune anomalie sur la sélection courante.</p>}
          </div>
        </section>
      </section>

      <section className="panel suivi-block suivi-block-portfolio">
        <div className="panel-head">
          <div><p className="eyebrow">Portefeuille administratif</p><h3>Vue portefeuille</h3></div>
          <div className="suivi-portfolio-kpis">
            <span>{props.stats.mandatNonDiffuse} non diffusés</span>
            <span>{props.stats.withErrors} avec erreur</span>
          </div>
        </div>
        <div className="table-wrap suivi-portfolio-wrap">
          <table className="suivi-portfolio-table">
            <thead><tr><th>Dossier</th><th>Mandat</th><th>Negociateur</th><th>Statut</th><th>Visibilite</th><th>Affaires</th><th>Actions</th></tr></thead>
            <tbody>
              {portfolioRows.map((item) => (
                <tr key={item.app_dossier_id} onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>
                  <td><strong>{item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                  <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.agence_nom ?? '-'}</span></td>
                  <td>{commercialDisplay(item)}</td>
                  <td><small>{item.statut_annonce ?? '-'}</small><small>{item.archive === '1' ? 'Archive' : 'Actif'}</small></td>
                  <td><small>{diffusableLabel(item.diffusable)}</small><small>{item.portails_resume || 'Aucune passerelle active'}</small><small>{erreurDiffusionLabel(item.has_diffusion_error)}</small></td>
                  <td><small>{item.offre_id ? 'Offre' : '-'}</small><small>{item.compromis_id ? 'Compromis' : '-'}</small><small>{item.vente_id ? 'Vente' : '-'}</small></td>
                  <td><div className="row-actions"><MandatActionMenu mandat={item} role="pauline" requests={props.requests} onOpenRequestModal={props.onOpenRequestModal} onOpenDiffusionModal={props.onOpenDiffusionModal} /></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  )
}
function DossierDetailLayout(props: {
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  texts: Array<{ id: string; title: string; html: string }>
  notes: Array<{ id: string; title: string; date: string; content: string }>
  contacts: Array<{ id: string; name: string; role: string; phone: string; email: string; address: string; comment: string }>
  mandats: Array<{ id: string; title: string; lines: Array<[string, string]> }>
  linkedWorkItems: WorkItem[]
  requestHistory: Array<{ id: string | number; title: string; date: string | null | undefined; body: string }>
  requestMessages: Array<{ id: string; author: string; date: string; message: string }>
  requestHistoryDiffusion: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesDiffusion: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryPriceDrop: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesPriceDrop: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  detailLoading: boolean
  eyebrow: string
  backLabel: string
  onBack: () => void
  allowMarkValidation?: boolean
  markValidationPending?: boolean
  validationDraft?: string | null
  validationObserved?: string | null
  validationSaved?: string | null
  onSetValidation?: (checked: boolean) => void
  allowMarkDiffusable?: boolean
  markDiffusablePending?: boolean
  onSetDiffusable?: (checked: boolean) => void
  diffusableDraft?: boolean | null
  diffusableObserved?: boolean | null
  diffusableSaved?: boolean | null
  pendingPortalKeys?: string[]
  onOpenImage?: (url: string) => void
}) {
  if (!props.selectedDossier) {
    return <section className="panel"><p className="empty-state">Aucun dossier selectionne.</p></section>
  }
  const [historyView, setHistoryView] = useState<'all' | 'diffusion' | 'price_drop'>('all')
  const dossier = props.selectedDossier
  const validationDraft = props.validationDraft ?? (isValidationApproved(dossier.validation_diffusion_state) ? 'oui' : 'non')
  const validationObserved = props.validationObserved ?? validationDraft
  const validationSaved = props.validationSaved ?? validationDraft
  const isValidated = isValidationApproved(validationDraft)
  const validationSyncPending = validationSaved !== validationObserved
  const isDraftDiffusable = props.diffusableDraft ?? isDiffusableValue(dossier.diffusable)
  const isObservedDiffusable = props.diffusableObserved ?? isDiffusableValue(dossier.diffusable)
  const isSavedDiffusable = props.diffusableSaved ?? isDraftDiffusable
  const hektorSyncPending = isSavedDiffusable !== isObservedDiffusable
  const observedPortals = uniquePortalKeys((dossier.portails_resume ?? '').split(','))
  const activePortals = uniquePortalKeys([...observedPortals, ...(props.pendingPortalKeys ?? [])])
  const portalSyncPending = (props.pendingPortalKeys ?? []).some((portal) => !observedPortals.includes(portal))
  const previewImages = props.images.slice(0, 5)
  const primaryImage = previewImages[0]?.url ?? dossier.photo_url_listing ?? null
  const showDiffusionHistory = historyView === 'all' || historyView === 'diffusion'
  const showPriceDropHistory = historyView === 'all' || historyView === 'price_drop'
  const hasAnyHistory = props.requestHistoryDiffusion.length > 0 || props.requestHistoryPriceDrop.length > 0
  const [mandatSectionOpen, setMandatSectionOpen] = useState(true)
  const [contactSectionOpen, setContactSectionOpen] = useState(false)
  const primaryContact = props.contacts[0] ?? null
  const secondaryContacts = props.contacts.slice(1)
  const buildRequestGroups = (
    historyItems: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>,
    messageItems: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>,
  ) => {
    const groups = new Map<string, { requestId: string; cycleTone: number; anchorDate: string | null | undefined; entries: Array<{ id: string | number; kind: 'summary' | 'message'; title: string; status?: string; date: string | null | undefined; body: string }> }>()
    for (const item of historyItems) {
      const current = groups.get(item.requestId) ?? {
        requestId: item.requestId,
        cycleTone: item.cycleTone ?? 0,
        anchorDate: item.date,
        entries: [],
      }
      current.anchorDate = current.anchorDate ?? item.date
      current.entries.push({
        id: item.id,
        kind: 'summary',
        title: item.title,
        status: item.status,
        date: item.date,
        body: item.body,
      })
      groups.set(item.requestId, current)
    }
    for (const item of messageItems) {
      const current = groups.get(item.requestId)
      if (!current) continue
      current.entries.push({
        id: item.id,
        kind: 'message',
        title: item.author,
        date: item.date,
        body: item.message,
      })
    }
    return Array.from(groups.values())
      .sort((a, b) => new Date(b.anchorDate ?? 0).getTime() - new Date(a.anchorDate ?? 0).getTime())
      .map((group) => ({
        ...group,
        entries: group.entries.slice().sort((a, b) => new Date(a.date ?? 0).getTime() - new Date(b.date ?? 0).getTime()),
      }))
  }
  const diffusionRequestGroups = buildRequestGroups(props.requestHistoryDiffusion, props.requestMessagesDiffusion)
  const priceDropRequestGroups = buildRequestGroups(props.requestHistoryPriceDrop, props.requestMessagesPriceDrop)

  return (
    <section className="detail-screen">
      <div className="panel">
        <div className="panel-head">
          <div className="detail-head-status">
            <span className="detail-status-chip">{dossier.statut_annonce ?? '-'}</span>
          </div>
          <div className="detail-head-actions">
            <button className="ghost-button button-accent" type="button" onClick={() => openHektorAnnonce(dossier.hektor_annonce_id)}>Ouvrir Hektor</button>
            <button className="ghost-button" type="button" onClick={props.onBack}>{props.backLabel}</button>
          </div>
        </div>

        <div className="full-detail-layout">
          <section className="detail-overview">
            <div className="detail-overview-media">
              {primaryImage ? (
                <div className="gallery gallery-compact">
                  <button className="gallery-medium-button" type="button" onClick={() => props.onOpenImage?.(primaryImage)}>
                    <img src={primaryImage} alt={dossier.titre_bien} />
                  </button>
                  {previewImages.length > 1 ? (
                    <div className="gallery-thumbs gallery-thumbs-compact">
                      {previewImages.slice(1, 5).map((item) => (
                        <button key={item.url} className="gallery-thumb-button" type="button" onClick={() => props.onOpenImage?.(item.url)}>
                          <img src={item.url} alt={item.legend || dossier.titre_bien} />
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : <div className="detail-photo-placeholder">Aucune photo synchronisee</div>}
            </div>
            <div className="detail-overview-summary">
              <h2>{dossier.titre_bien || dossier.numero_dossier || `Annonce #${dossier.hektor_annonce_id}`}</h2>
              {props.address ? <p className="detail-summary-address">{props.address}</p> : null}
              {dossier.agence_nom || dossier.commercial_nom ? (
                <p className="detail-summary-meta">
                  {[dossier.agence_nom, dossier.commercial_nom].filter(Boolean).join(' · ')}
                </p>
              ) : null}
              <div className="detail-keyfacts">
                <InfoCard label="Prix" value={formatPrice(dossier.prix)} />
                <InfoCard label="Surface" value={props.detail.surface_habitable_detail ?? props.detail.surface ?? '-'} />
                <InfoCard label="Dossier" value={dossier.numero_dossier ?? '-'} />
                <InfoCard label="Mandat" value={dossier.numero_mandat ?? '-'} />
              </div>
            </div>
          </section>

          <div className="detail-columns">
            <div className="detail-column-main">
              <section className="detail-section detail-section-topstack">
                <article className="detail-subsection">
                  <div className="section-header section-header-collapsible">
                    <h4>Detail mandat</h4>
                    <button className="section-toggle-button" type="button" onClick={() => setMandatSectionOpen((value) => !value)}>
                      {mandatSectionOpen ? 'Masquer' : 'Afficher'}
                    </button>
                  </div>
                  {mandatSectionOpen ? (props.mandats.length > 0 ? (
                    <div className="detail-entity-list detail-mandat-list">
                      {props.mandats.map((item) => (
                        <article key={item.id} className="detail-entity-card detail-mandat-card">
                          <strong>{item.title}</strong>
                          <div className="detail-mandat-grid">
                            {item.lines
                              .filter(([label]) => label.toLowerCase() !== 'note')
                              .map(([label, value]) => (
                                <div key={`${item.id}-${label}`} className="detail-mandat-cell">
                                  <span>{label}</span>
                                  <strong>{value || '-'}</strong>
                                </div>
                              ))}
                          </div>
                          {item.lines
                            .filter(([label]) => label.toLowerCase() === 'note')
                            .map(([label, value]) => (
                              <div key={`${item.id}-${label}`} className="detail-mandat-note">
                                <span>{label}</span>
                                <p>{value || '-'}</p>
                              </div>
                            ))}
                        </article>
                      ))}
                    </div>
                  ) : <p className="empty-state">Aucune information mandat riche.</p>) : null}
                </article>
                <article className="detail-subsection">
                  <div className="section-header">
                    <h4>Historique des prix</h4>
                  </div>
                  <PriceChangeHistoryCard
                    source={props.detail.price_change_events_json ? props.detail : dossier}
                    title="Historique des prix"
                    emptyLabel="Aucun changement de prix historisé pour cette annonce."
                  />
                </article>
                <article className="detail-subsection">
                  <div className="section-header section-header-collapsible">
                    <h4>Detail contact</h4>
                    {secondaryContacts.length > 0 ? (
                      <button className="section-toggle-button" type="button" onClick={() => setContactSectionOpen((value) => !value)}>
                        {contactSectionOpen ? 'Masquer la liste des mandants' : `Liste des mandants (${secondaryContacts.length + 1})`}
                      </button>
                    ) : null}
                  </div>
                  {primaryContact ? (
                    <div className="detail-entity-list detail-contact-list">
                      <article className="detail-entity-card detail-contact-card detail-contact-card-primary">
                        <div className="detail-contact-head">
                          <div className="detail-contact-avatar">{userInitials(primaryContact.name, primaryContact.email)}</div>
                          <div className="detail-contact-identity">
                            <strong>{primaryContact.name}</strong>
                            <span>{primaryContact.role || 'Contact principal'}</span>
                          </div>
                        </div>
                        <div className="detail-entity-lines detail-contact-lines">
                          <div className="detail-entity-line">
                            <span>Role</span>
                            <strong>{primaryContact.role || '-'}</strong>
                          </div>
                          <div className="detail-entity-line">
                            <span>Telephone</span>
                            <strong>{primaryContact.phone ? <a href={`tel:${primaryContact.phone}`} className="detail-contact-link">{primaryContact.phone}</a> : '-'}</strong>
                          </div>
                          <div className="detail-entity-line">
                            <span>Email</span>
                            <strong>{primaryContact.email ? <a href={`mailto:${primaryContact.email}`} className="detail-contact-link">{primaryContact.email}</a> : '-'}</strong>
                          </div>
                          <div className="detail-entity-line detail-entity-line-full">
                            <span>Adresse</span>
                            <strong>{primaryContact.address || '-'}</strong>
                          </div>
                          {primaryContact.comment ? (
                            <div className="detail-entity-line detail-entity-line-full detail-contact-note">
                              <span>Commentaire</span>
                              <strong>{primaryContact.comment}</strong>
                            </div>
                          ) : null}
                        </div>
                      </article>
                      {contactSectionOpen && secondaryContacts.length > 0 ? (
                        <div className="detail-secondary-contacts">
                          {secondaryContacts.map((contact) => (
                            <article key={contact.id} className="detail-entity-card detail-contact-card">
                              <div className="detail-contact-head">
                                <div className="detail-contact-avatar is-secondary">{userInitials(contact.name, contact.email)}</div>
                                <div className="detail-contact-identity">
                                  <strong>{contact.name}</strong>
                                  <span>{contact.role || 'Mandant'}</span>
                                </div>
                              </div>
                              <div className="detail-entity-lines detail-contact-lines">
                                <div className="detail-entity-line">
                                  <span>Role</span>
                                  <strong>{contact.role || '-'}</strong>
                                </div>
                                <div className="detail-entity-line">
                                  <span>Telephone</span>
                                  <strong>{contact.phone ? <a href={`tel:${contact.phone}`} className="detail-contact-link">{contact.phone}</a> : '-'}</strong>
                                </div>
                                <div className="detail-entity-line">
                                  <span>Email</span>
                                  <strong>{contact.email ? <a href={`mailto:${contact.email}`} className="detail-contact-link">{contact.email}</a> : '-'}</strong>
                                </div>
                                <div className="detail-entity-line detail-entity-line-full">
                                  <span>Adresse</span>
                                  <strong>{contact.address || '-'}</strong>
                                </div>
                                {contact.comment ? (
                                  <div className="detail-entity-line detail-entity-line-full detail-contact-note">
                                    <span>Commentaire</span>
                                    <strong>{contact.comment}</strong>
                                  </div>
                                ) : null}
                              </div>
                            </article>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ) : <p className="empty-state">Aucun contact detaille.</p>}
                </article>
              </section>

              <section className="detail-section">
                <div className="section-header"><h4>Descriptif</h4>{props.detailLoading ? <span>Chargement...</span> : null}</div>
                {props.texts.length > 0 ? (
                  <div className="rich-text-stack">
                    {props.texts.map((block) => <article key={block.id} className="rich-text-card"><span className="detail-label">{block.title}</span><div dangerouslySetInnerHTML={{ __html: block.html }} /></article>)}
                  </div>
                ) : <p className="empty-state">Aucun descriptif riche disponible.</p>}
              </section>

              <section className="detail-section">
                <div className="section-header"><h4>Caracteristiques du bien</h4></div>
                <div className="info-grid">
                  <InfoCard label="Type" value={propertyTypeLabel(dossier.type_bien)} />
                  <InfoCard label="Surface habitable" value={props.detail.surface_habitable_detail ?? '-'} />
                  <InfoCard label="Terrain" value={props.detail.surface_terrain_detail ?? '-'} />
                  <InfoCard label="Pieces" value={props.detail.nb_pieces ?? '-'} />
                  <InfoCard label="Chambres" value={props.detail.nb_chambres ?? '-'} />
                  <InfoCard label="Etage" value={props.detail.etage_detail ?? '-'} />
                  <InfoCard label="Terrasse" value={props.detail.terrasse_detail ?? '-'} />
                  <InfoCard label="Garage / box" value={props.detail.garage_box_detail ?? '-'} />
                  <InfoCard label="Ascenseur" value={props.detail.ascenseur_detail ?? '-'} />
                </div>
              </section>

              <section className="detail-section detail-section-transactions">
                <div className="section-header"><h4>Transactions</h4></div>
                <div className="transaction-columns">
                  <article className="transaction-card">
                    <h5>Offre</h5>
                    <div className="info-grid">
                      <InfoCard label="ID" value={props.detail.offre_id ?? '-'} />
                      <InfoCard label="Etat" value={props.detail.offre_state ?? '-'} />
                      <InfoCard label="Statut source" value={props.detail.offre_raw_status ?? '-'} />
                      <InfoCard label="Date" value={formatDate(props.detail.offre_event_date)} />
                      <InfoCard label="Montant" value={formatPrice(props.detail.offre_montant)} />
                      <InfoCard label="Acquereur" value={props.detail.offre_acquereur_nom ?? '-'} />
                    </div>
                  </article>
                  <article className="transaction-card">
                    <h5>Compromis</h5>
                    <div className="info-grid">
                      <InfoCard label="ID" value={props.detail.compromis_id ?? '-'} />
                      <InfoCard label="Etat" value={props.detail.compromis_state ?? '-'} />
                      <InfoCard label="Date debut" value={formatDate(props.detail.compromis_date_start)} />
                      <InfoCard label="Date fin" value={formatDate(props.detail.compromis_date_end)} />
                      <InfoCard label="Date acte" value={formatDate(props.detail.date_signature_acte)} />
                      <InfoCard label="Sequestre" value={formatPrice(props.detail.compromis_sequestre)} />
                    </div>
                  </article>
                  <article className="transaction-card">
                    <h5>Vente</h5>
                    <div className="info-grid">
                      <InfoCard label="ID" value={props.detail.vente_id ?? '-'} />
                      <InfoCard label="Date vente" value={formatDate(props.detail.vente_date)} />
                      <InfoCard label="Prix" value={formatPrice(props.detail.vente_prix)} />
                      <InfoCard label="Honoraires" value={formatPrice(props.detail.vente_honoraires)} />
                      <InfoCard label="Commission agence" value={formatPrice(props.detail.vente_commission_agence)} />
                      <InfoCard label="Notaires" value={props.detail.vente_notaires_resume ?? '-'} />
                    </div>
                  </article>
                </div>
              </section>

              <section className="detail-section">
                <div className="section-header"><h4>Notes et commentaires</h4></div>
                {props.notes.length > 0 ? (
                  <div className="timeline-list">
                    {props.notes.map((item) => <article key={item.id} className="timeline-card"><strong>{item.title}</strong><span>{item.date || '-'}</span><p>{item.content}</p></article>)}
                  </div>
                ) : <p className="empty-state">Aucune note disponible.</p>}
              </section>
            </div>

            <aside className="detail-column-side">
              <section className="detail-section detail-section-status">
                <div className="section-header"><h4>Diffusion</h4></div>
                {props.allowMarkValidation ? (
                  <div className="detail-diffusable-toggle detail-action-card">
                    <div className="detail-action-head">
                      <div>
                        <span className="detail-label">Pilotage Hektor</span>
                        <strong className="detail-action-title">Valider mandat</strong>
                      </div>
                      <span className={`detail-action-state ${isValidationApproved(validationDraft) ? 'is-positive' : 'is-negative'}`}>
                        {isValidationApproved(validationDraft) ? 'Etat actuel : valide' : 'Etat actuel : non valide'}
                      </span>
                    </div>
                    <div className="detail-action-meta">
                      <StatusPill value={`Validation : ${isValidationApproved(validationDraft) ? 'Oui' : 'Non'}`} />
                      <StatusPill value={`Diffusion : ${diffusableLabel(dossier.diffusable)}`} />
                    </div>
                    <div className="detail-action-buttons">
                      <button
                        className={`detail-action-button is-positive ${isValidationApproved(validationDraft) ? 'is-selected' : ''}`}
                        type="button"
                        disabled={Boolean(props.markValidationPending) || isValidationApproved(validationDraft)}
                        onClick={() => props.onSetValidation?.(true)}
                      >
                        Activer
                      </button>
                      <button
                        className={`detail-action-button is-negative ${!isValidationApproved(validationDraft) ? 'is-selected' : ''}`}
                        type="button"
                        disabled={Boolean(props.markValidationPending) || !isValidationApproved(validationDraft)}
                        onClick={() => props.onSetValidation?.(false)}
                      >
                        Desactiver
                      </button>
                    </div>
                    <div className="detail-action-caption">
                      Debloque la diffusion Hektor et les passerelles quand la validation est confirmee.
                    </div>
                    {props.markValidationPending ? (
                      <div className="detail-sync-alert is-pending">Validation Hektor en cours...</div>
                    ) : validationSyncPending ? (
                      <div className="detail-sync-alert is-waiting">{`Relecture Hektor : ${isValidationApproved(validationObserved) ? 'valide' : 'non valide'}`}</div>
                    ) : (
                      <div className="detail-sync-alert is-confirmed">{`Validation confirmee : ${isValidationApproved(validationObserved) ? 'Oui' : 'Non'}`}</div>
                    )}
                  </div>
                ) : null}
                {props.allowMarkDiffusable ? (
                  <div className="detail-diffusable-toggle detail-action-card">
                    <div className="detail-action-head">
                      <div>
                        <span className="detail-label">Pilotage Hektor</span>
                        <strong className="detail-action-title">Diffuser mandat</strong>
                      </div>
                      <span className={`detail-action-state ${isDraftDiffusable ? 'is-positive' : 'is-negative'}`}>
                        {isDraftDiffusable ? 'Etat actuel : diffusable' : 'Etat actuel : non diffusable'}
                      </span>
                    </div>
                    <div className="detail-action-meta">
                      <StatusPill value={`Diffusable : ${isDraftDiffusable ? 'Oui' : 'Non'}`} />
                      <StatusPill value={dossier.portails_resume || 'Aucune passerelle active'} />
                    </div>
                    <div className="detail-action-buttons">
                      <button
                        className={`detail-action-button is-positive ${isDraftDiffusable ? 'is-selected' : ''}`}
                        type="button"
                        disabled={Boolean(props.markDiffusablePending) || isDraftDiffusable}
                        onClick={() => props.onSetDiffusable?.(true)}
                      >
                        Activer
                      </button>
                      <button
                        className={`detail-action-button is-negative ${!isDraftDiffusable ? 'is-selected' : ''}`}
                        type="button"
                        disabled={Boolean(props.markDiffusablePending) || !isDraftDiffusable}
                        onClick={() => props.onSetDiffusable?.(false)}
                      >
                        Desactiver
                      </button>
                    </div>
                    <div className="detail-action-caption">
                      Pilote l'etat diffusable relu par Hektor et conditionne les actions de diffusion.
                    </div>
                    {props.markDiffusablePending || hektorSyncPending || portalSyncPending ? (
                      <div className={`detail-sync-alert ${props.markDiffusablePending ? 'is-pending' : 'is-waiting'}`}>
                        {props.markDiffusablePending
                          ? 'Mise a jour diffusion en cours...'
                          : 'Mise a jour envoyee. En attente de confirmation Hektor ou passerelles.'}
                      </div>
                    ) : (
                      <div className="detail-sync-alert is-confirmed">{`Diffusion confirmee : ${isDraftDiffusable ? 'Oui' : 'Non'}`}</div>
                    )}
                  </div>
                ) : null}
                <div className="detail-portals-list">
                  <span className="detail-label">Passerelles activees</span>
                  {activePortals.length > 0 ? (
                    <div className="timeline-list">
                      {activePortals.map((portal) => (
                        <article key={portal} className="timeline-card">
                          <strong>{portal}</strong>
                          <span>{observedPortals.includes(portal) ? "Etat lu dans l'application" : 'Activation demandee en attente Hektor'}</span>
                          <span>Depuis : {formatDate(props.detail.date_maj ?? null)}</span>
                        </article>
                      ))}
                    </div>
                  ) : <p className="empty-state">Aucune passerelle active.</p>}
                </div>
              </section>

              <section className="detail-section">
                <div className="section-header">
                  <h4>Historique des demandes</h4>
                  <div className="segmented-control">
                    <button className={`segment-button ${historyView === 'all' ? 'is-active' : ''}`} type="button" onClick={() => setHistoryView('all')}>Tout</button>
                    <button className={`segment-button ${historyView === 'diffusion' ? 'is-active' : ''}`} type="button" onClick={() => setHistoryView('diffusion')}>Diffusion</button>
                    <button className={`segment-button ${historyView === 'price_drop' ? 'is-active' : ''}`} type="button" onClick={() => setHistoryView('price_drop')}>Baisse de prix</button>
                  </div>
                </div>
                {showDiffusionHistory && props.requestHistoryDiffusion.length > 0 ? (
                  <>
                    <span className="detail-label">Diffusion</span>
                    <div className="request-group-list">
                      {diffusionRequestGroups.map((group, index) => (
                        <section key={`group-diffusion-${group.requestId}`} className={`request-group tone-${group.cycleTone}`}>
                          <div className="request-group-head">
                            <span className="request-group-badge">Demande {diffusionRequestGroups.length - index}</span>
                          </div>
                          <div className="timeline-list">
                            {group.entries.map((entry) => (
                              <article key={`history-diffusion-${entry.id}`} className={`timeline-card request-cycle-card tone-${group.cycleTone}`}>
                                <strong>{entry.title}</strong>
                                <span className="request-history-date">Date : {formatDate(entry.date)}</span>
                                {entry.kind === 'summary' && entry.status ? <span>{requestStatusLabel(entry.status)}</span> : null}
                                <p>{entry.body}</p>
                              </article>
                            ))}
                          </div>
                        </section>
                      ))}
                    </div>
                  </>
                ) : null}
                {showPriceDropHistory && props.requestHistoryPriceDrop.length > 0 ? (
                  <>
                    <span className="detail-label">Baisse de prix</span>
                    <div className="request-group-list">
                      {priceDropRequestGroups.map((group, index) => (
                        <section key={`group-price-${group.requestId}`} className={`request-group tone-${group.cycleTone}`}>
                          <div className="request-group-head">
                            <span className="request-group-badge">Demande {priceDropRequestGroups.length - index}</span>
                          </div>
                          <div className="timeline-list">
                            {group.entries.map((entry) => (
                              <article key={`history-price-${entry.id}`} className={`timeline-card request-cycle-card tone-${group.cycleTone}`}>
                                <strong>{entry.title}</strong>
                                <span className="request-history-date">Date : {formatDate(entry.date)}</span>
                                {entry.kind === 'summary' && entry.status ? <span>{requestStatusLabel(entry.status)}</span> : null}
                                <p>{entry.body}</p>
                              </article>
                            ))}
                          </div>
                        </section>
                      ))}
                    </div>
                  </>
                ) : null}
                {!hasAnyHistory ? (
                  props.linkedWorkItems.length > 0 ? (
                    <div className="timeline-list">
                      {props.linkedWorkItems.map((item) => <article key={`${item.app_dossier_id}-${item.type_demande_label}-${item.date_entree_file ?? 'na'}`} className="timeline-card"><strong>{item.type_demande_label ?? '-'}</strong><span>{item.work_status ?? '-'} - {item.internal_status ?? '-'}</span><span>{item.validation_diffusion_state ?? '-'} - {item.etat_visibilite ?? '-'}</span><span>Relance : {formatDate(item.date_relance_prevue)}</span></article>)}
                    </div>
                  ) : <p className="empty-state">Aucun historique de demande sur la page courante.</p>
                ) : null}
              </section>
            </aside>
          </div>
        </div>
      </div>
    </section>
  )
}

function DossierInlineDetail(props: {
  dossier: Dossier | MandatRecord | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  linkedWorkItems: WorkItem[]
  detailLoading: boolean
  extraCards?: React.ReactNode
}) {
  if (!props.dossier) {
    return <p className="empty-state">Chargement du detail...</p>
  }
  const heroImage = props.images[0]?.url || props.detail.photo_url_listing || null

  return (
    <div className="detail-stack detail-stack-rich">
      <article className="detail-card detail-card-hero">
        <div className="detail-card-hero-media">
          {heroImage ? <img src={heroImage} alt={props.dossier.titre_bien} loading="lazy" /> : <div className="detail-card-hero-placeholder">Aucune photo</div>}
        </div>
        <div className="detail-card-hero-body">
          <strong>{props.dossier.titre_bien}</strong>
          <p>{props.address || '-'}</p>
          <div className="tag-row">
            <StatusPill value={props.dossier.statut_annonce} />
            <StatusPill value={diffusableLabel(props.dossier.diffusable)} />
            <StatusPill value={props.dossier.portails_resume || 'Aucune passerelle active'} />
            <StatusPill value={erreurDiffusionLabel(props.dossier.has_diffusion_error)} />
          </div>
        </div>
      </article>
      <article className="detail-card">
        <span className="detail-label">Lecture detaillee</span>
        <div className="info-grid">
          <InfoCard label="Dossier" value={props.dossier.numero_dossier} />
          <InfoCard label="Mandat" value={props.dossier.numero_mandat} />
          <InfoCard label="Commercial" value={props.dossier.commercial_nom} />
          <InfoCard label="Agence" value={props.dossier.agence_nom} />
          <InfoCard label="Prix" value={formatPrice(props.dossier.prix)} />
          <InfoCard label="Surface" value={props.detail.surface_habitable_detail ?? props.detail.surface ?? '-'} />
          <InfoCard label="Pieces" value={props.detail.nb_pieces ?? '-'} />
          <InfoCard label="Chambres" value={props.detail.nb_chambres ?? '-'} />
          <InfoCard label="Photos" value={props.detail.nb_images ?? props.images.length} />
          <InfoCard label="Validation" value={props.dossier.validation_diffusion_state ?? '-'} />
          <InfoCard label="Visibilite" value={'etat_visibilite' in props.dossier ? props.dossier.etat_visibilite ?? '-' : '-'} />
        </div>
        {props.detailLoading ? <p className="detail-inline-loading">Chargement detail...</p> : null}
      </article>
      <article className="detail-card">
        <span className="detail-label">Affaires et suivi</span>
        <div className="info-grid">
          <InfoCard label="Offre" value={props.detail.offre_state ?? '-'} />
          <InfoCard label="Compromis" value={props.detail.compromis_state ?? '-'} />
          <InfoCard label="Vente" value={formatDate(props.detail.vente_date)} />
          <InfoCard label="Prochaine action" value={props.detail.next_action ?? '-'} />
          <InfoCard label="Blocage" value={props.detail.motif_blocage ?? '-'} />
          <InfoCard label="Commentaire" value={'commentaire_resume' in props.dossier ? props.dossier.commentaire_resume ?? '-' : '-'} />
        </div>
      </article>
      {props.extraCards}
      <article className="detail-card">
        <span className="detail-label">Demandes liees</span>
        {props.linkedWorkItems.length > 0 ? (
          <div className="detail-task-list">
            {props.linkedWorkItems.slice(0, 6).map((item) => (
              <div key={`${item.app_dossier_id}-${item.type_demande_label}-${item.date_entree_file ?? 'na'}`} className="detail-task-item">
                <strong>{item.type_demande_label ?? '-'}</strong>
                <span>{item.work_status ?? '-'} - {item.internal_status ?? '-'}</span>
                <span>{item.validation_diffusion_state ?? '-'} - {item.etat_visibilite ?? '-'}</span>
              </div>
            ))}
          </div>
        ) : <p>Aucune demande liee sur ce dossier.</p>}
      </article>
    </div>
  )
}

function AnnonceScreen(props: {
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  texts: Array<{ id: string; title: string; html: string }>
  notes: Array<{ id: string; title: string; date: string; content: string }>
  contacts: Array<{ id: string; name: string; role: string; phone: string; email: string; address: string; comment: string }>
  mandats: Array<{ id: string; title: string; lines: Array<[string, string]> }>
  linkedWorkItems: WorkItem[]
  requestHistory: Array<{ id: string | number; title: string; date: string | null | undefined; body: string }>
  requestMessages: Array<{ id: string; author: string; date: string; message: string }>
  requestHistoryDiffusion: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesDiffusion: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryPriceDrop: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesPriceDrop: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  detailLoading: boolean
  onBack: () => void
}) {
  return <DossierDetailLayout {...props} eyebrow="Annonce complete" backLabel="Retour stock" />
}

function DossierDetailScreen(props: {
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  texts: Array<{ id: string; title: string; html: string }>
  notes: Array<{ id: string; title: string; date: string; content: string }>
  contacts: Array<{ id: string; name: string; role: string; phone: string; email: string; address: string; comment: string }>
  mandats: Array<{ id: string; title: string; lines: Array<[string, string]> }>
  linkedWorkItems: WorkItem[]
  requestHistory: Array<{ id: string | number; title: string; date: string | null | undefined; body: string }>
  requestMessages: Array<{ id: string; author: string; date: string; message: string }>
  requestHistoryDiffusion: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesDiffusion: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryPriceDrop: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesPriceDrop: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  detailLoading: boolean
  sourceScreen: 'mandats' | 'suivi'
  onBack: () => void
}) {
  return (
    <DossierDetailLayout
      {...props}
      eyebrow={props.sourceScreen === 'mandats' ? 'Detail mandat' : 'Detail suivi'}
      backLabel={props.sourceScreen === 'mandats' ? 'Retour mandats' : 'Retour suivi'}
    />
  )
}

function StatusPill({ value }: { value: string | null }) {
  if (!value) return null
  return <span className="status-pill">{value}</span>
}

function PortalStatusMark({ enabled }: { enabled: boolean }) {
  return (
    <span className={`portal-mark ${enabled ? 'is-enabled' : 'is-disabled'}`} title={enabled ? 'Oui' : 'Non'} aria-label={enabled ? 'Oui' : 'Non'}>
      <svg viewBox="0 0 20 20" aria-hidden="true">
        {enabled ? (
          <path d="M5 10.5 8.2 13.7 15 6.8" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" />
        ) : (
          <>
            <path d="M6 6 14 14" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" />
            <path d="M14 6 6 14" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" />
          </>
        )}
      </svg>
    </span>
  )
}

function listingPreviewUrl(imagesPreviewJson?: string | null, fallbackUrl?: string | null) {
  const previewImages = parseJson<Array<Record<string, unknown>>>(imagesPreviewJson, [])
  for (const image of previewImages) {
    const candidate = safeText(image.url)
    if (candidate) return candidate
  }
  return fallbackUrl ?? null
}

function ListingThumbnail({ url, imagesPreviewJson, title }: { url?: string | null; imagesPreviewJson?: string | null; title: string }) {
  const resolvedUrl = listingPreviewUrl(imagesPreviewJson, url)
  if (!resolvedUrl) {
    return <div className="listing-thumb listing-thumb-placeholder" aria-hidden="true">{title.slice(0, 1).toUpperCase()}</div>
  }
  return (
    <img
      className="listing-thumb"
      src={resolvedUrl}
      alt={title}
      loading="lazy"
      decoding="async"
    />
  )
}

function PriceChangeHistoryCard({
  source,
  title = 'Historique des prix',
  emptyLabel = 'Aucun changement de prix detecte.',
}: {
  source: Record<string, unknown> | DossierDetailPayload | Dossier | MandatRecord
  title?: string
  emptyLabel?: string
}) {
  const events = readPriceChangeEvents(source)
    .slice()
    .sort((a, b) => new Date(priceChangeAnchorDate(b) ?? 0).getTime() - new Date(priceChangeAnchorDate(a) ?? 0).getTime())

  return (
    <article className="detail-card">
      <span className="detail-label">{title}</span>
      {events.length > 0 ? (
        <div className="timeline-list price-history-list">
          {events.map((entry, index) => (
            <article key={`price-history-${index}-${entry.detected_at ?? 'na'}`} className="timeline-card price-history-card">
              <div className="price-history-head">
                <strong>{formatPrice(entry.old_value)} → {formatPrice(entry.new_value)}</strong>
                <span>{priceChangeSourceLabel(entry.source_kind)}</span>
              </div>
              <div className="price-history-meta">
                <span>Maj Hektor : {formatDate(priceChangeAnchorDate(entry))}</span>
                {entry.detected_at && entry.detected_at !== entry.source_updated_at ? <span>Detecte : {formatDate(entry.detected_at)}</span> : null}
                {entry.numero_mandat ? <span>Mandat {entry.numero_mandat}</span> : null}
              </div>
            </article>
          ))}
        </div>
      ) : <p>{emptyLabel}</p>}
    </article>
  )
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: Array<string | { value: string; label: string }>
}) {
  return (
    <label className="filter-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value={allFilterValue}>Tous</option>
        {options.map((option) => {
          const normalized = typeof option === 'string' ? { value: option, label: option } : option
          return <option key={normalized.value} value={normalized.value}>{normalized.label}</option>
        })}
      </select>
    </label>
  )
}

function MetricCard({
  label,
  value,
  tone = 'neutral',
  active = false,
  onClick,
}: {
  label: string
  value: string | number | null | undefined
  tone?: 'brand' | 'success' | 'warning' | 'danger' | 'neutral'
  active?: boolean
  onClick?: () => void
}) {
  const content = (
    <>
      <span>{label}</span>
      <strong>{value == null || value === '' ? '-' : value}</strong>
    </>
  )
  if (onClick) {
    return <button className={`metric-card tone-${tone} ${active ? 'is-active' : ''}`} type="button" onClick={onClick}>{content}</button>
  }
  return <article className={`metric-card tone-${tone}`}><span>{label}</span><strong>{value == null || value === '' ? '-' : value}</strong></article>
}

function InfoCard({ label, value }: { label: string; value: string | number | null | undefined }) {
  return <article className="info-card"><span>{label}</span><strong>{value == null || value === '' ? '-' : value}</strong></article>
}


