#!/usr/bin/env node
"use strict";
/**
 * A.2 P8-1 — QUEL DOCUMENT DIT OU EN EST LA SIGNATURE DU MANDAT (cockpit + Mandat V3).                      06/11/2026
 *
 * On EXÉCUTE le code réel (src/lib/etatSignatureMandat.ts, esbuild + vm) et on le confronte à L'ANCIENNE règle
 * (recopiée ici telle qu'elle était dans App.tsx : le premier document, procédure ou signé, sinon rien).
 * Données FICTIVES, calquées sur des cas mesurés (61398, les 40 biens « rien », les 21 « attente + signé »).
 * Puis on vérifie les branchements dans App.tsx (cockpit, textes, dépôt visible, éditeur).
 * NE LANCE NI SERVEUR NI REQUÊTE.     node apps/hektor-v1/test_etat_signature_mandat.cjs
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
let M;
try {
  const { outputFiles } = esbuild.buildSync({ entryPoints: [path.resolve(__dirname, "src", "lib", "etatSignatureMandat.ts")], bundle: true, write: false, format: "cjs", platform: "neutral" });
  const module = { exports: {} };
  vm.runInNewContext(outputFiles[0].text, { module, exports: module.exports });
  M = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }

// L'ANCIENNE règle, à l'identique (App.tsx avant P8-1).
const ancienne = (docs, match, exclude, remplace) => {
  const doc = docs.find((d) => {
    const name = `${d.document_name ?? ""} ${d.document_type ?? ""}`;
    if (exclude && exclude.test(name)) return false;
    if (remplace(d)) return false;
    return match.test(name);
  });
  const sig = doc && doc.metadata_json && doc.metadata_json.signature;
  if (!sig) return null;
  const hasProcedure = sig.procedure_id != null && String(sig.procedure_id).trim() !== "";
  if (!hasProcedure && sig.status !== "signed") return null;
  return sig.status ?? null;
};
const nouvelle = (docs) => { const e = M.etatSignatureDuMandat(docs, /mandat/i, /avenant/i, (d) => Boolean(d.metadata_json && d.metadata_json.remplace)); return e ? e.status : null; };
const vieux = (docs) => ancienne(docs, /mandat/i, /avenant/i, (d) => Boolean(d.metadata_json && d.metadata_json.remplace));

// Un modèle Hektor « Mandat (Avec saisie du numéro) » : état par défaut, sans procédure (ce que la liste met devant).
const modele = (n) => ({ id: `modele-${n}`, document_type: "document", document_name: "Mandat (Avec saisie du numéro) (Vente)", created_at: "2026-08-18T18:09:55Z", metadata_json: { signature: { status: "to_send", procedure_id: null, hektor_doc_id: String(n) } } });
const youtrust = (status, extra = {}) => ({ id: "yt", document_type: "Mandat", document_name: "Mandat de vente - 18420.pdf", created_at: "2026-11-05T19:43:00Z",
  metadata_json: { signataires_du_pdf: { valide: true }, signature: { provider: "youtrust", status, sent_at: "2026-11-05T19:59:10Z", ...extra } } });
const immosign = (status, quand, proc = 514) => ({ id: `im-${status}-${quand}`, document_type: "document", document_name: "Mandat (Avec saisie du numéro) (Vente)", created_at: "2026-06-01T10:00:00Z",
  metadata_json: { signature: { status, procedure_id: proc, ...(status === "signed" ? { signed_at: quand } : { sent_at: quand }) } } });

// 1. LE CAS DE 61398 (06/11) : 10 modèles Hektor devant, le Youtrust signé en dernier.
{
  const docs = [modele(21), modele(43), modele(826), youtrust("signed", { signed_at: "06/11/2026 à 07:09", signed_at_iso: "2026-11-06T06:09:07Z" })];
  controle("1. 61398 : l'ANCIENNE règle lit « rien » (le 1er modèle) -> « à éditer »", vieux(docs) === null, vieux(docs));
  controle("1. 61398 : la NOUVELLE lit « signé » (le mandat Youtrust)", nouvelle(docs) === "signed", nouvelle(docs));
}
// 2. Youtrust EN COURS (aucune procédure ImmoSign, R2) -> « en signature ».
{
  const docs = [modele(21), youtrust("pending", { progress: "2/3" })];
  controle("2. Youtrust en cours : ancienne « rien », nouvelle « en attente »", vieux(docs) === null && nouvelle(docs) === "pending", `${vieux(docs)} / ${nouvelle(docs)}`);
  const seul = [youtrust("pending")];
  controle("2. ...même seul dans la liste, l'ancienne l'ignorait (pas de procédure)", vieux(seul) === null && nouvelle(seul) === "pending");
}
// 3. Youtrust annulé / expiré -> le PDF est édité, à renvoyer.
controle("3. Youtrust annulé -> « à envoyer »", nouvelle([youtrust("cancelled", { cancelled_at_iso: "2026-11-06T08:00:00Z" })]) === "to_send");
controle("3. Youtrust expiré -> « à envoyer »", nouvelle([youtrust("expired", { expired_at_iso: "2027-05-05T21:59:59Z" })]) === "to_send");
// 4. Un PDF de l'éditeur pas encore parti, et le même après que la synchro y a posé l'état par défaut de Hektor (déposé).
{
  const neuf = { id: "ed", document_type: "Mandat", document_name: "Mandat de vente - 18420.pdf", created_at: "2026-11-06T09:00:00Z", metadata_json: { signataires_du_pdf: { valide: true } } };
  controle("4. PDF de l'éditeur, pas encore envoyé -> « à envoyer » (l'ancienne : rien)", nouvelle([modele(1), neuf]) === "to_send" && vieux([modele(1), neuf]) === null);
  const depose = { ...neuf, metadata_json: { ...neuf.metadata_json, signature: { status: "to_send", procedure_id: null, hektor_doc_id: "715300" } } };
  controle("4. ...déposé chez Hektor (état par défaut posé par la synchro) -> toujours « à envoyer »", nouvelle([depose]) === "to_send");
}
// 5. ATTENTE + SIGNÉ (21 biens) : le PLUS RÉCENT gagne, plus l'alphabet.
{
  const ancienSigne = immosign("signed", "16/06/2026 à 14:35");
  const nouvelleAttente = immosign("pending", "2026-10-20T08:00:00Z", 900);
  controle("5. un nouvel envoi APRÈS un signé -> « en attente »", nouvelle([ancienSigne, nouvelleAttente]) === "pending" && nouvelle([nouvelleAttente, ancienSigne]) === "pending");
  const vieilleAttente = immosign("pending", "2026-05-02T08:00:00Z", 100);
  controle("5. une vieille attente AVANT le signé -> « signé », quel que soit l'ordre de la liste", nouvelle([vieilleAttente, ancienSigne]) === "signed" && nouvelle([ancienSigne, vieilleAttente]) === "signed");
  controle("5. TÉMOIN : l'ancienne dépendait de l'ordre", vieux([vieilleAttente, ancienSigne]) === "pending" && vieux([ancienSigne, vieilleAttente]) === "signed");
  // ⚠ LE PIÈGE DU REJEU (06/11) : 62806 -- procédure 809 « en attente », VUE le 15/10, et procédure 843 signée le 06/10.
  //   La date « vue le » est postérieure, mais le NUMÉRO dit que l'attente est la plus ancienne (abandonnée).
  const attentePerimee = immosign("pending", "2026-10-15T09:11:22Z", 809);
  const signe843 = immosign("signed", "06/10/2026 à 09:51", 843);
  controle("5. ⭐ 62806 : une attente de NUMÉRO inférieur au signé est périmée -> « signé » (pas « en attente »)",
    nouvelle([attentePerimee, signe843]) === "signed" && nouvelle([signe843, attentePerimee]) === "signed", nouvelle([attentePerimee, signe843]));
  // 63443 : procédure 958 en attente, numéro SUPÉRIEUR au signé 951 -> c'est bien un nouvel envoi, même vu « avant ».
  const signe951 = immosign("signed", "04/11/2026 à 14:04", 951);
  const attente958VueTot = immosign("pending", "2026-11-01T00:00:00Z", 958);
  controle("5. un numéro SUPÉRIEUR au signé est un nouvel envoi -> « en attente », même si sa date « vue le » est plus ancienne",
    nouvelle([signe951, attente958VueTot]) === "pending", nouvelle([signe951, attente958VueTot]));
}
// 6. TÉMOINS : là où l'ancienne avait raison, la nouvelle dit LA MÊME CHOSE.
{
  const casIdentiques = [
    [], [modele(1)], [modele(1), modele(2)],                                  // rien de fiable -> null
    [immosign("pending", "2026-10-01T08:00:00Z")], [immosign("signed", "08/04/2026 à 15:53")],   // un seul état fiable
    [immosign("signed", "08/04/2026 à 15:53"), modele(1)],                    // le fiable est premier
    [{ id: "m", document_name: "Mandat signé à la main", created_at: "2026-09-01T00:00:00Z", metadata_json: { signature: { status: "signed", source: "manuscrite", signed_at: "2026-09-01" } } }],
    [{ ...immosign("signed", "08/04/2026 à 15:53"), metadata_json: { ...immosign("signed", "08/04/2026 à 15:53").metadata_json, remplace: { le: "2026-11-01" } } }],   // remplacé : ignoré par les deux
  ];
  const ecarts = casIdentiques.filter((docs) => vieux(docs) !== nouvelle(docs));
  controle(`6. TÉMOIN : ${casIdentiques.length} cas où l'ancienne avait raison -> MÊME réponse`, ecarts.length === 0, JSON.stringify(ecarts.map((d) => [vieux(d), nouvelle(d)])));
  const avenant = { id: "av", document_name: "Avenant au mandat - 18420.pdf", document_type: "Mandat", created_at: "2026-11-06T00:00:00Z", metadata_json: { signature: { provider: "youtrust", status: "signed", signed_at_iso: "2026-11-06T09:00:00Z" } } };
  controle("6. l'avenant reste hors du mandat (exclu), et l'avenant se lit à part", nouvelle([modele(1), avenant]) === null
    && (M.etatSignatureDuMandat([avenant], /avenant/i, undefined, () => false) || {}).status === "signed");
}
// 7. Les dates, telles qu'elles sont écrites en base.
controle("7. « 06/11/2026 à 07:09 » (forme ImmoSign) est lue", M.dateDeSignature("06/11/2026 à 07:09") === Date.UTC(2026, 10, 6, 7, 9));
controle("7. « 2026-09-01 » (à la main) et l'ISO sont lus ; un texte vide ne l'est pas", Number.isFinite(M.dateDeSignature("2026-09-01")) && Number.isFinite(M.dateDeSignature("2026-11-05T19:59:10Z")) && !Number.isFinite(M.dateDeSignature("")));
controle("7. le fournisseur est rendu (les textes du cockpit en dépendent)", M.etatSignatureDuMandat([youtrust("pending")], /mandat/i, /avenant/i, () => false).fournisseur === "youtrust"
  && M.etatSignatureDuMandat([immosign("pending", "2026-10-01T08:00:00Z")], /mandat/i, /avenant/i, () => false).fournisseur === "immosign");

// 8. LES BRANCHEMENTS dans App.tsx.
const app = fs.readFileSync(path.resolve(__dirname, "src", "App.tsx"), "utf8");
controle("8. le cockpit lit la nouvelle règle", /const ckSigStatus = [\s\S]{0,400}etatSignatureDuMandat\(ckDocs, match, exclude,/.test(app));
controle("8. plus de « (ImmoSign) » en dur dans le cran « édité »", !/envoyez-le à la signature \(ImmoSign\)/.test(app));
controle("8. les textes « envoyé / signé » suivent le fournisseur", /\{mandatEnvoyeSur\} — vos mandants doivent signer/.test(app) && /<b>\{mandatSigneSur\}<\/b>/.test(app));
controle("8. G5 : la liste v21 montre l'état du dépôt chez Hektor", /mentionDepotHektor\(e\.doc\)/.test(app) && /dépôt chez Hektor a échoué, il sera repris à 12:30/.test(app));
controle("8. G6 : l'éditeur relit `mandat_nait_chez_nous` au clic et attend le dépôt confirmé avant la signature Hektor",
  /chezNousGen = await loadAppSettingActive\('mandat_nait_chez_nous'\)/.test(app) && /chezNousGen && fresh\.envoi_hektor_statut !== 'envoye'/.test(app));

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
