// ═══════════════════════════════════════════════════════════════════════════════
// LA RÉPARTITION EFFECTIVE D'UN DOSSIER -- la règle de CALCUL        04/11/2026
// ═══════════════════════════════════════════════════════════════════════════════
//
// Décision de Frédéric (04/11) : « corrige le mode de calcul, on corrigera la répartition des honoraires avec le
// sheet dans le chantier dédié ». La SAISIE n'est pas touchée : cette règle ne sert qu'à COMPTER, et le pilotage
// comme le registre des transactions la prennent ici, une seule fois. Audit : AUDIT_REGISTRE_NEGOCIATEURS §20-21.
//
//   1. aucune ligne                      -> 100 % au négociateur du MANDAT (le négociateur du bien) ;
//   2. lignes toutes à 0 %               -> 50 % entrée / 50 % sortie aux négociateurs inscrits ;
//   3. un seul côté saisi (l'autre vide ou à 0 %) -> l'autre côté prend les MÊMES négociateurs ;
//   4. total différent de 100 %          -> ramené à 100 %, dans la même proportion (25 + 25 -> 50 + 50).
//
// Mesuré le 04/11 sur les ventes 2026 : 274 dossiers sur 286 font déjà 100 % (inchangés), 12 tombent dans 1 à 4.
import type { RepartitionLigne } from './api'

export type RegleRepartition = 'saisie' | 'ramenee_100' | 'cote_recopie' | 'zero_moitie' | 'mandat_100'

/** Une ligne comptée : la ligne saisie (ou fabriquée par la règle), et la PERSONNE du registre quand elle est connue. */
export type PartEffective = RepartitionLigne & {
  personne: string | null
  /** le nom de la personne au registre (le nom saisi reste dans nomAuMoment) */
  nomRegistre: string | null
  regle: RegleRepartition
}

export type NegoDuMandat = { personne: string | null; nom: string | null } | null

const pct = (x: number) => (Number.isFinite(x) && x > 0 ? x : 0)
const total = (lignes: Array<{ pourcentage: number }>) => lignes.reduce((t, x) => t + pct(x.pourcentage), 0)

export function repartitionEffective(
  lignes: RepartitionLigne[],
  mandat: NegoDuMandat,
  personneDe: (ligne: RepartitionLigne) => { personne: string | null; nom: string | null },
): PartEffective[] {
  // 1. Rien de saisi : tout au négociateur du mandat. Sans négociateur connu, personne (le dossier reste « non réparti »).
  if (!lignes.length) {
    if (!mandat || (!mandat.personne && !mandat.nom)) return []
    return [{ cote: 'entree', rang: 1, hektorUserId: '', nomAuMoment: mandat.nom, pourcentage: 100, origine: 'regle',
      personne: mandat.personne, nomRegistre: mandat.nom, regle: 'mandat_100' }]
  }
  let regle: RegleRepartition = 'saisie'
  let entree = lignes.filter((x) => x.cote === 'entree').map((x) => ({ ...x }))
  let sortie = lignes.filter((x) => x.cote === 'sortie').map((x) => ({ ...x }))
  // 2. Tout à 0 % : chaque côté saisi vaut 50 %, partagé à parts égales entre ses négociateurs.
  if (total(entree) + total(sortie) === 0) {
    regle = 'zero_moitie'
    const moitie = (cote: RepartitionLigne[]) => cote.map((x) => ({ ...x, pourcentage: 50 / cote.length }))
    entree = moitie(entree)
    sortie = moitie(sortie)
  }
  // 3. Un côté vide (ou à 0 %) : il recopie l'autre, mêmes négociateurs, mêmes pourcentages.
  if (total(entree) === 0 && total(sortie) > 0) {
    if (regle === 'saisie') regle = 'cote_recopie'
    entree = sortie.map((x) => ({ ...x, cote: 'entree' as const }))
  } else if (total(sortie) === 0 && total(entree) > 0) {
    if (regle === 'saisie') regle = 'cote_recopie'
    sortie = entree.map((x) => ({ ...x, cote: 'sortie' as const }))
  }
  // 4. Le total ramené à 100 %, dans la même proportion.
  const tout = [...entree, ...sortie]
  const somme = total(tout)
  const facteur = somme > 0 && Math.abs(somme - 100) > 0.01 ? 100 / somme : 1
  if (facteur !== 1 && regle === 'saisie') regle = 'ramenee_100'
  return tout.map((x) => {
    const qui = personneDe(x)
    return { ...x, pourcentage: pct(x.pourcentage) * facteur, personne: qui.personne, nomRegistre: qui.nom, regle }
  })
}

/** La part d'une personne dans un dossier (0 à 1), entrée et sortie confondues. */
export function partDe(parts: Array<{ personne?: string | null; pourcentage: number }>, personne: string): number {
  return parts.reduce((t, x) => t + (x.personne === personne ? x.pourcentage : 0), 0) / 100
}
