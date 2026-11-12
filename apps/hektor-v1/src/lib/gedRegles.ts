// GED (12/11/2026, morceau 5) -- LES RÈGLES SANS IA : des croisements de ce que nous avons DÉJÀ (la fiche, le registre
// des transactions, les documents et leur état de signature). Fonction pure, sans lecture ni écriture : essais hors
// ligne dans test_ged_regles.cjs. Affichées dans « Reçu / Manque » sous « À regarder », derrière `ged_propositions`.
// ⭐ Cinq règles du catalogue (N1a, N3, N4 absent, N6, N7) sont déjà des pièces de « Reçu / Manque » (gedPieces.ts) :
//   elles ne sont PAS refaites ici. On SIGNALE ; on ne dit jamais « absent » (un document au nom muet n'est pas reconnu).
// Catalogue : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.10 (et E_synthese_catalogue.md §3.1).
import { momentDuDossier, typeDuDocument, type FaitsDuBien } from './gedPieces'

export type FaitsRegles = FaitsDuBien & {
  diffusable: boolean
  dpeDate: string | null
  nbLots: number | null
  charges: number | null
  prixAncien: number | null
  prixNouveau: number | null
  prixChangeLe: string | null
  mandatDebut: string | null
  mandatFin: string | null
}

// Un document, avec la date de son dépôt et l'état de signature électronique que l'écran sait déjà lire
// (etatFiableDuDocument : 'signed', 'pending', 'to_send'…, null pour un PDF sans état -- papier ou scan). `modele` : un
// document généré par le modèle de Hektor (source 'hektor_console_modele') n'est PAS un mandat papier signé.
export type DocumentRegle = { nom: string; typeCode: string | null; date: string | null; signature: string | null; modele?: boolean }
export type AffaireRegle = { kind: string; state: string | null; date: string | null; dateActe: string | null }

export type NiveauAlerte = 'alerte' | 'piece' | 'info'
export type Alerte = { code: string; niveau: NiveauAlerte; texte: string; pourquoi: string; typeADeposer?: string }

// Le nom de la pièce à déposer, pour le bandeau « Prochain fichier : … » de la fenêtre de dépôt.
export const LIBELLE_A_DEPOSER: Record<string, string> = {
  'mandat.vente': 'Mandat de vente signé',
  'mandat.avenant': 'Avenant au mandat',
  'diag.erp': 'État des risques',
  'diag.dpe': 'DPE',
  'copro.carnet': 'Fiche synthétique de la copropriété',
  'copro.appel_fonds': 'Appel de fonds de la copropriété',
  'transaction.acte': 'Acte de vente',
}

const JOUR = 86_400_000
const NON_BATIS = new Set(['5', '43', '15', '16'])

// Une date de la base ou de la fiche : « AAAA-MM-JJ… » ou « JJ/MM/AAAA ». Les dates vides de Hektor (0000-00-00) et la
// date zéro (1970-01-01, 90 fiches le 12/11) ne sont PAS des dates.
export function lireDate(v: string | null | undefined): Date | null {
  const s = String(v ?? '').trim()
  let m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s)
  let d: Date | null = null
  if (m) d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])))
  else if ((m = /^(\d{2})\/(\d{2})\/(\d{4})/.exec(s))) d = new Date(Date.UTC(Number(m[3]), Number(m[2]) - 1, Number(m[1])))
  if (!d || Number.isNaN(d.getTime()) || d.getUTCFullYear() < 1980) return null
  return d
}

const jjmmaaaa = (d: Date) => `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`

// La fin de validité d'un DPE (décret 2020-1610) : avant 2013 et 2013-2017 -> 31/12/2022 ; du 01/01/2018 au 30/06/2021
// -> 31/12/2024 ; depuis le 01/07/2021 -> 10 ans.
export function finValiditeDpe(date: Date): Date {
  if (date < new Date(Date.UTC(2018, 0, 1))) return new Date(Date.UTC(2022, 11, 31))
  if (date < new Date(Date.UTC(2021, 6, 1))) return new Date(Date.UTC(2024, 11, 31))
  return new Date(Date.UTC(date.getUTCFullYear() + 10, date.getUTCMonth(), date.getUTCDate()))
}

export function reglesSansIa(faits: FaitsRegles, documents: DocumentRegle[], affaires: AffaireRegle[], aujourdhui: Date): Alerte[] {
  const alertes: Alerte[] = []
  const moment = momentDuDossier(faits)
  const avecType = documents.map((d) => ({ ...d, type: typeDuDocument(d) }))
  const deType = (...codes: string[]) => avecType.filter((d) => d.type && codes.includes(d.type))
  const bati = faits.typeBien ? !NON_BATIS.has(faits.typeBien) : null
  const vivante = (a: AffaireRegle) => !['refused', 'cancelled'].includes(String(a.state ?? ''))

  // N1 -- le mandat signé. Un PDF de mandat SANS état électronique peut être un mandat papier signé : il fait taire la règle.
  const mandats = deType('mandat.vente')
  const signe = mandats.some((d) => d.signature === 'signed')
  const papier = mandats.some((d) => d.signature == null && !d.modele)
  const enAttente = mandats.some((d) => d.signature === 'pending' || d.signature === 'to_send')
  if (faits.diffusable && !signe && !papier && enAttente) {
    alertes.push({ code: 'N1b', niveau: 'alerte', texte: 'Bien diffusé, signature du mandat encore en attente', pourquoi: 'aucun mandat signé ni PDF papier trouvé au dossier' })
  }
  if ((moment === 'offre' || moment === 'compromis') && !signe && !papier) {
    alertes.push({ code: 'N1c', niveau: 'alerte', texte: `${moment === 'offre' ? 'Sous offre' : 'Sous compromis'} sans mandat signé trouvé au dossier`, pourquoi: 'loi Hoguet : pas de transaction sans mandat écrit', typeADeposer: 'mandat.vente' })
  }

  // N2 -- une baisse de prix d'au moins 3 % après le début du mandat, sans avenant déposé depuis.
  const debut = lireDate(faits.mandatDebut)
  const change = lireDate(faits.prixChangeLe)
  if (debut && change && change > debut && faits.prixAncien && faits.prixNouveau && faits.prixNouveau < faits.prixAncien * 0.97) {
    const avenant = deType('mandat.avenant').some((d) => { const x = lireDate(d.date); return !x || x >= debut })
    if (!avenant) {
      const baisse = Math.round((1 - faits.prixNouveau / faits.prixAncien) * 100)
      alertes.push({ code: 'N2', niveau: 'piece', texte: `Baisse de prix de ${baisse} % le ${jjmmaaaa(change)}, avenant non trouvé`, pourquoi: 'un prix baissé se signe par avenant au mandat', typeADeposer: 'mandat.avenant' })
    }
  }

  // N4 -- l'état des risques DÉPOSÉ il y a plus de 6 mois (date du dépôt, pas de l'état). Au compromis : une simple
  // information tant que la question n° 5 de l'étude n'est pas tranchée (le notaire le refait-il ?).
  if (moment === 'offre' || moment === 'compromis') {
    const erp = deType('diag.erp', 'diag.dossier').map((d) => lireDate(d.date)).filter((x): x is Date => Boolean(x))
    if (erp.length) {
      const dernier = new Date(Math.max(...erp.map((x) => x.getTime())))
      if (aujourdhui.getTime() - dernier.getTime() > 183 * JOUR) {
        alertes.push({ code: 'N4', niveau: moment === 'offre' ? 'alerte' : 'info', texte: `État des risques déposé le ${jjmmaaaa(dernier)} : plus de 6 mois`, pourquoi: 'il doit avoir moins de 6 mois à la signature (date du dépôt, pas de l\'état)', typeADeposer: 'diag.erp' })
      }
    }
  }

  // N5 -- le DPE de la fiche : échu, ou un bien bâti diffusé sans DPE (mention obligatoire de l'annonce).
  const dpe = lireDate(faits.dpeDate)
  if (dpe && finValiditeDpe(dpe) < aujourdhui) {
    alertes.push({ code: 'N5', niveau: 'alerte', texte: `DPE de la fiche (${jjmmaaaa(dpe)}) plus valable depuis le ${jjmmaaaa(finValiditeDpe(dpe))}`, pourquoi: 'un DPE périmé ne vaut plus pour la vente', typeADeposer: 'diag.dpe' })
  }
  if (faits.diffusable && bati === true && !faits.dpeNonConcerne && faits.dpeConso == null && faits.dpeGes == null) {
    alertes.push({ code: 'N5', niveau: 'alerte', texte: 'Bien diffusé sans DPE sur la fiche', pourquoi: 'la classe énergie est une mention obligatoire de l\'annonce' })
  }

  // N8 -- la case copropriété à NON alors que le dossier a des pièces de copropriété (le secteur la remet parfois à zéro).
  const pieceCopro = avecType.filter((d) => d.type?.startsWith('copro.'))
  if (faits.copropriete === false && pieceCopro.length) {
    alertes.push({ code: 'N8', niveau: 'alerte', texte: `Case copropriété à NON, mais ${pieceCopro.length} pièce${pieceCopro.length > 1 ? 's' : ''} de copropriété au dossier`, pourquoi: 'regarde la fiche : une sauvegarde du secteur chez Hektor remet parfois la case à NON' })
  }

  // N9 -- les mentions obligatoires d'un lot en copropriété (nombre de lots, charges) vides sur la fiche.
  if (faits.copropriete === true) {
    if (faits.nbLots == null) alertes.push({ code: 'N9', niveau: 'piece', texte: 'Nombre de lots de la copropriété non renseigné', pourquoi: 'mention obligatoire de l\'annonce : la fiche synthétique le donne', typeADeposer: 'copro.carnet' })
    if (faits.charges == null) alertes.push({ code: 'N9', niveau: 'piece', texte: 'Charges de copropriété (quote-part annuelle) non renseignées', pourquoi: 'mention obligatoire de l\'annonce : l\'appel de fonds la donne', typeADeposer: 'copro.appel_fonds' })
  }

  // N10 -- un document de transaction sans la transaction au registre.
  if (deType('transaction.offre').length && !affaires.some((a) => a.kind === 'offre')) {
    alertes.push({ code: 'N10', niveau: 'info', texte: 'Une offre est au dossier, aucune offre au registre', pourquoi: 'offre non saisie ?' })
  }
  if (deType('transaction.avant_contrat', 'transaction.acte').length && !affaires.some((a) => a.kind === 'compromis' || a.kind === 'vente')) {
    alertes.push({ code: 'N10', niveau: 'info', texte: 'Un compromis ou un acte est au dossier, aucun au registre', pourquoi: 'souvent la vente précédente : c\'est alors un titre de propriété' })
  }

  // N11 -- une offre ou un compromis daté après la fin du mandat (la tacite reconduction n'est pas lisible ici).
  const fin = lireDate(faits.mandatFin)
  if (fin) {
    // une ligne par sorte (la plus récente), pas une par offre
    for (const kind of ['offre', 'compromis']) {
      const apres = affaires.filter((a) => a.kind === kind && vivante(a)).map((a) => lireDate(a.date)).filter((x): x is Date => x !== null && x > fin)
      if (apres.length) {
        const quand = new Date(Math.max(...apres.map((x) => x.getTime())))
        alertes.push({ code: 'N11', niveau: 'alerte', texte: `${kind === 'offre' ? 'Offre' : 'Compromis'} du ${jjmmaaaa(quand)}, après la fin du mandat (${jjmmaaaa(fin)})`, pourquoi: 'hors mandat, pas d\'honoraires (loi Hoguet) ; à vérifier : reconduction ?' })
      }
    }
  }

  // N12 -- la date d'acte prévue est passée et l'acte n'est pas au dossier.
  if (moment === 'compromis') {
    const actes = affaires.filter((a) => a.kind === 'compromis' && vivante(a)).map((a) => lireDate(a.dateActe)).filter((x): x is Date => Boolean(x))
    const prevue = actes.length ? new Date(Math.max(...actes.map((x) => x.getTime()))) : null
    if (prevue && prevue < aujourdhui && !deType('transaction.acte').length) {
      alertes.push({ code: 'N12', niveau: 'piece', texte: `Acte prévu le ${jjmmaaaa(prevue)}, acte non trouvé au dossier`, pourquoi: 'la vente est-elle signée ?', typeADeposer: 'transaction.acte' })
    }
  }

  const ordre: Record<NiveauAlerte, number> = { alerte: 0, piece: 1, info: 2 }
  return alertes.sort((a, b) => ordre[a.niveau] - ordre[b.niveau])
}
