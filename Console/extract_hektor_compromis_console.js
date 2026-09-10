/**
 * LE RATTRAPAGE — CE QUE L'API NE REND PAS SUR UN COMPROMIS       10/09/2026
 * ═════════════════════════════════════════════════════════════════════════
 *
 * ⚠ CE SCRIPT N'ÉCRIT JAMAIS CHEZ HEKTOR, et ce n'est pas une intention,
 *   c'est une construction : il n'envoie QUE l'ouverture de l'assistant.
 *   L'enregistrement, chez Hektor, est la requête qui porte
 *       actionContainer[] = save  +  treat
 *   et ces deux mots n'apparaissent nulle part ici. La tâche 0.3 l'a
 *   d'ailleurs mesuré en contre-témoin : « ouvrir/fermer sans enregistrer
 *   -> AUCUN mouvement » de la date du bien.
 *
 * CE QU'IL RAMÈNE, par compromis, en UNE ouverture :
 *     notairesAcquereur[] · notairesMandant[]     absents de l'API (0/10 586)
 *     acquereurs[] · mandants[]                    à comparer avec l'API
 *     montantHonoraireEntree · tauxHonoraireEntree le TAUX VENDEUR
 *
 * ⚠ LES UNITÉS DE COMMISSION ET LES CONDITIONS NE SONT PAS ICI, et c'est
 *   délibéré. Elles vivent aux étapes 2 et 3, qu'il faudrait parcourir en
 *   postant chaque transition — trois fois plus de requêtes sur 10 586
 *   compromis. Le worker les rapporte déjà pour tout ce que l'app touche.
 *   Pour l'historique, ce sera une passe séparée, si elle se justifie.
 *
 * LA CADENCE est celle du run chauffage, la seule éprouvée ici : 56 926
 * lectures sans un seul bannissement. Le rattrapage des documents, lui, a
 * fait bannir notre IP par le débit — on ne s'en écarte pas.
 *
 * LE LECTEUR N'EST PAS RECOPIÉ : il est pris dans console_job_worker.js
 * (voir lecture_assistant.js). Une copie divergerait sans prévenir.
 *
 *   node Console/extract_hektor_compromis_console.js --cible 24933:50078
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");
const { chargerLecteur } = require("./lecture_assistant");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = (process.env.HEKTOR_BASE_URL
  || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN_URL = `${HEKTOR_BASE_URL}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;

// Les mêmes verbes que le worker. La coquille met Hektor dans l'état où le
// navigateur le met ; l'ouverture rend le formulaire de l'étape 0.
const COQUILLE = "annonce-SuiviVente-compromis-createCompromis";
const ETAPE = "annonce-SuiviVente-compromis-getStepCompromis";
// ⚠ LA COQUILLE N'EST PAS NECESSAIRE POUR LIRE -- MESURE LE 10/09.
//   Le worker l'envoie avant d'ECRIRE, et on ne touche pas a son chemin. Mais
//   pour une simple lecture, l'ouverture suffit : essai sur le compromis 23512
//   (annonce 225), JAMAIS ouvert auparavant, sans coquille --
//       44 984 caracteres rendus, notaire acquereur 129941, notaire mandant
//       85038, honoraires 6 000,00 -- soit exactement le meme formulaire.
//   Le premier essai (sur 50078) ne prouvait rien : une coquille venait d'etre
//   envoyee juste avant, l'etat serveur pouvait persister. C'est le second, sur
//   un compromis vierge, qui tranche.
//
// ➡ CELA DIVISE LE FLUX PAR DEUX, et c'est ce qui remet ce rattrapage dans la
//   methode de reference du projet : UNE requete par element, comme le run
//   chauffage. Deux requetes par element, c'etait exactement le profil qui a
//   fait bannir notre IP en juillet (« ~3 requetes par annonce a 1,3 s »).
const AVEC_COQUILLE = process.argv.includes("--avec-coquille");

function argValues(nom) {
  const out = [];
  for (let i = 0; i < process.argv.length; i += 1) {
    if (process.argv[i] === nom && i + 1 < process.argv.length) {
      out.push(String(process.argv[i + 1] || "").trim());
    }
  }
  return out.filter(Boolean);
}

function argValue(nom, defaut = "") {
  const v = argValues(nom);
  return v.length ? v[v.length - 1] : defaut;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, Math.max(0, ms)));
}

function cibles() {
  // « annonce:compromis », répétable ou séparé par des virgules.
  const brut = [...argValues("--cible"), ...argValues("--cibles").flatMap((v) => v.split(","))];
  const out = [];
  for (const c of brut) {
    const m = String(c).trim().match(/^(\d+):(\d+)$/);
    if (m) out.push({ annonce: m[1], compromis: m[2] });
  }
  return out;
}

function browserLaunchOptions() {
  const executablePath = [
    process.env.CONSOLE_CHROME_EXE,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].find((c) => c && fs.existsSync(c)) || "";
  return { headless: true, ...(executablePath ? { executablePath } : {}) };
}

function ressembleAuLogin(texte) {
  const html = String(texte || "").toLowerCase();
  return html.includes('name="login"') || html.includes("mot de passe")
    || html.includes("/admin/login");
}

/** La réponse d'étape : { success, data: { stepContent, basket } }. */
function contenuDeLEtape(texte) {
  try {
    const j = JSON.parse(String(texte || ""));
    const d = (j && j.data) || {};
    return typeof d.stepContent === "string" ? d.stepContent : "";
  } catch (_) {
    return "";
  }
}

async function poster(page, url, corps, referer) {
  return page.evaluate(async ({ url, corps, referer }) => {
    const r = await fetch(url, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        Accept: "application/json, text/javascript, */*; q=0.01",
        Referer: referer,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: corps,
    });
    return { status: r.status, text: await r.text() };
  }, { url, corps, referer });
}

async function lireUnCompromis(page, lire, cible) {
  const debut = Date.now();
  const referer = `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(cible.annonce)}`;
  const base = {
    hektor_annonce_id: cible.annonce,
    hektor_compromis_id: cible.compromis,
    lu_le: new Date().toISOString(),
  };

  // 1. la coquille — écartée par défaut, voir la note en tête de fichier.
  //    `--avec-coquille` la remet, si Hektor changeait d'avis un jour.
  if (AVEC_COQUILLE) await page.evaluate(async ({ url, referer }) => {
    await fetch(url, {
      credentials: "include",
      headers: { Accept: "application/json, text/javascript, */*; q=0.01", Referer: referer },
    });
  }, { url: `${XMLRPC_URL}?mode=${encodeURIComponent(COQUILLE)}`, referer });

  // 2. l'ouverture SUR CE COMPROMIS. C'est `idCompromis` qui fait la
  //    différence entre « créer » et « reprendre » — le JavaScript de Hektor
  //    fait exactement cela : popinPostInner({ idCompromis, initBasket: true }).
  // ⚠ PAS DE `mode` DANS LE CORPS. Le worker ne le met pas -- le mode voyage
  //   dans l'URL, et seulement la. L'y ajouter fait rendre a Hektor une reponse
  //   sans `stepContent` (mesure du 10/09, premier essai : « aucun contenu
  //   d'etape rendu »). On recopie le worker, on n'improvise pas.
  const corps = new URLSearchParams();
  corps.set("idAnnonce", cible.annonce);
  corps.set("idCompromis", cible.compromis);
  corps.set("basket", "");
  corps.set("initBasket", "true");

  const rep = await poster(page, `${XMLRPC_URL}?mode=${encodeURIComponent(ETAPE)}`,
    corps.toString(), referer);

  if (rep.status === 403) {
    return { ...base, status: "stopped_on_403", error: "Hektor 403 sur l'ouverture" };
  }
  if (rep.status >= 400) {
    return { ...base, status: "error", error: `HTTP ${rep.status}` };
  }
  if (ressembleAuLogin(rep.text)) {
    return { ...base, status: "session_expired", error: "session Hektor expiree" };
  }
  const html = contenuDeLEtape(rep.text);
  if (!html) {
    // ON GARDE CE QUE HEKTOR A REPONDU. Sans cela, « aucun contenu » est
    // indechiffrable -- lecon du 30/08, deja payee sur ce meme chemin.
    return { ...base, status: "error", error: "aucun contenu d'etape rendu",
             reponse_taille: String(rep.text || "").length,
             reponse: String(rep.text || "").slice(0, 300) };
  }
  return {
    ...base,
    status: "done",
    html_octets: html.length,
    elapsed_ms: Date.now() - debut,
    champs: lire([html]),
  };
}

async function main() {
  const liste = cibles();
  if (!liste.length) throw new Error("Aucune --cible <annonce>:<compromis> fournie");

  const storageStatePath = path.resolve(argValue(
    "--storage-state",
    process.env.CONSOLE_INSPECT_STORAGE_STATE_PATH
      || path.join(__dirname, "sessions", "storage_state_admin.json")));
  if (!fs.existsSync(storageStatePath)) {
    throw new Error(`Session Playwright introuvable: ${storageStatePath}`);
  }
  const delayMs = Number(argValue("--delay-ms", "500")) || 0;
  const timeoutMs = Number(argValue("--timeout-ms", "60000")) || 60000;

  const lire = chargerLecteur();
  const debut = Date.now();
  const browser = await chromium.launch(browserLaunchOptions());
  const context = await browser.newContext({ storageState: storageStatePath });
  const page = await context.newPage();
  page.setDefaultTimeout(timeoutMs);

  const resultats = [];
  try {
    await page.goto(ADMIN_URL, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    for (let i = 0; i < liste.length; i += 1) {
      const r = await lireUnCompromis(page, lire, liste[i]);
      resultats.push(r);
      // ⚠ ARRÊT DUR au premier 403 ou à la session perdue. On ne « réessaie
      //   pour voir » pas : c'est ce qui a fait bannir notre IP en juillet.
      if (r.status === "stopped_on_403" || r.status === "session_expired") {
        console.log(JSON.stringify({ status: r.status, resultats,
          elapsed_ms: Date.now() - debut }));
        process.exitCode = r.status === "stopped_on_403" ? 3 : 2;
        return;
      }
      if (i < liste.length - 1 && delayMs > 0) await sleep(delayMs);
    }
  } finally {
    await browser.close();
  }

  console.log(JSON.stringify({
    status: resultats.some((r) => r.status === "error") ? "partial" : "done",
    resultats,
    elapsed_ms: Date.now() - debut,
  }));
}

main().catch((e) => {
  console.log(JSON.stringify({
    status: "error",
    error: e && e.message ? e.message : String(e),
    lu_le: new Date().toISOString(),
  }));
  process.exitCode = 1;
});
