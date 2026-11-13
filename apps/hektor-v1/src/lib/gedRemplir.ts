// GED (13/11/2026, morceau 8) -- LES PROPOSITIONS « REMPLIR » : une valeur LUE dans un document, pour une case VIDE.
// Fonction pure, sans lecture ni écriture : essais hors ligne dans test_ged_remplir.cjs. L'écriture passe par les
// gestes EXISTANTS, appelés par l'écran après avoir RELU la case juste avant (App.tsx, remplirDepuisDocument).
// ⛔ Jamais par-dessus une valeur. ⛔ Ni la taxe foncière (son groupe Hektor renvoie aussi prix et honoraires), ni un
//   champ du mandat (décision ⑦-7), ni l'adresse, ni les mandants. Note du chantier §12.18.
import { annualiser, dateLue, lireDateIso, nombreLu, resoudreCible, texteLu, comparerNumero, personnesLuesDe } from './gedComparer'
import type { AffaireRegle, FaitsRegles } from './gedRegles'
import type { DocumentLu } from './gedReglesLues'

// fiche : la case de la fiche (nom Hektor), par editAnnonceOptimistic ; charge : le registre des mandats, par
// ecrireMandatCharge ; condition : la liste des conditions d'une transaction, par ecrireAffaireConditions.
export type GesteRemplir = 'fiche' | 'charge' | 'condition'
export type PropositionRemplir = {
  cle: string                // la proposition : « P1.dpe_cons »… (avec la valeur, c'est la clé d'une décision)
  geste: GesteRemplir
  champ: string              // le nom du champ que le geste écrit
  valeur: string             // la valeur, telle qu'elle sera écrite
  texte: string              // ce que l'écran dit
  source: string             // le document et sa page
  lectureId: string | null
  affaireId?: number         // condition : la transaction visée
}

// Faits de la fiche utiles ici en plus de ceux des règles (valeurs BRUTES : null = case vide).
export type FaitsRemplir = FaitsRegles & { quotePart?: number | null; erpDate?: string | null }

const jjmmaaaa = (iso: string) => { const [a, m, j] = iso.slice(0, 10).split('-'); return `${j}/${m}/${a}` }
const nombreTexte = (x: number) => String(Math.round(x * 100) / 100)

function plusRecent(docs: DocumentLu[], type: string, cleDate: string): DocumentLu | null {
  const deType = docs.filter((d) => d.lecture.typeCode === type && d.lecture.etat === 'lu')
  if (!deType.length) return null
  return deType.reduce((a, b) => {
    const da = lireDateIso(dateLue(a.lecture.valeurs, cleDate))
    const db = lireDateIso(dateLue(b.lecture.valeurs, cleDate))
    return db && (!da || db > da) ? b : a
  })
}
const page = (d: DocumentLu, cle: string) => d.lecture.valeurs.find((x) => x.cle === cle && x.rang === 0)?.page ?? null
const source = (d: DocumentLu, cle: string) => { const p = page(d, cle); return `${d.nom}${p ? `, page ${p}` : ''}` }

// `decisions` : les clés « cle|valeur » déjà remplies ou ignorées (app_ged_decision) -- elles ne reviennent pas.
// `conditionsParAffaire` : le nombre de conditions de chaque transaction, LU SANS ERREUR (absent = inconnu = rien).
export function propositionsRemplir(
  faits: FaitsRemplir, docs: DocumentLu[], affaires: AffaireRegle[], decisions: Set<string>,
  conditionsParAffaire: Map<number, number>,
): PropositionRemplir[] {
  const sortie: PropositionRemplir[] = []
  const lus = docs.filter((d) => d.lecture.etat === 'lu')
  const ajouter = (p: PropositionRemplir) => { if (!decisions.has(`${p.cle}|${p.valeur}`)) sortie.push(p) }

  // P1 -- le DPE (consommation, émissions, date) et la date de l'état des risques, cases VIDES seulement.
  const dpe = plusRecent(lus, 'diag.dpe', 'date_etablissement')
  if (dpe) {
    const v = dpe.lecture.valeurs
    const conso = nombreLu(v, 'conso_ep')
    const ges = nombreLu(v, 'emissions')
    const date = dateLue(v, 'date_etablissement')
    if (faits.dpeConso == null && conso != null) ajouter({ cle: 'P1.dpe_cons', geste: 'fiche', champ: 'dpe_cons', valeur: String(Math.round(conso)), texte: `DPE : consommation ${Math.round(conso)} kWh/m²/an`, source: source(dpe, 'conso_ep'), lectureId: dpe.lecture.id ?? null })
    if (faits.dpeGes == null && ges != null) ajouter({ cle: 'P1.dpe_ges', geste: 'fiche', champ: 'dpe_ges', valeur: String(Math.round(ges)), texte: `DPE : émissions ${Math.round(ges)} kg CO₂/m²/an`, source: source(dpe, 'emissions'), lectureId: dpe.lecture.id ?? null })
    if (!lireDateIso(faits.dpeDate) && date) ajouter({ cle: 'P1.dpe_date', geste: 'fiche', champ: 'dpe_date', valeur: date, texte: `DPE : établi le ${jjmmaaaa(date)}`, source: source(dpe, 'date_etablissement'), lectureId: dpe.lecture.id ?? null })
  }
  const erp = plusRecent(lus, 'diag.erp', 'date_etablissement')
  const dateErp = erp ? dateLue(erp.lecture.valeurs, 'date_etablissement') : null
  if (erp && dateErp && !lireDateIso(faits.erpDate)) {
    ajouter({ cle: 'P1.diag_risques_nat_tech_date', geste: 'fiche', champ: 'diag_risques_nat_tech_date', valeur: dateErp, texte: `État des risques : établi le ${jjmmaaaa(dateErp)}`, source: source(erp, 'date_etablissement'), lectureId: erp.lecture.id ?? null })
  }

  // P2 -- la copropriété : le nombre de lots (fiche synthétique) et la quote-part annuelle (appel de fonds, arrêté).
  // Seulement sur un bien MARQUÉ copropriété : jamais rien qui ferait passer la case à OUI.
  if (faits.copropriete === true) {
    const carnet = lus.find((x) => x.lecture.typeCode === 'copro.carnet' && texteLu(x.lecture.valeurs, 'sous_type') === 'fiche_synthetique')
    const total = carnet ? nombreLu(carnet.lecture.valeurs, 'nb_lots_total') : null
    if (carnet && faits.nbLots == null && total != null) ajouter({ cle: 'P2.copropriete_nb_lot', geste: 'fiche', champ: 'copropriete_nb_lot', valeur: String(Math.round(total)), texte: `Copropriété : ${Math.round(total)} lots`, source: source(carnet, 'nb_lots_total'), lectureId: carnet.lecture.id ?? null })
    const appels = lus.filter((x) => x.lecture.typeCode === 'copro.appel_fonds' || x.lecture.typeCode === 'copro.arrete_charges')
    const appel = appels.length ? appels.reduce((a, b) => ((lireDateIso(dateLue(b.lecture.valeurs, 'date_document')) ?? 0) > (lireDateIso(dateLue(a.lecture.valeurs, 'date_document')) ?? 0) ? b : a)) : null
    if (appel && faits.quotePart == null) {
      const v = appel.lecture.valeurs
      const cle = nombreLu(v, 'budget_annuel_lot') != null ? 'budget_annuel_lot' : nombreLu(v, 'charges_courantes_lot') != null ? 'charges_courantes_lot' : 'provision_budget'
      const annuel = nombreLu(v, 'budget_annuel_lot') ?? nombreLu(v, 'charges_courantes_lot') ?? annualiser(nombreLu(v, 'provision_budget'), texteLu(v, 'periode'))
      if (annuel != null) ajouter({ cle: 'P2.copropriete_quote_part', geste: 'fiche', champ: 'copropriete_quote_part', valeur: nombreTexte(annuel), texte: `Copropriété : charges du lot ${nombreTexte(annuel).replace('.', ',')} € par an`, source: source(appel, cle), lectureId: appel.lecture.id ?? null })
    }
  }

  // P3 -- qui paie les honoraires, au REGISTRE des mandats, si sa case est VIDE (lue et vide : `null` ; pas lue :
  // `undefined` -> rien). L'avenant fait foi sur le mandat ; « les deux » ne se remplit pas (un seul payeur au registre).
  if (faits.chargeRegistre === null) {
    const meme = (d: DocumentLu | undefined) => !!d && comparerNumero(texteLu(d.lecture.valeurs, 'numero_mandat'), faits.numeroMandat) !== 'different'
    const avenant = plusRecent(lus, 'mandat.avenant', 'date_avenant') ?? undefined
    const mandat = plusRecent(lus, 'mandat.vente', 'date_signature') ?? undefined
    const d = [avenant, mandat].find((x) => meme(x) && texteLu((x as DocumentLu).lecture.valeurs, 'charge_honoraires'))
    const charge = d ? texteLu(d.lecture.valeurs, 'charge_honoraires') : null
    if (d && faits.numeroMandat && (charge === 'vendeur' || charge === 'acquereur')) {
      ajouter({ cle: 'P3.charge_honoraires', geste: 'charge', champ: 'charge_honoraires', valeur: charge, texte: `Honoraires à la charge ${charge === 'vendeur' ? 'du vendeur' : 'de l\'acquéreur'} (registre des mandats)`, source: source(d, 'charge_honoraires'), lectureId: d.lecture.id ?? null })
    }
  }

  // P4 -- la condition « Obtention Crédit » avec la date limite du prêt, sur LA transaction du compromis lu, si sa liste
  // de conditions est VIDE (comptée sans erreur). Le geste remplace toute la liste : vide = rien à perdre.
  const cpv = plusRecent(lus, 'transaction.avant_contrat', 'date_signature')
  if (cpv && texteLu(cpv.lecture.valeurs, 'condition_pret') === 'oui') {
    const limite = dateLue(cpv.lecture.valeurs, 'date_limite_pret')
    const ligne = resoudreCible(affaires.filter((a) => a.kind === 'compromis' && !['refused', 'cancelled'].includes(String(a.state ?? ''))), {
      acquereurs: personnesLuesDe(cpv.lecture).filter((p) => p.qualite === 'acquereur'), date: dateLue(cpv.lecture.valeurs, 'date_signature'), montant: nombreLu(cpv.lecture.valeurs, 'prix'),
    })
    if (limite && ligne?.id != null && conditionsParAffaire.get(ligne.id) === 0) {
      ajouter({ cle: 'P4.condition_credit', geste: 'condition', champ: 'Obtention Crédit', valeur: limite, texte: `Condition « Obtention Crédit » jusqu'au ${jjmmaaaa(limite)}`, source: source(cpv, 'date_limite_pret'), lectureId: cpv.lecture.id ?? null, affaireId: ligne.id })
    }
  }

  return sortie
}

// Une case de la fiche est-elle VIDE ? (Hektor met « 0 » ou « 0000-00-00 » pour rien ; la date zéro 1970 non plus.)
export function caseVide(valeur: string | null | undefined): boolean {
  const s = String(valeur ?? '').trim()
  if (!s) return true
  if (/^0+([.,]0+)?$/.test(s)) return true
  return /^(0000-00-00|1970-01-01)/.test(s)
}
