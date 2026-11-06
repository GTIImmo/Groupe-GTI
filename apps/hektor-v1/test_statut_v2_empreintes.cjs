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

  // ─── LOT 8 (06/11) : TOUT CE QUE L'ANCIEN BLOC UTILISE, LA VUE L'UTILISE (plan §4.2) ───
  // Les listes viennent de la référence (setters, gestes, fonctions appelées, états lus, composants) : un nom de
  // l'ancien bloc absent de la vue serait un geste ou une information perdus en route.
  const motsV2 = new Set(v2.match(/[A-Za-z_$][A-Za-z0-9_$]*/g));
  // ─── 06/11 : DEUX CHAMPS RETIRÉS PAR DÉCISION DE FRÉDÉRIC ───
  // notice/AUDIT_CHAMPS_VENDEURS_ET_MANDAT_MODALE_STATUT_2026-11-06.md : « Vendeurs » (Hektor les pose seul, jamais
  // envoyés sans geste, 0 usage réel) et « N° de mandat » (nuisible à l'offre ; la modale ne l'envoie plus).
  // Ces noms, et tout geste ou condition qui les porte, sont ATTENDUS absents de la vue. Leur retour serait un écart.
  const RETIRES = ["statusChangeMandants", "setStatusChangeMandants", "statusChangeMandantsAffirmes",
    "setStatusChangeMandantsAffirmes", "statusChangeSelectedMandat", "setStatusChangeSelectedMandat", "SelecteurMandants"];
  const porteUnRetire = (t) => RETIRES.some((n) => new RegExp(`\\b${n}\\b`).test(t));
  const revenus = RETIRES.filter((n) => motsV2.has(n));
  ok(revenus.length === 0, `les champs retirés le 06/11 (vendeurs, n° de mandat) restent absents de la vue${revenus.length ? " — revenus : " + revenus.join(", ") : ""}`);
  for (const k of ["setters", "gestes", "appels", "etats", "composants"]) {
    const liste = ((ref.inventaire && ref.inventaire[k]) || []).filter((n) => !RETIRES.includes(n));
    const absents = liste.filter((n) => !motsV2.has(n));
    if (absents.length) console.log(`     absents (${k}) : ${absents.join(", ")}`);
    ok(liste.length > 0 && absents.length === 0, `inventaire de l'ancien bloc — ${k} : ${liste.length - absents.length} sur ${liste.length} dans la vue`);
  }

  // ─── LOT 2 (06/11) : LES GESTES DE SAISIE, REPRIS MOT POUR MOT ───
  // Chaque gestionnaire (onChange, onClick, onChoisir, onRetirer, onAjouter) d'une zone DÉJÀ PORTÉE de l'ancien
  // bloc doit se retrouver tel quel dans la nouvelle vue (commentaires et espaces mis à part). Un écart VOULU se
  // DÉCLARE ci-dessous, avec sa raison ; tout autre écart est un échec.
  const norm = (t) => t.replace(/\/\/[^\n]*/g, "").replace(/\{\/\*[\s\S]*?\*\/\}/g, "").replace(/\/\*[\s\S]*?\*\//g, "").replace(/\s+/g, "");
  const gestionnaires = (t) => {
    const out = []; const re = /\bon(Change|Click|Choisir|Retirer|Ajouter)=\{/g; let g;
    while ((g = re.exec(t))) {
      let k = g.index + g[0].length, p = 1;
      while (p && k < t.length) { if (t[k] === "{") p++; else if (t[k] === "}") p--; k++; }
      out.push(t.slice(g.index, k));
    }
    return out;
  };
  const lignesApp = src.app.replace(/\r\n/g, "\n").split("\n");
  const dBloc = lignesApp.findIndex((l, k) => l.includes("{statusChangeTarget ? (") && lignesApp.slice(k, k + 4).join("").includes("status-change-modal"));
  const mBloc = dBloc < 0 ? "" : lignesApp[dBloc].match(/^\s*/)[0];
  const fBloc = lignesApp.findIndex((l, k) => k > dBloc && l === mBloc + ") : null}");
  const ancien = dBloc < 0 || fBloc < 0 ? "" : lignesApp.slice(dBloc, fBloc + 1).join("\n");
  const ZONES = [
    { lot: 2, nom: "le formulaire offre / compromis / vente", debut: "{statusChangeNeedsTransaction(statusChangeStatus) ? (", fin: ") : statusChangeStatus === 'closed' ? (" },
    { lot: 1, nom: "l'en-tête et les cartes de statut", debut: "<div className=\"panel-head status-change-head\">", fin: "{statusChangeNeedsTransaction(statusChangeStatus) ? (" },
    { lot: 5, nom: "le pied (les boutons)", debut: "<div className=\"modal-actions\">", fin: "</form>" },
    { lot: 4, nom: "les affaires du bien et leurs bandeaux", debut: "{statusChangeAffaires.length > 0 ? (() => {", fin: "{modifierChezHektorPossible(statusChangeStatus, affaireCourantePourStatut(), statusChangeAffaires) ? (" },
    { lot: 3, nom: "la clôture du mandat (Clos)", debut: ") : statusChangeStatus === 'closed' ? (", fin: "{bvs(\"Le statut Actif est envoyé directement" },
  ];
  const ECARTS_VOULUS = [
    // « Qui paie la commission » : le menu devient deux boutons (même valeur, mêmes setters). Le clic sur le choix
    // déjà posé ne fait rien, comme un menu dont la valeur ne change pas : sinon la commission serait « touchée ».
    "onChange={(event)=>{setStatusChangeChargeCommission(event.target.value)setStatusChangeCommissionTouchee(true)}}",
    // Lot 1 : la carte de statut appelle `choisir(carte.statut)`, qui fait les DEUX mêmes appels dans le même ordre
    // (setStatusChangeStatus puis setStatusChangeAffaireChoisie(null)) — partagée avec « Aller à l'étape conseillée ».
    "onClick={()=>{setStatusChangeStatus(option.value);setStatusChangeAffaireChoisie(null)}}",
  ];
  const v2n = norm(v2);
  // ─── LOT 5 (06/11) : LES CONDITIONS AUSSI ───
  // Un bouton, c'est un geste ET deux conditions : quand il s'affiche, quand il s'éteint. On extrait de chaque zone
  // les `disabled={…}` et les conditions d'affichage (`{cond ? (` et `{cond ? null : (`), et chacune doit se
  // retrouver telle quelle dans la vue — sinon elle est déclarée ici avec sa raison.
  const disabledDe = (t) => {
    const out = []; const re = /\bdisabled=\{/g; let g;
    while ((g = re.exec(t))) {
      let k = g.index + g[0].length, p = 1;
      while (p && k < t.length) { if (t[k] === "{") p++; else if (t[k] === "}") p--; k++; }
      out.push(t.slice(g.index, k));
    }
    return out;
  };
  const conditionsDe = (t) => {
    const out = []; const re = /\?\s*(\(|null\s*:\s*\()/g; let g;
    while ((g = re.exec(t))) {
      // on remonte jusqu'à l'accolade qui ouvre l'expression JSX, en comptant parenthèses et accolades
      let k = g.index - 1, p = 0;
      while (k >= 0) {
        const c = t[k];
        if (c === ")" || c === "}") p++;
        else if (c === "(") { if (p === 0) break; p--; }
        else if (c === "{") { if (p === 0) break; p--; }
        k--;
      }
      if (k >= 0 && t[k] === "{") out.push(t.slice(k + 1, g.index).trim());
    }
    return out.filter((c) => c.length > 0 && !/^\s*\/\*/.test(c));
  };
  const CONDITIONS_VOULUES = [
    // Lot 4 : l'ancien bloc ne montre RIEN quand le bien n'a aucune affaire ; la vue dit « Aucune affaire lue pour ce
    // bien » (même test, inversé : `if (statusChangeAffaires.length === 0) return …`). Écran seulement.
    "statusChangeAffaires.length>0",
  ];
  for (const z of ZONES) {
    const a = ancien.indexOf(z.debut), b = ancien.indexOf(z.fin, a);
    if (a < 0 || b < 0) continue;
    const zone = ancien.slice(a, b);
    const conds = [...disabledDe(zone), ...conditionsDe(zone)];
    const absentes = conds.filter((c) => !v2n.includes(norm(c)) && !CONDITIONS_VOULUES.includes(norm(c)) && !porteUnRetire(c));
    for (const c of absentes) console.log(`     condition absente : ${c.replace(/\s+/g, " ").slice(0, 150)}`);
    ok(conds.length === 0 || absentes.length === 0,
      `lot ${z.lot} : ${z.nom} — ${conds.length - absentes.length} conditions sur ${conds.length} reprises telles quelles`);
  }
  for (const z of ZONES) {
    const a = ancien.indexOf(z.debut), b = ancien.indexOf(z.fin, a);
    if (a < 0 || b < 0) { ok(false, `lot ${z.lot} : zone « ${z.nom} » introuvable dans l'ancien bloc`); continue; }
    const tous = gestionnaires(ancien.slice(a, b));
    const differents = tous.filter((h) => !v2n.includes(norm(h)) && !ECARTS_VOULUS.includes(norm(h)) && !porteUnRetire(h));
    for (const h of differents) console.log(`     différent : ${h.replace(/\s+/g, " ").slice(0, 150)}`);
    ok(tous.length > 0 && differents.length === 0,
      `lot ${z.lot} : ${z.nom} — ${tous.length - differents.length} gestes sur ${tous.length} repris mot pour mot ou déclarés`);
  }
}

console.log(echecs ? `⛔ ${echecs} contrôle(s) en échec` : "TOUT VERT");
process.exit(echecs ? 1 : 0);
