// A.2 (06/11/2026) -- LE CRAN « admin » DE `signature_youtrust` : 'on' = tout le monde, 'admin' = seulement un travail
// DEMANDÉ PAR UN ADMIN ACTIF, le reste = éteint. Sur LE CODE RÉEL du worker (interrupteurSignatureYoutrust et
// exigerInterrupteurYoutrust découpés dans console_job_worker.js) contre une FAUSSE base : n'appelle rien.
//     node Console/test_signature_youtrust_cran_admin.js   (0 = vert · 1 = un échec · 2 = pas pu mesurer)
// ⭐ TÉMOIN INVERSE : la version d'avant (git HEAD) refuse 'admin' pour tout le monde, admin compris.
// + l'écran (apps/hektor-v1) : les deux lectures passent par loadSignatureYoutrustActive, même règle.
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
const racine = path.join(__dirname, "..");
const sansCR = (s) => s.split(String.fromCharCode(13)).join("");
const srcNeuf = sansCR(fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8"));
let srcAvant;
try {
  srcAvant = sansCR(execFileSync("git", ["show", "HEAD:Console/console_job_worker.js"], { cwd: racine, encoding: "utf8", maxBuffer: 128 * 1024 * 1024 }));
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }

const tranche = (src, debut) => { const i = src.indexOf(debut); if (i < 0) throw new Error(`introuvable : ${debut}`); return src.slice(i, src.indexOf("\n}\n", i) + 2); };
function monter(src, base) {
  const code = [
    'const MARQUE_REFUS_ETAT = "[REFUS D\'ETAT]";',
    tranche(src, "function cleanString("),
    tranche(src, "function refusEtatYoutrust("),
    tranche(src, "async function interrupteurSignatureYoutrust("),
    tranche(src, "async function exigerInterrupteurYoutrust("),
    "return { interrupteurSignatureYoutrust, exigerInterrupteurYoutrust };",
  ].join("\n");
  const lus = [];
  const supabaseRequest = async (chemin) => {
    lus.push(chemin);
    if (chemin.startsWith("app_setting?")) return base.valeur === undefined ? [] : [{ value: base.valeur }];
    if (chemin.startsWith("app_user_profile?")) {
      const id = decodeURIComponent((chemin.match(/id=eq\.([^&]+)/) || [])[1] || "");
      return base.profils[id] ? [base.profils[id]] : [];
    }
    throw new Error(`lecture inattendue : ${chemin}`);
  };
  // eslint-disable-next-line no-new-func
  const f = new Function("supabaseRequest", code)(supabaseRequest);
  return { ...f, lus };
}
const PROFILS = {
  "u-admin": { role: "admin", is_active: true },
  "u-admin-inactif": { role: "admin", is_active: false },
  "u-nego": { role: "commercial", is_active: true },
  "u-manager": { role: "manager", is_active: true },
};
const travail = (qui) => ({ id: "j1", job_type: "youtrust_send_signature", requested_by: qui });

(async () => {
  try {
    // 1. Le cran 'on' et l'éteint : rien ne change (et on ne lit AUCUN profil).
    for (const [valeur, attendu] of [["on", true], ["true", true], ["off", false], [undefined, false], ["", false]]) {
      const m = monter(srcNeuf, { valeur, profils: PROFILS });
      const r = await m.interrupteurSignatureYoutrust(travail("u-nego"));
      controle(`1. « ${valeur === undefined ? "(absent)" : valeur} » -> ${attendu ? "allumé" : "éteint"}, pour un négociateur, sans lire de profil`, r === attendu && !m.lus.some((l) => l.startsWith("app_user_profile")), JSON.stringify({ r, lus: m.lus }));
    }
    // 2. ⭐ Le cran 'admin'.
    const cas = [["u-admin", true, "un admin actif"], ["u-nego", false, "un négociateur"], ["u-admin-inactif", false, "un admin INACTIF"], ["u-manager", false, "un manager"], ["u-inconnu", false, "un demandeur sans profil"]];
    for (const [qui, attendu, libelle] of cas) {
      const m = monter(srcNeuf, { valeur: "admin", profils: PROFILS });
      const r = await m.interrupteurSignatureYoutrust(travail(qui));
      controle(`2. « admin » + ${libelle} -> ${attendu ? "ALLUMÉ" : "éteint"}`, r === attendu, String(r));
    }
    {
      const m = monter(srcNeuf, { valeur: "admin", profils: PROFILS });
      controle("2. « admin » sans travail, ou travail sans demandeur -> éteint (jamais allumé par défaut)",
        (await m.interrupteurSignatureYoutrust()) === false && (await m.interrupteurSignatureYoutrust({ id: "j" })) === false);
    }
    // 3. La garde des travaux : refus CLAIR pour un négociateur, passage pour l'admin.
    {
      const m = monter(srcNeuf, { valeur: "admin", profils: PROFILS });
      let refus = null;
      try { await m.exigerInterrupteurYoutrust(travail("u-nego")); } catch (e) { refus = e.message; }
      controle("3. « admin » : un envoi posé par un négociateur est REFUSÉ, avec la raison", /\[REFUS D'ETAT\]/.test(refus || "") && /pas un admin actif/.test(refus || ""), refus);
      let passe = true;
      try { await m.exigerInterrupteurYoutrust(travail("u-admin")); } catch (_e) { passe = false; }
      controle("3. « admin » : le même envoi posé par un admin PASSE", passe);
    }
    // 4. Les trois portes du worker passent bien le travail (envoi, relance/annulation/lien, génération).
    controle("4. l'envoi, la relance / l'annulation / le lien, et la génération passent le TRAVAIL à la garde",
      (srcNeuf.match(/await exigerInterrupteurYoutrust\(job\);/g) || []).length === 2
        && /if \(chezNousPuisHektor \|\| await interrupteurSignatureYoutrust\(job\)\) \{/.test(srcNeuf)
        && !/await exigerInterrupteurYoutrust\(\);/.test(srcNeuf) && !/await interrupteurSignatureYoutrust\(\)/.test(srcNeuf));
    // 5. ⭐ TÉMOIN INVERSE : la version d'avant refuse « admin » à tout le monde.
    {
      const m = monter(srcAvant, { valeur: "admin", profils: PROFILS });
      controle("5. TÉMOIN INVERSE : avant, « admin » était éteint même pour un admin", (await m.interrupteurSignatureYoutrust(travail("u-admin"))) === false);
    }
    // 6. L'écran : la même règle, aux deux lectures.
    const front = (f) => sansCR(fs.readFileSync(path.join(racine, "apps", "hektor-v1", "src", f), "utf8"));
    const app = front("App.tsx");
    const api = front(path.join("lib", "api.ts"));
    const corps = (api.match(/export async function loadSignatureYoutrustActive\(\)[\s\S]*?\n}\n/) || [""])[0];
    controle("6. l'écran : 'on' tout le monde ; 'admin' -> le rôle 'admin' ET actif de l'utilisateur connecté ; sinon éteint",
      /\['on', 'true', '1', 'yes'\]\.includes\(valeur \?\? ''\)\) return true/.test(corps) && /if \(valeur !== 'admin'/.test(corps) && /return p\.is_active === true && p\.role === 'admin'/.test(corps), corps.slice(0, 120));
    controle("6. les DEUX lectures de l'écran (le crochet, la génération) passent par elle ; plus aucune lecture à deux crans",
      /void loadSignatureYoutrustActive\(\)\.then/.test(app) && /const reperes = await loadSignatureYoutrustActive\(\)/.test(app) && !/loadAppSettingActive\('signature_youtrust'\)/.test(app));
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
