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
  const js = esbuild.transformSync(src + "\nthis.api = { peutRecevoirUnConjoint, raisonAjoutConjoint, initialesDePlace, biensPartageables };", { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  api = ctx.api;
} catch (e) {
  console.log("⛔ coupleAffichage.ts n'a pas pu être monté :", e.message);
  process.exit(2);
}

verifier("(42) initiales : prénom puis nom, deux lettres, « ? » sans rien", api.initialesDePlace("julie", "bertrand") === "JB"
  && api.initialesDePlace("Jean-Pierre") === "JP" && api.initialesDePlace("", null) === "?" && api.initialesDePlace("Élodie", "Ørsted") === "ÉØ");
const biens = api.biensPartageables([
  { hektor_annonce_id: "1", role_contact: "mandant", titre_bien: "Maison Firminy" },
  { hektor_annonce_id: "1", role_contact: "proprietaire", titre_bien: "Maison Firminy" },
  { hektor_annonce_id: "2", role_contact: "acquereur", titre_bien: "Appartement" },
  { hektor_annonce_id: "3", role_contact: "Propriétaire", numero_mandat: "18836" }]);
verifier("(43) biens partagés : mandant ou propriétaire, un par bien, jamais un achat", biens.length === 2
  && biens[0].libelle === "Maison Firminy" && biens[1].libelle === "Mandat 18836", JSON.stringify(biens));
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

// ── Les défauts vus à l'essai réel du 03/11 (synthèse §54), corrigés ──
verifier("(25) la création du conjoint n'est PLUS suivie (elle ouvrait sa fiche et cachait la réussite)",
  !/props\.onJobCreated\?\.\(creation\)/.test(modale));
verifier("(26) le conjoint naît chez le négociateur de LA PERSONNE, repli sur le compte de la session si refusé",
  /hektorUserEmail: negociateurDeLaPersonne/.test(modale) && /forbidden_create_contact/.test(modale)
  && /hektorNegotiatorId: props\.contact\.hektor_negociateur_id/.test(modale));
verifier("(27) le choix nouveau / existant dit lequel est actif (aria-checked)",
  (modale.match(/role="radio" aria-checked=\{mode === '(nouveau|existant)'\}/g) || []).length === 2);
verifier("(28) l'e-mail RGPD est un vrai interrupteur de formulaire, dans son libellé",
  /<label className="ajc-switch">\s*<input type="checkbox" role="switch" checked=\{rgpd\}/.test(modale));
// ── La maquette validée le 03/11 (« le foyer, deux places ») ──
verifier("(36) la place du conjoint se remplit pendant la saisie (initiales de la saisie ou de la fiche choisie)",
  /initialesDePlace\(conjointPrenom, conjointNom\)/.test(modale) && /ajc-pair-lien\$\{placeRemplie \? ' pret' : ''\}/.test(modale));
verifier("(37) le bouton dit « Former le couple »", /\{ICONE_LIEN\}\{envoi \? 'Envoi…' : 'Former le couple'\}/.test(modale));
verifier("(38) la réussite propose « Voir la fiche » par la porte EXISTANTE de l'adresse (popstate)",
  /ouvrirFicheContactParAdresse\(fait\.conjointId\)/.test(modale) && /window\.dispatchEvent\(new PopStateEvent\('popstate'\)\)/.test(app));
verifier("(39) la fenêtre liste les biens que la fiche connaît déjà (aucune lecture de plus)",
  /biens=\{biensPartageables\(props\.relations\)\}/.test(app));
verifier("(40) sur la fiche : la carte « Ajouter un conjoint » à deux places, et le bloc doré « Compléter »",
  /<button className="fxf-ajout" type="button" onClick=\{\(\) => setAjoutConjointOuvert\(true\)\}>/.test(app)
  && /className=\{`fxf-foyer\$\{foyer\.affiche\.incomplet \? ' incomplet' : ''\}`\}/.test(app)
  && /<button className="fxf-completer" type="button" onClick=\{\(\) => \{ setCompleterConjoint\(true\); setEditing\(true\) \}\}>/.test(app));
verifier("(41) aucune fonction perdue : l'onglet du conjoint reste cliquable, la place vide ne l'est pas, le numéro de fiche reste affiché",
  /onClick=\{\(\) => \{ if \(!onglet\.vide\) setOngletFoyer\(numero\) \}\}/.test(app) && /<i>\{onglet\.vide \? 'place vide' : onglet\.sousTitre\}<\/i>/.test(app));
verifier("(29) la réussite reste à l'écran jusqu'à « Fermer »", /\{fait \? \(\s*<div className="ajc-done" role="status">/.test(modale));
verifier("(30) Échap ferme la fenêtre (sauf pendant l'envoi)", /event\.key === 'Escape'/.test(modale) && /const fermer = \(\) => \{ if \(!envoi\) props\.onClose\(\) \}/.test(modale));
verifier("(35) la fenêtre est rendue HORS de la fiche (portail) : `#fcx-root *` y remet marges et retraits à zéro",
  /return createPortal\(\s*<div className="ajc-overlay"/.test(modale) && /<\/div>,\s*document\.body,\s*\)/.test(modale));
verifier("(31) le style est chargé", /import '\.\/ajout-conjoint\.css'/.test(app) && fs.existsSync(path.resolve(__dirname, "src", "ajout-conjoint.css")));

// La civilité à place vide (« _ ») : la vraie fonction de l'écran, jouée.
try {
  const i = app.indexOf("const CIVILITES_DE_COUPLE: Record<string, string> = {");
  const f = app.indexOf("function contactCivilityToken(");
  const js = esbuild.transformSync(app.slice(i, f) + "\nthis.civ = civiliteAffichee;", { loader: "ts" }).code;
  const ctx = { String, Object };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  const c = ctx.civ;
  verifier("(32) « _ » n'est plus affiché (place vide des deux côtés)", c("_") === "");
  verifier("(33) « _Mr/Mme » -> « Mr/Mme », « M_ » -> « M. »", c("_Mr/Mme") === "Mr/Mme" && c("M_") === "M.");
  verifier("(34) TÉMOIN : les quatre codes et une civilité simple inchangés",
    c("M_Mme") === "M. et Mme" && c("Mme_M") === "Mme et M." && c("M.") === "M." && c("m_mme") === "m_mme" && c(null) === "");
} catch (e) {
  verifier("(32-34) la civilité de l'écran a pu être jouée", false, e.message);
}

console.log(echecs ? `\n${echecs} ECHEC(S)` : "\nTOUT VERT");
process.exit(echecs ? 1 : 0);
