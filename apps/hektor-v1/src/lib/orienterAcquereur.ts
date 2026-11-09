// CHANTIER PARTENAIRES · LOT 6 (09/11/2026) — « ORIENTER UN ACQUÉREUR » vers un courtier ou une banque. Règles pures.
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.20-28.21. Même principe que 4.4 et le lot 5 : un MESSAGE
// PRÊT, modifiable, à copier ou à ouvrir dans la messagerie. RIEN n'est envoyé par l'app.
// ⛔ Décision de Frédéric (09/11, « Oui, sans coordonnées ») : le message ne porte NI le téléphone NI l'e-mail du client
// (les transmettre à un tiers demande son accord) — son nom, son projet et où il en est, rien d'autre.
import type { EtapeApport } from './affairesApportees'

// Une recherche active du client (`app_contact_search_current`), seulement ce qui sert au message.
export type RechercheProjet = {
  offre?: string | null
  types_json?: unknown
  villes_json?: unknown
  prix_min?: string | null
  prix_max?: string | null
}

const texte = (v: unknown) => String(v ?? '').trim()
const euros = (v: unknown) => {
  const n = Number(texte(v).replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(n) && n > 0 ? `${Math.round(n).toLocaleString('fr-FR').replace(/ /g, ' ')} €` : null
}
const valeurs = (v: unknown): string[] => {
  if (Array.isArray(v)) return v.map(texte).filter(Boolean)
  if (v && typeof v === 'object') return Object.values(v as Record<string, unknown>).map(texte).filter(Boolean)
  return []
}

// La recherche qui décrit un projet d'ACHAT (offre « 0 » au registre : 4 265 recherches actives sur 4 289 au 09/11) ;
// une recherche de location ou d'un autre type ne dit rien au courtier.
export function rechercheAchat(liste: RechercheProjet[]): RechercheProjet | null {
  return liste.find((r) => texte(r.offre) === '0') ?? null
}

// Les lignes « projet » : une donnée absente n'est pas écrite.
export function lignesProjet(r: RechercheProjet | null): string[] {
  if (!r) return []
  const types = [...new Set(valeurs(r.types_json))]
  const villes = valeurs(r.villes_json)
  const min = euros(r.prix_min)
  const max = euros(r.prix_max)
  const budget = min && max ? `de ${min} à ${max}` : max ? `jusqu'à ${max}` : min ? `à partir de ${min}` : null
  return [
    types.length ? `- Bien recherché : ${types.slice(0, 4).join(', ')}${types.length > 4 ? '…' : ''}` : null,
    budget ? `- Budget : ${budget}` : null,
    villes.length ? `- Secteur : ${villes.slice(0, 5).join(', ')}${villes.length > 5 ? '…' : ''}` : null,
  ].filter(Boolean) as string[]
}

const OU_IL_EN_EST: Partial<Record<EtapeApport, string>> = {
  offre: 'une offre d’achat est en cours',
  compromis: 'un compromis de vente est signé',
  vente: 'l’achat est conclu',
}

export function messageOrientation(input: {
  client: string
  etape: EtapeApport
  recherche: RechercheProjet | null
  signature?: string | null
}): { sujet: string; corps: string } {
  const client = texte(input.client) || 'un acquéreur'
  const projet = lignesProjet(input.recherche)
  const ouEnEst = OU_IL_EN_EST[input.etape]
  const corps = [
    'Bonjour,',
    '',
    `Nous accompagnons ${client} dans son projet d’achat immobilier et souhaitons vous l’orienter pour l’étude de son financement.`,
    projet.length || ouEnEst ? '' : null,
    ...projet,
    ouEnEst ? `- Où il en est : ${ouEnEst}` : null,
    '',
    'Pourriez-vous nous dire si vous pouvez l’accompagner ? Nous vous mettrons en relation.',
    '',
    'Bien cordialement,',
    texte(input.signature) || 'Groupe GTI',
  ].filter((l) => l !== null) as string[]
  return { sujet: `Un acquéreur à accompagner : ${client}`, corps: corps.join('\n') }
}
