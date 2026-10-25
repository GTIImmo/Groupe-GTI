// R3 -- LE CONTROLE AU RETOUR DE LA CREATION : essai hors ligne (chantier 8).        23/10/2026
//
// On eprouve LE CODE REEL (decoupe dans console_job_worker.js : memeValeurHektor, le bloc R3,
// et l'ancien marquerLeCarnetRestant pour le temoin inverse), monte avec un faux Supabase et une
// fausse API qui enregistrent ce qu'on leur demande. Les valeurs sont celles des essais reels du
// 22-23/10 (compromis 50129 sur VA6482, offres 33098 et 33094 sur 61672).
//
// 23/10 apres-midi : LA REGLE DE SORTIE DU 16/09 RETABLIE (note du registre, section 16) -- une ligne
// « arrivee » ne quitte le carnet que si le REGISTRE porte la meme valeur ; les champs sans colonne
// restent. Plus B (une ligne reecrite se rejuge), C (l'ancien verdict laisse a R3 ce qu'il ne sait
// pas juger), E (seules les saisies envoyees se jugent).
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

function monter({ registres = [], lignes = [], travaux = [], contacts = [], consoleLue = [], api = {}, erreur = false, eteint = false, source = null } = {}) {
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
      if (chemin.startsWith("app_affaire_console")) return consoleLue;
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
  const base = source || morceaux.r3;
  const r3 = eteint ? base.replace("const R3_CONTROLE_CARNET = true;", "const R3_CONTROLE_CARNET = false;") : base;
  vm.runInContext([morceaux.meme, morceaux.table, morceaux.ancien, r3,
    "this.controler = controlerLeCarnet; this.meme = memeValeurHektor; this.ancien = marquerLeCarnetRestant;"].join("\n"), contexte);
  return { contexte, appelsApi, supprimes, patches, journal };
}
const verdictDe = (m, cle) => { const p = m.patches.find((x) => x.cle === cle); return p ? p.etat : (m.supprimes.includes(cle) ? "arrivee" : "—"); };

// ── le compromis 50129 du 22/10 (VA6482 / 24113), relu tel que Hektor l'a rendu ──
const REG_50129 = { app_affaire_id: 1001375, kind: "compromis", hektor_affaire_id: "50129", last_seen_at: ECRIT,
                    numero_mandat: "18787", honoraires_sortie: null, notaire_acquereur_id: "10064499" };
// Le registre APRES le report (reporterAuRegistre) : ce que Hektor a retenu, dans ses colonnes.
const REG_50129_RELU = { ...REG_50129, montant: "135000.00", date: "2026-10-22", date_acte: "2027-02-15", sequestre: "6000.00",
                         prix_net_vendeur: "126000.00", honoraires_entree: "9000.00" };
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
    controle("(3) TEMOIN INVERSE : l'ancien verdict rend « inconnu » pour une creation (le defaut D3) -- sur les 8 champs a colonne",
      inconnus === 8 && m.supprimes.length === 0, `${inconnus} inconnu(s), ${m.supprimes.length} retiree(s)`);
    controle("(3c) C : les 3 champs SANS colonne (retractation, prix public, notaire) sont laisses a R3",
      !m.patches.some((p) => /:(jours_retractation|prix_publique|notaire_id)$/.test(p.cle)), JSON.stringify(m.patches));
  }
  {
    // ESSAI REEL du 23/10 (offre 33109) : apres une MODIFICATION, l'ancien verdict repassait sur les
    // lignes de la CREATION et ecrasait « sans_objet » / « en_attente » par « inconnu ».
    const reg = { ...REG_50129, montant: "135000", date: "2026-10-22" };
    const m = monter({ registres: [reg], lignes: [
      { champ: "prix_publique", valeur_app: "128787", valeur_hektor_au_moment: null, origine: "creation_app" },
      { champ: "numero_mandat", valeur_app: "18787", valeur_hektor_au_moment: null, origine: "creation_app" },
      { champ: "montant", valeur_app: "140000", valeur_hektor_au_moment: "135000", origine: "modification_app" }] });
    await m.contexte.ancien(JOB, 1001375);
    controle("(3b) apres une modification, l'ancien verdict ne touche PLUS les lignes de creation",
      !m.patches.some((p) => p.cle.endsWith(":prix_publique") || p.cle.endsWith(":numero_mandat")), JSON.stringify(m.patches));
    controle("(3b) ... et juge toujours la ligne de modification (montant : relu = photo -> en_attente)",
      m.patches.some((p) => p.cle.endsWith(":montant") && p.etat === "en_attente"), JSON.stringify(m.patches));
  }
  {
    const m = monter({ registres: [REG_50129_RELU], lignes: LIGNES_50129, travaux: [{ status: "done", created_at: ECRIT }] });
    const r = await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: CHEZ_50129, force: true });
    const sortent = ["montant", "date", "date_acte", "sequestre", "prix_net_vendeur", "honoraires_entree"];
    controle("(4) creation du compromis : les 6 champs que le REGISTRE porte a l'identique SORTENT du carnet",
      sortent.every((c) => m.supprimes.includes(`1001375:${c}`)) && m.supprimes.length === 6, JSON.stringify(m.supprimes));
    controle("(4) ... retractation (dateEnd - dateStart) et prix public : « arrivee » mais ils RESTENT (pas de colonne)",
      verdictDe(m, "1001375:jours_retractation") === "arrivee" && verdictDe(m, "1001375:prix_publique") === "arrivee"
      && !m.supprimes.includes("1001375:jours_retractation") && !m.supprimes.includes("1001375:prix_publique"), JSON.stringify(m.patches));
    controle("(4) ... le bilan le dit : 6 retirees, 2 gardees",
      r.bilan.filter((b) => b.retire === true).length === 6 && r.bilan.filter((b) => b.retire === false).length === 2, JSON.stringify(r.bilan));
    controle("(4) ... mandat et notaire attendent la nuit (« en_attente »)",
      verdictDe(m, "1001375:numero_mandat") === "en_attente" && verdictDe(m, "1001375:notaire_id") === "en_attente",
      JSON.stringify(m.patches));
    controle("(4) ... la validite (champ d'offre) est « sans_objet » sur un compromis", verdictDe(m, "1001375:jours_validite") === "sans_objet");
    controle("(4) ... aucune lecture de plus chez Hektor (la relecture etait en main)", m.appelsApi.length === 0 && r.status === "fait",
      JSON.stringify(m.appelsApi));
  }
  {
    // LE LENDEMAIN : la nuit a relu le compromis. ⑧ piece 3 (24/10) : la colonne porte NOTRE numero ;
    // le notaire de HEKTOR (122190) se lit dans la lecture de l'assistant (app_affaire_console).
    const reg = { ...REG_50129, last_seen_at: NUIT, notaire_acquereur_id: "10064499" };
    const lignes = [L("numero_mandat", "18787", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" }),
                    L("notaire_id", "10064499", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" })];
    const m = monter({ registres: [reg], lignes, travaux: [{ status: "done", created_at: ECRIT }],
                       contacts: [{ hektor_contact_id: "10064499", hektor_target_id: "122190" }],
                       consoleLue: [{ app_affaire_id: 1001375, notaires_acquereur: ["122190"], lu_le: NUIT }],
                       api: { "compromis:50129": { trouve: true, details: CHEZ_50129 } } });
    await m.contexte.controler(JOB, "24113");
    controle("(5) lendemain : le mandat et le notaire (la MEME personne sous deux numeros) sont « arrivee »",
      m.supprimes.includes("1001375:numero_mandat") && verdictDe(m, "1001375:notaire_id") === "arrivee", JSON.stringify({ s: m.supprimes, p: m.patches }));
    controle("(5) ... le mandat sort (registre identique), le notaire RESTE (pas de colonne)",
      m.supprimes.length === 1 && !m.supprimes.includes("1001375:notaire_id"), JSON.stringify(m.supprimes));
    // ⑧ R3 (25/10) : mandat (registre) et notaire (assistant) se lisent dans NOTRE base -- plus aucune lecture
    //   chez Hektor pour eux (c'etait 1 avant le tri « lire Hektor seulement si une ligne en a besoin »).
    controle("(5) ... AUCUNE lecture chez Hektor : mandat et notaire se lisent dans notre base", m.appelsApi.length === 0, JSON.stringify(m.appelsApi));
  }
  {
    const reg = { ...REG_50129, last_seen_at: NUIT, notaire_acquereur_id: "10064499" };
    const lignes = [L("notaire_id", "10064499", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" })];
    const m = monter({ registres: [reg], lignes, travaux: [{ status: "done", created_at: ECRIT }],
                       contacts: [{ hektor_contact_id: "10064499", hektor_target_id: "122190" }],
                       consoleLue: [{ app_affaire_id: 1001375, notaires_acquereur: ["999999"], lu_le: NUIT }],
                       api: { "compromis:50129": { trouve: true, details: CHEZ_50129 } } });
    await m.contexte.controler(JOB, "24113");
    controle("(6) lendemain : un AUTRE notaire chez Hektor -> « conflit »", verdictDe(m, "1001375:notaire_id") === "conflit", JSON.stringify(m.patches));
  }
  // ── ⑧ piece 3 (24/10) : le notaire se juge contre la SOURCE DE HEKTOR, jamais contre notre colonne ──
  const PIEGE = () => ({
    registres: [{ ...REG_50129, last_seen_at: NUIT, notaire_acquereur_id: "10064499" }],
    lignes: [L("notaire_id", "10064499", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" })],
    travaux: [{ status: "done", created_at: ECRIT }],
    contacts: [{ hektor_contact_id: "10064499", hektor_target_id: "122190" }],
    api: { "compromis:50129": { trouve: true, details: CHEZ_50129 } } });
  {
    const m = monter(PIEGE());
    await m.contexte.controler(JOB, "24113");
    controle("(6b) LE PIEGE : la colonne porte NOTRE numero et l'assistant n'a rien lu -> « en_attente », PAS « arrivee »",
      verdictDe(m, "1001375:notaire_id") === "en_attente", JSON.stringify(m.patches));
  }
  {
    // TEMOIN INVERSE du piege : la regle d'AVANT (git HEAD) dit « arrivee » sur la seule colonne
    let ancienR3 = null;
    try {
      // 25/10 : la version d'avant la piece 3 est FIGEE (41f0f2c^) -- HEAD porte la piece 3 depuis son commit.
      const head = require("child_process").execFileSync("git", ["show", "41f0f2c^:Console/console_job_worker.js"],
        { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
      const a = head.indexOf("const R3_CONTROLE_CARNET"), b = head.indexOf("// LA GARDE CONTRE LE DOUBLEMENT.");
      ancienR3 = a >= 0 && b > a ? head.slice(a, b) : null;
    } catch (_) { ancienR3 = null; }
    if (ancienR3 && !ancienR3.includes("r3NotaireDeLApi")) {
      const m = monter({ ...PIEGE(), source: ancienR3 });
      await m.contexte.controler(JOB, "24113");
      controle("(6b') TEMOIN INVERSE : la regle d'avant, sur le meme piege, disait « arrivee » sans preuve",
        verdictDe(m, "1001375:notaire_id") === "arrivee", JSON.stringify(m.patches));
    } else {
      controle("(6b') TEMOIN INVERSE : la version d'avant n'a pas pu etre lue (ou porte deja la piece 3)", false, "git show 41f0f2c^");
    }
  }
  {
    const m = monter({ ...PIEGE(), consoleLue: [{ app_affaire_id: 1001375, notaires_acquereur: ["122190"], lu_le: "2026-10-20T04:00:00Z" }] });
    await m.contexte.controler(JOB, "24113");
    controle("(6c) une lecture de l'assistant ANTERIEURE a la saisie ne prouve rien -> « en_attente »",
      verdictDe(m, "1001375:notaire_id") === "en_attente", JSON.stringify(m.patches));
  }
  {
    // la VENTE : la source est notaires_json (entree = acquereur), relu la nuit ; la colonne porte notre numero
    const VTE = { app_affaire_id: 1001395, kind: "vente", hektor_affaire_id: "23358", last_seen_at: NUIT,
                  numero_mandat: "18787", honoraires_sortie: "5000.00", notaire_acquereur_id: "10064499",
                  notaires_json: { entree: { id: "122190" }, sortie: { id: "605227" } } };
    const LV = (extra = {}) => [{ app_affaire_id: 1001395, champ: "notaire_id", valeur_app: "10064499", valeur_hektor_au_moment: null,
      origine: "creation_app", ecrit_le: ECRIT, etat: "en_attente", constate_le: "2026-10-22T21:50:00Z", ...extra }];
    const base = { travaux: [{ status: "done", created_at: ECRIT }], contacts: [{ hektor_contact_id: "10064499", hektor_target_id: "122190" }],
                   api: { "vente:23358": { trouve: true, details: { prix: "115000.00", date: "2026-10-23" } } } };
    let m = monter({ ...base, registres: [VTE], lignes: LV() });
    await m.contexte.controler(JOB, "24113");
    controle("(6d) vente : le notaire de Hektor (notaires_json, entree) est la meme personne -> « arrivee »",
      verdictDe(m, "1001395:notaire_id") === "arrivee", JSON.stringify(m.patches));
    m = monter({ ...base, registres: [{ ...VTE, notaires_json: JSON.stringify({ entree: { id: "777777" } }) }], lignes: LV() });
    await m.contexte.controler(JOB, "24113");
    controle("(6e) vente : un autre notaire chez Hektor (notaires_json en TEXTE) -> « conflit »",
      verdictDe(m, "1001395:notaire_id") === "conflit", JSON.stringify(m.patches));
    m = monter({ ...base, registres: [{ ...VTE, last_seen_at: ECRIT }], lignes: LV() });
    await m.contexte.controler(JOB, "24113");
    controle("(6f) vente : avant la nuit, notaires_json ne prouve rien -> « en_attente »",
      verdictDe(m, "1001395:notaire_id") === "en_attente", JSON.stringify(m.patches));
  }
  {
    const m = monter({ registres: [REG_50129], lignes: [L("montant", "135000")], travaux: [{ status: "done", created_at: ECRIT }] });
    await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: { ...CHEZ_50129, prixPublique: "140000.00" }, force: true });
    controle("(7) Hektor a garde un autre prix -> « conflit », la ligne reste", verdictDe(m, "1001375:montant") === "conflit" && !m.supprimes.length);
  }
  {
    // l'offre 33098 (61672) : la liste ne rend que les honoraires ; montant, validite, date PAR NUMERO
    const reg = { app_affaire_id: 1001361, kind: "offre", hektor_affaire_id: "33098", last_seen_at: ECRIT, numero_mandat: "18426",
                  montant: "16000", date: "2026-10-06 13:51:20", jours_validite: "10" };
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
    // Valeurs du PREMIER PASSAGE REEL (23/10, 09:34) : la derniere proposition date du 30/09,
    // l'offre elle-meme du 06/10 (registre relu la nuit).
    const reg = { app_affaire_id: 30712, kind: "offre", hektor_affaire_id: "33094", last_seen_at: NUIT, numero_mandat: "18426",
                  date: "2026-10-06 16:12:54", jours_validite: "10" };
    const M = (c, v, photo) => ({ app_affaire_id: 30712, champ: c, valeur_app: v, valeur_hektor_au_moment: photo,
                                  origine: "modification_app", ecrit_le: T, etat: null, constate_le: null });
    const m = monter({ registres: [reg], travaux: [{ status: "error", created_at: T }],
      lignes: [M("montant", "160000", "16000"), M("jours_validite", "10", "10"), M("date", "2026-10-06", "2026-10-06 16:12:54"),
               M("prix_publique", "180000", null)],
      api: { "offre:33094": { trouve: true, details: { montant: "16000", validite: "10", dateProposition: "2026-09-30" } } } });
    await m.contexte.controler(JOB, "61672");
    controle("(9) travail ECHOUE : le 160 000 jamais arrive -> « echec » (pas « en_attente »)", verdictDe(m, "30712:montant") === "echec", JSON.stringify(m.patches));
    controle("(9) ... ce qui est quand meme chez Hektor (validite, date DE L'OFFRE) sort du carnet",
      m.supprimes.includes("30712:jours_validite") && m.supprimes.includes("30712:date"), JSON.stringify({ s: m.supprimes, p: m.patches }));
    controle("(9) ... un champ qu'une offre n'a pas reste « sans_objet », meme travail echoue",
      verdictDe(m, "30712:prix_publique") === "sans_objet", JSON.stringify(m.patches));
  }
  {
    // ESSAI REEL du 23/10 (compromis 50130) : a la creation, le travail qui appelle le controle est
    // LUI-MEME « running ». Il jugeait 0 ligne ; ses propres lignes doivent etre jugees.
    const m = monter({ registres: [REG_50129_RELU], lignes: [L("montant", "135000")],
                       travaux: [{ id: JOB.id, status: "running", created_at: ECRIT }] });
    await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: CHEZ_50129, force: true });
    controle("(10a) a la creation, le travail lui-meme « running » juge SES lignes", m.supprimes.includes("1001375:montant"),
      JSON.stringify({ s: m.supprimes, p: m.patches }));
  }
  {
    const m = monter({ registres: [REG_50129], lignes: [L("montant", "135000")], travaux: [{ id: "un-autre", status: "pending", created_at: ECRIT }],
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
      verdictDe(m, "1001375:taux_honoraires") === "arrivee" && verdictDe(m, "1001375:honoraires") === "arrivee"
      && verdictDe(m2, "1001375:taux_honoraires") === "en_attente", JSON.stringify({ a: m.patches, b: m2.patches }));
    controle("(13) ... taux et honoraires arrives RESTENT au carnet (Hektor ne rend pas le taux ; pas de colonne)",
      !m.supprimes.length, JSON.stringify(m.supprimes));
  }
  {
    // LA REGLE DE SORTIE : Hektor porte bien 12, mais le REGISTRE porte encore 10 (report pas fait)
    const reg = { app_affaire_id: 1001377, kind: "offre", hektor_affaire_id: "33109", last_seen_at: ECRIT, jours_validite: "10" };
    const m = monter({ registres: [reg], travaux: [{ status: "done", created_at: ECRIT }],
      lignes: [{ ...L("jours_validite", "12"), app_affaire_id: 1001377, origine: "modification_app", valeur_hektor_au_moment: "10" }],
      api: { "offre:33109": { trouve: true, details: { montant: "120000", validite: "12", dateProposition: "2026-10-23" } } } });
    await m.contexte.controler(JOB, "24113");
    controle("(16) « arrivee » chez Hektor mais le REGISTRE differe -> la ligne RESTE (l'ecran perdrait la valeur)",
      verdictDe(m, "1001377:jours_validite") === "arrivee" && !m.supprimes.length, JSON.stringify({ s: m.supprimes, p: m.patches }));
  }
  {
    // B : une ligne gardee « arrivee » (le taux), REECRITE apres son verdict (il y a 1 h), se rejuge
    const vu = new Date(Date.now() - 2 * 3600 * 1000).toISOString();
    const ecrit = new Date(Date.now() - 3600 * 1000).toISOString();
    const chez = { ...CHEZ_50129, honorairesSortie: "9000.00", prixPublique: "180000.00" };
    const m = monter({ registres: [REG_50129], api: { "compromis:50129": { trouve: true, details: chez } },
      travaux: [{ status: "done", created_at: ecrit }],
      lignes: [L("taux_honoraires", "6", { origine: "modification_app", ecrit_le: ecrit, etat: "arrivee", constate_le: vu }),
               L("prix_publique", "180000", { etat: "arrivee", constate_le: vu })] });
    await m.contexte.controler(JOB, "24113");
    controle("(17) B : la ligne reecrite apres son verdict est rejugee (6 % faux -> « en_attente », plus « arrivee »)",
      verdictDe(m, "1001375:taux_honoraires") === "en_attente", JSON.stringify(m.patches));
    controle("(17) ... une ligne « arrivee » NON reecrite n'est pas rejugee",
      !m.patches.some((p) => p.cle === "1001375:prix_publique"), JSON.stringify(m.patches));
  }
  {
    // E : une correction gardee chez nous (saisie_app, classeur) ne part jamais chez Hektor
    const m = monter({ registres: [REG_50129_RELU], travaux: [],
      lignes: [L("montant", "999999", { origine: "saisie_app", ecrit_le: null }), L("date", "2026-01-01", { origine: "classeur", ecrit_le: null })] });
    const r = await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: CHEZ_50129, force: true });
    controle("(18) E : une saisie_app ou classeur n'est PAS jugee (elle dirait « conflit » a tort)",
      !m.patches.length && !m.supprimes.length && r.status === "rien_a_juger", JSON.stringify({ r, p: m.patches }));
  }
  {
    // C : apres une modification, l'ancien verdict ne repasse plus en « inconnu » ce que R3 juge
    const reg = { ...REG_50129, montant: "140000" };
    const lignes = [{ champ: "taux_honoraires", valeur_app: "5", valeur_hektor_au_moment: null, origine: "modification_app" },
                    { champ: "jours_retractation", valeur_app: "14", valeur_hektor_au_moment: null, origine: "modification_app" },
                    { champ: "montant", valeur_app: "140000", valeur_hektor_au_moment: "135000", origine: "modification_app" }];
    const m = monter({ registres: [reg], lignes });
    await m.contexte.ancien(JOB, 1001375);
    const m2 = monter({ registres: [reg], lignes, eteint: true });
    await m2.contexte.ancien(JOB, 1001375);
    controle("(19) C : R3 allume -> l'ancien verdict laisse taux et retractation a R3, et juge toujours le montant",
      !m.patches.some((p) => /:(taux_honoraires|jours_retractation)$/.test(p.cle)) && m.supprimes.includes("1001375:montant"),
      JSON.stringify({ s: m.supprimes, p: m.patches }));
    controle("(19) ... TEMOIN : R3 eteint -> l'ancien verdict reprend tout (« inconnu »), comportement d'avant",
      m2.patches.filter((p) => p.etat === "inconnu").length === 2, JSON.stringify(m2.patches));
  }
  {
    // F1 -- ESSAI REEL du compromis 50131 (23/10) : 120 000 de prix public, 5 000 d'honoraires acquereur,
    // donc 115 000 de prix de vente -- que le carnet range sous `prix_publique`.
    const chez = { ...CHEZ_50129, prixPublique: "120000.00", honorairesSortie: "5000.00" };
    const m = monter({ registres: [REG_50129_RELU], lignes: [L("prix_publique", "115000")], travaux: [{ status: "done", created_at: ECRIT }] });
    await m.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez, force: true });
    const m2 = monter({ registres: [REG_50129_RELU], lignes: [L("prix_publique", "110000")], travaux: [{ status: "done", created_at: ECRIT }] });
    await m2.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez, force: true });
    const m3 = monter({ registres: [REG_50129_RELU], lignes: [L("prix_publique", "115000")], travaux: [{ status: "done", created_at: ECRIT }] });
    await m3.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: { ...chez, honorairesSortie: undefined }, force: true });
    controle("(20) F1 : prix de vente 115 000 = 120 000 - 5 000 -> « arrivee » (plus de faux conflit), la ligne reste",
      verdictDe(m, "1001375:prix_publique") === "arrivee" && !m.supprimes.length, JSON.stringify(m.patches));
    controle("(20) ... un VRAI ecart (110 000) reste un « conflit »", verdictDe(m2, "1001375:prix_publique") === "conflit", JSON.stringify(m2.patches));
    controle("(20) ... sans honoraires relus, on ne deduit rien : « en_attente »", verdictDe(m3, "1001375:prix_publique") === "en_attente", JSON.stringify(m3.patches));
  }
  {
    // A L'OFFRE, honoraires / taux / notaire sont GARDES CHEZ NOUS : R3 ne les controle pas (offre 33110).
    const reg = { app_affaire_id: 1001378, kind: "offre", hektor_affaire_id: "33110", last_seen_at: ECRIT,
                  montant: "120000", date: "2026-10-23", jours_validite: "15" };
    const O = (c, v) => ({ ...L(c, v), app_affaire_id: 1001378 });
    const m = monter({ registres: [reg], travaux: [{ status: "done", created_at: ECRIT }],
      lignes: [O("montant", "120000"), O("honoraires", "5000"), O("taux_honoraires", "4.17"), O("notaire_id", "10064499")],
      api: { "offre:33110": { trouve: true, details: { montant: "120000", validite: "15", dateProposition: "2026-10-23" } } } });
    await m.contexte.controler(JOB, "24113", { appAffaireId: 1001378, chez: { honoraire_acquereur: "5000" }, force: true });
    controle("(21) offre : honoraires, taux et notaire NE SONT PAS controles (aucune ecriture), le montant l'est",
      !m.patches.some((p) => /:(honoraires|taux_honoraires|notaire_id)$/.test(p.cle))
      && !m.supprimes.some((s) => /:(honoraires|taux_honoraires|notaire_id)$/.test(s))
      && m.supprimes.includes("1001378:montant"), JSON.stringify({ s: m.supprimes, p: m.patches }));
    const m2 = monter({ registres: [REG_50129_RELU], lignes: [L("honoraires", "9000"), L("taux_honoraires", "5")], travaux: [{ status: "done", created_at: ECRIT }] });
    await m2.contexte.controler(JOB, "24113", { appAffaireId: 1001375, chez: { ...CHEZ_50129, honorairesSortie: "9000.00", prixPublique: "180000.00" }, force: true });
    controle("(21) ... TEMOIN : au COMPROMIS, honoraires et taux restent controles",
      verdictDe(m2, "1001375:honoraires") === "arrivee" && verdictDe(m2, "1001375:taux_honoraires") === "arrivee", JSON.stringify(m2.patches));
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

  // ── ⑧ R3 (25/10/2026) : LE RATTRAPAGE SANS RELECTURE (etude §17-19) ──
  // (22a-c) LE CODE REEL de handleRefreshConsoleData, avec des faux qui notent ce qu'on appelle.
  function monterRelecture() {
    const appels = [];
    const ctx = { console, JSON, String, Number, Date, Object, Array, encodeURIComponent,
      safeJsonParse: (x) => (typeof x === "string" ? JSON.parse(x) : (x || {})),
      logJob: async () => {},
      runCreatedAnnonceImmediateSync: async () => { appels.push("relecture"); return { synced: true }; },
      supabaseRequest: async (c) => { appels.push("supabase:" + String(c).split("?")[0]); return []; },
      reconcileSignatureStates: async () => { appels.push("signatures"); return 0; },
      cleanupProvisionalForAnnonce: async () => { appels.push("provisoire"); },
      poserNumerosManquants: async () => { appels.push("numeros"); return null; },
      controlerLeCarnet: async (job, a) => { appels.push("r3:" + a); return { status: "fait" }; },
      rebuildRequestedDetailCaches: async () => { appels.push("caches"); return null; } };
    vm.createContext(ctx);
    vm.runInContext(relecture + "\nthis.f = handleRefreshConsoleData;", ctx);
    return { ctx, appels };
  }
  {
    const m = monterRelecture();
    const r = await m.ctx.f({ id: "j", hektor_annonce_id: "24113",
      payload_json: JSON.stringify({ hektor_annonce_id: "24113", reason: "rattrapage_carnet", carnet_seul: true, light: true }) });
    controle("(22a) « carnet seul » : R3 est lance sur l'annonce, et RIEN d'autre (ni relecture, ni signatures, ni caches)",
      r.status === "carnet_seul" && m.appels.join(",") === "r3:24113", JSON.stringify({ r, a: m.appels }));
    controle("(22c) ... aucun index de bien n'est lu : un bien vendu, clos ou archive passe",
      !m.appels.some((a) => a.startsWith("supabase:")), JSON.stringify(m.appels));
  }
  {
    const m = monterRelecture();
    const r = await m.ctx.f({ id: "j", hektor_annonce_id: "24113",
      payload_json: JSON.stringify({ hektor_annonce_id: "24113", reason: "read_through_open", light: true }) });
    controle("(22b) TEMOIN INVERSE : sans « carnet seul », la relecture d'ouverture se fait comme avant (relecture, signatures, R3, caches)",
      r.status === "synced" && ["relecture", "signatures", "r3:24113", "caches"].every((x) => m.appels.includes(x))
      && m.appels.indexOf("relecture") < m.appels.indexOf("r3:24113"), JSON.stringify(m.appels));
  }
  // (22d-e) la vente de l'essai 5 (24113 / 23358), AVEC LA VRAIE REPONSE de l'API pour une vente : pas de detail.
  const VTE5 = { app_affaire_id: 1001395, kind: "vente", hektor_affaire_id: "23358", last_seen_at: "2026-10-25T05:01:17+00:00",
                 numero_mandat: "18787", honoraires_sortie: null, notaire_acquereur_id: "10064499",
                 notaires_json: JSON.stringify({ entree: { id: "122190" } }) };
  const ECRIT5 = "2026-10-23T17:41:19.163807+00:00";
  const LV5 = (champ, v) => ({ app_affaire_id: 1001395, champ, valeur_app: v, valeur_hektor_au_moment: null, origine: "creation_app",
                               ecrit_le: ECRIT5, etat: "en_attente", constate_le: "2026-10-23T17:41:54.678+00:00" });
  const ESSAI5 = () => ({ registres: [VTE5], lignes: [LV5("numero_mandat", "18787"), LV5("notaire_id", "10064499")],
    travaux: [{ status: "done", created_at: ECRIT5 }], contacts: [{ hektor_contact_id: "10064499", hektor_target_id: "122190" }],
    api: { "vente:23358": { trouve: true } } });
  {
    const m = monter(ESSAI5());
    await m.contexte.controler(JOB, "24113");
    controle("(22d) vente de l'essai 5 : mandat et notaire « arrivee », SANS AUCUN appel a Hektor",
      m.appelsApi.length === 0 && m.supprimes.includes("1001395:numero_mandat") && verdictDe(m, "1001395:notaire_id") === "arrivee",
      JSON.stringify({ a: m.appelsApi, s: m.supprimes, p: m.patches }));
    controle("(22d) ... le mandat sort du carnet (registre identique), le notaire reste (pas de colonne)",
      m.supprimes.length === 1 && !m.supprimes.includes("1001395:notaire_id"), JSON.stringify(m.supprimes));
  }
  {
    const m = monter({ ...ESSAI5(), source: morceaux.r3.replace("const R3_HEKTOR_SI_BESOIN = true;", "const R3_HEKTOR_SI_BESOIN = false;") });
    const r = await m.contexte.controler(JOB, "24113");
    controle("(22d') TEMOIN INVERSE : sans le tri, la meme vente n'est JAMAIS jugee (« non_juge » -- le defaut du contre-audit)",
      m.appelsApi.length === 1 && !m.patches.length && !m.supprimes.length && r.bilan.some((b) => b.resultat === "non_juge"),
      JSON.stringify({ r, a: m.appelsApi }));
  }
  {
    const m = monter({ registres: [{ ...REG_50129, last_seen_at: NUIT }], travaux: [{ status: "done", created_at: ECRIT }],
      lignes: [L("prix_publique", "135000", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" }),
               L("numero_mandat", "18787", { etat: "en_attente", constate_le: "2026-10-22T21:50:00Z" })] });
    const r = await m.contexte.controler(JOB, "24113");
    controle("(22e) TEMOIN : un compromis avec un PRIX a juger lit toujours Hektor, et l'API muette -> rien n'est juge",
      m.appelsApi.length === 1 && !m.patches.length && !m.supprimes.length && r.bilan.some((b) => b.resultat === "non_juge"),
      JSON.stringify({ r, a: m.appelsApi }));
  }

  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`); process.exit(2); });
