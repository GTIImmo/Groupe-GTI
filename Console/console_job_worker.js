const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { spawn } = require("child_process");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${HEKTOR_BASE_URL.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const STORAGE_BUCKET = process.env.CONSOLE_STORAGE_BUCKET || "hektor-console-documents";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "storage_state.json");
const LOCAL_ARCHIVE_ROOT = process.env.CONSOLE_LOCAL_ARCHIVE_ROOT || "C:\\HektorConsoleDocuments";
const WORKER_ID = process.env.CONSOLE_WORKER_ID || `${os.hostname()}:${process.pid}`;
const POLL_INTERVAL_MS = Number(process.env.CONSOLE_WORKER_POLL_INTERVAL_MS || 60000);
const HEKTOR_SESSION_REFRESH_MS = Number(process.env.CONSOLE_HEKTOR_SESSION_REFRESH_MS || 2 * 60 * 60 * 1000);
const ENABLE_HEKTOR_ACTIONS = String(process.env.CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS || "").toLowerCase() === "true";
const CLOUD_STATUSES = new Set(["Actif", "Sous offre", "Sous compromis", "Estimation"]);

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
  return message.includes("Hektor 403") || message.includes("Session Hektor expiree");
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

async function claimNextJob() {
  const rows = await supabaseRequest("rpc/app_console_claim_next_job", {
    method: "POST",
    body: JSON.stringify({ p_worker_id: WORKER_ID }),
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

async function loadDossier(job) {
  if (job.app_dossier_id == null && !job.hektor_annonce_id) throw new Error("Job without dossier or annonce id");
  const params = new URLSearchParams({
    select: "app_dossier_id,hektor_annonce_id,archive,statut_annonce,agence_nom",
    limit: "1",
  });
  if (job.app_dossier_id != null) params.set("app_dossier_id", `eq.${job.app_dossier_id}`);
  else params.set("hektor_annonce_id", `eq.${job.hektor_annonce_id}`);
  const rows = await supabaseRequest(`app_dossier_current?${params.toString()}`, { method: "GET" });
  if (!Array.isArray(rows) || !rows.length) throw new Error(`Dossier introuvable: ${job.app_dossier_id || job.hektor_annonce_id}`);
  return rows[0];
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

async function hektorFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
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

async function runHandler(job) {
  if (!ENABLE_HEKTOR_ACTIONS) {
    throw new Error("Console worker protected: set CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS=true to execute Hektor actions.");
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
    case "refresh_console_data":
      return handleSyncConsoleDocuments(job);
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
    enableHektorActions: ENABLE_HEKTOR_ACTIONS,
    mode: once ? "once" : "permanent",
  }));

  if (once) {
    await processOnce();
    return;
  }

  while (true) {
    try {
      const processed = await processOnce();
      if (!processed) await sleep(POLL_INTERVAL_MS);
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
