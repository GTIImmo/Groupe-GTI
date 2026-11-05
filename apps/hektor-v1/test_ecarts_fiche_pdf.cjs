#!/usr/bin/env node
"use strict";
/**
 * A.2 LOT 6b P5-P6 — COMPARER CE QU'UN PDF IMPRIME : « ce qui a changé » (ancien → nouveau PDF) et
 * « la fiche a changé depuis ce PDF » (PDF → fiche d'aujourd'hui).                                05/11/2026
 *
 * On EXÉCUTE le code réel : src/lib/ecartsFichePdf.ts, transformé par esbuild et joué par vm. Données FICTIVES.
 * Et on vérifie les branchements : mêmes clés que le worker (contenu_imprime), la fiche passée aux trois panneaux
 * Documents, l'éditeur qui ne compare pas un PDF qu'il vient de générer, la trace envoyée au worker.
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_ecarts_fiche_pdf.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const SRC = path.resolve(__dirname, "src", "lib", "ecartsFichePdf.ts");
const APP = path.resolve(__dirname, "src", "App.tsx");
const FENETRE = path.resolve(__dirname, "src", "EnvoiSignatureYoutrust.tsx");
const API = path.resolve(__dirname, "src", "lib", "api.ts");
const WORKER = path.resolve(__dirname, "..", "..", "Console", "console_job_worker.js");
const echecs = [];
const controle = (nom, ok, detail) => {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
};

let lib;
try {
  const { code } = esbuild.transformSync(fs.readFileSync(SRC, "utf8"), { loader: "ts", format: "cjs" });
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports });
  lib = module.exports;
} catch (e) {
  console.log(`⛔ ${e.message}`);
  process.exit(2);
}
const { ecartsAvecLaFiche, ceQuiAChange, CHAMPS_DE_LA_FICHE } = lib;
const J = (v) => JSON.stringify(v);

const m = (civilite, prenom, nom) => ({ civilite, prenom, nom });
const photo = (...mandants) => ({ version: 1, valide: true, problemes: [], reperes_attendus: 2 * mandants.length + 1, mandants: mandants.map((x, i) => ({ rang: i + 1, ...x, email: null, telephone: null, hektor_contact_id: null })) });
const CONTENU = { version: 1, numero_mandat: "24517", type_mandat: "Mandat de vente", bien_titre: "Maison", bien_adresse: "12 rue des Essais 42700 Firminy",
  nombre_pieces: "5", surface_habitable: "95", surface_terrain: "600", prix_vente: "205000", prix_net_vendeur: "195000", honoraires_ttc: "10000",
  date_signature: "04/11/2026", honoraires_charge: "mandant", clause_particuliere: "Clause A", execution_anticipee: null, inclure_couverture: true };
const ficheDe = (contenu, ...mandants) => ({ mandants, contenu });
const JEAN = m("M.", "Jean", "DUPOND"), CLAIRE = m("Mme", "Claire", "MARTIN"), SOPHIE = m("Mme", "Sophie", "DUPONT");

// 1. Un PDF fidèle à la fiche
{
  const r = ecartsAvecLaFiche(photo(JEAN, CLAIRE), CONTENU, ficheDe({ ...CONTENU }, JEAN, CLAIRE));
  controle("1. un PDF fidèle à la fiche : aucun écart", r.lignes.length === 0 && r.resume.length === 0 && r.prixCompare === true, J(r));
}
// 2. Deux écritures du même contenu
{
  const fiche = ficheDe({ ...CONTENU, prix_vente: "205 000 €", bien_adresse: "12  rue des essais 42700 FIRMINY", honoraires_ttc: "10000,00" },
    m("M.", "Jean", "Dupond"), m("Mme", " Claire", "MARTIN "));
  const r = ecartsAvecLaFiche(photo(JEAN, CLAIRE), CONTENU, fiche);
  controle("2. espaces, casse, « 205 000 € » et « 10000,00 » : pas un écart", r.lignes.length === 0, J(r.lignes));
  controle("2 bis. TÉMOIN : ces écritures sont bien différentes en texte brut (le contrôle 2 éprouve la normalisation)",
    fiche.contenu.prix_vente !== CONTENU.prix_vente && fiche.contenu.bien_adresse !== CONTENU.bien_adresse);
}
// 3-6. Les vrais écarts
{
  const r = ecartsAvecLaFiche(photo(JEAN, CLAIRE), CONTENU, ficheDe({ ...CONTENU }, JEAN, CLAIRE, SOPHIE));
  controle("3. une mandante AJOUTÉE sur la fiche : dite, et « sans Mme Sophie DUPONT » dans la confirmation",
    r.lignes.length === 1 && r.lignes[0].plus === "＋ Mme Sophie DUPONT" && J(r.resume) === J(["sans Mme Sophie DUPONT"]), J(r));
}
{
  const r = ecartsAvecLaFiche(photo(JEAN, CLAIRE), CONTENU, ficheDe({ ...CONTENU }, JEAN));
  controle("4. une mandante RETIRÉE de la fiche : dite, et « avec Mme Claire MARTIN »",
    r.lignes.length === 1 && r.lignes[0].moins === "− Mme Claire MARTIN" && J(r.resume) === J(["avec Mme Claire MARTIN"]), J(r));
}
{
  const r = ecartsAvecLaFiche(photo(JEAN), CONTENU, ficheDe({ ...CONTENU }, m("M.", "Jean", "DUPONT")));
  controle("5. un nom CORRIGÉ sur la fiche : PDF « DUPOND », fiche « DUPONT »",
    r.lignes.length === 1 && r.lignes[0].k === "Mandant 1" && r.lignes[0].avant === "M. Jean DUPOND" && r.lignes[0].apres === "M. Jean DUPONT"
      && J(r.resume) === J(["au nom de M. Jean DUPOND"]), J(r));
}
{
  const r = ecartsAvecLaFiche(photo(JEAN), CONTENU, ficheDe({ ...CONTENU, prix_vente: "199000" }, JEAN));
  const l = r.lignes[0] || {};
  controle("6. le PRIX a changé : PDF 205 000 €, fiche 199 000 €, et « Prix FAI 205 000 € » dans la confirmation",
    r.lignes.length === 1 && l.k === "Prix FAI" && /^205\D000 €$/.test(l.avant) && /^199\D000 €$/.test(l.apres) && /^Prix FAI 205\D000 €$/.test(r.resume[0]), J(r));
}
// 7-8. Ce qui ne doit PAS sonner
{
  const r = ecartsAvecLaFiche(photo(JEAN), CONTENU, ficheDe({ ...CONTENU, prix_vente: null, honoraires_ttc: "" }, JEAN));
  controle("7. une fiche MUETTE (prix, honoraires vides) ne contredit pas le PDF", r.lignes.length === 0, J(r.lignes));
}
{
  const r = ecartsAvecLaFiche(photo(JEAN), CONTENU, ficheDe({ ...CONTENU, date_signature: "05/11/2026", honoraires_charge: "acquereur", clause_particuliere: "Autre", inclure_couverture: false }, JEAN));
  controle("8. date, charge, clause, couverture (SAISIES dans l'éditeur) ne sont pas comparées", r.lignes.length === 0, J(r.lignes));
  controle("8 bis. …et la liste des champs comparés ne les contient pas",
    !["date_signature", "honoraires_charge", "clause_particuliere", "execution_anticipee", "inclure_couverture", "etat_occupation"].some((c) => CHAMPS_DE_LA_FICHE.includes(c)));
}
// 9-10. Les manques
{
  const r = ecartsAvecLaFiche(photo(JEAN), null, ficheDe({ ...CONTENU, prix_vente: "1" }, JEAN, SOPHIE));
  controle("9. PDF d'avant le 05/11 (sans contenu imprimé) : seuls les mandants, et il le dit (prixCompare = false)",
    r.lignes.length === 1 && r.lignes[0].plus && r.prixCompare === false, J(r));
}
{
  const r = ecartsAvecLaFiche(photo(JEAN), CONTENU, null);
  const r2 = ecartsAvecLaFiche(null, CONTENU, ficheDe({ ...CONTENU }, JEAN));
  controle("10. sans fiche, ou sans photo : rien n'est affirmé", r.lignes.length === 0 && r2.lignes.length === 0);
}
// 11. P5 déplacé : « ce qui a changé » rend les mêmes lignes qu'avant
{
  const r = ceQuiAChange(photo(JEAN, CLAIRE), photo(m("M.", "Jean", "DUPONT"), CLAIRE, SOPHIE),
    { ...CONTENU, honoraires_charge: "acquereur" }, { ...CONTENU, prix_vente: "199000" });
  const k = r.lignes.map((l) => l.k);
  controle("11. P5 (déplacé dans le module) : nom, mandant ajouté, signataires 3 → 4, prix, charge",
    r.compare && J(k) === J(["Mandant 1", "Mandants", "Signataires", "Prix FAI", "Charge des honoraires"]) && r.lignes[2].note === "· donc 4 crédits au lieu de 3", J(r.lignes));
}

// 12. Les branchements
const app = fs.readFileSync(APP, "utf8"), fenetre = fs.readFileSync(FENETRE, "utf8"), api = fs.readFileSync(API, "utf8"), worker = fs.readFileSync(WORKER, "utf8");
{
  const i = worker.indexOf("function contenuImprimeDuPdf(");
  const corps = i < 0 ? "" : worker.slice(i, worker.indexOf("\n}", i));
  const manquent = CHAMPS_DE_LA_FICHE.filter((c) => !new RegExp(`\\b${c}:`).test(corps));
  const j = app.indexOf("function ficheDuJourPourEnvoi(");
  const fiche = j < 0 ? "" : app.slice(j, app.indexOf("\n}", j));
  const manquentFiche = CHAMPS_DE_LA_FICHE.filter((c) => !new RegExp(`\\b${c}:`).test(fiche));
  controle("12. les champs comparés existent sous le MÊME nom dans le contenu imprimé du worker", corps && !manquent.length, manquent.join(", "));
  controle("12. …et dans la fiche d'aujourd'hui de l'écran (ficheDuJourPourEnvoi)", fiche && !manquentFiche.length, manquentFiche.join(", "));
}
controle("12. les TROIS panneaux Documents reçoivent la fiche du bien",
  (app.match(/<ConsoleDocumentsPanel dossier=\{dossier\} ficheDuMandat=\{\{ detail: props\.detail, contacts: props\.contacts, address: props\.address \}\}/g) || []).length === 3
  && (app.match(/<ConsoleDocumentsPanel /g) || []).length === 3);
controle("12. l'éditeur ne compare PAS un PDF qu'il vient de générer", /ficheDuJour=\{envoiJusteGenere \? null : ficheDuJourPourEnvoi\(initialDraft\)\}/.test(app)
  && (app.match(/setEnvoiJusteGenere\(true\)/g) || []).length === 2 && /setEnvoiJusteGenere\(false\)/.test(app));
controle("12. « Envoyer quand même » passe par une confirmation, et la trace part dans la demande",
  /setConfirmerEcarts\(true\)/.test(fenetre) && /Oui, envoyer ce PDF tel quel/.test(fenetre) && /ecartsAcceptes:/.test(fenetre)
  && /ecarts_acceptes: input\.ecartsAcceptes/.test(api) && /payload\.ecarts_acceptes/.test(worker));

console.log(echecs.length ? `\n⛔ ${echecs.length} contrôle(s) en échec.` : "\n✅ Tous les contrôles sont verts.");
process.exit(echecs.length ? 1 : 0);
