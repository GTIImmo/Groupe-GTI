const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "storage_state.json");
const args = process.argv.slice(2);
const ANNONCE_ID = args.find((arg) => !arg.startsWith("--")) || process.env.CAPTURE_UPDATE_ANNONCE_ID;
const HEKTOR_USER_ID = (args.find((arg) => arg.startsWith("--hektor-user-id=")) || "").split("=")[1]
  || process.env.CAPTURE_HEKTOR_USER_ID
  || null;
const EXPORT_ROOT = path.resolve(
  __dirname,
  "exports",
  `capture_update_announcement_${ANNONCE_ID || "unknown"}_${new Date().toISOString().replace(/[:.]/g, "-")}`
);
const STOP_FILE = path.join(EXPORT_ROOT, "STOP_CAPTURE.txt");
const MAX_DURATION_MS = Number(process.env.CAPTURE_UPDATE_ANNOUNCEMENT_MAX_MS || 12 * 60 * 1000);

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

function isInterestingUrl(url) {
  return url.includes("/admin/xmlrpc.php")
    || url.includes("/ws/GraphQL_Web")
    || url.includes("/admin/upload")
    || url.includes("/admin/?page=/mes-biens/mon-bien")
    || url.includes("/mes-biens/mon-bien")
    || url.includes("chargeannonce")
    || url.includes("labs_Bien")
    || url.includes("labs_Annonce")
    || url.includes("labs_Contact");
}

async function snapshot(page, label) {
  await fs.promises.writeFile(path.join(EXPORT_ROOT, `${label}_url.txt`), page.url(), "utf-8");
  await fs.promises.writeFile(
    path.join(EXPORT_ROOT, `${label}_text.txt`),
    await page.locator("body").innerText().catch(() => ""),
    "utf-8"
  );
  await page.screenshot({ path: path.join(EXPORT_ROOT, `${label}_screen.png`), fullPage: true }).catch(() => {});
}

async function main() {
  if (!ANNONCE_ID) {
    throw new Error("Usage: node capture_update_announcement_flow.js <hektor_annonce_id>");
  }
  ensureDir(EXPORT_ROOT);
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(`Session Hektor introuvable: ${STORAGE_STATE_PATH}`);
  }

  const events = [];
  const browser = await chromium.launch({ headless: false, slowMo: 70 });
  const context = await browser.newContext({
    storageState: STORAGE_STATE_PATH,
    viewport: { width: 1440, height: 950 },
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
      event: "response",
      method: request.method(),
      url,
      status: response.status(),
      headers: redactHeaders(response.headers()),
      bodyPreview: text.slice(0, 12000),
    });
  });

  const base = HEKTOR_BASE_URL.replace(/\/+$/, "");
  const targetUrl = `${base}/admin/?page=/mes-biens/mon-bien&id=${encodeURIComponent(ANNONCE_ID)}`;
  console.log(JSON.stringify({
    status: "capture_started",
    annonceId: ANNONCE_ID,
    hektorUserId: HEKTOR_USER_ID,
    targetUrl,
    exportRoot: EXPORT_ROOT,
    stopFile: STOP_FILE,
    maxDurationMs: MAX_DURATION_MS,
    instruction: "Modifier seulement l'annonce test, puis creer STOP_CAPTURE.txt dans le dossier export pour arreter.",
  }, null, 2));

  if (HEKTOR_USER_ID) {
    await page.goto(`${base}/admin/?call=authenticate&mode=autologin&idUser=${encodeURIComponent(HEKTOR_USER_ID)}`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
    await context.storageState({ path: STORAGE_STATE_PATH });
  }

  await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await snapshot(page, "initial");

  const startedAt = Date.now();
  while (!fs.existsSync(STOP_FILE) && Date.now() - startedAt < MAX_DURATION_MS) {
    await page.waitForTimeout(1000);
  }

  await context.storageState({ path: STORAGE_STATE_PATH });
  await fs.promises.writeFile(path.join(EXPORT_ROOT, "network_events.json"), JSON.stringify(events, null, 2), "utf-8");
  await snapshot(page, "final");
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
