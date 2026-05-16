const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
const { chromium } = require("playwright");

function must(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

function hostIncludes(url, expectedDomain) {
  try {
    return new URL(url).hostname.includes(expectedDomain);
  } catch {
    return false;
  }
}

async function safeClick(page, locator) {
  // 1) click normal
  try { await locator.click({ timeout: 5000 }); return; } catch (_) {}
  // 2) click force (ignore overlay)
  try { await locator.click({ force: true, timeout: 5000 }); return; } catch (_) {}
  // 3) click JS
  try {
    const handle = await locator.elementHandle();
    if (handle) {
      await page.evaluate((el) => el.click(), handle);
      return;
    }
  } catch (_) {}
  throw new Error("Could not click element");
}

async function saveDebug(page, baseDir) {
  const debugPng    = path.resolve(baseDir, "login_failed.png");
  const debugHtml   = path.resolve(baseDir, "debug_login.html");
  const debugUrlTxt = path.resolve(baseDir, "debug_login_url.txt");
  fs.writeFileSync(debugUrlTxt, page.url(), "utf-8");
  fs.writeFileSync(debugHtml, await page.content(), "utf-8");
  await page.screenshot({ path: debugPng, fullPage: true }).catch(() => {});
  console.log("🧾 Debug saved:", debugUrlTxt, debugHtml, debugPng);
}

async function findPageOnDomain(context, expectedDomain, timeoutMs = 90000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const pages = context.pages();
    for (const p of pages) {
      const u = p.url();
      if (hostIncludes(u, expectedDomain)) return p;
    }
    await new Promise(r => setTimeout(r, 400));
  }
  return null;
}

// ✅ Robust goto with retry for ERR_NETWORK_CHANGED and similar transient errors
async function gotoWithRetry(page, url, opts = {}) {
  const tries = opts.tries ?? 4;
  const waitUntil = opts.waitUntil ?? "domcontentloaded";
  const timeout = opts.timeout ?? 60000;
  const retryDelayMs = opts.retryDelayMs ?? 1500;

  for (let i = 1; i <= tries; i++) {
    try {
      // If already on url (or url prefix), skip navigation
      if (page.url() && (page.url() === url || page.url().startsWith(url))) {
        return;
      }

      await page.goto(url, { waitUntil, timeout });
      await page.waitForLoadState("networkidle", { timeout: 30000 }).catch(() => {});
      return;
    } catch (e) {
      const msg = String(e?.message || e);
      const transient =
        msg.includes("ERR_NETWORK_CHANGED") ||
        msg.includes("net::ERR_NETWORK_CHANGED") ||
        msg.includes("Navigation failed") ||
        msg.includes("net::ERR_CONNECTION_RESET") ||
        msg.includes("net::ERR_CONNECTION_CLOSED") ||
        msg.includes("net::ERR_TIMED_OUT");

      console.log(`⚠️ goto attempt ${i}/${tries} failed: ${msg}`);

      if (transient && i < tries) {
        await page.waitForTimeout(retryDelayMs);
        continue;
      }
      throw e;
    }
  }
}

(async () => {
  const BASE_DIR = __dirname;

  // Env
  const LOGIN_URL     = must("HEKTOR_LOGIN_URL");      // https://ma-boite-immo.com/connexion
  const EXPECT_DOMAIN = must("HEKTOR_EXPECT_DOMAIN");  // groupe-gti-immobilier.la-boite-immo.com
  const HEKTOR_BASE   = process.env.HEKTOR_BASE_URL || `https://${EXPECT_DOMAIN}`;
  const ADMIN_URL     = process.env.HEKTOR_ADMIN_URL || `${HEKTOR_BASE.replace(/\/+$/, "")}/admin/`;
  const LOGIN         = must("HEKTOR_LOGIN").trim();
  const PASSWORD      = must("HEKTOR_PASSWORD").trim();

  // Outputs
  const storagePath   = process.env.CONSOLE_STORAGE_STATE_PATH
    ? path.resolve(process.env.CONSOLE_STORAGE_STATE_PATH)
    : path.resolve(BASE_DIR, "storage_state.json");
  const tokenDumpPath = path.resolve(BASE_DIR, "token_dump.json");
  const gqlHeadersOut = path.resolve(BASE_DIR, "debug_graphql_headers.json");
  const tabsDumpPath  = path.resolve(BASE_DIR, "debug_tabs_urls.json");

  const browser = await chromium.launch({ headless: false, slowMo: 40 });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Dump the exact request headers used by the browser for GraphQL
  context.on("request", (req) => {
    try {
      if (req.url().includes("/ws/GraphQL_Web")) {
        const dump = {
          url: req.url(),
          method: req.method(),
          headers: req.headers(),
        };
        fs.writeFileSync(gqlHeadersOut, JSON.stringify(dump, null, 2), "utf-8");
        console.log("✅ debug_graphql_headers.json saved.");
      }
    } catch (_) {}
  });

  try {
    console.log("🔐 Opening login portal:", LOGIN_URL);
    await gotoWithRetry(page, LOGIN_URL, { tries: 4, waitUntil: "domcontentloaded", timeout: 60000 });

    await page.waitForLoadState("networkidle", { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(800);

    // A) Login
    const emailInput = page.locator('input[type="email"]').first();
    const passInput  = page.locator('input[type="password"]').first();
    await emailInput.waitFor({ state: "visible", timeout: 25000 });
    await passInput.waitFor({ state: "visible", timeout: 25000 });
    await emailInput.fill(LOGIN);
    await passInput.fill(PASSWORD);

    const submitBtn = page.locator(
      'button[type="submit"], input[type="submit"], button:has-text("Connexion"), button:has-text("Se connecter")'
    ).first();

    if (await submitBtn.count()) {
      await safeClick(page, submitBtn);
    } else {
      await page.keyboard.press("Enter");
    }

    await page.waitForLoadState("networkidle", { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(1200);

    // B) Click menu "Hektor"
    const hektorMenu = page.locator("text=Hektor").first();
    await hektorMenu.waitFor({ state: "visible", timeout: 30000 });
    await safeClick(page, hektorMenu);

    // Wait HeadlessUI dialog
    const dialog = page.locator('[role="dialog"][aria-modal="true"]').first();
    await dialog.waitFor({ state: "visible", timeout: 30000 });
    await page.waitForTimeout(400);

    // C) Click ADMIN / J’y accède
    const adminCard = dialog.locator(':has-text("ADMIN")').first();
    await adminCard.waitFor({ state: "visible", timeout: 30000 });

    const adminAccessBtn = adminCard.locator(
      'button:has-text("J’y accède"), button:has-text("J\'y accède")'
    ).first();
    await adminAccessBtn.waitFor({ state: "visible", timeout: 30000 });

    // Popup may open
    const popupPromise = context.waitForEvent("page", { timeout: 15000 }).catch(() => null);

    console.log("👉 Clicking ADMIN 'J’y accède' ...");
    await safeClick(page, adminAccessBtn);

    const popup = await popupPromise;
    if (popup) {
      await popup.waitForLoadState("domcontentloaded", { timeout: 60000 }).catch(() => {});
      console.log("🪟 Popup opened:", popup.url());
    }

    // D) Find any tab on expected domain
    console.log("⏳ Waiting to reach domain (any tab):", EXPECT_DOMAIN);
    const landed = await findPageOnDomain(context, EXPECT_DOMAIN, 90000);

    if (!landed) {
      const urls = context.pages().map(p => p.url());
      fs.writeFileSync(tabsDumpPath, JSON.stringify(urls, null, 2), "utf-8");
      throw new Error("Timeout: expected domain not found in any tab. See debug_tabs_urls.json");
    }

    console.log("✅ Landed on:", landed.url());

    // E) Ensure admin (robust)
    console.log("➡️ Opening admin:", ADMIN_URL);
    await gotoWithRetry(landed, ADMIN_URL, { tries: 4, waitUntil: "domcontentloaded", timeout: 60000 });
    await landed.waitForTimeout(800);
    console.log("✅ Admin loaded:", landed.url());

    // F) Trigger GraphQL fetch (status should be 200)
    console.log("⚠️ Triggering GraphQL call inside page...");
    const status = await landed.evaluate(async () => {
      const body = {
        operationName: "PropertyListing",
        query: `query PropertyListing($filters: AnnonceSearchInput!) {
          listing: properties(filters: $filters) {
            metadata { total perPage currentPage nextPage }
            properties: nodes { id }
          }
        }`,
        variables: {
          filters: {
            limit: 1,
            offers: ["SALE"],
            status: "ALL",
            page: 1,
            order: "LATEST",
            sources: ["local"],
            archived: false,
            negotiators: [],
            agencies: [],
            communityAgencies: [],
            agents: [],
            highlights: [],
            broadcastStatuses: [],
            matchingStatuses: [],
            propertyTypes: []
          }
        }
      };

      const r = await fetch("/ws/GraphQL_Web", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        credentials: "include",
      });
      return r.status;
    });

    console.log("ℹ️ GraphQL fetch status inside page:", status);

    // G) Dump local/session storage (for token hunting if any)
    const storageDump = await landed.evaluate(() => {
      const out = { localStorage: {}, sessionStorage: {} };
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        out.localStorage[k] = localStorage.getItem(k);
      }
      for (let i = 0; i < sessionStorage.length; i++) {
        const k = sessionStorage.key(i);
        out.sessionStorage[k] = sessionStorage.getItem(k);
      }
      return out;
    });
    fs.writeFileSync(tokenDumpPath, JSON.stringify(storageDump, null, 2), "utf-8");
    console.log("✅ token_dump.json saved.");

    // H) Save cookies/session for later scripts
    await context.storageState({ path: storagePath });
    console.log("✅ storage_state.json saved:", storagePath);

    await browser.close();
    process.exit(0);

  } catch (e) {
    console.error("❌ Playwright flow failed:", e.message);
    await saveDebug(page, BASE_DIR);
    await browser.close();
    process.exit(1);
  }
})();
