const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

// Capture du parcours "recherche d'un contact" dans la console Hektor.
// Modele : capture_create_announcement_flow.js
//
// But : enregistrer les appels reseau (xmlrpc.php / GraphQL) pendant que
// l'utilisateur effectue manuellement, sur un contact existant :
//   1. ouverture de la page "ajouter une recherche"
//   2. AJOUT d'une recherche (criteres + validation)
//   3. MODIFICATION de la recherche creee
//   4. SUPPRESSION de la recherche
//   5. (lecture) rechargement de la fiche pour voir la liste des recherches
//
// Astuce : pour annoter le parcours, cree/edite le fichier STEP_MARKER.txt
// dans le dossier d'export (ex: ecris "AJOUT", puis "MODIF", etc.). Sa valeur
// est attachee a chaque evenement capture pour faciliter le tri ensuite.

const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "storage_state.json");
const CONTACT_ID = process.env.CAPTURE_CONTACT_ID || process.argv[2] || "604009";
const EXPORT_ROOT = path.resolve(__dirname, "exports", `capture_contact_search_${new Date().toISOString().replace(/[:.]/g, "-")}`);
const STOP_FILE = path.join(EXPORT_ROOT, "STOP_CAPTURE.txt");
const STEP_MARKER_FILE = path.join(EXPORT_ROOT, "STEP_MARKER.txt");
const MAX_DURATION_MS = Number(process.env.CAPTURE_CONTACT_SEARCH_MAX_MS || 20 * 60 * 1000);

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function redactHeaders(headers) {
  const safe = {};
  for (const [key, value] of Object.entries(headers || {})) {
    if (/cookie|authorization|token|secret|password/i.test(key)) safe[key] = "[redacted]";
    else safe[key] = value;
  }
  return safe;
}

function currentStep() {
  try {
    return fs.readFileSync(STEP_MARKER_FILE, "utf-8").trim();
  } catch (_) {
    return "";
  }
}

// On capture large : tout xmlrpc.php et GraphQL, plus la page recherche et ses JS.
function isInterestingUrl(url) {
  return url.includes("/admin/xmlrpc.php")
    || url.includes("/ws/GraphQL_Web")
    || url.includes("call=ac_villes")
    || url.includes("recherche")
    || url.includes("Critere")
    || url.includes("critere")
    || url.includes("Prospect")
    || url.includes("mon-contact");
}

async function main() {
  ensureDir(EXPORT_ROOT);
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(`Session Hektor introuvable: ${STORAGE_STATE_PATH}`);
  }
  // Initialise le marqueur d'etape pour que l'utilisateur puisse l'editer.
  if (!fs.existsSync(STEP_MARKER_FILE)) {
    fs.writeFileSync(STEP_MARKER_FILE, "OUVERTURE", "utf-8");
  }

  const events = [];
  const browser = await chromium.launch({ headless: false, slowMo: 80 });
  const context = await browser.newContext({
    storageState: STORAGE_STATE_PATH,
    viewport: { width: 1400, height: 920 },
  });
  const page = await context.newPage();

  page.on("request", (request) => {
    const url = request.url();
    if (!isInterestingUrl(url)) return;
    events.push({
      at: new Date().toISOString(),
      step: currentStep(),
      event: "request",
      method: request.method(),
      url,
      headers: redactHeaders(request.headers()),
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
      step: currentStep(),
      event: "response",
      method: request.method(),
      url,
      status: response.status(),
      headers: redactHeaders(response.headers()),
      bodyPreview: text.slice(0, 8000),
    });
  });

  console.log(JSON.stringify({
    status: "capture_started",
    contactId: CONTACT_ID,
    exportRoot: EXPORT_ROOT,
    stopFile: STOP_FILE,
    stepMarkerFile: STEP_MARKER_FILE,
    maxDurationMs: MAX_DURATION_MS,
  }, null, 2));

  const targetUrl = `${HEKTOR_BASE_URL.replace(/\/+$/, "")}/admin/?page=/mes-contacts/mon-contact/recherche/ajouter-une-recherche&id=${encodeURIComponent(CONTACT_ID)}`;
  await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 60000 });

  const startedAt = Date.now();
  let lastFlush = 0;
  while (!fs.existsSync(STOP_FILE) && Date.now() - startedAt < MAX_DURATION_MS) {
    await page.waitForTimeout(1000);
    // Flush incremental toutes les ~10s pour ne rien perdre si la fenetre est fermee.
    if (Date.now() - lastFlush > 10000) {
      lastFlush = Date.now();
      await fs.promises.writeFile(
        path.join(EXPORT_ROOT, "network_events.json"),
        JSON.stringify(events, null, 2),
        "utf-8"
      ).catch(() => {});
    }
  }

  await context.storageState({ path: STORAGE_STATE_PATH });
  await fs.promises.writeFile(path.join(EXPORT_ROOT, "network_events.json"), JSON.stringify(events, null, 2), "utf-8");
  await fs.promises.writeFile(path.join(EXPORT_ROOT, "current_url.txt"), page.url(), "utf-8");
  await fs.promises.writeFile(path.join(EXPORT_ROOT, "page_text.txt"), await page.locator("body").innerText().catch(() => ""), "utf-8");
  await page.screenshot({ path: path.join(EXPORT_ROOT, "final_screen.png"), fullPage: true }).catch(() => {});
  await browser.close();

  console.log(JSON.stringify({
    status: "capture_saved",
    exportRoot: EXPORT_ROOT,
    events: events.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
