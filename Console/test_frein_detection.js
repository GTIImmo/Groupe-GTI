// LA DETECTION FREINE-T-ELLE, ET S'ARRETE-T-ELLE QUAND HEKTOR NOUS ECARTE ?
//                                                                  25/09/2026
// enqueue_console_sync_jobs.js lisait Hektor avec un fetch NU : aucune cadence, et un 403
// etait compte dans lectures_ko puis IGNORE -- le balayage continuait, jusqu'a 13 000
// requetes contre un serveur qui venait de nous fermer la porte. C'est la mecanique exacte
// du bannissement d'IP du 20/08.
//
// CE TEST FAIT TOURNER LES VRAIES FONCTIONS du fichier, avec un faux fetch. Il ne rejoue
// pas la regle : casser le frein ou l'arret doit le faire ECHOUER.
//
// La distinction est le coeur du correctif, et les deux sens comptent :
//   - 403 / 429 / 503 / session morte / connexion refusee  -> ON ARRETE
//   - 500 / timeout isole                                  -> on passe, on ne conclut rien
// Tout arreter perdrait le balayage sur un hoquet ; tout ignorer prolonge le bannissement.
//
//   node Console/test_frein_detection.js
// N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT RIEN.

const fs = require("fs");
const path = require("path");

const FICHIER = path.join(__dirname, "enqueue_console_sync_jobs.js");
const WORKER = path.join(__dirname, "console_job_worker.js");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

// ── on charge le bloc reel (frein + lecture) sans executer main() ─────────────
// Intervalle raccourci AVANT l'evaluation : les constantes lisent process.env a ce
// moment-la. Le test prouve donc aussi que le reglage passe bien par l'environnement.
const INTERVALLE = 250;
process.env.CONSOLE_HEKTOR_MIN_REQUEST_INTERVAL_MS = String(INTERVALLE);
process.env.CONSOLE_HEKTOR_PAUSE_EVERY_N_REQUESTS = "0";
process.env.CONSOLE_HEKTOR_WAVE_EVERY_N_REQUESTS = "0";

function charger(fauxFetch) {
  const src = fs.readFileSync(FICHIER, "utf8");
  const debut = src.indexOf("const MIN_INTERVAL_MS =");
  const marque = "async function fetchDocumentsHtml(";
  const i = src.indexOf(marque);
  if (debut < 0 || i < 0) return null;
  const fin = src.indexOf("\n}", i);
  if (fin < 0) return null;
  const bloc = src.slice(debut, fin + 2);
  // eslint-disable-next-line no-new-func
  return new Function("fetch", "HEKTOR_XMLRPC", "require", "DETECT_STORAGE_STATE",
    `${bloc}; return { fetchDocumentsHtml, ArretBalayage, freinHektor };`
  )(fauxFetch, "https://exemple.invalid/xmlrpc.php", require, "");
}

const reponse = (status, corps = "<html>ok</html>") => ({
  status, ok: status >= 200 && status < 300, text: async () => corps,
});

(async () => {
  // ── ① LE FREIN ────────────────────────────────────────────────────────────
  let appels = 0;
  let mod = charger(async () => { appels += 1; return reponse(200); });
  if (!mod) {
    controle("(0) le bloc frein + lecture est dans le fichier", false, "introuvable");
  } else {
    const t0 = Date.now();
    await mod.fetchDocumentsHtml("1", "c=1");
    await mod.fetchDocumentsHtml("2", "c=1");
    await mod.fetchDocumentsHtml("3", "c=1");
    const ecoule = Date.now() - t0;
    // 3 lectures = au moins 2 intervalles entre elles
    controle(`(a) 3 lectures sont espacees (>= ${2 * INTERVALLE} ms)`,
      ecoule >= 2 * INTERVALLE - 40, `${ecoule} ms seulement -- le frein ne freine pas`);
    controle("(b) les 3 lectures ont bien eu lieu", appels === 3, `${appels} appel(s)`);
  }

  // ── ② CE QUI DOIT ARRETER LE BALAYAGE ─────────────────────────────────────
  async function verdict(fauxFetch, id = "62087") {
    const m = charger(fauxFetch);
    try {
      await m.fetchDocumentsHtml(id, "c=1");
      return { type: "aucune erreur" };
    } catch (error) {
      return { type: error.name, message: error.message, arret: error.name === "ArretBalayage" };
    }
  }

  for (const code of [403, 401, 429, 503]) {
    const v = await verdict(async () => reponse(code));
    controle(`(c) un ${code} ARRETE le balayage`, v.arret === true, `${v.type} : ${v.message || ""}`);
  }

  let v = await verdict(async () => reponse(200, '<form><input type="password" name="pwd"></form>'));
  controle("(d) une page de login (session morte) ARRETE le balayage", v.arret === true, `${v.type}`);

  v = await verdict(async () => { const e = new Error("fetch failed"); e.cause = { code: "ECONNREFUSED" }; throw e; });
  controle("(e) une connexion refusee ARRETE le balayage", v.arret === true, `${v.type} : ${v.message || ""}`);

  // ── ③ CE QUI NE DOIT PAS L'ARRETER ────────────────────────────────────────
  v = await verdict(async () => reponse(500));
  controle("(f) un 500 isole n'arrete PAS (lecture ratee, on continue)",
    v.type === "Error" && !v.arret, `${v.type} : ${v.message || ""}`);

  v = await verdict(async () => { const e = new Error("The operation was aborted"); e.name = "AbortError"; throw e; });
  controle("(g) un timeout isole n'arrete PAS", !v.arret, `${v.type}`);

  v = await verdict(async () => reponse(200));
  controle("(h) une lecture normale rend la page", v.type === "aucune erreur", `${v.type}`);

  // ── ④ LA BOUCLE SORT, ET EMPILE QUAND MEME CE QUI EST TROUVE ──────────────
  const src = fs.readFileSync(FICHIER, "utf8");
  controle("(i) la boucle sort sur ArretBalayage",
    /if \(error instanceof ArretBalayage\) \{[\s\S]{0,120}?break;/.test(src), "pas de break");
  const iBreak = src.search(/stats\.arret = error\.motif;/);
  const iEmpile = src.search(/for \(let i = 0; i < aSynchroniser\.length; i \+= args\.batchSize\)/);
  controle("(i2) l'enfilage vient APRES la boucle : le travail fait n'est pas perdu",
    iBreak > 0 && iEmpile > iBreak, `break=${iBreak} enfilage=${iEmpile}`);
  controle("(i3) le motif d'arret remonte dans le compte rendu",
    /arret: null/.test(src), "stats.arret absent");

  // ── ⑤ UN SEUL REGLAGE POUR LES DEUX CHEMINS ───────────────────────────────
  // Dupliquer les valeurs en dur ferait diverger les deux cadences au premier ajustement :
  // on croirait freiner alors qu'un des deux chemins galoperait.
  const worker = fs.readFileSync(WORKER, "utf8");
  const variables = [
    "CONSOLE_HEKTOR_MIN_REQUEST_INTERVAL_MS",
    "CONSOLE_HEKTOR_PAUSE_EVERY_N_REQUESTS",
    "CONSOLE_HEKTOR_LONG_PAUSE_MS",
    "CONSOLE_HEKTOR_WAVE_EVERY_N_REQUESTS",
    "CONSOLE_HEKTOR_WAVE_PAUSE_MS",
  ];
  const manquantes = variables.filter((v2) => !(src.includes(v2) && worker.includes(v2)));
  controle("(j) les 5 reglages de cadence sont les MEMES que ceux du worker",
    manquantes.length === 0, `absente(s) d'un des deux : ${manquantes.join(", ")}`);

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
