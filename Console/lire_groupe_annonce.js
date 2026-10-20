// LIRE UN GROUPE DE CHAMPS D'UNE ANNONCE CHEZ HEKTOR -- LECTURE SEULE
//                                                      20/10/2026
//
// POURQUOI CET OUTIL. Avant d'ecrire un champ chez Hektor, il faut savoir ce qu'il
// vaut AUJOURD'HUI -- sinon on ne peut ni prouver le changement, ni remettre
// l'original. Le worker fait exactement cette lecture avant chaque ecriture
// (`postHektorMefUpdate`), par un GET :
//     ?mode=ihmChargeGroupe&idAnnonce=<id>&group=<groupe>&consultMode=editer&ajax=ajax
// Cet outil fait LE MEME GET et imprime les valeurs. Rien d'autre.
//
// ⛔ IL N'ECRIT JAMAIS. Aucun POST, aucune session reecrite.
// ⚠ Arret net au premier 401/403/429/503 ou si Hektor rend la page de connexion
//   (regle du projet : les refus repetes ont fait bannir notre IP le 20/08).
//
//   node Console/lire_groupe_annonce.js 62554
//   node Console/lire_groupe_annonce.js 62554 equipements
//
// Les groupes que le worker connait : ag_interieur, ag_exterieur, equipements,
// secteur, mandat_infofi, mandat_mandatdispo.

const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });
const { chromium } = require("playwright");

const BASE = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const ADMIN = (process.env.HEKTOR_ADMIN_URL || BASE + "/admin").replace(/\/+$/, "");
const SESSION = process.env.CONSOLE_DETECT_STORAGE_STATE_PATH
  || path.resolve(__dirname, "sessions", "storage_state_documents.json");

const ID = String(process.argv[2] || "").trim();
const GROUPE = String(process.argv[3] || "ag_interieur").trim();

if (!/^\d+$/.test(ID)) {
  console.error("usage : node Console/lire_groupe_annonce.js <idAnnonce> [groupe]");
  process.exit(2);
}

(async () => {
  const nav = await chromium.launch({ headless: true });
  try {
    const ctx = await nav.newContext({ storageState: SESSION });
    const url = `${ADMIN}/xmlrpc.php?mode=ihmChargeGroupe&idAnnonce=${encodeURIComponent(ID)}`
              + `&group=${encodeURIComponent(GROUPE)}&consultMode=editer&ajax=ajax`;
    const r = await ctx.request.get(url, {
      headers: { Referer: `${ADMIN}?page=/mes-biens/mon-bien&id=${encodeURIComponent(ID)}` },
      maxRedirects: 0,
    });
    const s = r.status();
    if ([401, 403, 429, 503].includes(s)) throw new Error(`ARRET NET : Hektor rend ${s} -- on ne rejoue jamais`);
    if (s >= 300 && s < 400) throw new Error("ARRET : redirection -- la session a expire");
    if (!r.ok()) throw new Error(`Hektor ${s}`);
    const t = await r.text();
    if (/type=["']password["']/i.test(t.slice(0, 20000))) {
      throw new Error("ARRET : Hektor rend la page de CONNEXION -- la session a expire");
    }

    console.log(`annonce ${ID} -- groupe ${GROUPE} -- ${t.length} caracteres`);
    if (t.length < 200) {
      console.log("\n⛔ REPONSE QUASI VIDE : Hektor ne sert pas ce groupe pour cette annonce.");
      return;
    }

    console.log("\nLES CHAMPS DE SAISIE, AVEC LEUR VALEUR ACTUELLE :");
    let n = 0;
    for (const m of t.matchAll(/<input\b[^>]*>/gi)) {
      const tag = m[0];
      const nom = (tag.match(/name=["']([^"']+)["']/i) || [, ""])[1];
      const type = (tag.match(/type=["']([^"']+)["']/i) || [, "text"])[1].toLowerCase();
      if (!nom || type === "hidden") continue;
      const val = (tag.match(/value=["']([^"']*)["']/i) || [, ""])[1];
      const coche = /\bchecked\b/i.test(tag) ? "  [coche]" : "";
      console.log(`   ${nom.padEnd(20)} (${type.padEnd(8)}) = ${JSON.stringify(val)}${coche}`);
      n += 1;
    }
    if (!n) console.log("   (aucun champ de saisie visible)");

    console.log("\nLES LISTES DEROULANTES ET L'OPTION CHOISIE :");
    let m2 = 0;
    for (const m of t.matchAll(/<select\b[^>]*name=["']([^"']+)["'][^>]*>([\s\S]*?)<\/select>/gi)) {
      const choisie = (m[2].match(/<option[^>]*\bselected\b[^>]*>([\s\S]*?)<\/option>/i) || [, "(rien de choisi)"])[1]
        .replace(/<[^>]+>/g, "").trim();
      const combien = (m[2].match(/<option/gi) || []).length;
      console.log(`   ${m[1].padEnd(20)} -> ${JSON.stringify(choisie)}   (${combien} options)`);
      m2 += 1;
    }
    if (!m2) console.log("   (aucune liste)");

    console.log("\nLES ZONES DE TEXTE :");
    let m3 = 0;
    for (const m of t.matchAll(/<textarea\b[^>]*name=["']([^"']+)["'][^>]*>([\s\S]*?)<\/textarea>/gi)) {
      const txt = m[2].replace(/<[^>]+>/g, "").trim();
      console.log(`   ${m[1].padEnd(20)} = ${JSON.stringify(txt.slice(0, 90))}${txt.length > 90 ? " …" : ""}`);
      m3 += 1;
    }
    if (!m3) console.log("   (aucune)");

    console.log("\n✅ 1 appel, aucune ecriture.");
  } catch (e) {
    console.error(`\n⛔ ${e.message}`);
    process.exitCode = 1;
  } finally {
    await nav.close();   // aucun storageState() : la session n'est PAS reecrite
  }
})();
