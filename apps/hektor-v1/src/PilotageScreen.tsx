// Pilotage (02/11/2026) — écran ADMIN, LECTURE SEULE, quatre onglets : vue d'ensemble, ventes, mandats, stock.
// 03/11 : étape 1 de la refonte (notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md § 27) — « L'essentiel » en 12 chiffres
// qui défilent, entrée animée des blocs, barres et courbes qui se dessinent.
// 03/11 soir : le tableau de bord v3 validé sur la maquette (§ 29 à 32) — la courbe des honoraires, trois chiffres de
// tête, trois phrases à retenir, à traiter, en route, les six premières agences ; les 12 chiffres repliés.
// Maquette validée : https://claude.ai/artifact/CJ9v7PnqkNvYHNGsG8R1Qr ; audit et décisions :
// notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md. Les lectures et les calculs sont dans lib/pilotage.ts.
// Décisions de Frédéric : admins seuls, honoraires HT par défaut (TTC d'un clic), comparaison à l'année
// précédente « à la même date », le C.A potentiel du stock mis en avant (honoraires, pas le prix).
// Une source qui ne se lit pas n'éteint que SON bloc (« n'a pas pu être lu ») ; le détail part en console.
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  aujourdhui, calculerMandats, calculerPortails, calculerSignatures, calculerStock, calculerVentes, cleAgence, loadPilotage, nomAgence,
  type PilotageSources,
} from './lib/pilotage'
import './pilotage.css'

type Onglet = 'ensemble' | 'ventes' | 'mandats' | 'stock'
const ONGLETS: Array<{ cle: Onglet; libelle: string }> = [
  { cle: 'ensemble', libelle: 'Tableau de bord' }, { cle: 'ventes', libelle: 'Ventes' }, { cle: 'mandats', libelle: 'Mandats' }, { cle: 'stock', libelle: 'Stock' },
]
const ANNEE_COURANTE = Number(aujourdhui().slice(0, 4))
const ANNEES = Array.from({ length: ANNEE_COURANTE - 2007 + 1 }, (_, i) => ANNEE_COURANTE - i)
const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
const MEMO = 'gti_pilotage_v1'

const entier = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
function lireMemo(): { onglet: Onglet; ttc: boolean } {
  try {
    const brut = JSON.parse(window.localStorage.getItem(MEMO) ?? '{}') as { onglet?: string; ttc?: boolean }
    return { onglet: ONGLETS.some((o) => o.cle === brut.onglet) ? brut.onglet as Onglet : 'ensemble', ttc: brut.ttc === true }
  } catch { return { onglet: 'ensemble', ttc: false } }
}

// ─── petites briques d'affichage ───

function ecart(a: number, b: number) {
  if (!b) return null
  const x = ((a - b) / b) * 100
  return { texte: `${x >= 0 ? '▲ +' : '▼ −'}${Math.abs(x).toFixed(1).replace('.', ',')} %`, bon: x >= 0 }
}
function ecartPoints(a: number, b: number) {
  const x = a - b
  return { texte: `${x >= 0 ? '▲ +' : '▼ −'}${Math.abs(Math.round(x))} pts`, bon: x >= 0 }
}
const pourcent = (a: number, b: number) => (b ? Math.round((a / b) * 100) : 0)

function Ecart({ valeur }: { valeur: { texte: string; bon: boolean } | null }) {
  if (!valeur) return null
  return <b className={`pl-ecart ${valeur.bon ? 'is-bon' : 'is-mauvais'}`}>{valeur.texte}</b>
}

function Courbe({ valeurs, prec, couleur, max }: { valeurs: number[]; prec?: number[]; couleur: string; max: number }) {
  if (!valeurs.length) return <span className="pl-courbe-vide" />
  const points = (liste: number[]) => liste.map((v, i) => `${((i * 100) / 11).toFixed(1)},${(26 - (v / (max || 1)) * 24).toFixed(1)}`).join(' ')
  return (
    <svg className="pl-courbe" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true">
      {prec?.length ? <polyline points={points(prec)} fill="none" stroke="#c9ced0" strokeWidth="1.6" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" /> : null}
      <polyline points={points(valeurs)} fill="none" stroke={couleur} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function Carte({ libelle, genre, valeur, detail, ecartValeur, courbe, onClick, grande }: {
  libelle: string; genre?: string; valeur: ReactNode; detail?: ReactNode; ecartValeur?: { texte: string; bon: boolean } | null; courbe?: ReactNode; onClick?: () => void; grande?: boolean
}) {
  const contenu = (
    <>
      <span className="pl-carte-haut"><span className="pl-lib">{libelle}</span>{genre ? <span className="pl-puce">{genre}</span> : null}</span>
      <b className={`pl-valeur pl-num${grande ? ' is-grande' : ''}`}>{valeur}</b>
      <span className="pl-detail"><Ecart valeur={ecartValeur ?? null} /> {detail}</span>
      {courbe}
    </>
  )
  return onClick
    ? <button type="button" className="pl-carte pl-kpi is-cliquable" onClick={onClick}>{contenu}</button>
    : <div className="pl-carte pl-kpi">{contenu}</div>
}

// Un chiffre qui défile jusqu'à sa valeur (1,1 s). Coupé si l'appareil demande moins de mouvement.
function Compteur({ valeur, format }: { valeur: number; format: (x: number) => string }) {
  const [affiche, setAffiche] = useState(valeur)
  useEffect(() => {
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) { setAffiche(valeur); return undefined }
    let id = 0
    const debut = performance.now()
    const tour = (t: number) => {
      const p = Math.min(1, (t - debut) / 1100)
      setAffiche(valeur * (1 - Math.pow(1 - p, 3)))
      if (p < 1) id = requestAnimationFrame(tour)
    }
    id = requestAnimationFrame(tour)
    return () => cancelAnimationFrame(id)
  }, [valeur])
  return <>{format(affiche)}</>
}

function Indisponible({ quoi, onReessayer }: { quoi: string; onReessayer: () => void }) {
  return (
    <div className="pl-carte pl-indispo" role="status">
      <b>{quoi} n’a pas pu être lu.</b>
      <button type="button" className="pl-bouton" onClick={onReessayer}>Réessayer</button>
    </div>
  )
}

function Barre({ part, ton, fine }: { part: number; ton: string; fine?: boolean }) {
  return <span className={`pl-piste${fine ? ' is-fine' : ''}`}><span style={{ width: `${Math.max(0, Math.min(100, part))}%`, background: ton }} /></span>
}

// ─── tableau de bord v3 (03/11) : la grande courbe, les chiffres de tête ───

const ICONES = {
  tient: 'M3 17l6-6 4 4 8-8M14 7h7v7',
  recul: 'M3 7l6 6 4-4 8 8M14 17h7v-7',
  etoile: 'M12 2l3 6.5 7 .9-5.1 4.8 1.3 7L12 17.8 5.8 21.2l1.3-7L2 9.4l7-.9z',
}

// Une courbe lissée : chaque segment est une courbe de Bézier dont les deux poignées sont à mi-chemin.
function lisser(points: Array<[number, number]>) {
  if (!points.length) return ''
  let d = `M${points[0][0].toFixed(1)} ${points[0][1].toFixed(1)}`
  for (let i = 1; i < points.length; i += 1) {
    const [x0, y0] = points[i - 1]
    const [x1, y1] = points[i]
    const cx = ((x0 + x1) / 2).toFixed(1)
    d += ` C${cx} ${y0.toFixed(1)} ${cx} ${y1.toFixed(1)} ${x1.toFixed(1)} ${y1.toFixed(1)}`
  }
  return d
}

// Les honoraires mois par mois : la courbe se trace, l'aire se dévoile, l'an passé en pointillé ;
// au survol d'un mois, un repère et une bulle donnent les deux années.
function GrandeCourbe({ valeurs, prec, annee, format }: { valeurs: number[]; prec: number[] | null; annee: number; format: (x: number) => string }) {
  const [survol, setSurvol] = useState<number | null>(null)
  if (!valeurs.length) return null
  const L = 640
  const H = 170
  const haut = 12
  const bas = 158
  const n = Math.max(valeurs.length, prec ? 12 : 0, 2)
  const max = Math.max(1, ...valeurs, ...(prec ?? [])) * 1.08
  const x = (i: number) => 10 + (i / (n - 1)) * (L - 20)
  const y = (v: number) => bas - (v / max) * (bas - haut)
  const courbe = lisser(valeurs.map((v, i) => [x(i), y(v)]))
  const courbePrec = prec ? lisser(prec.slice(0, n).map((v, i) => [x(i), y(v)])) : ''
  const fin = valeurs.length - 1
  const aire = `${courbe} L${x(fin).toFixed(1)} ${bas} L${x(0).toFixed(1)} ${bas} Z`
  const pas = (L - 20) / (n - 1)
  const lignes = [0.33, 0.66].map((part) => bas - part * (bas - haut))
  const gauche = survol != null ? Math.min(78, Math.max(0, (x(survol) / L) * 100 - 9)) : 0
  return (
    <div className="pl-gc" onMouseLeave={() => setSurvol(null)}>
      <svg viewBox={`0 0 ${L} ${H}`} className="pl-gc-svg" role="img" aria-label={`Honoraires par mois en ${annee}${prec ? `, comparés à ${annee - 1}` : ''}`}>
        <defs><linearGradient id="pl-gc-aire" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#e0457b" stopOpacity=".28" /><stop offset="1" stopColor="#e0457b" stopOpacity="0" /></linearGradient></defs>
        {lignes.map((v) => <line key={v} x1="0" x2={L} y1={v} y2={v} stroke="#eef0f2" strokeWidth="1" />)}
        <line x1="0" x2={L} y1={bas} y2={bas} stroke="#e3e6e7" strokeWidth="1" />
        <path className="pl-voile" d={aire} fill="url(#pl-gc-aire)" style={{ animationDelay: '.9s' }} />
        {courbePrec ? <path className="pl-voile" d={courbePrec} fill="none" stroke="#b9bec4" strokeWidth="2" strokeDasharray="4 5" strokeLinecap="round" style={{ animationDelay: '.5s' }} /> : null}
        <path className="pl-trace" d={courbe} pathLength={1} fill="none" stroke="#c5005f" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ animationDelay: '.3s' }} />
        <circle className="pl-onde" cx={x(fin)} cy={y(valeurs[fin])} r="5" fill="#c5005f" />
        <circle cx={x(fin)} cy={y(valeurs[fin])} r="5" fill="#fff" stroke="#c5005f" strokeWidth="3" />
        {survol != null ? <>
          <line x1={x(survol)} x2={x(survol)} y1="6" y2={bas} stroke="#1f2121" strokeOpacity=".18" strokeWidth="1" />
          {prec && prec[survol] != null ? <circle cx={x(survol)} cy={y(prec[survol])} r="4.5" fill="#fff" stroke="#9aa0a6" strokeWidth="2.5" /> : null}
          {survol <= fin ? <circle cx={x(survol)} cy={y(valeurs[survol])} r="6" fill="#c5005f" stroke="#fff" strokeWidth="3" /> : null}
        </> : null}
        {Array.from({ length: n }, (_, i) => (
          <rect key={i} x={Math.max(0, x(i) - pas / 2)} y="0" width={pas} height={H} fill="transparent" onMouseEnter={() => setSurvol(i)} />
        ))}
      </svg>
      <div className={`pl-gc-bulle${survol != null ? ' is-vue' : ''}`} style={{ left: `${gauche}%` }} aria-hidden={survol == null}>
        {survol != null ? <>
          <b>{MOIS[survol]} {annee}</b>
          <span className="pl-num is-marque">{survol <= fin ? format(valeurs[survol]) : '–'}</span>
          {prec ? <span className="pl-num pl-mute">{annee - 1} : {format(prec[survol] ?? 0)}</span> : null}
        </> : null}
      </div>
      <div className="pl-gc-mois">{Array.from({ length: n }, (_, i) => <span key={i} className={i > fin ? 'is-futur' : ''}>{MOIS[i]}</span>)}</div>
    </div>
  )
}

// Un chiffre de tête avec sa mini-courbe des mois de l'année, qui se dessine à l'ouverture.
function ChiffreTete({ libelle, valeur, prec, serie, couleur, sous, onClick, rang }: {
  libelle: string; valeur: number; prec: number | null; serie: number[]; couleur: string; sous?: string; onClick: () => void; rang: number
}) {
  const x = prec != null ? ecart(valeur, prec) : null
  const max = Math.max(...serie, 1)
  const min = Math.min(...serie, 0)
  const pts = serie.map((v, i) => [(i / Math.max(1, serie.length - 1)) * 106 + 2, 36 - ((v - min) / (max - min || 1)) * 30] as [number, number])
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ')
  const dernier = pts[pts.length - 1]
  return (
    <button type="button" className="pl-carte pl-tdb-chiffre pl-monte" style={{ animationDelay: `${120 + rang * 90}ms` }} onClick={onClick}>
      <span className="pl-carte-haut"><span className="pl-lib">{libelle}</span>{x ? <span className={`pl-delta is-${x.bon ? 'up' : 'dn'} pl-pop`} style={{ animationDelay: `${1.2 + rang * 0.12}s` }}>{x.texte}</span> : null}</span>
      <span className="pl-tdb-chiffre-bas">
        <span className="pl-tdb-chiffre-texte">
          <b className="pl-tdb-chiffre-valeur pl-num"><Compteur valeur={valeur} format={(v) => entier.format(Math.round(v))} /></b>
          <span className="pl-mute">{sous ?? (prec != null ? `contre ${entier.format(prec)}` : '')}</span>
        </span>
        {serie.length > 1 ? (
          <svg viewBox="0 0 110 40" className="pl-tdb-spark" aria-hidden="true">
            <path className="pl-trace" d={d} pathLength={1} fill="none" stroke={couleur} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ animationDelay: `${0.5 + rang * 0.15}s` }} />
            {dernier ? <circle cx={dernier[0]} cy={dernier[1]} r="3.5" fill={couleur} /> : null}
          </svg>
        ) : null}
      </span>
    </button>
  )
}

// ─── l'écran ───

export default function PilotageScreen() {
  const [depart] = useState(lireMemo)
  const [onglet, setOnglet] = useState<Onglet>(depart.onglet)
  const [ttc, setTtc] = useState(depart.ttc)
  const [annee, setAnnee] = useState(ANNEE_COURANTE)
  const [agence, setAgence] = useState<string | null>(null)
  const [comparer, setComparer] = useState(true)
  const [sources, setSources] = useState<PilotageSources | null>(null)
  const [essai, setEssai] = useState(0)
  const [tousNegos, setTousNegos] = useState(false)
  const [deplie, setDeplie] = useState(false)

  useEffect(() => {
    try { window.localStorage.setItem(MEMO, JSON.stringify({ onglet, ttc })) } catch { /* mémoire facultative */ }
  }, [onglet, ttc])

  // Sur téléphone, la barre d'onglets défile : l'onglet choisi reste en vue.
  useEffect(() => {
    const actif = document.querySelector<HTMLElement>('.pl-onglet.is-actif')
    const barre = actif?.parentElement
    if (actif && barre) barre.scrollLeft = Math.max(0, actif.offsetLeft - barre.offsetLeft - 16)
  }, [onglet])

  useEffect(() => {
    let annule = false
    setSources(null)
    loadPilotage(annee).then((lu) => {
      if (annule) return
      for (const [cle, valeur] of Object.entries(lu)) if (valeur instanceof Error) console.error(`[pilotage] ${cle}`, valeur)
      setSources(lu)
    })
    return () => { annule = true }
  }, [annee, essai])

  const reessayer = () => setEssai((x) => x + 1)
  const enCours = annee === ANNEE_COURANTE
  const coef = ttc ? 1 : 1 / 1.2
  const unite = ttc ? 'TTC' : 'HT'
  const euros = (x: number) => `${entier.format(Math.round(x * coef))} €`
  const compact = (x: number) => { const y = x * coef; return y >= 1e6 ? `${(y / 1e6).toFixed(2).replace('.', ',')} M€` : `${entier.format(Math.round(y / 1000))} k€` }
  const libelleComparaison = enCours ? `${annee - 1} à la même date` : `${annee - 1}`

  const ventes = useMemo(() => (sources && !(sources.ventes instanceof Error) ? calculerVentes(sources.ventes, annee, agence) : null), [sources, annee, agence])
  const mandats = useMemo(() => (sources && !(sources.mandats instanceof Error) ? calculerMandats(sources.mandats, annee, agence) : null), [sources, annee, agence])
  const stock = useMemo(() => (sources && !(sources.stock instanceof Error) ? calculerStock(sources.stock, agence) : null), [sources, agence])
  const signatures = useMemo(() => (sources && !(sources.signatures instanceof Error) ? calculerSignatures(sources.signatures, annee) : null), [sources, annee])
  const portails = useMemo(() => (sources && !(sources.portails instanceof Error) && !(sources.stock instanceof Error) ? calculerPortails(sources.portails, sources.stock, agence) : null), [sources, agence])

  // Les agences proposées au filtre : toutes celles que les sources connaissent, une seule fois chacune.
  const agencesConnues = useMemo(() => {
    const cles = new Set<string>()
    if (sources) {
      if (!(sources.ventes instanceof Error)) for (const l of [...sources.ventes.n, ...sources.ventes.p]) cles.add(cleAgence(l.agence_nom))
      if (!(sources.mandats instanceof Error)) for (const l of sources.mandats) cles.add(cleAgence(l.agence))
      if (!(sources.stock instanceof Error)) for (const l of sources.stock) cles.add(cleAgence(l.agence_nom))
    }
    cles.delete('')
    return [...cles].sort((a, b) => nomAgence(a).localeCompare(nomAgence(b), 'fr'))
  }, [sources])

  const chargement = sources == null
  const moisVisibles = enCours ? Number(aujourdhui().slice(5, 7)) : 12

  return (
    <section className="pl-ecran" aria-labelledby="pl-titre">
      <header className="pl-entete">
        <div className="pl-entete-haut">
          <div className="pl-titres">
            <span className="pl-surtitre">Pilotage · réseau GTI · réservé aux administrateurs</span>
            <h1 id="pl-titre" className="pl-titre">{ONGLETS.find((o) => o.cle === onglet)?.libelle}</h1>
          </div>
          <span className="pl-mute pl-fraicheur"><i className={`pl-vif${chargement ? ' is-attente' : ''}`} aria-hidden="true" />{chargement ? 'Lecture des données…' : `Données de cette nuit · lues le ${new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}`}</span>
        </div>
        <nav className="pl-onglets" role="tablist" aria-label="Onglets du pilotage">
          {ONGLETS.map((o) => (
            <button key={o.cle} type="button" role="tab" aria-selected={onglet === o.cle} className={`pl-onglet${onglet === o.cle ? ' is-actif' : ''}`} onClick={() => setOnglet(o.cle)}>{o.libelle}</button>
          ))}
          <span className="pl-onglet is-bientot" title="Disponible quand la photo quotidienne des statuts aura quelques mois">Estimations <span className="pl-puce">bientôt</span></span>
        </nav>
      </header>

      <div className="pl-filtres">
        <label className="pl-filtre">
          <span>{onglet === 'stock' ? 'Année (ventes et mandats)' : 'Période'}</span>
          <select value={annee} onChange={(e) => setAnnee(Number(e.target.value))}>
            {ANNEES.map((a) => <option key={a} value={a}>{a === ANNEE_COURANTE ? `${a} à date` : a}</option>)}
          </select>
        </label>
        <label className="pl-filtre">
          <span>Agence</span>
          <select value={agence ?? ''} onChange={(e) => setAgence(e.target.value || null)}>
            <option value="">Toutes ({agencesConnues.length})</option>
            {agencesConnues.map((a) => <option key={a} value={a}>{nomAgence(a)}</option>)}
          </select>
        </label>
        {onglet !== 'stock' ? (
          <button type="button" className={`pl-bascule${comparer ? ' is-actif' : ''}`} aria-pressed={comparer} onClick={() => setComparer((x) => !x)}>Comparer à {libelleComparaison}</button>
        ) : <span className="pl-puce" title="Le stock n’est gardé qu’au jour le jour">Photo du jour, sans comparaison possible</span>}
        <span className="pl-espace" />
        <div className="pl-seg" role="group" aria-label="Honoraires">
          <button type="button" className={!ttc ? 'is-actif' : ''} aria-pressed={!ttc} onClick={() => setTtc(false)}>HT</button>
          <button type="button" className={ttc ? 'is-actif' : ''} aria-pressed={ttc} onClick={() => setTtc(true)}>TTC</button>
        </div>
      </div>

      {chargement ? (
        <div className="pl-grille-kpi">{[0, 1, 2, 3].map((i) => <div key={i} className="pl-carte pl-kpi"><span className="pl-sk" /><span className="pl-sk is-grand" /></div>)}</div>
      ) : (
        // La clé rejoue l'entrée animée à chaque changement d'onglet, d'année ou d'agence.
        <div key={`${onglet}-${annee}-${agence ?? ''}`} className="pl-contenu">
          {onglet === 'ensemble' ? Ensemble() : onglet === 'ventes' ? Ventes() : onglet === 'mandats' ? Mandats() : Stock()}
        </div>
      )}
    </section>
  )

  // ───────────────────────── TABLEAU DE BORD ─────────────────────────
  // 03/11 : le tableau de bord v3 validé par Frédéric (maquette version 29-30) — le résultat d'abord, trois
  // phrases à retenir, ce qui est à traiter et ce qui est en route, les six premières agences ; le reste replié.
  function Ensemble() {
    const mois = Array.from({ length: moisVisibles }, (_, i) => i)
    const agences = new Set<string>([...(ventes ? ventes.agences.keys() : []), ...(mandats ? mandats.agences.keys() : []), ...(stock ? stock.agences.keys() : [])])
    agences.delete('')
    const lignes = [...agences].map((cle) => ({
      cle, v: ventes?.agences.get(cle), m: mandats?.agences.get(cle), s: stock?.agences.get(cle),
    })).sort((a, b) => (b.v?.h ?? 0) - (a.v?.h ?? 0))
    const maxH = Math.max(1, ...lignes.map((l) => l.v?.h ?? 0))
    const maxFlux = Math.max(1, ...mois.map((i) => Math.max(mandats?.parMois[i].n ?? 0, ventes?.parMois[i].n ?? 0)))
    const parActe = ventes && ventes.ventes ? ventes.honoraires / ventes.ventes : 0
    const parActePrec = ventes && ventes.ventesPrec ? ventes.honorairesPrec / ventes.ventesPrec : 0
    const prixMoyen = ventes && ventes.ventes ? ventes.volume / ventes.ventes : 0
    const prixMoyenPrec = ventes && ventes.ventesPrec ? ventes.volumePrec / ventes.ventesPrec : 0
    const taux = ventes && ventes.volume ? ((ventes.honoraires * coef) / ventes.volume) * 100 : 0
    const tauxPrec = ventes && ventes.volumePrec ? ((ventes.honorairesPrec * coef) / ventes.volumePrec) * 100 : 0
    const virgule = (x: number, d = 1) => x.toFixed(d).replace('.', ',')
    const delai = ventes?.delaiOffreActe ?? null
    const delaiPrec = ventes?.delaiOffreActePrec ?? null
    const tauxEx = mandats ? pourcent(mandats.exclusifs, mandats.n) : 0
    const tauxExPrec = mandats ? pourcent(mandats.exclusifsPrec, mandats.nPrec) : 0
    const pct = (a: number, b: number) => (b ? ((a - b) / b) * 100 : null)
    const sens = (x: number | null, seuil: number): 'up' | 'dn' | 'nt' => (x == null ? 'nt' : x >= seuil ? 'up' : x <= -seuil ? 'dn' : 'nt')
    const ecartCa = ventes ? pct(ventes.honoraires, ventes.honorairesPrec) : null
    const ecartCp = ventes ? pct(ventes.compromis.n, ventes.compromis.nPrec) : null
    const ecartEx = mandats && mandats.nPrec ? tauxEx - tauxExPrec : null

    // Les trois phrases « à retenir » se déduisent des chiffres affichés : aucune n'est écrite à la main.
    const retenir: Array<{ cle: string; titre: string; sous: string; ton: 'up' | 'dn' | 'nt'; icone: string }> = []
    if (ventes && comparer && ecartCa != null) {
      const t = sens(ecartCa, 3)
      retenir.push({ cle: 'ca', ton: t, icone: t === 'dn' ? ICONES.recul : ICONES.tient,
        titre: t === 'nt' ? 'Le chiffre d’affaires tient' : `Le chiffre d’affaires ${t === 'up' ? 'progresse' : 'recule'} de ${Math.abs(Math.round(ecartCa))} %`,
        sous: `${entier.format(ventes.ventes)} actes contre ${entier.format(ventes.ventesPrec)}, à ${euros(parActe)} ${unite} par acte contre ${euros(parActePrec)}.` })
    }
    if (ventes && comparer && ecartCp != null) {
      const t = sens(ecartCp, 3)
      retenir.push({ cle: 'cp', ton: t, icone: t === 'dn' ? ICONES.recul : ICONES.tient,
        titre: t === 'nt' ? 'Les compromis se maintiennent' : `Les compromis ${t === 'up' ? 'progressent' : 'reculent'} de ${Math.abs(Math.round(ecartCp))} %`,
        sous: `${entier.format(ventes.compromis.n)} signés contre ${entier.format(ventes.compromis.nPrec)} : les actes des prochains mois en dépendent.` })
    }
    if (mandats && comparer && ecartEx != null) {
      const t = sens(ecartEx, 2)
      const pts = Math.abs(Math.round(ecartEx))
      retenir.push({ cle: 'ex', ton: t, icone: ICONES.etoile,
        titre: t === 'nt' ? 'L’exclusivité se maintient' : `L’exclusivité ${t === 'up' ? 'gagne' : 'perd'} ${pts} point${pts > 1 ? 's' : ''}`,
        sous: `${tauxEx} % des mandats rentrés sont exclusifs, contre ${tauxExPrec} % ${enCours ? 'à la même date' : `en ${annee - 1}`}.` })
    }

    // À traiter : ce qui demande un geste aujourd'hui (seulement pour l'année en cours).
    type Action = { cle: string; n: number; h: number; titre: string; ton: 'rouge' | 'ambre' | 'bleu'; vers: Onglet }
    const actions: Action[] = []
    if (enCours && ventes) {
      actions.push({ cle: 'actes', n: ventes.enRoute.actesDepasses.n, h: ventes.enRoute.actesDepasses.h, titre: 'Actes à date dépassée', ton: 'rouge', vers: 'ventes' })
      actions.push({ cle: 'offres', n: ventes.enRoute.offresSansCompromis30.n, h: ventes.enRoute.offresSansCompromis30.h, titre: 'Offres acceptées sans compromis depuis 30 jours', ton: 'ambre', vers: 'ventes' })
    }
    if (enCours && stock) actions.push({ cle: 'echus', n: stock.echus, h: 0, titre: 'Mandats échus, bien toujours en vente', ton: 'ambre', vers: 'stock' })
    if (enCours && signatures) actions.push({ cle: 'sign', n: signatures.enAttente, h: 0, titre: 'Signatures de mandat en attente', ton: 'bleu', vers: 'mandats' })
    const maxAction = Math.max(1, ...actions.map((a) => a.n))

    const route = ventes && enCours ? [
      { cle: 'cp', libelle: 'Compromis en cours', n: ventes.enRoute.compromis.n, h: ventes.enRoute.compromis.h, ton: '#a3004f', quoi: 'dossiers' },
      { cle: 'of', libelle: 'Offres acceptées', n: ventes.enRoute.offresAcceptees.n, h: ventes.enRoute.offresAcceptees.h, ton: '#d4478a', quoi: 'dossiers' },
      ...(stock ? [{ cle: 'st', libelle: 'Biens en vente', n: stock.actifs, h: stock.potentiel, ton: '#f4b3cd', quoi: 'biens' }] : []),
    ] : []
    const engage = ventes ? ventes.enRoute.compromis.h + ventes.enRoute.offresAcceptees.h : 0

    const top = [...(ventes?.agences.entries() ?? [])].filter(([cle]) => cle).sort((a, b) => b[1].h - a[1].h).slice(0, 6)
    const maxTop = Math.max(1, ...top.map(([, a]) => Math.max(a.h, comparer ? a.hPrec : 0)))

    return (
      <>
        <section className="pl-tdb-heros" aria-label="Le résultat">
          {ventes ? (
            <div className="pl-carte pl-tdb-ca">
              <span className="pl-halo is-un" aria-hidden="true" /><span className="pl-halo is-deux" aria-hidden="true" />
              <div className="pl-tdb-ca-tete">
                <span className="pl-lib">Honoraires encaissés · {unite} · {enCours ? `janvier à ${MOIS[moisVisibles - 1]}` : annee}</span>
                <span className="pl-legende"><i style={{ background: '#c5005f' }} />{annee}{comparer ? <><i className="is-tirets" />{annee - 1}</> : null}</span>
              </div>
              <span className="pl-tdb-ca-ligne">
                <b className="pl-tdb-ca-valeur pl-num pl-brille"><Compteur valeur={ventes.honoraires} format={compact} /></b>
                {comparer && ecartCa != null ? <span className={`pl-delta is-${sens(ecartCa, 0.05)} pl-pop`}>{ecart(ventes.honoraires, ventes.honorairesPrec)?.texte}</span> : null}
                {comparer ? <span className="pl-mute">contre {compact(ventes.honorairesPrec)} en {annee - 1}</span> : null}
              </span>
              <GrandeCourbe valeurs={ventes.parMois.slice(0, moisVisibles).map((m) => m.h)} prec={comparer ? ventes.parMoisPrec.map((m) => m.h) : null}
                annee={annee} format={(x) => `${entier.format(Math.round((x * coef) / 1000))} k€`} />
            </div>
          ) : <Indisponible quoi="Le registre des ventes" onReessayer={reessayer} />}
          <div className="pl-tdb-trois">
            {ventes ? <>
              <ChiffreTete libelle="Actes signés" valeur={ventes.ventes} prec={comparer ? ventes.ventesPrec : null} serie={ventes.parMois.slice(0, moisVisibles).map((m) => m.n)} couleur="#c5005f" onClick={() => setOnglet('ventes')} rang={0} />
              <ChiffreTete libelle="Compromis signés" valeur={ventes.compromis.n} prec={comparer ? ventes.compromis.nPrec : null} serie={ventes.compromis.parMois.slice(0, moisVisibles)} couleur="#d98a00" onClick={() => setOnglet('ventes')} rang={1} />
            </> : null}
            {mandats ? <ChiffreTete libelle="Mandats rentrés" valeur={mandats.n} prec={comparer ? mandats.nPrec : null} serie={mandats.parMois.slice(0, moisVisibles).map((m) => m.n)} couleur="#2f6fd0" onClick={() => setOnglet('mandats')} rang={2}
              sous={`${tauxEx} % d’exclusifs${comparer ? `, contre ${tauxExPrec} %` : ''}`} /> : <Indisponible quoi="Le registre des mandats" onReessayer={reessayer} />}
          </div>
        </section>

        {retenir.length ? (
          <section className="pl-tdb-retenir" aria-label="À retenir">
            {retenir.map((r, i) => (
              <div key={r.cle} className="pl-carte pl-tdb-phrase pl-monte" style={{ animationDelay: `${160 + i * 90}ms` }}>
                <span className={`pl-icone is-${r.ton}`} aria-hidden="true"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d={r.icone} /></svg></span>
                <span className="pl-tdb-phrase-texte"><b>{r.titre}</b><span className="pl-mute">{r.sous}</span></span>
              </div>
            ))}
          </section>
        ) : null}

        {enCours && (actions.length || route.length) ? (
          <div className="pl-tdb-deux">
            {actions.length ? (
              <section className="pl-carte pl-bloc pl-tdb-bloc" aria-label="À traiter cette semaine">
                <div className="pl-bloc-tete"><h2>À traiter cette semaine</h2><span className="pl-mute">photo du jour</span></div>
                {actions.map((a, i) => (
                  <button key={a.cle} type="button" className="pl-tdb-action pl-glisse" style={{ animationDelay: `${420 + i * 110}ms` }} onClick={() => setOnglet(a.vers)}>
                    <span className={`pl-etq is-${a.ton}`}>{entier.format(a.n)}</span>
                    <span className="pl-tdb-action-texte"><b>{a.titre}</b><span className="pl-piste is-fine"><span className={`is-${a.ton}`} style={{ width: `${(a.n / maxAction) * 100}%`, animationDelay: `${600 + i * 110}ms` }} /></span></span>
                    <span className="pl-tdb-action-h">{a.h ? <><b className="pl-num">{compact(a.h)}</b><span className="pl-mute">{unite}</span></> : null}</span>
                  </button>
                ))}
              </section>
            ) : null}

            {route.length ? (
              <section className="pl-carte pl-bloc pl-tdb-bloc" aria-label="Ce qui est en route">
                <div className="pl-bloc-tete"><h2>Ce qui est en route</h2><button type="button" className="pl-lien" onClick={() => setOnglet('stock')}>Le stock <span aria-hidden="true">→</span></button></div>
                <span className="pl-tdb-route-tete">
                  <span className="pl-mute">Honoraires des compromis et des offres acceptées en cours</span>
                  <b className="pl-tdb-route-valeur pl-num"><Compteur valeur={engage} format={compact} /> {unite}</b>
                  <span className="pl-mute">Montants saisis, avant les chances d’aboutir.{stock ? ` Le stock en vente porte ${compact(stock.potentiel)} de plus.` : ''}</span>
                </span>
                <span className="pl-tdb-ruban" role="img" aria-label="Compromis, offres acceptées, biens en vente">
                  {route.map((r, i) => <span key={r.cle} style={{ flex: `${Math.max(r.h, 1)} 1 0`, background: r.ton, animationDelay: `${400 + i * 140}ms` }} />)}
                </span>
                <div className="pl-tdb-route-legende">
                  {route.map((r) => (
                    <span key={r.cle}><i style={{ background: r.ton }} /><span><b>{r.libelle}</b><span className="pl-mute">{entier.format(r.n)} {r.quoi}</span></span><b className="pl-num">{compact(r.h)}</b></span>
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        ) : null}

        {top.length ? (
          <section className="pl-carte pl-bloc" aria-label="Les premières agences">
            <div className="pl-bloc-tete"><h2>Les {top.length} premières agences</h2><button type="button" className="pl-lien" onClick={() => setDeplie(true)}>Toutes les agences <span aria-hidden="true">→</span></button></div>
            <div className="pl-defile">
              <div className="pl-tdb-agences">
                {top.map(([cle, a], i) => {
                  const x = comparer ? ecart(a.h, a.hPrec) : null
                  return (
                    <div key={cle} className="pl-tdb-agence pl-glisse" style={{ animationDelay: `${480 + i * 70}ms` }}>
                      <b className="pl-num pl-tdb-rang">{i + 1}</b>
                      <button type="button" className="pl-lien-nom" onClick={() => setAgence(cle)}>{nomAgence(cle)}</button>
                      <span className="pl-tdb-agence-piste">
                        <span style={{ width: `${(a.h / maxTop) * 100}%`, animationDelay: `${520 + i * 80}ms` }} />
                        {comparer && a.hPrec ? <i style={{ left: `${Math.min(100, (a.hPrec / maxTop) * 100)}%` }} title={`${annee - 1} : ${compact(a.hPrec)}`} /> : null}
                      </span>
                      <b className="pl-num pl-droite">{compact(a.h)}</b>
                      <span className="pl-droite">{x ? <span className={`pl-delta is-${x.bon ? 'up' : 'dn'} pl-pop`} style={{ animationDelay: `${1.1 + i * 0.1}s` }}>{x.texte}</span> : null}</span>
                    </div>
                  )
                })}
              </div>
            </div>
            <span className="pl-note">Honoraires {unite} {enCours ? `${annee} à date` : annee}{comparer ? ` · le trait marque ${libelleComparaison}` : ''} · un clic sur une agence filtre tout le pilotage.</span>
          </section>
        ) : null}

        <div className="pl-tdb-plier">
          <button type="button" className="pl-plier" aria-expanded={deplie} onClick={() => setDeplie((x) => !x)}>{deplie ? 'Masquer le détail' : 'Afficher les 12 autres chiffres et toutes les agences'}</button>
        </div>

        {deplie ? <>
          <section className="pl-essentiel" aria-label="L'essentiel">
            <span className="pl-lib">L’essentiel · {enCours ? `${annee} à date` : annee}{comparer ? ` · comparé à ${libelleComparaison}` : ''}</span>
            <div className="pl-grille-kpi is-douze">
              {ventes ? <>
                <Carte libelle={`Honoraires ${unite}`} genre="résultat" valeur={<Compteur valeur={ventes.honoraires} format={compact} />} ecartValeur={comparer ? ecart(ventes.honoraires, ventes.honorairesPrec) : null} detail={comparer ? `contre ${compact(ventes.honorairesPrec)}` : ''} onClick={() => setOnglet('ventes')} />
                <Carte libelle="Actes signés" genre="résultat" valeur={<Compteur valeur={ventes.ventes} format={(x) => entier.format(Math.round(x))} />} ecartValeur={comparer ? ecart(ventes.ventes, ventes.ventesPrec) : null} detail={comparer ? `contre ${ventes.ventesPrec}` : ''} onClick={() => setOnglet('ventes')} />
                <Carte libelle="Honoraires par acte" genre="résultat" valeur={<Compteur valeur={parActe} format={euros} />} ecartValeur={comparer ? ecart(parActe, parActePrec) : null} detail={comparer ? `contre ${euros(parActePrec)}` : `${unite}, en moyenne`} onClick={() => setOnglet('ventes')} />
                <Carte libelle="Prix moyen de vente" genre="résultat" valeur={<Compteur valeur={prixMoyen} format={(x) => `${entier.format(Math.round(x))} €`} />} ecartValeur={comparer ? ecart(prixMoyen, prixMoyenPrec) : null} detail={comparer ? `contre ${entier.format(Math.round(prixMoyenPrec))} €` : 'prix de l’acte'} onClick={() => setOnglet('ventes')} />
                <Carte libelle="Taux d’honoraires" genre="résultat" valeur={<Compteur valeur={taux} format={(x) => `${virgule(x)} %`} />} ecartValeur={comparer && tauxPrec ? { texte: `${taux >= tauxPrec ? '▲ +' : '▼ −'}${virgule(Math.abs(taux - tauxPrec))} pt`, bon: taux >= tauxPrec } : null} detail={`honoraires ${unite} ÷ prix de vente`} onClick={() => setOnglet('ventes')} />
                <Carte libelle="Volume vendu" genre="résultat" valeur={<Compteur valeur={ventes.volume} format={(x) => `${virgule(x / 1e6)} M€`} />} ecartValeur={comparer ? ecart(ventes.volume, ventes.volumePrec) : null} detail={comparer ? `contre ${virgule(ventes.volumePrec / 1e6)} M€` : 'somme des prix de vente'} onClick={() => setOnglet('ventes')} />
              </> : null}
              {mandats ? <>
                <Carte libelle="Mandats rentrés" genre="avancé" valeur={<Compteur valeur={mandats.n} format={(x) => entier.format(Math.round(x))} />} ecartValeur={comparer ? ecart(mandats.n, mandats.nPrec) : null} detail={comparer ? `contre ${mandats.nPrec}` : ''} onClick={() => setOnglet('mandats')} />
                <Carte libelle="Exclusivité" genre="avancé" valeur={<Compteur valeur={tauxEx} format={(x) => `${Math.round(x)} %`} />} ecartValeur={comparer ? ecartPoints(tauxEx, tauxExPrec) : null} detail={comparer ? `contre ${tauxExPrec} %` : `${mandats.exclusifs} exclusifs`} onClick={() => setOnglet('mandats')} />
              </> : null}
              {stock ? <>
                <Carte libelle="Biens en vente" genre="photo du jour" valeur={<Compteur valeur={stock.actifs} format={(x) => entier.format(Math.round(x))} />} detail={`C.A potentiel ${compact(stock.potentiel)}`} onClick={() => setOnglet('stock')} />
                <Carte libelle="Biens engagés" genre="photo du jour" valeur={<Compteur valeur={stock.engages} format={(x) => entier.format(Math.round(x))} />} detail={`${stock.sousOffre} sous offre · ${stock.sousCompromis} sous compromis`} onClick={() => setOnglet('stock')} />
              </> : null}
              {ventes ? <>
                <Carte libelle="Actes déjà datés" genre="à venir" valeur={<Compteur valeur={ventes.actesDates.h} format={compact} />} detail={`${ventes.actesDates.n} compromis, dont ${ventes.actesDates.dIciTroisMois.n} d’ici trois mois`} onClick={() => setOnglet('ventes')} />
                <Carte libelle="De l’offre à l’acte" genre="délai" valeur={delai != null ? <Compteur valeur={delai} format={(x) => `${Math.round(x)} j`} /> : '–'} ecartValeur={comparer && delai != null && delaiPrec ? { texte: `${delai <= delaiPrec ? '▼ −' : '▲ +'}${Math.abs(delai - delaiPrec)} j`, bon: delai <= delaiPrec } : null} detail={comparer && delaiPrec ? `contre ${delaiPrec} j · médiane` : 'médiane des ventes'} onClick={() => setOnglet('ventes')} />
              </> : null}
            </div>
          </section>

          <div className="pl-deux">
            <section className="pl-carte pl-bloc" aria-label="Entrées et sorties par mois">
              <div className="pl-bloc-tete">
                <h2>Ce qui rentre, ce qui se vend</h2>
                <span className="pl-legende"><i style={{ background: '#2f5fa7' }} />Mandats rentrés<i style={{ background: '#c5005f' }} />Ventes actées</span>
              </div>
              <div className="pl-defile">
                <div className="pl-histo" role="img" aria-label={`Mandats rentrés et ventes actées par mois en ${annee}`}>
                  {mois.map((i) => (
                    <div key={i} className="pl-histo-col">
                      <div className="pl-histo-barres">
                        <span style={{ height: `${((mandats?.parMois[i].n ?? 0) / maxFlux) * 100}%`, background: '#2f5fa7' }} title={`${mandats?.parMois[i].n ?? 0} mandats`} />
                        <span style={{ height: `${((ventes?.parMois[i].n ?? 0) / maxFlux) * 100}%`, background: '#c5005f' }} title={`${ventes?.parMois[i].n ?? 0} ventes`} />
                      </div>
                      <span className="pl-histo-lib">{MOIS[i]}<br /><span className="pl-mute pl-num">{mandats?.parMois[i].n ?? '–'} · {ventes?.parMois[i].n ?? '–'}</span></span>
                    </div>
                  ))}
                </div>
              </div>
              <span className="pl-note">Un mandat rentré aujourd’hui fait une vente dans quelques mois : la couleur bleue annonce la rose. Sous les mois : mandats · ventes.</span>
            </section>

            <section className="pl-carte pl-bloc" aria-label="À surveiller">
              <div className="pl-bloc-tete"><h2>À surveiller aussi</h2><span className="pl-mute">photo du jour</span></div>
              {stock ? <>
                <Surveiller ton="ambre" titre="Mandats qui échoient sous 30 jours" sous="à renouveler ou à clôturer" n={stock.echoient30} onClick={() => setOnglet('stock')} />
                <Surveiller ton="rouge" titre="Biens diffusables sans aucun portail" sous="aucune diffusion réussie" n={stock.sansPortail} onClick={() => setOnglet('stock')} />
                <Surveiller ton="gris" titre="Biens en vente depuis plus de 6 mois" sous={`${compact(stock.hBloque6Mois)} d’honoraires`} n={stock.plusDe6Mois} onClick={() => setOnglet('stock')} />
              </> : null}
              {!enCours && stock ? <Surveiller ton="rouge" titre="Mandats échus, bien toujours en vente" sous="date de fin passée" n={stock.echus} onClick={() => setOnglet('stock')} /> : null}
              {!enCours && signatures ? <Surveiller ton="bleu" titre="Signatures de mandat en attente" sous="envoyées, pas encore signées" n={signatures.enAttente} onClick={() => setOnglet('mandats')} /> : null}
            </section>
          </div>

          <section className="pl-carte pl-bloc is-table" aria-label="Les agences">
            <div className="pl-bloc-tete"><h2>Les agences</h2><span className="pl-mute">{comparer ? `écart avec ${libelleComparaison} · ` : ''}un clic filtre tout le pilotage sur l’agence</span></div>
            <div className="pl-defile">
              <table className="pl-table">
                <thead><tr><th scope="col">Agence</th><th scope="col">Honoraires {unite}</th>{comparer ? <th scope="col">Écart</th> : null}<th scope="col">Ventes</th><th scope="col">Mandats rentrés</th>{comparer ? <th scope="col">Écart</th> : null}<th scope="col">Exclusivité</th><th scope="col">En vente</th><th scope="col">C.A potentiel</th></tr></thead>
                <tbody>
                  {lignes.map((l) => (
                    <tr key={l.cle}>
                      <td><button type="button" className="pl-lien-nom" onClick={() => setAgence(l.cle)}>{nomAgence(l.cle)}</button></td>
                      <td className="pl-num pl-fort"><span className="pl-cellule-barre"><Barre part={((l.v?.h ?? 0) / maxH) * 100} ton="#c5005f" fine />{euros(l.v?.h ?? 0)}</span></td>
                      {comparer ? <td className="pl-num"><Ecart valeur={ecart(l.v?.h ?? 0, l.v?.hPrec ?? 0)} /></td> : null}
                      <td className="pl-num">{l.v?.ventes ?? 0}</td>
                      <td className="pl-num">{l.m?.n ?? 0}</td>
                      {comparer ? <td className="pl-num"><Ecart valeur={ecart(l.m?.n ?? 0, l.m?.nPrec ?? 0)} /></td> : null}
                      <td className="pl-num">{l.m?.n ? `${pourcent(l.m.ex, l.m.n)} %` : '–'}</td>
                      <td className="pl-num">{l.s?.actifs ?? 0}</td>
                      <td className="pl-num">{l.s ? compact(l.s.h) : '–'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </> : null}
      </>
    )
  }

  // ───────────────────────── VENTES ─────────────────────────
  function Ventes() {
    if (!ventes) return <Indisponible quoi="Le registre des ventes" onReessayer={reessayer} />
    const futurs = (i: number) => (enCours && i >= moisVisibles ? ventes.actesDates.parMois.get(`${annee}-${String(i + 1).padStart(2, '0')}`) ?? null : null)
    const max = Math.max(1, ...ventes.parMois.map((m) => m.h), ...(comparer ? ventes.parMoisPrec.map((m) => m.h) : []), ...Array.from({ length: 12 }, (_, i) => futurs(i)?.h ?? 0))
    const negos = tousNegos ? ventes.negos : ventes.negos.slice(0, 10)
    const maxNego = Math.max(1, ...ventes.negos.map((n) => Math.max(n.part, comparer ? n.partPrec : 0)))
    const agences = [...ventes.agences.entries()].filter(([cle]) => cle).sort((a, b) => b[1].h - a[1].h)
    const maxAg = Math.max(1, ...agences.map(([, a]) => Math.max(a.h, comparer ? a.hPrec : 0)))
    return (
      <>
        <div className="pl-grille-kpi">
          <Carte libelle={`Honoraires ${unite}${enCours ? ' à date' : ''}`} valeur={euros(ventes.honoraires)} ecartValeur={comparer ? ecart(ventes.honoraires, ventes.honorairesPrec) : null} detail={comparer ? `contre ${euros(ventes.honorairesPrec)}` : 'entrée + sortie'} />
          <Carte libelle="Ventes actées" valeur={entier.format(ventes.ventes)} ecartValeur={comparer ? ecart(ventes.ventes, ventes.ventesPrec) : null} detail={`${(ventes.volume / 1e6).toFixed(1).replace('.', ',')} M€ de volume`} />
          <Carte libelle="Actes déjà datés" valeur={compact(ventes.actesDates.h)} detail={`${ventes.actesDates.n} compromis en cours dont l’acte est daté`} />
          <Carte libelle="Délais médians" valeur={`${ventes.delaiOffreCompromis ?? '–'} j · ${ventes.delaiCompromisActe ?? '–'} j`} detail={comparer ? `offre → compromis · compromis → acte (${annee - 1} : ${ventes.delaisPrec[0] ?? '–'} j · ${ventes.delaisPrec[1] ?? '–'} j)` : 'offre → compromis · compromis → acte'} />
        </div>

        <section className="pl-carte pl-bloc" aria-label="Honoraires par mois">
          <div className="pl-bloc-tete">
            <h2>Honoraires {unite} par mois · {annee}</h2>
            <span className="pl-legende"><i style={{ background: '#c5005f' }} />Ventes actées{comparer ? <><i style={{ background: '#c9ced0' }} />{annee - 1}</> : null}{enCours ? <><i className="is-hachure" />Actes déjà datés</> : null}</span>
          </div>
          <div className="pl-defile">
            <div className="pl-histo is-haut" role="img" aria-label={`Honoraires mensuels ${annee}`}>
              {MOIS.map((nom, i) => {
                const f = futurs(i)
                const v = i < moisVisibles ? ventes.parMois[i] : null
                const valeur = v ? v.h : f ? f.h : 0
                return (
                  <div key={nom} className="pl-histo-col">
                    <span className="pl-histo-val pl-num">{valeur ? compact(valeur) : ''}</span>
                    <div className="pl-histo-barres">
                      {comparer ? <span style={{ height: `${(ventes.parMoisPrec[i].h / max) * 100}%`, background: '#c9ced0' }} title={`${annee - 1} : ${euros(ventes.parMoisPrec[i].h)}`} /> : null}
                      <span className={f ? 'is-hachure' : ''} style={{ height: `${(valeur / max) * 100}%`, ...(f ? {} : { background: '#c5005f' }) }} />
                    </div>
                    <span className="pl-histo-lib">{nom}<br /><span className="pl-mute">{v ? `${v.n} ventes` : f ? `${f.n} actes datés` : ''}</span></span>
                  </div>
                )
              })}
            </div>
          </div>
          <span className="pl-note">Mois d’une vente = date de l’acte.{enCours ? ' Hachuré : compromis dont l’acte est déjà daté, un plancher, pas une promesse.' : ''}</span>
        </section>

        <div className="pl-deux">
          <section className="pl-carte pl-bloc" aria-label="Négociateurs">
            <div className="pl-bloc-tete"><h2>Négociateurs · {annee}</h2><span className="pl-mute">part des honoraires · dossiers</span></div>
            <div className="pl-rangs">
              {negos.map((n) => (
                <div key={n.id} className="pl-rang">
                  <span className="pl-rang-nom"><b>{n.nom}</b><span className="pl-mute">{n.dossiers} dossier{n.dossiers > 1 ? 's' : ''}</span></span>
                  <span className="pl-rang-barres"><Barre part={(n.part / maxNego) * 100} ton="#c5005f" />{comparer ? <Barre part={(n.partPrec / maxNego) * 100} ton="#b4babc" fine /> : null}</span>
                  <b className="pl-num pl-droite">{euros(n.part)}</b>
                  {comparer ? <span className="pl-droite"><Ecart valeur={n.partPrec ? ecart(n.part, n.partPrec) : null} /></span> : null}
                </div>
              ))}
            </div>
            <div className="pl-bloc-pied">
              {ventes.negos.length > 10 ? <button type="button" className="pl-bouton" onClick={() => setTousNegos((x) => !x)}>{tousNegos ? 'Voir les 10 premiers' : `Voir les ${ventes.negos.length} personnes`}</button> : <span />}
              <span className="pl-note">Part = honoraires × pourcentage de la répartition. {euros(ventes.attribue)} attribués sur {euros(ventes.honoraires)} ({pourcent(ventes.attribue, ventes.honoraires)} %).</span>
            </div>
          </section>

          <section className="pl-carte pl-bloc" aria-label="Agences">
            <div className="pl-bloc-tete"><h2>Agences · {annee}</h2><span className="pl-mute">honoraires des ventes · ventes</span></div>
            <div className="pl-rangs">
              {agences.map(([cle, a]) => (
                <div key={cle} className="pl-rang">
                  <span className="pl-rang-nom"><button type="button" className="pl-lien-nom" onClick={() => setAgence(cle)}>{nomAgence(cle)}</button><span className="pl-mute">{a.ventes} vente{a.ventes > 1 ? 's' : ''}</span></span>
                  <span className="pl-rang-barres"><Barre part={(a.h / maxAg) * 100} ton="#1f2121" />{comparer ? <Barre part={(a.hPrec / maxAg) * 100} ton="#b4babc" fine /> : null}</span>
                  <b className="pl-num pl-droite">{euros(a.h)}</b>
                  {comparer ? <span className="pl-droite"><Ecart valeur={ecart(a.h, a.hPrec)} /></span> : null}
                </div>
              ))}
            </div>
            <span className="pl-note">Agence du dossier, la même que dans le registre des transactions.</span>
          </section>
        </div>
      </>
    )
  }

  // ───────────────────────── MANDATS ─────────────────────────
  function Mandats() {
    if (!mandats) return <Indisponible quoi="Le registre des mandats" onReessayer={reessayer} />
    const tauxEx = pourcent(mandats.exclusifs, mandats.n)
    const tauxExPrec = pourcent(mandats.exclusifsPrec, mandats.nPrec)
    const avecSemi = pourcent(mandats.exclusifs + mandats.semi, mandats.n)
    const avecSemiPrec = pourcent(mandats.exclusifsPrec + mandats.semiPrec, mandats.nPrec)
    const max = Math.max(1, ...mandats.parMois.map((m) => m.n), ...(comparer ? mandats.parMoisPrec : []))
    const maxType = Math.max(1, ...mandats.types.map((t) => Math.max(t.n, comparer ? t.nPrec : 0)))
    const agences = [...mandats.agences.entries()].filter(([cle]) => cle).sort((a, b) => b[1].n - a[1].n)
    const negos = tousNegos ? mandats.negos : mandats.negos.slice(0, 14)
    const maxSig = Math.max(1, ...(signatures?.parMois ?? [0]))
    const ligne = (cle: string, nom: ReactNode, x: { n: number; nPrec: number; ex: number }) => {
      const part = pourcent(x.ex, x.n)
      return (
        <tr key={cle}>
          <td>{nom}</td>
          <td className="pl-num pl-fort">{x.n}</td>
          {comparer ? <td className="pl-num"><Ecart valeur={x.nPrec ? ecart(x.n, x.nPrec) : null} /></td> : null}
          <td className="pl-num"><span className="pl-cellule-barre"><span className="pl-piste is-fine is-repere"><span style={{ width: `${part}%`, background: part >= tauxEx ? '#2f5fa7' : '#a9bfe0' }} /><i style={{ left: `${tauxEx}%` }} /></span>{part} %</span></td>
        </tr>
      )
    }
    return (
      <>
        <div className="pl-grille-kpi">
          <Carte libelle="Mandats rentrés" genre="avancé" valeur={entier.format(mandats.n)} ecartValeur={comparer ? ecart(mandats.n, mandats.nPrec) : null} detail={comparer ? `contre ${mandats.nPrec} · ${libelleComparaison}` : ''} />
          <Carte libelle="Exclusifs" genre="avancé" valeur={`${mandats.exclusifs} · ${tauxEx} %`} ecartValeur={comparer ? ecartPoints(tauxEx, tauxExPrec) : null} detail={comparer ? `contre ${mandats.exclusifsPrec} · ${tauxExPrec} % · avec les semi-exclusifs : ${avecSemi} % contre ${avecSemiPrec} %` : `avec les semi-exclusifs : ${avecSemi} %`} />
          <Carte libelle="Signés électroniquement" genre="activité" valeur={signatures ? entier.format(signatures.signes) : '–'} detail={signatures ? `en ${annee} · ${signatures.enAttente} en attente de signature` : 'n’a pas pu être lu'} />
          <Carte libelle="Échéances" genre="photo du jour" valeur={stock ? `${stock.echus} · ${stock.echoient30}` : '–'} detail="mandats échus encore en vente · échéance sous 30 jours" />
        </div>

        <div className="pl-deux">
          <section className="pl-carte pl-bloc" aria-label="Mandats rentrés par mois">
            <div className="pl-bloc-tete">
              <h2>Mandats rentrés par mois · {annee}</h2>
              <span className="pl-legende"><i style={{ background: '#2f5fa7' }} />Exclusifs<i style={{ background: '#a9bfe0' }} />Autres{comparer ? <><i className="is-trait" />{annee - 1}</> : null}</span>
            </div>
            <div className="pl-defile">
              <div className="pl-histo" role="img" aria-label="Mandats rentrés par mois, exclusifs et autres">
                {MOIS.slice(0, moisVisibles).map((nom, i) => (
                  <div key={nom} className="pl-histo-col">
                    <span className="pl-histo-val pl-num">{mandats.parMois[i].n}</span>
                    <div className="pl-histo-barres is-empile">
                      <span className="pl-empile" style={{ height: `${(mandats.parMois[i].n / max) * 100}%` }}>
                        <span style={{ flex: mandats.parMois[i].n - mandats.parMois[i].ex, background: '#a9bfe0' }} />
                        <span style={{ flex: mandats.parMois[i].ex, background: '#2f5fa7' }} />
                      </span>
                      {comparer ? <i className="pl-repere-prec" style={{ bottom: `${(mandats.parMoisPrec[i] / max) * 100}%` }} title={`${mandats.parMoisPrec[i]} en ${annee - 1}`} /> : null}
                    </div>
                    <span className="pl-histo-lib">{nom}<br /><span className="pl-mute">{pourcent(mandats.parMois[i].ex, mandats.parMois[i].n)} %</span></span>
                  </div>
                ))}
              </div>
            </div>
            <span className="pl-note">Sous chaque mois : part d’exclusifs.{comparer ? ` Le trait gris marque ${annee - 1}, même mois.` : ''}</span>
          </section>

          <section className="pl-carte pl-bloc" aria-label="Types de mandat">
            <div className="pl-bloc-tete"><h2>Par type de mandat</h2></div>
            {mandats.types.map((t) => (
              <div key={t.cle} className="pl-type">
                <span className="pl-type-tete"><b>{t.libelle}</b><span className="pl-num"><b>{t.n}</b>{comparer ? <> <span className="pl-mute">contre {t.nPrec}</span> <Ecart valeur={ecart(t.n, t.nPrec)} /></> : null}</span></span>
                <Barre part={(t.n / maxType) * 100} ton={t.cle === 'EXCLUSIF' ? '#2f5fa7' : t.cle === 'ACCORD' ? '#5b4a8b' : '#a9bfe0'} />
                {comparer ? <Barre part={(t.nPrec / maxType) * 100} ton="#b4babc" fine /> : null}
                <span className="pl-mute pl-petit">{t.prixMedian ? `prix médian au mandat ${entier.format(t.prixMedian)} €` : ''}</span>
              </div>
            ))}
            {signatures ? (
              <div className="pl-signatures">
                <span className="pl-type-tete"><b>Signés électroniquement · {annee}</b><span className="pl-mute">{signatures.signes} · {signatures.enAttente} en attente</span></span>
                <div className="pl-mini-histo" role="img" aria-label="Mandats signés électroniquement par mois">
                  {MOIS.slice(0, moisVisibles).map((nom, i) => (
                    <span key={nom} className="pl-mini-col"><span style={{ height: `${(signatures.parMois[i] / maxSig) * 100}%` }} title={`${signatures.parMois[i]} en ${nom}`} /><i>{nom.slice(0, 3)}</i></span>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        </div>

        <div className="pl-deux">
          <section className="pl-carte pl-bloc is-table" aria-label="Mandats par agence">
            <div className="pl-bloc-tete"><h2>Par agence</h2><span className="pl-mute">le repère marque la moyenne du réseau ({tauxEx} %)</span></div>
            <div className="pl-defile">
              <table className="pl-table">
                <thead><tr><th scope="col">Agence</th><th scope="col">{annee}</th>{comparer ? <th scope="col">Écart</th> : null}<th scope="col">Exclusivité</th></tr></thead>
                <tbody>{agences.map(([cle, a]) => ligne(cle, <button type="button" className="pl-lien-nom" onClick={() => setAgence(cle)}>{nomAgence(cle)}</button>, a))}</tbody>
              </table>
            </div>
          </section>
          <section className="pl-carte pl-bloc is-table" aria-label="Mandats par négociateur">
            <div className="pl-bloc-tete"><h2>Par négociateur</h2><span className="pl-mute">{mandats.nbNegos} personnes ont rentré un mandat</span></div>
            <div className="pl-defile">
              <table className="pl-table">
                <thead><tr><th scope="col">Négociateur</th><th scope="col">{annee}</th>{comparer ? <th scope="col">Écart</th> : null}<th scope="col">Exclusivité</th></tr></thead>
                <tbody>{negos.map((n) => ligne(n.nom, <b>{n.nom}</b>, n))}</tbody>
              </table>
            </div>
            {mandats.negos.length > 14 ? <div className="pl-bloc-pied"><button type="button" className="pl-bouton" onClick={() => setTousNegos((x) => !x)}>{tousNegos ? 'Voir les 14 premiers' : `Voir les ${mandats.negos.length}`}</button></div> : null}
          </section>
        </div>
      </>
    )
  }

  // ───────────────────────── STOCK ─────────────────────────
  function Stock() {
    if (!stock) return <Indisponible quoi="Le stock" onReessayer={reessayer} />
    const rythmeMensuel = ventes && ventes.honoraires ? ventes.honoraires / (enCours ? Math.max(1, Number(aujourdhui().slice(5, 7)) - 1 + Number(aujourdhui().slice(8, 10)) / 30) : 12) : 0
    const mois = rythmeMensuel ? Math.round(stock.potentiel / rythmeMensuel) : null
    const maxTranche = Math.max(1, ...stock.tranches.map((t) => t.h))
    const totalTypes = Math.max(1, stock.types.reduce((s, t) => s + t.h, 0))
    const agences = [...stock.agences.entries()].filter(([cle]) => cle).sort((a, b) => b[1].h - a[1].h)
    const maxAg = Math.max(1, ...agences.map(([, a]) => a.h))
    const rouge = (n: number, total: number) => (n * 3 > total ? 'pl-alerte' : '')
    return (
      <>
        <section className="pl-carte pl-heros" aria-label="C.A potentiel du stock">
          <div className="pl-heros-gauche">
            <span className="pl-lib is-marque">C.A potentiel du stock · honoraires {unite}</span>
            <b className="pl-heros-valeur pl-num">{compact(stock.potentiel)}</b>
            <span>sur les <b>{stock.avecHonoraires} biens</b> en vente dont les honoraires sont saisis</span>
            {stock.sansHonoraires ? (
              <span className="pl-mute">≈ <b className="pl-encre">{compact(stock.estime)}</b> de plus estimés pour les <b className="pl-encre">{stock.sansHonoraires} biens sans honoraires saisis</b> (au taux médian du réseau, {stock.tauxMedian != null ? `${(stock.tauxMedian * 100).toFixed(1).replace('.', ',')} %` : '–'} du prix)</span>
            ) : null}
          </div>
          <div className="pl-heros-droite">
            {mois ? <span className="pl-ligne-ecartee"><span>Au rythme des ventes {annee}</span><b className="pl-num">≈ {mois} mois d’honoraires</b></span> : null}
            <span className="pl-ruban" role="img" aria-label="C.A potentiel par ancienneté">
              {stock.tranches.map((t) => <span key={t.libelle} style={{ width: `${(t.h / Math.max(1, stock.potentiel)) * 100}%`, background: t.ton }} title={`${t.libelle} : ${compact(t.h)}`} />)}
            </span>
            <span className="pl-note">De gauche à droite : biens de moins de 3 mois → plus d’un an, puis sans date de mandat.</span>
            <span className="pl-puces">
              <span className="pl-puce is-ambre">{compact(stock.hBloque6Mois)} sur des biens de plus de 6 mois</span>
              <span className="pl-puce is-rouge">{compact(stock.hNonDiffusables)} sur des biens non diffusables</span>
            </span>
          </div>
        </section>

        <div className="pl-grille-kpi">
          <Carte libelle="Sous offre ou compromis" valeur={compact(stock.potentielEngages)} detail={`${stock.engages} biens engagés (${stock.sousOffre} sous offre, ${stock.sousCompromis} sous compromis)`} />
          <Carte libelle="Honoraires médians par bien" valeur={stock.honorairesMedian ? euros(stock.honorairesMedian) : '–'} detail={stock.tauxMedian != null ? `${(stock.tauxMedian * 100).toFixed(1).replace('.', ',')} % du prix affiché en médiane` : ''} />
          <Carte libelle="Biens en vente" valeur={entier.format(stock.actifs)} detail={`${stock.plusDe6Mois} depuis plus de 6 mois · âge médian ${stock.ageMedian ?? '–'} jours`} />
          <Carte libelle="Vraies baisses de prix" valeur={entier.format(stock.baisses)} detail={stock.baisseMediane != null ? `baisse médiane ${(stock.baisseMediane * 100).toFixed(1).replace('.', ',').replace('-', '−')} % · détectées depuis le 20 juin 2026` : ''} />
        </div>

        <div className="pl-trois">
          <section className="pl-carte pl-bloc" aria-label="C.A potentiel par ancienneté">
            <div className="pl-bloc-tete"><h2>C.A potentiel par ancienneté</h2><span className="pl-mute">depuis la date du mandat</span></div>
            {stock.tranches.map((t) => (
              <div key={t.libelle} className="pl-tranche">
                <span><b>{t.libelle}</b><span className="pl-mute">{t.biens} biens · {t.avec} avec honoraires</span></span>
                <Barre part={(t.h / maxTranche) * 100} ton={t.ton} />
                <b className="pl-num pl-droite">{compact(t.h)}</b>
              </div>
            ))}
          </section>
          <section className="pl-carte pl-bloc" aria-label="C.A potentiel par type de mandat">
            <div className="pl-bloc-tete"><h2>Par type de mandat</h2></div>
            <span className="pl-ruban is-epais" role="img" aria-label="C.A potentiel par type de mandat">
              {stock.types.map((t) => <span key={t.libelle} style={{ width: `${(t.h / totalTypes) * 100}%`, background: t.ton }} title={`${t.libelle} : ${compact(t.h)}`} />)}
            </span>
            {stock.types.map((t) => (
              <span key={t.libelle} className="pl-legende-ligne"><i style={{ background: t.ton }} /><span>{t.libelle} <span className="pl-mute">· {t.biens} biens</span></span><b className="pl-num">{compact(t.h)}</b><span className="pl-mute pl-num">{pourcent(t.h, totalTypes)} %</span></span>
            ))}
          </section>
          <section className="pl-carte pl-bloc" aria-label="Diffusion">
            <div className="pl-bloc-tete"><h2>Diffusion</h2><span className="pl-mute">{portails ? `sur ${portails.diffusables} biens diffusables` : ''}</span></div>
            {portails ? portails.portails.slice(0, 6).map((p) => (
              <div key={p.cle} className="pl-tranche is-court">
                <b>{p.libelle}</b>
                <Barre part={(p.ok / Math.max(1, portails.diffusables)) * 100} ton="#2f5fa7" />
                <b className="pl-num pl-droite">{p.ok}{p.erreur ? <span className="pl-alerte"> · {p.erreur} en erreur</span> : null}</b>
              </div>
            )) : <span className="pl-mute">La diffusion n’a pas pu être lue.</span>}
            <span className="pl-note"><b>{stock.nonDiffusables}</b> biens non diffusables, soit <b>{compact(stock.hNonDiffusables)}</b> d’honoraires invisibles des portails · <b>{stock.sansPortail}</b> diffusables sans aucun portail en ligne.</span>
          </section>
        </div>

        <section className="pl-carte pl-bloc is-table" aria-label="Le C.A potentiel de chaque agence">
          <div className="pl-bloc-tete"><h2>Le C.A potentiel de chaque agence</h2><span className="pl-mute">en rouge : plus d’un tiers des biens de l’agence</span></div>
          <div className="pl-defile">
            <table className="pl-table">
              <thead><tr><th scope="col">Agence</th><th scope="col">C.A potentiel {unite}</th><th scope="col">En vente</th><th scope="col">Sans honoraires</th><th scope="col">Engagés</th><th scope="col">Âge médian</th><th scope="col">Plus de 6 mois</th><th scope="col">Non diffusables</th><th scope="col">Mandat échu</th></tr></thead>
              <tbody>
                {agences.map(([cle, a]) => {
                  const ageMed = a.ages.length ? Math.round([...a.ages].sort((x, y) => x - y)[Math.floor(a.ages.length / 2)]) : null
                  return (
                    <tr key={cle}>
                      <td><button type="button" className="pl-lien-nom" onClick={() => setAgence(cle)}>{nomAgence(cle)}</button></td>
                      <td className="pl-num pl-fort"><span className="pl-cellule-barre"><Barre part={(a.h / maxAg) * 100} ton="#c5005f" fine />{compact(a.h)}</span></td>
                      <td className="pl-num">{a.actifs}</td>
                      <td className={`pl-num ${rouge(a.sans, a.actifs)}`}>{a.sans}</td>
                      <td className="pl-num">{a.engages}</td>
                      <td className="pl-num">{ageMed != null ? `${ageMed} j` : '–'}</td>
                      <td className={`pl-num ${rouge(a.vieux, a.actifs)}`}>{a.vieux}</td>
                      <td className={`pl-num ${rouge(a.nonDif, a.actifs)}`}>{a.nonDif}</td>
                      <td className={`pl-num ${a.echus >= 5 ? 'pl-alerte' : ''}`}>{a.echus}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <span className="pl-note">C.A potentiel = honoraires saisis sur les biens en vente. Une agence avec beaucoup de biens sans honoraires saisis a un C.A potentiel sous-estimé.</span>
        </section>
      </>
    )
  }
}

// Une ligne « à surveiller » de la vue d'ensemble : un clic ouvre l'onglet qui détaille.
function Surveiller({ ton, titre, sous, n, onClick }: { ton: 'rouge' | 'ambre' | 'bleu' | 'gris'; titre: string; sous: string; n: number; onClick: () => void }) {
  return (
    <button type="button" className="pl-surveiller" onClick={onClick}>
      <span className={`pl-pastille is-${ton}`} aria-hidden="true" />
      <span className="pl-surveiller-texte"><b>{titre}</b><span className="pl-mute">{sous}</span></span>
      <b className="pl-num pl-surveiller-n">{entier.format(n)}</b>
    </button>
  )
}
