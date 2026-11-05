// PARTENAIRES (05/11/2026, chantier partenaires §23) -- supprimer un contact EFFACE ses lignes du registre des partenaires
// (décision de Frédéric : « Effacer »). Cet essai lit le VRAI worker (sans le lancer) : il éprouve l'interrupteur sur un
// faux Supabase, et vérifie que l'étape est branchée au bon endroit, avec les bonnes clés.
//     node Console/test_partenaire_suppression.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const echecs = [];

function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}

function tranche(debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

const interrupteur = tranche("async function interrupteurAppSetting(");
const suppression = tranche("async function handleDeleteHektorContact(");
if (!interrupteur || !suppression) {
  console.log("⛔ Pièces introuvables dans le worker -- rien ne serait prouvé.");
  process.exit(2);
}

(async () => {
  // 1. l'interrupteur, sur un faux Supabase
  const essai = async (reponse) => {
    const ctx = { encodeURIComponent, supabaseRequest: async () => { if (reponse instanceof Error) throw reponse; return reponse; } };
    vm.createContext(ctx);
    vm.runInContext(`${interrupteur}\nthis.f = interrupteurAppSetting;`, ctx);
    return ctx.f("partenaire_efface_a_la_suppression");
  };
  controle("(1) « on » = allumé", (await essai([{ value: "on" }])) === true);
  controle("(2) « off » = éteint", (await essai([{ value: "off" }])) === false);
  controle("(3) absent = éteint", (await essai([])) === false);
  controle("(4) lecture ratée = éteint", (await essai(new Error("503"))) === false);

  // 2. le branchement dans la suppression
  const iLiens = suppression.indexOf('"registre_des_liens"');
  const iPart = suppression.indexOf('interrupteurAppSetting("partenaire_efface_a_la_suppression")');
  const iBuild = suppression.indexOf('cleanup.build = { status: "skipped"');
  controle("(5) l'étape vient APRÈS le registre des liens et AVANT la fin du nettoyage", iLiens > 0 && iPart > iLiens && iBuild > iPart,
    JSON.stringify([iLiens, iPart, iBuild]));
  const bloc = suppression.slice(iPart, iBuild);
  controle("(6) les MÉTIERS du contact sont effacés, par NOTRE numéro", /app_partenaire_metier\?contact_id=eq\.\$\{numero\}/.test(bloc)
    && /encodeURIComponent\(String\(numeroDemande\)\)/.test(bloc));
  controle("(7) ses LIENS sont effacés, comme partenaire ET comme client",
    /app_partenaire_lien\?partenaire_id=eq\.\$\{numero\}/.test(bloc) && /app_partenaire_lien\?client_contact_id=eq\.\$\{numero\}/.test(bloc));
  controle("(8) c'est un DELETE qui rend les lignes (pour les compter)", /method: "DELETE", headers: \{ Prefer: "return=representation" \}/.test(bloc));
  controle("(9) interrupteur éteint : l'étape est dite « skipped », rien n'est effacé", /status: "skipped", reason: "interrupteur_eteint"/.test(bloc));
  controle("(10) une erreur ne bloque pas la suppression : elle est notée dans cleanup.errors et au journal",
    /cleanup\.errors\.push\(\{ step: "registre_des_partenaires"/.test(bloc) && /logJob\(job\.id, "registre_des_partenaires", "error"/.test(bloc));
  controle("(11) aucune requête vers Hektor dans cette étape", !/hektorFetch|XMLRPC_URL/.test(bloc));

  console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTout est vert.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`⛔ ${e && e.message || e}`); process.exit(2); });
