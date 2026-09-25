// UN DOCUMENT EXISTE-T-IL MEME SI HEKTOR NE REPOND PAS ?
//                                                                  25/09/2026
// Jusqu'ici NON : le worker envoyait a Hektor D'ABORD, et la ligne n'existait qu'une
// fois Hektor confirme. Si Hektor ne repondait pas, le document n'existait nulle part.
// A la coupure, ajouter un document depuis l'app aurait CESSE de fonctionner.
//
// Les contacts, les annonces et les recherches ne marchent pas comme ca : l'app ecrit
// chez elle, et un worker pousse ensuite. Remarque de Frederic (25/09) : « les documents
// photos attendent toujours une confirmation de Hektor avant de sauvegarder,
// contrairement au reste du dev comme contact ».
//
// CE QUE CE TEST PROUVE :
//   ① l'ancien chemin est INCHANGE quand app_document_id est absent (dormant) ;
//   ② le nouveau ecrit sur NOTRE SERVEUR AVANT d'appeler Hektor -- c'est l'inversion ;
//   ③ un echec Hektor NE LEVE PAS : la ligne reste, marquee « echec » ;
//   ④ en cas de succes, le numero Hektor est pose sur NOTRE ligne AVANT la reindexation,
//      sinon l'indexation creerait une SECONDE ligne pour le meme document.
//
// Il fait tourner LA VRAIE fonction du worker avec un faux monde. N'APPELLE RIEN.

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

const bloc = tranche("async function completerEnvoiDocumentDiffere(");

function charger(hektorEchoue) {
  const journal = [];          // l'ORDRE des gestes, c'est ce qu'on verifie
  const patches = [];
  const faux = {
    supabaseRequest: async (chemin, options) => {
      if (!options || options.method === "GET") {
        journal.push("lecture_ligne");
        return [{
          id: "doc-1", hektor_annonce_id: "62087", document_name: "Mandat.pdf",
          visibility: "private", storage_path: "annonces/62087/documents/doc-1/Mandat.pdf",
          metadata_json: {},
        }];
      }
      journal.push("patch_ligne");
      patches.push(JSON.parse(options.body));
      return null;
    },
    downloadStorageObject: async () => {
      journal.push("lecture_fichier");
      return { buffer: Buffer.alloc(2048, 3), mimeType: "application/pdf" };
    },
    persistProvidedDocumentFile: async () => {
      journal.push("ECRITURE_SERVEUR");
      return { local_path: "C:/serveur/annonces/62087/documents/doc-1/Mandat.pdf" };
    },
    shouldKeepCloud: () => true,
    ensureHektorExecutionContext: async () => { journal.push("contexte_hektor"); },
    envoyerDocumentAHektor: async () => {
      journal.push("APPEL_HEKTOR");
      if (hektorEchoue) throw new Error("Session Hektor expiree");
      return { entries: [{ hektor_document_id: "H-99", document_name: "Mandat.pdf" }],
               found: { hektor_document_id: "H-99", document_name: "Mandat.pdf" } };
    },
    upsertConsoleDocuments: async () => { journal.push("reindexation"); return []; },
    enqueueRefreshConsoleDataJobBestEffort: async () => { journal.push("rafraichissement"); return null; },
    logJob: async () => { journal.push("journal"); },
    safeFilename: (n, f) => n || f,
  };
  // eslint-disable-next-line no-new-func
  const fn = new Function(...Object.keys(faux), `${bloc}; return completerEnvoiDocumentDiffere;`)(
    ...Object.values(faux));
  return { fn, journal, patches };
}

(async () => {
  if (!bloc) {
    controle("(0) le chemin differe est dans le worker", false, "introuvable");
  } else {
    // ── ② HEKTOR REPOND ────────────────────────────────────────────────────
    let { fn, journal, patches } = charger(false);
    let r = await fn({ id: "job-1" }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });

    const iServeur = journal.indexOf("ECRITURE_SERVEUR");
    const iHektor = journal.indexOf("APPEL_HEKTOR");
    controle("(a) le fichier est ecrit sur NOTRE SERVEUR",
      iServeur >= 0, journal.join(" > "));
    controle("(b) ⚠ AVANT d'appeler Hektor -- c'est l'inversion",
      iServeur >= 0 && iHektor > iServeur,
      `ordre : ${journal.join(" > ")}`);

    // ④ l'adoption avant la reindexation
    const iPatch = journal.indexOf("patch_ligne");
    const iReindex = journal.indexOf("reindexation");
    controle("(c) le numero Hektor est pose sur NOTRE ligne",
      patches.some((p) => p.hektor_document_id === "H-99"), JSON.stringify(patches));
    controle("(d) ⚠ AVANT la reindexation, sinon une SECONDE ligne serait creee",
      iPatch >= 0 && iReindex > iPatch, `ordre : ${journal.join(" > ")}`);
    controle("(e) le statut passe a « envoye »",
      patches.some((p) => p.envoi_hektor_statut === "envoye"), JSON.stringify(patches));
    controle("(f) le compte rendu le dit", r && r.envoi_hektor === "envoye", JSON.stringify(r));

    // ── ③ HEKTOR NE REPOND PAS ─────────────────────────────────────────────
    ({ fn, journal, patches } = charger(true));
    let leve = null;
    try {
      r = await fn({ id: "job-2" }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    } catch (e) { leve = e.message; }

    controle("(g) ⚠ un echec Hektor NE LEVE PAS", leve === null, `a leve : ${leve}`);
    controle("(h) le fichier est QUAND MEME sur notre serveur",
      journal.includes("ECRITURE_SERVEUR"), journal.join(" > "));
    controle("(i) la ligne est marquee « echec », pas supprimee",
      patches.some((p) => p.envoi_hektor_statut === "echec"), JSON.stringify(patches));
    controle("(j) le motif est conserve",
      patches.some((p) => /Session Hektor/.test(String(p.envoi_hektor_erreur || ""))),
      JSON.stringify(patches));
    controle("(k) l'echec est ecrit au journal", journal.includes("journal"), journal.join(" > "));
    controle("(l) le compte rendu le dit aussi", r && r.envoi_hektor === "echec", JSON.stringify(r));
    controle("(m) et le chemin serveur remonte quand meme",
      r && r.copie_serveur, JSON.stringify(r));
  }

  // ── ① LE CHEMIN D'ORIGINE EST INCHANGE ────────────────────────────────────
  controle("(n) sans app_document_id, l'ancien chemin s'execute",
    /if \(payload\.app_document_id\) \{\s*return await completerEnvoiDocumentDiffere/.test(src),
    "l'aiguillage est absent");
  controle("(o) l'ancien chemin leve toujours si Hektor n'a pas confirme",
    /if \(!found\) throw new Error\(`Upload Hektor non confirme/.test(src), "comportement change");
  controle("(p) et il indexe toujours AVANT ce controle, comme avant l'extraction",
    src.indexOf("const indexed = await upsertConsoleDocuments(dossier, entries);")
      < src.indexOf("if (!found) throw new Error(`Upload Hektor non confirme"),
    "l'ordre d'origine a ete inverse");

  // ── ⑤ L'ENVOI N'EXISTE QU'EN UN SEUL EXEMPLAIRE ──────────────────────────
  // ⚠ On compte les ENVOIS, pas les mentions de l'adresse : hektorFetch cite la meme
  // adresse pour l'exclure de la detection de page de login (l. 2969). Premiere version
  // de ce controle faussement au rouge pour cette raison.
  const envois = (src.match(/hektorFetch\(`\$\{ADMIN_URL\}upload_uploadeddoc\.php`/g) || []).length;
  controle("(q) l'envoi vers Hektor n'est ecrit QU'UNE FOIS",
    envois === 1, `${envois} envoi(s) dans le code -- deux copies divergeraient`);
  controle("(r) les deux chemins passent par la meme fonction",
    (src.match(/envoyerDocumentAHektor\(/g) || []).length >= 3,
    "un des chemins ne l'utilise pas");

  // ═══ ⑥ LA JUMELLE POUR LES PHOTOS ═══════════════════════════════════════
  const blocPhoto = tranche("async function completerEnvoiPhotoDifferee(");
  if (!blocPhoto) {
    controle("(s) le chemin differe photo est dans le worker", false, "introuvable");
  } else {
    function chargerPhoto(hektorEchoue) {
      const journal = [];
      const patches = [];
      const faux = {
        supabaseRequest: async (chemin, options) => {
          if (!options || options.method === "GET") {
            journal.push("lecture_ligne");
            return [{ id: "pho-1", hektor_annonce_id: "62087", filename: "salon.jpg",
                      storage_path: "annonces/62087/photos/pho-1/salon.jpg",
                      mime_type: "image/jpeg", metadata_json: {} }];
          }
          journal.push("patch_ligne");
          patches.push(JSON.parse(options.body));
          return null;
        },
        downloadStorageObject: async () => {
          journal.push("lecture_fichier");
          return { buffer: Buffer.alloc(1024, 5), mimeType: "image/jpeg" };
        },
        persistProvidedPhotoFile: async () => {
          journal.push("ECRITURE_SERVEUR");
          return { local_path: "C:/serveur/annonces/62087/photos/pho-1/salon.jpg" };
        },
        shouldKeepCloud: () => true,
        ensureHektorExecutionContext: async () => { journal.push("contexte_hektor"); },
        fetchConsolePhotoEntries: async () => (journal.push("galerie"), [{ hektor_photo_id: "1" }]),
        writeTempUploadFile: async () => ({ filePath: "/tmp/x.jpg", tempDir: "/tmp" }),
        uploadHektorPhotoWithPlaywright: async () => {
          journal.push("APPEL_HEKTOR");
          if (hektorEchoue) throw new Error("Playwright : Hektor injoignable");
          return { entries: [{ hektor_photo_id: "1" }, { hektor_photo_id: "42" }] };
        },
        upsertConsolePhotos: async () => { journal.push("reindexation"); return []; },
        enqueueRefreshConsoleDataJobBestEffort: async () => null,
        logJob: async () => { journal.push("journal"); },
        safeFilename: (n, f) => n || f,
        fs: { unlinkSync: () => {}, rmdirSync: () => {} },
      };
      // eslint-disable-next-line no-new-func
      const fn = new Function(...Object.keys(faux), `${blocPhoto}; return completerEnvoiPhotoDifferee;`)(
        ...Object.values(faux));
      return { fn, journal, patches };
    }

    let { fn, journal, patches } = chargerPhoto(false);
    let r = await fn({ id: "j" }, { hektor_annonce_id: "62087" }, { app_photo_id: "pho-1" });
    controle("(s) photo : le serveur AVANT Hektor",
      journal.indexOf("ECRITURE_SERVEUR") >= 0
        && journal.indexOf("APPEL_HEKTOR") > journal.indexOf("ECRITURE_SERVEUR"),
      journal.join(" > "));
    controle("(t) photo : le numero Hektor est adopte AVANT la reindexation",
      patches.some((p) => p.hektor_photo_id === "42")
        && journal.indexOf("patch_ligne") < journal.indexOf("reindexation"),
      `${JSON.stringify(patches)} | ${journal.join(" > ")}`);
    controle("(u) photo : statut « envoye »", r && r.envoi_hektor === "envoye", JSON.stringify(r));

    ({ fn, journal, patches } = chargerPhoto(true));
    let leve = null;
    try { r = await fn({ id: "j" }, { hektor_annonce_id: "62087" }, { app_photo_id: "pho-1" }); }
    catch (e) { leve = e.message; }
    controle("(v) photo : un echec Hektor NE LEVE PAS", leve === null, `a leve : ${leve}`);
    controle("(w) photo : le fichier est QUAND MEME sur notre serveur",
      journal.includes("ECRITURE_SERVEUR"), journal.join(" > "));
    controle("(x) photo : la ligne est marquee « echec »",
      patches.some((p) => p.envoi_hektor_statut === "echec"), JSON.stringify(patches));
  }

  // ⚠ Sans cette contrainte levee, l'app ne pourrait PAS creer une photo avant l'envoi.
  controle("(y) l'aiguillage photo existe",
    /if \(payload\.app_photo_id\) \{\s*return await completerEnvoiPhotoDifferee/.test(src),
    "le chemin differe photo n'est pas branche");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
