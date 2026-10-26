#!/usr/bin/env node
"use strict";
/**
 * ⑧ §58 POINT 6 n° 3 — LE COMPROMIS NEUF REPREND LE MONTANT ET L'ACQUEREUR DE L'OFFRE ACCEPTEE.   26/10/2026
 *
 * On EXECUTE le code reel : offreAccepteeAReprendreAuCompromis (qui designe l'offre) et lireMandantsAffaire
 * (qui lit son acquereur) sont decoupees dans App.tsx et jouees par esbuild + vm, sur des lignes de la forme
 * du registre (app_affaire_ledger ; l'acquereur d'une offre est un OBJET seul, celui d'un compromis une liste).
 * L'effet de la modale est verifie dans le source (ses gardes), puisqu'il vit dans le composant.
 *
 * ⚠ TEMOIN INVERSE : la modale d'avant (parent du commit) ne reprenait rien -- l'effet et la fonction y sont absents,
 *   et la valeur proposee etait le prix du mandat. MUTANTS : prendre la premiere offre vivante (et non
 *   l'acceptee) ; ignorer le dossier ouvert ; ignorer un compromis deja vivant -- chacun doit etre attrape.
 *
 * NE LANCE NI SERVEUR NI REQUETE.
 *     node apps/hektor-v1/test_heritage_compromis_offre.cjs
 *     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}
function ligne(src, debut) {
  const i = src.indexOf(debut);
  return i < 0 ? null : src.slice(i, src.indexOf("\n", i));
}

function monter(s, remplacer) {
  const morceaux = [];
  for (const c of ["const AFFAIRE_ETAT_MORT", "const AFFAIRE_ETATS_ACCEPTES"]) {
    const t = ligne(s, c);
    if (!t) return { erreur: `constante absente : ${c}` };
    morceaux.push(t);
  }
  for (const f of ["function affaireEstVivante(", "function dossiersOuvertsDuBien(",
                   "function offreAccepteeAReprendreAuCompromis(", "function lireMandantsAffaire("]) {
    let t = tranche(s, f);
    if (!t) return { erreur: `fonction absente : ${f}` };
    if (remplacer && remplacer[f]) {
      const [a, b] = remplacer[f];
      if (!t.includes(a)) return { erreur: `mutant impossible a poser dans ${f}` };
      t = t.replace(a, b);
    }
    morceaux.push(t);
  }
  const code = morceaux.join("\n\n") + "\nthis.api = { offreAccepteeAReprendreAuCompromis, lireMandantsAffaire };";
  const js = esbuild.transformSync(code, { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api };
}

// La version d'AVANT la correction : le parent du commit qui a introduit `marque` (HEAD tant qu'il n'est pas
// committe). Lire HEAD tout court casse le temoin des que la correction est committee (vu le 27/10).
function versionAvant(marque) {
  const h = execFileSync("git", ["log", "--format=%H", "-S", marque, "--", ":(top)apps/hektor-v1/src/App.tsx"],
    { cwd: __dirname, encoding: "utf8" }).trim().split(/\s+/).filter(Boolean).pop();
  return execFileSync("git", ["show", `${h ? h + "^" : "HEAD"}:apps/hektor-v1/src/App.tsx`],
    { cwd: __dirname, encoding: "utf8", maxBuffer: 64 << 20 });
}

let src, ancien;
try {
  src = fs.readFileSync(APP, "utf8").replace(/\r\n/g, "\n");
  ancien = versionAvant("function offreAccepteeAReprendreAuCompromis(").replace(/\r\n/g, "\n");
} catch (e) {
  console.log("IMPOSSIBLE de lire App.tsx ou git HEAD : " + e.message);
  process.exit(2);
}

// ─── Les lignes du registre ───
let n = 1000;
const L = (kind, state, chaine, extra = {}) => ({
  app_affaire_id: ++n, kind, state, app_chaine_id: chaine, hektor_affaire_id: String(30000 + n),
  present_in_hektor: true, montant: null, acquereurs_json: null, ...extra,
});
const acheteurA = { id: "605967", app_contact_id: 20000012, civilite: "Mme", prenom: "Alice", nom: "ESSAI" };
const acheteurB = { id: "605968", civilite: "M.", prenom: "Bruno", nom: "ESSAI" };

const cas = {
  // l'offre acceptee A (80 000) et l'ecartee B (78 000), chacune sa chaine ; B listee D'ABORD (mutant 1)
  engage_par_offre: [
    L("offre", "proposed", 501, { montant: "78000.00", acquereurs_json: acheteurB }),
    L("offre", "accepted", 502, { montant: "80000.00", acquereurs_json: acheteurA }),
  ],
  deux_acceptees: [
    L("offre", "accepted", 511, { montant: "80000.00", acquereurs_json: acheteurA }),
    L("offre", "accepted", 512, { montant: "79000.00", acquereurs_json: acheteurB }),
  ],
  // un compromis vit deja sur la chaine de l'offre : la modale le vise, on ne reprend rien (mutant 3)
  compromis_deja_la: [
    L("offre", "accepted", 521, { montant: "80000.00", acquereurs_json: acheteurA }),
    L("compromis", "active", 521, { montant: "80000.00", acquereurs_json: [acheteurA] }),
  ],
  // bien revendu : l'ancienne chaine est close par sa vente ; la nouvelle n'a qu'une offre proposee (mutant 2)
  revendu: [
    L("offre", "accepted", 531, { montant: "150000.00", acquereurs_json: acheteurB }),
    L("compromis", "active", 531, { montant: "150000.00" }),
    L("vente", null, 531, { montant: "150000.00" }),
    L("offre", "proposed", 532, { montant: "170000.00", acquereurs_json: acheteurA }),
  ],
  // revendu SANS compromis : offre acceptee puis vente directe sur l'ancienne chaine (mutant 2 -- dans « revendu »
  // le compromis vivant de l'ancienne chaine masquait le dossier clos)
  revendu_vente_directe: [
    L("offre", "accepted", 581, { montant: "150000.00", acquereurs_json: acheteurB }),
    L("vente", null, 581, { montant: "150000.00" }),
    L("offre", "proposed", 582, { montant: "170000.00", acquereurs_json: acheteurA }),
  ],
  // l'offre acceptee a ete effacee chez Hektor (numero + present_in_hektor = false)
  effacee: [L("offre", "accepted", 541, { montant: "80000.00", acquereurs_json: acheteurA, present_in_hektor: false })],
  // aucune offre acceptee : vente directe ou compromis sans offre -> on ne devine pas
  sans_acceptee: [L("offre", "proposed", 551, { montant: "80000.00", acquereurs_json: acheteurA })],
  // le dossier clos par une vente ANNULEE est rouvert (regle de l'heritage de la vente)
  vente_morte: [
    L("offre", "accepted", 561, { montant: "80000.00", acquereurs_json: acheteurA }),
    L("vente", "cancelled", 561, { montant: "80000.00" }),
  ],
  // une offre refusee + une acceptee : on prend l'acceptee
  refusee_et_acceptee: [
    L("offre", "refused", 571, { montant: "75000.00", acquereurs_json: acheteurB }),
    L("offre", "accepted", 572, { montant: "80000.00", acquereurs_json: acheteurA }),
  ],
};
const attendu = {
  engage_par_offre: "80000.00", deux_acceptees: null, compromis_deja_la: null, revendu: null, revendu_vente_directe: null,
  effacee: null, sans_acceptee: null, vente_morte: "80000.00", refusee_et_acceptee: "80000.00",
};

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "OK   " : "ECHEC"} ${nom}${ok ? "" : "  -> " + detail}`);
  if (!ok) echecs++;
}
const jouer = (api) => Object.fromEntries(Object.entries(cas).map(([k, lignes]) => {
  const o = api.offreAccepteeAReprendreAuCompromis(lignes);
  return [k, o ? String(o.montant) : null];
}));

const m = monter(src);
if (m.erreur) { console.log(m.erreur); process.exit(2); }
const vu = jouer(m.api);
for (const k of Object.keys(cas)) {
  verifier(`l'offre reprise -- ${k} = ${attendu[k] ?? "aucune"}`, vu[k] === attendu[k], `obtenu ${vu[k]}`);
}

// l'acquereur de l'offre : un OBJET seul, lu comme une liste d'un, NOTRE numero d'abord
const offreA = m.api.offreAccepteeAReprendreAuCompromis(cas.engage_par_offre);
const acq = offreA ? m.api.lireMandantsAffaire(offreA.acquereurs_json) : [];
verifier("l'acquereur de l'offre (objet seul) est lu", acq.length === 1, JSON.stringify(acq));
verifier("il part sous NOTRE numero (20000012)", acq[0] && (acq[0].app || acq[0].id) === "20000012", JSON.stringify(acq[0]));
verifier("son nom est lisible", acq[0] && acq[0].nom === "Mme Alice ESSAI", acq[0] && acq[0].nom);

// ─── L'effet de la modale : ses gardes, dans le source ───
const effet = (() => {
  const i = src.indexOf("LE COMPROMIS NEUF REPREND LE MONTANT ET L'ACQUEREUR DE L'OFFRE ACCEPTEE");
  return i < 0 ? "" : src.slice(i, src.indexOf("}, [statusChangeAffaires, statusChangeStatus, carnetAffaires])", i) + 70);
})();
const gardes = [
  ["seulement sur l'onglet Compromis", "if (statusChangeStatus !== 'compromise') return"],
  ["seulement a la creation", "if (affaireCourantePourStatut()) return"],
  ["la regle unique designe l'offre", "offreAccepteeAReprendreAuCompromis(statusChangeAffaires)"],
  ["le carnet de l'offre prime", "String(carnet.montant ?? '').trim() || String(offre.montant ?? '').trim()"],
  ["jamais par-dessus un montant touche", "!statusChangeTouches.includes('amount') && !statusChangeTouches.includes('sale_price')"],
  ["le montant va dans les deux cases", "setStatusChangeAmount(montant)\n      setStatusChangeSalePrice(montant)"],
  ["jamais par-dessus une liste touchee", "acquereurs.length && !statusChangeAcquereursAffirmes"],
  ["jamais par-dessus une liste remplie", "if (deja.length) return deja"],
  ["les cases touchees ne relancent pas l'effet", "}, [statusChangeAffaires, statusChangeStatus, carnetAffaires])"],
];
verifier("l'effet existe dans la modale", effet.length > 0, "absent");
for (const [nom, morceau] of gardes) verifier(`garde : ${nom}`, effet.includes(morceau), "absente");
verifier("l'effet ne leve aucun drapeau « affirme »", !/setStatusChange\w*Affirmes\(/.test(effet), "un drapeau est leve");

// ─── TEMOIN INVERSE : la modale d'avant ne reprenait rien ───
verifier("TEMOIN : avant, ni ni la regle ni l'effet",
  !ancien.includes("function offreAccepteeAReprendreAuCompromis(")
  && !ancien.includes("LE COMPROMIS NEUF REPREND LE MONTANT"), "deja present dans HEAD");
verifier("TEMOIN : avant, la modale ouvrait la modale sur le prix du mandat, liste vide",
  ancien.includes("setStatusChangeAmount(price)\n    setStatusChangeSalePrice(price)")
  && ancien.includes("setStatusChangeBuyers([])            // 2.6"), "ouverture differente");

// ─── MUTANTS ───
const F = "function offreAccepteeAReprendreAuCompromis(";
const mutants = [
  ["la premiere offre vivante, acceptee ou non",
    { [F]: ["&& AFFAIRE_ETATS_ACCEPTES.has(String(a.state ?? '').trim().toLowerCase()) && ouverts.has(cleDe(a))", "&& ouverts.has(cleDe(a))"] }],
  ["le dossier ouvert ignore",
    { [F]: ["&& ouverts.has(cleDe(a)))", ")"] }],
  ["un compromis deja vivant ignore",
    { [F]: ["if (lignes.some((a) => String(a.kind) === 'compromis' && affaireEstVivante(a) && cleDe(a) === chaine)) return null", ""] }],
  ["deux acceptees : la premiere au hasard",
    { [F]: ["if (offres.length !== 1) return null", "if (!offres.length) return null"] }],
];
for (const [nom, rempl] of mutants) {
  const mm = monter(src, rempl);
  if (mm.erreur) { verifier(`MUTANT ${nom}`, false, mm.erreur); continue; }
  const v = jouer(mm.api);
  const attrape = Object.keys(cas).some((k) => v[k] !== attendu[k]);
  verifier(`MUTANT attrape : ${nom}`, attrape, "le mutant passe tous les cas");
}

console.log(echecs ? `\n${echecs} controle(s) en echec` : "\ntout vert");
process.exit(echecs ? 1 : 0);
