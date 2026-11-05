#!/usr/bin/env node
"use strict";
/**
 * A.2 LOT 6b P7 — LE COUPLE DANS L'ÉDITEUR DU MANDAT (D34, D35, D36).                          05/11/2026
 *
 * On EXÉCUTE le code réel : src/lib/conjointsDuMandat.ts et src/lib/ecartsFichePdf.ts (esbuild, joués par vm), et le
 * contenu imprimé du worker (découpé). Données FICTIVES. Puis on vérifie les branchements dans App.tsx.
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_conjoints_du_mandat.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const echecs = [];
const controle = (nom, ok, detail) => {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
};
const charger = (fichier) => {
  const { outputFiles } = esbuild.buildSync({ entryPoints: [path.resolve(__dirname, "src", "lib", fichier)], bundle: true, write: false, format: "cjs", platform: "neutral" });
  const module = { exports: {} };
  vm.runInNewContext(outputFiles[0].text, { module, exports: module.exports });
  return module.exports;
};
let C, E;
try { C = charger("conjointsDuMandat.ts"); E = charger("ecartsFichePdf.ts"); } catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const J = (v) => JSON.stringify(v);
const { ficheDuMandant, situationsDesConjoints, mandantsImprimes, mandantsSansPrenomOuNom } = C;

const carte = (id, civilite, prenom, nom) => ({ id, civilite, prenom, nom, qualite: "Mandant", adresse: "12 rue des Essais", telephone: "", email: "" });
const JEAN = carte("detail-contact-1-603953-member-603953", "M.", "Jean", "DUPONT");
const SOPHIE = carte("detail-contact-1-603953-member-603954", "Mme", "Sophie", "DUPONT");
const CLAIRE = carte("detail-contact-2-604000", "Mme", "Claire", "MARTIN");
const fiche = (n, nature, couple, civ) => [n, { hektor_target_id: n, nature_fiche: nature, couple_json: couple, civilite_app: civ || null }];
// Forme MESURÉE le 05/11 : `id` = NOTRE numéro (10 xxx xxx), `hektor_id` = celui de Hektor (celui des cartes).
const nomme = (hektorId, prenom, nom, extra = {}) => ({ etat: "nomme", conjoint: { id: `10${hektorId}`, hektor_id: hektorId, prenom, nom, email: "conjoint@exemple.fr", telephone: "0600000002", archive: "0", ...extra } });

// 1. Le numéro de fiche d'une carte
controle("1. numéro de fiche : membre d'un couple, carte simple, carte ajoutée à la main",
  ficheDuMandant(JEAN.id) === "603953" && ficheDuMandant(CLAIRE.id) === "604000" && ficheDuMandant("mandant-1784905052078") === null
    && ficheDuMandant("conjoint-603953-member-700002") === "700002");

// 2. (a) D34 : conjoint nommé ET lié
{
  const fiches = new Map([fiche("603953", "couple", nomme("603954", "Sophie", "DUPONT")), fiche("603954", "conjoint", null), fiche("604000", "personne_seule", null)]);
  const s = situationsDesConjoints([JEAN, SOPHIE, CLAIRE], fiches);
  controle("2. (a) conjoint lié au bien : UNE question « lie », pas deux (la fiche du conjoint ne repose pas la question)",
    s.length === 1 && s[0].cas === "lie" && s[0].principal === "603953" && s[0].conjoint === "603954", J(s));
  const parDefaut = mandantsImprimes([JEAN, SOPHIE, CLAIRE], new Set(), new Map(), s);
  controle("2. (a) par défaut, il est imprimé (comme aujourd'hui)", J(parDefaut.map((m) => m.prenom)) === J(["Jean", "Sophie", "Claire"]));
  const retire = mandantsImprimes([JEAN, SOPHIE, CLAIRE], new Set(["603954"]), new Map(), s);
  controle("2. (a) « Non » : retiré du DOCUMENT, les autres gardent leur ordre", J(retire.map((m) => m.prenom)) === J(["Jean", "Claire"]));
  // P6 ne doit pas crier sur un retrait EXPRÈS
  const photo = { version: 1, valide: true, problemes: [], reperes_attendus: 5, mandants: retire.map((m, i) => ({ rang: i + 1, civilite: m.civilite, prenom: m.prenom, nom: m.nom, email: null, telephone: null, hektor_contact_id: null })) };
  const ficheDuJour = { mandants: [JEAN, SOPHIE, CLAIRE].map((m) => ({ civilite: m.civilite, prenom: m.prenom, nom: m.nom, id: m.id })), contenu: {} };
  const avecNote = E.ecartsAvecLaFiche(photo, { conjoints_retires: ["603954"] }, ficheDuJour);
  const sansNote = E.ecartsAvecLaFiche(photo, { conjoints_retires: [] }, ficheDuJour);
  controle("2. (a) le retrait noté dans le PDF : P6 ne le prend PAS pour un écart", avecNote.lignes.length === 0, J(avecNote.lignes));
  controle("2. (a) TÉMOIN : sans la note, P6 le signalerait (le contrôle ci-dessus éprouve bien la note)", sansNote.lignes.length > 0, J(sansNote.lignes));
}

// 3. (b) D35 : conjoint nommé mais NON lié
{
  const fiches = new Map([fiche("604000", "couple", nomme("700002", "Paul", "MARTIN")), fiche("700002", "conjoint", null, "M.")]);
  const s = situationsDesConjoints([CLAIRE, JEAN], fiches);
  const nl = s[0] || {};
  controle("3. (b) conjoint connu mais pas lié : question « non_lie », avec sa carte prête (civilité de SA fiche, e-mail du couple)",
    s.length === 1 && nl.cas === "non_lie" && nl.mandant.civilite === "M." && nl.mandant.prenom === "Paul" && nl.mandant.email === "conjoint@exemple.fr"
      && ficheDuMandant(nl.mandant.id) === "700002", J(s));
  controle("3. (b) par défaut, il n'est PAS imprimé (comme aujourd'hui)", J(mandantsImprimes([CLAIRE, JEAN], new Set(), new Map(), s).map((m) => m.prenom)) === J(["Claire", "Jean"]));
  const ajoutes = new Map([["700002", nl.mandant]]);
  controle("3. (b) « Oui » (lien posé) : imprimé JUSTE APRÈS son principal",
    J(mandantsImprimes([CLAIRE, JEAN], new Set(), ajoutes, s).map((m) => m.prenom)) === J(["Claire", "Paul", "Jean"]));
  const PAUL_RELU = carte("detail-contact-3-700002", "M.", "Paul", "MARTIN");
  const sRelu = situationsDesConjoints([CLAIRE, PAUL_RELU, JEAN], fiches);
  controle("3. (b) la fiche relue porte le conjoint : jamais deux fois, et la question devient « lie »",
    J(mandantsImprimes([CLAIRE, PAUL_RELU, JEAN], new Set(), ajoutes, sRelu).map((m) => m.prenom)) === J(["Claire", "Paul", "Jean"]) && sRelu[0].cas === "lie");
}

// 3 bis. Les numéros et l'archive
{
  const fiches = new Map([fiche("604000", "couple", nomme("700002", "Paul", "MARTIN"))]);
  const s = situationsDesConjoints([CLAIRE, carte("detail-contact-3-10700002", "M.", "Paul", "MARTIN")], fiches);
  controle("3 bis. le conjoint se reconnaît par son numéro HEKTOR (hektor_id), pas par notre numéro (id)",
    s[0]?.cas === "non_lie" && s[0].conjoint === "700002", JSON.stringify(s));
  const arch = situationsDesConjoints([CLAIRE], new Map([fiche("604000", "couple", nomme("700002", "Paul", "MARTIN", { archive: "1" }))]));
  controle("3 bis. un conjoint ARCHIVÉ est signalé (l'écran ne propose pas de le lier)", arch[0]?.archive === true);
  const sansNumero = situationsDesConjoints([CLAIRE], new Map([fiche("604000", "couple", { etat: "nomme", conjoint: { id: "10700002", prenom: "Paul" } })]));
  controle("3 bis. sans numéro Hektor : aucune question (on ne lie pas une fiche qu'on ne sait pas viser)", sansNumero.length === 0);
}

// 4-6. Les autres cas
{
  const fiches = new Map([fiche("604000", "couple", { etat: "vide", conjoint: { id: "604001" } })]);
  const s = situationsDesConjoints([CLAIRE], fiches);
  controle("4. place de conjoint vide : « inconnu », le mandant signe seul", s.length === 1 && s[0].cas === "inconnu" && mandantsImprimes([CLAIRE], new Set(), new Map(), s).length === 1);
}
{
  const fiches = new Map([fiche("604000", "notaire", nomme("1", "X", "Y")), fiche("603953", "personne_seule", null), fiche("603954", "case_conjoint_vide", nomme("2", "A", "B"))]);
  controle("5. notaire, personne seule sans couple, case vide : aucune question", situationsDesConjoints([CLAIRE, JEAN, SOPHIE], fiches).length === 0);
  controle("5. fiche illisible (lecture ratée) : aucune question, le mandat reste celui d'aujourd'hui", situationsDesConjoints([CLAIRE], new Map()).length === 0);
  const ancienne = new Map([fiche("604000", "personne_seule", { etat: "vide", conjoint: { id: "604001" } }), fiche("603953", "personne_seule", nomme("603954", "Sophie", "DUPONT"))]);
  controle("5. ⛔ règle du 02/11 : une « personne seule » au couple_json vide ou nommé n'est PAS un couple (aucune question)",
    situationsDesConjoints([CLAIRE, JEAN], ancienne).length === 0);
}
{
  const fiches = new Map([fiche("604000", "couple", JSON.stringify(nomme("700002", "Paul", "MARTIN")))]);
  controle("6. couple_json en texte JSON : lu pareil", situationsDesConjoints([CLAIRE], fiches)[0]?.cas === "non_lie");
}

// 7. (c) D36 : prénom / nom
{
  const COUPLE_NOM = carte("detail-contact-4-605000", "", "", "M. et Mme DURAND");
  const SANS_NOM = carte("detail-contact-5-605001", "M.", "Luc", "");
  const r = mandantsSansPrenomOuNom([JEAN, COUPLE_NOM, SANS_NOM]);
  controle("7. (c) un couple écrit dans un seul nom et un mandant sans nom sont listés, avec leur rang",
    r.length === 2 && /^mandant 2 .*prénom manquant$/.test(r[0]) && /^mandant 3 .*nom manquant$/.test(r[1]), J(r));
  controle("7. (c) des mandants complets ne bloquent rien", mandantsSansPrenomOuNom([JEAN, CLAIRE]).length === 0);
}

// 8. Le worker range la note des retraits dans ce que le PDF imprime
{
  const w = fs.readFileSync(path.resolve(__dirname, "..", "..", "Console", "console_job_worker.js"), "utf8");
  const tranche = (d) => { const i = w.indexOf(d); return i < 0 ? "" : w.slice(i, w.indexOf("\n}", i) + 2); };
  let ci = null;
  try {
    // eslint-disable-next-line no-new-func
    const f = new Function(`${tranche("function cleanString(")}\n${tranche("function contenuImprimeDuPdf(")}\nreturn contenuImprimeDuPdf;`)();
    ci = { avec: f({ render_payload: { conjoints_retires: ["603954", ""] } }), sans: f({ render_payload: {} }) };
  } catch (e) { ci = { erreur: e.message }; }
  controle("8. worker : contenu_imprime.conjoints_retires = la liste (vide écartée), [] sans retrait",
    ci && J(ci.avec && ci.avec.conjoints_retires) === J(["603954"]) && J(ci.sans && ci.sans.conjoints_retires) === J([]), J(ci));
}

// 9. Les branchements dans App.tsx
{
  const app = fs.readFileSync(path.resolve(__dirname, "src", "App.tsx"), "utf8");
  const i = app.indexOf("function MandatDocumentEditor(");
  const ed = app.slice(i, app.indexOf("\n}\n", i));
  controle("9. éteint : le brouillon d'avant, à l'identique", /youtrustActif \? \{ \.\.\.draft, mandants: mandantsImprimes\(/.test(ed) && /: draft\),/.test(ed));
  controle("9. l'aperçu ET la génération impriment draftDuDocument",
    (ed.match(/avenantPreviewHtml\(draftDuDocument/g) || []).length === 2 && (ed.match(/mandatPreviewHtml\(draftDuDocument/g) || []).length === 2 && !/mandatPreviewHtml\(draft,/.test(ed));
  controle("9. la charge de rendu porte la liste des conjoints retirés", /conjoints_retires: Array\.from\(conjointsRetires\)/.test(ed));
  const blocage = ed.indexOf("const manquants = reperes ? mandantsSansPrenomOuNom(draftDuDocument.mandants)");
  const job = ed.indexOf("await createGenerateMandatPdfJob(");
  controle("9. (c) le blocage est relu au clic avec l'interrupteur, et AVANT le travail de génération", blocage > 0 && job > blocage);
  controle("9. (b) le lien passe par la porte « lier comme mandant », après une confirmation",
    /createLinkHektorMandantJobOptimistic\(\{ dossier: props\.dossier, contactId: s\.conjoint/.test(ed) && /setLienAConfirmer\(s\.conjoint\)/.test(ed) && /Lier et l’inclure/.test(ed));
}

console.log(echecs.length ? `\n⛔ ${echecs.length} contrôle(s) en échec.` : "\n✅ Tous les contrôles sont verts.");
process.exit(echecs.length ? 1 : 0);
