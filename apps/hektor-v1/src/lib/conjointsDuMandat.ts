// A.2 lot 6b P7 (05/11/2026, D32 + D34-D36) -- LE COUPLE DANS L'EDITEUR DU MANDAT. Pur, sans requete
// (essai : test_conjoints_du_mandat.cjs). Proposition §11.2, reponses de Frederic du 05/11 :
//   D34 (a) conjoint nomme ET lie au bien : dans le mandat par defaut ; « Non » le retire du DOCUMENT seulement.
//   D35 (b) conjoint nomme mais NON lie : absent par defaut ; « Oui » le lie au bien comme mandant (geste confirme),
//           puis il est imprime.
//   D36 (c) Youtrust allume : un mandant imprime sans prenom ou sans nom BLOQUE la generation.
//   Place de conjoint vide : on le dit ; le mandant signe seul.
// ⚠ Le conjoint se lit dans `couple_json` (calcule la nuit et a la relecture), jamais devine par le texte.
import { lireCoupleJson, type CoupleJson } from './coupleAffichage'

export type MandantDuDocument = { id: string; civilite: string; prenom: string; nom: string; qualite: string; adresse: string; telephone: string; email: string }
export type FicheCouple = { hektor_target_id: string; nature_fiche: string | null; couple_json: CoupleJson | string | null; civilite_app?: string | null }
export type SituationConjoint =
  | { cas: 'lie'; principal: string; conjoint: string; nomConjoint: string }
  | { cas: 'non_lie'; principal: string; conjoint: string; nomConjoint: string; mandant: MandantDuDocument; archive: boolean }
  | { cas: 'inconnu'; principal: string }
// ⚠ MESURE DU 05/11 (300 couples « nomme ») : `conjoint.id` est NOTRE numero (10 xxx xxx) ; le numero HEKTOR, celui des
//   cartes de l'editeur et de la porte « lier comme mandant », est `conjoint.hektor_id` (300 sur 300, egal a la fiche
//   253 fois sur 253). 24 conjoints sur 300 sont archives.
type ConjointDuJson = { id?: string | number | null; hektor_id?: string | number | null; prenom?: string | null; nom?: string | null; civilite?: string | null; telephone?: string | null; email?: string | null; archive?: unknown }

// Le numero Hektor d'une carte de l'editeur -- MEMES regles que le worker (ficheDuMandantImprime, P1).
export function ficheDuMandant(id: string): string | null {
  const membre = String(id || '').match(/-member-(\d+)$/)
  if (membre) return membre[1]
  const carte = String(id || '').match(/^[a-z-]*contact-\d+-(\d+)$/i)
  return carte ? carte[1] : null
}

const nomDe = (prenom?: string | null, nom?: string | null) => [prenom, nom].map((x) => String(x ?? '').trim()).filter(Boolean).join(' ')

// Une ligne par mandant qui forme un couple. `mandants` = ce que la fiche met dans le mandat (sans les choix).
export function situationsDesConjoints(mandants: MandantDuDocument[], fiches: Map<string, FicheCouple>): SituationConjoint[] {
  const presents = new Set(mandants.map((m) => ficheDuMandant(m.id)).filter((x): x is string => Boolean(x)))
  const vus = new Set<string>()
  const situations: SituationConjoint[] = []
  for (const m of mandants) {
    const principal = ficheDuMandant(m.id)
    if (!principal || vus.has(principal)) continue
    vus.add(principal)
    const fiche = fiches.get(principal)
    // ⛔ Regle de Frederic (02/11) : une fiche est un couple SI ET SEULEMENT SI sa nature le dit ; `couple_json` ne
    //   decide pas (16 052 « personne seule » portent un couple_json « vide », couples anciens).
    if (!fiche || fiche.nature_fiche !== 'couple') continue
    const json = lireCoupleJson(fiche.couple_json)
    if (json?.etat === 'nomme') {
      const cj = (json.conjoint ?? {}) as ConjointDuJson
      const conjoint = String(cj.hektor_id ?? '').trim()
      if (!/^\d+$/.test(conjoint) || conjoint === principal) continue
      const nomConjoint = nomDe(cj.prenom, cj.nom) || `fiche ${conjoint}`
      vus.add(conjoint)
      if (presents.has(conjoint)) {
        situations.push({ cas: 'lie', principal, conjoint, nomConjoint })
      } else {
        const ficheConjoint = fiches.get(conjoint)
        situations.push({
          cas: 'non_lie', principal, conjoint, nomConjoint,
          mandant: {
            // « -member-<n°> » : le worker en deduit le numero de fiche (photo du PDF, P1).
            id: `conjoint-${principal}-member-${conjoint}`,
            civilite: String(ficheConjoint?.civilite_app ?? cj.civilite ?? '').trim(),
            prenom: String(cj.prenom ?? '').trim(),
            nom: String(cj.nom ?? '').trim(),
            qualite: 'Mandant',
            adresse: m.adresse,
            telephone: String(cj.telephone ?? '').trim(),
            email: String(cj.email ?? '').trim(),
          },
          archive: cj.archive === true || ['1', 'true', 'oui'].includes(String(cj.archive ?? '').trim().toLowerCase()),
        })
      }
    } else if (json?.etat === 'vide') {
      situations.push({ cas: 'inconnu', principal })
    }
  }
  return situations
}

// Le mandat tel qu'il sera imprime : sans les conjoints retires (D34), avec les conjoints lies a l'instant (D35),
// chacun juste apres son principal ; jamais deux fois la meme fiche (la fiche relue ensuite le portera deja).
export function mandantsImprimes(mandants: MandantDuDocument[], retires: Set<string>, ajoutes: Map<string, MandantDuDocument>, situations: SituationConjoint[]): MandantDuDocument[] {
  const presents = new Set(mandants.map((m) => ficheDuMandant(m.id)).filter(Boolean) as string[])
  const sortie: MandantDuDocument[] = []
  for (const m of mandants) {
    const fiche = ficheDuMandant(m.id)
    if (fiche && retires.has(fiche)) continue
    sortie.push(m)
    if (!fiche) continue
    for (const s of situations) {
      if (s.cas !== 'non_lie' || s.principal !== fiche) continue
      const ajout = ajoutes.get(s.conjoint)
      if (ajout && !presents.has(s.conjoint) && !retires.has(s.conjoint)) sortie.push(ajout)
    }
  }
  return sortie
}

// D36 : les mandants imprimes sans prenom ou sans nom (Youtrust exige les deux pour chaque signataire).
export function mandantsSansPrenomOuNom(mandants: MandantDuDocument[]): string[] {
  return mandants
    .map((m, i) => ({ m, i }))
    .filter(({ m }) => !String(m.prenom ?? '').trim() || !String(m.nom ?? '').trim())
    .map(({ m, i }) => `mandant ${i + 1} (${[m.civilite, m.prenom, m.nom].map((x) => String(x ?? '').trim()).filter(Boolean).join(' ') || 'sans nom'}) : ${!String(m.nom ?? '').trim() ? 'nom' : 'prénom'} manquant`)
}
