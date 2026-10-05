// SONDE : que rend `mandants(idAnnonce)` -- la requete DEDIEE aux mandants ?  05/10/2026
//
// Trouvee en sondant le schema (l'introspection est coupee, le serveur nomme ses
// champs dans ses messages d'erreur) :
//     mandats(idAnnonce: ID!)        <- le bloc mandat, celui dont le CORPS est faux
//     mandants(idAnnonce: ID!)       <- une requete A PART, pour les mandants
//     getMandatById(idMandat: ID!)   <- par l'identifiant RECYCLE, donc inutile ici
//
// L'ENJEU. Le registre tient 91 mandats dont les mandants et le montant viennent
// d'une AUTRE annonce, parce que Hektor joint par son identifiant de mandat, qu'il
// recycle. Si `mandants(idAnnonce)` rend les mandants SANS passer par cette
// jointure, elle est la bonne porte -- et c'est un appel d'API, pas un export.
// Voir notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md.
//
// Le cas d'epreuve : annonce 39707. Le bloc mandat dit « Marie-Jose BANO »
// (proprietaire de l'annonce 454) ; les proprietaires de 39707 sont SOUVIGNET.
//
// LECTURE SEULE. Deux `query`, aucune mutation.
//   node Console/sonde_mandants_annonce.js [idAnnonce]
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr";
const ENDPOINT = `${BASE.replace(/\/+$/, "")}/ws/GraphQL_Web`;
const ID = String(process.argv[2] || "39707");

function jetonHektor() {
  const base = BASE.replace(/\/+$/, "");
  try {
    const st = path.resolve(__dirname, "storage_state.json");
    if (fs.existsSync(st)) {
      const state = JSON.parse(fs.readFileSync(st, "utf-8"));
      const o = (state.origins || []).find((x) => x.origin === base);
      const t = o && (o.localStorage || []).find((x) => x.name === "token");
      if (t && t.value) return { source: "storage_state.json", valeur: t.value };
    }
  } catch (_) {}
  const dump = path.resolve(__dirname, "token_dump.json");
  if (fs.existsSync(dump)) {
    const d = JSON.parse(fs.readFileSync(dump, "utf-8"));
    const t = d && d.localStorage ? d.localStorage.token : null;
    if (t) return { source: "token_dump.json", valeur: t };
  }
  return null;
}

(async () => {
  const jeton = jetonHektor();
  if (!jeton) throw new Error("aucun jeton");
  const authorization = String(jeton.valeur).startsWith("Bearer ")
    ? jeton.valeur : `Bearer ${jeton.valeur}`;

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
      return { status: res.status, text: (await res.text()).slice(0, 8000) };
    }, { endpoint: ENDPOINT, authorization, query });
    console.log("--- " + libelle + " ---");
    try {
      const p = JSON.parse(out.text);
      if (p.errors) console.log("   " + p.errors.map((e) => e.message).join("\n   ").slice(0, 900));
      if (p.data) console.log("   " + JSON.stringify(p.data, null, 1).slice(0, 2500));
    } catch (_) {
      console.log("   non JSON : " + out.text.slice(0, 300));
    }
    console.log("");
  }

  // ① La forme du type : sans sous-selection valide, le serveur ENUMERE ses champs.
  await demande(`mandants(idAnnonce: ${ID}) -- forme du type`,
    `query { mandants(idAnnonce: ${ID}) { __typename } }`);

  // ② Les champs du type Prospect : une sous-selection fausse fait enumerer.
  await demande(`mandants -- quels champs ?`,
    `query { mandants(idAnnonce: ${ID}) { zzz_champ_inexistant } }`);

  // ③ L'identite des mandants, telle que Hektor la rend.
  await demande(`mandants -- identite`,
    `query { mandants(idAnnonce: ${ID}) { id nom prenom civilite } }`);

  // ④ Le bloc mandat, pour comparer les deux sources.
  await demande(`mandats(idAnnonce: ${ID})`,
    `query { mandats(idAnnonce: ${ID}) { __typename } }`);

  await browser.close();
})().catch((e) => {
  console.error("ECHEC :", e.message);
  process.exit(1);
});
