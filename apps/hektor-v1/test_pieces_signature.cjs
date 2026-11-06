#!/usr/bin/env node
"use strict";
/**
 * A.2 P8-4 — OUVRIR L'ORIGINAL ET LES PREUVES D'UN DOCUMENT SIGNÉ, ET LE CODE À USAGE UNIQUE.             06/11/2026
 * On EXÉCUTE le code réel (src/lib/piecesSignature.ts, esbuild + vm) sur des métadonnées À LA FORME RÉELLE (relevées
 * le 06/11 : le mandat Youtrust de 61398, un signé ImmoSign avec et sans ZIP au coffre), puis on vérifie les
 * branchements (App.tsx, PiecesSignature.tsx, api.ts) et les deux patchs SQL.
 * NE LANCE NI SERVEUR NI REQUÊTE.     node apps/hektor-v1/test_pieces_signature.cjs
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
let P;
try {
  const { outputFiles } = esbuild.buildSync({ entryPoints: [path.resolve(__dirname, "src", "lib", "piecesSignature.ts")], bundle: true, write: false, format: "cjs", platform: "neutral" });
  const module = { exports: {} };
  vm.runInNewContext(outputFiles[0].text, { module, exports: module.exports });
  P = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const J = (v) => JSON.stringify(v);

const DOSSIER = "annonces/61398/documents/f0d73f5a-b283-407d-a5f8-49496deb7027";
const youtrust = {
  storage_path: `${DOSSIER}/signed/Mandat de vente - 18420 - signe.pdf`,
  metadata_json: {
    local_archive_path: "C:\\Hektor\\HektorConsoleDocuments\\annonces\\61398\\documents\\f0d73f5a-b283-407d-a5f8-49496deb7027\\Mandat de vente - 18420.pdf",
    signed_document: {
      provider: "youtrust", storage_bucket: "hektor-console-documents", storage_path: `${DOSSIER}/signed/Mandat de vente - 18420 - signe.pdf`,
      preuves: [
        { index: 1, role: "mandant", filename: "preuves-1-mandant.pdf", storage_path: `${DOSSIER}/proofs/preuves-1-mandant.pdf` },
        { index: 2, role: "mandant", filename: "preuves-2-mandant.pdf", storage_path: `${DOSSIER}/proofs/preuves-2-mandant.pdf` },
        { index: 3, role: "mandataire", filename: "preuves-3-mandataire.pdf", storage_path: `${DOSSIER}/proofs/preuves-3-mandataire.pdf` },
      ],
    },
  },
};
const D2 = "annonces/11832/documents/0129e839-b57d-4069-b716-3730d93f162b";
const immosign = (zipAuCoffre) => ({
  storage_path: `${D2}/signed/Mandat (Avec saisie du numero) (Vente) - signe.pdf`,
  metadata_json: {
    local_archive_path: "C:\\Hektor\\HektorConsoleDocuments\\annonces\\11832\\documents\\0129e839-b57d-4069-b716-3730d93f162b\\Mandat (Avec saisie du numero) (Vente) - 580.pdf",
    signed_document: { storage_bucket: "hektor-console-documents", storage_path: `${D2}/signed/Mandat (Avec saisie du numero) (Vente) - signe.pdf` },
    immosign_files: {
      proofs_zip: { filename: "preuves-530.zip", storage_path: zipAuCoffre ? `${D2}/immosign/preuves-530.zip` : null, storage_bucket: zipAuCoffre ? "hektor-console-documents" : null },
      procedure_zip: { filename: "procedure-530.zip", storage_path: zipAuCoffre ? `${D2}/immosign/procedure-530.zip` : null, storage_bucket: zipAuCoffre ? "hektor-console-documents" : null },
    },
  },
});

// 1. Youtrust (la forme réelle de 61398).
{
  const p = P.piecesDeSignature(youtrust);
  controle("1. Youtrust : l'original + 3 preuves", p.length === 4 && p.filter((x) => x.genre === "preuve").length === 3, J(p.map((x) => x.cle)));
  controle("1. l'original est DÉDUIT au bon endroit (= l'objet du coffre relevé le 06/11)", p[0].storagePath === `${DOSSIER}/Mandat de vente - 18420.pdf`, p[0].storagePath);
  controle("1. chaque preuve porte la case de son signataire (pour le bouton « Preuve » du suivi)", J(p.filter((x) => x.genre === "preuve").map((x) => x.signataireIndex)) === "[1,2,3]");
  controle("1. le libellé dit le rôle", /mandataire \(négociateur\) \(case 3\)/.test(p[3].libelle), p[3].libelle);
}
// 2. ImmoSign.
{
  const p = P.piecesDeSignature(immosign(true));
  controle("2. ImmoSign avec ZIP au coffre : original + preuves (ZIP) + procédure (ZIP)", J(p.map((x) => x.cle)) === J(["original", "preuves-zip", "procedure-zip"]) && p[1].format === "zip", J(p.map((x) => x.cle)));
  controle("2. l'original ImmoSign au nom de la copie serveur (« - 580.pdf »)", p[0].storagePath === `${D2}/Mandat (Avec saisie du numero) (Vente) - 580.pdf`, p[0].storagePath);
  const s = P.piecesDeSignature(immosign(false));
  controle("2. TÉMOIN : ZIP sur le serveur seul (40 au 06/11) -> NON proposés, l'original reste", J(s.map((x) => x.cle)) === J(["original"]));
}
// 3. Rien à proposer.
{
  controle("3. TÉMOIN : document non signé -> aucune pièce", P.piecesDeSignature({ storage_path: `${DOSSIER}/Mandat.pdf`, metadata_json: { signature: { status: "pending" } } }).length === 0);
  controle("3. TÉMOIN : signé sans copie serveur connue -> pas d'original inventé", P.piecesDeSignature({ storage_path: `${D2}/signed/x.pdf`, metadata_json: { signed_document: { storage_path: `${D2}/signed/x.pdf` } } }).length === 0);
  controle("3. TÉMOIN : métadonnées vides -> rien, sans erreur", P.piecesDeSignature({}).length === 0);
}

// 4. LES BRANCHEMENTS.
const src = (f) => fs.readFileSync(path.resolve(__dirname, "src", f), "utf8");
const app = src("App.tsx").split(String.fromCharCode(13)).join("");
const fen = src("PiecesSignature.tsx");
const api = src(path.join("lib", "api.ts"));
const suivi = src("SuiviSignatairesYoutrust.tsx");
controle("4. l'interrupteur `signature_preuves` (absent = éteint)", /loadAppSettingActive\('signature_preuves'\)/.test(fen) && /useState\(false\)/.test(fen));
controle("4. le bouton « Preuves » : interrupteur + signé + au moins une pièce, dans la liste ET le suivi du mandat",
  (app.match(/preuvesActives && hasSignedFile && piecesDeSignature\(document\)\.length \?/g) || []).length === 2);
controle("4. la fenêtre est montée trois fois (liste v21, liste classique, suivi du mandat)", (app.match(/<PiecesSignatureFenetre document=\{piecesDoc\}/g) || []).length === 3);
controle("4. une pièce ABSENTE du coffre est grisée, sans geste (« Sur le serveur seulement »)",
  /disabled=\{occupe !== null \|\| absente\}/.test(fen) && /Sur le serveur seulement/.test(fen) && /\.list\(dossier, \{ search: nom, limit: 20 \}\)/.test(api));
controle("4. un ZIP se TÉLÉCHARGE, un PDF s'ouvre", /piece\.format === 'zip' \? \{ download: nom \} : undefined/.test(api));
controle("4. le suivi Youtrust : « Preuve » sur la ligne d'un signataire qui a signé", /l\.ton === 'signe' && l\.index != null && preuves\.some/.test(suivi) && /preuvesActives=\{preuvesActives\} document=/.test(app));

// 4 bis. ⭐ ESSAI RÉEL DU 06/11 : la fenêtre s'ouvrait 1 447 px AU-DESSUS de l'écran (le panneau de la fiche porte un
//   `transform`, qui piège un `position: fixed`). Les trois fenêtres de la signature sont montées dans le body.
{
  const envoi = src("EnvoiSignatureYoutrust.tsx");
  // La fenêtre du choix vit dans son propre fichier depuis sa refonte (06/11).
  const choix = src("ChoixSignatureFenetre.tsx");
  controle("4 bis. les trois fenêtres (Pièces, choix à trois, envoi Youtrust) passent par un PORTAIL vers le body",
    /return createPortal\(/.test(fen) && /window\.document\.body,/.test(fen)
      && /return createPortal\(/.test(envoi) && /window\.document\.body,/.test(envoi)
      && /return createPortal\(/.test(choix) && /window\.document\.body,/.test(choix), choix.slice(0, 80));
}

// 5. LES DEUX PATCHS.
const sql = (f) => fs.readFileSync(path.resolve(__dirname, "..", "..", "supabase", f), "utf8");
const coffre = sql("patch_a2_p8_4_preuves_coffre_2026-11-06.sql");
const otp = sql("patch_a2_p8_4_code_usage_unique_2026-11-06.sql");
controle("5. coffre : la règle GARDE ses deux branches et en ajoute une",
  /\(d\.storage_path = objects\.name\)/.test(coffre) && /'uploads'::text/.test(coffre) && /OR public\.app_console_dossier_document_lisible\(name\)/.test(coffre));
controle("5. coffre : la fonction vérifie l'uuid AVANT de convertir, et le numéro d'annonce du chemin",
  coffre.indexOf("f[4] !~ '^[0-9a-f]{8}-") < coffre.indexOf("d.id = f[4]::uuid") && /d\.hektor_annonce_id = f\[2\]/.test(coffre) && /d\.storage_status = 'cloud_available'/.test(coffre));
controle("5. coffre : fermée à public ET anon, ouverte à authenticated", /revoke all on function public\.app_console_dossier_document_lisible\(text\) from public, anon;/.test(coffre));
const colonnes = ["id", "provider", "provider_request_id", "sandbox", "app_console_document_id", "app_dossier_id", "hektor_annonce_id", "document_kind", "status", "signers", "external_id", "expiration_at", "activated_at", "done_at", "canceled_at", "expired_at", "signed_storage_path", "proofs", "last_event_at", "last_synced_at", "erreur", "requested_by", "created_at", "updated_at"];
const accordees = ((otp.match(/grant select \(([\s\S]*?)\)\s*on public\.app_signature_request to authenticated/) || [])[1] || "").split(",").map((c) => c.trim());
controle("5. code : authenticated garde les 23 colonnes, TOUTES sauf proofs (relevé du 06/11 : 24 colonnes)",
  accordees.length === 23 && colonnes.filter((c) => c !== "proofs").every((c) => accordees.includes(c)) && !accordees.includes("proofs"), J(accordees));
controle("5. code : la lecture du suivi (api.ts) ne demande que des colonnes accordées",
  (((api.match(/\.from\('app_signature_request'\)\s*\n\s*\.select\('([^']+)'\)/) || [])[1] || "").split(",").every((c) => accordees.includes(c))));
controle("5. code : sauvegarde datée AVANT le masquage, fermée à l'API",
  otp.indexOf("create table public.app_signature_request_avant_masquage_otp_20261106") < otp.indexOf("update public.app_signature_request")
  && /revoke all on public\.app_signature_request_avant_masquage_otp_20261106 from public, anon, authenticated/.test(otp));
const worker = fs.readFileSync(path.resolve(__dirname, "..", "..", "Console", "console_job_worker.js"), "utf8");
controle("5. worker : la piste JSON passe par masquerCodesUsageUnique AVANT d'être rangée",
  /const audit = masquerCodesUsageUnique\(await client\.lireAuditTrail\(/.test(worker));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
