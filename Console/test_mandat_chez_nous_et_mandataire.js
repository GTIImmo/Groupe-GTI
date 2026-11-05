// A.2 LOT 4 bis -- (A) le mandat genere nait CHEZ NOUS quand la signature Youtrust est allumee
// (D24), et rien ne change quand elle est eteinte ; (B) le mandataire (D21).        26/10/2026
// Sur LE CODE REEL du worker (fonctions decoupees, fausse base, doublures). N'appelle rien.
//     node Console/test_mandat_chez_nous_et_mandataire.js   (0 = vert · 1 = un echec · 2 = pas pu mesurer)
// ⭐ TEMOIN INVERSE : interrupteur ETEINT, la generation est jouee sur le code d'AVANT (le worker
//   juste avant le commit qui introduit enregistrerMandatChezNous) ET sur le code du travail :
//   les memes appels, la meme charge du travail Hektor, a l'octet.
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
const srcNeuf = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const git = (args) => execFileSync("git", args, { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 128 * 1024 * 1024 });
let srcAvant;
try {
  const introduit = git(["log", "--format=%H", "-S", "async function enregistrerMandatChezNous(", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }
const tranche = (src, d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n}", i) + 2); };

// ── (A) LA GENERATION ──────────────────────────────────────────────────────────────
function monterGeneration(src, base, statut = "Estimation") {
  const blocs = ["function shouldKeepCloud(", "async function handleGenerateMandatDocument(", "async function enregistrerMandatChezNous("]
    .map((d) => tranche(src, d)).filter(Boolean);
  const D = {
    safeJsonParse: (v) => (typeof v === "string" ? JSON.parse(v) : v || {}),
    loadDossier: async () => ({ app_dossier_id: 9000001, hektor_annonce_id: "70001", statut_annonce: statut, archive: "0" }),
    CLOUD_STATUSES: new Set(["Actif", "Sous offre", "Sous compromis", "Estimation"]),
    logJob: async () => {},
    renderHtmlToPdfBuffer: async () => Buffer.from("%PDF-1.4 mandat d'essai"),
    storageSafeFilename: (n, f) => String(n || f),
    uploadStorageObject: async (chemin) => { base.appels.push(`UPLOAD ${chemin}`); },
    persistProvidedDocumentFile: async (ligne, buf, mime, opts) => {
      base.appels.push(`RANGE ${ligne.id} cloud=${opts.cloud}`);
      const storage_path = `annonces/${ligne.hektor_annonce_id}/documents/${ligne.id}/${ligne.document_name}`;
      const l = base.documents.find((x) => x.id === ligne.id);
      if (l) Object.assign(l, opts.cloud ? { storage_path, storage_status: "cloud_available" } : { storage_status: "local_only" });
      return { storage_path: opts.cloud ? storage_path : null };
    },
    interrupteurSignatureYoutrust: async () => base.youtrust,
    supabaseRequest: async (chemin, options = {}) => {
      const m = options.method || "GET";
      base.appels.push(`${m} ${chemin.split("?")[0]}${m === "GET" ? "?" + chemin.split("?")[1] : ""}`);
      if (chemin.startsWith("app_console_job") && m === "POST") { base.travaux.push(...JSON.parse(options.body)); return [{ id: "upload-1" }]; }
      if (chemin.startsWith("app_console_document") && m === "POST") { base.documents.push(...JSON.parse(options.body)); return null; }
      if (chemin.startsWith("app_console_document") && m === "GET") {
        const j = decodeURIComponent((chemin.match(/generation_job_id=eq\.([^&]+)/) || [])[1] || "");
        return base.documents.filter((d) => d.metadata_json && d.metadata_json.generation_job_id === j);
      }
      throw new Error(`appel non prevu : ${m} ${chemin}`);
    },
    STORAGE_BUCKET: "hektor-console-documents",
    crypto: require("crypto"),
  };
  // eslint-disable-next-line no-new-func
  return new Function(...Object.keys(D), `${blocs.join("\n")}; return handleGenerateMandatDocument;`)(...Object.values(D));
}
const jobGen = { id: "job-gen-1", app_dossier_id: 9000001, requested_by: null,
  payload_json: { html: "<html>mandat</html>", document_label: "Mandat de vente - 18999", avenant_new_price: null } };

// ── (B) LE MANDATAIRE ──────────────────────────────────────────────────────────────
function monterMandataire(annuaire, profils) {
  const blocs = ["function cleanString(", "function emailSignataireValide(", "function refusEtatYoutrust(", "async function mandataireDuMandat("]
    .map((d) => tranche(srcNeuf, d));
  const supabaseRequest = async (chemin) => {
    if (chemin.startsWith("app_hektor_negotiator_agency_directory")) {
      const id = (chemin.match(/hektor_negociateur_id=eq\.([^&]+)/) || [])[1];
      const em = (chemin.match(/email=ilike\.([^&]+)/) || [])[1];
      if (id) return annuaire.filter((r) => r.hektor_negociateur_id === decodeURIComponent(id));
      // ilike : « _ » joker -> le faux renvoie AUSSI des voisins approchants, comme la vraie base
      const motif = new RegExp(`^${decodeURIComponent(em).replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/_/g, ".")}$`, "i");
      return annuaire.filter((r) => motif.test(r.email || ""));
    }
    if (chemin.startsWith("app_user_profile")) {
      const id = decodeURIComponent(chemin.match(/id=eq\.([^&]+)/)[1]);
      return profils.filter((p) => p.id === id);
    }
    throw new Error(`appel non prevu : ${chemin}`);
  };
  // eslint-disable-next-line no-new-func
  return new Function("supabaseRequest", "MARQUE_REFUS_ETAT", `${blocs.join("\n")}; return mandataireDuMandat;`)(supabaseRequest, "[REFUS D'ETAT]");
}
const annuaire = [
  { hektor_negociateur_id: "N1", prenom: "Pierre", nom: "ACTIF", display_name: "Pierre ACTIF", email: "pierre.actif@gti-immobilier.fr", portable: "06 11 22 33 44", telephone: "", is_active: true },
  { hektor_negociateur_id: "N2", prenom: "Paul", nom: "PARTI", display_name: "Paul PARTI", email: "paul.parti@gti-immobilier.fr", portable: "06 55 66 77 88", telephone: "", is_active: false },
  { hektor_negociateur_id: "N3", prenom: "Sans", nom: "MAIL", display_name: "Sans MAIL", email: "", portable: "06 00 00 00 00", telephone: "", is_active: true },
  { hektor_negociateur_id: "N4", prenom: "Pauline", nom: "EXPEDITRICE", display_name: "Pauline EXPEDITRICE", email: "pauline_x@gti-immobilier.fr", portable: "07 12 34 56 78", telephone: "", is_active: true },
  { hektor_negociateur_id: "N5", prenom: "Faux", nom: "VOISIN", display_name: "Faux VOISIN", email: "paulineAx@gti-immobilier.fr", portable: "07 99 99 99 99", telephone: "", is_active: true },
];
const profils = [
  { id: "u-pauline", email: "pauline_x@gti-immobilier.fr", first_name: "Pauline", last_name: "EXPEDITRICE", display_name: "Pauline" },
  { id: "u-hors", email: "hors.annuaire@gti-immobilier.fr", first_name: "Hors", last_name: "ANNUAIRE", display_name: "Hors" },
];

(async () => {
  try {
    // (A)
    controle("(0) LA PREUVE D'ABORD : enregistrerMandatChezNous est dans le code du travail, pas dans celui d'avant",
      Boolean(tranche(srcNeuf, "async function enregistrerMandatChezNous(")) && !tranche(srcAvant, "async function enregistrerMandatChezNous("));
    const bAvant = { youtrust: false, appels: [], travaux: [], documents: [] };
    const bNeuf = { youtrust: false, appels: [], travaux: [], documents: [] };
    const rAvant = await monterGeneration(srcAvant, bAvant)(jobGen);
    const rNeuf = await monterGeneration(srcNeuf, bNeuf)(jobGen);
    controle("A1. ETEINT : memes appels que le code d'avant", JSON.stringify(bAvant.appels) === JSON.stringify(bNeuf.appels), `${bAvant.appels} / ${bNeuf.appels}`);
    controle("A1. ETEINT : meme travail upload_document_to_hektor, charge identique", JSON.stringify(bAvant.travaux) === JSON.stringify(bNeuf.travaux.map((t) => ({ ...t, requested_at: bAvant.travaux[0].requested_at }))) && bNeuf.travaux[0].job_type === "upload_document_to_hektor");
    controle("A1. ETEINT : meme resultat, aucune ligne creee chez nous", JSON.stringify(rAvant) === JSON.stringify(rNeuf) && bNeuf.documents.length === 0);

    const bOn = { youtrust: true, appels: [], travaux: [], documents: [] };
    const rOn = await monterGeneration(srcNeuf, bOn)(jobGen);
    const doc = bOn.documents[0];
    controle("A2. ALLUME : AUCUN travail Hektor, aucun fichier temporaire", bOn.travaux.length === 0 && !bOn.appels.some((a) => /temp\/uploads/.test(a)), bOn.appels.join(" | "));
    controle("A2. ALLUME : UNE ligne chez nous, source app, « sans_hektor », sans numero Hektor", bOn.documents.length === 1 && doc.source === "app" && doc.envoi_hektor_statut === "sans_hektor" && !doc.hektor_document_id);
    controle("A2. ALLUME, bien en Estimation (vivant) : copie au coffre, SELON LA REGLE", bOn.appels.includes(`RANGE ${doc.id} cloud=true`) && doc.storage_status === "cloud_available");
    const bVendu = { youtrust: true, appels: [], travaux: [], documents: [] };
    await monterGeneration(srcNeuf, bVendu, "Vendu")({ ...jobGen, id: "job-gen-vendu" });
    const dv = bVendu.documents[0];
    controle("A2. ALLUME, bien Vendu : PAS de copie au coffre (regle shouldKeepCloud respectee), serveur seulement", bVendu.appels.includes(`RANGE ${dv.id} cloud=false`) && dv.storage_status === "local_only");
    controle("A2. ALLUME : le resultat porte app_document_id (l'envoi Youtrust en a besoin)", rOn.app_document_id === doc.id && rOn.sans_hektor === true);
    const rRejeu = await monterGeneration(srcNeuf, bOn)(jobGen);
    controle("A3. REJEU du meme travail : la MEME ligne, pas de doublon", bOn.documents.length === 1 && rRejeu.app_document_id === doc.id);

    // (B)
    const md = monterMandataire(annuaire, profils);
    const b1 = await md({ requested_by: "u-pauline" }, {}, { commercial_id: "N1" });
    controle("B1. negociateur DU BIEN actif : c'est lui qui signe", b1.email === "pierre.actif@gti-immobilier.fr" && b1.source === "negociateur_du_bien", JSON.stringify(b1));
    const b2 = await md({ requested_by: "u-pauline" }, {}, { commercial_id: "N2" });
    controle("B2. negociateur du bien INACTIF : la personne qui envoie signe (annuaire)", b2.email === "pauline_x@gti-immobilier.fr" && b2.source === "expediteur" && b2.telephone === "07 12 34 56 78", JSON.stringify(b2));
    const b3 = await md({ requested_by: "u-pauline" }, {}, { commercial_id: "N9" });
    controle("B3. negociateur du bien ABSENT de l'annuaire : la personne qui envoie", b3.email === "pauline_x@gti-immobilier.fr", JSON.stringify(b3));
    const b4 = await md({ requested_by: "u-pauline" }, {}, { commercial_id: "N3" });
    controle("B4. negociateur actif SANS e-mail : la personne qui envoie", b4.source === "expediteur", JSON.stringify(b4));
    controle("B5. « _ » joker de ilike : le voisin « paulineAx » n'est PAS pris", b2.nom === "EXPEDITRICE" && b2.telephone !== "07 99 99 99 99");
    const b6 = await md({ requested_by: "u-hors" }, {}, { commercial_id: "N2" });
    controle("B6. expediteur hors annuaire : son compte (sans portable -> code e-mail)", b6.email === "hors.annuaire@gti-immobilier.fr" && b6.telephone === null && b6.nom === "ANNUAIRE", JSON.stringify(b6));
    let refus = null;
    try { await md({ requested_by: null }, {}, { commercial_id: "N2" }); } catch (e) { refus = e.message; }
    controle("B7. personne de valable : REFUS D'ETAT, jamais l'agence", /REFUS D'ETAT/.test(refus || "") && /introuvable/.test(refus || ""), refus);
    const b8 = await md({ requested_by: "u-pauline" }, { mandataire: { prenom: "Choisi", nom: "ALAMAIN", email: "c@gti-immobilier.fr" } }, { commercial_id: "N1" });
    controle("B8. la fenetre d'envoi impose le sien : il est pris tel quel", b8.nom === "ALAMAIN" && b8.source === "fenetre_envoi");
    // (C) le PDF a signer : copie serveur d'abord, coffre ensuite, jamais autre chose qu'un PDF
    const tmp = require("os").tmpdir();
    const pdfLocal = path.join(tmp, `essai_pdf_${Date.now()}.pdf`);
    fs.writeFileSync(pdfLocal, "%PDF-1.4 copie serveur");
    const pasPdf = path.join(tmp, `essai_txt_${Date.now()}.pdf`);
    fs.writeFileSync(pasPdf, "<html>erreur 500</html>");
    const appelsCoffre = [];
    const lire = new Function("isReadableFile", "readLocalArchiveFile", "downloadStorageObject", "MARQUE_REFUS_ETAT",
      `${tranche(srcNeuf, "function refusEtatYoutrust(")}
${tranche(srcNeuf, "async function lirePdfDuDocumentPourSignature(")}; return lirePdfDuDocumentPourSignature;`)(
      (f) => fs.existsSync(f), (f, m) => ({ buffer: fs.readFileSync(f), mimeType: m }),
      async (p) => { appelsCoffre.push(p); return { buffer: Buffer.from("%PDF-1.4 copie coffre") }; }, "[REFUS D'ETAT]");
    const c1 = await lire({ document_name: "M", storage_path: "annonces/x.pdf", metadata_json: { local_archive_path: pdfLocal } });
    controle("C1. copie serveur presente : lue en PREMIER (le coffre n'est pas appele)", /copie serveur/.test(c1.buffer.toString()) && appelsCoffre.length === 0);
    const c2 = await lire({ document_name: "M", storage_path: "annonces/x.pdf", metadata_json: { local_archive_path: "C:/n/existe/pas.pdf" } });
    controle("C2. copie serveur absente : le coffre", /copie coffre/.test(c2.buffer.toString()) && appelsCoffre.length === 1);
    let c3 = null; try { await lire({ document_name: "M", storage_path: null, metadata_json: { local_archive_path: pasPdf } }); } catch (e) { c3 = e.message; }
    controle("C3. un fichier qui n'est pas un PDF : REFUS D'ETAT", /REFUS D'ETAT/.test(c3 || ""), c3);
    fs.unlinkSync(pdfLocal); fs.unlinkSync(pasPdf);
    controle("B9. le resolveur de l'avis de valeur (repli agence) n'est plus appele par l'envoi",
      !/resolveEstimNegotiatorContact\(/.test(tranche(srcNeuf, "async function handleYoutrustSendSignature(")));
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
