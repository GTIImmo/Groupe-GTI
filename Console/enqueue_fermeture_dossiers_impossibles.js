#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════════
// FERMER LES DOSSIERS « EN COURS » IMPOSSIBLES                       12/11/2026
// ═══════════════════════════════════════════════════════════════════════════════
// LA DECISION EST DE FREDERIC, un dossier a la fois, sur le tableau
//   « Chainage a trancher » du 12/11 : https://claude.ai/artifact/QCFjAzB1tNxpt34ojwhKGR
// Il a repondu « fermer » sur 22 dossiers, « laisser » sur 2 (14137 et 3699),
// et « fusionner » sur les autres -- ces fusions sont deja faites, par la regle D
// du chainage et par phase2/sync/rattachements_manuels.csv.
//
// CE QUE SONT CES 22 DOSSIERS. Des compromis « actifs » depuis 2006, 2008, 2011,
//   et des offres sans date ni etat, sur des biens CLOS ou VENDUS et archives.
//   L'affaire n'a pas abouti et personne n'a ferme la fiche chez Hektor.
//   Deux d'entre eux sont confirmes par le classeur, qui les dit ANNULEES
//   (27033 et 28155).
//
// ⛔⛔ EN BLANC PAR DEFAUT. Sans --envoyer, ce script COMPTE et n'ecrit RIEN.
//
//   node Console/enqueue_fermeture_dossiers_impossibles.js                 <- en blanc
//   node Console/enqueue_fermeture_dossiers_impossibles.js --dossiers 395  <- l'essai
//   node Console/enqueue_fermeture_dossiers_impossibles.js --envoyer
//
// ⭐ L'ORDRE COMPTE, ET IL EST IMPOSE ICI : les COMPROMIS d'abord (priorite 55),
//   les OFFRES ensuite (priorite 60). Un compromis annule avant l'offre laisse la
//   fiche Hektor dans un etat lisible ; l'inverse donne une offre refusee sous un
//   compromis encore actif, ce que personne ne saurait relire.
//
// ⚠ LA CASCADE DE SUPABASE NE JOUE PAS ICI, et c'est pourquoi les deux gestes sont
//   poses. Elle vit dans la RPC app_geste_affaire_optimistic ; ce script pose les
//   travaux DIRECTEMENT dans app_console_job, comme les six autres scripts du
//   projet. Rien ne refusera l'offre a notre place.
//
// ⚠ LES BIENS SONT PRESQUE TOUS ARCHIVES, et c'est deja eprouve : la base autorise
//   le geste d'ETAT sur une archive (app_console_can_access_dossier ne regarde
//   jamais l'archivage) ; le verrou est a l'ECRAN. Mesure du 10/11, et les 1 185
//   refus du 11/11 l'ont confirme en reel. ⛔ Ce qui reste interdit, c'est CREER
//   une transaction ou changer le STATUT d'une archive.
//
// Codes de sortie : 0 pose ou rien a faire · 1 panne · 3 file occupee · 4 trop d'erreurs
// ═══════════════════════════════════════════════════════════════════════════════

const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

const SOURCE_DE_LA_DECISION = "Frederic -- tableau « Chainage a trancher » du 12/11/2026";

// ═══════════════════════════════════════════════════════════════════════════════
// LES 22 DOSSIERS, ET POURQUOI CHACUN -- la trace doit survivre a la conversation
// ═══════════════════════════════════════════════════════════════════════════════
const DOSSIERS = new Map([
  // le bien s'est vendu, mais A QUELQU'UN D'AUTRE
  [23139, "bien 46032 ZARLI -- vendu dans le dossier 23137, a un autre acquereur"],
  [18985, "bien 39360 -- deux ventes sur le bien, aucune a cet acquereur (qui n'est meme pas renseigne)"],
  [21037, "bien 42578 LARDREAU-GIRE -- vendu dans le dossier 21036. ⚠ montant 650 EUR : une location ?"],
  // aucune vente, et le bien est CLOS ou archive
  [27033, "bien 53015 VULIN ET LAGRANGE -- LE CLASSEUR DIT ANNULEE, et le compromis n'a pas de date"],
  [28155, "bien 54726 LESAULT -- LE CLASSEUR DIT ANNULEE, compromis sans date"],
  [10802, "bien 22904 CREPET -- bien clos et archive, aucune vente, offre sans date ni etat"],
  [10810, "bien 22918 KADI -- idem"],
  [10816, "bien 22922 VALLAT -- idem"],
  [19050, "bien 39684 POULY et CHARTOIRE -- offre encore « proposee » sur un bien clos et archive"],
  [28724, "bien 59467 JUGE -- offre a 270 000 EUR encore « proposee », sans aucune date"],
  [25539, "bien 49306 PERINO CHINCHIN -- compromis « actif » depuis vingt ans, bien clos"],
  [13590, "bien 27849 CASTELLANO -- offre acceptee de 2008, jamais suivie d'un compromis"],
  [13555, "bien 27822 BARROT -- offre acceptee de 2008, bien clos et archive"],
  [10749, "bien 22866 MME CASTIAUX -- compromis « actif » depuis 2009"],
  [13387, "bien 27570 BASTIE GRIMAL -- offre acceptee de 2009, bien clos"],
  [10711, "bien 22816 -- l'offre reste vivante alors que son compromis est annule"],
  [18663, "bien 39092 CHARRE -- compromis « actif » depuis 2011, bien clos"],
  [395,   "bien 1195 CONSTANTINOU -- compromis « actif » depuis 2011, bien clos"],
  [1609,  "bien 4469 DALMASSO -- compromis « actif » depuis 2011, bien clos"],
  [21817, "bien 43476 -- montant 510 EUR et aucun acquereur : une location, ou une fiche d'essai"],
  [2993,  "bien 7494 MAURIN -- compromis « actif » depuis 2014, bien clos"],
  [14669, "bien 29955 DEFOUR -- compromis « actif » depuis 2016, bien clos"],
]);

// ⛔ CE QU'IL A DIT DE LAISSER -- et la raison, pour que personne ne le rouvre
const LAISSES = new Map([
  [14137, "bien 28668 LEJEUNE -- le classeur dit « Vente reglee » et AUCUNE vente n'existe, "
        + "ni chez nous ni chez Hektor. C'est une vente manquante, pas un dossier a fermer. "
        + "Et creer une vente sur une archive est refuse par decision."],
  [3699,  "bien 8494 MACHABERT -- le garage VS046 : sa vente a ete SUPPRIMEE chez Hektor. "
        + "Deja exclu des gestes par decision le 11/11."],
]);

const ETATS_OFFRE_MORTS = new Set(["refused", "refusee"]);
const ETATS_COMPROMIS_MORTS = new Set(["cancelled", "annule"]);

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
  return i >= 0 ? process.argv[i + 1] : null;
}

async function main() {
  if (!SUPABASE_URL || !KEY) {
    console.error("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis");
    return 1;
  }
  const envoyer = process.argv.includes("--envoyer");
  const choisis = (arg("--dossiers") || "").split(",").map((x) => x.trim()).filter(Boolean)
    .map(Number);
  const cibles = choisis.length ? choisis.filter((c) => DOSSIERS.has(c)) : [...DOSSIERS.keys()];
  if (choisis.length && cibles.length !== choisis.length) {
    console.error(`⛔ REFUS : ${choisis.filter((c) => !DOSSIERS.has(c)).join(", ")} `
      + `ne fait pas partie des 22 dossiers decides. On ne ferme pas un dossier `
      + `qui n'a pas ete tranche.`);
    return 1;
  }

  console.log(`la decision : ${SOURCE_DE_LA_DECISION}`);
  console.log(`22 dossiers « fermer » . 2 laisses expres : ${[...LAISSES.keys()].join(", ")}`);
  console.log(`cibles de ce passage : ${cibles.length} dossier(s)`);
  console.log();

  // ─── LES GARDES, AVANT TOUT ────────────────────────────────────────────────
  for (const type of ["cancel_hektor_compromis", "change_hektor_offre_status"]) {
    const enCours = await rest(`app_console_job?select=id&job_type=eq.${type}`
      + "&status=in.(pending,running)&limit=50");
    if (enCours.length >= 20) {
      console.error(`⛔ REFUS : ${enCours.length} travaux ${type} sont deja en file. `
        + `On n'empile pas.`);
      return 3;
    }
    const depuis = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
    const rates = await rest(`app_console_job?select=id&job_type=eq.${type}`
      + `&status=eq.error&created_at=gte.${depuis}&limit=20`);
    if (rates.length >= 10) {
      console.error(`⛔ REFUS : ${rates.length} echecs ${type} en 24 h. `
        + `Hektor nous rejette peut-etre -- ne RIEN rejouer.`);
      return 4;
    }
  }

  // ─── CE QUI EST ENCORE VIVANT DANS CES DOSSIERS ────────────────────────────
  const lignes = await rest("app_affaire_ledger?select=app_affaire_id,app_chaine_id,kind,state,"
    + "hektor_annonce_id,hektor_affaire_id,present_in_hektor,montant,date"
    + `&app_chaine_id=in.(${cibles.join(",")})&order=app_chaine_id.asc,kind.asc`);

  const aPoser = [];
  const ecartes = [];
  for (const l of lignes) {
    const vivante = l.present_in_hektor !== false && String(l.hektor_affaire_id || "").trim();
    if (!vivante) { ecartes.push([l.app_affaire_id, "absente de chez Hektor"]); continue; }
    const etat = String(l.state || "").toLowerCase();
    const annonce = String(l.hektor_annonce_id || "").trim();
    if (!annonce) { ecartes.push([l.app_affaire_id, "pas de numero d'annonce"]); continue; }
    const pourquoi = DOSSIERS.get(l.app_chaine_id) || "";

    if (l.kind === "compromis") {
      if (ETATS_COMPROMIS_MORTS.has(etat)) {
        ecartes.push([l.app_affaire_id, "compromis deja annule"]); continue;
      }
      aPoser.push({
        job_type: "cancel_hektor_compromis",
        hektor_annonce_id: annonce,
        status: "pending",
        // les compromis AVANT les offres : priorite plus haute (nombre plus petit)
        priority: 55,
        payload_json: {
          hektor_compromis_id: String(l.hektor_affaire_id),
          hektor_annonce_id: annonce,
          app_affaire_id: l.app_affaire_id,
          // ⛔ SANS LUI, restaurerEtatAffaire() ne peut rien remettre si Hektor refuse
          etat_avant: l.state,
          etat_apres: "cancelled",
          notes: "",
          sans_resynchro: true,
          origine: "enqueue_fermeture_dossiers_impossibles",
          decide_par: SOURCE_DE_LA_DECISION,
          raison: pourquoi,
        },
      });
    } else if (l.kind === "offre") {
      if (ETATS_OFFRE_MORTS.has(etat)) {
        ecartes.push([l.app_affaire_id, "offre deja refusee"]); continue;
      }
      aPoser.push({
        job_type: "change_hektor_offre_status",
        hektor_annonce_id: annonce,
        status: "pending",
        priority: 60,
        payload_json: {
          // ⚠ LA CLE EST `type`, PAS `geste` -- le handler jette le travail sinon
          type: "refus",
          hektor_offre_id: String(l.hektor_affaire_id),
          hektor_annonce_id: annonce,
          app_affaire_id: l.app_affaire_id,
          etat_avant: l.state,
          etat_apres: "refused",
          sans_resynchro: true,
          origine: "enqueue_fermeture_dossiers_impossibles",
          decide_par: SOURCE_DE_LA_DECISION,
          raison: pourquoi,
        },
      });
    } else {
      ecartes.push([l.app_affaire_id, `genre ${l.kind} -- aucun geste prevu`]);
    }
  }

  aPoser.sort((a, b) => a.priority - b.priority
    || Number(a.payload_json.app_affaire_id) - Number(b.payload_json.app_affaire_id));

  const compromis = aPoser.filter((j) => j.job_type === "cancel_hektor_compromis");
  const offres = aPoser.filter((j) => j.job_type === "change_hektor_offre_status");
  console.log(`A POSER : ${aPoser.length} geste(s)`);
  console.log(`   ${compromis.length} annulation(s) de compromis   (priorite 55, d'abord)`);
  console.log(`   ${offres.length} refus d'offre                 (priorite 60, ensuite)`);
  console.log();
  for (const j of aPoser) {
    const p = j.payload_json;
    console.log(`   ${j.job_type === "cancel_hektor_compromis" ? "ANNULER  " : "REFUSER  "}`
      + `affaire ${String(p.app_affaire_id).padEnd(8)} annonce ${String(j.hektor_annonce_id).padEnd(7)} `
      + `Hektor ${String(p.hektor_compromis_id || p.hektor_offre_id).padEnd(7)} `
      + `etat ${String(p.etat_avant || "(vide)").padEnd(10)} -> ${p.etat_apres}`);
  }
  if (ecartes.length) {
    console.log();
    console.log(`ECARTEES : ${ecartes.length}`);
    for (const [id, raison] of ecartes) console.log(`   affaire ${id} : ${raison}`);
  }
  console.log();

  if (!envoyer) {
    console.log("EN BLANC : rien n'a ete ecrit. Ajouter --envoyer pour poser ces travaux.");
    return 0;
  }

  let poses = 0;
  const rates = [];
  for (const job of aPoser) {
    try {
      await rest("app_console_job", {
        method: "POST",
        body: JSON.stringify({ ...job, payload_json: job.payload_json }),
      });
      poses += 1;
    } catch (erreur) {
      rates.push([job.payload_json.app_affaire_id, String(erreur.message).slice(0, 160)]);
      if (rates.length >= 5) { console.error("⛔ ARRET : 5 echecs."); break; }
    }
  }
  console.log(`poses : ${poses} / ${aPoser.length}`);
  if (rates.length) {
    console.log(`echecs : ${rates.length}`);
    for (const [id, message] of rates) console.log(`   ${id} : ${message}`);
    return 1;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // ET MAINTENANT L'ETAT CHEZ NOUS -- SANS CETTE PASSE, PERSONNE NE LE POSE
  // ═══════════════════════════════════════════════════════════════════════════
  // ⛔⛔ DEFAUT DE MA PREMIERE VERSION, ATTRAPE A L'ESSAI DU 12/11 sur le dossier
  //   395 : les deux travaux sont revenus `done`, Hektor avait bien annule le
  //   compromis et refuse l'offre -- et notre registre portait toujours `active`
  //   et `accepted`. `registre_lignes: 1` dans la reponse du worker ne veut PAS
  //   dire « l'etat est pose ».
  //
  // POURQUOI. Le handler du worker ne pose JAMAIS l'etat. Son contrat, ecrit dans
  // son propre commentaire : « L'etat est DEJA pose dans l'app (instantane). Si
  // Hektor refuse, on le remet. » C'est la RPC app_geste_affaire_optimistic qui le
  // pose, dans la meme transaction que le travail. En postant directement dans
  // app_console_job, on RETIRE ce maillon -- donc personne ne pose l'etat, et il
  // n'y a rien a restaurer non plus.
  // ⚠ LA LECON ETAIT DEJA ECRITE, dans enqueue_refus_offres_mortes_lot.js, par moi,
  //   le 10/11. Je l'ai refaite a l'identique. Avant d'ecrire un script qui pose des
  //   travaux, LIRE celui d'a cote.
  //
  // ⚠ L'ORDRE EST DELIBERE : le travail D'ABORD, l'etat ENSUITE. Un script REST ne
  //   peut pas etre transactionnel sur deux appels. Si l'etat echoue apres coup, le
  //   geste part quand meme chez Hektor et notre registre reste en retard d'une
  //   nuit -- le run le corrigera. L'inverse (etat d'abord) laisserait un registre
  //   qui MENT si le travail ne partait pas, et sans travail, rien ne le restaure.
  // ⚠ ON NE TOUCHE QUE `state`. Ni la date, ni le montant : le reste appartient a
  //   Hektor, et le run de nuit le relit.
  let etatsPoses = 0;
  const etatsRates = [];
  for (const job of aPoser.slice(0, poses)) {
    const id = job.payload_json.app_affaire_id;
    if (id == null) continue;
    try {
      await rest(`app_affaire_ledger?app_affaire_id=eq.${encodeURIComponent(String(id))}`, {
        method: "PATCH",
        body: JSON.stringify({ state: job.payload_json.etat_apres }),
      });
      etatsPoses += 1;
    } catch (erreur) {
      // ⛔ ON NE DEFAIT PAS LE TRAVAIL POUR AUTANT, et on ne se tait pas.
      etatsRates.push([id, String(erreur.message).slice(0, 160)]);
    }
  }
  console.log(`etats poses chez nous : ${etatsPoses} / ${poses}`);
  if (etatsRates.length) {
    console.log(`etats NON poses : ${etatsRates.length} -- le geste part quand meme chez `
      + `Hektor, et le run de nuit corrigera notre registre.`);
    for (const [id, message] of etatsRates) console.log(`   ${id} : ${message}`);
  }
  console.log();
  console.log("⏰ A CONTROLER : app_console_job (status), puis l'etat des transactions.");
  console.log("   Les travaux portent sans_resynchro : le run de nuit relira les fiches.");
  return 0;
}

main().then((code) => process.exit(code)).catch((erreur) => {
  console.error("panne :", erreur);
  process.exit(1);
});
