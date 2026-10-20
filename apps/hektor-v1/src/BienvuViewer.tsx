// bienvu — la visionneuse d'image : toutes les photos du bien, plein écran.
// Rendue seulement quand l'interrupteur est allumé (App.tsx garde l'ancienne fenêtre sinon).
//
// Clavier : ← → changer de photo · + − 0 zoom · F plein écran · Échap fermer.
// Souris  : molette ou double clic = zoom centré sur le curseur · glisser = déplacer.
// Doigt   : balayage gauche/droite = photo suivante/précédente · pincement = zoom · double toucher = zoom ·
//           glisser vers le bas = fermer · toucher = montrer ou cacher les barres.
// Les barres s'effacent seules après quelques secondes d'immobilité, la photo reste seule à l'écran.
import { useCallback, useEffect, useRef, useState } from 'react'
import type { PointerEvent as ReactPointerEvent } from 'react'
import './bienvu-viewer.css'

export type ViewerItem = {
  url: string
  thumb?: string | null
  legend?: string | null
  masquee?: boolean
}

const ZOOM_MIN = 1
const ZOOM_MAX = 5
const ZOOM_PAS = 0.5
const CALME_MS = 2800

const ICONES = {
  gauche: <path d="M15 6l-6 6 6 6" />,
  droite: <path d="M9 6l6 6-6 6" />,
  moins: <path d="M5 12h14" />,
  plus: <path d="M12 5v14M5 12h14" />,
  ajuster: <path d="M4 9V5h4M20 9V5h-4M4 15v4h4M20 15v4h-4" />,
  plein: <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" />,
  reduire: <path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5" />,
  original: <><path d="M14 4h6v6" /><path d="M20 4l-9 9" /><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></>,
  fermer: <path d="M6 6l12 12M18 6L6 18" />,
}

function Icone(props: { nom: keyof typeof ICONES }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICONES[props.nom]}
    </svg>
  )
}

type Geste = { x: number; y: number; t: number; px: number; py: number; bouge: boolean; fond: boolean; touch: boolean }

export function BienvuViewer(props: {
  items: ViewerItem[]
  index: number
  titre: string
  onIndex: (index: number) => void
  onClose: () => void
}) {
  const { items, index, titre, onIndex, onClose } = props
  const total = items.length
  const courant = items[index] ?? items[0]
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [charge, setCharge] = useState(false)
  const [erreur, setErreur] = useState(false)
  const [dims, setDims] = useState<string | null>(null)
  const [calme, setCalme] = useState(false)
  const [plein, setPlein] = useState(false)
  const [glisse, setGlisse] = useState(0) // glissement vers le bas pour fermer (px)
  const racine = useRef<HTMLDivElement | null>(null)
  const scene = useRef<HTMLDivElement | null>(null)
  const image = useRef<HTMLImageElement | null>(null)
  const bandeau = useRef<HTMLDivElement | null>(null)
  const geste = useRef<Geste | null>(null)
  const pointeurs = useRef(new Map<number, { x: number; y: number }>())
  const pincement = useRef<{ dist: number; zoom: number } | null>(null)
  const minuterie = useRef<number | null>(null)
  const survol = useRef(false)

  // position, zoom et décalage courants tenus ici aussi : deux événements rapprochés lisent la valeur à jour
  const indexRef = useRef(index)
  const zoomRef = useRef(1)
  const panRef = useRef({ x: 0, y: 0 })
  indexRef.current = index
  zoomRef.current = zoom
  panRef.current = pan

  const allerA = useCallback((cible: number) => {
    if (total < 2) return
    const suivant = ((cible % total) + total) % total
    indexRef.current = suivant
    onIndex(suivant)
  }, [onIndex, total])
  const aller = useCallback((delta: number) => allerA(indexRef.current + delta), [allerA])

  // --- barres : visibles au mouvement, effacées après un moment d'immobilité
  const reveiller = useCallback(() => {
    setCalme(false)
    if (minuterie.current) window.clearTimeout(minuterie.current)
    minuterie.current = window.setTimeout(() => { if (!survol.current) setCalme(true) }, CALME_MS)
  }, [])
  useEffect(() => {
    reveiller()
    return () => { if (minuterie.current) window.clearTimeout(minuterie.current) }
  }, [reveiller])

  // une nouvelle photo repart à zéro
  useEffect(() => {
    setZoom(1); zoomRef.current = 1
    setPan({ x: 0, y: 0 }); panRef.current = { x: 0, y: 0 }
    setCharge(false); setErreur(false); setDims(null); setGlisse(0)
  }, [courant?.url])

  // les deux suivantes et la précédente sont chargées d'avance
  useEffect(() => {
    if (total < 2) return
    for (const voisin of [items[(index + 1) % total], items[(index + 2) % total], items[(index - 1 + total) % total]]) {
      if (voisin?.url) { const pre = new Image(); pre.src = voisin.url }
    }
  }, [index, items, total])

  useEffect(() => {
    bandeau.current?.querySelector<HTMLElement>('[aria-current="true"]')?.scrollIntoView({ block: 'nearest', inline: 'center' })
  }, [index])

  // le focus entre dans la fenêtre et revient où il était ; la page derrière ne défile plus
  useEffect(() => {
    const avant = document.activeElement as HTMLElement | null
    const html = document.documentElement
    const overflow = html.style.overflow
    html.style.overflow = 'hidden'
    racine.current?.focus()
    const surPlein = () => setPlein(Boolean(document.fullscreenElement))
    document.addEventListener('fullscreenchange', surPlein)
    return () => {
      html.style.overflow = overflow
      document.removeEventListener('fullscreenchange', surPlein)
      if (document.fullscreenElement) void document.exitFullscreen?.().catch(() => undefined)
      avant?.focus?.()
    }
  }, [])

  const basculerPlein = useCallback(() => {
    if (document.fullscreenElement) void document.exitFullscreen?.().catch(() => undefined)
    else void racine.current?.requestFullscreen?.().catch(() => undefined)
  }, [])

  // décalage maximal : on ne perd jamais la photo hors de l'écran
  const borne = useCallback((x: number, y: number, z: number) => {
    const s = scene.current, im = image.current
    if (!s || !im || z <= 1) return { x: 0, y: 0 }
    const mx = Math.max(0, (im.offsetWidth * z - s.clientWidth) / 2) + 40
    const my = Math.max(0, (im.offsetHeight * z - s.clientHeight) / 2) + 40
    return { x: Math.max(-mx, Math.min(mx, x)), y: Math.max(-my, Math.min(my, y)) }
  }, [])

  // zoom autour d'un point de l'écran (le curseur, le milieu des deux doigts) : ce point reste sous le doigt
  const zoomerEn = useCallback((cible: number, cx?: number, cy?: number) => {
    const z = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, cible))
    const s = scene.current
    let p = panRef.current
    if (s && cx !== undefined && cy !== undefined && z > 1) {
      const r = s.getBoundingClientRect()
      const px = cx - (r.left + r.width / 2), py = cy - (r.top + r.height / 2)
      const k = z / zoomRef.current
      p = { x: px - (px - p.x) * k, y: py - (py - p.y) * k }
    }
    p = z <= 1 ? { x: 0, y: 0 } : borne(p.x, p.y, z)
    zoomRef.current = z; panRef.current = p
    setZoom(z); setPan(p)
  }, [borne])

  // molette : zoom centré sur le curseur (écouteur natif, pour pouvoir bloquer le défilement de la page)
  useEffect(() => {
    const s = scene.current
    if (!s) return
    function molette(e: WheelEvent) {
      e.preventDefault()
      zoomerEn(zoomRef.current * (e.deltaY < 0 ? 1.18 : 1 / 1.18), e.clientX, e.clientY)
      reveiller()
    }
    s.addEventListener('wheel', molette, { passive: false })
    return () => s.removeEventListener('wheel', molette)
  }, [reveiller, zoomerEn])

  useEffect(() => {
    function touche(e: KeyboardEvent) {
      reveiller()
      if (e.key === 'Escape') { if (document.fullscreenElement) return; e.preventDefault(); onClose() }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); aller(-1) }
      else if (e.key === 'ArrowRight') { e.preventDefault(); aller(1) }
      else if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomerEn(zoomRef.current + ZOOM_PAS) }
      else if (e.key === '-') { e.preventDefault(); zoomerEn(zoomRef.current - ZOOM_PAS) }
      else if (e.key === '0') { e.preventDefault(); zoomerEn(1) }
      else if (e.key === 'f' || e.key === 'F') { e.preventDefault(); basculerPlein() }
      else if (e.key === 'Tab') {
        // le focus tourne dans la fenêtre au lieu de partir dans la page derrière
        const cibles = racine.current ? [...racine.current.querySelectorAll<HTMLElement>('button:not([disabled]), a[href]')] : []
        if (!cibles.length) return
        const premier = cibles[0], dernier = cibles[cibles.length - 1]
        if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier.focus() }
        else if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier.focus() }
      }
    }
    window.addEventListener('keydown', touche)
    return () => window.removeEventListener('keydown', touche)
  }, [aller, basculerPlein, onClose, reveiller, zoomerEn])

  // --- souris et doigts
  function debut(e: ReactPointerEvent<HTMLDivElement>) {
    if ((e.target as HTMLElement).closest('button, a')) return
    pointeurs.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    try { (e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId) } catch { /* pointeur déjà relâché : on continue sans capture */ }
    if (pointeurs.current.size === 2) {
      const [a, b] = [...pointeurs.current.values()]
      pincement.current = { dist: Math.hypot(a.x - b.x, a.y - b.y) || 1, zoom: zoomRef.current }
      geste.current = null
      return
    }
    geste.current = { x: e.clientX, y: e.clientY, t: Date.now(), px: panRef.current.x, py: panRef.current.y, bouge: false, fond: e.target === e.currentTarget, touch: e.pointerType === 'touch' }
  }
  function deplace(e: ReactPointerEvent<HTMLDivElement>) {
    reveiller()
    if (pointeurs.current.has(e.pointerId)) pointeurs.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    if (pincement.current && pointeurs.current.size === 2) {
      const [a, b] = [...pointeurs.current.values()]
      const d = Math.hypot(a.x - b.x, a.y - b.y) || 1
      zoomerEn(pincement.current.zoom * (d / pincement.current.dist), (a.x + b.x) / 2, (a.y + b.y) / 2)
      return
    }
    const g = geste.current
    if (!g) return
    const dx = e.clientX - g.x, dy = e.clientY - g.y
    if (Math.abs(dx) + Math.abs(dy) > 6) g.bouge = true
    if (zoomRef.current > 1) {
      const p = borne(g.px + dx, g.py + dy, zoomRef.current)
      panRef.current = p; setPan(p)
    } else if (g.touch && dy > 0 && dy > Math.abs(dx)) {
      setGlisse(dy) // la photo suit le doigt vers le bas
    }
  }
  function fin(e: ReactPointerEvent<HTMLDivElement>) {
    pointeurs.current.delete(e.pointerId)
    if (pincement.current) { if (pointeurs.current.size < 2) pincement.current = null; geste.current = null; return }
    const g = geste.current
    geste.current = null
    if (!g) return
    const dx = e.clientX - g.x, dy = e.clientY - g.y
    const rapide = Date.now() - g.t < 700
    if (zoomRef.current === 1 && glisse > 0) {
      setGlisse(0)
      if (dy > 110) { onClose(); return }
    }
    if (zoomRef.current === 1 && rapide && Math.abs(dx) > 60 && Math.abs(dy) < 90) aller(dx < 0 ? 1 : -1)
    else if (!g.bouge && zoomRef.current === 1) {
      if (g.fond && !g.touch) onClose() // un clic souris dans le noir ferme (la cible est celle du début : la capture du pointeur la change)
      else if (g.touch) setCalme((c) => !c) // un toucher montre ou cache les barres
    }
  }

  if (!courant) return null
  const legende = courant.legend?.trim() || ''
  const couverture = index === 0 && !courant.masquee && total > 1
  const progression = total > 1 ? ((index + 1) / total) * 100 : 100
  const fond = glisse > 0 ? Math.max(0.25, 1 - glisse / 420) : 1

  return (
    <div
      ref={racine}
      className={`bvv${calme ? ' is-calme' : ''}`}
      role="dialog"
      aria-modal="true"
      aria-label={`Photos de ${titre}`}
      tabIndex={-1}
      style={{ ['--bvv-fond' as string]: String(fond) }}
    >
      <div
        ref={scene}
        className={`bvv-scene${zoom > 1 ? ' is-zoom' : ''}`}
        onPointerDown={debut}
        onPointerMove={deplace}
        onPointerUp={fin}
        onPointerCancel={() => { geste.current = null; pointeurs.current.clear(); pincement.current = null; setGlisse(0) }}
      >
        {erreur ? (
          <div className="bvv-erreur" role="alert">
            <strong>Cette image ne se charge pas.</strong>
            <a href={courant.url} target="_blank" rel="noopener noreferrer">Ouvrir l'adresse de l'image</a>
          </div>
        ) : (
          <>
            {/* l'aperçu flou apparaît tout de suite, la photo nette le remplace dès qu'elle est là */}
            {courant.thumb && courant.thumb !== courant.url ? (
              <img className={`bvv-low${charge ? ' is-off' : ''}`} src={courant.thumb} alt="" aria-hidden="true" draggable={false} />
            ) : null}
            <img
              key={courant.url}
              ref={image}
              className={`bvv-img${charge ? ' is-ok' : ''}`}
              src={courant.url}
              alt={legende || titre}
              draggable={false}
              style={{ transform: `translate(${pan.x}px, ${pan.y + glisse}px) scale(${zoom})`, transition: glisse > 0 || geste.current ? 'none' : undefined }}
              onLoad={(e) => { setCharge(true); const im = e.currentTarget; if (im.naturalWidth) setDims(`${im.naturalWidth} × ${im.naturalHeight} px`) }}
              onError={() => setErreur(true)}
              onDoubleClick={(e) => zoomerEn(zoomRef.current > 1 ? 1 : 2.5, e.clientX, e.clientY)}
            />
          </>
        )}
        {!charge && !erreur && !courant.thumb ? <span className="bvv-attente" role="status" aria-label="Chargement de l'image" /> : null}
        {total > 1 ? (
          <>
            <button type="button" className="bvv-nav bvv-prev" onClick={() => aller(-1)} aria-label="Photo précédente" title="Précédente (←)"><Icone nom="gauche" /></button>
            <button type="button" className="bvv-nav bvv-next" onClick={() => aller(1)} aria-label="Photo suivante" title="Suivante (→)"><Icone nom="droite" /></button>
          </>
        ) : null}
      </div>

      <div className="bvv-bar" onPointerEnter={() => { survol.current = true; setCalme(false) }} onPointerLeave={() => { survol.current = false; reveiller() }}>
        <div className="bvv-ttl">
          <strong>{titre}</strong>
          <span>
            {[legende, dims].filter(Boolean).join(' · ') || ' '}
          </span>
        </div>
        {couverture ? <span className="bvv-flag is-cover">Couverture</span> : null}
        {courant.masquee ? <span className="bvv-flag">Masquée sur l'annonce</span> : null}
        {total > 1 ? <span className="bvv-count" aria-live="polite">{index + 1} / {total}</span> : null}
        <div className="bvv-tools">
          <button type="button" onClick={() => zoomerEn(zoomRef.current - ZOOM_PAS)} disabled={zoom <= ZOOM_MIN} aria-label="Zoom arrière" title="Zoom arrière (−)"><Icone nom="moins" /></button>
          <span className="bvv-zoom" aria-live="polite">{Math.round(zoom * 100)} %</span>
          <button type="button" onClick={() => zoomerEn(zoomRef.current + ZOOM_PAS)} disabled={zoom >= ZOOM_MAX} aria-label="Zoom avant" title="Zoom avant (+)"><Icone nom="plus" /></button>
          <button type="button" onClick={() => zoomerEn(1)} disabled={zoom === 1} aria-label="Ajuster à l'écran" title="Ajuster à l'écran (0)"><Icone nom="ajuster" /></button>
          <button type="button" className="bvv-plein" onClick={basculerPlein} aria-label={plein ? 'Quitter le plein écran' : 'Plein écran'} title={plein ? 'Quitter le plein écran (F)' : 'Plein écran (F)'}><Icone nom={plein ? 'reduire' : 'plein'} /></button>
          <a href={courant.url} target="_blank" rel="noopener noreferrer" aria-label="Ouvrir l'original dans un nouvel onglet" title="Ouvrir l'original"><Icone nom="original" /></a>
          <button type="button" className="bvv-close" onClick={onClose} aria-label="Fermer" title="Fermer (Échap)"><Icone nom="fermer" /></button>
        </div>
        <span className="bvv-prog" aria-hidden="true"><i style={{ width: `${progression}%` }} /></span>
      </div>

      {total > 1 ? (
        <div className="bvv-pied" onPointerEnter={() => { survol.current = true; setCalme(false) }} onPointerLeave={() => { survol.current = false; reveiller() }}>
          <p className="bvv-aide" aria-hidden="true"><kbd>←</kbd><kbd>→</kbd> changer de photo <i /> <kbd>+</kbd><kbd>−</kbd> zoom <i /> <kbd>F</kbd> plein écran <i /> <kbd>Échap</kbd> fermer</p>
          <div className="bvv-bande" ref={bandeau} role="list" aria-label="Toutes les photos">
            {items.map((it, i) => (
              <button
                key={it.url}
                type="button"
                role="listitem"
                className={`bvv-vign${i === index ? ' is-on' : ''}${it.masquee ? ' is-masquee' : ''}`}
                aria-current={i === index ? 'true' : undefined}
                aria-label={`Photo ${i + 1}${it.legend ? ` : ${it.legend}` : ''}${it.masquee ? ' (masquée)' : ''}`}
                onClick={() => allerA(i)}
              >
                <img src={it.thumb || it.url} alt="" loading="lazy" draggable={false} />
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
