// A1 -- LE RETOUR ECRIT LA FIN DE RETRACTATION AU REGISTRE : essai hors ligne (chantier 8).   23/10/2026
//
// On eprouve LE CODE REEL (reporterAuRegistre et sa table REGISTRE_PAR_HEKTOR, decoupees dans le
// worker), avec un faux Supabase qui enregistre le PATCH. Valeurs : le compromis 50131 de l'essai
// complet du 23/10 (VA6482), relu chez Hektor.
//
//     node Console/test_report_retractation.js [worker.js]
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(process.argv[2] || path.join(__dirname, "console_job_worker.js"), "utf8");
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
const table = (() => { const i = src.indexOf("const REGISTRE_PAR_HEKTOR = {"); return i < 0 ? null : src.slice(i, src.indexOf("};", i) + 2); })();
const reporter = tranche("async function reporterAuRegistre(");
if (!table || !reporter) { console.log("⛔ Une piece manque : on s'arrete."); process.exit(2); }

async function reporter_(chez) {
  const patches = [];
  const ctx = {
    console, JSON, Array, String, Number, Object,
    supabaseRequest: async (chemin, opts = {}) => { if ((opts.method || "").toUpperCase() === "PATCH") patches.push(JSON.parse(opts.body)); return null; },
    logJob: async () => {},
  };
  vm.createContext(ctx);
  vm.runInContext([table, reporter, "this.reporter = reporterAuRegistre;"].join("\n"), ctx);
  await ctx.reporter({ id: "essai" }, 1001379, chez);
  return patches[0] || {};
}

(async () => {
  const COMPROMIS_50131 = { dateStart: "2026-10-23", dateEnd: "2026-11-06", dateSignatureActe: "2027-01-20", sequestre: "6000.00",
    prixNetVendeur: "107000.00", prixPublique: "120000.00", honorairesEntree: "8000.00", honorairesSortie: "5000.00" };
  {
    const p = await reporter_(COMPROMIS_50131);
    controle("(1) compromis : la fin de retractation relue (dateEnd 2026-11-06) part au registre",
      p.date_fin_retractation === "2026-11-06", JSON.stringify(p));
    controle("(1) ... et le reste du report est inchange (montant, date, acte, sequestre)",
      p.montant === "120000.00" && p.date === "2026-10-23" && p.date_acte === "2027-01-20" && p.sequestre === "6000.00", JSON.stringify(p));
  }
  {
    const p = await reporter_({ montant: "120000", validite: "15", dateProposition: "2026-10-23" });
    controle("(2) offre (pas de dateEnd) : la fin de retractation n'est PAS touchee", !("date_fin_retractation" in p), JSON.stringify(p));
  }
  {
    const p = await reporter_({ ...COMPROMIS_50131, dateEnd: "" });
    controle("(3) « vide ne gagne pas » : une fin vide chez Hektor n'efface pas la notre", !("date_fin_retractation" in p), JSON.stringify(p));
  }
  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`); process.exit(2); });
