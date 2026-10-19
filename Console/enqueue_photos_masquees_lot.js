// L'EMPILEUR DU BALAYAGE DES PHOTOS MASQUEES                       19/10/2026
// ═══════════════════════════════════════════════════════════════════════════════
// POURQUOI. Depuis le 18/05, deux flux ramenent nos photos et un seul voit les
// MASQUEES : le flux API (nocturne) ne connait que les visibles, la couche
// Console connait les deux -- et PERSONNE NE L'EMPILE PLUS depuis le 17/08
// (315 travaux `sync_hektor_photos`, le dernier le 27/09). Resultat mesure le
// 19/10 : sur 200 annonces sondees en direct, 1,5 % portent des masquees qu'on
// n'a pas, soit ~490 annonces et ~1 100 photos sur le parc vivant.
//
// ⚠⚠ CE SCRIPT NE PARLE JAMAIS A HEKTOR. Il POSE des travaux, et c'est le worker
//    « documents » qui appelle Hektor -- avec SES freins (1 s entre appels, 60 s
//    toutes les 100 lectures, 300 s toutes les 2 000, arret net au premier refus).
//    ⭐ C'EST TOUT L'INTERET DE PASSER PAR LE WORKER : un script separe aurait son
//      PROPRE frein, et les deux s'additionneraient. « Un frein ne protege QU'A
//      L'INTERIEUR d'un client » (lecon du bannissement du 17/09). Mesure du
//      19/10 : `sync_hektor_photos` n'est reclame que par worker_kind
//      « documents » -- donc UN SEUL processus, UN SEUL frein.
//
// ⭐⭐ UN SEUL LOT, DEUX PARTS -- et c'est ce qui evite deux taches qui se bloquent.
//    Deux taches separees se casseraient les dents : la part MAJ poserait ~29
//    travaux, puis le balayage verrait « la file n'est pas vide » et refuserait
//    son lot entier. Donc UN lot, rempli DANS CET ORDRE :
//        ① les annonces DONT LA DATE A BOUGE   (la part « mise a jour »)
//        ② les annonces JAMAIS VISITEES         (la part « balayage »)
//    (Meme patron que enqueue_empreinte_lot.js depuis son correctif du 14/10 :
//     « on ENCHAINE les perimetres jusqu'a remplir le lot ».)
//    ⭐ ET QUAND LE BALAYAGE SERA FINI, le lot tombera tout seul a ~29 par nuit et
//      DEVIENDRA le run de mise a jour. Pas d'interrupteur, pas de 2e tache.
//
// LA TAILLE DU LOT EST BORNEE PAR LE TEMPS, PAS PAR LE QUOTA -- mesure du 19/10 :
//    les 315 travaux reels ont une duree MEDIANE de 10 s (moyenne 12 s, max 79 s).
//        2 h 30 de creux (00:00-02:30) -> ~868 annonces
//        3 h 42 de creux (23:18-03:00) -> ~1 285 annonces
//    D'ou le defaut a 1 000. ⚠ Un lot de 2 000 aurait pris 5,8 a 6,6 HEURES et
//    deborde sur les recherches de 03:00 et le run de 05:00.
//    ⚠ Et cote quota, 1 000 annonces = 2 000 requetes Hektor (les DEUX galeries),
//      a ajouter aux ~4 500 que la nuit consomme deja (entretien 22:00 ~2 680 +
//      recherches 03:00) -- soit ~6 500, sous la cible de Frederic du 20/08
//      (« rester 40 % sous le seuil de 13 000-17 000 »).
//
//   node Console/enqueue_photos_masquees_lot.js --dry-run            <- compte, n'ecrit RIEN
//   node Console/enqueue_photos_masquees_lot.js --limit 1000 --exiger-file-vide
//   node Console/enqueue_photos_masquees_lot.js --scope archive      <- a la main seulement
//
// Codes de sortie : 0 pose ou rien a faire · 3 file occupee · 4 trop d'erreurs · 1 panne

const fs = require("fs");
const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const MIROIR = process.env.HEKTOR_SQLITE_PATH || path.resolve(__dirname, "..", "data", "hektor.sqlite");
const JOB_TYPE = "sync_hektor_photos";

const SOURCES = {
  vivant:     { table: "app_dossier_current",                     idColumn: "app_dossier_id" },
  archive:    { table: "app_archive_annonce_index_current",        idColumn: "app_archive_id" },
  historique: { table: "app_historical_annonce_index_current",     idColumn: "app_historical_id" },
};

// ═══════════════════════════════════════════════════════════════════════════════
// LES PERIMETRES QU'ON NE BALAIE PAS -- PAR DECISION, PAS PAR OUBLI    19/10/2026
// ═══════════════════════════════════════════════════════════════════════════════
// ⭐ MESURE QUI TRANCHE : une annonce ARCHIVEE N'EST PUBLIEE NULLE PART. La requete
//   de la vitrine publique (Ecrans Android/export_project_vitrine.py) filtre
//   `archive=eq.0 & diffusable=eq.1 & statut_annonce in (Actif, Sous offre,
//   Sous compromis)`. Les masquees des archives ne portent donc AUCUN risque de
//   publication -- leur seule valeur est l'archivage pour le jour de la coupure.
//
// ET LE PRIX, mesure le 19/10 :
//       archives 35 329 + historiques 8 948 = 44 277 annonces
//       taux de masquees mesure sur ce perimetre : 0,7 %  (contre 3,6 % sur les vivantes)
//       -> ~310 annonces, ~700 photos, pour 44 NUITS de balayage
//   Contre 14 nuits pour les 13 491 vivantes, ou le taux est 5 fois plus eleve ET
//   ou il y a un vrai risque de publication.
//
// ⚠⚠ POURQUOI UNE LISTE DECLAREE ET PAS UN SIMPLE RETRAIT. La lecon du 14/10
//   (chantier 6, point 6a) : retirer un perimetre sans le DECLARER faisait crier
//   « PERIMETRE OUBLIE » puis « LOT MAIGRE » en code 1 -- un e-mail rouge chaque
//   nuit. Une decision ecrite se DECLARE, elle ne se devine pas.
//
// ⚠ `--scope archive` CONTINUE DE MARCHER A LA MAIN : la porte reste ouverte si
//   Frederic change d'avis. Les brouillons, eux, n'ont rien a y chercher (leurs
//   956 photos sont deja sur le serveur, mesure du chantier 6) ET le worker ne
//   sait pas charger un brouillon (loadDossier ne connait que TROIS index).
const HORS_AUTO = {
  archive:    "19/10 : une archive n'est publiee nulle part (filtre de la vitrine) -- 44 nuits pour ~700 photos. A rouvrir si Frederic le demande.",
  historique: "19/10 : meme raison que les archives.",
  brouillon:  "chantier 6 : leurs 956 photos sont deja sur le serveur, et loadDossier ne connait pas cet index.",
};

// ⚠⚠ LA MARGE DE FUSEAU HORAIRE -- ET ELLE N'EST PAS DECORATIVE.
// Le miroir garde `hektor_annonce.date_maj` en heure LOCALE sans fuseau ecrit
// ('2026-02-20 13:07:26'), et `app_console_job.finished_at` est en UTC. Les
// comparer naivement a deja rendu L'INVERSE DE LA VERITE dans ce projet, a deux
// heures pres (13/10, memoire « comparer deux dates : UTC vs locale »).
// Node interprete une chaine sans fuseau dans le fuseau DE LA MACHINE -- qui est
// en France, donc ca tombe juste aujourd'hui. Mais on ne PARIE pas la dessus :
// on ajoute une marge, DANS LE SENS SUR. Revisiter une annonce pour rien coute
// 2 requetes ; en manquer une perd des photos pour toujours.
const MARGE_FUSEAU_MS = 3 * 3600 * 1000;

const argv = process.argv.slice(2);
function parseArgs() {
  const args = { scope: "vivant", limit: 1000, priority: 200, dryRun: false,
                 exigerFileVide: false, maxErreursRecentes: 0 };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const next = argv[i + 1];
    if (a === "--scope" && next) { args.scope = next; i += 1; }
    else if (a === "--limit" && next) { args.limit = Number(next); i += 1; }
    else if (a === "--priority" && next) { args.priority = Number(next); i += 1; }
    else if (a === "--dry-run") { args.dryRun = true; }
    else if (a === "--exiger-file-vide") { args.exigerFileVide = true; }
    else if (a === "--max-erreurs-recentes" && next) { args.maxErreursRecentes = Number(next); i += 1; }
    else throw new Error("Argument inconnu: " + a);
  }
  if (!SOURCES[args.scope]) {
    throw new Error("--scope doit valoir : " + Object.keys(SOURCES).join(", "));
  }
  if (!Number.isFinite(args.limit) || args.limit <= 0) throw new Error("--limit doit etre un nombre > 0");
  return args;
}

async function rest(pathname, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const response = await fetch(SUPABASE_URL + "/rest/v1/" + pathname.replace(/^\/+/, ""), {
    ...options,
    headers: {
      apikey: KEY, Authorization: "Bearer " + KEY, "Content-Type": "application/json",
      ...(options.prefer ? { Prefer: options.prefer } : {}),
    },
  });
  if (!response.ok) throw new Error("Supabase " + response.status + " " + (await response.text()).slice(0, 300));
  return options.prefer === "return=minimal" ? null : response.json();
}

// ⚠⚠ PAGINATION PAR CURSEUR, recopiee de enqueue_empreinte_lot.js -- et les deux
//   defauts qui l'imposent y sont ecrits : SANS TRI, Postgres n'est pas tenu de
//   rendre les lignes dans le meme ordre d'une page a l'autre (40 % du travail
//   perdu le 25/09, sans un message d'erreur) ; AVEC TRI MAIS PAR DECALAGE, ca
//   expire. On demande « les 1 000 suivants APRES cet identifiant ».
// ⚠ La cle du curseur doit etre UNIQUE et figurer dans le select.
async function lirePages(pathname, cleCurseur, surLigne) {
  const page = 1000;
  let curseur = null;
  for (;;) {
    const apres = curseur == null ? "" : "&" + cleCurseur + "=gt." + encodeURIComponent(String(curseur));
    const rows = await rest(pathname + apres + "&order=" + cleCurseur + ".asc&limit=" + page);
    if (!Array.isArray(rows) || !rows.length) break;
    for (const row of rows) surLigne(row);
    const dernier = rows[rows.length - 1][cleCurseur];
    if (dernier == null) throw new Error("lirePages() : " + cleCurseur + " absent du select");
    curseur = dernier;
    if (rows.length < page) break;
  }
}

// La date de modification que Hektor nous a donnee, par annonce. Elle est DEJA
// sur ce serveur : le run de nuit descend tout l'index chaque nuit (mesure du
// 19/10 : 61 431 lignes sur 61 431 portent synced_at du jour). Zero appel Hektor.
function lireDatesDuMiroir() {
  let Database;
  try { Database = require("node:sqlite").DatabaseSync; }
  catch (_) { throw new Error("node:sqlite indisponible -- Node 22+ requis"); }
  if (!fs.existsSync(MIROIR)) throw new Error("Miroir introuvable : " + MIROIR);
  const db = new Database(MIROIR, { readOnly: true });
  const dates = new Map();
  for (const l of db.prepare("select hektor_annonce_id, date_maj from hektor_annonce where date_maj is not null").all()) {
    const t = Date.parse(String(l.date_maj).replace(" ", "T"));
    if (Number.isFinite(t)) dates.set(String(l.hektor_annonce_id), t);
  }
  db.close();
  return dates;
}

// REFUS 1 : la file n'est pas vide. ⭐ C'EST LA GARDE QUI REGULE LA TAILLE DU LOT.
//   Mesure du 19/10 : la duree par annonce (10 s au median) n'est connue que sur des
//   travaux qui telechargeaient tous ; le vrai rythme du balayage est INCONNU. Si le
//   worker est plus lent que prevu, cette garde refuse le lot suivant et le DIT, au
//   lieu de laisser le retard grossir nuit apres nuit sans que personne le voie.
// REFUS 2 : des erreurs recentes en nombre = Hektor nous rejette. « Un 403 arrete
//   tout, on ne rejoue jamais » -- les ~1 300 refus repetes du 20/08 ont fait bannir
//   notre IP au meme titre que le debit.
async function refusEventuel(args, enFile) {
  if (args.exigerFileVide && enFile.size > 0) {
    console.log(JSON.stringify({ refus: "file_occupee", en_file: enFile.size,
      message: "le lot precedent n'est pas digere -- rien n'est pose. Le worker est plus lent que le lot : baisser --limit." }, null, 2));
    return 3;
  }
  if (args.maxErreursRecentes > 0) {
    const depuis = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
    const recentes = await rest("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE
      + "&status=eq.error&finished_at=gte." + encodeURIComponent(depuis) + "&limit=1000");
    const n = Array.isArray(recentes) ? recentes.length : 0;
    if (n >= args.maxErreursRecentes) {
      console.log(JSON.stringify({ refus: "trop_d_erreurs_recentes", erreurs_24h: n, seuil: args.maxErreursRecentes,
        message: "Hektor nous rejette peut-etre -- on arrete, on ne rejoue jamais" }, null, 2));
      return 4;
    }
  }
  return 0;
}

async function main() {
  const args = parseArgs();
  const source = SOURCES[args.scope];

  if (HORS_AUTO[args.scope] && !argv.includes("--scope")) {
    throw new Error("perimetre hors balayage automatique : " + HORS_AUTO[args.scope]);
  }

  // ── LES TROIS EXCLUSIONS, dans l'ordre du projet ───────────────────────────
  // ⚠ `derniereVisite` n'est pas un simple Set : la part « mise a jour » a besoin
  //   de SAVOIR QUAND on est passe, pour comparer a la date de Hektor.
  const derniereVisite = new Map();   // annonce -> instant du dernier travail fini
  await lirePages("app_console_job?select=id,hektor_annonce_id,finished_at&job_type=eq."
    + JOB_TYPE + "&status=eq.done", "id", (row) => {
      if (!row.hektor_annonce_id) return;
      const t = row.finished_at ? Date.parse(row.finished_at) : 0;
      const a = String(row.hektor_annonce_id);
      if (!derniereVisite.has(a) || t > derniereVisite.get(a)) derniereVisite.set(a, t);
    });

  const erreurs = new Set();
  await lirePages("app_console_job?select=id,hektor_annonce_id&job_type=eq." + JOB_TYPE
    + "&status=eq.error", "id", (row) => { if (row.hektor_annonce_id) erreurs.add(String(row.hektor_annonce_id)); });

  const enFile = new Set();
  await lirePages("app_console_job?select=id,hektor_annonce_id&job_type=eq." + JOB_TYPE
    + "&status=in.(pending,running)", "id", (row) => { if (row.hektor_annonce_id) enFile.add(String(row.hektor_annonce_id)); });

  const code = await refusEventuel(args, enFile);
  if (code) { process.exitCode = code; return; }

  const dates = lireDatesDuMiroir();

  // ── LE PERIMETRE ──────────────────────────────────────────────────────────
  const annonces = [];
  await lirePages(source.table + "?select=" + source.idColumn + ",hektor_annonce_id",
    source.idColumn, (row) => {
      if (row[source.idColumn] == null || !row.hektor_annonce_id) return;
      annonces.push({ dossier: Number(row[source.idColumn]), annonce: String(row.hektor_annonce_id) });
    });

  // ── LE LOT : LES MODIFIEES D'ABORD, LES JAMAIS-VISITEES ENSUITE ───────────
  const aMettreAJour = [];
  const jamaisVues = [];
  let sansDateAuMiroir = 0;
  let ecarteesErreur = 0;
  const nomsEcartees = [];

  for (const a of annonces) {
    if (enFile.has(a.annonce)) continue;
    if (erreurs.has(a.annonce)) {
      ecarteesErreur += 1;
      if (nomsEcartees.length < 20) nomsEcartees.push(a.annonce);
      continue;
    }
    if (!derniereVisite.has(a.annonce)) { jamaisVues.push(a); continue; }
    const quand = dates.get(a.annonce);
    if (quand == null) { sansDateAuMiroir += 1; continue; }
    if (quand > derniereVisite.get(a.annonce) - MARGE_FUSEAU_MS) aMettreAJour.push(a);
  }

  const lot = aMettreAJour.concat(jamaisVues).slice(0, args.limit);

  const bilan = {
    scope: args.scope,
    mode: args.dryRun ? "dry-run" : "applique",
    limite: args.limit,
    annonces_du_perimetre: annonces.length,
    deja_visitees: derniereVisite.size,
    // les deux parts du lot, separees : c'est ce qui dit ou on en est
    part_mise_a_jour_disponible: aMettreAJour.length,
    part_balayage_disponible: jamaisVues.length,
    lot_pose: lot.length,
    dont_mise_a_jour: Math.min(aMettreAJour.length, lot.length),
    dont_balayage: Math.max(0, lot.length - aMettreAJour.length),
    deja_en_file: enFile.size,
    // ⚠ ECARTEES POUR ERREUR : comptees ET NOMMEES. Le projet a paye deux fois
    //   l'exclusion definitive silencieuse (les 527 brouillons, les 33 annonces
    //   bloquees par le coffre). On ne les rejoue pas tout seul -- mais on les VOIT.
    ecartees_pour_erreur: ecarteesErreur,
    exemples_ecartees: nomsEcartees,
    sans_date_au_miroir: sansDateAuMiroir,
    requetes_hektor_attendues: lot.length * 2,
    nuits_restantes_a_ce_rythme: args.limit > 0
      ? Math.ceil((aMettreAJour.length + jamaisVues.length) / args.limit) : null,
  };

  if (!lot.length) {
    bilan.statut = "rien_a_faire";
    console.log(JSON.stringify(bilan, null, 2));
    return;
  }

  if (args.dryRun) {
    bilan.statut = "dry-run -- RIEN n'a ete pose";
    bilan.exemples_du_lot = lot.slice(0, 10).map((a) => a.annonce);
    console.log(JSON.stringify(bilan, null, 2));
    return;
  }

  // ── ON POSE, PAR PAQUETS ──────────────────────────────────────────────────
  // La charge est VIDE : c'est la forme exacte des 315 travaux existants
  // (payload_json = '{}'), mesuree le 19/10. On copie, on n'invente pas.
  const PAQUET = 200;
  let poses = 0;
  for (let i = 0; i < lot.length; i += PAQUET) {
    const tranche = lot.slice(i, i + PAQUET).map((a) => ({
      job_type: JOB_TYPE,
      app_dossier_id: a.dossier,
      hektor_annonce_id: a.annonce,
      payload_json: { origine: "balayage_photos_masquees", pose_le: new Date().toISOString() },
      priority: args.priority,
    }));
    // ⚠ GARDE-FOU : aucune ligne ne part sans notre numero de dossier. Une table de
    //   la chaine ancree sur le seul numero Hektor devient illisible a la coupure.
    const muettes = tranche.filter((r) => !Number.isFinite(r.app_dossier_id));
    if (muettes.length) throw new Error("REFUS : " + muettes.length + " ligne(s) sans numero d'app dans le paquet");
    await rest("app_console_job", { method: "POST", prefer: "return=minimal", body: JSON.stringify(tranche) });
    poses += tranche.length;
  }

  bilan.statut = "pose";
  bilan.travaux_poses = poses;
  console.log(JSON.stringify(bilan, null, 2));
}

main().catch((e) => { console.error("ECHEC :", e.message); process.exitCode = 1; });
