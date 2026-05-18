const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "matterport", ".env") });

const STORAGE_STATE_PATH = process.env.MATTERPORT_STORAGE_STATE_PATH || path.resolve(__dirname, "matterport_storage_state.json");
const MODELS_URL = process.env.MATTERPORT_MODELS_URL || "https://my.matterport.com/models";
const HEADLESS = /^(1|true|yes|oui)$/i.test(process.env.MATTERPORT_HEADLESS || "");
const EXPORT_ROOT = path.resolve(__dirname, "exports", `matterport_action_${new Date().toISOString().replace(/[:.]/g, "-")}`);

const args = process.argv.slice(2);
const command = args[0] || "help";
const modelId = args[1] || process.env.MATTERPORT_TEST_MODEL_ID || process.env.MATTERPORT_MODEL_ID || "";
const confirm = args.includes("--confirm");
const targetVisibility = (args.find((arg) => arg.startsWith("--visibility=")) || "").split("=")[1];

function usage() {
  console.log(`
Usage:
  node matterport_console_actions.js menu <modelId>
  node matterport_console_actions.js share <modelId>
  node matterport_console_actions.js online <modelId> --confirm
  node matterport_console_actions.js offline <modelId> --confirm
  node matterport_console_actions.js archive <modelId> --confirm
  node matterport_console_actions.js reactivate <modelId> --confirm
  node matterport_console_actions.js visibility <modelId> --visibility=private|unlisted|public --confirm

Sans --confirm, le script ouvre et inspecte seulement l'ecran Matterport.
Session requise: node matterport_playwright_login.js
`);
}

function ensureExportDir() {
  fs.mkdirSync(EXPORT_ROOT, { recursive: true });
}

function cssEscape(value) {
  return String(value).replace(/["\\]/g, "\\$&");
}

async function snapshot(page, label) {
  await fs.promises.writeFile(path.join(EXPORT_ROOT, `${label}_url.txt`), page.url(), "utf-8");
  await fs.promises.writeFile(path.join(EXPORT_ROOT, `${label}_text.txt`), await page.locator("body").innerText().catch(() => ""), "utf-8");
  await page.screenshot({ path: path.join(EXPORT_ROOT, `${label}.png`), fullPage: true }).catch(() => {});
}

async function collectControls(page, label) {
  const controls = await page.locator("button, [role='menuitem'], input, label, [data-testid]").evaluateAll((nodes) =>
    nodes.map((node, i) => ({
      i,
      tag: node.tagName,
      type: node.getAttribute("type"),
      role: node.getAttribute("role"),
      text: (node.innerText || node.textContent || "").trim(),
      value: node.value || node.getAttribute("value"),
      checked: node.checked ?? node.getAttribute("aria-checked"),
      aria: node.getAttribute("aria-label"),
      testid: node.getAttribute("data-testid"),
      disabled: node.disabled ?? node.getAttribute("aria-disabled"),
    }))
  );
  await fs.promises.writeFile(path.join(EXPORT_ROOT, `${label}_controls.json`), JSON.stringify(controls, null, 2), "utf-8");
  return controls;
}

async function openModels(page) {
  await page.goto(MODELS_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(1200);
}

async function applyStatusFilter(page, status) {
  if (!status) return;
  await page.locator('[data-testid="status-filter-button"], button:has-text("Statut"), button:has-text("Status")').first().click();
  await page.waitForTimeout(500);
  const testId = status === "archived" ? "archived" : "active";
  const label = status === "archived" ? /Archivé|Archived/i : /Actif|Active/i;
  await page.locator(`[data-testid="${testId}"], [role="menuitem"]`).filter({ hasText: label }).first().click();
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(1600);
}

async function searchModel(page, id) {
  const search = page.locator('input[aria-label="Rechercher"], input[placeholder*="Rechercher"], input[placeholder*="Search" i], input[type="search"]').first();
  if (!(await search.isVisible({ timeout: 5000 }).catch(() => false))) return false;
  await search.fill(id);
  await page.keyboard.press("Enter");
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(2500);
  return true;
}

async function openRowMenu(page, id, options = {}) {
  await applyStatusFilter(page, options.status);
  const rowContainer = page.locator(`#model_${cssEscape(id)}_container`);
  const visible = await rowContainer.isVisible({ timeout: 8000 }).catch(() => false);
  if (!visible) {
    await searchModel(page, id);
  }
  let actionButton;
  let row;
  if (await rowContainer.isVisible({ timeout: 5000 }).catch(() => false)) {
    row = rowContainer.locator("xpath=ancestor::li[1]");
    actionButton = row.locator('button:has([data-testid="icon-more-kebab"]), button[aria-label="Actions"]').last();
  } else {
    actionButton = page.locator('main button:has([data-testid="icon-more-kebab"]), main button[aria-label="Actions"]').last();
    row = actionButton.locator("xpath=ancestor::li[1]");
  }
  await actionButton.waitFor({ state: "visible", timeout: 30000 });
  await row.scrollIntoViewIfNeeded().catch(() => {});
  await actionButton.click();
  await page.getByRole("menuitem").first().waitFor({ state: "visible", timeout: 10000 });
  return row;
}

async function clickMenuItem(page, name) {
  const item = page.getByRole("menuitem", { name }).first();
  await item.waitFor({ state: "visible", timeout: 10000 });
  await item.click();
}

async function openSharePanel(page, id) {
  await openRowMenu(page, id);
  await clickMenuItem(page, /Partager et inviter/i);
  await page.locator('[role="dialog"], [data-testid="dialog"]').first().waitFor({ state: "visible", timeout: 15000 });
}

async function getVisibilityState(page) {
  const radios = await page.locator('input[type="radio"]').evaluateAll((nodes) =>
    nodes.map((node) => ({
      value: node.value,
      checked: node.checked,
      disabled: node.disabled,
      label: node.closest("label")?.innerText?.trim() || "",
    }))
  );
  return radios;
}

async function setVisibility(page, visibility) {
  const allowed = new Set(["private", "unlisted", "public"]);
  if (!allowed.has(visibility)) {
    throw new Error("--visibility doit valoir private, unlisted ou public");
  }

  const radio = page.locator(`input[type="radio"][value="${visibility}"]`).first();
  await radio.waitFor({ state: "attached", timeout: 10000 });
  const disabled = await radio.evaluate((node) => Boolean(node.disabled));
  if (disabled) {
    throw new Error(`La visibilite ${visibility} est presente mais desactivee dans Matterport pour ce modele.`);
  }
  await radio.locator("xpath=ancestor::label[1]").click();
}

async function confirmDialogLastButton(page, labelPattern) {
  const dialog = page.locator('[role="dialog"], [data-testid="dialog"]').first();
  await dialog.waitFor({ state: "visible", timeout: 15000 });
  const matchingButton = dialog.locator("button").filter({ hasText: labelPattern }).last();
  if (await matchingButton.isVisible({ timeout: 2500 }).catch(() => false)) {
    await matchingButton.click({ force: true });
  } else {
    await dialog.locator("button").last().click({ force: true });
  }
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(2500);
}

async function main() {
  if (command === "help" || !modelId) {
    usage();
    return;
  }
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    throw new Error(`Session Matterport introuvable: ${STORAGE_STATE_PATH}. Lance d'abord node matterport_playwright_login.js`);
  }

  ensureExportDir();
  const browser = await chromium.launch({ headless: HEADLESS, slowMo: HEADLESS ? 0 : 70 });
  const context = await browser.newContext({
    storageState: STORAGE_STATE_PATH,
    viewport: { width: 1440, height: 950 },
  });
  const page = await context.newPage();

  await openModels(page);

  if (command === "menu") {
    await openRowMenu(page, modelId);
    const items = await page.getByRole("menuitem").evaluateAll((nodes) => nodes.map((node) => node.innerText.trim()));
    await snapshot(page, "menu");
    console.log("Actions Matterport trouvees:");
    for (const item of items) console.log(`- ${item}`);
    console.log("Export:", EXPORT_ROOT);
  } else if (command === "share") {
    await openSharePanel(page, modelId);
    const radios = await getVisibilityState(page);
    await collectControls(page, "share");
    await snapshot(page, "share");
    console.log("Confidentialites Matterport:");
    for (const radio of radios) {
      console.log(`- ${radio.value}: checked=${radio.checked} disabled=${radio.disabled}`);
    }
    console.log("Export:", EXPORT_ROOT);
  } else if (command === "archive") {
    await openRowMenu(page, modelId);
    await snapshot(page, "archive_before");
    if (!confirm) {
      console.log("Dry-run: menu ouvert, aucune action d'archivage executee. Ajoute --confirm pour cliquer Archiver l'Espace.");
      console.log("Export:", EXPORT_ROOT);
    } else {
      await clickMenuItem(page, /Archiver l.?Espace/i);
      await confirmDialogLastButton(page, /Archiver/i);
      const stillArchiveDialog = /Archiver cet espace/i.test(await page.locator("body").innerText().catch(() => ""));
      if (stillArchiveDialog) {
        await confirmDialogLastButton(page, /Archiver/i);
      }
      await snapshot(page, "archive_after_confirm");
      console.log("Archivage confirme dans Matterport.");
      console.log("Export:", EXPORT_ROOT);
    }
  } else if (command === "reactivate" || command === "unarchive") {
    await openRowMenu(page, modelId, { status: "archived" });
    await snapshot(page, "reactivate_before");
    if (!confirm) {
      console.log("Dry-run: menu archive ouvert, aucune reactivation executee. Ajoute --confirm pour cliquer Reactiver l'espace.");
      console.log("Export:", EXPORT_ROOT);
    } else {
      await clickMenuItem(page, /Réactiver|Reactiver|Restaurer|Activer/i);
      await confirmDialogLastButton(page, /Réactiver|Reactiver|Restaurer|Activer/i);
      await snapshot(page, "reactivate_after_confirm");
      console.log("Reactivation confirmee dans Matterport.");
      console.log("Export:", EXPORT_ROOT);
    }
  } else if (command === "online" || command === "offline" || command === "visibility") {
    const nextVisibility = command === "online"
      ? "unlisted"
      : command === "offline"
        ? "private"
        : targetVisibility;
    await openSharePanel(page, modelId);
    const before = await getVisibilityState(page);
    await fs.promises.writeFile(path.join(EXPORT_ROOT, "visibility_before.json"), JSON.stringify(before, null, 2), "utf-8");
    await snapshot(page, "visibility_before");
    if (!confirm) {
      console.log("Dry-run: panneau de confidentialite ouvert, aucune modification executee. Ajoute --confirm pour changer.");
      console.log("Valeur demandee:", nextVisibility || "(non fournie)");
      console.log("Export:", EXPORT_ROOT);
    } else {
      await setVisibility(page, nextVisibility);
      await page.waitForTimeout(1500);
      const after = await getVisibilityState(page);
      await fs.promises.writeFile(path.join(EXPORT_ROOT, "visibility_after.json"), JSON.stringify(after, null, 2), "utf-8");
      await snapshot(page, "visibility_after");
      console.log("Changement de confidentialite clique:", nextVisibility);
      console.log("Export:", EXPORT_ROOT);
    }
  } else {
    usage();
  }

  await context.storageState({ path: STORAGE_STATE_PATH });
  await browser.close();
}

main().catch((error) => {
  console.error("Erreur commande Matterport:", error.message);
  process.exit(1);
});
