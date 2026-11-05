// A.2 lot 5, piece L5-1 (05/11/2026) -- LA RECEPTION DES AVIS DE YOUTRUST. Sans dependance (essai : test_logique.mjs).
//
// Ce que fait la fonction, et RIEN d'autre (plan signature, lot 5 ; doc Youtrust relue le 05/11) :
//   1. verifie la signature `X-Yousign-Signature-256` = "sha256=" + HMAC-SHA256 hex du corps BRUT (401 sinon) ;
//   2. range l'avis dans app_signature_event (`event_id` = cle primaire : un avis recu deux fois ne fait qu'une ligne) ;
//   3. s'assure qu'un travail `youtrust_sync_signature` EN ATTENTE existe pour la demande -- c'est le worker qui relit
//      la demande chez Youtrust (un avis peut arriver plusieurs fois et DANS LE DESORDRE : on ne le croit pas, on relit) ;
//   4. repond 200 tout de suite (Youtrust exige moins d'1 s).
// ⚠ Un avis d'une demande INCONNUE (creee hors de l'app) est garde, sans travail. ⚠ Une erreur de base rend 500 :
//   Youtrust renverra l'avis (8 nouvelles tentatives sur ~4 jours) ; au renvoi, le doublon est ignore MAIS le travail est
//   quand meme assure -- un travail rate une fois n'est jamais perdu.
// ⚠ Pas de jeton de connexion (Youtrust n'en a pas) : la fonction se deploie SANS verify_jwt ; sa seule protection est
//   le HMAC, et elle n'ecrit que l'avis et le travail.

export type Avis = {
  event_id?: string
  event_name?: string
  event_time?: string | number
  sandbox?: boolean
  data?: { signature_request?: { id?: string; external_id?: string | null; status?: string }; signer?: { id?: string } | null }
}
export type LigneAvis = {
  event_id: string
  provider: 'youtrust'
  event_name: string
  provider_request_id: string | null
  provider_signer_id: string | null
  sandbox: boolean | null
  event_time: string | null
  payload: Avis
}
export type Demande = { id: string; app_dossier_id: number | null; hektor_annonce_id: string | null }
export type Base = {
  rangerAvis(ligne: LigneAvis): Promise<'nouveau' | 'doublon'>
  trouverDemande(providerRequestId: string): Promise<Demande | null>
  travailEnAttente(signatureRequestId: string): Promise<boolean>
  poserTravail(travail: Record<string, unknown>): Promise<void>
}
export type Reponse = { statut: number; corps: Record<string, unknown> }

const enHex = (octets: ArrayBuffer) => Array.from(new Uint8Array(octets)).map((o) => o.toString(16).padStart(2, '0')).join('')

// Comparaison a duree constante (meme longueur d'abord : une longueur differente est deja un refus).
function egalConstant(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let diff = 0
  for (let i = 0; i < a.length; i += 1) diff |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return diff === 0
}

export async function signatureValide(corps: Uint8Array, entete: string | null, secret: string): Promise<boolean> {
  if (!entete || !secret) return false
  const cle = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const attendu = `sha256=${enHex(await crypto.subtle.sign('HMAC', cle, corps))}`
  return egalConstant(entete.trim().toLowerCase(), attendu)
}

export function ligneDeLAvis(avis: Avis): LigneAvis | null {
  const eventId = String(avis?.event_id ?? '').trim()
  const nom = String(avis?.event_name ?? '').trim()
  if (!eventId || !nom) return null
  const secondes = Number(avis.event_time)
  return {
    event_id: eventId,
    provider: 'youtrust',
    event_name: nom,
    provider_request_id: String(avis.data?.signature_request?.id ?? '').trim() || null,
    provider_signer_id: String(avis.data?.signer?.id ?? '').trim() || null,
    sandbox: typeof avis.sandbox === 'boolean' ? avis.sandbox : null,
    // `event_time` est une epoque Unix (en secondes) chez Youtrust ; une valeur illisible n'invente pas de date.
    event_time: Number.isFinite(secondes) && secondes > 0 ? new Date(secondes * 1000).toISOString() : null,
    payload: avis,
  }
}

export async function traiterAvis(entree: { methode: string; corps: Uint8Array; entete: string | null }, secret: string, base: Base): Promise<Reponse> {
  if (entree.methode !== 'POST') return { statut: 405, corps: { erreur: 'POST seulement' } }
  if (!secret) return { statut: 500, corps: { erreur: 'secret du webhook absent (YOUTRUST_WEBHOOK_SECRET)' } }
  if (!(await signatureValide(entree.corps, entree.entete, secret))) return { statut: 401, corps: { erreur: 'signature invalide' } }
  let avis: Avis
  try { avis = JSON.parse(new TextDecoder().decode(entree.corps)) } catch { return { statut: 400, corps: { erreur: 'corps illisible' } } }
  const ligne = ligneDeLAvis(avis)
  if (!ligne) return { statut: 400, corps: { erreur: 'event_id ou event_name absent' } }
  try {
    const rangement = await base.rangerAvis(ligne)
    if (!ligne.provider_request_id) return { statut: 200, corps: { recu: ligne.event_id, rangement, travail: 'sans_demande' } }
    const demande = await base.trouverDemande(ligne.provider_request_id)
    if (!demande) return { statut: 200, corps: { recu: ligne.event_id, rangement, travail: 'demande_inconnue' } }
    if (await base.travailEnAttente(demande.id)) return { statut: 200, corps: { recu: ligne.event_id, rangement, travail: 'deja_en_attente' } }
    await base.poserTravail({
      job_type: 'youtrust_sync_signature',
      app_dossier_id: demande.app_dossier_id,
      hektor_annonce_id: demande.hektor_annonce_id,
      payload_json: { signature_request_id: demande.id, provider_request_id: ligne.provider_request_id, event_id: ligne.event_id, event_name: ligne.event_name },
      status: 'pending',
      priority: 22,
      requested_by: null,
    })
    return { statut: 200, corps: { recu: ligne.event_id, rangement, travail: 'pose' } }
  } catch (e) {
    // 500 : Youtrust renverra. Le message reste court (aucune donnee personnelle dans la reponse).
    return { statut: 500, corps: { erreur: `base : ${e instanceof Error ? e.message.slice(0, 200) : 'erreur'}` } }
  }
}
