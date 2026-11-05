// A.2 LOT 6b P1 -- la PHOTO DU PDF (D31) : a la generation, le worker range avec le mandat la liste de
// qui il fait signer, confrontee aux cases de signature du HTML reellement rendu.        05/11/2026
// Sur LE CODE REEL du worker (fonctions decoupees, fausse base) et le HTML REEL du gabarit du projet
// (ecrit par apps/hektor-v1/scripts/test_reperes_signature.mjs avec TEST_DUMP_DIR). N'appelle rien.
//     node Console/test_photo_signataires_pdf.js   (0 = vert · 1 = un echec · 2 = pas pu mesurer)
// ⭐ TEMOIN INVERSE : le worker d'avant la photo ne range AUCUNE photo ; le code du travail, si.
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
const racine = path.join(__dirname, "..");
const srcNeuf = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
let srcAvant;
// La version d'avant = le worker juste avant le commit qui introduit la photo (HEAD tant qu'elle n'est pas commitee).
const git = (args) => execFileSync("git", args, { cwd: racine, encoding: "utf8", maxBuffer: 128 * 1024 * 1024 });
try {
  const introduit = git(["log", "--format=%H", "-S", "function photoSignatairesDuPdf(", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }
const tranche = (src, d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n}", i) + 2); };

// ── Le HTML REEL du gabarit, avec ses reperes ─────────────────────────────────────────
const dossierHtml = fs.mkdtempSync(path.join(os.tmpdir(), "photo-pdf-"));
try {
  execFileSync(process.execPath, [path.join(racine, "apps", "hektor-v1", "scripts", "test_reperes_signature.mjs")],
    { cwd: path.join(racine, "apps", "hektor-v1"), env: { ...process.env, TEST_DUMP_DIR: dossierHtml }, encoding: "utf8", stdio: "pipe" });
} catch (e) { console.log("ECHEC  le HTML reel n'a pas pu etre ecrit -- " + (e.stdout || e.message).slice(-400)); process.exit(2); }
const htmlDe = (nom) => fs.readFileSync(path.join(dossierHtml, nom), "utf8");

// Les mandants du rendu, comme l'ecran les envoie (render_payload.mandants = draft.mandants).
const mandantsRendus = (n) => Array.from({ length: n }, (_, i) => ({
  id: i === 1 ? `detail-contact-5-603953-member-60395${i}` : `detail-contact-${i}-60010${i}`,
  civilite: i % 2 ? "Mme" : "M.", prenom: `Prenom${i + 1}`, nom: `ESSAI${i + 1}`, qualite: "Mandant",
  adresse: `${i + 1} rue de l'Essai, 42700 Firminy`, telephone: `06 00 00 00 0${i}`, email: `essai${i + 1}@exemple.fr`,
}));

function monterPhoto(src) {
  const blocs = ["function cleanString(", "function ficheDuMandantImprime(", "function photoSignatairesDuPdf("].map((d) => tranche(src, d));
  if (blocs.some((b) => !b)) return null;
  // eslint-disable-next-line no-new-func
  return new Function(`${blocs.join("\n")}; return { photoSignatairesDuPdf, ficheDuMandantImprime };`)();
}

// La generation entiere, interrupteur ALLUME, contre une fausse base (meme montage que l'essai du 4 bis).
function monterGeneration(src, base) {
  const blocs = ["function shouldKeepCloud(", "function cleanString(", "function ficheDuMandantImprime(", "function photoSignatairesDuPdf(",
    "async function handleGenerateMandatDocument(", "async function enregistrerMandatChezNous("].map((d) => tranche(src, d)).filter(Boolean);
  const D = {
    safeJsonParse: (v) => (typeof v === "string" ? JSON.parse(v) : v || {}),
    loadDossier: async () => ({ app_dossier_id: 9000001, hektor_annonce_id: "70001", statut_annonce: "Estimation", archive: "0" }),
    CLOUD_STATUSES: new Set(["Actif", "Sous offre", "Sous compromis", "Estimation"]),
    logJob: async (id, etape, statut, texte, details) => { base.journal.push(details || {}); },
    renderHtmlToPdfBuffer: async () => Buffer.from("%PDF-1.4 mandat d'essai"),
    storageSafeFilename: (n, f) => String(n || f),
    uploadStorageObject: async () => {},
    persistProvidedDocumentFile: async () => ({ storage_path: null }),
    interrupteurSignatureYoutrust: async () => true,
    supabaseRequest: async (chemin, options = {}) => {
      const m = options.method || "GET";
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

(async () => {
  try {
    const neuf = monterPhoto(srcNeuf);
    controle("(0) LA PREUVE D'ABORD : photoSignatairesDuPdf existe dans le code du travail", Boolean(neuf));
    controle("(0) …et PAS dans la version d'avant (sinon le temoin ne temoigne de rien)", !monterPhoto(srcAvant));

    // 1. Le HTML reel, mandat a 2, 3 et 4 mandants, et l'avenant a 2 : la photo est VALIDE.
    for (const n of [2, 3, 4]) {
      const p = neuf.photoSignatairesDuPdf({ html: htmlDe(`mandat_${n}_mandants.html`), render_payload: { mandants: mandantsRendus(n) } });
      controle(`1. mandat a ${n} mandants : photo valide, ${2 * n + 1} reperes trouves`, p.valide && p.reperes_trouves === 2 * n + 1 && p.reperes_attendus === 2 * n + 1, JSON.stringify(p.problemes));
      controle(`1. mandat a ${n} mandants : rangs 1..${n}, dans l'ordre du rendu`, p.mandants.map((m) => m.rang).join(",") === Array.from({ length: n }, (_, i) => i + 1).join(",")
        && p.mandants.every((m, i) => m.nom === `ESSAI${i + 1}` && m.prenom === `Prenom${i + 1}`));
    }
    const av = neuf.photoSignatairesDuPdf({ html: htmlDe("avenant_2_mandants.html"), render_payload: { mandants: mandantsRendus(2) } });
    controle("1. avenant a 2 mandants : photo valide (5 reperes)", av.valide && av.reperes_trouves === 5, JSON.stringify(av.problemes));

    // 2. Ce que la photo doit REFUSER (l'envoi le refusera ensuite).
    const plus = neuf.photoSignatairesDuPdf({ html: htmlDe("mandat_2_mandants.html"), render_payload: { mandants: mandantsRendus(3) } });
    controle("2. le rendu annonce 3 mandants, le PDF n'en a que 2 : photo INVALIDE", !plus.valide && plus.problemes.length > 0, JSON.stringify(plus.problemes));
    const moins = neuf.photoSignatairesDuPdf({ html: htmlDe("mandat_3_mandants.html"), render_payload: { mandants: mandantsRendus(2) } });
    controle("2. le rendu annonce 2 mandants, le PDF en a 3 : photo INVALIDE", !moins.valide);
    const sansReperes = htmlDe("mandat_2_mandants.html").replace(/\{\{s\d+\|[^}]*\}\}/g, "");
    const muet = neuf.photoSignatairesDuPdf({ html: sansReperes, render_payload: { mandants: mandantsRendus(2) } });
    controle("2. un PDF genere SANS reperes : photo INVALIDE, 0 repere trouve", !muet.valide && muet.reperes_trouves === 0);
    const vide = neuf.photoSignatairesDuPdf({ html: htmlDe("mandat_2_mandants.html"), render_payload: {} });
    controle("2. aucun mandant dans le rendu : photo INVALIDE", !vide.valide && /aucun mandant/.test(vide.problemes.join(" ")));
    const rien = neuf.photoSignatairesDuPdf(null);
    controle("2. une charge absente ne fait pas tomber la generation : photo INVALIDE, sans exception", rien && !rien.valide);

    // 3. Le numero de la fiche.
    const f = neuf.ficheDuMandantImprime;
    controle("3. carte « detail-contact-5-603953 » -> fiche 603953 (deduite de l'ecran)", f({ id: "detail-contact-5-603953" }).numero === "603953" && f({ id: "detail-contact-5-603953" }).source === "id_ecran");
    controle("3. membre d'un couple « …-member-603954 » -> fiche 603954", f({ id: "detail-contact-5-603953-member-603954" }).numero === "603954");
    controle("3. ligne ajoutee a la main « mandant-1784905052078 » -> AUCUNE fiche (pas d'horodatage pris pour un numero)", f({ id: "mandant-1784905052078" }).numero === null);
    controle("3. un numero donne par l'ecran l'emporte sur l'identifiant de la carte", f({ id: "detail-contact-5-603953", hektor_contact_id: "20000101" }).numero === "20000101" && f({ id: "x", hektor_contact_id: "20000101" }).source === "ecran");

    // 4. La generation entiere : le document NE CHEZ NOUS porte la photo ; le temoin inverse n'en a pas.
    const payloadGen = { html: htmlDe("mandat_2_mandants.html"), document_label: "Mandat de vente - 24517", render_payload: { mandants: mandantsRendus(2) } };
    const baseNeuf = { documents: [], journal: [] };
    await monterGeneration(srcNeuf, baseNeuf)({ id: "job-p1", app_dossier_id: 9000001, payload_json: payloadGen });
    const photo = baseNeuf.documents[0] && baseNeuf.documents[0].metadata_json.signataires_du_pdf;
    controle("4. APRES : le mandat ne chez nous porte la photo, valide, 2 mandants", photo && photo.valide && photo.mandants.length === 2);
    controle("4. APRES : le journal du travail dit la photo (valide, 2 mandants)", baseNeuf.journal.some((d) => d.signataires_du_pdf && d.signataires_du_pdf.valide === true && d.signataires_du_pdf.mandants === 2));
    payloadGen.render_payload.mandants[0].nom = "CHANGE APRES COUP";
    controle("4. la photo est une COPIE : changer la charge apres coup ne la change pas", photo.mandants[0].nom === "ESSAI1");
    const baseAvant = { documents: [], journal: [] };
    await monterGeneration(srcAvant, baseAvant)({ id: "job-p1-avant", app_dossier_id: 9000001, payload_json: { ...payloadGen } });
    controle("4. TEMOIN INVERSE : le worker d'avant la photo ne range AUCUNE photo", baseAvant.documents.length === 1 && !baseAvant.documents[0].metadata_json.signataires_du_pdf);
    // Reprise : un travail rejoue retrouve SA ligne, la photo n'est pas reprise ni doublee.
    await monterGeneration(srcNeuf, baseNeuf)({ id: "job-p1", app_dossier_id: 9000001, payload_json: payloadGen });
    controle("4. un travail REJOUE retrouve sa ligne : une seule ligne, photo d'origine", baseNeuf.documents.length === 1 && baseNeuf.documents[0].metadata_json.signataires_du_pdf.mandants[0].nom === "ESSAI1");
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  } finally {
    fs.rmSync(dossierHtml, { recursive: true, force: true });
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
