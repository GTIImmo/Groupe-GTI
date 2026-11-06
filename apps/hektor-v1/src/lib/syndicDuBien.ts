// CHANTIER PARTENAIRES · LOT 4, PIÈCE 4.2 (06/11/2026) — LE SYNDIC D'UN BIEN, CHOISI CHEZ NOUS. Règles pures (aucun import).
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §27.3 (audit) et §27.4.
// Le lien vit dans `app_partenaire_lien` (role 'syndic', objet 'bien') ; rien n'est écrit chez Hektor (décision D2, 04/11).
// Ce que Hektor indique (`diagnostics_contacts_console_json` → syndic) est seulement LU, pour signaler un écart.

export type SyndicDuBien = {
  id: number
  partenaireId: string
  origine: 'app' | 'hektor' | 'netty' | string
  poseLe: string | null
  posePar: string | null
  nom: string
  ville: string | null
  telephone: string | null
  email: string | null
}

export type SyndicCatalogue = { id: string; nom: string; ville: string | null }

const texte = (v: unknown) => String(v ?? '').trim()

// Le retour de `app_partenaire_syndic_du_bien_lire` (null = pas de syndic).
export function lireSyndicDuBien(brut: unknown): SyndicDuBien | null {
  if (!brut || typeof brut !== 'object') return null
  const b = brut as Record<string, unknown>
  const id = Number(b.id)
  if (!Number.isFinite(id) || !texte(b.partenaire_id)) return null
  return {
    id,
    partenaireId: texte(b.partenaire_id),
    origine: texte(b.origine) || 'app',
    poseLe: texte(b.pose_le) || null,
    posePar: texte(b.pose_par) || null,
    nom: texte(b.nom) || `Contact ${texte(b.partenaire_id)}`,
    ville: texte(b.ville) || null,
    telephone: texte(b.telephone) || null,
    email: texte(b.email) || null,
  }
}

// Le syndic que HEKTOR indique sur la fiche du bien (lu la nuit), ou null.
export function syndicSelonHektor(detailDiagnostics: unknown): { numero: string; nom: string } | null {
  let o: unknown = detailDiagnostics
  if (typeof o === 'string') {
    if (!o.trim().startsWith('{')) return null
    try { o = JSON.parse(o) } catch { return null }
  }
  if (!o || typeof o !== 'object') return null
  const s = (o as Record<string, unknown>).syndic as Record<string, unknown> | undefined
  const numero = texte(s?.value)
  const nom = texte(s?.selected_label)
  return numero ? { numero, nom: nom || `Contact ${numero}` } : null
}

// Comparer deux noms de société : sans accents, sans ponctuation, sans les mots vides.
const VIDES = new Set(['le', 'la', 'les', 'de', 'des', 'du', 'et', 'sas', 'sarl', 'sa', 'eurl', 'sci', 'cabinet', 'syndic', 'immobilier', 'immobiliere', 'agence', 'gestion'])
export function motsDuNom(nom: string): string[] {
  return texte(nom).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ')
    .split(' ').filter((m) => m.length > 1 && !VIDES.has(m))
}
export function memeSociete(a: string, b: string): boolean {
  const ma = motsDuNom(a), mb = motsDuNom(b)
  if (!ma.length || !mb.length) return false
  const [petit, grand] = ma.length <= mb.length ? [ma, new Set(mb)] : [mb, new Set(ma)]
  return petit.every((m) => grand.has(m))
}

// L'écart avec Hektor : Hektor indique un syndic, et ce n'est pas le nôtre (comparé par le nom). Jamais écrasé : montré.
export function ecartAvecHektor(nous: SyndicDuBien | null, hektor: { nom: string } | null): string | null {
  if (!hektor) return null
  if (!nous) return hektor.nom
  return memeSociete(nous.nom, hektor.nom) ? null : hektor.nom
}

// La liste du sélecteur : les syndics du catalogue, filtrés par la recherche ; en tête ceux que proposent le registre
// des copropriétés (RNIC) et Hektor, quand leur nom correspond. Le syndic actuel est retiré de la liste.
export type ChoixSyndic = SyndicCatalogue & { propose: 'rnic' | 'hektor' | null }
export function choixSyndics(input: {
  catalogue: SyndicCatalogue[]
  recherche: string
  actuel: string | null
  nomRnic: string | null
  nomHektor: string | null
  limite?: number
}): ChoixSyndic[] {
  const q = motsDuNom(input.recherche)
  const liste: ChoixSyndic[] = []
  for (const s of input.catalogue) {
    if (s.id === input.actuel) continue
    const mots = motsDuNom(`${s.nom} ${s.ville ?? ''}`)
    if (q.length && !q.every((m) => mots.some((x) => x.startsWith(m)))) continue
    const propose = input.nomRnic && memeSociete(s.nom, input.nomRnic) ? 'rnic'
      : input.nomHektor && memeSociete(s.nom, input.nomHektor) ? 'hektor' : null
    liste.push({ ...s, propose })
  }
  const rang = (c: ChoixSyndic) => (c.propose === 'rnic' ? 0 : c.propose === 'hektor' ? 1 : 2)
  liste.sort((a, z) => rang(a) - rang(z) || a.nom.localeCompare(z.nom, 'fr'))
  return liste.slice(0, input.limite ?? 40)
}

// « choisi dans l'app par X le 06/11/2026 » / « repris de Hektor ».
export function origineDuSyndic(s: SyndicDuBien): string {
  const date = s.poseLe ? new Date(s.poseLe) : null
  const quand = date && !Number.isNaN(date.getTime()) ? ` le ${date.toLocaleDateString('fr-FR')}` : ''
  if (s.origine === 'hektor') return `repris de Hektor${quand}`
  if (s.origine === 'netty') return `repris de Netty${quand}`
  return `choisi dans l'app${s.posePar ? ` par ${s.posePar}` : ''}${quand}`
}
