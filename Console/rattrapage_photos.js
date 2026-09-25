// RAPATRIER LES PHOTOS DU PARC SUR LE SERVEUR
//                                                                  25/09/2026
// POURQUOI : Supabase ne contient AUCUN fichier photo, seulement des adresses chez
// Hektor. Le jour de la coupure, les 444 431 photos deviennent des images mortes
// d'un coup -- fiches, listes, vitrine publique.
//
// ⚠⚠ CE SCRIPT NE PARLE JAMAIS A HEKTOR.
//    Les adresses sont DEJA sur ce serveur, dans le miroir local (data/hektor.sqlite,
//    hektor_annonce_detail.images_json -- 57 967 annonces). On lit en local, on
//    telecharge sur le CDN public.
//    -> AUCUNE requete contre le quota Hektor, aucun risque de bannissement de ce
//       cote, et il tourne EN MEME TEMPS que le rattrapage des documents.
//    (Regle du projet : « chercher d'abord en LOCAL » -- le miroir garde tout.)
//
// ⚠ LE CDN N'EST PAS HEKTOR, ET SA CADENCE NON PLUS. staticlbi sert des fichiers,
//   c'est son metier : le 20/08 il repondait en 55 ms pendant que l'admin nous
//   bannissait. On va donc en parallele et a l'intervalle court -- mais on S'ARRETE
//   NET au premier refus, comme partout ailleurs ici.
//
// ⚠⚠ L'EMPLACEMENT DES FICHIERS VIENT DU WORKER, il n'est jamais recopie.
//    Le worker range une photo sous l'identifiant de SA LIGNE D'INDEX (uuid), pas
//    sous l'identifiant Hektor. Le script cree donc la ligne d'index D'ABORD, puis
//    ecrit le fichier a l'emplacement que le worker ira lire. Sans cela les deux
//    conventions divergeraient et tout serait retelecharge au premier passage.
//
// CE QU'IL ECRIT :
//   - la ligne d'index app_console_photo, cle (annonce, photo Hektor) ;
//   - le fichier sur le serveur.
//   ⛔ IL NE POUSSE RIEN DANS SUPABASE STORAGE. Le serveur est le coffre ; le
//      versement des annonces vivantes vers le cloud est un lot SEPARE.
//
//   node Console/rattrapage_photos.js --dry-run        <- compte, n'ecrit RIEN
//   node Console/rattrapage_photos.js --calibrer 200   <- mesure le debit, n'ecrit RIEN
//   node Console/rattrapage_photos.js --appliquer [--limite N] [--parallele 4]

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

// La convention d'emplacement vient DU WORKER (protege par require.main === module).
const { localPhotoPath, safeFilename } = require("./console_job_worker.js");

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const MIROIR = process.env.HEKTOR_SQLITE_PATH || path.resolve(__dirname, "..", "data", "hektor.sqlite");

const argv = process.argv.slice(2);
const opt = (nom, defaut) => { const i = argv.indexOf(nom); return i >= 0 ? Number(argv[i + 1]) || defaut : defaut; };
const APPLIQUER = argv.includes("--appliquer");
const CALIBRER = argv.includes("--calibrer") ? opt("--calibrer", 200) : 0;
const LIMITE = opt("--limite", 0);
const PARALLELE = Math.max(1, opt("--parallele", 4));
const INTERVALLE = Math.max(0, opt("--intervalle", 100));

class ArretTelechargement extends Error {
  constructor(motif) { super(motif); this.name = "ArretTelechargement"; this.motif = motif; }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Le frein : un jeton toutes les INTERVALLE ms, PARTAGE par les fils. En reservant
// l'instant avant d'attendre, N fils en parallele gardent le meme debit global --
// sinon chacun aurait sa propre cadence et on irait N fois trop vite.
let prochain = 0;
async function frein() {
  const maintenant = Date.now();
  const ceTour = Math.max(maintenant, prochain);
  prochain = ceTour + INTERVALLE;
  if (ceTour > maintenant) await sleep(ceTour - maintenant);
}

async function rest(chemin, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${chemin.replace(/^\/+/, "")}`, {
    ...options,
    headers: { apikey: KEY, Authorization: `Bearer ${KEY}`, "Content-Type": "application/json",
               ...(options.prefer ? { Prefer: options.prefer } : {}) },
  });
  if (!res.ok) throw new Error(`Supabase ${res.status} : ${(await res.text()).slice(0, 200)}`);
  const txt = await res.text();
  return txt ? JSON.parse(txt) : null;
}

// Pagination systematique : sans elle PostgREST plafonne a 1 000 lignes et on croirait
// que les lignes non rendues sont « a faire » -> on les rejouerait indefiniment.
async function tout(chemin) {
  const out = [];
  const page = 1000;
  for (let offset = 0; ; offset += page) {
    const rows = await rest(`${chemin}&limit=${page}&offset=${offset}`);
    if (!Array.isArray(rows) || !rows.length) break;
    out.push(...rows);
    if (rows.length < page) break;
  }
  return out;
}

async function telecharger(url, timeoutMs = 30000) {
  await frein();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: controller.signal,
      headers: { "User-Agent": "GTI-Rattrapage/1.0", Accept: "image/*,*/*" } });
    // ⚠ UN REFUS ARRETE TOUT. Un 404 (photo effacee chez Hektor) reste une erreur
    // ORDINAIRE : elle ne concerne que cette photo, on passe a la suivante.
    if ([401, 403, 429, 503].includes(res.status)) {
      throw new ArretTelechargement(`CDN ${res.status} -- le serveur nous ecarte`);
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return Buffer.from(await res.arrayBuffer());
  } finally { clearTimeout(timer); }
}

function lireLeMiroir() {
  let Database;
  try { Database = require("node:sqlite").DatabaseSync; }
  catch (_) { throw new Error("node:sqlite indisponible -- Node 22+ requis"); }
  if (!fs.existsSync(MIROIR)) throw new Error(`Miroir introuvable : ${MIROIR}`);
  const db = new Database(MIROIR, { readOnly: true });
  const lignes = db.prepare(
    "select hektor_annonce_id, images_json from hektor_annonce_detail where images_json is not null"
  ).all();
  const photos = [];
  const vus = new Set();
  for (const l of lignes) {
    let arr;
    try { arr = JSON.parse(l.images_json); } catch (_) { continue; }
    if (!Array.isArray(arr)) continue;
    for (const e of arr) {
      if (!e || typeof e !== "object") continue;
      const url = String(e.path || e.pathTumb || "").trim();
      const pid = String(e.id != null ? e.id : "").trim();
      if (!/^https?:\/\//i.test(url) || !pid) continue;
      const cle = `${l.hektor_annonce_id}|${pid}`;
      if (vus.has(cle)) continue;   // une meme photo peut figurer deux fois
      vus.add(cle);
      photos.push({
        cle,
        hektor_annonce_id: String(l.hektor_annonce_id),
        hektor_photo_id: pid,
        url,
        url_preview: String(e.pathTumb || url),
        ordre: Number(e.order) || 0,
        visible: !["0", "false", "non"].includes(String(e.visible).toLowerCase()),
        legende: e.legende == null ? null : String(e.legende),
        filename: String(e.img || "").trim() || null,
      });
    }
  }
  db.close();
  return photos;
}

(async () => {
  const mode = APPLIQUER ? "APPLIQUER" : (CALIBRER ? `CALIBRER (${CALIBRER})` : "A BLANC");
  console.log(`MODE : ${mode}   parallele=${PARALLELE}  intervalle=${INTERVALLE} ms`);
  console.log(`miroir : ${MIROIR}\n`);

  const photos = lireLeMiroir();
  console.log(`  photos dans le miroir        : ${photos.length}`);
  console.log(`  annonces concernees          : ${new Set(photos.map((p) => p.hektor_annonce_id)).size}`);

  // ── CALIBRER : on mesure le debit du CDN, sans rien ecrire NI LIRE de Supabase.
  if (CALIBRER) {
    const lot = photos.slice(0, CALIBRER);
    let faits = 0, octets = 0, rates = 0, arret = null, curseur = 0;
    const debut = Date.now();
    await Promise.all(Array.from({ length: PARALLELE }, async () => {
      while (curseur < lot.length && !arret) {
        const p = lot[curseur++];
        try { const b = await telecharger(p.url); faits += 1; octets += b.length; }
        catch (e) { if (e instanceof ArretTelechargement) { arret = e.motif; break; } rates += 1; }
      }
    }));
    const s = (Date.now() - debut) / 1000;
    const debit = faits / Math.max(0.001, s);
    console.log(`\n  CALIBRAGE : ${faits} photo(s), ${rates} en echec, ${(octets / 1024 / 1024).toFixed(1)} Mo en ${s.toFixed(1)} s`);
    console.log(`  DEBIT REEL  : ${debit.toFixed(1)} photos/s · ${(octets / 1024 / 1024 / s).toFixed(1)} Mo/s`);
    console.log(`  taille moyenne : ${faits ? Math.round(octets / faits / 1024) : 0} ko`);
    if (arret) console.log(`  ⛔ ARRET : ${arret}`);
    console.log(`  -> les ${photos.length} photos prendraient ${(photos.length / Math.max(0.01, debit) / 3600).toFixed(1)} h`);
    console.log(`     et peseraient ${(photos.length * (octets / Math.max(1, faits)) / 1024 / 1024 / 1024).toFixed(1)} Go`);
    console.log("\n  (calibrage : AUCUN fichier ecrit, AUCUNE ligne creee)");
    return;
  }

  // ── NOTRE numero de bien, depuis les QUATRE index ───────────────────────────
  // ⚠ REGLE DU PROJET, et elle vaut pour les photos comme pour tout le reste :
  // une ligne porte TOUJOURS les deux numeros. Le numero Hektor designe la fiche
  // chez eux ; le notre survit a la coupure et suit l'annonce si elle est
  // reindexee (REPOINT_TABLES contient app_console_photo).
  // Les 1 397 lignes deja en place les ont toutes les deux : 0 sans numero d'app.
  // Une annonce ne vit pas que dans app_dossier_current -- il faut les 4 index.
  const numeroApp = new Map();
  for (const [table, colonne] of [
    ["app_dossier_current", "app_dossier_id"],
    ["app_archive_annonce_index_current", "app_archive_id"],
    ["app_historical_annonce_index_current", "app_historical_id"],
    ["app_brouillon_annonce_index_current", "app_brouillon_id"],
  ]) {
    for (const r of await tout(`${table}?select=${colonne},hektor_annonce_id&${colonne}=not.is.null`)) {
      if (r.hektor_annonce_id != null) numeroApp.set(String(r.hektor_annonce_id), Number(r[colonne]));
    }
  }
  console.log(`  correspondance des numeros   : ${numeroApp.size} annonces`);

  // ── l'index existant, par (annonce, photo Hektor) ───────────────────────────
  const index = new Map();
  for (const r of await tout("app_console_photo?select=id,hektor_annonce_id,hektor_photo_id,file_size,metadata_json")) {
    index.set(`${r.hektor_annonce_id}|${r.hektor_photo_id}`, r);
  }
  console.log(`  deja dans l'index            : ${index.size}`);

  // On REFUSE d'indexer une photo dont l'annonce n'a pas notre numero : mieux vaut
  // une ligne absente qu'une ligne muette, invisible au repointage. Elles sont
  // comptees et nommees, pas avalees en silence.
  const sansNumeroApp = photos.filter((p) => !numeroApp.has(p.hektor_annonce_id));
  const connues = photos.filter((p) => numeroApp.has(p.hektor_annonce_id));
  const aIndexer = connues.filter((p) => !index.has(p.cle));
  let dejaLa = 0;
  const candidates = [];
  for (const p of connues) {
    const r = index.get(p.cle);
    const chemin = r && r.metadata_json && r.metadata_json.local_archive_path;
    if (chemin) {
      try { if (fs.existsSync(chemin) && fs.statSync(chemin).size > 0) { dejaLa += 1; continue; } }
      catch (_) { /* illisible -> a refaire */ }
    }
    candidates.push(p);
  }

  if (sansNumeroApp.length) {
    const annonces = new Set(sansNumeroApp.map((p) => p.hektor_annonce_id));
    console.log(`  ⛔ ECARTEES (pas de numero app) : ${sansNumeroApp.length} photo(s), ${annonces.size} annonce(s)`);
    console.log(`     annonces : ${[...annonces].slice(0, 10).join(", ")}${annonces.size > 10 ? " ..." : ""}`);
  }
  console.log(`  a creer dans l'index         : ${aIndexer.length}`);
  console.log(`  deja sur le serveur          : ${dejaLa}`);
  console.log(`  ⚠ A RAPATRIER                : ${candidates.length}`);
  const parSec = (1000 / Math.max(1, INTERVALLE));
  console.log(`  duree estimee                : ${(candidates.length / parSec / 3600).toFixed(1)} h a ${parSec.toFixed(1)} photos/s`);

  if (!APPLIQUER) {
    console.log("\n  --dry-run : RIEN n'a ete ecrit. Calibrer d'abord (--calibrer 200), puis --appliquer.");
    return;
  }

  // ── 1. creer les lignes d'index manquantes (par paquets) ────────────────────
  // C'est un prealable au telechargement : c'est l'identifiant de la ligne qui
  // determine l'emplacement du fichier chez le worker.
  const lotIndex = aIndexer.slice(0, LIMITE || aIndexer.length);
  for (let i = 0; i < lotIndex.length; i += 500) {
    const paquet = lotIndex.slice(i, i + 500).map((p) => ({
      app_dossier_id: numeroApp.get(p.hektor_annonce_id),   // NOTRE numero
      hektor_annonce_id: p.hektor_annonce_id,               // le sien
      hektor_photo_id: p.hektor_photo_id,
      filename: p.filename,
      url_hd: p.url,
      url_preview: p.url_preview,
      visible: p.visible,
      legend: p.legende,
      sort_order: p.ordre,
      source: "miroir_local",
      source_json: { origine: "hektor_annonce_detail.images_json", rattrape_le: new Date().toISOString() },
      storage_status: "pending",
    }));
    // Garde-fou : on ne pose RIEN si une seule ligne du paquet partait sans notre
    // numero. C'est le defaut corrige le matin meme sur l'empreinte documentaire --
    // une table de la chaine ancree sur le seul numero Hektor devient illisible a
    // la coupure, et invisible au repointage.
    const muettes = paquet.filter((r) => !Number.isFinite(r.app_dossier_id));
    if (muettes.length) {
      throw new Error(`REFUS : ${muettes.length} ligne(s) sans numero d'app dans le paquet`);
    }
    await rest("app_console_photo?on_conflict=hektor_annonce_id,hektor_photo_id", {
      method: "POST", prefer: "resolution=merge-duplicates,return=minimal", body: JSON.stringify(paquet),
    });
    process.stdout.write(`\r  index : ${Math.min(i + 500, lotIndex.length)}/${lotIndex.length}   `);
  }
  if (lotIndex.length) console.log("");

  // relire pour connaitre les identifiants tout juste crees
  index.clear();
  for (const r of await tout("app_console_photo?select=id,hektor_annonce_id,hektor_photo_id,metadata_json")) {
    index.set(`${r.hektor_annonce_id}|${r.hektor_photo_id}`, r);
  }

  // ── 2. telecharger et deposer sur le serveur ────────────────────────────────
  const lot = candidates.slice(0, LIMITE || candidates.length);
  let faits = 0, octets = 0, rates = 0, arret = null, curseur = 0;
  const debut = Date.now();

  async function fil() {
    while (curseur < lot.length && !arret) {
      const p = lot[curseur++];
      const ligne = index.get(p.cle);
      if (!ligne) { rates += 1; continue; }
      try {
        const buf = await telecharger(p.url);
        const nom = safeFilename(p.filename || `${p.hektor_photo_id}.jpg`, `${p.hektor_photo_id}.jpg`);
        const cible = localPhotoPath(p.hektor_annonce_id, ligne.id, nom);
        fs.mkdirSync(path.dirname(cible), { recursive: true });
        fs.writeFileSync(cible, buf);
        // On VERIFIE apres ecriture : un echec silencieux laisserait l'index
        // annoncer un fichier qui n'existe pas (defaut vecu le 25/09 au matin).
        const taille = fs.statSync(cible).size;
        if (taille !== buf.length) throw new Error(`serveur : ${taille} o au lieu de ${buf.length}`);
        await rest(`app_console_photo?id=eq.${encodeURIComponent(ligne.id)}`, {
          method: "PATCH", prefer: "return=minimal",
          body: JSON.stringify({
            file_size: buf.length,
            sha256: crypto.createHash("sha256").update(buf).digest("hex"),
            storage_status: "local_only",
            synced_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            metadata_json: { ...(ligne.metadata_json || {}), local_archive_path: cible, source_url: p.url },
          }),
        });
        faits += 1; octets += buf.length;
        if (faits % 50 === 0) {
          const s = (Date.now() - debut) / 1000;
          process.stdout.write(`\r  rapatriees : ${faits}/${lot.length}  ·  ${(faits / s).toFixed(1)} photos/s   `);
        }
      } catch (e) {
        if (e instanceof ArretTelechargement) { arret = e.motif; break; }
        rates += 1;
        if (rates <= 5) console.log(`\n  echec ${p.hektor_annonce_id}/${p.hektor_photo_id} : ${e.message}`);
      }
    }
  }
  await Promise.all(Array.from({ length: PARALLELE }, fil));

  const s = (Date.now() - debut) / 1000;
  console.log(`\n\n  ${faits} photo(s) rapatriee(s) · ${rates} en echec · ${(octets / 1024 / 1024).toFixed(1)} Mo`);
  console.log(`  debit : ${(faits / Math.max(0.001, s)).toFixed(1)} photos/s`);
  if (arret) console.log(`  ⛔ ARRET : ${arret}  -- relancer plus tard, la reprise se fait par identifiant`);
})().catch((e) => { console.error("ERREUR :", e.message); process.exit(1); });
