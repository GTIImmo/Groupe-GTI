// LE METIER D'UN CONTACT PARTENAIRE CHEZ HEKTOR (liste « metier » de son formulaire). 04/11/2026
// Jumeau de extract_hektor_diag_contacts_only.js : un navigateur pour tout le lot, UNE requete par
// contact (le formulaire d'edition, lecture seule, GET). --contact-ids 602487,605064,...
// Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §16 (lot 1, A9).
// (en-tete du jumeau ci-dessous, conserve pour memoire)
//
// Jumeau de extract_hektor_chauffage_only.js : un seul bloc console lu (« diagnostiques », mode
// editer), UNE requete par annonce, un seul navigateur pour tout le lot. L'outil complet
// (extract_hektor_missing_fields.js) lit 21 pages par annonce pour les memes deux valeurs.
//
// Il rend, pour chaque annonce, `diagnostics_contacts_console_json` sous la MEME forme que l'outil
// complet ({ diagnostiqueur: {value, selected_label, label, tag, type, id, checked}, syndic: {...} }),
// et, une seule fois par lot, la LISTE DES CHOIX des deux listes (= tous les contacts de Hektor dont
// le metier est Diagnostiqueur ou Syndic, mesure du 04/11).
//
// Lecture seule chez Hektor (GET). Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §10-12.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN_URL = `${HEKTOR_BASE_URL}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const DIAGNOSTIC_CONTACT_KEYS = ["diagnostiqueur", "syndic"];

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

// Meme lecture que extractFields + compactFields de l'outil complet, restreinte aux deux listes.
async function fetchContactFormHtml(page, contactId) {
  const group = "contacts,pilotage_accueil_contact,mefContacts/accueilContact";
  const url = `${XMLRPC_URL}?mode=contacts-ihmChargeGroupe&id=${encodeURIComponent(contactId)}&consultMode=editer&ajax=true&group=${encodeURIComponent(group)}`;
  const referer = `${ADMIN_URL}?page=/mes-contacts/mon-contact&id=${encodeURIComponent(contactId)}`;
  return page.evaluate(async ({ url, referer }) => {
    const response = await fetch(url, {
      credentials: "include",
      headers: { Accept: "application/json, text/javascript, text/html, */*; q=0.01", Referer: referer, "X-Requested-With": "XMLHttpRequest" },
    });
    return { status: response.status, url: response.url, text: await response.text() };
  }, { url, referer });
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
  if (fetched.status === 403) return { ...base, status: "stopped_on_403", error: "Hektor 403 sur le formulaire contact" };
  if (fetched.status >= 400) return { ...base, status: "error", error: `HTTP ${fetched.status} sur le formulaire contact` };
  if (!html.length) return { ...base, status: "error", error: "Formulaire vide (contact supprime ?)" };
  if (looksLikeLoginPage(html) && !html.includes('name="metier"')) {
    return { ...base, status: "session_expired", error: "Session Hektor expiree ou page login retournee" };
  }
  const metier = await page.evaluate(({ html }) => {
    const doc = new DOMParser().parseFromString(html || "", "text/html");
    const el = doc.querySelector('select[name="metier"]');
    if (!el) return null;
    const opt = Array.from(el.options || []).find((o) => o.selected) || null;
    return { value: el.value || "", label: opt ? String(opt.textContent || "").replace(/\s+/g, " ").trim() : "" };
  }, { html });
  if (!metier) return { ...base, status: "error", error: "Liste metier introuvable dans le formulaire" };
  return { ...base, status: "done", metier };
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
    for (let index = 0; index < annonceIds.length; index += 1) {
      const result = await extractOne(page, annonceIds[index]);
      results.push(result);
      if (result.status === "stopped_on_403" || result.status === "session_expired") {
        console.log(JSON.stringify({
          status: result.status,
          storage_state: storageStatePath,
          results,
          elapsed_ms: Date.now() - started,
        }));
        process.exitCode = result.status === "stopped_on_403" ? 3 : 2;
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
