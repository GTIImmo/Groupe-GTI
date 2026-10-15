import { useCallback, useEffect, useMemo, useState } from 'react'
import { loadMonitorStatus, loadAlertsCurrent, setAlertState, loadAgentRuns, localiserAnnonceParNumeroHektor, loadActionStatus, resolveAction, gesteLibelleFr, type MonitorStatusRow, type AlertRow, type AgentRunRow, type AnnonceLocalisee, type ActionAbandonnee } from './lib/api'
import './sante-systeme.css'

type SanteSystemeScreenProps = {
  isAdmin: boolean
  // 15/10/2026 : facultatif EXPRES. Sans lui, l'ecran se comporte exactement
  // comme avant -- les biens s'affichent, mais ne sont pas cliquables.
  onOpenDossier?: (appDossierId: number) => void
}

type Tone = 'ok' | 'warn' | 'crit' | 'unknown'

const STATUS_TONE: Record<string, Tone> = {
  ok: 'ok',
  info: 'ok',
  warning: 'warn',
  critical: 'crit',
  unknown: 'unknown',
}

const STATUS_LABEL: Record<Tone, string> = {
  ok: 'En ligne',
  warn: 'À surveiller',
  crit: 'Incident',
  unknown: 'Indéterminé',
}

const SOURCE_LABEL: Record<string, string> = {
  monitoring: 'Système',
  notification: 'Notif',
  relance: 'Relance',
  pauline: 'Pauline',
  agent: 'Agent',
}

const DOMAIN_LABEL: Record<string, string> = {
  system: 'Infrastructure & workers',
  business: 'Métier',
  data_quality: 'Qualité des données',
  cron: 'Tâches planifiées',
  surface: 'Surfaces publiques',
  console: 'File de jobs',
  supabase: 'Supabase',
  workers: 'Workers',
  sqlite: 'Bases locales',
  backend: 'Backend',
  logs: 'Logs',
  playwright: 'Sessions Playwright',
  documents: 'Documents',
  scheduledtasks: 'Tâches Windows',
  email: 'Emails',
  monitor: 'Superviseur',
}

const AGENT_LABEL: Record<string, string> = {
  redacteur: "Rédacteur d'annonce",
  avis_valeur: 'Avis de valeur',
  scan_fiche: 'Scan fiche',
}

const TONE_RANK: Record<Tone, number> = { crit: 0, warn: 1, unknown: 2, ok: 3 }

// ⭐ LES BIENS CITES PAR UNE ALERTE, CLIQUABLES (15/10/2026).
//
//   Les sondes qui sonnent joignent un APERCU a leur resultat -- c'est le `sample`
//   ajoute le 01/09, apres la question de Frederic « comment je le retrouve a partir
//   du monitoring pour savoir lequel ? ». Il porte deja tout :
//       { reference: "annonce 61672", libelle: "Villa de PP de 1999...", cause: "..." }
//   On s'en sert pour offrir un bouton par bien. RIEN N'EST AJOUTE EN BASE : la
//   colonne details_json etait deja chargee par loadMonitorStatus.
//
//   ⚠ Le numero cite est celui de HEKTOR ; l'ecran ouvre un bien par son
//     app_dossier_id. Le pont se fait au clic (findDossierIdByHektorAnnonce), pas
//     au chargement : une alerte qui sonne est rare, et on ne va pas interroger la
//     base pour des lignes que personne ne regardera.
type ApercuLigne = { reference?: string; libelle?: string; cause?: string }

function biensCites(row: MonitorStatusRow | undefined): ApercuLigne[] {
  const apercu = (row?.details_json as { apercu?: unknown } | null)?.apercu
  if (!Array.isArray(apercu)) return []
  return apercu.filter((x): x is ApercuLigne => typeof x === 'object' && x !== null)
}

function numeroHektor(reference: string | undefined): string | null {
  const m = /(\d{3,})/.exec(reference ?? '')
  return m ? m[1] : null
}

// ⭐⭐ LES DEUX BOUTONS SONT ICI, SUR LA LIGNE DE L'ALERTE (15/10/2026).
//
// LA QUESTION DE FREDERIC, LE 14/10 : « dans le monitoring je n'ai pas de bouton pour
// relancer ou annuler le worker ? ». J'avais repondu en rendant les biens CLIQUABLES,
// pour aller chercher le bandeau sur leur fiche. C'ETAIT LA MAUVAISE REPONSE, et le
// 15/10 l'a prouve : le bien 47824 est VENDU, il n'a aucun detail en cache, donc sa
// fiche ne s'ouvre qu'apres un import de detail chez Hektor -- trois etapes et une
// attente, pour eteindre une alerte.
//
// Desormais un clic sur le bien cite OUVRE UN PANNEAU, ici meme, avec les gestes qui
// attendent un humain et leurs deux boutons. La fiche reste accessible quand elle
// existe, mais elle n'est plus le seul chemin.
//
// ⚠ RIEN N'EST AJOUTE EN BASE : app_action_status et app_action_resolve sont celles du
//   bandeau de la fiche, et le repli vendus/clos/archives pose le matin meme fait
//   qu'elles repondent pour un bien qui n'est plus dans le parc vivant.
// ⚠ TOUT EST PARESSEUX : on n'interroge la base que pour le bien sur lequel on clique.
function TrancherIci({
  numero,
  onOpenDossier,
}: {
  numero: string
  onOpenDossier?: (appDossierId: number) => void
}) {
  const [etat, setEtat] = useState<'ferme' | 'charge' | 'ouvert'>('ferme')
  const [lieu, setLieu] = useState<AnnonceLocalisee | null>(null)
  const [gestes, setGestes] = useState<ActionAbandonnee[]>([])
  const [occupe, setOccupe] = useState<string | null>(null)
  const [souci, setSouci] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)

  const charger = async () => {
    if (etat === 'charge') return
    if (etat === 'ouvert') { setEtat('ferme'); return }
    setEtat('charge')
    setSouci(null)
    setNote(null)
    try {
      const ou = await localiserAnnonceParNumeroHektor(numero)
      if (!ou) {
        setSouci(`Bien ${numero} introuvable dans l'app (ni vivant, ni vendu, ni archive).`)
        setEtat('ouvert')
        return
      }
      setLieu(ou)
      const statut = await loadActionStatus(ou.app_dossier_id)
      setGestes(statut?.gestes ?? [])
      if (!statut) setSouci("Impossible de lire les gestes de ce bien (droits ou lecture en echec).")
      setEtat('ouvert')
    } catch (err) {
      setSouci(err instanceof Error ? err.message : String(err))
      setEtat('ouvert')
    }
  }

  const trancher = async (jobId: string, mode: 'refait' | 'abandon') => {
    if (occupe) return
    setOccupe(jobId)
    setSouci(null)
    setNote(null)
    try {
      const compte = await resolveAction(jobId, mode)
      if (compte && compte.resolved === false) {
        setSouci(compte.reason === 'deja_tranche'
          ? 'Ce geste a déjà été tranché.'
          : "Ce geste n'est pas encore tranchable : il lui faut 5 tentatives ou 3 heures.")
        return
      }
      if (compte && mode === 'abandon') {
        const remis = (compte.defait ?? []).filter((x) => Number(x.fiche_remise) > 0)
        setNote(remis.length
          ? `Abandonné. Remis comme Hektor : ${remis.map((x) => `${x.champ} = ${x.valeur_avant ?? 'vide'}`).join(', ')}.`
          : "Abandonné. Rien à remettre : votre fiche disait déjà la même chose que Hektor.")
      } else {
        setNote('Noté comme traité.')
      }
      setGestes((liste) => liste.filter((g) => g.job_id !== jobId))
    } catch (err) {
      setSouci(err instanceof Error ? err.message : String(err))
    } finally {
      setOccupe(null)
    }
  }

  return (
    <div className="ss-trancher">
      <button type="button" className="ss-bien-cite" onClick={() => { void charger() }} disabled={etat === 'charge'}>
        {etat === 'charge' ? 'Lecture…' : etat === 'ouvert' ? `Bien ${numero} ▴` : `Bien ${numero} — trancher ▾`}
      </button>
      {etat === 'ouvert' ? (
        <div className="ss-trancher-panneau">
          {lieu ? (
            <div className="ss-trancher-lieu">
              {lieu.titre_bien || `Bien ${numero}`}
              {lieu.monde !== 'vivant'
                ? ` · ${lieu.monde === 'archive' ? 'archivé' : lieu.statut_annonce || 'vendu / clos'} — sa fiche demande un import de détail`
                : null}
              {lieu.monde === 'vivant' && onOpenDossier ? (
                <>
                  {' · '}
                  <button type="button" className="ss-lien-fiche" onClick={() => onOpenDossier(lieu.app_dossier_id)}>
                    ouvrir la fiche
                  </button>
                </>
              ) : null}
            </div>
          ) : null}
          {gestes.map((g) => (
            <div className="ss-trancher-geste" key={g.job_id}>
              <div className="ss-trancher-geste-nom">{gesteLibelleFr(g.job_type)}</div>
              {g.erreur ? <div className="ss-trancher-geste-cause">{g.erreur}</div> : null}
              <div className="ss-trancher-actions">
                <button type="button" className="ss-btn-refait" disabled={occupe === g.job_id}
                        onClick={() => { void trancher(g.job_id, 'refait') }}>J'ai refait</button>
                <button type="button" className="ss-btn-abandon" disabled={occupe === g.job_id}
                        onClick={() => { void trancher(g.job_id, 'abandon') }}>Abandonner ce geste</button>
              </div>
            </div>
          ))}
          {!gestes.length && !souci ? <div className="ss-trancher-vide">Rien à trancher sur ce bien.</div> : null}
          {note ? <div className="ss-trancher-note">{note}</div> : null}
          {souci ? <div className="ss-trancher-souci">{souci}</div> : null}
        </div>
      ) : null}
    </div>
  )
}

function BiensCitesParLAlerte({
  lignes,
  onOpenDossier,
}: {
  lignes: ApercuLigne[]
  onOpenDossier?: (appDossierId: number) => void
}) {
  if (!lignes.length) return null
  return (
    <div className="ss-biens-cites">
      {lignes.map((l, i) => {
        const numero = numeroHektor(l.reference)
        if (!numero) {
          return <span className="ss-bien-cite ss-bien-cite-mort" key={i}>{l.libelle || l.reference || '—'}</span>
        }
        return <TrancherIci key={`${numero}-${i}`} numero={numero} onOpenDossier={onOpenDossier} />
      })}
    </div>
  )
}

function toneOf(status: string | null | undefined): Tone {
  if (!status) return 'unknown'
  return STATUS_TONE[status] ?? 'unknown'
}

function timeAgo(iso: string | null): string {
  if (!iso) return '—'
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return '—'
  const mins = Math.max(0, Math.round((Date.now() - then) / 60000))
  if (mins < 60) return `il y a ${mins} min`
  const hours = Math.round(mins / 60)
  if (hours < 48) return `il y a ${hours} h`
  return `il y a ${Math.round(hours / 24)} j`
}

export default function SanteSystemeScreen({ isAdmin, onOpenDossier }: SanteSystemeScreenProps) {
  const [rows, setRows] = useState<MonitorStatusRow[]>([])
  const [alerts, setAlerts] = useState<AlertRow[]>([])
  const [agentRuns, setAgentRuns] = useState<AgentRunRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // 14/10/2026 -- « C'est un sapin de Noel » (Frederic). L'ecran listait les 71
  // sondes a plat : 61 vertes, dont 21 qui disent litteralement « 0 (seuil 0) »,
  // et il fallait quatre ecrans pour arriver en bas. Les 10 lignes qui comptent
  // etaient noyees. On replie donc les vertes derriere une seule ligne, qui se
  // deplie d'un clic : RIEN N'EST SUPPRIME, tout reste consultable.
  const [verrouDesVerts, setVerrouDesVerts] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const refresh = useCallback(async () => {
    try {
      setError(null)
      const [status, alertRows, runs] = await Promise.all([loadMonitorStatus(), loadAlertsCurrent(), loadAgentRuns(7).catch(() => [])])
      setRows(status)
      setAlerts(alertRows)
      setAgentRuns(runs)
      setLastRefresh(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleAlertAction = useCallback(
    async (alertKey: string, status: 'acknowledged' | 'resolved') => {
      try {
        await setAlertState(alertKey, status)
        void refresh()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Action impossible')
      }
    },
    [refresh],
  )

  useEffect(() => {
    if (!isAdmin) return
    void refresh()
    const timer = window.setInterval(() => {
      void refresh()
    }, 120000)
    return () => window.clearInterval(timer)
  }, [isAdmin, refresh])

  const summaryRow = useMemo(
    () => rows.find((row) => row.status_key === 'monitor.summary') ?? null,
    [rows],
  )

  const counts = useMemo(() => {
    const acc: Record<Tone, number> = { ok: 0, warn: 0, crit: 0, unknown: 0 }
    for (const row of rows) {
      if (row.status_key === 'monitor.summary') continue
      acc[toneOf(row.status)] += 1
    }
    return acc
  }, [rows])

  const groups = useMemo(() => {
    const map = new Map<string, MonitorStatusRow[]>()
    for (const row of rows) {
      if (row.status_key === 'monitor.summary') continue
      const domain = row.domain ?? 'autre'
      const list = map.get(domain)
      if (list) list.push(row)
      else map.set(domain, [row])
    }
    const entries = Array.from(map.entries())
    for (const [, list] of entries) {
      list.sort(
        (a, b) =>
          TONE_RANK[toneOf(a.status)] - TONE_RANK[toneOf(b.status)] ||
          a.status_key.localeCompare(b.status_key),
      )
    }
    entries.sort((a, b) => {
      const worstA = Math.min(...a[1].map((row) => TONE_RANK[toneOf(row.status)]))
      const worstB = Math.min(...b[1].map((row) => TONE_RANK[toneOf(row.status)]))
      return worstA - worstB || a[0].localeCompare(b[0])
    })
    return entries
  }, [rows])

  // Ce qui ne va pas, groupe par groupe -- et combien de controles sont au vert.
  const groupesAffiches = useMemo(() => {
    if (!verrouDesVerts) return groups
    return groups
      .map(([domaine, liste]) =>
        [domaine, liste.filter((row) => toneOf(row.status) !== 'ok')] as [string, MonitorStatusRow[]],
      )
      .filter(([, liste]) => liste.length > 0)
  }, [groups, verrouDesVerts])

  const nbAuVert = useMemo(
    () => rows.filter((row) => row.status_key !== 'monitor.summary' && toneOf(row.status) === 'ok').length,
    [rows],
  )

  const alertsToTreat = useMemo(
    () =>
      alerts
        .filter(
          (alert) =>
            (alert.severity === 'warning' || alert.severity === 'critical') &&
            alert.lifecycle_status !== 'resolved' &&
            alert.lifecycle_status !== 'ignored' &&
            alert.lifecycle_status !== 'snoozed',
        )
        .sort(
          (a, b) =>
            (a.severity === 'critical' ? 0 : 1) - (b.severity === 'critical' ? 0 : 1) ||
            (b.created_at ?? '').localeCompare(a.created_at ?? ''),
        ),
    [alerts],
  )
  const alertsInfoCount = useMemo(
    () => alerts.filter((alert) => alert.severity !== 'warning' && alert.severity !== 'critical').length,
    [alerts],
  )

  const agentStats = useMemo(() => {
    const total = agentRuns.length
    let cost = 0
    const byAgent: Record<string, { n: number; cost: number }> = {}
    const errors: AgentRunRow[] = []
    let accepted = 0
    let rejected = 0
    for (const r of agentRuns) {
      const c = Number(r.cost_usd) || 0
      cost += c
      const a = byAgent[r.agent_key] ?? { n: 0, cost: 0 }
      a.n += 1
      a.cost += c
      byAgent[r.agent_key] = a
      if (r.status === 'accepted') accepted += 1
      else if (r.status === 'rejected') rejected += 1
      else if (r.status === 'error') errors.push(r)
    }
    const decided = accepted + rejected
    return { total, cost, byAgent, errors, accepted, rejected, acceptRate: decided ? accepted / decided : null }
  }, [agentRuns])

  if (!isAdmin) {
    return (
      <section className="panel">
        <p className="empty-state">Accès réservé aux administrateurs.</p>
      </section>
    )
  }

  const globalTone: Tone = counts.crit > 0 ? 'crit' : counts.warn > 0 ? 'warn' : 'ok'
  const globalLabel = counts.crit > 0 ? 'Incident' : counts.warn > 0 ? 'Attention' : 'Tout fonctionne'
  const staleSummary = summaryRow ? timeAgo(summaryRow.observed_at ?? summaryRow.updated_at) : '—'

  return (
    <section className="sante-systeme-v1">
      <header className="ss-top">
        <div className="ss-title">
          <span className={`ss-dot ss-${globalTone}`} aria-hidden="true" />
          <div>
            <h1>Santé système</h1>
            <p className="ss-sub">
              {loading && rows.length === 0 ? 'Chargement…' : `${globalLabel} · relevé ${staleSummary}`}
            </p>
          </div>
        </div>
        <button className="ss-refresh" type="button" onClick={() => { void refresh() }}>
          Rafraîchir
          {lastRefresh ? ` · ${lastRefresh.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` : ''}
        </button>
      </header>

      {error ? <p className="ss-error">Impossible de charger le monitoring : {error}</p> : null}

      <div className="ss-kpis">
        <div className="ss-kpi">
          <span className="ss-kpi-label">État global</span>
          <span className={`ss-kpi-val ss-text-${globalTone}`}>{globalLabel}</span>
        </div>
        <div className="ss-kpi">
          <span className="ss-kpi-label">En ligne</span>
          <span className="ss-kpi-val">{counts.ok}</span>
        </div>
        <div className="ss-kpi">
          <span className="ss-kpi-label">À surveiller</span>
          <span className={`ss-kpi-val ${counts.warn ? 'ss-text-warn' : ''}`}>{counts.warn}</span>
        </div>
        <div className="ss-kpi">
          <span className="ss-kpi-label">Incidents</span>
          <span className={`ss-kpi-val ${counts.crit ? 'ss-text-crit' : ''}`}>{counts.crit}</span>
        </div>
      </div>

      {alertsToTreat.length > 0 || alertsInfoCount > 0 ? (
        <div className="ss-group">
          <div className="ss-group-head">
            <h2>Alertes à traiter</h2>
            <span className="ss-count">{alertsToTreat.length}</span>
          </div>
          <div className="ss-rows">
            {alertsToTreat.map((alert) => {
              const tone = toneOf(alert.severity)
              return (
                <div className="ss-row" key={alert.alert_key}>
                  <span className={`ss-dot ss-${tone}`} aria-hidden="true" />
                  <div className="ss-row-body">
                    <div className="ss-row-name">
                      <span className="ss-src">{SOURCE_LABEL[alert.source] ?? alert.source}</span>{' '}
                      {alert.title ?? alert.alert_key}
                    </div>
                    <div className="ss-row-msg">{alert.owner_email ?? alert.owner_role ?? ''}</div>
                    <BiensCitesParLAlerte
                      lignes={biensCites(rows.find((r) => `monitor:${r.status_key}` === alert.alert_key))}
                      onOpenDossier={onOpenDossier}
                    />
                  </div>
                  <div className="ss-row-meta">
                    {alert.lifecycle_status === 'acknowledged' ? <span className="ss-ack">Pris en charge</span> : null}
                    <span className={`ss-pill ss-bg-${tone}`}>{STATUS_LABEL[tone]}</span>
                    <span className="ss-age">{timeAgo(alert.created_at)}</span>
                    <span className="ss-actions">
                      {alert.lifecycle_status === 'new' ? (
                        <button type="button" className="ss-act" onClick={() => { void handleAlertAction(alert.alert_key, 'acknowledged') }}>Prendre en charge</button>
                      ) : null}
                      <button type="button" className="ss-act ss-act-done" onClick={() => { void handleAlertAction(alert.alert_key, 'resolved') }}>Résolu</button>
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
          {alertsInfoCount > 0 ? (
            <div className="ss-alerts-info">
              + {alertsInfoCount} notification{alertsInfoCount > 1 ? 's' : ''} non lue{alertsInfoCount > 1 ? 's' : ''}
            </div>
          ) : null}
        </div>
      ) : null}

      {agentStats.total > 0 ? (
        <div className="ss-group">
          <div className="ss-group-head">
            <h2>Agents IA · 7 jours</h2>
            <span className="ss-count">{agentStats.total}</span>
          </div>
          <div className="ss-kpis">
            <div className="ss-kpi"><span className="ss-kpi-label">Exécutions</span><span className="ss-kpi-val">{agentStats.total}</span></div>
            <div className="ss-kpi"><span className="ss-kpi-label">Coût</span><span className="ss-kpi-val">{(agentStats.cost * 100).toFixed(1)} cts</span></div>
            <div className="ss-kpi"><span className="ss-kpi-label">Acceptation</span><span className="ss-kpi-val">{agentStats.acceptRate != null ? `${Math.round(agentStats.acceptRate * 100)}%` : '—'}</span></div>
            <div className="ss-kpi"><span className="ss-kpi-label">Erreurs</span><span className={`ss-kpi-val ${agentStats.errors.length ? 'ss-text-crit' : ''}`}>{agentStats.errors.length}</span></div>
          </div>
          <div className="ss-rows">
            {Object.entries(agentStats.byAgent).map(([agent, s]) => (
              <div className="ss-row" key={agent}>
                <span className="ss-dot ss-ok" aria-hidden="true" />
                <div className="ss-row-body">
                  <div className="ss-row-name">{AGENT_LABEL[agent] ?? agent}</div>
                  <div className="ss-row-msg">{s.n} run{s.n > 1 ? 's' : ''} · {(s.cost * 100).toFixed(1)} cts</div>
                </div>
              </div>
            ))}
            {agentStats.errors.slice(0, 3).map((e) => (
              <div className="ss-row" key={`err-${e.id}`}>
                <span className="ss-dot ss-crit" aria-hidden="true" />
                <div className="ss-row-body">
                  <div className="ss-row-name"><span className="ss-src">{AGENT_LABEL[e.agent_key] ?? e.agent_key}</span> erreur</div>
                  <div className="ss-row-msg">{(e.error_text ?? '').slice(0, 90)}</div>
                </div>
                <div className="ss-row-meta"><span className="ss-age">{timeAgo(e.created_at)}</span></div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {groupesAffiches.map(([domain, list]) => (
        <div className="ss-group" key={domain}>
          <div className="ss-group-head">
            <h2>{DOMAIN_LABEL[domain] ?? domain}</h2>
            <span className="ss-count">{list.length}</span>
          </div>
          <div className="ss-rows">
            {list.map((row) => {
              const tone = toneOf(row.status)
              return (
                <div className="ss-row" key={row.status_key}>
                  <span className={`ss-dot ss-${tone}`} aria-hidden="true" />
                  <div className="ss-row-body">
                    <div className="ss-row-name">{row.check_name || row.status_key}</div>
                    <div className="ss-row-msg">{row.message ?? ''}</div>
                    <BiensCitesParLAlerte lignes={biensCites(row)} onOpenDossier={onOpenDossier} />
                  </div>
                  <div className="ss-row-meta">
                    <span className={`ss-pill ss-bg-${tone}`}>{STATUS_LABEL[tone]}</span>
                    <span className="ss-age">{timeAgo(row.observed_at ?? row.updated_at)}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}

      {nbAuVert > 0 ? (
        <button
          type="button"
          className="ss-verts-repli"
          onClick={() => { setVerrouDesVerts((v) => !v) }}
        >
          <span className="ss-dot ss-ok" aria-hidden="true" />
          <span className="ss-verts-texte">
            {verrouDesVerts
              ? `${nbAuVert} controle${nbAuVert > 1 ? 's' : ''} au vert`
              : `${nbAuVert} controle${nbAuVert > 1 ? 's' : ''} au vert — affiches ci-dessus`}
          </span>
          <span className="ss-verts-action">{verrouDesVerts ? 'Afficher' : 'Masquer'}</span>
        </button>
      ) : null}

      {!loading && rows.length === 0 && !error ? (
        <p className="empty-state">Aucune donnée de monitoring pour le moment.</p>
      ) : null}
    </section>
  )
}
