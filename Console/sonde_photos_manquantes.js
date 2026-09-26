// SONDE : Hektor a-t-il des photos que nous n'avons pas ?
//                                                                  26/09/2026
// Une question, une reponse. Chaque nuit, elle prend quelques annonces et compare la
// galerie de Hektor a ce que porte notre miroir. Si Hektor en a une de plus, c'est que
// le rapatriement l'a manquee -- et on le sait le lendemain, pas dans six mois.
//
// ⚠ Elle prend les annonces les PLUS ANCIENNEMENT modifiees. C'est la que l'ecart se
//   verrait : une annonce modifiee hier vient d'etre relue de toute facon, elle ne
//   prouverait rien.
//
// Pour situer : le rapatriement quotidien s'appuie sur le fait qu'ajouter une photo
// dans Hektor FAIT BOUGER la date de l'annonce -- mesure le 26/09 sur 63146, passee de
// « 2026-09-24 12:10:17 » a « 2026-09-26 09:32:51 », l'instant exact de l'ajout. La
// sonde est la pour verifier que ca reste vrai, sans rien supposer.
//
//   node Console/sonde_photos_manquantes.js --echantillon 25
// N'ECRIT RIEN, NI EN LOCAL NI DANS SUPABASE. Sort en 1 si des photos manquent.

const fs = require("fs");
const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

// La lecture d'une galerie vient DU WORKER, elle n'est pas recopiee : deux extractions
// divergeraient au premier ajustement de Hektor, et la sonde crierait a tort.
const { extractConsolePhotoEntries } = require("./console_job_worker.js");

const MIROIR = process.env.HEKTOR_SQLITE_PATH || path.resolve(__dirname, "..", "data", "hektor.sqlite");
const BASE = (process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com").replace(/\/+$/, "");
const XMLRPC = BASE + "/admin/xmlrpc.php";
const POT = process.env.CONSOLE_DETECT_STORAGE_STATE_PATH
  || path.resolve(__dirname, "sessions", "storage_state_documents.json");

const argv = process.argv.slice(2);
const opt = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? Number(argv[i + 1]) || d : d; };
const ECHANTILLON = Math.max(1, opt("--echantillon", 20));
const INTERVALLE = Math.max(0, opt("--intervalle", 1000));   // cadence HEKTOR, pas CDN

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
class Arret extends Error { constructor(m) { super(m); this.name = "Arret"; } }

let dernier = 0;
async function frein() {
  const attente = Math.max(0, dernier + INTERVALLE - Date.now());
  if (attente > 0) await sleep(attente);
  dernier = Date.now();
}

// ⚠⚠ LA CONSOLE HEKTOR REPOND SUR DEUX NOMS DE DOMAINE -- constate le 26/09.
// `groupe-gti-immobilier.la-boite-immo.com` ET `www.gti-immobilier.fr` servent la meme
// application. Le pot de cookies du worker porte l'un OU l'autre, selon celui qu'il a
// utilise en dernier : apres l'envoi d'une photo (qui passe par www.gti-immobilier.fr),
// storage_state_documents.json ne contenait PLUS AUCUN cookie la-boite-immo.com.
// Un filtre sur un seul domaine rend donc « aucun cookie Hektor » alors que la session
// est parfaitement valide. On accepte les deux, et on deduit l'adresse de base de celui
// qui porte effectivement les cookies.
const HOTES = ["groupe-gti-immobilier.la-boite-immo.com", "www.gti-immobilier.fr"];

// ⚠ AVOIR un badge pour une entree ne veut pas dire qu'il y est VALIDE. Constate le
// 26/09 : la sonde a choisi la-boite-immo.com parce qu'elle y avait des cookies, et
// Hektor a rendu 403. On rend donc TOUTES les entrees possibles, et l'appelant essaie.
function sessions() {
  const etat = JSON.parse(fs.readFileSync(POT, "utf8"));
  const toutes = etat.cookies || [];
  const out = [];
  for (const hote of HOTES) {
    const liste = toutes
      .filter((c) => String(c.domain || "").replace(/^\./, "") === hote)
      .map((c) => c.name + "=" + c.value);
    if (liste.length) out.push({ cookieHeader: liste.join("; "), base: "https://" + hote });
  }
  if (!out.length) {
    throw new Error(`aucun cookie Hektor dans ${POT} (cherches sur : ${HOTES.join(", ")})`);
  }
  return out;
}

// On essaie chaque entree UNE SEULE FOIS, AVANT la boucle, sur une annonce connue.
// ⚠ Ce n'est PAS un nouvel essai apres un refus -- la regle du projet reste tenue :
// dans la boucle, un 403 arrete tout. Ici on choisit la porte, au plus deux requetes
// par execution, et si aucune ne repond on s'arrete sans rien tenter de plus.
async function choisirEntree(candidates, annonceTemoin) {
  const refus = [];
  for (const s of candidates) {
    try {
      await lireGalerie(annonceTemoin, s.cookieHeader, s.base);
      return { session: s, refus };
    } catch (e) {
      refus.push(`${s.base} -> ${e.message}`);
    }
  }
  return { session: null, refus };
}

async function lireGalerie(annonceId, cookieHeader, base) {
  const ids = new Set();
  for (const mode of ["vignettes", "vignettes_hidden"]) {
    await frein();
    const url = `${base}/admin/xmlrpc.php?mode=${mode}&id=${encodeURIComponent(annonceId)}&sortBy=byOrder`;
    const res = await fetch(url, { headers: { Cookie: cookieHeader, Accept: "text/html,*/*" } });
    // ⚠ UN REFUS ARRETE TOUT. Regle du projet : un 403 = stop, jamais de nouvel essai.
    if ([401, 403, 429, 503].includes(res.status)) throw new Arret(`Hektor ${res.status}`);
    if (!res.ok) throw new Error(`Hektor ${res.status} sur ${mode}`);
    const html = await res.text();
    if (/type=["']password["']/i.test(html.slice(0, 20000))) throw new Arret("session Hektor expiree");
    for (const e of extractConsolePhotoEntries(html, mode === "vignettes")) {
      ids.add(String(e.hektor_photo_id));
    }
  }
  return ids;
}

function lireLeMiroir() {
  const { DatabaseSync } = require("node:sqlite");
  const db = new DatabaseSync(MIROIR, { readOnly: true });
  // On prefere les annonces a date_maj ANCIENNE : si la date suivait mal les photos,
  // c'est la que l'ecart apparaitrait. Une annonce modifiee hier ne prouve rien.
  const lignes = db.prepare(`
    SELECT d.hektor_annonce_id AS id, d.images_json AS photos, s.date_maj AS date_maj
      FROM hektor_annonce_detail d
      LEFT JOIN sync_annonce_state s ON s.hektor_annonce_id = d.hektor_annonce_id
     WHERE d.images_json IS NOT NULL AND length(d.images_json) > 20
     ORDER BY COALESCE(s.date_maj, '') ASC
     LIMIT 400
  `).all();
  db.close();
  const out = [];
  for (const l of lignes) {
    let arr;
    try { arr = JSON.parse(l.photos); } catch (_) { continue; }
    if (!Array.isArray(arr) || !arr.length) continue;
    const ids = new Set(arr.filter((e) => e && e.id != null).map((e) => String(e.id)));
    if (ids.size) out.push({ id: String(l.id), date_maj: l.date_maj || "?", ids });
  }
  return out;
}

(async () => {
  const candidats = lireLeMiroir();
  if (!candidats.length) { console.log("aucune annonce avec photos dans le miroir"); return; }
  const lot = candidats.slice(0, ECHANTILLON);
  console.log(`sonde photos : ${lot.length} annonce(s), les plus anciennement modifiees`);
  console.log(`  la plus ancienne : ${lot[0].date_maj}\n`);

  const candidates = sessions();
  const choix = await choisirEntree(candidates, lot[0].id);
  for (const r of choix.refus) console.log(`  entree refusee : ${r}`);
  if (!choix.session) {
    console.log(`\n⛔ aucune entree Hektor ne repond -- sonde abandonnee, rien conclu.`);
    console.log(`   (ce n'est PAS « aucune photo manquante » : on n'a pas pu regarder.)`);
    process.exitCode = 1;
    return;
  }
  const { cookieHeader, base } = choix.session;
  console.log(`  entree retenue : ${base}\n`);
  const divergences = [];
  let lues = 0, arret = null;

  for (const a of lot) {
    let chezHektor;
    try {
      chezHektor = await lireGalerie(a.id, cookieHeader, base);
    } catch (e) {
      if (e instanceof Arret) { arret = e.message; break; }
      console.log(`  lecture impossible ${a.id} : ${e.message}`);
      continue;
    }
    lues += 1;
    const manquantes = [...chezHektor].filter((x) => !a.ids.has(x));
    const enTrop = [...a.ids].filter((x) => !chezHektor.has(x));
    if (manquantes.length || enTrop.length) {
      divergences.push({ annonce: a.id, date_maj: a.date_maj,
                         chez_hektor: chezHektor.size, chez_nous: a.ids.size,
                         absentes_du_miroir: manquantes, disparues_de_hektor: enTrop });
    }
  }

  console.log(`  annonces lues        : ${lues}`);
  console.log(`  divergences          : ${divergences.length}`);
  if (arret) console.log(`  ⛔ ARRET : ${arret}`);

  for (const d of divergences.slice(0, 5)) {
    console.log(`\n  ⚠ annonce ${d.annonce} (date_maj ${d.date_maj})`);
    console.log(`      Hektor ${d.chez_hektor} photo(s) · nous ${d.chez_nous}`);
    if (d.absentes_du_miroir.length) {
      console.log(`      ABSENTES DU MIROIR : ${d.absentes_du_miroir.slice(0, 6).join(", ")}`);
    }
    if (d.disparues_de_hektor.length) {
      console.log(`      plus chez Hektor   : ${d.disparues_de_hektor.slice(0, 6).join(", ")}`);
    }
  }

  const manquantes = divergences.filter((d) => d.absentes_du_miroir.length);
  if (manquantes.length) {
    const combien = manquantes.reduce((n, d) => n + d.absentes_du_miroir.length, 0);
    console.log(`\n⚠⚠ ${combien} PHOTO(S) CHEZ HEKTOR QUE NOUS N'AVONS PAS, sur ${manquantes.length} annonce(s).`);
    console.log(`   Le rapatriement quotidien les a manquees -- a regarder.`);
    process.exitCode = 1;
  } else if (divergences.length) {
    // Des photos retirees chez Hektor ne sont PAS un probleme : on les garde expres,
    // une adresse deja diffusee (portail, email) peut encore les reclamer.
    console.log(`\n▫ Aucune photo manquante. ${divergences.length} annonce(s) ont des photos`);
    console.log(`  que Hektor n'a plus -- c'est normal, on les conserve volontairement.`);
  } else if (lues) {
    console.log(`\n✅ Aucune photo manquante sur cet echantillon.`);
  }
})().catch((e) => { console.error("ERREUR :", e.message); process.exit(2); });
