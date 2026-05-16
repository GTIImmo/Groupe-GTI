import { ChangeEvent, FormEvent, Fragment, useEffect, useMemo, useRef, useState } from 'react'
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
  loadDossierByHektorAnnonceId,
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
  loadHektorNegotiatorOptions,
  loadUserNegotiatorContext,
  loadUserProfile,
  loadWorkItemsPage,
  sendPasswordResetEmail,
  submitDiffusionCorrection,
  updateAppUser,
  updateDiffusionRequest,
  verifyPriceDropOnHektor,
  loadConsoleDocuments,
  createPrepareConsoleDocumentJob,
  createUploadDocumentToHektorJob,
  createDeleteDocumentFromHektorJob,
  createHektorMandantContactJob,
  createUpdateHektorMandantContactJob,
  createUpdateHektorAnnonceFieldsJob,
  createDeleteHektorAnnonceJob,
  createHektorDraftAnnonceJob,
  createConsoleDocumentSignedUrl,
  loadActiveHektorActionJobs,
  loadConsoleJobsByIds,
} from './lib/api'
import { getCurrentSession, hasSupabaseEnv, signInWithPassword, signOut, supabase, updatePassword } from './lib/supabase'
import type { ConsoleDocument, ConsoleDocumentVisibility, ConsoleJob, DetailedDossier, DiffusionRequest, DiffusionRequestEvent, DiffusionTarget, Dossier, DossierDetailPayload, HektorNegotiatorOption, MandatBroadcast, MandatRecord, MatterportGroup, UserNegotiatorContext, UserProfile, WorkItem } from './types'
import { DesktopLayout } from './layouts/DesktopLayout'
import { MobileLayout } from './layouts/MobileLayout'
import { useResponsiveExperience } from './hooks/useResponsiveExperience'

type DetailContact = {
  id: string
  name: string
  role: string
  phone: string
  email: string
  address: string
  postalCode: string
  city: string
  civility: string
  firstName: string
  lastName: string
  comment: string
  sourceId?: string
  archive?: string
  dateCreated?: string
  dateUpdated?: string
  negotiatorId?: string
}

const allFilterValue = '__all__'
const activeArchiveFilterValue = '__active__'
const archivedFilterValue = '__archived__'
const withMandatFilterValue = '__with_mandat__'
const withoutMandatFilterValue = '__without_mandat__'
const withoutCommercialFilterValue = '__without_commercial__'
const activeListingsFilterValue = '__active_listings__'
type Screen = 'annonces' | 'mandats' | 'estimations' | 'registre' | 'suivi'
type BusinessRequestType = 'demande_diffusion' | 'demande_baisse_prix' | 'demande_annulation_mandat'

function numericDraft(value: unknown): string {
  return String(value ?? '').replace(/[^\d,.-]/g, '').trim()
}

function HektorAnnonceUpdateForm(props: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'titre_bien' | 'prix'>
  detail: Pick<DossierDetailPayload, 'surface_habitable_detail' | 'surface' | 'nb_pieces' | 'nb_chambres'>
  compact?: boolean
  fieldPanel?: boolean
  onCancel?: () => void
  onJobCreated?: (job: ConsoleJob) => void
}) {
  const { dossier, detail } = props
  const [title, setTitle] = useState(dossier.titre_bien ?? '')
  const [description, setDescription] = useState('')
  const [price, setPrice] = useState(numericDraft(dossier.prix))
  const [surface, setSurface] = useState(numericDraft(detail.surface_habitable_detail ?? detail.surface))
  const [roomCount, setRoomCount] = useState(numericDraft(detail.nb_pieces))
  const [bedroomCount, setBedroomCount] = useState(numericDraft(detail.nb_chambres))
  const [pending, setPending] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setTitle(dossier.titre_bien ?? '')
    setDescription('')
    setPrice(numericDraft(dossier.prix))
    setSurface(numericDraft(detail.surface_habitable_detail ?? detail.surface))
    setRoomCount(numericDraft(detail.nb_pieces))
    setBedroomCount(numericDraft(detail.nb_chambres))
    setMessage(null)
    setError(null)
    setPending(false)
  }, [dossier.app_dossier_id, dossier.titre_bien, dossier.prix, detail.surface_habitable_detail, detail.surface, detail.nb_pieces, detail.nb_chambres])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMessage(null)
    setError(null)
    setPending(true)
    try {
      const job = await createUpdateHektorAnnonceFieldsJob({
        dossier,
        fields: {
          title,
          description,
          price,
          surface,
          roomCount,
          bedroomCount,
        },
        priority: 14,
      })
      props.onJobCreated?.(job)
      setMessage(null)
      props.onCancel?.()
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Modification Hektor impossible.')
    } finally {
      setPending(false)
    }
  }

  return (
    <form className={`hektor-inline-form hektor-annonce-update-form ${props.compact ? 'is-compact' : ''} ${props.fieldPanel ? 'is-field-panel' : ''}`} onSubmit={handleSubmit}>
      <div className="hektor-inline-form-head">
        <span className="hektor-inline-icon" aria-hidden="true">M</span>
        <div>
          <strong>Modifier les champs Hektor</strong>
          <small>Prix, surface, pieces, chambres et texte principal.</small>
        </div>
      </div>
      <div className="hektor-inline-grid">
        <label>
          <span>Titre</span>
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Titre visible" />
        </label>
        <label>
          <span>Prix public</span>
          <input value={price} onChange={(event) => setPrice(event.target.value)} inputMode="decimal" placeholder="Prix" />
        </label>
        <label>
          <span>Surface</span>
          <input value={surface} onChange={(event) => setSurface(event.target.value)} inputMode="decimal" placeholder="m2" />
        </label>
        <label>
          <span>Pieces</span>
          <input value={roomCount} onChange={(event) => setRoomCount(event.target.value)} inputMode="numeric" placeholder="Pieces" />
        </label>
        <label>
          <span>Chambres</span>
          <input value={bedroomCount} onChange={(event) => setBedroomCount(event.target.value)} inputMode="numeric" placeholder="Chambres" />
        </label>
      </div>
      <label className="hektor-inline-textarea">
        <span>Description principale</span>
        <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Laisser vide pour ne pas changer le texte principal" />
      </label>
      <div className="hektor-inline-actions">
        <button type="submit" disabled={pending}>{pending ? 'Envoi...' : 'Envoyer vers Hektor'}</button>
        {props.onCancel ? <button className="button-subtle" type="button" onClick={props.onCancel} disabled={pending}>Fermer</button> : null}
        {message ? <span className="hektor-inline-feedback is-success">{message}</span> : null}
        {error ? <span className="hektor-inline-feedback is-error">{error}</span> : null}
      </div>
    </form>
  )
}

function HektorMandantContactForm(props: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'negociateur_email'>
  compact?: boolean
  initialOpen?: boolean
  onJobCreated?: (job: ConsoleJob) => void
}) {
  const [open, setOpen] = useState(Boolean(props.initialOpen))
  const [civility, setCivility] = useState('')
  const [lastName, setLastName] = useState('')
  const [firstName, setFirstName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [pending, setPending] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setOpen(Boolean(props.initialOpen))
    setCivility('')
    setLastName('')
    setFirstName('')
    setEmail('')
    setPhone('')
    setMessage(null)
    setError(null)
    setPending(false)
  }, [props.dossier.app_dossier_id, props.initialOpen])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMessage(null)
    setError(null)
    if (!lastName.trim() || !email.trim()) {
      setError('Nom et email sont obligatoires pour créer le contact Hektor.')
      return
    }
    setPending(true)
    try {
      const job = await createHektorMandantContactJob({
        dossier: props.dossier,
        contact: {
          civility,
          lastName,
          firstName,
          email,
          phone,
        },
        priority: 18,
      })
      setCivility('')
      setLastName('')
      setFirstName('')
      setEmail('')
      setPhone('')
      props.onJobCreated?.(job)
      setMessage(null)
      setOpen(false)
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Creation du mandant impossible.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className={`hektor-mandant-create-shell ${props.compact ? 'is-compact' : ''} ${open ? 'is-open' : ''}`}>
      {!open ? (
        <button className="hektor-mandant-add-card" type="button" onClick={() => setOpen(true)}>
          <span aria-hidden="true">+</span>
          <strong>Ajouter un mandant</strong>
          <small>Nouveau contact Hektor associe a cette annonce</small>
        </button>
      ) : null}
      {open ? (
    <form className={`hektor-inline-form hektor-mandant-create-form ${props.compact ? 'is-compact' : ''}`} onSubmit={handleSubmit}>
      <div className="hektor-inline-form-head">
        <span className="hektor-inline-icon" aria-hidden="true">+</span>
        <div>
          <strong>Créer un mandant Hektor</strong>
          <small>Le contact est créé puis associé automatiquement à cette annonce.</small>
        </div>
      </div>
      <div className="hektor-inline-grid">
        <label className="is-small">
          <span>Civilite</span>
          <select value={civility} onChange={(event) => setCivility(event.target.value)}>
            <option value="">-</option>
            <option value="M.">M.</option>
            <option value="Mme.">Mme.</option>
            <option value="Mlle.">Mlle.</option>
          </select>
        </label>
        <label>
          <span>Nom</span>
          <input value={lastName} onChange={(event) => setLastName(event.target.value)} placeholder="Nom" required />
        </label>
        <label>
          <span>Prenom</span>
          <input value={firstName} onChange={(event) => setFirstName(event.target.value)} placeholder="Prenom" />
        </label>
        <label>
          <span>Email</span>
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="email@exemple.fr" required />
        </label>
        <label>
          <span>Telephone</span>
          <input value={phone} onChange={(event) => setPhone(event.target.value)} inputMode="tel" placeholder="Portable" />
        </label>
      </div>
      <div className="hektor-inline-actions">
        <button type="submit" disabled={pending}>{pending ? 'Envoi...' : 'Créer et associer'}</button>
        <button className="button-subtle" type="button" onClick={() => setOpen(false)} disabled={pending}>Annuler</button>
        {message ? <span className="hektor-inline-feedback is-success">{message}</span> : null}
        {error ? <span className="hektor-inline-feedback is-error">{error}</span> : null}
      </div>
    </form>
      ) : null}
    </div>
  )
}

function HektorMandantContactEditForm(props: {
  dossier: Pick<Dossier, 'app_dossier_id' | 'hektor_annonce_id' | 'negociateur_email'>
  contact: DetailContact
  compact?: boolean
  onJobCreated?: (job: ConsoleJob) => void
}) {
  const [open, setOpen] = useState(false)
  const [civility, setCivility] = useState(props.contact.civility ?? '')
  const [lastName, setLastName] = useState(props.contact.lastName ?? '')
  const [firstName, setFirstName] = useState(props.contact.firstName ?? '')
  const [email, setEmail] = useState(props.contact.email ?? '')
  const [phone, setPhone] = useState(props.contact.phone ?? '')
  const [address, setAddress] = useState(props.contact.address ?? '')
  const [postalCode, setPostalCode] = useState(props.contact.postalCode ?? '')
  const [city, setCity] = useState(props.contact.city ?? '')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setOpen(false)
    setCivility(props.contact.civility ?? '')
    setLastName(props.contact.lastName ?? '')
    setFirstName(props.contact.firstName ?? '')
    setEmail(props.contact.email ?? '')
    setPhone(props.contact.phone ?? '')
    setAddress(props.contact.address ?? '')
    setPostalCode(props.contact.postalCode ?? '')
    setCity(props.contact.city ?? '')
    setPending(false)
    setError(null)
  }, [props.contact.sourceId, props.dossier.app_dossier_id])

  const canEdit = Boolean(props.contact.sourceId && /^\d+$/.test(props.contact.sourceId))

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    if (!canEdit || !props.contact.sourceId) {
      setError('ID contact Hektor manquant.')
      return
    }
    if (!lastName.trim() || !email.trim()) {
      setError('Nom et email sont obligatoires pour modifier le contact Hektor.')
      return
    }
    setPending(true)
    try {
      const job = await createUpdateHektorMandantContactJob({
        dossier: props.dossier,
        contactId: props.contact.sourceId,
        contact: {
          civility,
          lastName,
          firstName,
          email,
          phone,
          address,
          postalCode,
          city,
        },
        priority: 16,
      })
      props.onJobCreated?.(job)
      setOpen(false)
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Modification du mandant impossible.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className={`hektor-inline-form hektor-mandant-edit-form ${props.compact ? 'is-compact' : ''}`}>
      <button className="hektor-contact-edit-toggle" type="button" disabled={!canEdit} onClick={() => setOpen((value) => !value)}>
        <span aria-hidden="true">✎</span>
        {open ? 'Fermer' : 'Modifier'}
      </button>
      {open ? (
        <form onSubmit={handleSubmit}>
          <div className="hektor-inline-grid">
            <label className="is-small">
              <span>Civilite</span>
              <select value={civility} onChange={(event) => setCivility(event.target.value)}>
                <option value="">-</option>
                <option value="M.">M.</option>
                <option value="Mme.">Mme.</option>
                <option value="Mlle.">Mlle.</option>
              </select>
            </label>
            <label>
              <span>Nom</span>
              <input value={lastName} onChange={(event) => setLastName(event.target.value)} required />
            </label>
            <label>
              <span>Prenom</span>
              <input value={firstName} onChange={(event) => setFirstName(event.target.value)} />
            </label>
            <label>
              <span>Email</span>
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
            </label>
            <label>
              <span>Telephone</span>
              <input value={phone} onChange={(event) => setPhone(event.target.value)} inputMode="tel" />
            </label>
            <label>
              <span>Adresse</span>
              <input value={address} onChange={(event) => setAddress(event.target.value)} />
            </label>
            <label className="is-small">
              <span>CP</span>
              <input value={postalCode} onChange={(event) => setPostalCode(event.target.value)} inputMode="numeric" />
            </label>
            <label>
              <span>Ville</span>
              <input value={city} onChange={(event) => setCity(event.target.value)} />
            </label>
          </div>
          <div className="hektor-inline-actions">
            <button type="submit" disabled={pending}>{pending ? 'Envoi...' : 'Envoyer la modification'}</button>
            {error ? <span className="hektor-inline-feedback is-error">{error}</span> : null}
          </div>
        </form>
      ) : null}
    </div>
  )
}
type UpdateDiffusionRequestAction = {
  requestId: string
  requestType?: BusinessRequestType
  status: string
  response: string
  refusalReason: string
  followUpNeeded: boolean
  followUpDays: number
  relaunchCount: number
  priceDropChecked?: boolean
  publishAfterPriceDrop?: boolean
  validationChecked?: boolean
  runValidationWorkflow?: boolean
  cancellationChecked?: boolean
  unpublishAfterCancellation?: boolean
}

function detailVariantForScreen(screen: Screen): 'annonce' | 'mandat' | 'suivi' {
  if (screen === 'registre') return 'mandat'
  if (screen === 'suivi') return 'suivi'
  return 'annonce'
}

function detailEyebrowForScreen(screen: Screen) {
  if (screen === 'registre') return 'Detail mandat'
  if (screen === 'suivi') return 'Detail suivi'
  if (screen === 'estimations') return 'Detail estimation'
  return 'Detail annonce'
}

const activeListingStatusTokens = new Set(['actif', 'sous offre', 'sous compromis'])

function screenStatusToken(value: string | null | undefined) {
  return (value ?? '').trim().toLowerCase()
}

function filterMandatRowsForScreen(rows: MandatRecord[], screen: Screen) {
  if (screen === 'estimations') {
    return rows.filter((item) => screenStatusToken(item.statut_annonce) === 'estimation')
  }
  if (screen === 'mandats' || screen === 'suivi') {
    return rows.filter((item) => activeListingStatusTokens.has(screenStatusToken(item.statut_annonce)))
  }
  return rows
}

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
const cancellationRefusalReasonOptions = [
  { value: 'motif_annulation_manquant', label: "Motif d'annulation manquant" },
  { value: 'document_mandat_manquant', label: 'Document mandat manquant' },
  { value: 'annulation_non_conforme', label: 'Annulation non conforme' },
  { value: 'autre', label: 'Autre' },
]
const requestTypeOptions = [
  { value: 'demande_diffusion', label: 'Validation' },
  { value: 'demande_baisse_prix', label: 'Baisse de prix' },
  { value: 'demande_annulation_mandat', label: 'Annulation mandat' },
]

function refusalReasonLabel(value: string | null | undefined) {
  const normalized = (value ?? '').trim()
  if (!normalized) return ''
  const match = [...refusalReasonOptions, ...priceDropRefusalReasonOptions, ...cancellationRefusalReasonOptions].find((option) => option.value === normalized)
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
  mandateState: allFilterValue,
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

function defaultFiltersForScreen(screen: Screen): AppFilters {
  if (screen === 'registre') {
    return {
      ...emptyFilters,
      statut: 'Actif',
    }
  }
  if (screen === 'suivi') {
    return {
      ...emptyFilters,
      statut: activeListingsFilterValue,
    }
  }
  return emptyFilters
}

function metricDrilldownFilters(current: AppFilters, action: HeaderMetricItem['action']): AppFilters {
  const baseFilters: AppFilters = {
    ...current,
    affaire: allFilterValue,
    offreStatus: allFilterValue,
    compromisStatus: allFilterValue,
    requestScope: allFilterValue,
    mandat: allFilterValue,
    validationDiffusion: allFilterValue,
    diffusable: allFilterValue,
    passerelle: allFilterValue,
  }

  if (!action) return baseFilters

  return {
    ...baseFilters,
    affaire:
      action === 'offres_en_cours' || action === 'offres_refusees'
        ? 'offre_achat'
        : action === 'compromis_en_cours' || action === 'compromis_annules'
          ? 'compromis'
          : baseFilters.affaire,
    offreStatus:
      action === 'offres_en_cours'
        ? 'en_cours'
        : action === 'offres_refusees'
          ? 'refusee'
          : baseFilters.offreStatus,
    compromisStatus:
      action === 'compromis_en_cours'
        ? 'en_cours'
        : action === 'compromis_annules'
          ? 'annule'
          : baseFilters.compromisStatus,
    requestScope:
      action === 'demandes_envoyees'
        ? 'pending_or_in_progress'
        : action === 'correction_attente'
          ? 'waiting_correction'
          : baseFilters.requestScope,
    mandat:
      action === 'mandat_diffuse' || action === 'mandat_non_diffuse' || action === 'mandat_valide' || action === 'mandat_non_valide'
        ? withMandatFilterValue
        : action === 'sans_mandat'
          ? withoutMandatFilterValue
          : baseFilters.mandat,
    validationDiffusion:
      action === 'mandat_valide'
        ? '__validated__'
        : action === 'mandat_non_valide'
          ? '__not_validated__'
          : baseFilters.validationDiffusion,
    diffusable:
      action === 'mandat_diffuse'
        ? 'diffusable'
        : action === 'mandat_non_diffuse'
          ? 'non_diffusable'
          : baseFilters.diffusable,
    passerelle:
      action === 'leboncoin'
        ? 'leboncoin'
        : action === 'bienici'
          ? "bien'ici"
          : baseFilters.passerelle,
  }
}

function formatPrice(value: number | string | null | undefined) {
  if (value == null || value === '') return '-'
  const amount = typeof value === 'number' ? value : Number(value)
  if (Number.isNaN(amount)) return String(value)
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(amount)
}

function formatSurface(value: number | string | null | undefined) {
  if (value == null || value === '') return '-'
  if (typeof value === 'string' && /[a-zA-Z²]/.test(value)) return value
  const amount = typeof value === 'number' ? value : Number(String(value).replace(',', '.'))
  if (Number.isNaN(amount)) return String(value)
  return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(amount)} m²`
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

function extractRequestedPriceFromRequest(request: DiffusionRequest | null | undefined) {
  const text = [request?.request_reason, request?.request_comment].filter(Boolean).join('\n')
  const normalizedText = text.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  const match =
    normalizedText.match(/nouveau\s+prix\s+demande\s*:\s*([0-9][0-9\s.,]*)/i) ??
    normalizedText.match(/prix\s+demande\s*:\s*([0-9][0-9\s.,]*)/i)
  return normalizeRequestedPriceInput(match?.[1] ?? '')
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
  return isDiffusableValue(value) ? 'Diffusable' : 'Non diffusable'
}

function isDiffusableValue(value: boolean | number | string | null | undefined) {
  if (value === true || value === 1) return true
  const normalized = String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
  return ['1', 'true', 'oui', 'yes', 'active', 'enabled', 'diffusable'].includes(normalized)
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
  if (normalized === 'demande_annulation_mandat') return 'Demande d annulation de mandat'
  if (normalized === 'demande_diffusion' || !normalized) return 'Demande de validation'
  return 'Demande'
}

function requestCreateLabel(value: string | null | undefined) {
  if (isPriceDropRequest(value)) return 'Demande de baisse de prix'
  if (isMandateCancellationRequest(value)) return 'Demande d annulation de mandat'
  return 'Demande de validation'
}

function requestAcceptedLabel(value: string | null | undefined) {
  if (isPriceDropRequest(value)) return 'Baisse de prix acceptée'
  if (isMandateCancellationRequest(value)) return 'Annulation de mandat acceptée'
  return 'Demande acceptée'
}

function requestRefusedLabel(value: string | null | undefined) {
  if (isPriceDropRequest(value)) return 'Baisse de prix refusee'
  if (isMandateCancellationRequest(value)) return 'Annulation de mandat refusee'
  return 'Demande refusee'
}

function requestPendingLabel(value: string | null | undefined) {
  if (isPriceDropRequest(value)) return 'Baisse de prix envoyée'
  if (isMandateCancellationRequest(value)) return 'Annulation mandat envoyée'
  return 'Demande envoyée'
}

function normalizeRequestType(value: string | null | undefined): BusinessRequestType {
  const normalized = (value ?? '').trim().toLowerCase()
  if (normalized === 'demande_baisse_prix' || normalized === 'baisse_prix' || normalized === 'price_drop') return 'demande_baisse_prix'
  if (
    normalized === 'demande_annulation_mandat' ||
    normalized === 'annulation_mandat' ||
    normalized === 'demande_annulation' ||
    normalized === 'mandate_cancellation'
  ) return 'demande_annulation_mandat'
  return 'demande_diffusion'
}

function isPriceDropRequest(value: string | null | undefined) {
  return normalizeRequestType(value) === 'demande_baisse_prix'
}

function isMandateCancellationRequest(value: string | null | undefined) {
  return normalizeRequestType(value) === 'demande_annulation_mandat'
}

function isValidationRequest(value: string | null | undefined) {
  return normalizeRequestType(value) === 'demande_diffusion'
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

function latestActionRequest(requests: DiffusionRequest[], appDossierId: number, requestType: BusinessRequestType) {
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

function requestActionLabel(request: DiffusionRequest | null, requestType: BusinessRequestType) {
  if (!request) {
    if (requestType === 'demande_baisse_prix') return 'Demande de baisse de prix'
    if (requestType === 'demande_annulation_mandat') return 'Demande annulation mandat'
    return 'Demande de validation'
  }
  if (request.request_status === 'waiting_commercial') return requestType === 'demande_baisse_prix' ? 'Baisse de prix a corriger' : requestType === 'demande_annulation_mandat' ? 'Annulation a corriger' : 'A corriger'
  if (request.request_status === 'refused') return requestType === 'demande_baisse_prix' ? 'Baisse de prix a corriger' : requestType === 'demande_annulation_mandat' ? 'Annulation a corriger' : 'A corriger'
  if (request.request_status === 'in_progress') return requestType === 'demande_baisse_prix' ? 'Baisse de prix en traitement' : requestType === 'demande_annulation_mandat' ? 'Annulation en traitement' : 'Demande en traitement'
  if (request.request_status === 'pending') return requestPendingLabel(requestType)
  if (requestType === 'demande_baisse_prix') return 'Demande de baisse de prix'
  if (requestType === 'demande_annulation_mandat') return 'Demande annulation mandat'
  return 'Demande de validation'
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
  if ((!request || isValidationRequest(request.request_type)) && isValidationApproved(mandat.validation_diffusion_state)) {
    return { label: 'Diffusion', tone: 'ready', opens: 'diffusion' as const }
  }
  if (request?.request_status === 'refused' || request?.request_status === 'waiting_commercial') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Baisse de prix a corriger' : isMandateCancellationRequest(request?.request_type) ? 'Annulation a corriger' : 'A corriger', tone: 'warning', opens: 'request' as const }
  }
  if (request?.request_status === 'pending' || request?.request_status === 'in_progress') {
    return { label: requestPendingLabel(request?.request_type), tone: 'pending', opens: 'request' as const }
  }
  if (request?.request_status === 'accepted' && isPriceDropRequest(request?.request_type)) {
    return { label: 'Baisse de prix acceptée', tone: 'ready', opens: 'request' as const }
  }
  if (request?.request_status === 'accepted' && isMandateCancellationRequest(request?.request_type)) {
    return { label: 'Annulation acceptée', tone: 'ready', opens: 'request' as const }
  }
  return { label: 'Demande de validation', tone: 'idle', opens: 'request' as const }
}

function paulineDiffusionState(mandat: Pick<MandatRecord, 'diffusable' | 'validation_diffusion_state'>, request: DiffusionRequest | null) {
  if ((!request || isValidationRequest(request.request_type)) && isValidationApproved(mandat.validation_diffusion_state)) {
    return { label: 'Acceptée', tone: 'ready', opens: 'diffusion' as const }
  }
  if (request?.request_status === 'waiting_commercial') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Baisse de prix a corriger' : isMandateCancellationRequest(request?.request_type) ? 'Annulation a corriger' : 'A corriger', tone: 'warning', opens: 'request' as const }
  }
  if (request?.request_status === 'refused') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Rejetee' : 'Refusee', tone: 'warning', opens: 'request' as const }
  }
  if (request?.request_status === 'pending' || request?.request_status === 'in_progress') {
    return { label: isPriceDropRequest(request?.request_type) ? 'Baisse de prix a traiter' : isMandateCancellationRequest(request?.request_type) ? 'Annulation a traiter' : 'A traiter', tone: 'pending', opens: 'request' as const }
  }
  if (request?.request_status === 'accepted' && isPriceDropRequest(request?.request_type)) {
    return { label: 'Baisse de prix acceptée', tone: 'ready', opens: 'request' as const }
  }
  if (request?.request_status === 'accepted' && isMandateCancellationRequest(request?.request_type)) {
    return { label: 'Annulation acceptée', tone: 'ready', opens: 'request' as const }
  }
  return { label: 'Aucune demande', tone: 'idle', opens: 'request' as const }
}

function shouldTreatAsPublishableAnomaly(status: string | null | undefined) {
  const normalized = safeText(status).toLowerCase()
  if (!normalized) return true
  if (normalized.includes('offre') || normalized.includes('compromis')) return false
  return true
}

function normalizeMandateLifecycleStatus(value: string | null | undefined) {
  return safeText(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
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
  const status = normalizeMandateLifecycleStatus(item.statut_annonce)
  if (status.includes('vendu') || status.includes('vente') || status.includes('clos') || status.includes('clotur')) return 'Annulé'
  if (status.includes('offre') || status.includes('compromis')) return 'En cours'
  if (status === 'actif' && isMandateEndDateStillValid(item.mandat_date_fin)) return 'En cours'
  return 'Annulé'
}

function mandateLifecycleRowClass(item: Pick<MandatRecord, 'statut_annonce' | 'mandat_date_fin'>) {
  return mandateLifecycleState(item) === 'En cours' ? 'register-row-state-current' : 'register-row-state-cancelled'
}

function hasCancelledMandateExposureAnomaly(mandat: Pick<MandatRecord, 'diffusable' | 'nb_portails_actifs' | 'statut_annonce' | 'mandat_date_fin'>) {
  return mandateLifecycleState(mandat) === 'Annulé' && (((mandat.diffusable ?? '0') === '1') || Boolean(mandat.nb_portails_actifs))
}

type MandateAnomalyType =
  | 'all'
  | 'missing_mandate'
  | 'cancelled_exposed'
  | 'not_published'
  | 'unauthorized_publication'
  | 'gateway_error'

function mandateAnomalyType(mandat: Pick<MandatRecord, 'numero_mandat' | 'diffusable' | 'nb_portails_actifs' | 'has_diffusion_error' | 'statut_annonce' | 'mandat_date_fin'>): MandateAnomalyType {
  const shouldCheckPublishability = shouldTreatAsPublishableAnomaly(mandat.statut_annonce)
  if (!mandat.numero_mandat) return 'missing_mandate'
  if (hasCancelledMandateExposureAnomaly(mandat)) return 'cancelled_exposed'
  if (shouldCheckPublishability && (mandat.diffusable ?? '0') === '1' && !mandat.nb_portails_actifs) return 'not_published'
  if (!hasCancelledMandateExposureAnomaly(mandat) && (mandat.diffusable ?? '0') !== '1' && Boolean(mandat.nb_portails_actifs)) return 'unauthorized_publication'
  if (Boolean(mandat.has_diffusion_error)) return 'gateway_error'
  return 'all'
}

function mandateAnomalyTypeLabel(type: MandateAnomalyType) {
  switch (type) {
    case 'missing_mandate':
      return 'Mandat manquant'
    case 'cancelled_exposed':
      return 'Mandat annulé exposé'
    case 'not_published':
      return 'Diffusable non publié'
    case 'unauthorized_publication':
      return 'Publication non autorisée'
    case 'gateway_error':
      return 'Erreur passerelle'
    default:
      return 'Toutes'
  }
}

function matterportStateLabel(value: string | null | undefined) {
  const normalized = (value ?? '').trim().toLowerCase()
  if (normalized === 'active') return 'Actif'
  if (normalized === 'inactive') return 'Inactif'
  if (normalized === 'mixed') return 'Etat mixte'
  return value || '-'
}

function matterportVisibilityLabel(value: string | null | undefined) {
  const normalized = (value ?? '').trim().toLowerCase()
  if (normalized === 'public') return 'Public'
  if (normalized === 'private') return 'Prive'
  if (normalized === 'unlisted') return 'Non liste'
  if (normalized === 'password') return 'Mot de passe'
  if (normalized === 'mixed') return 'Visibilite mixte'
  return value || '-'
}

function matterportModelLabel(label: string | null | undefined, name: string | null | undefined, single: boolean) {
  const cleanLabel = (label ?? '').trim()
  if (cleanLabel) return cleanLabel
  return single ? 'Visite virtuelle' : (name ?? 'Visite virtuelle')
}

function mandateAnomalyLabels(mandat: Pick<MandatRecord, 'numero_mandat' | 'diffusable' | 'nb_portails_actifs' | 'has_diffusion_error' | 'statut_annonce' | 'mandat_date_fin'>) {
  const shouldCheckPublishability = shouldTreatAsPublishableAnomaly(mandat.statut_annonce)
  const cancelledExposure = hasCancelledMandateExposureAnomaly(mandat)
  const labels = [
    !mandat.numero_mandat ? 'Mandat manquant' : null,
    cancelledExposure ? 'Mandat annulé encore exposé' : null,
    !cancelledExposure && shouldCheckPublishability && (mandat.diffusable ?? '0') === '1' && !mandat.nb_portails_actifs ? 'Diffusable non publié' : null,
    !cancelledExposure && (mandat.diffusable ?? '0') !== '1' && Boolean(mandat.nb_portails_actifs) ? 'Publication active non autorisée' : null,
    Boolean(mandat.has_diffusion_error) ? 'Erreur de passerelle' : null,
  ].filter(Boolean) as string[]
  return {
    primary: labels[0] ?? 'Anomalie à qualifier',
    secondary: [
      ...labels.slice(1),
      ...(cancelledExposure && (mandat.diffusable ?? '0') === '1' ? ['Annonce encore diffusable'] : []),
      ...(cancelledExposure && Boolean(mandat.nb_portails_actifs) ? ['Passerelle encore active'] : []),
    ],
  }
}

function projectIdentityLines(item: Pick<MandatRecord, 'numero_dossier' | 'numero_mandat' | 'type_bien' | 'ville'>) {
  return {
    title: item.numero_dossier ?? '-',
    mandate: item.numero_mandat ? `Mandat ${item.numero_mandat}` : 'Sans mandat',
    context: [propertyTypeLabel(item.type_bien), item.ville].filter((value) => value && value !== '-').join(' · ') || '-',
  }
}

function listingProgressLabel(item: Pick<MandatRecord, 'statut_annonce' | 'numero_mandat' | 'validation_diffusion_state' | 'diffusable' | 'nb_portails_actifs' | 'offre_id' | 'compromis_id' | 'vente_id'>) {
  if ((item.statut_annonce ?? '').trim() === 'Estimation') return 'Estimation en cours'
  if (item.vente_id) return 'Vendu'
  if (item.compromis_id) return 'Compromis en cours'
  if (item.offre_id) return 'Offre en cours'
  if (!item.numero_mandat) return 'Annonce créée · mandat manquant'
  if (!isValidationApproved(item.validation_diffusion_state)) return 'Mandat à valider'
  if ((item.diffusable ?? '0') === '1' && Boolean(item.nb_portails_actifs)) return 'Diffusé'
  if ((item.diffusable ?? '0') === '1') return 'Mandat validé · non diffusé'
  return 'Mandat validé · diffusion à ouvrir'
}

type ActionButtonTypeTone = 'validation' | 'price-drop' | 'cancellation' | 'diffusion' | 'hektor'
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

function buildActionButtonParts(type: 'validation' | 'price_drop' | 'cancellation' | 'diffusion', stateLabel: string) {
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
  if (type === 'cancellation') {
    return {
      typeLabel: 'Annulation mandat',
      stateLabel,
      typeTone: 'cancellation' as ActionButtonTypeTone,
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
  const isExternal = props.typeTone === 'hektor'
  return (
    <button className={`action-menu-item action-menu-type-${props.typeTone} action-menu-state-${props.stateTone}`} type={props.type} onClick={props.onClick}>
      <span className={`action-menu-item-icon action-menu-item-icon-${props.typeTone}`} aria-hidden="true">
        <ActionGlyph typeTone={props.typeTone} stateTone={props.stateTone} />
      </span>
      <span className="action-menu-item-main">
        <span className="action-menu-item-label">{props.typeLabel}</span>
        {props.helperText ? <span className="action-menu-item-helper">{props.helperText}</span> : null}
      </span>
      <span className="action-menu-item-state">{props.stateLabel}</span>
      <span className={`action-menu-item-arrow ${isExternal ? 'is-external' : ''}`} aria-hidden="true">
        {isExternal ? <ActionExternalGlyph /> : <ActionChevronGlyph />}
      </span>
    </button>
  )
}

function ActionGlyph(props: { typeTone: ActionButtonTypeTone; stateTone: ActionButtonStateTone }) {
  if (props.stateTone === 'correction' || props.stateTone === 'rejected') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3L21 19H3L12 3Z" />
        <path d="M12 9V13" />
        <path d="M12 17H12.01" />
      </svg>
    )
  }
  if (props.typeTone === 'diffusion') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 3L10 14" />
        <path d="M21 3L14 21L10 14L3 10L21 3Z" />
      </svg>
    )
  }
  if (props.typeTone === 'price-drop') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 7L10 13L14 9L20 15" />
        <path d="M14 15H20V9" />
      </svg>
    )
  }
  if (props.typeTone === 'hektor') {
    return (
      <svg viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="11" fill="currentColor" opacity="0.14" />
        <path d="M8 6H11V10.2H13V6H16V18H13V13.3H11V18H8V6Z" fill="currentColor" />
      </svg>
    )
  }
  if (props.typeTone === 'cancellation') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 3H16L19 6V21H5V3H8Z" />
        <path d="M15 3V7H19" />
        <path d="M9 13H15" />
        <path d="M10 17H14" />
      </svg>
    )
  }
  if (props.typeTone === 'validation') {
    if (props.stateTone === 'accepted') {
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8 3H16L19 6V21H5V3H8Z" />
          <path d="M15 3V7H19" />
          <path d="M8.5 13L11 15.5L16 10.5" />
        </svg>
      )
    }
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 3H16L19 6V21H5V3H8Z" />
        <path d="M15 3V7H19" />
        <path d="M9 12H13" />
        <path d="M9 16H12" />
        <circle cx="17" cy="16" r="2.5" />
        <path d="M17 14.8V16.1" />
        <path d="M17 17.2H17.01" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6L9 17L4 12" />
    </svg>
  )
}

function ActionChevronGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 6L15 12L9 18" />
    </svg>
  )
}

function ActionExternalGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 5H19V10" />
      <path d="M10 14L19 5" />
      <path d="M19 14V19H5V5H10" />
    </svg>
  )
}

function actionMenuHelperText(typeLabel: string, stateLabel: string) {
  if (typeLabel === 'Hektor') return 'Acceder au cockpit Hektor'
  if (stateLabel === 'Ajouter') {
    if (typeLabel === 'Valider') return 'Creer une demande de validation du mandat'
    if (typeLabel === 'Baisse de prix') return 'Creer une demande de baisse de prix'
    if (typeLabel === 'Annulation mandat') return 'Creer une demande d annulation de mandat'
    return 'Creer une nouvelle demande'
  }
  if (stateLabel === 'Corriger') return 'Reprendre la demande apres retour Pauline'
  if (stateLabel === 'A traiter') return 'Ouvrir la demande a traiter dans le suivi'
  if (stateLabel === 'Envoyee' || stateLabel === 'En cours') return 'Consulter la demande deja envoyee'
  if (stateLabel === 'Modifier') return 'Ajuster les reglages et portails de diffusion'
  if (stateLabel === 'Refusee' || stateLabel === 'Rejetee') return 'Consulter le refus et le motif'
  if (stateLabel === 'Acceptée') return 'Consulter la demande acceptee'
  if (typeLabel === 'Diffusion') return "Diffuser l'annonce sur les portails"
  if (typeLabel === 'Baisse de prix') return 'Proposer une baisse du prix'
  if (typeLabel === 'Valider') return 'Confirmer et activer le mandat'
  return 'Ouvrir cette action'
}

function actionTriggerToneFromRequest(request: DiffusionRequest | null | undefined): ActionTriggerTone {
  const status = request?.request_status ?? null
  if (status === 'pending' || status === 'in_progress') return 'creation'
  if (status === 'waiting_commercial') return 'correction'
  if (status === 'refused') return 'rejected'
  return 'neutral'
}

type MandatActionSource = {
  app_dossier_id: number
  hektor_annonce_id: string | number
  diffusable?: string | null
  validation_diffusion_state?: string | null
  numero_mandat?: string | null
}

type MandatActionItemModel = {
  key: string
  typeLabel: string
  stateLabel: string
  typeTone: ActionButtonTypeTone
  stateTone: ActionButtonStateTone
  onClick: (event: { stopPropagation(): void }) => void
}

function buildMandatActionModel(input: {
  mandat: MandatActionSource
  role: 'nego' | 'pauline'
  requests: DiffusionRequest[]
  currentRequest?: DiffusionRequest | null
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
  onOpenDiffusionModal: (id: number) => void
  onBeforeAction?: () => void
}): { hasMandat: boolean; triggerTone: ActionTriggerTone; items: MandatActionItemModel[] } {
  const hasMandat = Boolean((input.mandat.numero_mandat ?? '').trim())
  const activeDiffusionRequest = latestActionRequest(input.requests, input.mandat.app_dossier_id, 'demande_diffusion')
  const activePriceDropRequest = latestActionRequest(input.requests, input.mandat.app_dossier_id, 'demande_baisse_prix')
  const activeCancellationRequest = latestActionRequest(input.requests, input.mandat.app_dossier_id, 'demande_annulation_mandat')
  const hasValidationApproval = isValidationApproved(input.mandat.validation_diffusion_state)
  const canOpenDiffusion = hasValidationApproval
  const canRequestPriceDrop = hasValidationApproval || Boolean(activePriceDropRequest)
  const canRequestCancellation = hasValidationApproval || Boolean(activeCancellationRequest)
  const rowRequestType = normalizeRequestType(input.currentRequest?.request_type)
  const run = (event: { stopPropagation(): void }, action: () => void) => {
    event.stopPropagation()
    input.onBeforeAction?.()
    action()
  }
  const triggerTone = input.role === 'pauline'
    ? actionTriggerToneFromRequest(input.currentRequest)
    : actionTriggerToneFromRequest(activeDiffusionRequest) !== 'neutral'
      ? actionTriggerToneFromRequest(activeDiffusionRequest)
      : actionTriggerToneFromRequest(activePriceDropRequest) !== 'neutral'
        ? actionTriggerToneFromRequest(activePriceDropRequest)
        : actionTriggerToneFromRequest(activeCancellationRequest)

  if (!hasMandat) return { hasMandat, triggerTone, items: [] }

  const paulineLabel = input.currentRequest ? paulineActionLabel(input.currentRequest) : null
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
  const cancellationLabel = (() => {
    const label = requestActionLabel(activeCancellationRequest, 'demande_annulation_mandat')
    if (label === 'Demande annulation mandat') return 'Ajouter'
    if (label === 'Annulation a corriger') return 'Corriger'
    if (label === 'Annulation mandat envoyée') return 'Envoyée'
    if (label === 'Annulation en traitement') return 'En cours'
    return label
  })()
  const paulineParts = input.currentRequest
    ? buildActionButtonParts(
        rowRequestType === 'demande_baisse_prix' ? 'price_drop' : rowRequestType === 'demande_annulation_mandat' ? 'cancellation' : 'validation',
        paulineLabel ?? 'A traiter',
      )
    : null
  const diffusionParts = buildActionButtonParts('diffusion', 'Modifier')
  const validationParts = buildActionButtonParts('validation', validationLabel)
  const priceDropParts = buildActionButtonParts('price_drop', priceDropLabel)
  const cancellationParts = buildActionButtonParts('cancellation', cancellationLabel)

  const items: MandatActionItemModel[] =
    input.role === 'pauline' && input.currentRequest && paulineParts
      ? [
          {
            key: `${input.currentRequest.id}-pauline`,
            ...paulineParts,
            onClick: (event) => run(event, () => input.onOpenRequestModal(input.mandat.app_dossier_id, input.role, rowRequestType)),
          },
          {
            key: 'open-hektor',
            typeLabel: 'Hektor',
            stateLabel: 'Ouvrir',
            typeTone: 'hektor',
            stateTone: 'diffusion',
            onClick: (event) => run(event, () => openHektorAnnonce(String(input.mandat.hektor_annonce_id))),
          },
        ]
      : [
          ...(canOpenDiffusion
            ? [
                {
                  key: 'diffusion',
                  ...diffusionParts,
                  onClick: (event: { stopPropagation(): void }) => run(event, () => input.onOpenDiffusionModal(input.mandat.app_dossier_id)),
                },
              ]
            : [
                {
                  key: 'validation',
                  ...validationParts,
                  onClick: (event: { stopPropagation(): void }) => run(event, () => input.onOpenRequestModal(input.mandat.app_dossier_id, input.role, 'demande_diffusion')),
                },
              ]),
          ...(canRequestPriceDrop
            ? [
                {
                  key: 'price-drop',
                  ...priceDropParts,
                  onClick: (event: { stopPropagation(): void }) => run(event, () => input.onOpenRequestModal(input.mandat.app_dossier_id, input.role, 'demande_baisse_prix')),
                },
              ]
            : []),
          ...(canRequestCancellation
            ? [
                {
                  key: 'mandate-cancellation',
                  ...cancellationParts,
                  onClick: (event: { stopPropagation(): void }) => run(event, () => input.onOpenRequestModal(input.mandat.app_dossier_id, input.role, 'demande_annulation_mandat')),
                },
              ]
            : []),
          {
            key: 'open-hektor',
            typeLabel: 'Hektor',
            stateLabel: 'Ouvrir',
            typeTone: 'hektor',
            stateTone: 'diffusion',
            onClick: (event) => run(event, () => openHektorAnnonce(String(input.mandat.hektor_annonce_id))),
          },
        ]

  return { hasMandat, triggerTone, items }
}

function requestLastMessage(request: DiffusionRequest | null) {
  if (!request) return 'Aucune demande'
  return request.processing_comment || request.admin_response || request.refusal_reason || request.request_reason || request.request_comment || 'Sans message'
}

function requestNumberLabel(request: DiffusionRequest | null | undefined) {
  const value = safeText(request?.id)
  if (!value) return '-'
  if (value.startsWith('local-')) return value.replace(/^local-/, '')
  return value.length > 8 ? value.slice(0, 8) : value
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

function buildHektorMandatPrixUrl(hektorAnnonceId: number | string | null | undefined) {
  if (hektorAnnonceId == null || hektorAnnonceId === '') return null
  const id = String(hektorAnnonceId).trim()
  if (!id) return null
  return `https://groupe-gti-immobilier.la-boite-immo.com/admin/?page=/mes-biens/mon-bien/mandat-prix&id=${encodeURIComponent(id)}`
}

function buildAppointmentAnnonceUrl(
  dossier: Pick<Dossier, 'hektor_annonce_id'> | Pick<MandatRecord, 'hektor_annonce_id'> | null | undefined,
  detail?: DossierDetailPayload | null,
) {
  const explicit = safeText(detail?.appointment_public_url)
  if (explicit) return explicit
  const annonceId = dossier?.hektor_annonce_id
  const normalizedAnnonceId = annonceId == null ? '' : String(annonceId).trim()
  if (!normalizedAnnonceId) return null
  const publicBase = safeText(import.meta.env.VITE_APPOINTMENT_PUBLIC_BASE_URL)
  const root = publicBase || (typeof window !== 'undefined' ? window.location.origin : '')
  if (!root) return null
  const normalizedRoot = root.replace(/\/+$/, '')
  const token = safeText(detail?.appointment_public_token)
  if (token) return `${normalizedRoot}/rdv/annonce/${encodeURIComponent(token)}`
  return `${normalizedRoot}/rdv/annonce/${encodeURIComponent(normalizedAnnonceId)}`
}

type AppointmentRequestEntry = {
  id?: string | number | null
  status?: string | null
  client_nom?: string | null
  client_email?: string | null
  client_telephone?: string | null
  requested_start_at?: string | null
  requested_end_at?: string | null
  message?: string | null
  created_at?: string | null
}

type AppointmentRequestEventEntry = {
  id?: string | number | null
  event_type?: string | null
  event_label?: string | null
  actor_name?: string | null
  created_at?: string | null
  payload_json?: string | null
}

function parseAppointmentRequests(detail: DossierDetailPayload | null | undefined) {
  return parseJson<AppointmentRequestEntry[]>(detail?.appointment_requests_json ?? '[]', [])
}

function parseAppointmentRequestEvents(detail: DossierDetailPayload | null | undefined) {
  return parseJson<AppointmentRequestEventEntry[]>(detail?.appointment_request_events_json ?? '[]', [])
}

function appointmentStatusLabel(value: string | null | undefined) {
  const normalized = safeText(value).toLowerCase()
  if (!normalized) return 'En attente'
  if (normalized === 'pending') return 'En attente'
  if (normalized === 'contacted') return 'Client recontacte'
  if (normalized === 'confirmed') return 'Confirme'
  if (normalized === 'rescheduled') return 'A redecaler'
  if (normalized === 'cancelled' || normalized === 'canceled') return 'Annule'
  return value ?? 'En attente'
}

function buildAppRequestUrl(
  appDossierId: number | null | undefined,
  role: 'nego' | 'pauline' = 'nego',
  requestType?: BusinessRequestType | null,
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
  const isCancellation = input.requestType === 'demande_annulation_mandat'
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
    isPriceDrop ? 'demande_baisse_prix' : isCancellation ? 'demande_annulation_mandat' : 'demande_diffusion',
  )

  const subject = input.status === 'accepted'
    ? `${isPriceDrop ? 'Baisse de prix acceptee' : isCancellation ? 'Annulation mandat acceptee' : 'Validation acceptee'} · ${dossierLabel}`
    : `${isPriceDrop ? 'Baisse de prix refusee' : isCancellation ? 'Annulation mandat refusee' : 'Validation refusee'} · ${dossierLabel}`

  const bodyLines = input.status === 'accepted'
    ? [
        isPriceDrop ? 'Demande de baisse de prix acceptee.' : isCancellation ? 'Demande d annulation de mandat acceptee.' : 'Demande de validation acceptee.',
        '',
        `Dossier : ${dossierLabel}`,
        `Statut : ${isPriceDrop ? 'Baisse de prix acceptee' : isCancellation ? 'Annulation mandat acceptee' : 'Validation acceptee'}`,
        trimmedResponse ? `Commentaire : ${trimmedResponse}` : null,
        '',
        `Action : ${isPriceDrop ? "Ouvrir l'application pour suivre la demande de prix." : isCancellation ? "Ouvrir l'application pour suivre la demande d'annulation de mandat." : "Ouvrir l'application pour suivre la validation."}`,
        appRequestUrl ? `Application : ${appRequestUrl}` : null,
      ]
        .filter(Boolean) as string[]
    : [
        isPriceDrop ? 'Demande de baisse de prix refusée.' : isCancellation ? 'Demande d annulation de mandat refusee.' : 'Demande de validation refusee.',
        '',
        `Dossier : ${dossierLabel}`,
        trimmedRefusalReason ? `Motif : ${trimmedRefusalReason}` : 'Motif : non précisé',
        trimmedResponse ? `Commentaire : ${trimmedResponse}` : null,
        '',
        `Action : ${isPriceDrop ? "Completer l'avenant puis renvoyer la demande dans l'application." : isCancellation ? "Corriger ou completer la demande d'annulation dans l'application." : "Corriger le dossier puis renvoyer la demande de validation dans l'application."}`,
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
    ? (isPriceDrop ? 'Baisse de prix acceptee' : isCancellation ? 'Annulation mandat acceptee' : 'Validation acceptee')
    : (trimmedRefusalReason || (isPriceDrop ? 'Baisse de prix refusee' : isCancellation ? 'Annulation mandat refusee' : 'Validation refusee'))

  const commentBlock = trimmedResponse
    ? `<div style="padding:14px 16px;border-radius:14px;background:#fff;border:1px solid #eadfce;margin:0 0 16px 0;">
         <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;color:#8b6b4a;margin-bottom:6px;">Commentaire</div>
         <div style="font-size:14px;line-height:1.55;color:#27313a;">${trimmedResponse}</div>
       </div>`
    : ''

  const actionLabel = input.status === 'accepted'
    ? (isPriceDrop ? "Ouvrir l'application pour suivre la demande de prix." : isCancellation ? "Ouvrir l'application pour suivre la demande d'annulation de mandat." : "Ouvrir l'application pour suivre la validation.")
    : (isPriceDrop ? "Completer l'avenant puis renvoyer la demande dans l'application." : isCancellation ? "Corriger ou completer la demande d'annulation dans l'application." : "Corriger le dossier puis renvoyer la demande de validation dans l'application.")

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

function buildRequestHistoryForType(requests: DiffusionRequest[], events: DiffusionRequestEvent[], requestType: BusinessRequestType) {
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

function buildRequestMessagesForType(requests: DiffusionRequest[], events: DiffusionRequestEvent[], requestType: BusinessRequestType) {
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

function openHektorMandatPrix(hektorAnnonceId: number | string | null | undefined) {
  const url = buildHektorMandatPrixUrl(hektorAnnonceId)
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

function isConsoleJobActive(job: Pick<ConsoleJob, 'status'>) {
  return job.status === 'pending' || job.status === 'running'
}

function consoleJobShortId(job: Pick<ConsoleJob, 'id'>) {
  return job.id.slice(0, 8)
}

function hektorActionJobTitle(job: ConsoleJob) {
  const payload = job.payload_json ?? {}
  const result = job.result_json ?? {}
  const documentName = typeof payload.document_name === 'string' && payload.document_name.trim()
    ? payload.document_name.trim()
    : typeof payload.original_filename === 'string' && payload.original_filename.trim()
      ? payload.original_filename.trim()
      : typeof payload.document_label === 'string' && payload.document_label.trim()
        ? payload.document_label.trim()
        : null
  if (job.job_type === 'delete_hektor_annonce') {
    return `Suppression ${job.hektor_annonce_id ?? payload.hektor_annonce_id ?? ''}`.trim()
  }
  if (job.job_type === 'delete_document_from_hektor') {
    return documentName ? `Suppression ${documentName}` : 'Suppression document'
  }
  if (job.job_type === 'upload_document_to_hektor') {
    return documentName ? `Ajout ${documentName}` : 'Ajout document Hektor'
  }
  if (job.job_type === 'prepare_document_cloud') {
    return documentName ? `Preparation ${documentName}` : 'Preparation document'
  }
  if (job.job_type === 'update_hektor_annonce_fields') {
    return `Modification ${job.hektor_annonce_id ?? payload.hektor_annonce_id ?? ''}`.trim()
  }
  if (job.job_type === 'create_hektor_mandant_contact' || job.job_type === 'update_hektor_mandant_contact' || job.job_type === 'link_hektor_mandant') {
    const contact = typeof payload.last_name === 'string' && payload.last_name.trim() ? payload.last_name.trim() : null
    return contact ? `Mandant ${contact}` : 'Mandant Hektor'
  }
  const folder = typeof result.folder_number === 'string' ? result.folder_number : null
  const title = typeof payload.title === 'string' && payload.title.trim() ? payload.title.trim() : null
  return folder ? `Creation ${folder}` : title ? `Creation ${title}` : 'Creation annonce Hektor'
}

function hektorActionJobLabel(job: ConsoleJob) {
  if (job.job_type === 'delete_hektor_annonce') return 'Suppression en cours'
  if (job.job_type === 'delete_document_from_hektor') return 'Suppression document'
  if (job.job_type === 'upload_document_to_hektor') return 'Ajout document'
  if (job.job_type === 'prepare_document_cloud') return 'Preparation document'
  if (job.job_type === 'update_hektor_annonce_fields') return 'Modification en cours'
  if (job.job_type === 'create_hektor_mandant_contact' || job.job_type === 'update_hektor_mandant_contact' || job.job_type === 'link_hektor_mandant') return 'Mandant en cours'
  return 'Creation en cours'
}

function hektorActionJobTone(job: ConsoleJob) {
  if (job.job_type === 'delete_hektor_annonce' || job.job_type === 'delete_document_from_hektor') return 'delete'
  if (job.job_type === 'update_hektor_annonce_fields') return 'update'
  if (job.job_type === 'create_hektor_mandant_contact' || job.job_type === 'update_hektor_mandant_contact' || job.job_type === 'link_hektor_mandant') return 'contact'
  if (job.job_type === 'upload_document_to_hektor' || job.job_type === 'prepare_document_cloud') return 'document'
  return 'create'
}

function hektorActionJobDetail(job: ConsoleJob) {
  const payload = job.payload_json ?? {}
  const result = job.result_json ?? {}
  const agency = typeof payload.agence_nom === 'string' ? payload.agence_nom : null
  const negotiator = typeof payload.hektor_user_label === 'string' ? payload.hektor_user_label : null
  const folder = typeof result.folder_number === 'string' ? result.folder_number : null
  if (job.status === 'error') return job.error_message || 'Action Hektor en erreur'
  if (job.job_type === 'upload_document_to_hektor') return 'Document envoye au PC serveur'
  if (job.job_type === 'prepare_document_cloud') return 'Mise en cloud demandee'
  if (job.job_type === 'delete_document_from_hektor') return 'Suppression Hektor demandee'
  if (job.job_type === 'update_hektor_annonce_fields') return 'Modification puis resynchronisation'
  if (job.job_type === 'create_hektor_mandant_contact' || job.job_type === 'link_hektor_mandant') return 'Association puis resynchronisation'
  if (job.job_type === 'update_hektor_mandant_contact') return 'Modification puis resynchronisation'
  if (folder) return `${folder} synchronise dans l'app`
  return [negotiator, agency].filter(Boolean).join(' - ') || `Job ${consoleJobShortId(job)}`
}

function isPrimaryHektorActionJob(job: ConsoleJob) {
  return job.job_type !== 'refresh_console_data'
}

function hektorJobSyncJobId(job: ConsoleJob) {
  const syncJob = job.result_json?.sync_job
  if (!syncJob || typeof syncJob !== 'object') return null
  const id = (syncJob as { id?: unknown; job_id?: unknown; sync_job_id?: unknown }).id
    ?? (syncJob as { job_id?: unknown }).job_id
    ?? (syncJob as { sync_job_id?: unknown }).sync_job_id
  return typeof id === 'string' && id.trim() ? id : null
}

function hektorActionRelatedJobIds(jobs: ConsoleJob[]) {
  return Array.from(new Set(jobs.flatMap((job) => [job.id, hektorJobSyncJobId(job)].filter((id): id is string => Boolean(id)))))
}

function hektorCreatedAnnonceId(job: ConsoleJob) {
  const resultId = job.result_json?.hektor_annonce_id
  const payloadId = job.payload_json?.hektor_annonce_id
  const source = resultId ?? job.hektor_annonce_id ?? payloadId
  const value = String(source ?? '').trim()
  return value || null
}

function hektorActionProgress(job: ConsoleJob, syncJob: ConsoleJob | null, appDossier?: Dossier | null) {
  if (job.status === 'error' || syncJob?.status === 'error') return 'error'
  const syncJobId = hektorJobSyncJobId(job)
  if (syncJobId && syncJob?.status !== 'done') {
    if (job.status === 'done') return 'syncing'
    if (job.status === 'running') return 'creating'
    return 'queued'
  }
  if (syncJobId && syncJob?.status === 'done') return 'available'
  if (appDossier) return 'available'
  if (job.job_type !== 'create_hektor_draft_annonce' && job.status === 'done') return 'available'
  if (job.status === 'done') return 'syncing'
  if (job.status === 'running') return 'creating'
  return 'queued'
}

function hektorActionProgressLabel(progress: ReturnType<typeof hektorActionProgress>, job?: ConsoleJob) {
  if (progress === 'available') {
    if (!job || job.job_type === 'create_hektor_draft_annonce') return 'Annonce disponible'
    if (job.job_type === 'update_hektor_annonce_fields') return 'Modification terminee'
    if (job.job_type === 'create_hektor_mandant_contact' || job.job_type === 'link_hektor_mandant') return 'Mandant synchronise'
    if (job.job_type === 'update_hektor_mandant_contact') return 'Mandant modifie'
    if (job.job_type === 'upload_document_to_hektor') return 'Document ajoute'
    if (job.job_type === 'prepare_document_cloud') return 'Document pret'
    if (job.job_type === 'delete_document_from_hektor') return 'Document supprime'
    if (job.job_type === 'delete_hektor_annonce') return 'Suppression terminee'
    return 'Action terminee'
  }
  if (progress === 'syncing') {
    if (!job || job.job_type === 'create_hektor_draft_annonce') return "Ajout dans l'app"
    if (job.job_type === 'update_hektor_annonce_fields' || job.job_type === 'update_hektor_mandant_contact') return "Mise a jour de l'app"
    if (job.job_type === 'create_hektor_mandant_contact' || job.job_type === 'link_hektor_mandant') return 'Synchronisation mandant'
    if (job.job_type === 'upload_document_to_hektor' || job.job_type === 'prepare_document_cloud' || job.job_type === 'delete_document_from_hektor') return 'Synchronisation document'
    return "Mise a jour de l'app"
  }
  if (progress === 'creating') return job && job.job_type !== 'create_hektor_draft_annonce' ? 'Commande Hektor' : 'Creation Hektor'
  if (progress === 'error') return 'Action a verifier'
  return 'En attente'
}

function hektorActionWaitingLabel(job: ConsoleJob) {
  if (job.job_type === 'update_hektor_mandant_contact') return 'Hektor a modifie le mandant. Mise a jour de l app en cours...'
  if (job.job_type === 'update_hektor_annonce_fields') return 'Hektor a modifie l annonce. Mise a jour de l app en cours...'
  if (job.job_type === 'create_hektor_mandant_contact' || job.job_type === 'link_hektor_mandant') return 'Hektor a mis a jour le mandant. Synchronisation app en cours...'
  if (job.job_type === 'create_hektor_draft_annonce') return 'Annonce creee dans Hektor. Ajout dans l app en cours...'
  if (job.job_type === 'upload_document_to_hektor') return 'Document ajoute dans Hektor. Synchronisation app en cours...'
  if (job.job_type === 'delete_document_from_hektor') return 'Document supprime dans Hektor. Mise a jour app en cours...'
  return 'Commande Hektor terminee. Mise a jour de l app en cours...'
}

function HektorActionStatusPopup(props: {
  jobs: ConsoleJob[]
  linkedDossiers: Record<string, Dossier>
  onDismiss: (jobId: string) => void
  onOpenAppDossier: (job: ConsoleJob) => void
}) {
  const [openButtonReadyJobId, setOpenButtonReadyJobId] = useState<string | null>(null)
  const primaryJobs = props.jobs.filter(isPrimaryHektorActionJob).slice(0, 3)
  const jobsById = new Map(props.jobs.map((job) => [job.id, job]))
  const mainJob = primaryJobs[0] ?? null
  const mainSyncJobId = mainJob ? hektorJobSyncJobId(mainJob) : null
  const mainSyncJob = mainSyncJobId ? jobsById.get(mainSyncJobId) ?? null : null
  const mainAnnonceId = mainJob ? hektorCreatedAnnonceId(mainJob) : null
  const mainDossier = mainAnnonceId ? props.linkedDossiers[mainAnnonceId] : null
  const mainProgress = mainJob ? hektorActionProgress(mainJob, mainSyncJob, mainDossier) : 'queued'
  const isAvailable = mainProgress === 'available'
  const isError = mainProgress === 'error'
  const isWaitingForAppSync = Boolean(mainJob && mainProgress === 'syncing' && mainJob.status === 'done')
  const canShowOpenDelay = Boolean(mainJob && isAvailable && mainJob.job_type !== 'delete_hektor_annonce' && openButtonReadyJobId !== mainJob.id)
  const canOpenApp = Boolean(mainJob && isAvailable && mainJob.job_type !== 'delete_hektor_annonce' && openButtonReadyJobId === mainJob.id)
  const canOpenHektor = Boolean(mainJob && mainAnnonceId && mainJob.job_type !== 'delete_hektor_annonce')

  useEffect(() => {
    setOpenButtonReadyJobId(null)
    if (!mainJob || !isAvailable || mainJob.job_type === 'delete_hektor_annonce') return
    const timer = window.setTimeout(() => setOpenButtonReadyJobId(mainJob.id), 1200)
    return () => window.clearTimeout(timer)
  }, [isAvailable, mainJob?.id, mainJob?.job_type])

  if (!mainJob) return null

  return (
    <aside className={`hektor-action-popup hektor-action-popup-${mainProgress}`} aria-live="polite">
      <div className="hektor-action-popup-head">
        <span className="hektor-action-popup-icon" aria-hidden="true">{isError ? '!' : isAvailable ? 'OK' : 'H'}</span>
        <div>
          <p className="hektor-action-popup-eyebrow">Suivi Hektor</p>
          <h3>{hektorActionProgressLabel(mainProgress, mainJob)}</h3>
        </div>
        <button className="hektor-action-popup-close" type="button" onClick={() => props.onDismiss(mainJob.id)} aria-label="Masquer le suivi">x</button>
      </div>

      <div className="hektor-action-popup-main">
        <strong>{hektorActionJobTitle(mainJob)}</strong>
        <span>{isWaitingForAppSync ? hektorActionWaitingLabel(mainJob) : canShowOpenDelay ? "Tout est synchronise. Patientez, preparation de l'ouverture..." : hektorActionJobDetail(mainJob)}</span>
      </div>

      <div className="hektor-action-steps">
        <span className={mainJob.status === 'done' ? 'is-done' : mainJob.status === 'running' ? 'is-current' : isError ? 'is-error' : ''}>
          <i aria-hidden="true" /> Hektor
        </span>
        <span className={isAvailable ? 'is-done' : mainProgress === 'syncing' ? 'is-current' : mainSyncJob?.status === 'error' ? 'is-error' : ''}>
          <i aria-hidden="true" /> App
        </span>
      </div>

      <div className="hektor-action-popup-actions">
        {canOpenApp ? (
          <button className="ghost-button button-primary" type="button" onClick={() => props.onOpenAppDossier(mainJob)}>Ouvrir l'annonce</button>
        ) : null}
        {isWaitingForAppSync ? (
          <button className="ghost-button button-primary is-waiting" type="button" disabled>Actualisation app...</button>
        ) : null}
        {canShowOpenDelay ? (
          <button className="ghost-button button-primary is-waiting hektor-action-wait-button" type="button" disabled>
            <span className="hektor-action-wait-spinner" aria-hidden="true" />
            Patientez...
          </button>
        ) : null}
        {canOpenHektor && mainAnnonceId ? <button className="ghost-button" type="button" onClick={() => openHektorAnnonce(mainAnnonceId)}>Hektor</button> : null}
      </div>

      {primaryJobs.length > 1 ? (
        <div className="hektor-action-popup-queue">
          {primaryJobs.slice(1).map((job) => (
            <button key={job.id} type="button" onClick={() => props.onDismiss(job.id)}>
              <span>{hektorActionJobLabel(job)}</span>
              <strong>{hektorActionJobTitle(job)}</strong>
            </button>
          ))}
        </div>
      ) : null}
    </aside>
  )
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

function screenContextLabel(screen: Screen) {
  if (screen === 'annonces') return 'Vue stock'
  if (screen === 'mandats') return 'Vue mandat'
  if (screen === 'estimations') return 'Estimations'
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

function mandateRegisterSourceBadge(item: MandatRecord) {
  return (item.register_source_kind ?? '').trim().toLowerCase() === 'historique' ? 'Historique' : null
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
  '31': 'Loft',
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

function summarizeApplyFailures(failed: Array<Record<string, unknown>> | undefined) {
  const details = (failed ?? [])
    .map((item) => {
      const portal = safeText(item.portal_key) || safeText(item.broadcast_id) || 'passerelle'
      const error = safeText(item.error)
      return error ? `${portal}: ${error}` : portal
    })
    .filter(Boolean)
  return details.join(' | ')
}

function portalBrandLabel(value: string | null | undefined) {
  const normalized = normalizePortalToken(value)
  if (normalized.includes('leboncoin') || normalized.includes('lbc')) return 'Leboncoin'
  if (normalized.includes('bienici') || normalized.includes("bien'ici")) return "Bien'ici"
  if (normalized.includes('gti') || normalized.includes('site')) return 'GTI'
  if (normalized.includes('seloger')) return 'SeLoger'
  return safeText(value) || 'Passerelle'
}

function portalBrandClass(value: string | null | undefined) {
  const normalized = normalizePortalToken(value)
  if (normalized.includes('leboncoin') || normalized.includes('lbc')) return 'is-leboncoin'
  if (normalized.includes('bienici') || normalized.includes("bien'ici")) return 'is-bienici'
  if (normalized.includes('gti') || normalized.includes('site')) return 'is-gti'
  if (normalized.includes('seloger')) return 'is-seloger'
  return 'is-generic'
}

function portalSummaryPriority(value: string | null | undefined) {
  const normalized = normalizePortalToken(value).replace(/\s+/g, '')
  if (normalized.includes('leboncoin') || normalized.includes('lbc')) return 0
  if (normalized.includes('bienici')) return 1
  if (normalized.includes('gti') || normalized.includes('sitegti')) return 2
  return 3
}

function sortSummaryPortals(values: string[]) {
  return [...values].sort((left, right) => {
    const priorityGap = portalSummaryPriority(left) - portalSummaryPriority(right)
    if (priorityGap !== 0) return priorityGap
    return left.localeCompare(right, 'fr', { sensitivity: 'base' })
  })
}

type DetailTabKey = 'summary' | 'commercial' | 'mandate' | 'diffusion' | 'content' | 'history'
type DetailIconKey = 'summary' | 'commercial' | 'mandate' | 'diffusion' | 'content' | 'history' | 'virtual' | 'location' | 'visibility' | 'priority' | 'alert' | 'actions' | 'photo' | 'contact' | 'hektor'

const detailTabs: Array<{ key: DetailTabKey; label: string; short: string; icon: DetailIconKey }> = [
  { key: 'summary', label: 'Synthese', short: '01', icon: 'summary' },
  { key: 'commercial', label: 'Commercialisation', short: '02', icon: 'commercial' },
  { key: 'mandate', label: 'Mandat & contacts', short: '03', icon: 'mandate' },
  { key: 'diffusion', label: 'Diffusion', short: '04', icon: 'diffusion' },
  { key: 'content', label: 'Contenu annonce', short: '05', icon: 'content' },
  { key: 'history', label: 'Historique', short: '06', icon: 'history' },
]

function DetailIcon({ type }: { type: DetailIconKey }) {
  if (type === 'commercial') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M4 19V7" />
        <path d="M4 15L9 10L13 14L20 6" />
        <path d="M16 6H20V10" />
      </svg>
    )
  }
  if (type === 'mandate') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M8 3H16L19 6V21H5V3H8Z" />
        <path d="M15 3V7H19" />
        <path d="M8 11H16" />
        <path d="M8 15H14" />
      </svg>
    )
  }
  if (type === 'diffusion') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M21 4L10.5 14.5" />
        <path d="M21 4L15.5 21L10.5 14.5L3 10.5L21 4Z" />
      </svg>
    )
  }
  if (type === 'content' || type === 'photo') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="4" y="5" width="16" height="14" rx="2" />
        <path d="M8 14L10.3 11.7L13 14.4L14.5 12.9L18 16.4" />
        <path d="M8.5 9.5H8.6" />
      </svg>
    )
  }
  if (type === 'history') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M4 12A8 8 0 1 0 6.3 6.3" />
        <path d="M4 5V10H9" />
        <path d="M12 8V12L15 14" />
      </svg>
    )
  }
  if (type === 'virtual') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M4 8L12 4L20 8V16L12 20L4 16V8Z" />
        <path d="M12 4V12L20 8" />
        <path d="M12 12V20" />
        <path d="M12 12L4 8" />
      </svg>
    )
  }
  if (type === 'location') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 21S5.5 15.8 5.5 10A6.5 6.5 0 0 1 18.5 10C18.5 15.8 12 21 12 21Z" />
        <circle cx="12" cy="10" r="2.3" />
      </svg>
    )
  }
  if (type === 'visibility') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M2.5 12S6 6 12 6S21.5 12 21.5 12S18 18 12 18S2.5 12 2.5 12Z" />
        <circle cx="12" cy="12" r="2.6" />
      </svg>
    )
  }
  if (type === 'priority' || type === 'alert') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 3L21 19H3L12 3Z" />
        <path d="M12 9V13" />
        <path d="M12 17H12.01" />
      </svg>
    )
  }
  if (type === 'actions') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M9 5H7A2 2 0 0 0 5 7V20H19V7A2 2 0 0 0 17 5H15" />
        <path d="M9 5A3 3 0 0 1 15 5V7H9V5Z" />
        <path d="M9 13H15" />
        <path d="M9 17H13" />
        <path d="M16.5 14.5L18 16L21 12.5" />
      </svg>
    )
  }
  if (type === 'contact') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="8" r="3.5" />
        <path d="M5 20C6.2 16.9 8.6 15.3 12 15.3S17.8 16.9 19 20" />
      </svg>
    )
  }
  if (type === 'hektor') {
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 3L19 6V11C19 15.2 16.3 19 12 21C7.7 19 5 15.2 5 11V6L12 3Z" />
        <path d="M9 12L11 14L15.5 9.5" />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.85" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 6H19" />
      <path d="M5 12H19" />
      <path d="M5 18H13" />
    </svg>
  )
}

function DetailSectionTitle({ icon, title }: { icon: DetailIconKey; title: string }) {
  return (
    <span className={`detail-section-title detail-section-title-${icon}`}>
      <span className="detail-section-icon" aria-hidden="true"><DetailIcon type={icon} /></span>
      <h4>{title}</h4>
    </span>
  )
}

function consoleDocumentStatusLabel(status: ConsoleDocument['storage_status']) {
  switch (status) {
    case 'cloud_available':
      return 'Cloud'
    case 'local_only':
      return 'A preparer'
    case 'pending_upload':
      return 'En attente'
    case 'uploading':
      return 'Upload'
    case 'archived_cloud_removed':
      return 'Archive cloud'
    case 'missing':
      return 'Introuvable'
    case 'error':
      return 'Erreur'
    default:
      return status || '-'
  }
}

function consoleDocumentVisibilityLabel(value: ConsoleDocumentVisibility | null | undefined) {
  if (value === 'private') return 'Prive'
  if (value === 'shared') return 'Partage'
  return 'Console'
}

function formatFileSize(bytes: number | null | undefined) {
  if (!bytes || bytes <= 0) return '-'
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(bytes >= 10 * 1024 * 1024 ? 0 : 1)} Mo`
}

function consoleDocumentIconType(document: Pick<ConsoleDocument, 'mime_type' | 'document_name' | 'document_type'>): DetailIconKey {
  const text = `${document.mime_type ?? ''} ${document.document_name ?? ''} ${document.document_type ?? ''}`.toLowerCase()
  if (text.includes('image/') || /\.(jpe?g|png|webp|gif)$/i.test(document.document_name ?? '')) return 'photo'
  if (text.includes('dpe') || text.includes('diagnostic')) return 'hektor'
  if (text.includes('mandat')) return 'mandate'
  return 'content'
}

function ConsoleDocumentsPanel({ dossier, compact = false, onJobCreated }: { dossier: Dossier; compact?: boolean; onJobCreated?: (job: ConsoleJob) => void }) {
  const [documents, setDocuments] = useState<ConsoleDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [pendingDocumentIds, setPendingDocumentIds] = useState<Set<string>>(() => new Set())
  const [deletingDocumentIds, setDeletingDocumentIds] = useState<Set<string>>(() => new Set())
  const [busyDocumentId, setBusyDocumentId] = useState<string | null>(null)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLabel, setUploadLabel] = useState('')
  const [uploadVisibility, setUploadVisibility] = useState<Exclude<ConsoleDocumentVisibility, 'unknown'>>('private')
  const [uploadType, setUploadType] = useState('')
  const [uploadPending, setUploadPending] = useState(false)
  const [uploadInputVersion, setUploadInputVersion] = useState(0)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refreshDocuments = async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      const rows = await loadConsoleDocuments(dossier.app_dossier_id)
      setDocuments(rows)
      setPendingDocumentIds((current) => {
        const next = new Set(current)
        for (const item of rows) {
          if (item.storage_status === 'cloud_available') next.delete(item.id)
        }
        return next
      })
      setDeletingDocumentIds((current) => {
        const visibleIds = new Set(rows.map((item) => item.id))
        const next = new Set(current)
        for (const id of next) {
          if (!visibleIds.has(id)) next.delete(id)
        }
        return next
      })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de chargement des documents Console')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  useEffect(() => {
    setDocuments([])
    setPendingDocumentIds(new Set())
    setDeletingDocumentIds(new Set())
    setMessage(null)
    setError(null)
    void refreshDocuments()
  }, [dossier.app_dossier_id])

  useEffect(() => {
    if (!pendingDocumentIds.size && !deletingDocumentIds.size && !documents.some((item) => item.storage_status === 'pending_upload' || item.storage_status === 'uploading')) return
    const timer = window.setInterval(() => void refreshDocuments(true), 8000)
    return () => window.clearInterval(timer)
  }, [pendingDocumentIds, deletingDocumentIds, documents, dossier.app_dossier_id])

  const cloudCount = documents.filter((item) => item.storage_status === 'cloud_available').length
  const localCount = documents.filter((item) => item.storage_status !== 'cloud_available').length

  async function handleOpenDocument(document: ConsoleDocument) {
    setBusyDocumentId(document.id)
    setMessage(null)
    setError(null)
    try {
      const url = await createConsoleDocumentSignedUrl(document)
      window.open(url, '_blank', 'noopener,noreferrer')
      void refreshDocuments(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible d ouvrir le document')
    } finally {
      setBusyDocumentId(null)
    }
  }

  async function handlePrepareDocument(document: ConsoleDocument) {
    setBusyDocumentId(document.id)
    setMessage(null)
    setError(null)
    try {
      const job = await createPrepareConsoleDocumentJob({ document, priority: 30 })
      onJobCreated?.(job)
      setPendingDocumentIds((current) => new Set([...current, document.id]))
      setMessage(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible de demander la preparation')
    } finally {
      setBusyDocumentId(null)
    }
  }

  function handleUploadFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null
    setUploadFile(file)
    if (file) {
      const extensionIndex = file.name.lastIndexOf('.')
      setUploadLabel(extensionIndex > 0 ? file.name.slice(0, extensionIndex) : file.name)
      setMessage(null)
      setError(null)
    }
  }

  async function handleUploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!uploadFile) {
      setError('Choisis un fichier avant de lancer l upload.')
      return
    }
    setUploadPending(true)
    setMessage(null)
    setError(null)
    try {
      const job = await createUploadDocumentToHektorJob({
        dossier,
        file: uploadFile,
        visibility: uploadVisibility,
        documentLabel: uploadLabel.trim() || null,
        documentType: uploadType.trim() || null,
        priority: 20,
      })
      onJobCreated?.(job)
      setUploadFile(null)
      setUploadLabel('')
      setUploadType('')
      setUploadInputVersion((value) => value + 1)
      setMessage(null)
      window.setTimeout(() => void refreshDocuments(true), 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible de creer la demande upload Hektor')
    } finally {
      setUploadPending(false)
    }
  }

  async function handleDeleteDocument(document: ConsoleDocument) {
    const confirmed = window.confirm(`Supprimer ce document dans Hektor ?\n\n${document.document_name}`)
    if (!confirmed) return
    setBusyDocumentId(document.id)
    setMessage(null)
    setError(null)
    try {
      const job = await createDeleteDocumentFromHektorJob({ document, priority: 15 })
      onJobCreated?.(job)
      setDeletingDocumentIds((current) => new Set([...current, document.id]))
      setMessage(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impossible de creer la demande de suppression Hektor')
    } finally {
      setBusyDocumentId(null)
    }
  }

  return (
    <details className={`console-documents-panel ${compact ? 'is-compact' : ''}`}>
      <summary className="console-documents-head">
        <span className="console-documents-title">
          <span className="console-documents-title-icon" aria-hidden="true"><DetailIcon type="mandate" /></span>
          <span>
            <strong>Documents Hektor Console</strong>
            <small>Ajouter, consulter et preparer les documents</small>
          </span>
        </span>
        <div className="console-documents-summary">
          <StatusPill value={`${documents.length} doc${documents.length > 1 ? 's' : ''}`} />
          <StatusPill value={`${cloudCount} cloud`} />
          {localCount > 0 ? <StatusPill value={`${localCount} a preparer`} /> : null}
        </div>
      </summary>

      <div className="console-documents-body">
        {message ? <p className="console-documents-message">{message}</p> : null}
        {error ? <p className="console-documents-error">{error}</p> : null}

        <form className="console-upload-form" onSubmit={handleUploadDocument}>
          <div className="console-upload-card-head">
            <span className="console-upload-card-icon" aria-hidden="true"><DetailIcon type="actions" /></span>
            <div>
              <strong>Ajouter un document</strong>
              <small>Le fichier sera envoye dans Hektor puis indexe dans l'app.</small>
            </div>
          </div>

          <label className="console-upload-file">
            <span className="console-upload-label">Fichier</span>
            <div className={`console-upload-dropzone ${uploadFile ? 'has-file' : ''}`}>
              <span className="console-upload-dropzone-icon" aria-hidden="true"><DetailIcon type={uploadFile ? consoleDocumentIconType({ mime_type: uploadFile.type, document_name: uploadFile.name, document_type: uploadType }) : 'content'} /></span>
              <span className="console-upload-dropzone-copy">
                <strong>{uploadFile ? uploadFile.name : 'Choisir un fichier'}</strong>
                <small>{uploadFile ? formatFileSize(uploadFile.size) : 'PDF, image, document ou photo mobile'}</small>
              </span>
              <span className="console-upload-pickers">
                <label className="ghost-button console-upload-picker">
                  <span aria-hidden="true"><DetailIcon type="content" /></span>
                  Parcourir
                  <input key={`file-${uploadInputVersion}`} type="file" onChange={handleUploadFileChange} />
                </label>
                <label className="ghost-button console-upload-picker console-upload-camera">
                  <span aria-hidden="true"><DetailIcon type="photo" /></span>
                  Camera
                  <input key={`camera-${uploadInputVersion}`} type="file" accept="image/*" capture="environment" onChange={handleUploadFileChange} />
                </label>
              </span>
            </div>
          </label>

          <label className="filter-field">
            <span>Libelle</span>
            <input value={uploadLabel} onChange={(event) => setUploadLabel(event.target.value)} placeholder="Nom visible dans Hektor" />
          </label>

          <fieldset className="console-visibility-field">
            <span>Visibilite</span>
            <div className="console-segmented-control">
              <button className={uploadVisibility === 'private' ? 'is-active' : ''} type="button" onClick={() => setUploadVisibility('private')}>
                <span aria-hidden="true"><DetailIcon type="visibility" /></span>
                Prive
              </button>
              <button className={uploadVisibility === 'shared' ? 'is-active' : ''} type="button" onClick={() => setUploadVisibility('shared')}>
                <span aria-hidden="true"><DetailIcon type="contact" /></span>
                Public
              </button>
            </div>
          </fieldset>

          <label className="filter-field">
            <span>Type</span>
            <select value={uploadType} onChange={(event) => setUploadType(event.target.value)}>
              <option value="">Autre</option>
              <option value="DPE">DPE</option>
              <option value="Mandat">Mandat</option>
              <option value="Diagnostic">Diagnostic</option>
              <option value="Plan">Plan</option>
              <option value="Facture">Facture</option>
              <option value="Photo">Photo</option>
              <option value="Taxe fonciere">Taxe fonciere</option>
              <option value="Bon de visite">Bon de visite</option>
              <option value="Piece identite">Piece identite</option>
            </select>
          </label>

          <button className="ghost-button button-primary console-upload-submit" type="submit" disabled={uploadPending || !uploadFile}>
            <span aria-hidden="true"><DetailIcon type="hektor" /></span>
            {uploadPending ? 'Demande...' : 'Envoyer'}
          </button>
        </form>

        {loading ? <p className="empty-state">Chargement des documents Console...</p> : null}
        {!loading && documents.length === 0 ? <p className="empty-state">Aucun document Console indexe pour ce dossier.</p> : null}
        {documents.length > 0 ? (
          <div className="console-documents-list">
            {documents.map((document) => {
              const preparing = pendingDocumentIds.has(document.id)
              const deleting = deletingDocumentIds.has(document.id)
              const canOpen = document.storage_status === 'cloud_available'
              const canPrepare = !canOpen && !preparing && document.storage_status !== 'missing' && document.storage_status !== 'error'
              return (
                <article key={document.id} className={`console-document-row console-document-${document.storage_status}`}>
                  <span className="console-document-icon" aria-hidden="true"><DetailIcon type={consoleDocumentIconType(document)} /></span>
                  <div className="console-document-main">
                    <strong>{document.document_name}</strong>
                    <span>{[document.document_type, consoleDocumentVisibilityLabel(document.visibility), formatFileSize(document.file_size)].filter((value) => value && value !== '-').join(' - ') || 'Document Console'}</span>
                  </div>
                  <StatusPill value={deleting ? 'Suppression demandee' : preparing ? 'Demande envoyee' : consoleDocumentStatusLabel(document.storage_status)} />
                  <div className="console-document-actions">
                    {canOpen ? (
                      <button className="ghost-button console-document-open" type="button" onClick={() => void handleOpenDocument(document)} disabled={busyDocumentId === document.id}>
                        <span aria-hidden="true"><DetailIcon type="content" /></span>
                        Ouvrir
                      </button>
                    ) : (
                      <button className="ghost-button console-document-prepare" type="button" onClick={() => void handlePrepareDocument(document)} disabled={!canPrepare || busyDocumentId === document.id}>
                        <span aria-hidden="true"><DetailIcon type="hektor" /></span>
                        {preparing ? 'En attente' : 'Preparer'}
                      </button>
                    )}
                    <button className="ghost-button console-document-delete" type="button" onClick={() => void handleDeleteDocument(document)} disabled={deleting || busyDocumentId === document.id}>
                      <span aria-hidden="true"><DetailIcon type="actions" /></span>
                      {deleting ? 'Suppression' : 'Supprimer'}
                    </button>
                  </div>
                </article>
              )
            })}
          </div>
        ) : null}
      </div>
    </details>
  )
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
  mandat: MandatActionSource
  role: 'nego' | 'pauline'
  requests: DiffusionRequest[]
  currentRequest?: DiffusionRequest | null
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
  onOpenDiffusionModal: (id: number) => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const actionModel = buildMandatActionModel({
    mandat: props.mandat,
    role: props.role,
    requests: props.requests,
    currentRequest: props.currentRequest,
    onOpenRequestModal: props.onOpenRequestModal,
    onOpenDiffusionModal: props.onOpenDiffusionModal,
    onBeforeAction: () => setMenuOpen(false),
  })

  if (!actionModel.hasMandat) {
    return <span className="table-note">Sans mandat</span>
  }

  return (
    <div className="action-menu-shell">
      <button
        className={`ghost-button button-subtle action-menu-trigger action-menu-trigger-${actionModel.triggerTone}`}
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
              {actionModel.items.map((item) => (
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

function DetailDossierActionPanel(props: {
  mandat: MandatActionSource
  role: 'nego' | 'pauline'
  requests: DiffusionRequest[]
  currentRequest?: DiffusionRequest | null
  nextActionLabel?: string
  nextActionDetail?: string | null
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
  onOpenDiffusionModal: (id: number) => void
  renderExtraActions?: () => ReturnType<typeof DetailAdminPilotPanel>
}) {
  const [extraActionsOpen, setExtraActionsOpen] = useState(false)
  const actionModel = buildMandatActionModel({
    mandat: props.mandat,
    role: props.role,
    requests: props.requests,
    currentRequest: props.currentRequest,
    onOpenRequestModal: props.onOpenRequestModal,
    onOpenDiffusionModal: props.onOpenDiffusionModal,
  })

  return (
    <div className="detail-action-console">
      <div className="section-header detail-action-console-head detail-action-console-head-compact">
        <span className="detail-action-console-title-icon" aria-label="Actions du dossier">
          <span className="detail-section-icon" aria-hidden="true"><DetailIcon type="actions" /></span>
        </span>
        {props.renderExtraActions ? (
          <button
            className={`detail-action-more-button ${extraActionsOpen ? 'is-open' : ''}`}
            type="button"
            aria-expanded={extraActionsOpen}
            onClick={() => setExtraActionsOpen((value) => !value)}
          >
            <span>Plus d&apos;actions</span>
            <span aria-hidden="true">⋮</span>
          </button>
        ) : null}
      </div>
      {!actionModel.hasMandat ? (
        <p className="empty-state">Sans mandat : aucune action de validation, diffusion ou baisse de prix disponible.</p>
      ) : (
        <>
          <div className="action-menu-dialog-list detail-action-console-list">
            {actionModel.items.map((item) => (
              <ActionButton
                key={item.key}
                type="button"
                typeLabel={item.typeLabel}
                stateLabel={item.stateLabel}
                typeTone={item.typeTone}
                stateTone={item.stateTone}
                helperText={actionMenuHelperText(item.typeLabel, item.stateLabel)}
                onClick={item.onClick}
              />
            ))}
          </div>
        </>
      )}
      {props.nextActionLabel ? (
        <div className="detail-action-next">
          <span>Prochaine action</span>
          <strong>{props.nextActionLabel}</strong>
          {props.nextActionDetail ? <p>{props.nextActionDetail}</p> : null}
        </div>
      ) : null}
      {props.renderExtraActions && extraActionsOpen ? (
        <div className="detail-action-extra-panel">
          {props.renderExtraActions()}
        </div>
      ) : null}
    </div>
  )
}

function DetailAdminPilotPanel(props: {
  allowValidation?: boolean
  allowDiffusable?: boolean
  validationActive: boolean
  validationObserved: boolean
  validationPending: boolean
  validationSyncPending: boolean
  diffusableActive: boolean
  diffusableObserved: boolean
  diffusablePending: boolean
  diffusableSyncPending: boolean
  onSetValidation?: (checked: boolean) => void
  onSetDiffusable?: (checked: boolean) => void
  onOpenHektor?: () => void
}) {
  if (!props.allowValidation && !props.allowDiffusable) return null
  const validationTone = props.validationPending
    ? 'is-pending'
    : props.validationSyncPending
      ? 'is-alert'
      : props.validationActive
        ? 'is-positive'
        : 'is-neutral'
  const diffusableTone = props.diffusablePending
    ? 'is-pending'
    : props.diffusableSyncPending
      ? 'is-alert'
      : props.diffusableActive
        ? 'is-positive'
        : 'is-neutral'
  const pilotDates = {
    validation: props.validationPending
      ? 'Synchronisation en cours'
      : props.validationObserved
        ? 'Etat confirme par Hektor'
        : 'En attente de validation',
    diffusion: props.diffusablePending
      ? 'Synchronisation en cours'
      : props.diffusableObserved
        ? 'Etat confirme par Hektor'
        : 'Diffusion inactive cote Hektor',
  }

  return (
    <div className="detail-admin-pilot">
      <div className="section-header"><DetailSectionTitle icon="hektor" title="Pilotage Hektor" /></div>
      <p className="detail-admin-intro">Configurez et controlez les automatisations Hektor.</p>
      <div className="detail-admin-pilot-grid">
        {props.allowValidation ? (
          <article className={`detail-admin-tile ${validationTone}`}>
            <div className="detail-admin-tile-shell">
              <div className="detail-admin-identity">
                <span className="detail-admin-icon is-validation" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 3L19 6V11C19 15.2 16.3 19 12 21C7.7 19 5 15.2 5 11V6L12 3Z" />
                    <path d="M9.2 11.8L11.2 13.8L15.4 9.6" />
                  </svg>
                </span>
                <div className="detail-admin-identity-copy">
                  <strong>Validation mandat</strong>
                  <span className={`detail-admin-state ${validationTone}`}>
                    {props.validationPending ? 'Synchronisation...' : props.validationActive ? 'Active' : 'Desactivee'}
                  </span>
                </div>
              </div>
              <div className="detail-admin-control">
                <div className="detail-admin-segmented" role="group" aria-label="Pilotage validation mandat">
                  <button
                    className={`detail-admin-segment is-positive ${props.validationActive ? 'is-selected' : ''}`}
                    type="button"
                    disabled={props.validationPending || props.validationActive}
                    onClick={() => props.onSetValidation?.(true)}
                  >
                    <span className="detail-admin-segment-dot" aria-hidden="true" />
                    <span>Activer</span>
                  </button>
                  <button
                    className={`detail-admin-segment is-negative ${!props.validationActive ? 'is-selected' : ''}`}
                    type="button"
                    disabled={props.validationPending || !props.validationActive}
                    onClick={() => props.onSetValidation?.(false)}
                  >
                    <span className="detail-admin-segment-dot" aria-hidden="true" />
                    <span>Desactiver</span>
                  </button>
                </div>
              </div>
            </div>
            <div className="detail-admin-meta">
              <p className="detail-admin-copy">
                {props.validationActive ? "L'annonce est automatiquement validee apres controle." : 'Validation manquante avant pilotage complet.'}
              </p>
              <div className="detail-admin-timestamps">
                <span>{pilotDates.validation}</span>
                <span>{props.validationSyncPending ? `Relecture : ${props.validationObserved ? 'valide' : 'non valide'}` : `Etat actuel : ${props.validationObserved ? 'valide' : 'non valide'}`}</span>
              </div>
            </div>
          </article>
        ) : null}
        {props.allowDiffusable ? (
          <article className={`detail-admin-tile ${diffusableTone}`}>
            <div className="detail-admin-tile-shell">
              <div className="detail-admin-identity">
                <span className="detail-admin-icon is-diffusion" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 12V8C4 6.3 5.3 5 7 5H8.5L16.5 2V22L8.5 19H7C5.3 19 4 17.7 4 16V12Z" />
                    <path d="M19 8C20.4 9.1 21.3 10.5 21.3 12C21.3 13.5 20.4 14.9 19 16" />
                  </svg>
                </span>
                <div className="detail-admin-identity-copy">
                  <strong>Diffusion</strong>
                  <span className={`detail-admin-state ${diffusableTone}`}>
                    {props.diffusablePending ? 'Synchronisation...' : props.diffusableActive ? 'Active' : 'Desactivee'}
                  </span>
                </div>
              </div>
              <div className="detail-admin-control">
                <div className="detail-admin-segmented" role="group" aria-label="Pilotage diffusion">
                  <button
                    className={`detail-admin-segment is-positive ${props.diffusableActive ? 'is-selected' : ''}`}
                    type="button"
                    disabled={props.diffusablePending || props.diffusableActive}
                    onClick={() => props.onSetDiffusable?.(true)}
                  >
                    <span className="detail-admin-segment-dot" aria-hidden="true" />
                    <span>Activer</span>
                  </button>
                  <button
                    className={`detail-admin-segment is-negative ${!props.diffusableActive ? 'is-selected' : ''}`}
                    type="button"
                    disabled={props.diffusablePending || !props.diffusableActive}
                    onClick={() => props.onSetDiffusable?.(false)}
                  >
                    <span className="detail-admin-segment-dot" aria-hidden="true" />
                    <span>Desactiver</span>
                  </button>
                </div>
              </div>
            </div>
            <div className="detail-admin-meta">
              <p className="detail-admin-copy">
                {props.diffusableActive ? "L'annonce est diffusee automatiquement sur les portails." : 'Diffusion coupee cote Hektor.'}
              </p>
              <div className="detail-admin-timestamps">
                <span>{pilotDates.diffusion}</span>
                <span>{props.diffusableSyncPending ? `Relecture : ${props.diffusableObserved ? 'diffusable' : 'non diffusable'}` : `Etat actuel : ${props.diffusableObserved ? 'diffusable' : 'non diffusable'}`}</span>
              </div>
            </div>
          </article>
        ) : null}
      </div>
      <div className="detail-admin-footer">
        <div className="detail-admin-footer-copy">
          <span className="detail-admin-footer-icon" aria-hidden="true">i</span>
          <p>Les parametres Hektor s&apos;appliquent aux controles de cette annonce.</p>
        </div>
        {props.onOpenHektor ? (
          <button className="detail-admin-footer-button" type="button" onClick={props.onOpenHektor}>
            <ActionExternalGlyph />
            <span>Ouvrir Hektor</span>
          </button>
        ) : null}
      </div>
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
    filters.mandateState !== allFilterValue ? ['État mandat', filters.mandateState] : null,
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
  const [screen, setScreen] = useState<Screen>('mandats')
  const [filterCatalog, setFilterCatalog] = useState<FilterCatalog>(emptyFilterCatalog)
  const [filters, setFilters] = useState<AppFilters>(emptyFilters)
  const [dossiers, setDossiers] = useState<Dossier[]>([])
  const [dossiersTotal, setDossiersTotal] = useState(0)
  const [dossierPage, setDossierPage] = useState(1)
  const [dataReloadKey, setDataReloadKey] = useState(0)
  const [hektorActionJobs, setHektorActionJobs] = useState<ConsoleJob[]>([])
  const hektorActionJobsRef = useRef<ConsoleJob[]>([])
  const [dismissedHektorActionJobIds, setDismissedHektorActionJobIds] = useState<string[]>([])
  const [hektorActionLinkedDossiers, setHektorActionLinkedDossiers] = useState<Record<string, Dossier>>({})
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
  const [mobileStatsOpen, setMobileStatsOpen] = useState(false)
  const [priorityPanelOpen, setPriorityPanelOpen] = useState(false)
  const [commercialMetricsExpanded, setCommercialMetricsExpanded] = useState(false)
  const [activeMandatKpiAction, setActiveMandatKpiAction] = useState<HeaderMetricItem['action']>(null)
  const [mandatDrilldownLabel, setMandatDrilldownLabel] = useState<{ eyebrow: string; title: string } | null>(null)
  const [suiviDrilldownLabel, setSuiviDrilldownLabel] = useState<{ eyebrow: string; title: string } | null>(null)
  const [suiviRequestFilter, setSuiviRequestFilter] = useState<'pending_or_in_progress' | 'accepted_history' | 'refused' | 'waiting_correction' | 'anomalies' | 'price_alert' | 'portfolio' | null>('pending_or_in_progress')
  const [requestLoading, setRequestLoading] = useState(false)
  const [requestPending, setRequestPending] = useState(false)
  const [noticeMessage, setNoticeMessage] = useState<string | null>(null)
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [requestComment, setRequestComment] = useState('')
  const [requestModalOpen, setRequestModalOpen] = useState(false)
  const [requestModalMandatId, setRequestModalMandatId] = useState<number | null>(null)
  const [requestModalComment, setRequestModalComment] = useState('')
  const [requestModalType, setRequestModalType] = useState<BusinessRequestType>('demande_diffusion')
  const [requestModalPriceValue, setRequestModalPriceValue] = useState('')
  const [draftAnnonceModalOpen, setDraftAnnonceModalOpen] = useState(false)
  const [draftAnnoncePending, setDraftAnnoncePending] = useState(false)
  const [draftAnnonceTitle, setDraftAnnonceTitle] = useState('')
  const [draftAnnonceAgency, setDraftAnnonceAgency] = useState('')
  const [draftAnnonceNegotiatorId, setDraftAnnonceNegotiatorId] = useState('')
  const [draftAnnonceAddress, setDraftAnnonceAddress] = useState('')
  const [draftAnnoncePostalCode, setDraftAnnoncePostalCode] = useState('')
  const [draftAnnonceCity, setDraftAnnonceCity] = useState('')
  const [draftAnnoncePrice, setDraftAnnoncePrice] = useState('')
  const [draftAnnonceSurface, setDraftAnnonceSurface] = useState('')
  const [draftAnnonceRoomCount, setDraftAnnonceRoomCount] = useState('')
  const [draftAnnonceBedroomCount, setDraftAnnonceBedroomCount] = useState('')
  const [draftAnnonceNote, setDraftAnnonceNote] = useState('')
  const [deleteAnnonceTarget, setDeleteAnnonceTarget] = useState<Dossier | null>(null)
  const [deleteAnnonceReason, setDeleteAnnonceReason] = useState('')
  const [deleteAnnonceConfirmText, setDeleteAnnonceConfirmText] = useState('')
  const [deleteAnnoncePending, setDeleteAnnoncePending] = useState(false)
  const [hektorNegotiators, setHektorNegotiators] = useState<HektorNegotiatorOption[]>([])
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
  const [priceDropCheckPrompt, setPriceDropCheckPrompt] = useState<null | {
    kind: 'mismatch' | 'confirmed'
    message: string
    hektorAnnonceId: number | string | null
    requestedPrice?: number | null
    observedPrice?: number | null
    pendingAction?: UpdateDiffusionRequestAction
  }>(null)
  const [validationCheckPrompt, setValidationCheckPrompt] = useState<null | {
    kind: 'mismatch' | 'confirmed'
    title: string
    message: string
    detail?: string | null
    hektorAnnonceId: number | string | null
    pendingAction?: UpdateDiffusionRequestAction
  }>(null)
  const [cancellationCheckPrompt, setCancellationCheckPrompt] = useState<null | {
    kind: 'confirmed'
    title: string
    message: string
    detail?: string | null
    hektorAnnonceId: number | string | null
    pendingAction?: UpdateDiffusionRequestAction
  }>(null)
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

  function updateHektorActionJobs(updater: (current: ConsoleJob[]) => ConsoleJob[]) {
    setHektorActionJobs((current) => {
      const next = updater(current)
      hektorActionJobsRef.current = next
      return next
    })
  }

  function rememberHektorActionJob(job: ConsoleJob) {
    updateHektorActionJobs((current) => {
      const withoutSame = current.filter((item) => item.id !== job.id)
      return [job, ...withoutSame].slice(0, 12)
    })
    setDismissedHektorActionJobIds((current) => current.filter((id) => id !== job.id))
  }

  const sessionEmail = normalizeEmail(session?.user.email ?? profile?.email ?? null)
  const dataScope = useMemo<DataScope | undefined>(() => {
    if (profile?.role !== 'commercial') return undefined
    return { negotiatorEmail: sessionEmail || null }
  }, [profile?.role, sessionEmail])
  const draftNegotiatorOptions = useMemo(() => {
    const selectedAgency = draftAnnonceAgency.trim()
    return hektorNegotiators.filter((item) => {
      if (profile?.role === 'commercial') return normalizeEmail(item.email) === sessionEmail
      if (!selectedAgency) return true
      return !item.agenceNom || item.agenceNom === selectedAgency
    })
  }, [draftAnnonceAgency, hektorNegotiators, profile?.role, sessionEmail])
  const selectedDraftNegotiator = useMemo(() => {
    return hektorNegotiators.find((item) => item.idUser === draftAnnonceNegotiatorId) ?? null
  }, [draftAnnonceNegotiatorId, hektorNegotiators])
  const dataFilters = useMemo<AppFilters>(() => {
    if ((screen === 'mandats' || screen === 'suivi') && filters.statut === allFilterValue) return { ...filters, statut: activeListingsFilterValue }
    if (screen === 'estimations') return { ...filters, statut: 'Estimation' }
    return filters
  }, [filters, screen])
  const activeHektorActionJobs = useMemo(() => hektorActionJobs.filter((job) => isPrimaryHektorActionJob(job) && isConsoleJobActive(job)), [hektorActionJobs])
  const visibleHektorActionPopupJobs = useMemo(() => {
    const dismissed = new Set(dismissedHektorActionJobIds)
    return hektorActionJobs
      .filter((job) => !dismissed.has(job.id))
      .filter((job) => isConsoleJobActive(job) || job.status === 'done' || job.status === 'error')
      .sort((left, right) => new Date(right.requested_at).getTime() - new Date(left.requested_at).getTime())
      .slice(0, 8)
  }, [dismissedHektorActionJobIds, hektorActionJobs])
  const activeDeleteAnnonceJobs = useMemo(() => activeHektorActionJobs.filter((job) => job.job_type === 'delete_hektor_annonce'), [activeHektorActionJobs])
  const deletingAppDossierIds = useMemo(() => new Set(activeDeleteAnnonceJobs.map((job) => Number(job.app_dossier_id)).filter((value) => Number.isFinite(value))), [activeDeleteAnnonceJobs])
  const deletingHektorAnnonceIds = useMemo(() => new Set(activeDeleteAnnonceJobs.map((job) => String(job.hektor_annonce_id ?? job.payload_json?.hektor_annonce_id ?? '')).filter(Boolean)), [activeDeleteAnnonceJobs])
  const visibleDossiers = useMemo(() => dossiers.filter((item) => !deletingAppDossierIds.has(item.app_dossier_id) && !deletingHektorAnnonceIds.has(String(item.hektor_annonce_id))), [dossiers, deletingAppDossierIds, deletingHektorAnnonceIds])

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
    loadHektorNegotiatorOptions(dataScope)
      .then((rows) => {
        if (!cancelled) setHektorNegotiators(rows)
      })
      .catch(() => {
        if (!cancelled) setHektorNegotiators([])
      })
    return () => {
      cancelled = true
    }
  }, [session, dataScope])

  useEffect(() => {
    if (!draftAnnonceModalOpen) return
    if (profile?.role === 'commercial') {
      const ownNegotiator = hektorNegotiators.find((item) => normalizeEmail(item.email) === sessionEmail)
      setDraftAnnonceNegotiatorId(ownNegotiator?.idUser ?? '')
      return
    }
    if (draftAnnonceNegotiatorId && !draftNegotiatorOptions.some((item) => item.idUser === draftAnnonceNegotiatorId)) {
      setDraftAnnonceNegotiatorId('')
    }
  }, [draftAnnonceModalOpen, draftAnnonceNegotiatorId, draftNegotiatorOptions, hektorNegotiators, profile?.role, sessionEmail])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    const statsPromise = screen === 'registre'
      ? loadMandatRegisterStats({ ...dataFilters, mandat: withMandatFilterValue }, dataScope)
      : loadMandatStats(dataFilters, dataScope)
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
  }, [session, dataFilters, dataScope, screen])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    loadSuiviRequestStats(dataFilters, dataScope)
      .then((stats) => {
        if (!cancelled) setSuiviRequestStats(stats)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des stats suivi')
      })
    return () => {
      cancelled = true
    }
  }, [session, dataFilters, dataScope, screen])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    loadCommercialRequestStats(dataFilters, dataScope)
      .then((stats) => {
        if (!cancelled) setCommercialRequestStats(stats)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des stats commerciales')
      })
    return () => {
      cancelled = true
    }
  }, [session, dataFilters, dataScope, screen])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    let refreshQueued = false
    async function refreshHektorActionJobs() {
      try {
        const trackedIds = hektorActionRelatedJobIds(hektorActionJobsRef.current)
        const [activeJobs, trackedJobs] = await Promise.all([
          loadActiveHektorActionJobs(),
          loadConsoleJobsByIds(trackedIds),
        ])
        if (cancelled) return
        updateHektorActionJobs((current) => {
          const previousById = new Map(current.map((job) => [job.id, job]))
          const nextById = new Map(current.map((job) => [job.id, job]))
          for (const job of [...activeJobs, ...trackedJobs]) nextById.set(job.id, job)
          const transitioned = [...nextById.values()].some((job) => {
            const previous = previousById.get(job.id)
            return previous && isConsoleJobActive(previous) && !isConsoleJobActive(job)
          })
          if (transitioned && !refreshQueued) {
            refreshQueued = true
            window.setTimeout(() => {
              refreshQueued = false
              setDataReloadKey((value) => value + 1)
            }, 600)
          }
          return [...nextById.values()]
            .sort((left, right) => new Date(right.requested_at).getTime() - new Date(left.requested_at).getTime())
            .slice(0, 12)
        })
      } catch (error) {
        if (!cancelled) console.warn('Hektor action jobs refresh failed', error)
      }
    }
    void refreshHektorActionJobs()
    const interval = window.setInterval(refreshHektorActionJobs, 5000)
    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [session])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    const idsToResolve = visibleHektorActionPopupJobs
      .filter((job) => job.status === 'done')
      .map(hektorCreatedAnnonceId)
      .filter((id): id is string => Boolean(id))
      .filter((id) => !hektorActionLinkedDossiers[id])
    if (idsToResolve.length === 0) return
    let cancelled = false
    async function resolveCreatedDossiers() {
      const resolvedEntries: Array<[string, Dossier]> = []
      for (const id of Array.from(new Set(idsToResolve))) {
        try {
          const dossier = await loadDossierByHektorAnnonceId(id, dataScope)
          if (dossier) resolvedEntries.push([id, dossier])
        } catch (error) {
          console.warn('Hektor created dossier lookup failed', error)
        }
      }
      if (cancelled || resolvedEntries.length === 0) return
      setHektorActionLinkedDossiers((current) => {
        const next = { ...current }
        for (const [id, dossier] of resolvedEntries) next[id] = dossier
        return next
      })
    }
    void resolveCreatedDossiers()
    return () => {
      cancelled = true
    }
  }, [dataScope, hektorActionLinkedDossiers, session, visibleHektorActionPopupJobs])

  useEffect(() => {
    if (hasSupabaseEnv && !session) return
    let cancelled = false
    setPageLoading(true)
    setMandatLoading(true)
    const nextMandatPage = screen === 'suivi' ? 1 : mandatPage
    const nextMandatPageSize = screen === 'suivi' ? 1000 : mandatPageSize
    const dossiersPromise = loadDossiersPage({ filters: dataFilters, page: dossierPage, pageSize: dossierPageSize, scope: dataScope })
    const mandatsPromise = screen === 'registre'
      ? loadMandatRegisterPage({ filters: { ...dataFilters, mandat: withMandatFilterValue }, page: nextMandatPage, pageSize: nextMandatPageSize, scope: dataScope })
      : loadMandatsPage({ filters: dataFilters, page: nextMandatPage, pageSize: nextMandatPageSize, scope: dataScope })
    const workItemsPromise = loadWorkItemsPage({ filters: dataFilters, page: workItemPage, pageSize: workItemPageSize, scope: dataScope })

    mandatsPromise
      .then((nextMandatsPage) => {
        if (cancelled) return
        const scopedRows = filterMandatRowsForScreen(nextMandatsPage.rows, screen)
        setMandats(scopedRows)
        setMandatsTotal(nextMandatsPage.total)
        setFilterCatalog((current) => mergeCatalog(current, buildPageFilterCatalog([], [], scopedRows)))
        if (screen === 'registre') {
          setSelectedRegisterRowId((current) => {
            if (current && scopedRows.some((item) => item.register_row_id === current)) return current
            return scopedRows[0]?.register_row_id ?? null
          })
        } else {
          setSelectedMandatId((current) => current ?? (scopedRows[0]?.app_dossier_id ?? null))
        }
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement des annonces actives')
      })
      .finally(() => {
        if (!cancelled) setMandatLoading(false)
      })

    Promise.all([dossiersPromise, workItemsPromise])
      .then(([nextDossiersPage, nextWorkItemsPage]) => {
        if (cancelled) return
        setDossiers(nextDossiersPage.rows)
        setDossiersTotal(nextDossiersPage.total)
        setWorkItems(nextWorkItemsPage.rows)
        setWorkItemsTotal(nextWorkItemsPage.total)
        setFilterCatalog((current) => mergeCatalog(current, buildPageFilterCatalog(nextDossiersPage.rows, nextWorkItemsPage.rows, [])))
        setSelectedDossierId((current) => current ?? nextDossiersPage.rows[0]?.app_dossier_id ?? null)
      })
      .catch((error) => {
        if (!cancelled) setErrorMessage(error instanceof Error ? error.message : 'Erreur de chargement')
      })
      .finally(() => {
        if (!cancelled) setPageLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [session, dataFilters, dossierPage, mandatPage, workItemPage, dataScope, screen, dataReloadKey])

  useEffect(() => {
    if (selectedDossierId == null) return
    const quickMandat = mandats.find((item) => item.app_dossier_id === selectedDossierId)
    const quickBase = dossiers.find((item) => item.app_dossier_id === selectedDossierId) ?? (quickMandat ? mandateAsDossier(quickMandat) : null)
    setSelectedDossier((current) => {
      if (!quickBase) return current?.app_dossier_id === selectedDossierId ? current : null
      const currentDetailPayload = current?.app_dossier_id === selectedDossierId ? current.detail_payload_json : null
      return { ...quickBase, detail_payload_json: currentDetailPayload }
    })
  }, [selectedDossierId, dossiers, mandats])

  useEffect(() => {
    if (selectedDossierId == null || (hasSupabaseEnv && !session)) return
    let cancelled = false
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
  }, [selectedDossierId, session, dataReloadKey])

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
    const deepLinkRequestType: BusinessRequestType | undefined =
      requestTypeParam === 'demande_baisse_prix'
        ? 'demande_baisse_prix'
        : requestTypeParam === 'demande_annulation_mandat'
          ? 'demande_annulation_mandat'
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
    if (screen === 'mandats') setActiveMandatKpiAction(null)
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
    setFilters(defaultFiltersForScreen(screen))
    setMandatDrilldownLabel(null)
    setActiveMandatKpiAction(null)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(screen === 'suivi' ? 'pending_or_in_progress' : null)
    setPriorityPanelOpen(false)
    setCommercialMetricsExpanded(false)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
  }

  function openScreen(nextScreen: Screen) {
    setScreen(nextScreen === 'annonces' ? 'mandats' : nextScreen)
    setMobileMenuOpen(false)
    setMandatDrilldownLabel(null)
    setActiveMandatKpiAction(null)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(nextScreen === 'suivi' ? 'pending_or_in_progress' : null)
    setFiltersOpen(false)
    setPriorityPanelOpen(false)
    setCommercialMetricsExpanded(false)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
    setFilters(defaultFiltersForScreen(nextScreen))
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
      setPriorityPanelOpen(false)
      setDossierPage(1)
      setMandatPage(1)
      setWorkItemPage(1)
      setDetailOpen(false)
      setCommercialMetricsExpanded(false)
      setMandatDrilldownLabel(null)
      setActiveMandatKpiAction(null)
      setSuiviDrilldownLabel(nextSuiviLabel)
      setSuiviRequestFilter(nextSuiviFilter)
      setFilters(emptyFilters)
      return
    }
    const nextFilters = metricDrilldownFilters(filters, action)
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
    setPriorityPanelOpen(false)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
    setCommercialMetricsExpanded(false)
    setMandatDrilldownLabel(nextLabel)
    setActiveMandatKpiAction(action)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(null)
    setFilters(nextFilters)
  }

  function openRegisterDrilldown(action: HeaderMetricItem['action']) {
    if (!action) return
    const nextFilters = metricDrilldownFilters(filters, action)
    setScreen('registre')
    setFiltersOpen(false)
    setPriorityPanelOpen(false)
    setDossierPage(1)
    setMandatPage(1)
    setWorkItemPage(1)
    setDetailOpen(false)
    setCommercialMetricsExpanded(false)
    setMandatDrilldownLabel(null)
    setActiveMandatKpiAction(null)
    setSuiviDrilldownLabel(null)
    setSuiviRequestFilter(null)
    setFilters(nextFilters)
  }

  function openDossierDetailPage(appDossierId: number) {
    const quickMandat = mandats.find((item) => item.app_dossier_id === appDossierId)
    const quickBase = dossiers.find((item) => item.app_dossier_id === appDossierId) ?? (quickMandat ? mandateAsDossier(quickMandat) : null)
    const currentDetailPayload = selectedDossier?.app_dossier_id === appDossierId ? selectedDossier.detail_payload_json : null
    setSelectedDossier(quickBase ? { ...quickBase, detail_payload_json: currentDetailPayload } : null)
    setDetailLoading(true)
    setSelectedDossierId(appDossierId)
    setDetailOpen(true)
  }

  function closeDossierDetailPage() {
    setDetailOpen(false)
    setDetailImageModalUrl(null)
  }

function openRequestModal(appDossierId: number, role: 'nego' | 'pauline' = 'nego', requestType?: BusinessRequestType) {
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
    setPriceDropCheckPrompt(null)
    setValidationCheckPrompt(null)
    setCancellationCheckPrompt(null)
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
    setPriceDropCheckPrompt(null)
    setValidationCheckPrompt(null)
    setCancellationCheckPrompt(null)
  }

  function openDraftAnnonceModal() {
    const agency = userNegotiatorContext?.agence_nom || (filters.agency !== allFilterValue ? filters.agency : '')
    const ownNegotiator = hektorNegotiators.find((item) => normalizeEmail(item.email) === sessionEmail)
    setDraftAnnonceAgency(agency === allFilterValue ? '' : agency)
    setDraftAnnonceNegotiatorId(profile?.role === 'commercial' ? (ownNegotiator?.idUser ?? '') : '')
    setDraftAnnonceTitle('')
    setDraftAnnonceAddress('')
    setDraftAnnoncePostalCode('')
    setDraftAnnonceCity('')
    setDraftAnnoncePrice('')
    setDraftAnnonceSurface('')
    setDraftAnnonceRoomCount('')
    setDraftAnnonceBedroomCount('')
    setDraftAnnonceNote('')
    setNoticeMessage(null)
    setErrorMessage(null)
    setDraftAnnonceModalOpen(true)
  }

  function closeDraftAnnonceModal() {
    if (draftAnnoncePending) return
    setDraftAnnonceModalOpen(false)
  }

  function dismissHektorActionPopup(jobId: string) {
    const job = hektorActionJobsRef.current.find((item) => item.id === jobId)
    const relatedIds = job ? [job.id, hektorJobSyncJobId(job)].filter((id): id is string => Boolean(id)) : [jobId]
    setDismissedHektorActionJobIds((current) => Array.from(new Set([...current, ...relatedIds])))
  }

  async function openHektorActionAppDossier(job: ConsoleJob) {
    const hektorAnnonceId = hektorCreatedAnnonceId(job)
    if (!hektorAnnonceId) return
    let dossier: Dossier | null = hektorActionLinkedDossiers[hektorAnnonceId] ?? null
    if (!dossier) {
      dossier = await loadDossierByHektorAnnonceId(hektorAnnonceId, dataScope)
      if (dossier) {
        setHektorActionLinkedDossiers((current) => ({ ...current, [hektorAnnonceId]: dossier as Dossier }))
      }
    }
    if (!dossier) {
      setNoticeMessage("L'annonce est creee dans Hektor. Elle n'est pas encore visible dans l'app, la synchronisation continue.")
      return
    }
    setScreen('annonces')
    setSelectedDossierId(dossier.app_dossier_id)
    setDataReloadKey((value) => value + 1)
    setDetailOpen(true)
    dismissHektorActionPopup(job.id)
  }

  async function handleCreateDraftAnnonce(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!draftAnnonceAgency.trim()) {
      setErrorMessage('Choisis une agence avant de creer l annonce Hektor.')
      return
    }
    if (!selectedDraftNegotiator) {
      setErrorMessage(profile?.role === 'commercial' ? 'Impossible d identifier ton acces negociateur Hektor.' : 'Choisis le negociateur Hektor qui portera l annonce.')
      return
    }
    setDraftAnnoncePending(true)
    setNoticeMessage(null)
    setErrorMessage(null)
    try {
      const job = await createHektorDraftAnnonceJob({
        title: draftAnnonceTitle,
        agenceNom: draftAnnonceAgency,
        hektorUserId: selectedDraftNegotiator.idUser,
        hektorUserLabel: selectedDraftNegotiator.label,
        hektorUserEmail: selectedDraftNegotiator.email,
        propertyType: 'Appartement',
        offerType: 'sale',
        address: draftAnnonceAddress,
        postalCode: draftAnnoncePostalCode,
        city: draftAnnonceCity,
        price: draftAnnoncePrice,
        surface: draftAnnonceSurface,
        roomCount: draftAnnonceRoomCount,
        bedroomCount: draftAnnonceBedroomCount,
        note: draftAnnonceNote,
        priority: 10,
      })
      rememberHektorActionJob(job)
      setDraftAnnonceModalOpen(false)
      setNoticeMessage(null)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Impossible de creer la demande d annonce Hektor')
    } finally {
      setDraftAnnoncePending(false)
    }
  }

  function openDeleteAnnonceModal(dossier: Dossier) {
    if (!isAdmin) return
    setDeleteAnnonceTarget(dossier)
    setDeleteAnnonceReason('')
    setDeleteAnnonceConfirmText('')
    setNoticeMessage(null)
    setErrorMessage(null)
  }

  function closeDeleteAnnonceModal() {
    if (deleteAnnoncePending) return
    setDeleteAnnonceTarget(null)
    setDeleteAnnonceReason('')
    setDeleteAnnonceConfirmText('')
  }

  async function handleDeleteHektorAnnonce(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!deleteAnnonceTarget) return
    const expected = `SUPPRIMER ${deleteAnnonceTarget.hektor_annonce_id}`
    if (deleteAnnonceConfirmText.trim() !== expected) {
      setErrorMessage(`Confirmation incorrecte. Tape exactement : ${expected}`)
      return
    }
    setDeleteAnnoncePending(true)
    setNoticeMessage(null)
    setErrorMessage(null)
    try {
      const job = await createDeleteHektorAnnonceJob({
        dossier: deleteAnnonceTarget,
        reason: deleteAnnonceReason,
        confirmText: deleteAnnonceConfirmText,
        priority: 5,
      })
      const deletedAppDossierId = deleteAnnonceTarget.app_dossier_id
      rememberHektorActionJob(job)
      setDossiers((current) => current.filter((item) => item.app_dossier_id !== deletedAppDossierId))
      setMandats((current) => current.filter((item) => item.app_dossier_id !== deletedAppDossierId))
      setWorkItems((current) => current.filter((item) => item.app_dossier_id !== deletedAppDossierId))
      setSelectedDossierId((current) => current === deletedAppDossierId ? null : current)
      setSelectedDossier((current) => current?.app_dossier_id === deletedAppDossierId ? null : current)
      setDeleteAnnonceTarget(null)
      setDeleteAnnonceReason('')
      setDeleteAnnonceConfirmText('')
      setDetailOpen(false)
      setNoticeMessage(`Annonce masquee. Suppression Hektor en arriere-plan, job ${job.id.slice(0, 8)}.`)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Impossible de creer la demande de suppression Hektor')
    } finally {
      setDeleteAnnoncePending(false)
    }
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

  async function handleCreateDiffusionRequest(input?: { mandatId?: number | null; comment?: string; requestType?: BusinessRequestType; requestedPrice?: string | null }) {
    const mandatId = input?.mandatId ?? selectedMandatId
    if (!mandatId || !profile) return
    const mandat = mandats.find((item) => item.app_dossier_id === mandatId)
    if (!mandat) return
    const nextType = input?.requestType ?? requestModalType
    if (nextType === 'demande_baisse_prix' && !isValidationApproved(mandat.validation_diffusion_state)) {
      setErrorMessage("Baisse de prix impossible : le mandat doit etre sous validation = oui.")
      return
    }
    if (nextType === 'demande_annulation_mandat' && !isValidationApproved(mandat.validation_diffusion_state)) {
      setErrorMessage("Annulation de mandat impossible : le mandat doit etre sous validation = oui.")
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
          : nextType === 'demande_annulation_mandat'
            ? [`Demande d annulation de mandat`, baseComment ? `Motif / contexte : ${baseComment}` : null].filter(Boolean).join('\n')
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

  async function handleUpdateDiffusionRequest(input: UpdateDiffusionRequestAction) {
    if (!profile) return
    setRequestLoading(true)
    setErrorMessage(null)
    let mutationCommitted = false
    let requestTypeForCatch: BusinessRequestType | null = null
    try {
      const currentRequest = diffusionRequests.find((item) => item.id === input.requestId) ?? null
      const currentMandat = currentRequest ? mandats.find((item) => item.app_dossier_id === currentRequest.app_dossier_id) ?? null : null
      const currentRequestType = normalizeRequestType(input.requestType ?? currentRequest?.request_type)
      requestTypeForCatch = currentRequestType
      let acceptanceResult: Awaited<ReturnType<typeof acceptDiffusionRequestOnHektor>> | Awaited<ReturnType<typeof applyDiffusionTargetsOnHektor>> | null = null
      let acceptanceInfoMessage: string | null = null
      if (currentRequest && currentRequestType === 'demande_annulation_mandat') {
        setPriceDropCheckPrompt(null)
        setValidationCheckPrompt(null)
        if (input.status === 'accepted' && !input.cancellationChecked) {
          setCancellationCheckPrompt({
            kind: 'confirmed',
            title: 'Finaliser l annulation ?',
            message: 'Demande d annulation acceptee. Voulez vous decocher Valide et Diffuse sur l annonce ?',
            detail: 'Oui lance le decochement Hektor. Non accepte la demande sans automatisme Hektor.',
            hektorAnnonceId: currentRequest.hektor_annonce_id,
            pendingAction: { ...input, cancellationChecked: true },
          })
          return
        }
        setCancellationCheckPrompt(null)
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
        if (input.status === 'accepted' && input.unpublishAfterCancellation) {
          acceptanceInfoMessage = 'Demande d annulation de mandat acceptee.'
          try {
            const diffusableResult = await setDossierDiffusableOnHektor({
              appDossierId: currentRequest.app_dossier_id,
              diffusable: false,
            })
            const validationResult = await setDossierValidationOnHektor({
              appDossierId: currentRequest.app_dossier_id,
              state: 0,
            })
            const observedValidation = validationResult.observed_validation
            const validationValue =
              observedValidation && normalizeValidationState(observedValidation)
                ? isValidationApproved(observedValidation) ? 'oui' : 'non'
                : 'non'
            const observedDiffusable = validationResult.observed_diffusable ?? diffusableResult.observed_diffusable
            const diffusableValue = isDiffusableValue(observedDiffusable) ? '1' : '0'
            await setDossierHektorState(currentRequest.app_dossier_id, {
              validationDiffusionState: validationValue,
              diffusable: diffusableValue === '1',
            })
            const patch = { validation_diffusion_state: validationValue, diffusable: diffusableValue }
            setDossiers((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, ...patch } : item))
            setMandats((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, ...patch } : item))
            setSelectedDossier((current) => current && current.app_dossier_id === currentRequest.app_dossier_id ? { ...current, ...patch } : current)
            if (selectedDossier?.app_dossier_id === currentRequest.app_dossier_id) {
              setDetailValidationDraft(validationValue)
              setDetailValidationObserved(validationValue)
              setDetailValidationSaved(validationValue)
              setDetailDiffusableDraft(diffusableValue === '1')
              setDetailDiffusableObserved(diffusableValue === '1')
              setDetailDiffusableSaved(diffusableValue === '1')
            }
            acceptanceInfoMessage = 'Demande d annulation de mandat acceptee. Valide et Diffuse ont ete decoches sur Hektor.'
          } catch (error) {
            const hektorError = error instanceof Error ? error.message : 'Decochement Hektor impossible'
            acceptanceInfoMessage = `Demande d annulation de mandat acceptee, mais Valide/Diffuse n ont pas pu etre decoches : ${hektorError}`
          }
        } else if (input.status === 'accepted') {
          acceptanceInfoMessage = 'Demande d annulation de mandat acceptee. Aucun automatisme Hektor n a ete lance.'
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
        const decisionEmail = buildDiffusionDecisionEmail({
          status: input.status,
          requestType: currentRequestType,
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
        if (!decisionEmail && (input.status === 'accepted' || input.status === 'refused')) {
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
        return
      }
      setCancellationCheckPrompt(null)
      const isPriceDropApproval = input.status === 'accepted' && currentRequest && currentRequestType === 'demande_baisse_prix'
      if (isPriceDropApproval && !input.priceDropChecked) {
        const requestedPrice = extractRequestedPriceFromRequest(currentRequest)
        if (!requestedPrice.numeric) {
          throw new Error('Montant de baisse de prix introuvable dans la demande.')
        }
        const requestText = [currentRequest.request_reason, currentRequest.request_comment].filter(Boolean).join('\n')
        const check = await verifyPriceDropOnHektor({
          appDossierId: currentRequest.app_dossier_id,
          requestedPrice: requestedPrice.normalized,
          requestText,
        })
        if (!check.matches) {
          setPriceDropCheckPrompt({
            kind: 'mismatch',
            message: 'Opération refusée : Prix différent Hektor',
            hektorAnnonceId: currentRequest.hektor_annonce_id,
            requestedPrice: check.requested_price,
            observedPrice: check.observed_price,
          })
          return
        }
        setPriceDropCheckPrompt({
          kind: 'confirmed',
          message: 'Opération validé ! Voulez vous diffusé et activer toute les passerelles ?',
          hektorAnnonceId: currentRequest.hektor_annonce_id,
          requestedPrice: check.requested_price,
          observedPrice: check.observed_price,
          pendingAction: { ...input, priceDropChecked: true },
        })
        return
      }
      setPriceDropCheckPrompt(null)
      const isClassicValidationApproval =
        input.status === 'accepted' &&
        currentRequest &&
        currentRequestType === 'demande_diffusion'
      if (isClassicValidationApproval && !input.validationChecked) {
        setValidationCheckPrompt({
          kind: 'confirmed',
          title: 'Lancer la validation Hektor ?',
          message: 'Cette action va accepter la demande, demander Validation = oui, activer Diffusable puis appliquer les passerelles par defaut.',
          detail: 'Clique sur Non pour accepter la demande sans lancer l automatisme Hektor.',
          hektorAnnonceId: currentRequest.hektor_annonce_id,
          pendingAction: { ...input, validationChecked: true },
        })
        return
      }
      setValidationCheckPrompt(null)
      if (input.status === 'accepted' && currentRequest) {
        if (currentRequestType === 'demande_baisse_prix' && input.publishAfterPriceDrop) {
          if (!currentMandat) {
            throw new Error('Mandat introuvable pour activer les passerelles de cette baisse de prix.')
          }
          const defaultPreview = await previewDefaultDiffusionTargets({ appDossierId: currentRequest.app_dossier_id })
          const defaultTargets = (defaultPreview.targets ?? []).map((target) => ({
            hektor_broadcast_id: String(target.hektor_broadcast_id),
            portal_key: target.portal_key,
            target_state: 'enabled' as const,
          }))
          if (defaultTargets.length === 0) {
            throw new Error('Aucune passerelle par defaut trouvee pour ce mandat.')
          }
          await saveDiffusionTargets({
            mandat: currentMandat,
            targets: defaultTargets,
            requestedByName: userFullName(profile),
            requestedByRole: 'system',
          })
          acceptanceInfoMessage = "Baisse de prix acceptee. L'app active les passerelles par defaut sans modifier Validation ni Diffusable."
          acceptanceResult = await applyDiffusionTargetsOnHektor({
            appDossierId: currentRequest.app_dossier_id,
            ensureDiffusable: false,
          })
          if ((acceptanceResult.failed ?? []).length > 0) {
            const failureDetails = summarizeApplyFailures(acceptanceResult.failed)
            throw new Error(
              failureDetails
                ? `Activation passerelles refusee par Hektor : ${failureDetails}. La demande reste en attente.`
                : 'Activation passerelles refusee par Hektor. La demande reste en attente.',
            )
          }
        } else if (currentRequestType === 'demande_diffusion' && input.runValidationWorkflow !== false) {
          if (!isValidationApproved(currentMandat?.validation_diffusion_state ?? null)) {
            acceptanceInfoMessage = "Demande acceptee. L'app demande d'abord Validation = oui sur Hektor, puis active la diffusion et les passerelles si Hektor confirme la validation."
          }
          acceptanceResult = await acceptDiffusionRequestOnHektor({
            appDossierId: currentRequest.app_dossier_id,
          })
          if ((acceptanceResult.failed ?? []).length > 0) {
            const failureDetails = summarizeApplyFailures(acceptanceResult.failed)
            setValidationCheckPrompt({
              kind: 'mismatch',
              title: 'Opération refusée par Hektor',
              message: 'La demande n a pas ete acceptee : Hektor a refuse la validation ou l activation des passerelles.',
              detail: failureDetails || acceptanceResult.waiting_message || null,
              hektorAnnonceId: currentRequest.hektor_annonce_id,
            })
            return
          }
        } else if (currentRequestType === 'demande_diffusion') {
          acceptanceInfoMessage = 'Demande acceptee sans lancement de la validation Hektor.'
        }
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
        const isPriceDropPublish = currentRequestType === 'demande_baisse_prix' && input.publishAfterPriceDrop
        const observedDiffusable = acceptanceResult.observed_diffusable
        const currentDiffusable = currentMandat?.diffusable ?? (selectedDossier?.app_dossier_id === currentRequest.app_dossier_id ? selectedDossier.diffusable : null)
        const diffusableValue =
          observedDiffusable != null && String(observedDiffusable).trim() !== ''
            ? isDiffusableValue(observedDiffusable) ? '1' : '0'
            : isDiffusableValue(currentDiffusable) ? '1' : '0'
        const validationValue =
          acceptanceResult.observed_validation && isValidationApproved(acceptanceResult.observed_validation)
            ? acceptanceResult.observed_validation
            : acceptanceResult.validation_state && isValidationApproved(acceptanceResult.validation_state)
              ? acceptanceResult.validation_state
              : currentMandat?.validation_diffusion_state ?? null
        if (isPriceDropPublish) {
          const observedStatePatch: Parameters<typeof setDossierHektorState>[1] = {}
          if (observedDiffusable != null && String(observedDiffusable).trim() !== '') {
            observedStatePatch.diffusable = isDiffusableValue(observedDiffusable)
          }
          if (acceptanceResult.observed_validation && isValidationApproved(acceptanceResult.observed_validation)) {
            observedStatePatch.validationDiffusionState = acceptanceResult.observed_validation
          }
          if (typeof observedStatePatch.diffusable !== 'undefined' || typeof observedStatePatch.validationDiffusionState !== 'undefined') {
            await setDossierHektorState(currentRequest.app_dossier_id, observedStatePatch)
            setDossiers((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? {
              ...item,
              ...(typeof observedStatePatch.diffusable !== 'undefined' ? { diffusable: observedStatePatch.diffusable ? '1' : '0' } : {}),
              ...(observedStatePatch.validationDiffusionState ? { validation_diffusion_state: observedStatePatch.validationDiffusionState } : {}),
            } : item))
            setMandats((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? {
              ...item,
              ...(typeof observedStatePatch.diffusable !== 'undefined' ? { diffusable: observedStatePatch.diffusable ? '1' : '0' } : {}),
              ...(observedStatePatch.validationDiffusionState ? { validation_diffusion_state: observedStatePatch.validationDiffusionState } : {}),
            } : item))
            setSelectedDossier((current) => current && current.app_dossier_id === currentRequest.app_dossier_id ? {
              ...current,
              ...(typeof observedStatePatch.diffusable !== 'undefined' ? { diffusable: observedStatePatch.diffusable ? '1' : '0' } : {}),
              ...(observedStatePatch.validationDiffusionState ? { validation_diffusion_state: observedStatePatch.validationDiffusionState } : {}),
            } : current)
          }
        }
        if (!isPriceDropPublish && currentRequestType === 'demande_diffusion') {
          await setDossierHektorState(currentRequest.app_dossier_id, {
            validationDiffusionState: validationValue,
            diffusable: diffusableValue === '1',
          })
          setDossiers((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, diffusable: diffusableValue, validation_diffusion_state: validationValue } : item))
          setMandats((current) => current.map((item) => item.app_dossier_id === currentRequest.app_dossier_id ? { ...item, diffusable: diffusableValue, validation_diffusion_state: validationValue } : item))
          setSelectedDossier((current) => current && current.app_dossier_id === currentRequest.app_dossier_id ? { ...current, diffusable: diffusableValue, validation_diffusion_state: validationValue } : current)
        }
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
        if (currentRequestType === 'demande_diffusion') {
          await setDossierHektorState(currentRequest.app_dossier_id, {
            validationDiffusionState: acceptanceResult.observed_validation ?? acceptanceResult.validation_state ?? currentMandat?.validation_diffusion_state ?? null,
            diffusable:
              isDiffusableValue(acceptanceResult.observed_diffusable)
                ? true
                : acceptanceResult.observed_diffusable === '0'
                  ? false
                  : null,
          })
        }
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
            requestType: currentRequestType,
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
      if (!decisionEmail && currentRequest && (input.status === 'accepted' || input.status === 'refused')) {
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
        const currentRequest = diffusionRequests.find((item) => item.id === input.requestId) ?? null
        const message = error instanceof Error ? error.message : 'Erreur de mise a jour de demande'
        const currentRequestType = requestTypeForCatch ?? normalizeRequestType(input.requestType ?? currentRequest?.request_type)
        if (input.status === 'accepted' && currentRequest && currentRequestType === 'demande_diffusion') {
          setValidationCheckPrompt({
            kind: 'mismatch',
            title: 'Opération refusée par Hektor',
            message: 'La demande n a pas ete acceptee : Hektor a bloque la validation ou la diffusion.',
            detail: message,
            hektorAnnonceId: currentRequest.hektor_annonce_id,
          })
        } else {
          setErrorMessage(message)
        }
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
  const canCreateHektorDraftAnnonce = profile?.role === 'admin' || profile?.role === 'manager' || profile?.role === 'commercial'
  const visibleDossiersCount = dossiersTotal || dossiers.length
  const dossierTotalPages = totalPages(dossiersTotal, dossierPageSize)
  const mandatTotalPages = totalPages(mandatsTotal, mandatPageSize)
  const workItemTotalPages = totalPages(workItemsTotal, workItemPageSize)
  const screenMandats = useMemo(() => filterMandatRowsForScreen(mandats, screen), [mandats, screen])
  const activeFilters = useMemo(() => activeFilterEntries(filters), [filters])
  const screenHeader = useMemo(() => {
    if (screen === 'annonces') {
      return { title: 'Annonces', copy: '' }
    }
    if (screen === 'mandats') {
      return {
        title: mandatDrilldownLabel?.title ?? 'Annonces actives',
        copy: '',
      }
    }
    if (screen === 'estimations') {
      return { title: 'Estimations', copy: '' }
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
      screenMandats.find((item) => item.app_dossier_id === selectedMandatId) ??
      (selectedDossier && selectedDossier.app_dossier_id === selectedMandatId ? (selectedDossier as unknown as MandatRecord) : null),
    [screenMandats, selectedDossier, selectedMandatId],
  )
  const selectedRegisterMandat = useMemo(
    () => screenMandats.find((item) => (item.register_row_id ?? null) === selectedRegisterRowId) ?? null,
    [screenMandats, selectedRegisterRowId],
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
    () => requestModalRequest ? normalizeRequestType(requestModalRequest.request_type) : requestModalType,
    [requestModalRequest, requestModalType],
  )
  const requestModalNegoLabel = useMemo(() => {
    const label = requestActionLabel(requestModalRequest, requestModalEffectiveType)
    if (label === 'Demande de validation') return 'Ajouter'
    if (label === 'Demande de baisse de prix') return 'Ajouter'
    if (label === 'Demande annulation mandat') return 'Ajouter'
    return label
  }, [requestModalRequest, requestModalEffectiveType])
  const requestModalEligibleForPriceDrop = useMemo(
    () => isValidationApproved(requestModalMandat?.validation_diffusion_state ?? null) || (requestModalEffectiveType === 'demande_baisse_prix' && Boolean(requestModalRequest)),
    [requestModalEffectiveType, requestModalMandat, requestModalRequest],
  )
  const requestModalEligibleForCancellation = useMemo(
    () => isValidationApproved(requestModalMandat?.validation_diffusion_state ?? null) || (requestModalEffectiveType === 'demande_annulation_mandat' && Boolean(requestModalRequest)),
    [requestModalEffectiveType, requestModalMandat, requestModalRequest],
  )
  const requestModalRefusalOptions = useMemo(
    () => (requestModalEffectiveType === 'demande_baisse_prix' ? priceDropRefusalReasonOptions : requestModalEffectiveType === 'demande_annulation_mandat' ? cancellationRefusalReasonOptions : refusalReasonOptions),
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
    if (screen === 'estimations') {
      return [
        { label: 'Estimations', value: new Intl.NumberFormat('fr-FR').format(mandatStats.total), tone: 'volume', action: null },
        { label: 'Futurs mandats', value: new Intl.NumberFormat('fr-FR').format(Math.max(0, mandatStats.total - mandatStats.withoutMandat)), tone: 'diffusion', action: null },
        { label: 'Sans mandat', value: new Intl.NumberFormat('fr-FR').format(mandatStats.withoutMandat), tone: 'warning', action: null },
      ]
    }
    return [
      { label: 'Demandes à traiter', value: new Intl.NumberFormat('fr-FR').format(suiviRequestStats.pendingOrInProgress), tone: 'demandes', action: 'suivi_a_traiter' },
      { label: 'Demandes acceptées', value: new Intl.NumberFormat('fr-FR').format(suiviRequestStats.acceptedHistorical), tone: 'demandes', action: 'suivi_acceptees' },
      { label: 'Demandes rejetées', value: new Intl.NumberFormat('fr-FR').format(suiviRequestStats.refused), tone: 'demandes', action: 'suivi_rejetees' },
      { label: 'Affaires en cours', value: new Intl.NumberFormat('fr-FR').format(mandatStats.affairesEnCours), tone: 'affaires', action: null },
    ]
  }, [screen, visibleDossiersCount, workItemsTotal, workItems.length, mandatStats, commercialRequestStats, suiviRequestStats])
  const statsMetrics = headerMetrics
  const viewPriorities = useMemo<Array<{
    label: string
    value: string
    detail: string
    tone: HeaderMetricItem['tone']
    action: HeaderMetricItem['action']
  }>>(() => {
    const format = (value: number) => new Intl.NumberFormat('fr-FR').format(value)
    if (screen === 'mandats') {
      return [
        { label: 'Diffusion à ouvrir', value: format(mandatStats.mandatNonDiffuse), detail: 'Ouvrir les portails non activés', tone: 'diffusion', action: 'mandat_non_diffuse' },
        { label: 'Mandats à valider', value: format(mandatStats.mandatNonValide), detail: 'Vérifier et valider les nouveaux mandats', tone: 'warning', action: 'mandat_non_valide' },
        { label: 'Erreur passerelle', value: format(workItemsTotal || workItems.length), detail: 'Corrections requises sur les portails', tone: 'warning', action: 'correction_attente' },
      ]
    }
    if (screen === 'registre') {
      return [
        { label: 'Non validés', value: format(mandatStats.mandatNonValide), detail: 'Mandats enregistrés à contrôler', tone: 'warning', action: 'mandat_non_valide' },
        { label: 'Non diffusables', value: format(mandatStats.mandatNonDiffuse), detail: 'Mandats à préparer avant diffusion', tone: 'diffusion', action: 'mandat_non_diffuse' },
        { label: 'Registre', value: format(Math.max(0, mandatStats.total - mandatStats.withoutMandat)), detail: 'Mandats disponibles dans la vue', tone: 'volume', action: 'all_annonces' },
      ]
    }
    if (screen === 'estimations') {
      return [
        { label: 'Sans mandat', value: format(mandatStats.withoutMandat), detail: 'Estimations à transformer ou qualifier', tone: 'warning', action: null },
        { label: 'Futurs mandats', value: format(Math.max(0, mandatStats.total - mandatStats.withoutMandat)), detail: 'Projets déjà reliés à un mandat', tone: 'diffusion', action: null },
        { label: 'Portefeuille', value: format(mandatStats.total), detail: 'Estimations visibles avec les filtres courants', tone: 'volume', action: null },
      ]
    }
    return [
      { label: 'À traiter', value: format(workItemsTotal || workItems.length), detail: 'Demandes à revoir dans les dossiers visibles', tone: 'demandes', action: 'correction_attente' },
      { label: 'Visibles', value: format(visibleDossiersCount), detail: 'Dossiers correspondant aux filtres actuels', tone: 'volume', action: 'all_annonces' },
      { label: 'Filtres actifs', value: format(activeFilters.length), detail: 'Critères qui réduisent le listing', tone: 'neutral', action: null },
    ]
  }, [activeFilters.length, mandatStats, screen, visibleDossiersCount, workItems.length, workItemsTotal])
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
      const postalCode = safeText(locality.code)
      const city = safeText(locality.ville)
      const civility = safeText(item.civilite)
      const firstName = safeText(item.prenom)
      const lastName = safeText(item.nom)
      return {
        id: `${index}-${lastName}`,
        name: [civility, firstName, lastName].filter(Boolean).join(' ') || `Contact ${index + 1}`,
        role: Array.isArray(item.typologie) ? item.typologie.join(', ') : '',
        phone: safeText(coords.portable) || safeText(coords.telephone),
        email: safeText(coords.email),
        address: safeText(locality.adresse),
        postalCode,
        city,
        civility,
        firstName,
        lastName,
        comment: sanitizeContactComment(item.commentaires as string | null | undefined),
        sourceId: safeText(item.id),
        archive: safeText(item.archive),
        dateCreated: safeText(item.dateenr),
        dateUpdated: safeText(item.datemaj),
        negotiatorId: safeText(item.id_negociateur),
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

  function openPriorityAction(action: HeaderMetricItem['action']) {
    if (!action) return
    if (screen === 'registre') {
      openRegisterDrilldown(action)
    } else {
      openMandatDrilldown(action)
    }
    setPriorityPanelOpen(false)
  }

  const priorityPanel = priorityPanelOpen ? (
    <div className="priority-dropdown" role="region" aria-label="Priorités de la vue">
      {viewPriorities.map((item) => (
        <button
          key={item.label}
          className={`priority-card tone-${item.tone} ${item.action ? 'is-clickable' : ''}`}
          type="button"
          onClick={() => openPriorityAction(item.action)}
          disabled={!item.action}
        >
          <span className="priority-card-icon" aria-hidden="true" />
          <span className="priority-card-copy">
            <strong>{item.label}</strong>
            <small>{item.detail}</small>
          </span>
          <em>{item.value}</em>
        </button>
      ))}
    </div>
  ) : null
  const responsiveExperience = useResponsiveExperience()

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

  const appModals = (
    <>
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
        {draftAnnonceModalOpen ? (
          <div className="modal-overlay" onClick={closeDraftAnnonceModal}>
            <section className="modal-panel modal-panel-wide draft-annonce-modal" onClick={(event) => event.stopPropagation()}>
              <div className="panel-head draft-annonce-head">
                <span className="modal-hero-icon modal-hero-icon-diffusion" aria-hidden="true" />
                <div>
                  <p className="eyebrow">Console Hektor</p>
                  <h3>Nouvelle annonce Hektor</h3>
                </div>
                <button className="ghost-button button-subtle" type="button" onClick={closeDraftAnnonceModal} disabled={draftAnnoncePending}>Fermer</button>
              </div>
              <p className="modal-subline">Cette action cree l annonce dans Hektor avec le contexte negociateur selectionne, sans diffusion automatique.</p>
              <form className="draft-annonce-form" onSubmit={handleCreateDraftAnnonce}>
                <section className="draft-annonce-intro">
                  <div>
                    <span>01</span>
                    <strong>Contexte Hektor</strong>
                    <small>Le brouillon est cree avec l acces negociateur choisi.</small>
                  </div>
                  <div>
                    <span>02</span>
                    <strong>Bien initial</strong>
                    <small>Les champs servent a pre-remplir Hektor puis l app se synchronise.</small>
                  </div>
                </section>
                <label className="filter-field draft-annonce-field-wide">
                  <span>Titre / repere interne</span>
                  <input value={draftAnnonceTitle} onChange={(event) => setDraftAnnonceTitle(event.target.value)} placeholder="Exemple : Maison test Saint-Etienne" />
                </label>
                <div className="draft-annonce-section-title">
                  <span>Compte</span>
                  <strong>Qui porte l annonce</strong>
                </div>
                <label className="filter-field">
                  <span>Agence</span>
                  <select value={draftAnnonceAgency} onChange={(event) => setDraftAnnonceAgency(event.target.value)} required>
                    <option value="">Choisir</option>
                    {filterCatalog.agencies.map((agency) => <option key={agency} value={agency}>{agency}</option>)}
                  </select>
                </label>
                <label className="filter-field">
                  <span>Negociateur Hektor</span>
                  <select
                    value={draftAnnonceNegotiatorId}
                    onChange={(event) => setDraftAnnonceNegotiatorId(event.target.value)}
                    disabled={profile?.role === 'commercial'}
                    required
                  >
                    <option value="">{profile?.role === 'commercial' ? 'Acces personnel' : 'Choisir'}</option>
                    {draftNegotiatorOptions.map((negotiator) => (
                      <option key={negotiator.idUser} value={negotiator.idUser}>
                        {negotiator.label}{negotiator.agenceNom ? ` - ${negotiator.agenceNom}` : ''}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="filter-field">
                  <span>Type Hektor</span>
                  <select value="Appartement" disabled>
                    <option value="Appartement">Appartement</option>
                  </select>
                </label>
                <div className="draft-annonce-section-title">
                  <span>Localisation</span>
                  <strong>Adresse privee</strong>
                </div>
                <label className="filter-field">
                  <span>Adresse</span>
                  <input value={draftAnnonceAddress} onChange={(event) => setDraftAnnonceAddress(event.target.value)} placeholder="Adresse privee" />
                </label>
                <label className="filter-field">
                  <span>Code postal</span>
                  <input value={draftAnnoncePostalCode} onChange={(event) => setDraftAnnoncePostalCode(event.target.value)} inputMode="numeric" />
                </label>
                <label className="filter-field">
                  <span>Ville</span>
                  <input value={draftAnnonceCity} onChange={(event) => setDraftAnnonceCity(event.target.value)} />
                </label>
                <div className="draft-annonce-section-title">
                  <span>Valeurs</span>
                  <strong>Prix et caracteristiques</strong>
                </div>
                <label className="filter-field">
                  <span>Prix</span>
                  <input value={draftAnnoncePrice} onChange={(event) => setDraftAnnoncePrice(event.target.value)} inputMode="numeric" placeholder="0" />
                </label>
                <label className="filter-field">
                  <span>Surface</span>
                  <input value={draftAnnonceSurface} onChange={(event) => setDraftAnnonceSurface(event.target.value)} inputMode="decimal" />
                </label>
                <label className="filter-field">
                  <span>Pieces</span>
                  <input value={draftAnnonceRoomCount} onChange={(event) => setDraftAnnonceRoomCount(event.target.value)} inputMode="numeric" />
                </label>
                <label className="filter-field">
                  <span>Chambres</span>
                  <input value={draftAnnonceBedroomCount} onChange={(event) => setDraftAnnonceBedroomCount(event.target.value)} inputMode="numeric" />
                </label>
                <label className="filter-field draft-annonce-field-wide">
                  <span>Note</span>
                  <textarea className="inline-textarea" value={draftAnnonceNote} onChange={(event) => setDraftAnnonceNote(event.target.value)} placeholder="Infos utiles pour completer l annonce ensuite" />
                </label>
                <section className="draft-annonce-warning">
                  <strong>Creation sans diffusion</strong>
                  <span>L'enrichissement complet, la validation et la diffusion resteront des actions separees.</span>
                </section>
                <div className="modal-actions">
                  <button className="ghost-button button-subtle" type="button" onClick={closeDraftAnnonceModal} disabled={draftAnnoncePending}>Annuler</button>
                  <button className="ghost-button button-primary" type="submit" disabled={draftAnnoncePending || !draftAnnonceAgency.trim() || !selectedDraftNegotiator}>
                    {draftAnnoncePending ? 'Creation...' : 'Creer l annonce'}
                  </button>
                </div>
              </form>
            </section>
          </div>
        ) : null}
        {deleteAnnonceTarget ? (
          <div className="modal-overlay" onClick={closeDeleteAnnonceModal}>
            <section className="modal-panel delete-annonce-modal" onClick={(event) => event.stopPropagation()}>
              <div className="panel-head delete-annonce-head">
                <span className="modal-hero-icon modal-hero-icon-danger" aria-hidden="true" />
                <div>
                  <p className="eyebrow">Administration Hektor</p>
                  <h3>Supprimer l'annonce</h3>
                </div>
                <button className="ghost-button button-subtle" type="button" onClick={closeDeleteAnnonceModal} disabled={deleteAnnoncePending}>Fermer</button>
              </div>
              <form className="delete-annonce-form" onSubmit={handleDeleteHektorAnnonce}>
                <section className="delete-annonce-warning">
                  <strong>{deleteAnnonceTarget.titre_bien || deleteAnnonceTarget.numero_dossier || `Annonce ${deleteAnnonceTarget.hektor_annonce_id}`}</strong>
                  <span>Cette demande supprime l'annonce dans Hektor avec une session administrateur, puis nettoie Supabase et les fichiers locaux connus.</span>
                </section>
                <label className="filter-field">
                  <span>Raison interne</span>
                  <textarea className="inline-textarea" value={deleteAnnonceReason} onChange={(event) => setDeleteAnnonceReason(event.target.value)} placeholder="Erreur de creation, doublon, test..." />
                </label>
                <label className="filter-field">
                  <span>Confirmation</span>
                  <input
                    value={deleteAnnonceConfirmText}
                    onChange={(event) => setDeleteAnnonceConfirmText(event.target.value)}
                    placeholder={`Tape : SUPPRIMER ${deleteAnnonceTarget.hektor_annonce_id}`}
                    autoComplete="off"
                    required
                  />
                </label>
                <div className="modal-actions">
                  <button className="ghost-button button-subtle" type="button" onClick={closeDeleteAnnonceModal} disabled={deleteAnnoncePending}>Annuler</button>
                  <button
                    className="ghost-button button-danger"
                    type="submit"
                    disabled={deleteAnnoncePending || deleteAnnonceConfirmText.trim() !== `SUPPRIMER ${deleteAnnonceTarget.hektor_annonce_id}`}
                  >
                    {deleteAnnoncePending ? 'Envoi...' : 'Supprimer dans Hektor'}
                  </button>
                </div>
              </form>
            </section>
          </div>
        ) : null}
        {requestModalOpen && requestModalMandat ? (
          <div className="modal-overlay" onClick={closeRequestModal}>
            <section
              className={`modal-panel request-modal-panel ${requestModalEffectiveType === 'demande_baisse_prix' ? 'request-modal-panel-price' : requestModalEffectiveType === 'demande_annulation_mandat' ? 'request-modal-panel-cancellation' : 'request-modal-panel-validation'}`}
              onClick={(event) => event.stopPropagation()}
            >
              <div className="panel-head request-modal-head">
                <span
                  className={`modal-hero-icon ${requestModalEffectiveType === 'demande_baisse_prix' ? 'modal-hero-icon-price' : requestModalEffectiveType === 'demande_annulation_mandat' ? 'modal-hero-icon-cancellation' : 'modal-hero-icon-validation'}`}
                  aria-hidden="true"
                />
                <div className="request-modal-title">
                  <p className="eyebrow">Gestion des demandes</p>
                  <h3>{requestModalRole === 'pauline' ? 'Traitement Pauline' : requestModalEffectiveType === 'demande_baisse_prix' ? 'Demande de baisse de prix' : requestModalEffectiveType === 'demande_annulation_mandat' ? 'Demande d annulation de mandat' : 'Demande de validation'}</h3>
                </div>
                {requestModalRole === 'pauline' && requestModalEffectiveType === 'demande_annulation_mandat' ? (
                  <button className="ghost-button button-subtle request-modal-hektor-link" type="button" onClick={() => openHektorMandatPrix(requestModalMandat.hektor_annonce_id)}>Lien Hektor</button>
                ) : null}
                <button className="ghost-button button-subtle request-modal-close" type="button" onClick={closeRequestModal}>Fermer</button>
              </div>
              <p className="modal-subline">{requestModalMandat.numero_dossier ?? '-'} - {requestModalMandat.numero_mandat ?? '-'} - {commercialDisplay(requestModalMandat)}</p>
              {requestModalEffectiveType !== 'demande_baisse_prix' ? (
                <section className="request-summary-card">
                  <div className="request-summary-hero">
                    <div className="request-summary-copy">
                      <p className="request-summary-kicker">{requestModalEffectiveType === 'demande_annulation_mandat' ? 'Annulation mandat' : 'Validation diffusion'}</p>
                      <h4 className="request-summary-heading">
                        {requestModalEffectiveType === 'demande_annulation_mandat'
                          ? requestModalRole === 'pauline'
                            ? 'Decision sur l annulation'
                            : requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger')
                              ? 'Correction prete a renvoyer'
                              : requestModalNegoLabel.includes('envoyee') || requestModalNegoLabel.includes('envoyée')
                                ? 'Demande deja transmise'
                                : 'Annulation en preparation'
                          : requestModalRole === 'pauline'
                          ? requestModalPaulineState?.label?.toLowerCase().includes('refusee')
                            ? 'Relecture avant retour'
                            : 'Decision de Pauline'
                            : requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger')
                            ? 'Correction prete a renvoyer'
                            : requestModalNegoLabel.includes('envoyee') || requestModalNegoLabel.includes('envoyée')
                              ? 'Demande deja transmise'
                              : 'Validation en preparation'}
                      </h4>
                      <p className="request-summary-note">
                        {requestModalEffectiveType === 'demande_annulation_mandat'
                          ? requestModalRole === 'pauline'
                            ? 'Controle le mandat dans Hektor via le lien puis accepte ou refuse la demande.'
                            : requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger')
                              ? 'La demande a ete completee. Tu peux la renvoyer a Pauline.'
                              : requestModalNegoLabel.includes('envoyee') || requestModalNegoLabel.includes('envoyée')
                                ? 'La demande est partie. Il reste a suivre le retour de Pauline.'
                                : 'Explique le motif d annulation pour que Pauline controle le mandat dans Hektor.'
                          : requestModalRole === 'pauline'
                          ? requestModalPaulineState?.label?.toLowerCase().includes('refusee')
                            ? 'Relis le dernier retour puis decide si le dossier peut repartir ou non.'
                            : 'Tout le contexte utile est centralise ici pour valider rapidement le bien.'
                          : requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger')
                            ? 'Le dossier a ete ajuste. Tu peux renvoyer une version propre a Pauline.'
                            : requestModalNegoLabel.includes('envoyee') || requestModalNegoLabel.includes('envoyée')
                              ? 'La demande est partie. Il reste a suivre le retour de validation.'
                              : 'Une fois approuvee, la diffusion et les passerelles par defaut seront activees automatiquement.'}
                      </p>
                    </div>
                    <div className="request-summary-state">
                      <StatusPill value={requestModalRole === 'pauline' ? (requestModalPaulineState?.label ?? 'A traiter') : requestModalNegoLabel} />
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
                      <strong>{requestModalEffectiveType === 'demande_annulation_mandat' ? 'Email commercial envoye' : 'Diffusion activee'}</strong>
                      <small>{requestModalEffectiveType === 'demande_annulation_mandat' ? 'Aucun automatisme Hektor' : 'Passerelles par defaut appliquees'}</small>
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
                      onChange={(event) => setRequestModalType(event.target.value as BusinessRequestType)}
                      disabled={Boolean(requestModalRequest && (requestModalRequest.request_status === 'pending' || requestModalRequest.request_status === 'in_progress' || requestModalRequest.request_status === 'waiting_commercial' || requestModalRequest.request_status === 'refused'))}
                    >
                      {requestTypeOptions.map((option) => (
                        <option
                          key={option.value}
                          value={option.value}
                          disabled={
                            (option.value === 'demande_baisse_prix' && !requestModalEligibleForPriceDrop) ||
                            (option.value === 'demande_annulation_mandat' && !requestModalEligibleForCancellation)
                          }
                        >
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
                <span>{requestModalRole === 'pauline' ? 'Message Pauline' : requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger') ? 'Message / correction pour Pauline' : requestModalEffectiveType === 'demande_baisse_prix' ? 'Contexte de la baisse de prix' : requestModalEffectiveType === 'demande_annulation_mandat' ? 'Contexte de l annulation' : 'Contexte pour Pauline'}</span>
                <textarea
                  className="inline-textarea"
                  value={requestModalComment}
                  onChange={(event) => setRequestModalComment(event.target.value)}
                  placeholder={
                    requestModalRole === 'pauline'
                      ? requestModalEffectiveType === 'demande_baisse_prix'
                        ? "Exemple : avenant signe controle, baisse de prix validee."
                        : requestModalEffectiveType === 'demande_annulation_mandat'
                          ? 'Exemple : mandat controle dans Hektor, annulation acceptee.'
                          : 'Exemple : dossier controle, validation accordee.'
                      : requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger')
                        ? requestModalEffectiveType === 'demande_baisse_prix'
                          ? "Exemple : avenant ajoute et corrige, merci de revoir la demande."
                          : requestModalEffectiveType === 'demande_annulation_mandat'
                            ? "Exemple : motif d'annulation complete, merci de revoir la demande."
                            : 'Exemple : pieces et informations corrigees, merci de revoir la demande.'
                        : requestModalEffectiveType === 'demande_baisse_prix'
                          ? "Exemple : avenant signe depose dans Hektor, merci de valider la baisse."
                          : requestModalEffectiveType === 'demande_annulation_mandat'
                            ? "Exemple : merci de controler l'annulation du mandat dans Hektor."
                            : 'Exemple : le mandat est pret, merci de valider le bien.'
                  }
                />
              </label>
              {requestModalRole === 'pauline' ? (
                <div className="admin-form-grid request-form-grid">
                  <label className="filter-field">
                    <span>Decision Pauline</span>
                    <select
                      value={requestModalDecision}
                      onChange={(event) => {
                        setRequestModalDecision(event.target.value)
                        setPriceDropCheckPrompt(null)
                        setValidationCheckPrompt(null)
                        setCancellationCheckPrompt(null)
                      }}
                    >
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
                      requestType: requestModalEffectiveType,
                      status: requestModalDecision,
                      response: requestModalComment,
                      refusalReason: requestModalRefusalReason,
                      followUpNeeded: requestModalDecision === 'refused',
                      followUpDays: requestModalDecision === 'refused' ? 2 : 0,
                      relaunchCount: requestModalRequest.relaunch_count ?? 0,
                    })}
                    disabled={
                      requestLoading ||
                      (requestModalDecision === 'accepted' && priceDropCheckPrompt?.kind === 'confirmed') ||
                      (requestModalDecision === 'accepted' && validationCheckPrompt?.kind === 'confirmed') ||
                      (requestModalDecision === 'accepted' && cancellationCheckPrompt?.kind === 'confirmed') ||
                      (requestModalDecision === 'refused' && !requestModalRefusalReason)
                    }
                  >
                    {requestLoading ? 'Enregistrement...' : requestModalDecision === 'accepted' ? (requestModalEffectiveType === 'demande_baisse_prix' ? 'Approuver la baisse' : requestModalEffectiveType === 'demande_annulation_mandat' ? 'Accepter l annulation' : 'Accepter') : requestModalDecision === 'refused' ? 'Refuser' : 'Enregistrer le traitement'}
                  </button>
                ) : (
                  <button
                    className="ghost-button button-primary"
                    type="button"
                    onClick={() => (requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger')) && requestModalRequest
                      ? handleSubmitDiffusionCorrection({ requestId: requestModalRequest.id, comment: requestModalComment })
                      : handleCreateDiffusionRequest({ mandatId: requestModalMandat.app_dossier_id, comment: requestModalComment, requestType: requestModalEffectiveType, requestedPrice: requestModalPriceValue })}
                    disabled={
                      requestPending ||
                      requestModalNegoLabel.includes('envoyee') || requestModalNegoLabel.includes('envoyée') ||
                      (requestModalEffectiveType === 'demande_baisse_prix' && (!requestModalEligibleForPriceDrop || !requestModalPriceValue.trim())) ||
                      (requestModalEffectiveType === 'demande_annulation_mandat' && !requestModalEligibleForCancellation)
                    }
                  >
                    {requestPending ? 'Envoi en cours...' : requestModalNegoLabel.includes('corriger') || requestModalNegoLabel.includes('Corriger') ? 'Envoyer la correction' : requestModalNegoLabel.includes('envoyee') || requestModalNegoLabel.includes('envoyée') ? 'Demande deja envoyee' : requestModalEffectiveType === 'demande_baisse_prix' ? 'Envoyer la demande de baisse' : requestModalEffectiveType === 'demande_annulation_mandat' ? 'Envoyer la demande d annulation' : 'Envoyer la demande de validation'}
                  </button>
                )}
              </div>
            </section>
          </div>
        ) : null}
        {priceDropCheckPrompt && requestModalOpen && requestModalEffectiveType === 'demande_baisse_prix' ? (
          <div className="modal-overlay price-drop-popup-overlay" role="presentation">
            <section
              className={`price-drop-popup price-drop-popup-${priceDropCheckPrompt.kind}`}
              role="dialog"
              aria-modal="true"
              aria-labelledby="price-drop-popup-title"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="price-drop-popup-icon" aria-hidden="true" />
              <p className="price-drop-popup-eyebrow">Contrôle prix Hektor</p>
              <h3 id="price-drop-popup-title">
                {priceDropCheckPrompt.kind === 'mismatch' ? 'Prix différent Hektor' : 'Prix confirmé'}
              </h3>
              <p className="price-drop-popup-message">{priceDropCheckPrompt.message}</p>
              <div className="price-drop-popup-prices">
                <span>Demande <strong>{formatPrice(priceDropCheckPrompt.requestedPrice)}</strong></span>
                <span>Hektor <strong>{formatPrice(priceDropCheckPrompt.observedPrice)}</strong></span>
              </div>
              <div className="price-drop-popup-actions">
                {priceDropCheckPrompt.kind === 'mismatch' ? (
                  <>
                    <button
                      className="ghost-button button-subtle"
                      type="button"
                      onClick={() => setPriceDropCheckPrompt(null)}
                    >
                      Fermer
                    </button>
                    <button
                      className="ghost-button button-primary"
                      type="button"
                      onClick={() => openHektorMandatPrix(priceDropCheckPrompt.hektorAnnonceId)}
                    >
                      Lien Hektor
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      className="ghost-button button-subtle"
                      type="button"
                      disabled={requestLoading || !priceDropCheckPrompt.pendingAction}
                      onClick={() => priceDropCheckPrompt.pendingAction && handleUpdateDiffusionRequest({
                        ...priceDropCheckPrompt.pendingAction,
                        priceDropChecked: true,
                        publishAfterPriceDrop: false,
                      })}
                    >
                      Non
                    </button>
                    <button
                      className="ghost-button button-primary"
                      type="button"
                      disabled={requestLoading || !priceDropCheckPrompt.pendingAction}
                      onClick={() => priceDropCheckPrompt.pendingAction && handleUpdateDiffusionRequest({
                        ...priceDropCheckPrompt.pendingAction,
                        priceDropChecked: true,
                        publishAfterPriceDrop: true,
                      })}
                    >
                      Oui
                    </button>
                  </>
                )}
              </div>
            </section>
          </div>
        ) : null}
        {validationCheckPrompt && requestModalOpen && requestModalEffectiveType === 'demande_diffusion' ? (
          <div className="modal-overlay price-drop-popup-overlay" role="presentation">
            <section
              className={`price-drop-popup price-drop-popup-${validationCheckPrompt.kind}`}
              role="dialog"
              aria-modal="true"
              aria-labelledby="validation-popup-title"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="price-drop-popup-icon" aria-hidden="true" />
              <p className="price-drop-popup-eyebrow">Validation Hektor</p>
              <h3 id="validation-popup-title">{validationCheckPrompt.title}</h3>
              <p className="price-drop-popup-message">{validationCheckPrompt.message}</p>
              {validationCheckPrompt.detail ? (
                <p className="price-drop-popup-detail">{validationCheckPrompt.detail}</p>
              ) : null}
              <div className="price-drop-popup-actions">
                {validationCheckPrompt.kind === 'mismatch' ? (
                  <>
                    <button
                      className="ghost-button button-subtle"
                      type="button"
                      onClick={() => setValidationCheckPrompt(null)}
                    >
                      Fermer
                    </button>
                    <button
                      className="ghost-button button-primary"
                      type="button"
                      onClick={() => openHektorMandatPrix(validationCheckPrompt.hektorAnnonceId)}
                    >
                      Lien Hektor
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      className="ghost-button button-subtle"
                      type="button"
                      disabled={requestLoading || !validationCheckPrompt.pendingAction}
                      onClick={() => validationCheckPrompt.pendingAction && handleUpdateDiffusionRequest({
                        ...validationCheckPrompt.pendingAction,
                        validationChecked: true,
                        runValidationWorkflow: false,
                      })}
                    >
                      Non
                    </button>
                    <button
                      className="ghost-button button-primary"
                      type="button"
                      disabled={requestLoading || !validationCheckPrompt.pendingAction}
                      onClick={() => validationCheckPrompt.pendingAction && handleUpdateDiffusionRequest({
                        ...validationCheckPrompt.pendingAction,
                        validationChecked: true,
                        runValidationWorkflow: true,
                      })}
                    >
                      Oui
                    </button>
                  </>
                )}
              </div>
            </section>
          </div>
        ) : null}
        {cancellationCheckPrompt && requestModalOpen && requestModalEffectiveType === 'demande_annulation_mandat' ? (
          <div className="modal-overlay price-drop-popup-overlay" role="presentation">
            <section
              className="price-drop-popup price-drop-popup-confirmed"
              role="dialog"
              aria-modal="true"
              aria-labelledby="cancellation-popup-title"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="price-drop-popup-icon" aria-hidden="true" />
              <p className="price-drop-popup-eyebrow">Annulation mandat</p>
              <h3 id="cancellation-popup-title">{cancellationCheckPrompt.title}</h3>
              <p className="price-drop-popup-message">{cancellationCheckPrompt.message}</p>
              {cancellationCheckPrompt.detail ? (
                <p className="price-drop-popup-detail">{cancellationCheckPrompt.detail}</p>
              ) : null}
              <div className="price-drop-popup-actions">
                <button
                  className="ghost-button button-subtle"
                  type="button"
                  disabled={requestLoading || !cancellationCheckPrompt.pendingAction}
                  onClick={() => cancellationCheckPrompt.pendingAction && handleUpdateDiffusionRequest({
                    ...cancellationCheckPrompt.pendingAction,
                    cancellationChecked: true,
                    unpublishAfterCancellation: false,
                  })}
                >
                  Non
                </button>
                <button
                  className="ghost-button button-primary"
                  type="button"
                  disabled={requestLoading || !cancellationCheckPrompt.pendingAction}
                  onClick={() => cancellationCheckPrompt.pendingAction && handleUpdateDiffusionRequest({
                    ...cancellationCheckPrompt.pendingAction,
                    cancellationChecked: true,
                    unpublishAfterCancellation: true,
                  })}
                >
                  Oui
                </button>
              </div>
            </section>
          </div>
        ) : null}
        {diffusionModalOpen && diffusionModalMandat ? (
          <div className="modal-overlay" onClick={closeDiffusionModal}>
            <section className="modal-panel modal-panel-wide diffusion-modal-panel" onClick={(event) => event.stopPropagation()}>
              <div className="panel-head diffusion-modal-head">
                <span className="modal-hero-icon modal-hero-icon-diffusion" aria-hidden="true" />
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
                    <article className="diffusion-state-item diffusion-state-item-wide diffusion-state-status">
                      <span>Statut Hektor</span>
                      <strong>{diffusionModalMandat.statut_annonce ?? '-'}</strong>
                    </article>
                    <article className="diffusion-state-item diffusion-state-diffusable">
                      <span>Diffusable</span>
                      <strong>{diffusableLabel(diffusionModalMandat.diffusable)}</strong>
                    </article>
                    <article className="diffusion-state-item diffusion-state-portals">
                      <span>Passerelles actives</span>
                      <strong>{String(diffusionEnabledCount)}</strong>
                    </article>
                    <article className="diffusion-state-item diffusion-state-item-wide diffusion-state-save">
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

    </>
  )

  if (!responsiveExperience.isDesktop) {
    const mobileScreenTitle = screenHeader.title
    const mobileUserLabel = resolvedUserNegotiatorContext?.commercial_nom || profile?.display_name || 'Utilisateur'
    const mobileAgencyLabel = resolvedUserNegotiatorContext?.agence_nom || 'Agence non détectée'
    const mobileMetrics = statsMetrics.slice(0, 5)
    const mobileDetailMessages = selectedDossierRequestEvents
      .filter((event) => parseJson<{ message?: string | null }>(event.payload_json, {}).message)
      .slice()
      .sort((a, b) => new Date(b.event_at).getTime() - new Date(a.event_at).getTime())
      .map((event) => ({
        id: `detail-message-${event.id}`,
        author: event.actor_name || event.event_label,
        date: event.event_at,
        message: parseJson<{ message?: string | null }>(event.payload_json, {}).message || '',
      }))

    return (
      <>
        <MobileLayout
        currentScreen={screen}
        title={mobileScreenTitle}
        isAdmin={isAdmin}
        userInitials={userInitials(profile?.display_name, session?.user.email ?? profile?.email ?? null)}
        userLabel={mobileUserLabel}
        agencyLabel={mobileAgencyLabel}
        onNavigate={openScreen}
        onOpenUsers={isAdmin ? () => void openUserTool() : undefined}
        onSignOut={session ? handleSignOut : undefined}
      >
        <section className="mobile-command-card">
          <label className="mobile-search-field">
            <span>Recherche</span>
            <input
              value={filters.query}
              onChange={(event) => updateFilter('query', event.target.value)}
              placeholder={screen === 'registre' ? 'Mandat, bien, mandant...' : 'Annonce, ville, négociateur...'}
            />
          </label>
          <div className="mobile-command-actions">
            {canCreateHektorDraftAnnonce ? <button className="mobile-draft-button" type="button" onClick={openDraftAnnonceModal}>Nouveau</button> : null}
            <button type="button" onClick={() => setFiltersOpen((open) => !open)}>{filtersOpen ? 'Fermer filtres' : 'Filtres'}</button>
            <button
              className={`mobile-stats-toggle ${mobileStatsOpen ? 'is-active' : ''}`}
              type="button"
              onClick={() => setMobileStatsOpen((open) => !open)}
              aria-expanded={mobileStatsOpen}
            >
              Stats
              {mobileMetrics.length > 0 ? <span>{mobileMetrics.length}</span> : null}
            </button>
            <button type="button" onClick={resetFilters}>Réinitialiser</button>
          </div>
          {mobileStatsOpen && mobileMetrics.length > 0 ? (
            <div className="mobile-metric-strip" aria-label="Indicateurs">
              {mobileMetrics.map((item) => (
                <button
                  key={`mobile-metric-${item.label}`}
                  className="mobile-metric-chip"
                  type="button"
                  onClick={item.action ? () => openPriorityAction(item.action) : undefined}
                  disabled={!item.action}
                >
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </button>
              ))}
            </div>
          ) : null}
        </section>

        {filtersOpen ? (
          <div className="filters-overlay mobile-filter-overlay" onClick={() => setFiltersOpen(false)}>
            <section className="filters-drawer" onClick={(event) => event.stopPropagation()}>
              <div className="filters-head">
                <div>
                  <p className="eyebrow">Filtres mobile</p>
                  <strong>{mobileScreenTitle}</strong>
                </div>
                <button className="ghost-button" type="button" onClick={() => setFiltersOpen(false)}>Fermer</button>
              </div>
              <div className="filter-grid">
                <FilterSelect label="Négociateur" value={filters.commercial} onChange={(value) => updateFilter('commercial', value)} options={[{ value: withoutCommercialFilterValue, label: 'Sans' }, ...filterCatalog.commercials]} />
                <FilterSelect label="Agence" value={filters.agency} onChange={(value) => updateFilter('agency', value)} options={filterCatalog.agencies} />
                <FilterSelect label="Statut" value={filters.statut} onChange={(value) => updateFilter('statut', value)} options={filterCatalog.statuts} />
                <FilterSelect label="Validation" value={filters.validationDiffusion} onChange={(value) => updateFilter('validationDiffusion', value)} options={filterCatalog.validationDiffusions} />
                <FilterSelect
                  label="Diffusable"
                  value={filters.diffusable}
                  onChange={(value) => updateFilter('diffusable', value)}
                  options={[
                    { value: 'diffusable', label: 'Oui' },
                    { value: 'non_diffusable', label: 'Non' },
                  ]}
                />
                <FilterSelect label="Passerelle" value={filters.passerelle} onChange={(value) => updateFilter('passerelle', value)} options={filterCatalog.passerelles} />
              </div>
            </section>
          </div>
        ) : null}

        {bootLoading && dossiers.length === 0 && workItems.length === 0 ? <section className="info-banner">Chargement initial des données...</section> : null}
        {noticeMessage ? <section className="info-banner">{noticeMessage}</section> : null}
        {errorMessage ? <section className="error-banner">{errorMessage}</section> : null}

        {screen === 'annonces' ? (
          <MobileDossierCards
            dossiers={visibleDossiers}
            total={dossiersTotal}
            loading={pageLoading}
            hektorActionJobs={activeHektorActionJobs}
            onFocusDossier={setSelectedDossierId}
            onOpenDetail={() => setDetailOpen(true)}
          />
        ) : screen === 'mandats' ? (
          <MobileMandatCards
            mandats={screenMandats}
            total={mandatsTotal}
            loading={mandatLoading}
            mode="active"
            onOpenDetailPage={openDossierDetailPage}
            onOpenRequestModal={openRequestModal}
          />
        ) : screen === 'estimations' ? (
          <MobileMandatCards
            mandats={screenMandats}
            total={mandatsTotal}
            loading={mandatLoading}
            mode="estimation"
            onOpenDetailPage={openDossierDetailPage}
            onOpenRequestModal={openRequestModal}
          />
        ) : screen === 'registre' ? (
          <MobileRegisterCards
            mandats={screenMandats}
            total={mandatsTotal}
            loading={mandatLoading}
            onSelectMandat={(rowId) => {
              setSelectedRegisterRowId(rowId)
              const row = screenMandats.find((item) => mandateRegisterRowKey(item) === rowId)
              if (row?.app_dossier_id) openDossierDetailPage(row.app_dossier_id)
            }}
          />
        ) : (
          <MobileMandatCards
            mandats={screenMandats}
            total={mandatsTotal}
            loading={requestLoading || mandatLoading}
            mode="active"
            onOpenDetailPage={openDossierDetailPage}
            onOpenRequestModal={(id) => openRequestModal(id, 'pauline')}
          />
        )}

        {detailOpen && selectedDossier ? (
          <div className="mobile-detail-overlay" onClick={closeDossierDetailPage}>
            <section className="mobile-detail-panel" onClick={(event) => event.stopPropagation()}>
              <MobileDossierDetail
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
                requestMessages={mobileDetailMessages}
                requestHistoryDiffusion={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')}
                requestMessagesDiffusion={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')}
                requestHistoryPriceDrop={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')}
                requestMessagesPriceDrop={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')}
                requestHistoryCancellation={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_annulation_mandat')}
                requestMessagesCancellation={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_annulation_mandat')}
                actionRequests={selectedDossierRequests}
                currentActionRequest={screen === 'suivi' ? selectedDossierRequest : null}
                actionRole={screen === 'suivi' ? 'pauline' : 'nego'}
                onOpenRequestModal={openRequestModal}
                onOpenDiffusionModal={openDiffusionModal}
                detailLoading={detailLoading}
                eyebrow="Mobile"
                backLabel="Fermer"
                onBack={closeDossierDetailPage}
                detailVariant={detailVariantForScreen(screen)}
                allowMarkValidation={(screen === 'suivi' || screen === 'mandats') && isAdmin}
                markValidationPending={detailValidationPending}
                validationDraft={detailValidationDraft}
                validationObserved={detailValidationObserved}
                validationSaved={detailValidationSaved}
                onSetValidation={handleSetSelectedDossierValidation}
                allowMarkDiffusable={(screen === 'suivi' || screen === 'mandats') && isAdmin}
                markDiffusablePending={detailDiffusablePending}
                onSetDiffusable={handleSetSelectedDossierDiffusable}
                diffusableDraft={detailDiffusableDraft}
                diffusableObserved={detailDiffusableObserved}
                diffusableSaved={detailDiffusableSaved}
                adminPilotSurface={(screen === 'mandats' || screen === 'suivi') ? 'both' : 'none'}
                onOpenImage={setDetailImageModalUrl}
                onDeleteAnnonce={isAdmin ? openDeleteAnnonceModal : undefined}
                onHektorActionJobCreated={rememberHektorActionJob}
              />
            </section>
          </div>
        ) : null}
        </MobileLayout>
        <HektorActionStatusPopup
          jobs={visibleHektorActionPopupJobs}
          linkedDossiers={hektorActionLinkedDossiers}
          onDismiss={dismissHektorActionPopup}
          onOpenAppDossier={(job) => void openHektorActionAppDossier(job)}
        />
        {appModals}
      </>
    )
  }

  return (
    <DesktopLayout>
    <div className="app-shell">
      <header className={`side-rail ${mobileMenuOpen ? 'is-mobile-menu-open' : ''}`}>
        <button
          className="mobile-nav-toggle"
          type="button"
          aria-label={mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
          aria-expanded={mobileMenuOpen}
          aria-controls="main-mobile-navigation"
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          <span aria-hidden="true" />
        </button>
        <div className="brand-block">
          <p className="eyebrow">GTI Immobilier</p>
          <h1>{screenHeader.title}</h1>
          {screenHeader.copy ? <p>{screenHeader.copy}</p> : null}
        </div>
        <nav id="main-mobile-navigation" className="screen-nav" aria-label="Navigation principale">
          <button className={`nav-button ${screen === 'mandats' ? 'is-active' : ''}`} type="button" onClick={() => openScreen('mandats')}>Annonces</button>
          <button className={`nav-button ${screen === 'estimations' ? 'is-active' : ''}`} type="button" onClick={() => openScreen('estimations')}>Estimations</button>
          <button className={`nav-button ${screen === 'registre' ? 'is-active' : ''}`} type="button" onClick={() => openScreen('registre')}>Mandats</button>
          {isAdmin ? <button className={`nav-button ${screen === 'suivi' ? 'is-active' : ''}`} type="button" onClick={() => openScreen('suivi')}>Suivi</button> : null}
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

      <div className="workspace-shell">
        <main className="content">
        {screen !== 'suivi' ? (
        <section className="hero">
          <div className="hero-stack">
              <div className="hero-top-row">
                <label className="search-box">
                  <span>Recherche rapide</span>
                  <input value={filters.query} onChange={(event) => updateFilter('query', event.target.value)} placeholder={screen === 'annonces' || screen === 'mandats' ? 'Rechercher une annonce, un bien, une ville...' : screen === 'registre' ? 'Mandat, dossier, bien, mandant, commercial, ville' : screen === 'estimations' ? 'Projet, adresse, ville, proprietaire, negociateur' : 'Dossier, mandat, commercial, ville'} />
                </label>
                <div className="hero-actions">
                  {canCreateHektorDraftAnnonce ? <button className="ghost-button button-primary draft-annonce-open-button" type="button" onClick={openDraftAnnonceModal}>Nouvelle annonce</button> : null}
                  <button className="ghost-button" type="button" onClick={() => setFiltersOpen((open) => !open)}>{filtersOpen ? 'Masquer les filtres' : 'Filtres'}</button>
                  <button className="ghost-button" type="button" onClick={resetFilters}>Réinitialiser</button>
                </div>
              </div>
            {screen === 'mandats' ? (
              <div className="header-kpi-stack">
                <div className="header-control-row">
                  <button
                    className={`ghost-button kpi-toggle-button ${commercialMetricsExpanded ? 'is-open' : ''}`}
                    type="button"
                    onClick={() => setCommercialMetricsExpanded((value) => !value)}
                  >
                    <span className="control-icon control-icon-stats" aria-hidden="true" />
                    <span>{commercialMetricsExpanded ? 'Masquer stats' : 'Stats'}</span>
                    <strong>{statsMetrics.length}</strong>
                  </button>
                  <button
                    className={`ghost-button kpi-toggle-button priority-toggle ${priorityPanelOpen ? 'is-open' : ''}`}
                    type="button"
                    onClick={() => setPriorityPanelOpen((value) => !value)}
                  >
                    <span className="control-icon control-icon-priority" aria-hidden="true" />
                    <span>Priorités</span>
                    <strong>{viewPriorities.length}</strong>
                  </button>
                </div>
                {priorityPanel}
                {commercialMetricsExpanded ? (
                  <div className="header-kpis header-kpis-secondary">
                    {statsMetrics.map((item) => (
                      <article
                        key={item.label}
                        className={`header-kpi-card tone-${item.tone} ${item.action ? 'is-clickable' : ''} ${item.action && item.action === activeMandatKpiAction ? 'is-active' : ''}`}
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
              <div className="header-kpi-stack">
                <div className="header-control-row is-inline">
                  <button
                    className={`ghost-button kpi-toggle-button ${commercialMetricsExpanded ? 'is-open' : ''}`}
                    type="button"
                    onClick={() => setCommercialMetricsExpanded((value) => !value)}
                  >
                    <span className="control-icon control-icon-stats" aria-hidden="true" />
                    <span>{commercialMetricsExpanded ? 'Masquer stats' : 'Stats'}</span>
                    <strong>{statsMetrics.length}</strong>
                  </button>
                  <button
                    className={`ghost-button kpi-toggle-button priority-toggle ${priorityPanelOpen ? 'is-open' : ''}`}
                    type="button"
                    onClick={() => setPriorityPanelOpen((value) => !value)}
                  >
                    <span className="control-icon control-icon-priority" aria-hidden="true" />
                    <span>Priorités</span>
                    <strong>{viewPriorities.length}</strong>
                  </button>
                </div>
                {priorityPanel}
                {commercialMetricsExpanded ? (
                  <div className="header-kpis header-kpis-secondary">
                    {statsMetrics.map((item) => (
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
                ) : null}
              </div>
            ) : (
              <div className="header-kpi-stack">
                <div className="header-control-row is-inline">
                  <button
                    className={`ghost-button kpi-toggle-button ${commercialMetricsExpanded ? 'is-open' : ''}`}
                    type="button"
                    onClick={() => setCommercialMetricsExpanded((value) => !value)}
                  >
                    <span className="control-icon control-icon-stats" aria-hidden="true" />
                    <span>{commercialMetricsExpanded ? 'Masquer stats' : 'Stats'}</span>
                    <strong>{statsMetrics.length}</strong>
                  </button>
                  <button
                    className={`ghost-button kpi-toggle-button priority-toggle ${priorityPanelOpen ? 'is-open' : ''}`}
                    type="button"
                    onClick={() => setPriorityPanelOpen((value) => !value)}
                  >
                    <span className="control-icon control-icon-priority" aria-hidden="true" />
                    <span>Priorités</span>
                    <strong>{viewPriorities.length}</strong>
                  </button>
                </div>
                {priorityPanel}
                {commercialMetricsExpanded ? (
                  <div className="header-kpis header-kpis-secondary">
                    {statsMetrics.map((item) => (
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
            )}
          </div>
        </section>
        ) : null}

        {filtersOpen ? <div className="filters-overlay" onClick={() => setFiltersOpen(false)}>
          <section className="filters-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="filters-head">
              <div>
                <p className="eyebrow">{screen === 'annonces' ? 'Filtres annonces' : screen === 'mandats' ? 'Filtres annonces actives' : screen === 'estimations' ? 'Filtres estimations' : screen === 'registre' ? 'Filtres registre' : 'Filtres suivi administratif'}</p>
                <strong>{screen === 'annonces' ? 'Appliqués côté serveur' : screen === 'mandats' ? 'Projets, mandats et diffusion' : screen === 'estimations' ? 'Futurs mandats potentiels' : screen === 'registre' ? 'Mandats avec numéro' : 'Demandes et parc mandat'}</strong>
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
            ) : screen === 'estimations' ? (
              <>
                <FilterSelect label="Negociateur" value={filters.commercial} onChange={(value) => updateFilter('commercial', value)} options={[{ value: withoutCommercialFilterValue, label: 'Sans' }, ...filterCatalog.commercials]} />
                <FilterSelect label="Agence" value={filters.agency} onChange={(value) => updateFilter('agency', value)} options={filterCatalog.agencies} />
                <FilterSelect
                  label="Archive"
                  value={filters.archive}
                  onChange={(value) => updateFilter('archive', value)}
                  options={[
                    { value: activeArchiveFilterValue, label: 'Actives' },
                    { value: archivedFilterValue, label: 'Archives' },
                  ]}
                />
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
                <FilterSelect
                  label="Etat du mandat"
                  value={filters.mandateState}
                  onChange={(value) => updateFilter('mandateState', value)}
                  options={[
                    { value: 'En cours', label: 'En cours' },
                    { value: 'Annulé', label: 'Annulé' },
                  ]}
                />
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
        {noticeMessage ? <section className="info-banner">{noticeMessage}</section> : null}
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
            }))} requestHistoryDiffusion={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')} requestMessagesDiffusion={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_diffusion')} requestHistoryPriceDrop={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')} requestMessagesPriceDrop={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_baisse_prix')} requestHistoryCancellation={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_annulation_mandat')} requestMessagesCancellation={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_annulation_mandat')} actionRequests={selectedDossierRequests} actionRole="nego" onOpenRequestModal={openRequestModal} onOpenDiffusionModal={openDiffusionModal} onHektorActionJobCreated={rememberHektorActionJob} detailLoading={detailLoading} onBack={closeDossierDetailPage} />
        ) : screen === 'annonces' ? (
          <StockScreen dossiers={visibleDossiers} dossiersTotal={dossiersTotal} dossierPage={dossierPage} dossierTotalPages={dossierTotalPages} hektorActionJobs={activeHektorActionJobs} onPrevDossier={() => setDossierPage((page) => Math.max(1, page - 1))} onNextDossier={() => setDossierPage((page) => Math.min(dossierTotalPages, page + 1))} onGoToDossierPage={(page) => setDossierPage(Math.min(dossierTotalPages, Math.max(1, page)))} selectedDossier={selectedDossier} address={address} linkedWorkItems={linkedWorkItems} workItems={workItems} workItemsTotal={workItemsTotal} workItemPage={workItemPage} workItemTotalPages={workItemTotalPages} onPrevWorkItem={() => setWorkItemPage((page) => Math.max(1, page - 1))} onNextWorkItem={() => setWorkItemPage((page) => Math.min(workItemTotalPages, page + 1))} onGoToWorkItemPage={(page) => setWorkItemPage(Math.min(workItemTotalPages, Math.max(1, page)))} onSelectDossier={setSelectedDossierId} onOpenDetail={() => setDetailOpen(true)} onFocusDossier={(id) => setSelectedDossierId(id)} pageLoading={pageLoading} hasActiveFilters={activeFilters.length > 0} onResetFilters={resetFilters} />
        ) : screen === 'mandats' ? (
          <MandatsScreen
            mandats={screenMandats}
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
            title={mandatDrilldownLabel?.title ?? 'Annonces actives'}
            mode="active"
          />
        ) : screen === 'estimations' ? (
          <MandatsScreen
            mandats={screenMandats}
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
            eyebrow="Estimations"
            title="Futurs mandats potentiels"
            mode="estimation"
          />
        ) : screen === 'registre' ? (
          <MandatRegisterScreen
            mandats={screenMandats}
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
            mandats={screenMandats}
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
            onSetRequestFilter={setSuiviRequestFilter}
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
                requestHistoryCancellation={buildRequestHistoryForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_annulation_mandat')}
                requestMessagesCancellation={buildRequestMessagesForType(selectedDossierRequests, selectedDossierAllRequestEvents, 'demande_annulation_mandat')}
                actionRequests={selectedDossierRequests}
                currentActionRequest={screen === 'suivi' ? selectedDossierRequest : null}
                actionRole={screen === 'suivi' ? 'pauline' : 'nego'}
                onOpenRequestModal={openRequestModal}
                onOpenDiffusionModal={openDiffusionModal}
                detailLoading={detailLoading}
                eyebrow={detailEyebrowForScreen(screen)}
                backLabel="Fermer"
                onBack={closeDossierDetailPage}
                detailVariant={detailVariantForScreen(screen)}
                allowMarkValidation={(screen === 'suivi' || screen === 'mandats') && isAdmin}
                markValidationPending={detailValidationPending}
                validationDraft={detailValidationDraft}
                validationObserved={detailValidationObserved}
                validationSaved={detailValidationSaved}
                onSetValidation={handleSetSelectedDossierValidation}
                allowMarkDiffusable={(screen === 'suivi' || screen === 'mandats') && isAdmin}
                markDiffusablePending={detailDiffusablePending}
                onSetDiffusable={handleSetSelectedDossierDiffusable}
                diffusableDraft={detailDiffusableDraft}
                diffusableObserved={detailDiffusableObserved}
                diffusableSaved={detailDiffusableSaved}
                adminPilotSurface={(screen === 'mandats' || screen === 'suivi') ? 'both' : 'none'}
                onOpenImage={setDetailImageModalUrl}
                onDeleteAnnonce={isAdmin ? openDeleteAnnonceModal : undefined}
                onHektorActionJobCreated={rememberHektorActionJob}
              />
            </section>
          </div>
        ) : null}
        <HektorActionStatusPopup
          jobs={visibleHektorActionPopupJobs}
          linkedDossiers={hektorActionLinkedDossiers}
          onDismiss={dismissHektorActionPopup}
          onOpenAppDossier={(job) => void openHektorActionAppDossier(job)}
        />
        {appModals}
        </main>
      </div>

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
    </DesktopLayout>
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
  hektorActionJobs: ConsoleJob[]
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
        {props.hektorActionJobs.length > 0 ? (
          <div className="hektor-job-strip">
            {props.hektorActionJobs.map((job) => (
              <article key={job.id} className={`hektor-job-card hektor-job-card-${hektorActionJobTone(job)}`}>
                <span>{hektorActionJobLabel(job)}</span>
                <strong>{hektorActionJobTitle(job)}</strong>
                <small>{hektorActionJobDetail(job)}</small>
              </article>
            ))}
          </div>
        ) : null}
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
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
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
  mode?: 'active' | 'estimation'
}) {
  const isEstimationMode = props.mode === 'estimation'
  const listingTotalLabel = `${new Intl.NumberFormat('fr-FR').format(props.mandatsTotal)} ${isEstimationMode ? 'estimations' : 'annonces actives'}`
  return (
    <section className={`panel-grid ${isEstimationMode ? 'panel-grid-estimation' : 'panel-grid-active-listing'}`}>
      <section className={`panel panel-wide ${isEstimationMode ? 'panel-estimation-listing' : 'panel-active-listing'}`}>
        <div className="panel-head">
          <div className="listing-title-stack">
            <h3>{props.title ?? 'Liste des annonces'}</h3>
            <span className="listing-total-label">{listingTotalLabel}</span>
          </div>
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
        <div className={`table-wrap listing-table-wrap ${isEstimationMode ? 'listing-table-estimation' : 'listing-table-active'} ${props.loading ? 'is-refreshing' : ''}`}>
          {props.loading ? <div className="listing-loading-banner">Chargement du listing...</div> : null}
          <table>
            <thead>
              {isEstimationMode ? (
                <tr><th>Projet</th><th>Bien</th><th>Negociateur</th><th>Avancement</th><th>Photo</th><th>Actions</th></tr>
              ) : (
                <tr><th>Mandat</th><th>Bien</th><th>Negociateur</th><th>Statut</th><th className="portal-col">LBC</th><th className="portal-col">BI</th><th className="portal-col">GTI</th><th>Photo</th><th>Actions</th></tr>
              )}
            </thead>
            <tbody>
              {props.mandats.map((item) => {
                const isSelected = item.app_dossier_id === props.selectedMandat?.app_dossier_id
                const activeRequest = latestDiffusionRequest(props.requests, item.app_dossier_id)
                const hasLeboncoin = hasPortalEnabled(item, ['leboncoin'])
                const hasBienici = hasPortalEnabled(item, ['bienici'])
                const hasSiteGti = isSiteGtiEnabled(item)
                const project = projectIdentityLines(item)
                return (
                  <Fragment key={item.app_dossier_id}>
                    <tr
                      className={`${isSelected ? 'is-selected' : ''} ${props.loading ? 'is-refreshing-row' : ''}`.trim()}
                      onClick={() => {
                        props.onSelectMandat(item.app_dossier_id)
                        props.onOpenDetailPage(item.app_dossier_id)
                      }}
                    >
                      {isEstimationMode ? (
                        <td className="estimation-project-cell"><strong>{project.title}</strong><span>{project.mandate}</span><span>{project.context}</span></td>
                      ) : (
                        <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.ville ?? '-'}</span></td>
                      )}
                      <td className={isEstimationMode ? 'estimation-property-cell' : undefined}><strong>{item.titre_bien}</strong><span>{propertyTypeLabel(item.type_bien)}</span><span>{item.numero_dossier ?? '-'}</span></td>
                      <td className={isEstimationMode ? 'estimation-negotiator-cell' : undefined}><strong>{commercialDisplay(item)}</strong><span>{item.agence_nom ?? '-'}</span></td>
                      {isEstimationMode ? (
                        <td className="estimation-progress-cell"><StatusPill value={listingProgressLabel(item)} /><small>{item.statut_annonce ?? '-'}</small></td>
                      ) : (
                        <>
                          <td><StatusPill value={item.statut_annonce} /></td>
                          <td className="portal-cell"><PortalStatusMark enabled={hasLeboncoin} /></td>
                          <td className="portal-cell"><PortalStatusMark enabled={hasBienici} /></td>
                          <td className="portal-cell"><PortalStatusMark enabled={hasSiteGti} /></td>
                        </>
                      )}
                      <td className={isEstimationMode ? 'estimation-photo-cell' : undefined}><ListingThumbnail url={item.photo_url_listing} imagesPreviewJson={item.images_preview_json} title={item.titre_bien} /></td>
                      <td>
                        <div className="row-actions">
                          {isEstimationMode ? (
                            <button className="ghost-button estimation-action-button" type="button" onClick={(event) => { event.stopPropagation(); props.onOpenDetailPage(item.app_dossier_id) }}>Voir le projet</button>
                          ) : (
                            <MandatActionMenu mandat={item} role="nego" requests={props.requests} onOpenRequestModal={props.onOpenRequestModal} onOpenDiffusionModal={props.onOpenDiffusionModal} />
                          )}
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
  const selectedContactItems = parseJson<Array<Record<string, unknown>>>(String(selectedDetailPayload.proprietaires_json ?? '[]'), []).map((item, index) => {
    const coords = (item.coordonnees as Record<string, unknown> | undefined) ?? {}
    const locality = ((item.localite as Record<string, unknown> | undefined)?.localite as Record<string, unknown> | undefined) ?? {}
    return {
      id: `register-contact-${index}-${safeText(item.nom)}`,
      name: [safeText(item.civilite), safeText(item.prenom), safeText(item.nom)].filter(Boolean).join(' ') || `Contact ${index + 1}`,
      role: Array.isArray(item.typologie) ? item.typologie.join(', ') : 'Mandant',
      phone: safeText(coords.portable) || safeText(coords.telephone),
      email: safeText(coords.email),
      address: [safeText(locality.adresse), safeText(locality.code), safeText(locality.ville)].filter(Boolean).join(', '),
      comment: sanitizeContactComment(item.commentaires as string | null | undefined),
    }
  })
  const selectedMandateLines = selectedDetail ? [
    ['Numero', selectedDetail.numero_mandat ?? '-'] as [string, string],
    ['Type', selectedDetail.mandat_type ?? selectedDetail.mandat_type_source ?? '-'] as [string, string],
    ['Debut', formatDate(selectedDetail.mandat_date_debut)] as [string, string],
    ['Fin', formatDate(selectedDetail.mandat_date_fin)] as [string, string],
    ['Montant', formatPrice(selectedDetail.mandat_montant ?? selectedDetail.prix)] as [string, string],
    ['Validation', selectedDetail.validation_diffusion_state ?? '-'] as [string, string],
    ['Diffusable', mandateRegisterDiffusableLabel(selectedDetail.diffusable)] as [string, string],
    ['Commercial', selectedDetail.commercial_nom ?? '-'] as [string, string],
    ['Agence', selectedDetail.agence_nom ?? '-'] as [string, string],
  ] : []
  const selectedMandantsLabel = selectedDetail ? mandateRegisterMandantsLabel(selectedDetail) : ''

  return (
    <section className="panel-grid">
      <section className="panel panel-wide">
        <div className="panel-head">
          <div><h3>Registre des mandats</h3></div>
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
                    className={`${mandateLifecycleRowClass(item)} ${isSelected ? 'is-selected' : ''}`.trim()}
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
                        <StatusPill value={mandateRegisterSourceBadge(item)} />
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
            <button className="mandate-register-close" type="button" onClick={() => setDetailOpen(false)}>Fermer</button>
            <div className="panel-head">
              <div>
                <p className="eyebrow">Fiche mandat</p>
                <h3>{selectedDetail.numero_mandat ?? '-'} · {selectedDetail.titre_bien}</h3>
                <p className="mandate-register-subtitle">{selectedDetail.register_source_kind === 'historique' ? 'Mandat historique' : 'Mandat actif'} · {selectedDetail.numero_dossier ?? '-'}</p>
              </div>
              <div className="row-actions">
                <button className="ghost-button button-subtle" type="button" onClick={() => setDetailOpen(false)}>Fermer</button>
              </div>
            </div>
            <div className="detail-stack detail-stack-rich">
              <article className="detail-card mandate-sheet-hero-card">
                <div className="mandate-sheet-hero-layout">
                  <div className="mandate-sheet-visual">
                    <div className="mandate-sheet-media">
                      {selectedImageUrl ? <img src={selectedImageUrl} alt={selectedDetail.titre_bien} loading="lazy" /> : <div className="detail-card-hero-placeholder">Mandat</div>}
                    </div>
                    <div className="mandate-sheet-visual-caption">
                      <span>Mandat</span>
                      <strong>{selectedDetail.numero_mandat ?? '-'}</strong>
                    </div>
                  </div>
                  <div className="mandate-sheet-summary">
                    <div className="mandate-sheet-title-row">
                      <span className="mandate-register-kicker">Mandat {selectedDetail.numero_mandat ?? '-'}</span>
                      <div className="tag-row">
                        <StatusPill value={selectedDetail.statut_annonce} />
                        <StatusPill value={mandateRegisterSourceLabel(selectedDetail)} />
                        {(selectedDetail.register_version_count ?? 1) > 1 ? <StatusPill value={`${selectedDetail.register_version_count} versions`} /> : null}
                        {(selectedDetail.register_embedded_avenant_count ?? 0) > 0 ? <StatusPill value={`${selectedDetail.register_embedded_avenant_count} avenant${(selectedDetail.register_embedded_avenant_count ?? 0) > 1 ? 's' : ''}`} /> : null}
                      </div>
                    </div>
                    <strong>{selectedDetail.titre_bien}</strong>
                    <p>{String(selectedDetailPayload.adresse_detail ?? selectedDetail.adresse_detail ?? selectedDetail.adresse_privee_listing ?? selectedDetail.ville ?? '-')}</p>
                    <div className="mandate-sheet-actions">
                      {Boolean(selectedDetail.register_detail_available) ? (
                        <button
                          className="ghost-button mandate-register-link primary"
                          type="button"
                          onClick={() => {
                            setDetailOpen(false)
                            props.onOpenDetailPage(Number(selectedDetail.app_dossier_id))
                          }}
                        >
                          Fiche bien
                        </button>
                      ) : null}
                      <button className="ghost-button mandate-register-link" type="button" onClick={() => openHektorAnnonce(selectedDetail.hektor_annonce_id)}>Hektor</button>
                    </div>
                  </div>
                </div>
              </article>
              <div className="mandate-register-sections">
                <article className="detail-subsection detail-mandate-section mandate-register-section">
                  <div className="section-header">
                    <DetailSectionTitle icon="mandate" title="Detail mandat" />
                    <strong className="mandate-section-amount">{formatPrice(selectedDetail.mandat_montant ?? selectedDetail.prix)}</strong>
                  </div>
                  <div className="detail-entity-list detail-mandat-list">
                    <article className="detail-entity-card detail-mandat-card">
                      <strong>Mandat {selectedDetail.numero_mandat ?? '-'}</strong>
                      <div className="detail-mandat-grid">
                        {selectedMandateLines.map(([label, value]) => (
                          <div key={`register-mandate-${label}`} className={`detail-mandat-cell ${label === 'Montant' ? 'is-accent' : ''}`}>
                            <span>{label}</span>
                            <strong>{value || '-'}</strong>
                          </div>
                        ))}
                      </div>
                    </article>
                  </div>
                </article>
                <article className="detail-subsection detail-contact-section mandate-register-section">
                  <div className="section-header">
                    <DetailSectionTitle icon="contact" title="Contact" />
                    {selectedContactItems.length > 0 ? <span>{selectedContactItems.length} contact{selectedContactItems.length > 1 ? 's' : ''}</span> : null}
                  </div>
                  <div className="detail-entity-list detail-contact-list">
                    {selectedContactItems.length > 0 ? selectedContactItems.map((contact, index) => (
                      <article key={contact.id} className={`detail-entity-card detail-contact-card ${index === 0 ? 'detail-contact-card-primary' : ''}`}>
                        <div className="detail-contact-head">
                          <div className={`detail-contact-avatar ${index > 0 ? 'is-secondary' : ''}`}>{userInitials(contact.name, contact.email)}</div>
                          <div className="detail-contact-identity">
                            <strong>{contact.name}</strong>
                            <span>{contact.role || 'Mandant'}</span>
                          </div>
                        </div>
                        <div className="detail-entity-lines detail-contact-lines">
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
                    )) : (
                      <article className="detail-entity-card detail-contact-card detail-contact-card-primary">
                        <div className="detail-contact-head">
                          <div className="detail-contact-avatar">{userInitials(selectedMandantsLabel, null)}</div>
                          <div className="detail-contact-identity">
                            <strong>Mandant(s)</strong>
                            <span>{mandateRegisterSourceLabel(selectedDetail)}</span>
                          </div>
                        </div>
                        <div className="detail-entity-lines detail-contact-lines">
                          <div className="detail-entity-line detail-entity-line-full">
                            <span>Nom(s)</span>
                            <strong>{selectedMandantsLabel || '-'}</strong>
                          </div>
                          {selectedDetail.mandat_note ? (
                            <div className="detail-entity-line detail-entity-line-full detail-contact-note">
                              <span>Note mandat</span>
                              <strong>{selectedDetail.mandat_note}</strong>
                            </div>
                          ) : null}
                        </div>
                      </article>
                    )}
                  </div>
                </article>
              </div>
              <div className="mandate-sheet-secondary-grid">
                <article className="detail-card mandate-sheet-section mandate-price-section">
                  <PriceChangeHistoryCard
                    source={selectedDetailPayload.price_change_events_json ? selectedDetailPayload : selectedDetail}
                    title="Historique des prix"
                    emptyLabel="Aucun changement de prix historisé pour ce mandat."
                  />
                </article>
                <article className="detail-card mandate-sheet-section">
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
                <article className="detail-card mandate-sheet-section mandate-avenants-section">
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
                  <td><StatusPill value={item.statut_annonce} /><small>{item.archive === '1' ? 'Archive' : 'Actif'}</small></td>
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
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
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
                        <td><strong>{requestTypeLabel(item.request_type)}</strong><span>N° demande {requestNumberLabel(item)}</span><span>{item.numero_mandat ?? item.numero_dossier ?? '-'}</span><span>{formatDate(item.requested_at)}</span></td>
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
                      <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.agence_nom ?? '-'}</span></td>
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
                      <td><StatusPill value={item.statut_annonce} /><small>{item.archive === '1' ? 'Archive' : 'Actif'}</small></td>
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
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
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
  requestFilter?: 'pending_or_in_progress' | 'accepted_history' | 'refused' | 'waiting_correction' | 'anomalies' | 'price_alert' | 'portfolio' | null
  onSetRequestFilter: (value: 'pending_or_in_progress' | 'accepted_history' | 'refused' | 'waiting_correction' | 'anomalies' | 'price_alert' | 'portfolio' | null) => void
}) {
  if (!props.isAdmin) {
    return <section className="panel"><p className="empty-state">Cette vue est reservee aux administrateurs.</p></section>
  }
  const [secondaryKpisOpen, setSecondaryKpisOpen] = useState(false)
  const [priorityPanelOpen, setPriorityPanelOpen] = useState(false)
  const [activeAnomalyType, setActiveAnomalyType] = useState<MandateAnomalyType>('all')

  const activeSuiviFilter = props.requestFilter ?? 'pending_or_in_progress'

  const requestRowsSource = activeSuiviFilter === 'accepted_history'
    ? props.mandats
        .filter((item) => Boolean((item.numero_mandat ?? '').trim()))
        .flatMap((item) => {
          const diffusionRequest = props.requests
            .filter((request) => request.app_dossier_id === item.app_dossier_id && normalizeRequestType(request.request_type) === 'demande_diffusion' && request.request_status === 'accepted')
            .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())[0]
          const priceDropRequest = props.requests
            .filter((request) => request.app_dossier_id === item.app_dossier_id && normalizeRequestType(request.request_type) === 'demande_baisse_prix' && request.request_status === 'accepted')
            .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())[0]
          const cancellationRequest = props.requests
            .filter((request) => request.app_dossier_id === item.app_dossier_id && normalizeRequestType(request.request_type) === 'demande_annulation_mandat' && request.request_status === 'accepted')
            .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())[0]
          return [diffusionRequest, priceDropRequest, cancellationRequest].filter(Boolean).map((request) => ({ mandat: item, request: request as DiffusionRequest }))
        })
    : props.mandats
        .filter((item) => Boolean((item.numero_mandat ?? '').trim()))
        .flatMap((item) => {
          const diffusionRequest = latestDiffusionRequest(props.requests, item.app_dossier_id, 'demande_diffusion')
          const priceDropRequest = latestDiffusionRequest(props.requests, item.app_dossier_id, 'demande_baisse_prix')
          const cancellationRequest = latestDiffusionRequest(props.requests, item.app_dossier_id, 'demande_annulation_mandat')
          return [diffusionRequest, priceDropRequest, cancellationRequest].filter(Boolean).map((request) => ({ mandat: item, request: request as DiffusionRequest }))
        })

  const pendingRows = requestRowsSource.filter((row) => row.request.request_status === 'pending' || row.request.request_status === 'in_progress')
  const acceptedRows = requestRowsSource.filter((row) => row.request.request_status === 'accepted')
  const refusedRows = requestRowsSource.filter((row) => row.request.request_status === 'refused')
  const anomalyRows = props.mandats.filter((item) =>
    Boolean((item.numero_mandat ?? '').trim()) && (
      hasCancelledMandateExposureAnomaly(item) ||
      (shouldTreatAsPublishableAnomaly(item.statut_annonce) && (item.diffusable ?? '0') === '1' && !item.nb_portails_actifs) ||
      ((item.diffusable ?? '0') !== '1' && Boolean(item.nb_portails_actifs)) ||
      Boolean(item.has_diffusion_error) ||
      !item.numero_mandat
    ),
  )
  const anomalyTypeKeys: MandateAnomalyType[] = [
    'all',
    'missing_mandate',
    'cancelled_exposed',
    'not_published',
    'unauthorized_publication',
    'gateway_error',
  ]
  const anomalyTypeOptions: Array<{ key: MandateAnomalyType; label: string; count: number }> = anomalyTypeKeys.map((key) => ({
    key,
    label: mandateAnomalyTypeLabel(key),
    count: key === 'all' ? anomalyRows.length : anomalyRows.filter((item) => mandateAnomalyType(item) === key).length,
  }))
  const visibleAnomalyRows = activeAnomalyType === 'all'
    ? anomalyRows
    : anomalyRows.filter((item) => mandateAnomalyType(item) === activeAnomalyType)
  const priceAlertRows = props.mandats
    .filter((item) => Boolean((item.numero_mandat ?? '').trim()))
    .map((item) => {
      const acceptedPriceDrop = props.requests
        .filter((request) =>
          request.app_dossier_id === item.app_dossier_id &&
          normalizeRequestType(request.request_type) === 'demande_baisse_prix' &&
          request.request_status === 'accepted',
        )
        .sort((a, b) => new Date(requestTimelineDate(b)).getTime() - new Date(requestTimelineDate(a)).getTime())[0] ?? null
      const hasPriceChange = Number(item.price_change_event_count ?? 0) > 0
      const priceChangedAt = new Date(item.price_change_last_detected_at ?? 0).getTime()
      const acceptedAt = acceptedPriceDrop ? new Date(requestTimelineDate(acceptedPriceDrop)).getTime() : 0
      const isAlert =
        (hasPriceChange && !acceptedPriceDrop) ||
        (Boolean(acceptedPriceDrop) && (!hasPriceChange || priceChangedAt < acceptedAt))
      return isAlert ? { mandat: item, request: acceptedPriceDrop } : null
    })
    .filter(Boolean) as Array<{ mandat: MandatRecord; request: DiffusionRequest | null }>
  const portfolioRows = props.mandats.slice()

  const suiviRequestRows = requestRowsSource
    .filter((row) => {
      if (activeSuiviFilter === 'pending_or_in_progress') return row.request.request_status === 'pending' || row.request.request_status === 'in_progress'
      if (activeSuiviFilter === 'accepted_history') return row.request.request_status === 'accepted'
      if (activeSuiviFilter === 'refused') return row.request.request_status === 'refused'
      return true
    })
    .slice()
    .sort((a, b) => {
      const dateA = new Date(requestTimelineDate(a.request) ?? 0).getTime()
      const dateB = new Date(requestTimelineDate(b.request) ?? 0).getTime()
      if (dateA !== dateB) return dateB - dateA
      return String(a.mandat.numero_mandat ?? '').localeCompare(String(b.mandat.numero_mandat ?? ''), 'fr')
    })

  const suiviKpis: Array<{
    key: 'pending_or_in_progress' | 'accepted_history' | 'refused' | 'anomalies' | 'price_alert' | 'portfolio'
    label: string
    value: number
    tone: string
  }> = [
    { key: 'pending_or_in_progress', label: 'À traiter', value: pendingRows.length, tone: 'demandes' },
    { key: 'accepted_history', label: 'Acceptées', value: acceptedRows.length, tone: 'affaires' },
    { key: 'refused', label: 'Refusées', value: refusedRows.length, tone: 'warning' },
    { key: 'anomalies', label: 'Anomalies', value: anomalyRows.length, tone: 'warning' },
    { key: 'price_alert', label: 'Alerte prix', value: priceAlertRows.length, tone: 'demandes' },
    { key: 'portfolio', label: 'Portefeuille', value: portfolioRows.length, tone: 'neutral' },
  ]
  const primarySuiviKpis = suiviKpis.filter((item) => ['À traiter', 'Anomalies', 'Alerte prix'].includes(item.label))
  const secondarySuiviKpis = suiviKpis.filter((item) => ['Acceptées', 'Refusées', 'Portefeuille'].includes(item.label))
  const suiviPriorities = [
    { key: 'pending_or_in_progress' as const, label: 'À traiter', value: pendingRows.length, detail: 'Demandes de diffusion, baisse ou annulation à décider', tone: 'demandes' },
    { key: 'anomalies' as const, label: 'Anomalies', value: anomalyRows.length, detail: 'Mandats ou diffusions à corriger', tone: 'warning' },
    { key: 'price_alert' as const, label: 'Alerte prix', value: priceAlertRows.length, detail: 'Baisses à contrôler dans Hektor', tone: 'diffusion' },
  ]

  const listingTitle =
    activeSuiviFilter === 'pending_or_in_progress'
      ? 'Demandes à traiter'
      : activeSuiviFilter === 'accepted_history'
        ? 'Demandes acceptées'
        : activeSuiviFilter === 'refused'
          ? 'Demandes refusées'
          : activeSuiviFilter === 'anomalies'
            ? 'Anomalies diffusion et mandat'
            : activeSuiviFilter === 'price_alert'
              ? 'Alertes prix'
              : 'Portefeuille'

  useEffect(() => {
    if (activeSuiviFilter !== 'anomalies') setActiveAnomalyType('all')
  }, [activeSuiviFilter])

  return (
    <section className="panel-grid suivi-pauline-view">
      <section className="panel suivi-command-panel">
        <div className="panel-head">
          <div><p className="eyebrow">{props.eyebrow ?? 'Console Pauline'}</p><h3>{props.title ?? 'Parc mandat'}</h3></div>
          {props.loading ? <span className="loading-inline">Mise a jour...</span> : null}
        </div>
        <div className="header-kpis suivi-header-kpis">
          {primarySuiviKpis.map((item) => (
            <article
              key={item.key}
              className={`header-kpi-card tone-${item.tone} is-clickable ${activeSuiviFilter === item.key ? 'is-active' : ''}`}
              onClick={() => props.onSetRequestFilter(item.key)}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  props.onSetRequestFilter(item.key)
                }
              }}
            >
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </article>
          ))}
        </div>
        <div className="header-control-row">
          <button
            className={`ghost-button kpi-toggle-button ${secondaryKpisOpen ? 'is-open' : ''}`}
            type="button"
            onClick={() => setSecondaryKpisOpen((value) => !value)}
          >
            <span className="control-icon control-icon-stats" aria-hidden="true" />
            <span>{secondaryKpisOpen ? 'Masquer stats' : 'Stats secondaires'}</span>
            <strong>{secondarySuiviKpis.length}</strong>
          </button>
          <button
            className={`ghost-button kpi-toggle-button priority-toggle ${priorityPanelOpen ? 'is-open' : ''}`}
            type="button"
            onClick={() => setPriorityPanelOpen((value) => !value)}
          >
            <span className="control-icon control-icon-priority" aria-hidden="true" />
            <span>Priorités</span>
            <strong>{suiviPriorities.length}</strong>
          </button>
        </div>
        {priorityPanelOpen ? (
          <div className="priority-dropdown" role="region" aria-label="Priorités du suivi">
            {suiviPriorities.map((item) => (
              <button
                key={item.key}
                className={`priority-card tone-${item.tone} is-clickable`}
                type="button"
                onClick={() => {
                  props.onSetRequestFilter(item.key)
                  setPriorityPanelOpen(false)
                }}
              >
                <span className="priority-card-icon" aria-hidden="true" />
                <span className="priority-card-copy">
                  <strong>{item.label}</strong>
                  <small>{item.detail}</small>
                </span>
                <em>{item.value}</em>
              </button>
            ))}
          </div>
        ) : null}
        {secondaryKpisOpen ? (
          <div className="header-kpis header-kpis-secondary">
            {secondarySuiviKpis.map((item) => (
              <article
                key={item.key}
                className={`header-kpi-card tone-${item.tone} is-clickable ${activeSuiviFilter === item.key ? 'is-active' : ''}`}
                onClick={() => props.onSetRequestFilter(item.key)}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    props.onSetRequestFilter(item.key)
                  }
                }}
              >
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <section className="panel suivi-block suivi-block-portfolio">
        <div className="panel-head">
          <div><h3>{listingTitle}</h3></div>
          <div className="suivi-portfolio-kpis">
            <span>
              {activeSuiviFilter === 'anomalies'
                ? visibleAnomalyRows.length
                : activeSuiviFilter === 'price_alert'
                  ? priceAlertRows.length
                  : activeSuiviFilter === 'portfolio'
                    ? portfolioRows.length
                    : suiviRequestRows.length} ligne(s)
            </span>
          </div>
        </div>
        {activeSuiviFilter === 'anomalies' ? (
          <div className="suivi-anomaly-filters" role="tablist" aria-label="Types d'anomalies">
            {anomalyTypeOptions.filter((item) => item.key === 'all' || item.count > 0).map((item) => (
              <button
                key={item.key}
                className={`suivi-anomaly-chip ${activeAnomalyType === item.key ? 'is-active' : ''}`}
                type="button"
                onClick={() => setActiveAnomalyType(item.key)}
              >
                <span>{item.label}</span>
                <strong>{item.count}</strong>
              </button>
            ))}
          </div>
        ) : null}
        <div className="table-wrap suivi-portfolio-wrap">
          {activeSuiviFilter === 'anomalies' ? (
            <table className="suivi-portfolio-table">
              <thead><tr><th>Dossier</th><th>Mandat</th><th>Negociateur</th><th>Diffusion</th><th>Anomalie</th></tr></thead>
              <tbody>
                {visibleAnomalyRows.length > 0 ? visibleAnomalyRows.map((item) => {
                  const anomaly = mandateAnomalyLabels(item)
                  return (
                    <tr key={item.app_dossier_id} onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>
                      <td><strong>{item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                      <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.agence_nom ?? '-'}</span></td>
                      <td>{commercialDisplay(item)}</td>
                      <td><small>{diffusableLabel(item.diffusable)}</small><small>{item.portails_resume || 'Aucune passerelle active'}</small></td>
                      <td>
                        <strong>{anomaly.primary}</strong>
                        {anomaly.secondary.map((label) => <small key={label}>{label}</small>)}
                      </td>
                    </tr>
                  )
                }) : <tr><td colSpan={5}><p className="empty-state">Aucune anomalie dans ce filtre.</p></td></tr>}
              </tbody>
            </table>
          ) : activeSuiviFilter === 'price_alert' ? (
            <table className="suivi-portfolio-table">
              <thead><tr><th>Mandat</th><th>Negociateur</th><th>Prix</th><th>Contrôle</th><th>Dernière date</th></tr></thead>
              <tbody>
                {priceAlertRows.length > 0 ? priceAlertRows.map(({ mandat: item, request }) => (
                  <tr key={`price-alert-${item.app_dossier_id}`} onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>
                    <td><strong>{item.numero_mandat ?? item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                    <td>{commercialDisplay(item)}</td>
                    <td><small>{formatPrice(item.price_change_last_old_value ?? item.prix)}</small><small>{formatPrice(item.price_change_last_new_value ?? item.prix)}</small></td>
                    <td><small>{request ? 'Validation prix sans changement constaté' : 'Prix changé sans baisse validée'}</small></td>
                    <td><small>{formatDate(item.price_change_last_detected_at)}</small><small>{request ? `Validation ${formatDate(requestTimelineDate(request))}` : 'Aucune validation'}</small></td>
                  </tr>
                )) : <tr><td colSpan={5}><p className="empty-state">Aucune alerte prix dans cette vue.</p></td></tr>}
              </tbody>
            </table>
          ) : activeSuiviFilter === 'portfolio' ? (
            <table className="suivi-portfolio-table">
              <thead><tr><th>Dossier</th><th>Mandat</th><th>Negociateur</th><th>Statut</th><th>Visibilite</th></tr></thead>
              <tbody>
                {portfolioRows.length > 0 ? portfolioRows.map((item) => (
                  <tr key={item.app_dossier_id} onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>
                    <td><strong>{item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                    <td><strong>{item.numero_mandat ?? '-'}</strong><span>{item.agence_nom ?? '-'}</span></td>
                    <td>{commercialDisplay(item)}</td>
                    <td><StatusPill value={item.statut_annonce} /><small>{item.archive === '1' ? 'Archive' : 'Actif'}</small></td>
                    <td><small>{diffusableLabel(item.diffusable)}</small><small>{item.portails_resume || 'Aucune passerelle active'}</small></td>
                  </tr>
                )) : <tr><td colSpan={5}><p className="empty-state">Aucun mandat dans cette vue.</p></td></tr>}
              </tbody>
            </table>
          ) : (
            <table className="suivi-portfolio-table">
              <thead><tr><th>Demande</th><th>Mandat</th><th>Negociateur</th><th>Statut</th><th>Motif</th><th>Actions</th></tr></thead>
              <tbody>
                {suiviRequestRows.length > 0 ? suiviRequestRows.map(({ mandat: item, request: activeRequest }) => (
                  <tr key={`${item.app_dossier_id}-${activeRequest.id}`} onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>
                    <td><strong>{requestTypeLabel(activeRequest.request_type)}</strong><span>N° demande {requestNumberLabel(activeRequest)}</span><span>{formatDate(activeRequest.requested_at)}</span></td>
                    <td><strong>{item.numero_mandat ?? item.numero_dossier ?? '-'}</strong><span>{item.titre_bien}</span></td>
                    <td>{commercialDisplay(item)}</td>
                    <td><small>{requestStatusLabel(activeRequest.request_status)}</small><StatusPill value={item.statut_annonce} /></td>
                    <td><small>{activeRequest.request_reason || activeRequest.request_comment || 'Sans motif'}</small></td>
                    <td><div className="row-actions"><MandatActionMenu mandat={item} role="pauline" requests={props.requests} currentRequest={activeRequest} onOpenRequestModal={props.onOpenRequestModal} onOpenDiffusionModal={props.onOpenDiffusionModal} /></div></td>
                  </tr>
                )) : <tr><td colSpan={6}><p className="empty-state">Aucune demande dans cette vue.</p></td></tr>}
              </tbody>
            </table>
          )}
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
  contacts: DetailContact[]
  mandats: Array<{ id: string; title: string; lines: Array<[string, string]> }>
  linkedWorkItems: WorkItem[]
  requestHistory: Array<{ id: string | number; title: string; date: string | null | undefined; body: string }>
  requestMessages: Array<{ id: string; author: string; date: string; message: string }>
  requestHistoryDiffusion: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesDiffusion: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryPriceDrop: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesPriceDrop: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryCancellation: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesCancellation: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  actionRequests?: DiffusionRequest[]
  currentActionRequest?: DiffusionRequest | null
  actionRole?: 'nego' | 'pauline'
  onOpenRequestModal?: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
  onOpenDiffusionModal?: (id: number) => void
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
  adminPilotSurface?: 'none' | 'sidebar' | 'diffusion' | 'both'
  pendingPortalKeys?: string[]
  onOpenImage?: (url: string) => void
  onDeleteAnnonce?: (dossier: Dossier) => void
  onHektorActionJobCreated?: (job: ConsoleJob) => void
  detailVariant?: 'annonce' | 'mandat' | 'suivi'
}) {
  if (!props.selectedDossier) {
    return <section className="panel"><p className="empty-state">Aucun dossier selectionne.</p></section>
  }
  const [historyView, setHistoryView] = useState<'all' | 'diffusion' | 'price_drop' | 'cancellation'>('all')
  const dossier = props.selectedDossier
  const detailVariant = props.detailVariant ?? 'annonce'
  const actionRequests = props.actionRequests ?? []
  const actionRole = props.actionRole ?? 'nego'
  const openRequestFromDetail = props.onOpenRequestModal ?? (() => undefined)
  const openDiffusionFromDetail = props.onOpenDiffusionModal ?? (() => undefined)
  const validationDraft = props.validationDraft ?? (isValidationApproved(dossier.validation_diffusion_state) ? 'oui' : 'non')
  const validationObserved = props.validationObserved ?? validationDraft
  const validationSaved = props.validationSaved ?? validationDraft
  const isValidated = isValidationApproved(validationDraft)
  const validationSyncPending = validationSaved !== validationObserved
  const isDraftDiffusable = props.diffusableDraft ?? isDiffusableValue(dossier.diffusable)
  const isObservedDiffusable = props.diffusableObserved ?? isDiffusableValue(dossier.diffusable)
  const isSavedDiffusable = props.diffusableSaved ?? isDraftDiffusable
  const hektorSyncPending = isSavedDiffusable !== isObservedDiffusable
  const adminPilotSurface = props.adminPilotSurface ?? 'none'
  const showMandatePilot = adminPilotSurface === 'sidebar' || adminPilotSurface === 'both'
  const showDiffusionPilot = adminPilotSurface === 'diffusion' || adminPilotSurface === 'both'
  const observedPortals = uniquePortalKeys((dossier.portails_resume ?? '').split(','))
  const activePortals = uniquePortalKeys([...observedPortals, ...(props.pendingPortalKeys ?? [])])
  const summaryPortals = sortSummaryPortals(activePortals)
  const visibleSummaryPortals = summaryPortals.slice(0, 4)
  const activePortalTotal = Math.max(activePortals.length, Number(dossier.nb_portails_actifs) || 0)
  const hiddenSummaryPortalCount = Math.max(0, activePortalTotal - visibleSummaryPortals.length)
  const portalSyncPending = (props.pendingPortalKeys ?? []).some((portal) => !observedPortals.includes(portal))
  const previewImages = props.images.slice(0, 5)
  const primaryImage = previewImages[0]?.url ?? dossier.photo_url_listing ?? null
  const showDiffusionHistory = historyView === 'all' || historyView === 'diffusion'
  const showPriceDropHistory = historyView === 'all' || historyView === 'price_drop'
  const showCancellationHistory = historyView === 'all' || historyView === 'cancellation'
  const hasAnyHistory = props.requestHistoryDiffusion.length > 0 || props.requestHistoryPriceDrop.length > 0 || props.requestHistoryCancellation.length > 0
  const [mandatSectionOpen, setMandatSectionOpen] = useState(true)
  const [contactSectionOpen, setContactSectionOpen] = useState(false)
  const [hektorFieldEditOpen, setHektorFieldEditOpen] = useState(false)
  const [hektorInlineTitle, setHektorInlineTitle] = useState(dossier.titre_bien ?? '')
  const [hektorInlinePrice, setHektorInlinePrice] = useState(numericDraft(dossier.prix))
  const [hektorInlineSurface, setHektorInlineSurface] = useState(numericDraft(props.detail.surface_habitable_detail ?? props.detail.surface))
  const [hektorInlineRoomCount, setHektorInlineRoomCount] = useState(numericDraft(props.detail.nb_pieces))
  const [hektorInlineBedroomCount, setHektorInlineBedroomCount] = useState(numericDraft(props.detail.nb_chambres))
  const [hektorInlinePending, setHektorInlinePending] = useState(false)
  const [hektorInlineError, setHektorInlineError] = useState<string | null>(null)
  const [activeDetailTab, setActiveDetailTab] = useState<DetailTabKey>(detailVariant === 'mandat' ? 'mandate' : 'summary')
  const [transactionDetailsOpen, setTransactionDetailsOpen] = useState({ offer: false, compromis: false, sale: false })
  const primaryContact = props.contacts[0] ?? null
  const secondaryContacts = props.contacts.slice(1)
  const contactSummaryLabel = props.detail.mandants_texte || props.contacts.map((contact) => contact.name).filter(Boolean).join(' | ')

  useEffect(() => {
    setActiveDetailTab(detailVariant === 'mandat' ? 'mandate' : 'summary')
    setMandatSectionOpen(true)
    setContactSectionOpen(false)
    setHektorFieldEditOpen(false)
    setHektorInlineError(null)
    setHektorInlinePending(false)
  }, [dossier.app_dossier_id, detailVariant])

  useEffect(() => {
    if (hektorFieldEditOpen) return
    setHektorInlineTitle(dossier.titre_bien ?? '')
    setHektorInlinePrice(numericDraft(dossier.prix))
    setHektorInlineSurface(numericDraft(props.detail.surface_habitable_detail ?? props.detail.surface))
    setHektorInlineRoomCount(numericDraft(props.detail.nb_pieces))
    setHektorInlineBedroomCount(numericDraft(props.detail.nb_chambres))
    setHektorInlineError(null)
  }, [
    hektorFieldEditOpen,
    dossier.app_dossier_id,
    dossier.titre_bien,
    dossier.prix,
    props.detail.surface_habitable_detail,
    props.detail.surface,
    props.detail.nb_pieces,
    props.detail.nb_chambres,
  ])

  const resetHektorInlineDraft = () => {
    setHektorInlineTitle(dossier.titre_bien ?? '')
    setHektorInlinePrice(numericDraft(dossier.prix))
    setHektorInlineSurface(numericDraft(props.detail.surface_habitable_detail ?? props.detail.surface))
    setHektorInlineRoomCount(numericDraft(props.detail.nb_pieces))
    setHektorInlineBedroomCount(numericDraft(props.detail.nb_chambres))
    setHektorInlineError(null)
  }

  const closeHektorInlineEdit = () => {
    resetHektorInlineDraft()
    setHektorFieldEditOpen(false)
  }

  const submitHektorInlineEdit = async () => {
    setHektorInlineError(null)
    setHektorInlinePending(true)
    try {
      const job = await createUpdateHektorAnnonceFieldsJob({
        dossier,
        fields: {
          title: hektorInlineTitle,
          description: '',
          price: hektorInlinePrice,
          surface: hektorInlineSurface,
          roomCount: hektorInlineRoomCount,
          bedroomCount: hektorInlineBedroomCount,
        },
        priority: 14,
      })
      props.onHektorActionJobCreated?.(job)
      setHektorFieldEditOpen(false)
    } catch (submitError) {
      setHektorInlineError(submitError instanceof Error ? submitError.message : 'Modification Hektor impossible.')
    } finally {
      setHektorInlinePending(false)
    }
  }

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
  const cancellationRequestGroups = buildRequestGroups(props.requestHistoryCancellation, props.requestMessagesCancellation)
  const latestRequestSignals = [...props.requestHistoryDiffusion, ...props.requestHistoryPriceDrop, ...props.requestHistoryCancellation]
    .sort((left, right) => {
      const leftTime = left.date ? Date.parse(left.date) : 0
      const rightTime = right.date ? Date.parse(right.date) : 0
      return rightTime - leftTime
    })
    .slice(0, 3)
  const matterportGroups = parseJson<MatterportGroup[]>(props.detail.matterport_groups_json, [])
  const matterportModels = matterportGroups.flatMap((group) => group.models.map((model) => ({ group, model })))
  const hasMatterport = matterportModels.length > 0
  const hektorActionModel = buildMandatActionModel({
    mandat: dossier,
    role: actionRole,
    requests: actionRequests,
    currentRequest: props.currentActionRequest,
    onOpenRequestModal: openRequestFromDetail,
    onOpenDiffusionModal: openDiffusionFromDetail,
  })
  const hektorActionItem = hektorActionModel.items.find((item) => item.typeTone === 'hektor')
  return (
    <section className={`detail-screen detail-screen-${detailVariant}`}>
      <div className="panel detail-cockpit-panel">
        <div className="full-detail-layout">
          <div className="detail-cockpit-body">
            <main className="detail-cockpit-main">
              <section className="detail-overview">
                <button className="detail-overview-close" type="button" onClick={props.onBack}>{props.backLabel}</button>
                <div className="detail-overview-summary">
                  <div className="detail-header-topline">
                    <div className="detail-property-title">
                      <span>{detailVariant === 'mandat' ? 'Dossier mandat' : detailVariant === 'suivi' ? 'Dossier suivi' : 'Dossier annonce'}</span>
                      <div className="detail-editable-title-row">
                        {hektorFieldEditOpen ? (
                          <label className="detail-inline-field detail-inline-title-field">
                            <span>Titre</span>
                            <input value={hektorInlineTitle} onChange={(event) => setHektorInlineTitle(event.target.value)} placeholder="Titre visible dans Hektor" />
                          </label>
                        ) : (
                          <h2>{dossier.titre_bien || dossier.numero_dossier || `Annonce #${dossier.hektor_annonce_id}`}</h2>
                        )}
                        <button className={`hektor-field-edit-button ${hektorFieldEditOpen ? 'is-active' : ''}`} type="button" onClick={() => (hektorFieldEditOpen ? closeHektorInlineEdit() : setHektorFieldEditOpen(true))} aria-label={hektorFieldEditOpen ? 'Annuler la modification Hektor' : 'Modifier les champs Hektor'}>
                          <span aria-hidden="true">M</span>
                          {hektorFieldEditOpen ? 'Annuler' : 'Modifier'}
                        </button>
                      </div>
                    {props.address ? <p className="detail-summary-address">{props.address}</p> : null}
                    </div>
                    {dossier.commercial_nom || dossier.agence_nom ? (
                      <div className="detail-owner-card">
                        <div className="detail-owner-avatar">{userInitials(dossier.commercial_nom, null)}</div>
                        <div className="detail-owner-copy">
                          <span>Responsable</span>
                          <strong>{dossier.commercial_nom ?? '-'}</strong>
                          {dossier.agence_nom ? <small>{dossier.agence_nom}</small> : null}
                        </div>
                      </div>
                    ) : null}
                    {props.onDeleteAnnonce ? (
                      <button className="detail-delete-annonce-button" type="button" onClick={() => props.onDeleteAnnonce?.(dossier)}>
                        <span aria-hidden="true"><DetailIcon type="alert" /></span>
                        <strong>Supprimer</strong>
                      </button>
                    ) : null}
                  </div>
                  <div className="detail-keyfacts" aria-label="Carte d'identite du bien">
                    <div className="detail-keyfact-grid">
                      <div className="detail-keyfact-item">
                        <span>Surface habitable</span>
                        {hektorFieldEditOpen ? (
                          <input className="detail-inline-fact-input" value={hektorInlineSurface} onChange={(event) => setHektorInlineSurface(event.target.value)} inputMode="decimal" aria-label="Surface habitable" />
                        ) : (
                          <>
                            <strong>{formatSurface(props.detail.surface_habitable_detail ?? props.detail.surface)}</strong>
                            <button className="hektor-field-mini-edit" type="button" onClick={() => setHektorFieldEditOpen(true)} aria-label="Modifier la surface">M</button>
                          </>
                        )}
                      </div>
                      <div className="detail-keyfact-item">
                        <span>Type de bien</span>
                        <strong>{propertyTypeLabel(dossier.type_bien)}</strong>
                      </div>
                      <div className="detail-keyfact-item detail-keyfact-reference">
                        <span>Reference</span>
                        <strong>{dossier.numero_dossier ?? '-'}</strong>
                      </div>
                    </div>
                    <div className="detail-keyfact-main">
                      <span>Prix annonce</span>
                      {hektorFieldEditOpen ? (
                        <input className="detail-inline-fact-input is-price" value={hektorInlinePrice} onChange={(event) => setHektorInlinePrice(event.target.value)} inputMode="decimal" aria-label="Prix annonce" />
                      ) : (
                        <>
                          <strong>{formatPrice(dossier.prix)}</strong>
                          <button className="hektor-field-mini-edit" type="button" onClick={() => setHektorFieldEditOpen(true)} aria-label="Modifier le prix">M</button>
                        </>
                      )}
                    </div>
                  </div>
                  {hektorFieldEditOpen ? (
                    <div className="detail-inline-edit-bar">
                      <div className="detail-inline-edit-copy">
                        <strong>Champs modifiables</strong>
                        <small>Les valeurs encadrees seront envoyees a Hektor puis resynchronisees dans l app.</small>
                      </div>
                      <label className="detail-inline-mini-field">
                        <span>Pieces</span>
                        <input value={hektorInlineRoomCount} onChange={(event) => setHektorInlineRoomCount(event.target.value)} inputMode="numeric" />
                      </label>
                      <label className="detail-inline-mini-field">
                        <span>Chambres</span>
                        <input value={hektorInlineBedroomCount} onChange={(event) => setHektorInlineBedroomCount(event.target.value)} inputMode="numeric" />
                      </label>
                      <div className="detail-inline-edit-actions">
                        <button type="button" onClick={submitHektorInlineEdit} disabled={hektorInlinePending}>{hektorInlinePending ? 'Envoi...' : 'Enregistrer'}</button>
                        <button type="button" onClick={closeHektorInlineEdit} disabled={hektorInlinePending}>Annuler</button>
                      </div>
                      {hektorInlineError ? <span className="detail-inline-edit-error">{hektorInlineError}</span> : null}
                    </div>
                  ) : null}
                </div>
              </section>

              <nav className="detail-tabbar" aria-label="Navigation detail annonce">
                {detailTabs.map((tab) => (
                  <button
                    key={tab.key}
                    className={`detail-tab-button ${activeDetailTab === tab.key ? 'is-active' : ''}`}
                    type="button"
                    onClick={() => setActiveDetailTab(tab.key)}
                  >
                    <span className="detail-tab-icon" aria-hidden="true"><DetailIcon type={tab.icon} /></span>
                    <span className="detail-tab-index">{tab.short}</span>
                    <strong>{tab.label}</strong>
                  </button>
                ))}
              </nav>

              <div className="detail-column-main">
              {activeDetailTab === 'summary' ? (
                <section className="detail-section detail-summary-cockpit">
                  <div className="detail-summary-board">
                    <article className="detail-summary-visual">
                      {primaryImage ? (
                        <button className="detail-summary-main-image" type="button" onClick={() => props.onOpenImage?.(primaryImage)}>
                          <img src={primaryImage} alt={dossier.titre_bien} />
                        </button>
                      ) : <div className="detail-photo-placeholder">Aucune photo synchronisee</div>}
                    </article>
                    <article className="detail-summary-card is-status">
                      <div className="detail-summary-card-head">
                        <span className="detail-summary-card-icon" aria-hidden="true"><DetailIcon type="summary" /></span>
                        <h5>Points cles</h5>
                      </div>
                      <div className="detail-status-list">
                        <div><span>Statut annonce</span><StatusPill value={dossier.statut_annonce ?? '-'} /></div>
                        <div><span>Mandat</span><StatusPill value={isValidationApproved(validationDraft) ? 'Mandat valide' : 'Mandat a valider'} /></div>
                        <div><span>Diffusable</span><StatusPill value={diffusableLabel(dossier.diffusable)} /></div>
                        <div><span>Passerelles</span><strong>{activePortalTotal ? `${activePortalTotal} actif${activePortalTotal > 1 ? 's' : ''}` : 'Aucune'}</strong></div>
                      </div>
                    </article>
                    <article className="detail-summary-card is-visibility">
                      <div className="detail-summary-card-head">
                        <span className="detail-summary-card-icon" aria-hidden="true"><DetailIcon type="visibility" /></span>
                        <h5>Visibilite</h5>
                      </div>
                      <strong>{activePortalTotal ? `${activePortalTotal} portail${activePortalTotal > 1 ? 's' : ''} actif${activePortalTotal > 1 ? 's' : ''}` : 'Aucun portail actif'}</strong>
                      <div className="detail-mini-portals">
                        {visibleSummaryPortals.length > 0 ? visibleSummaryPortals.map((portal) => (
                          <span key={`summary-${portal}`} className={`detail-mini-portal ${portalBrandClass(portal)}`}>{portalBrandLabel(portal)}</span>
                        )) : <span className="detail-mini-portal is-generic">Aucune</span>}
                        {hiddenSummaryPortalCount > 0 ? <span className="detail-mini-portal is-overflow">+{hiddenSummaryPortalCount}</span> : null}
                      </div>
                    </article>
                    {props.contacts.length > 0 ? (
                      <article className="detail-summary-card is-contact">
                        <div className="detail-summary-card-head">
                          <span className="detail-summary-card-icon" aria-hidden="true"><DetailIcon type="contact" /></span>
                          <h5>Mandants</h5>
                        </div>
                        <strong>{props.contacts.length} contact{props.contacts.length > 1 ? 's' : ''} lie{props.contacts.length > 1 ? 's' : ''}</strong>
                        <p>{contactSummaryLabel || primaryContact?.name || '-'}</p>
                        <button className="section-toggle-button" type="button" onClick={() => setActiveDetailTab('mandate')}>
                          Voir contacts
                        </button>
                      </article>
                    ) : null}
                  </div>
                </section>
              ) : null}

              {(activeDetailTab === 'mandate' || activeDetailTab === 'commercial') ? (
              <section className="detail-section detail-section-topstack">
                {activeDetailTab === 'mandate' ? (
                <article className="detail-subsection detail-mandate-section">
                  <div className="section-header section-header-collapsible">
                    <DetailSectionTitle icon="mandate" title="Detail mandat" />
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
                ) : null}
                {activeDetailTab === 'mandate' && showMandatePilot && props.allowMarkValidation ? (
                <article className="detail-subsection detail-admin-inline-pilot">
                  <DetailAdminPilotPanel
                    allowValidation={props.allowMarkValidation}
                    allowDiffusable={false}
                    validationActive={isValidated}
                    validationObserved={isValidationApproved(validationObserved)}
                    validationPending={Boolean(props.markValidationPending)}
                    validationSyncPending={validationSyncPending}
                    diffusableActive={isDraftDiffusable}
                    diffusableObserved={isObservedDiffusable}
                    diffusablePending={Boolean(props.markDiffusablePending)}
                    diffusableSyncPending={hektorSyncPending || portalSyncPending}
                    onSetValidation={props.onSetValidation}
                    onSetDiffusable={props.onSetDiffusable}
                    onOpenHektor={hektorActionItem ? () => hektorActionItem.onClick({ stopPropagation() {} }) : undefined}
                  />
                </article>
                ) : null}
                {activeDetailTab === 'commercial' ? (
                <article className="detail-subsection detail-price-section">
                  <div className="section-header">
                    <DetailSectionTitle icon="commercial" title="Historique des prix" />
                  </div>
                  <PriceChangeHistoryCard
                    source={props.detail.price_change_events_json ? props.detail : dossier}
                    title="Historique des prix"
                    emptyLabel="Aucun changement de prix historisé pour cette annonce."
                  />
                </article>
                ) : null}
                {activeDetailTab === 'mandate' ? (
                <article className="detail-subsection detail-contact-section">
                  <div className="section-header section-header-collapsible">
                    <DetailSectionTitle icon="contact" title="Mandants / proprietaires" />
                    {secondaryContacts.length > 0 ? (
                      <button className={`mandants-toggle-button ${contactSectionOpen ? 'is-open' : ''}`} type="button" onClick={() => setContactSectionOpen((value) => !value)} aria-expanded={contactSectionOpen}>
                        <span className="mandants-toggle-icon" aria-hidden="true">{contactSectionOpen ? '-' : '+'}</span>
                        <span className="mandants-toggle-copy">
                          <strong>{contactSectionOpen ? 'Masquer les autres vendeurs' : `Voir ${secondaryContacts.length} autre${secondaryContacts.length > 1 ? 's' : ''} vendeur${secondaryContacts.length > 1 ? 's' : ''}`}</strong>
                          <small>{props.contacts.length} mandants lies a cette annonce</small>
                        </span>
                      </button>
                    ) : null}
                  </div>
                  {primaryContact ? (
                    <div className="detail-entity-list detail-contact-list">
                      <div className="detail-contact-summary-strip">
                        <span className="detail-contact-source-badge">API AnnonceById</span>
                        <strong>{props.contacts.length} mandant{props.contacts.length > 1 ? 's' : ''} lie{props.contacts.length > 1 ? 's' : ''}</strong>
                        <small>{props.detail.mandants_texte || primaryContact.name}</small>
                      </div>
                      <HektorMandantContactForm dossier={dossier} onJobCreated={props.onHektorActionJobCreated} />
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
                            <span>ID Hektor</span>
                            <strong>{primaryContact.sourceId || '-'}</strong>
                          </div>
                          <div className="detail-entity-line">
                            <span>Telephone</span>
                            <strong>{primaryContact.phone ? <a href={`tel:${primaryContact.phone}`} className="detail-contact-link">{primaryContact.phone}</a> : '-'}</strong>
                          </div>
                          <div className="detail-entity-line">
                            <span>Email</span>
                            <strong>{primaryContact.email ? <a href={`mailto:${primaryContact.email}`} className="detail-contact-link">{primaryContact.email}</a> : '-'}</strong>
                          </div>
                          <div className="detail-entity-line">
                            <span>MAJ Hektor</span>
                            <strong>{formatDate(primaryContact.dateUpdated) || '-'}</strong>
                          </div>
                          <div className="detail-entity-line detail-entity-line-full">
                            <span>Adresse</span>
                            <strong>{[primaryContact.address, primaryContact.postalCode, primaryContact.city].filter(Boolean).join(', ') || '-'}</strong>
                          </div>
                          {primaryContact.comment ? (
                            <div className="detail-entity-line detail-entity-line-full detail-contact-note">
                              <span>Commentaire</span>
                              <strong>{primaryContact.comment}</strong>
                            </div>
                          ) : null}
                        </div>
                        <HektorMandantContactEditForm dossier={dossier} contact={primaryContact} onJobCreated={props.onHektorActionJobCreated} />
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
                                  <span>ID Hektor</span>
                                  <strong>{contact.sourceId || '-'}</strong>
                                </div>
                                <div className="detail-entity-line">
                                  <span>Telephone</span>
                                  <strong>{contact.phone ? <a href={`tel:${contact.phone}`} className="detail-contact-link">{contact.phone}</a> : '-'}</strong>
                                </div>
                                <div className="detail-entity-line">
                                  <span>Email</span>
                                  <strong>{contact.email ? <a href={`mailto:${contact.email}`} className="detail-contact-link">{contact.email}</a> : '-'}</strong>
                                </div>
                                <div className="detail-entity-line">
                                  <span>MAJ Hektor</span>
                                  <strong>{formatDate(contact.dateUpdated) || '-'}</strong>
                                </div>
                                <div className="detail-entity-line detail-entity-line-full">
                                  <span>Adresse</span>
                                  <strong>{[contact.address, contact.postalCode, contact.city].filter(Boolean).join(', ') || '-'}</strong>
                                </div>
                                {contact.comment ? (
                                  <div className="detail-entity-line detail-entity-line-full detail-contact-note">
                                    <span>Commentaire</span>
                                    <strong>{contact.comment}</strong>
                                  </div>
                                ) : null}
                              </div>
                              <HektorMandantContactEditForm dossier={dossier} contact={contact} onJobCreated={props.onHektorActionJobCreated} />
                            </article>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <div className="detail-entity-list detail-contact-list">
                      <HektorMandantContactForm dossier={dossier} initialOpen onJobCreated={props.onHektorActionJobCreated} />
                    </div>
                  )}
                </article>
                ) : null}
              </section>
              ) : null}

              {activeDetailTab === 'content' ? (
              <section className="detail-section detail-photo-section">
                <div className="section-header"><DetailSectionTitle icon="photo" title="Photos" /><span>{props.images.length} photo{props.images.length > 1 ? 's' : ''}</span></div>
                {props.images.length > 0 ? (
                  <div className="detail-media-grid">
                    {props.images.slice(0, 6).map((item) => (
                      <button key={`content-photo-${item.url}`} className="detail-media-tile" type="button" onClick={() => props.onOpenImage?.(item.url)}>
                        <img src={item.url} alt={item.legend || dossier.titre_bien} />
                      </button>
                    ))}
                  </div>
                ) : <p className="empty-state">Aucune photo synchronisee.</p>}
              </section>
              ) : null}

              {activeDetailTab === 'content' ? (
              <section className="detail-section detail-console-documents-section">
                <ConsoleDocumentsPanel dossier={dossier} onJobCreated={props.onHektorActionJobCreated} />
              </section>
              ) : null}

              {activeDetailTab === 'content' ? (
              <section className="detail-section detail-virtual-section matterport-section">
                <div className="section-header">
                  <DetailSectionTitle icon="virtual" title="Visite virtuelle" />
                </div>
                {hasMatterport ? (
                  <div className="matterport-group-list">
                    {matterportGroups.map((group) => {
                      const models = group.models ?? []
                      const single = models.length <= 1
                      return (
                        <article key={group.id} className="matterport-group-card">
                          <div className="matterport-group-head">
                            <div>
                              <strong>{group.group_label || (group.numero_mandat ? `Mandat ${group.numero_mandat}` : 'Groupe Matterport')}</strong>
                              <span>{models.length} visite{models.length > 1 ? 's' : ''} liee{models.length > 1 ? 's' : ''}</span>
                            </div>
                            <div className="matterport-state-row">
                              <StatusPill value={matterportStateLabel(group.group_state)} />
                              <StatusPill value={matterportVisibilityLabel(group.group_visibility)} />
                            </div>
                          </div>
                          <div className="matterport-model-list">
                            {models.map((model) => (
                              <div key={model.matterport_model_id} className="matterport-model-row">
                                <div className="matterport-model-main">
                                  <strong>{matterportModelLabel(model.label, model.matterport_name, single)}</strong>
                                  <span>{model.matterport_name || model.matterport_model_id}</span>
                                </div>
                                <div className="matterport-model-actions">
                                  <a className="ghost-button matterport-open-link" href={model.matterport_url} target="_blank" rel="noreferrer">Ouvrir</a>
                                  <button className="ghost-button" type="button" disabled title="Action bloquee cote Matterport tant que l'acces API model.locked n'est pas leve.">
                                    {matterportStateLabel(model.state)}
                                  </button>
                                  <button className="ghost-button" type="button" disabled title="Action bloquee cote Matterport tant que l'acces API model.locked n'est pas leve.">
                                    {matterportVisibilityLabel(model.visibility)}
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </article>
                      )
                    })}
                  </div>
                ) : <p className="empty-state">Aucune visite Matterport liee a cette annonce.</p>}
              </section>
              ) : null}

              {activeDetailTab === 'content' ? (
              <section className="detail-section detail-text-section">
                <div className="section-header"><DetailSectionTitle icon="content" title="Descriptif" />{props.detailLoading ? <span>Chargement...</span> : null}</div>
                {props.texts.length > 0 ? (
                  <div className="rich-text-stack">
                    {props.texts.map((block) => <article key={block.id} className="rich-text-card"><span className="detail-label">{block.title}</span><div dangerouslySetInnerHTML={{ __html: block.html }} /></article>)}
                  </div>
                ) : <p className="empty-state">Aucun descriptif riche disponible.</p>}
              </section>
              ) : null}

              {activeDetailTab === 'content' ? (
              <section className="detail-section detail-features-section">
                <div className="section-header"><DetailSectionTitle icon="summary" title="Caracteristiques du bien" /></div>
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
              ) : null}

              {activeDetailTab === 'commercial' ? (
              <section className="detail-section detail-section-transactions">
                <div className="section-header"><DetailSectionTitle icon="commercial" title="Transactions" /></div>
                <div className="transaction-flow">
                  <article className={`transaction-card transaction-card-offer ${transactionDetailsOpen.offer ? 'is-open' : ''}`}>
                    <div className="transaction-card-head">
                      <button
                        className="transaction-toggle"
                        type="button"
                        aria-expanded={transactionDetailsOpen.offer}
                        aria-controls="transaction-offer-details"
                        onClick={() => setTransactionDetailsOpen((current) => ({ ...current, offer: !current.offer }))}
                      >
                        <span>01</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M6 9L12 15L18 9" />
                        </svg>
                      </button>
                      <div>
                        <h5>Offre</h5>
                        <span>{props.detail.offre_state ?? 'Etat non renseigne'}</span>
                      </div>
                    </div>
                    <div className="transaction-highlight">
                      <div><span>Montant</span><strong>{formatPrice(props.detail.offre_montant)}</strong></div>
                      <div><span>Date</span><strong>{formatDate(props.detail.offre_event_date)}</strong></div>
                    </div>
                    {transactionDetailsOpen.offer ? (
                    <div id="transaction-offer-details" className="transaction-detail-drawer">
                      <span className="transaction-detail-label">Details complets</span>
                      <div className="transaction-detail-lines">
                        <div><span>ID</span><strong>{props.detail.offre_id ?? '-'}</strong></div>
                        <div><span>Etat</span><strong>{props.detail.offre_state ?? '-'}</strong></div>
                        <div><span>Statut source</span><strong>{props.detail.offre_raw_status ?? '-'}</strong></div>
                        <div><span>Date</span><strong>{formatDate(props.detail.offre_event_date)}</strong></div>
                        <div><span>Montant</span><strong>{formatPrice(props.detail.offre_montant)}</strong></div>
                        <div><span>Acquereur</span><strong>{props.detail.offre_acquereur_nom ?? '-'}</strong></div>
                      </div>
                    </div>
                    ) : null}
                  </article>
                  <article className={`transaction-card transaction-card-compromis ${transactionDetailsOpen.compromis ? 'is-open' : ''}`}>
                    <div className="transaction-card-head">
                      <button
                        className="transaction-toggle"
                        type="button"
                        aria-expanded={transactionDetailsOpen.compromis}
                        aria-controls="transaction-compromis-details"
                        onClick={() => setTransactionDetailsOpen((current) => ({ ...current, compromis: !current.compromis }))}
                      >
                        <span>02</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M6 9L12 15L18 9" />
                        </svg>
                      </button>
                      <div>
                        <h5>Compromis</h5>
                        <span>{props.detail.compromis_state ?? 'Etat non renseigne'}</span>
                      </div>
                    </div>
                    <div className="transaction-highlight">
                      <div><span>Sequestre</span><strong>{formatPrice(props.detail.compromis_sequestre)}</strong></div>
                      <div><span>Date acte</span><strong>{formatDate(props.detail.date_signature_acte)}</strong></div>
                    </div>
                    {transactionDetailsOpen.compromis ? (
                    <div id="transaction-compromis-details" className="transaction-detail-drawer">
                      <span className="transaction-detail-label">Details complets</span>
                      <div className="transaction-detail-lines">
                        <div><span>ID</span><strong>{props.detail.compromis_id ?? '-'}</strong></div>
                        <div><span>Etat</span><strong>{props.detail.compromis_state ?? '-'}</strong></div>
                        <div><span>Date debut</span><strong>{formatDate(props.detail.compromis_date_start)}</strong></div>
                        <div><span>Date fin</span><strong>{formatDate(props.detail.compromis_date_end)}</strong></div>
                        <div><span>Date acte</span><strong>{formatDate(props.detail.date_signature_acte)}</strong></div>
                        <div><span>Sequestre</span><strong>{formatPrice(props.detail.compromis_sequestre)}</strong></div>
                      </div>
                    </div>
                    ) : null}
                  </article>
                  <article className={`transaction-card transaction-card-sale ${transactionDetailsOpen.sale ? 'is-open' : ''}`}>
                    <div className="transaction-card-head">
                      <button
                        className="transaction-toggle"
                        type="button"
                        aria-expanded={transactionDetailsOpen.sale}
                        aria-controls="transaction-sale-details"
                        onClick={() => setTransactionDetailsOpen((current) => ({ ...current, sale: !current.sale }))}
                      >
                        <span>03</span>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                          <path d="M6 9L12 15L18 9" />
                        </svg>
                      </button>
                      <div>
                        <h5>Vente</h5>
                        <span>{props.detail.vente_id ? 'Vente renseignee' : 'Vente non renseignee'}</span>
                      </div>
                    </div>
                    <div className="transaction-highlight">
                      <div><span>Prix</span><strong>{formatPrice(props.detail.vente_prix)}</strong></div>
                      <div><span>Date vente</span><strong>{formatDate(props.detail.vente_date)}</strong></div>
                    </div>
                    {transactionDetailsOpen.sale ? (
                    <div id="transaction-sale-details" className="transaction-detail-drawer">
                      <span className="transaction-detail-label">Details complets</span>
                      <div className="transaction-detail-lines">
                        <div><span>ID</span><strong>{props.detail.vente_id ?? '-'}</strong></div>
                        <div><span>Date vente</span><strong>{formatDate(props.detail.vente_date)}</strong></div>
                        <div><span>Prix</span><strong>{formatPrice(props.detail.vente_prix)}</strong></div>
                        <div><span>Honoraires</span><strong>{formatPrice(props.detail.vente_honoraires)}</strong></div>
                        <div><span>Commission agence</span><strong>{formatPrice(props.detail.vente_commission_agence)}</strong></div>
                        <div><span>Notaires</span><strong>{props.detail.vente_notaires_resume ?? '-'}</strong></div>
                      </div>
                    </div>
                    ) : null}
                  </article>
                </div>
              </section>
              ) : null}

              {activeDetailTab === 'content' ? (
              <section className="detail-section">
                <div className="section-header"><DetailSectionTitle icon="history" title="Notes et commentaires" /></div>
                {props.notes.length > 0 ? (
                  <div className="timeline-list">
                    {props.notes.map((item) => <article key={item.id} className="timeline-card"><strong>{item.title}</strong><span>{item.date || '-'}</span><p>{item.content}</p></article>)}
                  </div>
                ) : <p className="empty-state">Aucune note disponible.</p>}
              </section>
              ) : null}

              {activeDetailTab === 'commercial' ? <AppointmentAnnonceSection dossier={dossier} detail={props.detail} /> : null}
              </div>
            </main>

            <aside className="detail-column-side">
              <section className="detail-section detail-side-quick">
                <DetailDossierActionPanel
                  mandat={dossier}
                  role={actionRole}
                  requests={actionRequests}
                  currentRequest={props.currentActionRequest}
                  nextActionLabel={!isValidationApproved(validationDraft) ? 'Valider le mandat' : isDraftDiffusable ? 'Controler la diffusion' : 'Activer la diffusion'}
                  nextActionDetail={props.detail.next_action || props.detail.motif_blocage || "Le mandat n'est pas encore qualifie avec une prochaine action."}
                  onOpenRequestModal={openRequestFromDetail}
                  onOpenDiffusionModal={openDiffusionFromDetail}
                  renderExtraActions={(showMandatePilot && props.allowMarkValidation) || (showDiffusionPilot && props.allowMarkDiffusable) ? () => (
                    <DetailAdminPilotPanel
                      allowValidation={showMandatePilot && props.allowMarkValidation}
                      allowDiffusable={showDiffusionPilot && props.allowMarkDiffusable}
                      validationActive={isValidated}
                      validationObserved={isValidationApproved(validationObserved)}
                      validationPending={Boolean(props.markValidationPending)}
                      validationSyncPending={validationSyncPending}
                      diffusableActive={isDraftDiffusable}
                      diffusableObserved={isObservedDiffusable}
                      diffusablePending={Boolean(props.markDiffusablePending)}
                      diffusableSyncPending={hektorSyncPending || portalSyncPending}
                      onSetValidation={props.onSetValidation}
                      onSetDiffusable={props.onSetDiffusable}
                      onOpenHektor={hektorActionItem ? () => hektorActionItem.onClick({ stopPropagation() {} }) : undefined}
                    />
                  ) : undefined}
                />
              </section>
            </aside>

            <div className="detail-column-main">
              {activeDetailTab === 'diffusion' ? (
              <section className="detail-section detail-section-status">
                <div className="section-header"><DetailSectionTitle icon="diffusion" title="Diffusion" /></div>
                {props.allowMarkDiffusable && showDiffusionPilot ? (
                  <DetailAdminPilotPanel
                    allowValidation={false}
                    allowDiffusable={props.allowMarkDiffusable}
                    validationActive={isValidated}
                    validationObserved={isValidationApproved(validationObserved)}
                    validationPending={Boolean(props.markValidationPending)}
                    validationSyncPending={validationSyncPending}
                    diffusableActive={isDraftDiffusable}
                    diffusableObserved={isObservedDiffusable}
                    diffusablePending={Boolean(props.markDiffusablePending)}
                    diffusableSyncPending={hektorSyncPending || portalSyncPending}
                    onSetValidation={props.onSetValidation}
                    onSetDiffusable={props.onSetDiffusable}
                    onOpenHektor={hektorActionItem ? () => hektorActionItem.onClick({ stopPropagation() {} }) : undefined}
                  />
                ) : null}
                <div className="detail-portals-list">
                  <span className="detail-label">Passerelles activees</span>
                  {activePortals.length > 0 ? (
                    <div className="detail-portal-badges">
                      {activePortals.map((portal) => (
                        <article key={portal} className={`detail-portal-badge ${portalBrandClass(portal)}`}>
                          <strong>{portalBrandLabel(portal)}</strong>
                          <span>{observedPortals.includes(portal) ? 'Actif' : 'En attente'}</span>
                        </article>
                      ))}
                    </div>
                  ) : <p className="empty-state">Aucune passerelle active.</p>}
                </div>
              </section>
              ) : null}

              {activeDetailTab === 'diffusion' && latestRequestSignals.length > 0 ? (
                <section className="detail-section detail-latest-requests-section">
                  <div className="section-header"><DetailSectionTitle icon="history" title="Dernieres demandes" /></div>
                  <div className="detail-request-table">
                    {latestRequestSignals.map((item) => (
                      <article key={`diffusion-signal-${item.requestId}-${item.id}`} className="detail-request-row">
                        <span>{formatDate(item.date)}</span>
                        <strong>{item.title}</strong>
                        <StatusPill value={requestStatusLabel(item.status)} />
                      </article>
                    ))}
                  </div>
                </section>
              ) : null}

              {activeDetailTab === 'history' ? (
              <section className="detail-section detail-history-section">
                <div className="section-header">
                  <DetailSectionTitle icon="history" title="Historique des demandes" />
                  <div className="segmented-control">
                    <button className={`segment-button ${historyView === 'all' ? 'is-active' : ''}`} type="button" onClick={() => setHistoryView('all')}>Tout</button>
                    <button className={`segment-button ${historyView === 'diffusion' ? 'is-active' : ''}`} type="button" onClick={() => setHistoryView('diffusion')}>Diffusion</button>
                    <button className={`segment-button ${historyView === 'price_drop' ? 'is-active' : ''}`} type="button" onClick={() => setHistoryView('price_drop')}>Baisse de prix</button>
                    <button className={`segment-button ${historyView === 'cancellation' ? 'is-active' : ''}`} type="button" onClick={() => setHistoryView('cancellation')}>Annulation</button>
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
                {showCancellationHistory && props.requestHistoryCancellation.length > 0 ? (
                  <>
                    <span className="detail-label">Annulation mandat</span>
                    <div className="request-group-list">
                      {cancellationRequestGroups.map((group, index) => (
                        <section key={`group-cancel-${group.requestId}`} className={`request-group tone-${group.cycleTone}`}>
                          <div className="request-group-head">
                            <span className="request-group-badge">Demande {cancellationRequestGroups.length - index}</span>
                          </div>
                          <div className="timeline-list">
                            {group.entries.map((entry) => (
                              <article key={`history-cancel-${entry.id}`} className={`timeline-card request-cycle-card tone-${group.cycleTone}`}>
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
              ) : null}
            </div>
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
  const appointmentUrl = buildAppointmentAnnonceUrl(props.dossier, props.detail)
  const appointmentEmail = safeText(props.detail.appointment_negociateur_email) || props.dossier.negociateur_email || '-'

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
      <article className="detail-card">
        <span className="detail-label">Rendez-vous annonce</span>
        <div className="info-grid">
          <InfoCard label="QR cible" value="Annonce vitrine" />
          <InfoCard label="ID annonce" value={props.dossier.hektor_annonce_id} />
          <InfoCard label="Commercial cible" value={props.dossier.commercial_nom ?? '-'} />
          <InfoCard label="Email nego" value={appointmentEmail} />
          <InfoCard label="Agence" value={props.dossier.agence_nom ?? '-'} />
          <InfoCard label="URL publique" value={appointmentUrl ?? 'A configurer'} />
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

function AppointmentAnnonceSection(props: {
  dossier: Dossier | null
  detail: DossierDetailPayload
}) {
  const appointmentUrl = buildAppointmentAnnonceUrl(props.dossier, props.detail)
  const requests = parseAppointmentRequests(props.detail)
  const events = parseAppointmentRequestEvents(props.detail)
  const appointmentEmail = safeText(props.detail.appointment_negociateur_email) || props.dossier?.negociateur_email || '-'
  const appointmentNegociateurId = props.detail.appointment_negociateur_id ?? props.dossier?.commercial_id ?? '-'

  return (
    <section className="detail-section detail-appointment-section">
      <div className="section-header"><DetailSectionTitle icon="contact" title="Rendez-vous annonce" /></div>
      <div className="detail-stack">
        <article className="detail-card">
          <span className="detail-label">Ciblage QR</span>
          <div className="info-grid">
            <InfoCard label="Mode" value="QR annonce vitrine" />
            <InfoCard label="ID annonce" value={props.dossier?.hektor_annonce_id ?? '-'} />
            <InfoCard label="Negociateur" value={props.dossier?.commercial_nom ?? '-'} />
            <InfoCard label="ID nego" value={appointmentNegociateurId} />
            <InfoCard label="Email nego" value={appointmentEmail} />
            <InfoCard label="Agence" value={props.dossier?.agence_nom ?? '-'} />
          </div>
          <div className="detail-rich-copy">
            <strong>URL publique cible</strong>
            <p>{appointmentUrl ?? 'Aucune URL publique configuree pour le moment.'}</p>
          </div>
        </article>
        <article className="detail-card">
          <span className="detail-label">Demandes recues</span>
          {requests.length > 0 ? (
            <div className="timeline-list">
              {requests.map((item, index) => (
                <article key={String(item.id ?? index)} className="timeline-card">
                  <strong>{item.client_nom ?? 'Client sans nom'} · {appointmentStatusLabel(item.status)}</strong>
                  <span>{formatDate(item.requested_start_at)}{item.requested_end_at ? ` → ${formatDate(item.requested_end_at)}` : ''}</span>
                  <span>{item.client_telephone ?? item.client_email ?? '-'}</span>
                  <p>{item.message ?? 'Sans message client.'}</p>
                </article>
              ))}
            </div>
          ) : <p className="empty-state">Aucune demande RDV stockee pour cette annonce pour le moment.</p>}
        </article>
        <article className="detail-card">
          <span className="detail-label">Historique RDV</span>
          {events.length > 0 ? (
            <div className="timeline-list">
              {events.map((item, index) => (
                <article key={String(item.id ?? index)} className="timeline-card">
                  <strong>{item.event_label ?? item.event_type ?? 'Evenement RDV'}</strong>
                  <span>{formatDate(item.created_at)}</span>
                  <span>{item.actor_name ?? 'Systeme'}</span>
                  <p>{item.payload_json ?? 'Sans detail supplementaire.'}</p>
                </article>
              ))}
            </div>
          ) : <p className="empty-state">Historique RDV vide tant que le module de demandes n'est pas encore stocke en base.</p>}
        </article>
      </div>
    </section>
  )
}

function AnnonceScreen(props: {
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  texts: Array<{ id: string; title: string; html: string }>
  notes: Array<{ id: string; title: string; date: string; content: string }>
  contacts: DetailContact[]
  mandats: Array<{ id: string; title: string; lines: Array<[string, string]> }>
  linkedWorkItems: WorkItem[]
  requestHistory: Array<{ id: string | number; title: string; date: string | null | undefined; body: string }>
  requestMessages: Array<{ id: string; author: string; date: string; message: string }>
  requestHistoryDiffusion: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesDiffusion: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryPriceDrop: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesPriceDrop: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryCancellation: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesCancellation: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  actionRequests?: DiffusionRequest[]
  currentActionRequest?: DiffusionRequest | null
  actionRole?: 'nego' | 'pauline'
  onOpenRequestModal?: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
  onOpenDiffusionModal?: (id: number) => void
  onHektorActionJobCreated?: (job: ConsoleJob) => void
  detailLoading: boolean
  onBack: () => void
}) {
  return <DossierDetailLayout {...props} eyebrow="Annonce complete" backLabel="Retour stock" detailVariant="annonce" />
}

function DossierDetailScreen(props: {
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  texts: Array<{ id: string; title: string; html: string }>
  notes: Array<{ id: string; title: string; date: string; content: string }>
  contacts: DetailContact[]
  mandats: Array<{ id: string; title: string; lines: Array<[string, string]> }>
  linkedWorkItems: WorkItem[]
  requestHistory: Array<{ id: string | number; title: string; date: string | null | undefined; body: string }>
  requestMessages: Array<{ id: string; author: string; date: string; message: string }>
  requestHistoryDiffusion: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesDiffusion: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryPriceDrop: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesPriceDrop: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryCancellation: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesCancellation: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  onHektorActionJobCreated?: (job: ConsoleJob) => void
  detailLoading: boolean
  sourceScreen: 'mandats' | 'suivi'
  onBack: () => void
}) {
  return (
    <DossierDetailLayout
      {...props}
      eyebrow={props.sourceScreen === 'mandats' ? 'Detail mandat' : 'Detail suivi'}
      backLabel={props.sourceScreen === 'mandats' ? 'Retour mandats' : 'Retour suivi'}
      detailVariant={props.sourceScreen === 'mandats' ? 'mandat' : 'suivi'}
    />
  )
}

function MobileDossierDetail(props: {
  selectedDossier: Dossier | null
  detail: DossierDetailPayload
  address: string
  images: Array<{ url: string; legend: string }>
  texts: Array<{ id: string; title: string; html: string }>
  notes: Array<{ id: string; title: string; date: string; content: string }>
  contacts: DetailContact[]
  mandats: Array<{ id: string; title: string; lines: Array<[string, string]> }>
  linkedWorkItems: WorkItem[]
  requestHistory: Array<{ id: string | number; title: string; date: string | null | undefined; body: string }>
  requestMessages: Array<{ id: string; author: string; date: string; message: string }>
  requestHistoryDiffusion: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesDiffusion: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryPriceDrop: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesPriceDrop: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  requestHistoryCancellation: Array<{ id: string | number; requestId: string; title: string; status: string; date: string | null | undefined; body: string; cycleTone?: number }>
  requestMessagesCancellation: Array<{ id: string; requestId: string; author: string; date: string; message: string; cycleTone?: number }>
  actionRequests?: DiffusionRequest[]
  currentActionRequest?: DiffusionRequest | null
  actionRole?: 'nego' | 'pauline'
  onOpenRequestModal?: (id: number, role?: 'nego' | 'pauline', requestType?: BusinessRequestType) => void
  onOpenDiffusionModal?: (id: number) => void
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
  adminPilotSurface?: 'none' | 'sidebar' | 'diffusion' | 'both'
  pendingPortalKeys?: string[]
  onOpenImage?: (url: string) => void
  onDeleteAnnonce?: (dossier: Dossier) => void
  onHektorActionJobCreated?: (job: ConsoleJob) => void
  detailVariant?: 'annonce' | 'mandat' | 'suivi'
}) {
  const dossier = props.selectedDossier
  const [mobileHektorEditOpen, setMobileHektorEditOpen] = useState(false)

  useEffect(() => {
    setMobileHektorEditOpen(false)
  }, [dossier?.app_dossier_id])

  if (!dossier) return <section className="mobile-detail-empty">Aucun dossier sélectionné.</section>

  const primaryImage = props.images[0]?.url ?? dossier.photo_url_listing ?? null
  const activePortals = uniquePortalKeys([...(dossier.portails_resume ?? '').split(','), ...(props.pendingPortalKeys ?? [])])
  const matterportGroups = parseJson<MatterportGroup[]>(props.detail.matterport_groups_json, [])
  const matterportModels = matterportGroups.flatMap((group) => group.models.map((model) => ({ group, model })))
  const actionRole = props.actionRole ?? 'nego'
  const canShowDiffusion = props.adminPilotSurface === 'diffusion' || props.adminPilotSurface === 'both'
  const canShowMandatePilot = props.adminPilotSurface === 'sidebar' || props.adminPilotSurface === 'both'
  const requestItems = [...props.requestHistoryDiffusion, ...props.requestHistoryPriceDrop, ...props.requestHistoryCancellation]
    .sort((left, right) => new Date(right.date ?? 0).getTime() - new Date(left.date ?? 0).getTime())
  const messageItems = [...props.requestMessagesDiffusion, ...props.requestMessagesPriceDrop, ...props.requestMessagesCancellation, ...props.requestMessages]
    .sort((left, right) => new Date(right.date ?? 0).getTime() - new Date(left.date ?? 0).getTime())
  const detailFacts = [
    ['Prix', formatPrice(dossier.prix)],
    ['Surface', props.detail.surface_habitable_detail ?? props.detail.surface ?? '-'],
    ['Pièces', props.detail.nb_pieces ?? '-'],
    ['Chambres', props.detail.nb_chambres ?? '-'],
    ['Type', propertyTypeLabel(dossier.type_bien)],
    ['Référence', dossier.numero_dossier ?? '-'],
  ]
  const featureFacts = [
    ['Type', propertyTypeLabel(dossier.type_bien)],
    ['Surface habitable', props.detail.surface_habitable_detail ?? '-'],
    ['Terrain', props.detail.surface_terrain_detail ?? '-'],
    ['Pieces', props.detail.nb_pieces ?? '-'],
    ['Chambres', props.detail.nb_chambres ?? '-'],
    ['Etage', props.detail.etage_detail ?? '-'],
    ['Terrasse', props.detail.terrasse_detail ?? '-'],
    ['Garage / box', props.detail.garage_box_detail ?? '-'],
    ['Ascenseur', props.detail.ascenseur_detail ?? '-'],
  ]
  const offerFacts = [
    ['ID', props.detail.offre_id ?? '-'],
    ['Etat', props.detail.offre_state ?? '-'],
    ['Statut source', props.detail.offre_raw_status ?? '-'],
    ['Date', formatDate(props.detail.offre_event_date)],
    ['Montant', formatPrice(props.detail.offre_montant)],
    ['Acquereur', props.detail.offre_acquereur_nom ?? '-'],
  ]
  const compromisFacts = [
    ['ID', props.detail.compromis_id ?? '-'],
    ['Etat', props.detail.compromis_state ?? '-'],
    ['Date debut', formatDate(props.detail.compromis_date_start)],
    ['Date fin', formatDate(props.detail.compromis_date_end)],
    ['Date acte', formatDate(props.detail.date_signature_acte)],
    ['Sequestre', formatPrice(props.detail.compromis_sequestre)],
  ]
  const saleFacts = [
    ['ID', props.detail.vente_id ?? '-'],
    ['Date vente', formatDate(props.detail.vente_date)],
    ['Prix', formatPrice(props.detail.vente_prix)],
    ['Honoraires', formatPrice(props.detail.vente_honoraires)],
    ['Commission agence', formatPrice(props.detail.vente_commission_agence)],
    ['Notaires', props.detail.vente_notaires_resume ?? '-'],
  ]
  const adminValidationState = props.validationDraft ?? (isValidationApproved(dossier.validation_diffusion_state) ? 'oui' : 'non')
  const adminDiffusableState = props.diffusableDraft ?? isDiffusableValue(dossier.diffusable)

  return (
    <article className="mobile-detail-view">
      <header className="mobile-detail-hero">
        <button className="mobile-detail-close" type="button" onClick={props.onBack}>{props.backLabel}</button>
        {primaryImage ? (
          <button className="mobile-detail-photo" type="button" onClick={() => props.onOpenImage?.(primaryImage)}>
            <img src={primaryImage} alt={dossier.titre_bien} />
          </button>
        ) : <div className="mobile-detail-photo is-empty">Photo</div>}
        <div className="mobile-detail-title-card">
          <span>{props.detailVariant === 'mandat' ? 'Fiche mandat' : props.detailVariant === 'suivi' ? 'Suivi mandat' : 'Détail annonce'}</span>
          <h2>{dossier.titre_bien || dossier.numero_dossier || `Annonce ${dossier.hektor_annonce_id}`}</h2>
          {props.address ? <p>{props.address}</p> : null}
          <div className="mobile-status-row">
            <StatusPill value={dossier.statut_annonce} />
            <StatusPill value={diffusableLabel(dossier.diffusable)} />
            {dossier.validation_diffusion_state ? <StatusPill value={dossier.validation_diffusion_state} /> : null}
          </div>
        </div>
      </header>

      <section className="mobile-detail-actionbar" aria-label="Actions du dossier">
        <button className="mobile-primary-button" type="button" onClick={() => props.onOpenRequestModal?.(dossier.app_dossier_id, actionRole, 'demande_diffusion')}>Action métier</button>
        <button className="mobile-ghost-button" type="button" onClick={() => props.onOpenRequestModal?.(dossier.app_dossier_id, actionRole, 'demande_baisse_prix')}>Baisse prix</button>
        <button className="mobile-ghost-button" type="button" onClick={() => props.onOpenRequestModal?.(dossier.app_dossier_id, actionRole, 'demande_annulation_mandat')}>Annulation</button>
        {canShowDiffusion ? <button className="mobile-ghost-button" type="button" onClick={() => props.onOpenDiffusionModal?.(dossier.app_dossier_id)}>Diffusion</button> : null}
        {props.onDeleteAnnonce ? <button className="mobile-ghost-button mobile-danger-button" type="button" onClick={() => props.onDeleteAnnonce?.(dossier)}>Supprimer</button> : null}
      </section>

      {props.detailLoading ? <section className="mobile-detail-loading">Chargement du détail...</section> : null}

      <section className="mobile-detail-section">
        <div className="mobile-detail-section-head">
          <span>Synthèse</span>
          <strong>{dossier.commercial_nom ?? '-'}</strong>
        </div>
        <div className="mobile-detail-facts">
          {detailFacts.map(([label, value]) => (
            <div key={`mobile-fact-${label}`}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
        <button className="mobile-hektor-field-edit-button" type="button" onClick={() => setMobileHektorEditOpen((value) => !value)}>
          <span aria-hidden="true">M</span>
          Modifier les champs Hektor
        </button>
        {mobileHektorEditOpen ? (
          <div className="mobile-detail-embedded">
            <HektorAnnonceUpdateForm dossier={dossier} detail={props.detail} compact fieldPanel onCancel={() => setMobileHektorEditOpen(false)} onJobCreated={props.onHektorActionJobCreated} />
          </div>
        ) : null}
        <div className="mobile-detail-portals">
          {[
            ['LBC', ['leboncoin', 'le bon coin', 'lbc']],
            ['BI', ['bienici']],
            ['GTI', ['gti', 'sitegti', 'site gti']],
          ].map(([label, aliases]) => (
            <span key={label as string} className="mobile-portal-chip">
              {label as string}
              <PortalStatusMark enabled={(aliases as string[]).some((alias) => activePortals.some((portal) => portal.includes(alias.replace(/\s+/g, '')) || portal.includes(alias)))} />
            </span>
          ))}
        </div>
      </section>

      {canShowMandatePilot || props.allowMarkValidation || props.allowMarkDiffusable ? (
        <section className="mobile-detail-section mobile-detail-pilot">
          <div className="mobile-detail-section-head">
            <span>Pilotage Hektor</span>
            <strong>{props.markValidationPending || props.markDiffusablePending ? 'Synchronisation...' : 'Contrôle'}</strong>
          </div>
          {props.allowMarkValidation ? (
            <label className="mobile-toggle-row">
              <span>Mandat validé</span>
              <input type="checkbox" checked={isValidationApproved(adminValidationState)} onChange={(event) => props.onSetValidation?.(event.target.checked)} disabled={props.markValidationPending} />
            </label>
          ) : null}
          {props.allowMarkDiffusable ? (
            <label className="mobile-toggle-row">
              <span>Diffusable</span>
              <input type="checkbox" checked={adminDiffusableState} onChange={(event) => props.onSetDiffusable?.(event.target.checked)} disabled={props.markDiffusablePending} />
            </label>
          ) : null}
        </section>
      ) : null}

      <details className="mobile-detail-section mobile-detail-disclosure">
        <summary>Commercialisation</summary>
        <div className="mobile-detail-embedded">
          <PriceChangeHistoryCard
            source={props.detail.price_change_events_json ? props.detail : dossier}
            title="Historique des prix"
            emptyLabel="Aucun changement de prix historise pour cette annonce."
          />
        </div>
        <div className="mobile-transaction-stack">
          <article className="mobile-transaction-card">
            <div className="mobile-transaction-head">
              <span>01</span>
              <strong>Offre</strong>
              <StatusPill value={props.detail.offre_state ?? 'Non renseigne'} />
            </div>
            <div className="mobile-detail-lines">
              {offerFacts.map(([label, value]) => <div key={`mobile-offer-${label}`}><span>{label}</span><b>{value || '-'}</b></div>)}
            </div>
          </article>
          <article className="mobile-transaction-card">
            <div className="mobile-transaction-head">
              <span>02</span>
              <strong>Compromis</strong>
              <StatusPill value={props.detail.compromis_state ?? 'Non renseigne'} />
            </div>
            <div className="mobile-detail-lines">
              {compromisFacts.map(([label, value]) => <div key={`mobile-compromis-${label}`}><span>{label}</span><b>{value || '-'}</b></div>)}
            </div>
          </article>
          <article className="mobile-transaction-card">
            <div className="mobile-transaction-head">
              <span>03</span>
              <strong>Vente</strong>
              <StatusPill value={props.detail.vente_id ? 'Vente renseignee' : 'Non renseigne'} />
            </div>
            <div className="mobile-detail-lines">
              {saleFacts.map(([label, value]) => <div key={`mobile-sale-${label}`}><span>{label}</span><b>{value || '-'}</b></div>)}
            </div>
          </article>
        </div>
        <div className="mobile-detail-embedded">
          <AppointmentAnnonceSection dossier={dossier} detail={props.detail} />
        </div>
      </details>

      <details className="mobile-detail-section mobile-detail-disclosure">
        <summary>Caracteristiques</summary>
        <div className="mobile-detail-facts">
          {featureFacts.map(([label, value]) => (
            <div key={`mobile-feature-${label}`}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </details>

      <details className="mobile-detail-section mobile-detail-disclosure">
        <summary>Mandat et contacts</summary>
        <HektorMandantContactForm dossier={dossier} compact initialOpen={props.contacts.length === 0} onJobCreated={props.onHektorActionJobCreated} />
        {props.mandats.length > 0 ? props.mandats.map((mandat) => (
          <div key={`mobile-mandat-${mandat.id}`} className="mobile-detail-lines">
            <strong>{mandat.title}</strong>
            {mandat.lines.map(([label, value]) => <div key={`mobile-mandat-${mandat.id}-${label}`}><span>{label}</span><b>{value || '-'}</b></div>)}
          </div>
        )) : <p className="mobile-detail-muted">Aucun mandat detaille disponible.</p>}
        {props.contacts.length > 0 ? (
          <div className="mobile-contact-stack">
            {props.contacts.map((contact) => (
              <div key={`mobile-contact-${contact.id}`} className="mobile-contact-card">
                <span>{contact.role || 'Contact'}</span>
                <strong>{contact.name || '-'}</strong>
                {contact.phone ? <a href={`tel:${contact.phone}`}>{contact.phone}</a> : null}
                {contact.email ? <a href={`mailto:${contact.email}`}>{contact.email}</a> : null}
                {[contact.address, contact.postalCode, contact.city].filter(Boolean).length ? <p>{[contact.address, contact.postalCode, contact.city].filter(Boolean).join(', ')}</p> : null}
                {contact.comment ? <p>{contact.comment}</p> : null}
                <HektorMandantContactEditForm dossier={dossier} contact={contact} compact onJobCreated={props.onHektorActionJobCreated} />
              </div>
            ))}
          </div>
        ) : <p className="mobile-detail-muted">Aucun contact detaille.</p>}
      </details>

      <details className="mobile-detail-section mobile-detail-disclosure">
        <summary>Contenu de l'annonce</summary>
        <div className="mobile-console-documents">
          <ConsoleDocumentsPanel dossier={dossier} compact onJobCreated={props.onHektorActionJobCreated} />
        </div>
        {props.images.length > 0 ? (
          <div className="mobile-detail-gallery">
            {props.images.map((image) => (
              <button key={image.url} type="button" onClick={() => props.onOpenImage?.(image.url)}>
                <img src={image.url} alt={image.legend || dossier.titre_bien} loading="lazy" />
              </button>
            ))}
          </div>
        ) : null}
        {props.texts.map((text) => (
          <div key={text.id} className="mobile-detail-text">
            <strong>{text.title}</strong>
            <div className="mobile-rich-text" dangerouslySetInnerHTML={{ __html: text.html || '-' }} />
          </div>
        ))}
        {matterportModels.length > 0 ? (
          <div className="mobile-detail-lines">
            <strong>Visite virtuelle</strong>
            {matterportModels.map(({ group, model }) => (
              <div key={`${group.id}-${model.matterport_model_id}`}>
                <span>{group.group_label ?? `Mandat ${group.numero_mandat ?? '-'}`}</span>
                <b>{matterportModelLabel(model.label, model.matterport_name, false)}</b>
                <small>
                  {matterportStateLabel(model.state)} - {matterportVisibilityLabel(model.visibility)}
                  {model.matterport_url ? <a href={model.matterport_url} target="_blank" rel="noreferrer">Ouvrir</a> : null}
                </small>
              </div>
            ))}
          </div>
        ) : null}
      </details>

      <details className="mobile-detail-section mobile-detail-disclosure">
        <summary>Diffusion</summary>
        {activePortals.length > 0 ? (
          <div className="mobile-detail-lines">
            <strong>Portails actifs</strong>
            {activePortals.map((portal) => (
              <div key={`mobile-portal-${portal}`}>
                <span>{portal}</span>
                <b>{portalBrandLabel(portal)}</b>
              </div>
            ))}
          </div>
        ) : <p className="mobile-detail-muted">Aucun portail actif detecte.</p>}
        {requestItems.length > 0 ? (
          <div className="mobile-detail-timeline">
            {requestItems.map((item) => (
              <div key={`mobile-diffusion-history-${item.id}`} className="mobile-timeline-item">
                <span>{formatDate(item.date)}</span>
                <strong>{item.title}</strong>
                <p>{item.body}</p>
              </div>
            ))}
          </div>
        ) : null}
      </details>

      <details className="mobile-detail-section mobile-detail-disclosure">
        <summary>Historique et notes</summary>
        {requestItems.length > 0 ? requestItems.map((item) => (
          <div key={`mobile-history-${item.id}`} className="mobile-timeline-item">
            <span>{formatDate(item.date)}</span>
            <strong>{item.title}</strong>
            <p>{item.body}</p>
          </div>
        )) : <p className="mobile-detail-muted">Aucun historique de demande.</p>}
        {messageItems.map((item) => (
          <div key={`mobile-message-${item.id}`} className="mobile-timeline-item">
            <span>{formatDate(item.date)}</span>
            <strong>{item.author}</strong>
            <p>{item.message}</p>
          </div>
        ))}
        {props.notes.map((note) => (
          <div key={note.id} className="mobile-timeline-item">
            <span>{formatDate(note.date)}</span>
            <strong>{note.title}</strong>
            <p>{note.content}</p>
          </div>
        ))}
      </details>

      {props.linkedWorkItems.length > 0 ? (
        <details className="mobile-detail-section mobile-detail-disclosure">
          <summary>Demandes liées</summary>
          {props.linkedWorkItems.map((item) => (
            <div key={`mobile-work-${item.app_dossier_id}-${item.type_demande_label}-${item.date_entree_file ?? 'na'}`} className="mobile-timeline-item">
              <span>{formatDate(item.date_entree_file)}</span>
              <strong>{item.type_demande_label ?? '-'}</strong>
              <p>{item.work_status ?? '-'} · {item.internal_status ?? '-'}</p>
            </div>
          ))}
        </details>
      ) : null}
    </article>
  )
}

function MobileMandatCards(props: {
  mandats: MandatRecord[]
  total: number
  loading: boolean
  mode: 'active' | 'estimation'
  onOpenDetailPage: (id: number) => void
  onOpenRequestModal: (id: number, role?: 'nego' | 'pauline') => void
}) {
  const title = props.mode === 'estimation' ? 'Estimations' : 'Annonces actives'
  const primaryLabel = props.mode === 'estimation' ? 'Voir estimation' : 'Voir le détail'
  if (props.mandats.length === 0) {
    return <section className="mobile-empty-card">{props.loading ? 'Chargement...' : 'Aucune ligne disponible.'}</section>
  }
  return (
    <section className="mobile-card-list" aria-label={title}>
      <div className="mobile-list-head">
        <div>
          <span className="mobile-section-kicker">{props.mode === 'estimation' ? 'Projets' : 'Portefeuille'}</span>
          <h2>{title}</h2>
        </div>
        <span>{props.mandats.length} / {props.total}</span>
      </div>
      {props.mandats.map((item, index) => {
        const hasLeboncoin = hasPortalEnabled(item, ['leboncoin', 'le bon coin', 'lbc'])
        const hasBienici = hasPortalEnabled(item, ['bienici'])
        const hasSiteGti = isSiteGtiEnabled(item)
        const cardKey = [
          props.mode,
          item.app_dossier_id,
          item.numero_mandat ?? 'no-mandat',
          item.numero_dossier ?? 'no-dossier',
          item.register_source_kind ?? 'current',
          index,
        ].join('-')
        return (
          <article key={cardKey} className="mobile-list-card">
            <div className="mobile-card-top">
              <ListingThumbnail url={item.photo_url_listing} imagesPreviewJson={item.images_preview_json} title={item.titre_bien} />
              <div className="mobile-list-card-main">
                <span className="mobile-card-meta">{item.numero_mandat ? `Mandat ${item.numero_mandat}` : item.numero_dossier ?? '-'}</span>
                <strong>{item.titre_bien}</strong>
                <span className="mobile-card-subline">{propertyTypeLabel(item.type_bien)} · {item.ville ?? item.agence_nom ?? '-'}</span>
              </div>
            </div>
            <div className="mobile-card-grid">
              <div><span className="mobile-mini-label">Prix</span><strong>{formatPrice(item.prix)}</strong></div>
              <div><span className="mobile-mini-label">Négociateur</span><strong>{commercialDisplay(item)}</strong></div>
            </div>
            <div className="mobile-status-row">
              <StatusPill value={props.mode === 'estimation' ? listingProgressLabel(item) : item.statut_annonce} />
              <span className="mobile-portal-chip">LBC <PortalStatusMark enabled={hasLeboncoin} /></span>
              <span className="mobile-portal-chip">BI <PortalStatusMark enabled={hasBienici} /></span>
              <span className="mobile-portal-chip">GTI <PortalStatusMark enabled={hasSiteGti} /></span>
            </div>
            <div className="mobile-card-actions">
              {props.mode === 'active' ? <button className="mobile-ghost-button" type="button" onClick={() => props.onOpenRequestModal(item.app_dossier_id, 'nego')}>Action métier</button> : null}
              <button className="mobile-primary-button" type="button" onClick={() => props.onOpenDetailPage(item.app_dossier_id)}>{primaryLabel}</button>
            </div>
          </article>
        )
      })}
    </section>
  )
}

function MobileRegisterCards(props: {
  mandats: MandatRecord[]
  total: number
  loading: boolean
  onSelectMandat: (registerRowId: string) => void
}) {
  if (props.mandats.length === 0) {
    return <section className="mobile-empty-card">{props.loading ? 'Chargement...' : 'Aucun mandat disponible.'}</section>
  }
  return (
    <section className="mobile-card-list" aria-label="Registre des mandats">
      <div className="mobile-list-head">
        <div>
          <span className="mobile-section-kicker">Registre</span>
          <h2>Mandats</h2>
        </div>
        <span>{props.mandats.length} / {props.total}</span>
      </div>
      {props.mandats.map((item) => (
        <article key={mandateRegisterRowKey(item)} className="mobile-list-card">
          <div className="mobile-card-top">
            <ListingThumbnail url={item.photo_url_listing} imagesPreviewJson={item.images_preview_json} title={item.titre_bien || `Mandat ${item.numero_mandat ?? '-'}`} />
            <div className="mobile-list-card-main">
              <span className="mobile-card-meta">{mandateRegisterTypeInlineLabel(item) || mandateRegisterSourceLabel(item)}</span>
              <strong>Mandat {item.numero_mandat ?? '-'}</strong>
              <span className="mobile-card-subline">{mandateRegisterMandantsLabel(item)}</span>
            </div>
          </div>
          <div className="mobile-card-grid">
            <div><span className="mobile-mini-label">Montant</span><strong>{formatPrice(item.mandat_montant ?? item.prix)}</strong></div>
            <div><span className="mobile-mini-label">Fin</span><strong>{formatDate(item.mandat_date_fin)}</strong></div>
          </div>
          <div className="mobile-status-row">
            <StatusPill value={item.statut_annonce} />
            <StatusPill value={mandateRegisterDiffusableLabel(item.diffusable)} />
          </div>
          <span className="mobile-card-subline">{mandateRegisterNatureLabel(item)}</span>
          <div className="mobile-card-actions">
            <button className="mobile-primary-button" type="button" onClick={() => props.onSelectMandat(mandateRegisterRowKey(item))}>Voir le mandat</button>
          </div>
        </article>
      ))}
    </section>
  )
}

function MobileDossierCards(props: {
  dossiers: Dossier[]
  total: number
  loading: boolean
  hektorActionJobs: ConsoleJob[]
  onFocusDossier: (id: number) => void
  onOpenDetail: () => void
}) {
  if (props.dossiers.length === 0 && props.hektorActionJobs.length === 0) {
    return <section className="mobile-empty-card">{props.loading ? 'Chargement...' : 'Aucun dossier disponible.'}</section>
  }
  return (
    <section className="mobile-card-list" aria-label="Annonces">
      <div className="mobile-list-head">
        <div>
          <span className="mobile-section-kicker">Stock</span>
          <h2>Annonces</h2>
        </div>
        <span>{props.dossiers.length} / {props.total}</span>
      </div>
      {props.hektorActionJobs.map((job) => (
        <article key={`mobile-hektor-job-${job.id}`} className={`mobile-list-card mobile-hektor-job-card mobile-hektor-job-card-${hektorActionJobTone(job)}`}>
          <span className="mobile-card-meta">{hektorActionJobLabel(job)}</span>
          <strong>{hektorActionJobTitle(job)}</strong>
          <span className="mobile-card-subline">{hektorActionJobDetail(job)}</span>
        </article>
      ))}
      {props.dossiers.map((item) => (
        <article key={`mobile-dossier-${item.app_dossier_id}`} className="mobile-list-card">
          <div className="mobile-card-top">
            <ListingThumbnail url={item.photo_url_listing} imagesPreviewJson={item.images_preview_json} title={item.titre_bien} />
            <div className="mobile-list-card-main">
              <span className="mobile-card-meta">{item.numero_dossier ?? '-'}</span>
              <strong>{item.titre_bien}</strong>
              <span className="mobile-card-subline">{propertyTypeLabel(item.type_bien)} · {item.ville ?? '-'}</span>
            </div>
          </div>
          <div className="mobile-card-grid">
            <div><span className="mobile-mini-label">Prix</span><strong>{formatPrice(item.prix)}</strong></div>
            <div><span className="mobile-mini-label">Négociateur</span><strong>{commercialDisplay(item)}</strong></div>
          </div>
          <div className="mobile-status-row">
            <StatusPill value={item.statut_annonce} />
            <StatusPill value={diffusableLabel(item.diffusable)} />
          </div>
          <div className="mobile-card-actions">
            <button
              className="mobile-primary-button"
              type="button"
              onClick={() => {
                props.onFocusDossier(item.app_dossier_id)
                props.onOpenDetail()
              }}
            >
              Voir le détail
            </button>
          </div>
        </article>
      ))}
    </section>
  )
}

function StatusPill({ value }: { value: string | null }) {
  if (!value) return null
  const normalized = safeText(value).toLowerCase()
  const toneClass =
    normalized === 'actif'
      ? ' status-pill-state-active'
      : normalized.includes('offre')
        ? ' status-pill-state-offer'
        : normalized.includes('compromis')
          ? ' status-pill-state-compromis'
          : normalized.includes('vendu') || normalized.includes('vente')
            ? ' status-pill-state-sold'
            : normalized.includes('clos') || normalized.includes('clotur')
              ? ' status-pill-state-closed'
              : normalized.includes('archive')
                ? ' status-pill-state-archived'
                : normalized.includes('historique')
                  ? ' status-pill-state-history'
                  : ''
  return <span className={`status-pill${toneClass}`}>{value}</span>
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
    <article className="detail-card price-history-panel">
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
