const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

// Extraction AUTONOME (lecture seule) du parcours "recherche d'un contact".
// On ouvre la page "ajouter une recherche" avec la session enregistree, on
// enregistre tous les appels reseau declenches au chargement, on telecharge le
// HTML + les fichiers JS du wizard de recherche, et on extrait les `mode=...`
// et fonctions cles. Aucune soumission (pas de mutation en prod).

const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "storage_state.json");
const CONTACT_ID = process.env.CAPTURE_CONTACT_ID || process.argv[2] || "604009";
const EXPORT_ROOT = path.resolve(__dirname, "exports", `extract_contact_search_${new Date().toISOString().replace(/[:.]/g, "-")}`);

function ensureDir(dir) { fs.mkdirSync(dir, { recursive: true }); }

function redactHeaders(headers) {
  const safe = {};
  for (const [key, value] of Object.entries(headers || {})) {
    if (/cookie|authorization|token|secret|password/i.test(key)) safe[key] = "[redacted]";
    else safe[key] = value;
  }
  return safe;
}

function isInterestingNetwork(url) {
  return url.includes("/admin/xmlrpc.php")
    || url.includes("/ws/GraphQL_Web")
    || url.includes("call=ac_villes")
    || /critere|recherche|prospect/i.test(url);
}

function isSearchJs(url) {
  return /\.js(\?|$)/i.test(url) && /critere|recherche|prospect|contact|wizard|labs/i.test(url);
}

// Extrait toutes les occurrences "mode=xxx" et 'mode':'xxx' / mode:"xxx" d'un texte.
function extractModes(text) {
  const modes = new Set();
  const patterns = [
    /mode=([a-zA-Z0-9_\-]+)/g,
    /["']mode["']\s*:\s*["']([a-zA-Z0-9_\-]+)["']/g,
    /mode\s*:\s*["']([a-zA-Z0-9_\-]+)["']/g,
  ];
  for (const re of patterns) {
    let m;
    while ((m = re.exec(text)) !== null) modes.add(m[1]);
  }
  return Array.from(modes).sort();
}

function extractStateValues(text) {
  const states = new Set();
  const re = /["']?state["']?\s*[:=]\s*["']([a-zA-Z0-9_\-]+)["']/g;
  let m;
  while ((m = re.exec(text)) !== null) states.add(m[1]);
  return Array.from(states).sort();
}

async function main() {
  ensureDir(EXPORT_ROOT);
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(`Session Hektor introuvable: ${STORAGE_STATE_PATH}`);
  }

  const events = [];
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: STORAGE_STATE_PATH,
    viewport: { width: 1400, height: 920 },
  });
  const page = await context.newPage();

  page.on("request", (request) => {
    const url = request.url();
    if (!isInterestingNetwork(url)) return;
    events.push({
      at: new Date().toISOString(), event: "request", method: request.method(),
      url, headers: redactHeaders(request.headers()), postData: request.postData(),
    });
  });
  page.on("response", async (response) => {
    const url = response.url();
    if (!isInterestingNetwork(url)) return;
    let text = "";
    try {
      const ct = response.headers()["content-type"] || "";
      if (/json|text|html|javascript|x-www-form-urlencoded/i.test(ct)) text = await response.text();
    } catch (_) { text = "[unavailable]"; }
    events.push({
      at: new Date().toISOString(), event: "response", method: response.request().method(),
      url, status: response.status(), bodyPreview: text.slice(0, 12000),
    });
  });

  const targetUrl = `${HEKTOR_BASE_URL.replace(/\/+$/, "")}/admin/?page=/mes-contacts/mon-contact/recherche/ajouter-une-recherche&id=${encodeURIComponent(CONTACT_ID)}`;
  const resp = await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(3000);

  const finalUrl = page.url();
  const html = await page.content();
  const bodyText = await page.locator("body").innerText().catch(() => "");
  const loginDetected = /connexion|se connecter|mot de passe|identifiant/i.test(bodyText) && !/recherche/i.test(bodyText);

  // Liste des <script src> et <form> presents dans le DOM.
  const scriptSrcs = await page.$$eval("script[src]", (els) => els.map((e) => e.getAttribute("src")));
  const forms = await page.$$eval("form", (els) => els.map((f) => ({
    id: f.getAttribute("id") || null,
    name: f.getAttribute("name") || null,
    action: f.getAttribute("action") || null,
    method: f.getAttribute("method") || null,
    fields: Array.from(f.querySelectorAll("input,select,textarea")).map((i) => ({
      tag: i.tagName.toLowerCase(),
      name: i.getAttribute("name") || null,
      type: i.getAttribute("type") || null,
      value: i.tagName.toLowerCase() === "select" ? null : (i.getAttribute("value") || null),
    })),
  })));

  // Telecharge les JS susceptibles de contenir la logique recherche/critere.
  const jsDir = path.join(EXPORT_ROOT, "js");
  ensureDir(jsDir);
  const downloadedJs = [];
  const baseOrigin = new URL(HEKTOR_BASE_URL).origin;
  const seen = new Set();
  for (const rawSrc of scriptSrcs) {
    if (!rawSrc) continue;
    let abs;
    try { abs = new URL(rawSrc, finalUrl).toString(); } catch (_) { continue; }
    if (seen.has(abs)) continue;
    seen.add(abs);
    if (!isSearchJs(abs)) continue;
    try {
      const r = await context.request.get(abs);
      const body = await r.text();
      const fname = abs.split("/").pop().split("?")[0].replace(/[^a-zA-Z0-9_.\-]/g, "_");
      fs.writeFileSync(path.join(jsDir, fname), body, "utf-8");
      downloadedJs.push({ url: abs, file: `js/${fname}`, bytes: body.length, modes: extractModes(body), states: extractStateValues(body) });
    } catch (e) {
      downloadedJs.push({ url: abs, error: e && e.message ? e.message : String(e) });
    }
  }

  // Agrege les modes/states trouves dans le HTML, le texte des reponses reseau et les JS.
  const allText = [html, ...events.map((e) => e.bodyPreview || "" ), ...events.map((e) => e.postData || "")].join("\n");
  const summary = {
    contactId: CONTACT_ID,
    targetUrl,
    finalUrl,
    httpStatus: resp ? resp.status() : null,
    loginDetected,
    networkEventCount: events.length,
    scriptSrcCount: scriptSrcs.length,
    downloadedJsCount: downloadedJs.length,
    modesInHtmlAndNetwork: extractModes(allText),
    statesInHtmlAndNetwork: extractStateValues(allText),
    modesInJs: Array.from(new Set(downloadedJs.flatMap((j) => j.modes || []))).sort(),
    statesInJs: Array.from(new Set(downloadedJs.flatMap((j) => j.states || []))).sort(),
    forms,
    downloadedJs: downloadedJs.map((j) => ({ url: j.url, file: j.file, bytes: j.bytes, error: j.error })),
  };

  fs.writeFileSync(path.join(EXPORT_ROOT, "page.html"), html, "utf-8");
  fs.writeFileSync(path.join(EXPORT_ROOT, "page_text.txt"), bodyText, "utf-8");
  fs.writeFileSync(path.join(EXPORT_ROOT, "network_events.json"), JSON.stringify(events, null, 2), "utf-8");
  fs.writeFileSync(path.join(EXPORT_ROOT, "summary.json"), JSON.stringify(summary, null, 2), "utf-8");
  await page.screenshot({ path: path.join(EXPORT_ROOT, "page.png"), fullPage: true }).catch(() => {});

  await context.storageState({ path: STORAGE_STATE_PATH });
  await browser.close();

  console.log(JSON.stringify({ status: "extract_done", exportRoot: EXPORT_ROOT, ...summary, forms: `${forms.length} forms`, downloadedJs: summary.downloadedJsCount }, null, 2));
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
