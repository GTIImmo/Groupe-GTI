#!/usr/bin/env node
"use strict";
/**
 * A.2 (06/11/2026) -- LE CODE PAR E-MAIL CHOISI A L'ENVOI, meme quand le signataire a un portable (Frederic).
 * La regle par defaut reste (portable -> SMS, sinon e-mail). Controles sur la fenetre d'envoi (EnvoiSignatureYoutrust.tsx)
 * et api.ts, et TEMOIN contre HEAD. Le comportement reel a ete vu sur la planche : demande sortie
 * {"corrections":[{"rang":1,"code":"email"}],"codeMandataire":"email"}, aucune ecriture de fiche.
 * Le worker a son propre essai : Console/test_envoi_lit_la_photo.js (bloc 6).
 * NE LANCE NI SERVEUR NI REQUETE.     node apps/hektor-v1/test_code_par_email.cjs
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
};
const sansCR = (s) => s.split(String.fromCharCode(13)).join("");
const racine = path.resolve(__dirname, "..", "..");
const lire = (f) => sansCR(fs.readFileSync(path.resolve(__dirname, "src", f), "utf8"));
// La version d'AVANT le choix : le commit qui l'introduit, moins un (HEAD tant qu'il n'est pas commite).
const lireHead = (f) => {
  try {
    const introduit = execFileSync("git", ["log", "--format=%H", "-S", "Envoyer le code par e-mail", "--", `apps/hektor-v1/src/${f}`], { cwd: racine, encoding: "utf8" }).trim().split("\n").filter(Boolean).pop();
    return sansCR(execFileSync("git", ["show", `${introduit ? `${introduit}~1` : "HEAD"}:apps/hektor-v1/src/${f}`], { cwd: racine, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }));
  } catch { return null; }
};
const envoi = lire("EnvoiSignatureYoutrust.tsx");
const api = lire(path.join("lib", "api.ts"));

const corpsEnvoyer = envoi.slice(envoi.indexOf("const envoyer = async () => {"), envoi.indexOf("const casesTotal"));
const ficheFin = corpsEnvoyer.indexOf("// A.2 (06/11/2026) : le code par e-mail choisi");
const ficheDebut = corpsEnvoyer.indexOf("for (const c of corrections) {");

controle("1. par defaut la regle reste : portable valide -> « Code par SMS au … », sinon « Code par e-mail »",
  envoi.includes("{portableValide(tel)") && envoi.includes("<span>Code par SMS au {masquer(tel)}</span>") && envoi.includes(": 'Code par e-mail'}"));
controle("1. le lien « Envoyer le code par e-mail » n'est offert que si un portable valide existe, avec « Revenir au SMS »",
  envoi.includes("Envoyer le code par e-mail</button>") && envoi.includes("Revenir au SMS</button>"));
controle("1. le negociateur a le meme choix (« Toujours par e-mail » / « Revenir a la regle »)",
  envoi.includes("Toujours par e-mail</button>") && envoi.includes("Revenir à la règle</button>"));
controle("2. ⛔ le choix s'ajoute APRES l'enregistrement sur la fiche : un choix de code n'ecrit jamais la fiche (D33)",
  ficheDebut >= 0 && ficheFin > ficheDebut && corpsEnvoyer.indexOf("c.code = 'email'") > ficheFin, `${ficheDebut} / ${ficheFin}`);
controle("2. il n'est pose que la ou un portable valide existe",
  corpsEnvoyer.includes("if (!parEmail.has(m.rang) || !portableValide(valeur(m.rang, 'telephone'))) continue"));
controle("3. la demande porte code: 'email' par rang, et code_mandataire pour le negociateur (cles que lit le worker)",
  api.includes("code?: 'email' }") && api.includes("...(input.codeMandataire === 'email' ? { code_mandataire: 'email' } : {}),")
    && corpsEnvoyer.includes("...(negoParEmail ? { codeMandataire: 'email' as const } : {}),"));
const worker = sansCR(fs.readFileSync(path.join(racine, "Console", "console_job_worker.js"), "utf8"));
controle("3. le worker lit ces memes cles (c.code, payload.code_mandataire)",
  worker.includes('codeParEmail: c.code === "email",') && worker.includes('if (payload.code_mandataire === "email") mandataireBrut.codeParEmail = true;'));

const head = lireHead("EnvoiSignatureYoutrust.tsx");
controle("4. TEMOIN : la fenetre d'avant (HEAD) n'offrait pas ce choix", head !== null && !head.includes("Envoyer le code par e-mail"), head === null ? "HEAD illisible" : "");

console.log(echecs.length ? `\n${echecs.length} contrôle(s) en échec` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
