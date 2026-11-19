#!/usr/bin/env node
"use strict";
/**
 * ÉTAPE 4, CHAPITRE 6 — LOT 0 : LES 10 DÉFAUTS DU §84.6 (note ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT, §89-§90).   19/11/2026
 *
 * Ce que cet essai EXÉCUTE (code réel découpé dans App.tsx, esbuild + vm) :
 *   D3  le statut du syndicat dicté se résout en CODE de la liste (et un texte inconnu laisse la case vide) ;
 *   D4  un type de pièce inconnu n'est reconnu comme rien (plus de « Chambre » par défaut à la lecture).
 * Ce qu'il GARDE (les ancres des corrections, prouvées à l'écran le 19/11 en mode maquette, §90) :
 *   D1 D2 D5 D6 D8a D9 D10.
 * ⚠ TÉMOIN INVERSE : la version d'AVANT (le parent du commit du lot 0) doit échouer sur D3 et ne porter aucune ancre.
 *
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_etape4_lot0_defauts.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");
const ASSISTANT = path.resolve(__dirname, "src", "lib", "assistant.ts");
const JPEG = path.resolve(__dirname, "src", "lib", "photoJpeg.ts");

function tranche(src, debut, fin) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf(fin, i);
  return f < 0 ? null : src.slice(i, f + fin.length);
}

function monter(src) {
  const s = src.replace(/\r\n/g, "\n");
  const morceaux = [
    tranche(s, "type HektorSelectOption =", "}\n"),
    tranche(s, "const wizardProcedureOptions = [", "]\n"),
    tranche(s, "const hektorCompositionPieceTypeOptions: HektorSelectOption[] = [", "]\n"),
    tranche(s, "function normalizeDraftAnnonceScanText(", "\n}\n"),
    tranche(s, "function resolveWizardOptionValue(", "\n}\n"),
    tranche(s, "function compositionPieceTypeIdFromLabel(", "\n}\n"),
  ];
  if (morceaux.some((m) => !m)) return { erreur: "un morceau est absent d'App.tsx" };
  const code = morceaux.join("\n\n") + "\nthis.api = { wizardProcedureOptions, resolveWizardOptionValue, compositionPieceTypeIdFromLabel };";
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON };
  vm.createContext(ctx);
  vm.runInContext(esbuild.transformSync(code, { loader: "ts" }).code, ctx);
  return { api: ctx.api };
}

// La version d'AVANT : le parent du commit qui a introduit l'ancre (HEAD tant que rien n'est commité).
function versionAvant(marque) {
  const h = execFileSync("git", ["log", "--format=%H", "-S", marque, "--", ":(top)apps/hektor-v1/src/App.tsx"],
    { cwd: __dirname, encoding: "utf8" }).trim().split(/\s+/).filter(Boolean).pop();
  return execFileSync("git", ["show", `${h ? h + "^" : "HEAD"}:apps/hektor-v1/src/App.tsx`],
    { cwd: __dirname, encoding: "utf8", maxBuffer: 64 << 20 });
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "OK   " : "ECHEC"} ${nom}${ok ? "" : "  -> " + detail}`);
  if (!ok) echecs++;
}

const ENTREE_D3 = "{ ocr: 'coproSyndicateStatus', name: 'copropriete_statut_syndicat', kind: 'enum', options: wizardProcedureOptions }";
let src, ancien, assistant, jpeg;
try {
  src = fs.readFileSync(APP, "utf8");
  assistant = fs.readFileSync(ASSISTANT, "utf8");
  jpeg = fs.readFileSync(JPEG, "utf8");
  ancien = versionAvant(ENTREE_D3);
} catch (e) {
  console.log("IMPOSSIBLE de lire les sources ou git : " + e.message);
  process.exit(2);
}

const neuf = monter(src);
if (neuf.erreur) { console.log("IMPOSSIBLE de monter le code : " + neuf.erreur); process.exit(2); }
const { wizardProcedureOptions, resolveWizardOptionValue, compositionPieceTypeIdFromLabel } = neuf.api;

// ─── D3 : le statut du syndicat ───
verifier("D3 la table du scan résout la case en LISTE", src.includes(ENTREE_D3), "entrée absente");
const cas = [["procédure en cours", "PROCEDURE_EN_COURS"], ["Pas de procédure", "PAS_DE_PROCEDURE"], ["Procédure d'alerte", "ALERTE"],
  ["redressement", "REDRESSEMENT"], ["blabla", ""]];
for (const [dit, attendu] of cas) {
  const obtenu = resolveWizardOptionValue(dit, wizardProcedureOptions);
  verifier(`D3 « ${dit} » -> « ${attendu || "(vide)"} »`, obtenu === attendu, `obtenu « ${obtenu} »`);
}
verifier("D3 témoin inverse : AVANT, la case était un texte libre",
  ancien.includes("{ ocr: 'coproSyndicateStatus', name: 'copropriete_statut_syndicat', kind: 'text' }") && !ancien.includes(ENTREE_D3),
  "la version d'avant ne porte pas l'ancien texte");

// ─── D4 : la pièce inconnue ───
verifier("D4 « Chaufferie » n'est reconnue comme aucun type", compositionPieceTypeIdFromLabel("Chaufferie") === "", "reconnue");
verifier("D4 « Séjour » reste reconnu (Salon/sejour)", compositionPieceTypeIdFromLabel("Séjour") === "2", "non reconnu");
verifier("D4 la lecture garde la pièce SANS type", src.includes("return idTypePiece ? brouillon : { ...brouillon, idTypePiece: '', typeLabel: libelle, detailPiece: detail || libelle }"), "ancre absente");
verifier("D4 « Créer » demande le type", src.includes("const piecesSansType = draftAnnonceCompositionPieces.filter(") && src.includes("setDraftAnnonceStep('composition')"), "ancre absente");
verifier("D4 le choix vide n'existe que pour une pièce sans type", src.includes("{piece.idTypePiece === '' ? <option value=\"\">— type à choisir —</option> : null}"), "ancre absente");
verifier("D4 témoin inverse : AVANT, aucune pièce sans type", !ancien.includes("piecesSansType"), "déjà présent avant");

// ─── D5 : la date d'estimation ───
verifier("D5 le remplisseur a l'option « date du jour »", src.includes("if (!value('estimationDate') && dateDuJour) {"), "ancre absente");
verifier("D5 l'assistant ne la pose que pour une estimation", src.includes("applyDraftAnnonceScan(fusion, { dateDuJour: o.genre === 'estimation' })"), "ancre absente");
verifier("D5 le scan garde son défaut (appel sans option)", /\n\s+applyDraftAnnonceScan\(scan\)\n/.test(src.replace(/\r\n/g, "\n")), "appel du scan changé");

// ─── D6 : la marque et le compte ───
verifier("D6 l'adresse du haut a sa clé", src.includes("address: 'adresse_haut'") && src.includes("marqueAssistant('adresse_haut')"), "ancre absente");
verifier("D6 le compte suit les cases RÉELLES", src.includes("const draftPrefillReels = (draftPrefillAssistant?.champs ?? []).filter(") && src.includes("{draftPrefillReels.length} case"), "ancre absente");
verifier("D6 plus de marque sur la case Hektor « adresse » par erreur", !src.includes("marqueAssistant('adresse')}"), "ancienne marque présente");

// ─── D1 / D2 : le mandant et le négociateur ───
verifier("D1 le mandant de l'assistant est remis en tête de liste", src.includes("rows = [{ hektor_contact_id: mandantAssistant.hektor_contact_id, display_name: mandantAssistant.nom } as MandantContactSearchOption, ...rows]"), "ancre absente");
verifier("D1 la fenêtre ouverte à la main l'oublie", src.includes("draftMandantAssistantRef.current = null  // 19/11 (§89, D1-D2)"), "ancre absente");
verifier("D2 l'agence est prise dans la liste des négociateurs", src.includes("|| hektorNegotiators.find((item) => item.idUser === o.negociateur?.hektor_user_id)?.agenceNom"), "ancre absente");
verifier("D2 l'effacement est DIT", src.includes("Le négociateur proposé par l'assistant (${negoAssistant.nom}) n'est pas dans la liste"), "ancre absente");

// ─── D8 a : fermer l'éditeur ───
const fermetures = (src.match(/fermerEditeurAvis\(\(\) =>/g) || []).length;
verifier("D8a les 5 portes de fermeture de l'éditeur demandent confirmation (Retour + 4 fonds)", fermetures === 5, `${fermetures} trouvées`);
verifier("D8a « Générer » solde la saisie", src.includes("saisieNonGeneree.current = false  // la saisie est dans la charge du PDF"), "ancre absente");

// ─── D9 : les 4 cases ───
verifier("D9 DPE et GES en liste A à G", src.includes("{(['dpe', 'ges'] as const).map((cle) => (") && src.includes("[...'ABCDEFG', ...(draft[cle] && ![...'ABCDEFG'].includes(draft[cle]) ? [draft[cle]] : [])]"), "ancre absente");
verifier("D9 chauffage et exposition", src.includes("upd('chauffage', e.target.value)") && src.includes("upd('exposition', e.target.value)"), "ancre absente");
verifier("D9 témoin inverse : AVANT, aucune case chauffage", !ancien.includes("upd('chauffage', e.target.value)"), "déjà présente avant");

// ─── D10 : le WebP ───
verifier("D10 la conversion ne touche que le WebP", jpeg.includes("if (fichier.type !== 'image/webp') return fichier") && jpeg.includes("toile.toBlob(resoudre, 'image/jpeg', qualite)"), "ancre absente");
verifier("D10 le trombone convertit avant le dépôt", assistant.includes("fichier = await webpEnJpeg(fichier)"), "ancre absente");
verifier("D10 l'étape 2 de la fenêtre convertit", src.includes("const converties = await Promise.all(selectedFiles.map((file) => webpEnJpeg(file)))"), "ancre absente");

// ─── Le crochet d'essai de la maquette ne doit JAMAIS partir ───
verifier("le crochet d'essai temporaire est retiré", !assistant.includes("ESSAI-TEMPORAIRE") && !assistant.includes("__ouvertureEssai"), "crochet présent");

console.log(echecs ? `\n${echecs} contrôle(s) en échec` : "\nTout est vert");
process.exit(echecs ? 1 : 0);
