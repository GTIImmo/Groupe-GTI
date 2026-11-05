// A.2 lot 5, piece L5-1 (05/11/2026) -- fonction Supabase `youtrust-webhook` : le branchement de logique.ts sur la base.
// ⚠ DEPLOIEMENT (geste de Frederic, jamais par un push) : SANS verification de jeton (Youtrust n'en envoie pas) --
//     npx supabase functions deploy youtrust-webhook --no-verify-jwt --project-ref <projet>
//   et le secret de l'abonnement Youtrust (32 caracteres, donne par l'app Youtrust a la creation) :
//     npx supabase secrets set YOUTRUST_WEBHOOK_SECRET=<secret> --project-ref <projet>
// L'URL a donner a Youtrust : https://<projet>.supabase.co/functions/v1/youtrust-webhook
import { createClient } from 'jsr:@supabase/supabase-js@2'
import { traiterAvis, type Base } from './logique.ts'

const url = Deno.env.get('SUPABASE_URL') ?? ''
const cleService = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
const secret = Deno.env.get('YOUTRUST_WEBHOOK_SECRET')?.trim() ?? ''
const client = createClient(url, cleService, { auth: { persistSession: false } })

const base: Base = {
  async rangerAvis(ligne) {
    const { data, error } = await client.from('app_signature_event')
      .upsert(ligne, { onConflict: 'event_id', ignoreDuplicates: true })
      .select('event_id')
    if (error) throw new Error(error.message)
    return Array.isArray(data) && data.length ? 'nouveau' : 'doublon'
  },
  async trouverDemande(providerRequestId) {
    const { data, error } = await client.from('app_signature_request')
      .select('id,app_dossier_id,hektor_annonce_id')
      .eq('provider_request_id', providerRequestId)
      .maybeSingle()
    if (error) throw new Error(error.message)
    return data ?? null
  },
  async travailEnAttente(signatureRequestId) {
    const { data, error } = await client.from('app_console_job')
      .select('id')
      .eq('job_type', 'youtrust_sync_signature')
      .eq('status', 'pending')
      .eq('payload_json->>signature_request_id', signatureRequestId)
      .limit(1)
    if (error) throw new Error(error.message)
    return Array.isArray(data) && data.length > 0
  },
  async poserTravail(travail) {
    const { error } = await client.from('app_console_job').insert(travail)
    if (error) throw new Error(error.message)
  },
}

Deno.serve(async (request) => {
  const corps = new Uint8Array(await request.arrayBuffer())
  const r = await traiterAvis({ methode: request.method, corps, entete: request.headers.get('x-yousign-signature-256') }, secret, base)
  if (r.statut >= 400) console.warn(`[youtrust-webhook] ${r.statut} ${JSON.stringify(r.corps)}`)
  return new Response(JSON.stringify(r.corps), { status: r.statut, headers: { 'Content-Type': 'application/json' } })
})
