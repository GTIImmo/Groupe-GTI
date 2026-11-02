// COUPLES, pièce C (02/11/2026) -- ce que l'annuaire montre d'un couple.
//
// ⭐ LA RÈGLE DE FRÉDÉRIC (02/11) : une fiche s'affiche « Couple » SI ET SEULEMENT SI la nature
//   calculée la nuit le dit (`nature_fiche = 'couple'`). `couple_json` (P2) NE DÉCIDE PAS : il
//   n'apporte que le conjoint (prénom, téléphone). Les deux calculs divergent -- 16 052 « personne
//   seule » portent un `couple_json` à l'état « vide » (couples anciens) -- et c'est la nature qui gagne.
//   Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §17-18.
//
// ⚠ Pas de couleur d'alerte dans l'annuaire (décision du 31/10) : l'orange « conjoint à compléter »
//   est pour la fiche seulement. Ici, sans prénom du conjoint, l'étiquette dit simplement « Couple ».

export type CoupleConjoint = {
  id?: string | null
  prenom?: string | null
  nom?: string | null
  telephone?: string | null
  email?: string | null
}

export type CoupleJson = {
  etat?: string | null          // 'nomme' | 'vide' | 'aucun' | 'plusieurs'
  autres?: number | null
  conjoint?: CoupleConjoint | null
}

export type CoupleSource = {
  nature_fiche?: string | null
  couple_json?: CoupleJson | string | null
  prenom?: string | null
  phone_primary?: string | null
}

export type CoupleAffiche = {
  etiquette: string
  /** Vide = garder l'affichage habituel (un seul téléphone). */
  telephones: { qui: string; numero: string }[]
}

export function lireCoupleJson(valeur: CoupleSource['couple_json']): CoupleJson | null {
  if (!valeur) return null
  if (typeof valeur === 'object') return valeur
  try {
    const lu = JSON.parse(valeur)
    return lu && typeof lu === 'object' ? (lu as CoupleJson) : null
  } catch {
    return null
  }
}

function initiale(prenom: string): string {
  const lettre = prenom.trim().charAt(0)
  return lettre ? `${lettre.toUpperCase()}.` : ''
}

export function coupleAffiche(contact: CoupleSource): CoupleAffiche | null {
  if (contact.nature_fiche !== 'couple') return null
  const json = lireCoupleJson(contact.couple_json)
  const conjoint = json?.etat === 'nomme' ? json.conjoint ?? null : null
  const prenom1 = (contact.prenom ?? '').trim()
  const prenom2 = (conjoint?.prenom ?? '').trim()
  const etiquette = prenom1 && prenom2 && prenom1.toLowerCase() !== prenom2.toLowerCase()
    ? `Couple · ${prenom1} & ${prenom2}`
    : 'Couple'
  const tel1 = (contact.phone_primary ?? '').trim()
  const tel2 = (conjoint?.telephone ?? '').trim()
  const telephones: CoupleAffiche['telephones'] = []
  // Un second téléphone seulement s'il est DIFFÉRENT : un même numéro recopié sur les deux fiches
  // ne se montre qu'une fois, comme aujourd'hui.
  if (tel2 && tel2.replace(/\D/g, '') !== tel1.replace(/\D/g, '')) {
    if (tel1) telephones.push({ qui: initiale(prenom1), numero: tel1 })
    telephones.push({ qui: initiale(prenom2), numero: tel2 })
  }
  return { etiquette, telephones }
}
