const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const DAILY_STATUSES = ["Actif", "Sous offre", "Sous compromis", "Estimation"];

function parseArgs(argv) {
  const args = {
    scope: "daily-cloud",
    batchSize: 100,
    limit: 0,
    priority: 100,
    dryRun: false,
  };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];
    if (arg === "--scope" && next) {
      args.scope = next;
      index += 1;
    } else if (arg === "--batch-size" && next) {
      args.batchSize = Number(next);
      index += 1;
    } else if (arg === "--limit" && next) {
      args.limit = Number(next);
      index += 1;
    } else if (arg === "--priority" && next) {
      args.priority = Number(next);
      index += 1;
    } else if (arg === "--dry-run") {
      args.dryRun = true;
    } else {
      throw new Error(`Argument inconnu: ${arg}`);
    }
  }
  if (!["daily-cloud", "all-local"].includes(args.scope)) {
    throw new Error("--scope doit valoir daily-cloud ou all-local");
  }
  return args;
}

function requireEnv(name, value) {
  if (!value) throw new Error(`Missing environment variable: ${name}`);
  return value;
}

function restHeaders(contentType = "application/json") {
  return {
    apikey: requireEnv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY),
    Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
    ...(contentType ? { "Content-Type": contentType } : {}),
  };
}

async function supabaseRequest(pathname, options = {}) {
  const baseUrl = requireEnv("SUPABASE_URL", SUPABASE_URL).replace(/\/+$/, "");
  const response = await fetch(`${baseUrl}/rest/v1/${pathname.replace(/^\/+/, "")}`, {
    ...options,
    headers: {
      ...restHeaders(options.contentType === undefined ? "application/json" : options.contentType),
      Prefer: options.prefer || undefined,
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = payload && typeof payload === "object" ? payload.message || payload.msg || payload.error : text;
    throw new Error(`Supabase ${response.status} on ${pathname}: ${detail || response.statusText}`);
  }
  return payload;
}

function buildDossierPath(args, offset) {
  const params = new URLSearchParams({
    select: "app_dossier_id,hektor_annonce_id,archive,statut_annonce",
    order: "app_dossier_id.asc",
    limit: String(args.batchSize),
    offset: String(offset),
  });
  if (args.scope === "daily-cloud") {
    params.set("archive", "eq.0");
    params.set("statut_annonce", `in.(${DAILY_STATUSES.map((status) => `"${status}"`).join(",")})`);
  }
  return `app_dossier_current?${params.toString()}`;
}

async function loadPendingJobs(hektorAnnonceIds) {
  if (!hektorAnnonceIds.length) return new Set();
  const params = new URLSearchParams({
    select: "hektor_annonce_id",
    job_type: "eq.sync_console_documents",
    status: "in.(pending,running)",
    hektor_annonce_id: `in.(${hektorAnnonceIds.map((id) => `"${id}"`).join(",")})`,
  });
  const rows = await supabaseRequest(`app_console_job?${params.toString()}`, { method: "GET" });
  return new Set((Array.isArray(rows) ? rows : []).map((row) => String(row.hektor_annonce_id)));
}

async function enqueueBatch(dossiers, args) {
  const pending = await loadPendingJobs(dossiers.map((dossier) => String(dossier.hektor_annonce_id)));
  const jobs = dossiers
    .filter((dossier) => dossier.app_dossier_id != null && dossier.hektor_annonce_id != null)
    .filter((dossier) => !pending.has(String(dossier.hektor_annonce_id)))
    .map((dossier) => ({
      job_type: "sync_console_documents",
      app_dossier_id: Number(dossier.app_dossier_id),
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      payload_json: { scope: args.scope },
      status: "pending",
      priority: args.priority,
    }));

  if (!jobs.length || args.dryRun) return jobs.length;
  await supabaseRequest("app_console_job", {
    method: "POST",
    prefer: "return=minimal",
    body: JSON.stringify(jobs),
  });
  return jobs.length;
}

async function main() {
  const args = parseArgs(process.argv);
  requireEnv("SUPABASE_URL", SUPABASE_URL);
  requireEnv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY);

  let offset = 0;
  let seen = 0;
  let queued = 0;
  while (true) {
    const remaining = args.limit > 0 ? Math.max(0, args.limit - seen) : args.batchSize;
    if (remaining === 0) break;
    const batchSize = Math.min(args.batchSize, remaining);
    const batchArgs = { ...args, batchSize };
    const dossiers = await supabaseRequest(buildDossierPath(batchArgs, offset), { method: "GET" });
    if (!Array.isArray(dossiers) || !dossiers.length) break;
    seen += dossiers.length;
    queued += await enqueueBatch(dossiers, args);
    offset += dossiers.length;
    if (dossiers.length < batchSize) break;
  }

  console.log(JSON.stringify({
    scope: args.scope,
    dry_run: args.dryRun,
    dossiers_seen: seen,
    jobs_queued: queued,
  }, null, 2));
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
