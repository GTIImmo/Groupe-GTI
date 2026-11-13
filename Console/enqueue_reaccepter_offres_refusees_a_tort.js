#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════════
// RÉPARER LES 20 OFFRES REFUSÉES À TORT PAR MON LOT DU 11/11      12/11/2026
// ═══════════════════════════════════════════════════════════════════════════════
// ⛔⛔ EN BLANC PAR DÉFAUT. Sans --envoyer, ce script LIT, VÉRIFIE et n'écrit RIEN.
//
// ═══════════════════════════════════════════════════════════════════════════════
// ⛔⛔⛔ NE PAS LE RELANCER SANS AVOIR LU CECI — SON EFFET DE BORD, MESURÉ LE 13/11
// ═══════════════════════════════════════════════════════════════════════════════
// ACCEPTER UNE OFFRE CHEZ HEKTOR FAIT REDESCENDRE LE STATUT DU BIEN À
// « SOUS OFFRE » — même si ce bien est VENDU depuis des années.
//
// MESURE DU 13/11, avec son témoin :
//     bien 39333  vendu en 2007  ->  « Sous offre »   touché par ce script
//     bien  5550  vendu en 2009  ->  « Sous offre »   touché
//     bien 11161  vendu en 2015  ->  « Sous offre »   touché
//     bien 36732  vendu en 2023  ->  « VENDU »        NON touché  ⭐ LE TÉMOIN
//   Quinze biens vendus portent aujourd'hui « Sous offre » à cause de ce script.
//
// ⭐ CE QUI N'A PAS ÉTÉ CASSÉ, et c'est mesuré aussi : aucun n'est reparti en
//   diffusion (14 « non_diffusable », 1 « diffusable_non_visible »). Le dégât est
//   INTERNE — un affichage faux — pas une fuite publique.
//
// ⛔⛔ ET LA RÉPARATION NAÏVE EST PIRE QUE LE MAL. Deux pièges mesurés :
//   1) remettre « Vendu » par change_hektor_annonce_status CRÉERAIT UNE VENTE :
//      HEKTOR_STATUS_CONFIG.sold porte transactionMode « createVente » ;
//   2) et app_statut_redescente_calcule() rend « ACTIF » pour ces quinze biens --
//      or « Actif » porte diffusable = 1, donc ON LES REPUBLIERAIT.
//   ⭐ LE SEUL CHEMIN SÛR est redescendreStatutHektor() avec statut_apres fourni
//     EXPLICITEMENT (« Vendu ») : un unique upval&champ=status, sans transaction
//     et sans toucher diffusable.
//
// ⭐⭐ LA LEÇON, ET ELLE A ÉTÉ PAYÉE TROIS FOIS EN TROIS JOURS :
//     11/11  refuser une offre   -> a déplacé 1 185 DATES
//     12/11  refuser une offre   -> a FABRIQUÉ 8 dates là où il n'y en avait pas
//     12/11  accepter une offre  -> a remis 15 biens vendus « Sous offre »
//   UN GESTE NE TOUCHE JAMAIS LE SEUL CHAMP QU'ON VISE. Avant d'en relancer un
//   sur des milliers de lignes : lire ce que le worker envoie, ET mesurer ce que
//   Hektor écrit en retour — pas seulement le champ qu'on croit modifier.
// ═══════════════════════════════════════════════════════════════════════════════
//
//   node Console/enqueue_reaccepter_offres_refusees_a_tort.js              <- en blanc
//   node Console/enqueue_reaccepter_offres_refusees_a_tort.js --offres 3678  <- l'essai
//   node Console/enqueue_reaccepter_offres_refusees_a_tort.js --envoyer
//
// ═══════════════════════════════════════════════════════════════════════════════
// POURQUOI CE SCRIPT EXISTE, ET C'EST UNE ERREUR DE MA PART
// ═══════════════════════════════════════════════════════════════════════════════
// Le 11/11 au soir j'ai refusé 1 185 offres chez Hektor (enqueue_refus_offres_mortes_lot.js).
// Le 12/11 au matin j'ai posé la règle D du chaînage, qui a réuni 727 dossiers.
// Résultat : 20 de ces refus portaient sur des offres QUI AVAIENT ABOUTI.
//
// ⭐ LE SCRIPT DE REFUS N'AVAIT PAS DE DÉFAUT. Sa garde était juste et explicite :
//      if (cpAnnule && !cpVivant && !vente && offreAcceptee)
//    Elle excluait bien les dossiers avec une vente ou un compromis vivant.
//    MAIS ELLE INTERROGEAIT UNE VÉRITÉ PROVISOIRE : hier soir l'offre 3678 était
//    seule dans son dossier ; ce matin la règle D l'a réunie aux trois autres
//    transactions de DEFOUR sur le bien 8454 -- dont la VENTE du 03/10/2025.
//
// ⛔ L'ERREUR EST DANS L'ORDRE, PAS DANS LE CODE : le chaînage d'abord, le geste
//   de masse ensuite. Voir la mémoire geste-de-masse-sur-chainage-incomplet.
//
// ═══════════════════════════════════════════════════════════════════════════════
// LE PÉRIMÈTRE, ET IL EST ÉTROIT PAR DÉCISION
// ═══════════════════════════════════════════════════════════════════════════════
//   offres refusees portant le nom de CELUI QUI A ACHETE        517
//     dont posees par MON lot du 11/11                           20   <- CE SCRIPT
//     dont ANTERIEURES (Hektor, 2007 -> 2026, 10 a 25 par an)   496   <- ON NE TOUCHE PAS
//
// ⛔ LES 496 AUTRES NE SONT PAS DANS CE SCRIPT. Elles sont chez Hektor depuis 2007,
//   régulièrement, bien avant nous. Les réécrire serait un geste sans mandat.
//   ⚠ Et ce n'est pas un oubli : c'est une exclusion DÉCLARÉE (règle du 14/10).
//
// ⚠ L'EFFET DE BORD, ANNONCÉ : réaccepter pose un TROISIÈME mouvement dans le
//   journal de l'offre, donc sa colonne `date` chez Hektor passera au 12/11/2026.
//   ⭐ C'est sans conséquence DEPUIS le commit 541f1be : l'écran lit désormais la
//     PREMIÈRE PROPOSITION, pas la colonne. Hier, ce geste aurait aggravé les choses.
// ═══════════════════════════════════════════════════════════════════════════════

const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const JOB_TYPE = "change_hektor_offre_status";
const SOURCE_DE_LA_DECISION = "Frederic -- alerte du 12/11/2026 sur le dossier 3676";

// ═══════════════════════════════════════════════════════════════════════════════
// LES 20, EN DUR, CHACUNE AVEC SA PREUVE
// ═══════════════════════════════════════════════════════════════════════════════
// ⚠ EN DUR ET PAS RECALCULÉ, pour la même raison que le script de refus : « un
//   script qui redéciderait tout seul ferait un second juge, et deux juges finissent
//   par diverger ». La liste vient d'UNE mesure, datée, que le script RE-VÉRIFIE
//   ligne par ligne avant d'écrire -- il refuse si la base ne dit plus la même chose.
const OFFRES = new Map([
  [1876,    { dossier: 1875,    bien: 5262,  acheteur: "GUERIN",            offre: "2024-01-12", vendu: "2024-04-10" }],
  [2087,    { dossier: 2085,    bien: 5550,  acheteur: "SENES",             offre: "2008-09-30", vendu: "2009-05-26" }],
  [3427,    { dossier: 3425,    bien: 8128,  acheteur: "GAGNE",             offre: "2008-07-21", vendu: "2009-01-31" }],
  [3678,    { dossier: 3676,    bien: 8454,  acheteur: "DEFOUR",            offre: "2025-08-14", vendu: "2025-10-03" }],
  [4747,    { dossier: 4745,    bien: 10165, acheteur: "BELLAT",            offre: "2021-03-11", vendu: "2021-06-17" }],
  [5574,    { dossier: 5572,    bien: 11161, acheteur: "GUITARD",           offre: "2015-02-21", vendu: "2015-10-23" }],
  [8018,    { dossier: 8016,    bien: 16073, acheteur: "BRETTE",            offre: "2018-02-15", vendu: "2019-03-22" }],
  [11415,   { dossier: 11412,   bien: 24119, acheteur: "MERCIER",           offre: "2021-05-18", vendu: "2021-10-29" }],
  [11597,   { dossier: 11595,   bien: 24410, acheteur: "FERNANDEZ",         offre: "2022-09-05", vendu: "2022-12-19" }],
  [11958,   { dossier: 11956,   bien: 24733, acheteur: "CIMINO",            offre: "2020-06-12", vendu: "2020-09-18" }],
  [13984,   { dossier: 13983,   bien: 28242, acheteur: "GOUSSET",           offre: "2007-03-02", vendu: "2008-05-14" }],
  [16363,   { dossier: 16362,   bien: 34048, acheteur: "GERBAUD",           offre: "2020-02-11", vendu: "2021-02-25" }],
  [17505,   { dossier: 17502,   bien: 37344, acheteur: "CHOMAT",            offre: "2019-12-20", vendu: "2020-06-19" }],
  [18957,   { dossier: 18955,   bien: 39333, acheteur: "BERGER",            offre: "2007-02-04", vendu: "2007-10-29" }],
  [19951,   { dossier: 19949,   bien: 41239, acheteur: "BOUTIN",            offre: "2015-11-04", vendu: "2016-09-02" }],
  [21137,   { dossier: 21135,   bien: 42685, acheteur: "BRIAND",            offre: "2011-11-28", vendu: "2012-08-24" }],
  [21552,   { dossier: 21551,   bien: 43091, acheteur: "CHAPUIS",           offre: "2026-03-09", vendu: "2026-07-30" }],
  [23741,   { dossier: 23738,   bien: 47065, acheteur: "BERTHEAS",          offre: "2010-02-15", vendu: "2010-06-09" }],
  [1000050, { dossier: 1000050, bien: 50119, acheteur: "MARCHINI",          offre: "2025-02-12", vendu: "2025-07-21" }],
]);

// ═══════════════════════════════════════════════════════════════════════════════
// ⛔ CELLE QU'ON LAISSE — PAR DÉCISION, PAS PAR OUBLI
// ═══════════════════════════════════════════════════════════════════════════════
// ⚠ UNE EXCLUSION SE DÉCLARE (règle du 14/10, payée).
const LAISSEES = new Map([
  [14420, {
    dossier: 14419, bien: 29285, acheteur: "M ET MME BELLAVIA",
    raison: "SON OFFRE EST DATEE APRES SA VENTE : proposee le 20/11/2009, vendue le "
          + "25/07/2008. C'est l'un des cas de « vente a date fausse chez Hektor » "
          + "deja repertories (5 cas, memoire du chainage). Le refus etait faux quand "
          + "meme -- BELLAVIA est bien l'acheteur -- mais deux defauts se superposent "
          + "ici, et on ne repare pas deux choses d'un seul geste : on ne saurait plus "
          + "laquelle a bouge. A TRAITER A PART, apres les 19.",
  }],
]);

// ═══════════════════════════════════════════════════════════════════════════════
// ⭐⭐ LE JUGE HONNETE -- ajoute le 12/11 APRES l'essai sur l'offre 3678
// ═══════════════════════════════════════════════════════════════════════════════
// L'ESSAI A MONTRE QUE NI LE WORKER NI LA RELECTURE NE PROUVENT RIEN :
//   . le travail finit « done » avec verbe « GET » et reponse_hektor « 1 » ;
//   . le refresh_console_data qui suit relit L'ANNONCE, pas les TRANSACTIONS
//     (elles ont leur propre listing, list_offres, relu la NUIT) ;
//   . donc notre registre disait encore « refused » et le journal de l'offre
//     portait toujours ses 3 evenements, SANS le 4e.
//   ⛔ A ce stade je ne POUVAIS PAS dire si Hektor avait bascule.
//
// ⭐ LE SEUL JUGE INDEPENDANT est l'API, par identifiant -- et le projet a deja
//   le script qu'il faut (phase2/sync/transaction_etat_from_api.py, porte 2,
//   ecrit le 16/09 pour cette raison exacte : « une verification qui ne depend
//   pas de l'ordre des choses »). Sur 9886 il a rendu « etat: accepte ».
//
// ⚠ UNE LECTURE RATEE N'EST PAS UN REFUS : elle rend null, et on n'ecrit RIEN.
function etatChezHektor(hektorOffreId) {
  const { execFileSync } = require("child_process");
  const py = path.resolve(__dirname, "..", ".venv", "Scripts", "python.exe");
  try {
    const brut = execFileSync(py, [
      path.resolve(__dirname, "..", "phase2", "sync", "transaction_etat_from_api.py"),
      "--kind", "offre", "--id", String(hektorOffreId),
    ], { encoding: "utf8", timeout: 90000 });
    // ⚠ Pas de barre oblique inverse ici : l'outil qui a ecrit ce fichier les
    //   avale (memoire outil-bash-avale-les-barres-obliques-inverses).
    const toutes = String(brut).trim().split(String.fromCharCode(10));
    const ligne = String(toutes[toutes.length - 1]).trim();
    const rep = JSON.parse(ligne);
    if (rep._error) return { lu: false, pourquoi: String(rep._error).slice(0, 120) };
    if (rep.trouve === false) return { lu: true, etat: "(absente de chez Hektor)" };
    return { lu: true, etat: String(((rep.details || {}).etat) || "").toLowerCase() };
  } catch (e) {
    return { lu: false, pourquoi: String(e.message || e).slice(0, 120) };
  }
}

async function rest(chemin, options = {}) {
  const reponse = await fetch(`${SUPABASE_URL}/rest/v1/${chemin}`, {
    ...options,
    headers: {
      apikey: KEY, Authorization: `Bearer ${KEY}`,
      "Content-Type": "application/json",
      Prefer: options.method === "POST" ? "return=representation" : "return=minimal",
      ...(options.headers || {}),
    },
  });
  const texte = await reponse.text();
  if (!reponse.ok) throw new Error(`${reponse.status} ${chemin} -- ${texte.slice(0, 300)}`);
  return texte ? JSON.parse(texte) : null;
}

function arg(nom) {
  const i = process.argv.indexOf(nom);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : null;
}

const ENVOYER = process.argv.includes("--envoyer");
const CIBLES = (arg("--offres") || "").split(",").map((s) => s.trim()).filter(Boolean);

async function main() {
  console.log("=".repeat(78));
  console.log(ENVOYER ? "ENVOI REEL -- des travaux vont etre poses chez Hektor"
                      : "EN BLANC -- rien ne sera ecrit (ajouter --envoyer pour de vrai)");
  console.log("=".repeat(78));
  if (!SUPABASE_URL || !KEY) { console.error("ARRET : SUPABASE_URL ou la cle service_role manque."); return 1; }

  // ── LE FREIN : on n'empile pas sur une file qui travaille deja.
  //   ⛔ Leçon du 19/10 : un redemarrage pendant un travail en cours a tue 14 photos.
  const enCours = await rest("app_console_job?select=id,job_type,status"
    + "&status=in.(pending,running)&limit=200");
  if (enCours.length) {
    const parType = {};
    for (const j of enCours) parType[j.job_type] = (parType[j.job_type] || 0) + 1;
    console.log(`file occupee : ${enCours.length} travail(aux) -- ${JSON.stringify(parType)}`);
    if (ENVOYER) { console.error("ARRET : on attend que la file soit vide."); return 3; }
    console.log("(en blanc : on continue quand meme, rien ne sera ecrit)");
  } else {
    console.log("file : vide (0 pending, 0 running)");
  }

  let cibles = [...OFFRES.keys()];
  if (CIBLES.length) {
    cibles = cibles.filter((o) => CIBLES.includes(String(o)));
    console.log(`cibles demandees a la main : ${CIBLES.join(", ")}`);
  }
  console.log(`offres a reparer   : ${cibles.length} sur ${OFFRES.size}`);
  console.log(`laissees de cote   : ${LAISSEES.size}`);
  for (const [id, l] of LAISSEES) {
    console.log(`  - offre ${id} (bien ${l.bien}, ${l.acheteur}) : ${l.raison.slice(0, 110)}...`);
  }
  console.log("");

  // ── LA RE-VERIFICATION, LIGNE PAR LIGNE. C'est elle qui rend le « en dur »
  //   honnete : la liste vient d'une mesure datee, la base dit la verite d'AUJOURD'HUI.
  const aFaire = [];
  const refusees = [];
  for (const idOffre of cibles) {
    const attendu = OFFRES.get(idOffre);
    const lignes = await rest(`app_affaire_ledger?select=app_affaire_id,app_chaine_id,kind,state,`
      + `hektor_affaire_id,hektor_annonce_id,present_in_hektor,acquereurs_json,date`
      + `&app_affaire_id=eq.${idOffre}`);
    const o = lignes[0];
    const refuser = (pourquoi) => { refusees.push({ idOffre, pourquoi }); };

    if (!o) { refuser("absente du registre"); continue; }
    if (o.kind !== "offre") { refuser(`ce n'est pas une offre (${o.kind})`); continue; }
    if (!["refused", "refusee"].includes(String(o.state || "").toLowerCase())) {
      refuser(`son etat n'est plus « refusee » mais « ${o.state} » -- deja reparee ?`); continue;
    }
    if (o.present_in_hektor === false) { refuser("absente de chez Hektor"); continue; }
    if (!o.hektor_affaire_id) { refuser("pas de numero Hektor"); continue; }
    if (String(o.hektor_annonce_id) !== String(attendu.bien)) {
      refuser(`le bien a change : ${o.hektor_annonce_id} au lieu de ${attendu.bien}`); continue;
    }

    // ⭐ ET LA PREUVE QUI COMPTE : le dossier porte-t-il TOUJOURS une vente au
    //   MEME acheteur ? C'est la seule raison de reparer. Si le chainage a encore
    //   bouge depuis ma mesure, ce controle le voit et refuse.
    const membres = await rest(`app_affaire_ledger?select=app_affaire_id,kind,state,acquereurs_json,date`
      + `&app_chaine_id=eq.${o.app_chaine_id}`);
    const noms = (blob) => {
      let charge = blob;
      if (typeof blob === "string") { try { charge = JSON.parse(blob); } catch { return []; } }
      const gens = Array.isArray(charge) ? charge : (charge && typeof charge === "object" ? [charge] : []);
      return gens.map((g) => String((g || {}).nom || "").trim().toUpperCase()).filter(Boolean).sort();
    };
    const acqOffre = noms(o.acquereurs_json).join("|");
    const vente = membres.find((m) => m.kind === "vente" && noms(m.acquereurs_json).join("|") === acqOffre);
    const cpActif = membres.find((m) => m.kind === "compromis"
      && String(m.state || "").toLowerCase() === "active"
      && noms(m.acquereurs_json).join("|") === acqOffre);
    if (!acqOffre) { refuser("l'offre n'a aucun acquereur nomme"); continue; }
    if (!vente && !cpActif) {
      refuser(`son dossier ${o.app_chaine_id} ne porte plus ni vente ni compromis actif `
        + `au nom de ${acqOffre} -- LE CHAINAGE A BOUGE depuis la mesure`); continue;
    }
    if (acqOffre !== attendu.acheteur.toUpperCase()
        && !acqOffre.includes(attendu.acheteur.toUpperCase())) {
      refuser(`l'acheteur a change : « ${acqOffre} » au lieu de « ${attendu.acheteur} »`); continue;
    }

    aFaire.push({
      idOffre, hektorOffreId: String(o.hektor_affaire_id), bien: String(o.hektor_annonce_id),
      dossier: o.app_chaine_id, acheteur: acqOffre,
      aboutissement: vente ? `vente ${vente.app_affaire_id} du ${String(vente.date || "").slice(0, 10)}`
                           : `compromis ACTIF ${cpActif.app_affaire_id}`,
    });
  }

  console.log("-".repeat(78));
  console.log(`VERIFIEES ET BONNES : ${aFaire.length}`);
  for (const f of aFaire) {
    console.log(`  offre ${String(f.idOffre).padStart(7)} (Hektor ${f.hektorOffreId.padStart(6)}) `
      + `bien ${f.bien.padStart(5)} . ${f.acheteur.padEnd(20)} . ${f.aboutissement}`);
  }
  if (refusees.length) {
    console.log("");
    console.log(`REFUSEES PAR LA VERIFICATION : ${refusees.length}`);
    for (const r of refusees) console.log(`  offre ${r.idOffre} : ${r.pourquoi}`);
  }
  console.log("-".repeat(78));

  if (!ENVOYER) {
    console.log("");
    console.log("EN BLANC : rien n'a ete ecrit. Ce qui serait pose, si --envoyer :");
    console.log(`  ${aFaire.length} travail(aux) « ${JOB_TYPE} », type « accepte »,`);
    console.log("  puis une SECONDE PASSE qui remet l'etat « accepted » dans le registre.");
    console.log("");
    console.log("  ⛔ ET POURQUOI CETTE SECONDE PASSE EST OBLIGATOIRE -- defaut attrape le");
    console.log("    12/11 au matin sur le dossier 395 : le handler du worker NE POSE JAMAIS");
    console.log("    l'etat. C'est la RPC app_geste_affaire_optimistic qui le pose, depuis");
    console.log("    l'ecran. En postant directement dans app_console_job on RETIRE ce");
    console.log("    maillon : Hektor agit, et notre registre reste sur l'ancien etat.");
    return 0;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // L'ENVOI REEL
  // ═══════════════════════════════════════════════════════════════════════════
  if (!aFaire.length) { console.log("rien a poser."); return 0; }
  const poses = [];
  for (const f of aFaire) {
    const cree = await rest("app_console_job", {
      method: "POST",
      body: JSON.stringify({
        job_type: JOB_TYPE,
        status: "pending",
        priority: 65,
        hektor_annonce_id: f.bien,
        payload_json: {
          hektor_offre_id: f.hektorOffreId,
          type: "accepte",
          hektor_annonce_id: f.bien,
          app_affaire_id: f.idOffre,
          etat_apres: "accepted",
          raison: `reparation du refus a tort du 11/11 -- ${f.aboutissement}`,
          source: SOURCE_DE_LA_DECISION,
        },
      }),
    });
    poses.push({ ...f, jobId: (cree && cree[0] && cree[0].id) || null });
    console.log(`pose : offre ${f.idOffre} -> travail ${(cree && cree[0] && cree[0].id) || "?"}`);
  }
  console.log("");
  console.log(`${poses.length} travail(aux) pose(s). Le worker les prendra avec son frein habituel.`);
  console.log("");
  console.log("⏰ ENSUITE, ET C'EST OBLIGATOIRE : quand les travaux sont « done »,");
  console.log("   relancer ce script avec --seconde-passe pour remettre l'etat du registre.");
  return 0;
}

// ═══════════════════════════════════════════════════════════════════════════════
// LA SECONDE PASSE — elle ne touche QUE les offres dont le travail est « done »
// ═══════════════════════════════════════════════════════════════════════════════
async function secondePasse() {
  console.log("=".repeat(78));
  console.log(ENVOYER ? "SECONDE PASSE REELLE -- l'etat du registre va etre remis"
                      : "SECONDE PASSE EN BLANC -- rien ne sera ecrit");
  console.log("=".repeat(78));
  let remis = 0, attente = 0, echecs = 0;
  for (const idOffre of OFFRES.keys()) {
    const jobs = await rest(`app_console_job?select=id,status,created_at,payload_json`
      + `&job_type=eq.${JOB_TYPE}&order=created_at.desc&limit=50`);
    const mien = jobs.find((j) => String((j.payload_json || {}).app_affaire_id) === String(idOffre)
      && (j.payload_json || {}).type === "accepte");
    if (!mien) continue;
    if (mien.status !== "done") {
      console.log(`offre ${idOffre} : travail ${mien.status} -- on attend`);
      if (mien.status === "error" || mien.status === "failed") echecs++; else attente++;
      continue;
    }
    const lignes = await rest(`app_affaire_ledger?select=app_affaire_id,state,hektor_affaire_id`
      + `&app_affaire_id=eq.${idOffre}`);
    const etat = String(((lignes[0] || {}).state) || "").toLowerCase();
    if (["accepted", "acceptee"].includes(etat)) { console.log(`offre ${idOffre} : deja « ${etat} »`); continue; }

    // ⛔ LA PREUVE AVANT L'ECRITURE. On ne pose pas chez nous un etat qu'on n'a
    //   pas lu chez Hektor -- « on exige LA PREUVE DU SUCCES, jamais l'absence
    //   d'erreur » (lecon du 20/10, payee sur le redemarrage du service Documents).
    const chezHektor = etatChezHektor((lignes[0] || {}).hektor_affaire_id);
    if (!chezHektor.lu) {
      console.log(`offre ${idOffre} : LECTURE RATEE chez Hektor (${chezHektor.pourquoi}) -- on n'ecrit RIEN`);
      echecs++; continue;
    }
    if (!["accepte", "acceptee", "accepted"].includes(chezHektor.etat)) {
      console.log(`offre ${idOffre} : Hektor dit « ${chezHektor.etat} » et NON « accepte » `
        + `-- le geste n'a PAS pris. On n'ecrit RIEN.`);
      echecs++; continue;
    }
    if (!ENVOYER) {
      console.log(`offre ${idOffre} : Hektor dit « ${chezHektor.etat} » -> serait remise de `
        + `« ${etat} » a « accepted »`);
      remis++; continue;
    }
    await rest(`app_affaire_ledger?app_affaire_id=eq.${idOffre}`, {
      method: "PATCH", body: JSON.stringify({ state: "accepted" }),
    });
    console.log(`offre ${idOffre} : Hektor « ${chezHektor.etat} » -> chez nous « ${etat} » devient « accepted »`);
    remis++;
  }
  console.log("-".repeat(78));
  console.log(`remis : ${remis} . en attente : ${attente} . en echec : ${echecs}`);
  if (echecs) { console.log("⛔ DES TRAVAUX ONT ECHOUE : lire app_console_job_log avant de rejouer."); return 1; }
  return 0;
}

const lancer = process.argv.includes("--seconde-passe") ? secondePasse : main;
lancer().then((code) => process.exit(code || 0)).catch((e) => {
  console.error("PANNE :", e.message);
  process.exit(1);
});
