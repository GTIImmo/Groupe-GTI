// 17/11/2026 -- LE GARDE : un document SIGNE ou EN COURS de signature ne se SUPPRIME pas.
// Note : notice/BLOCAGE_SUPPRESSION_DOCUMENT_SIGNE_2026-11-17.md.
//
// CE QUI EST EPROUVE, sur LE CODE REEL (fonctions decoupees dans console_job_worker.js et
// montees contre de faux Hektor / Supabase -- methode de test_garde_r1_signature.js) :
//   handleDeleteDocumentFromHektor, scene par scene (signe ImmoSign, signe Youtrust, a la main,
//   en attente, en cours, en approbation ; puis annule, refuse, a envoyer, sans signature).
// ⭐ LE TEMOIN INVERSE : chaque scene est aussi jouee sur le worker d'AVANT ce garde (git) -- il
//   doit avoir APPELE Hektor pour les documents signes (sinon le test ne prouverait rien).
// N'appelle rien, n'ecrit rien.
//     node Console/test_garde_suppression_document_signe.js   (0 = vert · 1 = un echec · 2 = pas pu mesurer)

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}

const srcNeuf = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
let srcAvant;
try {
  // « AVANT » = le worker juste avant le commit qui a introduit documentSignatureEngagee ; tant que ce n'est pas
  // commite, HEAD (qui ne la contient pas encore).
  const git = (args) => execFileSync("git", args, { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 128 * 1024 * 1024 });
  const introduit = git(["log", "--format=%H", "-S", "function documentSignatureEngagee(", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) {
  console.log("ECHEC  lecture de la version d'avant (git) -- " + e.message);
  process.exit(2);
}
if (srcAvant.includes("function documentSignatureEngagee(")) {
  console.log("ECHEC  la version d'avant contient deja le garde : le temoin se comparerait a lui-meme");
  process.exit(2);
}

// Decoupe une declaration de haut niveau (de son debut jusqu'a la declaration suivante).
function decoupe(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const reste = src.slice(i + debut.length);
  const m = reste.match(/\n(?:async function |function |const |let |class )/);
  return src.slice(i, i + debut.length + (m ? m.index : reste.length));
}

function monter(src) {
  const morceaux = [
    decoupe(src, "const STATUTS_SIGNATURE_EN_COURS"),
    decoupe(src, "function documentSignatureEngagee("),
    decoupe(src, "async function handleDeleteDocumentFromHektor("),
  ].filter(Boolean);
  const appels = [];
  const faux = {
    MARQUE_REFUS_ETAT: "[REFUS D'ETAT]",
    XMLRPC_URL: "https://hektor.test/xmlrpc",
    safeJsonParse: (x) => (typeof x === "string" ? JSON.parse(x) : x || {}),
    loadDossier: async () => ({ app_dossier_id: 77, hektor_annonce_id: "62963" }),
    loadConsoleDocumentById: async () => faux.document,
    ensureHektorExecutionContext: async () => { appels.push("session_hektor"); },
    hektorFetch: async (url) => { appels.push("hektor:" + (url.includes("_delete") ? "supprime" : "liste")); return { text: "deleteUploadedDocument('555')" }; },
    sleep: async () => {},
    fetchConsoleDocumentEntries: async () => { appels.push("hektor:relit"); return []; },
    insertDeletedDocumentLog: async () => { appels.push("trace"); },
    deleteStorageObject: async () => { appels.push("coffre:supprime"); },
    isReadableFile: () => false,
    fs: { unlinkSync: () => { appels.push("serveur:supprime"); } },
    supabaseRequest: async () => { appels.push("ligne:supprimee"); },
    upsertConsoleDocuments: async () => {},
    enqueueRefreshConsoleDataJobBestEffort: async () => null,
    document: null,
  };
  const corps = `${morceaux.join("\n")}\nreturn { handleDeleteDocumentFromHektor, documentSignatureEngagee: typeof documentSignatureEngagee === "function" ? documentSignatureEngagee : null };`;
  const fabrique = new Function(...Object.keys(faux).filter((k) => k !== "document"), corps);
  const api = fabrique(...Object.keys(faux).filter((k) => k !== "document").map((k) => faux[k]));
  return { api, faux, appels };
}

function documentAvec(metadata) {
  return { id: "doc-1", hektor_annonce_id: "62963", document_name: "Mandat 18420.pdf", visibility: "private",
           hektor_document_id: "h1", storage_path: "annonces/62963/documents/doc-1/m.pdf",
           metadata_json: { hektor_uploaded_document_id: "555", ...metadata } };
}

async function jouer(src, metadata) {
  const { api, faux, appels } = monter(src);
  faux.document = documentAvec(metadata);
  let erreur = null;
  try {
    await api.handleDeleteDocumentFromHektor({ id: "job-1", payload_json: { document_id: "doc-1" } });
  } catch (e) {
    erreur = e.message;
  }
  return { erreur, appels };
}

const BLOQUES = [
  ["signé ImmoSign (copie signée rapatriée)", { signed_document: { path: "signed/x.pdf" }, signature: { procedure_id: "33", status: "signed" } }],
  ["signé Youtrust", { signed_document: { path: "signed/y.pdf" }, signature: { provider: "youtrust", status: "signed" } }],
  ["signé à la main", { signature: { status: "signed", source: "manuscrite", signed_at: "2026-11-17" } }],
  ["ImmoSign en attente", { signature: { procedure_id: "34", status: "pending" } }],
  ["Youtrust en cours", { signature: { provider: "youtrust", status: "ongoing" } }],
  ["Youtrust en approbation", { signature: { provider: "youtrust", status: "approval" } }],
];
const LIBRES = [
  ["Youtrust annulé", { signature: { provider: "youtrust", status: "cancelled" } }],
  ["ImmoSign refusé", { signature: { procedure_id: "35", status: "refused" } }],
  ["à envoyer", { signature: { status: "to_send" } }],
  ["sans signature", {}],
];

(async () => {
  for (const [nom, md] of BLOQUES) {
    const neuf = await jouer(srcNeuf, md);
    controle(`NEUF  ${nom} : refusé, définitif, RIEN chez Hektor ni chez nous`,
      Boolean(neuf.erreur && neuf.erreur.startsWith("[REFUS D'ETAT]")) && neuf.appels.length === 0,
      `erreur=${neuf.erreur} appels=${neuf.appels.join(",")}`);
    const avant = await jouer(srcAvant, md);
    controle(`AVANT ${nom} : l'ancien code SUPPRIMAIT (témoin inverse)`,
      !avant.erreur && avant.appels.includes("hektor:supprime") && avant.appels.includes("ligne:supprimee"),
      `erreur=${avant.erreur} appels=${avant.appels.join(",")}`);
  }
  for (const [nom, md] of LIBRES) {
    const neuf = await jouer(srcNeuf, md);
    controle(`NEUF  ${nom} : se supprime toujours (trace écrite AVANT la destruction)`,
      !neuf.erreur && neuf.appels.includes("hektor:supprime") && neuf.appels.indexOf("trace") < neuf.appels.indexOf("ligne:supprimee"),
      `erreur=${neuf.erreur} appels=${neuf.appels.join(",")}`);
  }
  const { api } = monter(srcNeuf);
  controle("la règle est exportée par le worker et identique à celle découpée ici",
    typeof api.documentSignatureEngagee === "function" && srcNeuf.includes("module.exports = { documentSignatureEngagee,"));
  console.log(echecs.length ? `\n${echecs.length} échec(s)` : "\nTout est vert");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => {
  console.log("ECHEC  " + (e && e.stack || e));
  process.exit(2);
});
