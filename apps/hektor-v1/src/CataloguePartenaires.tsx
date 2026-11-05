// CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.5 (05/11/2026) — LE CATALOGUE DES MÉTIERS (côté « Partenaires » de l'annuaire).
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §26 quater à sexies. ⭐ Dessin = la maquette VALIDÉE le 04/11
// (planche 1, Main.dc.html) : en-tête « Clients | Partenaires » + recherche + « Ajouter un partenaire », grand titre, tuiles
// à icône (la choisie se remplit de sa couleur), liste en cartes, aperçu à droite, filtre Agence. Adaptations dites à
// Frédéric (« oui », 05/11) : police et couleurs de l'app (celles des fiches) ; l'ACTIVITÉ avec l'agence n'existe pas
// encore → montrée « en construction » (colonne, anneau, chiffres, dernières affaires), tri par nom ; ni « Administrations »
// ni « fiches à classer » (règle du 05/11 : cinq métiers et c'est tout).
// LECTURE SEULE : le registre `app_partenaire_metier`, les fiches `app_contact_current`. « Ouvrir la fiche » lit la fiche
// COMPLÈTE et la rend à l'écran Contacts, qui l'ouvre avec `ouverture='catalogue_metiers'` (la liste des clients ne
// connaît pas ces contacts). Une lecture ratée est DITE, jamais un catalogue vide.
import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import {
  LIBELLE_METIER_CATALOGUE, METIERS_DU_CATALOGUE, TUILES_CATALOGUE, construireCatalogue, filtrerCatalogue,
  type Catalogue, type ContactCatalogue, type LigneCatalogue, type TuileCatalogue,
} from './lib/cataloguePartenaires'
import type { AppContact } from './types'
import './catalogue-partenaires.css'

const COLONNES = 'hektor_contact_id,civilite,prenom,nom,display_name,archive,ville,phone_primary,email,agence_nom'
const PAGE = 1000
const TOUTES = ''

async function lireCatalogue(): Promise<Catalogue> {
  if (!hasSupabaseEnv || !supabase) throw new Error('base indisponible')
  const reg = await supabase.from('app_partenaire_metier').select('contact_id,metier').is('retire_le', null).in('metier', METIERS_DU_CATALOGUE)
  if (reg.error) throw new Error(reg.error.message)
  const registre = (reg.data ?? []) as { contact_id: string; metier: string }[]
  const ids = Array.from(new Set(registre.map((r) => String(r.contact_id))))
  const contacts: ContactCatalogue[] = []
  for (let i = 0; i < ids.length; i += 200) {
    const r = await supabase.from('app_contact_current').select(COLONNES).in('hektor_contact_id', ids.slice(i, i + 200))
    if (r.error) throw new Error(r.error.message)
    contacts.push(...((r.data ?? []) as ContactCatalogue[]))
  }
  // Les notaires : la règle actuelle (celle de la fiche notaire), les deux côtés de la table des parties.
  const notaires: ContactCatalogue[] = []
  for (let debut = 0; ; debut += PAGE) {
    const r = await supabase.from('app_contact_current').select(COLONNES)
      .or(['notaire_vendeur', 'notaire_acquereur'].map((v) => `relation_roles_json.cs.${JSON.stringify([v])}`).join(','))
      .order('hektor_contact_id').range(debut, debut + PAGE - 1)
    if (r.error) throw new Error(r.error.message)
    const lot = (r.data ?? []) as ContactCatalogue[]
    notaires.push(...lot)
    if (lot.length < PAGE) break
  }
  return construireCatalogue(registre, contacts, notaires)
}

const Ico = (props: { d: string; size?: number; width?: number }) => (
  <svg width={props.size ?? 18} height={props.size ?? 18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={props.width ?? 2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={props.d} /></svg>
)
const initiales = (nom: string) => nom.split(/\s+/).filter((m) => /^[A-Za-zÀ-ÿ]/.test(m)).slice(0, 2).map((m) => m[0]).join('').toUpperCase() || '•'
const Wip = (props: { children?: ReactNode }) => <span className="pa-wip" title="Les données n'existent pas encore : la place est montrée (décision du 27/10)">{props.children ?? 'en construction'}</span>

export default function CataloguePartenaires(props: {
  onOuvrir: (contact: AppContact) => void
  onVueClients: () => void
  onAjouter?: () => void
}) {
  const [etat, setEtat] = useState<{ etat: 'chargement' | 'pret' | 'erreur'; catalogue?: Catalogue; erreur?: string }>({ etat: 'chargement' })
  const [version, setVersion] = useState(0)
  const [tuile, setTuile] = useState<TuileCatalogue>('notaire')
  const [requete, setRequete] = useState('')
  const [agence, setAgence] = useState(TOUTES)
  const [voirArchives, setVoirArchives] = useState(false)
  const [choisi, setChoisi] = useState<string | null>(null)
  const [ouverture, setOuverture] = useState<{ id: string; erreur?: string } | null>(null)

  useEffect(() => {
    let annule = false
    setEtat((avant) => (avant.catalogue ? avant : { etat: 'chargement' }))
    lireCatalogue()
      .then((catalogue) => { if (!annule) setEtat({ etat: 'pret', catalogue }) })
      .catch((e) => { if (!annule) setEtat({ etat: 'erreur', erreur: e instanceof Error ? e.message : String(e) }) })
    return () => { annule = true }
  }, [version])

  const cur = TUILES_CATALOGUE.find((t) => t.tuile === tuile) ?? TUILES_CATALOGUE[0]
  const liste = etat.catalogue?.[tuile]
  const agences = useMemo(() => Array.from(new Set([...(liste?.actifs ?? []), ...(liste?.archives ?? [])].map((l) => l.agence).filter(Boolean)))
    .sort((a, b) => a.localeCompare(b, 'fr')), [liste])
  const parAgence = (ls: LigneCatalogue[]) => (agence ? ls.filter((l) => l.agence === agence) : ls)
  const actifs = filtrerCatalogue(parAgence(liste?.actifs ?? []), requete)
  const archives = filtrerCatalogue(parAgence(liste?.archives ?? []), requete)
  const sel = choisi ? [...actifs, ...archives].find((l) => l.id === choisi) ?? null : null

  function choisirTuile(t: TuileCatalogue) {
    setTuile(t); setVoirArchives(false); setChoisi(null); setAgence(TOUTES)
  }

  async function ouvrir(id: string) {
    if (!supabase || ouverture) return
    setOuverture({ id })
    const { data, error } = await supabase.from('app_contact_current').select('*').eq('hektor_contact_id', id).maybeSingle()
    if (error || !data) { setOuverture({ id, erreur: error?.message ?? 'fiche introuvable' }); return }
    setOuverture(null)
    props.onOuvrir(data as AppContact)
  }

  const metiersDe = (l: LigneCatalogue) => (tuile === 'notaire' ? ['Notaire'] : l.metiers.map((m) => LIBELLE_METIER_CATALOGUE[m] ?? m))
  const carte = (l: LigneCatalogue, i: number) => (
    <li key={l.id}>
      <button type="button" className={`pa-row${choisi === l.id ? ' on' : ''}${l.archive ? ' archive' : ''}`} style={{ animationDelay: `${Math.min(i, 12) * 40}ms` }}
        aria-pressed={choisi === l.id} onClick={() => setChoisi(l.id)} onDoubleClick={() => { void ouvrir(l.id) }}>
        <span className="pa-av" aria-hidden="true">{initiales(l.nom)}</span>
        <span className="pa-who">
          <span className="pa-name">{l.nom}</span>
          <span className="pa-sub">{metiersDe(l).join(' · ')} · {l.detail}</span>
        </span>
        <span className="pa-stat">
          <span className="pa-stat-v">—</span>
          <span className="pa-stat-s">activité avec l'agence</span>
        </span>
        <span className="pa-end">
          {l.archive ? <span className="pa-chip arch">Archivé</span> : null}
          <span className="pa-chip">{metiersDe(l)[0]}</span>
          <Ico d="m9 6 6 6-6 6" size={16} width={2.4} />
        </span>
      </button>
    </li>
  )

  return (
    <div className="pa-cat" style={{ ['--c']: cur.couleur, ['--s']: cur.doux } as CSSProperties}>
      <header className="pa-header">
        <div className="pa-top">
          <div className="pa-switch" role="group" aria-label="Côté de l'annuaire">
            <button type="button" aria-pressed="false" onClick={props.onVueClients}>Clients</button>
            <button type="button" aria-pressed="true">Partenaires</button>
          </div>
          <div className="pa-spacer" />
          <label className="pa-search">
            <Ico d="M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4" size={17} />
            <input aria-label="Chercher un partenaire" placeholder="Nom, ville, téléphone, e-mail…" value={requete} onChange={(e) => setRequete(e.target.value)} />
          </label>
          {props.onAjouter ? (
            <button type="button" className="pa-add" onClick={props.onAjouter}><Ico d="M12 5v14M5 12h14" size={16} width={2.6} />Ajouter un partenaire</button>
          ) : null}
        </div>
        <div className="pa-title">
          <h1>Partenaires</h1>
          <p>Les professionnels qui font avancer nos affaires, rangés par métier.</p>
        </div>
        {etat.etat === 'erreur' ? (
          <div className="pa-error" role="alert">Le catalogue n'a pas pu être lu ({etat.erreur}). <button type="button" onClick={() => setVersion((v) => v + 1)}>Réessayer</button></div>
        ) : null}
        <div className="pa-tiles" role="tablist" aria-label="Métiers">
          {TUILES_CATALOGUE.map((t) => {
            const c = etat.catalogue?.[t.tuile]
            return (
              <button key={t.tuile} type="button" role="tab" aria-selected={tuile === t.tuile} className={`pa-tile${tuile === t.tuile ? ' on' : ''}`}
                style={{ ['--tc']: t.couleur, ['--ts']: t.doux } as CSSProperties} onClick={() => choisirTuile(t.tuile)}>
                <span className="pa-tile-top">
                  <span className="pa-tile-ic"><Ico d={t.icone} /></span>
                  <span className="pa-tile-n">{c ? c.actifs.length : '…'}</span>
                </span>
                <span className="pa-tile-l">{t.libelle}</span>
                <span className="pa-tile-s">{c && c.archives.length ? `${t.sous} · ${c.archives.length} archivé${c.archives.length > 1 ? 's' : ''}` : t.sous}</span>
              </button>
            )
          })}
        </div>
      </header>

      <div className="pa-body">
        <section className="pa-list" aria-label="Liste des partenaires">
          <div className="pa-list-head">
            <span className="pa-list-l">{cur.libelle}</span>
            <span>· triés par nom (l'activité avec l'agence est <Wip />)</span>
            <div className="pa-spacer" />
            {agences.length ? (
              <label className="pa-agence"><span>Agence</span>
                <select aria-label="Agence" value={agence} onChange={(e) => { setAgence(e.target.value); setChoisi(null) }}>
                  <option value={TOUTES}>Toutes</option>
                  {agences.map((a) => <option key={a} value={a}>{a}</option>)}
                </select>
              </label>
            ) : null}
          </div>
          {ouverture?.erreur ? <div className="pa-error" role="alert">La fiche n'a pas pu être ouverte ({ouverture.erreur}). <button type="button" onClick={() => setOuverture(null)}>Fermer</button></div> : null}
          {etat.etat === 'chargement' && !etat.catalogue ? <div className="pa-empty">Chargement du catalogue…</div> : null}
          {etat.catalogue ? (
            <>
              {actifs.length ? <ul className="pa-rows">{actifs.map(carte)}</ul>
                : <div className="pa-empty">{requete || agence ? 'Aucun partenaire actif ne correspond.' : 'Aucun partenaire actif dans ce métier.'}</div>}
              {archives.length ? (
                <div className="pa-archives">
                  <button type="button" className="pa-archives-btn" aria-expanded={voirArchives} onClick={() => setVoirArchives((v) => !v)}>
                    {voirArchives ? 'Masquer' : 'Voir'} les archivés ({archives.length})
                  </button>
                  {voirArchives ? <ul className="pa-rows">{archives.map(carte)}</ul> : null}
                </div>
              ) : null}
            </>
          ) : null}
        </section>

        {sel ? (
          <aside className="pa-panel" aria-label="Aperçu du partenaire" key={sel.id}>
            <div className="pa-band">
              <div className="pa-band-top">
                <span className="pa-band-chip">{cur.libelle}</span>
                <button type="button" aria-label="Fermer l'aperçu" onClick={() => setChoisi(null)}><Ico d="M18 6 6 18M6 6l12 12" size={14} width={2.4} /></button>
              </div>
              <div className="pa-band-id">
                <svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="28" fill="none" stroke="rgba(255,255,255,.22)" strokeWidth="6" /><text x="32" y="37" textAnchor="middle" fill="#fff" fontSize="15" fontWeight="800">—</text></svg>
                <div>
                  <div className="pa-band-name">{sel.nom}</div>
                  <div className="pa-band-who">{metiersDe(sel).join(' · ')}{sel.ville ? ` · ${sel.ville}` : ''}</div>
                  <div className="pa-band-act">Activité avec l'agence sur 12 mois · en construction</div>
                </div>
              </div>
              <div className="pa-band-actions">
                {sel.telephone ? <a className="primary" href={`tel:${sel.telephone.replace(/\s+/g, '')}`}><Ico d="M4 5a2 2 0 0 1 2-2h2.5l1.5 4-2 1.5a12 12 0 0 0 5 5l1.5-2 4 1.5V18a2 2 0 0 1-2 2A15 15 0 0 1 4 5Z" size={15} width={2.2} />Appeler</a>
                  : <span className="primary off" title="Pas de téléphone sur la fiche">Appeler</span>}
                {sel.email ? <a href={`mailto:${sel.email}`}>Écrire</a> : <span className="off" title="Pas d'e-mail sur la fiche">Écrire</span>}
                <span className="off" title="Le RDV se crée depuis la fiche (« Ouvrir la fiche »)">RDV</span>
              </div>
            </div>
            <div className="pa-panel-body">
              <div className="pa-kpis">
                {['affaires ensemble', 'en cours', 'délai moyen'].map((l) => <div key={l} className="pa-kpi"><div className="v">—</div><div className="l">{l}</div></div>)}
              </div>
              <div className="pa-recent">
                <h2>Dernières affaires ensemble <Wip /></h2>
                <p>Les affaires menées ensemble viendront avec le lot du métier.</p>
              </div>
              {sel.ville || sel.agence ? (
                <div className="pa-places">
                  {sel.ville ? <span>{sel.ville}</span> : null}
                  {sel.agence ? <span>{sel.agence}</span> : null}
                </div>
              ) : null}
              <button type="button" className="pa-cta" disabled={Boolean(ouverture)} onClick={() => { void ouvrir(sel.id) }}>
                {ouverture?.id === sel.id && !ouverture.erreur ? 'Ouverture…' : `Ouvrir la fiche ${cur.court}`}<Ico d="m9 6 6 6-6 6" size={15} width={2.4} />
              </button>
            </div>
          </aside>
        ) : (
          <aside className="pa-panel-empty" aria-label="Aperçu du partenaire">Choisissez un partenaire pour voir sa fiche en aperçu.</aside>
        )}
      </div>
    </div>
  )
}
