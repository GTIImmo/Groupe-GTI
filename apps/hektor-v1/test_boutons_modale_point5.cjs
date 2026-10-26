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
  const s = src.replace(/\r\n/g, "\n");
  for (const f of ["function compromisVerrouilleParSaVente(", "function gesteOffreSansEffet(",
                   "function modifierChezHektorPossible(", "function affaireEstVivante(",
                   "function offreVerrouilleeParSonDossier(", "function dossiersOuvertsDuBien(",
                   "function bienEngage(", "function offreEcarteeSurBienEngage(",
                   "function nouvelleOffreFermeeSurBienEngage("]) {
    const t = tranche(s, f);
    if (!t) return { erreur: `fonction absente de App.tsx : ${f}` };
    morceaux.push(t);
  }
  // les constantes, recopiees DEPUIS App.tsx (pas retapees)
  for (const c of ["const AFFAIRE_RANG", "const AFFAIRE_ETAT_MORT", "const AFFAIRE_ETATS_ACCEPTES"]) {
    const i = s.indexOf(c);
    if (i < 0) return { erreur: `constante absente de App.tsx : ${c}` };
    morceaux.unshift(s.slice(i, s.indexOf("\n", i)));
  }
  const code = morceaux.join("\n\n") + `
    this.api = { compromisVerrouilleParSaVente, gesteOffreSansEffet, modifierChezHektorPossible,
                 bienEngage, offreEcarteeSurBienEngage, nouvelleOffreFermeeSurBienEngage };`;
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
// ⚠ bien LIBRE ici : sur un bien qui porte un compromis ouvert (LIGNES), une offre en cours d'un autre dossier
//   est une offre ECARTEE (n° 2) et n'a plus de « Modifier » -- c'est voulu, controle juste en dessous.
ok(modif("offer", offre("proposed"), [offre("proposed")]) === true, "offre en cours sur un bien libre : bouton et message");
ok(modif("offer", offre("proposed"), LIGNES) === false, "offre en cours sur un bien ENGAGE (compromis ouvert ailleurs) : ni bouton, ni message");
ok(modif("compromise", COMPROMIS_SEUL, LIGNES) === true, "compromis seul : bouton et message");
ok(modif("compromise", COMPROMIS_VENDU, LIGNES) === false, "compromis d'une chaine VENDUE : ni bouton, ni message");
ok(modif("sold", VENTE, LIGNES) === true, "vente : bouton et message (« on ne touche pas », 24/10)");
ok(modif("active", offre("proposed"), LIGNES) === false && modif("closed", offre("proposed"), LIGNES) === false, "Actif / Clos : rien");
ok(modif("offer", null, LIGNES) === false, "aucune affaire visee : rien");

console.log("n° 2 — un bien ENGAGE : pas de nouvelle offre ; l'offre ecartee se refuse, et c'est tout");
const { bienEngage: engage, offreEcarteeSurBienEngage: ecartee, nouvelleOffreFermeeSurBienEngage: fermee } = m.api;
const of = (id, chaine, state, extra = {}) => ({ ...commun, app_affaire_id: id, app_chaine_id: chaine, kind: "offre", state, hektor_affaire_id: String(id), ...extra });
const co = (id, chaine, state) => ({ ...commun, app_affaire_id: id, app_chaine_id: chaine, kind: "compromis", state, hektor_affaire_id: String(id) });
const ve = (id, chaine) => ({ ...commun, app_affaire_id: id, app_chaine_id: chaine, kind: "vente", state: null, hektor_affaire_id: String(id) });
// S1 bien LIBRE : deux offres en concurrence
const S1 = [of(101, 101, "proposed"), of(102, 102, "proposed")];
// S2 engage par une offre ACCEPTEE : A retenue, B en cours, C deja refusee
const A2 = of(201, 201, "accepted"), B2 = of(202, 202, "proposed"), C2 = of(203, 203, "refused");
const S2 = [A2, B2, C2];
// S3 engage par un COMPROMIS : A acceptee + compromis (dossier 301), B en cours ailleurs, D en cours DANS le dossier du compromis
const A3 = of(301, 301, "accepted"), D3 = of(303, 301, "proposed"), B3 = of(302, 302, "proposed");
const S3 = [A3, co(310, 301, "active"), B3, D3];
// S4 bien REVENDU : un vieux dossier ferme par sa vente, une offre neuve en cours
const S4 = [of(401, 401, "accepted"), co(410, 401, "active"), ve(420, 401), of(402, 402, "proposed")];
// S5 engage, mais l'offre en cours a disparu de Hektor
const B5 = of(502, 502, "proposed", { present_in_hektor: false });
const S5 = [of(501, 501, "accepted"), B5];
ok(engage(S1) === false && fermee("offer", S1) === false, "S1 bien libre : « Envoyer vers Offre » reste");
ok(ecartee(S1, S1[0]) === false, "S1 bien libre : aucune offre n'est « ecartee » (toutes se choisissent deja)");
ok(engage(S2) === true && fermee("offer", S2) === true, "S2 offre acceptee : « Envoyer vers Offre » masque");
ok(fermee("compromise", S2) === false, "S2 : le compromis, lui, n'est pas touche par cette regle (2.2c decide)");
ok(ecartee(S2, B2) === true, "S2 : l'offre B encore en cours est ECARTEE -> elle se choisit pour etre refusee");
ok(ecartee(S2, A2) === false, "S2 : l'offre ACCEPTEE n'est pas ecartee (elle est visee par les actions)");
ok(ecartee(S2, C2) === false, "S2 : l'offre deja REFUSEE n'est pas ecartee (rien a refuser)");
ok(modif("offer", B2, S2) === false, "S2 : pas de « Modifier » sur l'offre ecartee");
ok(modif("offer", A2, S2) === true, "S2 : « Modifier » reste sur l'offre retenue");
ok(engage(S3) === true && ecartee(S3, B3) === true, "S3 compromis : l'offre d'un autre dossier encore en cours est ecartee");
ok(ecartee(S3, D3) === false, "S3 : une offre DANS le dossier du compromis reste verrouillee (16/09), pas ecartee");
ok(engage(S4) === false && fermee("offer", S4) === false, "S4 bien revendu : la vente ferme le vieux dossier, une offre neuve passe");
ok(ecartee(S5, B5) === false, "S5 : une offre disparue de Hektor n'est pas proposee au refus");

console.log("TEMOIN INVERSE — les regles d'avant, sur les memes cas");
const avantFermee = () => false;                       // « Envoyer vers Offre » toujours la (avisGardeFouSaisie : genre offre -> rien)
const avantChoisir = (lignes) => !engage(lignes);      // 08/09 : rien ne se choisit sur un bien engage
ok(avantFermee("offer", S2) !== fermee("offer", S2), "avant : une offre neuve se creait sur un bien engage ; maintenant non");
ok(avantChoisir(S2) === false && ecartee(S2, B2) === true, "avant : l'offre ecartee ne se choisissait pas, donc ne se refusait pas ; maintenant oui");
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
const r3 = mutant("if (!bienEngage(lignes)) return false", "",
  (api) => api.offreEcarteeSurBienEngage(S1, S1[0]) !== false);
ok(r3 === "attrape", `mutant 3 (ecartee sans bien engage) : ${r3}`);
const r4 = mutant("return !offreVerrouilleeParSonDossier(lignes, affaire)", "return true",
  (api) => api.offreEcarteeSurBienEngage(S3, D3) !== false);
ok(r4 === "attrape", `mutant 4 (oublier le verrou du 16/09) : ${r4}`);
const r5 = mutant("return statut === \"offer\" && bienEngage(lignes)", "return statut === \"offer\"",
  (api) => api.nouvelleOffreFermeeSurBienEngage("offer", S4) !== false);
ok(r5 === "attrape", `mutant 5 (fermer toute offre, meme sur un bien revendu) : ${r5}`);

console.log(echecs ? `⛔ ${echecs} controle(s) en echec` : "TOUT VERT");
process.exit(echecs ? 1 : 0);
