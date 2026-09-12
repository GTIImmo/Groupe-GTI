/**
 * LA LECTURE DE LA PAGE DES COMMISSIONS, ÉPROUVÉE HORS LIGNE     12/09/2026
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * ⚠ IL N'APPELLE PAS HEKTOR. Il rejoue les fonctions du worker sur du HTML
 *   CAPTURÉ, comme test_lecture_console.js le fait depuis le 10/09. C'est ce qui
 *   permet de vérifier un correctif sans écrire chez eux, et sans attendre
 *   qu'une transaction réelle passe.
 *
 * CE QU'IL PROUVE, ET POURQUOI CHAQUE POINT COMPTE :
 *   ① sur une transaction SANS intervenant, on sait qui Hektor propose ;
 *   ② on lit le montant de chaque moitié SANS le recalculer ;
 *   ③ sur une transaction QUI EN PORTE DÉJÀ UN, on ne touche à rien -- c'est la
 *      garde qui empêche de remplacer le choix d'un humain par le nôtre ;
 *   ④ un montant illisible ne produit JAMAIS une valeur devinée.
 *
 *   node Console/test_commission_intervenants.js
 */
const fs = require("fs");
const path = require("path");

const DOSSIER = path.join(__dirname, "exports", "releve_assistant");
const SANS = path.join(DOSSIER, "compromis_etape_0_2_infosFinancieresCompromis_"
  + "acquereurNotaireAutresProspectsCompromis_annonceMandatCompromis_agenceInterkabCompromis_.html");

// ─── Les trois fonctions, RECOPIÉES du worker à l'identique ───
// Volontairement recopiées : un test qui importe le code qu'il éprouve ne prouve
// que sa propre cohérence. Si elles divergent, ce test doit tomber.
const COTES_COMMISSION = ["Entree", "Sortie"];

function montantMoitieCommission(html, cote) {
  const m = String(html || "").match(new RegExp(
    `id=["']header-section-amount-${cote}["'][^>]*>([^<]*)<`, "i"));
  if (!m) return "";
  const v = m[1].replace(/&nbsp;/gi, " ").replace(/[\s ]/g, "").replace(",", ".").trim();
  return /^\d+(\.\d+)?$/.test(v) ? v : "";
}

function candidatsCommission(html) {
  const out = { Entree: [], Sortie: [] };
  const re = /addIntervenantRow\s*\(\s*this\s*,\s*'([\s\S]*?)'\s*,\s*'(Entree|Sortie)'/gi;
  let m;
  while ((m = re.exec(String(html || "")))) {
    const brut = m[1].replace(/\\u([0-9a-fA-F]{4})/g, (_, x) => String.fromCharCode(parseInt(x, 16)));
    const lire = (cle) => (brut.match(new RegExp(`"${cle}"\\s*:\\s*"([^"]*)"`)) || [])[1] || "";
    const id = lire("idUser") || lire("id");
    if (!id) continue;
    if (out[m[2]].some((x) => x.id === id)) continue;
    out[m[2]].push({ id, alias: lire("alias"), type: lire("type") || "NEGO" });
  }
  return out;
}

function cotesDejaAttribuees(html) {
  const vus = new Set();
  const re = /name\s*=\s*["']intervenants(Entree|Sortie)\[(\d+)\]/gi;
  let m;
  while ((m = re.exec(String(html || "")))) vus.add(m[1]);
  return vus;
}

let echecs = 0;
function verifier(titre, reel, attendu) {
  const a = JSON.stringify(reel), b = JSON.stringify(attendu);
  const ok = a === b;
  if (!ok) echecs += 1;
  console.log(`   ${ok ? "OK  " : "ECHEC"} ${titre}`);
  if (!ok) console.log(`        attendu ${b}\n        obtenu  ${a}`);
}

if (!fs.existsSync(SANS)) {
  console.error("HTML capturé absent : relancer d'abord\n"
    + "   node Console/releve_assistant_etapes.js compromis 24933 50078");
  process.exit(1);
}
const sans = fs.readFileSync(SANS, "utf8");

console.log("① UNE TRANSACTION SANS INTERVENANT (compromis 50078, créé par l'app)");
verifier("aucun côté n'est déjà attribué", [...cotesDejaAttribuees(sans)].sort(), []);
const props = candidatsCommission(sans);
verifier("Hektor propose une personne côté entrée", props.Entree.map((x) => x.id), ["51"]);
verifier("Hektor propose une personne côté sortie", props.Sortie.map((x) => x.id), ["51"]);
verifier("et il la nomme", (props.Entree[0] || {}).alias, "Mme. Emmanuelle PEREIRA");
verifier("son type est NEGO", (props.Entree[0] || {}).type, "NEGO");
verifier("montant de la moitié entrée, LU et non calculé",
  montantMoitieCommission(sans, "Entree"), "4166.67");
verifier("montant de la moitié sortie", montantMoitieCommission(sans, "Sortie"), "4166.67");

console.log("");
console.log("② UNE PAGE QUI PORTE DÉJÀ SES INTERVENANTS (forme de la vente 23304)");
// Reconstituée à partir du relevé réel du 12/09 : c'est la FORME qui est testée.
const avec = '<input name="intervenantsEntree[115][id]" value="115">'
  + '<input name="intervenantsEntree[115][montant]" value="4166.67">'
  + '<input name="intervenantsSortie[55][id]" value="55">'
  + '<span id="header-section-amount-Entree">4 166,67</span>';
verifier("les deux côtés sont vus comme attribués",
  [...cotesDejaAttribuees(avec)].sort(), ["Entree", "Sortie"]);

console.log("");
console.log("③ CE QUI NE DOIT JAMAIS PRODUIRE DE VALEUR DEVINÉE");
verifier("page sans le montant -> vide, pas un calcul",
  montantMoitieCommission("<div>rien du tout</div>", "Entree"), "");
verifier("montant illisible -> vide",
  montantMoitieCommission('<span id="header-section-amount-Entree">n/c</span>', "Entree"), "");
verifier("aucun candidat -> listes vides",
  candidatsCommission("<div>rien</div>"), { Entree: [], Sortie: [] });

console.log("");
console.log(echecs ? `${echecs} ASSERTION(S) EN ÉCHEC` : "TOUTES LES ASSERTIONS PASSENT");
process.exit(echecs ? 1 : 0);
