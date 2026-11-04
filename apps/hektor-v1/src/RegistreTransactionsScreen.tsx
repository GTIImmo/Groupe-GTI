import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  bienEstDansLesAnnonces, createConsoleDocumentSignedUrl, createPrepareConsoleDocumentJob, loadBienHistoriquePourStatut, loadConsoleDocuments,
  loadDossierDeLaChaine, loadHistoriqueDuDossier, loadNomsNegociateurs, loadRegistreDossiers, loadRepartitionsDesChaines,
  type AffaireLedgerRow, type AffairePartieRow, type DossierDeLaChaine, type HistoriqueDossierLigne, type RegistreDossierRow, type RegistreEtape, type RepartitionLigne,
} from './lib/api'
import { compterRepartitions, construireRepereDepuisRegistre, lireRegistre, lireRepartitions, type RepereNegos } from './lib/pilotage'
import { partDe } from './lib/repartitionEffective'
import type { ConsoleDocument } from './types'
import './registre-transactions.css'

// Registre des transactions -- étape « écran liste » (01/11/2026), derrière l'interrupteur
// `registre_transactions_ecran`. Une ligne = un DOSSIER (offre -> compromis -> vente).
// Étape 4 (02/11/2026) : un clic ouvre la FICHE DU DOSSIER (lecture), et ses boutons ouvrent la
// fenêtre de statut EXISTANTE sur la bonne transaction -- l'écran n'écrit rien lui-même.
// Les gestes ne sont proposés que si le bien est encore dans les annonces : un dossier vendu se
// modifie à l'étape 4C (note § 10).
// Maquette : https://claude.ai/artifact/3FA3yDqWuDWuqLdZAkvS8x · note : notice/AUDIT_GESTES_REGISTRE_TRANSACTIONS_2026-10-30.md § 8-10.
// ⛔ Aucun mot « Hektor » à l'écran (décision du 30/10) ; une lecture ratée se dit, sans détail technique.

export type GesteDuRegistre = { onglet: 'offre' | 'compromis' | 'vente'; appAffaireId: number | null; hektorAffaireId?: string | null }

type RegistreTransactionsScreenProps = {
  isAdmin: boolean
  libelleTypeBien?: (code: string | null | undefined) => string
  /** La fiche du bien : vivante, ou par le détail gardé d'un bien vendu ou clos. */
  onOuvrirBien?: (ligne: RegistreDossierRow) => void
  /** Ouvre la fenêtre de statut sur ce bien, cet onglet et cette transaction. Absent = pas de geste. */
  onGeste?: (ligne: RegistreDossierRow, geste: GesteDuRegistre) => void
  /** Vrai tant que la fenêtre de statut est ouverte : à sa fermeture, la liste et la fiche se relisent. */
  fenetreOuverte?: boolean
  onOuvrirContact?: (contactId: string) => void
}

const ETAPES: Array<{ cle: RegistreEtape; libelle: string }> = [
  { cle: 'offre_proposee', libelle: 'Offre proposée' },
  { cle: 'offre_acceptee', libelle: 'Offre acceptée' },
  { cle: 'compromis', libelle: 'Compromis' },
  { cle: 'vendu', libelle: 'Vendu' },
  { cle: 'compromis_annule', libelle: 'Compromis annulé' },
  { cle: 'offre_refusee', libelle: 'Offre refusée' },
]
const LIBELLE_ETAPE = Object.fromEntries(ETAPES.map((etape) => [etape.cle, etape.libelle])) as Record<RegistreEtape, string>
const EN_COURS: RegistreEtape[] = ['offre_proposee', 'offre_acceptee', 'compromis']
const OFFRES: RegistreEtape[] = ['offre_proposee', 'offre_acceptee']

const PAR_PAGE = 50
const ANNEE_COURANTE = new Date().getFullYear()
const ANNEES = Array.from({ length: ANNEE_COURANTE - 2006 + 1 }, (_, index) => ANNEE_COURANTE - index)
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']

type Tri = 'recent' | 'prix' | 'honoraires'
type Sens = 'desc' | 'asc'
// « offres » (v3.1) = offre proposée + offre acceptée : le filtre de la carte « Offres en cours ».
type FiltreEtape = RegistreEtape | 'en_cours' | 'offres' | null

// ─── Icônes au trait (maquette v3.1, mêmes tracés) : constantes, jamais de donnée ───
const TRACES = {
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  left: '<path d="m15 6-6 6 6 6"/>', right: '<path d="m9 6 6 6-6 6"/>', down: '<path d="m6 9 6 6 6-6"/>',
  horloge: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  coche: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  stylo: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13 7 4 4"/>',
  cle: '<circle cx="8" cy="15" r="4"/><path d="m11 12 8.5-8.5M16 7l2.5 2.5M13.5 9.5l2 2"/>',
  croix: '<path d="M7 7l10 10M17 7 7 17"/>',
  barre: '<circle cx="12" cy="12" r="8.5"/><path d="m6 6 12 12"/>',
  alerte: '<path d="M10.3 4.2 2.6 18a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z"/><path d="M12 9.5V14M12 17.5h.01"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
  maison: '<path d="M3.5 11 12 4l8.5 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/>',
  immeuble: '<rect x="5" y="3.5" width="14" height="17" rx="1.5"/><path d="M9 7.5h2M13 7.5h2M9 11h2M13 11h2M9 14.5h2M13 14.5h2M10.5 20.5v-3h3v3"/>',
  terrain: '<path d="M3 19h18"/><path d="m5 19 4.5-7 3 4 2-2.5L19 19"/><path d="M15 4v6M15 4h4.5L18 5.75 19.5 7.5H15"/>',
  ouvrir: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
  crayon: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
  calendrier: '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M8 3v4M16 3v4M3.5 10h17"/>',
  personnes: '<circle cx="9" cy="8.5" r="3.2"/><path d="M3 19.5c.7-3.3 3.1-5 6-5s5.3 1.7 6 5"/><path d="M15.5 5.5a3.2 3.2 0 0 1 0 6M17.5 14.6c1.6.7 2.8 2.3 3.3 4.9"/>',
  corbeille: '<path d="M4.5 7h15M10 7V4.5h4V7M6.5 7l1 13h9l1-13"/>',
  note: '<path d="M5 4h10l4 4v12H5z"/><path d="M15 4v4h4M9 12.5h6M9 16h4"/>',
  doc: '<path d="M6 3.5h8.5L18 7v13.5H6z"/><path d="M9 11h6M9 14.5h6M9 18h3.5"/>',
  agence: '<path d="M4 9.5 5.5 4h13L20 9.5"/><path d="M4 9.5a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0"/><path d="M5.5 11.5v9h13v-9M10 20.5v-5h4v5"/>',
  trier: '<path d="M7 4v16M3.5 7.5 7 4l3.5 3.5M17 20V4M13.5 16.5 17 20l3.5-3.5"/>',
  rafraichir: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4.5V11h-6.5"/>',
  filtre: '<path d="M4 5h16l-6 7.5V19l-4 1.5v-8z"/>',
  flHaut: '<path d="M12 19V5M6 11l6-6 6 6"/>', flBas: '<path d="M12 5v14M6 13l6 6 6-6"/>', flDeux: '<path d="M8 9l4-4 4 4M8 15l4 4 4-4"/>',
  // v4 (fiche) : prix, net vendeur, honoraires, notaire, conditions
  euro: '<path d="M18 7a6.5 6.5 0 1 0 0 10M4.5 10.5h9M4.5 13.5h8"/>',
  porte: '<path d="M20 12V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h7"/><path d="m16 19 2 2 4-4M8 10h8M8 14h5"/>',
  camembert: '<path d="M20.5 15.5A9 9 0 1 1 8.5 3.7"/><path d="M21 12a9 9 0 0 0-9-9v9z"/>',
  balance: '<path d="M12 4v16M8 20h8M5 7.5h14M5 7.5 2.5 13a2.6 2.6 0 0 0 5 0zM19 7.5 16.5 13a2.6 2.6 0 0 0 5 0z"/>',
  liste: '<path d="M9 6.5h11M9 12h11M9 17.5h11M4.5 6.5h.01M4.5 12h.01M4.5 17.5h.01"/>',
} as const
type NomIcone = keyof typeof TRACES

function Ic({ n, className }: { n: NomIcone; className?: string }) {
  return (
    <svg
      className={`ic${className ? ` ${className}` : ''}`}
      viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true" focusable="false"
      dangerouslySetInnerHTML={{ __html: TRACES[n] }}
    />
  )
}

// Le symbole bienvu (toit + coche) : fixe pour l'état vide, animé pour le chargement.
function Logo({ anime = false }: { anime?: boolean }) {
  return (
    <svg className={anime ? 'ld' : 'logo'} viewBox="0 0 28 28" aria-hidden="true" focusable="false">
      <path className={anime ? 'ld-toit' : undefined} d="M3 13 L14 4 L25 13" fill="none" stroke="currentColor" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" />
      <path className={anime ? 'ld-coche' : undefined} d="M8 16 L12.5 20.5 L21 11" fill="none" stroke="#c5005f" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" pathLength={100} />
    </svg>
  )
}

function Chargement({ texte, lignes }: { texte: string; lignes: number[] }) {
  return (
    <>
      <span className="v3-loader"><Logo anime /><span>{texte}</span></span>
      <span className="v3-sk" aria-hidden="true">
        {lignes.map((largeur, index) => <span key={index} className="sk" style={{ width: `${largeur}%` }} />)}
      </span>
    </>
  )
}

const ICONE_ETAPE: Record<RegistreEtape, NomIcone> = {
  offre_proposee: 'horloge', offre_acceptee: 'coche', compromis: 'stylo', vendu: 'cle', compromis_annule: 'barre', offre_refusee: 'croix',
}

function Pastille({ etape }: { etape: RegistreEtape }) {
  return <span className={`rt-pastille is-${etape}`}><Ic n={ICONE_ETAPE[etape]} />{LIBELLE_ETAPE[etape]}</span>
}

// Un sélecteur dessiné : icône à gauche, chevron à droite (le menu reste le menu natif).
function Selecteur({ icone, children }: { icone: NomIcone; children: ReactNode }) {
  return <span className="v3-sel"><Ic n={icone} className="ic-g" />{children}<Ic n="down" className="ic-d" /></span>
}

/** Le pictogramme du type de bien, pour la vignette « sans photo ». */
function iconeDuType(libelle: string | null | undefined): NomIcone {
  const texte = String(libelle ?? '')
  return /appart|immeuble|studio|loft|duplex/i.test(texte) ? 'immeuble' : /terrain/i.test(texte) ? 'terrain' : 'maison'
}

const MOTS_SANS_INITIALE = new Set(['m.', 'm', 'mme', 'mlle', 'me', 'mr', 'mrs', 'm_mme', 'mm.', 'et', '&', 'indivision', 'monsieur', 'madame', 'maître', 'maitre'])

/** Les initiales d'un nom (« Léa Brunon » -> « LB », « Me Lionel SANIAL » -> « LS »). */
function initiales(nom: string | null | undefined) {
  const mots = String(nom ?? '').split(/[\s,]+/).filter((mot) => mot && !MOTS_SANS_INITIALE.has(mot.toLowerCase()))
  const lettre = (mot: string) => (mot.match(/\p{L}/u)?.[0] ?? '')
  if (!mots.length) return '?'
  const premiere = lettre(mots[0])
  const seconde = mots.length > 1 ? lettre(mots[mots.length - 1]) : (mots[0].match(/\p{L}/gu)?.[1] ?? '')
  return (premiere + seconde).toUpperCase() || '?'
}

// ─── Mémoire de l'écran (v3.1) : gardée dans le navigateur, l'écran marche sans ───
const CLE_MEMOIRE = 'bienvu-registre-transactions'
type Memoire = { annee: number | null; mois: string; etape: FiltreEtape; tri: Tri; sens: Sens; nomme: boolean; agence: string; nego: string }
const MEMOIRE_DEFAUT: Memoire = { annee: ANNEE_COURANTE, mois: '', etape: null, tri: 'recent', sens: 'desc', nomme: false, agence: '', nego: '' }
const FILTRES_VALIDES = new Set<string>(['en_cours', 'offres', ...ETAPES.map((etape) => etape.cle)])

function lireMemoire(): Memoire {
  try {
    const brut = JSON.parse(window.localStorage.getItem(CLE_MEMOIRE) ?? 'null') as Partial<Record<keyof Memoire, unknown>> | null
    if (!brut || typeof brut !== 'object') return MEMOIRE_DEFAUT
    const annee = brut.annee === null ? null : Number(brut.annee)
    const mois = String(brut.mois ?? '')
    return {
      annee: annee === null ? null : ANNEES.includes(annee) ? annee : MEMOIRE_DEFAUT.annee,
      mois: /^(?:[1-9]|1[0-2])$/.test(mois) ? mois : '',
      etape: typeof brut.etape === 'string' && FILTRES_VALIDES.has(brut.etape) ? (brut.etape as FiltreEtape) : null,
      tri: brut.tri === 'prix' || brut.tri === 'honoraires' ? brut.tri : 'recent',
      sens: brut.sens === 'asc' ? 'asc' : 'desc',
      nomme: brut.nomme === true,
      agence: typeof brut.agence === 'string' ? brut.agence : '',
      nego: typeof brut.nego === 'string' ? brut.nego : '',
    }
  } catch {
    return MEMOIRE_DEFAUT
  }
}

function ecrireMemoire(memoire: Memoire) {
  try {
    window.localStorage.setItem(CLE_MEMOIRE, JSON.stringify(memoire))
  } catch {
    /* stockage indisponible : l'écran marche sans */
  }
}

const euros = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
const entier = new Intl.NumberFormat('fr-FR')
const dateParis = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris' })

function formatEuros(valeur: number | null | undefined) {
  return valeur == null || Number.isNaN(valeur) ? '—' : euros.format(valeur)
}

function formatMillions(valeur: number) {
  if (Math.abs(valeur) >= 1_000_000) return `${(valeur / 1_000_000).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} M€`
  if (Math.abs(valeur) >= 10_000) return `${Math.round(valeur / 1000).toLocaleString('fr-FR')} k€`
  return euros.format(valeur)
}

// Les dates du registre sont du TEXTE, en plusieurs formes : « 2026-01-05 », « 2019-12-30 23:00:00 »
// (minuit à Paris écrit en UTC), « 2026-11-01T04:24:59Z », et « 0000-00-00 » pour une date vide.
function dateEnClair(valeur: string | null | undefined): string | null {
  const texte = String(valeur ?? '').trim()
  if (!texte || texte.startsWith('0000')) return null
  if (texte.length <= 10) {
    const [annee, mois, jour] = texte.split('-')
    return annee && mois && jour ? `${jour}/${mois}/${annee}` : texte
  }
  const iso = texte.replace(' ', 'T')
  const date = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  return Number.isNaN(date.getTime()) ? texte.slice(0, 10) : dateParis.format(date)
}

function anneeDe(valeur: string | null | undefined) {
  const texte = String(valeur ?? '').trim()
  return texte && !texte.startsWith('0000') ? Number(texte.slice(0, 4)) : null
}

function sansAccents(texte: string) {
  return texte.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

function nomPart(ligne: RepartitionLigne) {
  const nom = (ligne.nomAuMoment ?? '').trim()
  if (!nom) return 'Sans nom'
  if (/supprim/i.test(nom)) return 'Compte supprimé'
  return nom
}

// « Mme. Sandrine DELAVAUD » -> « S. DELAVAUD » : la colonne Répartition de la liste n'a la place
// que pour un nom court ; le nom complet reste au survol.
function nomCourt(nom: string) {
  const mots = nom.replace(/^(m_mme|mr\.?\/mme\.?|mme\.?|mlle\.?|mr\.?|m\.)\s+/i, '').trim().split(/\s+/)
  if (mots.length < 2 || nom === 'Sans nom' || nom === 'Compte supprimé') return mots.join(' ')
  return `${mots[0].charAt(0).toUpperCase()}. ${mots.slice(1).join(' ')}`
}

function Repartition({ lignes }: { lignes: RepartitionLigne[] | undefined }) {
  if (lignes === undefined) return <span className="rt-mute">…</span>
  if (!lignes.length) return <span className="v3-non">Non saisie</span>
  const cotes: Array<{ cle: 'entree' | 'sortie'; libelle: string }> = [
    { cle: 'entree', libelle: 'Entrée' },
    { cle: 'sortie', libelle: 'Sortie' },
  ]
  return (
    <div className="rt-repartition">
      {cotes.map(({ cle, libelle }) => {
        const parts = lignes.filter((ligne) => ligne.cote === cle).sort((a, b) => a.rang - b.rang)
        if (!parts.length) return null
        return (
          <div key={cle} className={`rt-repartition-cote${parts.length > 1 ? ' is-plusieurs' : ''}`}>
            <span className="rt-repartition-libelle">{libelle}</span>
            {parts.length === 1 ? (
              // Un seul intervenant : son nom, terminé par « … » s'il est trop long.
              <span className="rt-part v3-solo" title={`${nomPart(parts[0])} ${entier.format(parts[0].pourcentage)} %`}>
                <span className="v3-nom">{nomCourt(nomPart(parts[0]))}</span><b>{entier.format(parts[0].pourcentage)} %</b>
              </span>
            ) : parts.map((part) => (
              // Plusieurs : leurs initiales ; le nom complet au survol et pour les lecteurs d'écran.
              <span key={`${cle}-${part.rang}-${part.hektorUserId}`} className="rt-part" title={`${nomPart(part)} ${entier.format(part.pourcentage)} %`}>
                <span className="v3-av" aria-hidden="true">{initiales(nomPart(part))}</span>
                <span className="rt-cache">{nomPart(part)}</span>
                <b>{entier.format(part.pourcentage)} %</b>
              </span>
            ))}
          </div>
        )
      })}
    </div>
  )
}

// « 05/01/2026 » -> « 05/01/26 » : le parcours de la liste tient ainsi dans sa colonne.
const dateCourte = (date: string | null) => (date && date.length === 10 ? `${date.slice(0, 6)}${date.slice(8)}` : date)

function Parcours({ ligne }: { ligne: RegistreDossierRow }) {
  const offre = dateEnClair(ligne.date_offre)
  const compromis = dateEnClair(ligne.date_compromis)
  const vente = dateEnClair(ligne.date_vente)
  const acte = dateEnClair(ligne.date_acte_prevue)
  const tombe = ligne.etape === 'compromis_annule' || ligne.etape === 'offre_refusee'
  const marches: Array<{ cle: string; libelle: string; date: string | null; etat: 'fait' | 'ici' | 'tombe' | 'vide' }> = [
    { cle: 'offre', libelle: 'Offre', date: offre, etat: ligne.etape === 'offre_refusee' ? 'tombe' : ligne.etape.startsWith('offre') ? 'ici' : offre || compromis || vente ? 'fait' : 'vide' },
    { cle: 'compromis', libelle: 'Compromis', date: compromis, etat: ligne.etape === 'compromis_annule' ? 'tombe' : ligne.etape === 'compromis' ? 'ici' : compromis || vente ? 'fait' : 'vide' },
    { cle: 'vente', libelle: ligne.etape === 'compromis' && acte ? 'Acte prévu' : 'Vente', date: vente ?? (ligne.etape === 'compromis' ? acte : null), etat: ligne.etape === 'vendu' ? 'ici' : 'vide' },
  ]
  return (
    <ol className={`rt-parcours${tombe ? ' is-tombe' : ''}`} aria-label="Parcours du dossier">
      {marches.map((marche, index) => {
        // Le trait vers la marche suivante est plein quand elle est atteinte ; la vente close en vert.
        const suivante = marches[index + 1]
        const classes = [`rt-marche is-${marche.etat}`, suivante && suivante.etat !== 'vide' ? 'seg-plein' : '', index === 2 && ligne.etape === 'vendu' ? 'is-fin' : '']
        return (
          <li key={marche.cle} className={classes.filter(Boolean).join(' ')} title={`${marche.libelle}${marche.date ? ` : ${marche.date}` : ''}`}>
            <span className="rt-point" aria-hidden="true" />
            <span className="rt-marche-texte">
              <span className="rt-marche-libelle">{marche.libelle}</span>
              <span className="rt-marche-date">{dateCourte(marche.date) ?? '—'}</span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}

// ─── La fiche d'un dossier (étape 4, 02/11/2026) ───

const montantNombre = (valeur: unknown) => {
  const texte = String(valeur ?? '').trim().replace(',', '.')
  if (!texte) return null
  const nombre = Number(texte)
  return Number.isFinite(nombre) ? nombre : null
}

function libelleLigne(ligne: AffaireLedgerRow) {
  const etat = String(ligne.state ?? '').toLowerCase()
  if (ligne.kind === 'offre') return etat === 'accepted' ? 'Offre acceptée' : etat === 'refused' ? 'Offre refusée' : 'Offre proposée'
  if (ligne.kind === 'compromis') return etat === 'cancelled' ? 'Compromis annulé' : 'Compromis signé'
  if (ligne.kind === 'vente') return 'Vente actée'
  return 'Transaction'
}

function classeLigne(ligne: AffaireLedgerRow): RegistreEtape {
  const etat = String(ligne.state ?? '').toLowerCase()
  if (ligne.kind === 'offre') return etat === 'accepted' ? 'offre_acceptee' : etat === 'refused' ? 'offre_refusee' : 'offre_proposee'
  if (ligne.kind === 'compromis') return etat === 'cancelled' ? 'compromis_annule' : 'compromis'
  return 'vendu'
}

function joursJusqua(valeur: string | null | undefined) {
  const texte = String(valeur ?? '').trim()
  if (!texte || texte.startsWith('0000')) return null
  const cible = new Date(`${texte.slice(0, 10)}T12:00:00`)
  if (Number.isNaN(cible.getTime())) return null
  const aujourdhui = new Date()
  aujourdhui.setHours(12, 0, 0, 0)
  return Math.round((cible.getTime() - aujourdhui.getTime()) / 86_400_000)
}

const ROLES: Array<{ cle: string; libelle: string; pluriel: string }> = [
  { cle: 'vendeur', libelle: 'Vendeur', pluriel: 'Vendeurs' },
  { cle: 'acquereur', libelle: 'Acquéreur', pluriel: 'Acquéreurs' },
  { cle: 'notaire_vendeur', libelle: 'Notaire du vendeur', pluriel: 'Notaires du vendeur' },
  { cle: 'notaire_acquereur', libelle: 'Notaire de l’acquéreur', pluriel: 'Notaires de l’acquéreur' },
]

const ETAT_CONDITION: Record<string, string> = { attente: 'en attente', levee: 'levée', non_levee: 'non levée', sans_objet: 'sans objet' }
const ICONE_CONDITION: Record<string, NomIcone> = { attente: 'horloge', levee: 'coche', non_levee: 'croix', sans_objet: 'info' }

// ─── v3.1 : l'ordre du parcours, et le délai entre deux étapes ───

const RANG_DU_GENRE: Record<string, number> = { offre: 0, compromis: 1, vente: 2 }
const jourIso = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit', day: '2-digit' })

/** Le JOUR d'une date du registre, « AAAA-MM-JJ » : les 10 premiers caractères, sauf pour une date
 *  écrite avec une heure en UTC (« 2019-12-30 23:00:00 » = minuit à Paris), ramenée au jour de Paris
 *  -- le même jour que celui qu'affiche dateEnClair, pour que le délai et l'ordre collent à l'écran. */
function jourDe(valeur: string | null | undefined) {
  const texte = String(valeur ?? '').trim()
  if (!/^\d{4}-\d{2}-\d{2}/.test(texte) || texte.startsWith('0000')) return ''
  if (texte.length <= 10) return texte.slice(0, 10)
  const iso = texte.replace(' ', 'T')
  const date = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  return Number.isNaN(date.getTime()) ? texte.slice(0, 10) : jourIso.format(date)
}

/** L'ordre du parcours : le JOUR (pas l'heure), puis offre < compromis < vente, puis le numéro.
 *  Corrige l'ordre de lecture par date complète : une offre porte une heure, une vente non, et une
 *  offre et une vente du même jour s'affichaient à l'envers. */
function ordreDuParcours(lignes: AffaireLedgerRow[]) {
  return [...lignes].sort((a, b) => jourDe(a.date).localeCompare(jourDe(b.date))
    || (RANG_DU_GENRE[String(a.kind)] ?? 3) - (RANG_DU_GENRE[String(b.kind)] ?? 3)
    || Number(a.app_affaire_id) - Number(b.app_affaire_id))
}

function apresQuoi(ligne: AffaireLedgerRow) {
  if (ligne.kind === 'offre') return String(ligne.state ?? '').toLowerCase() === 'accepted' ? 'l’offre acceptée' : 'l’offre'
  return ligne.kind === 'compromis' ? 'le compromis' : ligne.kind === 'vente' ? 'la vente' : 'la transaction précédente'
}

const pluriel = (nombre: number, mot: string) => `${entier.format(nombre)} ${mot}${Math.abs(nombre) > 1 ? 's' : ''}`

/** « 5 jours après l'offre » (depuis la transaction précédente non supprimée) et, pour un compromis
 *  signé d'un dossier encore sous compromis, « acte dans N jours » / « acte dépassé de N jours ». */
function delaiDeLEtape(lignes: AffaireLedgerRow[], index: number, etapeDuDossier: RegistreEtape): { texte: string; alerte: boolean } | null {
  const ligne = lignes[index]
  if (ligne.present_in_hektor === false) return null
  const morceaux: string[] = []
  let alerte = false
  const precedente = lignes.slice(0, index).reverse().find((item) => item.present_in_hektor !== false)
  const jour = jourDe(ligne.date)
  const jourAvant = precedente ? jourDe(precedente.date) : ''
  if (precedente && jour && jourAvant) {
    const ecart = Math.round((Date.parse(`${jour}T12:00:00Z`) - Date.parse(`${jourAvant}T12:00:00Z`)) / 86_400_000)
    morceaux.push(ecart === 0 ? `le même jour que ${apresQuoi(precedente)}` : `${pluriel(ecart, 'jour')} après ${apresQuoi(precedente)}`)
  }
  if (classeLigne(ligne) === 'compromis' && etapeDuDossier === 'compromis') {
    const jours = joursJusqua(ligne.date_acte)
    if (jours != null) {
      alerte = jours < 0
      morceaux.push(jours > 0 ? `acte dans ${pluriel(jours, 'jour')}` : jours === 0 ? 'acte aujourd’hui' : `acte dépassé de ${pluriel(-jours, 'jour')}`)
    }
  }
  return morceaux.length ? { texte: morceaux.join(' · '), alerte } : null
}

// ─── v4 (02/11/2026) : la frise du parcours en tête de fiche, et l'anneau ───

/** Nombre de jours entre deux jours « AAAA-MM-JJ » (b - a) ; null si l'un manque. */
function ecartEnJours(a: string, b: string) {
  if (!a || !b) return null
  return Math.round((Date.parse(`${b}T12:00:00Z`) - Date.parse(`${a}T12:00:00Z`)) / 86_400_000)
}

type JalonFrise = { cle: string; libelle: string; jour: string; montant: number | null; etat: 'fait' | 'ici' | 'tombe' | 'prevu' | 'vide'; icone: NomIcone }

/** Les trois jalons du dossier (offre, compromis, vente ou acte prévu), d'après la ligne de la liste
 *  et, quand il est lu, le dernier élément de chaque genre (pour les montants). */
function jalonsDuDossier(ligne: RegistreDossierRow, offre: AffaireLedgerRow | null, compromis: AffaireLedgerRow | null, vente: AffaireLedgerRow | null): JalonFrise[] {
  const etape = ligne.etape
  const jourOffre = jourDe(ligne.date_offre) || jourDe(offre?.date)
  const jourCompromis = jourDe(ligne.date_compromis) || jourDe(compromis?.date)
  const jourVente = jourDe(ligne.date_vente) || jourDe(vente?.date)
  const jourActe = jourDe(ligne.date_acte_prevue) || jourDe(compromis?.date_acte)
  return [
    {
      cle: 'offre', libelle: etape === 'offre_refusee' ? 'Offre refusée' : etape === 'offre_proposee' ? 'Offre proposée' : 'Offre acceptée',
      jour: jourOffre, montant: montantNombre(offre?.montant),
      etat: etape === 'offre_refusee' ? 'tombe' : OFFRES.includes(etape) ? 'ici' : jourOffre ? 'fait' : 'vide',
      icone: etape === 'offre_refusee' ? 'croix' : etape === 'offre_proposee' ? 'horloge' : 'coche',
    },
    {
      cle: 'compromis', libelle: etape === 'compromis_annule' ? 'Compromis annulé' : jourCompromis || jourVente ? 'Compromis signé' : 'Compromis',
      jour: jourCompromis, montant: montantNombre(compromis?.montant),
      etat: etape === 'compromis_annule' ? 'tombe' : etape === 'compromis' ? 'ici' : jourCompromis || jourVente ? 'fait' : 'vide',
      icone: etape === 'compromis_annule' ? 'barre' : 'stylo',
    },
    etape === 'vendu' || jourVente
      ? { cle: 'vente', libelle: 'Vente actée', jour: jourVente, montant: montantNombre(vente?.montant) ?? (etape === 'vendu' ? ligne.montant : null), etat: etape === 'vendu' ? 'ici' : 'fait', icone: 'cle' }
      : etape === 'compromis' && jourActe
        ? { cle: 'vente', libelle: 'Acte prévu', jour: jourActe, montant: null, etat: 'prevu', icone: 'calendrier' }
        : { cle: 'vente', libelle: 'Vente', jour: '', montant: null, etat: 'vide', icone: 'cle' },
  ]
}

const dateDuJour = (jour: string) => (jour ? `${jour.slice(8, 10)}/${jour.slice(5, 7)}/${jour.slice(0, 4)}` : null)

/** Un anneau : des parts (valeur + classe de couleur) sur un total, et un texte au centre. */
function Anneau(props: { parts: Array<{ valeur: number; classe: string }>; total: number; centre: string; sous?: string; etiquette: string; className?: string }) {
  const { parts, total, centre, sous, etiquette, className } = props
  const rayon = 14
  const tour = 2 * Math.PI * rayon
  let depart = 0
  return (
    <svg className={`v4-anneau${className ? ` ${className}` : ''}`} viewBox="0 0 36 36" role="img" aria-label={etiquette}>
      <circle className="v4-anneau-fond" cx="18" cy="18" r={rayon} />
      {total > 0 ? parts.filter((part) => part.valeur > 0).map((part, index) => {
        const longueur = (Math.min(part.valeur, total) / total) * tour
        const arc = <circle key={index} className={`v4-anneau-arc ${part.classe}`} cx="18" cy="18" r={rayon} strokeDasharray={`${longueur} ${tour}`} strokeDashoffset={-depart} transform="rotate(-90 18 18)" />
        depart += longueur
        return arc
      }) : null}
      <text className="v4-anneau-centre" x="18" y={sous ? 18 : 20.5} textAnchor="middle">{centre}</text>
      {sous ? <text className="v4-anneau-sous" x="18" y="23.5" textAnchor="middle">{sous}</text> : null}
    </svg>
  )
}

// ─── v3.1 : le bloc « Documents » de la fiche ───

// Les documents d'une TRANSACTION se reconnaissent au nom (libre) : mesure du 02/11, note § 13.
const DOCUMENT_DE_TRANSACTION = /compromis|promesse|offre|acte|authentique/i
const DOCUMENTS_VISIBLES = 8

function tailleEnClair(octets: number | null | undefined) {
  if (!octets || octets <= 0) return null
  if (octets >= 1_000_000) return `${(octets / 1_000_000).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} Mo`
  return `${Math.max(1, Math.round(octets / 1000)).toLocaleString('fr-FR')} Ko`
}

function extensionDe(nom: string) {
  const extension = nom.match(/\.([a-z0-9]{1,5})$/i)?.[1]
  return extension ? extension.toUpperCase().slice(0, 4) : 'DOC'
}

const attendre = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

function BlocDocuments({ appDossierId, relecture }: { appDossierId: number | null; relecture: number }) {
  const [documents, setDocuments] = useState<ConsoleDocument[] | null>(null)
  const [erreur, setErreur] = useState(false)
  const [toutVoir, setToutVoir] = useState(false)
  const [enCours, setEnCours] = useState<Record<string, 'ouverture' | 'preparation'>>({})
  const [messages, setMessages] = useState<Record<string, string>>({})
  const monte = useRef(true)

  useEffect(() => {
    monte.current = true
    return () => {
      monte.current = false
    }
  }, [])

  useEffect(() => {
    let annule = false
    setDocuments(null)
    setErreur(false)
    setToutVoir(false)
    if (appDossierId == null) {
      setDocuments([])
      return
    }
    loadConsoleDocuments(appDossierId)
      .then((lus) => {
        if (!annule) setDocuments(lus)
      })
      .catch((cause: unknown) => {
        console.error('[registre des transactions] documents illisibles', cause)
        if (!annule) setErreur(true)
      })
    return () => {
      annule = true
    }
  }, [appDossierId, relecture])

  // Les documents de la transaction d'abord (compromis, offre, acte…), puis les autres ; les plus récents en tête.
  const tries = useMemo(() => {
    const date = (document: ConsoleDocument) => String(document.created_at_hektor ?? document.created_at ?? '')
    return [...(documents ?? [])].sort((a, b) => Number(DOCUMENT_DE_TRANSACTION.test(b.document_name)) - Number(DOCUMENT_DE_TRANSACTION.test(a.document_name))
      || date(b).localeCompare(date(a)) || a.document_name.localeCompare(b.document_name, 'fr'))
  }, [documents])

  const poser = (id: string, etat: 'ouverture' | 'preparation' | null, message?: string) => {
    if (!monte.current) return
    setEnCours((avant) => {
      const suite = { ...avant }
      if (etat) suite[id] = etat
      else delete suite[id]
      return suite
    })
    setMessages((avant) => {
      const suite = { ...avant }
      if (message) suite[id] = message
      else delete suite[id]
      return suite
    })
  }

  const ouvrirLAdresse = async (document: ConsoleDocument) => {
    const adresse = await createConsoleDocumentSignedUrl(document)
    const fenetre = window.open(adresse, '_blank')
    if (fenetre) fenetre.opener = null
    return Boolean(fenetre)
  }

  const ouvrir = async (document: ConsoleDocument) => {
    poser(document.id, 'ouverture')
    try {
      if (document.storage_status === 'cloud_available' && document.storage_path) {
        await ouvrirLAdresse(document)
        poser(document.id, null)
        return
      }
      // Gardé sur notre serveur seulement (la règle pour un bien vendu) : on le fait remonter, puis on l'ouvre.
      poser(document.id, 'preparation')
      await createPrepareConsoleDocumentJob({ document, priority: 30 })
      for (let essai = 0; essai < 20; essai += 1) {
        await attendre(2000)
        if (!monte.current || appDossierId == null) return
        const relu = (await loadConsoleDocuments(appDossierId)).find((item) => item.id === document.id)
        if (relu?.storage_status === 'cloud_available' && relu.storage_path) {
          setDocuments((avant) => (avant ? avant.map((item) => (item.id === relu.id ? relu : item)) : avant))
          const ouverte = await ouvrirLAdresse(relu)
          poser(document.id, null, ouverte ? undefined : 'Le document est prêt : cliquez à nouveau sur « Ouvrir ».')
          return
        }
        if (relu && (relu.storage_status === 'missing' || relu.storage_status === 'error')) break
      }
      poser(document.id, null, 'Ce document n’a pas pu être préparé. Réessayez dans un instant.')
    } catch (cause) {
      console.error('[registre des transactions] ouverture du document impossible', cause)
      poser(document.id, null, 'Ce document n’a pas pu être ouvert. Réessayez dans un instant.')
    }
  }

  const visibles = toutVoir ? tries : tries.slice(0, DOCUMENTS_VISIBLES)
  return (
    <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-docs">
      <div className="rt-bloc-tete">
        <h3 id="rt-bloc-docs" className="rt-bloc-titre">Documents</h3>
        {tries.length ? <span className="rt-compte">{entier.format(tries.length)}</span> : null}
      </div>
      {erreur ? <p className="rt-mute">Les documents n’ont pas pu être chargés.</p>
        : documents === null ? <p className="rt-mute" role="status">Chargement des documents…</p>
          : !tries.length ? <p className="rt-mute">Aucun document lié à ce dossier.</p> : (
            <>
              <ul className="v4-docs">
                {visibles.map((document) => {
                  const etat = enCours[document.id]
                  const introuvable = document.storage_status === 'missing' || document.storage_status === 'error'
                  const details = [dateEnClair(document.created_at_hektor ?? document.created_at), tailleEnClair(document.file_size)].filter(Boolean).join(' · ')
                  const extension = extensionDe(document.document_name)
                  const genre = extension === 'PDF' ? 'pdf' : /^(JPG|JPEG|PNG|GIF|WEBP|HEIC|TIF|TIFF|BMP)$/.test(extension) ? 'image' : 'autre'
                  return (
                    <li key={document.id}>
                      {/* v4 : toute la vignette ouvre le document (même geste qu'avant : lien signé, ou préparation). */}
                      <button
                        type="button"
                        className="v4-doc"
                        disabled={Boolean(etat) || introuvable}
                        title={introuvable ? 'Fichier introuvable' : document.document_name}
                        onClick={() => void ouvrir(document)}
                      >
                        <span className={`v4-fichier is-${genre}`} aria-hidden="true">{extension}</span>
                        <span className="v4-doc-txt">
                          <b>{document.document_name}</b>
                          <span>{etat === 'preparation' ? 'Préparation…' : etat === 'ouverture' ? 'Ouverture…' : introuvable ? 'Fichier introuvable' : details}</span>
                          {messages[document.id] ? <span className="v31-doc-erreur" role="status">{messages[document.id]}</span> : null}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
              {tries.length > DOCUMENTS_VISIBLES ? (
                <button type="button" className="v31-lien" aria-expanded={toutVoir} onClick={() => setToutVoir((valeur) => !valeur)}>
                  {toutVoir ? 'Voir moins' : `Voir les ${entier.format(tries.length)} documents`}<Ic n={toutVoir ? 'flHaut' : 'right'} />
                </button>
              ) : null}
            </>
          )}
    </section>
  )
}

// ─── v3.1 : le bloc « Historique » de la fiche ───

const HISTORIQUE_VISIBLE = 5
const heureParis = new Intl.DateTimeFormat('fr-FR', { timeZone: 'Europe/Paris', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

function quandEnClair(ligne: HistoriqueDossierLigne) {
  if (!ligne.heure) return dateEnClair(ligne.quand) ?? ligne.quand
  const date = new Date(ligne.quand)
  return Number.isNaN(date.getTime()) ? ligne.quand : heureParis.format(date).replace(',', '')
}

// v4 : la couleur du point suit l'événement (vente vert, compromis ambre, offre bleu, annulé brique).
function genreDHistorique(texte: string) {
  return /annul|refus|supprim/i.test(texte) ? 'tombe' : /vente/i.test(texte) ? 'vente' : /compromis/i.test(texte) ? 'compromis' : /offre/i.test(texte) ? 'offre' : 'autre'
}

function BlocHistorique(props: { chaineId: number; hektorAnnonceId: number | null; lignes: AffaireLedgerRow[]; relecture: number }) {
  const { chaineId, hektorAnnonceId, lignes, relecture } = props
  const [historique, setHistorique] = useState<HistoriqueDossierLigne[] | null>(null)
  const [toutVoir, setToutVoir] = useState(false)

  useEffect(() => {
    let annule = false
    setHistorique(null)
    // La fonction ne rejette pas (chaque source a son try/catch) ; par prudence, une panne rend la liste vide.
    loadHistoriqueDuDossier({ chaineId, hektorAnnonceId, lignes })
      .then((lu) => {
        if (!annule) setHistorique(lu)
      })
      .catch((cause: unknown) => {
        console.error('[registre des transactions] historique illisible', cause)
        if (!annule) setHistorique([])
      })
    return () => {
      annule = true
    }
  }, [chaineId, hektorAnnonceId, lignes, relecture])

  const liste = historique ?? []
  const visibles = toutVoir ? liste : liste.slice(0, HISTORIQUE_VISIBLE)
  return (
    <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-hist">
      <h3 id="rt-bloc-hist" className="rt-bloc-titre">Historique</h3>
      {historique === null ? <p className="rt-mute" role="status">Chargement de l’historique…</p>
        : !liste.length ? <p className="rt-mute">Aucun changement enregistré.</p> : (
          <>
            <ol className="v31-hist">
              {visibles.map((ligne) => (
                <li key={ligne.cle} className={`is-${genreDHistorique(ligne.texte)}`}>
                  <time className="rt-num" dateTime={ligne.quand}>{quandEnClair(ligne)}</time>
                  <span>{ligne.auteur ? <><b>{ligne.auteur}</b> · </> : null}{ligne.texte}</span>
                </li>
              ))}
            </ol>
            {liste.length > HISTORIQUE_VISIBLE ? (
              <button type="button" className="v31-lien" aria-expanded={toutVoir} onClick={() => setToutVoir((valeur) => !valeur)}>
                {toutVoir ? 'Voir moins' : `Voir tout (${entier.format(liste.length)})`}
              </button>
            ) : null}
          </>
        )}
    </section>
  )
}

/** Précédent / suivant dans la liste (v3.1). */
type NavigationDossier = { position: number; total: number; precedent: (() => void) | null; suivant: (() => void) | null }

function FicheDossier(props: {
  ligne: RegistreDossierRow
  type: string | null
  relecture: number
  onRetour: () => void
  onOuvrirBien?: (ligne: RegistreDossierRow) => void
  onGeste?: (ligne: RegistreDossierRow, geste: GesteDuRegistre) => void
  onOuvrirContact?: (contactId: string) => void
  /** v3.1 : le nom du négociateur (l'e-mail reste au survol) ; null = on garde l'e-mail. */
  nomNegociateur?: string | null
  /** v3.1 : dossier précédent / suivant, dans l'ordre de la liste. */
  navigation?: NavigationDossier | null
}) {
  const { ligne, type, relecture, onRetour, onOuvrirBien, onGeste, onOuvrirContact, nomNegociateur, navigation } = props
  const [dossier, setDossier] = useState<DossierDeLaChaine | null>(null)
  const [vivant, setVivant] = useState<boolean | null>(null)
  // 4C : un bien hors annonces est dans l'historique (vendu ou clos) ou archivé (lecture seule).
  const [historique, setHistorique] = useState<boolean | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [essai, setEssai] = useState(0)
  const retourRef = useRef<HTMLButtonElement>(null)

  // Un AUTRE dossier (précédent / suivant) : on n'affiche pas l'ancien pendant la lecture.
  useEffect(() => {
    setDossier(null)
    setVivant(null)
    setHistorique(null)
  }, [ligne.app_chaine_id])

  // Le focus va au retour à l'OUVERTURE ; il reste sur « précédent / suivant » quand on navigue.
  useEffect(() => {
    retourRef.current?.focus()
  }, [])

  useEffect(() => {
    let annule = false
    setErreur(null)
    Promise.all([
      loadDossierDeLaChaine(ligne.app_chaine_id),
      ligne.app_dossier_id == null ? Promise.resolve(false) : bienEstDansLesAnnonces(ligne.app_dossier_id),
    ])
      .then(async ([lu, estVivant]) => {
        const estHistorique = !estVivant && ligne.app_dossier_id != null
          ? (await loadBienHistoriquePourStatut(ligne.app_dossier_id)) != null
          : false
        if (annule) return
        setDossier(lu)
        setVivant(estVivant)
        setHistorique(estHistorique)
      })
      .catch((cause: unknown) => {
        console.error('[registre des transactions] fiche du dossier illisible', cause)
        if (!annule) setErreur('Ce dossier n’a pas pu être chargé. Réessayez dans un instant.')
      })
    return () => {
      annule = true
    }
  }, [ligne.app_chaine_id, ligne.app_dossier_id, relecture, essai])

  const lignes = useMemo(() => ordreDuParcours(dossier?.lignes ?? []), [dossier])
  const derniereDuGenre = (kind: string) => [...lignes].reverse().find((item) => item.kind === kind) ?? null
  const offre = derniereDuGenre('offre')
  const compromis = derniereDuGenre('compromis')
  const vente = derniereDuGenre('vente')
  const peutAgir = Boolean(onGeste && vivant && ligne.app_dossier_id != null)
  // 4C (02/11/2026) : bien vendu, dans l'historique -> seule LA VENTE se corrige (la base refuse toute
  // création hors annonces, et l'offre et le compromis sont verrouillés par la vente).
  const venteACorriger = onGeste && vivant === false && historique && ligne.app_dossier_id != null
    && vente && vente.present_in_hektor !== false ? vente : null
  const agir = (geste: GesteDuRegistre) => onGeste?.(ligne, geste)
  const corrigerLaVente = (cible: AffaireLedgerRow) => agir({ onglet: 'vente', appAffaireId: Number(cible.app_affaire_id), hektorAffaireId: cible.hektor_affaire_id == null ? null : String(cible.hektor_affaire_id) })

  // Le geste « suivant » de l'étape, en tête de fiche.
  const suivant: { libelle: string; geste: GesteDuRegistre } | null = !peutAgir ? null
    : ligne.etape === 'offre_proposee' && offre ? { libelle: 'Accepter ou refuser l’offre', geste: { onglet: 'offre', appAffaireId: offre.app_affaire_id } }
      : ligne.etape === 'offre_acceptee' ? { libelle: 'Passer au compromis', geste: { onglet: 'compromis', appAffaireId: null } }
        : ligne.etape === 'compromis' ? { libelle: 'Enregistrer la vente', geste: { onglet: 'vente', appAffaireId: null } }
          : null

  // Les parties : une personne par rôle, prise sur la transaction la plus récente qui la nomme.
  const parties = useMemo(() => {
    const rangDe = new Map(lignes.map((item, index) => [Number(item.app_affaire_id), index]))
    const triees = [...(dossier?.parties ?? [])].sort((a, b) => (rangDe.get(b.app_affaire_id) ?? 0) - (rangDe.get(a.app_affaire_id) ?? 0) || a.rang - b.rang)
    const parRole = new Map<string, AffairePartieRow[]>()
    const vus = new Set<string>()
    for (const partie of triees) {
      const qui = partie.hektor_contact_id ?? partie.app_contact_id ?? `${partie.app_affaire_id}-${partie.rang}`
      const cle = `${partie.role}|${qui}`
      if (vus.has(cle)) continue
      // On ne garde que les personnes de la transaction la plus récente pour ce rôle.
      const deja = parRole.get(partie.role)
      if (deja?.length && deja[0].app_affaire_id !== partie.app_affaire_id) continue
      vus.add(cle)
      parRole.set(partie.role, [...(deja ?? []), partie])
    }
    return parRole
  }, [dossier, lignes])

  const acquereursDe = (appAffaireId: number) => (dossier?.parties ?? [])
    .filter((partie) => partie.app_affaire_id === appAffaireId && partie.role === 'acquereur')
    .map((partie) => partie.nom || (partie.fiche_sans_nom ? 'Fiche sans nom' : null))
    .filter(Boolean)
    .join(', ')

  const prix = ligne.montant
  const netVendeur = montantNombre(compromis?.prix_net_vendeur) ?? montantNombre(offre?.prix_net_vendeur)
  const tauxHonoraires = prix && ligne.honoraires ? (ligne.honoraires / prix) * 100 : null
  const quatrieme = ligne.etape === 'vendu'
    ? { libelle: 'Vendu le', valeur: dateEnClair(ligne.date_vente), detail: ligne.date_compromis ? `compromis du ${dateEnClair(ligne.date_compromis)}` : '' }
    : ligne.etape === 'compromis'
      ? (() => {
          const jours = joursJusqua(ligne.date_acte_prevue)
          return {
            libelle: 'Acte prévu',
            valeur: dateEnClair(ligne.date_acte_prevue),
            detail: jours == null ? 'date non saisie' : jours > 0 ? `dans ${entier.format(jours)} jour${jours > 1 ? 's' : ''}` : jours === 0 ? 'aujourd’hui' : `dépassé de ${entier.format(-jours)} jour${jours < -1 ? 's' : ''}`,
            alerte: jours != null && jours < 0,
          }
        })()
      : { libelle: ligne.etape === 'compromis_annule' ? 'Compromis du' : 'Offre du', valeur: dateEnClair(ligne.etape === 'compromis_annule' ? ligne.date_compromis : ligne.date_offre), detail: '' }

  const conditions = lignes.flatMap((item) => (dossier?.conditions.get(Number(item.app_affaire_id)) ?? []).map((condition) => ({ ...condition, kind: item.kind })))
  const notes = lignes
    .map((item) => ({ kind: item.kind, libelle: libelleLigne(item), texte: (dossier?.notes.get(Number(item.app_affaire_id)) ?? '').trim() }))
    .filter((note) => note.texte)

  const titre = [type, ligne.ville || 'Ville inconnue'].filter(Boolean).join(' · ')
  const statutBien = String(ligne.statut_annonce ?? '').toLowerCase()
  const parcoursOuvrable = (item: AffaireLedgerRow) => ({ onglet: (item.kind === 'offre' ? 'offre' : item.kind === 'compromis' ? 'compromis' : 'vente') as GesteDuRegistre['onglet'], appAffaireId: Number(item.app_affaire_id), hektorAffaireId: item.hektor_affaire_id == null ? null : String(item.hektor_affaire_id) })
  const repartitionTriee = [...(dossier?.repartition ?? [])].sort((a, b) => (a.cote === b.cote ? a.rang - b.rang : a.cote === 'entree' ? -1 : 1))
  const entree = ligne.honoraires_entree ?? 0
  const sortie = ligne.honoraires_sortie ?? 0

  // v4 : la frise, et sous elle le délai total et l'acte signé par rapport à la date prévue.
  const jalons = jalonsDuDossier(ligne, offre, compromis, vente)
  const totalFrise: Array<{ cle: string; texte: string; fort: string; fin?: string }> = []
  const jourVente = jalons[2].cle === 'vente' && jalons[2].etat !== 'prevu' ? jalons[2].jour : ''
  const premierJour = jalons[0].jour || jalons[1].jour
  const total = ecartEnJours(premierJour, jourVente)
  if (total != null && total >= 0) totalFrise.push({ cle: 'total', texte: jalons[0].jour ? 'De l’offre à l’acte : ' : 'Du compromis à l’acte : ', fort: pluriel(total, 'jour') })
  const jourActePrevu = jourDe(compromis?.date_acte) || jourDe(ligne.date_acte_prevue)
  const retardActe = ecartEnJours(jourActePrevu, jourVente)
  if (retardActe != null) {
    totalFrise.push({
      cle: 'acte', texte: `Acte prévu au compromis le ${dateDuJour(jourActePrevu)}, signé `,
      fort: retardActe === 0 ? 'à la date prévue' : `${pluriel(Math.abs(retardActe), 'jour')} plus ${retardActe > 0 ? 'tard' : 'tôt'}`,
    })
  }
  // Prix de vente comparé à l'offre retenue (le montant de la dernière offre lue).
  const montantOffre = montantNombre(offre?.montant)
  const ecartOffre = ligne.etape === 'vendu' && prix != null && montantOffre != null && montantOffre !== prix ? prix - montantOffre : null
  // Répartition : la part attribuée (toutes lignes confondues, plafond 100 % côté base).
  const pourcentReparti = repartitionTriee.reduce((somme, part) => somme + Math.max(part.pourcentage, 0), 0)
  const resteARepartir = repartitionTriee.length ? Math.max(0, Math.round((100 - pourcentReparti) * 100) / 100) : 0

  return (
    <section className="rt-ecran rt-fiche" aria-labelledby="rt-fiche-titre">
      <nav className="rt-fiche-fil" aria-label="Fil d’Ariane">
        <button ref={retourRef} type="button" className="rt-bouton rt-retour" onClick={onRetour}>
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 6l-6 6 6 6" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" /></svg>
          Registre des transactions
        </button>
        <span className="rt-mute">Dossier <b className="rt-num">N° {ligne.app_chaine_id}</b></span>
        {navigation && navigation.total > 0 ? (
          <span className="v31-nav">
            <span className="rt-mute rt-num">{entier.format(navigation.position)} sur {entier.format(navigation.total)}</span>
            <button type="button" className="v31-ic" aria-label="Dossier précédent" title="Dossier précédent" disabled={!navigation.precedent} onClick={() => navigation.precedent?.()}>
              <Ic n="left" />
            </button>
            <button type="button" className="v31-ic" aria-label="Dossier suivant" title="Dossier suivant" disabled={!navigation.suivant} onClick={() => navigation.suivant?.()}>
              <Ic n="right" />
            </button>
          </span>
        ) : null}
      </nav>

      <div className={`v4-heros is-${ligne.etape}`}>
      <header className="rt-fiche-entete">
        <div className="rt-fiche-identite">
          {ligne.photo_url_listing ? (
            <img className="rt-fiche-photo" src={ligne.photo_url_listing} alt="" />
          ) : (
            <span className="rt-fiche-photo v3-vide" title="Pas de photo"><Ic n={iconeDuType(type)} /><span>Pas de photo</span></span>
          )}
          <div className="rt-fiche-titres">
            <span className="rt-fiche-pastilles">
              <Pastille etape={ligne.etape} />
              {vivant === false && ligne.app_dossier_id != null ? (
                <span className="rt-pastille is-neutre"><Ic n={/vendu/.test(statutBien) ? 'cle' : 'info'} />Bien {statutBien || 'hors annonces'}</span>
              ) : null}
            </span>
            <h2 id="rt-fiche-titre" className="rt-fiche-titre">{titre}{ligne.code_postal ? <span className="rt-mute"> {ligne.code_postal}</span> : null}</h2>
            {ligne.numero_mandat || ligne.agence_nom || ligne.negociateur_email ? (
              <span className="v3-meta">
                {ligne.numero_mandat ? <span><Ic n="doc" />Mandat <b className="rt-num">{ligne.numero_mandat}</b></span> : null}
                {ligne.agence_nom ? <span><Ic n="agence" />{ligne.agence_nom}</span> : null}
                {ligne.negociateur_email ? (
                  nomNegociateur ? (
                    <span title={ligne.negociateur_email}>
                      <span className="v3-av" aria-hidden="true">{initiales(nomNegociateur)}</span>
                      suivi par <b>{nomNegociateur}</b><span className="rt-cache"> ({ligne.negociateur_email})</span>
                    </span>
                  ) : (
                    <span><Ic n="personnes" />suivi par <span className="v3-mail">{ligne.negociateur_email}</span></span>
                  )
                ) : null}
              </span>
            ) : <span className="rt-mute">—</span>}
          </div>
        </div>
        <div className="rt-fiche-actions-tete">
          {onOuvrirBien && ligne.app_dossier_id != null ? (
            <button type="button" className="rt-bouton" onClick={() => onOuvrirBien(ligne)}><Ic n="ouvrir" />Ouvrir la fiche du bien</button>
          ) : null}
          {suivant ? (
            <button type="button" className="rt-bouton rt-bouton-principal" onClick={() => agir(suivant.geste)}>
              <Ic n={ligne.etape === 'offre_proposee' ? 'coche' : ligne.etape === 'offre_acceptee' ? 'stylo' : 'cle'} />{suivant.libelle}
            </button>
          ) : null}
          {venteACorriger ? (
            <button type="button" className="rt-bouton rt-bouton-principal" onClick={() => corrigerLaVente(venteACorriger)}><Ic n="crayon" />Modifier la vente</button>
          ) : null}
        </div>
      </header>

      {/* v4 : le parcours en un coup d'œil -- trois jalons, la durée entre eux, et le total. */}
      <div className="v4-frise" aria-label="Parcours en un coup d’œil">
        {jalons.map((jalon, index) => {
          const precedent = jalons[index - 1]
          const duree = precedent && jalon.etat !== 'prevu' ? ecartEnJours(precedent.jour, jalon.jour) : null
          return (
            <Fragment key={jalon.cle}>
              {index > 0 ? (
                <span className={`v4-lien is-${precedent.cle}-${jalon.cle}${jalon.etat === 'vide' || jalon.etat === 'prevu' ? ' is-attente' : ''}`} aria-hidden={duree == null}>
                  <span className="v4-trait" />
                  {duree != null ? <span className="v4-duree rt-num"><Ic n="horloge" />{pluriel(duree, 'jour').replace(/ jours?$/, ' j')}</span> : null}
                </span>
              ) : null}
              <div className={`v4-jalon is-${jalon.cle} is-${jalon.etat}`}>
                <span className="v4-pt" aria-hidden="true"><Ic n={jalon.icone} /></span>
                <span className="v4-jalon-txt">
                  <span className="v4-jalon-lib">{jalon.libelle}</span>
                  <span className="v4-jalon-date rt-num">{dateDuJour(jalon.jour) ?? '—'}</span>
                  {jalon.montant != null ? <span className="v4-jalon-mt rt-num">{formatEuros(jalon.montant)}</span> : null}
                </span>
              </div>
            </Fragment>
          )
        })}
        {totalFrise.length ? <div className="v4-total">{totalFrise.map((morceau) => <span key={morceau.cle}>{morceau.texte}<b>{morceau.fort}</b>{morceau.fin}</span>)}</div> : null}
      </div>
      </div>

      <div className="rt-indicateurs" aria-label="Chiffres du dossier">
        <div className="rt-carte rt-indicateur v4-chiffre">
          <span className="v4-tuile is-prix" aria-hidden="true"><Ic n="euro" /></span>
          <span className="rt-indicateur-libelle">{ligne.etape === 'vendu' ? 'Prix de vente' : ligne.etape.startsWith('offre') ? 'Montant de l’offre' : 'Prix'}</span>
          <strong className="rt-indicateur-valeur rt-num">{formatEuros(prix)}</strong>
          <span className="rt-indicateur-detail">
            {ecartOffre != null ? (
              <><span className={`v4-ecart ${ecartOffre < 0 ? 'is-baisse' : 'is-hausse'}`}><Ic n={ecartOffre < 0 ? 'flBas' : 'flHaut'} />{ecartOffre > 0 ? '+' : '−'}{formatEuros(Math.abs(ecartOffre))}</span>par rapport à l’offre</>
            ) : ligne.nb_transactions > 1 ? `${ligne.nb_transactions} transactions dans ce dossier` : 'une transaction'}
          </span>
        </div>
        <div className="rt-carte rt-indicateur v4-chiffre">
          <span className="v4-tuile is-net" aria-hidden="true"><Ic n="porte" /></span>
          <span className="rt-indicateur-libelle">Net vendeur</span>
          <strong className="rt-indicateur-valeur rt-num">{formatEuros(netVendeur)}</strong>
          <span className="rt-indicateur-detail">{netVendeur == null ? 'non renseigné' : 'au compromis'}</span>
        </div>
        <div className="rt-carte rt-indicateur v4-chiffre">
          <span className="v4-tuile is-hono" aria-hidden="true"><Ic n="camembert" /></span>
          <span className="rt-indicateur-libelle">Honoraires</span>
          <span className="v4-hono">
            <strong className="rt-indicateur-valeur rt-num">{ligne.honoraires ? formatEuros(ligne.honoraires) : '—'}</strong>
            {ligne.honoraires ? (
              // L'anneau : entrée (plein) et sortie (clair), le taux au centre.
              <Anneau
                className="is-petit"
                parts={[{ valeur: entree, classe: 'is-entree' }, { valeur: sortie, classe: 'is-sortie' }]}
                total={entree + sortie}
                centre={tauxHonoraires ? `${tauxHonoraires.toLocaleString('fr-FR', { maximumFractionDigits: 1 })}%` : ''}
                etiquette={`Entrée ${formatEuros(entree)}, sortie ${formatEuros(sortie)}${tauxHonoraires ? `, ${tauxHonoraires.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} % du prix` : ''}`}
              />
            ) : null}
          </span>
          <span className="rt-indicateur-detail">
            {ligne.honoraires ? (
              <span className="v4-hono-leg"><span><i className="v4-sw is-entree" />entrée {formatEuros(entree)}</span><span><i className="v4-sw is-sortie" />sortie {formatEuros(sortie)}</span></span>
            ) : 'non renseignés'}
          </span>
        </div>
        <div className={`rt-carte rt-indicateur v4-chiffre${'alerte' in quatrieme && quatrieme.alerte ? ' is-alerte' : ''}`}>
          <span className="v4-tuile is-date" aria-hidden="true"><Ic n="calendrier" /></span>
          <span className="rt-indicateur-libelle">{quatrieme.libelle}</span>
          <strong className="rt-indicateur-valeur rt-num">{quatrieme.valeur ?? '—'}</strong>
          <span className="rt-indicateur-detail">{'alerte' in quatrieme && quatrieme.alerte ? <Ic n="alerte" /> : null}{quatrieme.detail}</span>
        </div>
      </div>

      {erreur ? (
        <div key="erreur" className="rt-carte rt-etat rt-etat-erreur" role="alert">
          <span className="v3-etat-ic err"><Ic n="alerte" /></span>
          <p>{erreur}</p>
          <button type="button" className="rt-bouton" onClick={() => setEssai((valeur) => valeur + 1)}><Ic n="rafraichir" />Réessayer</button>
        </div>
      ) : !dossier ? (
        <div key="chargement" className="rt-carte rt-etat" role="status"><Chargement texte="Chargement du dossier…" lignes={[90, 74, 84]} /></div>
      ) : (
        <div key="dossier" className="rt-fiche-grille">
          <div className="rt-fiche-colonne">
            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-parcours">
              <h3 id="rt-bloc-parcours" className="rt-bloc-titre">Parcours du dossier</h3>
              {!lignes.length ? <p className="rt-mute">Aucune transaction lisible pour ce dossier.</p> : (
                <ol className="rt-etapes">
                  {lignes.map((item, index) => {
                    const montant = montantNombre(item.montant)
                    const acquereurs = acquereursDe(Number(item.app_affaire_id))
                    const details = item.kind === 'offre'
                      ? [item.jours_validite ? `validité ${item.jours_validite} jours` : null, acquereurs || null]
                      : item.kind === 'compromis'
                        ? [
                            dateEnClair(item.date_fin_retractation) ? `fin de rétractation ${dateEnClair(item.date_fin_retractation)}` : null,
                            dateEnClair(item.date_acte) ? `acte prévu ${dateEnClair(item.date_acte)}` : null,
                            montantNombre(item.sequestre) ? `séquestre ${formatEuros(montantNombre(item.sequestre))}` : null,
                            acquereurs || null,
                          ]
                        : [acquereurs || null]
                    const retiree = item.present_in_hektor === false
                    const classe = classeLigne(item)
                    const delai = delaiDeLEtape(lignes, index, ligne.etape)
                    return (
                      <li key={item.app_affaire_id} className={`rt-etape is-${classe}${retiree ? ' is-retiree' : ''}`}>
                        <span className="rt-etape-point" aria-hidden="true"><Ic n={retiree ? 'corbeille' : ICONE_ETAPE[classe]} /></span>
                        <div className="rt-etape-corps">
                          <div className="rt-etape-haut">
                            <b>{libelleLigne(item)}</b>
                            {retiree ? <span className="rt-pastille is-neutre">supprimée</span> : null}
                            <span className="rt-mute rt-num">{dateEnClair(item.date) ?? 'date inconnue'}</span>
                            <span className="rt-etape-montant rt-num">{formatEuros(montant)}</span>
                          </div>
                          {details.some(Boolean) ? (
                            <span className="v4-tags">{details.filter(Boolean).map((detail) => <span key={String(detail)} className="v4-tag">{detail}</span>)}</span>
                          ) : null}
                          {delai ? (
                            <span className={`v31-delai${delai.alerte ? ' is-alerte' : ''}`}><Ic n={delai.alerte ? 'alerte' : 'horloge'} />{delai.texte}</span>
                          ) : null}
                        </div>
                        {peutAgir && !retiree ? (
                          <button type="button" className="rt-bouton rt-bouton-petit" onClick={() => agir(parcoursOuvrable(item))}>
                            Ouvrir<Ic n="right" />
                          </button>
                        ) : venteACorriger && item.app_affaire_id === venteACorriger.app_affaire_id ? (
                          <button type="button" className="rt-bouton rt-bouton-petit" onClick={() => corrigerLaVente(venteACorriger)}>
                            <Ic n="crayon" />Modifier
                          </button>
                        ) : null}
                      </li>
                    )
                  })}
                </ol>
              )}
              {onGeste && vivant === false && historique !== null && ligne.app_dossier_id != null ? (
                <p className="rt-fiche-remarque">
                  <Ic n="info" />
                  <span>
                    {venteACorriger
                      ? 'Ce bien n’est plus en annonce : la vente se corrige ici, mais aucune nouvelle transaction ne peut être créée.'
                      : historique
                        ? 'Ce bien n’est plus en annonce : ce dossier se consulte ici. Seule une vente se corrige depuis le registre.'
                        : 'Ce bien est archivé : ce dossier se consulte ici, il ne se modifie pas.'}
                  </span>
                </p>
              ) : null}
            </section>

            <BlocDocuments appDossierId={ligne.app_dossier_id} relecture={relecture} />
          </div>

          <div className="rt-fiche-colonne">
            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-parties">
              <h3 id="rt-bloc-parties" className="rt-bloc-titre">Les parties</h3>
              {!parties.size ? <p className="rt-mute">Aucune partie connue pour ce dossier.</p> : (
                <div className="rt-parties">
                  {ROLES.filter((role) => parties.get(role.cle)?.length).map((role) => {
                    const personnes = parties.get(role.cle) ?? []
                    return (
                      <div key={role.cle} className={`rt-partie v4-role-${role.cle.startsWith('notaire') ? 'notaire' : role.cle}`}>
                        <span className="rt-indicateur-libelle"><Ic n={role.cle === 'vendeur' ? 'maison' : role.cle === 'acquereur' ? 'cle' : 'balance'} />{personnes.length > 1 ? `${role.pluriel} · ${personnes.length}` : role.libelle}</span>
                        {personnes.map((personne) => {
                          const id = String(personne.hektor_contact_id ?? personne.app_contact_id ?? '').trim()
                          const nom = personne.nom || (personne.fiche_sans_nom ? 'Fiche sans nom' : id ? `Contact n° ${id}` : 'Contact inconnu')
                          const contenu = <><span className="v3-av" aria-hidden="true">{initiales(nom)}</span><span>{nom}</span></>
                          return onOuvrirContact && id ? (
                            <button key={`${personne.app_affaire_id}-${personne.rang}-${id}`} type="button" className="rt-lien v3-pers" title={nom} onClick={() => onOuvrirContact(id)}>{contenu}</button>
                          ) : (
                            <b key={`${personne.app_affaire_id}-${personne.rang}-${id}`} className="v3-pers" title={nom}>{contenu}</b>
                          )
                        })}
                      </div>
                    )
                  })}
                </div>
              )}
            </section>

            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-repartition">
              <div className="rt-bloc-tete">
                <h3 id="rt-bloc-repartition" className="rt-bloc-titre">Répartition des honoraires</h3>
                {(peutAgir && (vente ?? compromis ?? offre)) || venteACorriger ? (
                  <button
                    type="button"
                    className="rt-bouton rt-bouton-petit"
                    onClick={() => {
                      if (venteACorriger) return corrigerLaVente(venteACorriger)
                      const cible = vente ?? compromis ?? offre
                      if (cible) agir(parcoursOuvrable(cible))
                    }}
                  >
                    <Ic n="crayon" />Modifier
                  </button>
                ) : null}
              </div>
              {!repartitionTriee.length ? <p className="rt-mute">Aucune répartition saisie.</p> : (
                <>
                  {/* v4 : l'anneau de ce qui est attribué, une couleur par intervenant, puis le reste. */}
                  <div className="v4-rp-tete">
                    <Anneau
                      className="is-grand"
                      parts={repartitionTriee.map((part, index) => ({ valeur: Math.max(part.pourcentage, 0), classe: `is-p${index % 4}` }))}
                      total={100}
                      centre={`${entier.format(pourcentReparti)} %`}
                      sous="réparti"
                      etiquette={repartitionTriee.map((part) => `${part.cote === 'entree' ? 'entrée' : 'sortie'} ${nomPart(part)} ${entier.format(part.pourcentage)} %`).join(', ')}
                    />
                    <ul className="v4-rp-leg">
                      {repartitionTriee.map((part, index) => (
                        <li key={`${part.cote}-${part.rang}-${part.hektorUserId}`}><i className={`v4-sw is-p${index % 4}`} /><span>{nomPart(part)}</span><b className="rt-num">{ligne.honoraires ? formatEuros((ligne.honoraires * part.pourcentage) / 100) : `${entier.format(part.pourcentage)} %`}</b></li>
                      ))}
                      {resteARepartir > 0 ? (
                        <li><i className="v4-sw is-reste" /><span>Non attribué</span><b className="rt-num">{ligne.honoraires ? formatEuros((ligne.honoraires * resteARepartir) / 100) : `${entier.format(resteARepartir)} %`}</b></li>
                      ) : null}
                    </ul>
                  </div>
                  <ul className="rt-parts">
                    {repartitionTriee.map((part, index) => (
                      <li key={`${part.cote}-${part.rang}-${part.hektorUserId}`} className="rt-part-ligne">
                        <span className={`rt-part-cote is-${part.cote}`}>{part.cote === 'entree' ? 'Entrée' : 'Sortie'}</span>
                        <span className="rt-part-nom"><span className={`v3-av is-p${index % 4}`} aria-hidden="true">{initiales(nomPart(part))}</span><span>{nomPart(part)}</span></span>
                        <span className="rt-mute rt-num">{entier.format(part.pourcentage)} %</span>
                        <b className="rt-num">{ligne.honoraires ? formatEuros((ligne.honoraires * part.pourcentage) / 100) : '—'}</b>
                        <span className="v4-jauge" aria-hidden="true"><i className={`is-p${index % 4}`} style={{ width: `${Math.min(Math.max(part.pourcentage, 0), 100)}%` }} /></span>
                      </li>
                    ))}
                  </ul>
                  {resteARepartir > 0 ? (
                    <p className="v4-reste"><Ic n="alerte" />{`${entier.format(resteARepartir)} % des honoraires ne sont attribués à personne.`}</p>
                  ) : null}
                </>
              )}
            </section>
            {!conditions.length && !notes.length ? (
              // v4 : rien à dire -> une seule petite carte, au lieu de deux blocs vides.
              <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-suivi">
                <h3 id="rt-bloc-suivi" className="rt-bloc-titre">Conditions et notes</h3>
                <div className="v4-vides">
                  <p className="v4-vide"><Ic n="liste" /><span><b>Conditions suspensives</b>Aucune saisie</span></p>
                  <p className="v4-vide"><Ic n="note" /><span><b>Notes</b>Aucune note</span></p>
                </div>
              </section>
            ) : (
              <>
            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-conditions">
              <h3 id="rt-bloc-conditions" className="rt-bloc-titre">Conditions suspensives</h3>
              {!conditions.length ? <p className="rt-mute">Aucune condition saisie.</p> : (
                <ul className="rt-conditions">
                  {conditions.map((condition, index) => {
                    const etat = String(condition.etat ?? '')
                    const echeance = dateEnClair(condition.date_echeance)
                    return (
                      <li key={`${condition.kind}-${condition.rang ?? index}`} className="rt-condition">
                        <b>{condition.libelle}</b>
                        {ETAT_CONDITION[etat] ? (
                          <>
                            {echeance ? <span className="rt-mute">échéance {echeance}</span> : null}
                            <span className={`v3-etat-c v3-c-${etat}`}><Ic n={ICONE_CONDITION[etat]} />{ETAT_CONDITION[etat]}</span>
                          </>
                        ) : (
                          <span className="rt-mute">{[echeance ? `échéance ${echeance}` : null, condition.etat].filter(Boolean).join(' · ')}</span>
                        )}
                      </li>
                    )
                  })}
                </ul>
              )}
            </section>

            <section className="rt-carte rt-bloc" aria-labelledby="rt-bloc-notes">
              <h3 id="rt-bloc-notes" className="rt-bloc-titre">Notes</h3>
              {!notes.length ? <p className="rt-mute">Aucune note sur ce dossier.</p> : (
                <ul className="rt-notes">
                  {notes.map((note, index) => (
                    <li key={`${note.kind}-${index}`}>
                      <span className="rt-indicateur-libelle"><Ic n="note" />{note.libelle}</span>
                      <p>{note.texte}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>

              </>
            )}
            <BlocHistorique chaineId={ligne.app_chaine_id} hektorAnnonceId={ligne.hektor_annonce_id} lignes={lignes} relecture={relecture} />
          </div>
        </div>
      )}
    </section>
  )
}

/** Les honoraires d'une ligne : entiers, ou SA part quand un négociateur est choisi et qu'elle n'est pas de 100 %. */
function SaPart({ honoraires, part }: { honoraires: number; part: number }) {
  if (Math.abs(part - 1) < 1e-9) return <>{formatEuros(honoraires)}</>
  return <span title={`sa part : ${entier.format(Math.round(part * 100))} % de ${formatEuros(honoraires)}`}>{formatEuros(honoraires * part)} <span className="rt-mute">· {entier.format(Math.round(part * 100))} %</span></span>
}

export default function RegistreTransactionsScreen({ isAdmin, libelleTypeBien, onOuvrirBien, onGeste, fenetreOuverte, onOuvrirContact }: RegistreTransactionsScreenProps) {
  // v3.1 : période, mois, filtre d'étape, tri et sens, « Où je suis nommé », agence et négociateur
  // sont gardés dans le navigateur (lecture une seule fois, à l'ouverture). La recherche ne l'est pas.
  const [depart] = useState(lireMemoire)
  const [annee, setAnnee] = useState<number | null>(depart.annee)
  const [mois, setMois] = useState(depart.mois)
  const [lignes, setLignes] = useState<RegistreDossierRow[]>([])
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState<string | null>(null)
  const [relecture, setRelecture] = useState(0)
  const [etape, setEtape] = useState<FiltreEtape>(depart.etape)
  const [recherche, setRecherche] = useState('')
  const [seulementNomme, setSeulementNomme] = useState(depart.nomme)
  const [tri, setTri] = useState<Tri>(depart.tri)
  const [sens, setSens] = useState<Sens>(depart.sens)
  const [agence, setAgence] = useState(depart.agence)
  const [nego, setNego] = useState(depart.nego)
  const [noms, setNoms] = useState<Map<string, string>>(new Map())
  const [page, setPage] = useState(1)
  const [repartitions, setRepartitions] = useState<Map<string, RepartitionLigne[]>>(new Map())
  // 04/11 : SA PART quand un négociateur est choisi -- la MÊME règle de calcul que le pilotage (lib/repartitionEffective.ts :
  // sans répartition 100 % au négociateur du mandat, un seul côté saisi recopié, total ramené à 100 %). Le registre des
  // négociateurs donne la personne de l'e-mail choisi ; la répartition de toute la période est lue à part.
  const [repere, setRepere] = useState<RepereNegos | null>(null)
  const [repTout, setRepTout] = useState<{ cle: string; lu: Map<string, RepartitionLigne[]> } | null>(null)
  const [ouverte, setOuverte] = useState<RegistreDossierRow | null>(null)
  const [relectureFiche, setRelectureFiche] = useState(0)
  const fenetreEtaitOuverte = useRef(false)

  // Agence et négociateur : des filtres d'ADMIN. Gardés en mémoire, mais sans effet pour un négociateur.
  const agenceActive = isAdmin ? agence : ''
  const negoActif = isAdmin ? nego : ''
  // Le mois n'a de sens que dans une année.
  const moisActif = annee == null ? '' : mois

  useEffect(() => {
    ecrireMemoire({ annee, mois, etape, tri, sens, nomme: seulementNomme, agence, nego })
  }, [annee, mois, etape, tri, sens, seulementNomme, agence, nego])

  // À la fermeture de la fenêtre de statut ouverte depuis la fiche : on relit la fiche et la liste.
  useEffect(() => {
    if (fenetreOuverte) {
      fenetreEtaitOuverte.current = true
      return
    }
    if (!fenetreEtaitOuverte.current) return
    fenetreEtaitOuverte.current = false
    setRelectureFiche((valeur) => valeur + 1)
    setRepartitions(new Map())
    setRelecture((valeur) => valeur + 1)
  }, [fenetreOuverte])

  // La fiche suit la ligne relue (étape, montants) sans se fermer.
  useEffect(() => {
    setOuverte((avant) => (avant ? lignes.find((ligne) => ligne.app_chaine_id === avant.app_chaine_id) ?? avant : avant))
  }, [lignes])

  useEffect(() => {
    let annule = false
    setChargement(true)
    setErreur(null)
    loadRegistreDossiers(annee)
      .then((resultat) => {
        if (!annule) setLignes(resultat)
      })
      .catch((cause: unknown) => {
        console.error('[registre des transactions] lecture impossible', cause)
        if (!annule) {
          setLignes([])
          setErreur('Les dossiers n’ont pas pu être chargés. Réessayez dans un instant.')
        }
      })
      .finally(() => {
        if (!annule) setChargement(false)
      })
    return () => {
      annule = true
    }
  }, [annee, relecture])

  // v3.1 : le NOM des négociateurs, en une lecture pour les e-mails de la liste (fiche et menu admin).
  useEffect(() => {
    const manquants = Array.from(new Set(lignes.map((ligne) => String(ligne.negociateur_email ?? '').trim().toLowerCase()).filter((email) => email && !noms.has(email))))
    if (!manquants.length) return
    let annule = false
    loadNomsNegociateurs(manquants).then((lus) => {
      if (annule || !lus.size) return
      setNoms((avant) => {
        const suite = new Map(avant)
        for (const [cle, nom] of lus) suite.set(cle, nom)
        return suite
      })
    })
    return () => {
      annule = true
    }
  }, [lignes, noms])

  useEffect(() => setPage(1), [annee, moisActif, etape, recherche, seulementNomme, tri, sens, agenceActive, negoActif])

  useEffect(() => {
    if (!isAdmin) return undefined
    let annule = false
    lireRegistre().then(
      (registre) => { if (!annule) setRepere(construireRepereDepuisRegistre(registre)) },
      (cause: unknown) => console.error('[registre des transactions] registre des négociateurs illisible', cause),
    )
    return () => { annule = true }
  }, [isAdmin])
  // Une année entière (~15 lectures) dès l'ouverture pour un admin : le menu propose aussi ceux qui n'ont qu'une part sur
  // le bien d'un autre. « Toutes années » : seulement quand un négociateur est choisi.
  const cleRep = `${annee ?? 'tout'}-${relecture}-${lignes.length}`
  const lireToutesRep = isAdmin && (annee != null || Boolean(negoActif)) && lignes.length > 0
  useEffect(() => {
    if (!lireToutesRep) return undefined
    let annule = false
    lireRepartitions(lignes.map((ligne) => ligne.app_chaine_id)).then(
      (lu) => { if (!annule) setRepTout({ cle: cleRep, lu }) },
      (cause: unknown) => console.error('[registre des transactions] répartition illisible', cause),
    )
    return () => { annule = true }
  }, [lireToutesRep, lignes, cleRep])
  const comptees = useMemo(() => (repere && repTout && repTout.cle === cleRep ? compterRepartitions(lignes, repTout.lu, repere) : null), [repere, repTout, cleRep, lignes])
  const personneChoisie = negoActif && repere ? repere.parEmail.get(negoActif) ?? null : null
  // Tant que sa part n'est pas calculable (lecture en cours, ou e-mail inconnu du registre), le filtre reste celui
  // d'avant : les biens qu'il suit, honoraires entiers -- et l'indicateur le dit.
  const partActive = Boolean(negoActif && personneChoisie && comptees)
  const partDuDossier = useMemo(() => (ligne: RegistreDossierRow) => (
    comptees && personneChoisie ? partDe(comptees.get(String(ligne.app_chaine_id)) ?? [], personneChoisie) : 1), [comptees, personneChoisie])

  const nomDuNegociateur = (email: string | null | undefined) => noms.get(String(email ?? '').trim().toLowerCase()) ?? null
  const aDesNommes = useMemo(() => lignes.some((ligne) => ligne.je_suis_nomme), [lignes])
  // Sans dossier « nommé », la case est cachée : un réglage gardé ne doit pas vider la liste en silence.
  const nommeActif = seulementNomme && aDesNommes

  // La BASE de l'écran : l'année (lue en base), puis le mois, l'agence et le négociateur. Indicateurs,
  // compteurs, sous-titre et liste la suivent. ⚠ L'année d'un dossier = left(date_dernier_evenement, 4)
  // (règle de la base) : le mois se filtre donc ici, sur les caractères 6-7 de la même date.
  const lignesBase = useMemo(() => lignes.filter((ligne) => {
    if (moisActif) {
      const date = String(ligne.date_dernier_evenement ?? '').trim()
      if (!date || date.startsWith('0000') || Number(date.slice(5, 7)) !== Number(moisActif)) return false
    }
    // Comparé SANS les espaces de bord, comme la liste des choix : les 34 dossiers d'Ambert arrivent
    // en « Groupe GTI Ambert   » (mesuré le 02/11) et le filtre n'en trouvait aucun.
    if (agenceActive && (ligne.agence_nom ?? '').trim() !== agenceActive.trim()) return false
    if (negoActif) {
      if (partActive) { if (!(partDuDossier(ligne) > 0)) return false }
      else if (String(ligne.negociateur_email ?? '').trim().toLowerCase() !== negoActif) return false
    }
    return true
  }), [lignes, moisActif, agenceActive, negoActif, partActive, partDuDossier])

  const chiffres = useMemo(() => {
    const ventes = lignesBase.filter((ligne) => ligne.etape === 'vendu' && (annee == null || anneeDe(ligne.date_vente) === annee))
    const compromis = lignesBase.filter((ligne) => ligne.etape === 'compromis')
    const offres = lignesBase.filter((ligne) => OFFRES.includes(ligne.etape))
    // Honoraires : SA PART quand un négociateur est choisi ; le volume (prix) reste entier, comme au pilotage.
    const somme = (liste: RegistreDossierRow[], cle: 'montant' | 'honoraires') => liste.reduce((total, ligne) => total + (ligne[cle] ?? 0) * (cle === 'honoraires' && partActive ? partDuDossier(ligne) : 1), 0)
    const parEtape = new Map<RegistreEtape, number>()
    for (const ligne of lignesBase) parEtape.set(ligne.etape, (parEtape.get(ligne.etape) ?? 0) + 1)
    return {
      ventes: ventes.length,
      volume: somme(ventes, 'montant'),
      honoraires: somme(ventes, 'honoraires'),
      compromis: compromis.length,
      honorairesAttendus: somme(compromis, 'honoraires'),
      offres: offres.length,
      parEtape,
    }
  }, [lignesBase, annee, partActive, partDuDossier])

  // Le tri, dans les deux sens ; un dossier sans prix ou sans honoraires reste en bas.
  const comparer = useMemo(() => {
    const facteur = sens === 'asc' ? -1 : 1
    const date = (ligne: RegistreDossierRow) => String(ligne.date_dernier_evenement ?? '').replace(/^0000.*/, '')
    return (a: RegistreDossierRow, b: RegistreDossierRow) => {
      if (tri === 'prix' || tri === 'honoraires') {
        const cle = tri === 'prix' ? 'montant' : 'honoraires'
        const va = a[cle]
        const vb = b[cle]
        if (va == null || vb == null) return va == null && vb == null ? b.app_chaine_id - a.app_chaine_id : va == null ? 1 : -1
        return facteur * (vb - va) || b.app_chaine_id - a.app_chaine_id
      }
      return facteur * (date(b).localeCompare(date(a)) || b.app_chaine_id - a.app_chaine_id)
    }
  }, [tri, sens])

  const filtrees = useMemo(() => {
    const mots = sansAccents(recherche.trim()).split(/\s+/).filter(Boolean)
    const resultat = lignesBase.filter((ligne) => {
      if (etape === 'en_cours' && !EN_COURS.includes(ligne.etape)) return false
      if (etape === 'offres' && !OFFRES.includes(ligne.etape)) return false
      if (etape && etape !== 'en_cours' && etape !== 'offres' && ligne.etape !== etape) return false
      if (nommeActif && !ligne.je_suis_nomme) return false
      if (!mots.length) return true
      const texte = sansAccents(
        [ligne.ville, ligne.code_postal, ligne.acquereur_nom, ligne.numero_mandat, ligne.app_chaine_id, ligne.hektor_annonce_id, ligne.agence_nom, ligne.negociateur_email, nomDuNegociateur(ligne.negociateur_email)]
          .filter((valeur) => valeur != null && valeur !== '')
          .join(' '),
      )
      return mots.every((mot) => texte.includes(mot))
    })
    return resultat.sort(comparer)
    // `noms` : la recherche trouve aussi le nom du négociateur.
  }, [lignesBase, etape, recherche, nommeActif, comparer, noms])

  const pages = Math.max(1, Math.ceil(filtrees.length / PAR_PAGE))
  const pageCourante = Math.min(page, pages)
  const visibles = useMemo(() => filtrees.slice((pageCourante - 1) * PAR_PAGE, pageCourante * PAR_PAGE), [filtrees, pageCourante])

  // La répartition se lit pour la PAGE affichée seulement (50 dossiers) : elle n'est pas dans la liste.
  useEffect(() => {
    const manquantes = visibles.map((ligne) => String(ligne.app_chaine_id)).filter((id) => !repartitions.has(id))
    if (!manquantes.length) return
    let annule = false
    loadRepartitionsDesChaines(manquantes).then((lues) => {
      if (annule) return
      setRepartitions((avant) => {
        const suite = new Map(avant)
        for (const id of manquantes) suite.set(id, lues.get(id) ?? [])
        return suite
      })
    })
    return () => {
      annule = true
    }
  }, [visibles, repartitions])

  // v3.1 : précédent / suivant, dans l'ordre de la liste filtrée et triée ; si le dossier ouvert n'y
  // est plus (filtre changé), on repart de la liste complète de la période.
  const ordreNavigation = useMemo(() => {
    if (!ouverte) return [] as RegistreDossierRow[]
    if (filtrees.some((ligne) => ligne.app_chaine_id === ouverte.app_chaine_id)) return filtrees
    return [...lignes].sort(comparer)
  }, [ouverte, filtrees, lignes, comparer])

  const typeEnClair = (code: string | null) => {
    if (!code) return null
    const libelle = libelleTypeBien ? libelleTypeBien(code) : code
    return libelle && libelle !== '-' ? libelle : null
  }

  const ouvrir = (ligne: RegistreDossierRow) => setOuverte(ligne)

  if (ouverte) {
    const index = ordreNavigation.findIndex((ligne) => ligne.app_chaine_id === ouverte.app_chaine_id)
    const precedente = index > 0 ? ordreNavigation[index - 1] : null
    const suivante = index >= 0 && index < ordreNavigation.length - 1 ? ordreNavigation[index + 1] : null
    return (
      <FicheDossier
        ligne={ouverte}
        type={typeEnClair(ouverte.type_bien)}
        relecture={relectureFiche}
        onRetour={() => setOuverte(null)}
        onOuvrirBien={onOuvrirBien}
        onGeste={onGeste}
        onOuvrirContact={onOuvrirContact}
        nomNegociateur={nomDuNegociateur(ouverte.negociateur_email)}
        navigation={index < 0 ? null : {
          position: index + 1,
          total: ordreNavigation.length,
          precedent: precedente ? () => setOuverte(precedente) : null,
          suivant: suivante ? () => setOuverte(suivante) : null,
        }}
      />
    )
  }

  const periode = annee == null ? 'toutes années' : moisActif ? `${MOIS[Number(moisActif) - 1]} ${annee}` : String(annee)
  const nombreDossiers = lignesBase.length
  const filtres: Array<{ cle: FiltreEtape; libelle: string; nombre: number }> = [
    { cle: null, libelle: 'Tous', nombre: lignesBase.length },
    { cle: 'en_cours', libelle: 'En cours', nombre: EN_COURS.reduce((total, cle) => total + (chiffres.parEtape.get(cle) ?? 0), 0) },
    ...ETAPES.map((item) => ({ cle: item.cle, libelle: item.libelle, nombre: chiffres.parEtape.get(item.cle) ?? 0 })),
  ]
  const detailPart = !negoActif ? 'entrée + sortie, sur les ventes'
    : partActive ? 'sa part, selon la répartition'
      : repere && !personneChoisie ? 'les biens qu’il suit (inconnu du registre des négociateurs)' : 'les biens qu’il suit (calcul de sa part…)'
  const indicateurs: Array<{ libelle: string; valeur: string; detail: string; filtre: Exclude<FiltreEtape, null> }> = [
    { libelle: `Honoraires actés · ${periode}`, valeur: formatMillions(chiffres.honoraires), detail: detailPart, filtre: 'vendu' },
    { libelle: 'Ventes actées', valeur: entier.format(chiffres.ventes), detail: chargement ? '' : `${formatMillions(chiffres.volume)} de volume`, filtre: 'vendu' },
    { libelle: 'Sous compromis', valeur: entier.format(chiffres.compromis), detail: chargement ? '' : `${formatMillions(chiffres.honorairesAttendus)} d’honoraires attendus${partActive ? ' (sa part)' : ''}`, filtre: 'compromis' },
    { libelle: 'Offres en cours', valeur: entier.format(chiffres.offres), detail: 'proposées ou acceptées', filtre: 'offres' },
  ]

  // Les menus d'admin : options tirées des lignes chargées pour la période.
  const agences = Array.from(new Set(lignes.map((ligne) => (ligne.agence_nom ?? '').trim()).filter(Boolean))).sort((a, b) => a.localeCompare(b, 'fr'))
  if (agence && !agences.includes(agence)) agences.push(agence)
  const negociateurs = Array.from(new Set(lignes.map((ligne) => String(ligne.negociateur_email ?? '').trim().toLowerCase()).filter(Boolean)))
    .map((email) => ({ email, nom: noms.get(email) ?? email }))
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'))
  // 04/11 : aussi ceux qui n'ont qu'une PART (sur le bien d'un autre), par leur personne du registre.
  if (comptees && repere) {
    const deja = new Set(negociateurs.map((item) => repere.parEmail.get(item.email) ?? item.email))
    for (const parts of comptees.values()) for (const x of parts) {
      const qui = x.personne ? repere.personnes.get(x.personne) : undefined
      const email = qui ? [...qui.emails][0] : undefined
      if (!qui || !email || deja.has(qui.cle) || /supprim/i.test(qui.nom)) continue
      deja.add(qui.cle)
      negociateurs.push({ email, nom: qui.nom })
    }
    negociateurs.sort((a, b) => a.nom.localeCompare(b.nom, 'fr'))
  }
  if (nego && !negociateurs.some((item) => item.email === nego)) negociateurs.push({ email: nego, nom: noms.get(nego) ?? nego })

  const horsDefaut = annee !== MEMOIRE_DEFAUT.annee || moisActif !== '' || etape !== null || tri !== 'recent' || sens !== 'desc' || nommeActif
    || Boolean(agenceActive) || Boolean(negoActif)
  const reinitialiser = () => {
    setAnnee(MEMOIRE_DEFAUT.annee)
    setMois('')
    setEtape(null)
    setTri('recent')
    setSens('desc')
    setSeulementNomme(false)
    setAgence('')
    setNego('')
  }

  // L'en-tête triable : 1er clic = du plus haut au plus bas (comme le menu), 2e clic = l'inverse.
  const enTeteTriable = (libelle: string, cle: Tri, quoi: string, droite = false) => {
    const actif = tri === cle
    return (
      <th scope="col" className={droite ? 'rt-droite' : undefined} aria-sort={actif ? (sens === 'asc' ? 'ascending' : 'descending') : undefined}>
        <button
          type="button"
          className={`v31-th${actif ? ' is-on' : ''}`}
          title={`Trier par ${quoi}`}
          onClick={() => {
            if (actif) setSens((avant) => (avant === 'asc' ? 'desc' : 'asc'))
            else {
              setTri(cle)
              setSens('desc')
            }
          }}
        >
          {libelle}<Ic n={actif ? (sens === 'asc' ? 'flHaut' : 'flBas') : 'flDeux'} />
        </button>
      </th>
    )
  }

  return (
    <section className="rt-ecran" aria-labelledby="rt-titre">
      <header className="rt-entete">
        <div className="rt-entete-titres">
          <span className="rt-surtitre">Ventes</span>
          <h1 id="rt-titre" className="rt-titre">Registre des transactions</h1>
          <p className="rt-sous-titre">
            {chargement ? 'Chargement des dossiers…' : <><b className="rt-num">{entier.format(nombreDossiers)}</b>{` dossier${nombreDossiers > 1 ? 's' : ''} · ${periode} · une ligne par dossier, de l’offre à l’acte`}</>}
            {!isAdmin ? ' · vos biens et les dossiers où vous êtes nommé' : ''}
          </p>
        </div>
        <div className="rt-periode v31-periode">
          <label className="v31-lab">
            <span>Période</span>
            <Selecteur icone="calendrier">
              <select value={annee == null ? 'tout' : String(annee)} onChange={(event) => setAnnee(event.target.value === 'tout' ? null : Number(event.target.value))}>
                {ANNEES.map((valeur) => (
                  <option key={valeur} value={valeur}>{valeur}</option>
                ))}
                <option value="tout">Toutes les années</option>
              </select>
            </Selecteur>
          </label>
          <label className="v31-lab">
            <span className="rt-cache">Mois</span>
            <Selecteur icone="calendrier">
              <select
                value={moisActif}
                disabled={annee == null}
                title={annee == null ? 'Choisissez une année pour filtrer par mois' : undefined}
                onChange={(event) => setMois(event.target.value)}
              >
                <option value="">Toute l’année</option>
                {MOIS.map((nom, index) => (
                  <option key={nom} value={String(index + 1)}>{nom.charAt(0).toUpperCase() + nom.slice(1)}</option>
                ))}
              </select>
            </Selecteur>
          </label>
        </div>
      </header>

      <div className="rt-indicateurs" aria-label="Indicateurs">
        {indicateurs.map((indicateur) => {
          const actif = etape === indicateur.filtre
          return (
            <button
              key={indicateur.libelle}
              type="button"
              className={`rt-carte rt-indicateur v31-kpi${actif ? ' is-actif' : ''}`}
              aria-pressed={actif}
              title={actif ? 'Retirer ce filtre' : 'Filtrer la liste sur ces dossiers'}
              onClick={() => setEtape(actif ? null : indicateur.filtre)}
            >
              <span className="rt-indicateur-libelle">{indicateur.libelle}</span>
              <strong className="rt-indicateur-valeur">{chargement ? <span className="sk v3-sk-kpi" /> : indicateur.valeur}</strong>
              <span className="rt-indicateur-detail">{indicateur.detail}</span>
              <span className="v31-kpi-ic" aria-hidden="true"><Ic n={actif ? 'croix' : 'filtre'} /></span>
            </button>
          )
        })}
      </div>

      <div className="rt-carte rt-liste">
        <div className="rt-outils">
          <label className="rt-recherche">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth={2} /><path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth={2} strokeLinecap="round" /></svg>
            <span className="rt-cache">Rechercher un dossier</span>
            <input
              type="search"
              value={recherche}
              onChange={(event) => setRecherche(event.target.value)}
              placeholder="Ville, acquéreur, n° de mandat, de dossier ou d’annonce…"
            />
          </label>
          <label className="rt-tri">
            <span className="rt-cache">Trier</span>
            <Selecteur icone="trier">
              <select
                value={tri}
                onChange={(event) => {
                  // Le menu trie toujours du plus haut au plus bas ; l'ordre inverse passe par l'en-tête.
                  setTri(event.target.value as Tri)
                  setSens('desc')
                }}
              >
                <option value="recent">Plus récents</option>
                <option value="prix">Prix le plus haut</option>
                <option value="honoraires">Honoraires les plus hauts</option>
              </select>
            </Selecteur>
          </label>
          {isAdmin ? (
            <>
              <label className="rt-tri v31-f">
                <span className="rt-cache">Agence</span>
                <Selecteur icone="agence">
                  <select value={agence} onChange={(event) => setAgence(event.target.value)}>
                    <option value="">Toutes les agences</option>
                    {agences.map((nom) => <option key={nom} value={nom}>{nom}</option>)}
                  </select>
                </Selecteur>
              </label>
              <label className="rt-tri v31-f">
                <span className="rt-cache">Négociateur</span>
                <Selecteur icone="personnes">
                  <select value={nego} onChange={(event) => setNego(event.target.value)}>
                    <option value="">Tous les négociateurs</option>
                    {negociateurs.map((item) => <option key={item.email} value={item.email}>{item.nom}</option>)}
                  </select>
                </Selecteur>
              </label>
            </>
          ) : null}
          {aDesNommes ? (
            <label className="rt-case">
              <input type="checkbox" checked={seulementNomme} onChange={(event) => setSeulementNomme(event.target.checked)} />
              <span>Où je suis nommé</span>
            </label>
          ) : null}
          {horsDefaut ? (
            <span className="v31-garde">
              <Ic n="coche" />Filtres gardés · <button type="button" className="v31-lien" onClick={reinitialiser}>Réinitialiser</button>
            </span>
          ) : null}
        </div>
        <div className="rt-filtres" role="group" aria-label="Étape du dossier">
          {filtres.map((filtre) => (
            <button
              key={filtre.cle ?? 'tous'}
              type="button"
              className={`rt-filtre${etape === filtre.cle ? ' is-actif' : ''}`}
              aria-pressed={etape === filtre.cle}
              onClick={() => setEtape(filtre.cle)}
            >
              {filtre.cle && filtre.cle !== 'en_cours' && filtre.cle !== 'offres' ? <Ic n={ICONE_ETAPE[filtre.cle]} className={`v3-fi is-${filtre.cle}`} /> : null}
              {filtre.libelle}
              <span className="rt-compte">{chargement ? '…' : entier.format(filtre.nombre)}</span>
            </button>
          ))}
        </div>

        {erreur ? (
          <div className="rt-etat rt-etat-erreur" role="alert">
            <span className="v3-etat-ic err"><Ic n="alerte" /></span>
            <p>{erreur}</p>
            <button type="button" className="rt-bouton" onClick={() => setRelecture((valeur) => valeur + 1)}><Ic n="rafraichir" />Réessayer</button>
          </div>
        ) : chargement ? (
          <div className="rt-etat" role="status"><Chargement texte="Chargement des dossiers…" lignes={[92, 78, 86, 70, 82]} /></div>
        ) : !filtrees.length ? (
          lignesBase.length || agenceActive || negoActif ? (
            <div className="rt-etat"><span className="v3-etat-ic"><Ic n="search" /></span>Aucun dossier ne correspond à ces critères.</div>
          ) : (
            <div className="rt-etat"><span className="v3-etat-ic"><Logo /></span>{`Aucun dossier pour ${periode}.`}</div>
          )
        ) : (
          <>
            <div className="rt-table-boite">
              <table className="rt-table">
                <colgroup>
                  {/* Largeurs fixes. Mesure en ligne du 02/11 à 1 280 px : la table fait 1 083 px, le
                      parcours était tassé et les noms de la répartition coupés -> on les élargit, le
                      bien prend le reste (≈ 220 px). */}
                  <col style={{ width: 140 }} />
                  <col />
                  <col style={{ width: '9%' }} />
                  <col style={{ width: 230 }} />
                  <col style={{ width: 86 }} />
                  <col style={{ width: 94 }} />
                  <col style={{ width: 212 }} />
                </colgroup>
                <thead>
                  <tr>
                    {enTeteTriable('Dossier', 'recent', 'date du dernier événement')}
                    <th scope="col">Bien</th>
                    <th scope="col">Acquéreur</th>
                    <th scope="col">Parcours</th>
                    {enTeteTriable('Prix', 'prix', 'prix', true)}
                    {enTeteTriable('Honoraires', 'honoraires', 'honoraires', true)}
                    <th scope="col">Répartition</th>
                  </tr>
                </thead>
                <tbody>
                  {visibles.map((ligne) => {
                    const type = typeEnClair(ligne.type_bien)
                    const sousTitre = [type, ligne.numero_mandat ? `mandat ${ligne.numero_mandat}` : null].filter(Boolean).join(' · ') || '—'
                    return (
                      <tr key={ligne.app_chaine_id} className="is-ouvrable" onClick={() => ouvrir(ligne)}>
                        <td>
                          <div className="rt-dossier">
                            <Pastille etape={ligne.etape} />
                            <span className="rt-mute rt-num">N° {ligne.app_chaine_id}{ligne.je_suis_nomme ? <> · <span className="rt-nomme">nommé</span></> : null}</span>
                          </div>
                        </td>
                        <td>
                          <div className="rt-bien">
                            {ligne.photo_url_listing ? (
                              <img className="rt-vignette" src={ligne.photo_url_listing} alt="" loading="lazy" />
                            ) : (
                              <span className="rt-vignette v3-vide" title="Pas de photo"><Ic n={iconeDuType(type)} /></span>
                            )}
                            <div className="rt-bien-texte">
                              <button type="button" className="rt-lien" title={ligne.ville || undefined} onClick={(event) => { event.stopPropagation(); ouvrir(ligne) }}>
                                {ligne.ville || 'Ville inconnue'}
                              </button>
                              <span className="rt-mute" title={sousTitre}>{sousTitre}</span>
                            </div>
                          </div>
                        </td>
                        <td>{ligne.acquereur_nom ? <span className="v3-clamp" title={ligne.acquereur_nom}>{ligne.acquereur_nom}</span> : <span className="rt-mute">—</span>}</td>
                        <td><Parcours ligne={ligne} /></td>
                        <td className="rt-droite rt-num">{formatEuros(ligne.montant)}</td>
                        <td className="rt-droite rt-num">{ligne.honoraires ? <SaPart honoraires={ligne.honoraires} part={partActive ? partDuDossier(ligne) : 1} /> : <span className="rt-mute">—</span>}</td>
                        <td><Repartition lignes={repartitions.get(String(ligne.app_chaine_id))} /></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <ul className="rt-cartes" aria-label="Dossiers">
              {visibles.map((ligne) => {
                const type = typeEnClair(ligne.type_bien)
                const derniere = dateEnClair(ligne.date_dernier_evenement)
                const contenu = (
                  <>
                    <span className="rt-carte-haut">
                      <Pastille etape={ligne.etape} />
                      <span className="rt-mute rt-num">N° {ligne.app_chaine_id}{derniere ? ` · ${derniere}` : ''}</span>
                    </span>
                    <span className="rt-carte-milieu">
                      <span className="rt-carte-bien">
                        <b>{ligne.ville || 'Ville inconnue'}</b>
                        <span className="rt-mute">{[type, ligne.acquereur_nom].filter(Boolean).join(' · ') || '—'}</span>
                      </span>
                      <span className="rt-carte-prix">
                        <b className="rt-num">{formatEuros(ligne.montant)}</b>
                        <span className="rt-mute rt-num">{ligne.honoraires ? <><SaPart honoraires={ligne.honoraires} part={partActive ? partDuDossier(ligne) : 1} /> d’honoraires</> : 'sans honoraires'}</span>
                      </span>
                    </span>
                  </>
                )
                return (
                  <li key={ligne.app_chaine_id}>
                    <button type="button" className="rt-carte-dossier" onClick={() => ouvrir(ligne)}>{contenu}</button>
                  </li>
                )
              })}
            </ul>

            <nav className="rt-pages" aria-label="Pages">
              <span className="rt-mute">
                <b className="rt-num">{entier.format((pageCourante - 1) * PAR_PAGE + 1)}–{entier.format(Math.min(pageCourante * PAR_PAGE, filtrees.length))}</b> sur <b className="rt-num">{entier.format(filtrees.length)}</b>
              </span>
              <span className="rt-pages-boutons">
                <button type="button" className="rt-bouton" disabled={pageCourante <= 1} onClick={() => setPage(pageCourante - 1)}><Ic n="left" />Précédent</button>
                <span className="rt-num">{pageCourante} / {pages}</span>
                <button type="button" className="rt-bouton" disabled={pageCourante >= pages} onClick={() => setPage(pageCourante + 1)}>Suivant<Ic n="right" /></button>
              </span>
            </nav>
          </>
        )}
      </div>
    </section>
  )
}
