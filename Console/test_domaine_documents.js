// LE DOMAINE DES DOCUMENTS -- essai hors ligne des trois pieces.   20/10/2026
//
// CE QU'ON EPROUVE, sur LE CODE REEL (les fonctions sont decoupees dans
// console_job_worker.js et montees avec un faux Supabase -- meme technique que
// test_adoption_ligne_app.js, ecrit la veille) :
//
//   A. cheminDocument()        l'adresse sans l'hote, et rien d'invente
//   B. reconcilierParChemin()  re-cle la fiche EN PLACE : elle garde son id et son fichier
//   C. pruneDeletedDocuments() ne supprime plus ce qui est toujours la, et refuse les blocs
//
// ⚠ LA PREUVE D'ABORD : le controle (1) exige que le helper existe. S'il manque, tout le
//   reste ne prouverait rien, et l'essai sort en code 2 au lieu de se declarer vert.
// ⚠ ET LE TEMOIN INVERSE EST OBLIGATOIRE : une vraie suppression isolee doit TOUJOURS
//   passer. Un garde-fou qui bloque tout protege de tout, y compris de ce qu'on veut.
//
//     node Console/test_domaine_documents.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

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

// ── LA PREUVE D'ABORD ────────────────────────────────────────────────────────
const tCheminDocument = tranche("function cheminDocument(");
const tReconcilier = tranche("async function reconcilierParChemin(");
const tPrune = tranche("async function pruneDeletedDocuments(");
// A.2 lot 4 (26/10) : la purge appelle desormais signatureProtegee (regle R1). On AJOUTE la
// tranche, on ne restructure pas -- meme raison qu'aux ajouts du 20/10.
const tSignatureProtegee = tranche("function signatureProtegee(") || "function signatureProtegee() { return false; }";
controle("(1) LA PREUVE D'ABORD : les trois pieces sont dans le worker",
  Boolean(tCheminDocument && tReconcilier && tPrune),
  `cheminDocument=${Boolean(tCheminDocument)} reconcilier=${Boolean(tReconcilier)} prune=${Boolean(tPrune)}`);
if (!tCheminDocument || !tReconcilier || !tPrune) {
  console.log("\n⛔ Une piece manque : les controles suivants ne prouveraient RIEN. On s'arrete.");
  process.exit(2);
}

// ── le faux Supabase : il enregistre, et il applique l'unicite ───────────────
class FauxSupabase {
  constructor(lignes) { this.lignes = lignes.map((l) => ({ ...l })); this.appels = []; this.journal = []; }
  async requete(chemin, options = {}) {
    const methode = options.method || "GET";
    this.appels.push(`${methode} ${chemin.split("?")[0]}`);
    if (chemin.startsWith("app_console_job_log")) {
      this.journal.push(JSON.parse(options.body)[0]);
      return [];
    }
    if (methode === "GET") return this.lignes.map((l) => ({ ...l }));
    if (methode === "PATCH") {
      const m = chemin.match(/id=eq\.([^&]+)/);
      const id = m ? decodeURIComponent(m[1]) : null;
      const corps = JSON.parse(options.body);
      const cible = this.lignes.find((l) => l.id === id);
      if (!cible) throw new Error(`PATCH sur une ligne inconnue : ${id}`);
      // ⚠ l'unicite REELLE de la base : (annonce, source, numero)
      if (corps.hektor_document_id) {
        const collision = this.lignes.find((l) => l.id !== id
          && l.hektor_annonce_id === cible.hektor_annonce_id && l.source === cible.source
          && l.hektor_document_id === corps.hektor_document_id);
        if (collision) throw new Error("409 unicite (annonce, source, numero)");
      }
      Object.assign(cible, corps);
      return [];
    }
    if (methode === "DELETE") {
      const m = chemin.match(/id=in\.\(([^)]*)\)/);
      const ids = m ? decodeURIComponent(m[1]).split(",").map((x) => decodeURIComponent(x)) : [];
      this.supprimees = ids;
      this.lignes = this.lignes.filter((l) => !ids.includes(l.id));
      return [];
    }
    return [];
  }
}

function monterReconciliation(faux) {
  // eslint-disable-next-line no-new-func
  return new Function("supabaseRequest", "logJob",
    `${tCheminDocument}\n${tReconcilier}; return { cheminDocument, reconcilierParChemin };`)(
    (c, o) => faux.requete(c, o),
    async (jobId, step, status, message, payload) =>
      faux.requete("app_console_job_log", { method: "POST", body: JSON.stringify([{ jobId, step, status, message, payload }]) }));
}

function monterPrune(faux, htmlCharge) {
  // eslint-disable-next-line no-new-func
  return new Function("supabaseRequest", "logJob", "hektorFetch", "XMLRPC_URL",
    "buildSignatureMapFromHtml", "loadExistingDocuments",
    `${tSignatureProtegee}\n${tCheminDocument}\n${tPrune}; return pruneDeletedDocuments;`)(
    (c, o) => faux.requete(c, o),
    async (jobId, step, status, message, payload) =>
      faux.requete("app_console_job_log", { method: "POST", body: JSON.stringify([{ jobId, step, status, message, payload }]) }),
    async () => ({ text: async () => htmlCharge }),
    "http://faux/xmlrpc.php",
    () => new Map(),
    async () => ({ rows: faux.lignes.map((l) => ({ ...l })) }));
}

const ANNONCE = "62325";
const ANCIEN = "https://groupe-gti-immobilier.la-boite-immo.com";
const NOUVEAU = "https://www.gti-immobilier.fr";
const CHEMIN = "/admin/documents/biens/62325/diagnostic.pdf?flag=lbiDocumentsSecure";
const sha1 = (s) => crypto.createHash("sha1").update(s).digest("hex");
const dossier = { app_dossier_id: 1, hektor_annonce_id: ANNONCE };

function fiche(extra = {}) {
  return {
    id: "aaaa-1111", hektor_annonce_id: ANNONCE, source: "hektor_console_uploaded_private",
    hektor_document_id: sha1(ANCIEN + CHEMIN), document_name: "diagnostic.pdf",
    storage_bucket: "hektor-console-documents", storage_path: `annonces/${ANNONCE}/d/diagnostic.pdf`,
    metadata_json: { console_url: ANCIEN + CHEMIN }, ...extra,
  };
}
function entree(extra = {}) {
  return {
    hektor_document_id: sha1(NOUVEAU + CHEMIN), document_name: "diagnostic.pdf",
    source: "hektor_console_uploaded_private", console_url: NOUVEAU + CHEMIN, ...extra,
  };
}

(async () => {
  // ══ A. cheminDocument ══
  const faux0 = new FauxSupabase([]);
  const { cheminDocument } = monterReconciliation(faux0);
  controle("(2) le chemin est le MEME sous les deux domaines",
    cheminDocument(ANCIEN + CHEMIN) === cheminDocument(NOUVEAU + CHEMIN)
    && cheminDocument(ANCIEN + CHEMIN) === CHEMIN,
    `${cheminDocument(ANCIEN + CHEMIN)} vs ${cheminDocument(NOUVEAU + CHEMIN)}`);
  controle("(3) et il n'invente rien : vide, nul, texte -> null",
    cheminDocument("") === null && cheminDocument(null) === null && cheminDocument("pas une url") === null);

  // ══ B. la reconciliation ══
  const faux1 = new FauxSupabase([fiche()]);
  const { reconcilierParChemin } = monterReconciliation(faux1);
  const recles = await reconcilierParChemin({ id: "job-1" }, dossier, [entree()], faux1.lignes);
  const apres = faux1.lignes[0];
  controle("(4) ⭐ LA FICHE EST RE-CLEE : nouveau numero, nouvelle adresse",
    recles === 1 && apres.hektor_document_id === sha1(NOUVEAU + CHEMIN)
    && apres.metadata_json.console_url === NOUVEAU + CHEMIN,
    `recles=${recles} numero=${apres.hektor_document_id.slice(0, 8)}`);
  controle("(5) ⭐⭐ ET ELLE GARDE SON id ET SON FICHIER",
    apres.id === "aaaa-1111" && apres.storage_path === `annonces/${ANNONCE}/d/diagnostic.pdf`,
    `id=${apres.id} fichier=${apres.storage_path}`);
  controle("(6) le journal le DIT (un succes muet n'est pas un succes)",
    faux1.journal.some((l) => /re-cles/i.test(JSON.parse(l.body || "{}").message || l.message || "")
      || /re-cles/i.test(String(l.message || ""))),
    JSON.stringify(faux1.journal).slice(0, 120));

  // ══ B2. les refus de la reconciliation ══
  const faux2 = new FauxSupabase([fiche(), fiche({ id: "bbbb-2222", hektor_document_id: sha1(NOUVEAU + CHEMIN) })]);
  const r2 = monterReconciliation(faux2);
  const n2 = await r2.reconcilierParChemin({ id: "job-2" }, dossier, [entree()], faux2.lignes);
  controle("(7) ⚠ elle NE re-cle PAS vers un numero deja pris (sinon 409)",
    n2 === 0 && faux2.lignes[0].hektor_document_id === sha1(ANCIEN + CHEMIN), `recles=${n2}`);

  const faux3 = new FauxSupabase([fiche({ metadata_json: {} })]);
  const r3 = monterReconciliation(faux3);
  const n3 = await r3.reconcilierParChemin({ id: "job-3" }, dossier, [entree()], faux3.lignes);
  controle("(8) ⚠ une fiche sans adresse lisible n'est JAMAIS touchee", n3 === 0, `recles=${n3}`);

  const faux4 = new FauxSupabase([fiche({ source: "app" })]);
  const r4 = monterReconciliation(faux4);
  const n4 = await r4.reconcilierParChemin({ id: "job-4" }, dossier, [entree()], faux4.lignes);
  controle("(9) ⚠ et les sources qui ne sont pas hektor_console sont epargnees", n4 === 0, `recles=${n4}`);

  // ══ C. le garde-fou du prune ══
  // niveau 1 (EXACT) : le chemin est present dans la liste lue -> on ne supprime pas
  const faux5 = new FauxSupabase([fiche()]);
  const prune5 = monterPrune(faux5, "<html></html>");
  const supp5 = await prune5({ id: "job-5" }, dossier, [entree()]);
  controle("(10) ⭐⭐ NIVEAU 1 : une fiche dont le CHEMIN est toujours la n'est PAS supprimee",
    supp5 === 0 && faux5.lignes.length === 1, `supprimees=${supp5}`);

  // niveau 2 (CHIFFRE) : 4 fiches sur 4 emportees -> refus
  const quatre = [0, 1, 2, 3].map((k) => fiche({
    id: `cccc-${k}`, hektor_document_id: sha1(`${ANCIEN}/x${k}`),
    metadata_json: { console_url: `${ANCIEN}/admin/documents/biens/62325/x${k}.pdf` },
  }));
  const faux6 = new FauxSupabase(quatre);
  const prune6 = monterPrune(faux6, "<html></html>");
  const supp6 = await prune6({ id: "job-6" }, dossier, [entree({ hektor_document_id: sha1("autre"), console_url: `${NOUVEAU}/admin/documents/biens/62325/neuf.pdf` })]);
  controle("(11) ⭐ NIVEAU 2 : une suppression EN BLOC est refusee",
    supp6 === 0 && faux6.lignes.length === 4, `supprimees=${supp6}, reste ${faux6.lignes.length}`);
  controle("(12) et le refus est ECRIT au journal",
    faux6.journal.some((l) => /REFUSEE/i.test(JSON.stringify(l))),
    JSON.stringify(faux6.journal).slice(0, 140));

  // ══ ⚠ LE TEMOIN INVERSE : une vraie suppression isolee doit TOUJOURS passer ══
  const dix = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((k) => fiche({
    id: `dddd-${k}`, hektor_document_id: sha1(`${NOUVEAU}/y${k}`),
    metadata_json: { console_url: `${NOUVEAU}/admin/documents/biens/62325/y${k}.pdf` },
  }));
  const faux7 = new FauxSupabase(dix);
  const prune7 = monterPrune(faux7, "<html></html>");
  // 9 entrees sur 10 : la 10e a vraiment ete supprimee chez Hektor
  const neufEntrees = [0, 1, 2, 3, 4, 5, 6, 7, 8].map((k) =>
    entree({ hektor_document_id: sha1(`${NOUVEAU}/y${k}`), console_url: `${NOUVEAU}/admin/documents/biens/62325/y${k}.pdf` }));
  const supp7 = await prune7({ id: "job-7" }, dossier, neufEntrees);
  controle("(13) ⚠⚠ TEMOIN INVERSE : une VRAIE suppression isolee passe toujours",
    supp7 === 1 && faux7.lignes.length === 9,
    `supprimees=${supp7}, reste ${faux7.lignes.length} -- si 0, le garde-fou bloque TOUT`);

  console.log("");
  if (echecs.length) {
    console.log(`${echecs.length} controle(s) en ECHEC : ${echecs.join(", ")}`);
    process.exit(1);
  }
  console.log("Un document reconnu par son chemin garde son id et son fichier ;");
  console.log("ce qui est toujours la n'est plus supprime ; et une vraie suppression passe encore.");
})();
