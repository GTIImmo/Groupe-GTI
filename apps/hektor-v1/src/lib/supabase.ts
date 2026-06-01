import { createClient } from '@supabase/supabase-js'
import type { Session } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabaseUrl = url
export const supabaseAnonKey = anonKey

export const hasSupabaseEnv = Boolean(url && anonKey)
export const googleWorkspaceDomain = (import.meta.env.VITE_GOOGLE_WORKSPACE_DOMAIN ?? 'gti-immobilier.fr').trim().toLowerCase()
const defaultProductionAppUrl = 'https://groupe-gti.vercel.app'
export const appPublicUrl = (
  import.meta.env.VITE_APP_PUBLIC_URL
  ?? (!import.meta.env.DEV ? defaultProductionAppUrl : '')
).trim().replace(/\/+$/, '')

export const supabase = hasSupabaseEnv
  ? createClient(url, anonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null

export function isGoogleWorkspaceEmail(email?: string | null): boolean {
  const normalized = (email ?? '').trim().toLowerCase()
  return normalized.endsWith(`@${googleWorkspaceDomain}`)
}

export async function getCurrentSession(): Promise<Session | null> {
  if (!supabase) return null
  const { data } = await supabase.auth.getSession()
  return data.session
}

export async function signInWithPassword(email: string, password: string): Promise<void> {
  if (!supabase) throw new Error('Supabase is not configured')
  const { error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw new Error(error.message)
}

export async function signInWithGoogleWorkspace(redirectTo?: string): Promise<void> {
  if (!supabase) throw new Error('Supabase is not configured')
  const cleanRedirectTo = (appPublicUrl || redirectTo || '').trim().replace(/\/+$/, '') || undefined
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: cleanRedirectTo,
      scopes: 'openid email profile',
      queryParams: {
        hd: googleWorkspaceDomain,
        prompt: 'select_account',
      },
    },
  })
  if (error) throw new Error(error.message)
}

export async function signOut(): Promise<void> {
  if (!supabase) return
  const { error } = await supabase.auth.signOut()
  if (error) throw new Error(error.message)
}

export async function updatePassword(password: string): Promise<void> {
  if (!supabase) throw new Error('Supabase is not configured')
  const { error } = await supabase.auth.updateUser({ password })
  if (error) throw new Error(error.message)
}
