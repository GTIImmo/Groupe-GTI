// QUEL EST LE TAUX REEL DE PHOTOS MASQUEES CHEZ HEKTOR ?            19/10/2026
//
// POURQUOI. Frederic veut rapatrier « l'ensemble des photos masquees sur les
// biens vivants et archives » (48 820 annonces, 1 appel Hektor chacune, soit
// 5 a 10 nuits a cadence sure). AVANT d'engager ca, il faut savoir CE QU'ON VA
// CHERCHER -- et les deux seuls chiffres qu'on a SE CONTREDISENT :
//     · 4,6 % sur les 304 annonces passees par `sync_hektor_photos` en aout
//       (14 avec des masquees) -- mais cet echantillon a probablement ete choisi
//       PARCE QU'ELLES POSAIENT PROBLEME ;
//     · 0 % sur les 10 biens vivants sondes en direct les 16-19/10.
//
// ⚠ ET ON NE PEUT PAS S'APPUYER SUR LA SONDE DU RUN : mesure du 19/10, elle
//   interroge LES MEMES 25 ANNONCES chaque nuit (son journal imprime la meme
//   date, « 2025-10-24 15:08:55 », dix nuits de suite). Elle trie par date de
//   modification croissante, et les plus anciennes sont justement celles qui ne
//   bougent jamais. Son vert est VRAI et il ne repond pas a cette question-ci.
//
// CE QUE FAIT CE FICHIER : UN SEUL GET par annonce, sur un echantillon TIRE AU
// HASARD, et il compte. Il n'ecrit RIEN -- ni Supabase, ni le serveur, ni un
// fichier. Il ne telecharge AUCUNE image.
//
// ⚠ IL PARLE A HEKTOR, et c'est son seul cout. Donc :
//     · cadence 1 appel/seconde (celle de sonde_photos_manquantes.js) ;
//     · ARRET NET au premier 401/403/429/503 -- regle du projet, jamais de
//       nouvel essai (le bannissement du 20/08 est arrive vers 18 000 req/nuit) ;
//     · arret aussi si Hektor rend la page de connexion.
//
// ⭐ LA LECTURE DE LA GALERIE VIENT DU WORKER, elle n'est pas recopiee : deux
//   extractions divergeraient au premier ajustement de Hektor.
//
//   node Console/sonde_taux_photos_masquees.js <fichier-d-ids>
//   node Console/sonde_taux_photos_masquees.js --ids "11008 11156 ..."
//   options : --intervalle 1000

const fs = require("fs");
const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const { extractConsolePhotoEntries } = require("./console_job_worker.js");

const BASE = (process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr").replace(/\/+$/, "");
const POT = process.env.CONSOLE_DETECT_STORAGE_STATE_PATH
  || path.resolve(__dirname, "sessions", "storage_state_documents.json");
const HOTES = ["www.gti-immobilier.fr", "groupe-gti-immobilier.la-boite-immo.com"];

const argv = process.argv.slice(2);
const opt = (n, d) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
const INTERVALLE = Math.max(0, Number(opt("--intervalle", 1000)) || 1000);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
class Arret extends Error { constructor(m) { super(m); this.name = "Arret"; } }

let dernier = 0;
async function frein() {
  const attente = Math.max(0, dernier + INTERVALLE - Date.now());
  if (attente > 0) await sleep(attente);
  dernier = Date.now();
}

// ⚠ L'HOTE VIENT DE LA CONFIGURATION, LES COOKIES SUIVENT (lecon du 26/09) : la
//   Console repond sur DEUX noms, et le pot porte les deux -- avec des valeurs
//   DIFFERENTES. Envoyer les cookies de l'autre session rend la page de login.
function sessions() {
  const etat = JSON.parse(fs.readFileSync(POT, "utf8"));
  const toutes = etat.cookies || [];
  let ordre;
  try {
    const configure = new URL(BASE).hostname;
    ordre = [configure, ...HOTES.filter((h) => h !== configure)];
  } catch (_) { ordre = [...HOTES]; }
  const out = [];
  for (const hote of ordre) {
    const liste = toutes
      .filter((c) => String(c.domain || "").replace(/^\./, "") === hote)
      .map((c) => c.name + "=" + c.value);
    if (liste.length) out.push({ cookieHeader: liste.join("; "), base: "https://" + hote });
  }
  if (!out.length) {
    const presents = [...new Set(toutes.map((c) => String(c.domain || "").replace(/^\./, "")))].join(", ");
    throw new Error(`aucun cookie Hektor dans ${POT} -- domaines presents : ${presents}`);
  }
  return out;
}

async function lireMasquees(annonceId, cookieHeader, base) {
  await frein();
  const url = `${base}/admin/xmlrpc.php?mode=vignettes_hidden&id=${encodeURIComponent(annonceId)}&sortBy=byOrder`;
  const res = await fetch(url, { headers: { Cookie: cookieHeader, Accept: "text/html,*/*" } });
  if ([401, 403, 429, 503].includes(res.status)) throw new Arret(`Hektor ${res.status}`);
  if (!res.ok) throw new Error(`Hektor ${res.status}`);
  const html = await res.text();
  if (/type=["']password["']/i.test(html.slice(0, 20000))) throw new Arret("session Hektor expiree");
  return extractConsolePhotoEntries(html, false);
}

(async () => {
  let ids = [];
  const fichier = argv.find((a) => !a.startsWith("--") && fs.existsSync(a));
  if (fichier) {
    ids = fs.readFileSync(fichier, "utf8").split(/\s+/).map((s) => s.trim()).filter(Boolean);
  } else {
    ids = String(opt("--ids", "")).split(/\s+/).map((s) => s.trim()).filter(Boolean);
  }
  if (!ids.length) { console.error("aucun identifiant d'annonce fourni"); process.exit(2); }

  console.log(`sonde du taux de photos masquees : ${ids.length} annonces, 1 appel/seconde`);
  console.log(`  duree estimee : ${Math.round(ids.length * INTERVALLE / 1000 / 60 * 10) / 10} min\n`);

  const candidates = sessions();
  let session = null;
  for (const s of candidates) {
    try { await lireMasquees(ids[0], s.cookieHeader, s.base); session = s; break; }
    catch (e) { console.log(`  entree refusee : ${s.base} -> ${e.message}`); }
  }
  if (!session) {
    console.log("\n⛔ aucune entree Hektor ne repond -- sonde abandonnee, RIEN CONCLU.");
    console.log("   (ce n'est PAS « 0 % » : on n'a pas pu regarder.)");
    process.exit(1);
  }

  let lues = 0, avecMasquees = 0, totalMasquees = 0, arret = null;
  const detail = [];
  for (const id of ids) {
    try {
      const entries = await lireMasquees(id, session.cookieHeader, session.base);
      lues += 1;
      if (entries.length) {
        avecMasquees += 1;
        totalMasquees += entries.length;
        detail.push({ annonce: id, masquees: entries.length });
      }
      if (lues % 25 === 0) process.stderr.write(`  ${lues}/${ids.length}\r`);
    } catch (e) {
      if (e instanceof Arret) { arret = e.message; break; }
      detail.push({ annonce: id, erreur: e.message });
    }
  }

  const taux = lues ? (avecMasquees / lues) * 100 : 0;
  console.log("\n" + JSON.stringify({
    annonces_demandees: ids.length,
    annonces_LUES: lues,
    arret_premature: arret,
    annonces_AVEC_masquees: avecMasquees,
    taux_pourcent: Math.round(taux * 10) / 10,
    photos_masquees_TOTAL: totalMasquees,
    moyenne_par_annonce_concernee: avecMasquees ? Math.round(totalMasquees / avecMasquees * 10) / 10 : 0,
    // ⚠ UNE PROJECTION N'EST PAS UNE MESURE : elle suppose que l'echantillon
    //   represente le parc. Avec 200 annonces, l'incertitude reste large.
    projection_sur_48820_annonces: Math.round(48820 * taux / 100),
    projection_photos: avecMasquees
      ? Math.round(48820 * taux / 100 * (totalMasquees / avecMasquees)) : 0,
    exemples: detail.slice(0, 12),
  }, null, 2));

  if (arret) {
    console.log(`\n⛔ ARRET PREMATURE (${arret}) -- le taux ci-dessus ne porte que sur ${lues} annonces.`);
    process.exit(1);
  }
  console.log(`\n✅ ${lues} annonces lues, aucun refus de Hektor. Rien n'a ete ecrit.`);
})().catch((e) => { console.error("ECHEC :", e.message); process.exit(1); });
