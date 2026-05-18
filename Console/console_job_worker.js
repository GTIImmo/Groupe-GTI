const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { spawn } = require("child_process");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${HEKTOR_BASE_URL.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const RAW_WORKER_KIND = String(process.env.CONSOLE_WORKER_KIND || process.env.CONSOLE_WORKER_MODE || "actions").toLowerCase();
const WORKER_KINDS = new Set(["actions", "documents", "admin", "sync_light", "sync_full", "sync", "all"]);
const WORKER_KIND = WORKER_KINDS.has(RAW_WORKER_KIND) ? RAW_WORKER_KIND : "actions";
const STORAGE_BUCKET = process.env.CONSOLE_STORAGE_BUCKET || "hektor-console-documents";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "sessions", `storage_state_${WORKER_KIND}.json`);
const LOCAL_ARCHIVE_ROOT = process.env.CONSOLE_LOCAL_ARCHIVE_ROOT || "C:\\HektorConsoleDocuments";
const PROJECT_ROOT = path.resolve(__dirname, "..");
const PYTHON_EXE = process.env.CONSOLE_PYTHON_EXE || path.resolve(PROJECT_ROOT, ".venv", "Scripts", "python.exe");
const ACTION_JOB_TYPES = new Set([
  "link_hektor_mandant",
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
]);
const ADMIN_JOB_TYPES = new Set([
  "delete_hektor_annonce",
]);
const SYNC_LIGHT_JOB_TYPES = new Set([
  "refresh_console_data",
]);
const SYNC_FULL_JOB_TYPES = new Set([
  "archive_cloud_documents",
]);
const ALL_JOB_TYPES_BY_KIND = {
  actions: ACTION_JOB_TYPES,
  documents: DOCUMENT_JOB_TYPES,
  admin: ADMIN_JOB_TYPES,
  sync_light: SYNC_LIGHT_JOB_TYPES,
  sync_full: SYNC_FULL_JOB_TYPES,
};
const WORKER_ID = process.env.CONSOLE_WORKER_ID || `${os.hostname()}:${WORKER_KIND}:${process.pid}`;
const DEFAULT_POLL_INTERVAL_MS = ["sync", "sync_full"].includes(WORKER_KIND) ? 60000 : WORKER_KIND === "sync_light" ? 10000 : 5000;
const POLL_INTERVAL_MS = Number(process.env.CONSOLE_WORKER_POLL_INTERVAL_MS || DEFAULT_POLL_INTERVAL_MS);
const HEKTOR_SESSION_REFRESH_MS = Number(process.env.CONSOLE_HEKTOR_SESSION_REFRESH_MS || 2 * 60 * 60 * 1000);
const ENABLE_HEKTOR_ACTIONS = String(process.env.CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS || "").toLowerCase() === "true";
const CREATE_HEKTOR_HTTP_DIRECT = String(process.env.CONSOLE_CREATE_HEKTOR_HTTP_DIRECT || "true").toLowerCase() !== "false";
const CREATE_HEKTOR_PLAYWRIGHT_FALLBACK = String(process.env.CONSOLE_CREATE_HEKTOR_PLAYWRIGHT_FALLBACK || "true").toLowerCase() !== "false";
const CLOUD_STATUSES = new Set(["Actif", "Sous offre", "Sous compromis", "Estimation"]);
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

function runNodeScript(scriptPath) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [scriptPath], {
      cwd: __dirname,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", reject);
    child.on("close", (code) => {
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

async function refreshHektorSession(reason = "scheduled") {
  if (hektorLoginPromise) return hektorLoginPromise;
  const loginScript = path.resolve(__dirname, "playwright_login.js");
  hektorLoginPromise = (async () => {
    console.log(JSON.stringify({ worker: WORKER_ID, step: "hektor_login", reason }));
    await runNodeScript(loginScript);
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

async function loadDossier(job) {
  if (job.app_dossier_id == null && !job.hektor_annonce_id) throw new Error("Job without dossier or annonce id");
  const params = new URLSearchParams({
    select: "app_dossier_id,hektor_annonce_id,archive,statut_annonce,agence_nom,commercial_id,commercial_nom,negociateur_email",
    limit: "1",
  });
  if (job.app_dossier_id != null) params.set("app_dossier_id", `eq.${job.app_dossier_id}`);
  else params.set("hektor_annonce_id", `eq.${job.hektor_annonce_id}`);
  const rows = await supabaseRequest(`app_dossier_current?${params.toString()}`, { method: "GET" });
  if (!Array.isArray(rows) || !rows.length) throw new Error(`Dossier introuvable: ${job.app_dossier_id || job.hektor_annonce_id}`);
  return rows[0];
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

async function resolveHektorExecutionUser(job, dossier, payload, options = {}) {
  const directId = payload.hektor_user_id || payload.hektor_id_user || payload.target_hektor_user_id;
  if (directId) {
    const directoryUser = await loadHektorDirectoryUserById(directId).catch(() => null);
    return {
      idUser: String(directId),
      label: (directoryUser && directoryUser.display_name) || payload.hektor_user_label || payload.negociateur_label || null,
      email: (directoryUser && directoryUser.email) || payload.hektor_user_email || null,
      source: "payload",
    };
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
    const directoryUser = await loadHektorDirectoryUserByEmail(normalized).catch(() => null);
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
    browser = await chromium.launch({ headless });
    const context = await browser.newContext({ storageState: STORAGE_STATE_PATH });
    const page = await context.newPage();
    await page.goto(`${ADMIN_URL}?call=authenticate&mode=autologin&idUser=${encodeURIComponent(targetId)}`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
    await page.goto(ADMIN_URL, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
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
        return String(payload.userId || "") === String(expectedId);
      } catch (_) {
        return false;
      }
    }, targetId, { timeout: 12000 }).then(() => true).catch(() => false);
    await context.storageState({ path: STORAGE_STATE_PATH });
    lastHektorLoginAt = Date.now();
    return confirmed;
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

async function hektorHtmlRequestWithJar(jar, url) {
  const response = await fetch(url, {
    redirect: "manual",
    headers: {
      Cookie: cookieHeaderFromJar(jar),
      Referer: ADMIN_URL,
      "User-Agent": "Mozilla/5.0 ConsoleWorker/1.0",
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    },
  });
  absorbSetCookieHeaders(jar, response.headers);
  const text = await response.text();
  if (response.status >= 500) throw new Error(`Hektor ${response.status} on context switch`);
  return {
    status: response.status,
    location: response.headers.get("location"),
    text,
  };
}

async function switchHektorUserContext(idUser) {
  const targetId = String(idUser || "").trim();
  if (!targetId) throw new Error("idUser Hektor requis pour changer de contexte");

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
}

async function returnHektorDefaultContext() {
  const state = readHektorStorageState();
  const jar = cookieJarFromStorageState(state);
  const htmlParts = [];

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

  if (!current) {
    await logJob(job.id, "hektor_context", "running", "Session Hektor illisible, reconnexion avant contexte negociateur", {
      target_id_user: target.idUser,
    });
    await refreshHektorSession("context_switch_missing_session");
    current = currentHektorSessionIdentity();
  }

  if (current && current.role && current.role !== "ADMIN") {
    await logJob(job.id, "hektor_context", "running", "Retour session admin avant changement de negociateur", {
      current_user_id: current.userId,
      current_role: current.role,
      target_id_user: target.idUser,
    });
    try {
      await returnHektorDefaultContext();
      current = currentHektorSessionIdentity();
    } catch (error) {
      await logJob(job.id, "hektor_context", "running", "Retour admin direct impossible, relance Playwright", {
        error: error && error.message ? error.message : String(error),
      });
    }
    if (!current || current.role !== "ADMIN") {
      await refreshHektorSession("context_switch_admin_login");
    }
    current = currentHektorSessionIdentity();
  }

  await logJob(job.id, "hektor_context", "running", "Changement de contexte Hektor negociateur", {
    current_user_id: current && current.userId ? current.userId : null,
    current_role: current && current.role ? current.role : null,
    target_id_user: target.idUser,
    target_label: target.label,
    source: target.source,
  });
  const switchConfirmed = await switchHektorUserContext(target.idUser);

  const after = currentHektorSessionIdentity();
  if (!after || after.userId !== String(target.idUser)) {
    if (String(process.env.CONSOLE_HEKTOR_ALLOW_UNVERIFIED_CONTEXT || "true").toLowerCase() !== "false") {
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
    throw new Error(`Changement de contexte Hektor non confirme pour idUser ${target.idUser}`);
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

async function hektorGraphQL(variables) {
  const authorization = hektorGraphQLAuthorizationHeader();
  const result = await hektorFetch(`${HEKTOR_BASE_URL.replace(/\/+$/, "")}/ws/GraphQL_Web`, {
    method: "POST",
    body: JSON.stringify({
      operationName: "PropertyListing",
      query: PROPERTY_LISTING_QUERY,
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

async function ensureAdminHektorSession(job, reason) {
  let current = currentHektorSessionIdentity();
  if (!current || current.role !== "ADMIN") {
    await logJob(job.id, "hektor_context", "running", "Retour session administrateur Hektor", {
      reason,
      current_user_id: current && current.userId ? current.userId : null,
      current_role: current && current.role ? current.role : null,
    });
    await refreshHektorSession(reason || "admin_required");
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

async function createHektorAnnonceWithPlaywright(job, payload) {
  const headless = String(process.env.CONSOLE_HEKTOR_HEADLESS || "true").toLowerCase() !== "false";
  let browser = null;
  try {
    browser = await chromium.launch({ headless });
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
  return {
    ...result,
    status: "synced",
    reason: payload.reason || null,
    parent_job_id: payload.parent_job_id || null,
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

  return {
    uploaded_filename: filename,
    visibility,
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    indexed: indexed.length,
    hektor_document_id: found.hektor_document_id,
    local_path: stored ? stored.local_path : null,
    storage_path: stored ? stored.storage_path : null,
  };
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

  return {
    deleted_document_id: document.id,
    deleted_name: document.document_name,
    hektor_uploaded_document_id: String(hektorUploadedDocumentId),
    hektor_annonce_id: String(dossier.hektor_annonce_id),
    indexed: entries.length,
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
    const fieldGroup = attrValue(field, "group");
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

function normalizeHektorAnnonceUpdatePayload(payload) {
  const fields = payload && payload.fields_json && typeof payload.fields_json === "object" ? payload.fields_json : payload.fields || payload;
  const clean = {};
  const textKeys = [
    "title",
    "description",
    "kitchen",
    "exposure",
    "view",
    "interior_state",
    "exterior_state",
    "dpe_value",
    "ges_value",
    "diagnostic_note",
    "mandate_number",
    "mandate_type",
    "mandate_start_date",
    "mandate_end_date",
  ];
  const numberKeys = [
    "price",
    "net_seller_price",
    "surface",
    "carrez_surface",
    "room_count",
    "bedroom_count",
    "bathroom_count",
    "shower_room_count",
    "wc_count",
    "land_surface",
    "garden_surface",
    "terrace_count",
    "garage_count",
    "parking_inside_count",
    "parking_outside_count",
    "pool",
    "construction_year",
    "copro_lots",
    "copro_charges",
    "copro_quote_part",
    "copro_works_fund",
    "fees",
  ];
  for (const key of textKeys) {
    if (fields[key] == null) continue;
    const value = String(fields[key]).trim();
    if (value) clean[key] = value;
  }
  for (const key of numberKeys) {
    if (fields[key] == null) continue;
    const value = String(fields[key]).replace(",", ".").trim();
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
  if (cleanFields.terrace_count != null) agExterieur.terrace_count = fieldSpec(cleanFields.terrace_count, ["TERRASSE"]);
  if (cleanFields.garage_count != null) agExterieur.garage_count = fieldSpec(cleanFields.garage_count, ["GARAGE_BOX"]);
  if (cleanFields.parking_inside_count != null) agExterieur.parking_inside_count = fieldSpec(cleanFields.parking_inside_count, ["NB_PARK_INT"]);
  if (cleanFields.parking_outside_count != null) agExterieur.parking_outside_count = fieldSpec(cleanFields.parking_outside_count, ["NB_PARK_EXT"]);
  if (cleanFields.pool != null) agExterieur.pool = fieldSpec(cleanFields.pool, ["PISCINE"]);
  await pushHektorGroupUpdate(results, job, annonceId, "ag_exterieur", "ihmChargeGroupe", agExterieur);

  const terrain = {};
  if (cleanFields.land_surface != null) terrain.land_surface = fieldSpec(cleanFields.land_surface, ["surfterrain"]);
  await pushHektorGroupUpdate(results, job, annonceId, "terrain", "ihmChargeGroupe", terrain);

  const diagnostics = {};
  if (cleanFields.dpe_value != null) diagnostics.dpe_value = fieldSpec(cleanFields.dpe_value, ["DPE", "dpe", "classe_energie"]);
  if (cleanFields.ges_value != null) diagnostics.ges_value = fieldSpec(cleanFields.ges_value, ["GES", "ges", "classe_ges"]);
  if (cleanFields.construction_year != null) diagnostics.construction_year = fieldSpec(cleanFields.construction_year, ["ANNEE_CONSTRUCTION", "annee_construction", "construction_year"]);
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

async function applyCreatedAnnonceInitialFields(job, annonceId, payload) {
  const fields = normalizeHektorAnnonceUpdatePayload(payload);
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

async function fetchHektorManualMandantForm() {
  const body = new URLSearchParams({
    mode: "contacts-actions-addManuelContactFromOtherObject",
    idNego: "",
    statut: "contact_seule",
    metier: "",
    inputId: "",
    qualification: "3",
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

async function handleDeleteHektorAnnonce(job) {
  const payload = safeJsonParse(job.payload_json);
  const hektorAnnonceId = String(job.hektor_annonce_id || payload.hektor_annonce_id || "").trim();
  const appDossierId = job.app_dossier_id == null ? payload.app_dossier_id : job.app_dossier_id;
  if (!hektorAnnonceId) throw new Error("hektor_annonce_id required");
  const expectedConfirm = `SUPPRIMER ${hektorAnnonceId}`;
  if (payload.confirm_text !== expectedConfirm) {
    throw new Error(`Confirmation suppression invalide pour annonce ${hektorAnnonceId}`);
  }

  await ensureAdminHektorSession(job, "delete_annonce_admin_login");
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
    initialFieldsUpdate = await applyCreatedAnnonceInitialFields(job, idannWizard, payload);
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

async function runHandler(job) {
  if (!ENABLE_HEKTOR_ACTIONS) {
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
    case "link_hektor_mandant":
      return handleLinkHektorMandant(job);
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
    case "create_hektor_draft_annonce":
      return handleCreateHektorDraftAnnonce(job);
    case "refresh_console_data":
      return handleRefreshConsoleData(job);
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
    const result = await runHandlerWithSessionRetry(job);
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
