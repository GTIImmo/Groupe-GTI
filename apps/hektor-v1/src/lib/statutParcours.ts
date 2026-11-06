// Modale « Changer le statut », refonte VISUELLE (lot 1, 06/11/2026) — LE PARCOURS.
//
// Plan : notice/PLAN_REFONTE_VISUELLE_MODALE_STATUT_2026-11-05.md §2 · matrice : audit §10.4 et §11.
//
// Ce module ne DÉCIDE rien : il ORIENTE. Il lit la situation du bien (statut de l'annonce, dossiers
// d'affaire, mandat) et dit, pour chacune des 5 cartes, si elle est l'étape actuelle, l'étape conseillée,
// hors du parcours logique (possible, assumé), en lecture seule (ce que la BASE refuse déjà) ou sans effet.
//
// ⛔ AUCUNE RÈGLE N'EST RÉÉCRITE ICI. Les gardes du projet (etatFermeAuxTransactions, bienEngage,
//   dossiersOuvertsDuBien…) vivent dans App.tsx et sont PASSÉES en paramètre : une seule copie de chaque
//   règle, comme le veut le commentaire de dossiersOuvertsDuBien (« deux copies d'une formule divergent »).
// ⛔ Rien n'est bloqué : décision de Frédéric du 05/11 (audit §11), la modale est réservée à admin et
//   manager, TOUT reste accessible. Une carte « hors parcours » ou « lecture seule » reste cliquable ;
//   les boutons et leurs conditions restent ceux d'aujourd'hui.
// ⚠ La situation 5 de la matrice (annulation du mandat demandée) n'est pas reconnue : la modale ne lit pas
//   les demandes, et ce lot n'ajoute aucune lecture. Aucune n'était en attente le 05/11.

import type { AffaireLedgerRow, HektorAnnonceStatusTarget } from './api'
// Les types seulement, redonnés à la vue : ModaleStatutV2.tsx n'importe RIEN de lib/api (contrôle de parité).
export type { AffaireLedgerRow, HektorAnnonceStatusTarget }

export type EtatCarte = 'libre' | 'hors' | 'lecture' | 'sans_effet'

export type CarteParcours = {
  statut: HektorAnnonceStatusTarget
  etat: EtatCarte
  /** l'étape où le bien se trouve (lu sur le statut de l'annonce) */
  actuel: boolean
  /** l'étape logique suivante */
  conseille: boolean
  /** pourquoi la carte est hors parcours, en lecture seule ou sans effet ; ou un avertissement sur une
   *  carte libre. Vide sinon. */
  raison: string
}

export type SituationParcours = {
  /** le numéro de la matrice de l'audit (§10.4), de 1 à 11 ; 5 n'est jamais rendu (voir l'en-tête) */
  numero: number
  conseille: HektorAnnonceStatusTarget | null
  actuel: HektorAnnonceStatusTarget | null
  cartes: CarteParcours[]
  /** ce que le guide doit dire en plus (mandat à contrôler, mandat échu), sans rien bloquer */
  avertissements: string[]
}

/** Ce que la situation lit — rien d'autre que ce que la modale a déjà en main. */
export type EntreeParcours = {
  statutAnnonce: string | null | undefined
  affaires: AffaireLedgerRow[]
  mandatDateFin?: string | null
  mandatValide: boolean
  /** jj du jour, AAAA-MM-JJ (paramètre pour l'essai) */
  aujourdhui: string
}

/** Les gardes du projet, passées telles quelles depuis App.tsx. */
export type GardesParcours = {
  etatFermeAuxTransactions: (d: { statut_annonce: string | null }) => 'vendu' | 'clos' | 'estimation' | null
  bienEngage: (lignes: AffaireLedgerRow[]) => boolean
  dossiersOuvertsDuBien: (lignes: AffaireLedgerRow[]) => Array<{ ouvert: boolean; genres: Set<string> }>
}

export const ORDRE_PARCOURS: HektorAnnonceStatusTarget[] = ['active', 'offer', 'compromise', 'sold', 'closed']

/** Le statut de l'annonce, ramené à une carte. « Estimation » n'en a pas : rien n'est encore en vente. */
export function carteDuStatut(statutAnnonce: string | null | undefined): HektorAnnonceStatusTarget | null {
  const s = String(statutAnnonce ?? '').trim().toLowerCase()
  if (!s) return null
  if (s.includes('vendu')) return 'sold'
  if (s.includes('clos')) return 'closed'
  if (s.includes('compromis')) return 'compromise'
  if (s.includes('offre')) return 'offer'
  if (s.includes('actif')) return 'active'
  return null
}

type Regle = { conseille: HektorAnnonceStatusTarget | null; cartes: Partial<Record<HektorAnnonceStatusTarget, [EtatCarte, string]>> }

const RARE_VENTE = 'Une vente sans compromis est rare : 5 ventes sur 640 depuis 2025.'

export function situationDuBien(e: EntreeParcours, g: GardesParcours): SituationParcours {
  const actuel = carteDuStatut(e.statutAnnonce)
  const ferme = g.etatFermeAuxTransactions({ statut_annonce: e.statutAnnonce ?? null })
  const dossiers = g.dossiersOuvertsDuBien(e.affaires).filter((d) => d.ouvert)
  const compromisVivant = dossiers.some((d) => d.genres.has('compromis'))
  const engage = g.bienEngage(e.affaires)
  const offresEnCours = dossiers.some((d) => d.genres.has('offre'))
  const fin = String(e.mandatDateFin ?? '').trim().slice(0, 10)
  // ⚠ « 0000-00-00 » est la date VIDE de Hektor : ce n'est pas un mandat échu en l'an zéro.
  const echu = /^\d{4}-\d{2}-\d{2}$/.test(fin) && !fin.startsWith('0000') && fin < e.aujourdhui
  const dejaActif = actuel === 'active' ? 'Le bien est déjà en vente.' : ''

  let numero: number
  let r: Regle
  if (ferme === 'vendu') {
    numero = 10
    r = { conseille: null, cartes: {
      active: ['hors', 'Rouvrir un bien vendu : à réserver à une nouvelle mise en vente.'],
      offer: ['lecture', 'Le bien est vendu : plus de nouvelle transaction.'],
      compromise: ['lecture', 'Le bien est vendu : plus de nouvelle transaction.'],
      closed: ['hors', 'Le mandat est clos chez nous à la date de la vente.'] } }
  } else if (ferme === 'clos') {
    numero = 11
    r = { conseille: null, cartes: {
      active: ['hors', 'Remettre en vente rouvre le mandat clos.'],
      offer: ['lecture', 'Le mandat est clos : plus de nouvelle transaction.'],
      compromise: ['lecture', 'Le mandat est clos : plus de nouvelle transaction.'],
      sold: ['lecture', 'Le mandat est clos : plus de nouvelle transaction.'],
      closed: ['sans_effet', 'Le mandat est déjà clos.'] } }
  } else if (ferme === 'estimation') {
    numero = 1
    r = { conseille: null, cartes: {
      active: ['hors', 'Un avis de valeur passe en vente par le mandat et sa validation.'],
      offer: ['lecture', 'Le bien est en estimation : pas encore de transaction.'],
      compromise: ['lecture', 'Le bien est en estimation : pas encore de transaction.'],
      sold: ['lecture', 'Le bien est en estimation : pas encore de transaction.'] } }
  } else if (compromisVivant) {
    numero = 8
    r = { conseille: 'sold', cartes: {
      active: ['hors', 'Un compromis est en cours. Remettre en vente ne l’annule pas.'],
      offer: ['lecture', 'L’offre de ce dossier ne se modifie plus : un compromis est en cours.'],
      closed: ['hors', 'Un compromis est en cours. Clore le mandat sans le régler laisse une affaire ouverte.'] } }
  } else if (engage) {
    numero = 7
    r = { conseille: 'compromise', cartes: {
      active: ['hors', 'Une offre est acceptée. Fais d’abord tomber l’affaire.'],
      offer: ['libre', 'Pas de nouvelle offre : le bien est engagé. Refuser une offre reste possible.'],
      sold: ['hors', RARE_VENTE],
      closed: ['hors', 'Une offre est acceptée. Fais d’abord tomber l’affaire.'] } }
  } else if (offresEnCours) {
    numero = 6
    r = { conseille: 'offer', cartes: {
      active: ['hors', 'Une offre est en cours. Remettre en vente ne la refuse pas.'],
      compromise: ['libre', 'Accepte d’abord l’offre : le compromis la reprendra.'],
      sold: ['hors', RARE_VENTE],
      closed: ['libre', 'Une offre est en cours : vérifie-la avant de clore.'] } }
  } else if (actuel === 'offer' || actuel === 'compromise') {
    numero = 9
    // ⚠ UN REGISTRE VIDE N'EST PAS « RIEN DE VIVANT ». La modale lit les affaires APRÈS son ouverture, et une
    //   lecture ratée rend une liste vide (openStatusChangeModal, « best-effort »). Un bien « Sous compromis »
    //   sans AUCUNE ligne : on ne sait pas, on ne conseille rien (vu en démonstration le 06/11).
    r = { conseille: e.affaires.length ? 'active' : null, cartes: {
      sold: ['hors', RARE_VENTE] } }
  } else if (echu) {
    numero = 4
    r = { conseille: null, cartes: {
      active: dejaActif ? ['sans_effet', dejaActif] : ['libre', ''],
      offer: ['hors', 'Le mandat est échu : vérifie qu’il court toujours avant d’agir.'],
      compromise: ['hors', 'Le mandat est échu : vérifie qu’il court toujours avant d’agir.'],
      sold: ['hors', 'Le mandat est échu : vérifie qu’il court toujours avant d’agir.'] } }
  } else if (!e.mandatValide) {
    numero = 2
    r = { conseille: null, cartes: {
      active: dejaActif ? ['sans_effet', dejaActif] : ['hors', 'Le mandat n’est pas encore validé par la Direction.'],
      offer: ['libre', 'Le mandat n’est pas encore validé par la Direction.'],
      compromise: ['libre', 'Le mandat n’est pas encore validé par la Direction.'],
      sold: ['hors', RARE_VENTE] } }
  } else {
    numero = 3
    r = { conseille: 'offer', cartes: {
      active: dejaActif ? ['sans_effet', dejaActif] : ['libre', ''],
      sold: ['hors', RARE_VENTE] } }
  }

  const avertissements: string[] = []
  if (numero === 9 && !e.affaires.length) {
    avertissements.push('Les affaires de ce bien ne sont pas lues : le conseil attend. Vérifie la rubrique Affaires.')
  }
  if (echu && numero !== 10 && numero !== 11) {
    avertissements.push(`Le mandat est échu depuis le ${fin.split('-').reverse().join('/')}. Les dates de mandat ne sont pas toutes fiables : vérifie avant d’agir.`)
  }
  if (!e.mandatValide && (numero === 2 || numero === 3 || numero === 6 || numero === 7)) {
    avertissements.push('Le mandat n’est pas encore validé par la Direction : la diffusion attend sa validation.')
  }

  const cartes = ORDRE_PARCOURS.map((statut): CarteParcours => {
    const [etat, raison] = r.cartes[statut] ?? ['libre', '']
    return { statut, etat, raison, actuel: actuel === statut, conseille: r.conseille === statut }
  })
  return { numero, conseille: r.conseille, actuel, cartes, avertissements }
}
