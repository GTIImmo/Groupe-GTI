// SONDE EN LECTURE SEULE -- LA COMMANDE QUI SUPPRIME UNE PHOTO CHEZ HEKTOR
//                                                       14/10/2026, chantier ③ bloc 2
//
// POURQUOI. Le geste « supprimer une photo depuis l'app » n'existe pas : l'audit du 25/09
// (notice/AUDIT_PHOTOS_2026-09-25.md) disait « les commandes Hektor ne sont pas connues,
// c'est le vrai travail : les trouver d'abord ». Le 14/10, une capture du 13/05
// (Console/exports/inspect_announcement_delete_62200_.../report.json) a rendu le corps de
// `delete_img` :
//     GET xmlrpc.php?mode=delete_img&img=<fichier>&idann=<annonce>&table=<table>
// puis, si la table vaut 'ordre_img', saveOrder('liste_photos') et
// saveOrder('liste_photos_hidden'). Il reste DEUX inconnues, et cette sonde ne lit que ca :
//   ① delete_img a-t-il change depuis mai ?  (une capture de cinq mois n'est pas une mesure)
//   ② que fait saveOrder ?                    (jamais capture)
//
// ⚠ CE QU'ELLE NE FAIT PAS -- et c'est tout son contrat :
//   · pas de connexion : elle REUTILISE la session deja enregistree par le worker
//     (patron : Console/find_delete_ids.js) et NE LA REECRIT PAS ;
//   · pas de clic, pas de POST, pas d'appel a xmlrpc.php : UN SEUL GET, vers le fichier
//     JavaScript statique de la page Photos ;
//   · si la session a expire, elle le DIT et s'arrete -- elle ne tente aucune reconnexion.
//   ⚠ Ce n'est PAS le worker (memoire : ne jamais lancer le worker pour l'inspecter).
//
//   node Console/sonde_photos_suppression.js

const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
const { chromium } = require("playwright");

const BASE = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN = (process.env.HEKTOR_ADMIN_URL || BASE + "/admin").replace(/\/+$/, "");
const SESSION = path.resolve(__dirname, "sessions", "storage_state_documents.json");

function corpsDeLaFonction(js, nom) {
  const i = js.search(new RegExp(`function\\s+${nom}\\s*\\(`));
  if (i < 0) return null;
  // On suit les accolades depuis la premiere ouvrante : suffisant pour du JS de 2010.
  const debut = js.indexOf("{", i);
  let profondeur = 0;
  for (let k = debut; k < js.length; k += 1) {
    if (js[k] === "{") profondeur += 1;
    else if (js[k] === "}") { profondeur -= 1; if (profondeur === 0) return js.slice(i, k + 1); }
  }
  return js.slice(i, i + 2000);
}

(async () => {
  const navigateur = await chromium.launch({ headless: true });
  try {
    const contexte = await navigateur.newContext({ storageState: SESSION });
    const url = `${ADMIN}/xmlrpc.1.2.js.php`;
    const reponse = await contexte.request.get(url, { maxRedirects: 0 });
    const statut = reponse.status();
    console.log(`GET ${url} -> ${statut}`);
    if (statut === 403) { console.log("⛔ 403 : on s'arrete (regle du projet)."); process.exitCode = 3; return; }
    if (statut >= 300 && statut < 400) {
      console.log(`⛔ redirection vers ${reponse.headers().location || "?"} : la session a expire. Rien n'est tente.`);
      process.exitCode = 2;
      return;
    }
    const js = await reponse.text();
    console.log(`taille : ${js.length} caracteres`);
    if (!/function\s+\w+\s*\(/.test(js)) {
      console.log("⛔ la reponse n'est pas du JavaScript -- probablement une page de connexion. Arret.");
      process.exitCode = 2;
      return;
    }
    for (const nom of ["delete_img", "saveOrder", "saveOrderProgrammeNeuf"]) {
      const corps = corpsDeLaFonction(js, nom);
      console.log(`\n===== ${nom} =====`);
      console.log(corps || "(absente de ce fichier)");
    }
  } finally {
    await navigateur.close();   // aucun storageState() : la session n'est PAS reecrite
  }
})().catch((e) => { console.error(`ECHEC : ${e.message}`); process.exit(1); });
