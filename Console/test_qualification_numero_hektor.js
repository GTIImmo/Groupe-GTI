// LA QUALIFICATION D'UN ACQUEREUR LE RECONNAIT SOUS SES DEUX NUMEROS : essai hors ligne.   23/10/2026
//
// L'essai reel du 23/10 (vente 23354 sur VA6482) : l'acquereur d'une vente HERITE du registre, ou il
// porte le numero de HEKTOR (605963) ; nos fiches sont rangees par NOTRE numero (20000011). La
// qualification ne cherchait que le notre -> « Contact 605963 inconnu de notre base », pas de
// qualification. Le 18/09 ca marchait : les fiches portaient encore les numeros de Hektor.
//
// On eprouve LE CODE REEL (qualifierAcquereursAvantTransaction, decoupee dans le worker), montee avec
// un faux Supabase qui applique vraiment le filtre de la requete.
//
//     node Console/test_qualification_numero_hektor.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const fichier = process.argv[2] || path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(fichier, "utf8");
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
  qualifier: tranche("async function qualifierAcquereursAvantTransaction("),
  demandes: tranche("function acquereursDemandesPourQualification("),
  estQualifie: tranche("function estQualifieAcquereur("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
if (manquants.length) { console.log(`⛔ Une piece manque : ${manquants.join(", ")}`); process.exit(2); }

// Les fiches : notre numero dans hektor_contact_id, celui de Hektor dans hektor_target_id.
const FICHES = [
  { hektor_contact_id: "20000011", hektor_target_id: "605963", typologies_json: ["acquéreur"] },
  { hektor_contact_id: "10354641", hektor_target_id: "603953", typologies_json: ["mandant"] },
];
function filtrer(chemin) {
  const liste = (re) => { const m = chemin.match(re); return m ? m[1].split(",") : null; };
  const parNotre = liste(/hektor_contact_id[=.]in\.\(([^)]*)\)/);
  const parHektor = liste(/hektor_target_id\.in\.\(([^)]*)\)/);
  return FICHES.filter((f) => (parNotre && parNotre.includes(f.hektor_contact_id))
                           || (parHektor && parHektor.includes(f.hektor_target_id)));
}

async function lancer(acquereur) {
  const journal = [];
  const ctx = {
    console, JSON, Set, Map, Array, String, Number, Math, Object, encodeURIComponent,
    ASSISTANTS_HEKTOR: { sold: true, compromise: true },
    safeJsonParse: (x) => { try { return JSON.parse(x); } catch (_) { return null; } },
    r3Texte: (v) => (v == null ? "" : String(v).trim()),
    supabaseRequest: async (chemin) => {
      if (chemin.startsWith("app_console_job_log")) return [];
      if (chemin.startsWith("app_contact_current")) return filtrer(chemin);
      if (chemin.startsWith("app_dossier_current")) return [];   // bien inconnu : la qualification s'arrete la
      return [];
    },
    logJob: async (id, step, status, message) => { journal.push({ step, status, message }); },
  };
  vm.createContext(ctx);
  vm.runInContext([morceaux.demandes, morceaux.estQualifie, morceaux.qualifier,
    "this.qualifier = qualifierAcquereursAvantTransaction;"].join("\n"), ctx);
  const r = await ctx.qualifier({ id: "essai" }, { buyer_contact_id: acquereur, amount: "120000" }, "sold", "24113");
  return { r, journal };
}

(async () => {
  {
    const { journal } = await lancer("605963");
    controle("(1) l'acquereur sous son numero HEKTOR (605963) est reconnu -- plus de « inconnu de notre base »",
      !journal.some((j) => /inconnu de notre base/.test(j.message)), JSON.stringify(journal));
  }
  {
    const { journal } = await lancer("20000011");
    controle("(2) sous NOTRE numero (20000011), il l'est toujours", !journal.some((j) => /inconnu de notre base/.test(j.message)), JSON.stringify(journal));
  }
  {
    const { journal } = await lancer("603953");
    controle("(3) un contact NON acquereur, connu sous son numero Hektor, est bien envoye a la qualification",
      journal.some((j) => /Bien ou montant incomplet/.test(j.message)), JSON.stringify(journal));
  }
  {
    const { journal } = await lancer("999999");
    controle("(4) un numero inconnu des deux cotes reste « inconnu » (on ne devine pas)",
      journal.some((j) => /Contact 999999 inconnu de notre base/.test(j.message)), JSON.stringify(journal));
  }
  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`); process.exit(2); });
