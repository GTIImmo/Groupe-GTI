#!/usr/bin/env node
/**
 * G.13 -- FABRIQUER LES DERIVES DES PHOTOS D'ANNONCES EN VENTE       26/09/2026
 *
 * Il ne contient AUCUNE logique de fabrication : il appelle genererDerivesPhoto du
 * worker, la meme fonction que le run utilisera. Une seule recette, un seul endroit.
 *
 *   node Console/generer_derives_photos.js --dry-run
 *   node Console/generer_derives_photos.js --appliquer --limite 200
 *   node Console/generer_derives_photos.js --appliquer --parallele 4
 *
 * ⚠ IL NE PARLE JAMAIS A HEKTOR. Il lit les masters sur NOTRE serveur et depose chez
 *   Supabase. Aucune requete contre le quota -- il peut tourner en pleine journee.
 *
 * ⚠ REPRENABLE PAR NATURE : il ne prend que les photos dont derives_generes_le est
 *   NULL. Coupe-le, relance-le, il repart ou il s'est arrete. Pas de curseur a garder.
 *
 * ⚠ PAGINATION PAR CURSEUR, jamais par position. Le 25/09, un offset sans ORDER BY a
 *   fait disparaitre 174 433 photos sur 435 126 en silence ; avec ORDER BY, la requete
 *   expirait en profondeur. On avance donc par id croissant.
 */

const path = require("path");

for (const f of ["Console/.env", ".env", "matterport/.env", "apps/hektor-v1/.env"]) {
  require("dotenv").config({ path: path.join(__dirname, "..", f.replace("Console/", "")) });
}
const worker = require("./console_job_worker.js");
const fs = require("fs");

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

const args = process.argv.slice(2);
const opt = (nom, repli) => {
  const i = args.indexOf(nom);
  return i >= 0 && args[i + 1] ? args[i + 1] : repli;
};
const APPLIQUER = args.includes("--appliquer");
const DRY = !APPLIQUER;
const LIMITE = Number(opt("--limite", "0")) || Infinity;
const PARALLELE = Math.max(1, Number(opt("--parallele", "4")));

function rest(chemin, options = {}) {
  return fetch(`${SUPABASE_URL}/rest/v1/${chemin}`, {
    ...options,
    headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}`, ...(options.headers || {}) },
  }).then(async (r) => {
    if (!r.ok) throw new Error(`Supabase ${r.status} sur ${chemin} : ${(await r.text()).slice(0, 200)}`);
    return r.json();
  });
}

const ko = (o) => (o / 1024).toFixed(0);
const go = (o) => (o / 1073741824).toFixed(1);

(async () => {
  if (!SUPABASE_URL || !SERVICE_KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");

  // ── qui est VIVANTE ? la meme verite que partout : app_dossier_current ──────
  const vivantes = new Set();
  for (let p = 0; ; p += 1000) {
    const l = await rest(`app_dossier_current?select=app_dossier_id&order=app_dossier_id&limit=1000&offset=${p}`);
    for (const r of l) vivantes.add(Number(r.app_dossier_id));
    if (l.length < 1000) break;
  }
  console.log(`annonces en vente          : ${vivantes.size}`);

  // ── la liste a faire ────────────────────────────────────────────────────────
  // ⚠ ON INTERROGE PAR PAQUETS DE NUMEROS D'ANNONCES, pas par curseur sur toute la
  // table. Mesure du 26/09 : « derives_generes_le is null » vise ~362 000 photos (toutes
  // les archivees), et filtrer « vivante » en JS obligeait a parcourir 362 pages pour
  // trouver 3 photos -- six minutes de liste pour trois secondes de travail. Or le
  // perimetre EST connu d'avance : les 13 438 annonces en vente. On demande donc
  // directement leurs photos, par paquets de PAQUET numeros.
  // (Le curseur reste la bonne reponse quand on balaie TOUT -- cf rattrapage_photos.js.
  //  Ici on ne balaie pas tout : on connait la liste des annonces.)
  const PAQUET = 200;
  const numeros = [...vivantes];
  const aFaire = [];
  for (let d = 0; d < numeros.length && aFaire.length < LIMITE; d += PAQUET) {
    const tranche = numeros.slice(d, d + PAQUET);
    const lot = await rest(
      "app_console_photo?select=id,app_dossier_id,hektor_annonce_id,hektor_photo_id,filename,metadata_json,file_size"
      + "&derives_generes_le=is.null&present_in_hektor=is.true"
      + `&app_dossier_id=in.(${tranche.join(",")})&order=id&limit=5000`);
    for (const r of lot) if (aFaire.length < LIMITE) aFaire.push(r);
  }
  console.log(`photos sans derives        : ${aFaire.length}`);

  // ── le master est-il bien sur le serveur ? ──────────────────────────────────
  const cheminMaster = (r) => (r.metadata_json && r.metadata_json.local_archive_path)
    || worker.localPhotoPath(r.hektor_annonce_id, r.id, r.filename);
  const presents = [];
  const absents = [];
  for (const r of aFaire) (fs.existsSync(cheminMaster(r)) ? presents : absents).push(r);
  console.log(`  master present sur disque: ${presents.length}`);
  console.log(`  master ABSENT            : ${absents.length}`
    + (absents.length ? `   (ex. annonces ${[...new Set(absents.slice(0, 5).map((r) => r.hektor_annonce_id))].join(", ")})` : ""));

  const poidsMasters = presents.reduce((s, r) => s + Number(r.file_size || 0), 0);
  console.log(`  poids des masters        : ${go(poidsMasters)} Go`);

  if (DRY) {
    // 18 Go mesures sur 74 550 au calibrage G.12 -> ratio derives/master
    const ratio = 18 / 49.7;
    console.log(`\n(marche a blanc) projection : ~${(go(poidsMasters) * ratio).toFixed(1)} Go de derives`);
    console.log("Rien n'a ete fabrique. Relancer avec --appliquer.");
    return;
  }

  // ── on fabrique ─────────────────────────────────────────────────────────────
  console.log(`\nfabrication, ${PARALLELE} en parallele...\n`);
  const t0 = Date.now();
  let faites = 0, sautees = 0, erreurs = 0, octets = 0;
  const parErreur = new Map();
  let i = 0;

  async function fil() {
    for (;;) {
      const r = aFaire[i++];
      if (!r) return;
      try {
        // ⚠ force: true -- l'interrupteur du worker reste ETEINT ; c'est CE script qui
        // decide, pas une variable d'environnement oubliee quelque part.
        const res = await worker.genererDerivesPhoto(r, { force: true });
        if (res.saute) { sautees += 1; parErreur.set(res.saute, (parErreur.get(res.saute) || 0) + 1); }
        else {
          faites += 1;
          octets += Object.values(res.derives).reduce((s, d) => s + d.octets, 0);
        }
      } catch (e) {
        // ⚠ try/catch PAR PHOTO : une photo en echec n'arrete pas les 74 549 autres.
        erreurs += 1;
        const cle = (e && e.message ? e.message : String(e)).slice(0, 70);
        parErreur.set(cle, (parErreur.get(cle) || 0) + 1);
      }
      const total = faites + sautees + erreurs;
      if (total % 250 === 0) {
        const s = (Date.now() - t0) / 1000;
        const reste = (aFaire.length - total) / (total / s);
        console.log(`  ${String(total).padStart(6)}/${aFaire.length}`
          + `  ${(total / s).toFixed(1)}/s  ${go(octets)} Go  reste ~${(reste / 60).toFixed(0)} min`);
      }
    }
  }
  await Promise.all(Array.from({ length: PARALLELE }, fil));

  const s = (Date.now() - t0) / 1000;
  console.log(`\n${"-".repeat(64)}`);
  console.log(`fabriquees   : ${faites}`);
  console.log(`sautees      : ${sautees}`);
  console.log(`en erreur    : ${erreurs}`);
  console.log(`poids depose : ${go(octets)} Go   (moyenne ${ko(octets / Math.max(1, faites))} ko par photo)`);
  console.log(`duree        : ${(s / 60).toFixed(1)} min   (${(faites / s).toFixed(1)} photos/s)`);
  if (parErreur.size) {
    console.log("\ncauses :");
    for (const [c, n] of [...parErreur].sort((a, b) => b[1] - a[1]).slice(0, 8)) console.log(`  ${String(n).padStart(6)}  ${c}`);
  }
  process.exit(erreurs > faites ? 1 : 0);
})().catch((e) => { console.error("ERREUR :", e.message); process.exit(1); });
