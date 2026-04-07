import { execFile } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import nodemailer from 'nodemailer'
import { createClient } from '@supabase/supabase-js'
import { defineConfig, loadEnv, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

function hektorDiffusionDevApi(): Plugin {
  const projectRoot = fileURLToPath(new URL('../..', import.meta.url))
  const pythonPath = path.join(projectRoot, '.venv', 'Scripts', 'python.exe')
  const scriptPath = path.join(projectRoot, 'phase2', 'sync', 'hektor_diffusion_writeback.py')
  const refreshScriptPath = path.join(projectRoot, 'phase2', 'sync', 'refresh_single_annonce.py')

  const handleCommand = (
    req: any,
    res: any,
    command: 'apply-targets' | 'accept-request',
  ) => {
    if (req.method !== 'POST') {
      res.statusCode = 405
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify({ error: 'Method not allowed' }))
      return
    }

    const chunks: Buffer[] = []
    req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
    req.on('end', () => {
      try {
        const raw = Buffer.concat(chunks).toString('utf-8') || '{}'
        const body = JSON.parse(raw) as { appDossierId?: number; dryRun?: boolean; ensureDiffusable?: boolean }
        const appDossierId = Number(body.appDossierId)
        if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
          res.statusCode = 400
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Invalid appDossierId' }))
          return
        }

        const args = [scriptPath, command, '--app-dossier-id', String(appDossierId)]
        if (body.dryRun) args.push('--dry-run')
        if (command === 'apply-targets' && body.ensureDiffusable) args.push('--ensure-diffusable')

        execFile(pythonPath, args, { cwd: projectRoot, timeout: 120000 }, (error, stdout, stderr) => {
          res.setHeader('Content-Type', 'application/json')
          if (error) {
            res.statusCode = 500
            res.end(JSON.stringify({
              ok: false,
              error: error.message,
              stderr: stderr.trim() || null,
              stdout: stdout.trim() || null,
            }))
            return
          }
          try {
            const payload = JSON.parse(stdout)
            const shouldRefreshSingleAnnonce =
              (command === 'accept-request' || command === 'apply-targets') &&
              !body.dryRun &&
              typeof payload?.hektor_annonce_id === 'string' &&
              payload.hektor_annonce_id.trim().length > 0
            if (shouldRefreshSingleAnnonce) {
              execFile(
                pythonPath,
                [refreshScriptPath, '--id-annonce', String(payload.hektor_annonce_id).trim()],
                { cwd: projectRoot, timeout: 120000 },
                (refreshError, refreshStdout, refreshStderr) => {
                  if (refreshError) {
                    res.statusCode = 200
                    res.end(JSON.stringify({
                      ok: true,
                      payload: {
                        ...payload,
                        refresh_single_annonce: {
                          ok: false,
                          error: refreshError.message,
                          stdout: refreshStdout.trim() || null,
                          stderr: refreshStderr.trim() || null,
                        },
                      },
                    }))
                    return
                  }
                  let refreshPayload: unknown = { stdout: refreshStdout.trim() || null, stderr: refreshStderr.trim() || null }
                  try {
                    refreshPayload = JSON.parse(refreshStdout)
                  } catch {
                    // no-op
                  }
                  res.statusCode = 200
                  res.end(JSON.stringify({
                    ok: true,
                    payload: {
                      ...payload,
                      refresh_single_annonce: refreshPayload,
                    },
                  }))
                },
              )
              return
            }
            res.statusCode = 200
            res.end(JSON.stringify({ ok: true, payload }))
          } catch {
            res.statusCode = 200
            res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }))
          }
        })
      } catch (error) {
        res.statusCode = 500
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
      }
    })
  }

  return {
    name: 'hektor-diffusion-dev-api',
    configureServer(server) {
      server.middlewares.use('/api/hektor-diffusion/targets', (req, res) => {
        if (req.method === 'GET') {
          const url = new URL(req.url ?? '', 'http://localhost')
          const appDossierId = Number(url.searchParams.get('appDossierId'))
          if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
            res.statusCode = 400
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ error: 'Invalid appDossierId' }))
            return
          }
          execFile(
            pythonPath,
            [scriptPath, 'list-targets', '--app-dossier-id', String(appDossierId)],
            { cwd: projectRoot, timeout: 120000 },
            (error, stdout, stderr) => {
              res.setHeader('Content-Type', 'application/json')
              if (error) {
                res.statusCode = 500
                res.end(JSON.stringify({
                  ok: false,
                  error: error.message,
                  stderr: stderr.trim() || null,
                  stdout: stdout.trim() || null,
                }))
                return
              }
              try {
                res.statusCode = 200
                res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }))
              } catch {
                res.statusCode = 200
                res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }))
              }
            },
          )
          return
        }
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }
        const chunks: Buffer[] = []
        req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
        req.on('end', () => {
          try {
            const raw = Buffer.concat(chunks).toString('utf-8') || '{}'
            const body = JSON.parse(raw) as { appDossierId?: number; requestedBy?: string | null; targets?: unknown[] }
            const appDossierId = Number(body.appDossierId)
            if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
              res.statusCode = 400
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ error: 'Invalid appDossierId' }))
              return
            }
            const payloadJson = JSON.stringify(Array.isArray(body.targets) ? body.targets : [])
            const args = [
              scriptPath,
              'replace-targets',
              '--app-dossier-id',
              String(appDossierId),
              '--requested-by',
              String(body.requestedBy ?? 'app'),
              '--payload-json',
              payloadJson,
            ]
            execFile(pythonPath, args, { cwd: projectRoot, timeout: 120000 }, (error, stdout, stderr) => {
              res.setHeader('Content-Type', 'application/json')
              if (error) {
                res.statusCode = 500
                res.end(JSON.stringify({
                  ok: false,
                  error: error.message,
                  stderr: stderr.trim() || null,
                  stdout: stdout.trim() || null,
                }))
                return
              }
              try {
                res.statusCode = 200
                res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }))
              } catch {
                res.statusCode = 200
                res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }))
              }
            })
          } catch (error) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
          }
        })
      })
      server.middlewares.use('/api/hektor-diffusion/seed', (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }
        const chunks: Buffer[] = []
        req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
        req.on('end', () => {
          try {
            const raw = Buffer.concat(chunks).toString('utf-8') || '{}'
            const body = JSON.parse(raw) as { appDossierId?: number }
            const appDossierId = Number(body.appDossierId)
            if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
              res.statusCode = 400
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ error: 'Invalid appDossierId' }))
              return
            }
            execFile(
              pythonPath,
              [scriptPath, 'seed-default-targets', '--app-dossier-id', String(appDossierId)],
              { cwd: projectRoot, timeout: 120000 },
              (error, stdout, stderr) => {
                res.setHeader('Content-Type', 'application/json')
                if (error) {
                  res.statusCode = 500
                  res.end(JSON.stringify({
                    ok: false,
                    error: error.message,
                    stderr: stderr.trim() || null,
                    stdout: stdout.trim() || null,
                  }))
                  return
                }
                try {
                  res.statusCode = 200
                  res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }))
                } catch {
                  res.statusCode = 200
                  res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }))
                }
              },
            )
          } catch (error) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
          }
        })
      })
      server.middlewares.use('/api/hektor-diffusion/preview-targets', (req, res) => {
        if (req.method !== 'GET') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }
        const url = new URL(req.url ?? '', 'http://localhost')
        const appDossierId = Number(url.searchParams.get('appDossierId'))
        if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
          res.statusCode = 400
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Invalid appDossierId' }))
          return
        }
        execFile(
          pythonPath,
          [scriptPath, 'preview-default-targets', '--app-dossier-id', String(appDossierId)],
          { cwd: projectRoot, timeout: 120000 },
          (error, stdout, stderr) => {
            res.setHeader('Content-Type', 'application/json')
            if (error) {
              res.statusCode = 500
              res.end(JSON.stringify({
                ok: false,
                error: error.message,
                stderr: stderr.trim() || null,
                stdout: stdout.trim() || null,
              }))
              return
            }
            try {
              res.statusCode = 200
              res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }))
            } catch {
              res.statusCode = 200
              res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }))
            }
          },
        )
      })
      server.middlewares.use('/api/hektor-diffusion/broadcasts', (req, res) => {
        if (req.method !== 'GET') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }
        const url = new URL(req.url ?? '', 'http://localhost')
        const appDossierId = Number(url.searchParams.get('appDossierId'))
        if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
          res.statusCode = 400
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Invalid appDossierId' }))
          return
        }
        execFile(
          pythonPath,
          [scriptPath, 'list-broadcasts', '--app-dossier-id', String(appDossierId)],
          { cwd: projectRoot, timeout: 120000 },
          (error, stdout, stderr) => {
            res.setHeader('Content-Type', 'application/json')
            if (error) {
              res.statusCode = 500
              res.end(JSON.stringify({
                ok: false,
                error: error.message,
                stderr: stderr.trim() || null,
                stdout: stdout.trim() || null,
              }))
              return
            }
            try {
              res.statusCode = 200
              res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }))
            } catch {
              res.statusCode = 200
              res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }))
            }
          },
        )
      })
      server.middlewares.use('/api/hektor-diffusion/apply', (req, res) => {
        handleCommand(req, res, 'apply-targets')
      })
      server.middlewares.use('/api/hektor-diffusion/accept', (req, res) => {
        handleCommand(req, res, 'accept-request')
      })
    },
  }
}

function diffusionNotificationDevApi(env: Record<string, string>): Plugin {
  const buildTransporter = () => {
    const host = env.SMTP_HOST
    const port = Number(env.SMTP_PORT ?? 587)
    const user = env.SMTP_USER
    const pass = env.SMTP_PASS
    const secure = String(env.SMTP_SECURE ?? '').trim().toLowerCase() === 'true' || port === 465
    if (!host || !Number.isFinite(port) || !user || !pass) {
      throw new Error('SMTP non configure. Variables requises : SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS')
    }
    return nodemailer.createTransport({
      host,
      port,
      secure,
      auth: { user, pass },
    })
  }

  return {
    name: 'diffusion-notification-dev-api',
    configureServer(server) {
      server.middlewares.use('/api/notifications/diffusion-decision', (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }))
          return
        }

        const chunks: Buffer[] = []
        req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
        req.on('end', async () => {
          try {
            const raw = Buffer.concat(chunks).toString('utf-8') || '{}'
            const body = JSON.parse(raw) as {
              to?: string
              subject?: string
              bodyText?: string
              bodyHtml?: string | null
              fromEmail?: string | null
              fromName?: string | null
              replyTo?: string | null
            }

            const to = body.to?.trim()
            const subject = body.subject?.trim()
            const bodyText = body.bodyText?.trim()
            if (!to || !subject || !bodyText) {
              res.statusCode = 400
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ ok: false, error: 'Missing to, subject or bodyText' }))
              return
            }

            const transporter = buildTransporter()
            const smtpFrom = env.SMTP_FROM?.trim() || env.SMTP_USER?.trim() || ''
            const allowUserFrom = String(env.SMTP_ALLOW_USER_FROM ?? '').trim().toLowerCase() === 'true'
            const senderName = body.fromName?.trim() || 'Application diffusion'
            const senderEmail = body.fromEmail?.trim() || null
            const effectiveFrom = allowUserFrom && senderEmail
              ? `"${senderName.replace(/"/g, "'")}" <${senderEmail}>`
              : smtpFrom
                ? `"${senderName.replace(/"/g, "'")}" <${smtpFrom}>`
                : null

            if (!effectiveFrom) {
              res.statusCode = 500
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ ok: false, error: 'SMTP_FROM ou SMTP_USER manquant pour definir l expediteur' }))
              return
            }

            const info = await transporter.sendMail({
              from: effectiveFrom,
              to,
              replyTo: body.replyTo?.trim() || senderEmail || undefined,
              subject,
              text: bodyText,
              html: body.bodyHtml?.trim() || undefined,
            })

            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: true, messageId: info.messageId ?? null }))
          } catch (error) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
          }
        })
      })
    },
  }
}

function adminUserDevApi(env: Record<string, string>): Plugin {
  const supabaseUrl = env.VITE_SUPABASE_URL?.trim()
  const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY?.trim()

  const getAdminClient = () => {
    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error('SUPABASE_SERVICE_ROLE_KEY non configure')
    }
    return createClient(supabaseUrl, serviceRoleKey, { auth: { persistSession: false, autoRefreshToken: false } })
  }

  return {
    name: 'admin-user-dev-api',
    configureServer(server) {
      server.middlewares.use('/api/admin/users/create', (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }))
          return
        }

        const chunks: Buffer[] = []
        req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
        req.on('end', async () => {
          try {
            const raw = Buffer.concat(chunks).toString('utf-8') || '{}'
            const body = JSON.parse(raw) as {
              email?: string
              password?: string
              role?: 'admin' | 'manager' | 'commercial' | 'lecture'
              firstName?: string
              lastName?: string
              displayName?: string
              isActive?: boolean
            }

            const email = body.email?.trim().toLowerCase()
            const password = body.password?.trim()
            const role = body.role?.trim() as 'admin' | 'manager' | 'commercial' | 'lecture' | undefined
            const firstName = body.firstName?.trim() || null
            const lastName = body.lastName?.trim() || null
            const displayName = body.displayName?.trim() || [firstName, lastName].filter(Boolean).join(' ') || email || null
            const isActive = body.isActive !== false

            if (!email || !password || !role) {
              res.statusCode = 400
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ ok: false, error: 'Email, password and role are required' }))
              return
            }

            const adminClient = getAdminClient()
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

            if (profileError) {
              throw new Error(profileError.message)
            }

            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: true, userId, email }))
          } catch (error) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
          }
        })
      })

      server.middlewares.use('/api/admin/users/list', async (_req, res) => {
        try {
          const adminClient = getAdminClient()
          const { data, error } = await adminClient
            .from('app_user_profile')
            .select('*')
            .order('is_active', { ascending: false })
            .order('display_name', { ascending: true })

          if (error) throw new Error(error.message)

          res.statusCode = 200
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ ok: true, users: data ?? [] }))
        } catch (error) {
          res.statusCode = 500
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
        }
      })

      server.middlewares.use('/api/admin/users/update', (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }))
          return
        }

        const chunks: Buffer[] = []
        req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
        req.on('end', async () => {
          try {
            const raw = Buffer.concat(chunks).toString('utf-8') || '{}'
            const body = JSON.parse(raw) as {
              id?: string
              email?: string
              role?: 'admin' | 'manager' | 'commercial' | 'lecture'
              firstName?: string
              lastName?: string
              displayName?: string
              isActive?: boolean
            }

            const id = body.id?.trim()
            const email = body.email?.trim().toLowerCase()
            const role = body.role?.trim() as 'admin' | 'manager' | 'commercial' | 'lecture' | undefined
            if (!id || !email || !role) {
              res.statusCode = 400
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ ok: false, error: 'id, email and role are required' }))
              return
            }

            const adminClient = getAdminClient()
            const firstName = body.firstName?.trim() || null
            const lastName = body.lastName?.trim() || null
            const displayName = body.displayName?.trim() || [firstName, lastName].filter(Boolean).join(' ') || email
            const isActive = body.isActive !== false

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

            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: true }))
          } catch (error) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
          }
        })
      })

      server.middlewares.use('/api/admin/users/send-reset', (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }))
          return
        }

        const chunks: Buffer[] = []
        req.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
        req.on('end', async () => {
          try {
            const raw = Buffer.concat(chunks).toString('utf-8') || '{}'
            const body = JSON.parse(raw) as { email?: string }
            const email = body.email?.trim().toLowerCase()
            if (!email) {
              res.statusCode = 400
              res.setHeader('Content-Type', 'application/json')
              res.end(JSON.stringify({ ok: false, error: 'email is required' }))
              return
            }

            const adminClient = getAdminClient()
            const redirectTo = env.APP_BASE_URL?.trim()
            const result = await adminClient.auth.resetPasswordForEmail(email, redirectTo ? { redirectTo } : undefined)
            if (result.error) throw new Error(result.error.message)

            res.statusCode = 200
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: true }))
          } catch (error) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }))
          }
        })
      })
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), hektorDiffusionDevApi(), diffusionNotificationDevApi(env), adminUserDevApi(env)],
  }
})
