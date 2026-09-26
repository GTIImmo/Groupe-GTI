// LES DERIVES PUBLICS D'UNE PHOTO -- G.11                             26/09/2026
//
// Ce fichier tient les CINQ pieges mesures le 26/09 en preparant le generateur :
//   ① l'adresse publique ne porte AUCUN numero Hektor -- elle ne se corrige plus
//      apres diffusion (un portail l'a en cache, un email l'integre) ;
//   ② une photo sans notre numero doit faire REFUSER, pas produire une adresse
//      boiteuse -- c'est la regle des deux numeros appliquee a L'ECRITURE, la leçon
//      du 25/09 (je l'appliquais en inspectant, je l'oubliais en ecrivant) ;
//   ③ le depot doit viser le coffre PUBLIC : sans le parametre, un derive partirait
//      dans le coffre PRIVE des documents, invisible du front ;
//   ④ la duree de cache doit valoir EXACTEMENT « max-age=N ». Mesure : la forme plus
//      riche (« public, max-age=N, immutable ») est ignoree EN SILENCE par Supabase et
//      le fichier ressort en no-cache -- chaque affichage repasserait en egress ;
//   ⑤ rien ne doit se generer tant que l'interrupteur est eteint.
//
// Il fait tourner LES VRAIES fonctions du worker avec un faux Supabase et un faux
// sharp. N'APPELLE RIEN : ni Hektor, ni le CDN, ni Supabase. N'ECRIT RIEN.

const fs = require("fs");
const os = require("os");
const path = require("path");

// TEST_WORKER_FILE permet de viser une COPIE ABIMEE du worker : c'est ainsi qu'on
// verifie que ce fichier passe au ROUGE quand le code est faux. Un test qui n'a
// jamais ete rouge ne prouve rien.
const WORKER = process.env.TEST_WORKER_FILE || path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(WORKER, "utf8");
const FIN = String.fromCharCode(10) + "}";

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}
function tranche(marque) {
  const d = src.indexOf(marque);
  if (d < 0) return null;
  const f = src.indexOf(FIN, d);
  return f < 0 ? null : src.slice(d, f + 2);
}

const blocReglages = (() => {
  const d = src.indexOf("const COFFRE_PHOTO_PUBLIC");
  const f = src.indexOf(String.fromCharCode(10), src.indexOf("const DERIVES_PHOTO_ENABLED"));
  return d < 0 || f < 0 ? null : src.slice(d, f);
})();
const blocChemin = tranche("function cheminDerivePhoto(");
const blocGen = tranche("async function genererDerivesPhoto(");
const blocStorage = tranche("async function storageRequest(");
const blocUpload = tranche("async function uploadStorageObject(");

for (const [nom, bloc] of [["reglages", blocReglages], ["cheminDerivePhoto", blocChemin],
  ["genererDerivesPhoto", blocGen], ["storageRequest", blocStorage], ["uploadStorageObject", blocUpload]]) {
  if (!bloc) { console.error(`${nom} introuvable -- test non concluant`); process.exit(1); }
}
if (!/return \{ derives, coffre/.test(blocGen)) {
  console.error("tranche de genererDerivesPhoto incomplete -- test non concluant");
  process.exit(1);
}

// ── le banc d'essai ───────────────────────────────────────────────────────────
function banc({ allume = true, env = {} } = {}) {
  const depots = [];
  const patchs = [];
  // ⚠ UN SEUL journal, dans l'ordre : deux listes separees ne disent pas QUI est
  // venu avant. C'est ce qui manquait au controle (i) -- une avarie deplaçant
  // l'ecriture avant le depot restait verte.
  const journal = [];
  const fauxProcess = { env: { CONSOLE_DERIVES_PHOTO_ENABLED: allume ? "1" : "", ...env } };
  const fauxSharp = () => {
    const chaine = {
      resize(o) { chaine._resize = o; return chaine; },
      jpeg(o) { chaine._jpeg = o; return chaine; },
      async toBuffer() { return Buffer.alloc(1234, 7); },
    };
    return chaine;
  };
  const uploadStorageObject = async (chemin, buffer, mime, options = {}) => {
    depots.push({ chemin, octets: buffer.length, mime, ...options });
    journal.push(`depot:${chemin}`);
  };
  const supabaseRequest = async (chemin, options = {}) => {
    patchs.push({ chemin, methode: options.method, corps: options.body ? JSON.parse(options.body) : null });
    journal.push(`ecriture:${options.method}`);
  };
  // eslint-disable-next-line no-new-func
  const fn = new Function("fs", "process", "require", "localPhotoPath", "uploadStorageObject",
    "supabaseRequest", "chargerSharp", "Buffer",
    `${blocReglages}
     ${blocChemin}
     ${blocGen}
     return genererDerivesPhoto;`)(
    fs, fauxProcess, require,
    (a, p, n) => path.join(os.tmpdir(), "absent", String(a), String(p), String(n)),
    uploadStorageObject, supabaseRequest, () => fauxSharp, Buffer);
  return { fn, depots, patchs, journal };
}

// un vrai fichier sur le disque, pour que le master existe
const dossierTmp = fs.mkdtempSync(path.join(os.tmpdir(), "derives-"));
const master = path.join(dossierTmp, "master.jpg");
fs.writeFileSync(master, Buffer.alloc(9000, 3));
const ligne = (extra = {}) => ({
  id: "71ff6473-0173-4a47-84d0-221fb05337a4",
  app_dossier_id: 1354344,
  hektor_annonce_id: "100",
  hektor_photo_id: "347",
  filename: "photo.jpg",
  metadata_json: { local_archive_path: master },
  ...extra,
});

(async () => {
  console.log("\nLES DERIVES PUBLICS D'UNE PHOTO -- G.11\n");

  // ── ⑤ dormant ─────────────────────────────────────────────────────────────
  console.log("⑤ l'interrupteur");
  {
    const { fn, depots, patchs } = banc({ allume: false });
    const r = await fn(ligne());
    controle("(a) eteint -> RIEN ne se genere, rien ne se depose, rien ne s'ecrit",
      r.saute === "eteint" && !depots.length && !patchs.length,
      `${JSON.stringify(r)} depots=${depots.length} ecritures=${patchs.length}`);
  }

  // ── ① et ③ et ④ le depot ──────────────────────────────────────────────────
  console.log("\n① l'adresse, ③ le coffre, ④ la duree de cache");
  {
    const { fn, depots, patchs, journal } = banc();
    await fn(ligne());
    controle("(b) deux tailles deposees, w400 et w1600",
      depots.length === 2 && depots[0].chemin.endsWith("w400.jpg") && depots[1].chemin.endsWith("w1600.jpg"),
      JSON.stringify(depots.map((d) => d.chemin)));
    controle("(c) ⚠ AUCUN numero Hektor dans l'adresse (ni l'annonce 100, ni la photo 347)",
      depots.every((d) => !/(^|\/)100(\/|$)/.test(d.chemin) && !/(^|\/)347(\/|$)/.test(d.chemin)),
      JSON.stringify(depots.map((d) => d.chemin)));
    controle("(d) elle porte NOS deux numeros, dans cet ordre : dossier / photo / taille",
      depots[0].chemin === "1354344/71ff6473-0173-4a47-84d0-221fb05337a4/w400.jpg",
      depots[0].chemin);
    controle("(e) ③ le coffre est le PUBLIC, pas celui des documents",
      depots.every((d) => d.bucket === "gti-photo"), JSON.stringify(depots.map((d) => d.bucket)));
    controle("(f) ④ la duree de cache vaut EXACTEMENT « max-age=N », sans enrobage",
      depots.every((d) => /^max-age=\d+$/.test(String(d.cacheControl || ""))),
      JSON.stringify(depots.map((d) => d.cacheControl)));
    controle("(g) et elle est longue (un an au moins)",
      depots.every((d) => Number(String(d.cacheControl).replace("max-age=", "")) >= 31536000),
      JSON.stringify(depots.map((d) => d.cacheControl)));
    controle("(h) le type depose est une image",
      depots.every((d) => d.mime === "image/jpeg"), JSON.stringify(depots.map((d) => d.mime)));
    // ⚠ L'ORDRE, pas seulement le contenu. Noter avant d'avoir depose ferait croire
    // au front qu'une adresse existe alors que le coffre est vide -- ecran cassé.
    controle("(i) la ligne n'est notee qu'APRES le depot des deux tailles",
      journal.length === 3
        && journal[0].startsWith("depot:") && journal[1].startsWith("depot:")
        && journal[2] === "ecriture:PATCH"
        && Boolean(patchs[0].corps.derives_generes_le) && Boolean(patchs[0].corps.derives_json.w1600),
      journal.join(" -> "));
    controle("(j) et elle retient le chemin ET le poids de chaque taille",
      Boolean(patchs[0].corps.derives_json.w400.chemin)
        && Number.isFinite(patchs[0].corps.derives_json.w400.octets),
      JSON.stringify(patchs[0].corps.derives_json));
  }

  // ── ② le refus ────────────────────────────────────────────────────────────
  console.log("\n② ⚠ la regle des deux numeros, appliquee a L'ECRITURE");
  for (const [quoi, extra] of [["app_dossier_id absent", { app_dossier_id: null }],
                               ["app_dossier_id a zero", { app_dossier_id: 0 }],
                               ["app_dossier_id non numerique", { app_dossier_id: "abc" }]]) {
    const { fn, depots } = banc();
    let leve = "";
    try { await fn(ligne(extra)); } catch (e) { leve = e.message; }
    controle(`(k) ${quoi} -> on REFUSE, et rien n'est depose`,
      /REFUS/.test(leve) && !depots.length,
      leve ? `a leve « ${leve.slice(0, 70)} » mais ${depots.length} depot(s)` : "n'a PAS leve");
  }
  {
    const { fn, depots } = banc();
    let leve = "";
    try { await fn(ligne({ id: null })); } catch (e) { leve = e.message; }
    controle("(l) sans id de ligne non plus -- c'est lui qui porte l'adresse",
      /REFUS/.test(leve) && !depots.length, leve || "n'a PAS leve");
  }

  // ── le master manquant ne doit pas lever ──────────────────────────────────
  console.log("\n▫ le master manquant");
  {
    const { fn, depots, patchs } = banc();
    const r = await fn(ligne({ metadata_json: {} }));
    controle("(m) master absent -> on saute SANS lever, et on ne pretend pas avoir des derives",
      r.saute === "master_absent" && !depots.length && !patchs.length,
      JSON.stringify(r));
  }

  // ── on n'agrandit jamais, et les reglages sont ceux du calibrage ───────────
  console.log("\n▫ les reglages calibres (G.12)");
  controle("(n) withoutEnlargement : un master plus petit que la cible n'est pas agrandi",
    /withoutEnlargement:\s*true/.test(blocGen), "un master de 800 px serait etire en 1600");
  controle("(o) les deux tailles sont 400 et 1600, aux qualites calibrees 75 et 82",
    /nom:\s*"w400",\s*largeur:\s*400,\s*qualite:\s*75/.test(blocReglages)
    && /nom:\s*"w1600",\s*largeur:\s*1600,\s*qualite:\s*82/.test(blocReglages),
    blocReglages.replace(/\s+/g, " ").slice(-160));

  // ── AUCUNE REGRESSION sur le depot des documents ──────────────────────────
  console.log("\n▫ le depot des documents n'a pas bouge");
  {
    const appels = [];
    const fauxFetch = async (url, options) => {
      appels.push({ url, headers: options.headers });
      return { ok: true, status: 200 };
    };
    // eslint-disable-next-line no-new-func
    const mod = new Function("fetch", "requireEnv", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
      "STORAGE_BUCKET", "storagePathEncode", "restHeaders",
      `${blocStorage}\n${blocUpload}\nreturn { storageRequest, uploadStorageObject };`)(
      fauxFetch, (n, v) => v, "https://x.supabase.co", "cle", "hektor-console-documents",
      (v) => String(v), (ct) => (ct ? { "Content-Type": ct } : {}));

    await mod.uploadStorageObject("a/b.pdf", Buffer.alloc(10), "application/pdf");
    controle("(p) sans parametre de coffre -> toujours le coffre PRIVE des documents",
      appels[0].url.includes("/object/hektor-console-documents/"), appels[0].url);
    controle("(q) et toujours AUCUNE duree de cache (les documents passent par URL signee)",
      !("cache-control" in appels[0].headers), JSON.stringify(appels[0].headers));

    await mod.uploadStorageObject("1/2/w400.jpg", Buffer.alloc(10), "image/jpeg",
      { bucket: "gti-photo", cacheControl: "max-age=31536000" });
    controle("(r) avec les parametres -> coffre public ET duree de cache posee",
      appels[1].url.includes("/object/gti-photo/")
      && appels[1].headers["cache-control"] === "max-age=31536000",
      `${appels[1].url} ${JSON.stringify(appels[1].headers)}`);
  }

  fs.rmSync(dossierTmp, { recursive: true, force: true });
  console.log(`\n${echecs ? `⛔ ${echecs} controle(s) en echec` : "✅ tout passe"}\n`);
  process.exit(echecs ? 1 : 0);
})();
