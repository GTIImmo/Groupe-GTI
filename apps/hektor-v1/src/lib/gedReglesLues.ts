// GED (13/11/2026, morceau 7, sous-lot 7a) -- LES RÈGLES AVEC LECTURE : ce que l'IA a lu dans les justificatifs et les
// diagnostics du bien, comparé à la fiche et aux mandants (lib/gedComparer.ts). Fonction pure : essais hors ligne dans
// test_ged_regles_lues.cjs. Affichées avec les règles sans IA sous « À regarder », derrière `ged_propositions`.
// On SIGNALE, on n'écrit rien (les « remplir » sont le morceau 8). Seule une vraie différence sonne.
// Catalogue : E_synthese_catalogue.md §3.2 (L2, L6, L11, L13, L15, L16, L17) et note du chantier §12.14, §12.17.
import {
  annualiser, comparerCommune, comparerNombre, dateLue, finDeValidite, lireDateIso, lireNombre, nombreLu,
  personnesLuesDe, personneSurLaFiche, texteLu, TOLERANCES, type PersonneDuBien,
} from './gedComparer'
import type { LectureDocument } from './gedLecture'
import { classeDpe, momentDuDossier } from './gedPieces'
import type { AffaireRegle, Alerte, FaitsRegles } from './gedRegles'

// Un document lu par l'IA : son nom (pour le dire à l'écran) et sa lecture.
export type DocumentLu = { nom: string; lecture: LectureDocument }

const jjmmaaaa = (d: Date) => `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
const euros = (x: number) => `${Math.round(x).toLocaleString('fr-FR').replace(/ | /g, ' ')} €`
const nomDe = (p: { nom: string; prenoms: string }) => [p.prenoms, p.nom].filter(Boolean).join(' ')

const LIBELLE_DIAG: Record<string, string> = {
  'diag.electricite': 'Diagnostic électricité', 'diag.gaz': 'Diagnostic gaz', 'diag.assainissement': 'Contrôle de l\'assainissement',
  'diag.termites': 'État termites', 'diag.plomb': 'Constat plomb',
}
const QUALITE_TITRE = new Set(['proprietaire', 'usufruitier', 'nu_proprietaire', 'indivisaire', 'heritier', 'donataire'])
const QUALITE_TAXE = new Set(['redevable', 'proprietaire', 'usufruitier', 'nu_proprietaire'])
const LIBELLE_QUALITE: Record<string, string> = {
  proprietaire: 'propriétaire', usufruitier: 'usufruitier', nu_proprietaire: 'nu-propriétaire', indivisaire: 'indivisaire',
  heritier: 'héritier', donataire: 'donataire', redevable: 'redevable',
}

// Le plus récent document lu d'un type, d'après une date LUE (à défaut, le premier venu).
function plusRecent(docs: DocumentLu[], types: string[], cleDate: string): DocumentLu | null {
  const deType = docs.filter((d) => types.includes(d.lecture.typeCode) && d.lecture.etat === 'lu')
  if (!deType.length) return null
  return deType.reduce((a, b) => {
    const da = lireDateIso(dateLue(a.lecture.valeurs, cleDate))
    const db = lireDateIso(dateLue(b.lecture.valeurs, cleDate))
    return db && (!da || db > da) ? b : a
  })
}

export function reglesLues(faits: FaitsRegles, docs: DocumentLu[], personnesDuBien: PersonneDuBien[], affaires: AffaireRegle[], aujourdhui: Date): Alerte[] {
  const alertes: Alerte[] = []
  const lus = docs.filter((d) => d.lecture.etat === 'lu')
  const moment = momentDuDossier(faits)
  const vivante = (a: AffaireRegle) => !['refused', 'cancelled'].includes(String(a.state ?? ''))

  // L13 -- un document d'un AUTRE bien ? La commune lue (celle du bien, dans chaque fiche de lecture) ≠ celle de la fiche.
  for (const d of lus) {
    const commune = texteLu(d.lecture.valeurs, 'commune')
    if (comparerCommune(commune, faits.ville ?? null) === 'different') {
      alertes.push({ code: 'L13', niveau: 'alerte', texte: `${d.nom} : commune lue « ${commune} », le bien est à ${faits.ville}`, pourquoi: 'document d\'un autre bien ? (ou commune nouvelle, à vérifier)' })
    }
  }

  // L11 (7a) -- les propriétaires du TITRE et les redevables de la TAXE doivent être parmi les mandants. Seul un
  // inconnu sonne (une personne lue qu'on ne retrouve nulle part sur la fiche) ; la fiche vide se tait.
  const inconnus = new Map<string, string>()
  for (const [type, qualites, ou] of [['justif.titre', QUALITE_TITRE, 'au titre'], ['justif.taxe', QUALITE_TAXE, 'sur l\'avis de taxe']] as const) {
    for (const d of lus.filter((x) => x.lecture.typeCode === type)) {
      for (const p of personnesLuesDe(d.lecture)) {
        if (p.qualite && !qualites.has(p.qualite)) continue
        if (personneSurLaFiche(p, personnesDuBien) !== 'different') continue
        const cle = `${p.nom}|${p.prenoms}`.toUpperCase()
        if (!inconnus.has(cle)) inconnus.set(cle, `${nomDe(p)} (${LIBELLE_QUALITE[p.qualite ?? ''] ?? 'personne'} ${ou})`)
      }
    }
  }
  for (const qui of inconnus.values()) {
    alertes.push({ code: 'L11', niveau: 'alerte', texte: `${qui} n'est pas parmi les mandants du bien`, pourquoi: 'chaque propriétaire doit signer le mandat (ou donner pouvoir)', typeADeposer: 'mandat.vente' })
  }

  // Taxe foncière -- le montant de l'avis le plus récent face à la case de la fiche ; un avis ancien.
  const taxe = lus.filter((x) => x.lecture.typeCode === 'justif.taxe')
    .reduce<DocumentLu | null>((a, b) => ((nombreLu(b.lecture.valeurs, 'annee_imposition') ?? 0) > (a ? nombreLu(a.lecture.valeurs, 'annee_imposition') ?? 0 : -1) ? b : a), null)
  if (taxe) {
    const annee = nombreLu(taxe.lecture.valeurs, 'annee_imposition')
    const montant = nombreLu(taxe.lecture.valeurs, 'montant_total')
    const plusieurs = texteLu(taxe.lecture.valeurs, 'plusieurs_biens') === 'oui'
    const fiche = lireNombre(faits.taxeFonciere)
    const avis = annee ? `avis ${annee}` : 'l\'avis'
    if (montant != null && !plusieurs) {
      if (fiche == null) {
        alertes.push({ code: 'T1', niveau: 'info', texte: `Taxe foncière non renseignée sur la fiche (${avis} : ${euros(montant)})`, pourquoi: 'information de l\'annonce' })
      } else if (comparerNombre(montant, fiche, TOLERANCES.taxe) === 'different') {
        alertes.push({ code: 'T1', niveau: 'alerte', texte: `Taxe foncière : fiche ${euros(fiche)}, ${avis} ${euros(montant)}`, pourquoi: 'la fiche annonce un autre montant que l\'avis' })
      }
    }
    if (annee != null && annee < aujourdhui.getUTCFullYear() - 1) {
      alertes.push({ code: 'T2', niveau: 'info', texte: `Le dernier avis de taxe foncière lu est de ${annee}`, pourquoi: 'demander l\'avis de l\'année dernière', typeADeposer: 'justif.taxe' })
    }
  }

  // L2 -- la validité des diagnostics à la date de référence : la signature du compromis (le plus récent vivant), sinon
  // aujourd'hui. Une ALERTE à l'offre et au compromis ; avant, une information (« à refaire avant le compromis »).
  const signatures = affaires.filter((a) => a.kind === 'compromis' && vivante(a)).map((a) => lireDateIso(a.date)).filter((x): x is Date => Boolean(x))
  const reference = moment === 'compromis' && signatures.length ? new Date(Math.max(...signatures.map((x) => x.getTime()))) : aujourdhui
  const quand = reference === aujourdhui ? 'aujourd\'hui' : `au compromis du ${jjmmaaaa(reference)}`
  for (const type of Object.keys(LIBELLE_DIAG)) {
    const d = plusRecent(lus, [type], type === 'diag.assainissement' ? 'date_controle' : 'date_etablissement')
    if (!d) continue
    const date = lireDateIso(dateLue(d.lecture.valeurs, type === 'diag.assainissement' ? 'date_controle' : 'date_etablissement'))
    if (!date) continue
    if (type === 'diag.assainissement' && texteLu(d.lecture.valeurs, 'type') !== 'non_collectif') continue
    const fin = finDeValidite(type, date, texteLu(d.lecture.valeurs, 'resultat'))
    if (fin && fin < reference) {
      const enVente = moment === 'offre' || moment === 'compromis'
      alertes.push({ code: 'L2', niveau: enVente ? 'alerte' : 'info', texte: `${LIBELLE_DIAG[type]} du ${jjmmaaaa(date)} : plus valable ${quand} (fin le ${jjmmaaaa(fin)})`, pourquoi: enVente ? 'un diagnostic périmé à la signature ne vaut plus' : 'à refaire avant le compromis', typeADeposer: type })
    }
  }

  // L6 -- le DPE lu (le plus récent) face à la fiche : consommation, émissions (± 1), classe recalculée.
  const dpe = plusRecent(lus, ['diag.dpe'], 'date_etablissement')
  if (dpe) {
    const v = dpe.lecture.valeurs
    const ecarts: string[] = []
    if (comparerNombre(nombreLu(v, 'conso_ep'), faits.dpeConso, TOLERANCES.dpe) === 'different') ecarts.push(`consommation ${nombreLu(v, 'conso_ep')} lue, ${faits.dpeConso} sur la fiche`)
    if (comparerNombre(nombreLu(v, 'emissions'), faits.dpeGes, TOLERANCES.dpe) === 'different') ecarts.push(`émissions ${nombreLu(v, 'emissions')} lues, ${faits.dpeGes} sur la fiche`)
    const classeFiche = classeDpe(faits.dpeConso, faits.dpeGes)
    const classeLue = texteLu(v, 'classe_energie')
    if (!ecarts.length && texteLu(v, 'modele') === '2021' && classeFiche && classeLue && classeFiche !== classeLue) ecarts.push(`classe ${classeLue} lue, ${classeFiche} d'après la fiche`)
    if (ecarts.length) {
      const date = lireDateIso(dateLue(v, 'date_etablissement'))
      alertes.push({ code: 'L6', niveau: 'alerte', texte: `DPE${date ? ` du ${jjmmaaaa(date)}` : ''} : ${ecarts.join(' ; ')}`, pourquoi: 'la fiche (et l\'annonce) ne porte pas le DPE déposé' })
    }
  }

  // L15 -- la Carrez lue plus PETITE de plus de 5 % que celle de la fiche (sens unique : l'acquéreur peut agir).
  const surface = plusRecent(lus, ['diag.surface'], 'date_mesurage')
  const carrezLue = surface ? nombreLu(surface.lecture.valeurs, 'surface_carrez') : null
  const carrezFiche = lireNombre(faits.carrez)
  if (carrezLue != null && carrezFiche != null && carrezLue < carrezFiche * (1 - TOLERANCES.carrezSensUnique)) {
    alertes.push({ code: 'L15', niveau: 'alerte', texte: `Surface Carrez : ${String(carrezFiche).replace('.', ',')} m² sur la fiche, ${String(carrezLue).replace('.', ',')} m² mesurés`, pourquoi: 'plus de 5 % en moins : l\'acquéreur peut demander une baisse du prix (loi Carrez)', typeADeposer: 'diag.surface' })
  }

  // L16 -- la copropriété : le nombre de lots (fiche synthétique) et les charges annuelles du lot (appel de fonds, arrêté).
  const carnet = lus.find((x) => x.lecture.typeCode === 'copro.carnet' && texteLu(x.lecture.valeurs, 'sous_type') === 'fiche_synthetique')
  if (carnet && faits.nbLots != null) {
    const total = nombreLu(carnet.lecture.valeurs, 'nb_lots_total')
    const principaux = nombreLu(carnet.lecture.valeurs, 'nb_lots_principaux')
    if (total != null && total !== faits.nbLots && principaux !== faits.nbLots) {
      alertes.push({ code: 'L16', niveau: 'alerte', texte: `Copropriété : ${faits.nbLots} lots sur la fiche, ${total} sur la fiche synthétique${principaux ? ` (dont ${principaux} principaux)` : ''}`, pourquoi: 'mention obligatoire de l\'annonce' })
    }
  }
  const appel = plusRecent(lus, ['copro.appel_fonds', 'copro.arrete_charges'], 'date_document')
  if (appel && faits.charges != null) {
    const v = appel.lecture.valeurs
    const annuel = nombreLu(v, 'budget_annuel_lot') ?? nombreLu(v, 'charges_courantes_lot') ?? annualiser(nombreLu(v, 'provision_budget'), texteLu(v, 'periode'))
    if (comparerNombre(annuel, faits.charges, TOLERANCES.chargesAnnuelles) === 'different' && annuel != null) {
      alertes.push({ code: 'L16', niveau: 'alerte', texte: `Charges de copropriété : ${euros(faits.charges)} par an sur la fiche, ${euros(annuel)} d'après ${appel.nom}`, pourquoi: 'mention obligatoire de l\'annonce (quote-part annuelle)' })
    }
  }

  // L17 -- une procédure de la copropriété lue (fiche synthétique ou PV d'AG) : mention obligatoire de l'annonce.
  for (const d of lus.filter((x) => x.lecture.typeCode === 'copro.carnet' || x.lecture.typeCode === 'copro.pv_ag')) {
    const procedure = texteLu(d.lecture.valeurs, 'procedure')
    const sauvegarde = texteLu(d.lecture.valeurs, 'plan_sauvegarde') === 'oui'
    if ((procedure && procedure !== 'aucune') || sauvegarde) {
      const quoi = sauvegarde && (!procedure || procedure === 'aucune') ? 'plan de sauvegarde' : (procedure as string).replace(/_/g, ' ')
      const fiche = String(faits.statutSyndicat ?? '').toUpperCase()
      const contredit = ['NOTPROCESS', 'PAS_DE_PROCEDURE'].includes(fiche)
      alertes.push({ code: 'L17', niveau: 'alerte', texte: `Copropriété : ${quoi} (lu dans ${d.nom})${contredit ? ' — la fiche dit « pas de procédure »' : ''}`, pourquoi: 'une copropriété en difficulté se mentionne dans l\'annonce' })
      break
    }
  }

  return alertes
}
