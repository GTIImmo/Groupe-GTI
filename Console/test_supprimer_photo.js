/**
 * EPREUVE : SUPPRIMER UNE PHOTO -- chantier ③, bloc 2 (14/10/2026).
 *
 * Le geste n'existait pas : la commande Hektor etait inconnue jusqu'au releve en lecture
 * seule du 14/10 (Console/sonde_photos_suppression.js). Il est la jumelle du geste
 * « supprimer un document », et cette epreuve garde ce qui fait sa surete :
 *
 *   la PREUVE AVANT  -> la COMMANDE  -> la PREUVE APRES -> la RENUMEROTATION
 *   -> le JOURNAL (condition, pas effet de bord) -> PUIS nos copies
 *
 * ⚠ ELLE N'EXECUTE PAS LE WORKER : elle DECOUPE handleDeleteHektorPhoto dans le fichier
 *   et la fait tourner avec des doublures. N'appelle ni Hektor ni Supabase.
 *
 *   node Console/test_supprimer_photo.js
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

const bloc = tranche("async function handleDeleteHektorPhoto(");
const XMLRPC = "https://hektor.test/admin/xmlrpc.php";

const PHOTO = {
  id: "uuid-photo-1", app_dossier_id: 3828957, hektor_annonce_id: "62774",
  hektor_photo_id: "115569", filename: "salon.jpg",
  storage_path: "annonces/62774/photos/uuid-photo-1/salon.jpg",
  metadata_json: { local_archive_path: "C:/serveur/annonces/62774/photos/uuid-photo-1/salon.jpg" },
  derives_json: {
    w400: { chemin: "3828957/uuid-photo-1/w400.jpg" },
    w1600: { chemin: "3828957/uuid-photo-1/w1600.jpg" },
  },
};

function entree(id, visible, ordre, fichier, annonce = "62774", peutSupprimer = true) {
  return {
    hektor_photo_id: id, visible, sort_order: ordre,
    source_json: {
      delete_filename: fichier, delete_annonce_id: annonce, delete_photo_id: id,
      actions: { can_delete: peutSupprimer },
    },
  };
}

// La galerie de Hektor : 3 visibles + 1 masquee. On supprime 115569 (position 2).
const GALERIE = [
  entree("115564", true, 1, "aaa.jpg"),
  entree("115569", true, 2, "bbb.jpg"),
  entree("115573", true, 3, "ccc.jpg"),
  entree("115580", false, 1, "ddd.jpg"),
];

function charger(options = {}) {
  const {
    photo = PHOTO,
    galerieAvant = GALERIE,
    hektorConfirme = true,
    journalEchoue = false,
    renumerotationEchoue = false,
  } = options;
  const journal = [];
  const appelsHektor = [];
  let lecture = 0;
  const faux = {
    safeJsonParse: (x) => (typeof x === "string" ? JSON.parse(x) : x),
    loadDossier: async () => ({ hektor_annonce_id: "62774", app_dossier_id: 3828957 }),
    ensureHektorExecutionContext: async () => { journal.push("contexte"); },
    supabaseRequest: async (chemin, opts = {}) => {
      if ((opts.method || "GET") === "GET") return photo ? [photo] : [];
      journal.push(`SUPABASE_${opts.method}:${chemin.split("?")[0]}`);
      return null;
    },
    fetchConsolePhotoEntries: async () => {
      lecture += 1;
      journal.push(`LECTURE_GALERIE_${lecture}`);
      if (lecture === 1) return galerieAvant;
      return hektorConfirme
        ? galerieAvant.filter((e) => e.hektor_photo_id !== "115569")
        : galerieAvant;
    },
    hektorFetch: async (url, opts = {}) => {
      appelsHektor.push({ url, methode: opts.method || "GET", corps: opts.body || null });
      journal.push(`HEKTOR_${opts.method || "GET"}`);
      if (renumerotationEchoue && opts.method === "POST") throw new Error("Hektor 500 on ordonne_photos");
      return { text: "" };
    },
    XMLRPC_URL: XMLRPC,
    sleep: async () => {},
    logJob: async (_id, _type, _etat, message) => { journal.push(`JOURNAL_TRAVAIL:${message}`); },
    insertDeletedPhotoLog: async (_job, donnees) => {
      journal.push("JOURNAL_SUPPRESSION");
      if (journalEchoue) throw new Error("journal de suppression de la photo non ecrit : on ne detruit pas");
      faux._journalEcrit = donnees;
      return { id: 1 };
    },
    deleteStorageObject: async (chemin) => { journal.push(`DETRUIT_CLOUD:${chemin}`); },
    isReadableFile: () => true,
    fs: { unlinkSync: (p) => { journal.push(`DETRUIT_SERVEUR:${p}`); } },
    storageRequest: async (chemin, opts) => { journal.push(`DETRUIT_DERIVE:${opts.bucket}/${chemin}`); },
    COFFRE_PHOTO_PUBLIC: "gti-photo",
    upsertConsolePhotos: async (_d, entries) => { journal.push(`REINDEX:${entries.length}`); return []; },
    enqueueRefreshConsoleDataJobBestEffort: async () => null,
  };
  // eslint-disable-next-line no-new-func
  const fn = new Function(...Object.keys(faux), `${bloc}; return handleDeleteHektorPhoto;`)(
    ...Object.values(faux));
  return { fn, journal, appelsHektor, faux };
}

const travail = (payload = { photo_id: "uuid-photo-1" }) => ({ id: "job-9", requested_by: "u-1", payload_json: payload });
const destructions = (journal) => journal.filter((e) => /^DETRUIT_|^SUPABASE_DELETE/.test(e));

(async () => {
  console.log("\nSupprimer une photo -- la preuve avant, la preuve apres, le journal, puis nos copies\n");
  if (!bloc) {
    controle("(0) le geste est dans le worker", false, "handleDeleteHektorPhoto introuvable");
  } else {
    // ── (A) LE CAS NORMAL ───────────────────────────────────────────────────
    let { fn, journal, appelsHektor, faux } = charger();
    let r = await fn(travail());

    const get = appelsHektor.find((a) => a.methode === "GET");
    controle("(a) la commande est celle de la page de Hektor",
      get && get.url === `${XMLRPC}?mode=delete_img&img=bbb.jpg&idann=62774&table=ordre_img`,
      get && get.url);
    controle("(b) ⚠ le fichier vient de la galerie RELUE, pas de notre copie",
      get && get.url.includes("img=bbb.jpg") && !get.url.includes("salon.jpg"), get && get.url);

    const posts = appelsHektor.filter((a) => a.methode === "POST");
    controle("(c) la renumerotation porte sur les DEUX listes, comme saveOrder",
      posts.length === 2 && /div=liste_photos&/.test(posts[0].corps) && /div=liste_photos_hidden&/.test(posts[1].corps),
      JSON.stringify(posts.map((p) => p.corps)));
    controle("(d) ⭐ avec l'ordre RELU chez Hektor, sans la photo supprimee",
      posts[0] && posts[0].corps.startsWith("liste_photos[]=115564&liste_photos[]=115573&mode=ordonne_photos")
        && posts[1].corps.startsWith("liste_photos_hidden[]=115580&mode=ordonne_photos"),
      posts.map((p) => p.corps).join(" || "));
    controle("(e) l'annonce est donnee a la renumerotation",
      posts.every((p) => p.corps.includes("&idann=62774&")), posts.map((p) => p.corps).join(" || "));

    const iJournal = journal.indexOf("JOURNAL_SUPPRESSION");
    const iPremiereDestruction = journal.findIndex((e) => /^DETRUIT_|^SUPABASE_DELETE/.test(e));
    controle("(f) ⚠ LE JOURNAL S'ECRIT AVANT LA PREMIERE DESTRUCTION",
      iJournal >= 0 && iPremiereDestruction > iJournal, journal.join(" > "));
    controle("(g) et APRES la preuve que Hektor a supprime",
      iJournal > journal.indexOf("LECTURE_GALERIE_2"), journal.join(" > "));
    controle("(h) le fichier cloud est detruit",
      journal.includes(`DETRUIT_CLOUD:${PHOTO.storage_path}`), journal.join(" > "));
    controle("(i) le fichier serveur est detruit",
      journal.includes(`DETRUIT_SERVEUR:${PHOTO.metadata_json.local_archive_path}`), journal.join(" > "));
    controle("(j) ⭐ les DEUX derives publics partent, dans le coffre PUBLIC",
      journal.includes("DETRUIT_DERIVE:gti-photo/3828957/uuid-photo-1/w400.jpg")
        && journal.includes("DETRUIT_DERIVE:gti-photo/3828957/uuid-photo-1/w1600.jpg"), journal.join(" > "));
    controle("(k) la ligne est supprimee (decision du 13/10, exception VOULUE a G.10bis)",
      journal.includes("SUPABASE_DELETE:app_console_photo"), journal.join(" > "));
    controle("(l) l'index est relu avec la galerie d'apres",
      journal.includes("REINDEX:3"), journal.join(" > "));
    controle("(m) le journal emporte la ligne entiere et ce qui a ete detruit",
      faux._journalEcrit && faux._journalEcrit.before_json === PHOTO
        && faux._journalEcrit.result_json.derives_publics.length === 2
        && faux._journalEcrit.result_json.hektor_confirme === true,
      JSON.stringify(faux._journalEcrit && faux._journalEcrit.result_json));
    controle("(n) le compte rendu le dit", r && r.derives_supprimes === 2 && r.disparues_en_trop.length === 0,
      JSON.stringify(r));

    // ── (B) HEKTOR NE CONFIRME PAS ──────────────────────────────────────────
    ({ fn, journal, appelsHektor } = charger({ hektorConfirme: false }));
    let leve = null;
    try { await fn(travail()); } catch (e) { leve = e.message; }
    controle("(o) Hektor ne confirme pas -> ca leve",
      leve && /non confirmee/.test(leve), `a leve : ${leve}`);
    controle("(p) ⭐ TEMOIN INVERSE : alors RIEN n'est detruit chez nous, et pas de journal",
      destructions(journal).length === 0 && !journal.includes("JOURNAL_SUPPRESSION"), journal.join(" > "));
    controle("(q) et on ne renumerote pas une liste qui n'a pas change",
      !appelsHektor.some((a) => a.methode === "POST"), JSON.stringify(appelsHektor));

    // ── (C) LE JOURNAL NE S'ECRIT PAS ───────────────────────────────────────
    ({ fn, journal } = charger({ journalEchoue: true }));
    leve = null;
    try { await fn(travail()); } catch (e) { leve = e.message; }
    controle("(r) ⭐ le journal echoue -> ON NE DETRUIT PAS (nos copies restent)",
      leve && /non ecrit/.test(leve) && destructions(journal).length === 0, `${leve} | ${journal.join(" > ")}`);

    // ── (D) UNE PHOTO PAS ENCORE CHEZ HEKTOR ────────────────────────────────
    ({ fn, journal, appelsHektor } = charger({ photo: { ...PHOTO, hektor_photo_id: null } }));
    leve = null;
    try { await fn(travail()); } catch (e) { leve = e.message; }
    controle("(s) une photo pas encore envoyee est REFUSEE (on ne la supprime pas en vol)",
      leve && /pas encore chez Hektor/.test(leve) && appelsHektor.length === 0, `${leve}`);

    // ── (E) ABSENTE DE LA GALERIE AVANT ─────────────────────────────────────
    ({ fn, journal, appelsHektor } = charger({ galerieAvant: GALERIE.filter((e) => e.hektor_photo_id !== "115569") }));
    leve = null;
    try { await fn(travail()); } catch (e) { leve = e.message; }
    controle("(t) absente de la galerie avant -> refus, AUCUNE commande envoyee",
      leve && /introuvable avant/.test(leve) && !appelsHektor.some((a) => /delete_img/.test(a.url)), `${leve}`);

    // ── (F) HEKTOR NE PROPOSE PAS LA SUPPRESSION ────────────────────────────
    const sansBouton = GALERIE.map((e) => (e.hektor_photo_id === "115569" ? entree("115569", true, 2, "bbb.jpg", "62774", false) : e));
    ({ fn, appelsHektor } = charger({ galerieAvant: sansBouton }));
    leve = null;
    try { await fn(travail()); } catch (e) { leve = e.message; }
    controle("(u) pas de bouton chez Hektor (droits ?) -> refus, AUCUNE commande",
      leve && /bouton absent/.test(leve) && appelsHektor.length === 0, `${leve}`);

    // ── (G) LA GALERIE DESIGNE UNE AUTRE ANNONCE ────────────────────────────
    const autreAnnonce = GALERIE.map((e) => (e.hektor_photo_id === "115569" ? entree("115569", true, 2, "bbb.jpg", "99999") : e));
    ({ fn, appelsHektor } = charger({ galerieAvant: autreAnnonce }));
    leve = null;
    try { await fn(travail()); } catch (e) { leve = e.message; }
    controle("(v) la galerie designe une autre annonce -> refus, AUCUNE commande",
      leve && /designe l'annonce 99999/.test(leve) && appelsHektor.length === 0, `${leve}`);

    // ── (H) LA RENUMEROTATION ECHOUE ────────────────────────────────────────
    ({ fn, journal } = charger({ renumerotationEchoue: true }));
    leve = null;
    try { r = await fn(travail()); } catch (e) { leve = e.message; }
    controle("(w) ⚠ la renumerotation echoue -> on ne leve PAS (la photo EST supprimee chez Hektor)",
      leve === null && r && r.renumerotation.liste_photos.ok === false, `a leve : ${leve}`);
    controle("(x) on le DIT au journal du travail",
      journal.some((e) => /n'a pas pu etre renumerote/.test(e)), journal.join(" > "));
    controle("(y) et le journal + nos destructions ont bien lieu quand meme",
      journal.includes("JOURNAL_SUPPRESSION") && destructions(journal).length === 5, journal.join(" > "));
    // 5 operations : le fichier cloud, le fichier serveur, les DEUX derives publics, la ligne.
  }

  // ── LE BRANCHEMENT ────────────────────────────────────────────────────────
  const docTypes = (src.match(/const DOCUMENT_JOB_TYPES = new Set\(\[[\s\S]*?\]\);/) || [""])[0];
  controle("(z1) le service documents prend ce travail", docTypes.includes('"delete_hektor_photo"'), "absent de DOCUMENT_JOB_TYPES");
  controle("(z2) l'aiguillage mene au geste",
    /case "delete_hektor_photo":\s*return handleDeleteHektorPhoto\(job\);/.test(src), "aiguillage absent");
  const notifier = (src.match(/const JOB_TYPES_A_NOTIFIER = new Set\(\[[\s\S]*?\]\);/) || [""])[0];
  controle("(z3) un echec est notifie a celui qui l'a demande", notifier.includes('"delete_hektor_photo"'), "absent des notifications");
  controle("(z4) le geste a un libelle lisible", /delete_hektor_photo: "La suppression de la photo"/.test(src), "libelle absent");
  controle("(z5) ⚠ la SYNCHRO garde sa regle : upsertConsolePhotos ne supprime toujours aucune ligne",
    !/method: "DELETE"/.test(tranche("async function upsertConsolePhotos(") || "method: \"DELETE\""),
    "un DELETE est apparu dans la synchro");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
