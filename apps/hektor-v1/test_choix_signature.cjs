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
const app = fs.readFileSync(path.resolve(__dirname, "src", "App.tsx"), "utf8").split(String.fromCharCode(13)).join("");
// A.2 (06/11/2026) : la fenêtre refaite vit dans son propre fichier (maquette validée : habillage + points 1 à 4).
const fen = fs.readFileSync(path.resolve(__dirname, "src", "ChoixSignatureFenetre.tsx"), "utf8").split(String.fromCharCode(13)).join("");
controle("6. la fenêtre garde les TROIS voies visibles : une voie ouverte est un bouton, une voie fermée affiche sa raison",
  fen.includes("{ cle: 'youtrust',") && fen.includes("{ cle: 'hektor',") && fen.includes("{ cle: 'manuscrite',")
    && fen.includes('<button type="button" className="cxs-voie-main" onClick={v.agir}>') && fen.includes("{!ouvert && v.c.raison ? (")
    && app.includes("import ChoixSignatureFenetre from './ChoixSignatureFenetre'") && !app.includes("function ChoixSignatureFenetre("));
controle("6. ordre inchangé (point 5 abandonné) : Youtrust, puis Hektor, puis manuscrite, sans voie « recommandée »",
  fen.indexOf("{ cle: 'youtrust',") < fen.indexOf("{ cle: 'hektor',") && fen.indexOf("{ cle: 'hektor',") < fen.indexOf("{ cle: 'manuscrite',")
    && !/recommand/i.test(fen.split("\n").filter((l) => !l.trim().startsWith("//")).join("\n")));
controle("6. point 3 : « Régénérer le mandat » seulement sur la raison « pas fait par l'éditeur », et sans marquer le document remplacé",
  fen.includes("v.cle === 'youtrust' && v.c.raison === TEXTE_REGENERER && props.onRegenerer")
    && app.includes("pris: false, nouveau: true }") && app.includes("if (demande.nouveau) {") && app.includes("setCorrection(null)"));
controle("6. point 4 : « Voir le suivi » quand une signature Youtrust est en cours, vers l'ancre du suivi",
  fen.includes("choix.procedureEnCours === 'youtrust' && props.onVoirSuivi") && app.includes("getElementById(`sst-${document.id}`)")
    && fs.readFileSync(path.resolve(__dirname, "src", "SuiviSignatairesYoutrust.tsx"), "utf8").includes("id={`sst-${document.id}`}"));
controle("6. la fenêtre reçoit le bien, le n° de mandat et le négociateur aux QUATRE montages",
  (app.match(/numeroMandat=\{(props\.)?dossier\.numero_mandat != null \? String\((props\.)?dossier\.numero_mandat\) : null\}/g) || []).length === 4, String((app.match(/numeroMandat=/g) || []).length));

// 7. Points 1 et 2 : ce que la fenêtre montre du document et de ses signataires (code réel).
{
  const photo = { valide: true, mandants: [{ prenom: "Anne", nom: "EXEMPLE" }, { prenom: "Paul", nom: "EXEMPLE" }] };
  const ed = C.identiteDuDocument({ document_name: "Mandat de vente - 18420.pdf", document_type: "Mandat", source: "app", envoi_hektor_statut: "envoye", hektor_document_id: "x",
    metadata_json: { cree_le: "2026-11-06T11:40:00Z", signataires_du_pdf: photo } }, { numeroMandat: "18420", negociateur: "Claire NÉGOCIATRICE" });
  controle("7. mandat de l'éditeur : « Mandat de vente n° 18420 », généré le 06/11 à 12:40 (Paris), 3 cases, déposé",
    ed.titre === "Mandat de vente n° 18420" && ed.meta === "Généré dans l’app le 06/11 à 12:40, 3 cases de signature" && ed.depot.texte === "Déposé chez Hektor" && ed.depot.ton === "ok", J(ed));
  controle("7. qui signe : « Anne EXEMPLE et Paul EXEMPLE, les mandants, puis Claire NÉGOCIATRICE en dernier »",
    ed.signataires === "Signent : Anne EXEMPLE et Paul EXEMPLE, les mandants, puis Claire NÉGOCIATRICE en dernier.", ed.signataires);
  const depot = C.identiteDuDocument({ document_name: "Avenant au mandat - 18420.pdf", source: "app", envoi_hektor_statut: "a_envoyer", metadata_json: { signataires_du_pdf: { mandants: [{ prenom: "Anne", nom: "EXEMPLE" }] } } }, {});
  controle("7. avenant, dépôt en cours, un seul mandant, négociateur inconnu", depot.titre === "Avenant au mandat" && depot.depot.ton === "attente"
    && depot.signataires === "Signent : Anne EXEMPLE, le mandant, puis le négociateur en dernier.", J(depot));
  const hk = C.identiteDuDocument({ document_name: "Mandat (Avec saisie du numéro) (Vente)", document_type: "document", source: "hektor_console_immosign", metadata_json: { signature: { status: "pending", progress: "1/3" } } }, { numeroMandat: "18420" });
  controle("7. TÉMOIN modèle Hektor : son nom tel quel, « Modèle Hektor », « Chez Hektor », signataires choisis dans Hektor, « 1 signature sur 3 »",
    hk.titre === "Mandat (Avec saisie du numéro) (Vente)" && /^Modèle Hektor/.test(hk.meta) && hk.depot.texte === "Chez Hektor" && /se choisissent dans Hektor/.test(hk.signataires) && hk.progression === "1 signature sur 3", J(hk));
  controle("7. la raison « régénérez » de Youtrust est la constante qu'utilise le bouton du point 3",
    C.choixDeSignature(modele(), on).youtrust.raison === C.TEXTE_REGENERER);
}
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
