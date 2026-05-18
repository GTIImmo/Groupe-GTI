const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "matterport", ".env") });

const STORAGE_STATE_PATH = process.env.MATTERPORT_STORAGE_STATE_PATH || path.resolve(__dirname, "matterport_storage_state.json");
const MODELS_URL = process.env.MATTERPORT_MODELS_URL || "https://my.matterport.com/models";
const DEFAULT_MODEL_ID = process.env.MATTERPORT_TEST_MODEL_ID || process.env.MATTERPORT_MODEL_ID || "";
const EXPORT_ROOT = path.resolve(__dirname, "exports", `matterport_inspect_${new Date().toISOString().replace(/[:.]/g, "-")}`);
const args = process.argv.slice(2);
const TARGET = args.find((arg) => !arg.startsWith("--")) || DEFAULT_MODEL_ID;
const HEADLESS = args.includes("--headless");

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function redactHeaders(headers) {
  const safe = {};
  for (const [key, value] of Object.entries(headers || {})) {
    if (/cookie|authorization|token|secret|password|x-matterport-session|csrf/i.test(key)) safe[key] = "[redacted]";
    else safe[key] = value;
  }
  return safe;
}

function redactText(value) {
  return String(value || "")
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [redacted]")
    .replace(/"access[_-]?token"\s*:\s*"[^"]+"/gi, '"access_token":"[redacted]"')
    .replace(/"id[_-]?token"\s*:\s*"[^"]+"/gi, '"id_token":"[redacted]"')
    .replace(/"refresh[_-]?token"\s*:\s*"[^"]+"/gi, '"refresh_token":"[redacted]"')
    .replace(/(clientSecret|client_secret|password)"?\s*[:=]\s*"?[^",}\s]+/gi, '$1:"[redacted]"');
}

function isInterestingUrl(url) {
  return /matterport\.com/i.test(url)
    && (
      /\/api\//i.test(url)
      || /graphql|graph/i.test(url)
      || /model|space|folder|asset|showcase/i.test(url)
      || /authn|oauth|token/i.test(url)
    );
}

function modelIdFromTarget(target) {
  if (!target) return "";
  try {
    const url = new URL(target);
    return url.searchParams.get("m") || url.pathname.split("/").filter(Boolean).pop() || target;
  } catch (_) {
    return target;
  }
}

async function snapshot(page, label) {
  await fs.promises.writeFile(path.join(EXPORT_ROOT, `${label}_url.txt`), page.url(), "utf-8");
  await fs.promises.writeFile(
    path.join(EXPORT_ROOT, `${label}_text.txt`),
    await page.locator("body").innerText({ timeout: 10000 }).catch(() => ""),
    "utf-8"
  );
  await page.screenshot({ path: path.join(EXPORT_ROOT, `${label}_screen.png`), fullPage: true }).catch(() => {});
}

async function clickLikelyModel(page, modelId, target) {
  const searchText = modelId || target;
  if (!searchText) return false;

  const searchInput = page.locator('input[type="search"], input[placeholder*="Search" i], input[placeholder*="recher" i]').first();
  if (await searchInput.isVisible({ timeout: 8000 }).catch(() => false)) {
    await searchInput.fill(searchText).catch(() => {});
    await page.keyboard.press("Enter").catch(() => {});
    await page.waitForTimeout(2500);
  }

  const candidates = [
    page.locator(`a[href*="${modelId}"]`).first(),
    page.locator(`text=${modelId}`).first(),
    page.locator(`text=${target}`).first(),
  ];

  for (const candidate of candidates) {
    if (await candidate.isVisible({ timeout: 3000 }).catch(() => false)) {
      await candidate.click({ timeout: 5000 }).catch(async () => {
        const handle = await candidate.elementHandle().catch(() => null);
        if (handle) await page.evaluate((el) => el.click(), handle).catch(() => {});
      });
      await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
      await page.waitForTimeout(1500);
      return true;
    }
  }
  return false;
}

async function main() {
  if (!TARGET) {
    throw new Error("Usage: node matterport_inspect_model.js <matterport_model_id_or_show_url>");
  }
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(`Session Matterport introuvable: ${STORAGE_STATE_PATH}. Lance d'abord node matterport_playwright_login.js`);
  }

  ensureDir(EXPORT_ROOT);
  const modelId = modelIdFromTarget(TARGET);
  const directModelUrl = `https://my.matterport.com/models/${modelId}`;
  const showUrl = `https://my.matterport.com/show/?m=${modelId}`;
  const events = [];

  const browser = await chromium.launch({ headless: HEADLESS, slowMo: HEADLESS ? 0 : 60 });
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
      postData: redactText(request.postData() || ""),
    });
  });

  page.on("response", async (response) => {
    const url = response.url();
    if (!isInterestingUrl(url)) return;
    const contentType = response.headers()["content-type"] || "";
    let body = "";
    if (/json|graphql|text/i.test(contentType)) {
      body = redactText((await response.text().catch(() => "")).slice(0, 6000));
    }
    events.push({
      at: new Date().toISOString(),
      event: "response",
      status: response.status(),
      url,
      headers: redactHeaders(response.headers()),
      body,
    });
  });

  console.log("Inspection Matterport:", modelId);
  console.log("Export:", EXPORT_ROOT);

  await page.goto(directModelUrl, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(async () => {
    await page.goto(MODELS_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
  });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await snapshot(page, "01_after_direct_model");

  const bodyText = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
  const probablyLogin = /sign in|login|connexion|password|mot de passe/i.test(bodyText) && /authn\.matterport\.com/i.test(page.url());
  if (probablyLogin) {
    await fs.promises.writeFile(path.join(EXPORT_ROOT, "SESSION_EXPIRED.txt"), "Session Matterport expiree. Relance matterport_playwright_login.js.\n", "utf-8");
    throw new Error("Session Matterport expiree. Relance matterport_playwright_login.js.");
  }

  if (!page.url().includes(modelId)) {
    await page.goto(MODELS_URL, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    await clickLikelyModel(page, modelId, TARGET);
    await snapshot(page, "02_after_search_click");
  }

  await page.goto(showUrl, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await snapshot(page, "03_showcase");

  await context.storageState({ path: STORAGE_STATE_PATH });
  await fs.promises.writeFile(path.join(EXPORT_ROOT, "network_events_redacted.json"), JSON.stringify(events, null, 2), "utf-8");
  await fs.promises.writeFile(path.join(EXPORT_ROOT, "summary.json"), JSON.stringify({
    modelId,
    directModelUrl,
    showUrl,
    finalUrl: page.url(),
    events: events.length,
    storageStatePath: STORAGE_STATE_PATH,
  }, null, 2), "utf-8");

  await browser.close();
  console.log("Inspection terminee.");
  console.log("Fichiers:", EXPORT_ROOT);
}

main().catch((error) => {
  console.error("Erreur inspection Matterport:", error.message);
  process.exit(1);
});
