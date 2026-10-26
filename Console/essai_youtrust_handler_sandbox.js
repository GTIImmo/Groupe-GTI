// A.2 LOT 4 -- essai des VRAIS handlers Youtrust du worker, en SANDBOX, contre une FAUSSE base.
// Le bloc « A.2 -- SIGNATURE YOUTRUST, LOT 4 » est decoupe dans console_job_worker.js et monte
// avec des doublures : base en memoire (l'interrupteur y est « on » -- la VRAIE base n'est jamais
// lue ni ecrite), coffre = un PDF local, negociateur = la boite de Frederic. Youtrust = la vraie
// sandbox (boite de Frederic uniquement, code par e-mail : aucun SMS).
//     node essai_youtrust_handler_sandbox.js --pdf=<mandat a 2 mandants avec reperes>
// Scenes : 1 envoi · 2 rejeu sans double envoi · 3 relance · 4 lien du negociateur avant son tour
//          · 5 annulation · 6 PDF a 2 mandants envoye avec 1 seul -> refuse AVANT activation.
const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, ".env") });
const { SANDBOX_URL } = require("./youtrust_client");

const BOITE = "frederic.gerphagnon@gti-immobilier.fr";
const arg = (n) => { const a = process.argv.find((x) => x.startsWith(`--${n}=`)); return a ? a.slice(n.length + 3) : null; };
const pdfChemin = arg("pdf");
const N = Number(arg("mandants") || 2);   // mandants dans le PDF (5 signataires max pendant l'essai)
if (!pdfChemin) { console.error("--pdf=<fichier> requis"); process.exit(2); }
if ((process.env.YOUTRUST_BASE_URL || SANDBOX_URL) !== SANDBOX_URL) { console.error("refus : sandbox seulement"); process.exit(2); }

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const debut = src.indexOf("// A.2 -- SIGNATURE YOUTRUST, LOT 4");
const fin = src.indexOf("async function handleSyncConsoleDocuments(");
if (debut < 0 || fin < 0) { console.error("bloc du lot 4 introuvable"); process.exit(2); }
const bloc = src.slice(src.lastIndexOf("// ═", debut), fin);
const tranche = (d) => { const i = src.indexOf(d); return src.slice(i, src.indexOf("\n}", i) + 2); };

// ── la fausse base ─────────────────────────────────────────────────────────────────
const base = {
  setting: "on",
  documents: new Map(),
  demandes: [],
  journal: [],
};
const DOC = "dddddddd-0000-4000-8000-000000000001";
base.documents.set(DOC, { id: DOC, app_dossier_id: 9000001, hektor_annonce_id: "70001", document_name: "Mandat de vente - 18999", storage_path: "annonces/70001/documents/x/Mandat.pdf", metadata_json: { signature: { status: "to_send", hektor_doc_id: "D1" } } });
async function supabaseRequest(chemin, options = {}) {
  const m = options.method || "GET";
  base.journal.push(`${m} ${chemin.split("?")[0]}`);
  if (chemin.startsWith("app_setting")) return [{ value: base.setting }];
  if (chemin.startsWith("app_console_document")) {
    const id = decodeURIComponent((chemin.match(/id=eq\.([^&]+)/) || [])[1] || "");
    const d = base.documents.get(id);
    if (m === "GET") return d ? [JSON.parse(JSON.stringify(d))] : [];
    if (m === "PATCH") { Object.assign(d, JSON.parse(options.body)); return null; }
  }
  if (chemin.startsWith("app_signature_request")) {
    if (m === "POST") { const row = { id: `req-${base.demandes.length + 1}`, created_at: new Date().toISOString(), ...JSON.parse(options.body) }; base.demandes.push(row); return [row]; }
    if (m === "PATCH") { const id = decodeURIComponent(chemin.match(/id=eq\.([^&]+)/)[1]); Object.assign(base.demandes.find((r) => r.id === id), JSON.parse(options.body)); return null; }
    if (m === "GET") {
      const id = (chemin.match(/[?&]id=eq\.([^&]+)/) || [])[1];
      if (id) return base.demandes.filter((r) => r.id === decodeURIComponent(id));
      const docId = decodeURIComponent((chemin.match(/app_console_document_id=eq\.([^&]+)/) || [])[1] || "");
      return base.demandes.filter((r) => r.app_console_document_id === docId && ["draft", "approval", "ongoing", "paused"].includes(r.status)).reverse().slice(0, 1);
    }
  }
  throw new Error(`appel de base non prevu : ${m} ${chemin}`);
}
const doublures = {
  supabaseRequest,
  logJob: async (_id, etape, statut, message) => { base.journal.push(`LOG ${etape}/${statut} ${message}`); },
  safeJsonParse: (v) => (typeof v === "string" ? JSON.parse(v) : v || {}),
  downloadStorageObject: async () => ({ buffer: fs.readFileSync(pdfChemin), mimeType: "application/pdf" }),
  loadDossier: async () => ({ app_dossier_id: 9000001, hektor_annonce_id: "70001", commercial_nom: "Frederic Gerphagnon", negociateur_email: BOITE }),
  resolveEstimNegotiatorContact: async () => ({ nom: "Frederic Gerphagnon", email: BOITE, telephone: null }),
  MARQUE_REFUS_ETAT: "[REFUS D'ETAT]",
  require: (m) => require(m === "./youtrust_client" ? path.join(__dirname, "youtrust_client") : m),
};
// eslint-disable-next-line no-new-func
const H = new Function(...Object.keys(doublures),
  `${tranche("function cleanString(")}\n${tranche("function safeFilename(")}\n${tranche("function storageSafeFilename(")}\n${bloc}
   return { handleYoutrustSendSignature, handleYoutrustRemindSigner, handleYoutrustCancelSignature, handleYoutrustSigningLink, handleYoutrustSyncSignature, clientYoutrust };`)(
  ...Object.values(doublures));

const mandant = (i) => ({ prenom: "Frederic", nom: `Gerphagnon (mandant ${i})`, email: BOITE, telephone: "" });
const job = (payload) => ({ id: `job-${Date.now()}`, requested_by: null, payload_json: payload });
const attendre = (ms) => new Promise((r) => setTimeout(r, ms));
const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
async function refus(promesse) { try { await promesse; return null; } catch (e) { return e.message; } }

(async () => {
  const payload = { app_console_document_id: DOC, document_kind: "mandat", numero_mandat: "18999", bien_adresse: "1 rue de l'Essai, 42000 Saint-Étienne", mandants: Array.from({ length: N }, (_, i) => mandant(i + 1)) };

  // 0. interrupteur eteint -> refus d'etat
  base.setting = "off";
  const r0 = await refus(H.handleYoutrustSendSignature(job(payload)));
  controle("0. interrupteur eteint : REFUS D'ETAT, rien n'est cree", /REFUS D'ETAT/.test(r0 || "") && base.demandes.length === 0, r0);
  base.setting = "on";

  // 1. l'envoi
  const r1 = await H.handleYoutrustSendSignature(job(payload));
  const dem = base.demandes[0];
  controle(`1. envoi : statut « sent », ${N + 1} signataires (${N} mandants + mandataire)`, r1.status === "sent" && dem.signers.length === N + 1, JSON.stringify(r1));
  controle("1. envoi : notre ligne porte l'id Youtrust et l'etat « ongoing »", dem.provider_request_id === r1.provider_request_id && dem.status === "ongoing", `${dem.status}`);
  controle("1. envoi : code par e-mail pour tous (aucun portable) -- D16", dem.signers.every((s) => s.otp === "otp_email"));
  const sig = base.documents.get(DOC).metadata_json.signature;
  controle(`1. miroir : provider youtrust, « pending », « 0/${N + 1} », SANS procedure_id (R2)`, sig.provider === "youtrust" && sig.status === "pending" && sig.progress === `0/${N + 1}` && sig.procedure_id === undefined && !sig.hektor_doc_id, JSON.stringify(sig));
  const client = H.clientYoutrust();
  let lu = null;
  for (let i = 0; i < 10; i += 1) { await attendre(3000); lu = await client.lireDemande(r1.provider_request_id); if ((lu.signers || []).some((s) => s.status === "notified")) break; }
  const etat = Object.fromEntries((lu.signers || []).map((s) => [s.id, s.status]));
  const mandantsS = dem.signers.filter((s) => s.role === "mandant");
  const m1 = mandantsS[0];
  const ng = dem.signers.find((s) => s.role === "mandataire");
  controle(`1. ordre D7 : les ${N} mandants invites EN PARALLELE, le negociateur ATTEND`, mandantsS.every((s) => etat[s.provider_signer_id] === "notified") && etat[ng.provider_signer_id] === "initiated", JSON.stringify(etat));
  const docs = await client.requete("GET", `/signature_requests/${r1.provider_request_id}/documents`);
  const docId = (Array.isArray(docs) ? docs : docs.data || [])[0].id;
  const ch = await client.listerChamps(r1.provider_request_id, docId);
  const champs = Array.isArray(ch) ? ch : ch.data || [];
  const compte = (id, type) => champs.filter((f) => f.signer_id === id && f.type === type).length;
  controle(`1. cases : chacun des ${N} mandants a 1 signature + 1 mention « Bon pour mandat »`, mandantsS.every((s) => compte(s.provider_signer_id, "signature") === 1 && compte(s.provider_signer_id, "mention") === 1), JSON.stringify(mandantsS.map((s) => [compte(s.provider_signer_id, "signature"), compte(s.provider_signer_id, "mention")])));
  controle("1. cases : le negociateur a 1 signature et AUCUNE mention", compte(ng.provider_signer_id, "signature") === 1 && compte(ng.provider_signer_id, "mention") === 0);
  // ordre de LECTURE (page, ligne, colonne) : la case GTI est la derniere de la grille -- a cote du
  // dernier mandant quand leur nombre est impair, en dessous quand il est pair.
  const lecture = (x) => x.page * 1e6 + Math.round(x.y / 20) * 1e3 + x.x;
  const fNego = champs.find((x) => x.signer_id === ng.provider_signer_id && x.type === "signature");
  const casesMandants = champs.filter((x) => x.type === "signature" && x.signer_id !== ng.provider_signer_id);
  console.log("       cases (page,x,y) :", [...casesMandants.map((x) => `M@p${x.page},${x.x},${x.y}`), `GTI@p${fNego.page},${fNego.x},${fNego.y}`].join("  "));
  controle("1. cases : la case du negociateur est la DERNIERE de la grille (ordre de lecture)", casesMandants.every((x) => lecture(fNego) > lecture(x)));
  controle("1. textes D19 : le nom de la demande est celui du mandat", lu.name === "Mandat de vente n° 18999 – 1 rue de l'Essai, 42000 Saint-Étienne", lu.name);

  // 2. rejeu du meme travail : pas de seconde demande
  const r2 = await H.handleYoutrustSendSignature(job(payload));
  controle("2. rejeu : « deja_envoye », AUCUNE nouvelle demande", r2.status === "deja_envoye" && base.demandes.length === 1, JSON.stringify(r2));

  // 3. relance du mandant 1
  const r3 = await H.handleYoutrustRemindSigner(job({ signature_request_id: dem.id, provider_signer_id: m1.provider_signer_id }));
  controle("3. relance d'un mandant invite : acceptee", r3.status === "reminded");
  const r3b = await refus(H.handleYoutrustRemindSigner(job({ signature_request_id: dem.id, provider_signer_id: ng.provider_signer_id })));
  controle("3. relance du negociateur avant son tour : REFUS D'ETAT (pas de rejeu)", /REFUS D'ETAT/.test(r3b || ""), r3b);

  // 4. le lien « Signer maintenant » du negociateur, avant son tour
  const r4 = await refus(H.handleYoutrustSigningLink(job({ signature_request_id: dem.id })));
  controle("4. lien du negociateur avant son tour : REFUS D'ETAT clair", /pas le tour/.test(r4 || ""), r4);

  // 5. annulation
  const r5 = await H.handleYoutrustCancelSignature(job({ signature_request_id: dem.id }));
  const sig5 = base.documents.get(DOC).metadata_json.signature;
  const lu5 = await client.lireDemande(r1.provider_request_id);
  controle("5. annulation : Youtrust « canceled », notre ligne « canceled », miroir « cancelled »", r5.status === "cancelled" && lu5.status === "canceled" && dem.status === "canceled" && sig5.status === "cancelled", `${lu5.status} ${dem.status} ${sig5.status}`);

  // 6. PDF a 2 mandants envoye avec UN seul -> refuse AVANT activation (aucun credit)
  const r6 = await refus(H.handleYoutrustSendSignature(job({ ...payload, mandants: Array.from({ length: N - 1 }, (_, i) => mandant(i + 1)) })));
  const dem6 = base.demandes[base.demandes.length - 1];
  const lu6 = dem6 && dem6.provider_request_id ? await client.lireDemande(dem6.provider_request_id).catch((e) => ({ status: `illisible (${e.status})` })) : null;
  controle(`6. reperes : ${2 * N + 1} dans le PDF, ${2 * N - 1} attendus -> REFUS D'ETAT avant activation`, /repere\(s\)/.test(r6 || "") && dem6.status === "failed", r6);
  controle("6. …et le brouillon Youtrust est SUPPRIME (jamais active)", !lu6 || /deleted|illisible/.test(lu6.status), lu6 && lu6.status);

  // 7. la mise a jour (lot 5) refuse clairement
  const r7 = await refus(H.handleYoutrustSyncSignature(job({})));
  controle("7. youtrust_sync_signature : refus clair « lot 5 »", /lot 5/.test(r7 || ""), r7);

  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.error("ECHEC DE L'ESSAI :", e.message, JSON.stringify(e.body || "").slice(0, 400)); process.exit(1); });
