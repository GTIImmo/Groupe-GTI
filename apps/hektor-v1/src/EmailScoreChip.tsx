// Chip de suivi email de rapprochement (Lot C) : affiche le score chaud/tiède/froid
// du dernier email envoyé à l'acquéreur. Rendu uniquement s'il existe un envoi.
import { useEffect, useState } from 'react'
import { loadEmailTracking, type EmailEnvoiRow } from './lib/api'

const SCORE_META: Record<string, { label: string; bg: string; fg: string }> = {
  chaud: { label: 'Contact chaud', bg: '#fdecef', fg: '#c5005f' },
  tiede: { label: 'Contact tiède', bg: '#fbf1e2', fg: '#b66a16' },
  froid: { label: 'Contact froid', bg: '#eef0f1', fg: '#5c6163' },
}

export default function EmailScoreChip({ contactSearchKey, hektorContactId }: { contactSearchKey?: string | null; hektorContactId?: string | null }) {
  const [last, setLast] = useState<EmailEnvoiRow | null>(null)

  useEffect(() => {
    let alive = true
    if (!contactSearchKey && !hektorContactId) { setLast(null); return }
    loadEmailTracking({ contactSearchKey, hektorContactId })
      .then((rows) => { if (alive) setLast(rows[0] ?? null) })
      .catch(() => { if (alive) setLast(null) })
    return () => { alive = false }
  }, [contactSearchKey, hektorContactId])

  if (!last) return null
  const meta = (last.score && SCORE_META[last.score]) || SCORE_META.froid
  const detail = last.statut === 'desinscrit' ? 'désinscrit'
    : last.statut === 'rdv' ? 'RDV demandé'
    : last.click_count > 0 ? `${last.click_count} clic${last.click_count > 1 ? 's' : ''}`
    : last.open_count > 0 ? 'ouvert' : 'envoyé'

  return (
    <span
      className="chip"
      title={`Dernier email · ${detail}${last.relances_count ? ` · ${last.relances_count} relance(s)` : ''}${last.dry_run ? ' · test' : ''}`}
      style={{ background: meta.bg, color: meta.fg, borderColor: 'transparent' }}
    >
      <span className="d" style={{ background: meta.fg }} />
      {meta.label} · {detail}
    </span>
  )
}
