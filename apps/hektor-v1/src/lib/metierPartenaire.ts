// CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.1 (05/11/2026) — LE MÉTIER D'UN PARTENAIRE, ET D'OÙ IL VIENT.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §24 ; maquette maquettes/fiche-partenaire-v1.html (bloc « Métier »).
// Les règles d'affichage, en fonctions pures (aucun import) : essayées par test_metier_partenaire.cjs.
// Le registre (`app_partenaire_metier`) range un métier par ligne, avec sa SOURCE : netty (l'ancien logiciel), hektor (son
// formulaire ou les listes syndic / diagnostiqueur), transactions (la table des parties), ecran (saisi dans l'app).

export type LigneMetier = { metier: string; source: string; ecrit_le?: string | null; confirme_le?: string | null }

export const LIBELLE_METIER: Record<string, string> = {
  notaire: 'Notaire', syndic: 'Syndic', diagnostiqueur: 'Diagnostiqueur', courtier: 'Courtier', banque: 'Banque',
  apporteur: 'Apporteur', parrain: 'Parrain', administration: 'Administration', societe: 'Société',
  agent_immobilier: 'Agent immobilier', mandataire: 'Mandataire', promoteur: 'Promoteur',
  marchand_de_biens: 'Marchand de biens', investisseur: 'Investisseur', avocat: 'Avocat', huissier: 'Huissier',
  technicien: 'Technicien', autre: 'Autre',
}

// PIÈCE 3.2 (05/11/2026) — la fenêtre « Métier du contact » (maquette maquettes/fenetre-metier-v1.html).
// L'ordre des pastilles : les six métiers du chantier d'abord (marqués `premier`), puis les autres.
const PREMIERS = ['syndic', 'diagnostiqueur', 'courtier', 'banque', 'apporteur', 'parrain']
export const METIERS_ORDONNES: { metier: string; libelle: string; premier: boolean }[] = [
  ...PREMIERS,
  'notaire', 'agent_immobilier', 'mandataire', 'promoteur', 'marchand_de_biens', 'investisseur', 'administration',
  'societe', 'avocat', 'huissier', 'technicien', 'autre',
].map((metier) => ({ metier, libelle: LIBELLE_METIER[metier], premier: PREMIERS.includes(metier) }))

// Ce que « Enregistrer » envoie, dans l'ordre : les RETRAITS d'abord (un métier retiré puis rajouté dans la même fenêtre
// n'a pas de sens : on l'ignore), puis les AJOUTS. Seuls les métiers réellement actifs peuvent être retirés ; un métier
// déjà actif n'est pas « ajouté ». Une liste vide = rien à envoyer.
export function planDesChangements(actifs: string[], retraits: Iterable<string>, ajouts: Iterable<string>): { metier: string; retirer: boolean }[] {
  const actuels = new Set(actifs)
  const connus = new Set(METIERS_ORDONNES.map((m) => m.metier))
  const aRetirer = [...new Set(retraits)].filter((m) => actuels.has(m))
  const aAjouter = [...new Set(ajouts)].filter((m) => connus.has(m) && !actuels.has(m))
  return [...aRetirer.map((metier) => ({ metier, retirer: true })), ...aAjouter.map((metier) => ({ metier, retirer: false }))]
}

// PIÈCE 3.3a (05/11/2026) — le volet de la FICHE PARTENAIRE (maquette fiche-partenaire-v1).
// Une fiche devient « partenaire » quand le contact a un métier actif AUTRE que notaire (le notaire a sa fiche, 28/10).
// Le métier principal = le premier dans l'ordre de METIERS_ORDONNES ; il donne la couleur (famille), l'icône et l'action
// propre au métier (bouton magenta, « en construction » jusqu'aux lots 4 à 7). Une famille sans action = pas de bouton.
export type FamillePartenaire = 'courtier' | 'diag' | 'syndic' | 'apporteur' | 'autre'
export type ProfilPartenaire = { metier: string; famille: FamillePartenaire; action: string | null; lot: string | null; libelles: string[] }

const FAMILLE: Record<string, FamillePartenaire> = {
  courtier: 'courtier', banque: 'courtier', diagnostiqueur: 'diag', syndic: 'syndic', apporteur: 'apporteur', parrain: 'apporteur',
}
const ACTION: Record<Exclude<FamillePartenaire, 'autre'>, [string, string]> = {
  syndic: ['Demander un document', 'lot 4'],
  diag: ['Commander un diagnostic', 'lot 5'],
  courtier: ['Orienter un acquéreur', 'lots 6 et 7'],
  apporteur: ['Noter une affaire apportée', 'lots 6 et 7'],
}

export function profilDuPartenaire(lignes: LigneMetier[] | null | undefined): ProfilPartenaire | null {
  const actifs = new Set((lignes ?? []).map((l) => l?.metier).filter((m): m is string => Boolean(m) && m !== 'notaire'))
  if (!actifs.size) return null
  const ordonnes = METIERS_ORDONNES.filter((m) => actifs.has(m.metier))
  const inconnus = [...actifs].filter((m) => !METIERS_ORDONNES.some((o) => o.metier === m)).sort()
  const metier = ordonnes[0]?.metier ?? inconnus[0]
  const famille = FAMILLE[metier] ?? 'autre'
  const [action, lot] = famille === 'autre' ? [null, null] : ACTION[famille]
  const libelles = [...ordonnes.map((m) => m.libelle), ...inconnus.map((m) => majuscule(m.replace(/_/g, ' ')))]
  return { metier, famille, action, lot, libelles }
}

const dateCourte = (v: string | null | undefined) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(v ?? '').trim())
  return m ? `${m[3]}/${m[2]}/${m[1]}` : null
}

export function origineDuMetier(ligne: LigneMetier): string {
  switch (ligne.source) {
    case 'netty': return "d'après l'ancien logiciel (Netty)"
    case 'hektor': return "d'après Hektor"
    case 'transactions': return "d'après ses transactions"
    case 'ecran': {
      const le = dateCourte(ligne.confirme_le ?? ligne.ecrit_le)
      return le ? `saisi dans l'app le ${le}` : "saisi dans l'app"
    }
    default: return 'origine inconnue'
  }
}

const majuscule = (texte: string) => texte.charAt(0).toUpperCase() + texte.slice(1)

// Le titre (« Syndic · Diagnostiqueur ») et la phrase d'origine. Aucune ligne = rien à montrer (null).
// Une seule origine pour tous les métiers : dite une fois ; sinon, métier par métier.
export function resumerMetiers(lignes: LigneMetier[] | null | undefined): { titre: string; origine: string } | null {
  const vues = new Set<string>()
  const gardees = (lignes ?? [])
    .filter((l) => l && typeof l.metier === 'string' && l.metier.trim())
    .slice()
    .sort((a, b) => String(a.ecrit_le ?? '').localeCompare(String(b.ecrit_le ?? '')) || a.metier.localeCompare(b.metier))
    .filter((l) => (vues.has(l.metier) ? false : (vues.add(l.metier), true)))
  if (!gardees.length) return null
  const nom = (l: LigneMetier) => LIBELLE_METIER[l.metier] ?? majuscule(l.metier.replace(/_/g, ' '))
  const origines = gardees.map(origineDuMetier)
  const origine = new Set(origines).size === 1
    ? majuscule(origines[0])
    : gardees.map((l, i) => `${nom(l)} : ${origines[i]}`).join(' · ')
  return { titre: gardees.map(nom).join(' · '), origine }
}
