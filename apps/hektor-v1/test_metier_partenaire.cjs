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
  && /<NotaireDossiers[\s\S]{0,800}<PartenaireSectionMetier blocs=\{blocsPartenaire\} \/>/.test(app)
  && /<NotaireAVenir vue=\{vueNotaire\} \/> : null\}\s*\{blocsPartenaire \? <PartenaireAVenir/.test(app)
  && /<NotaireVentesEtAvecNous[^\n]*\n\s*\{(ficheSyndicActive \? <SyndicNosBiens vue=\{ficheSyndic\.vue\} \/> : )?blocsPartenaire \? <PartenaireAvecNous/.test(app)
  // lot 5 (06/11) : le chiffre et la section du diagnostiqueur s'intercalent avant les blocs 3.3b, qui restent en dernier recours.
  && /: ficheDiagActive \? <DiagChiffres vue=\{ficheDiag\.vue\} \/> : blocsPartenaire \? <PartenaireChiffres blocs=\{blocsPartenaire\} \/> : null\}/.test(app));
const fp = fs.readFileSync(path.resolve(__dirname, "src", "FichePartenaire.tsx"), "utf8");
// 06/11 (3.4) : une seule lecture permise, celle des interlocuteurs ; l'écriture passe par le carnet du notaire (relais).
controle("(46) FichePartenaire : une seule lecture (app_partenaire_interlocuteur), aucune écriture ni fetch",
  (fp.match(/supabase\.from\(/g) || []).length === 1 && /supabase\.from\('app_partenaire_interlocuteur'\)\.select\(/.test(fp) && !/\.rpc\(|fetch\(|\.(insert|update|upsert|delete)\(/.test(fp.replace(/^\/\/.*$/gm, "")));
controle("(70) 3.4 : le carnet sur les fiches métier seulement (pas « autre »), titre « Interlocuteurs », le notaire inchangé",
  /\{blocsPartenaire && profilPartenaire && profilPartenaire\.famille !== 'autre'\s*\? <PartenaireInterlocuteurs/.test(app) && /titre="Interlocuteurs"/.test(fp)
  && /\{props\.titre \?\? "Interlocuteurs de l'étude"\}/.test(fs.readFileSync(path.resolve(__dirname, "src", "FicheNotaire.tsx"), "utf8")));
controle("(47) section, À venir et avec nous disent « en construction » ; les chiffres valent « — » (pas de faux zéro)",
  (fp.match(/<EnConstruction/g) || []).length === 3 && /aria-label="pas encore de données">—</.test(fp));

// ── Règle du 05/11 : la PORTE choisit la fiche ; une fiche client ne change jamais ──
controle("(48) la fiche métier n'existe que si la fiche est ouverte depuis le catalogue des métiers (propriété « ouverture »)",
  /ouverture\?: 'catalogue_metiers'/.test(app) && (app.match(/catalogue_metiers/g) || []).length >= 2);
controle("(49) famille « autre » (société, administration…) : pas de fiche dédiée",
  /const profilPartenaire = profilBrut && profilBrut\.famille !== 'autre' \? profilBrut : null/.test(app));
controle("(50) DEUX portes seulement passent « ouverture » : l'écran Contacts du bureau et celui du téléphone, côté Partenaires (vueMetiers)",
  (app.match(/ouverture=\{[^}]*catalogue_metiers[^}]*\}/g) || []).length === 2
  && (app.match(/ouverture=\{vueMetiers \? 'catalogue_metiers' : undefined\}/g) || []).length === 2);

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
controle("(51) cinq tuiles et c'est tout, dans l'ordre de la maquette (notaire, banques et courtiers, diag, apporteurs, syndics)",
  J(cat.TUILES_CATALOGUE.map((t) => t.tuile)) === J(["notaire", "courtier", "diag", "apporteur", "syndic"]) && J(Object.keys(cg).sort()) === J(["apporteur", "courtier", "diag", "notaire", "syndic"]));
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
  // 4.2 (06/11) : le côté devient un paramètre, « clients » par défaut ; « voir le contact » n'en passe aucun.
  && /function showContactInDirectory\(normalizedId: string, vue: 'clients' \| 'metiers' = 'clients'\) \{\s*setScreen\('contacts'\)[\s\S]{0,300}?setContactsVue\(vue\)/.test(app)
  && /if \(detailOpen\) \{ setAnnonceContactId\(normalizedId\); return \}\s*showContactInDirectory\(normalizedId\)\s*\}/.test(app));
const catTsx = fs.readFileSync(path.resolve(__dirname, "src", "CataloguePartenaires.tsx"), "utf8");
// 09/11 (§28.10) : une seule fonction permise, la LECTURE des numéros des notaires (index), avec repli sur la lecture d'avant.
controle("(61) le catalogue ne fait que LIRE (aucune écriture ; seule fonction : app_catalogue_notaires_ids, avec repli)",
  !/\.(insert|update|upsert|delete)\(/.test(catTsx) && (catTsx.match(/\.rpc\(/g) || []).length === 1
  && /\.rpc\('app_catalogue_notaires_ids'\)/.test(catTsx) && /relation_roles_json\.cs\./.test(catTsx));

// ── 3.5, le dessin de la maquette (05/11, « oui ») ──
const cg2 = cat.construireCatalogue([{ contact_id: "1", metier: "syndic" }, { contact_id: "2", metier: "syndic" }], [C("1"), C("2", { ville: "Firminy", phone_primary: "06" })], []);
controle("(62) sans ville ni téléphone ni e-mail, la carte montre le NUMÉRO (doublons discernables)",
  cg2.syndic.actifs.find((l) => l.id === "1").detail === "n° 1" && cg2.syndic.actifs.find((l) => l.id === "2").detail === "Firminy");
controle("(63) la recherche trouve aussi par numéro et par téléphone", cat.filtrerCatalogue(cg2.syndic.actifs, "1").some((l) => l.id === "1") && cat.filtrerCatalogue(cg2.syndic.actifs, "06").length === 1);
controle("(64) HARMONISATION (06/11) : la barre commune de l'app est AUSSI celle du côté Partenaires (recherche du catalogue, « Ajouter un partenaire », Filtres / Stats / Priorités grisés) ; « Clients | Partenaires » est l'onglet de vue du titre, aux deux côtés et au téléphone",
  !/&& !vueMetiersApp \? \(\s*<section className=\{`hero/.test(app) && /value=\{vueMetiersApp \? rechercheCatalogue : searchDraft\}/.test(app)
  && /\{vueMetiersApp \? 'Ajouter un partenaire' : 'Nouveau contact'\}/.test(app) && (app.match(/disabled=\{vueMetiersApp\}/g) || []).length >= 3
  && /<CataloguePartenaires\s+enTeteCommun\s+requete=\{props\.rechercheCatalogue\}/.test(app) && /<OngletsAnnuaire vue="clients"/.test(app)
  // 06/11 : l'onglet de vue vit SOUS la recherche, dans la barre commune ; plus dans le titre des cartes.
  && /<div className="hero-onglets"><OngletsAnnuaire vue=\{vueMetiersApp \? 'metiers' : 'clients'\} onVue=\{setContactsVue\} \/><\/div>/.test(app)
  && !/lc-badge[^\n]*\n\s*<OngletsAnnuaire/.test(catTsx) && !/\{catalogueVisible \? <OngletsAnnuaire/.test(app)
  && /<h1>Annuaire des partenaires<\/h1>/.test(catTsx) && /export function OngletsAnnuaire/.test(catTsx)
  && /props\.enTeteCommun && props\.variante !== 'telephone'/.test(catTsx) && /onAjouter=\{props\.canManageContacts \? props\.onOpenCreate : undefined\}/.test(app));
controle("(65) l'aperçu : l'activité est « en construction », jamais un faux chiffre", /Activité avec l'agence sur 12 mois · en construction/.test(catTsx) && !/\d+ ?%/.test(catTsx.replace(/\/\/.*$/gm, "")));

controle("(66) quitter le côté Partenaires ferme la fiche ouverte depuis le catalogue (jamais le 1er client de la page à sa place)",
  /if \(!vueMetiers && contactCatalogue\) \{ setDetailOpen\(false\); setContactCatalogue\(null\) \}/.test(app));

// ── 3.6 : le téléphone (06/11, « visible par tous ») ──
const iMob = app.indexOf("function MobileContactCards(props: {"), mob = app.slice(iMob, app.indexOf("function StatusPill(", iMob));
controle("(67) téléphone : même cran, catalogue en version téléphone AVANT la liste vide, fiche du catalogue et garde de sortie",
  /useCranCouplesVisible\('partenaires_catalogue', props\.profileRole\)/.test(mob) && /variante="telephone"/.test(mob)
  && mob.indexOf("if (vueMetiers) {") > 0 && mob.indexOf("if (vueMetiers) {") < mob.indexOf("if (props.contacts.length === 0) {")
  && /const ficheContact = vueMetiers && contactCatalogue/.test(mob) && /if \(!vueMetiers && contactCatalogue\) \{ setDetailOpen\(false\); setContactCatalogue\(null\) \}/.test(mob));
controle("(68) téléphone : la carte de recherche des clients se cache côté Partenaires ; la feuille a « Voir toute la fiche »",
  /const showMobileCommandCard = [^\n]*\n\s*&& !vueMetiersApp/.test(app) && /Voir toute la fiche/.test(catTsx) && /className="pt-sheet"/.test(catTsx));
controle("(69) les pastilles et les actions du téléphone suivent la maquette (planche 2) et la fiche (3.3a)",
  J(cat.TUILES_CATALOGUE.map((t) => t.puce)) === J(["Notaires", "Banques", "Diagnostics", "Apporteurs", "Syndics"])
  && cat.TUILES_CATALOGUE.find((t) => t.tuile === "notaire").action === null && cat.TUILES_CATALOGUE.find((t) => t.tuile === "syndic").action === "Demander un document");

// ── LOT 4, PIÈCE 4.1 : la fiche syndic remplie (06/11) ──
let sy;
try {
  const { code } = esbuild.transformSync(fs.readFileSync(path.resolve(__dirname, "src", "lib", "ficheSyndic.ts"), "utf8"), { loader: "ts", format: "cjs" });
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports });
  sy = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const props = { copropriete: { value: "OUI" }, copropriete_lot: { value: "210 - 101" }, copropriete_nb_lot: { value: "255" }, copropriete_quote_part: { value: "2960" },
  montant_fonds_travaux: { value: "0" }, copropriete_statut_syndicat: { value: "NOTPROCESS" }, copropriete_plan_sauvegarde: { value: "NON" } };
const payload = JSON.stringify({ copropriete_detail: "OUI", copropriete_json: JSON.stringify({ titre: "copropriete", props }) });
const cp = sy.lireCopro(payload);
controle("(71) 4.1 lireCopro : le texte JSON imbriqué de Hektor (lots, quote-part, fonds, NOTPROCESS = aucune procédure, plan NON)",
  cp && cp.lots === 255 && cp.quotePart === 2960 && cp.fondsTravaux === 0 && cp.procedure === "aucune" && cp.planSauvegarde === false && cp.numerosLots === "210 - 101");
controle("(72) 4.1 lireCopro : rien de lisible = null (jamais un faux zéro) ; autre statut = procédure en cours",
  sy.lireCopro("{}") === null && sy.lireCopro(null) === null && sy.lireCopro("pas du json") === null
  && sy.lireCopro({ copropriete_json: { props: { copropriete_statut_syndicat: { value: "PROCESS" } } } }).procedure === "en_cours");
controle("(73) 4.1 documents de copropriété reconnus par le nom (accents, espaces, « _ »), pas les autres",
  ["Pré-état daté.pdf", "pre_etat_date_2025.pdf", "PV AG 2026.pdf", "pv_d_ag.pdf", "Procès-verbal assemblée.pdf", "reglement_de_copro.pdf", "Carnet d'entretien.pdf", "fiche_synthetique.pdf", "DTG immeuble.pdf"].every(sy.estDocumentCopro)
  && !["Plan cadastral.pdf", "DPE.pdf", "Mandat de vente.pdf", "taxe_fonciere_2024.pdf", "compromis.pdf"].some(sy.estDocumentCopro));
const vue = sy.construireVueSyndic({
  liens: [{ hektor_annonce_id: 1, app_dossier_id: 11 }, { hektor_annonce_id: 2, app_dossier_id: 12 }, { hektor_annonce_id: 1, app_dossier_id: 11 }, { hektor_annonce_id: 3, app_dossier_id: null }],
  biens: [{ hektor_annonce_id: 1, app_dossier_id: 11, titre_bien: "Zèbre T3", ville: "Firminy", statut_annonce: "Vendu" }, { hektor_annonce_id: 2, app_dossier_id: 12, titre_bien: "Appart T2", statut_annonce: "Actif", numero_mandat: "18 870" }],
  details: [{ hektor_annonce_id: 2, detail_payload_json: payload }],
  documents: [{ hektor_annonce_id: "2", document_name: "PV AG 2026.pdf" }, { hektor_annonce_id: "2", document_name: "DPE.pdf" }, { hektor_annonce_id: "2", document_name: "PV AG 2026.pdf" }],
});
controle("(74) 4.1 la vue : un bien par annonce (doublon de lien ignoré), en vente d'abord, inconnu montré par son numéro, docs copro seuls et sans doublon",
  vue.biens.length === 3 && vue.biens[0].hektorAnnonceId === "2" && vue.biens[0].enVente && vue.enVente === 1 && vue.quotePartMoyenne === 2960
  && J(vue.biens[0].documents) === J(["PV AG 2026.pdf"]) && vue.biens.some((b) => b.titre === "Bien 3" && b.appDossierId === null) && vue.avecDocuments === 1 && !("lots" in vue));
// 09/11 (§28.10) : Hektor coupé -> un bien né dans l'app (lien sur NOTRE numéro seul) a tout ce qu'il faut ; un bien archivé
// (index par numéro Hektor seul) reste trouvé ; deux liens d'un même bien = un bien.
const vueApp = sy.construireVueSyndic({
  liens: [{ hektor_annonce_id: null, app_dossier_id: 10000213 }, { hektor_annonce_id: 40529, app_dossier_id: 5853060 }, { hektor_annonce_id: 63487, app_dossier_id: 10000213 }],
  biens: [{ app_dossier_id: 10000213, hektor_annonce_id: null, titre_bien: "Né dans l'app", statut_annonce: "Estimation" }, { hektor_annonce_id: 40529, titre_bien: "Vendu archivé", statut_annonce: "Vendu" }],
  details: [{ app_dossier_id: 10000213, hektor_annonce_id: null, detail_payload_json: payload }],
  documents: [{ app_dossier_id: 10000213, hektor_annonce_id: null, document_name: "PV AG 2026.pdf" }, { app_dossier_id: null, hektor_annonce_id: "40529", document_name: "Pré-état daté.pdf" }],
});
const nApp = vueApp.biens.find((b) => b.cle === "10000213"), nArch = vueApp.biens.find((b) => b.cle === "5853060");
controle("(74 bis) 09/11 Hektor coupé : un bien né dans l'app se lit par NOTRE numéro (titre, copro, documents) ; l'archivé par le numéro Hektor ; un bien par numéro",
  vueApp.biens.length === 2 && nApp && nApp.titre === "Né dans l'app" && nApp.hektorAnnonceId === "" && nApp.appDossierId === 10000213 && nApp.copro && nApp.copro.lots === 255
  && J(nApp.documents) === J(["PV AG 2026.pdf"]) && nArch && nArch.titre === "Vendu archivé" && J(nArch.documents) === J(["Pré-état daté.pdf"]));
const fsy = fs.readFileSync(path.resolve(__dirname, "src", "FicheSyndic.tsx"), "utf8");
controle("(75) 4.1 FicheSyndic : LECTURE seule (aucune écriture, aucune fonction appelée)", !/\.(insert|update|upsert|delete|rpc)\(|fetch\(/.test(fsy.replace(/^\/\/.*$/gm, "")));
controle("(76) 4.1 branchement : cran `partenaires_syndic_fiche`, fiche SYNDIC seulement, les blocs 3.3b ailleurs",
  /useCranCouplesVisible\('partenaires_syndic_fiche', props\.profileRole\)/.test(app) && /const ficheSyndicActive = syndicFicheCran && profilPartenaire\?\.famille === 'syndic'/.test(app)
  && /\{ficheSyndicActive \? <SyndicChiffres vue=\{ficheSyndic\.vue\} \/> : (ficheDiagActive \? <DiagChiffres vue=\{ficheDiag\.vue\} \/> : )?blocsPartenaire \? <PartenaireChiffres/.test(app)
  && /\{ficheSyndicActive \? <SyndicNosBiens vue=\{ficheSyndic\.vue\} \/> : blocsPartenaire \? <PartenaireAvecNous/.test(app));

// ── LOT 4, PIÈCE 4.2 : choisir le syndic d'un bien (06/11) ──
let sb;
try {
  const { code } = esbuild.transformSync(fs.readFileSync(path.resolve(__dirname, "src", "lib", "syndicDuBien.ts"), "utf8"), { loader: "ts", format: "cjs" });
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports });
  sb = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const diagHektor = JSON.stringify({ diagnostiqueur: { value: "", selected_label: "" }, syndic: { value: "423683", selected_label: "IMMO DE FRANCE FOREZ VELAY" } });
controle("(77) 4.2 ce que Hektor indique : lu dans le texte JSON de la fiche ; vide ou illisible = null",
  J(sb.syndicSelonHektor(diagHektor)) === J({ numero: "423683", nom: "IMMO DE FRANCE FOREZ VELAY" })
  && sb.syndicSelonHektor(JSON.stringify({ syndic: { value: "" } })) === null && sb.syndicSelonHektor("") === null && sb.syndicSelonHektor("pas du json") === null);
controle("(78) 4.2 même société : sans accents ni mots vides (« Agence immobilière de Bellevue » = « AGENCE BELLEVUE ») ; FONCIA ≠ CITYA",
  sb.memeSociete("Agence immobilière de Bellevue", "AGENCE BELLEVUE") && sb.memeSociete("FONCIA", "FONCIA LOIRE AUVERGNE")
  && !sb.memeSociete("FONCIA LOIRE", "CITYA LOIRE") && !sb.memeSociete("", "FONCIA"));
const nous = sb.lireSyndicDuBien({ id: 5, partenaire_id: "10217295", origine: "app", pose_le: "2026-11-06T10:00:00Z", pose_par: "Frédéric", nom: "IMMO DE FRANCE FOREZ VELAY" });
controle("(79) 4.2 l'écart avec Hektor : montré seulement s'il indique un AUTRE syndic (ou un syndic quand nous n'en avons pas)",
  sb.ecartAvecHektor(nous, { nom: "Immo de France Forez-Velay" }) === null && sb.ecartAvecHektor(nous, { nom: "FONCIA" }) === "FONCIA"
  && sb.ecartAvecHektor(null, { nom: "FONCIA" }) === "FONCIA" && sb.ecartAvecHektor(nous, null) === null && sb.lireSyndicDuBien(null) === null);
const cat42 = [{ id: "1", nom: "CITYA BELLEVUE", ville: "Saint-Étienne" }, { id: "2", nom: "FONCIA LOIRE AUVERGNE", ville: "Saint-Étienne" },
  { id: "3", nom: "AGENCE GIBERT", ville: "Firminy" }, { id: "4", nom: "IMMO DE FRANCE FOREZ VELAY", ville: "Le Puy-en-Velay" }];
const ch = sb.choixSyndics({ catalogue: cat42, recherche: "", actuel: "3", nomRnic: "FONCIA", nomHektor: "IMMO DE FRANCE FOREZ VELAY" });
controle("(80) 4.2 le sélecteur : le proposé par le registre RNIC en tête, puis celui de Hektor, puis l'ordre alphabétique ; le syndic actuel retiré",
  J(ch.map((c) => c.id)) === J(["2", "4", "1"]) && ch[0].propose === "rnic" && ch[1].propose === "hektor" && ch[2].propose === null);
controle("(81) 4.2 le sélecteur : la recherche par début de mot, sur le nom ET la ville, sans accents",
  J(sb.choixSyndics({ catalogue: cat42, recherche: "saint eti", actuel: null, nomRnic: null, nomHektor: null }).map((c) => c.id)) === J(["1", "2"])
  && J(sb.choixSyndics({ catalogue: cat42, recherche: "gib", actuel: null, nomRnic: null, nomHektor: null }).map((c) => c.id)) === J(["3"]));
controle("(82) 4.2 d'où vient le syndic : « repris de Hektor » / « choisi dans l'app par X le JJ/MM/AAAA »",
  sb.origineDuSyndic(nous) === "choisi dans l'app par Frédéric le 06/11/2026"
  && sb.origineDuSyndic({ ...nous, origine: "hektor", posePar: null, poseLe: null }) === "repris de Hektor");
const sbx = fs.readFileSync(path.resolve(__dirname, "src", "SyndicDuBien.tsx"), "utf8").replace(/^\s*\/\/.*$/gm, "");
controle("(83) 4.2 la carte n'écrit QUE par la fonction gardée (aucune table écrite en direct, aucun travail chez Hektor)",
  /rpc\('app_partenaire_syndic_du_bien', \{/.test(sbx) && /rpc\('app_partenaire_du_bien', \{/.test(sbx) && !/\.(insert|upsert)\(/.test(sbx) && !/from\('[^']+'\)\s*\.(update|delete)\(/.test(sbx) && !/console_job|create_hektor|fetch\(/.test(sbx));
controle("(84) 4.2 « Ouvrir sa fiche » passe par le CATALOGUE (vue métiers), l'écoute est AVANT le retour de connexion",
  /function showContactInDirectory\(normalizedId: string, vue: 'clients' \| 'metiers' = 'clients'\)/.test(app)
  && /if \(id\) showContactInDirectory\(id, 'metiers'\)/.test(app)
  && app.indexOf("window.addEventListener(EVENEMENT_OUVRIR_PARTENAIRE") < app.indexOf("if (hasSupabaseEnv && recoveryMode && !bootLoading)"));
controle("(85) 4.2 branchements derrière `partenaires_syndic_choix` : cockpit (carte), téléphone (LECTURE), assistant et aide RNIC sans syndic en texte",
  (app.match(/useCranCouplesVisible\('partenaires_syndic_choix'/g) || []).length === 4
  && /\{syndicCarteVisible \? \(\s*<SyndicDuBien/.test(app) && /<SyndicDuBien\s+variante="telephone"/.test(app)
  && /if \(syndicChoixCranApp && field\.name === 'syndic'\) return false/.test(app)
  && /syndicChoixCran \? \{ \.\.\.sec, fields: sec\.fields\.filter\(\(\[, k\]\) => k !== 'syndic'\) \}/.test(app)
  && /!String\(curSyndic \?\? ''\)\.trim\(\) && !syndicAuChoix\) \{ fields\.syndic = syndicComposed/.test(app)
  && (app.match(/onOpenEditor=\{\(\) => setEstimEditorOpen\(true\)\} profileRole=\{props\.profileRole\} \/>/g) || []).length === 3);
const nuit = fs.readFileSync(path.resolve(__dirname, "..", "..", "phase2", "contacts", "registre_partenaires_reprise.py"), "utf8");
controle("(86) 4.2c la nuit ne remet pas un lien retiré par quelqu'un (même partenaire, même bien), et le compte",
  /def liens_retires_par_quelquun\(\)/.test(nuit) && /"retire_par": "not\.is\.null", "objet": "eq\.bien"/.test(nuit)
  && /if \(annonce, role, str\(voulu\["partenaire"\]\)\) in liens_retires:/.test(nuit) && /"liens_retires_ecartes": liens_retires_ecartes/.test(nuit));
const patch42 = fs.readFileSync(path.resolve(__dirname, "..", "..", "supabase", "patch_partenaire_syndic_du_bien_2026-11-06.sql"), "utf8");
controle("(87) 4.2a le patch : droit sur le bien, syndic du registre, l'ancien retiré daté avec l'auteur, un seul syndic par bien, anon fermé",
  /app_console_can_access_dossier\(p_app_dossier_id, p_hektor_annonce_id::text\)/.test(patch42) && /metier = 'syndic' AND retire_le IS NULL/.test(patch42)
  && /SET retire_le = now\(\), retire_par = auth\.uid\(\) WHERE id = v_actuel\.id/.test(patch42) && /CREATE UNIQUE INDEX app_partenaire_lien_un_syndic_uidx/.test(patch42)
  && /FROM PUBLIC, anon/.test(patch42) && !/hektor_api|console_job/.test(patch42));

// ── 4.2 suite (06/11) : les syndics EN DOUBLE (15 noms, 41 fiches) — montrer de quoi choisir ──
const homo = [{ id: "10217296", nom: "FONCIA LOIRE AUVERGNE", ville: null, telephone: null, email: null, biens: 0 },
  { id: "10352728", nom: "FONCIA LOIRE AUVERGNE", ville: null, telephone: "04 77 00 00 01", biens: 5 },
  { id: "10354119", nom: "Foncia Loire Auvergne", ville: null, email: "exemple@foncia.test", biens: 1 },
  { id: "10215568", nom: "GIBERT IMMOBILIER", ville: "Firminy", telephone: "04 77 99 88 77", biens: 2 }];
const ch2 = sb.choixSyndics({ catalogue: homo, recherche: "foncia", actuel: null, nomRnic: null, nomHektor: null });
controle("(88) doublons : entre homonymes, la fiche qui porte DÉJÀ le plus de nos biens d'abord ; « 3 fiches à ce nom »",
  J(ch2.map((c) => c.id)) === J(["10352728", "10354119", "10217296"]) && ch2.every((c) => c.homonymes === 3)
  && sb.choixSyndics({ catalogue: homo, recherche: "gibert", actuel: null, nomRnic: null, nomHektor: null })[0].homonymes === 1);
controle("(89) doublons : ce qui distingue une fiche (n°, téléphone sinon e-mail, nos biens)",
  sb.distinguerSyndic(homo[1]) === "n° 10352728 · 04 77 00 00 01 · 5 biens chez nous"
  && sb.distinguerSyndic(homo[2]) === "n° 10354119 · exemple@foncia.test · 1 bien chez nous"
  && sb.distinguerSyndic(homo[0]) === "n° 10217296 · aucun de nos biens");
controle("(90) doublons : un numéro tapé retrouve la fiche (n°) ou le téléphone",
  J(sb.choixSyndics({ catalogue: homo, recherche: "10354", actuel: null, nomRnic: null, nomHektor: null }).map((c) => c.id)) === J(["10354119"])
  && J(sb.choixSyndics({ catalogue: homo, recherche: "99 88", actuel: null, nomRnic: null, nomHektor: null }).map((c) => c.id)) === J(["10215568"]));
const sbx2 = fs.readFileSync(path.resolve(__dirname, "src", "SyndicDuBien.tsx"), "utf8");
controle("(91) doublons : la carte lit téléphone, e-mail et les liens actifs (biens par fiche), relit après un choix, et l'affiche",
  /select\('hektor_contact_id,display_name,prenom,nom,ville,archive,phone_primary,email'\)/.test(sbx2)
  && /from\('app_partenaire_lien'\)\.select\('partenaire_id'\)\.eq\('role', role\)\.eq\('objet', 'bien'\)\.is\('retire_le', null\)/.test(sbx2)
  && /oublierLeCatalogue\(role\)\s*setVersion/.test(sbx2) && /\{distinguerSyndic\(s\)\}/.test(sbx2) && /s\.homonymes > 1 \?/.test(sbx2));

// ── 4.4 (06/11) : « Demander un document » au syndic, version simple ──
let dd;
try {
  const { code } = esbuild.transformSync(fs.readFileSync(path.resolve(__dirname, "src", "lib", "demandeDocument.ts"), "utf8"), { loader: "ts", format: "cjs" });
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports });
  dd = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const bienD = { id: "1", titre: "T3 exemple", adresse: "12 rue Exemple", codePostal: "42000", ville: "Saint-Étienne", lots: "210 - 101", mandat: "18 870" };
const msg = dd.messageDemande({ bien: bienD, pieces: dd.piecesParDefaut(), signature: "Négociatrice Test" });
controle("(93) 4.4 le message : adresse, lots, mandat, les 5 pièces cochées d'office, le délai du pré-état daté, la signature",
  msg.sujet === "Demande de documents de copropriété : 12 rue Exemple, 42000 Saint-Étienne (lots 210 - 101)"
  && /- Adresse : 12 rue Exemple, 42000 Saint-Étienne/.test(msg.corps) && /- Lots : 210 - 101/.test(msg.corps) && /mandat n° 18 870/.test(msg.corps)
  && dd.piecesParDefaut().length === 5 && /- Pré-état daté/.test(msg.corps) && /coût d'établissement du pré-état daté/.test(msg.corps) && /Négociatrice Test$/.test(msg.corps));
const msg2 = dd.messageDemande({ bien: { id: "2", titre: "Studio", adresse: null, codePostal: null, ville: null, lots: null, mandat: null }, pieces: ["pv_ag"] });
controle("(94) 4.4 une donnée absente n'est pas écrite (ni lot, ni mandat inventé) ; sans pré-état daté, pas de phrase sur son délai",
  !/Lot|mandat n°|pré-état daté/.test(msg2.corps) && /Adresse : Studio/.test(msg2.corps) && /Groupe GTI$/.test(msg2.corps));
controle("(95) 4.4 « ouvrir dans ma messagerie » seulement avec un e-mail valable (3 syndics sur 75 en ont un)",
  dd.lienMessagerie("syndic@exemple.fr", "S", "C") === "mailto:syndic@exemple.fr?subject=S&body=C" && dd.lienMessagerie("", "S", "C") === null && dd.lienMessagerie("pas un mail", "S", "C") === null);
const ddx = fs.readFileSync(path.resolve(__dirname, "src", "DemandeDocument.tsx"), "utf8").replace(/^\s*\/\/.*$/gm, "");
controle("(96) 4.4 la fenêtre n'enregistre ni n'envoie RIEN (pas de base, pas de travail, pas de requête)",
  !/supabase|rpc\(|fetch\(|console_job|insert|update\(/.test(ddx) && /createPortal\(/.test(ddx) && /navigator\.clipboard\.writeText/.test(ddx));
controle("(97) 4.4 branchements derrière `partenaires_syndic_demande` : bouton de la fiche syndic (au lieu de « bientôt ») et carte syndic d'un bien",
  /const demandeSyndicPossible = demandeSyndicCran && ficheSyndicActive/.test(app) && /\{demandeSyndicPossible \? \(\s*<button className="fa-cx-act primary wide" type="button" onClick=\{\(\) => setDemandeSyndicOuverte\(true\)\}>/.test(app)
  && /demandePossible=\{demandeSyndicBienCran\}/.test(app) && (app.match(/useCranCouplesVisible\('partenaires_syndic_demande'/g) || []).length === 2
  && /props\.demandePossible && props\.bienDemande \?/.test(sbx2));

// ── LOT 5 (06/11) : le diagnostiqueur, version simple ──
let cd;
try {
  const { code } = esbuild.transformSync(fs.readFileSync(path.resolve(__dirname, "src", "lib", "commandeDiagnostic.ts"), "utf8"), { loader: "ts", format: "cjs" });
  const module = { exports: {} };
  vm.runInNewContext(code, { module, exports: module.exports, require: () => ({}) });
  cd = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const bienV = { id: "1", titre: "Maison exemple", adresse: "3 chemin Fictif", codePostal: "42700", ville: "Firminy", lots: null, mandat: "19 001", annee: 1962, copro: false, typeBien: "Maison", surface: "110" };
controle("(98) lot 5 : diagnostics cochés d'office selon le bien (1962 : amiante oui, plomb non ; pas de Carrez hors copro ; année inconnue : les deux)",
  J(cd.diagnosticsParDefaut(bienV).sort()) === J(["amiante", "dpe", "electricite", "erp", "gaz"])
  && cd.diagnosticsParDefaut({ ...bienV, annee: null, copro: true }).includes("plomb") && cd.diagnosticsParDefaut({ ...bienV, annee: null, copro: true }).includes("carrez")
  && !cd.diagnosticsParDefaut({ ...bienV, annee: 2005 }).includes("amiante"));
const mc = cd.messageCommande({ bien: bienV, pieces: cd.diagnosticsParDefaut(bienV), signature: "Négociateur Essai" });
controle("(99) lot 5 : le message de commande (adresse, bien, année, mandat, diagnostics, rendez-vous et tarif)",
  mc.sujet === "Commande de diagnostics : 3 chemin Fictif, 42700 Firminy" && /- Bien : Maison, 110 m²/.test(mc.corps) && /- Année de construction : 1962/.test(mc.corps)
  && /mandat n° 19 001/.test(mc.corps) && /- Repérage de l'amiante/.test(mc.corps) && !/plomb/.test(mc.corps) && /date de rendez-vous et de nous indiquer votre tarif/.test(mc.corps) && !/copropriété/i.test(mc.corps));
controle("(100) lot 5 : ce que Hektor indique pour le DIAGNOSTIQUEUR se lit avec la même règle",
  J(sb.syndicSelonHektor(JSON.stringify({ diagnostiqueur: { value: "191362", selected_label: "DIAG EXEMPLE" } }), "diagnostiqueur")) === J({ numero: "191362", nom: "DIAG EXEMPLE" })
  && sb.syndicSelonHektor(JSON.stringify({ diagnostiqueur: { value: "191362", selected_label: "DIAG EXEMPLE" } })) === null);
const sbx3 = fs.readFileSync(path.resolve(__dirname, "src", "SyndicDuBien.tsx"), "utf8");
controle("(101) lot 5 : la carte sert au diagnostiqueur par le geste GÉNÉRIQUE ; le syndic garde ses fonctions de la 4.2 ; pas de RNIC pour un diagnostiqueur",
  /rpc\('app_partenaire_du_bien', \{\s*p_role: role,/.test(sbx3) && /rpc\('app_partenaire_du_bien_lire', \{ p_role: role,/.test(sbx3)
  && /role === 'syndic'\s*\? await supabase\.rpc\('app_partenaire_syndic_du_bien', \{/.test(sbx3) && /if \(role === 'syndic' && nomRnic === null/.test(sbx3)
  && /modele=\{role === 'syndic' \? 'copro' : 'diag'\}/.test(sbx3));
controle("(102) lot 5 : branchements derrière `partenaires_diag` : fiche (biens, chiffres, « Commander un diagnostic »), carte du bien (bureau), téléphone en lecture",
  (app.match(/useCranCouplesVisible\('partenaires_diag'/g) || []).length === 3 && /const ficheDiagActive = diagCran && profilPartenaire\?\.famille === 'diag'/.test(app)
  && /ficheDiagActive \? <DiagChiffres vue=\{ficheDiag\.vue\} \/>/.test(app) && /: ficheDiagActive \? <DiagBiens /.test(app)
  && /<SyndicDuBien\s+role="diagnostiqueur"\s+appDossierId/.test(app) && /<SyndicDuBien\s+role="diagnostiqueur"\s+variante="telephone"/.test(app) && /modele="diag"/.test(app));
const patch5 = fs.readFileSync(path.resolve(__dirname, "..", "..", "supabase", "patch_partenaire_du_bien_2026-11-06.sql"), "utf8");
controle("(103) lot 5 : le patch générique (rôle syndic ou diagnostiqueur seulement, droit sur le bien, métier au registre, un seul diagnostiqueur par bien, anon fermé)",
  /WHEN 'syndic' THEN 'syndic' WHEN 'diagnostiqueur' THEN 'diagnostiqueur' END/.test(patch5) && /app_console_can_access_dossier\(p_app_dossier_id, p_hektor_annonce_id::text\)/.test(patch5)
  && /metier = p_role AND retire_le IS NULL/.test(patch5) && /CREATE UNIQUE INDEX app_partenaire_lien_un_diag_uidx/.test(patch5) && /FROM PUBLIC, anon/.test(patch5)
  && !/app_partenaire_syndic_du_bien\(/.test(patch5.replace(/^--.*$/gm, "").replace(/to_regprocedure\('public\.app_partenaire_syndic_du_bien[^)]*\)'\)/g, "")));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTout est vert.");
process.exit(echecs.length ? 1 : 0);
