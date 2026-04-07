import { createClient } from 'jsr:@supabase/supabase-js@2'

type DiffusionTargetRow = {
  app_dossier_id: number
  hektor_annonce_id: number
  hektor_broadcast_id: string
  portal_key: string | null
  target_state: 'enabled' | 'disabled'
}

type DossierRow = {
  app_dossier_id: number
  hektor_annonce_id: number
  validation_diffusion_state: string | null
  agence_nom: string | null
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders,
      ...(init.headers ?? {}),
    },
  })
}

function normalizeText(value: string | null | undefined) {
  return (value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ')
}

function isValidationApproved(value: string | null | undefined) {
  const normalized = normalizeText(value)
  return normalized === 'oui' || normalized === 'valide' || normalized === 'validee' || normalized === 'validation ok' || normalized === 'ok'
}

function normalizeHektorMessage(message: string | undefined) {
  return (message ?? '').replace(/Ã‚/g, ' ').replace(/\s+/g, ' ').trim()
}

function parseMaybeJson(text: string) {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function toIsoNow() {
  return new Date().toISOString()
}

function requireEnv(name: string) {
  const value = Deno.env.get(name)?.trim()
  if (!value) throw new Error(`Missing environment variable: ${name}`)
  return value
}

async function createClients(authHeader: string | null) {
  const supabaseUrl = requireEnv('SUPABASE_URL')
  const anonKey = requireEnv('SUPABASE_ANON_KEY')
  const serviceRoleKey = requireEnv('SUPABASE_SERVICE_ROLE_KEY')

  const userClient = createClient(supabaseUrl, anonKey, {
    global: {
      headers: authHeader ? { Authorization: authHeader } : {},
    },
  })
  const adminClient = createClient(supabaseUrl, serviceRoleKey)
  return { userClient, adminClient }
}

async function assertAuthenticatedUser(userClient: ReturnType<typeof createClient>) {
  const { data, error } = await userClient.auth.getUser()
  if (error || !data.user) throw new Error('Utilisateur non authentifie')
  return data.user
}

async function loadDossier(adminClient: ReturnType<typeof createClient>, appDossierId: number) {
  const { data, error } = await adminClient
    .from('app_dossiers_current')
    .select('app_dossier_id,hektor_annonce_id,validation_diffusion_state,agence_nom')
    .eq('app_dossier_id', appDossierId)
    .maybeSingle()
  if (error || !data) throw new Error(error?.message ?? `Dossier introuvable: ${appDossierId}`)
  return data as DossierRow
}

async function loadTargets(adminClient: ReturnType<typeof createClient>, appDossierId: number) {
  const { data, error } = await adminClient
    .from('app_diffusion_target')
    .select('app_dossier_id,hektor_annonce_id,hektor_broadcast_id,portal_key,target_state')
    .eq('app_dossier_id', appDossierId)
    .order('portal_key', { ascending: true })
  if (error) throw new Error(error.message)
  return (data ?? []) as DiffusionTargetRow[]
}

async function loadAgencyTargets(adminClient: ReturnType<typeof createClient>, agenceNom: string | null | undefined) {
  const normalizedAgency = normalizeText(agenceNom)
  if (!normalizedAgency) return []
  const { data, error } = await adminClient
    .from('app_diffusion_agency_target')
    .select('agence_nom,portal_key,hektor_broadcast_id,is_active')
    .eq('is_active', 1)
  if (error) throw new Error(error.message)
  return (data ?? []).filter((item) => normalizeText(item.agence_nom) === normalizedAgency)
}

async function replaceTargetsFromAgencyDefaults(
  adminClient: ReturnType<typeof createClient>,
  dossier: DossierRow,
  actorName: string | null,
  actorRole: string,
  targetState: 'enabled' | 'disabled',
) {
  const agencyTargets = await loadAgencyTargets(adminClient, dossier.agence_nom)
  if (agencyTargets.length === 0) throw new Error(`Aucun mapping agence pour '${dossier.agence_nom ?? ''}'`)
  const now = toIsoNow()
  const payload = agencyTargets.map((item) => ({
    app_dossier_id: dossier.app_dossier_id,
    hektor_annonce_id: dossier.hektor_annonce_id,
    hektor_broadcast_id: String(item.hektor_broadcast_id),
    portal_key: item.portal_key,
    target_state: targetState,
    source_ref: targetState === 'enabled' ? 'accepted_default' : 'console_seed',
    note: targetState === 'enabled' ? 'Activation par defaut suite a acceptation' : 'Passerelles proposees par defaut dans la console diffusion',
    requested_by_role: actorRole,
    requested_by_name: actorName,
    requested_at: now,
    last_applied_at: null,
    last_apply_status: null,
    last_apply_error: null,
    updated_at: now,
  }))
  const { error: deleteError } = await adminClient.from('app_diffusion_target').delete().eq('app_dossier_id', dossier.app_dossier_id)
  if (deleteError) throw new Error(deleteError.message)
  const { data, error } = await adminClient.from('app_diffusion_target').insert(payload).select('app_dossier_id,hektor_annonce_id,hektor_broadcast_id,portal_key,target_state')
  if (error) throw new Error(error.message)
  return (data ?? []) as DiffusionTargetRow[]
}

let cachedHektorJwt: string | null = null

async function authenticateHektor() {
  const baseUrl = requireEnv('HEKTOR_API_BASE_URL').replace(/\/+$/, '')
  const clientId = requireEnv('HEKTOR_CLIENT_ID')
  const clientSecret = requireEnv('HEKTOR_CLIENT_SECRET')

  const authResponse = await fetch(
    `${baseUrl}/Api/OAuth/Authenticate/?client_id=${encodeURIComponent(clientId)}&client_secret=${encodeURIComponent(clientSecret)}&grant_type=client_credentials`,
    { method: 'POST' },
  )
  const authText = await authResponse.text()
  const authParsed = parseMaybeJson(authText) as Record<string, unknown>
  if (!authResponse.ok || !authParsed || typeof authParsed !== 'object' || !authParsed.access_token) {
    throw new Error(typeof authParsed === 'string' ? authParsed : JSON.stringify(authParsed))
  }

  const ssoResponse = await fetch(
    `${baseUrl}/Api/OAuth/Sso/?token=${encodeURIComponent(String(authParsed.access_token))}&scope=sso&client_id=${encodeURIComponent(clientId)}`,
    { method: 'POST' },
  )
  const ssoText = await ssoResponse.text()
  const ssoParsed = parseMaybeJson(ssoText) as Record<string, unknown>
  if (!ssoResponse.ok || !ssoParsed || typeof ssoParsed !== 'object' || !ssoParsed.jwt) {
    throw new Error(typeof ssoParsed === 'string' ? ssoParsed : JSON.stringify(ssoParsed))
  }

  cachedHektorJwt = String(ssoParsed.jwt)
  return cachedHektorJwt
}

async function callHektor(path: string, init: RequestInit = {}, retry = true) {
  const baseUrl = requireEnv('HEKTOR_API_BASE_URL').replace(/\/+$/, '')
  if (!cachedHektorJwt) {
    await authenticateHektor()
  }
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      jwt: cachedHektorJwt ?? '',
      ...(init.headers ?? {}),
    },
  })
  const refresh = response.headers.get('x-refresh-token')
  if (refresh) cachedHektorJwt = refresh
  const text = await response.text()
  const parsed = parseMaybeJson(text)
  if (response.status === 403 && typeof parsed === 'string' && parsed.toLowerCase().includes('expired token') && retry) {
    cachedHektorJwt = null
    await authenticateHektor()
    return callHektor(path, init, false)
  }
  if (!response.ok) {
    throw new Error(typeof parsed === 'string' ? parsed : JSON.stringify(parsed))
  }
  return { response, parsed, rawText: text }
}

async function fetchAnnonceDetail(annonceId: string) {
  const version = Deno.env.get('HEKTOR_API_VERSION')?.trim() || 'v2'
  const { parsed } = await callHektor(`/Api/Annonce/AnnonceById/?id=${encodeURIComponent(annonceId)}&version=${encodeURIComponent(version)}`)
  return parsed as Record<string, unknown>
}

function extractDiffusable(detailPayload: Record<string, unknown>) {
  const data = detailPayload?.data
  if (data && typeof data === 'object') {
    const candidates = [Reflect.get(data, 'annonce'), Reflect.get(data, 'keyData'), data]
    for (const candidate of candidates) {
      if (candidate && typeof candidate === 'object') {
        const value = Reflect.get(candidate, 'diffusable')
        if (value != null) return String(value)
      }
    }
  }
  return null
}

async function tryDiffuseRequest(annonceId: string) {
  const version = Deno.env.get('HEKTOR_API_VERSION')?.trim() || 'v2'
  const attempts: Array<{ method: 'POST' | 'GET'; params: Record<string, string> }> = [
    { method: 'POST', params: { idAnnonce: annonceId, version } },
    { method: 'GET', params: { idAnnonce: annonceId, version } },
    { method: 'POST', params: { id: annonceId, version } },
    { method: 'GET', params: { id: annonceId, version } },
  ]
  const errors: string[] = []
  for (const attempt of attempts) {
    const query = new URLSearchParams(attempt.params)
    try {
      const { rawText } = await callHektor(`/Api/Annonce/Diffuse/?${query.toString()}`, { method: attempt.method })
      return rawText.slice(0, 500) || `${attempt.method} ok`
    } catch (error) {
      errors.push(`${attempt.method} ${JSON.stringify(attempt.params)} => ${normalizeHektorMessage(error instanceof Error ? error.message : 'Erreur Hektor')}`)
    }
  }
  throw new Error(errors.join(' | '))
}

async function ensureDiffusable(annonceId: string, dryRun: boolean) {
  const detail = await fetchAnnonceDetail(annonceId)
  const current = extractDiffusable(detail)
  if (current === '1') return { changed: false, result: 'already_diffusable' }
  if (dryRun) return { changed: true, result: 'dry_run' }
  try {
    const responsePreview = await tryDiffuseRequest(annonceId)
    return { changed: true, result: responsePreview }
  } catch (error) {
    const message = normalizeHektorMessage(error instanceof Error ? error.message : 'Erreur Hektor')
    try {
      const detailAfterError = await fetchAnnonceDetail(annonceId)
      if (extractDiffusable(detailAfterError) === '1') {
        return { changed: true, result: `confirmed_after_diffuse_error: ${message}` }
      }
    } catch {
      // no-op
    }
    return { changed: true, result: `diffuse_unconfirmed: ${message}` }
  }
}

async function applyPortalChange(action: 'add' | 'remove', annonceId: string, broadcastId: string) {
  const path = action === 'add' ? '/Api/Passerelle/addAnnonceToPasserelle/' : '/Api/Passerelle/removeAnnonceToPasserelle/'
  const method = action === 'add' ? 'PUT' : 'DELETE'
  const params = new URLSearchParams({
    idPasserelle: broadcastId,
    idAnnonce: annonceId,
  })
  const { parsed } = await callHektor(`${path}?${params.toString()}`, { method })
  return parsed
}

async function runApply(adminClient: ReturnType<typeof createClient>, dossier: DossierRow, requestedBy: string | null, dryRun: boolean, ensureDiffusableFlag: boolean, resetToAgencyDefaults: boolean) {
  let targets = await loadTargets(adminClient, dossier.app_dossier_id)
  if ((resetToAgencyDefaults || targets.length === 0) && dossier.agence_nom) {
    targets = await replaceTargetsFromAgencyDefaults(adminClient, dossier, requestedBy, resetToAgencyDefaults ? 'system' : 'app', resetToAgencyDefaults ? 'enabled' : 'disabled')
  }
  if (targets.length === 0) throw new Error(`Aucune cible de diffusion pour app_dossier_id=${dossier.app_dossier_id}`)

  let diffusableChanged = false
  let diffusableResult = 'not_managed_in_console'
  let observedDiffusable = null as string | null
  if (ensureDiffusableFlag) {
    try {
      const ensureResult = await ensureDiffusable(String(dossier.hektor_annonce_id), dryRun)
      diffusableChanged = ensureResult.changed
      diffusableResult = normalizeHektorMessage(ensureResult.result)
      if (!dryRun) {
        try {
          const detailAfter = await fetchAnnonceDetail(String(dossier.hektor_annonce_id))
          observedDiffusable = extractDiffusable(detailAfter)
        } catch (error) {
          observedDiffusable = null
          diffusableResult = normalizeHektorMessage(`${diffusableResult} | detail_read_error: ${error instanceof Error ? error.message : 'Erreur detail'}`)
        }
        if (observedDiffusable !== '1') {
          return {
            app_dossier_id: dossier.app_dossier_id,
            hektor_annonce_id: String(dossier.hektor_annonce_id),
            dry_run: dryRun,
            diffusable_changed: diffusableChanged,
            diffusable_result: diffusableResult,
            observed_diffusable: observedDiffusable,
            validation_state: dossier.validation_diffusion_state,
            validation_approved: isValidationApproved(dossier.validation_diffusion_state),
            waiting_on_hektor: true,
            waiting_message: isValidationApproved(dossier.validation_diffusion_state)
              ? "En attente de mise a jour Hektor. Le bien n'est pas encore confirme en diffusable."
              : "Action Hektor non appliquee : l'annonce est encore en validation = non. Ouvre Hektor pour corriger la validation, puis relance.",
            current_enabled_count: 0,
            targets_count: targets.length,
            to_add_count: 0,
            to_remove_count: 0,
            applied: [],
            failed: [],
            pending: [],
          }
        }
      }
    } catch (error) {
      return {
        app_dossier_id: dossier.app_dossier_id,
        hektor_annonce_id: String(dossier.hektor_annonce_id),
        dry_run: dryRun,
        diffusable_changed: diffusableChanged,
        diffusable_result: normalizeHektorMessage(error instanceof Error ? error.message : 'Erreur diffusable'),
        observed_diffusable: observedDiffusable,
        validation_state: dossier.validation_diffusion_state,
        validation_approved: isValidationApproved(dossier.validation_diffusion_state),
        waiting_on_hektor: true,
        waiting_message: "Action Hektor envoyee, mais le retour serveur n'est pas assez propre pour confirmer automatiquement le resultat.",
        current_enabled_count: 0,
        targets_count: targets.length,
        to_add_count: 0,
        to_remove_count: 0,
        applied: [],
        failed: [],
        pending: [],
      }
    }
  }

  const toAdd = targets.filter((item) => item.target_state === 'enabled')
  const toRemove = targets.filter((item) => item.target_state === 'disabled')
  const applied: Array<Record<string, unknown>> = []
  const failed: Array<Record<string, unknown>> = []

  for (const target of toAdd) {
    if (dryRun) {
      applied.push({ action: 'add', portal_key: target.portal_key, broadcast_id: target.hektor_broadcast_id, dry_run: true })
      continue
    }
    try {
      const parsed = await applyPortalChange('add', String(dossier.hektor_annonce_id), target.hektor_broadcast_id)
      applied.push({ action: 'add', portal_key: target.portal_key, broadcast_id: target.hektor_broadcast_id, result: parsed })
    } catch (error) {
      failed.push({ action: 'add', portal_key: target.portal_key, broadcast_id: target.hektor_broadcast_id, error: error instanceof Error ? normalizeHektorMessage(error.message) : 'Erreur Hektor' })
    }
  }

  for (const target of toRemove) {
    if (dryRun) {
      applied.push({ action: 'remove', portal_key: target.portal_key, broadcast_id: target.hektor_broadcast_id, dry_run: true })
      continue
    }
    try {
      const parsed = await applyPortalChange('remove', String(dossier.hektor_annonce_id), target.hektor_broadcast_id)
      applied.push({ action: 'remove', portal_key: target.portal_key, broadcast_id: target.hektor_broadcast_id, result: parsed })
    } catch (error) {
      failed.push({ action: 'remove', portal_key: target.portal_key, broadcast_id: target.hektor_broadcast_id, error: error instanceof Error ? normalizeHektorMessage(error.message) : 'Erreur Hektor' })
    }
  }

  return {
    app_dossier_id: dossier.app_dossier_id,
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    dry_run: dryRun,
    diffusable_changed: diffusableChanged,
    diffusable_result: diffusableResult,
    observed_diffusable: observedDiffusable,
    validation_state: dossier.validation_diffusion_state,
    validation_approved: isValidationApproved(dossier.validation_diffusion_state),
    waiting_on_hektor: false,
    waiting_message: null,
    current_enabled_count: toAdd.length,
    targets_count: targets.length,
    to_add_count: toAdd.length,
    to_remove_count: toRemove.length,
    applied,
    failed,
    pending: [],
  }
}

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    if (request.method !== 'POST') {
      return jsonResponse({ ok: false, error: 'Method not allowed' }, { status: 405 })
    }

    const authHeader = request.headers.get('Authorization')
    const { userClient, adminClient } = await createClients(authHeader)
    const user = await assertAuthenticatedUser(userClient)

    const body = await request.json().catch(() => ({}))
    const action = String(body?.action ?? '').trim()
    const appDossierId = Number(body?.appDossierId)
    const dryRun = Boolean(body?.dryRun)

    if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
      return jsonResponse({ ok: false, error: 'appDossierId invalide' }, { status: 400 })
    }

    const dossier = await loadDossier(adminClient, appDossierId)
    const actorName = user.email ?? user.id

    if (action === 'apply') {
      const payload = await runApply(adminClient, dossier, actorName, dryRun, Boolean(body?.ensureDiffusable), false)
      return jsonResponse({ ok: true, payload })
    }

    if (action === 'accept') {
      const payload = await runApply(adminClient, dossier, actorName, dryRun, true, true)
      return jsonResponse({ ok: true, payload })
    }

    return jsonResponse({ ok: false, error: 'Action inconnue' }, { status: 400 })
  } catch (error) {
    return jsonResponse(
      { ok: false, error: error instanceof Error ? error.message : 'Erreur interne' },
      { status: 500 },
    )
  }
})
