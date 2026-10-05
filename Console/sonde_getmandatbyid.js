// SONDE : getMandatById rend-il le mandat NEUF ou l'ANCIEN ?            05/10/2026
//
// L'ENJEU, pose par Frederic : « les 89 sont donc des id annonces identiques ? sinon
// il y a juste a recuperer par appel api sur idannonce ».
//
// Ce qu'on sait deja :
//    mandats(idAnnonce: ID!)   -> rend [] partout, meme sur les annonces saines
//    mandants(idAnnonce: ID!)  -> MARCHE, rend des [Prospect] (c'est ce qui a servi
//                                 a prouver que nos liens etaient justes)
//    getMandatById(idMandat: ID!) -> existe, mais l'identifiant est RECYCLE
//
// LA QUESTION DECISIVE : Hektor a-t-il DEUX enregistrements de mandat derriere
// l'identifiant 105 (le mandat de 2022 ET celui de 2026), ou UN SEUL ?
//    - s'il en a deux, le montant du mandat 2026 existe chez lui et est recuperable
//    - s'il n'en a qu'un, le montant du mandat 2026 n'existe NULLE PART : la fiche
//      annonce fabrique sa ligne avec le numero/les dates de l'annonce et le corps
//      du mandat 105. Il n'y a alors rien a aller chercher.
//
// Le cas : identifiant 105 = annonce 454 (num 14898, 2022, 62000, « Marie-Jose BANO »)
//                         ET annonce 39707 (num 18523, 2026, 62000, meme mandants)
//
// LECTURE SEULE. Que des query.
//   node Console/sonde_getmandatbyid.js [idMandat ...]
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr";
const ENDPOINT = `${BASE.replace(/\/+$/, "")}/ws/GraphQL_Web`;
const IDS = process.argv.slice(2).filter((x) => /^\d+$/.test(x));
const CIBLES = IDS.length ? IDS : ["105", "219", "760", "762"];

function jetonHektor() {
  const base = BASE.replace(/\/+$/, "");
  try {
    const st = path.resolve(__dirname, "storage_state.json");
    if (fs.existsSync(st)) {
      const state = JSON.parse(fs.readFileSync(st, "utf-8"));
      const o = (state.origins || []).find((x) => x.origin === base);
      const t = o && (o.localStorage || []).find((x) => x.name === "token");
      if (t && t.value) return t.value;
    }
  } catch (_) {}
  const dump = path.resolve(__dirname, "token_dump.json");
  if (fs.existsSync(dump)) {
    const d = JSON.parse(fs.readFileSync(dump, "utf-8"));
    if (d && d.localStorage && d.localStorage.token) return d.localStorage.token;
  }
  return null;
}

(async () => {
  const brut = jetonHektor();
  if (!brut) throw new Error("aucun jeton");
  const authorization = String(brut).startsWith("Bearer ") ? brut : `Bearer ${brut}`;

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: path.resolve(__dirname, "storage_state.json"),
  });
  const page = await context.newPage();
  await page.goto(`${BASE.replace(/\/+$/, "")}/admin/`, { waitUntil: "domcontentloaded" });

  async function demande(libelle, query) {
    const out = await page.evaluate(async ({ endpoint, authorization, query }) => {
      const res = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json", Authorization: authorization },
        body: JSON.stringify({ query, variables: {} }),
      });
      return { status: res.status, text: (await res.text()).slice(0, 6000) };
    }, { endpoint: ENDPOINT, authorization, query });
    console.log("--- " + libelle + " ---");
    try {
      const p = JSON.parse(out.text);
      if (p.errors) console.log("   " + p.errors.map((e) => e.message).join("\n   ").slice(0, 700));
      if (p.data) console.log("   " + JSON.stringify(p.data).slice(0, 1200));
    } catch (_) {
      console.log("   non JSON : " + out.text.slice(0, 200));
    }
    console.log("");
  }

  // ① un champ a la fois : chaque erreur nomme les champs PROCHES du mien, et c'est
  //   la seule facon de lire un schema dont l'introspection est coupee.
  // Les champs du type HektorMandat, trouves par sondage :
  //    id · numero · montant · mandants · dateDebut · dateFin · type · note · user
  // ⭐ LA NOTE DU 25/08 : « Hektor n'attend pas un numero mais un couple
  //   <id>-<FAMILLE> -- 648-PROTEXA ou 9887-HEKTOR -- et une valeur amputee est
  //   IGNOREE SANS ERREUR ». Les mandats depuis mars 2026 sont PROTEXA, les anciens
  //   HEKTOR : l'identifiant nu est donc ambigu. On essaie les deux formes.
  for (const id of CIBLES) {
    for (const forme of [id, `${id}-PROTEXA`, `${id}-HEKTOR`]) {
      await demande(`getMandatById("${forme}")`,
        `query { getMandatById(idMandat: "${forme}") { id numero type dateDebut dateFin montant mandants } }`);
    }
  }
  await browser.close();
})().catch((e) => {
  console.error("ECHEC :", e.message);
  process.exit(1);
});
