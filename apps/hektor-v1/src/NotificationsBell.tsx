import { useCallback, useEffect, useRef, useState } from 'react'
import { loadNotifications, markNotificationRead, type NotificationRow } from './lib/api'

/**
 * Cloche de notifications négociateur (étape C du moteur de rapprochement).
 * Lit app_notification filtré par l'email du négociateur courant, affiche le
 * nombre de non-lues et un panneau déroulant. 100% autonome, scopé .gti-notif.
 */

function timeAgo(iso: string): string {
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return ''
  const s = Math.max(0, Math.round((Date.now() - t) / 1000))
  if (s < 60) return "à l'instant"
  const m = Math.round(s / 60)
  if (m < 60) return `il y a ${m} min`
  const h = Math.round(m / 60)
  if (h < 24) return `il y a ${h} h`
  const d = Math.round(h / 24)
  return `il y a ${d} j`
}

export interface NotificationsBellProps {
  negociateurEmail: string | null
}

export default function NotificationsBell({ negociateurEmail }: NotificationsBellProps) {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<NotificationRow[]>([])
  const [loading, setLoading] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)

  const refresh = useCallback(() => {
    if (!negociateurEmail) { setItems([]); return }
    setLoading(true)
    loadNotifications(negociateurEmail)
      .then(setItems)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [negociateurEmail])

  // chargement initial + rafraîchissement périodique léger (badge)
  useEffect(() => {
    if (!negociateurEmail) return
    refresh()
    const id = window.setInterval(refresh, 120000)
    return () => window.clearInterval(id)
  }, [negociateurEmail, refresh])

  // fermeture au clic extérieur / Échap
  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => { if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false) }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('mousedown', onDown); document.removeEventListener('keydown', onKey) }
  }, [open])

  const unread = items.filter((n) => !n.read_at).length

  const onToggle = useCallback(() => {
    setOpen((v) => {
      const next = !v
      if (next) refresh()
      return next
    })
  }, [refresh])

  const markOne = useCallback((n: NotificationRow) => {
    if (n.read_at) return
    setItems((list) => list.map((x) => x.id === n.id ? { ...x, read_at: new Date().toISOString() } : x))
    markNotificationRead(n.id).catch(() => {})
  }, [])

  const markAll = useCallback(() => {
    const unreadIds = items.filter((n) => !n.read_at).map((n) => n.id)
    if (!unreadIds.length) return
    const now = new Date().toISOString()
    setItems((list) => list.map((x) => x.read_at ? x : { ...x, read_at: now }))
    unreadIds.forEach((id) => markNotificationRead(id).catch(() => {}))
  }, [items])

  if (!negociateurEmail) return null

  return (
    <div className={`gti-notif${open ? ' is-open' : ''}`} ref={wrapRef}>
      <button
        type="button"
        className="gti-notif-btn"
        aria-label={`Notifications${unread ? ` (${unread} non lues)` : ''}`}
        aria-expanded={open}
        onClick={onToggle}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" />
        </svg>
        {unread > 0 && <span className="gti-notif-badge">{unread > 9 ? '9+' : unread}</span>}
      </button>

      {open && (
        <div className="gti-notif-pop" role="dialog" aria-label="Notifications">
          <div className="gti-notif-head">
            <span className="gti-notif-title">Notifications</span>
            {unread > 0 && <button type="button" className="gti-notif-mark" onClick={markAll}>Tout marquer lu</button>}
          </div>
          <div className="gti-notif-list">
            {loading && items.length === 0 && <div className="gti-notif-empty">Chargement…</div>}
            {!loading && items.length === 0 && <div className="gti-notif-empty">Aucune notification.</div>}
            {items.map((n) => (
              <button type="button" key={n.id} className={`gti-notif-item${n.read_at ? '' : ' is-unread'}`} onClick={() => markOne(n)}>
                {!n.read_at && <span className="gti-notif-dot" aria-hidden="true" />}
                <span className="gti-notif-it-bd">
                  <span className="gti-notif-it-t">{n.title}</span>
                  {n.body && <span className="gti-notif-it-s">{n.body}</span>}
                  <span className="gti-notif-it-d">{timeAgo(n.created_at)}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
