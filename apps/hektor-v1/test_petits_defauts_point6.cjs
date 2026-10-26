#!/usr/bin/env node
"use strict";
/**
 * ⑧ §58 POINT 6 — LES PETITS DEFAUTS n° 1 et n° 6.   26/10/2026
 *
 *   n° 1  dateLocaleIso   l'echeance d'une condition, la date de cloture proposee par defaut et
 *                         « aujourd'hui » des relances prennent la date CALENDAIRE locale, plus
 *                         `toISOString().slice(0, 10)` (la date en UTC : la veille en France).
 *   n° 6  avisPlusieursAffaires  le bandeau « une offre acceptee + d'autres vivantes » ne dit plus
 *                         « Designe celle qui fait foi » (on ne peut plus que REFUSER l'ecartee,
 *                         point 5 n° 2) et accorde « Cette offre » / « Ces offres ».
 *
 * On EXECUTE le code reel : les fonctions sont decoupees dans App.tsx et jouees par esbuild + vm,
 * en heure de PARIS (l'essai se relance lui-meme avec TZ=Europe/Paris).
 * ⚠ TEMOIN INVERSE : l'ancienne formule et l'ancien bandeau (lus dans git HEAD) doivent ECHOUER.
 *   Un MUTANT (la date prise en UTC) doit etre attrape.
 *
 * NE LANCE NI SERVEUR NI REQUETE.
 *     node apps/hektor-v1/test_petits_defauts_point6.cjs
 *     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync, spawnSync } = require("child_process");

if (process.env.TZ !== "Europe/Paris") {
  const r = spawnSync(process.execPath, [__filename], { stdio: "inherit", env: { ...process.env, TZ: "Europe/Paris" } });
  process.exit(r.status == null ? 2 : r.status);
}
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

function monter(src, fonctions, constantes, exporte) {
  const s = src.replace(/\r\n/g, "\n");
  const morceaux = [];
  for (const c of constantes) {
    const t = tranche(s, c);
    if (!t) return { erreur: `constante absente : ${c}` };
    morceaux.push(t);
  }
  for (const f of fonctions) {
    const t = tranche(s, f);
    if (!t) return { erreur: `fonction absente : ${f}` };
    morceaux.push(t);
  }
  const code = morceaux.join("\n\n") + `\nthis.api = { ${exporte.join(", ")} };`;
  const js = esbuild.transformSync(code, { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, Date };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api };
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "OK   " : "ECHEC"} ${nom}${ok ? "" : "  -> " + detail}`);
  if (!ok) echecs++;
}

let src, ancien;
try {
  src = fs.readFileSync(APP, "utf8");
  ancien = execFileSync("git", ["show", "HEAD:apps/hektor-v1/src/App.tsx"], { cwd: __dirname, encoding: "utf8", maxBuffer: 64 << 20 });
} catch (e) {
  console.log("IMPOSSIBLE de lire App.tsx ou git HEAD : " + e.message);
  process.exit(2);
}

// ─── Le fuseau est bien celui de Paris (sinon l'essai ne prouve rien) ───
const decalage = new Date("2026-10-26T00:30:00").getTimezoneOffset();
if (decalage !== -60) {
  console.log(`le fuseau n'est pas Paris (decalage ${decalage}) : rien de mesurable`);
  process.exit(2);
}

// ═══ n° 1 : la date locale ═══
const m1 = monter(src, ["function dateLocaleIso("], [], ["dateLocaleIso"]);
if (m1.erreur) { console.log(m1.erreur); process.exit(2); }
const { dateLocaleIso } = m1.api;

// l'echeance : compromis du 26/10, condition a 45 jours, posee a minuit local comme echeanceCondition
function echeance(fmt, base, jours) {
  const quand = new Date(`${base}T00:00:00`);
  quand.setDate(quand.getDate() + jours);
  return fmt(quand);
}
const ancienneFormule = (d) => d.toISOString().slice(0, 10);
const mutantUtc = (d) => `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`;

const cas = [
  ["echeance 26/10 + 45 j (heure d'hiver)", () => echeance(dateLocaleIso, "2026-10-26", 45), "2026-12-10"],
  ["echeance 01/06 + 10 j (heure d'ete)", () => echeance(dateLocaleIso, "2026-06-01", 10), "2026-06-11"],
  ["echeance qui traverse le changement d'heure (24/10 + 3 j)", () => echeance(dateLocaleIso, "2026-10-24", 3), "2026-10-27"],
  ["« aujourd'hui » a 00:30 le 27/10", () => dateLocaleIso(new Date("2026-10-27T00:30:00")), "2026-10-27"],
  ["« aujourd'hui » a 23:30 le 26/10", () => dateLocaleIso(new Date("2026-10-26T23:30:00")), "2026-10-26"],
  ["« aujourd'hui » a 01:30 l'ete (15/07)", () => dateLocaleIso(new Date("2026-07-15T01:30:00")), "2026-07-15"],
];
for (const [nom, f, attendu] of cas) {
  const v = f();
  verifier(`n°1 ${nom} = ${attendu}`, v === attendu, `obtenu ${v}`);
}

// TEMOIN INVERSE : l'ancienne formule rendait la veille
verifier("n°1 TEMOIN : l'ancienne formule rendait la VEILLE pour l'echeance",
  echeance(ancienneFormule, "2026-10-26", 45) === "2026-12-09", echeance(ancienneFormule, "2026-10-26", 45));
verifier("n°1 TEMOIN : l'ancienne formule rendait la VEILLE a 00:30",
  ancienneFormule(new Date("2026-10-27T00:30:00")) === "2026-10-26", ancienneFormule(new Date("2026-10-27T00:30:00")));
verifier("n°1 TEMOIN : l'ancienne formule etait bien dans HEAD (3 fois)",
  (ancien.match(/toISOString\(\)\.slice\(0, 10\)/g) || []).length === 3, "compte different");
// MUTANT : la date prise en UTC est attrapee par au moins un cas
verifier("n°1 MUTANT (getUTC*) attrape",
  cas.some(([, , attendu], i) => {
    const essais = [() => echeance(mutantUtc, "2026-10-26", 45), () => echeance(mutantUtc, "2026-06-01", 10),
      () => echeance(mutantUtc, "2026-10-24", 3), () => mutantUtc(new Date("2026-10-27T00:30:00")),
      () => mutantUtc(new Date("2026-10-26T23:30:00")), () => mutantUtc(new Date("2026-07-15T01:30:00"))];
    return essais[i]() !== attendu;
  }), "le mutant passe partout");

// les trois endroits appellent la nouvelle fonction ; plus aucun toISOString().slice hors commentaire
const s = src.replace(/\r\n/g, "\n");
const corps = tranche(s, "  function echeanceCondition(") || "";
verifier("n°1 echeanceCondition rend dateLocaleIso(quand)", corps.includes("return dateLocaleIso(quand)"), "absent");
verifier("n°1 la date de cloture par defaut est locale",
  s.includes("useState(() => dateLocaleIso(new Date()))"), "absent");
verifier("n°1 « aujourd'hui » des relances est local",
  s.includes("const todayIso = dateLocaleIso(new Date())"), "absent");
const horsCommentaire = s.split("\n").filter((l) => l.includes("toISOString().slice(0, 10)") && !/^\s*\*/.test(l));
verifier("n°1 plus aucun toISOString().slice(0, 10) dans le code", horsCommentaire.length === 0, horsCommentaire.join(" | "));

// ═══ n° 6 : le bandeau 2.2b ═══
function avis(source) {
  const m = monter(source, ["function avisPlusieursAffaires("], ["const AFFAIRE_GENRE_PLURIEL"], ["avisPlusieursAffaires"]);
  if (m.erreur) { console.log(m.erreur); process.exit(2); }
  return m.api.avisPlusieursAffaires;
}
const neuf = avis(src);
const vieux = avis(ancien);
const off = (id, state) => ({ hektor_affaire_id: id, kind: "offre", state });

const une = neuf("offre", [off("1", "accepted"), off("2", "proposed")]);
verifier("n°6 une ecartee : « Cette offre n'a pas été refusée »", une && une.detail.startsWith("Cette offre n'a pas été refusée"), une && une.detail);
verifier("n°6 une ecartee : propose de la REFUSER", une && une.detail.includes("Choisis-la pour la refuser"), une && une.detail);
verifier("n°6 une ecartee : ne dit plus « fait foi »", une && !une.detail.includes("fait foi"), une && une.detail);
verifier("n°6 une ecartee : le titre et le ton ne bougent pas",
  une && une.ton === "avertir" && une.titre === "Une offre est acceptée, et ce bien en porte encore 1 autre", une && une.titre);
const deux = neuf("offre", [off("1", "accepted"), off("2", "proposed"), off("3", "proposed")]);
verifier("n°6 deux ecartees : « Ces offres n'ont pas été refusées »", deux && deux.detail.startsWith("Ces offres n'ont pas été refusées"), deux && deux.detail);
verifier("n°6 deux ecartees : « une à une »", deux && deux.detail.includes("Choisis-les une à une pour les refuser"), deux && deux.detail);
// les autres situations ne bougent pas
for (const [nom, genre, lignes] of [
  ["concurrence sans acceptee", "offre", [off("1", "proposed"), off("2", "proposed")]],
  ["deux acceptees", "offre", [off("1", "accepted"), off("2", "accepted")]],
  ["deux compromis", "compromis", [{ kind: "compromis", state: "active", hektor_acquereur_id: "7" }, { kind: "compromis", state: "active", hektor_acquereur_id: "7" }]],
  ["une seule offre", "offre", [off("1", "accepted")]],
]) {
  verifier(`n°6 inchange : ${nom}`, JSON.stringify(neuf(genre, lignes)) === JSON.stringify(vieux(genre, lignes)), "le message a change");
}
// TEMOIN INVERSE : l'ancien bandeau avait la faute et le « fait foi »
const v1 = vieux("offre", [off("1", "accepted"), off("2", "proposed")]);
verifier("n°6 TEMOIN : l'ancien disait « Ces offre aurait »", v1 && v1.detail.startsWith("Ces offre aurait"), v1 && v1.detail);
verifier("n°6 TEMOIN : l'ancien disait « fait foi »", v1 && v1.detail.includes("fait foi"), v1 && v1.detail);

console.log(echecs ? `\n${echecs} controle(s) en echec` : "\ntout vert");
process.exit(echecs ? 1 : 0);
