#!/usr/bin/env node
"use strict";
/**
 * 05/11/2026 — L'OFFRE OUBLIEE QUI SE REGULARISE (option 1) ET CE QUE LA MODALE DIT DU RATTACHEMENT (option 2).
 * Note : notice/AUDIT_REFONTE_MODALE_STATUT_2026-11-05.md §13-14.
 *
 * On EXECUTE le code reel : les fonctions sont decoupees dans App.tsx, depouillees de leurs types par esbuild,
 * et jouees sur des lignes de la forme du registre (app_affaire_ledger).
 *   offreARegulariser / compromisDeLaRegularisation   « Accepter » rendu a l'offre ecartee, et a elle seule,
 *                                                      quand le run de nuit la rattacherait sans ambiguite
 *   dateOffreFaite                                    la date de la PREMIERE proposition, comme la nuit
 *   rattachementOffreProposee                         « rattachee » / « sera rattachee cette nuit »
 *
 * ⚠ TEMOIN INVERSE : la regle d'avant (offre ecartee = jamais « Accepter ») est rejouee sur le cas R1 -- elle
 *   doit dire NON la ou la nouvelle dit OUI. Et trois MUTANTS (une condition retiree) doivent etre attrapes.
 *
 * NE LANCE NI SERVEUR NI REQUETE.
 *     node apps/hektor-v1/test_offre_regularisation.cjs
 *     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

function monter(src) {
  const morceaux = [];
  const s = src.replace(/\r\n/g, "\n");
  for (const f of ["function affaireEstVivante(", "function offreVerrouilleeParSonDossier(",
                   "function dossiersOuvertsDuBien(", "function bienEngage(", "function offreEcarteeSurBienEngage(",
                   "function dateOffreFaite(", "function offreARegulariser(", "function compromisDeLaRegularisation(",
                   "function rattachementOffreProposee(", "function lireMandantsAffaire("]) {
    const t = tranche(s, f);
    if (!t) return { erreur: `fonction absente de App.tsx : ${f}` };
    morceaux.push(t);
  }
  for (const c of ["const AFFAIRE_RANG", "const AFFAIRE_ETAT_MORT", "const AFFAIRE_ETATS_ACCEPTES"]) {
    const i = s.indexOf(c);
    if (i < 0) return { erreur: `constante absente de App.tsx : ${c}` };
    morceaux.unshift(s.slice(i, s.indexOf("\n", i)));
  }
  const code = morceaux.join("\n\n") + `
    this.api = { offreARegulariser, compromisDeLaRegularisation, dateOffreFaite, rattachementOffreProposee,
                 offreEcarteeSurBienEngage };`;
  const js = esbuild.transformSync(code, { loader: "ts" }).code;
  return { api: executer(js), code: js };
}
function executer(js) {
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return ctx.api;
}

// ── des lignes de la forme du registre ──
const commun = { hektor_annonce_id: 59132, app_dossier_id: 1386543, present_in_hektor: true };
const acq = (...ids) => ids.map((id) => ({ id, nom: "N" + id }));
const of = (id, chaine, state, jour, extra = {}) => ({ ...commun, app_affaire_id: id, app_chaine_id: chaine, kind: "offre",
  state, hektor_affaire_id: String(id), date: jour, propositions_json: [{ type: "proposition", date: jour + " 10:00:00" }],
  acquereurs_json: acq("A1"), ...extra });
const co = (id, chaine, state, jour, extra = {}) => ({ ...commun, app_affaire_id: id, app_chaine_id: chaine, kind: "compromis",
  state, hektor_affaire_id: String(id), date: jour, acquereurs_json: acq("B1"), ...extra });

let echecs = 0;
function ok(cond, libelle) {
  console.log(`${cond ? "  OK " : "  ⛔ "} ${libelle}`);
  if (!cond) echecs++;
}

const src = fs.readFileSync(APP, "utf8");
const m = monter(src);
if (m.erreur) { console.log("⛔ " + m.erreur); process.exit(2); }
const { offreARegulariser: reg, compromisDeLaRegularisation: lequel, dateOffreFaite: dateDe, rattachementOffreProposee: ratt } = m.api;

// R1 le cas : offre au nom de Monsieur (A1) le 01/09, compromis au nom de Madame (B1) le 12/10, deux dossiers
const X1 = of(101, 101, "proposed", "2026-09-01");
const C1 = co(110, 110, "active", "2026-10-12");
const R1 = [X1, C1];

console.log("Option 1 — « Accepter » rendu a l'offre oubliee, et a elle seule");
ok(reg(R1, X1) === true, "R1 offre du 01/09, compromis du 12/10, autre dossier, aucune offre acceptee : OUI");
ok(lequel(R1, X1)?.app_affaire_id === 110, "R1 : le compromis retenu est bien le 110");
const X2 = of(102, 102, "proposed", "2026-10-20");
ok(reg([X2, C1], X2) === false, "R2 offre datee APRES le compromis : NON (vraie concurrente)");
const A3 = of(120, 120, "accepted", "2026-09-05", { acquereurs_json: acq("Z9") });
ok(reg([X1, A3, C1], X1) === false, "R3 une AUTRE offre acceptee vit : NON (le compromis s'y rattache deja)");
const X4 = of(101, 110, "proposed", "2026-09-01");
ok(reg([X4, C1], X4) === false, "R4 offre DANS le dossier du compromis : NON (verrou du 16/09)");
const X5 = of(101, 101, "refused", "2026-09-01");
ok(reg([X5, C1], X5) === false, "R5 offre deja refusee : NON");
const Y6 = of(111, 110, "proposed", "2026-09-10", { acquereurs_json: acq("B1") });
ok(reg([X1, Y6, C1], X1) === false, "R6 le dossier du compromis porte deja une offre (§ 2.8) : NON (on ne la detache pas)");
const C7 = co(130, 130, "active", "2026-10-15", { acquereurs_json: acq("C1") });
ok(reg([X1, C1, C7], X1) === false, "R7 deux compromis vivants : NON (ambigu)");
const X8 = of(101, 101, "proposed", "2026-10-25", { propositions_json: [{ type: "proposition", date: "2026-09-01 09:00:00" },
  { type: "proposition", date: "2026-10-25 09:00:00" }] });
ok(dateDe(X8) === "2026-09-01", "R8 la date de l'offre = sa PREMIERE proposition (comme la nuit), pas la colonne");
ok(reg([X8, C1], X8) === true, "R8 colonne datee apres le compromis, premiere proposition avant : OUI");
const X9 = of(101, 101, "proposed", "2026-10-12");
ok(reg([X9, C1], X9) === true, "R9 meme jour que le compromis : OUI (la nuit range l'offre d'abord)");
const X10 = of(101, 101, "proposed", "0000-00-00", { propositions_json: [] });
ok(reg([X10, C1], X10) === false, "R10 offre sans date utilisable : NON (on ne devine pas)");
const X11 = of(101, 101, "proposed", "2026-09-01", { present_in_hektor: false });
ok(reg([X11, C1], X11) === false, "R11 offre disparue de Hektor : NON");
ok(reg([of(101, 101, "proposed", "2026-09-01")], X1) === false, "R12 bien libre (aucun compromis) : NON (Accepter y est deja)");

console.log("Option 2 — ce que la modale dit du rattachement");
const r1 = ratt([X4, C1], X4);
ok(r1?.quand === "fait" && r1.compromis.app_affaire_id === 110, "P1 offre « proposee » dans le dossier du compromis : « rattachee »");
const XN = of(101, 101, "proposed", "2026-09-01", { acquereurs_json: acq("A1") });
const CN = co(110, 110, "active", "2026-10-12", { acquereurs_json: acq("A1", "B1") });
const r2 = ratt([XN, CN], XN);
ok(r2?.quand === "nuit" && r2.compromis.app_affaire_id === 110, "P2 autre dossier, meme acquereur, compromis apres : « sera rattachee cette nuit »");
ok(ratt([X1, C1], X1) === null, "P3 aucun acquereur commun : rien");
ok(ratt([of(101, 110, "accepted", "2026-09-01"), C1], of(101, 110, "accepted", "2026-09-01")) === null, "P4 offre deja acceptee : rien");
const CA = co(110, 101, "cancelled", "2026-10-12", { acquereurs_json: acq("A1") });
ok(ratt([of(101, 101, "proposed", "2026-09-01"), CA], of(101, 101, "proposed", "2026-09-01")) === null, "P5 compromis annule dans son dossier : rien");
const CN2 = co(120, 120, "active", "2026-10-14", { acquereurs_json: acq("A1") });
ok(ratt([XN, CN, CN2], XN) === null, "P6 deux compromis possibles : rien (on ne devine pas)");
ok(ratt([of(101, 101, "proposed", "2026-10-20"), CN], of(101, 101, "proposed", "2026-10-20")) === null, "P7 offre apres le compromis : rien");

console.log("TEMOIN INVERSE — la regle d'avant, sur R1");
const avant = (lignes, offre) => !m.api.offreEcarteeSurBienEngage(lignes, offre);   // 26/10 : ecartee = pas d'« Accepter »
ok(avant(R1, X1) === false && reg(R1, X1) === true, "avant : « Accepter » cache sur l'offre oubliee ; maintenant affiche");

console.log("MUTANTS — une condition retiree doit etre attrapee");
function mutant(remplacer, par, essai) {
  const code = m.code.replace(remplacer, par);
  if (code === m.code) return "le mutant n'a rien change (ancre perdue)";
  return essai(executer(code)) ? "attrape" : "PAS attrape";
}
const r1m = mutant("if (acceptee) return null", "", (api) => api.offreARegulariser([X1, A3, C1], X1) !== false);
ok(r1m === "attrape", `mutant 1 (oublier l'autre offre acceptee) : ${r1m}`);
const r2m = mutant("return dOffre <= dCompromis ? compromis[0] : null", "return compromis[0]",
  (api) => api.offreARegulariser([X2, C1], X2) !== false);
ok(r2m === "attrape", `mutant 2 (oublier la date) : ${r2m}`);
const r3m = mutant("return (dates.length ? utile([...dates].sort()[0]) : \"\") || utile(a.date)", "return utile(a.date)",
  (api) => api.offreARegulariser([X8, C1], X8) !== true);
ok(r3m === "attrape", `mutant 3 (dater l'offre par la colonne) : ${r3m}`);

console.log(echecs ? `⛔ ${echecs} controle(s) en echec` : "TOUT VERT");
process.exit(echecs ? 1 : 0);
