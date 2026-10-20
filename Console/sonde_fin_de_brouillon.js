// SONDE EN LECTURE SEULE -- QU'EST-CE QUI TERMINE UN BROUILLON CHEZ HEKTOR ?
//                                                      20/10/2026
//
// LA QUESTION DE FREDERIC : « comment faire pour que ce ne soit plus un draft si on
// le souhaite ? il y a surement un bouton aussi pour cela dans hektor. »
//
// CE QU'ON SAIT DEJA (note du 22/06, mesure) : notre creation
// `create_hektor_draft_annonce` ouvre la page du wizard dans un vrai navigateur et
// appelle `window.saveAndQuitte()` -- et le resultat est une annonce `isDraft=false`.
// ⭐ Donc LE GESTE EXISTE, et on l'appelle deja. Reste a savoir ce qu'il ENVOIE, et
//   s'il y a un chemin plus simple (un mode xmlrpc) pour une annonce EXISTANTE.
//
// ⛔ LECTURE SEULE : 1 appel (le JavaScript vivant), aucune ecriture.
//   node Console/sonde_fin_de_brouillon.js

const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });
const { chromium } = require("playwright");

const BASE = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN = (process.env.HEKTOR_ADMIN_URL || BASE + "/admin").replace(/\/+$/, "");
const SESSION = path.resolve(__dirname, "sessions", "storage_state_documents.json");

function corps(js, nom) {
  const i = js.search(new RegExp(`function\s+${nom}\s*\(`));
  if (i < 0) return null;
  const d = js.indexOf("{", i);
  let p = 0;
  for (let k = d; k < js.length; k += 1) {
    if (js[k] === "{") p += 1;
    else if (js[k] === "}") { p -= 1; if (p === 0) return js.slice(i, k + 1); }
  }
  return js.slice(i, i + 2500);
}

(async () => {
  const nav = await chromium.launch({ headless: true });
  try {
    const ctx = await nav.newContext({ storageState: SESSION });
    const r = await ctx.request.get(`${ADMIN}/xmlrpc.1.2.js.php`, { maxRedirects: 0 });
    if ([401, 403, 429, 503].includes(r.status())) throw new Error(`ARRET NET : ${r.status()}`);
    if (!r.ok()) throw new Error(`Hektor ${r.status()}`);
    const js = await r.text();
    if (/type=["']password["']/i.test(js.slice(0, 20000))) throw new Error("ARRET : page de connexion");
    console.log(`le JavaScript vivant : ${js.length} caracteres\n`);

    console.log("===== LE VOCABULAIRE DU BROUILLON =====");
    for (const mot of ["isDraft", "is_draft", "draft", "brouillon", "saveAndQuitte", "WizardNext",
                       "wizard", "idannWizard", "finaliser", "publier", "valider"]) {
      const n = (js.match(new RegExp(mot, "gi")) || []).length;
      if (n) console.log(`   ${String(n).padStart(4)}x  ${mot}`);
    }

    console.log("\n===== LES MODES QUI PARLENT DE WIZARD OU DE BROUILLON =====");
    const modes = new Set();
    for (const m of js.matchAll(/mode\s*[:=]\s*['"]([^'"]*(?:[Ww]izard|[Dd]raft|[Bb]rouillon|quitte|Quitte)[^'"]*)['"]/g)) modes.add(m[1]);
    for (const m of js.matchAll(/mode=([a-zA-Z0-9_-]*(?:[Ww]izard|[Dd]raft|quitte|Quitte)[a-zA-Z0-9_-]*)/g)) modes.add(m[1]);
    if (!modes.size) console.log("   (aucun)");
    for (const x of [...modes].sort()) console.log(`   ${x}`);

    console.log("\n===== LE CORPS DE saveAndQuitte (ce qu'il ENVOIE) =====");
    const c = corps(js, "saveAndQuitte");
    console.log(c ? c.slice(0, 2200) : "   (fonction introuvable dans ce fichier)");

    console.log("\n===== LES AUTRES FONCTIONS QUI SENTENT LA FIN DE SAISIE =====");
    const noms = new Set();
    for (const m of js.matchAll(/function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g)) {
      const n = m[1];
      if (/quitte|wizard|draft|finalis|publi/i.test(n)) noms.add(n);
    }
    console.log(noms.size ? [...noms].join(", ") : "   (aucune)");

    console.log("\n✅ 1 appel, aucune ecriture.");
  } catch (e) {
    console.error(`\n⛔ ${e.message}`);
    process.exitCode = 1;
  } finally {
    await nav.close();
  }
})();
