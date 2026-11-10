#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════════
// ENFILER LE REFUS DES OFFRES MORTES, PAR LOTS                       10/11/2026
// ═══════════════════════════════════════════════════════════════════════════════
// Demande de Frederic (10/11) apres l'audit : 526 offres « acceptees » dorment sur
// des affaires mortes, dont 514 sur des annonces ARCHIVEES. Les traiter a la main
// voudrait dire 514 ouvertures de fiche ; l'ecran ne propose meme aucun geste sur
// une archive. D'ou ce script, calque sur enqueue_photos_masquees_lot.js.
//
// ⭐ POURQUOI UN SCRIPT ET PAS UN ECRAN -- mesure du 10/11 :
//   . la base AUTORISE DEJA le geste sur une archive : app_console_can_access_dossier
//     rend TRUE pour un admin sans jamais regarder l'archivage ;
//   . le verrou est uniquement A L'ECRAN (fiche d'archive en lecture seule) ;
//   . et six scripts du projet posent deja des travaux par POST direct dans
//     app_console_job, en service_role, sans utilisateur connecte.
//   ⛔ Rien n'est force ni contourne : il manquait un chemin, pas un droit.
//
// ⛔⛔ EN BLANC PAR DEFAUT. Sans --envoyer, ce script COMPTE et n'ecrit RIEN.
//
//   node Console/enqueue_refus_offres_mortes_lot.js                    <- en blanc
//   node Console/enqueue_refus_offres_mortes_lot.js --dossiers 20,366  <- l'essai
//   node Console/enqueue_refus_offres_mortes_lot.js --envoyer --limite 25
//
// Codes de sortie : 0 pose ou rien a faire · 3 file occupee · 4 trop d'erreurs · 1 panne
// ═══════════════════════════════════════════════════════════════════════════════

const fs = require("fs");
const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const JOB_TYPE = "change_hektor_offre_status";

// La decision ne se recalcule PAS ici : elle est tracee dans la table de controle,
// qui porte pour chaque dossier LA SOURCE qui a tranche (le classeur d'abord, le
// fichier Netty ensuite, le statut du bien en dernier). Un script qui redeciderait
// tout seul ferait un second juge, et deux juges finissent par diverger.
const TABLE_DEFAUT = path.resolve(
  __dirname, "..", "notice",
  "TABLE_DE_CONTROLE_REGISTRE_2026-11-10_APRES_CHAINAGE.csv");

const ETATS_OFFRE_MORTS = new Set(["refused", "refusee"]);
const ETATS_COMPROMIS_MORTS = new Set(["cancelled", "annule"]);

// ═══════════════════════════════════════════════════════════════════════════════
// LES GARDE-FOUS
// ═══════════════════════════════════════════════════════════════════════════════
// ⛔ ① LE PLAFOND PAR NUIT. 514 refus font jusqu'a ~1 500 requetes chez Hektor ;
//   la nuit en consomme deja ~4 500 sur un quota de 13 000 a 17 000, et la regle
//   de Frederic est de rester 40 % en dessous. Le balayage des photos a paye cette
//   lecon : on etale, on ne vide pas la file d'un coup.
// ⛔ ② LA GARDE DU COMPROMIS, RECOPIEE DE LA RPC (16/09/2026). En postant
//   directement dans app_console_job, on court-circuite
//   app_geste_affaire_optimistic -- et donc son verrou « l'offre est verrouillee
//   par son compromis ». Il est reproduit ici a l'identique : une offre dont LE
//   DOSSIER porte une vente, ou un compromis non annule, n'est pas touchee.
//   ⭐ Par construction elle ne devrait jamais mordre (ce sont des offres SEULES
//     dans leur dossier) : si elle mord, c'est que la table de controle est
//     perimee, et ca doit s'arreter la.
// ⛔ ③ `etat_avant` DANS LA CHARGE. Sans lui, restaurerEtatAffaire() du worker ne
//   peut RIEN remettre si Hektor refuse : l'etat optimiste resterait faux.
// ⚠ ④ ON NE REPOSE JAMAIS CE QUI EST EN COURS ou qui vient d'echouer.
const PLAFOND_DEFAUT = 25;

function arg(nom, defaut) {
  const i = process.argv.indexOf(nom);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : defaut;
}
const ENVOYER = process.argv.includes("--envoyer");
const PLAFOND = Number(arg("--limite", PLAFOND_DEFAUT));
const CIBLES = String(arg("--dossiers", "")).split(",").map((x) => x.trim()).filter(Boolean);
const CHEMIN_TABLE = arg("--table", TABLE_DEFAUT);

async function rest(pathname, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const response = await fetch(SUPABASE_URL + "/rest/v1/" + pathname.replace(/^\/+/, ""), {
    ...options,
    headers: {
      apikey: KEY, Authorization: "Bearer " + KEY, "Content-Type": "application/json",
      ...(options.prefer ? { Prefer: options.prefer } : {}),
    },
  });
  if (!response.ok) throw new Error("Supabase " + response.status + " " + (await response.text()).slice(0, 300));
  return options.prefer === "return=minimal" ? null : response.json();
}

// ⚠ Le CSV est ecrit en utf-8-sig avec « ; » : on retire le BOM, sinon la premiere
//   colonne s'appelle « ﻿famille » et aucune cle ne correspond.
function lireTable(chemin) {
  const brut = fs.readFileSync(chemin, "utf8").replace(/^﻿/, "");
  const lignes = brut.split(/\r?\n/).filter((l) => l.trim() !== "");
  const entete = lignes.shift().split(";");
  return lignes.map((l) => {
    const cases = l.split(";");
    const o = {};
    entete.forEach((c, i) => { o[c] = (cases[i] || "").trim(); });
    return o;
  });
}

function vivante(t) {
  return !(String(t.hektor_affaire_id || "").trim() !== "" && t.present_in_hektor === false);
}

async function main() {
  console.log("═".repeat(78));
  console.log(ENVOYER ? "ENFILEMENT REEL -- des travaux vont etre poses"
                      : "EN BLANC -- rien ne sera ecrit (ajouter --envoyer pour de vrai)");
  console.log("═".repeat(78));

  // ── 1. LA DECISION, telle qu'elle a ete tracee ───────────────────────────────
  const table = lireTable(CHEMIN_TABLE);
  let dossiers = table
    .filter((r) => (r.proposition || "").startsWith("REFUSER"))
    .map((r) => ({ dossier: Number(r.dossier), bien: r.bien, source: r.source }));
  if (CIBLES.length) {
    dossiers = dossiers.filter((d) => CIBLES.includes(String(d.dossier)));
    console.log(`cibles demandees a la main : ${CIBLES.join(", ")}`);
  }
  console.log(`table de controle  : ${path.basename(CHEMIN_TABLE)}`);
  console.log(`dossiers « REFUSER l'offre » : ${dossiers.length}`);
  if (!dossiers.length) { console.log("rien a faire."); return 0; }

  // ── 2. LE REGISTRE, pour ces dossiers seulement ──────────────────────────────
  const ids = dossiers.map((d) => d.dossier);
  const transactions = [];
  for (let i = 0; i < ids.length; i += 200) {
    const tranche = ids.slice(i, i + 200);
    const page = await rest("app_affaire_ledger?select=app_affaire_id,app_chaine_id,kind,state,"
      + "hektor_affaire_id,hektor_annonce_id,present_in_hektor,montant,date"
      + "&app_chaine_id=in.(" + tranche.join(",") + ")");
    transactions.push(...page);
  }
  const parDossier = new Map();
  for (const t of transactions) {
    if (!parDossier.has(t.app_chaine_id)) parDossier.set(t.app_chaine_id, []);
    parDossier.get(t.app_chaine_id).push(t);
  }

  // ── 3. CE QUI EST DEJA EN COURS OU QUI VIENT D'ECHOUER ───────────────────────
  const dejaEnCours = new Set();
  const erreursRecentes = [];
  const enFile = await rest("app_console_job?select=hektor_annonce_id,status,error_message,finished_at"
    + "&job_type=eq." + JOB_TYPE + "&status=in.(pending,running)");
  for (const j of enFile) dejaEnCours.add(String(j.hektor_annonce_id));
  const recentes = await rest("app_console_job?select=hektor_annonce_id,error_message,finished_at"
    + "&job_type=eq." + JOB_TYPE + "&status=eq.error"
    + "&finished_at=gte." + new Date(Date.now() - 24 * 3600 * 1000).toISOString());
  for (const j of recentes) { dejaEnCours.add(String(j.hektor_annonce_id)); erreursRecentes.push(j); }
  // ⛔ LE FREIN GLOBAL, recopie du balayage : si Hektor nous rejette en serie, on
  //   NE REJOUE RIEN. Dix refus en 24 h = un signal, pas une malchance.
  if (erreursRecentes.length >= 10) {
    console.log(`⛔ ${erreursRecentes.length} erreurs en 24 h sur ce type de travail -- ON N'ENFILE RIEN.`);
    console.log("   Regarder pourquoi Hektor refuse AVANT de rejouer.");
    return 4;
  }

  // ── 4. LE TRI, cas par cas, en DISANT pourquoi on ecarte ─────────────────────
  const aPoser = [];
  const ecartes = new Map();
  const ecarter = (quoi, detail) => {
    ecartes.set(quoi, (ecartes.get(quoi) || 0) + 1);
    if (detail) console.log(`   ecartee -- ${detail}`);
  };

  for (const d of dossiers) {
    const membres = (parDossier.get(d.dossier) || []).filter(vivante);
    if (!membres.length) { ecarter("dossier introuvable au registre"); continue; }

    const offres = membres.filter((t) => t.kind === "offre"
      && !ETATS_OFFRE_MORTS.has(String(t.state || "").toLowerCase()));
    if (!offres.length) { ecarter("plus aucune offre vivante -- deja refusee ?"); continue; }

    // ⛔ LA GARDE DE LA RPC, A L'IDENTIQUE (16/09). On ne lit QUE le dossier de
    //   cette offre : une offre d'un autre acquereur, dans un autre dossier du
    //   meme bien, reste libre.
    const bloc = membres.find((t) => t.kind === "vente")
      || membres.find((t) => t.kind === "compromis"
           && !ETATS_COMPROMIS_MORTS.has(String(t.state || "").toLowerCase()));
    if (bloc) {
      ecarter("offre VERROUILLEE par son dossier",
        `dossier ${d.dossier} : il porte ${bloc.kind === "vente" ? "une vente" : "un compromis en cours"}`
        + ` (n° ${bloc.hektor_affaire_id || "?"}) -- la table de controle est peut-etre perimee`);
      continue;
    }

    for (const offre of offres) {
      const idOffre = String(offre.hektor_affaire_id || "").trim();
      if (!idOffre) { ecarter("offre sans numero Hektor -- le worker la jetterait"); continue; }
      const annonce = String(offre.hektor_annonce_id || d.bien || "").trim();
      if (!annonce) { ecarter("pas de numero d'annonce"); continue; }
      if (dejaEnCours.has(annonce)) { ecarter("un travail est deja en cours ou vient d'echouer"); continue; }
      aPoser.push({
        job_type: JOB_TYPE,
        hektor_annonce_id: annonce,
        status: "pending",
        // ⚠ PRIORITE BASSE EXPRES. Les gestes humains (priorite 7) doivent passer
        //   AVANT un menage de fond : personne n'attend derriere ces 514 refus.
        priority: 60,
        payload_json: {
          // ⚠ LA CLE EST `type`, PAS `geste` -- le handler jette le travail sinon
          //   (handleChangeHektorOffreStatus, console_job_worker.js l. 23667).
          type: "refus",
          hektor_offre_id: idOffre,
          hektor_annonce_id: annonce,
          app_affaire_id: offre.app_affaire_id,
          // ⛔ SANS LUI, restaurerEtatAffaire() NE PEUT RIEN REMETTRE si Hektor refuse.
          etat_avant: offre.state,
          etat_apres: "refused",
          // ⭐⭐ PAS DE RELECTURE INDIVIDUELLE (10/11/2026). Mesure : le geste prend
          //   16,6 s, sa resynchro 26,7 s. Sur 524 refus, les relectures ajoutent
          //   4 h 27 et TRENTE FOIS le trafic d'une journee normale (18 resynchros),
          //   pour une information que le run de nuit relit en un seul passage.
          //   Le worker lit ce drapeau dans enqueueRefreshConsoleDataJobBestEffort
          //   et l'ecrit au journal : une relecture sautee n'est jamais silencieuse.
          // ⛔ IL N'EST POSE QUE PAR CE SCRIPT. Aucun geste humain ne le porte, donc
          //   aucun clic ne perd sa relecture.
          sans_resynchro: true,
          // La trace de QUI a decide, et SUR QUELLE SOURCE. Un menage de masse sans
          // cette trace est indefendable six mois plus tard.
          origine: "enqueue_refus_offres_mortes_lot",
          decide_par: d.source,
          table_de_controle: path.basename(CHEMIN_TABLE),
        },
      });
    }
  }

  // ── 5. LE COMPTE RENDU, AVANT d'ecrire ───────────────────────────────────────
  console.log("");
  console.log(`a poser (avant plafond) : ${aPoser.length}`);
  for (const [quoi, n] of [...ecartes].sort((a, b) => b[1] - a[1])) {
    console.log(`   ecartees -- ${quoi} : ${n}`);
  }
  const lot = aPoser.slice(0, PLAFOND);
  console.log(`plafond ${PLAFOND} -> ${lot.length} travail(aux) dans ce lot`);
  console.log("");
  for (const j of lot) {
    console.log(`   annonce ${j.hektor_annonce_id} . offre Hektor ${j.payload_json.hektor_offre_id}`
      + ` . affaire ${j.payload_json.app_affaire_id} . etat ${j.payload_json.etat_avant} -> refused`
      + ` . decide par ${j.payload_json.decide_par}`);
  }

  if (!ENVOYER) {
    console.log("");
    console.log("EN BLANC : aucun travail n'a ete pose. Ajouter --envoyer pour de vrai.");
    return 0;
  }
  if (!lot.length) { console.log("rien a poser."); return 0; }

  // ── 6. L'ECRITURE, par tranches ──────────────────────────────────────────────
  for (let i = 0; i < lot.length; i += 50) {
    const tranche = lot.slice(i, i + 50);
    await rest("app_console_job", { method: "POST", prefer: "return=minimal", body: JSON.stringify(tranche) });
    console.log(`   pose ${i + tranche.length} / ${lot.length}`);
  }

  // ── 7. ⭐⭐ L'ETAT CHEZ NOUS -- LE MAILLON QUI MANQUAIT (10/11/2026) ──────────
  //
  // ⛔ CE DEFAUT A ETE MESURE EN REEL, pas suppose. Essai du 10/11 sur les offres
  //   10014 et 10136 (annonces 40 et 1122, archivees) : Hektor les a REFUSEES --
  //   la fiche Hektor porte « Offre de l'acquereur CASSONE Boris pour 53 000 EUR
  //   refusee », datee du jour -- et notre registre les montrait encore
  //   « accepted ». Le geste avait reussi ; c'est notre cote qui n'avait pas suivi.
  //
  // POURQUOI. Le handler du worker ne pose JAMAIS l'etat. Son contrat, ecrit dans
  // son propre commentaire, est : « L'etat est DEJA pose dans l'app (instantane).
  // Si Hektor refuse, on le remet. » C'est la RPC app_geste_affaire_optimistic qui
  // le pose, dans la meme transaction que le travail. En postant directement dans
  // app_console_job, ce script avait RETIRE ce maillon -- donc personne ne posait
  // l'etat, et il n'y avait rien a restaurer non plus.
  //
  // ⚠ L'ORDRE EST DELIBERE : le travail D'ABORD, l'etat ENSUITE. Un script REST ne
  //   peut pas etre transactionnel sur deux appels. Si l'etat echoue apres coup, le
  //   geste part quand meme chez Hektor et notre registre reste en retard d'une
  //   nuit -- le run le corrigera. L'inverse (etat d'abord) laisserait un registre
  //   qui MENT si le travail ne partait pas, et sans travail, rien ne le restaure.
  // ⚠ ON NE TOUCHE QUE `state`. Ni la date, ni le montant, ni quoi que ce soit
  //   d'autre : le reste appartient a Hektor et le run le relit.
  let etats_poses = 0;
  const etats_rates = [];
  for (const j of lot) {
    const id = j.payload_json.app_affaire_id;
    if (id == null) continue;
    try {
      await rest(`app_affaire_ledger?app_affaire_id=eq.${encodeURIComponent(String(id))}`, {
        method: "PATCH", prefer: "return=minimal",
        body: JSON.stringify({ state: j.payload_json.etat_apres }),
      });
      etats_poses += 1;
    } catch (erreur) {
      // ⛔ ON NE DEFAIT PAS LE TRAVAIL POUR AUTANT, et on ne se tait pas : le geste
      //   partira chez Hektor, et un registre en retard est reparable par le run.
      etats_rates.push(`${id} (${erreur && erreur.message ? erreur.message : erreur})`);
    }
  }

  console.log("");
  console.log(`✅ ${lot.length} travail(aux) pose(s). Le worker les prendra a sa cadence.`);
  console.log(`✅ ${etats_poses} etat(s) pose(s) chez nous (${lot.length} attendus).`);
  if (etats_rates.length) {
    console.log(`⚠ ${etats_rates.length} etat(s) NON posé(s) -- le geste part quand meme,`);
    console.log("   et le run de nuit remettra le registre d'accord avec Hektor :");
    for (const x of etats_rates.slice(0, 10)) console.log(`      ${x}`);
  }
  console.log("   Controler : select status, count(*) from app_console_job"
    + ` where job_type = '${JOB_TYPE}' group by status;`);
  return 0;
}

main().then((code) => process.exit(code)).catch((e) => {
  console.error("PANNE :", e && e.message ? e.message : e);
  process.exit(1);
});
