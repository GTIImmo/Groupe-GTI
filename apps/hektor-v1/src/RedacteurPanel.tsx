import { useEffect, useState } from 'react'
import {
  generateAnnonceDescription,
  recordRedacteurDecision,
  wakeBackendApi,
  type RedacteurProposal,
} from './lib/api'
import './redacteur-panel.css'

type RedacteurPanelProps = {
  /** Donnees factuelles deja affichees sur la fiche (aucune re-derivation serveur). */
  propertyData: Record<string, unknown>
  photoUrls?: string[]
  appDossierId?: number | null
  hektorAnnonceId?: number | null
  /**
   * Appele quand le negociateur ACCEPTE la proposition (eventuellement editee).
   * Recoit les 4 sorties editees ; l'hote decide comment les repartir dans les
   * champs de l'annonce. L'agent n'ecrit jamais lui-meme : propose-only.
   */
  onAccept?: (result: { title: string; accroche: string; description: string; highlights: string[] }) => void
}

export default function RedacteurPanel({
  propertyData,
  photoUrls,
  appDossierId,
  hektorAnnonceId,
  onAccept,
}: RedacteurPanelProps) {
  const [loading, setLoading] = useState(false)
  const [waking, setWaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [proposal, setProposal] = useState<RedacteurProposal | null>(null)
  const [title, setTitle] = useState('')
  const [accroche, setAccroche] = useState('')
  const [description, setDescription] = useState('')
  const [highlightsText, setHighlightsText] = useState('')
  const [decided, setDecided] = useState<null | 'accepted' | 'rejected'>(null)

  // Reveil anticipe du backend des l'ouverture du panneau (Render gratuit s'endort) :
  // il se reveille pendant que l'utilisateur lit/remplit, l'appel repond ensuite vite.
  useEffect(() => { wakeBackendApi() }, [])

  const currentHighlights = () => highlightsText.split('\n').map((h) => h.trim()).filter(Boolean)

  const runGenerate = async () => {
    setLoading(true)
    setWaking(false)
    setError(null)
    setDecided(null)
    try {
      const result = await generateAnnonceDescription({
        propertyData,
        photoUrls,
        appDossierId,
        hektorAnnonceId,
      }, () => setWaking(true))
      setProposal(result)
      setTitle(result.title)
      setAccroche(result.accroche)
      setDescription(result.description)
      setHighlightsText(result.highlights.join('\n'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Génération impossible')
    } finally {
      setLoading(false)
      setWaking(false)
    }
  }

  const accept = () => {
    const highlights = currentHighlights()
    if (proposal?.runId) void recordRedacteurDecision(proposal.runId, 'accepted', title, description)
    onAccept?.({ title, accroche, description, highlights })
    setDecided('accepted')
  }

  const reject = () => {
    if (proposal?.runId) void recordRedacteurDecision(proposal.runId, 'rejected')
    setDecided('rejected')
    setProposal(null)
  }

  const copyDescription = () => {
    void navigator.clipboard?.writeText(description).catch(() => undefined)
  }

  return (
    <div className="redac-panel">
      <div className="redac-head">
        <div className="redac-title">
          <span className="redac-badge">IA</span>
          <div>
            <h3>Rédacteur d'annonce</h3>
            <p className="redac-sub">
              Propose un titre et une description à partir des données du bien et des photos.
              Vous validez avant toute utilisation.
            </p>
          </div>
        </div>
        <button type="button" className="redac-generate" onClick={() => { void runGenerate() }} disabled={loading}>
          {loading ? (waking ? 'Réveil du serveur (~30 s)…' : 'Génération…') : proposal ? 'Régénérer' : 'Générer avec l’IA'}
        </button>
      </div>

      {error ? <p className="redac-error">{error}</p> : null}

      {decided === 'accepted' ? (
        <p className="redac-ok">Proposition acceptée — reportée dans la fiche. Pensez à enregistrer.</p>
      ) : null}

      {proposal && decided !== 'rejected' ? (
        <div className="redac-body">
          <label className="redac-field">
            <span className="redac-label">Titre annonce proposé</span>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="redac-input"
              maxLength={120}
            />
          </label>

          <label className="redac-field">
            <span className="redac-label">Accroche</span>
            <textarea
              value={accroche}
              onChange={(e) => setAccroche(e.target.value)}
              className="redac-textarea"
              rows={2}
            />
          </label>

          <label className="redac-field">
            <span className="redac-label">Descriptif</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="redac-textarea"
              rows={9}
            />
          </label>

          <label className="redac-field">
            <span className="redac-label">Points forts (un par ligne)</span>
            <textarea
              value={highlightsText}
              onChange={(e) => setHighlightsText(e.target.value)}
              className="redac-textarea"
              rows={4}
            />
          </label>

          <div className="redac-actions">
            <button type="button" className="redac-accept" onClick={accept}>Accepter</button>
            <button type="button" className="redac-copy" onClick={copyDescription}>Copier la description</button>
            <button type="button" className="redac-reject" onClick={reject}>Rejeter</button>
            <span className="redac-meta">
              {proposal.model ?? ''}
              {proposal.costUsd != null ? ` · ~${(proposal.costUsd * 100).toFixed(2)} cts` : ''}
            </span>
          </div>
        </div>
      ) : null}
    </div>
  )
}
