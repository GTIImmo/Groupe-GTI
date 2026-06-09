const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN_URL = `${HEKTOR_BASE_URL}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;

function argValues(name) {
  const values = [];
  for (let index = 0; index < process.argv.length; index += 1) {
    if (process.argv[index] === name && index + 1 < process.argv.length) {
      values.push(String(process.argv[index + 1] || "").trim());
    }
  }
  return values.filter(Boolean);
}

function argValue(name, fallback = "") {
  const values = argValues(name);
  return values.length ? values[values.length - 1] : fallback;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms)));
}

function browserLaunchOptions(options = {}) {
  const executablePath = [
    process.env.CONSOLE_CHROME_EXE,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].find((candidate) => candidate && fs.existsSync(candidate)) || "";
  return {
    headless: true,
    ...options,
    ...(executablePath ? { executablePath } : {}),
  };
}

function uniqueAnnonceIds() {
  const values = [
    ...argValues("--annonce-id"),
    ...argValues("--annonce-ids").flatMap((value) => value.split(",")),
  ];
  return Array.from(new Set(values.map((value) => String(value || "").trim()).filter((value) => /^\d+$/.test(value))));
}

function decodeMaybeJsonHtml(text) {
  const raw = String(text || "");
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed === "string") return parsed;
    if (parsed && typeof parsed === "object" && typeof parsed.content === "string") return parsed.content;
  } catch (_) {
    // Hektor can return raw HTML or JSON encoded HTML.
  }
  return raw;
}

function looksLikeLoginPage(text) {
  const html = String(text || "").toLowerCase();
  return (
    html.includes("name=\"login\"")
    || html.includes("name='login'")
    || html.includes("mot de passe")
    || html.includes("connexion")
    || html.includes("/admin/login")
  );
}

function cleanText(value) {
  return String(value == null ? "" : value).replace(/\s+/g, " ").trim();
}

async function extractChauffages(page, html) {
  return page.evaluate(({ html }) => {
    const clean = (value) => String(value == null ? "" : value).replace(/\s+/g, " ").trim();
    const doc = new DOMParser().parseFromString(html || "", "text/html");
    return Array.from(doc.querySelectorAll('table[id^="chauffageExist"]')).map((table) => {
      const id = (table.getAttribute("id") || "").replace(/^chauffageExist/, "");
      const item = { id, format: null, type: null, energie: null };
      for (const select of Array.from(table.querySelectorAll("select"))) {
        const onchange = select.getAttribute("onchange") || "";
        const match = onchange.match(/updateValueChauffage\(["']\d+["']\s*,\s*["'](format|type|energie)["']\s*,\s*this\.value\)/i);
        if (!match) continue;
        const selected = Array.from(select.options || []).find((option) => option.selected) || null;
        item[match[1]] = {
          value: select.value || "",
          label: selected ? clean(selected.textContent) : "",
        };
      }
      return item;
    });
  }, { html });
}

async function fetchEquipementsHtml(page, annonceId) {
  const params = new URLSearchParams({
    mode: "ihmChargeGroupe",
    ajax: "ajax",
    idAnnonce: annonceId,
    group: "equipements",
    consultMode: "editer",
  });
  const url = `${XMLRPC_URL}?${params.toString()}`;
  const referer = `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`;
  return page.evaluate(async ({ url, referer }) => {
    const response = await fetch(url, {
      credentials: "include",
      headers: {
        Accept: "application/json, text/javascript, text/html, */*; q=0.01",
        Referer: referer,
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    return {
      status: response.status,
      url: response.url,
      text: await response.text(),
    };
  }, { url, referer });
}

async function extractOne(page, annonceId) {
  const started = Date.now();
  const fetched = await fetchEquipementsHtml(page, annonceId);
  const html = decodeMaybeJsonHtml(fetched.text);
  const base = {
    hektor_annonce_id: annonceId,
    http_status: fetched.status,
    html_bytes: html.length,
    elapsed_ms: Date.now() - started,
    extracted_at: new Date().toISOString(),
  };
  if (fetched.status === 403) {
    return { ...base, status: "stopped_on_403", error: "Hektor 403 sur le groupe equipements" };
  }
  if (fetched.status >= 400) {
    return { ...base, status: "error", error: `HTTP ${fetched.status} sur le groupe equipements` };
  }
  if (looksLikeLoginPage(html)) {
    return { ...base, status: "session_expired", error: "Session Hektor expiree ou page login retournee" };
  }
  const chauffages = await extractChauffages(page, html);
  return {
    ...base,
    status: "done",
    chauffage_console_json: chauffages,
    chauffage_count: chauffages.length,
  };
}

async function main() {
  const annonceIds = uniqueAnnonceIds();
  const storageStatePath = path.resolve(argValue(
    "--storage-state",
    process.env.CONSOLE_INSPECT_STORAGE_STATE_PATH || path.join(__dirname, "sessions", "storage_state_admin.json"),
  ));
  const delayMs = Number(argValue("--delay-ms", "0")) || 0;
  const timeoutMs = Number(argValue("--timeout-ms", "60000")) || 60000;
  if (!annonceIds.length) {
    throw new Error("Aucun --annonce-id fourni");
  }
  if (!fs.existsSync(storageStatePath)) {
    throw new Error(`Session Playwright introuvable: ${storageStatePath}`);
  }

  const started = Date.now();
  const browser = await chromium.launch(browserLaunchOptions());
  const context = await browser.newContext({ storageState: storageStatePath });
  const page = await context.newPage();
  page.setDefaultTimeout(timeoutMs);

  const results = [];
  try {
    await page.goto(ADMIN_URL, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    for (let index = 0; index < annonceIds.length; index += 1) {
      const result = await extractOne(page, annonceIds[index]);
      results.push(result);
      if (result.status === "stopped_on_403") {
        const summary = {
          status: "stopped_on_403",
          storage_state: storageStatePath,
          results,
          elapsed_ms: Date.now() - started,
        };
        console.log(JSON.stringify(summary));
        process.exitCode = 3;
        return;
      }
      if (result.status === "session_expired") {
        const summary = {
          status: "session_expired",
          storage_state: storageStatePath,
          results,
          elapsed_ms: Date.now() - started,
        };
        console.log(JSON.stringify(summary));
        process.exitCode = 2;
        return;
      }
      if (index < annonceIds.length - 1 && delayMs > 0) {
        await sleep(delayMs);
      }
    }
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({
    status: results.some((item) => item.status === "error") ? "partial" : "done",
    storage_state: storageStatePath,
    results,
    elapsed_ms: Date.now() - started,
  }));
}

main().catch((error) => {
  console.log(JSON.stringify({
    status: "error",
    error: error && error.message ? error.message : String(error),
    extracted_at: new Date().toISOString(),
  }));
  process.exitCode = 1;
});
