// SONDE EN LECTURE SEULE -- LA COMMANDE QUI ARCHIVE / DESARCHIVE UNE FICHE CONTACT
//                                                       15/10/2026, chantier ⑦ point ⑦-1
//
// POURQUOI. La note du 14/10 disait « la commande Hektor pour archiver une FICHE est
// INCONNUE ». C'etait faux : elle dort dans DEUX captures de juin, qui concordent.
//   · Console/exports/impersonate_create_annonce_2026-06-01.../labs_contactsRefonte.js:436
//       POST xmlrpc.php   mode=contacts-contactProfile-archiveContact
//                         & id=<idContact> & archive=<true|false>
//     enveloppee dans setArchiveContact(archive, callback) -- UN SEUL ordre pour les
//     deux sens, c'est le parametre `archive` qui decide.
//   · Console/exports/probe_search_listing_603882_2026-06-12.../fiche.html
//       le bouton est un INTERRUPTEUR (.switchButtonState, rel on/off), et sa fonction
//       de rappel ne fait QUE de l'animation.
//
// CE QUE CETTE SONDE REPOND, et rien de plus :
//   ① la commande a-t-elle change depuis le 1er juin ?  (une capture de 4 mois et demi
//      n'est pas une mesure -- meme question que pour delete_img le 14/10)
//   ② le fichier d'aujourd'hui fait-il autre chose en archivant (les criteres) ?
//
// ⚠ CE QU'ELLE NE PEUT PAS DIRE : ce que le SERVEUR de Hektor fait de son cote
//   (archive-t-il les criteres du contact en meme temps ?). Aucune lecture ne peut le
//   savoir -- seul un essai sur une fiche d'essai le dira, et il demande un accord.
//
// ⚠ CE QU'ELLE NE FAIT PAS -- et c'est tout son contrat :
//   · pas de connexion : elle REUTILISE la session deja enregistree par le worker et
//     NE LA REECRIT PAS (aucun appel a storageState()) ;
//   · pas de clic, pas de POST, aucun appel a xmlrpc.php : UN SEUL GET, vers le fichier
//     JavaScript statique de la page Contacts ;
//   · elle ne touche AUCUNE fiche : l'adresse ne porte aucun numero de contact ;
//   · si la session a expire, elle le DIT et s'arrete -- aucune reconnexion.
//   ⚠ Ce n'est PAS le worker (memoire : ne jamais lancer le worker pour l'inspecter).
//
//   node Console/sonde_archive_contact.js

const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
const { chromium } = require("playwright");

const BASE = (process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr").replace(/\/+$/, "");
const ADMIN = (process.env.HEKTOR_ADMIN_URL || BASE + "/admin").replace(/\/+$/, "");
const SESSION = path.resolve(__dirname, "sessions", "storage_state_documents.json");
const CAPTURE_JUIN = path.resolve(
  __dirname, "exports", "impersonate_create_annonce_2026-06-01T09-42-48-999Z",
  "labs_contactsRefonte.js");

// Le chemin exact est celui que la capture de juin a enregistre dans son report.json.
const CHEMIN_JS = "labs/contacts/labs_contactsRefonte.js";

function corpsDeLaFonction(js, nom) {
  const i = js.search(new RegExp(`function\\s+${nom}\\s*\\(`));
  if (i < 0) return null;
  const debut = js.indexOf("{", i);
  let profondeur = 0;
  for (let k = debut; k < js.length; k += 1) {
    if (js[k] === "{") profondeur += 1;
    else if (js[k] === "}") { profondeur -= 1; if (profondeur === 0) return js.slice(i, k + 1); }
  }
  return js.slice(i, i + 2000);
}

// Fins de ligne : un fichier servi par Hektor et un fichier pose sur disque Windows
// peuvent differer par les seuls retours chariot. On compare TOUJOURS sans eux
// (memoire : « empreinte md5 faussee par les fins de ligne Windows », 3 fois paye).
const empreinte = (texte) =>
  crypto.createHash("md5").update(String(texte).replace(/\r/g, "")).digest("hex");

// Et une seconde empreinte, SANS LES ACCENTS. La capture de juin a ete ecrite par un
// outil qui a mal relu l'encodage (« Ãªtes-vous sÃ»r » au lieu de « êtes-vous sûr ») :
// sans ce second regard, un simple accent fait crier « la commande a change ».
const empreinteSansAccents = (texte) =>
  crypto.createHash("md5")
    .update(String(texte).replace(/\r/g, "").replace(/[^\x00-\x7F]/g, ""))
    .digest("hex");

(async () => {
  const navigateur = await chromium.launch({ headless: true });
  try {
    const contexte = await navigateur.newContext({ storageState: SESSION });
    const url = `${ADMIN}/?call=getJs&js=${CHEMIN_JS}&t=${Date.now()}`;
    const reponse = await contexte.request.get(url, { maxRedirects: 0 });
    const statut = reponse.status();
    console.log(`GET ${url}\n  -> ${statut}`);
    if (statut === 403) { console.log("⛔ 403 : on s'arrete (regle du projet)."); process.exitCode = 3; return; }
    if (statut >= 300 && statut < 400) {
      console.log(`⛔ redirection vers ${reponse.headers().location || "?"} : la session a expire. Rien n'est tente.`);
      process.exitCode = 2;
      return;
    }
    const js = await reponse.text();
    console.log(`  taille : ${js.length} caracteres`);
    if (!/function\s+\w+\s*\(/.test(js)) {
      console.log("⛔ la reponse n'est pas du JavaScript -- probablement une page de connexion. Arret.");
      process.exitCode = 2;
      return;
    }

    // ⓿ On GARDE le fichier lu, pour ne plus avoir a rappeler Hektor plus tard
    //   (c'est ce qui a manque pendant quatre mois : la commande etait dans une capture,
    //    personne ne savait qu'elle y etait).
    const dossier = path.resolve(__dirname, "exports", "sonde_archive_contact_" +
      new Date().toISOString().slice(0, 10));
    fs.mkdirSync(dossier, { recursive: true });
    const copie = path.join(dossier, "labs_contactsRefonte.js");
    fs.writeFileSync(copie, js, "utf8");
    console.log(`  copie gardee : ${path.relative(path.resolve(__dirname, ".."), copie)}`);

    // ① LA COMMANDE D'AUJOURD'HUI, mot pour mot.
    for (const nom of ["setArchiveContact", "deleteContact"]) {
      const corps = corpsDeLaFonction(js, nom);
      console.log(`\n===== ${nom} (aujourd'hui) =====`);
      console.log(corps || "(absente de ce fichier)");
    }

    // ② A-T-ELLE CHANGE DEPUIS JUIN ? On compare le corps, sans les retours chariot.
    console.log("\n===== comparaison avec la capture du 01/06 =====");
    if (!fs.existsSync(CAPTURE_JUIN)) {
      console.log("(capture de juin introuvable : comparaison impossible)");
    } else {
      const juin = fs.readFileSync(CAPTURE_JUIN, "utf8");
      for (const nom of ["setArchiveContact", "deleteContact"]) {
        const a = corpsDeLaFonction(juin, nom);
        const b = corpsDeLaFonction(js, nom);
        const ea = a ? empreinte(a) : "(absente)";
        const eb = b ? empreinte(b) : "(absente)";
        const sa = a ? empreinteSansAccents(a) : "(absente)";
        const sb = b ? empreinteSansAccents(b) : "(absente)";
        console.log(`${nom.padEnd(20)} brut        ${ea === eb ? "IDENTIQUE" : "⚠ DIFFERENT"}   (${ea} / ${eb})`);
        console.log(`${"".padEnd(20)} sans accents ${sa === sb ? "IDENTIQUE" : "⚠ DIFFERENT"}   (${sa} / ${sb})`);
      }
      console.log(`fichier entier       juin ${empreinte(juin)}   aujourd'hui ${empreinte(js)}`);
    }

    // ③ LE FICHIER D'AUJOURD'HUI TOUCHE-T-IL LES CRITERES EN ARCHIVANT LA FICHE ?
    const corpsArchive = corpsDeLaFonction(js, "setArchiveContact") || "";
    const indices = ["modifDateArchiveCritere", "archiveUnarchiveContactRecherche",
                     "utoarchivage", "Critere", "critere", "recherche"];
    console.log("\n===== la fiche entraine-t-elle les criteres ? (dans la page) =====");
    for (const mot of indices) {
      const dansLaFonction = corpsArchive.includes(mot);
      const dansLeFichier = js.includes(mot);
      console.log(`${mot.padEnd(34)} dans setArchiveContact : ${dansLaFonction ? "OUI ⚠" : "non"}   ailleurs dans le fichier : ${dansLeFichier ? "oui" : "non"}`);
    }
    console.log("\n⚠ RAPPEL : cette sonde ne lit que le NAVIGATEUR. Ce que le serveur de");
    console.log("   Hektor fait en recevant l'ordre reste inconnu jusqu'a un essai reel.");
  } finally {
    await navigateur.close();   // aucun storageState() : la session n'est PAS reecrite
  }
})().catch((e) => { console.error(`ECHEC : ${e.message}`); process.exit(1); });
