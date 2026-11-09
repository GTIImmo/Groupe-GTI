// CHANTIER PARTENAIRES §28.13 (09/11/2026) — LA FENÊTRE « AJOUTER UN PARTENAIRE » : règles pures (aucune lecture, aucune écriture).
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.13. Maquette : canevas, planches 5 et 6.
// Décisions de Frédéric (09/11) : la fenêtre ne change selon le métier QUE par la couleur et les libellés ; pour un
// partenaire, PAS d'e-mail d'activation « espace client », PAS d'automatismes clients ; les notaires restent à part ;
// « Société » coché par défaut.
import { TUILES_CATALOGUE, type TuileCatalogue } from './cataloguePartenaires'

export type MetierAjout = 'syndic' | 'diagnostiqueur' | 'apporteur' | 'courtier' | 'parrain' | 'banque'

// Le code métier de Hektor (registre_partenaires_reprise.py, METIER_HEKTOR). Courtier et parrain n'en ont PAS : on envoie
// « non défini » (le déclencheur D-1 n'écrit alors rien) et l'app écrit le métier chez nous après la création — envoyer
// « 21 Autre » ferait naître une ligne « autre » parasite au registre.
export const METIERS_AJOUT: { metier: MetierAjout; libelle: string; tuile: Exclude<TuileCatalogue, 'notaire'>; hektor: string }[] = [
  { metier: 'syndic', libelle: 'syndic', tuile: 'syndic', hektor: '5' },
  { metier: 'diagnostiqueur', libelle: 'diagnostiqueur', tuile: 'diag', hektor: '4' },
  { metier: 'apporteur', libelle: 'apporteur', tuile: 'apporteur', hektor: '15' },
  { metier: 'courtier', libelle: 'courtier', tuile: 'courtier', hektor: '' },
  { metier: 'parrain', libelle: 'parrain', tuile: 'apporteur', hektor: '' },
  { metier: 'banque', libelle: 'banque', tuile: 'courtier', hektor: '19' },
]
export const estMetierAjout = (m: unknown): m is MetierAjout => METIERS_AJOUT.some((x) => x.metier === m)
export const metierAjout = (m: MetierAjout) => METIERS_AJOUT.find((x) => x.metier === m) ?? METIERS_AJOUT[0]
export function apparenceMetier(m: MetierAjout) {
  const t = TUILES_CATALOGUE.find((x) => x.tuile === metierAjout(m).tuile)
  return { couleur: t?.couleur ?? '#5b4a9e', doux: t?.doux ?? '#efecf9', icone: t?.icone ?? '' }
}
const majuscule = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)
// « un syndic », « un apporteur » : les six métiers sont masculins.
export const libellesMetier = (m: MetierAjout) => {
  const l = metierAjout(m).libelle
  return { titre: `Ajouter un ${l}`, nouveau: `Nouveau ${l}`, enFaire: `En faire un ${l}`, creer: `Créer le ${l}`,
    nouveauBouton: `＋ Créer un nouveau ${l}`, deja: `Déjà ${l} au catalogue`, pastille: majuscule(l) }
}

const texte = (v: unknown) => String(v ?? '').trim()
export const normaliser = (v: unknown) => texte(v).normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/[^\p{L}\p{N}]+/gu, ' ').replace(/\s+/g, ' ').trim().toLowerCase()

// La recherche part dès 3 caractères. Les motifs sont ceux d'un filtre « ilike » de PostgREST (« * » = n'importe quoi) :
// les mots se suivent (« foncia loire » trouve « FONCIA LOIRE AUVERGNE ») ; un numéro se cherche sous les TROIS formes
// que portent les fiches — collé, en paires à points, en paires à espaces (« 0428550020 » trouve « 04.28.55.00.20 »).
// 09/11, vu en ligne : un motif « *04*28*… » (n'importe quoi entre les paires) ramenait aussi d'AUTRES numéros. Les
// caractères qui casseraient le filtre (virgule, parenthèses, guillemets, « * », « % ») sont retirés.
export function motifsDeRecherche(saisie: string): string[] {
  const t = texte(saisie).replace(/[,()"*%\\]/g, ' ').replace(/\s+/g, ' ').trim()
  if (t.length < 3) return []
  const chiffres = t.replace(/[\s.\-]/g, '').replace(/^\+/, '')
  if (/^\d{3,}$/.test(chiffres)) {
    const paires = chiffres.match(/\d{1,2}/g) ?? []
    return [...new Set([`*${chiffres}*`, `*${paires.join('.')}*`, `*${paires.join(' ')}*`])]
  }
  return [`*${t.split(' ').join('*')}*`]
}

export type ContactTrouve = {
  id: string
  nom: string
  ville: string | null
  telephone: string | null
  email: string | null
  archive: boolean
  metiers: string[]          // métiers ACTIFS au registre (app_partenaire_metier)
  biens: number              // biens reliés à ce partenaire pour CE métier
}
// Deux groupes : celui qui a DÉJÀ ce métier (Choisir), et les autres (En faire un …). Les fiches archivées passent
// après ; dans chaque groupe, celle qui porte le plus de nos biens d'abord, puis par nom.
export function grouperResultats(liste: ContactTrouve[], metier: MetierAjout) {
  const tri = (a: ContactTrouve, z: ContactTrouve) =>
    Number(a.archive) - Number(z.archive) || z.biens - a.biens || a.nom.localeCompare(z.nom, 'fr')
  return {
    deja: liste.filter((c) => c.metiers.includes(metier)).sort(tri),
    autres: liste.filter((c) => !c.metiers.includes(metier)).sort(tri),
  }
}

// Le détail d'une ligne de résultat : ville · n° · téléphone (ou e-mail).
export const detailContact = (c: ContactTrouve) =>
  [c.ville, `n° ${c.id}`, c.telephone || c.email].filter(Boolean).join(' · ')

export type FichePartenaire = {
  forme: 'societe' | 'personne'
  raisonSociale: string
  civilite: string
  prenom: string
  nom: string
  telephone: string
  portable: string
  email: string
  adresse: string
  codePostal: string
  ville: string
  site: string
  note: string
}
export const ficheVide = (): FichePartenaire => ({ forme: 'societe', raisonSociale: '', civilite: '', prenom: '', nom: '',
  telephone: '', portable: '', email: '', adresse: '', codePostal: '', ville: '', site: '', note: '' })

// Ce qui manque pour créer (mêmes garde-fous que createHektorContactJob : un nom, un moyen de joindre, un compte).
export function manquesFiche(f: FichePartenaire, compteChoisi: boolean): string[] {
  const manques: string[] = []
  if (f.forme === 'societe' ? !texte(f.raisonSociale) : !texte(f.nom)) manques.push(f.forme === 'societe' ? 'la raison sociale' : 'le nom')
  if (!texte(f.email) && !texte(f.telephone) && !texte(f.portable)) manques.push('un téléphone ou un e-mail')
  if (!compteChoisi) manques.push('le négociateur')
  return manques
}

// La fiche → l'entrée de createHektorContactJob (même travail, même worker que la fenêtre client). Une société porte
// son nom en raison sociale ET en nom (comme la fenêtre client : lastName = companyName) ; la personne à qui parler
// passe en commentaire, pour ne rien perdre.
export function entreeCreation(f: FichePartenaire, m: MetierAjout, compte: {
  email: string | null; idUser: string | null; negociateurId?: string | null; agenceId?: string | null; agenceIdUser?: string | null; agenceNom?: string | null
}) {
  const societe = f.forme === 'societe'
  const raison = texte(f.raisonSociale)
  const interlocuteur = [texte(f.civilite), texte(f.prenom), texte(f.nom)].filter(Boolean).join(' ')
  const notes = [societe && interlocuteur ? `Interlocuteur : ${interlocuteur}` : '', texte(f.note)].filter(Boolean).join('\n')
  return {
    civility: societe ? '' : texte(f.civilite),
    lastName: societe ? raison : texte(f.nom),
    firstName: societe ? '' : texte(f.prenom),
    companyName: societe ? raison : '',
    partnerJobId: metierAjout(m).hektor,
    website: texte(f.site),
    email: texte(f.email),
    // Mêmes cases que la fenêtre client : « Portable » = phone, « Fixe » = phoneSecondary.
    phone: texte(f.portable),
    phoneSecondary: texte(f.telephone),
    address: texte(f.adresse),
    postalCode: texte(f.codePostal),
    city: texte(f.ville),
    contactKind: 'partenaire',
    personType: societe ? 'personne_morale' : 'personne_physique',
    comments: notes,
    // Décisions (a) et (b) du 09/11 : rien d'« espace client », aucun automatisme client pour un partenaire.
    sendRgpdEmail: false,
    crmMandateSummaryEnabled: false,
    crmMandateExpirationEnabled: false,
    crmBirthdayEnabled: false,
    hektorUserEmail: compte.email,
    hektorUserId: compte.idUser,
    hektorNegotiatorId: compte.negociateurId ?? null,
    hektorAgencyId: compte.agenceId ?? null,
    hektorAgencyUserId: compte.agenceIdUser ?? null,
    hektorAgencyLabel: compte.agenceNom ?? null,
  }
}

// Le compte Hektor sous lequel la fiche naît — MÊME règle que la fenêtre client (App.tsx `HektorContactIdentityForm`,
// `availableHektorNegotiators` / `defaultHektorOption` / `selectedHektorEmail`, et la règle de Frédéric du 06/11
// `emailHektorHorsSession`) : un négociateur ne voit que lui-même et part de lui-même ; un admin ou un manager n'est
// JAMAIS pris sous l'e-mail de sa propre session — il choisit le négociateur.
export type NegoOption = { idUser: string; label: string; email: string | null; agenceNom: string | null;
  hektorNegociateurId?: string | null; hektorAgenceId?: string | null; agenceIdUser?: string | null; actif?: boolean }
const mail = (s: string | null | undefined) => String(s ?? '').trim().toLowerCase()
export function comptesHektor<N extends NegoOption>(negos: N[], ctx: { role: string | null; sessionEmail: string | null; hektorUserId: string | null; hektorUserEmail: string | null }) {
  const commercial = ctx.role === 'commercial'
  const dispo = commercial ? negos.filter((n) => mail(n.email) === mail(ctx.sessionEmail)) : negos
  const designe = commercial ? ctx.hektorUserEmail : (mail(ctx.hektorUserEmail) && mail(ctx.hektorUserEmail) !== mail(ctx.sessionEmail) ? ctx.hektorUserEmail : null)
  const parId = ctx.hektorUserId ? dispo.find((n) => n.idUser === String(ctx.hektorUserId)) : undefined
  const parEmail = designe ? dispo.find((n) => mail(n.email) === mail(designe)) : undefined
  const soiMeme = commercial ? dispo.find((n) => mail(n.email) === mail(ctx.sessionEmail)) : undefined
  return { dispo, defaut: parId ?? parEmail ?? soiMeme ?? null }
}
export function compteRetenu(choisi: NegoOption | null, dispoVide: boolean, ctx: { role: string | null; sessionEmail: string | null; hektorUserId: string | null; hektorUserEmail: string | null }) {
  const commercial = ctx.role === 'commercial'
  const designe = commercial ? ctx.hektorUserEmail : (mail(ctx.hektorUserEmail) && mail(ctx.hektorUserEmail) !== mail(ctx.sessionEmail) ? ctx.hektorUserEmail : null)
  return {
    email: choisi?.email ?? designe ?? (commercial ? ctx.sessionEmail : null),
    idUser: choisi?.idUser ?? (dispoVide ? ctx.hektorUserId : null),
    negociateurId: choisi?.hektorNegociateurId ?? null,
    agenceId: choisi?.hektorAgenceId ?? null,
    agenceIdUser: choisi?.agenceIdUser ?? null,
    agenceNom: choisi?.agenceNom ?? null,
  }
}

// La ville suit le code postal (même règle que la fenêtre client, 8a C-3 : App.tsx avertissementLocaliteContact).
export function avertissementVille(codePostal: string, ville: string, communes: string[]): string | null {
  const cp = texte(codePostal)
  const v = texte(ville)
  if (!cp && !v) return null
  if (v && !cp) return 'Sans code postal, Hektor ne gardera pas la ville.'
  if (cp && !/^\d{5}$/.test(cp)) return 'Le code postal doit compter 5 chiffres.'
  if (v && communes.length && !communes.some((c) => normaliser(c) === normaliser(v))) {
    const liste = communes.slice(0, 5).join(', ') + (communes.length > 5 ? '…' : '')
    return `« ${v} » n'est pas une commune du ${cp} : Hektor risque de ne pas garder la ville (communes du ${cp} : ${liste}).`
  }
  return null
}
