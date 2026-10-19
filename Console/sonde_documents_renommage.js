// SONDE EN LECTURE SEULE -- HEKTOR SAIT-IL RENOMMER UN DOCUMENT ?
//                                                      19/10/2026, chantier ⑦-9
//
// POURQUOI. Le point ⑦-9 (« renommer un document ») vient de l'audit du 08/10, qui
// l'avait repere en TROIS MOTS -- « C2 | 🟠 | ⑦ (renommer) » -- avec sa colonne
// « preuve » VIDE. Il n'a donc jamais ete audite.
//
// LE BESOIN EST REEL, mesure le 19/10 : sur 189 809 documents, 187 610 (99 %)
// portent un nom DE FICHIER, c'est-a-dire illisible --
//     _194401863817793382_1_.jpg   ·   _20480087_diagnostic_technique.pdf
// Seuls 2 199 ont une vraie etiquette.
//
// ⛔ ET LA COMMANDE EST INTROUVABLE DANS MES CAPTURES. J'ai cherche la ou ca a
//   marche deux fois cette semaine (delete_img le 14/10, vignette_visibilite
//   aujourd'hui) :
//     · le JS de la page Documents (104 Ko, capture du 13/05) : il porte
//       `deleteUploadedDocument(` mais AUCUN renommage ;
//     · labs_Header.js (12/06) : `editDocAnnonce` est le MOTEUR DE GENERATION ;
//     · les ~60 modes « doc » des captures : `UploadedDocument_list`, `_delete`,
//       `_uploadForm` -- et AUCUN `_rename` ni `_update`.
//   Les faux amis, verifies un par un : `editDocSave` edite un MODELE ;
//   `documents-updateDocDD` RATTACHE un document a un mandat (aucun champ de nom) ;
//   `getNameOrRenameBloc` renomme un BLOC dans un modele.
//
// ⭐ ET LE PRECEDENT EST PARLANT : pour les photos, notre extracteur releve
//   `can_edit_legend` (Hektor a `legendVignette(`). Pour les documents, RIEN
//   d'equivalent n'a ete capture.
//
// ⚠⚠ MAIS MES CAPTURES SONT DU JAVASCRIPT, PAS LA PAGE RENDUE -- et les boutons
//   d'une ligne de document vivent dans le HTML. C'est precisement ce trou que
//   cette sonde comble. Elle peut tres bien CONCLURE QUE CA N'EXISTE PAS : ce
//   serait une reponse, pas un echec.
//
// CE QU'ELLE NE FAIT PAS -- et c'est tout son contrat :
//   · pas de connexion : elle REUTILISE la session du worker et NE LA REECRIT PAS ;
//   · pas de clic, pas de POST, aucune ecriture : 2 a 3 LECTURES, pas plus ;
//   · arret NET au premier 403/401/429/503, ou si Hektor rend la page de
//     connexion -- jamais de nouvel essai (regle du projet : les ~1 300 refus
//     repetes ont fait bannir notre IP le 20/08) ;
//   · ⚠ ce n'est PAS le worker (memoire : ne jamais lancer le worker pour
//     l'inspecter).
//
//   node Console/sonde_documents_renommage.js            <- sur le bac a sable 62774
//   node Console/sonde_documents_renommage.js 24113      <- l'annonce dont j'ai la capture de mai

const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
const { chromium } = require("playwright");

const BASE = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN = (process.env.HEKTOR_ADMIN_URL || BASE + "/admin").replace(/\/+$/, "");
const SESSION = process.env.CONSOLE_DETECT_STORAGE_STATE_PATH
  || path.resolve(__dirname, "sessions", "storage_state_documents.json");

const ANNONCE = String(process.argv[2] || "62774").trim();

// Les mots qui trahiraient un renommage. ⚠ On cherche LARGE : si Hektor appelle
// ca « libelle », « titre » ou « label », on veut le voir aussi.
const MOTS = ["rename", "renom", "updatename", "editname", "setname", "changename",
              "libelle", "nomdoc", "docname", "document_name", "titre", "label",
              "editlibelle", "savename", "updatedoc", "editdoc", "modifdoc",
              // ajoutes au 2e passage du 19/10 : les derniers candidats a ecarter
              "updateaction", "listuploaded", "uploadeddocument"];

function corpsDeLaFonction(js, nom) {
  const i = js.search(new RegExp(`function\\s+${nom}\\s*\\(`));
  if (i < 0) return null;
  const debut = js.indexOf("{", i);
  let profondeur = 0;
  for (let k = debut; k < js.length; k += 1) {
    if (js[k] === "{") profondeur += 1;
    else if (js[k] === "}") { profondeur -= 1; if (profondeur === 0) return js.slice(i, k + 1); }
  }
  return js.slice(i, i + 1500);
}

function refus(statut) { return [401, 403, 429, 503].includes(statut); }

(async () => {
  const navigateur = await chromium.launch({ headless: true });
  let appels = 0;
  try {
    const contexte = await navigateur.newContext({ storageState: SESSION });

    async function lire(url, quoi) {
      appels += 1;
      const r = await contexte.request.get(url, { maxRedirects: 0 });
      const s = r.status();
      console.log(`  [${appels}] ${quoi} -> ${s}`);
      if (refus(s)) { throw new Error(`ARRET NET : Hektor rend ${s} -- on ne rejoue jamais`); }
      if (s >= 300 && s < 400) {
        throw new Error(`ARRET : redirection vers ${r.headers().location || "?"} -- la session a expire, rien n'est tente`);
      }
      if (!r.ok()) throw new Error(`Hektor ${s} sur ${quoi}`);
      const t = await r.text();
      if (/type=["']password["']/i.test(t.slice(0, 20000))) {
        throw new Error("ARRET : Hektor rend la page de CONNEXION -- la session a expire");
      }
      return t;
    }

    console.log(`SONDE RENOMMAGE DOCUMENT -- annonce ${ANNONCE}`);
    console.log("lecture seule, aucune ecriture, arret net au premier refus\n");

    // ① LA PAGE DES DOCUMENTS, RENDUE. C'est le trou que mes captures laissaient.
    const page = await lire(
      `${ADMIN}/xmlrpc.php?mode=chargeannonce_Documents&idann=${encodeURIComponent(ANNONCE)}`,
      "la page Documents (HTML rendu)",
    );
    console.log(`      taille : ${page.length} caracteres`);

    // ② LE JAVASCRIPT VIVANT. Ma capture a CINQ MOIS : une capture n'est pas une mesure.
    const js = await lire(`${ADMIN}/xmlrpc.1.2.js.php`, "le JavaScript vivant");
    console.log(`      taille : ${js.length} caracteres`);

    // ── CE QUE LA PAGE OFFRE PAR DOCUMENT ────────────────────────────────────
    console.log("\n===== LES APPELS DE FONCTION DANS LA PAGE (ce que les boutons font) =====");
    const appelsPage = new Map();
    for (const m of page.matchAll(/\b([a-zA-Z_][a-zA-Z0-9_]{3,})\s*\(/g)) {
      const n = m[1];
      if (["function", "if", "for", "while", "switch", "catch", "return", "typeof"].includes(n)) continue;
      appelsPage.set(n, (appelsPage.get(n) || 0) + 1);
    }
    const tries = [...appelsPage.entries()].sort((a, b) => b[1] - a[1]).slice(0, 30);
    for (const [n, c] of tries) console.log(`   ${String(c).padStart(4)}x  ${n}`);

    // ── LES CHAMPS DE SAISIE : y a-t-il un champ de NOM ? ────────────────────
    console.log("\n===== LES CHAMPS DE SAISIE DE LA PAGE =====");
    const champs = [...page.matchAll(/<(input|textarea)\b[^>]*>/gi)].map((m) => m[0]);
    if (!champs.length) console.log("   (aucun) -- donc aucun champ de nom a l'ecran");
    else for (const c of champs.slice(0, 25)) console.log("   " + c.replace(/\s+/g, " ").slice(0, 150));

    // ── LA RECHERCHE LARGE, DANS LES DEUX SOURCES ────────────────────────────
    console.log("\n===== LES MOTS QUI TRAHIRAIENT UN RENOMMAGE =====");
    let trouve = 0;
    for (const mot of MOTS) {
      const dansPage = (page.toLowerCase().match(new RegExp(mot, "g")) || []).length;
      const dansJs = (js.toLowerCase().match(new RegExp(mot, "g")) || []).length;
      if (dansPage || dansJs) {
        trouve += 1;
        console.log(`   ⭐ « ${mot} » : ${dansPage}x dans la page, ${dansJs}x dans le JS`);
      }
    }
    if (!trouve) console.log("   ⛔ AUCUN de ces mots, nulle part. Hektor ne propose pas de renommer.");

    // ── LES MODES QUE LA PAGE ET LE JS CONNAISSENT, filtres sur « doc » ──────
    console.log("\n===== LES MODES « doc » DU JAVASCRIPT VIVANT =====");
    const modes = new Set();
    for (const src of [page, js]) {
      for (const m of src.matchAll(/mode\s*[:=]\s*['"]([^'"]*[Dd]oc[^'"]*)['"]/g)) modes.add(m[1]);
      for (const m of src.matchAll(/mode=([a-zA-Z0-9_-]*[Dd]oc[a-zA-Z0-9_-]*)/g)) modes.add(m[1]);
    }
    const suspects = [];
    for (const m of [...modes].sort()) {
      const suspect = MOTS.some((w) => m.toLowerCase().includes(w));
      if (suspect) suspects.push(m);
      console.log(`   ${suspect ? "⭐" : "  "} ${m}`);
    }

    // ⭐⭐ LE CONTEXTE DES MODES SUSPECTS -- ajoute apres le 1er passage du 19/10,
    //   qui a trouve `updatedocument` SANS pouvoir dire ce qu'il envoie. Un nom de
    //   mode ne prouve rien : c'est sa CHARGE qui dit s'il renomme.
    for (const m of suspects) {
      console.log(`\n===== LE CONTEXTE DE « ${m} » (ce qu'il ENVOIE) =====`);
      let vu = 0;
      for (const src of [page, js]) {
        const re = new RegExp(`mode\\s*[:=]\\s*['"]${m}['"]|mode=${m}\\b`, "g");
        let occ;
        while ((occ = re.exec(src)) && vu < 3) {
          vu += 1;
          const a = Math.max(0, occ.index - 700);
          const b = Math.min(src.length, occ.index + 700);
          console.log(`--- occurrence ${vu} ---`);
          console.log(src.slice(a, b));
        }
      }
      if (!vu) console.log("   (le mode est nomme mais son appel n'est pas dans ces deux sources)");
    }

    // ── LES FONCTIONS SUSPECTES, EN ENTIER ───────────────────────────────────
    console.log("\n===== LES FONCTIONS SUSPECTES, LEUR CORPS =====");
    const noms = new Set();
    for (const m of js.matchAll(/function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g)) {
      const n = m[1];
      if (MOTS.some((w) => n.toLowerCase().includes(w))) noms.add(n);
    }
    if (!noms.size) console.log("   (aucune fonction dont le nom evoque un renommage)");
    for (const n of [...noms].slice(0, 6)) {
      console.log(`\n--- ${n} ---`);
      console.log((corpsDeLaFonction(js, n) || "(corps introuvable)").slice(0, 1200));
    }

    console.log(`\n✅ ${appels} lectures, aucun refus de Hektor. RIEN N'A ETE ECRIT.`);
  } catch (e) {
    console.error(`\n⛔ ${e.message}`);
    console.error(`   (${appels} lecture(s) faite(s) -- rien n'a ete ecrit)`);
    process.exitCode = 1;
  } finally {
    await navigateur.close();   // aucun storageState() : la session n'est PAS reecrite
  }
})();
