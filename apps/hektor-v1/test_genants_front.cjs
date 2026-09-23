#!/usr/bin/env node
"use strict";
/**
 * G-1 a G-7 — CONTROLE DU FRONT : les deux numeros, la ou il le faut.
 *                                                            23/09/2026
 *
 * CE QU'ON EPROUVE, et la nuance qui compte : le front interroge un contact par
 * son numero a CINQ endroits, mais trois seulement recoivent un numero venu de
 * l'EXTERIEUR. Les deux autres le tiennent d'un contact deja charge : elles sont
 * coherentes par construction, et elargir leur filtre n'ajouterait que du risque.
 * Ce fichier verifie les deux choses -- ce qui doit changer ET ce qui ne doit pas.
 *
 * ⚠ CHAQUE CONTROLE EST REJOUE SUR LA VERSION D'AVANT (git show HEAD). Il doit y
 *   ECHOUER. Un controle qu'on n'a pas vu echouer sur le defaut n'est pas un
 *   controle -- lecon de trois assertions fausses ecrites cette semaine.
 *
 * NE LANCE NI SERVEUR NI REQUETE. Lecture de fichiers.
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const RACINE = path.resolve(__dirname, "..", "..");
const API = "apps/hektor-v1/src/lib/api.ts";
const APP = "apps/hektor-v1/src/App.tsx";

const lire = (rel) => fs.readFileSync(path.join(RACINE, rel), "utf8");

function versionDavant(rel) {
  try {
    // maxBuffer : App.tsx depasse le megaoctet par defaut. Sans ce reglage,
    // la lecture echouait en silence et la preuve etait « non faite » --
    // pendant que la derniere ligne affirmait le contraire.
    return execFileSync("git", ["show", `HEAD:${rel}`],
      { cwd: RACINE, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  } catch (_) { return null; }
}

const controles = [
  {
    nom: "G-6 la porte unique retrouve par les DEUX numeros",
    fichier: API,
    ok: (s) => /\.or\(`hektor_contact_id\.eq\.\$\{cleanId\},hektor_target_id\.eq\.\$\{cleanId\}`\)/.test(s),
  },
  {
    nom: "G-2 les DEUX barres de recherche numeriques acceptent la cible",
    fichier: API,
    // Deux, pas une : l'ecran Contacts ET la recherche d'un mandant a rattacher.
    // C'est une assertion qui a REVELE la seconde -- elle exigeait 1, il y en avait 2.
    ok: (s) => (s.match(/hektor_contact_id\.eq\.\$\{search\},hektor_target_id\.eq\.\$\{search\}/g) || []).length === 2,
  },
  {
    nom: "G-3 la repartition de commission retrouve son negociateur",
    fichier: API,
    ok: (s) => /\.or\(`hektor_contact_id\.eq\.\$\{cle\},hektor_target_id\.eq\.\$\{cle\}`\)/.test(s),
  },
  {
    nom: "G-7 l'option de mandant expose la cible",
    fichier: API,
    ok: (s) => /export type MandantContactSearchOption[\s\S]{0,400}'hektor_target_id'/.test(s),
  },
  {
    nom: "G-1 les invites d'un RDV se reconcilient sur une seule personne",
    fichier: APP,
    ok: (s) => /const identiteParCible = new Map<string, string>\(\)/.test(s)
            && /identiteParCible\.get\(brut\) \?\? brut/.test(s),
  },
  {
    nom: "G-4 un acquereur ne peut plus etre ajoute deux fois",
    fichier: APP,
    ok: (s) => /function numerosDuContact\(/.test(s)
            && /liste\.some\(\(x\) => numerosDuContact\(x\)\.some\(\(n\) => candidat\.has\(n\)\)\)/.test(s),
  },
  {
    nom: "G-4 et le retrait enleve la PERSONNE, pas un seul de ses numeros",
    fichier: APP,
    ok: (s) => /!numerosDuContact\(x\)\.includes\(String\(id \?\? ''\)\.trim\(\)\)/.test(s),
  },
  {
    // LA MOITIE QUI NE DOIT PAS BOUGER. Ces deux fonctions recoivent le numero
    // d'un contact DEJA CHARGE : les deux cotes basculent ensemble. Elargir leur
    // filtre serait du bruit, et du risque.
    nom: "les fonctions coherentes par construction n'ont PAS ete elargies",
    fichier: API,
    ok: (s) => /loadContactRelations[\s\S]{0,400}\.eq\('hektor_contact_id', contactId\.trim\(\)\)/.test(s)
            && /loadContactSearches[\s\S]{0,400}\.eq\('hektor_contact_id', contactId\.trim\(\)\)/.test(s),
    pasDePreuve: true, // elle passe AUSSI sur la version d'avant, et c'est voulu
  },
];

let echecs = 0;
let preuvesManquantes = 0;
for (const c of controles) {
  const vert = c.ok(lire(c.fichier));
  if (!vert) echecs += 1;
  console.log(`${vert ? "  OK  " : "ECHEC "} ${c.nom}`);
  if (c.pasDePreuve) continue;
  const avant = versionDavant(c.fichier);
  if (avant == null) {
    // UNE PREUVE QU'ON N'A PAS PU FAIRE N'EST PAS UNE PREUVE. On la compte
    // comme manquante plutot que de laisser la derniere ligne affirmer que
    // tout a ete eprouve.
    preuvesManquantes += 1;
    console.log("        ⚠ version d'avant ILLISIBLE : ce controle n'a pas ete eprouve.");
    continue;
  }
  if (c.ok(avant)) {
    preuvesManquantes += 1;
    console.log("        ⚠ CE CONTROLE PASSE AUSSI SUR LA VERSION D'AVANT : il ne voit rien.");
  }
}

console.log();
if (echecs || preuvesManquantes) {
  if (echecs) console.log(`${echecs} controle(s) en ECHEC.`);
  if (preuvesManquantes) console.log(`${preuvesManquantes} controle(s) sans preuve : ils ne detectent pas le defaut.`);
  process.exit(1);
}
console.log(`${controles.length} controles passes, et chacun a ete vu ECHOUER sur la version d'avant.`);
