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
// A.2 P8-0 / G1 (06/11) : l'anti-doublon, decoupe du VRAI worker lui aussi.
const blocAideG1 = [tranche("async function numerosHektorDejaPris("), tranche("function documentNonReclame(")].join("\n");

function charger(hektorEchoue, indexationEchoue = false, opts = {}) {
  const journal = [];          // l'ORDRE des gestes, c'est ce qu'on verifie
  const patches = [];
  const faux = {
    supabaseRequest: async (chemin, options) => {
      if (!options || options.method === "GET") {
        journal.push("lecture_ligne");
        const ligne = { id: "doc-1", hektor_annonce_id: "62087", document_name: "Mandat.pdf",
          visibility: "private", storage_path: "annonces/62087/documents/doc-1/Mandat.pdf",
          sha256: "S-NOTRE", created_at: "2026-11-06T08:00:00Z",
          metadata_json: {}, ...(opts.ligne || {}) };
        // P8-0 / G1 : la lecture des AUTRES lignes de l'annonce (numerosHektorDejaPris)
        if (/select=id,hektor_document_id/.test(chemin)) return [ligne, ...(opts.autres || [])];
        return [ligne];
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
    upsertConsoleDocuments: async () => {
      journal.push("reindexation");
      if (indexationEchoue) {
        throw new Error('Supabase 409 on app_console_document?on_conflict=hektor_annonce_id,source,hektor_document_id: duplicate key value violates unique constraint "app_console_document_pkey"');
      }
      return [];
    },
    enqueueRefreshConsoleDataJobBestEffort: async () => { journal.push("rafraichissement"); return null; },
    logJob: async () => { journal.push("journal"); },
    safeFilename: (n, f) => n || f,
    isReadableFile: (chemin) => Boolean(opts.copieServeurLisible && chemin),
    readLocalArchiveFile: () => { journal.push("LECTURE_SERVEUR"); return { buffer: Buffer.alloc(16, 1), mimeType: "application/pdf" }; },
    fetchConsoleDocumentEntries: async () => { journal.push("LISTE_HEKTOR"); return opts.entries || []; },
    // 3d / lot 2c : declaree pour que l'epreuve puisse PROUVER qu'elle ne sert pas
    // quand la ligne n'est pas en attente d'envoi.
    deleteStorageObject: async (chemin) => { journal.push(`SUPPRESSION:${chemin}`); },
  };
  // eslint-disable-next-line no-new-func
  const fn = new Function(...Object.keys(faux), `${bloc}; ${blocAideG1}; return completerEnvoiDocumentDiffere;`)(
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

    // ── ④ HEKTOR A LE FICHIER, MAIS NOTRE INDEXATION PLANTE (le cas du 19/10) ──
    // Le numero Hektor est deja pose sur la ligne : l'envoi est REUSSI. Le statut ne doit
    // pas passer a « echec », sinon l'app ment et la reprise renvoie un doublon.
    ({ fn, journal, patches } = charger(false, true));
    leve = null;
    try {
      r = await fn({ id: "job-3" }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    } catch (e) { leve = e.message; }
    controle("(n) l'indexation qui plante apres l'envoi NE LEVE PAS", leve === null, `a leve : ${leve}`);
    controle("(o) ⭐ le numero Hektor est bien pose sur la ligne",
      patches.some((p) => p.hektor_document_id === "H-99" && p.envoi_hektor_statut === "envoye"),
      JSON.stringify(patches));
    controle("(p) ⭐⭐ le statut ne repasse JAMAIS a « echec » (Hektor a le fichier)",
      !patches.some((p) => p.envoi_hektor_statut === "echec"), JSON.stringify(patches));
    controle("(q) le compte rendu dit « envoye » ET porte l'erreur d'indexation",
      r && r.envoi_hektor === "envoye" && r.hektor_document_id === "H-99" && /app_console_document_pkey/.test(String(r.indexation_erreur || "")),
      JSON.stringify(r));
    controle("(r) l'echec du rangement est ecrit au journal", journal.includes("journal"), journal.join(" > "));

    // ── ⑦ A.2 P8-0 / G1 (06/11) : L'ANTI-DOUBLON -- le cas de 59203 (23-24/10) ──
    // La ligne a deja ete tentee (« echec ») et Hektor a DEJA le fichier : on l'adopte, on ne le renvoie pas.
    const chezHektor = [{ hektor_document_id: "H-OLD", document_name: "Mandat.pdf", hektor_uploaded_document_id: "715224" }];
    ({ fn, journal, patches } = charger(false, false, { ligne: { envoi_hektor_statut: "echec" }, entries: chezHektor }));
    r = await fn({ id: "job-g1", attempt_count: 1 }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(g1) ⭐⭐ deja tente + Hektor a le fichier : AUCUN renvoi", !journal.includes("APPEL_HEKTOR"), journal.join(" > "));
    controle("(g1) ...et le numero de Hektor est ADOPTE, statut « envoye »",
      patches.some((p) => p.hektor_document_id === "H-OLD" && p.envoi_hektor_statut === "envoye"), JSON.stringify(patches));
    controle("(g1) ...le serveur garde quand meme sa copie, AVANT tout", journal.indexOf("ECRITURE_SERVEUR") >= 0 && journal.indexOf("ECRITURE_SERVEUR") < journal.indexOf("LISTE_HEKTOR"), journal.join(" > "));
    // Temoin : PREMIER essai (a_envoyer, 1re tentative) -> on envoie, sans regarder (pas de tentative a reprendre).
    ({ fn, journal, patches } = charger(false, false, { ligne: { envoi_hektor_statut: "a_envoyer" }, entries: chezHektor }));
    r = await fn({ id: "job-g1b", attempt_count: 1 }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(g2) TEMOIN : premier essai -> l'envoi part (on n'adopte rien a l'aveugle)", journal.includes("APPEL_HEKTOR") && !journal.includes("LISTE_HEKTOR"), journal.join(" > "));
    // Travail REJOUE (le worker est tombe apres l'envoi) : meme anti-doublon que l'echec.
    ({ fn, journal, patches } = charger(false, false, { ligne: { envoi_hektor_statut: "a_envoyer" }, entries: chezHektor }));
    r = await fn({ id: "job-g1c", attempt_count: 2 }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(g3) travail rejoue (tentative 2) -> adopte, pas renvoye", !journal.includes("APPEL_HEKTOR") && patches.some((p) => p.hektor_document_id === "H-OLD"), journal.join(" > "));
    // Le document du meme nom est un AUTRE document, deja reconnu par une autre ligne (autre empreinte) -> on envoie.
    ({ fn, journal, patches } = charger(false, false, { ligne: { envoi_hektor_statut: "echec" }, entries: chezHektor,
      autres: [{ id: "doc-autre", hektor_document_id: "H-OLD", document_name: "Mandat.pdf", source: "hektor_console_uploaded_private", sha256: "S-AUTRE" }] }));
    r = await fn({ id: "job-g1d", attempt_count: 1 }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(g4) ⭐ un AUTRE document du meme nom (deja reconnu) n'est jamais adopte : l'envoi part", journal.includes("APPEL_HEKTOR") && !patches.some((p) => p.hektor_document_id === "H-OLD"), journal.join(" > "));
    // La synchro a indexe ENTRE-TEMPS notre propre depot comme une ligne a part (meme nom, meme empreinte) -> adoptable.
    ({ fn, journal, patches } = charger(false, false, { ligne: { envoi_hektor_statut: "echec" }, entries: chezHektor,
      autres: [{ id: "doc-copie", hektor_document_id: "H-OLD", document_name: "Mandat.pdf", source: "hektor_console_uploaded_private", sha256: "S-NOTRE" }] }));
    r = await fn({ id: "job-g1e", attempt_count: 1 }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(g5) notre propre depot deja indexe a part (meme empreinte) -> adopte, pas renvoye", !journal.includes("APPEL_HEKTOR") && patches.some((p) => p.hektor_document_id === "H-OLD"), journal.join(" > "));

    // ── ⑧ A.2 P8-0 / G4 (06/11) : un document hors coffre part avec sa copie SERVEUR ──
    ({ fn, journal, patches } = charger(false, false, { ligne: { storage_path: null, metadata_json: { local_archive_path: "C:/serveur/m.pdf" } }, copieServeurLisible: true }));
    r = await fn({ id: "job-g4", attempt_count: 1 }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(g6) sans coffre : la copie serveur est lue, le depot part", journal.includes("LECTURE_SERVEUR") && !journal.includes("lecture_fichier") && journal.includes("APPEL_HEKTOR"), journal.join(" > "));
    ({ fn, journal, patches } = charger(false, false, { ligne: { storage_path: null, metadata_json: {} } }));
    leve = null;
    try { await fn({ id: "job-g4b", attempt_count: 1 }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" }); } catch (e) { leve = e.message; }
    controle("(g7) TEMOIN : ni coffre ni serveur -> refus clair « sans fichier »", /sans fichier/.test(String(leve || "")), String(leve));

    // TEMOIN INVERSE : si l'echec survient AVANT la pose du numero, c'est bien un echec d'envoi.
    ({ fn, journal, patches } = charger(true, true));
    r = await fn({ id: "job-4" }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(s) ⭐ TEMOIN INVERSE : Hektor sans reponse -> toujours « echec »",
      r && r.envoi_hektor === "echec" && patches.some((p) => p.envoi_hektor_statut === "echec"),
      JSON.stringify([r, patches]));
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

  // ── ④ LE FICHIER DEPOSE PAR L'APP EST DANS temp/ ─────────────────────
  //
  // 3d / lot 2c (14/10/2026). L'app cree la ligne AVANT l'envoi, avec le fichier encore
  // sous temp/uploads/<travail>/ et storage_status = 'pending_upload'.
  //
  // ⚠⚠ CE QUE CES EPREUVES EMPECHENT DE REVENIR : persistProvidedDocumentFile calcule
  //   `document.storage_path || <place definitive>`. Si on lui passe la ligne telle
  //   quelle, le `||` ne se declenche JAMAIS -- il garde le chemin temporaire comme
  //   domicile, marque la ligne « cloud_available », et le document vit dans temp/ pour
  //   toujours. Le jour d'un nettoyage des temporaires, on detruit un vrai document.
  if (bloc) {
    function chargerProvisoire(rangementRendUnePlace) {
      const journal = [];
      const vus = [];            // ce que le rangement a RECU : c'est le coeur de l'epreuve
      const faux = {
        supabaseRequest: async (chemin, options) => {
          if (!options || options.method === "GET") {
            return [{
              id: "doc-1", hektor_annonce_id: "62087", document_name: "Mandat.pdf",
              visibility: "private",
              storage_path: "temp/uploads/j-1/Mandat.pdf",
              storage_status: "pending_upload",
              metadata_json: {},
            }];
          }
          return null;
        },
        downloadStorageObject: async (chemin) => {
          journal.push(`LECTURE:${chemin}`);
          return { buffer: Buffer.alloc(2048, 3), mimeType: "application/pdf" };
        },
        persistProvidedDocumentFile: async (ligne) => {
          vus.push(ligne);
          journal.push("ECRITURE_SERVEUR");
          // Avec cloud : le rangement rend la place definitive. Sans cloud, il rend
          // ce qu'il a recu -- donc VIDE, et il n'y a plus de copie au coffre.
          return rangementRendUnePlace
            ? { local_path: "C:/serveur/x", storage_path: "annonces/62087/documents/doc-1/Mandat.pdf" }
            : { local_path: "C:/serveur/x", storage_path: null };
        },
        shouldKeepCloud: () => rangementRendUnePlace,
        ensureHektorExecutionContext: async () => {},
        envoyerDocumentAHektor: async () => ({
          entries: [{ hektor_document_id: "H-99" }], found: { hektor_document_id: "H-99" } }),
        upsertConsoleDocuments: async () => [],
        enqueueRefreshConsoleDataJobBestEffort: async () => null,
        logJob: async () => { journal.push("journal"); },
        safeFilename: (n, f) => n || f,
        isReadableFile: () => false,
        readLocalArchiveFile: () => ({ buffer: Buffer.alloc(16, 1), mimeType: "application/pdf" }),
        fetchConsoleDocumentEntries: async () => [],
        deleteStorageObject: async (chemin) => { journal.push(`SUPPRESSION:${chemin}`); },
      };
      // eslint-disable-next-line no-new-func
      const fn = new Function(...Object.keys(faux), `${bloc}; ${blocAideG1}; return completerEnvoiDocumentDiffere;`)(
        ...Object.values(faux));
      return { fn, journal, vus };
    }

    // (A) le cas courant : l'annonce va au coffre, la place change
    let { fn, journal, vus } = chargerProvisoire(true);
    await fn({ id: "job-1" }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });

    controle("(z1) le fichier est lu A SA PLACE PROVISOIRE",
      journal.includes("LECTURE:temp/uploads/j-1/Mandat.pdf"), journal.join(" > "));
    controle("(z2) ⚠ le rangement recoit storage_path VIDE, donc il calcule la place definitive",
      vus.length === 1 && !vus[0].storage_path,
      `recu : ${JSON.stringify(vus.map((v) => v.storage_path))}`);
    controle("(z3) ⚠ et le temporaire est RETIRE",
      journal.includes("SUPPRESSION:temp/uploads/j-1/Mandat.pdf"), journal.join(" > "));

    // (B) le temoin inverse : si le rangement ne rend AUCUNE place (pas de coffre),
    //     on ne supprime pas -- on ne detruit jamais sans savoir ou est le fichier.
    ({ fn, journal, vus } = chargerProvisoire(false));
    await fn({ id: "job-1" }, { hektor_annonce_id: "62087" }, { app_document_id: "doc-1" });
    controle("(z4) ⭐ TEMOIN INVERSE : sans nouvelle place, le temporaire est GARDE",
      !journal.some((e) => e.startsWith("SUPPRESSION:")), journal.join(" > "));
  }

  // ⚠ Sans cette contrainte levee, l'app ne pourrait PAS creer une photo avant l'envoi.
  controle("(y) l'aiguillage photo existe",
    /if \(payload\.app_photo_id\) \{\s*return await completerEnvoiPhotoDifferee/.test(src),
    "le chemin differe photo n'est pas branche");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
