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
  { target: 's-offre', label: 'Offre & type' }, { target: 's-loc', label: 'Localités' }, { target: 's-budget', label: 'Budget' },
  { target: 's-surface', label: 'Surfaces' }, { target: 's-pieces', label: 'Pièces' }, { target: 's-equip', label: 'Équipements' },
  { target: 's-energie', label: 'Énergie' },
]

const EQUIP_ITEM_BY_CODE: Record<string, string> = {
  garage_parking: 'ITEM_GARAGE_PARKING', terrasse: 'ITEM_TERRASSE', balcon: 'ITEM_BALCON', piscine: 'ITEM_PISCINE',
  ascenseur: 'ITEM_ASCENSEUR', cheminee: 'ITEM_CHEMINEE', cave: 'ITEM_CAVE', double_vitrage: 'ITEM_DOUBLE_VITRAGE',
  plain_pied: 'ITEM_PLAIN_PIED', grenier_comble: 'ITEM_GRENIER_COMBLE', acces_handi: 'ITEM_ACCES_HANDI',
  terrain_constructible: 'ITEM_TERRAIN_CONSTRUCTIBLE', terrain_arbore: 'ITEM_TERRAIN_ARBORE',
  terrain_piscinable: 'ITEM_TERRAIN_PISCINABLE', terrain_viabilise: 'ITEM_TERRAIN_VIABILISE',
}

function fmtEur(n: number) { return new Intl.NumberFormat('fr-FR').format(n) }

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

// Construit une valeur de formulaire a partir d'une recherche existante (mode edition).
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

  const recap = useMemo(() => ({
    offre: offerOptions.find((o) => o.value === value.offerCode)?.label ?? value.offerCode,
    types: value.typeIds.length,
    budget: `${Math.round(value.priceMin / 1000)}–${Math.round(value.priceMax / 1000)} k€`,
    secteur: value.localities.length ? `${value.localities[0].city || value.localities[0].postalCode}${value.localities.length > 1 ? ` +${value.localities.length - 1}` : ''}` : '—',
    surface: value.surfaceMin ? `≥ ${value.surfaceMin} m²` : '—',
    pieces: `${value.rooms || '—'} p. · ${value.bedrooms || '—'} ch.`,
  }), [value, offerOptions])

  return (
    <div className={`step2a${showNav ? '' : ' no-nav'}${showPreview ? '' : ' no-pre'}`}>
      {showNav ? (
        <aside className="s2-nav">
          <div className="s2-nav-t">Le brief</div>
          {NAV.map((n) => (
            <button key={n.target} type="button" className={`enav${activeNav === n.target ? ' on' : ''}`} onClick={() => goSection(n.target)}>{n.label}</button>
          ))}
        </aside>
      ) : null}

      <div className="s2-body">
        <div className="fsec" id="s-offre">
          <div className="fsec-h"><span className="fsec-t">Offre &amp; type de bien</span><span className="fsec-sp" /><span className="tag-sync">Synchronisé</span></div>
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
          <div className="fsec-h"><span className="fsec-t">Localités</span><span className="fsec-sp" /><span className="tag-sync">Requis</span></div>
          <div className="field full">
            <div className="crit-label"><span>Communes · city + postalCode</span></div>
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
        </div>

        <div className="fsec" id="s-budget">
          <div className="fsec-h"><span className="fsec-t">Budget</span><span className="fsec-sp" /><span className="tag-sync">PRIX_MIN / MAX</span></div>
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
              <div className="crit-label"><span>Marge · PRIX_MARGE</span></div>
              <select className="inp" value={value.priceMargin} disabled={disabled} onChange={(e) => set({ priceMargin: e.target.value })}>
                <option value="">Aucune</option><option value="5">± 5 %</option><option value="10">± 10 %</option><option value="20">± 20 %</option>
              </select>
            </div>
          </div>
        </div>

        <div className="fsec" id="s-surface">
          <div className="fsec-h"><span className="fsec-t">Surfaces</span><span className="fsec-sp" /><span className="tag-sync">SURFACE_MIN / TERRAIN</span></div>
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
          <div className="fsec-h"><span className="fsec-t">Pièces &amp; chambres</span><span className="fsec-sp" /><span className="tag-sync">PIECES / CHAMBRE_MIN</span></div>
          <div className="steps">
            {[
              { label: 'Pièces min.', key: 'rooms' as const, min: 0, max: 12 },
              { label: 'Chambres min.', key: 'bedrooms' as const, min: 0, max: 10 },
              { label: 'SDB / SDE min.', key: 'bathrooms' as const, min: 0, max: 6 },
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
          <div className="fsec-h"><span className="fsec-t">Équipements</span><span className="fsec-sp" /><span className="tag-sync">Synchronisé</span></div>
          <div className="choice">
            {EQUIPMENTS.map((e) => (
              <button key={e.code} type="button" className={`cbtn teal${value.equipments.includes(e.code) ? ' on' : ''}`} disabled={disabled} onClick={() => set({ equipments: toggleIn(value.equipments, e.code) })}>{e.label}</button>
            ))}
          </div>
        </div>

        <div className="fsec" id="s-energie">
          <div className="fsec-h"><span className="fsec-t">Énergie</span><span className="fsec-sp" /><span className="tag-sync">DPE</span></div>
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
          <div className="pv-t">Récapitulatif</div>
          <div className="pv-recap">
            <div className="pv-row"><span className="k">Offre</span><span className="v">{recap.offre}</span></div>
            <div className="pv-row"><span className="k">Types</span><span className="v">{recap.types}</span></div>
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
