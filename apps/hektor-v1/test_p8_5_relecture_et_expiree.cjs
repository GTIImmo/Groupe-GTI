#!/usr/bin/env node
"use strict";
/**
 * A.2 P8-5 — APRÈS UN ENVOI DEPUIS L'ÉDITEUR, L'ÉCRAN SE RELIT ; ET « EXPIRÉE » SE DIT.                   06/11/2026
 * Contrôles sur le code tel qu'il est (App.tsx, EnvoiSignatureYoutrust.tsx, le worker) et TÉMOIN contre HEAD~ (git) :
 * le code d'avant n'avait ni onSent dans l'éditeur, ni pastille « expirée ».
 * NE LANCE NI SERVEUR NI REQUÊTE.     node apps/hektor-v1/test_p8_5_relecture_et_expiree.cjs
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
};
const racine = path.resolve(__dirname, "..", "..");
const sansCR = (s) => s.split(String.fromCharCode(13)).join("");   // le disque est en CRLF (autocrlf), git en LF
const app = sansCR(fs.readFileSync(path.resolve(__dirname, "src", "App.tsx"), "utf8"));
const envoi = sansCR(fs.readFileSync(path.resolve(__dirname, "src", "EnvoiSignatureYoutrust.tsx"), "utf8"));
const worker = sansCR(fs.readFileSync(path.join(racine, "Console", "console_job_worker.js"), "utf8"));
let avant = "";
try {
  const introduit = execFileSync("git", ["log", "--format=%H", "-S", "function relireQuandLeTravailFinit(", "--", "apps/hektor-v1/src/App.tsx"], { cwd: racine, encoding: "utf8" }).trim().split("\n").filter(Boolean).pop();
  avant = execFileSync("git", ["show", `${introduit ? `${introduit}~1` : "HEAD"}:apps/hektor-v1/src/App.tsx`], { cwd: racine, encoding: "utf8", maxBuffer: 256 * 1024 * 1024 });
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }

const ontLeCorrectif = (src) => ({
  onSentEditeur: /onSent=\{\(job\) => relireQuandLeTravailFinit\(job\)\}/.test(src),
  pastille: /expired: \{ bg: '#fbefd8', fg: '#b06a05', icon: 'x', label: `Signature expirée/.test(src),
  v21: /st === 'expired' \? `Signature expirée/.test(src) && /st === 'expired' \? 'Expirée'/.test(src),
});

// 1. L'éditeur relit l'écran à la FIN du travail d'envoi.
{
  const c = ontLeCorrectif(app);
  controle("1. l'éditeur passe onSent à la fenêtre d'envoi", c.onSentEditeur);
  controle("1. la fenêtre appelle onSent avec le travail créé", /const job = await createYoutrustSendSignatureJob\(/.test(envoi) && /props\.onSent\?\.\(job\)/.test(envoi));
  const corps = (app.match(/function relireQuandLeTravailFinit\([\s\S]*?\n}\n/) || [""])[0];
  controle("1. on attend la FIN du travail (relu par numéro, toutes les 3 s), puis on relit l'app (signalerGeste)",
    /loadConsoleJobsByIds\(\[String\(job\.id\)\]\)/.test(corps) && /if \(lu && !isConsoleJobActive\(lu\)\) \{ signalerGeste\(\); return \}/.test(corps) && /setTimeout\(verifier, 3000\)/.test(corps), corps.slice(0, 200));
  controle("1. borné : 2 min au plus, rien en maquette (mock)", /delaiMaxMs = 120000/.test(corps) && /import\.meta\.env\.MODE === 'mock'/.test(corps));
  controle("1. la relecture de l'app est RELAYÉE à la liste Documents et au suivi du mandat (déjà en place)",
    /window\.dispatchEvent\(new CustomEvent\(EVENEMENT_RELIRE_RUBRIQUES\)\)/.test(app) && (app.match(/const relecture = useRelectureRubriques\(\)/g) || []).length >= 2);
}
// 2. « Expirée ».
{
  const c = ontLeCorrectif(app);
  controle("2. la pastille (liste classique, suivi du mandat) dit « Signature expirée le … — à renvoyer »", c.pastille);
  controle("2. la présentation v21 le dit aussi, et sa pastille dit « Expirée »", c.v21);
  controle("2. le worker écrit bien expired_at au format affiché (jj/mm/aaaa à hh:mm)", /langue === "expired" \? \{ expired_at: dateFaconImmoSign\(expiredAt\)/.test(worker));
  controle("2. un document expiré se renvoie : le bouton « Signature » ne l'écarte pas (seul « signé » l'écarte)",
    /\{choixSignature\.actif \? \(signature\?\.status !== 'signed' && !documentRemplace\(document\) \? \(/.test(app));
}
// 3. TÉMOIN : le code d'avant n'avait rien de tout ça.
{
  const c = ontLeCorrectif(avant);
  controle("3. TÉMOIN : avant, ni onSent dans l'éditeur, ni pastille, ni libellé v21", !c.onSentEditeur && !c.pastille && !c.v21, JSON.stringify(c));
}

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
