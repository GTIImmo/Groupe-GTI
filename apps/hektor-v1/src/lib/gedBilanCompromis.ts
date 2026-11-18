// GED (17/11/2026, lot 10c) -- « CE QUE DIT LE COMPROMIS » : le compromis lu, face à SA transaction, champ par champ.
// Fonction pure, sans lecture ni écriture : essais hors ligne dans test_ged_bilan.cjs. Elle remplace les cartes P4
// (lots 10a et 10b) : un seul chemin par champ, jamais deux.
// ⛔ LA DESTINATION DÉPEND DU CHAMP (Frédéric, 17/11) : prix, dates, séquestre, net vendeur et honoraires sont des champs
//   que Hektor connaît -- ils passent par la modale « Modifier le compromis », qui les ENVOIE à Hektor (la correction
//   « chez nous seulement » de ces champs a été retirée le 15/09). Les conditions suspensives sont gardées chez nous
//   (décision du 16/09). Chaque ligne porte donc sa destination, et l'écran la dit.
// GED lot 2 (17/11, « étends ») : le même bilan pour L'OFFRE lue (bilanOffre) -- montant, date, validité. ⛔ Une offre
//   ACCEPTÉE est figée chez Hektor (200 + corps vide, mesure du 13/10) et une offre REFUSÉE porte au registre la date du
//   refus (mémoire du 12/11) : leurs lignes se montrent, rien ne se propose (`fige`). L'acte de vente n'a PAS de bilan :
//   un bien vendu sort des annonces (0 sur 147 ventes depuis juin), sa fiche n'a pas de panneau des documents.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.28 et §12.29.
import {
  comparerNombre, conditionsGeneralesLues, conditionsLuesDe, dateLue, joursEntre, LIBELLE_CONDITION, lireDateIso, natureDuLibelle, nombreLu,
  normaliserTexte, personnesLuesDe, resoudreCible, texteLu, TOLERANCES, type NatureCondition,
} from './gedComparer'
import type { AffaireRegle } from './gedRegles'
import type { DocumentLu } from './gedReglesLues'

export type DestinationBilan = 'hektor' | 'nous'
// trancher : le compromis et la transaction disent deux choses ; ajouter : la transaction est vide ; accord : pareil
export type EtatBilan = 'trancher' | 'ajouter' | 'accord'
// la case de la modale « Modifier le compromis » que la valeur préremplit (null : à saisir à la main dans la modale)
export type ChampModale = 'amount' | 'transaction_date' | 'signature_date' | 'sequestration' | 'net_seller_price' | 'validity_days'
export type LigneBilan = {
  cle: string                 // « B.sequestre », « B.condition.preemption » : avec la valeur, la clé d'une décision
  libelle: string
  destination: DestinationBilan
  etat: EtatBilan
  lu: string                  // la valeur du compromis, en clair
  valeur: string              // la même, telle qu'elle s'écrit (AAAA-MM-JJ, euros sans espace)
  transaction: string | null  // la valeur de la transaction, en clair ; null = vide
  page: number | null
  note: string | null
  champModale: ChampModale | null
  condition: { nature: NatureCondition; libelle: string; date: string | null; catalogueId: string | null; retirer: boolean } | null
  regle: string | null        // la ligne « À regarder » qui dit la même chose (L7, L20 ; lot 3 : L6, L15, L16)
  // lot 10c (audit) : la valeur de la transaction n'est pas (encore) chez Hektor -- carnet seul, ou envoyée sans retour
  attente: 'jamais_envoye' | 'en_route' | 'echec' | null
  // lot 2 : la transaction ne se modifie pas d'ici (offre acceptée ou refusée) -- la raison, dite ; rien ne se propose
  fige: string | null
  // lot 3 (18/11) : une case de la FICHE DU BIEN (nom Hektor, par editAnnonceOptimistic) et ce que la fiche portait quand
  // le bilan a été calculé (null = vide) -- l'écriture relit la case et ne part que si elle le porte encore
  champFiche: string | null
  temoin: string | null
}
// lot 3 (18/11) : les genres de la FICHE DU BIEN -- un par document (le DPE, l'état des risques, la fiche synthétique, l'appel
// de fonds, le métré)
// lot A (18/11) : les six rapports de diagnostic et le dossier de diagnostics (DDT), chacun SA fenêtre
export type GenreFiche = 'dpe' | 'erp' | 'copro_lots' | 'copro_charges' | 'copro_ag' | 'taxe' | 'titre' | 'surface' | 'ddt'
  | 'diag_electricite' | 'diag_gaz' | 'diag_plomb' | 'diag_termites' | 'diag_amiante' | 'diag_assainissement'
// lot F (18/11) : les PIÈCES DES PERSONNES (pièce d'identité, fiche de renseignements) -- une fenêtre par document, qui
// corrige la fiche d'un CONTACT. Elles se tranchent comme la fiche (même droit, pas de modale) : estGenreFiche les compte,
// et l'écriture les aiguille d'abord par estGenrePersonne (App.tsx, appliquerBilanPersonne).
export type GenrePersonne = 'identite' | 'renseignements'
export type GenreBilan = 'compromis' | 'offre' | GenreFiche | GenrePersonne
export const estGenreFiche = (g: GenreBilan): g is GenreFiche | GenrePersonne => g !== 'compromis' && g !== 'offre'
export const estGenrePersonne = (g: GenreBilan): g is GenrePersonne => g === 'identite' || g === 'renseignements'
export type BilanCompromis = {
  genre: GenreBilan
  lectureId: string | null
  nom: string
  luLe: string | null
  affaireId: number
  dateTransaction: string | null
  conditionsLues: boolean     // false : la liste de la transaction n'a pas pu être lue -> aucune ligne de condition
  conditionsGenerales: string[] // lues mais NON comparées : conditions générales, pas suspensives (Frédéric, 17/11)
  lignes: LigneBilan[]
}
export type CatalogueCondition = { id: string; libelle: string }

const jjmmaaaa = (iso: string) => { const [a, m, j] = iso.slice(0, 10).split('-'); return `${j}/${m}/${a}` }
const eurosClair = (x: number) => `${Math.round(x * 100) / 100}`.replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' €'
const eurosTexte = (x: number) => String(Math.round(x * 100) / 100)
const montant = (v: number | null | undefined) => (v != null && Number.isFinite(v) && v > 0 ? v : null)
const sansAccent = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim()

function plusRecent(docs: DocumentLu[]): DocumentLu | null {
  const deType = docs.filter((d) => d.lecture.typeCode === 'transaction.avant_contrat' && d.lecture.etat === 'lu')
  if (!deType.length) return null
  return deType.reduce((a, b) => {
    const da = lireDateIso(dateLue(a.lecture.valeurs, 'date_signature'))
    const db = lireDateIso(dateLue(b.lecture.valeurs, 'date_signature'))
    return db && (!da || db > da) ? b : a
  })
}

export function bilanCompromis(docs: DocumentLu[], affaires: AffaireRegle[], catalogue: CatalogueCondition[] | null): BilanCompromis | null {
  const cpv = plusRecent(docs)
  if (!cpv) return null
  const v = cpv.lecture.valeurs
  // LA transaction du compromis : un compromis vivant, départagé par les acquéreurs, la date et le prix (comme P4) ;
  // deux que rien ne départage -> null -> pas de bilan (jamais la mauvaise transaction).
  const ligne = resoudreCible(affaires.filter((a) => a.kind === 'compromis' && !['refused', 'cancelled'].includes(String(a.state ?? ''))), {
    acquereurs: personnesLuesDe(cpv.lecture).filter((p) => p.qualite === 'acquereur'), date: dateLue(v, 'date_signature'), montant: nombreLu(v, 'prix'),
  })
  if (!ligne || ligne.id == null) return null
  const page = (cle: string) => v.find((x) => x.cle === cle && x.rang === 0)?.page ?? null
  const lignes: LigneBilan[] = []
  const pousser = (l: Omit<LigneBilan, 'note' | 'champModale' | 'condition' | 'regle' | 'attente' | 'fige' | 'champFiche' | 'temoin'> & Partial<Pick<LigneBilan, 'note' | 'champModale' | 'condition' | 'regle'>>) =>
    lignes.push({ note: null, champModale: null, condition: null, regle: null, attente: null, fige: null, champFiche: null, temoin: null, ...l })

  // ── les champs que Hektor connaît : ils partent par la modale « Modifier le compromis » ──
  const euros = (cle: string, libelle: string, lu: number | null, base: number | null, champ: ChampModale | null, note: string | null = null) => {
    if (lu == null || lu <= 0) return
    const etat: EtatBilan = base == null ? 'ajouter' : comparerNombre(lu, base, TOLERANCES.euros) === 'different' ? 'trancher' : 'accord'
    pousser({ cle, libelle, destination: 'hektor', etat, lu: eurosClair(lu), valeur: eurosTexte(lu), transaction: base == null ? null : eurosClair(base), page: page(cle.slice(2) === 'net_vendeur' ? 'prix_net_vendeur' : cle.slice(2)), champModale: champ, note: etat === 'accord' ? null : note, regle: etat === 'trancher' ? 'L7' : null })
  }
  euros('B.prix', 'Prix de vente', nombreLu(v, 'prix'), montant(ligne.montant), 'amount')
  const signe = dateLue(v, 'date_signature')
  if (signe) {
    const base = lireDateIso(ligne.date)
    const lu = lireDateIso(signe) as Date
    const etat: EtatBilan = !base ? 'ajouter' : Math.abs(joursEntre(lu, base)) > 1 ? 'trancher' : 'accord'
    pousser({ cle: 'B.date', libelle: 'Date de signature', destination: 'hektor', etat, lu: jjmmaaaa(signe), valeur: signe.slice(0, 10), transaction: base ? jjmmaaaa(base.toISOString()) : null, page: page('date_signature'), champModale: 'transaction_date', regle: etat === 'trancher' ? 'L7' : null })
  }
  // ⛔ Frédéric (17/11) : la date BUTOIR du compromis (la réitération) et la date PRÉVUE de l'acte dans la transaction
  //   sont la même date -- identiques, sinon c'est un conflit (dans un sens comme dans l'autre).
  const reiteration = dateLue(v, 'date_reiteration')
  if (reiteration) {
    const base = lireDateIso(ligne.dateActe)
    const butoir = lireDateIso(reiteration) as Date
    const etat: EtatBilan = !base ? 'ajouter' : Math.abs(joursEntre(butoir, base)) > 1 ? 'trancher' : 'accord'
    pousser({
      cle: 'B.date_acte', libelle: 'Date de l\'acte', destination: 'hektor', etat, lu: `le ${jjmmaaaa(reiteration)}`, valeur: reiteration.slice(0, 10),
      transaction: base ? `le ${jjmmaaaa(base.toISOString())}` : null, page: page('date_reiteration'), champModale: 'signature_date',
      note: etat === 'trancher' ? 'la date butoir du compromis et la date prévue de l\'acte doivent être la même' : null,
      regle: etat === 'trancher' ? 'L7' : null,
    })
  }
  euros('B.sequestre', 'Séquestre', nombreLu(v, 'sequestre'), montant(ligne.sequestre), 'sequestration')
  euros('B.net_vendeur', 'Net vendeur', nombreLu(v, 'prix_net_vendeur'), montant(ligne.prixNetVendeur), 'net_seller_price')
  const honorairesBase = ligne.honorairesEntree != null || ligne.honorairesSortie != null ? (ligne.honorairesEntree ?? 0) + (ligne.honorairesSortie ?? 0) : null
  euros('B.honoraires', 'Honoraires', nombreLu(v, 'honoraires'), montant(honorairesBase), null, 'à répartir entre honoraires d\'entrée et de sortie dans la transaction')

  // lot 10c (audit du 17/11) : ce qui n'est PAS chez Hektor se DIT. « jamais_envoye » : le carnet seul portait la valeur
  // (l'ancien chemin « chez nous seulement ») -- la case compte comme vide et se propose à envoyer. « en_route » : envoyée,
  // pas encore confirmée par le retour de Hektor -- on compare à la valeur envoyée, sans la renvoyer d'office.
  const CHAMP_CARNET: Record<string, string> = { 'B.prix': 'montant', 'B.date': 'date', 'B.date_acte': 'date_acte', 'B.sequestre': 'sequestre', 'B.net_vendeur': 'prix_net_vendeur' }
  for (const l of lignes) {
    const attente = ligne.enAttente?.[CHAMP_CARNET[l.cle] ?? ''] ?? null
    if (!attente) continue
    l.attente = attente
    const dit = attente === 'echec' ? 'le dernier envoi à Hektor a échoué : la valeur n\'y est pas' : attente === 'jamais_envoye' ? 'notre carnet seul la portait : elle n\'est jamais partie chez Hektor' : 'envoyée à Hektor, pas encore confirmée par son retour'
    l.note = l.note ? `${dit} ; ${l.note}` : dit
  }

  // ── les conditions suspensives : gardées CHEZ NOUS (app_affaire_condition), jamais envoyées à Hektor ──
  const conditionsLues = ligne.conditions != null
  if (ligne.conditions) {
    const parNature = new Map(ligne.conditions.map((c) => [natureDuLibelle(c.libelle), c]))
    // la clause du catalogue : le libellé EXACT d'abord (« Obtention du permis de construire »), sinon la même nature
    const duCatalogue = (nature: NatureCondition) => (catalogue ?? []).find((c) => sansAccent(c.libelle) === sansAccent(LIBELLE_CONDITION[nature]))
      ?? (nature !== 'autre' ? (catalogue ?? []).find((c) => natureDuLibelle(c.libelle) === nature) : undefined) ?? null
    for (const c of conditionsLuesDe(cpv.lecture)) {
      const suivie = parNature.get(c.nature)
      const cat = duCatalogue(c.nature)
      const libelle = suivie?.libelle ?? cat?.libelle ?? LIBELLE_CONDITION[c.nature]
      const lu = c.date ? `jusqu'au ${jjmmaaaa(c.date)}` : 'prévue, sans date'
      const cle = `B.condition.${c.nature}`
      const condition = { nature: c.nature, libelle, date: c.date, catalogueId: cat?.id ?? null, retirer: false }
      if (!suivie) {
        pousser({ cle, libelle, destination: 'nous', etat: 'ajouter', lu, valeur: c.date ?? '', transaction: null, page: page('conditions.nature'), condition, note: cat ? null : 'condition libre : elle n\'est pas au catalogue de l\'agence', regle: ligne.conditions.length ? 'L20' : null })
        continue
      }
      const dLu = lireDateIso(c.date)
      const dSuivi = lireDateIso(suivie.date)
      const etat: EtatBilan = dLu && (!dSuivi || Math.abs(joursEntre(dLu, dSuivi)) > 1) ? 'trancher' : 'accord'
      pousser({ cle, libelle, destination: 'nous', etat, lu, valeur: c.date ?? '', transaction: dSuivi ? `jusqu'au ${jjmmaaaa(dSuivi.toISOString())}` : 'sans date', page: page('conditions.nature'), condition, regle: etat === 'trancher' ? 'L20' : null })
    }
    // le compromis dit « pas de condition de prêt » (ou y renonce) alors que la transaction la suit : la retirer ?
    const pret = texteLu(v, 'condition_pret')
    const suiviePret = parNature.get('pret')
    if ((pret === 'non' || pret === 'renonciation') && suiviePret) {
      pousser({
        cle: 'B.condition.pret', libelle: suiviePret.libelle, destination: 'nous', etat: 'trancher', lu: pret === 'renonciation' ? 'renonciation au prêt' : 'pas de condition de prêt',
        valeur: 'retirer', transaction: suiviePret.date ? `suivie jusqu'au ${jjmmaaaa(suiviePret.date)}` : 'suivie', page: page('condition_pret'),
        condition: { nature: 'pret', libelle: suiviePret.libelle, date: null, catalogueId: null, retirer: true }, regle: 'L20',
      })
    }
  }
  const conditionsGenerales = conditionsGeneralesLues(cpv.lecture).map((n) => LIBELLE_CONDITION[n])
  return { genre: 'compromis', lectureId: cpv.lecture.id ?? null, nom: cpv.nom, luLe: cpv.lecture.luLe, affaireId: ligne.id, dateTransaction: ligne.date ?? null, conditionsLues, conditionsGenerales, lignes }
}

// ── GED lot 2 (17/11) : « CE QUE DIT L'OFFRE » -- l'offre lue face à SON offre au registre ──
// Le montant (seulement s'il s'entend frais d'agence inclus, ou sans base lue : comme L7), la date de la PROPOSITION
// (jamais la colonne `date`, qui porte le dernier mouvement) et la validité en jours. Tout part chez Hektor par la modale
// « Modifier l'offre », VISIBLE : le chemin de l'offre construit un corps NEUF et renvoie montant, date et validité
// préremplis, sans la liste des cases touchées ni le témoin du compromis -- on ne le fait pas partir sans être vu.
const FIGEE_ACCEPTEE = 'offre acceptée : figée chez Hektor, son montant, sa date et sa validité ne se modifient plus (seul son état change)'
const FIGEE_REFUSEE = 'offre refusée : le registre y porte la date du refus, la modifier la réécrirait -- rien ne se propose'
export function bilanOffre(docs: DocumentLu[], affaires: AffaireRegle[]): BilanCompromis | null {
  const lues = docs.filter((d) => d.lecture.typeCode === 'transaction.offre' && d.lecture.etat === 'lu')
  if (!lues.length) return null
  const doc = lues.reduce((a, b) => {
    const da = lireDateIso(dateLue(a.lecture.valeurs, 'date_offre'))
    const db = lireDateIso(dateLue(b.lecture.valeurs, 'date_offre'))
    return db && (!da || db > da) ? b : a
  })
  const v = doc.lecture.valeurs
  // départager les offres par la date de la PROPOSITION (celle du registre peut être celle du refus)
  const offres = affaires.filter((a) => a.kind === 'offre').map((a) => ({ ...a, date: a.dateProposee ?? a.date }))
  const ligne = resoudreCible(offres, {
    acquereurs: personnesLuesDe(doc.lecture).filter((p) => p.qualite === 'acquereur'), date: dateLue(v, 'date_offre'), montant: nombreLu(v, 'montant_offert'),
  })
  if (!ligne || ligne.id == null) return null
  const page = (cle: string) => v.find((x) => x.cle === cle && x.rang === 0)?.page ?? null
  const etatOffre = String(ligne.state ?? '').trim().toLowerCase()
  const fige = etatOffre === 'accepted' ? FIGEE_ACCEPTEE : etatOffre === 'refused' ? FIGEE_REFUSEE : null
  const lignes: LigneBilan[] = []
  const pousser = (l: Omit<LigneBilan, 'note' | 'condition' | 'regle' | 'attente' | 'fige' | 'destination' | 'champFiche' | 'temoin'> & Partial<Pick<LigneBilan, 'note' | 'regle'>>) =>
    lignes.push({ note: null, condition: null, regle: null, attente: null, fige: null, champFiche: null, temoin: null, destination: 'hektor', ...l })

  const montantLu = nombreLu(v, 'montant_offert')
  if (montantLu != null && montantLu > 0 && texteLu(v, 'base_prix') !== 'net_vendeur') {
    const base = montant(ligne.montant)
    const etat: EtatBilan = base == null ? 'ajouter' : comparerNombre(montantLu, base, TOLERANCES.euros) === 'different' ? 'trancher' : 'accord'
    pousser({ cle: 'O.montant', libelle: 'Montant offert', etat, lu: eurosClair(montantLu), valeur: eurosTexte(montantLu), transaction: base == null ? null : eurosClair(base), page: page('montant_offert'), champModale: 'amount', regle: etat === 'trancher' ? 'L7' : null })
  }
  const dateOffre = dateLue(v, 'date_offre')
  if (dateOffre) {
    const base = lireDateIso(ligne.date)
    const lu = lireDateIso(dateOffre) as Date
    const etat: EtatBilan = !base ? 'ajouter' : Math.abs(joursEntre(lu, base)) > 1 ? 'trancher' : 'accord'
    pousser({ cle: 'O.date', libelle: 'Date de l\'offre', etat, lu: jjmmaaaa(dateOffre), valeur: dateOffre.slice(0, 10), transaction: base ? jjmmaaaa(base.toISOString()) : null, page: page('date_offre'), champModale: 'transaction_date' })
  }
  // la validité en jours : lue telle quelle, sinon déduite de « valable jusqu'au » (de 1 à 365 jours, sinon on ne devine pas)
  const joursLus = (() => {
    const n = nombreLu(v, 'validite_jours')
    if (n != null && n >= 1 && n <= 365) return Math.round(n)
    const debut = lireDateIso(dateOffre)
    const fin = lireDateIso(dateLue(v, 'validite_jusquau'))
    const j = debut && fin ? joursEntre(debut, fin) : null
    return j != null && j >= 1 && j <= 365 ? j : null
  })()
  if (joursLus != null) {
    const base = ligne.joursValidite != null && ligne.joursValidite > 0 ? ligne.joursValidite : null
    const etat: EtatBilan = base == null ? 'ajouter' : base !== joursLus ? 'trancher' : 'accord'
    const clair = (j: number) => `${j} jour${j > 1 ? 's' : ''}`
    pousser({ cle: 'O.validite', libelle: 'Validité', etat, lu: clair(joursLus), valeur: String(joursLus), transaction: base == null ? null : clair(base), page: page(nombreLu(v, 'validite_jours') != null ? 'validite_jours' : 'validite_jusquau'), champModale: 'validity_days' })
  }
  const CHAMP_CARNET: Record<string, string> = { 'O.montant': 'montant', 'O.date': 'date', 'O.validite': 'jours_validite' }
  for (const l of lignes) {
    if (fige && l.etat !== 'accord') { l.fige = fige; continue }
    const attente = ligne.enAttente?.[CHAMP_CARNET[l.cle] ?? ''] ?? null
    if (!attente) continue
    l.attente = attente
    l.note = attente === 'echec' ? 'le dernier envoi à Hektor a échoué : la valeur n\'y est pas' : attente === 'jamais_envoye' ? 'notre carnet seul la portait : elle n\'est jamais partie chez Hektor' : 'envoyée à Hektor, pas encore confirmée par son retour'
  }
  return { genre: 'offre', lectureId: doc.lecture.id ?? null, nom: doc.nom, luLe: doc.lecture.luLe, affaireId: ligne.id, dateTransaction: ligne.date ?? null, conditionsLues: true, conditionsGenerales: [], lignes }
}

// Les bilans d'un dossier, dans l'ordre de la vie d'une vente (l'offre, puis le compromis) ; seuls ceux qui ont un document
// lu ET leur transaction sûre au registre.
export function bilansDuDossier(docs: DocumentLu[], affaires: AffaireRegle[], catalogue: CatalogueCondition[] | null): BilanCompromis[] {
  return [bilanOffre(docs, affaires), bilanCompromis(docs, affaires, catalogue)].filter((b): b is BilanCompromis => b !== null)
}

// Les conditions de la transaction APRÈS les choix « prendre » (toute la liste : le geste la remplace). On part de la
// liste COMPLÈTE relue strictement (état, levée, note, délai gardés) ; une condition ajoutée arrive « en attente ».
export type ConditionComplete = { rang?: number; libelle: string; jours?: number | null; date_echeance?: string | null; etat?: string; date_levee?: string | null; note?: string | null; catalogue_id?: string | null }
export function conditionsApres(actuelles: ConditionComplete[], prises: LigneBilan[]): ConditionComplete[] {
  let liste = actuelles.map((c) => ({ ...c }))
  for (const l of prises) {
    const c = l.condition
    if (!c) continue
    const i = liste.findIndex((x) => natureDuLibelle(x.libelle) === c.nature && c.nature !== 'autre')
    if (c.retirer) { if (i >= 0) liste = liste.filter((_, k) => k !== i); continue }
    if (i >= 0) liste[i] = { ...liste[i], date_echeance: c.date }
    else liste.push({ libelle: c.libelle, date_echeance: c.date, etat: 'attente', catalogue_id: c.catalogueId })
  }
  return liste.map((c, k) => ({ ...c, rang: k + 1 }))
}

// La note « Vrai / Faux » d'une ligne « À regarder », déduite des choix (morceau 10) : une ligne PRISE -> l'alerte avait
// raison (vrai) ; toutes GARDÉES -> elle a sonné pour rien (faux) ; sinon (rien de tranché) -> pas de note.
export function verdictDesChoix(alerteTexte: string, code: string, lignes: LigneBilan[], choix: Map<string, 'prendre' | 'garder'>): 'vrai' | 'faux' | null {
  const texte = normaliserTexte(alerteTexte)
  const liees = lignes.filter((l) => l.regle === code && (code !== 'L20' || texte.includes(normaliserTexte(l.libelle)) || texte.includes(normaliserTexte(LIBELLE_CONDITION[l.condition?.nature ?? 'autre']))))
  const tranchees = liees.filter((l) => choix.has(l.cle))
  if (!tranchees.length) return null
  if (tranchees.some((l) => choix.get(l.cle) === 'prendre')) return 'vrai'
  return tranchees.length === liees.length ? 'faux' : null
}
