// CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.5 (05/11/2026) — LE CATALOGUE DES MÉTIERS, EN RÈGLES PURES (aucun import).
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §26 ter et §26 quater ; maquette planche 1 (Main.dc.html).
// Règle de Frédéric (05/11) : cinq métiers et c'est tout. Les NOTAIRES = ceux qui ont aujourd'hui la fiche notaire (rôle
// notaire dans la table des parties, règle actuelle) ; les quatre autres viennent du registre `app_partenaire_metier`.
// Essayé par test_metier_partenaire.cjs.

export type TuileCatalogue = 'notaire' | 'syndic' | 'diag' | 'courtier' | 'apporteur'

export const TUILES_CATALOGUE: { tuile: TuileCatalogue; libelle: string; sous: string; couleur: string }[] = [
  { tuile: 'notaire', libelle: 'Notaires', sous: 'actes et dossiers', couleur: '#3b4a8c' },
  { tuile: 'syndic', libelle: 'Syndics', sous: 'copropriétés', couleur: '#5b4a9e' },
  { tuile: 'diag', libelle: 'Diagnostiqueurs', sous: 'DPE et contrôles', couleur: '#b26a0e' },
  { tuile: 'courtier', libelle: 'Banques et courtiers', sous: 'financements', couleur: '#1f7a55' },
  { tuile: 'apporteur', libelle: 'Apporteurs et parrains', sous: 'affaires apportées', couleur: '#b0306f' },
]

// Le métier du registre → sa tuile. Tout autre métier (société, administration…) n'est PAS au catalogue.
const TUILE_DU_METIER: Record<string, Exclude<TuileCatalogue, 'notaire'>> = {
  syndic: 'syndic', diagnostiqueur: 'diag', courtier: 'courtier', banque: 'courtier', apporteur: 'apporteur', parrain: 'apporteur',
}
export const METIERS_DU_CATALOGUE = Object.keys(TUILE_DU_METIER)
export const LIBELLE_METIER_CATALOGUE: Record<string, string> = {
  syndic: 'Syndic', diagnostiqueur: 'Diagnostiqueur', courtier: 'Courtier', banque: 'Banque', apporteur: 'Apporteur', parrain: 'Parrain',
}

export type ContactCatalogue = {
  hektor_contact_id: string
  civilite?: string | null
  prenom?: string | null
  nom?: string | null
  display_name?: string | null
  archive?: boolean | number | string | null
  ville?: string | null
  phone_primary?: string | null
  email?: string | null
}
export type LigneCatalogue = { id: string; nom: string; detail: string; metiers: string[]; archive: boolean; recherche: string }
export type Catalogue = Record<TuileCatalogue, { actifs: LigneCatalogue[]; archives: LigneCatalogue[] }>

const texte = (v: unknown) => String(v ?? '').trim()
const estArchive = (v: unknown) => v === true || v === 1 || ['true', '1', 't', 'yes', 'oui'].includes(texte(v).toLowerCase())
const sansAccents = (v: string) => v.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export function nomDuContact(c: ContactCatalogue): string {
  return [c.prenom, c.nom].map(texte).filter(Boolean).join(' ') || texte(c.display_name) || `Contact ${c.hektor_contact_id}`
}

function ligne(c: ContactCatalogue, metiers: string[]): LigneCatalogue {
  const nom = nomDuContact(c)
  const detail = [texte(c.ville), texte(c.phone_primary) || texte(c.email)].filter(Boolean).join(' · ')
  return { id: texte(c.hektor_contact_id), nom, detail, metiers, archive: estArchive(c.archive), recherche: sansAccents(`${nom} ${detail}`) }
}

const parNom = (a: LigneCatalogue, b: LigneCatalogue) => a.nom.localeCompare(b.nom, 'fr', { sensitivity: 'base' }) || a.id.localeCompare(b.id)

// Range chaque contact dans sa ou ses tuiles : les actifs d'abord (par nom), les archivés à part.
// Un contact absent des fiches (`contacts`) est ignoré : on ne montre que ce qu'on peut ouvrir.
export function construireCatalogue(
  registre: { contact_id: string | number; metier: string }[],
  contacts: ContactCatalogue[],
  notaires: ContactCatalogue[],
): Catalogue {
  const parId = new Map(contacts.map((c) => [texte(c.hektor_contact_id), c]))
  const metiersParTuile = new Map<TuileCatalogue, Map<string, string[]>>()
  for (const r of registre ?? []) {
    const tuile = TUILE_DU_METIER[texte(r?.metier)]
    const id = texte(r?.contact_id)
    if (!tuile || !id || !parId.has(id)) continue
    const m = metiersParTuile.get(tuile) ?? new Map<string, string[]>()
    const liste = m.get(id) ?? []
    if (!liste.includes(r.metier)) liste.push(r.metier)
    m.set(id, liste)
    metiersParTuile.set(tuile, m)
  }
  const vide = () => ({ actifs: [] as LigneCatalogue[], archives: [] as LigneCatalogue[] })
  const out: Catalogue = { notaire: vide(), syndic: vide(), diag: vide(), courtier: vide(), apporteur: vide() }
  const vus = new Set<string>()
  for (const c of notaires ?? []) {
    const id = texte(c?.hektor_contact_id)
    if (!id || vus.has(id)) continue
    vus.add(id)
    const l = ligne(c, ['notaire'])
    out.notaire[l.archive ? 'archives' : 'actifs'].push(l)
  }
  for (const [tuile, m] of metiersParTuile) {
    for (const [id, metiers] of m) {
      const l = ligne(parId.get(id) as ContactCatalogue, metiers.slice().sort())
      out[tuile][l.archive ? 'archives' : 'actifs'].push(l)
    }
  }
  for (const t of Object.values(out)) { t.actifs.sort(parNom); t.archives.sort(parNom) }
  return out
}

// La recherche de la liste : chaque mot doit se trouver (nom, ville, téléphone ou e-mail), accents ignorés.
export function filtrerCatalogue(lignes: LigneCatalogue[], requete: string): LigneCatalogue[] {
  const mots = sansAccents(requete).split(/\s+/).filter(Boolean)
  if (!mots.length) return lignes
  return lignes.filter((l) => mots.every((m) => l.recherche.includes(m)))
}
