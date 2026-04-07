import { createClient } from 'jsr:@supabase/supabase-js@2'

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

async function assertAdmin(userClient: ReturnType<typeof createClient>, adminClient: ReturnType<typeof createClient>) {
  const { data, error } = await userClient.auth.getUser()
  if (error || !data.user) throw new Error('Utilisateur non authentifie')
  let profileQuery = await adminClient
    .from('app_user_profile')
    .select('id,email,role,is_active')
    .eq('id', data.user.id)
    .maybeSingle()

  if (!profileQuery.data && data.user.email) {
    profileQuery = await adminClient
      .from('app_user_profile')
      .select('id,email,role,is_active')
      .ilike('email', data.user.email)
      .maybeSingle()
  }

  const profile = profileQuery.data
  const profileError = profileQuery.error
  if (profileError || !profile) {
    throw new Error(profileError?.message ?? `Profil admin introuvable pour ${data.user.email ?? data.user.id}`)
  }
  if (!profile.is_active || !['admin', 'manager'].includes(String(profile.role ?? ''))) {
    throw new Error('Acces admin refuse')
  }
  return data.user
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
    await assertAdmin(userClient, adminClient)

    const body = await request.json().catch(() => ({}))
    const action = String(body?.action ?? '').trim()

    if (action === 'list') {
      const { data, error } = await adminClient
        .from('app_user_profile')
        .select('*')
        .order('is_active', { ascending: false })
        .order('display_name', { ascending: true })
      if (error) throw new Error(error.message)
      return jsonResponse({ ok: true, users: data ?? [] })
    }

    if (action === 'create') {
      const email = String(body?.email ?? '').trim().toLowerCase()
      const password = String(body?.password ?? '').trim()
      const role = String(body?.role ?? '').trim()
      const firstName = String(body?.firstName ?? '').trim() || null
      const lastName = String(body?.lastName ?? '').trim() || null
      const displayName = String(body?.displayName ?? '').trim() || [firstName, lastName].filter(Boolean).join(' ') || email || null
      const isActive = body?.isActive !== false

      if (!email || !password || !role) {
        return jsonResponse({ ok: false, error: 'Email, password and role are required' }, { status: 400 })
      }

      const created = await adminClient.auth.admin.createUser({
        email,
        password,
        email_confirm: true,
        user_metadata: {
          first_name: firstName,
          last_name: lastName,
          display_name: displayName,
        },
      })
      if (created.error || !created.data.user) {
        throw new Error(created.error?.message ?? 'Unable to create auth user')
      }

      const userId = created.data.user.id
      const { error: profileError } = await adminClient.from('app_user_profile').upsert({
        id: userId,
        email,
        role,
        first_name: firstName,
        last_name: lastName,
        display_name: displayName,
        is_active: isActive,
        updated_at: new Date().toISOString(),
      })
      if (profileError) throw new Error(profileError.message)

      return jsonResponse({ ok: true, userId, email })
    }

    if (action === 'update') {
      const id = String(body?.id ?? '').trim()
      const email = String(body?.email ?? '').trim().toLowerCase()
      const role = String(body?.role ?? '').trim()
      const firstName = String(body?.firstName ?? '').trim() || null
      const lastName = String(body?.lastName ?? '').trim() || null
      const displayName = String(body?.displayName ?? '').trim() || [firstName, lastName].filter(Boolean).join(' ') || email || null
      const isActive = body?.isActive !== false

      if (!id || !email || !role) {
        return jsonResponse({ ok: false, error: 'id, email and role are required' }, { status: 400 })
      }

      const { error } = await adminClient
        .from('app_user_profile')
        .update({
          email,
          role,
          first_name: firstName,
          last_name: lastName,
          display_name: displayName,
          is_active: isActive,
          updated_at: new Date().toISOString(),
        })
        .eq('id', id)
      if (error) throw new Error(error.message)

      return jsonResponse({ ok: true })
    }

    if (action === 'send-reset') {
      const email = String(body?.email ?? '').trim().toLowerCase()
      if (!email) {
        return jsonResponse({ ok: false, error: 'email is required' }, { status: 400 })
      }
      const redirectTo = Deno.env.get('APP_BASE_URL')?.trim()
      const result = await adminClient.auth.resetPasswordForEmail(email, redirectTo ? { redirectTo } : undefined)
      if (result.error) throw new Error(result.error.message)
      return jsonResponse({ ok: true })
    }

    return jsonResponse({ ok: false, error: 'Action inconnue' }, { status: 400 })
  } catch (error) {
    return jsonResponse(
      { ok: false, error: error instanceof Error ? error.message : 'Erreur interne' },
      { status: 500 },
    )
  }
})
