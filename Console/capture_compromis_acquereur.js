// CAPTURE EN LECTURE SEULE -- comment Hektor ATTACHE UN ACQUEREUR a un compromis.
//
// POURQUOI CE SCRIPT EXISTE
// -------------------------
// 02/09/2026. L'app a cree le compromis 50059 sur l'annonce 24933. Tout est arrive
// chez Hektor -- prix, dates, sequestre, honoraires, mandat, mandants -- SAUF
// l'acquereur :
//
//     acquereurs : []      alors que buyer_contact_id = 605075 a bien ete envoye
//
// Et ce n'est pas une omission du worker : le releve complet des champs postes se
// termine par « ...,tauxHonoraireSortie,acquereurs[],idAnnonce ». Le champ PART.
// Hektor l'ignore.
//
// Contre-epreuve dans nos propres donnees : 50059 est le SEUL compromis sans
// acquereur -- 2 997 sur 3 000 en ont un. Ce n'est donc pas un comportement de
// Hektor, c'est notre facon de lui parler.
//
// CE QUE LE JAVASCRIPT DE HEKTOR MONTRE, ET OU IL S'ARRETE
// --------------------------------------------------------
// La capture du 12/06 contient l'APPELANT :
//
//     callPopinAcqId(data, 'addAcquereur', 'compromis', "2", "acquereurs[]", false)
//
// Un appel DEDIE, a l'etape 2. Mais sa DEFINITION n'est dans aucun de nos 30
// fichiers captures -- meme constat que le 28/08 pour accepter/refuser :
// « le module se charge A LA DEMANDE, il n'est donc dans aucune de nos captures ».
//
// L'HYPOTHESE, ET POURQUOI ELLE NE SUFFIT PAS
// -------------------------------------------
// L'assistant garde son etat dans un `basket` -- de l'etat PHP serialise que le
// worker recopie sans le lire. Les parties vivent probablement dedans, et
// callPopinAcqId serait ce qui les y inscrit, en renvoyant un panier a jour.
// Poster acquereurs[] dans le formulaire ne toucherait pas ce panier, et Hektor
// reconstruirait le module depuis LUI.
//
// C'est plausible. Ce n'est pas mesure. Et deviner un nom de champ est exclu :
// « un mauvais nom n'ecrit rien ET ne dit rien » -- lecon du 28/08.
//
// CE QUE CE SCRIPT FAIT, ET CE QU'IL NE FAIT PAS
// ----------------------------------------------
// Il ouvre un VRAI navigateur sur la fiche du bien, avec la session admin, et il
// ECOUTE. C'est VOUS qui faites le geste :
//
//     1. ouvrir l'assistant « Sous compromis »
//     2. taper le nom dans le champ acquereur
//     3. CLIQUER sur le resultat pour le selectionner   <- LE CLIC QU'ON VEUT VOIR
//     4. FERMER la popin, SANS ENREGISTRER
//
// Le script n'envoie AUCUNE requete de lui-meme. Il ne clique nulle part. Il ne
// sauvegarde rien. Il regarde.
//
// TROIS GARDE-FOUS
// ----------------
//   * LA SESSION N'EST JAMAIS REECRITE. Le script d'origine dont celui-ci
//     s'inspire fait context.storageState({ path }) en fin de course : il REECRIT
//     le fichier de session du worker. Ici on lit une COPIE jetable, et on ne rend
//     jamais rien. Quatre services partagent ces sessions.
//   * 403 = ARRET IMMEDIAT, sans retenter. Notre IP a deja ete bannie deux fois.
//   * Rien n'est poste par le script : le seul debit est celui de vos clics.
//
//   node Console/capture_compromis_acquereur.js 24933
const fs = require("fs");
const path = require("path");
const os = require("os");
const { chromium } = require("playwright");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const HEKTOR_BASE_URL = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const SESSION_SOURCE = process.env.CAPTURE_ACQ_SESSION
  || path.resolve(__dirname, "sessions", "storage_state_admin.json");
const ANNONCE_ID = (process.argv.slice(2).find((a) => !a.startsWith("--")) || "").trim();
const MAX_DURATION_MS = Number(process.env.CAPTURE_ACQ_MAX_MS || 15 * 60 * 1000);

const EXPORT_ROOT = path.resolve(__dirname, "exports",
  "capture_compromis_acquereur_" + (ANNONCE_ID || "unknown") + "_" +
  new Date().toISOString().replace(/[:.]/g, "-"));
const STOP_FILE = path.join(EXPORT_ROOT, "STOP_CAPTURE.txt");

function redactHeaders(headers) {
  const safe = {};
  for (const [k, v] of Object.entries(headers || {})) {
    safe[k] = /cookie|authorization|token|secret|password/i.test(k) ? "[redacted]" : v;
  }
  return safe;
}

// Ce qui nous interesse : la console (xmlrpc) et les routes de l'assistant.
function urlInteressante(url) {
  return url.includes("/admin/xmlrpc.php")
    || url.includes("/ws/GraphQL")
    || url.includes("getStepCompromis")
    || url.includes("getStepVente");
}

// Ce qui parle d'un ACQUEREUR, dans l'URL ou dans le corps poste.
function parleDAcquereur(url, postData) {
  const foin = String(url) + " " + String(postData || "");
  return /acquereur|addAcquereur|popinAcq|prospect/i.test(foin);
}

async function main() {
  if (!/^\d+$/.test(ANNONCE_ID)) {
    throw new Error("Usage: node Console/capture_compromis_acquereur.js <hektor_annonce_id>");
  }
  if (!fs.existsSync(SESSION_SOURCE)) {
    throw new Error("Session Hektor introuvable : " + SESSION_SOURCE);
  }
  fs.mkdirSync(EXPORT_ROOT, { recursive: true });

  // ─── LA COPIE, ET C'EST LE POINT IMPORTANT ───
  // On travaille sur une copie jetable. Le fichier que les quatre services
  // partagent n'est ni ouvert en ecriture, ni reecrit en fin de course.
  const sessionCopie = path.join(os.tmpdir(), "hektor_capture_acq_" + process.pid + ".json");
  fs.copyFileSync(SESSION_SOURCE, sessionCopie);

  const evenements = [];
  let banni = false;

  const browser = await chromium.launch({ headless: false, slowMo: 60 });
  const context = await browser.newContext({
    storageState: sessionCopie,
    viewport: { width: 1500, height: 980 },
  });
  const page = await context.newPage();

  page.on("request", (req) => {
    const url = req.url();
    if (!urlInteressante(url)) return;
    const postData = req.postData();
    evenements.push({
      at: new Date().toISOString(), sens: "requete", methode: req.method(), url,
      entetes: redactHeaders(req.headers()), corps: postData,
      parle_d_acquereur: parleDAcquereur(url, postData),
    });
  });

  page.on("response", async (rep) => {
    const url = rep.url();
    if (!urlInteressante(url)) return;
    if (rep.status() === 403) banni = true;
    let corps = "";
    try {
      const ct = rep.headers()["content-type"] || "";
      if (/json|text|html|javascript|x-www-form-urlencoded/i.test(ct)) corps = await rep.text();
    } catch (_) { corps = "[corps indisponible]"; }
    evenements.push({
      at: new Date().toISOString(), sens: "reponse", methode: rep.request().method(), url,
      statut: rep.status(), corps_apercu: corps.slice(0, 40000),
      parle_d_acquereur: parleDAcquereur(url, rep.request().postData()),
    });
  });

  const cible = HEKTOR_BASE_URL + "/admin/?page=/mes-biens/mon-bien&id=" + encodeURIComponent(ANNONCE_ID);
  console.log(JSON.stringify({
    statut: "capture_demarree",
    annonce: ANNONCE_ID,
    cible: cible,
    export: EXPORT_ROOT,
    session_lue: SESSION_SOURCE,
    session_jamais_reecrite: true,
    a_faire: [
      "1. ouvrir l'assistant « Sous compromis »",
      "2. taper le nom de l'acquereur dans son champ",
      "3. CLIQUER sur le resultat pour le selectionner",
      "4. FERMER la popin SANS ENREGISTRER",
      "5. fermer la fenetre du navigateur pour arreter la capture",
    ],
  }, null, 2));

  await page.goto(cible, { waitUntil: "domcontentloaded", timeout: 60000 });

  const depart = Date.now();
  let fermee = false;
  page.on("close", () => { fermee = true; });
  while (!fs.existsSync(STOP_FILE) && !fermee && !banni && Date.now() - depart < MAX_DURATION_MS) {
    await new Promise((r) => setTimeout(r, 1000));
  }
  if (banni) console.error("403 RENCONTRE -- arret immediat, on ne retente pas.");

  fs.writeFileSync(path.join(EXPORT_ROOT, "network_events.json"),
    JSON.stringify(evenements, null, 2), "utf-8");
  const distillat = evenements.filter((e) => e.parle_d_acquereur);
  fs.writeFileSync(path.join(EXPORT_ROOT, "appels_acquereur.json"),
    JSON.stringify(distillat, null, 2), "utf-8");

  await browser.close().catch(() => {});
  try { fs.unlinkSync(sessionCopie); } catch (_) {}

  console.log(JSON.stringify({
    statut: banni ? "arret_403" : "capture_enregistree",
    export: EXPORT_ROOT,
    evenements: evenements.length,
    appels_parlant_d_acquereur: distillat.length,
  }, null, 2));
}

main().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
