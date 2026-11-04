// LE SYNDIC ET LE DIAGNOSTIQUEUR D'UNE ANNONCE, SEULS.                       04/11/2026
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

// Meme lecture que extractFields + compactFields de l'outil complet, restreinte aux deux listes.
async function extractDiagContacts(page, html) {
  return page.evaluate(({ html, keys }) => {
    const clean = (value) => String(value == null ? "" : value).replace(/\s+/g, " ").trim();
    const doc = new DOMParser().parseFromString(html || "", "text/html");
    const labelFor = (el) => {
      const id = el.getAttribute("id") || "";
      const forLabel = id ? doc.querySelector(`label[for="${CSS.escape(id)}"]`) : null;
      const wrapper = el.closest("table[id^='Element_']");
      const rowTitle = wrapper ? wrapper.querySelector(".titreIhmBien, .OpenSansSemiBold, td:first-child") : null;
      const nearLabel = el.closest("label");
      return clean((forLabel && forLabel.textContent) || (rowTitle && rowTitle.textContent) || (nearLabel && nearLabel.textContent) || "");
    };
    const fields = {};
    const choix = {};
    for (const key of keys) {
      const el = doc.querySelector(`select[name="${key}"]`) || doc.querySelector(`[name="${key}"]`);
      if (!el) continue;
      const options = el.tagName === "SELECT"
        ? Array.from(el.options || []).map((option) => ({ value: option.value, label: clean(option.textContent), selected: option.selected }))
        : [];
      const selected = options.find((option) => option.selected) || null;
      fields[key] = {
        value: el.tagName === "SELECT"
          ? options.filter((option) => option.selected).map((option) => option.value).join("|")
          : String(el.getAttribute("value") || el.value || ""),
        selected_label: selected ? selected.label : null,
        label: labelFor(el),
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute("type") || null,
        id: el.getAttribute("id") || null,
        checked: "checked" in el ? Boolean(el.checked) : null,
      };
      choix[key] = options.filter((option) => option.value).map((option) => ({ value: option.value, label: option.label }));
    }
    return { fields, choix };
  }, { html, keys: DIAGNOSTIC_CONTACT_KEYS });
}

async function fetchDiagnostiquesHtml(page, annonceId) {
  const params = new URLSearchParams({
    mode: "ihmChargeGroupe",
    ajax: "ajax",
    idAnnonce: annonceId,
    group: "diagnostiques",
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
  const fetched = await fetchDiagnostiquesHtml(page, annonceId);
  const html = decodeMaybeJsonHtml(fetched.text);
  const base = {
    hektor_annonce_id: annonceId,
    http_status: fetched.status,
    html_bytes: html.length,
    elapsed_ms: Date.now() - started,
    extracted_at: new Date().toISOString(),
  };
  if (fetched.status === 403) {
    return { ...base, status: "stopped_on_403", error: "Hektor 403 sur le groupe diagnostiques" };
  }
  if (fetched.status >= 400) {
    return { ...base, status: "error", error: `HTTP ${fetched.status} sur le groupe diagnostiques` };
  }
  if (looksLikeLoginPage(html)) {
    return { ...base, status: "session_expired", error: "Session Hektor expiree ou page login retournee" };
  }
  const { fields, choix } = await extractDiagContacts(page, html);
  // Un bloc SANS aucune des deux listes n'est pas un « vide » : c'est une forme inconnue (annonce
  // archivee, page changee). On le dit, on ne range rien.
  if (!Object.keys(fields).length) {
    return { ...base, status: "error", error: "Listes diagnostiqueur et syndic introuvables dans le bloc diagnostiques" };
  }
  return {
    ...base,
    status: "done",
    diagnostics_contacts_console_json: fields,
    _choix: choix,
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
  let choix = null;
  try {
    await page.goto(ADMIN_URL, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    for (let index = 0; index < annonceIds.length; index += 1) {
      const result = await extractOne(page, annonceIds[index]);
      // La liste des choix est la meme pour tout le groupe : on ne la garde qu'une fois par lot.
      if (result._choix) {
        if (!choix) choix = result._choix;
        delete result._choix;
      }
      results.push(result);
      if (result.status === "stopped_on_403" || result.status === "session_expired") {
        console.log(JSON.stringify({
          status: result.status,
          storage_state: storageStatePath,
          results,
          choix,
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
    choix,
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
