// CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.1 (06/11/2026) — LA FICHE SYNDIC REMPLIE, EN LECTURE SEULE.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §27 ; règles pures : lib/ficheSyndic.ts.
// Remplace, sur une fiche SYNDIC ouverte depuis le catalogue, les blocs « en construction » de 3.3b par ce qui EXISTE déjà :
// nos biens chez ce syndic (liens repris de Hektor chaque nuit), leur copropriété (lots, charges, fonds de travaux,
// procédure, plan de sauvegarde) et les documents de copropriété du bien (reconnus par leur nom, en attendant la GED).
// Restent « en construction » : les demandes et leur délai (4.4), les assemblées générales (4.5), l'immeuble (4.3).
// AUCUNE écriture. Les lectures suivent les droits de chacun (périmètre). Une lecture ratée est DITE, jamais un vide.
import { useEffect, useState, type CSSProperties } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import { construireVueSyndic, type BienSyndic, type VueSyndic } from './lib/ficheSyndic'
import { EnConstruction } from './FicheNotaire'
import './fiche-syndic.css'

const COLONNES_BIEN = 'hektor_annonce_id,numero_mandat,titre_bien,ville,statut_annonce,photo_url_listing_app,photo_url_listing'

async function lireBiens(table: string, champ: 'app_dossier_id' | 'hektor_annonce_id', ids: string[], avecDossier: boolean): Promise<Record<string, unknown>[]> {
  if (!supabase || !ids.length) return []
  const r = await supabase.from(table).select(avecDossier ? `app_dossier_id,${COLONNES_BIEN}` : COLONNES_BIEN).in(champ, ids)
  if (r.error) throw new Error(`${table} : ${r.error.message}`)
  return ((r.data ?? []) as unknown as Record<string, unknown>[]).map((b) => ({ ...b, photo: b.photo_url_listing_app || b.photo_url_listing || null }))
}

// Lot 5 (06/11) : la même lecture sert au diagnostiqueur (role='diagnostiqueur').
// 09/11 (§28.10) : l'app doit marcher Hektor coupé -> le bien, son détail et ses documents se lisent par NOTRE numéro
// (`app_dossier_id`, porté par chaque lien). Le numéro Hektor, déjà chez nous, ne sert plus qu'aux biens sortis du parc
// vivant (vendus / clos / archivés : leurs index n'ont que lui) et à un lien qui n'aurait pas le nôtre (0 le 09/11).
async function lireVueSyndic(contactId: string, role: 'syndic' | 'diagnostiqueur' = 'syndic'): Promise<VueSyndic> {
  if (!hasSupabaseEnv || !supabase) throw new Error('base indisponible')
  const l = await supabase.from('app_partenaire_lien').select('hektor_annonce_id,app_dossier_id')
    .eq('partenaire_id', contactId).eq('role', role).is('retire_le', null)
  if (l.error) throw new Error(`liens : ${l.error.message}`)
  const liens = (l.data ?? []) as { hektor_annonce_id: number | null; app_dossier_id: number | null }[]
  const unique = (v: (number | null)[]) => Array.from(new Set(v.map((x) => String(x ?? '')).filter(Boolean)))
  const dossiers = unique(liens.map((x) => x.app_dossier_id))
  if (!dossiers.length && !liens.some((x) => x.hektor_annonce_id)) return construireVueSyndic({ liens, biens: [], details: [], documents: [] })
  // Le bien : le parc vivant par notre numéro d'abord, puis les index des archives par le numéro Hektor (comme la fiche notaire).
  const vivants = await lireBiens('app_dossiers_current', 'app_dossier_id', dossiers, true)
  const vus = new Set(vivants.map((b) => String(b.app_dossier_id)))
  const reste = unique(liens.filter((x) => !vus.has(String(x.app_dossier_id ?? ''))).map((x) => x.hektor_annonce_id))
  const archives = await lireBiens('app_archive_annonce_index_current', 'hektor_annonce_id', reste, false)
  const trouves = new Set(archives.map((b) => String(b.hektor_annonce_id)))
  const historiques = await lireBiens('app_historical_annonce_index_current', 'hektor_annonce_id', reste.filter((id) => !trouves.has(id)), false)
  const lire = async <T,>(table: string, colonnes: string, quoi: string): Promise<T[]> => {
    const lignes: T[] = []
    for (const [champ, ids] of [['app_dossier_id', dossiers], ['hektor_annonce_id', reste]] as const) {
      if (!ids.length) continue
      const r = await supabase!.from(table).select(colonnes).in(champ, ids)
      if (r.error) throw new Error(`${quoi} : ${r.error.message}`)
      lignes.push(...((r.data ?? []) as unknown as T[]))
    }
    return lignes
  }
  const details = await lire<{ hektor_annonce_id: number | null; app_dossier_id: number | null; detail_payload_json: unknown }>(
    'app_dossier_detail_current', 'app_dossier_id,hektor_annonce_id,detail_payload_json', 'détail des biens')
  const documents = await lire<{ hektor_annonce_id: string | null; app_dossier_id: number | null; document_name: string | null }>(
    'app_console_document', 'app_dossier_id,hektor_annonce_id,document_name', 'documents')
  return construireVueSyndic({ liens, biens: [...vivants, ...archives, ...historiques], details, documents })
}

export function useFicheSyndic(contactId: string, actif: boolean, role: 'syndic' | 'diagnostiqueur' = 'syndic') {
  const [etat, setEtat] = useState<{ vue: VueSyndic | null; erreur: string | null; chargement: boolean }>({ vue: null, erreur: null, chargement: actif })
  useEffect(() => {
    if (!actif || !contactId.trim()) { setEtat({ vue: null, erreur: null, chargement: false }); return }
    let annule = false
    setEtat((e) => ({ ...e, chargement: true, erreur: null }))
    lireVueSyndic(contactId.trim(), role)
      .then((vue) => { if (!annule) setEtat({ vue, erreur: null, chargement: false }) })
      .catch((e) => { if (!annule) setEtat({ vue: null, erreur: e instanceof Error ? e.message : String(e), chargement: false }) })
    return () => { annule = true }
  }, [contactId, actif, role])
  return etat
}

const euros = (n: number | null | undefined) => (n == null ? null : `${new Intl.NumberFormat('fr-FR').format(n)} €`)

export function SyndicChiffres(props: { vue: VueSyndic | null }) {
  const v = props.vue
  const kpi = (titre: string, valeur: string, sous: string, couleur: string, wip = false) => (
    <div className="fa-cx-kpi" key={titre} style={{ ['--sc']: couleur } as CSSProperties}>
      <div className="fa-cx-kpi-k">{titre}</div>
      <div className="fa-cx-kpi-v">{valeur}</div>
      <div className="fa-cx-kpi-s">{wip ? <EnConstruction titre={sous} /> : sous}</div>
    </div>
  )
  return (
    <div className="fa-cx-kpis">
      {kpi('Nos biens chez lui', v ? String(v.biens.length) : '…', v && v.avecDocuments ? `${v.avecDocuments} avec des documents de copro` : 'en copropriété, syndic posé chez Hektor', 'var(--ty)')}
      {kpi('Demandes ouvertes', '—', '4.4', '#c2512a', true)}
      {kpi('Biens en vente', v ? String(v.enVente) : '…', 'actifs, sous offre ou sous compromis', '#1f5b96')}
      {kpi('Charges moyennes', v?.quotePartMoyenne != null ? euros(v.quotePartMoyenne) ?? '—' : '—', 'quote-part annuelle de nos lots', '#2f8a5b')}
    </div>
  )
}

function CarteBien(props: { bien: BienSyndic; onOuvrir?: (id: number) => void; diag?: boolean }) {
  const b = props.bien
  const c = b.copro
  const puces: string[] = []
  if (c?.lots != null) puces.push(`${c.lots} lots dans l'immeuble`)
  if (c?.quotePart != null && c.quotePart > 0) puces.push(`${euros(c.quotePart)} de charges / an`)
  if (c?.fondsTravaux != null && c.fondsTravaux > 0) puces.push(`fonds de travaux ${euros(c.fondsTravaux)}`)
  const ouvrable = Boolean(props.onOuvrir && b.appDossierId)
  const contenu = (
    <>
      <span className="sy-thumb">{b.photo ? <img src={b.photo} alt="" loading="lazy" onError={(e) => { e.currentTarget.style.display = 'none' }} /> : <span>Photo</span>}</span>
      <span className="sy-main">
        <span className="sy-top">
          <span className="sy-titre">{b.titre}</span>
          <span className={`sy-statut${b.enVente ? ' vente' : ''}`}>{b.statut}</span>
        </span>
        <span className="sy-sous">{[b.ville, b.mandat ? `mandat ${b.mandat}` : null, c?.numerosLots ? `lot ${c.numerosLots}` : null].filter(Boolean).join(' · ') || '—'}</span>
        {props.diag ? (
          <span className="sy-puces">{b.annee ? <span className="sy-puce">construit en {b.annee}</span> : <span className="sy-puce vide">année de construction non renseignée</span>}</span>
        ) : <>
        <span className="sy-puces">
          {puces.map((p) => <span key={p} className="sy-puce">{p}</span>)}
          {c?.procedure === 'en_cours' ? <span className="sy-puce alerte">procédure en cours</span> : null}
          {c?.planSauvegarde ? <span className="sy-puce alerte">plan de sauvegarde</span> : null}
          {!c ? <span className="sy-puce vide">copropriété non renseignée chez Hektor</span> : null}
        </span>
        {b.documents.length ? (
          <span className="sy-docs" title="Reconnus par leur nom, en attendant le classement des documents (chantier GED)">
            {b.documents.slice(0, 4).map((d) => <span key={d} className="sy-doc">{d}</span>)}
            {b.documents.length > 4 ? <span className="sy-doc plus">+{b.documents.length - 4}</span> : null}
          </span>
        ) : <span className="sy-docs"><span className="sy-doc manque">aucun document de copropriété au coffre</span></span>}
        </>}
      </span>
    </>
  )
  return ouvrable
    ? <button type="button" className="sy-bien" onClick={() => props.onOuvrir?.(b.appDossierId as number)}>{contenu}</button>
    : <div className="sy-bien">{contenu}</div>
}

export function SyndicCoproprietes(props: { vue: VueSyndic | null; erreur: string | null; chargement: boolean; onOuvrirBien?: (id: number) => void }) {
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round"><path d="M3 11l9-7 9 7v9H3z" /><path d="M10 20v-6h4v6" /></svg></span>
        Copropriétés
        <span className="fa-cx-sec-meta">{props.vue ? `${props.vue.biens.length} bien${props.vue.biens.length > 1 ? 's' : ''}` : ''}</span>
        <span className="fa-cx-sec-ln" />
      </div>
      <section className="fa-cx-mod full" style={{ marginBottom: 24 }}>
        {props.erreur ? <div className="fa-cx-ech-empty fa-cx-err">Copropriétés illisibles pour le moment ({props.erreur}).</div>
          : props.chargement && !props.vue ? <div className="fa-cx-ech-empty">Chargement des copropriétés…</div>
          : props.vue && props.vue.biens.length ? (
            <div className="sy-biens">{props.vue.biens.map((b) => <CarteBien key={b.cle} bien={b} onOuvrir={props.onOuvrirBien} />)}</div>
          ) : <div className="fa-cx-ech-empty">Aucun de nos biens n'est relié à ce syndic chez Hektor (liste « Syndic » de l'annonce).</div>}
        <div className="sy-note">Un bien = sa copropriété, en attendant le regroupement par immeuble (pièce 4.3) <EnConstruction titre="4.3" /></div>
      </section>
    </>
  )
}

export function SyndicNosBiens(props: { vue: VueSyndic | null }) {
  const v = props.vue
  const vendus = v ? v.biens.filter((b) => /vendu/i.test(b.statut)).length : 0
  const autres = v ? v.biens.length - v.enVente - vendus : 0
  return (
    <div className="fa-cx-duo">
      <div>
        <div className="fa-cx-sec" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}>
          <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M4 19V9M10 19V5M16 19v-7M22 19H2" /></svg></span>
          Nos biens dans ses copropriétés<span className="fa-cx-sec-ln" />
        </div>
        <section className="fa-cx-mod full">
          {v ? (
            <div className="sy-repart">
              <div><b>{v.enVente}</b><span>en vente</span></div>
              <div><b>{vendus}</b><span>vendus</span></div>
              <div><b>{Math.max(0, autres)}</b><span>autres (clos, estimation…)</span></div>
            </div>
          ) : <div className="fa-cx-ech-empty">…</div>}
        </section>
      </div>
      <div>
        <div className="fa-cx-sec" style={{ ['--sc']: '#a8814a' } as CSSProperties}>
          <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M4 19V9M10 19V5M16 19v-7M22 19H2" /></svg></span>
          Demandes et délais<EnConstruction titre="4.4" /><span className="fa-cx-sec-ln" />
        </div>
        <section className="fa-cx-mod full"><div className="fa-cx-ech-empty">pré-état daté, PV d'assemblée, carnet d'entretien : ce qu'on demande et en combien de jours</div></section>
      </div>
    </div>
  )
}

// LOT 5 (06/11/2026) — la fiche DIAGNOSTIQUEUR, version simple : ses biens (liens du registre) ; le reste « en construction ».
export function DiagChiffres(props: { vue: VueSyndic | null }) {
  const v = props.vue
  const kpi = (titre: string, valeur: string, sous: string, couleur: string, wip = false) => (
    <div className="fa-cx-kpi" key={titre} style={{ ['--sc']: couleur } as CSSProperties}>
      <div className="fa-cx-kpi-k">{titre}</div>
      <div className="fa-cx-kpi-v">{valeur}</div>
      <div className="fa-cx-kpi-s">{wip ? <EnConstruction titre={sous} /> : sous}</div>
    </div>
  )
  return (
    <div className="fa-cx-kpis">
      {kpi('Nos biens avec lui', v ? String(v.biens.length) : '…', 'diagnostiqueur posé sur le bien', 'var(--ty)')}
      {kpi('Biens en vente', v ? String(v.enVente) : '…', 'actifs, sous offre ou sous compromis', '#1f5b96')}
      {kpi('Commandes en cours', '—', 'suivi des commandes', '#c2512a', true)}
      {kpi('DPE à renouveler', '—', 'DPE qui expire', '#2f8a5b', true)}
    </div>
  )
}

export function DiagBiens(props: { vue: VueSyndic | null; erreur: string | null; chargement: boolean; onOuvrirBien?: (id: number) => void }) {
  return (
    <>
      <div className="fa-cx-sec" style={{ ['--sc']: 'var(--ty)' } as CSSProperties}>
        <span className="fa-cx-sec-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round"><path d="M9 11l3 3 8-8" /><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9" /></svg></span>
        Biens diagnostiqués
        <span className="fa-cx-sec-meta">{props.vue ? `${props.vue.biens.length} bien${props.vue.biens.length > 1 ? 's' : ''}` : ''}</span>
        <span className="fa-cx-sec-ln" />
      </div>
      <section className="fa-cx-mod full" style={{ marginBottom: 24 }}>
        {props.erreur ? <div className="fa-cx-ech-empty fa-cx-err">Biens illisibles pour le moment ({props.erreur}).</div>
          : props.chargement && !props.vue ? <div className="fa-cx-ech-empty">Chargement des biens…</div>
          : props.vue && props.vue.biens.length ? (
            <div className="sy-biens">{props.vue.biens.map((b) => <CarteBien key={b.cle} bien={b} onOuvrir={props.onOuvrirBien} diag />)}</div>
          ) : <div className="fa-cx-ech-empty">Aucun de nos biens n'est relié à ce diagnostiqueur : choisissez-le sur la fiche d'un bien (onglet Contact).</div>}
        <div className="sy-note">Les commandes et leur suivi, le DPE qui expire : plus tard <EnConstruction titre="lot 5" /></div>
      </section>
    </>
  )
}
