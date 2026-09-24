#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════
// C.9-e (e2) — LE NUMERO HEKTOR SE POSE-T-IL SUR LA LIGNE DE L'APP, ET AVANT ?
//                                                                 24/09/2026
// ═══════════════════════════════════════════════════════════════════════════
// N'APPELLE NI HEKTOR NI SUPABASE : un faux Supabase enregistre les requetes.
//
// (1) la regle : on ne remplit qu'une case VIDE, jamais d'ecrasement, trois
//     tentatives sur une panne passagere, rien du tout pour une annonce ordinaire.
// (2) le placement dans le worker : APRES la confirmation de Hektor, AVANT le
//     rafraichissement. ⚠ Rejoue sur la version d'avant, EPINGLEE par son numero
//     de commit -- jamais HEAD, qui glisse des que le correctif est commite.
"use strict";
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { poserNumeroHektorSurLigneApp, ArretVolontaire } = require("./numero_annonce_app");

const VERSION_AVANT = "59aac63"; // le dernier commit SANS e2 -- ne pas remplacer par HEAD
const echecs = [];
function controle(nom, ok, detail = "") {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + detail}`);
  if (!ok) echecs.push(nom);
}

function fauxSupabase({ ligne = null, pannes = 0 } = {}) {
  const journal = [];
  let restantes = pannes;
  const requete = async (chemin, options) => {
    journal.push({ chemin, methode: options.method, corps: options.body || null });
    if (restantes > 0) { restantes -= 1; throw new Error("503 passager (simule)"); }
    if (options.method === "PATCH") {
      if (ligne && (ligne.hektor_annonce_id === null || ligne.hektor_annonce_id === undefined)) {
        ligne.hektor_annonce_id = JSON.parse(options.body).hektor_annonce_id;
        return [ligne];
      }
      return [];
    }
    return ligne ? [ligne] : [];
  };
  return { requete, journal };
}
const attentes = [];
const attendre = async (ms) => { attentes.push(ms); };

(async () => {
  // ── (1) la regle ────────────────────────────────────────────────────────
  let f = fauxSupabase();
  let r = await poserNumeroHektorSurLigneApp({ appDossierId: undefined, hektorAnnonceId: 63200, requete: f.requete, attendre });
  controle("(1) annonce ordinaire (pas de numero d'app) : rien, pas une requete",
    r.status === "skipped" && f.journal.length === 0, JSON.stringify(r));
  r = await poserNumeroHektorSurLigneApp({ appDossierId: 7589128, hektorAnnonceId: 63200, requete: f.requete, attendre });
  controle("(1) numero de la plage SERVEUR : rien", r.status === "skipped" && f.journal.length === 0);

  f = fauxSupabase({ ligne: { app_dossier_id: 10000001, hektor_annonce_id: null } });
  r = await poserNumeroHektorSurLigneApp({ appDossierId: 10000001, hektorAnnonceId: 63200, requete: f.requete, attendre });
  controle("(1) case vide : le numero Hektor est POSE", r.status === "pose" && r.tentatives === 1, JSON.stringify(r));
  controle("(1) ... par un PATCH qui ne vise QUE la case vide",
    f.journal[0].methode === "PATCH" && f.journal[0].chemin.includes("hektor_annonce_id=is.null")
    && f.journal[0].chemin.includes("app_dossier_id=eq.10000001")
    && JSON.parse(f.journal[0].corps).hektor_annonce_id === 63200, JSON.stringify(f.journal[0]));

  r = await poserNumeroHektorSurLigneApp({ appDossierId: 10000001, hektorAnnonceId: 63200, requete: f.requete, attendre });
  controle("(1) rejoue : deja pose, rien d'ecrit", r.status === "deja_pose", JSON.stringify(r));

  f = fauxSupabase({ ligne: { app_dossier_id: 10000001, hektor_annonce_id: 55555 } });
  try {
    await poserNumeroHektorSurLigneApp({ appDossierId: 10000001, hektorAnnonceId: 63200, requete: f.requete, attendre });
    controle("(1) une AUTRE valeur deja la : on s'arrete", false, "il a continue");
  } catch (e) {
    controle("(1) une AUTRE valeur deja la : on s'arrete, sans reessayer",
      e instanceof ArretVolontaire && f.journal.filter((j) => j.methode === "PATCH").length === 1, e.message);
    controle("(1) ... et on n'ecrase pas", f.journal.length === 2, JSON.stringify(f.journal));
  }

  attentes.length = 0;
  f = fauxSupabase({ ligne: { app_dossier_id: 10000001, hektor_annonce_id: null }, pannes: 2 });
  r = await poserNumeroHektorSurLigneApp({ appDossierId: 10000001, hektorAnnonceId: 63200, requete: f.requete, attendre });
  controle("(1) deux pannes passageres puis succes : pose a la 3e tentative",
    r.status === "pose" && r.tentatives === 3 && attentes.join(",") === "2000,8000", `${JSON.stringify(r)} attentes=${attentes}`);

  f = fauxSupabase({ ligne: { app_dossier_id: 10000001, hektor_annonce_id: null }, pannes: 9 });
  try {
    await poserNumeroHektorSurLigneApp({ appDossierId: 10000001, hektorAnnonceId: 63200, requete: f.requete, attendre });
    controle("(1) panne durable : le travail tombe en ERREUR", false, "il a reussi ?");
  } catch (e) {
    controle("(1) panne durable : le travail tombe en ERREUR, avec la reparation ecrite",
      !(e instanceof ArretVolontaire) && /A reparer a la main/.test(e.message) && f.journal.length === 3, e.message);
  }

  f = fauxSupabase({ ligne: null });
  try {
    await poserNumeroHektorSurLigneApp({ appDossierId: 10000001, hektorAnnonceId: 63200, requete: f.requete, attendre });
    controle("(1) ligne absente : arret", false, "il a continue");
  } catch (e) { controle("(1) ligne absente : arret, sans reessayer", e instanceof ArretVolontaire && f.journal.length === 2, e.message); }

  try {
    await poserNumeroHektorSurLigneApp({ appDossierId: 10000001, hektorAnnonceId: 10000009, requete: fauxSupabase().requete, attendre });
    controle("(1) un « numero Hektor » dans NOTRE plage : refuse", false, "accepte");
  } catch (e) { controle("(1) un « numero Hektor » dans NOTRE plage : refuse", e instanceof ArretVolontaire, e.message); }

  // ── (2) le placement dans le worker ──────────────────────────────────────
  function placementCorrect(source) {
    const debut = source.indexOf("async function handleCreateHektorDraftAnnonce(job)");
    const fin = source.indexOf("async function handleCreateHektorDraftAnnonceWithProvisional(job)");
    if (debut < 0 || fin < 0) return [false, "traitement de creation introuvable"];
    const corps = source.slice(debut, fin);
    const confirme = corps.indexOf("if (!created) {");
    const pose = corps.indexOf("poserNumeroHektorSurLigneApp(");
    const rafraichit = corps.indexOf("enqueueRefreshConsoleDataJobBestEffort(job, created.id");
    if (pose < 0) return [false, "la pose du numero n'est pas appelee"];
    if (!(confirme >= 0 && confirme < pose && pose < rafraichit)) {
      return [false, `ordre faux : confirmation ${confirme}, pose ${pose}, rafraichissement ${rafraichit}`];
    }
    if (!/require\("\.\/numero_annonce_app"\)/.test(source)) return [false, "module non charge"];
    return [true, ""];
  }
  const actuel = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
  const [ok, pourquoi] = placementCorrect(actuel);
  controle("(2) la pose est APRES la confirmation de Hektor et AVANT le rafraichissement", ok, pourquoi);
  let avant = "";
  try {
    avant = execFileSync("git", ["show", `${VERSION_AVANT}:Console/console_job_worker.js`],
      { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  } catch (e) { avant = ""; }
  if (!avant) {
    controle("(2) PREUVE sur la version d'avant", false, `illisible (${VERSION_AVANT})`);
  } else {
    const [okAvant, pourquoiAvant] = placementCorrect(avant);
    controle(`(2) PREUVE : sur ${VERSION_AVANT} (avant e2), le controle ECHOUE`, !okAvant,
      "il passait deja : ce controle ne voit rien");
    console.log(`       version d'avant : « ${pourquoiAvant} »`);
  }

  console.log();
  if (echecs.length) {
    console.log(`${echecs.length} controle(s) en ECHEC : ${echecs.join(", ")}`);
    process.exit(1);
  }
  console.log("Le numero Hektor se pose sur la ligne de l'app, avant le rafraichissement -- et jamais par-dessus un autre.");
})();
