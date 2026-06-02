const fs = require("fs");
const path = require("path");
const readline = require("readline");
const { chromium } = require("playwright");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "matterport", ".env") });

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

const LOGIN_URL = process.env.MATTERPORT_LOGIN_URL || "https://authn.matterport.com/login";
const MODELS_URL = process.env.MATTERPORT_MODELS_URL || "https://my.matterport.com/models";
const STORAGE_STATE_PATH = process.env.MATTERPORT_STORAGE_STATE_PATH || path.resolve(__dirname, "matterport_storage_state.json");
const EMAIL = process.env.MATTERPORT_EMAIL || "";
const PASSWORD = process.env.MATTERPORT_PASSWORD || "";
const MANUAL_CONFIRM = /^(1|true|yes|oui)$/i.test(process.env.MATTERPORT_LOGIN_MANUAL_CONFIRM || "");
const LOGIN_WAIT_MS = Number(process.env.MATTERPORT_LOGIN_WAIT_MS || 120000);
const DEBUG_DIR = path.resolve(__dirname, "exports", "matterport_login_debug");

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function waitForEnter(message) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(message, () => {
      rl.close();
      resolve();
    });
  });
}

function hostIncludes(url, expected) {
  try {
    return new URL(url).hostname.includes(expected);
  } catch (_) {
    return false;
  }
}

async function waitForMatterportConsole(page, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const url = page.url();
    if (hostIncludes(url, "my.matterport.com")) return true;
    const body = await page.locator("body").innerText({ timeout: 1000 }).catch(() => "");
    const loggedInText = /spaces|models|all spaces|my spaces|account|library|dashboard/i.test(body);
    const passwordVisible = await page.locator('input[type="password"]').first().isVisible({ timeout: 500 }).catch(() => false);
    if (loggedInText && !passwordVisible) return true;
    await page.waitForTimeout(1000);
  }
  return false;
}

async function fillInputBySelector(page, selector, value) {
  if (!value) return false;
  const locator = page.locator(selector).first();
  await locator.waitFor({ state: "visible", timeout: 20000 });
  await locator.fill(value);
  await locator.evaluate((el, nextValue) => {
    const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    if (setter) setter.call(el, nextValue);
    else el.value = nextValue;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true }));
  }, value);
  const length = await locator.evaluate((el) => el.value.length).catch(() => 0);
  return length > 0;
}

async function main() {
  ensureDir(STORAGE_STATE_PATH);
  fs.mkdirSync(DEBUG_DIR, { recursive: true });

  const browser = await chromium.launch(browserLaunchOptions({
    headless: false,
    slowMo: 40,
  }));

  const context = await browser.newContext({
    viewport: { width: 1440, height: 950 },
  });
  const page = await context.newPage();

  console.log("Ouverture Matterport:", LOGIN_URL);
  await page.goto(LOGIN_URL, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(1000);

  if (EMAIL) {
    const emailFilled = await fillInputBySelector(page, '#email, input[type="email"], input[name*="email" i], input[id*="email" i]', EMAIL).catch(() => false);
    console.log("Email Matterport rempli:", emailFilled ? "OK" : "NON");
  }

  if (PASSWORD) {
    const passwordFilled = await fillInputBySelector(page, '#password, input[type="password"], input[name*="password" i], input[id*="password" i]', PASSWORD).catch(() => false);
    console.log("Mot de passe Matterport rempli:", passwordFilled ? "OK" : "NON");
    await page.waitForTimeout(800);
    const submit = page.locator('#submitBtn, button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), button:has-text("Connexion"), input[type="submit"]').first();
    const disabled = await submit.evaluate((el) => Boolean(el.disabled || el.getAttribute("aria-disabled") === "true")).catch(() => false);
    console.log("Bouton connexion desactive:", disabled ? "OUI" : "NON");
    if (await submit.isVisible({ timeout: 5000 }).catch(() => false)) {
      await submit.click({ force: true }).catch(() => {});
    } else {
      await page.keyboard.press("Enter").catch(() => {});
    }
    await page.waitForLoadState("networkidle", { timeout: 25000 }).catch(() => {});
    await page.waitForTimeout(2000);
  }

  console.log("");
  console.log("Attente de la console Matterport. Si Matterport demande une double authentification, termine-la dans la fenetre.");
  const reachedConsole = await waitForMatterportConsole(page, LOGIN_WAIT_MS);
  if (!reachedConsole && MANUAL_CONFIRM) {
    console.log("La console n'a pas ete detectee automatiquement.");
    await waitForEnter("Appuie sur Entree pour sauvegarder la session Matterport...");
  } else if (!reachedConsole) {
    console.log("La console n'a pas ete detectee automatiquement, sauvegarde quand meme la session courante pour diagnostic.");
  }

  await page.goto(MODELS_URL, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await fs.promises.writeFile(path.join(DEBUG_DIR, "last_url.txt"), page.url(), "utf-8").catch(() => {});
  await fs.promises.writeFile(path.join(DEBUG_DIR, "last_text.txt"), await page.locator("body").innerText().catch(() => ""), "utf-8").catch(() => {});
  await page.screenshot({ path: path.join(DEBUG_DIR, "last_screen.png"), fullPage: true }).catch(() => {});

  await context.storageState({ path: STORAGE_STATE_PATH });
  console.log("Session Matterport sauvegardee:", STORAGE_STATE_PATH);
  console.log("URL courante:", page.url());

  await browser.close();
}

main().catch((error) => {
  console.error("Erreur login Matterport:", error.message);
  process.exit(1);
});
