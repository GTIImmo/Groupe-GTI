#!/usr/bin/env node
"use strict";
/**
 * ⑧ NOTAIRE, ÉTAPE 4 — LA FICHE NOTAIRE : LES RÈGLES.   28/10/2026
 *
 * On EXÉCUTE le code réel : la partie « règles » de src/FicheNotaire.tsx (construireVueNotaire et ses aides) est découpée,
 * transformée par esbuild et jouée par vm, À DATE FIXE (2026-10-28). Données SYNTHÉTIQUES pour chaque règle.
 * Décisions de Frédéric (28/10, note des types §49.6-49.7) : « en cours » borné (acte prévu non passé, ou moins de 6 mois sans
 * date d'acte), le reste « À vérifier » ; honoraires = entrée + sortie (reconfirmé) ; un dossier = une chaîne.
 * MUTANT : sans la borne des 6 mois, un compromis de 2024 redevient « en cours » -> attrapé.
 * En option, un passage sur des données RÉELLES lues dans une transaction annulée (argument : un fichier JSON, jamais versionné).
 *
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_fiche_notaire.cjs [fiches_reelles.json]
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const SRC = path.resolve(__dirname, "src", "FicheNotaire.tsx");
const APP = path.resolve(__dirname, "src", "App.tsx");
const AUJ = "2026-10-28";

function monter(src) {
  const s = src.replace(/\r\n/g, "\n");
  const i = s.indexOf("// ─── les règles, en fonctions pures");
  const f = s.indexOf("// ─── le chargement");
  if (i < 0 || f < 0) return { erreur: "la partie « règles » est introuvable dans FicheNotaire.tsx" };
  const partie = s.slice(i, f).replace(/^export (?=(function|const|type) )/gm, "");
  const js = esbuild.transformSync(partie + "\nthis.api = { construireVueNotaire, coteDuDossier, echeanceCondition, conditionLevee, piecesDuDossier, exportCsvNotaire };", { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp, Date, Math, Intl };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api };
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log((ok ? "OK    " : "ECHEC ") + nom + (ok ? "" : "  -> " + (detail || "")));
  if (!ok) echecs += 1;
}

let n = 0;
const d = (o) => ({ app_affaire_id: ++n, kind: "compromis", state: "active", date: null, date_acte: null, date_fin_retractation: null,
  montant: "200000.00", commission_agence: null, prix_net_vendeur: null, sequestre: "0.00", app_chaine_id: n, numero_mandat: null,
  hektor_annonce_id: 60000 + n, app_dossier_id: 900 + n, cotes: ["notaire_vendeur"], vente_chaine: null, compromis_chaine: null,
  vendeurs: [{ id: "1", nom: "M. Vendeur" }], acquereurs: [{ id: "2", nom: "Mme Acheteuse" }], confreres: [],
  bien: { agence_nom: "Firminy", ville: "Firminy", titre_bien: "Maison" }, ...o });

const RETRACT = d({ date: "2026-10-20", date_fin_retractation: "2026-10-31", date_acte: "2027-01-15" });
const ACTE = d({ date: "2026-08-01", date_fin_retractation: "2026-08-11", date_acte: "2026-11-12", cotes: ["notaire_acquereur", "notaire_vendeur"] });
const AFIXER_RECENT = d({ date: "2026-06-01" });
const AFIXER_VIEUX = d({ date: "2024-10-31" });
const ACTE_PASSE = d({ date: "2026-01-05", date_acte: "2026-03-31" });
const VENDU = d({ date: "2026-01-13", date_acte: "2026-04-13", vente_chaine: { date: "2026-04-03", montant: "190000.00" } });
const ANNULE = d({ date: "2026-09-01", date_acte: "2026-12-01", state: "cancelled" });
const V1 = d({ kind: "vente", date: "2026-04-03", compromis_chaine: "2026-01-13", commission_agence: "0.00", honoraires_entree: "8000.00", honoraires_sortie: "1000.00", montant: "190000.00", app_chaine_id: VENDU.app_chaine_id,
  confreres: [{ id: "77", nom: "Maître Garnier", ville: "Firminy" }] });
const V2 = d({ kind: "vente", date: "2026-02-10", compromis_chaine: "2025-11-01", commission_agence: "6000.00", honoraires_entree: "6000.00", bien: { agence_nom: "Unieux" },
  confreres: [{ id: "77", nom: "Maître Garnier", ville: "Firminy" }, { id: "88", nom: "Maître Collet", ville: "Unieux" }] });
const V_VIEILLE = d({ kind: "vente", date: "2024-06-01", compromis_chaine: "2024-03-01", commission_agence: "5000.00", date_premier: true });
const COMPROMIS_DE_V1 = { ...VENDU, confreres: [{ id: "77", nom: "Maître Garnier", ville: "Firminy" }] }; // même chaîne que V1
const BRUTE = { contact: "10166165", mediane_agence_jours: 85,
  dossiers: [RETRACT, ACTE, AFIXER_RECENT, AFIXER_VIEUX, ACTE_PASSE, COMPROMIS_DE_V1, ANNULE, V1, V2, V_VIEILLE] };

const m = monter(fs.readFileSync(SRC, "utf8"));
if (m.erreur) { console.log("⛔ " + m.erreur); process.exit(2); }
const A = m.api;
const v = A.construireVueNotaire(JSON.parse(JSON.stringify(BRUTE)), AUJ);
const ids = (l) => l.map((x) => x.app_affaire_id).sort((a, b) => a - b).join(",");

// 1. « en cours » et « À vérifier » (décision 2)
verifier("en cours = compromis vivants sans vente, acte à venir ou de moins de 6 mois (3 sur 7 compromis)",
  ids(v.enCours) === ids([RETRACT, ACTE, AFIXER_RECENT]), ids(v.enCours));
verifier("À vérifier = sans vente, acte passé ou plus de 6 mois sans date (2), jamais cachés",
  ids(v.aVerifier) === ids([AFIXER_VIEUX, ACTE_PASSE]), ids(v.aVerifier));
verifier("la vente de la CHAÎNE clôt le compromis, même sans le notaire ; un compromis annulé n'est nulle part",
  !v.enCours.concat(v.aVerifier).some((x) => x.app_affaire_id === COMPROMIS_DE_V1.app_affaire_id || x.app_affaire_id === ANNULE.app_affaire_id));
// 2. les étapes
const etape = (x) => v.enCours.find((y) => y.app_affaire_id === x.app_affaire_id);
verifier("étapes : rétractation (J-3), acte prévu, date à fixer",
  etape(RETRACT).etape === "retractation" && etape(RETRACT).joursRestants === 3 && etape(ACTE).etape === "acte" && etape(AFIXER_RECENT).etape === "a_fixer",
  JSON.stringify(v.enCours.map((x) => [x.app_affaire_id, x.etape, x.joursRestants])));
verifier("ordre : rétractation d'abord, puis acte, puis date à fixer", v.enCours.map((x) => x.etape).join(",") === "retractation,acte,a_fixer");
// 3. les chiffres
verifier("dossiers en cours par côté : 2 vendeur, 0 acquéreur, 1 les deux",
  v.cotesEnCours.vendeur === 2 && v.cotesEnCours.acquereur === 0 && v.cotesEnCours.deux === 1, JSON.stringify(v.cotesEnCours));
verifier("actes ≤ 30 jours : 1 (le 12/11)", v.actes30.length === 1 && v.actes30[0].acte === "2026-11-12", JSON.stringify(v.actes30.map((x) => x.acte)));
verifier("ventes 12 mois : 2, honoraires = entrée + sortie (8 000 + 1 000 + 6 000 ; la commission vide ne compte pas)", v.ventes12.length === 2 && v.honoraires12 === 15000, `${v.ventes12.length} / ${v.honoraires12}`);
// (la vente de juin 2024 est DANS les 3 ans au 28/10/2026 : 80, 92 et 101 jours -> 92)
verifier("compromis -> acte : médiane du notaire sur 3 ans (80, 92, 101 j -> 92), médiane de l'agence 85",
  v.delaiNotaire === 92 && v.delaiAgence === 85, `${v.delaiNotaire} / ${v.delaiAgence}`);
const sansVieille = A.construireVueNotaire({ ...BRUTE, dossiers: BRUTE.dossiers.filter((x) => x !== V_VIEILLE) }, AUJ);
verifier("témoin : sans la vente de 2024, la médiane passe à 91 (80 et 101)", sansVieille.delaiNotaire === 91, String(sansVieille.delaiNotaire));
// 4. à venir
verifier("à venir : rétractation 31/10, acte 12/11, acte 15/01, puis la date à fixer en dernier",
  v.aVenir.map((x) => `${x.genre}:${x.date ?? "-"}`).join(" ") === "retractation:2026-10-31 acte:2026-11-12 acte:2027-01-15 a_fixer:-",
  v.aVenir.map((x) => `${x.genre}:${x.date ?? "-"}`).join(" "));
// 5. avec nous, confrères, partenaire depuis
const total = v.parAgence.reduce((s, a) => s + a.n, 0);
verifier("avec nous : un dossier = une chaîne (10 transactions, 9 chaînes : le compromis et la vente de V1 comptent une fois)",
  total === 9, `${total} : ${JSON.stringify(v.parAgence)}`);
verifier("par agence, la plus fréquente d'abord (Firminy 8, Unieux 1)",
  v.parAgence[0].agence === "Firminy" && v.parAgence[0].n === 8 && v.parAgence[1].agence === "Unieux", JSON.stringify(v.parAgence));
verifier("confrères : Garnier sur 2 dossiers (sa présence sur le compromis ET la vente de V1 compte une fois), Collet 1",
  v.confreres[0].id === "77" && v.confreres[0].n === 2 && v.confreres[1].id === "88" && v.confreres[1].n === 1, JSON.stringify(v.confreres));
verifier("partenaire depuis : la plus ancienne date (2024)", v.partenaireDepuis === "2024-03-01" || v.partenaireDepuis === "2024-06-01", v.partenaireDepuis);
// 6. robustesse
const vide = A.construireVueNotaire({ contact: "x", mediane_agence_jours: null, dossiers: [] }, AUJ);
verifier("une fiche vide ne casse rien (0 partout, pas de médiane)", vide.enCours.length === 0 && vide.delaiNotaire === null && vide.delaiAgence === null && vide.parAgence.length === 0);
const zero = A.construireVueNotaire({ ...BRUTE, dossiers: [d({ date: "0000-00-00", date_acte: "0000-00-00" })] }, AUJ);
verifier("une date « vide » de Hektor (0000-00-00) est traitée comme absente (À vérifier, pas une erreur)", zero.aVerifier.length === 1 && zero.enCours.length === 0);
verifier("le résultat ne dépend pas de l'ordre reçu",
  JSON.stringify(A.construireVueNotaire({ ...BRUTE, dossiers: [...BRUTE.dossiers].reverse() }, AUJ).enCours.map((x) => x.app_affaire_id)) === JSON.stringify(v.enCours.map((x) => x.app_affaire_id)));

// 6 bis. LES 4 BLOCS (28/10, §50-51)
// la condition de prêt : l'échéance = la date saisie, sinon le compromis + les jours ; levée par l'état ou la date de levée
verifier("condition : la date saisie l'emporte ; sinon compromis du 20/10 + 45 j = 04/12 ; sans jours ni date -> pas d'échéance",
  A.echeanceCondition({ libelle: "Obtention Crédit", jours: 45, date_echeance: "2026-11-30", etat: "attente" }, { date: "2026-10-20" }) === "2026-11-30"
  && A.echeanceCondition({ libelle: "Obtention Crédit", jours: 45, date_echeance: null, etat: "attente" }, { date: "2026-10-20" }) === "2026-12-04"
  && A.echeanceCondition({ libelle: "X", jours: null, date_echeance: null, etat: "attente" }, { date: "2026-10-20" }) === null);
verifier("condition levée : par son état, ou par une date de levée ; « attente » ne l'est pas",
  A.conditionLevee({ etat: "levee" }) && A.conditionLevee({ etat: "attente", date_levee: "2026-10-01" }) && !A.conditionLevee({ etat: "attente", date_levee: null }));
const AVEC_COND = { ...RETRACT, conditions: [{ libelle: "Obtention Crédit", jours: 45, date_echeance: null, etat: "attente", date_levee: null },
  { libelle: "Préemption mairie", jours: 0, date_echeance: null, etat: "levee", date_levee: "2026-10-22" }] };
const vc = A.construireVueNotaire({ ...BRUTE, dossiers: BRUTE.dossiers.map((x) => (x === RETRACT ? AVEC_COND : x)) }, AUJ);
verifier("« Conditions » compte les dossiers en cours avec une condition EN ATTENTE (1), et « À venir » porte son échéance (04/12), pas la levée",
  vc.avecCondition === 1 && vc.aVenir.some((x) => x.genre === "condition" && x.date === "2026-12-04" && x.libelle === "Obtention Crédit")
  && !vc.aVenir.some((x) => x.libelle === "Préemption mairie"), `${vc.avecCondition} / ${vc.aVenir.map((x) => x.genre + ":" + x.date).join(" ")}`);
// les pièces : reconnues par le nom, accents et majuscules compris
const p = A.piecesDuDossier(["Diagnostics DPE 2026.pdf", "COMPROMIS SIGNÉ.pdf", "Titre de propriété.pdf", "CNI M. Dupont.jpg", "Taxe foncière 2025.pdf", "photo salon.jpg"]);
const trouvees = p.pieces.filter((x) => x.trouve).map((x) => x.cle).join(",");
verifier("pièces : 5 reconnues sur 11 par le nom (accents, majuscules) ; une photo n'est pas une pièce",
  p.trouvees === 5 && p.total === 11 && trouvees === "titre,diagnostics,compromis,identite,taxe", `${p.trouvees} : ${trouvees}`);
verifier("pièces : aucun document -> 0 sur 11, toutes « à demander »", A.piecesDuDossier([]).trouvees === 0 && A.piecesDuDossier(null).total === 11);
// les vrais noms du mandat 18593 (28/10) : 4 ratés à rattraper, 1 fausse détection à éviter
const vrai = A.piecesDuDossier(["AUDIT ENERGETIQUE.pdf", "TF 2025 Parrain.pdf", "DONATION PARRAIN.pdf", "Parcelles PARRAIN.pdf", "mail de Mme Rous retard prêt 02.10.2026.pdf"]);
const vus = vrai.pieces.filter((x) => x.trouve).map((x) => x.cle).join(",");
verifier("vrais noms : audit énergétique = diagnostics, TF = taxe foncière, donation = titre, parcelles = cadastre ; un mail sur le prêt n'est PAS une offre de prêt",
  vus === "titre,diagnostics,taxe,cadastre", vus);
// l'export
const csv = A.exportCsvNotaire({ ...BRUTE, dossiers: [...BRUTE.dossiers, d({ date: "2026-10-27", bien: { titre_bien: 'Maison "jolie"; jardin', ville: "Firminy" } })] });
const lignesCsv = csv.replace(/^﻿/, "").split("\r\n");
verifier("export : BOM pour Excel, une ligne d'en-tête + une par dossier, séparateur « ; »",
  csv.startsWith("﻿") && lignesCsv.length === BRUTE.dossiers.length + 2 && lignesCsv[0].startsWith("Date;Type;État;Mandat;Bien"), String(lignesCsv.length));
verifier("export : le plus récent d'abord, et un « ; » ou un guillemet dans un texte est protégé",
  lignesCsv[1].startsWith("2026-10-27;") && lignesCsv[1].includes('"Maison ""jolie""; jardin"'), lignesCsv[1]);
verifier("export : les honoraires = entrée + sortie (V1 : 9000)", lignesCsv.some((l) => l.startsWith("2026-04-03;vente;") && l.includes(";9000;")),
  lignesCsv.find((l) => l.startsWith("2026-04-03;vente;")));
// (la ligne est découpée par ses bornes, sans motif : sa classe d'accents peut être écrite en caractères ou en codes)
const srcP = fs.readFileSync(SRC, "utf8");
const kP = srcP.indexOf("const sansAccent = ");
const eP = srcP.indexOf("toLowerCase()", kP) + "toLowerCase()".length;
const mutP = monter(kP < 0 ? "" : srcP.slice(0, kP) + "const sansAccent = (s: string) => s" + srcP.slice(eP));
verifier("MUTANT (sans retirer les accents ni les majuscules) : « COMPROMIS SIGNÉ » et « Titre de propriété » ne sont plus reconnus -> attrapé",
  !mutP.erreur && mutP.api.piecesDuDossier(["COMPROMIS SIGNÉ.pdf", "Titre de propriété.pdf"]).trouvees < 2);

// 7. le branchement dans la fiche V2 (App.tsx), derrière les deux interrupteurs
const app = fs.readFileSync(APP, "utf8").replace(/\r\n/g, "\n");
verifier("App.tsx : la fiche notaire n'est chargée que pour un notaire, derrière FICHE_NOTAIRE_V2 et TYPE_NOTAIRE_ECRAN",
  /const estFicheNotaire = FICHE_NOTAIRE_V2 && TYPE_NOTAIRE_ECRAN && primaryCategory === 'notaire'/.test(app)
  && /useFicheNotaire\(String\(props\.contact\.hektor_contact_id \?\? ''\), estFicheNotaire\)/.test(app));
const blocs = ["<NotaireKpis", "<NotaireDossiers", "<NotaireAVenir", "<NotaireVentesEtAvecNous", "<NotaireInterlocuteurs"];
verifier("App.tsx : les 5 blocs sont posés, chacun sous sa condition", blocs.every((b) => app.split(b).length === 2), blocs.filter((b) => app.split(b).length !== 2).join(","));
verifier("App.tsx : « Recherche & rapprochement » ne s'efface que pour un notaire SANS recherche active",
  /const masquerRecherche = estFicheNotaire && Number\(props\.contact\.active_search_count \?\? 0\) === 0/.test(app) && /\{masquerRecherche \? null : \(<>/.test(app));
verifier("App.tsx : la bande « Biens & mandats liés » reste (décision 3)", /Lot 3 — Bande « Biens & mandats liés »/.test(app.slice(app.indexOf("{masquerRecherche ? null : (<>"))));

// 8. MUTANT : sans la borne des 6 mois
const mut = monter(fs.readFileSync(SRC, "utf8").replace("decaler(aujourdhui, -183)", "decaler(aujourdhui, -3650)"));
verifier("MUTANT (sans la borne des 6 mois) : le compromis de 2024 redevient « en cours » -> attrapé",
  !mut.erreur && mut.api.construireVueNotaire(JSON.parse(JSON.stringify(BRUTE)), AUJ).enCours.some((x) => x.app_affaire_id === AFIXER_VIEUX.app_affaire_id));

// 9. données réelles (facultatif)
const reel = process.argv[2];
if (reel && fs.existsSync(reel)) {
  const fiches = JSON.parse(fs.readFileSync(reel, "utf8"));
  for (const [id, f] of Object.entries(fiches)) {
    const t0 = Date.now(); const vr = A.construireVueNotaire(f, AUJ); const ms = Date.now() - t0;
    console.log(`      réel ${id} : ${f.dossiers.length} transactions -> en cours ${vr.enCours.length}, à vérifier ${vr.aVerifier.length}, ventes 12 m ${vr.ventes12.length} (${Math.round(vr.honoraires12)} €), `
      + `actes ≤ 30 j ${vr.actes30.length}, délai ${vr.delaiNotaire} j / agence ${vr.delaiAgence} j, agences ${vr.parAgence.length}, confrères ${vr.confreres.length}, depuis ${vr.partenaireDepuis} -- ${ms} ms`);
    verifier(`réel ${id} : calculé sans erreur, en moins de 200 ms, rien de compté deux fois`, ms < 200
      && new Set(vr.enCours.map((x) => x.app_affaire_id)).size === vr.enCours.length);
  }
}

console.log(echecs ? `\n${echecs} contrôle(s) en échec` : "\ntout vert");
process.exit(echecs ? 1 : 0);
