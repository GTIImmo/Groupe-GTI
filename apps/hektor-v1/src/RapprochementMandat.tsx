import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  loadRapprochementsForDossier, loadDossierTimeline,
  recordProposition, setBienStatut, sendGoogleWorkspaceCrmEmail, loadGoogleCalendarEventLinks,
  type RapprochementForDossierRow, type TimelineRow, type GoogleCalendarEventLink,
} from './lib/api'
import type { VisitePlanInput } from './RechercheAcquereur'

/**
 * Rapprochement Mandat → Acquéreurs — écran inverse (bien → acquéreurs).
 *
 * Transposition fidèle (React) du prototype ui_kits/console/rapprochement-mandat.html
 * (handoff Claude Design / GTI). Part d'UN bien (mandat) et liste les acquéreurs dont
 * la recherche active correspond, triés par score décroissant. Branché sur le vrai
 * moteur de scoring v2 (RPC app_get_rapprochements_for_dossier). Le couple bien×recherche
 * partage les mêmes tables d'action que l'écran Recherche Acquéreur : toute proposition /
 * statut / visite tracée ici apparaît aussi côté acquéreur, et inversement.
 *
 * Styles scopés dans recherche-mandat.css sous `.rapp-mandat`.
 */

type Status = 'todo' | 'propose' | 'visite' | 'ecarte'
type Group = 'todo' | 'encours' | 'ecarte'
type FilterKey = 'all' | 'todo' | 'encours' | 'ecarte'
type SortKey = 'score' | 'budget' | 'nouveaute'
type Channel = 'email' | 'telephone' | 'visite'
interface Crit { k: string; ok: boolean; v: string }

interface Buyer {
  searchKey: string
  contactId: string | null
  name: string
  initials: string
  email: string | null
  phone: string | null
  ownerNom: string | null
  budgetMin: number | null
  budgetMax: number | null
  budgetLabel: string
  score: number
  scoreClass: 's-green' | 's-gold' | 's-red'
  status: Status
  group: Group
  statusLabel: string
  crit: Crit[]
  date: string
  briefType: string | null
  briefVilles: string[]
  briefBudget: string | null
  briefSurfaceMin: string | null
  briefPiecesMin: string | null
  isNew?: boolean
  sel?: boolean
}

export interface MandatContext {
  appDossierId: number
  hektorAnnonceId: number | null
  numeroMandat: string | null
  numeroDossier: string | null
  titre: string
  type: string | null
  ville: string | null
  codePostal: string | null
  prix: number | null
  surface: number | null
  photo: string | null
  statut: string | null
  negociateurNom: string | null
  negociateurEmail: string | null
  agence: string | null
}

export interface RapprochementMandatProps {
  open: boolean
  onClose: () => void
  mandat: MandatContext | null
  senderEmail?: string | null
  visitRefreshKey?: number
  onOpenContact?: (hektorContactId: string) => void
  onPlanifierVisite?: (input: VisitePlanInput) => void
  onImprimerBonVisite?: (event: GoogleCalendarEventLink) => void
  onModifierRdv?: (event: GoogleCalendarEventLink) => void
  onSupprimerRdv?: (event: GoogleCalendarEventLink) => void
}

const GTI_DOMAIN = 'gti-immobilier.fr'
const STATUS_LABEL: Record<Status, string> = { todo: 'À contacter', propose: 'En cours', visite: 'Visite', ecarte: 'Écarté' }

const MAIL_TEMPLATES = {
  contact: {
    subj: 'Un bien correspond à votre recherche',
    msg: "Bonjour,\n\nUn bien que je commercialise correspond à votre projet d'acquisition. Je vous le transmets en priorité — dites-moi s'il vous intéresse et je vous organise une visite.\n\nBien à vous,",
  },
  coup: {
    subj: 'Un bien à ne pas manquer',
    msg: "Bonjour,\n\nJ'ai un bien qui colle particulièrement à vos critères — à voir rapidement selon moi. Voici les détails, je reste à votre disposition pour une visite.\n\nBien à vous,",
  },
} as const
type TemplateKey = keyof typeof MAIL_TEMPLATES

/* ----------------------------- icônes ----------------------------- */
const IcSend = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M22 4 11 15M22 4l-7 18-4-9-9-4 20-5Z" /></svg>
const IcClose = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 6l12 12M18 6 6 18" /></svg>
const IcBell = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" /></svg>
const IcCheck = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5 10 17 19 7" /></svg>
const IcX3 = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M6 6l12 12M18 6 6 18" /></svg>
const IcCal = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></svg>
const IcPhone = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07A19.5 19.5 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92Z" /></svg>
const IcMail = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="m2 8 10 7 10-7" /></svg>
const IcEuro = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 7a7 7 0 1 0 0 10M4 10h9M4 14h7" /></svg>
const IcPin = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>

const fmtEuro = (n: number | null | undefined) => (n != null && Number.isFinite(Number(n)) ? `${Math.round(Number(n)).toLocaleString('fr-FR')} €` : '—')
const fmtDate = (iso: string): string => { const d = new Date(iso); return Number.isFinite(d.getTime()) ? d.toLocaleDateString('fr-FR') : '' }
const initialsOf = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]?.toUpperCase() ?? '').join('') || 'AC'
const htmlEsc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const isRecent = (iso: string | null) => { if (!iso) return false; const t = new Date(iso).getTime(); return Number.isFinite(t) && (Date.now() - t) < 7 * 86400000 }

// Statut couple → modèle de carte
function mapStatus(st: string | null): { status: Status; group: Group } {
  if (st === 'ecarte') return { status: 'ecarte', group: 'ecarte' }
  if (st === 'visite') return { status: 'visite', group: 'encours' }
  if (st === 'propose') return { status: 'propose', group: 'encours' }
  return { status: 'todo', group: 'todo' }
}

// Premier type de bien recherché (types_json = { code: label }).
function parseFirstTypeLabel(tj: Record<string, string> | string[] | null): string | null {
  if (!tj) return null
  if (Array.isArray(tj)) { const v = tj.map((x) => String(x).trim()).filter(Boolean)[0]; return v || null }
  for (const [k, v] of Object.entries(tj as Record<string, unknown>)) {
    const s = String(v ?? '').trim()
    if (s && s !== '0' && s.toLowerCase() !== 'false') return s !== '1' ? s : k
  }
  return null
}
// Communes recherchées (villes_json = tableau ou objet).
function parseVilles(vj: Record<string, string> | string[] | null): string[] {
  if (!vj) return []
  const raw = Array.isArray(vj) ? vj : Object.values(vj as Record<string, unknown>)
  return raw
    .map((x) => String(x ?? '').replace(/\b\d{5}\b/g, '').replace(/[()]/g, '').replace(/\s+/g, ' ').trim())
    .filter(Boolean)
}
// Budget compact en k€ pour le résumé de recherche.
function compactBudget(min: number | null, max: number | null): string | null {
  const k = (n: number) => `${Math.round(n / 1000)}`
  if (min != null && max != null) return `${k(min)}–${k(max)} k€`
  if (max != null) return `≤ ${k(max)} k€`
  if (min != null) return `≥ ${k(min)} k€`
  return null
}
// Pourcentage lisible dans un libellé de composant ("85 %"), sinon null.
function critPct(v: string): number | null {
  const m = v.match(/(\d+)\s*%/)
  return m ? Math.min(100, Number(m[1])) : null
}

function rowToBuyer(r: RapprochementForDossierRow): Buyer {
  const name = (r.display_name || `${r.prenom ?? ''} ${r.nom ?? ''}`).trim() || 'Acquéreur'
  const { status, group } = mapStatus(r.statut)
  const min = r.prix_min != null ? Number(r.prix_min) : null
  const max = r.prix_max != null ? Number(r.prix_max) : null
  const budgetLabel = min != null && max != null ? `${Math.round(min).toLocaleString('fr-FR')} – ${Math.round(max).toLocaleString('fr-FR')} €`
    : max != null ? `≤ ${Math.round(max).toLocaleString('fr-FR')} €`
    : min != null ? `≥ ${Math.round(min).toLocaleString('fr-FR')} €`
    : 'Budget non précisé'
  const scoreClass: Buyer['scoreClass'] = r.score >= 85 ? 's-green' : r.score >= 70 ? 's-gold' : 's-red'
  const dateFoot = status === 'ecarte' ? (r.statut_reason ? `Écarté · ${r.statut_reason}` : 'Écarté par le négociateur')
    : status === 'visite' ? 'Visite prévue'
    : status === 'propose' ? `Proposé${r.statut_channel ? ` · ${r.statut_channel}` : ''}${r.proposed_at ? ` le ${fmtDate(r.proposed_at)}` : ''}`
    : r.first_seen_at ? `Détecté le ${fmtDate(r.first_seen_at)}` : 'Nouveau profil correspondant'
  return {
    searchKey: r.contact_search_key,
    contactId: r.hektor_contact_id,
    name, initials: initialsOf(name),
    email: r.email?.trim() || null,
    phone: r.phone?.trim() || null,
    ownerNom: r.owner_commercial_nom?.trim() || null,
    budgetMin: min, budgetMax: max, budgetLabel,
    score: r.score, scoreClass, status, group,
    statusLabel: STATUS_LABEL[status],
    crit: (r.components ?? []).map((c) => ({ k: c.k, ok: c.ok, v: c.v })),
    date: dateFoot,
    briefType: parseFirstTypeLabel(r.types_json),
    briefVilles: parseVilles(r.villes_json),
    briefBudget: compactBudget(min, max),
    briefSurfaceMin: r.surface_min != null ? `≥ ${Math.round(Number(r.surface_min))} m²` : null,
    briefPiecesMin: r.pieces_min != null ? `≥ ${Math.round(Number(r.pieces_min))} pièces` : null,
    isNew: status === 'todo' && isRecent(r.first_seen_at),
  }
}

// Corps HTML de l'email : message + carte du bien (mandat) + signature.
function buildEmailHtml(message: string, m: MandatContext, signature: string): string {
  const intro = htmlEsc(message).replace(/\n/g, '<br>')
  const ref = m.numeroMandat || m.numeroDossier || (m.hektorAnnonceId ? `V${m.hektorAnnonceId}` : `#${m.appDossierId}`)
  const specs = [m.surface != null ? `${Math.round(Number(m.surface))} m²` : '', m.type ?? ''].filter(Boolean).join(' · ')
  const card = `
    <table role="presentation" style="width:100%;border-collapse:collapse;margin:10px 0;border:1px solid #e2e5e6;border-radius:8px;overflow:hidden">
      <tr>
        ${m.photo ? `<td style="width:150px;vertical-align:top"><img src="${m.photo}" width="150" style="display:block;width:150px;height:112px;object-fit:cover" alt=""></td>` : ''}
        <td style="padding:10px 14px;vertical-align:top;font-family:Arial,Helvetica,sans-serif">
          <div style="font-size:12px;color:#9da0a0">${htmlEsc(ref)}${m.ville ? ` · ${htmlEsc(m.ville)}` : ''}</div>
          <div style="font-size:15px;font-weight:bold;color:#222323;margin:2px 0">${htmlEsc(m.titre)}</div>
          <div style="font-size:15px;color:#c5005f;font-weight:bold">${fmtEuro(m.prix)}</div>
          <div style="font-size:12px;color:#5c6163;margin-top:3px">${htmlEsc(specs)}</div>
        </td>
      </tr>
    </table>`
  return `<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222323;line-height:1.5">${intro}<br><br>${card}<br><div style="color:#5c6163;font-size:13px;white-space:pre-line">${htmlEsc(signature)}</div></div>`
}

function MatchTags({ crit }: { crit: Crit[] }) {
  return (
    <div className="ac-match">
      {crit.slice(0, 6).map((c) => (
        <span className={`mt${c.ok ? '' : ' no'}`} key={c.k}>{c.ok ? <IcCheck /> : <IcX3 />}{c.k}</span>
      ))}
    </div>
  )
}

export default function RapprochementMandat({ open, onClose, mandat, senderEmail, visitRefreshKey, onOpenContact, onPlanifierVisite, onImprimerBonVisite, onModifierRdv, onSupprimerRdv }: RapprochementMandatProps) {
  const [buyers, setBuyers] = useState<Buyer[]>([])
  const [filter, setFilter] = useState<FilterKey>('all')
  const [sort, setSort] = useState<SortKey>('score')
  const [seuil, setSeuil] = useState(75)
  const [alerteOpen, setAlerteOpen] = useState(false)
  const [discMode, setDiscMode] = useState(false)
  const [discIdx, setDiscIdx] = useState(0)
  const [swipe, setSwipe] = useState<'' | 'left' | 'right'>('')
  const [timeline, setTimeline] = useState<TimelineRow[]>([])
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)
  const [visitEvents, setVisitEvents] = useState<Record<string, GoogleCalendarEventLink>>({})
  const [toasts, setToasts] = useState<{ id: number; msg: string }[]>([])

  // popovers
  const [chanKeys, setChanKeys] = useState<string[] | null>(null)
  const [mailKeys, setMailKeys] = useState<string[] | null>(null)
  const [mailTpl, setMailTpl] = useState<TemplateKey>('contact')
  const [mailSubj, setMailSubj] = useState<string>(MAIL_TEMPLATES.contact.subj)
  const [mailMsg, setMailMsg] = useState<string>(MAIL_TEMPLATES.contact.msg)
  const [confirmSend, setConfirmSend] = useState(false)
  const [sending, setSending] = useState(false)

  const toastId = useRef(0)
  const toast = useCallback((msg: string) => {
    const id = ++toastId.current
    setToasts((t) => [...t, { id, msg }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2800)
  }, [])

  const dossierId = mandat?.appDossierId ?? null
  const negoEmail = mandat?.negociateurEmail ?? null
  const bienPrix = mandat?.prix ?? null

  // Chargement : rapprochements inversés + timeline du bien
  useEffect(() => {
    if (!open || dossierId == null) { setBuyers([]); setTimeline([]); return }
    let cancelled = false
    setLoading(true); setLoadError(null)
    Promise.all([loadRapprochementsForDossier(dossierId), loadDossierTimeline(dossierId)])
      .then(([rows, tl]: [RapprochementForDossierRow[], TimelineRow[]]) => {
        if (cancelled) return
        setBuyers(rows.map((r) => rowToBuyer(r)))
        setTimeline(tl)
      })
      .catch((e) => { if (!cancelled) { setLoadError(e?.message ?? 'Erreur de chargement'); setBuyers([]); setTimeline([]) } })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, dossierId, visitRefreshKey, reloadKey])

  // RDV "visite" Google de ce bien, indexés par clé de recherche (couple bien×acquéreur)
  useEffect(() => {
    if (!open || dossierId == null) { setVisitEvents({}); return }
    let cancelled = false
    loadGoogleCalendarEventLinks({ appDossierId: dossierId, limit: 200 })
      .then((events) => {
        if (cancelled) return
        const map: Record<string, GoogleCalendarEventLink> = {}
        for (const e of events) {
          if (e.event_type !== 'visite') continue
          if (e.status && e.status !== 'active') continue
          const sk = (e.metadata_json as Record<string, unknown> | null)?.contact_search_key
          const key = typeof sk === 'string' ? sk : e.hektor_contact_id ? `c:${e.hektor_contact_id}` : null
          if (!key) continue
          const prev = map[key]
          if (!prev || (e.starts_at || '') > (prev.starts_at || '')) map[key] = e
        }
        setVisitEvents(map)
      })
      .catch(() => { if (!cancelled) setVisitEvents({}) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, dossierId, visitRefreshKey, reloadKey])

  /* --------------------------- dérivés --------------------------- */
  const counts = useMemo(() => ({
    all: buyers.length,
    todo: buyers.filter((b) => b.group === 'todo').length,
    encours: buyers.filter((b) => b.group === 'encours').length,
    ecarte: buyers.filter((b) => b.group === 'ecarte').length,
  }), [buyers])
  const newCount = useMemo(() => buyers.filter((b) => b.isNew).length, [buyers])
  const avgScore = useMemo(() => buyers.length ? Math.round(buyers.reduce((s, b) => s + b.score, 0) / buyers.length) : 0, [buyers])
  const hot85 = useMemo(() => buyers.filter((b) => b.score >= 85).length, [buyers])

  const sorted = useMemo(() => {
    if (sort === 'score') return buyers
    const arr = [...buyers]
    if (sort === 'budget') arr.sort((a, b) => (b.budgetMax ?? 0) - (a.budgetMax ?? 0))
    else if (sort === 'nouveaute') arr.sort((a, b) => Number(!!b.isNew) - Number(!!a.isNew) || b.score - a.score)
    return arr
  }, [buyers, sort])

  const visible = useMemo(
    () => sorted.filter((b) =>
      (filter === 'all' || b.group === filter) &&
      (b.group !== 'todo' || b.score >= seuil)),
    [sorted, filter, seuil],
  )
  const hiddenByCursor = useMemo(
    () => sorted.filter((b) => (filter === 'all' || b.group === filter) && b.group === 'todo' && b.score < seuil).length,
    [sorted, filter, seuil],
  )
  const selKeys = useMemo(() => buyers.filter((b) => b.sel).map((b) => b.searchKey), [buyers])

  // relances dérivées : proposés sans visite (les + anciens en tête)
  const relances = useMemo(() => buyers
    .filter((b) => b.status === 'propose')
    .slice(0, 6)
    .map((b) => ({ key: b.searchKey, name: b.name, initials: b.initials, sub: b.date })), [buyers])

  const discPool = useMemo(() => visible.filter((b) => b.status !== 'ecarte'), [visible])

  const buyersByKeys = useCallback((keys: string[]) => buyers.filter((b) => keys.includes(b.searchKey)), [buyers])

  /* --------------------------- actions --------------------------- */
  const applyLocal = useCallback((keys: string[], patch: Partial<Buyer>) => {
    setBuyers((list) => list.map((b) => keys.includes(b.searchKey) ? { ...b, ...patch } : b))
  }, [])

  const propose = useCallback((keys: string[], chan: Channel, gmail?: { messageId?: string | null; threadId?: string | null }) => {
    if (dossierId == null) return
    applyLocal(keys, { status: 'propose', group: 'encours', statusLabel: STATUS_LABEL.propose, date: `Proposé · ${chan}`, sel: false })
    Promise.all(keys.map((k) => recordProposition(k, dossierId, chan, null, negoEmail, gmail?.messageId ?? null, gmail?.threadId ?? null)))
      .then(() => setReloadKey((x) => x + 1))
      .catch((e) => toast(`Erreur d'enregistrement : ${e?.message ?? ''}`))
    toast(`Bien proposé à ${keys.length} acquéreur(s) par ${chan}.`)
  }, [dossierId, negoEmail, applyLocal, toast])

  const ecarter = useCallback((keys: string[]) => {
    if (dossierId == null) return
    applyLocal(keys, { status: 'ecarte', group: 'ecarte', statusLabel: STATUS_LABEL.ecarte, date: 'Écarté par le négociateur', sel: false })
    Promise.all(keys.map((k) => setBienStatut(k, dossierId, 'ecarte', null, negoEmail))).catch((e) => toast(`Erreur : ${e?.message ?? ''}`))
    toast(`${keys.length} acquéreur(s) écarté(s) de ce rapprochement.`)
  }, [dossierId, negoEmail, applyLocal, toast])

  const restore = useCallback((key: string) => {
    if (dossierId == null) return
    applyLocal([key], { status: 'todo', group: 'todo', statusLabel: STATUS_LABEL.todo, date: 'Rétabli · à contacter' })
    setBienStatut(key, dossierId, 'jamais_vu', null, negoEmail).catch(() => {})
    toast('Acquéreur rétabli dans « À contacter ».')
  }, [dossierId, negoEmail, applyLocal, toast])

  const toggleSel = useCallback((key: string) => {
    setBuyers((list) => list.map((b) => b.searchKey === key ? { ...b, sel: !b.sel } : b))
  }, [])
  const clearSel = useCallback(() => setBuyers((list) => list.map((b) => b.sel ? { ...b, sel: false } : b)), [])

  const openChan = useCallback((keys: string[]) => { if (keys.length) setChanKeys(keys) }, [])

  const openMail = useCallback((keys: string[]) => {
    setMailKeys(keys); setMailTpl('contact'); setMailSubj(MAIL_TEMPLATES.contact.subj); setMailMsg(MAIL_TEMPLATES.contact.msg)
  }, [])

  const openVisit = useCallback((keys: string[]) => {
    setChanKeys(null)
    if (keys.length !== 1) { toast('La visite se planifie pour un acquéreur à la fois.'); return }
    const b = buyers.find((x) => x.searchKey === keys[0])
    if (!b || !mandat || dossierId == null) { toast('Acquéreur introuvable pour la visite.'); return }
    if (!onPlanifierVisite) { toast('Planification de visite indisponible ici.'); return }
    onPlanifierVisite({
      appDossierId: dossierId,
      hektorAnnonceId: mandat.hektorAnnonceId ?? null,
      titre: mandat.titre,
      ville: mandat.ville ?? null,
      numeroMandat: mandat.numeroMandat ?? null,
      numeroDossier: mandat.numeroDossier ?? null,
      photo: mandat.photo ?? null,
      acquereurEmail: b.email ?? null,
      acquereurContactId: b.contactId ?? null,
      acquereurName: b.name,
      contactSearchKey: b.searchKey,
      calendarEmail: senderEmail ?? null,
      negoCommercialNom: mandat.negociateurNom ?? null,
      negoAgenceNom: mandat.agence ?? null,
    })
  }, [buyers, mandat, dossierId, onPlanifierVisite, senderEmail, toast])

  const applyTemplate = useCallback((t: TemplateKey) => { setMailTpl(t); setMailSubj(MAIL_TEMPLATES[t].subj); setMailMsg(MAIL_TEMPLATES[t].msg) }, [])

  const chooseChannel = useCallback((chan: Channel) => {
    const keys = chanKeys ?? []
    setChanKeys(null)
    if (chan === 'email') openMail(keys)
    else if (chan === 'visite') openVisit(keys)
    else propose(keys, chan)
  }, [chanKeys, openMail, openVisit, propose])

  const senderValid = Boolean(senderEmail && senderEmail.toLowerCase().endsWith(`@${GTI_DOMAIN}`))
  const mailBuyers = useMemo(() => buyersByKeys(mailKeys ?? []), [buyersByKeys, mailKeys])
  const mailRecipients = useMemo(() => mailBuyers.filter((b) => b.email), [mailBuyers])
  const canSendEmail = senderValid && mailRecipients.length > 0

  const requestSend = useCallback(() => {
    if (!senderValid) { toast('Adresse Gmail négociateur invalide (@gti-immobilier.fr requise).'); return }
    if (mailRecipients.length === 0) { toast('Aucun acquéreur avec une adresse email — envoi impossible.'); return }
    setConfirmSend(true)
  }, [senderValid, mailRecipients.length, toast])

  // Envoi réel Gmail : un email individuel par acquéreur destinataire. Proposition tracée par succès.
  const confirmAndSend = useCallback(async () => {
    if (sending || !mandat || !senderEmail || dossierId == null) return
    setSending(true)
    const signature = `${mandat.negociateurNom || 'Groupe GTI'}\n${mandat.agence || 'Groupe GTI'}`
    const bodyHtml = buildEmailHtml(mailMsg, mandat, signature)
    let okCount = 0
    const sentKeys: string[] = []
    for (const b of mailRecipients) {
      try {
        const res = await sendGoogleWorkspaceCrmEmail({
          subjectEmail: senderEmail,
          to: [b.email as string],
          subject: mailSubj,
          bodyText: mailMsg,
          bodyHtml,
          fromName: mandat.negociateurNom ? `${mandat.negociateurNom} - GTI Immobilier` : 'GTI Immobilier',
          replyTo: senderEmail,
          relatedEntityType: 'annonce',
          relatedEntityId: mandat.hektorAnnonceId != null ? String(mandat.hektorAnnonceId) : null,
        })
        if (!res?.ok) throw new Error('refusé')
        await recordProposition(b.searchKey, dossierId, 'email', null, negoEmail, res?.messageId ?? null, res?.threadId ?? null).catch(() => {})
        sentKeys.push(b.searchKey)
        okCount += 1
      } catch { /* on continue les autres destinataires */ }
    }
    if (sentKeys.length) applyLocal(sentKeys, { status: 'propose', group: 'encours', statusLabel: STATUS_LABEL.propose, date: `Proposé · email le ${new Date().toLocaleDateString('fr-FR')}`, sel: false })
    setSending(false); setConfirmSend(false); setMailKeys(null)
    setReloadKey((x) => x + 1)
    toast(okCount === mailRecipients.length ? `Email envoyé à ${okCount} acquéreur(s).` : `${okCount}/${mailRecipients.length} envoyé(s) — les échecs n'ont pas été tracés.`)
  }, [sending, mandat, senderEmail, dossierId, mailMsg, mailSubj, mailRecipients, negoEmail, applyLocal, toast])

  /* --------------------------- discovery --------------------------- */
  const discGo = useCallback((d: number) => {
    setSwipe('')
    setDiscIdx((i) => { const n = discPool.length; if (!n) return 0; return Math.min(Math.max(0, i + d), n - 1) })
  }, [discPool.length])

  const discAction = useCallback((action: 'ecart' | 'propose') => {
    const b = discPool[Math.min(discIdx, discPool.length - 1)]
    if (!b) return
    if (action === 'ecart') {
      setSwipe('left')
      setTimeout(() => { ecarter([b.searchKey]); setSwipe(''); setDiscIdx((i) => i) }, 360)
    } else {
      setSwipe('right')
      setTimeout(() => { setSwipe(''); openChan([b.searchKey]); setDiscIdx((i) => Math.min(i + 1, Math.max(0, discPool.length - 1))) }, 360)
    }
  }, [discPool, discIdx, ecarter, openChan])

  useEffect(() => { if (discIdx >= discPool.length) setDiscIdx(Math.max(0, discPool.length - 1)) }, [discPool.length, discIdx])

  // raccourcis clavier
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (confirmSend) { if (!sending) setConfirmSend(false); return }
        if (mailKeys) { setMailKeys(null); return }
        if (chanKeys) { setChanKeys(null); return }
        onClose(); return
      }
      if (discMode && !chanKeys && !mailKeys && !confirmSend) {
        if (e.key === 'ArrowLeft') discAction('ecart')
        else if (e.key === 'ArrowRight') discAction('propose')
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, discMode, chanKeys, mailKeys, confirmSend, sending, discAction, onClose])

  if (!open || !mandat) return null

  const ref = mandat.numeroMandat || mandat.numeroDossier || (mandat.hektorAnnonceId ? `V${mandat.hektorAnnonceId}` : `#${mandat.appDossierId}`)
  const crumb = `${mandat.type || 'Bien'}${mandat.ville ? ` · ${mandat.ville}` : ''}`
  const negoInitials = mandat.negociateurNom ? initialsOf(mandat.negociateurNom) : 'GTI'
  const specs = [
    mandat.surface != null ? `${Math.round(Number(mandat.surface))} m²` : '',
    mandat.type ?? '',
  ].filter(Boolean)
  const budgetState = (b: Buyer): 'ok' | 'warn' | 'bad' | 'na' => {
    if (b.budgetMax == null || bienPrix == null) return 'na'
    if (bienPrix <= b.budgetMax) return 'ok'
    if (bienPrix <= b.budgetMax * 1.05) return 'warn'
    return 'bad'
  }
  const budgetHintLabel: Record<'ok' | 'warn' | 'bad' | 'na', string> = { ok: '✓ Dans le budget', warn: '⚠ Limite haute', bad: '✗ Au-dessus', na: 'Budget non précisé' }

  const renderActions = (b: Buyer) => {
    if (b.status === 'ecarte') return (
      <>
        <button className="btn-sm ghost" onClick={() => restore(b.searchKey)}>Réactiver</button>
        {b.contactId && <button className="btn-sm ghost" onClick={() => onOpenContact?.(b.contactId as string)}>Fiche acq.</button>}
      </>
    )
    if (b.status === 'visite') {
      const ev = visitEvents[b.searchKey]
      return (
        <>
          {ev ? (
            <>
              {onImprimerBonVisite && <button className="btn-sm brand-soft" onClick={() => onImprimerBonVisite(ev)}>Bon de visite</button>}
              {onModifierRdv && <button className="btn-sm ghost" onClick={() => onModifierRdv(ev)}>Modifier</button>}
              {onSupprimerRdv && <button className="btn-sm ghost" onClick={() => onSupprimerRdv(ev)}>Supprimer</button>}
            </>
          ) : (
            <button className="btn-sm brand-soft" onClick={() => openVisit([b.searchKey])}><IcCal />Planifier la visite</button>
          )}
          {b.contactId && <button className="btn-sm ghost" onClick={() => onOpenContact?.(b.contactId as string)}>Fiche acq.</button>}
        </>
      )
    }
    if (b.status === 'propose') return (
      <>
        <button className="btn-sm brand-soft" onClick={() => { openMail([b.searchKey]); applyTemplate('coup') }}>Relancer</button>
        <button className="btn-sm ghost" onClick={() => openVisit([b.searchKey])}>Planifier visite</button>
        <button className="btn-sm ghost" onClick={() => restore(b.searchKey)}>Remettre à proposer</button>
      </>
    )
    return (
      <>
        <button className="btn-sm brand-fill" onClick={() => openChan([b.searchKey])}><IcSend />Proposer</button>
        <button className="btn-ecart" onClick={() => ecarter([b.searchKey])}>Écarter</button>
      </>
    )
  }

  const discCur = discPool[Math.min(discIdx, Math.max(0, discPool.length - 1))]
  const discHero = (b: Buyer) => b.status === 'visite' ? 'h-green' : b.status === 'propose' ? 'h-teal' : b.scoreClass === 's-green' ? 'h-green' : b.scoreClass === 's-gold' ? 'h-gold' : 'h-red'

  return (
    <div className="rapp-mandat" role="dialog" aria-modal="true" aria-label="Rapprochement mandat vers acquéreurs">
      <div className="panel">
        {/* Topbar */}
        <header className="topbar">
          <div className="tb-left">
            <button className="btn icon" aria-label="Retour" onClick={onClose}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 6-6 6 6 6" /></svg></button>
            <span className="tb-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg></span>
            <div className="crumb"><span className="ey">Rapprochement acquéreurs</span><span className="ref">{crumb} &nbsp;<b>{ref}</b></span></div>
          </div>
          <div className="tb-right">
            <button className={`btn${alerteOpen ? ' on' : ''}`} onClick={() => setAlerteOpen((v) => !v)}><IcBell />Alerte CRM</button>
            <button className="btn brand" onClick={() => { if (selKeys.length) openChan(selKeys); else toast('Sélectionnez d’abord des acquéreurs.') }}><IcSend />Envoyer le bien à…</button>
            <button className="btn-close" aria-label="Fermer" onClick={onClose}><IcClose /></button>
          </div>
        </header>

        <div className="workspace">
          {/* Rail : fiche mandat */}
          <aside className="rail">
            <div className="m-photo">
              {mandat.photo ? <img className="m-photo-img" src={mandat.photo} alt="" onError={(e) => { e.currentTarget.style.display = 'none' }} /> : (
                <div className="m-photo-lbl"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="m4 18 5-5 4 4 3-3 4 4" /></svg>Photo à venir</div>
              )}
              {mandat.statut && <span className="m-status-tag">{mandat.statut}</span>}
              <div className="m-price-block">
                <span className="m-price">{fmtEuro(mandat.prix)}</span>
                {mandat.surface != null && <span className="m-surf">{Math.round(Number(mandat.surface))} m²</span>}
              </div>
            </div>
            <div className="rail-body">
              <div className="m-head"><span className="m-ref">{ref}</span><span className="m-type">{mandat.type ?? 'Bien'}</span></div>
              <h2 className="m-title">{mandat.titre}</h2>
              {(mandat.ville || mandat.codePostal) && (
                <div className="m-addr"><IcPin />{[mandat.ville, mandat.codePostal].filter(Boolean).join(' · ')}</div>
              )}
              {specs.length > 0 && (
                <div className="m-specs">
                  {mandat.surface != null && <span className="m-spec"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 3h18v18H3zM3 9h18" /></svg>{Math.round(Number(mandat.surface))} m²</span>}
                  {mandat.type && <span className="m-spec"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 12h18M5 18v-6h14v6" /></svg>{mandat.type}</span>}
                </div>
              )}
              <div className="rdiv" />
              <span className="rlabel">Négociateur propriétaire</span>
              <div className="nego-row">
                <div className="nego-av">{negoInitials}</div>
                <div><div className="nego-nm">{mandat.negociateurNom || 'Groupe GTI'}</div><div className="nego-ag">{mandat.agence || 'Groupe GTI'}</div></div>
              </div>
              <div className="rdiv" />
              <span className="rlabel">Indicateurs</span>
              <div className="rail-kpi">
                <div className="rk"><span className="k">Acq. CRM</span><span className="v hot">{counts.all}</span><span className="s">dont {counts.todo} à contacter</span></div>
                <div className="rk"><span className="k">Score moy.</span><span className="v ok">{avgScore} %</span><span className="s">{hot85} profil(s) ≥ 85 %</span></div>
              </div>
            </div>
          </aside>

          {/* Main : liste acquéreurs */}
          <div className="main">
            <div className="results-head">
              <div className="rh-title">Acquéreurs correspondants</div>
              <div className="rh-sub">
                <span className="it"><b>{counts.all}</b> profils dans le CRM</span>
                <span className="dot" />
                <span className="it new"><b>{newCount}</b> nouveaux cette semaine</span>
                <span className="dot" />
                <span className="it">score moyen <b>{avgScore} %</b></span>
              </div>
            </div>

            <div className="filters">
              {([['all', 'Tous'], ['todo', 'À contacter'], ['encours', 'En cours'], ['ecarte', 'Écartés']] as [FilterKey, string][]).map(([key, label]) => (
                <button key={key} className={`fpill${filter === key ? ' on' : ''}`} onClick={() => setFilter(key)}>{label} <span className="c">{counts[key]}</span></button>
              ))}
              <button className={`fpill alerte-btn${alerteOpen ? ' on' : ''}`} onClick={() => setAlerteOpen((v) => !v)}><IcBell />Alerte CRM</button>
            </div>

            {alerteOpen && (
              <div className="alerte-band">
                <div className="al-ic"><IcBell /></div>
                <div><div className="al-t">Alerte CRM active</div><div className="al-s">Tout nouveau profil correspondant au-dessus du seuil est signalé au négociateur propriétaire.</div></div>
                <div className="al-grid">
                  <div className="af"><span className="k">État</span><span className="v ok">Active</span></div>
                  <div className="af"><span className="k">Seuil de score</span><span className="v">≥ 80 %</span></div>
                  <div className="af"><span className="k">Fréquence</span><span className="v">Temps réel</span></div>
                </div>
              </div>
            )}

            {selKeys.length > 0 && (
              <div className="tray">
                <div className="tray-ic"><IcSend /></div>
                <div className="tray-l"><b>{selKeys.length}</b> acquéreur(s) sélectionné(s)</div>
                <div className="tray-r">
                  <button className="btn brand" onClick={() => openChan(selKeys)}><IcSend />Proposer le bien à la sélection</button>
                  <button className="btn" onClick={clearSel}>Vider</button>
                </div>
              </div>
            )}

            <div className="sortbar">
              <span className="listcount">
                {visible.length} acquéreur{visible.length > 1 ? 's' : ''}
                {hiddenByCursor > 0 && <span className="lc-hidden"> · {hiddenByCursor} sous le seuil</span>}
                {' · classés par '}{sort === 'score' ? 'score' : sort === 'budget' ? 'budget' : 'nouveauté'}
              </span>
              <div className="mode-toggle">
                <button className={`mode-btn-list${!discMode ? ' on' : ''}`} onClick={() => setDiscMode(false)}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>Liste
                </button>
                <button className={`mode-btn-disc${discMode ? ' on' : ''}`} onClick={() => { setDiscMode(true); setDiscIdx(0) }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z" /></svg>Mode Découverte
                </button>
              </div>
              <div className="spills">
                {([['score', 'Score'], ['budget', 'Budget'], ['nouveaute', 'Nouveauté']] as [SortKey, string][]).map(([key, label]) => (
                  <button key={key} className={`spill${sort === key ? ' on' : ''}`} onClick={() => setSort(key)}>{label}</button>
                ))}
              </div>
            </div>

            <div className="score-ctrl">
              <span className="sc-lbl">Score min</span>
              <span className="sc-val">{seuil}<small>%</small></span>
              <input type="range" className="sc-range" min={0} max={95} step={5} value={seuil}
                style={{ ['--pct' as string]: `${(seuil / 95) * 100}%` }}
                onChange={(e) => setSeuil(Number(e.target.value))} aria-label="Seuil d'affichage du score" />
              <span className="sc-hint">{seuil === 0 ? 'Tous les profils' : `Profils ≥ ${seuil} %`}</span>
            </div>

            {!discMode ? (
              <div className="feed">
                {loading && <div className="feed-state">Chargement des acquéreurs correspondants…</div>}
                {loadError && <div className="feed-state err">Impossible de charger : {loadError}</div>}
                {!loading && !loadError && visible.length === 0 && (
                  <div className="feed-state">Aucun acquéreur ne correspond au seuil de {seuil} %.<br /><span style={{ fontSize: 12 }}>Abaissez le curseur pour en voir davantage.</span></div>
                )}
                <div id="ramFeed">
                  {visible.slice(0, 80).map((b) => {
                    return (
                      <article key={b.searchKey} className={`acard${b.sel ? ' sel' : ''}`} data-status={b.status}>
                        <div className="ac-thumb">
                          <span className="ac-av">{b.initials}</span>
                          <span className={`ac-status-flag ${b.status}`}>{b.statusLabel}</span>
                          <div className={`ac-score-badge ${b.scoreClass}`} tabIndex={b.crit.length ? 0 : undefined}>
                            {b.score}<small>%</small>
                            {b.crit.length > 0 && (
                              <div className="sc-bd">
                                <div className="sc-bd-h">Pourquoi {b.score} % ?</div>
                                {b.crit.map((c) => {
                                  const pct = critPct(c.v)
                                  return (
                                    <div className={`sc-bd-row${c.ok ? '' : ' no'}`} key={c.k}>
                                      <span className="bdk">{c.k}</span>
                                      {pct != null ? <span className="bdbar"><span style={{ width: `${pct}%` }} /></span> : null}
                                      <span className={`bdv${c.ok ? ' ok' : ''}`}>{c.v}</span>
                                    </div>
                                  )
                                })}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="ac-main">
                          <div className="ac-top">
                            <div>
                              <div className="ac-name-row">
                                {b.contactId ? (
                                  <button type="button" className="ac-name-link" onClick={() => onOpenContact?.(b.contactId as string)} title="Ouvrir la fiche contact">
                                    {b.name}<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9"><path d="M14 4h6v6M20 4 10 14" /><path d="M19 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6" /></svg>
                                  </button>
                                ) : <span className="ac-name">{b.name}</span>}
                              </div>
                              <div className="ac-meta">
                                {b.ownerNom && <span className="ac-owner"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9"><circle cx="12" cy="8" r="3.5" /><path d="M5 20a7 7 0 0 1 14 0" /></svg>Négo : {b.ownerNom}</span>}
                                {b.isNew && <span className="ac-new">Nouveau</span>}
                              </div>
                            </div>
                          </div>
                          <div className="ac-contact">
                            {b.phone && <span><IcPhone />{b.phone}</span>}
                            {b.email && <span><IcMail />{b.email}</span>}
                          </div>
                          <div className="ac-brief">
                            <div className="ac-brief-h"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.2-3.2" strokeLinecap="round" /></svg>Sa recherche</div>
                            <div className="ac-brief-chips">
                              {b.briefType && <span className="ac-chip type">{b.briefType}</span>}
                              {b.briefVilles.length > 0 && <span className="ac-chip"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>{b.briefVilles[0]}{b.briefVilles.length > 1 ? ` +${b.briefVilles.length - 1}` : ''}</span>}
                              {b.briefBudget && <span className="ac-chip">{b.briefBudget}</span>}
                              {b.briefSurfaceMin && <span className="ac-chip">{b.briefSurfaceMin}</span>}
                              {b.briefPiecesMin && <span className="ac-chip">{b.briefPiecesMin}</span>}
                            </div>
                          </div>
                        </div>
                        <div className="ac-side">
                          {b.status === 'todo' && (
                            <button className="ac-pick" aria-label="Sélectionner" onClick={() => toggleSel(b.searchKey)}><IcCheck /></button>
                          )}
                          <div className="ac-date"><IcCal />{b.date}</div>
                          <div className="ac-actions">{renderActions(b)}</div>
                        </div>
                      </article>
                    )
                  })}
                </div>
                {visible.length > 80 && <div className="feed-state">+ {visible.length - 80} autres acquéreurs (affinez le seuil ou le tri).</div>}
              </div>
            ) : (
              <div className="discovery">
                <div className="disc-topbar">
                  <button className="disc-nav-btn" onClick={() => discGo(-1)} title="Précédent"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 6-6 6 6 6" /></svg></button>
                  <div className="disc-progress"><div className="disc-progress-inner" style={{ width: discPool.length ? `${((Math.min(discIdx, discPool.length - 1) + 1) / discPool.length) * 100}%` : '100%' }} /></div>
                  <span className="disc-counter-txt">{discPool.length ? Math.min(discIdx, discPool.length - 1) + 1 : 0} / {discPool.length}</span>
                  <button className="disc-nav-btn" onClick={() => discGo(1)} title="Suivant"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 6 6 6-6 6" /></svg></button>
                </div>
                <div className="disc-card-wrap">
                  <div className={`disc-card${swipe === 'left' ? ' swipe-left' : swipe === 'right' ? ' swipe-right' : ''}`}>
                    {discCur ? (() => {
                      const bs = budgetState(discCur)
                      return (
                        <>
                          <span className="disc-stamp like">PROPOSER ✓</span>
                          <span className="disc-stamp nope">ÉCARTER ✗</span>
                          <div className={`disc-card-hero ${discHero(discCur)}`}>
                            <div className="disc-hero-score">{discCur.score}<small>%</small></div>
                            <div className="disc-hero-av">{discCur.initials}</div>
                            <div className="disc-hero-overlay" />
                            <div className="disc-hero-bottom">
                              <div className="disc-hero-name">{discCur.name}</div>
                              <div className="disc-hero-meta">
                                {discCur.ownerNom && <span className="tagw">{discCur.ownerNom}</span>}
                                <span className="tagw">{discCur.statusLabel}</span>
                                {discCur.isNew && <span className="tagw">Nouveau</span>}
                              </div>
                            </div>
                          </div>
                          <div className="disc-body">
                            {discCur.phone && <div className="disc-crow"><IcPhone />{discCur.phone}</div>}
                            {discCur.email && <div className="disc-crow"><IcMail />{discCur.email}</div>}
                            <div className="disc-budget">
                              <span className={`disc-bic ${bs === 'ok' ? 'ok' : 'warn'}`}><IcEuro /></span>
                              <div><div style={{ fontSize: 10, fontWeight: 800, letterSpacing: '.07em', textTransform: 'uppercase', color: 'var(--faint)' }}>Budget</div><div className="disc-bval">{discCur.budgetLabel}</div></div>
                              <span className={`disc-bhint ${bs === 'ok' ? 'ok' : 'warn'}`}>{budgetHintLabel[bs]}</span>
                            </div>
                            <div className="disc-match"><MatchTags crit={discCur.crit} /></div>
                          </div>
                          <div className="disc-actions">
                            <div className="disc-act-wrap"><button className="disc-act-circle ecart" onClick={() => discAction('ecart')}><IcClose /></button><span className="disc-act-label">Écarter</span></div>
                            <div className="disc-act-wrap"><button className="disc-act-circle skip" onClick={() => discGo(1)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 6 6 6-6 6" /></svg></button><span className="disc-act-label">Passer</span></div>
                            <div className="disc-act-wrap"><button className="disc-act-circle propose" onClick={() => discAction('propose')}><IcSend /></button><span className="disc-act-label">Proposer</span></div>
                          </div>
                        </>
                      )
                    })() : (
                      <div className="disc-empty">Tous les profils ont été traités !<br /><span style={{ fontSize: 12, opacity: .7 }}>Abaissez le seuil de score pour en voir davantage.</span></div>
                    )}
                  </div>
                </div>
                <div className="disc-hint">← Écarter &nbsp;·&nbsp; Proposer → &nbsp;·&nbsp; touches clavier</div>
              </div>
            )}
          </div>

          {/* Right panel */}
          <aside className="rpanel">
            <div className="rp-sec">
              <div className="rp-hdr"><span className="rp-title">Relances à faire</span><span className="rp-badge">{relances.length}</span></div>
              {relances.length === 0 ? <div className="rp-empty">Aucune relance en attente.</div> : relances.map((r) => (
                <div className="rl-item" key={r.key} onClick={() => { const buyer = buyers.find((x) => x.searchKey === r.key); if (buyer?.contactId) onOpenContact?.(buyer.contactId) }}>
                  <div className="rl-av">{r.initials}</div>
                  <div className="rl-body"><div className="rl-name">{r.name}</div><div className="rl-sub">{r.sub}</div></div>
                </div>
              ))}
            </div>

            <div className="rp-sec">
              <div className="rp-hdr"><span className="rp-title">Historique</span></div>
              {timeline.length === 0 ? <div className="rp-empty">Aucune activité enregistrée.</div> : timeline.map((ev, i) => (
                <div className="hist-item" key={i}>
                  <div className={`hist-ic ${ev.kind}`}>
                    {ev.kind === 'email' || ev.kind === 'proposition' ? <IcMail /> : ev.kind === 'visite' ? <IcCal /> : <IcBell />}
                  </div>
                  <div className="hist-body"><div className="hist-txt">{ev.title}{ev.sub ? <> — <b>{ev.sub}</b></> : null}</div><div className="hist-date">{fmtDate(ev.event_at)}</div></div>
                </div>
              ))}
            </div>

            <div className="rp-sec">
              <div className="rp-hdr"><span className="rp-title">Alerte CRM</span><span style={{ fontSize: '9.5px', fontWeight: 800, color: 'var(--green)', background: 'var(--green-soft)', border: '1px solid var(--green-line)', padding: '2px 8px', borderRadius: 99 }}>Active</span></div>
              <div style={{ fontSize: '11.5px', color: 'var(--muted)', lineHeight: 1.5 }}>
                Seuil&nbsp;<b style={{ color: 'var(--ink)' }}>80 %</b> · Temps réel
                <br />Le négociateur propriétaire est notifié à chaque nouveau profil correspondant.
              </div>
            </div>
          </aside>
        </div>
      </div>

      {/* Channel popover */}
      {chanKeys && (() => {
        const targets = buyersByKeys(chanKeys)
        const title = targets.length === 1 ? `Proposer le bien à ${targets[0]?.name ?? ''}` : `Proposer le bien à ${targets.length} acquéreurs`
        return (
          <div className="chan-back" onClick={(e) => { if (e.target === e.currentTarget) setChanKeys(null) }}>
            <div className="chan-pop" role="dialog" aria-label="Choisir le canal">
              <div className="chan-top">
                <span className="chan-top-ic"><IcSend /></span>
                <div><div className="chan-top-t">{title}</div><div className="chan-top-s">{ref} · {mandat.titre}</div></div>
                <button className="chan-x" aria-label="Fermer" onClick={() => setChanKeys(null)}><IcClose /></button>
              </div>
              <div className="chan-body">
                <button className="chan-item" onClick={() => chooseChannel('email')}><span className="chan-ic email"><IcMail /></span><div><div className="ci-t">Email avec le bien</div><div className="ci-s">Fiche du bien + lien annonce</div></div></button>
                <button className="chan-item" onClick={() => chooseChannel('telephone')}><span className="chan-ic tel"><IcPhone /></span><div><div className="ci-t">Téléphone</div><div className="ci-s">Tracer un contact téléphonique</div></div></button>
                <button className="chan-item" onClick={() => chooseChannel('visite')}><span className="chan-ic visite"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 11.5 12 4l9 7.5" /><path d="M5 10v9a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-9" /></svg></span><div><div className="ci-t">Planifier une visite</div><div className="ci-s">Créer un RDV dans l'agenda</div></div></button>
              </div>
              <div className="chan-foot"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" /><path d="M14 3v5h5" /></svg>Toute action est tracée dans l'activité du mandat et de la fiche acquéreur.</div>
            </div>
          </div>
        )
      })()}

      {/* Email preview */}
      {mailKeys && (
        <div className="chan-back" onClick={(e) => { if (e.target === e.currentTarget) setMailKeys(null) }}>
          <div className="chan-pop mail-pop" role="dialog" aria-label="Aperçu de l'email">
            <div className="chan-top">
              <span className="chan-top-ic"><IcMail /></span>
              <div><div className="chan-top-t">Aperçu de l'email</div><div className="chan-top-s">{mailRecipients.length} destinataire{mailRecipients.length > 1 ? 's' : ''}{mailBuyers.length > mailRecipients.length ? ` · ${mailBuyers.length - mailRecipients.length} sans email` : ''}</div></div>
              <button className="chan-x" aria-label="Fermer" onClick={() => setMailKeys(null)}><IcClose /></button>
            </div>
            <div className="mail-tpl">
              <span className="mail-tpl-lbl">Modèle</span>
              {([['contact', 'Premier contact'], ['coup', 'Coup de cœur']] as [TemplateKey, string][]).map(([key, label]) => (
                <button key={key} className={`tpl${mailTpl === key ? ' on' : ''}`} onClick={() => applyTemplate(key)}>{label}</button>
              ))}
            </div>
            <div className="mail-body">
              <label className="mail-field"><span className="mail-flbl">Objet</span><input className="mail-subj" type="text" value={mailSubj} onChange={(e) => setMailSubj(e.target.value)} /></label>
              <textarea className="mail-msg" rows={5} value={mailMsg} onChange={(e) => setMailMsg(e.target.value)} />
              <div className="mb-card">
                <div className="mb-photo">{mandat.photo ? <img src={mandat.photo} alt="" onError={(e) => { e.currentTarget.style.display = 'none' }} /> : <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="m4 18 5-5 4 4 3-3 4 4" /></svg>}</div>
                <div>
                  <div className="mb-ref">{ref}{mandat.ville ? ` · ${mandat.ville}` : ''}</div>
                  <div className="mb-title">{mandat.titre}</div>
                  <div className="mb-price">{fmtEuro(mandat.prix)}</div>
                  <div className="mb-specs">{specs.join(' · ')}</div>
                </div>
              </div>
              <div className="mail-sign" style={{ fontSize: '12.5px', color: 'var(--muted)', whiteSpace: 'pre-line' }}>{mandat.negociateurNom || 'Groupe GTI'}<br />{mandat.agence || 'Groupe GTI'}</div>
            </div>
            <div className="mail-foot">
              <span className="mail-foot-n">{mailRecipients.length} envoi(s) individuel(s)</span>
              <div className="mail-foot-btns">
                <button className="btn-flat" onClick={() => setMailKeys(null)}>Annuler</button>
                <button className="btn-flat" onClick={() => {
                  const signature = `${mandat.negociateurNom || 'Groupe GTI'}\n${mandat.agence || 'Groupe GTI'}`
                  const w = window.open('', '_blank')
                  if (!w) { toast('Autorise les pop-ups pour voir l’aperçu.'); return }
                  w.document.open(); w.document.write(buildEmailHtml(mailMsg, mandat, signature)); w.document.close()
                }}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>Aperçu</button>
                <button className="btn-flat brand" onClick={requestSend} disabled={!canSendEmail} title={canSendEmail ? undefined : 'Adresse négociateur (@gti-immobilier.fr) ou email acquéreur manquant'}><IcSend />Envoyer</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirm send */}
      {confirmSend && (
        <div className="chan-back confirm-back" onClick={(e) => { if (e.target === e.currentTarget && !sending) setConfirmSend(false) }}>
          <div className="chan-pop" role="dialog" aria-label="Confirmer l'envoi">
            <div className="chan-top">
              <span className="chan-top-ic"><IcSend /></span>
              <div><div className="chan-top-t">Confirmer l'envoi</div><div className="chan-top-s">{mailRecipients.length} email(s) individuel(s) · envoi réel</div></div>
              <button className="chan-x" aria-label="Fermer" onClick={() => { if (!sending) setConfirmSend(false) }}><IcClose /></button>
            </div>
            <div className="confirm-body">
              <div className="confirm-row"><span className="confirm-k">Expéditeur</span><span className="confirm-v">{senderEmail}</span></div>
              <div className="confirm-row"><span className="confirm-k">Destinataires</span><span className="confirm-v">{mailRecipients.length === 1 ? mailRecipients[0]?.email : `${mailRecipients.length} acquéreurs`}</span></div>
              <div className="confirm-warn">Ces emails partent réellement aux acquéreurs et ne peuvent pas être annulés.</div>
            </div>
            <div className="mail-foot">
              <span className="mail-foot-n" />
              <div className="mail-foot-btns">
                <button className="btn-flat" onClick={() => setConfirmSend(false)} disabled={sending}>Annuler</button>
                <button className="btn-flat brand" onClick={confirmAndSend} disabled={sending}><IcSend />{sending ? 'Envoi…' : `Confirmer (${mailRecipients.length})`}</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="toast-wrap">{toasts.map((t) => <div className="toast" key={t.id}><IcCheck />{t.msg}</div>)}</div>
    </div>
  )
}
