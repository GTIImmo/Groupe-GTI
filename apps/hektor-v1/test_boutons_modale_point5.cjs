#!/usr/bin/env node
"use strict";
/**
 * ⑧ §58 POINT 5 — LES BOUTONS DE LA MODALE DES TRANSACTIONS (n° 1 et n° 5).   26/10/2026
 *
 * On EXECUTE le code reel : les fonctions sont decoupees dans App.tsx, depouillees de leurs types
 * par esbuild, et jouees sur des lignes de la forme du registre (app_affaire_ledger).
 *   n° 1  gesteOffreSansEffet        « Accepter » une offre deja acceptee / « Refuser » une offre deja
 *                                    refusee ne sont plus proposes -- la MEME comparaison que la base
 *                                    (app_geste_affaire_optimistic : `coalesce(a.state, '') = etat_apres`).
 *   n° 5  modifierChezHektorPossible le message « Modifier chez Hektor reprend celle-la… » suit le bouton.
 *
 * ⚠ TEMOIN INVERSE : les deux regles d'AVANT (bouton toujours la ; message des qu'une affaire est visee)
 *   sont rejouees sur les memes cas -- elles doivent ECHOUER la ou le defaut etait. Et deux MUTANTS
 *   (la regle sans la garde) doivent etre attrapes.
 *
 * NE LANCE NI SERVEUR NI REQUETE.
 *     node apps/hektor-v1/test_boutons_modale_point5.cjs
 *     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");

// Une fonction de premier niveau se termine par « \n} » en colonne 0 (le reste est indente).
function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

function monter(src) {
  const morceaux = [];
  for (const f of ["function compromisVerrouilleParSaVente(", "function gesteOffreSansEffet(",
                   "function modifierChezHektorPossible("]) {
    const t = tranche(src.replace(/\r\n/g, "\n"), f);
    if (!t) return { erreur: `fonction absente de App.tsx : ${f}` };
    morceaux.push(t);
  }
  const code = morceaux.join("\n\n") + `
    this.api = { compromisVerrouilleParSaVente, gesteOffreSansEffet, modifierChezHektorPossible };`;
  const js = esbuild.transformSync(code, { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api, code: js };
}

// ── des lignes de la forme du registre ──
const commun = { hektor_annonce_id: 24113, app_dossier_id: 1068399, present_in_hektor: true };
const offre = (state, id = 1) => ({ ...commun, app_affaire_id: id, app_chaine_id: id, kind: "offre", state });
const COMPROMIS_SEUL = { ...commun, app_affaire_id: 20, app_chaine_id: 20, kind: "compromis", state: "active" };
const COMPROMIS_VENDU = { ...commun, app_affaire_id: 30, app_chaine_id: 31, kind: "compromis", state: "active" };
const VENTE = { ...commun, app_affaire_id: 32, app_chaine_id: 31, kind: "vente", state: null };
const LIGNES = [COMPROMIS_SEUL, COMPROMIS_VENDU, VENTE];

let echecs = 0;
function ok(cond, libelle) {
  console.log(`${cond ? "  OK " : "  ⛔ "} ${libelle}`);
  if (!cond) echecs++;
}

const src = fs.readFileSync(APP, "utf8");
const m = monter(src);
if (m.erreur) { console.log("⛔ " + m.erreur); process.exit(2); }
const { gesteOffreSansEffet: sans, modifierChezHektorPossible: modif } = m.api;

console.log("n° 1 — le geste sans effet n'est plus propose (la regle de la base, au mot pres)");
ok(sans(offre("accepted"), "accepte") === true, "offre ACCEPTEE : « Accepter » cache");
ok(sans(offre("accepted"), "refus") === false, "offre ACCEPTEE : « Refuser » reste (le chemin pour corriger son montant)");
ok(sans(offre("refused"), "refus") === true, "offre REFUSEE : « Refuser » cache");
ok(sans(offre("refused"), "accepte") === false, "offre REFUSEE : « Accepter » reste (voulu le 08/09)");
ok(sans(offre("proposed"), "accepte") === false && sans(offre("proposed"), "refus") === false, "offre EN COURS : les deux restent");
ok(sans(offre(null), "accepte") === false && sans(offre(null), "refus") === false, "offre SANS ETAT : les deux restent");
ok(sans(offre("Accepted"), "accepte") === false, "« Accepted » (autre casse) : reste -- la base ne le jugerait pas sans effet");
ok(sans(COMPROMIS_SEUL, "accepte") === false, "pas une offre : rien n'est cache");
ok(sans(null, "accepte") === false, "aucune affaire visee : rien n'est cache");

console.log("n° 5 — le message suit le bouton « Modifier chez Hektor »");
ok(modif("offer", offre("proposed"), LIGNES) === true, "offre en cours : bouton et message");
ok(modif("compromise", COMPROMIS_SEUL, LIGNES) === true, "compromis seul : bouton et message");
ok(modif("compromise", COMPROMIS_VENDU, LIGNES) === false, "compromis d'une chaine VENDUE : ni bouton, ni message");
ok(modif("sold", VENTE, LIGNES) === true, "vente : bouton et message (« on ne touche pas », 24/10)");
ok(modif("active", offre("proposed"), LIGNES) === false && modif("closed", offre("proposed"), LIGNES) === false, "Actif / Clos : rien");
ok(modif("offer", null, LIGNES) === false, "aucune affaire visee : rien");

console.log("TEMOIN INVERSE — les regles d'avant, sur les memes cas");
const avantBouton = () => true;                       // Refuser / Accepter toujours affiches
const avantMessage = (affaire) => Boolean(affaire);   // App.tsx:22094 avant le 26/10
// « affiche » se compare a « affiche » : avant = toujours ; maintenant = quand le geste a un effet
ok(avantBouton(offre("accepted"), "accepte") === true && !sans(offre("accepted"), "accepte") === false,
  "avant : « Accepter » s'affichait sur une offre acceptee ; maintenant il est cache");
ok(avantMessage(COMPROMIS_VENDU) !== modif("compromise", COMPROMIS_VENDU, LIGNES), "avant : le message s'affichait sur le compromis d'une chaine vendue");

console.log("MUTANTS — la regle sans sa garde doit etre attrapee");
function mutant(remplacer, par, essai) {
  const code = m.code.replace(remplacer, par);
  if (code === m.code) return "le mutant n'a rien change (ancre perdue)";
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON };
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return essai(ctx.api) ? "attrape" : "PAS attrape";
}
const r1 = mutant("=== (geste === \"accepte\" ? \"accepted\" : \"refused\")", "!== \"\"",
  (api) => api.gesteOffreSansEffet(offre("proposed"), "accepte") !== false);
ok(r1 === "attrape", `mutant 1 (cacher des qu'il y a un etat) : ${r1}`);
const r2 = mutant("!(statut === \"compromise\" && compromisVerrouilleParSaVente(lignes, affaire))", "true",
  (api) => api.modifierChezHektorPossible("compromise", COMPROMIS_VENDU, LIGNES) !== false);
ok(r2 === "attrape", `mutant 2 (oublier la chaine vendue) : ${r2}`);

console.log(echecs ? `⛔ ${echecs} controle(s) en echec` : "TOUT VERT");
process.exit(echecs ? 1 : 0);
