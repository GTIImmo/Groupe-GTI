// UNE ADRESSE DE PHOTO PUBLIEE PEUT-ELLE DISPARAITRE ?                26/09/2026
//
// ⚠ POURQUOI CE FICHIER EXISTE. Le plan (G.10 -> G.15) va publier les photos a une
// adresse PERMANENTE, deduite de deux numeros de l'app :
//     gti-photo/{app_dossier_id}/{id de la ligne photo}/w1600.jpg
// Un portail la met en cache, un email l'integre, un client la garde en favori.
// ⚠⚠ P-1 de l'audit : UNE ADRESSE PUBLIEE NE CHANGE JAMAIS.
//
// Or cette adresse repose entierement sur l'id de la ligne app_console_photo. Cet id
// est un uuid tire a l'insertion : si la ligne est SUPPRIMEE puis recreee, l'id change
// et l'adresse publiee pointe dans le vide. La stabilite de l'adresse est donc la
// stabilite de la LIGNE, et c'est ce que ce fichier controle.
//
// Il fait tourner LA VRAIE fonction upsertConsolePhotos du worker, avec un faux
// Supabase. N'APPELLE RIEN : ni Hektor, ni le CDN, ni Supabase. N'ECRIT RIEN.

const fs = require("fs");
const path = require("path");

const WORKER = path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(WORKER, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

// ── on extrait la vraie fonction ──────────────────────────────────────────────
function tranche(marque) {
  const d = src.indexOf(marque);
  if (d < 0) return null;
  const f = src.indexOf("\n}", d);
  return f < 0 ? null : src.slice(d, f + 2);
}
const bloc = tranche("async function upsertConsolePhotos(");
if (!bloc || !/return rows;/.test(bloc)) {
  console.error("upsertConsolePhotos introuvable ou tranche incomplete -- test non concluant");
  process.exit(1);
}

// ── le faux Supabase : il enregistre ce qu'on lui demande ─────────────────────
function fauxSupabase(lignesExistantes) {
  const appels = [];
  const supabaseRequest = async (chemin, options = {}) => {
    appels.push({ chemin, methode: options.method, prefer: options.prefer || "",
                  corps: options.body ? JSON.parse(options.body) : null });
    if (options.method === "GET") return lignesExistantes;
    return null;
  };
  // eslint-disable-next-line no-new-func
  const fn = new Function("supabaseRequest", `${bloc}; return upsertConsolePhotos;`)(supabaseRequest);
  return { fn, appels };
}

const DOSSIER = { app_dossier_id: 4242, hektor_annonce_id: "63146" };
const photo = (id, hpid) => ({ id, hektor_photo_id: hpid });
const entree = (hpid) => ({ hektor_photo_id: hpid, filename: `${hpid}.jpg`, visible: true, sort_order: 1 });

const suppressions = (appels) => appels.filter((a) => a.methode === "DELETE");

(async () => {
  console.log("\nUNE ADRESSE DE PHOTO PUBLIEE PEUT-ELLE DISPARAITRE ?\n");

  // ── ce qui doit RESTER vrai : l'upsert porte sur le couple Hektor ───────────
  console.log("① la ligne survit a une synchronisation normale");
  {
    const { fn, appels } = fauxSupabase([photo("uuid-A", "111"), photo("uuid-B", "222")]);
    await fn(DOSSIER, [entree("111"), entree("222")]);
    const dep = appels.find((a) => a.methode === "POST");
    controle("(a) le depot se fait en upsert sur (annonce, photo Hektor)",
      dep && /on_conflict=hektor_annonce_id,hektor_photo_id/.test(dep.chemin),
      dep ? dep.chemin : "aucun depot");
    // ⚠ il ne suffit pas de viser le bon couple : il faut FUSIONNER. Un depot qui
    // remplacerait la ligne lui donnerait un id neuf, et l'adresse publiee tomberait.
    controle("(b) et il FUSIONNE (merge-duplicates) : la ligne garde son id, donc son adresse",
      dep && /merge-duplicates/.test(dep.prefer), dep ? `prefer = ${dep.prefer}` : "aucun depot");
    controle("(c) aucune suppression quand toutes les photos sont la",
      suppressions(appels).length === 0, JSON.stringify(suppressions(appels).map((a) => a.chemin)));
    controle("(d) les DEUX numeros de l'app sont ecrits",
      dep && dep.corps.every((r) => Number(r.app_dossier_id) === 4242 && r.hektor_annonce_id === "63146"),
      JSON.stringify(dep && dep.corps[0]));
  }

  // ── LE DEFAUT ① : une lecture vide efface TOUT ──────────────────────────────
  console.log("\n② ⚠ une lecture VIDE ne doit pas effacer l'annonce entiere");
  {
    const { fn, appels } = fauxSupabase([photo("uuid-A", "111"), photo("uuid-B", "222")]);
    await fn(DOSSIER, []);   // Hektor n'a rien rendu : accroc, lecture partielle, parse rate
    const sup = suppressions(appels);
    const efface = sup.length && /uuid-A/.test(sup[0].chemin) && /uuid-B/.test(sup[0].chemin);
    controle("(e) une liste vide n'emporte PAS les lignes existantes",
      !efface,
      `les 2 lignes sont supprimees -> 2 adresses publiees perdues : ${sup[0] && sup[0].chemin}`);
    controle("(f) et la garde doit etre SYMETRIQUE : rien depose -> rien supprime",
      !(appels.every((a) => a.methode !== "POST") && sup.length),
      "l'ajout est garde par if (rows.length), la suppression NON");
  }

  // ── LE DEFAUT ② : P-2, une photo retiree se MARQUE, ne se supprime pas ──────
  console.log("\n③ ⚠ P-2 : une photo retiree chez Hektor se MARQUE, elle ne se supprime pas");
  {
    const { fn, appels } = fauxSupabase([photo("uuid-A", "111"), photo("uuid-B", "222")]);
    await fn(DOSSIER, [entree("111")]);   // 222 a ete retiree chez Hektor
    const sup = suppressions(appels);
    controle("(g) la ligne de la photo retiree n'est pas supprimee",
      sup.length === 0,
      `supprimee -> son derive dans gti-photo devient orphelin : ${sup[0] && sup[0].chemin}`);
    const marque = appels.find((a) => a.methode === "PATCH");
    controle("(h) elle est marquee « plus dans Hektor » (delete-never, comme le ledger)",
      Boolean(marque), "aucun PATCH de marquage");
  }

  console.log(`\n${echecs ? `⛔ ${echecs} controle(s) en echec` : "✅ tout passe"}\n`);
  process.exit(echecs ? 1 : 0);
})();
