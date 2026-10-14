// Composeur de lot pour le rattrapage d'empreintes documentaires (2026-08-21).
//
// enqueue_console_sync_jobs.js empile TOUT un perimetre : il ne sait pas sauter les annonces
// deja marquees. Rejouer une annonce deja traitee coute des requetes Hektor pour rien, et le
// quota de la console web est la contrainte qui a fait bannir notre IP le 20/08.
// Ce script ne retient donc que les annonces reellement a faire.
//
// Trois exclusions, dans cet ordre :
//   1. empreinte deja posee            -> deja rattrapee
//   2. job en erreur sur cette annonce -> NE JAMAIS REJOUER (les 403 repetes ont fait bannir l'IP)
//   3. job pending/running             -> deja dans la file
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const JOB_TYPE = "sync_console_documents";

const SOURCES = {
  archive: { table: "app_archive_annonce_index_current", idColumn: "app_archive_id" },
  historical: { table: "app_historical_annonce_index_current", idColumn: "app_historical_id" },
  brouillon: { table: "app_brouillon_annonce_index_current", idColumn: "app_brouillon_id" },
};

// ═══════════════════════════════════════════════════════════════════════════════
// LES PERIMETRES QU'ON NE RATTRAPE PAS -- PAR DECISION, PAS PAR OUBLI   14/10/2026
// ═══════════════════════════════════════════════════════════════════════════════
// DECISION DE FREDERIC (14/10, chantier 6 point 6a) : « il n'y a pas de documents
// dans les brouillons, donc pas necessaire -- il faut juste le savoir. »
// Les mesures du meme jour vont dans le meme sens : sur les 527 brouillons,
// AUCUN n'est sous mandat (0 numero de mandat), et 0 document n'est indexe chez
// nous pour eux. Un brouillon est une saisie en cours, pas un bien avec un dossier.
//
// ⚠⚠ POURQUOI UNE LISTE DECLAREE, ET PAS UN SIMPLE RETRAIT DE `auto`.
//   Deux alarmes de ce fichier regardent TOUS les perimetres de SOURCES :
//     · « PERIMETRE OUBLIE » -- un perimetre qui a du travail et que `auto` ne
//       visite pas ; elle sort en code 1 ;
//     · « LOT MAIGRE » -- il reste du travail ailleurs et on pose moins d'un
//       dixieme du lot ; elle sort aussi en code 1.
//   La tache « GTI Rattrapage Documents » est surveillee en `critical` dans
//   check_gti_health.py -> un code 1 = UN E-MAIL ROUGE CHAQUE NUIT. Retirer
//   `brouillon` de la liste de `auto` sans le declarer ici aurait donc remplace un
//   probleme par un autre. Une decision ecrite se DECLARE ; elle ne se devine pas.
//
// ⚠ `--scope brouillon` CONTINUE DE MARCHER a la main : la porte reste ouverte si
//   la decision change. Mais dans ce cas il faudra D'ABORD reparer le worker :
//   loadDossier (console_job_worker.js:1927) ne connait que TROIS index, pas celui
//   des brouillons -> aujourd'hui un lot pose a la main echouerait 527 fois sur
//   527, et « on ne rejoue jamais » les exclurait pour toujours (G.1-b).
const HORS_AUTO = {
  brouillon: "decision du 14/10 : pas de documents dans les brouillons (chantier 6, point 6a)",
};

// AJOUTS DU 25/09 pour la tache planifiee de 23:00 -- tous ADDITIFS : sans eux, le
// comportement manuel d'origine est inchange.
//   --scope auto              enchaine les perimetres tout seul. ⚠ DEPUIS LE 14/10 il
//                             enchaine archive -> historical SEULEMENT : les brouillons
//                             sont hors rattrapage par decision (voir HORS_AUTO ci-dessous)
//   --exiger-file-vide        REFUSE de poser un lot si le precedent n'est pas digere
//   --max-erreurs-recentes N  REFUSE si N erreurs ou plus en 24 h (signature d'un rejet Hektor)
// Codes de sortie : 0 pose ou rien a faire · 3 file occupee · 4 trop d'erreurs · 1 panne
function parseArgs(argv) {
  const args = { scope: "archive", limit: 3000, priority: 200, dryRun: false,
                 exigerFileVide: false, maxErreursRecentes: 0 };
  for (let i = 2; i < argv.length; i += 1) {
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
  if (args.scope !== "auto" && !SOURCES[args.scope]) {
    throw new Error("--scope doit valoir : auto, " + Object.keys(SOURCES).join(", "));
  }
  return args;
}

async function rest(pathname, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const response = await fetch(SUPABASE_URL + "/rest/v1/" + pathname.replace(/^\/+/, ""), {
    ...options,
    headers: { apikey: KEY, Authorization: "Bearer " + KEY, "Content-Type": "application/json", ...(options.prefer ? { Prefer: options.prefer } : {}) },
  });
  if (!response.ok) throw new Error("Supabase " + response.status + " " + (await response.text()).slice(0, 300));
  return options.prefer === "return=minimal" ? null : response.json();
}

// ⚠⚠ PAGINATION PAR CURSEUR, et deux defauts vecus le 25/09 au soir l'imposent.
//
// ① SANS TRI, rien ne tient. Lire 436 000 lignes par pages de 1 000 avec un simple
//    decalage et sans ORDER BY ne garantit rien : Postgres n'est pas tenu de rendre les
//    lignes dans le meme ordre d'une page a l'autre. Certaines reviennent deux fois,
//    d'autres JAMAIS. Constate : 174 433 photos sur 435 126 absentes de la table de
//    correspondance, comptees « en echec » alors que le CDN n'avait rien refuse.
//    40 % du travail perdu, sans un seul message d'erreur.
//
// ② AVEC TRI MAIS PAR DECALAGE, ca expire. « saute 400 000 lignes puis donne-m'en
//    1 000 » oblige Postgres a parcourir les 400 000 a chaque page -> statement timeout.
//
// -> On demande « les 1 000 suivants APRES cet identifiant ». Le cout ne depend plus de
//    la profondeur, et l'ordre est stable par construction.
// ⚠ La cle doit etre UNIQUE et figurer dans le select, sinon le curseur saute des lignes.
async function loadSet(pathname, column, cleUnique) {
  const cle = cleUnique || column;
  const set = new Set();
  const page = 1000;
  let curseur = null;
  for (;;) {
    const apres = curseur == null ? "" : "&" + cle + "=gt." + encodeURIComponent(String(curseur));
    const rows = await rest(pathname + apres + "&order=" + cle + ".asc&limit=" + page);
    if (!Array.isArray(rows) || !rows.length) break;
    for (const row of rows) set.add(String(row[column]));
    const dernier = rows[rows.length - 1][cle];
    if (dernier == null) throw new Error("loadSet() : " + cle + " absent du select");
    curseur = dernier;
    if (rows.length < page) break;
  }
  return set;
}

// REFUS 1 : la file n'est pas vide. Poser un lot par-dessus un lot non digere ferait
// grossir le retard nuit apres nuit sans que personne ne le voie -- et un jour le
// rattrapage deborderait sur le run de 05:00, qui a lui aussi besoin de Hektor.
// REFUS 2 : des erreurs recentes en nombre = Hektor nous rejette. La regle du projet est
// « un 403 arrete tout, on ne rejoue jamais » : on s'arrete et on laisse regarder.
async function refusEventuel(args, enFile) {
  if (args.exigerFileVide && enFile.size > 0) {
    console.log(JSON.stringify({ refus: "file_occupee", en_file: enFile.size,
      message: "le lot precedent n'est pas digere -- rien n'est pose" }, null, 2));
    return 3;
  }
  if (args.maxErreursRecentes > 0) {
    const depuis = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
    const recentes = await rest("app_console_job?select=hektor_annonce_id&job_type=eq." + JOB_TYPE
      + "&status=eq.error&finished_at=gte." + encodeURIComponent(depuis) + "&limit=1000");
    const n = Array.isArray(recentes) ? recentes.length : 0;
    if (n >= args.maxErreursRecentes) {
      console.log(JSON.stringify({ refus: "trop_d_erreurs_recentes", erreurs_24h: n,
        seuil: args.maxErreursRecentes,
        message: "Hektor nous rejette peut-etre -- on arrete, on ne rejoue jamais" }, null, 2));
      return 4;
    }
  }
  return 0;
}

// Y a-t-il encore au moins UNE annonce a faire dans ce perimetre ? On s'arrete des la
// premiere trouvee : inutile de balayer 35 000 lignes pour repondre oui.
async function premierReste(source, empreintes, erreurs, enFile) {
  const page = 1000;
  for (let offset = 0; ; offset += page) {
    const rows = await rest(source.table + "?select=" + source.idColumn + ",hektor_annonce_id&order="
      + source.idColumn + ".asc&limit=" + page + "&offset=" + offset);
    if (!Array.isArray(rows) || !rows.length) return false;
    for (const row of rows) {
      const id = String(row.hektor_annonce_id);
      if (!row.hektor_annonce_id || row[source.idColumn] == null) continue;
      if (empreintes.has(id) || erreurs.has(id) || enFile.has(id)) continue;
      return true;
    }
    if (rows.length < page) return false;
  }
}

async function main() {
  const args = parseArgs(process.argv);

  const empreintes = await loadSet("app_console_document_fingerprint?select=hektor_annonce_id", "hektor_annonce_id", "hektor_annonce_id");
  const erreurs = await loadSet("app_console_job?select=id,hektor_annonce_id&job_type=eq." + JOB_TYPE + "&status=eq.error", "hektor_annonce_id", "id");
  const enFile = await loadSet("app_console_job?select=id,hektor_annonce_id&job_type=eq." + JOB_TYPE + "&status=in.(pending,running)", "hektor_annonce_id", "id");

  const code = await refusEventuel(args, enFile);
  if (code) { process.exitCode = code; return; }

  // ⚠⚠ CORRIGE LE 14/10/2026 -- LE SCRIPT NE FAISAIT PAS CE QUE SON PROPRE COMMENTAIRE
  //    ANNONCE. La ligne 29 dit « --scope auto ENCHAINE archive -> historical ->
  //    brouillon tout seul ». Le code, lui, prenait le PREMIER perimetre ayant du
  //    travail et s'arretait la.
  //
  // CE QUE CA A COUTE, MESURE SUR LES JOURNAUX DES NUITS :
  //      30/09 -> 07/10   archive       2 500/nuit
  //      08/10 -> 12/10   historical    2 500 puis 1 000/nuit
  //      13/10            archive       ⛔ UN SEUL TRAVAIL
  //    Pourquoi : `archive` SE REMPLIT TOUS LES JOURS -- chaque annonce archivee dans
  //    la journee y reapparait comme « a faire ». `auto` repartait donc sur `archive`,
  //    y trouvait 1 ou 2 annonces, les posait, et s'arretait -- pendant que
  //    `historical` (2 396) et `brouillon` (527) attendaient.
  //    ⛔ ET IL SORTAIT EN SUCCES : Planificateur vert, moniteur muet. Au rythme
  //      obtenu, les 2 925 annonces restantes n'auraient JAMAIS ete rattrapees.
  //
  // LE CORRECTIF : on ENCHAINE les perimetres jusqu'a remplir le lot. `archive` donne
  // ses 2, `historical` complete jusqu'a la limite, et quand il est fini `brouillon`
  // prend la suite. ⚠ Le comportement de `--scope <un seul>` NE CHANGE PAS.
  // ⚠ 14/10 : `.filter` sur HORS_AUTO -- la liste reste ecrite en entier pour qu'on
  //   voie d'un coup d'oeil l'ordre complet, et la decision se lit a cote.
  //   `--scope <un seul>` n'est PAS filtre : une demande explicite reste explicite.
  const scopes = args.scope === "auto"
    ? ["archive", "historical", "brouillon"].filter((s) => !HORS_AUTO[s])
    : [args.scope];

  const retenus = [];
  const stats = { balayees: 0, deja_marquees: 0, exclues_erreur: 0, deja_en_file: 0 };
  const parScope = {};
  const page = 1000;

  for (const s of scopes) {
    if (retenus.length >= args.limit) break;
    const source = SOURCES[s];
    const avant = retenus.length;
    for (let offset = 0; retenus.length < args.limit; offset += page) {
      const rows = await rest(source.table + "?select=" + source.idColumn + ",hektor_annonce_id&order=" + source.idColumn + ".asc&limit=" + page + "&offset=" + offset);
      if (!Array.isArray(rows) || !rows.length) break;
      for (const row of rows) {
        if (retenus.length >= args.limit) break;
        stats.balayees += 1;
        const id = String(row.hektor_annonce_id);
        if (!row.hektor_annonce_id || row[source.idColumn] == null) continue;
        if (empreintes.has(id)) { stats.deja_marquees += 1; continue; }
        if (erreurs.has(id)) { stats.exclues_erreur += 1; continue; }
        if (enFile.has(id)) { stats.deja_en_file += 1; continue; }
        // ⚠ LE PERIMETRE EST PORTE PAR LA LIGNE, plus par une variable globale : un lot
        //   peut desormais melanger deux perimetres, et chaque travail doit savoir d'ou
        //   il vient (la charge le dit, et `app_dossier_id` depend de la colonne).
        retenus.push({ row, scope: s, source });
      }
      if (rows.length < page) break;
    }
    const pris = retenus.length - avant;
    if (pris) parScope[s] = pris;
  }

  if (!retenus.length) {
    // ⚠ 14/10 : le message disait « TOUS les perimetres sont rattrapes ». Des qu'un
    //   perimetre est hors rattrapage par decision, c'est faux -- et un message faux
    //   dans un journal de nuit, c'est ce qui fait raisonner a cote des semaines plus
    //   tard. On nomme donc ce qui n'est pas compte.
    //   (une demande explicite `--scope brouillon` n'est pas filtree : rien a signaler)
    const horsAuto = args.scope === "auto" ? Object.keys(HORS_AUTO) : [];
    console.log(JSON.stringify({ scope: args.scope, rien_a_faire: true,
      hors_rattrapage: horsAuto.length ? HORS_AUTO : undefined,
      message: horsAuto.length
        ? `perimetres rattrapes, hors : ${horsAuto.join(", ")} (par decision)`
        : "tous les perimetres sont rattrapes" }, null, 2));
    return;
  }

  let empiles = 0;
  if (!args.dryRun) {
    for (let i = 0; i < retenus.length; i += 100) {
      const jobs = retenus.slice(i, i + 100).map(({ row, scope, source }) => ({
        job_type: JOB_TYPE,
        app_dossier_id: Number(row[source.idColumn]),
        hektor_annonce_id: String(row.hektor_annonce_id),
        payload_json: { scope, lot: "empreinte" },
        status: "pending",
        priority: args.priority,
      }));
      await rest("app_console_job", { method: "POST", prefer: "return=minimal", body: JSON.stringify(jobs) });
      empiles += jobs.length;
    }
  }

  // ⚠⚠ ET IL DOIT CRIER QUAND IL POSE RIDICULEMENT PEU (14/10/2026).
  //
  // C'est la seconde moitie du defaut : la nuit du 13/10 a pose 1 travail sur 2 925
  // restants et a SORTI EN SUCCES. Une nuit perdue ne se voyait nulle part -- ni dans
  // le Planificateur, ni dans check_gti_health. Un rattrapage qui cale en silence est
  // pire que pas de rattrapage, parce que personne ne le cherche.
  //
  // LA REGLE : s'il reste du travail ET qu'on en a pris moins d'un dixieme du lot
  // demande, quelque chose cloche -- on le DIT et on sort en 1. On ne juge pas sur un
  // nombre absolu : un lot de 50 demande qui en pose 40 est normal, un lot de 1 000 qui
  // en pose 1 ne l'est pas.
  // ⚠ Et on ne crie PAS quand tout est rattrape : « plus rien a faire » est un succes,
  //   c'est le cas `rien_a_faire` au-dessus, qui sort avant.
  // ⚠ ET MON ALARME AVAIT ELLE-MEME UN DEFAUT, TROUVE EN L'EPROUVANT : `enFile` ne
  //   contient pas ce qu'on vient de poser, donc `premierReste` revoyait les lignes du
  //   lot comme « restantes ». La DERNIERE nuit -- celle qui pose les 2 dernieres
  //   annonces et termine le rattrapage -- aurait donc crie « lot maigre » alors que
  //   tout etait fini. Une alarme qui crie le jour de la victoire, c'est precisement
  //   ce que je passe mes journees a corriger ailleurs.
  const posees = new Set(retenus.map(({ row }) => String(row.hektor_annonce_id)));
  const dejaVues = new Set([...enFile, ...posees]);

  // ⚠⚠ ET ON REGARDE **TOUS** LES PERIMETRES CONNUS, pas seulement ceux qu'on vient de
  //   parcourir. C'est ce qui rend cette alarme ATTEIGNABLE, et donc utile.
  //
  //   Une fois le defaut d'enchainement corrige, « lot maigre » ne peut plus arriver
  //   par la cause d'hier : `auto` remplit le lot en enchainant. L'alarme ne servirait
  //   alors a rien -- et une alarme qu'on ne peut pas declencher est un decor.
  //   LE CAS QU'ELLE ATTRAPE VRAIMENT : un perimetre ajoute a SOURCES et OUBLIE dans la
  //   liste de `auto`. Son travail ne serait jamais pose, et personne ne le saurait --
  //   exactement le defaut d'hier, sous une autre forme. En balayant SOURCES, on le voit.
  const aRegarder = args.scope === "auto" ? Object.keys(SOURCES) : scopes;
  const restantAilleurs = [];
  for (const s of aRegarder) {
    if (await premierReste(SOURCES[s], empreintes, erreurs, dejaVues)) restantAilleurs.push(s);
  }
  // Un perimetre qui a du travail et que `auto` n'a jamais visite : c'est un oubli de
  // cablage, et il est GRAVE -- on crie meme si le lot est plein.
  //
  // ⚠⚠ 14/10 : LES DEUX ALARMES IGNORENT LES PERIMETRES DE `HORS_AUTO`, et sans ca le
  //   frein des brouillons se payait en rouges quotidiens :
  //     · « PERIMETRE OUBLIE » aurait crie DES CETTE NUIT (brouillon a du travail et
  //       n'est plus visite) ;
  //     · « LOT MAIGRE » aurait crie des la fin des vendus/clos (il ne reste alors que
  //       les 1 ou 2 archives du jour, soit moins d'un dixieme du lot, avec « du travail
  //       ailleurs » = les brouillons).
  //   Un perimetre hors rattrapage par DECISION n'est ni un oubli ni un calage. Il
  //   reste affiche dans `reste_a_faire` -- on le voit -- mais il ne declenche rien.
  const restantSansDecision = restantAilleurs.filter((s) => !HORS_AUTO[s]);
  const oublies = restantSansDecision.filter((s) => !scopes.includes(s));
  const maigre = retenus.length < Math.max(1, Math.floor(args.limit / 10));

  console.log(JSON.stringify({ scope: args.scope, par_perimetre: parScope, ...stats,
    retenus: retenus.length, jobs_empiles: args.dryRun ? 0 : empiles, dry_run: args.dryRun,
    reste_a_faire: restantAilleurs,
    hors_rattrapage: args.scope === "auto" ? HORS_AUTO : undefined }, null, 2));

  if (oublies.length) {
    console.error(`PERIMETRE OUBLIE : ${oublies.join(", ")} -- il a du travail et `
      + `« --scope auto » ne le visite pas. Son travail ne sera JAMAIS pose. `
      + `Ajouter le perimetre a la liste de "auto" (voir l'en-tete de ce fichier).`);
    process.exitCode = 1;
  } else if (maigre && restantSansDecision.length) {
    console.error(`LOT MAIGRE : ${retenus.length} travail(aux) pose(s) pour une limite de `
      + `${args.limit}, alors qu'il reste du travail dans : ${restantSansDecision.join(", ")}. `
      + `Le rattrapage n'avance pas -- voir l'en-tete de ce fichier.`);
    process.exitCode = 1;
  }
}

main().catch((error) => { console.error(error.message); process.exit(1); });
