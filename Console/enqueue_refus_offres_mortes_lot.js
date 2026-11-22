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
// ═══════════════════════════════════════════════════════════════════════════════
// ⚠⚠ SON EFFET DE BORD, MESURE LES 11, 12 ET 13/11 -- A LIRE AVANT DE LE RELANCER
// ═══════════════════════════════════════════════════════════════════════════════
// REFUSER UNE OFFRE NE CHANGE PAS QUE SON ETAT : Hektor ecrit l'horodatage du
// refus dans la colonne "date" de l'offre, ET ajoute une entree « refus » a son
// journal (propositions_json).
//
// CE QUE CA A COUTE :
//   . le 11/11, 1 185 offres ont vu leur date passer au 11/11/2026 ;
//   . sept lecteurs s'en servaient -- le registre classait 1 190 dossiers en 2026
//     a tort, et le pilotage annoncait un delai mandat->offre de 2 148 jours ;
//   . le 12/11 a 12:07, un second lot a refait le coup sur 8 offres qui n'avaient
//     AUCUNE date : le refus leur en a FABRIQUE une.
//   ⛔ Les deux fois, c'est Frederic qui l'a vu, pas un controle.
//
// ⭐ CE N'EST PLUS GRAVE AUJOURD'HUI, et c'est structurel : depuis le 13/11, le
//   lecteur app_dossier_jour_date_transaction REFUSE la colonne "date" d'une
//   offre des que son journal porte des entrees. Un refus ne peut donc plus
//   fabriquer de date. ⭐ Et la sentinelle le verifie :
//        .venv\Scripts\python.exe phase2\checks\controle_date_offre.py
//
// ⭐⭐ MAIS LA LECON RESTE, ET ELLE VAUT POUR TOUT GESTE DE MASSE :
//   UN GESTE NE TOUCHE JAMAIS QU'UN SEUL CHAMP. Avant d'en relancer un sur des
//   milliers de lignes, LIRE ce que le worker envoie et MESURER ce que Hektor
//   ecrit en retour -- pas seulement le champ qu'on vise.
// ═══════════════════════════════════════════════════════════════════════════════
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

// ═══════════════════════════════════════════════════════════════════════════════
// ⛔ LES DOSSIERS QU'ON N'ENFILE PAS -- PAR DECISION, PAS PAR OUBLI   11/11/2026
// ═══════════════════════════════════════════════════════════════════════════════
// ⚠ UNE EXCLUSION SE DECLARE. Un dossier retire en silence d'une liste de 1 158
//   est un dossier que personne ne retrouvera, et la raison du retrait sera perdue
//   avec la conversation qui l'a decidee. Regle du projet, payee le 14/10.
// Chaque entree porte : le dossier, le bien, et POURQUOI.
const DOSSIERS_EXCLUS = new Map([
  [3699, {
    bien: 8494,
    raison: "Garage VS046 au Puy-en-Velay (6 800 EUR). Sa VENTE du 21/03/2025 "
          + "(aff 3701, Hektor n° 8683) a ete SUPPRIMEE chez Hektor apres le "
          + "18/09/2026, et le premier compromis (aff 3698) apres le 07/09. Nous "
          + "les gardons par le delete-never, mais le chainage ne voit QUE ce qui "
          + "est encore chez Hektor : il ne reste donc qu'une offre acceptee et un "
          + "compromis actif, ce qui fait croire a une affaire en cours. "
          + "⛔ TANT QU'ON NE SAIT PAS si cette vente a ete supprimee EXPRES, tout "
          + "geste risque d'effacer la trace d'une affaire reelle. "
          + "Decision de Frederic, 11/11/2026.",
  }],
]);
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
// ⛔⛔ ⑤ LA GARDE DU BIEN -- 23/11/2026, demande de Frederic (son mot du 23/11, § 4 a).
//   Une offre dont LE BIEN porte une vente n'est pas touchee, quel que soit le
//   dossier ou se trouve cette vente. On la cherche par `hektor_annonce_id`, EN
//   PLUS de la chaine : la garde ② ne lit que le dossier (`app_chaine_id`), et la
//   chaine est RECALCULEE CHAQUE NUIT. Le 11/11 au soir, la vente et son offre
//   n'etaient pas encore dans la meme chaine (la regle D du 12/11 a reuni 727
//   dossiers apres coup). Le numero du bien, lui, NE CHANGE JAMAIS.
//   ⛔ CE QUE CA A COUTE : 36 offres refusees a tort chez Hektor, dont 19
//     reacceptees le 12/11 et 17 qui restent refusees (13 en « cascade », 4 en
//     « table ») -- 14 biens VENDUS sans aucune offre acceptee.
//   ⭐ SON TEMOIN, rejoue sur l'etat du 11/11 : elle retient EXACTEMENT ces 36, et
//     aucune autre (Console/test_garde_du_bien_refus_offres.js).
//   ⚠ TOUTES LES VENTES COMPTENT : supprimee chez Hektor ou non, reprise du classeur
//     ou non. Cette garde ne fait que RETENIR un geste, elle n'en declenche aucun :
//     dans le doute, on ne refuse pas (c'est la lecon du dossier 3699).
//   ⚠ Et une lecture ratee n'est pas « aucune vente » : la liste des ventes porte un
//     TEMOIN POSITIF (une vente qu'on sait exister) ; s'il manque, on n'enfile rien.
const PLAFOND_DEFAUT = 25;
// Le temoin positif de la garde ⑤ : la vente 23997 (n° Hektor 1438) du bien 47557,
// le bien de l'offre 23995 -- une des 17. Elle existe, et elle ne se supprime pas
// chez nous (« un numero ne se perd jamais »).
const TEMOIN_VENTE = { bien: "47557", vente: 23997 };

function arg(nom, defaut) {
  const i = process.argv.indexOf(nom);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : defaut;
}
const ENVOYER = process.argv.includes("--envoyer");
const PLAFOND = Number(arg("--limite", PLAFOND_DEFAUT));
const CIBLES = String(arg("--dossiers", "")).split(",").map((x) => x.trim()).filter(Boolean);
const CHEMIN_TABLE = arg("--table", TABLE_DEFAUT);
// La source de la liste : « table » (le classeur tranche) ou « cascade »
// (le dossier se contredit tout seul). Voir le bloc 1 pour la mesure des deux.
const SOURCE = String(arg("--source", "table")).toLowerCase();
if (!["table", "cascade"].includes(SOURCE)) {
  console.error(`--source doit valoir « table » ou « cascade » (recu : ${SOURCE})`);
  process.exit(1);
}

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

// ⛔⛔ ⑤ LA GARDE DU BIEN (23/11) : les ventes du bien, TOUTES (voir l'en-tete).
function ventesDuBien(ventesParBien, annonce) {
  return ventesParBien.get(String(annonce || "").trim()) || [];
}

// ── LA SELECTION « cascade », sortie de main() le 23/11 pour etre REJOUEE TELLE
//   QUELLE sur l'etat du 11/11 (le temoin de la garde ⑤). Le code est le meme.
function selectionCascade(lignes) {
  const parChaine = new Map();
  for (const t of lignes) {
    if (!vivante(t)) continue;
    // ⛔⛔ LA GARDE DE L'ORIGINE -- C.19-d, 16/11/2026. CE SCRIPT ECRIT CHEZ HEKTOR.
    //   Une transaction REPRISE DU CLASSEUR n'a jamais existe chez Hektor : elle ne
    //   doit donc ni declencher un refus, ni en etre la cible.
    //   ⛔ SANS CETTE LIGNE, poser les compromis « Annulee » du classeur suffirait a
    //     faire refuser, A LA PROCHAINE RELANCE DU LOT, les offres acceptees de leurs
    //     dossiers -- CHEZ HEKTOR, sur la foi d'une reprise d'historique. Et poser
    //     plus tard les offres « Vente reglee » (state 'accepted') les rendrait
    //     elles-memes CIBLES d'un refus chez Hektor, ou elles n'existent pas.
    //   ⚠ `vivante(t)` ne protege PAS : elle ecarte « porte un numero ET absente de
    //     Hektor », or nos lignes n'ont PAS de numero -- elles passent donc pour
    //     vivantes. Mesure du 16/11.
    //   ⭐ C'est le 6e lecteur de la famille `transaction_origine`, et LE SEUL QUI
    //     ECRIT CHEZ HEKTOR. Les cinq autres crient ou affichent : la sentinelle
    //     data.transaction_disparue, la vue app_affaires_sans_numero_hektor, le filet
    //     poserNumerosManquants, l'ecran, et le filet du cockpit
    //     (export_app_payload.py). Il avait ete manque le matin du 16/11 parce que le
    //     balayage cherchait `present_in_hektor`, alors que celui-ci se declenche sur
    //     l'ETAT d'une autre transaction de la chaine.
    //   ⚠ Et ce script a deja fait un degat : les 20 offres refusees a tort le 11/11.
    //     ⛔ 23/11 : pas 20 -- TRENTE-SIX (19 reacceptees + 17 restees refusees). Voir ⑤.
    if (String(t.transaction_origine || "").trim() !== "") continue;
    if (!parChaine.has(t.app_chaine_id)) parChaine.set(t.app_chaine_id, []);
    parChaine.get(t.app_chaine_id).push(t);
  }
  const dossiers = [];
  for (const [chaine, membres] of parChaine) {
    const cpAnnule = membres.some((t) => t.kind === "compromis"
      && ETATS_COMPROMIS_MORTS.has(String(t.state || "").toLowerCase()));
    const cpVivant = membres.some((t) => t.kind === "compromis"
      && !ETATS_COMPROMIS_MORTS.has(String(t.state || "").toLowerCase()));
    // ⚠ Ce `vente` ne regarde que la CHAINE. Il reste juste, mais il ne suffit pas :
    //   la vente du meme bien peut etre dans une autre chaine -> garde ⑤, dans trier(),
    //   qui sert aux DEUX modes.
    const vente = membres.some((t) => t.kind === "vente");
    const offreAcceptee = membres.some((t) => t.kind === "offre"
      && ["accepted", "acceptee"].includes(String(t.state || "").toLowerCase()));
    if (cpAnnule && !cpVivant && !vente && offreAcceptee) {
      const bien = String((membres.find((t) => t.hektor_annonce_id) || {}).hektor_annonce_id || "");
      dossiers.push({ dossier: chaine, bien, source: "coherence : compromis annule" });
    }
  }
  return dossiers;
}

// ── LE TRI, cas par cas, en DISANT pourquoi on ecarte -- sorti de main() le 23/11,
//   meme raison. Il sert aux DEUX modes : c'est donc ICI que vit la garde ⑤.
//   `ventesParBien` : Map bien -> ventes (TOUTES). `opts` : { source, cheminTable, dire }.
function trier(dossiers, parDossier, dejaEnCours, ventesParBien, opts = {}) {
  const source = opts.source || "table";
  const cheminTable = opts.cheminTable || TABLE_DEFAUT;
  const dire = opts.dire || ((s) => console.log(s));
  const aPoser = [];
  const ecartes = new Map();
  const ecarter = (quoi, detail) => {
    ecartes.set(quoi, (ecartes.get(quoi) || 0) + 1);
    if (detail) dire(`   ecartee -- ${detail}`);
  };

  for (const d of dossiers) {
    // ⛔ L'EXCLUSION DECLAREE PASSE AVANT TOUT, et elle se DIT a chaque passage :
    //   une liste d'exclusions muette redevient un oubli au bout de six mois.
    const exclu = DOSSIERS_EXCLUS.get(d.dossier);
    if (exclu) {
      ecarter("EXCLU PAR DECISION",
        `dossier ${d.dossier} (bien ${exclu.bien}) -- ${exclu.raison}`);
      continue;
    }
    const membres = (parDossier.get(d.dossier) || []).filter(vivante);
    if (!membres.length) { ecarter("dossier introuvable au registre"); continue; }

    const offres = membres.filter((t) => t.kind === "offre"
      && !ETATS_OFFRE_MORTS.has(String(t.state || "").toLowerCase()));
    if (!offres.length) { ecarter("plus aucune offre vivante -- deja refusee ?"); continue; }

    // ⛔ LA GARDE DE LA RPC, A L'IDENTIQUE (16/09). On ne lit QUE le dossier de
    //   cette offre : une offre d'un autre acquereur, dans un autre dossier du
    //   meme bien, reste libre.
    //   ⛔ 23/11 : SAUF SI LE BIEN PORTE UNE VENTE -- c'est la garde ⑤, plus bas.
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
      // ⛔⛔ ⑤ LA GARDE DU BIEN (23/11) -- par le NUMERO DU BIEN, qui ne change jamais.
      const ventes = ventesDuBien(ventesParBien, annonce);
      if (ventes.length) {
        ecarter("⑤ LE BIEN PORTE UNE VENTE (hors de ce dossier)",
          `offre ${idOffre} (affaire ${offre.app_affaire_id}, dossier ${d.dossier}) : le bien ${annonce}`
          + ` porte la vente ${ventes.map((v) => `${v.app_affaire_id}`
              + (v.hektor_affaire_id ? ` (n° ${v.hektor_affaire_id})` : " (sans numero)")
              + (v.app_chaine_id != null ? ` dans le dossier ${v.app_chaine_id}` : "")).join(", ")}`);
        continue;
      }
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
          // La trace dit AUSSI par quelle source il est passe : dans six mois,
          // « pourquoi cette offre a-t-elle ete refusee ? » doit avoir une reponse.
          origine: source === "cascade"
            ? "rattrapage_cascade_annulation"
            : "enqueue_refus_offres_mortes_lot",
          decide_par: d.source,
          table_de_controle: path.basename(cheminTable),
        },
      });
    }
  }
  return { aPoser, ecartes };
}

async function main() {
  console.log("═".repeat(78));
  console.log(ENVOYER ? "ENFILEMENT REEL -- des travaux vont etre poses"
                      : "EN BLANC -- rien ne sera ecrit (ajouter --envoyer pour de vrai)");
  console.log("═".repeat(78));

  // ── 1. LA DECISION -- DEUX SOURCES, ET ELLES NE SE RECOUVRENT PAS ───────────
  //
  // ⭐⭐ POURQUOI DEUX SOURCES, mesure le 11/11 sur les 9 970 offres « acceptees »
  //   vivantes du registre :
  //       8 659  leur dossier est VENDU          ⛔ NORMAL, on n'y touche jamais :
  //                                                une offre qui aboutit RESTE acceptee
  //         102  compromis encore VIVANT         ⛔ affaire EN COURS
  //         661  compromis ANNULE                -> source « cascade »
  //         548  offre SEULE, sans compromis     -> source « table »
  //   Les deux dernieres s'excluent PAR CONSTRUCTION : un dossier a un compromis
  //   ou il n'en a pas. ZERO recouvrement, donc aucun geste en double.
  //
  // ⚠ ET ELLES NE SE DECIDENT PAS DE LA MEME FACON :
  //   . « table »   une SOURCE EXTERIEURE tranche (le classeur, puis le fichier
  //                 Netty, puis le statut du bien). On lui obeit, y compris quand
  //                 elle dit GARDER -- d'ou 526 retenues sur 548.
  //   . « cascade » AUCUN juge n'est necessaire : le dossier se contredit TOUT
  //                 SEUL. Son compromis est annule, donc l'affaire a echoue, donc
  //                 l'offre ne peut pas etre restee « acceptee ». C'est de la
  //                 coherence interne, pas un arbitrage.
  //
  // ⚠ LA SOURCE « cascade » EST LE RATTRAPAGE DU PASSE. La regle posee en base le
  //   11/11 (app_geste_affaire_optimistic) traite l'AVENIR : elle se declenche
  //   quand on annule un compromis. Elle ne repassera jamais sur ces 661, dont le
  //   compromis a ete annule il y a parfois quinze ans.
  let dossiers;
  if (SOURCE === "cascade") {
    const lignes = [];
    let apres = 0;
    for (;;) {
      const page = await rest("app_affaire_ledger?select=app_affaire_id,app_chaine_id,kind,state,"
        + "hektor_annonce_id,hektor_affaire_id,present_in_hektor,transaction_origine"
        + "&app_chaine_id=not.is.null"
        + `&app_affaire_id=gt.${apres}&order=app_affaire_id.asc&limit=1000`);
      if (!page.length) break;
      lignes.push(...page);
      apres = page[page.length - 1].app_affaire_id;
    }
    // ⭐ La selection est dans selectionCascade() (plus haut), avec la garde de l'origine.
    dossiers = selectionCascade(lignes);
    console.log(`source             : CASCADE (coherence du dossier, pas de CSV)`);
  } else {
    const table = lireTable(CHEMIN_TABLE);
    dossiers = table
      .filter((r) => (r.proposition || "").startsWith("REFUSER"))
      .map((r) => ({ dossier: Number(r.dossier), bien: r.bien, source: r.source }));
    console.log(`source             : table de controle -- ${path.basename(CHEMIN_TABLE)}`);
  }
  if (CIBLES.length) {
    dossiers = dossiers.filter((d) => CIBLES.includes(String(d.dossier)));
    console.log(`cibles demandees a la main : ${CIBLES.join(", ")}`);
  }
  console.log(`dossiers a traiter : ${dossiers.length}`);
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

  // ── 2 bis. ⛔⛔ LES VENTES DES BIENS -- la garde ⑤ (23/11) ──────────────────────
  //   Par le NUMERO DU BIEN, pas par la chaine. TOUTES les ventes : supprimees chez
  //   Hektor comprises, reprises du classeur comprises (voir l'en-tete).
  const biens = new Set([TEMOIN_VENTE.bien]);
  for (const d of dossiers) if (String(d.bien || "").trim()) biens.add(String(d.bien).trim());
  for (const t of transactions) if (String(t.hektor_annonce_id || "").trim()) biens.add(String(t.hektor_annonce_id).trim());
  const listeBiens = [...biens];
  const ventesParBien = new Map();
  for (let i = 0; i < listeBiens.length; i += 200) {
    const tranche = listeBiens.slice(i, i + 200);
    const page = await rest("app_affaire_ledger?select=app_affaire_id,app_chaine_id,hektor_annonce_id,"
      + "hektor_affaire_id,present_in_hektor,transaction_origine"
      + "&kind=eq.vente&hektor_annonce_id=in.(" + tranche.join(",") + ")");
    for (const v of page) {
      const b = String(v.hektor_annonce_id || "").trim();
      if (!ventesParBien.has(b)) ventesParBien.set(b, []);
      ventesParBien.get(b).push(v);
    }
  }
  // ⛔ LE TEMOIN POSITIF : une lecture ratee ne vaut jamais « aucune vente ».
  if (!ventesDuBien(ventesParBien, TEMOIN_VENTE.bien).some((v) => Number(v.app_affaire_id) === TEMOIN_VENTE.vente)) {
    console.log(`⛔ garde ⑤ : la vente temoin ${TEMOIN_VENTE.vente} du bien ${TEMOIN_VENTE.bien} n'est pas lue --`
      + " la lecture des ventes est ratee, ON N'ENFILE RIEN (code 2).");
    return 2;
  }
  let nVentes = 0;
  for (const vs of ventesParBien.values()) nVentes += vs.length;
  console.log(`garde ⑤ du bien    : ${listeBiens.length} bien(s) regarde(s), ${ventesParBien.size} portent`
    + ` ${nVentes} vente(s) (temoin ${TEMOIN_VENTE.vente} lu)`);

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
  //   Il vit dans trier() (plus haut), qui sert aux DEUX modes, avec la garde ⑤.
  const { aPoser, ecartes } = trier(dossiers, parDossier, dejaEnCours, ventesParBien,
    { source: SOURCE, cheminTable: CHEMIN_TABLE });

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

// ⭐ 23/11 : les fonctions pures s'exportent, pour que le temoin de la garde ⑤ rejoue
//   LE VRAI CODE sur l'etat du 11/11 (Console/test_garde_du_bien_refus_offres.js).
//   Appele directement, le script fait exactement ce qu'il faisait.
module.exports = { vivante, ventesDuBien, selectionCascade, trier, lireTable, TABLE_DEFAUT,
  TEMOIN_VENTE, DOSSIERS_EXCLUS };

if (require.main === module) {
  main().then((code) => process.exit(code)).catch((e) => {
    console.error("PANNE :", e && e.message ? e.message : e);
    process.exit(1);
  });
}
