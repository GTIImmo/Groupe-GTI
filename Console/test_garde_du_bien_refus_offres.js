// ════════════════════════════════════════════════════════════════════════════
// LA GARDE DU BIEN (⑤) SUR LE LOT DE REFUS D'OFFRES.              23/11/2026
//
//     python -u -X utf8 phase2/checks/extraire_etat_du_11_11_pour_la_garde_du_bien.py
//     node Console/test_garde_du_bien_refus_offres.js
//
// SA DEMANDE (mot du 23/11, § 4 a) : « Qu'elle cherche la vente par
// `hektor_annonce_id` en plus de la chaine. [...] SON TEMOIN INVERSE, et il est
// deja ecrit par la mesure : rejouee sur le 11/11, elle doit retenir EXACTEMENT
// ces 17 offres -- et PAS UNE DE PLUS. Si elle en retient 20 ou 14, elle est
// fausse, et je ne la prends pas. »
//
// CE QU'ON EPROUVE, EN DEUX PARTIES :
//   1. HORS LIGNE : la garde sur des lignes fabriquees -- le danger sans elle,
//      le temoin inverse (un bien sans vente reste refusable), les deux modes,
//      et sa place dans le fichier.
//   2. SUR L'ETAT DU 11/11 (sauvegarde datee de 08:00, AVANT le lot de 17:21) :
//      on rejoue LE VRAI CODE du lot (selectionCascade et trier, exportes), les
//      deux modes, SANS puis AVEC la garde.
//        a. SANS la garde, le rejeu doit retrouver ce que le lot a VRAIMENT pose
//           le 11/11 (les travaux, lus chez Supabase) -- sinon le rejeu ne prouve
//           rien ;
//        b. AVEC la garde, les offres retenues doivent etre EXACTEMENT ses 17, plus
//           les 19 deja reacceptees le 12/11 (meme defaut, deja repare : « LE
//           TOTAL EST 36 ») -- et AUCUNE autre ;
//        c. rien d'autre ne bouge : avec = sans moins les retenues.
// ⛔ AUCUNE ECRITURE, NULLE PART. Le lot est REQUIS, pas lance (require.main).
// CODES : 0 vert . 1 un rouge . 2 pas pu (l'etat du 11/11 n'est pas extrait)
// ════════════════════════════════════════════════════════════════════════════
"use strict";
const fs = require("node:fs");
const path = require("node:path");

const FICHIER_LOT = path.join(__dirname, "enqueue_refus_offres_mortes_lot.js");
const src = fs.readFileSync(FICHIER_LOT, "utf8");
const LOT = require(FICHIER_LOT);
const ETAT = "C:\\Hektor\\chantier_classeur_q6_cache\\garde_du_bien\\etat_du_11_11.json";

// SES 17, telles qu'il les a ecrites (offre = notre numero d'affaire / bien).
const SES_17 = ["531/1387", "3648/8395", "6556/12728", "7780/15722", "14112/28653", "14420/29285",
  "17322/36794", "22384/44914", "22446/45081", "24159/47815",
  "5126/10703", "16421/34296", "18600/39032", "21600/43126",
  "14008/28422", "17025/36165", "23995/47557"];

let verts = 0;
const rouges = [];
function juger(nom, attendu, obtenu) {
  const a = JSON.stringify(attendu), o = JSON.stringify(obtenu);
  if (a === o) { verts += 1; console.log("  OK    " + nom); }
  else { rouges.push(nom); console.log("  ROUGE " + nom + "\n        attendu " + a + "\n        obtenu  " + o); }
}
const muet = () => {};
const ids = (aPoser) => aPoser.map((j) => Number(j.payload_json.app_affaire_id)).sort((a, b) => a - b);
function parChaineDe(lignes) {
  const m = new Map();
  for (const t of lignes) {
    if (t.app_chaine_id == null) continue;
    if (!m.has(t.app_chaine_id)) m.set(t.app_chaine_id, []);
    m.get(t.app_chaine_id).push(t);
  }
  return m;
}
function ventesDe(lignes) {
  const m = new Map();
  for (const t of lignes) {
    if (t.kind !== "vente") continue;
    const b = String(t.hektor_annonce_id || "").trim();
    if (!m.has(b)) m.set(b, []);
    m.get(b).push(t);
  }
  return m;
}

// ── 1. HORS LIGNE ───────────────────────────────────────────────────────────
let n = 0;
const L = (ch, kind, state, bien, extra = {}) => ({
  app_affaire_id: ++n, app_chaine_id: ch, kind, state, hektor_affaire_id: String(9000 + n),
  hektor_annonce_id: String(bien), present_in_hektor: true, transaction_origine: null, ...extra });

console.log("=== 1. LE DANGER : la vente du MEME BIEN est dans une AUTRE chaine ===");
const cas1 = [L(1, "offre", "accepted", 100), L(1, "compromis", "cancelled", 100), L(2, "vente", null, 100)];
const d1 = LOT.selectionCascade(cas1);
juger("1  la cascade retient le dossier 1 (sa chaine ne porte pas la vente)", [1], d1.map((d) => d.dossier));
const sans1 = LOT.trier(d1, parChaineDe(cas1), new Set(), new Map(), { source: "cascade", dire: muet });
const avec1 = LOT.trier(d1, parChaineDe(cas1), new Set(), ventesDe(cas1), { source: "cascade", dire: muet });
juger("1b SANS la garde, l offre du bien VENDU part au refus", 1, sans1.aPoser.length);
juger("1c AVEC la garde, elle est retenue", 0, avec1.aPoser.length);
juger("1d et le motif est DIT", 1, avec1.ecartes.get("⑤ LE BIEN PORTE UNE VENTE (hors de ce dossier)") || 0);

console.log("");
console.log("=== 2. ⭐ LE TEMOIN INVERSE : un bien SANS vente reste refusable ===");
const cas2 = [L(3, "offre", "accepted", 200), L(3, "compromis", "cancelled", 200), L(4, "vente", null, 201)];
const d2 = LOT.selectionCascade(cas2);
const avec2 = LOT.trier(d2, parChaineDe(cas2), new Set(), ventesDe(cas2), { source: "cascade", dire: muet });
juger("2  la vente d un AUTRE bien ne protege pas", 1, avec2.aPoser.length);

console.log("");
console.log("=== 3. TOUTES LES VENTES COMPTENT (dans le doute, on ne refuse pas) ===");
for (const [nom, extra] of [["supprimee chez Hektor", { present_in_hektor: false }],
                            ["reprise du classeur", { transaction_origine: "classeur", hektor_affaire_id: null }]]) {
  const c = [L(5, "offre", "accepted", 300), L(5, "compromis", "cancelled", 300), L(6, "vente", null, 300, extra)];
  const a = LOT.trier(LOT.selectionCascade(c), parChaineDe(c), new Set(), ventesDe(c), { source: "cascade", dire: muet });
  juger("3  une vente " + nom + " retient l offre", 0, a.aPoser.length);
}

console.log("");
console.log("=== 4. LE MODE « table » a la meme garde (trier sert aux deux) ===");
const cas4 = [L(7, "offre", "accepted", 400), L(8, "vente", null, 400)];
const t4 = [{ dossier: 7, bien: "400", source: "classeur" }];
juger("4  sans la garde, l offre seule du bien vendu part au refus", 1,
      LOT.trier(t4, parChaineDe(cas4), new Set(), new Map(), { source: "table", dire: muet }).aPoser.length);
juger("4b avec la garde, elle est retenue", 0,
      LOT.trier(t4, parChaineDe(cas4), new Set(), ventesDe(cas4), { source: "table", dire: muet }).aPoser.length);

console.log("");
console.log("=== 5. ON NE CASSE RIEN ===");
const cas5 = [L(9, "offre", "accepted", 500), L(9, "vente", null, 500)];
const a5 = LOT.trier([{ dossier: 9, bien: "500", source: "x" }], parChaineDe(cas5), new Set(), ventesDe(cas5),
                     { source: "table", dire: muet });
juger("5  une vente DANS le dossier est toujours attrapee par la garde ② (la RPC), avant ⑤",
      1, a5.ecartes.get("offre VERROUILLEE par son dossier") || 0);
juger("5b la charge est inchangee (origine, etat_avant, sans_resynchro)",
      ["rattrapage_cascade_annulation", "accepted", true],
      [sans1.aPoser[0].payload_json.origine, sans1.aPoser[0].payload_json.etat_avant,
       sans1.aPoser[0].payload_json.sans_resynchro]);

console.log("");
console.log("=== 6. LA GARDE EST DANS LE FICHIER, AU BON ENDROIT ===");
const iTrier = src.indexOf("function trier(");
const iGarde = src.indexOf("const ventes = ventesDuBien(ventesParBien, annonce);");
const iPush = src.indexOf("aPoser.push({");
juger("6  elle est DANS trier(), AVANT l enfilement", true, iTrier > 0 && iGarde > iTrier && iPush > iGarde);
juger("6b main() lit les ventes PAR LE BIEN", true, src.includes("&kind=eq.vente&hektor_annonce_id=in.("));
juger("6c le temoin positif arrete tout s il n est pas lu (code 2)", true,
      /TEMOIN_VENTE\.vente\)\) \{[\s\S]{0,300}return 2;/.test(src));
juger("6d main() passe les ventes a trier()", true,
      src.includes("trier(dossiers, parDossier, dejaEnCours, ventesParBien,"));
juger("6e le lot ne se lance pas quand on le requiert", true, src.includes("if (require.main === module) {"));

// ── 2. SUR L'ETAT DU 11/11 ──────────────────────────────────────────────────
console.log("");
console.log("=== 7. ⭐⭐ LE TEMOIN : LE VRAI CODE, REJOUE SUR L'ETAT DU 11/11 ===");
if (!fs.existsSync(ETAT)) {
  console.log("⛔ l'etat du 11/11 n'est pas extrait : " + ETAT);
  console.log("   python -u -X utf8 phase2/checks/extraire_etat_du_11_11_pour_la_garde_du_bien.py  -- code 2");
  console.log(verts + "/" + (verts + rouges.length) + " verts (hors ligne seulement)");
  process.exit(2);
}
const etat = JSON.parse(fs.readFileSync(ETAT, "utf8"));
console.log(`   registre du 11/11 : ${etat.lignes.length} lignes (${etat.sauvegarde}, ${etat.prise_le_utc})`);
const lignes = etat.lignes;
const parDossier = parChaineDe(lignes);
const ventes = ventesDe(lignes);
const modes = {
  cascade: { origine: "rattrapage_cascade_annulation",
             dossiers: LOT.selectionCascade(lignes.filter((t) => t.app_chaine_id != null)) },
  table: { origine: "enqueue_refus_offres_mortes_lot",
           dossiers: LOT.lireTable(LOT.TABLE_DEFAUT).filter((r) => (r.proposition || "").startsWith("REFUSER"))
             .map((r) => ({ dossier: Number(r.dossier), bien: r.bien, source: r.source })) },
};
const reacceptees = new Set(etat.travaux.filter((j) => j.type === "accepte").map((j) => Number(j.app_affaire_id)));
const ses17 = new Set(SES_17.map((x) => Number(x.split("/")[0])));
const bienDe17 = new Map(SES_17.map((x) => [Number(x.split("/")[0]), x.split("/")[1]]));
let toutesRetenues = [];
for (const [nom, m] of Object.entries(modes)) {
  const vrais = etat.travaux.filter((j) => j.origine === m.origine && j.type === "refus")
    .map((j) => Number(j.app_affaire_id)).sort((a, b) => a - b);
  const sans = LOT.trier(m.dossiers, parDossier, new Set(), new Map(), { source: nom, dire: muet });
  const avec = LOT.trier(m.dossiers, parDossier, new Set(), ventes, { source: nom, dire: muet });
  const S = ids(sans.aPoser), A = ids(avec.aPoser);
  const setV = new Set(vrais), setS = new Set(S), setA = new Set(A);
  const enTrop = S.filter((x) => !setV.has(x)), manquent = vrais.filter((x) => !setS.has(x));
  console.log(`   ${nom} : ${m.dossiers.length} dossiers ; rejeu SANS la garde ${S.length} refus ; `
    + `le lot en a VRAIMENT pose ${vrais.length} ; en trop ${enTrop.length}, manquent ${manquent.length}`);
  if (enTrop.length || manquent.length) console.log(`      en trop ${JSON.stringify(enTrop)} . manquent ${JSON.stringify(manquent)}`);
  juger(`7a ${nom} : SANS la garde, le rejeu retrouve EXACTEMENT les refus du 11/11`, vrais, S);
  const retenues = S.filter((x) => !setA.has(x));
  juger(`7c ${nom} : rien d autre ne bouge (avec = sans moins les retenues)`,
        S.filter((x) => !retenues.includes(x)), A);
  console.log(`   ${nom} : AVEC la garde, ${retenues.length} retenue(s) -- dont ${retenues.filter((x) => ses17.has(x)).length}`
    + ` de tes 17, ${retenues.filter((x) => reacceptees.has(x)).length} des 19 reacceptees, `
    + `${retenues.filter((x) => !ses17.has(x) && !reacceptees.has(x)).length} autre(s)`);
  toutesRetenues = toutesRetenues.concat(retenues.map((x) => ({ x, nom, bien: (lignes.find((t) => t.app_affaire_id === x) || {}).hektor_annonce_id })));
}
const R = toutesRetenues.map((r) => r.x).sort((a, b) => a - b);
juger("7b ⭐ AVEC la garde, les retenues = TES 17 + les 19 deja reacceptees, et AUCUNE autre",
      [...new Set([...ses17, ...reacceptees])].sort((a, b) => a - b), R);
juger("7b' parmi les offres RESTEES REFUSEES, elle retient EXACTEMENT tes 17",
      [...ses17].sort((a, b) => a - b), R.filter((x) => !reacceptees.has(x)));
juger("7b'' et chacune sur LE BIEN que tu as ecrit",
      SES_17.slice().sort(), toutesRetenues.filter((r) => ses17.has(r.x)).map((r) => `${r.x}/${r.bien}`).sort());
juger("7b''' 13 en « cascade », 4 en « table » (tes chiffres)", [13, 4],
      [toutesRetenues.filter((r) => ses17.has(r.x) && r.nom === "cascade").length,
       toutesRetenues.filter((r) => ses17.has(r.x) && r.nom === "table").length]);

console.log("");
console.log(verts + "/" + (verts + rouges.length) + " verts");
if (rouges.length) { console.log("ROUGES : " + rouges.join(" . ")); process.exit(1); }
