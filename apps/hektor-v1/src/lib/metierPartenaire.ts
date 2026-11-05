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
