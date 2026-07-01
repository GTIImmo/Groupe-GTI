const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const zlib = require("zlib");
const { spawn } = require("child_process");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "matterport", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${HEKTOR_BASE_URL.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const HEKTOR_ROOT_ADMIN_USER_ID = String(process.env.CONSOLE_HEKTOR_ROOT_ADMIN_USER_ID || process.env.HEKTOR_ROOT_ADMIN_USER_ID || "4").trim();
const RAW_WORKER_KIND = String(process.env.CONSOLE_WORKER_KIND || process.env.CONSOLE_WORKER_MODE || "actions").toLowerCase();
const WORKER_KINDS = new Set(["actions", "documents", "admin", "matterport", "sync_light", "sync_full", "sync", "all"]);
const WORKER_KIND = WORKER_KINDS.has(RAW_WORKER_KIND) ? RAW_WORKER_KIND : "actions";
const STORAGE_BUCKET = process.env.CONSOLE_STORAGE_BUCKET || "hektor-console-documents";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "sessions", `storage_state_${WORKER_KIND}.json`);
const MATTERPORT_STORAGE_STATE_PATH = process.env.MATTERPORT_STORAGE_STATE_PATH || path.resolve(__dirname, "matterport_storage_state.json");
const LOCAL_ARCHIVE_ROOT = process.env.CONSOLE_LOCAL_ARCHIVE_ROOT || "C:\\Hektor\\HektorConsoleDocuments";
const PROJECT_ROOT = path.resolve(__dirname, "..");
const PYTHON_EXE = process.env.CONSOLE_PYTHON_EXE || path.resolve(PROJECT_ROOT, ".venv", "Scripts", "python.exe");
const ACTION_JOB_TYPES = new Set([
  "link_hektor_mandant",
  "create_hektor_contact",
  "update_hektor_contact",
  "add_hektor_contact_search",
  "update_hektor_contact_search",
  "delete_hektor_contact_search",
  "create_hektor_mandant_contact",
  "update_hektor_mandant_contact",
  "update_hektor_annonce_fields",
  "create_hektor_mandat_auto_number",
  "create_hektor_draft_annonce",
]);
const DOCUMENT_JOB_TYPES = new Set([
  "sync_console_documents",
  "prepare_document_cloud",
  "generate_estimation_pdf",
  "generate_mandat_document",
  "generate_cadastre_document",
  "relance_signature",
  "cancel_signature_procedure",
  "upload_document_to_hektor",
  "delete_document_from_hektor",
  "sync_hektor_photos",
  "upload_hektor_photo",
  "prepare_archived_annonce_detail",
  "prepare_historical_annonce_detail",
]);
const ADMIN_JOB_TYPES = new Set([
  "delete_hektor_annonce",
  "delete_hektor_contact",
  "archive_hektor_annonce",
  "restore_hektor_annonce",
  "change_hektor_annonce_status",
  "assign_hektor_annonce_negotiator",
]);
const MATTERPORT_JOB_TYPES = new Set([
  "matterport_online",
  "matterport_offline",
  "matterport_archive",
  "matterport_reactivate",
]);
const SYNC_LIGHT_JOB_TYPES = new Set([
  "refresh_console_data",
  "refresh_console_contact_data",
]);
const SYNC_FULL_JOB_TYPES = new Set([
  "archive_cloud_documents",
]);
const ALL_JOB_TYPES_BY_KIND = {
  actions: ACTION_JOB_TYPES,
  documents: DOCUMENT_JOB_TYPES,
  admin: ADMIN_JOB_TYPES,
  matterport: MATTERPORT_JOB_TYPES,
  sync_light: SYNC_LIGHT_JOB_TYPES,
  sync_full: SYNC_FULL_JOB_TYPES,
};
const WORKER_ID = process.env.CONSOLE_WORKER_ID || `${os.hostname()}:${WORKER_KIND}:${process.pid}`;
const WORKER_LOCK_DIR = path.resolve(__dirname, ".locks");
const WORKER_GENERATION = String(process.env.CONSOLE_WORKER_GENERATION || "manual").replace(/[^A-Za-z0-9_-]/g, "_");
const WORKER_LOCK_PATH = path.join(WORKER_LOCK_DIR, `console_worker_${WORKER_KIND}_${WORKER_GENERATION}.lock`);
const DEFAULT_POLL_INTERVAL_MS = ["sync", "sync_full"].includes(WORKER_KIND) ? 60000 : WORKER_KIND === "sync_light" ? 10000 : 5000;
const POLL_INTERVAL_MS = Number(process.env.CONSOLE_WORKER_POLL_INTERVAL_MS || DEFAULT_POLL_INTERVAL_MS);
const HEKTOR_SESSION_REFRESH_MS = Number(process.env.CONSOLE_HEKTOR_SESSION_REFRESH_MS || 2 * 60 * 60 * 1000);
const NODE_SCRIPT_TIMEOUT_MS = Number(process.env.CONSOLE_NODE_SCRIPT_TIMEOUT_MS || 3 * 60 * 1000);
const JOB_TIMEOUT_MS = Number(process.env.CONSOLE_JOB_TIMEOUT_MS || 10 * 60 * 1000);
const ENABLE_HEKTOR_ACTIONS = String(process.env.CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS || "").toLowerCase() === "true";
const ENABLE_MATTERPORT_ACTIONS = String(process.env.CONSOLE_WORKER_ENABLE_MATTERPORT_ACTIONS || "").toLowerCase() === "true";
const CREATE_HEKTOR_HTTP_DIRECT = String(process.env.CONSOLE_CREATE_HEKTOR_HTTP_DIRECT || "true").toLowerCase() !== "false";
const CREATE_HEKTOR_PLAYWRIGHT_FALLBACK = String(process.env.CONSOLE_CREATE_HEKTOR_PLAYWRIGHT_FALLBACK || "true").toLowerCase() !== "false";
const CLOUD_STATUSES = new Set(["Actif", "Sous offre", "Sous compromis", "Estimation"]);

function browserLaunchOptions(options = {}) {
  const executablePath = [
    process.env.CONSOLE_CHROME_EXE,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].find((candidate) => candidate && fs.existsSync(candidate)) || "";
  return {
    ...options,
    ...(executablePath ? { executablePath } : {}),
  };
}

const PROPERTY_LISTING_QUERY = `
query PropertyListing($filters: AnnonceSearchInput!) {
  listing: properties(filters: $filters) {
    metadata { total perPage currentPage nextPage }
    properties: nodes {
      id
      folderNumber
      createdAt
      datemaj
      status
      isArchived
      isDraft
      isMasked
      isBroadcasted
      isValid
      price(force: true)
      surface
      roomCount
      adresse
      ville { nom }
      villeprivee { nom }
      type { name }
    }
  }
}`;

const CRM_CONTACT_CONFIGURATION_QUERY = `
query CrmContactRelationshipConfigurations($prospect: Int) {
  mandateSummaryConfiguration(prospect: $prospect) { enabled }
  mandateExpirationConfiguration(prospect: $prospect) { enabled }
  crmBirthdayConfiguration(prospect: $prospect) { enabled }
}`;

const CRM_TOGGLE_MANDATE_SUMMARY_CONFIGURATION_MUTATION = `
mutation ToggleMandateSummaryConfiguration($enabled: Boolean!, $prospect: Int) {
  toggleMandateSummaryConfiguration(enabled: $enabled, prospect: $prospect)
}`;

const CRM_TOGGLE_MANDATE_EXPIRATION_CONFIGURATION_MUTATION = `
mutation ToggleMandateExpirationConfiguration($enabled: Boolean!, $prospect: Int) {
  toggleMandateExpirationConfiguration(enabled: $enabled, prospect: $prospect)
}`;

const CRM_TOGGLE_BIRTHDAY_CONFIGURATION_MUTATION = `
mutation ToggleCrmBirthdayConfiguration($enabled: Boolean!, $prospect: Int) {
  toggleCrmBirthdayConfiguration(enabled: $enabled, prospect: $prospect)
}`;

let hektorLoginPromise = null;
let lastHektorLoginAt = fs.existsSync(STORAGE_STATE_PATH) ? fs.statSync(STORAGE_STATE_PATH).mtimeMs : 0;

function requireEnv(name, value) {
  if (!value) throw new Error(`Missing environment variable: ${name}`);
  return value;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isHektorSessionError(error) {
  const message = error && error.message ? error.message : String(error || "");
  return message.includes("Hektor 403")
    || message.includes("Session Hektor expiree")
    || message.includes("Missing HTTP_AUTHORIZATION");
}

function isHektorForbiddenError(error) {
  const message = error && error.message ? error.message : String(error || "");
  return message.includes("Hektor 403") || message.includes("HEKTOR_403") || message.includes("stopped_on_403");
}

function runNodeScript(scriptPath, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const childEnv = {
      ...process.env,
      ...(options.env || {}),
    };
    const child = spawn(process.execPath, [scriptPath, ...args], {
      cwd: __dirname,
      env: childEnv,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    const timeoutMs = Number(options.timeoutMs || 0);
    const timeout = timeoutMs > 0 ? setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGTERM");
      setTimeout(() => {
        if (!child.killed) child.kill("SIGKILL");
      }, 5000).unref();
      reject(new Error(`Script ${path.basename(scriptPath)} timeout apres ${timeoutMs}ms`));
    }, timeoutMs) : null;
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", (error) => {
      if (settled) return;
      settled = true;
      if (timeout) clearTimeout(timeout);
      reject(error);
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      if (timeout) clearTimeout(timeout);
      if (code === 0) {
        resolve({ stdout, stderr });
        return;
      }
      reject(new Error(`Script ${path.basename(scriptPath)} failed with code ${code}: ${stderr || stdout}`.slice(0, 3000)));
    });
  });
}

function runProjectPythonScript(args, options = {}) {
  const childEnv = {
    ...process.env,
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
  };
  return new Promise((resolve, reject) => {
    let settled = false;
    const child = spawn(PYTHON_EXE, args, {
      cwd: PROJECT_ROOT,
      env: childEnv,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    const timeoutMs = Number(options.timeoutMs || 0);
    const timeout = timeoutMs > 0 ? setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGTERM");
      setTimeout(() => {
        if (!child.killed) child.kill("SIGKILL");
      }, 5000).unref();
      reject(new Error(`Python ${args.join(" ")} timeout apres ${timeoutMs}ms`));
    }, timeoutMs) : null;
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", (error) => {
      if (settled) return;
      settled = true;
      if (timeout) clearTimeout(timeout);
      reject(error);
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      if (timeout) clearTimeout(timeout);
      if (code === 0) {
        resolve({
          stdout: stdout.slice(-Number(options.previewSize || 1800)),
          stderr: stderr.slice(-Number(options.previewSize || 1800)),
        });
        return;
      }
      reject(new Error(`Python ${args.join(" ")} failed with code ${code}: ${stderr || stdout}`.slice(0, 3000)));
    });
  });
}

function withTimeout(promise, timeoutMs, label) {
  if (!timeoutMs || timeoutMs <= 0) return promise;
  let timeout = null;
  const timeoutPromise = new Promise((_, reject) => {
    timeout = setTimeout(() => {
      reject(new Error(`${label} timeout apres ${timeoutMs}ms`));
    }, timeoutMs);
  });
  return Promise.race([promise, timeoutPromise]).finally(() => {
    if (timeout) clearTimeout(timeout);
  });
}

async function refreshHektorSession(reason = "scheduled") {
  if (hektorLoginPromise) return hektorLoginPromise;
  const loginScript = path.resolve(__dirname, "playwright_login.js");
  hektorLoginPromise = (async () => {
    console.log(JSON.stringify({ worker: WORKER_ID, step: "hektor_login", reason }));
    await runNodeScript(loginScript, [], {
      timeoutMs: NODE_SCRIPT_TIMEOUT_MS,
      env: { CONSOLE_STORAGE_STATE_PATH: STORAGE_STATE_PATH },
    });
    lastHektorLoginAt = Date.now();
    console.log(JSON.stringify({ worker: WORKER_ID, step: "hektor_login", status: "done", reason }));
  })();
  try {
    await hektorLoginPromise;
  } finally {
    hektorLoginPromise = null;
  }
}

async function refreshHektorSessionIfDue() {
  if (!ENABLE_HEKTOR_ACTIONS) return;
  if (HEKTOR_SESSION_REFRESH_MS <= 0) return;
  const stateMtime = fs.existsSync(STORAGE_STATE_PATH) ? fs.statSync(STORAGE_STATE_PATH).mtimeMs : 0;
  lastHektorLoginAt = Math.max(lastHektorLoginAt, stateMtime);
  if (Date.now() - lastHektorLoginAt >= HEKTOR_SESSION_REFRESH_MS) {
    await refreshHektorSession("scheduled_refresh");
  }
}

function safeJsonParse(value, fallback = {}) {
  if (!value) return fallback;
  if (typeof value === "object") return value;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function normalizeEmail(value) {
  return String(value || "").trim().toLowerCase();
}

function decodeJwtPayload(token) {
  const clean = String(token || "").replace(/^Bearer\s+/i, "").trim();
  const part = clean.split(".")[1];
  if (!part) return null;
  try {
    const normalized = part.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    return JSON.parse(Buffer.from(padded, "base64").toString("utf-8"));
  } catch (_) {
    return null;
  }
}

function extractImpersonateUserId(value) {
  const raw = String(value || "").trim();
  const validId = (candidate) => {
    const text = String(candidate == null ? "" : candidate).trim();
    return /^[1-9]\d*$/.test(text) ? text : null;
  };
  if (!raw) return null;
  if (/^\d+$/.test(raw)) return validId(raw);
  try {
    const parsed = JSON.parse(raw);
    const queue = [parsed];
    while (queue.length) {
      const item = queue.shift();
      if (!item || typeof item !== "object") continue;
      for (const key of ["idUser", "userId", "id_user", "id"]) {
        const found = validId(item[key]);
        if (found) return found;
      }
      for (const value of Object.values(item)) {
        if (value && typeof value === "object") queue.push(value);
      }
    }
  } catch (_) {
    // Some Hektor builds store a compact non-JSON impersonation marker.
  }
  const match = raw.match(/(?:idUser|userId|id_user|id)["'\s:=]+(\d+)/i);
  return match ? validId(match[1]) : null;
}

function readHektorStorageState() {
  if (!fs.existsSync(STORAGE_STATE_PATH)) throw new Error(`Session console introuvable: ${STORAGE_STATE_PATH}`);
  return JSON.parse(fs.readFileSync(STORAGE_STATE_PATH, "utf-8"));
}

function hektorOriginLocalStorage(state) {
  const origins = Array.isArray(state.origins) ? state.origins : [];
  const hektorOrigin = HEKTOR_BASE_URL.replace(/\/+$/, "");
  const origin = origins.find((item) => item.origin === hektorOrigin);
  return origin && Array.isArray(origin.localStorage) ? origin.localStorage : [];
}

function ensureHektorOrigin(state) {
  if (!Array.isArray(state.origins)) state.origins = [];
  const hektorOrigin = HEKTOR_BASE_URL.replace(/\/+$/, "");
  let origin = state.origins.find((item) => item.origin === hektorOrigin);
  if (!origin) {
    origin = { origin: hektorOrigin, localStorage: [] };
    state.origins.push(origin);
  }
  if (!Array.isArray(origin.localStorage)) origin.localStorage = [];
  return origin;
}

function setHektorLocalStorageValue(state, name, value) {
  const origin = ensureHektorOrigin(state);
  const current = origin.localStorage.find((item) => item.name === name);
  if (current) current.value = value;
  else origin.localStorage.push({ name, value });
}

function currentHektorSessionIdentity() {
  try {
    const state = readHektorStorageState();
    const localStorage = hektorOriginLocalStorage(state);
    const tokenEntry = localStorage.find((item) => item.name === "token");
    const impersonateEntry = localStorage.find((item) => item.name === "impersonate");
    const decoded = decodeJwtPayload(tokenEntry && tokenEntry.value);
    const payload = decoded && decoded.data ? decoded.data : decoded;
    if (!payload) return null;
    const tokenUserId = payload.userId == null ? null : String(payload.userId);
    const impersonateUserId = extractImpersonateUserId(impersonateEntry && impersonateEntry.value);
    return {
      userId: tokenUserId || impersonateUserId,
      tokenUserId,
      impersonateUserId,
      userObjectId: payload.userObjectId == null ? null : String(payload.userObjectId),
      role: payload.role || (impersonateUserId ? "IMPERSONATED" : null),
      tokenRole: payload.role || null,
      alias: payload.alias || payload.userAlias || null,
      impersonate: impersonateEntry ? "present" : null,
    };
  } catch (_) {
    return null;
  }
}

function parseJsonOutput(value, fallback = {}) {
  const text = String(value || "").trim();
  if (!text) return fallback;
  try {
    return JSON.parse(text);
  } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return safeJsonParse(text.slice(start, end + 1), fallback);
    }
    return fallback;
  }
}

function isHektorRootAdminIdentity(identity) {
  if (!identity || identity.role !== "ADMIN") return false;
  if (HEKTOR_ROOT_ADMIN_USER_ID && String(identity.userId || "") !== HEKTOR_ROOT_ADMIN_USER_ID) return false;
  return !identity.impersonateUserId;
}

function cookieJarFromStorageState(state) {
  const jar = new Map();
  const now = Date.now() / 1000;
  for (const cookie of Array.isArray(state.cookies) ? state.cookies : []) {
    if (cookie.expires && cookie.expires > 0 && cookie.expires <= now) continue;
    jar.set(cookie.name, { ...cookie });
  }
  return jar;
}

function cookieHeaderFromJar(jar) {
  return Array.from(jar.values()).map((cookie) => `${cookie.name}=${cookie.value}`).join("; ");
}

function setCookieHeaders(headers) {
  if (headers && typeof headers.getSetCookie === "function") return headers.getSetCookie();
  const combined = headers && typeof headers.get === "function" ? headers.get("set-cookie") : null;
  if (!combined) return [];
  return combined.split(/,(?=[^;,]+=)/g);
}

function absorbSetCookieHeaders(jar, headers) {
  for (const raw of setCookieHeaders(headers)) {
    const first = String(raw || "").split(";")[0];
    const eq = first.indexOf("=");
    if (eq <= 0) continue;
    const name = first.slice(0, eq).trim();
    const value = first.slice(eq + 1).trim();
    const existing = jar.get(name) || {
      name,
      domain: new URL(HEKTOR_BASE_URL).hostname,
      path: "/",
      expires: -1,
      httpOnly: false,
      secure: true,
      sameSite: "Lax",
    };
    jar.set(name, { ...existing, value });
  }
}

function saveCookieJarToStorageState(state, jar) {
  const byName = new Map(Array.from(jar.entries()));
  const nextCookies = [];
  const seen = new Set();
  for (const cookie of Array.isArray(state.cookies) ? state.cookies : []) {
    if (byName.has(cookie.name)) {
      nextCookies.push(byName.get(cookie.name));
      seen.add(cookie.name);
    } else {
      nextCookies.push(cookie);
    }
  }
  for (const [name, cookie] of byName.entries()) {
    if (!seen.has(name)) nextCookies.push(cookie);
  }
  state.cookies = nextCookies;
}

function decodeJsString(value) {
  return String(value || "")
    .replace(/\\x([0-9a-fA-F]{2})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
    .replace(/\\u([0-9a-fA-F]{4})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
    .replace(/\\n/g, "\n")
    .replace(/\\r/g, "\r")
    .replace(/\\t/g, "\t")
    .replace(/\\(['"\\])/g, "$1")
    .replace(/\\\\/g, "\\");
}

function extractLocalStorageSetItems(html) {
  const output = new Map();
  const pattern = /localStorage\.setItem\(\s*(['"])([^'"]+)\1\s*,\s*(['"])((?:\\.|(?!\3)[\s\S])*?)\3\s*\)/g;
  let match;
  while ((match = pattern.exec(String(html || "")))) {
    output.set(match[2], decodeJsString(match[4]));
  }
  return output;
}

function storagePathEncode(value) {
  return String(value).split("/").map((part) => encodeURIComponent(part)).join("/");
}

function safeFilename(name, fallback) {
  const clean = String(name || "")
    .replace(/[\\/:*?"<>|]+/g, "_")
    .replace(/\s+/g, " ")
    .trim();
  return clean || fallback;
}

function storageSafeFilename(name, fallback) {
  const clean = safeFilename(name, fallback)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\x20-\x7E]+/g, "_")
    .replace(/[#%?&{}^`[\]]+/g, "_")
    .replace(/\s+/g, " ")
    .trim();
  return clean || fallback;
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function shouldKeepCloud(dossier) {
  return Number(dossier.archive || 0) === 0 && CLOUD_STATUSES.has(String(dossier.statut_annonce || "").trim());
}

function localDocumentDir(hektorAnnonceId, documentId) {
  return path.join(LOCAL_ARCHIVE_ROOT, "annonces", safeFilename(hektorAnnonceId, "annonce"), "documents", safeFilename(documentId, "document"));
}

function localDocumentPath(hektorAnnonceId, documentId, filename) {
  return path.join(localDocumentDir(hektorAnnonceId, documentId), safeFilename(filename, "document.bin"));
}

function isReadableFile(filePath) {
  if (!filePath) return false;
  try {
    return fs.existsSync(filePath) && fs.statSync(filePath).isFile();
  } catch {
    return false;
  }
}

function mimeTypeFromFilename(filename) {
  const ext = path.extname(String(filename || "")).toLowerCase();
  const known = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain",
  };
  return known[ext] || "application/octet-stream";
}

function normalizeMimeType(mimeType, filename) {
  const clean = String(mimeType || "").split(";")[0].trim().toLowerCase();
  if (!clean || clean === "application/octet-stream" || clean === "binary/octet-stream") {
    return mimeTypeFromFilename(filename);
  }
  return clean;
}

function decodeHtml(value) {
  return String(value || "")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

function stripHtml(value) {
  return decodeHtml(String(value || "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim());
}

function sha1(value) {
  return crypto.createHash("sha1").update(String(value)).digest("hex");
}

function sha256Buffer(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function absoluteUrl(raw) {
  const value = decodeHtml(raw || "").trim();
  if (!value || value === "#" || value.startsWith("javascript:") || value.startsWith("data:")) return "";
  try {
    return new URL(value, ADMIN_URL).toString();
  } catch {
    return "";
  }
}

function parseQuotedArgs(argsText) {
  const args = [];
  const re = /'((?:\\'|[^'])*)'|"((?:\\"|[^"])*)"/g;
  let match;
  while ((match = re.exec(argsText))) {
    args.push(decodeHtml((match[1] || match[2] || "").replace(/\\'/g, "'").replace(/\\"/g, '"')));
  }
  return args;
}

function extractInputValue(html, key) {
  const escaped = String(key).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const patterns = [
    new RegExp(`<input[^>]*(?:id|name)=["']${escaped}["'][^>]*value=["']([^"']*)["'][^>]*>`, "i"),
    new RegExp(`<input[^>]*value=["']([^"']*)["'][^>]*(?:id|name)=["']${escaped}["'][^>]*>`, "i"),
    new RegExp(`${escaped}\\s*=\\s*["']([^"']+)["']`, "i"),
  ];
  for (const pattern of patterns) {
    const match = String(html || "").match(pattern);
    if (match) return decodeHtml(match[1]);
  }
  return "";
}

// Statut de signature electronique lu dans la ligne document Hektor (ImmoSign/Yousign).
// Ex: "SIGNATURE(S) EN ATTENTE : 1/1" -> { status:'pending', progress:'1/1' }.
function parseSignatureStatus(text) {
  const t = String(text || "").replace(/\s+/g, " ");
  const m = t.match(/signature\(?s?\)?\s*[^.<]{0,70}/i);
  if (!m) return null;
  const seg = m[0].toLowerCase();
  const prog = seg.match(/(\d+)\s*\/\s*(\d+)/);
  const progress = prog ? `${prog[1]}/${prog[2]}` : null;
  if (/en attente/.test(seg)) return { status: "pending", progress };
  if (/refus/.test(seg)) return { status: "refused", progress };
  if (/sign[ée]e?\b|termin|effectu|complet/.test(seg)) return { status: "signed", progress };
  return null;
}

// Etat de signature lu sur l'EMPREINTE (button#docBtnSign_{docId}_{type}) de la ligne document Hektor.
// Source FIABLE du "signe" (le texte "SIGNATURE(S)..." disparait une fois signe) :
//  - is__successed + title "Signe le {date}" => signed (+ date)
//  - texte "SIGNATURE(S) EN ATTENTE : x/y"   => pending (x/y)
//  - sinon onclick editProcedure(...)         => to_send (brouillon / pas encore envoye)
// procedure_id (downloadProcedureFiles/downloadProofs) sert au telechargement du signe + relance.
function parseSignatureFromRow(rowHtml) {
  const row = String(rowHtml || "");
  const text = stripHtml(row);
  const btn = row.match(/<button[^>]*id="docBtnSign_(\d+)_(\d+)[^"]*"[^>]*>/i);
  // procedure_id : present sous plusieurs formes selon l'etat (signe = download/proofs ; en attente = relance/ceremony).
  const dlp = row.match(/downloadProcedureFiles\(\s*['"]?(\d+)['"]?\s*\)/i)
    || row.match(/reminderProcedureSignatories\(\s*['"]?(\d+)['"]?\s*\)/i)
    || row.match(/downloadProofs\(\s*['"]?(\d+)['"]?\s*\)/i)
    || row.match(/docBtnPrintCeremony_(\d+)/i);
  const procedureId = dlp ? Number(dlp[1]) : null;
  let status = null, progress = null, signedAt = null, cancelledAt = null, hektorDocId = null, docType = null;
  if (btn) {
    hektorDocId = btn[1];
    docType = btn[2];
    const tag = btn[0];
    const cls = (tag.match(/class="([^"]*)"/i) || [, ""])[1];
    const title = decodeHtml((tag.match(/title="([^"]*)"/i) || [, ""])[1]);
    const onclick = (tag.match(/onclick="([^"]*)"/i) || [, ""])[1];
    if (/is__successed/.test(cls)) {
      status = "signed";
      // Date apres "le " (robuste a l'entite &eacute; dans "Sign&eacute; le ...").
      const m = title.match(/\ble\s+(.+)$/i);
      signedAt = m ? m[1].trim() : (title ? title.replace(/&[a-z]+;/gi, "").trim() : null);
    } else if (/annul/i.test(title)) {
      // Procedure ANNULEE par le commercial : title "Annule le ...", redevient envoyable (editProcedure).
      status = "cancelled";
      const m = title.match(/\ble\s+(.+)$/i);
      cancelledAt = m ? m[1].trim() : null;
    } else {
      const st = parseSignatureStatus(text);
      if (st && st.status === "refused") { status = "refused"; progress = st.progress; }
      else if (st && st.status === "pending") { status = "pending"; progress = st.progress; }
      else if (procedureId) { status = "pending"; progress = st && st.progress ? st.progress : null; } // procedure existante + pas signe => envoye, en attente
      else if (/editProcedure\(/.test(onclick)) { status = "to_send"; }
    }
  } else {
    const st = parseSignatureStatus(text);
    if (st) { status = st.status; progress = st.progress; }
  }
  if (!status && !procedureId) return null;
  return { status, progress, signed_at: signedAt, cancelled_at: cancelledAt, procedure_id: procedureId, hektor_doc_id: hektorDocId, doc_type: docType };
}

function extractDocumentEntries(html, source, visibility) {
  const entries = [];
  const re = /force_transfert\(([\s\S]*?)\)\s*;?\s*return false/gi;
  let match;
  while ((match = re.exec(html))) {
    const args = parseQuotedArgs(match[1]);
    const url = absoluteUrl(args[0]);
    if (!url || !url.includes("/admin/documents/")) continue;

    const rowStart = html.lastIndexOf('<div class="tbodyContent tbodyContainer', match.index);
    const nextRowStart = html.indexOf('<div class="tbodyContent tbodyContainer', match.index + 1);
    const rowHtml = html.slice(rowStart >= 0 ? rowStart : Math.max(0, match.index - 3500), nextRowStart > match.index ? nextRowStart : Math.min(html.length, match.index + 3500));
    const before = rowHtml.slice(0, Math.max(0, match.index - (rowStart >= 0 ? rowStart : Math.max(0, match.index - 3500))));
    const labels = [];
    const cellRe = /<div[^>]*class=["'][^"']*tdContent[^"']*["'][^>]*>([\s\S]*?)<\/div>/gi;
    let cell;
    while ((cell = cellRe.exec(before))) {
      const text = stripHtml(cell[1]);
      if (!text) continue;
      if (/^\d{2}\/\d{2}\/\d{4}$/.test(text)) continue;
      if (["apercu", "aperçu", "nom du document"].includes(text.toLowerCase())) continue;
      if (/\.(pdf|jpe?g|png|docx?|xlsx?|csv|txt)$/i.test(text)) labels.push(text);
    }

    const technicalName = args[1] || path.basename(new URL(url).pathname);
    const transferName = args[2] || "";
    const crmLabel = labels[labels.length - 1] || transferName || technicalName;
    const deleteMatch = rowHtml.match(/deleteUploadedDocument\(\s*['"]([^'"]+)['"]/i);
    const signature = parseSignatureFromRow(rowHtml);
    entries.push({
      hektor_document_id: sha1(url),
      document_name: safeFilename(crmLabel, technicalName),
      document_type: "document",
      visibility,
      source,
      console_url: url,
      technical_name: technicalName,
      transfer_name: transferName,
      hektor_uploaded_document_id: deleteMatch ? deleteMatch[1] : null,
      signature,
    });
  }

  const seen = new Set();
  return entries.filter((entry) => {
    if (seen.has(entry.hektor_document_id)) return false;
    seen.add(entry.hektor_document_id);
    return true;
  });
}

function htmlAttrValue(html, attrName) {
  const escaped = String(attrName).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`\\b${escaped}\\s*=\\s*(["'])([\\s\\S]*?)\\1`, "i");
  const match = String(html || "").match(pattern);
  return match ? decodeHtml(match[2]) : "";
}

function cleanImageUrl(url) {
  const resolved = absoluteUrl(url);
  if (!resolved) return "";
  try {
    const parsed = new URL(resolved);
    parsed.search = "";
    return parsed.toString();
  } catch {
    return resolved.replace(/\?.*$/, "");
  }
}

function filenameFromImageUrl(url) {
  try {
    return path.basename(new URL(url).pathname);
  } catch {
    return "";
  }
}

function extractConsolePhotoEntries(html, visible) {
  const entries = [];
  const itemPattern = /<li\b[^>]*class=["'][^"']*classementPhoto[^"']*["'][^>]*id=["']item_([^"']+)["'][^>]*>[\s\S]*?(?=<li\b[^>]*class=["'][^"']*(?:classementPhoto|addNewPhoto)|<\/ul>)/gi;
  let match;
  while ((match = itemPattern.exec(String(html || "")))) {
    const hektorPhotoId = String(match[1] || "").trim();
    const itemHtml = match[0];
    if (!hektorPhotoId) continue;
    const imgMatch = itemHtml.match(/<img\b[^>]*class=["'][^"']*galerie[^"']*["'][^>]*>/i)
      || itemHtml.match(/<img\b[^>]*(?:srcHD|src)=["'][^"']+["'][^>]*>/i);
    const imgHtml = imgMatch ? imgMatch[0] : "";
    const previewUrl = cleanImageUrl(htmlAttrValue(imgHtml, "src"));
    const hdUrl = cleanImageUrl(htmlAttrValue(imgHtml, "srcHD") || htmlAttrValue(imgHtml, "srchd") || previewUrl);
    if (!previewUrl && !hdUrl) continue;
    const detailIndexMatch = imgHtml.match(/\bid=["']detailPhoto(\d+)["']/i);
    const deleteMatch = itemHtml.match(/delete_img\(\s*['"]([^'"]+)['"]\s*,\s*([^,]+)\s*,\s*['"]([^'"]+)['"]/i);
    const legendMatch = itemHtml.match(new RegExp(`<div[^>]*id=["']div_legende_${hektorPhotoId}["'][^>]*>([\\s\\S]*?)<\\/div>`, "i"));
    const textareaMatch = itemHtml.match(new RegExp(`<textarea[^>]*id=["']legende_${hektorPhotoId}["'][^>]*>([\\s\\S]*?)<\\/textarea>`, "i"));
    const legend = stripHtml((legendMatch && legendMatch[1]) || (textareaMatch && textareaMatch[1]) || "");
    const sortOrder = detailIndexMatch ? Number(detailIndexMatch[1]) + 1 : entries.length + 1;
    const filename = safeFilename((deleteMatch && deleteMatch[1]) || filenameFromImageUrl(hdUrl || previewUrl), `${hektorPhotoId}.jpg`);
    entries.push({
      hektor_photo_id: hektorPhotoId,
      filename,
      url_preview: previewUrl || hdUrl,
      url_hd: hdUrl || previewUrl,
      visible: Boolean(visible),
      legend: legend || null,
      sort_order: Number.isFinite(sortOrder) ? sortOrder : entries.length + 1,
      source_json: {
        delete_filename: deleteMatch ? deleteMatch[1] : null,
        delete_annonce_id: deleteMatch ? String(deleteMatch[2] || "").trim() : null,
        delete_photo_id: deleteMatch ? deleteMatch[3] : null,
        actions: {
          can_change_visibility: /visibiliteVignette\(/i.test(itemHtml),
          can_edit_legend: /legendVignette\(/i.test(itemHtml),
          can_delete: /delete_img\(/i.test(itemHtml),
        },
      },
    });
  }
  return entries;
}

function restHeaders(contentType = "application/json") {
  const headers = {
    apikey: requireEnv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY),
    Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
  };
  if (contentType) headers["Content-Type"] = contentType;
  return headers;
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

// --- Création optimiste : réconciliation de la ligne provisoire (app_annonce_provisional) ---
// La provisoire est insérée par le front au moment du "Créer" (affichage instantané "En création").
// Le worker la relie ensuite au vrai bien Hektor (link), ou la marque en erreur, et le read-through
// la supprime une fois le vrai bien présent dans Supabase. Service role => bypass RLS. Best effort :
// un échec ici ne doit JAMAIS faire échouer la création Hektor elle-même.
async function linkProvisionalCreation(creationToken, hektorAnnonceId) {
  const token = cleanString(creationToken);
  const annonceId = cleanString(hektorAnnonceId);
  if (!token || !annonceId) return;
  try {
    await supabaseRequest(`app_annonce_provisional?creation_token=eq.${encodeURIComponent(token)}`, {
      method: "PATCH",
      prefer: "return=minimal",
      body: JSON.stringify({
        hektor_annonce_id: annonceId,
        status: "linked",
        error_message: null,
        updated_at: new Date().toISOString(),
      }),
    });
  } catch (error) {
    console.warn(`[provisional] link echoue (token ${token}): ${error && error.message ? error.message : error}`);
  }
}

async function markProvisionalCreationError(creationToken, message) {
  const token = cleanString(creationToken);
  if (!token) return;
  try {
    await supabaseRequest(`app_annonce_provisional?creation_token=eq.${encodeURIComponent(token)}`, {
      method: "PATCH",
      prefer: "return=minimal",
      body: JSON.stringify({
        status: "error",
        error_message: cleanString(message) || "Erreur de création",
        updated_at: new Date().toISOString(),
      }),
    });
  } catch (error) {
    console.warn(`[provisional] mark error echoue (token ${token}): ${error && error.message ? error.message : error}`);
  }
}

async function cleanupProvisionalForAnnonce(hektorAnnonceId) {
  const annonceId = cleanString(hektorAnnonceId);
  if (!annonceId) return;
  try {
    await supabaseRequest(`app_annonce_provisional?hektor_annonce_id=eq.${encodeURIComponent(annonceId)}`, {
      method: "DELETE",
      prefer: "return=minimal",
    });
  } catch (error) {
    console.warn(`[provisional] cleanup echoue (annonce ${annonceId}): ${error && error.message ? error.message : error}`);
  }
}

async function storageRequest(objectPath, options = {}) {
  const baseUrl = requireEnv("SUPABASE_URL", SUPABASE_URL).replace(/\/+$/, "");
  const response = await fetch(`${baseUrl}/storage/v1/object/${STORAGE_BUCKET}/${storagePathEncode(objectPath)}`, {
    ...options,
    headers: {
      ...restHeaders(options.contentType || null),
      ...(options.upsert ? { "x-upsert": "true" } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`Supabase Storage ${response.status} on ${objectPath}: ${text || response.statusText}`);
  }
  return response;
}

async function uploadStorageObject(objectPath, buffer, mimeType) {
  await storageRequest(objectPath, {
    method: "POST",
    body: buffer,
    contentType: mimeType || "application/octet-stream",
    upsert: true,
  });
}

async function deleteStorageObject(objectPath) {
  if (!objectPath) return;
  try {
    await storageRequest(objectPath, { method: "DELETE" });
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    if (!message.includes("404")) throw error;
  }
}

async function downloadStorageObject(objectPath) {
  const response = await storageRequest(objectPath, { method: "GET" });
  const arrayBuffer = await response.arrayBuffer();
  return {
    buffer: Buffer.from(arrayBuffer),
    mimeType: response.headers.get("content-type") || "application/octet-stream",
  };
}

function writeLocalArchiveFile(filePath, buffer) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, buffer);
}

function readLocalArchiveFile(filePath, mimeType) {
  const buffer = fs.readFileSync(filePath);
  return {
    buffer,
    mimeType: mimeType || "application/octet-stream",
  };
}

function localArchiveMetadata(filePath) {
  const stat = fs.statSync(filePath);
  return {
    local_archive_path: filePath,
    local_archive_root: LOCAL_ARCHIVE_ROOT,
    local_archived_at: new Date().toISOString(),
    local_file_size: stat.size,
  };
}

function workerCanHandleJob(jobType) {
  if (WORKER_KIND === "all") return true;
  if (WORKER_KIND === "sync") return SYNC_LIGHT_JOB_TYPES.has(jobType) || SYNC_FULL_JOB_TYPES.has(jobType);
  const allowed = ALL_JOB_TYPES_BY_KIND[WORKER_KIND];
  return allowed ? allowed.has(jobType) : false;
}

async function claimNextJob() {
  const rows = await supabaseRequest("rpc/app_console_claim_next_job", {
    method: "POST",
    body: JSON.stringify({ p_worker_id: WORKER_ID, p_worker_kind: WORKER_KIND }),
  });
  return Array.isArray(rows) && rows.length ? rows[0] : null;
}

async function logJob(jobId, step, status, message, payload) {
  const preview = payload == null ? null : JSON.stringify(payload).slice(0, 1800);
  await supabaseRequest("app_console_job_log", {
    method: "POST",
    body: JSON.stringify([{ job_id: jobId, step, status, message, payload_preview: preview }]),
  });
}

async function finishJob(jobId, status, result, errorMessage) {
  await supabaseRequest(`app_console_job?id=eq.${encodeURIComponent(jobId)}`, {
    method: "PATCH",
    prefer: "return=minimal",
    body: JSON.stringify({
      status,
      finished_at: new Date().toISOString(),
      result_json: result || null,
      error_message: errorMessage || null,
      updated_at: new Date().toISOString(),
    }),
  });
}

async function enqueueRefreshConsoleDataJob(parentJob, hektorAnnonceId, options = {}) {
  const id = String(hektorAnnonceId || "").trim();
  if (!id) return { status: "skipped", reason: "missing_hektor_annonce_id" };

  const existingParams = new URLSearchParams({
    select: "id,status,priority,requested_at",
    job_type: "eq.refresh_console_data",
    hektor_annonce_id: `eq.${id}`,
    status: "in.(pending,running)",
    order: "requested_at.desc",
    limit: "1",
  });
  const existing = await supabaseRequest(`app_console_job?${existingParams.toString()}`, { method: "GET" });
  if (Array.isArray(existing) && existing.length) {
    const current = existing[0];
    await logJob(parentJob.id, "sync_queue", "done", "Sync data deja en attente pour cette annonce", {
      hektor_annonce_id: id,
      sync_job_id: current.id,
      sync_status: current.status,
    });
    return {
      status: "already_queued",
      job_id: current.id,
      job_status: current.status,
      hektor_annonce_id: id,
    };
  }

  const payload = {
    reason: options.reason || parentJob.job_type,
    parent_job_id: parentJob.id,
    parent_job_type: parentJob.job_type,
    hektor_annonce_id: id,
  };
  const rows = await supabaseRequest("app_console_job", {
    method: "POST",
    prefer: "return=representation",
    body: JSON.stringify([{
      job_type: "refresh_console_data",
      app_dossier_id: parentJob.app_dossier_id || options.appDossierId || null,
      hektor_annonce_id: id,
      payload_json: payload,
      status: "pending",
      priority: options.priority || 80,
      requested_by: parentJob.requested_by || null,
      requested_at: new Date().toISOString(),
    }]),
  });
  const created = Array.isArray(rows) ? rows[0] : null;
  await logJob(parentJob.id, "sync_queue", "done", "Sync data differee creee", {
    hektor_annonce_id: id,
    sync_job_id: created ? created.id : null,
    priority: options.priority || 80,
  });
  return {
    status: "queued",
    job_id: created ? created.id : null,
    hektor_annonce_id: id,
    priority: options.priority || 80,
  };
}

async function enqueueRefreshConsoleDataJobBestEffort(parentJob, hektorAnnonceId, options = {}) {
  try {
    return await enqueueRefreshConsoleDataJob(parentJob, hektorAnnonceId, options);
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    await logJob(parentJob.id, "sync_queue", "error", "Creation sync data differee echouee", {
      hektor_annonce_id: String(hektorAnnonceId || ""),
      error: message,
    });
    return { status: "error", error: message, hektor_annonce_id: String(hektorAnnonceId || "") };
  }
}

async function enqueueRefreshConsoleContactDataJob(parentJob, hektorContactId, options = {}) {
  const id = String(hektorContactId || "").trim();
  if (!id) return { status: "skipped", reason: "missing_hektor_contact_id" };

  const existingParams = new URLSearchParams({
    select: "id,status,priority,requested_at",
    job_type: "eq.refresh_console_contact_data",
    status: "in.(pending,running)",
    order: "requested_at.desc",
    limit: "1",
  });
  existingParams.append("payload_json->>hektor_contact_id", `eq.${id}`);
  const existing = await supabaseRequest(`app_console_job?${existingParams.toString()}`, { method: "GET" });
  if (Array.isArray(existing) && existing.length) {
    const current = existing[0];
    await logJob(parentJob.id, "contact_sync_queue", "done", "Sync contact deja en attente", {
      hektor_contact_id: id,
      sync_job_id: current.id,
      sync_status: current.status,
    });
    return {
      status: "already_queued",
      job_id: current.id,
      job_status: current.status,
      hektor_contact_id: id,
    };
  }

  const payload = {
    reason: options.reason || parentJob.job_type,
    parent_job_id: parentJob.id,
    parent_job_type: parentJob.job_type,
    hektor_contact_id: id,
  };
  const rows = await supabaseRequest("app_console_job", {
    method: "POST",
    prefer: "return=representation",
    body: JSON.stringify([{
      job_type: "refresh_console_contact_data",
      app_dossier_id: parentJob.app_dossier_id || null,
      hektor_annonce_id: parentJob.hektor_annonce_id || null,
      payload_json: payload,
      status: "pending",
      priority: options.priority || 82,
      requested_by: parentJob.requested_by || null,
      requested_at: new Date().toISOString(),
    }]),
  });
  const created = Array.isArray(rows) ? rows[0] : null;
  await logJob(parentJob.id, "contact_sync_queue", "done", "Sync contact differee creee", {
    hektor_contact_id: id,
    sync_job_id: created ? created.id : null,
    priority: options.priority || 82,
  });
  return {
    status: "queued",
    job_id: created ? created.id : null,
    hektor_contact_id: id,
    priority: options.priority || 82,
  };
}

async function enqueueRefreshConsoleContactDataJobBestEffort(parentJob, hektorContactId, options = {}) {
  try {
    return await enqueueRefreshConsoleContactDataJob(parentJob, hektorContactId, options);
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    await logJob(parentJob.id, "contact_sync_queue", "error", "Creation sync contact differee echouee", {
      hektor_contact_id: String(hektorContactId || ""),
      error: message,
    });
    return { status: "error", error: message, hektor_contact_id: String(hektorContactId || "") };
  }
}

async function cancelPendingContactRefreshJobs(parentJob, hektorContactId) {
  const id = String(hektorContactId || "").trim();
  if (!id) return { status: "skipped", reason: "missing_hektor_contact_id" };
  const params = new URLSearchParams({
    job_type: "eq.refresh_console_contact_data",
    status: "eq.pending",
  });
  params.append("payload_json->>hektor_contact_id", `eq.${id}`);
  const rows = await supabaseRequest(`app_console_job?${params.toString()}`, {
    method: "PATCH",
    prefer: "return=representation",
    body: JSON.stringify({
      status: "done",
      finished_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      error_message: null,
      result_json: {
        status: "cancelled",
        reason: "contact_deleted",
        hektor_contact_id: id,
        parent_job_id: parentJob.id,
      },
    }),
  });
  const count = Array.isArray(rows) ? rows.length : 0;
  if (count) {
    await logJob(parentJob.id, "contact_sync_queue", "done", "Sync contact obsoletes annulees", {
      hektor_contact_id: id,
      cancelled_jobs: count,
    });
  }
  return { status: "done", cancelled_jobs: count, hektor_contact_id: id };
}

async function loadDossier(job) {
  if (job.app_dossier_id == null && !job.hektor_annonce_id) throw new Error("Job without dossier or annonce id");
  const params = new URLSearchParams({
    select: "app_dossier_id,hektor_annonce_id,archive,statut_annonce,agence_nom,commercial_id,commercial_nom,negociateur_email",
    limit: "1",
  });
  if (job.app_dossier_id != null) params.set("app_dossier_id", `eq.${job.app_dossier_id}`);
  else params.set("hektor_annonce_id", `eq.${job.hektor_annonce_id}`);
  const rows = await supabaseRequest(`app_dossier_current?${params.toString()}`, { method: "GET" });
  if (Array.isArray(rows) && rows.length) return rows[0];

  const historicalParams = new URLSearchParams({
    select: "app_historical_id,hektor_annonce_id,archive,statut_annonce,agence_nom,commercial_id,commercial_nom,negociateur_email",
    limit: "1",
  });
  if (job.app_dossier_id != null) historicalParams.set("app_historical_id", `eq.${job.app_dossier_id}`);
  else historicalParams.set("hektor_annonce_id", `eq.${job.hektor_annonce_id}`);
  const historicalRows = await supabaseRequest(`app_historical_annonce_index_current?${historicalParams.toString()}`, { method: "GET" });
  if (Array.isArray(historicalRows) && historicalRows.length) {
    const row = historicalRows[0];
    return {
      ...row,
      app_dossier_id: Number(row.app_historical_id),
      archive: row.archive || "0",
    };
  }

  const archiveParams = new URLSearchParams({
    select: "app_archive_id,hektor_annonce_id,numero_dossier,statut_annonce,archive",
    limit: "1",
  });
  if (job.app_dossier_id != null) archiveParams.set("app_archive_id", `eq.${job.app_dossier_id}`);
  else archiveParams.set("hektor_annonce_id", `eq.${job.hektor_annonce_id}`);
  const archiveRows = await supabaseRequest(`app_archive_annonce_index_current?${archiveParams.toString()}`, { method: "GET" });
  if (Array.isArray(archiveRows) && archiveRows.length) {
    throw new Error(`Annonce archivee: ${job.app_dossier_id || job.hektor_annonce_id}. Desarchivez avant d'executer cette action Hektor.`);
  }

  throw new Error(`Dossier introuvable: ${job.app_dossier_id || job.hektor_annonce_id}`);
}

async function loadContactExecutionContext(contactId) {
  const cleanContactId = String(contactId || "").trim();
  if (!/^\d+$/.test(cleanContactId)) throw new Error("contact_id Hektor numerique requis");

  const params = new URLSearchParams({
    select: "hektor_contact_id,hektor_agence_id,hektor_negociateur_id,negociateur_email,commercial_nom,agence_nom,display_name,archive,ville,code_postal,typologies_json,relation_roles_json",
    hektor_contact_id: `eq.${cleanContactId}`,
    limit: "1",
  });
  const contacts = await supabaseRequest(`app_contact_current?${params.toString()}`, { method: "GET" });
  const contact = Array.isArray(contacts) && contacts.length ? contacts[0] : null;
  if (!contact) throw new Error(`Contact introuvable dans l'index Supabase: ${cleanContactId}`);

  let dossier = null;
  const relationParams = new URLSearchParams({
    select: "app_dossier_id,hektor_annonce_id,is_active_annonce,role_contact",
    hektor_contact_id: `eq.${cleanContactId}`,
    app_dossier_id: "not.is.null",
    order: "is_active_annonce.desc,refreshed_at.desc",
    limit: "5",
  });
  const relations = await supabaseRequest(`app_contact_relation_current?${relationParams.toString()}`, { method: "GET" }).catch(() => []);
  for (const relation of Array.isArray(relations) ? relations : []) {
    const appDossierId = relation && relation.app_dossier_id != null ? String(relation.app_dossier_id) : "";
    if (!appDossierId) continue;
    const dossierParams = new URLSearchParams({
      select: "app_dossier_id,hektor_annonce_id,archive,statut_annonce,agence_nom,commercial_id,commercial_nom,negociateur_email",
      app_dossier_id: `eq.${appDossierId}`,
      limit: "1",
    });
    const rows = await supabaseRequest(`app_dossier_current?${dossierParams.toString()}`, { method: "GET" }).catch(() => []);
    if (Array.isArray(rows) && rows.length) {
      dossier = rows[0];
      break;
    }
  }

  const contactDossier = dossier || {
    app_dossier_id: null,
    hektor_annonce_id: null,
    archive: Boolean(contact.archive),
    statut_annonce: null,
    agence_nom: contact.agence_nom || null,
    hektor_agence_id: contact.hektor_agence_id || null,
    commercial_id: contact.hektor_negociateur_id || null,
    commercial_nom: contact.commercial_nom || contact.display_name || null,
    negociateur_email: contact.negociateur_email || null,
  };

  return { contact, dossier: contactDossier };
}

async function loadAppUserProfile(userId) {
  if (!userId) return null;
  const params = new URLSearchParams({
    select: "id,email,display_name,role,is_active",
    id: `eq.${userId}`,
    limit: "1",
  });
  const rows = await supabaseRequest(`app_user_profile?${params.toString()}`, { method: "GET" });
  return Array.isArray(rows) && rows.length ? rows[0] : null;
}

let activeHektorNegoUserIdsCache = null;
let activeHektorNegoUserIdsCacheAt = 0;

async function loadActiveHektorNegoUserIds() {
  const now = Date.now();
  if (activeHektorNegoUserIdsCache && now - activeHektorNegoUserIdsCacheAt < 5 * 60 * 1000) {
    return activeHektorNegoUserIdsCache;
  }
  const params = new URLSearchParams({
    select: "id_user",
    user_type: "eq.NEGO",
    limit: "1000",
  });
  const rows = await supabaseRequest(`app_user_directory?${params.toString()}`, { method: "GET" });
  const ids = new Set(
    (Array.isArray(rows) ? rows : [])
      .map((row) => String((row && row.id_user) || "").trim())
      .filter(Boolean)
  );
  activeHektorNegoUserIdsCache = ids;
  activeHektorNegoUserIdsCacheAt = now;
  return ids;
}

async function loadHektorDirectoryUserByEmail(email) {
  const normalized = normalizeEmail(email);
  if (!normalized) return null;
  const params = new URLSearchParams({
    select: "id_user,display_name,email,user_type",
    user_type: "eq.NEGO",
    email: `ilike.${normalized}`,
    limit: "1",
  });
  const rows = await supabaseRequest(`app_user_directory?${params.toString()}`, { method: "GET" });
  return Array.isArray(rows) && rows.length ? rows[0] : null;
}

async function loadHektorDirectoryUserById(idUser) {
  if (idUser == null || String(idUser).trim() === "") return null;
  const params = new URLSearchParams({
    select: "id_user,display_name,email,user_type",
    user_type: "eq.NEGO",
    id_user: `eq.${String(idUser).trim()}`,
    limit: "1",
  });
  const rows = await supabaseRequest(`app_user_directory?${params.toString()}`, { method: "GET" });
  return Array.isArray(rows) && rows.length ? rows[0] : null;
}

async function loadHektorNegotiatorAgencyRows(filters = {}) {
  const params = new URLSearchParams({
    select: "hektor_negociateur_id,hektor_user_id,hektor_agence_id,agence_id_user,agence_nom,display_name,email",
    limit: String(filters.limit || 10),
  });
  if (filters.negotiatorId) params.set("hektor_negociateur_id", `eq.${String(filters.negotiatorId).trim()}`);
  if (filters.userId) params.set("hektor_user_id", `eq.${String(filters.userId).trim()}`);
  if (filters.agencyId) params.set("hektor_agence_id", `eq.${String(filters.agencyId).trim()}`);
  if (filters.agencyUserId) params.set("agence_id_user", `eq.${String(filters.agencyUserId).trim()}`);
  if (filters.email) params.set("email", `ilike.${normalizeEmail(filters.email)}`);
  const rows = await supabaseRequest(`app_hektor_negotiator_agency_directory?${params.toString()}`, { method: "GET" });
  if (!Array.isArray(rows)) return [];
  if (filters.includeInactive) return rows;
  const activeUserIds = await loadActiveHektorNegoUserIds();
  return rows.filter((row) => activeUserIds.has(String((row && row.hektor_user_id) || "").trim()));
}

function agencyNameMatches(left, right) {
  const normalize = (value) => String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  const a = normalize(left);
  const b = normalize(right);
  return Boolean(a && b && (a === b || a.includes(b) || b.includes(a)));
}

function agencyDirectoryRowToExecutionUser(row, source, fallback = {}) {
  if (!row || !row.hektor_user_id) return null;
  return {
    idUser: String(row.hektor_user_id),
    label: row.display_name || fallback.label || null,
    email: row.email || fallback.email || null,
    source,
    agencyId: row.hektor_agence_id || row.agence_id_user || null,
    negotiatorId: row.hektor_negociateur_id || null,
  };
}

async function resolveHektorNegotiatorFromAgencyDirectory(dossier, email = null) {
  const commercialId = dossier && dossier.commercial_id ? String(dossier.commercial_id).trim() : "";
  const agenceNom = dossier && dossier.agence_nom ? String(dossier.agence_nom).trim() : "";

  if (commercialId) {
    const rows = await loadHektorNegotiatorAgencyRows({ negotiatorId: commercialId, limit: 10 }).catch(() => []);
    const exactAgency = rows.find((row) => agencyNameMatches(row.agence_nom, agenceNom));
    const row = exactAgency || rows[0];
    const user = agencyDirectoryRowToExecutionUser(row, exactAgency ? "dossier_commercial_id_agency" : "dossier_commercial_id", {
      label: dossier.commercial_nom,
      email: dossier.negociateur_email,
    });
    if (user) return user;
  }

  const normalizedEmail = normalizeEmail(email || (dossier && dossier.negociateur_email));
  if (normalizedEmail) {
    const rows = await loadHektorNegotiatorAgencyRows({ email: normalizedEmail, limit: 25 }).catch(() => []);
    const exactCommercial = commercialId ? rows.find((row) => String(row.hektor_negociateur_id || "").trim() === commercialId) : null;
    const exactAgency = rows.find((row) => agencyNameMatches(row.agence_nom, agenceNom));
    const row = exactCommercial || exactAgency || (rows.length === 1 ? rows[0] : null);
    const user = agencyDirectoryRowToExecutionUser(row, exactCommercial ? "email_commercial_id" : exactAgency ? "email_agency" : "email_unique", {
      label: dossier && dossier.commercial_nom,
      email: normalizedEmail,
    });
    if (user) return user;
  }

  return null;
}

async function resolveHektorAnnonceAgencyContext(annonceId, target = {}) {
  const args = [
    "Console/resolve_hektor_annonce_agency.py",
    "--annonce-id",
    String(annonceId),
  ];
  if (target.idUser) args.push("--target-user-id", String(target.idUser));
  if (target.email) args.push("--target-email", String(target.email));
  if (target.agencyId) args.push("--agency-id", String(target.agencyId));
  const result = await runProjectPythonScript(args, { timeoutMs: 30000, previewSize: 4000 });
  const text = String(result.stdout || "").trim();
  if (!text) return null;
  try {
    const parsed = JSON.parse(text);
    return parsed && parsed.found ? parsed : null;
  } catch (error) {
    throw new Error(`Resolution agence Hektor illisible: ${text.slice(0, 500)}`);
  }
}

async function resolveHektorExecutionUser(job, dossier, payload, options = {}) {
  const directId = payload.hektor_user_id || payload.hektor_id_user || payload.target_hektor_user_id;
  if (directId) {
    const directoryUser = await loadHektorDirectoryUserById(directId).catch(() => null);
    if (!directoryUser || !directoryUser.id_user) {
      throw new Error(`idUser Hektor actif introuvable dans l'annuaire app_user_directory: ${directId}`);
    }
    const requestedAgencyName = String(payload.agence_nom || payload.requested_agence_nom || payload.target_agence_nom || "").trim();
    const requestedAgencyId = String(payload.hektor_agence_id || payload.target_hektor_agence_id || "").trim();
    const requestedNegotiatorId = String(
      payload.hektor_negociator_form_id
        || payload.hektor_negociateur_id
        || payload.target_hektor_negociateur_id
        || ""
    ).trim();
    if (requestedAgencyName || requestedAgencyId || requestedNegotiatorId) {
      const rows = await loadHektorNegotiatorAgencyRows({ userId: directId, limit: 50 }).catch(() => []);
      const matchingRow = rows.find((row) => {
        const rowAgencyId = String(row.hektor_agence_id || "").trim();
        const rowAgencyUserId = String(row.agence_id_user || "").trim();
        const rowNegotiatorId = String(row.hektor_negociateur_id || "").trim();
        const agencyOk = !requestedAgencyId || rowAgencyId === requestedAgencyId || rowAgencyUserId === requestedAgencyId;
        const agencyNameOk = !requestedAgencyName || agencyNameMatches(row.agence_nom, requestedAgencyName);
        const negotiatorOk = !requestedNegotiatorId || rowNegotiatorId === requestedNegotiatorId;
        return agencyOk && agencyNameOk && negotiatorOk;
      });
      if (!matchingRow) {
        throw new Error(`idUser Hektor ${directId} actif mais non rattache a l'agence/nego demande (${requestedAgencyName || requestedAgencyId || requestedNegotiatorId}).`);
      }
      return {
        idUser: String(directId),
        label: matchingRow.display_name || directoryUser.display_name || payload.hektor_user_label || payload.negociateur_label || null,
        email: matchingRow.email || directoryUser.email || payload.hektor_user_email || null,
        source: "payload_agency_directory",
        agencyId: matchingRow.hektor_agence_id || matchingRow.agence_id_user || null,
        negotiatorId: matchingRow.hektor_negociateur_id || null,
      };
    }
    return {
      idUser: String(directId),
      label: (directoryUser && directoryUser.display_name) || payload.hektor_user_label || payload.negociateur_label || null,
      email: (directoryUser && directoryUser.email) || payload.hektor_user_email || null,
      source: "payload",
    };
  }

  if (options.preferDossierOwner && dossier && dossier.commercial_id) {
    const agencyDirectoryUser = await resolveHektorNegotiatorFromAgencyDirectory(dossier).catch(() => null);
    if (agencyDirectoryUser && agencyDirectoryUser.idUser) return agencyDirectoryUser;

    const directoryUser = await loadHektorDirectoryUserById(dossier.commercial_id).catch(() => null);
    if (directoryUser && directoryUser.id_user) {
      return {
        idUser: String(directoryUser.id_user),
        label: directoryUser.display_name || dossier.commercial_nom || null,
        email: directoryUser.email || dossier.negociateur_email || null,
        source: "dossier_commercial_id_legacy",
      };
    }
  }

  const emails = [];
  const profile = job.requested_by ? await loadAppUserProfile(job.requested_by).catch(() => null) : null;
  if (options.preferRequester && profile && profile.role === "commercial" && profile.email) emails.push(profile.email);
  if (options.preferDossierOwner && dossier && dossier.negociateur_email) emails.push(dossier.negociateur_email);
  if (payload.hektor_user_email || payload.negociateur_email) emails.push(payload.hektor_user_email || payload.negociateur_email);
  if (profile && profile.email) emails.push(profile.email);
  if (dossier && dossier.negociateur_email) emails.push(dossier.negociateur_email);

  const seen = new Set();
  for (const email of emails) {
    const normalized = normalizeEmail(email);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    const agencyDirectoryUser = await resolveHektorNegotiatorFromAgencyDirectory(dossier, normalized).catch(() => null);
    if (agencyDirectoryUser && agencyDirectoryUser.idUser) return agencyDirectoryUser;

    let directoryUser = await loadHektorDirectoryUserByEmail(normalized).catch(() => null);
    if (directoryUser && directoryUser.id_user) {
      return {
        idUser: String(directoryUser.id_user),
        label: directoryUser.display_name || null,
        email: directoryUser.email || normalized,
        source: "email",
      };
    }
  }

  return null;
}

async function switchHektorUserContextWithPlaywright(idUser) {
  const targetId = String(idUser || "").trim();
  if (!targetId) throw new Error("idUser Hektor requis pour changer de contexte");

  const headless = String(process.env.CONSOLE_HEKTOR_HEADLESS || "true").toLowerCase() !== "false";
  let browser = null;
  let confirmed = false;
  try {
    browser = await chromium.launch(browserLaunchOptions({ headless }));
    const context = await browser.newContext({ storageState: STORAGE_STATE_PATH });
    const page = await context.newPage();
    const loginResponse = await page.goto(`${ADMIN_URL}?call=authenticate&mode=autologin&idUser=${encodeURIComponent(targetId)}`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    if (loginResponse && loginResponse.status() === 403) {
      throw new Error(`Hektor 403 on context switch autologin idUser ${targetId}`);
    }
    await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
    const adminResponse = await page.goto(ADMIN_URL, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => null);
    if (adminResponse && adminResponse.status() === 403) {
      throw new Error(`Hektor 403 after context switch autologin idUser ${targetId}`);
    }
    confirmed = await page.waitForFunction((expectedId) => {
      const matchesImpersonate = (raw) => {
        const value = String(raw || "").trim();
        if (!value) return false;
        if (value === String(expectedId)) return true;
        return new RegExp(`(?:idUser|userId|id_user|id)["'\\s:=]+${String(expectedId)}\\b`, "i").test(value);
      };
      if (matchesImpersonate(localStorage.getItem("impersonate"))) return true;
      const raw = localStorage.getItem("token") || "";
      const token = raw.replace(/^Bearer\s+/i, "");
      const part = token.split(".")[1];
      if (!part) return false;
      try {
        const normalized = part.replace(/-/g, "+").replace(/_/g, "/");
        const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
        const payload = JSON.parse(atob(padded));
        const data = payload && payload.data ? payload.data : payload;
        return String(data.userId || "") === String(expectedId);
      } catch (_) {
        return false;
      }
    }, targetId, { timeout: 12000 }).then(() => true).catch(() => false);
    if (confirmed) {
      await context.storageState({ path: STORAGE_STATE_PATH });
      lastHektorLoginAt = Date.now();
    }
    return confirmed;
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

async function hektorHtmlRequestWithJar(jar, url) {
  const timeoutMs = 45000;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      redirect: "manual",
      signal: controller.signal,
      headers: {
        Cookie: cookieHeaderFromJar(jar),
        Referer: ADMIN_URL,
        "User-Agent": "Mozilla/5.0 ConsoleWorker/1.0",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      },
    });
    absorbSetCookieHeaders(jar, response.headers);
    const text = await response.text();
    if (response.status === 403) throw new Error(`Hektor 403 on context switch ${url}`);
    if (response.status >= 500) throw new Error(`Hektor ${response.status} on context switch`);
    if (isHektorLoginPage(text)) {
      const error = new Error(`Session Hektor expiree ou invalide sur ${url}`);
      error.code = "HEKTOR_SESSION_EXPIRED";
      throw error;
    }
    return {
      status: response.status,
      location: response.headers.get("location"),
      text,
    };
  } catch (error) {
    if (error && error.name === "AbortError") throw new Error(`Hektor context switch timeout ${timeoutMs}ms on ${url}`);
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function isHektorSessionExpiredError(error) {
  const message = String(error && error.message ? error.message : "");
  return Boolean(error && (
    error.code === "HEKTOR_SESSION_EXPIRED"
    || message.includes("Session Hektor expiree")
    || message.includes("Session console introuvable")
  ));
}

async function switchHektorUserContextOnce(targetId) {
  const state = readHektorStorageState();
  const jar = cookieJarFromStorageState(state);
  const htmlParts = [];
  const autolog = await hektorHtmlRequestWithJar(jar, `${ADMIN_URL}?call=authenticate&mode=autologin&idUser=${encodeURIComponent(targetId)}`);
  htmlParts.push(autolog.text);

  if (autolog.location) {
    const redirectedUrl = new URL(autolog.location, ADMIN_URL).toString();
    const redirected = await hektorHtmlRequestWithJar(jar, redirectedUrl);
    htmlParts.push(redirected.text);
  }

  const admin = await hektorHtmlRequestWithJar(jar, ADMIN_URL);
  htmlParts.push(admin.text);

  const localStorageItems = new Map();
  for (const html of htmlParts) {
    for (const [name, value] of extractLocalStorageSetItems(html).entries()) {
      localStorageItems.set(name, value);
    }
  }

  const token = localStorageItems.get("token");
  const decoded = decodeJwtPayload(token);
  const payload = decoded && decoded.data ? decoded.data : decoded;
  const impersonateUserId = extractImpersonateUserId(localStorageItems.get("impersonate"));
  if ((!token || !payload || String(payload.userId || "") !== targetId) && impersonateUserId !== targetId) {
    if (String(process.env.CONSOLE_HEKTOR_CONTEXT_SWITCH_FALLBACK_PLAYWRIGHT || "true").toLowerCase() !== "false") {
      return switchHektorUserContextWithPlaywright(targetId);
    }
    throw new Error(`Switch HTTP Hektor non confirme pour idUser ${targetId}`);
  }

  saveCookieJarToStorageState(state, jar);
  for (const [name, value] of localStorageItems.entries()) {
    setHektorLocalStorageValue(state, name, value);
  }
  fs.writeFileSync(STORAGE_STATE_PATH, JSON.stringify(state, null, 2), "utf-8");
  lastHektorLoginAt = Date.now();
  return true;
}

async function switchHektorUserContext(idUser) {
  const targetId = String(idUser || "").trim();
  if (!targetId) throw new Error("idUser Hektor requis pour changer de contexte");
  try {
    return await switchHektorUserContextOnce(targetId);
  } catch (error) {
    if (!isHektorSessionExpiredError(error)) throw error;
    await refreshHektorSession(`context_switch_expired_session_${targetId}`);
    return switchHektorUserContextOnce(targetId);
  }
}

async function returnHektorDefaultContextOnce() {
  const state = readHektorStorageState();
  const jar = cookieJarFromStorageState(state);
  const htmlParts = [];

  // Hektor's visible "Retour" action routes to /retour, then to this DEFAULT autologin command.
  const autolog = await hektorHtmlRequestWithJar(jar, `${ADMIN_URL}?call=authenticate&mode=autologin&type=DEFAULT`);
  htmlParts.push(autolog.text);

  if (autolog.location) {
    const redirectedUrl = new URL(autolog.location, ADMIN_URL).toString();
    const redirected = await hektorHtmlRequestWithJar(jar, redirectedUrl);
    htmlParts.push(redirected.text);
  }

  const admin = await hektorHtmlRequestWithJar(jar, ADMIN_URL);
  htmlParts.push(admin.text);

  const localStorageItems = new Map();
  for (const html of htmlParts) {
    for (const [name, value] of extractLocalStorageSetItems(html).entries()) {
      localStorageItems.set(name, value);
    }
  }

  saveCookieJarToStorageState(state, jar);
  for (const [name, value] of localStorageItems.entries()) {
    setHektorLocalStorageValue(state, name, value);
  }
  fs.writeFileSync(STORAGE_STATE_PATH, JSON.stringify(state, null, 2), "utf-8");
  lastHektorLoginAt = Date.now();
}

async function returnHektorDefaultContext() {
  try {
    return await returnHektorDefaultContextOnce();
  } catch (error) {
    if (!isHektorSessionExpiredError(error)) throw error;
    await refreshHektorSession("return_default_expired_session");
    return returnHektorDefaultContextOnce();
  }
}

// Résout le contexte AGENCE d'une entité pour le fallback (négo inactif).
// Annonce -> agence de l'annonce ; contact (pas d'annonce) -> agence du payload
// (déjà résolue par resolveContactAgencyExecutionPayload).
async function resolveAgencyContextForFallback(dossier, payload) {
  const safePayload = payload && typeof payload === "object" ? payload : {};
  const annonceId = dossier && dossier.hektor_annonce_id ? String(dossier.hektor_annonce_id) : null;
  if (annonceId) {
    const ctx = await resolveHektorAnnonceAgencyContext(annonceId, {
      agencyId: safePayload.hektor_agence_id || safePayload.target_hektor_agence_id || null,
    }).catch(() => null);
    if (ctx && ctx.agency_id_user) return ctx;
  }
  // Cas CONTACT (pas d'annonce liée) ou annonce sans contexte agence : on résout l'agence
  // depuis le négo PROPRIÉTAIRE via l'annuaire agence complet. includeInactive: true car le
  // négo est justement inactif/orphelin -> il faut quand même retrouver SON agence.
  const negotiatorId = (dossier && dossier.commercial_id)
    || safePayload.hektor_negociateur_id || safePayload.target_hektor_negociateur_id || null;
  const agencyId = (dossier && dossier.hektor_agence_id)
    || safePayload.hektor_agence_id || safePayload.target_hektor_agence_id || null;
  const email = (dossier && dossier.negociateur_email)
    || safePayload.negociateur_email || safePayload.hektor_user_email || null;
  const tryRows = (filters) =>
    loadHektorNegotiatorAgencyRows({ ...filters, includeInactive: true, limit: 10 }).catch(() => []);
  let rows = [];
  if (negotiatorId) rows = await tryRows({ negotiatorId });
  if (!rows.length && agencyId) rows = await tryRows({ agencyId });
  if (!rows.length && email) rows = await tryRows({ email });
  const row = (Array.isArray(rows) ? rows : []).find((r) => r && r.agence_id_user);
  if (row && row.agence_id_user) {
    return {
      found: true,
      agency_id_user: String(row.agence_id_user),
      hektor_agence_id: row.hektor_agence_id || agencyId || null,
      agency_label: row.agence_nom || safePayload.agence_nom || (dossier && dossier.agence_nom) || null,
    };
  }
  // Dernier recours : agence fournie explicitement dans le payload.
  const agencyIdUser = cleanString(
    safePayload.target_agency_id_user || safePayload.agence_id_user || safePayload.agency_id_user
  );
  if (agencyIdUser) {
    return {
      found: true,
      agency_id_user: agencyIdUser,
      hektor_agence_id: cleanString(safePayload.hektor_agence_id || safePayload.target_hektor_agence_id) || null,
      agency_label: safePayload.target_agency_label || safePayload.agence_nom || null,
    };
  }
  return null;
}

// Source de vérité actif/inactif : app_hektor_negotiator_agency_directory.is_active
// (annuaire COMPLET des négos). On NE s'appuie PLUS sur la présence dans app_user_directory
// (table décimée, qui ne "marchait" que via le hack de fusion des actifs).
async function loadAgencyDirectoryRowForOwner({ email, negotiatorId, userId }) {
  const select = "hektor_negociateur_id,hektor_user_id,hektor_agence_id,agence_id_user,agence_nom,display_name,email,is_active,portable,telephone";
  const tryQuery = async (column, value, op) => {
    if (value == null || String(value).trim() === "") return null;
    const params = new URLSearchParams({ select, limit: "1" });
    params.set(column, op === "ilike" ? `ilike.${normalizeEmail(value)}` : `eq.${String(value).trim()}`);
    const rows = await supabaseRequest(
      `app_hektor_negotiator_agency_directory?${params.toString()}`,
      { method: "GET" }
    ).catch(() => null);
    return Array.isArray(rows) && rows.length ? rows[0] : null;
  };
  return (await tryQuery("hektor_negociateur_id", negotiatorId, "eq"))
    || (await tryQuery("email", email, "ilike"))
    || (await tryQuery("hektor_user_id", userId, "eq"));
}

// Normalise un nom d'agence pour comparaison tolérante (casse / accents / espaces).
function normalizeAgencyName(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

// Le négo PROPRIÉTAIRE de l'entité est-il actif ? On teste le négo PROPRE (email / id négo /
// id user de l'entité), PAS un collègue substitué. Inactif, orphelin OU null -> écriture agence.
async function isOwnerNegotiatorActive(dossier, payload) {
  const safePayload = payload && typeof payload === "object" ? payload : {};
  const email = (dossier && dossier.negociateur_email)
    || safePayload.negociateur_email
    || safePayload.hektor_user_email
    || safePayload.target_hektor_user_email
    || null;
  const negotiatorId = (dossier && dossier.commercial_id)
    || safePayload.hektor_negociateur_id
    || safePayload.target_hektor_negociateur_id
    || null;
  const userId = safePayload.hektor_user_id || safePayload.hektor_id_user || safePayload.target_hektor_user_id || null;
  // Aucun négo identifiable (null) -> traité comme inactif -> écriture via agence.
  if (!email && !negotiatorId && !userId) return false;
  const row = await loadAgencyDirectoryRowForOwner({ email, negotiatorId, userId }).catch(() => null);
  if (!row || row.is_active !== true) return false;
  // Garde-fou cohérence d'agence (négos multi-agences) : le négo résolu peut être ACTIF mais
  // dans une AUTRE agence que le bien (ex. propriétaire à Saint-Étienne inactif, mais commercial_id
  // pointant sur son identité Firminy active). Hektor refuse alors l'écriture ("Credential Error")
  // car ce négo n'est pas propriétaire de CE bien. On le traite comme non-propriétaire-ici ->
  // écriture via l'AGENCE du bien (resolveAgencyContextForFallback). Garde appliquée uniquement
  // quand les DEUX agences sont connues et diffèrent -> aucun impact sur les biens cohérents.
  const ownerAgence = normalizeAgencyName(dossier && dossier.agence_nom);
  const rowAgence = normalizeAgencyName(row.agence_nom);
  if (ownerAgence && rowAgence && ownerAgence !== rowAgence) return false;
  return true;
}

async function ensureHektorExecutionContext(job, dossier, payload, options = {}) {
  // RÈGLE FALLBACK AGENCE (additif, flag-gated) : si le négo PROPRIÉTAIRE de l'entité
  // n'est pas actif, on écrit via l'AGENCE au lieu de laisser substituer un collègue
  // (qui ne pourrait pas écrire une entité qui n'est pas la sienne). Couvre aussi le
  // cas "aucun négo". Activé par CONSOLE_HEKTOR_AGENCY_FALLBACK=true OU write_via_agency.
  // Sans flag : comportement 100% inchangé.
  const agencyFallbackEnabled =
    String(process.env.CONSOLE_HEKTOR_AGENCY_FALLBACK || "false").toLowerCase() === "true"
    || (payload && payload.write_via_agency === true);
  if (agencyFallbackEnabled && !(await isOwnerNegotiatorActive(dossier, payload))) {
    const agencyContext = await resolveAgencyContextForFallback(dossier, payload).catch(() => null);
    if (agencyContext && agencyContext.agency_id_user) {
      await ensureAdminHektorWriteSession(job, "agency_fallback_admin_login");
      await ensureHektorAgencySession(job, agencyContext, "execution_context_agency_fallback");
      await logJob(job.id, "hektor_context", "done", "Negociateur proprietaire inactif -> ecriture via contexte AGENCE (fallback)", {
        hektor_annonce_id: dossier && dossier.hektor_annonce_id ? String(dossier.hektor_annonce_id) : null,
        agency_id_user: agencyContext.agency_id_user,
        agency_label: agencyContext.agency_label || null,
      });
      return { agencyFallback: true, agencyContext };
    }
  }

  const target = await resolveHektorExecutionUser(job, dossier, payload, options);
  if (!target || !target.idUser) {
    if (options.required) {
      throw new Error("Contexte negociateur Hektor requis pour cette ecriture");
    }
    await logJob(job.id, "hektor_context", "running", "Aucun contexte negociateur cible resolu, session courante conservee", {
      prefer_dossier_owner: Boolean(options.preferDossierOwner),
      hektor_annonce_id: dossier && dossier.hektor_annonce_id ? String(dossier.hektor_annonce_id) : null,
    });
    return null;
  }

  const forceRemoteSwitch = options.forceRemoteSwitch !== false;
  let current = currentHektorSessionIdentity();
  if (current && current.userId === String(target.idUser) && !forceRemoteSwitch) {
    await logJob(job.id, "hektor_context", "done", "Contexte Hektor negociateur deja actif", {
      id_user: target.idUser,
      label: target.label,
      source: target.source,
    });
    return target;
  }
  if (current && current.userId === String(target.idUser) && forceRemoteSwitch) {
    await logJob(job.id, "hektor_context", "running", "Verification distante du contexte Hektor negociateur", {
      id_user: target.idUser,
      label: target.label,
      source: target.source,
      current_role: current.role || null,
    });
  }

  current = await ensureAdminHektorWriteSession(job, forceRemoteSwitch ? "context_switch_forced_admin_login" : "context_switch_admin_login");

  await logJob(job.id, "hektor_context", "running", "Changement de contexte Hektor negociateur", {
    current_user_id: current && current.userId ? current.userId : null,
    current_role: current && current.role ? current.role : null,
    target_id_user: target.idUser,
    target_label: target.label,
    source: target.source,
  });
  let switchConfirmed = await switchHektorUserContext(target.idUser);

  let after = currentHektorSessionIdentity();
  if (!after || after.userId !== String(target.idUser)) {
    await logJob(job.id, "hektor_context", "running", "Bascule non confirmee, relance session admin avant nouveau changement", {
      target_id_user: target.idUser,
      target_label: target.label,
      source: target.source,
      switch_confirmed: Boolean(switchConfirmed),
      visible_user_id: after && after.userId ? after.userId : null,
      visible_role: after && after.role ? after.role : null,
    });
    current = await ensureAdminHektorWriteSession(job, "context_switch_retry_admin_login");
    switchConfirmed = await switchHektorUserContext(target.idUser);
    after = currentHektorSessionIdentity();
  }

  if (!after || after.userId !== String(target.idUser)) {
    const allowUnverified = String(process.env.CONSOLE_HEKTOR_ALLOW_UNVERIFIED_CONTEXT || "true").toLowerCase() !== "false";
    const hasConflictingVisibleIdentity = Boolean(after && after.userId && after.userId !== String(target.idUser));
    if (allowUnverified && !hasConflictingVisibleIdentity) {
      await logJob(job.id, "hektor_context", "done", "Contexte Hektor envoye mais identite locale non verifiable", {
        target_id_user: target.idUser,
        target_label: target.label,
        source: target.source,
        switch_confirmed: Boolean(switchConfirmed),
        visible_user_id: after && after.userId ? after.userId : null,
        visible_role: after && after.role ? after.role : null,
      });
      return target;
    }
    await logJob(job.id, "hektor_context", "error", "Bascule Hektor non confirmee, commande arretee avant ecriture", {
      target_id_user: target.idUser,
      target_label: target.label,
      source: target.source,
      switch_confirmed: Boolean(switchConfirmed),
      visible_user_id: after && after.userId ? after.userId : null,
      visible_role: after && after.role ? after.role : null,
    });
    throw new Error(`Bascule Hektor non confirmee pour idUser ${target.idUser}; commande arretee avant ecriture.`);
  }
  await logJob(job.id, "hektor_context", "done", "Contexte Hektor negociateur actif", {
    id_user: after.userId,
    role: after.role,
    alias: after.alias,
    target_label: target.label,
  });
  return target;
}

function hektorCookieHeader() {
  if (!fs.existsSync(STORAGE_STATE_PATH)) throw new Error(`Session console introuvable: ${STORAGE_STATE_PATH}`);
  const state = JSON.parse(fs.readFileSync(STORAGE_STATE_PATH, "utf-8"));
  const cookies = Array.isArray(state.cookies) ? state.cookies : [];
  const now = Date.now() / 1000;
  return cookies
    .filter((cookie) => !cookie.expires || cookie.expires < 0 || cookie.expires > now)
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");
}

function hektorGraphQLAuthorizationHeader() {
  try {
    if (fs.existsSync(STORAGE_STATE_PATH)) {
      const state = JSON.parse(fs.readFileSync(STORAGE_STATE_PATH, "utf-8"));
      const origins = Array.isArray(state.origins) ? state.origins : [];
      const hektorOrigin = HEKTOR_BASE_URL.replace(/\/+$/, "");
      const origin = origins.find((item) => item.origin === hektorOrigin);
      const localStorage = origin && Array.isArray(origin.localStorage) ? origin.localStorage : [];
      const tokenEntry = localStorage.find((item) => item.name === "token");
      if (tokenEntry && tokenEntry.value) {
        return String(tokenEntry.value).startsWith("Bearer ") ? String(tokenEntry.value) : `Bearer ${tokenEntry.value}`;
      }
    }
  } catch (_) {
    // Fall back to token_dump.json below.
  }

  const tokenPath = path.resolve(__dirname, "token_dump.json");
  if (!fs.existsSync(tokenPath)) return null;
  try {
    const dump = JSON.parse(fs.readFileSync(tokenPath, "utf-8"));
    const token = dump && dump.localStorage ? dump.localStorage.token : null;
    if (!token) return null;
    return String(token).startsWith("Bearer ") ? String(token) : `Bearer ${token}`;
  } catch (_) {
    return null;
  }
}

async function hektorFetch(url, options = {}) {
  const timeoutMs = Number(options.timeoutMs || 45000);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
      headers: {
        Cookie: hektorCookieHeader(),
        Referer: ADMIN_URL,
        Origin: HEKTOR_BASE_URL.replace(/\/+$/, ""),
        "X-Requested-With": "XMLHttpRequest",
        ...(options.headers || {}),
      },
    });
    const buffer = Buffer.from(await response.arrayBuffer());
    const text = buffer.toString("utf-8");
    if (!response.ok) throw new Error(`Hektor ${response.status} on ${url}: ${text.slice(0, 300)}`);
    if (isHektorLoginPage(text) && !url.includes("upload_uploadeddoc.php")) {
      throw new Error("Session Hektor expiree ou invalide");
    }
    return {
      response,
      buffer,
      text,
      mimeType: response.headers.get("content-type") || "application/octet-stream",
    };
  } catch (error) {
    if (error && error.name === "AbortError") throw new Error(`Hektor timeout ${timeoutMs}ms on ${url}`);
    const message = error && error.message ? error.message : String(error);
    if (/^(Hektor \d+ on |Session Hektor|Session console)/i.test(message)) throw error;
    const cause = error && error.cause ? error.cause : null;
    const details = [
      message,
      error && error.code ? `code=${error.code}` : null,
      cause && cause.code ? `cause_code=${cause.code}` : null,
      cause && cause.message ? `cause=${cause.message}` : null,
    ].filter(Boolean).join(" | ");
    throw new Error(`Hektor fetch failed on ${url}: ${details || "network error"}`);
  } finally {
    clearTimeout(timeout);
  }
}

async function hektorGraphQLOperation({ operationName, query, variables = {} }) {
  if (!operationName || !query) throw new Error("Operation GraphQL Hektor incomplete");
  const authorization = hektorGraphQLAuthorizationHeader();
  const result = await hektorFetch(`${HEKTOR_BASE_URL.replace(/\/+$/, "")}/ws/GraphQL_Web`, {
    method: "POST",
    body: JSON.stringify({
      operationName,
      query,
      variables,
    }),
    headers: {
      "Content-Type": "application/json",
      ...(authorization ? { Authorization: authorization } : {}),
    },
  });
  const payload = JSON.parse(result.text);
  if (payload.errors && payload.errors.length) {
    throw new Error(`GraphQL Hektor: ${payload.errors.map((item) => item.message || String(item)).join("; ")}`);
  }
  return payload;
}

async function hektorGraphQL(variables) {
  return hektorGraphQLOperation({
    operationName: "PropertyListing",
    query: PROPERTY_LISTING_QUERY,
    variables,
  });
}

async function fetchLatestHektorProperties(page = 1, archived = false) {
  const payload = await hektorGraphQL({
    filters: {
      limit: 50,
      offers: ["SALE"],
      status: "ALL",
      page,
      order: "LATEST",
      sources: ["local"],
      archived,
    },
  });
  return payload && payload.data && payload.data.listing && Array.isArray(payload.data.listing.properties)
    ? payload.data.listing.properties
    : [];
}

async function fetchHektorPropertyById(hektorAnnonceId, options = {}) {
  const id = String(hektorAnnonceId || "").trim();
  if (!id) return null;
  const maxPages = Number(options.maxPages || 8);
  for (const archived of [false, true]) {
    for (let page = 1; page <= maxPages; page += 1) {
      const properties = await fetchLatestHektorProperties(page, archived);
      const found = properties.find((property) => String(property.id) === id);
      if (found) return { property: found, archived, page };
      if (properties.length < 50) break;
    }
  }
  return null;
}

async function fetchHektorPropertyByIdBestEffort(job, hektorAnnonceId, step) {
  try {
    return await fetchHektorPropertyById(hektorAnnonceId, { maxPages: 2 });
  } catch (error) {
    await logJob(job.id, step, "error", "Verification GraphQL Hektor ignoree apres erreur", {
      hektor_annonce_id: String(hektorAnnonceId),
      error: error && error.message ? error.message : String(error),
    });
    return null;
  }
}

async function rememberCreatedHektorAnnonceId(job, hektorAnnonceId) {
  const id = String(hektorAnnonceId || "").trim();
  if (!id) return;
  try {
    await supabaseRequest(`app_console_job?id=eq.${encodeURIComponent(job.id)}`, {
      method: "PATCH",
      prefer: "return=minimal",
      body: JSON.stringify({
        hektor_annonce_id: id,
        updated_at: new Date().toISOString(),
      }),
    });
  } catch (error) {
    await logJob(job.id, "hektor_annonce", "error", "ID annonce creee non rattache au job", {
      hektor_annonce_id: id,
      error: error && error.message ? error.message : String(error),
    });
  }
}

function hektorPropertyFromDetailKeyData(hektorAnnonceId, keyData, payload) {
  if (!keyData || typeof keyData !== "object") return null;
  if (!Object.keys(keyData).length) return null;
  const exactFields = exactHektorWizardFields(payload);
  return {
    id: String(hektorAnnonceId),
    folderNumber: cleanString(keyData.NO_DOSSIER || keyData.no_dossier || keyData.folderNumber || exactFields.NO_DOSSIER || payload.NO_DOSSIER || payload.folder_number),
    createdAt: keyData.createdAt || keyData.date_creation || null,
    status: keyData.status || keyData.etatAnnonce || null,
    isArchived: keyData.archive === "1" || keyData.isArchived === true,
    isDraft: keyData.isDraft === true,
    isBroadcasted: keyData.diffusable === "1" || keyData.isBroadcasted === true,
    isValid: keyData.isValid === true,
    price: keyData.prix || payload.price || null,
    surface: keyData.surfappart || payload.surface || null,
    type: { name: payload.property_type || null },
  };
}

async function confirmCreatedHektorAnnonce(job, idannWizard, payload, beforeIds, startedAtMs) {
  const id = String(idannWizard || "").trim();
  if (!id) return null;

  for (let attempt = 1; attempt <= 6; attempt += 1) {
    await sleep(attempt === 1 ? 1800 : 2500);
    const latest = await fetchLatestHektorProperties(1, false);
    const candidates = latest
      .map((property) => ({ property, score: annonceCreationScore(property, beforeIds, startedAtMs) }))
      .filter((item) => item.score >= 0)
      .sort((left, right) => right.score - left.score);
    if (candidates.length) {
      await logJob(job.id, "hektor_annonce_confirm", "done", "Creation confirmee par liste GraphQL recente", {
        hektor_annonce_id: String(candidates[0].property.id),
        attempt,
      });
      return candidates[0].property;
    }
  }

  try {
    const direct = await fetchHektorPropertyById(id, { maxPages: 8 });
    if (direct && direct.property) {
      await logJob(job.id, "hektor_annonce_confirm", "done", "Creation confirmee par recherche GraphQL directe", {
        hektor_annonce_id: id,
        archived: direct.archived,
        page: direct.page,
      });
      return direct.property;
    }
  } catch (error) {
    if (isHektorForbiddenError(error)) throw error;
    await logJob(job.id, "hektor_annonce_confirm", "error", "Recherche GraphQL directe ignoree apres erreur", {
      hektor_annonce_id: id,
      error: error && error.message ? error.message : String(error),
    });
  }

  const keyData = await fetchHektorAnnonceDetailKeyDataBestEffort(job, id, "hektor_annonce_confirm_api");
  const keyDataProperty = hektorPropertyFromDetailKeyData(id, keyData, payload);
  if (keyDataProperty) {
    await logJob(job.id, "hektor_annonce_confirm", "done", "Creation confirmee par API detail Hektor", {
      hektor_annonce_id: id,
      fields: Object.keys(keyData).slice(0, 30),
    });
    return keyDataProperty;
  }

  await ensureAdminHektorWriteSession(job, "create_annonce_confirm_admin_login");
  const adminDirect = await fetchHektorPropertyById(id, { maxPages: 8 });
  if (adminDirect && adminDirect.property) {
    await logJob(job.id, "hektor_annonce_confirm", "done", "Creation confirmee en session admin par ID Hektor", {
      hektor_annonce_id: id,
      archived: adminDirect.archived,
      page: adminDirect.page,
    });
    return adminDirect.property;
  }

  const adminKeyData = await fetchHektorAnnonceDetailKeyDataBestEffort(job, id, "hektor_annonce_confirm_admin_api");
  const adminKeyDataProperty = hektorPropertyFromDetailKeyData(id, adminKeyData, payload);
  if (adminKeyDataProperty) {
    await logJob(job.id, "hektor_annonce_confirm", "done", "Creation confirmee en session admin par API detail Hektor", {
      hektor_annonce_id: id,
      fields: Object.keys(adminKeyData).slice(0, 30),
    });
    return adminKeyDataProperty;
  }

  return null;
}

async function fetchHektorAnnonceDetailKeyDataBestEffort(job, hektorAnnonceId, step) {
  const id = String(hektorAnnonceId || "").trim();
  if (!id) return null;
  try {
    const result = await hektorFetch(`${HEKTOR_BASE_URL.replace(/\/+$/, "")}/Api/Annonce/AnnonceById/?${new URLSearchParams({
      id,
      version: process.env.HEKTOR_VERSION || process.env.VERSION || "v2",
    }).toString()}`, {
      headers: {
        Accept: "application/json",
        ...(process.env.HEKTOR_JWT ? { jwt: process.env.HEKTOR_JWT } : {}),
      },
    });
    const payload = JSON.parse(result.text);
    return payload && payload.data && payload.data.keyData ? payload.data.keyData : null;
  } catch (error) {
    await logJob(job.id, step, "error", "Verification API Hektor ignoree apres erreur", {
      hektor_annonce_id: id,
      error: error && error.message ? error.message : String(error),
    });
    return null;
  }
}

// date_maj FRAÎCHE d'un contact via le Python (porte 2 / ContactById, qui a le JWT OAuth),
// comme le run quotidien. Léger : juste l'appel API, AUCUN re-sync destructif. Best-effort
// (retourne null sur erreur -> le garde-fou laisse écrire). Renvoie la date_maj (string) ou null.
async function fetchContactDateMajFromApi(job, contactId, step) {
  const id = String(contactId || "").trim();
  if (!id) return null;
  try {
    const out = await runProjectPythonScript(
      ["phase2/sync/contact_datemaj_from_api.py", "--contact-id", id],
      { timeoutMs: 30000, previewSize: 1000 });
    const last = String(out.stdout || "").trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
    const parsed = safeJsonParse(last);
    return parsed && typeof parsed === "object" && parsed.datemaj ? String(parsed.datemaj) : null;
  } catch (error) {
    await logJob(job.id, step, "error", "Lecture date_maj contact (API) ignoree apres erreur", {
      hektor_contact_id: id,
      error: error && error.message ? error.message : String(error),
    });
    return null;
  }
}

// date_maj FRAÎCHE d'une annonce via le Python (porte 2 / AnnonceById, qui a le JWT OAuth),
// comme le run quotidien. Le worker n'a PAS de JWT -> son appel Node direct
// (fetchHektorAnnonceDetailKeyDataBestEffort) faisait 403 et le garde-fou ne bloquait jamais.
// Léger : juste l'appel API, AUCUN re-sync. Best-effort (null sur erreur -> on laisse écrire).
async function fetchAnnonceDateMajFromApi(job, annonceId, step) {
  const id = String(annonceId || "").trim();
  if (!id) return null;
  try {
    const out = await runProjectPythonScript(
      ["phase2/sync/annonce_datemaj_from_api.py", "--annonce-id", id],
      { timeoutMs: 30000, previewSize: 1000 });
    const last = String(out.stdout || "").trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
    const parsed = safeJsonParse(last);
    return parsed && typeof parsed === "object" && parsed.datemaj ? String(parsed.datemaj) : null;
  } catch (error) {
    await logJob(job.id, step, "error", "Lecture date_maj annonce (API) ignoree apres erreur", {
      hektor_annonce_id: id,
      error: error && error.message ? error.message : String(error),
    });
    return null;
  }
}

async function ensureAdminHektorSession(job, reason, options = {}) {
  const requireRootAdmin = options.requireRootAdmin !== false;
  const isExpectedAdmin = (identity) => requireRootAdmin
    ? isHektorRootAdminIdentity(identity)
    : Boolean(identity && identity.role === "ADMIN");
  let current = currentHektorSessionIdentity();
  if (options.forceReturn || !isExpectedAdmin(current)) {
    await logJob(job.id, "hektor_context", "running", "Retour session administrateur Hektor", {
      reason,
      current_user_id: current && current.userId ? current.userId : null,
      current_role: current && current.role ? current.role : null,
      expected_admin_user_id: requireRootAdmin ? HEKTOR_ROOT_ADMIN_USER_ID : null,
    });
    if (options.forceReturn || (current && current.role)) {
      try {
        await returnHektorDefaultContext();
      } catch (error) {
        if (isHektorForbiddenError(error)) throw error;
        await logJob(job.id, "hektor_context", "error", "Retour admin DEFAULT impossible, commande arretee", {
          reason,
          error: error && error.message ? error.message : String(error),
        });
        throw error;
      }
    }
    current = currentHektorSessionIdentity();
    if (!isExpectedAdmin(current)) {
      await refreshHektorSession(reason || "admin_required");
    }
    current = currentHektorSessionIdentity();
  }
  if (!isExpectedAdmin(current)) {
    throw new Error(`Session Hektor administrateur racine requise, session actuelle: ${current && current.role ? current.role : "inconnue"} user_id=${current && current.userId ? current.userId : "inconnu"}`);
  }
  await logJob(job.id, "hektor_context", "done", "Session Hektor administrateur active", {
    user_id: current.userId || null,
    role: current.role || null,
    alias: current.alias || null,
    expected_admin_user_id: requireRootAdmin ? HEKTOR_ROOT_ADMIN_USER_ID : null,
  });
  return current;
}

async function ensureAdminHektorWriteSession(job, reason) {
  return ensureAdminHektorSession(job, reason, { forceReturn: true });
}

async function returnAdminHektorSessionBestEffort(job, reason) {
  try {
    await ensureAdminHektorSession(job, reason, { forceReturn: true });
  } catch (error) {
    if (isHektorForbiddenError(error)) throw error;
    await logJob(job.id, "hektor_context", "error", "Retour administrateur Hektor non confirme apres action", {
      reason,
      error: error && error.message ? error.message : String(error),
    });
  }
}

async function ensureHektorAgencySession(job, agencyContext, reason) {
  const targetId = String(agencyContext && agencyContext.agency_id_user ? agencyContext.agency_id_user : "").trim();
  if (!/^\d+$/.test(targetId)) {
    throw new Error(`idUser agence Hektor invalide pour ${reason}`);
  }

  let current = currentHektorSessionIdentity();
  if (current && current.userId === targetId && current.role === "AGENCE") {
    await logJob(job.id, "hektor_context", "running", "Retour admin force avant reprise du contexte Hektor agence", {
      id_user: targetId,
      role: current.role,
      alias: current.alias || null,
      reason,
    });
  }

  current = await ensureAdminHektorWriteSession(job, `${reason}_admin_login`);

  await logJob(job.id, "hektor_context", "running", "Changement de contexte Hektor agence", {
    reason,
    current_user_id: current && current.userId ? current.userId : null,
    current_role: current && current.role ? current.role : null,
    agency_id_user: targetId,
    agency_label: agencyContext.agency_label || null,
  });

  let switchConfirmed = await switchHektorUserContext(targetId);
  let after = currentHektorSessionIdentity();
  if (!after || after.userId !== targetId || after.role !== "AGENCE") {
    await logJob(job.id, "hektor_context", "running", "Bascule agence non confirmee, relance session admin avant nouveau changement", {
      reason,
      agency_id_user: targetId,
      agency_label: agencyContext.agency_label || null,
      switch_confirmed: Boolean(switchConfirmed),
      visible_user_id: after && after.userId ? after.userId : null,
      visible_role: after && after.role ? after.role : null,
    });
    current = await ensureAdminHektorSession(job, `${reason}_retry_admin_login`, { forceReturn: true });
    switchConfirmed = await switchHektorUserContext(targetId);
    after = currentHektorSessionIdentity();
  }

  if (!after || after.userId !== targetId || after.role !== "AGENCE") {
    await logJob(job.id, "hektor_context", "error", "Bascule agence non confirmee, commande arretee avant ecriture", {
      reason,
      agency_id_user: targetId,
      agency_label: agencyContext.agency_label || null,
      switch_confirmed: Boolean(switchConfirmed),
      visible_user_id: after && after.userId ? after.userId : null,
      visible_role: after && after.role ? after.role : null,
    });
    throw new Error(`Bascule Hektor agence non confirmee pour idUser ${targetId}; commande arretee avant ecriture.`);
  }

  await logJob(job.id, "hektor_context", "done", "Contexte Hektor agence actif", {
    id_user: after.userId,
    role: after.role,
    alias: after.alias || null,
    agency_label: agencyContext.agency_label || null,
    reason,
  });
  return after;
}

function resolveHektorCreationStatus(payload) {
  const raw = firstDefined(payload || {}, [
    "statutAnnonce",
    "statut_annonce",
    "status_annonce",
    "statusAnnonceWizard",
    "creation_status",
    "creationStatus",
  ]);
  const text = String(raw == null ? "" : raw).trim().toLowerCase();
  if (["1", "estimation", "estimate", "estim"].includes(text)) {
    return { statutAnnonce: "1", label: "Estimation" };
  }
  if (["2", "active", "actif", "annonce", "mandat"].includes(text)) {
    return { statutAnnonce: "2", label: "Actif" };
  }
  if (/^\d+$/.test(text)) {
    return { statutAnnonce: text, label: text };
  }
  return { statutAnnonce: "2", label: "Actif" };
}

async function createHektorAnnonceWithPlaywright(job, payload) {
  const creationStatus = resolveHektorCreationStatus(payload);
  if (creationStatus.statutAnnonce !== "2") {
    throw new Error("Fallback Playwright refuse pour une creation Estimation; la route directe Hektor doit confirmer statutAnnonce=1.");
  }
  const headless = String(process.env.CONSOLE_HEKTOR_HEADLESS || "true").toLowerCase() !== "false";
  let browser = null;
  try {
    browser = await chromium.launch(browserLaunchOptions({ headless }));
    const context = await browser.newContext({ storageState: STORAGE_STATE_PATH });
    const page = await context.newPage();
    const captured = [];
    page.on("requestfinished", async (request) => {
      const requestUrl = request.url();
      if (!requestUrl.includes("xmlrpc.php") && !requestUrl.includes("GraphQL_Web")) return;
      const response = await request.response().catch(() => null);
      captured.push({
        method: request.method(),
        url: requestUrl.replace(/\?.*$/, ""),
        status: response ? response.status() : null,
        postData: String(request.postData() || "").slice(0, 220),
      });
    });

    await page.goto(`${ADMIN_URL}?page=/mes-biens/ajouter-un-nouveau-bien`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForSelector("#WizardNext", { timeout: 30000 });
    await page.waitForFunction(() => typeof window.saveAndQuitte === "function", null, { timeout: 30000 });

    const idannWizard = await page.locator("#idannWizard").inputValue();
    await logJob(job.id, "hektor_annonce", "running", "Enregistrement et finalisation annonce via Playwright", {
      idannWizard,
      property_type: payload.property_type || "Appartement",
    });

    await page.evaluate(() => {
      if (typeof window.setDeepCache !== "function") window.setDeepCache = () => {};
      window.saveAndQuitte();
    });
    await page.waitForTimeout(9000);
    await context.storageState({ path: STORAGE_STATE_PATH });

    return {
      idannWizard,
      captured: captured.slice(-12),
    };
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    if (message.includes("Timeout") || message.includes("Navigation") || message.includes("ERR_ABORTED")) {
      throw new Error(`Session Hektor expiree ou invalide: ${message.slice(0, 500)}`);
    }
    throw error;
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

async function createHektorAnnonceWithHttpDirect(job, payload) {
  const offredem = String(payload.offredem ?? payload.offer_demand ?? 0);
  const idType = String(payload.hektor_id_type ?? payload.idType ?? payload.id_type ?? 2);
  const creationStatus = resolveHektorCreationStatus(payload);
  const statutAnnonce = creationStatus.statutAnnonce;
  const programmeNeuf = String(payload.programme_neuf ?? 0);
  const captured = [];
  let idannWizard = null;
  const fetchAfterAnnonceId = async (url, options) => {
    try {
      return await hektorFetch(url, options);
    } catch (error) {
      if (idannWizard) error.createdHektorAnnonceId = idannWizard;
      throw error;
    }
  };

  await logJob(job.id, "hektor_annonce_http", "running", "Creation annonce via commande HTML directe", {
    offredem,
    idType,
    statutAnnonce,
    status_label: creationStatus.label,
    programme_neuf: programmeNeuf,
  });

  const createUrl = `${XMLRPC_URL}?${new URLSearchParams({
    mode: "ajoutebien",
    offredem,
    idType,
    statutAnnonce,
  }).toString()}`;
  const createResponse = await hektorFetch(createUrl, {
    headers: { Referer: `${ADMIN_URL}?page=/mes-biens/ajouter-un-nouveau-bien` },
    timeoutMs: 60000,
  });
  captured.push({
    method: "GET",
    mode: "ajoutebien",
    status: createResponse.response.status,
    bytes: createResponse.buffer.length,
  });

  idannWizard = extractWizardAnnonceId(createResponse.text);
  if (!idannWizard) {
    const error = new Error("Commande ajoutebien executee mais idannWizard introuvable dans la reponse Hektor");
    error.createdHektorAnnonceId = null;
    throw error;
  }

  const wizardBody = new URLSearchParams({
    mode: "ajoutebien_wizardBien",
    offredem,
    idType,
    statutAnnonce,
    idann: idannWizard,
    programme_neuf: programmeNeuf,
  });
  const wizardResponse = await fetchAfterAnnonceId(XMLRPC_URL, {
    method: "POST",
    body: wizardBody,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/ajouter-un-nouveau-bien`,
    },
    timeoutMs: 60000,
  });
  captured.push({
    method: "POST",
    mode: "ajoutebien_wizardBien",
    status: wizardResponse.response.status,
    bytes: wizardResponse.buffer.length,
  });

  const wizardFieldCaptures = await applyHektorCreateWizardFields(
    job,
    fetchAfterAnnonceId,
    idannWizard,
    { offredem, idType, statutAnnonce, programmeNeuf },
    payload,
    wizardResponse.text,
  );
  captured.push(...wizardFieldCaptures);

  const compositionCaptures = await applyHektorCompositionPieces(job, idannWizard, payload);
  captured.push(...compositionCaptures);

  const activationCommands = [
    { champ: "etatAnnonce", val: "1" },
    { champ: "diffusable", val: "0" },
    { champ: "partage", val: "0" },
  ];
  for (const command of activationCommands) {
    const response = await fetchAfterAnnonceId(`${XMLRPC_URL}?${new URLSearchParams({
      mode: "upval",
      champ: command.champ,
      val: command.val,
      id: idannWizard,
    }).toString()}`, {
      headers: { Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(idannWizard)}` },
      timeoutMs: 30000,
    });
    captured.push({
      method: "GET",
      mode: "upval",
      champ: command.champ,
      val: command.val,
      status: response.response.status,
      preview: response.text.slice(0, 80),
    });
  }

  await logJob(job.id, "hektor_annonce_http", "done", "Annonce creee et activee via commandes HTML directes", {
    idannWizard,
    captured,
  });

  return {
    idannWizard,
    captured,
    transport: "http_direct",
  };
}

async function createHektorAnnonce(job, payload) {
  const creationStatus = resolveHektorCreationStatus(payload);
  if (CREATE_HEKTOR_HTTP_DIRECT) {
    try {
      return await createHektorAnnonceWithHttpDirect(job, payload);
    } catch (error) {
      const createdId = error && error.createdHektorAnnonceId ? error.createdHektorAnnonceId : null;
      const sessionExpired = isHektorSessionError(error);
      await logJob(job.id, "hektor_annonce_http", "error", "Creation HTTP directe Hektor echouee", {
        error: error && error.message ? error.message : String(error),
        created_hektor_annonce_id: createdId,
        playwright_fallback: CREATE_HEKTOR_PLAYWRIGHT_FALLBACK && !createdId && !sessionExpired && creationStatus.statutAnnonce === "2",
        session_retry: sessionExpired,
        requested_status: creationStatus.label,
      });
      if (createdId || sessionExpired || !CREATE_HEKTOR_PLAYWRIGHT_FALLBACK || creationStatus.statutAnnonce !== "2") throw error;
    }
  }
  const result = await createHektorAnnonceWithPlaywright(job, payload);
  return {
    ...result,
    transport: "playwright_fallback",
  };
}

function annonceCreationScore(property, beforeIds, startedAtMs) {
  if (!property || beforeIds.has(String(property.id))) return -1;
  if (property.isArchived === true || property.isDraft === true) return -1;
  const createdAtMs = property.createdAt ? Date.parse(property.createdAt) : 0;
  const recentEnough = !Number.isFinite(createdAtMs) || !createdAtMs || createdAtMs >= startedAtMs - (10 * 60 * 1000);
  if (!recentEnough) return -1;
  let score = createdAtMs || startedAtMs;
  if (property.folderNumber == null) score += 1000;
  if (Number(property.price || 0) === 0) score += 1000;
  return score;
}

async function runImmediateAnnonceSyncStep(job, hektorAnnonceId, step) {
  await logJob(job.id, "hektor_annonce_sync", "running", `Sync immediate: ${step.label}`, {
    hektor_annonce_id: hektorAnnonceId,
    args: step.args,
  });
  const output = await runProjectPythonScript(step.args, { timeoutMs: step.timeoutMs, previewSize: step.previewSize || 1800 });
  await logJob(job.id, "hektor_annonce_sync", "done", `Sync immediate terminee: ${step.label}`, {
    hektor_annonce_id: hektorAnnonceId,
    stdout: output.stdout || null,
    stderr: output.stderr || null,
  });
  return { step: step.label, stdout: output.stdout || null, stderr: output.stderr || null };
}

async function runTargetedConsoleMissingFields(job, hektorAnnonceId, reason) {
  const id = String(hektorAnnonceId || "").trim();
  if (!id) return { status: "skipped", reason: "missing_hektor_annonce_id" };
  const args = [
    "phase2/sync/sync_console_missing_fields.py",
    "--hektor-annonce-id",
    id,
    "--annonce-scope",
    "all",
    "--limit",
    "1",
    "--delay-seconds",
    "0",
    "--batch-size",
    "1",
    "--batch-pause-seconds",
    "0",
    "--skip-job-check",
    "--refresh-session-on-expired",
  ];
  await logJob(job.id, "console_missing_fields", "running", "Extraction console ciblee avant reconstruction du detail", {
    hektor_annonce_id: id,
    reason,
    args,
  });
  try {
    const output = await runProjectPythonScript(args, { timeoutMs: 240000, previewSize: 8000 });
    const summary = parseJsonOutput(output.stdout, { raw_stdout: output.stdout || null });
    if (summary && summary.stopped_on_403) {
      throw new Error(`Hektor 403 pendant extraction console ciblee ${id}: ${JSON.stringify(summary.stopped_on_403)}`);
    }
    await logJob(job.id, "console_missing_fields", "done", "Extraction console ciblee terminee", {
      hektor_annonce_id: id,
      reason,
      selected: summary && summary.selected != null ? summary.selected : null,
      extracted: summary && Array.isArray(summary.extracted) ? summary.extracted : [],
      errors: summary && Array.isArray(summary.errors) ? summary.errors : [],
      skipped: summary && summary.skipped != null ? summary.skipped : null,
    });
    return summary;
  } catch (error) {
    if (isHektorForbiddenError(error)) {
      await logJob(job.id, "console_missing_fields", "error", "Hektor 403 pendant extraction console ciblee, arret immediat", {
        hektor_annonce_id: id,
        reason,
        error: error && error.message ? error.message : String(error),
      });
      throw new Error(`Hektor 403 pendant extraction console ciblee ${id}: ${error && error.message ? error.message : String(error)}`);
    }
    await logJob(job.id, "console_missing_fields", "error", "Extraction console ciblee impossible", {
      hektor_annonce_id: id,
      reason,
      error: error && error.message ? error.message : String(error),
    });
    throw error;
  }
}

async function runCreatedAnnonceImmediateSync(job, hektorAnnonceId, options = {}) {
  const id = String(hektorAnnonceId || "").trim();
  if (!id) return { status: "skipped", reason: "missing_hektor_annonce_id" };

  const completed = [];
  completed.push(await runImmediateAnnonceSyncStep(job, id, {
    label: "refresh_single_annonce",
    args: ["phase2/sync/refresh_single_annonce.py", "--id-annonce", id],
    timeoutMs: 120000,
  }));
  // Read-through LÉGER (options.light) : on saute l'extraction Console (champs statiques
  // honoraires / copropriété / diagnostics détaillés). La vignette DPE/GES reste calculée
  // depuis l'API par le push (build_dpe_image_urls_from_api_detail). Gain : ~40s -> ~10-15s.
  if (options.light) {
    completed.push({ step: "console_missing_fields_skipped", summary: { status: "skipped", reason: "light_read_through" } });
  } else {
    const consoleSummary = await runTargetedConsoleMissingFields(job, id, "refresh_console_data");
    completed.push({ step: "console_missing_fields_targeted", summary: consoleSummary });
  }
  completed.push(await runImmediateAnnonceSyncStep(job, id, {
    label: "phase2_push_single_annonce_direct",
    args: [
      "phase2/sync/push_single_annonce_to_supabase.py",
      "--hektor-annonce-id", id,
    ],
    timeoutMs: 90000,
  }));

  return {
    status: "done",
    hektor_annonce_id: id,
    steps: completed.map((item) => item.step),
  };
}

async function loadExistingDetailCacheState(hektorAnnonceId) {
  const id = encodeURIComponent(String(hektorAnnonceId || "").trim());
  if (!id) return { archive: null, historical: null, archiveIndex: null, historicalIndex: null, current: null };
  const select = "select=hektor_annonce_id,requested_by,expires_at&limit=1";
  const [archiveRows, historicalRows, archiveIndexRows, historicalIndexRows, currentRows] = await Promise.all([
    supabaseRequest(`app_archive_annonce_detail_cache?${select}&hektor_annonce_id=eq.${id}`, { method: "GET" }),
    supabaseRequest(`app_historical_annonce_detail_cache?${select}&hektor_annonce_id=eq.${id}`, { method: "GET" }),
    supabaseRequest(`app_archive_annonce_index_current?select=hektor_annonce_id&hektor_annonce_id=eq.${id}&limit=1`, { method: "GET" }),
    supabaseRequest(`app_historical_annonce_index_current?select=hektor_annonce_id&hektor_annonce_id=eq.${id}&limit=1`, { method: "GET" }),
    supabaseRequest(`app_dossier_current?select=hektor_annonce_id&hektor_annonce_id=eq.${id}&limit=1`, { method: "GET" }),
  ]);
  return {
    archive: Array.isArray(archiveRows) && archiveRows.length ? archiveRows[0] : null,
    historical: Array.isArray(historicalRows) && historicalRows.length ? historicalRows[0] : null,
    archiveIndex: Array.isArray(archiveIndexRows) && archiveIndexRows.length ? archiveIndexRows[0] : null,
    historicalIndex: Array.isArray(historicalIndexRows) && historicalIndexRows.length ? historicalIndexRows[0] : null,
    current: Array.isArray(currentRows) && currentRows.length ? currentRows[0] : null,
  };
}

async function rebuildDetailCacheFromLocal(job, hektorAnnonceId, cacheKind, cacheRow, payload) {
  const ttlHours = Number(payload.cache_ttl_hours || payload.ttl_hours || 24);
  const requestedBy = cacheRow && cacheRow.requested_by ? cacheRow.requested_by : job.requested_by;
  const script = cacheKind === "archive"
    ? "Console/prepare_archived_annonce_detail.py"
    : "Console/prepare_historical_annonce_detail.py";
  const label = cacheKind === "archive" ? "archive_detail_cache_refresh" : "historical_detail_cache_refresh";
  const args = [
    script,
    "--hektor-annonce-id",
    String(hektorAnnonceId),
    "--ttl-hours",
    String(Number.isFinite(ttlHours) && ttlHours > 0 ? ttlHours : 24),
  ];
  if (requestedBy) args.push("--requested-by", String(requestedBy));

  await logJob(job.id, label, "running", "Reconstruction du detail cloud deja demande", {
    hektor_annonce_id: String(hektorAnnonceId),
    cache_kind: cacheKind,
  });
  await runTargetedConsoleMissingFields(job, hektorAnnonceId, `${cacheKind}_detail_cache_refresh`);
  const output = await runProjectPythonScript(args, { timeoutMs: 60000 });
  const lastLine = String(output.stdout || "").trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
  const result = safeJsonParse(lastLine);
  await logJob(job.id, label, "done", "Detail cloud reconstruit depuis la base locale", {
    hektor_annonce_id: String(hektorAnnonceId),
    cache_kind: cacheKind,
    result,
  });
  return {
    cache_kind: cacheKind,
    cache_table: cacheKind === "archive" ? "app_archive_annonce_detail_cache" : "app_historical_annonce_detail_cache",
    ...result,
  };
}

async function deleteDetailCache(job, hektorAnnonceId, cacheKind, reason) {
  const table = cacheKind === "archive" ? "app_archive_annonce_detail_cache" : "app_historical_annonce_detail_cache";
  await supabaseRequest(`${table}?hektor_annonce_id=eq.${encodeURIComponent(String(hektorAnnonceId))}`, {
    method: "DELETE",
    prefer: "return=minimal",
  });
  await logJob(job.id, "detail_cache_refresh", "done", "Cache detail cloud obsolete supprime", {
    hektor_annonce_id: String(hektorAnnonceId),
    cache_kind: cacheKind,
    reason,
  });
  return { cache_kind: cacheKind, cache_table: table, status: "deleted", reason };
}

async function rebuildRequestedDetailCaches(job, hektorAnnonceId, payload = {}) {
  const cacheState = await loadExistingDetailCacheState(hektorAnnonceId);
  const rebuilt = [];
  if (cacheState.historicalIndex) {
    if (cacheState.historical) {
      rebuilt.push(await rebuildDetailCacheFromLocal(job, hektorAnnonceId, "historical", cacheState.historical, payload));
    }
    if (cacheState.archive) {
      rebuilt.push(await deleteDetailCache(job, hektorAnnonceId, "archive", "annonce_now_historical"));
    }
  } else if (cacheState.archiveIndex) {
    if (cacheState.archive) {
      rebuilt.push(await rebuildDetailCacheFromLocal(job, hektorAnnonceId, "archive", cacheState.archive, payload));
    }
    if (cacheState.historical) {
      rebuilt.push(await deleteDetailCache(job, hektorAnnonceId, "historical", "annonce_now_archived"));
    }
  } else if (cacheState.current) {
    if (cacheState.archive) {
      rebuilt.push(await deleteDetailCache(job, hektorAnnonceId, "archive", "annonce_now_current"));
    }
    if (cacheState.historical) {
      rebuilt.push(await deleteDetailCache(job, hektorAnnonceId, "historical", "annonce_now_current"));
    }
  } else {
    if (cacheState.historical) {
      rebuilt.push(await rebuildDetailCacheFromLocal(job, hektorAnnonceId, "historical", cacheState.historical, payload));
    }
    if (cacheState.archive) {
      rebuilt.push(await rebuildDetailCacheFromLocal(job, hektorAnnonceId, "archive", cacheState.archive, payload));
    }
  }
  if (!rebuilt.length) {
    await logJob(job.id, "detail_cache_refresh", "done", "Aucun detail cloud deja demande a reconstruire", {
      hektor_annonce_id: String(hektorAnnonceId),
    });
  }
  return {
    status: rebuilt.length ? "rebuilt" : "skipped",
    rebuilt,
  };
}

async function handleRefreshConsoleData(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorAnnonceId = String(job.hektor_annonce_id || payload.hektor_annonce_id || "").trim();
  if (!hektorAnnonceId) throw new Error("hektor_annonce_id required for refresh_console_data");
  await logJob(job.id, "refresh_console_data", "running", "Synchronisation differee des donnees annonce", {
    hektor_annonce_id: hektorAnnonceId,
    reason: payload.reason || null,
    parent_job_id: payload.parent_job_id || null,
  });
  const result = await runCreatedAnnonceImmediateSync(job, hektorAnnonceId, { light: payload.light === true });
  // Read-through signature (sans 2e job côté app) : à l'ouverture de l'annonce, on rafraîchit l'état
  // signature ET on récupère automatiquement le PDF signé. Best-effort, ne fait jamais échouer le refresh.
  let signatureSync = null;
  try {
    const drow = await supabaseRequest(`app_dossier_current?select=app_dossier_id,hektor_annonce_id&hektor_annonce_id=eq.${encodeURIComponent(hektorAnnonceId)}&limit=1`, { method: "GET" });
    const dossier = Array.isArray(drow) && drow[0]
      ? { app_dossier_id: drow[0].app_dossier_id, hektor_annonce_id: hektorAnnonceId }
      : { hektor_annonce_id: hektorAnnonceId };
    const signedFetched = await reconcileSignatureStates(job, dossier, "refresh_console_data", "all");
    signatureSync = { signed_fetched: signedFetched };
  } catch (error) {
    signatureSync = { error: error && error.message ? error.message : String(error) };
  }
  // Création optimiste : le vrai bien est maintenant dans Supabase -> on retire la ligne provisoire
  // correspondante (no-op pour les annonces normales : 0 ligne supprimée). Best effort.
  await cleanupProvisionalForAnnonce(hektorAnnonceId);
  const cacheRefresh = await rebuildRequestedDetailCaches(job, hektorAnnonceId, payload);
  return {
    ...result,
    status: "synced",
    reason: payload.reason || null,
    parent_job_id: payload.parent_job_id || null,
    cache_refresh: cacheRefresh,
    signature_sync: signatureSync,
  };
}

// Pipeline de rafraîchissement d'UN contact : Hektor -> local -> Supabase
// (détail ContactById -> normalize -> build couche contacts -> push Supabase).
// Extrait de handleRefreshConsoleContactData pour être réutilisé À L'IDENTIQUE par
// le garde-fou anti-écrasement de update_hektor_contact_search (correctif n°1).
async function runContactRefreshPipeline(job, hektorContactId, logCategory = "refresh_console_contact_data") {
  // Read-through fusionné (optim n°8) : les 4 étapes (detail -> normalize -> build ->
  // push) tournent dans UN SEUL process Python (refresh_contact_inproc.py) au lieu de
  // 4 lancements séparés. Mêmes flags qu'avant, scripts d'origine inchangés (le chef
  // d'orchestre les rejoue via runpy). Gain mesuré ~3-4 s (3 démarrages Python en moins).
  // Échec d'une étape -> code non nul -> runProjectPythonScript rejette -> job en erreur
  // (comportement identique à l'ancien enchaînement séquentiel).
  const output = await runProjectPythonScript([
    "phase2/sync/refresh_contact_inproc.py",
    "--contact-id",
    hektorContactId,
  ], { timeoutMs: 180000, previewSize: 8000 });
  await logJob(job.id, logCategory, "running", "Read-through contact fusionne (1 process)", {
    hektor_contact_id: hektorContactId,
    stdout: output.stdout,
    stderr: output.stderr,
  });

  // Compat appelants : la sortie combinée est renvoyée sous les 4 clés historiques.
  return { detailOutput: output, normalizeOutput: output, buildOutput: output, pushOutput: output };
}

async function handleRefreshConsoleContactData(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorContactId = String(payload.hektor_contact_id || payload.contact_id || "").trim();
  if (!/^\d+$/.test(hektorContactId)) throw new Error("hektor_contact_id numerique requis pour refresh_console_contact_data");

  await logJob(job.id, "refresh_console_contact_data", "running", "Synchronisation differee du contact", {
    hektor_contact_id: hektorContactId,
    reason: payload.reason || null,
    parent_job_id: payload.parent_job_id || null,
  });

  const { detailOutput, normalizeOutput, buildOutput, pushOutput } = await runContactRefreshPipeline(job, hektorContactId, "refresh_console_contact_data");

  await logJob(job.id, "refresh_console_contact_data", "done", "Contact reconstruit et pousse vers Supabase", {
    hektor_contact_id: hektorContactId,
    normalize_stdout: normalizeOutput.stdout,
    build_stdout: buildOutput.stdout,
    push_stdout: pushOutput.stdout,
  });

  return {
    status: "synced",
    hektor_contact_id: hektorContactId,
    reason: payload.reason || null,
    parent_job_id: payload.parent_job_id || null,
    detail_stdout: detailOutput.stdout,
    build_stdout: buildOutput.stdout,
    push_stdout: pushOutput.stdout,
  };
}

async function handlePrepareArchivedAnnonceDetail(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorAnnonceId = String(job.hektor_annonce_id || payload.hektor_annonce_id || "").trim();
  if (!hektorAnnonceId) throw new Error("hektor_annonce_id required for prepare_archived_annonce_detail");
  await logJob(job.id, "archive_detail_cache", "running", "Preparation du detail archive depuis la base locale", {
    hektor_annonce_id: hektorAnnonceId,
    ttl_hours: payload.ttl_hours || 24,
  });
  const args = [
    "Console/prepare_archived_annonce_detail.py",
    "--hektor-annonce-id",
    hektorAnnonceId,
    "--ttl-hours",
    String(payload.ttl_hours || 24),
  ];
  if (job.requested_by) {
    args.push("--requested-by", String(job.requested_by));
  }
  await runTargetedConsoleMissingFields(job, hektorAnnonceId, "prepare_archived_annonce_detail");
  const output = await runProjectPythonScript(args, { timeoutMs: 60000 });
  const lastLine = String(output.stdout || "").trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
  const result = safeJsonParse(lastLine);
  await logJob(job.id, "archive_detail_cache", "done", "Detail archive disponible temporairement dans Supabase", {
    hektor_annonce_id: hektorAnnonceId,
    result,
  });
  return {
    ...result,
    hektor_annonce_id: hektorAnnonceId,
    cache_table: "app_archive_annonce_detail_cache",
  };
}

async function handlePrepareHistoricalAnnonceDetail(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorAnnonceId = String(job.hektor_annonce_id || payload.hektor_annonce_id || "").trim();
  if (!hektorAnnonceId) throw new Error("hektor_annonce_id required for prepare_historical_annonce_detail");
  await logJob(job.id, "historical_detail_cache", "running", "Preparation du detail Vendu/Clos depuis la base locale", {
    hektor_annonce_id: hektorAnnonceId,
    ttl_hours: payload.ttl_hours || 24,
  });
  const args = [
    "Console/prepare_historical_annonce_detail.py",
    "--hektor-annonce-id",
    hektorAnnonceId,
    "--ttl-hours",
    String(payload.ttl_hours || 24),
  ];
  if (job.requested_by) {
    args.push("--requested-by", String(job.requested_by));
  }
  await runTargetedConsoleMissingFields(job, hektorAnnonceId, "prepare_historical_annonce_detail");
  const output = await runProjectPythonScript(args, { timeoutMs: 60000 });
  const lastLine = String(output.stdout || "").trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
  const result = safeJsonParse(lastLine);
  await logJob(job.id, "historical_detail_cache", "done", "Detail Vendu/Clos disponible temporairement dans Supabase", {
    hektor_annonce_id: hektorAnnonceId,
    result,
  });
  return {
    ...result,
    hektor_annonce_id: hektorAnnonceId,
    cache_table: "app_historical_annonce_detail_cache",
  };
}

function isHektorLoginPage(text) {
  const normalized = String(text || "").slice(0, 20000).toLowerCase();
  return (
    normalized.includes("ma-boite-immo.com/connexion") ||
    normalized.includes('type="password"') ||
    normalized.includes("type='password'") ||
    normalized.includes("name=\"password\"") ||
    normalized.includes("name='password'") ||
    (normalized.includes("<form") && normalized.includes("mot de passe") && normalized.includes("connexion"))
  );
}

async function fetchConsoleDocumentEntries(hektorAnnonceId) {
  const id = encodeURIComponent(String(hektorAnnonceId));
  const endpoints = [
    {
      source: "hektor_console",
      visibility: "unknown",
      url: `${XMLRPC_URL}?mode=chargeannonce_Documents&id=${id}&lang=fr`,
    },
    {
      source: "hektor_console_uploaded_private",
      visibility: "private",
      url: `${XMLRPC_URL}?mode=UploadedDocument_list&id_foreign=${id}&type=bien&idContentDiv=listDocUpload_privee&docType=privee`,
    },
    {
      source: "hektor_console_uploaded_shared",
      visibility: "shared",
      url: `${XMLRPC_URL}?mode=UploadedDocument_list&id_foreign=${id}&type=bien&public=2&idContentDiv=listDocUpload_partage&docType=partage`,
    },
  ];
  const entries = [];
  for (const endpoint of endpoints) {
    const result = await hektorFetch(endpoint.url);
    entries.push(...extractDocumentEntries(result.text, endpoint.source, endpoint.visibility));
  }
  return entries;
}

async function fetchConsolePhotoEntries(hektorAnnonceId) {
  const id = encodeURIComponent(String(hektorAnnonceId));
  const endpoints = [
    {
      visible: true,
      url: `${XMLRPC_URL}?mode=vignettes&id=${id}&sortBy=byOrder`,
    },
    {
      visible: false,
      url: `${XMLRPC_URL}?mode=vignettes_hidden&id=${id}&sortBy=byOrder`,
    },
  ];
  const entries = [];
  for (const endpoint of endpoints) {
    const result = await hektorFetch(endpoint.url);
    entries.push(...extractConsolePhotoEntries(result.text, endpoint.visible));
  }
  const byId = new Map();
  for (const entry of entries) {
    byId.set(entry.hektor_photo_id, entry);
  }
  return Array.from(byId.values()).sort((left, right) => {
    if (left.visible !== right.visible) return left.visible ? -1 : 1;
    return Number(left.sort_order || 9999) - Number(right.sort_order || 9999);
  });
}

async function upsertConsolePhotos(dossier, entries) {
  const now = new Date().toISOString();
  const rows = entries.map((entry) => ({
    app_dossier_id: Number(dossier.app_dossier_id),
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    hektor_photo_id: entry.hektor_photo_id,
    filename: entry.filename || null,
    url_preview: entry.url_preview || null,
    url_hd: entry.url_hd || null,
    visible: Boolean(entry.visible),
    legend: entry.legend || null,
    sort_order: entry.sort_order || null,
    source: "hektor_console",
    source_json: entry.source_json || {},
    synced_at: now,
    updated_at: now,
  }));

  if (rows.length) {
    await supabaseRequest("app_console_photo?on_conflict=hektor_annonce_id,hektor_photo_id", {
      method: "POST",
      prefer: "resolution=merge-duplicates,return=minimal",
      body: JSON.stringify(rows),
    });
  }

  const keepIds = new Set(rows.map((row) => row.hektor_photo_id));
  const existing = await supabaseRequest(`app_console_photo?hektor_annonce_id=eq.${encodeURIComponent(String(dossier.hektor_annonce_id))}&select=id,hektor_photo_id`, {
    method: "GET",
  });
  const obsoleteIds = (Array.isArray(existing) ? existing : [])
    .filter((row) => row.hektor_photo_id && !keepIds.has(String(row.hektor_photo_id)))
    .map((row) => row.id)
    .filter(Boolean);
  if (obsoleteIds.length) {
    await supabaseRequest(`app_console_photo?id=in.(${obsoleteIds.map((id) => encodeURIComponent(id)).join(",")})`, {
      method: "DELETE",
      prefer: "return=minimal",
    });
  }

  return rows;
}

function entryPriority(entry) {
  if (entry.visibility === "private") return 3;
  if (entry.visibility === "shared") return 2;
  return 1;
}

function dedupeDocumentEntries(entries) {
  const byDocumentId = new Map();
  for (const entry of entries) {
    const previous = byDocumentId.get(entry.hektor_document_id);
    if (!previous || entryPriority(entry) > entryPriority(previous)) {
      byDocumentId.set(entry.hektor_document_id, entry);
    }
  }
  return Array.from(byDocumentId.values()).sort((left, right) => {
    return String(left.document_name).localeCompare(String(right.document_name), "fr", { sensitivity: "base" });
  });
}

async function loadExistingDocuments(hektorAnnonceId) {
  const params = new URLSearchParams({
    select: "*",
    hektor_annonce_id: `eq.${hektorAnnonceId}`,
  });
  const rows = await supabaseRequest(`app_console_document?${params.toString()}`, { method: "GET" });
  const byDocumentId = new Map();
  const byKey = new Map();
  for (const row of Array.isArray(rows) ? rows : []) {
    if (row.hektor_document_id && row.source) {
      byKey.set(`${row.hektor_document_id}:${row.source}`, row);
    }
    const previous = byDocumentId.get(row.hektor_document_id);
    if (!previous || entryPriority(row) > entryPriority(previous)) {
      byDocumentId.set(row.hektor_document_id, row);
    }
  }
  return {
    rows: Array.isArray(rows) ? rows : [],
    byDocumentId,
    byKey,
  };
}

async function upsertConsoleDocuments(dossier, entries) {
  const selectedEntries = dedupeDocumentEntries(entries);
  const existing = await loadExistingDocuments(String(dossier.hektor_annonce_id));
  const now = new Date().toISOString();
  const selectedKeys = new Set(selectedEntries.map((entry) => `${entry.hektor_document_id}:${entry.source}`));
  const rows = selectedEntries.map((entry) => {
    const key = `${entry.hektor_document_id}:${entry.source}`;
    const current = existing.byKey.get(key) || existing.byDocumentId.get(entry.hektor_document_id) || {};
    return {
      id: current.id || crypto.randomUUID(),
      app_dossier_id: Number(dossier.app_dossier_id),
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      hektor_document_id: entry.hektor_document_id,
      document_type: entry.document_type,
      document_name: entry.document_name,
      source: entry.source,
      visibility: entry.visibility,
      storage_bucket: current.storage_bucket || null,
      storage_path: current.storage_path || null,
      storage_status: current.storage_status || "local_only",
      file_size: current.file_size || null,
      sha256: current.sha256 || null,
      mime_type: current.mime_type || null,
      synced_at: now,
      archive_policy: current.archive_policy || null,
      metadata_json: {
        ...(current.metadata_json || {}),
        console_url: entry.console_url,
        technical_name: entry.technical_name,
        transfer_name: entry.transfer_name,
        hektor_uploaded_document_id: entry.hektor_uploaded_document_id,
        signature: entry.signature || null,
      },
      updated_at: now,
    };
  });
  const preservedIds = new Set(rows.map((row) => row.id).filter(Boolean));
  if (!rows.length) return [];
  await supabaseRequest("app_console_document?on_conflict=hektor_annonce_id,source,hektor_document_id", {
    method: "POST",
    prefer: "resolution=merge-duplicates,return=minimal",
    body: JSON.stringify(rows),
  });
  const duplicateIds = existing.rows
    .filter((row) => row.hektor_document_id && !selectedKeys.has(`${row.hektor_document_id}:${row.source}`) && selectedEntries.some((entry) => entry.hektor_document_id === row.hektor_document_id))
    .map((row) => row.id)
    .filter((id) => id && !preservedIds.has(id));

  if (duplicateIds.length) {
    const ids = duplicateIds.map((id) => encodeURIComponent(id)).join(",");
    await supabaseRequest(`app_console_document?id=in.(${ids})`, {
      method: "DELETE",
      prefer: "return=minimal",
    });
  }
  return rows;
}

async function persistConsoleDocumentFile(dossier, document, options = {}) {
  const metadata = document.metadata_json || {};
  const consoleUrl = metadata.console_url;
  const filename = safeFilename(document.document_name, `${document.id}.bin`);
  const storageFilename = storageSafeFilename(document.document_name, `${document.id}.bin`);
  const localPath = metadata.local_archive_path || localDocumentPath(document.hektor_annonce_id, document.id, filename);
  let file;

  if (isReadableFile(localPath)) {
    file = readLocalArchiveFile(localPath, document.mime_type);
  } else {
    if (!consoleUrl) throw new Error(`URL Console absente pour document ${document.id}`);
    file = await hektorFetch(consoleUrl, { headers: { Accept: "*/*" } });
    writeLocalArchiveFile(localPath, file.buffer);
  }

  const mimeType = normalizeMimeType(file.mimeType, filename);
  const digest = sha256Buffer(file.buffer);
  const cloudWanted = Boolean(options.cloud);
  const storagePath = document.storage_path || `annonces/${document.hektor_annonce_id}/documents/${document.id}/${storageFilename}`;

  if (cloudWanted) {
    await uploadStorageObject(storagePath, file.buffer, mimeType);
  }

  const nextStatus = cloudWanted ? "cloud_available" : (document.storage_status === "cloud_available" ? "cloud_available" : "local_only");
  const nextMetadata = {
    ...metadata,
    ...localArchiveMetadata(localPath),
  };

  await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(document.id)}`, {
    method: "PATCH",
    prefer: "return=minimal",
    body: JSON.stringify({
      storage_bucket: cloudWanted ? STORAGE_BUCKET : document.storage_bucket,
      storage_path: cloudWanted ? storagePath : document.storage_path,
      storage_status: nextStatus,
      file_size: file.buffer.length,
      sha256: digest,
      mime_type: mimeType,
      synced_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata_json: nextMetadata,
    }),
  });

  return {
    document_id: document.id,
    local_path: localPath,
    storage_path: cloudWanted ? storagePath : document.storage_path,
    cloud_available: cloudWanted || document.storage_status === "cloud_available",
    bytes: file.buffer.length,
    sha256: digest,
  };
}

async function persistProvidedDocumentFile(document, buffer, mimeType, options = {}) {
  const metadata = document.metadata_json || {};
  const filename = safeFilename(document.document_name, `${document.id}.bin`);
  const storageFilename = storageSafeFilename(document.document_name, `${document.id}.bin`);
  const localPath = metadata.local_archive_path || localDocumentPath(document.hektor_annonce_id, document.id, filename);
  writeLocalArchiveFile(localPath, buffer);

  const cleanMimeType = normalizeMimeType(mimeType, filename);
  const digest = sha256Buffer(buffer);
  const cloudWanted = Boolean(options.cloud);
  const storagePath = document.storage_path || `annonces/${document.hektor_annonce_id}/documents/${document.id}/${storageFilename}`;
  if (cloudWanted) {
    await uploadStorageObject(storagePath, buffer, cleanMimeType);
  }

  await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(document.id)}`, {
    method: "PATCH",
    prefer: "return=minimal",
    body: JSON.stringify({
      storage_bucket: cloudWanted ? STORAGE_BUCKET : document.storage_bucket,
      storage_path: cloudWanted ? storagePath : document.storage_path,
      storage_status: cloudWanted ? "cloud_available" : "local_only",
      file_size: buffer.length,
      sha256: digest,
      mime_type: cleanMimeType,
      synced_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata_json: {
        ...metadata,
        ...localArchiveMetadata(localPath),
      },
    }),
  });

  return { local_path: localPath, storage_path: cloudWanted ? storagePath : document.storage_path, bytes: buffer.length, sha256: digest };
}

// Dezip minimal (sans dependance) : extrait le 1er PDF d'un buffer ZIP via la Central Directory + zlib.
// Le ZIP du doc signe (ImmoSign-downloadProcedureZip) contient le PDF signe (deflate ou stored).
function extractPdfFromZip(buf) {
  if (!Buffer.isBuffer(buf) || buf.length < 22) throw new Error("ZIP vide/invalide");
  let eocd = -1;
  const minEocd = Math.max(0, buf.length - 22 - 65536);
  for (let i = buf.length - 22; i >= minEocd; i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("ZIP EOCD introuvable");
  const count = buf.readUInt16LE(eocd + 10);
  let off = buf.readUInt32LE(eocd + 16);
  const files = [];
  for (let n = 0; n < count && off + 46 <= buf.length; n++) {
    if (buf.readUInt32LE(off) !== 0x02014b50) break;
    const method = buf.readUInt16LE(off + 10);
    const compSize = buf.readUInt32LE(off + 20);
    const nameLen = buf.readUInt16LE(off + 28);
    const extraLen = buf.readUInt16LE(off + 30);
    const commentLen = buf.readUInt16LE(off + 32);
    const lhOff = buf.readUInt32LE(off + 42);
    const name = buf.toString("utf8", off + 46, off + 46 + nameLen);
    files.push({ name, method, compSize, lhOff });
    off += 46 + nameLen + extraLen + commentLen;
  }
  if (!files.length) throw new Error("ZIP sans fichier");
  const pick = files.find((f) => /\.pdf$/i.test(f.name)) || files[0];
  const lh = pick.lhOff;
  if (buf.readUInt32LE(lh) !== 0x04034b50) throw new Error("ZIP local header invalide");
  const dataStart = lh + 30 + buf.readUInt16LE(lh + 26) + buf.readUInt16LE(lh + 28);
  const data = buf.subarray(dataStart, dataStart + pick.compSize);
  const out = pick.method === 0 ? Buffer.from(data) : zlib.inflateRawSync(data);
  return { name: pick.name, buffer: out };
}

// Recupere le PDF SIGNE d'une procedure ImmoSign (ZIP -> PDF), l'archive (storage + local),
// et l'enregistre dans metadata_json.signed_document SANS ecraser le reste (la sync ne touche pas cette cle).
async function downloadSignedProcedureDocument(dossier, document) {
  const metadata = document.metadata_json || {};
  const sig = metadata.signature || {};
  const procId = sig.procedure_id;
  if (!procId) return null;
  const url = `${XMLRPC_URL}?mode=ImmoSign-downloadProcedureZip&procedureId=${encodeURIComponent(procId)}`;
  const res = await hektorFetch(url, { headers: { Accept: "*/*" } });
  const zip = res.buffer;
  if (!zip || zip.length < 4 || zip.readUInt32LE(0) !== 0x04034b50) {
    throw new Error(`Reponse non-ZIP pour la procedure ${procId} (${(res.text || "").slice(0, 120)})`);
  }
  const pdf = extractPdfFromZip(zip);
  const baseName = String(document.document_name || "document").replace(/\.pdf$/i, "");
  const storageFilename = storageSafeFilename(`${baseName} - signe.pdf`, `signed-${document.id}.pdf`);
  const storagePath = `annonces/${document.hektor_annonce_id}/documents/${document.id}/signed/${storageFilename}`;
  await uploadStorageObject(storagePath, pdf.buffer, "application/pdf");
  const localPath = localDocumentPath(document.hektor_annonce_id, document.id, `signed/${safeFilename(storageFilename, "signe.pdf")}`);
  try { writeLocalArchiveFile(localPath, pdf.buffer); } catch (_e) { /* archive locale best-effort */ }
  const signed_document = {
    storage_bucket: STORAGE_BUCKET,
    storage_path: storagePath,
    filename: storageFilename,
    size: pdf.buffer.length,
    sha256: sha256Buffer(pdf.buffer),
    mime_type: "application/pdf",
    procedure_id: procId,
    signed_at: sig.signed_at || null,
    downloaded_at: new Date().toISOString(),
    local_archive_path: localPath,
  };
  // relit la ligne pour fusionner sur le metadata le plus recent
  const fresh = await loadConsoleDocumentById(document.id).catch(() => null);
  const md = (fresh && fresh.metadata_json) || metadata || {};
  // IMPORTANT : on fait pointer la COLONNE storage_path vers le PDF signe (le signe remplace l'original).
  // C'est requis pour la policy storage 'hektor_console_documents_read_scope' (lecture autorisee seulement
  // si storage_path = nom de l'objet + cloud_available) -> sinon "Object not found" cote app.
  await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(document.id)}`, {
    method: "PATCH",
    prefer: "return=minimal",
    body: JSON.stringify({
      storage_bucket: STORAGE_BUCKET,
      storage_path: storagePath,
      storage_status: "cloud_available",
      file_size: pdf.buffer.length,
      sha256: signed_document.sha256,
      mime_type: "application/pdf",
      metadata_json: { ...md, signed_document },
      synced_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }),
  });
  return signed_document;
}

// Map des etats de signature par hektor_doc_id, lue sur chargeannonce_Documents (qui liste TOUS les docs,
// y compris les SIGNES — qui perdent leur lien force_transfert et sont donc invisibles pour extractDocumentEntries).
function buildSignatureMapFromHtml(html) {
  const map = new Map();
  const parts = String(html || "").split('<div class="tbodyContent tbodyContainer');
  for (let i = 1; i < parts.length; i++) {
    const row = '<div class="tbodyContent tbodyContainer' + parts[i];
    if (!/docBtnSign_/.test(row)) continue;
    const sig = parseSignatureFromRow(row);
    if (!sig || !sig.hektor_doc_id) continue;
    const nameMatch = row.match(/<div[^>]*tdContent[^>]*>\s*([^<]+\.pdf)\s*<\/div>/i) || row.match(/([^>\s][^<]*\.pdf)/i);
    sig.document_name = nameMatch ? decodeHtml(nameMatch[1]).trim() : `Document ${sig.hektor_doc_id}`;
    map.set(String(sig.hektor_doc_id), sig);
  }
  return map;
}

// Cree (ou retrouve) une ligne dediee pour un doc SIGNE non rattachable a une ligne existante.
async function upsertSyntheticSignedRow(dossier, sig) {
  const key = `immosign-signed-${sig.hektor_doc_id}-${sig.doc_type}`;
  const params = new URLSearchParams({
    select: "*",
    hektor_annonce_id: `eq.${dossier.hektor_annonce_id}`,
    hektor_document_id: `eq.${key}`,
    limit: "1",
  });
  const found = await supabaseRequest(`app_console_document?${params.toString()}`, { method: "GET" });
  if (Array.isArray(found) && found[0]) return found[0];
  const now = new Date().toISOString();
  const row = {
    id: crypto.randomUUID(),
    app_dossier_id: Number(dossier.app_dossier_id),
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    hektor_document_id: key,
    document_type: "document",
    document_name: sig.document_name || `Mandat signe ${sig.hektor_doc_id}`,
    source: "hektor_immosign_signed",
    visibility: "private",
    storage_status: "local_only",
    synced_at: now,
    updated_at: now,
    metadata_json: { signature: sig },
  };
  await supabaseRequest("app_console_document?on_conflict=hektor_annonce_id,source,hektor_document_id", {
    method: "POST",
    prefer: "resolution=merge-duplicates,return=minimal",
    body: JSON.stringify([row]),
  });
  return row;
}

// Detecte les docs signes via la map empreintes, met a jour/ cree la ligne, et recupere le PDF signe.
// Réconcilie l'état signature de TOUS les docs (to_send/pending/signed) à partir de la map empreintes
// (chargeannonce_Documents = liste complète, signés compris qui perdent leur force_transfert), met à jour
// la ligne suivie (par hektor_doc_id) ou crée une ligne synthétique pour un signé, et récupère le PDF signé.
// Utilisée par la sync documents ET par le read-through (1 passe légère : 1 fetch + map + quelques PATCH).
// gateMode: "pending" = ne s'active QUE si un mandat est EN ATTENTE (read-through a l'ouverture) ;
//           "all"     = aussi "a envoyer" + "signe pas encore recupere" (run quotidien, filet de securite
//                       qui rattrape le cas a_envoyer->signe le meme jour, le signe perdant son force_transfert).
async function reconcileSignatureStates(job, dossier, logCat = "hektor", gateMode = "all") {
  let signedFetched = 0;
  if (!dossier || !dossier.hektor_annonce_id) return 0;
  const existing = await loadExistingDocuments(String(dossier.hektor_annonce_id));
  // GARDE-FOU : ne lit Hektor QUE s'il y a un mandat a traiter. Sinon on sort sans aucun appel Hektor.
  const hasWork = existing.rows.some((r) => {
    const sig = r.metadata_json && r.metadata_json.signature;
    if (!sig) return false;
    if (sig.status === "pending") return true;
    if (gateMode === "all" && sig.status === "to_send") return true;
    if (gateMode === "all" && sig.status === "signed" && !(r.metadata_json && r.metadata_json.signed_document)) return true;
    return false;
  });
  if (!hasWork) return 0;
  let chargeHtml;
  try {
    chargeHtml = (await hektorFetch(`${XMLRPC_URL}?mode=chargeannonce_Documents&id=${encodeURIComponent(String(dossier.hektor_annonce_id))}&lang=fr`)).text;
  } catch (error) {
    await logJob(job.id, logCat, "running", "Lecture empreintes signature indisponible", {
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      error: error && error.message ? error.message : String(error),
    });
    return 0;
  }
  const sigMap = buildSignatureMapFromHtml(chargeHtml);
  if (!sigMap.size) return 0;
  const byDocId = new Map();
  for (const r of existing.rows) {
    const hid = r.metadata_json && r.metadata_json.signature && r.metadata_json.signature.hektor_doc_id;
    if (hid) byDocId.set(String(hid), r);
  }
  const usedCandidateIds = new Set();
  for (const sig of sigMap.values()) {
    if (!sig.status) continue;
    let target = byDocId.get(String(sig.hektor_doc_id));
    if (target) {
      const cur = (target.metadata_json && target.metadata_json.signature) || {};
      if (cur.status !== sig.status || cur.procedure_id !== sig.procedure_id || cur.signed_at !== sig.signed_at) {
        const md = { ...(target.metadata_json || {}), signature: sig };
        await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(target.id)}`, {
          method: "PATCH",
          prefer: "return=minimal",
          body: JSON.stringify({ metadata_json: md, updated_at: new Date().toISOString() }),
        });
        target = { ...target, metadata_json: md };
      }
    } else if (sig.status === "signed") {
      // Pas de ligne suivie par hektor_doc_id (mandat signe AVANT suivi, p.ex. deja signe a la 1re indexation
      // -> il a perdu son force_transfert). Pour EVITER UN DOUBLON, on rattache une ligne "candidate"
      // (meme nom, jamais finalisee, sans signed_document, non deja utilisee) ; sinon ligne synthetique.
      const candidates = existing.rows.filter((r) => {
        if (usedCandidateIds.has(r.id)) return false;
        if (r.metadata_json && r.metadata_json.signed_document) return false;
        const s = r.metadata_json && r.metadata_json.signature;
        const untracked = !s || !s.hektor_doc_id;
        return untracked && String(r.document_name || "") === String(sig.document_name || "");
      });
      if (candidates.length === 1) {
        target = candidates[0];
        usedCandidateIds.add(target.id);
        const md = { ...(target.metadata_json || {}), signature: sig };
        await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(target.id)}`, {
          method: "PATCH",
          prefer: "return=minimal",
          body: JSON.stringify({ metadata_json: md, updated_at: new Date().toISOString() }),
        });
        target = { ...target, metadata_json: md };
      } else if (dossier.app_dossier_id) {
        target = await upsertSyntheticSignedRow(dossier, sig);
      } else {
        continue;
      }
    } else {
      continue; // pending/to_send sans ligne suivie : sera créé par la prochaine sync documents complète
    }
    if (sig.status === "signed" && sig.procedure_id && target && !(target.metadata_json && target.metadata_json.signed_document)) {
      try {
        await downloadSignedProcedureDocument(dossier, target);
        signedFetched += 1;
      } catch (error) {
        await logJob(job.id, logCat, "running", "Recup doc signe echouee", {
          hektor_annonce_id: String(dossier.hektor_annonce_id),
          procedure_id: sig.procedure_id,
          error: error && error.message ? error.message : String(error),
        });
      }
    }
  }
  return signedFetched;
}

// Purge des documents SUPPRIMES dans Hektor (le run quotidien etant additif, ils resteraient fantomes).
// GARDE-FOUS stricts : ne purge QUE des docs indexes Hektor, absents A LA FOIS des entrees (force_transfert)
// ET des empreintes (chargeannonce). Ne touche JAMAIS : lignes synthetiques signees, archives signees
// (signed_document). Ne purge rien si la lecture est vide (anti-suppression massive sur erreur Hektor).
async function pruneDeletedDocuments(job, dossier, entries) {
  if (!Array.isArray(entries) || entries.length === 0) return 0;
  let chargeHtml;
  try {
    chargeHtml = (await hektorFetch(`${XMLRPC_URL}?mode=chargeannonce_Documents&id=${encodeURIComponent(String(dossier.hektor_annonce_id))}&lang=fr`)).text;
  } catch (_e) {
    return 0; // lecture empreintes KO -> on ne purge pas (securite)
  }
  const empreinteIds = new Set([...buildSignatureMapFromHtml(chargeHtml).keys()].map(String));
  const presentHashes = new Set(entries.map((e) => e.hektor_document_id));
  const existing = await loadExistingDocuments(String(dossier.hektor_annonce_id));
  const toDelete = [];
  for (const r of existing.rows) {
    const src = String(r.source || "");
    if (src === "hektor_immosign_signed") continue;                 // ligne synthetique signee
    if (r.metadata_json && r.metadata_json.signed_document) continue; // archive signee conservee
    if (!/^hektor_console/.test(src)) continue;                      // ne purge que les docs indexes Hektor
    if (presentHashes.has(r.hektor_document_id)) continue;           // doc encore present (force_transfert)
    const hid = r.metadata_json && r.metadata_json.signature && r.metadata_json.signature.hektor_doc_id;
    if (hid && empreinteIds.has(String(hid))) continue;             // encore une empreinte (signe/en attente/annule)
    toDelete.push(r.id);
  }
  if (!toDelete.length) return 0;
  const ids = toDelete.map((id) => encodeURIComponent(id)).join(",");
  await supabaseRequest(`app_console_document?id=in.(${ids})`, { method: "DELETE", prefer: "return=minimal" });
  await logJob(job.id, "hektor", "running", "Docs supprimes dans Hektor retires de l'app", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    removed: toDelete.length,
  });
  return toDelete.length;
}

// Relance de signature ImmoSign : POST xmlrpc ImmoSign-remindProcedureSignatories (envoie les mails de rappel).
async function handleRelanceSignature(job) {
  const payload = safeJsonParse(job.payload_json) || {};
  const dossier = await loadDossier(job);
  const procId = payload.procedure_id || payload.procedureId;
  if (!procId) throw new Error("payload_json.procedure_id requis");
  await logJob(job.id, "immosign", "running", "Relance signature", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    procedure_id: procId,
  });
  const doRemind = async () => {
    const res = await hektorFetch(XMLRPC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", Accept: "application/json, text/plain, */*" },
      body: new URLSearchParams({ mode: "ImmoSign-remindProcedureSignatories", procedureId: String(procId) }).toString(),
    });
    return res;
  };
  let res;
  try {
    res = await doRemind();
  } catch (error) {
    if (!isHektorForbiddenError(error)) throw error;
    await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true, forceRemoteSwitch: true });
    res = await doRemind();
  }
  const okText = String(res.text || "");
  await logJob(job.id, "immosign", "done", "Rappel signature envoye", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    procedure_id: procId,
    response: okText.slice(0, 160),
  });
  return { status: "reminded", hektor_annonce_id: String(dossier.hektor_annonce_id), procedure_id: procId };
}

// Annulation de signature ImmoSign par le commercial : POST xmlrpc ImmoSign-deleteProcedure.
// Le doc redevient envoyable (editProcedure) et porte "Annule le ...". Ne supprime PAS le document.
async function handleCancelSignatureProcedure(job) {
  const payload = safeJsonParse(job.payload_json) || {};
  const dossier = await loadDossier(job);
  const procId = payload.procedure_id || payload.procedureId;
  if (!procId) throw new Error("payload_json.procedure_id requis");
  await logJob(job.id, "immosign", "running", "Annulation signature", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    procedure_id: procId,
  });
  const doCancel = async () => hektorFetch(XMLRPC_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", Accept: "application/json, text/plain, */*" },
    body: new URLSearchParams({ mode: "ImmoSign-deleteProcedure", procedureId: String(procId) }).toString(),
  });
  let res;
  try {
    res = await doCancel();
  } catch (error) {
    if (!isHektorForbiddenError(error)) throw error;
    await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true, forceRemoteSwitch: true });
    res = await doCancel();
  }
  // Met a jour la ligne suivie (par hektor_doc_id) en "cancelled" pour un affichage immediat (best-effort).
  try {
    const hid = payload.hektor_doc_id || payload.hektorDocId;
    if (hid) {
      const existing = await loadExistingDocuments(String(dossier.hektor_annonce_id));
      const target = existing.rows.find((r) => r.metadata_json && r.metadata_json.signature && String(r.metadata_json.signature.hektor_doc_id) === String(hid));
      if (target) {
        const md = { ...(target.metadata_json || {}), signature: { ...(target.metadata_json.signature || {}), status: "cancelled", procedure_id: null } };
        await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(target.id)}`, { method: "PATCH", prefer: "return=minimal", body: JSON.stringify({ metadata_json: md, updated_at: new Date().toISOString() }) });
      }
    }
  } catch (_e) { /* affichage best-effort, la prochaine sync corrige */ }
  await logJob(job.id, "immosign", "done", "Signature annulee", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    procedure_id: procId,
    response: String(res.text || "").slice(0, 160),
  });
  return { status: "cancelled", hektor_annonce_id: String(dossier.hektor_annonce_id), procedure_id: procId };
}

async function handleSyncConsoleDocuments(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await logJob(job.id, "hektor", "running", "Lecture documents Console", { hektor_annonce_id: dossier.hektor_annonce_id });
  let entries;
  try {
    entries = await fetchConsoleDocumentEntries(dossier.hektor_annonce_id);
  } catch (error) {
    if (!isHektorForbiddenError(error)) throw error;
    // 403 = bien dans un contexte negociateur que la session de base ne voit pas
    // (ex. compte separe). On bascule dans le contexte du proprietaire puis on reessaie.
    // Les biens de l'agence ne declenchent pas le 403 -> aucun impact sur le run quotidien.
    await logJob(job.id, "hektor", "running", "Lecture documents refusee (403), bascule contexte negociateur puis retry", {
      hektor_annonce_id: dossier.hektor_annonce_id,
      error: error.message || String(error),
    });
    await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true, forceRemoteSwitch: true });
    entries = await fetchConsoleDocumentEntries(dossier.hektor_annonce_id);
  }
  const rows = await upsertConsoleDocuments(dossier, entries);
  const cloud = shouldKeepCloud(dossier);
  let localStored = 0;
  let cloudStored = 0;
  for (const row of rows) {
    const result = await persistConsoleDocumentFile(dossier, row, { cloud });
    localStored += result.local_path ? 1 : 0;
    cloudStored += result.cloud_available && cloud ? 1 : 0;
  }
  // Réconcilie l'état signature (incl. signés qui perdent leur force_transfert) + récupère le PDF signé.
  // BEST-EFFORT : ne doit JAMAIS faire échouer la sync documents (donc le run quotidien). Try/catch.
  let signedFetched = 0;
  try {
    signedFetched = await reconcileSignatureStates(job, dossier);
  } catch (error) {
    await logJob(job.id, "hektor", "running", "Reconciliation signature ignoree (best-effort)", {
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      error: error && error.message ? error.message : String(error),
    });
  }
  // Purge des docs supprimes dans Hektor (best-effort, garde-fous stricts -> ne casse jamais la sync).
  let pruned = 0;
  try {
    pruned = await pruneDeletedDocuments(job, dossier, entries);
  } catch (error) {
    await logJob(job.id, "hektor", "running", "Purge docs supprimes ignoree (best-effort)", {
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      error: error && error.message ? error.message : String(error),
    });
  }
  return {
    indexed: rows.length,
    local_stored: localStored,
    cloud_stored: cloudStored,
    signed_fetched: signedFetched,
    pruned,
    cloud_policy: cloud ? "daily_cloud_scope" : "local_archive_only",
    hektor_annonce_id: String(dossier.hektor_annonce_id),
  };
}

async function handleSyncHektorPhotos(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  const photoContextOptions = { preferRequester: true, preferDossierOwner: true, required: true, forceRemoteSwitch: true };
  await ensureHektorExecutionContext(job, dossier, payload, photoContextOptions);
  await logJob(job.id, "hektor_photos", "running", "Lecture photos Console", {
    hektor_annonce_id: dossier.hektor_annonce_id,
  });
  let entries;
  try {
    entries = await fetchConsolePhotoEntries(dossier.hektor_annonce_id);
  } catch (error) {
    if (!isHektorForbiddenError(error)) throw error;
    await logJob(job.id, "hektor_photos", "running", "Lecture photos refusee par Hektor, relance session puis retry", {
      hektor_annonce_id: dossier.hektor_annonce_id,
      error: error.message || String(error),
    });
    await refreshHektorSession("photo_403_retry");
    await ensureHektorExecutionContext(job, dossier, payload, photoContextOptions);
    entries = await fetchConsolePhotoEntries(dossier.hektor_annonce_id);
  }
  const rows = await upsertConsolePhotos(dossier, entries);
  const visibleCount = rows.filter((row) => row.visible).length;
  const hiddenCount = rows.length - visibleCount;
  await logJob(job.id, "hektor_photos", "done", "Photos Console indexees", {
    hektor_annonce_id: dossier.hektor_annonce_id,
    total: rows.length,
    visible: visibleCount,
    hidden: hiddenCount,
  });
  return {
    status: "photos_synced",
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    total: rows.length,
    visible: visibleCount,
    hidden: hiddenCount,
  };
}

async function loadConsoleDocumentById(documentId) {
  const params = new URLSearchParams({ select: "*", id: `eq.${documentId}`, limit: "1" });
  const rows = await supabaseRequest(`app_console_document?${params.toString()}`, { method: "GET" });
  if (!Array.isArray(rows) || !rows.length) throw new Error(`Document introuvable: ${documentId}`);
  return rows[0];
}

async function handlePrepareDocumentCloud(job) {
  const payload = safeJsonParse(job.payload_json);
  const documentId = payload.document_id;
  if (!documentId) throw new Error("payload_json.document_id required");
  const document = await loadConsoleDocumentById(documentId);

  await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(documentId)}`, {
    method: "PATCH",
    prefer: "return=minimal",
    body: JSON.stringify({ storage_status: "uploading", updated_at: new Date().toISOString() }),
  });

  const result = await persistConsoleDocumentFile(null, { ...document, storage_status: "uploading" }, { cloud: true });
  return {
    document_id: documentId,
    storage_path: result.storage_path,
    local_path: result.local_path,
    bytes: result.bytes,
    sha256: result.sha256,
  };
}

// =========================================================================
// Avis de valeur (estimation) : génère un PDF pro à partir des données du
// payload, l'upload en temp storage, puis réutilise le flux éprouvé
// upload_document_to_hektor (push Hektor + archive locale + Supabase).
// Rendu PDF via Playwright (déjà présent pour le login/upload Hektor).
// =========================================================================
const ESTIM_MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];

function estimEscapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function estimText(value, fallback) {
  const v = String(value == null ? "" : value).trim();
  return estimEscapeHtml(v || fallback || "");
}

function estimEuro(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " €";
}

// Charge le détail annonce et en extrait les champs riches pour l'avis de valeur premium.
// --- Extraction enrichie du détail (detail_raw_json) pour l'avis de valeur -----
// Source = detail_raw_json : groupes (ag_interieur/ag_exterieur/equipements/secteur/
// diagnostiques/copropriete/mandat_infofi…) avec props[KEY].value. Réplique la
// logique du front (rawWizardDetailField) : on cherche une clé à travers les groupes.
const ESTIM_RAW_GROUPS = ["mandat_infofi", "mandat_mandatdispo", "secteur", "ag_interieur",
  "ag_exterieur", "terrain", "equipements", "diagnostiques", "copropriete", "organiser_visite"];
function estimParseRaw(j) {
  try { let r = j.detail_raw_json; if (typeof r === "string") r = JSON.parse(r); return r && typeof r === "object" ? r : {}; }
  catch (_) { return {}; }
}
function estimRawAny(raw, key) {
  const cands = key.endsWith("-") ? [key, key.slice(0, -1)] : [key, key + "-"];
  for (const g of ESTIM_RAW_GROUPS) {
    const gp = raw[g] && raw[g].props;
    if (!gp) continue;
    for (const c of cands) { const p = gp[c]; if (p && p.value != null) { const v = String(p.value).trim(); if (v !== "") return v; } }
  }
  return null;
}
const estimNum = (v) => { const n = Number(v); return Number.isFinite(n) && n > 0 ? n : null; };
const estimYear = (v) => { const n = parseInt(String(v || ""), 10); return n >= 1700 && n <= 2100 ? String(n) : null; };
const estimOui = (v) => String(v || "").trim().toUpperCase() === "OUI";
// Libellés Hektor courants (codes sans accents -> affichage propre).
const ESTIM_LABELS = {
  "AMERICAINE": "Américaine", "EQUIPEE": "Équipée", "AMENAGEE": "Aménagée", "SEMI EQUIPEE": "Semi-équipée",
  "INDEPENDANT": "Indépendant", "INDEPENDANTE": "Indépendante", "MITOYEN": "Mitoyen", "MITOYENNE": "Mitoyenne",
  "TOUT A L EGOUT": "Tout à l'égout", "FOSSE SEPTIQUE": "Fosse septique", "ASSAINISSEMENT INDIVIDUEL": "Assainissement individuel",
  "ELECTRIQUE": "Électrique", "GAZ": "Gaz", "FIOUL": "Fioul", "BOIS": "Bois", "POMPE A CHALEUR": "Pompe à chaleur",
  "INDIVIDUEL": "Individuel", "COLLECTIF": "Collectif", "CENTRAL": "Central", "RADIATEUR": "Radiateur",
};
function estimHuman(v) {
  if (v == null) return null;
  const s = String(v).trim(); if (!s) return null;
  const up = s.toUpperCase();
  if (up === "OUI") return "Oui";
  if (up === "NON") return "Non";
  if (up === "NON PRÉCISÉ" || up === "NON PRECISE" || up === "-" || up === "0") return null;
  const key = up.replace(/[\s'_-]+/g, " ").trim();
  if (ESTIM_LABELS[key]) return ESTIM_LABELS[key];
  return s.toLowerCase().replace(/(^|[\s\-'])([a-zàâäéèêëîïôöùûüç])/g, (m, p, c) => p + c.toUpperCase());
}
const estimDiagDone = (v) => { const s = String(v || "").trim(); if (!s || s === "0000-00-00") return false; const y = parseInt(s.slice(0, 4), 10); return y >= 2000 && y <= 2100; };
function estimEnrichDetail(j) {
  const raw = estimParseRaw(j);
  const diagKeys = { DPE: "dpe_date", Amiante: "diag_amiante_date", Plomb: "diag_plomb_date",
    Gaz: "diag_gaz_date", "Électricité": "diag_electrique_date", Termites: "diag_termites_date",
    "Loi Carrez": "diag_loi_carrez_date", Assainissement: "diag_assainissement_date",
    "Risques nat. & tech.": "diag_risques_nat_tech_date" };
  const diagnostics = {};
  for (const [label, key] of Object.entries(diagKeys)) {
    const d = estimRawAny(raw, key);
    diagnostics[label] = { done: estimDiagDone(d), date: estimDiagDone(d) ? d : null };
  }
  return {
    exposition: estimHuman(estimRawAny(raw, "EXPOSITION")), vue: estimHuman(estimRawAny(raw, "vuee")),
    niveaux: estimNum(estimRawAny(raw, "NB_NIVEAUX")), etages: estimNum(estimRawAny(raw, "NB_ETAGES")),
    anneeConstruction: estimYear(estimRawAny(raw, "ANNEE_CONS")), anneeRef: estimYear(estimRawAny(raw, "dpe_annee_reference")),
    copropriete: estimHuman(estimRawAny(raw, "copropriete")), coproprieteNbLots: estimNum(estimRawAny(raw, "copropriete_nb_lot")),
    mursMitoyens: estimHuman(estimRawAny(raw, "MURS_MITOYENS")), particularites: estimRawAny(raw, "Particularites"),
    sdb: estimNum(estimRawAny(raw, "NB_SDB")), se: estimNum(estimRawAny(raw, "NB_SE")), wc: estimNum(estimRawAny(raw, "NB_WC")),
    surfCarrez: estimNum(estimRawAny(raw, "SURF_CARREZ")), surfSejour: estimNum(estimRawAny(raw, "SURF_SEJOUR")),
    cuisine: estimHuman(estimRawAny(raw, "CUISINE")), cuisineEquip: estimHuman(estimRawAny(raw, "CUISINE_EQUIPEMENT")),
    jardin: estimHuman(estimRawAny(raw, "JARDIN")), surfJardin: estimNum(estimRawAny(raw, "SURFACE_JARDIN")),
    piscine: estimHuman(estimRawAny(raw, "PISCINE")),
    terrasse: estimHuman(estimRawAny(raw, "TERRASSE")), nbTerrasses: estimNum(estimRawAny(raw, "NB_TERRASSE")), surfTerrasse: estimNum(estimRawAny(raw, "SURFACE_TERRASSE")),
    cave: estimHuman(estimRawAny(raw, "CAVE")), surfCave: estimNum(estimRawAny(raw, "SURFACE_CAVE")),
    balcon: estimNum(estimRawAny(raw, "NB_BALCON")), surfBalcon: estimNum(estimRawAny(raw, "SURFACE_BALCON")),
    surfGarage: estimNum(estimRawAny(raw, "SURFACE_GARAGE")), parkInt: estimNum(estimRawAny(raw, "NB_PARK_INT")), parkExt: estimNum(estimRawAny(raw, "NB_PARK_EXT")),
    chauffageType: estimHuman(estimRawAny(raw, "typeChauff")), chauffageEnergie: estimHuman(estimRawAny(raw, "energieChauff")), chauffageFormat: estimHuman(estimRawAny(raw, "formatChauff")),
    climatisation: estimOui(estimRawAny(raw, "climatisation")),
    eau: estimHuman(estimRawAny(raw, "EAU")), assainissement: estimHuman(estimRawAny(raw, "ASSAINISSEMENT")),
    cheminee: estimOui(estimRawAny(raw, "cheminee")), voletsElec: estimOui(estimRawAny(raw, "volets_elctriques")),
    doubleVitrage: estimOui(estimRawAny(raw, "double_vitrage")), tripleVitrage: estimOui(estimRawAny(raw, "triple_vitrage")),
    porteBlindee: estimOui(estimRawAny(raw, "porte_blindee")), interphone: estimOui(estimRawAny(raw, "interphone")),
    visiophone: estimOui(estimRawAny(raw, "visiophone")), alarme: estimOui(estimRawAny(raw, "alarme")),
    digicode: estimOui(estimRawAny(raw, "digicode")), detecteurFumee: estimOui(estimRawAny(raw, "detecteur_fumee")),
    accesHandi: estimOui(estimRawAny(raw, "ACCES_HANDI")),
    transport: estimRawAny(raw, "TRANSPORT"), proximite: estimRawAny(raw, "PROXIMITE"),
    environnement: estimRawAny(raw, "ENVIRONNEMENT"), adresseCompl: estimRawAny(raw, "ADRESSE_COMPL"),
    conso: estimNum(estimRawAny(raw, "dpe_cons")), gesVal: estimNum(estimRawAny(raw, "dpe_ges")),
    coutMin: estimNum(estimRawAny(raw, "dpe_couts_min")), coutMax: estimNum(estimRawAny(raw, "dpe_couts_max")), diagnostics,
    taxeFonciere: estimNum(estimRawAny(raw, "TAXE_FONCIERE")), taxeHabitation: estimNum(estimRawAny(raw, "TAXE_HABITATION")), charges: estimNum(estimRawAny(raw, "CHARGES")),
  };
}

// Commodités OSM via Overpass — appelé depuis le worker (IP fiable, contrairement
// au navigateur (CORS) et à Render (souvent bloqué)). Renvoie counts + gare proche.
function estimHaversineKm(lat1, lon1, lat2, lon2) {
  const r = 6371, d = Math.PI / 180;
  const a = Math.sin((lat2 - lat1) * d / 2) ** 2 + Math.cos(lat1 * d) * Math.cos(lat2 * d) * Math.sin((lon2 - lon1) * d / 2) ** 2;
  return r * 2 * Math.asin(Math.sqrt(a));
}
async function fetchCommodites(lat, lon) {
  const q = `[out:json][timeout:25];(nwr[amenity=school](around:1500,${lat},${lon});nwr[shop](around:1000,${lat},${lon});nwr[amenity~"pharmacy|doctors|hospital|clinic"](around:1500,${lat},${lon});nwr[railway=station](around:8000,${lat},${lon}););out center tags 250;`;
  const hosts = ["https://overpass-api.de/api/interpreter", "https://lz4.overpass-api.de/api/interpreter"];
  for (const host of hosts) {
    try {
      const r = await fetch(host, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "GTI-Immobilier-Estimation/1.0 (contact@gti-immobilier.fr)" }, body: "data=" + encodeURIComponent(q) });
      if (!r.ok) continue;
      const j = await r.json();
      let ecoles = 0, commerces = 0, sante = 0, gareNom = null, gareKm = null;
      const pois = [];  // coords des POI pour les pins sur la carte (visuel commodités)
      for (const el of (j.elements || [])) {
        const t = el.tags || {};
        const elat = el.lat || (el.center && el.center.lat), elon = el.lon || (el.center && el.center.lon);
        let type = null;
        if (t.amenity === "school") { ecoles++; type = "ecole"; }
        else if (t.shop) { commerces++; type = "commerce"; }
        else if (["pharmacy", "doctors", "hospital", "clinic"].includes(t.amenity)) { sante++; type = "sante"; }
        else if (t.railway === "station") {
          if (elat && elon) { const km = Math.round(estimHaversineKm(lat, lon, elat, elon) * 10) / 10; if (gareKm == null || km < gareKm) { gareKm = km; gareNom = t.name || "Gare"; } }
        }
        if (type && elat && elon) pois.push({ lat: elat, lon: elon, type, km: estimHaversineKm(lat, lon, elat, elon) });
      }
      // Les plus proches d'abord, plafonnés (anti-saturation de la carte).
      pois.sort((a, b) => a.km - b.km);
      const cap = { ecole: 0, commerce: 0, sante: 0 };
      const poisMap = pois.filter((p) => (cap[p.type] = (cap[p.type] || 0) + 1) <= 8)
        .map((p) => ({ lat: p.lat, lon: p.lon, type: p.type }));
      return { ecoles, commerces, sante, gareNom, gareKm, pois: poisMap };
    } catch (_) { /* miroir suivant */ }
  }
  return null;
}

// Éléments cadastraux (IGN apicarto) : parcelle(s) sous le point + zonage PLU (module GPU).
// Données publiques gratuites, sans clé. Côté serveur (Node) : pas de souci CORS.
// Pas de donnée nominative (propriétaire indisponible publiquement).
async function fetchCadastre(lat, lon) {
  if (!Number.isFinite(+lat) || !Number.isFinite(+lon)) return null;
  const UA = { "User-Agent": "GTI-Immobilier-Estimation/1.0 (contact@gti-immobilier.fr)" };
  const geom = encodeURIComponent(JSON.stringify({ type: "Point", coordinates: [+lon, +lat] }));
  const getFeatures = async (path) => {
    try {
      const r = await fetch(`https://apicarto.ign.fr/api${path}?geom=${geom}`, { headers: UA });
      if (!r.ok) return [];
      const j = await r.json();
      return (j && j.features) || [];
    } catch (_) { return []; }
  };
  const parcelles = [];
  let contenanceTotale = 0;
  for (const f of await getFeatures("/cadastre/parcelle")) {
    const p = f.properties || {};
    let c = p.contenance != null ? parseInt(p.contenance, 10) : null;
    if (!Number.isFinite(c)) c = null;
    if (c) contenanceTotale += c;
    parcelles.push({
      reference: [p.section, p.numero].filter(Boolean).join(" ") || null,
      section: p.section || null, numero: p.numero || null, contenance: c,
      commune: p.nom_com || null, code_insee: p.code_insee || null, idu: p.idu || null,
    });
  }
  let plu = null;
  const zf = await getFeatures("/gpu/zone-urba");
  if (zf.length) { const p = zf[0].properties || {}; plu = { zone: p.libelle || null, libelle: p.libelong || null, type: p.typezone || null }; }
  return { ok: parcelles.length > 0, lat: +lat, lon: +lon, parcelles, contenance_totale: contenanceTotale || null, plu };
}

// Profil commune INSEE (pré-chargé) : population + série + revenu médian, avec repères
// département (médiane) et France. Lu à la génération, comme DVF/risques.
const FRANCE_REVENU_MEDIAN = 22040; // niveau de vie médian France (INSEE FiLoSoFi, €/an)
async function loadCommuneInsee(insee, dept) {
  if (!insee) return null;
  try {
    const rows = await supabaseRequest(
      `app_commune_insee?code_insee=eq.${encodeURIComponent(String(insee).trim())}&select=commune,population,population_annee,pop_evolution,pop_tendance,revenu_median,pop_series&limit=1`,
      { method: "GET" }
    ).catch(() => null);
    const r = Array.isArray(rows) && rows[0] ? rows[0] : null;
    if (!r) return null;
    let deptRevenu = null;
    if (dept) {
      const dr = await supabaseRequest(
        `app_commune_insee?dept=eq.${encodeURIComponent(String(dept).trim())}&revenu_median=not.is.null&select=revenu_median`,
        { method: "GET" }
      ).catch(() => null);
      if (Array.isArray(dr) && dr.length) {
        const vals = dr.map((x) => Number(x.revenu_median)).filter((n) => Number.isFinite(n)).sort((a, b) => a - b);
        if (vals.length) deptRevenu = vals[Math.floor(vals.length / 2)];
      }
    }
    let series = null;
    try { series = typeof r.pop_series === "string" ? JSON.parse(r.pop_series) : r.pop_series; } catch (_) { /* tolérant */ }
    return {
      commune: r.commune || null,
      population: r.population != null ? Number(r.population) : null,
      population_annee: r.population_annee != null ? Number(r.population_annee) : null,
      pop_evolution: r.pop_evolution != null ? Number(r.pop_evolution) : null,
      pop_tendance: r.pop_tendance || null,
      revenu_median: r.revenu_median != null ? Number(r.revenu_median) : null,
      pop_series: series && typeof series === "object" ? series : null,
      dept_revenu_median: deptRevenu,
      france_revenu_median: FRANCE_REVENU_MEDIAN,
    };
  } catch (_) { return null; }
}

async function loadEstimationDetail(appDossierId) {
  try {
    if (!appDossierId) return {};
    const rows = await supabaseRequest(
      `app_dossier_detail_current?app_dossier_id=eq.${encodeURIComponent(appDossierId)}&select=detail_payload_json&limit=1`,
      { method: "GET" },
    );
    const raw = Array.isArray(rows) && rows[0] ? rows[0].detail_payload_json : null;
    if (!raw) return {};
    let j = typeof raw === "string" ? JSON.parse(raw) : raw;
    if (typeof j === "string") j = JSON.parse(j);
    const num = (v) => { const n = Number(v); return Number.isFinite(n) && n > 0 ? n : null; };
    let photos = [];
    try {
      const imgs = j.images_preview_json ? JSON.parse(j.images_preview_json) : (j.images_json ? JSON.parse(j.images_json) : []);
      if (Array.isArray(imgs)) photos = imgs.map((x) => (typeof x === "string" ? x : (x && (x.url || x.full)))).filter(Boolean);
    } catch (_) { /* photos best-effort */ }
    if (photos.length === 0 && j.photo_url_listing) photos = [j.photo_url_listing];
    const descriptif = String(j.corps_listing_html || j.texte_principal_html || "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim();
    return {
      surface: num(j.surface_habitable_detail) || num(j.surface),
      terrain: num(j.surface_terrain_detail),
      pieces: num(j.nb_pieces),
      chambres: num(j.nb_chambres),
      garage: num(j.garage_box_detail) ? "Oui" : null,
      etage: j.etage_detail || null,
      descriptif: descriptif || null,
      photos: photos.slice(0, 6),
      dpe_img: j.dpe_image_url || null,
      ges_img: j.ges_image_url || null,
      ...estimEnrichDetail(j),  // Lot A : caractéristiques étendues, intérieur/extérieur, équipements, diagnostics, charges
    };
  } catch (_) {
    return {};
  }
}

const ESTIM_PREMIUM_CSS = `
*{box-sizing:border-box;margin:0;padding:0}
:root{--brand:#c5005f;--brand-d:#8c0044;--brand-50:#fbeaf2;--ink:#1d1e1f;--body:#42474a;--mute:#8b8f92;--faint:#b4b7b9;--cream:#f7f2ec;--line:#e4ddd2;--line2:#efe9df;--green:#1f8a5b;--mx:16mm}
html,body{background:#fff;-webkit-font-smoothing:antialiased}
body{font-family:'Inter',system-ui,sans-serif;color:var(--ink);line-height:1.5}
svg{display:block}.serif{font-family:'Spectral',Georgia,serif}.tnum{font-variant-numeric:tabular-nums}
.page{position:relative;width:210mm;height:297mm;background:#fff;margin:0 auto;padding:var(--mx);display:flex;flex-direction:column;overflow:hidden;page-break-after:always}
.page:last-child{page-break-after:auto}
.rh{display:flex;align-items:center;justify-content:space-between;padding-bottom:9px;border-bottom:1.5px solid var(--line);flex:none}
.rh img{height:68px;width:auto}
.rh .meta{text-align:right}.rh .meta .t{font-family:'Spectral',serif;font-size:13px;font-weight:700;line-height:1}.rh .meta .d{font-size:8.5px;color:var(--mute);margin-top:3px;letter-spacing:.04em}
.rf{display:flex;align-items:center;justify-content:space-between;padding-top:9px;border-top:1px solid var(--line);flex:none;font-size:8px;color:var(--faint);letter-spacing:.03em}
.rf .pg{font-weight:700;color:var(--mute)}
.content{flex:1;padding:11px 0;min-height:0}
.h{font-size:9px;font-weight:800;color:var(--ink);letter-spacing:2.5px;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:11px;padding-bottom:5px;border-bottom:1.5px solid var(--ink)}
.h::before{content:"";width:9px;height:9px;background:var(--brand);flex:none}.h.mt{margin-top:13px}
.todo{color:var(--faint);font-style:italic;font-weight:500}
.cover{padding:0;display:flex;flex-direction:column;color:#1a1614;overflow:hidden}
.cover .c-head{display:flex;align-items:center;justify-content:space-between;padding:6mm var(--mx);background:linear-gradient(115deg,#160a10,#241019 45%,#3a1224)}
.cover .c-head img{height:128px;width:auto}
.cover .c-head .ref{font-size:8px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.55);text-align:right;line-height:1.8}
.cover .c-head .ref b{display:block;color:#fff;font-size:9.5px;letter-spacing:2.4px}
.cover .c-hero{position:relative;flex:none;height:112mm;overflow:hidden;background:linear-gradient(135deg,#2a2230,#3a1224)}
.cover .c-hero>img{width:100%;height:100%;object-fit:cover}
.cover .c-hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 55%,rgba(15,13,12,.45))}
.cover .c-photo-tag{position:absolute;left:var(--mx);bottom:6mm;z-index:4;display:inline-flex;align-items:center;gap:7px;font-size:9px;font-weight:700;color:#fff;background:rgba(15,13,12,.5);border:1px solid rgba(255,255,255,.22);padding:7px 13px;border-radius:2px}
.cover .c-photo-tag svg{width:12px;height:12px;color:#ff9ec8}
.cover .c-hero-foot{flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 var(--mx)}
.cover .c-kicker{display:flex;align-items:center;gap:11px;font-size:9px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:var(--brand)}
.cover .c-kicker svg{width:13px;height:13px}.cover .c-kicker::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(26,22,20,.18),transparent)}
.cover .c-title{font-family:'Spectral',serif;font-size:48px;font-weight:700;letter-spacing:-.025em;line-height:.96;margin-top:14px;color:#1a1614}
.cover .c-bien{font-family:'Spectral',serif;font-size:18px;font-weight:500;font-style:italic;margin-top:11px;color:#4a4038}
.cover .c-loc{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:600;color:#6a5f56;margin-top:7px}.cover .c-loc svg{width:13px;height:13px;color:var(--brand)}
.cover .c-tags{display:flex;gap:7px;margin-top:16px}.cover .c-tags span{font-size:9.5px;font-weight:700;border:1px solid rgba(26,22,20,.2);background:rgba(26,22,20,.03);padding:7px 13px;color:#3a322c;white-space:nowrap;border-radius:2px}
.cover .c-info{flex:none;margin:9mm var(--mx) var(--mx)}.cover .c-info-row{display:flex}
.cover .c-info-cell{flex:1;padding:13px 16px;border:1px solid rgba(26,22,20,.16);border-left:none;min-width:0}.cover .c-info-cell:first-child{border-left:1px solid transparent}
.cover .c-info-cell.accent{background:var(--brand);border-color:var(--brand);flex:0 0 36%;display:flex;flex-direction:column;justify-content:center}
.cover .c-info-cell .l{display:block;font-size:7.5px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:var(--brand)}.cover .c-info-cell.accent .l{color:rgba(255,255,255,.85)}
.cover .c-info-cell .v{display:block;font-size:11.5px;font-weight:600;margin-top:5px;color:#1a1614;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.cover .c-info-cell.accent .v{color:#fff;font-family:'Spectral',serif;font-size:22px;font-weight:700;letter-spacing:-.02em}
.gal{display:grid;grid-template-columns:repeat(4,1fr);grid-auto-rows:29mm;gap:6px}
.gal .g{border-radius:6px;overflow:hidden;background:linear-gradient(135deg,#efe9df,#e4ddd2);position:relative}
.gal .g img{width:100%;height:100%;object-fit:cover}.gal .g.big{grid-column:span 2;grid-row:span 2}
.specs{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.spec{background:#fff;padding:11px 14px}.spec .k{font-size:8.5px;color:var(--mute);font-weight:700;letter-spacing:.04em;text-transform:uppercase}
.spec .v{font-family:'Spectral',serif;font-size:18px;font-weight:600;margin-top:6px}.spec .v small{font-size:11px;color:var(--mute);font-weight:400}
.energy{display:flex;gap:10px;margin-top:12px}.epill{display:flex;align-items:stretch;border:1px solid var(--line);border-radius:9px;overflow:hidden}
.epill .g{width:40px;display:grid;place-items:center;font-family:'Spectral',serif;font-size:18px;font-weight:700;color:#1a1c1d}.epill .i{padding:8px 12px}
.epill .i .l{font-size:8.5px;letter-spacing:1.3px;text-transform:uppercase;color:var(--mute);font-weight:700}.epill .i .d{font-size:11px;margin-top:2px}
.val{background:linear-gradient(160deg,#1d1e1f,#2c2228 72%,#3a1226);color:#fff;border-radius:12px;padding:26px 28px;position:relative;overflow:hidden}
.val .grid{position:relative;display:grid;grid-template-columns:1.1fr 1fr;gap:30px;align-items:center}
.val .lbl{font-size:9px;font-weight:800;color:#ff9ec8;letter-spacing:2.5px;text-transform:uppercase}
.val .main{font-family:'Spectral',serif;font-size:44px;font-weight:700;letter-spacing:-.03em;line-height:1;margin-top:10px}
.val .sub{font-size:11.5px;color:rgba(255,255,255,.62);margin-top:9px}
.gauge-h{font-size:9px;font-weight:700;color:rgba(255,255,255,.5);letter-spacing:1.4px;text-transform:uppercase;margin-bottom:15px}
.gbar{height:7px;border-radius:99px;background:linear-gradient(90deg,#5a82b0,#7fd1a8 45%,#e8c34a 72%,#d7674a);position:relative}
.gpin{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:17px;height:17px;border-radius:50%;background:#fff;border:4px solid var(--brand)}
.gends{display:flex;justify-content:space-between;margin-top:18px;position:relative}.gend .v{font-family:'Spectral',serif;font-size:15px;font-weight:600}
.gend .k{font-size:8px;letter-spacing:1.2px;text-transform:uppercase;color:rgba(255,255,255,.5);font-weight:700;margin-top:3px}
.gend.mid{position:absolute;left:50%;transform:translateX(-50%);text-align:center}.gend.mid .v{color:#ff9ec8}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}.scard{border:1px solid var(--line);border-radius:11px;padding:15px 16px}
.acq{display:flex;align-items:center;gap:11px;margin-top:8px;padding:9px 13px;background:var(--brand-50);border:1px solid #f3c9dd;border-radius:11px;font-size:11px;color:var(--body);line-height:1.4}
.acq b{color:var(--brand-d)}.acq-ic{flex:none;width:30px;height:30px;display:flex;align-items:center;justify-content:center;background:var(--brand);border-radius:50%;color:#fff}.acq-ic svg{width:15px;height:15px}
.cdv-map{position:relative;width:100%;height:76mm;border-radius:11px;overflow:hidden;border:1px solid var(--line);background:var(--cream)}
.cdv-map img{width:100%;height:100%;object-fit:cover;display:block}
.cdv-pin{position:absolute;left:50%;top:50%;transform:translate(-50%,-100%);color:var(--brand)}.cdv-pin svg{width:30px;height:30px}
.cdv-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-top:13px}
.cdv-card{border:1px solid var(--line);border-radius:11px;overflow:hidden}
.cdv-card .ch{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);padding:10px 14px;border-bottom:1px solid var(--line);background:var(--cream)}
.cdv-row{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:10.5px;color:var(--body);padding:8px 14px;border-bottom:1px solid var(--line2)}
.cdv-row:last-child{border-bottom:none}.cdv-row b{color:var(--ink);font-weight:700}
.cdv-risks{display:flex;flex-wrap:wrap;gap:7px;margin-top:4px}
.cdv-risk{font-size:9.5px;font-weight:600;color:var(--body);background:var(--cream);border:1px solid var(--line);border-radius:20px;padding:5px 11px}
.cdv-lvls{display:flex;gap:22px;margin-top:12px;flex-wrap:wrap}
.cdv-lvl .k{font-size:8.5px;font-weight:700;text-transform:uppercase;color:var(--mute);letter-spacing:.04em}.cdv-lvl .v{font-weight:800;margin-top:2px;font-size:11px}
.scard .ic{width:30px;height:30px;border-radius:8px;background:var(--brand-50);color:var(--brand);display:grid;place-items:center}.scard .ic svg{width:15px;height:15px}
.scard .v{font-family:'Spectral',serif;font-size:22px;font-weight:600;margin-top:11px}.scard .v small{font-size:11px;color:var(--mute)}.scard .l{font-size:10.5px;color:var(--body);margin-top:2px}
.chart{border:1px solid var(--line);border-radius:12px;padding:13px 18px;margin-top:9px}
.chart .ch{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:16px}
.chart .ch .t{font-size:12px;font-weight:700}.chart .ch .s{font-size:10.5px;color:var(--mute)}
.bars{display:flex;align-items:flex-end;gap:12px;height:24mm}
.bcol{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;justify-content:flex-end}
.bcol .bv{font-size:10px;font-weight:700}.bcol .bar{flex:none;width:100%;max-width:42px;border-radius:6px 6px 0 0;background:linear-gradient(180deg,#c9c0b0,#b8ad99);-webkit-print-color-adjust:exact;print-color-adjust:exact}
.bcol .bar.hl{background:linear-gradient(180deg,var(--brand),var(--brand-d))}.bcol .bk{font-size:9.5px;color:var(--mute);font-weight:600}
.comps{display:flex;flex-direction:column;gap:8px}
.comp{display:flex;align-items:center;gap:13px;padding:10px 13px;border:1px solid var(--line);border-left:3px solid var(--brand);border-radius:2px}
.comp .info{flex:1;min-width:0}.comp .info .t{font-size:12.5px;font-weight:700}.comp .info .d{font-size:10px;color:var(--mute);margin-top:2px}
.comp .stat{text-align:right}.comp .stat .p{font-family:'Spectral',serif;font-size:15px;font-weight:600}.comp .stat .pm{font-size:10px;color:var(--brand);font-weight:700;margin-top:1px}
.comp .bdg{font-size:9px;font-weight:700;color:var(--green);background:#e9f6ef;border:1px solid #c3e6d4;padding:3px 8px;border-radius:99px}
.dvf-sub{font-size:10.5px;color:var(--body);line-height:1.5;margin:-2px 0 10px}
.dvf-table{border:1px solid var(--line);border-radius:8px;overflow:hidden}
.dvf-head,.dvf-row{display:grid;grid-template-columns:minmax(0,1.8fr) 20mm 18mm 24mm 23mm 14mm;gap:7px;align-items:center}
.dvf-head{background:var(--cream);font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:var(--mute);padding:7px 8px}
.dvf-row{padding:6px 8px;border-top:1px solid var(--line2);font-size:9.2px;color:var(--body)}
.dvf-main{min-width:0}.dvf-main b{display:block;font-size:10px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.dvf-main small{display:block;font-size:8.5px;color:var(--mute);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}
.dvf-num{text-align:right;font-weight:700;color:var(--ink)}.dvf-muted{color:var(--mute)}
.etat-top{display:flex;align-items:center;gap:14px;padding:13px 16px;border:1px solid var(--line);border-radius:3px;background:var(--cream);margin-bottom:12px}
.etat-stars{display:flex;gap:2px}.etat-stars svg{width:15px;height:15px}.etat-stars .on{color:var(--brand)}.etat-stars .off{color:var(--line)}
.etat-rl{font-family:'Spectral',serif;font-size:15px;font-weight:600}.etat-rs{font-size:9.5px;color:var(--mute)}
.etat-sep{width:1px;align-self:stretch;background:var(--line)}.etat-meta{display:flex;gap:18px;flex-wrap:wrap}
.etat-meta .k{font-size:8px;font-weight:700;color:var(--mute);text-transform:uppercase}.etat-meta .v{font-size:11.5px;font-weight:700;margin-top:2px}
.pts-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}.pts{border:1px solid var(--line);border-radius:3px;padding:13px 15px}
.pts .ph{font-size:9px;font-weight:800;text-transform:uppercase;display:flex;align-items:center;gap:7px;margin-bottom:9px}.pts .ph svg{width:13px;height:13px}
.pts.forts .ph{color:var(--green)}.pts.vigi .ph{color:#b8860b}.pts ul{list-style:none;display:flex;flex-direction:column;gap:7px}.pts li{font-size:10.5px;color:var(--body);line-height:1.4;display:flex;align-items:flex-start;gap:7px}.pts li svg{width:13px;height:13px;flex:none;margin-top:1px}.pts.forts li svg{color:var(--green)}.pts.vigi li svg{color:#b8860b}
.method{display:flex;gap:10px;padding:12px 15px;background:var(--brand-50);border:1px solid #f3d4e3;border-radius:3px;margin-top:12px}.method svg{width:16px;height:16px;color:var(--brand);flex:none;margin-top:1px}
.method .t{font-size:11px;font-weight:700}.method .d{font-size:10px;color:var(--body);line-height:1.5;margin-top:2px}
.diag-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}.diag{border:1px solid var(--line);border-radius:3px;overflow:hidden}
.diag-h{font-size:9px;font-weight:800;text-transform:uppercase;color:var(--mute);padding:10px 14px;border-bottom:1px solid var(--line);background:var(--cream)}
.pst-leg{display:flex;flex-wrap:wrap;gap:6px 16px;background:var(--cream);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:8px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:var(--mute);margin:10px 0 12px}
.pst-leg span{display:inline-flex;align-items:center;gap:6px}.pst-leg i{width:9px;height:9px;border-radius:2px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.pst-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px 26px}
.pst-top{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:4px}
.pst-n{font-size:10.5px;font-weight:600;color:var(--ink)}.pst-v{font-size:8.5px;font-weight:800;text-transform:uppercase;letter-spacing:.03em}
.pst-bar{display:block;height:5px;background:var(--line2);border-radius:3px;overflow:hidden}
.pst-fill{display:block;height:100%;border-radius:3px;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.detail-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:11px}
.eqps{display:flex;flex-wrap:wrap;gap:6px;margin-top:2px}
.eqp{display:inline-flex;align-items:center;gap:5px;font-size:9.5px;font-weight:600;color:var(--body);border:1px solid var(--line);border-radius:20px;padding:5px 11px}
.eqp svg{width:11px;height:11px;color:var(--green)}
.diag-row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 14px;border-bottom:1px solid var(--line2);font-size:10.5px}.diag-row:last-child{border-bottom:none}
.diag-row .k{color:var(--body);font-weight:500}.diag-row .v{font-weight:700}.diag-row .v.ok{color:var(--green)}.diag-row .v.na{color:var(--mute);font-weight:600}
.avis .lead{font-family:'Spectral',serif;font-size:15px;font-style:italic;font-weight:500;border-left:3px solid var(--brand);padding-left:15px;line-height:1.5}
.avis p{font-size:11.5px;color:var(--body);line-height:1.7;margin-top:9px}
.contact-fuse{border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-top:4px;background:#fff;display:flex;align-items:stretch}
.cf-body{padding:15px 20px;flex:1;min-width:0}.cf-nego{display:flex;align-items:center;gap:13px;padding-bottom:13px;border-bottom:1px solid var(--line)}
.cf-qr{flex:none;width:150px;border-left:1px solid var(--line);background:var(--cream);padding:14px 12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;text-align:center}
.cf-qr .qr-box{width:112px;height:112px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:7px;display:grid;place-items:center}
.cf-qr .qr-box svg{width:100%;height:100%;display:block}
.cf-qr .qr-cap{font-size:9px;font-weight:800;color:var(--brand);letter-spacing:.4px;text-transform:uppercase;line-height:1.3}
.cf-qr .qr-sub{font-size:8px;color:var(--mute);line-height:1.35}
.cf-nego .av{width:50px;height:50px;border-radius:50%;flex:none;background:linear-gradient(150deg,var(--brand),var(--brand-d));display:grid;place-items:center;color:#fff;font-family:'Spectral',serif;font-size:19px;font-weight:600}
.cf-role{font-size:8.5px;font-weight:800;color:var(--brand);letter-spacing:1.3px;text-transform:uppercase}.cf-nm{font-family:'Spectral',serif;font-size:18px;font-weight:600;margin-top:2px}
.cf-contact{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:6px}.cf-contact span{display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--body);font-weight:500}.cf-contact svg{width:12px;height:12px;color:var(--brand)}
.cf-agence-lbl{font-size:8.5px;font-weight:800;color:var(--brand);letter-spacing:1.3px;text-transform:uppercase;margin-top:14px}
.cf-agence{display:flex;align-items:center;gap:14px;margin-top:9px}
.cf-agence-photo{flex:none;width:72px;height:58px;border-radius:9px;background:var(--cream);border:1px dashed #d8cfc8;display:grid;place-items:center;color:var(--brand);overflow:hidden}
.cf-agence-photo svg{width:30px;height:30px;opacity:.7}.cf-agence-photo img{width:100%;height:100%;object-fit:cover}
.cf-agence .cf-rows{margin-top:0;flex:1;min-width:0}
.cf-rows{margin-top:9px;display:flex;flex-direction:column;gap:8px}.cf-row{display:flex;align-items:center;gap:10px;font-size:11px;color:var(--body)}
.cf-row .i{width:24px;height:24px;flex:none;border-radius:7px;background:var(--cream);display:grid;place-items:center;color:var(--brand)}.cf-row .i svg{width:12px;height:12px}
.disc{font-size:9.5px;color:var(--body);line-height:1.5;padding:9px 13px;background:var(--cream);border-radius:9px;border-left:3px solid var(--brand);margin-top:10px}.disc b{color:var(--ink)}
.legal{font-size:8px;color:var(--mute);line-height:1.55;margin-top:10px}
/* ===== Visuels ===== */
.energy2{display:flex;gap:24px;margin-top:6px}
.rg,.rg-img{flex:1;min-width:0}.rg-h{font-size:8.5px;font-weight:800;color:var(--brand);letter-spacing:.6px;text-transform:uppercase;margin-bottom:8px}
.rg-row{display:flex;align-items:center;gap:7px;height:18px;margin-bottom:3px}
.rg-bar{display:inline-flex;align-items:center;padding-left:8px;color:#fff;font-weight:800;font-size:9.5px;height:14px;border-radius:0 7px 7px 0}
.rg-row.on .rg-bar{height:18px;font-size:11px;box-shadow:0 2px 4px rgba(0,0,0,.22)}
.rg-cur{font-size:11px;font-weight:800}.rg-na{font-size:10px;color:var(--mute);padding:8px 0}
.rg-img img{width:100%;max-height:118px;object-fit:contain;display:block}
.dn{display:flex;align-items:center;gap:22px}.dn-c1{font-family:'Spectral',serif;font-size:27px;font-weight:700;fill:var(--ink)}.dn-c2{font-size:10px;fill:var(--mute);text-transform:uppercase;letter-spacing:1px}
.dn-side{flex:1}.dn-leg{display:flex;flex-direction:column;gap:5px;margin-bottom:11px}
.dn-li{display:flex;align-items:center;gap:7px;font-size:10.5px}.dn-li b{margin-left:auto;font-size:12px;color:var(--ink)}.dn .dot{width:9px;height:9px;border-radius:3px}
.pics{display:grid;grid-template-columns:1fr 1fr;gap:8px}.pic{display:flex;align-items:center;gap:8px}.pic-ic{width:28px;height:28px;border-radius:8px;background:var(--cream);display:grid;place-items:center;color:var(--brand);flex:none}.pic-ic svg{width:15px;height:15px}
.pic b{font-size:12px;color:var(--ink);display:block;line-height:1.1}.pic small{font-size:9px;color:var(--mute)}
.jgs{display:flex;flex-direction:column;gap:11px;margin-top:4px}
.jg-top{display:flex;justify-content:space-between;margin-bottom:5px}.jg-l{font-size:11px;font-weight:600;color:var(--ink)}.jg-v{font-size:10.5px;font-weight:700}
.jg-bar{display:flex;gap:4px}.jg-c{flex:1;height:8px;border-radius:4px;background:#ece5dd}
.cdv-map .mp{position:absolute;width:22px;height:22px;border-radius:50%;background:#fff;border:2px solid var(--line);display:grid;place-items:center;box-shadow:0 1px 3px rgba(0,0,0,.35);transform:translate(-50%,-50%)}
.cdv-map .mp svg{width:14px;height:14px}
.cdv-map .mp.home{width:30px;height:30px;border:none;background:none;box-shadow:none;transform:translate(-50%,-100%);filter:drop-shadow(0 2px 3px rgba(0,0,0,.4))}
.cdv-map .mp.ecole{border-color:#1d4ed8}.cdv-map .mp.commerce{border-color:#0e7a4b}.cdv-map .mp.sante{border-color:var(--brand)}
.cdv-leg{display:flex;gap:14px;margin-top:9px;font-size:9.5px;color:var(--body)}.cdv-leg span{display:inline-flex;align-items:center;gap:5px}.cdv-leg i{width:9px;height:9px;border-radius:50%}
.commune-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start}
.cm-h{font-size:8.5px;font-weight:800;color:var(--brand);letter-spacing:.6px;text-transform:uppercase;margin:4px 0 11px}
.pop{display:flex;flex-direction:column}.pop-main{display:flex;flex-direction:column;align-items:flex-start}
.pop-v{font-family:'Spectral',serif;font-size:32px;font-weight:700;color:var(--ink);line-height:1}.pop-l{font-size:10px;color:var(--mute);text-transform:uppercase;letter-spacing:.5px;margin:4px 0 9px}
.pop-badge{font-size:10px;font-weight:700;padding:4px 9px;border-radius:18px;display:inline-block}
.pop-chart{margin-top:12px}.pop-ax{display:flex;justify-content:space-between;font-size:9px;color:var(--mute);margin-top:2px}
.rev-row{display:flex;align-items:center;gap:10px;margin-bottom:9px}.rev-l{width:120px;font-size:10.5px;color:var(--body)}.rev-row.hl .rev-l{font-weight:700;color:var(--brand)}
.rev-track{flex:1;height:15px;background:var(--cream);border-radius:8px;overflow:hidden}.rev-bar{display:block;height:100%;border-radius:8px;background:linear-gradient(90deg,#d98cae,#c9c2bc)}
.rev-row.hl .rev-bar{background:linear-gradient(90deg,var(--brand),var(--brand-d))}
.rev-v{width:70px;text-align:right;font-size:11.5px;font-weight:700;color:var(--ink)}.rev-note{font-size:9px;color:var(--mute);margin-top:5px}
`;

// ============================ VISUELS PDF (avis de valeur) ============================
const ESTIM_DPECOL = { A: "#2a9d3f", B: "#57b03a", C: "#a0cf3a", D: "#f5d800", E: "#f3a712", F: "#ec6c1f", G: "#d7191c" };
const ESTIM_POI_ICO = {
  ecole: '<svg viewBox="0 0 24 24" fill="#fff" stroke="#1d4ed8" stroke-width="1.5"><path d="M3 9l9-5 9 5-9 5z"/><path d="M7 11v4c0 1 5 3 5 3s5-2 5-3v-4"/></svg>',
  commerce: '<svg viewBox="0 0 24 24" fill="#fff" stroke="#0e7a4b" stroke-width="1.5"><path d="M4 8h16l-1 11H5z"/><path d="M9 8a3 3 0 0 1 6 0"/></svg>',
  sante: '<svg viewBox="0 0 24 24" fill="#fff" stroke="#c5005f" stroke-width="1.5"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M12 8v8M8 12h8" stroke="#c5005f" stroke-width="2"/></svg>',
};

// ① Réglette DPE/GES : image officielle si dispo (et réalisée), sinon réglette CSS depuis la lettre.
function estimReglette(kind, letter, imgUrl) {
  const img = String(imgUrl || "").trim();
  if (img && !/nonEffectue/i.test(img)) {
    return `<div class="rg-img"><div class="rg-h">${kind === "dpe" ? "DPE · consommation énergie" : "GES · émissions CO₂"}</div><img src="${estimText(img)}" alt="${kind.toUpperCase()}"></div>`;
  }
  const cls = String(letter || "").trim().toUpperCase();
  const rows = ["A", "B", "C", "D", "E", "F", "G"].map((l, i) => {
    const w = 38 + i * 9, on = l === cls;
    return `<div class="rg-row${on ? " on" : ""}"><span class="rg-bar" style="width:${w}%;background:${ESTIM_DPECOL[l]}">${l}</span>${on ? `<span class="rg-cur" style="color:${ESTIM_DPECOL[l]}">◀</span>` : ""}</div>`;
  }).join("");
  return `<div class="rg"><div class="rg-h">${kind === "dpe" ? "DPE · consommation énergie" : "GES · émissions CO₂"}</div>${cls && ESTIM_DPECOL[cls] ? rows : `<div class="rg-na">${kind.toUpperCase()} à compléter</div>`}</div>`;
}

// ② Donut composition du bien (répartition des pièces) + pictos chiffrés.
function estimDonut(detail, pieces, surface) {
  const ch = Math.max(0, parseInt(pieces, 10) || 0);
  const cb = Math.max(0, parseInt(detail.chambres, 10) || 0);
  const eau = (parseInt(detail.sdb, 10) || 0) + (parseInt(detail.se, 10) || 0);
  const autres = Math.max(0, ch - cb);
  const segs = [{ l: "Chambres", v: cb, c: "#c5005f" }, { l: "Pièces d'eau", v: Math.max(1, eau), c: "#e0662a" }, { l: "Séjour + autres", v: Math.max(1, autres), c: "#8a0042" }].filter((s) => s.v > 0);
  const tot = segs.reduce((s, x) => s + x.v, 0) || 1;
  const R = 52, C = 2 * Math.PI * R; let a0 = 0;
  const arcs = segs.map((s) => { const frac = s.v / tot, len = frac * C, off = C * (a0 / 360); a0 += frac * 360; return `<circle r="${R}" cx="70" cy="70" fill="none" stroke="${s.c}" stroke-width="18" stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-off}" transform="rotate(-90 70 70)"></circle>`; }).join("");
  const legend = segs.map((s) => `<div class="dn-li"><span class="dot" style="background:${s.c}"></span>${s.l}<b>${s.v}</b></div>`).join("");
  const pic = (ic, n, l) => `<div class="pic"><span class="pic-ic">${ic}</span><div><b>${n}</b><small>${l}</small></div></div>`;
  const I = {
    bed: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18v-6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6M3 18h18M3 14h18M7 10V8a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2"></path></svg>',
    bath: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12h16v3a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4z"></path><path d="M6 12V6a2 2 0 0 1 2-2"></path></svg>',
    surf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M3 9h18M9 21V9"></path></svg>',
    room: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"></rect></svg>',
  };
  return `<div class="dn"><svg viewBox="0 0 140 140" width="124" height="124">${arcs}<text x="70" y="64" text-anchor="middle" class="dn-c1">${ch || "—"}</text><text x="70" y="82" text-anchor="middle" class="dn-c2">pièces</text></svg>
    <div class="dn-side"><div class="dn-leg">${legend}</div><div class="pics">${pic(I.bed, cb || "—", "chambres")}${pic(I.bath, eau || "—", "salles de bain/eau")}${pic(I.surf, surface ? surface + " m²" : "—", "surface")}${pic(I.room, ch || "—", "pièces")}</div></div></div>`;
}

// ③ Jauge de risque (5 crans, niveau coloré)
function estimJauge(label, level) {
  const s = String(level || "").toLowerCase();
  if (!s) return "";
  let n = 1, col = "#1f8a5b";
  if (/élev|elev|fort|catégorie 3|categorie 3|zone 4|zone 5/.test(s)) { n = 4; col = "#d7191c"; }
  else if (/modér|moder|moyen|catégorie 2|categorie 2|zone 3/.test(s)) { n = 3; col = "#f3a712"; }
  else if (/faible|catégorie 1|categorie 1|zone 1|zone 2/.test(s)) { n = 2; col = "#1f8a5b"; }
  const cells = Array.from({ length: 5 }, (_, i) => `<span class="jg-c" style="${i < n ? `background:${col}` : ""}"></span>`).join("");
  return `<div class="jg"><div class="jg-top"><span class="jg-l">${estimText(label)}</span><span class="jg-v" style="color:${col}">${estimText(level)}</span></div><div class="jg-bar">${cells}</div></div>`;
}

// ④ Carte IGN + pins (bien + commodités). Bbox parsée depuis l'URL WMS (EPSG:3857).
function estimMapMerc(lat, lon) { return { x: lon * 20037508.34 / 180, y: Math.log(Math.tan((90 + lat) * Math.PI / 360)) / (Math.PI / 180) * 20037508.34 / 180 }; }

// Plan cadastral : fond Plan IGN v2 + surcouche parcellaire (PCI Express), centré sur le bien.
// Zoom serré (parcelle visible). Réutilise le WMS data.geopf.fr déjà employé pour le cadre de vie.
function estimCadastreMapUrl(lat, lon, half) {
  if (!Number.isFinite(+lat) || !Number.isFinite(+lon)) return null;
  const m = estimMapMerc(+lat, +lon);
  const hy = half || 260, hx = hy * (760 / 460);
  const bbox = `${m.x - hx},${m.y - hy},${m.x + hx},${m.y + hy}`;
  return `https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2,CADASTRALPARCELS.PARCELLAIRE_EXPRESS&STYLES=,&CRS=EPSG:3857&BBOX=${bbox}&WIDTH=760&HEIGHT=460&FORMAT=image/png`;
}
function estimMapWithPins(cdv) {
  if (!cdv || !cdv.mapUrl) return "";
  const homeSvg = '<svg viewBox="0 0 24 24" fill="#c5005f" stroke="#fff" stroke-width="1.5"><path d="M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7z"/><circle cx="12" cy="9" r="2.4" fill="#fff"/></svg>';
  const bb = (String(cdv.mapUrl).match(/[?&]BBOX=([^&]+)/i) || [])[1];
  const parts = bb ? bb.split(",").map(Number) : null;
  const pins = [];
  if (parts && parts.length === 4 && parts.every(Number.isFinite)) {
    const [minx, miny, maxx, maxy] = parts;
    const pct = (lat, lon) => { const p = estimMapMerc(lat, lon); return { x: (p.x - minx) / (maxx - minx) * 100, y: (maxy - p.y) / (maxy - miny) * 100 }; };
    if (Number.isFinite(+cdv.lat) && Number.isFinite(+cdv.lon)) { const c = pct(+cdv.lat, +cdv.lon); pins.push(`<span class="mp home" style="left:${c.x}%;top:${c.y}%">${homeSvg}</span>`); }
    const pois = (cdv.commodites && Array.isArray(cdv.commodites.pois)) ? cdv.commodites.pois : [];
    let n = 0;
    for (const p of pois) { if (!Number.isFinite(+p.lat) || !Number.isFinite(+p.lon)) continue; const c = pct(+p.lat, +p.lon); if (c.x >= 2 && c.x <= 98 && c.y >= 2 && c.y <= 98) { pins.push(`<span class="mp ${p.type}">${ESTIM_POI_ICO[p.type] || ""}</span>`.replace("<span ", `<span style="left:${c.x}%;top:${c.y}%" `)); if (++n >= 14) break; } }
  } else if (Number.isFinite(+cdv.lat)) {
    pins.push(`<span class="mp home" style="left:50%;top:50%">${homeSvg}</span>`);
  }
  return `<div class="cdv-map"><img src="${estimText(cdv.mapUrl)}" alt="Carte du secteur">${pins.join("")}</div>`;
}

// ⑤ Courbe d'évolution de la population (série INSEE complète).
function estimPopChart(prof) {
  if (!prof || !prof.population) return "";
  const evoCol = (prof.pop_evolution || 0) >= 4 ? "#1f8a5b" : (prof.pop_evolution || 0) <= -4 ? "#d7191c" : "#e0a800";
  const fmt = (n) => Number(n).toLocaleString("fr-FR");
  const badge = `<span class="pop-badge" style="background:${evoCol}1a;color:${evoCol}">${estimText(prof.pop_tendance || "—")}${prof.pop_evolution != null ? ` · ${prof.pop_evolution > 0 ? "+" : ""}${prof.pop_evolution}% / 15 ans` : ""}</span>`;
  let chart = "";
  const ser = prof.pop_series && typeof prof.pop_series === "object" ? Object.entries(prof.pop_series).map(([y, v]) => [parseInt(y, 10), Number(v)]).filter(([y, v]) => y && v).sort((a, b) => a[0] - b[0]) : [];
  if (ser.length >= 3) {
    const W = 380, H = 96, P = 6;
    const ys = ser.map((s) => s[1]), x0 = ser[0][0], x1 = ser[ser.length - 1][0];
    const vmin = Math.min(...ys), vmax = Math.max(...ys), span = (vmax - vmin) || vmax * 0.1;
    const X = (y) => P + (y - x0) / ((x1 - x0) || 1) * (W - 2 * P);
    const Y = (v) => P + (1 - (v - (vmin - span * 0.15)) / ((vmax + span * 0.15) - (vmin - span * 0.15))) * (H - 2 * P);
    const pts = ser.map((s) => `${X(s[0]).toFixed(1)},${Y(s[1]).toFixed(1)}`).join(" ");
    const area = `${P},${H - P} ${pts} ${W - P},${H - P}`;
    chart = `<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" preserveAspectRatio="none"><polygon points="${area}" fill="${evoCol}14"></polygon><polyline points="${pts}" fill="none" stroke="${evoCol}" stroke-width="2.2"></polyline><circle cx="${X(x1).toFixed(1)}" cy="${Y(ser[ser.length - 1][1]).toFixed(1)}" r="3.4" fill="${evoCol}"></circle></svg>
      <div class="pop-ax"><span>${x0}</span><span>${x1}</span></div>`;
  }
  return `<div class="pop"><div class="pop-main"><div class="pop-v">${fmt(prof.population)}</div><div class="pop-l">habitants${prof.population_annee ? " · " + prof.population_annee : ""}</div>${badge}</div><div class="pop-chart">${chart}</div></div>`;
}

// ⑥ Revenu médian comparatif (commune / département / France).
function estimRevenuChart(prof) {
  if (!prof || !prof.revenu_median) return "";
  const fmt = (n) => Number(n).toLocaleString("fr-FR") + " €";
  const rows = [
    { l: (prof.commune || "Commune"), v: prof.revenu_median, hl: true },
    prof.dept_revenu_median ? { l: "Département (médiane)", v: prof.dept_revenu_median } : null,
    prof.france_revenu_median ? { l: "France", v: prof.france_revenu_median } : null,
  ].filter(Boolean);
  const max = Math.max(...rows.map((r) => r.v));
  return `<div class="rev">${rows.map((r) => `<div class="rev-row${r.hl ? " hl" : ""}"><span class="rev-l">${estimText(r.l)}</span><span class="rev-track"><span class="rev-bar" style="width:${Math.round(r.v / max * 100)}%"></span></span><span class="rev-v">${fmt(r.v)}</span></div>`).join("")}<div class="rev-note">Niveau de vie médian annuel — INSEE FiLoSoFi</div></div>`;
}

// Logos officiels (design system) embarqués en base64 -> PDF self-contained.
function estimAssetDataUri(file) {
  try { return "data:image/png;base64," + fs.readFileSync(path.join(__dirname, "assets", file)).toString("base64"); }
  catch (_) { return null; }
}
const ESTIM_LOGO_COVER = estimAssetDataUri("gti-logo-cover.png");  // logo complet fond foncé : couverture
const ESTIM_MARK = estimAssetDataUri("gti-mark.png");              // carré magenta arrondi : autres pages

function estimationAvisValeurHtmlPremium(payload, dossier, detail) {
  detail = detail || {};
  const bien = payload.bien || {};
  const prop = payload.proprietaire || {};
  const nego = payload.negociateur || {};
  const valeurs = payload.valeurs || {};
  const now = new Date();
  const dateLong = `${now.getDate()} ${ESTIM_MOIS_FR[now.getMonth()]} ${now.getFullYear()}`;
  const ref = String(bien.reference || dossier.numero_dossier || dossier.hektor_annonce_id || "").trim();
  const docNumber = "AV-" + (ref || "ESTIM").toString().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);
  const LOGO = "https://www.gti-immobilier.fr/images/logoSite.png";
  const titre = estimText(bien.titre, "Votre bien");
  const type = bien.type || null;
  const ville = bien.ville || null;
  const cp = bien.code_postal || null;
  const localite = [cp, ville].filter(Boolean).join(" ");
  const surface = detail.surface || (bien.surface ? Number(bien.surface) : null);
  const terrain = detail.terrain || null;
  const pieces = detail.pieces || (bien.pieces ? Number(bien.pieces) : null);
  const chambres = detail.chambres || null;
  const garage = detail.garage || null;
  const photos = Array.isArray(detail.photos) ? detail.photos : [];
  const descriptif = detail.descriptif || null;
  const proprio = estimText(prop.nom, "Propriétaire");
  const negoNom = estimText(nego.nom, "Votre conseiller Groupe GTI");
  const agence = estimText(nego.agence, "Groupe GTI");
  const tel = String(nego.telephone || "").trim();
  const email = String(nego.email || "").trim();
  const agenceTel = String(nego.agenceTel || "").trim();
  const agenceMail = String(nego.agenceMail || "").trim();
  const agencePhoto = String(nego.agencePhoto || "").trim();
  const qrSvg = String(payload._vcardQrSvg || "").trim();
  const avis = String(payload.commentaire || "").trim();
  const argPrix = String(payload.argumentaire || "").trim();
  const valEstimee = estimEuro(valeurs.estimee) || "À compléter";
  const valBasse = estimEuro(valeurs.basse) || "—";
  const valHaute = estimEuro(valeurs.haute) || "—";
  const todo = (t) => `<span class="todo">${estimText(t)}</span>`;
  const cellSpec = (k, v, has) => `<div class="spec"><div class="k">${k}</div><div class="v">${has ? v : '<span class="todo">—</span>'}</div></div>`;
  const photoCell = (i, cls) => photos[i] ? `<div class="g ${cls || ""}"><img src="${estimText(photos[i])}" alt=""></div>` : `<div class="g ${cls || ""}"></div>`;
  const heroImg = photos[0] ? `<img src="${estimText(photos[0])}" alt="">` : "";
  const tags = [surface ? surface + " m²" : null, pieces ? pieces + " pièces" : null, terrain ? "Terrain " + terrain + " m²" : null].filter(Boolean).map((t) => `<span>${estimText(t)}</span>`).join("");
  const rh = `<div class="rh"><img src="${ESTIM_MARK || LOGO}" alt=""><div class="meta"><div class="t serif">Avis de valeur</div><div class="d">${titre} · ${estimText(ville || "")} · ${docNumber}</div></div></div>`;
  const rf = (n) => `<div class="rf"><span>GTI Immobilier · Avis de valeur ${docNumber}</span><span class="pg">Page ${n} / ${totalPages}</span></div>`;
  const initials = (String(nego.nom || "GTI").trim().split(/\s+/).map((p) => p[0]).join("").slice(0, 2) || "GTI").toUpperCase();
  const pricePerM2 = (surface && Number(valeurs.estimee)) ? `soit ≈ ${estimEuro(Math.round(Number(valeurs.estimee) / surface))}/m² · net vendeur indicatif` : "net vendeur indicatif";

  // --- Champs éditoriaux saisis par le négociateur (Lot B) : état, points, charges, DPE/GES.
  const etat = payload.etat || {};
  const note = Math.max(0, Math.min(5, Number(etat.note) || 0));
  const stars = Array.from({ length: 5 }, (_, i) =>
    `<svg viewBox="0 0 24 24" fill="currentColor" class="${i < note ? "on" : "off"}"><path d="M12 2l2.9 6.3 6.9.7-5.1 4.6 1.4 6.8L12 17.8 5.9 20.4l1.4-6.8L2.2 9l6.9-.7z"></path></svg>`).join("");
  const etatLabel = String(etat.label || "").trim();
  const etatMeta = (k, v) => `<div><div class="k">${k}</div><div class="v">${v ? estimText(v) : todo("—")}</div></div>`;
  const toList = (v) => Array.isArray(v) ? v.filter(Boolean) : String(v || "").split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
  const forts = toList(payload.pointsForts);
  const vigi = toList(payload.pointsVigilance);
  const ptsItems = (arr, icon) => arr.length
    ? arr.map((t) => `<li>${icon}${estimText(t)}</li>`).join("")
    : `<li>${todo("À compléter par votre conseiller")}</li>`;
  const checkIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5 10 17 19 7"></path></svg>`;
  const warnIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path><path d="M12 9v4M12 17h.01"></path></svg>`;
  const charges = payload.charges || {};
  const chargeRow = (k, v) => { const e = estimEuro(v); return `<div class="diag-row"><span class="k">${k}</span><span class="v ${e ? "" : "na"}">${e ? e + "/an" : todo("à compléter")}</span></div>`; };
  const dpe = String((bien.dpe || etat.dpe) || "").trim().toUpperCase();
  const ges = String((bien.ges || etat.ges) || "").trim().toUpperCase();
  const dpeColors = { A: "#2a9d3f", B: "#57b03a", C: "#a0cf3a", D: "#f5d800", E: "#f3a712", F: "#ec6c1f", G: "#d7191c" };
  const validite = String(payload.validite || "3 mois").trim();
  const methode = String(payload.methode || "").trim() || "Estimation par comparaison directe avec les transactions récentes du secteur, ajustées selon les caractéristiques du bien (surface, terrain, état, performance énergétique).";

  // --- Données marché DVF (Lot C) : passées par le front (payload.marche) ---
  const marche = payload.marche && payload.marche.ok ? payload.marche : null;
  const mEvo = marche && Array.isArray(marche.evolution) ? marche.evolution : [];
  // v2 : on privilégie la MÉDIANE (repli moyenne) ; nb de comparables après nettoyage.
  const mMed = marche ? (marche.median_prix_m2 || marche.avg_prix_m2 || null) : null;
  const mCount = marche ? (marche.count_clean != null ? marche.count_clean : marche.count) : null;
  const mRadius = marche && marche.radius_km != null ? marche.radius_km : null;
  const mP25 = marche && marche.p25_prix_m2 ? marche.p25_prix_m2 : null;
  const mP75 = marche && marche.p75_prix_m2 ? marche.p75_prix_m2 : null;
  const mFiable = marche ? marche.fiable !== false : true;
  const mTrend = mEvo.length >= 2 && mEvo[0].prix_m2 ? Math.round(((mEvo[mEvo.length - 1].prix_m2 - mEvo[0].prix_m2) / mEvo[0].prix_m2) * 1000) / 10 : null;
  const mComps = marche && Array.isArray(marche.comparables) ? marche.comparables : [];
  const mCompsList = mComps.slice(0, 10);
  const totalPages = mCompsList.length ? 9 : 8;
  const mEvoMax = mEvo.length ? Math.max(...mEvo.map((e) => e.prix_m2 || 0)) : 0;
  const dateCourt = (s) => { const p = String(s || "").split("-"); return p.length === 3 ? `${p[2]}/${p[1]}/${p[0].slice(2)}` : s; };
  const compRow = (c) => `<div class="comp"><div class="info"><div class="t">${estimText(c.type)} ${c.surface ? c.surface + " m²" : ""}${c.pieces ? " · " + estimText(c.pieces) + " p." : ""}</div><div class="d">${estimText(c.commune)}${c.terrain ? " · terrain " + c.terrain + " m²" : ""} · ${estimText(dateCourt(c.date))} · ${estimText(c.distance_km)} km</div></div><div class="stat"><div class="p tnum">${estimEuro(c.valeur) || "—"}</div><div class="pm tnum">${c.prix_m2 ? estimEuro(c.prix_m2) + "/m²" : ""}</div></div><span class="bdg">Vendu</span></div>`;
  const compTableRow = (c, i) => `<div class="dvf-row"><div class="dvf-main"><b>${i + 1}. ${estimText(c.type || "Bien")} ${c.surface ? c.surface + " m²" : ""}${c.pieces ? " · " + estimText(c.pieces) + " p." : ""}</b><small>${estimText(c.commune || "—")}${c.terrain ? " · terrain " + estimText(c.terrain) + " m²" : ""}</small></div><span class="dvf-muted">${estimText(dateCourt(c.date) || "—")}</span><span class="tnum">${c.surface ? estimText(c.surface) + " m²" : "—"}</span><span class="dvf-num tnum">${estimEuro(c.valeur) || "—"}</span><span class="dvf-num tnum">${c.prix_m2 ? estimEuro(c.prix_m2) + "/m²" : "—"}</span><span class="dvf-muted tnum">${c.distance_km != null ? estimText(c.distance_km) + " km" : "—"}</span></div>`;
  const evoBars = mEvo.map((e) => `<div class="bcol"><div class="bv tnum">${estimEuro(e.prix_m2) || "—"}</div><div class="bar${e === mEvo[mEvo.length - 1] ? " hl" : ""}" style="height:${mEvoMax ? Math.round((e.prix_m2 / mEvoMax) * 11) + 4 : 4}mm"></div><div class="bk">${estimText(e.annee)}</div></div>`).join("");

  // --- Lot B : blocs détaillés (caractéristiques étendues, intérieur/extérieur/équipements, diagnostics réels) ---
  const detRow = (k, v) => v != null && v !== "" ? `<div class="diag-row"><span class="k">${k}</span><span class="v">${estimText(v)}</span></div>` : "";
  const ouiSurf = (oui, surf) => oui ? (surf ? `Oui · ${surf} m²` : "Oui") : null;
  const interieurRows = [
    detRow("Salles de bain", detail.sdb), detRow("Salles d'eau", detail.se), detRow("WC", detail.wc),
    detRow("Surface séjour", detail.surfSejour ? detail.surfSejour + " m²" : null),
    detRow("Surface Carrez", detail.surfCarrez ? detail.surfCarrez + " m²" : null),
    detRow("Cuisine", detail.cuisine), detRow("Équipement cuisine", detail.cuisineEquip),
    detRow("Exposition", detail.exposition), detRow("Vue", detail.vue),
  ].join("");
  const exterieurRows = [
    detRow("Murs mitoyens", detail.mursMitoyens), detRow("Niveaux", detail.niveaux),
    detRow("Jardin", ouiSurf(detail.jardin === "Oui", detail.surfJardin)), detRow("Piscine", detail.piscine),
    detRow("Terrasse", ouiSurf(detail.terrasse === "Oui", detail.surfTerrasse)),
    detRow("Cave", ouiSurf(detail.cave === "Oui", detail.surfCave)),
    detRow("Garage", detail.surfGarage ? detail.surfGarage + " m²" : detail.garage),
    detRow("Parking intérieur", detail.parkInt), detRow("Parking extérieur", detail.parkExt),
  ].join("");
  const confortRows = [
    detRow("Chauffage", [detail.chauffageType, detail.chauffageEnergie].filter(Boolean).join(" · ") || null),
    detRow("Eau", detail.eau), detRow("Assainissement", detail.assainissement),
  ].join("");
  const equipDefs = [["Double vitrage", detail.doubleVitrage], ["Triple vitrage", detail.tripleVitrage], ["Volets électriques", detail.voletsElec], ["Cheminée", detail.cheminee], ["Climatisation", detail.climatisation], ["Porte blindée", detail.porteBlindee], ["Interphone", detail.interphone], ["Visiophone", detail.visiophone], ["Alarme", detail.alarme], ["Digicode", detail.digicode], ["Détecteur de fumée", detail.detecteurFumee], ["Accès handicapé", detail.accesHandi]];
  const equipList = equipDefs.filter(([, v]) => v).map(([k]) => `<span class="eqp">${checkIcon}${k}</span>`).join("");
  const hasDetailPage = !!(interieurRows || exterieurRows || confortRows || equipList || detail.particularites);
  const acquereursN = Math.max(0, parseInt(payload.acquereurs, 10) || 0);
  // Cadre de vie & risques (carte IGN + commodités + risques), passé par le front.
  const cdv = payload.cadreDeVie && payload.cadreDeVie.ok ? payload.cadreDeVie : null;
  const dpeImg = detail.dpe_img || null, gesImg = detail.ges_img || null;
  const inseeProfil = cdv && cdv.insee_profil ? cdv.insee_profil : null;
  const cdvCom = cdv && cdv.commodites ? cdv.commodites : null;
  const cdvRisk = cdv && cdv.risques ? cdv.risques : null;
  // Éléments cadastraux (payload.cadastre, enrichi server-side si besoin) : parcelle(s) + PLU.
  const cad = payload.cadastre && payload.cadastre.ok ? payload.cadastre : null;
  const cadParcelles = cad && Array.isArray(cad.parcelles) ? cad.parcelles : [];
  const cadPlu = cad && cad.plu ? cad.plu : null;
  const cadLat = cad && Number.isFinite(+cad.lat) ? +cad.lat : (cdv && Number.isFinite(+cdv.lat) ? +cdv.lat : null);
  const cadLon = cad && Number.isFinite(+cad.lon) ? +cad.lon : (cdv && Number.isFinite(+cdv.lon) ? +cdv.lon : null);
  const cadMapUrl = cad && cadLat != null && cadLon != null ? estimCadastreMapUrl(cadLat, cadLon) : null;
  const lvlColor = (v) => { const s = String(v || "").toLowerCase(); if (/élev|elev|fort/.test(s)) return "#d7191c"; if (/moyen/.test(s)) return "#f3a712"; if (/faible/.test(s)) return "#1f8a5b"; return "var(--mute)"; };
  const cdvRow = (k, v) => `<div class="cdv-row"><span>${estimText(k)}</span><b>${estimText(v)}</b></div>`;
  const cdvLvl = (k, v) => v ? `<div class="cdv-lvl"><div class="k">${k}</div><div class="v" style="color:${lvlColor(v)}">${estimText(v)}</div></div>` : "";
  // Barème d'état par poste (saisie négo) : barres colorées page État.
  const POSTE_NIV = { neuf: { c: "#1f8a5b", f: 100, t: "Neuf / Refait" }, bon: { c: "#46a35a", f: 84, t: "Bon état" }, correct: { c: "#e0a800", f: 55, t: "Correct" }, aprevoir: { c: "#e0662a", f: 30, t: "À prévoir" } };
  const postes = (etat.postes && Array.isArray(etat.postes)) ? etat.postes.filter((p) => p && POSTE_NIV[p.niveau]) : [];
  const posteRow = (p) => { const n = POSTE_NIV[p.niveau]; const lbl = (p.label && String(p.label).trim()) ? String(p.label).trim() : n.t; return `<div class="pst"><div class="pst-top"><span class="pst-n">${estimText(p.poste)}</span><span class="pst-v" style="color:${n.c}">${estimText(lbl)}</span></div><span class="pst-bar"><span class="pst-fill" style="width:${n.f}%;background:${n.c}"></span></span></div>`; };
  const postesBlock = postes.length ? `<div class="pst-leg"><span><i style="background:#1f8a5b"></i>Neuf / Refait</span><span><i style="background:#46a35a"></i>Bon état</span><span><i style="background:#e0a800"></i>Correct</span><span><i style="background:#e0662a"></i>À prévoir</span></div><div class="pst-grid">${postes.map(posteRow).join("")}</div>` : "";
  const diagOtherLines = Object.entries(detail.diagnostics || {}).filter(([label]) => label !== "DPE").map(([label, d]) =>
    `<div class="diag-row"><span class="k">${label}</span><span class="v ${d && d.done ? "ok" : "na"}">${d && d.done ? "Réalisé · " + estimText(dateCourt(d.date)) : "Non communiqué"}</span></div>`).join("");

  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Avis de valeur ${docNumber}</title>
<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>${ESTIM_PREMIUM_CSS}</style></head><body>
<div class="page cover">
  <div class="c-head"><img src="${ESTIM_LOGO_COVER || LOGO}" alt="GTI Immobilier"><div class="ref">Dossier confidentiel<b>N° ${docNumber}</b></div></div>
  <div class="c-hero">${heroImg}<div class="c-photo-tag"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6z"></path></svg>Établi par un professionnel</div></div>
  <div class="c-hero-foot">
    <span class="c-kicker"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6z"></path></svg>Estimation immobilière</span>
    <div class="c-title serif">Avis de valeur</div>
    <div class="c-bien serif">${titre}</div>
    <div class="c-loc"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>${estimText(localite || "—")}</div>
    <div class="c-tags">${[tags, dpe ? `<span>DPE ${dpe}</span>` : ""].filter(Boolean).join("") || '<span class="todo">Caractéristiques à compléter</span>'}</div>
  </div>
  <div class="c-info"><div class="c-info-row">
    <div class="c-info-cell"><span class="l">Établi pour</span><span class="v">${proprio}</span></div>
    <div class="c-info-cell"><span class="l">Conseiller</span><span class="v">${negoNom}</span></div>
    <div class="c-info-cell"><span class="l">Date · validité</span><span class="v">${dateLong} · ${estimText(validite)}</span></div>
  </div></div>
</div>
<div class="page">${rh}<div class="content">
  <div class="h">Votre bien en images</div>
  <div class="gal">${photoCell(0, "big")}${photoCell(1)}${photoCell(2)}${photoCell(3)}${photoCell(4)}</div>
  <div class="h mt">Caractéristiques principales</div>
  <div class="specs">
    ${cellSpec("Type", estimText(type), !!type)}
    ${cellSpec("Surface", `${surface} <small>m²</small>`, !!surface)}
    ${cellSpec("Terrain", `${terrain} <small>m²</small>`, !!terrain)}
    ${cellSpec("Pièces", estimText(pieces), !!pieces)}
    ${cellSpec("Chambres", estimText(chambres), !!chambres)}
    ${cellSpec("Garage", estimText(garage), !!garage)}
    ${cellSpec("Étage", estimText(detail.etage), !!detail.etage)}
    ${detail.niveaux ? cellSpec("Niveaux", estimText(detail.niveaux), true) : ""}
    ${detail.anneeConstruction ? cellSpec("Année constr.", estimText(detail.anneeConstruction), true) : ""}
    ${detail.copropriete ? cellSpec("Copropriété", estimText(detail.copropriete) + (detail.coproprieteNbLots ? ` · ${detail.coproprieteNbLots} lots` : ""), true) : ""}
    ${cellSpec("Localité", estimText(localite), !!localite)}
  </div>
  <div class="h mt">Performance énergétique</div>
  <div class="energy2">${estimReglette("dpe", dpe, dpeImg)}${estimReglette("ges", ges, gesImg)}</div>
  <div class="h mt">Descriptif</div>
  <p style="font-size:11.5px;color:var(--body);line-height:1.7">${descriptif ? estimEscapeHtml(descriptif) : todo("Descriptif du bien à compléter par votre conseiller.")}</p>
</div>${rf(2)}</div>
<div class="page">${rh}<div class="content">
  <div class="h">Composition du bien</div>
  ${estimDonut(detail, pieces, surface)}
  <div class="h mt">Le bien en détail</div>
  ${hasDetailPage ? `<div class="detail-grid">
    ${interieurRows ? `<div class="diag"><div class="diag-h">Intérieur</div>${interieurRows}</div>` : ""}
    ${exterieurRows ? `<div class="diag"><div class="diag-h">Extérieur</div>${exterieurRows}</div>` : ""}
    ${confortRows ? `<div class="diag"><div class="diag-h">Confort &amp; énergie</div>${confortRows}</div>` : ""}
  </div>
  ${equipList ? `<div class="h mt">Équipements &amp; sécurité</div><div class="eqps">${equipList}</div>` : ""}
  ${detail.particularites ? `<div class="h mt">Particularités</div><p style="font-size:11px;color:var(--body);line-height:1.6">${estimEscapeHtml(detail.particularites)}</p>` : ""}`
  : `<p style="font-size:11.5px;color:var(--body);line-height:1.7">${todo("Caractéristiques détaillées non renseignées dans la fiche du bien.")}</p>`}
</div>${rf(3)}</div>
<div class="page">${rh}<div class="content">
  <div class="h">Cadre de vie &amp; localisation${cdv && cdv.commune ? ` · ${estimText(cdv.commune)}` : ""}</div>
  ${cdv ? `${estimMapWithPins(cdv)}
  ${cdvCom && Array.isArray(cdvCom.pois) && cdvCom.pois.length ? `<div class="cdv-leg"><span><i style="background:var(--brand)"></i>Le bien</span><span><i style="background:#1d4ed8"></i>Écoles</span><span><i style="background:#0e7a4b"></i>Commerces</span><span><i style="background:#c5005f"></i>Santé</span></div>` : ""}
  <div class="cdv-grid">
    <div class="cdv-card"><div class="ch">À proximité</div>
      ${cdvCom ? cdvRow("Écoles", (cdvCom.ecoles || 0) + " à moins d'1,5 km") + cdvRow("Commerces", (cdvCom.commerces || 0) + " à moins d'1 km") + cdvRow("Santé", (cdvCom.sante || 0) + " (pharmacie, médecin…)") + (cdvCom.gareKm != null ? cdvRow("Gare", estimText(cdvCom.gareNom) + " · " + cdvCom.gareKm + " km") : "") : `<div class="cdv-row">${todo("Commodités à charger")}</div>`}
    </div>
    <div class="cdv-card"><div class="ch">Accès aux pôles</div>
      ${cdv.poles && cdv.poles.length ? cdv.poles.map((p) => cdvRow(p.nom, p.km + " km")).join("") : `<div class="cdv-row">${todo("—")}</div>`}
    </div>
  </div>
  <div class="h mt">Risques (état des risques)</div>
  ${cdvRisk ? `${cdvRisk.risques && cdvRisk.risques.length ? `<div class="cdv-risks">${cdvRisk.risques.map((r) => `<span class="cdv-risk">${estimText(r)}</span>`).join("")}</div>` : ""}
  <div class="jgs">${estimJauge("Potentiel radon", cdvRisk.radon)}${estimJauge("Sismicité", cdvRisk.sismicite)}${estimJauge("Retrait-gonflement argiles", cdvRisk.argiles)}</div>` : `<p style="font-size:11px;color:var(--mute)">${todo("Risques à charger par votre conseiller.")}</p>`}
  <div class="disc" style="margin-top:14px"><b>Sources.</b> Fond de carte IGN · commodités OpenStreetMap · risques Géorisques (état des risques). Données indicatives ; l'état des risques officiel (ERP) est annexé au compromis.</div>`
  : `<p style="font-size:11.5px;color:var(--body);line-height:1.7">${todo("Cadre de vie, carte et risques à charger par votre conseiller (bouton « Charger le cadre de vie »).")}</p>`}
  ${cad ? `<div class="h mt">Éléments cadastraux${cadPlu && cadPlu.zone ? ` · PLU ${estimText(cadPlu.zone)}` : ""}</div>
  ${cadMapUrl ? `<div class="cdv-map"><img src="${estimText(cadMapUrl)}" alt="Plan cadastral"><span class="mp home" style="left:50%;top:50%">${homeSvg}</span></div>` : ""}
  <div class="cdv-grid">
    <div class="cdv-card"><div class="ch">Parcelle${cadParcelles.length > 1 ? "s" : ""} cadastrale${cadParcelles.length > 1 ? "s" : ""}</div>
      ${cadParcelles.length ? cadParcelles.map((p) => cdvRow(estimText(p.reference || "—"), p.contenance ? Number(p.contenance).toLocaleString("fr-FR") + " m²" : "—")).join("") : `<div class="cdv-row">${todo("—")}</div>`}
      ${cadParcelles.length > 1 && cad.contenance_totale ? cdvRow("Contenance totale", Number(cad.contenance_totale).toLocaleString("fr-FR") + " m²") : ""}
    </div>
    <div class="cdv-card"><div class="ch">Urbanisme</div>
      ${cadPlu ? cdvRow("Zone PLU", estimText(cadPlu.zone || "—")) + (cadPlu.type ? cdvRow("Type de zone", estimText(cadPlu.type)) : "") + (cadPlu.libelle ? cdvRow("Libellé", estimText(cadPlu.libelle)) : "") : `<div class="cdv-row">${todo("Zonage PLU non disponible sur ce secteur")}</div>`}
    </div>
  </div>
  <div class="disc" style="margin-top:12px"><b>Sources.</b> Parcellaire IGN (PCI Express) · zonage Géoportail de l'Urbanisme. Références à titre informatif ; le titre de propriété et le document d'arpentage font foi. Identité du propriétaire non communiquée (donnée nominative).</div>` : ""}
</div>${rf(4)}</div>
<div class="page">${rh}<div class="content">
  <div class="h">Profil de la commune${inseeProfil && inseeProfil.commune ? ` · ${estimText(inseeProfil.commune)}` : (cdv && cdv.commune ? ` · ${estimText(cdv.commune)}` : "")}</div>
  ${inseeProfil ? `<div class="cm-h">Population</div>${estimPopChart(inseeProfil)}
  <div class="cm-h" style="margin-top:22px">Revenu des ménages</div>${estimRevenuChart(inseeProfil)}
  <div class="disc" style="margin-top:18px"><b>Source.</b> INSEE — recensements de la population (séries historiques) et dispositif FiLoSoFi (niveau de vie médian annuel). Données communales à titre informatif.</div>`
  : `<p style="font-size:11.5px;color:var(--body);line-height:1.7">${todo("Profil INSEE de la commune à charger (population, revenu médian) — via le bouton « Charger le cadre de vie ».")}</p>`}
</div>${rf(5)}</div>
<div class="page">${rh}<div class="content">
  <div class="h">État du logement &amp; prestations</div>
  <div class="etat-top">
    <div class="etat-stars">${stars}</div>
    <div><div class="etat-rl serif">${etatLabel ? estimText(etatLabel) : todo("État à évaluer")}</div><div class="etat-rs">${etatLabel ? "Évaluation du conseiller" : "À renseigner par votre conseiller"}</div></div>
    <div class="etat-sep"></div>
    <div class="etat-meta">${etatMeta("Chauffage", etat.chauffage || [detail.chauffageType, detail.chauffageEnergie].filter(Boolean).join(" · "))}${etatMeta("Exposition", etat.exposition || detail.exposition)}${etatMeta("Toiture", etat.toiture)}${etatMeta("Menuiseries", etat.menuiseries || (detail.doubleVitrage ? "Double vitrage" : detail.tripleVitrage ? "Triple vitrage" : ""))}</div>
  </div>
  ${etat.commentaire ? `<p style="font-size:11px;color:var(--body);line-height:1.65;margin-top:12px">${estimEscapeHtml(String(etat.commentaire))}</p>` : ""}
  ${postesBlock}
  <div class="pts-grid">
    <div class="pts forts"><div class="ph"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5 10 17 19 7"></path></svg>Points forts</div><ul>${ptsItems(forts, checkIcon)}</ul></div>
    <div class="pts vigi"><div class="ph"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"></path><path d="M12 9v4M12 17h.01"></path></svg>Points de vigilance</div><ul>${ptsItems(vigi, warnIcon)}</ul></div>
  </div>
  <div class="method"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"></circle><path d="M12 16v-4M12 8h.01"></path></svg><div><div class="t">Méthode d'estimation</div><div class="d">${estimText(methode)}</div></div></div>
  <div class="h" style="margin-top:22px">Diagnostics &amp; charges</div>
  <div class="diag-grid">
    <div class="diag"><div class="diag-h">Diagnostics obligatoires</div>
      <div class="diag-row"><span class="k">DPE &amp; GES</span><span class="v ${dpe ? "ok" : "na"}">${dpe ? "Réalisé · " + dpe + (ges ? " / " + ges : "") : "À actualiser"}</span></div>
      ${diagOtherLines}
    </div>
    <div class="diag"><div class="diag-h">Charges annuelles estimées</div>
      ${chargeRow("Taxe foncière", charges.taxe_fonciere || detail.taxeFonciere)}
      ${detail.taxeHabitation ? chargeRow("Taxe d'habitation", detail.taxeHabitation) : ""}
      ${chargeRow("Énergie", charges.energie || detail.coutMax)}
      ${chargeRow("Eau", charges.eau)}
      ${chargeRow("Assurance", charges.assurance)}
      ${detail.charges ? chargeRow("Charges copro.", detail.charges) : ""}
    </div>
  </div>
</div>${rf(6)}</div>
<div class="page">${rh}<div class="content">
  <div class="h">Valeur vénale estimée</div>
  <div class="val"><div class="grid">
    <div><div class="lbl">Notre estimation</div><div class="main serif">${valEstimee}</div><div class="sub">${pricePerM2}</div></div>
    <div><div class="gauge-h">Positionnement de marché</div><div class="gbar"><div class="gpin"></div></div>
      <div class="gends"><div class="gend" style="text-align:left"><div class="v serif tnum">${valBasse}</div><div class="k">Bas</div></div><div class="gend mid"><div class="v serif tnum">${valEstimee}</div><div class="k">Conseillé</div></div><div class="gend" style="text-align:right"><div class="v serif tnum">${valHaute}</div><div class="k">Haut</div></div></div>
    </div>
  </div></div>
  ${argPrix
    ? `<div class="method" style="margin-top:12px"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"></circle><path d="M12 16v-4M12 8h.01"></path></svg><div><div class="t">L'analyse de votre conseiller sur la valeur</div><div class="d">${estimEscapeHtml(argPrix)}</div></div></div>`
    : `<p style="font-size:10.5px;color:var(--mute);margin-top:10px;line-height:1.55">Le prix conseillé vise une commercialisation dans un délai raisonnable. Un positionnement dans le haut de la fourchette est possible mais allonge généralement le délai de vente.</p>`}
  ${acquereursN > 0 ? `<div class="acq"><span class="acq-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><path d="m21 21-4.3-4.3"></path></svg></span><div><b>${acquereursN} acquéreur${acquereursN > 1 ? "s" : ""}</b> de notre fichier recherche${acquereursN > 1 ? "nt" : ""} actuellement un bien correspondant au vôtre.</div></div>` : ""}
  <div class="h mt">Le marché en chiffres${marche && marche.commune ? ` · ${estimText(marche.commune)}` : ""}</div>
  <div class="stats">
    <div class="scard"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"></path><path d="m7 14 4-4 3 3 5-6"></path></svg></span><div class="v tnum">${mMed ? estimEuro(mMed) + "<small>/m²</small>" : todo("—")}</div><div class="l">Prix médian · ${estimText(marche ? marche.type : "secteur")}</div></div>
    <div class="scard"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"></path><path d="m19 9-5 5-4-4-3 3"></path></svg></span><div class="v tnum">${mTrend != null ? (mTrend >= 0 ? "+" : "") + mTrend + " %" : todo("—")}</div><div class="l">Évolution prix/m²</div></div>
    <div class="scard"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"></path><rect x="7" y="10" width="3" height="8"></rect><rect x="14" y="6" width="3" height="12"></rect></svg></span><div class="v tnum">${mCount != null ? mCount : todo("—")}</div><div class="l">Comparables${mRadius != null ? " · " + mRadius + " km" : ""}</div></div>
  </div>${marche && !mFiable ? `<p style="font-size:10px;color:#9a3412;margin-top:6px">Échantillon limité (${mCount} comparables) — valeurs de marché à confirmer par votre conseiller.</p>` : ""}
  ${mEvo.length ? `<div class="chart"><div class="ch"><div class="t">Évolution du prix au m² · secteur</div><div class="s">${mEvo[0].annee} → ${mEvo[mEvo.length - 1].annee}</div></div><div class="bars">${evoBars}</div></div>` : ""}
  ${mCompsList.length ? `<div class="disc"><b>Comparables DVF.</b> ${mCompsList.length} ventes retenues sont listées page suivante${mComps.length > mCompsList.length ? ` (sur ${mComps.length} ventes reçues du moteur).` : "."}</div>` : ""}
  <div class="disc"><b>Source.</b> Données issues des Demandes de Valeurs Foncières (DVF, open data publique) ${marche ? `· prix <b>médian</b> sur ${mCount} ventes ${estimText(marche.type)} comparables, dans un rayon de ${mRadius} km${marche.commune ? " autour de " + estimText(marche.commune) : ""}, sur ${Math.round(marche.months / 12)} ans · ventes en bloc exclues, surface ±25 %` : "— à charger par votre conseiller"}. Valeurs à titre indicatif.</div>
</div>${rf(7)}</div>
${mCompsList.length ? `<div class="page">${rh}<div class="content">
  <div class="h">Biens comparables DVF vendus</div>
  <p class="dvf-sub">Liste compacte des ${mCompsList.length} ventes comparables retenues pour documenter le prix au m² et la fourchette de valeur.</p>
  <div class="dvf-table"><div class="dvf-head"><span>Bien</span><span>Date</span><span>Surface</span><span>Prix</span><span>Prix/m²</span><span>Dist.</span></div>${mCompsList.map(compTableRow).join("")}</div>
  <div class="disc"><b>Source.</b> Demandes de Valeurs Foncières (DVF, open data publique)${marche ? ` · ${mCount} ventes ${estimText(marche.type)} analysées dans un rayon de ${mRadius} km${marche.commune ? " autour de " + estimText(marche.commune) : ""}` : ""}. Affichage : ${mCompsList.length} ventes listées dans le document.</div>
</div>${rf(8)}</div>` : ""}
<div class="page">${rh}<div class="content">
  <div class="h">L'avis de votre conseiller</div>
  <div class="avis"><div class="lead">${avis ? estimEscapeHtml(avis) : "Estimation établie à partir des caractéristiques du bien et de la connaissance du marché local."}</div></div>
  <div class="h mt">Votre conseiller</div>
  <div class="contact-fuse"><div class="cf-body">
    <div class="cf-nego"><div class="av">${estimText(initials)}</div><div><div class="cf-role">Votre conseiller</div><div class="cf-nm serif">${negoNom}</div>
      <div class="cf-contact">${tel ? `<span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 4h4l2 5-3 2a11 11 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"></path></svg>${estimText(tel)}</span>` : ""}${email ? `<span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="m3 7 9 6 9-6"></path></svg>${estimText(email)}</span>` : ""}</div></div></div>
    <div class="cf-agence-lbl">Agence</div>
    <div class="cf-agence">
      <div class="cf-agence-photo">${agencePhoto ? `<img src="${estimText(agencePhoto)}" alt="${estimText(agence)}">` : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 21V9l9-6 9 6v12"></path><path d="M3 21h18M9 21v-6h6v6"></path><path d="M9 11h.01M15 11h.01"></path></svg>`}</div>
      <div class="cf-rows">
        <div class="cf-row"><span class="i"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21V8l9-5 9 5v13"></path></svg></span><b>${agence}</b></div>
        ${agenceTel ? `<div class="cf-row"><span class="i"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 4h4l2 5-3 2a11 11 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"></path></svg></span>${estimText(agenceTel)}</div>` : ""}
        ${agenceMail ? `<div class="cf-row"><span class="i"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="m3 7 9 6 9-6"></path></svg></span>${estimText(agenceMail)}</div>` : ""}
      </div>
    </div>
  </div>${qrSvg ? `<aside class="cf-qr"><div class="qr-box">${qrSvg}</div><div class="qr-cap">Ajoutez-moi à vos contacts</div><div class="qr-sub">Scannez avec l'appareil photo de votre téléphone</div></aside>` : ""}</div>
  <div class="disc"><b>Avis de valeur indicatif.</b> Le présent document constitue une estimation de la valeur vénale du bien, établie à partir des éléments communiqués et de la connaissance du marché local. Il ne constitue ni une expertise au sens réglementaire, ni un engagement sur un prix de vente.</div>
  <div class="legal">GROUPE GTI, SAS au capital de 309 968 € — Siège : 22 rue Jean Jaurès, 42700 Firminy — RCS Saint-Étienne 502 811 144 — Carte professionnelle CPI 42022019 000 043 878 (CCI Lyon St Étienne Roanne).</div>
</div>${rf(totalPages)}</div>
</body></html>`;
}

function estimationAvisValeurHtml(payload, dossier) {
  const bien = payload.bien || {};
  const prop = payload.proprietaire || {};
  const nego = payload.negociateur || {};
  const valeurs = payload.valeurs || {};
  const now = new Date();
  const dateLong = `${now.getDate()} ${ESTIM_MOIS_FR[now.getMonth()]} ${now.getFullYear()}`;
  const reference = String(bien.reference || dossier.hektor_annonce_id || "").trim();
  const docNumber = "AV-" + (reference || "ESTIM").toString().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);

  const valEstimee = estimEuro(valeurs.estimee) || "À compléter";
  const valBasse = estimEuro(valeurs.basse) || "À compléter";
  const valHaute = estimEuro(valeurs.haute) || "À compléter";

  const caracteristiques = [
    ["Type", estimText(bien.type, "—")],
    ["Surface", bien.surface ? estimText(bien.surface) + " m²" : "—"],
    ["Pièces", estimText(bien.pieces, "—")],
    ["Terrain", bien.terrain ? estimText(bien.terrain) + " m²" : "—"],
    ["DPE", estimText(bien.dpe, "—")],
    ["Localité", estimText([bien.code_postal, bien.ville].filter(Boolean).join(" "), "—")],
  ].map(([k, v]) => `<div><div class="ck">${k}</div><div class="cv">${v}</div></div>`).join("");

  const commentaire = String(payload.commentaire || "").trim();
  const commentaireBlock = commentaire
    ? `<section class="notice"><span class="lbl">L'avis du négociateur</span><p>${estimEscapeHtml(commentaire)}</p></section>`
    : "";

  return `<!doctype html>
<html lang="fr"><head><meta charset="utf-8" /><title>Avis de valeur ${docNumber}</title>
<style>
  *{box-sizing:border-box}
  html,body{margin:0;color:#222323;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.45;background:#fff}
  .sheet{padding:4mm 2mm}
  .head{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid #c5005f;padding-bottom:12px;margin-bottom:16px}
  .brand{font-size:18px;font-weight:bold;letter-spacing:.5px}
  .brand small{display:block;font-size:11px;font-weight:normal;color:#7a7570;letter-spacing:0}
  .head-meta{text-align:right}
  .head-meta .doc{font-size:20px;font-weight:bold;color:#c5005f}
  .head-meta .sub{font-size:11px;color:#7a7570}
  .to{margin-bottom:16px}
  .to .lbl,.lbl{display:block;font-size:10px;font-weight:bold;letter-spacing:.06em;text-transform:uppercase;color:#c5005f;margin-bottom:4px}
  .to .nm{font-size:14px;font-weight:bold}
  .to .ad{font-size:12px;color:#555}
  .bien{border:1px solid #e6dde1;border-radius:8px;padding:12px 14px;margin-bottom:16px;background:#fffafb}
  .bien .titre{font-size:14px;font-weight:bold;margin-bottom:10px}
  .carac{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .ck{font-size:10px;color:#9a948f;text-transform:uppercase;letter-spacing:.04em}
  .cv{font-size:13px;font-weight:bold}
  .value{display:grid;grid-template-columns:1fr 1.3fr 1fr;gap:10px;align-items:end;text-align:center;background:#fbeaf0;border-radius:8px;padding:16px;margin-bottom:16px}
  .value .vk{font-size:10px;color:#993556;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}
  .value .vmain{font-size:26px;font-weight:bold;color:#c5005f}
  .value .vside{font-size:15px;font-weight:bold;color:#72243e}
  .notice{border:1px solid #f0d4e2;border-left:3px solid #c5005f;border-radius:8px;padding:12px 14px;margin-bottom:16px;background:#fff6fa}
  .notice p{margin:6px 0 0;text-align:justify}
  .nego{display:flex;align-items:center;gap:12px;border-top:1px solid #e6dde1;padding-top:14px;margin-bottom:14px}
  .nego .av{width:44px;height:44px;border-radius:50%;background:#fbeaf0;color:#c5005f;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:15px;flex:none}
  .nego .nm{font-size:14px;font-weight:bold}
  .nego .co{font-size:12px;color:#555}
  .legal{font-size:10px;color:#9a948f;text-align:justify;border-top:1px solid #eee;padding-top:10px}
</style></head>
<body><main class="sheet">
  <section class="head">
    <div class="brand">GTI Immobilier<small>${estimText(nego.agence, "Groupe GTI")} · Estimation immobilière</small></div>
    <div class="head-meta"><div class="doc">Avis de valeur</div><div class="sub">Établi le ${dateLong} · réf. ${docNumber}</div></div>
  </section>
  <section class="to"><span class="lbl">À l'attention de</span><div class="nm">${estimText(prop.nom, "Propriétaire")}</div><div class="ad">${estimText([bien.code_postal, bien.ville].filter(Boolean).join(" "), "")}</div></section>
  <section class="bien"><div class="titre">${estimText(bien.titre, "Le bien")}</div><div class="carac">${caracteristiques}</div></section>
  <section class="value">
    <div><div class="vk">Fourchette basse</div><div class="vside">${valBasse}</div></div>
    <div><div class="vk">Valeur estimée</div><div class="vmain">${valEstimee}</div></div>
    <div><div class="vk">Fourchette haute</div><div class="vside">${valHaute}</div></div>
  </section>
  ${commentaireBlock}
  <section class="nego">
    <div class="av">${estimText((String(nego.nom || "GTI").trim().split(/\s+/).map((p) => p[0]).join("").slice(0, 2) || "GTI").toUpperCase())}</div>
    <div><div class="nm">${estimText(nego.nom, "Votre négociateur")}</div><div class="co">${estimText([nego.agence, nego.telephone, nego.email].filter(Boolean).join(" · "), "GTI Immobilier")}</div></div>
  </section>
  <section class="legal">Le présent avis de valeur constitue une estimation indicative de la valeur vénale du bien, établie à partir des éléments communiqués et de la connaissance du marché local. Il ne constitue ni une expertise au sens réglementaire, ni un engagement sur un prix de vente.</section>
</main></body></html>`;
}

async function renderHtmlToPdfBuffer(html, opts) {
  let browser = null;
  try {
    browser = await chromium.launch(browserLaunchOptions({ headless: true }));
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle", timeout: 30000 });
    return await page.pdf({
      format: "A4",
      printBackground: true,
      margin: (opts && opts.margin) || { top: "12mm", bottom: "12mm", left: "12mm", right: "12mm" },
    });
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

// vCard 3.0 du conseiller pour le QR de l'avis de valeur.
// IMPORTANT : code 100% séparé de buildVCard (apps/rdv-public/app.js, mini-sites vitrine).
// Aucun import/partage : modifier l'un n'affecte JAMAIS l'autre. buildVCard reste intouché.
function estimVCard(c) {
  const tel = String((c && c.telephone) || "").replace(/[^\d+]/g, "");
  const nom = String((c && c.nom) || "Conseiller Groupe GTI").trim();
  return [
    "BEGIN:VCARD", "VERSION:3.0",
    `N:${nom};;;`,
    `FN:${nom}`,
    `ORG:${String((c && c.agence) || "Groupe GTI").trim()}`,
    "TITLE:Conseiller immobilier",
    tel ? `TEL;TYPE=CELL:${tel}` : "",
    c && c.email ? `EMAIL;TYPE=WORK:${String(c.email).trim()}` : "",
    "URL:https://www.gti-immobilier.fr",
    "END:VCARD",
  ].filter(Boolean).join("\r\n");
}

// Résout le contact du conseiller pour le QR (option B : négo CONNECTÉ passé par le front),
// complète le portable depuis l'annuaire idnego (seul champ absent de la session front),
// puis repli agence. Voir mémoire estimation-qr-vcard-source-nego.
async function resolveEstimNegotiatorContact(payload, dossier, opts) {
  const safe = payload && typeof payload === "object" ? payload : {};
  const nego = safe.negociateur && typeof safe.negociateur === "object" ? safe.negociateur : {};
  const connected = safe.negociateurConnecte && typeof safe.negociateurConnecte === "object" ? safe.negociateurConnecte : {};
  const preferConnected = !!(opts && opts.preferConnected);
  // Option B (QR) : on part de l'email du conseiller CONNECTÉ ; nom/agence/portable seront
  // résolus depuis l'annuaire complet pour ne pas mélanger avec l'identité du dossier.
  const connectedEmail = preferConnected ? cleanString(connected.email) : null;
  const out = connectedEmail ? {
    nom: null, agence: null, email: connectedEmail, telephone: null,
  } : {
    nom: cleanString(nego.nom) || cleanString(dossier && dossier.commercial_nom),
    agence: cleanString(nego.agence) || cleanString(dossier && dossier.agence_nom),
    email: cleanString(nego.email) || cleanString(dossier && dossier.negociateur_email),
    telephone: cleanString(nego.telephone),
  };
  const negotiatorId = connectedEmail ? null : cleanString(nego.idnego || nego.hektor_negociateur_id
    || safe.hektor_negociateur_id || (dossier && dossier.commercial_id));
  const userId = cleanString(nego.hektor_user_id || safe.hektor_user_id);
  if (!out.telephone || !out.email || !out.agence || !out.nom) {
    const row = await loadAgencyDirectoryRowForOwner({ email: out.email, negotiatorId, userId }).catch(() => null);
    if (row) {
      const port = cleanString(row.portable) || cleanString(row.telephone);
      if (!out.telephone && port && /\d{6,}/.test(port)) out.telephone = port;
      if (!out.email) out.email = cleanString(row.email);
      if (!out.agence) out.agence = cleanString(row.agence_nom);
      if (!out.nom) out.nom = cleanString(row.display_name);
    }
  }
  // Coordonnées agence : toujours résolues (pour le bloc « Agence » du PDF) + repli conseiller.
  out.agenceTel = null;
  out.agenceMail = null;
  out.agenceResponsable = null;
  if (out.agence) {
    const ar = await supabaseRequest(
      `app_agence_directory?select=tel,mail,responsable&nom=ilike.${encodeURIComponent(out.agence)}&limit=1`,
      { method: "GET" }
    ).catch(() => null);
    const a = Array.isArray(ar) && ar.length ? ar[0] : null;
    if (a) {
      out.agenceTel = cleanString(a.tel);
      out.agenceMail = cleanString(a.mail);
      out.agenceResponsable = cleanString(a.responsable);
      // Repli conseiller : si le négo n'a ni tél ni email, on prend ceux de l'agence.
      if (!out.telephone) out.telephone = out.agenceTel;
      if (!out.email) out.email = out.agenceMail;
    }
  }
  return out;
}

async function handleGenerateEstimationPdf(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await logJob(job.id, "estimation_pdf", "running", "Generation de l'avis de valeur", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
  });

  const detail = await loadEstimationDetail(dossier.app_dossier_id || job.app_dossier_id);
  // Commodités : (re)calculées côté worker (IP fiable). Le proxy front/Render peut
  // échouer (Overpass bloque souvent les datacenters) -> on garantit la donnée ici.
  if (payload.cadreDeVie && payload.cadreDeVie.ok) {
    const cdvLat = Number(payload.cadreDeVie.lat), cdvLon = Number(payload.cadreDeVie.lon);
    if (Number.isFinite(cdvLat) && Number.isFinite(cdvLon) && cdvLat && cdvLon) {
      try { const com = await fetchCommodites(cdvLat, cdvLon); if (com) payload.cadreDeVie.commodites = com; }
      catch (_) { /* best effort */ }
    }
    // Profil commune INSEE (population + série + revenu) résolu par code INSEE.
    if (payload.cadreDeVie.insee) {
      try {
        const prof = await loadCommuneInsee(payload.cadreDeVie.insee, String(payload.cadreDeVie.insee).slice(0, 2));
        if (prof) payload.cadreDeVie.insee_profil = prof;
      } catch (_) { /* best effort */ }
    }
  }
  // Éléments cadastraux : si le front les a déjà passés (payload.cadastre.ok) on les garde,
  // sinon on tente un fetch server-side à partir des coords du bien (cadastre ou cadre de vie).
  if (!(payload.cadastre && payload.cadastre.ok)) {
    const cLat = Number((payload.cadastre && payload.cadastre.lat) ?? (payload.cadreDeVie && payload.cadreDeVie.lat));
    const cLon = Number((payload.cadastre && payload.cadastre.lon) ?? (payload.cadreDeVie && payload.cadreDeVie.lon));
    if (Number.isFinite(cLat) && Number.isFinite(cLon) && cLat && cLon) {
      try { const cad = await fetchCadastre(cLat, cLon); if (cad && cad.ok) payload.cadastre = cad; }
      catch (_) { /* best effort : le PDF se génère sans le bloc cadastre */ }
    }
  }
  // Bloc « Votre conseiller » + QR vCard (option B = conseiller CONNECTÉ, repli négo dossier).
  // On enrichit le bloc visible avec le mobile résolu + les coordonnées agence (tél/mail).
  try {
    const c = await resolveEstimNegotiatorContact(payload, dossier, { preferConnected: true });
    if (c) {
      payload.negociateur = Object.assign({}, payload.negociateur, {
        nom: c.nom || (payload.negociateur && payload.negociateur.nom) || null,
        agence: c.agence || (payload.negociateur && payload.negociateur.agence) || null,
        email: c.email || (payload.negociateur && payload.negociateur.email) || null,
        telephone: c.telephone || (payload.negociateur && payload.negociateur.telephone) || null,
        agenceTel: c.agenceTel || null,
        agenceMail: c.agenceMail || null,
        agenceResponsable: c.agenceResponsable || null,
      });
      if (c.nom || c.telephone || c.email) {
        const QRCode = require("qrcode");
        payload._vcardQrSvg = await QRCode.toString(estimVCard(c), {
          type: "svg", margin: 0, errorCorrectionLevel: "M",
          color: { dark: "#1c1c1c", light: "#00000000" },
        }).catch(() => "");
      }
    }
  } catch (_) { /* le PDF se génère même sans QR */ }
  const html = estimationAvisValeurHtmlPremium(payload, dossier, detail);
  // Marges PDF à 0 : chaque .page fait déjà 210×297mm (marge interne via --mx) -> 1 page
  // physique exacte. Sinon les marges 12mm font déborder la page de 297mm sur une 2e page.
  const pdfBuffer = await renderHtmlToPdfBuffer(html, { margin: { top: "0", bottom: "0", left: "0", right: "0" } });

  const label = (payload.document_label && String(payload.document_label).trim()) || "Avis de valeur";
  const filename = storageSafeFilename(`${label}.pdf`, "avis-de-valeur.pdf");
  const tempPath = `temp/uploads/${job.id}/${filename}`;
  await uploadStorageObject(tempPath, pdfBuffer, "application/pdf");

  // Réutilise le flux éprouvé upload_document_to_hektor (push Hektor + archive local+cloud).
  const rows = await supabaseRequest("app_console_job", {
    method: "POST",
    prefer: "return=representation",
    body: JSON.stringify([{
      job_type: "upload_document_to_hektor",
      app_dossier_id: dossier.app_dossier_id || job.app_dossier_id || null,
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      payload_json: {
        visibility: payload.visibility === "shared" ? "shared" : "private",
        document_type: "Avis de valeur",
        original_filename: filename,
        source_filename: filename,
        document_label: label,
        mime_type: "application/pdf",
        temp_storage_bucket: STORAGE_BUCKET,
        temp_storage_path: tempPath,
      },
      status: "pending",
      priority: 40,
      requested_by: job.requested_by || null,
      requested_at: new Date().toISOString(),
    }]),
  });
  const uploadJob = Array.isArray(rows) ? rows[0] : null;

  await logJob(job.id, "estimation_pdf", "done", "Avis de valeur genere, upload Hektor en file", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    pdf_bytes: pdfBuffer.length,
    upload_job_id: uploadJob ? uploadJob.id : null,
  });

  return {
    ok: true,
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    pdf_bytes: pdfBuffer.length,
    temp_storage_path: tempPath,
    upload_job_id: uploadJob ? uploadJob.id : null,
  };
}

// Genere le PDF du mandat a partir du HTML rendu cote front (payload.html), puis enchaine
// upload_document_to_hektor pour le DEPOSER DANS HEKTOR (prerequis a la signature ImmoSign).
// Calque 1:1 de handleGenerateEstimationPdf : meme moteur Puppeteer, meme flux de depot.
async function handleGenerateMandatDocument(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await logJob(job.id, "mandat_pdf", "running", "Generation du mandat", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
  });

  const html = String(payload && payload.html ? payload.html : "");
  if (!html.trim()) throw new Error("payload_json.html requis (HTML du mandat rendu cote front)");
  const pdfBuffer = await renderHtmlToPdfBuffer(html);

  const label = (payload.document_label && String(payload.document_label).trim()) || "Mandat de vente";
  const filename = storageSafeFilename(`${label}.pdf`, "mandat-de-vente.pdf");
  const tempPath = `temp/uploads/${job.id}/${filename}`;
  await uploadStorageObject(tempPath, pdfBuffer, "application/pdf");

  // Reutilise le flux eprouve upload_document_to_hektor (push Hektor + archive local+cloud).
  const rows = await supabaseRequest("app_console_job", {
    method: "POST",
    prefer: "return=representation",
    body: JSON.stringify([{
      job_type: "upload_document_to_hektor",
      app_dossier_id: dossier.app_dossier_id || job.app_dossier_id || null,
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      payload_json: {
        visibility: payload.visibility === "shared" ? "shared" : "private",
        document_type: "Mandat",
        original_filename: filename,
        source_filename: filename,
        document_label: label,
        mime_type: "application/pdf",
        temp_storage_bucket: STORAGE_BUCKET,
        temp_storage_path: tempPath,
      },
      status: "pending",
      priority: 40,
      requested_by: job.requested_by || null,
      requested_at: new Date().toISOString(),
    }]),
  });
  const uploadJob = Array.isArray(rows) ? rows[0] : null;

  await logJob(job.id, "mandat_pdf", "done", "Mandat genere, upload Hektor en file", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    pdf_bytes: pdfBuffer.length,
    upload_job_id: uploadJob ? uploadJob.id : null,
  });

  return {
    ok: true,
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    pdf_bytes: pdfBuffer.length,
    temp_storage_path: tempPath,
    upload_job_id: uploadJob ? uploadJob.id : null,
  };
}

// Document « Plan cadastral » : page A4 designée (plan IGN + surcouche parcellaire,
// tableau des parcelles + contenance, zonage PLU). Données IGN publiques.
function cadastrePlanHtml(cad, dossier) {
  const LOGO = "https://www.gti-immobilier.fr/images/logoSite.png";
  const now = new Date();
  const dateLong = `${now.getDate()} ${ESTIM_MOIS_FR[now.getMonth()]} ${now.getFullYear()}`;
  const titre = estimText(dossier && (dossier.titre_bien || dossier.adresse) || "", "Le bien");
  const ville = estimText(dossier && (dossier.ville || dossier.code_postal) || "", "");
  const ref = estimText(dossier && (dossier.numero_dossier || dossier.numero_mandat || dossier.hektor_annonce_id) || "", "");
  const parcelles = cad && Array.isArray(cad.parcelles) ? cad.parcelles : [];
  const plu = cad && cad.plu ? cad.plu : null;
  const mapUrl = cad ? estimCadastreMapUrl(cad.lat, cad.lon) : null;
  const rows = parcelles.length
    ? parcelles.map((p) => `<tr><td>${estimText(p.reference || "—")}</td><td>${estimText(p.commune || "—")}</td><td class="num">${p.contenance ? Number(p.contenance).toLocaleString("fr-FR") + " m²" : "—"}</td></tr>`).join("")
    : `<tr><td colspan="3" class="muted">Aucune parcelle trouvée.</td></tr>`;
  const total = cad && cad.contenance_totale ? Number(cad.contenance_totale).toLocaleString("fr-FR") + " m²" : null;
  const insee = parcelles.find((p) => p.code_insee) ? estimText(parcelles.find((p) => p.code_insee).code_insee) : "";
  const commune = parcelles.find((p) => p.commune) ? estimText(parcelles.find((p) => p.commune).commune) : (ville || "—");
  const docNo = "PC-" + (ref || "CAD").toString().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);
  const corner = (cls) => `<span class="tick ${cls}"></span>`;
  const statCard = (k, v, sub) => `<div class="scard"><div class="sv serif">${v}</div><div class="sk">${estimText(k)}</div>${sub ? `<div class="ss">${estimText(sub)}</div>` : ""}</div>`;
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8">
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
  @page { size: A4; margin: 0; }
  :root{--brand:#c5005f;--brand-d:#8c0044;--brand-50:#fbeaf2;--ink:#1d1e1f;--body:#42474a;--mute:#8b8f92;--faint:#b4b7b9;--cream:#f7f2ec;--line:#e4ddd2;--line2:#efe9df}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',system-ui,sans-serif;color:var(--ink);line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .serif{font-family:'Spectral',Georgia,serif}.tnum{font-variant-numeric:tabular-nums}
  .page{position:relative;width:210mm;height:297mm;padding:15mm 16mm 13mm;overflow:hidden;background:#fff}
  .page::before{content:"";position:absolute;top:0;left:0;right:0;height:6mm;background:linear-gradient(90deg,var(--brand),var(--brand-d))}
  /* running header */
  .rh{display:flex;align-items:center;justify-content:space-between;padding:4mm 0 9px;border-bottom:1px solid var(--line)}
  .rh .bd{display:flex;align-items:center;gap:9px}.rh img{height:30px;width:30px;border-radius:7px}
  .rh .wm{font-family:'Spectral',serif;font-size:13px;font-weight:700;letter-spacing:.01em;line-height:1}
  .rh .wm small{display:block;font-family:'Inter',sans-serif;font-size:7.5px;font-weight:700;letter-spacing:.22em;color:var(--mute);text-transform:uppercase;margin-top:3px}
  .rh .meta{text-align:right}.rh .meta .t{font-size:7.5px;font-weight:800;letter-spacing:.18em;color:var(--brand);text-transform:uppercase}
  .rh .meta .d{font-size:8.5px;color:var(--mute);margin-top:3px;letter-spacing:.04em}
  /* hero */
  .hero{margin-top:13px}
  .hero .ey{font-size:8.5px;font-weight:800;letter-spacing:.2em;color:var(--brand);text-transform:uppercase}
  .hero h1{font-family:'Spectral',serif;font-size:34px;font-weight:700;letter-spacing:-.02em;line-height:1;margin-top:7px;color:#1a1614}
  .hero .sub{font-family:'Spectral',serif;font-style:italic;font-weight:500;font-size:14px;color:#4a4038;margin-top:9px}
  /* plan frame — survey sheet */
  .plan{position:relative;margin-top:15px;height:104mm;border:1px solid var(--line);border-radius:11px;overflow:hidden;background:#eef0ec;box-shadow:0 1px 0 #fff inset,0 6px 18px rgba(20,14,18,.07)}
  .plan img{width:100%;height:100%;object-fit:cover;display:block}
  .plan .grid{position:absolute;inset:0;background-image:linear-gradient(rgba(28,20,24,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(28,20,24,.05) 1px,transparent 1px);background-size:14mm 14mm;pointer-events:none}
  .plan .tick{position:absolute;width:18px;height:18px}
  .plan .tick::before,.plan .tick::after{content:"";position:absolute;background:var(--brand)}
  .plan .tick::before{width:18px;height:2px}.plan .tick::after{width:2px;height:18px}
  .plan .tl{top:9px;left:9px}.plan .tr{top:9px;right:9px}.plan .tr::before{right:0}.plan .tr::after{right:0}
  .plan .bl{bottom:9px;left:9px}.plan .bl::before{bottom:0}.plan .bl::after{bottom:0}
  .plan .br{bottom:9px;right:9px}.plan .br::before{right:0;bottom:0}.plan .br::after{right:0;bottom:0}
  .plan .mk{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:54px;height:54px;display:grid;place-items:center}
  .plan .mk .halo{position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle,rgba(197,0,95,.22),rgba(197,0,95,0) 68%)}
  .plan .mk .dot{position:relative;width:13px;height:13px;border-radius:50%;background:var(--brand);box-shadow:0 0 0 3px #fff,0 2px 5px rgba(0,0,0,.35)}
  .plan .mk .cx,.plan .mk .cy{position:absolute;background:rgba(197,0,95,.55)}
  .plan .mk .cx{left:50%;top:-7px;width:1.4px;height:68px;transform:translateX(-50%)}
  .plan .mk .cy{top:50%;left:-7px;height:1.4px;width:68px;transform:translateY(-50%)}
  .plan .cap{position:absolute;left:0;bottom:0;right:0;display:flex;justify-content:space-between;padding:7px 12px;font-size:8px;font-weight:600;letter-spacing:.05em;color:#fff;background:linear-gradient(0deg,rgba(20,14,18,.62),rgba(20,14,18,0))}
  .plan .empty{display:grid;place-items:center;height:100%;font-size:11px;color:var(--mute)}
  /* lower split */
  .split{display:grid;grid-template-columns:1.32fr .9fr;gap:14px;margin-top:16px}
  .sh{font-size:8.5px;font-weight:800;letter-spacing:.16em;color:var(--brand);text-transform:uppercase;margin-bottom:8px}
  table{width:100%;border-collapse:collapse}
  thead th{font-size:8px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--mute);text-align:left;padding:0 9px 6px;border-bottom:1.5px solid var(--ink)}
  thead th.num{text-align:right}
  tbody td{padding:9px;border-bottom:1px solid var(--line2);font-size:11.5px}
  tbody tr:last-child td{border-bottom:none}
  td.ref{font-family:'Spectral',serif;font-weight:600;font-size:13px;letter-spacing:.02em}
  td.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
  td.muted{color:var(--mute);font-style:italic}
  .tot{display:flex;align-items:baseline;justify-content:space-between;margin-top:9px;padding:9px 11px;background:var(--cream);border-radius:8px}
  .tot .k{font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--body)}
  .tot .v{font-family:'Spectral',serif;font-size:19px;font-weight:700;color:var(--brand)}
  /* PLU accent */
  .plu{border:1px solid var(--line);border-radius:11px;overflow:hidden}
  .plu .top{padding:13px 14px 12px;background:linear-gradient(135deg,#fff,var(--brand-50))}
  .plu .lbl{font-size:8px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--brand)}
  .plu .z{font-family:'Spectral',serif;font-size:30px;font-weight:700;letter-spacing:-.01em;color:#1a1614;line-height:1;margin-top:5px}
  .plu .ty{display:inline-block;margin-top:8px;padding:3px 9px;border-radius:999px;background:var(--brand);color:#fff;font-size:8.5px;font-weight:700;letter-spacing:.05em}
  .plu .desc{padding:11px 14px;font-size:10px;color:var(--body);line-height:1.5;border-top:1px solid var(--line2)}
  .plu .na{padding:16px 14px;font-size:10.5px;color:var(--mute);font-style:italic}
  /* stat row */
  .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}
  .scard{border:1px solid var(--line);border-radius:10px;padding:12px 13px;background:#fff}
  .scard .sv{font-family:'Spectral',serif;font-size:21px;font-weight:700;color:var(--ink);line-height:1}
  .scard .sk{font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--body);margin-top:7px}
  .scard .ss{font-size:9px;color:var(--mute);margin-top:2px}
  /* footer */
  .foot{position:absolute;left:16mm;right:16mm;bottom:8mm}
  .disc{font-size:8px;color:var(--faint);line-height:1.55}.disc b{color:var(--mute)}
  .rf{display:flex;justify-content:space-between;align-items:center;margin-top:8px;padding-top:7px;border-top:1px solid var(--line);font-size:8px;letter-spacing:.05em;color:var(--mute)}
  .rf .br{color:var(--brand);font-weight:700}
  </style></head><body><div class="page">
    <div class="rh">
      <div class="bd"><img src="${ESTIM_MARK || LOGO}" alt=""><div class="wm">GTI Immobilier<small>Conseil &amp; transaction</small></div></div>
      <div class="meta"><div class="t">Plan cadastral</div><div class="d">${docNo} · ${dateLong}</div></div>
    </div>
    <div class="hero">
      <div class="ey">Document parcellaire</div>
      <h1 class="serif">Plan cadastral</h1>
      <div class="sub">${titre}${ville ? " · " + ville : ""}${ref ? " · réf. " + ref : ""}</div>
    </div>
    <div class="plan">${mapUrl
      ? `<img src="${estimText(mapUrl)}" alt="Plan cadastral"><span class="grid"></span>${corner("tl")}${corner("tr")}${corner("bl")}${corner("br")}<span class="mk"><span class="halo"></span><span class="cx"></span><span class="cy"></span><span class="dot"></span></span><div class="cap"><span>Fond Plan IGN v2 · parcellaire PCI Express</span><span>Localisation indicative</span></div>`
      : `<div class="empty">Plan indisponible — coordonnées du bien manquantes.</div>`}</div>
    <div class="split">
      <div>
        <div class="sh">Références cadastrales</div>
        <table><thead><tr><th>Parcelle</th><th>Commune</th><th class="num">Contenance</th></tr></thead><tbody>${rows}</tbody></table>
        ${total ? `<div class="tot"><span class="k">Contenance ${parcelles.length > 1 ? "totale" : "cadastrale"}</span><span class="v tnum">${total}</span></div>` : ""}
      </div>
      <div>
        <div class="sh">Urbanisme</div>
        <div class="plu">${plu
          ? `<div class="top"><div class="lbl">Zone PLU</div><div class="z">${estimText(plu.zone || "—")}</div>${plu.type ? `<span class="ty">Type ${estimText(plu.type)}</span>` : ""}</div>${plu.libelle ? `<div class="desc">${estimText(plu.libelle)}</div>` : ""}`
          : `<div class="na">Zonage PLU non disponible sur ce secteur.</div>`}</div>
      </div>
    </div>
    <div class="stats">
      ${statCard(parcelles.length > 1 ? "Parcelles" : "Parcelle", parcelles.length || "—", parcelles.length > 1 ? "réunies" : "cadastrale")}
      ${statCard("Contenance", total ? total.replace(" m²", "") : "—", "m² · surface officielle")}
      ${statCard("Commune", commune, insee ? "INSEE " + insee : "")}
    </div>
    <div class="foot">
      <div class="disc"><b>Sources.</b> Parcellaire IGN (PCI Express) · fond Plan IGN v2 · zonage Géoportail de l'Urbanisme. Document établi le ${dateLong} à titre informatif ; le titre de propriété et le document d'arpentage font foi. L'identité du propriétaire n'est pas communiquée (donnée nominative).</div>
      <div class="rf"><span class="br">GTI Immobilier — Plan cadastral</span><span>${docNo}</span></div>
    </div>
  </div></body></html>`;
}

async function handleGenerateCadastreDocument(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await logJob(job.id, "cadastre_pdf", "running", "Generation du plan cadastral", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
  });

  const lat = Number(payload && payload.lat);
  const lon = Number(payload && payload.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || !lat || !lon) {
    throw new Error("payload_json.lat/lon requis (geolocalisation du bien absente)");
  }

  let cad;
  const chosen = payload && Array.isArray(payload.parcelles) ? payload.parcelles.filter((p) => p && (p.reference || p.numero)) : null;
  if (chosen && chosen.length) {
    // Parcelles choisies par l'utilisateur (sélecteur — cas « point sur la voie »).
    const mapLat = Number(payload.map_lat) || lat;
    const mapLon = Number(payload.map_lon) || lon;
    let contenance = 0;
    for (const p of chosen) { const c = parseInt(p.contenance, 10); if (Number.isFinite(c)) contenance += c; }
    let plu = null;
    try { const at = await fetchCadastre(mapLat, mapLon); if (at) plu = at.plu; } catch (_) { /* PLU best-effort */ }
    cad = { ok: true, lat: mapLat, lon: mapLon, parcelles: chosen, contenance_totale: contenance || null, plu };
  } else {
    // Sinon : recherche au point (comportement par défaut).
    cad = await fetchCadastre(lat, lon);
    if (!cad || !cad.ok) throw new Error("Aucune parcelle cadastrale trouvee pour ces coordonnees");
  }

  const html = cadastrePlanHtml(cad, dossier);
  // Document plein cadre (210×297, @page margin:0) : on rend sans marge Puppeteer, comme l'avis de valeur.
  const pdfBuffer = await renderHtmlToPdfBuffer(html, { margin: { top: "0", bottom: "0", left: "0", right: "0" } });

  const label = "Plan cadastral";
  const filename = storageSafeFilename(`${label}.pdf`, "plan-cadastral.pdf");
  const tempPath = `temp/uploads/${job.id}/${filename}`;
  await uploadStorageObject(tempPath, pdfBuffer, "application/pdf");

  // Reutilise le flux eprouve upload_document_to_hektor (push Hektor + archive local+cloud).
  const rows = await supabaseRequest("app_console_job", {
    method: "POST",
    prefer: "return=representation",
    body: JSON.stringify([{
      job_type: "upload_document_to_hektor",
      app_dossier_id: dossier.app_dossier_id || job.app_dossier_id || null,
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      payload_json: {
        visibility: payload.visibility === "shared" ? "shared" : "private",
        document_type: "Plan",
        original_filename: filename,
        source_filename: filename,
        document_label: label,
        mime_type: "application/pdf",
        temp_storage_bucket: STORAGE_BUCKET,
        temp_storage_path: tempPath,
      },
      status: "pending",
      priority: 40,
      requested_by: job.requested_by || null,
      requested_at: new Date().toISOString(),
    }]),
  });
  const uploadJob = Array.isArray(rows) ? rows[0] : null;

  // Persiste les elements cadastraux par dossier (re-affichage instant sans re-fetch).
  // Best-effort : si la table n'existe pas encore (migration non appliquee), on n'echoue pas.
  if (dossier.app_dossier_id != null) {
    try {
      await supabaseRequest("app_dossier_cadastre?on_conflict=app_dossier_id", {
        method: "POST",
        prefer: "resolution=merge-duplicates,return=minimal",
        body: JSON.stringify([{
          app_dossier_id: dossier.app_dossier_id,
          hektor_annonce_id: String(dossier.hektor_annonce_id),
          parcelles: cad.parcelles || [],
          contenance_totale: cad.contenance_totale || null,
          plu: cad.plu || null,
          updated_at: new Date().toISOString(),
        }]),
      });
    } catch (_) { /* table absente / RLS : non bloquant */ }
  }

  await logJob(job.id, "cadastre_pdf", "done", "Plan cadastral genere, upload Hektor en file", {
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    pdf_bytes: pdfBuffer.length,
    upload_job_id: uploadJob ? uploadJob.id : null,
  });

  return {
    ok: true,
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    parcelles: cad.parcelles ? cad.parcelles.length : 0,
    pdf_bytes: pdfBuffer.length,
    temp_storage_path: tempPath,
    upload_job_id: uploadJob ? uploadJob.id : null,
  };
}

async function handleUploadDocumentToHektor(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });
  const tempPath = payload.temp_storage_path;
  const filename = safeFilename(payload.original_filename, "document.pdf");
  const visibility = payload.visibility === "shared" ? "shared" : "private";
  const publicValue = visibility === "shared" ? "2" : "0";
  const publicKey = visibility === "shared" ? "partage" : "privee";
  const idContentDiv = visibility === "shared" ? "listDocUpload_partage" : "listDocUpload_privee";

  if (!tempPath) throw new Error("payload_json.temp_storage_path required");
  const temp = await downloadStorageObject(tempPath);
  const id = encodeURIComponent(String(dossier.hektor_annonce_id));
  const formUrl = `${XMLRPC_URL}?mode=UploadedDocument_uploadForm&type=bien&id_foreign=${id}&public=${publicValue}&publicKey=${publicKey}&idContentDiv=${idContentDiv}`;
  await hektorFetch(formUrl);

  const form = new FormData();
  form.set("type", "bien");
  form.set("id_foreign", String(dossier.hektor_annonce_id));
  form.set("subType", "0");
  form.set("subId", "0");
  form.set("public", publicValue);
  form.set("Filedata", new Blob([temp.buffer], { type: temp.mimeType }), filename);
  await hektorFetch(`${ADMIN_URL}upload_uploadeddoc.php`, { method: "POST", body: form, headers: {} });

  const entries = await fetchConsoleDocumentEntries(dossier.hektor_annonce_id);
  const indexed = await upsertConsoleDocuments(dossier, entries);
  const found = entries.find((entry) => entry.document_name === filename || entry.document_name.includes(filename) || filename.includes(entry.document_name));
  if (!found) throw new Error(`Upload Hektor non confirme dans la liste documents: ${filename}`);
  const storedRow = indexed.find((row) => row.hektor_document_id === found.hektor_document_id);
  const stored = storedRow ? await persistProvidedDocumentFile(storedRow, temp.buffer, temp.mimeType, { cloud: shouldKeepCloud(dossier) }) : null;
  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, dossier.hektor_annonce_id, {
    reason: "upload_document_to_hektor",
    priority: 82,
  });

  return {
    uploaded_filename: filename,
    visibility,
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    indexed: indexed.length,
    hektor_document_id: found.hektor_document_id,
    local_path: stored ? stored.local_path : null,
    storage_path: stored ? stored.storage_path : null,
    sync_job: syncJob,
  };
}

async function writeTempUploadFile(buffer, filename) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "hektor-console-upload-"));
  const safe = safeFilename(filename, "upload.bin");
  const filePath = path.join(tempDir, safe);
  fs.writeFileSync(filePath, buffer);
  return { tempDir, filePath };
}

async function uploadHektorPhotoWithPlaywright(job, dossier, payload, filePath, beforeCount) {
  const headless = String(process.env.CONSOLE_HEKTOR_HEADLESS || "true").toLowerCase() !== "false";
  const visible = payload.visible !== false;
  const selector = visible ? "#fileupload" : "#fileuploadHidden";
  const fileInputSelector = `input[type="file"]${selector}:not([disabled])`;
  const pageUrl = `${ADMIN_URL}?page=/mes-biens/mon-bien/photos&id=${encodeURIComponent(String(dossier.hektor_annonce_id))}`;
  let browser = null;
  try {
    browser = await chromium.launch(browserLaunchOptions({ headless }));
    const context = await browser.newContext({ storageState: STORAGE_STATE_PATH });
    const page = await context.newPage();
    const captured = [];
    page.on("requestfinished", async (request) => {
      const requestUrl = request.url();
      if (!/upload|vignette|photo|xmlrpc/i.test(requestUrl)) return;
      const response = await request.response().catch(() => null);
      captured.push({
        method: request.method(),
        url: requestUrl.replace(/\?.*$/, ""),
        status: response ? response.status() : null,
        postData: String(request.postData() || "").slice(0, 220),
      });
    });

    await page.goto(pageUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForSelector(fileInputSelector, { state: "attached", timeout: 45000 });
    await page.waitForFunction(() => typeof window.uploadPhotoInit === "function" || document.querySelector("#fileupload"), null, { timeout: 30000 }).catch(() => {});
    const input = page.locator(fileInputSelector).first();
    await input.setInputFiles(filePath);

    let entries = [];
    const deadline = Date.now() + 55000;
    while (Date.now() < deadline) {
      await page.waitForTimeout(3000);
      entries = await fetchConsolePhotoEntries(dossier.hektor_annonce_id).catch(() => []);
      if (entries.length > beforeCount) break;
    }

    await context.storageState({ path: STORAGE_STATE_PATH });
    return {
      entries,
      captured: captured.slice(-12),
    };
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    if (message.includes("Timeout") || message.includes("Navigation") || message.includes("ERR_ABORTED")) {
      throw new Error(`Session Hektor expiree ou upload photo non disponible: ${message.slice(0, 500)}`);
    }
    throw error;
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

async function handleUploadHektorPhoto(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });
  const tempPath = payload.temp_storage_path;
  const filename = safeFilename(payload.original_filename, "photo.jpg");
  const visible = payload.visible !== false;
  if (!tempPath) throw new Error("payload_json.temp_storage_path required");

  const temp = await downloadStorageObject(tempPath);
  const mimeType = String(payload.mime_type || temp.mimeType || "");
  if (mimeType && !/^image\/(jpeg|jpg|png|webp|gif)$/i.test(mimeType)) {
    throw new Error(`Type fichier photo refuse: ${mimeType}`);
  }

  const beforeEntries = await fetchConsolePhotoEntries(dossier.hektor_annonce_id);
  const local = await writeTempUploadFile(temp.buffer, filename);
  try {
    const uploadResult = await uploadHektorPhotoWithPlaywright(job, dossier, payload, local.filePath, beforeEntries.length);
    const entries = uploadResult.entries.length ? uploadResult.entries : await fetchConsolePhotoEntries(dossier.hektor_annonce_id);
    if (entries.length <= beforeEntries.length) {
      throw new Error(`Upload photo Hektor non confirme dans la galerie: ${filename}`);
    }
    const indexed = await upsertConsolePhotos(dossier, entries);
    await deleteStorageObject(tempPath);
    const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, dossier.hektor_annonce_id, {
      reason: "upload_hektor_photo",
      priority: 82,
    });
    return {
      uploaded_filename: filename,
      visibility: visible ? "visible" : "hidden",
      hektor_annonce_id: String(dossier.hektor_annonce_id),
      indexed: indexed.length,
      before_count: beforeEntries.length,
      after_count: entries.length,
      captured: uploadResult.captured,
      sync_job: syncJob,
    };
  } finally {
    try { fs.unlinkSync(local.filePath); } catch (_) {}
    try { fs.rmdirSync(local.tempDir); } catch (_) {}
  }
}

async function handleDeleteDocumentFromHektor(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });
  const documentId = payload.document_id;
  if (!documentId) throw new Error("payload_json.document_id required");
  const document = await loadConsoleDocumentById(documentId);
  if (String(document.hektor_annonce_id) !== String(dossier.hektor_annonce_id)) {
    throw new Error(`Document ${documentId} hors annonce ${dossier.hektor_annonce_id}`);
  }

  const metadata = document.metadata_json || {};
  const hektorUploadedDocumentId = metadata.hektor_uploaded_document_id || payload.hektor_uploaded_document_id;
  if (!hektorUploadedDocumentId) {
    throw new Error(`ID Hektor supprimable absent pour document ${document.document_name}`);
  }
  const visibility = document.visibility === "shared" ? "shared" : "private";
  const publicValue = visibility === "shared" ? "2" : "0";
  const id = encodeURIComponent(String(dossier.hektor_annonce_id));
  const publicKey = visibility === "shared" ? "partage" : "privee";
  const idContentDiv = visibility === "shared" ? "listDocUpload_partage" : "listDocUpload_privee";
  const listUrl = `${XMLRPC_URL}?mode=UploadedDocument_list&id_foreign=${id}&type=bien${publicValue === "2" ? "&public=2" : ""}&idContentDiv=${idContentDiv}&docType=${publicKey}`;

  const before = await hektorFetch(listUrl);
  if (!before.text.includes(`deleteUploadedDocument('${hektorUploadedDocumentId}'`) && !before.text.includes(`deleteUploadedDocument("${hektorUploadedDocumentId}"`)) {
    throw new Error(`Document Hektor ${hektorUploadedDocumentId} introuvable avant suppression`);
  }

  const deleteUrl = `${XMLRPC_URL}?mode=UploadedDocument_delete&id=${encodeURIComponent(String(hektorUploadedDocumentId))}&type=bien&isDocUploadPropsect=${publicValue}`;
  await hektorFetch(deleteUrl);
  await sleep(1500);

  const entries = await fetchConsoleDocumentEntries(dossier.hektor_annonce_id);
  const stillExists = entries.some((entry) => {
    return entry.hektor_uploaded_document_id === String(hektorUploadedDocumentId) || entry.hektor_document_id === document.hektor_document_id;
  });
  if (stillExists) throw new Error(`Suppression Hektor non confirmee pour ${document.document_name}`);

  if (document.storage_path) await deleteStorageObject(document.storage_path);
  const localPath = document.metadata_json && document.metadata_json.local_archive_path;
  if (isReadableFile(localPath)) fs.unlinkSync(localPath);
  await supabaseRequest(`app_console_document?id=eq.${encodeURIComponent(document.id)}`, {
    method: "DELETE",
    prefer: "return=minimal",
  });
  await upsertConsoleDocuments(dossier, entries);
  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, dossier.hektor_annonce_id, {
    reason: "delete_document_from_hektor",
    priority: 82,
  });

  return {
    deleted_document_id: document.id,
    deleted_name: document.document_name,
    hektor_uploaded_document_id: String(hektorUploadedDocumentId),
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    indexed: entries.length,
    sync_job: syncJob,
  };
}

function hektorProspectLinkedInHtml(html, contactId, annonceId) {
  const text = String(html || "");
  const contact = String(contactId || "").trim();
  const annonce = String(annonceId || "").trim();
  if (!contact || !annonce) return false;
  return (
    text.includes(`changeInfo${contact}_${annonce}`) ||
    text.includes(`changeDate${contact}_${annonce}`) ||
    text.includes(`degroupproprioForAnnonce('${contact}', '${annonce}'`) ||
    text.includes(`degroupproprioForAnnonce("${contact}", "${annonce}"`) ||
    text.includes(`navigateToProspect('${contact}'`) ||
    text.includes(`navigateToProspect("${contact}"`)
  );
}

function parseHektorLinkedMandantContactIds(html, annonceId) {
  const text = String(html || "");
  const annonce = String(annonceId || "").trim();
  const ids = new Set();
  const add = (value) => {
    const id = String(value || "").trim();
    if (/^\d+$/.test(id)) ids.add(id);
  };
  if (annonce) {
    const escapedAnnonce = annonce.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const directPattern = new RegExp(`(?:changeInfo|changeDate)(\\d+)_${escapedAnnonce}\\b`, "g");
    let match;
    while ((match = directPattern.exec(text))) add(match[1]);

    const ungroupPattern = /degroupproprioForAnnonce\(\s*['"](\d+)['"]\s*,\s*['"]?(\d+)/g;
    while ((match = ungroupPattern.exec(text))) {
      if (String(match[2]) === annonce) add(match[1]);
    }
  }

  const navigatePattern = /navigateToProspect\(\s*['"](\d+)['"]/g;
  let match;
  while ((match = navigatePattern.exec(text))) add(match[1]);

  return Array.from(ids);
}

async function fetchHektorProspectsList(hektorAnnonceId) {
  const id = encodeURIComponent(String(hektorAnnonceId));
  return hektorFetch(`${XMLRPC_URL}?mode=div_display_prospects_liste&id=${id}`);
}

function decodeHtmlEntities(value) {
  return String(value || "")
    .replace(/&quot;/g, "\"")
    .replace(/&#039;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

function attrValue(tag, name) {
  const match = String(tag || "").match(new RegExp(`${name}\\s*=\\s*([\"'])(.*?)\\1`, "i"));
  return match ? decodeHtmlEntities(match[2]) : null;
}

function extractHektorFormValues(html, groupName) {
  const values = new URLSearchParams();
  const source = String(html || "");
  const fieldRegex = /<textarea\b[^>]*>[\s\S]*?<\/textarea>|<select\b[^>]*>[\s\S]*?<\/select>|<input\b[^>]*>/gi;
  let match;
  while ((match = fieldRegex.exec(source))) {
    const field = match[0];
    const name = attrValue(field, "name");
    if (!name) continue;
    const fieldGroup = attrValue(field, "group") || attrValue(field, "data-group");
    if (groupName && fieldGroup && fieldGroup !== groupName) continue;
    const lower = field.toLowerCase();
    if (lower.startsWith("<input")) {
      const type = (attrValue(field, "type") || "text").toLowerCase();
      if (["button", "submit", "file", "image", "reset"].includes(type)) continue;
      if ((type === "radio" || type === "checkbox") && !/\bchecked\b/i.test(field)) continue;
      values.append(name, attrValue(field, "value") || "");
      continue;
    }
    if (lower.startsWith("<textarea")) {
      const body = (field.match(/<textarea\b[^>]*>([\s\S]*?)<\/textarea>/i) || [])[1] || "";
      values.append(name, decodeHtmlEntities(body));
      continue;
    }
    if (lower.startsWith("<select")) {
      const options = Array.from(field.matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((optionMatch) => optionMatch[0]);
      const selected = options.find((option) => /\bselected\b/i.test(option)) || options[0];
      if (!selected) continue;
      values.append(name, attrValue(selected, "value") || "");
    }
  }
  return values;
}

function extractWizardAnnonceId(html) {
  let source = String(html || "");
  try {
    const parsed = JSON.parse(source);
    if (typeof parsed === "string") source = parsed;
  } catch (_) {
    // Hektor sometimes returns raw HTML and sometimes a JSON-encoded HTML string.
  }
  const inputMatch = source.match(/<input\b[^>]*(?:id|name)\s*=\s*["']idannWizard["'][^>]*>/i);
  if (inputMatch) {
    const value = attrValue(inputMatch[0], "value");
    if (/^\d+$/.test(String(value || ""))) return String(value);
  }
  const patterns = [
    /\bidannWizard\b\s*[:=]\s*["']?(\d+)["']?/i,
    /\bidann\b\s*[:=]\s*["']?(\d+)["']?/i,
    /name\s*=\s*["']idannWizard["'][\s\S]{0,160}?value\s*=\s*["'](\d+)["']/i,
    /value\s*=\s*["'](\d+)["'][\s\S]{0,160}?name\s*=\s*["']idannWizard["']/i,
  ];
  for (const pattern of patterns) {
    const match = source.match(pattern);
    if (match && /^\d+$/.test(match[1])) return String(match[1]);
  }
  return null;
}

function mergeHektorFormValues(...sources) {
  const values = new URLSearchParams();
  for (const source of sources) {
    if (!source) continue;
    for (const [key, value] of source.entries()) {
      values.set(key, value);
    }
  }
  return values;
}

function payloadRawValue(payload, keys) {
  return firstDefined(payload || {}, keys);
}

function payloadTextValue(payload, keys) {
  const raw = payloadRawValue(payload, keys);
  if (raw === undefined || raw === null) return null;
  const text = String(raw).trim();
  return text || null;
}

function normalizeHektorWizardNumber(value, fieldName) {
  if (value === undefined || value === null || value === "") return null;
  const text = String(value).replace(/\s+/g, "").replace(",", ".").replace(/[^\d.-]/g, "").trim();
  if (!text) return null;
  if (!/^-?\d+(\.\d+)?$/.test(text)) throw new Error(`Champ numerique Hektor invalide: ${fieldName}`);
  return text;
}

function payloadNumberValue(payload, keys, fieldName) {
  return normalizeHektorWizardNumber(payloadRawValue(payload, keys), fieldName || keys[0]);
}

function payloadFrenchDateValue(payload, keys) {
  const raw = payloadRawValue(payload, keys);
  if (raw === undefined || raw === null || raw === "") return null;
  return normalizeOptionalFrenchDate(raw);
}

function setWizardText(values, target, payload, aliases) {
  const value = payloadTextValue(payload, aliases);
  if (value != null) values.set(target, value);
}

function setWizardNumber(values, target, payload, aliases) {
  const value = payloadNumberValue(payload, aliases, target);
  if (value != null) values.set(target, value);
}

function setWizardNumberIfPresent(values, target, payload, aliases) {
  if (values.has(target)) setWizardNumber(values, target, payload, aliases);
}

function setWizardTextIfPresent(values, target, payload, aliases) {
  if (values.has(target)) setWizardText(values, target, payload, aliases);
}

function setWizardDate(values, target, payload, aliases) {
  const value = payloadFrenchDateValue(payload, aliases);
  if (value != null) values.set(target, value);
}

function setWizardDateIfPresent(values, target, payload, aliases) {
  if (values.has(target)) setWizardDate(values, target, payload, aliases);
}

function setWizardDefault(values, target, value) {
  if (!values.has(target)) values.set(target, value);
}

function setWizardDefaultIfPresent(values, target, value) {
  if (values.has(target) && !values.get(target)) values.set(target, value);
}

function normalizeHektorSearchText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function textFromClass(html, className) {
  const pattern = new RegExp(`<[^>]*class=["'][^"']*\\b${className}\\b[^"']*["'][^>]*>([\\s\\S]*?)<\\/[^>]+>`, "i");
  const match = String(html || "").match(pattern);
  return match ? decodeHtmlEntities(match[1].replace(/<[^>]+>/g, "")).trim() : "";
}

function parseHektorLocalityCandidate(html, postalCode, city) {
  const source = String(html || "");
  const cityNeedle = normalizeHektorSearchText(city);
  const postalNeedle = String(postalCode || "").trim();
  const candidates = [];
  const liRegex = /<li\b[^>]*>[\s\S]*?<\/li>/gi;
  let match;
  while ((match = liRegex.exec(source))) {
    const block = match[0];
    const text = decodeHtmlEntities(block.replace(/<[^>]+>/g, " ")).replace(/\s+/g, " ").trim();
    const code = textFromClass(block, "code") || text.match(/\b\d{5}\b/)?.[0] || "";
    const name = textFromClass(block, "frontal") || textFromClass(block, "nameCode") || text;
    const idVille = textFromClass(block, "idVille") || attrValue(block, "idVille") || attrValue(block, "data-idville") || "";
    const idCode = textFromClass(block, "idVilleCode") || attrValue(block, "idCode") || attrValue(block, "data-idcode") || "";
    const latitude = textFromClass(block, "latitude") || attrValue(block, "data-latitude") || "";
    const longitude = textFromClass(block, "longitude") || attrValue(block, "data-longitude") || attrValue(block, "data-lng") || "";
    const normalizedText = normalizeHektorSearchText(`${name} ${text}`);
    let score = 0;
    if (postalNeedle && code === postalNeedle) score += 4;
    if (cityNeedle && normalizedText.includes(cityNeedle)) score += 3;
    if (idVille) score += 1;
    if (idCode) score += 1;
    if (score > 0) candidates.push({ score, code, name, idVille, idCode, latitude, longitude });
  }
  candidates.sort((a, b) => b.score - a.score);
  return candidates[0] || null;
}

async function resolveHektorPublicLocality(postalCode, city) {
  const cleanPostal = cleanString(postalCode);
  const cleanCity = cleanString(city);
  if (!cleanPostal && !cleanCity) return null;

  const body = new URLSearchParams({
    scope: cleanCity ? "ville" : "code",
    ville: cleanCity || cleanPostal,
    wellformed: "true",
    idpays: "1",
    country: "France",
    uCountry: "true",
  });
  if (cleanPostal) body.set("scopeCode", cleanPostal);
  if (cleanCity) body.set("scopeVille", cleanCity);

  let candidate = null;
  try {
    const response = await hektorFetch(`${ADMIN_URL}?call=ac_villes`, {
      method: "POST",
      body,
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        Referer: ADMIN_URL,
      },
      timeoutMs: 20000,
    });
    candidate = parseHektorLocalityCandidate(response.text, cleanPostal, cleanCity);
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    if (/Hektor 403|Session Hektor/i.test(message)) throw error;
    return null;
  }

  if (!candidate) return null;
  if (candidate.idVille && candidate.idCode && (!candidate.latitude || !candidate.longitude)) {
    try {
      const params = new URLSearchParams({
        mode: "villes-assocVilleFromHA",
        externalIdVille: candidate.idVille,
        externalIdCode: candidate.idCode,
      });
      const response = await hektorFetch(`${XMLRPC_URL}?${params.toString()}`, { timeoutMs: 20000 });
      const data = JSON.parse(response.text);
      if (data && !data.error) {
        return {
          code: cleanString(data.code) || candidate.code,
          name: cleanString(data.name) || candidate.name,
          idVille: cleanString(data.idVille) || cleanString(data.id) || candidate.idVille,
          idCode: cleanString(data.idCode) || candidate.idCode,
          latitude: cleanString(data.latitude) || candidate.latitude,
          longitude: cleanString(data.longitude) || candidate.longitude,
        };
      }
    } catch (error) {
      const message = error && error.message ? error.message : String(error);
      if (/Hektor 403|Session Hektor/i.test(message)) throw error;
    }
  }
  return candidate;
}

// Lot 2 : la localite du formulaire contact est TYPEE (champs caches idVille/idCode).
// Pousser seulement le texte ville/code ne suffit pas -> Hektor les renvoie vides (miroir
// annonce idVillepublique/idCodepublique). On resout la commune en identifiants Hektor et
// on aligne texte + id dans `values`. Best-effort : si la resolution echoue, on garde le
// comportement texte actuel (aucune regression).
async function applyContactLocalityIds(values, contact, job, contactId) {
  if (!contact || (!contact.city && !contact.postalCode)) return;
  let locality = null;
  try {
    locality = await resolveHektorPublicLocality(contact.postalCode, contact.city);
  } catch (_) {
    locality = null;
  }
  if (!locality || (!locality.idVille && !locality.idCode)) return;
  if (locality.idVille) values.set("idVille", locality.idVille);
  if (locality.idCode) values.set("idCode", locality.idCode);
  if (locality.name) values.set("ville", locality.name);
  if (locality.code) values.set("code", locality.code);
  if (job) {
    await logJob(job.id, "contact_locality_resolved", "running", "Localite contact resolue en identifiants Hektor", {
      hektor_contact_id: contactId ? String(contactId) : null,
      ville: locality.name, code: locality.code, idVille: locality.idVille, idCode: locality.idCode,
    });
  }
}

function exactHektorWizardFields(payload) {
  let source = null;
  if (payload && typeof payload === "object") {
    source = payload.hektor_wizard_fields || payload.wizard_fields || payload.wizardFields || null;
    const nested = payload.fields_json && typeof payload.fields_json === "object"
      ? payload.fields_json
      : payload.fields && typeof payload.fields === "object"
        ? payload.fields
        : null;
    if (!source && nested) {
      source = nested.hektor_wizard_fields || nested.wizard_fields || nested.wizardFields || null;
    }
  }
  return source && typeof source === "object" && !Array.isArray(source) ? source : {};
}

function textFromObjectKeys(source, keys) {
  if (!source || typeof source !== "object") return "";
  for (const key of keys) {
    const value = source[key];
    if (value === undefined || value === null) continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return "";
}

function hektorPayloadMergedFields(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const fieldsJson = source.fields_json && typeof source.fields_json === "object" ? source.fields_json : {};
  const fields = source.fields && typeof source.fields === "object" ? source.fields : {};
  return {
    ...source,
    ...fieldsJson,
    ...fields,
    ...exactHektorWizardFields(payload),
  };
}

const HEKTOR_PROFILE_ALIASES = new Set(["apartment", "house", "land", "garage", "building", "other"]);

function normalizeProfileText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function hektorPropertyProfileKindFromTypeId(value) {
  const id = String(value || "").trim();
  if (["5", "43", "44", "45"].includes(id)) return "land";
  if (["15", "16", "29"].includes(id)) return "garage";
  if (id === "21") return "building";
  if (["1", "10", "11", "17", "22", "25", "27", "28", "30", "39", "49"].includes(id)) return "house";
  if (["2", "4", "18", "26", "31", "41", "50"].includes(id)) return "apartment";
  return null;
}

function hektorPropertyProfileKindFromText(value) {
  const text = normalizeProfileText(value);
  if (!text) return null;
  if (text.includes("terrain")) return "land";
  if (text.includes("garage") || text.includes("parking") || text.includes("cave")) return "garage";
  if (text.includes("immeuble")) return "building";
  if (text.includes("maison") || text.includes("villa") || text.includes("propriete") || text.includes("ferme") || text.includes("mas") || text.includes("chalet")) return "house";
  if (text.includes("appartement") || text.includes("studio") || text.includes("duplex") || text.includes("loft")) return "apartment";
  return "other";
}

function resolveHektorPropertyProfile(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const direct = normalizeProfileText(source.property_profile || source.propertyProfile || source.type_profile || source.typeProfile || "");
  if (HEKTOR_PROFILE_ALIASES.has(direct)) return { kind: direct, explicit: true };
  const typeId = source.hektor_id_type || source.idType || source.id_type || source.idtype || source.idTypeWizard;
  const fromId = hektorPropertyProfileKindFromTypeId(typeId);
  if (fromId) return { kind: fromId, explicit: true };
  const fromText = hektorPropertyProfileKindFromText(source.property_type || source.type_bien || source.typeBien);
  if (fromText) return { kind: fromText, explicit: true };
  return { kind: "apartment", explicit: false };
}

const HEKTOR_WIZARD_COMMON_FIELDS = new Set([
  "prix", "PRIXNETVENDEUR", "NO_DOSSIER", "dateenr", "idpays", "NEGOCIATEUR", "codepublique", "villepublique",
  "idCodepublique", "idVillepublique", "idLocalitePrivee", "ADRESSE_COMPL", "adresse", "TRANSPORT",
  "PROXIMITE", "ENVIRONNEMENT", "latitude", "longitude", "diffusable", "titre", "corps",
  "_selecterHonoraires2", "_tauxHonoraire2", "_pourcentHonoraire2", "_detailHonoraire2",
  "_selecterHonoraires3", "_tauxHonoraire3", "_pourcentHonoraire3", "_detailHonoraire3",
  "masque", "ESTIMATION_MONTANT", "ESTIMATION_DATE", "TRAVAUX", "DEPOT_GARANTIE",
  "TAXE_FONCIERE", "TAXE_HABITATION", "CHARGES", "CHARGES_DETAIL", "Loc_EstimationLoyer",
  "Loc_ChargeLocative", "Loc_RendementBrut", "Loc_Occupation",
]);

const HEKTOR_COMPOSITION_LEGACY_FIELD_KEYS = new Set([
  "typePiece",
  "detailPiece",
  "etagePiece",
  "surfacePiece",
  "notePublique",
  "notePrivee",
  "noteInterAgence",
]);

const HEKTOR_CHAUFFAGE_FIELD_KEYS = new Set(["formatChauff", "typeChauff", "energieChauff"]);

const HEKTOR_WIZARD_FIELDS_BY_PROFILE = {
  apartment: new Set([
    "surfappart", "nbpieces", "NB_CHAMBRES", "NB_NIVEAUX", "GARAGE_BOX", "EXPOSITION", "vuee",
    "immeuble", "NB_SDB", "NB_SE", "NB_WC", "SURF_CARREZ",
    "SURF_SEJOUR", "CUISINE", "CUISINE_EQUIPEMENT", "floorState", "ETAGE", "DERNIER_ETAGE",
    "NB_ETAGES", "CAVE", "SURFACE_CAVE", "BALCON", "NB_BALCON", "SURFACE_BALCON",
    "TERRASSE", "NB_TERRASSE", "SURFACE_TERRASSE", "SURFACE_GARAGE", "NB_PARK_INT",
    "NB_PARK_EXT", "RESIDENCE", "TYPE_RESIDENCE", "formatChauff", "typeChauff",
    "energieChauff", "ASCENSEUR", "ACCES_HANDI", "climatisation", "climatisationspec",
    "EAU", "ASSAINISSEMENT", "DISTRIBUTION_EAU", "ENERGIE_EAU", "cheminee",
    "volets_elctriques", "gardien", "double_vitrage", "triple_vitrage", "cable",
    "porte_blindee", "interphone", "visiophone", "alarme", "digicode",
    "detecteur_fumee", "ANNEE_CONS", "etat_exterieur", "etat_interieur", "dpe_date",
    "dpe_non_concerne", "dpe_vierge", "isDpeAltitude", "dpe_cons", "dpe_ges",
    "valeurEnergieFinale", "dpe_couts_min", "dpe_couts_max", "dpe_annee_reference",
    "diagnostiqueur", "syndic", "diag_termites", "diag_termites_date", "diag_termites_commentaire", "diag_amiante",
    "diag_amiante_date", "diag_amiante_commentaire", "diag_electrique", "diag_electrique_date",
    "diag_electrique_commentaire", "diag_loi_carrez", "diag_loi_carrez_date",
    "diag_loi_carrez_commentaire", "diag_risques_nat_tech", "diag_risques_nat_tech_date",
    "diag_risques_nat_tech_commentaire", "diag_plomb", "diag_plomb_date",
    "diag_plomb_commentaire", "diag_gaz", "diag_gaz_date", "diag_gaz_commentaire",
    "diag_assainissement", "diag_assainissement_date", "diag_assainissement_commentaire", "clearing",
    "copropriete", "copropriete_lot", "copropriete_nb_lot", "copropriete_quote_part",
    "montant_fonds_travaux", "copropriete_plan_sauvegarde", "copropriete_statut_syndicat",
    "DISPO", "DATE_LIBER", "DATE_DISPO", "CLES", "moyens_visite",
  ]),
  house: new Set([
    "surfappart", "nbpieces", "NB_CHAMBRES", "NB_NIVEAUX", "surfterrain", "JARDIN",
    "JARDIN-", "SURFACE_JARDIN", "PISCINE", "PISCINE-", "GARAGE_BOX", "EXPOSITION", "vuee",
    "NB_SDB", "NB_SE", "NB_WC", "SURF_CARREZ", "SURF_SEJOUR", "CUISINE",
    "CUISINE_EQUIPEMENT", "MURS_MITOYENS", "NB_ETAGES", "CAVE", "SURFACE_CAVE",
    "TERRASSE", "NB_TERRASSE", "SURFACE_TERRASSE", "SURFACE_GARAGE", "NB_PARK_INT",
    "NB_PARK_EXT", "formatChauff", "typeChauff", "energieChauff", "ACCES_HANDI",
    "climatisation", "climatisationspec", "EAU", "ASSAINISSEMENT", "DISTRIBUTION_EAU",
    "ENERGIE_EAU", "cheminee", "volets_elctriques", "gardien", "double_vitrage",
    "triple_vitrage", "cable", "porte_blindee", "interphone", "visiophone", "alarme", "digicode",
    "detecteur_fumee", "ANNEE_CONS", "etat_exterieur", "etat_interieur", "dpe_date",
    "dpe_non_concerne", "dpe_vierge", "isDpeAltitude", "dpe_cons", "dpe_ges",
    "valeurEnergieFinale", "dpe_couts_min", "dpe_couts_max", "dpe_annee_reference",
    "diagnostiqueur", "syndic", "diag_termites", "diag_termites_date", "diag_termites_commentaire", "diag_amiante",
    "diag_amiante_date", "diag_amiante_commentaire", "diag_electrique", "diag_electrique_date",
    "diag_electrique_commentaire", "diag_risques_nat_tech", "diag_risques_nat_tech_date",
    "diag_risques_nat_tech_commentaire", "diag_plomb", "diag_plomb_date",
    "diag_plomb_commentaire", "diag_gaz", "diag_gaz_date", "diag_gaz_commentaire",
    "diag_assainissement", "diag_assainissement_date", "diag_assainissement_commentaire", "clearing",
    "DISPO", "DATE_LIBER", "DATE_DISPO", "CLES", "moyens_visite",
  ]),
  land: new Set([
    "surfterrain", "EAU", "ASSAINISSEMENT", "DISTRIBUTION_EAU", "terrain_constructible",
    "terrain_surface_constructible", "terrain_viabilise", "terrain_raccordement_eau",
    "terrain_raccordement_gaz", "terrain_raccordement_electricite", "terrain_raccordement_telephone",
    "diag_termites",
    "diag_termites_date", "diag_termites_commentaire", "diag_risques_nat_tech",
    "diag_risques_nat_tech_date", "diag_risques_nat_tech_commentaire", "diag_assainissement",
    "diag_assainissement_date", "diag_assainissement_commentaire", "DISPO", "DATE_LIBER",
    "DATE_DISPO", "CLES", "moyens_visite",
  ]),
  garage: new Set([
    "SURFACE_GARAGE", "CAVE", "SURFACE_CAVE", "GARAGE_BOX", "NB_PARK_INT", "NB_PARK_EXT",
    "ACCES_HANDI", "EAU", "CLES", "moyens_visite",
  ]),
  building: new Set([
    "surfappart", "immeuble", "SURF_CARREZ", "SURF_SEJOUR",
    "MURS_MITOYENS", "NB_ETAGES", "GARAGE_BOX", "SURFACE_GARAGE", "NB_PARK_INT",
    "NB_PARK_EXT", "RESIDENCE", "TYPE_RESIDENCE", "ASCENSEUR", "ACCES_HANDI", "EAU",
    "ASSAINISSEMENT", "DISTRIBUTION_EAU", "ANNEE_CONS", "etat_exterieur", "dpe_date",
    "dpe_cons", "dpe_ges", "diag_risques_nat_tech", "diag_risques_nat_tech_date",
    "diag_risques_nat_tech_commentaire", "copropriete", "copropriete_lot",
    "copropriete_nb_lot", "copropriete_quote_part", "montant_fonds_travaux", "DISPO",
    "DATE_LIBER", "DATE_DISPO", "CLES", "moyens_visite",
  ]),
  other: new Set([
    "surfappart", "SURF_CARREZ", "SURF_SEJOUR", "GARAGE_BOX", "SURFACE_GARAGE",
    "NB_PARK_INT", "NB_PARK_EXT", "EAU", "ASSAINISSEMENT", "ANNEE_CONS", "etat_exterieur",
    "dpe_cons", "dpe_ges", "diag_risques_nat_tech", "diag_risques_nat_tech_date",
    "diag_risques_nat_tech_commentaire", "CLES", "moyens_visite",
  ]),
};

function isHektorWizardFieldAllowedForPayload(payload, key) {
  if (HEKTOR_CHAUFFAGE_FIELD_KEYS.has(key)) return false;
  if (HEKTOR_COMPOSITION_LEGACY_FIELD_KEYS.has(key)) return false;
  const profile = resolveHektorPropertyProfile(payload);
  if (!profile.explicit) return true;
  if (HEKTOR_WIZARD_COMMON_FIELDS.has(key)) return true;
  const allowed = HEKTOR_WIZARD_FIELDS_BY_PROFILE[profile.kind] || HEKTOR_WIZARD_FIELDS_BY_PROFILE.apartment;
  return allowed.has(key);
}

const HEKTOR_UPDATE_COMMON_FIELDS = new Set([
  "title", "description", "address", "postal_code", "city", "building", "transport",
  "proximity", "environment", "latitude", "longitude", "price", "net_seller_price",
  "fees", "mandate_number", "mandate_type", "mandate_start_date", "mandate_end_date",
  "terrace",
]);

const HEKTOR_UPDATE_FIELDS_BY_PROFILE = {
  apartment: new Set([
    "surface", "carrez_surface", "room_count", "bedroom_count", "level_count", "floor",
    "bathroom_count", "shower_room_count", "wc_count", "kitchen", "exposure", "view",
    "interior_state", "exterior_state", "garden_surface", "terrace_count", "garage_count",
    "garage_surface", "parking_inside_count", "parking_outside_count", "dpe_value",
    "ges_value", "construction_year", "diagnostic_risk_comment", "copro_lots",
    "copro_charges", "copro_quote_part", "copro_works_fund",
  ]),
  house: new Set([
    "surface", "carrez_surface", "room_count", "bedroom_count", "level_count",
    "bathroom_count", "shower_room_count", "wc_count", "kitchen", "exposure", "view",
    "interior_state", "exterior_state", "land_surface", "garden_surface", "terrace_count",
    "garage_count", "garage_surface", "parking_inside_count", "parking_outside_count",
    "garden", "pool", "dpe_value", "ges_value", "construction_year", "diagnostic_risk_comment",
  ]),
  land: new Set([
    "land_surface", "exterior_state", "diagnostic_risk_comment",
  ]),
  garage: new Set([
    "garage_surface", "garage_count", "parking_inside_count", "parking_outside_count",
    "exterior_state",
  ]),
  building: new Set([
    "surface", "carrez_surface", "garage_count", "garage_surface", "parking_inside_count",
    "parking_outside_count", "exterior_state", "dpe_value", "ges_value", "construction_year",
    "diagnostic_risk_comment", "copro_lots", "copro_charges", "copro_quote_part",
    "copro_works_fund",
  ]),
  other: new Set([
    "surface", "carrez_surface", "garage_count", "garage_surface", "parking_inside_count",
    "parking_outside_count", "exterior_state", "dpe_value", "ges_value", "construction_year",
    "diagnostic_risk_comment",
  ]),
};

function filterHektorAnnonceUpdateFieldsForProfile(payload, clean) {
  const profile = resolveHektorPropertyProfile(payload);
  if (!profile.explicit) return clean;
  const allowed = HEKTOR_UPDATE_FIELDS_BY_PROFILE[profile.kind] || HEKTOR_UPDATE_FIELDS_BY_PROFILE.apartment;
  const filtered = {};
  for (const [key, value] of Object.entries(clean || {})) {
    if (HEKTOR_UPDATE_COMMON_FIELDS.has(key) || allowed.has(key)) filtered[key] = value;
  }
  return filtered;
}

const HEKTOR_WIZARD_UPDATE_GROUPS = [
  {
    group: "secteur",
    mode: "ihmChargeGroupe_Secteur",
    fields: new Set(["codepublique", "villepublique", "idCodepublique", "idVillepublique", "idLocalitePrivee", "ADRESSE_COMPL", "adresse", "immeuble", "TRANSPORT", "PROXIMITE", "ENVIRONNEMENT", "latitude", "longitude"]),
  },
  {
    group: "ag_interieur",
    mode: "ihmChargeGroupe",
    fields: new Set(["surfappart", "nbpieces", "NB_CHAMBRES", "NB_NIVEAUX", "NB_SDB", "SDB", "NB_SE", "SE", "SDE", "NB_WC", "WC", "SURF_CARREZ", "SURF_SEJOUR", "CUISINE", "CUISINE_EQUIPEMENT", "EXPOSITION", "vuee"]),
  },
  {
    group: "ag_exterieur",
    mode: "ihmChargeGroupe",
    fields: new Set(["JARDIN", "JARDIN-", "SURFACE_JARDIN", "MURS_MITOYENS", "floorState", "ETAGE", "DERNIER_ETAGE", "NB_ETAGES", "CAVE", "SURFACE_CAVE", "BALCON", "NB_BALCON", "SURFACE_BALCON", "TERRASSE", "NB_TERRASSE", "SURFACE_TERRASSE", "GARAGE_BOX", "SURFACE_GARAGE", "NB_PARK_INT", "NB_PARK_EXT", "PISCINE", "PISCINE-", "RESIDENCE", "TYPE_RESIDENCE"]),
  },
  {
    group: "terrain",
    mode: "ihmChargeGroupe",
    fields: new Set(["surfterrain", "terrain_constructible", "terrain_surface_constructible", "terrain_viabilise", "terrain_raccordement_eau", "terrain_raccordement_gaz", "terrain_raccordement_electricite", "terrain_raccordement_telephone"]),
  },
  {
    group: "equipements",
    mode: "ihmChargeGroupe",
    fields: new Set(["ASCENSEUR", "ACCES_HANDI", "climatisation", "climatisationspec", "EAU", "ASSAINISSEMENT", "DISTRIBUTION_EAU", "ENERGIE_EAU", "cheminee", "volets_elctriques", "gardien", "double_vitrage", "triple_vitrage", "cable", "porte_blindee", "interphone", "visiophone", "alarme", "digicode", "detecteur_fumee"]),
  },
  {
    group: "diagnostiques",
    mode: "ihmChargeGroupe",
    fields: new Set(["ANNEE_CONS", "ANNEE_CONSTRUCTION", "etat_exterieur", "ETAT_EXTERIEUR", "etat_interieur", "ETAT_INTERIEUR", "dpe_date", "dpe_non_concerne", "dpe_vierge", "isDpeAltitude", "dpe_cons", "DPE", "dpe_ges", "GES", "valeurEnergieFinale", "dpe_couts_min", "dpe_couts_max", "dpe_annee_reference", "diagnostiqueur", "syndic", "diag_termites", "diag_termites_date", "diag_termites_commentaire", "diag_amiante", "diag_amiante_date", "diag_amiante_commentaire", "diag_electrique", "diag_electrique_date", "diag_electrique_commentaire", "diag_loi_carrez", "diag_loi_carrez_date", "diag_loi_carrez_commentaire", "diag_risques_nat_tech", "diag_risques_nat_tech_date", "diag_risques_nat_tech_commentaire", "diag_plomb", "diag_plomb_date", "diag_plomb_commentaire", "diag_gaz", "diag_gaz_date", "diag_gaz_commentaire", "diag_assainissement", "diag_assainissement_date", "diag_assainissement_commentaire", "clearing"]),
  },
  {
    group: "copropriete",
    mode: "ihmChargeGroupe",
    fields: new Set(["copropriete", "copropriete_lot", "copropriete_nb_lot", "copropriete_quote_part", "montant_fonds_travaux", "copropriete_plan_sauvegarde", "copropriete_statut_syndicat"]),
  },
  {
    group: "organiser_visite",
    mode: "ihmChargeGroupe",
    fields: new Set(["CLES", "moyens_visite"]),
  },
  {
    group: "mandat_infofi",
    mode: "ihmChargeGroupe_MandatPrix",
    fields: new Set(["prix", "PRIXNETVENDEUR", "_selecterHonoraires2", "_tauxHonoraire2", "_pourcentHonoraire2", "_detailHonoraire2", "_selecterHonoraires3", "_tauxHonoraire3", "_pourcentHonoraire3", "_detailHonoraire3", "masque", "ESTIMATION_MONTANT", "ESTIMATION_DATE", "TRAVAUX", "DEPOT_GARANTIE", "TAXE_HABITATION", "TAXE_FONCIERE", "CHARGES", "CHARGES_DETAIL", "Loc_EstimationLoyer", "Loc_ChargeLocative", "Loc_RendementBrut", "Loc_Occupation"]),
  },
  {
    group: "mandat_mandatdispo",
    mode: "ihmChargeGroupe",
    fields: new Set(["NO_DOSSIER", "dateenr", "DISPO", "DATE_LIBER", "DATE_DISPO"]),
  },
];

function exactWizardCandidateKeys(key) {
  const candidates = [key];
  if (key.endsWith("-")) candidates.push(key.slice(0, -1));
  else candidates.push(`${key}-`);
  return candidates;
}

const HEKTOR_EXACT_SKIP_WHEN_FINANCIAL_LOCKED = new Set([
  "prix", "PRIXNETVENDEUR",
  "_selecterHonoraires2", "_tauxHonoraire2", "_pourcentHonoraire2", "_detailHonoraire2",
  "_selecterHonoraires3", "_tauxHonoraire3", "_pourcentHonoraire3", "_detailHonoraire3",
]);

const HEKTOR_OUI_NON_EXACT_FIELDS = new Set([
  "ASCENSEUR", "ACCES_HANDI", "climatisation", "cheminee", "volets_elctriques", "gardien",
  "double_vitrage", "triple_vitrage", "cable", "porte_blindee", "interphone", "visiophone",
  "alarme", "digicode", "detecteur_fumee", "DERNIER_ETAGE", "CAVE", "BALCON", "TERRASSE",
  "JARDIN", "JARDIN-", "PISCINE", "PISCINE-",
  "copropriete", "copropriete_plan_sauvegarde", "diag_termites", "diag_amiante",
  "diag_electrique", "diag_loi_carrez", "diag_risques_nat_tech", "clearing", "diag_plomb",
  "diag_gaz", "diag_assainissement", "terrain_constructible", "terrain_viabilise",
  "terrain_raccordement_eau", "terrain_raccordement_gaz", "terrain_raccordement_electricite",
  "terrain_raccordement_telephone",
]);

const HEKTOR_DATE_EXACT_FIELDS = new Set([
  "dpe_date",
  "diag_termites_date",
  "diag_amiante_date",
  "diag_electrique_date",
  "diag_loi_carrez_date",
  "diag_risques_nat_tech_date",
  "diag_plomb_date",
  "diag_gaz_date",
  "diag_assainissement_date",
  "ESTIMATION_DATE",
  "DATE_LIBER",
  "DATE_DISPO",
]);

function normalizeHektorFrenchDateValue(key, rawValue) {
  const text = String(rawValue == null ? "" : rawValue).trim();
  if (!text) return "";
  if (text === "00-00-0000") return text;
  const iso = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (iso) return `${iso[3]}-${iso[2]}-${iso[1]}`;
  const compactFr = text.match(/^(\d{2})(\d{2})(\d{4})$/);
  if (compactFr) return `${compactFr[1]}-${compactFr[2]}-${compactFr[3]}`;
  const fr = text.match(/^(\d{2})[/-](\d{2})[/-](\d{4})$/);
  if (fr) return `${fr[1]}-${fr[2]}-${fr[3]}`;
  throw new Error(`Date Hektor invalide pour ${key}: format attendu jj-mm-aaaa`);
}

function normalizeHektorOuiNonValue(rawValue) {
  const value = String(rawValue == null ? "" : rawValue).trim();
  if (!value) return "";
  const normalized = value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
  if (["OUI", "YES", "TRUE", "1", "ON"].includes(normalized)) return "OUI";
  if (["NON", "NO", "FALSE", "0", "OFF"].includes(normalized)) return "NON";
  return value;
}

function normalizeHektorExactWizardUpdateValue(key, rawValue) {
  const value = String(rawValue == null ? "" : rawValue).trim();
  if (!value) return "";
  if (HEKTOR_DATE_EXACT_FIELDS.has(key)) return normalizeHektorFrenchDateValue(key, value);
  if (HEKTOR_OUI_NON_EXACT_FIELDS.has(key)) return normalizeHektorOuiNonValue(value);
  if (key !== "DISPO") return value;
  const normalized = value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
  if (["OUI", "YES", "TRUE", "1", "IMMEDIAT", "IMMEDIATE", "LIBRE", "LIB"].includes(normalized)) return "OUI";
  if (["NON", "NO", "FALSE", "0", "DIFFERE", "DIFFEREE", "DATE", "OCCUPE", "OCCUPEE", "LOUE", "LOUEE"].includes(normalized)) return "NON";
  return value;
}

function inferHektorFloorStateValue(value) {
  const text = String(value == null ? "" : value).replace(",", ".").trim();
  if (!text) return "";
  const numeric = Number(text);
  if (Number.isFinite(numeric) && numeric === 0) return "GROUND_FLOOR";
  return "OTHER_FLOOR";
}

function buildExactWizardGroupUpdates(payload, options = {}) {
  const exact = exactHektorWizardFields(payload);
  const protectedKeys = new Set(["mode", "step", "idann", "offredem", "programme_neuf", "isInterkabActive", "enabled", "content_pdf", "mdn_id", "diffusable", "titre", "corps"]);
  const grouped = new Map();

  for (const [rawKey, rawValue] of Object.entries(exact)) {
    const key = String(rawKey || "").trim();
    if (!key || protectedKeys.has(key)) continue;
    if (options.skipFinancial && HEKTOR_EXACT_SKIP_WHEN_FINANCIAL_LOCKED.has(key)) continue;
    if (!/^[A-Za-z0-9_[\]-]+$/.test(key)) continue;
    if (!isHektorWizardFieldAllowedForPayload(payload, key)) continue;
    if (rawValue === undefined || rawValue === null) continue;
    const value = normalizeHektorExactWizardUpdateValue(key, rawValue);
    if (!value) continue;
    const candidates = exactWizardCandidateKeys(key);
    const config = HEKTOR_WIZARD_UPDATE_GROUPS.find((item) => candidates.some((candidate) => item.fields.has(candidate)));
    if (!config) continue;
    const current = grouped.get(config.group) || { mode: config.mode, fields: {} };
    current.fields[key] = fieldSpec(value, candidates);
    grouped.set(config.group, current);
  }

  if (!Object.prototype.hasOwnProperty.call(exact, "floorState") && Object.prototype.hasOwnProperty.call(exact, "ETAGE")) {
    const floorState = inferHektorFloorStateValue(normalizeHektorExactWizardUpdateValue("ETAGE", exact.ETAGE));
    if (floorState && isHektorWizardFieldAllowedForPayload(payload, "floorState")) {
      const config = HEKTOR_WIZARD_UPDATE_GROUPS.find((item) => item.group === "ag_exterieur");
      if (config) {
        const current = grouped.get(config.group) || { mode: config.mode, fields: {} };
        current.fields.floorState = fieldSpec(floorState, ["floorState"]);
        grouped.set(config.group, current);
      }
    }
  }

  const profile = resolveHektorPropertyProfile(payload);
  if (profile.kind === "land") {
    const config = HEKTOR_WIZARD_UPDATE_GROUPS.find((item) => item.group === "terrain");
    if (config) {
      const current = grouped.get(config.group) || { mode: config.mode, fields: {} };
      const addTerrainField = (target, rawValue) => {
        if (current.fields[target]) return;
        const value = normalizeHektorOuiNonValue(rawValue);
        if (!value || !isHektorWizardFieldAllowedForPayload(payload, target)) return;
        current.fields[target] = fieldSpec(value, [target]);
      };
      if (!Object.prototype.hasOwnProperty.call(exact, "terrain_raccordement_eau") && Object.prototype.hasOwnProperty.call(exact, "EAU")) {
        addTerrainField("terrain_raccordement_eau", String(exact.EAU || "").toUpperCase() === "SANS" ? "NON" : "OUI");
      }
      if (!Object.prototype.hasOwnProperty.call(exact, "terrain_viabilise") && (
        Object.prototype.hasOwnProperty.call(exact, "EAU")
        || Object.prototype.hasOwnProperty.call(exact, "ASSAINISSEMENT")
        || Object.prototype.hasOwnProperty.call(exact, "DISTRIBUTION_EAU")
      )) {
        addTerrainField("terrain_viabilise", "OUI");
      }
      if (Object.keys(current.fields).length) grouped.set(config.group, current);
    }
  }

  return Array.from(grouped.entries()).map(([group, config]) => ({ group, mode: config.mode, fields: config.fields }));
}

function stripHektorSpecialWizardFields(body) {
  for (const key of HEKTOR_CHAUFFAGE_FIELD_KEYS) body.delete(key);
}

function applyExactHektorWizardFields(body, payload, step) {
  stripHektorSpecialWizardFields(body);
  const exact = exactHektorWizardFields(payload);
  if (!Object.keys(exact).length) return [];
  const applied = [];
  const protectedKeys = new Set(["mode", "step", "idann", "offredem", "programme_neuf", "isInterkabActive", "enabled", "content_pdf", "mdn_id"]);
  for (const [rawKey, rawValue] of Object.entries(exact)) {
    const key = String(rawKey || "").trim();
    if (!key || protectedKeys.has(key)) continue;
    if (!/^[A-Za-z0-9_[\]-]+$/.test(key)) continue;
    if (!isHektorWizardFieldAllowedForPayload(payload, key)) continue;
    if (key === "diffusable") {
      if (Number(step) === 7) {
        body.set("diffusable", "0");
        applied.push(key);
      }
      continue;
    }
    if (rawValue === undefined || rawValue === null) continue;
    const value = String(rawValue).trim();
    if (!value) continue;
    body.set(key, value);
    applied.push(key);
  }
  stripHektorSpecialWizardFields(body);
  return applied;
}

function wizardStepBaseBody(idannWizard, step, meta, extractedValues = null) {
  const body = mergeHektorFormValues(extractedValues);
  body.set("mode", "annonce-createBien-Ajx_Bien_wizardStepNew");
  body.set("step", String(step));
  body.set("offredem", String(meta.offredem));
  body.set("idann", String(idannWizard));
  body.set("programme_neuf", String(meta.programmeNeuf));
  body.set("isInterkabActive", "undefined");
  return body;
}

function buildWizardStep2Body(idannWizard, meta, html, payload) {
  const values = mergeHektorFormValues(
    extractHektorFormValues(html, "wizard_obligatoire"),
    extractHektorFormValues(html, "wizard_obligatoire_proposed"),
  );
  const body = wizardStepBaseBody(idannWizard, 2, meta, values);
  body.set("idMandant", "0");
  body.set("statusAnnonceWizard", String(meta.statutAnnonce));
  body.set("idtype", String(meta.idType));
  body.set("offredem", String(meta.offredem));
  setWizardDefault(body, "idpays", "1");
  setWizardDefault(body, "prix", "0");
  setWizardDefault(body, "PRIXNETVENDEUR", "0");
  for (const field of ["surfappart", "surfterrain", "SURFACE_GARAGE", "nbpieces", "NB_CHAMBRES", "NB_NIVEAUX", "GARAGE_BOX"]) {
    setWizardDefaultIfPresent(body, field, "0");
  }
  setWizardNumber(body, "prix", payload, ["price", "prix"]);
  setWizardNumber(body, "PRIXNETVENDEUR", payload, ["net_seller_price", "netSellerPrice", "prix_net_vendeur"]);
  setWizardNumberIfPresent(body, "surfappart", payload, ["surface", "surfappart", "surface_habitable"]);
  setWizardNumberIfPresent(body, "surfterrain", payload, ["land_surface", "landSurface", "surfterrain", "surface_terrain"]);
  setWizardNumberIfPresent(body, "SURFACE_GARAGE", payload, ["garage_surface", "garageSurface", "SURFACE_GARAGE"]);
  setWizardNumberIfPresent(body, "nbpieces", payload, ["room_count", "roomCount", "nbpieces", "pieces"]);
  setWizardNumberIfPresent(body, "NB_CHAMBRES", payload, ["bedroom_count", "bedroomCount", "NB_CHAMBRES", "chambres"]);
  setWizardNumberIfPresent(body, "NB_NIVEAUX", payload, ["level_count", "levelCount", "NB_NIVEAUX", "niveaux"]);
  setWizardNumberIfPresent(body, "GARAGE_BOX", payload, ["garage_count", "garageCount", "GARAGE_BOX"]);
  setWizardTextIfPresent(body, "JARDIN-", payload, ["garden", "jardin", "JARDIN", "JARDIN-"]);
  setWizardTextIfPresent(body, "PISCINE-", payload, ["pool", "piscine", "PISCINE", "PISCINE-"]);
  setWizardTextIfPresent(body, "EXPOSITION", payload, ["exposure", "exposition", "EXPOSITION"]);
  setWizardTextIfPresent(body, "vuee", payload, ["view", "vue", "vuee"]);
  setWizardText(body, "NO_DOSSIER", payload, ["folder_number", "folderNumber", "no_dossier", "NO_DOSSIER"]);
  const formNegotiatorId = payloadTextValue(payload, ["hektor_negociator_form_id", "negociator_form_id", "NEGOCIATEUR"]);
  if (formNegotiatorId && !body.has("NEGOCIATEUR")) body.set("NEGOCIATEUR", formNegotiatorId);
  applyExactHektorWizardFields(body, payload, 2);
  return body;
}

async function buildWizardStep4Body(idannWizard, meta, html, payload) {
  const values = mergeHektorFormValues(
    extractHektorFormValues(html, "wizard_secteur"),
    extractHektorFormValues(html, "wizard_obligatoire"),
  );
  const body = wizardStepBaseBody(idannWizard, 4, meta, values);
  setWizardDefault(body, "idpays", "1");
  setWizardDefault(body, "latitude", "0.000000000");
  setWizardDefault(body, "longitude", "0.000000000");
  setWizardDefault(body, "fromWizardSecteur", "1");
  const postalCode = payloadTextValue(payload, ["postal_code", "postalCode", "code_postal", "codepublique"]);
  const city = payloadTextValue(payload, ["city", "ville", "villepublique"]);
  const address = payloadTextValue(payload, ["address", "adresse", "private_address", "adresse_privee"]);
  if (postalCode) body.set("codepublique", postalCode);
  if (city) body.set("villepublique", city);
  if (address) body.set("ADRESSE_COMPL", address);
  const locality = await resolveHektorPublicLocality(postalCode, city);
  if (locality) {
    if (locality.code && !postalCode) body.set("codepublique", locality.code);
    if (locality.name && !city) body.set("villepublique", locality.name);
    if (locality.idCode) body.set("idCodepublique", locality.idCode);
    if (locality.idVille) body.set("idVillepublique", locality.idVille);
    if (locality.latitude) body.set("latitude", locality.latitude);
    if (locality.longitude) body.set("longitude", locality.longitude);
  }
  setWizardText(body, "immeuble", payload, ["building", "immeuble"]);
  setWizardText(body, "TRANSPORT", payload, ["transport", "TRANSPORT"]);
  setWizardText(body, "PROXIMITE", payload, ["proximity", "proximite", "PROXIMITE"]);
  setWizardText(body, "ENVIRONNEMENT", payload, ["environment", "environnement", "ENVIRONNEMENT"]);
  setWizardText(body, "idCodepublique", payload, ["idCodepublique", "id_codepublique", "hektor_public_postal_code_id"]);
  setWizardText(body, "idVillepublique", payload, ["idVillepublique", "id_villepublique", "hektor_public_city_id"]);
  setWizardText(body, "idLocalitePrivee", payload, ["idLocalitePrivee", "id_localite_privee", "hektor_private_locality_id"]);
  setWizardNumber(body, "latitude", payload, ["latitude", "lat"]);
  setWizardNumber(body, "longitude", payload, ["longitude", "lng", "lon"]);
  applyExactHektorWizardFields(body, payload, 4);
  return body;
}

function buildWizardStep3Body(idannWizard, meta, html, payload) {
  const body = wizardStepBaseBody(idannWizard, 3, meta, null);
  applyExactHektorWizardFields(body, payload, 3);
  return body;
}

function buildWizardStep5Body(idannWizard, meta, html, payload) {
  const body = wizardStepBaseBody(idannWizard, 5, meta, null);
  applyExactHektorWizardFields(body, payload, 5);
  return body;
}

function buildWizardStep6Body(idannWizard, meta, html, payload) {
  const values = mergeHektorFormValues(
    extractHektorFormValues(html, "ag_interieur"),
    extractHektorFormValues(html, "ag_exterieur"),
    extractHektorFormValues(html, "equipements"),
    extractHektorFormValues(html, "diagnostiques"),
    extractHektorFormValues(html, "copropriete"),
    extractHektorFormValues(html, "mandat_mandatdispo"),
    extractHektorFormValues(html, "organiser_visite"),
  );
  const body = wizardStepBaseBody(idannWizard, 6, meta, values);
  const zeroDefaults = [
    "NB_CHAMBRES", "NB_SDB", "NB_SE", "NB_WC", "SURF_CARREZ", "SURF_SEJOUR",
    "ETAGE", "NB_ETAGES", "SURFACE_CAVE", "NB_BALCON", "SURFACE_BALCON",
    "NB_TERRASSE", "SURFACE_TERRASSE", "GARAGE_BOX", "SURFACE_GARAGE",
    "NB_PARK_INT", "NB_PARK_EXT", "ANNEE_CONS", "dpe_cons", "dpe_ges",
    "valeurEnergieFinale", "dpe_couts_min", "dpe_couts_max", "dpe_annee_reference",
    "copropriete_nb_lot", "copropriete_quote_part", "montant_fonds_travaux",
  ];
  for (const field of zeroDefaults) setWizardDefaultIfPresent(body, field, "0");
  for (const field of ["dpe_date", "diag_termites_date", "diag_amiante_date", "diag_electrique_date", "diag_loi_carrez_date", "diag_risques_nat_tech_date", "diag_plomb_date", "diag_gaz_date", "diag_assainissement_date"]) {
    setWizardDefaultIfPresent(body, field, "00-00-0000");
  }
  setWizardNumberIfPresent(body, "NB_CHAMBRES", payload, ["bedroom_count", "bedroomCount", "NB_CHAMBRES"]);
  setWizardNumberIfPresent(body, "NB_SDB", payload, ["bathroom_count", "bathroomCount", "NB_SDB", "sdb"]);
  setWizardNumberIfPresent(body, "NB_SE", payload, ["shower_room_count", "showerRoomCount", "NB_SE", "salle_eau"]);
  setWizardNumberIfPresent(body, "NB_WC", payload, ["wc_count", "wcCount", "NB_WC", "wc"]);
  setWizardNumberIfPresent(body, "SURF_CARREZ", payload, ["carrez_surface", "carrezSurface", "SURF_CARREZ"]);
  setWizardNumberIfPresent(body, "SURF_SEJOUR", payload, ["living_surface", "livingSurface", "SURF_SEJOUR"]);
  setWizardTextIfPresent(body, "CUISINE", payload, ["kitchen", "cuisine", "CUISINE"]);
  setWizardTextIfPresent(body, "CUISINE_EQUIPEMENT", payload, ["kitchen_equipment", "kitchenEquipment", "CUISINE_EQUIPEMENT"]);
  setWizardTextIfPresent(body, "EXPOSITION", payload, ["exposure", "exposition", "EXPOSITION"]);
  setWizardTextIfPresent(body, "vuee", payload, ["view", "vue", "vuee"]);
  setWizardTextIfPresent(body, "etat_interieur", payload, ["interior_state", "interiorState", "etat_interieur"]);
  setWizardTextIfPresent(body, "etat_exterieur", payload, ["exterior_state", "exteriorState", "etat_exterieur"]);
  setWizardNumberIfPresent(body, "ETAGE", payload, ["floor", "etage", "ETAGE"]);
  setWizardNumberIfPresent(body, "NB_ETAGES", payload, ["floor_count", "floorCount", "NB_ETAGES"]);
  setWizardNumberIfPresent(body, "NB_BALCON", payload, ["balcony_count", "balconyCount", "NB_BALCON"]);
  setWizardNumberIfPresent(body, "SURFACE_BALCON", payload, ["balcony_surface", "balconySurface", "SURFACE_BALCON"]);
  setWizardNumberIfPresent(body, "NB_TERRASSE", payload, ["terrace_count", "terraceCount", "NB_TERRASSE"]);
  setWizardNumberIfPresent(body, "SURFACE_TERRASSE", payload, ["terrace_surface", "terraceSurface", "SURFACE_TERRASSE"]);
  setWizardNumberIfPresent(body, "GARAGE_BOX", payload, ["garage_count", "garageCount", "GARAGE_BOX"]);
  setWizardNumberIfPresent(body, "SURFACE_GARAGE", payload, ["garage_surface", "garageSurface", "SURFACE_GARAGE"]);
  setWizardNumberIfPresent(body, "NB_PARK_INT", payload, ["parking_inside_count", "parkingInsideCount", "NB_PARK_INT"]);
  setWizardNumberIfPresent(body, "NB_PARK_EXT", payload, ["parking_outside_count", "parkingOutsideCount", "NB_PARK_EXT"]);
  setWizardTextIfPresent(body, "ASCENSEUR", payload, ["elevator", "ascenseur", "ASCENSEUR"]);
  setWizardTextIfPresent(body, "ACCES_HANDI", payload, ["handicap_access", "handicapAccess", "ACCES_HANDI"]);
  setWizardTextIfPresent(body, "climatisation", payload, ["air_conditioning", "airConditioning", "climatisation"]);
  setWizardTextIfPresent(body, "double_vitrage", payload, ["double_glazing", "doubleGlazing", "double_vitrage"]);
  setWizardTextIfPresent(body, "interphone", payload, ["intercom", "interphone"]);
  setWizardTextIfPresent(body, "visiophone", payload, ["videophone", "visiophone"]);
  setWizardTextIfPresent(body, "digicode", payload, ["digicode"]);
  setWizardNumberIfPresent(body, "ANNEE_CONS", payload, ["construction_year", "constructionYear", "ANNEE_CONS"]);
  setWizardNumberIfPresent(body, "dpe_cons", payload, ["dpe_value", "dpeValue", "dpe_cons"]);
  setWizardNumberIfPresent(body, "dpe_ges", payload, ["ges_value", "gesValue", "dpe_ges"]);
  setWizardDateIfPresent(body, "dpe_date", payload, ["dpe_date", "dpeDate"]);
  setWizardTextIfPresent(body, "dpe_non_concerne", payload, ["dpe_non_concerne", "dpeNotApplicable", "chk_dpe_non_concerne"]);
  setWizardTextIfPresent(body, "dpe_vierge", payload, ["dpe_vierge", "dpeBlank", "chk_dpe_vierge"]);
  setWizardTextIfPresent(body, "isDpeAltitude", payload, ["isDpeAltitude", "dpeAltitude", "chk_isDpeAltitude"]);
  setWizardTextIfPresent(body, "diagnostiqueur", payload, ["diagnostician", "diagnostiqueur"]);
  setWizardTextIfPresent(body, "diag_risques_nat_tech_commentaire", payload, ["diagnostic_risk_comment", "diagnosticRiskComment", "diag_risques_nat_tech_commentaire"]);
  setWizardTextIfPresent(body, "syndic", payload, ["syndic"]);
  setWizardTextIfPresent(body, "copropriete", payload, ["copropriete", "copro"]);
  setWizardNumberIfPresent(body, "copropriete_nb_lot", payload, ["copro_lots", "coproLots", "copropriete_nb_lot"]);
  setWizardNumberIfPresent(body, "copropriete_quote_part", payload, ["copro_quote_part", "coproQuotePart", "copropriete_quote_part"]);
  setWizardNumberIfPresent(body, "montant_fonds_travaux", payload, ["copro_works_fund", "coproWorksFund", "montant_fonds_travaux"]);
  applyExactHektorWizardFields(body, payload, 6);
  return body;
}

function buildWizardStep7Body(idannWizard, meta, html, payload) {
  const values = mergeHektorFormValues(
    extractHektorFormValues(html, "wizard_titleDescription"),
    extractHektorFormValues(html, "wizard_Mandant_BienInsert"),
    extractHektorFormValues(html, "mandat_infofi"),
    extractHektorFormValues(html, "mandat_investissementloc"),
  );
  const body = wizardStepBaseBody(idannWizard, 7, meta, values);
  setWizardDefaultIfPresent(body, "PRIXNETVENDEUR", "0");
  setWizardDefaultIfPresent(body, "prix", "0");
  setWizardDefaultIfPresent(body, "_selecterHonoraires2", "NON");
  setWizardDefaultIfPresent(body, "_tauxHonoraire2", "0");
  setWizardDefaultIfPresent(body, "_selecterHonoraires3", "NON");
  setWizardDefaultIfPresent(body, "_tauxHonoraire3", "0");
  setWizardDefaultIfPresent(body, "ESTIMATION_MONTANT", "0");
  setWizardDefaultIfPresent(body, "ESTIMATION_DATE", "00-00-0000");
  setWizardDefaultIfPresent(body, "DEPOT_GARANTIE", "0");
  setWizardDefaultIfPresent(body, "TAXE_HABITATION", "0");
  setWizardDefaultIfPresent(body, "TAXE_FONCIERE", "0");
  setWizardDefaultIfPresent(body, "CHARGES", "0");
  setWizardTextIfPresent(body, "titre", payload, ["title", "titre"]);
  setWizardTextIfPresent(body, "corps", payload, ["description", "corps"]);
  setWizardNumberIfPresent(body, "PRIXNETVENDEUR", payload, ["net_seller_price", "netSellerPrice", "prix_net_vendeur"]);
  setWizardNumberIfPresent(body, "prix", payload, ["price", "prix"]);
  setWizardNumberIfPresent(body, "ESTIMATION_MONTANT", payload, ["estimation_amount", "estimationAmount", "ESTIMATION_MONTANT"]);
  setWizardDateIfPresent(body, "ESTIMATION_DATE", payload, ["estimation_date", "estimationDate", "ESTIMATION_DATE"]);
  setWizardNumberIfPresent(body, "DEPOT_GARANTIE", payload, ["deposit", "depot_garantie", "DEPOT_GARANTIE"]);
  setWizardNumberIfPresent(body, "TAXE_HABITATION", payload, ["housing_tax", "housingTax", "TAXE_HABITATION"]);
  setWizardNumberIfPresent(body, "TAXE_FONCIERE", payload, ["property_tax", "propertyTax", "TAXE_FONCIERE"]);
  setWizardNumberIfPresent(body, "CHARGES", payload, ["copro_charges", "coproCharges", "charges", "CHARGES"]);
  setWizardTextIfPresent(body, "TRAVAUX", payload, ["works", "travaux", "TRAVAUX"]);
  setWizardTextIfPresent(body, "CHARGES_DETAIL", payload, ["charges_detail", "chargesDetail", "CHARGES_DETAIL"]);
  setWizardNumberIfPresent(body, "Loc_EstimationLoyer", payload, ["rent_estimate", "rentEstimate", "Loc_EstimationLoyer"]);
  setWizardNumberIfPresent(body, "Loc_ChargeLocative", payload, ["rent_charges", "rentCharges", "Loc_ChargeLocative"]);
  setWizardTextIfPresent(body, "Loc_Occupation", payload, ["rental_occupation", "rentalOccupation", "Loc_Occupation"]);
  applyExactHektorWizardFields(body, payload, 7);
  body.set("diffusable", "0");
  return body;
}

async function fetchHektorWizardBienHtml(fetcher, idannWizard, meta) {
  const wizardBody = new URLSearchParams({
    mode: "ajoutebien_wizardBien",
    offredem: String(meta.offredem),
    idType: String(meta.idType),
    statutAnnonce: String(meta.statutAnnonce),
    idann: String(idannWizard),
    programme_neuf: String(meta.programmeNeuf),
  });
  const response = await fetcher(XMLRPC_URL, {
    method: "POST",
    body: wizardBody,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/ajouter-un-nouveau-bien`,
    },
    timeoutMs: 60000,
  });
  return response.text;
}

async function postHektorWizardCreateStep(job, fetcher, idannWizard, meta, step, body) {
  await logJob(job.id, "hektor_annonce_wizard", "running", `Sauvegarde page Hektor ${step} du wizard`, {
    hektor_annonce_id: String(idannWizard),
    step,
    fields: Array.from(body.keys()).filter((key) => !["mode", "step", "idann", "offredem", "programme_neuf", "isInterkabActive"].includes(key)).slice(0, 80),
  });

  await fetcher(XMLRPC_URL, {
    method: "POST",
    body: new URLSearchParams({
      mode: "deepFlowReality-setDeepCache",
      idann: String(idannWizard),
      step: String(step),
    }),
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/ajouter-un-nouveau-bien`,
    },
    timeoutMs: 30000,
  });

  const response = await fetcher(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/ajouter-un-nouveau-bien`,
    },
    timeoutMs: 60000,
  });
  return {
    method: "POST",
    mode: "annonce-createBien-Ajx_Bien_wizardStepNew",
    step,
    status: response.response.status,
    bytes: response.buffer.length,
  };
}

async function applyHektorCreateWizardFields(job, fetcher, idannWizard, meta, payload, firstWizardHtml) {
  const captured = [];
  let html = firstWizardHtml;
  const steps = [
    { step: 2, build: buildWizardStep2Body },
    { step: 3, build: buildWizardStep3Body },
    { step: 4, build: buildWizardStep4Body },
    { step: 5, build: buildWizardStep5Body },
    { step: 6, build: buildWizardStep6Body },
    { step: 7, build: buildWizardStep7Body },
  ];

  for (const item of steps) {
    const body = await item.build(idannWizard, meta, html, payload);
    const result = await postHektorWizardCreateStep(job, fetcher, idannWizard, meta, item.step, body);
    captured.push(result);
    if (item.step !== 7) {
      html = await fetchHektorWizardBienHtml(fetcher, idannWizard, meta);
    }
  }

  await logJob(job.id, "hektor_annonce_wizard", "done", "Pages Hektor du wizard sauvegardees sans diffusion", {
    hektor_annonce_id: String(idannWizard),
    steps: captured.map((item) => item.step),
  });
  return captured;
}

async function postHektorMefUpdate(job, annonceId, groupName, readMode, overrides) {
  const id = encodeURIComponent(String(annonceId));
  const group = encodeURIComponent(groupName);
  const html = await hektorFetch(`${XMLRPC_URL}?mode=${readMode}&idAnnonce=${id}&group=${group}&consultMode=editer&ajax=ajax`, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${id}`,
    },
  });
  const values = extractHektorFormValues(html.text, groupName);
  if (groupName === "equipements") stripHektorSpecialWizardFields(values);
  const applied = [];
  const skipped = [];
  for (const [key, rawSpec] of Object.entries(overrides)) {
    const spec = rawSpec && typeof rawSpec === "object" && Object.prototype.hasOwnProperty.call(rawSpec, "value")
      ? rawSpec
      : { value: rawSpec, candidates: [key] };
    if (spec.value == null) continue;
    const candidates = Array.isArray(spec.candidates) && spec.candidates.length ? spec.candidates : [key];
    const targetKey = candidates.find((candidate) => values.has(candidate));
    if (!targetKey) {
      skipped.push({ field: key, candidates });
      continue;
    }
    values.set(targetKey, String(spec.value));
    applied.push({ field: key, target: targetKey });
  }
  if (!applied.length) {
    await logJob(job.id, "hektor_annonce_update", "running", `Aucun champ reconnu dans groupe ${groupName}`, {
      hektor_annonce_id: String(annonceId),
      group: groupName,
      requested_fields: Object.keys(overrides),
      skipped,
    });
    return null;
  }
  values.set("mode", "update_annonce_MEF");
  values.set("idann", String(annonceId));
  values.set("MEFgroup", groupName);

  await logJob(job.id, "hektor_annonce_update", "running", `Sauvegarde groupe ${groupName}`, {
    hektor_annonce_id: String(annonceId),
    group: groupName,
    fields: applied.map((item) => item.field),
    targets: applied,
    skipped,
  });

  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: values,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${id}`,
    },
  });
  let parsed = null;
  try {
    parsed = JSON.parse(response.text);
  } catch (_) {
    parsed = null;
  }
  if (parsed && String(parsed.result) !== "1") {
    if (groupName === "mandat_infofi" && /Credential Error/i.test(response.text)) {
      throw new Error("Hektor refuse la modification directe du prix ou des champs financiers sur cette fiche. Utilise le workflow mandat/statut adapte ou modifie ces champs directement dans Hektor.");
    }
    throw new Error(`Hektor update_annonce_MEF ${groupName} refuse: ${response.text.slice(0, 500)}`);
  }
  return {
    group: groupName,
    fields: applied.map((item) => item.field),
    targets: applied,
    skipped,
    response: parsed || response.text.slice(0, 300),
  };
}

async function postHektorPrincipalTextUpdate(job, annonceId, fields) {
  const title = fields.title == null ? null : String(fields.title);
  const body = fields.description == null ? null : String(fields.description);
  if (title == null && body == null) return null;

  const id = encodeURIComponent(String(annonceId));
  const current = await hektorFetch(`${XMLRPC_URL}?mode=chargeAnnonceText&modeText=editer&typeText=principal&fromCallback=false&idann=${id}&lang=fr`, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${id}`,
    },
  });
  const values = extractHektorFormValues(current.text, null);
  const payload = new URLSearchParams();
  payload.set("mode", "annonce-update_infos_textes");
  payload.set("idann", String(annonceId));
  payload.set("idModule", "0");
  payload.set("titre", title == null ? values.get("titre") || "" : title);
  payload.set("corps", body == null ? values.get("corps_ann") || "" : body);

  await logJob(job.id, "hektor_annonce_update", "running", "Sauvegarde texte principal", {
    hektor_annonce_id: String(annonceId),
    fields: Object.keys(fields).filter((key) => fields[key] != null),
  });

  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: payload,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${id}`,
    },
  });
  const parsed = JSON.parse(response.text);
  if (String(parsed.result) !== "1") {
    throw new Error(`Hektor annonce-update_infos_textes refuse: ${response.text.slice(0, 500)}`);
  }
  return {
    group: "principal_text",
    fields: Object.keys(fields).filter((key) => fields[key] != null),
    response: parsed,
  };
}

function hektorChauffageFromPayload(payload) {
  const fields = hektorPayloadMergedFields(payload);
  const chauffage = {
    formatChauff: textFromObjectKeys(fields, ["formatChauff", "format_chauff", "heating_format", "heatingFormat"]),
    typeChauff: textFromObjectKeys(fields, ["typeChauff", "type_chauff", "heating_type", "heatingType"]),
    energieChauff: textFromObjectKeys(fields, ["energieChauff", "energie_chauff", "heating_energy", "heatingEnergy"]),
  };
  return Object.values(chauffage).some((value) => value) ? chauffage : null;
}

function selectedOptionValue(selectHtml) {
  const options = Array.from(String(selectHtml || "").matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((match) => match[0]);
  const selected = options.find((option) => /\bselected\b/i.test(option)) || options[0];
  return selected ? attrValue(selected, "value") || "" : "";
}

function extractHektorExistingChauffages(html) {
  const source = String(html || "");
  const rowStarts = [];
  const rowRegex = /<table\b[^>]*id\s*=\s*["']chauffageExist(\d+)["'][^>]*>/gi;
  let match;
  while ((match = rowRegex.exec(source))) {
    rowStarts.push({ id: match[1], index: match.index });
  }
  return rowStarts.map((row, index) => {
    const next = rowStarts[index + 1] ? rowStarts[index + 1].index : source.length;
    const block = source.slice(row.index, next);
    const values = {};
    const selectRegex = /<select\b[^>]*>[\s\S]*?<\/select>/gi;
    let selectMatch;
    while ((selectMatch = selectRegex.exec(block))) {
      const onchange = attrValue(selectMatch[0], "onchange") || "";
      const typeMatch = onchange.match(/updateValueChauffage\(["']\d+["']\s*,\s*["'](format|type|energie)["']\s*,\s*this\.value\)/i);
      if (typeMatch) values[typeMatch[1]] = selectedOptionValue(selectMatch[0]);
    }
    return {
      id: row.id,
      format: values.format || "",
      type: values.type || "",
      energie: values.energie || "",
    };
  });
}

async function postHektorChauffageController(job, annonceId, body, action) {
  const id = encodeURIComponent(String(annonceId));
  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${id}`,
    },
  });
  let parsed = null;
  try {
    parsed = JSON.parse(response.text);
  } catch (_) {
    parsed = null;
  }
  if (parsed && Object.prototype.hasOwnProperty.call(parsed, "result") && String(parsed.result) !== "1") {
    throw new Error(`Hektor chauffage ${action} refuse: ${response.text.slice(0, 500)}`);
  }
  if (!parsed && /Credential Error|Forbidden|403/i.test(response.text)) {
    throw new Error(`Hektor chauffage ${action} refuse: ${response.text.slice(0, 500)}`);
  }
  return parsed || response.text.slice(0, 300);
}

async function applyHektorChauffage(job, annonceId, payload) {
  const chauffage = hektorChauffageFromPayload(payload);
  if (!chauffage) return null;

  const id = encodeURIComponent(String(annonceId));
  const html = await hektorFetch(`${XMLRPC_URL}?mode=ihmChargeGroupe&idAnnonce=${id}&group=equipements&consultMode=editer&ajax=ajax`, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${id}`,
    },
  });
  const existing = extractHektorExistingChauffages(html.text);
  await logJob(job.id, "hektor_annonce_chauffage", "running", "Application chauffage via controleur dedie", {
    hektor_annonce_id: String(annonceId),
    requested: chauffage,
    existing_count: existing.length,
    existing_ids: existing.map((item) => item.id),
  });

  const defaulted = {
    formatChauff: chauffage.formatChauff || "4",
    typeChauff: chauffage.typeChauff || "9",
    energieChauff: chauffage.energieChauff || "14",
  };
  const responses = [];
  let action = "add";

  if (existing.length) {
    action = "update";
    const target = existing[0];
    const updateMap = [
      ["format", defaulted.formatChauff, target.format],
      ["type", defaulted.typeChauff, target.type],
      ["energie", defaulted.energieChauff, target.energie],
    ];
    for (const [type, value, current] of updateMap) {
      if (!value || value === current) continue;
      const body = new URLSearchParams({
        mode: "annonce-equipements-controllerChauffages",
        updateExistingElement: "updateElement",
        idChauffage: target.id,
        type,
        valeur: value,
      });
      responses.push(await postHektorChauffageController(job, annonceId, body, `update:${type}`));
    }
  } else {
    const body = new URLSearchParams({
      mode: "annonce-equipements-controllerChauffages",
      getNewElement: "newElement",
      idAnnonce: String(annonceId),
      formatChauff: defaulted.formatChauff,
      typeChauff: defaulted.typeChauff,
      energieChauff: defaulted.energieChauff,
    });
    responses.push(await postHektorChauffageController(job, annonceId, body, "add"));
  }

  await logJob(job.id, "hektor_annonce_chauffage", "done", "Chauffage sauvegarde dans Hektor", {
    hektor_annonce_id: String(annonceId),
    action,
    requested: defaulted,
    existing_count_before: existing.length,
    duplicate_existing_count: Math.max(0, existing.length - 1),
  });

  return {
    group: "chauffage",
    action,
    fields: Object.keys(defaulted),
    requested: defaulted,
    existing_count_before: existing.length,
    duplicate_existing_count: Math.max(0, existing.length - 1),
    response: responses.length ? responses : "already_current",
  };
}

function hektorCompositionPayloadCandidates(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const fieldsJson = source.fields_json && typeof source.fields_json === "object" ? source.fields_json : {};
  const fields = source.fields && typeof source.fields === "object" ? source.fields : {};
  return [
    source.composition_pieces,
    source.compositionPieces,
    source.hektor_composition_pieces,
    fieldsJson.composition_pieces,
    fieldsJson.compositionPieces,
    fields.composition_pieces,
    fields.compositionPieces,
  ];
}

function hektorCompositionRowsFromUnknown(value) {
  if (!value) return [];
  if (typeof value === "string") return hektorCompositionRowsFromUnknown(safeJsonParse(value, null));
  if (Array.isArray(value)) return value.filter((item) => item && typeof item === "object" && !Array.isArray(item));
  if (typeof value === "object") {
    return hektorCompositionRowsFromUnknown(value.pieces || value.rows || value.data || value.items);
  }
  return [];
}

function textFromCompositionPiece(piece, keys) {
  for (const key of keys) {
    const value = piece[key];
    if (value === undefined || value === null) continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return "";
}

const HEKTOR_COMPOSITION_PIECE_TYPE_OPTIONS = [
  { id: "1", label: "Chambre" },
  { id: "13", label: "Cuisine" },
  { id: "2", label: "Salon/sejour" },
  { id: "9", label: "Salle de bains" },
  { id: "15", label: "Bureau" },
  { id: "16", label: "WC" },
  { id: "26", label: "Entree" },
  { id: "14", label: "Piece a vivre" },
  { id: "21", label: "Dressing" },
  { id: "11", label: "Buanderie" },
  { id: "12", label: "Cave" },
  { id: "5", label: "Garage" },
  { id: "8", label: "Parking" },
  { id: "18", label: "Balcon" },
  { id: "17", label: "Terrasse" },
  { id: "4", label: "Jardin" },
  { id: "32", label: "Piscine" },
  { id: "20", label: "Veranda" },
  { id: "25", label: "Accueil" },
  { id: "6", label: "Annexe" },
  { id: "59", label: "Chambre de bonne" },
  { id: "60", label: "Chambre de service" },
  { id: "27", label: "Chambre froide" },
  { id: "28", label: "Depot" },
  { id: "29", label: "Entrepot" },
  { id: "30", label: "Espace bien-etre" },
  { id: "31", label: "Mezzanine" },
  { id: "24", label: "Reserve" },
  { id: "23", label: "Salle" },
  { id: "33", label: "Suite" },
  { id: "3", label: "Terrain" },
  { id: "34", label: "Vestiaire" },
];

const HEKTOR_COMPOSITION_PIECE_TYPE_BY_ID = new Map(
  HEKTOR_COMPOSITION_PIECE_TYPE_OPTIONS.map((option) => [option.id, option])
);

function normalizeHektorCompositionTypeLabel(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

const HEKTOR_COMPOSITION_PIECE_TYPE_ALIASES = new Map();
for (const option of HEKTOR_COMPOSITION_PIECE_TYPE_OPTIONS) {
  HEKTOR_COMPOSITION_PIECE_TYPE_ALIASES.set(normalizeHektorCompositionTypeLabel(option.label), option);
}
for (const [alias, id] of [
  ["sejour", "2"],
  ["salon", "2"],
  ["salon sejour", "2"],
  ["salle de bain", "9"],
  ["salle de bains", "9"],
  ["sdb", "9"],
  ["toilette", "16"],
  ["toilettes", "16"],
  ["bureau", "15"],
  ["entree", "26"],
  ["piece a vivre", "14"],
  ["depot", "28"],
  ["veranda", "20"],
  ["reserve", "24"],
]) {
  const option = HEKTOR_COMPOSITION_PIECE_TYPE_BY_ID.get(id);
  if (option) HEKTOR_COMPOSITION_PIECE_TYPE_ALIASES.set(normalizeHektorCompositionTypeLabel(alias), option);
}

function hektorCompositionTypeOptionFromLabel(label) {
  const normalized = normalizeHektorCompositionTypeLabel(label);
  return normalized ? HEKTOR_COMPOSITION_PIECE_TYPE_ALIASES.get(normalized) || null : null;
}

function inferHektorCompositionTypeOptionFromText(text) {
  const normalized = normalizeHektorCompositionTypeLabel(text);
  if (!normalized) return null;
  const aliases = Array.from(HEKTOR_COMPOSITION_PIECE_TYPE_ALIASES.entries())
    .filter(([label]) => label)
    .sort((a, b) => b[0].length - a[0].length);
  for (const [label, option] of aliases) {
    const pattern = new RegExp(`(^| )${label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}( |$)`);
    if (pattern.test(normalized)) return option;
  }
  return null;
}

function resolveHektorCompositionPieceType(piece, rawIdTypePiece) {
  const rawId = String(rawIdTypePiece || "").trim();
  const explicitLabel = textFromCompositionPiece(piece, [
    "typeLabel",
    "type_label",
    "typePieceLabel",
    "labelTypePiece",
    "libelleTypePiece",
    "libelle",
    "label",
    "type",
  ]);
  const explicitOption = hektorCompositionTypeOptionFromLabel(explicitLabel);
  const inferredOption = explicitOption
    || inferHektorCompositionTypeOptionFromText(textFromCompositionPiece(piece, ["namePiece", "name_piece", "name", "customName"]))
    || inferHektorCompositionTypeOptionFromText(textFromCompositionPiece(piece, ["detailPiece", "detail_piece", "detail", "description"]));
  const knownOption = rawId ? HEKTOR_COMPOSITION_PIECE_TYPE_BY_ID.get(rawId) || null : null;

  if (!rawId && inferredOption) {
    return {
      idTypePiece: inferredOption.id,
      typeLabel: explicitLabel || inferredOption.label,
      originalIdTypePiece: null,
      corrected: false,
    };
  }

  if (rawId && knownOption && inferredOption && knownOption.id !== inferredOption.id) {
    return {
      idTypePiece: inferredOption.id,
      typeLabel: explicitLabel || inferredOption.label,
      originalIdTypePiece: rawId,
      originalTypeLabel: knownOption.label,
      corrected: true,
    };
  }

  return {
    idTypePiece: rawId || "1",
    typeLabel: explicitLabel || (knownOption ? knownOption.label : "") || (inferredOption ? inferredOption.label : ""),
    originalIdTypePiece: null,
    corrected: false,
  };
}

function normalizeHektorCompositionPiece(piece, index) {
  const actionRaw = textFromCompositionPiece(piece, ["action", "_action", "mode"]).toLowerCase();
  const action = actionRaw === "delete" || actionRaw === "remove" || actionRaw === "deleted"
    ? "delete"
    : actionRaw === "update" || actionRaw === "edit"
      ? "update"
      : "add";
  const idPiece = textFromCompositionPiece(piece, ["idPiece", "id_piece", "id", "ID", "idpiece"]);
  const rawIdTypePiece = textFromCompositionPiece(piece, ["idTypePiece", "id_type_piece", "typePiece", "type_piece", "typePieceId", "idType"]);
  const typeResolution = resolveHektorCompositionPieceType(piece, rawIdTypePiece);
  const idTypePiece = typeResolution.idTypePiece || "1";
  const detailPiece = textFromCompositionPiece(piece, ["detailPiece", "detail_piece", "detail", "description"]);
  const namePiece = textFromCompositionPiece(piece, ["namePiece", "name_piece", "name", "customName"]);
  const surfacePiece = textFromCompositionPiece(piece, ["surfacePiece", "surface_piece", "surface"]).replace(",", ".");
  const etagePiece = textFromCompositionPiece(piece, ["etagePiece", "etage_piece", "etage", "floor"]);
  const notePublique = textFromCompositionPiece(piece, ["notePublique", "note_publique", "notePublic", "note_public"]);
  const notePrivee = textFromCompositionPiece(piece, ["notePrivee", "note_privee", "notePrivate", "note_private"]);
  const noteInterAgence = textFromCompositionPiece(piece, ["noteInterAgence", "note_inter_agence", "noteInterAgency", "note_interagency"]);
  const photosPiece = textFromCompositionPiece(piece, ["photosPiece", "photos_piece", "photos"]);

  if (action === "delete" && !idPiece) {
    throw new Error(`Piece ${index + 1}: idPiece obligatoire pour supprimer`);
  }
  if (surfacePiece && !/^-?\d+(\.\d+)?$/.test(surfacePiece)) {
    throw new Error(`Piece ${index + 1}: surfacePiece invalide`);
  }
  const hasContent = [rawIdTypePiece, typeResolution.typeLabel, detailPiece, namePiece, surfacePiece, etagePiece, notePublique, notePrivee, noteInterAgence, photosPiece]
    .some((value) => String(value || "").trim());
  if (!hasContent && action !== "delete") return null;
  return {
    action,
    idPiece,
    idTypePiece,
    typeLabel: typeResolution.typeLabel || null,
    originalIdTypePiece: typeResolution.originalIdTypePiece || null,
    originalTypeLabel: typeResolution.originalTypeLabel || null,
    idTypePieceCorrected: typeResolution.corrected === true,
    detailPiece,
    namePiece,
    surfacePiece,
    etagePiece,
    notePublique,
    notePrivee,
    noteInterAgence,
    photosPiece,
  };
}

function hektorCompositionPiecesFromPayload(payload) {
  for (const candidate of hektorCompositionPayloadCandidates(payload)) {
    const rows = hektorCompositionRowsFromUnknown(candidate);
    if (!rows.length) continue;
    return rows
      .map((piece, index) => normalizeHektorCompositionPiece(piece, index))
      .filter(Boolean);
  }
  return [];
}

async function postHektorCompositionPieceMutation(job, annonceId, piece, index) {
  const body = new URLSearchParams();
  const action = piece.action || (piece.idPiece ? "update" : "add");
  if (action === "delete") {
    body.set("mode", "piece-deletePiece");
    body.set("idPiece", piece.idPiece);
  } else {
    body.set("mode", action === "update" && piece.idPiece ? "piece-updatePiece" : "piece-addNewPiece");
    if (piece.idPiece) body.set("idPiece", piece.idPiece);
    body.set("idTypePiece", piece.idTypePiece || "1");
    body.set("surfacePiece", piece.surfacePiece || "");
    body.set("etagePiece", piece.etagePiece || "");
    body.set("namePiece", piece.namePiece || "");
    body.set("notePublique", piece.notePublique || "");
    body.set("notePrivee", piece.notePrivee || "");
    body.set("noteInterAgence", piece.noteInterAgence || "");
    body.set("photosPiece", piece.photosPiece || "");
    body.set("detailPiece", piece.detailPiece || "");
    body.set("idAnnonce", String(annonceId));
  }

  await logJob(job.id, "hektor_annonce_piece", "running", `Sauvegarde piece ${index + 1}`, {
    hektor_annonce_id: String(annonceId),
    action,
    idPiece: piece.idPiece || null,
    idTypePiece: piece.idTypePiece || null,
    typeLabel: piece.typeLabel || null,
    originalIdTypePiece: piece.originalIdTypePiece || null,
    originalTypeLabel: piece.originalTypeLabel || null,
    idTypePieceCorrected: piece.idTypePieceCorrected === true,
    detailPiece: piece.detailPiece || null,
  });

  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(String(annonceId))}`,
    },
  });
  let parsed = null;
  try {
    parsed = JSON.parse(response.text);
  } catch (_) {
    parsed = null;
  }
  if (parsed && Object.prototype.hasOwnProperty.call(parsed, "result") && String(parsed.result) !== "1") {
    throw new Error(`Hektor ${body.get("mode")} refuse: ${response.text.slice(0, 500)}`);
  }
  if (!parsed && /Credential Error|Forbidden|403/i.test(response.text)) {
    throw new Error(`Hektor ${body.get("mode")} refuse: ${response.text.slice(0, 500)}`);
  }
  return {
    group: "composition_piece",
    mode: body.get("mode"),
    action,
    idPiece: piece.idPiece || null,
    idTypePiece: piece.idTypePiece || null,
    typeLabel: piece.typeLabel || null,
    originalIdTypePiece: piece.originalIdTypePiece || null,
    originalTypeLabel: piece.originalTypeLabel || null,
    idTypePieceCorrected: piece.idTypePieceCorrected === true,
    response: parsed || response.text.slice(0, 300),
  };
}

async function applyHektorCompositionPieces(job, annonceId, payload) {
  const pieces = hektorCompositionPiecesFromPayload(payload);
  if (!pieces.length) return [];
  await logJob(job.id, "hektor_annonce_piece", "running", "Application des pieces de composition", {
    hektor_annonce_id: String(annonceId),
    count: pieces.length,
    actions: pieces.map((piece) => piece.action),
  });
  const results = [];
  for (const [index, piece] of pieces.entries()) {
    results.push(await postHektorCompositionPieceMutation(job, annonceId, piece, index));
  }
  await logJob(job.id, "hektor_annonce_piece", "done", "Pieces de composition sauvegardees", {
    hektor_annonce_id: String(annonceId),
    count: results.length,
  });
  return results;
}

// Tier 2 — listes d'alias des champs "standards" (consommes par la voie cleanFields).
// Extraites ici comme SOURCE UNIQUE : utilisees par normalizeHektorAnnonceUpdatePayload ET
// par synthesizeWizardFieldsForPending (qui doit EXCLURE ces champs de hektor_wizard_fields
// pour eviter le double-traitement). Ne pas dupliquer cette liste ailleurs.
const HEKTOR_CLEANFIELD_TEXT_KEYS = [
  ["title", ["title", "titre"]],
  ["description", ["description", "corps"]],
  ["address", ["address", "adresse", "ADRESSE_COMPL"]],
  ["postal_code", ["postal_code", "postalCode", "code_postal", "codepublique"]],
  ["city", ["city", "ville", "villepublique"]],
  ["building", ["building", "immeuble"]],
  ["transport", ["transport", "TRANSPORT"]],
  ["proximity", ["proximity", "proximite", "PROXIMITE"]],
  ["environment", ["environment", "environnement", "ENVIRONNEMENT"]],
  ["kitchen", ["kitchen", "cuisine", "CUISINE"]],
  ["exposure", ["exposure", "exposition", "EXPOSITION"]],
  ["view", ["view", "vue", "vuee"]],
  ["garden", ["garden", "jardin", "JARDIN", "JARDIN-"]],
  ["pool", ["pool", "piscine", "PISCINE", "PISCINE-"]],
  ["terrace", ["terrace", "terrasse", "TERRASSE"]],
  ["interior_state", ["interior_state", "interiorState", "etat_interieur", "ETAT_INTERIEUR"]],
  ["exterior_state", ["exterior_state", "exteriorState", "etat_exterieur", "ETAT_EXTERIEUR"]],
  ["dpe_value", ["dpe_value", "dpeValue", "DPE", "dpe_cons"]],
  ["ges_value", ["ges_value", "gesValue", "GES", "dpe_ges"]],
  ["diagnostic_risk_comment", ["diagnostic_risk_comment", "diagnosticRiskComment", "diagnostic_note", "diagnosticNote", "diag_risques_nat_tech_commentaire"]],
  ["mandate_number", ["mandate_number", "mandateNumber", "NO_MANDAT"]],
  ["mandate_type", ["mandate_type", "mandateType"]],
  ["mandate_start_date", ["mandate_start_date", "mandateStartDate"]],
  ["mandate_end_date", ["mandate_end_date", "mandateEndDate"]],
];
const HEKTOR_CLEANFIELD_NUMBER_KEYS = [
  ["price", ["price", "prix"]],
  ["net_seller_price", ["net_seller_price", "netSellerPrice", "PRIXNETVENDEUR"]],
  ["surface", ["surface", "surfappart", "surface_habitable"]],
  ["carrez_surface", ["carrez_surface", "carrezSurface", "SURF_CARREZ"]],
  ["room_count", ["room_count", "roomCount", "nbpieces"]],
  ["bedroom_count", ["bedroom_count", "bedroomCount", "NB_CHAMBRES"]],
  ["floor", ["floor", "etage", "ETAGE"]],
  ["level_count", ["level_count", "levelCount", "NB_NIVEAUX"]],
  ["bathroom_count", ["bathroom_count", "bathroomCount", "NB_SDB", "SDB"]],
  ["shower_room_count", ["shower_room_count", "showerRoomCount", "NB_SE", "SE", "SDE"]],
  ["wc_count", ["wc_count", "wcCount", "NB_WC", "WC"]],
  ["land_surface", ["land_surface", "landSurface", "surfterrain"]],
  ["garden_surface", ["garden_surface", "gardenSurface", "SURFACE_JARDIN"]],
  ["terrace_count", ["terrace_count", "terraceCount", "NB_TERRASSE"]],
  ["garage_count", ["garage_count", "garageCount", "GARAGE_BOX"]],
  ["garage_surface", ["garage_surface", "garageSurface", "SURFACE_GARAGE"]],
  ["parking_inside_count", ["parking_inside_count", "parkingInsideCount", "NB_PARK_INT"]],
  ["parking_outside_count", ["parking_outside_count", "parkingOutsideCount", "NB_PARK_EXT"]],
  ["construction_year", ["construction_year", "constructionYear", "ANNEE_CONS", "ANNEE_CONSTRUCTION"]],
  ["copro_lots", ["copro_lots", "coproLots", "copropriete_nb_lot"]],
  ["copro_charges", ["copro_charges", "coproCharges", "CHARGES"]],
  ["copro_quote_part", ["copro_quote_part", "coproQuotePart", "copropriete_quote_part"]],
  ["copro_works_fund", ["copro_works_fund", "coproWorksFund", "montant_fonds_travaux"]],
  ["fees", ["fees", "HONORAIRES", "honoraires"]],
  ["latitude", ["latitude", "lat"]],
  ["longitude", ["longitude", "lng", "lon"]],
];
const HEKTOR_CLEANFIELD_ALIASES = new Set(
  [...HEKTOR_CLEANFIELD_TEXT_KEYS, ...HEKTOR_CLEANFIELD_NUMBER_KEYS].flatMap(([, aliases]) => aliases),
);

// Tier 2 — edition optimiste : les champs arrivent A PLAT (pas de hektor_wizard_fields).
// La voie standard lit le plat (champs typés OK) mais la voie wizard ne lit QUE
// hektor_wizard_fields -> les equipements (EAU, CAVE, alarme, surfaces annexes...) etaient
// PERDUS. On reconstruit hektor_wizard_fields = champs a plat NON consommes par cleanFields
// (=> aucun double-traitement : un champ = une seule voie). Ne touche que le cas optimiste.
function synthesizeWizardFieldsForPending(payload) {
  if (!payload || typeof payload !== "object") return;
  const existing = exactHektorWizardFields(payload);
  if (existing && Object.keys(existing).length) return; // deja niche (chemin manuel/creation)
  const source = payload.fields_json && typeof payload.fields_json === "object"
    ? payload.fields_json
    : (payload.fields && typeof payload.fields === "object" ? payload.fields : payload);
  if (!source || typeof source !== "object") return;
  const meta = new Set([
    "from_pending", "base_snapshot", "app_dossier_id", "hektor_annonce_id", "source",
    "push_after", "fields_json", "fields", "hektor_wizard_fields", "wizard_fields", "wizardFields",
    "composition_pieces", "compositionPieces", "hektor_composition_pieces",
  ]);
  const wizard = {};
  for (const [k, v] of Object.entries(source)) {
    if (meta.has(k)) continue;
    if (HEKTOR_CLEANFIELD_ALIASES.has(k)) continue;   // gere par cleanFields -> reste au top-level
    if (HEKTOR_CHAUFFAGE_FIELD_KEYS.has(k)) continue; // gere par hektorChauffageFromPayload
    if (v === undefined || v === null) continue;
    wizard[k] = v;
  }
  if (Object.keys(wizard).length) payload.hektor_wizard_fields = wizard;
}

function normalizeHektorAnnonceUpdatePayload(payload, options = {}) {
  const baseFields = payload && payload.fields_json && typeof payload.fields_json === "object" ? payload.fields_json : payload.fields || payload;
  const fields = {
    ...(baseFields && typeof baseFields === "object" ? baseFields : {}),
    ...exactHektorWizardFields(payload),
  };
  const profilePayload = {
    ...(payload && typeof payload === "object" ? payload : {}),
    ...fields,
  };
  const clean = {};
  const textKeys = HEKTOR_CLEANFIELD_TEXT_KEYS;
  const numberKeys = HEKTOR_CLEANFIELD_NUMBER_KEYS;
  const skippedFinancial = new Set(options.skipFinancial ? ["price", "net_seller_price", "copro_charges", "fees"] : []);
  for (const [key, aliases] of textKeys) {
    if (skippedFinancial.has(key)) continue;
    const raw = firstDefined(fields || {}, aliases);
    if (raw == null) continue;
    const value = key === "garden" || key === "pool" || key === "terrace"
      ? normalizeHektorOuiNonValue(raw)
      : String(raw).trim();
    if (value) clean[key] = value;
  }
  for (const [key, aliases] of numberKeys) {
    if (skippedFinancial.has(key)) continue;
    const raw = firstDefined(fields || {}, aliases);
    if (raw == null) continue;
    const value = String(raw).replace(",", ".").trim();
    if (value && !/^-?\d+(\.\d+)?$/.test(value)) {
      if (options.skipInvalidNumbers) continue;
      throw new Error(`Champ numerique invalide: ${key}`);
    }
    if (value) clean[key] = value;
  }
  return filterHektorAnnonceUpdateFieldsForProfile(profilePayload, clean);
}

function fieldSpec(value, candidates) {
  return { value, candidates };
}

async function pushHektorGroupUpdate(results, job, annonceId, groupName, readMode, fields, options = {}) {
  if (!Object.keys(fields).length) return;
  try {
    const result = await postHektorMefUpdate(job, annonceId, groupName, readMode, fields);
    if (result) results.push(result);
  } catch (error) {
    if (!options.continueOnGroupError) throw error;
    const message = error && error.message ? error.message : String(error);
    await logJob(job.id, "hektor_annonce_update", "error", `Sauvegarde groupe ${groupName} echouee`, {
      hektor_annonce_id: String(annonceId),
      group: groupName,
      fields: Object.keys(fields || {}),
      error: message,
    });
    results.push({
      group: groupName,
      status: "error",
      fields: Object.keys(fields || {}),
      error: message,
    });
  }
}

async function applyHektorAnnonceFieldUpdates(job, annonceId, fields, options = {}) {
  const cleanFields = normalizeHektorAnnonceUpdatePayload(fields, options);
  const results = [];

  try {
    const textResult = await postHektorPrincipalTextUpdate(job, annonceId, {
      title: cleanFields.title,
      description: cleanFields.description,
    });
    if (textResult) results.push(textResult);
  } catch (error) {
    if (!options.continueOnGroupError) throw error;
    const message = error && error.message ? error.message : String(error);
    await logJob(job.id, "hektor_annonce_update", "error", "Sauvegarde texte principal echouee", {
      hektor_annonce_id: String(annonceId),
      fields: ["title", "description"].filter((key) => cleanFields[key] != null),
      error: message,
    });
    results.push({ group: "principal_text", status: "error", fields: ["title", "description"], error: message });
  }

  if (!options.skipComposition) {
    const compositionResults = await applyHektorCompositionPieces(job, annonceId, fields);
    results.push(...compositionResults);
  }

  try {
    const chauffageResult = await applyHektorChauffage(job, annonceId, fields);
    if (chauffageResult) results.push(chauffageResult);
  } catch (error) {
    if (!options.continueOnGroupError) throw error;
    const message = error && error.message ? error.message : String(error);
    await logJob(job.id, "hektor_annonce_chauffage", "error", "Sauvegarde chauffage echouee", {
      hektor_annonce_id: String(annonceId),
      error: message,
    });
    results.push({ group: "chauffage", status: "error", fields: Array.from(HEKTOR_CHAUFFAGE_FIELD_KEYS), error: message });
  }

  for (const update of buildExactWizardGroupUpdates(fields, options)) {
    await pushHektorGroupUpdate(results, job, annonceId, update.group, update.mode, update.fields, options);
  }

  const secteur = {};
  if (cleanFields.postal_code != null) secteur.postal_code = fieldSpec(cleanFields.postal_code, ["codepublique"]);
  if (cleanFields.city != null) secteur.city = fieldSpec(cleanFields.city, ["villepublique"]);
  if (cleanFields.address != null) secteur.address = fieldSpec(cleanFields.address, ["ADRESSE_COMPL"]);
  if (cleanFields.building != null) secteur.building = fieldSpec(cleanFields.building, ["immeuble"]);
  if (cleanFields.transport != null) secteur.transport = fieldSpec(cleanFields.transport, ["TRANSPORT"]);
  if (cleanFields.proximity != null) secteur.proximity = fieldSpec(cleanFields.proximity, ["PROXIMITE"]);
  if (cleanFields.environment != null) secteur.environment = fieldSpec(cleanFields.environment, ["ENVIRONNEMENT"]);
  if (cleanFields.latitude != null) secteur.latitude = fieldSpec(cleanFields.latitude, ["latitude"]);
  if (cleanFields.longitude != null) secteur.longitude = fieldSpec(cleanFields.longitude, ["longitude"]);
  if (cleanFields.postal_code != null || cleanFields.city != null) {
    const locality = await resolveHektorPublicLocality(cleanFields.postal_code, cleanFields.city);
    if (locality && locality.idCode) secteur.id_codepublique = fieldSpec(locality.idCode, ["idCodepublique"]);
    if (locality && locality.idVille) secteur.id_villepublique = fieldSpec(locality.idVille, ["idVillepublique"]);
    if (locality && locality.latitude && cleanFields.latitude == null) secteur.latitude = fieldSpec(locality.latitude, ["latitude"]);
    if (locality && locality.longitude && cleanFields.longitude == null) secteur.longitude = fieldSpec(locality.longitude, ["longitude"]);
  }
  await pushHektorGroupUpdate(results, job, annonceId, "secteur", "ihmChargeGroupe_Secteur", secteur, options);

  const agInterieur = {};
  if (cleanFields.room_count != null) agInterieur.room_count = fieldSpec(cleanFields.room_count, ["nbpieces"]);
  if (cleanFields.bedroom_count != null) agInterieur.bedroom_count = fieldSpec(cleanFields.bedroom_count, ["NB_CHAMBRES"]);
  if (cleanFields.level_count != null) agInterieur.level_count = fieldSpec(cleanFields.level_count, ["NB_NIVEAUX"]);
  if (cleanFields.surface != null) agInterieur.surface = fieldSpec(cleanFields.surface, ["surfappart"]);
  if (cleanFields.carrez_surface != null) agInterieur.carrez_surface = fieldSpec(cleanFields.carrez_surface, ["SURF_CARREZ"]);
  if (cleanFields.bathroom_count != null) agInterieur.bathroom_count = fieldSpec(cleanFields.bathroom_count, ["SDB", "NB_SDB", "nb_sdb", "sdb"]);
  if (cleanFields.shower_room_count != null) agInterieur.shower_room_count = fieldSpec(cleanFields.shower_room_count, ["SE", "SDE", "NB_SE", "NB_SALLE_EAU", "salle_eau"]);
  if (cleanFields.wc_count != null) agInterieur.wc_count = fieldSpec(cleanFields.wc_count, ["WC", "NB_WC", "wc"]);
  if (cleanFields.kitchen != null) agInterieur.kitchen = fieldSpec(cleanFields.kitchen, ["CUISINE", "cuisine"]);
  if (cleanFields.exposure != null) agInterieur.exposure = fieldSpec(cleanFields.exposure, ["EXPOSITION", "exposition"]);
  if (cleanFields.view != null) agInterieur.view = fieldSpec(cleanFields.view, ["vuee", "VUE", "vue"]);
  await pushHektorGroupUpdate(results, job, annonceId, "ag_interieur", "ihmChargeGroupe", agInterieur, options);

  const agExterieur = {};
  if (cleanFields.floor != null) {
    const floorState = inferHektorFloorStateValue(cleanFields.floor);
    if (floorState) agExterieur.floor_state = fieldSpec(floorState, ["floorState"]);
    agExterieur.floor = fieldSpec(cleanFields.floor, ["ETAGE"]);
  }
  if (cleanFields.garden != null) agExterieur.garden = fieldSpec(cleanFields.garden, ["JARDIN", "JARDIN-"]);
  if (cleanFields.garden_surface != null) agExterieur.garden_surface = fieldSpec(cleanFields.garden_surface, ["SURFACE_JARDIN"]);
  if (cleanFields.terrace_count != null) agExterieur.terrace_count = fieldSpec(cleanFields.terrace_count, ["NB_TERRASSE"]);
  if (cleanFields.terrace != null) agExterieur.terrace = fieldSpec(cleanFields.terrace, ["TERRASSE"]);
  if (cleanFields.garage_count != null) agExterieur.garage_count = fieldSpec(cleanFields.garage_count, ["GARAGE_BOX"]);
  if (cleanFields.garage_surface != null) agExterieur.garage_surface = fieldSpec(cleanFields.garage_surface, ["SURFACE_GARAGE"]);
  if (cleanFields.parking_inside_count != null) agExterieur.parking_inside_count = fieldSpec(cleanFields.parking_inside_count, ["NB_PARK_INT"]);
  if (cleanFields.parking_outside_count != null) agExterieur.parking_outside_count = fieldSpec(cleanFields.parking_outside_count, ["NB_PARK_EXT"]);
  if (cleanFields.pool != null) agExterieur.pool = fieldSpec(cleanFields.pool, ["PISCINE", "PISCINE-"]);
  await pushHektorGroupUpdate(results, job, annonceId, "ag_exterieur", "ihmChargeGroupe", agExterieur, options);

  const terrain = {};
  if (cleanFields.land_surface != null) terrain.land_surface = fieldSpec(cleanFields.land_surface, ["surfterrain"]);
  await pushHektorGroupUpdate(results, job, annonceId, "terrain", "ihmChargeGroupe", terrain, options);

  const diagnostics = {};
  if (cleanFields.interior_state != null) diagnostics.interior_state = fieldSpec(cleanFields.interior_state, ["etat_interieur", "ETAT_INTERIEUR"]);
  if (cleanFields.exterior_state != null) diagnostics.exterior_state = fieldSpec(cleanFields.exterior_state, ["etat_exterieur", "ETAT_EXTERIEUR"]);
  if (cleanFields.dpe_value != null) diagnostics.dpe_value = fieldSpec(cleanFields.dpe_value, ["dpe_cons", "DPE", "dpe", "classe_energie"]);
  if (cleanFields.ges_value != null) diagnostics.ges_value = fieldSpec(cleanFields.ges_value, ["dpe_ges", "GES", "ges", "classe_ges"]);
  if (cleanFields.construction_year != null) diagnostics.construction_year = fieldSpec(cleanFields.construction_year, ["ANNEE_CONS", "ANNEE_CONSTRUCTION", "annee_construction", "construction_year"]);
  if (cleanFields.diagnostic_risk_comment != null) diagnostics.diagnostic_risk_comment = fieldSpec(cleanFields.diagnostic_risk_comment, ["diag_risques_nat_tech_commentaire"]);
  await pushHektorGroupUpdate(results, job, annonceId, "diagnostiques", "ihmChargeGroupe", diagnostics, options);

  const copropriete = {};
  if (cleanFields.copro_lots != null) copropriete.copro_lots = fieldSpec(cleanFields.copro_lots, ["copropriete_nb_lot"]);
  if (cleanFields.copro_quote_part != null) copropriete.copro_quote_part = fieldSpec(cleanFields.copro_quote_part, ["copropriete_quote_part"]);
  if (cleanFields.copro_works_fund != null) copropriete.copro_works_fund = fieldSpec(cleanFields.copro_works_fund, ["montant_fonds_travaux"]);
  await pushHektorGroupUpdate(results, job, annonceId, "copropriete", "ihmChargeGroupe", copropriete, options);

  const mandatInfo = {};
  if (cleanFields.price != null) mandatInfo.price = fieldSpec(cleanFields.price, ["prix"]);
  if (cleanFields.net_seller_price != null) mandatInfo.net_seller_price = fieldSpec(cleanFields.net_seller_price, ["PRIXNETVENDEUR"]);
  if (cleanFields.copro_charges != null) mandatInfo.copro_charges = fieldSpec(cleanFields.copro_charges, ["CHARGES"]);
  if (cleanFields.fees != null) mandatInfo.fees = fieldSpec(cleanFields.fees, ["HONORAIRES", "honoraires", "HONORAIRES_ACQUEREUR"]);
  await pushHektorGroupUpdate(results, job, annonceId, "mandat_infofi", "ihmChargeGroupe_MandatPrix", mandatInfo, options);

  return results;
}

async function applyCreatedAnnonceInitialFields(job, annonceId, payload, options = {}) {
  // Blindage (meme garde-fou que le chemin update, BUG A) : si un appelant envoie les
  // champs A PLAT (sans hektor_wizard_fields), on reconstruit la boite pour ne PAS perdre
  // les equipements a la creation. No-op aujourd'hui (le front niche deja la boite), mais
  // protege tout futur appelant (autre client/script) qui enverrait a plat.
  synthesizeWizardFieldsForPending(payload);
  const updateOptions = {
    ...options,
    skipInvalidNumbers: true,
    continueOnGroupError: true,
  };
  const cleanFields = normalizeHektorAnnonceUpdatePayload(payload, updateOptions);
  const exactUpdates = buildExactWizardGroupUpdates(payload, updateOptions);
  const chauffage = hektorChauffageFromPayload(payload);
  const chauffageFields = chauffage ? Object.keys(chauffage).filter((key) => chauffage[key]) : [];
  if (!Object.keys(cleanFields).length && !exactUpdates.length && !chauffageFields.length) {
    return { status: "skipped", reason: "no_initial_fields" };
  }
  const requestedFields = Array.from(new Set([
    ...Object.keys(cleanFields),
    ...exactUpdates.flatMap((update) => Object.keys(update.fields || {})),
    ...chauffageFields,
  ]));

  await logJob(job.id, "hektor_annonce_initial_fields", "running", "Application des champs saisis apres creation Hektor", {
    hektor_annonce_id: String(annonceId),
    fields: requestedFields,
  });
  const results = await applyHektorAnnonceFieldUpdates(job, annonceId, payload, {
    ...updateOptions,
    skipComposition: true,
  });
  const successfulResults = results.filter((item) => item && item.status !== "error");
  const errorResults = results.filter((item) => item && item.status === "error");
  if (!successfulResults.length) {
    if (errorResults.length) return { status: "error", fields: requestedFields, errors: errorResults };
    return { status: "skipped", reason: "no_supported_initial_fields", fields: requestedFields };
  }
  await logJob(job.id, "hektor_annonce_initial_fields", "done", "Champs initiaux sauvegardes dans Hektor", {
    hektor_annonce_id: String(annonceId),
    updated_groups: successfulResults.map((item) => item.group),
    error_groups: errorResults.map((item) => item.group),
  });
  return {
    status: errorResults.length ? "partial" : "updated",
    updated_groups: successfulResults,
    errors: errorResults,
  };
}

async function handleUpdateHektorAnnonceFields(job) {
  const payload = safeJsonParse(job.payload_json);
  const fromPending = payload.from_pending === true;  // Tier 2 : push optimiste débouncé
  // Tier 2 : l'edition optimiste envoie les champs A PLAT. On reconstruit la boite
  // hektor_wizard_fields (equipements/surfaces annexes) pour que la voie wizard les voie,
  // sinon ils sont silencieusement perdus. Sans recouvrement avec la voie standard.
  if (fromPending) synthesizeWizardFieldsForPending(payload);
  let dossier = null;
  try {
    dossier = await loadDossier(job);
  } catch (error) {
    if (!job.hektor_annonce_id || !(payload.hektor_user_id || payload.hektor_id_user || payload.target_hektor_user_id)) throw error;
    dossier = {
      app_dossier_id: job.app_dossier_id || payload.app_dossier_id || null,
      hektor_annonce_id: String(job.hektor_annonce_id),
      negociateur_email: payload.hektor_user_email || null,
    };
  }
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });

  const annonceId = String(dossier.hektor_annonce_id);

  // Tier 2 garde-fou anti-écrasement : pour un push from_pending, si le bien a été
  // modifié dans Hektor DEPUIS l'édition optimiste (date_maj plus récente que la photo),
  // on ne l'écrase pas -> conflit. Best-effort : si la relecture Hektor échoue, on écrit.
  if (fromPending) {
    const base = (payload.base_snapshot && typeof payload.base_snapshot === "object") ? payload.base_snapshot : {};
    const baseDateMaj = base._date_maj ? String(base._date_maj) : null;
    if (baseDateMaj) {
      // Porte 2 / AnnonceById via Python (le worker n'a pas de JWT -> l'appel Node direct
      // faisait 403 et ne bloquait jamais). Miroir du garde-fou contact (Lot B).
      const freshDateMaj = await fetchAnnonceDateMajFromApi(job, annonceId, "annonce_overwrite_guard");
      if (freshDateMaj && freshDateMaj > baseDateMaj) {
        const conflictDossierId = job.app_dossier_id || payload.app_dossier_id || (dossier && dossier.app_dossier_id) || null;
        await markAnnoncePendingConflict(conflictDossierId);
        await logJob(job.id, "annonce_overwrite_guard", "done", "Bien modifié dans Hektor depuis l'édition : écriture bloquée (anti-écrasement)", {
          hektor_annonce_id: annonceId,
          base_date_maj: baseDateMaj,
          fresh_date_maj: freshDateMaj,
        });
        return { status: "held_conflict", hektor_annonce_id: annonceId, reason: "bien_modifie_dans_hektor_depuis_edition" };
      }
    }
  }

  const results = await applyHektorAnnonceFieldUpdates(job, annonceId, payload);

  if (!results.length) throw new Error("Aucun champ annonce modifiable fourni");

  // Tier 2 : push from_pending réussi -> on efface le pending (avant l'after-refresh,
  // pour qu'il resynchronise normalement). Clone du clearSearchPending des recherches.
  if (fromPending) {
    const appDossierId = job.app_dossier_id || payload.app_dossier_id || (dossier && dossier.app_dossier_id) || null;
    await clearAnnoncePending(appDossierId);
  }

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
    reason: "update_hektor_annonce_fields",
    priority: 80,
  });

  return {
    status: "updated",
    hektor_annonce_id: annonceId,
    updated_groups: results,
    sync_job: syncJob,
  };
}

function isProcessAlive(pid) {
  const numericPid = Number(pid);
  if (!Number.isFinite(numericPid) || numericPid <= 0) return false;
  try {
    process.kill(numericPid, 0);
    return true;
  } catch (error) {
    return error && error.code === "EPERM";
  }
}

function acquireWorkerLock() {
  fs.mkdirSync(WORKER_LOCK_DIR, { recursive: true });
  try {
    fs.writeFileSync(WORKER_LOCK_PATH, JSON.stringify({
      pid: process.pid,
      worker: WORKER_ID,
      workerKind: WORKER_KIND,
      startedAt: new Date().toISOString(),
    }), { flag: "wx" });
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    let existing = null;
    try {
      existing = JSON.parse(fs.readFileSync(WORKER_LOCK_PATH, "utf8"));
    } catch (_) {
      existing = null;
    }
    if (existing && isProcessAlive(existing.pid)) {
      console.log(JSON.stringify({
        worker: WORKER_ID,
        step: "worker_lock",
        status: "skip",
        message: `Worker ${WORKER_KIND} deja actif`,
        activeWorker: existing.worker || null,
        activePid: existing.pid || null,
      }));
      process.exit(0);
    }
    fs.rmSync(WORKER_LOCK_PATH, { force: true });
    fs.writeFileSync(WORKER_LOCK_PATH, JSON.stringify({
      pid: process.pid,
      worker: WORKER_ID,
      workerKind: WORKER_KIND,
      startedAt: new Date().toISOString(),
      replacedStaleLock: existing,
    }), { flag: "wx" });
  }

  const release = () => {
    try {
      const current = JSON.parse(fs.readFileSync(WORKER_LOCK_PATH, "utf8"));
      if (Number(current.pid) === process.pid) {
        fs.rmSync(WORKER_LOCK_PATH, { force: true });
      }
    } catch (_) {
      // Best effort cleanup only.
    }
  };
  process.once("exit", release);
  process.once("SIGINT", () => {
    release();
    process.exit(130);
  });
  process.once("SIGTERM", () => {
    release();
    process.exit(143);
  });
}

const HEKTOR_STATUS_CONFIG = {
  active: { hektorValue: "2", label: "Actif", diffusable: "1" },
  offer: { hektorValue: "3", label: "Sous offre", transactionMode: "annonce-SuiviVente-offre-createOffre" },
  compromise: { hektorValue: "4", label: "Sous compromis", transactionMode: "annonce-SuiviVente-compromis-createCompromis" },
  sold: { hektorValue: "5", label: "Vendu", transactionMode: "annonce-SuiviVente-vente-createVente" },
  closed: { hektorValue: "6", label: "Mandat clos", diffusable: "0" },
};

function normalizeHektorStatusTarget(value) {
  const text = String(value || "").trim().toLowerCase();
  const aliases = {
    actif: "active",
    active: "active",
    offre: "offer",
    "sous offre": "offer",
    offer: "offer",
    compromis: "compromise",
    "sous compromis": "compromise",
    compromise: "compromise",
    vendu: "sold",
    sold: "sold",
    clos: "closed",
    "mandat clos": "closed",
    closed: "closed",
  };
  const target = aliases[text] || text;
  if (!HEKTOR_STATUS_CONFIG[target]) throw new Error(`Statut Hektor non supporte: ${value}`);
  return target;
}

function normalizeStatusFrenchDate(value, fallback = new Date()) {
  const raw = String(value || "").trim();
  if (/^\d{2}-\d{2}-\d{4}$/.test(raw)) return raw;
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    const [year, month, day] = raw.split("-");
    return `${day}-${month}-${year}`;
  }
  const date = fallback instanceof Date && !Number.isNaN(fallback.getTime()) ? fallback : new Date();
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return `${day}-${month}-${date.getFullYear()}`;
}

function cleanMoneyValue(value, fallback = "") {
  const raw = String(value == null ? "" : value).replace(/\s+/g, "").replace(",", ".").trim();
  return raw || String(fallback || "");
}

function htmlInputValue(html, key) {
  const source = String(html || "");
  const patterns = [
    new RegExp(`<input\\b[^>]*(?:name|id)=["']${key}["'][^>]*>`, "i"),
    new RegExp(`<input\\b[^>]*(?:name|id)=["'][^"']*["'][^>]*(?:name|id)=["']${key}["'][^>]*>`, "i"),
  ];
  for (const pattern of patterns) {
    const match = source.match(pattern);
    if (!match) continue;
    const value = htmlAttrValue(match[0], "value");
    if (value != null) return value;
  }
  return "";
}

function appendIfValue(params, key, value) {
  const clean = String(value == null ? "" : value).trim();
  if (clean) params.set(key, clean);
}

async function setHektorAnnonceStatusValue(job, annonceId, config, reason) {
  await hektorFetch(`${XMLRPC_URL}?${new URLSearchParams({
    mode: "upval",
    id: annonceId,
    champ: "status",
    val: config.hektorValue,
  }).toString()}`, {
    headers: { Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}` },
  });
  if (config.diffusable != null) {
    await hektorFetch(`${XMLRPC_URL}?${new URLSearchParams({
      mode: "upval",
      id: annonceId,
      champ: "diffusable",
      val: config.diffusable,
    }).toString()}`, {
      headers: { Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}` },
    });
  }
  await logJob(job.id, "hektor_status", "done", `Statut Hektor ${config.label} envoye`, {
    hektor_annonce_id: annonceId,
    status_value: config.hektorValue,
    diffusable: config.diffusable == null ? null : config.diffusable,
    reason,
  });
}

function normalizeStatusTransactionPayload(payload, config, initHtml) {
  const amount = cleanMoneyValue(payload.amount || payload.montant_offre || payload.montant || payload.price, htmlInputValue(initHtml, "montant_offre") || htmlInputValue(initHtml, "montantOffre"));
  const salePrice = cleanMoneyValue(payload.sale_price || payload.prix_de_vente || payload.prixDeVente || payload.price, htmlInputValue(initHtml, "offre_prixDeVente") || htmlInputValue(initHtml, "prixDeVente") || amount);
  const date = normalizeStatusFrenchDate(payload.transaction_date || payload.date || payload.date_offre || payload.date_compromis || payload.date_vente);
  const validity = String(payload.validity_days || payload.nb_jours_validite || payload.nbJoursValidite || htmlInputValue(initHtml, "availability") || "10").trim();
  const selectedMandat = String(payload.selected_mandat || payload.selectedMandat || htmlInputValue(initHtml, "selectedMandatId") || "").trim();
  const mandat = String(payload.mandat || htmlInputValue(initHtml, "id_mandat") || selectedMandat || "").trim();
  const negotiator = String(payload.instigateur || payload.negociateur_id || htmlInputValue(initHtml, "negociateurSelect") || "").trim();
  const agency = String(payload.agence_reseau_selected || payload.agenceReseauSelected || "").trim();
  const buyer = String(payload.acquereur_id || payload.buyer_contact_id || payload.id_acquereur || "").trim();
  const notary = String(payload.notaire_id || payload.buyer_notary_id || payload.id_notaire || "").trim();
  const fees = cleanMoneyValue(payload.buyer_fees || payload.montant_honoraire_sortie || payload.montantHonoraireSortie, htmlInputValue(initHtml, "offre_montant_honoraires_0") || "0");
  const feesRate = cleanMoneyValue(payload.buyer_fees_rate || payload.taux_honoraire_sortie || payload.tauxHonoraireSortie, htmlInputValue(initHtml, "offreHonorairesSortiePercent_1") || "0");
  if (!amount && (config.hektorValue === "3" || config.hektorValue === "4")) throw new Error("Montant requis pour ce changement de statut");
  if (!salePrice && (config.hektorValue === "4" || config.hektorValue === "5")) throw new Error("Prix de vente requis pour ce changement de statut");
  return {
    amount,
    salePrice: salePrice || amount,
    date,
    validity,
    selectedMandat,
    mandat,
    negotiator,
    agency,
    buyer,
    notary,
    fees,
    feesRate,
    isWritten: payload.is_written === false || payload.isWrite === false || payload.is_written === "0" ? "0" : "1",
    sequestration: cleanMoneyValue(payload.sequestre || payload.sequestration, htmlInputValue(initHtml, "sequestre") || "0"),
    netSellerPrice: cleanMoneyValue(payload.net_seller_price || payload.prix_net_vendeur || payload.prixNetVendeur, htmlInputValue(initHtml, "prixNetVendeur") || ""),
  };
}

async function submitHektorTransactionStatus(job, annonceId, target, config, payload) {
  const initBody = new URLSearchParams({
    mode: config.transactionMode,
    idAnnonce: annonceId,
    init: "1",
  });
  if (target === "compromise" || target === "sold") initBody.set("initBasket", "true");
  const init = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: initBody,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`,
      Accept: "application/json, text/javascript, */*; q=0.01",
    },
    timeoutMs: 60000,
  });
  const initJson = parseHektorJson(init.text, `init ${config.label}`);
  const initHtml = String(
    initJson.html ||
    (initJson.data && (initJson.data.defaultTemplate || initJson.data.html || initJson.data.template)) ||
    ""
  );
  const tx = normalizeStatusTransactionPayload(payload, config, initHtml);
  const body = new URLSearchParams();
  body.set("mode", config.transactionMode);
  body.set("idAnnonce", annonceId);
  body.append("actionContainer[]", "save");
  body.append("actionContainer[]", "treat");
  appendIfValue(body, "mandat", tx.mandat);
  appendIfValue(body, "selectedMandat", tx.selectedMandat);
  appendIfValue(body, "instigateur", tx.negotiator);
  appendIfValue(body, "agenceReseauSelected", tx.agency);
  appendIfValue(body, "acquereurs[]", tx.buyer);
  appendIfValue(body, "notairesAcquereur[]", tx.notary);
  body.set("fromContact", "0");

  if (target === "offer") {
    body.set("idOffre", "");
    body.set("montantOffre", tx.amount);
    body.set("dateOffre", tx.date);
    body.set("nbJoursValidite", tx.validity);
    body.set("prixDeVente", tx.salePrice);
    if (tx.isWritten === "1") body.set("isWrite", "1");
    body.set("montantHonoraireSortie", tx.fees);
    body.set("tauxHonoraireSortie", tx.feesRate);
    body.append("containerModule[]", "infosFinancieres");
    body.append("containerModule[]", "acquereurNotaireAutresProspects");
    body.append("containerModule[]", "AnnoncesOffreMandat");
    body.set("containerName", "PopinOffre");
  } else if (target === "compromise") {
    body.set("idCompromis", "");
    body.set("dateCompromis", tx.date);
    body.set("dateSignatureActe", normalizeStatusFrenchDate(payload.signature_date || payload.date_signature_acte || payload.dateSignatureActe));
    body.set("nbJoursRetractation", String(payload.retraction_days || payload.nb_jours_retractation || "10"));
    body.set("prixPublique", tx.amount || tx.salePrice);
    body.set("prixDeVente", tx.salePrice);
    body.set("prixNetVendeur", tx.netSellerPrice || tx.salePrice);
    body.set("sequestre", tx.sequestration);
    body.set("montantHonoraireSortie", tx.fees);
    body.set("tauxHonoraireSortie", tx.feesRate);
    body.append("containerModule[]", "infosFinancieres");
    body.append("containerModule[]", "acquereurNotaireAutresProspects");
    body.append("containerModule[]", "AnnoncesCompromisMandat");
    body.set("containerName", "PopinCompromis");
  } else if (target === "sold") {
    body.set("idVente", "");
    body.set("dateVente", tx.date);
    body.set("prixDeVente", tx.salePrice);
    body.set("prixNetVendeur", tx.netSellerPrice || tx.salePrice);
    body.set("montantHonoraireSortie", tx.fees);
    body.set("tauxHonoraireSortie", tx.feesRate);
    body.append("containerModule[]", "infosFinancieres");
    body.append("containerModule[]", "acquereurNotaireAutresProspects");
    body.append("containerModule[]", "AnnoncesVenteMandat");
    body.set("containerName", "PopinVente");
  }

  const saved = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`,
      Accept: "application/json, text/javascript, */*; q=0.01",
    },
    timeoutMs: 60000,
  });
  const savedJson = parseHektorJson(saved.text, `save ${config.label}`);
  if (savedJson.error && !savedJson.returnValue) {
    throw new Error(`Hektor refuse ${config.label}: ${stripHtml(savedJson.html || saved.text).slice(0, 600)}`);
  }
  await logJob(job.id, "hektor_transaction", "done", `Transaction ${config.label} envoyee`, {
    hektor_annonce_id: annonceId,
    target,
    return_keys: savedJson.returnValue ? Object.keys(savedJson.returnValue) : [],
  });
  await setHektorAnnonceStatusValue(job, annonceId, config, `transaction_${target}`);
  return {
    init_error: initJson.error === true,
    transaction_returned: Boolean(savedJson.returnValue),
    transaction_keys: savedJson.returnValue ? Object.keys(savedJson.returnValue) : [],
  };
}

async function submitHektorClosedStatus(job, annonceId, config, payload) {
  const body = new URLSearchParams({
    mode: "annonce-SuiviVente-saveMandatClos",
    idAnnonce: annonceId,
    state: String(payload.close_state || payload.state || "autre"),
    reason: String(payload.close_reason || payload.reason || "Cloture demandee depuis l app").trim(),
    idConfrere: String(payload.confrere_id || payload.idConfrere || "").trim(),
    prix: cleanMoneyValue(payload.close_price || payload.price || ""),
  });
  await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`,
    },
    timeoutMs: 60000,
  });
  await setHektorAnnonceStatusValue(job, annonceId, config, "closed_form");
  return { closed_reason: body.get("reason"), closed_state: body.get("state") };
}

async function handleChangeHektorAnnonceStatus(job) {
  const payload = safeJsonParse(job.payload_json);
  const target = normalizeHektorStatusTarget(payload.target_status || payload.status || payload.targetStatus);
  const config = HEKTOR_STATUS_CONFIG[target];
  let dossier = null;
  try {
    dossier = await loadDossier(job);
  } catch (error) {
    if (!job.hektor_annonce_id) throw error;
    dossier = {
      app_dossier_id: job.app_dossier_id || payload.app_dossier_id || null,
      hektor_annonce_id: String(job.hektor_annonce_id),
      negociateur_email: payload.hektor_user_email || payload.negociateur_email || null,
    };
  }
  const annonceId = String(dossier.hektor_annonce_id || job.hektor_annonce_id || "").trim();
  if (!annonceId) throw new Error("hektor_annonce_id required");

  await ensureAdminHektorWriteSession(job, "change_status_admin_login");
  if (config.transactionMode) {
    await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: false, preferDossierOwner: true, required: true });
  }

  await logJob(job.id, "hektor_status", "running", `Changement statut Hektor vers ${config.label}`, {
    hektor_annonce_id: annonceId,
    target_status: target,
    app_dossier_id: dossier.app_dossier_id || null,
  });
  const before = await fetchHektorPropertyByIdBestEffort(job, annonceId, "hektor_status_verify_before");
  let transactionResult = null;
  try {
    transactionResult = config.transactionMode
      ? await submitHektorTransactionStatus(job, annonceId, target, config, payload)
      : target === "closed"
        ? await submitHektorClosedStatus(job, annonceId, config, payload)
        : await setHektorAnnonceStatusValue(job, annonceId, config, "direct_status");
  } finally {
    if (config.transactionMode) {
      await returnAdminHektorSessionBestEffort(job, "change_status_return_admin");
    }
  }

  await sleep(2500);
  const after = await fetchHektorPropertyByIdBestEffort(job, annonceId, "hektor_status_verify_after");
  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
    reason: "change_hektor_annonce_status",
    priority: 72,
  });

  return {
    status: "changed",
    hektor_annonce_id: annonceId,
    app_dossier_id: dossier.app_dossier_id || null,
    target_status: target,
    target_label: config.label,
    before_property: before && before.property ? {
      id: before.property.id,
      folderNumber: before.property.folderNumber || null,
      status: before.property.status || null,
      isArchived: before.property.isArchived === true,
    } : null,
    after_property: after && after.property ? {
      id: after.property.id,
      folderNumber: after.property.folderNumber || null,
      status: after.property.status || null,
      isArchived: after.property.isArchived === true,
    } : null,
    transaction: transactionResult || null,
    sync_job: syncJob,
  };
}

async function handleAssignHektorAnnonceNegotiator(job) {
  const payload = safeJsonParse(job.payload_json);
  let dossier = null;
  try {
    dossier = await loadDossier(job);
  } catch (error) {
    if (!job.hektor_annonce_id) throw error;
    dossier = {
      app_dossier_id: job.app_dossier_id || payload.app_dossier_id || null,
      hektor_annonce_id: String(job.hektor_annonce_id),
      negociateur_email: null,
    };
  }
  const annonceId = String(dossier.hektor_annonce_id || job.hektor_annonce_id || "").trim();
  const targetId = String(payload.target_hektor_user_id || payload.hektor_user_id || "").trim();
  if (!annonceId) throw new Error("hektor_annonce_id required");
  if (!/^\d+$/.test(targetId)) throw new Error("target_hektor_user_id numerique requis");

  const directoryUser = await loadHektorDirectoryUserById(targetId).catch(() => null);
  if (!directoryUser || !directoryUser.id_user || String(directoryUser.user_type || "").toUpperCase() !== "NEGO") {
    throw new Error(`Negociateur Hektor actif introuvable dans app_user_directory pour idUser ${targetId}`);
  }

  const agencyContext = await resolveHektorAnnonceAgencyContext(annonceId, {
    idUser: targetId,
    email: directoryUser.email || payload.target_hektor_user_email || payload.hektor_user_email || null,
    agencyId: payload.target_hektor_agence_id || payload.hektor_agence_id || null,
  });
  if (!agencyContext || !agencyContext.agency_id_user) {
    throw new Error(`Contexte agence Hektor introuvable pour l'annonce ${annonceId}`);
  }
  if (!agencyContext.target_found || !agencyContext.target_hektor_negociateur_id) {
    throw new Error(`Ce negociateur n'est pas rattache a l'agence Hektor ${agencyContext.agency_label || agencyContext.hektor_agence_id || ""}. Choisis un negociateur de cette agence ou change d'abord l'agence dans Hektor.`);
  }
  const targetNegotiatorId = String(agencyContext.target_hektor_negociateur_id);
  const activeAgencyRows = await loadHektorNegotiatorAgencyRows({
    userId: targetId,
    agencyId: agencyContext.hektor_agence_id || null,
    limit: 25,
  }).catch(() => []);
  const activeAgencyRow = activeAgencyRows.find((row) => String(row.hektor_negociateur_id || "").trim() === targetNegotiatorId);
  if (!activeAgencyRow) {
    throw new Error(`Negociateur Hektor ${targetId} non confirme actif pour l'agence ${agencyContext.agency_label || agencyContext.hektor_agence_id || ""}.`);
  }

  await ensureAdminHektorWriteSession(job, "assign_negotiator_admin_login");
  if (agencyContext.agency_changed) {
    await logJob(job.id, "hektor_assign_agency", "running", "Changement de l'agence Hektor", {
      hektor_annonce_id: annonceId,
      current_hektor_agence_id: agencyContext.current_hektor_agence_id || null,
      target_hektor_agence_id: agencyContext.hektor_agence_id || null,
      target_agency_label: agencyContext.agency_label || null,
    });
    await hektorFetch(`${XMLRPC_URL}?${new URLSearchParams({
      mode: "upval",
      id: annonceId,
      champ: "agence",
      val: String(agencyContext.hektor_agence_id),
    })}`, {
      headers: {
        Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`,
      },
    });
    await sleep(1500);
  }
  let agencySwitchAttempted = false;
  try {
    agencySwitchAttempted = true;
    await ensureHektorAgencySession(job, agencyContext, "assign_negotiator_agency_switch");
    await logJob(job.id, "hektor_assign_negotiator", "running", "Affectation du negociateur Hektor", {
      hektor_annonce_id: annonceId,
      agency_id_user: agencyContext.agency_id_user,
      agency_label: agencyContext.agency_label || null,
      target_hektor_user_id: targetId,
      target_hektor_negociateur_id: targetNegotiatorId,
      target_label: directoryUser.display_name || null,
      target_email: directoryUser.email || null,
    });

    const before = await fetchHektorPropertyByIdBestEffort(job, annonceId, "hektor_assign_negotiator_verify_before");
    await hektorFetch(`${XMLRPC_URL}?${new URLSearchParams({
      mode: "upval",
      id: annonceId,
      champ: "NEGOCIATEUR",
      val: targetNegotiatorId,
    })}`, {
      headers: {
        Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`,
      },
    });

    const after = await fetchHektorPropertyByIdBestEffort(job, annonceId, "hektor_assign_negotiator_verify_after");
    const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
      reason: "assign_hektor_annonce_negotiator",
      priority: 82,
    });

    return {
      status: "assigned",
      hektor_annonce_id: annonceId,
      app_dossier_id: dossier.app_dossier_id || null,
      agency_id_user: agencyContext.agency_id_user,
      agency_label: agencyContext.agency_label || null,
      target_hektor_user_id: targetId,
      target_hektor_negociateur_id: targetNegotiatorId,
      target_label: directoryUser.display_name || null,
      target_email: directoryUser.email || null,
      confirmed_negotiator_id: null,
      before_property: before && before.property ? {
        id: before.property.id,
        folderNumber: before.property.folderNumber || null,
        status: before.property.status || null,
        isArchived: before.property.isArchived === true,
      } : null,
      after_property: after && after.property ? {
        id: after.property.id,
        folderNumber: after.property.folderNumber || null,
        status: after.property.status || null,
        isArchived: after.property.isArchived === true,
      } : null,
      sync_job: syncJob,
    };
  } finally {
    if (agencySwitchAttempted) {
      await returnAdminHektorSessionBestEffort(job, "assign_negotiator_return_admin");
    }
  }
}

async function handleLinkHektorMandant(job) {
  const payload = safeJsonParse(job.payload_json);
  const dossier = await loadDossier(job);
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });

  const contactId = String(payload.contact_id || payload.hektor_contact_id || "").trim();
  if (!/^\d+$/.test(contactId)) throw new Error("contact_id Hektor numerique requis");

  const annonceId = String(dossier.hektor_annonce_id);
  const linkResult = await linkHektorMandantContact(job, annonceId, contactId, "hektor_mandant");

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
    reason: "link_hektor_mandant",
    priority: 80,
  });

  return {
    status: linkResult.status,
    hektor_annonce_id: annonceId,
    hektor_contact_id: contactId,
    wait_attempts: linkResult.waitAttempts,
    sync_job: syncJob,
  };
}

async function waitForHektorMandantLink(job, annonceId, contactId, step, options = {}) {
  const attempts = Number(options.attempts || 4);
  const intervalMs = Number(options.intervalMs || 650);
  for (let index = 0; index < attempts; index += 1) {
    const list = await fetchHektorProspectsList(annonceId);
    if (hektorProspectLinkedInHtml(list.text, contactId, annonceId)) {
      return { status: "confirmed", waitAttempts: index + 1 };
    }
    if (index < attempts - 1) await sleep(intervalMs);
  }
  throw new Error(`Association mandant non confirmee pour contact ${contactId} sur annonce ${annonceId}`);
}

async function linkHektorMandantContact(job, annonceId, contactId, step = "hektor_mandant") {
  const before = await fetchHektorProspectsList(annonceId);
  if (hektorProspectLinkedInHtml(before.text, contactId, annonceId)) {
    return {
      status: "already_linked",
      hektor_annonce_id: annonceId,
      hektor_contact_id: contactId,
      waitAttempts: 0,
    };
  }

  await logJob(job.id, step, "running", "Association mandant/proprietaire dans Hektor", {
    hektor_annonce_id: annonceId,
    hektor_contact_id: contactId,
  });

  await hektorFetch(`${XMLRPC_URL}?mode=selectnouveauproprio_sup&id=${encodeURIComponent(contactId)}&idann=${encodeURIComponent(annonceId)}`);
  const confirmed = await waitForHektorMandantLink(job, annonceId, contactId, `${step}_confirm`);
  return {
    status: "linked",
    hektor_annonce_id: annonceId,
    hektor_contact_id: contactId,
    waitAttempts: confirmed.waitAttempts,
  };
}

function cleanString(value) {
  const text = String(value || "").trim();
  return text || null;
}

function firstDefined(source, keys) {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(source || {}, key)) return source[key];
  }
  return undefined;
}

function normalizeOptionalBoolean(value) {
  if (value === undefined || value === null || value === "") return null;
  if (value === true || value === 1) return true;
  if (value === false || value === 0) return false;
  const text = String(value).trim().toLowerCase();
  if (["true", "1", "yes", "oui", "on", "enabled", "active"].includes(text)) return true;
  if (["false", "0", "no", "non", "off", "disabled", "inactive"].includes(text)) return false;
  return null;
}

function normalizeOptionalFrenchDate(value) {
  const text = String(value || "").trim();
  if (!text || text === "00-00-0000") return text ? "00-00-0000" : "";
  const iso = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (iso) return `${iso[3]}-${iso[2]}-${iso[1]}`;
  const compactFr = text.match(/^(\d{2})(\d{2})(\d{4})$/);
  if (compactFr) return `${compactFr[1]}-${compactFr[2]}-${compactFr[3]}`;
  const fr = text.match(/^(\d{2})[/-](\d{2})[/-](\d{4})$/);
  if (fr) return `${fr[1]}-${fr[2]}-${fr[3]}`;
  throw new Error("date_naissance contact invalide, format attendu jj-mm-aaaa");
}

function todayFrenchDate() {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, "0");
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${day}-${month}-${now.getFullYear()}`;
}

function normalizeFrenchDate(value) {
  const text = String(value || "").trim();
  if (!text) return todayFrenchDate();
  const iso = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (iso) return `${iso[3]}-${iso[2]}-${iso[1]}`;
  const fr = text.match(/^(\d{2})[/-](\d{2})[/-](\d{4})$/);
  if (fr) return `${fr[1]}-${fr[2]}-${fr[3]}`;
  throw new Error("date_debut mandat invalide, format attendu jj-mm-aaaa");
}

function normalizeMandatContactIds(payload) {
  const raw = Array.isArray(payload.mandant_contact_ids)
    ? payload.mandant_contact_ids
    : Array.isArray(payload.mandantContactIds)
      ? payload.mandantContactIds
      : typeof payload.idMandants === "string"
        ? payload.idMandants.split("|")
        : [];
  const ids = [];
  const seen = new Set();
  for (const value of raw) {
    const id = String(value || "").trim();
    if (/^\d+$/.test(id) && !seen.has(id)) {
      ids.push(id);
      seen.add(id);
    }
  }
  return ids;
}

function normalizeInitialMandantContactIds(payload) {
  const raw = Array.isArray(payload.initial_mandant_contact_ids)
    ? payload.initial_mandant_contact_ids
    : Array.isArray(payload.initialMandantContactIds)
      ? payload.initialMandantContactIds
      : [
          payload.initial_mandant_contact_id,
          payload.initialMandantContactId,
          payload.contact_id_mandant,
          payload.hektor_mandant_contact_id,
        ];
  const ids = [];
  const seen = new Set();
  for (const value of raw) {
    const id = String(value || "").trim();
    if (/^\d+$/.test(id) && !seen.has(id)) {
      ids.push(id);
      seen.add(id);
    }
  }
  return ids;
}

function normalizeHektorMandatPayload(payload) {
  const typeMandat = cleanString(payload.type_mandat || payload.typeMandat) || "Mandat de vente";
  const subTypeMandat = cleanString(payload.sub_type_mandat || payload.subTypeMandat || payload.sub_type) || typeMandat;
  const durationText = String(payload.duree_mandat || payload.duree || payload.duration || "12").trim();
  if (!/^\d+$/.test(durationText) || Number(durationText) <= 0 || Number(durationText) > 120) {
    throw new Error("duree_mandat invalide");
  }
  const tacite = payload.tacite_reconduction ?? payload.taciteReconduction ?? payload.tr ?? true;
  const taciteValue = tacite === true || tacite === "true" || tacite === "1" || tacite === 1 ? "1" : "0";
  return {
    typeMandat,
    subTypeMandat,
    dateDebut: normalizeFrenchDate(payload.date_debut || payload.dateDebut),
    duree: durationText,
    taciteReconduction: taciteValue,
    mandantContactIds: normalizeMandatContactIds(payload),
  };
}

function parseHektorJson(text, step) {
  try {
    return JSON.parse(String(text || ""));
  } catch (error) {
    throw new Error(`Reponse Hektor JSON invalide ${step}: ${String(text || "").slice(0, 500)}`);
  }
}

async function hektorProtexaGetJson(job, step, params) {
  const url = `${XMLRPC_URL}?${params.toString()}`;
  const response = await hektorFetch(url, {
    headers: {
      Accept: "application/json, text/javascript, */*; q=0.01",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien/mandat-prix&id=${encodeURIComponent(params.get("id") || params.get("idann") || "")}`,
    },
  });
  const parsed = parseHektorJson(response.text, step);
  if (parsed && typeof parsed === "object" && (parsed.error || parsed.errors || parsed.err)) {
    throw new Error(`Hektor ${step} refuse: ${JSON.stringify(parsed).slice(0, 800)}`);
  }
  await logJob(job.id, step, "done", `Etape mandat ${step} OK`, parsed);
  return parsed;
}

function mandatIdMandantsValue(ids) {
  return ids.map((id) => `${id}|`).join("");
}

async function handleCreateHektorMandatAutoNumber(job) {
  const payload = safeJsonParse(job.payload_json);
  let dossier = null;
  try {
    dossier = await loadDossier(job);
  } catch (error) {
    if (!job.hektor_annonce_id || !(payload.hektor_user_id || payload.hektor_id_user || payload.target_hektor_user_id || payload.hektor_user_email)) throw error;
    dossier = {
      app_dossier_id: job.app_dossier_id || payload.app_dossier_id || null,
      hektor_annonce_id: String(job.hektor_annonce_id),
      negociateur_email: payload.hektor_user_email || null,
    };
  }
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });

  const annonceId = String(dossier.hektor_annonce_id || job.hektor_annonce_id || "").trim();
  if (!annonceId) throw new Error("hektor_annonce_id requis pour generer un mandat");
  const mandat = normalizeHektorMandatPayload(payload);

  await logJob(job.id, "hektor_mandat_number", "running", "Preparation generation numero mandat Hektor", {
    hektor_annonce_id: annonceId,
    type_mandat: mandat.typeMandat,
    sub_type_mandat: mandat.subTypeMandat,
    date_debut: mandat.dateDebut,
    duree: mandat.duree,
    mandant_contact_ids_payload: mandat.mandantContactIds,
  });

  await hektorFetch(`${XMLRPC_URL}?mode=chargeannonce_MandatPrix&id=${encodeURIComponent(annonceId)}&lang=fr`, {
    headers: { Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien/mandat-prix&id=${encodeURIComponent(annonceId)}` },
  });
  await hektorFetch(`${XMLRPC_URL}?mode=protexa-mandat&mandat=0&idann=${encodeURIComponent(annonceId)}`, {
    headers: { Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien/mandat-prix&id=${encodeURIComponent(annonceId)}` },
  });
  await hektorFetch(`${XMLRPC_URL}?mode=protexa-listeTypeMandat`, {
    method: "POST",
    body: new URLSearchParams(),
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien/mandat-prix&id=${encodeURIComponent(annonceId)}`,
    },
  });

  let mandantIds = mandat.mandantContactIds;
  const prospects = await fetchHektorProspectsList(annonceId);
  if (!mandantIds.length) {
    mandantIds = parseHektorLinkedMandantContactIds(prospects.text, annonceId);
  }
  if (!mandantIds.length) {
    throw new Error("Aucun mandant Hektor rattache a cette annonce: cree ou associe un mandant avant de generer le numero de mandat.");
  }
  for (const contactId of mandantIds) {
    if (!hektorProspectLinkedInHtml(prospects.text, contactId, annonceId)) {
      throw new Error(`Le contact ${contactId} n'est pas confirme comme mandant de l'annonce ${annonceId}`);
    }
  }

  const step1 = await hektorProtexaGetJson(job, "hektor_mandat_step1_number", new URLSearchParams({
    mode: "protexa-valideStep1",
    id: annonceId,
    numMandat: "0",
  }));
  const numeroMandat = String(step1 && step1.mandat && step1.mandat.numero ? step1.mandat.numero : "").trim();
  if (!numeroMandat) {
    throw new Error(`Numero de mandat non retourne par Hektor: ${JSON.stringify(step1).slice(0, 800)}`);
  }

  await hektorProtexaGetJson(job, "hektor_mandat_step2_type", new URLSearchParams({
    mode: "protexa-valideStep2",
    id: annonceId,
    numMandat: numeroMandat,
    typeMandat: mandat.typeMandat,
    subType: mandat.subTypeMandat,
  }));
  await hektorProtexaGetJson(job, "hektor_mandat_step3_dates", new URLSearchParams({
    mode: "protexa-valideStep3",
    id: annonceId,
    numMandat: numeroMandat,
    date_debut: mandat.dateDebut,
    duree: mandat.duree,
    TR: mandat.taciteReconduction,
  }));
  await hektorProtexaGetJson(job, "hektor_mandat_step4_mandants", new URLSearchParams({
    mode: "protexa-valideStep4",
    id: annonceId,
    numMandat: numeroMandat,
    idMandants: mandatIdMandantsValue(mandantIds),
  }));

  const step5 = await hektorFetch(`${XMLRPC_URL}?${new URLSearchParams({
    mode: "protexa-valideStep5",
    id: annonceId,
    numMandat: numeroMandat,
  }).toString()}`, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien/mandat-prix&id=${encodeURIComponent(annonceId)}`,
    },
  });
  await logJob(job.id, "hektor_mandat_step5_finish", "done", "Mandat Hektor finalise", {
    hektor_annonce_id: annonceId,
    numero_mandat: numeroMandat,
    response_preview: step5.text.slice(0, 500),
  });

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
    reason: "create_hektor_mandat_auto_number",
    priority: 70,
  });

  return {
    status: "mandat_created",
    hektor_annonce_id: annonceId,
    numero_mandat: numeroMandat,
    mandat_contact_ids: mandantIds,
    type_mandat: mandat.typeMandat,
    sub_type_mandat: mandat.subTypeMandat,
    date_debut: mandat.dateDebut,
    duree_mandat: mandat.duree,
    tacite_reconduction: mandat.taciteReconduction,
    sync_job: syncJob,
  };
}

function replaceParam(values, name, value) {
  values.delete(name);
  values.append(name, value == null ? "" : String(value));
}

function replaceFirstArrayParam(values, name, value) {
  values.delete(name);
  values.append(name, value == null ? "" : String(value));
}

async function fetchHektorManualMandantForm(options = {}) {
  const qualification = cleanString(options.qualification) || "3";
  const statut = cleanString(options.statut) || "contact_seule";
  const negotiatorId = cleanString(options.negotiatorId || options.idNego);
  const body = new URLSearchParams({
    mode: "contacts-actions-addManuelContactFromOtherObject",
    idNego: negotiatorId,
    statut,
    metier: "",
    inputId: "",
    qualification,
    ihmCenter: "",
  });
  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: ADMIN_URL,
    },
  });
  const parsed = JSON.parse(response.text);
  return String(parsed || "");
}

async function fetchHektorContactEditForm(contactId) {
  const id = encodeURIComponent(String(contactId));
  const group = "contacts,pilotage_accueil_contact,mefContacts/accueilContact";
  const response = await hektorFetch(`${XMLRPC_URL}?mode=contacts-ihmChargeGroupe&id=${id}&consultMode=editer&ajax=true&group=${encodeURIComponent(group)}`, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${id}`,
    },
  });
  try {
    const parsed = JSON.parse(response.text);
    if (typeof parsed === "string") return parsed;
  } catch (_) {
    // The same endpoint can return either raw HTML or a JSON-encoded HTML string.
  }
  return String(response.text || "");
}

function normalizeHektorContactQualification(value, fallback = "2") {
  const text = String(cleanString(value) || "").toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9_ -]/g, "")
    .replace(/\s+/g, "_");
  const map = {
    "1": "1",
    locataire: "1",
    tenant: "1",
    "2": "2",
    acquereur: "2",
    acheteur: "2",
    buyer: "2",
    "3": "3",
    proprietaire: "3",
    mandant: "3",
    vendeur: "3",
    owner: "3",
    "4": "4",
    partenaire: "4",
    notaire: "4",
    partner: "4",
  };
  return map[text] || map[String(value || "").trim()] || fallback;
}

function normalizeHektorContactStatus(value, fallback = "1") {
  const text = String(cleanString(value) || "").toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9_ -]/g, "")
    .replace(/\s+/g, "_");
  const map = {
    "1": "1",
    personne_seule: "1",
    contact_seule: "1",
    seul: "1",
    single: "1",
    "2": "2",
    couple: "2",
    "3": "3",
    personne_morale: "3",
    societe: "3",
    company: "3",
    "4": "4",
    personne_physique: "4",
    partenaire_physique: "4",
    partner_person: "4",
  };
  return map[text] || map[String(value || "").trim()] || fallback;
}

function hektorManualContactFormStatus(contactStatus, qualification) {
  const status = normalizeHektorContactStatus(contactStatus, "1");
  const qual = normalizeHektorContactQualification(qualification, "2");
  if (qual === "4" && status === "4") return "partenaire_physique";
  if (qual === "4" && status === "3") return "partenaire_morale";
  if (status === "2") return "contact_couple";
  if (status === "3") return "contact_morale";
  return "contact_seule";
}

function hektorContactEditFormExists(html) {
  const source = String(html || "");
  if (!source.trim()) return false;
  const values = extractHektorFormValues(source, "mefContacts/contacts_full_accueil");
  return values.has("nom") || values.has("prenom") || values.has("email[]") || /idContact/i.test(source);
}

async function fetchHektorContactBeforeDelete(job, contactId) {
  try {
    const html = await fetchHektorContactEditForm(contactId);
    const values = extractHektorFormValues(html, "mefContacts/contacts_full_accueil");
    return {
      exists: hektorContactEditFormExists(html),
      nom: values.get("nom") || null,
      prenom: values.get("prenom") || null,
      email: values.get("email[]") || null,
      telephone: values.get("telephone[]") || null,
    };
  } catch (error) {
    await logJob(job.id, "hektor_contact_delete_verify", "error", "Verification contact Hektor ignoree avant suppression", {
      hektor_contact_id: String(contactId),
      error: error && error.message ? error.message : String(error),
    });
    return { exists: null, error: error && error.message ? error.message : String(error) };
  }
}

function normalizeHektorContactPayload(payload, options = {}) {
  const source = payload || {};
  const contactId = cleanString(source.hektor_contact_id || source.contact_id || source.id_contact || source.idContact);
  const companyName = cleanString(source.company_name || source.companyName || source.sociale || source.raison_sociale);
  const lastName = cleanString(source.last_name || source.nom || source.name || companyName);
  const firstName = source.first_name !== undefined || source.prenom !== undefined
    ? cleanString(source.first_name || source.prenom) || ""
    : cleanString(source.first_name || source.prenom);
  const legalForm = cleanString(source.legal_form || source.legalForm || source.juridique || source.forme_juridique);
  const siret = cleanString(source.siret || source.siren);
  const partnerJobId = cleanString(source.partner_job_id || source.partnerJobId || source.metier || source.metier_id);
  const website = cleanString(source.website || source.url || source.site_internet);
  const spouseLastName = cleanString(source.spouse_last_name || source.spouseLastName || source.nom_m2 || source.conjoint_nom);
  const spouseFirstName = cleanString(source.spouse_first_name || source.spouseFirstName || source.prenom_m2 || source.conjoint_prenom);
  const spouseEmail = cleanString(source.spouse_email || source.spouseEmail || source.email_m2);
  const spousePhone = cleanString(source.spouse_phone || source.spousePhone || source.telephone_m2 || source.conjoint_phone);
  const spouseAddress = cleanString(source.spouse_address || source.spouseAddress || source.adresse_m2);
  const spousePostalCode = cleanString(source.spouse_postal_code || source.spousePostalCode || source.codeprivee || source.code_m2);
  const spouseCity = cleanString(source.spouse_city || source.spouseCity || source.villeprivee || source.ville_m2);
  const email = source.email !== undefined ? cleanString(source.email) || "" : cleanString(source.email);
  const phone = source.phone !== undefined || source.telephone !== undefined || source.mobile !== undefined
    ? cleanString(source.phone || source.telephone || source.mobile) || ""
    : cleanString(source.phone || source.telephone || source.mobile);
  const phoneSecondary = source.phone_secondary !== undefined || source.telephone_secondaire !== undefined || source.phoneSecondary !== undefined
    ? cleanString(source.phone_secondary || source.telephone_secondaire || source.phoneSecondary) || ""
    : cleanString(source.phone_secondary || source.telephone_secondaire || source.phoneSecondary);
  const civility = source.civility !== undefined || source.civilite !== undefined
    ? cleanString(source.civility || source.civilite) || ""
    : cleanString(source.civility || source.civilite);
  const address = source.address !== undefined || source.adresse !== undefined
    ? cleanString(source.address || source.adresse) || ""
    : cleanString(source.address || source.adresse);
  const city = source.city !== undefined || source.ville !== undefined
    ? cleanString(source.city || source.ville) || ""
    : cleanString(source.city || source.ville);
  const postalCode = source.postal_code !== undefined || source.code_postal !== undefined || source.code !== undefined
    ? cleanString(source.postal_code || source.code_postal || source.code) || ""
    : cleanString(source.postal_code || source.code_postal || source.code);
  const rawBirthDate = firstDefined(source, ["birth_date", "date_naissance", "dateNaissance", "birthDate"]);
  const rawBirthPlace = firstDefined(source, ["birth_place", "lieu_naissance", "lieuNaissance", "birthPlace"]);
  const rawMaritalStatus = firstDefined(source, ["marital_status", "statut_matrimonial", "maritalStatus"]);
  const crmMandateSummaryEnabled = normalizeOptionalBoolean(firstDefined(source, [
    "crm_mandate_summary_enabled",
    "crmMandateSummaryEnabled",
    "mail_nouveau_mandat",
  ]));
  const crmMandateExpirationEnabled = normalizeOptionalBoolean(firstDefined(source, [
    "crm_mandate_expiration_enabled",
    "crmMandateExpirationEnabled",
    "mail_echeance_mandat",
  ]));
  const crmBirthdayEnabled = normalizeOptionalBoolean(firstDefined(source, [
    "crm_birthday_enabled",
    "crmBirthdayEnabled",
    "message_anniversaire_client",
  ]));
  if (options.requireContactId && (!contactId || !/^\d+$/.test(contactId))) {
    throw new Error("contact_id Hektor numerique requis");
  }
  if (options.requireName && !lastName) {
    throw new Error("Nom contact requis");
  }
  if (options.requireReachable && !email && !phone && !phoneSecondary) {
    throw new Error("Email ou telephone requis pour creer un contact Hektor");
  }
  const qualification = normalizeHektorContactQualification(
    source.qualification || source.contact_qualification || source.contact_kind || source.kind,
    "2"
  );
  const contactStatus = normalizeHektorContactStatus(
    source.statut || source.status || source.contact_status || source.person_type || source.personType,
    qualification === "4" ? "3" : "1"
  );
  return {
    contactId,
    civility,
    lastName,
    firstName,
    companyName,
    legalForm,
    siret,
    partnerJobId,
    website,
    spouseLastName,
    spouseFirstName,
    spouseEmail,
    spousePhone,
    spouseAddress,
    spousePostalCode,
    spouseCity,
    email,
    phone,
    phoneSecondary,
    address,
    postalCode,
    city,
    birthDate: rawBirthDate !== undefined ? normalizeOptionalFrenchDate(rawBirthDate) : null,
    birthPlace: rawBirthPlace !== undefined ? cleanString(rawBirthPlace) || "" : null,
    maritalStatus: rawMaritalStatus !== undefined ? cleanString(rawMaritalStatus) || "" : null,
    qualification,
    contactStatus,
    sourceId: cleanString(source.id_source || source.source_id || source.sourceId),
    categoryId: cleanString(source.category_id || source.categorie_id || source.categories),
    comments: source.comments !== undefined || source.commentaires !== undefined
      ? cleanString(source.comments || source.commentaires) || ""
      : null,
    sendRgpdEmail: source.send_rgpd_email === false || source.send_rgpd_email === "false" || source.send_rgpd_email === "0"
      ? false
      : true,
    crmMandateSummaryEnabled,
    crmMandateExpirationEnabled,
    crmBirthdayEnabled,
    hektorUserEmail: cleanString(source.hektor_user_email || source.negociateur_email || source.target_hektor_user_email),
    hektorUserId: cleanString(source.hektor_user_id || source.hektor_id_user || source.target_hektor_user_id),
    hektorUserLabel: cleanString(source.hektor_user_label || source.target_hektor_user_label),
    targetNegotiatorId: cleanString(source.target_hektor_negociateur_id || source.hektor_negociateur_id || source.id_negociateur),
    targetAgencyId: cleanString(source.target_hektor_agence_id || source.hektor_agence_id),
    targetAgencyUserId: cleanString(source.target_agency_id_user || source.agence_id_user || source.agency_id_user),
    targetAgencyLabel: cleanString(source.target_agency_label || source.agence_nom || source.hektor_agence_label),
  };
}

function replaceContactTelephoneParams(values, primaryPhone, secondaryPhone) {
  values.delete("label_telephone[]");
  values.delete("id_telephone[]");
  values.delete("telephone[]");
  if (primaryPhone) {
    values.append("label_telephone[]", "portable");
    values.append("id_telephone[]", "");
    values.append("telephone[]", primaryPhone);
  }
  if (secondaryPhone) {
    values.append("label_telephone[]", "fixe");
    values.append("id_telephone[]", "");
    values.append("telephone[]", secondaryPhone);
  }
  if (!primaryPhone && !secondaryPhone) {
    values.append("label_telephone[]", "portable");
    values.append("id_telephone[]", "");
    values.append("telephone[]", "");
  }
}

function applyHektorContactIdentityValues(values, contact) {
  const isCompany = contact.contactStatus === "3";
  if (isCompany) {
    values.set("sociale", contact.companyName || contact.lastName || "");
    if (contact.legalForm !== null && contact.legalForm !== undefined) values.set("juridique", contact.legalForm || "");
    if (contact.siret !== null && contact.siret !== undefined) values.set("siret", contact.siret || "");
  } else {
    if (contact.civility !== null && contact.civility !== undefined) values.set("civilite", contact.civility || "");
    if (contact.lastName) values.set("nom", contact.lastName);
    if (contact.firstName !== null && contact.firstName !== undefined) values.set("prenom", contact.firstName || "");
  }
  if (contact.partnerJobId !== null && contact.partnerJobId !== undefined) values.set("metier", contact.partnerJobId || "");
  if (contact.website !== null && contact.website !== undefined) values.set("url", contact.website || "");
  if (contact.email !== null && contact.email !== undefined) {
    replaceParam(values, "label_email[]", "email");
    replaceParam(values, "id_email[]", "");
    replaceParam(values, "email[]", contact.email || "");
  }
  if (contact.phone !== null || contact.phoneSecondary !== null) {
    replaceContactTelephoneParams(values, contact.phone || "", contact.phoneSecondary || "");
  }
  if (contact.contactStatus === "2") {
    if (contact.spouseLastName) values.set("nom_m2", contact.spouseLastName);
    if (contact.spouseFirstName !== null && contact.spouseFirstName !== undefined) values.set("prenom_m2", contact.spouseFirstName || "");
    if (contact.spouseEmail !== null && contact.spouseEmail !== undefined) {
      replaceParam(values, "label_email_m2[]", "email");
      replaceParam(values, "id_email_m2[]", "");
      replaceParam(values, "email_m2[]", contact.spouseEmail || "");
    }
    if (contact.spousePhone !== null && contact.spousePhone !== undefined) {
      replaceParam(values, "label_telephone_m2[]", "portable");
      replaceParam(values, "id_telephone_m2[]", "");
      replaceParam(values, "telephone_m2[]", contact.spousePhone || "");
    }
    if (contact.spouseAddress !== null && contact.spouseAddress !== undefined) values.set("adresse_m2", contact.spouseAddress || "");
    if (contact.spouseCity !== null && contact.spouseCity !== undefined) values.set("villeprivee", contact.spouseCity || "");
    if (contact.spousePostalCode !== null && contact.spousePostalCode !== undefined) values.set("codeprivee", contact.spousePostalCode || "");
  }
  if (contact.address !== null && contact.address !== undefined) values.set("adresse", contact.address || "");
  if (contact.city !== null && contact.city !== undefined) values.set("ville", contact.city || "");
  if (contact.postalCode !== null && contact.postalCode !== undefined) values.set("code", contact.postalCode || "");
  if (contact.birthDate !== null && contact.birthDate !== undefined) values.set("dateNaissance", contact.birthDate || "00-00-0000");
  if (contact.birthPlace !== null && contact.birthPlace !== undefined) values.set("lieuNaissance", contact.birthPlace || "");
  if (contact.maritalStatus !== null && contact.maritalStatus !== undefined) values.set("marital_status", contact.maritalStatus || "");
  if (contact.sourceId !== null && contact.sourceId !== undefined) values.set("id_source", contact.sourceId || "");
  if (contact.categoryId !== null && contact.categoryId !== undefined) values.set("categories", contact.categoryId || "");
  if (contact.targetNegotiatorId) values.set("id_negociateur", contact.targetNegotiatorId);
  if (contact.comments !== null && contact.comments !== undefined) {
    values.set("commentaires", contact.comments || "");
    values.set("commentairess", contact.comments || "");
  }
  values.delete("_email_rgpd");
  if (contact.sendRgpdEmail !== false) values.append("_email_rgpd", "1");
}

function contactAgencyExecutionPayload(payload) {
  const executionUserId = cleanString(payload.target_hektor_user_id || payload.hektor_user_id || payload.hektor_id_user);
  if (!executionUserId) return payload;
  return {
    ...payload,
    hektor_user_id: executionUserId,
    hektor_id_user: executionUserId,
    target_hektor_user_id: executionUserId,
    hektor_user_label: payload.target_hektor_user_label || payload.hektor_user_label || null,
    hektor_user_email: payload.target_hektor_user_email || payload.hektor_user_email || null,
  };
}

async function resolveContactAgencyExecutionPayload(payload) {
  const source = payload || {};
  const before = source.before_contact && typeof source.before_contact === "object" ? source.before_contact : {};
  const targetNegotiatorId = cleanString(
    source.target_hektor_negociateur_id ||
    source.hektor_negociateur_id ||
    source.id_negociateur ||
    before.hektor_negociateur_id
  );
  const targetAgencyId = cleanString(
    source.target_hektor_agence_id ||
    source.hektor_agence_id ||
    before.hektor_agence_id
  );
  const targetAgencyUserId = cleanString(
    source.target_agency_id_user ||
    source.agence_id_user ||
    source.agency_id_user ||
    before.agence_id_user
  );
  const targetEmail = cleanString(
    source.target_hektor_user_email ||
    source.hektor_user_email ||
    source.negociateur_email ||
    before.negociateur_email
  );

  let row = null;
  const rows = targetNegotiatorId || targetAgencyId || targetAgencyUserId || targetEmail
    ? await loadHektorNegotiatorAgencyRows({
        negotiatorId: targetNegotiatorId,
        agencyId: targetAgencyId,
        agencyUserId: targetAgencyUserId,
        email: targetEmail,
        limit: 20,
      }).catch(() => [])
    : [];

  if (rows.length) {
    row = rows.find((candidate) => {
      if (targetNegotiatorId && String(candidate.hektor_negociateur_id || "") !== targetNegotiatorId) return false;
      if (targetAgencyId && String(candidate.hektor_agence_id || "") !== targetAgencyId) return false;
      if (targetAgencyUserId && String(candidate.agence_id_user || "") !== targetAgencyUserId) return false;
      if (targetEmail && normalizeEmail(candidate.email) !== normalizeEmail(targetEmail)) return false;
      return true;
    }) || rows[0];
  }

  const agencyUserId = cleanString((row && row.agence_id_user) || targetAgencyUserId);
  if (!agencyUserId) return null;

  return contactAgencyExecutionPayload({
    ...source,
    target_hektor_user_id: cleanString((row && row.hektor_user_id) || source.target_hektor_user_id || source.hektor_user_id),
    target_hektor_user_label: cleanString((row && row.display_name) || source.target_hektor_user_label || source.hektor_user_label) || null,
    target_hektor_user_email: cleanString((row && row.email) || targetEmail) || null,
    target_hektor_negociateur_id: cleanString((row && row.hektor_negociateur_id) || targetNegotiatorId) || null,
    target_hektor_agence_id: cleanString((row && row.hektor_agence_id) || targetAgencyId) || null,
    target_agency_id_user: agencyUserId,
    target_agency_label: cleanString((row && row.agence_nom) || source.target_agency_label || before.agence_nom) || null,
  });
}

const CRM_CONTACT_TOGGLE_FIELDS = [
  {
    key: "crmMandateSummaryEnabled",
    label: "Mail nouveau mandat",
    operationName: "ToggleMandateSummaryConfiguration",
    query: CRM_TOGGLE_MANDATE_SUMMARY_CONFIGURATION_MUTATION,
  },
  {
    key: "crmMandateExpirationEnabled",
    label: "Mail echeance mandat",
    operationName: "ToggleMandateExpirationConfiguration",
    query: CRM_TOGGLE_MANDATE_EXPIRATION_CONFIGURATION_MUTATION,
  },
  {
    key: "crmBirthdayEnabled",
    label: "Message anniversaire client",
    operationName: "ToggleCrmBirthdayConfiguration",
    query: CRM_TOGGLE_BIRTHDAY_CONFIGURATION_MUTATION,
  },
];

function mapHektorContactCrmConfigurations(data) {
  const source = data || {};
  return {
    crmMandateSummaryEnabled: source.mandateSummaryConfiguration && typeof source.mandateSummaryConfiguration.enabled === "boolean"
      ? source.mandateSummaryConfiguration.enabled
      : null,
    crmMandateExpirationEnabled: source.mandateExpirationConfiguration && typeof source.mandateExpirationConfiguration.enabled === "boolean"
      ? source.mandateExpirationConfiguration.enabled
      : null,
    crmBirthdayEnabled: source.crmBirthdayConfiguration && typeof source.crmBirthdayConfiguration.enabled === "boolean"
      ? source.crmBirthdayConfiguration.enabled
      : null,
  };
}

async function fetchHektorContactCrmSettings(contactId) {
  const prospect = Number(contactId);
  if (!Number.isSafeInteger(prospect)) throw new Error("contact_id Hektor numerique requis pour CRM");
  const payload = await hektorGraphQLOperation({
    operationName: "CrmContactRelationshipConfigurations",
    query: CRM_CONTACT_CONFIGURATION_QUERY,
    variables: { prospect },
  });
  return mapHektorContactCrmConfigurations(payload.data || {});
}

async function updateHektorContactCrmSettings(job, contactId, payload) {
  const contact = normalizeHektorContactPayload({ ...(payload || {}), hektor_contact_id: contactId }, { requireContactId: true });
  const requested = CRM_CONTACT_TOGGLE_FIELDS
    .map((field) => ({ ...field, enabled: contact[field.key] }))
    .filter((field) => typeof field.enabled === "boolean");
  if (!requested.length) return null;

  const prospect = Number(contactId);
  if (!Number.isSafeInteger(prospect)) throw new Error("contact_id Hektor numerique requis pour CRM");
  await logJob(job.id, "hektor_contact_crm", "running", "Mise a jour CRM contact Hektor", {
    hektor_contact_id: String(contactId),
    fields: requested.map((field) => ({ label: field.label, enabled: field.enabled })),
  });

  for (const field of requested) {
    await hektorGraphQLOperation({
      operationName: field.operationName,
      query: field.query,
      variables: { prospect, enabled: field.enabled },
    });
  }

  const verified = await fetchHektorContactCrmSettings(contactId);
  const mismatches = requested.filter((field) => verified[field.key] !== field.enabled);
  if (mismatches.length) {
    throw new Error(`Configuration CRM contact Hektor non confirmee: ${mismatches.map((field) => field.label).join(", ")}`);
  }
  await logJob(job.id, "hektor_contact_crm", "done", "CRM contact Hektor confirme", {
    hektor_contact_id: String(contactId),
    verified,
  });
  return verified;
}

function parseHektorCreatedContactId(responseText) {
  const raw = String(responseText || "").trim();
  let parsed = raw;
  try {
    parsed = JSON.parse(raw);
  } catch (_) {
    parsed = raw;
  }
  const candidates = [
    parsed,
    parsed && typeof parsed === "object" ? parsed.idContact : null,
    parsed && typeof parsed === "object" ? parsed.id_contact : null,
    parsed && typeof parsed === "object" ? parsed.contact_id : null,
    parsed && typeof parsed === "object" ? parsed.id : null,
  ];
  for (const candidate of candidates) {
    const text = String(candidate == null ? "" : candidate).trim();
    if (/^\d+$/.test(text)) return text;
  }
  return "";
}

async function createHektorContact(job, payload) {
  const contact = normalizeHektorContactPayload(payload, { requireName: true, requireReachable: true });
  const formHtml = await fetchHektorManualMandantForm({
    qualification: contact.qualification,
    statut: hektorManualContactFormStatus(contact.contactStatus, contact.qualification),
    negotiatorId: contact.targetNegotiatorId,
  });
  const values = extractHektorFormValues(formHtml, null);
  values.set("mode", "contacts-actions-insertManuelContactFromOtherObject");
  values.set("statut", contact.contactStatus);
  values.set("qualification", contact.qualification);
  values.delete("saveOrUpdate");
  values.delete("saveOrUpdateValue");
  applyHektorContactIdentityValues(values, contact);
  await applyContactLocalityIds(values, contact, job, null);

  await logJob(job.id, "hektor_contact_create", "running", "Creation contact global dans Hektor", {
    nom: contact.lastName,
    prenom: contact.firstName,
    sociale: contact.companyName,
    email: contact.email,
    phone: contact.phone,
    qualification: contact.qualification,
    statut: contact.contactStatus,
    metier: contact.partnerJobId,
  });

  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: values,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact`,
    },
  });
  const contactId = parseHektorCreatedContactId(response.text);
  if (!contactId) {
    throw new Error(`Creation contact Hektor non confirmee: ${response.text.slice(0, 500)}`);
  }
  return {
    ...contact,
    contactId,
  };
}

function contactNextStepPayload(payload) {
  const source = payload || {};
  const next = source.contact_next_step || source.contactNextStep || source.next_step || null;
  return next && typeof next === "object" ? next : null;
}

function stringArray(value) {
  if (Array.isArray(value)) return value.map((item) => cleanString(item)).filter(Boolean);
  if (typeof value === "string") return value.split(/[|,;]/).map((item) => cleanString(item)).filter(Boolean);
  return [];
}

function contactJsonStringArray(value) {
  if (Array.isArray(value)) return stringArray(value);
  if (typeof value === "string") {
    const parsed = safeJsonParse(value, null);
    if (Array.isArray(parsed)) return stringArray(parsed);
    return stringArray(value);
  }
  return [];
}

function normalizeContactSearchContextText(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9_ -]/g, " ")
    .replace(/\s+/g, "_");
}

function inferContactSearchQualification(payload, contact) {
  const explicit = firstDefined(payload, ["qualification", "contact_qualification", "contactQualification"]);
  const explicitQualification = normalizeHektorContactQualification(explicit, "");
  if (["1", "2"].includes(explicitQualification)) return explicitQualification;

  const kind = firstDefined(payload, ["contact_kind", "contactKind", "search_contact_kind", "searchContactKind"]);
  const kindQualification = normalizeHektorContactQualification(kind, "");
  if (["1", "2"].includes(kindQualification)) return kindQualification;

  const tags = [
    ...contactJsonStringArray(contact && contact.typologies_json),
    ...contactJsonStringArray(contact && contact.relation_roles_json),
  ].map(normalizeContactSearchContextText);
  if (tags.some((tag) => tag.includes("locataire"))) return "1";
  if (tags.some((tag) => tag.includes("acquereur") || tag.includes("acheteur"))) return "2";
  return "2";
}

function contactSearchExecutionContact(payload, contact) {
  const source = payload || {};
  return {
    qualification: inferContactSearchQualification(source, contact),
    city: cleanString(source.city || source.ville || (contact && contact.ville)),
    postalCode: cleanString(source.postal_code || source.code_postal || source.code || (contact && contact.code_postal)),
  };
}

function firstCleanString(source, keys) {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(source || {}, key)) {
      const value = cleanString(source[key]);
      if (value) return value;
    }
  }
  return "";
}

function appendJqueryParam(params, key, value) {
  if (value === undefined || value === null) return;
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      if (item && typeof item === "object" && !Array.isArray(item)) {
        appendJqueryParam(params, `${key}[${index}]`, item);
      } else {
        appendJqueryParam(params, `${key}[]`, item);
      }
    });
    return;
  }
  if (typeof value === "object") {
    for (const [childKey, childValue] of Object.entries(value)) {
      appendJqueryParam(params, `${key}[${childKey}]`, childValue);
    }
    return;
  }
  params.append(key, String(value));
}

function appendHektorCriteriaRequest(params, payload) {
  for (const [key, value] of Object.entries(payload || {})) {
    appendJqueryParam(params, key, value);
  }
  return params;
}

async function buildHektorContactSearchContainer(contactId, contact, payload) {
  const next = contactNextStepPayload(payload);
  if (!next || next.kind !== "search_criteria" || next.enabled === false) {
    return null;
  }
  if (!["1", "2"].includes(contact.qualification)) {
    throw new Error(`Recherche contact Hektor impossible pour qualification ${contact.qualification || "manquante"} (acquereur ou locataire requis)`);
  }

  const typeIds = stringArray(next.propertyTypeIds || next.property_type_ids || next.typesBiens || next.types_biens)
    .map((item) => Number(String(item).replace(/[^0-9]/g, "")))
    .filter((value) => Number.isSafeInteger(value) && value > 0);
  if (!typeIds.length) throw new Error("Type de bien requis pour creer la recherche contact Hektor");

  const offerCode = firstCleanString(next, ["offerCode", "offer_code", "offreDem", "offre"])
    || (contact.qualification === "1" ? "2" : "0");
  const city = firstCleanString(next, ["city", "ville"]) || contact.city || "";
  const postalCode = firstCleanString(next, ["postalCode", "postal_code", "code_postal", "code"]) || contact.postalCode || "";
  const cityId = firstCleanString(next, ["hektorCityId", "hektor_city_id", "idVille"]);
  const postalId = firstCleanString(next, ["hektorPostalCodeId", "hektor_postal_code_id", "idCode"]);

  // Localites : on accepte soit une liste next.localities[{city,postalCode,hektorCityId,...}],
  // soit la commune unique city/postalCode. Chaque commune est resolue en {id,type}.
  const localityEntries = [];
  if (Array.isArray(next.localities)) {
    for (const loc of next.localities) {
      if (!loc || typeof loc !== "object") continue;
      localityEntries.push({
        city: firstCleanString(loc, ["city", "ville"]),
        postalCode: firstCleanString(loc, ["postalCode", "postal_code", "code_postal", "code"]),
        cityId: firstCleanString(loc, ["hektorCityId", "hektor_city_id", "idVille"]),
        postalId: firstCleanString(loc, ["hektorPostalCodeId", "hektor_postal_code_id", "idCode"]),
      });
    }
  }
  if (!localityEntries.length) {
    localityEntries.push({ city, postalCode, cityId, postalId });
  }

  const villes = [];
  const seenVilleKeys = new Set();
  for (const entry of localityEntries) {
    let resolved = null;
    if (entry.cityId) resolved = { id: entry.cityId, type: "0" };
    else if (entry.postalId) resolved = { id: entry.postalId, type: "1" };
    else if (entry.city || entry.postalCode) {
      const locality = await resolveHektorPublicLocality(entry.postalCode, entry.city);
      if (locality && locality.idVille) resolved = { id: locality.idVille, type: "0" };
      else if (locality && locality.idCode) resolved = { id: locality.idCode, type: "1" };
    }
    if (!resolved) continue;
    const key = `${resolved.type}:${resolved.id}`;
    if (seenVilleKeys.has(key)) continue;
    seenVilleKeys.add(key);
    villes.push(resolved);
  }
  if (!villes.length) throw new Error("Ville Hektor non resolue pour creer la recherche contact");

  const criteresDetails = {};
  const addCriterion = (key, keys) => {
    const value = firstCleanString(next, keys);
    if (value) criteresDetails[key] = { value, ponderation: "1" };
  };
  addCriterion("ITEM_PRIX_MIN", ["priceMin", "price_min", "prix_min"]);
  addCriterion("ITEM_PRIX_MAX", ["priceMax", "price_max", "prix_max"]);
  addCriterion("ITEM_SURFACE_MIN", ["surfaceMin", "surface_min"]);
  addCriterion("ITEM_SURFACE_MAX", ["surfaceMax", "surface_max"]);
  addCriterion("ITEM_PIECES_MIN", ["roomsMin", "rooms_min", "pieces_min"]);
  addCriterion("ITEM_PIECES_MAX", ["roomsMax", "rooms_max", "pieces_max"]);
  addCriterion("ITEM_CHAMBRE_MIN", ["bedroomsMin", "bedrooms_min", "chambre_min"]);
  addCriterion("ITEM_CHAMBRE_MAX", ["bedroomsMax", "bedrooms_max", "chambre_max"]);
  addCriterion("ITEM_SURFACE_TERRAIN_MIN", ["landSurfaceMin", "land_surface_min", "surface_terrain_min"]);
  addCriterion("ITEM_SURFACE_TERRAIN_MAX", ["landSurfaceMax", "land_surface_max", "surface_terrain_max"]);
  // Criteres supplementaires (format Hektor confirme sur les recherches reelles).
  addCriterion("ITEM_PRIX_MARGE", ["priceMargin", "price_margin", "prix_marge", "marge"]);
  addCriterion("ITEM_SDB_SDE_MIN", ["bathroomsMin", "bathrooms_min", "sdb_min", "sdbMin"]);
  addCriterion("ITEM_SDB_SDE_MAX", ["bathroomsMax", "bathrooms_max", "sdb_max", "sdbMax"]);
  addCriterion("ITEM_SURFACE_SEJOUR_MIN", ["livingRoomSurfaceMin", "living_room_surface_min", "sejour_min"]);
  addCriterion("ITEM_SURFACE_SEJOUR_MAX", ["livingRoomSurfaceMax", "living_room_surface_max", "sejour_max"]);
  addCriterion("ITEM_FLOORS_MIN", ["floorsMin", "floors_min", "etage_min"]);
  addCriterion("ITEM_FLOORS_MAX", ["floorsMax", "floors_max", "etage_max"]);
  addCriterion("ITEM_NB_NIVEAU_MIN", ["levelsMin", "levels_min", "niveaux_min"]);
  addCriterion("ITEM_NB_NIVEAU_MAX", ["levelsMax", "levels_max", "niveaux_max"]);
  // Enums (lettre DPE, chauffage, cuisine, occupation) : valeur = code Hektor.
  addCriterion("ITEM_DPE_CONS_LETTER", ["dpeLetter", "dpe_letter", "dpe"]);
  addCriterion("ITEM_CHAUFFAGE_TYPE", ["heatingType", "heating_type", "chauffage_type"]);
  addCriterion("ITEM_CHAUFFAGE_ENERGIE", ["heatingEnergy", "heating_energy", "chauffage_energie"]);
  addCriterion("ITEM_CUISINE_TYPE", ["kitchenType", "kitchen_type", "cuisine_type"]);
  addCriterion("ITEM_OCCUPATION", ["occupation"]);

  // Equipements / terrain : criteres booleens Hektor (valeur "OUI" / "NON").
  const EQUIPMENT_CRITERIA = {
    garage_parking: "ITEM_GARAGE_PARKING",
    terrasse: "ITEM_TERRASSE",
    balcon: "ITEM_BALCON",
    piscine: "ITEM_PISCINE",
    ascenseur: "ITEM_ASCENSEUR",
    cheminee: "ITEM_CHEMINEE",
    cave: "ITEM_CAVE",
    double_vitrage: "ITEM_DOUBLE_VITRAGE",
    plain_pied: "ITEM_PLAIN_PIED",
    mitoyen: "ITEM_MITTOYEN",
    grenier_comble: "ITEM_GRENIER_COMBLE",
    acces_handi: "ITEM_ACCES_HANDI",
    terrain_constructible: "ITEM_TERRAIN_CONSTRUCTIBLE",
    terrain_arbore: "ITEM_TERRAIN_ARBORE",
    terrain_piscinable: "ITEM_TERRAIN_PISCINABLE",
    terrain_viabilise: "ITEM_TERRAIN_VIABILISE",
  };
  const equipmentItemByKey = new Map();
  for (const [shortKey, itemKey] of Object.entries(EQUIPMENT_CRITERIA)) {
    equipmentItemByKey.set(shortKey.toUpperCase(), itemKey);
    equipmentItemByKey.set(itemKey.toUpperCase(), itemKey);
  }
  const addBooleanEquipment = (rawKey, rawValue) => {
    const itemKey = equipmentItemByKey.get(String(rawKey || "").trim().toUpperCase());
    if (!itemKey) return;
    const truthy = rawValue === undefined
      || /^(1|true|oui|yes|on)$/i.test(String(rawValue).trim());
    criteresDetails[itemKey] = { value: truthy ? "OUI" : "NON", ponderation: "1" };
  };
  const equipmentList = stringArray(next.equipments || next.equipements || next.equipment || next.features);
  for (const item of equipmentList) addBooleanEquipment(item);
  if (next.equipmentMap && typeof next.equipmentMap === "object") {
    for (const [key, value] of Object.entries(next.equipmentMap)) addBooleanEquipment(key, value);
  }

  // Particularites Hektor : liste d'ids -> conteneur.particularites.
  const particulariteIds = stringArray(next.particulariteIds || next.particularite_ids || next.particularites)
    .map((item) => Number(String(item).replace(/[^0-9]/g, "")))
    .filter((value) => Number.isSafeInteger(value) && value > 0);

  if (!criteresDetails.ITEM_PRIX_MAX) {
    throw new Error("Budget maximum requis pour creer la recherche contact Hektor");
  }

  // criteresId : 0 = nouvelle recherche ; > 0 = edition d'une recherche existante.
  const criteresId = Number(firstCleanString(next, ["criteresId", "idCritere", "critere_id", "hektor_critere_id"]).replace(/[^0-9]/g, "")) || 0;

  return {
    prospectId: Number(contactId),
    criteresId,
    offreDem: Number(offerCode),
    typesBiens: typeIds,
    typesTransacs: [],
    criteresDetails,
    quartiers: [],
    particularites: particulariteIds,
    activites: [],
    villes,
    isFirstCallEditSearch: false,
    quartierOfficiels: [],
    communes: [],
  };
}

function compactHektorPreview(text, maxLength = 240) {
  return String(text || "").replace(/\s+/g, " ").trim().slice(0, maxLength);
}

async function primeHektorContactSearchWizard(job, contactId, container) {
  const idCritere = container.criteresId ? String(container.criteresId) : "";
  const launchState = idCritere ? "relaunchCreate" : "launchCreate";
  const referer = `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(String(contactId))}`;
  const launchBody = new URLSearchParams({
    mode: "contact-ajoutCritereProspect",
    idProspect: String(contactId),
    isFirstCallEditSearch: "false",
    state: launchState,
  });
  if (idCritere) launchBody.set("idCritere", idCritere);

  await logJob(job.id, "hektor_contact_search_wizard", "running", "Initialisation assistant recherche contact Hektor", {
    hektor_contact_id: String(contactId),
    state: launchState,
    idCritere: idCritere || null,
  });

  const launchResponse = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: launchBody,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: referer,
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  const viewBody = appendHektorCriteriaRequest(new URLSearchParams(), {
    mode: "contact-ajoutCritereProspect",
    state: "getVueByContext",
    container,
  });
  const viewResponse = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: viewBody,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: referer,
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  await logJob(job.id, "hektor_contact_search_wizard", "done", "Assistant recherche contact Hektor initialise", {
    hektor_contact_id: String(contactId),
    state: launchState,
    idCritere: idCritere || null,
    launch_preview: compactHektorPreview(launchResponse.text),
    view_preview: compactHektorPreview(viewResponse.text),
  });
}

async function createHektorContactSearchCriteria(job, contactId, contact, payload) {
  const container = await buildHektorContactSearchContainer(contactId, contact, payload);
  if (!container) return { status: "skipped", reason: "not_requested" };

  await logJob(job.id, "hektor_contact_search", "running", container.criteresId ? "Modification recherche contact Hektor" : "Creation recherche contact Hektor", {
    hektor_contact_id: String(contactId),
    criteresId: container.criteresId || null,
    offreDem: container.offreDem,
    typesBiens: container.typesBiens,
    villes: container.villes,
    criteres: Object.keys(container.criteresDetails),
  });

  if (payload && (payload.__prime_contact_search_wizard || container.criteresId)) {
    await primeHektorContactSearchWizard(job, contactId, container);
  }

  const checkBody = appendHektorCriteriaRequest(new URLSearchParams(), {
    mode: "contact-ajoutCritereProspect",
    state: "checkIfRequiredIsOk",
    typesBiens: container.typesBiens,
    container,
  });
  const checkResponse = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: checkBody,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(String(contactId))}`,
    },
  });
  let check = null;
  try {
    check = JSON.parse(checkResponse.text);
  } catch (_) {
    throw new Error(`Controle recherche contact Hektor illisible: ${checkResponse.text.slice(0, 400)}`);
  }
  if (check && String(check.error || "") === "1") {
    const missing = [check.CRTypeBien ? "type de bien" : null, check.CRPrix ? "prix" : null].filter(Boolean).join(", ");
    throw new Error(`Recherche contact Hektor incomplete${missing ? `: ${missing}` : ""}`);
  }

  const createBody = appendHektorCriteriaRequest(new URLSearchParams(), {
    mode: "contact-ajoutCritereProspect",
    state: "createCritereCr",
    container,
  });
  const createResponse = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: createBody,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(String(contactId))}`,
    },
  });
  let created = createResponse.text;
  try {
    created = JSON.parse(createResponse.text);
  } catch (_) {
    created = createResponse.text;
  }
  await logJob(job.id, "hektor_contact_search", "done", container.criteresId ? "Recherche contact Hektor modifiee" : "Recherche contact Hektor creee", {
    hektor_contact_id: String(contactId),
    criteresId: container.criteresId || null,
    result: created,
  });
  return {
    status: container.criteresId ? "updated" : "created",
    hektor_contact_id: String(contactId),
    idCritere: container.criteresId || null,
    result: created,
  };
}

async function applyHektorOwnerNextStep(job, contactId, payload) {
  const next = contactNextStepPayload(payload);
  if (!next || next.kind !== "owner_relation") return { status: "skipped", reason: "not_requested" };
  const action = cleanString(next.action) || "finish";
  if (action === "finish") return { status: "done", action };
  if (action === "create_property") {
    return {
      status: "pending_create_property",
      action,
      hektor_contact_id: String(contactId),
    };
  }
  if (action !== "link_existing") return { status: "skipped", reason: `unsupported_action:${action}` };

  const annonceId = cleanString(next.hektorAnnonceId || next.hektor_annonce_id || next.annonce_id);
  if (!/^\d+$/.test(annonceId || "")) throw new Error("ID annonce Hektor numerique requis pour rattacher le proprietaire");

  const linkResult = await linkHektorMandantContact(job, annonceId, String(contactId), "hektor_contact_owner_link");
  return { status: linkResult.status, action, hektor_contact_id: String(contactId), hektor_annonce_id: annonceId, wait_attempts: linkResult.waitAttempts };
}

async function applyHektorContactPostCreateStep(job, created, payload) {
  if (created.qualification === "1" || created.qualification === "2") {
    return createHektorContactSearchCriteria(job, created.contactId, created, payload);
  }
  if (created.qualification === "3") {
    return applyHektorOwnerNextStep(job, created.contactId, payload);
  }
  return { status: "skipped", reason: "no_post_create_step" };
}

async function updateHektorContactIdentity(job, contactId, payload) {
  const contact = normalizeHektorContactPayload({ ...payload, hektor_contact_id: contactId }, { requireContactId: true, requireName: true });
  const formHtml = await fetchHektorContactEditForm(contactId);
  const values = extractHektorFormValues(formHtml, "mefContacts/contacts_full_accueil");
  if (!values.has("nom")) {
    throw new Error(`Formulaire edition contact Hektor introuvable pour ${contactId}`);
  }
  applyHektorContactIdentityValues(values, contact);

  await applyContactLocalityIds(values, contact, job, contactId);

  const body = new URLSearchParams();
  body.set("mode", "contacts-saveDataEditContact");
  body.set("group", "mefContacts/contacts_full_accueil");
  body.set("idContact", String(contactId));
  for (const [key, value] of values.entries()) body.append(key, value);

  await logJob(job.id, "hektor_contact_update", "running", "Modification contact global dans Hektor", {
    hektor_contact_id: String(contactId),
    fields: Object.keys(payload || {}).filter((key) => payload[key] != null),
  });

  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(String(contactId))}`,
    },
  });

  let parsed = null;
  try {
    parsed = JSON.parse(response.text);
  } catch (_) {
    parsed = response.text;
  }
  const parsedText = typeof parsed === "string" ? parsed : JSON.stringify(parsed);
  if (/emailErrors|erreur|error/i.test(parsedText) && !/content_mefContacts/i.test(parsedText)) {
    throw new Error(`Modification contact Hektor refusee: ${parsedText.slice(0, 500)}`);
  }
  return {
    hektor_contact_id: String(contactId),
    contact: {
      civilite: contact.civility,
      nom: contact.lastName,
      prenom: contact.firstName,
      sociale: contact.companyName,
      juridique: contact.legalForm,
      siret: contact.siret,
      metier: contact.partnerJobId,
      url: contact.website,
      email: contact.email,
      telephone: contact.phone,
      telephone_secondaire: contact.phoneSecondary,
      conjoint_nom: contact.spouseLastName,
      conjoint_prenom: contact.spouseFirstName,
      conjoint_email: contact.spouseEmail,
      conjoint_telephone: contact.spousePhone,
      adresse: contact.address,
      code: contact.postalCode,
      ville: contact.city,
      date_naissance: contact.birthDate,
      lieu_naissance: contact.birthPlace,
      statut_matrimonial: contact.maritalStatus,
      qualification: contact.qualification,
      statut: contact.contactStatus,
    },
  };
}

async function handleCreateHektorContact(job) {
  const payload = safeJsonParse(job.payload_json);
  const executionPayload = await resolveContactAgencyExecutionPayload(payload) || contactAgencyExecutionPayload(payload);
  await ensureHektorExecutionContext(job, null, executionPayload, { preferRequester: true, preferDossierOwner: false, required: true });

  const created = await createHektorContact(job, payload);
  const crmSettings = await updateHektorContactCrmSettings(job, created.contactId, payload);
  const postCreateStep = await applyHektorContactPostCreateStep(job, created, payload);
  await sleep(1200);
  const syncJob = await enqueueRefreshConsoleContactDataJobBestEffort(job, created.contactId, {
    reason: "create_hektor_contact",
    priority: 82,
  });

  return {
    status: "created",
    hektor_contact_id: created.contactId,
    contact: {
      nom: created.lastName,
      prenom: created.firstName,
      sociale: created.companyName,
      email: created.email,
      telephone: created.phone,
      date_naissance: created.birthDate,
      lieu_naissance: created.birthPlace,
      statut_matrimonial: created.maritalStatus,
    },
    crm_settings: crmSettings,
    post_create_step: postCreateStep,
    sync_job: syncJob,
  };
}

async function handleUpdateHektorContact(job) {
  const payload = safeJsonParse(job.payload_json);
  const contactId = String(payload.hektor_contact_id || payload.contact_id || "").trim();
  if (!/^\d+$/.test(contactId)) throw new Error("contact_id Hektor numerique requis");
  const context = await loadContactExecutionContext(contactId);
  const contextPayload = {
    ...payload,
    hektor_user_email: payload.hektor_user_email || payload.target_hektor_user_email || context.contact.negociateur_email || null,
    target_hektor_user_email: payload.target_hektor_user_email || payload.hektor_user_email || context.contact.negociateur_email || null,
    contact_negociateur_email: context.contact.negociateur_email || null,
    contact_hektor_agence_id: context.contact.hektor_agence_id || null,
    hektor_agence_id: payload.hektor_agence_id || payload.target_hektor_agence_id || context.contact.hektor_agence_id || null,
    target_hektor_agence_id: payload.target_hektor_agence_id || payload.hektor_agence_id || context.contact.hektor_agence_id || null,
    contact_hektor_negociateur_id: context.contact.hektor_negociateur_id || null,
    hektor_negociateur_id: payload.hektor_negociateur_id || payload.target_hektor_negociateur_id || context.contact.hektor_negociateur_id || null,
    target_hektor_negociateur_id: payload.target_hektor_negociateur_id || payload.hektor_negociateur_id || context.contact.hektor_negociateur_id || null,
  };
  const executionPayload = await resolveContactAgencyExecutionPayload(contextPayload) || contactAgencyExecutionPayload(contextPayload);
  await ensureHektorExecutionContext(job, context.dossier, executionPayload, { preferRequester: true, preferDossierOwner: true, required: true });

  // Lot B garde-fou anti-écrasement (miroir annonce) : pour un push from_pending, si le
  // contact a été modifié dans Hektor DEPUIS l'édition optimiste (date_maj plus récente que
  // la photo), on ne l'écrase pas -> conflit. Best-effort : si la relecture API échoue, on écrit.
  if (payload.from_pending === true) {
    const base = (payload.base_snapshot && typeof payload.base_snapshot === "object") ? payload.base_snapshot : {};
    const baseDateMaj = base._date_maj ? String(base._date_maj) : null;
    if (baseDateMaj) {
      const freshDateMaj = await fetchContactDateMajFromApi(job, contactId, "contact_overwrite_guard");
      if (freshDateMaj && freshDateMaj > baseDateMaj) {
        await markContactPendingConflict(contactId);
        await notifyNegoContactConflict(job, contactId, contextPayload);
        await logJob(job.id, "contact_overwrite_guard", "done", "Contact modifié dans Hektor depuis l'édition : écriture bloquée (anti-écrasement)", {
          hektor_contact_id: contactId,
          base_date_maj: baseDateMaj,
          fresh_date_maj: freshDateMaj,
        });
        return { status: "held_conflict", hektor_contact_id: contactId, reason: "contact_modifie_dans_hektor_depuis_edition" };
      }
    }
  }

  const updated = await updateHektorContactIdentity(job, contactId, contextPayload);
  const crmSettings = await updateHektorContactCrmSettings(job, contactId, contextPayload);
  // Lot B : push from_pending réussi -> on efface le pending (avant l'after-refresh).
  if (payload.from_pending === true) await clearContactPending(contactId);
  await sleep(1000);
  const syncJob = await enqueueRefreshConsoleContactDataJobBestEffort(job, contactId, {
    reason: "update_hektor_contact",
    priority: 82,
  });

  return {
    status: "updated",
    ...updated,
    crm_settings: crmSettings,
    sync_job: syncJob,
  };
}

// Construit l'objet "search spec" attendu par buildHektorContactSearchContainer
// a partir d'un payload de job autonome. Accepte la spec sous payload.search,
// payload.contact_next_step, ou directement a la racine du payload.
function contactSearchSpecFromPayload(payload) {
  const source = payload || {};
  const nested = (source.search && typeof source.search === "object" && source.search)
    || (source.recherche && typeof source.recherche === "object" && source.recherche)
    || contactNextStepPayload(source)
    || source;
  return { ...nested, kind: "search_criteria", enabled: true };
}

async function handleAddHektorContactSearch(job) {
  const payload = safeJsonParse(job.payload_json);
  const contactId = String(payload.hektor_contact_id || payload.contact_id || "").trim();
  if (!/^\d+$/.test(contactId)) throw new Error("contact_id Hektor numerique requis");

  const context = await loadContactExecutionContext(contactId);
  const contextPayload = {
    ...payload,
    hektor_user_email: payload.hektor_user_email || payload.target_hektor_user_email || context.contact.negociateur_email || null,
    target_hektor_user_email: payload.target_hektor_user_email || payload.hektor_user_email || context.contact.negociateur_email || null,
    contact_negociateur_email: context.contact.negociateur_email || null,
    contact_hektor_agence_id: context.contact.hektor_agence_id || null,
    hektor_agence_id: payload.hektor_agence_id || payload.target_hektor_agence_id || context.contact.hektor_agence_id || null,
    target_hektor_agence_id: payload.target_hektor_agence_id || payload.hektor_agence_id || context.contact.hektor_agence_id || null,
    contact_hektor_negociateur_id: context.contact.hektor_negociateur_id || null,
    hektor_negociateur_id: payload.hektor_negociateur_id || payload.target_hektor_negociateur_id || context.contact.hektor_negociateur_id || null,
    target_hektor_negociateur_id: payload.target_hektor_negociateur_id || payload.hektor_negociateur_id || context.contact.hektor_negociateur_id || null,
  };
  const executionPayload = await resolveContactAgencyExecutionPayload(contextPayload) || contactAgencyExecutionPayload(contextPayload);
  await ensureHektorExecutionContext(job, context.dossier, executionPayload, { preferRequester: true, preferDossierOwner: true, required: true });

  // La recherche reutilise createHektorContactSearchCriteria via le contact_next_step.
  // Qualification 1 (locataire) / 2 (acquereur) : indispensable au garde-fou et au code offre.
  const contact = contactSearchExecutionContact(payload, context.contact);
  const wrappedPayload = {
    ...contextPayload,
    __prime_contact_search_wizard: true,
    contact_next_step: contactSearchSpecFromPayload(payload),
  };

  const search = await createHektorContactSearchCriteria(job, contactId, contact, wrappedPayload);
  if (search && search.status === "skipped") {
    throw new Error(`Recherche contact non creee (${search.reason || "payload incomplet"})`);
  }

  await sleep(1000);
  const syncJob = await enqueueRefreshConsoleContactDataJobBestEffort(job, contactId, {
    reason: "add_hektor_contact_search",
    priority: 82,
  });

  return {
    status: "created",
    hektor_contact_id: contactId,
    search,
    sync_job: syncJob,
  };
}

// Prepare l'execution d'une action recherche : resout l'id contact, bascule dans
// le contexte negociateur cible (indispensable, sinon Hektor renvoie 403).
async function ensureContactSearchExecution(job, payload) {
  const contactId = String(payload.hektor_contact_id || payload.contact_id || "").trim();
  if (!/^\d+$/.test(contactId)) throw new Error("contact_id Hektor numerique requis");
  const context = await loadContactExecutionContext(contactId);
  const contextPayload = {
    ...payload,
    hektor_user_email: payload.hektor_user_email || payload.target_hektor_user_email || context.contact.negociateur_email || null,
    target_hektor_user_email: payload.target_hektor_user_email || payload.hektor_user_email || context.contact.negociateur_email || null,
    contact_negociateur_email: context.contact.negociateur_email || null,
    contact_hektor_agence_id: context.contact.hektor_agence_id || null,
    hektor_agence_id: payload.hektor_agence_id || payload.target_hektor_agence_id || context.contact.hektor_agence_id || null,
    target_hektor_agence_id: payload.target_hektor_agence_id || payload.hektor_agence_id || context.contact.hektor_agence_id || null,
    contact_hektor_negociateur_id: context.contact.hektor_negociateur_id || null,
    hektor_negociateur_id: payload.hektor_negociateur_id || payload.target_hektor_negociateur_id || context.contact.hektor_negociateur_id || null,
    target_hektor_negociateur_id: payload.target_hektor_negociateur_id || payload.hektor_negociateur_id || context.contact.hektor_negociateur_id || null,
  };
  const executionPayload = await resolveContactAgencyExecutionPayload(contextPayload) || contactAgencyExecutionPayload(contextPayload);
  await ensureHektorExecutionContext(job, context.dossier, executionPayload, { preferRequester: true, preferDossierOwner: true, required: true });
  return { contactId, contextPayload, context };
}

// Liste les recherches (criteres prospect) d'un contact en scrapant l'onglet
// recherche de la console : seul endroit qui expose l'idCritere Hektor.
// A appeler APRES ensureContactSearchExecution (contexte negociateur actif).
async function fetchHektorContactSearchList(contactId) {
  const id = String(contactId);
  const body = new URLSearchParams({
    mode: "contacts-contactProfile-recherche-changeTab",
    id,
    idContact: id,
  });
  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(id)}`,
      "X-Requested-With": "XMLHttpRequest",
    },
  });
  let html = response.text;
  try {
    const parsed = JSON.parse(html);
    if (typeof parsed === "string") html = parsed;
  } catch (_) {
    // l'endpoint renvoie soit du HTML brut soit une chaine HTML encodee en JSON
  }
  const ids = [];
  const seen = new Set();
  const re = /(?:dropDownMenu_|contentDrop_|valueInputAutoarchivage|rel=["'])(\d{3,9})|getWizardCritere\(\s*\d+\s*,\s*(\d{3,9})/g;
  let match;
  while ((match = re.exec(html))) {
    const critId = match[1] || match[2];
    if (!critId || critId === id || seen.has(critId)) continue;
    seen.add(critId);
    ids.push(critId);
  }
  return ids.map((idCritere, index) => ({ index, idCritere }));
}

// Resout l'idCritere cible : id explicite du payload, sinon par index de recherche.
async function resolveContactSearchTargetCritereId(job, contactId, payload) {
  const explicit = cleanString(payload.idCritere || payload.critere_id || payload.hektor_critere_id);
  if (/^\d+$/.test(explicit)) return explicit;
  const list = await fetchHektorContactSearchList(contactId);
  if (!list.length) throw new Error(`Aucune recherche Hektor trouvee pour le contact ${contactId}`);
  const rawIndex = cleanString(payload.search_index !== undefined ? payload.search_index : payload.searchIndex);
  const index = /^\d+$/.test(rawIndex) ? Number(rawIndex) : 0;
  const target = list.find((entry) => entry.index === index) || list[0];
  await logJob(job.id, "hektor_contact_search_list", "done", "Recherches Hektor listees", {
    hektor_contact_id: String(contactId),
    count: list.length,
    requested_index: index,
    selected_idCritere: target.idCritere,
  });
  return target.idCritere;
}

// --- Correctif n°1 : garde-fou anti-écrasement des recherches contact ---
// La "photo" (base_snapshot) capture, AU MOMENT de l'édition, les champs NON
// éditables par le client (villes, types, autres critères ; cf. backend
// contact_search_mapping.SNAPSHOT_KEYS). Avant d'écrire, on rafraîchit le contact
// depuis Hektor et on compare : si un négociateur a modifié la recherche dans
// Hektor depuis l'édition, ces champs diffèrent -> on NE RÉÉCRIT PAS (sinon on
// écraserait sa saisie). On le prévient à la place.
function normSearchList(raw) {
  let v = raw;
  if (typeof v === "string") {
    const t = v.trim();
    if (!t) return [];
    try { v = JSON.parse(t); } catch (_) { return [t]; }
  }
  if (Array.isArray(v)) return v.map((x) => String(x == null ? "" : x).trim()).filter(Boolean).sort();
  if (v && typeof v === "object") return Object.keys(v).map((k) => String(k).trim()).filter(Boolean).sort();
  return v == null || v === "" ? [] : [String(v).trim()];
}

function normSearchCriteres(raw) {
  let v = raw;
  if (typeof v === "string") {
    const t = v.trim();
    if (!t) return "";
    try { v = JSON.parse(t); } catch (_) { return t; }
  }
  const items = Array.isArray(v) ? v : (v && typeof v === "object" ? Object.values(v) : []);
  const map = {};
  for (const it of items) {
    if (it && typeof it === "object" && it.cle != null) {
      map[String(it.cle)] = it.valeur == null ? "" : String(it.valeur).trim();
    }
  }
  return Object.keys(map).sort().map((k) => `${k}=${map[k]}`).join("|");
}

function normSearchNum(raw) {
  if (raw == null) return "";
  const n = Number(String(raw).replace(/[^0-9.]/g, ""));
  return Number.isFinite(n) && n > 0 ? String(Math.trunc(n)) : "";
}

// Empreinte stable des champs comparés (ordre/casse/espaces neutralisés).
// includeNumeric : compare aussi prix/surface/pièces/chambres — activé uniquement
// si la photo (base_snapshot) porte ces champs (rétro-compat avec les anciens jobs).
function searchCoreFingerprint(snap, includeNumeric) {
  if (!snap || typeof snap !== "object") return null;
  const fp = {
    offre: String(snap.offre == null ? "" : snap.offre).trim(),
    terrain: normSearchNum(snap.surface_terrain_min),
    types: normSearchList(snap.types_json),
    villes: normSearchList(snap.villes_json),
    criteres: normSearchCriteres(snap.criteres_json),
  };
  if (includeNumeric) {
    fp.prixMin = normSearchNum(snap.prix_min);
    fp.prixMax = normSearchNum(snap.prix_max);
    fp.surfaceMin = normSearchNum(snap.surface_min);
    fp.piecesMin = normSearchNum(snap.pieces_min);
    fp.chambreMin = normSearchNum(snap.chambre_min);
  }
  return JSON.stringify(fp);
}

async function fetchFreshContactSearchSnapshot(contactId, searchIndex) {
  const params = new URLSearchParams({
    select: "offre,types_json,villes_json,surface_terrain_min,criteres_json,prix_min,prix_max,surface_min,pieces_min,chambre_min,search_index",
    hektor_contact_id: `eq.${contactId}`,
    search_index: `eq.${searchIndex}`,
    archive: "eq.false",
    limit: "1",
  });
  const rows = await supabaseRequest(`app_contact_search_current?${params.toString()}`, { method: "GET" }).catch(() => null);
  return Array.isArray(rows) && rows.length ? rows[0] : null;
}

// Affinage Supabase-first : pour un push from_pending, lit l'état Hektor FRAIS dans le
// LOCAL (le push a sauté la recherche dirty dans Supabase, qui garde l'état optimiste).
// Voir phase2/sync/read_local_search_snapshot.py.
async function fetchLocalContactSearchSnapshot(job, contactId, searchIndex) {
  try {
    const out = await runProjectPythonScript(
      ["phase2/sync/read_local_search_snapshot.py", "--contact-id", String(contactId), "--search-index", String(searchIndex)],
      { timeoutMs: 30000, previewSize: 2000 });
    const last = String(out.stdout || "").trim().split(/\r?\n/).filter(Boolean).pop() || "{}";
    const parsed = safeJsonParse(last);
    return parsed && typeof parsed === "object" && Object.keys(parsed).length ? parsed : null;
  } catch (_) {
    return null;
  }
}

async function notifyNegoSearchConflict(job, contactId, payload, opts = {}) {
  try {
    const negoEmail = cleanString(opts.negoEmail || payload.contact_negociateur_email || payload.hektor_user_email || payload.target_hektor_user_email);
    if (!negoEmail) return;
    const s = (payload.search && typeof payload.search === "object") ? payload.search : {};
    const resume = `budget ${cleanString(s.priceMin) || "?"}–${cleanString(s.priceMax) || "?"} €`;
    await supabaseRequest("app_notification", {
      method: "POST",
      prefer: "return=minimal",
      body: JSON.stringify([{
        negociateur_email: negoEmail,
        type: "recherche_conflit_ecriture",
        title: "Modification non appliquée (recherche déjà modifiée)",
        body: opts.found === false
          ? "La recherche n'a pas été retrouvée côté Hektor : la modification n'a pas été appliquée."
          : `La recherche a été modifiée dans Hektor entre-temps : la modification (${resume}) n'a pas été appliquée pour ne pas écraser votre saisie.`,
        payload: { source: "search_overwrite_guard", hektor_contact_id: String(contactId), edits: payload.edits || null },
      }]),
    });
  } catch (_) {
    // notification best-effort : ne doit jamais faire échouer le job
  }
}

// Affinage Supabase-first (E) : nettoyage du pending après push, ou marquage conflit.
async function clearSearchPending(contactId, searchIndex) {
  try {
    await supabaseRequest(
      `app_search_pending?hektor_contact_id=eq.${encodeURIComponent(String(contactId))}&search_index=eq.${Number(searchIndex)}`,
      { method: "DELETE", prefer: "return=minimal" });
  } catch (_) { /* best-effort */ }
}
async function markSearchPendingConflict(contactId, searchIndex) {
  try {
    await supabaseRequest(
      `app_search_pending?hektor_contact_id=eq.${encodeURIComponent(String(contactId))}&search_index=eq.${Number(searchIndex)}`,
      { method: "PATCH", prefer: "return=minimal",
        body: JSON.stringify({ conflict: true, push_job_id: null, updated_at: new Date().toISOString() }) });
  } catch (_) { /* best-effort */ }
}

// Tier 2 (annonces) : nettoyage du pending annonce après push réussi, ou marquage conflit.
async function clearAnnoncePending(appDossierId) {
  if (appDossierId == null) return;
  try {
    await supabaseRequest(
      `app_annonce_pending?app_dossier_id=eq.${Number(appDossierId)}`,
      { method: "DELETE", prefer: "return=minimal" });
  } catch (_) { /* best-effort */ }
}
async function markAnnoncePendingConflict(appDossierId) {
  if (appDossierId == null) return;
  try {
    await supabaseRequest(
      `app_annonce_pending?app_dossier_id=eq.${Number(appDossierId)}`,
      { method: "PATCH", prefer: "return=minimal",
        body: JSON.stringify({ conflict: true, push_job_id: null, updated_at: new Date().toISOString() }) });
  } catch (_) { /* best-effort */ }
}

// Lot B (contacts) : nettoyage du pending contact après push réussi, ou marquage conflit.
async function clearContactPending(contactId) {
  const id = String(contactId || "").trim();
  if (!id) return;
  try {
    await supabaseRequest(
      `app_contact_pending?hektor_contact_id=eq.${encodeURIComponent(id)}`,
      { method: "DELETE", prefer: "return=minimal" });
  } catch (_) { /* best-effort */ }
}
async function markContactPendingConflict(contactId) {
  const id = String(contactId || "").trim();
  if (!id) return;
  try {
    await supabaseRequest(
      `app_contact_pending?hektor_contact_id=eq.${encodeURIComponent(id)}`,
      { method: "PATCH", prefer: "return=minimal",
        body: JSON.stringify({ conflict: true, push_job_id: null, updated_at: new Date().toISOString() }) });
  } catch (_) { /* best-effort */ }
}
// Notif négo en cas de conflit contact (miroir notifyNegoSearchConflict).
async function notifyNegoContactConflict(job, contactId, payload) {
  try {
    const safe = payload && typeof payload === "object" ? payload : {};
    const negoEmail = cleanString(safe.contact_negociateur_email || safe.hektor_user_email || safe.target_hektor_user_email);
    if (!negoEmail) return;
    await supabaseRequest("app_notification", {
      method: "POST",
      prefer: "return=minimal",
      body: JSON.stringify([{
        negociateur_email: negoEmail,
        type: "contact_conflit_ecriture",
        title: "Modification non appliquée (contact déjà modifié)",
        body: "Le contact a été modifié dans Hektor entre-temps : votre modification n'a pas été appliquée pour ne pas écraser le changement. Re-faites-la si nécessaire.",
        payload: { source: "contact_overwrite_guard", hektor_contact_id: String(contactId) },
      }]),
    });
  } catch (_) { /* best-effort */ }
}

// Retourne { blocked: false } si l'écriture est sûre, sinon { blocked: true, result }.
async function guardContactSearchOverwrite(job, contactId, payload, negoEmail) {
  const base = payload.base_snapshot;
  // Comparer aussi les champs numériques seulement si la photo les porte (rétro-compat).
  const includeNumeric = !!(base && typeof base === "object" && "prix_max" in base);
  const baseFp = searchCoreFingerprint(base, includeNumeric);
  if (baseFp == null) {
    // Pas de photo (chemin app négociateur / ancien client) -> comportement historique.
    return { blocked: false };
  }
  const fromPending = payload.from_pending === true;
  const rawIndex = cleanString(payload.search_index !== undefined ? payload.search_index : payload.searchIndex);
  const searchIndex = /^\d+$/.test(rawIndex) ? Number(rawIndex) : 0;

  await logJob(job.id, "search_overwrite_guard", "running", "Garde-fou : relecture Hektor avant écriture recherche", {
    hektor_contact_id: String(contactId),
    search_index: searchIndex,
    from_pending: fromPending,
  });
  await runContactRefreshPipeline(job, String(contactId), "search_overwrite_guard");

  // from_pending : la recherche dirty est sautée par le push (C) -> Supabase garde l'état
  // optimiste. On compare donc à l'état Hektor FRAIS lu dans le local.
  const fresh = fromPending
    ? await fetchLocalContactSearchSnapshot(job, contactId, searchIndex)
    : await fetchFreshContactSearchSnapshot(contactId, searchIndex);
  const freshFp = fresh ? searchCoreFingerprint(fresh, includeNumeric) : null;

  if (fresh && freshFp === baseFp) {
    await logJob(job.id, "search_overwrite_guard", "done", "Base inchangée côté Hektor : écriture autorisée", {
      hektor_contact_id: String(contactId),
      search_index: searchIndex,
    });
    return { blocked: false };
  }

  await notifyNegoSearchConflict(job, contactId, payload, { found: Boolean(fresh), negoEmail });
  await logJob(job.id, "search_overwrite_guard", "done", "Recherche modifiée côté Hektor : écriture bloquée (anti-écrasement)", {
    hektor_contact_id: String(contactId),
    search_index: searchIndex,
    fresh_found: Boolean(fresh),
  });
  return {
    blocked: true,
    result: {
      status: "held_conflict",
      hektor_contact_id: String(contactId),
      search_index: searchIndex,
      reason: fresh ? "negociateur_a_modifie_la_recherche_dans_hektor" : "recherche_introuvable_cote_hektor",
    },
  };
}

async function handleUpdateHektorContactSearch(job) {
  const payload = safeJsonParse(job.payload_json);
  const { contactId, contextPayload, context } = await ensureContactSearchExecution(job, payload);

  const idCritere = await resolveContactSearchTargetCritereId(job, contactId, payload);

  // Affinage Supabase-first (E) : ce job vient-il du balayage débounce d'un pending ?
  const fromPending = payload.from_pending === true;
  const pendingIndex = Number(payload.search_index);

  // Correctif n°1 — anti-écrasement : si la recherche a été modifiée dans Hektor
  // depuis l'édition (par un négociateur), on protège sa saisie et on n'écrit pas.
  const guard = await guardContactSearchOverwrite(job, contactId, payload, context.contact && context.contact.negociateur_email);
  if (guard.blocked) {
    if (fromPending) await markSearchPendingConflict(contactId, pendingIndex);
    return { ...guard.result, idCritere };
  }

  const contact = contactSearchExecutionContact(payload, context.contact);
  const spec = contactSearchSpecFromPayload(payload);
  spec.criteresId = idCritere;
  const wrappedPayload = {
    ...contextPayload,
    __prime_contact_search_wizard: true,
    contact_next_step: spec,
  };

  const search = await createHektorContactSearchCriteria(job, contactId, contact, wrappedPayload);
  if (search && search.status === "skipped") {
    throw new Error(`Recherche contact non modifiee (${search.reason || "payload incomplet"})`);
  }

  // Affinage Supabase-first (E) : push Hektor confirmé -> on efface le pending (avant
  // l'after-refresh, pour qu'il resynchronise normalement).
  if (fromPending) await clearSearchPending(contactId, pendingIndex);

  await sleep(1000);
  const syncJob = await enqueueRefreshConsoleContactDataJobBestEffort(job, contactId, {
    reason: "update_hektor_contact_search",
    priority: 82,
  });

  return {
    status: "updated",
    hektor_contact_id: contactId,
    idCritere,
    search,
    sync_job: syncJob,
  };
}

// Archive (= suppression cote app) une recherche via modifDateArchiveCritere.
async function archiveHektorContactSearch(job, contactId, idCritere) {
  const now = new Date();
  const dateArchive = `${String(now.getDate()).padStart(2, "0")}-${String(now.getMonth() + 1).padStart(2, "0")}-${now.getFullYear()}`;
  await logJob(job.id, "hektor_contact_search_archive", "running", "Archivage recherche contact Hektor", {
    hektor_contact_id: String(contactId),
    idCritere: String(idCritere),
    dateArchive,
  });
  const body = new URLSearchParams({
    mode: "contacts-contactProfile-modifDateArchiveCritere",
    idCritere: String(idCritere),
    dateArchive,
  });
  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(String(contactId))}`,
      "X-Requested-With": "XMLHttpRequest",
    },
  });
  let parsed = response.text;
  try {
    parsed = JSON.parse(response.text);
  } catch (_) {
    parsed = response.text;
  }
  await logJob(job.id, "hektor_contact_search_archive", "done", "Recherche contact Hektor archivee", {
    hektor_contact_id: String(contactId),
    idCritere: String(idCritere),
    result: parsed,
  });
  return { dateArchive, result: parsed };
}

async function handleDeleteHektorContactSearch(job) {
  const payload = safeJsonParse(job.payload_json);
  const { contactId } = await ensureContactSearchExecution(job, payload);
  const idCritere = await resolveContactSearchTargetCritereId(job, contactId, payload);
  const archive = await archiveHektorContactSearch(job, contactId, idCritere);
  await sleep(1000);
  const syncJob = await enqueueRefreshConsoleContactDataJobBestEffort(job, contactId, {
    reason: "delete_hektor_contact_search",
    priority: 82,
  });
  return {
    status: "archived",
    hektor_contact_id: contactId,
    idCritere,
    archive,
    sync_job: syncJob,
  };
}

async function createHektorMandantContact(job, annonceId, payload) {
  const lastName = cleanString(payload.last_name || payload.nom || payload.name);
  const firstName = cleanString(payload.first_name || payload.prenom);
  const email = cleanString(payload.email);
  const phone = cleanString(payload.phone || payload.telephone || payload.mobile);
  const civility = cleanString(payload.civility || payload.civilite) || "";
  const address = cleanString(payload.address || payload.adresse);
  const city = cleanString(payload.city || payload.ville);
  const postalCode = cleanString(payload.postal_code || payload.code_postal || payload.code);

  if (!lastName) throw new Error("Nom mandant requis");
  if (!email) throw new Error("Email mandant requis");

  const formHtml = await fetchHektorManualMandantForm();
  const values = extractHektorFormValues(formHtml, null);
  values.set("mode", "contacts-actions-insertManuelContactFromOtherObject");
  values.set("statut", "1");
  values.set("qualification", "3");
  values.set("saveOrUpdate", "mandantOnAnnonce");
  values.set("saveOrUpdateValue", String(annonceId));
  values.set("civilite", civility);
  values.set("nom", lastName);
  values.set("prenom", firstName || "");
  replaceParam(values, "label_email[]", "email");
  replaceParam(values, "id_email[]", "");
  replaceParam(values, "email[]", email);
  if (phone) {
    replaceParam(values, "label_telephone[]", "portable");
    replaceParam(values, "id_telephone[]", "");
    replaceParam(values, "telephone[]", phone);
  }
  if (address) values.set("adresse", address);
  if (city) values.set("ville", city);
  if (postalCode) values.set("code", postalCode);

  await logJob(job.id, "hektor_mandant_create", "running", "Creation contact mandant dans Hektor", {
    hektor_annonce_id: String(annonceId),
    nom: lastName,
    prenom: firstName,
    email,
  });

  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body: values,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(String(annonceId))}`,
    },
  });
  const parsed = JSON.parse(response.text);
  const contactId = String(parsed || "").trim();
  if (!/^\d+$/.test(contactId)) {
    throw new Error(`Creation contact mandant non confirmee: ${response.text.slice(0, 500)}`);
  }
  return {
    contactId,
    lastName,
    firstName,
    email,
  };
}

async function handleCreateHektorMandantContact(job) {
  const payload = safeJsonParse(job.payload_json);
  let dossier = null;
  try {
    dossier = await loadDossier(job);
  } catch (error) {
    if (!job.hektor_annonce_id || !(payload.hektor_user_id || payload.hektor_id_user || payload.target_hektor_user_id)) throw error;
    dossier = {
      app_dossier_id: job.app_dossier_id || payload.app_dossier_id || null,
      hektor_annonce_id: String(job.hektor_annonce_id),
      negociateur_email: payload.hektor_user_email || null,
    };
  }
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });

  const annonceId = String(dossier.hektor_annonce_id);
  const created = await createHektorMandantContact(job, annonceId, payload);
  await sleep(1800);

  let after = await fetchHektorProspectsList(annonceId);
  if (!hektorProspectLinkedInHtml(after.text, created.contactId, annonceId)) {
    await logJob(job.id, "hektor_mandant_create", "running", "Association automatique absente, tentative association mandant", {
      hektor_annonce_id: annonceId,
      hektor_contact_id: created.contactId,
    });
    await hektorFetch(`${XMLRPC_URL}?mode=selectnouveauproprio_sup&id=${encodeURIComponent(created.contactId)}&idann=${encodeURIComponent(annonceId)}`);
    await sleep(1800);
    after = await fetchHektorProspectsList(annonceId);
  }
  if (!hektorProspectLinkedInHtml(after.text, created.contactId, annonceId)) {
    throw new Error(`Creation contact OK mais association mandant non confirmee pour ${created.contactId}`);
  }

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
    reason: "create_hektor_mandant_contact",
    priority: 80,
  });
  const contactSyncJob = await enqueueRefreshConsoleContactDataJobBestEffort(job, created.contactId, {
    reason: "create_hektor_mandant_contact",
    priority: 82,
  });

  return {
    status: "created_and_linked",
    hektor_annonce_id: annonceId,
    hektor_contact_id: created.contactId,
    contact: {
      nom: created.lastName,
      prenom: created.firstName,
      email: created.email,
    },
    sync_job: syncJob,
    contact_sync_job: contactSyncJob,
  };
}

async function updateHektorMandantContact(job, annonceId, contactId, payload) {
  const lastName = cleanString(payload.last_name || payload.nom || payload.name);
  const firstName = payload.first_name !== undefined || payload.prenom !== undefined
    ? cleanString(payload.first_name || payload.prenom) || ""
    : null;
  const email = cleanString(payload.email);
  const phone = payload.phone !== undefined || payload.telephone !== undefined || payload.mobile !== undefined
    ? cleanString(payload.phone || payload.telephone || payload.mobile) || ""
    : null;
  const civility = payload.civility !== undefined || payload.civilite !== undefined
    ? cleanString(payload.civility || payload.civilite) || ""
    : null;
  const address = payload.address !== undefined || payload.adresse !== undefined
    ? cleanString(payload.address || payload.adresse) || ""
    : null;
  const city = payload.city !== undefined || payload.ville !== undefined
    ? cleanString(payload.city || payload.ville) || ""
    : null;
  const postalCode = payload.postal_code !== undefined || payload.code_postal !== undefined || payload.code !== undefined
    ? cleanString(payload.postal_code || payload.code_postal || payload.code) || ""
    : null;

  if (!lastName) throw new Error("Nom mandant requis");
  if (!email) throw new Error("Email mandant requis");

  const formHtml = await fetchHektorContactEditForm(contactId);
  const values = extractHektorFormValues(formHtml, "mefContacts/contacts_full_accueil");
  if (!values.has("nom")) {
    throw new Error(`Formulaire edition contact Hektor introuvable pour ${contactId}`);
  }

  values.set("nom", lastName);
  if (firstName !== null) values.set("prenom", firstName);
  if (civility !== null) values.set("civilite", civility);
  replaceFirstArrayParam(values, "email[]", email);
  if (!values.has("label_email[]")) replaceFirstArrayParam(values, "label_email[]", "email");
  if (!values.has("id_email[]")) replaceFirstArrayParam(values, "id_email[]", "");
  if (phone !== null) {
    replaceFirstArrayParam(values, "telephone[]", phone);
    if (!values.has("label_telephone[]")) replaceFirstArrayParam(values, "label_telephone[]", "portable");
    if (!values.has("id_telephone[]")) replaceFirstArrayParam(values, "id_telephone[]", "");
  }
  if (address !== null) values.set("adresse", address);
  if (city !== null) values.set("ville", city);
  if (postalCode !== null) values.set("code", postalCode);

  const body = new URLSearchParams();
  body.set("mode", "contacts-saveDataEditContact");
  body.set("group", "mefContacts/contacts_full_accueil");
  body.set("idContact", String(contactId));
  for (const [key, value] of values.entries()) body.append(key, value);

  await logJob(job.id, "hektor_mandant_update", "running", "Modification contact mandant dans Hektor", {
    hektor_annonce_id: String(annonceId),
    hektor_contact_id: String(contactId),
    fields: Object.keys(payload || {}).filter((key) => payload[key] != null),
  });

  const response = await hektorFetch(XMLRPC_URL, {
    method: "POST",
    body,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(String(contactId))}`,
    },
  });

  let parsed = null;
  try {
    parsed = JSON.parse(response.text);
  } catch (_) {
    parsed = response.text;
  }
  const parsedText = typeof parsed === "string" ? parsed : JSON.stringify(parsed);
  if (/emailErrors|erreur|error/i.test(parsedText) && !/content_mefContacts/i.test(parsedText)) {
    throw new Error(`Modification contact Hektor refusee: ${parsedText.slice(0, 500)}`);
  }

  return {
    hektor_contact_id: String(contactId),
    hektor_annonce_id: String(annonceId),
    contact: {
      civilite: civility,
      nom: lastName,
      prenom: firstName,
      email,
      telephone: phone,
      adresse: address,
      code: postalCode,
      ville: city,
    },
  };
}

async function handleUpdateHektorMandantContact(job) {
  const payload = safeJsonParse(job.payload_json);
  let dossier = null;
  try {
    dossier = await loadDossier(job);
  } catch (error) {
    if (!job.hektor_annonce_id || !(payload.hektor_user_id || payload.hektor_id_user || payload.target_hektor_user_id || payload.hektor_user_email)) throw error;
    dossier = {
      app_dossier_id: job.app_dossier_id || payload.app_dossier_id || null,
      hektor_annonce_id: String(job.hektor_annonce_id),
      negociateur_email: payload.hektor_user_email || null,
    };
  }
  await ensureHektorExecutionContext(job, dossier, payload, { preferRequester: true, preferDossierOwner: true, required: true });

  const annonceId = String(dossier.hektor_annonce_id);
  const contactId = String(payload.hektor_contact_id || payload.contact_id || "").trim();
  if (!/^\d+$/.test(contactId)) throw new Error("contact_id Hektor numerique requis");

  const before = await fetchHektorProspectsList(annonceId);
  if (!hektorProspectLinkedInHtml(before.text, contactId, annonceId)) {
    throw new Error(`Le contact ${contactId} n'est pas lie comme mandant de l'annonce ${annonceId}`);
  }

  const updated = await updateHektorMandantContact(job, annonceId, contactId, payload);
  await sleep(1200);

  const after = await fetchHektorProspectsList(annonceId);
  if (!hektorProspectLinkedInHtml(after.text, contactId, annonceId)) {
    throw new Error(`Modification contact OK mais association mandant non confirmee pour ${contactId}`);
  }

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
    reason: "update_hektor_mandant_contact",
    priority: 80,
  });
  const contactSyncJob = await enqueueRefreshConsoleContactDataJobBestEffort(job, contactId, {
    reason: "update_hektor_mandant_contact",
    priority: 82,
  });

  return {
    status: "updated",
    ...updated,
    sync_job: syncJob,
    contact_sync_job: contactSyncJob,
  };
}

async function loadConsoleDocumentsForAnnonce(hektorAnnonceId) {
  const params = new URLSearchParams({
    select: "id,storage_path,metadata_json,document_name",
    hektor_annonce_id: `eq.${String(hektorAnnonceId)}`,
  });
  const rows = await supabaseRequest(`app_console_document?${params.toString()}`, { method: "GET" });
  return Array.isArray(rows) ? rows : [];
}

async function cleanupConsoleDocumentsForAnnonce(hektorAnnonceId) {
  const rows = await loadConsoleDocumentsForAnnonce(hektorAnnonceId);
  const deletedStorage = [];
  const deletedLocal = [];
  for (const document of rows) {
    if (document.storage_path) {
      await deleteStorageObject(document.storage_path);
      deletedStorage.push(document.storage_path);
    }
    const metadata = document.metadata_json || {};
    const localPath = metadata.local_archive_path;
    if (isReadableFile(localPath)) {
      fs.unlinkSync(localPath);
      deletedLocal.push(localPath);
    }
  }
  await supabaseRequest(`app_console_document?hektor_annonce_id=eq.${encodeURIComponent(String(hektorAnnonceId))}`, {
    method: "DELETE",
    prefer: "return=minimal",
  });
  return {
    indexed_documents: rows.length,
    storage_objects_deleted: deletedStorage.length,
    local_files_deleted: deletedLocal.length,
  };
}

async function deleteSupabaseRows(table, filters) {
  const results = [];
  for (const [column, value] of filters) {
    if (value == null || String(value).trim() === "") continue;
    try {
      await supabaseRequest(`${table}?${column}=eq.${encodeURIComponent(String(value))}`, {
        method: "DELETE",
        prefer: "return=minimal",
      });
      results.push({ table, column, status: "done" });
    } catch (error) {
      const message = error && error.message ? error.message : String(error);
      results.push({ table, column, status: "error", error: message });
    }
  }
  return results;
}

async function cleanupSupabaseAnnonceRows(appDossierId, hektorAnnonceId) {
  const filters = [
    ["app_dossier_id", appDossierId],
    ["hektor_annonce_id", hektorAnnonceId],
  ];
  const tables = [
    "app_contact_relation_current",
    "app_work_item_current",
    "app_dossier_detail_current",
    "app_mandat_broadcast_current",
    "app_mandat_register_current",
    "app_diffusion_target",
    "app_dossier_current",
  ];
  const results = [];
  for (const table of tables) {
    results.push(...await deleteSupabaseRows(table, filters));
  }
  return results;
}

async function cleanupSupabaseContactRows(hektorContactId) {
  const filters = [["hektor_contact_id", hektorContactId]];
  const tables = [
    "app_contact_search_current",
    "app_contact_relation_current",
    "app_contact_duplicate_member_current",
    "app_contact_current",
  ];
  const results = [];
  for (const table of tables) {
    results.push(...await deleteSupabaseRows(table, filters));
  }
  return results;
}

async function loadSupabaseContactRelationsForCleanup(hektorContactId) {
  const params = new URLSearchParams({
    select: "hektor_annonce_id,app_dossier_id,role_contact,numero_dossier,numero_mandat",
    hektor_contact_id: `eq.${String(hektorContactId)}`,
    order: "last_seen_at.desc",
  });
  const rows = await supabaseRequest(`app_contact_relation_current?${params.toString()}`, { method: "GET" });
  return Array.isArray(rows) ? rows : [];
}

async function runDeletedAnnonceLocalCleanup(job, hektorAnnonceId, appDossierId) {
  const args = ["phase2/sync/delete_local_annonce.py", "--id-annonce", String(hektorAnnonceId)];
  if (appDossierId != null) args.push("--app-dossier-id", String(appDossierId));
  const output = await runProjectPythonScript(args);
  let parsed = null;
  try {
    parsed = JSON.parse(output.stdout || "{}");
  } catch (_) {
    parsed = { stdout: output.stdout || null, stderr: output.stderr || null };
  }
  await logJob(job.id, "local_cleanup", "done", "Caches locaux nettoyes pour annonce supprimee", parsed);
  return parsed;
}

async function runDeletedContactLocalCleanup(job, hektorContactId) {
  const output = await runProjectPythonScript(["phase2/sync/delete_local_contact.py", "--contact-id", String(hektorContactId)]);
  let parsed = null;
  try {
    parsed = JSON.parse(output.stdout || "{}");
  } catch (_) {
    parsed = { stdout: output.stdout || null, stderr: output.stderr || null };
  }
  await logJob(job.id, "local_cleanup", "done", "Caches locaux nettoyes pour contact supprime", parsed);
  return parsed;
}

async function insertDeletedAnnonceLog(job, payload) {
  try {
    await supabaseRequest("app_console_deleted_annonce_log", {
      method: "POST",
      body: JSON.stringify([{
        job_id: job.id,
        app_dossier_id: payload.app_dossier_id == null ? null : payload.app_dossier_id,
        hektor_annonce_id: String(payload.hektor_annonce_id),
        requested_by: job.requested_by || null,
        reason: payload.reason || null,
        before_json: payload.before_json || null,
        result_json: payload.result_json || null,
      }]),
    });
  } catch (error) {
    await logJob(job.id, "delete_audit", "error", "Journal de suppression non ecrit", {
      error: error && error.message ? error.message : String(error),
    });
  }
}

async function insertDeletedContactLog(job, payload) {
  try {
    await supabaseRequest("app_console_deleted_contact_log", {
      method: "POST",
      body: JSON.stringify([{
        job_id: job.id,
        hektor_contact_id: String(payload.hektor_contact_id),
        requested_by: job.requested_by || null,
        reason: payload.reason || null,
        before_json: payload.before_json || null,
        result_json: payload.result_json || null,
      }]),
    });
  } catch (error) {
    await logJob(job.id, "delete_contact_audit", "error", "Journal de suppression contact non ecrit", {
      error: error && error.message ? error.message : String(error),
    });
  }
}

async function handleDeleteHektorContact(job) {
  const payload = safeJsonParse(job.payload_json);
  const contactId = String(payload.hektor_contact_id || payload.contact_id || "").trim();
  if (!/^\d+$/.test(contactId)) throw new Error("contact_id Hektor numerique requis");
  const expectedConfirm = `SUPPRIMER CONTACT ${contactId}`;
  if (payload.confirm_text !== expectedConfirm) {
    throw new Error(`Confirmation suppression contact invalide pour ${contactId}`);
  }

  await ensureAdminHektorWriteSession(job, "delete_contact_admin_login");
  await logJob(job.id, "hektor_contact_delete", "running", "Verification contact avant suppression", {
    hektor_contact_id: contactId,
  });
  const before = await fetchHektorContactBeforeDelete(job, contactId);
  let relatedAnnonces = [];
  try {
    relatedAnnonces = await loadSupabaseContactRelationsForCleanup(contactId);
  } catch (error) {
    await logJob(job.id, "contact_relations_snapshot", "error", "Relations annonce non lues avant suppression", {
      hektor_contact_id: contactId,
      error: error && error.message ? error.message : String(error),
    });
  }
  let hektorDeleteSent = false;

  if (before.exists !== false) {
    const body = new URLSearchParams({
      mode: "contacts-contactProfile-deleteContact",
      id: contactId,
    });
    await hektorFetch(XMLRPC_URL, {
      method: "POST",
      body,
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        Referer: `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(contactId)}`,
      },
    });
    hektorDeleteSent = true;
    await sleep(1800);
  }

  const after = await fetchHektorContactBeforeDelete(job, contactId);
  if (hektorDeleteSent && after.exists === true) {
    throw new Error(`Suppression Hektor non confirmee pour contact ${contactId}`);
  }
  await logJob(job.id, "hektor_contact_delete", "done", "Suppression Hektor envoyee", {
    hektor_contact_id: contactId,
    before_found: before.exists,
    after_found: after.exists,
    hektor_delete_sent: hektorDeleteSent,
  });

  const cleanup = {
    pending_contact_sync_jobs: null,
    related_annonce_sync_jobs: [],
    supabase_rows: null,
    local: null,
    build: null,
    push: null,
    errors: [],
  };
  try {
    cleanup.pending_contact_sync_jobs = await cancelPendingContactRefreshJobs(job, contactId);
  } catch (error) {
    cleanup.errors.push({ step: "pending_contact_sync_jobs", error: error && error.message ? error.message : String(error) });
  }
  try {
    const uniqueAnnonceIds = Array.from(new Set(relatedAnnonces.map((relation) => String(relation.hektor_annonce_id || "").trim()).filter(Boolean)));
    for (const annonceId of uniqueAnnonceIds) {
      const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
        reason: "delete_hektor_contact",
        priority: 82,
      });
      cleanup.related_annonce_sync_jobs.push(syncJob);
    }
  } catch (error) {
    cleanup.errors.push({ step: "related_annonce_sync_jobs", error: error && error.message ? error.message : String(error) });
  }
  try {
    cleanup.supabase_rows = await cleanupSupabaseContactRows(contactId);
  } catch (error) {
    cleanup.errors.push({ step: "supabase_rows", error: error && error.message ? error.message : String(error) });
  }
  try {
    cleanup.local = await runDeletedContactLocalCleanup(job, contactId);
  } catch (error) {
    cleanup.errors.push({ step: "local", error: error && error.message ? error.message : String(error) });
  }
  cleanup.build = { status: "skipped", reason: "contact_delete_cleanup_is_already_scoped" };
  cleanup.push = { status: "skipped", reason: "contact_delete_cleanup_is_already_scoped" };

  const result = {
    deleted_hektor_contact_id: contactId,
    before_contact: payload.before_contact || before || null,
    related_annonce_count: relatedAnnonces.length,
    after_found: after.exists,
    hektor_delete_sent: hektorDeleteSent,
    cleanup,
  };
  await insertDeletedContactLog(job, {
    hektor_contact_id: contactId,
    reason: payload.reason || null,
    before_json: payload.before_contact || before || null,
    result_json: result,
  });
  return result;
}

async function handleDeleteHektorAnnonce(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorAnnonceId = String(job.hektor_annonce_id || payload.hektor_annonce_id || "").trim();
  const appDossierId = job.app_dossier_id == null ? payload.app_dossier_id : job.app_dossier_id;
  if (!hektorAnnonceId) throw new Error("hektor_annonce_id required");
  const expectedConfirm = `SUPPRIMER ${hektorAnnonceId}`;
  if (payload.confirm_text !== expectedConfirm) {
    throw new Error(`Confirmation suppression invalide pour annonce ${hektorAnnonceId}`);
  }

  await ensureAdminHektorWriteSession(job, "delete_annonce_admin_login");
  await logJob(job.id, "hektor_annonce_delete", "running", "Verification annonce avant suppression", {
    hektor_annonce_id: hektorAnnonceId,
    app_dossier_id: appDossierId || null,
  });
  const before = await fetchHektorPropertyByIdBestEffort(job, hektorAnnonceId, "hektor_annonce_delete_verify_before");
  const deleteUrl = `${XMLRPC_URL}?mode=supprimeannonce&id=${encodeURIComponent(hektorAnnonceId)}&path=undefined`;
  await hektorFetch(deleteUrl, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(hektorAnnonceId)}`,
    },
  });
  await sleep(2500);
  const after = await fetchHektorPropertyByIdBestEffort(job, hektorAnnonceId, "hektor_annonce_delete_verify_after");
  if (after && after.archived === false) {
    throw new Error(`Suppression Hektor non confirmee pour annonce ${hektorAnnonceId}`);
  }
  await logJob(job.id, "hektor_annonce_delete", "done", "Suppression Hektor envoyee et verifiee", {
    hektor_annonce_id: hektorAnnonceId,
    before_found: Boolean(before),
    after_found: Boolean(after),
    after_archived: after ? after.archived : null,
  });

  const cleanup = {
    documents: null,
    supabase_rows: null,
    local: null,
    errors: [],
  };
  try {
    cleanup.documents = await cleanupConsoleDocumentsForAnnonce(hektorAnnonceId);
  } catch (error) {
    cleanup.errors.push({ step: "documents", error: error && error.message ? error.message : String(error) });
  }
  try {
    cleanup.supabase_rows = await cleanupSupabaseAnnonceRows(appDossierId, hektorAnnonceId);
  } catch (error) {
    cleanup.errors.push({ step: "supabase_rows", error: error && error.message ? error.message : String(error) });
  }
  try {
    cleanup.local = await runDeletedAnnonceLocalCleanup(job, hektorAnnonceId, appDossierId);
  } catch (error) {
    cleanup.errors.push({ step: "local", error: error && error.message ? error.message : String(error) });
  }

  const result = {
    deleted_hektor_annonce_id: hektorAnnonceId,
    app_dossier_id: appDossierId || null,
    before_property: before && before.property ? {
      id: before.property.id,
      folderNumber: before.property.folderNumber || null,
      status: before.property.status || null,
      isArchived: before.property.isArchived === true,
      isDraft: before.property.isDraft === true,
      isBroadcasted: before.property.isBroadcasted === true,
      isValid: before.property.isValid === true,
    } : null,
    after_found: Boolean(after),
    cleanup,
  };

  await insertDeletedAnnonceLog(job, {
    hektor_annonce_id: hektorAnnonceId,
    app_dossier_id: appDossierId || null,
    reason: payload.reason || null,
    before_json: before && before.property ? before.property : null,
    result_json: result,
  });
  return result;
}

async function handleRestoreHektorAnnonce(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorAnnonceId = String(job.hektor_annonce_id || payload.hektor_annonce_id || "").trim();
  const appDossierId = job.app_dossier_id == null ? payload.app_dossier_id : job.app_dossier_id;
  if (!hektorAnnonceId) throw new Error("hektor_annonce_id required");

  await ensureAdminHektorWriteSession(job, "restore_annonce_admin_login");
  await logJob(job.id, "hektor_annonce_restore", "running", "Verification annonce avant desarchivage", {
    hektor_annonce_id: hektorAnnonceId,
    app_dossier_id: appDossierId || null,
  });
  const before = await fetchHektorPropertyByIdBestEffort(job, hektorAnnonceId, "hektor_annonce_restore_verify_before");

  const restoreUrl = `${XMLRPC_URL}?mode=upval&id=${encodeURIComponent(hektorAnnonceId)}&champ=archive&val=0`;
  await hektorFetch(restoreUrl, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(hektorAnnonceId)}`,
    },
  });
  await sleep(2500);

  const after = await fetchHektorPropertyByIdBestEffort(job, hektorAnnonceId, "hektor_annonce_restore_verify_after");
  if (after && after.archived === true) {
    throw new Error(`Desarchivage Hektor non confirme pour annonce ${hektorAnnonceId}`);
  }

  await logJob(job.id, "hektor_annonce_restore", "done", "Desarchivage Hektor envoye", {
    hektor_annonce_id: hektorAnnonceId,
    before_archived: before ? before.archived : null,
    after_archived: after ? after.archived : null,
  });

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, hektorAnnonceId, {
    reason: "restore_hektor_annonce",
    priority: 78,
  });

  return {
    hektor_annonce_id: hektorAnnonceId,
    app_dossier_id: appDossierId || null,
    before_property: before && before.property ? {
      id: before.property.id,
      folderNumber: before.property.folderNumber || null,
      status: before.property.status || null,
      isArchived: before.property.isArchived === true,
    } : null,
    after_property: after && after.property ? {
      id: after.property.id,
      folderNumber: after.property.folderNumber || null,
      status: after.property.status || null,
      isArchived: after.property.isArchived === true,
    } : null,
    sync_job: syncJob,
  };
}

const ARCHIVE_MAIN_CHOICES = new Set(["choiceVendu", "choiceAutre"]);
const ARCHIVE_SUB_CHOICES = {
  choiceVendu: new Set(["agence", "confrere", "proprietaire"]),
  choiceAutre: new Set(["concurence", "vendre_seule", "annuler_vente", "non_renouvele", "mandat_non_obtenu", "autre"]),
};

function normalizeArchiveReasonPayload(payload) {
  const mainChoice = String(payload.archive_main_choice || payload.main_choice || "").trim();
  const subChoice = String(payload.archive_sub_choice || payload.sub_choice || "").trim();
  if (!ARCHIVE_MAIN_CHOICES.has(mainChoice)) {
    throw new Error("Motif principal d archivage invalide");
  }
  if (!ARCHIVE_SUB_CHOICES[mainChoice] || !ARCHIVE_SUB_CHOICES[mainChoice].has(subChoice)) {
    throw new Error("Motif secondaire d archivage invalide");
  }
  const otherText = String(payload.archive_other_text || payload.autre || "").trim();
  if (mainChoice === "choiceAutre" && subChoice === "autre" && !otherText) {
    throw new Error("Le motif autre est obligatoire pour archiver");
  }
  return {
    mainChoice,
    subChoice,
    price: String(payload.archive_price || payload.prix || "").trim(),
    confrere: String(payload.archive_confrere || payload.confrere || "").trim(),
    otherText,
    confrereId: String(payload.archive_confrere_id || payload.id_confrere || "").trim(),
  };
}

async function handleArchiveHektorAnnonce(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorAnnonceId = String(job.hektor_annonce_id || payload.hektor_annonce_id || "").trim();
  const appDossierId = job.app_dossier_id == null ? payload.app_dossier_id : job.app_dossier_id;
  if (!hektorAnnonceId) throw new Error("hektor_annonce_id required");
  const reason = normalizeArchiveReasonPayload(payload);

  await ensureAdminHektorWriteSession(job, "archive_annonce_admin_login");
  await logJob(job.id, "hektor_annonce_archive", "running", "Verification annonce avant archivage", {
    hektor_annonce_id: hektorAnnonceId,
    app_dossier_id: appDossierId || null,
    main_choice: reason.mainChoice,
    sub_choice: reason.subChoice,
  });
  const before = await fetchHektorPropertyByIdBestEffort(job, hektorAnnonceId, "hektor_annonce_archive_verify_before");

  const archiveUrl = `${XMLRPC_URL}?${new URLSearchParams({
    mode: "upval",
    id: hektorAnnonceId,
    champ: "archive",
    val: "1",
  })}`;
  await hektorFetch(archiveUrl, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(hektorAnnonceId)}`,
    },
  });

  const archiveReasonParams = new URLSearchParams();
  archiveReasonParams.set("mode", "popins-StatutBien-statutBienDispatcher");
  archiveReasonParams.set("context", "validerArchivage");
  archiveReasonParams.set("idAnnonce", hektorAnnonceId);
  archiveReasonParams.set("params[id_annonce]", hektorAnnonceId);
  archiveReasonParams.set("params[prix]", reason.price);
  archiveReasonParams.set("params[confrere]", reason.confrere);
  archiveReasonParams.set("params[etat]", reason.mainChoice);
  archiveReasonParams.set("params[raison]", reason.subChoice);
  archiveReasonParams.set("params[autre]", reason.otherText);
  archiveReasonParams.set("params[id_confrere]", reason.confrereId);
  await hektorFetch(`${XMLRPC_URL}?${archiveReasonParams.toString()}`, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(hektorAnnonceId)}`,
    },
  });

  const diffusableUrl = `${XMLRPC_URL}?${new URLSearchParams({
    mode: "upval",
    id: hektorAnnonceId,
    champ: "diffusable",
    val: "0",
  })}`;
  await hektorFetch(diffusableUrl, {
    headers: {
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(hektorAnnonceId)}`,
    },
  });
  await sleep(2500);

  const after = await fetchHektorPropertyByIdBestEffort(job, hektorAnnonceId, "hektor_annonce_archive_verify_after");
  if (after && after.archived === false) {
    throw new Error(`Archivage Hektor non confirme pour annonce ${hektorAnnonceId}`);
  }

  await logJob(job.id, "hektor_annonce_archive", "done", "Archivage Hektor envoye", {
    hektor_annonce_id: hektorAnnonceId,
    before_archived: before ? before.archived : null,
    after_archived: after ? after.archived : null,
    main_choice: reason.mainChoice,
    sub_choice: reason.subChoice,
  });

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, hektorAnnonceId, {
    reason: "archive_hektor_annonce",
    priority: 78,
  });

  return {
    hektor_annonce_id: hektorAnnonceId,
    app_dossier_id: appDossierId || null,
    archive_reason: {
      main_choice: reason.mainChoice,
      sub_choice: reason.subChoice,
      other_text: reason.otherText || null,
    },
    before_property: before && before.property ? {
      id: before.property.id,
      folderNumber: before.property.folderNumber || null,
      status: before.property.status || null,
      isArchived: before.property.isArchived === true,
    } : null,
    after_property: after && after.property ? {
      id: after.property.id,
      folderNumber: after.property.folderNumber || null,
      status: after.property.status || null,
      isArchived: after.property.isArchived === true,
    } : null,
    sync_job: syncJob,
  };
}

async function handleCreateHektorDraftAnnonce(job) {
  const payload = safeJsonParse(job.payload_json);
  const creationToken = cleanString(payload.creation_token);
  const startedAtMs = Date.now();
  await ensureHektorExecutionContext(job, null, payload, { preferDossierOwner: false, required: true });

  await logJob(job.id, "hektor_annonce", "running", "Lecture GraphQL avant creation annonce", {
    property_type: payload.property_type || "Appartement",
    agence_nom: payload.agence_nom || null,
    hektor_user_id: payload.hektor_user_id || null,
    hektor_user_label: payload.hektor_user_label || null,
  });
  const before = await fetchLatestHektorProperties(1, false);
  const beforeIds = new Set(before.map((property) => String(property.id)));

  const wizardResult = await createHektorAnnonce(job, payload);
  const idannWizard = wizardResult.idannWizard;
  await rememberCreatedHektorAnnonceId(job, idannWizard);
  let initialFieldsUpdate = { status: "skipped", reason: "not_started" };

  try {
    await sleep(1200);
    initialFieldsUpdate = await applyCreatedAnnonceInitialFields(job, idannWizard, payload, { skipFinancial: true });
  } catch (error) {
    initialFieldsUpdate = {
      status: "error",
      error: error && error.message ? error.message : String(error),
    };
    await logJob(job.id, "hektor_annonce_initial_fields", "error", "Creation faite, mais champs initiaux non sauvegardes dans Hektor", {
      hektor_annonce_id: String(idannWizard),
      error: initialFieldsUpdate.error,
    });
  }

  const created = await confirmCreatedHektorAnnonce(job, idannWizard, payload, beforeIds, startedAtMs);

  if (!created) {
    throw new Error(`Creation annonce Hektor non confirmee par GraphQL apres enregistrement wizard ${idannWizard}`);
  }

  let initialMandantLinks = { status: "skipped", reason: "not_requested", links: [] };
  const initialMandantContactIds = normalizeInitialMandantContactIds(payload);
  if (initialMandantContactIds.length) {
    const links = [];
    for (const contactId of initialMandantContactIds) {
      try {
        await ensureHektorExecutionContext(job, null, payload, { preferDossierOwner: false, required: true });
        const linkResult = await linkHektorMandantContact(job, String(created.id), contactId, "hektor_mandant_link_initial");
        links.push(linkResult);
        await logJob(job.id, "hektor_mandant_link_initial", "done", "Mandant existant associe a l annonce creee", {
          hektor_annonce_id: String(created.id),
          hektor_contact_id: contactId,
          status: linkResult.status,
          wait_attempts: linkResult.waitAttempts,
        });
      } catch (error) {
        const message = error && error.message ? error.message : String(error);
        links.push({
          status: "error",
          hektor_annonce_id: String(created.id),
          hektor_contact_id: contactId,
          error: message,
        });
        await logJob(job.id, "hektor_mandant_link_initial", "error", "Annonce creee, mais mandant existant non associe", {
          hektor_annonce_id: String(created.id),
          hektor_contact_id: contactId,
          error: message,
        });
      }
    }
    initialMandantLinks = {
      status: links.some((link) => link.status === "error") ? "partial_error" : "linked",
      links,
    };
  }

  let initialMandantCreate = { status: "skipped", reason: "not_requested" };
  const initialMandantPayload = payload.initial_mandant || payload.initialMandant || null;
  if (initialMandantPayload && (cleanString(initialMandantPayload.last_name || initialMandantPayload.nom || initialMandantPayload.name) || cleanString(initialMandantPayload.email))) {
    try {
      await ensureHektorExecutionContext(job, null, payload, { preferDossierOwner: false, required: true });
      const createdContact = await createHektorMandantContact(job, created.id, {
        ...initialMandantPayload,
        hektor_user_email: payload.hektor_user_email || null,
      });
      await sleep(1800);
      let afterMandant = await fetchHektorProspectsList(created.id);
      if (!hektorProspectLinkedInHtml(afterMandant.text, createdContact.contactId, created.id)) {
        await hektorFetch(`${XMLRPC_URL}?mode=selectnouveauproprio_sup&id=${encodeURIComponent(createdContact.contactId)}&idann=${encodeURIComponent(String(created.id))}`);
        await sleep(1800);
        afterMandant = await fetchHektorProspectsList(created.id);
      }
      if (!hektorProspectLinkedInHtml(afterMandant.text, createdContact.contactId, created.id)) {
        throw new Error(`Creation contact OK mais association mandant non confirmee pour ${createdContact.contactId}`);
      }
      initialMandantCreate = {
        status: "created_and_linked",
        hektor_contact_id: createdContact.contactId,
        contact: {
          nom: createdContact.lastName,
          prenom: createdContact.firstName,
          email: createdContact.email,
        },
      };
      await logJob(job.id, "hektor_mandant_create", "done", "Mandant initial cree et associe a l annonce", {
        hektor_annonce_id: String(created.id),
        hektor_contact_id: createdContact.contactId,
      });
    } catch (error) {
      initialMandantCreate = {
        status: "error",
        error: error && error.message ? error.message : String(error),
      };
      await logJob(job.id, "hektor_mandant_create", "error", "Annonce creee, mais mandant initial non associe", {
        hektor_annonce_id: String(created.id),
        error: initialMandantCreate.error,
      });
    }
  }

  await logJob(job.id, "hektor_annonce", "done", "Annonce Hektor finalisee confirmee par GraphQL", {
    hektor_annonce_id: String(created.id),
    isDraft: created.isDraft,
    isBroadcasted: created.isBroadcasted,
    isValid: created.isValid,
  });

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, created.id, {
    reason: "create_hektor_draft_annonce",
    priority: 80,
  });

  // Création optimiste : relier la ligne provisoire au vrai bien Hektor. Le front cesse alors
  // d'afficher le doublon (dédup par hektor_annonce_id) ; le read-through ci-dessus la supprimera.
  await linkProvisionalCreation(creationToken, created.id);

  return {
    hektor_annonce_id: String(created.id),
    wizard_id: String(idannWizard),
    is_draft: created.isDraft === true,
    is_broadcasted: created.isBroadcasted === true,
    is_valid: created.isValid === true,
    folder_number: created.folderNumber || null,
    created_at_hektor: created.createdAt || null,
    property_type: created.type && created.type.name ? created.type.name : payload.property_type || null,
    initial_fields_update: initialFieldsUpdate,
    initial_mandant_links: initialMandantLinks,
    initial_mandant_create: initialMandantCreate,
    sync_job: syncJob,
    requested_payload: {
      title: payload.title || null,
      agence_nom: payload.agence_nom || null,
      city: payload.city || null,
      postal_code: payload.postal_code || null,
      price: payload.price || null,
      surface: payload.surface || null,
      room_count: payload.room_count || null,
      bedroom_count: payload.bedroom_count || null,
      initial_mandant_contact_ids: initialMandantContactIds,
      initial_mandant_contact_label: payload.initial_mandant_contact_label || payload.initialMandantContactLabel || null,
      initial_mandant: initialMandantPayload ? {
        last_name: initialMandantPayload.last_name || initialMandantPayload.nom || null,
        first_name: initialMandantPayload.first_name || initialMandantPayload.prenom || null,
        email: initialMandantPayload.email || null,
        phone: initialMandantPayload.phone || initialMandantPayload.telephone || null,
      } : null,
    },
  };
}

// Enveloppe création optimiste : si la création Hektor échoue, on marque la ligne provisoire
// en "erreur" (le front affiche "Erreur de création") avant de relancer l'erreur au runner.
async function handleCreateHektorDraftAnnonceWithProvisional(job) {
  try {
    return await handleCreateHektorDraftAnnonce(job);
  } catch (error) {
    try {
      const payload = safeJsonParse(job.payload_json);
      await markProvisionalCreationError(payload && payload.creation_token, error && error.message ? error.message : String(error));
    } catch (_) {
      /* best effort : ne jamais masquer l'erreur d'origine */
    }
    throw error;
  }
}

async function handleMatterportAction(job) {
  const payload = safeJsonParse(job.payload_json, {});
  const modelId = String(payload.matterport_model_id || "").trim();
  if (!/^[A-Za-z0-9_-]+$/.test(modelId)) {
    throw new Error("ID Matterport invalide ou manquant");
  }
  if (!fs.existsSync(MATTERPORT_STORAGE_STATE_PATH)) {
    throw new Error(`Session Matterport absente: lancer Console/matterport_playwright_login.js avant le worker`);
  }
  const commandByJobType = {
    matterport_online: "online",
    matterport_offline: "offline",
    matterport_archive: "archive",
    matterport_reactivate: "reactivate",
  };
  const command = commandByJobType[job.job_type];
  if (!command) throw new Error(`Action Matterport inconnue: ${job.job_type}`);

  await logJob(job.id, "matterport_console", "running", `Commande Matterport ${command}`, {
    matterport_model_id: modelId,
    matterport_name: payload.matterport_name || null,
  });
  const scriptPath = path.resolve(__dirname, "matterport_console_actions.js");
  const result = await runNodeScript(scriptPath, [command, modelId, "--confirm"], { timeoutMs: NODE_SCRIPT_TIMEOUT_MS });
  await logJob(job.id, "matterport_console", "done", `Commande Matterport ${command} terminee`, {
    matterport_model_id: modelId,
  });
  return {
    matterport_model_id: modelId,
    matterport_action: command,
    matterport_url: payload.matterport_url || `https://my.matterport.com/show/?m=${modelId}`,
    stdout: result.stdout.slice(-2000),
    stderr: result.stderr.slice(-1000),
  };
}

async function runHandler(job) {
  if (MATTERPORT_JOB_TYPES.has(job.job_type)) {
    if (!ENABLE_MATTERPORT_ACTIONS) {
      throw new Error("Console worker protected: set CONSOLE_WORKER_ENABLE_MATTERPORT_ACTIONS=true to execute Matterport actions.");
    }
  } else if (!ENABLE_HEKTOR_ACTIONS) {
    throw new Error("Console worker protected: set CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS=true to execute Hektor actions.");
  }
  if (!workerCanHandleJob(job.job_type)) {
    throw new Error(`Worker ${WORKER_KIND} ne doit pas executer le job ${job.job_type}. Appliquer la migration app_console_claim_next_job.`);
  }

  switch (job.job_type) {
    case "sync_console_documents":
      return handleSyncConsoleDocuments(job);
    case "prepare_document_cloud":
      return handlePrepareDocumentCloud(job);
    case "generate_estimation_pdf":
      return handleGenerateEstimationPdf(job);
    case "generate_mandat_document":
      return handleGenerateMandatDocument(job);
    case "generate_cadastre_document":
      return handleGenerateCadastreDocument(job);
    case "relance_signature":
      return handleRelanceSignature(job);
    case "cancel_signature_procedure":
      return handleCancelSignatureProcedure(job);
    case "upload_document_to_hektor":
      return handleUploadDocumentToHektor(job);
    case "delete_document_from_hektor":
      return handleDeleteDocumentFromHektor(job);
    case "sync_hektor_photos":
      return handleSyncHektorPhotos(job);
    case "upload_hektor_photo":
      return handleUploadHektorPhoto(job);
    case "prepare_archived_annonce_detail":
      return handlePrepareArchivedAnnonceDetail(job);
    case "prepare_historical_annonce_detail":
      return handlePrepareHistoricalAnnonceDetail(job);
    case "link_hektor_mandant":
      return handleLinkHektorMandant(job);
    case "create_hektor_contact":
      return handleCreateHektorContact(job);
    case "update_hektor_contact":
      return handleUpdateHektorContact(job);
    case "add_hektor_contact_search":
      return handleAddHektorContactSearch(job);
    case "update_hektor_contact_search":
      return handleUpdateHektorContactSearch(job);
    case "delete_hektor_contact_search":
      return handleDeleteHektorContactSearch(job);
    case "delete_hektor_contact":
      return handleDeleteHektorContact(job);
    case "create_hektor_mandant_contact":
      return handleCreateHektorMandantContact(job);
    case "update_hektor_mandant_contact":
      return handleUpdateHektorMandantContact(job);
    case "update_hektor_annonce_fields":
      return handleUpdateHektorAnnonceFields(job);
    case "create_hektor_mandat_auto_number":
      return handleCreateHektorMandatAutoNumber(job);
    case "delete_hektor_annonce":
      return handleDeleteHektorAnnonce(job);
    case "archive_hektor_annonce":
      return handleArchiveHektorAnnonce(job);
    case "restore_hektor_annonce":
      return handleRestoreHektorAnnonce(job);
    case "change_hektor_annonce_status":
      return handleChangeHektorAnnonceStatus(job);
    case "assign_hektor_annonce_negotiator":
      return handleAssignHektorAnnonceNegotiator(job);
    case "create_hektor_draft_annonce":
      return handleCreateHektorDraftAnnonceWithProvisional(job);
    case "matterport_online":
    case "matterport_offline":
    case "matterport_archive":
    case "matterport_reactivate":
      return handleMatterportAction(job);
    case "refresh_console_data":
      return handleRefreshConsoleData(job);
    case "refresh_console_contact_data":
      return handleRefreshConsoleContactData(job);
    case "archive_cloud_documents":
      throw new Error("archive_cloud_documents handler will be implemented after first storage sizing validation");
    default:
      throw new Error(`Unknown job type: ${job.job_type}`);
  }
}

async function runHandlerWithSessionRetry(job) {
  try {
    return await runHandler(job);
  } catch (error) {
    if (isHektorForbiddenError(error)) throw error;
    if (!isHektorSessionError(error)) throw error;
    await logJob(job.id, "hektor_session", "running", "Session Hektor invalide, relance Playwright puis retry", {
      error: error.message || String(error),
    });
    await refreshHektorSession("session_error_retry");
    try {
      const result = await runHandler(job);
      await logJob(job.id, "hektor_session", "done", "Retry apres relogin Hektor reussi", null);
      return result;
    } catch (retryError) {
      if (isHektorSessionError(retryError)) {
        await logJob(job.id, "hektor_session", "error", "Retry apres relogin Hektor echoue", {
          error: retryError.message || String(retryError),
        });
      }
      throw retryError;
    }
  }
}

async function processOnce() {
  await refreshHektorSessionIfDue();
  const job = await claimNextJob();
  if (!job) return false;

  await logJob(job.id, "claim", "running", `Job claimed by ${WORKER_ID}`, {
    worker_kind: WORKER_KIND,
    job_type: job.job_type,
    app_dossier_id: job.app_dossier_id,
    hektor_annonce_id: job.hektor_annonce_id,
  });

  try {
    const result = await withTimeout(runHandlerWithSessionRetry(job), JOB_TIMEOUT_MS, `Job ${job.job_type}`);
    await logJob(job.id, "finish", "done", "Job completed", result || {});
    await finishJob(job.id, "done", result || {}, null);
  } catch (error) {
    const message = error && error.message ? error.message : String(error);
    await logJob(job.id, "finish", "error", message, null);
    await finishJob(job.id, "error", null, message);
  }

  return true;
}

async function main() {
  requireEnv("SUPABASE_URL", SUPABASE_URL);
  requireEnv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY);
  acquireWorkerLock();

  const once = process.argv.includes("--once");
  console.log(JSON.stringify({
    worker: WORKER_ID,
    pollIntervalMs: POLL_INTERVAL_MS,
    workerKind: WORKER_KIND,
    enableHektorActions: ENABLE_HEKTOR_ACTIONS,
    mode: once ? "once" : "permanent",
    storageStatePath: STORAGE_STATE_PATH,
    actionJobTypes: Array.from(ACTION_JOB_TYPES),
    documentJobTypes: Array.from(DOCUMENT_JOB_TYPES),
    adminJobTypes: Array.from(ADMIN_JOB_TYPES),
    syncLightJobTypes: Array.from(SYNC_LIGHT_JOB_TYPES),
    syncFullJobTypes: Array.from(SYNC_FULL_JOB_TYPES),
  }));

  if (once) {
    await processOnce();
    return;
  }

  while (true) {
    try {
      const processed = await processOnce();
      if (processed) continue;
      await sleep(POLL_INTERVAL_MS);
    } catch (error) {
      console.error(error && error.stack ? error.stack : error);
      await sleep(POLL_INTERVAL_MS);
    }
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error && error.stack ? error.stack : error);
    process.exit(1);
  });
}

// Export pour tests/outils (n'affecte pas le service : lancé via `node console_job_worker.js`).
module.exports = { estimationAvisValeurHtmlPremium, renderHtmlToPdfBuffer, cadastrePlanHtml };
