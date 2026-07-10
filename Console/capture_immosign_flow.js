// =============================================================================
// ENREGISTREUR DE FLUX IMMOSIGN (capture réseau Hektor)
// -----------------------------------------------------------------------------
// But : capturer UNE FOIS, à la main, l'ouverture + l'envoi d'une procédure de
// signature électronique ImmoSign sur un document de test, pour isoler la
// requête finale d'envoi (le "code PIN manquant" — voir RAPPORT_IMMOSIGN_HEKTOR).
//
// Ce script N'AUTOMATISE RIEN : il ouvre Hektor connecté (session existante),
// puis ENREGISTRE tout le réseau pendant que TOI tu fais les clics.
//
// Utilisation :
//   node capture_immosign_flow.js 59624
//   (59624 = bien de TEST ; mets un autre id si besoin)
//
// Sécurité : bien de test uniquement, TOI comme signataire (ton mail + portable),
// annule la procédure et supprime le doc test juste après.
//
// Pour ARRÊTER : crée un fichier STOP_CAPTURE.txt dans le dossier export affiché,
// ou ferme la fenêtre (la capture est sauvegardée à chaque arrêt propre).
// =============================================================================

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "storage_state.json");
const args = process.argv.slice(2);
const ANNONCE_ID = args.find((arg) => !arg.startsWith("--")) || process.env.CAPTURE_IMMOSIGN_ANNONCE_ID;
const EXPORT_ROOT = path.resolve(
  __dirname,
  "exports",
  `capture_immosign_${ANNONCE_ID || "unknown"}_${new Date().toISOString().replace(/[:.]/g, "-")}`
);
const STOP_FILE = path.join(EXPORT_ROOT, "STOP_CAPTURE.txt");
const MAX_DURATION_MS = Number(process.env.CAPTURE_IMMOSIGN_MAX_MS || 20 * 60 * 1000); // 20 min

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function redactHeaders(headers, url) {
  // On garde les en-têtes d'AUTH uniquement vers le SaaS de signature (immo-sign/mylegitech),
  // car le full-auto HTTP a besoin du Bearer token. Cookies/secret Hektor restent masqués.
  const isSaaS = /immo-sign\.com|mylegitech\.com/i.test(url || "");
  const safe = {};
  for (const [key, value] of Object.entries(headers || {})) {
    const k = key.toLowerCase();
    if (/cookie|secret|password/.test(k)) { safe[key] = "[redacted]"; continue; }
    if ((k === "authorization" || k.includes("token") || k.includes("api-key")) && !isSaaS) { safe[key] = "[redacted]"; continue; }
    safe[key] = value;
  }
  return safe;
}

// On capte large : tout xmlrpc, tout ce qui contient "immosign"/"signature", et l'upload de doc.
function isInterestingUrl(url) {
  const u = url.toLowerCase();
  return u.includes("/admin/xmlrpc.php")
    || u.includes("immosign")
    || u.includes("signature")
    || u.includes("/admin/upload")
    || u.includes("upload_uploadeddoc")
    || u.includes("chargeannonce")
    // bascule en acces negociateur (impersonation) : on capte aussi le passage
    || u.includes("call=authenticate")
    || u.includes("autologin")
    || u.includes("impersonate");
}

// Une requête est "ImmoSign" si l'URL ou le corps mentionne ImmoSign / une procédure.
function isImmoSignEvent(ev) {
  const hay = `${ev.url} ${ev.postData || ""}`.toLowerCase();
  return hay.includes("immosign") || hay.includes("procedure") || hay.includes("signat");
}

async function snapshot(page, label) {
  await fs.promises.writeFile(path.join(EXPORT_ROOT, `${label}_url.txt`), page.url(), "utf-8").catch(() => {});
  await fs.promises.writeFile(
    path.join(EXPORT_ROOT, `${label}_text.txt`),
    await page.locator("body").innerText().catch(() => ""),
    "utf-8"
  ).catch(() => {});
  await page.screenshot({ path: path.join(EXPORT_ROOT, `${label}_screen.png`), fullPage: true }).catch(() => {});
}

async function main() {
  if (!ANNONCE_ID) {
    throw new Error("Usage: node capture_immosign_flow.js <hektor_annonce_id_de_test>");
  }
  ensureDir(EXPORT_ROOT);
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(
      `Session Hektor introuvable: ${STORAGE_STATE_PATH}\n` +
      `Lance d'abord la connexion (ex: node playwright_login.js) pour générer storage_state.json.`
    );
  }

  const events = [];
  const browser = await chromium.launch({ headless: false, slowMo: 60, args: ["--start-maximized"] });
  const context = await browser.newContext({
    storageState: STORAGE_STATE_PATH,
    viewport: null,  // suit la taille reelle de la fenetre (maximisee) -> scroll + boutons a droite visibles
  });
  const page = await context.newPage();

  page.on("request", (request) => {
    const url = request.url();
    if (!isInterestingUrl(url)) return;
    events.push({
      at: new Date().toISOString(),
      event: "request",
      method: request.method(),
      url,
      headers: redactHeaders(request.headers(), url),
      postData: request.postData(),
    });
  });

  page.on("response", async (response) => {
    const request = response.request();
    const url = response.url();
    if (!isInterestingUrl(url)) return;
    let text = "";
    try {
      const contentType = response.headers()["content-type"] || "";
      if (/json|text|html|javascript|x-www-form-urlencoded/i.test(contentType)) {
        text = await response.text();
      }
    } catch (_) {
      text = "[response body unavailable]";
    }
    events.push({
      at: new Date().toISOString(),
      event: "response",
      method: request.method(),
      url,
      status: response.status(),
      headers: redactHeaders(response.headers(), url),
      bodyPreview: text.slice(0, 12000),
    });
  });

  const base = HEKTOR_BASE_URL.replace(/\/+$/, "");
  const targetUrl = `${base}/admin/?page=/mes-biens/mon-bien&id=${encodeURIComponent(ANNONCE_ID)}`;

  console.log(JSON.stringify({
    status: "capture_started",
    annonceId: ANNONCE_ID,
    targetUrl,
    exportRoot: EXPORT_ROOT,
    stopFile: STOP_FILE,
    maxDurationMs: MAX_DURATION_MS,
    instructions: [
      "PRE-REQUIS : un document de test doit deja etre present dans Hektor sur ce bien",
      "  (pousse-le via l'app -> upload_document_to_hektor, ou reutilise un doc deja la).",
      "1. Va sur l'onglet Documents du bien.",
      "2. Clique le picto signature (empreinte) sur ce document de test.",
      "3. Mets TOI comme signataire (ton email + ton portable).",
      "4. VALIDE l'envoi (c'est le clic important).",
      "5. Cree le fichier STOP_CAPTURE.txt dans le dossier export pour arreter.",
      "6. ENSUITE : annule la procedure dans Hektor + supprime le doc test.",
    ],
  }, null, 2));

  await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await snapshot(page, "initial");

  const startedAt = Date.now();
  while (!fs.existsSync(STOP_FILE) && Date.now() - startedAt < MAX_DURATION_MS) {
    // Sauvegarde incrémentale toutes les ~5 s (au cas où la fenêtre est fermée brutalement)
    await page.waitForTimeout(5000).catch(() => {});
    try {
      fs.writeFileSync(path.join(EXPORT_ROOT, "network_events.json"), JSON.stringify(events, null, 2), "utf-8");
    } catch (_) { /* best effort */ }
    if (page.isClosed()) break;
  }

  // Sauvegarde finale
  await fs.promises.writeFile(path.join(EXPORT_ROOT, "network_events.json"), JSON.stringify(events, null, 2), "utf-8");

  // Fichier filtré : uniquement les requêtes ImmoSign/signature/procédure (le coeur de l'étude)
  const immosignOnly = events.filter((ev) => ev.event === "request" && isImmoSignEvent(ev));
  await fs.promises.writeFile(
    path.join(EXPORT_ROOT, "immosign_requests.json"),
    JSON.stringify(immosignOnly, null, 2),
    "utf-8"
  );

  await snapshot(page, "final").catch(() => {});
  // NB: on NE réécrit PAS storageState ici — pour ne pas laisser la session en
  // contexte negociateur impersonné après la capture (lecture seule de la session).
  await browser.close().catch(() => {});

  console.log(JSON.stringify({
    status: "capture_saved",
    exportRoot: EXPORT_ROOT,
    totalEvents: events.length,
    immosignRequests: immosignOnly.length,
    next: "Donne-moi le dossier export (surtout immosign_requests.json) pour analyse.",
  }, null, 2));
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
