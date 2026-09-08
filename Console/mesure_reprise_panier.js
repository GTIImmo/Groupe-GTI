/**
 * MESURE (2/2) — OU VIT L'IDENTITE DE LA REPRISE ?      08/09/2026, tache 3.2
 * ═════════════════════════════════════════════════════════════════════════════
 * La premiere mesure a rendu un resultat que je n'attendais pas : AVEC et SANS
 * `idCompromis`, le formulaire revient IDENTIQUE -- 44 146 caracteres des deux
 * cotes, memes valeurs. Hektor pre-remplit a partir du compromis en cours de
 * l'annonce, que l'on nomme celui-ci ou non.
 *
 * MAIS LES PANIERS DIFFERENT : 708 caracteres contre 646. C'est le seul endroit
 * ou la reprise laisse une trace -- et c'est aussi ce que le worker RENVOIE a
 * chaque etape (`corps.set("basket", etat.basket)`). Si l'identifiant y est,
 * alors notre correctif fait bien voyager la reprise jusqu'a l'enregistrement.
 *
 * ⚠ LECTURE SEULE, comme la premiere : on s'arrete a l'ouverture.
 */
const fs = require("fs");
const path = require("path");

// ─── GENERALISE A LA VENTE, 08/09 au soir ───
// La question posee au compromis se pose aussi a la vente, et la reponse n'est
// PAS forcement la meme : 0.2 (03/09) a capture leur interface postant `idVente`
// A CHAQUE ETAPE, ce qui laisse penser que le panier de la vente ne le retient
// peut-etre pas. Si le panier differe, il le retient ; sinon, l'identifiant doit
// voyager a la main -- et c'est ce qui separerait modifier de CREER UNE SECONDE
// VENTE sur un dossier reel.
//   node Console/mesure_reprise_panier.js [genre] [idAnnonce] [idTransaction]
const GENRE = String(process.argv[2] || "compromis").toLowerCase();
const ANNONCE = String(process.argv[3] || "24933");
const COMPROMIS = String(process.argv[4] || "50078");
const BASE = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${BASE.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const GENRES = {
  compromis: { coquille: "annonce-SuiviVente-compromis-createCompromis",
               etape: "annonce-SuiviVente-compromis-getStepCompromis", cle: "idCompromis" },
  vente:     { coquille: "annonce-SuiviVente-vente-createVente",
               etape: "annonce-SuiviVente-vente-getStepVente", cle: "idVente" },
};
const G = GENRES[GENRE];
if (!G) { console.error("genre inconnu : " + GENRE); process.exit(1); }
const COQUILLE = G.coquille;
const ETAPE = G.etape;
const SESSION = path.resolve(__dirname, "sessions", "storage_state_admin.json");

const etat = JSON.parse(fs.readFileSync(SESSION, "utf8"));
const maintenant = Date.now() / 1000;
const cookies = (etat.cookies || [])
  .filter((c) => !c.expires || c.expires < 0 || c.expires > maintenant)
  .map((c) => `${c.name}=${c.value}`).join("; ");

async function panier(avec) {
  const entetes = {
    Cookie: cookies,
    Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(ANNONCE)}`,
    Accept: "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Mozilla/5.0",
  };
  await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(COQUILLE)}`, { headers: entetes });
  const corps = new URLSearchParams();
  corps.set("idAnnonce", ANNONCE);
  if (avec) corps.set(G.cle, COMPROMIS);
  corps.set("basket", "");
  corps.set("initBasket", "true");
  const rep = await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(ETAPE)}`, {
    method: "POST", body: corps,
    headers: { ...entetes, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
  });
  const j = JSON.parse(await rep.text());
  return String((j.data && j.data.basket) || "");
}

function lisible(b) {
  // Le panier est serialise. On tente les formes usuelles, sans rien forcer.
  try { return JSON.stringify(JSON.parse(b), null, 1); } catch (_) {}
  try {
    const d = Buffer.from(b, "base64").toString("utf8");
    if (/[{[]/.test(d)) { try { return JSON.stringify(JSON.parse(d), null, 1); } catch (_) { return d; } }
    return d;
  } catch (_) {}
  return b;
}

(async () => {
  const avec = await panier(true);
  await new Promise((r) => setTimeout(r, 1500));
  const sans = await panier(false);

  const sorties = path.resolve(__dirname, "exports", "mesure_reprise");
  fs.mkdirSync(sorties, { recursive: true });
  fs.writeFileSync(path.join(sorties, "panier_avec.txt"), lisible(avec), "utf8");
  fs.writeFileSync(path.join(sorties, "panier_sans.txt"), lisible(sans), "utf8");

  console.log(`GENRE ${GENRE.toUpperCase()} · annonce ${ANNONCE} · transaction ${COMPROMIS}`);
  console.log("⚠ LECTURE SEULE : on s'arrete a l'ouverture, rien n'est enregistre.");
  console.log("");
  console.log(`panier AVEC : ${avec.length} car.`);
  console.log(`panier SANS : ${sans.length} car.`);
  console.log("");
  const la = lisible(avec); const ls = lisible(sans);
  console.log("--- LE PANIER DE LA REPRISE, EN CLAIR ---");
  console.log(la.slice(0, 1600));
  console.log("");
  console.log(`--- L'IDENTIFIANT ${COMPROMIS} Y EST-IL ? ---`);
  console.log(`   avec : ${la.includes(COMPROMIS) ? "OUI" : "non"}`);
  console.log(`   sans : ${ls.includes(COMPROMIS) ? "OUI" : "non"}`);
  console.log("");
  console.log("--- LES LIGNES QUI DIFFERENT ---");
  const A = la.split(/\r?\n/); const S = new Set(ls.split(/\r?\n/));
  const seulesAvec = A.filter((l) => !S.has(l));
  const Sa = new Set(A);
  const seulesSans = ls.split(/\r?\n/).filter((l) => !Sa.has(l));
  console.log(`   seulement AVEC (${seulesAvec.length}) :`);
  seulesAvec.slice(0, 25).forEach((l) => console.log(`      ${l.trim().slice(0, 140)}`));
  console.log(`   seulement SANS (${seulesSans.length}) :`);
  seulesSans.slice(0, 25).forEach((l) => console.log(`      ${l.trim().slice(0, 140)}`));
})().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
