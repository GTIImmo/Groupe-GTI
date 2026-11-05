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

// ── PIÈCE 3.3a : le volet de la fiche partenaire ──
const { profilDuPartenaire } = api;
const P = (lignes) => profilDuPartenaire(lignes.map((metier) => ({ metier, source: "netty" })));
controle("(27) sans métier, ou notaire seul : pas une fiche partenaire", profilDuPartenaire([]) === null && P(["notaire"]) === null);
controle("(28) un syndic : famille syndic, « Demander un document », lot 4",
  J(P(["syndic"])) === J({ metier: "syndic", famille: "syndic", action: "Demander un document", lot: "lot 4", libelles: ["Syndic"] }), J(P(["syndic"])));
controle("(29) courtier et banque → famille courtier ; apporteur et parrain → famille apporteur ; diagnostiqueur → diag",
  P(["banque"]).famille === "courtier" && P(["parrain"]).famille === "apporteur" && P(["diagnostiqueur"]).action === "Commander un diagnostic");
controle("(30) plusieurs métiers : le principal suit l'ordre (courtier avant parrain), le notaire n'entre pas dans le titre",
  J(P(["parrain", "notaire", "courtier"])) === J({ metier: "courtier", famille: "courtier", action: "Orienter un acquéreur", lot: "lots 6 et 7", libelles: ["Courtier", "Parrain"] }),
  J(P(["parrain", "notaire", "courtier"])));
controle("(31) un métier sans action (société) : famille autre, pas de bouton", J(P(["societe"])) === J({ metier: "societe", famille: "autre", action: null, lot: null, libelles: ["Société"] }));
controle("(32) un métier inconnu reste lisible, famille autre", P(["geometre_expert"]).famille === "autre" && P(["geometre_expert"]).libelles[0] === "Geometre expert");

controle("(33) le cran `partenaires_fiche` ET le bloc métier ET ouverte depuis le catalogue ET pas fiche notaire ET lecture prête",
  /useCranCouplesVisible\('partenaires_fiche', props\.profileRole\)/.test(app)
  && /profilBrut = partenairesEcran && ficheCran && props\.ouverture === 'catalogue_metiers' && !estFicheNotaire && metiersPartenaire\.etat === 'pret'/.test(app));
controle("(34) la couleur : ty-<famille> (ty-partenaire pour « autre »), sinon la classe d'avant",
  /profilPartenaire\s*\?\s*`ty-\$\{profilPartenaire\.famille === 'autre' \? 'partenaire' : profilPartenaire\.famille\}`\s*:\s*primaryCategory === 'notaire'/.test(app));
controle("(35) l'action du métier est montrée DÉSACTIVÉE (« bientôt »)", /className="fa-cx-act primary wide bientot" type="button" disabled/.test(app));
controle("(36) menu réduit : « Modifier la fiche » passe dans le menu, le bouton Modifier quitte la rangée",
  /props\.canManageContacts && !profilPartenaire \?/.test(app) && /profilPartenaire && props\.canManageContacts \? \([\s\S]{0,800}Modifier la fiche/.test(app));
controle("(37) « Ouvrir dans Hektor » caché sur une fiche partenaire sans numéro Hektor", /\{!profilPartenaire \|\| cibleHektorDuContact\(props\.contact\) \? \(/.test(app));
controle("(38) P1 : bandeau « Fiche archivée · elle reste modifiable » + Réactiver (le geste d'archivage existant)",
  /profilPartenaire && isArchived \?/.test(app) && /archivage\.basculer\(\)[\s\S]{0,120}'Réactiver'/.test(app));
controle("(39) les autres rôles du contact restent dits à côté du métier",
  /profilPartenaire\.libelles\.join\(' · '\)[\s\S]{0,200}dirCategories\.filter\(\(cat\) => cat !== 'autre'\)/.test(app));

// ── PIÈCE 3.3b : la partie droite de la fiche partenaire ──
const { blocsDuPartenaire } = api;
const familles = ["syndic", "diag", "courtier", "apporteur"];
controle("(40) chaque famille a 4 chiffres, une section avec ses étapes, « À venir » et 2 blocs « avec nous »",
  familles.every((f) => { const b = blocsDuPartenaire(f); return b && b.chiffres.length === 4 && b.section.etapes.length >= 3 && b.aVenir && b.avecNous.length === 2 && /^lots? /.test(b.lot); }));
controle("(41) « autre », absent ou inconnu : pas de blocs", blocsDuPartenaire("autre") === null && blocsDuPartenaire(null) === null && blocsDuPartenaire(undefined) === null);
controle("(42) le lot des blocs = le lot de l'action du métier",
  familles.every((f) => { const prof = profilDuPartenaire([{ metier: { syndic: "syndic", diag: "diagnostiqueur", courtier: "courtier", apporteur: "apporteur" }[f], source: "netty" }]); return prof.lot === blocsDuPartenaire(f).lot; }));
controle("(43) les libellés de la maquette sont repris (syndic, diag, courtier, apporteur)",
  J(blocsDuPartenaire("syndic").section.etapes) === J(["Demandes", "AG à venir", "À jour"])
  && J(blocsDuPartenaire("diag").section.etapes) === J(["Commandé", "RDV fixé", "Rapport reçu", "Au coffre"])
  && J(blocsDuPartenaire("courtier").section.etapes) === J(["Orientés", "Accord de principe", "Offre de prêt", "Financés"])
  && J(blocsDuPartenaire("apporteur").section.etapes) === J(["Contact apporté", "Mandat", "Commission due", "Réglé"]));
controle("(44) branchement : blocs du profil, et Recherche cachée sans recherche active (notaire OU partenaire à blocs ; pas « autre »)",
  /const blocsPartenaire = blocsDuPartenaire\(profilPartenaire\?\.famille\)/.test(app)
  && /const masquerRecherche = \(estFicheNotaire \|\| Boolean\(blocsPartenaire\)\) && Number\(props\.contact\.active_search_count \?\? 0\) === 0/.test(app));
controle("(45) les 4 blocs sont posés à leur place (chiffres avant le tableau, section, À venir, avec nous)",
  /<PartenaireChiffres blocs=\{blocsPartenaire\} \/>[\s\S]{0,120}fa-cx-dash-top/.test(app)
  && /<NotaireDossiers[\s\S]{0,200}<PartenaireSectionMetier blocs=\{blocsPartenaire\} \/>/.test(app)
  && /<NotaireAVenir vue=\{vueNotaire\} \/> : null\}\s*\{blocsPartenaire \? <PartenaireAVenir/.test(app)
  && /<NotaireVentesEtAvecNous[^\n]*\n\s*\{blocsPartenaire \? <PartenaireAvecNous/.test(app));
const fp = fs.readFileSync(path.resolve(__dirname, "src", "FichePartenaire.tsx"), "utf8");
controle("(46) FichePartenaire : aucune lecture ni écriture (ni supabase, ni rpc, ni fetch)", !/supabase|\.rpc\(|fetch\(/.test(fp.replace(/^\/\/.*$/gm, "")));
controle("(47) section, À venir et avec nous disent « en construction » ; les chiffres valent « — » (pas de faux zéro)",
  (fp.match(/<EnConstruction/g) || []).length === 3 && /aria-label="pas encore de données">—</.test(fp));

// ── Règle du 05/11 : la PORTE choisit la fiche ; une fiche client ne change jamais ──
controle("(48) la fiche métier n'existe que si la fiche est ouverte depuis le catalogue des métiers (propriété « ouverture »)",
  /ouverture\?: 'catalogue_metiers'/.test(app) && (app.match(/catalogue_metiers/g) || []).length >= 2);
controle("(49) famille « autre » (société, administration…) : pas de fiche dédiée",
  /const profilPartenaire = profilBrut && profilBrut\.famille !== 'autre' \? profilBrut : null/.test(app));
controle("(50) UNE SEULE porte passe « ouverture » : l'écran Contacts, côté Partenaires (vueMetiers)",
  (app.match(/ouverture=\{[^}]*catalogue_metiers[^}]*\}/g) || []).length === 1
  && /ouverture=\{vueMetiers \? 'catalogue_metiers' : undefined\}/.test(app));

// ── PIÈCE 3.5 : le catalogue des métiers ──
let cat;
try {
  const { code } = esbuild.transformSync(fs.readFileSync(path.resolve(__dirname, "src", "lib", "cataloguePartenaires.ts"), "utf8"), { loader: "ts", format: "cjs" });
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports });
  cat = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const C = (id, extra = {}) => ({ hektor_contact_id: id, prenom: "", nom: `N${id}`, archive: false, ...extra });
const reg = [
  { contact_id: "1", metier: "syndic" }, { contact_id: "2", metier: "banque" }, { contact_id: "2", metier: "courtier" },
  { contact_id: "3", metier: "parrain" }, { contact_id: "4", metier: "diagnostiqueur" }, { contact_id: "5", metier: "societe" },
  { contact_id: "6", metier: "administration" }, { contact_id: "9", metier: "syndic" },
];
const cg = cat.construireCatalogue(reg, [C("1"), C("2"), C("3", { archive: "1" }), C("4"), C("5"), C("6")], [C("7"), C("8", { archive: true }), C("7")]);
controle("(51) cinq tuiles et c'est tout (notaire, syndic, diag, courtier, apporteur)",
  J(cat.TUILES_CATALOGUE.map((t) => t.tuile)) === J(["notaire", "syndic", "diag", "courtier", "apporteur"]) && J(Object.keys(cg).sort()) === J(["apporteur", "courtier", "diag", "notaire", "syndic"]));
controle("(52) société et administration ne sont PAS au catalogue", ![].concat(...Object.values(cg).map((t) => [...t.actifs, ...t.archives])).some((l) => l.id === "5" || l.id === "6"));
controle("(53) banque + courtier = une seule ligne, avec ses deux métiers", cg.courtier.actifs.length === 1 && J(cg.courtier.actifs[0].metiers) === J(["banque", "courtier"]));
controle("(54) les archivés à part (« 1 », true)", cg.apporteur.archives.length === 1 && cg.apporteur.actifs.length === 0 && cg.notaire.archives.length === 1);
controle("(55) un notaire en double n'est compté qu'une fois ; un contact sans fiche est ignoré (9)", cg.notaire.actifs.length === 1 && cg.syndic.actifs.length === 1);
const lignes = [{ id: "1", nom: "Étude Durand", detail: "Firminy · 06", recherche: "etude durand firminy · 06" }, { id: "2", nom: "Martin", detail: "Lyon", recherche: "martin lyon" }];
controle("(56) la recherche : chaque mot, accents ignorés, vide = tout", cat.filtrerCatalogue(lignes, "ÉTUDE firm").length === 1 && cat.filtrerCatalogue(lignes, " ").length === 2 && cat.filtrerCatalogue(lignes, "durand lyon").length === 0);
controle("(57) le nom : prénom + nom, sinon le nom affiché, sinon « Contact N »",
  cat.nomDuContact({ hektor_contact_id: "1", prenom: "Ana", nom: "B" }) === "Ana B" && cat.nomDuContact({ hektor_contact_id: "2", display_name: "SCI X" }) === "SCI X" && cat.nomDuContact({ hektor_contact_id: "3" }) === "Contact 3");
controle("(58) l'annuaire : cran `partenaires_catalogue`, pastille Notaire retirée là où il est visible",
  /useCranCouplesVisible\('partenaires_catalogue', props\.profileRole\)/.test(app) && /\{TYPE_NOTAIRE_ECRAN && !catalogueVisible \? <button/.test(app));
controle("(59) la fiche du catalogue vient du catalogue (pas du 1er de la page des clients)",
  /const ficheContact = vueMetiers && contactCatalogue && contactCatalogue\.hektor_contact_id !== props\.selectedContact\?\.hektor_contact_id/.test(app)
  && /contact=\{ficheContact\}/.test(app));
controle("(60) l'adresse garde « vue=metiers » ; « voir le contact » remet le côté clients",
  /const CLES_ADRESSE = \['ecran', 'annonce', 'contact', 'vue'\]/.test(app) && /p\.set\('vue', 'metiers'\)/.test(app)
  && /function showContactInDirectory\(normalizedId: string\) \{\s*setScreen\('contacts'\)\s*setContactsVue\('clients'\)/.test(app));
const catTsx = fs.readFileSync(path.resolve(__dirname, "src", "CataloguePartenaires.tsx"), "utf8");
controle("(61) le catalogue ne fait que LIRE (aucune écriture, aucune fonction appelée)", !/\.(insert|update|upsert|delete|rpc)\(/.test(catTsx));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTout est vert.");
process.exit(echecs.length ? 1 : 0);
