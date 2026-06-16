import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { AppContact, AppContactSearch } from './types'
import {
  loadRapprochements, loadSearchStatuts, loadRelances, loadSearchTimeline, loadDossierPhotos,
  recordProposition, setBienStatut, setRelanceStatus, sendGoogleWorkspaceCrmEmail,
  loadGoogleCalendarEventLinks, loadNotificationsForSearch, markNotificationRead,
  type RapprochementRow, type StatutRow, type RelanceRow, type TimelineRow, type GoogleCalendarEventLink,
  type NotificationRow,
} from './lib/api'
import RapprochementStats from './RapprochementStats'

/**
 * Recherche Acquéreur — écran de rapprochement acquéreur / biens.
 *
 * Reproduction fidèle (React) du prototype "Recherche Acquéreur.html" issu du
 * handoff Claude Design (Groupe GTI). Composant autonome : toutes les données
 * sont fictives et tout l'état est local. À brancher sur les vraies données
 * Hektor (recherches acquéreurs / rapprochements) ultérieurement.
 *
 * Charte : fond beige #f1ece4, magenta #c2125f, serif Spectral + sans Hanken
 * Grotesk. Styles scopés dans recherche-acquereur.css sous `.rech-acq`.
 */

const TODAY = '13/06/2026'

type Status = 'todo' | 'propose' | 'visite' | 'ecarte'
type Group = 'todo' | 'encours' | 'ecarte'
type FilterKey = 'all' | 'todo' | 'encours' | 'ecarte'
type SortKey = 'score' | 'prix' | 'nouveaute' | 'surface'
type Channel = 'email' | 'telephone' | 'rdv' | 'visite' | 'virtuelle'
type SpecKey = 'surface' | 'pieces' | 'chambres'

interface Spec { icon: SpecKey; label: string }
interface Crit { k: string; ok: boolean; v: string }

interface Property {
  ref: string
  type: string
  title: string
  price: string
  priceNum: number
  surface: number
  scoreClass: 's-green' | 's-gold' | 's-red'
  score: number
  status: Status
  group: Group
  isNew?: boolean
  flag?: string
  tagCls: 'todo' | 'propose' | 'visite' | 'refuse' | 'ecarte'
  tagLabel: string
  foot?: string
  crit: Crit[]
  specs: Spec[]
  inEnvoi?: boolean
  appDossierId?: number
  hektorAnnonceId?: number | null
  ville?: string | null
  numeroMandat?: string | null
  numeroDossier?: string | null
  photo?: string | null
  pricePerM2?: string
  priceOld?: string
  priceDrop?: string
  terrain?: string
  equipements?: string[]
}

interface Relance {
  id: string
  dbId?: number
  ref: string
  icon: 'late' | 'normal' | 'fav' | 'maj'
  title: string
  sub: string
  snoozable?: boolean
}

const INITIAL_PROPERTIES: Property[] = [
  {
    ref: 'V770062329', type: 'Maison · Craponne', title: 'Maison de plain-pied, jardin clos',
    price: '219 000 €', priceNum: 219000, surface: 96, scoreClass: 's-green', score: 94,
    status: 'visite', group: 'encours', tagCls: 'visite', tagLabel: 'Visite demandée',
    foot: 'Proposé par email le 09/06 · visite demandée',
    specs: [{ icon: 'surface', label: '96 m²' }, { icon: 'pieces', label: '4 pièces' }, { icon: 'chambres', label: '3 ch.' }],
    crit: [
      { k: 'Budget', ok: true, v: '100 %' }, { k: 'Secteur', ok: true, v: '95 %' },
      { k: 'Surface', ok: true, v: '90 %' }, { k: 'Pièces', ok: true, v: '100 %' },
      { k: 'Jardin', ok: true, v: '85 %' },
    ],
  },
  {
    ref: 'V770061188', type: 'Maison · Beaune', title: 'Maison village rénovée, garage',
    price: '228 000 €', priceNum: 228000, surface: 112, scoreClass: 's-green', score: 88,
    status: 'propose', group: 'encours', tagCls: 'propose', tagLabel: 'Proposé · en attente',
    foot: 'Proposé par email le 06/06 · sans réponse',
    specs: [{ icon: 'surface', label: '112 m²' }, { icon: 'pieces', label: '5 pièces' }, { icon: 'chambres', label: '4 ch.' }],
    crit: [
      { k: 'Budget', ok: true, v: '95 %' }, { k: 'Secteur', ok: true, v: '90 %' },
      { k: 'Surface', ok: true, v: '90 %' }, { k: 'Garage', ok: true, v: '80 %' },
    ],
  },
  {
    ref: 'V770063402', type: 'Maison · Craponne', title: 'Maison de bourg avec cour',
    price: '199 000 €', priceNum: 199000, surface: 84, scoreClass: 's-gold', score: 79,
    status: 'todo', group: 'todo', isNew: true, flag: 'Baisse de prix', tagCls: 'todo', tagLabel: 'À proposer',
    specs: [{ icon: 'surface', label: '84 m²' }, { icon: 'pieces', label: '3 pièces' }, { icon: 'chambres', label: '2 ch.' }],
    crit: [
      { k: 'Budget', ok: true, v: '100 %' }, { k: 'Secteur', ok: true, v: '90 %' },
      { k: 'Surface', ok: false, v: 'Hors critère' }, { k: 'Pièces', ok: false, v: 'Hors critère' },
    ],
  },
  {
    ref: 'V770060755', type: 'Maison · Saint-Pal', title: 'Maison contemporaine, terrasse',
    price: '245 000 €', priceNum: 245000, surface: 101, scoreClass: 's-gold', score: 72,
    status: 'todo', group: 'todo', isNew: true, tagCls: 'todo', tagLabel: 'À proposer',
    specs: [{ icon: 'surface', label: '101 m²' }, { icon: 'pieces', label: '4 pièces' }, { icon: 'chambres', label: '3 ch.' }],
    crit: [
      { k: 'Budget', ok: false, v: 'Hors critère' }, { k: 'Secteur', ok: true, v: '95 %' },
      { k: 'Surface', ok: true, v: '85 %' }, { k: 'Pièces', ok: true, v: '90 %' },
    ],
  },
  {
    ref: 'V770059910', type: 'Maison · Craponne', title: 'Maison avec dépendance',
    price: '212 000 €', priceNum: 212000, surface: 118, scoreClass: 's-gold', score: 81,
    status: 'ecarte', group: 'ecarte', tagCls: 'refuse', tagLabel: 'Refusé par l’acquéreur',
    foot: 'Proposé le 28/05 · non retenu (préfère du plain-pied)',
    specs: [{ icon: 'surface', label: '118 m²' }, { icon: 'pieces', label: '5 pièces' }, { icon: 'chambres', label: '3 ch.' }],
    crit: [],
  },
  {
    ref: 'V770058221', type: 'Appartement · Craponne', title: 'Appartement T3, centre-ville',
    price: '165 000 €', priceNum: 165000, surface: 65, scoreClass: 's-red', score: 58,
    status: 'ecarte', group: 'ecarte', tagCls: 'ecarte', tagLabel: 'Écarté · négociateur',
    foot: 'Motif : type de bien (Maison) non respecté',
    specs: [{ icon: 'surface', label: '65 m²' }, { icon: 'pieces', label: '3 pièces' }, { icon: 'chambres', label: '2 ch.' }],
    crit: [],
  },
  {
    ref: 'V770057004', type: 'Maison · Craponne', title: 'Maison à rénover, grange',
    price: '149 000 €', priceNum: 149000, surface: 140, scoreClass: 's-red', score: 64,
    status: 'ecarte', group: 'ecarte', tagCls: 'ecarte', tagLabel: 'Écarté · négociateur',
    foot: 'Motif : gros travaux exclus du brief',
    specs: [{ icon: 'surface', label: '140 m²' }, { icon: 'pieces', label: '6 pièces' }, { icon: 'chambres', label: '4 ch.' }],
    crit: [],
  },
]

const INITIAL_RELANCES: Relance[] = [
  { id: 'r-V770061188', ref: 'V770061188', icon: 'late', title: 'Relancer M. MOREL', sub: 'V770061188 proposé il y a 6 j · sans réponse', snoozable: true },
  { id: 'r-search', ref: 'search', icon: 'normal', title: 'Mettre à jour la recherche', sub: 'Point client à confirmer · budget & secteur', snoozable: true },
]

const CHAN_CONFIG: Record<Channel, { status: Status; tagCls: Property['tagCls']; tagLabel: string; foot: string; lbl: string }> = {
  email: { status: 'propose', tagCls: 'propose', tagLabel: 'Proposé · email', foot: `Proposé par email le ${TODAY}`, lbl: 'email' },
  telephone: { status: 'propose', tagCls: 'propose', tagLabel: 'Proposé · téléphone', foot: `Proposé par téléphone le ${TODAY}`, lbl: 'téléphone' },
  rdv: { status: 'propose', tagCls: 'propose', tagLabel: 'Proposé · RDV agence', foot: `Rendez-vous agence proposé le ${TODAY}`, lbl: 'rendez-vous agence' },
  visite: { status: 'visite', tagCls: 'visite', tagLabel: 'Visite physique prévue', foot: `Visite physique proposée le ${TODAY}`, lbl: 'visite physique' },
  virtuelle: { status: 'visite', tagCls: 'visite', tagLabel: 'Visite virtuelle prévue', foot: `Visite virtuelle proposée le ${TODAY}`, lbl: 'visite virtuelle' },
}

const MAIL_TEMPLATES = {
  contact: {
    subj: 'Une sélection de biens pour votre projet',
    msg: "Bonjour M. MOREL,\n\nSuite à notre échange, voici une première sélection de biens correspondant à votre recherche (maison 4 pièces, secteur Craponne-sur-Arzon). Dites-moi ceux que vous souhaitez visiter, je m'occupe de l'organisation.\n\nBien à vous,",
  },
  relance: {
    subj: 'De nouveaux biens correspondent à votre recherche',
    msg: "Bonjour M. MOREL,\n\nDe nouveaux biens viennent d'arriver et correspondent à vos critères. Je vous les transmets en priorité, avant leur diffusion large. Un coup de cœur ? Je vous cale une visite cette semaine.\n\nBien à vous,",
  },
  coup: {
    subj: 'Un bien à ne pas manquer',
    msg: "Bonjour M. MOREL,\n\nJ'ai repéré un bien qui colle particulièrement à votre projet — à voir rapidement selon moi. Voici les détails, je reste à votre disposition pour une visite.\n\nBien à vous,",
  },
} as const
type TemplateKey = keyof typeof MAIL_TEMPLATES

/* ----------------------------- icônes ----------------------------- */
const IcSend = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M22 4 11 15M22 4l-7 18-4-9-9-4 20-5Z" /></svg>
const IcPhoto = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="m4 18 5-5 4 4 3-3 4 4" /></svg>
const IcDoc = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" /><path d="M14 3v5h5" /></svg>
const IcBell = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" /></svg>
const IcSync = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M4 4v6h6M20 20v-6h-6" /><path d="M4 10a8 8 0 0 1 14-3M20 14a8 8 0 0 1-14 3" /></svg>
const IcClock = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
const IcCheck = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5 10 17 19 7" /></svg>
const IcClose = () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 6l12 12M18 6 6 18" /></svg>

function SpecIcon({ k }: { k: SpecKey }) {
  if (k === 'surface') return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 3h18v18H3zM3 9h18" /></svg>
  if (k === 'pieces') return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 12h18M5 18v-6h14v6" /></svg>
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 7v10M3 13h18v4M21 13v-2a3 3 0 0 0-3-3h-7v5" /></svg>
}

/* --------- dérivation du brief depuis la recherche réelle --------- */
// Une borne valant 0 (ou vide) = non renseignée → ignorée.
const raClean = (v?: string | null) => {
  const t = (v ?? '').trim()
  if (!t) return ''
  return /^0+([.,]0+)?$/.test(t) ? '' : t
}
const raNum = (t: string) => {
  const n = Number(t.replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(n) ? n.toLocaleString('fr-FR') : t
}
const raRange = (min?: string | null, max?: string | null, suf = '') => {
  const l = raClean(min), r = raClean(max)
  if (!l && !r) return ''
  if (l && r) return `${raNum(l)} – ${raNum(r)}${suf}`
  if (l) return `≥ ${raNum(l)}${suf}`
  return `≤ ${raNum(r)}${suf}`
}
const raParse = <T,>(v: unknown, fallback: T): T => {
  if (typeof v !== 'string') return (v as T) ?? fallback
  try { return JSON.parse(v) as T } catch { return fallback }
}
const raList = (v: unknown): string[] => {
  const arr = Array.isArray(v) ? v : raParse<unknown[]>(v, [])
  return Array.isArray(arr) ? arr.map((x) => String(x).trim()).filter(Boolean) : []
}
const raTypes = (v: AppContactSearch['types_json']): string[] => {
  const obj = v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : raParse<Record<string, unknown>>(v, {})
  if (!obj || typeof obj !== 'object') return []
  return Object.entries(obj)
    .filter(([, val]) => {
      const t = String(val ?? '').trim().toLowerCase()
      return val === true || val === 1 || t === '1' || Boolean(t && t !== '0' && t !== 'false')
    })
    .map(([k, val]) => (typeof val === 'string' && val.trim() && val !== '1' ? val.trim() : k))
    .filter(Boolean)
}
const raOffreLabel = (o?: string | null) => {
  const c = (o ?? '').trim()
  if (c === '2') return 'Location'
  if (c === '8') return 'Location saisonnière'
  if (c === '10' || c === '11') return 'Immobilier professionnel'
  return 'Achat / Vente'
}
const RA_EQUIP: Record<string, string> = {
  ITEM_GARAGE_PARKING: 'Garage / parking', ITEM_TERRASSE: 'Terrasse', ITEM_BALCON: 'Balcon',
  ITEM_PISCINE: 'Piscine', ITEM_ASCENSEUR: 'Ascenseur', ITEM_CHEMINEE: 'Cheminée',
  ITEM_CAVE: 'Cave', ITEM_DOUBLE_VITRAGE: 'Double vitrage', ITEM_PLAIN_PIED: 'Plain-pied',
  ITEM_MITTOYEN: 'Mitoyen', ITEM_GRENIER_COMBLE: 'Grenier / combles', ITEM_ACCES_HANDI: 'Accès handicapé',
  ITEM_TERRAIN_CONSTRUCTIBLE: 'Terrain constructible', ITEM_TERRAIN_ARBORE: 'Terrain arboré',
  ITEM_TERRAIN_PISCINABLE: 'Terrain piscinable', ITEM_TERRAIN_VIABILISE: 'Terrain viabilisé',
}
const raInitials = (name: string) =>
  name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]?.toUpperCase() ?? '').join('') || 'AC'

const fmtDate = (iso: string): string => {
  const d = new Date(iso)
  return Number.isFinite(d.getTime()) ? d.toLocaleDateString('fr-FR') : ''
}

const htmlEsc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// Corps HTML de l'email de proposition : message + cartes biens (photo, ref, prix, specs) + signature.
function buildEmailHtml(message: string, biens: Property[], signature: string): string {
  const intro = htmlEsc(message).replace(/\n/g, '<br>')
  const cards = biens.map((b) => `
    <table role="presentation" style="width:100%;border-collapse:collapse;margin:10px 0;border:1px solid #e7ddce;border-radius:8px;overflow:hidden">
      <tr>
        ${b.photo ? `<td style="width:150px;vertical-align:top"><img src="${b.photo}" width="150" style="display:block;width:150px;height:112px;object-fit:cover" alt=""></td>` : ''}
        <td style="padding:10px 14px;vertical-align:top;font-family:Arial,Helvetica,sans-serif">
          <div style="font-size:12px;color:#8a8278">${htmlEsc(b.ref)} · ${htmlEsc(b.type)}</div>
          <div style="font-size:15px;font-weight:bold;color:#1c1815;margin:2px 0">${htmlEsc(b.title)}</div>
          <div style="font-size:15px;color:#c2125f;font-weight:bold">${htmlEsc(b.price)}</div>
          <div style="font-size:12px;color:#5a5249;margin-top:3px">${b.specs.map((s) => htmlEsc(s.label)).join(' · ')}</div>
        </td>
      </tr>
    </table>`).join('')
  return `<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#1c1815;line-height:1.5">${intro}<br><br>${cards}<br><div style="color:#5a5249;font-size:13px;white-space:pre-line">${htmlEsc(signature)}</div></div>`
}

// Map d'un rapprochement persisté (RPC) vers le modèle de carte Property de l'écran.
function rapproToProperty(r: RapprochementRow, search?: AppContactSearch | null): Property {
  const tj = search?.types_json
  const typeMap = (tj && typeof tj === 'object' && !Array.isArray(tj))
    ? (tj as Record<string, unknown>)
    : raParse<Record<string, unknown>>(tj, {})
  const typeLabel = r.type_code && typeMap?.[r.type_code]
    ? String(typeMap[r.type_code])
    : (r.type_code ? `Type ${r.type_code}` : 'Bien')
  const ref = r.numero_mandat || r.numero_dossier || (r.hektor_annonce_id ? `V${r.hektor_annonce_id}` : String(r.app_dossier_id))
  const specs: Spec[] = []
  if (r.surface != null) specs.push({ icon: 'surface', label: `${Math.round(Number(r.surface))} m²` })
  if (r.nb_pieces != null) specs.push({ icon: 'pieces', label: `${Math.round(Number(r.nb_pieces))} pièces` })
  if (r.nb_chambres != null) specs.push({ icon: 'chambres', label: `${Math.round(Number(r.nb_chambres))} ch.` })
  const scoreClass: Property['scoreClass'] = r.score >= 85 ? 's-green' : r.score >= 70 ? 's-gold' : 's-red'
  const priceNum = r.prix != null ? Number(r.prix) : 0
  const price = r.prix != null ? `${Math.round(Number(r.prix)).toLocaleString('fr-FR')} €` : '—'
  const crit: Crit[] = (r.components ?? []).map((c) => ({ k: c.k, ok: c.ok, v: c.v }))
  const surfNum = r.surface != null ? Number(r.surface) : 0
  const pricePerM2 = priceNum > 0 && surfNum > 0 ? `${Math.round(priceNum / surfNum).toLocaleString('fr-FR')} €/m²` : undefined
  const priceOldNum = r.prix_old != null ? Number(r.prix_old) : 0
  const priceOld = priceOldNum > priceNum ? `${Math.round(priceOldNum).toLocaleString('fr-FR')} €` : undefined
  const priceDrop = priceOldNum > priceNum ? `− ${Math.round(priceOldNum - priceNum).toLocaleString('fr-FR')} €` : undefined
  const terrainNum = r.surface_terrain != null ? Number(r.surface_terrain) : 0
  const terrain = terrainNum > 0 ? `Terrain ${Math.round(terrainNum).toLocaleString('fr-FR')} m²` : undefined
  const equipements = (r.equipements ?? []).filter(Boolean)
  return {
    ref,
    type: `${typeLabel}${r.ville ? ` · ${r.ville}` : ''}`,
    title: r.title || `${typeLabel}${r.ville ? ` à ${r.ville}` : ''}`,
    price, priceNum,
    surface: r.surface != null ? Math.round(Number(r.surface)) : 0,
    scoreClass, score: r.score,
    status: 'todo', group: 'todo', tagCls: 'todo', tagLabel: 'À proposer',
    crit, specs, appDossierId: r.app_dossier_id, photo: r.photo_url,
    hektorAnnonceId: r.hektor_annonce_id ?? null, ville: r.ville ?? null,
    numeroMandat: r.numero_mandat ?? null, numeroDossier: r.numero_dossier ?? null,
    pricePerM2, priceOld, priceDrop, terrain, equipements,
  }
}

// Applique le statut persisté (étape B) sur une carte (par défaut: à proposer).
function applyStatut(p: Property, st?: StatutRow): Property {
  if (!st || st.status === 'jamais_vu') return p
  if (st.status === 'ecarte') return { ...p, status: 'ecarte', group: 'ecarte', tagCls: 'ecarte', tagLabel: 'Écarté · négociateur', foot: st.reason ? `Écarté · ${st.reason}` : 'Écarté par le négociateur' }
  if (st.status === 'visite') return { ...p, status: 'visite', group: 'encours', tagCls: 'visite', tagLabel: 'Visite prévue', foot: st.channel ? `Visite proposée · ${st.channel}` : 'Visite prévue' }
  const lbl = st.channel || 'contact'
  return { ...p, status: 'propose', group: 'encours', tagCls: 'propose', tagLabel: `Proposé · ${lbl}`, foot: `Proposé par ${lbl}` }
}

// Map d'une relance persistée vers le modèle d'affichage.
function relToRelance(r: RelanceRow): Relance {
  const late = r.due_date ? new Date(r.due_date).getTime() < Date.now() : false
  return {
    id: `db-${r.id}`, dbId: r.id,
    ref: r.app_dossier_id != null ? String(r.app_dossier_id) : 'search',
    icon: late ? 'late' : 'normal',
    title: r.label || 'Relance', sub: r.sub || '', snoozable: true,
  }
}

export interface VisitePlanInput {
  appDossierId: number
  hektorAnnonceId: number | null
  titre: string
  ville: string | null
  numeroMandat: string | null
  numeroDossier: string | null
  photo: string | null
  acquereurEmail: string | null
  acquereurContactId: string | null
  acquereurName: string
  contactSearchKey: string | null
  // Optionnel : permet à l'écran Rapprochement Mandat d'imposer l'agenda et l'identité
  // du négociateur propriétaire du bien (sinon résolu depuis le contact sélectionné dans App).
  calendarEmail?: string | null
  negoCommercialNom?: string | null
  negoAgenceNom?: string | null
}

export interface RechercheAcquereurProps {
  open: boolean
  onClose: () => void
  contact?: AppContact | null
  search?: AppContactSearch | null
  senderEmail?: string | null
  acquereurEmail?: string | null
  onOpenAnnonce?: (appDossierId: number) => void
  onPlanifierVisite?: (input: VisitePlanInput) => void
  visitRefreshKey?: number
  onImprimerBonVisite?: (event: GoogleCalendarEventLink) => void
  onModifierRdv?: (event: GoogleCalendarEventLink) => void
  onSupprimerRdv?: (event: GoogleCalendarEventLink) => void
  onAffinerRecherche?: () => void
}

const GTI_DOMAIN = 'gti-immobilier.fr'

export default function RechercheAcquereur({ open, onClose, contact, search, senderEmail, acquereurEmail, onOpenAnnonce, onPlanifierVisite, visitRefreshKey, onImprimerBonVisite, onModifierRdv, onSupprimerRdv, onAffinerRecherche }: RechercheAcquereurProps) {
  const [properties, setProperties] = useState<Property[]>(INITIAL_PROPERTIES)
  const [relances, setRelances] = useState<Relance[]>(INITIAL_RELANCES)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [sort, setSort] = useState<SortKey>('score')
  const [seuilAffichage, setSeuilAffichage] = useState(75)
  const [alerteOpen, setAlerteOpen] = useState(false)
  const [moreOpen, setMoreOpen] = useState(false)
  const [relExpanded, setRelExpanded] = useState(false)
  const [flashing, setFlashing] = useState<Set<string>>(new Set())
  const [toasts, setToasts] = useState<{ id: number; msg: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [statsOpen, setStatsOpen] = useState(false)
  const [timeline, setTimeline] = useState<TimelineRow[]>([])
  const [notifs, setNotifs] = useState<NotificationRow[]>([])
  const [reloadKey, setReloadKey] = useState(0)
  const [visitEvents, setVisitEvents] = useState<Record<number, GoogleCalendarEventLink>>({})
  const [prPhotos, setPrPhotos] = useState<string[]>([])
  const [confirmSend, setConfirmSend] = useState(false)
  const [sending, setSending] = useState(false)

  // sélecteur de canal : refs en attente d'un choix de canal
  const [chanRefs, setChanRefs] = useState<string[] | null>(null)
  // aperçu email : refs joints
  const [mailRefs, setMailRefs] = useState<string[] | null>(null)
  const [mailTpl, setMailTpl] = useState<TemplateKey>('contact')
  const [mailSubj, setMailSubj] = useState<string>(MAIL_TEMPLATES.contact.subj)
  const [mailMsg, setMailMsg] = useState<string>(MAIL_TEMPLATES.contact.msg)
  // présentation client
  const [presenterOpen, setPresenterOpen] = useState(false)
  const [prIdx, setPrIdx] = useState(0)
  const [prPhoto, setPrPhoto] = useState(0)

  const railRef = useRef<HTMLDivElement>(null)
  const toastId = useRef(0)

  const toast = useCallback((msg: string) => {
    const id = ++toastId.current
    setToasts((t) => [...t, { id, msg }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2600)
  }, [])

  const flash = useCallback((refs: string[]) => {
    setFlashing((prev) => {
      const next = new Set(prev)
      refs.forEach((r) => next.add(r))
      return next
    })
    setTimeout(() => {
      setFlashing((prev) => {
        const next = new Set(prev)
        refs.forEach((r) => next.delete(r))
        return next
      })
    }, 1100)
  }, [])

  // Chargement des rapprochements persistés (scoring SQL) + statuts + relances. Fallback mock si aucune recherche.
  const searchKey = search?.contact_search_key
  const negoEmail = contact?.negociateur_email ?? null
  const mailName = contact?.display_name?.trim() || 'Madame, Monsieur'

  useEffect(() => {
    if (!open) return
    if (!searchKey) { setProperties(INITIAL_PROPERTIES); setRelances(INITIAL_RELANCES); setTimeline([]); setNotifs([]); setLoadError(null); setLoading(false); return }
    let cancelled = false
    setLoading(true); setLoadError(null)
    Promise.all([loadRapprochements(searchKey), loadSearchStatuts(searchKey), loadRelances(searchKey), loadSearchTimeline(searchKey), loadNotificationsForSearch(searchKey)])
      .then(([rows, sts, rels, tl, nts]: [RapprochementRow[], StatutRow[], RelanceRow[], TimelineRow[], NotificationRow[]]) => {
        if (cancelled) return
        const stMap = new Map(sts.map((s) => [s.app_dossier_id, s]))
        setProperties(rows.map((r) => applyStatut(rapproToProperty(r, search), stMap.get(r.app_dossier_id))))
        setRelances(rels.map(relToRelance))
        setTimeline(tl)
        setNotifs(nts)
      })
      .catch((e) => { if (!cancelled) { setLoadError(e?.message ?? 'Erreur de chargement'); setProperties([]); setRelances([]); setTimeline([]); setNotifs([]) } })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, searchKey, visitRefreshKey, reloadKey])

  // RDV Google "visite" du contact, indexés par bien (pour les boutons Bon de visite / Modifier / Supprimer)
  useEffect(() => {
    const cid = contact?.hektor_contact_id
    if (!open || !cid) { setVisitEvents({}); return }
    let cancelled = false
    loadGoogleCalendarEventLinks({ hektorContactId: cid, limit: 100 })
      .then((events) => {
        if (cancelled) return
        const map: Record<number, GoogleCalendarEventLink> = {}
        for (const e of events) {
          if (e.event_type !== 'visite') continue
          if (e.status && e.status !== 'active') continue
          if (e.app_dossier_id == null) continue
          const prev = map[e.app_dossier_id]
          if (!prev || (e.starts_at || '') > (prev.starts_at || '')) map[e.app_dossier_id] = e
        }
        setVisitEvents(map)
      })
      .catch(() => { if (!cancelled) setVisitEvents({}) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, contact?.hektor_contact_id, searchKey, visitRefreshKey])

  const reloadRelances = useCallback(() => {
    if (!searchKey) return
    loadRelances(searchKey).then((rels) => setRelances(rels.map(relToRelance))).catch(() => {})
  }, [searchKey])

  /* --------------------------- dérivés --------------------------- */
  const counts = useMemo(() => ({
    all: properties.length,
    todo: properties.filter((p) => p.group === 'todo').length,
    encours: properties.filter((p) => p.group === 'encours').length,
    ecarte: properties.filter((p) => p.group === 'ecarte').length,
  }), [properties])

  const newCount = useMemo(() => properties.filter((p) => p.isNew).length, [properties])
  const avgScore = useMemo(() => Math.round(properties.reduce((s, p) => s + p.score, 0) / Math.max(1, properties.length)), [properties])

  const sortedProperties = useMemo(() => {
    if (sort === 'score') return properties // ordre d'auteur = score décroissant pertinent
    const arr = [...properties]
    if (sort === 'prix') arr.sort((a, b) => a.priceNum - b.priceNum)
    else if (sort === 'surface') arr.sort((a, b) => b.surface - a.surface)
    else if (sort === 'nouveaute') arr.sort((a, b) => Number(!!b.isNew) - Number(!!a.isNew) || b.score - a.score)
    return arr
  }, [properties, sort])

  const visibleProperties = useMemo(
    () => sortedProperties.filter((p) =>
      (filter === 'all' || p.group === filter) &&
      // le curseur ne masque que les biens encore "à proposer" ; les biens
      // déjà engagés (en cours) ou écartés restent toujours visibles
      (p.group !== 'todo' || p.score >= seuilAffichage)),
    [sortedProperties, filter, seuilAffichage],
  )

  const hiddenByCursor = useMemo(
    () => sortedProperties.filter((p) =>
      (filter === 'all' || p.group === filter) && p.group === 'todo' && p.score < seuilAffichage).length,
    [sortedProperties, filter, seuilAffichage],
  )

  const trayRefs = useMemo(() => properties.filter((p) => p.inEnvoi).map((p) => p.ref), [properties])
  const presenterBiens = useMemo(() => sortedProperties.filter((p) => p.status !== 'ecarte'), [sortedProperties])

  // photos du bien affiché dans le présentateur (chargées à la navigation)
  const prDossierId = presenterBiens[Math.min(prIdx, Math.max(0, presenterBiens.length - 1))]?.appDossierId
  useEffect(() => {
    if (!presenterOpen || prDossierId == null) { setPrPhotos([]); return }
    let cancelled = false
    loadDossierPhotos(prDossierId).then((ph) => { if (!cancelled) setPrPhotos(ph) }).catch(() => { if (!cancelled) setPrPhotos([]) })
    return () => { cancelled = true }
  }, [presenterOpen, prDossierId])

  const sortLabel = sort === 'score' ? 'classés par correspondance'
    : sort === 'prix' ? 'classés par prix' : sort === 'surface' ? 'classés par surface' : 'nouveautés en tête'

  /* --------------------------- actions --------------------------- */
  const addRelance = useCallback((ref: string) => {
    setRelances((list) => {
      if (list.some((r) => r.id === `r-${ref}`)) return list
      return [{ id: `r-${ref}`, ref, icon: 'normal', title: 'Relancer M. MOREL', sub: `${ref} proposé le ${TODAY} · relance dans 5 j`, snoozable: true }, ...list]
    })
  }, [])

  const dossierIdsForRefs = useCallback((refs: string[]) =>
    properties.filter((p) => refs.includes(p.ref)).map((p) => p.appDossierId).filter((x): x is number => x != null),
    [properties])

  const propose = useCallback((refs: string[], chan: Channel, gmail?: { messageId?: string | null; threadId?: string | null }) => {
    const c = CHAN_CONFIG[chan]
    setProperties((list) => list.map((p) => refs.includes(p.ref)
      ? { ...p, status: c.status, group: 'encours', tagCls: c.tagCls, tagLabel: c.tagLabel, foot: c.foot, inEnvoi: false }
      : p))
    flash(refs)
    if (searchKey) {
      Promise.all(dossierIdsForRefs(refs).map((id) => recordProposition(searchKey, id, chan, null, negoEmail, gmail?.messageId ?? null, gmail?.threadId ?? null)))
        .then(reloadRelances)
        .catch((e) => toast(`Erreur d'enregistrement : ${e?.message ?? ''}`))
    } else {
      refs.forEach(addRelance)
    }
    toast(`${refs.length} bien(s) proposé(s) par ${c.lbl}.`)
  }, [searchKey, negoEmail, dossierIdsForRefs, reloadRelances, addRelance, flash, toast])

  const ecarter = useCallback((refs: string[]) => {
    setProperties((list) => list.map((p) => refs.includes(p.ref)
      ? { ...p, status: 'ecarte', group: 'ecarte', tagCls: 'ecarte', tagLabel: 'Écarté · négociateur', foot: `Écarté par le négociateur le ${TODAY} · hors sélection.`, inEnvoi: false }
      : p))
    if (searchKey) {
      Promise.all(dossierIdsForRefs(refs).map((id) => setBienStatut(searchKey, id, 'ecarte', null, negoEmail)))
        .catch((e) => toast(`Erreur : ${e?.message ?? ''}`))
    }
    toast(`${refs.length} bien(s) écarté(s).`)
  }, [searchKey, negoEmail, dossierIdsForRefs, toast])

  const restore = useCallback((ref: string) => {
    setProperties((list) => list.map((p) => p.ref === ref
      ? { ...p, status: 'todo', group: 'todo', tagCls: 'todo', tagLabel: 'À proposer', foot: undefined, inEnvoi: false }
      : p))
    flash([ref])
    if (searchKey) {
      const id = properties.find((p) => p.ref === ref)?.appDossierId
      if (id != null) setBienStatut(searchKey, id, 'jamais_vu', null, negoEmail).catch(() => {})
    }
    toast('Bien rétabli dans « À proposer ».')
  }, [searchKey, negoEmail, properties, flash, toast])

  const toggleBook = useCallback((ref: string) => {
    setProperties((list) => list.map((p) => p.ref === ref ? { ...p, inEnvoi: !p.inEnvoi } : p))
  }, [])

  const clearTray = useCallback(() => {
    setProperties((list) => list.map((p) => p.inEnvoi ? { ...p, inEnvoi: false } : p))
  }, [])

  const openChan = useCallback((refs: string[]) => {
    if (!refs.length) return
    setChanRefs(refs)
  }, [])

  const openMail = useCallback((refs: string[]) => {
    setMailRefs(refs)
    setMailTpl('contact')
    setMailSubj(MAIL_TEMPLATES.contact.subj)
    setMailMsg(MAIL_TEMPLATES.contact.msg.replace(/M\. MOREL/g, mailName))
  }, [mailName])

  const chooseChannel = useCallback((chan: Channel) => {
    const refs = chanRefs ?? []
    setChanRefs(null)
    if (chan === 'email') openMail(refs)
    else propose(refs, chan)
  }, [chanRefs, openMail, propose])

  // planification de visite : délègue à App (vrai RDV Google Agenda pré-rempli)
  const openVisit = useCallback((refs: string[]) => {
    if (!refs.length) return
    setChanRefs(null)
    const p = properties.find((x) => refs.includes(x.ref) && x.appDossierId != null)
    if (!p || p.appDossierId == null) { toast('Bien introuvable pour la visite.'); return }
    if (!onPlanifierVisite) { toast('Planification de visite indisponible ici.'); return }
    onPlanifierVisite({
      appDossierId: p.appDossierId,
      hektorAnnonceId: p.hektorAnnonceId ?? null,
      titre: p.title,
      ville: p.ville ?? null,
      numeroMandat: p.numeroMandat ?? null,
      numeroDossier: p.numeroDossier ?? null,
      photo: p.photo ?? null,
      acquereurEmail: acquereurEmail ?? null,
      acquereurContactId: contact?.hektor_contact_id ?? null,
      acquereurName: contact?.display_name?.trim() || 'Acquéreur',
      contactSearchKey: searchKey || null,
    })
  }, [properties, onPlanifierVisite, acquereurEmail, contact, searchKey, toast])

  const applyTemplate = useCallback((t: TemplateKey) => {
    setMailTpl(t)
    setMailSubj(MAIL_TEMPLATES[t].subj)
    setMailMsg(MAIL_TEMPLATES[t].msg.replace(/M\. MOREL/g, mailName))
  }, [mailName])

  const senderValid = Boolean(senderEmail && senderEmail.toLowerCase().endsWith(`@${GTI_DOMAIN}`))
  const canSendEmail = senderValid && Boolean(acquereurEmail)

  // Étape 1 : demander confirmation (jamais d'envoi direct)
  const requestSend = useCallback(() => {
    if (!acquereurEmail) { toast("Aucune adresse email pour cet acquéreur — envoi impossible."); return }
    if (!senderValid) { toast("Adresse Gmail négociateur invalide (@gti-immobilier.fr requise)."); return }
    setConfirmSend(true)
  }, [acquereurEmail, senderValid, toast])

  // Étape 2 : envoi réel Gmail après confirmation ; proposition tracée UNIQUEMENT si succès
  const confirmAndSend = useCallback(async () => {
    const refs = mailRefs ?? []
    if (sending || !acquereurEmail || !senderEmail) return
    setSending(true)
    try {
      const biens = refs.map((r) => properties.find((p) => p.ref === r)).filter(Boolean) as Property[]
      const signature = `${contact?.commercial_nom || 'Groupe GTI'}\n${contact?.agence_nom || 'Groupe GTI'}`
      const res = await sendGoogleWorkspaceCrmEmail({
        subjectEmail: senderEmail,
        to: [acquereurEmail],
        subject: mailSubj,
        bodyText: mailMsg,
        bodyHtml: buildEmailHtml(mailMsg, biens, signature),
        fromName: contact?.commercial_nom ? `${contact.commercial_nom} - GTI Immobilier` : 'GTI Immobilier',
        replyTo: senderEmail,
        relatedEntityType: 'contact',
        relatedEntityId: contact?.hektor_contact_id ?? null,
      })
      if (!res?.ok) throw new Error('Envoi refusé par le serveur')
      setConfirmSend(false)
      setMailRefs(null)
      propose(refs, 'email', { messageId: res?.messageId ?? null, threadId: res?.threadId ?? null }) // succès uniquement → trace proposition + relance J+5
      toast(`Email envoyé à ${acquereurEmail}.`)
    } catch (e) {
      toast(`Échec de l'envoi : ${(e as Error)?.message ?? 'erreur'} — aucun bien marqué proposé.`)
    } finally {
      setSending(false)
    }
  }, [mailRefs, sending, acquereurEmail, senderEmail, properties, mailSubj, mailMsg, contact, propose, toast])

  const doneRelance = useCallback((id: string) => {
    const rel = relances.find((r) => r.id === id)
    setRelances((list) => list.filter((r) => r.id !== id))
    if (rel?.dbId) setRelanceStatus(rel.dbId, 'fait').catch(() => {})
    toast('Relance marquée comme faite.')
  }, [relances, toast])

  const snoozeRelance = useCallback((id: string) => {
    const rel = relances.find((r) => r.id === id)
    if (rel?.dbId) setRelanceStatus(rel.dbId, 'reporte').then(reloadRelances).catch(() => {})
    toast('Relance reportée de 3 jours.')
  }, [relances, reloadRelances, toast])

  const cardAction = useCallback((p: Property, act: string) => {
    if (act === 'book') toggleBook(p.ref)
    else if (act === 'propose') openChan([p.ref])
    else if (act === 'visite') openVisit([p.ref])
    else if (act === 'ecarter') ecarter([p.ref])
    else if (act === 'restore') restore(p.ref)
    else if (act === 'relance') { openMail([p.ref]); applyTemplate('relance') }
    else if (act === 'annonce') {
      if (onOpenAnnonce && p.appDossierId != null) onOpenAnnonce(p.appDossierId)
      else toast('Ouverture de l’annonce…')
    }
  }, [toggleBook, openChan, openVisit, ecarter, restore, openMail, applyTemplate, toast, onOpenAnnonce])

  const focusBrief = useCallback(() => {
    railRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  /* --------------------------- présentation --------------------------- */
  const openPresenter = useCallback(() => {
    if (!presenterBiens.length) return
    setPrIdx(0); setPrPhoto(0); setPresenterOpen(true)
  }, [presenterBiens.length])

  const prGo = useCallback((d: number) => {
    setPrPhoto(0)
    setPrIdx((i) => {
      const n = presenterBiens.length
      if (!n) return 0
      return (i + d + n) % n
    })
  }, [presenterBiens.length])

  // clamp / fermeture quand la liste de présentation rétrécit (écarter)
  useEffect(() => {
    if (!presenterOpen) return
    if (!presenterBiens.length) { setPresenterOpen(false); return }
    if (prIdx >= presenterBiens.length) setPrIdx(presenterBiens.length - 1)
  }, [presenterBiens.length, presenterOpen, prIdx])

  // raccourcis clavier
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (presenterOpen) {
        if (e.key === 'Escape') setPresenterOpen(false)
        else if (e.key === 'ArrowLeft') prGo(-1)
        else if (e.key === 'ArrowRight') prGo(1)
        return
      }
      if (e.key === 'Escape') {
        if (statsOpen) return // l'overlay stats gère sa propre fermeture
        if (confirmSend) { if (!sending) setConfirmSend(false); return }
        if (mailRefs) setMailRefs(null)
        else if (chanRefs) setChanRefs(null)
        else if (moreOpen) setMoreOpen(false)
        else onClose()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, presenterOpen, mailRefs, chanRefs, moreOpen, statsOpen, confirmSend, sending, prGo, onClose])

  if (!open) return null

  const prCurrent = presenterBiens[Math.min(prIdx, Math.max(0, presenterBiens.length - 1))]
  const verdict = (s: number): ['ok' | 'mid', string] => s >= 85 ? ['ok', 'Excellente correspondance'] : s >= 70 ? ['ok', 'Bonne correspondance'] : ['mid', 'Correspondance partielle']

  /* ---------- identité & brief dérivés des données réelles ---------- */
  const acqName = contact?.display_name?.trim() || 'Acquéreur'
  const acqEmail = contact?.email?.trim() || ''
  const acqPhone = contact?.phone_primary?.trim() || ''
  const acqInitials = raInitials(acqName)
  const negoName = contact?.commercial_nom?.trim() || ''
  const agenceName = contact?.agence_nom?.trim() || 'Groupe GTI'
  const negoInitials = negoName ? raInitials(negoName) : 'GTI'

  const types = search ? raTypes(search.types_json) : []
  const cities = search ? raList(search.villes_json) : []
  const prixRange = search ? raRange(search.prix_min, search.prix_max, ' €') : ''
  const surfRange = search ? raRange(search.surface_min, search.surface_max, ' m²') : ''
  const terrainRange = search ? raRange(search.surface_terrain_min, search.surface_terrain_max, ' m²') : ''
  const piecesRange = search ? raRange(search.pieces_min, search.pieces_max) : ''
  const chambreRange = search ? raRange(search.chambre_min, search.chambre_max) : ''
  const criteres = search ? raParse<Array<Record<string, unknown>>>(search.criteres_json, []) : []
  const equipements = (Array.isArray(criteres) ? criteres : [])
    .filter((c) => { const v = String(c?.valeur ?? '').trim().toUpperCase(); return RA_EQUIP[String(c?.cle ?? '')] && (v === 'OUI' || v === '1' || v === 'TRUE') })
    .map((c) => RA_EQUIP[String(c.cle)])
  const findCrit = (cle: string) => { const m = (Array.isArray(criteres) ? criteres : []).find((c) => String(c?.cle ?? '') === cle); return m ? String(m.valeur ?? '').trim() : '' }
  const dpe = findCrit('ITEM_DPE_CONS_LETTER')
  const searchActive = contact ? (search ? search.is_active === true || search.is_active === 1 || search.is_active === '1' : false) : true
  // Alertes « nouveau bien correspondant » (notifications, perspective contact) → cloche + bloc dédié.
  const newAlertsCount = useMemo(() => notifs.filter((n) => !n.read_at).length, [notifs])
  const openNotif = useCallback((n: NotificationRow) => {
    setNotifs((list) => list.map((x) => (x.id === n.id ? { ...x, read_at: new Date().toISOString() } : x)))
    markNotificationRead(n.id).catch(() => {})
    if (onOpenAnnonce && n.app_dossier_id != null) onOpenAnnonce(n.app_dossier_id)
  }, [onOpenAnnonce])
  const typeLabel = types.join(' · ')
  const cityLabel = cities[0] || 'Toutes communes'
  const crumbRef = `${types[0] || 'Bien'}${cities.length ? ` · ${cities[0]}` : ''}`

  // Insights « À surveiller » calculés depuis le feed réel
  const prixMaxNum = Number((search?.prix_max ?? '').replace(/[^0-9.]/g, '')) || 0
  const insights: { title: string; body: string }[] = []
  if (prixMaxNum > 0) {
    const over = properties.filter((p) => p.priceNum > prixMaxNum)
    if (over.length > 0) insights.push({
      title: 'Budget bientôt atteint',
      body: `${over.length} bien${over.length > 1 ? 's' : ''} au-dessus du budget (dans la marge) — à valider avec l'acquéreur avant proposition.`,
    })
  }
  if (cities.length > 0) {
    const inSecteur = properties.filter((p) => p.crit.some((c) => c.k === 'Secteur' && c.ok)).length
    if (inSecteur < 3) insights.push({
      title: 'Secteur peu fourni',
      body: `${inSecteur === 0 ? 'Aucun bien' : `${inSecteur} bien${inSecteur > 1 ? 's' : ''}`} dans le secteur recherché. Élargir le rayon améliorerait les correspondances.`,
    })
  }

  const renderActions = (p: Property) => {
    if (p.status === 'todo') return (
      <>
        <button className="btn brand sm" onClick={() => cardAction(p, 'propose')}><IcSend />Proposer…</button>
        <button className="lc-ecart" onClick={() => cardAction(p, 'ecarter')}>Écarter</button>
      </>
    )
    if (p.status === 'propose') return (
      <>
        <button className="btn brand-soft sm" onClick={() => cardAction(p, 'relance')}>Relancer</button>
        <button className="btn ghost sm" onClick={() => cardAction(p, 'visite')}>Planifier visite</button>
        <button className="btn ghost sm" onClick={() => cardAction(p, 'restore')}>Remettre à proposer</button>
      </>
    )
    if (p.status === 'visite') {
      const ev = p.appDossierId != null ? visitEvents[p.appDossierId] : undefined
      return (
        <>
          {ev ? (
            <>
              <button className="btn brand-soft sm" onClick={() => onImprimerBonVisite?.(ev)}>Bon de visite</button>
              <button className="btn ghost sm" onClick={() => onModifierRdv?.(ev)}>Modifier</button>
              <button className="btn ghost sm" onClick={() => onSupprimerRdv?.(ev)}>Supprimer</button>
            </>
          ) : (
            <button className="btn brand-soft sm" onClick={() => cardAction(p, 'visite')}>Planifier la visite</button>
          )}
          <button className="btn ghost sm" onClick={() => cardAction(p, 'restore')}>Remettre à proposer</button>
          <button className="btn ghost sm" onClick={() => cardAction(p, 'annonce')}>Voir l’annonce</button>
        </>
      )
    }
    return (
      <>
        <button className="btn ghost sm" onClick={() => cardAction(p, 'restore')}>Rétablir</button>
        <button className="btn ghost sm" onClick={() => cardAction(p, 'annonce')}>Voir l’annonce</button>
      </>
    )
  }

  const mailBiens = (mailRefs ?? []).map((r) => properties.find((p) => p.ref === r)).filter(Boolean) as Property[]

  return (
    <div className="rech-acq" role="dialog" aria-modal="true" aria-label="Recherche acquéreur">
      <main className="ra-panel">
        {/* topbar */}
        <header className="topbar">
          <div className="tb-left">
            <button className="btn icon" aria-label="Retour" onClick={onClose}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 6-6 6 6 6" /></svg></button>
            <span className="tb-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg></span>
            <div className="crumb"><span className="ey">Recherche acquéreur</span><span className="ref">{crumbRef}</span></div>
          </div>
          <div className="tb-right">
            <button className="btn" onClick={() => onAffinerRecherche ? onAffinerRecherche() : focusBrief()}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M3 5h18M6 12h12M10 19h4" /></svg>Affiner les critères</button>
            <button className="btn brand" onClick={() => { if (trayRefs.length) openChan(trayRefs); else toast('Sélectionnez d’abord des biens à proposer.') }}><IcSend />Envoyer une sélection</button>
            <div className={`menu-wrap${moreOpen ? ' open' : ''}`}>
              <button className="btn icon" aria-haspopup="true" aria-expanded={moreOpen} aria-label="Plus d'options" onClick={(e) => { e.stopPropagation(); setMoreOpen((v) => !v) }}>
                <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" /></svg>
              </button>
              <div className="menu-pop" hidden={!moreOpen} onClick={() => setMoreOpen(false)}>
                <button className="menu-item" onClick={() => setReloadKey((k) => k + 1)}><IcSync />Actualiser les rapprochements</button>
                <button className="menu-item" onClick={() => setStatsOpen(true)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M3 3v18h18" /><path d="M7 14l3-4 3 3 4-6" /></svg>Statistiques des rapprochements</button>
                <button className="menu-item" onClick={onClose}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="m15 6-6 6 6 6" /></svg>Revenir à la fiche acquéreur</button>
              </div>
            </div>
            <button className="btn-close" aria-label="Fermer" onClick={onClose}><IcClose /></button>
          </div>
        </header>

        <div className="workspace">
          {/* RAIL : le brief */}
          <aside className="rail">
            <div className="rail-inner" ref={railRef}>
              <div className="shero">
                <div className="shero-top">
                  <div className="shero-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M3 11.5 12 4l9 7.5" /><path d="M5 10v9a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-9" /><path d="M9.5 20v-5h5v5" /></svg></div>
                  <div className="shero-bd">
                    <div className="shero-ey">Projet d'acquisition</div>
                    <h1 className="shero-nm">{typeLabel || 'Recherche acquéreur'}</h1>
                  </div>
                </div>
                <div className="chips">
                  <span className={`chip ${searchActive ? 'green' : 'gold'}`}><span className="d" />{searchActive ? 'Recherche active' : 'Recherche archivée'}</span>
                  {cities.length > 0 && <span className="chip teal"><span className="d" />{cities.length} commune{cities.length > 1 ? 's' : ''}</span>}
                </div>
              </div>

              <div className="rblock">
                <div className="rblock-h"><span className="rlabel">Le brief · critères</span><button className="linkmini" onClick={() => onAffinerRecherche ? onAffinerRecherche() : focusBrief()}>Affiner</button></div>

                <div className="crit-must">
                  <div className="must-row">
                    <span className="crit-ic brand"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8Z" /><circle cx="7.5" cy="7.5" r="1.4" /></svg></span>
                    <div className="crit-bd"><div className="crit-k">Type d'offre</div><div className="crit-v">{raOffreLabel(search?.offre)}</div></div>
                    <span className="must-badge">Requis</span>
                  </div>
                  <div className="must-row">
                    <span className="crit-ic brand"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg></span>
                    <div className="crit-bd"><div className="crit-k">Localités</div><div className="crit-v">{cities.length ? <>{cities.slice(0, 3).join(' · ')}{cities.length > 3 ? <span className="soft"> · +{cities.length - 3}</span> : null}</> : <span className="soft">Toutes communes</span>}</div></div>
                    <span className="must-badge">Requis</span>
                  </div>
                  <div className="must-row">
                    <span className="crit-ic brand"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M18 7a7 7 0 1 0 0 10M4 10h9M4 14h7" /></svg></span>
                    <div className="crit-bd"><div className="crit-k">Prix</div><div className="crit-v">{prixRange || <span className="soft">Non renseigné</span>}</div></div>
                    <span className="must-badge">Requis</span>
                  </div>
                </div>

                {types.length > 0 && (
                  <>
                    <div className="brief-sub">Types de bien</div>
                    <div className="type-chips">
                      {types.map((t) => <span className="type-chip on" key={t}>{t}</span>)}
                    </div>
                  </>
                )}

                {(surfRange || terrainRange || piecesRange || chambreRange) && (
                  <>
                    <div className="brief-sub">Surfaces &amp; pièces</div>
                    <div className="crit-grid">
                      <div className="cg-cell"><div className="cg-k">Surface hab.</div><div className={`cg-v${surfRange ? '' : ' soft'}`}>{surfRange || 'Indifférent'}</div></div>
                      <div className="cg-cell"><div className="cg-k">Terrain</div><div className={`cg-v${terrainRange ? '' : ' soft'}`}>{terrainRange || 'Indifférent'}</div></div>
                      <div className="cg-cell"><div className="cg-k">Pièces</div><div className={`cg-v${piecesRange ? '' : ' soft'}`}>{piecesRange || 'Indifférent'}</div></div>
                      <div className="cg-cell"><div className="cg-k">Chambres</div><div className={`cg-v${chambreRange ? '' : ' soft'}`}>{chambreRange || 'Indifférent'}</div></div>
                    </div>
                  </>
                )}

                {equipements.length > 0 && (
                  <>
                    <div className="brief-sub">Équipements souhaités</div>
                    <div className="eq-chips">
                      {equipements.map((eq) => (
                        <span className="eq-chip" key={eq}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M5 12.5 10 17 19 7" /></svg>{eq}</span>
                      ))}
                    </div>
                  </>
                )}

                {dpe && (
                  <>
                    <div className="brief-sub">Énergie</div>
                    <div className="crit-grid">
                      <div className="cg-cell"><div className="cg-k">DPE</div><div className="cg-v">Classe {dpe} ou mieux</div></div>
                    </div>
                  </>
                )}
              </div>

              {negoName && (
                <div className="rblock">
                  <div className="rblock-h"><span className="rlabel">Négociateur</span></div>
                  <div className="resp">
                    <div className="avatar mb">{negoInitials}</div>
                    <div><div className="nm">{negoName}</div><div className="sb">{agenceName}</div></div>
                  </div>
                </div>
              )}
            </div>
          </aside>

          {/* MAIN : biens correspondants */}
          <div className="main">
            <div className="results-head">
              <div>
                <div className="rh-title">Biens correspondants</div>
                <div className="rh-sub">
                  <span className="it"><b>{counts.all}</b> biens dans le portefeuille</span>
                  <span className="dot" />
                  <span className="it new"><b>{newCount}</b> nouveaux cette semaine</span>
                  <span className="dot" />
                  <span className="it">score moyen <b>{avgScore} %</b></span>
                </div>
              </div>
            </div>

            <div className="filters">
              {([['all', 'Tous'], ['todo', 'À proposer'], ['encours', 'En cours'], ['ecarte', 'Écartés']] as [FilterKey, string][]).map(([key, label]) => (
                <button key={key} className={`fpill${filter === key ? ' on' : ''}`} onClick={() => setFilter(key)}>{label} <span className="c">{counts[key]}</span></button>
              ))}
              <button className={`fpill alerte-btn${alerteOpen ? ' on' : ''}`} onClick={() => setAlerteOpen((v) => !v)}><IcBell />Alertes{newAlertsCount > 0 && <span className="c alert">{newAlertsCount}</span>}</button>
            </div>

            {alerteOpen && (
              <div className="alerte-wrap">
                <div className="alerte">
                  <span className="alerte-ic"><IcBell /></span>
                  <div>
                    <div className="alerte-t">{newAlertsCount > 0 ? `${newAlertsCount} nouveau${newAlertsCount > 1 ? 'x' : ''} bien${newAlertsCount > 1 ? 's' : ''} correspondant${newAlertsCount > 1 ? 's' : ''}` : 'Aucune nouvelle alerte'}</div>
                    <div className="alerte-s">Le négociateur est notifié dès qu'un nouveau bien correspond à cette recherche au-dessus du seuil — détail dans « Nouveaux rapprochements ».</div>
                  </div>
                  <div className="alerte-grid">
                    <div className="af"><span className="k">État</span><span className={`v ${searchActive ? 'ok' : ''}`}>{searchActive ? 'Active' : 'Inactive'}</span></div>
                    <div className="af"><span className="k">Seuil de score</span><span className="v">≥ 80 %</span></div>
                  </div>
                </div>
              </div>
            )}

            {trayRefs.length > 0 && (
              <div className="tray">
                <div className="tray-l"><span className="tray-ic"><IcSend /></span><span><b>{trayRefs.length}</b> bien(s) prêts à proposer à {acqName}</span></div>
                <div className="tray-chips">
                  {trayRefs.map((r) => (
                    <span className="tray-chip" key={r}>{r} <button aria-label="Retirer" onClick={() => toggleBook(r)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"><path d="M6 6l12 12M18 6 6 18" /></svg></button></span>
                  ))}
                </div>
                <div className="tray-r"><button className="btn brand sm" onClick={() => openChan(trayRefs)}>Proposer par…</button><button className="btn sm" onClick={clearTray}>Vider</button></div>
              </div>
            )}

            <div className="sortbar">
              <span className="listcount">
                {visibleProperties.length} bien(s) affichés
                {hiddenByCursor > 0 && <span className="lc-hidden"> · {hiddenByCursor} sous le seuil</span>}
                {' · '}{sortLabel}
              </span>
              <label className="seuil-ctl" title="Masquer du feed les biens à proposer dont la correspondance est sous ce seuil (l'alerte reste à ≥ 80 %)">
                <span className="seuil-lbl">Afficher ≥ <b>{seuilAffichage} %</b></span>
                <input
                  type="range" min={60} max={95} step={5} value={seuilAffichage}
                  onChange={(e) => setSeuilAffichage(Number(e.target.value))}
                  className="seuil-range" aria-label="Seuil d'affichage des correspondances"
                />
              </label>
              <div className="pills">
                {([['score', 'Score'], ['prix', 'Prix'], ['nouveaute', 'Nouveauté'], ['surface', 'Surface']] as [SortKey, string][]).map(([key, label]) => (
                  <button key={key} className={`pill${sort === key ? ' on' : ''}`} onClick={() => setSort(key)}>{label}</button>
                ))}
              </div>
              <button className="present-btn" onClick={openPresenter}><svg viewBox="0 0 24 24"><path d="M7 4v16l13-8z" fill="currentColor" /></svg>Présenter au client</button>
            </div>

            <div className="feed">
              {loading && <div className="ra-feed-state">Chargement des biens correspondants…</div>}
              {loadError && <div className="ra-feed-state err">Impossible de charger les rapprochements : {loadError}</div>}
              {!loading && !loadError && visibleProperties.length === 0 && (
                <div className="ra-feed-state">Aucun bien correspondant pour cette recherche.</div>
              )}
              {visibleProperties.slice(0, 60).map((p) => (
                <article key={p.ref} className={`lcard${p.inEnvoi ? ' inenvoi' : ''}${flashing.has(p.ref) ? ' lc-flash' : ''}`} data-status={p.status}>
                  <div className="lc-accent" />
                  <div className="lc-photo">
                    {p.photo
                      ? <img className="lc-photo-img" src={p.photo} alt="" loading="lazy" onError={(e) => { e.currentTarget.style.display = 'none' }} />
                      : <span className="lc-photo-lbl"><IcPhoto />Sans photo</span>}
                    <span className={`lc-tag ${p.tagCls}`}><span className="d" />{p.tagLabel}</span>
                    {p.priceDrop && <span className="lc-drop"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M3 7l6 6 4-4 8 8M21 17v-4h-4" /></svg>{p.priceDrop}</span>}
                    {p.flag && <span className="lc-flag">{p.flag}</span>}
                    <div className={`lc-score ${p.scoreClass}`} tabIndex={p.crit.length ? 0 : undefined}>
                      <span>{p.score}</span><small>%</small>
                      {p.crit.length > 0 && (
                        <div className="lc-bd">
                          <div className="lc-bd-h">Pourquoi {p.score} % ?</div>
                          {p.crit.map((c) => (
                            <div className={`lc-bd-row${c.ok ? '' : ' no'}`} key={c.k}><span className="bdk">{c.k}</span><span className={`bdv${c.ok ? ' ok' : ''}`}>{c.v}</span></div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="lc-main">
                    <div className="lc-head">
                      <span className="lc-ref">{p.ref}</span>
                      <span className="lc-type">{p.type}</span>
                      {p.isNew && <span className="lc-new">Nouveau</span>}
                    </div>
                    <h3 className="lc-title">{p.title}</h3>
                    <div className="lc-price-row">
                      <span className="lc-price">{p.price}</span>
                      {p.pricePerM2 && <span className="lc-ppm2">· {p.pricePerM2}</span>}
                      {p.priceOld && <span className="lc-price-old">{p.priceOld}</span>}
                    </div>
                    <div className="lc-specs">
                      {p.specs.map((s, i) => <span className="lc-spec" key={i}><SpecIcon k={s.icon} />{s.label}</span>)}
                      {p.terrain && <span className="lc-spec"><SpecIcon k="surface" />{p.terrain}</span>}
                    </div>
                    {p.equipements && p.equipements.length > 0 && (
                      <div className="lc-equip"><IcCheck />{p.equipements.join(' · ')}</div>
                    )}
                    {p.foot && <div className="lc-foot"><IcDoc />{p.foot}</div>}
                    {onOpenAnnonce && p.appDossierId != null && (
                      <button className="lc-annonce" type="button" onClick={() => cardAction(p, 'annonce')}>Voir l'annonce<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M7 17 17 7M9 7h8v8" /></svg></button>
                    )}
                  </div>
                  <div className="lc-side">
                    {p.status === 'todo' && (
                      <button className="lc-pick" aria-label="Ajouter à la sélection d’envoi" onClick={() => cardAction(p, 'book')}>
                        <IcCheck />
                        <span className="sig-tip"><span className="t-add">Sélectionner</span><span className="t-on">Dans la sélection ✓</span></span>
                      </button>
                    )}
                    <div className="lc-actions">{renderActions(p)}</div>
                  </div>
                </article>
              ))}
              {visibleProperties.length > 60 && (
                <div className="ra-feed-state">+ {visibleProperties.length - 60} autres biens correspondants (affinez les critères ou le tri).</div>
              )}
            </div>
          </div>

          {/* CONTEXT : acquéreur & activité */}
          <aside className="context">
            <div className="cx cx-rel">
              <div className={`relpanel${relExpanded ? ' expanded' : ''}`}>
                <div className="relpanel-h"><span className="relpanel-ic"><IcBell /></span><span className="relpanel-t">Relances à faire</span><span className="relpanel-c">{relances.length}</span></div>
                <div className="rel-list">
                  {(relExpanded ? relances : relances.slice(0, 2)).map((r) => (
                    <div className="rel" key={r.id}>
                      <span className={`rel-ic${r.icon === 'late' ? ' late' : r.icon === 'fav' ? ' fav' : r.icon === 'maj' ? ' maj' : ''}`}>
                        {r.icon === 'fav' ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6"><path d="M5 12.5 10 17 19 7" /></svg>
                          : r.icon === 'maj' ? <IcSync />
                            : r.icon === 'normal' && r.ref === 'search' ? <IcSync /> : <IcClock />}
                      </span>
                      <div className="rel-bd"><div className="rel-t">{r.title}</div><div className="rel-s">{r.sub}</div></div>
                      <div className="rel-act">
                        <button className="rel-btn" onClick={() => doneRelance(r.id)}>Fait</button>
                        {r.snoozable && <button className="rel-btn ghost" onClick={() => snoozeRelance(r.id)}>+3 j</button>}
                      </div>
                    </div>
                  ))}
                </div>
                {relances.length > 2 && (
                  <button className="rel-more" onClick={() => setRelExpanded((v) => !v)}>
                    {relExpanded ? 'Réduire' : `Voir les ${relances.length - 2} autre${relances.length - 2 > 1 ? 's' : ''}`}
                  </button>
                )}
              </div>
            </div>

            {notifs.length > 0 && (
              <div className="cx">
                <div className="cx-h"><span className="t">Nouveaux rapprochements</span>{newAlertsCount > 0 && <span className="cx-badge">{newAlertsCount}</span>}</div>
                <div className="notif-list">
                  {notifs.map((n) => (
                    <button type="button" key={n.id} className={`notif-it${n.read_at ? '' : ' unread'}`} onClick={() => openNotif(n)} title="Ouvrir l’annonce">
                      <span className="notif-ic"><IcBell /></span>
                      <span className="notif-bd">
                        <span className="notif-t">{n.title}</span>
                        {n.body && <span className="notif-s">{n.body}</span>}
                        <span className="notif-d">{fmtDate(n.created_at)}</span>
                      </span>
                      {!n.read_at && <span className="notif-dot" aria-hidden />}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="cx">
              <div className="cx-h"><span className="t">Acquéreur rattaché</span></div>
              <div className="acq-card">
                <div className="acq-top">
                  <div className="avatar">{acqInitials}</div>
                  <div className="acq-bd">
                    <div className="acq-nm">{acqName}</div>
                    <div className="acq-meta">Acquéreur{contact?.ville ? ` · ${contact.ville}` : ''}</div>
                  </div>
                </div>
                <div className="coordmini">
                  {acqPhone && <span className="cm"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M4 5a2 2 0 0 1 2-2h2.5l1.5 4-2 1.5a12 12 0 0 0 5 5l1.5-2 4 1.5V18a2 2 0 0 1-2 2A15 15 0 0 1 4 5Z" /></svg>{acqPhone}</span>}
                  {acqEmail && <span className="cm"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></svg>{acqEmail}</span>}
                </div>
              </div>
            </div>

            <div className="cx">
              <div className="cx-h"><span className="t">Activité de la recherche</span></div>
              <div className="tl">
                {timeline.length === 0 ? (
                  <div className="empty"><span className="et">Aucune activité enregistrée pour le moment.</span></div>
                ) : timeline.map((ev, i) => (
                  <div className={`tl-it${ev.kind === 'nouveau' ? ' soft' : ''}`} key={i}>
                    <div className="tl-d">{fmtDate(ev.event_at)}</div>
                    <div className="tl-t">{ev.title}</div>
                    {ev.sub && <div className="tl-s">{ev.sub}</div>}
                  </div>
                ))}
              </div>
            </div>

            {insights.length > 0 && (
              <div className="cx">
                <div className="cx-h"><span className="t">À surveiller</span></div>
                {insights.map((ins, i) => (
                  <div className="insight" key={i}>
                    <div className="ih"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" /></svg>{ins.title}</div>
                    <div className="ib">{ins.body}</div>
                  </div>
                ))}
              </div>
            )}
          </aside>
        </div>
      </main>

      {/* choix du canal de proposition */}
      {chanRefs && (
        <div className="chan-back" onClick={(e) => { if (e.target === e.currentTarget) setChanRefs(null) }}>
          <div className="chan-pop" role="dialog" aria-label="Choisir le canal">
            <div className="chan-top">
              <span className="chan-top-ic"><IcSend /></span>
              <div className="chan-top-bd"><div className="chan-top-t">Proposer à {acqName}</div><div className="chan-top-s">{chanRefs.length > 1 ? `${chanRefs.length} biens sélectionnés` : '1 bien sélectionné'} · choisissez le canal</div></div>
              <button className="x" aria-label="Fermer" onClick={() => setChanRefs(null)}><IcClose /></button>
            </div>
            <div className="chan-body">
              <button className="chan-item" onClick={() => chooseChannel('email')}><span className="chan-ic email"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></svg></span><span><span className="ci-t">Email</span><span className="ci-s">Envoyer la sélection avec lien annonce</span></span></button>
              <button className="chan-item" onClick={() => chooseChannel('telephone')}><span className="chan-ic tel"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M4 5a2 2 0 0 1 2-2h2.5l1.5 4-2 1.5a12 12 0 0 0 5 5l1.5-2 4 1.5V18a2 2 0 0 1-2 2A15 15 0 0 1 4 5Z" /></svg></span><span><span className="ci-t">Téléphone</span><span className="ci-s">Appeler l'acquéreur pour présenter le(s) bien(s)</span></span></button>
              <button className="chan-item" onClick={() => openVisit(chanRefs ?? [])}><span className="chan-ic visite"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><circle cx="8" cy="15" r="4" /><path d="m11 12 8-8 2 2-2 2 2 2-2 2-3-3" /></svg></span><span><span className="ci-t">Visite du bien</span><span className="ci-s">Planifier une visite (sur place ou à distance)</span></span></button>
            </div>
            <div className="chan-foot"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 7.6h.01" /></svg>L'acquéreur sera notifié et une relance programmée automatiquement.</div>
          </div>
        </div>
      )}

      {/* aperçu email */}
      {mailRefs && (
        <div className="mail-back" onClick={(e) => { if (e.target === e.currentTarget) setMailRefs(null) }}>
          <div className="mail-pop" role="dialog" aria-label="Aperçu de l'email">
            <div className="mail-head">
              <span className="mail-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></svg></span>
              <div className="mail-head-bd"><div className="mail-h-t">Aperçu de l'email</div><div className="mail-h-s">À : {mailName}{acquereurEmail ? ` <${acquereurEmail}>` : ' — aucune adresse email'}</div></div>
              <button className="x" aria-label="Fermer" onClick={() => setMailRefs(null)}><IcClose /></button>
            </div>
            <div className="mail-tpl">
              <span className="mail-tpl-lbl">Modèle</span>
              {([['contact', 'Premier contact'], ['relance', 'Relance'], ['coup', 'Coup de cœur']] as [TemplateKey, string][]).map(([key, label]) => (
                <button key={key} className={`tpl${mailTpl === key ? ' on' : ''}`} onClick={() => applyTemplate(key)}>{label}</button>
              ))}
            </div>
            <div className="mail-body">
              <label className="mail-field"><span className="mail-flbl">Objet</span><input className="mail-subj" type="text" value={mailSubj} onChange={(e) => setMailSubj(e.target.value)} /></label>
              <textarea className="mail-msg" rows={5} value={mailMsg} onChange={(e) => setMailMsg(e.target.value)} />
              <div className="mail-biens">
                {mailBiens.map((b) => (
                  <div className="mb-card" key={b.ref}>
                    <div className="mb-photo">{b.photo ? <img className="mb-photo-img" src={b.photo} alt="" loading="lazy" onError={(e) => { e.currentTarget.style.display = 'none' }} /> : <IcPhoto />}</div>
                    <div className="mb-bd">
                      <div className="mb-ref">{b.ref}</div>
                      <div className="mb-title">{b.title}</div>
                      <div className="mb-price">{b.price}</div>
                      <div className="mb-specs">{b.specs.map((s) => s.label).join(' · ')}</div>
                      <a className="mb-link" onClick={() => { if (onOpenAnnonce && b.appDossierId != null) onOpenAnnonce(b.appDossierId); else toast('Ouverture de l’annonce…') }}>Voir l’annonce →</a>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mail-inter">
                <span className="mi-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M9 11l3 3 8-8" /><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9" /></svg></span>
                <div className="mi-bd">
                  <div className="mi-t">Email interactif</div>
                  <div className="mi-s">Le client répond directement : « Ça m'intéresse » / « Pas pour moi » pour chaque bien, et peut mettre à jour sa recherche. Ses réponses remontent dans votre liste.</div>
                </div>
              </div>
              <div className="mail-sign">{negoName || 'Groupe GTI'}<br />{agenceName}</div>
            </div>
            <div className="mail-foot">
              <span className="mail-foot-n">{mailBiens.length}{mailBiens.length > 1 ? ' biens joints' : ' bien joint'}</span>
              <div className="mail-foot-btns">
                <button className="btn ghost sm" onClick={() => setMailRefs(null)}>Annuler</button>
                <button className="btn ghost sm" onClick={() => {
                  const signature = `${contact?.commercial_nom || 'Groupe GTI'}\n${contact?.agence_nom || 'Groupe GTI'}`
                  const w = window.open('', '_blank')
                  if (!w) { toast('Autorise les pop-ups pour voir l’aperçu.'); return }
                  w.document.open(); w.document.write(buildEmailHtml(mailMsg, mailBiens, signature)); w.document.close()
                }} title="Aperçu de l'email tel qu'il sera reçu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" /><circle cx="12" cy="12" r="3" /></svg>Aperçu</button>
                <button className="btn brand sm" onClick={requestSend} disabled={!canSendEmail} title={canSendEmail ? undefined : 'Adresse négociateur ou acquéreur manquante'}><IcSend />Envoyer l'email</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* mode présentation client (plein écran, bien par bien) */}
      {presenterOpen && prCurrent && (() => {
        const v = verdict(prCurrent.score)
        const critRows: Crit[] = prCurrent.crit.length ? prCurrent.crit : [{ k: 'Correspond au brief', ok: true, v: '' }]
        return (
          <div className="presenter">
            <div className="pr-progress"><span style={{ width: `${((prIdx + 1) / presenterBiens.length) * 100}%` }} /></div>
            <div className="pr-bar">
              <div className="pr-bar-l"><span className="pr-bar-ic"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor" /></svg></span>Présentation à <b>{acqName}</b></div>
              <div className="pr-count">Bien <b>{prIdx + 1}</b> sur <span>{presenterBiens.length}</span></div>
              <button className="pr-close" onClick={() => setPresenterOpen(false)}><IcClose />Quitter</button>
            </div>
            <div className="pr-stage">
              <button className="pr-nav prev" aria-label="Bien précédent" onClick={() => prGo(-1)}><span className="pr-nav-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 6-6 6 6 6" /></svg></span><span className="pr-nav-lbl">Bien préc.</span></button>
              <div className="pr-card">
                <div className="pr-gallery">
                  <div className="pr-slide" style={prPhotos.length ? { backgroundImage: `url("${prPhotos[Math.min(prPhoto, prPhotos.length - 1)]}")`, backgroundSize: 'cover', backgroundPosition: 'center' } : undefined}>
                    {prPhotos.length === 0 && (
                      <>
                        <svg viewBox="0 0 24 24" fill="none" stroke="rgba(20,14,10,.38)" strokeWidth="1.3"><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="m4 18 5-5 4 4 3-3 4 4" /></svg>
                        <span className="pr-slide-lbl">Sans photo</span>
                      </>
                    )}
                  </div>
                  {prPhotos.length > 1 && <button className="pr-gnav prev" aria-label="Photo précédente" onClick={() => setPrPhoto((i) => (i - 1 + prPhotos.length) % prPhotos.length)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="m15 6-6 6 6 6" /></svg></button>}
                  {prPhotos.length > 1 && <button className="pr-gnav next" aria-label="Photo suivante" onClick={() => setPrPhoto((i) => (i + 1) % prPhotos.length)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="m9 6 6 6-6 6" /></svg></button>}
                  {prPhotos.length > 0 && <div className="pr-pcount">{Math.min(prPhoto, prPhotos.length - 1) + 1} / {prPhotos.length}</div>}
                  {prCurrent.priceDrop && <div className="pr-drop"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M3 7l6 6 4-4 8 8M21 17v-4h-4" /></svg>{prCurrent.priceDrop}</div>}
                  <div className={`pr-verdict ${v[0]}`}>{v[1]}</div>
                  {prPhotos.length > 1 && (
                    <div className="pr-thumbs">
                      {prPhotos.slice(0, 8).map((url, i) => <button key={i} className={`pr-thumb${i === prPhoto ? ' on' : ''}`} style={{ backgroundImage: `url("${url}")`, backgroundSize: 'cover', backgroundPosition: 'center' }} onClick={() => setPrPhoto(i)} />)}
                    </div>
                  )}
                </div>
                <div className="pr-info" data-n={prIdx + 1}>
                  <div className="pr-info-top">
                    <div className="pr-ref">{prCurrent.ref} · {prCurrent.type}</div>
                    <h2 className="pr-title">{prCurrent.title}</h2>
                    <div className="pr-price-row">
                      <span className="pr-price">{prCurrent.price}</span>
                      {prCurrent.pricePerM2 && <span className="pr-ppm2">· {prCurrent.pricePerM2}</span>}
                      {prCurrent.priceOld && <span className="pr-price-old">{prCurrent.priceOld}</span>}
                    </div>
                    <div className="pr-specs">{prCurrent.specs.map((s, i) => <span className="pr-spec" key={i}>{s.label}</span>)}{prCurrent.terrain && <span className="pr-spec">{prCurrent.terrain}</span>}</div>
                    {prCurrent.equipements && prCurrent.equipements.length > 0 && (
                      <div className="pr-equip"><IcCheck />{prCurrent.equipements.join(' · ')}</div>
                    )}
                    <div className="pr-crit-h">Correspondance avec votre recherche</div>
                    <div className="pr-criteria">
                      {critRows.map((c) => (
                        <div className={`pr-crit ${c.ok ? 'ok' : 'no'}`} key={c.k}>
                          <span className="pr-crit-ic">{c.ok ? <IcCheck /> : <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M6 6l12 12M18 6 6 18" /></svg>}</span>
                          <span className="pr-crit-k">{c.k}</span>
                          <span className="pr-crit-v">{c.v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="pr-actions">
                    <button className="pr-act ecart" onClick={() => ecarter([prCurrent.ref])}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 6l12 12M18 6 6 18" /></svg>Écarter</button>
                    <button className="pr-act annonce" onClick={() => { if (onOpenAnnonce && prCurrent.appDossierId != null) onOpenAnnonce(prCurrent.appDossierId); else toast('Ouverture de l’annonce…') }}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9"><path d="M14 4h6v6M20 4 10 14" /><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" /></svg>Annonce</button>
                    <button className="pr-act prop" onClick={() => openChan([prCurrent.ref])}><IcSend />Proposer…</button>
                  </div>
                </div>
              </div>
              <button className="pr-nav next" aria-label="Bien suivant" onClick={() => prGo(1)}><span className="pr-nav-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m9 6 6 6-6 6" /></svg></span><span className="pr-nav-lbl">Bien suiv.</span></button>
            </div>
            <div className="pr-dots">
              {presenterBiens.map((_, i) => <button key={i} className={`pr-dot${i === prIdx ? ' on' : ''}`} onClick={() => { setPrIdx(i); setPrPhoto(0) }} />)}
            </div>
          </div>
        )
      })()}

      {/* confirmation d'envoi réel (garde-fou anti-envoi accidentel) */}
      {confirmSend && (
        <div className="chan-back ra-confirm-back" onClick={(e) => { if (e.target === e.currentTarget && !sending) setConfirmSend(false) }}>
          <div className="chan-pop ra-confirm" role="dialog" aria-label="Confirmer l'envoi de l'email">
            <div className="chan-top">
              <span className="chan-top-ic"><IcSend /></span>
              <div className="chan-top-bd">
                <div className="chan-top-t">Confirmer l'envoi de l'email</div>
                <div className="chan-top-s">{mailRefs?.length ?? 0} bien{(mailRefs?.length ?? 0) > 1 ? 's' : ''} · envoi réel au client</div>
              </div>
              <button className="x" aria-label="Fermer" onClick={() => { if (!sending) setConfirmSend(false) }}><IcClose /></button>
            </div>
            <div className="ra-confirm-body">
              <div className="ra-confirm-row"><span className="ra-confirm-k">Destinataire</span><span className="ra-confirm-v">{acquereurEmail}</span></div>
              <div className="ra-confirm-row"><span className="ra-confirm-k">Expéditeur</span><span className="ra-confirm-v">{senderEmail}</span></div>
              <div className="ra-confirm-warn">Cet email part réellement au client et ne peut pas être annulé.</div>
            </div>
            <div className="ra-confirm-foot">
              <button className="btn sm" onClick={() => setConfirmSend(false)} disabled={sending}>Annuler</button>
              <button className="btn brand sm" onClick={confirmAndSend} disabled={sending}><IcSend />{sending ? 'Envoi…' : `Confirmer l'envoi à ${acquereurEmail}`}</button>
            </div>
          </div>
        </div>
      )}

      <RapprochementStats open={statsOpen} onClose={() => setStatsOpen(false)} />

      {/* toasts */}
      <div className="rech-acq-toasts">
        {toasts.map((t) => <div className="toast" key={t.id}>{t.msg}</div>)}
      </div>
    </div>
  )
}
