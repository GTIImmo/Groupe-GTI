/**
 * EPREUVE : LA SALLE D'ATTENTE SE VIDE -- et seulement quand c'est sur.
 * 14/10/2026. Chantier ③ / 3d.
 *
 * CE QU'ELLE GARDE. Le 14/10, 109 fichiers (196 Mo) dormaient sous temp/ du coffre
 * documents depuis le 14/05 -- dont 93 sortis des TROIS GENERATEURS DE PDF (estimation
 * 137 Mo, cadastre, mandat), pas de l'ajout de documents. Les quatre types de travaux
 * font passer leur fichier par `handleUploadDocumentToHektor`, qui ne vidait jamais la
 * salle d'attente. Ils ont ete supprimes, et le chemin a ete bouche ; cette epreuve
 * empeche la fuite de revenir.
 *
 * ⚠ ELLE N'EXECUTE PAS LE WORKER. Elle DECOUPE le bloc de la fonction dans le fichier
 *   et le fait tourner avec des doublures -- lancer console_job_worker.js demarrerait un
 *   5e worker a cote des 4 services.
 *
 * LES TROIS CAS, ET POURQUOI LES DEUX DERNIERS COMPTENT AUTANT QUE LE PREMIER :
 *   (A) Hektor confirme, la copie serveur est faite  -> le temporaire est RETIRE
 *   (B) la copie serveur n'a PAS eu lieu             -> le temporaire est GARDE, et DIT
 *   (C) Hektor ne confirme pas                       -> ca leve, le temporaire est GARDE
 *       (sinon un rejeu n'aurait plus de fichier a envoyer)
 *
 *   node Console/test_nettoyage_temporaire.js
 */

const fs = require("fs");
const path = require("path");

const WORKER = path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(WORKER, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function tranche(marque) {
  const i = src.indexOf(marque);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

const bloc = tranche("async function handleUploadDocumentToHektor(");
const TEMP = "temp/uploads/j-1/Estimation.pdf";

function charger({ hektorConfirme = true, copieServeur = true } = {}) {
  const journal = [];
  const faux = {
    safeJsonParse: (x) => (typeof x === "string" ? JSON.parse(x) : x),
    loadDossier: async () => ({ hektor_annonce_id: "62087", app_dossier_id: 1 }),
    completerEnvoiDocumentDiffere: async () => { journal.push("CHEMIN_DIFFERE"); return {}; },
    ensureHektorExecutionContext: async () => {},
    safeFilename: (n, f) => n || f,
    shouldKeepCloud: () => true,
    downloadStorageObject: async (chemin) => {
      journal.push(`LECTURE:${chemin}`);
      return { buffer: Buffer.alloc(1024, 7), mimeType: "application/pdf" };
    },
    envoyerDocumentAHektor: async () => {
      journal.push("APPEL_HEKTOR");
      return hektorConfirme
        ? { entries: [{ hektor_document_id: "H-7" }], found: { hektor_document_id: "H-7" } }
        : { entries: [], found: null };
    },
    // L'indexation rend la ligne rangee -- ou RIEN, et c'est le cas (B) : sans ligne,
    // persistProvidedDocumentFile n'est pas appele, donc `stored` reste null.
    upsertConsoleDocuments: async () => {
      journal.push("reindexation");
      return copieServeur ? [{ id: "doc-9", hektor_document_id: "H-7", hektor_annonce_id: "62087" }] : [];
    },
    persistProvidedDocumentFile: async () => {
      journal.push("ECRITURE_SERVEUR");
      return { local_path: "C:/serveur/x", storage_path: "annonces/62087/documents/doc-9/Estimation.pdf" };
    },
    deleteStorageObject: async (chemin) => { journal.push(`SUPPRESSION:${chemin}`); },
    logJob: async (_id, _type, _etat, message) => { journal.push(`JOURNAL:${message}`); },
    supabaseRequest: async () => null,
    enqueueRefreshConsoleDataJobBestEffort: async () => null,
    console: { warn: () => {} },
  };
  // eslint-disable-next-line no-new-func
  const fn = new Function(...Object.keys(faux), `${bloc}; return handleUploadDocumentToHektor;`)(
    ...Object.values(faux));
  return { fn, journal };
}

const travail = () => ({
  id: "job-1",
  payload_json: JSON.stringify({ temp_storage_path: TEMP, original_filename: "Estimation.pdf" }),
});

(async () => {
  console.log("\nLa salle d'attente se vide -- et seulement quand c'est sur\n");

  if (!bloc) {
    controle("(0) le chemin immediat est dans le worker", false, "introuvable");
  } else {
    // ── (A) TOUT S'EST BIEN PASSE ──────────────────────────────────────────
    let { fn, journal } = charger();
    await fn(travail());
    controle("(a) le fichier est lu dans la salle d'attente",
      journal.includes(`LECTURE:${TEMP}`), journal.join(" > "));
    controle("(b) ⚠ LE TEMPORAIRE EST RETIRE une fois le document envoye ET copie",
      journal.includes(`SUPPRESSION:${TEMP}`), journal.join(" > "));
    controle("(c) ⚠ et APRES la copie serveur, jamais avant",
      journal.indexOf(`SUPPRESSION:${TEMP}`) > journal.indexOf("ECRITURE_SERVEUR"),
      `ordre : ${journal.join(" > ")}`);

    // ── (B) LA COPIE SERVEUR N'A PAS EU LIEU ───────────────────────────────
    //    Le temporaire est alors la SEULE copie connue : on ne le touche pas.
    ({ fn, journal } = charger({ copieServeur: false }));
    await fn(travail());
    controle("(d) ⭐ TEMOIN INVERSE : sans copie serveur, le temporaire est GARDE",
      !journal.some((e) => e.startsWith("SUPPRESSION:")), journal.join(" > "));
    controle("(e) et on le DIT au journal, au lieu de le perdre en silence",
      journal.some((e) => e.startsWith("JOURNAL:") && /NON copie sur le serveur/.test(e)),
      journal.join(" > "));

    // ── (C) HEKTOR NE CONFIRME PAS ─────────────────────────────────────────
    //    Ca leve, comme avant. Le temporaire doit survivre pour un rejeu.
    ({ fn, journal } = charger({ hektorConfirme: false }));
    let leve = null;
    try { await fn(travail()); } catch (e) { leve = e.message; }
    controle("(f) Hektor non confirme : ca leve toujours, comme avant",
      leve !== null && /non confirme/i.test(leve), `a leve : ${leve}`);
    controle("(g) ⭐ TEMOIN INVERSE : et le temporaire est GARDE pour le rejeu",
      !journal.some((e) => e.startsWith("SUPPRESSION:")), journal.join(" > "));

    // ── L'AIGUILLAGE N'A PAS BOUGE ─────────────────────────────────────────
    ({ fn, journal } = charger());
    await fn({ id: "job-1", payload_json: JSON.stringify({ app_document_id: "doc-1" }) });
    controle("(h) avec app_document_id, c'est toujours le chemin differe qui prend",
      journal.includes("CHEMIN_DIFFERE") && !journal.includes("APPEL_HEKTOR"),
      journal.join(" > "));

    // ── LA JUMELLE PHOTO FAISAIT DEJA LE GESTE : il ne doit pas disparaitre ──
    controle("(i) le chemin immediat des photos vide toujours sa salle d'attente",
      /else \{\s*await deleteStorageObject\(tempPath\);\s*\}/.test(src),
      "le geste des photos a disparu");
  }

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
