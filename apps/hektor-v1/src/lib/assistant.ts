import { hasSupabaseEnv, supabase } from './supabase'

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
}

export type ConversationAssistant = { id: string; titre: string; cree_le?: string; maj_le?: string }
export type MessageAssistant = { id: number; role: 'user' | 'assistant'; contenu: string; cree_le: string }

export type EvenementFlux =
  | { type: 'debut'; conversationId: string }
  | { type: 'texte'; delta: string }
  | { type: 'outil'; nom: string | null }
  | { type: 'carte'; id: string; geste: string; resume: string; expire_le?: string | null; cibles?: CibleCarte[] }
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

/** Pose une question. Rend `true` si le flux s'est fini proprement (« fin » ou « erreur » reçus), `false` s'il a été coupé. */
export async function poserQuestion(
  question: string,
  conversationId: string | null,
  surEvenement: (evenement: EvenementFlux) => void,
  signal: AbortSignal,
): Promise<boolean> {
  if (MAQUETTE) return fauxFlux(question, conversationId, surEvenement, signal)
  if (!baseUrl) throw new RefusAssistant(0, "L'adresse du serveur n'est pas configurée.")
  const reponse = await fetch(`${baseUrl}/assistant/message`, {
    method: 'POST',
    headers: await entetes(true),
    body: JSON.stringify(conversationId ? { question, conversationId } : { question }),
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
  if (MAQUETTE) return attendre(900).then(() => ({ ok: true, etat: 'executee' as const, resultat: { relance_id: 1 } }))
  return appeler<ReponseCarte>(`/assistant/actions/${encodeURIComponent(id)}/valider`, 'POST')
}

export async function refuserCarte(id: string): Promise<ReponseCarte> {
  if (MAQUETTE) return attendre(300).then(() => ({ ok: true, etat: 'refusee' as const }))
  return appeler<ReponseCarte>(`/assistant/actions/${encodeURIComponent(id)}/refuser`, 'POST')
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
  const texte = q.includes('carte') || q.includes('relance')
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
  if (q.includes('carte') || q.includes('relance')) {
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
