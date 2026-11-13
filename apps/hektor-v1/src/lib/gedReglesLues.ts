// GED (13/11/2026, morceau 7, sous-lot 7a) -- LES RÈGLES AVEC LECTURE : ce que l'IA a lu dans les justificatifs et les
// diagnostics du bien, comparé à la fiche et aux mandants (lib/gedComparer.ts). Fonction pure : essais hors ligne dans
// test_ged_regles_lues.cjs. Affichées avec les règles sans IA sous « À regarder », derrière `ged_propositions`.
// On SIGNALE, on n'écrit rien (les « remplir » sont le morceau 8). Seule une vraie différence sonne.
// Catalogue : E_synthese_catalogue.md §3.2 (L2, L6, L11, L13, L15, L16, L17) et note du chantier §12.14, §12.17.
// Sous-lot 7b (13/11) : le mandat -- L1 charge, L4 prix de signature, L10 signatures papier, L12 termes, L14 avenant,
// L18 fin de mandat, et L11 étendu aux mandants lus et aux vendeurs du compromis.
import {
  annualiser, comparerCommune, comparerListe, comparerNombre, comparerNumero, dateLue, finDeValidite, lireDateIso, lireNombre, nombreLu,
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
const QUALITE_MANDANT = new Set(['mandant', 'proprietaire'])
const QUALITE_VENDEUR = new Set(['vendeur'])
const LIBELLE_QUALITE: Record<string, string> = {
  proprietaire: 'propriétaire', usufruitier: 'usufruitier', nu_proprietaire: 'nu-propriétaire', indivisaire: 'indivisaire',
  heritier: 'héritier', donataire: 'donataire', redevable: 'redevable', mandant: 'mandant', vendeur: 'vendeur',
}
const CHARGE: Record<string, string> = { vendeur: 'du vendeur', acquereur: 'de l\'acquéreur', les_deux: 'des deux' }

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
  // 7b : les MANDANTS lus au mandat et à l'avenant, les VENDEURS lus au compromis, même contrôle (la fiche incomplète,
  // ou un document d'une autre affaire).
  const inconnus = new Map<string, { qui: string; pourquoi: string }>()
  const sources = [
    ['justif.titre', QUALITE_TITRE, 'au titre', 'chaque propriétaire doit signer le mandat (ou donner pouvoir)'],
    ['justif.taxe', QUALITE_TAXE, 'sur l\'avis de taxe', 'chaque propriétaire doit signer le mandat (ou donner pouvoir)'],
    ['mandat.vente', QUALITE_MANDANT, 'au mandat', 'il a signé le mandat : la fiche ne le porte pas'],
    ['mandat.avenant', QUALITE_MANDANT, 'à l\'avenant', 'il a signé l\'avenant : la fiche ne le porte pas'],
    ['transaction.avant_contrat', QUALITE_VENDEUR, 'au compromis', 'un vendeur doit être mandant (ou représenté)'],
  ] as const
  for (const [type, qualites, ou, pourquoi] of sources) {
    for (const d of lus.filter((x) => x.lecture.typeCode === type)) {
      for (const p of personnesLuesDe(d.lecture)) {
        // qualité non lue : on la compte, sauf au compromis (ce pourrait être un acquéreur)
        if (p.qualite ? !(qualites as ReadonlySet<string>).has(p.qualite) : type === 'transaction.avant_contrat') continue
        if (personneSurLaFiche(p, personnesDuBien) !== 'different') continue
        const cle = `${p.nom}|${p.prenoms}`.toUpperCase()
        if (!inconnus.has(cle)) inconnus.set(cle, { qui: `${nomDe(p)} (${LIBELLE_QUALITE[p.qualite ?? ''] ?? 'personne'} ${ou})`, pourquoi })
      }
    }
  }
  for (const { qui, pourquoi } of inconnus.values()) {
    alertes.push({ code: 'L11', niveau: 'alerte', texte: `${qui} n'est pas parmi les mandants du bien`, pourquoi, typeADeposer: 'mandat.vente' })
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

  // ── 7b : le mandat ──────────────────────────────────────────────────────────
  // Le mandat lu (déposé à la main) et l'avenant le plus récent. ⛔ On ne modifie ni ne prolonge jamais un mandat : on
  // compare seulement. Un mandat lu sous un AUTRE numéro (l'ancien mandat du bien) ne se compare pas plus loin.
  const mandat = plusRecent(lus, ['mandat.vente'], 'date_signature')
  const avenant = plusRecent(lus, ['mandat.avenant'], 'date_avenant')
  const memeNumero = (d: DocumentLu | null) => !!d && comparerNumero(texteLu(d.lecture.valeurs, 'numero_mandat'), faits.numeroMandat) !== 'different'

  // L12 -- les termes du mandat lu face à la fiche : numéro, type (hors « ACCORD »), date de signature = début du mandat.
  if (mandat) {
    const v = mandat.lecture.valeurs
    const numero = texteLu(v, 'numero_mandat')
    if (!memeNumero(mandat)) {
      alertes.push({ code: 'L12', niveau: 'alerte', texte: `${mandat.nom} : mandat n° ${numero}, la fiche porte le n° ${faits.numeroMandat}`, pourquoi: 'l\'ancien mandat du bien, ou une erreur de numéro ?' })
    } else {
      const ecarts: string[] = []
      const type = String(faits.mandatType ?? '').toUpperCase()
      if (type !== 'ACCORD' && comparerListe(texteLu(v, 'nature'), faits.mandatType) === 'different') ecarts.push(`${texteLu(v, 'nature')?.replace('_', '-')} lu, ${String(faits.mandatType).toLowerCase()} sur la fiche`)
      const signe = lireDateIso(dateLue(v, 'date_signature'))
      const debut = lireDateIso(faits.mandatDebut)
      if (signe && debut && Math.abs(signe.getTime() - debut.getTime()) > 86_400_000) ecarts.push(`signé le ${jjmmaaaa(signe)}, début du mandat le ${jjmmaaaa(debut)} sur la fiche`)
      if (ecarts.length) alertes.push({ code: 'L12', niveau: 'alerte', texte: `Mandat n° ${numero ?? faits.numeroMandat} : ${ecarts.join(' ; ')}`, pourquoi: 'la fiche ne dit pas ce que dit le mandat signé' })
    }
  }

  // L14 -- l'avenant le plus récent : son numéro, et le prix qu'il fixe face au prix affiché (sauf si le prix a encore
  // bougé APRÈS l'avenant : c'est alors la règle N2, « baisse sans avenant »).
  if (avenant) {
    const v = avenant.lecture.valeurs
    const date = lireDateIso(dateLue(v, 'date_avenant'))
    if (!memeNumero(avenant)) {
      alertes.push({ code: 'L14', niveau: 'alerte', texte: `${avenant.nom} : avenant au mandat n° ${texteLu(v, 'numero_mandat')}, la fiche porte le n° ${faits.numeroMandat}`, pourquoi: 'un avenant d\'un autre mandat ?' })
    } else {
      const nouveau = nombreLu(v, 'nouveau_prix')
      const bougeApres = date && lireDateIso(faits.prixChangeLe) ? (lireDateIso(faits.prixChangeLe) as Date) > date : false
      if (!bougeApres && comparerNombre(nouveau, faits.prix ?? null, TOLERANCES.euros) === 'different') {
        alertes.push({ code: 'L14', niveau: 'alerte', texte: `L'avenant${date ? ` du ${jjmmaaaa(date)}` : ''} fixe le prix à ${euros(nouveau as number)}, la fiche affiche ${euros(faits.prix as number)}`, pourquoi: 'le prix affiché doit être celui du dernier avenant signé' })
      }
    }
  }

  // L4 -- le prix de signature du mandat ≠ le prix affiché, sans avenant lu qui l'explique : une information.
  if (mandat && memeNumero(mandat)) {
    const prixMandat = nombreLu(mandat.lecture.valeurs, 'prix')
    const explique = lus.some((d) => d.lecture.typeCode === 'mandat.avenant' && comparerNombre(nombreLu(d.lecture.valeurs, 'nouveau_prix'), faits.prix ?? null, TOLERANCES.euros) !== 'different')
    if (!explique && comparerNombre(prixMandat, faits.prix ?? null, TOLERANCES.euros) === 'different') {
      alertes.push({ code: 'L4', niveau: 'info', texte: `Prix au mandat ${euros(prixMandat as number)}, prix affiché ${euros(faits.prix as number)}`, pourquoi: 'un avenant est-il au dossier ?', typeADeposer: 'mandat.avenant' })
    }
  }

  // L1 -- qui paie les honoraires : lu (l'avenant s'il le dit, sinon le mandat) face au REGISTRE des mandats.
  // Registre pas encore lu (undefined) : silence. Registre vide : information (le report est le morceau 8).
  const chargeDoc = [avenant, mandat].find((d) => d && memeNumero(d) && texteLu(d.lecture.valeurs, 'charge_honoraires'))
  const chargeLue = chargeDoc ? texteLu(chargeDoc.lecture.valeurs, 'charge_honoraires') : null
  if (chargeLue && faits.chargeRegistre !== undefined) {
    if (chargeLue === 'les_deux') {
      alertes.push({ code: 'L1', niveau: 'info', texte: 'Honoraires partagés entre vendeur et acquéreur (lu au mandat)', pourquoi: 'le registre ne connaît qu\'un seul payeur : à vérifier' })
    } else if (!faits.chargeRegistre) {
      alertes.push({ code: 'L1', niveau: 'info', texte: `Honoraires à la charge ${CHARGE[chargeLue] ?? chargeLue} (lu), non renseigné au registre des mandats`, pourquoi: 'information du registre' })
    } else if (comparerListe(chargeLue, faits.chargeRegistre) === 'different') {
      alertes.push({ code: 'L1', niveau: 'alerte', texte: `Honoraires : à la charge ${CHARGE[chargeLue] ?? chargeLue} au ${chargeDoc === avenant ? 'dernier avenant' : 'mandat'}, ${CHARGE[faits.chargeRegistre] ?? faits.chargeRegistre} au registre`, pourquoi: 'le prix affiché et les honoraires en dépendent' })
    }
  }

  // L10 -- les signatures d'un mandat ou d'un avenant PAPIER : moins de signatures que de mandants LUS dans le même
  // document (jamais la fiche, qui peut porter des acquéreurs rangés « mandant »), ou pas de signature de l'agence.
  for (const d of [mandat, avenant]) {
    if (!d || !memeNumero(d)) continue
    const v = d.lecture.valeurs
    const signatures = nombreLu(v, 'signatures_mandants_nb')
    const mandants = personnesLuesDe(d.lecture).length
    const quoi = d === mandat ? 'Mandat' : 'Avenant'
    if (signatures != null && mandants > signatures) {
      alertes.push({ code: 'L10', niveau: 'alerte', texte: `${quoi} : ${mandants} mandants, ${signatures} signature${signatures > 1 ? 's' : ''} lue${signatures > 1 ? 's' : ''}`, pourquoi: 'chaque mandant signe (ou un pouvoir est au dossier)', typeADeposer: 'justif.pouvoir' })
    }
    if (texteLu(v, 'signature_agence') === 'non') {
      alertes.push({ code: 'L10', niveau: 'alerte', texte: `${quoi} : l'agence n'a pas signé`, pourquoi: 'un mandat n\'engage l\'agence que signé par elle' })
    }
  }

  // L18 -- une fin du mandat EN COURS (même numéro) alors que le bien est encore diffusé.
  const fin = lus.find((d) => d.lecture.typeCode === 'mandat.fin' && comparerNumero(texteLu(d.lecture.valeurs, 'numero_mandat'), faits.numeroMandat) === 'egal')
  if (fin && faits.diffusable) {
    const effet = lireDateIso(dateLue(fin.lecture.valeurs, 'date_effet'))
    if (!effet || effet <= aujourdhui) {
      alertes.push({ code: 'L18', niveau: 'alerte', texte: `Fin du mandat n° ${faits.numeroMandat}${effet ? ` au ${jjmmaaaa(effet)}` : ''} au dossier, le bien est encore diffusé`, pourquoi: 'sans mandat, le bien ne se diffuse plus' })
    }
  }

  return alertes
}
