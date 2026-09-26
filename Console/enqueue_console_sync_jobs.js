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

// =====================================================================================
// LE FREIN (2026-09-25) — les MEMES reglages que le worker, pas une seconde verite
// =====================================================================================
// Ce fichier lisait Hektor avec un fetch NU : aucune cadence, et un 403 etait compte dans
// lectures_ko puis IGNORE -- le balayage continuait, jusqu'a 13 000 requetes contre un
// serveur qui venait de nous fermer la porte. C'est la mecanique exacte du bannissement
// d'IP du 20/08 (debit + 403 repetes), que hektorFetch a corrigee cote worker (7143a1a)
// mais qui restait entiere ici.
//
// Les constantes sont lues dans LES MEMES variables d'environnement que le worker : un
// seul reglage pour les deux. Les dupliquer en dur ferait diverger les deux cadences au
// premier ajustement, et on croirait freiner alors qu'un des deux chemins galoperait.
const MIN_INTERVAL_MS = Number(process.env.CONSOLE_HEKTOR_MIN_REQUEST_INTERVAL_MS || 1000);
const PAUSE_EVERY_N = Number(process.env.CONSOLE_HEKTOR_PAUSE_EVERY_N_REQUESTS || 100);
const LONG_PAUSE_MS = Number(process.env.CONSOLE_HEKTOR_LONG_PAUSE_MS || 60000);
const WAVE_EVERY_N = Number(process.env.CONSOLE_HEKTOR_WAVE_EVERY_N_REQUESTS || 2000);
const WAVE_PAUSE_MS = Number(process.env.CONSOLE_HEKTOR_WAVE_PAUSE_MS || 300000);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let derniereRequeteAt = 0;
let nbRequetes = 0;

async function freinHektor() {
  const attente = Math.max(0, derniereRequeteAt + MIN_INTERVAL_MS - Date.now());
  if (attente > 0) await sleep(attente);
  nbRequetes += 1;
  // La vague prime sur la respiration : 2 000 etant un multiple de 100, les deux tomberaient
  // ensemble et on dormirait 6 minutes d'affilee sans raison. (Meme regle que hektorThrottle.)
  if (WAVE_EVERY_N > 0 && nbRequetes % WAVE_EVERY_N === 0) {
    console.error(JSON.stringify({ step: "hektor_fin_de_vague", requetes: nbRequetes, pause_ms: WAVE_PAUSE_MS }));
    await sleep(WAVE_PAUSE_MS);
  } else if (PAUSE_EVERY_N > 0 && nbRequetes % PAUSE_EVERY_N === 0) {
    console.error(JSON.stringify({ step: "hektor_respiration", requetes: nbRequetes, pause_ms: LONG_PAUSE_MS }));
    await sleep(LONG_PAUSE_MS);
  }
  derniereRequeteAt = Date.now();
}

// Erreur qui ARRETE le balayage, par opposition a une lecture ratee isolee (timeout, 500)
// qu'on passe sans rien conclure. La distinction est le coeur du correctif : tout ignorer
// prolongeait le bannissement, tout arreter perdrait le balayage sur un hoquet.
class ArretBalayage extends Error {
  constructor(motif) {
    super(motif);
    this.name = "ArretBalayage";
    this.motif = motif;
  }
}

// Signature d'un blocage reseau (bannissement constate les 19 et 20/08) : la connexion
// n'aboutit meme pas. Chaque nouvelle tentative le prolonge -> on arrete.
const RESEAU_BLOQUE = /UND_ERR_CONNECT_TIMEOUT|ECONNREFUSED|ECONNRESET|EAI_AGAIN/i;

// Session Hektor : on REUTILISE le pot de cookies du worker documents, en LECTURE SEULE.
// On ne le reecrit jamais et on ne relogue pas ici : si la session est morte, la detection
// s'arrete proprement et le passage suivant reessaiera.
// ⚠⚠ LA CONSOLE HEKTOR REPOND SUR DEUX NOMS DE DOMAINE -- constate le 26/09.
// `groupe-gti-immobilier.la-boite-immo.com` ET `www.gti-immobilier.fr` servent la meme
// application. Le pot de cookies du worker porte l'un OU l'autre, selon celui qu'il a
// utilise en dernier : apres l'envoi d'une photo (qui passe par www.gti-immobilier.fr),
// storage_state_documents.json ne contenait PLUS AUCUN cookie la-boite-immo.com.
// Un filtre sur un seul domaine rend donc « aucun cookie Hektor » alors que la session
// est parfaitement valide. On accepte les deux, et on deduit l'adresse de base de celui
// qui porte effectivement les cookies.
// ⚠⚠ L'HOTE VIENT DE LA CONFIGURATION, LES COOKIES SUIVENT -- mesure du 26/09.
//
// La Console Hektor repond sur deux noms : `www.gti-immobilier.fr` (celui que
// HEKTOR_BASE_URL designe, et qui REPOND) et `groupe-gti-immobilier.la-boite-immo.com`
// (qui rend 403). Le pot de cookies du worker porte LES DEUX -- memes noms de cookie,
// MAIS DES VALEURS DIFFERENTES : ce sont deux sessions distinctes, mesure faite
// (0 valeur identique sur 2 cookies communs).
//
// Consequence, et c'etait le defaut : ce fichier appelait le BON hote avec les cookies
// de L'AUTRE session -> Hektor rendait la page de connexion, et la detection aurait
// echoue sur CHAQUE annonce. Ce n'etait pas « aucun cookie trouve », c'etait
// « mauvaise session envoyee ».
// ⚠ Et deduire l'hote DES COOKIES ne corrige rien : on appelle alors l'hote qui refuse.
//
// La regle est donc : on prend l'hote de HEKTOR_BASE_URL, et les cookies DE CET HOTE.
// Si cet hote n'a pas de cookie, on le DIT au lieu d'en envoyer d'autres au hasard.
function loadHektorCookieHeader() {
  const fs = require("fs");
  const hote = new URL(HEKTOR_BASE_URL).hostname;
  const state = JSON.parse(fs.readFileSync(DETECT_STORAGE_STATE, "utf8"));
  const cookies = (state.cookies || [])
    .filter((c) => String(c.domain || "").replace(/^\./, "") === hote)
    .map((c) => c.name + "=" + c.value);
  if (!cookies.length) {
    const presents = [...new Set((state.cookies || [])
      .map((c) => String(c.domain || "").replace(/^\./, "")))].join(", ");
    throw new Error(`Aucun cookie pour ${hote} dans ${DETECT_STORAGE_STATE}`
      + ` -- domaines presents : ${presents}`);
  }
  return { header: cookies.join("; "), base: "https://" + hote };
}

async function fetchDocumentsHtml(hektorAnnonceId, session, timeoutMs = 20000) {
  await freinHektor();
  const cookieHeader = session.header;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const url = session.base + "/admin/xmlrpc.php?mode=chargeannonce_Documents&id="
      + encodeURIComponent(hektorAnnonceId) + "&lang=fr";
    let response;
    try {
      response = await fetch(url, { signal: controller.signal, headers: { Cookie: cookieHeader, Accept: "text/html,*/*" } });
    } catch (error) {
      const message = String((error && error.message) || error);
      const code = String((error && error.cause && error.cause.code) || (error && error.code) || "");
      if (RESEAU_BLOQUE.test(message) || RESEAU_BLOQUE.test(code)) {
        throw new ArretBalayage("connexion refusee (" + (code || message).slice(0, 60) + ") -- signature d'un blocage reseau");
      }
      throw error;   // timeout isole : lecture ratee, on passera a la suivante
    }
    // ⚠ UN REFUS ARRETE TOUT. Avant, le 403 etait compte puis ignore et le balayage
    // continuait -- c'est ce qui a fait bannir notre IP. Regle du projet : un 403 = stop,
    // jamais de nouvel essai.
    if ([401, 403, 429, 503].includes(response.status)) {
      throw new ArretBalayage("Hektor " + response.status + " -- le serveur nous ecarte");
    }
    if (!response.ok) throw new Error("Hektor " + response.status);
    const text = await response.text();
    // Page de login = session morte. Sans ce controle on conclurait "contenu vide" et on
    // ferait resynchroniser tout le parc. Et toutes les lectures suivantes sont vouees a
    // l'echec -> on arrete au lieu de les enchainer.
    if (/type=["']password["']/i.test(text.slice(0, 20000))) throw new ArretBalayage("Session Hektor expiree");
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
  const session = loadHektorCookieHeader();
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
  const stats = { balayees: 0, inchangees: 0, changees: 0, sans_empreinte: 0, suivi_signature: 0, lectures_ko: 0, arret: null };

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
      html = await fetchDocumentsHtml(id, session);
    } catch (error) {
      // ARRET : le serveur nous ecarte, ou la session est morte. On sort de la boucle --
      // insister prolonge le bannissement. Ce qui a DEJA ete retenu est quand meme empile
      // juste apres : le travail fait n'est pas perdu, et la reprise se fera par identifiant
      // au passage suivant (l'empreinte absente vaut "a traiter").
      if (error instanceof ArretBalayage) {
        stats.arret = error.motif;
        break;
      }
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
