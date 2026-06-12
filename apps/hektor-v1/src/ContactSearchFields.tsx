import { useMemo, useRef, useState } from 'react'
import type { HektorContactSearchInput } from './lib/api'
import type { AppContactSearch } from './types'
import './contact-search.css'

export type Locality = { city: string; postalCode: string }

export type ContactSearchFieldsValue = {
  offerCode: string
  typeIds: string[]
  localities: Locality[]
  priceMin: number
  priceMax: number
  priceMargin: string
  surfaceMin: number
  landSurfaceMin: number
  rooms: number
  bedrooms: number
  bathrooms: number
  equipments: string[]
  dpeLetter: string
}

export type OfferOption = { value: string; label: string }

export const DEFAULT_OFFER_OPTIONS: OfferOption[] = [
  { value: '0', label: 'Achat / Vente' },
  { value: '2', label: 'Location' },
  { value: '8', label: 'Saisonnier' },
  { value: '10', label: 'Immo. Pro.' },
]

const TYPE_MAIN = [
  { id: '1', label: 'Maison' }, { id: '2', label: 'Appartement' }, { id: '4', label: 'Studio' }, { id: '18', label: 'Duplex' },
  { id: '39', label: 'Maison de village' }, { id: '25', label: 'Villa' }, { id: '5', label: 'Terrain' }, { id: '21', label: 'Immeuble' },
]
const TYPE_MORE = [
  { id: '43', label: 'Terrain à bâtir' }, { id: '44', label: 'Terrain agricole' }, { id: '45', label: 'Terrain de loisir' },
  { id: '22', label: 'Propriété' }, { id: '10', label: 'Mas' }, { id: '11', label: 'Bastide' }, { id: '30', label: 'Ferme' },
  { id: '28', label: 'Château' }, { id: '17', label: 'Chalet' }, { id: '31', label: 'Loft' }, { id: '41', label: 'Triplex' },
  { id: '27', label: 'Rez-de-villa' }, { id: '26', label: 'Rez-de-jardin' }, { id: '16', label: 'Parking' },
  { id: '15', label: 'Garage' }, { id: '29', label: 'Cave' }, { id: '24', label: 'Cabanon' }, { id: '20', label: 'Autre' },
]
const EQUIPMENTS = [
  { code: 'garage_parking', label: 'Garage / parking' }, { code: 'terrasse', label: 'Terrasse' }, { code: 'balcon', label: 'Balcon' },
  { code: 'piscine', label: 'Piscine' }, { code: 'ascenseur', label: 'Ascenseur' }, { code: 'cheminee', label: 'Cheminée' },
  { code: 'cave', label: 'Cave' }, { code: 'double_vitrage', label: 'Double vitrage' }, { code: 'plain_pied', label: 'Plain-pied' },
  { code: 'grenier_comble', label: 'Grenier / combles' }, { code: 'acces_handi', label: 'Accès handicapé' },
  { code: 'terrain_constructible', label: 'Terrain constructible' }, { code: 'terrain_arbore', label: 'Terrain arboré' },
  { code: 'terrain_piscinable', label: 'Terrain piscinable' }, { code: 'terrain_viabilise', label: 'Terrain viabilisé' },
]
const DPE_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
const NAV = [
  { target: 's-offre', label: 'Offre & type' }, { target: 's-loc', label: 'Localités & rayon' }, { target: 's-budget', label: 'Budget' },
  { target: 's-surface', label: 'Surfaces' }, { target: 's-pieces', label: 'Pièces' }, { target: 's-equip', label: 'Équipements' },
  { target: 's-alerte', label: 'Alerte & note' },
]

const TYPE_LABEL: Record<string, string> = Object.fromEntries([...TYPE_MAIN, ...TYPE_MORE].map((t) => [t.id, t.label]))

const EQUIP_ITEM_BY_CODE: Record<string, string> = {
  garage_parking: 'ITEM_GARAGE_PARKING', terrasse: 'ITEM_TERRASSE', balcon: 'ITEM_BALCON', piscine: 'ITEM_PISCINE',
  ascenseur: 'ITEM_ASCENSEUR', cheminee: 'ITEM_CHEMINEE', cave: 'ITEM_CAVE', double_vitrage: 'ITEM_DOUBLE_VITRAGE',
  plain_pied: 'ITEM_PLAIN_PIED', grenier_comble: 'ITEM_GRENIER_COMBLE', acces_handi: 'ITEM_ACCES_HANDI',
  terrain_constructible: 'ITEM_TERRAIN_CONSTRUCTIBLE', terrain_arbore: 'ITEM_TERRAIN_ARBORE',
  terrain_piscinable: 'ITEM_TERRAIN_PISCINABLE', terrain_viabilise: 'ITEM_TERRAIN_VIABILISE',
}

function fmtEur(n: number) { return new Intl.NumberFormat('fr-FR').format(n) }

// Icônes SVG inline (trait 1.7, viewBox 24) — identiques à la maquette.
const IC = {
  home: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M3 11.5 12 4l9 7.5" /><path d="M5 10v9a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-9" /></svg>,
  pin: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>,
  euro: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>,
  grid: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M3 3h18v18H3zM3 9h18M9 21V9" /></svg>,
  rooms: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M3 12h18M5 18v-6h14v6" /></svg>,
  shield: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" /></svg>,
  bell: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" /></svg>,
}

export function defaultContactSearchValue(seed?: Partial<ContactSearchFieldsValue>): ContactSearchFieldsValue {
  return {
    offerCode: '0', typeIds: ['1'], localities: [], priceMin: 120000, priceMax: 250000, priceMargin: '',
    surfaceMin: 0, landSurfaceMin: 0, rooms: 0, bedrooms: 0, bathrooms: 0, equipments: [], dpeLetter: '',
    ...seed,
  }
}

export function contactSearchValueToInput(value: ContactSearchFieldsValue): HektorContactSearchInput {
  return {
    kind: 'search_criteria', enabled: true,
    offerCode: value.offerCode,
    propertyTypeIds: value.typeIds,
    localities: value.localities.map((l) => ({ city: l.city, postalCode: l.postalCode })),
    priceMin: String(value.priceMin),
    priceMax: String(value.priceMax),
    priceMargin: value.priceMargin || undefined,
    surfaceMin: value.surfaceMin ? String(value.surfaceMin) : undefined,
    landSurfaceMin: value.landSurfaceMin ? String(value.landSurfaceMin) : undefined,
    roomsMin: value.rooms ? String(value.rooms) : undefined,
    bedroomsMin: value.bedrooms ? String(value.bedrooms) : undefined,
    bathroomsMin: value.bathrooms ? String(value.bathrooms) : undefined,
    dpeLetter: value.dpeLetter || undefined,
    equipments: value.equipments,
  }
}

function parseJsonSafe(value: unknown): any {
  if (value == null) return null
  if (typeof value === 'object') return value
  try { return JSON.parse(String(value)) } catch { return null }
}
function critereMap(raw: unknown): Record<string, string> {
  const parsed = parseJsonSafe(raw)
  const out: Record<string, string> = {}
  const items = Array.isArray(parsed) ? parsed : (parsed && typeof parsed === 'object' ? Object.values(parsed) : [])
  for (const it of items) {
    if (it && typeof it === 'object' && 'cle' in it) {
      const k = String((it as any).cle || ''); const v = (it as any).valeur
      if (k) out[k] = v == null ? '' : String(v)
    }
  }
  return out
}
function num(value: unknown, fallback: number): number {
  const n = Number(String(value ?? '').replace(/[^0-9.]/g, ''))
  return Number.isFinite(n) && n > 0 ? n : fallback
}

export function contactSearchValueFromSearch(src: AppContactSearch): ContactSearchFieldsValue {
  const crit = critereMap(src.criteres_json)
  const villes = parseJsonSafe(src.villes_json)
  const localities: Locality[] = (Array.isArray(villes) ? villes : []).map((entry) => {
    const s = String(entry || ''); const m = s.match(/(\d{4,5})/)
    return { city: s.replace(/\d{4,5}/, '').replace(/[·,]/g, '').trim(), postalCode: m ? m[1] : '' }
  }).filter((l) => l.city || l.postalCode)
  const typesParsed = parseJsonSafe(src.types_json)
  const typeIds = Array.isArray(typesParsed) ? typesParsed.map((v) => String(v)) : (typesParsed && typeof typesParsed === 'object' ? Object.keys(typesParsed) : [])
  const equipments: string[] = []
  for (const [code, item] of Object.entries(EQUIP_ITEM_BY_CODE)) {
    if (/^(1|oui|true)$/i.test(String(crit[item] || ''))) equipments.push(code)
  }
  return {
    offerCode: src.offre ? String(src.offre) : '0',
    typeIds: typeIds.length ? typeIds : ['1'],
    localities,
    priceMin: num(src.prix_min, 120000),
    priceMax: num(src.prix_max, 250000),
    priceMargin: crit.ITEM_PRIX_MARGE || '',
    surfaceMin: num(src.surface_min, 0),
    landSurfaceMin: num(src.surface_terrain_min, 0),
    rooms: num(src.pieces_min, 0),
    bedrooms: num(src.chambre_min, 0),
    bathrooms: num(crit.ITEM_SDB_SDE_MIN, 0),
    equipments,
    dpeLetter: crit.ITEM_DPE_CONS_LETTER || '',
  }
}

export type ContactSearchFieldsProps = {
  value: ContactSearchFieldsValue
  onChange: (next: ContactSearchFieldsValue) => void
  offerOptions?: OfferOption[]
  showNav?: boolean
  showPreview?: boolean
  disabled?: boolean
  scrollRef?: React.RefObject<HTMLDivElement | null>
}

export default function ContactSearchFields(props: ContactSearchFieldsProps) {
  const { value, onChange } = props
  const offerOptions = props.offerOptions ?? DEFAULT_OFFER_OPTIONS
  const showNav = props.showNav !== false
  const showPreview = props.showPreview !== false
  const disabled = !!props.disabled
  const internalScroll = useRef<HTMLDivElement | null>(null)
  const scrollRef = props.scrollRef ?? internalScroll
  const [activeNav, setActiveNav] = useState('s-offre')
  const [showMoreTypes, setShowMoreTypes] = useState(false)
  const [locInput, setLocInput] = useState('')
  // Champs visuels (alignés sur la maquette) — non envoyés au worker.
  const [rayon, setRayon] = useState(15)
  const [financement, setFinancement] = useState('valide')
  const [alerteOn, setAlerteOn] = useState(true)
  const [alerteFreq, setAlerteFreq] = useState('quotidienne')
  const [seuil, setSeuil] = useState(75)

  const set = (patch: Partial<ContactSearchFieldsValue>) => onChange({ ...value, ...patch })
  const toggleIn = (list: string[], v: string) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v])

  const addLocality = () => {
    const raw = locInput.trim()
    if (!raw) return
    const m = raw.match(/(\d{4,5})/)
    const postalCode = m ? m[1] : ''
    const city = raw.replace(/\d{4,5}/, '').replace(/[·,]/g, '').trim()
    if (!city && !postalCode) return
    set({ localities: [...value.localities, { city, postalCode }] })
    setLocInput('')
  }

  const goSection = (target: string) => {
    const scroller = scrollRef.current
    const el = scroller?.querySelector<HTMLElement>(`#${target}`)
    if (scroller && el) {
      const top = scroller.scrollTop + (el.getBoundingClientRect().top - scroller.getBoundingClientRect().top) - 12
      scroller.scrollTo({ top: Math.max(0, top), behavior: 'smooth' })
    }
    setActiveNav(target)
  }

  // Estimation visuelle (heuristique de demo, comme la maquette) — pas un vrai matching.
  const nMatch = useMemo(() => {
    let n = 12
    const span = value.priceMax - value.priceMin
    n -= span < 60000 ? 3 : 0
    n += span > 120000 ? 2 : 0
    n += Math.round(rayon / 8)
    n -= value.surfaceMin > 120 ? 3 : value.surfaceMin > 100 ? 1 : 0
    n -= seuil >= 85 ? 3 : seuil >= 80 ? 1 : 0
    n -= value.rooms >= 5 ? 2 : 0
    return Math.max(0, Math.min(18, n))
  }, [value.priceMin, value.priceMax, value.surfaceMin, value.rooms, rayon, seuil])

  const recap = useMemo(() => ({
    budget: `${Math.round(value.priceMin / 1000)}–${Math.round(value.priceMax / 1000)} k€`,
    secteur: value.localities.length ? `${value.localities[0].city || value.localities[0].postalCode}${rayon ? ` · ${rayon} km` : ''}` : '—',
    surface: value.surfaceMin ? `≥ ${value.surfaceMin} m²` : '—',
    pieces: `${value.rooms || '—'} p. · ${value.bedrooms || '—'} ch.`,
  }), [value, rayon])

  return (
    <div className={`step2a${showNav ? '' : ' no-nav'}${showPreview ? '' : ' no-pre'}`}>
      {showNav ? (
        <aside className="s2-nav">
          <div className="s2-nav-t">Le brief</div>
          {NAV.map((n) => (
            <button key={n.target} type="button" className={`enav${activeNav === n.target ? ' on' : ''}`} onClick={() => goSection(n.target)}>
              {n.target === 's-offre' ? IC.home : n.target === 's-loc' ? IC.pin : n.target === 's-budget' ? IC.euro : n.target === 's-surface' ? IC.grid : n.target === 's-pieces' ? IC.rooms : n.target === 's-equip' ? IC.shield : IC.bell}
              {n.label}
            </button>
          ))}
        </aside>
      ) : null}

      <div className="s2-body">
        <div className="fsec" id="s-offre">
          <div className="fsec-h"><span className="fsec-ic">{IC.home}</span><span className="fsec-t">Offre &amp; type de bien</span><span className="fsec-sp" /><span className="tag-sync">Synchronisé</span></div>
          <div className="field full" style={{ marginBottom: 16 }}>
            <div className="crit-label"><span>Type d'offre · offerCode</span></div>
            <div className="seg">
              {offerOptions.map((o) => (
                <button key={o.value} type="button" className={value.offerCode === o.value ? 'on' : ''} disabled={disabled} onClick={() => set({ offerCode: o.value })}>{o.label}</button>
              ))}
            </div>
          </div>
          <div className="field full">
            <div className="crit-label"><span>Types de bien · propertyTypeIds</span><span className="fsec-tag">{value.typeIds.length} type{value.typeIds.length > 1 ? 's' : ''}</span></div>
            <div className="choice">
              {TYPE_MAIN.map((t) => (
                <button key={t.id} type="button" className={`cbtn${value.typeIds.includes(t.id) ? ' on' : ''}`} disabled={disabled} onClick={() => set({ typeIds: toggleIn(value.typeIds, t.id) })}>{t.label}</button>
              ))}
            </div>
            {showMoreTypes ? (
              <div className="choice" style={{ marginTop: 10 }}>
                {TYPE_MORE.map((t) => (
                  <button key={t.id} type="button" className={`cbtn${value.typeIds.includes(t.id) ? ' on' : ''}`} disabled={disabled} onClick={() => set({ typeIds: toggleIn(value.typeIds, t.id) })}>{t.label}</button>
                ))}
              </div>
            ) : null}
            <button type="button" className={`morebtn${showMoreTypes ? ' open' : ''}`} onClick={() => setShowMoreTypes((v) => !v)}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="m6 9 6 6 6-6" /></svg>
              <span>{showMoreTypes ? 'Réduire les types' : `${TYPE_MORE.length} autres types`}</span>
            </button>
          </div>
        </div>

        <div className="fsec" id="s-loc">
          <div className="fsec-h"><span className="fsec-ic">{IC.pin}</span><span className="fsec-t">Localités &amp; rayon</span><span className="fsec-sp" /><span className="tag-sync">Requis</span></div>
          <div className="field full" style={{ marginBottom: 16 }}>
            <div className="crit-label"><span>Localités · city + postalCode</span></div>
            <div className="choice">
              {value.localities.map((l, i) => (
                <button key={`${l.city}-${l.postalCode}-${i}`} type="button" className="cbtn on" disabled={disabled} onClick={() => set({ localities: value.localities.filter((_, j) => j !== i) })}>
                  {[l.city, l.postalCode].filter(Boolean).join(' · ')} <span className="x">×</span>
                </button>
              ))}
              {!value.localities.length ? <span className="ctx-hint">Aucune commune — ajoute-en au moins une.</span> : null}
            </div>
            <div className="loc-input">
              <input className="inp" value={locInput} placeholder="Ajouter une commune (ville + code postal)…" disabled={disabled}
                onChange={(e) => setLocInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addLocality() } }} />
              <button type="button" className="btn-ghost" disabled={disabled} onClick={addLocality}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M12 5v14M5 12h14" /></svg>Ajouter
              </button>
            </div>
          </div>
          <div className="field full">
            <label>Rayon autour des localités</label>
            <div className="slider">
              <div className="slider-top"><span className="slider-val">{rayon} km autour</span><span className="slider-cap">{rayon === 0 ? 'localités seules' : `~ ${Math.max(1, Math.round(rayon / 1.4))} communes`}</span></div>
              <input type="range" min={0} max={40} step={5} value={rayon} aria-label="Rayon en km" disabled={disabled} onChange={(e) => setRayon(Number(e.target.value))} />
              <div className="range-ends"><span>Localités seules</span><span>40 km</span></div>
            </div>
          </div>
        </div>

        <div className="fsec" id="s-budget">
          <div className="fsec-h"><span className="fsec-ic">{IC.euro}</span><span className="fsec-t">Budget</span><span className="fsec-sp" /><span className="tag-sync">PRIX_MIN / MAX</span></div>
          <div className="field full" style={{ marginBottom: 16 }}>
            <label>Fourchette de prix</label>
            <div className="slider">
              <div className="slider-top"><span className="slider-val">{fmtEur(value.priceMin)} € – {fmtEur(value.priceMax)} €</span><span className="slider-cap">amplitude {fmtEur(value.priceMax - value.priceMin)} €</span></div>
              <div className="dual">
                <div className="track" />
                <div className="fill" style={{ left: `${(value.priceMin - 50000) / 450000 * 100}%`, width: `${(value.priceMax - value.priceMin) / 450000 * 100}%` }} />
                <input type="range" min={50000} max={500000} step={5000} value={value.priceMin} aria-label="Budget minimum" disabled={disabled}
                  onChange={(e) => set({ priceMin: Math.min(Number(e.target.value), value.priceMax - 5000) })} />
                <input type="range" min={50000} max={500000} step={5000} value={value.priceMax} aria-label="Budget maximum" disabled={disabled}
                  onChange={(e) => set({ priceMax: Math.max(Number(e.target.value), value.priceMin + 5000) })} />
              </div>
              <div className="range-ends"><span>50 000 €</span><span>500 000 €</span></div>
            </div>
          </div>
          <div className="fgrid2">
            <div className="field">
              <div className="crit-label"><span>Marge · PRIX_MARGE</span><span className="tag-todo">À brancher</span></div>
              <select className="inp" value={value.priceMargin} disabled={disabled} onChange={(e) => set({ priceMargin: e.target.value })}>
                <option value="">Aucune</option><option value="5">± 5 %</option><option value="10">± 10 %</option><option value="20">± 20 %</option>
              </select>
            </div>
            <div className="field">
              <label>Financement</label>
              <select className="inp" value={financement} disabled={disabled} onChange={(e) => setFinancement(e.target.value)}>
                <option value="valide">Validé</option><option value="encours">En cours</option><option value="comptant">Comptant</option>
              </select>
            </div>
          </div>
        </div>

        <div className="fsec" id="s-surface">
          <div className="fsec-h"><span className="fsec-ic">{IC.grid}</span><span className="fsec-t">Surfaces</span><span className="fsec-sp" /><span className="tag-sync">SURFACE_MIN / TERRAIN</span></div>
          <div className="fgrid2">
            <div className="field">
              <label>Habitable min.</label>
              <div className="slider">
                <div className="slider-top"><span className="slider-val">{value.surfaceMin || 0} m²</span></div>
                <input type="range" min={0} max={300} step={5} value={value.surfaceMin} disabled={disabled} onChange={(e) => set({ surfaceMin: Number(e.target.value) })} />
                <div className="range-ends"><span>Indifférent</span><span>300 m²</span></div>
              </div>
            </div>
            <div className="field">
              <label>Terrain min.</label>
              <div className="slider">
                <div className="slider-top"><span className="slider-val">{value.landSurfaceMin || 0} m²</span></div>
                <input type="range" min={0} max={2000} step={50} value={value.landSurfaceMin} disabled={disabled} onChange={(e) => set({ landSurfaceMin: Number(e.target.value) })} />
                <div className="range-ends"><span>Aucun</span><span>2000 m²</span></div>
              </div>
            </div>
          </div>
        </div>

        <div className="fsec" id="s-pieces">
          <div className="fsec-h"><span className="fsec-ic">{IC.rooms}</span><span className="fsec-t">Pièces &amp; chambres</span><span className="fsec-sp" /><span className="tag-sync">PIECES / CHAMBRE_MIN</span></div>
          <div className="steps">
            {[
              { label: 'Pièces min.', key: 'rooms' as const, min: 0, max: 12, todo: false },
              { label: 'Chambres min.', key: 'bedrooms' as const, min: 0, max: 10, todo: false },
              { label: 'SDB / SDE min.', key: 'bathrooms' as const, min: 0, max: 6, todo: true },
            ].map((s) => (
              <div className="sg" key={s.key}>
                <label>{s.label}</label>
                <div className="stepper-n">
                  <button type="button" disabled={disabled} onClick={() => set({ [s.key]: Math.max(s.min, (value[s.key] as number) - 1) } as Partial<ContactSearchFieldsValue>)}>–</button>
                  <span className="num">{value[s.key]}</span>
                  <button type="button" disabled={disabled} onClick={() => set({ [s.key]: Math.min(s.max, (value[s.key] as number) + 1) } as Partial<ContactSearchFieldsValue>)}>+</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="fsec" id="s-equip">
          <div className="fsec-h"><span className="fsec-ic">{IC.shield}</span><span className="fsec-t">Équipements</span><span className="fsec-sp" /><span className="tag-sync">Synchronisé</span></div>
          <div className="choice">
            {EQUIPMENTS.map((e) => (
              <button key={e.code} type="button" className={`cbtn teal${value.equipments.includes(e.code) ? ' on' : ''}`} disabled={disabled} onClick={() => set({ equipments: toggleIn(value.equipments, e.code) })}>{e.label}</button>
            ))}
          </div>
        </div>

        <div className="fsec" id="s-alerte">
          <div className="fsec-h"><span className="fsec-ic">{IC.bell}</span><span className="fsec-t">Alerte email &amp; note</span><span className="fsec-sp" /><span className="tag-todo">À brancher</span></div>
          <button type="button" className={`toggle-row${alerteOn ? '' : ' off'}`} aria-pressed={alerteOn} onClick={() => setAlerteOn((v) => !v)}>
            <span className="tg" />
            <span className="tr-bd"><span className="tr-t">Alerte email automatique</span><span className="tr-s">L'acquéreur reçoit les nouveaux biens dépassant le seuil de score.</span></span>
          </button>
          <div className={`fgrid2 alerte-params${alerteOn ? '' : ' off'}`}>
            <div className="field">
              <label>Fréquence</label>
              <select className="inp" value={alerteFreq} onChange={(e) => setAlerteFreq(e.target.value)}>
                <option value="quotidienne">Quotidienne</option><option value="hebdo">Hebdomadaire</option><option value="temps_reel">Temps réel</option>
              </select>
            </div>
            <div className="field">
              <label>Seuil de score</label>
              <div className="slider">
                <div className="slider-top"><span className="slider-val">≥ {seuil} %</span></div>
                <input type="range" min={50} max={95} step={5} value={seuil} onChange={(e) => setSeuil(Number(e.target.value))} />
                <div className="range-ends"><span>50 %</span><span>95 %</span></div>
              </div>
            </div>
          </div>
        </div>

        <div className="fsec" id="s-energie">
          <div className="fsec-h"><span className="fsec-ic">{IC.shield}</span><span className="fsec-t">Énergie (DPE)</span><span className="fsec-sp" /><span className="tag-sync">DPE</span></div>
          <div className="field full">
            <div className="crit-label"><span>DPE max · DPE_CONS_LETTER</span></div>
            <div className="choice">
              {DPE_LETTERS.map((l) => (
                <button key={l} type="button" className={`cbtn${value.dpeLetter === l ? ' on' : ''}`} disabled={disabled} onClick={() => set({ dpeLetter: value.dpeLetter === l ? '' : l })}>{l}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {showPreview ? (
        <aside className="s2-pre">
          <div className="pv-t">Aperçu en direct</div>
          <div className="pv-card">
            <div className="pv-num">{nMatch}</div>
            <div className="pv-lab">biens correspondants</div>
            <div className="pv-bar"><i style={{ width: `${Math.round(nMatch / 18 * 100)}%` }} /></div>
            <div className="pv-hint">Sur {Math.max(nMatch, Math.round(nMatch * 2.6))} biens {value.typeIds[0] && TYPE_LABEL[value.typeIds[0]] ? TYPE_LABEL[value.typeIds[0]].toLowerCase() : 'similaires'} au portefeuille dans la zone.</div>
          </div>
          <div className="pv-recap">
            <div className="pv-row"><span className="k">Budget</span><span className="v">{recap.budget}</span></div>
            <div className="pv-row"><span className="k">Secteur</span><span className="v">{recap.secteur}</span></div>
            <div className="pv-row"><span className="k">Surface</span><span className="v">{recap.surface}</span></div>
            <div className="pv-row"><span className="k">Pièces</span><span className="v">{recap.pieces}</span></div>
          </div>
        </aside>
      ) : null}
    </div>
  )
}
