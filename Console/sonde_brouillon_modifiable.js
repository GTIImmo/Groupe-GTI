// SONDE EN LECTURE SEULE -- UN BROUILLON A-T-IL UN FORMULAIRE DE MODIFICATION ?
//                                                      20/10/2026, question de Frederic
//
// SA QUESTION : « peux-tu tester de modifier une fiche brouillon ? peut-etre que le
// probleme etait plutot la ? si la modification fonctionne on pourrait rendre cet
// index complet, mais c'est etonnant que nous ne l'ayons pas fait. »
//
// ⭐ ET IL A RAISON : CE TEST N'A JAMAIS ETE FAIT. La note du 22/06 a bien eprouve
//   `update_hektor_annonce_fields` -- mais sur l'annonce JETABLE 62556, et elle dit
//   elle-meme que notre creation fabrique une annonce `is_draft=false` depuis le
//   15/05. Donc la modification a ete prouvee sur une NON-brouillon, et la
//   conclusion « le worker de modif est sain » ne dit rien des brouillons.
//
// ⚠⚠ ET ON NE PEUT PAS FABRIQUER UN BROUILLON DE TEST : il nait d'un humain qui
//   abandonne le wizard. Toute cible est donc le travail de quelqu'un -- raison de
//   plus pour commencer en LECTURE.
//
// ⭐⭐ CE QUI REND LE TEST POSSIBLE SANS ECRIRE. Le worker charge le formulaire
//   AVANT de le renvoyer (`postHektorMefUpdate`, console_job_worker.js) :
//       ?mode=ihmChargeGroupe&idAnnonce=<id>&group=<groupe>&consultMode=editer&ajax=ajax
//   C'est un GET. Si Hektor sert ce formulaire pour un brouillon, la modification
//   est techniquement possible ; s'il ne le sert pas, un brouillon n'a pas de fiche
//   modifiable -- ce que les notes affirment sans l'avoir mesure.
//
// ⚠ LE TEMOIN INVERSE EST OBLIGATOIRE : on interroge AUSSI de vraies annonces. Sans
//   lui, une session expiree ou un mauvais parametre rendrait « rien » partout et
//   passerait pour « les brouillons ne sont pas modifiables ».
//
// CE QU'ELLE NE FAIT PAS :
//   · aucun POST, aucune ecriture, rien de modifie chez Hektor ;
//   · pas de connexion : elle REUTILISE la session du worker et NE LA REECRIT PAS ;
//   · arret NET au premier 401/403/429/503 ou si Hektor rend la page de connexion
//     (regle du projet : les refus repetes ont fait bannir notre IP le 20/08) ;
//   · 4 appels, annonces d'avance.
//
//   node Console/sonde_brouillon_modifiable.js

const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });
const { chromium } = require("playwright");

const BASE = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN = (process.env.HEKTOR_ADMIN_URL || BASE + "/admin").replace(/\/+$/, "");
const XMLRPC = ADMIN + "/xmlrpc.php";
const SESSION = process.env.CONSOLE_DETECT_STORAGE_STATE_PATH
  || path.resolve(__dirname, "sessions", "storage_state_documents.json");

// ⚠ LES CIBLES SONT CHOISIES, PAS PRISES AU HASARD -- et les deux familles sont la.
const CIBLES = [
  { id: "63314", quoi: "BROUILLON avec detail REST (status 2 = Actif)" },
  { id: "63275", quoi: "BROUILLON sans detail REST (status 1 = Estimation)" },
  { id: "62774", quoi: "VRAIE annonce (le bac a sable)        <- TEMOIN INVERSE" },
  { id: "63073", quoi: "VRAIE annonce (celle des 24 photos)   <- TEMOIN INVERSE" },
];

const GROUPE = "ag_interieur";   // le groupe que le worker ecrit en premier

function refus(s) { return [401, 403, 429, 503].includes(s); }

(async () => {
  const nav = await chromium.launch({ headless: true });
  let appels = 0;
  const resultats = [];
  try {
    const ctx = await nav.newContext({ storageState: SESSION });

    async function lireFormulaire(id) {
      appels += 1;
      const url = `${XMLRPC}?mode=ihmChargeGroupe&idAnnonce=${encodeURIComponent(id)}`
                + `&group=${encodeURIComponent(GROUPE)}&consultMode=editer&ajax=ajax`;
      const r = await ctx.request.get(url, {
        headers: { Referer: `${ADMIN}?page=/mes-biens/mon-bien&id=${encodeURIComponent(id)}` },
        maxRedirects: 0,
      });
      const s = r.status();
      if (refus(s)) throw new Error(`ARRET NET : Hektor rend ${s} -- on ne rejoue jamais`);
      if (s >= 300 && s < 400) throw new Error(`ARRET : redirection -- la session a expire`);
      const t = r.ok() ? await r.text() : "";
      if (/type=["']password["']/i.test(t.slice(0, 20000))) {
        throw new Error("ARRET : Hektor rend la page de CONNEXION -- la session a expire");
      }
      return { statut: s, texte: t };
    }

    console.log("SONDE : UN BROUILLON A-T-IL UN FORMULAIRE DE MODIFICATION ?");
    console.log("lecture seule, 4 appels, aucune ecriture\n");

    for (const cible of CIBLES) {
      const { statut, texte } = await lireFormulaire(cible.id);
      // Ce que le worker cherche ensuite : des champs de saisie du groupe.
      const inputs = (texte.match(/<input\b[^>]*>/gi) || []).length;
      const selects = (texte.match(/<select\b[^>]*>/gi) || []).length;
      const textareas = (texte.match(/<textarea\b[^>]*>/gi) || []).length;
      // les noms de champs que le worker ecrit vraiment dans ag_interieur
      const attendus = ["surfappart", "nbpieces", "NB_CHAMBRES"];
      const presents = attendus.filter((n) => new RegExp(`name=["']${n}["']`, "i").test(texte));
      const verdict = (inputs + selects + textareas) > 0 && presents.length > 0
        ? "⭐ FORMULAIRE SERVI -- modifiable"
        : (texte.length < 200 ? "⛔ REPONSE QUASI VIDE" : "⚠ reponse non vide mais SANS les champs attendus");
      resultats.push({ ...cible, statut, taille: texte.length, inputs, selects, textareas, presents, verdict });
      console.log(`  ${cible.id}  ${cible.quoi}`);
      console.log(`      HTTP ${statut} · ${texte.length} caracteres · ${inputs} input, ${selects} select, ${textareas} textarea`);
      console.log(`      champs attendus trouves : ${presents.length ? presents.join(", ") : "AUCUN"}`);
      console.log(`      -> ${verdict}\n`);
      await new Promise((r) => setTimeout(r, 1200));   // le frein du projet
    }

    console.log("=".repeat(70));
    console.log("LE VERDICT, EN CROISANT LES DEUX FAMILLES");
    console.log("=".repeat(70));
    const brouillons = resultats.filter((r) => r.quoi.startsWith("BROUILLON"));
    const vraies = resultats.filter((r) => r.quoi.startsWith("VRAIE"));
    const okB = brouillons.filter((r) => r.verdict.startsWith("⭐")).length;
    const okV = vraies.filter((r) => r.verdict.startsWith("⭐")).length;
    console.log(`  brouillons servis : ${okB} sur ${brouillons.length}`);
    console.log(`  vraies annonces   : ${okV} sur ${vraies.length}   <- le temoin inverse`);
    console.log("");
    if (okV === 0) {
      console.log("  ⛔ LE TEMOIN INVERSE EST MUET : meme les VRAIES annonces ne rendent rien.");
      console.log("     Donc la sonde mesure autre chose (session, parametres) -- ON NE CONCLUT PAS.");
      process.exitCode = 2;
    } else if (okB === brouillons.length) {
      console.log("  ⭐⭐ UN BROUILLON A BIEN UN FORMULAIRE DE MODIFICATION.");
      console.log("     Donc la modification est techniquement possible, et la lecture seule");
      console.log("     est une DECISION, pas une limite de Hektor.");
    } else if (okB === 0) {
      console.log("  ⛔ AUCUN BROUILLON NE REND DE FORMULAIRE, alors que les vraies annonces oui.");
      console.log("     La lecture seule est donc une LIMITE DE HEKTOR, pas seulement un choix.");
    } else {
      console.log("  ⚠ LES DEUX BROUILLONS NE SE COMPORTENT PAS PAREIL -- a lire ligne par ligne.");
    }
    console.log(`\n✅ ${appels} appels, aucune ecriture.`);
  } catch (e) {
    console.error(`\n⛔ ${e.message}`);
    console.error(`   (${appels} appel(s) fait(s) -- rien n'a ete ecrit)`);
    process.exitCode = 1;
  } finally {
    await nav.close();   // aucun storageState() : la session n'est PAS reecrite
  }
})();
