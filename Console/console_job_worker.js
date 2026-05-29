const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
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
  "create_hektor_mandant_contact",
  "update_hektor_mandant_contact",
  "update_hektor_annonce_fields",
  "create_hektor_mandat_auto_number",
  "create_hektor_draft_annonce",
]);
const DOCUMENT_JOB_TYPES = new Set([
  "sync_console_documents",
  "prepare_document_cloud",
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
  return message.includes("Hektor 403");
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
    select: "hektor_contact_id,hektor_agence_id,hektor_negociateur_id,negociateur_email,commercial_nom,agence_nom,display_name,archive",
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
  return Boolean(error && (error.code === "HEKTOR_SESSION_EXPIRED" || String(error.message || "").includes("Session Hektor expiree")));
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
  }
}

async function ensureHektorExecutionContext(job, dossier, payload, options = {}) {
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

  let current = currentHektorSessionIdentity();
  if (current && current.userId === String(target.idUser)) {
    await logJob(job.id, "hektor_context", "done", "Contexte Hektor negociateur deja actif", {
      id_user: target.idUser,
      label: target.label,
      source: target.source,
    });
    return target;
  }

  current = await ensureAdminHektorWriteSession(job, "context_switch_admin_login");

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
    await refreshHektorSession("context_switch_retry_unconfirmed");
    current = currentHektorSessionIdentity();
    if (!current || current.role !== "ADMIN") {
      await logJob(job.id, "hektor_context", "error", "Session admin non confirmee apres relance avant changement de negociateur", {
        target_id_user: target.idUser,
        visible_user_id: current && current.userId ? current.userId : null,
        visible_role: current && current.role ? current.role : null,
      });
      throw new Error(`Session Hektor admin non confirmee avant deuxieme bascule negociateur ${target.idUser}`);
    }
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
    throw error;
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

async function ensureAdminHektorSession(job, reason, options = {}) {
  let current = currentHektorSessionIdentity();
  if (options.forceReturn || !current || current.role !== "ADMIN") {
    await logJob(job.id, "hektor_context", "running", "Retour session administrateur Hektor", {
      reason,
      current_user_id: current && current.userId ? current.userId : null,
      current_role: current && current.role ? current.role : null,
    });
    if (options.forceReturn || (current && current.role)) {
      try {
        await returnHektorDefaultContext();
      } catch (error) {
        if (isHektorForbiddenError(error)) throw error;
        await logJob(job.id, "hektor_context", "running", "Retour admin direct impossible, relance Playwright", {
          reason,
          error: error && error.message ? error.message : String(error),
        });
      }
    }
    current = currentHektorSessionIdentity();
    if (!current || current.role !== "ADMIN") {
      await refreshHektorSession(reason || "admin_required");
    }
    current = currentHektorSessionIdentity();
  }
  if (!current || current.role !== "ADMIN") {
    throw new Error(`Session Hektor administrateur requise, session actuelle: ${current && current.role ? current.role : "inconnue"}`);
  }
  await logJob(job.id, "hektor_context", "done", "Session Hektor administrateur active", {
    user_id: current.userId || null,
    role: current.role || null,
    alias: current.alias || null,
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
    await logJob(job.id, "hektor_context", "done", "Contexte Hektor agence deja actif", {
      id_user: targetId,
      role: current.role,
      alias: current.alias || null,
      reason,
    });
    return current;
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

async function createHektorAnnonceWithPlaywright(job, payload) {
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
  const statutAnnonce = String(payload.statutAnnonce ?? payload.statut_annonce ?? payload.status_annonce ?? 2);
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
  if (CREATE_HEKTOR_HTTP_DIRECT) {
    try {
      return await createHektorAnnonceWithHttpDirect(job, payload);
    } catch (error) {
      const createdId = error && error.createdHektorAnnonceId ? error.createdHektorAnnonceId : null;
      const sessionExpired = isHektorSessionError(error);
      await logJob(job.id, "hektor_annonce_http", "error", "Creation HTTP directe Hektor echouee", {
        error: error && error.message ? error.message : String(error),
        created_hektor_annonce_id: createdId,
        playwright_fallback: CREATE_HEKTOR_PLAYWRIGHT_FALLBACK && !createdId && !sessionExpired,
        session_retry: sessionExpired,
      });
      if (createdId || sessionExpired || !CREATE_HEKTOR_PLAYWRIGHT_FALLBACK) throw error;
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

async function runCreatedAnnonceImmediateSync(job, hektorAnnonceId) {
  const id = String(hektorAnnonceId || "").trim();
  if (!id) return { status: "skipped", reason: "missing_hektor_annonce_id" };

  const steps = [
    {
      label: "refresh_single_annonce",
      args: ["phase2/sync/refresh_single_annonce.py", "--id-annonce", id],
      timeoutMs: 120000,
    },
    {
      label: "phase2_push_single_annonce_direct",
      args: [
        "phase2/sync/push_single_annonce_to_supabase.py",
        "--hektor-annonce-id", id,
      ],
      timeoutMs: 90000,
    },
  ];

  const completed = [];
  for (const step of steps) {
    await logJob(job.id, "hektor_annonce_sync", "running", `Sync immediate: ${step.label}`, {
      hektor_annonce_id: id,
      args: step.args,
    });
    const output = await runProjectPythonScript(step.args, { timeoutMs: step.timeoutMs });
    completed.push({ step: step.label, stdout: output.stdout || null, stderr: output.stderr || null });
    await logJob(job.id, "hektor_annonce_sync", "done", `Sync immediate terminee: ${step.label}`, {
      hektor_annonce_id: id,
      stdout: output.stdout || null,
      stderr: output.stderr || null,
    });
  }

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
  const result = await runCreatedAnnonceImmediateSync(job, hektorAnnonceId);
  const cacheRefresh = await rebuildRequestedDetailCaches(job, hektorAnnonceId, payload);
  return {
    ...result,
    status: "synced",
    reason: payload.reason || null,
    parent_job_id: payload.parent_job_id || null,
    cache_refresh: cacheRefresh,
  };
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

  const detailOutput = await runProjectPythonScript([
    "phase2/sync/sync_contact_details.py",
    "--skip-listing-refresh",
    "--contact-id",
    hektorContactId,
    "--batch-size",
    "1",
    "--limit",
    "0",
    "--request-delay-seconds",
    "0",
    "--batch-pause-seconds",
    "0",
    "--max-hard-errors",
    "1",
    "--max-consecutive-hard-errors",
    "1",
    "--no-normalize",
  ], { timeoutMs: 90000, previewSize: 3000 });
  await logJob(job.id, "refresh_console_contact_data", "running", "Detail contact Hektor relu localement", {
    hektor_contact_id: hektorContactId,
    stdout: detailOutput.stdout,
    stderr: detailOutput.stderr,
  });

  const normalizeOutput = await runProjectPythonScript(["normalize_source.py"], { timeoutMs: 120000, previewSize: 2000 });
  const buildOutput = await runProjectPythonScript(["phase2/contacts/build_contacts_layer.py", "--no-reports"], { timeoutMs: 180000, previewSize: 3000 });
  const pushOutput = await runProjectPythonScript([
    "phase2/sync/push_contacts_to_supabase.py",
    "--push-mode",
    "update",
    "--contacts-scope",
    "active_or_eligible",
  ], { timeoutMs: 180000, previewSize: 3000 });

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

async function handleSyncConsoleDocuments(job) {
  const dossier = await loadDossier(job);
  await logJob(job.id, "hektor", "running", "Lecture documents Console", { hektor_annonce_id: dossier.hektor_annonce_id });
  const entries = await fetchConsoleDocumentEntries(dossier.hektor_annonce_id);
  const rows = await upsertConsoleDocuments(dossier, entries);
  const cloud = shouldKeepCloud(dossier);
  let localStored = 0;
  let cloudStored = 0;
  for (const row of rows) {
    const result = await persistConsoleDocumentFile(dossier, row, { cloud });
    localStored += result.local_path ? 1 : 0;
    cloudStored += result.cloud_available && cloud ? 1 : 0;
  }
  return {
    indexed: rows.length,
    local_stored: localStored,
    cloud_stored: cloudStored,
    cloud_policy: cloud ? "daily_cloud_scope" : "local_archive_only",
    hektor_annonce_id: String(dossier.hektor_annonce_id),
  };
}

async function handleSyncHektorPhotos(job) {
  const dossier = await loadDossier(job);
  await logJob(job.id, "hektor_photos", "running", "Lecture photos Console", {
    hektor_annonce_id: dossier.hektor_annonce_id,
  });
  const entries = await fetchConsolePhotoEntries(dossier.hektor_annonce_id);
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
    await page.waitForSelector(selector, { timeout: 45000 });
    await page.waitForFunction(() => typeof window.uploadPhotoInit === "function" || document.querySelector("#fileupload"), null, { timeout: 30000 }).catch(() => {});
    const input = page.locator(selector).first();
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

function setWizardDate(values, target, payload, aliases) {
  const value = payloadFrenchDateValue(payload, aliases);
  if (value != null) values.set(target, value);
}

function setWizardDefault(values, target, value) {
  if (!values.has(target)) values.set(target, value);
}

function exactHektorWizardFields(payload) {
  const source = payload && typeof payload === "object"
    ? (payload.hektor_wizard_fields || payload.wizard_fields || payload.wizardFields || null)
    : null;
  return source && typeof source === "object" && !Array.isArray(source) ? source : {};
}

function applyExactHektorWizardFields(body, payload, step) {
  const exact = exactHektorWizardFields(payload);
  if (!Object.keys(exact).length) return [];
  const applied = [];
  const protectedKeys = new Set(["mode", "step", "idann", "offredem", "programme_neuf", "isInterkabActive", "enabled", "content_pdf", "mdn_id"]);
  for (const [rawKey, rawValue] of Object.entries(exact)) {
    const key = String(rawKey || "").trim();
    if (!key || protectedKeys.has(key)) continue;
    if (!/^[A-Za-z0-9_[\]-]+$/.test(key)) continue;
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
  setWizardDefault(body, "surfappart", "0");
  setWizardDefault(body, "nbpieces", "0");
  setWizardDefault(body, "PRIXNETVENDEUR", "0");
  setWizardDefault(body, "NB_CHAMBRES", "0");
  setWizardDefault(body, "NB_NIVEAUX", "0");
  setWizardDefault(body, "GARAGE_BOX", "0");
  setWizardNumber(body, "prix", payload, ["price", "prix"]);
  setWizardNumber(body, "PRIXNETVENDEUR", payload, ["net_seller_price", "netSellerPrice", "prix_net_vendeur"]);
  setWizardNumber(body, "surfappart", payload, ["surface", "surfappart", "surface_habitable"]);
  setWizardNumber(body, "nbpieces", payload, ["room_count", "roomCount", "nbpieces", "pieces"]);
  setWizardNumber(body, "NB_CHAMBRES", payload, ["bedroom_count", "bedroomCount", "NB_CHAMBRES", "chambres"]);
  setWizardNumber(body, "NB_NIVEAUX", payload, ["level_count", "levelCount", "NB_NIVEAUX", "niveaux"]);
  setWizardNumber(body, "GARAGE_BOX", payload, ["garage_count", "garageCount", "GARAGE_BOX"]);
  setWizardText(body, "EXPOSITION", payload, ["exposure", "exposition", "EXPOSITION"]);
  setWizardText(body, "vuee", payload, ["view", "vue", "vuee"]);
  setWizardText(body, "NO_DOSSIER", payload, ["folder_number", "folderNumber", "no_dossier", "NO_DOSSIER"]);
  const formNegotiatorId = payloadTextValue(payload, ["hektor_negociator_form_id", "negociator_form_id", "NEGOCIATEUR"]);
  if (formNegotiatorId && !body.has("NEGOCIATEUR")) body.set("NEGOCIATEUR", formNegotiatorId);
  applyExactHektorWizardFields(body, payload, 2);
  return body;
}

function buildWizardStep4Body(idannWizard, meta, html, payload) {
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
  setWizardText(body, "immeuble", payload, ["building", "immeuble"]);
  setWizardText(body, "TRANSPORT", payload, ["transport", "TRANSPORT"]);
  setWizardText(body, "PROXIMITE", payload, ["proximity", "proximite", "PROXIMITE"]);
  setWizardText(body, "ENVIRONNEMENT", payload, ["environment", "environnement", "ENVIRONNEMENT"]);
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
  for (const field of zeroDefaults) setWizardDefault(body, field, "0");
  for (const field of ["dpe_date", "diag_termites_date", "diag_amiante_date", "diag_electrique_date", "diag_loi_carrez_date", "diag_risques_nat_tech_date", "diag_plomb_date", "diag_gaz_date", "diag_assainissement_date"]) {
    setWizardDefault(body, field, "00-00-0000");
  }
  setWizardNumber(body, "NB_CHAMBRES", payload, ["bedroom_count", "bedroomCount", "NB_CHAMBRES"]);
  setWizardNumber(body, "NB_SDB", payload, ["bathroom_count", "bathroomCount", "NB_SDB", "sdb"]);
  setWizardNumber(body, "NB_SE", payload, ["shower_room_count", "showerRoomCount", "NB_SE", "salle_eau"]);
  setWizardNumber(body, "NB_WC", payload, ["wc_count", "wcCount", "NB_WC", "wc"]);
  setWizardNumber(body, "SURF_CARREZ", payload, ["carrez_surface", "carrezSurface", "SURF_CARREZ"]);
  setWizardNumber(body, "SURF_SEJOUR", payload, ["living_surface", "livingSurface", "SURF_SEJOUR"]);
  setWizardText(body, "CUISINE", payload, ["kitchen", "cuisine", "CUISINE"]);
  setWizardText(body, "CUISINE_EQUIPEMENT", payload, ["kitchen_equipment", "kitchenEquipment", "CUISINE_EQUIPEMENT"]);
  setWizardText(body, "EXPOSITION", payload, ["exposure", "exposition", "EXPOSITION"]);
  setWizardText(body, "vuee", payload, ["view", "vue", "vuee"]);
  setWizardText(body, "etat_interieur", payload, ["interior_state", "interiorState", "etat_interieur"]);
  setWizardText(body, "etat_exterieur", payload, ["exterior_state", "exteriorState", "etat_exterieur"]);
  setWizardNumber(body, "ETAGE", payload, ["floor", "etage", "ETAGE"]);
  setWizardNumber(body, "NB_ETAGES", payload, ["floor_count", "floorCount", "NB_ETAGES"]);
  setWizardNumber(body, "NB_BALCON", payload, ["balcony_count", "balconyCount", "NB_BALCON"]);
  setWizardNumber(body, "SURFACE_BALCON", payload, ["balcony_surface", "balconySurface", "SURFACE_BALCON"]);
  setWizardNumber(body, "NB_TERRASSE", payload, ["terrace_count", "terraceCount", "NB_TERRASSE"]);
  setWizardNumber(body, "SURFACE_TERRASSE", payload, ["terrace_surface", "terraceSurface", "SURFACE_TERRASSE"]);
  setWizardNumber(body, "GARAGE_BOX", payload, ["garage_count", "garageCount", "GARAGE_BOX"]);
  setWizardNumber(body, "NB_PARK_INT", payload, ["parking_inside_count", "parkingInsideCount", "NB_PARK_INT"]);
  setWizardNumber(body, "NB_PARK_EXT", payload, ["parking_outside_count", "parkingOutsideCount", "NB_PARK_EXT"]);
  setWizardText(body, "ASCENSEUR", payload, ["elevator", "ascenseur", "ASCENSEUR"]);
  setWizardText(body, "ACCES_HANDI", payload, ["handicap_access", "handicapAccess", "ACCES_HANDI"]);
  setWizardText(body, "climatisation", payload, ["air_conditioning", "airConditioning", "climatisation"]);
  setWizardText(body, "double_vitrage", payload, ["double_glazing", "doubleGlazing", "double_vitrage"]);
  setWizardText(body, "interphone", payload, ["intercom", "interphone"]);
  setWizardText(body, "visiophone", payload, ["videophone", "visiophone"]);
  setWizardText(body, "digicode", payload, ["digicode"]);
  setWizardNumber(body, "ANNEE_CONS", payload, ["construction_year", "constructionYear", "ANNEE_CONS"]);
  setWizardNumber(body, "dpe_cons", payload, ["dpe_value", "dpeValue", "dpe_cons"]);
  setWizardNumber(body, "dpe_ges", payload, ["ges_value", "gesValue", "dpe_ges"]);
  setWizardDate(body, "dpe_date", payload, ["dpe_date", "dpeDate"]);
  setWizardText(body, "diagnostiqueur", payload, ["diagnostician", "diagnostiqueur"]);
  setWizardText(body, "syndic", payload, ["syndic"]);
  setWizardText(body, "copropriete", payload, ["copropriete", "copro"]);
  setWizardNumber(body, "copropriete_nb_lot", payload, ["copro_lots", "coproLots", "copropriete_nb_lot"]);
  setWizardNumber(body, "copropriete_quote_part", payload, ["copro_quote_part", "coproQuotePart", "copropriete_quote_part"]);
  setWizardNumber(body, "montant_fonds_travaux", payload, ["copro_works_fund", "coproWorksFund", "montant_fonds_travaux"]);
  applyExactHektorWizardFields(body, payload, 6);
  return body;
}

function buildWizardStep7Body(idannWizard, meta, html, payload) {
  const values = mergeHektorFormValues(
    extractHektorFormValues(html, "wizard_Mandant_BienInsert"),
    extractHektorFormValues(html, "mandat_infofi"),
    extractHektorFormValues(html, "mandat_investissementloc"),
  );
  const body = wizardStepBaseBody(idannWizard, 7, meta, values);
  setWizardDefault(body, "PRIXNETVENDEUR", "0");
  setWizardDefault(body, "prix", "0");
  setWizardDefault(body, "_selecterHonoraires2", "NON");
  setWizardDefault(body, "_tauxHonoraire2", "0");
  setWizardDefault(body, "_selecterHonoraires3", "NON");
  setWizardDefault(body, "_tauxHonoraire3", "0");
  setWizardDefault(body, "ESTIMATION_MONTANT", "0");
  setWizardDefault(body, "ESTIMATION_DATE", "00-00-0000");
  setWizardDefault(body, "DEPOT_GARANTIE", "0");
  setWizardDefault(body, "TAXE_HABITATION", "0");
  setWizardDefault(body, "TAXE_FONCIERE", "0");
  setWizardDefault(body, "CHARGES", "0");
  setWizardNumber(body, "PRIXNETVENDEUR", payload, ["net_seller_price", "netSellerPrice", "prix_net_vendeur"]);
  setWizardNumber(body, "prix", payload, ["price", "prix"]);
  setWizardNumber(body, "ESTIMATION_MONTANT", payload, ["estimation_amount", "estimationAmount", "ESTIMATION_MONTANT"]);
  setWizardDate(body, "ESTIMATION_DATE", payload, ["estimation_date", "estimationDate", "ESTIMATION_DATE"]);
  setWizardNumber(body, "DEPOT_GARANTIE", payload, ["deposit", "depot_garantie", "DEPOT_GARANTIE"]);
  setWizardNumber(body, "TAXE_HABITATION", payload, ["housing_tax", "housingTax", "TAXE_HABITATION"]);
  setWizardNumber(body, "TAXE_FONCIERE", payload, ["property_tax", "propertyTax", "TAXE_FONCIERE"]);
  setWizardNumber(body, "CHARGES", payload, ["copro_charges", "coproCharges", "charges", "CHARGES"]);
  setWizardText(body, "TRAVAUX", payload, ["works", "travaux", "TRAVAUX"]);
  setWizardText(body, "CHARGES_DETAIL", payload, ["charges_detail", "chargesDetail", "CHARGES_DETAIL"]);
  setWizardNumber(body, "Loc_EstimationLoyer", payload, ["rent_estimate", "rentEstimate", "Loc_EstimationLoyer"]);
  setWizardNumber(body, "Loc_ChargeLocative", payload, ["rent_charges", "rentCharges", "Loc_ChargeLocative"]);
  setWizardText(body, "Loc_Occupation", payload, ["rental_occupation", "rentalOccupation", "Loc_Occupation"]);
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
    const body = item.build(idannWizard, meta, html, payload);
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

function normalizeHektorAnnonceUpdatePayload(payload, options = {}) {
  const baseFields = payload && payload.fields_json && typeof payload.fields_json === "object" ? payload.fields_json : payload.fields || payload;
  const fields = {
    ...(baseFields && typeof baseFields === "object" ? baseFields : {}),
    ...exactHektorWizardFields(payload),
  };
  const clean = {};
  const textKeys = [
    ["title", ["title", "titre"]],
    ["description", ["description", "corps"]],
    ["kitchen", ["kitchen", "cuisine", "CUISINE"]],
    ["exposure", ["exposure", "exposition", "EXPOSITION"]],
    ["view", ["view", "vue", "vuee"]],
    ["interior_state", ["interior_state", "interiorState", "etat_interieur", "ETAT_INTERIEUR"]],
    ["exterior_state", ["exterior_state", "exteriorState", "etat_exterieur", "ETAT_EXTERIEUR"]],
    ["dpe_value", ["dpe_value", "dpeValue", "DPE", "dpe_cons"]],
    ["ges_value", ["ges_value", "gesValue", "GES", "dpe_ges"]],
    ["diagnostic_note", ["diagnostic_note", "diagnosticNote", "diag_risques_nat_tech_date"]],
    ["mandate_number", ["mandate_number", "mandateNumber", "NO_MANDAT"]],
    ["mandate_type", ["mandate_type", "mandateType"]],
    ["mandate_start_date", ["mandate_start_date", "mandateStartDate"]],
    ["mandate_end_date", ["mandate_end_date", "mandateEndDate"]],
  ];
  const numberKeys = [
    ["price", ["price", "prix"]],
    ["net_seller_price", ["net_seller_price", "netSellerPrice", "PRIXNETVENDEUR"]],
    ["surface", ["surface", "surfappart", "surface_habitable"]],
    ["carrez_surface", ["carrez_surface", "carrezSurface", "SURF_CARREZ"]],
    ["room_count", ["room_count", "roomCount", "nbpieces"]],
    ["bedroom_count", ["bedroom_count", "bedroomCount", "NB_CHAMBRES"]],
    ["bathroom_count", ["bathroom_count", "bathroomCount", "NB_SDB", "SDB"]],
    ["shower_room_count", ["shower_room_count", "showerRoomCount", "NB_SE", "SE", "SDE"]],
    ["wc_count", ["wc_count", "wcCount", "NB_WC", "WC"]],
    ["land_surface", ["land_surface", "landSurface", "surfterrain"]],
    ["garden_surface", ["garden_surface", "gardenSurface", "SURFACE_JARDIN"]],
    ["terrace_count", ["terrace_count", "terraceCount", "NB_TERRASSE", "TERRASSE"]],
    ["garage_count", ["garage_count", "garageCount", "GARAGE_BOX"]],
    ["parking_inside_count", ["parking_inside_count", "parkingInsideCount", "NB_PARK_INT"]],
    ["parking_outside_count", ["parking_outside_count", "parkingOutsideCount", "NB_PARK_EXT"]],
    ["pool", ["pool", "PISCINE"]],
    ["construction_year", ["construction_year", "constructionYear", "ANNEE_CONS", "ANNEE_CONSTRUCTION"]],
    ["copro_lots", ["copro_lots", "coproLots", "copropriete_nb_lot"]],
    ["copro_charges", ["copro_charges", "coproCharges", "CHARGES"]],
    ["copro_quote_part", ["copro_quote_part", "coproQuotePart", "copropriete_quote_part"]],
    ["copro_works_fund", ["copro_works_fund", "coproWorksFund", "montant_fonds_travaux"]],
    ["fees", ["fees", "HONORAIRES", "honoraires"]],
  ];
  const skippedFinancial = new Set(options.skipFinancial ? ["price", "net_seller_price", "copro_charges", "fees"] : []);
  for (const [key, aliases] of textKeys) {
    if (skippedFinancial.has(key)) continue;
    const raw = firstDefined(fields || {}, aliases);
    if (raw == null) continue;
    const value = String(raw).trim();
    if (value) clean[key] = value;
  }
  for (const [key, aliases] of numberKeys) {
    if (skippedFinancial.has(key)) continue;
    const raw = firstDefined(fields || {}, aliases);
    if (raw == null) continue;
    const value = String(raw).replace(",", ".").trim();
    if (value && !/^-?\d+(\.\d+)?$/.test(value)) throw new Error(`Champ numerique invalide: ${key}`);
    if (value) clean[key] = value;
  }
  return clean;
}

function fieldSpec(value, candidates) {
  return { value, candidates };
}

async function pushHektorGroupUpdate(results, job, annonceId, groupName, readMode, fields) {
  if (!Object.keys(fields).length) return;
  const result = await postHektorMefUpdate(job, annonceId, groupName, readMode, fields);
  if (result) results.push(result);
}

async function applyHektorAnnonceFieldUpdates(job, annonceId, fields) {
  const cleanFields = normalizeHektorAnnonceUpdatePayload(fields);
  const results = [];

  const textResult = await postHektorPrincipalTextUpdate(job, annonceId, {
    title: cleanFields.title,
    description: cleanFields.description,
  });
  if (textResult) results.push(textResult);

  const agInterieur = {};
  if (cleanFields.room_count != null) agInterieur.room_count = fieldSpec(cleanFields.room_count, ["nbpieces"]);
  if (cleanFields.bedroom_count != null) agInterieur.bedroom_count = fieldSpec(cleanFields.bedroom_count, ["NB_CHAMBRES"]);
  if (cleanFields.surface != null) agInterieur.surface = fieldSpec(cleanFields.surface, ["surfappart"]);
  if (cleanFields.carrez_surface != null) agInterieur.carrez_surface = fieldSpec(cleanFields.carrez_surface, ["SURF_CARREZ"]);
  if (cleanFields.bathroom_count != null) agInterieur.bathroom_count = fieldSpec(cleanFields.bathroom_count, ["SDB", "NB_SDB", "nb_sdb", "sdb"]);
  if (cleanFields.shower_room_count != null) agInterieur.shower_room_count = fieldSpec(cleanFields.shower_room_count, ["SE", "SDE", "NB_SE", "NB_SALLE_EAU", "salle_eau"]);
  if (cleanFields.wc_count != null) agInterieur.wc_count = fieldSpec(cleanFields.wc_count, ["WC", "NB_WC", "wc"]);
  if (cleanFields.kitchen != null) agInterieur.kitchen = fieldSpec(cleanFields.kitchen, ["CUISINE", "cuisine"]);
  if (cleanFields.exposure != null) agInterieur.exposure = fieldSpec(cleanFields.exposure, ["EXPOSITION", "exposition"]);
  if (cleanFields.view != null) agInterieur.view = fieldSpec(cleanFields.view, ["vuee", "VUE", "vue"]);
  if (cleanFields.interior_state != null) agInterieur.interior_state = fieldSpec(cleanFields.interior_state, ["ETAT_INTERIEUR", "ETATINT", "etat_interieur"]);
  await pushHektorGroupUpdate(results, job, annonceId, "ag_interieur", "ihmChargeGroupe", agInterieur);

  const agExterieur = {};
  if (cleanFields.exterior_state != null) agExterieur.exterior_state = fieldSpec(cleanFields.exterior_state, ["ETAT_EXTERIEUR", "ETAT_EXT", "etat_exterieur"]);
  if (cleanFields.garden_surface != null) agExterieur.garden_surface = fieldSpec(cleanFields.garden_surface, ["SURFACE_JARDIN"]);
  if (cleanFields.terrace_count != null) agExterieur.terrace_count = fieldSpec(cleanFields.terrace_count, ["NB_TERRASSE", "TERRASSE"]);
  if (cleanFields.garage_count != null) agExterieur.garage_count = fieldSpec(cleanFields.garage_count, ["GARAGE_BOX"]);
  if (cleanFields.parking_inside_count != null) agExterieur.parking_inside_count = fieldSpec(cleanFields.parking_inside_count, ["NB_PARK_INT"]);
  if (cleanFields.parking_outside_count != null) agExterieur.parking_outside_count = fieldSpec(cleanFields.parking_outside_count, ["NB_PARK_EXT"]);
  if (cleanFields.pool != null) agExterieur.pool = fieldSpec(cleanFields.pool, ["PISCINE"]);
  await pushHektorGroupUpdate(results, job, annonceId, "ag_exterieur", "ihmChargeGroupe", agExterieur);

  const terrain = {};
  if (cleanFields.land_surface != null) terrain.land_surface = fieldSpec(cleanFields.land_surface, ["surfterrain"]);
  await pushHektorGroupUpdate(results, job, annonceId, "terrain", "ihmChargeGroupe", terrain);

  const diagnostics = {};
  if (cleanFields.dpe_value != null) diagnostics.dpe_value = fieldSpec(cleanFields.dpe_value, ["dpe_cons", "DPE", "dpe", "classe_energie"]);
  if (cleanFields.ges_value != null) diagnostics.ges_value = fieldSpec(cleanFields.ges_value, ["dpe_ges", "GES", "ges", "classe_ges"]);
  if (cleanFields.construction_year != null) diagnostics.construction_year = fieldSpec(cleanFields.construction_year, ["ANNEE_CONS", "ANNEE_CONSTRUCTION", "annee_construction", "construction_year"]);
  if (cleanFields.diagnostic_note != null) diagnostics.diagnostic_note = fieldSpec(cleanFields.diagnostic_note, ["diag_risques_nat_tech_date", "dpe_date"]);
  await pushHektorGroupUpdate(results, job, annonceId, "diagnostiques", "ihmChargeGroupe", diagnostics);

  const copropriete = {};
  if (cleanFields.copro_lots != null) copropriete.copro_lots = fieldSpec(cleanFields.copro_lots, ["copropriete_nb_lot"]);
  if (cleanFields.copro_quote_part != null) copropriete.copro_quote_part = fieldSpec(cleanFields.copro_quote_part, ["copropriete_quote_part"]);
  if (cleanFields.copro_works_fund != null) copropriete.copro_works_fund = fieldSpec(cleanFields.copro_works_fund, ["montant_fonds_travaux"]);
  await pushHektorGroupUpdate(results, job, annonceId, "copropriete", "ihmChargeGroupe", copropriete);

  const mandatInfo = {};
  if (cleanFields.price != null) mandatInfo.price = fieldSpec(cleanFields.price, ["prix"]);
  if (cleanFields.net_seller_price != null) mandatInfo.net_seller_price = fieldSpec(cleanFields.net_seller_price, ["PRIXNETVENDEUR"]);
  if (cleanFields.copro_charges != null) mandatInfo.copro_charges = fieldSpec(cleanFields.copro_charges, ["CHARGES"]);
  if (cleanFields.fees != null) mandatInfo.fees = fieldSpec(cleanFields.fees, ["HONORAIRES", "honoraires", "HONORAIRES_ACQUEREUR"]);
  await pushHektorGroupUpdate(results, job, annonceId, "mandat_infofi", "ihmChargeGroupe_MandatPrix", mandatInfo);

  return results;
}

async function applyCreatedAnnonceInitialFields(job, annonceId, payload, options = {}) {
  const fields = normalizeHektorAnnonceUpdatePayload(payload, options);
  if (!Object.keys(fields).length) {
    return { status: "skipped", reason: "no_initial_fields" };
  }

  await logJob(job.id, "hektor_annonce_initial_fields", "running", "Application des champs saisis apres creation Hektor", {
    hektor_annonce_id: String(annonceId),
    fields: Object.keys(fields),
  });
  const results = await applyHektorAnnonceFieldUpdates(job, annonceId, fields);
  if (!results.length) {
    return { status: "skipped", reason: "no_supported_initial_fields", fields: Object.keys(fields) };
  }
  await logJob(job.id, "hektor_annonce_initial_fields", "done", "Champs initiaux sauvegardes dans Hektor", {
    hektor_annonce_id: String(annonceId),
    updated_groups: results.map((item) => item.group),
  });
  return { status: "updated", updated_groups: results };
}

async function handleUpdateHektorAnnonceFields(job) {
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
  const results = await applyHektorAnnonceFieldUpdates(job, annonceId, payload);

  if (!results.length) throw new Error("Aucun champ annonce modifiable fourni");

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
  const before = await fetchHektorProspectsList(annonceId);
  if (hektorProspectLinkedInHtml(before.text, contactId, annonceId)) {
    return {
      status: "already_linked",
      hektor_annonce_id: annonceId,
      hektor_contact_id: contactId,
    };
  }

  await logJob(job.id, "hektor_mandant", "running", "Association mandant/proprietaire dans Hektor", {
    hektor_annonce_id: annonceId,
    hektor_contact_id: contactId,
  });

  await hektorFetch(`${XMLRPC_URL}?mode=selectnouveauproprio_sup&id=${encodeURIComponent(contactId)}&idann=${encodeURIComponent(annonceId)}`);
  await sleep(1800);

  const after = await fetchHektorProspectsList(annonceId);
  if (!hektorProspectLinkedInHtml(after.text, contactId, annonceId)) {
    throw new Error(`Association mandant non confirmee pour contact ${contactId} sur annonce ${annonceId}`);
  }

  const syncJob = await enqueueRefreshConsoleDataJobBestEffort(job, annonceId, {
    reason: "link_hektor_mandant",
    priority: 80,
  });

  return {
    status: "linked",
    hektor_annonce_id: annonceId,
    hektor_contact_id: contactId,
    sync_job: syncJob,
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
  const text = cleanString(value).toLowerCase()
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
  const text = cleanString(value).toLowerCase()
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
  };
  return map[text] || map[String(value || "").trim()] || fallback;
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
  const lastName = cleanString(source.last_name || source.nom || source.name);
  const firstName = source.first_name !== undefined || source.prenom !== undefined
    ? cleanString(source.first_name || source.prenom) || ""
    : cleanString(source.first_name || source.prenom);
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
  return {
    contactId,
    civility,
    lastName,
    firstName,
    email,
    phone,
    phoneSecondary,
    address,
    postalCode,
    city,
    birthDate: rawBirthDate !== undefined ? normalizeOptionalFrenchDate(rawBirthDate) : null,
    birthPlace: rawBirthPlace !== undefined ? cleanString(rawBirthPlace) || "" : null,
    maritalStatus: rawMaritalStatus !== undefined ? cleanString(rawMaritalStatus) || "" : null,
    qualification: normalizeHektorContactQualification(
      source.qualification || source.contact_qualification || source.contact_kind || source.kind,
      "2"
    ),
    contactStatus: normalizeHektorContactStatus(
      source.statut || source.status || source.contact_status || source.person_type || source.personType,
      "1"
    ),
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
  if (contact.civility !== null && contact.civility !== undefined) values.set("civilite", contact.civility || "");
  if (contact.lastName) values.set("nom", contact.lastName);
  if (contact.firstName !== null && contact.firstName !== undefined) values.set("prenom", contact.firstName || "");
  if (contact.email !== null && contact.email !== undefined) {
    replaceParam(values, "label_email[]", "email");
    replaceParam(values, "id_email[]", "");
    replaceParam(values, "email[]", contact.email || "");
  }
  if (contact.phone !== null || contact.phoneSecondary !== null) {
    replaceContactTelephoneParams(values, contact.phone || "", contact.phoneSecondary || "");
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
    negotiatorId: contact.targetNegotiatorId,
  });
  const values = extractHektorFormValues(formHtml, null);
  values.set("mode", "contacts-actions-insertManuelContactFromOtherObject");
  values.set("statut", contact.contactStatus);
  values.set("qualification", contact.qualification);
  values.delete("saveOrUpdate");
  values.delete("saveOrUpdateValue");
  applyHektorContactIdentityValues(values, contact);

  await logJob(job.id, "hektor_contact_create", "running", "Creation contact global dans Hektor", {
    nom: contact.lastName,
    prenom: contact.firstName,
    email: contact.email,
    phone: contact.phone,
    qualification: contact.qualification,
    statut: contact.contactStatus,
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

async function updateHektorContactIdentity(job, contactId, payload) {
  const contact = normalizeHektorContactPayload({ ...payload, hektor_contact_id: contactId }, { requireContactId: true, requireName: true });
  const formHtml = await fetchHektorContactEditForm(contactId);
  const values = extractHektorFormValues(formHtml, "mefContacts/contacts_full_accueil");
  if (!values.has("nom")) {
    throw new Error(`Formulaire edition contact Hektor introuvable pour ${contactId}`);
  }
  applyHektorContactIdentityValues(values, contact);

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
      email: contact.email,
      telephone: contact.phone,
      telephone_secondaire: contact.phoneSecondary,
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
      email: created.email,
      telephone: created.phone,
      date_naissance: created.birthDate,
      lieu_naissance: created.birthPlace,
      statut_matrimonial: created.maritalStatus,
    },
    crm_settings: crmSettings,
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

  const updated = await updateHektorContactIdentity(job, contactId, contextPayload);
  const crmSettings = await updateHektorContactCrmSettings(job, contactId, contextPayload);
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

  return {
    status: "updated",
    ...updated,
    sync_job: syncJob,
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
  try {
    const buildOutput = await runProjectPythonScript(["phase2/contacts/build_contacts_layer.py", "--no-reports"], { timeoutMs: 180000, previewSize: 3000 });
    cleanup.build = { stdout: buildOutput.stdout, stderr: buildOutput.stderr };
  } catch (error) {
    cleanup.errors.push({ step: "build_contacts_layer", error: error && error.message ? error.message : String(error) });
  }
  try {
    const pushOutput = await runProjectPythonScript([
      "phase2/sync/push_contacts_to_supabase.py",
      "--push-mode",
      "update",
      "--contacts-scope",
      "active_or_eligible",
    ], { timeoutMs: 180000, previewSize: 3000 });
    cleanup.push = { stdout: pushOutput.stdout, stderr: pushOutput.stderr };
  } catch (error) {
    cleanup.errors.push({ step: "push_contacts_to_supabase", error: error && error.message ? error.message : String(error) });
  }

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

  let created = null;
  for (let attempt = 1; attempt <= 6; attempt += 1) {
    await sleep(attempt === 1 ? 1800 : 2500);
    const latest = await fetchLatestHektorProperties(1, false);
    const candidates = latest
      .map((property) => ({ property, score: annonceCreationScore(property, beforeIds, startedAtMs) }))
      .filter((item) => item.score >= 0)
      .sort((left, right) => right.score - left.score);
    if (candidates.length) {
      created = candidates[0].property;
      break;
    }
  }

  if (!created) {
    throw new Error(`Creation annonce Hektor non confirmee par GraphQL apres enregistrement wizard ${idannWizard}`);
  }

  let initialMandantCreate = { status: "skipped", reason: "not_requested" };
  const initialMandantPayload = payload.initial_mandant || payload.initialMandant || null;
  if (initialMandantPayload && (cleanString(initialMandantPayload.last_name || initialMandantPayload.nom || initialMandantPayload.name) || cleanString(initialMandantPayload.email))) {
    try {
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
      initial_mandant: initialMandantPayload ? {
        last_name: initialMandantPayload.last_name || initialMandantPayload.nom || null,
        first_name: initialMandantPayload.first_name || initialMandantPayload.prenom || null,
        email: initialMandantPayload.email || null,
        phone: initialMandantPayload.phone || initialMandantPayload.telephone || null,
      } : null,
    },
  };
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
      return handleCreateHektorDraftAnnonce(job);
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

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
