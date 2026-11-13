// GED (13/11/2026, morceau 7) -- LE SOCLE DES COMPARAISONS : ce que l'IA a LU dans un document, face à ce que nous avons
// (la fiche, les mandants). Fonctions pures, sans lecture ni écriture : essais hors ligne dans test_ged_regles_lues.cjs.
// Chaque comparaison rend « egal », « proche », « different » ou « incomparable ». ⛔ SEUL « different » peut faire
// sonner une règle : une valeur vide, non vue ou incertaine, une unité ou une base inconnue -> « incomparable », silence.
// Catalogue : E_synthese_catalogue.md §2 (C1 nombre, C2 date, C3 personnes, C4 lieu, C6 liste) ; note du chantier §12.17.
import type { LectureDocument, ValeurLue } from './gedLecture'

export type Verdict = 'egal' | 'proche' | 'different' | 'incomparable'

// LES TOLÉRANCES, en UN seul endroit (§2 de l'étude) : on prend la plus large de l'absolue et de la relative.
export const TOLERANCES = {
  euros: { absolue: 1, relative: 0 },
  taxe: { absolue: 5, relative: 0.02 },
  chargesAnnuelles: { absolue: 120, relative: 0.1 },
  dpe: { absolue: 1, relative: 0 },
  carrezSensUnique: 0.05,
}

// ── Étape 0 : normaliser ──────────────────────────────────────────────────────
// Un texte sans accents, en capitales, la ponctuation en espaces : « Saint-Étienne » = « ST ETIENNE ».
export function normaliserTexte(v: string | null | undefined): string {
  return String(v ?? '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, ' ')
    .replace(/\bSAINTE\b/g, 'STE').replace(/\bSAINT\b/g, 'ST')
    .replace(/\s+/g, ' ').trim()
}

// Un nombre de la fiche ou du document : « 1 234,50 », « 0581 », « 0 » (= vide chez Hektor).
export function lireNombre(v: string | number | null | undefined): number | null {
  if (v == null) return null
  const x = typeof v === 'number' ? v : Number(String(v).replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(x) && x > 0 ? x : null
}

// La valeur LUE d'une clé (rang 0), seulement si elle a été lue nettement : « incertain » ne compare pas.
export function valeurNette(valeurs: ValeurLue[], cle: string): ValeurLue | null {
  const v = valeurs.find((x) => x.cle === cle && x.rang === 0)
  return v && v.etat === 'lu' ? v : null
}
export const texteLu = (valeurs: ValeurLue[], cle: string) => valeurNette(valeurs, cle)?.valeur ?? null
export const nombreLu = (valeurs: ValeurLue[], cle: string) => valeurNette(valeurs, cle)?.valeur_num ?? null
export const dateLue = (valeurs: ValeurLue[], cle: string) => valeurNette(valeurs, cle)?.valeur_date ?? null

// ── C1 : nombre ───────────────────────────────────────────────────────────────
export function comparerNombre(lu: number | null, base: number | null, tol: { absolue: number; relative: number }): Verdict {
  if (lu == null || base == null) return 'incomparable'
  const ecart = Math.abs(lu - base)
  if (ecart === 0) return 'egal'
  return ecart <= Math.max(tol.absolue, tol.relative * Math.max(lu, base)) ? 'proche' : 'different'
}

// Une somme périodique ramenée à l'année (un appel de fonds trimestriel × 4). Période inconnue -> null (incomparable).
export function annualiser(montant: number | null, periode: string | null): number | null {
  const fois: Record<string, number> = { mois: 12, trimestre: 4, semestre: 2, annuel: 1 }
  return montant != null && periode && fois[periode] ? montant * fois[periode] : null
}

// ── C2 : date et validités ────────────────────────────────────────────────────
const JOUR = 86_400_000
export function lireDateIso(v: string | null | undefined): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(v ?? ''))
  if (!m) return null
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])))
  return Number.isNaN(d.getTime()) || d.getUTCFullYear() < 1980 ? null : d
}
const plusMois = (d: Date, mois: number) => new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + mois, d.getUTCDate()))

// La fin de validité d'un diagnostic pour une VENTE, d'après sa date et ce qu'il dit. null = sans limite (ou inconnue).
// Électricité, gaz, assainissement non collectif : 3 ans ; termites : 6 mois ; plomb : 1 an s'il y en a au-dessus du
// seuil, sans limite sinon. (L'état des risques est la règle N4 ; le DPE, N5 sur la fiche et L6.)
export function finDeValidite(type: string, date: Date, resultat: string | null): Date | null {
  if (type === 'diag.electricite' || type === 'diag.gaz' || type === 'diag.assainissement') return plusMois(date, 36)
  if (type === 'diag.termites') return plusMois(date, 6)
  if (type === 'diag.plomb') return resultat === 'au_dessus_du_seuil' ? plusMois(date, 12) : null
  return null
}
export const joursEntre = (a: Date, b: Date) => Math.round((b.getTime() - a.getTime()) / JOUR)

// ── C4 : lieu ─────────────────────────────────────────────────────────────────
// Même commune : égalité après normalisation, ou l'une contient l'autre (« FIRMINY CEDEX », « ST ETIENNE 42100 »).
// ⚠ Pas de table des communes nouvelles : un « different » se dit « à vérifier », jamais « faux ».
export function comparerCommune(lue: string | null, duBien: string | null): Verdict {
  const a = normaliserTexte(lue).replace(/\b\d{5}\b/g, '').trim()
  const b = normaliserTexte(duBien).replace(/\b\d{5}\b/g, '').trim()
  if (!a || !b) return 'incomparable'
  if (a === b) return 'egal'
  const mots = (s: string) => ` ${s.replace(/\bCEDEX\b/g, '').trim()} `
  return mots(a).includes(mots(b)) || mots(b).includes(mots(a)) ? 'proche' : 'different'
}

// ── C5 : références ───────────────────────────────────────────────────────────
// Un numéro de mandat comparé par ses CHIFFRES, sans les zéros de tête (« n° 018836 », « 18836/2026 » -> la suite
// la plus longue). Pas de chiffres d'un côté -> incomparable.
export function comparerNumero(lu: string | null | undefined, base: string | null | undefined): Verdict {
  const suite = (s: string | null | undefined) => (String(s ?? '').match(/\d+/g) ?? []).reduce((a, b) => (b.length > a.length ? b : a), '').replace(/^0+/, '')
  const a = suite(lu)
  const b = suite(base)
  if (!a || !b) return 'incomparable'
  return a === b ? 'egal' : 'different'
}

// C6 : une valeur de liste fermée, avec ses synonymes (le type du mandat de la fiche, la charge des honoraires).
const SYNONYMES: Record<string, string> = {
  EXCLUSIF: 'exclusif', SIMPLE: 'simple', 'SEMI EXCLUSIF': 'semi_exclusif', 'CO EXCLUSIF': 'semi_exclusif',
  VENDEUR: 'vendeur', MANDANT: 'vendeur', ACQUEREUR: 'acquereur', ACHETEUR: 'acquereur', 'LES DEUX': 'les_deux',
}
export function comparerListe(lu: string | null | undefined, base: string | null | undefined): Verdict {
  const sens = (s: string | null | undefined) => { const n = normaliserTexte(s); return SYNONYMES[n] ?? (n ? n.toLowerCase().replace(/ /g, '_') : '') }
  const a = sens(lu)
  const b = sens(base)
  if (!a || !b) return 'incomparable'
  return a === b ? 'egal' : 'different'
}

// ── Étape 1 : résoudre la cible (7c) ─────────────────────────────────────────
// LA ligne du registre que vise un document lu, parmi celles du bon genre : d'abord par les ACQUÉREURS (un nom lu
// retrouvé), puis par la DATE (± 15 jours), puis par le MONTANT (± 1 %), et une ligne seule se prend telle quelle.
// Zéro ou plusieurs candidates à la fin -> null : la règle se tait (jamais « comparer à la mauvaise ligne »).
// ⚠ La date d'une offre REFUSÉE est celle du refus (mémoire du 12/11) : pour une offre, le nom passe avant la date.
export type CandidateAffaire = { date?: string | null; montant?: number | null; acquereurs?: PersonneDuBien[] }
export function resoudreCible<T extends CandidateAffaire>(candidates: T[], indices: { acquereurs?: PersonneLue[]; date?: string | null; montant?: number | null }): T | null {
  let reste = candidates
  if (reste.length > 1 && indices.acquereurs?.length) {
    const parNom = reste.filter((c) => (indices.acquereurs as PersonneLue[]).some((p) => ['egal', 'proche'].includes(personneSurLaFiche(p, c.acquereurs ?? []))))
    if (parNom.length) reste = parNom
  }
  const date = lireDateIso(indices.date)
  if (reste.length > 1 && date) {
    const parDate = reste.filter((c) => { const d = lireDateIso(c.date); return d && Math.abs(joursEntre(d, date)) <= 15 })
    if (parDate.length) reste = parDate
  }
  if (reste.length > 1 && indices.montant != null) {
    const parMontant = reste.filter((c) => c.montant != null && comparerNombre(indices.montant as number, c.montant, { absolue: 1, relative: 0.01 }) !== 'different')
    if (parMontant.length) reste = parMontant
  }
  return reste.length === 1 ? reste[0] : null
}

// ── C3 : personnes ────────────────────────────────────────────────────────────
export type PersonneDuBien = { nom: string; prenom: string }
export type PersonneLue = { nom: string; prenoms: string; qualite: string | null }

// Les personnes LUES d'une lecture (liste « personnes »), nettement lues seulement.
export function personnesLuesDe(l: Pick<LectureDocument, 'valeurs'>): PersonneLue[] {
  const rangs = [...new Set(l.valeurs.filter((x) => x.cle === 'personnes.nom' && x.etat === 'lu' && x.valeur).map((x) => x.rang))]
  return rangs.map((r) => ({
    nom: l.valeurs.find((x) => x.cle === 'personnes.nom' && x.rang === r)?.valeur ?? '',
    prenoms: l.valeurs.find((x) => x.cle === 'personnes.prenoms' && x.rang === r && x.etat !== 'non_vu')?.valeur ?? '',
    qualite: l.valeurs.find((x) => x.cle === 'personnes.qualite' && x.rang === r && x.etat !== 'non_vu')?.valeur ?? null,
  }))
}

const MOTS_VIDES = new Set(['DE', 'DU', 'DES', 'LE', 'LA', 'LES', 'ET', 'EP', 'NEE', 'VEUVE', 'VVE', 'M', 'MME', 'MR', 'MLLE'])
const motsDe = (s: string) => normaliserTexte(s).split(' ').filter((m) => m.length >= 2 && !MOTS_VIDES.has(m))

// Une personne lue est-elle sur la fiche ? « egal » : nom et un prénom ; « proche » : un mot du nom retrouvé (prénom
// absent, nom composé, nom et prénom inversés, fiche de couple « M. et Mme X ») ; « different » : AUCUN mot de son nom ni de
// ses prénoms n'est chez une personne du bien ; « incomparable » : la fiche n'a personne. Prudente par construction : on
// préfère se taire sur un vrai inconnu que crier sur un couple mal rangé.
export function personneSurLaFiche(lue: PersonneLue, duBien: PersonneDuBien[]): Verdict {
  if (!duBien.length) return 'incomparable'
  const nom = motsDe(lue.nom)
  if (!nom.length) return 'incomparable'
  const prenoms = motsDe(lue.prenoms)
  let proche = false
  for (const p of duBien) {
    const sesMots = new Set([...motsDe(p.nom), ...motsDe(p.prenom)])
    const nomVu = nom.some((m) => sesMots.has(m))
    if (nomVu && prenoms.some((m) => motsDe(p.prenom).includes(m))) return 'egal'
    if (nomVu || prenoms.some((m) => motsDe(p.nom).includes(m))) proche = true
  }
  return proche ? 'proche' : 'different'
}
