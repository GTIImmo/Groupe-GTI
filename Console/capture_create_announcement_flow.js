const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const STORAGE_STATE_PATH = process.env.CONSOLE_STORAGE_STATE_PATH || path.resolve(__dirname, "storage_state.json");
const EXPORT_ROOT = path.resolve(__dirname, "exports", `capture_create_announcement_${new Date().toISOString().replace(/[:.]/g, "-")}`);
const STOP_FILE = path.join(EXPORT_ROOT, "STOP_CAPTURE.txt");
const MAX_DURATION_MS = Number(process.env.CAPTURE_CREATE_ANNOUNCEMENT_MAX_MS || 15 * 60 * 1000);

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
    || url.includes("/mes-biens/ajouter-un-nouveau-bien")
    || url.includes("labs_Bien_Wizard_New.js");
}

async function main() {
  ensureDir(EXPORT_ROOT);
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(`Session Hektor introuvable: ${STORAGE_STATE_PATH}`);
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
      bodyPreview: text.slice(0, 5000),
    });
  });

  console.log(JSON.stringify({
    status: "capture_started",
    exportRoot: EXPORT_ROOT,
    stopFile: STOP_FILE,
    maxDurationMs: MAX_DURATION_MS,
  }, null, 2));

  await page.goto(`${HEKTOR_BASE_URL.replace(/\/+$/, "")}/admin/?page=/mes-biens/ajouter-un-nouveau-bien`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });

  const startedAt = Date.now();
  while (!fs.existsSync(STOP_FILE) && Date.now() - startedAt < MAX_DURATION_MS) {
    await page.waitForTimeout(1000);
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
