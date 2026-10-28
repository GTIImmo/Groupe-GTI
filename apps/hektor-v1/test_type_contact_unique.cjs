#!/usr/bin/env node
"use strict";
/**
 * ⑧ TYPES, ÉTAPE 4 — P1 : UN SEUL VOCABULAIRE.   27/10/2026
 *
 *   L'écran avait trois logiques de type : l'annuaire du bureau (contactDirectoryCategories), le téléphone et la
 *   pastille (contactToneFromRoles), la recherche globale (rolesContact). Interrupteur allumé (TYPE_CONTACT_UNIQUE),
 *   le téléphone, la pastille et la recherche globale doivent dire EXACTEMENT ce que dit l'annuaire du bureau.
 *
 * On EXÉCUTE le code réel : les fonctions sont découpées dans App.tsx / RechercheGlobale.tsx et jouées par esbuild + vm,
 * sur TOUTES les combinaisons des 5 rôles réels (mesure du 27/10) × recherche active oui / non.
 * ⚠ TÉMOIN INVERSE : la version d'avant (git) doit être EN DÉSACCORD avec l'annuaire. MUTANT : l'interrupteur à false
 *   doit l'être aussi.
 *
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_type_contact_unique.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");
const RG = path.resolve(__dirname, "src", "RechercheGlobale.tsx");

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const finLigne = src.indexOf("\n", i);
  const ligne = src.slice(i, finLigne < 0 ? undefined : finLigne);
  if (/^const \w+ = [^{]*$/.test(ligne)) return ligne;           // constante sur une ligne
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

function monter(src, morceaux, exporte) {
  const s = src.replace(/\r\n/g, "\n");
  const code = [];
  for (const m of morceaux) {
    const t = tranche(s, m);
    if (!t) return { erreur: `absent : ${m}` };
    code.push(t);
  }
  const js = esbuild.transformSync(code.join("\n\n") + `\nthis.api = { ${exporte.join(", ")} };`, { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api };
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "OK   " : "ECHEC"} ${nom}${ok ? "" : "  -> " + detail}`);
  if (!ok) echecs++;
}

// La version d'AVANT : le parent du commit qui a introduit la marque (HEAD tant qu'il n'est pas committé).
function versionAvant(fichier, marque) {
  const h = execFileSync("git", ["log", "--format=%H", "-S", marque, "--", `:(top)apps/hektor-v1/src/${fichier}`],
    { cwd: __dirname, encoding: "utf8" }).trim().split(/\s+/).filter(Boolean).pop();
  return execFileSync("git", ["show", `${h ? h + "^" : "HEAD"}:apps/hektor-v1/src/${fichier}`],
    { cwd: __dirname, encoding: "utf8", maxBuffer: 64 << 20 });
}

const APP_MORCEAUX = ["function isBuyerRole(", "const contactDirectoryTypeLabel", "function contactDirectoryCategories(",
  "function contactToneFromRoles(", "function contactToneLabel(", "function contactToneBadgeLabel(", "function contactDirectoryRoleLabel("];
// ⑧ notaire, étape 3 (28/10) : contactDirectoryCategories appelle les aides du notaire
const APP_NEUFS = ["const TYPE_CONTACT_UNIQUE = ", "const TON_LIBELLE_UNIQUE", "const TYPE_NOTAIRE_ECRAN = ", "function estRoleNotaire("];
const APP_API = ["contactDirectoryCategories", "contactDirectoryTypeLabel", "contactToneFromRoles", "contactToneLabel",
  "contactToneBadgeLabel", "contactDirectoryRoleLabel"];

let app, appAvant, rg, rgAvant;
try {
  app = fs.readFileSync(APP, "utf8");
  rg = fs.readFileSync(RG, "utf8");
  appAvant = versionAvant("App.tsx", "const TYPE_CONTACT_UNIQUE = ");
  rgAvant = versionAvant("RechercheGlobale.tsx", "const TYPE_CONTACT_UNIQUE = ");
} catch (e) {
  console.log("IMPOSSIBLE de lire les sources ou git : " + e.message);
  process.exit(2);
}

const neuf = monter(app, [...APP_NEUFS, ...APP_MORCEAUX], APP_API);
const mutant = monter(app.replace("const TYPE_CONTACT_UNIQUE = true", "const TYPE_CONTACT_UNIQUE = false"),
  [...APP_NEUFS, ...APP_MORCEAUX], APP_API);
const avant = monter(appAvant, APP_MORCEAUX, APP_API);
for (const [nom, m] of [["neuf", neuf], ["mutant", mutant], ["avant", avant]]) {
  if (m.erreur) { console.log(`${nom} : ${m.erreur}`); process.exit(2); }
}
const rgNeuf = monter(rg, ["function rolesContact(", "const TYPE_CONTACT_UNIQUE = "], ["rolesContact"]);
const rgAncien = monter(rgAvant, ["function rolesContact("], ["rolesContact"]);
if (rgNeuf.erreur || rgAncien.erreur) { console.log(rgNeuf.erreur || rgAncien.erreur); process.exit(2); }

// Les 5 rôles réellement présents dans les types (mesure du 27/10 sur 62 339 contacts), toutes leurs combinaisons.
const ROLES = ["mandant", "proprietaire", "acquereur_offre", "acquereur_compromis", "acquereur_vente"];
const cas = [];
for (let m = 0; m < 1 << ROLES.length; m++) {
  const roles = ROLES.filter((_, i) => m & (1 << i));
  for (const actives of [0, 2]) cas.push({ roles, actives });
}

// Ce que dit l'annuaire du bureau : le type DOMINANT, avec ses mots (la référence, inchangée par P1).
function bureau(api, roles, actives) {
  const dominant = api.contactDirectoryCategories(roles, actives)[0];
  return dominant ? api.contactDirectoryTypeLabel[dominant] : "Contact";
}
function bureauTous(api, roles, actives) {
  return api.contactDirectoryCategories(roles, actives).map((c) => api.contactDirectoryTypeLabel[c]).join(" · ");
}
function desaccords(api, rgApi) {
  let n = 0;
  for (const { roles, actives } of cas) {
    const contact = { active_search_count: actives, total_search_count: actives };
    const ton = api.contactToneFromRoles(roles, contact);
    const ref = bureau(neuf.api, roles, actives);
    if (api.contactToneLabel(ton) !== ref) n++;
    if (api.contactToneBadgeLabel(ton) !== ref) n++;
    if (rgApi) {
      const c = { relation_roles_json: JSON.stringify(roles), active_search_count: actives };
      if (rgApi.rolesContact(c) !== bureauTous(neuf.api, roles, actives)) n++;
    }
  }
  return n;
}

// ═══ 1. Allumé : le téléphone, la pastille et la recherche globale disent ce que dit le bureau ═══
let ecarts = [];
for (const { roles, actives } of cas) {
  const contact = { active_search_count: actives, total_search_count: actives };
  const ton = neuf.api.contactToneFromRoles(roles, contact);
  const ref = bureau(neuf.api, roles, actives);
  const titre = neuf.api.contactToneLabel(ton), pastille = neuf.api.contactToneBadgeLabel(ton);
  const rgMots = rgNeuf.api.rolesContact({ relation_roles_json: JSON.stringify(roles), active_search_count: actives });
  if (titre !== ref || pastille !== ref) ecarts.push(`[${roles}] rech=${actives} : ${titre}/${pastille} au lieu de ${ref}`);
  if (rgMots !== bureauTous(neuf.api, roles, actives)) ecarts.push(`RG [${roles}] rech=${actives} : « ${rgMots} »`);
}
verifier(`les ${cas.length} combinaisons : téléphone, pastille et recherche globale = annuaire du bureau`, ecarts.length === 0, ecarts.slice(0, 5).join(" | "));

// ═══ 2. Les cas qui comptent, un par un ═══
const ton = (roles, actives = 0) => neuf.api.contactToneBadgeLabel(neuf.api.contactToneFromRoles(roles, { active_search_count: actives }));
verifier("un acheteur (vente) s'appelle « Acheteur », plus « Acquereur »", ton(["acquereur_vente"]) === "Acheteur", ton(["acquereur_vente"]));
verifier("un propriétaire s'appelle « Propriétaire », plus « Vendeur »", ton(["proprietaire"]) === "Propriétaire", ton(["proprietaire"]));
verifier("une recherche active s'appelle « Acquéreur »", ton([], 2) === "Acquéreur", ton([], 2));
verifier("JACQUIER (propriétaire + acheteur) : « Acheteur », plus « Mixte »",
  ton(["proprietaire", "acquereur_offre", "acquereur_compromis", "acquereur_vente"]) === "Acheteur",
  ton(["proprietaire", "acquereur_offre", "acquereur_compromis", "acquereur_vente"]));
verifier("mandant + propriétaire : « Mandant » (priorité de l'annuaire)", ton(["mandant", "proprietaire"]) === "Mandant", ton(["mandant", "proprietaire"]));
verifier("sans rôle ni recherche : « Contact »", ton([]) === "Contact", ton([]));
const lib = neuf.api.contactDirectoryRoleLabel;
verifier("les lignes de la fiche : « Acheteur — vente », « Acheteur — offre », « Propriétaire »",
  lib("acquereur_vente") === "Acheteur — vente" && lib("acquereur_offre") === "Acheteur — offre" && lib("proprietaire") === "Propriétaire",
  [lib("acquereur_vente"), lib("acquereur_offre"), lib("proprietaire")].join(" / "));
verifier("les notaires gardent leurs mots", lib("notaire_entree") === "Notaire entree" && lib("mandant") === "Mandant", lib("notaire_entree"));

// ═══ 3. Les deux menus « Rôle contact » ═══
const menus = (app.match(/\{ value: 'acquereur', label: TYPE_CONTACT_UNIQUE \? 'Acheteur' : 'Acquereur' \}/g) || []).length;
verifier("les deux menus « Rôle contact » disent « Acheteur »", menus === 2, `${menus} menu(s)`);
const restants = (app.match(/\{ value: 'acquereur', label: 'Acquereur' \}/g) || []).length;
verifier("aucun menu n'a gardé l'ancien mot", restants === 0, `${restants} restant(s)`);

// ═══ 4. TÉMOIN INVERSE et MUTANT ═══
const dAvant = desaccords(avant.api, rgAncien.api);
verifier(`TÉMOIN : la version d'avant était en désaccord avec le bureau (${dAvant} écarts)`, dAvant > 0, "aucun écart : l'essai ne prouve rien");
const dMutant = desaccords(mutant.api, null);
verifier(`MUTANT : l'interrupteur à false redonne les écarts (${dMutant})`, dMutant > 0, "le mutant passe");

console.log(echecs ? `\n${echecs} contrôle(s) en échec` : "\ntout vert");
process.exit(echecs ? 1 : 0);
