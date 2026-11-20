// GED (16/11/2026, morceau 10) -- LA MESURE : juger chaque ligne « À regarder » (vrai / faux / déjà su) pendant deux
// semaines, puis décider règle par règle (garder, resserrer, retirer). Fonctions pures : essais hors ligne dans
// test_ged_mesure.cjs. L'écriture passe par app_ged_juger (lib/ged.ts), derrière `ged_propositions`.
// Note du chantier : notice/CHANTIER_GED_DOCUMENTS_2026-11-06.md §12.20.
import { normaliserTexte } from './gedComparer'
import type { Alerte } from './gedRegles'

// Visuel V3, morceau 4 (20/11/2026) : la période de test est RETIRÉE (décision de Frédéric) -- l'écran n'offre plus
// « Vrai / Faux / Déjà su ». Un point d'attention s'écarte par « Masquer » (verdict `masque`), POUR TOUT LE MONDE sur le
// bien, et revient par « Réafficher » (`reaffiche`) ; le plus récent fait foi (patch_ged_masquer_2026-11-20). Les trois
// anciens verdicts restent lisibles (8 jugements du 17-19/11) : ils ne masquent rien.
export type VerdictGed = 'vrai' | 'faux' | 'deja_su' | 'masque' | 'reaffiche'
export const VERDICTS: Array<{ code: VerdictGed; libelle: string }> = [
  { code: 'vrai', libelle: 'Vrai' }, { code: 'faux', libelle: 'Faux' }, { code: 'deja_su', libelle: 'Déjà su' },
]
export const LIBELLE_VERDICT: Record<VerdictGed, string> = { vrai: 'vrai', faux: 'faux', deja_su: 'déjà su', masque: 'masqué', reaffiche: 'réaffiché' }
// Une ligne est MASQUÉE si et seulement si son dernier mot est « masque ».
export const estMasquee = (verdict: VerdictGed | null | undefined): boolean => verdict === 'masque'

// La CLÉ d'une ligne : la règle et son texte, sans casse, accents ni ponctuation. Une ligne dont le texte change (une
// date, un nombre de pièces) est une AUTRE ligne : elle se rejuge -- on mesure ce que l'écran a dit, pas la règle en l'air.
export function cleJugement(a: Pick<Alerte, 'code' | 'texte'>): string {
  return `${a.code}|${normaliserTexte(a.texte)}`
}
