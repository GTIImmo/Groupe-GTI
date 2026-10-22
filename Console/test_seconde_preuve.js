// LA SECONDE PREUVE A LA RELECTURE -- essai hors ligne de 1a (chantier 8).       22/10/2026
//
// LE DEFAUT : la preuve de creation relit l'API 3 fois en ~15 s ; si Hektor n'a pas encore
// publie la transaction, le numero n'est jamais pose (19 preuves ratees sur ~60 creations,
// dont le compromis 50128 du 22/10, bien cree).
//
// CE QU'ON EPROUVE, sur LE CODE REEL (fonctions decoupees dans console_job_worker.js, montees
// avec un faux Supabase et une fausse API qui enregistrent ce qu'on leur demande) :
//   (1)  les pieces sont la, et la relecture appelle bien la seconde preuve
//   (2)  aucune ligne orpheline : on ne lit RIEN chez Hektor
//   (3)  le cas du 22/10 : un candidat, notre acquereur -> le numero 50128 est pose
//   (4)  un candidat d'un AUTRE acquereur -> abstention, rien n'est pose
//   (5)  deux candidats du meme acquereur -> abstention
//   (6)  un candidat deja connu du registre -> ignore
//   (7)  registre illisible -> abstention
//   (8)  API muette -> abstention
//   (9)  une ligne qui porte notre IDENTITE (avant 1b) -> abstention, rien n'est invente
//   (10) deux lignes orphelines du meme acquereur -> abstention
//   (11) l'offre (acquereur a plat) -> le numero est pose
//   (12) une erreur de Supabase -> la relecture n'echoue pas
//   (13) TEMOIN INVERSE : interrupteur a false -> rien n'est lu, rien n'est pose
//
//     node Console/test_seconde_preuve.js
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
const morceaux = {
  interrupteur: (() => { const i = src.indexOf("const SECONDE_PREUVE_RELECTURE"); return i < 0 ? null : src.slice(i, src.indexOf("\n", i) + 1); })(),
  acquereurs: tranche("function acquereursDuDetail("),
  poser: tranche("async function poserNumerosManquants("),
  relecture: tranche("async function handleRefreshConsoleData("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
controle("(1) LA PREUVE D'ABORD : les pieces sont la, et la relecture appelle la seconde preuve",
  !manquants.length && /await poserNumerosManquants\(job, hektorAnnonceId\)/.test(morceaux.relecture || ""),
  manquants.length ? `manquent : ${manquants.join(", ")}` : "l'appel manque dans handleRefreshConsoleData");
if (manquants.length) { console.log("\n⛔ Une piece manque : on s'arrete."); process.exit(2); }

const JOB = { id: "essai" };

function monter({ orphelines = [], api = {}, connus = {}, erreurSupabase = false, eteint = false } = {}) {
  const appelsApi = [];
  const poses = [];
  const journal = [];
  const contexte = {
    console, JSON, Set, Map, Array, String, Number,
    supabaseRequest: async () => {
      if (erreurSupabase) throw new Error("HTTP 503 simule");
      return orphelines;
    },
    lireTransactionsParApi: async (job, annonce, genre) => {
      appelsApi.push(genre);
      const lu = api[genre];
      return lu === null || lu === undefined ? null : { tous: new Set(Object.keys(lu)), details: lu };
    },
    idsDejaConnusDuRegistre: async (job, annonce, genre) => {
      const c = connus[genre];
      return c === null ? null : new Set(c || []);
    },
    poserIdTransactionSurAffaire: async (job, aid, id) => { poses.push([aid, id]); return { status: "done", lignes: 1 }; },
    logJob: async (id, step, status, message, data) => { journal.push({ step, status, message, data }); },
  };
  vm.createContext(contexte);
  const interrupteur = eteint ? morceaux.interrupteur.replace("= true", "= false") : morceaux.interrupteur;
  vm.runInContext([interrupteur, morceaux.acquereurs, morceaux.poser,
    "this.poser = poserNumerosManquants;"].join("\n"), contexte);
  return { contexte, appelsApi, poses, journal };
}

const ORPHELINE_50128 = { app_affaire_id: 1001368, kind: "compromis", hektor_acquereur_id: "605946", date: "2026-10-22" };
const DETAIL_50128 = { prixPublique: "130000.00", acquereurs: [{ id: "605946", nom: "ESSAI 8A B2" }] };

(async () => {
  {
    const m = monter({ orphelines: [] });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(2) aucune ligne orpheline : rien n'est lu chez Hektor", r.status === "rien_a_faire" && m.appelsApi.length === 0,
      JSON.stringify({ r, api: m.appelsApi }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128], api: { compromis: { 50128: DETAIL_50128 } }, connus: { compromis: [] } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(3) le cas du 22/10 : un candidat, notre acquereur -> 50128 pose sur 1001368",
      m.poses.length === 1 && m.poses[0][0] === 1001368 && m.poses[0][1] === "50128" && r.poses === 1,
      JSON.stringify({ r, poses: m.poses }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128],
      api: { compromis: { 50999: { acquereurs: [{ id: "111111" }] } } }, connus: { compromis: [] } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(4) un candidat d'un AUTRE acquereur -> abstention", m.poses.length === 0 && r.bilan[0].resultat === "abstention",
      JSON.stringify({ r, poses: m.poses }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128],
      api: { compromis: { 50128: DETAIL_50128, 50129: DETAIL_50128 } }, connus: { compromis: [] } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(5) deux candidats du meme acquereur -> abstention", m.poses.length === 0 && /2_candidat/.test(r.bilan[0].raison),
      JSON.stringify({ r, poses: m.poses }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128],
      api: { compromis: { 50128: DETAIL_50128, 50050: DETAIL_50128 } }, connus: { compromis: ["50050"] } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(6) un candidat deja connu du registre est ignore -> 50128 pose", m.poses.length === 1 && m.poses[0][1] === "50128",
      JSON.stringify({ r, poses: m.poses }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128], api: { compromis: { 50128: DETAIL_50128 } }, connus: { compromis: null } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(7) registre illisible -> abstention", m.poses.length === 0 && r.bilan[0].raison === "registre_illisible",
      JSON.stringify({ r }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128], api: { compromis: null }, connus: { compromis: [] } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(8) API muette -> abstention", m.poses.length === 0 && r.bilan[0].raison === "api_muette", JSON.stringify({ r }));
  }
  {
    const m = monter({ orphelines: [{ ...ORPHELINE_50128, hektor_acquereur_id: "20000008" }],
      api: { compromis: { 50128: DETAIL_50128 } }, connus: { compromis: [] } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(9) une ligne qui porte notre IDENTITE -> abstention, rien n'est invente",
      m.poses.length === 0 && r.bilan[0].resultat === "abstention", JSON.stringify({ r }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128, { ...ORPHELINE_50128, app_affaire_id: 1001369 }],
      api: { compromis: { 50128: DETAIL_50128 } }, connus: { compromis: [] } });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(10) deux lignes orphelines du meme acquereur -> abstention",
      m.poses.length === 0 && r.bilan.every((b) => b.raison === "plusieurs_lignes_orphelines"), JSON.stringify({ r }));
  }
  {
    const m = monter({ orphelines: [{ app_affaire_id: 1001370, kind: "offre", hektor_acquereur_id: "605717", date: "2026-10-13" }],
      api: { offre: { 33098: { id_acquereur: "605717", montant: "16000" } } }, connus: { offre: [] } });
    const r = await m.contexte.poser(JOB, "61672");
    controle("(11) l'offre (acquereur a plat) -> 33098 pose", m.poses.length === 1 && m.poses[0][1] === "33098" && m.appelsApi[0] === "offre",
      JSON.stringify({ r, poses: m.poses }));
  }
  {
    const m = monter({ erreurSupabase: true });
    let jete = false;
    let r = null;
    try { r = await m.contexte.poser(JOB, "24113"); } catch (_) { jete = true; }
    controle("(12) une erreur de Supabase ne fait PAS echouer la relecture",
      !jete && r.status === "error" && m.journal.some((j) => j.step === "hektor_transaction_seconde_preuve"), JSON.stringify({ jete, r }));
  }
  {
    const m = monter({ orphelines: [ORPHELINE_50128], api: { compromis: { 50128: DETAIL_50128 } }, connus: { compromis: [] }, eteint: true });
    const r = await m.contexte.poser(JOB, "24113");
    controle("(13) TEMOIN INVERSE : interrupteur a false -> rien n'est lu, rien n'est pose",
      r.status === "eteint" && m.poses.length === 0 && m.appelsApi.length === 0, JSON.stringify({ r }));
  }

  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`); process.exit(2); });
