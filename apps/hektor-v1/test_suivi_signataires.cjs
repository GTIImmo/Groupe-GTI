#!/usr/bin/env node
"use strict";
/**
 * A.2 P8-3 — LE SUIVI PAR SIGNATAIRE (Youtrust) : qui a signé, qui attend, Relancer / Annuler.            06/11/2026
 * On EXÉCUTE le code réel (src/lib/suiviSignataires.ts, esbuild + vm), puis on vérifie les branchements : App.tsx,
 * api.ts, et que les clés posées sont CELLES QUE LE WORKER LIT (Console/console_job_worker.js).
 * Données FICTIVES. NE LANCE NI SERVEUR NI REQUÊTE.     node apps/hektor-v1/test_suivi_signataires.cjs
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
let S;
try {
  const { outputFiles } = esbuild.buildSync({ entryPoints: [path.resolve(__dirname, "src", "lib", "suiviSignataires.ts")], bundle: true, write: false, format: "cjs", platform: "neutral" });
  const module = { exports: {} };
  vm.runInNewContext(outputFiles[0].text, { module, exports: module.exports });
  S = module.exports;
} catch (e) { console.log(`⛔ ${e.message}`); process.exit(2); }
const J = (v) => JSON.stringify(v);

// Une demande à trois : deux mandants (ordre libre), le négociateur en dernier (D7).
const demande = (status, statuts, extra = {}) => ({
  id: "r1", status, expiration_at: "2026-12-06T10:00:00Z",
  signers: [
    { index: 2, role: "mandataire", prenom: "Frédéric", nom: "GERPHAGNON", email: "f@x", status: statuts[2], provider_signer_id: "s3" },
    { index: 0, role: "mandant", prenom: "Jean", nom: "DUPONT", email: "j@x", status: statuts[0], provider_signer_id: "s1", signed_at: statuts[0] === "signed" ? "2026-11-06T06:05:00Z" : null },
    { index: 1, role: "mandant", prenom: "Delphine", nom: "DUPONT", email: "d@x", status: statuts[1], provider_signer_id: "s2" },
  ],
  ...extra,
});

// 1. L'ordre, les noms, les rôles, l'heure de Paris.
{
  const s = S.suiviDeLaDemande(demande("ongoing", ["signed", "notified", "initiated"]));
  controle("1. dans l'ordre des cases (index), pas dans l'ordre de la table", J(s.lignes.map((l) => l.nom)) === J(["Jean DUPONT", "Delphine DUPONT", "Frédéric GERPHAGNON"]), J(s.lignes.map((l) => l.nom)));
  controle("1. le rôle en clair (Mandant / Mandataire)", s.lignes[0].role === "Mandant" && /Mandataire/.test(s.lignes[2].role));
  controle("1. « A signé le 06/11/2026 à 07:05 » — l'heure de PARIS (06:05 Z + 1 h en novembre)", s.lignes[0].libelle === "A signé le 06/11/2026 à 07:05", s.lignes[0].libelle);
  controle("1. le résumé « 1 signature sur 3 » et l'expiration", /^1 signature sur 3 — le lien expire le 06\/12\/2026/.test(s.resume), s.resume);
}
// 2. ⭐ RELANCER : seulement `notified` dans une demande `ongoing` (la règle de Youtrust — un refus = une alerte).
{
  const s = S.suiviDeLaDemande(demande("ongoing", ["signed", "notified", "initiated"]));
  controle("2. le mandant invité (notified) est relançable", s.lignes[1].relancable === true && /Invité par e-mail/.test(s.lignes[1].libelle));
  controle("2. TÉMOIN : celui qui a signé ne l'est pas", s.lignes[0].relancable === false);
  controle("2. TÉMOIN : le négociateur dont ce n'est pas le tour (initiated) ne l'est pas, « Pas encore son tour »", s.lignes[2].relancable === false && s.lignes[2].libelle === "Pas encore son tour");
  const v = S.suiviDeLaDemande(demande("ongoing", ["signed", "consent_given", "initiated"]));
  controle("2. TÉMOIN : en train de signer (consent_given) -> pas de relance", v.lignes[1].relancable === false && v.lignes[1].libelle === "En train de signer");
  const fin = S.suiviDeLaDemande(demande("canceled", ["signed", "notified", "initiated"]));
  controle("2. TÉMOIN : demande annulée -> personne n'est relançable, « N'a pas signé »", fin.lignes.every((l) => !l.relancable) && fin.lignes[1].libelle === "N’a pas signé");
  const sansId = S.suiviDeLaDemande({ id: "r", status: "ongoing", signers: [{ index: 0, role: "mandant", nom: "X", status: "notified" }] });
  controle("2. TÉMOIN : un signataire sans numéro Youtrust n'est pas relançable (le worker l'exige)", sansId.lignes[0].relancable === false);
}
// 3. ANNULER : une demande en cours seulement.
{
  controle("3. ongoing -> annulable", S.suiviDeLaDemande(demande("ongoing", ["notified", "notified", "initiated"])).annulable === true);
  controle("3. approval -> annulable", S.suiviDeLaDemande(demande("approval", ["initiated", "initiated", "initiated"])).annulable === true);
  for (const st of ["done", "canceled", "expired", "declined"]) {
    controle(`3. TÉMOIN : ${st} -> PAS annulable`, S.suiviDeLaDemande(demande(st, ["signed", "signed", "signed"])).annulable === false);
  }
}
// 4. Les fins de demande.
{
  const d = S.suiviDeLaDemande(demande("done", ["signed", "signed", "signed"], { done_at: "2026-11-06T06:09:00Z" }));
  controle("4. done : « Signé par tous — le 06/11/2026 à 07:09 »", d.resume === "Signé par tous — le 06/11/2026 à 07:09" && d.signes === 3, d.resume);
  const e = S.suiviDeLaDemande(demande("expired", ["signed", "notified", "initiated"], { expired_at: "2026-12-06T10:00:00Z" }));
  controle("4. expired : « Signature expirée … — à renvoyer »", /^Signature expirée le 06\/12\/2026 à 11:00 — à renvoyer$/.test(e.resume), e.resume);
  const r = S.suiviDeLaDemande(demande("declined", ["declined", "notified", "initiated"]));
  controle("4. un refus se voit en rouge, « A refusé de signer »", r.lignes[0].ton === "refus" && r.lignes[0].libelle === "A refusé de signer");
  controle("4. demande introuvable (null) : rien ne casse", S.suiviDeLaDemande(null).lignes.length === 0 && S.suiviDeLaDemande(null).annulable === false);
}

// 5. LES BRANCHEMENTS.
const src = (f) => fs.readFileSync(path.resolve(__dirname, "src", f), "utf8");
const app = src("App.tsx");
const api = src(path.join("lib", "api.ts"));
const comp = src("SuiviSignatairesYoutrust.tsx");
const worker = fs.readFileSync(path.resolve(__dirname, "..", "..", "Console", "console_job_worker.js"), "utf8");
controle("5. le suivi est monté aux TROIS endroits (liste v21, liste classique, suivi du mandat)", (app.match(/<SuiviSignatairesYoutrust document=/g) || []).length === 3);
controle("5. gestes = interrupteur Youtrust (le worker les refuse sinon)", (app.match(/gestesActifs=\{signatureYoutrust\}/g) || []).length === 2 && /gestesActifs=\{choixSignature\.youtrust\}/.test(app)
  && /exigerInterrupteurYoutrust\(\);\s*\n\s*const payload = safeJsonParse\(job\.payload_json\)/.test(worker));
controle("5. Youtrust SEULEMENT : le composant exige provider youtrust + signature_request_id (ImmoSign inchangé)",
  /sig && sig\.provider === 'youtrust' && sig\.signature_request_id \? sig : null/.test(comp) && /if \(!id\) return null/.test(comp));
controle("5. ⛔ la lecture ne prend JAMAIS `proofs` (le code à usage unique y est)",
  /\.from\('app_signature_request'\)\s*\n\s*\.select\('id,status,signers,expiration_at,done_at,canceled_at,expired_at,last_synced_at'\)/.test(api));
controle("5. les clés posées sont celles que le WORKER lit (signature_request_id, provider_signer_id)",
  /signature_request_id: input\.signatureRequestId/.test(api) && /provider_signer_id: input\.providerSignerId/.test(api)
  && /cleanString\(payload\.signature_request_id\)/.test(worker) && /const signerId = cleanString\(payload\.provider_signer_id\)/.test(worker));
controle("5. chaque geste demande une confirmation, la relance NOMME la personne", /Renvoyer le lien de signature à \$\{nom\}/.test(comp) && /Annuler la signature électronique en cours \?/.test(comp));
const choix = src(path.join("lib", "choixSignature.ts"));
controle("5. le message « annulez-la d'abord » (Youtrust) dit OÙ annuler", (choix.match(/« Annuler la signature », sous la liste des signataires/g) || []).length === 2);

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
