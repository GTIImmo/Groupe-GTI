// GED (13/11/2026, morceau 8) -- LES PROPOSITIONS « REMPLIR » : une valeur LUE dans un document, pour une case VIDE.
// Fonction pure, sans lecture ni écriture : essais hors ligne dans test_ged_remplir.cjs. L'écriture passe par les
// gestes EXISTANTS, appelés par l'écran après avoir RELU la case juste avant (App.tsx, remplirDepuisDocument).
// ⛔ Jamais par-dessus une valeur. ⛔ Ni la taxe foncière (son groupe Hektor renvoie aussi prix et honoraires), ni un
//   champ du mandat (décision ⑦-7), ni l'adresse, ni les mandants. Note du chantier §12.18.
import { annualiser, dateLue, LIBELLE_CONDITION, lireDateIso, nombreLu, texteLu, comparerNumero, type ConditionLue } from './gedComparer'
import type { FaitsRegles } from './gedRegles'
import type { DocumentLu } from './gedReglesLues'

// fiche : la case de la fiche (nom Hektor), par editAnnonceOptimistic ; charge : le registre des mandats, par
// ecrireMandatCharge ; condition : la liste des conditions d'une transaction, par ecrireAffaireConditions ;
// contact (lot 9c) : une case de la fiche d'un mandant, par editContactOptimistic (gedRemplirContact.ts).
export type GesteRemplir = 'fiche' | 'charge' | 'condition' | 'contact' | 'affaire'
export type PropositionRemplir = {
  cle: string                // la proposition : « P1.dpe_cons »… (avec la valeur, c'est la clé d'une décision)
  geste: GesteRemplir
  champ: string              // le nom du champ que le geste écrit
  valeur: string             // la valeur, telle qu'elle sera écrite
  texte: string              // ce que l'écran dit
  source: string             // le document et sa page
  lectureId: string | null
  affaireId?: number         // condition : la transaction visée
  contactId?: string         // contact : le contact visé (notre numéro, clé de app_contact_current)
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
export function propositionsRemplir(faits: FaitsRemplir, docs: DocumentLu[], decisions: Set<string>): PropositionRemplir[] {
  const sortie: PropositionRemplir[] = []
  const lus = docs.filter((d) => d.lecture.etat === 'lu')
  const ajouter = (p: PropositionRemplir) => { if (!decisions.has(`${p.cle}|${p.valeur}`)) sortie.push(p) }

  // P1 (DPE, date de l'état des risques) et P2 (copropriété : nombre de lots, charges annuelles) -- RETIRÉS le 18/11 (lot 3) :
  // la fiche du bien face à ses documents passe par la fenêtre « Ce que dit le DPE… » (gedBilanFiche.ts), qui propose la case
  // VIDE à ajouter ET la case remplie qui diffère à corriger -- un seul chemin par case, jamais deux.

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

  // P4 (lots 10a et 10b) -- RETIRÉ le 17/11 (lot 10c) : le compromis lu face à SA transaction passe désormais par la
  // fenêtre « Ce que dit le compromis » (gedBilanCompromis.ts), un seul chemin par champ. Les champs que Hektor connaît
  // (date d'acte, séquestre) s'y envoient par la modale « Modifier le compromis » -- jamais plus « chez nous seulement ».

  return sortie
}

// Lot 10b : la liste de conditions d'une proposition, en texte (la clé d'une décision est « cle|valeur ») --
// « nature@date|nature@ » ; le décodage rejette tout ce qui n'est pas une nature connue et une date AAAA-MM-JJ.
export function encoderConditions(cs: ConditionLue[]): string {
  return cs.map((c) => `${c.nature}@${c.date ?? ''}`).join('|')
}
export function decoderConditions(s: string): ConditionLue[] {
  return s.split('|').map((m) => m.split('@')).filter(([n, d]) => n in LIBELLE_CONDITION && (!d || /^\d{4}-\d{2}-\d{2}$/.test(d)))
    .map(([n, d]) => ({ nature: n as ConditionLue['nature'], date: d || null }))
}

// Une case de la fiche est-elle VIDE ? (Hektor met « 0 » ou « 0000-00-00 » pour rien ; la date zéro 1970 non plus.)
export function caseVide(valeur: string | null | undefined): boolean {
  const s = String(valeur ?? '').trim()
  if (!s) return true
  if (/^0+([.,]0+)?$/.test(s)) return true
  return /^(0000-00-00|1970-01-01)/.test(s)
}
