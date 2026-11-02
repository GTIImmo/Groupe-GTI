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

// ─── COUPLES, pièce D (02/11/2026) -- la FICHE d'un couple (interrupteur `contacts_couples_fiche`) ───
//
// Deux onglets, une personne chacun, qui ne pilotent QUE les coordonnées (décision du 02/11 : le second
// est en LECTURE SEULE -- modifier un conjoint passe chez Hektor par la fiche principale, geste pas écrit).
// Recherches, activité, relances et boutons restent ceux de la fiche principale (0 conjoint n'a de recherche).
// L'orange « conjoint à compléter » est pour la fiche seulement (décision du 31/10).

export type FoyerPersonne = {
  hektor_contact_id: string
  civilite?: string | null
  prenom?: string | null
  nom?: string | null
}

export type FoyerOnglet = { titre: string; sousTitre: string; vide: boolean }

export type FoyerAffiche = {
  etiquette: string
  incomplet: boolean
  onglets: [FoyerOnglet, FoyerOnglet]
}

const SITUATION_DU_COUPLE: Record<string, string> = { married: 'mariés', civil_union: 'pacsés' }

function nomDeLOnglet(personne: FoyerPersonne): string {
  const prenom = (personne.prenom ?? '').trim()
  if (prenom) return prenom
  const nom = (personne.nom ?? '').trim()
  // Les codes de civilité de Hektor (« Mr./Mme », « M_Mme ») ne servent pas d'étiquette : on garde le nom seul.
  const civilite = (personne.civilite ?? '').trim()
  const civiliteSimple = /^(m\.?|mr\.?|mme\.?|mlle\.?)$/i.test(civilite) ? civilite : ''
  return [civiliteSimple, nom].filter(Boolean).join(' ') || 'Conjoint'
}

/** `principal` = la première fiche (porteuse du couple) ; `conjoint` = la seconde fiche NOMMÉE, ou null. */
export function foyerAffiche(
  principal: FoyerPersonne & { nature_fiche?: string | null; marital_status?: string | null },
  conjoint: FoyerPersonne | null,
): FoyerAffiche | null {
  if (principal.nature_fiche !== 'couple') return null
  const situation = SITUATION_DU_COUPLE[(principal.marital_status ?? '').trim()]
  const incomplet = !conjoint
  const etiquette = incomplet ? 'Couple · conjoint à compléter' : situation ? `Couple · ${situation}` : 'Couple'
  return {
    etiquette,
    incomplet,
    onglets: [
      { titre: nomDeLOnglet(principal), sousTitre: `fiche ${principal.hektor_contact_id} · principal`, vide: false },
      conjoint
        ? { titre: nomDeLOnglet(conjoint), sousTitre: `fiche ${conjoint.hektor_contact_id}`, vide: false }
        : { titre: 'Conjoint', sousTitre: 'à compléter', vide: true },
    ],
  }
}

/** Le numéro de la seconde fiche NOMMÉE, ou null (case vide, aucune, illisible). */
export function conjointNommeId(couple_json: CoupleSource['couple_json']): string | null {
  const json = lireCoupleJson(couple_json)
  if (json?.etat !== 'nomme') return null
  const id = String(json.conjoint?.id ?? '').trim()
  return id || null
}

/** Les liens des deux personnes, sans doublon (même bien, même rôle) : la fiche du foyer montre les biens
 *  propres au conjoint (21 au 02/11) et un rôle qui diffère (10), sans répéter les autres. */
export function unirLiensDuFoyer<T extends { hektor_annonce_id?: string | number | null; role_contact?: string | null }>(
  principaux: T[],
  duConjoint: T[],
): T[] {
  const cle = (lien: T) => `${String(lien.hektor_annonce_id ?? '')}|${String(lien.role_contact ?? '').toLowerCase()}`
  const vus = new Set(principaux.map(cle))
  return [...principaux, ...duConjoint.filter((lien) => !vus.has(cle(lien)))]
}
