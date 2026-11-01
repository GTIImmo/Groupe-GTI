// ═══ LE DOCUMENT DE MANDAT N'IMPRIME PLUS LA CASE VIDE D'UN COUPLE ═══   02/11/2026
//
// Défaut n° 1 de l'audit des couples (notice/AUDIT_COUPLES_CONJOINTS_MENAGES_2026-10-29.md §5,
// SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md §2.6 et §11). Hektor rattache au bien la
// fiche de la personne ET une seconde fiche VIDE, « place du second membre ». Le registre la
// livre telle quelle : sans prénom, sans nom, sans coordonnée, son nom affiché se réduit à la
// civilité (« Mr./Mme ») ou à « Contact <numéro> ». Le document de mandat en faisait un
// MANDANT SANS NOM, avec sa case de signature.
// Mesure du 01/11 : 3 777 de ces cases sont dans l'app, TOUTES à côté d'une personne nommée du
// même bien ; plus ~12 000 cases rattachées à leur foyer.
//
// ⚠ LE CRITÈRE EST ÉTROIT, ET C'EST VOULU : une fiche n'est écartée que si elle n'a RIEN à
//   elle (ni prénom, ni nom, ni téléphone, ni e-mail, ni adresse) ET que son nom n'est qu'une
//   civilité ou « Contact <numéro> ». Un mandant venu du blob de Hektor avec son seul nom
//   (« DUPONT Paul ») est GARDÉ. Et si TOUS les mandants sont vides, on les garde tous : le
//   document ne perd jamais son dernier mandant en silence (règle du registre, App.tsx).

export type MandantCandidat = {
  name: string
  civility: string
  firstName: string
  lastName: string
  phone: string
  email: string
  address: string
}

// Une suite faite UNIQUEMENT de mots de civilité : « Mr./Mme », « M. et Mme », « M_Mme »…
const QUE_DES_CIVILITES = /^(?:[\s./_&-]*(?:m|mr|mme|mlle|me|mmes|mm|et)\b)*[\s./_&-]*$/i
const CONTACT_NUMERO = /^contact\s+\d+$/i

export function estCaseVideDeMenage(contact: MandantCandidat): boolean {
  if (contact.firstName || contact.lastName || contact.phone || contact.email || contact.address) return false
  let reste = (contact.name || '').trim()
  if (contact.civility && reste.startsWith(contact.civility)) reste = reste.slice(contact.civility.length).trim()
  return !reste || CONTACT_NUMERO.test(reste) || QUE_DES_CIVILITES.test(reste)
}

/** Écarte les cases vides, SAUF si elles sont tout ce qu'il y a (on garde alors la liste entière). */
export function sansCasesVides<T extends MandantCandidat>(contacts: T[]): T[] {
  const reels = contacts.filter((contact) => !estCaseVideDeMenage(contact))
  return reels.length ? reels : contacts
}
