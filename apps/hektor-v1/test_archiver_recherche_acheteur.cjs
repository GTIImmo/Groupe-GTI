#!/usr/bin/env node
"use strict";
/**
 * ⑧ types §52 B — L'ACHETEUR QUI A ENCORE UNE RECHERCHE ACTIVE : la fenêtre Oui / Non.   28/10/2026
 *
 * On EXECUTE le vrai `achatsDeLAcheteur` (découpé dans App.tsx, types retirés par esbuild) sur des lignes au format de
 * la vue des liens, et on lit dans le code de la fiche V2 les trois promesses de Frédéric : rien d'automatique (la
 * fenêtre ne part que d'un clic), « Non » ferme sans rien envoyer, « Oui » passe par LE MÊME travail que la corbeille.
 * ⚠ TEMOIN INVERSE : rejoué sur HEAD, l'essai doit échouer (la fonction n'y existe pas).
 * NE LANCE NI SERVEUR NI REQUETE.   node apps/hektor-v1/test_archiver_recherche_acheteur.cjs
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { execFileSync } = require("child_process");
const esbuild = require("esbuild");

const RACINE = path.resolve(__dirname, "..", "..");
const APP = "apps/hektor-v1/src/App.tsx";
function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}
function monter(src) {
  const t = tranche(src, "function achatsDeLAcheteur(");
  if (!t) return null;
  const ctx = { String, Map, Array };
  vm.createContext(ctx);
  vm.runInContext(esbuild.transformSync(t + "\nthis.f = achatsDeLAcheteur;", { loader: "ts" }).code, ctx);
  return ctx.f;
}
function essai(src) {
  const R = [];
  const ok = (nom, vrai, detail) => R.push({ nom, vrai: Boolean(vrai), detail });
  const f = monter(src);
  ok("la fonction existe dans App.tsx", typeof f === "function");
  if (typeof f !== "function") return R;
  const l = (role, annonce, date, titre) => ({ role_contact: role, hektor_annonce_id: annonce, transaction_date: date, titre_bien: titre });
  // 20000015 sur 24113, mesuré le 28/10 : offre, compromis, vente vivante, propriétaire
  const a = f([l("acquereur_offre", "24113", "2026-10-23 19:35:55"), l("acquereur_compromis", "24113", "2026-10-23"),
    l("acquereur_vente", "24113", "2026-10-23", "VA6482"), l("proprietaire", "24113", null)]);
  ok("un acheteur dont la vente vit : 1 achat, daté de la vente", a.length === 1 && a[0].annonce === "24113" && a[0].date === "2026-10-23" && a[0].titre === "VA6482", a);
  ok("une offre ou un compromis seuls ne font pas un achat (D4 : seulement après la vente)",
    f([l("acquereur_offre", "1", "2026-10-01"), l("acquereur_compromis", "1", "2026-10-02")]).length === 0);
  ok("un mandant ou un propriétaire ne sont pas des achats", f([l("mandant", "1"), l("proprietaire", "2")]).length === 0);
  const deux = f([l("acquereur_vente", "1", "2020-05-01"), l("acquereur_vente", "2", "2026-09-01"), l("acquereur_vente", "1", "2021-01-01")]);
  ok("deux biens achetés : un par bien, le plus récent d'abord", deux.length === 2 && deux[0].annonce === "2" && deux[1].date === "2021-01-01", deux);
  ok("une ligne sans bien est ignorée", f([l("acquereur_vente", "", "2026-01-01")]).length === 0);
  // le code de la fiche V2
  const v2 = src.slice(src.indexOf("function ContactDetailPopupV2("), src.indexOf("function ContactDetailPopup(props"));
  ok("la fenêtre ne s'ouvre que d'un clic (rien d'automatique)",
    (v2.match(/setArchiverAcheteurOuvert\(true\)/g) || []).length === 1 && /onClick=\{\(\) => \{ setArchiverAcheteurErreur\(null\); setArchiverAcheteurOuvert\(true\) \}\}/.test(v2));
  ok("« Non » ferme sans rien envoyer", /type="button" onClick=\{\(\) => setArchiverAcheteurOuvert\(false\)\} disabled=\{archiverAcheteurEnvoi\}>Non</.test(v2));
  ok("« Oui » passe par le MÊME travail que la corbeille (archivage daté chez Hektor)",
    /async function archiverRecherchesAcheteur\(\)[\s\S]{0,400}createDeleteHektorContactSearchJob\(\{ contactId: props\.contact\.hektor_contact_id, searchIndex: search\.search_index \}\)/.test(v2));
  ok("la question est celle de Frédéric", v2.includes('summary="Voulez-vous archiver la recherche de l\'acheteur ?"'));
  ok("réservé à qui peut gérer les contacts", /props\.canManageContacts && recherchesAcheteurAArchiver\.length > 0/.test(v2) && /archiverAcheteurOuvert && props\.canManageContacts/.test(v2));
  ok("une recherche en création ou déjà en archivage n'est pas reproposée",
    /!contactSearchProvisional\(s\)\.provisoire && !\(s\.contact_search_key in recherchesEnSuppression\.enCours\)/.test(v2));
  return R;
}
const neuf = essai(fs.readFileSync(path.join(RACINE, APP), "utf8"));
let echecs = 0;
for (const r of neuf) { console.log(`${r.vrai ? "  OK  " : "ECHEC "} ${r.nom}${r.vrai ? "" : " -- " + JSON.stringify(r.detail ?? "")}`); if (!r.vrai) echecs++; }
try {
  const avant = execFileSync("git", ["show", `HEAD:${APP}`], { cwd: RACINE, encoding: "utf8", maxBuffer: 1 << 27 });
  const anciens = essai(avant);
  console.log(`\nTEMOIN INVERSE (HEAD) : ${anciens.filter((r) => !r.vrai).length} controle(s) sur ${anciens.length} y echouent`);
} catch (e) { console.log("\n⚠ temoin inverse non fait : " + e.message); }
console.log(echecs ? `\n⛔ ${echecs} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
process.exit(echecs ? 1 : 0);
