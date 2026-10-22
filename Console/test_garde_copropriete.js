// LA GARDE DE LA COPROPRIETE -- essai hors ligne.                     22/10/2026
//
// LE DEFAUT (mesure le 22/10 sur 63331, trois essais) : sauver le groupe SECTEUR chez
// Hektor remet, cote serveur, copropriete = NON et copropriete_nb_lot = 0.
// LE REMEDE (console_job_worker.js, gardeCoproprieteApresSecteur) : lire la copropriete
// AVANT le secteur, la relire APRES, remettre ce que Hektor portait si elle a bouge.
//
// CE QU'ON EPROUVE, sur LE CODE REEL (fonctions decoupees dans le worker, montees avec
// un FAUX HEKTOR qui reproduit le defaut -- meme technique que test_domaine_documents.js) :
//   (2) le defaut reproduit SANS la garde : la case tombe (le faux Hektor est fidele)
//   (3) avec la garde : la case et les lots reviennent, le reste du bloc est intact
//   (4) TEMOIN INVERSE : un Hektor qui ne remet rien a zero -> aucune ecriture en plus
//   (5) une case a NON par l'utilisateur reste NON (on remet l'AVANT, on ne decide rien)
//   (6) rien a perdre (NON / 0) -> pas de relecture, pas d'ecriture
//   (7) Hektor refuse la remise -> l'erreur est LEVEE, avec le nom des champs
//   (8) lecture impossible avant -> le secteur passe quand meme, et c'est DIT
//   (9) groupe copropriete non servi -> sans objet, le secteur passe
//  (10) un autre groupe que le secteur -> la garde ne s'en mele pas
//
//     node Console/test_garde_copropriete.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const echecs = [];

function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}

function tranche(debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

function ligne(debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  return src.slice(i, src.indexOf("\n", i) + 1);
}

// ── LA PREUVE D'ABORD ────────────────────────────────────────────────────────
const morceaux = {
  constante: ligne("const GARDE_COPROPRIETE_CHAMPS = "),
  lire: tranche("async function lireCoproprieteHektor("),
  diff: tranche("function coproprieteDifferente("),
  garde: tranche("async function gardeCoproprieteApresSecteur("),
  mef: tranche("async function postHektorMefUpdate("),
  decode: tranche("function decodeHtmlEntities("),
  attr: tranche("function attrValue("),
  extract: tranche("function extractHektorFormValues("),
  options: tranche("function extractHektorFormSelectOptions("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
controle("(1) LA PREUVE D'ABORD : la garde est dans le worker, et branchee dans postHektorMefUpdate",
  !manquants.length && /lireCoproprieteHektor\(annonceId\)/.test(morceaux.mef || "") && /gardeCoproprieteApresSecteur\(/.test(morceaux.mef || ""),
  manquants.length ? `manquent : ${manquants.join(", ")}` : "postHektorMefUpdate n'appelle pas la garde");
if (manquants.length) {
  console.log("\n⛔ Une piece manque : les controles suivants ne prouveraient RIEN. On s'arrete.");
  process.exit(2);
}

// ── le faux Hektor : il garde un etat, sert les formulaires, et reproduit le defaut ──
class FauxHektor {
  constructor({ copro = { copropriete: "OUI", copropriete_nb_lot: "24", copropriete_lot: "12", copropriete_quote_part: "120" },
    remetAZero = true, refuseRemise = false, sertCopro = true, lectureCoproCassee = false } = {}) {
    this.copro = { ...copro };
    this.secteur = { immeuble: "Ancien", TRANSPORT: "" };
    this.remetAZero = remetAZero;
    this.refuseRemise = refuseRemise;
    this.sertCopro = sertCopro;
    this.lectureCoproCassee = lectureCoproCassee;
    this.appels = [];
  }
  radio(nom, valeurs, courante) {
    return valeurs.map((v) => `<input type="radio" name="${nom}" id="${nom}-${v}" value="${v}" group="copropriete" ${v === courante ? 'checked="checked"' : ""} />`).join("\n");
  }
  htmlCopro() {
    if (!this.sertCopro) return "<div></div>";
    return [
      this.radio("copropriete", ["", "OUI", "NON"], this.copro.copropriete),
      `<input type="text" name="copropriete_lot" value="${this.copro.copropriete_lot}" group="copropriete" />`,
      `<input type="text"\r\n name="copropriete_nb_lot" value="${this.copro.copropriete_nb_lot}" group="copropriete" />`,
      `<input type="text" name="copropriete_quote_part" value="${this.copro.copropriete_quote_part}" group="copropriete" />`,
    ].join("\n");
  }
  htmlSecteur() {
    return `<input type="text" name="immeuble" value="${this.secteur.immeuble}" /><input type="text" name="TRANSPORT" value="${this.secteur.TRANSPORT}" /><select name="idpays"><option value="1" selected>France</option></select>`;
  }
  htmlAgInterieur() {
    return `<input type="text" name="nbpieces" value="3" group="ag_interieur" />`;
  }
  async fetch(url, options = {}) {
    const methode = options.method || "GET";
    if (methode === "GET") {
      const q = new URL(url).searchParams;
      const groupe = q.get("group");
      this.appels.push(`GET ${groupe}`);
      if (groupe === "copropriete") {
        if (this.lectureCoproCassee) throw new Error("HTTP 503 simule");
        return { text: this.htmlCopro() };
      }
      if (groupe === "secteur") return { text: this.htmlSecteur() };
      if (groupe === "ag_interieur") return { text: this.htmlAgInterieur() };
      return { text: "" };
    }
    const corps = options.body;
    const groupe = corps.get("MEFgroup");
    this.appels.push(`POST ${groupe}`);
    if (groupe === "secteur") {
      for (const k of Object.keys(this.secteur)) if (corps.has(k)) this.secteur[k] = corps.get(k);
      if (this.remetAZero) { this.copro.copropriete = "NON"; this.copro.copropriete_nb_lot = "0"; } // LE DEFAUT
    } else if (groupe === "copropriete" && !this.refuseRemise) {
      for (const k of Object.keys(this.copro)) if (corps.has(k)) this.copro[k] = corps.get(k);
    }
    return { text: '{"result":"1"}' };
  }
}

function monter(hektor, { sansGarde = false } = {}) {
  const journal = [];
  const contexte = {
    console, URL, URLSearchParams,
    ADMIN_URL: "https://faux.hektor/admin/",
    XMLRPC_URL: "https://faux.hektor/admin/xmlrpc.php",
    hektorFetch: (url, options) => hektor.fetch(url, options),
    logJob: async (jobId, step, status, message, data) => { journal.push({ step, status, message, data }); },
    resolveHektorSelectValue: () => null,
    stripHektorSpecialWizardFields: () => {},
  };
  vm.createContext(contexte);
  let mef = morceaux.mef;
  if (sansGarde) {
    // Le worker d'AVANT : la meme fonction, sans les deux appels de la garde.
    mef = mef.replace(/coproAvant = await lireCoproprieteHektor\(annonceId\);/, "coproAvant = null;")
      .replace(/gardeCopropriete = await gardeCoproprieteApresSecteur\([^;]*\);/, "");
  }
  const code = [morceaux.constante, morceaux.decode, morceaux.attr, morceaux.extract, morceaux.options,
    morceaux.lire, morceaux.diff, morceaux.garde, mef,
    "this.postHektorMefUpdate = postHektorMefUpdate;"].join("\n");
  vm.runInContext(code, contexte);
  return { post: contexte.postHektorMefUpdate, journal };
}

const JOB = { id: "essai" };
const SECTEUR = { building: { value: "Residence Les Tilleuls", candidates: ["immeuble"] } };

(async () => {
  // (2) le defaut, sans la garde
  {
    const h = new FauxHektor();
    const { post } = monter(h, { sansGarde: true });
    await post(JOB, 63331, "secteur", "ihmChargeGroupe_Secteur", SECTEUR);
    controle("(2) SANS la garde, le faux Hektor fait tomber la case (NON / 0) -- il est fidele au defaut",
      h.copro.copropriete === "NON" && h.copro.copropriete_nb_lot === "0", JSON.stringify(h.copro));
  }

  // (3) avec la garde
  {
    const h = new FauxHektor();
    const { post, journal } = monter(h);
    const r = await post(JOB, 63331, "secteur", "ihmChargeGroupe_Secteur", SECTEUR);
    controle("(3) AVEC la garde, la case et les lots REVIENNENT (OUI / 24)",
      h.copro.copropriete === "OUI" && h.copro.copropriete_nb_lot === "24", JSON.stringify(h.copro));
    controle("(3b) le reste du bloc est intact (lot 12, quote-part 120) et le secteur est bien sauve",
      h.copro.copropriete_lot === "12" && h.copro.copropriete_quote_part === "120" && h.secteur.immeuble === "Residence Les Tilleuls",
      JSON.stringify({ copro: h.copro, secteur: h.secteur }));
    controle("(3c) le compte rendu dit « remise » et nomme les 2 champs",
      r.garde_copropriete && r.garde_copropriete.status === "remise" && r.garde_copropriete.champs.join(",") === "copropriete,copropriete_nb_lot",
      JSON.stringify(r.garde_copropriete));
    controle("(3d) le journal le DIT",
      journal.some((j) => /Garde copropriete : le secteur l'a remise a zero/.test(j.message)), journal.map((j) => j.message).join(" | "));
    controle("(3e) le geste exact : lire copro, lire+poster secteur, relire copro, lire+poster copro, verifier",
      h.appels.join(" > ") === "GET secteur > GET copropriete > POST secteur > GET copropriete > GET copropriete > POST copropriete > GET copropriete",
      h.appels.join(" > "));
  }

  // (4) TEMOIN INVERSE : Hektor ne remet rien a zero
  {
    const h = new FauxHektor({ remetAZero: false });
    const { post } = monter(h);
    const r = await post(JOB, 63331, "secteur", "ihmChargeGroupe_Secteur", SECTEUR);
    const posts = h.appels.filter((a) => a.startsWith("POST"));
    controle("(4) TEMOIN INVERSE : la case tient seule -> « intacte », UNE seule ecriture (le secteur)",
      r.garde_copropriete.status === "intacte" && posts.join(",") === "POST secteur" && h.copro.copropriete === "OUI",
      JSON.stringify({ garde: r.garde_copropriete, posts }));
  }

  // (5) une case a NON (avec des lots) par l'utilisateur reste NON
  {
    const h = new FauxHektor({ copro: { copropriete: "NON", copropriete_nb_lot: "8", copropriete_lot: "", copropriete_quote_part: "" } });
    const { post } = monter(h);
    const r = await post(JOB, 63331, "secteur", "ihmChargeGroupe_Secteur", SECTEUR);
    controle("(5) on remet L'AVANT, on ne decide rien : NON reste NON, et les 8 lots reviennent",
      h.copro.copropriete === "NON" && h.copro.copropriete_nb_lot === "8" && r.garde_copropriete.status === "remise"
        && r.garde_copropriete.champs.join(",") === "copropriete_nb_lot",
      JSON.stringify({ copro: h.copro, garde: r.garde_copropriete }));
  }

  // (6) rien a perdre
  {
    const h = new FauxHektor({ copro: { copropriete: "NON", copropriete_nb_lot: "0", copropriete_lot: "", copropriete_quote_part: "" } });
    const { post } = monter(h);
    const r = await post(JOB, 63331, "secteur", "ihmChargeGroupe_Secteur", SECTEUR);
    controle("(6) rien a perdre (NON / 0) : UNE lecture copro, aucune relecture, aucune ecriture en plus",
      r.garde_copropriete.status === "rien_a_perdre" && h.appels.filter((a) => a === "GET copropriete").length === 1
        && h.appels.filter((a) => a.startsWith("POST")).join(",") === "POST secteur",
      JSON.stringify({ garde: r.garde_copropriete, appels: h.appels }));
  }

  // (6b) case non renseignee, sans lots
  {
    const h = new FauxHektor({ copro: { copropriete: "", copropriete_nb_lot: "", copropriete_lot: "", copropriete_quote_part: "" } });
    const { post } = monter(h);
    const r = await post(JOB, 62000, "secteur", "ihmChargeGroupe_Secteur", SECTEUR);
    controle("(6b) case NON RENSEIGNEE sans lots (une maison) : rien a perdre, aucune ecriture en plus",
      r.garde_copropriete.status === "rien_a_perdre" && h.appels.filter((a) => a.startsWith("POST")).join(",") === "POST secteur",
      JSON.stringify({ garde: r.garde_copropriete, appels: h.appels }));
  }

  // (6c) case non renseignee AVEC des lots : on remet les lots, on ne touche pas la case
  {
    const h = new FauxHektor({ copro: { copropriete: "", copropriete_nb_lot: "5", copropriete_lot: "", copropriete_quote_part: "" } });
    const { post } = monter(h);
    let erreur = null;
    let r = null;
    try { r = await post(JOB, 62000, "secteur", "ihmChargeGroupe_Secteur", SECTEUR); } catch (e) { erreur = e; }
    controle("(6c) case non renseignee AVEC 5 lots : les lots reviennent, la case n'est pas « remise » a \"\", et AUCUNE erreur",
      !erreur && h.copro.copropriete_nb_lot === "5" && r.garde_copropriete.status === "remise" && r.garde_copropriete.champs.join(",") === "copropriete_nb_lot",
      erreur ? erreur.message : JSON.stringify({ copro: h.copro, garde: r.garde_copropriete }));
  }

  // (7) Hektor refuse la remise
  {
    const h = new FauxHektor({ refuseRemise: true });
    const { post } = monter(h);
    let erreur = null;
    try { await post(JOB, 63331, "secteur", "ihmChargeGroupe_Secteur", SECTEUR); } catch (e) { erreur = e; }
    controle("(7) la remise echoue -> l'erreur est LEVEE (jamais d'echec silencieux), avec les champs et les valeurs",
      erreur && /Garde copropriete/.test(erreur.message) && /copropriete, copropriete_nb_lot/.test(erreur.message) && /attendu OUI \/ 24/.test(erreur.message),
      erreur ? erreur.message : "aucune erreur levee");
  }

  // (8) lecture impossible avant
  {
    const h = new FauxHektor({ lectureCoproCassee: true });
    const { post, journal } = monter(h);
    let erreur = null;
    let r = null;
    try { r = await post(JOB, 63331, "secteur", "ihmChargeGroupe_Secteur", SECTEUR); } catch (e) { erreur = e; }
    controle("(8) lecture impossible avant : le secteur passe quand meme, et c'est DIT (journal + compte rendu)",
      !erreur && h.secteur.immeuble === "Residence Les Tilleuls" && r.garde_copropriete.status === "lecture_impossible"
        && journal.some((j) => /lecture impossible avant le secteur/.test(j.message)),
      erreur ? erreur.message : JSON.stringify(r && r.garde_copropriete));
  }

  // (9) groupe copropriete non servi
  {
    const h = new FauxHektor({ sertCopro: false });
    const { post } = monter(h);
    const r = await post(JOB, 62000, "secteur", "ihmChargeGroupe_Secteur", SECTEUR);
    controle("(9) groupe copropriete non servi (ex. une maison) : « sans objet », une seule ecriture",
      r.garde_copropriete.status === "sans_objet" && h.appels.filter((a) => a.startsWith("POST")).join(",") === "POST secteur",
      JSON.stringify({ garde: r.garde_copropriete, appels: h.appels }));
  }

  // (10) un autre groupe
  {
    const h = new FauxHektor();
    const { post } = monter(h);
    const r = await post(JOB, 63331, "ag_interieur", "ihmChargeGroupe", { room_count: { value: "4", candidates: ["nbpieces"] } });
    controle("(10) un autre groupe que le secteur : la garde ne lit rien, ne pose rien",
      !h.appels.includes("GET copropriete") && !("garde_copropriete" in r),
      JSON.stringify({ appels: h.appels, r }));
  }

  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => {
  console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`);
  process.exit(2);
});
