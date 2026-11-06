#!/usr/bin/env node
"use strict";
/**
 * A.2 P8-2 — UN SEUL BOUTON « SIGNATURE », TROIS CHOIX (D42).                                              06/11/2026
 * On EXÉCUTE le code réel (src/lib/choixSignature.ts, esbuild + vm), puis on vérifie les branchements dans App.tsx.
 * Données FICTIVES. NE LANCE NI SERVEUR NI REQUÊTE.     node apps/hektor-v1/test_choix_signature.cjs
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
let C;
try {
  const { outputFiles } = esbuild.buildSync({ entryPoints: [path.resolve(__dirname, "src", "lib", "choixSignature.ts")], bundle: true, write: false, format: "cjs", platform: "neutral" });
  const module = { exports: {} };
  vm.runInNewContext(outputFiles[0].text, { module, exports: module.exports });
  C = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const J = (v) => JSON.stringify(v);
const on = { youtrustActif: true, manuscriteActive: true };

// Un mandat de l'éditeur (photo), né chez nous, déposé chez Hektor.
const mandat = (extra = {}, md = {}) => ({ document_name: "Mandat de vente - 18420.pdf", document_type: "Mandat", source: "app", hektor_document_id: "abc", envoi_hektor_statut: "envoye",
  ...extra, metadata_json: { signataires_du_pdf: { valide: true }, ...md } });
// Un modèle Hektor (ImmoSign), sans photo.
const modele = (sig = { status: "to_send", procedure_id: null }) => ({ document_name: "Mandat (Avec saisie du numéro) (Vente)", document_type: "document", source: "hektor_console_immosign", hektor_document_id: "h1", metadata_json: { signature: sig } });

// 1. Le cas nominal : les trois choix ouverts.
{
  const c = C.choixDeSignature(mandat(), on);
  controle("1. mandat de l'éditeur, déposé chez Hektor : les TROIS choix sont possibles", c.youtrust.possible && c.hektor.possible && c.manuscrite.possible, J(c));
}
// 2. ⭐ La consigne de Frédéric : une procédure lancée -> le bouton RESTE, le message dit d'annuler d'abord.
{
  const cy = C.choixDeSignature(mandat({}, { signature: { provider: "youtrust", status: "pending" } }), on);
  controle("2. Youtrust en cours : manuscrite FERMÉE avec le message « annulez-la d'abord »", !cy.manuscrite.possible && /annulez-la d’abord pour pouvoir marquer ce document signé à la main/.test(cy.manuscrite.raison), J(cy.manuscrite));
  controle("2. ...et ni Youtrust ni Hektor ne repartent (jamais deux procédures)", !cy.youtrust.possible && !cy.hektor.possible && cy.procedureEnCours === "youtrust");
  const ci = C.choixDeSignature(modele({ status: "pending", procedure_id: 851 }), on);
  controle("2. ImmoSign en attente : manuscrite fermée, le message parle d'ImmoSign et du bouton « Annuler »", !ci.manuscrite.possible && /ImmoSign/.test(ci.manuscrite.raison) && /Annuler/.test(ci.manuscrite.raison) && ci.procedureEnCours === "immosign", J(ci.manuscrite));
  const ca = C.choixDeSignature(modele({ status: "cancelled", procedure_id: null }), on);
  controle("2. TÉMOIN : une procédure ANNULÉE ne bloque plus rien", ca.procedureEnCours === null && ca.hektor.possible && ca.manuscrite.possible, J(ca));
}
// 3. Youtrust : l'interrupteur, la photo.
{
  const off = C.choixDeSignature(mandat(), { youtrustActif: false, manuscriteActive: true });
  controle("3. interrupteur Youtrust éteint : Youtrust fermé, « pas encore activée »", !off.youtrust.possible && /pas encore activée/.test(off.youtrust.raison) && off.hektor.possible);
  const m = C.choixDeSignature(modele(), on);
  controle("3. un modèle Hektor (sans photo) : Youtrust fermé « régénérez », Hektor ouvert", !m.youtrust.possible && /régénérez/.test(m.youtrust.raison) && m.hektor.possible, J(m));
}
// 4. Hektor : le document doit être CHEZ Hektor (dépôt confirmé).
{
  const enCours = C.choixDeSignature(mandat({ envoi_hektor_statut: "a_envoyer", hektor_document_id: null }), on);
  controle("4. né chez nous, dépôt en cours : Hektor fermé « dépôt en cours », Youtrust ouvert", !enCours.hektor.possible && /Dépôt chez Hektor en cours/.test(enCours.hektor.raison) && enCours.youtrust.possible, J(enCours.hektor));
  const echec = C.choixDeSignature(mandat({ envoi_hektor_statut: "echec", hektor_document_id: null }), on);
  controle("4. dépôt en échec : Hektor fermé, « repris à 12:30 »", !echec.hektor.possible && /12:30/.test(echec.hektor.raison));
  const seul = C.choixDeSignature(mandat({ envoi_hektor_statut: "sans_hektor", hektor_document_id: null }), on);
  controle("4. mandat Youtrust seul (sans_hektor) : Hektor fermé « pas chez Hektor »", !seul.hektor.possible && /pas chez Hektor/.test(seul.hektor.raison));
}
// 5. Rien ne se signe deux fois ; un PDF remplacé ne se signe pas ; la manuscrite seulement sur mandat / avenant.
{
  const s = C.choixDeSignature(mandat({}, { signature: { provider: "youtrust", status: "signed" } }), on);
  controle("5. déjà signé : les trois fermés", s.signe && !s.youtrust.possible && !s.hektor.possible && !s.manuscrite.possible);
  const r = C.choixDeSignature(mandat({}, { remplace: { le: "2026-11-06" } }), on);
  controle("5. PDF remplacé : les trois fermés, « signez le nouveau »", !r.youtrust.possible && !r.hektor.possible && !r.manuscrite.possible && /signez le nouveau/.test(r.youtrust.raison));
  const dpe = C.choixDeSignature({ document_name: "DPE.pdf", document_type: "document", source: "hektor_console_uploaded_private", hektor_document_id: "d", metadata_json: {} }, on);
  controle("5. un DPE : manuscrite fermée (mandat / avenant seulement), Hektor ouvert", !dpe.manuscrite.possible && dpe.hektor.possible);
  const av = C.choixDeSignature(mandat({ document_name: "Avenant au mandat - 18420.pdf" }), on);
  controle("5. un avenant de l'éditeur : les trois ouverts", av.youtrust.possible && av.hektor.possible && av.manuscrite.possible);
}

// 6. LES BRANCHEMENTS dans App.tsx.
const app = fs.readFileSync(path.resolve(__dirname, "src", "App.tsx"), "utf8");
controle("6. la fenêtre de choix existe et garde les TROIS boutons visibles (un choix fermé dit sa raison)",
  /function ChoixSignatureFenetre\(/.test(app) && /onClick=\{\(\) => \{ if \(o\.c\.possible\) \{ setRaison\(null\); o\.agir\(\) \} else setRaison\(o\.c\.raison\) \}\}/.test(app));
controle("6. allumée seulement si un interrupteur de la signature l'est (sinon l'écran d'avant)",
  /return \{ actif: youtrust \|\| chezNous, youtrust \}/.test(app) && /loadAppSettingActive\('mandat_nait_chez_nous'\)\.then/.test(app));
controle("6. la liste Documents : un seul bouton « Signature » quand le choix est allumé, les anciens sinon",
  /\{choixSignature\.actif \? \(signature\?\.status !== 'signed' && !documentRemplace\(document\) \? \(/.test(app) && /onClick=\{\(\) => setChoixDoc\(document\)\}/.test(app));
controle("6. la fenêtre est montée dans les DEUX présentations de la liste", (app.match(/\{\/\* A\.2 P8-2 : le choix a trois signatures\. \*\/\}/g) || []).length === 2);
controle("6. le suivi du mandat ouvre le même choix (et sa signature manuscrite a le même texte)",
  /onClick=\{choixSignature\.actif \? \(\) => setChoixDoc\(document\) : openHektorSignature\}/.test(app) && /async function signeALaMain\(document: ConsoleDocument\)/.test(app));
controle("6. l'éditeur ouvre le choix juste après la génération, et le met à jour jusqu'au dépôt confirmé",
  /if \(fresh && \(youtrustGen \|\| chezNousGen\)\) \{/.test(app) && /setChoixApresGen\(\(ouvert\) => \(ouvert && ouvert\.id === fresh\.id \? fresh : ouvert\)\)/.test(app));
const sql = fs.readFileSync(path.resolve(__dirname, "..", "..", "supabase", "patch_a2_p8_2_signe_main_garde_2026-11-06.sql"), "utf8");
controle("6. la même règle CÔTÉ BASE est prête (patch : refus si Youtrust ou ImmoSign en attente)",
  /v_sig ->> 'status' = 'pending'/.test(sql) && /v_sig ->> 'provider' = 'youtrust' or nullif/.test(sql));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
