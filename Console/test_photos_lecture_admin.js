// ⑧ LES PHOTOS SE LISENT EN ADMIN -- essai hors ligne de handleSyncHektorPhotos.   29/10/2026
//
// CE QU'ON EPROUVE, sur LE CODE REEL (fonctions decoupees dans le worker, montees dans un bac a sable avec un
// FAUX Hektor et une FAUSSE base qui notent les appels -- meme technique que test_p4a_mandant_creation.js) :
//   (1) cas courant : lecture en admin, AUCUNE bascule de compte, aucune connexion complete
//   (2) Hektor refuse (403) en admin : UNE bascule vers le negociateur, pas de connexion complete, relecture
//   (3) une photo presente chez nous manque a la lecture admin : relecture en negociateur AVANT de marquer,
//       et c'est la liste du negociateur qui part dans l'index
//   (4) une photo masquee invisible a l'admin est retrouvee par la relecture : rien n'est marque a tort
//   (5) interrupteur coupe (CONSOLE_PHOTOS_LECTURE_ADMIN=false) : exactement le chemin d'avant
//   (6) TEMOIN INVERSE : la version d'avant (le commit 15ea354, FIXE -- lecon du 27/10) basculait a CHAQUE lecture
//   (7) MUTANT : sans la garde des photos manquantes, le cas (3) marquerait la photo absente -> l'essai le voit
//
//     node Console/test_photos_lecture_admin.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");

const TEMOIN = "15ea354";
const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8").replace(/\r\n/g, "\n");
const echecs = [];
function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}
function tranche(texte, debut) {
  const i = texte.indexOf(debut);
  if (i < 0) return null;
  const f = texte.indexOf("\n}", i);
  return f < 0 ? null : texte.slice(i, f + 2);
}
function ligne(texte, debut) {
  const i = texte.indexOf(debut);
  return i < 0 ? null : texte.slice(i, texte.indexOf("\n", i));
}

// hektor : { admin: [ids], negociateur: [ids], adminRefuse: bool } -- un id « m… » est une masquee
function monter(texte, { hektor, base, env }) {
  const morceaux = ["async function handleSyncHektorPhotos(", "function isHektorForbiddenError("].map((n) => tranche(texte, n));
  if (morceaux.some((m) => !m)) return null;
  const garde = tranche(texte, "async function photosAbsentesDeLaLecture(");
  const constante = ligne(texte, "const PHOTOS_LECTURE_ADMIN =");
  const ctx = { console, JSON, String, Array, Set, Map, Number, Boolean, encodeURIComponent,
    process: { env: env || {} }, hektor, base, appels: [], journal: [], compte: { actuel: "admin" } };
  vm.createContext(ctx);
  vm.runInContext(`
    ${constante || ""}
    function safeJsonParse(v) { return v || {}; }
    async function loadDossier() { return { app_dossier_id: 10000001, hektor_annonce_id: "62189" }; }
    async function logJob(id, etape, statut, message, details) { journal.push({ etape, statut, message, details }); }
    async function ensureAdminHektorSession(job, raison) { appels.push("admin:" + raison); compte.actuel = "admin"; }
    async function ensureHektorExecutionContext() { appels.push("bascule"); compte.actuel = "negociateur"; return { idUser: "77" }; }
    async function refreshHektorSession(raison) { appels.push("connexion:" + raison); }
    async function fetchConsolePhotoEntries() {
      appels.push("lecture:" + compte.actuel);
      if (compte.actuel === "admin" && hektor.adminRefuse) throw new Error("Hektor 403 on vignettes: refus");
      return (compte.actuel === "admin" ? hektor.admin : hektor.negociateur)
        .map((id) => ({ hektor_photo_id: id, visible: !String(id).startsWith("m") }));
    }
    async function supabaseRequest(chemin) { appels.push("base"); return base.map((id) => ({ hektor_photo_id: id })); }
    async function upsertConsolePhotos(dossier, entries) {
      const lues = new Set(entries.map((e) => e.hektor_photo_id));
      this_marquees.push(...base.filter((id) => !lues.has(id)));
      return entries.map((e) => ({ visible: e.visible }));
    }
    var this_marquees = [];
    async function downloadConsolePhotoFiles() { return { downloaded: 0, unchanged: 0, failed: 0, bytes: 0 }; }
    ${garde || ""}
    ${morceaux.join("\n\n")}
    this.api = { handleSyncHektorPhotos, marquees: () => this_marquees };`, ctx);
  return ctx;
}

const job = { id: "essai", payload_json: {} };
const nb = (c, quoi) => c.appels.filter((a) => a.startsWith(quoi)).length;

(async () => {
  const sept = ["1", "2", "3", "4", "m5", "m6", "m7"];

  // (1)
  let c = monter(src, { hektor: { admin: sept, negociateur: sept }, base: sept });
  if (!c) { console.log("⛔ fonctions introuvables dans le worker"); process.exit(2); }
  let r = await c.api.handleSyncHektorPhotos(job);
  controle("(1) cas courant : aucune bascule de compte", nb(c, "bascule") === 0, c.appels.join(" "));
  controle("(1) aucune connexion complete", nb(c, "connexion") === 0, c.appels.join(" "));
  controle("(1) lecture faite en admin, et le resultat le dit", nb(c, "lecture:admin") === 1 && r.lecture === "admin", JSON.stringify(r));
  controle("(1) 7 photos, 3 masquees, rien marque absent", r.total === 7 && r.hidden === 3 && c.api.marquees().length === 0, JSON.stringify(r));

  // (2)
  c = monter(src, { hektor: { admin: sept, negociateur: sept, adminRefuse: true }, base: sept });
  r = await c.api.handleSyncHektorPhotos(job);
  controle("(2) 403 en admin : UNE bascule, puis relecture en negociateur",
    nb(c, "bascule") === 1 && nb(c, "lecture:negociateur") === 1 && r.lecture === "negociateur", c.appels.join(" "));
  controle("(2) pas de connexion complete sur le 403 (comme les documents)", nb(c, "connexion") === 0, c.appels.join(" "));

  // (3) + (4) : l'admin ne voit pas la masquee m7, le negociateur la voit
  const sansM7 = sept.filter((id) => id !== "m7");
  c = monter(src, { hektor: { admin: sansM7, negociateur: sept }, base: sept });
  r = await c.api.handleSyncHektorPhotos(job);
  controle("(3) photo manquante en admin : relecture en negociateur avant de marquer",
    nb(c, "bascule") === 1 && c.appels.indexOf("lecture:negociateur") > c.appels.indexOf("lecture:admin"), c.appels.join(" "));
  controle("(3) c'est ECRIT au journal, avec la photo", c.journal.some((l) => /avant de les marquer/.test(l.message)
    && l.details.photos.includes("m7")), JSON.stringify(c.journal.map((l) => l.message)));
  controle("(4) la masquee est retrouvee : RIEN n'est marque absent", c.api.marquees().length === 0, c.api.marquees().join(","));
  controle("(4) le resultat dit 1 manquante, 1 retrouvee", r.relue_en_negociateur && r.relue_en_negociateur.manquantes_en_admin === 1
    && r.relue_en_negociateur.retrouvees === 1, JSON.stringify(r.relue_en_negociateur));

  // une photo vraiment retiree chez Hektor : les deux lectures concordent, elle est marquee (le geste normal)
  c = monter(src, { hektor: { admin: sansM7, negociateur: sansM7 }, base: sept });
  r = await c.api.handleSyncHektorPhotos(job);
  controle("(4b) photo vraiment retiree : marquee absente apres confirmation", c.api.marquees().join(",") === "m7"
    && r.relue_en_negociateur.retrouvees === 0, c.api.marquees().join(","));

  // (5)
  c = monter(src, { hektor: { admin: sept, negociateur: sept }, base: sept, env: { CONSOLE_PHOTOS_LECTURE_ADMIN: "false" } });
  r = await c.api.handleSyncHektorPhotos(job);
  controle("(5) interrupteur coupe : bascule AVANT la lecture, comme avant", c.appels[0] === "bascule"
    && nb(c, "lecture:negociateur") === 1 && nb(c, "admin:") === 0 && nb(c, "base") === 0, c.appels.join(" "));
  c = monter(src, { hektor: { admin: sept, negociateur: sept, adminRefuse: true }, base: sept, env: { CONSOLE_PHOTOS_LECTURE_ADMIN: "false" } });
  c.compte.actuel = "admin"; // force le 403 au 1er essai : on simule l'ancien enchainement
  // (dans l'ancien chemin la 1re lecture se fait deja en negociateur ; on verifie seulement l'ordre des gestes)
  r = await c.api.handleSyncHektorPhotos(job);
  controle("(5) interrupteur coupe : aucune garde ajoutee (pas de lecture de la base)", nb(c, "base") === 0, c.appels.join(" "));

  // (6) TEMOIN INVERSE
  let ancien;
  try {
    ancien = execFileSync("git", ["show", `${TEMOIN}:Console/console_job_worker.js`], { cwd: path.join(__dirname, ".."), maxBuffer: 64 * 1024 * 1024 })
      .toString("utf8").replace(/\r\n/g, "\n");
  } catch (e) { console.log("⛔ temoin illisible : " + e.message); process.exit(2); }
  c = monter(ancien, { hektor: { admin: sept, negociateur: sept }, base: sept });
  if (!c) { console.log("⛔ temoin : fonctions introuvables"); process.exit(2); }
  r = await c.api.handleSyncHektorPhotos(job);
  controle("(6) TEMOIN : l'ancienne version basculait a CHAQUE lecture", nb(c, "bascule") === 1 && nb(c, "lecture:admin") === 0, c.appels.join(" "));
  c = monter(ancien, { hektor: { admin: sept, negociateur: sansM7 }, base: sept });
  controle("(6) TEMOIN : l'ancienne version n'a pas la constante", !ancien.includes("PHOTOS_LECTURE_ADMIN"));

  // (7) MUTANT : on retire la garde
  const mutant = src.replace("const manquantes = await photosAbsentesDeLaLecture(dossier.hektor_annonce_id, entries);", "const manquantes = [];");
  controle("(7) le mutant est bien fabrique", mutant !== src);
  c = monter(mutant, { hektor: { admin: sansM7, negociateur: sept }, base: sept });
  r = await c.api.handleSyncHektorPhotos(job);
  controle("(7) MUTANT ATTRAPE : sans la garde, la masquee serait marquee absente", c.api.marquees().join(",") === "m7", c.api.marquees().join(","));

  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\ntout est vert");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log("⛔ " + (e && e.stack || e)); process.exit(2); });
