// `mandants(idAnnonce)` de Hektor contre NOTRE registre des liens.        05/10/2026
//
// CE QUE CETTE SONDE ETABLIT. Le registre des mandats affiche, depuis le 05/10, les
// mandants que NOTRE registre des liens connait, a la place du texte figé que Hektor
// colle dans le bloc mandat -- texte faux sur 91 mandats (il porte le corps d'un
// autre, voir notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md).
//
// En sondant le schema (introspection coupee, le serveur nomme ses champs dans ses
// erreurs) on a trouve une requete DEDIEE :
//     mandants(idAnnonce: ID!) -> [Prospect]   avec id, nom, prenom, civilite
// Elle ne passe PAS par l'identifiant de mandat recycle. C'est donc l'arbitre.
//
// Sur l'annonce 39707 elle rend SOUVIGNET (133818, 325798, 482358) -- nos liens --
// et non BANO (le bloc mandat). Cette sonde verifie si l'accord tient en general.
//
// LECTURE SEULE. Une `query` par annonce, aucune mutation.
//   node Console/comparer_mandants_api_vs_liens.js 39707 61650 62928 ...
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr";
const ENDPOINT = `${BASE.replace(/\/+$/, "")}/ws/GraphQL_Web`;
const IDS = process.argv.slice(2).filter((x) => /^\d+$/.test(x));

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
  if (!IDS.length) throw new Error("donner au moins un idAnnonce");
  const brut = jetonHektor();
  if (!brut) throw new Error("aucun jeton");
  const authorization = String(brut).startsWith("Bearer ") ? brut : `Bearer ${brut}`;

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: path.resolve(__dirname, "storage_state.json"),
  });
  const page = await context.newPage();
  await page.goto(`${BASE.replace(/\/+$/, "")}/admin/`, { waitUntil: "domcontentloaded" });

  const resultat = {};
  for (const id of IDS) {
    const out = await page.evaluate(async ({ endpoint, authorization, id }) => {
      const res = await fetch(endpoint, {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json", Authorization: authorization },
        body: JSON.stringify({
          query: `query { mandants(idAnnonce: ${id}) { id nom prenom civilite } }`,
          variables: {},
        }),
      });
      return { status: res.status, text: (await res.text()).slice(0, 6000) };
    }, { endpoint: ENDPOINT, authorization, id });
    try {
      const p = JSON.parse(out.text);
      resultat[id] = p.errors
        ? { erreur: p.errors.map((e) => e.message).join(" | ") }
        : { mandants: (p.data && p.data.mandants) || [] };
    } catch (_) {
      resultat[id] = { erreur: "reponse non JSON" };
    }
  }
  await browser.close();
  // On ecrit a cote, pour que la comparaison avec nos liens se fasse en Python.
  const sortie = path.resolve(__dirname, "exports", "mandants_api.json");
  fs.mkdirSync(path.dirname(sortie), { recursive: true });
  fs.writeFileSync(sortie, JSON.stringify(resultat, null, 1), "utf-8");
  console.log(JSON.stringify(resultat, null, 1));
  console.log("ecrit dans", sortie);
})().catch((e) => {
  console.error("ECHEC :", e.message);
  process.exit(1);
});
