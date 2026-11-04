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
  relation_roles_json?: string[] | string | null
}

// ⛔ RÈGLE DE FRÉDÉRIC (02/11) : UNE FICHE NOTAIRE N'EST JAMAIS UN COUPLE -- dans l'historique comme dans les ajouts.
//   Hektor range des études (SCP, SELARL…) en fiches « ménage » : 50 notaires étaient « couple » au 02/11.
//   « Notaire » = la même règle que l'écran (`estRoleNotaire`, App.tsx) : un rôle notaire_vendeur / notaire_acquereur,
//   calculé chez Supabase depuis nos registres -- un notaire ajouté sur une vente est donc couvert À LA SECONDE,
//   sans attendre la nuit (qui, elle, pose la nature « notaire » : synthèse §23-24).
export function estFicheNotaire(contact: { relation_roles_json?: string[] | string | null }): boolean {
  let roles: unknown = contact.relation_roles_json
  if (typeof roles === 'string') {
    try { roles = JSON.parse(roles) } catch { roles = [] }
  }
  return Array.isArray(roles) && roles.some((role) => role === 'notaire_vendeur' || role === 'notaire_acquereur')
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
  if (contact.nature_fiche !== 'couple' || estFicheNotaire(contact)) return null
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

// `fiche` et `principal` (04/11/2026) : les deux morceaux de `sousTitre`, séparés pour la liste du foyer.
export type FoyerOnglet = { titre: string; sousTitre: string; vide: boolean; fiche: string | null; principal: boolean }

export type FoyerAffiche = {
  etiquette: string
  incomplet: boolean
  situation: string | null       // « mariés » / « pacsés », ou null
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
  principal: FoyerPersonne & { nature_fiche?: string | null; marital_status?: string | null; relation_roles_json?: string[] | string | null },
  conjoint: FoyerPersonne | null,
): FoyerAffiche | null {
  if (principal.nature_fiche !== 'couple' || estFicheNotaire(principal)) return null
  const situation = SITUATION_DU_COUPLE[(principal.marital_status ?? '').trim()]
  const incomplet = !conjoint
  const etiquette = incomplet ? 'Couple · conjoint à compléter' : situation ? `Couple · ${situation}` : 'Couple'
  return {
    etiquette,
    incomplet,
    situation: situation ?? null,
    onglets: [
      { titre: nomDeLOnglet(principal), sousTitre: `fiche ${principal.hektor_contact_id} · principal`, vide: false, fiche: principal.hektor_contact_id, principal: true },
      conjoint
        ? { titre: nomDeLOnglet(conjoint), sousTitre: `fiche ${conjoint.hektor_contact_id}`, vide: false, fiche: conjoint.hektor_contact_id, principal: false }
        : { titre: 'Conjoint', sousTitre: 'à compléter', vide: true, fiche: null, principal: false },
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

/** COUPLES (02/11/2026) : le numéro de la seconde fiche VIDE que Hektor connaît comme place 2 du couple
 *  (`etat = vide`, 975 couples actifs au 02/11) -- la seule case qu'on propose de « compléter » : remplir la place 2
 *  de la première la remplit (essai du 02/11, synthèse §31). null pour tout le reste : nommé, aucune seconde,
 *  case rattachée par notre nuit (chez Hektor, une coquille séparée : écrire créerait un doublon). */
export function conjointVideId(couple_json: CoupleSource['couple_json']): string | null {
  const json = lireCoupleJson(couple_json)
  if (json?.etat !== 'vide') return null
  const id = String(json.conjoint?.id ?? '').trim()
  return id || null
}

/** COUPLES, pièce G (03/11/2026) : « Ajouter un conjoint » n'est proposé qu'à une PERSONNE SEULE -- nature de la nuit
 *  `personne_seule`, pas notaire, sans conjoint connu (`couple_json` absent ou « aucun »), active, connue de Hektor
 *  (`hektor_target_id`). La base refait TOUS ces contrôles (app_ajouter_conjoint_optimistic) : ici, on ne fait que ne
 *  pas montrer un bouton qui serait refusé. Les « couples écrits dans le nom » (nature `couple`) n'ont pas le bouton :
 *  leurs deux prénoms sont sur une seule fiche, à séparer d'abord (synthèse couples §52). */
export function peutRecevoirUnConjoint(contact: CoupleSource & { archive?: boolean | string | number | null; hektor_target_id?: string | null }): boolean {
  // `archive` arrive en booléen, en nombre ou en texte selon la source : seule une valeur VRAIE écarte la fiche.
  const archivee = contact.archive === true || contact.archive === 1 || ['1', 'true', 'oui'].includes(String(contact.archive ?? '').trim().toLowerCase())
  if (contact.nature_fiche !== 'personne_seule' || estFicheNotaire(contact) || archivee) return false
  if (!String(contact.hektor_target_id ?? '').trim()) return false
  const etat = lireCoupleJson(contact.couple_json)?.etat
  return !etat || etat === 'aucun'
}

/** COUPLES, pièce G (03/11/2026, maquette « le foyer, deux places ») : les initiales d'une place -- deux lettres au
 *  plus, prénom puis nom ; « ? » quand on ne sait rien (la place vide). */
export function initialesDePlace(...morceaux: (string | null | undefined)[]): string {
  const mots = morceaux.flatMap((m) => String(m ?? '').trim().split(/[\s-]+/)).filter((m) => /\p{L}/u.test(m))
  const lettres = mots.slice(0, 2).map((m) => (m.match(/\p{L}/u)?.[0] ?? '').toUpperCase()).join('')
  return lettres || '?'
}

/** Les biens que le conjoint partagera, tels que la fiche les connaît déjà (aucune lecture de plus) : ceux où la
 *  personne est mandant ou propriétaire, un par bien. La base refait le vrai tri au clic (bien vivant, droits). */
export function biensPartageables(relations: { hektor_annonce_id?: string | number | null; role_contact?: string | null; titre_bien?: string | null; numero_mandat?: string | null; numero_dossier?: string | null }[]): { id: string; libelle: string }[] {
  const vus = new Set<string>()
  const biens: { id: string; libelle: string }[] = []
  for (const lien of relations) {
    const id = String(lien.hektor_annonce_id ?? '').trim()
    const role = String(lien.role_contact ?? '').toLowerCase()
    if (!id || vus.has(id) || !(role.includes('mandant') || role.includes('proprietaire') || role.includes('propriétaire'))) continue
    vus.add(id)
    const titre = String(lien.titre_bien ?? '').trim()
    const numero = String(lien.numero_mandat ?? lien.numero_dossier ?? '').trim()
    biens.push({ id, libelle: titre || (numero ? `Mandat ${numero}` : `Bien ${id}`) })
  }
  return biens
}

/** Ce que l'écran dit d'un refus de la base (`raison` de app_ajouter_conjoint_optimistic). */
export function raisonAjoutConjoint(raison: string | null | undefined): string {
  switch (raison) {
    case 'cran_ferme': return "Ce geste n'est pas encore ouvert."
    case 'meme_fiche': return "On ne peut pas choisir la même fiche comme conjoint."
    case 'conjoint_introuvable': return 'La fiche choisie est introuvable.'
    case 'personne_archivee': return 'Cette fiche est archivée : réactivez-la d’abord.'
    case 'conjoint_archive': return 'La fiche choisie est archivée.'
    case 'notaire': return "Une fiche notaire n'est jamais un couple."
    case 'personne_pas_seule': return "Cette fiche n'est pas une personne seule."
    case 'conjoint_pas_seul': return "La fiche choisie n'est pas une personne seule (case vide, conjoint d'un autre…)."
    case 'personne_deja_en_couple': return 'Cette personne a déjà un conjoint.'
    case 'conjoint_deja_en_couple': return 'La fiche choisie a déjà un conjoint.'
    case 'personne_sans_numero_hektor': return "Cette fiche n'est pas encore créée chez Hektor : réessayez dans une minute."
    case 'conjoint_sans_numero_hektor': return "La fiche choisie n'est pas connue de Hektor."
    case 'deja_en_cours': return 'Un ajout de conjoint est déjà en cours pour ces fiches.'
    default: return raison ? `Refusé (${raison}).` : 'Refusé.'
  }
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
