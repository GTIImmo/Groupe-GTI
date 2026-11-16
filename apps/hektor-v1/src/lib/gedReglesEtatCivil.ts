// GED (16/11/2026, morceau 9, lot 9d-2) -- LES RÈGLES DE L'ÉTAT CIVIL LU : P9 le conjoint (logement de la famille),
// P10 le décès d'un mandant et la mesure de protection. Fonction pure : essais hors ligne dans
// test_ged_regles_etat_civil.cjs. Affichées avec les autres règles sous « À regarder », derrière `ged_propositions`.
// On SIGNALE, on n'écrit rien. D'une pièce d'état civil lue on ne connaît que sa nature, la date de l'acte et les époux,
// partenaires ou le défunt (1re page seule) ; d'une mesure de protection, SA NATURE SEULE (le serveur jette le reste).
// ⚠ Le PACS ne crie pas : le consentement de l'article 215 du Code civil ne vaut que pour des ÉPOUX.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md, audit du lot 9d.
import { dateLue, lireDateIso, normaliserTexte, personneSurLaFiche, personnesLuesDe, texteLu, type PersonneDuBien, type PersonneLue } from './gedComparer'
import type { Alerte } from './gedRegles'
import type { DocumentLu } from './gedReglesLues'

export type EtatCivilLu = { doc: string; nature: string | null; date: Date | null; personnes: PersonneLue[] }

export function etatsCivilsLusDe(docs: DocumentLu[]): EtatCivilLu[] {
  return docs.filter((d) => d.lecture.typeCode === 'justif.etat_civil' && d.lecture.etat === 'lu').map((d) => ({
    doc: d.nom,
    nature: texteLu(d.lecture.valeurs, 'nature'),
    date: lireDateIso(dateLue(d.lecture.valeurs, 'date_acte')),
    personnes: personnesLuesDe(d.lecture),
  }))
}

const MARIAGES = new Set(['acte_mariage', 'livret_famille', 'contrat_mariage'])
const jjmmaaaa = (d: Date) => `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`
const nomDe = (p: PersonneLue) => [p.prenoms.split(/[, ]+/)[0], p.nom].filter(Boolean).join(' ')
const commeFiche = (p: PersonneLue): PersonneDuBien => ({ nom: p.nom, prenom: p.prenoms })
const meme = (p: PersonneLue, q: PersonneLue) => personneSurLaFiche(p, [commeFiche(q)]) === 'egal'

// `personnesDuBien` : les mandants et propriétaires de la fiche. Les MANDANTS DU MANDAT LU (signataires) s'y ajoutent ici.
export function reglesEtatCivil(docs: DocumentLu[], personnesDuBien: PersonneDuBien[]): Alerte[] {
  const alertes: Alerte[] = []
  const lus = etatsCivilsLusDe(docs)
  if (!lus.length) return alertes
  const signataires = docs.filter((d) => d.lecture.typeCode === 'mandat.vente' && d.lecture.etat === 'lu')
    .flatMap((d) => personnesLuesDe(d.lecture).filter((p) => p.qualite === 'mandant').map(commeFiche))
  const duBien = [...personnesDuBien, ...signataires]
  const deces = lus.filter((e) => e.nature === 'acte_deces')
  const defunts = deces.flatMap((e) => e.personnes.filter((p) => p.qualite === 'defunt' || e.personnes.length === 1).map((p) => ({ p, date: e.date })))
  const divorces = lus.filter((e) => e.nature === 'divorce').flatMap((e) => e.personnes)
  // une fiche sans prénom : on ne sait pas dire « ce n'est pas lui » -> P9 se tait plutôt que crier sur un couple mal rangé
  const ficheSure = duBien.length > 0 && duBien.every((q) => q.prenom.trim())

  // P9 -- le conjoint : un mandant MARIÉ dont l'époux n'est ni sur la fiche ni signataire du mandat lu. Un divorce lu ou
  // un décès lu de l'un d'eux fait taire la règle. Une ligne par couple (le livret et l'acte ne répètent pas).
  if (ficheSure) {
    const vus = new Set<string>()
    for (const m of lus.filter((e) => e.nature != null && MARIAGES.has(e.nature) && e.personnes.length === 2)) {
      for (const [a, b] of [[m.personnes[0], m.personnes[1]], [m.personnes[1], m.personnes[0]]]) {
        if (personneSurLaFiche(a, duBien) !== 'egal' || personneSurLaFiche(b, duBien) === 'egal') continue
        if (divorces.some((x) => meme(x, a) || meme(x, b))) continue
        if (defunts.some(({ p }) => meme(p, b))) continue
        const cle = [normaliserTexte(nomDe(a)), normaliserTexte(nomDe(b))].sort().join('|')
        if (vus.has(cle)) continue
        vus.add(cle)
        alertes.push({ code: 'P9', niveau: 'alerte', texte: `${nomDe(a)} est marié(e)${m.date ? ` depuis le ${jjmmaaaa(m.date)}` : ''} avec ${nomDe(b)}, qui n'est ni sur la fiche ni signataire du mandat`, pourquoi: 'logement de la famille : le conjoint doit consentir à la vente, même s\'il n\'est pas propriétaire (article 215 du Code civil)' })
      }
    }
  }

  // P10 -- le décès d'un mandant : le mandat prend fin (article 2003 du Code civil). Une ligne par personne.
  const morts = new Set<string>()
  for (const { p, date } of defunts) {
    if (personneSurLaFiche(p, duBien) !== 'egal') continue
    const cle = normaliserTexte(nomDe(p))
    if (morts.has(cle)) continue
    morts.add(cle)
    alertes.push({ code: 'P10', niveau: 'alerte', texte: `${nomDe(p)}, au dossier, est décédé(e)${date ? ` le ${jjmmaaaa(date)}` : ''} : un mandat prend fin au décès du mandant`, pourquoi: 'article 2003 du Code civil : reprendre avec les héritiers ou le notaire chargé de la succession' })
  }

  // P10 -- une mesure de protection au dossier (on n'en connaît QUE la nature : ni la personne, ni le représentant).
  const protections = lus.filter((e) => e.nature === 'protection').length
  if (protections) {
    alertes.push({ code: 'P10', niveau: 'alerte', texte: `Une mesure de protection juridique est au dossier${protections > 1 ? ` (${protections} pièces)` : ''}`, pourquoi: 'qui signe : le tuteur ou le curateur, avec l\'autorisation du juge des tutelles pour une tutelle' })
  }
  return alertes
}
