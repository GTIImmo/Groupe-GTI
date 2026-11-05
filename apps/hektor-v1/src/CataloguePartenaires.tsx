// CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.5 (05/11/2026) — LE CATALOGUE DES MÉTIERS (côté « Partenaires » de l'annuaire).
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §26 quater ; maquette planche 1 (Main.dc.html), sans l'aperçu
// de droite (ses chiffres n'existent pas encore) ni les tuiles « Administrations » / « à classer » (règle du 05/11).
// LECTURE SEULE : le registre `app_partenaire_metier`, les fiches `app_contact_current`. Un clic lit la fiche COMPLÈTE du
// contact et la rend à l'écran Contacts, qui l'ouvre avec `ouverture='catalogue_metiers'` (la liste des clients ne
// connaît pas ces contacts : on ne passe jamais par elle). Une lecture ratée est DITE, jamais un catalogue vide.
import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import {
  LIBELLE_METIER_CATALOGUE, METIERS_DU_CATALOGUE, TUILES_CATALOGUE, construireCatalogue, filtrerCatalogue,
  type Catalogue, type ContactCatalogue, type TuileCatalogue,
} from './lib/cataloguePartenaires'
import type { AppContact } from './types'
import './catalogue-partenaires.css'

const COLONNES = 'hektor_contact_id,civilite,prenom,nom,display_name,archive,ville,phone_primary,email'
const PAGE = 1000

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
  // Les notaires : la règle actuelle (celle de la fiche notaire et du filtre « Notaire »), les deux côtés de la table des parties.
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

export default function CataloguePartenaires(props: { onOuvrir: (contact: AppContact) => void }) {
  const [etat, setEtat] = useState<{ etat: 'chargement' | 'pret' | 'erreur'; catalogue?: Catalogue; erreur?: string }>({ etat: 'chargement' })
  const [version, setVersion] = useState(0)
  const [tuile, setTuile] = useState<TuileCatalogue>('notaire')
  const [requete, setRequete] = useState('')
  const [voirArchives, setVoirArchives] = useState(false)
  const [ouverture, setOuverture] = useState<{ id: string; erreur?: string } | null>(null)

  useEffect(() => {
    let annule = false
    setEtat((avant) => (avant.catalogue ? avant : { etat: 'chargement' }))
    lireCatalogue()
      .then((catalogue) => { if (!annule) setEtat({ etat: 'pret', catalogue }) })
      .catch((e) => { if (!annule) setEtat({ etat: 'erreur', erreur: e instanceof Error ? e.message : String(e) }) })
    return () => { annule = true }
  }, [version])

  const choix = TUILES_CATALOGUE.find((t) => t.tuile === tuile) ?? TUILES_CATALOGUE[0]
  const liste = etat.catalogue?.[tuile]
  const actifs = useMemo(() => filtrerCatalogue(liste?.actifs ?? [], requete), [liste, requete])
  const archives = useMemo(() => filtrerCatalogue(liste?.archives ?? [], requete), [liste, requete])

  async function ouvrir(id: string) {
    if (!supabase || ouverture) return
    setOuverture({ id })
    const { data, error } = await supabase.from('app_contact_current').select('*').eq('hektor_contact_id', id).maybeSingle()
    if (error || !data) { setOuverture({ id, erreur: error?.message ?? 'fiche introuvable' }); return }
    setOuverture(null)
    props.onOuvrir(data as AppContact)
  }

  const rangee = (l: { id: string; nom: string; detail: string; metiers: string[]; archive: boolean }) => (
    <li key={l.id}>
      <button type="button" className={`cat-row${l.archive ? ' archive' : ''}`} onClick={() => { void ouvrir(l.id) }} disabled={Boolean(ouverture)}>
        <span className="cat-av" aria-hidden="true">{l.nom.split(/\s+/).filter(Boolean).slice(0, 2).map((m) => m[0]).join('').toUpperCase()}</span>
        <span className="cat-who">
          <span className="cat-name">{l.nom}</span>
          <span className="cat-detail">{l.detail || '—'}</span>
        </span>
        {tuile !== 'notaire' ? <span className="cat-tags">{l.metiers.map((m) => <span key={m} className="cat-tag">{LIBELLE_METIER_CATALOGUE[m] ?? m}</span>)}</span> : null}
        {l.archive ? <span className="cat-arch">Archivé</span> : null}
        <span className="cat-go" aria-hidden="true">{ouverture?.id === l.id && !ouverture.erreur ? '…' : '›'}</span>
      </button>
    </li>
  )

  return (
    <div className="cat-partenaires" style={{ ['--cat']: choix.couleur } as CSSProperties}>
      <div className="cat-head">
        <div>
          <h1>Partenaires</h1>
          <p>Les professionnels qui font avancer nos affaires, rangés par métier.</p>
        </div>
      </div>

      {etat.etat === 'erreur' ? (
        <div className="cat-error" role="alert">
          Le catalogue n'a pas pu être lu ({etat.erreur}). <button type="button" onClick={() => setVersion((v) => v + 1)}>Réessayer</button>
        </div>
      ) : null}

      <div className="cat-tiles" role="tablist" aria-label="Métiers">
        {TUILES_CATALOGUE.map((t) => {
          const c = etat.catalogue?.[t.tuile]
          return (
            <button key={t.tuile} type="button" role="tab" aria-selected={tuile === t.tuile}
              className={`cat-tile${tuile === t.tuile ? ' on' : ''}`} style={{ ['--tc']: t.couleur } as CSSProperties}
              onClick={() => { setTuile(t.tuile); setVoirArchives(false) }}>
              <span className="cat-tile-n">{c ? c.actifs.length : '…'}</span>
              <span className="cat-tile-l">{t.libelle}</span>
              <span className="cat-tile-s">{c && c.archives.length ? `${t.sous} · ${c.archives.length} archivé${c.archives.length > 1 ? 's' : ''}` : t.sous}</span>
            </button>
          )
        })}
      </div>

      <div className="cat-list">
        <div className="cat-list-head">
          <h2>{choix.libelle}</h2>
          <label className="cat-search">
            <span className="cat-sr">Rechercher dans {choix.libelle.toLowerCase()}</span>
            <input type="search" value={requete} onChange={(e) => setRequete(e.target.value)} placeholder="Nom, ville, téléphone…" />
          </label>
        </div>
        {ouverture?.erreur ? <div className="cat-error" role="alert">La fiche n'a pas pu être ouverte ({ouverture.erreur}). <button type="button" onClick={() => setOuverture(null)}>Fermer</button></div> : null}
        {etat.etat === 'chargement' && !etat.catalogue ? <div className="cat-empty">Chargement du catalogue…</div> : null}
        {etat.catalogue ? (
          <>
            {actifs.length ? <ul className="cat-rows">{actifs.map(rangee)}</ul>
              : <div className="cat-empty">{requete ? 'Aucun partenaire actif ne correspond à cette recherche.' : 'Aucun partenaire actif dans ce métier.'}</div>}
            {archives.length ? (
              <div className="cat-archives">
                <button type="button" className="cat-archives-btn" aria-expanded={voirArchives} onClick={() => setVoirArchives((v) => !v)}>
                  {voirArchives ? 'Masquer' : 'Voir'} les archivés ({archives.length})
                </button>
                {voirArchives ? <ul className="cat-rows">{archives.map(rangee)}</ul> : null}
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  )
}
