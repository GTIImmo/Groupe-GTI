// LECTURE SEULE : le formulaire contact de Hektor porte-t-il le bloc conjoint ?
// N'ECRIT NULLE PART. Trois fiches, 1,5 s entre deux.
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
const RACINE = "C:/Hektor/Projet";
require("dotenv").config({ path: path.join(RACINE, "Console", ".env") });
require("dotenv").config({ path: path.join(RACINE, ".env") });

const BASE = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN = BASE + "/admin/";
const XML = ADMIN + "xmlrpc.php";
const FICHES = ["141053"];

function html2(text) {
  const raw = String(text || "");
  try { const p = JSON.parse(raw); if (typeof p === "string") return p; } catch (_) {}
  return raw;
}

(async () => {
  const sess = path.join(RACINE, "Console", "sessions", "storage_state_admin.json");
  if (!fs.existsSync(sess)) throw new Error("session introuvable: " + sess);
  const exe = ["C:\Program Files\Google\Chrome\Application\chrome.exe"].find((c) => fs.existsSync(c));
  const browser = await chromium.launch({ headless: true, ...(exe ? { executablePath: exe } : {}) });
  const ctx = await browser.newContext({ storageState: sess });
  const page = await ctx.newPage();
  for (const id of FICHES) {
    const group = "contacts,pilotage_accueil_contact,mefContacts/accueilContact";
    const url = XML + "?mode=contacts-ihmChargeGroupe&id=" + encodeURIComponent(id)
      + "&consultMode=editer&ajax=true&group=" + encodeURIComponent(group);
    const rep = await page.request.get(url, { headers: { Referer: ADMIN + "?page=/mes-contacts/mon-contact&id=" + id } });
    const html = html2(await rep.text());
    console.log("=== fiche " + id + "  statut " + rep.status() + "  " + html.length + " caracteres ===");
    const champs = [];
    const re = /<input\b[^>]*>/gi;
    let m;
    while ((m = re.exec(html))) {
      const nm = /name=["']([^"']+)["']/i.exec(m[0]);
      if (!nm) continue;
      const n = nm[1];
      if (!/m2|prive|conjoint|^nom$|^prenom$|^civilite$/i.test(n)) continue;
      const v = /value=["']([^"']*)["']/i.exec(m[0]);
      champs.push([n, v ? v[1] : ""]);
    }
    if (!champs.length) console.log("   aucun champ correspondant");
    for (const [n, v] of champs) console.log("   " + n.padEnd(26) + " = " + JSON.stringify(v));
    console.log();
    await new Promise((r) => setTimeout(r, 1500));
  }
  await browser.close();
})().catch((e) => { console.error("ERREUR", e && e.message ? e.message : e); process.exit(1); });
