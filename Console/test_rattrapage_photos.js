// LE RAPATRIEMENT DES PHOTOS FREINE-T-IL, ET S'ARRETE-T-IL AU REFUS ?
//                                                                  25/09/2026
// Deux chemins telechargent des photos, et AUCUN des deux n'avait de frein :
//   - le worker      : fetchPublicBinary, appele par persistConsolePhotoFile
//   - le rattrapage  : Console/rattrapage_photos.js (444 431 photos)
//
// ⚠ LE PIEGE PROPRE AU PARALLELISME, et c'est le controle central de ce fichier :
//   un frein naif (« attendre INTERVALLE avant chaque appel ») donne a CHAQUE fil sa
//   propre cadence -- 8 fils vont alors 8 fois trop vite, et le frein ne freine rien.
//   Le frein doit RESERVER son tour avant d'attendre, pour que le debit GLOBAL tienne.
//
// Il fait tourner LES VRAIES FONCTIONS des deux fichiers, avec un faux serveur.
// N'APPELLE NI HEKTOR NI LE CDN NI SUPABASE. N'ECRIT RIEN hors du dossier temporaire.

const fs = require("fs");
const os = require("os");
const path = require("path");

const SCRIPT = path.join(__dirname, "rattrapage_photos.js");
const WORKER = path.join(__dirname, "console_job_worker.js");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function tranche(src, debutMarque, finMarque) {
  const d = src.indexOf(debutMarque);
  const i = src.indexOf(finMarque);
  if (d < 0 || i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(d, f + 2);
}

const srcScript = fs.readFileSync(SCRIPT, "utf8");
const srcWorker = fs.readFileSync(WORKER, "utf8");

const reponse = (status, taille = 1024) => ({
  status, ok: status >= 200 && status < 300,
  arrayBuffer: async () => new ArrayBuffer(taille),
  headers: { get: () => "image/jpeg" },
});

(async () => {
  // ═══ ① LE FREIN PARTAGE DU RATTRAPAGE ════════════════════════════════════
  const blocFrein = tranche(srcScript, "let prochain = 0;", "async function frein(");
  if (!blocFrein) {
    controle("(0) le frein est dans le rattrapage", false, "introuvable");
  } else {
    const INTERVALLE = 40;
    // eslint-disable-next-line no-new-func
    const { frein } = new Function("INTERVALLE", "sleep",
      `${blocFrein}; return { frein };`
    )(INTERVALLE, (ms) => new Promise((r) => setTimeout(r, ms)));

    // 24 jetons pris par 8 fils EN PARALLELE. Si le frein etait par fil, ce serait
    // ~3 x 40 = 120 ms. Partage, c'est ~23 x 40 = 920 ms.
    const N = 24, FILS = 8;
    let pris = 0;
    const t0 = Date.now();
    await Promise.all(Array.from({ length: FILS }, async () => {
      while (pris < N) { pris += 1; await frein(); }
    }));
    const ecoule = Date.now() - t0;
    const attenduPartage = (N - 1) * INTERVALLE;
    const attenduParFil = (N / FILS) * INTERVALLE;
    controle(`(a) le frein est PARTAGE : ${N} jetons par ${FILS} fils >= ${attenduPartage} ms`,
      ecoule >= attenduPartage * 0.8,
      `${ecoule} ms -- proche de ${attenduParFil} ms = chaque fil a sa cadence, le frein ne freine rien`);

    // et il ne bride pas inutilement : pas plus du double
    controle("(b) il ne bride pas au-dela du necessaire",
      ecoule <= attenduPartage * 2.2, `${ecoule} ms pour ${attenduPartage} ms attendus`);
  }

  // ═══ ② L'ARRET AU REFUS, DANS LE RATTRAPAGE ══════════════════════════════
  const blocDl = tranche(srcScript, "class ArretTelechargement", "async function telecharger(");
  if (!blocDl) {
    controle("(0b) telecharger est dans le rattrapage", false, "introuvable");
  } else {
    function charger(fauxFetch) {
      // eslint-disable-next-line no-new-func
      return new Function("fetch", "INTERVALLE", "Buffer",
        `${blocDl}; return { telecharger, ArretTelechargement };`
      )(fauxFetch, 0, Buffer);
    }
    async function verdict(code) {
      const m = charger(async () => reponse(code));
      try { await m.telecharger("https://exemple.invalid/p.jpg"); return { arret: false, type: "aucune erreur" }; }
      catch (e) { return { arret: e.name === "ArretTelechargement", type: e.name, msg: e.message }; }
    }
    for (const c of [401, 403, 429, 503]) {
      const v = await verdict(c);
      controle(`(c) rattrapage : un ${c} ARRETE tout`, v.arret === true, `${v.type} : ${v.msg || ""}`);
    }
    // ⚠ LE 404 EST DIFFERENT : une photo effacee chez Hektor ne concerne QU'ELLE.
    // L'arreter ferait echouer tout le rapatriement sur une seule image disparue.
    const v404 = await verdict(404);
    controle("(d) rattrapage : un 404 n'arrete PAS (photo disparue, on continue)",
      v404.type === "Error" && !v404.arret, `${v404.type}`);
    const v500 = await verdict(500);
    controle("(e) rattrapage : un 500 isole n'arrete PAS", !v500.arret, `${v500.type}`);
    const ok = await verdict(200);
    controle("(f) rattrapage : une reponse normale rend le fichier", ok.type === "aucune erreur", ok.type);
  }

  // ═══ ③ LE MEME FREIN DANS LE WORKER ══════════════════════════════════════
  const blocWorker = tranche(srcWorker, "const CDN_MIN_INTERVAL_MS", "async function fetchPublicBinary(");
  if (!blocWorker) {
    controle("(0c) le frein CDN est dans le worker", false, "introuvable");
  } else {
    function chargerWorker(fauxFetch, intervalle = 60) {
      process.env.CONSOLE_CDN_MIN_REQUEST_INTERVAL_MS = String(intervalle);
      process.env.CONSOLE_CDN_PAUSE_EVERY_N_REQUESTS = "0";
      // eslint-disable-next-line no-new-func
      return new Function("fetch", "sleep", "Buffer", "WORKER_ID", "process",
        `${blocWorker}; return { fetchPublicBinary, ArretTelechargement, freinCdn };`
      )(fauxFetch, (ms) => new Promise((r) => setTimeout(r, ms)), Buffer, "test", process);
    }
    const m = chargerWorker(async () => reponse(200), 60);
    const t0 = Date.now();
    await m.fetchPublicBinary("https://exemple.invalid/1.jpg");
    await m.fetchPublicBinary("https://exemple.invalid/2.jpg");
    await m.fetchPublicBinary("https://exemple.invalid/3.jpg");
    const ecoule = Date.now() - t0;
    controle("(g) worker : 3 telechargements sont espaces (>= 120 ms)",
      ecoule >= 100, `${ecoule} ms -- le frein CDN ne freine pas`);

    const m403 = chargerWorker(async () => reponse(403), 0);
    let arret = false;
    try { await m403.fetchPublicBinary("https://exemple.invalid/x.jpg"); }
    catch (e) { arret = e.name === "ArretTelechargement"; }
    controle("(h) worker : un 403 leve ArretTelechargement", arret, "erreur ordinaire");

    const m404 = chargerWorker(async () => reponse(404), 0);
    let ordinaire = false;
    try { await m404.fetchPublicBinary("https://exemple.invalid/x.jpg"); }
    catch (e) { ordinaire = e.name !== "ArretTelechargement"; }
    controle("(i) worker : un 404 reste une erreur ordinaire", ordinaire, "a arrete a tort");

    // Les reglages du CDN ne doivent PAS etre ceux de Hektor : les melanger
    // reglerait les deux d'un coup, alors que ce sont deux serveurs et deux quotas.
    controle("(j) les reglages CDN sont SEPARES de ceux de Hektor",
      /CONSOLE_CDN_MIN_REQUEST_INTERVAL_MS/.test(srcWorker)
        && !/CONSOLE_CDN_MIN_REQUEST_INTERVAL_MS[\s\S]{0,200}HEKTOR_MIN_REQUEST_INTERVAL_MS/.test(blocWorker),
      "les deux cadences sont melangees");
  }

  // ═══ ④ LA LECTURE DU MIROIR ══════════════════════════════════════════════
  const blocMiroir = tranche(srcScript, "function lireLeMiroir(", "function lireLeMiroir(");
  let Database = null;
  try { Database = require("node:sqlite").DatabaseSync; } catch (_) { /* Node < 22 */ }
  if (!blocMiroir || !Database) {
    console.log("  -- (④) lecture du miroir : controle saute (node:sqlite indisponible)");
  } else {
    const tmp = path.join(os.tmpdir(), `miroir_essai_${process.pid}.sqlite`);
    try { fs.rmSync(tmp, { force: true }); } catch (_) { /* vide */ }
    const db = new Database(tmp);
    db.exec("create table hektor_annonce_detail (hektor_annonce_id integer, images_json text)");
    const ins = db.prepare("insert into hektor_annonce_detail values (?, ?)");
    ins.run(101, JSON.stringify([
      { id: 1, order: "1", img: "a.jpg", visible: "1", legende: "salon",
        path: "https://cdn.test/original/a.jpg", pathTumb: "https://cdn.test/thumb/a.jpg" },
      { id: 2, order: "2", img: "b.jpg", visible: "0", legende: null,
        path: "https://cdn.test/original/b.jpg", pathTumb: "" },
      { id: 1, order: "1", img: "a.jpg", visible: "1", path: "https://cdn.test/original/a.jpg" }, // DOUBLON
      { id: 3, img: "c.jpg", path: "" },                    // sans url  -> ecartee
      { order: "9", img: "d.jpg", path: "https://cdn.test/d.jpg" }, // sans id -> ecartee
    ]));
    ins.run(102, "pas du json");                            // illisible -> ignoree
    ins.run(103, JSON.stringify([]));                       // vide
    db.close();

    // eslint-disable-next-line no-new-func
    const { lireLeMiroir } = new Function("require", "fs", "MIROIR",
      `${blocMiroir}; return { lireLeMiroir };`)(require, fs, tmp);
    const p = lireLeMiroir();

    controle("(k) le miroir rend 2 photos (doublon et entrees incompletes ecartes)",
      p.length === 2, `${p.length} : ${p.map((x) => x.hektor_photo_id).join(",")}`);
    const a = p.find((x) => x.hektor_photo_id === "1");
    controle("(l) l'url ORIGINALE est preferee a la vignette",
      a && a.url === "https://cdn.test/original/a.jpg", a ? a.url : "absente");
    controle("(m) ordre, legende et nom de fichier sont repris",
      a && a.ordre === 1 && a.legende === "salon" && a.filename === "a.jpg", JSON.stringify(a));
    const b = p.find((x) => x.hektor_photo_id === "2");
    controle("(n) visible=0 est bien lu comme masquee", b && b.visible === false, JSON.stringify(b));
    controle("(o) une annonce au json illisible ne fait pas tomber la lecture",
      p.every((x) => x.hektor_annonce_id === "101"), "une autre annonce est passee");
    try { fs.rmSync(tmp, { force: true }); } catch (_) { /* vide */ }
  }

  // ═══ ⑤ L'EMPLACEMENT VIENT DU WORKER, IL N'EST PAS RECOPIE ═══════════════
  // Deux conventions divergeraient au premier ajustement, et les 444 431 photos
  // seraient retelechargees au passage suivant.
  controle("(p) le rattrapage IMPORTE localPhotoPath du worker",
    /require\("\.\/console_job_worker\.js"\)/.test(srcScript)
      && /localPhotoPath/.test(srcScript), "chemin recopie au lieu d'etre importe");
  controle("(q) il ne refabrique pas le chemin a la main",
    !/path\.join\([^)]*"photos"/.test(srcScript), "un chemin est construit en dur");
  controle("(r) le fichier est range sous l'identifiant de la LIGNE, comme le worker",
    /localPhotoPath\(p\.hektor_annonce_id, ligne\.id, nom\)/.test(srcScript),
    "range sous l'identifiant Hektor -> divergence avec le worker");
  controle("(s) il ne pousse rien dans Supabase Storage",
    !/uploadStorageObject|\/storage\/v1\/object/.test(srcScript), "un envoi vers le stockage existe");
  controle("(t) il ne parle jamais a Hektor",
    !/xmlrpc|la-boite-immo\.com\/admin|hektorFetch/.test(srcScript), "une requete Hektor existe");

  // ═══ ⑥ LES DEUX NUMEROS, TOUJOURS ════════════════════════════════════════
  // Regle du projet : une ligne porte NOTRE numero ET celui de Hektor. Les 1 397
  // lignes photo deja en place les ont toutes les deux (0 sans numero d'app).
  // Une table ancree sur le seul numero Hektor devient illisible a la coupure et
  // invisible au repointage -- defaut corrige le matin meme sur l'empreinte
  // documentaire, et que la 1re version de ce script reproduisait a l'identique.
  controle("(u) la ligne creee porte NOTRE numero",
    /app_dossier_id: numeroApp\.get\(p\.hektor_annonce_id\)/.test(srcScript),
    "app_dossier_id absent de la creation");
  controle("(v) elle porte aussi celui de Hektor",
    /hektor_annonce_id: p\.hektor_annonce_id/.test(srcScript), "numero Hektor absent");
  controle("(w) la correspondance est lue dans les QUATRE index",
    ["app_dossier_current", "app_archive_annonce_index_current",
     "app_historical_annonce_index_current", "app_brouillon_annonce_index_current"]
      .every((t2) => srcScript.includes(t2)),
    "un index manque -- les archives n'auraient pas de numero");
  controle("(x) une photo sans numero d'app est ECARTEE, pas ecrite a moitie",
    /sansNumeroApp/.test(srcScript) && /const connues = photos\.filter/.test(srcScript),
    "les photos sans numero seraient indexees quand meme");

  // le garde-fou du paquet, execute pour de vrai
  const blocGarde = (() => {
    const i = srcScript.indexOf("const muettes = paquet.filter");
    if (i < 0) return null;
    // ⚠ PAS la 1re accolade fermante apres le throw : le message est un gabarit de
    // chaine, et `${muettes.length}` en contient une. On va jusqu'a la fermeture du
    // `if`, seule a cette indentation. (1re version du test fausse pour cette raison.)
    const f = srcScript.indexOf("\n    }\n", i);
    return f < 0 ? null : srcScript.slice(i, f + 7);
  })();
  if (!blocGarde) {
    controle("(y) le garde-fou du paquet existe", false, "introuvable");
  } else {
    const essai = (paquet) => {
      try {
        // eslint-disable-next-line no-new-func
        new Function("paquet", `${blocGarde}; return "pose";`)(paquet);
        return "pose";
      } catch (e) { return e.message; }
    };
    controle("(y) un paquet complet passe",
      essai([{ app_dossier_id: 12 }, { app_dossier_id: 13 }]) === "pose", "refuse a tort");
    controle("(z) un paquet avec UNE ligne muette est REFUSE EN ENTIER",
      /REFUS/.test(essai([{ app_dossier_id: 12 }, { app_dossier_id: undefined }])),
      "la ligne muette serait posee");
  }

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
