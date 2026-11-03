#!/usr/bin/env node
"use strict";
/**
 * COUPLES · PIÈCE G — « AJOUTER UN CONJOINT » : L'ÉCRAN.   03/11/2026
 *
 * On EXÉCUTE le code réel : src/lib/coupleAffichage.ts (peutRecevoirUnConjoint, raisonAjoutConjoint) est transformé par
 * esbuild et joué par vm, sur des fiches SYNTHÉTIQUES. Puis on lit App.tsx et api.ts pour le câblage : le bouton suit le
 * cran, le droit et la personne seule ; la fenêtre crée d'abord le NOUVEAU conjoint, puis rattache avec SON numéro.
 * MUTANT : une fiche archivée en texte (« 1 ») doit perdre le bouton -- attrapé.
 * Synthèse couples §52-53. NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_ajouter_conjoint_ecran.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const LIB = path.resolve(__dirname, "src", "lib", "coupleAffichage.ts");
const APP = path.resolve(__dirname, "src", "App.tsx");
const API = path.resolve(__dirname, "src", "lib", "api.ts");
const TYPES = path.resolve(__dirname, "src", "types.ts");

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs += 1;
}

let api;
try {
  const src = fs.readFileSync(LIB, "utf8").replace(/^export (?=(function|const|type) )/gm, "");
  const js = esbuild.transformSync(src + "\nthis.api = { peutRecevoirUnConjoint, raisonAjoutConjoint };", { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  api = ctx.api;
} catch (e) {
  console.log("⛔ coupleAffichage.ts n'a pas pu être monté :", e.message);
  process.exit(2);
}

const seule = { nature_fiche: "personne_seule", hektor_target_id: "84", archive: false, couple_json: null, relation_roles_json: ["mandant"] };
verifier("(1) une personne seule, active, connue de Hektor : le bouton", api.peutRecevoirUnConjoint(seule) === true);
verifier("(2) couple_json « aucun » : le bouton", api.peutRecevoirUnConjoint({ ...seule, couple_json: { etat: "aucun" } }) === true);
verifier("(3) couple_json en TEXTE « aucun » : le bouton", api.peutRecevoirUnConjoint({ ...seule, couple_json: '{"etat":"aucun"}' }) === true);
verifier("(4) une case vide connue (« vide ») : PAS de bouton (c'est « Compléter »)", api.peutRecevoirUnConjoint({ ...seule, couple_json: { etat: "vide", conjoint: { id: "1" } } }) === false);
verifier("(5) un conjoint nommé : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, couple_json: { etat: "nomme" } }) === false);
verifier("(6) une fiche couple (dans le nom) : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, nature_fiche: "couple" }) === false);
verifier("(7) un notaire : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, relation_roles_json: ["notaire_vendeur"] }) === false);
verifier("(8) une coquille : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, nature_fiche: "case_conjoint_vide" }) === false);
verifier("(9) sans numéro Hektor (née il y a une seconde) : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, hektor_target_id: null }) === false);
verifier("(10) archivée en booléen : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, archive: true }) === false);
verifier("(11) MUTANT : archivée en TEXTE « 1 » : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, archive: "1" }) === false);
verifier("(12) nature pas encore calculée : PAS de bouton", api.peutRecevoirUnConjoint({ ...seule, nature_fiche: null }) === false);
const raisons = ["cran_ferme", "meme_fiche", "conjoint_introuvable", "personne_archivee", "conjoint_archive", "notaire", "personne_pas_seule",
  "conjoint_pas_seul", "personne_deja_en_couple", "conjoint_deja_en_couple", "personne_sans_numero_hektor", "conjoint_sans_numero_hektor", "deja_en_cours"];
verifier("(13) chaque refus de la base a sa phrase (13 raisons, aucune en repli)",
  raisons.every((r) => !/^Refusé/.test(api.raisonAjoutConjoint(r))), raisons.filter((r) => /^Refusé/.test(api.raisonAjoutConjoint(r))).join(","));
verifier("(14) une raison inconnue est dite telle quelle", api.raisonAjoutConjoint("x_y") === "Refusé (x_y).");

// Les raisons de la base : chacune doit exister dans le patch (sinon l'écran dirait une phrase pour un refus qui n'existe pas).
const patch = fs.readFileSync(path.resolve(__dirname, "..", "..", "supabase", "patch_couple_phase3g_ajouter_conjoint_2026-11-03.sql"), "utf8");
verifier("(15) les 13 raisons sont celles que la base rend", raisons.every((r) => patch.includes(`'raison', '${r}'`)),
  raisons.filter((r) => !patch.includes(`'raison', '${r}'`)).join(","));

// Le câblage
const app = fs.readFileSync(APP, "utf8").replace(/\r\n/g, "\n");
const apiSrc = fs.readFileSync(API, "utf8");
const types = fs.readFileSync(TYPES, "utf8");
verifier("(16) le bouton suit le cran, le droit, l'absence de foyer et la personne seule",
  /const peutAjouterConjoint = ajoutConjointVisible && props\.canManageContacts && !foyer\n\s+&& natureLue\?\.pour === String\(props\.contact\.hektor_contact_id \?\? ''\)\.trim\(\)\n\s+&& peutRecevoirUnConjoint\(\{ \.\.\.props\.contact, nature_fiche: natureLue\.nature_fiche, couple_json: natureLue\.couple_json/.test(app)
  && /useCranCouplesVisible\('contacts_couples_ajout', props\.profileRole\)/.test(app)
  // la nature est LUE pour la fiche ouverte (la fiche venue d'un autre écran ne la porte pas toujours)
  && /void loadContactCoupleInfo\(id\)\n\s+\.then\(\(info\) => \{ if \(!annule && info\) setNatureLue\(\{ pour: id, nature_fiche: info\.nature_fiche, couple_json: info\.couple_json \}\) \}\)/.test(app));
verifier("(17) la fenêtre n'est rendue que si le bouton est permis", /\{ajoutConjointOuvert && peutAjouterConjoint \? \(\n\s+<AjouterConjointModal/.test(app));
const modale = app.slice(app.indexOf("function AjouterConjointModal("), app.indexOf("function appContactAgendaEmail("));
const iCreation = modale.indexOf("await createHektorContactJob(");
const iNumero = modale.indexOf("creation.payload_json?.app_identite");
const iRattache = modale.indexOf("await ajouterConjointOptimistic(");
verifier("(18) nouveau : la création PUIS le rattachement avec le numéro de la création",
  iCreation > 0 && iNumero > iCreation && iRattache > iNumero, `${iCreation} ${iNumero} ${iRattache}`);
verifier("(19) le nouveau conjoint naît PERSONNE SEULE (jamais une 2e paire par la création)", /personType: 'personne_seule'/.test(modale));
verifier("(20) un refus de la base est dit (pas avalé)", /if \(!resultat\.ok\) \{[\s\S]{0,300}raisonAjoutConjoint\(resultat\.raison\)/.test(modale));
verifier("(21) existante : la fiche elle-même est retirée des résultats",
  /options\.filter\(\(o\) => o\.hektor_contact_id !== props\.contact\.hektor_contact_id\)/.test(modale));
verifier("(22) l'appel de la base porte les deux numéros", /supabase\.rpc\('app_ajouter_conjoint_optimistic', \{\s*target_contact_id: input\.contactId\.trim\(\),\s*conjoint_contact_id: input\.conjointId\.trim\(\),/.test(apiSrc));
verifier("(23) le type est suivi (ConsoleJobType, liste des actions, gestes qui préviennent)",
  /\| 'link_hektor_conjoint'/.test(types) && /'archive_hektor_contact',\n  'link_hektor_conjoint',/.test(apiSrc.replace(/\r\n/g, "\n"))
  && /'archive_hektor_contact', 'link_hektor_conjoint',\n  'add_hektor_contact_search',/.test(app));
verifier("(24) les 8 habillages du suivi connaissent le type", (app.match(/'link_hektor_conjoint'/g) || []).length >= 8, String((app.match(/'link_hektor_conjoint'/g) || []).length));

console.log(echecs ? `\n${echecs} ECHEC(S)` : "\nTOUT VERT");
process.exit(echecs ? 1 : 0);
