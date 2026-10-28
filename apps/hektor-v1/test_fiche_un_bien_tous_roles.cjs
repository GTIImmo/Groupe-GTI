#!/usr/bin/env node
"use strict";
/**
 * ⑧ TYPES, P2 — DANS LA FICHE CONTACT, UN BIEN = UNE LIGNE AVEC TOUS SES RÔLES.   27/10/2026
 *
 *   La vue rend une ligne PAR RÔLE ; les deux fiches gardaient la première et jetaient les autres, et la première
 *   était tirée au hasard (égalité de `last_seen_at`). regrouperRelationsParBien (App.tsx) fait une ligne par bien,
 *   avec tous ses rôles, dans un ordre fixe, et l'étape d'acheteur décidée par Frédéric le 27/10 :
 *   la VENTE si elle existe, sinon la plus récente ; offre refusée / compromis annulé montrés en gris ;
 *   « Propriétaire depuis le … » quand le lien est né de la vente.
 *
 * On EXÉCUTE le code réel : les fonctions sont découpées dans App.tsx et jouées par esbuild + vm.
 * ⚠ TÉMOIN INVERSE : l'ancien dédoublonnage (découpé lui aussi dans App.tsx) CHANGE de rôle affiché quand on mélange
 *   les lignes ; le nouveau, jamais. MUTANT : sans la règle « la vente d'abord », un cas doit tomber.
 * Données SYNTHÉTIQUES, construites sur les combinaisons mesurées le 27/10 (aucune donnée personnelle).
 *
 * NE LANCE NI SERVEUR NI REQUÊTE.
 *     node apps/hektor-v1/test_fiche_un_bien_tous_roles.cjs
 *     sortie 0 = tout vert · 1 = un contrôle en échec · 2 = n'a pas pu mesurer
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const esbuild = require("esbuild");

const APP = path.resolve(__dirname, "src", "App.tsx");

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const finLigne = src.indexOf("\n", i);
  const ligne = src.slice(i, finLigne < 0 ? undefined : finLigne);
  if (/^const \w+ = [^{(]*$/.test(ligne)) return ligne;           // constante sur une ligne
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

// ⑧ notaire, étape 3 (28/10) : familleDuRole et regrouperRelationsParBien appellent les aides du notaire
const MORCEAUX = ["const TYPE_CONTACT_UNIQUE = ", "const FICHE_UN_BIEN_TOUS_ROLES = ", "const TYPE_NOTAIRE_ECRAN = ",
  "function estRoleNotaire(", "function roleNotaireDuBien(", "function contactDirectoryRoleLabel(",
  "function dateDuRole(", "function couleurDuRoleDuBien(", "function familleDuRole(", "function etapeAcheteurRetenue(",
  "function detailEtapeAcheteur(", "function regrouperRelationsParBien("];

function monter(src) {
  const s = src.replace(/\r\n/g, "\n");
  const code = [];
  for (const m of MORCEAUX) {
    const t = tranche(s, m);
    if (!t) return { erreur: `absent : ${m}` };
    code.push(t);
  }
  // l'ANCIEN dédoublonnage, tel qu'il est dans la fiche V2 (bloc « Biens & mandats liés (Lot 3) »)
  const debutAncien = s.indexOf("const linkedRelations = (() => {", s.indexOf("Biens & mandats liés (Lot 3)"));
  const finAncien = s.indexOf("\n  })()", debutAncien);
  if (debutAncien < 0 || finAncien < 0) return { erreur: "absent : l'ancien dédoublonnage de la fiche V2" };
  const ancien = s.slice(debutAncien, finAncien + "\n  })()".length)
    .replace("const linkedRelations = (() => {", "function ancienDedoublonnage(props) {").replace(/\n  \}\)\(\)$/, "\n}");
  code.push(ancien);
  const js = esbuild.transformSync(code.join("\n\n") + "\nthis.api = { regrouperRelationsParBien, ancienDedoublonnage, contactDirectoryRoleLabel, FICHE_UN_BIEN_TOUS_ROLES };",
    { loader: "ts" }).code;
  const ctx = { String, Number, Boolean, Array, Set, Map, Object, JSON, RegExp };
  vm.createContext(ctx);
  vm.runInContext(js, ctx);
  return { api: ctx.api };
}

let echecs = 0;
function verifier(nom, ok, detail) {
  console.log(`${ok ? "OK   " : "ECHEC"} ${nom}${ok ? "" : "  -> " + detail}`);
  if (!ok) echecs++;
}

let src;
try { src = fs.readFileSync(APP, "utf8"); } catch (e) { console.log("IMPOSSIBLE de lire App.tsx : " + e.message); process.exit(2); }
const neuf = monter(src);
if (neuf.erreur) { console.log(neuf.erreur); process.exit(2); }
const { regrouperRelationsParBien: grouper, ancienDedoublonnage } = neuf.api;

// ── les données : une ligne de la vue, au format réel (les deux formes de last_seen_at comprises) ──
let n = 0;
const lienBien = (c, a, role, extra = {}) => ({ relation_key: `k${++n}`, hektor_contact_id: c, hektor_annonce_id: a, app_dossier_id: Number(a) * 10,
  numero_mandat: "17 482", titre_bien: "Maison", role_contact: role, relation_source: "sync_annonce_contact_link",
  transaction_state: null, transaction_date: null, transaction_amount: null, last_seen_at: "2026-10-27T04:52:00+00:00", ...extra });
const ligneRegistre = (c, a, kind, state, date, montant, id) => ({ relation_key: `aff_${id}_${c}`, hektor_contact_id: c, hektor_annonce_id: a,
  app_dossier_id: Number(a) * 10, numero_mandat: "17 482", titre_bien: "Maison", role_contact: `acquereur_${kind}`,
  relation_source: "registre_transactions", transaction_type: kind, transaction_id: String(id), transaction_state: state,
  transaction_date: date, transaction_amount: kind === "offre" ? null : montant, last_seen_at: "2026-10-27 04:48:59+00" });

const CAS = {
  // le cas de JACQUIER sur 61730 (dates et montant de la mesure du 27/10, noms retirés)
  jacquier: [lienBien("C1", "61730", "proprietaire", { origine: "vente", proprietaire_depuis: "2026-09-25" }),
    ligneRegistre("C1", "61730", "offre", "accepted", "2026-05-26 09:08:58", null, 101),
    ligneRegistre("C1", "61730", "compromis", "active", "2026-06-12", "210000.00", 102),
    ligneRegistre("C1", "61730", "vente", "vente", "2026-09-25", "210000.00", 103)],
  offreCompromis: [ligneRegistre("C2", "500", "offre", "accepted", "2026-03-01 10:00:00", null, 201),
    ligneRegistre("C2", "500", "compromis", "active", "2026-03-20", "150000.00", 202)],
  compromisAnnule: [ligneRegistre("C3", "501", "offre", "accepted", "2026-03-01 10:00:00", null, 301),
    ligneRegistre("C3", "501", "compromis", "cancelled", "2026-03-10", "150000.00", 302)],
  deuxOffres: [ligneRegistre("C4", "502", "offre", "refused", "2026-02-01 09:00:00", null, 401),
    ligneRegistre("C4", "502", "offre", "accepted", "2026-02-15 09:00:00", null, 402)],
  offreRefusee: [ligneRegistre("C5", "503", "offre", "refused", "2026-04-01 09:00:00", null, 501)],
  venteEtOffrePlusTard: [ligneRegistre("C6", "504", "vente", "vente", "2025-11-05", "99000.00", 601),
    ligneRegistre("C6", "504", "offre", "proposed", "2026-06-01 09:00:00", null, 602)],
  mandantAcheteur: [lienBien("C7", "505", "mandant"),
    ligneRegistre("C7", "505", "compromis", "active", "2024-01-10", "180000.00", 701),
    ligneRegistre("C7", "505", "vente", "vente", "2024-04-02", "180000.00", 702)],
  proprioSansOrigine: [lienBien("C8", "506", "proprietaire")],
  memeJour: [ligneRegistre("C9", "507", "offre", "accepted", "2026-05-05 08:00:00", null, 901),
    ligneRegistre("C9", "507", "compromis", "active", "2026-05-05", "120000.00", 902)],
  // avant le patch de la vue : pas de colonne origine du tout
  avantPatch: [{ ...lienBien("C10", "508", "proprietaire") },
    ligneRegistre("C10", "508", "vente", "vente", "2026-09-01", "75000.00", 1001)],
};
for (const l of CAS.avantPatch) { delete l.origine; delete l.proprietaire_depuis; }

const un = (lignes) => grouper(lignes)[0];
const roles = (b) => b.roles.map((r) => r.libelle + (r.gris ? "(gris)" : "")).join(" + ");

// ═══ 1. Les cas qui comptent ═══
let b = un(CAS.jacquier);
verifier("JACQUIER : une seule ligne, « Propriétaire + Acheteur »", grouper(CAS.jacquier).length === 1 && roles(b) === "Propriétaire + Acheteur", roles(b));
verifier("JACQUIER : « Propriétaire depuis le 25/09/2026 · Vente signée le 25/09/2026 », 210 000",
  b.sousTitre === "Propriétaire depuis le 25/09/2026 · Vente signée le 25/09/2026" && b.montant === "210000.00", `${b.sousTitre} / ${b.montant}`);
verifier("JACQUIER : la ligne porteuse est celle du lien du bien (propriétaire)", b.relation.role_contact === "proprietaire", b.relation.role_contact);
b = un(CAS.offreCompromis);
verifier("offre + compromis : « Compromis du 20/03/2026 » et son montant", b.sousTitre === "Compromis du 20/03/2026" && b.montant === "150000.00", `${b.sousTitre} / ${b.montant}`);
b = un(CAS.compromisAnnule);
verifier("compromis annulé après l'offre : « Compromis annulé (du 10/03/2026) », EN GRIS", b.sousTitre === "Compromis annulé (du 10/03/2026)" && b.roles[0].gris === true, `${b.sousTitre} / gris=${b.roles[0].gris}`);
b = un(CAS.deuxOffres);
verifier("deux offres (refusée puis acceptée) : la plus récente, « Offre acceptée »", b.sousTitre === "Offre acceptée (du 15/02/2026)" && !b.roles[0].gris, b.sousTitre);
b = un(CAS.offreRefusee);
verifier("offre refusée seule : montrée, en gris", b.sousTitre === "Offre refusée (du 01/04/2026)" && b.roles[0].gris === true, b.sousTitre);
b = un(CAS.venteEtOffrePlusTard);
verifier("la VENTE d'abord, même si une offre est plus récente", b.sousTitre === "Vente signée le 05/11/2025" && b.montant === "99000.00", b.sousTitre);
b = un(CAS.mandantAcheteur);
verifier("mandant + acheteur du même bien : « Mandant + Acheteur », l'achat n'est plus caché", roles(b) === "Mandant + Acheteur" && b.sousTitre === "Vente signée le 02/04/2024", `${roles(b)} / ${b.sousTitre}`);
b = un(CAS.proprioSansOrigine);
verifier("propriétaire sans origine : « Propriétaire », sans date ni montant", roles(b) === "Propriétaire" && b.sousTitre === null && b.montant === null, `${roles(b)} / ${b.sousTitre}`);
b = un(CAS.memeJour);
verifier("offre et compromis le même jour : le compromis (le plus avancé)", b.sousTitre === "Compromis du 05/05/2026", b.sousTitre);
b = un(CAS.avantPatch);
verifier("AVANT le patch de la vue (pas de colonne origine) : pas d'erreur, « Propriétaire + Acheteur » sans date de propriété",
  roles(b) === "Propriétaire + Acheteur" && b.sousTitre === "Vente signée le 01/09/2026", `${roles(b)} / ${b.sousTitre}`);
verifier("aucun mot anglais dans les sous-titres (active, accepted, cancelled, refused, proposed)",
  Object.values(CAS).every((l) => !/\b(active|accepted|cancelled|refused|proposed)\b/.test(String(un(l).sousTitre))), "un mot brut reste");

// ═══ 2. La liste : mêmes biens, même ordre, même nombre que l'ancien dédoublonnage ═══
const melange = [...CAS.jacquier.slice(0, 2), ...CAS.mandantAcheteur, { ...lienBien("C1", "", "mandant"), app_dossier_id: null },
  ...CAS.jacquier.slice(2), ...CAS.offreRefusee];
const anc = ancienDedoublonnage({ relations: melange });
const nv = grouper(melange);
const cle = (r) => String(r.app_dossier_id ?? "").trim() || String(r.hektor_annonce_id ?? "").trim() || "(sans clé)";
verifier(`le i-ème bien regroupé est le i-ème bien d'avant (${anc.length} biens, une ligne sans clé comprise)`,
  anc.length === nv.length && anc.every((r, i) => cle(r) === cle(nv[i].relation)), `${anc.map(cle)} / ${nv.map((x) => cle(x.relation))}`);

// ═══ 3. TÉMOIN INVERSE : l'ordre des lignes ne change plus rien ═══
function permutations(a) { if (a.length <= 1) return [a]; return a.flatMap((x, i) => permutations([...a.slice(0, i), ...a.slice(i + 1)]).map((p) => [x, ...p])); }
let neufStable = true, ancienChange = false, essais = 0;
for (const [nom, lignes] of Object.entries(CAS)) {
  const ref = JSON.stringify(grouper(lignes).map((x) => ({ r: x.relation.relation_key, roles: x.roles, m: x.montant, s: x.sousTitre })));
  const vusAncien = new Set();
  for (const p of permutations(lignes)) {
    essais++;
    const s = JSON.stringify(grouper(p).map((x) => ({ r: x.relation.relation_key, roles: x.roles, m: x.montant, s: x.sousTitre })));
    if (s !== ref) { neufStable = false; console.log("   instable :", nom); }
    vusAncien.add(ancienDedoublonnage({ relations: p }).map((r) => r.role_contact).join(","));
  }
  if (vusAncien.size > 1) ancienChange = true;
}
verifier(`le nouveau regroupement ne dépend pas de l'ordre (${essais} ordres essayés)`, neufStable, "un résultat change avec l'ordre");
verifier("TÉMOIN : l'ancien dédoublonnage, lui, change de rôle affiché selon l'ordre", ancienChange, "l'ancien ne bouge pas : l'essai ne prouve rien");

// ═══ 4. Le branchement dans les deux fiches, et le chemin d'avant gardé ═══
const s = src.replace(/\r\n/g, "\n");
verifier("l'interrupteur est allumé", /\nconst FICHE_UN_BIEN_TOUS_ROLES = true\n/.test(s), "absent ou éteint");
verifier("les DEUX fiches (V1 et V2) regroupent derrière l'interrupteur",
  (s.match(/const biensDuContact = FICHE_UN_BIEN_TOUS_ROLES \? regrouperRelationsParBien\(props\.relations\) : null/g) || []).length === 2, "pas 2 branchements");
verifier("l'ancien affichage reste pour l'interrupteur éteint (les deux fiches)",
  (s.match(/: <span className=\{roleTagClass\(relation\.role_contact\)\}>\{contactDirectoryRoleLabel\(relation\.role_contact\)\}<\/span>\}/g) || []).length === 1
  && (s.match(/<span className="fa-cx-lk-role">\{contactDirectoryRoleLabel\(relation\.role_contact\)\}<\/span>/g) || []).length === 1, "un chemin d'avant a disparu");
verifier("props.relations n'est pas touché (bon de visite, modales) : aucune affectation",
  !/props\.relations\s*=(?!=)/.test(s) && !/props\.relations\.(sort|splice|reverse)\(/.test(s), "props.relations est modifié");

// ═══ 5. MUTANT : sans « la vente d'abord », un cas doit tomber ═══
const mut = monter(src.replace("const candidates = ventes.length ? ventes : lignes", "const candidates = lignes"));
if (mut.erreur) { console.log(mut.erreur); process.exit(2); }
const bm = mut.api.regrouperRelationsParBien(CAS.venteEtOffrePlusTard)[0];
verifier("MUTANT (sans la règle de la vente) : attrapé", bm.sousTitre !== "Vente signée le 05/11/2025", "le mutant passe");

console.log(echecs ? `\n${echecs} contrôle(s) en échec` : "\ntout vert");
process.exit(echecs ? 1 : 0);
