#!/usr/bin/env node
"use strict";
/**
 * ⑧ C9 — L'EDITEUR DU MANDAT OUVERT DEPUIS LE REGISTRE LIT NOTRE REGISTRE, COMME LA FICHE ANNONCE.   29/10/2026
 *
 * On EXECUTE les deux vrais choix de source de l'editeur (les `useMemo` de editorFullContacts et editorPartialContacts,
 * decoupes dans App.tsx, types retires par esbuild), avec des batisseurs FACTICES qui disent d'ou vient la liste :
 *   (1) charge complet, registre lu       -> NOTRE registre, pas le blob de Hektor
 *   (2) charge complet, registre lu VIDE  -> la liste vide est respectee (pas de retour au blob)
 *   (3) charge complet, registre muet     -> repli sur le blob de Hektor (interrupteur eteint ou lecture ratee)
 *   (4) rien de charge                    -> liste vide
 *   (5) charge partiel, blob absent       -> NOTRE liste du registre des mandats (mandants_json)
 *   (6) charge partiel, blob present      -> le blob (le repli d'avant reste)
 *   (7) la fiche annonce suit la meme regle (lue dans le code)
 *   (8) TEMOIN INVERSE sur le commit 46a28ed (FIXE) : l'ancien editeur lisait le blob, meme registre lu -> (1) echoue
 *   (9) MUTANT : sans la branche du registre, (1) echoue -> l'essai le voit
 * NE LANCE NI SERVEUR NI REQUETE.   node apps/hektor-v1/test_c9_editeur_registre.cjs
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");
const esbuild = require("esbuild");

const RACINE = path.resolve(__dirname, "..", "..");
const APP = "apps/hektor-v1/src/App.tsx";
const TEMOIN = "46a28ed";

// Decoupe « const <nom> = useMemo(<callback>, [deps]) » et rend le callback seul.
function callback(src, nom) {
  const i = src.indexOf(`const ${nom} = useMemo(`);
  if (i < 0) return null;
  const debut = i + `const ${nom} = useMemo(`.length;
  // le callback finit a la virgule de premier niveau qui precede le tableau des deps
  let prof = 0;
  for (let k = debut; k < src.length; k += 1) {
    const ch = src[k];
    if (ch === "(" || ch === "{" || ch === "[") prof += 1;
    else if (ch === ")" || ch === "}" || ch === "]") prof -= 1;
    else if (ch === "," && prof === 0) return src.slice(debut, k);
  }
  return null;
}
function monter(src) {
  const plein = callback(src, "editorFullContacts");
  const partiel = callback(src, "editorPartialContacts");
  if (!plein || !partiel) return null;
  const code = `
    function buildDetailContactsFromRegistre(v) { return [{ source: "registre", v }]; }
    function buildDetailContactsFromProprietaires(v) { const l = JSON.parse(v || "[]"); return l.length ? [{ source: "hektor", v }] : []; }
    function buildDetailContactsFromMandantsJson(v) { const l = JSON.parse(v || "[]"); return l.length ? [{ source: "mandants_json", v }] : []; }
    this.plein = (editorFullDetail) => (${plein})();
    this.partiel = (editorPartialDetail, selectedDetail) => (${partiel})();`;
  const ctx = { JSON, String };
  vm.createContext(ctx);
  vm.runInContext(esbuild.transformSync(code, { loader: "ts" }).code, ctx);
  return ctx;
}
const src = (texte) => texte.replace(/\r\n/g, "\n");
const blob = JSON.stringify([{ nom: "un mandant de Hektor" }]);
const notre = JSON.stringify([{ hektor_contact_id: "10000001" }]);

function essai(texte) {
  const R = [];
  const ok = (nom, vrai, detail) => R.push({ nom, vrai: Boolean(vrai), detail });
  const c = monter(texte);
  ok("les deux choix de source existent dans App.tsx", c);
  if (!c) return R;
  const s = (l) => (l[0] ? l[0].source : "(vide)");
  ok("(1) complet + registre lu : NOTRE registre", s(c.plein({ mandants_registre_json: notre, proprietaires_json: blob })) === "registre",
    s(c.plein({ mandants_registre_json: notre, proprietaires_json: blob })));
  ok("(2) complet + registre lu VIDE : on le respecte, pas de retour au blob",
    s(c.plein({ mandants_registre_json: "[]", proprietaires_json: blob })) === "registre");
  ok("(3) complet + registre muet : repli sur le blob de Hektor", s(c.plein({ proprietaires_json: blob })) === "hektor");
  ok("(4) rien de charge : liste vide", c.plein(null).length === 0);
  ok("(5) partiel + blob absent : notre liste du registre des mandats",
    s(c.partiel({}, { mandants_json: JSON.stringify([{ nom: "x" }]) })) === "mandants_json", s(c.partiel({}, { mandants_json: "[1]" })));
  ok("(6) partiel + blob present : le blob, comme avant", s(c.partiel({ proprietaires_json: blob }, { mandants_json: "[1]" })) === "hektor");
  ok("(6b) partiel, ni blob ni liste : vide", c.partiel({}, null).length === 0);
  return R;
}

let echecs = 0;
const actuel = src(fs.readFileSync(path.join(RACINE, APP), "utf8"));
for (const r of essai(actuel)) { console.log(`${r.vrai ? "  OK  " : "ECHEC "} ${r.nom}${r.vrai ? "" : " -- " + JSON.stringify(r.detail)}`); if (!r.vrai) echecs += 1; }

// (7) la fiche annonce porte la meme regle
const fiche = actuel.indexOf("const duRegistre = detail.mandants_registre_json");
const okFiche = fiche > 0 && actuel.slice(fiche, fiche + 400).includes("buildDetailContactsFromRegistre(duRegistre");
console.log(`${okFiche ? "  OK  " : "ECHEC "} (7) la fiche annonce suit la meme regle (registre d'abord)`); if (!okFiche) echecs += 1;

// (8) TEMOIN INVERSE
let ancien;
try { ancien = src(execFileSync("git", ["show", `${TEMOIN}:${APP}`], { cwd: RACINE, maxBuffer: 256 * 1024 * 1024 }).toString("utf8")); }
catch (e) { console.log("⛔ temoin illisible : " + e.message); process.exit(2); }
const t = essai(ancien).find((r) => r.nom.startsWith("(1)"));
const okTemoin = t && !t.vrai;
console.log(`${okTemoin ? "  OK  " : "ECHEC "} (8) TEMOIN : l'ancien editeur (${TEMOIN}) lisait le blob meme avec le registre lu`); if (!okTemoin) echecs += 1;

// (9) MUTANT
const mutant = actuel.replace("if (duRegistre !== null && duRegistre !== undefined) {\n      return buildDetailContactsFromRegistre(duRegistre, 'detail-contact')\n    }\n    return buildDetailContactsFromProprietaires(editorFullDetail.proprietaires_json",
  "return buildDetailContactsFromProprietaires(editorFullDetail.proprietaires_json");
const m = mutant !== actuel && essai(mutant).find((r) => r.nom.startsWith("(1)"));
const okMutant = m && !m.vrai;
console.log(`${okMutant ? "  OK  " : "ECHEC "} (9) MUTANT ATTRAPE : sans la branche du registre, (1) echoue`); if (!okMutant) echecs += 1;

console.log(echecs ? `\n${echecs} controle(s) en echec` : "\ntout est vert");
process.exit(echecs ? 1 : 0);
