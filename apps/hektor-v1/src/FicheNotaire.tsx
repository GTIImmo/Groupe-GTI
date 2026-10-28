// ⑧ NOTAIRE, ÉTAPE 4 (28/10/2026) — LA FICHE NOTAIRE (maquette maquettes/fiche-notaire-v2.html).
//
// Les blocs notaire de la fiche contact V2, quand la catégorie dominante est « Notaire » : chiffres en tête, dossiers en
// cours (et « À vérifier »), « À venir », ventes des 12 mois, « Avec nous », confrères fréquents. Les données viennent de
// la fonction de base app_notaire_fiche (SECURITY INVOKER : un négociateur n'y voit que SES dossiers, décision 1 du 28/10).
// Les règles (« en cours », étapes, chiffres) sont ICI, dans des fonctions pures, essayées par test_fiche_notaire.cjs.
// Décisions de Frédéric (28/10, note des types §49.6-49.7) :
//   2. « en cours » = compromis vivant sans vente dans sa chaîne, dont l'acte prévu n'est pas passé (ou, sans date d'acte,
//      de moins de 6 mois) ; les autres dans « À vérifier », replié, jamais caché ;
//   3. la bande « Biens & mandats liés » reste (elle vit dans App.tsx) ;
//   4. les honoraires encaissés = commission_agence ;
//   5. « Exporter » : en construction. Et décision 5 du 27/10 : les blocs sans données (interlocuteurs de l'étude, pièces du
//      dossier, condition de prêt) sont MONTRÉS, marqués « en construction ».
// Interrupteur : FICHE_NOTAIRE_V2 (false = la fiche d'avant, à l'identique).
import { useEffect, useState, type CSSProperties } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'

export const FICHE_NOTAIRE_V2 = true

type Personne = { id: string | null; nom: string; ville?: string }
export type DossierNotaire = {
  app_affaire_id: number
  kind: string
  state: string | null
  date: string | null
  date_acte: string | null
  date_fin_retractation: string | null
  montant: string | null
  commission_agence: string | null
  honoraires_entree?: string | null
  honoraires_sortie?: string | null
  prix_net_vendeur: string | null
  sequestre: string | null
  app_chaine_id: number | null
  numero_mandat: string | null
  hektor_annonce_id: number | string | null
  app_dossier_id: number | null
  cotes: string[]
  vente_chaine: { date: string | null; montant: string | null } | null
  compromis_chaine: string | null
  vendeurs: Personne[]
  acquereurs: Personne[]
  confreres: Personne[]
  bien: { numero_mandat?: string | null; numero_dossier?: string | null; titre_bien?: string | null; ville?: string | null;
    agence_nom?: string | null; commercial_nom?: string | null; statut_annonce?: string | null; photo?: string | null } | null
}
export type FicheNotaireBrute = { contact: string; mediane_agence_jours: number | null; dossiers: DossierNotaire[] }

// ─── les règles, en fonctions pures ───────────────────────────────────────────────────────────────────────
const jour = (v: string | null | undefined) => {
  const m = /^(\d{4}-\d{2}-\d{2})/.exec(String(v ?? '').trim())
  return m && !m[1].startsWith('0000') ? m[1] : null
}
const decaler = (j: string, n: number) => {
  const d = new Date(`${j}T12:00:00Z`); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10)
}
const ecart = (a: string, b: string) => Math.round((Date.parse(`${b}T12:00:00Z`) - Date.parse(`${a}T12:00:00Z`)) / 86400000)
const nombre = (v: string | null | undefined) => {
  const n = Number(String(v ?? '').replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(n) ? n : 0
}
const mediane = (xs: number[]) => {
  if (!xs.length) return null
  const s = [...xs].sort((a, b) => a - b); const m = Math.floor(s.length / 2)
  return s.length % 2 ? s[m] : Math.round((s[m - 1] + s[m]) / 2)
}
// ⚠ LES HONORAIRES (décision 4 du 28/10 : commission_agence). Mesure du 28/10 sur les 348 ventes des 12 mois : commission_agence
//   n'est non nulle que sur 82, honoraires_entree sur 330 -- la décision est à reconfirmer (note des types §49.8). Un seul endroit.
export const honorairesDuDossier = (d: Pick<DossierNotaire, 'commission_agence'>) => nombre(d.commission_agence)
const cleDossier = (d: DossierNotaire) => (d.app_chaine_id != null ? `c${d.app_chaine_id}` : `a${d.app_affaire_id}`)

export type EtapeNotaire = 'retractation' | 'acte' | 'a_fixer'
export type DossierEnCours = DossierNotaire & { etape: EtapeNotaire; joursRestants: number | null; acte: string | null; retractation: string | null }
export type VueNotaire = {
  enCours: DossierEnCours[]
  aVerifier: DossierNotaire[]
  ventes12: DossierNotaire[]
  honoraires12: number
  actes30: DossierEnCours[]
  delaiNotaire: number | null
  delaiAgence: number | null
  cotesEnCours: { vendeur: number; acquereur: number; deux: number }
  aVenir: { date: string | null; genre: 'retractation' | 'acte' | 'a_fixer'; dossier: DossierEnCours }[]
  parAgence: { agence: string; n: number }[]
  cotesTous: { vendeur: number; acquereur: number; deux: number }
  confreres: { id: string; nom: string; ville: string; n: number }[]
  partenaireDepuis: string | null
}

export function coteDuDossier(d: Pick<DossierNotaire, 'cotes'>): 'vendeur' | 'acquereur' | 'deux' {
  const v = d.cotes.includes('notaire_vendeur'), a = d.cotes.includes('notaire_acquereur')
  return v && a ? 'deux' : v ? 'vendeur' : 'acquereur'
}

// « aujourdhui » = AAAA-MM-JJ (passé par l'appelant : la fonction ne lit pas l'horloge, elle s'essaie à date fixe)
export function construireVueNotaire(brute: FicheNotaireBrute, aujourdhui: string): VueNotaire {
  const tous = brute.dossiers ?? []
  const vivants = tous.filter((d) => d.kind === 'compromis' && d.state !== 'cancelled' && !jour(d.vente_chaine?.date))
  const enCours: DossierEnCours[] = []
  const aVerifier: DossierNotaire[] = []
  for (const d of vivants) {
    const acte = jour(d.date_acte), signe = jour(d.date), retractation = jour(d.date_fin_retractation)
    const vivant = acte ? acte >= aujourdhui : (signe ? signe >= decaler(aujourdhui, -183) : false)
    if (!vivant) { aVerifier.push(d); continue }
    const etape: EtapeNotaire = retractation && retractation >= aujourdhui ? 'retractation' : acte && acte >= aujourdhui ? 'acte' : 'a_fixer'
    const cible = etape === 'retractation' ? retractation : etape === 'acte' ? acte : null
    enCours.push({ ...d, etape, acte, retractation, joursRestants: cible ? ecart(aujourdhui, cible) : null })
  }
  const ordreEtape = { retractation: 0, acte: 1, a_fixer: 2 } as const
  enCours.sort((a, b) => ordreEtape[a.etape] - ordreEtape[b.etape] || (a.joursRestants ?? 9999) - (b.joursRestants ?? 9999) || b.app_affaire_id - a.app_affaire_id)
  aVerifier.sort((a, b) => String(jour(b.date) ?? '').localeCompare(String(jour(a.date) ?? '')))

  const depuis12 = decaler(aujourdhui, -365)
  const ventes = tous.filter((d) => d.kind === 'vente')
  const ventes12 = ventes.filter((d) => (jour(d.date) ?? '') >= depuis12).sort((a, b) => String(jour(b.date)).localeCompare(String(jour(a.date))))
  const honoraires12 = ventes12.reduce((s, d) => s + honorairesDuDossier(d), 0)
  const depuis3ans = decaler(aujourdhui, -3 * 365)
  const delais = ventes.filter((d) => (jour(d.date) ?? '') >= depuis3ans)
    .map((d) => (jour(d.compromis_chaine) && jour(d.date) ? ecart(jour(d.compromis_chaine)!, jour(d.date)!) : null))
    .filter((x): x is number => x != null && x >= 0 && x <= 400)

  const compte = (liste: { cotes: string[] }[]) => {
    const c = { vendeur: 0, acquereur: 0, deux: 0 }
    for (const d of liste) c[coteDuDossier(d)] += 1
    return c
  }
  const actes30 = enCours.filter((d) => d.acte && d.acte >= aujourdhui && d.acte <= decaler(aujourdhui, 30))
    .sort((a, b) => String(a.acte).localeCompare(String(b.acte)))

  const aVenir: VueNotaire['aVenir'] = []
  for (const d of enCours) {
    if (d.retractation && d.retractation >= aujourdhui) aVenir.push({ date: d.retractation, genre: 'retractation', dossier: d })
    if (d.acte && d.acte >= aujourdhui) aVenir.push({ date: d.acte, genre: 'acte', dossier: d })
    if (!d.acte) aVenir.push({ date: null, genre: 'a_fixer', dossier: d })
  }
  aVenir.sort((a, b) => (a.date ?? '9999').localeCompare(b.date ?? '9999'))

  // « Avec nous » : un DOSSIER = une chaîne (compromis + vente comptent une fois)
  const parChaine = new Map<string, DossierNotaire>()
  for (const d of tous) if (!parChaine.has(cleDossier(d))) parChaine.set(cleDossier(d), d)
  const chaines = [...parChaine.values()]
  const agences = new Map<string, number>()
  for (const d of chaines) { const a = String(d.bien?.agence_nom ?? '').trim() || 'Agence inconnue'; agences.set(a, (agences.get(a) ?? 0) + 1) }
  const parAgence = [...agences.entries()].map(([agence, n]) => ({ agence, n })).sort((a, b) => b.n - a.n || a.agence.localeCompare(b.agence))
  const confs = new Map<string, { id: string; nom: string; ville: string; chaines: Set<string> }>()
  for (const d of tous) for (const c of d.confreres ?? []) {
    if (!c.id) continue
    const e = confs.get(c.id) ?? { id: c.id, nom: c.nom || 'Notaire', ville: c.ville ?? '', chaines: new Set<string>() }
    e.chaines.add(cleDossier(d)); confs.set(c.id, e)
  }
  const confreres = [...confs.values()].map((c) => ({ id: c.id, nom: c.nom, ville: c.ville, n: c.chaines.size }))
    .sort((a, b) => b.n - a.n || a.nom.localeCompare(b.nom)).slice(0, 4)
  const premiers = tous.map((d) => jour(d.date)).filter((x): x is string => !!x).sort()

  return {
    enCours, aVerifier, ventes12, honoraires12, actes30,
    delaiNotaire: mediane(delais), delaiAgence: brute.mediane_agence_jours != null ? Math.round(Number(brute.mediane_agence_jours)) : null,
    cotesEnCours: compte(enCours), aVenir, parAgence, cotesTous: compte(chaines), confreres,
    partenaireDepuis: premiers[0] ?? null,
  }
}

// ─── le chargement ────────────────────────────────────────────────────────────────────────────────────────
export function useFicheNotaire(contactId: string, actif: boolean) {
  const [etat, setEtat] = useState<{ fiche: FicheNotaireBrute | null; erreur: string | null; chargement: boolean }>({ fiche: null, erreur: null, chargement: false })
  useEffect(() => {
    if (!FICHE_NOTAIRE_V2 || !actif || !contactId || !hasSupabaseEnv || !supabase) { setEtat({ fiche: null, erreur: null, chargement: false }); return }
    let vivant = true
    setEtat({ fiche: null, erreur: null, chargement: true })
    supabase.rpc('app_notaire_fiche', { p_contact: contactId }).then(({ data, error }) => {
      if (!vivant) return
      if (error || !data) setEtat({ fiche: null, erreur: error?.message ?? 'fiche notaire indisponible', chargement: false })
      else setEtat({ fiche: data as FicheNotaireBrute, erreur: null, chargement: false })
    })
    return () => { vivant = false }
  }, [contactId, actif])
  return etat
}

// ─── l'affichage ──────────────────────────────────────────────────────────────────────────────────────────
const euros = (v: number | string | null | undefined) => {
  const n = typeof v === 'number' ? v : nombre(v)
  return n > 0 ? `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(n)} €` : '—'
}
const dateFr = (v: string | null | undefined) => { const j = jour(v); return j ? `${j.slice(8, 10)}/${j.slice(5, 7)}/${j.slice(0, 4)}` : '—' }
const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
const noms = (ps: Personne[] | null | undefined) => (ps ?? []).map((p) => p.nom).filter(Boolean).join(', ') || '—'
const libelleCote = (c: 'vendeur' | 'acquereur' | 'deux') => (c === 'deux' ? 'Les deux côtés' : c === 'vendeur' ? 'Côté vendeur' : 'Côté acquéreur')
const refBien = (d: DossierNotaire) => {
  const mandat = d.bien?.numero_mandat || d.numero_mandat
  const t = [d.bien?.titre_bien, d.bien?.ville].filter(Boolean).join(', ')
  return `${mandat ? `Mandat ${mandat}` : d.bien?.numero_dossier || `Annonce ${d.hektor_annonce_id}`}${t ? ` · ${t}` : ''}`
}
const initiales = (nom: string) => nom.split(/\s+/).filter((m) => /^[A-Za-zÀ-ÿ]/.test(m) && !/^(ma[iî]tre|me|office|notarial|etude|étude|de|du|la|le)$/i.test(m))
  .slice(0, 2).map((m) => m[0].toUpperCase()).join('') || 'N'

export function EnConstruction(props: { titre?: string }) {
  return <span className="fa-cx-wip" title="Les données n'existent pas encore : le bloc est montré pour situer la fiche (décision du 27/10)">{props.titre ? `${props.titre} · ` : ''}en construction</span>
}

export function NotaireInterlocuteurs() {
  return (
    <div className="fa-cx-team">
      <div className="fa-cx-team-head">Interlocuteurs de l'étude <EnConstruction /></div>
      <div className="fa-cx-ech-empty">Clercs, formalistes et associés de l'étude : à venir.</div>
    </div>
  )
}

export function NotaireKpis(props: { vue: VueNotaire }) {
  const v = props.vue
  const c = v.cotesEnCours
  const prochain = v.actes30[0]?.acte
  const diff = v.delaiNotaire != null && v.delaiAgence != null ? v.delaiAgence - v.delaiNotaire : null
  return (
    <div className="fa-cx-kpis">
      <div className="fa-cx-kpi" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}><div className="fa-cx-kpi-k">Dossiers en cours</div><div className="fa-cx-kpi-v">{v.enCours.length}</div>
        <div className="fa-cx-kpi-s">{c.vendeur} côté vendeur · {c.acquereur} acquéreur · {c.deux} les deux</div></div>
      <div className="fa-cx-kpi" style={{ ['--sc']: '#c2512a' } as CSSProperties}><div className="fa-cx-kpi-k">Actes ≤ 30 jours</div><div className="fa-cx-kpi-v">{v.actes30.length}</div>
        <div className="fa-cx-kpi-s">{prochain ? `le prochain le ${dateFr(prochain)}` : 'aucun acte prévu'}</div></div>
      <div className="fa-cx-kpi" style={{ ['--sc']: '#1f5b96' } as CSSProperties}><div className="fa-cx-kpi-k">Ventes · 12 mois</div><div className="fa-cx-kpi-v">{v.ventes12.length}<small>· {euros(v.honoraires12)}</small></div>
        <div className="fa-cx-kpi-s">d'honoraires encaissés</div></div>
      <div className="fa-cx-kpi" style={{ ['--sc']: '#2f8a5b' } as CSSProperties}><div className="fa-cx-kpi-k">Compromis → acte</div>
        <div className="fa-cx-kpi-v">{v.delaiNotaire ?? '—'}<small>jours</small></div>
        <div className="fa-cx-kpi-s">{diff == null ? (v.delaiAgence != null ? `médiane de l'agence : ${v.delaiAgence} j` : 'pas assez de ventes') : diff >= 0
          ? <><b>{diff} j plus vite</b> que la médiane ({v.delaiAgence} j)</> : <><b>{-diff} j plus lent</b> que la médiane ({v.delaiAgence} j)</>}</div></div>
    </div>
  )
}

function CarteDossier(props: { d: DossierEnCours | DossierNotaire; onOpenDossier?: (id: number) => void; aVerifier?: boolean }) {
  const [ouvert, setOuvert] = useState(false)
  const d = props.d
  const e = (d as DossierEnCours).etape
  const n = (d as DossierEnCours).joursRestants
  const echeance = props.aVerifier ? `Acte prévu ${dateFr(d.date_acte)} · à vérifier`
    : e === 'retractation' ? `Rétractation J-${n}` : e === 'acte' ? `Acte le ${dateFr(d.date_acte)}` : "Date d'acte à fixer"
  const statut = props.aVerifier ? 'À vérifier' : e === 'acte' ? 'Acte prévu' : 'Compromis'
  const photo = String(d.bien?.photo ?? '').trim()
  return (
    <div className={`fa-cx-dos${ouvert ? ' open' : ''}`}>
      <div className="fa-cx-dos-row" role="button" tabIndex={0} onClick={() => setOuvert(!ouvert)} onKeyDown={(ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); setOuvert(!ouvert) } }}>
        <span className="fa-cx-lk-thumb">{photo && !/no[_-]pic/i.test(photo) ? <img src={photo} alt="" loading="lazy" /> : <span className="rf">Photo</span>}</span>
        <div className="fa-cx-dos-main">
          <div className="fa-cx-dos-ref"><b>{refBien(d)}</b><span className={`fa-cx-lk-stat ${props.aVerifier ? 'muted' : e === 'acte' ? 'ok' : 'warn'}`}>{statut}</span></div>
          <div className="fa-cx-dos-parties">{noms(d.vendeurs)}<i>→</i>{noms(d.acquereurs)}</div>
          <div className="fa-cx-dos-tags">
            <span className="fa-cx-tag side">{libelleCote(coteDuDossier(d))}</span>
            {d.confreres?.length ? <span className="fa-cx-tag face">Face : {noms(d.confreres)}</span> : null}
            {d.bien?.commercial_nom ? <span className="fa-cx-tag">Négo. {d.bien.commercial_nom}</span> : null}
          </div>
        </div>
        <div className="fa-cx-dos-meta">
          <span className="fa-cx-dos-amt">{euros(d.montant)}</span>
          <span className={`fa-cx-dos-due${e === 'acte' ? ' calm' : ''}`}>{echeance}</span>
        </div>
        <span className="fa-cx-dos-chev"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg></span>
      </div>
      {ouvert ? (
        <div className="fa-cx-dos-more">
          <div className="fa-cx-facts">
            <div className="fa-cx-fact"><span className="k">Compromis</span><span className="v">{dateFr(d.date)}</span></div>
            <div className="fa-cx-fact"><span className="k">Fin rétractation</span><span className="v">{dateFr(d.date_fin_retractation)}</span></div>
            <div className="fa-cx-fact"><span className="k">Condition de prêt</span><span className="v"><EnConstruction /></span></div>
            <div className="fa-cx-fact"><span className="k">Acte prévu</span><span className="v">{jour(d.date_acte) ? dateFr(d.date_acte) : 'à fixer'}</span></div>
            {nombre(d.sequestre) > 0 ? <div className="fa-cx-fact"><span className="k">Séquestre</span><span className="v">{euros(d.sequestre)}</span></div> : null}
            <div className="fa-cx-fact"><span className="k">Honoraires</span><span className="v">{euros(honorairesDuDossier(d))}</span></div>
            <div className="fa-cx-fact"><span className="k">Prix net vendeur</span><span className="v">{euros(d.prix_net_vendeur)}</span></div>
          </div>
          <div className="fa-cx-pcs-t">Pièces du dossier <EnConstruction /></div>
          <div className="fa-cx-dos-acts">
            {d.app_dossier_id != null && props.onOpenDossier
              ? <button className="fa-cx-sec-act ghost" type="button" onClick={() => props.onOpenDossier?.(Number(d.app_dossier_id))}>Ouvrir l'annonce</button> : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}

export function NotaireDossiers(props: { vue: VueNotaire; onOpenDossier?: (id: number) => void }) {
  const v = props.vue
  const [filtre, setFiltre] = useState<EtapeNotaire | null>(null)
  const [voirAVerifier, setVoirAVerifier] = useState(false)
  const nb = (e: EtapeNotaire) => v.enCours.filter((d) => d.etape === e).length
  const liste = filtre ? v.enCours.filter((d) => d.etape === filtre) : v.enCours
  const etapes: { e: EtapeNotaire; t: string; c: string }[] = [
    { e: 'retractation', t: 'Rétractation', c: '#c2512a' }, { e: 'acte', t: 'Acte prévu', c: '#3b4a8c' }, { e: 'a_fixer', t: 'Date à fixer', c: '#a8814a' }]
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M6 3h8l4 4v14H6z" /><path d="M14 3v4h4" /></svg></span>
        Dossiers en cours
        <span className="fa-cx-sec-ln" />
        <span className="fa-cx-sec-meta">{v.enCours.length} dossier{v.enCours.length > 1 ? 's' : ''}</span>
      </div>
      <section className="fa-cx-mod full">
        <div className="fa-cx-stages">
          {etapes.map((s) => (
            <button key={s.e} className={`fa-cx-stage${filtre === s.e ? ' on' : ''}`} type="button" style={{ ['--st']: s.c } as CSSProperties}
              onClick={() => setFiltre(filtre === s.e ? null : s.e)}><b>{nb(s.e)}</b><span>{s.t}</span></button>
          ))}
          <span className="fa-cx-stage wip" title="Les conditions suspensives (prêt) ne sont pas encore enregistrées"><b>—</b><span>Conditions <EnConstruction /></span></span>
        </div>
        {liste.length ? liste.map((d) => <CarteDossier key={d.app_affaire_id} d={d} onOpenDossier={props.onOpenDossier} />)
          : <div className="fa-cx-ech-empty">{v.enCours.length ? 'Aucun dossier à cette étape.' : 'Aucun dossier en cours avec ce notaire.'}</div>}
        {v.aVerifier.length ? (
          <div className="fa-cx-averif">
            <button className="fa-cx-lk-more" type="button" onClick={() => setVoirAVerifier(!voirAVerifier)}>
              {voirAVerifier ? 'Replier' : 'Voir'} « À vérifier » · {v.aVerifier.length} compromis sans vente dont l'acte prévu est passé (ou de plus de 6 mois)
            </button>
            {voirAVerifier ? v.aVerifier.map((d) => <CarteDossier key={d.app_affaire_id} d={d} aVerifier onOpenDossier={props.onOpenDossier} />) : null}
          </div>
        ) : null}
      </section>
    </>
  )
}

export function NotaireAVenir(props: { vue: VueNotaire }) {
  const items = props.vue.aVenir.slice(0, 8)
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: '#c2512a' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
        À venir
        <span className="fa-cx-sec-ln" />
        <span className="fa-cx-sec-meta" style={{ ['--sc']: '#c2512a' } as CSSProperties}>{props.vue.aVenir.length}</span>
      </div>
      <section className="fa-cx-mod full">
        <div className="fa-cx-ech-list">
          {items.length ? items.map((it) => {
            const d = it.dossier
            const j = it.date
            return (
              <div key={`${it.genre}-${d.app_affaire_id}`} className={`fa-cx-ech${it.genre === 'acte' ? ' sign' : ''}`}>
                <span className="fa-cx-ech-date"><b>{j ? j.slice(8, 10) : '—'}</b><i>{j ? MOIS[Number(j.slice(5, 7)) - 1] : 'à fixer'}</i></span>
                <div className="fa-cx-ech-bd">
                  <span className="fa-cx-ech-k">{it.genre === 'retractation' ? 'Rétractation' : it.genre === 'acte' ? "Signature d'acte" : "Date d'acte"}</span>
                  <div className="fa-cx-ech-t">{it.genre === 'retractation' ? 'Fin du délai · ' : ''}{noms(d.vendeurs)} → {noms(d.acquereurs)}</div>
                  <div className="fa-cx-ech-s">{[d.bien?.ville, (d.bien?.numero_mandat || d.numero_mandat) ? `mandat ${d.bien?.numero_mandat || d.numero_mandat}` : null].filter(Boolean).join(' · ')}</div>
                </div>
              </div>
            )
          }) : <div className="fa-cx-ech-empty">Rien à venir.</div>}
          <div className="fa-cx-ech-empty">Conditions de prêt : <EnConstruction /></div>
        </div>
      </section>
    </>
  )
}

export function NotaireVentesEtAvecNous(props: { vue: VueNotaire }) {
  const v = props.vue
  const max = Math.max(1, ...v.parAgence.map((a) => a.n))
  const tot = Math.max(1, v.cotesTous.vendeur + v.cotesTous.acquereur + v.cotesTous.deux)
  const pc = (x: number) => Math.round((x / tot) * 100)
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: '#1f5b96' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M5 12.5 10 17 19 7" /></svg></span>
        Ventes signées · 12 mois
        <span className="fa-cx-sec-ln" />
        <span className="fa-cx-sec-meta" style={{ ['--sc']: '#1f5b96' } as CSSProperties}>{v.ventes12.length} vente{v.ventes12.length > 1 ? 's' : ''} · {euros(v.honoraires12)}</span>
        <span className="fa-cx-sec-act ghost"><EnConstruction titre="Exporter" /></span>
      </div>
      <section className="fa-cx-mod full" style={{ ['--sc']: '#1f5b96', marginBottom: 24 } as CSSProperties}>
        {v.ventes12.length ? v.ventes12.map((d) => {
          const delai = jour(d.compromis_chaine) && jour(d.date) ? ecart(jour(d.compromis_chaine)!, jour(d.date)!) : null
          return (
            <div key={d.app_affaire_id} className="fa-cx-lk static r-notaire">
              <span className="fa-cx-lk-thumb">{d.bien?.photo ? <img src={d.bien.photo} alt="" loading="lazy" /> : <span className="rf">Photo</span>}</span>
              <span className="fa-cx-lk-main"><span className="fa-cx-lk-refrow"><span className="fa-cx-lk-ref">{refBien(d)}</span><span className="fa-cx-lk-stat done">Vendu</span></span>
                <span className="fa-cx-lk-t">Acte du {dateFr(d.date)}{delai != null && delai >= 0 ? ` · ${delai} jours après le compromis` : ''}</span></span>
              <span className="fa-cx-lk-meta"><span className="fa-cx-lk-role">{libelleCote(coteDuDossier(d))}</span><span className="fa-cx-lk-amt">{euros(d.montant)}</span></span>
            </div>
          )
        }) : <div className="fa-cx-lk-empty">Aucune vente signée ces 12 derniers mois.</div>}
      </section>
      <div className="fa-cx-duo">
        <div>
          <div className="fa-cx-sec" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}>Avec nous<span className="fa-cx-sec-ln" /></div>
          <section className="fa-cx-mod full">
            <div className="fa-cx-mini-t">Dossiers{v.partenaireDepuis ? ` depuis ${v.partenaireDepuis.slice(0, 4)}` : ''}, par agence</div>
            <div className="fa-cx-bars">
              {v.parAgence.slice(0, 6).map((a) => (
                <div key={a.agence} className="fa-cx-bar-r"><span>{a.agence}</span><span className="t"><span style={{ width: `${Math.round((a.n / max) * 100)}%` }} /></span><b>{a.n}</b></div>
              ))}
            </div>
            <div className="fa-cx-mini-t">Son côté dans nos dossiers</div>
            <div>
              <div className="fa-cx-split"><span style={{ width: `${pc(v.cotesTous.vendeur)}%`, background: '#3b4a8c' }} /><span style={{ width: `${pc(v.cotesTous.acquereur)}%`, background: '#8f9ad0' }} /><span style={{ width: `${pc(v.cotesTous.deux)}%`, background: '#d6dbf1' }} /></div>
              <div className="fa-cx-legend"><span><i style={{ background: '#3b4a8c' }} />vendeur {pc(v.cotesTous.vendeur)} %</span><span><i style={{ background: '#8f9ad0' }} />acquéreur {pc(v.cotesTous.acquereur)} %</span><span><i style={{ background: '#d6dbf1' }} />les deux {pc(v.cotesTous.deux)} %</span></div>
            </div>
          </section>
        </div>
        <div>
          <div className="fa-cx-sec" style={{ ['--sc']: '#a8814a' } as CSSProperties}>Confrères fréquents<span className="fa-cx-sec-ln" /></div>
          <section className="fa-cx-mod full">
            {v.confreres.length ? v.confreres.map((c) => (
              <div key={c.id} className="fa-cx-conf"><span className="fa-cx-mate-av">{initiales(c.nom)}</span><span className="nm">{c.nom}{c.ville ? <small>{c.ville}</small> : null}</span><span className="n">{c.n} dossier{c.n > 1 ? 's' : ''}</span></div>
            )) : <div className="fa-cx-ech-empty">Aucun confrère sur ses dossiers.</div>}
          </section>
        </div>
      </div>
    </>
  )
}
