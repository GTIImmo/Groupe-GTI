// Scraper Console contact : récupère naissance/lieu/matrimonial du formulaire Hektor
// (l'API ContactById ne les renvoie pas). Calqué sur extract_hektor_chauffage_only.js :
// même session (storage_state), même gestion 403 / session expirée. LECTURE SEULE.
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

function uniqueContactIds() {
  const values = [
    ...argValues("--contact-id"),
    ...argValues("--contact-ids").flatMap((value) => value.split(",")),
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
    // Hektor peut renvoyer du HTML brut ou du HTML encodé en JSON.
  }
  return raw;
}

function looksLikeLoginPage(text) {
  const html = String(text || "").toLowerCase();
  return (
    html.includes("name=\"login\"")
    || html.includes("name='login'")
    || html.includes("mot de passe")
    || html.includes("/admin/login")
  );
}

// Hektor : dateNaissance en JJ-MM-AAAA (ou 00-00-0000 = vide). On normalise en AAAA-MM-JJ
// pour coller au stockage app (Lot 3).
function normalizeBirthDate(raw) {
  const s = String(raw || "").trim();
  if (!s) return "";
  if (/^0{2,4}[-/]?0{0,2}[-/]?0{0,4}$/.test(s.replace(/\s/g, ""))) return "";
  let m = s.match(/^(\d{2})[-/](\d{2})[-/](\d{4})$/);
  if (m) return `${m[3]}-${m[2]}-${m[1]}`;
  m = s.match(/^(\d{4})[-/](\d{2})[-/](\d{2})$/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  return s;
}

async function fetchContactFormHtml(page, contactId) {
  const group = "contacts,pilotage_accueil_contact,mefContacts/accueilContact";
  const params = new URLSearchParams({
    mode: "contacts-ihmChargeGroupe",
    id: contactId,
    consultMode: "editer",
    ajax: "true",
    group,
  });
  const url = `${XMLRPC_URL}?${params.toString()}`;
  const referer = `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(contactId)}`;
  return page.evaluate(async ({ url, referer }) => {
    const response = await fetch(url, {
      credentials: "include",
      headers: {
        Accept: "application/json, text/javascript, text/html, */*; q=0.01",
        Referer: referer,
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    return { status: response.status, url: response.url, text: await response.text() };
  }, { url, referer });
}

async function extractContactIdentity(page, html) {
  return page.evaluate(({ html }) => {
    const clean = (v) => String(v == null ? "" : v).replace(/\s+/g, " ").trim();
    const doc = new DOMParser().parseFromString(html || "", "text/html");
    const fieldValue = (name) => {
      const el = doc.querySelector(`[name="${name}"]`);
      if (!el) return null;
      const tag = (el.tagName || "").toLowerCase();
      if (tag === "select") {
        const sel = Array.from(el.options || []).find((o) => o.selected);
        return sel ? clean(sel.value) : clean(el.value);
      }
      return clean(el.getAttribute("value") || el.value || "");
    };
    return {
      birth_date: fieldValue("dateNaissance"),
      birth_place: fieldValue("lieuNaissance"),
      marital_status: fieldValue("marital_status"),
    };
  }, { html });
}

async function extractOne(page, contactId) {
  const started = Date.now();
  const fetched = await fetchContactFormHtml(page, contactId);
  const html = decodeMaybeJsonHtml(fetched.text);
  const base = {
    hektor_contact_id: contactId,
    http_status: fetched.status,
    html_bytes: html.length,
    elapsed_ms: Date.now() - started,
    extracted_at: new Date().toISOString(),
  };
  if (fetched.status === 403) {
    return { ...base, status: "stopped_on_403", error: "Hektor 403 sur le formulaire contact" };
  }
  if (fetched.status >= 400) {
    return { ...base, status: "error", error: `HTTP ${fetched.status} sur le formulaire contact` };
  }
  if (looksLikeLoginPage(html)) {
    return { ...base, status: "session_expired", error: "Session Hektor expiree ou page login retournee" };
  }
  const identity = await extractContactIdentity(page, html);
  return {
    ...base,
    status: "done",
    birth_date: normalizeBirthDate(identity.birth_date),
    birth_place: identity.birth_place || "",
    marital_status: identity.marital_status || "",
  };
}

async function main() {
  const contactIds = uniqueContactIds();
  const storageStatePath = path.resolve(argValue(
    "--storage-state",
    process.env.CONSOLE_INSPECT_STORAGE_STATE_PATH || path.join(__dirname, "sessions", "storage_state_admin.json"),
  ));
  const delayMs = Number(argValue("--delay-ms", "0")) || 0;
  const timeoutMs = Number(argValue("--timeout-ms", "60000")) || 60000;
  if (!contactIds.length) {
    throw new Error("Aucun --contact-id fourni");
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
    for (let index = 0; index < contactIds.length; index += 1) {
      const result = await extractOne(page, contactIds[index]);
      results.push(result);
      if (result.status === "stopped_on_403" || result.status === "session_expired") {
        const summary = {
          status: result.status,
          storage_state: storageStatePath,
          results,
          elapsed_ms: Date.now() - started,
        };
        console.log(JSON.stringify(summary));
        process.exitCode = result.status === "stopped_on_403" ? 3 : 2;
        return;
      }
      if (index < contactIds.length - 1 && delayMs > 0) {
        await sleep(delayMs);
      }
    }
    console.log(JSON.stringify({
      status: "done",
      storage_state: storageStatePath,
      results,
      elapsed_ms: Date.now() - started,
    }));
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exitCode = 1;
});
