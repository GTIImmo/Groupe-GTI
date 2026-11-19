import { hasSupabaseEnv, supabase } from './supabase'
import { webpEnJpeg } from './photoJpeg'

// ─────────────────────────────────────────────────────────────────────────────
// Étape 4 de l'assistant IA, lot 2 (17/11/2026) -- LES APPELS DE L'ÉCRAN À L'ASSISTANT (Render).
// Le serveur est celui des étapes 1 à 3 (backend/app/routers/assistant.py) : rien n'y change.
//   POST /assistant/message                    -> flux NDJSON : debut, texte, outil, carte, puis fin OU erreur
//   GET  /assistant/conversations              -> mes 50 dernières
//   GET  /assistant/conversations/{id}         -> la conversation et ses messages
//   GET  /assistant/conversations/{id}/actions -> ses cartes et leur état
//   POST /assistant/actions/{id}/valider|refuser
// ⛔ Les refus arrivent AVANT le flux, avec leur vrai code (403 éteint, 404, 429 plafonds) et la phrase du serveur,
//   affichée telle quelle. Un échec d'un geste revient en 200 { ok: false, detail: « Non fait : … » }.
// Mode maquette (sans base) : un faux flux, pour dessiner chaque état à l'écran et le comparer aux planches.
// ─────────────────────────────────────────────────────────────────────────────

export type EtatCarte = 'proposee' | 'en_cours' | 'executee' | 'refusee' | 'echec' | 'expiree'

/** Lot 3 : sur quoi porte la carte (tiré par le serveur de SES paramètres) -> le lien « Ouvrir la fiche ». */
export type CibleCarte =
  | { type: 'contact'; id: string } | { type: 'annonce'; numero: string } | { type: 'bien'; id: string }
  // lot 3b
  | { type: 'transaction'; id: string } | { type: 'recherche'; cle: string } | { type: 'rdv'; date: string }
  | { type: 'demande'; numero: string }

/** 18/11 (étape 4 §66, marche 6a) : ce que la carte « créer » pré-remplit, mis en forme par le SERVEUR (planche 1). */
export type FicheCarte = {
  genre: 'estimation' | 'annonce'
  titre: string
  chiffres: Array<{ libelle: string; valeur: string; complement?: string }>
  lignes: Array<{ libelle: string; valeur: string; contact?: boolean }>
  composition: number
  mandant: boolean
  negociateur: boolean
  photos: number
  a_remplir: string[]
}

export type CarteAssistant = {
  id: string
  geste: string
  resume: string
  etat: EtatCarte
  expire_le?: string | null
  cree_le?: string | null
  execute_le?: string | null
  resultat?: Record<string, unknown> | null
  cibles?: CibleCarte[]
  fiche?: FicheCarte
}

/** 18/11 (§66) : l'ordre d'ouverture de la fenêtre de création, rendu par le serveur au clic (rien n'est écrit).
 *  `cases` = les clés du SCAN de la fiche papier (DraftAnnonceSheetScanFieldKey), déjà vérifiées par le serveur. */
export type OuvertureCreation = {
  ouvrir: 'creation_annonce'
  genre: 'estimation' | 'annonce'
  cases: Record<string, string>
  composition: Array<{ type: string; surface: string; etage: string; detail: string }>
  mandant: { hektor_contact_id: string; nom: string } | null
  negociateur: { hektor_negociateur_id: string; hektor_user_id: string; nom: string; agence: string | null } | null
  photos: Array<{ nom: string; type: string; url: string }>
  cree?: { app_dossier_id: number | null; genre: string; le: string }
}

/** 18/11 (§70-3) : l'ordre d'ouverture de l'ÉDITEUR « Avis de valeur » d'un bien existant (rien n'est écrit).
 *  `champs` = les clés du brouillon de l'éditeur (basse, estimee, haute, etatNote…), `postes` = le barème d'état par
 *  code de poste (ESTIM_POSTES), déjà vérifiés par le serveur. */
export type OuvertureAvis = {
  ouvrir: 'avis_de_valeur'
  app_dossier_id: number
  hektor_annonce_id: number | null
  champs: Record<string, string>
  postes: Record<string, { niveau: string; label: string }>
}

export type ConversationAssistant = { id: string; titre: string; cree_le?: string; maj_le?: string }
export type MessageAssistant = { id: number; role: 'user' | 'assistant'; contenu: string; cree_le: string }

export type EvenementFlux =
  | { type: 'debut'; conversationId: string }
  | { type: 'texte'; delta: string }
  | { type: 'outil'; nom: string | null }
  | { type: 'carte'; id: string; geste: string; resume: string; expire_le?: string | null; cibles?: CibleCarte[]; fiche?: FicheCarte }
  | { type: 'fin'; messageId: number | null; enregistre: boolean }
  | { type: 'erreur'; detail: string }

/** Un refus du serveur : son code HTTP et SA phrase. */
export class RefusAssistant extends Error {
  statut: number
  constructor(statut: number, detail: string) {
    super(detail)
    this.statut = statut
  }
}

const baseUrl = (
  import.meta.env.VITE_BACKEND_API_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8010' : '')
).trim().replace(/\/+$/, '')

const MAQUETTE = !hasSupabaseEnv || !supabase

async function entetes(json: boolean): Promise<Record<string, string>> {
  const jeton = (await supabase!.auth.getSession()).data.session?.access_token
  if (!jeton) throw new RefusAssistant(401, 'Session expirée : reconnecte-toi.')
  return json ? { 'Content-Type': 'application/json', Authorization: `Bearer ${jeton}` } : { Authorization: `Bearer ${jeton}` }
}

async function phraseDuServeur(reponse: Response): Promise<string> {
  const texte = await reponse.text().catch(() => '')
  try {
    const corps = JSON.parse(texte) as { detail?: unknown }
    if (typeof corps.detail === 'string' && corps.detail.trim()) return corps.detail.trim()
  } catch {
    // pas du JSON : on garde le texte brut, ou une phrase générique
  }
  return texte.trim().slice(0, 300) || `L'assistant n'a pas répondu (code ${reponse.status}).`
}

async function appeler<T>(chemin: string, methode: 'GET' | 'POST'): Promise<T> {
  if (!baseUrl) throw new RefusAssistant(0, "L'adresse du serveur n'est pas configurée.")
  const reponse = await fetch(`${baseUrl}${chemin}`, { method: methode, headers: await entetes(false) })
  if (!reponse.ok) throw new RefusAssistant(reponse.status, await phraseDuServeur(reponse))
  return (await reponse.json()) as T
}

// ── 17/11/2026 : LE TROMBONE (note étape 4 §51-52) ─────────────────────────────────────────────────────────────
// Le serveur vérifie qui dépose, le type et la taille, et rend une adresse d'envoi SIGNÉE pour UN fichier à UN endroit
// (temp/assistant/<personne>/<numéro>/) ; l'écran y envoie le fichier DIRECTEMENT au coffre (il ne passe pas par Render),
// puis le serveur RELIT ce qui a été déposé et le supprime s'il sort des règles. Le modèle ne voit que nom, type, taille.
export type EtatFichiers = { ouvert: boolean; types: string[]; tailleMax: number; maxFichiers: number }
export type FichierJoint = { id: string; nom: string; type: string; libelle: string; taille: number }

export async function etatFichiers(): Promise<EtatFichiers> {
  if (MAQUETTE) return { ouvert: true, types: ['application/pdf', 'image/jpeg', 'image/png'], tailleMax: 50 * 1024 * 1024, maxFichiers: 10 }
  return appeler<EtatFichiers>('/assistant/fichiers/etat', 'GET')
}

async function appelerJson<T>(chemin: string, methode: 'POST' | 'DELETE', corps?: unknown): Promise<T> {
  if (!baseUrl) throw new RefusAssistant(0, "L'adresse du serveur n'est pas configurée.")
  const reponse = await fetch(`${baseUrl}${chemin}`, {
    method: methode, headers: await entetes(true), body: corps === undefined ? undefined : JSON.stringify(corps),
  })
  if (!reponse.ok) throw new RefusAssistant(reponse.status, await phraseDuServeur(reponse))
  return (await reponse.json()) as T
}

/** Dépose UN fichier : préparer (le serveur contrôle) -> envoyer au coffre (adresse signée) -> confirmer (le serveur relit). */
export async function deposerFichier(fichier: File): Promise<FichierJoint> {
  fichier = await webpEnJpeg(fichier)  // 19/11 (§89, D10) : la carte « Ajouter des photos » ne prend que JPEG / PNG
  if (MAQUETTE) {
    await attendre(400)
    return { id: Math.random().toString(16).slice(2).padEnd(32, '0').slice(0, 32), nom: fichier.name, type: fichier.type, libelle: fichier.type, taille: fichier.size }
  }
  const depot = await appelerJson<{ id: string; bucket: string; chemin: string; jeton: string; type: string }>(
    '/assistant/fichiers/preparer', 'POST', { nom: fichier.name, type: fichier.type || 'application/octet-stream', taille: fichier.size })
  const { error } = await supabase!.storage.from(depot.bucket).uploadToSignedUrl(depot.chemin, depot.jeton, fichier, { contentType: depot.type })
  if (error) {
    await retirerFichier(depot.id).catch(() => undefined)
    throw new RefusAssistant(0, `« ${fichier.name} » n'a pas pu être envoyé au coffre : ${error.message}`)
  }
  return appelerJson<FichierJoint>(`/assistant/fichiers/${depot.id}/confirmer`, 'POST')
}

export async function retirerFichier(id: string): Promise<void> {
  if (MAQUETTE) return
  await appelerJson<{ retires: number }>(`/assistant/fichiers/${encodeURIComponent(id)}`, 'DELETE')
}

/** Le texte d'une question SANS la marque des fichiers joints (ajoutée par le serveur pour le modèle), et ces fichiers. */
export function separerFichiersJoints(contenu: string): { texte: string; fichiers: string[] } {
  const i = contenu.lastIndexOf('\n\n[Fichiers joints par la personne')
  if (i < 0) return { texte: contenu, fichiers: [] }
  const noms = Array.from(contenu.slice(i).matchAll(/fichier:[0-9a-f]{32} « ([^»]+) »/g)).map((m) => m[1].trim())
  return { texte: contenu.slice(0, i), fichiers: noms }
}

/** Pose une question. Rend `true` si le flux s'est fini proprement (« fin » ou « erreur » reçus), `false` s'il a été coupé. */
export async function poserQuestion(
  question: string,
  conversationId: string | null,
  surEvenement: (evenement: EvenementFlux) => void,
  signal: AbortSignal,
  fichiers: string[] = [],
): Promise<boolean> {
  if (MAQUETTE) return fauxFlux(question, conversationId, surEvenement, signal)
  if (!baseUrl) throw new RefusAssistant(0, "L'adresse du serveur n'est pas configurée.")
  const reponse = await fetch(`${baseUrl}/assistant/message`, {
    method: 'POST',
    headers: await entetes(true),
    body: JSON.stringify({ question, ...(conversationId ? { conversationId } : {}), ...(fichiers.length ? { fichiers } : {}) }),
    signal,
  })
  if (!reponse.ok || !reponse.body) throw new RefusAssistant(reponse.status, await phraseDuServeur(reponse))
  const lecteur = reponse.body.getReader()
  const decodeur = new TextDecoder()
  let reste = ''
  let fini = false
  const traiter = (ligne: string) => {
    if (!ligne.trim()) return
    let evenement: EvenementFlux
    try {
      evenement = JSON.parse(ligne) as EvenementFlux
    } catch {
      return  // une ligne illisible ne casse pas la réponse ; la « fin » manquera, et l'écran le dira
    }
    if (evenement.type === 'fin' || evenement.type === 'erreur') fini = true
    surEvenement(evenement)
  }
  try {
    for (;;) {
      const { value, done } = await lecteur.read()
      if (done) break
      reste += decodeur.decode(value, { stream: true })
      const lignes = reste.split('\n')
      reste = lignes.pop() ?? ''
      lignes.forEach(traiter)
    }
    traiter(reste + decodeur.decode())
  } catch (erreur) {
    if (signal.aborted) return fini
    if (!fini) return false  // coupure réseau en cours de route : l'écran propose « Renvoyer »
    throw erreur
  }
  return fini
}

export async function listerConversations(): Promise<ConversationAssistant[]> {
  if (MAQUETTE) return CONVERSATIONS_EXEMPLE
  const r = await appeler<{ conversations: ConversationAssistant[] }>('/assistant/conversations', 'GET')
  return r.conversations ?? []
}

export async function relireConversation(id: string): Promise<{ conversation: ConversationAssistant; messages: MessageAssistant[]; cartes: CarteAssistant[] }> {
  if (MAQUETTE) return conversationExemple(id)
  const [conv, cartes] = await Promise.all([
    appeler<{ conversation: ConversationAssistant & { messages: MessageAssistant[] } }>(`/assistant/conversations/${encodeURIComponent(id)}`, 'GET'),
    appeler<{ actions: CarteAssistant[] }>(`/assistant/conversations/${encodeURIComponent(id)}/actions`, 'GET'),
  ])
  return { conversation: conv.conversation, messages: conv.conversation.messages ?? [], cartes: cartes.actions ?? [] }
}

// ── Lot 3b : deux lectures pour les liens (avec la session de la personne : la RLS dit ce qu'elle voit) ──
/** Une transaction (app_affaire_id) -> sa chaîne, pour le registre des transactions. Rien de lisible = null.
 *  `annee` = l'année du DERNIER évènement de la chaîne : c'est elle que le registre lit (app_registre_dossiers filtre
 *  left(date_dernier_evenement, 4) = p_annee). ⚠ Lire toutes les années d'un coup dépasse le délai de la base
 *  (« statement timeout », vu en ligne le 16/11) : on ne lit que la bonne. */
export async function transactionPourLien(appAffaireId: string): Promise<{ chaine: number | null; appDossierId: number | null; annee: number | null } | null> {
  if (MAQUETTE) return { chaine: 1, appDossierId: 7801, annee: 2026 }
  const { data, error } = await supabase!.from('app_affaire_ledger').select('app_chaine_id, app_dossier_id')
    .eq('app_affaire_id', Number(appAffaireId)).limit(1).maybeSingle()
  if (error || !data) return null
  const ligne = data as { app_chaine_id: number | null; app_dossier_id: number | null }
  let annee: number | null = null
  if (ligne.app_chaine_id != null) {
    const { data: chaine } = await supabase!.from('app_affaire_ledger').select('date, date_acte, date_annulation_app')
      .eq('app_chaine_id', ligne.app_chaine_id).limit(50)
    const dates = ((chaine ?? []) as Array<Record<string, string | null>>)
      .flatMap((l) => [l.date, l.date_acte, l.date_annulation_app])
      .map((d) => String(d ?? '').slice(0, 10)).filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d) && !d.startsWith('0000')).sort()
    annee = dates.length ? Number(dates[dates.length - 1].slice(0, 4)) : null
  }
  return { chaine: ligne.app_chaine_id ?? null, appDossierId: ligne.app_dossier_id ?? null, annee }
}

/** Une recherche (contact_search_key) -> le contact qui la porte. */
export async function contactDeLaRecherche(cle: string): Promise<string | null> {
  if (MAQUETTE) return '10354641'
  const { data, error } = await supabase!.from('app_contact_searches_current').select('hektor_contact_id')
    .eq('contact_search_key', cle).limit(1).maybeSingle()
  if (error || !data) return null
  return String((data as { hektor_contact_id: string | null }).hektor_contact_id ?? '').trim() || null
}

export type ReponseCarte = { ok: boolean; etat: EtatCarte; detail?: string; resultat?: Record<string, unknown> }

export async function validerCarte(id: string): Promise<ReponseCarte> {
  if (MAQUETTE) return attendre(900).then(() => ({ ok: true, etat: 'executee' as const, resultat: id.startsWith('carte-creation') ? OUVERTURE_EXEMPLE : id.startsWith('carte-avis') ? AVIS_EXEMPLE : { relance_id: 1 } }))
  return appeler<ReponseCarte>(`/assistant/actions/${encodeURIComponent(id)}/valider`, 'POST')
}

export async function refuserCarte(id: string): Promise<ReponseCarte> {
  if (MAQUETTE) return attendre(300).then(() => ({ ok: true, etat: 'refusee' as const }))
  return appeler<ReponseCarte>(`/assistant/actions/${encodeURIComponent(id)}/refuser`, 'POST')
}

// ── 18/11 (étape 4 §66, marche 6a) : la carte « créer » APRÈS son clic ──
/** « Rouvrir la création » : le serveur re-vérifie tout (comme au clic) et rend un ordre d'ouverture frais. */
export async function rouvrirCarte(id: string): Promise<{ ok: boolean; resultat?: OuvertureCreation | OuvertureAvis; detail?: string }> {
  if (MAQUETTE) return attendre(300).then(() => ({ ok: true, resultat: id.startsWith('carte-avis') ? AVIS_EXEMPLE : OUVERTURE_EXEMPLE }))
  return appeler(`/assistant/actions/${encodeURIComponent(id)}/rouvrir`, 'POST')
}

/** La fenêtre a créé la fiche : la carte le garde (« Estimation créée »), pour un rechargement. */
export async function noterCreationCarte(id: string, suite: { app_dossier_id: number | null; genre: 'estimation' | 'annonce' }): Promise<Record<string, unknown>> {
  if (MAQUETTE) return { cree: { ...suite, le: new Date().toISOString() } }
  const r = await appelerJson<{ resultat: Record<string, unknown> }>(`/assistant/actions/${encodeURIComponent(id)}/suite`, 'POST', suite)
  return r.resultat
}

// ── 19/11 (étape 4 chap. 6, P2) : LE PARCOURS GUIDÉ — les questions à boutons, sans modèle ──────────────────────────
// Le serveur (routers/assistant.py, P1) pose la question suivante et garde les réponses dans app_assistant_parcours, dans la
// LANGUE DE LA FENÊTRE (noms de ses cases). Un clic n'appelle jamais le modèle. Derrière l'interrupteur `assistant_parcours`
// (403 tant qu'il n'est pas ouvert pour ce compte). ⛔ Les coordonnées d'un NOUVEAU mandant ne passent pas par ici.
export type QuestionParcours = { id: string; titre: string; phrase: string; forme: string; champs: string[] }
export type EtatQuestionParcours = 'faite' | 'passee' | 'nsp' | null
export type ParcoursVue = {
  id: string
  genre: 'creation_estimation' | 'creation_annonce' | 'avis'
  etat: 'en_cours' | 'termine' | 'abandonne'
  app_dossier_id: number | null
  maj_le?: string
  profil: string | null
  question: QuestionParcours | null
  repere: { rang: number; total: number; faites: number }
  questions: Array<QuestionParcours & { etat: EtatQuestionParcours }>
  reponses: Record<string, unknown>
  fin: boolean
}
/** Une case de la fenêtre, telle que la fenêtre la montre (libellé, liste), fournie par l'App : une seule source. */
export type CaseParcours = {
  nom: string
  libelle: string
  genre: 'liste' | 'nombre' | 'texte' | 'long'
  options?: Array<{ value: string; label: string }>
  entier?: boolean
  si?: { nom: string; vaut: string }
}
export type CatalogueParcours = { cases: Record<string, CaseParcours>; typesPiece: Array<{ value: string; label: string }> }

const AUCUNE_CONVERSATION = '00000000-0000-0000-0000-000000000000'

/** Ouvert pour ce compte ? Sonde la liste (une conversation qui n'existe pas : 200 et rien, ou 403 interrupteur fermé). */
export async function parcoursOuvert(): Promise<boolean> {
  if (MAQUETTE) return true
  try {
    await appeler<{ ok: boolean }>(`/assistant/parcours?conversationId=${AUCUNE_CONVERSATION}`, 'GET')
    return true
  } catch {
    return false
  }
}

export async function parcoursDeConversation(conversationId: string): Promise<ParcoursVue[]> {
  if (MAQUETTE) return fauxParcours.filter((p) => p.conversation === conversationId).map((p) => vueFausse(p))
  const r = await appeler<{ parcours: ParcoursVue[] }>(`/assistant/parcours?conversationId=${encodeURIComponent(conversationId)}`, 'GET')
  return r.parcours
}

export async function commencerParcours(genre: 'creation_estimation' | 'creation_annonce', conversationId: string | null): Promise<ParcoursVue> {
  if (MAQUETTE) {
    const p = { id: `p${Date.now()}`.padEnd(36, '0'), conversation: conversationId, genre, reponses: {} as Record<string, unknown>, etats: {} as Record<string, EtatQuestionParcours>, etat: 'en_cours' as const }
    fauxParcours.push(p)
    return vueFausse(p)
  }
  const r = await appelerJson<{ parcours: ParcoursVue }>('/assistant/parcours', 'POST', { genre, conversationId })
  return r.parcours
}

export async function repondreParcours(id: string, question: string, geste: 'repondre' | 'passer' | 'nsp', valeurs: Record<string, unknown>): Promise<ParcoursVue> {
  if (MAQUETTE) {
    await attendre(250)
    const p = fauxParcours.find((x) => x.id === id)
    if (!p) throw new RefusAssistant(404, 'Parcours introuvable')
    for (const [k, v] of Object.entries(valeurs)) {
      if (v === '' || v === null || (Array.isArray(v) && !v.length)) delete p.reponses[k]
      else p.reponses[k] = v
    }
    p.etats[question] = geste === 'repondre' ? 'faite' : geste === 'passer' ? 'passee' : 'nsp'
    return vueFausse(p)
  }
  const r = await appelerJson<{ parcours: ParcoursVue }>(`/assistant/parcours/${encodeURIComponent(id)}/reponse`, 'POST', { question, geste, valeurs })
  return r.parcours
}

export async function noterParcoursCree(id: string, appDossierId: number | null): Promise<ParcoursVue> {
  if (MAQUETTE) {
    const p = fauxParcours.find((x) => x.id === id)
    if (p) { p.etat = 'termine'; p.app_dossier_id = appDossierId }
    return vueFausse(p!)
  }
  const r = await appelerJson<{ parcours: ParcoursVue }>(`/assistant/parcours/${encodeURIComponent(id)}/cree`, 'POST', { app_dossier_id: appDossierId })
  return r.parcours
}

// ── P2 morceau 3 (D7) : LES COORDONNÉES D'UN NOUVEAU MANDANT -- jamais par le serveur de l'assistant, jamais au modèle.
// L'écran les dépose lui-même, avec le JETON de la personne, dans le schéma privé (P3 : assistant_prive, invisible de
// l'API et de la descente) ; la fenêtre les PREND à son ouverture, et prendre, c'est effacer (règle du 19/11).
export type CoordonneesMandant = Partial<Record<'civilite' | 'nom' | 'prenom' | 'email' | 'telephone' | 'adresse' | 'cp' | 'ville', string>>
const coffreMaquette = new Map<string, CoordonneesMandant>()

export async function deposerCoordonneesMandant(parcoursId: string, coordonnees: CoordonneesMandant): Promise<number> {
  if (MAQUETTE) {
    const propres = Object.fromEntries(Object.entries(coordonnees).filter(([, v]) => String(v ?? '').trim())) as CoordonneesMandant
    if (Object.keys(propres).length) coffreMaquette.set(parcoursId, propres)
    else coffreMaquette.delete(parcoursId)
    return Object.keys(propres).length
  }
  const { data, error } = await supabase!.rpc('app_assistant_mandant_deposer', { p_parcours_id: parcoursId, p_coordonnees: coordonnees })
  if (error) throw new RefusAssistant(0, `Les coordonnées n'ont pas été gardées : ${error.message}`)
  return Number(data ?? 0)
}

export async function prendreCoordonneesMandant(parcoursId: string): Promise<CoordonneesMandant | null> {
  if (MAQUETTE) {
    const c = coffreMaquette.get(parcoursId) ?? null
    coffreMaquette.delete(parcoursId)
    return c
  }
  const { data, error } = await supabase!.rpc('app_assistant_mandant_prendre', { p_parcours_id: parcoursId })
  if (error) throw new RefusAssistant(0, `Les coordonnées du mandant n'ont pas pu être reprises : ${error.message}`)
  return (data as CoordonneesMandant | null) ?? null
}

// Mode maquette (sans base) : quatre questions pour dessiner chaque forme à l'écran (le vrai moteur en a 19, côté serveur)
type FauxParcours = { id: string; conversation: string | null; genre: 'creation_estimation' | 'creation_annonce'; reponses: Record<string, unknown>; etats: Record<string, EtatQuestionParcours>; etat: 'en_cours' | 'termine'; app_dossier_id?: number | null }
const fauxParcours: FauxParcours[] = []
const FAUSSES_QUESTIONS: QuestionParcours[] = [
  { id: 'bien', titre: 'Le bien', phrase: "Quel bien, et où ?", forme: 'cases', champs: ['type', 'agence', 'adresse_haut', 'cp', 'ville'] },
  { id: 'interieur', titre: "L'intérieur", phrase: "Combien de pièces, et comment est l'intérieur ?", forme: 'compteurs', champs: ['surfappart', 'nbpieces', 'NB_CHAMBRES', 'NB_NIVEAUX', 'EXPOSITION'] },
  { id: 'composition', titre: 'La composition', phrase: 'Pièce par pièce.', forme: 'pieces', champs: ['composition'] },
  { id: 'dehors', titre: 'Le dehors', phrase: "Qu'y a-t-il dehors ?", forme: 'cocher', champs: ['JARDIN-', 'PISCINE-', 'surfterrain', 'GARAGE_BOX'] },
  { id: 'mandant', titre: 'Le mandant', phrase: 'Qui vend ?', forme: 'mandant', champs: ['mandant_choix', 'mandant'] },
]
function vueFausse(p: FauxParcours): ParcoursVue {
  const q = FAUSSES_QUESTIONS.find((x) => !p.etats[x.id]) ?? null
  return {
    id: p.id, genre: p.genre, etat: p.etat, app_dossier_id: p.app_dossier_id ?? null, profil: p.reponses.type === '1' ? 'house' : 'apartment',  // maquette : 1 = Maison, sinon un appartement
    question: q, repere: { rang: q ? FAUSSES_QUESTIONS.indexOf(q) + 1 : FAUSSES_QUESTIONS.length, total: FAUSSES_QUESTIONS.length, faites: Object.keys(p.etats).length },
    questions: FAUSSES_QUESTIONS.map((x) => ({ ...x, etat: p.etats[x.id] ?? null })), reponses: { ...p.reponses }, fin: !q,
  }
}

/** L'App prévient l'écran de l'assistant qu'une carte « créer » a abouti (il peut être démonté : la carte se relira). */
export const EVENEMENT_CREATION_FAITE = 'gti-assistant-creation-faite'
export type CreationFaite = { carteId: string; resultat: Record<string, unknown> }

const OUVERTURE_EXEMPLE: OuvertureCreation = {
  ouvrir: 'creation_annonce', genre: 'estimation',
  cases: { propertyType: 'maison', price: '245000', surface: '125', roomCount: '5', bedroomCount: '3', landSurface: '900',
    address: '12 rue des Tilleuls', postalCode: '42700', city: 'Firminy', title: 'Maison 5 pièces avec jardin de 900 m²' },
  composition: [], mandant: { hektor_contact_id: '10354641', nom: 'Mme CLAUDE TESTCLAUDE' }, negociateur: null, photos: [],
}
const AVIS_EXEMPLE: OuvertureAvis = {
  ouvrir: 'avis_de_valeur', app_dossier_id: 32621, hektor_annonce_id: 4,  // un bien de la maquette (lib/mockData)
  champs: { etatNote: '4', pointsForts: 'Jardin plat\nProche des écoles' },
  postes: { toiture: { niveau: 'neuf', label: 'refaite 2019' } },
}
const FICHE_EXEMPLE: FicheCarte = {
  genre: 'estimation', titre: 'Maison de 125 m² à Firminy',
  chiffres: [{ libelle: 'Prix', valeur: '245 000 €' }, { libelle: 'Surface habitable', valeur: '125 m²' },
    { libelle: 'Pièces', valeur: '5', complement: 'dont 3 chambres' }, { libelle: 'Terrain', valeur: '900 m²' }],
  lignes: [{ libelle: 'Adresse', valeur: '12 rue des Tilleuls, 42700 Firminy' },
    { libelle: 'Mandant', valeur: 'Mme CLAUDE TESTCLAUDE', contact: true },
    { libelle: 'Titre', valeur: 'Maison 5 pièces avec jardin de 900 m²' }],
  composition: 0, mandant: true, negociateur: false, photos: 0, a_remplir: ['Photos', 'Composition'],
}

// ── le mode maquette ─────────────────────────────────────────────────────────
// Les exemples de la planche 3 ; une question qui contient « coupe » simule une coupure, « erreur » une erreur,
// « plafond » le refus 429, « carte » une carte à valider.

function attendre(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const minuterie = window.setTimeout(resolve, ms)
    signal?.addEventListener('abort', () => { window.clearTimeout(minuterie); resolve() })
  })
}

const CONVERSATIONS_EXEMPLE: ConversationAssistant[] = [
  { id: 'exemple-1', titre: 'Demande une baisse à 149 000 € pour la maison de La Chaise-Dieu', maj_le: '2026-11-17T10:21:00Z' },
  { id: 'exemple-2', titre: "Sur l'annonce 24935, masque la photo 480827 (la dernière).", maj_le: '2026-11-16T16:40:00Z' },
  { id: 'exemple-3', titre: 'Sur le bien 63330, passe le nombre de pièces à 6.', maj_le: '2026-11-15T13:17:00Z' },
]

function conversationExemple(id: string) {
  const conversation = CONVERSATIONS_EXEMPLE.find((c) => c.id === id) ?? { id, titre: 'Conversation' }
  const dans30min = new Date(Date.now() + 30 * 60_000).toISOString()
  const messages: MessageAssistant[] = [
    { id: 1, role: 'user', contenu: conversation.titre, cree_le: '2026-11-17T10:12:00Z' },
    {
      id: 2, role: 'assistant', cree_le: '2026-11-17T10:12:30Z',
      contenu: "C'est l'[annonce 63289](annonce:63289), en exclusivité chez Marion BILLIG DURAND. Son mandat est validé : la baisse passe par une demande à la direction. La voici, prête à partir.",
    },
  ]
  const cartes: CarteAssistant[] = [{
    id: 'carte-exemple-1', geste: 'demande_direction', etat: 'proposee', cree_le: '2026-11-17T10:12:20Z', expire_le: dans30min,
    resume: "Demander une baisse de prix — annonce 63289 « Grande maison de maitre de 131m² env avec dépendances », nouveau prix 149 000 € (aujourd'hui 154 500 €)",
    cibles: [{ type: 'annonce', numero: '63289' }],
  }]
  return Promise.resolve({ conversation, messages, cartes })
}

async function fauxFlux(question: string, conversationId: string | null, surEvenement: (e: EvenementFlux) => void, signal: AbortSignal): Promise<boolean> {
  const q = question.toLowerCase()
  if (q.includes('plafond')) throw new RefusAssistant(429, '100 questions aujourd\'hui : reprends demain')
  surEvenement({ type: 'debut', conversationId: conversationId ?? `exemple-${Date.now()}` })
  await attendre(500, signal)
  surEvenement({ type: 'outil', nom: q.includes('agenda') ? 'lire_mon_agenda' : 'chercher' })
  await attendre(700, signal)
  if (q.includes('erreur')) {
    surEvenement({ type: 'erreur', detail: "L'assistant n'a pas pu répondre" })
    return true
  }
  const avis = q.includes('avis de valeur')
  const creation = !avis && q.includes('estimation')
  const texte = avis
    ? "J'ai préparé l'avis de valeur de l'[annonce 4](annonce:4). L'éditeur reprendra le dernier avis, calculera le marché DVF et les autres sources ; rien ne sera généré avant ton clic sur « Générer »."
    : creation
    ? "J'ai préparé la création. Relis les valeurs : la fenêtre s'ouvrira déjà remplie, et rien ne sera créé avant ton clic sur « Créer ». Le [patron vierge à imprimer](patron:fiche-saisie) sert pour la prochaine fiche papier."
    : q.includes('carte') || q.includes('relance')
    ? "Je prépare la relance de [M. AVOIR TEST4](contact:10354641) pour **vendredi 20 novembre**. La voici, à valider :"
    : q.includes('objets')
      ? "Les cinq : le [mandat 18787](mandat:18787), l'[offre du 12/11](transaction:1001409), [sa recherche](recherche:344a6bbc6068564a4e2bd9df), le [rendez-vous du 18/11](rdv:2026-11-18) et la [demande en attente](demande:7801)."
      : "Voici ce que je trouve :\n\n- **3 annonces** sans aucun portail, dont l'[annonce 44506](annonce:44506) ;\n- la plus ancienne est le bien **62965**, depuis le 02/06.\n\nTu veux que je les liste ?"
  for (const mot of texte.split(/(?<= )/)) {
    if (signal.aborted) return false
    surEvenement({ type: 'texte', delta: mot })
    await attendre(40, signal)
    if (q.includes('coupe') && mot.startsWith('annonces')) return false
  }
  if (avis) {
    surEvenement({ type: 'outil', nom: 'proposer_ouvrir_avis_de_valeur' })
    surEvenement({
      type: 'carte', id: `carte-avis-${Date.now()}`, geste: 'ouvrir_avis_de_valeur',
      resume: "Ouvrir l'avis de valeur de l'annonce 4 « Appartement T3 », pré-rempli : État (sur 5) 4 ; Points forts « Jardin plat Proche des écoles » ; barème : toiture / charpente neuf / refait. L'éditeur calcule le marché DVF et les autres sources ; rien n'est généré ni envoyé tant que tu n'as pas cliqué « Générer » DANS l'éditeur",
      expire_le: new Date(Date.now() + 30 * 60_000).toISOString(),
      cibles: [{ type: 'bien', id: '32621' }],
    })
  } else if (creation) {
    surEvenement({ type: 'outil', nom: 'proposer_ouvrir_creation_annonce' })
    surEvenement({
      type: 'carte', id: `carte-creation-${Date.now()}`, geste: 'ouvrir_creation_annonce',
      resume: "Ouvrir la création d'une estimation, pré-remplie : Type de bien maison ; Prix 245 000 € ; Surface habitable 125 m² ; Pièces 5 ; Chambres 3 ; Terrain 900 m² ; mandant : Mme CLAUDE TESTCLAUDE (contact existant)",
      expire_le: new Date(Date.now() + 30 * 60_000).toISOString(),
      cibles: [{ type: 'contact', id: '10354641' }], fiche: FICHE_EXEMPLE,
    })
  } else if (q.includes('carte') || q.includes('relance')) {
    surEvenement({ type: 'outil', nom: 'proposer_creer_relance' })
    surEvenement({
      type: 'carte', id: `carte-${Date.now()}`, geste: 'creer_relance',
      resume: 'Créer une relance pour M. AVOIR TEST4 le 20/11/2026 : Rappeler pour la visite',
      expire_le: new Date(Date.now() + 30 * 60_000).toISOString(),
      cibles: [{ type: 'contact', id: '10354641' }, { type: 'bien', id: '7801' }],
    })
  }
  await attendre(200, signal)
  surEvenement({ type: 'fin', messageId: 1, enregistre: !q.includes('non enregistr') })
  return true
}
