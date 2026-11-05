// essai_youtrust_correction_signataire.js -- A.2, décision D30 (05/11/2026) : peut-on CORRIGER un
// signataire APRÈS l'envoi ? Essai en SANDBOX Youtrust, avant de prévoir le bouton « corriger l'e-mail ».
//
// La doc Youtrust dit que PATCH /signers/{id} change les « info » d'un signataire, mais n'est pas claire
// sur l'e-mail une fois la demande activée. Trois mesures, dans l'ordre :
//   1. après l'activation, changer le PRÉNOM seul (même e-mail)           -> accepté ou refusé ?
//   2. changer l'E-MAIL vers un alias de la même boîte (+essai-a2)         -> accepté ou refusé ?
//   3. relire le signataire : quel statut, quelle adresse, quel lien de signature ?
// puis la demande est ANNULÉE (sauf --garder), pour ne rien laisser traîner.
//
//   node essai_youtrust_correction_signataire.js --sortie=<dossier>
//
// Garde-fous : SANDBOX seulement (refus si l'adresse de base n'est pas la sandbox) ; e-mails vers la
// boîte de Frédéric seulement — l'alias « +essai-a2 » arrive dans la MÊME boîte (mémoire
// test-signature-email-contrainte) ; code par e-mail, jamais de SMS ; aucune écriture en base, aucun
// appel à Hektor. La clé n'est jamais affichée.

const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, ".env") });
const { chromium } = require("playwright");
const { creerClientYoutrust, SANDBOX_URL, YoutrustError } = require("./youtrust_client");

const SIGNATAIRE_AUTORISE = "frederic.gerphagnon@gti-immobilier.fr";
const ALIAS_MEME_BOITE = "frederic.gerphagnon+essai-a2@gti-immobilier.fr";

function arg(nom) {
  const a = process.argv.find((x) => x === `--${nom}` || x.startsWith(`--${nom}=`));
  if (!a) return null;
  return a.includes("=") ? a.slice(a.indexOf("=") + 1) : true;
}

// Même recherche d'exécutable que essai_youtrust_sandbox.js.
function optionsChromium() {
  const executablePath = [
    process.env.CONSOLE_CHROME_EXE,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].find((c) => c && fs.existsSync(c)) || "";
  return { headless: true, ...(executablePath ? { executablePath } : {}) };
}

// Un mandat FICTIF à une seule case, ancre {{s1|signature|150|45}} (lot 1, prouvé le 26/10).
function mandatFictifHtml() {
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
    body{font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#222}
    .case{border:1.5px dashed #9aa;height:66px;width:260px;position:relative;background:#fafbfc;margin-top:20px}
    .yt-ancre{position:absolute;left:4px;top:4px;color:#fafbfc;font-family:Arial;font-size:10px;white-space:nowrap}
  </style></head><body>
    <h1>ESSAI SANDBOX A.2 — CORRECTION D'UN SIGNATAIRE (DOCUMENT FICTIF)</h1>
    <p>Document d'essai sans valeur. Aucune donnée réelle.</p>
    <div class="case"><span class="yt-ancre">{{s1|signature|150|45}}</span></div>
  </body></html>`;
}

async function rendrePdf(html) {
  const browser = await chromium.launch(optionsChromium());
  try {
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle", timeout: 30000 });
    return await page.pdf({ format: "A4", printBackground: true });
  } finally {
    await browser.close().catch(() => {});
  }
}

// Résumé d'un signataire relu : rien de secret, de quoi comparer avant / après.
function resume(s) {
  if (!s) return null;
  return {
    status: s.status,
    first_name: s.info && s.info.first_name,
    email: s.info && s.info.email,
    lien_present: Boolean(s.signature_link),
    lien_empreinte: s.signature_link ? require("crypto").createHash("sha1").update(String(s.signature_link)).digest("hex").slice(0, 10) : null,
    authentication: s.signature_authentication_mode,
  };
}

// Un appel qui peut être refusé : on garde le refus comme RÉSULTAT, pas comme panne.
async function tenter(etape, fn) {
  try {
    const r = await fn();
    return { etape, accepte: true, reponse: r };
  } catch (e) {
    if (e instanceof YoutrustError) return { etape, accepte: false, http: e.status, corps: e.body };
    throw e;
  }
}

(async () => {
  const sortie = arg("sortie");
  if (!sortie || sortie === true) throw new Error("préciser --sortie=<dossier>");
  fs.mkdirSync(sortie, { recursive: true });
  const client = creerClientYoutrust();
  if (!client.sandbox || client.baseUrl !== SANDBOX_URL) throw new Error("refus : cet essai ne tourne qu'en SANDBOX");

  const etat = { debut: new Date().toISOString(), mesures: [] };
  const ecrire = () => fs.writeFileSync(path.join(sortie, "etat.json"), JSON.stringify(etat, null, 2));

  const pdf = await rendrePdf(mandatFictifHtml());
  const demande = await client.creerDemande({
    name: "ESSAI A.2 sandbox - correction d'un signataire apres l'envoi (D30)",
    delivery_mode: "email",
    timezone: "Europe/Paris",
    audit_trail_locale: "fr",
    signers_allowed_to_decline: false,
    external_id: `essai-a2-d30-${Date.now()}`,
  });
  etat.demande_id = demande.id;
  ecrire();
  const doc = await client.ajouterDocument(demande.id, { buffer: pdf, filename: "essai_d30.pdf", parseAnchors: true });
  etat.ancres = doc.total_anchors;
  const signataire = await client.ajouterSignataire(demande.id, {
    info: { first_name: "Frederic (avant)", last_name: "Gerphagnon", email: SIGNATAIRE_AUTORISE, locale: "fr" },
    signature_level: "electronic_signature",
    signature_authentication_mode: "otp_email",
  });
  etat.signataire_id = signataire.id;
  ecrire();
  const active = await client.activer(demande.id);
  etat.statut_demande_apres_activation = active.status;
  etat.signataire_avant = resume(await client.lireSignataire(demande.id, signataire.id));
  // --attendre-notifie : le vrai cas est la correction APRÈS l'envoi de l'invitation (statut « notified »),
  // pas pendant les secondes où le signataire est encore « initiated ». On relit toutes les 5 s, 120 s au plus.
  if (arg("attendre-notifie")) {
    for (let i = 0; i < 24 && etat.signataire_avant.status === "initiated"; i += 1) {
      await new Promise((r) => setTimeout(r, 5000));
      etat.signataire_avant = resume(await client.lireSignataire(demande.id, signataire.id));
    }
    etat.attente_notifie = etat.signataire_avant.status;
  }
  ecrire();
  console.log(`Demande ${demande.id} activée (${active.status}) ; signataire : ${JSON.stringify(etat.signataire_avant)}`);

  const chemin = `/signature_requests/${demande.id}/signers/${signataire.id}`;
  // 1. le prénom seul
  const m1 = await tenter("1. prenom seul apres activation", () => client.requete("PATCH", chemin, {
    json: { info: { first_name: "Frederic (corrige)", last_name: "Gerphagnon", email: SIGNATAIRE_AUTORISE, locale: "fr" } },
  }));
  m1.signataire_apres = resume(await client.lireSignataire(demande.id, signataire.id));
  etat.mesures.push({ ...m1, reponse: m1.accepte ? resume(m1.reponse) : undefined });
  ecrire();
  console.log(`${m1.etape} : ${m1.accepte ? "ACCEPTE" : `REFUSE (HTTP ${m1.http}) ${JSON.stringify(m1.corps)}`} -> ${JSON.stringify(m1.signataire_apres)}`);

  // 2. l'e-mail, vers un alias de la même boîte
  const m2 = await tenter("2. e-mail apres activation (alias de la meme boite)", () => client.requete("PATCH", chemin, {
    json: { info: { first_name: "Frederic (corrige)", last_name: "Gerphagnon", email: ALIAS_MEME_BOITE, locale: "fr" } },
  }));
  m2.signataire_apres = resume(await client.lireSignataire(demande.id, signataire.id));
  etat.mesures.push({ ...m2, reponse: m2.accepte ? resume(m2.reponse) : undefined });
  ecrire();
  console.log(`${m2.etape} : ${m2.accepte ? "ACCEPTE" : `REFUSE (HTTP ${m2.http}) ${JSON.stringify(m2.corps)}`} -> ${JSON.stringify(m2.signataire_apres)}`);

  // --relancer : 05/11, après la 1re mesure, Youtrust n'a PAS renvoyé l'invitation à la nouvelle adresse
  // (seule l'invitation de départ est arrivée, au nom « avant »). On mesure la relance : part-elle vers la NOUVELLE ?
  if (arg("relancer") && m2.accepte) {
    const m3 = await tenter("3. relance apres correction de l'e-mail", () => client.relancerSignataire(demande.id, signataire.id));
    etat.mesures.push({ etape: m3.etape, accepte: m3.accepte, http: m3.http, corps: m3.corps, a: new Date().toISOString() });
    ecrire();
    console.log(`${m3.etape} : ${m3.accepte ? "ACCEPTE" : `REFUSE (HTTP ${m3.http}) ${JSON.stringify(m3.corps)}`}`);
    // On laisse quelques secondes à l'envoi avant d'annuler (l'annulation envoie son propre e-mail).
    await new Promise((r) => setTimeout(r, 20000));
  }

  const relue = await client.lireDemande(demande.id);
  etat.statut_demande_avant_annulation = relue.status;
  if (!arg("garder")) {
    const annulee = await client.annuler(demande.id, "other", "Essai A.2 D30 : correction d'un signataire");
    etat.statut_final = annulee.status;
  }
  etat.fin = new Date().toISOString();
  ecrire();
  console.log(`Demande : ${relue.status} -> ${etat.statut_final || "gardée (--garder)"}`);
})().catch((e) => {
  console.error(`ECHEC : ${e && e.message}${e && e.body ? ` ${JSON.stringify(e.body)}` : ""}`);
  process.exit(1);
});
