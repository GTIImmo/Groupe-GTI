/**
 * A', B ET B2 DE LA MODIFICATION D'UNE TRANSACTION, EPROUVES HORS LIGNE   03/11/2026
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * ⚠ IL N'APPELLE PAS HEKTOR. Il decoupe les VRAIES fonctions dans le worker (meme
 *   methode que lecture_assistant.js) et les rejoue sur les pages capturees et sur
 *   le cas reel du compromis 50039 (annonce 62323), soiree du 02/11.
 *
 *   A'  commission changee -> les lignes de repartition ne sont pas repostees ;
 *       rien d'autre ne bouge dans le corps.
 *   B   en modification, seul un champ TOUCHE est une intention.
 *   B2  au rejeu, une fiche changee chez Hektor depuis le 1er essai arrete tout --
 *       sauf si elle vaut deja ce qu'on veut ecrire.
 *
 *   node Console/test_reprise_commission_temoin.js
 *
 * Audit : notice/AUDIT_PILOTAGE_GLOBAL_2026-11-02.md § 20 quater et quinquies.
 */
const fs = require("fs");
const path = require("path");
const { extraire, chargerReposeur, SOURCE } = require("./lecture_assistant");

const src = fs.readFileSync(SOURCE, "utf8");
const fonctions = ["memeValeurFormulaire", "valeursVouluesReprise", "ecartsTemoinReprise",
  "retirerLignesRepartition"].map((n) => extraire(src, n, "function")).join("\n");
const { memeValeurFormulaire, valeursVouluesReprise, ecartsTemoinReprise, retirerLignesRepartition } =
  new Function(`${fonctions}\nreturn { memeValeurFormulaire, valeursVouluesReprise, ecartsTemoinReprise, retirerLignesRepartition };`)();
const debutChamps = src.indexOf("const CHAMPS_TEMOIN_REPRISE = [");
const CHAMPS_TEMOIN_REPRISE = new Function(`${src.slice(debutChamps, src.indexOf("];", debutChamps) + 2)}\nreturn CHAMPS_TEMOIN_REPRISE;`)();
const reposer = chargerReposeur();

let ok = 0;
let ko = 0;
function verifier(nom, condition, detail) {
  if (condition) { ok += 1; console.log(`  OK  ${nom}`); }
  else { ko += 1; console.log(`  KO  ${nom}${detail ? ` -- ${detail}` : ""}`); }
}
const fixture = (f) => fs.readFileSync(path.join(__dirname, "fixtures", f), "utf8");

console.log("\nA' -- les lignes de repartition");
{
  const corps = new URLSearchParams();
  for (const [k, v] of reposer(fixture("commissions_vente_23300_2026-09-10.html")).entries()) corps.append(k, v);
  const avant = [...corps.keys()];
  const autresAvant = avant.filter((k) => !/^intervenants/.test(k));
  const retirees = retirerLignesRepartition(corps);
  verifier("la page a repartition porte 14 cases (7 par cote)", retirees.length === 14, `${retirees.length}`);
  verifier("plus aucune case intervenants* dans le corps", ![...corps.keys()].some((k) => /^intervenants/.test(k)));
  verifier("les autres cases sont intactes (unites compris)",
    JSON.stringify([...corps.keys()]) === JSON.stringify(autresAvant) && corps.get("unitesEntreePercent") === "50");
}
{
  const corps = new URLSearchParams();
  for (const [k, v] of reposer(fixture("commissions_compromis_50092_2026-09-18.html")).entries()) corps.append(k, v);
  const n = [...corps.keys()].length;
  verifier("une page SANS repartition : rien n'est retire", retirerLignesRepartition(corps).length === 0
    && [...corps.keys()].length === n);
}

console.log("\nB -- les valeurs voulues ne portent que les champs touches");
const chargeDu02 = { amount: "100000.00", sale_price: "100000.00", seller_fees: "7000", net_seller_price: "93000",
  transaction_date: "2026-08-14", signature_date: "2026-11-14", retraction_days: "10",
  champs_touches: ["seller_fees", "net_seller_price"] };
const toucheDu02 = (c) => chargeDu02.champs_touches.includes(c);
{
  const voulu = valeursVouluesReprise(chargeDu02, toucheDu02);
  verifier("le prix pre-rempli (non touche) n'est PAS voulu", voulu.prixDeVente === "" && voulu.prixPublique === "");
  verifier("les dates pre-remplies ne sont PAS voulues", voulu.dateCompromis === "" && voulu.dateSignatureActe === "");
  verifier("honoraires et net touches sont voulus", voulu.montantHonoraireEntree === "7000" && voulu.prixNetVendeur === "93000");
  const tout = valeursVouluesReprise(chargeDu02, () => true);
  verifier("sans liste (ecran d'avant) : tout est voulu, comme avant", tout.prixDeVente === "100000.00");
}

console.log("\nB2 -- le temoin de reprise");
verifier("100000.00 = 100000", memeValeurFormulaire("100000.00", "100000"));
verifier("3 333,33 = 3333.33", memeValeurFormulaire("3 333,33", "3333.33"));
verifier("14-08-2026 = 2026-08-14", memeValeurFormulaire("14-08-2026", "2026-08-14"));
verifier("95000 != 100000", !memeValeurFormulaire("95000", "100000"));
verifier("vide != 0", !memeValeurFormulaire("", "0"));
verifier("le temoin relit prix, net, honoraires et dates",
  ["prixDeVente", "prixNetVendeur", "montantHonoraireEntree", "dateCompromis"].every((c) => CHAMPS_TEMOIN_REPRISE.includes(c)));
{
  // LE CAS REEL : 1er essai 23:10, Frederic corrige chez Hektor, rejeu 23:28.
  const premier = { prixDeVente: "100000", prixNetVendeur: "7000.00", montantHonoraireEntree: "93000.00" };
  const au_rejeu = { prixDeVente: "95000", prixNetVendeur: "88000", montantHonoraireEntree: "7000" };
  const ecarts = ecartsTemoinReprise(premier, au_rejeu, valeursVouluesReprise(chargeDu02, toucheDu02));
  verifier("02/11 23:28 : le rejeu S'ARRETE (prix et net changes par un humain)",
    ecarts.length === 2 && ecarts.some((e) => e.champ === "prixDeVente") && ecarts.some((e) => e.champ === "prixNetVendeur"),
    JSON.stringify(ecarts));
  verifier("les honoraires deja a 7 000 (ce qu'on veut) ne sont pas un ecart",
    !ecarts.some((e) => e.champ === "montantHonoraireEntree"));
}
{
  // Un essai precedent a ENREGISTRE puis echoue plus loin : la fiche vaut ce qu'on veut.
  const premier = { prixDeVente: "100000", prixNetVendeur: "7000.00", montantHonoraireEntree: "93000.00" };
  const au_rejeu = { prixDeVente: "100000.00", prixNetVendeur: "93000", montantHonoraireEntree: "7000.00" };
  verifier("un essai deja enregistre n'arrete PAS le rejeu",
    ecartsTemoinReprise(premier, au_rejeu, valeursVouluesReprise(chargeDu02, toucheDu02)).length === 0);
}
{
  const premier = { prixDeVente: "100000", dateCompromis: "14-08-2026" };
  verifier("rien n'a bouge : le rejeu continue", ecartsTemoinReprise(premier, { ...premier }, {}).length === 0);
  verifier("sans temoin du 1er essai : aucun ecart invente", ecartsTemoinReprise(null, { prixDeVente: "1" }, {}).length === 0);
}

console.log(`\n${ok} OK, ${ko} KO`);
process.exit(ko ? 1 : 0);
