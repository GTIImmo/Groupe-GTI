// GED (16/11/2026, morceau 9, lot 9d) -- LES RÈGLES DU FINANCEMENT : P7 le prêt à la date limite du compromis lu (et la
// pièce manquante à 7 jours, FIN-1 du catalogue), P8 l'emprunteur est l'acquéreur. Fonction pure : essais hors ligne dans
// test_ged_regles_financement.cjs. Affichées avec les autres règles sous « À regarder », derrière `ged_propositions`.
// On SIGNALE, on n'écrit rien. D'une pièce de financement lue on ne connaît QUE sa nature, sa date et ses emprunteurs
// (1re page seule, redit par le serveur) : jamais un montant, un taux, une banque, l'assurance.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md, audit du lot 9d.
import { dateLue, joursEntre, lireDateIso, nombreLu, normaliserTexte, personneSurLaFiche, personnesLuesDe, resoudreCible, texteLu, type PersonneLue } from './gedComparer'
import { typeDuDocument } from './gedPieces'
import type { AffaireRegle, Alerte, DocumentRegle } from './gedRegles'
import type { DocumentLu } from './gedReglesLues'

// Une pièce de financement lue NETTEMENT : une nature incertaine compte comme inconnue (null).
export type FinancementLu = { doc: string; nature: string | null; date: Date | null; emprunteurs: PersonneLue[] }

export function financementsLusDe(docs: DocumentLu[]): FinancementLu[] {
  return docs.filter((d) => d.lecture.typeCode === 'transaction.financement' && d.lecture.etat === 'lu').map((d) => ({
    doc: d.nom,
    nature: texteLu(d.lecture.valeurs, 'nature'),
    date: lireDateIso(dateLue(d.lecture.valeurs, 'date_document')),
    emprunteurs: personnesLuesDe(d.lecture),
  }))
}

const ACCORDS = new Set(['offre_de_pret', 'accord_de_principe'])
const jjmmaaaa = (d: Date) => `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
const nomDe = (p: PersonneLue) => [p.prenoms.split(/[, ]+/)[0], p.nom].filter(Boolean).join(' ')

export function reglesFinancement(documents: DocumentRegle[], docs: DocumentLu[], affaires: AffaireRegle[], aujourdhui: Date): Alerte[] {
  const alertes: Alerte[] = []
  // Rien sans un compromis VIVANT : un financement n'a de sens que pour une vente en cours.
  const vivants = affaires.filter((a) => a.kind === 'compromis' && !['refused', 'cancelled'].includes(String(a.state ?? '')))
  if (!vivants.length) return alertes
  const financements = financementsLusDe(docs)

  // Le compromis LU le plus récent qui porte une condition de prêt, rattaché à UNE ligne vivante (sinon : silence).
  const avecPret = docs.filter((d) => d.lecture.typeCode === 'transaction.avant_contrat' && d.lecture.etat === 'lu' && texteLu(d.lecture.valeurs, 'condition_pret') === 'oui')
  const cpv = avecPret.length ? avecPret.reduce((a, b) => ((lireDateIso(dateLue(b.lecture.valeurs, 'date_signature'))?.getTime() ?? 0) > (lireDateIso(dateLue(a.lecture.valeurs, 'date_signature'))?.getTime() ?? 0) ? b : a)) : null
  const acquereursLus = cpv ? personnesLuesDe(cpv.lecture).filter((p) => p.qualite === 'acquereur') : []
  const ligne = cpv ? resoudreCible(vivants, { acquereurs: acquereursLus, date: dateLue(cpv.lecture.valeurs, 'date_signature'), montant: nombreLu(cpv.lecture.valeurs, 'prix') }) : null
  const limite = ligne && cpv ? lireDateIso(dateLue(cpv.lecture.valeurs, 'date_limite_pret')) : null

  // P7 -- le prêt à la date limite.
  const refus = financements.filter((f) => f.nature === 'refus')
  for (const f of refus) {
    alertes.push({ code: 'P7', niveau: 'alerte', texte: `Refus de prêt lu${f.date ? ` (du ${jjmmaaaa(f.date)})` : ''} : la condition suspensive d'obtention du prêt peut jouer`, pourquoi: 'prévenir le vendeur et le notaire ; vérifier le délai prévu au compromis' })
  }
  if (limite) {
    // les pièces de financement du dossier, lues ou non (un ancien document se reconnaît à son nom)
    const presentes = documents.filter((d) => typeDuDocument(d) === 'transaction.financement').length
    const nonLues = Math.max(0, presentes - financements.length)
    const dans = joursEntre(aujourdhui, limite)
    const passee = dans < 0
    const accords = financements.filter((f) => f.nature != null && ACCORDS.has(f.nature))
    if (!presentes && !financements.length && dans <= 7) {
      // FIN-1 (catalogue V1), sans lecture : 7 jours avant la date limite, aucune pièce de financement au dossier
      alertes.push({ code: 'P7', niveau: passee ? 'alerte' : 'piece', texte: passee ? `La date limite du prêt (${jjmmaaaa(limite)}) est passée : aucune pièce de financement au dossier` : `Date limite du prêt le ${jjmmaaaa(limite)}${dans === 0 ? " (aujourd'hui)" : ` (dans ${dans} jour${dans > 1 ? 's' : ''})`} : aucune pièce de financement au dossier`, pourquoi: 'une offre ou un accord de prêt avant la date limite du compromis', typeADeposer: 'transaction.financement' })
    } else if (passee && !refus.length && financements.length) {
      if (!accords.length) {
        // une pièce non lue peut être l'offre : on le dit, plus bas (information, pas alerte)
        alertes.push({ code: 'P7', niveau: nonLues ? 'info' : 'alerte', texte: `La date limite du prêt (${jjmmaaaa(limite)}) est passée : aucune offre ni accord de prêt lu${nonLues ? ` (${nonLues} pièce${nonLues > 1 ? 's' : ''} de financement non lue${nonLues > 1 ? 's' : ''})` : ''}`, pourquoi: 'condition suspensive : prêt obtenu, prorogée par avenant, ou à lever' })
      } else if (accords.every((f) => f.date && f.date > limite)) {
        // un accord daté APRÈS la date limite ; un accord sans date lue fait taire la règle (on ne sait pas)
        const premier = new Date(Math.min(...accords.map((f) => (f.date as Date).getTime())))
        alertes.push({ code: 'P7', niveau: 'info', texte: `L'accord de prêt lu est daté du ${jjmmaaaa(premier)}, après la date limite du ${jjmmaaaa(limite)}`, pourquoi: 'la condition a-t-elle été prorogée (avenant au compromis) ?' })
      }
    }
  }
  if (financements.length && financements.every((f) => f.nature === 'simulation') && !(limite && joursEntre(aujourdhui, limite) < 0)) {
    alertes.push({ code: 'P7', niveau: 'info', texte: 'Seule une simulation de prêt est au dossier : ce n\'est pas un accord de la banque', pourquoi: 'demander l\'offre ou l\'accord de principe avant la date limite' })
  }

  // P8 -- l'emprunteur est-il un acquéreur ? Les acquéreurs des compromis vivants (registre) et ceux du compromis lu.
  // Une pièce dont AUCUN emprunteur n'est acquéreur sonne ; une ligne par groupe d'emprunteurs (même pièce déposée deux fois).
  const acquereurs = [...vivants.flatMap((a) => a.acquereurs ?? []), ...acquereursLus.map((p) => ({ nom: p.nom, prenom: p.prenoms }))]
  if (acquereurs.length) {
    const vus = new Map<string, { f: FinancementLu; n: number }>()
    for (const f of financements) {
      if (!f.emprunteurs.length || !f.emprunteurs.every((e) => personneSurLaFiche(e, acquereurs) === 'different')) continue
      const cle = f.emprunteurs.map((e) => normaliserTexte(nomDe(e))).sort().join('|')
      const g = vus.get(cle)
      if (g) g.n++
      else vus.set(cle, { f, n: 1 })
    }
    for (const { f, n } of vus.values()) {
      alertes.push({ code: 'P8', niveau: 'alerte', texte: `La pièce de financement de ${f.emprunteurs.map(nomDe).join(' et ')} n'est au nom d'aucun acquéreur du compromis${n > 1 ? ` (${n} pièces)` : ''}`, pourquoi: 'document d\'une autre affaire, ou acquéreur manquant au registre' })
    }
  }
  return alertes
}
