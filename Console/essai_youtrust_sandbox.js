// essai_youtrust_sandbox.js -- LOT 1 de A.2 : essai de bout en bout en SANDBOX Youtrust.
//
// Leve les deux doutes de l'audit (notice/AUDIT_SIGNATURE_YOUTRUST_2026-10-26.md §3.4) :
//   1. Youtrust accepte-t-il un PDF 1.4 sorti de Chromium, comme nos mandats ?
//   2. Reconnait-il les ancres {{sN|signature|l|h}} posees dans les cases de signature ?
//
// Deux temps :
//   node essai_youtrust_sandbox.js --envoyer --sortie=<dossier>
//       fabrique un mandat FICTIF (memes classes CSS que mandatSignatureBlocksHtml), l'envoie
//       avec UN signataire (Frederic, code par e-mail), active, ecrit <dossier>/etat.json
//   node essai_youtrust_sandbox.js --suivre --sortie=<dossier>
//       relit la demande ; si elle est « done », telecharge le PDF signe + l'audit trail
//
// Garde-fous : SANDBOX seulement ; signataire = la boite de Frederic seulement (memoire
// test-signature-email-contrainte) ; aucune ecriture en base, aucun appel a Hektor.

const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, ".env") });
const { chromium } = require("playwright");
const { creerClientYoutrust, SANDBOX_URL, YoutrustError } = require("./youtrust_client");

const SIGNATAIRE_AUTORISE = "frederic.gerphagnon@gti-immobilier.fr";

function arg(nom) {
  const a = process.argv.find((x) => x === `--${nom}` || x.startsWith(`--${nom}=`));
  if (!a) return null;
  return a.includes("=") ? a.slice(a.indexOf("=") + 1) : true;
}

// Meme recherche d'executable que browserLaunchOptions du worker (console_job_worker.js).
function optionsChromium() {
  const executablePath = [
    process.env.CONSOLE_CHROME_EXE,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].find((c) => c && fs.existsSync(c)) || "";
  return { headless: true, ...(executablePath ? { executablePath } : {}) };
}

// Ancre Youtrust : une ligne, Arial 10 px, de la couleur du fond de la case (#fafbfc).
function ancre(indexSignataire) {
  return `<span class="yt-ancre">{{s${indexSignataire}|signature|150|45}}</span>`;
}

function mandatFictifHtml() {
  const box = (titre, nom, idx) => `<div class="mandat-signature-box">
      <div class="mandat-signature-title">${titre}</div>
      <div class="mandat-signature-name">${nom}</div>
      <div class="mandat-signature-area">${ancre(idx)}<span>signature</span></div>
    </div>`;
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
    body{font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#222}
    h1{font-size:16px;color:#c2185b}
    .mandat-signatures-page{page-break-before:always}
    .mandat-signatures-heading{font-size:13px;font-weight:800;margin-bottom:8px;text-transform:uppercase}
    .mandat-signatures-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .mandat-signature-box{border:1px solid #d8d8d8;padding:6px;break-inside:avoid;page-break-inside:avoid;border-radius:4px}
    .mandat-signature-title{border-bottom:2px solid #c2185b;font-size:8.7px;font-weight:800;margin-bottom:4px;padding-bottom:3px;text-align:center;text-transform:uppercase}
    .mandat-signature-name{font-size:8.9px;font-weight:800;margin-bottom:3px;min-height:10px;text-align:center}
    .mandat-signature-area{border:1.5px dashed #9aa;height:66px;position:relative;border-radius:3px;background:#fafbfc}
    .mandat-signature-area span{position:absolute;right:6px;bottom:4px;color:#aaa;font-size:7px;letter-spacing:.05em;text-transform:uppercase}
    .mandat-signature-area .yt-ancre{left:4px;top:4px;right:auto;bottom:auto;color:#fafbfc;font-family:Arial;font-size:10px;letter-spacing:0;text-transform:none;white-space:nowrap}
    @page{size:A4;margin:10mm}
  </style></head><body>
    <h1>MANDAT DE VENTE — ESSAI SANDBOX (DOCUMENT FICTIF)</h1>
    <p>Document d'essai de la tâche A.2, sans valeur. Mandant fictif : Jean ESSAI, 1 rue de l'Essai, 42000 Saint-Étienne.</p>
    <p>Bien fictif : maison de 100 m², prix demandé 100 000 €. Aucune donnée réelle.</p>
    <div class="mandat-signatures-page">
      <div class="mandat-signatures-heading">Signatures</div>
      <div class="mandat-signatures-grid">
        ${box("Mandant 1", "Jean ESSAI", 1)}
        ${box("Mandataire", "Groupe GTI", 2)}
      </div>
    </div>
  </body></html>`;
}

async function rendrePdf(html) {
  const browser = await chromium.launch(optionsChromium());
  try {
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle", timeout: 30000 });
    return await page.pdf({ format: "A4", printBackground: true,
      margin: { top: "12mm", bottom: "12mm", left: "12mm", right: "12mm" } });
  } finally {
    await browser.close().catch(() => {});
  }
}

function lireEtat(sortie) {
  return JSON.parse(fs.readFileSync(path.join(sortie, "etat.json"), "utf8"));
}

function ecrireEtat(sortie, etat) {
  fs.writeFileSync(path.join(sortie, "etat.json"), JSON.stringify(etat, null, 2));
}

async function envoyer(client, sortie) {
  const pdf = await rendrePdf(mandatFictifHtml());
  const fichierPdf = path.join(sortie, "mandat_fictif.pdf");
  fs.writeFileSync(fichierPdf, pdf);
  const enTete = pdf.subarray(0, 8).toString("latin1");
  console.log(`PDF fabrique : ${pdf.length} octets, en-tete ${enTete}`);

  // --deux-signataires : la case « Mandataire » (ancre s2) est remplie aussi, par la meme boite
  // (Youtrust accepte la meme adresse deux fois, verifie le 26/10), DANS L'ORDRE mandant puis mandataire.
  const deux = Boolean(arg("deux-signataires"));
  const demande = await client.creerDemande({
    name: deux ? "ESSAI A.2 sandbox - mandat fictif, 2 signataires" : "ESSAI A.2 sandbox - mandat fictif",
    delivery_mode: "email",
    ordered_signers: deux,
    timezone: "Europe/Paris",
    audit_trail_locale: "fr",
    signers_allowed_to_decline: false,
    external_id: `essai-a2-${Date.now()}`,
  });
  console.log(`Demande creee : ${demande.id} (${demande.status})`);
  const etat = { demande_id: demande.id, cree_le: new Date().toISOString(), en_tete_pdf: enTete };
  ecrireEtat(sortie, etat);

  const doc = await client.ajouterDocument(demande.id, {
    buffer: pdf, filename: "mandat_fictif.pdf", parseAnchors: true,
  });
  etat.document_id = doc.id;
  etat.total_anchors = doc.total_anchors;
  ecrireEtat(sortie, etat);
  console.log(`Document accepte : ${doc.id}, pages ${doc.total_pages}, ancres detectees ${doc.total_anchors}`);

  // L'ordre de creation DOIT suivre l'ordre des ancres : 1er cree = s1 (mandant), 2e = s2 (mandataire).
  const roles = deux ? ["Mandant", "Mandataire"] : ["Mandant"];
  etat.signataires = [];
  for (const role of roles) {
    const signataire = await client.ajouterSignataire(demande.id, {
      info: { first_name: `Frederic (${role})`, last_name: "Gerphagnon", email: SIGNATAIRE_AUTORISE, locale: "fr" },
      signature_level: "electronic_signature",
      signature_authentication_mode: "otp_email",
    });
    etat.signataires.push({ role, id: signataire.id });
    ecrireEtat(sortie, etat);
    console.log(`Signataire ajoute (${role}) : ${signataire.id}`);
  }

  const active = await client.activer(demande.id);
  etat.statut_apres_activation = active.status;
  const champs = await client.listerChamps(demande.id, doc.id);
  const liste = Array.isArray(champs) ? champs : (champs && champs.data) || [];
  etat.champs = liste.map((c) => ({ type: c.type, page: c.page, x: c.x, y: c.y,
    width: c.width, height: c.height, signer_id: c.signer_id }));
  ecrireEtat(sortie, etat);
  console.log(`Activee : statut ${active.status}`);
  console.log(`Champs crees par les ancres : ${JSON.stringify(etat.champs)}`);
  console.log("-> L'e-mail d'invitation part vers la boite de Frederic.");
}

async function suivre(client, sortie) {
  const etat = lireEtat(sortie);
  const demande = await client.lireDemande(etat.demande_id);
  const sig = (demande.signers || []).map((s) => `${s.id}:${s.status}`).join(", ");
  console.log(`Demande ${demande.id} : ${demande.status} · signataires ${sig}`);
  etat.dernier_statut = demande.status;
  etat.suivi_le = new Date().toISOString();
  if (demande.status !== "done") {
    ecrireEtat(sortie, etat);
    console.log("Pas encore signee : relancer --suivre apres la signature.");
    return;
  }
  const signe = await client.telechargerDocuments(etat.demande_id, "completed");
  fs.writeFileSync(path.join(sortie, "mandat_fictif_signe.pdf"), signe.buffer);
  etat.signe = { octets: signe.buffer.length, type: signe.contentType,
    en_tete: signe.buffer.subarray(0, 8).toString("latin1") };
  console.log(`PDF signe : ${etat.signe.octets} octets, ${etat.signe.type}, ${etat.signe.en_tete}`);
  // un audit trail PAR signataire (l'ancien etat.json n'a que signataire_id)
  const signataires = etat.signataires || [{ role: "Mandant", id: etat.signataire_id }];
  etat.audit_trails = [];
  for (const s of signataires) {
    const audit = await client.telechargerAuditTrail(etat.demande_id, s.id);
    const nom = `audit_trail_${s.role.toLowerCase()}.pdf`;
    fs.writeFileSync(path.join(sortie, nom), audit.buffer);
    etat.audit_trails.push({ role: s.role, fichier: nom, octets: audit.buffer.length, type: audit.contentType });
    console.log(`Audit trail ${s.role} : ${audit.buffer.length} octets, ${audit.contentType}`);
  }
  ecrireEtat(sortie, etat);
}

async function main() {
  const sortie = arg("sortie");
  if (!sortie || sortie === true) throw new Error("--sortie=<dossier> obligatoire");
  fs.mkdirSync(sortie, { recursive: true });
  const client = creerClientYoutrust();
  if (client.baseUrl !== SANDBOX_URL) throw new Error(`refus : cet essai ne tourne qu'en sandbox (${client.baseUrl})`);
  if (arg("envoyer")) return envoyer(client, sortie);
  if (arg("suivre")) return suivre(client, sortie);
  throw new Error("preciser --envoyer ou --suivre");
}

main().catch((e) => {
  console.error(e instanceof YoutrustError
    ? `${e.message}\n${JSON.stringify(e.body, null, 2)}`
    : (e && e.stack) || e);
  process.exit(1);
});
