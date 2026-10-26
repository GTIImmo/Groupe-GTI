// ⛔ 26/10/2026 -- POINT 4 : LA RECHERCHE GLOBALE.
//   Une seule saisie qui cherche partout : annonces en cours, vendues / closes / archivees (lecture
//   seule), contacts, mandats du registre. Cinq lectures en meme temps (lib/api.ts rechercherPartout),
//   memes vues et memes regles d'acces que les listes. Un clic ouvre la fiche par les portes qui
//   existent deja (App.tsx). La derniere recherche est retrouvee a la reouverture.
//   Ergonomie validee par Frederic le 26/10 : notice/AUDIT_NAVIGATION_APRES_ACTION_2026-10-23.md §20.1.
//   Habillage : la charte bienvu (en-tete encre + filet magenta, comme les modales « Pilotage »).
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { RECHERCHE_GLOBALE_LIGNES, rechercherPartout, type AppFilters, type DataScope, type RechercheGlobaleResultat } from './lib/api'
import type { AppContact, Dossier, MandatRecord } from './types'
import './recherche-globale.css'

export type GroupeRecherche = 'annonces' | 'horsCatalogue' | 'contacts' | 'mandats'

type Element =
  | { groupe: 'annonces'; cle: string; annonce: Dossier }
  | { groupe: 'horsCatalogue'; cle: string; annonce: Dossier }
  | { groupe: 'contacts'; cle: string; contact: AppContact }
  | { groupe: 'mandats'; cle: string; mandat: MandatRecord }

// La derniere recherche survit a la fermeture de la fenetre (recommandation 5), pas au rechargement.
let derniereRecherche: { saisie: string; resultat: RechercheGlobaleResultat | null } = { saisie: '', resultat: null }

const TITRES: Record<GroupeRecherche, string> = {
  annonces: 'Annonces en cours',
  horsCatalogue: 'Vendues, closes, archivées',
  contacts: 'Contacts',
  mandats: 'Mandats',
}

const PICTOS: Record<GroupeRecherche, ReactNode> = {
  annonces: <path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" />,
  horsCatalogue: <><rect x="3" y="4" width="18" height="5" rx="1" /><path d="M5 9v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9M10 13h4" /></>,
  contacts: <><circle cx="12" cy="8" r="4" /><path d="M4 20c1.5-3.5 4.5-5 8-5s6.5 1.5 8 5" /></>,
  mandats: <><path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></>,
}

function Picto({ groupe }: { groupe: GroupeRecherche }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.9} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{PICTOS[groupe]}</svg>
}

// L'ordre suit ce qui est tape (recommandation 2) : un telephone ou un e-mail cherche une personne,
// un numero cherche un bien ou un mandat.
function ordreDesGroupes(saisie: string): GroupeRecherche[] {
  const t = saisie.trim()
  const chiffres = t.replace(/\D/g, '')
  if (t.includes('@') || (/^\+?[\d\s.]+$/.test(t) && chiffres.length >= 8)) return ['contacts', 'annonces', 'horsCatalogue', 'mandats']
  if (/^\d+$/.test(t) || /^[A-Za-z]{1,3}\d{3,}$/.test(t)) return ['annonces', 'mandats', 'horsCatalogue', 'contacts']
  return ['annonces', 'horsCatalogue', 'contacts', 'mandats']
}

// Le mot tape, surligne dans le titre (insensible a la casse et aux accents).
function sansAccent(v: string) {
  return v.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}
function Surligne({ texte, terme }: { texte: string; terme: string }) {
  const t = sansAccent(terme.trim())
  if (t.length < 2) return <>{texte}</>
  const i = sansAccent(texte).indexOf(t)
  if (i < 0) return <>{texte}</>
  return <>{texte.slice(0, i)}<mark>{texte.slice(i, i + t.length)}</mark>{texte.slice(i + t.length)}</>
}

type Ton = 'ok' | 'warn' | 'rose' | 'neutre'
function pastilleStatut(d: Dossier): { libelle: string; ton: Ton } {
  if (String(d.archive ?? '') === '1') return { libelle: 'Archivée', ton: 'neutre' }
  const s = String(d.statut_annonce ?? '').trim()
  if (/^actif/i.test(s)) return { libelle: s, ton: 'ok' }
  if (/offre|compromis/i.test(s)) return { libelle: s, ton: 'warn' }
  if (/estimation/i.test(s)) return { libelle: s, ton: 'rose' }
  return { libelle: s || '—', ton: 'neutre' }
}

function lieu(ville?: string | null, cp?: string | null) {
  return [ville, cp].map((v) => String(v ?? '').trim()).filter(Boolean).join(' ')
}

function rolesContact(c: AppContact) {
  const brut = (c as { relation_roles_json?: unknown }).relation_roles_json
  let roles: string[] = []
  try {
    const v = typeof brut === 'string' ? JSON.parse(brut) : brut
    if (Array.isArray(v)) roles = v.map((x) => String(x))
  } catch { /* liste illisible : rien */ }
  const noms: Record<string, string> = { mandant: 'Mandant', proprietaire: 'Propriétaire', acquereur: 'Acquéreur', acquereur_offre: 'Acquéreur', acquereur_compromis: 'Acquéreur', acquereur_vente: 'Acquéreur' }
  return Array.from(new Set(roles.map((r) => noms[r] ?? '').filter(Boolean))).join(' · ')
}

function initiales(nom: string) {
  const mots = nom.replace(/^(M\.|Mme\.?|Mr\.?\/Mme|Mr\.?|Mlle\.?)\s+/i, '').split(/\s+/).filter(Boolean)
  return ((mots[0]?.[0] ?? '') + (mots[1]?.[0] ?? '')).toUpperCase() || '?'
}

// L'adresse (26/10, index poses) : on la montre, pour que l'agent voie pourquoi la ligne est sortie.
function adresseDe(objet: unknown) {
  const x = objet as { adresse_detail?: string | null; adresse?: string | null }
  return String(x.adresse_detail ?? x.adresse ?? '').trim()
}

function photoDe(a: Dossier) {
  const x = a as { photo_url_listing_app?: string | null; photo_url_listing?: string | null }
  return String(x.photo_url_listing_app || x.photo_url_listing || '').trim() || null
}

export default function RechercheGlobale(props: {
  ouverte: boolean
  filtresDeBase: AppFilters
  scope?: DataScope | null
  onFermer: () => void
  onOuvrirAnnonce: (annonce: Dossier) => void
  onOuvrirHorsCatalogue: (annonce: Dossier) => void
  onOuvrirContact: (contactId: string) => void
  onOuvrirMandat: (mandat: MandatRecord) => void
  onVoirTout: (groupe: GroupeRecherche, terme: string) => void
}) {
  const [saisie, setSaisie] = useState(derniereRecherche.saisie)
  const [resultat, setResultat] = useState<RechercheGlobaleResultat | null>(derniereRecherche.resultat)
  const [chargement, setChargement] = useState(false)
  const [actif, setActif] = useState(0)
  const champRef = useRef<HTMLInputElement | null>(null)
  const listeRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!props.ouverte) return
    window.setTimeout(() => { champRef.current?.focus(); champRef.current?.select() }, 0)
  }, [props.ouverte])

  // 300 ms apres la derniere frappe, a partir de 3 caracteres (la regle des listes).
  useEffect(() => {
    if (!props.ouverte) return
    const terme = saisie.trim()
    if (terme.length < 3) {
      setResultat(null)
      setChargement(false)
      derniereRecherche = { saisie, resultat: null }
      return
    }
    if (derniereRecherche.resultat && derniereRecherche.saisie === saisie) {
      setResultat(derniereRecherche.resultat)
      return
    }
    let annule = false
    setChargement(true)
    const minuteur = window.setTimeout(() => {
      rechercherPartout({
        terme,
        filtresDeBase: props.filtresDeBase,
        scope: props.scope,
        // Chaque groupe s'affiche des qu'il arrive (mesure du 26/10 : annonces ~0,3 s, mandats ~1,1 s).
        surGroupe: (partiel) => { if (!annule) setResultat(partiel) },
      })
        .then((r) => {
          if (annule) return
          setResultat(r)
          setActif(0)
          derniereRecherche = { saisie, resultat: r }
        })
        .catch(() => { if (!annule) setResultat({ terme, annonces: [], horsCatalogue: [], contacts: [], mandats: [], echecs: ['toutes'] }) })
        .finally(() => { if (!annule) setChargement(false) })
    }, 300)
    return () => { annule = true; window.clearTimeout(minuteur) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [saisie, props.ouverte])

  const groupes = useMemo(() => ordreDesGroupes(saisie), [saisie])
  const montres = RECHERCHE_GLOBALE_LIGNES - 1
  const elements = useMemo<Element[]>(() => {
    if (!resultat) return []
    const liste: Element[] = []
    for (const g of groupes) {
      if (g === 'annonces') resultat.annonces.slice(0, montres).forEach((a) => liste.push({ groupe: g, cle: `a-${a.app_dossier_id}`, annonce: a }))
      if (g === 'horsCatalogue') resultat.horsCatalogue.slice(0, montres).forEach((a) => liste.push({ groupe: g, cle: `h-${a.hektor_annonce_id}`, annonce: a }))
      if (g === 'contacts') resultat.contacts.slice(0, montres).forEach((c) => liste.push({ groupe: g, cle: `c-${c.hektor_contact_id}`, contact: c }))
      if (g === 'mandats') resultat.mandats.slice(0, montres).forEach((m, i) => liste.push({ groupe: g, cle: `m-${m.register_row_id ?? i}`, mandat: m }))
    }
    return liste
  }, [resultat, groupes, montres])

  useEffect(() => {
    const el = listeRef.current?.querySelector<HTMLElement>(`[data-rg-index="${actif}"]`)
    el?.scrollIntoView({ block: 'nearest' })
  }, [actif])

  if (!props.ouverte) return null

  const ouvrir = (e: Element) => {
    props.onFermer()
    if (e.groupe === 'annonces') props.onOuvrirAnnonce(e.annonce)
    else if (e.groupe === 'horsCatalogue') props.onOuvrirHorsCatalogue(e.annonce)
    else if (e.groupe === 'contacts') props.onOuvrirContact(String(e.contact.hektor_contact_id))
    else props.onOuvrirMandat(e.mandat)
  }

  const surTouche = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') { event.preventDefault(); props.onFermer(); return }
    if (event.key === 'ArrowDown') { event.preventDefault(); setActif((i) => Math.min(i + 1, Math.max(elements.length - 1, 0))); return }
    if (event.key === 'ArrowUp') { event.preventDefault(); setActif((i) => Math.max(i - 1, 0)); return }
    if (event.key === 'Enter' && elements[actif]) { event.preventDefault(); ouvrir(elements[actif]) }
  }

  const terme = saisie.trim()
  const termeOk = terme.length >= 3
  const rien = termeOk && !chargement && resultat && elements.length === 0

  const vignette = (e: Element) => {
    if (e.groupe === 'annonces' || e.groupe === 'horsCatalogue') {
      const photo = photoDe(e.annonce)
      return (
        <span className={`rg-vignette${e.groupe === 'horsCatalogue' ? ' is-passe' : ''}`}>
          {photo ? <img src={photo} alt="" loading="lazy" /> : <Picto groupe={e.groupe} />}
        </span>
      )
    }
    if (e.groupe === 'contacts') return <span className="rg-avatar">{initiales(String(e.contact.display_name ?? ''))}</span>
    return <span className="rg-vignette is-doc"><Picto groupe="mandats" /></span>
  }

  const contenu = (e: Element) => {
    if (e.groupe === 'annonces' || e.groupe === 'horsCatalogue') {
      const a = e.annonce
      const pastille = pastilleStatut(a)
      const mandants = String((a as { mandants_texte?: string | null }).mandants_texte ?? '').trim()
      return {
        titre: String(a.titre_bien ?? '').trim() || 'Sans titre',
        ref: a.numero_dossier || `n° ${a.hektor_annonce_id}`,
        detail: [adresseDe(a), lieu(a.ville, a.code_postal), mandants, a.commercial_nom].filter(Boolean).join(' · '),
        pastille,
      }
    }
    if (e.groupe === 'contacts') {
      const c = e.contact
      const archive = String(c.archive) === 'true'
      return {
        titre: String(c.display_name ?? '').trim() || `Contact ${c.hektor_contact_id}`,
        ref: rolesContact(c),
        detail: [(c as { phone_primary?: string | null }).phone_primary, c.email, adresseDe(c), c.ville].filter(Boolean).join(' · '),
        pastille: archive ? { libelle: 'Archivé', ton: 'neutre' as Ton } : null,
      }
    }
    const m = e.mandat
    return {
      titre: `Mandat ${m.numero_mandat ?? '—'}`,
      ref: m.numero_dossier ?? '',
      detail: [adresseDe(m), m.titre_bien, m.mandants_texte].filter(Boolean).join(' · '),
      pastille: m.mandat_type ? { libelle: String(m.mandat_type), ton: 'rose' as Ton } : null,
    }
  }

  return (
    <div className="rg-fond" onMouseDown={(event) => { if (event.target === event.currentTarget) props.onFermer() }}>
      <div className="rg-fenetre" role="dialog" aria-modal="true" aria-label="Rechercher partout" onKeyDown={surTouche}>
        <header className="rg-tete">
          <div className="rg-tete-ligne">
            <p className="rg-surtitre">Rechercher partout</p>
            <button type="button" className="rg-fermer" onClick={props.onFermer} aria-label="Fermer">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
            </button>
          </div>
          <label className="rg-champ">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" /><path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
            <input
              ref={champRef}
              value={saisie}
              onChange={(event) => setSaisie(event.target.value)}
              placeholder="Un nom, un numéro, une adresse, un téléphone…"
              aria-label="Rechercher partout"
            />
            {saisie ? <button type="button" className="rg-effacer" onClick={() => { setSaisie(''); champRef.current?.focus() }}>Effacer</button> : null}
          </label>
          <span className={`rg-progres${chargement ? ' is-actif' : ''}`} aria-hidden="true" />
        </header>

        <div className="rg-resultats" ref={listeRef}>
          {!termeOk ? (
            <div className="rg-vide">
              <strong>Retrouver un bien ou un client, d'une seule frappe</strong>
              <span>Dossier, mandat, n° Hektor, adresse, ville, mandant, nom, téléphone ou e-mail — dès 3 caractères.</span>
              <div className="rg-perimetre">
                {(['annonces', 'horsCatalogue', 'contacts', 'mandats'] as GroupeRecherche[]).map((g) => (
                  <span key={g}><Picto groupe={g} />{TITRES[g]}</span>
                ))}
              </div>
            </div>
          ) : null}
          {termeOk && chargement && !resultat ? <p className="rg-attente">Recherche en cours…</p> : null}
          {rien ? (
            <div className="rg-vide">
              <strong>Rien pour « {terme} »</strong>
              <span>Ni dans les annonces (archives comprises), ni dans les contacts, ni dans les mandats. Essaie une partie du nom, ou le numéro.</span>
            </div>
          ) : null}
          {resultat && termeOk && resultat.echecs.length ? <p className="rg-echec">Une partie n'a pas pu être lue ({resultat.echecs.join(', ')}). Les autres résultats sont bien là.</p> : null}
          {resultat && termeOk ? groupes.map((g) => {
            const lignes = elements.filter((e) => e.groupe === g)
            if (!lignes.length) return null
            const plus = resultat[g].length > montres
            return (
              <section key={g} className={`rg-groupe rg-groupe-${g}`}>
                <h3>
                  <Picto groupe={g} />
                  <span>{TITRES[g]}</span>
                  {g === 'horsCatalogue' ? <em>lecture seule</em> : null}
                  <b>{plus ? `${montres}+` : lignes.length}</b>
                </h3>
                {lignes.map((e) => {
                  const index = elements.indexOf(e)
                  const c = contenu(e)
                  return (
                    <button
                      key={e.cle}
                      type="button"
                      className={`rg-ligne${index === actif ? ' is-actif' : ''}`}
                      data-rg-index={index}
                      onMouseEnter={() => setActif(index)}
                      onClick={() => ouvrir(e)}
                    >
                      {vignette(e)}
                      <span className="rg-corps">
                        <span className="rg-titre">
                          <Surligne texte={c.titre} terme={terme} />
                          {c.ref ? <span className="rg-ref"><Surligne texte={String(c.ref)} terme={terme} /></span> : null}
                        </span>
                        {c.detail ? <span className="rg-detail"><Surligne texte={c.detail} terme={terme} /></span> : null}
                      </span>
                      {c.pastille ? <span className={`rg-pastille is-${c.pastille.ton}`}>{c.pastille.libelle}</span> : null}
                      <span className="rg-entree" aria-hidden="true">↵</span>
                    </button>
                  )
                })}
                {plus ? (
                  <button type="button" className="rg-voir-tout" onClick={() => { props.onFermer(); props.onVoirTout(g, terme) }}>
                    Voir tout dans {g === 'contacts' ? 'Contacts' : g === 'mandats' ? 'Mandats' : 'Annonces'}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
                  </button>
                ) : null}
              </section>
            )
          }) : null}
        </div>

        <footer className="rg-pied">
          {[['↑', '↓', 'choisir'], ['↵', '', 'ouvrir'], ['Échap', '', 'fermer'], ['/', '', 'rouvrir de partout']].map(([a, b, l]) => (
            <span key={l}><kbd>{a}</kbd>{b ? <kbd>{b}</kbd> : null}{l}</span>
          ))}
        </footer>
      </div>
    </div>
  )
}

