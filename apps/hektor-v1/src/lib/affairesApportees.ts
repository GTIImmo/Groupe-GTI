// CHANTIER PARTENAIRES · LOT 7 (09/11/2026) — LES AFFAIRES APPORTÉES : règles pures (aucune lecture, aucune écriture).
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.17. Un client apporté (lien `objet client`, rôle
// apporteur) prend l'étape que notre registre lui donne DÉJÀ (`relation_roles_json` de sa fiche) — rien n'est inventé :
// une vente d'acquéreur, un compromis, une offre, un mandat, un propriétaire sans mandat, sinon « contact apporté ».
// La commission reste « en construction » (H1, plus tard).

export type EtapeApport = 'vente' | 'compromis' | 'offre' | 'mandat' | 'proprietaire' | 'contact'
const ORDRE: [EtapeApport, string, string][] = [
  ['vente', 'acquereur_vente', 'Vente (acquéreur)'],
  ['compromis', 'acquereur_compromis', 'Compromis (acquéreur)'],
  ['offre', 'acquereur_offre', 'Offre (acquéreur)'],
  ['mandat', 'mandant', 'Sous mandat'],
  ['proprietaire', 'proprietaire', 'Propriétaire, sans mandat'],
]
const roles = (v: unknown): string[] => {
  if (Array.isArray(v)) return v.map(String)
  if (typeof v === 'string' && v.trim().startsWith('[')) { try { const a = JSON.parse(v); return Array.isArray(a) ? a.map(String) : [] } catch { return [] } }
  return []
}
export function etapeDuClient(relationRoles: unknown): { etape: EtapeApport; libelle: string } {
  const r = new Set(roles(relationRoles))
  const trouve = ORDRE.find(([, role]) => r.has(role))
  return trouve ? { etape: trouve[0], libelle: trouve[2] } : { etape: 'contact', libelle: 'Contact apporté' }
}

export type ClientApporte = { lienId: number; clientId: string; nom: string; ville: string | null; archive: boolean; poseLe: string | null; etape: EtapeApport; libelle: string }
// Les quatre étapes de la fiche (BLOCS.apporteur) : « Contact apporté » = tous ; « Mandat » = ceux qui sont passés au mandat
// ou plus loin ; « Commission due » et « Réglé » : pas encore de données (null = « en construction »).
export function compterEtapes(liste: ClientApporte[]): Record<'Contact apporté' | 'Mandat' | 'Commission due' | 'Réglé', number | null> {
  return {
    'Contact apporté': liste.length,
    'Mandat': liste.filter((c) => c.etape === 'mandat').length,
    'Commission due': null,
    'Réglé': null,
  }
}
// Les plus avancés d'abord (vente → contact), puis le plus récent.
export function trierApports(liste: ClientApporte[]): ClientApporte[] {
  const rang = (e: EtapeApport) => ORDRE.findIndex(([x]) => x === e) === -1 ? ORDRE.length : ORDRE.findIndex(([x]) => x === e)
  return [...liste].sort((a, z) => rang(a.etape) - rang(z.etape) || String(z.poseLe ?? '').localeCompare(String(a.poseLe ?? '')))
}
