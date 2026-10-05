// INTROSPECTION : le schema GraphQL de Hektor expose-t-il une liste de MANDATS ?
//                                                                      05/10/2026
// POURQUOI. Les mandats ne sont recuperes que par `AnnonceById.mandats`, donc par
// l'ANNONCE -- et c'est cette jointure que Hektor rate : 91 mandats portent le
// corps (mandants + montant) d'un autre. Voir
// notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md et
// phase2/checks/mandat_corps_recopie.py.
//
// On cherche une porte qui prenne le NUMERO DE MANDAT, pas l'annonce. L'export
// xlsx « liste mandat » que le projet sait deja lire (manual_mandat_corrections.py)
// porte des noms de CHAMPS D'API (mandate_number, linked_product_ref, exclusivity,
// fees, product_recap) : cette porte existe donc probablement.
//
// LECTURE SEULE. Aucune mutation, aucune ecriture. Reutilise la session du worker.
//   node Console/introspect_mandats_query.js
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr";

// Le jeton, exactement comme le worker le lit (hektorGraphQLAuthorizationHeader) :
// localStorage « token » de storage_state.json pour l'origine Hektor, sinon
// token_dump.json. L'endpoint refuse l'appel sans en-tete Authorization, meme avec
// les cookies ("Missing HTTP_AUTHORIZATION in your request headers").
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
const ENDPOINT = `${BASE.replace(/\/+$/, "")}/ws/GraphQL_Web`;

// On ne demande QUE les noms et les arguments des champs de Query : le schema
// entier peserait des megaoctets pour rien.
const QUERY = `query I {
  __schema {
    queryType {
      fields {
        name
        args { name type { name kind ofType { name kind } } }
        type { name kind ofType { name kind } }
      }
    }
  }
}`;

(async () => {
  const storageState = path.resolve(__dirname, "storage_state.json");
  if (!fs.existsSync(storageState)) {
    throw new Error(`Session console introuvable: ${storageState}`);
  }
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ storageState });
  const page = await context.newPage();
  // Le referer /admin/ fait partie des en-tetes que le worker envoie (voir
  // Console/debug_graphql_headers.json) : on passe par la page pour les avoir.
  await page.goto(`${BASE.replace(/\/+$/, "")}/admin/`, { waitUntil: "domcontentloaded" });

  const jeton = jetonHektor();
  if (!jeton) throw new Error("aucun jeton : ni storage_state.json ni token_dump.json");
  console.log("jeton lu dans", jeton.source);
  const authorization = String(jeton.valeur).startsWith("Bearer ") ? jeton.valeur : `Bearer ${jeton.valeur}`;

  const out = await page.evaluate(async ({ endpoint, query, authorization }) => {
    const res = await fetch(endpoint, {
      method: "POST",
      credentials: "include",
      headers: { "content-type": "application/json", Authorization: authorization },
      body: JSON.stringify({ operationName: "I", query, variables: {} }),
    });
    return { status: res.status, text: (await res.text()).slice(0, 400000) };
  }, { endpoint: ENDPOINT, query: QUERY, authorization });

  console.log("HTTP", out.status);
  if (out.status !== 200) console.log("CORPS :", out.text.slice(0, 600));
  let payload;
  try {
    payload = JSON.parse(out.text);
  } catch (e) {
    console.log("reponse non JSON (debut) :", out.text.slice(0, 300));
    await browser.close();
    return;
  }
  if (payload.errors) {
    // L'introspection est souvent coupee en production. Ce n'est pas un echec de
    // la question : c'est une reponse, et elle dit « passe par l'ecran ».
    console.log("ERREURS :", payload.errors.map((e) => e.message).join(" | ").slice(0, 400));
    await browser.close();
    return;
  }
  const fields = (((payload.data || {}).__schema || {}).queryType || {}).fields || [];
  console.log("champs de Query :", fields.length);
  const interessants = fields.filter((f) =>
    /mandat|mandate/i.test(f.name) || (f.args || []).some((a) => /mandat|mandate|numero|number/i.test(a.name)));
  console.log("");
  console.log("=== ceux qui parlent de MANDAT ===");
  for (const f of interessants) {
    const t = f.type && (f.type.name || (f.type.ofType && f.type.ofType.name)) || f.type && f.type.kind;
    console.log(`   ${f.name}(${(f.args || []).map((a) => a.name).join(", ")}) -> ${t}`);
  }
  if (!interessants.length) console.log("   AUCUN");
  console.log("");
  console.log("=== tous les champs de Query, pour memoire ===");
  console.log("   " + fields.map((f) => f.name).sort().join(", "));
  await browser.close();
})().catch((e) => {
  console.error("ECHEC :", e.message);
  process.exit(1);
});
