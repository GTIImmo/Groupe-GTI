// SONDE : trouver la requete GraphQL qui rend les MANDATS par leur numero. 05/10/2026
//
// L'introspection est coupee chez Hektor (« GraphQL introspection is not allowed »),
// mais un serveur GraphQL nomme souvent le bon champ dans son message d'erreur
// (« Cannot query field X ... Did you mean Y ? »). On lui demande donc des champs
// plausibles, un par un, et on lit ce qu'il repond.
//
// POURQUOI on cherche cette porte : les mandats ne sont lus que par
// `AnnonceById.mandats`, donc par l'ANNONCE, et c'est cette jointure que Hektor
// rate -- 91 mandats portent le corps d'un autre (mandants + montant). Voir
// notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md.
//
// LECTURE SEULE : que des `query`, jamais de mutation, et on ne demande qu'un
// seul champ `id` pour ne rien charger.
//   node Console/sonde_mandats_graphql.js
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr";
const ENDPOINT = `${BASE.replace(/\/+$/, "")}/ws/GraphQL_Web`;

// Les noms plausibles, du plus au moins probable. `properties` existe (le worker
// l'utilise), il sert de temoin : si lui repond autre chose qu'une erreur de nom,
// la sonde fonctionne.
const CANDIDATS = (process.env.SONDE_NOMS || [
  "properties",
  "mandates", "mandats", "mandate", "mandat",
  "mandateListing", "mandatesListing", "mandateList",
  "mandateById", "mandatById", "mandateByNumber",
  "contracts", "contract",
].join(",")).split(",").map((x) => x.trim()).filter(Boolean);

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
  if (!jeton) throw new Error("aucun jeton : ni storage_state.json ni token_dump.json");
  console.log("jeton lu dans", jeton.source);
  const authorization = String(jeton.valeur).startsWith("Bearer ")
    ? jeton.valeur : `Bearer ${jeton.valeur}`;

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: path.resolve(__dirname, "storage_state.json"),
  });
  const page = await context.newPage();
  await page.goto(`${BASE.replace(/\/+$/, "")}/admin/`, { waitUntil: "domcontentloaded" });

  for (const nom of CANDIDATS) {
    const out = await page.evaluate(async ({ endpoint, authorization, nom }) => {
      const res = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json", Authorization: authorization },
        body: JSON.stringify({ operationName: "S", query: `query S { ${nom} { __typename } }`, variables: {} }),
      });
      return { status: res.status, text: (await res.text()).slice(0, 1200) };
    }, { endpoint: ENDPOINT, authorization, nom });

    let msg = out.text;
    try {
      const p = JSON.parse(out.text);
      if (p.errors && p.errors.length) msg = p.errors.map((e) => e.message).join(" | ");
      else if (p.data) msg = "REPOND : " + JSON.stringify(p.data).slice(0, 160);
    } catch (_) {}
    // « Cannot query field » = le nom n'existe pas. Tout autre message (argument
    // manquant, sous-selection invalide) veut dire QUE LE CHAMP EXISTE.
    const inexistant = /Cannot query field/i.test(msg);
    console.log(`${inexistant ? "  -  " : "  *  "} ${nom.padEnd(18)} ${msg.slice(0, 180)}`);
  }
  await browser.close();
})().catch((e) => {
  console.error("ECHEC :", e.message);
  process.exit(1);
});
