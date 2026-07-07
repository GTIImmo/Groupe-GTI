import { useCallback, useEffect, useMemo, useState } from 'react'
import { loadMonitorStatus, loadAlertsCurrent, setAlertState, loadAgentRuns, type MonitorStatusRow, type AlertRow, type AgentRunRow } from './lib/api'
import './sante-systeme.css'

type SanteSystemeScreenProps = {
  isAdmin: boolean
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

export default function SanteSystemeScreen({ isAdmin }: SanteSystemeScreenProps) {
  const [rows, setRows] = useState<MonitorStatusRow[]>([])
  const [alerts, setAlerts] = useState<AlertRow[]>([])
  const [agentRuns, setAgentRuns] = useState<AgentRunRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
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

      {groups.map(([domain, list]) => (
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

      {!loading && rows.length === 0 && !error ? (
        <p className="empty-state">Aucune donnée de monitoring pour le moment.</p>
      ) : null}
    </section>
  )
}
