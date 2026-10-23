#!/usr/bin/env node
"use strict";
/**
 * ⑧ C1-C6 — LA RUBRIQUE AFFAIRES MONTRE TOUT CE QUI A ETE SAISI, TOUT DE SUITE.   23/10/2026
 *
 * On EXECUTE le code reel : les fonctions sont decoupees dans App.tsx, depouillees de leurs
 * types par esbuild, et jouees sur les lignes MESUREES en base le 23/10 sur VA6482 (chaines
 * 1001378 et 1001381 : offre refusee ; offre acceptee -> compromis 50132 -> vente 23355).
 *
 * ⚠ TEMOIN INVERSE : le meme essai est rejoue sur la version d'AVANT (git show HEAD). Les
 *   controles des corrections doivent y ECHOUER -- sinon ils ne prouvent rien.
 *
 * NE LANCE NI SERVEUR NI REQUETE.
 *     node apps/hektor-v1/test_rubrique_affaires_complete.cjs
 *     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");
const esbuild = require("esbuild");

const RACINE = path.resolve(__dirname, "..", "..");
const APP = "apps/hektor-v1/src/App.tsx";

function versionDavant() {
  try {
    return execFileSync("git", ["show", `HEAD:${APP}`], { cwd: RACINE, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  } catch (_) { return null; }
}

// Une fonction de premier niveau se termine par « \n} » en colonne 0 (le reste est indente).
function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}
// Le corps de repartitionChaineId : l'arrow passee a useCallback.
function trancheRepartition(src) {
  const i = src.indexOf("const repartitionChaineId = useCallback(");
  if (i < 0) return null;
  const a = src.indexOf("(): string =>", i);
  const f = src.indexOf("\n  }, [", a);
  return a < 0 || f < 0 ? null : "const repartitionChaineId = " + src.slice(a, f + 4);
}

const FONCTIONS = [
  "function formatPrice(", "function formatDate(", "function parseJson<T>(",
  "function ckPartyName(", "function ckAffPartyCoord(", "function ckPartieConsole(",
  "function affaireAcquereurParty(", "function affaireAcquereursParties(", "function affaireAcquereursDeChaine(",
  "function affaireAcquereursNoms(", "function affairePrix(", "function derniereDuGenre(",
  "function grouperAffairesParChaine(", "function ckAffaireDepuisChaine(", "function dossiersOuvertsDuBien(",
];
const FONCTIONS_NEUVES = ["function aliasNumerosAcquereur(", "function ckPartiesDuJson(", "function ckNomsParties(",
  "function ckDetailDepuisRegistre(", "function ckResumeNuitAJour(", "function compromisVerrouilleParSaVente(",
  "function bienVenduPourStatut("];

function monter(src) {
  const morceaux = [];
  const absentes = [];
  for (const f of [...FONCTIONS, ...FONCTIONS_NEUVES]) {
    const t = tranche(src, f);
    if (t) morceaux.push(t); else absentes.push(f);
  }
  const rep = trancheRepartition(src);
  if (rep) morceaux.push(rep);
  const prelude = `
    const AFFAIRE_RANG = { offre: 1, compromis: 2, vente: 3 };
    const AFFAIRE_ETAT_MORT = new Set(['refused', 'cancelled']);
    const AFFAIRE_GENRE_LABEL = { offre: 'Offre', compromis: 'Compromis', vente: 'Vente' };
    function affaireEtatLabel(k, s) { return String(s ?? ''); }
    // la modale : ce que la cible vise, et les affaires du bien
    let __visee = null; let statusChangeAffaires = [];
    function affaireCourantePourStatut() { return __visee; }
    function useCallback(f) { return f; }
  `;
  const code = prelude + morceaux.join("\n\n") + `
    this.api = { ckAffaireDepuisChaine, grouperAffairesParChaine, affaireAcquereursNoms,
      ckDetailDepuisRegistre: typeof ckDetailDepuisRegistre === 'function' ? ckDetailDepuisRegistre : null,
      ckResumeNuitAJour: typeof ckResumeNuitAJour === 'function' ? ckResumeNuitAJour : null,
      compromisVerrouilleParSaVente: typeof compromisVerrouilleParSaVente === 'function' ? compromisVerrouilleParSaVente : null,
      bienVenduPourStatut: typeof bienVenduPourStatut === 'function' ? bienVenduPourStatut : null,
      repartitionChaineId: typeof repartitionChaineId === 'function' ? repartitionChaineId : null,
      viser: (a) => { __visee = a; }, poserAffaires: (l) => { statusChangeAffaires = l; } };`;
  const js = esbuild.transformSync(code, { loader: "ts" }).code;
  const ctx = { console, JSON, Set, Map, Array, String, Number, Math, Object, Date, Intl, Boolean, Promise };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api, absentes };
}

// ── LES LIGNES MESUREES EN BASE LE 23/10 (app_affaire_ledger, VA6482) ──
const ACQ_OFFRE = { id: "20000012", nom: "ESSAI 8 R3 PROPRIO", prenom: "Seconde", civilite: "Mme.",
  coordonnees: { email: "essai.8.r3.proprio.23102026@example.invalid", portable: "0600000195" } };
const ACQ_HK = { ...ACQ_OFFRE, id: "605967" };
const MANDANTS_VENTE = [
  { id: "189298", nom: "PHILIBERT", prenom: "Louis", civilite: "M." },
  { id: "189301", nom: "PHILIBERT", prenom: "Jean-Pierre et Brigitte", civilite: "Mr./Mme" },
  { id: "189302", nom: "MANOA", prenom: "Pascale", civilite: "" },
  { id: "189303", nom: "", prenom: "", civilite: "Mr./Mme" },
  { id: "279528", nom: "SAMUEL - PHILIBERT BERTILLE", prenom: "", civilite: "" },
  { id: "603953", nom: "TESTCLAUDE", prenom: "CLAUDE", civilite: "Mme." },
  { id: "605963", nom: "ESSAI 8 R3", prenom: "Chaine", civilite: "M." },
];
const commun = { app_dossier_id: 1068399, hektor_annonce_id: 24113, numero_mandat: "18787", present_in_hektor: true,
  date: "2026-10-23", app_contact_id: 20000012, hektor_acquereur_id: "605967" };
const OFFRE_REFUSEE = { ...commun, app_affaire_id: 1001378, app_chaine_id: 1001378, kind: "offre", state: "refused",
  hektor_affaire_id: "33110", montant: "120000", app_contact_id: 20000011, hektor_acquereur_id: "605963",
  acquereur_json: { id: "20000011", nom: "ESSAI 8 R3", prenom: "Chaine", civilite: "M." },
  acquereurs_json: [{ id: "20000011", nom: "ESSAI 8 R3", prenom: "Chaine", civilite: "M." }] };
const OFFRE = { ...commun, app_affaire_id: 1001381, app_chaine_id: 1001381, kind: "offre", state: "accepted",
  hektor_affaire_id: "33112", montant: "118000", jours_validite: "20", taux_honoraires: "5.08",
  honoraires_sortie: "6000", honoraires_entree_app: "7000", honoraires_sortie_app: "6000", charge_commission_app: "acquereur",
  acquereur_json: ACQ_OFFRE, acquereurs_json: [ACQ_OFFRE] };
const COMPROMIS = { ...commun, app_affaire_id: 1001382, app_chaine_id: 1001381, kind: "compromis", state: "en_cours",
  hektor_affaire_id: "50132", montant: "118000.00", date_acte: "2027-02-15", sequestre: "6500.00",
  prix_net_vendeur: "105000.00", honoraires_entree: "7000.00", honoraires_sortie: "6000.00", taux_honoraires: "5.08",
  notaire_mandant_id: "10355906", notaire_mandant_nom: "Me. Eric PAILHES", notaire_acquereur_id: "10064499",
  notaire_acquereur_nom: null, charge_commission_app: "acquereur", date_fin_retractation: "2026-11-20",
  mandants_json: [{ id: "603953", nom: "TESTCLAUDE", prenom: "CLAUDE", civilite: "Mme." }],
  acquereur_json: ACQ_HK, acquereurs_json: [ACQ_HK] };
const VENTE = { ...commun, app_affaire_id: 1001383, app_chaine_id: 1001381, kind: "vente", state: "en_cours",
  hektor_affaire_id: "23355", montant: "118000.00", prix_net_vendeur: "105000.00", honoraires_entree: "7000.00",
  honoraires_sortie: "6000.00", taux_honoraires: "5.08", notaires_json: null,
  notaire_mandant_id: "10355906", notaire_mandant_nom: "Me. Eric PAILHES", notaire_acquereur_id: "10064499",
  notaire_acquereur_nom: null, charge_commission_app: "acquereur", mandants_json: MANDANTS_VENTE,
  acquereur_json: ACQ_HK, acquereurs_json: [ACQ_HK] };
// L'ordre de loadAffairesForDossier : date decroissante, puis app_affaire_id decroissant.
const LIGNES = [VENTE, COMPROMIS, OFFRE, OFFRE_REFUSEE];

// La lecture de l'assistant : celle du compromis porte SES conditions ; celle de la vente, autre chose.
const CONSOLE = new Map([
  [1001382, { app_affaire_id: 1001382, parties_json: { notaires_acquereur: [{ id: "10064499", nom: "Me. NOTAIRE ACQ" }] },
    conditions_suspensives: [{ libelle: "Pret", jours: "45" }] }],
  [1001383, { app_affaire_id: 1001383, parties_json: {}, conditions_suspensives: [] }],
]);
const rep = (cote, rang, nom) => ({ cote, rang, hektorUserId: String(rang), nomAuMoment: nom, pourcentage: 25, origine: "saisie" });
const APP_DONNEES = (avecConditions) => ({
  carnet: new Map([
    [1001381, { honoraires: "6000", notaire_id: "10064499", numero_mandat: "18787", prix_publique: "128787", taux_honoraires: "5.08", jours_retractation: "10" }],
    [1001382, { prix_publique: "112000", taux_honoraires: "5.08", jours_retractation: "28" }],
  ]),
  repartition: new Map([["1001381", [rep("entree", 1, "FRANCK GERPHAGNON"), rep("entree", 2, "Alice RONDEAU"), rep("sortie", 1, "FRANCK GERPHAGNON"), rep("sortie", 2, "Alice RONDEAU")]]]),
  conditions: new Map(avecConditions ? [[1001382, [{ libelle: "Obtention de pret", jours: 60, etat: "attente" }]]] : []),
  notes: new Map([[1001383, "Acte chez Me PAILHES"]]),
});

function essai(api) {
  const R = [];
  const ok = (nom, vrai, detail) => R.push({ nom, vrai: Boolean(vrai), detail });
  const chaines = api.grouperAffairesParChaine(LIGNES);
  const ch = chaines.find((c) => c.chaine === "1001381");
  const af = api.ckAffaireDepuisChaine(ch, null, CONSOLE, APP_DONNEES(false));
  const afC = api.ckAffaireDepuisChaine(ch, null, CONSOLE, APP_DONNEES(true));
  const rows = (g) => (af.lignesApp && af.lignesApp[g]) || [];
  const val = (g, k) => (rows(g).find((r) => r[0] === k) || [])[1] || "";
  const J = (x) => JSON.stringify(x);

  ok("C4 le nom de l'acquereur n'est plus double (« X et X »)",
    !/ et /.test(api.affaireAcquereursNoms(ch.lignes)), api.affaireAcquereursNoms(ch.lignes));
  ok("C3 la carte du compromis lit SA lecture : ses conditions, pas celles de la vente",
    af.console && /Pret/.test(af.console.conditions), J(af.console));
  ok("C3 le notaire de l'acquereur du compromis est nomme (registre + lecture)",
    af.console && af.console.notaireAcq === "Me. NOTAIRE ACQ", J(af.console));
  ok("le notaire du vendeur du compromis vient du registre des le clic",
    af.console && af.console.notaireVend === "Me. Eric PAILHES", J(af.console));
  ok("C2 la carte de la vente a ses notaires sans attendre la nuit",
    af.vente && /PAILHES \(vendeur\)/.test(af.vente.notaires) && /NOTAIRE ACQ \(acquéreur\)/.test(af.vente.notaires), af.vente && af.vente.notaires);
  ok("offre : honoraires vendeur, charge, taux, mandat, notaire",
    /7\s?000/.test(val("offre", "Honoraires vendeur (agence)")) && val("offre", "Charge de la commission") === "Acquéreur"
      && val("offre", "Taux honoraires acquéreur") === "5,08 %" && val("offre", "N° de mandat") === "18787"
      && val("offre", "Notaire acquéreur") === "Me. NOTAIRE ACQ", J(rows("offre")));
  {
    // ⑧ N (23/10) : le notaire du VENDEUR d'une offre n'existe qu'au carnet.
    const avecN = APP_DONNEES(false);
    avecN.carnet.set(1001381, { ...avecN.carnet.get(1001381), notaire_mandant_id: "10355906", notaire_mandant_nom: "Me. Eric PAILHES" });
    const afN = api.ckAffaireDepuisChaine(ch, null, CONSOLE, avecN);
    const ligneN = ((afN.lignesApp && afN.lignesApp.offre) || []).find((r) => r[0] === "Notaire vendeur");
    ok("N : la carte de l'offre montre le notaire du vendeur garde au carnet",
      ligneN && ligneN[1] === "Me. Eric PAILHES", J(afN.lignesApp && afN.lignesApp.offre));
    ok("N : sans carnet, pas de ligne « Notaire vendeur » (pas de tiret)",
      !rows("offre").some((r) => r[0] === "Notaire vendeur"), J(rows("offre")));
  }
  ok("offre : la retractation et le prix public PRE-REMPLIS ne s'affichent pas",
    !rows("offre").some((r) => /Rétractation|Prix public/.test(r[0])), J(rows("offre")));
  ok("compromis : acquereur (une fois), mandant, prix public, honoraires acquereur",
    val("compromis", "Acquéreur(s)") === "Mme. Seconde ESSAI 8 R3 PROPRIO" && val("compromis", "Mandant(s)") === "Mme. CLAUDE TESTCLAUDE"
      && /112\s?000/.test(val("compromis", "Prix public")) && /6\s?000/.test(val("compromis", "Honoraires acquéreur")), J(rows("compromis")));
  // 7 mandants chez Hektor, dont une fiche sans nom ni prenom (« Mr./Mme » seul) : 6 noms.
  ok("vente : les mandants NOMMES de Hektor (6 sur 7), le net vendeur, la note",
    val("vente", "Mandant(s)").split(", ").length === 6 && /105\s?000/.test(val("vente", "Prix net vendeur"))
      && val("vente", "Note") === "Acte chez Me PAILHES", J(rows("vente")));
  // ⚠ LES 4 PARTS SE COMPTENT ENSEMBLE SUR 100 % (regle de la modale et de la base) : 4 x 25 est
  //   une repartition COMPLETE -- aucune ligne « Total ». La 1re version disait « 50 % » a tort.
  ok("la repartition : 4 lignes, et 4 x 25 % = 100 % ne signale RIEN",
    af.repartition && af.repartition.length === 4 && !af.repartition.some((r) => /^Total/.test(r[0]))
      && af.repartition[0][1] === "FRANCK GERPHAGNON · 25 %", J(af.repartition));
  {
    const incomplete = APP_DONNEES(false);
    incomplete.repartition.set("1001381", [rep("entree", 1, "FRANCK GERPHAGNON"), rep("sortie", 1, "Alice RONDEAU")]);
    const afI = api.ckAffaireDepuisChaine(ch, null, CONSOLE, incomplete);
    ok("une repartition a 50 % le DIT : « 50 % attribués à personne »",
      afI.repartition && afI.repartition.length === 3 && /^Total$/.test(afI.repartition[2][0])
        && /50 % attribués à personne/.test(afI.repartition[2][1]), J(afI.repartition));
  }
  ok("nos conditions passent AVANT celles de Hektor (pas les deux)",
    afC.console && afC.console.conditions === "" && /Obtention de pret · 60 j · en attente/.test(
      ((afC.lignesApp.compromis || []).find((r) => r[0] === "Conditions suspensives") || [])[1] || ""), J(afC.console));

  // C1 : le resume de nuit refait a partir du registre
  const det = api.ckDetailDepuisRegistre ? api.ckDetailDepuisRegistre(LIGNES, "18787", "18787") : null;
  ok("C1 les parties viennent du registre : acquereur 605967, mandant 189298, notaire de la vente",
    det && det.vente && det.vente.acquereur.id === "605967" && det.vente.mandant.id === "189298"
      && det.vente.notaire && det.vente.notaire.id === "10355906" && det.compromis.mandant.id === "603953", J(det));
  ok("C1 l'offre refusee de l'autre chaine n'est pas retenue",
    det && det.offre && det.offre.id === "33112", J(det && det.offre));
  ok("C1 un resume de nuit qui a deja vu la vente fait foi (comme avant)",
    api.ckResumeNuitAJour && det && api.ckResumeNuitAJour({ vente: { id: "23355" } }, det) === true);
  ok("C1 un resume de nuit en retard (sans la vente) cede la place au registre",
    api.ckResumeNuitAJour && det && api.ckResumeNuitAJour({ compromis: { id: "50132" } }, det) === false);
  ok("C1 un autre mandat (cycle passe) ne prend pas les lignes du mandat courant",
    api.ckDetailDepuisRegistre && api.ckDetailDepuisRegistre(LIGNES, "17000", "18787") === null);

  // V (23/10) : le compromis verrouille par sa vente
  const verrou = api.compromisVerrouilleParSaVente;
  ok("V : le compromis d'une chaine vendue est verrouille, par la vente 23355",
    verrou && (verrou(LIGNES, COMPROMIS) || {}).hektor_affaire_id === "23355", J(verrou && verrou(LIGNES, COMPROMIS)));
  ok("V : une vente EFFACEE chez Hektor ne verrouille pas ; une offre n'est pas concernee",
    verrou && verrou([{ ...VENTE, present_in_hektor: false }, COMPROMIS, OFFRE], COMPROMIS) === null
      && verrou(LIGNES, OFFRE) === null, "");
  // ⑧ (23/10) : un bien vendu ne prend plus de NOUVELLE transaction (« Envoyer vers » disparait)
  const vendu = api.bienVenduPourStatut;
  const fiche = (statut, mandat) => ({ statut_annonce: statut, numero_mandat: mandat });
  ok("vendu : VA6482 « Vendu » -> fermé par la vente 23355 (nommée)",
    vendu && (vendu(fiche("Vendu", "18787"), LIGNES) || {}).hektor_affaire_id === "23355", J(vendu && vendu(fiche("Vendu", "18787"), LIGNES)));
  ok("vendu : juste après la vente, la fiche dit encore « Sous compromis » -> le registre suffit",
    vendu && (vendu(fiche("Sous compromis", "18787"), LIGNES) || {}).hektor_affaire_id === "23355", "");
  ok("vendu : une vente SANS numéro Hektor (travail échoué) ne ferme rien",
    vendu && vendu(fiche("Sous compromis", "18787"), [{ ...VENTE, hektor_affaire_id: null }, COMPROMIS, OFFRE]) === null, "");
  ok("vendu : une vente EFFACÉE chez Hektor ne ferme rien",
    vendu && vendu(fiche("Sous compromis", "18787"), [{ ...VENTE, present_in_hektor: false }, COMPROMIS, OFFRE]) === null, "");
  ok("vendu : la REVENTE (nouveau mandat, statut actif) garde ses boutons",
    vendu && vendu(fiche("Actif", "19001"), LIGNES) === null, "");
  ok("vendu : le statut seul suffit (registre pas encore lu) ; pas de fiche -> rien",
    vendu && vendu(fiche("Vendu", "18787"), []) === true && vendu(null, LIGNES) === null, "");

  // ⑧ (23/10) : le nom du notaire par sa fiche contact -- la lecture de l'assistant porte le numero de
  // HEKTOR (122190), le registre le notre (10064499).
  {
    const consoleHk = new Map([[1001382, { app_affaire_id: 1001382, parties_json: { notaires_acquereur: [{ id: "122190", nom: "CORNU SELARL" }] }, conditions_suspensives: [] }]]);
    const avecNoms = { ...APP_DONNEES(false), nomsContacts: new Map([["10064499", "Tiffany SELARL CORNU"], ["122190", "Tiffany SELARL CORNU"]]) };
    const afNoms = api.ckAffaireDepuisChaine(ch, null, consoleHk, avecNoms);
    const afSans = api.ckAffaireDepuisChaine(ch, null, consoleHk, APP_DONNEES(false));
    ok("le notaire de l'acquereur est nomme par sa fiche contact (deux numeros)",
      afNoms.console && afNoms.console.notaireAcq === "Tiffany SELARL CORNU" && /Tiffany SELARL CORNU \(acquéreur\)/.test(afNoms.vente.notaires),
      J({ c: afNoms.console, v: afNoms.vente && afNoms.vente.notaires }));
    ok("sans la fiche, « Contact 10064499 » (on ne fabrique pas de nom)",
      afSans.console && afSans.console.notaireAcq === "Contact 10064499", J(afSans.console));
  }

  // C5 : la modale
  let c5 = null, c5creation = null;
  if (api.repartitionChaineId) {
    api.poserAffaires(LIGNES);
    api.viser(COMPROMIS);
    c5 = api.repartitionChaineId();
    api.viser(null);
    api.poserAffaires([OFFRE_REFUSEE, { ...OFFRE, app_affaire_id: 1001390, app_chaine_id: 1001390, state: "accepted" }]);
    c5creation = api.repartitionChaineId();
  }
  ok("C5 rouvrir le compromis APRES la vente retrouve la chaine 1001381", c5 === "1001381", J(c5));
  ok("C5 a la creation (rien de vise), l'ancienne regle joue : la chaine de l'offre ouverte", c5creation === "1001390", J(c5creation));
  return R;
}

(async () => {
  let neuf, ancien;
  try { neuf = monter(fs.readFileSync(path.join(RACINE, APP), "utf8")); }
  catch (e) { console.log("⛔ montage impossible :", e.message); process.exit(2); }
  if (neuf.absentes.length) { console.log("⛔ pieces absentes :", neuf.absentes.join(", ")); process.exit(2); }
  const resultats = essai(neuf.api);
  let echecs = 0;
  for (const r of resultats) {
    console.log(`${r.vrai ? "  OK  " : "ECHEC "} ${r.nom}${r.vrai ? "" : " -- " + (r.detail || "")}`);
    if (!r.vrai) echecs++;
  }
  // TEMOIN INVERSE
  const avant = versionDavant();
  if (avant) {
    try {
      ancien = monter(avant);
      const anciens = essai(ancien.api);
      const tombes = anciens.filter((r) => !r.vrai).map((r) => r.nom);
      console.log(`\nTEMOIN INVERSE (version d'avant, HEAD) : ${tombes.length} controle(s) sur ${anciens.length} y echouent`);
      for (const n of tombes) console.log("   x " + n);
    } catch (e) { console.log("\nTEMOIN INVERSE : la version d'avant ne se monte pas -- " + e.message); }
  } else console.log("\n⚠ temoin inverse NON FAIT (git show HEAD impossible)");
  console.log(echecs ? `\n⛔ ${echecs} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs ? 1 : 0);
})();
