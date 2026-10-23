// R3 -- LE CONTROLE AU RETOUR DE LA CREATION : essai hors ligne (chantier 8).        23/10/2026
//
// On eprouve LE CODE REEL (decoupe dans console_job_worker.js : memeValeurHektor, le bloc R3,
// et l'ancien marquerLeCarnetRestant pour le temoin inverse), monte avec un faux Supabase et une
// fausse API qui enregistrent ce qu'on leur demande. Les valeurs sont celles des essais reels du
// 22-23/10 (compromis 50129 sur VA6482, offres 33098 et 33094 sur 61672).
//
//     node Console/test_controle_carnet_r3.js
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
const iR3 = src.indexOf("const R3_CONTROLE_CARNET");
const fR3 = src.indexOf("// LA GARDE CONTRE LE DOUBLEMENT.");
const morceaux = {
  meme: tranche("function memeValeurHektor("),
  r3: iR3 >= 0 && fR3 > iR3 ? src.slice(iR3, fR3) : null,
  ancien: tranche("async function marquerLeCarnetRestant("),
  table: (() => { const i = src.indexOf("const CARNET_VERS_REGISTRE = {"); return i < 0 ? null : src.slice(i, src.indexOf("};", i) + 2); })(),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
const creation = tranche("async function prouverTransactionCreee(") || "";
const relecture = tranche("async function handleRefreshConsoleData(") || "";
controle("(1) LA PREUVE D'ABORD : les pieces sont la, et les deux appelants les appellent",
  !manquants.length && /controlerLeCarnet\(job, annonceId,/.test(creation)
  && /reporterAuRegistre\(job, appAffaireId/.test(creation)
  && /await controlerLeCarnet\(job, hektorAnnonceId\)/.test(relecture),
  manquants.length ? `manquent : ${manquants.join(", ")}` : "un appel manque");
if (manquants.length) { console.log("\n⛔ Une piece manque : on s'arrete."); process.exit(2); }

const JOB = { id: "essai" };
const ECRIT = "2026-10-22T21:47:07.486998+00:00";
const NUIT = "2026-10-23T04:46:27+00:00";

function monter({ registres = [], lignes = [], travaux = [], contacts = [], api = {}, erreur = false, eteint = false } = {}) {
  const appelsApi = [];
  const supprimes = [];
  const patches = [];
  const journal = [];
  const contexte = {
    console, JSON, Set, Map, Array, String, Number, Date, Math, Object, encodeURIComponent,
    supabaseRequest: async (chemin, opts = {}) => {
      if (erreur) throw new Error("HTTP 503 simule");
      const m = (opts.method || "GET").toUpperCase();
      const champ = decodeURIComponent((chemin.match(/champ=eq\.([^&]+)/) || [])[1] || "");
      const aff = Number((chemin.match(/app_affaire_id=eq\.(\d+)/) || [])[1] || 0);
      if (m === "DELETE") { supprimes.push(`${aff}:${champ}`); return null; }
      if (m === "PATCH") { patches.push({ cle: `${aff}:${champ}`, ...JSON.parse(opts.body || "{}") }); return null; }
      if (chemin.startsWith("app_affaire_ledger")) return registres;
      if (chemin.startsWith("app_affaire_champ_app")) return lignes;
      if (chemin.startsWith("app_console_job")) return travaux;
      if (chemin.startsWith("app_contact_current")) return contacts;
      return [];
    },
    lireEtatTransactionViaApi: async (job, genre, id) => {
      appelsApi.push(`${genre}:${id}`);
      const lu = api[`${genre}:${id}`];
      return lu === undefined ? { _error: "api muette (simule)" } : lu;
    },
    logJob: async (id, step, status, message, data) => { journal.push({ step, status, message, data }); },
  };
  vm.createContext(contexte);
  const r3 = eteint ? morceaux.r3.replace("const R3_CONTROLE_CARNET = true;", "const R3_CONTROLE_CARNET = false;") : morceaux.r3;
  vm.runInContext([morceaux.meme, morceaux.table, morceaux.ancien, r3,
    "this.controler = controlerLeCarnet; this.meme = memeValeurHektor; this.ancien = marquerLeCarnetRestant;"].join("\n"), contexte);
  return { contexte, appelsApi, supprimes, patches, journal };
}
const verdictDe = (m, cle) => { const p = m.patches.find((x) => x.cle === cle); return p ? p.etat : (m.supprimes.includes(cle) ? "arrivee" : "—"); };

// ── le compromis 50129 du 22/10 (VA6482 / 24113), relu tel que Hektor l'a rendu ──
const REG_50129 = { app_affaire_id: 1001375, kind: "compromis", hektor_affaire_id: "50129", last_seen_at: ECRIT,
                    numero_mandat: "18787", honoraires_sortie: null, notaire_acquereur_id: "10064499" };
const L = (champ, valeur, extra = {}) => ({ app_affaire_id: 1001375, champ, valeur_app: valeur, valeur_hektor_au_moment: null,
                                            origine: "creation_app", ecrit_le: ECRIT, etat: null, constate_le: null, ...extra });
const LIGNES_50129 = [L("montant", "135000"), L("date", "2026-10-22"), L("date_acte", "2027-02-15"), L("sequestre", "6000"),
  L("prix_net_vendeur", "126000"), L("honoraires_entree", "9000"), L("jours_retractation", "10"), L("prix_publique", "135000"),
  L("numero_mandat", "18787"), L("notaire_id", "10064499"), L("jours_validite", "10")];
const CHEZ_50129 = { dateStart: "2026-10-22", dateEnd: "2026-11-01", dateSignatureActe: "2027-02-15", sequestre: "6000.00",
  prixNetVendeur: "126000.00", prixPublique: "135000.00", honorairesEntree: "9000.00", honorairesSortie: "0.00", status: "1" };

(async () => {
  {
    const m = monter();
    controle("(2) dates : un jour sans heure = le meme jour avec heure",
      m.contexte.meme("2026-10-06", "2026-10-06 16:12:54") === true && m.contexte.meme("2026-10-06 16:12:54", "2026-10-06") === true
      && m.contexte.meme("2026-10-06", "2026-10-07 10:00:00") === false && m.contexte.meme("168500", "168500.00") === true
      && m.contexte.meme("2026-10-06", "2026-10-06") === true);
  }
  {
    // TEMOIN INVERSE : l'ancien verdict, sur les lignes d'une creation, ne sait rien dire
    const m = monter({ registres: [REG_50129], lignes: LIGNES_50129.map((l) => ({ champ: l.champ, valeur_app: l.valeur_app, valeur_hektor_au_moment: null })) });
    await m.contexte.ancien(JOB, 1001375);
    const inconnus = m.patches.filter((p) => p.etat === "inconnu").length;
    controle("(3) TEMOIN INVERSE : l'ancien verdict rend « inconnu » pour une creation (le defaut D3)",
      inconnus === LIGNES_50129.length && m.supprimes.length === 0, `${inconnus} inconnu(s), ${m.supprimes.length} retiree(s)`);
  }
  {
    const m = monter({ registres: [REG_50129], lignes: LIGNES_50129, travaux: [{ status: "done", created_at: ECRIT }] });
    const r = await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: CHEZ_50129, force: true });
    const arrivees = ["montant", "date", "date_acte", "sequestre", "prix_net_vendeur", "honoraires_entree", "jours_retractation", "prix_publique"];
    controle("(4) creation du compromis : les 8 champs relus sont « arrivee » et SORTENT du carnet",
      arrivees.every((c) => m.supprimes.includes(`1001375:${c}`)) && m.supprimes.length === 8, JSON.stringify(m.supprimes));
    controle("(4) ... la retractation se juge par dateEnd - dateStart (10 jours)", m.supprimes.includes("1001375:jours_retractation"));
    controle("(4) ... mandat et notaire attendent la nuit (« en_attente »)",
      verdictDe(m, "1001375:numero_mandat") === "en_attente" && verdictDe(m, "1001375:notaire_id") === "en_attente",
      JSON.stringify(m.patches));
    controle("(4) ... la validite (champ d'offre) est « sans_objet » sur un compromis", verdictDe(m, "1001375:jours_validite") === "sans_objet");
    controle("(4) ... aucune lecture de plus chez Hektor (la relecture etait en main)", m.appelsApi.length === 0 && r.status === "fait",
      JSON.stringify(m.appelsApi));
  }
  {
    // LE LENDEMAIN : la nuit a relu le compromis ; le registre porte le notaire de HEKTOR (122190)
    const reg = { ...REG_50129, last_seen_at: NUIT, notaire_acquereur_id: "122190" };
    const lignes = [L("numero_mandat", "18787", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" }),
                    L("notaire_id", "10064499", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" })];
    const m = monter({ registres: [reg], lignes, travaux: [{ status: "done", created_at: ECRIT }],
                       contacts: [{ hektor_contact_id: "10064499", hektor_target_id: "122190" }],
                       api: { "compromis:50129": { trouve: true, details: CHEZ_50129 } } });
    await m.contexte.controler(JOB, "24113");
    controle("(5) lendemain : le mandat et le notaire (la MEME personne sous deux numeros) sont « arrivee »",
      m.supprimes.includes("1001375:numero_mandat") && m.supprimes.includes("1001375:notaire_id"), JSON.stringify({ s: m.supprimes, p: m.patches }));
    controle("(5) ... une seule lecture par numero chez Hektor", m.appelsApi.length === 1, JSON.stringify(m.appelsApi));
  }
  {
    const reg = { ...REG_50129, last_seen_at: NUIT, notaire_acquereur_id: "999999" };
    const lignes = [L("notaire_id", "10064499", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" })];
    const m = monter({ registres: [reg], lignes, travaux: [{ status: "done", created_at: ECRIT }],
                       contacts: [{ hektor_contact_id: "10064499", hektor_target_id: "122190" }],
                       api: { "compromis:50129": { trouve: true, details: CHEZ_50129 } } });
    await m.contexte.controler(JOB, "24113");
    controle("(6) lendemain : un AUTRE notaire chez Hektor -> « conflit »", verdictDe(m, "1001375:notaire_id") === "conflit", JSON.stringify(m.patches));
  }
  {
    const m = monter({ registres: [REG_50129], lignes: [L("montant", "135000")], travaux: [{ status: "done", created_at: ECRIT }] });
    await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: { ...CHEZ_50129, prixPublique: "140000.00" }, force: true });
    controle("(7) Hektor a garde un autre prix -> « conflit », la ligne reste", verdictDe(m, "1001375:montant") === "conflit" && !m.supprimes.length);
  }
  {
    // l'offre 33098 (61672) : la liste ne rend que les honoraires ; montant, validite, date PAR NUMERO
    const reg = { app_affaire_id: 1001361, kind: "offre", hektor_affaire_id: "33098", last_seen_at: ECRIT, numero_mandat: "18426" };
    const O = (c, v) => ({ ...L(c, v), app_affaire_id: 1001361 });
    const m = monter({ registres: [reg], travaux: [{ status: "done", created_at: ECRIT }],
      lignes: [O("montant", "16000"), O("date", "2026-10-06"), O("jours_validite", "10"), O("prix_publique", "180000"),
               O("jours_retractation", "10"), O("numero_mandat", "18426")],
      api: { "offre:33098": { trouve: true, details: { montant: "16000", validite: "10", dateProposition: "2026-10-06" } } } });
    await m.contexte.controler(JOB, "61672", { appAffaireId: 1001361, chez: { honoraire_acquereur: "0" }, force: true });
    controle("(8) offre : montant, date et validite « arrivee », relus PAR NUMERO (1 lecture)",
      ["montant", "date", "jours_validite"].every((c) => m.supprimes.includes(`1001361:${c}`)) && m.appelsApi.length === 1,
      JSON.stringify({ s: m.supprimes, a: m.appelsApi }));
    controle("(8) ... prix de l'annonce et retractation : « sans_objet » sur une offre",
      verdictDe(m, "1001361:prix_publique") === "sans_objet" && verdictDe(m, "1001361:jours_retractation") === "sans_objet");
  }
  {
    // 30712 / offre 33094 : la modification du 13/10 a ECHOUE (offre acceptee). Hektor dit 16 000.
    const T = "2026-10-13T09:37:38.900921+00:00";
    const reg = { app_affaire_id: 30712, kind: "offre", hektor_affaire_id: "33094", last_seen_at: NUIT, numero_mandat: "18426" };
    const M = (c, v, photo) => ({ app_affaire_id: 30712, champ: c, valeur_app: v, valeur_hektor_au_moment: photo,
                                  origine: "modification_app", ecrit_le: T, etat: null, constate_le: null });
    const m = monter({ registres: [reg], travaux: [{ status: "error", created_at: T }],
      lignes: [M("montant", "160000", "16000"), M("jours_validite", "10", "10"), M("date", "2026-10-06", "2026-10-06 16:12:54")],
      api: { "offre:33094": { trouve: true, details: { montant: "16000", validite: "10", dateProposition: "2026-10-06" } } } });
    await m.contexte.controler(JOB, "61672");
    controle("(9) travail ECHOUE : le 160 000 jamais arrive -> « echec » (pas « en_attente »)", verdictDe(m, "30712:montant") === "echec", JSON.stringify(m.patches));
    controle("(9) ... ce qui est quand meme chez Hektor (validite, date) sort du carnet",
      m.supprimes.includes("30712:jours_validite") && m.supprimes.includes("30712:date"), JSON.stringify(m.supprimes));
  }
  {
    const m = monter({ registres: [REG_50129], lignes: [L("montant", "135000")], travaux: [{ status: "pending", created_at: ECRIT }],
                       api: { "compromis:50129": { trouve: true, details: CHEZ_50129 } } });
    await m.contexte.controler(JOB, "24113");
    controle("(10) travail ENCORE EN COURS -> on ne juge pas", !m.patches.length && !m.supprimes.length);
  }
  {
    const m = monter({ registres: [REG_50129], lignes: [L("montant", "135000")], travaux: [] });
    const r = await m.contexte.controler(JOB, "24113");
    controle("(11) REGLE DE LA COUPURE : API muette -> rien n'est juge, aucune alarme",
      !m.patches.length && !m.supprimes.length && r.status === "fait" && r.bilan[0].resultat === "non_juge"
      && !m.journal.some((j) => j.status === "error"), JSON.stringify({ r, j: m.journal }));
  }
  {
    const recent = new Date(Date.now() - 3600 * 1000).toISOString();
    const m = monter({ registres: [REG_50129], lignes: [L("numero_mandat", "18787", { etat: "en_attente", constate_le: recent })],
                       api: { "compromis:50129": { trouve: true, details: CHEZ_50129 } } });
    const r = await m.contexte.controler(JOB, "24113");
    controle("(12) vu il y a 1 h : la relecture ne relit PAS chez Hektor (6 h)", m.appelsApi.length === 0 && r.status === "rien_a_juger", JSON.stringify(r));
  }
  {
    const lignes = [L("taux_honoraires", "5"), L("honoraires", "9000")];
    const chez = { ...CHEZ_50129, honorairesSortie: "9000.00", prixPublique: "180000.00" };
    const m = monter({ registres: [REG_50129], lignes, travaux: [{ status: "done", created_at: ECRIT }] });
    await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez, force: true });
    const m2 = monter({ registres: [REG_50129], lignes: [L("taux_honoraires", "7")], travaux: [{ status: "done", created_at: ECRIT }] });
    await m2.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez, force: true });
    controle("(13) taux recalcule : 9 000 / 180 000 = 5 % -> « arrivee » ; un taux faux reste « en_attente », jamais « conflit »",
      m.supprimes.includes("1001375:taux_honoraires") && m.supprimes.includes("1001375:honoraires")
      && verdictDe(m2, "1001375:taux_honoraires") === "en_attente", JSON.stringify({ a: m.supprimes, b: m2.patches }));
  }
  {
    const m = monter({ erreur: true });
    let jete = false; let r = null;
    try { r = await m.contexte.controler(JOB, "24113"); } catch (_) { jete = true; }
    controle("(14) une erreur de Supabase ne fait PAS echouer le travail", !jete && r.status === "error"
      && m.journal.some((j) => j.step === "app_carnet_controle"), JSON.stringify({ jete, r }));
  }
  {
    const m = monter({ registres: [REG_50129], lignes: LIGNES_50129, eteint: true });
    const r = await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: CHEZ_50129, force: true });
    controle("(15) TEMOIN : interrupteur a false -> rien n'est lu, rien n'est ecrit",
      r.status === "eteint" && !m.patches.length && !m.supprimes.length && !m.appelsApi.length);
  }

  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`); process.exit(2); });
