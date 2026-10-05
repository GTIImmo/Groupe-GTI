// SONDE : `rechercheMandants` -- une porte qui prendrait le NUMERO ?       05/10/2026
//
// L'ENJEU, pose par Frederic : « Hektor nous retourne bien le numero de mandat en
// plus de l'id mandat, donc on peut bien retrouver ? »
//
// Le numero QUE NOUS AVONS est le bon (18523 pour l'annonce 39707). Ce qui est faux,
// c'est le CORPS que Hektor attache, parce que son POINTEUR (id 105) designe un vieux
// mandat. Si une requete acceptait le NUMERO, on retrouverait le vrai mandat.
//
// Deja elimine : getMandatByNumero, mandatByNumero, mandatsByNumero, mandatsListing,
// getMandats, allMandats -> « Cannot query field ». Et mandats(idAnnonce) rend [].
// Reste `rechercheMandants`, qui repond SANS erreur, et `lastMandants(idUser)`.
//
// LECTURE SEULE. Que des query.
//   node Console/sonde_recherche_mandants.js
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr";
const ENDPOINT = `${BASE.replace(/\/+$/, "")}/ws/GraphQL_Web`;

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
        method: "POST", credentials: "include",
        headers: { "content-type": "application/json", Authorization: authorization },
        body: JSON.stringify({ query, variables: {} }),
      });
      return { status: res.status, text: (await res.text()).slice(0, 5000) };
    }, { endpoint: ENDPOINT, authorization, query });
    console.log("--- " + libelle + " ---");
    try {
      const p = JSON.parse(out.text);
      if (p.errors) console.log("   ERR " + p.errors.map((e) => e.message).join(" | ").slice(0, 500));
      if (p.data) console.log("   " + JSON.stringify(p.data).slice(0, 900));
    } catch (_) { console.log("   non JSON : " + out.text.slice(0, 200)); }
    console.log("");
  }

  // ① rechercheMandants : quels arguments, quels champs ?
  await demande("rechercheMandants { __typename }", `query { rechercheMandants { __typename } }`);
  await demande("rechercheMandants -- champs", `query { rechercheMandants { zzz } }`);
  await demande("rechercheMandants(numero)", `query { rechercheMandants(numero: "18523") { __typename } }`);
  await demande("rechercheMandants(search)", `query { rechercheMandants(search: "18523") { __typename } }`);

  // ② le VRAI mandat 2026 existe-t-il sous un identifiant HAUT ?
  //   Un mandat de 2026 dont NOTRE miroir porte un id >= 30000 : si l'API rend le
  //   meme numero, alors les enregistrements de 2026 existent bel et bien.
  for (const id of ["79720", "79673", "70410"]) {
    await demande(`getMandatById(${id})`,
      `query { getMandatById(idMandat: ${id}) { id numero type dateDebut montant mandants } }`);
  }
  await browser.close();
})().catch((e) => { console.error("ECHEC :", e.message); process.exit(1); });
