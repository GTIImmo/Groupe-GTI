// GED (13/11/2026, morceau 9, lot 9b) -- LES RÈGLES DES PIÈCES D'IDENTITÉ LUES : P4 le nom (la pièce face à la fiche),
// P5 la pièce périmée au jour de la signature, P6 une pièce par personne. Fonction pure : essais hors ligne dans
// test_ged_regles_personnes.cjs. Affichées avec les autres règles sous « À regarder », derrière `ged_propositions`.
// On SIGNALE, on n'écrit rien. Le numéro de la pièce n'est jamais là (il est au registre, côté serveur) : seuls le nom,
// les prénoms, la naissance et la fin de validité servent. La ligne « Pièce d'identité de chaque mandant » de « Reçu /
// Manque » (gedPieces.ts) RESTE : elle reconnaît aussi les anciens documents par leur nom (décision du 13/11).
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.19.
import { dateLue, lireDateIso, normaliserTexte, personneSurLaFiche, type PersonneDuBien, type Verdict } from './gedComparer'
import type { LectureDocument } from './gedLecture'
import { momentDuDossier } from './gedPieces'
import type { AffaireRegle, Alerte, FaitsRegles } from './gedRegles'
import type { DocumentLu } from './gedReglesLues'

// Une pièce lue : son document, son rang dans le fichier (une entrée par pièce) et ce que l'IA y a lu NETTEMENT.
export type PieceLue = {
  doc: string; nom: string; nomUsage: string; prenoms: string; nature: string | null
  naissance: string | null; fin: string | null; finIncertaine: boolean
}

export function piecesLuesDe(nomDoc: string, l: Pick<LectureDocument, 'valeurs'>): PieceLue[] {
  const rangs = [...new Set(l.valeurs.filter((x) => x.cle === 'pieces.nom' && x.etat === 'lu' && x.valeur).map((x) => x.rang))]
  const de = (cle: string, r: number) => l.valeurs.find((x) => x.cle === cle && x.rang === r && x.etat !== 'non_vu')
  return rangs.map((r) => ({
    doc: nomDoc,
    nom: de('pieces.nom', r)?.valeur ?? '',
    nomUsage: de('pieces.nom_usage', r)?.valeur ?? '',
    prenoms: de('pieces.prenoms', r)?.valeur ?? '',
    nature: de('pieces.nature', r)?.valeur ?? null,
    naissance: de('pieces.date_naissance', r)?.valeur_date ?? null,
    fin: de('pieces.date_fin_validite', r)?.valeur_date ?? null,
    finIncertaine: de('pieces.date_fin_validite', r)?.etat === 'incertain',
  }))
}

const jjmmaaaa = (d: Date) => `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
const ans = (d: Date, n: number) => new Date(Date.UTC(d.getUTCFullYear() + n, d.getUTCMonth(), d.getUTCDate()))
const nomDe = (p: PieceLue) => [p.prenoms.split(/[, ]+/)[0], p.nom].filter(Boolean).join(' ')
const nomFiche = (p: PersonneDuBien) => [p.prenom, p.nom].filter(Boolean).join(' ')
const SANS_PROLONGATION = new Set(['passeport', 'titre_sejour', 'permis_conduire'])
const NATURE: Record<string, string> = { passeport: 'Le passeport', titre_sejour: 'Le titre de séjour', permis_conduire: 'Le permis de conduire' }
const laPiece = (p: PieceLue) => NATURE[p.nature ?? ''] ?? 'La carte d\'identité'
const perime = (p: PieceLue) => (NATURE[p.nature ?? ''] ? 'périmé' : 'périmée')

// La fin de validité EFFECTIVE. Une carte d'identité délivrée à un MAJEUR du 02/01/2004 au 31/12/2013 vaut 15 ans, malgré
// la date imprimée (10 ans) : on la reconnaît à sa fin imprimée (2014-2023), pas à son « modèle » (l'IA l'a mal lu une
// fois sur deux sur une fausse carte ; une carte au nouveau format ne peut pas finir avant 2031). Mineur à la délivrance
// (naissance lue) : pas de prolongation. Naissance inconnue : on prolonge (on préfère se taire que crier à tort).
export function finEffective(p: Pick<PieceLue, 'nature' | 'naissance' | 'fin'>): { date: Date; prolongee: boolean } | null {
  const fin = lireDateIso(p.fin)
  if (!fin) return null
  if (SANS_PROLONGATION.has(p.nature ?? '')) return { date: fin, prolongee: false }
  if (fin < new Date(Date.UTC(2014, 0, 2)) || fin > new Date(Date.UTC(2023, 11, 31))) return { date: fin, prolongee: false }
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(p.naissance ?? '')
  const naissance = m ? new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]))) : null
  const delivrance = ans(fin, -10)
  if (naissance && ans(naissance, 18) > delivrance) return { date: fin, prolongee: false }
  return { date: ans(fin, 5), prolongee: true }
}

// La personne de la fiche (ou acquéreur) qui correspond le mieux à une pièce : par le nom de naissance OU le nom d'usage.
const RANG: Record<Verdict, number> = { egal: 3, proche: 2, different: 1, incomparable: 0 }
function correspondance(p: PieceLue, personnes: PersonneDuBien[]): { verdict: Verdict; qui: PersonneDuBien | null } {
  let meilleur: { verdict: Verdict; qui: PersonneDuBien | null } = { verdict: personnes.length ? 'different' : 'incomparable', qui: null }
  for (const qui of personnes) {
    for (const nom of [p.nom, p.nomUsage].filter(Boolean)) {
      const v = personneSurLaFiche({ nom, prenoms: p.prenoms, qualite: null }, [qui])
      if (RANG[v] > RANG[meilleur.verdict]) meilleur = { verdict: v, qui }
    }
  }
  return meilleur
}

export function reglesPersonnes(faits: FaitsRegles, docs: DocumentLu[], personnesDuBien: PersonneDuBien[], affaires: AffaireRegle[], aujourdhui: Date): Alerte[] {
  const alertes: Alerte[] = []
  const pieces = docs.filter((d) => d.lecture.typeCode === 'justif.identite' && d.lecture.etat === 'lu').flatMap((d) => piecesLuesDe(d.nom, d.lecture))
  if (!pieces.length) return alertes
  const vivantes = affaires.filter((a) => !['refused', 'cancelled'].includes(String(a.state ?? '')))
  const acquereurs = vivantes.filter((a) => a.kind === 'compromis' || a.kind === 'offre').flatMap((a) => a.acquereurs ?? [])
  const tous = [...personnesDuBien, ...acquereurs]

  // P4 -- le nom : la pièce d'une personne inconnue (alerte) ; une écriture différente (information, rien ne s'écrit).
  // UNE LIGNE PAR PERSONNE, pas par pièce : la même carte déposée deux fois, ou carte + passeport, ne répète pas la ligne
  // (vu en réel sur 63331 le 14/11) ; le nombre de pièces est dit à la fin.
  const groupesP4 = new Map<string, { p: PieceLue; verdict: Verdict; qui: PersonneDuBien | null; n: number }>()
  for (const p of pieces) {
    const { verdict, qui } = correspondance(p, tous)
    if (verdict !== 'different' && !(verdict === 'proche' && qui)) continue
    const cle = `${verdict}|${normaliserTexte(nomDe(p))}|${qui ? normaliserTexte(nomFiche(qui)) : ''}`
    const g = groupesP4.get(cle)
    if (g) g.n++
    else groupesP4.set(cle, { p, verdict, qui, n: 1 })
  }
  for (const { p, verdict, qui, n } of groupesP4.values()) {
    const combien = n > 1 ? ` (${n} pièces)` : ''
    const surPiece = `${p.prenoms} ${p.nom}${p.nomUsage ? ` (nom d'usage ${p.nomUsage})` : ''}`
    if (verdict === 'different') {
      alertes.push({ code: 'P4', niveau: 'alerte', texte: `La pièce d'identité de ${nomDe(p)} n'est ni à un mandant ni à un acquéreur du bien${combien}`, pourquoi: 'document d\'une autre affaire, ou fiche incomplète' })
    } else if (qui) {
      alertes.push({ code: 'P4', niveau: 'info', texte: `La pièce dit « ${surPiece} », la fiche « ${nomFiche(qui)} »${combien}`, pourquoi: 'nom ou prénom écrit autrement (rien n\'est corrigé seul)' })
    }
  }

  // P5 -- la pièce périmée au jour de la signature : le compromis vivant le plus récent, sinon la signature du mandat
  // (lue au mandat, sinon le début du mandat de la fiche), sinon aujourd'hui.
  const compromis = vivantes.filter((a) => a.kind === 'compromis').map((a) => lireDateIso(a.date)).filter((x): x is Date => Boolean(x))
  const mandatLu = docs.filter((d) => d.lecture.typeCode === 'mandat.vente' && d.lecture.etat === 'lu').map((d) => lireDateIso(dateLue(d.lecture.valeurs, 'date_signature'))).filter((x): x is Date => Boolean(x))
  const signatureMandat = mandatLu.length ? new Date(Math.max(...mandatLu.map((x) => x.getTime()))) : lireDateIso(faits.mandatDebut)
  const reference = compromis.length
    ? { date: new Date(Math.max(...compromis.map((x) => x.getTime()))), quand: 'au compromis' }
    : signatureMandat ? { date: signatureMandat, quand: 'à la signature du mandat' } : { date: aujourdhui, quand: 'aujourd\'hui' }
  const avantCompromis = !compromis.length && momentDuDossier(faits) !== 'compromis'
  // PAR PERSONNE, pas par pièce (14/11) : une personne est en règle si UNE de ses pièces l'est -- un vieux passeport périmé
  // ne sonne pas à côté d'une carte valide ; la même carte déposée deux fois ne sonne qu'une fois. C'est la pièce qui va
  // le plus loin qui parle, et le nombre de pièces est dit à la fin.
  const parPersonne = new Map<string, { p: PieceLue; fin: { date: Date; prolongee: boolean }; n: number }>()
  for (const p of pieces) {
    const fin = finEffective(p)
    if (!fin) continue
    const cle = normaliserTexte(nomDe(p))
    const g = parPersonne.get(cle)
    if (!g) parPersonne.set(cle, { p, fin, n: 1 })
    else parPersonne.set(cle, fin.date > g.fin.date ? { p, fin, n: g.n + 1 } : { ...g, n: g.n + 1 })
  }
  for (const { p, fin, n } of parPersonne.values()) {
    const combien = n > 1 ? ` (${n} pièces, aucune valable)` : ''
    const jusque = `valable jusqu'au ${jjmmaaaa(fin.date)}${fin.prolongee ? ' (carte prolongée de 5 ans)' : ''}${p.finIncertaine ? ' (date lue avec doute)' : ''}`
    if (fin.date < reference.date) {
      alertes.push({ code: 'P5', niveau: 'alerte', texte: `${laPiece(p)} de ${nomDe(p)} était ${perime(p)} ${reference.quand} du ${jjmmaaaa(reference.date)} (${jusque})${combien}`, pourquoi: 'une pièce en cours de validité est exigée (lutte anti-blanchiment)', typeADeposer: 'justif.identite' })
    } else if (avantCompromis && fin.date < aujourdhui) {
      alertes.push({ code: 'P5', niveau: 'info', texte: `${laPiece(p)} de ${nomDe(p)} est ${perime(p)} depuis le ${jjmmaaaa(fin.date)}${combien}`, pourquoi: 'en demander une à jour avant le compromis', typeADeposer: 'justif.identite' })
    }
  }

  // P6 -- une pièce par personne : chaque mandant de la fiche, et chaque acquéreur d'un compromis vivant. Ne parle que si
  // une pièce au moins a été LUE sur ce bien (sinon les cartes déposées avant l'outil, jamais lues, feraient crier).
  const attendues = [...personnesDuBien, ...vivantes.filter((a) => a.kind === 'compromis').flatMap((a) => a.acquereurs ?? [])]
  const vues = new Set<string>()
  for (const qui of attendues) {
    const cle = normaliserTexte(`${qui.prenom} ${qui.nom}`)
    if (!cle || vues.has(cle)) continue
    vues.add(cle)
    // couverte : nom ET prénom (« egal ») ; « proche » seulement si la fiche n'a pas de prénom -- sinon, dans un couple,
    // la pièce de Marc FICTIF « couvrirait » Jeanne FICTIF par le seul nom (trouvé par les essais du 13/11)
    const couverte = pieces.some((p) => { const v = correspondance(p, [qui]).verdict; return v === 'egal' || (v === 'proche' && !qui.prenom.trim()) })
    if (!couverte) {
      alertes.push({ code: 'P6', niveau: 'piece', texte: `Pièce d'identité de ${nomFiche(qui)} : non trouvée parmi les pièces lues`, pourquoi: 'une pièce par mandant (et par acquéreur au compromis)', typeADeposer: 'justif.identite' })
    }
  }
  return alertes
}
