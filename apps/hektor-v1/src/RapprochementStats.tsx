import { useEffect, useState } from 'react'
import { loadRapprochementStats, type RapprochementStats } from './lib/api'

/**
 * Reporting du moteur de rapprochement (étape E). Overlay autonome scopé .ra-stats,
 * alimenté par la RPC app_get_rapprochement_stats(). Ouvert depuis le menu « ⋯ »
 * de l'écran Recherche Acquéreur.
 */

export interface RapprochementStatsProps {
  open: boolean
  onClose: () => void
}

const nf = new Intl.NumberFormat('fr-FR')

export default function RapprochementStats({ open, onClose }: RapprochementStatsProps) {
  const [stats, setStats] = useState<RapprochementStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setLoading(true); setError(null)
    loadRapprochementStats()
      .then((s) => { if (!cancelled) setStats(s) })
      .catch((e) => { if (!cancelled) setError(e?.message ?? 'Erreur de chargement') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const g = stats?.global
  const c = stats?.criteres

  const kpi = (label: string, value: string | number, hint?: string) => (
    <div className="ras-kpi">
      <div className="ras-kpi-v">{value}</div>
      <div className="ras-kpi-l">{label}</div>
      {hint && <div className="ras-kpi-h">{hint}</div>}
    </div>
  )

  return (
    <div className="ra-stats" role="dialog" aria-modal="true" aria-label="Statistiques des rapprochements">
      <div className="ras-back" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
        <div className="ras-panel">
          <header className="ras-head">
            <div>
              <div className="ras-ey">Moteur de rapprochement</div>
              <h2 className="ras-title">Statistiques &amp; reporting</h2>
            </div>
            <button className="ras-close" aria-label="Fermer" onClick={onClose}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 6l12 12M18 6 6 18" /></svg>
            </button>
          </header>

          <div className="ras-body">
            {loading && <div className="ras-state">Chargement des statistiques…</div>}
            {error && <div className="ras-state err">Impossible de charger : {error}</div>}
            {!loading && !error && stats && (
              <>
                <div className="ras-kpis">
                  {kpi('Rapprochements', nf.format(g?.rapprochements ?? 0), `${nf.format(g?.recherches_avec_rappro ?? 0)} recherches`)}
                  {kpi('Propositions', nf.format(g?.propositions ?? 0))}
                  {kpi('Visites', nf.format(g?.visites ?? 0))}
                  {kpi('Écartés', nf.format(g?.ecartes ?? 0))}
                  {kpi('Délai moyen', g?.delai_moyen_jours != null ? `${g.delai_moyen_jours} j` : '—', 'rapprochement → proposition')}
                  {kpi('Recherches dormantes', nf.format(stats.recherches_dormantes ?? 0), 'sans proposition (14 j)')}
                  {kpi('Alertes non lues', nf.format(g?.alertes_non_lues ?? 0))}
                </div>

                <div className="ras-cols">
                  <section className="ras-card">
                    <div className="ras-card-h">Performance par négociateur</div>
                    {stats.par_negociateur.length === 0 ? (
                      <div className="ras-empty">Aucune donnée pour le moment.</div>
                    ) : (
                      <table className="ras-table">
                        <thead>
                          <tr><th>Négociateur</th><th>Rappr.</th><th>≥80%</th><th>Prop.</th><th>Taux</th></tr>
                        </thead>
                        <tbody>
                          {stats.par_negociateur.map((n) => (
                            <tr key={n.negociateur_email}>
                              <td className="ras-nego">{n.negociateur_email}</td>
                              <td>{nf.format(n.rapprochements)}</td>
                              <td>{nf.format(n.rapprochements_80)}</td>
                              <td>{nf.format(n.propositions)}</td>
                              <td>{n.taux_proposition_pct != null ? `${n.taux_proposition_pct} %` : '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </section>

                  <div className="ras-col-side">
                    <section className="ras-card">
                      <div className="ras-card-h">Biens les plus écartés</div>
                      {stats.biens_ecartes.length === 0 ? (
                        <div className="ras-empty">Aucun bien écarté.</div>
                      ) : (
                        <ul className="ras-list">
                          {stats.biens_ecartes.map((b) => (
                            <li key={b.app_dossier_id}>
                              <span className="ras-list-t">{b.titre || `Bien ${b.app_dossier_id}`}{b.ville ? ` · ${b.ville}` : ''}</span>
                              <span className="ras-list-n">{b.n_ecarte}×</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </section>

                    <section className="ras-card">
                      <div className="ras-card-h">Santé des critères</div>
                      <div className="ras-crit">
                        <div className="ras-crit-row"><span>Recherches actives</span><b>{nf.format(c?.actives ?? 0)}</b></div>
                        <div className="ras-crit-row warn"><span>Sans secteur</span><b>{nf.format(c?.sans_secteur ?? 0)}</b></div>
                        <div className="ras-crit-row warn"><span>Sans type</span><b>{nf.format(c?.sans_type ?? 0)}</b></div>
                        <div className="ras-crit-row warn"><span>Sans type ni secteur</span><b>{nf.format(c?.sans_type_ni_secteur ?? 0)}</b></div>
                      </div>
                      <div className="ras-note">Les recherches sans type ni secteur sont exclues du scan d'alertes (faible pertinence).</div>
                    </section>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
