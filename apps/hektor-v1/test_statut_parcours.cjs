#!/usr/bin/env node
"use strict";
/**
 * 06/11/2026 — LE PARCOURS DE LA MODALE « CHANGER LE STATUT » (refonte visuelle, lot 1).
 * Plan : notice/PLAN_REFONTE_VISUELLE_MODALE_STATUT_2026-11-05.md §3 (lot 1) · matrice : audit §10.4 et §11.
 *
 * On EXECUTE le code reel : src/lib/statutParcours.ts, et les VRAIES gardes d'App.tsx qu'il recoit
 * (etatFermeAuxTransactions, bienEngage, dossiersOuvertsDuBien), decoupees et depouillees de leurs types
 * par esbuild. Les 11 situations de la matrice sont jouees sur des lignes de la forme du registre.
 *
 * ⚠ La situation 5 (annulation du mandat demandee) n'est pas reconnue, et c'est voulu : la modale ne lit
 *   pas les demandes, et ce lot n'ajoute aucune lecture. L'essai le VERIFIE (aucune situation ne rend 5).
 * ⚠ TEMOIN INVERSE : avec une garde « bienEngage » qui dirait toujours non, la situation 7 doit tomber en 6 ;
 *   avec une garde « etatFermeAuxTransactions » muette, un bien vendu ne doit plus etre reconnu.
 *
 * NE LANCE NI SERVEUR NI REQUETE.
 *     node apps/hektor-v1/test_statut_parcours.cjs
 *     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");
const PARCOURS = path.resolve(__dirname, "src", "lib", "statutParcours.ts");

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

function monter() {
  const s = fs.readFileSync(APP, "utf8").replace(/\r\n/g, "\n");
  const morceaux = [];
  for (const c of ["const AFFAIRE_ETAT_MORT", "const AFFAIRE_ETATS_ACCEPTES"]) {
    const i = s.indexOf(c);
    if (i < 0) return { erreur: `constante absente de App.tsx : ${c}` };
    morceaux.push(s.slice(i, s.indexOf("\n", i)));
  }
  for (const f of ["function etatFermeAuxTransactions(", "function dossiersOuvertsDuBien(", "function bienEngage("]) {
    const t = tranche(s, f);
    if (!t) return { erreur: `fonction absente de App.tsx : ${f}` };
    morceaux.push(t);
  }
  const gardes = esbuild.transformSync(morceaux.join("\n\n")
    + "\nthis.gardes = { etatFermeAuxTransactions, dossiersOuvertsDuBien, bienEngage };", { loader: "ts" }).code;
  const parcours = esbuild.transformSync(fs.readFileSync(PARCOURS, "utf8"), { loader: "ts", format: "cjs" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp, module: { exports: {} } };
  ctx.exports = ctx.module.exports;
  vm.createContext(ctx);
  vm.runInContext(gardes, ctx);
  vm.runInContext(parcours, ctx);
  return { gardes: ctx.gardes, parcours: ctx.module.exports };
}

let echecs = 0;
function ok(cond, libelle) {
  console.log(`${cond ? "  OK " : "  ⛔ "} ${libelle}`);
  if (!cond) echecs++;
}

let m;
try { m = monter(); } catch (e) { console.log("⛔ n'a pas pu monter le code : " + e.message); process.exit(2); }
if (m.erreur) { console.log("⛔ " + m.erreur); process.exit(2); }
const { situationDuBien } = m.parcours;

// ── des lignes de la forme du registre ──
const commun = { hektor_annonce_id: 59132, app_dossier_id: 1386543, present_in_hektor: true };
const af = (id, chaine, kind, state) => ({ ...commun, app_affaire_id: id, app_chaine_id: chaine, kind, state, hektor_affaire_id: String(id) });
const JOUR = "2026-11-06";
const entree = (statutAnnonce, affaires = [], o = {}) => ({ statutAnnonce, affaires, mandatDateFin: "2027-06-30", mandatValide: true, aujourdhui: JOUR, ...o });
const etats = (s) => Object.fromEntries(s.cartes.map((c) => [c.statut, c.etat]));
const carte = (s, k) => s.cartes.find((c) => c.statut === k);

function cas(n, libelle, e, attendu, gardes = m.gardes) {
  const s = situationDuBien(e, gardes);
  const et = etats(s);
  const bon = s.numero === attendu.numero && s.conseille === attendu.conseille && s.actuel === attendu.actuel
    && Object.entries(attendu.etats || {}).every(([k, v]) => et[k] === v)
    && s.cartes.every((c) => c.etat === "libre" || c.raison.trim() !== "");
  ok(bon, `${n} ${libelle} -> situation ${s.numero}, conseille ${s.conseille}, actuel ${s.actuel}, ${JSON.stringify(et)}`);
  return s;
}

console.log("Les 11 situations de la matrice (audit §10.4)");
cas(1, "Estimation", entree("Estimation"), { numero: 1, conseille: null, actuel: null,
  etats: { active: "hors", offer: "lecture", compromise: "lecture", sold: "lecture", closed: "libre" } });
const s2 = cas(2, "Actif, mandat a controler, aucune affaire", entree("Actif", [], { mandatValide: false }), { numero: 2, conseille: null, actuel: "active",
  etats: { active: "sans_effet", offer: "libre", compromise: "libre", sold: "hors", closed: "libre" } });
ok(s2.avertissements.length === 1 && carte(s2, "offer").raison !== "", "2 l'avertissement « mandat non valide » est dit, et la carte Offre le rappelle sans bloquer");
cas(3, "Actif, mandat valide, aucune affaire", entree("Actif"), { numero: 3, conseille: "offer", actuel: "active",
  etats: { active: "sans_effet", offer: "libre", compromise: "libre", sold: "hors", closed: "libre" } });
const s4 = cas(4, "Actif, mandat echu, aucune affaire", entree("Actif", [], { mandatDateFin: "2026-10-01" }), { numero: 4, conseille: null, actuel: "active",
  etats: { active: "sans_effet", offer: "hors", compromise: "hors", sold: "hors", closed: "libre" } });
ok(s4.avertissements.some((a) => a.includes("01/10/2026")), "4 la date d'echeance est dite, en jj/mm/aaaa");
const s6 = cas(6, "Sous offre, offre proposee", entree("Sous offre", [af(101, 101, "offre", "proposed")]), { numero: 6, conseille: "offer", actuel: "offer",
  etats: { active: "hors", offer: "libre", compromise: "libre", sold: "hors", closed: "libre" } });
ok(carte(s6, "closed").raison !== "" && carte(s6, "compromise").raison !== "", "6 Clos et Compromis restent libres, avec leur avertissement");
cas(7, "Sous offre, offre acceptee (engage)", entree("Sous offre", [af(101, 101, "offre", "accepted")]), { numero: 7, conseille: "compromise", actuel: "offer",
  etats: { active: "hors", offer: "libre", compromise: "libre", sold: "hors", closed: "hors" } });
cas(8, "Sous compromis, compromis vivant", entree("Sous compromis", [af(101, 101, "offre", "accepted"), af(110, 101, "compromis", "active")]),
  { numero: 8, conseille: "sold", actuel: "compromise",
    etats: { active: "hors", offer: "lecture", compromise: "libre", sold: "libre", closed: "hors" } });
cas(9, "Sous compromis, compromis annule (rien de vivant)", entree("Sous compromis", [af(101, 101, "offre", "accepted"), af(110, 101, "compromis", "cancelled")]),
  { numero: 9, conseille: "active", actuel: "compromise",
    etats: { active: "libre", offer: "libre", compromise: "libre", sold: "hors", closed: "libre" } });
cas(10, "Vendu", entree("Vendu", [af(101, 101, "offre", "accepted"), af(110, 101, "compromis", "active"), af(120, 101, "vente", "active")]),
  { numero: 10, conseille: null, actuel: "sold",
    etats: { active: "hors", offer: "lecture", compromise: "lecture", sold: "libre", closed: "hors" } });
cas(11, "Clos", entree("Clos"), { numero: 11, conseille: null, actuel: "closed",
  etats: { active: "hors", offer: "lecture", compromise: "lecture", sold: "lecture", closed: "sans_effet" } });

console.log("Les cas voisins");
const s9v = cas("9b", "Sous compromis, AUCUNE affaire lue (lecture ratee ou en cours) : pas de conseil", entree("Sous compromis"),
  { numero: 9, conseille: null, actuel: "compromise" });
ok(s9v.avertissements.some((a) => a.includes("ne sont pas lues")), "9b le guide dit que les affaires ne sont pas lues");
cas("8b", "Actif mais un compromis vivant (1 cas au parc le 05/11) : on suit le DOSSIER", entree("Actif", [af(110, 110, "compromis", "active")]),
  { numero: 8, conseille: "sold", actuel: "active" });
cas("6b", "Sous offre, offre refusee : rien de vivant -> remettre en vente", entree("Sous offre", [af(101, 101, "offre", "refused")]),
  { numero: 9, conseille: "active", actuel: "offer" });
cas("8c", "compromis efface chez Hektor : ne tient plus le dossier", entree("Sous compromis",
  [{ ...af(110, 110, "compromis", "active"), present_in_hektor: false }]), { numero: 9, conseille: "active", actuel: "compromise" });
cas("10b", "un bien vendu autrefois puis revenu Actif est LIBRE (objection du 08/09)", entree("Actif",
  [af(101, 101, "offre", "accepted"), af(110, 101, "compromis", "active"), af(120, 101, "vente", "active")]), { numero: 3, conseille: "offer", actuel: "active" });
cas("4b", "mandat echu mais compromis vivant : le compromis passe avant", entree("Sous compromis", [af(110, 110, "compromis", "active")], { mandatDateFin: "2026-01-01" }),
  { numero: 8, conseille: "sold", actuel: "compromise" });
cas("3b", "date de fin vide : pas echu", entree("Actif", [], { mandatDateFin: null }), { numero: 3, conseille: "offer", actuel: "active" });
cas("3c", "date de fin « 0000-00-00 » de Hektor : pas echu", entree("Actif", [], { mandatDateFin: "0000-00-00" }), { numero: 3, conseille: "offer", actuel: "active" });
cas("3d", "date de fin AUJOURD'HUI : pas encore echu", entree("Actif", [], { mandatDateFin: JOUR }), { numero: 3, conseille: "offer", actuel: "active" });

console.log("Le guide (src/lib/statutGuide.ts) : un texte pour chaque carte de chaque situation");
const guide = (() => {
  const js = esbuild.transformSync(fs.readFileSync(path.resolve(__dirname, "src", "lib", "statutGuide.ts"), "utf8"), { loader: "ts", format: "cjs" }).code;
  const ctx = { String, Array, Object, module: { exports: {} } }; ctx.exports = ctx.module.exports;
  vm.createContext(ctx); vm.runInContext(js, ctx); return ctx.module.exports;
})();
const situations = [entree("Estimation"), entree("Actif", [], { mandatValide: false }), entree("Actif"), entree("Actif", [], { mandatDateFin: "2026-10-01" }),
  entree("Sous offre", [af(101, 101, "offre", "proposed")]), entree("Sous offre", [af(101, 101, "offre", "accepted")]),
  entree("Sous compromis", [af(101, 101, "offre", "accepted"), af(110, 101, "compromis", "active")]),
  entree("Sous compromis", [af(110, 101, "compromis", "cancelled")]), entree("Sous compromis"), entree("Vendu"), entree("Clos")]
  .map((e) => situationDuBien(e, m.gardes));
let guidesVides = 0, vus = 0;
for (const s of situations) for (const k of ["active", "offer", "compromise", "sold", "closed"]) {
  const g = guide.guidePour(k, s); vus++;
  if (!g.titre.trim() || !g.texte.trim() || g.etapes.length !== 3 || g.etapes.some(([a, b]) => !a.trim() || !b.trim())) {
    guidesVides++; console.log(`     guide incomplet : situation ${s.numero}, carte ${k}`);
  }
}
ok(guidesVides === 0, `${vus} guides (11 situations x 5 cartes) : titre, texte et 3 etapes partout`);
ok(Object.keys(guide.DESCRIPTION_CARTE).join() === "active,offer,compromise,sold,closed", "une description metier pour chacune des 5 cartes");

console.log("Ce que le module ne fait PAS");
const tous = [entree("Estimation"), entree("Actif"), entree("Actif", [], { mandatValide: false }), entree("Clos"), entree("Vendu"),
  entree("Sous offre", [af(1, 1, "offre", "proposed")]), entree("Sous compromis", [af(1, 1, "compromis", "active")])].map((e) => situationDuBien(e, m.gardes));
ok(tous.every((s) => s.numero !== 5), "la situation 5 n'est jamais rendue (la modale ne lit pas les demandes)");
ok(tous.every((s) => s.cartes.length === 5 && s.cartes.map((c) => c.statut).join() === "active,offer,compromise,sold,closed"),
  "toujours les 5 cartes, dans l'ordre de l'ancienne modale : rien n'est retire");
ok(tous.every((s) => s.cartes.filter((c) => c.conseille).length <= 1), "au plus UNE carte conseillee");
const src = fs.readFileSync(PARCOURS, "utf8");
ok(!/from ['"]\.\/api['"]/.test(src.replace(/import type[^\n]*\n/g, "")) && !/supabase|fetch\(|create\w*Job/i.test(src.replace(/\/\/[^\n]*/g, "")),
  "le module n'importe que des TYPES, n'appelle ni Supabase, ni fetch, ni un travail");

console.log("TEMOIN INVERSE — on fausse une garde, la situation doit changer");
const sansEngage = { ...m.gardes, bienEngage: () => false };
ok(situationDuBien(entree("Sous offre", [af(101, 101, "offre", "accepted")]), sansEngage).numero === 6,
  "bienEngage muette : l'offre acceptee n'engage plus -> situation 6 (la 7 vient bien de la garde)");
const sansFerme = { ...m.gardes, etatFermeAuxTransactions: () => null };
ok(situationDuBien(entree("Vendu"), sansFerme).numero !== 10,
  "etatFermeAuxTransactions muette : un bien vendu n'est plus reconnu (la 10 vient bien de la garde)");

console.log(echecs ? `⛔ ${echecs} controle(s) en echec` : "TOUT VERT");
process.exit(echecs ? 1 : 0);
