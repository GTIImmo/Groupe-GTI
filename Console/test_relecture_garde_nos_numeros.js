// Essai : la relecture du worker garde NOS numeros a cote de ceux de Hektor
// (⑧ types, chantier 2 -- b, le point 4 ; 26/10/2026).
//
//     node Console/test_relecture_garde_nos_numeros.js
//
// Hors ligne : les fonctions sont EXTRAITES du worker et executees dans un bac a
// sable ; Supabase est simule. Rien n'est appele, rien n'est ecrit.

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
const morceaux = {
  interrupteur: (src.match(/const GARDER_NOS_NUMEROS_A_LA_RELECTURE = (true|false);/) || [null])[0],
  poser: tranche("function poserNosNumerosDansLaListe("),
  table: tranche("async function tableDeNosNumeros("),
  reporter: tranche("async function reporterAuRegistre("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
controle("(0) les pieces sont la", !manquants.length, `manquent : ${manquants.join(", ")}`);
if (manquants.length) process.exit(2);

function monter({ registre = null, annuaire = [], panne = false } = {}) {
  const patches = [];
  const journal = [];
  const lectures = [];
  const ctx = {
    console, JSON, Set, Map, Array, String, Number, Object, encodeURIComponent,
    PLAGE_NUMEROS_APP: 10000000,
    REGISTRE_PAR_HEKTOR: {},
    supabaseRequest: async (chemin, opts = {}) => {
      const m = (opts.method || "GET").toUpperCase();
      if (m === "PATCH") { patches.push(JSON.parse(opts.body || "{}")); return null; }
      lectures.push(chemin);
      if (panne && chemin.startsWith("app_contact_current")) throw new Error("HTTP 503 simule");
      if (chemin.startsWith("app_affaire_ledger")) return registre ? [registre] : [];
      if (chemin.startsWith("app_contact_current")) return annuaire;
      return [];
    },
    logJob: async (id, step, status, message, data) => { journal.push({ step, status, message }); },
  };
  vm.createContext(ctx);
  vm.runInContext([morceaux.interrupteur, morceaux.poser, morceaux.table, morceaux.reporter,
    "this.reporterAuRegistre = reporterAuRegistre; this.poser = poserNosNumerosDansLaListe;"].join("\n"), ctx);
  return { ctx, patches, journal, lectures };
}

const JOB = { id: "essai" };
const relu = {
  acquereurs: [{ id: "604016", nom: "A" }, { id: "700001", nom: "B" }, { id: "700002", nom: "C" }],
  mandants: [{ id: "421306", nom: "RENDLA" }, { id: "999999", nom: "INCONNU" }],
};

(async () => {
  // (1) le registre portait deja nos numeros (la nuit) + l'annuaire pour un nouveau
  {
    const { ctx, patches } = monter({
      registre: {
        acquereurs_json: [{ id: "604016", app_contact_id: 10354701 }],
        mandants_json: JSON.stringify([{ id: "421306", app_contact_id: 10216900 }]),
        acquereur_json: { id: "700001", app_contact_id: 10400001 },
      },
      annuaire: [{ hektor_target_id: "700002", hektor_contact_id: "10400002" }],
    });
    await ctx.reporterAuRegistre(JOB, 31001, JSON.parse(JSON.stringify(relu)));
    const c = patches[0] || {};
    const num = (l, i) => (l || [])[i] && l[i].app_contact_id;
    controle("(1a) un acquereur garde le numero que le registre portait", num(c.acquereurs_json, 0) === 10354701);
    controle("(1b) le principal (acquereur_json) aussi", c.acquereur_json && c.acquereur_json.app_contact_id === 10354701);
    controle("(1c) un acquereur repris du singulier", num(c.acquereurs_json, 1) === 10400001);
    controle("(1d) un acquereur NOUVEAU trouve par l'annuaire", num(c.acquereurs_json, 2) === 10400002);
    controle("(1e) un vendeur garde son numero (blob en texte)", num(c.mandants_json, 0) === 10216900);
    controle("(1f) un vendeur INCONNU ne recoit rien (on n'invente pas)", c.mandants_json && !("app_contact_id" in c.mandants_json[1]));
    controle("(1g) `id` reste le numero de HEKTOR partout",
      (c.acquereurs_json || []).map((p) => p.id).join(",") === "604016,700001,700002"
      && (c.mandants_json || []).map((p) => p.id).join(",") === "421306,999999");
  }
  // (2) un numero hors de notre plage n'est jamais pose
  {
    const { ctx, patches } = monter({
      registre: { acquereurs_json: [{ id: "604016", app_contact_id: 604016 }] },
      annuaire: [{ hektor_target_id: "700001", hektor_contact_id: "700001" }],
    });
    await ctx.reporterAuRegistre(JOB, 31002, { acquereurs: [{ id: "604016" }, { id: "700001" }] });
    const l = (patches[0] || {}).acquereurs_json || [];
    controle("(2) un « numero » de la plage de Hektor n'est jamais pris pour le notre",
      l.length === 2 && !l.some((p) => "app_contact_id" in p));
  }
  // (3) l'annuaire en panne : la liste part brute, le travail n'echoue pas, et on le DIT
  {
    const { ctx, patches, journal } = monter({ registre: null, panne: true });
    let erreur = null;
    try { await ctx.reporterAuRegistre(JOB, 31003, JSON.parse(JSON.stringify(relu))); } catch (e) { erreur = e; }
    const c = patches[0] || {};
    controle("(3a) pas d'exception", erreur === null, String(erreur));
    controle("(3b) la liste est quand meme ecrite, brute", Array.isArray(c.acquereurs_json) && c.acquereurs_json.length === 3
      && !c.acquereurs_json.some((p) => "app_contact_id" in p));
    controle("(3c) la panne est journalisee", journal.some((j) => j.status === "error" && /pas pu etre retrouves/.test(j.message)));
  }
  // (4) une seule lecture de l'annuaire, et seulement pour ceux qui manquent
  {
    const { ctx, lectures } = monter({
      registre: { acquereurs_json: [{ id: "604016", app_contact_id: 10354701 }] },
      annuaire: [],
    });
    await ctx.reporterAuRegistre(JOB, 31004, { acquereurs: [{ id: "604016" }, { id: "700005" }] });
    const lu = lectures.filter((x) => x.startsWith("app_contact_current"));
    controle("(4) l'annuaire n'est lu qu'une fois, pour le seul manquant", lu.length === 1 && /in\.\(700005\)$/.test(lu[0]), lu.join(" | "));
  }
  // (5) rien de relu : rien n'est lu, rien n'est ecrit (« vide ne gagne pas »)
  {
    const { ctx, patches, lectures } = monter({});
    await ctx.reporterAuRegistre(JOB, 31005, { acquereurs: [], mandants: null });
    controle("(5) liste vide : aucune lecture, aucune ecriture", !patches.length && !lectures.length);
  }
  // (6) l'interrupteur
  controle("(6) l'interrupteur est ALLUME dans le code livre", /GARDER_NOS_NUMEROS_A_LA_RELECTURE = true;/.test(morceaux.interrupteur));

  console.log(`\n${echecs.length ? "⛔ " + echecs.length + " ECHEC(S)" : "TOUT EST VERT"}`);
  process.exit(echecs.length ? 1 : 0);
})();
