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
    // Mode DETECTION (2026-08-20) : au lieu d'empiler tout le perimetre, on relit la page
    // documents de chaque annonce, on recalcule son empreinte de contenu et on ne synchronise
    // que celles qui ont bouge. Purement additif : sans --detect, comportement d'origine.
    detect: false,
    cap: 3000,
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
    } else if (arg === "--detect") {
      args.detect = true;
    } else if (arg === "--cap" && next) {
      args.cap = Number(next);
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


// =====================================================================================
// MODE DETECTION (2026-08-20) — active par --detect, sinon comportement d'origine inchange
// =====================================================================================
// Hektor ne date pas les sous-entites : la date de mise a jour d'une annonce NE BOUGE PAS
// quand un document y est depose (mesure : 91 % des documents sont plus recents que la MAJ
// declaree de leur annonce). Un delta par date manquerait donc 9 ajouts sur 10.
// On compare a la place une EMPREINTE DU CONTENU documentaire, calculee par le worker et
// stockee dans app_console_document_fingerprint.
//
// Deux ensembles sont empiles, et les DEUX sont necessaires :
//   1. les annonces dont l'empreinte a change (ou qui n'en ont pas)  -> contenu modifie
//   2. les annonces ayant un cycle de signature EN COURS             -> etat modifie
// L'empreinte ne detecte pas le passage "en attente -> signe" : les identifiants de procedure
// sont les memes avant et apres. Sans le second ensemble, aucune signature ne serait jamais
// vue aboutir.
//
// L'empreinte est IMPORTEE du worker (source unique). La recalculer ici ferait diverger les
// deux implementations au premier ajustement, et toutes les comparaisons deviendraient fausses.
const { documentContentFingerprint } = require("./console_job_worker.js");

const HEKTOR_BASE_URL = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const HEKTOR_XMLRPC = HEKTOR_BASE_URL + "/admin/xmlrpc.php";
const DETECT_STORAGE_STATE = process.env.CONSOLE_DETECT_STORAGE_STATE_PATH
  || path.resolve(__dirname, "sessions", "storage_state_documents.json");

// Session Hektor : on REUTILISE le pot de cookies du worker documents, en LECTURE SEULE.
// On ne le reecrit jamais et on ne relogue pas ici : si la session est morte, la detection
// s'arrete proprement et le passage suivant reessaiera.
function loadHektorCookieHeader() {
  const fs = require("fs");
  const state = JSON.parse(fs.readFileSync(DETECT_STORAGE_STATE, "utf8"));
  const cookies = (state.cookies || [])
    .filter((c) => String(c.domain || "").includes("la-boite-immo.com"))
    .map((c) => c.name + "=" + c.value);
  if (!cookies.length) throw new Error("Aucun cookie Hektor dans " + DETECT_STORAGE_STATE);
  return cookies.join("; ");
}

async function fetchDocumentsHtml(hektorAnnonceId, cookieHeader, timeoutMs = 20000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const url = HEKTOR_XMLRPC + "?mode=chargeannonce_Documents&id=" + encodeURIComponent(hektorAnnonceId) + "&lang=fr";
    const response = await fetch(url, { signal: controller.signal, headers: { Cookie: cookieHeader, Accept: "text/html,*/*" } });
    if (!response.ok) throw new Error("Hektor " + response.status);
    const text = await response.text();
    // Page de login = session morte. Sans ce controle on conclurait "contenu vide" et on
    // ferait resynchroniser tout le parc.
    if (/type=["']password["']/i.test(text.slice(0, 20000))) throw new Error("Session Hektor expiree");
    return text;
  } finally {
    clearTimeout(timer);
  }
}

async function loadFingerprints() {
  const map = new Map();
  const pageSize = 1000;
  for (let offset = 0; ; offset += pageSize) {
    const rows = await supabaseRequest(
      "app_console_document_fingerprint?select=hektor_annonce_id,fingerprint,checked_at&limit=" + pageSize + "&offset=" + offset,
      { method: "GET" },
    );
    if (!Array.isArray(rows) || !rows.length) break;
    for (const row of rows) map.set(String(row.hektor_annonce_id), row);
    if (rows.length < pageSize) break;
  }
  return map;
}

// Ensemble 2 : annonces dont un document a un cycle de signature EN COURS.
// Meme regle que le garde-fou du worker (reconcileSignatureStates) : une procedure existe,
// la signature n'est pas manuscrite, et le cycle n'est ni abouti ni annule.
async function loadSignatureFollowSet() {
  const annonces = new Set();
  const pageSize = 1000;
  for (let offset = 0; ; offset += pageSize) {
    const rows = await supabaseRequest(
      "app_console_document?select=hektor_annonce_id,metadata_json&limit=" + pageSize + "&offset=" + offset,
      { method: "GET" },
    );
    if (!Array.isArray(rows) || !rows.length) break;
    for (const row of rows) {
      const md = row.metadata_json || {};
      const sig = md.signature || null;
      const statut = (sig && sig.status) || "";
      if (sig && sig.source === "manuscrite") continue;
      if (statut === "cancelled") continue;
      if (statut === "signed" && md.signed_document) continue;
      const procedure = (md.modelo && md.modelo.procedure_id) || (sig && sig.procedure_id) || null;
      if (!procedure) continue;
      annonces.add(String(row.hektor_annonce_id));
    }
    if (rows.length < pageSize) break;
  }
  return annonces;
}

async function touchFingerprintChecked(hektorAnnonceId) {
  await supabaseRequest(
    "app_console_document_fingerprint?hektor_annonce_id=eq." + encodeURIComponent(hektorAnnonceId),
    { method: "PATCH", prefer: "return=minimal", body: JSON.stringify({ checked_at: new Date().toISOString() }) },
  );
}

async function runDetection(args) {
  const cookieHeader = loadHektorCookieHeader();
  const empreintes = await loadFingerprints();
  const suiviSignature = await loadSignatureFollowSet();

  // Perimetre complet charge d'un bloc, puis trie : jamais controlees d'abord, ensuite les
  // plus anciennement controlees. Sans cet ordre, un plafond atteint verrouillerait le
  // balayage sur les memes annonces et le reste ne serait jamais revu.
  const dossiers = [];
  for (let offset = 0; ; offset += args.batchSize) {
    const rows = await supabaseRequest(buildDossierPath(args, offset), { method: "GET" });
    if (!Array.isArray(rows) || !rows.length) break;
    dossiers.push(...rows);
    if (rows.length < args.batchSize) break;
  }
  dossiers.sort((a, b) => {
    const ea = empreintes.get(String(a.hektor_annonce_id));
    const eb = empreintes.get(String(b.hektor_annonce_id));
    const ta = ea && ea.checked_at ? Date.parse(ea.checked_at) : 0;
    const tb = eb && eb.checked_at ? Date.parse(eb.checked_at) : 0;
    return ta - tb;
  });

  const aSynchroniser = [];
  const stats = { balayees: 0, inchangees: 0, changees: 0, sans_empreinte: 0, suivi_signature: 0, lectures_ko: 0 };

  // Ensemble 2 d'abord : aucune lecture Hektor, et c'est le seul moyen de voir une signature
  // aboutir.
  for (const dossier of dossiers) {
    if (aSynchroniser.length >= args.cap) break;
    if (!suiviSignature.has(String(dossier.hektor_annonce_id))) continue;
    aSynchroniser.push(dossier);
    stats.suivi_signature += 1;
  }
  const dejaPris = new Set(aSynchroniser.map((d) => String(d.hektor_annonce_id)));

  // Ensemble 1 : balayage et comparaison d'empreinte.
  for (const dossier of dossiers) {
    if (aSynchroniser.length >= args.cap) break;
    const id = String(dossier.hektor_annonce_id);
    if (dejaPris.has(id)) continue;
    const connue = empreintes.get(id);
    if (!connue) { aSynchroniser.push(dossier); stats.sans_empreinte += 1; continue; }
    let html;
    try {
      html = await fetchDocumentsHtml(id, cookieHeader);
    } catch (error) {
      // Lecture impossible : on ne conclut RIEN. L'empreinte reste en place et l'annonce sera
      // revue au prochain passage. Une panne Hektor ne doit provoquer ni fausse detection, ni
      // resynchronisation massive.
      stats.lectures_ko += 1;
      continue;
    }
    stats.balayees += 1;
    if (documentContentFingerprint(html) === connue.fingerprint) {
      stats.inchangees += 1;
      if (!args.dryRun) await touchFingerprintChecked(id).catch(() => {});
      continue;
    }
    aSynchroniser.push(dossier);
    stats.changees += 1;
  }

  let empiles = 0;
  for (let i = 0; i < aSynchroniser.length; i += args.batchSize) {
    empiles += await enqueueBatch(aSynchroniser.slice(i, i + args.batchSize), args);
  }
  return Object.assign({}, stats, { plafond: args.cap, jobs_empiles: empiles });
}

async function main() {
  const args = parseArgs(process.argv);
  requireEnv("SUPABASE_URL", SUPABASE_URL);
  requireEnv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY);

  if (args.detect) {
    const resultat = await runDetection(args);
    console.log(JSON.stringify({ mode: "detection", scope: args.scope, dry_run: args.dryRun, ...resultat }, null, 2));
    return;
  }

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
