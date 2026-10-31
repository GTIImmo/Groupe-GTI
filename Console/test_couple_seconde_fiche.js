// LA SECONDE FICHE DU COUPLE -- essai hors ligne (couples · piece B).   31/10/2026
//
// CE QU'ON EPROUVE, sur LE CODE REEL (fonction decoupee dans le worker, montee avec
// un FAUX script de recherche et une FAUSSE base -- meme technique que
// test_garde_copropriete.js) :
//   (1) trouvee, case vide, personne d'autre -> la case cible est posee, 1 ligne
//   (2) le PATCH ne vise que la personne 2 ET seulement si sa case est vide
//   (3) non trouvee -> rien n'est ecrit, et c'est DIT au journal
//   (4) le numero est deja porte par un autre contact -> rien n'est ecrit, c'est dit
//   (5) la case etait deja pourvue (0 ligne) -> dit, pas d'erreur levee
//   (6) le script plante -> le travail ne tombe pas, c'est dit
//   (7) l'appel dans executerCreationContactHektor est garde par app_identite_m2
//       (TEMOIN INVERSE : sans personne 2 dans la charge, rien n'est appele)
//
//     node Console/test_couple_seconde_fiche.js
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

const code = tranche("async function rangerSecondeFicheDuCouple(");
const appelant = tranche("async function executerCreationContactHektor(");
if (!code || !appelant) {
  console.log("NE PEUT PAS MESURER : fonction introuvable dans le worker");
  process.exit(2);
}

function monter({ sortieScript, scriptPlante, porteurs, lignesPatch }) {
  const journal = [];
  const appels = [];
  const bac = {
    cleanString: (v) => (v === null || v === undefined ? "" : String(v).trim()),
    safeJsonParse: (t) => { try { return JSON.parse(t); } catch (_) { return null; } },
    runProjectPythonScript: async (argv) => {
      appels.push({ type: "python", argv });
      if (scriptPlante) throw new Error("python introuvable");
      return { stdout: "[log] lecture\n" + JSON.stringify(sortieScript) + "\n" };
    },
    supabaseRequest: async (chemin, options) => {
      appels.push({ type: "supabase", chemin, options });
      if ((options.method || "GET") === "GET") return porteurs;
      return lignesPatch;
    },
    logJob: async (id, etape, statut, message, details) => { journal.push({ etape, statut, message, details }); },
    encodeURIComponent,
    JSON, Array, String,
  };
  vm.createContext(bac);
  vm.runInContext(code + "\nthis.rangerSecondeFicheDuCouple = rangerSecondeFicheDuCouple;", bac);
  return { f: bac.rangerSecondeFicheDuCouple, journal, appels };
}

(async () => {
  const job = { id: "job-essai" };

  // (1) + (2)
  {
    const m = monter({ sortieScript: { seconde: "606072", lus: [{ id: "606072", issue: "seconde" }] },
                       porteurs: [], lignesPatch: [{ hektor_contact_id: "20000032" }] });
    const r = await m.f(job, "20000032", "606071");
    controle("1 trouvee -> case cible posee", r.status === "linked" && r.seconde === "606072", JSON.stringify(r));
    controle("1 journal « done »", m.journal.length === 1 && m.journal[0].statut === "done", JSON.stringify(m.journal));
    const py = m.appels.find((a) => a.type === "python");
    controle("1 le script recoit la premiere", py && py.argv.join(" ") === "phase2/sync/contact_seconde_fiche_from_api.py --premiere 606071", py && py.argv.join(" "));
    const patch = m.appels.find((a) => a.type === "supabase" && a.options.method === "PATCH");
    controle("2 le PATCH vise la personne 2 seulement si sa case est vide",
      patch && patch.chemin === "app_contact_current?hektor_contact_id=eq.20000032&hektor_target_id=is.null", patch && patch.chemin);
    controle("2 le PATCH ne porte QUE la case cible",
      patch && patch.options.body === JSON.stringify({ hektor_target_id: "606072" }), patch && patch.options.body);
  }

  // (3)
  {
    const m = monter({ sortieScript: { seconde: null, lus: [{ id: "606072", issue: "autre" }], arret: null },
                       porteurs: [], lignesPatch: [] });
    const r = await m.f(job, "20000032", "606071");
    controle("3 non trouvee -> rien n'est ecrit", r.status === "not_found" && !m.appels.some((a) => a.type === "supabase"), JSON.stringify(m.appels));
    controle("3 et c'est dit", m.journal[0] && m.journal[0].statut === "error" && /NON trouvee/.test(m.journal[0].message), JSON.stringify(m.journal));
  }

  // (4)
  {
    const m = monter({ sortieScript: { seconde: "606072", lus: [] },
                       porteurs: [{ hektor_contact_id: "10650999" }], lignesPatch: [{}] });
    const r = await m.f(job, "20000032", "606071");
    controle("4 numero deja porte -> rien n'est ecrit",
      r.status === "conflict" && !m.appels.some((a) => a.type === "supabase" && a.options.method === "PATCH"), JSON.stringify(r));
  }

  // (4 bis) la personne 2 elle-meme portant deja ce numero n'est pas un conflit
  {
    const m = monter({ sortieScript: { seconde: "606072", lus: [] },
                       porteurs: [{ hektor_contact_id: "20000032" }], lignesPatch: [] });
    const r = await m.f(job, "20000032", "606071");
    controle("4bis porte par elle-meme : pas un conflit", r.status === "not_written", JSON.stringify(r));
  }

  // (5)
  {
    const m = monter({ sortieScript: { seconde: "606072", lus: [] }, porteurs: [], lignesPatch: [] });
    const r = await m.f(job, "20000032", "606071");
    controle("5 case deja pourvue -> dit, sans lever", r.status === "not_written" && m.journal[0].statut === "error", JSON.stringify(r));
  }

  // (6)
  {
    const m = monter({ scriptPlante: true, porteurs: [], lignesPatch: [] });
    let leve = false;
    let r = null;
    try { r = await m.f(job, "20000032", "606071"); } catch (_) { leve = true; }
    controle("6 le script plante -> le travail ne tombe pas", !leve && r && r.status === "error", JSON.stringify(r));
    controle("6 et c'est dit", m.journal[0] && m.journal[0].statut === "error", JSON.stringify(m.journal));
  }

  // (7) la garde de l'appel, lue dans le code reel
  controle("7 l'appel est garde par app_identite_m2",
    /const identiteM2 = cleanString\(payload\.app_identite_m2 \|\| ""\);\s*const secondeFiche = identiteM2 && created && created\.contactId\s*\? await rangerSecondeFicheDuCouple\(job, identiteM2, created\.contactId\)\s*: null;/.test(appelant));
  controle("7 le resultat est rendu", /couple_seconde_fiche: secondeFiche/.test(appelant));

  console.log(echecs.length ? `${echecs.length} ECHEC(S)` : "TOUT VERT");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log("NE PEUT PAS MESURER : " + (e && e.stack || e)); process.exit(2); });
