const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN_URL = `${HEKTOR_BASE_URL}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;

const GROUPS = [
  { group: "secteur", mode: "ihmChargeGroupe_Secteur" },
  { group: "ag_interieur", mode: "ihmChargeGroupe" },
  { group: "ag_exterieur", mode: "ihmChargeGroupe" },
  { group: "terrain", mode: "ihmChargeGroupe" },
  { group: "equipements", mode: "ihmChargeGroupe" },
  { group: "diagnostiques", mode: "ihmChargeGroupe" },
  { group: "copropriete", mode: "ihmChargeGroupe" },
  { group: "organiser_visite", mode: "ihmChargeGroupe" },
  { group: "mandat_infofi", mode: "ihmChargeGroupe_MandatPrix" },
  { group: "mandat_mandatdispo", mode: "ihmChargeGroupe" },
];

const SECTEUR_KEYS = ["immeuble", "TRANSPORT", "PROXIMITE", "ENVIRONNEMENT"];
const DIAGNOSTIC_CONTACT_KEYS = ["diagnostiqueur", "syndic"];
const HONORAIRES_KEYS = [
  "_selecterHonoraires2",
  "_tauxHonoraire2",
  "_pourcentHonoraire2",
  "_detailHonoraire2",
  "_selecterHonoraires3",
  "_tauxHonoraire3",
  "_pourcentHonoraire3",
  "_detailHonoraire3",
];
const LOCATION_KEYS = ["Loc_EstimationLoyer", "Loc_ChargeLocative", "Loc_RendementBrut", "Loc_Occupation"];

function argValue(name, fallback = "") {
  const index = process.argv.indexOf(name);
  return index >= 0 && index + 1 < process.argv.length ? String(process.argv[index + 1] || "").trim() : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

const annonceId = argValue("--annonce-id", process.argv[2] || "");
const storageStatePath = path.resolve(argValue(
  "--storage-state",
  process.env.CONSOLE_INSPECT_STORAGE_STATE_PATH || path.join(__dirname, "sessions", "storage_state_admin.json"),
));
const writeDebug = hasFlag("--write-debug");
const exportRoot = path.resolve(argValue(
  "--export-root",
  path.join(__dirname, "exports", `missing_fields_${annonceId || "unknown"}_${new Date().toISOString().replace(/[:.]/g, "-")}`),
));

function browserLaunchOptions(options = {}) {
  const executablePath = [
    process.env.CONSOLE_CHROME_EXE,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].find((candidate) => candidate && fs.existsSync(candidate)) || "";
  return {
    ...options,
    ...(executablePath ? { executablePath } : {}),
  };
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function redactUrl(url) {
  return String(url || "").replace(/([?&](?:token|jwt|authorization|password|secret)=)[^&]+/ig, "$1[redacted]");
}

function decodeMaybeJsonHtml(text) {
  const raw = String(text || "");
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed === "string") return parsed;
    if (parsed && typeof parsed === "object" && typeof parsed.content === "string") return parsed.content;
  } catch (_) {
    // Hektor returns either raw HTML or JSON encoded HTML.
  }
  return raw;
}

function cleanText(value) {
  return String(value == null ? "" : value).replace(/\s+/g, " ").trim();
}

function extractDpeUrlsFromText(text) {
  const urls = new Set();
  const source = String(text || "");
  const patterns = [
    /https?:\/\/[^"'()\s<>]+\/wa\/images\/DPEImages\/[^"'()\s<>]+/gi,
    /\/\/[^"'()\s<>]+\/wa\/images\/DPEImages\/[^"'()\s<>]+/gi,
    /(?:https?:)?\/\/groupe-gti-immobilier\.staticlbi\.com\/wa\/images\/DPEImages\/[^"'()\s<>]+/gi,
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(source))) {
      const raw = match[0].replace(/&amp;/g, "&");
      urls.add(raw.startsWith("//") ? `https:${raw}` : raw);
    }
  }
  return Array.from(urls).sort();
}

function classifyDpeUrls(urls) {
  const unique = Array.from(new Set((urls || []).filter(Boolean))).sort();
  const filename = (url) => {
    try {
      return path.basename(new URL(url).pathname).toLowerCase();
    } catch (_) {
      return String(url || "").toLowerCase();
    }
  };
  const ges = unique.find((url) => filename(url).includes("ges")) || null;
  const dpe = unique.find((url) => {
    const name = filename(url);
    return !name.includes("ges") && (name.includes("dpe") || name.includes("cons"));
  }) || null;
  return { dpe_image_url: dpe, ges_image_url: ges, dpe_image_urls: unique };
}

async function extractFields(page, html, sourceName) {
  return page.evaluate(({ html, sourceName }) => {
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
    return Array.from(doc.querySelectorAll("input[name], select[name], textarea[name]")).map((el) => {
      const options = el.tagName === "SELECT"
        ? Array.from(el.options || []).map((option) => ({ value: option.value, label: clean(option.textContent), selected: option.selected }))
        : [];
      const selected = options.find((option) => option.selected) || null;
      return {
        source: sourceName,
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute("type") || null,
        id: el.getAttribute("id") || null,
        name: el.getAttribute("name") || null,
        group: el.getAttribute("group") || el.getAttribute("data-group") || null,
        value: el.tagName === "SELECT"
          ? options.filter((option) => option.selected).map((option) => option.value).join("|")
          : el.getAttribute("value") || el.value || "",
        selected_label: selected ? selected.label : null,
        checked: "checked" in el ? Boolean(el.checked) : null,
        label: labelFor(el),
        text: clean(el.textContent),
        options: options.slice(0, 80),
      };
    });
  }, { html, sourceName });
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

function compactFields(fields) {
  const result = {};
  for (const field of fields || []) {
    const key = cleanText(field.name || field.id);
    if (!key) continue;
    if (field.type === "radio" && field.checked !== true) continue;
    result[key] = {
      value: field.value == null ? "" : String(field.value),
      selected_label: field.selected_label || null,
      label: cleanText(field.label),
      tag: field.tag || null,
      type: field.type || null,
      id: field.id || null,
      checked: field.checked,
    };
  }
  return result;
}

function pickFields(fields, keys) {
  const out = {};
  for (const key of keys) {
    if (fields && fields[key]) out[key] = fields[key];
  }
  return out;
}

function extractPieceHintsFromHtml(html) {
  const source = String(html || "");
  const hasPieceForm = /id\s*=\s*["'](?:detailPiece|typePiece|surfacePiece|notePublique|notePrivee|noteInterAgence)["']/i.test(source)
    || /piece-(?:addNewPiece|updatePiece|deletePiece)/i.test(source);
  return {
    found: hasPieceForm,
    note: hasPieceForm
      ? "La page contient des champs de composition; extraction fine a consolider par route composition si necessaire."
      : "Aucun formulaire de composition detaillee detecte dans les groupes lus.",
  };
}

async function fetchGroup(page, report, groupConfig, consultMode) {
  const params = new URLSearchParams({
    mode: groupConfig.mode,
    ajax: "ajax",
    idAnnonce: annonceId,
    group: groupConfig.group,
    consultMode,
  });
  const url = `${XMLRPC_URL}?${params.toString()}`;
  const referer = `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`;
  const result = await page.evaluate(async ({ url, referer }) => {
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

  report.fetches.push({
    name: `${groupConfig.group}_${consultMode}`,
    status: result.status,
    url: redactUrl(result.url),
    bytes: result.text.length,
  });
  if (result.status === 403) {
    report.forbidden403.push({ name: `${groupConfig.group}_${consultMode}`, status: result.status, url: redactUrl(result.url) });
    const error = new Error(`Hektor 403 pendant groupe ${groupConfig.group} ${consultMode}`);
    error.code = "HEKTOR_403";
    throw error;
  }

  const html = decodeMaybeJsonHtml(result.text);
  if (writeDebug) {
    await fs.promises.writeFile(path.join(exportRoot, `${groupConfig.group}_${consultMode}.html`), html, "utf8");
  }
  const fields = await extractFields(page, html, `${groupConfig.group}_${consultMode}`);
  const compact = compactFields(fields);
  return {
    group: groupConfig.group,
    consultMode,
    status: result.status,
    bytes: result.text.length,
    html,
    fields: compact,
    dpeUrls: extractDpeUrlsFromText(html),
  };
}

function countExtractedFields(report) {
  let count = 0;
  for (const group of Object.values(report.groups || {})) {
    for (const mode of Object.values(group || {})) {
      count += Object.keys((mode && mode.fields) || {}).length;
    }
  }
  count += Array.isArray(report.chauffage_console_json) ? report.chauffage_console_json.length : 0;
  count += Object.keys(report.secteur_console_json || {}).length;
  count += Object.keys(report.diagnostics_contacts_console_json || {}).length;
  count += Object.keys(report.honoraires_detail_console_json || {}).length;
  count += Object.keys(report.location_rendement_console_json || {}).length;
  return count;
}

async function main() {
  if (!/^\d+$/.test(annonceId)) throw new Error("--annonce-id numerique requis");
  if (!fs.existsSync(storageStatePath)) throw new Error(`Session Hektor introuvable: ${storageStatePath}`);
  if (writeDebug) ensureDir(exportRoot);

  const report = {
    status: "started",
    hektor_annonce_id: annonceId,
    extracted_at: new Date().toISOString(),
    storage_state_path: storageStatePath,
    fetches: [],
    forbidden403: [],
    groups: {},
    dpe_image_urls: [],
    dpe_image_url: null,
    ges_image_url: null,
    secteur_console_json: null,
    chauffage_console_json: null,
    diagnostics_contacts_console_json: null,
    honoraires_detail_console_json: null,
    location_rendement_console_json: null,
    pieces_detail_console_json: null,
    error: null,
  };

  const browser = await chromium.launch(browserLaunchOptions({ headless: String(process.env.CONSOLE_HEKTOR_HEADLESS || "true").toLowerCase() !== "false" }));
  const context = await browser.newContext({ storageState: storageStatePath, viewport: { width: 1440, height: 960 } });
  const page = await context.newPage();

  page.on("response", (response) => {
    const url = response.url();
    if (!url.startsWith(ADMIN_URL) && !url.includes("staticlbi.com")) return;
    if (response.status() === 403) {
      report.forbidden403.push({
        at: new Date().toISOString(),
        method: response.request().method(),
        status: response.status(),
        url: redactUrl(url),
      });
    }
    report.dpe_image_urls.push(...extractDpeUrlsFromText(url));
  });

  try {
    const detailResponse = await page.goto(`${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonceId)}`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.waitForLoadState("networkidle", { timeout: 12000 }).catch(() => {});
    await page.waitForTimeout(800);
    if ((detailResponse && detailResponse.status() === 403) || report.forbidden403.length) {
      const error = new Error("Hektor 403 ouverture detail annonce");
      error.code = "HEKTOR_403";
      throw error;
    }
    const detailHtml = await page.content();
    const bodyText = cleanText(await page.locator("body").innerText({ timeout: 3000 }).catch(() => ""));
    if (/mot de passe|connexion|identifiant/i.test(bodyText) && !/Mes biens|Mon bien|Accueil/i.test(bodyText)) {
      const error = new Error("Session Hektor expiree ou page de login detectee");
      error.code = "SESSION_EXPIRED";
      throw error;
    }
    if (writeDebug) await fs.promises.writeFile(path.join(exportRoot, "detail_initial.html"), detailHtml, "utf8");
    report.dpe_image_urls.push(...extractDpeUrlsFromText(detailHtml));
    report.pieces_detail_console_json = extractPieceHintsFromHtml(detailHtml);

    for (const groupConfig of GROUPS) {
      const groupResult = {};
      for (const consultMode of ["editer", "consulter"]) {
        const current = await fetchGroup(page, report, groupConfig, consultMode);
        groupResult[consultMode] = {
          status: current.status,
          bytes: current.bytes,
          fields: current.fields,
        };
        report.dpe_image_urls.push(...current.dpeUrls);
        if (groupConfig.group === "equipements" && consultMode === "editer") {
          report.chauffage_console_json = await extractChauffages(page, current.html);
        }
        if (!report.pieces_detail_console_json.found) {
          const hints = extractPieceHintsFromHtml(current.html);
          if (hints.found) report.pieces_detail_console_json = hints;
        }
      }
      report.groups[groupConfig.group] = groupResult;
    }

    const secteurFields = report.groups.secteur && report.groups.secteur.editer ? report.groups.secteur.editer.fields : {};
    const diagnosticFields = report.groups.diagnostiques && report.groups.diagnostiques.editer ? report.groups.diagnostiques.editer.fields : {};
    const mandatFields = report.groups.mandat_infofi && report.groups.mandat_infofi.editer ? report.groups.mandat_infofi.editer.fields : {};
    report.secteur_console_json = pickFields(secteurFields, SECTEUR_KEYS);
    report.diagnostics_contacts_console_json = pickFields(diagnosticFields, DIAGNOSTIC_CONTACT_KEYS);
    report.honoraires_detail_console_json = pickFields(mandatFields, HONORAIRES_KEYS);
    report.location_rendement_console_json = pickFields(mandatFields, LOCATION_KEYS);

    const classified = classifyDpeUrls(report.dpe_image_urls);
    report.dpe_image_urls = classified.dpe_image_urls;
    report.dpe_image_url = classified.dpe_image_url;
    report.ges_image_url = classified.ges_image_url;
    if (countExtractedFields(report) <= 0) {
      throw new Error("Aucun groupe Hektor exploitable retourne par les appels console");
    }
    report.status = "done";
  } catch (error) {
    report.error = error && error.message ? error.message : String(error);
    if (error && error.code === "HEKTOR_403") report.status = "stopped_on_403";
    else if (error && error.code === "SESSION_EXPIRED") report.status = "session_expired";
    else report.status = report.forbidden403.length ? "stopped_on_403" : "error";
    if (writeDebug) {
      await fs.promises.writeFile(path.join(exportRoot, "error_page.html"), await page.content().catch(() => ""), "utf8");
    }
  } finally {
    await browser.close().catch(() => {});
  }

  if (writeDebug) await fs.promises.writeFile(path.join(exportRoot, "missing_fields_report.json"), JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report));
  if (report.status !== "done") process.exit(report.status === "stopped_on_403" ? 3 : 1);
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
