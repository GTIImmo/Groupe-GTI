// GED (13/11/2026, morceau 9, lot 9b) -- LES RÈGLES DES PIÈCES D'IDENTITÉ LUES : P4 le nom (la pièce face à la fiche),
// P5 la pièce périmée au jour de la signature, P6 une pièce par personne. Fonction pure : essais hors ligne dans
// test_ged_regles_personnes.cjs. Affichées avec les autres règles sous « À regarder », derrière `ged_propositions`.
// On SIGNALE, on n'écrit rien. Le numéro de la pièce n'est jamais là (il est au registre, côté serveur) : seuls le nom,
// les prénoms, la naissance et la fin de validité servent. La ligne « Pièce d'identité de chaque mandant » de « Reçu /
// Manque » (gedPieces.ts) RESTE : elle reconnaît aussi les anciens documents par leur nom (décision du 13/11).
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.19.
import { dateLue, lireDateIso, motsDe, normaliserTexte, personneSurLaFiche, type PersonneDuBien, type Verdict } from './gedComparer'
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

// P6 (19/11) -- UNE PIÈCE COUVRE UNE SEULE PERSONNE : celle qui lui ressemble LE MIEUX parmi toutes les personnes du bien
// (mandants et acquéreurs vivants). Avant, une personne était couverte dès qu'UNE pièce lui ressemblait : la carte de
// « Jean MARTIN » couvrait aussi « Jean MARTIN DUPONT » (même prénom, un mot du nom commun), et le second n'était jamais
// réclamé (vu en réel sur 63331 avec les noms d'essai, le mot « ESSAI »). Peut couvrir : « egal », ou « proche » si la fiche
// n'a pas de prénom (essais du 13/11). Départage : le verdict, puis la part du nom en commun (nom de naissance ou d'usage),
// puis le premier prénom. ÉGALITÉ PARFAITE entre deux personnes : la pièce ne couvre NI l'une NI l'autre -- on ne sait
// pas à qui elle est, et une pièce manquante se réclame plutôt que de se taire (lutte anti-blanchiment). SAUF si chacune
// porte EXACTEMENT un nom de la pièce (naissance ou usage) : c'est la même personne inscrite sous ses deux noms.
const partDuNom = (a: string, b: string) => {
  const x = new Set(motsDe(a)), y = new Set(motsDe(b))
  const communs = [...x].filter((m) => y.has(m)).length
  return x.size + y.size ? communs / new Set([...x, ...y]).size : 0
}
function scoreCouverture(p: PieceLue, qui: PersonneDuBien): number[] | null {
  const v = correspondance(p, [qui]).verdict
  if (!(v === 'egal' || (v === 'proche' && !qui.prenom.trim()))) return null
  const part = Math.max(...[p.nom, p.nomUsage].filter(Boolean).map((n) => partDuNom(n, qui.nom)))
  const prenom = motsDe(p.prenoms)[0] && motsDe(p.prenoms)[0] === motsDe(qui.prenom)[0] ? 1 : 0
  return [RANG[v], part, prenom]
}
const compare = (a: number[], b: number[]) => { for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] - b[i]; return 0 }
const clePersonne = (qui: PersonneDuBien) => normaliserTexte(`${qui.prenom} ${qui.nom}`)
// Les personnes (clés) que chaque pièce couvre : sa meilleure, seule.
export function personnesCouvertes(pieces: PieceLue[], personnes: PersonneDuBien[]): Set<string> {
  const uniques = [...new Map(personnes.filter((q) => clePersonne(q)).map((q) => [clePersonne(q), q])).values()]
  const couvertes = new Set<string>()
  for (const p of pieces) {
    let meilleur: number[] | null = null
    let qui: string[] = []
    for (const q of uniques) {
      const s = scoreCouverture(p, q)
      if (!s) continue
      const c = meilleur ? compare(s, meilleur) : 1
      if (c > 0) { meilleur = s; qui = [clePersonne(q)] } else if (c === 0) qui.push(clePersonne(q))
    }
    if (qui.length === 1 || (meilleur && meilleur[1] === 1)) qui.forEach((c) => couvertes.add(c))
  }
  return couvertes
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
  // couverte : par une pièce dont elle est LA meilleure correspondance (voir personnesCouvertes) -- la pièce de Marc FICTIF
  // ne couvre pas Jeanne FICTIF (13/11), celle de Jean MARTIN ne couvre pas Jean MARTIN DUPONT (19/11)
  const couvertes = personnesCouvertes(pieces, tous)
  const vues = new Set<string>()
  for (const qui of attendues) {
    const cle = clePersonne(qui)
    if (!cle || vues.has(cle)) continue
    vues.add(cle)
    if (!couvertes.has(cle)) {
      alertes.push({ code: 'P6', niveau: 'piece', texte: `Pièce d'identité de ${nomFiche(qui)} : non trouvée parmi les pièces lues`, pourquoi: 'une pièce par mandant (et par acquéreur au compromis)', typeADeposer: 'justif.identite' })
    }
  }
  return alertes
}
