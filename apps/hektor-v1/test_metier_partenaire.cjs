#!/usr/bin/env node
"use strict";
/**
 * CHANTIER PARTENAIRES · LOT 3, PIÈCE 3.1 — LE BLOC « MÉTIER » : LES RÈGLES.   05/11/2026
 *
 * On EXÉCUTE le code réel : src/lib/metierPartenaire.ts, transformé par esbuild et joué par vm. Données SYNTHÉTIQUES.
 * Et on vérifie le branchement dans App.tsx (le cran `partenaires_ecran`, le bloc sous le statut).
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_metier_partenaire.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const SRC = path.resolve(__dirname, "src", "lib", "metierPartenaire.ts");
const BLOC = path.resolve(__dirname, "src", "MetierPartenaire.tsx");
const APP = path.resolve(__dirname, "src", "App.tsx");
const echecs = [];
const controle = (nom, ok, detail) => {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
};

let api;
try {
  const { code } = esbuild.transformSync(fs.readFileSync(SRC, "utf8"), { loader: "ts", format: "cjs" });
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports });
  api = module.exports;
} catch (e) {
  console.log(`⛔ ${e.message}`);
  process.exit(2);
}
const { resumerMetiers, origineDuMetier } = api;
const J = (v) => JSON.stringify(v);

controle("(1) aucune ligne = rien à montrer", resumerMetiers([]) === null && resumerMetiers(null) === null);
controle("(2) un syndic de Hektor", J(resumerMetiers([{ metier: "syndic", source: "hektor" }])) === J({ titre: "Syndic", origine: "D'après Hektor" }),
  J(resumerMetiers([{ metier: "syndic", source: "hektor" }])));
controle("(3) Netty est nommé « l'ancien logiciel »", origineDuMetier({ metier: "courtier", source: "netty" }) === "d'après l'ancien logiciel (Netty)");
controle("(4) les transactions", origineDuMetier({ metier: "notaire", source: "transactions" }) === "d'après ses transactions");
controle("(5) saisi dans l'app, avec la date de confirmation", origineDuMetier({ metier: "syndic", source: "ecran", confirme_le: "2026-11-05T10:52:27Z" }) === "saisi dans l'app le 05/11/2026");
controle("(6) deux métiers d'une même origine : l'origine dite une fois",
  J(resumerMetiers([{ metier: "syndic", source: "hektor", ecrit_le: "2026-11-04" }, { metier: "diagnostiqueur", source: "hektor", ecrit_le: "2026-11-04" }]))
  === J({ titre: "Diagnostiqueur · Syndic", origine: "D'après Hektor" }));
controle("(7) deux origines : métier par métier, dans l'ordre d'arrivée",
  J(resumerMetiers([{ metier: "syndic", source: "ecran", ecrit_le: "2026-11-05" }, { metier: "notaire", source: "netty", ecrit_le: "2026-11-04" }]))
  === J({ titre: "Notaire · Syndic", origine: "Notaire : d'après l'ancien logiciel (Netty) · Syndic : saisi dans l'app le 05/11/2026" }),
  J(resumerMetiers([{ metier: "syndic", source: "ecran", ecrit_le: "2026-11-05" }, { metier: "notaire", source: "netty", ecrit_le: "2026-11-04" }])));
controle("(8) libellés français (société, agent immobilier, marchand de biens)",
  resumerMetiers([{ metier: "societe", source: "netty" }]).titre === "Société"
  && resumerMetiers([{ metier: "agent_immobilier", source: "netty" }]).titre === "Agent immobilier"
  && resumerMetiers([{ metier: "marchand_de_biens", source: "netty" }]).titre === "Marchand de biens");
controle("(9) un métier inconnu reste lisible", resumerMetiers([{ metier: "geometre_expert", source: "ecran" }]).titre === "Geometre expert");
controle("(10) une ligne vide est ignorée", resumerMetiers([{ metier: "", source: "netty" }, { metier: "syndic", source: "hektor" }]).titre === "Syndic");
controle("(11) un même métier n'apparaît qu'une fois", resumerMetiers([{ metier: "syndic", source: "hektor" }, { metier: "syndic", source: "netty" }]).titre === "Syndic");

const bloc = fs.readFileSync(BLOC, "utf8");
const lecture = bloc.slice(bloc.indexOf("export function useMetiersPartenaire("), bloc.indexOf("export function BlocMetierPartenaire("));
controle("(12) lecture : lignes ACTIVES du contact, par notre numéro, rien d'écrit dans la lecture",
  lecture.length > 0 && /from\('app_partenaire_metier'\)/.test(lecture) && /\.eq\('contact_id', contactId\.trim\(\)\)/.test(lecture)
  && /\.is\('retire_le', null\)/.test(lecture) && !/\.insert\(|\.update\(|\.delete\(|\.rpc\(/.test(lecture));
controle("(12 bis) la seule écriture du fichier est app_partenaire_metier_ecrire",
  (bloc.match(/\.rpc\(/g) || []).length === 1 && (bloc.match(/supabase\.from\(/g) || []).length === 1
  && !/\.(insert|upsert|update)\(/.test(bloc));
controle("(13) une lecture ratée est DITE (jamais « aucun métier »)", /etat === 'erreur'/.test(bloc) && /Lecture du registre impossible/.test(bloc));

const app = fs.readFileSync(APP, "utf8");
controle("(14) le cran `partenaires_ecran` commande la lecture", /useCranCouplesVisible\('partenaires_ecran', props\.profileRole\)/.test(app)
  && /useMetiersPartenaire\(String\(props\.contact\.hektor_contact_id \?\? ''\), partenairesEcran\)/.test(app));
controle("(15) le bloc est sous le statut, dans le volet gauche", /fa-cx-st-chip sev[\s\S]{0,200}<\/div>\s*<BlocMetierPartenaire metiers=\{metiersPartenaire\}/.test(app));

// ── PIÈCE 3.2 : la fenêtre « Métier du contact » ──
const { planDesChangements, METIERS_ORDONNES } = api;
controle("(16) 18 métiers, les six du chantier d'abord", METIERS_ORDONNES.length === 18
  && J(METIERS_ORDONNES.filter((m) => m.premier).map((m) => m.metier)) === J(["syndic", "diagnostiqueur", "courtier", "banque", "apporteur", "parrain"])
  && METIERS_ORDONNES.slice(0, 6).every((m) => m.premier) && METIERS_ORDONNES.every((m) => m.libelle));
controle("(17) rien de changé = rien à envoyer", J(planDesChangements(["syndic"], [], [])) === "[]");
controle("(18) les retraits partent AVANT les ajouts", J(planDesChangements(["syndic"], ["syndic"], ["diagnostiqueur"]))
  === J([{ metier: "syndic", retirer: true }, { metier: "diagnostiqueur", retirer: false }]));
controle("(19) on ne retire que ce qui est actif, on n'ajoute pas ce qui l'est déjà",
  J(planDesChangements(["syndic"], ["courtier"], ["syndic", "banque"])) === J([{ metier: "banque", retirer: false }]));
controle("(20) un métier inconnu n'est jamais envoyé", J(planDesChangements([], [], ["geometre"])) === "[]");
controle("(21) un doublon dans la saisie n'est envoyé qu'une fois", J(planDesChangements([], [], ["syndic", "syndic"])) === J([{ metier: "syndic", retirer: false }]));
controle("(22) l'écriture passe par app_partenaire_metier_ecrire (notre numéro, le métier, retirer ou non)",
  /rpc\('app_partenaire_metier_ecrire', \{\s*p_contact: props\.contactId, p_metier: changement\.metier, p_retirer: changement\.retirer,\s*\}\)/.test(bloc));
controle("(23) après une erreur, ce qui est passé est relu et l'arrêt est dit", /if \(faits > 0\) props\.onEnregistre\(\)/.test(bloc) && /échec : /.test(bloc));
controle("(24) le geste : cran `partenaires_metier_modif` ET droit de gérer les contacts ET lecture prête",
  /useCranCouplesVisible\('partenaires_metier_modif', props\.profileRole\)/.test(app)
  && /peutChangerMetier = partenairesEcran && metierModifCran && Boolean\(props\.canManageContacts\) && metiersPartenaire\.etat === 'pret'/.test(app));
controle("(25) deux portes : « Changer » dans le bloc et « Changer le métier » dans le menu ⋯",
  /onChanger=\{peutChangerMetier \? \(\) => setFenetreMetierOuverte\(true\) : undefined\}/.test(app)
  && /\{peutChangerMetier \? \([\s\S]{0,700}Changer le métier/.test(app));
controle("(26) la fenêtre relit le bloc après l'enregistrement", /onEnregistre=\{metiersPartenaire\.recharger\}/.test(app));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTout est vert.");
process.exit(echecs.length ? 1 : 0);
