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
    // Le meme mecanisme sert aux documents et aux photos : seul le type de job change.
    // sync_console_documents = pieces (diagnostics, mandats...) ; sync_hektor_photos = reportage.
    jobType: "sync_console_documents",
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
    } else if (arg === "--job-type" && next) {
      args.jobType = next;
      index += 1;
    } else if (arg === "--dry-run") {
      args.dryRun = true;
    } else {
      throw new Error(`Argument inconnu: ${arg}`);
    }
  }
  const scopes = Object.keys(INDEX_SOURCES);
  if (!scopes.includes(args.scope)) {
    throw new Error(`--scope doit valoir : ${scopes.join(", ")}`);
  }
  if (!["sync_console_documents", "sync_hektor_photos"].includes(args.jobType)) {
    throw new Error("--job-type doit valoir sync_console_documents ou sync_hektor_photos");
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

// Les annonces ne vivent pas toutes dans app_dossier_current : ce sont QUATRE index
// distincts (chantier d'independance 2026-08-17). Chacun a sa table et sa cle technique,
// mais tous portent hektor_annonce_id -- c'est lui qui permet au worker de retrouver le bien.
// Sans cette table de correspondance, l'enfilement ne couvre que les 13 214 actives et
// laisse 43 649 annonces sans documents ni photos.
const INDEX_SOURCES = {
  "daily-cloud": { table: "app_dossier_current", idColumn: "app_dossier_id", dailyFilter: true },
  "all-local": { table: "app_dossier_current", idColumn: "app_dossier_id", dailyFilter: false },
  archive: { table: "app_archive_annonce_index_current", idColumn: "app_archive_id", dailyFilter: false },
  historical: { table: "app_historical_annonce_index_current", idColumn: "app_historical_id", dailyFilter: false },
  brouillon: { table: "app_brouillon_annonce_index_current", idColumn: "app_brouillon_id", dailyFilter: false },
};

function buildDossierPath(args, offset) {
  const source = INDEX_SOURCES[args.scope];
  const params = new URLSearchParams({
    select: `${source.idColumn},hektor_annonce_id`,
    order: `${source.idColumn}.asc`,
    limit: String(args.batchSize),
    offset: String(offset),
  });
  if (source.dailyFilter) {
    params.set("archive", "eq.0");
    params.set("statut_annonce", `in.(${DAILY_STATUSES.map((status) => `"${status}"`).join(",")})`);
  }
  return `${source.table}?${params.toString()}`;
}

async function loadPendingJobs(hektorAnnonceIds, jobType = "sync_console_documents") {
  if (!hektorAnnonceIds.length) return new Set();
  const params = new URLSearchParams({
    select: "hektor_annonce_id",
    job_type: `eq.${jobType}`,
    status: "in.(pending,running)",
    hektor_annonce_id: `in.(${hektorAnnonceIds.map((id) => `"${id}"`).join(",")})`,
  });
  const rows = await supabaseRequest(`app_console_job?${params.toString()}`, { method: "GET" });
  return new Set((Array.isArray(rows) ? rows : []).map((row) => String(row.hektor_annonce_id)));
}

async function enqueueBatch(dossiers, args) {
  // La cle technique change selon l'index (app_dossier_id / app_archive_id /
  // app_historical_id / app_brouillon_id) : on la normalise ici. Le worker sait
  // retrouver le bien dans les trois index a partir de cette valeur (loadDossier).
  const idColumn = INDEX_SOURCES[args.scope].idColumn;
  const pending = await loadPendingJobs(dossiers.map((dossier) => String(dossier.hektor_annonce_id)), args.jobType);
  const jobs = dossiers
    .filter((dossier) => dossier[idColumn] != null && dossier.hektor_annonce_id != null)
    .filter((dossier) => !pending.has(String(dossier.hektor_annonce_id)))
    .map((dossier) => ({
      job_type: args.jobType,
      app_dossier_id: Number(dossier[idColumn]),
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
