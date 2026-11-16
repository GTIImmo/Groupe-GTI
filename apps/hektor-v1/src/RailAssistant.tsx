import { useCallback, useEffect, useState } from 'react'
import { loadAppSettingValeur } from './lib/api'
import { hasSupabaseEnv, supabase } from './lib/supabase'
import './rail-assistant.css'

// ─────────────────────────────────────────────────────────────────────────────
// Étape 4 de l'assistant IA, lot 1 (17/11/2026) -- LE RAIL DE L'ASSISTANT.
// Maquette VALIDÉE le 17/11 (« Je valide ») : notice/ETAPE4_MAQUETTE_ACCUEIL_DESIGN_2026-11-17.md §5 sexies,
// planches 20 (admin ouvert), 21 (replié), 22 (négociateur), 18 (pièces). Plan : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §11.
//
// ⛔ L'INTERRUPTEUR `accueil_assistant` (app_setting), lu au démarrage comme `registre_transactions_ecran` :
//   absent / off = le rail d'aujourd'hui, à l'identique ; 'admin' = les admins ; 'on' = tout le monde ;
//   sinon une liste d'adresses séparées par des virgules (décision du 17/11 : « Moi seul » d'abord).
// ⛔ Les conversations et les cartes sont lues avec la session de la personne ; l'admin, qui relit celles des
//   autres (règle de l'étape 1), ne voit dans SON rail que les siennes (filtre user_id).
// ─────────────────────────────────────────────────────────────────────────────

export type ConversationRail = { id: string; titre: string; enAttente: number }

export const EVENEMENT_ASSISTANT_OUVRIR = 'assistant:ouvrir'   // detail : { conversationId: string | null }
export const EVENEMENT_ASSISTANT_CHANGE = 'assistant:change'   // une question posée, une carte validée : relire

const NOMBRE_CONVERSATIONS = 3
const RELIRE_TOUTES_LES_MS = 60_000

// Mode maquette (sans base) : les exemples de la planche 20, pour comparer l'écran à la maquette.
const EXEMPLES: ConversationRail[] = [
  { id: 'exemple-1', titre: 'Demande une baisse à 149 000 € pour la maison de La Chaise-Dieu', enAttente: 1 },
  { id: 'exemple-2', titre: "Sur l'annonce 24935, masque la photo 480827 (la dernière).", enAttente: 0 },
  { id: 'exemple-3', titre: 'Sur le bien 63330, passe le nombre de pièces à 6.', enAttente: 0 },
]

export function accueilAssistantPour(cran: string | null | undefined, email: string | null | undefined, isAdmin: boolean): boolean {
  const valeur = String(cran ?? '').trim().toLowerCase()
  if (!valeur || ['off', 'false', '0', 'no'].includes(valeur)) return false
  if (['on', 'true', '1', 'yes'].includes(valeur)) return true
  if (valeur === 'admin') return isAdmin
  const moi = String(email ?? '').trim().toLowerCase()
  return Boolean(moi) && valeur.split(/[\s,;]+/).filter(Boolean).includes(moi)
}

export function useAccueilAssistant(connecte: boolean, email: string | null | undefined, isAdmin: boolean): boolean {
  const [cran, setCran] = useState<string | null | undefined>(undefined)
  useEffect(() => {
    if (hasSupabaseEnv && !connecte) {
      setCran(undefined)
      return
    }
    let annule = false
    void loadAppSettingValeur('accueil_assistant').then((valeur) => {
      if (!annule) setCran(valeur)
    })
    return () => {
      annule = true
    }
  }, [connecte])
  return accueilAssistantPour(cran, email, isAdmin)
}

export function useConversationsRail(actif: boolean, userId: string | null | undefined) {
  const [conversations, setConversations] = useState<ConversationRail[]>([])
  const [enAttente, setEnAttente] = useState(0)

  const relire = useCallback(async () => {
    if (!actif) return
    if (!hasSupabaseEnv || !supabase) {
      setConversations(EXEMPLES)
      setEnAttente(EXEMPLES.reduce((n, c) => n + c.enAttente, 0))
      return
    }
    if (!userId) return
    try {
      const [convs, cartes] = await Promise.all([
        supabase.from('app_assistant_conversation').select('id,titre')
          .eq('user_id', userId).eq('archivee', false).order('maj_le', { ascending: false }).limit(NOMBRE_CONVERSATIONS),
        supabase.from('app_assistant_action').select('conversation_id')
          .eq('user_id', userId).eq('etat', 'proposee').gt('expire_le', new Date().toISOString()).limit(200),
      ])
      if (convs.error || cartes.error) return  // une lecture ratée garde l'affichage d'avant, sans inventer un zéro
      const parConversation = new Map<string, number>()
      for (const ligne of (cartes.data ?? []) as Array<{ conversation_id: string | null }>) {
        const id = String(ligne.conversation_id ?? '')
        if (id) parConversation.set(id, (parConversation.get(id) ?? 0) + 1)
      }
      setConversations(((convs.data ?? []) as Array<{ id: string; titre: string | null }>).map((c) => ({
        id: c.id,
        titre: String(c.titre ?? '').trim() || 'Conversation sans titre',
        enAttente: parConversation.get(c.id) ?? 0,
      })))
      setEnAttente((cartes.data ?? []).length)
    } catch {
      // idem : on garde ce qu'on affichait
    }
  }, [actif, userId])

  useEffect(() => {
    if (!actif) return
    void relire()
    const minuterie = window.setInterval(() => { void relire() }, RELIRE_TOUTES_LES_MS)
    const surChangement = () => { void relire() }
    window.addEventListener(EVENEMENT_ASSISTANT_CHANGE, surChangement)
    return () => {
      window.clearInterval(minuterie)
      window.removeEventListener(EVENEMENT_ASSISTANT_CHANGE, surChangement)
    }
  }, [actif, relire])

  return { conversations, enAttente }
}

// Lot 2 : le clic part souvent d'un autre écran, quand l'Accueil n'est pas encore monté pour entendre l'évènement.
// La demande est donc GARDÉE ici, et l'Accueil la prend en arrivant (prendreDemandeConversation).
let demandeEnAttente: { conversationId: string | null } | null = null

export function ouvrirConversation(conversationId: string | null) {
  demandeEnAttente = { conversationId }
  window.dispatchEvent(new CustomEvent(EVENEMENT_ASSISTANT_OUVRIR, { detail: { conversationId } }))
}

export function prendreDemandeConversation(): { conversationId: string | null } | null {
  const demande = demandeEnAttente
  demandeEnAttente = null
  return demande
}

export function signalerChangementAssistant() {
  window.dispatchEvent(new Event(EVENEMENT_ASSISTANT_CHANGE))
}

// Les branches de l'Accueil : les 3 dernières conversations, puis « Toutes les conversations ».
// Rail replié : la même liste devient une bulle, au survol ou au clavier (rail-assistant.css).
export function BranchesAccueil(props: {
  conversations: ConversationRail[]
  onOuvrir: (conversationId: string | null) => void
}) {
  return (
    <div className="ra-kids" role="group" aria-label="Conversations de l'assistant">
      <span className="ra-bulle-titre" aria-hidden="true">Assistant</span>
      <button type="button" className="ra-kid ra-kid-new" onClick={() => props.onOuvrir(null)}>
        <span className="t">Nouvelle conversation</span>
      </button>
      {props.conversations.map((c) => (
        <button key={c.id} type="button" className="ra-kid" title={c.titre} onClick={() => props.onOuvrir(c.id)}>
          <span className="t">{c.titre}</span>
          {c.enAttente > 0 ? (
            <span className="ra-dot" role="img" aria-label={c.enAttente > 1 ? `${c.enAttente} cartes attendent ta validation` : 'Une carte attend ta validation'} />
          ) : null}
        </button>
      ))}
      <button type="button" className="ra-kid ra-kid-more" onClick={() => props.onOuvrir('toutes')}>
        <span className="t">Toutes les conversations</span>
      </button>
    </div>
  )
}
