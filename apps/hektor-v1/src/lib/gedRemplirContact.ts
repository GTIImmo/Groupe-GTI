// GED (14/11/2026, morceau 9, lot 9c) -- REMPLIR LA FICHE D'UN MANDANT depuis ses pièces lues : C1 la date de naissance,
// C2 le lieu de naissance (pièce d'identité ou fiche de renseignements), C3 la situation de famille (fiche de
// renseignements seulement). Fonction pure : essais hors ligne dans test_ged_remplir_contact.cjs. L'écriture passe par
// le geste EXISTANT « modifier un contact » (editContactOptimistic), appelé par l'écran après avoir RELU le contact
// (App.tsx, remplirDepuisDocument). Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md, audit du lot 9c.
// ⛔ Jamais par-dessus une valeur. ⛔ Ni l'adresse, ni le régime matrimonial. ⛔ Une PERSONNE SEULE seulement (un couple :
//   plus tard). ⛔ Le nom et le premier prénom EXACTEMENT ceux de la pièce, et une seule personne du bien qui les porte.
//   ⛔ Deux pièces qui se contredisent : rien.
import { normaliserTexte, type PersonneDuBien } from './gedComparer'
import type { BilanCompromis, EtatBilan, GenrePersonne, LigneBilan } from './gedBilanCompromis'
import type { LectureDocument } from './gedLecture'
import type { DocumentLu } from './gedReglesLues'
import { caseVide, type PropositionRemplir } from './gedRemplir'

// Un contact du bien, RELU dans app_contact_current (valeurs brutes : null ou vide = case vide).
export type ContactEtatCivil = {
  contactId: string
  nom: string
  prenom: string
  personneSeule: boolean      // nature_fiche « personne_seule », sans rôle de couple, pas une fiche fusionnée à l'écran
  // lot F (18/11) : la PREMIÈRE personne d'un couple (nature_fiche « couple », sans rôle) -- sa fiche Hektor est le
  // formulaire de couple, que le worker relit et renvoie avec le bloc du conjoint intact
  premiereDuCouple?: boolean
  naissance: string | null
  lieu: string | null
  situation: string | null
}

// Les codes de Hektor (la fenêtre « Modifier » : married, single, widower, divorced, civil_union). « separe »,
// « concubinage » et « autre » n'en ont pas : ils ne se proposent jamais.
export const SITUATION_HEKTOR: Record<string, string> = { marie: 'married', celibataire: 'single', veuf: 'widower', divorce: 'divorced', pacse: 'civil_union' }
const SITUATION_TEXTE: Record<string, string> = { married: 'marié(e)', single: 'célibataire', widower: 'veuf(ve)', divorced: 'divorcé(e)', civil_union: 'pacsé(e)' }

// Une personne lue, NETTEMENT (etat « lu ») : dans une pièce d'identité (liste « pieces ») ou une fiche de
// renseignements (liste « personnes »).
type PersonneLueEtatCivil = { nom: string; nomUsage: string; prenoms: string; naissance: string | null; lieu: string | null; situation: string | null; source: string; lectureId: string | null; page: number | null }

function personnesDe(d: DocumentLu): PersonneLueEtatCivil[] {
  const l: LectureDocument = d.lecture
  const liste = l.typeCode === 'justif.identite' ? 'pieces' : l.typeCode === 'transaction.renseignements' ? 'personnes' : null
  if (!liste || l.etat !== 'lu') return []
  const net = (cle: string, r: number) => l.valeurs.find((x) => x.cle === `${liste}.${cle}` && x.rang === r && x.etat === 'lu')
  const rangs = [...new Set(l.valeurs.filter((x) => x.cle === `${liste}.nom` && x.etat === 'lu' && x.valeur).map((x) => x.rang))]
  return rangs.map((r) => {
    const page = net('nom', r)?.page
    return {
      nom: net('nom', r)?.valeur ?? '',
      nomUsage: net('nom_usage', r)?.valeur ?? '',
      prenoms: net('prenoms', r)?.valeur ?? '',
      naissance: net('date_naissance', r)?.valeur_date ?? null,
      lieu: (net('lieu_naissance', r)?.valeur ?? '').trim() || null,
      situation: liste === 'personnes' ? (net('situation_famille', r)?.valeur ?? null) : null,
      source: `${d.nom}${page ? `, page ${page}` : ''}`,
      lectureId: l.id ?? null,
      page: page ?? null,
    }
  })
}

// La personne lue porte-t-elle EXACTEMENT ce nom (de naissance ou d'usage) et ce premier prénom ?
const premierMot = (s: string) => normaliserTexte(s).split(' ')[0] ?? ''
function memePersonne(lue: PersonneLueEtatCivil, p: PersonneDuBien): boolean {
  const nom = normaliserTexte(p.nom)
  const prenom = premierMot(p.prenom)
  if (!nom || !prenom) return false
  return [lue.nom, lue.nomUsage].some((n) => n && normaliserTexte(n) === nom) && premierMot(lue.prenoms) === prenom
}

const jjmmaaaa = (iso: string) => { const [a, m, j] = iso.slice(0, 10).split('-'); return `${j}/${m}/${a}` }
function naissanceValable(iso: string | null, aujourdhui: Date): string | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '')
  if (!m) return null
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])))
  if (Number.isNaN(d.getTime()) || d.getUTCDate() !== Number(m[3]) || Number(m[1]) < 1900 || d >= aujourdhui) return null
  return iso as string
}

// Une seule valeur, ou rien : toutes les pièces qui en disent une disent LA MÊME (comparée sans casse ni accents).
function uneSeule<T extends { valeur: string }>(lues: T[], comparer: (v: string) => string): T | null {
  if (!lues.length) return null
  const premiere = comparer(lues[0].valeur)
  return lues.every((x) => comparer(x.valeur) === premiere) ? lues[0] : null
}

// `personnesDuBien` : TOUTES les personnes du bien (membres d'un couple compris) -- une pièce qui correspond à deux
// d'entre elles ne se rattache à personne. `decisions` : les clés « cle|valeur » déjà remplies ou ignorées.
export function propositionsContact(
  contacts: ContactEtatCivil[], personnesDuBien: PersonneDuBien[], docs: DocumentLu[], decisions: Set<string>, aujourdhui: Date,
): PropositionRemplir[] {
  const sortie: PropositionRemplir[] = []
  const lues = docs.flatMap(personnesDe)
  for (const c of contacts) {
    if (!c.personneSeule || !/^\d+$/.test(c.contactId)) continue
    const fiche = { nom: c.nom, prenom: c.prenom }
    const siennes = lues.filter((l) => memePersonne(l, fiche) && personnesDuBien.filter((p) => memePersonne(l, p)).length <= 1)
    if (!siennes.length) continue
    const qui = [c.prenom, c.nom].filter(Boolean).join(' ')
    const ajouter = (p: Omit<PropositionRemplir, 'geste' | 'contactId'>) => {
      if (!decisions.has(`${p.cle}|${p.valeur}`)) sortie.push({ ...p, geste: 'contact', contactId: c.contactId })
    }

    if (caseVide(c.naissance)) {
      const v = uneSeule(siennes.flatMap((l) => { const n = naissanceValable(l.naissance, aujourdhui); return n ? [{ valeur: n, l }] : [] }), (x) => x)
      if (v) ajouter({ cle: `C1.birth_date.${c.contactId}`, champ: 'birth_date', valeur: v.valeur, texte: `${qui} : date de naissance ${jjmmaaaa(v.valeur)}`, source: v.l.source, lectureId: v.l.lectureId })
    }
    if (!String(c.lieu ?? '').trim()) {
      const v = uneSeule(siennes.flatMap((l) => (l.lieu ? [{ valeur: l.lieu, l }] : [])), normaliserTexte)
      if (v) ajouter({ cle: `C2.birth_place.${c.contactId}`, champ: 'birth_place', valeur: v.valeur, texte: `${qui} : lieu de naissance ${v.valeur}`, source: v.l.source, lectureId: v.l.lectureId })
    }
    if (!String(c.situation ?? '').trim()) {
      // une situation SANS code Hektor (séparé, concubinage, autre) compte quand même comme une voix : elle contredit
      const dites = siennes.flatMap((l) => (l.situation ? [{ valeur: l.situation, l }] : []))
      const v = uneSeule(dites, (x) => x)
      const code = v ? SITUATION_HEKTOR[v.valeur] : undefined
      if (v && code) ajouter({ cle: `C3.marital_status.${c.contactId}`, champ: 'marital_status', valeur: code, texte: `${qui} : situation de famille « ${SITUATION_TEXTE[code]} »`, source: v.l.source, lectureId: v.l.lectureId })
    }
  }
  return sortie
}

// ── GED lot F (18/11) -- « Ce que dit la pièce d'identité / la fiche de renseignements » ─────────────────────────────
// La même fenêtre que le compromis et la fiche du bien (BilanCompromis.tsx), UNE PAR DOCUMENT LU. Ses lignes : pour chaque
// personne du bien qu'il nomme (nom ET premier prénom stricts, une seule personne du bien qui les porte -- comme 9c), sa
// date et son lieu de naissance, et (fiche de renseignements seulement) la situation de famille. Case vide -> à ajouter ;
// différente -> à trancher (on n'écrit par-dessus que sur le choix de l'humain) ; égale -> d'accord. Personne seule et
// PREMIÈRE personne d'un couple. Les cartes C1-C3 se retirent au profit de la fenêtre (un seul chemin par case).
// ⛔ Un seul chemin par case : la naissance d'une personne est dite par SA pièce d'identité la plus récemment lue ; la
//   fiche de renseignements n'en parle que si aucune pièce d'identité lue ne nomme la personne. Les pièces d'identité de
//   la même personne qui se contredisent : aucune ne parle de la case en désaccord.
// ⛔ Jamais l'adresse, ni le régime matrimonial, ni le numéro, la délivrance ou l'autorité de la pièce (ged_prive).
const DOC_PERSONNE: Record<string, GenrePersonne> = { 'justif.identite': 'identite', 'transaction.renseignements': 'renseignements' }

export function bilansPersonnes(contacts: ContactEtatCivil[], personnesDuBien: PersonneDuBien[], docs: DocumentLu[], aujourdhui: Date): BilanCompromis[] {
  // ⛔ une première de couple au nom ou au prénom FUSIONNÉ (« Annette et Patrick », « DUPONT/ MARTIN » : 3 104 prénoms et
  //   640 noms sur 6 597 premières fiches, mesuré le 18/11) ne se propose pas : son premier prénom ne dit pas QUI est la
  //   première personne chez Hektor -- la pièce du conjoint finirait sur la fiche de l'autre
  const fusionne = (s: string) => /( et |\/|&|\+)/i.test(` ${s} `)
  const eligibles = contacts.filter((c) => (c.personneSeule || (c.premiereDuCouple === true && !fusionne(c.prenom) && !fusionne(c.nom))) && /^\d+$/.test(c.contactId))
  const lus = docs.filter((d) => d.lecture.etat === 'lu' && DOC_PERSONNE[d.lecture.typeCode])
    .map((d) => ({ d, personnes: personnesDe(d) }))
  // la personne lue dans ce document pour ce contact, si elle se rattache sans ambiguïté
  const laSienne = (personnes: PersonneLueEtatCivil[], c: ContactEtatCivil) => personnes.find((l) => memePersonne(l, { nom: c.nom, prenom: c.prenom })
    && personnesDuBien.filter((p) => memePersonne(l, p)).length <= 1) ?? null
  const sortie: BilanCompromis[] = []
  for (const { d, personnes } of lus) {
    const genre = DOC_PERSONNE[d.lecture.typeCode]
    const lignes: LigneBilan[] = []
    for (const c of eligibles) {
      const lue = laSienne(personnes, c)
      if (!lue) continue
      const qui = [premierMot(c.prenom) ? c.prenom.trim().split(/\s+/)[0] : '', c.nom].filter(Boolean).join(' ')
      const ligneCase = (champ: string, libelle: string, lu: string, valeur: string, fiche: string | null, egal: (f: string) => boolean, clair: (f: string) => string): LigneBilan => {
        const brut = String(fiche ?? '').trim()
        const vide = !brut || (champ === 'birth_date' && caseVide(brut))
        const etat: EtatBilan = vide ? 'ajouter' : egal(brut) ? 'accord' : 'trancher'
        return {
          cle: `P.${champ}.${c.contactId}`, libelle: `${libelle} de ${qui}`, destination: 'hektor', etat, lu, valeur, transaction: vide ? null : clair(brut),
          page: lue.page, note: null, champModale: null, condition: null, regle: null, attente: null, fige: null, champFiche: champ, temoin: vide ? null : brut,
        }
      }
      // la naissance : SA pièce d'identité la plus récemment lue (et les autres pièces d'accord) ; sinon la fiche
      const pieces = lus.filter((x) => x.d.lecture.typeCode === 'justif.identite' && laSienne(x.personnes, c))
        .sort((a, b) => String(b.d.lecture.luLe ?? '').localeCompare(String(a.d.lecture.luLe ?? '')))
      const parle = genre === 'identite' ? pieces[0]?.d === d : pieces.length === 0
      if (parle) {
        const autres = genre === 'identite' ? pieces.map((x) => laSienne(x.personnes, c) as PersonneLueEtatCivil) : [lue]
        const naissance = naissanceValable(lue.naissance, aujourdhui)
        const dates = autres.map((x) => naissanceValable(x.naissance, aujourdhui)).filter((x): x is string => !!x)
        if (naissance && dates.every((x) => x === naissance)) {
          lignes.push(ligneCase('birth_date', 'Date de naissance', jjmmaaaa(naissance), naissance, c.naissance, (f) => f.slice(0, 10) === naissance, (f) => (/^\d{4}-\d{2}-\d{2}/.test(f) ? jjmmaaaa(f) : f)))
        }
        const lieux = autres.map((x) => x.lieu).filter((x): x is string => !!x)
        if (lue.lieu && lieux.every((x) => normaliserTexte(x) === normaliserTexte(lue.lieu as string))) {
          lignes.push(ligneCase('birth_place', 'Lieu de naissance', lue.lieu, lue.lieu, c.lieu, (f) => normaliserTexte(f) === normaliserTexte(lue.lieu as string), (f) => f))
        }
      }
      // la situation de famille : la fiche de renseignements seulement, et seulement un code Hektor
      const code = genre === 'renseignements' && lue.situation ? SITUATION_HEKTOR[lue.situation] : undefined
      if (code) lignes.push(ligneCase('marital_status', 'Situation de famille', SITUATION_TEXTE[code], code, c.situation, (f) => f === code, (f) => SITUATION_TEXTE[f] ?? f))
    }
    if (lignes.length) {
      sortie.push({ genre, lectureId: d.lecture.id ?? null, nom: d.nom, luLe: d.lecture.luLe ?? null, affaireId: 0, dateTransaction: null, conditionsLues: true, conditionsGenerales: [], lignes })
    }
  }
  return sortie
}

// Le contact d'une ligne de la fenêtre (« P.birth_date.<notre numéro> ») -- l'écriture regroupe les lignes par contact.
export const contactDeLaLigne = (cle: string): string | null => { const m = /^P\.(?:birth_date|birth_place|marital_status)\.(\d+)$/.exec(cle); return m ? m[1] : null }
