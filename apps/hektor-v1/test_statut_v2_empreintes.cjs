#!/usr/bin/env node
"use strict";
/**
 * 05/11/2026 — REFONTE VISUELLE DE LA MODALE « CHANGER LE STATUT », LOT 0 : « RIEN N'A CHANGÉ DERRIÈRE ».
 * Plan : notice/PLAN_REFONTE_VISUELLE_MODALE_STATUT_2026-11-05.md §0 et §4 · inventaire :
 * notice/INVENTAIRE_PARITE_MODALE_STATUT_2026-11-05.md.
 *
 * Ce script prend l'EMPREINTE (sha1) de tout ce qui agit derrière la modale :
 *   · les fonctions du §0 du plan (gestes, gardes, reprise, aides), dans App.tsx et lib/api.ts ;
 *   · les effets de préremplissage et d'héritage (un useEffect qui écrit dans l'état de la modale) ;
 *   · l'ANCIEN BLOC de la modale, entier — interrupteur éteint, il doit rester octet pour octet ;
 * et l'INVENTAIRE de ce que l'ancien bloc utilise (setters, gestes, fonctions, états lus, composants,
 * boutons, conditions d'affichage), pour le contrôle de parité des lots suivants.
 *
 * Chaque empreinte est prise deux fois : sur le texte exact, et sur le texte SANS commentaires ni
 * espaces. Un écart sur la première seule = « commentaire seulement » (à relire, pas une alerte).
 *
 * ⚠ TEMOIN INVERSE, joué à chaque contrôle sur une copie EN MÉMOIRE du source :
 *   1. une instruction ajoutée dans handleGesteHektor → UN écart, sur elle seule, « code » ;
 *   2. une ligne ajoutée hors de tout morceau suivi   → ZÉRO écart (les découpes ne débordent pas) ;
 *   3. un commentaire changé dans affaireEstVivante   → UN écart, « commentaire seulement » ;
 *   4. un caractère changé dans l'ancien bloc         → le bloc est signalé.
 *
 * NE LANCE NI SERVEUR NI REQUÊTE. N'écrit que la référence, et seulement avec --poser.
 *     node apps/hektor-v1/test_statut_v2_empreintes.cjs            contrôle contre la référence
 *     node apps/hektor-v1/test_statut_v2_empreintes.cjs --poser    (re)pose la référence
 *     sortie 0 = tout vert · 1 = un écart · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const RACINE = __dirname;
const SOURCES = { app: path.join(RACINE, "src", "App.tsx"), api: path.join(RACINE, "src", "lib", "api.ts") };
const REFERENCE = path.join(RACINE, "statut_v2_reference.json");
const V2 = path.join(RACINE, "src", "ModaleStatutV2.tsx");

// ── ce qui ne doit pas bouger (plan §0), par fichier ──
const FONCTIONS = {
  app: [
    // les gestes et leur cycle
    "handleChangeHektorAnnonceStatus", "handleGesteHektor", "openStatusChangeModal", "closeStatusChangeModal",
    "relireApresLeGeste", "rememberHektorActionJob",
    // la reprise et les gardes
    "affaireCourantePourStatut", "affairesVivantesPourStatut", "gardeFouPourStatut", "etatFermeAuxTransactions",
    "bienEngage", "offreVerrouilleeParSonDossier", "compromisVerrouilleParSaVente", "gesteOffreSansEffet",
    "modifierChezHektorPossible", "nouvelleOffreFermeeSurBienEngage", "avisGardeFouSaisie", "offreEcarteeSurBienEngage",
    "offreAccepteeFigeeChezHektor", "dossiersOuvertsDuBien", "affaireEstVivante", "avisPlusieursAffaires",
    "gestesEcartCarnet", "offreARegulariser", "compromisDeLaRegularisation", "rattachementOffreProposee",
    "dateOffreFaite", "statusChangeNeedsTransaction", "statusChangeNeedsSalePrice", "hektorClosureRaisonsFor",
    "hektorStatusTargetLabel",
    // les aides de saisie que le bloc appelle
    "toucherStatusChange", "apresSaisieCommission", "rechargerPersonnesEcarts", "ajouterAcquereurStatut",
    "retirerAcquereurStatut", "ajouterCondition", "retirerCondition", "modifierCondition", "repartitionPoser",
    "repartitionAjouterCase", "repartitionRetirerCase",
  ],
  api: [
    "createChangeHektorAnnonceStatusJob", "gesteAffaireOptimistic", "setMandatClotureApp", "saveRepartition",
    "ecrireAffaireCommission", "trancherAffaireCarnetEcart", "fermerAffairePersonneEcart",
  ],
};
// un effet est suivi s'il lit l'état de la modale ET écrit dans un de ces états
const EFFET_LIT = /statusChange[A-Z]/;
const EFFET_ECRIT = /\bset(StatusChange|Carnet|Personnes|Repartition)[A-Za-z]*\(/;

const sha1 = (t) => crypto.createHash("sha1").update(t).digest("hex").slice(0, 16);
function sansCommentaires(t) {
  return t.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\{\s*\}/g, "{}")
    .split("\n").map((l) => l.replace(/(^|\s)\/\/.*$/, "")).join("\n").replace(/\s+/g, " ").trim();
}
const empreintes = (t) => ({ exacte: sha1(t), code: sha1(sansCommentaires(t)) });

// la fin d'un morceau : « } » à la même marge, ou « }, [deps]) » d'un hook (deps sur plusieurs lignes)
function finDuMorceau(lignes, debut, marge) {
  for (let j = debut + 1; j < lignes.length; j++) {
    const l = lignes[j];
    if (!l.startsWith(marge + "}")) continue;
    const reste = l.slice(marge.length);
    if (/^\}\s*$/.test(reste) || /^\}\)\s*;?\s*$/.test(reste)) return j;
    if (/^\},\s*\[/.test(reste)) {
      let k = j;
      while (k < lignes.length && !/\]\)\s*;?\s*$/.test(lignes[k])) k++;
      return k;
    }
  }
  return -1;
}

function decouperFonction(lignes, nom) {
  const re = new RegExp(`^(\\s*)(?:export\\s+)?(?:async\\s+)?(?:function\\s+${nom}\\b|(?:const|let)\\s+${nom}\\b)`);
  const debuts = [];
  lignes.forEach((l, i) => { const m = l.match(re); if (m) debuts.push([i, m[1]]); });
  if (debuts.length !== 1) return { erreur: `${nom} : ${debuts.length} définition(s) trouvée(s), il en faut une` };
  const [i, marge] = debuts[0];
  const j = finDuMorceau(lignes, i, marge);
  if (j < 0) return { erreur: `${nom} : fin introuvable` };
  return { debut: i, fin: j, texte: lignes.slice(i, j + 1).join("\n") };
}

function decouperEffets(lignes) {
  const effets = [];
  const vus = {};
  for (let i = 0; i < lignes.length; i++) {
    const m = lignes[i].match(/^(\s*)useEffect\(/);
    if (!m) continue;
    const j = finDuMorceau(lignes, i, m[1]);
    if (j < 0) continue;
    const texte = lignes.slice(i, j + 1).join("\n");
    if (!EFFET_LIT.test(texte) || !EFFET_ECRIT.test(texte)) continue;
    const deps = (texte.match(/\},\s*(\[[\s\S]*\])\)\s*;?\s*$/) || [, "?"])[1].replace(/\s+/g, " ");
    vus[deps] = (vus[deps] || 0) + 1;
    effets.push({ cle: `effet ${deps}${vus[deps] > 1 ? " #" + vus[deps] : ""}`, debut: i, fin: j, texte });
  }
  return effets;
}

function decouperBloc(lignes) {
  const debuts = [];
  lignes.forEach((l, i) => {
    if (/^(\s*)\{statusChangeTarget \? \(\s*$/.test(l) && /status-change-modal/.test(lignes.slice(i, i + 3).join(" "))) debuts.push(i);
  });
  if (debuts.length !== 1) return { erreur: `ancien bloc : ${debuts.length} début(s) trouvé(s), il en faut un` };
  const i = debuts[0];
  const marge = lignes[i].match(/^(\s*)/)[1];
  let j = i + 1;
  while (j < lignes.length && !new RegExp(`^${marge}\\) : null\\}\\s*$`).test(lignes[j])) j++;
  if (j >= lignes.length) return { erreur: "ancien bloc : fin introuvable" };
  return { debut: i, fin: j, texte: lignes.slice(i, j + 1).join("\n") };
}

const NATIFS = new Set(("if for while switch catch return typeof trim map filter some every find findIndex includes has get set " +
  "toLocaleString toFixed toLowerCase toUpperCase startsWith endsWith replace split join slice isArray from parse stringify " +
  "test match abs max min round floor ceil Number String Boolean preventDefault stopPropagation push concat keys values entries " +
  "sort reduce indexOf padStart").split(" "));

function inventaire(bloc) {
  const uniq = (re) => [...new Set((bloc.match(re) || []))].sort();
  const appels = uniq(/\b[a-z][A-Za-z0-9_]*(?=\()/g).filter((n) => !NATIFS.has(n) && !/^set[A-Z]/.test(n));
  const etats = uniq(/\b(?:statusChange|repartition|carnet|personnes)[A-Z][A-Za-z0-9_]*\b/g)
    .filter((n) => !appels.includes(n));
  const boutons = [];
  const lb = bloc.split("\n");
  for (let i = 0; i < lb.length; i++) {
    if (!/<button/.test(lb[i])) continue;
    let t = "";
    for (let j = i; j < lb.length && j < i + 14; j++) { t += " " + lb[j].trim(); if (/<\/button>/.test(lb[j])) break; }
    const action = (t.match(/onClick=\{\(?[^)]*\)?\s*=>\s*(?:\{\s*)?(?:void\s+)?([A-Za-z]+)\(/) || t.match(/onClick=\{([A-Za-z]+)\}/) || [, /type="submit"/.test(t) ? "SUBMIT" : "?"])[1];
    const libelle = t.replace(/\{\/\*[\s\S]*?\*\/\}/g, "").replace(/<[^>]*>/g, " ").replace(/\{[^{}]*\}/g, " ").replace(/\s+/g, " ").trim().slice(-60);
    boutons.push(`${action} · ${libelle}`);
  }
  const conditions = lb.filter((l) => /\?\s*\(\s*$|&&\s*\(\s*$|\{\(\(\)\s*=>\s*\{/.test(l) && !/^\s*\{\s*\/\*/.test(l)).length;
  return {
    setters: uniq(/\bset[A-Z][A-Za-z0-9_]*\b/g),
    gestes: uniq(/\b(?:handle|close|open)[A-Z][A-Za-z0-9_]*\b/g),
    appels,
    etats,
    composants: uniq(/<[A-Z][A-Za-z0-9_]*/g).map((c) => c.slice(1)).filter((c) => !["T", "HTMLFormElement", "Fragment"].includes(c)),
    boutons,
    conditions,
    classes_telephone: (bloc.match(/className="[^"]*\brq-mobile\b[^"]*"/g) || []).length,
  };
}

// ── la mesure complète, sur des sources données (vraies ou mutées) ──
function mesurer(src) {
  const lignes = { app: src.app.replace(/\r\n/g, "\n").split("\n"), api: src.api.replace(/\r\n/g, "\n").split("\n") };
  const morceaux = {};
  const erreurs = [];
  for (const f of ["app", "api"]) {
    for (const nom of FONCTIONS[f]) {
      const d = decouperFonction(lignes[f], nom);
      if (d.erreur) erreurs.push(d.erreur); else morceaux[`${f}:${nom}`] = { ...d, fichier: f };
    }
  }
  for (const e of decouperEffets(lignes.app)) morceaux[`app:${e.cle}`] = { ...e, fichier: "app" };
  const bloc = decouperBloc(lignes.app);
  if (bloc.erreur) erreurs.push(bloc.erreur); else morceaux["app:ANCIEN BLOC de la modale"] = { ...bloc, fichier: "app" };
  const sortie = { empreintes: {}, lignes: {}, inventaire: bloc.erreur ? null : inventaire(bloc.texte) };
  for (const [cle, m] of Object.entries(morceaux)) {
    sortie.empreintes[cle] = empreintes(m.texte);
    sortie.lignes[cle] = `${m.debut + 1}-${m.fin + 1}`;
  }
  return { sortie, erreurs, morceaux };
}

function comparer(ref, cur) {
  const ecarts = [];
  const cles = new Set([...Object.keys(ref.empreintes), ...Object.keys(cur.empreintes)]);
  for (const k of cles) {
    const a = ref.empreintes[k], b = cur.empreintes[k];
    if (!a) ecarts.push({ cle: k, nature: "nouveau (absent de la référence)" });
    else if (!b) ecarts.push({ cle: k, nature: "DISPARU" });
    else if (a.code !== b.code) ecarts.push({ cle: k, nature: "CODE CHANGÉ" });
    else if (a.exacte !== b.exacte) ecarts.push({ cle: k, nature: "commentaire ou espaces seulement" });
  }
  return ecarts;
}

// ── programme ──
let src;
try { src = { app: fs.readFileSync(SOURCES.app, "utf8"), api: fs.readFileSync(SOURCES.api, "utf8") }; }
catch (e) { console.log("⛔ lecture impossible : " + e.message); process.exit(2); }

const { sortie, erreurs, morceaux } = mesurer(src);
if (erreurs.length) { erreurs.forEach((e) => console.log("⛔ " + e)); process.exit(2); }
const nbFonctions = FONCTIONS.app.length + FONCTIONS.api.length;
const nbEffets = Object.keys(sortie.empreintes).filter((k) => k.startsWith("app:effet ")).length;
console.log(`mesuré : ${nbFonctions} fonctions, ${nbEffets} effets, l'ancien bloc (l. ${sortie.lignes["app:ANCIEN BLOC de la modale"]})`);

if (process.argv.includes("--poser")) {
  const ref = { pose_le: new Date().toISOString(), commit: null, ...sortie };
  try { ref.commit = require("child_process").execSync("git rev-parse --short HEAD", { cwd: RACINE }).toString().trim(); } catch { /* sans git */ }
  fs.writeFileSync(REFERENCE, JSON.stringify(ref, null, 2) + "\n");
  console.log(`référence posée : ${path.relative(process.cwd(), REFERENCE)} (sommet ${ref.commit})`);
  process.exit(0);
}

let echecs = 0;
const ok = (cond, libelle) => { console.log(`${cond ? "  OK " : "  ⛔ "} ${libelle}`); if (!cond) echecs++; };

console.log("TEMOIN INVERSE — sur une copie en mémoire");
const ancre = (cle) => morceaux[cle];
function muter(cle, transformer) {
  const m = ancre(cle);
  const l = src[m.fichier].replace(/\r\n/g, "\n").split("\n");
  transformer(l, m);
  return { ...src, [m.fichier]: l.join("\n") };
}
{
  const r = mesurer(muter("app:handleGesteHektor", (l, m) => l.splice(m.debut + 2, 0, "    void 0")));
  const e = comparer(sortie, r.sortie);
  ok(e.length === 1 && e[0].cle === "app:handleGesteHektor" && e[0].nature === "CODE CHANGÉ",
    `1. une instruction dans handleGesteHektor : ${e.map((x) => x.cle + " " + x.nature).join(", ") || "rien vu"}`);
}
{
  const l = src.app.replace(/\r\n/g, "\n").split("\n");
  l.push("// ligne ajoutee hors de tout morceau suivi");
  const e = comparer(sortie, mesurer({ ...src, app: l.join("\n") }).sortie);
  ok(e.length === 0, `2. une ligne hors des morceaux : ${e.length} écart(s)`);
}
{
  const r = mesurer(muter("app:affaireEstVivante", (l, m) => l.splice(m.debut + 1, 0, "  // commentaire du temoin")));
  const e = comparer(sortie, r.sortie);
  ok(e.length === 1 && e[0].nature === "commentaire ou espaces seulement",
    `3. un commentaire dans affaireEstVivante : ${e.map((x) => x.cle + " " + x.nature).join(", ") || "rien vu"}`);
}
{
  const r = mesurer(muter("app:ANCIEN BLOC de la modale", (l, m) => {
    let k = m.debut;
    while (k <= m.fin && !/>Fermer<\/button>/.test(l[k])) k++;
    if (k <= m.fin) l[k] = l[k].replace(/>Fermer</, ">Fermez<");
  }));
  const e = comparer(sortie, r.sortie);
  ok(e.some((x) => x.cle === "app:ANCIEN BLOC de la modale" && x.nature === "CODE CHANGÉ"),
    `4. un caractère dans l'ancien bloc : ${e.map((x) => x.cle + " " + x.nature).join(", ") || "rien vu"}`);
}

let ref;
try { ref = JSON.parse(fs.readFileSync(REFERENCE, "utf8")); }
catch { console.log("⛔ pas de référence : la poser d'abord avec --poser"); process.exit(2); }
console.log(`CONTRÔLE — contre la référence du ${ref.pose_le} (sommet ${ref.commit})`);
const ecarts = comparer(ref, sortie);
for (const x of ecarts) {
  const grave = x.nature !== "commentaire ou espaces seulement";
  console.log(`  ${grave ? "⛔" : "⚠ "} ${x.cle} : ${x.nature} (l. ${sortie.lignes[x.cle] || "?"})`);
  if (grave) echecs++;
}
if (!ecarts.length) console.log(`  OK  ${Object.keys(ref.empreintes).length} morceaux identiques`);
const inv = JSON.stringify(ref.inventaire) === JSON.stringify(sortie.inventaire);
ok(inv, "l'inventaire de l'ancien bloc est identique");

console.log("PARITÉ — la nouvelle vue");
if (!fs.existsSync(V2)) console.log("  ·   src/ModaleStatutV2.tsx n'existe pas encore (lot 1) : contrôle en attente");
else {
  const v2 = fs.readFileSync(V2, "utf8");
  const interdits = [/from\s+['"]\.\/lib\/api['"]/, /supabase/i, /\bcreate[A-Z][A-Za-z]*Job\b/, /\bfetch\(/];
  for (const r of interdits) ok(!r.test(v2), `ModaleStatutV2.tsx n'utilise pas ${r}`);
}

console.log(echecs ? `⛔ ${echecs} contrôle(s) en échec` : "TOUT VERT");
process.exit(echecs ? 1 : 0);
