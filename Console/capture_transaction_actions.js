// CAPTURE EN LECTURE SEULE -- comment Hektor accepte/refuse une offre, annule un compromis.
//
// POURQUOI
// --------
// L'app sait LIRE ces etats (statistique "compromis annules", icone "offre refusee")
// mais ne sait pas les POSER. Pour les coder il faut le nom exact des appels, et
// deviner est exclu : un mauvais nom de champ n'ecrit rien ET ne dit rien -- c'est
// exactement le defaut corrige le 28/08 sur la cloture de mandat.
//
// Recherche faite avant d'ecrire ce script (28/08) : le JavaScript de Hektor qu'on a
// capture le 12/06 ne connait que trois modes -- createOffre, createCompromis,
// addOffre. Le module qui porte "accepter" et "refuser" se charge A LA DEMANDE, il
// n'est donc dans aucune de nos captures. Et l'API v2 ne sait que LIRE les
// transactions (Liste Compromis, Detail Vente) : aucune action.
//
// CE QUE CE SCRIPT FAIT, ET CE QU'IL NE FAIT PAS
// ----------------------------------------------
// Il demande a Hektor le formulaire d'une transaction EXISTANTE, avec init="1" --
// exactement l'appel que console_job_worker.js fait deja avant chaque enregistrement
// (submitHektorTransactionStatus). Il enregistre la reponse et en extrait les champs.
//
// Il n'envoie JAMAIS actionContainer[]=save ni actionContainer[]=treat : ce sont eux
// qui declenchent l'ecriture chez Hektor. Sans eux, ouvrir un formulaire ne modifie
// rien -- c'est ce que fait le navigateur quand on clique pour regarder une offre.
//
// DISCIPLINE DE DEBIT -- notre IP a deja ete bannie deux fois.
//   deux requetes, 1,5 s d'intervalle, et 403 = ARRET IMMEDIAT SANS RETENTER.
//
//   node Console/capture_transaction_actions.js
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN_URL = `${HEKTOR_BASE_URL}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const PAUSE_MS = 1500;

function argValue(name, fallback = "") {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? String(process.argv[i + 1] || "").trim() : fallback;
}

const storageStatePath = path.resolve(argValue(
  "--storage-state",
  process.env.CONSOLE_INSPECT_STORAGE_STATE_PATH || path.join(__dirname, "sessions", "storage_state_actions.json"),
));
const exportRoot = path.resolve(argValue(
  "--export-root",
  path.join(__dirname, "exports", `transaction_actions_${new Date().toISOString().replace(/[:.]/g, "-")}`),
));

// Cibles choisies sur nos donnees : une offre vivante, un compromis actif.
const CIBLES = [
  {
    nom: "offre",
    mode: "annonce-SuiviVente-offre-createOffre",
    annonce: argValue("--annonce-offre", "62774"),
    idChamp: "id_offre",
    id: argValue("--id-offre", "33026"),
  },
  {
    nom: "compromis",
    mode: "annonce-SuiviVente-compromis-createCompromis",
    annonce: argValue("--annonce-compromis", "53372"),
    idChamp: "idCompromis",
    id: argValue("--id-compromis", "50043"),
    initBasket: true,
  },
];

const dors = (ms) => new Promise((r) => setTimeout(r, ms));

// Ce qu'on cherche dans le HTML rendu : les commandes d'action et les champs caches.
function inspecter(html) {
  const texte = String(html || "");
  const trouve = (re) => Array.from(new Set((texte.match(re) || []))).slice(0, 40);
  return {
    champs: trouve(/name=["'][^"']+["']/g).map((s) => s.slice(6, -1)),
    identifiants: trouve(/id=["'][^"']*(?:offre|compromis|status|etat|refus|accept|annul)[^"']*["']/gi),
    appels: trouve(/(?:mode=|mode["']?\s*:\s*["'])([A-Za-z][A-Za-z0-9_-]{4,})/g),
    fonctions: trouve(/\b(?:onclick|onChange)=["'][^"']{0,90}["']/gi),
    motsCles: trouve(/\b[a-zA-Z_]*(?:refus|accept|annul|cancel)[a-zA-Z_]*\b/gi),
  };
}

(async () => {
  if (!fs.existsSync(storageStatePath)) {
    console.error(`Session absente : ${storageStatePath}`);
    process.exit(2);
  }
  fs.mkdirSync(exportRoot, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ storageState: storageStatePath });
  const page = await context.newPage();
  const resume = {};

  try {
    for (const cible of CIBLES) {
      const corps = {
        mode: cible.mode,
        idAnnonce: cible.annonce,
        init: "1",
        [cible.idChamp]: cible.id,
      };
      if (cible.initBasket) corps.initBasket = "true";

      console.log(`--- ${cible.nom} : annonce ${cible.annonce}, ${cible.idChamp}=${cible.id} ---`);
      const reponse = await page.request.post(XMLRPC_URL, {
        form: corps,
        headers: {
          Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(cible.annonce)}`,
          Accept: "application/json, text/javascript, */*; q=0.01",
        },
        timeout: 60000,
      });

      if (reponse.status() === 403) {
        console.error("403 -- signature de bannissement. ARRET, on ne retente pas.");
        process.exit(3);
      }
      const brut = await reponse.text();
      let html = brut;
      try {
        const j = JSON.parse(brut);
        html = String(j.html || (j.data && (j.data.defaultTemplate || j.data.html || j.data.template)) || brut);
      } catch (_) { /* deja du HTML */ }

      fs.writeFileSync(path.join(exportRoot, `${cible.nom}_brut.txt`), brut, "utf8");
      fs.writeFileSync(path.join(exportRoot, `${cible.nom}.html`), html, "utf8");
      resume[cible.nom] = { statut: reponse.status(), taille: html.length, ...inspecter(html) };
      console.log(`    HTTP ${reponse.status()}, ${html.length} caracteres`);

      await dors(PAUSE_MS);
    }
  } finally {
    await context.close();
    await browser.close();
  }

  fs.writeFileSync(path.join(exportRoot, "resume.json"), JSON.stringify(resume, null, 2), "utf8");
  console.log(`\nCapture dans ${exportRoot}`);
  for (const [nom, r] of Object.entries(resume)) {
    console.log(`\n=== ${nom} : ${r.taille} caracteres ===`);
    console.log(`   mots-cles action : ${(r.motsCles || []).join(", ") || "(aucun)"}`);
    console.log(`   modes cites      : ${(r.appels || []).join(", ") || "(aucun)"}`);
  }
})();
