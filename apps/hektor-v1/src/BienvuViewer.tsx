// bienvu — la visionneuse d'image : toutes les photos du bien, pas une seule.
// Rendue seulement quand l'interrupteur est allumé (App.tsx garde l'ancienne fenêtre sinon).
// Au clavier : ← → pour passer d'une photo à l'autre, + − 0 pour le zoom, Échap pour fermer.
// Au doigt : balayage gauche/droite, double toucher pour zoomer, glisser pour déplacer une photo zoomée.
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
const ZOOM_MAX = 4
const ZOOM_PAS = 0.5

const ICONES = {
  gauche: <path d="M15 6l-6 6 6 6" />,
  droite: <path d="M9 6l6 6-6 6" />,
  moins: <path d="M5 12h14" />,
  plus: <path d="M12 5v14M5 12h14" />,
  ajuster: <><path d="M4 9V5h4M20 9V5h-4M4 15v4h4M20 15v4h-4" /></>,
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
  const racine = useRef<HTMLDivElement | null>(null)
  const scene = useRef<HTMLDivElement | null>(null)
  const image = useRef<HTMLImageElement | null>(null)
  const geste = useRef<{ x: number; y: number; t: number; px: number; py: number; bouge: boolean; fond: boolean } | null>(null)
  const bandeau = useRef<HTMLDivElement | null>(null)

  // la position et le zoom courants sont aussi tenus ici : deux touches très rapprochées lisent la valeur à jour,
  // pas celle du dernier affichage
  const indexRef = useRef(index)
  const zoomRef = useRef(1)
  indexRef.current = index
  zoomRef.current = zoom
  const allerA = useCallback((cible: number) => {
    if (total < 2) return
    const suivant = ((cible % total) + total) % total
    indexRef.current = suivant
    onIndex(suivant)
  }, [onIndex, total])
  const aller = useCallback((delta: number) => allerA(indexRef.current + delta), [allerA])

  // une nouvelle photo repart à zéro : taille réelle de l'écran, pas de décalage, pas d'erreur
  useEffect(() => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setCharge(false)
    setErreur(false)
  }, [courant?.url])

  // les deux voisines sont chargées d'avance : le passage est immédiat
  useEffect(() => {
    if (total < 2) return
    for (const voisin of [items[(index + 1) % total], items[(index - 1 + total) % total]]) {
      if (voisin?.url) { const pre = new Image(); pre.src = voisin.url }
    }
  }, [index, items, total])

  // la vignette courante reste visible dans la bande
  useEffect(() => {
    const actif = bandeau.current?.querySelector<HTMLElement>('[aria-current="true"]')
    actif?.scrollIntoView({ block: 'nearest', inline: 'center' })
  }, [index])

  // le focus entre dans la fenêtre et revient où il était ; la page derrière ne défile plus
  useEffect(() => {
    const avant = document.activeElement as HTMLElement | null
    const html = document.documentElement
    const overflow = html.style.overflow
    html.style.overflow = 'hidden'
    racine.current?.focus()
    return () => { html.style.overflow = overflow; avant?.focus?.() }
  }, [])

  const borne = useCallback((x: number, y: number, z: number) => {
    const s = scene.current, im = image.current
    if (!s || !im || z <= 1) return { x: 0, y: 0 }
    const mx = Math.max(0, (im.offsetWidth * z - s.clientWidth) / 2) + 40
    const my = Math.max(0, (im.offsetHeight * z - s.clientHeight) / 2) + 40
    return { x: Math.max(-mx, Math.min(mx, x)), y: Math.max(-my, Math.min(my, y)) }
  }, [])

  const changerZoom = useCallback((suivant: number) => {
    const z = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, suivant))
    zoomRef.current = z
    setZoom(z)
    setPan((p) => (z <= 1 ? { x: 0, y: 0 } : borne(p.x, p.y, z)))
  }, [borne])

  useEffect(() => {
    function touche(e: KeyboardEvent) {
      if (e.key === 'Escape') { e.preventDefault(); onClose() }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); aller(-1) }
      else if (e.key === 'ArrowRight') { e.preventDefault(); aller(1) }
      else if (e.key === '+' || e.key === '=') { e.preventDefault(); changerZoom(zoomRef.current + ZOOM_PAS) }
      else if (e.key === '-') { e.preventDefault(); changerZoom(zoomRef.current - ZOOM_PAS) }
      else if (e.key === '0') { e.preventDefault(); changerZoom(1) }
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
  }, [aller, changerZoom, onClose])

  function debut(e: ReactPointerEvent<HTMLDivElement>) {
    if ((e.target as HTMLElement).closest('button, a')) return
    geste.current = { x: e.clientX, y: e.clientY, t: Date.now(), px: pan.x, py: pan.y, bouge: false, fond: e.target === e.currentTarget }
    ;(e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId)
  }
  function deplace(e: ReactPointerEvent<HTMLDivElement>) {
    const g = geste.current
    if (!g) return
    const dx = e.clientX - g.x, dy = e.clientY - g.y
    if (Math.abs(dx) + Math.abs(dy) > 6) g.bouge = true
    if (zoom > 1) setPan(borne(g.px + dx, g.py + dy, zoom))
  }
  function fin(e: ReactPointerEvent<HTMLDivElement>) {
    const g = geste.current
    geste.current = null
    if (!g) return
    const dx = e.clientX - g.x, dy = e.clientY - g.y
    if (zoom === 1 && Date.now() - g.t < 700 && Math.abs(dx) > 60 && Math.abs(dy) < 90) aller(dx < 0 ? 1 : -1)
    else if (!g.bouge && zoom === 1 && g.fond) onClose() // un clic dans le noir ferme (la cible est celle du début : la capture du pointeur la change)
  }

  if (!courant) return null
  const legende = courant.legend?.trim() || ''

  return (
    <div
      ref={racine}
      className="bvv"
      role="dialog"
      aria-modal="true"
      aria-label={`Photos de ${titre}`}
      tabIndex={-1}
    >
      <div className="bvv-bar">
        <div className="bvv-ttl">
          <strong>{titre}</strong>
          {legende ? <span>{legende}</span> : null}
        </div>
        {total > 1 ? <span className="bvv-count" aria-live="polite">{index + 1} / {total}</span> : null}
        {courant.masquee ? <span className="bvv-flag">Masquée sur l'annonce</span> : null}
        <div className="bvv-tools">
          <button type="button" onClick={() => changerZoom(zoom - ZOOM_PAS)} disabled={zoom <= ZOOM_MIN} aria-label="Zoom arrière" title="Zoom arrière (−)"><Icone nom="moins" /></button>
          <span className="bvv-zoom" aria-live="polite">{Math.round(zoom * 100)} %</span>
          <button type="button" onClick={() => changerZoom(zoom + ZOOM_PAS)} disabled={zoom >= ZOOM_MAX} aria-label="Zoom avant" title="Zoom avant (+)"><Icone nom="plus" /></button>
          <button type="button" onClick={() => changerZoom(1)} disabled={zoom === 1} aria-label="Ajuster à l'écran" title="Ajuster à l'écran (0)"><Icone nom="ajuster" /></button>
          <a href={courant.url} target="_blank" rel="noopener noreferrer" aria-label="Ouvrir l'original dans un nouvel onglet" title="Ouvrir l'original"><Icone nom="original" /></a>
          <button type="button" className="bvv-close" onClick={onClose} aria-label="Fermer" title="Fermer (Échap)"><Icone nom="fermer" /></button>
        </div>
      </div>

      <div
        ref={scene}
        className={`bvv-scene${zoom > 1 ? ' is-zoom' : ''}`}
        onPointerDown={debut}
        onPointerMove={deplace}
        onPointerUp={fin}
        onPointerCancel={() => { geste.current = null }}
      >
        {erreur ? (
          <div className="bvv-erreur" role="alert">
            <strong>Cette image ne se charge pas.</strong>
            <a href={courant.url} target="_blank" rel="noopener noreferrer">Ouvrir l'adresse de l'image</a>
          </div>
        ) : (
          <img
            key={courant.url}
            ref={image}
            className={`bvv-img${charge ? ' is-ok' : ''}`}
            src={courant.url}
            alt={legende || titre}
            draggable={false}
            style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
            onLoad={() => setCharge(true)}
            onError={() => setErreur(true)}
            onDoubleClick={() => changerZoom(zoom > 1 ? 1 : 2.5)}
          />
        )}
        {!charge && !erreur ? <span className="bvv-attente" role="status" aria-label="Chargement de l'image" /> : null}
        {total > 1 ? (
          <>
            <button type="button" className="bvv-nav bvv-prev" onClick={() => aller(-1)} aria-label="Photo précédente" title="Précédente (←)"><Icone nom="gauche" /></button>
            <button type="button" className="bvv-nav bvv-next" onClick={() => aller(1)} aria-label="Photo suivante" title="Suivante (→)"><Icone nom="droite" /></button>
          </>
        ) : null}
      </div>

      {total > 1 ? (
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
      ) : null}
    </div>
  )
}
