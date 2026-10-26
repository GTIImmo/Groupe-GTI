// A.2 LOT 4 -- LE GARDE-FOU R1 : la lecture Hektor/ImmoSign ne touche jamais un etat de
// signature ecrit par YOUTRUST ni marque « SIGNE A LA MAIN ».                    26/10/2026
// Plan : notice/PLAN_DEV_SIGNATURE_YOUTRUST_2026-10-26.md (regle R1, lot 4, D18).
//
// CE QUI EST EPROUVE, sur LE CODE REEL (fonctions decoupees dans console_job_worker.js et
// montees contre un faux Supabase -- methode de test_adoption_ligne_app.js) :
//   1. la fusion de la synchro         (upsertConsoleDocuments)
//   2. le suivi ImmoSign, ligne suivie  (reconcileSignatureStates)
//   3. le rattachement d'un signe orphelin (reconcileSignatureStates, « candidate »)
//   4. la purge                          (pruneDeletedDocuments)
// ⭐ LE TEMOIN INVERSE EST DOUBLE : chaque scene est jouee sur le code d'AVANT (git HEAD) ET
//   sur le code du travail. La ligne IMMOSIGN doit sortir IDENTIQUE des deux (rien ne change
//   pour elle) ; les lignes Youtrust / a la main doivent etre ecrasees AVANT et intactes APRES
//   (sinon le test ne prouverait rien : il faut que l'ancien code montre le defaut).
// N'appelle rien, n'ecrit rien.
//     node Console/test_garde_r1_signature.js     (0 = vert · 1 = un echec · 2 = pas pu mesurer)

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { execFileSync } = require("child_process");

const echecs = [];
function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}

const srcNeuf = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
let srcAvant;
try {
  // « AVANT » = le worker JUSTE AVANT le commit qui a introduit signatureProtegee (et non HEAD :
  // une fois le lot 4 commite, HEAD le contient -- le temoin se comparerait a lui-meme).
  const git = (args) => execFileSync("git", args, { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 128 * 1024 * 1024 });
  const introduit = git(["log", "--format=%H", "-S", "function signatureProtegee(", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) {
  console.log("ECHEC  lecture de la version d'avant (git) -- " + e.message);
  process.exit(2);
}

function tranche(src, debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

// ── le faux Supabase ──────────────────────────────────────────────────────────────
class FauxSupabase {
  constructor(lignes) { this.lignes = JSON.parse(JSON.stringify(lignes)); this.appels = []; }
  async requete(chemin, options = {}) {
    const methode = options.method || "GET";
    this.appels.push(`${methode} ${chemin.split("?")[0]}`);
    if (methode === "GET") {
      const m = chemin.match(/hektor_annonce_id=eq\.([^&]+)/);
      return JSON.parse(JSON.stringify(this.lignes.filter((l) => !m || String(l.hektor_annonce_id) === decodeURIComponent(m[1]))));
    }
    if (methode === "POST" && chemin.startsWith("app_console_document?on_conflict=")) {
      for (const neuve of JSON.parse(options.body)) {
        const cible = this.lignes.find((l) => l.hektor_annonce_id === neuve.hektor_annonce_id
          && l.source === neuve.source && l.hektor_document_id === neuve.hektor_document_id);
        if (cible) Object.assign(cible, neuve); else this.lignes.push({ ...neuve });
      }
      return null;
    }
    if (methode === "DELETE") {
      const m = chemin.match(/id=in\.\(([^)]*)\)/);
      const ids = m ? decodeURIComponent(m[1]).split(",") : [];
      this.lignes = this.lignes.filter((l) => !ids.includes(l.id));
      return null;
    }
    if (methode === "PATCH") {
      const m = chemin.match(/id=(?:eq\.([^&]+)|in\.\(([^)]*)\))/);
      const ids = m ? decodeURIComponent(m[1] || m[2]).split(",") : [];
      for (const l of this.lignes) if (ids.includes(l.id)) Object.assign(l, JSON.parse(options.body));
      return null;
    }
    throw new Error(`appel non prevu : ${methode} ${chemin}`);
  }
}

// Monte les vraies fonctions d'une version du worker contre un faux Supabase et des doublures.
function monter(src, faux, doublures) {
  const noms = [
    "function signatureProtegee(",            // absent dans la version d'avant : normal
    "function entryPriority(",
    "function dedupeDocumentEntries(",
    "async function loadExistingDocuments(",
    "function adoptExistingImmoSignRows(",
    "function adoptExistingAppRows(",
    "function cheminDocument(",
    "async function reconcilierParChemin(",
    "async function upsertConsoleDocuments(",
    "async function reconcileSignatureStates(",
    "async function pruneDeletedDocuments(",
  ];
  const blocs = noms.map((n) => tranche(src, n)).filter(Boolean);
  const manquants = noms.slice(1).filter((n) => !tranche(src, n));
  if (manquants.length) throw new Error(`fonctions introuvables : ${manquants.join(", ")}`);
  if (!tranche(src, noms[0])) blocs.unshift("function signatureProtegee() { return false; }");
  // eslint-disable-next-line no-new-func
  return new Function("supabaseRequest", "crypto", "storageSafeFilename", "logJob", "D",
    `const XMLRPC_URL = "https://hektor.invalid/xmlrpc.php";
     const { ensureHektorExecutionContext, hektorFetch, buildSignatureMapFromHtml, restoreAdminAfterSignatureRead,
             downloadSignedProcedureDocument, upsertSyntheticSignedRow } = D;
     ${blocs.join("\n")}
     return { upsertConsoleDocuments, reconcileSignatureStates, pruneDeletedDocuments };`)(
    (chemin, options) => faux.requete(chemin, options), crypto, (n, f) => String(n || f), async () => {}, doublures);
}

// ── la scene : une annonce, une ligne de chaque famille, et des voisines « normales » ──
const ANNONCE = "70001";
const dossier = { app_dossier_id: 9000001, hektor_annonce_id: ANNONCE };
const base = (id, hid, nom, signature, extra = {}) => ({
  id, app_dossier_id: 9000001, hektor_annonce_id: ANNONCE, hektor_document_id: hid,
  document_type: "Mandat", document_name: nom, source: "hektor_console_uploaded_private", visibility: "private",
  storage_bucket: "hektor-console-documents", storage_path: `annonces/${ANNONCE}/documents/${id}/${nom}.pdf`,
  storage_status: "cloud_available",
  metadata_json: { console_url: `https://h.invalid/admin/documents/biens/${ANNONCE}/${hid}.pdf?flag=lbiDocumentsSecure`, ...(signature ? { signature } : {}) },
  ...extra,
});
const L_IMM = "aaaaaaaa-0000-4000-8000-000000000001";
const L_YOU = "aaaaaaaa-0000-4000-8000-000000000002";
const L_MAN = "aaaaaaaa-0000-4000-8000-000000000003";
const SIG_YOU = { provider: "youtrust", status: "pending", progress: "1/3", sent_at: "2026-10-26T10:00:00Z", provider_request_id: "yt-1", hektor_doc_id: "D2" };
const SIG_MAN = { status: "signed", source: "manuscrite", signed_at: "2026-10-20", marked_manual_at: "2026-10-20T09:00:00", hektor_doc_id: "D3" };
const lignes = [
  base(L_IMM, "H1", "Mandat de vente - 1", { status: "pending", procedure_id: 573, hektor_doc_id: "D1", sent_at: "2026-10-01T08:00:00Z" }),
  base(L_YOU, "H2", "Mandat de vente - 2", SIG_YOU),
  base(L_MAN, "H3", "Mandat de vente - 3", SIG_MAN),
  ...Array.from({ length: 10 }, (_, i) => base(`bbbbbbbb-0000-4000-8000-00000000000${i}`, `HV${i}`, `Voisin ${i}`, null)),
];
const ligne = (faux, id) => faux.lignes.find((l) => l.id === id);
const sigDe = (faux, id) => JSON.stringify((ligne(faux, id) || {}).metadata_json?.signature ?? null);

// ── 1. LA FUSION DE LA SYNCHRO ────────────────────────────────────────────────────
// La relecture Hektor rend les 3 documents « a envoyer » (c'est ce que Hektor montre d'un PDF depose).
const entree = (l, sig) => ({
  hektor_document_id: l.hektor_document_id, document_type: l.document_type, document_name: l.document_name,
  source: l.source, visibility: "private", console_url: l.metadata_json.console_url, technical_name: `${l.hektor_document_id}.pdf`,
  transfer_name: "", hektor_uploaded_document_id: null, signature: sig,
});
const entrees = lignes.map((l, i) => entree(l, i < 3 ? { status: "to_send", hektor_doc_id: `D${i + 1}` } : null));
async function scene1(src) {
  const faux = new FauxSupabase(lignes);
  await monter(src, faux, {}).upsertConsoleDocuments(dossier, entrees, { id: "job-test" });
  return faux;
}

// ── 2 et 3. LE SUIVI IMMOSIGN ─────────────────────────────────────────────────────
// Hektor dit : D1 signe (le vrai ImmoSign), D2 et D3 « a envoyer » ; D9 signe sans ligne suivie,
// au NOM de la ligne Youtrust (le piege du rattachement « candidate »).
function doubluresSuivi(journal) {
  const carte = new Map([
    ["D1", { hektor_doc_id: "D1", status: "signed", procedure_id: 573, signed_at: "26/10/2026 à 10:00", document_name: "Mandat de vente - 1" }],
    ["D2", { hektor_doc_id: "D2", status: "to_send", document_name: "Mandat de vente - 2" }],
    ["D3", { hektor_doc_id: "D3", status: "to_send", document_name: "Mandat de vente - 3" }],
    ["D9", { hektor_doc_id: "D9", status: "signed", procedure_id: 999, signed_at: "26/10/2026 à 11:00", document_name: "Mandat de vente - 2" }],
  ]);
  return {
    ensureHektorExecutionContext: async () => false,
    hektorFetch: async () => ({ text: "<html>empreintes</html>" }),
    buildSignatureMapFromHtml: () => carte,
    restoreAdminAfterSignatureRead: async () => {},
    downloadSignedProcedureDocument: async (_d, t) => { journal.push(`telecharge:${t.id}`); },
    upsertSyntheticSignedRow: async (_d, sig) => { journal.push(`synthetique:${sig.hektor_doc_id}`); return { id: `synth-${sig.hektor_doc_id}`, metadata_json: { signature: sig } }; },
  };
}
async function scene2(src, lignesDeDepart) {
  const faux = new FauxSupabase(lignesDeDepart);
  const journal = [];
  await monter(src, faux, doubluresSuivi(journal)).reconcileSignatureStates({ id: "job-test" }, dossier, "test", "all");
  return { faux, journal };
}
// Pour la scene 3 : la ligne Youtrust n'a PAS de hektor_doc_id (cas d'un miroir neuf) -> elle
// devient « non suivie » et, de meme nom que D9 signe, l'ancien code la prenait pour candidate.
const lignesScene3 = lignes.map((l) => (l.id === L_YOU
  ? { ...l, metadata_json: { ...l.metadata_json, signature: { ...SIG_YOU, hektor_doc_id: undefined } } } : l));

// ── 4. LA PURGE ───────────────────────────────────────────────────────────────────
// Les 3 documents ont disparu de la liste Hektor (et de ses empreintes) ; les 10 voisins restent.
async function scene4(src) {
  const faux = new FauxSupabase(lignes);
  const presentes = entrees.slice(3);
  const D = { hektorFetch: async () => ({ text: "<html></html>" }), buildSignatureMapFromHtml: () => new Map() };
  const n = await monter(src, faux, D).pruneDeletedDocuments({ id: "job-test" }, dossier, presentes);
  return { faux, n };
}

(async () => {
  try {
    controle("(0) LA PREUVE D'ABORD : signatureProtegee existe dans le code du travail", Boolean(tranche(srcNeuf, "function signatureProtegee(")));
    controle("(0) …et PAS dans la version d'avant (sinon le temoin ne temoigne de rien)", !tranche(srcAvant, "function signatureProtegee("));

    const [a1, n1] = [await scene1(srcAvant), await scene1(srcNeuf)];
    controle("1. fusion -- ImmoSign : resultat IDENTIQUE avant / apres", sigDe(a1, L_IMM) === sigDe(n1, L_IMM), `${sigDe(a1, L_IMM)} / ${sigDe(n1, L_IMM)}`);
    controle("1. fusion -- ImmoSign : toujours mise a jour depuis Hektor (to_send, sent_at garde)", /"status":"to_send"/.test(sigDe(n1, L_IMM)) && /2026-10-01/.test(sigDe(n1, L_IMM)));
    controle("1. fusion -- AVANT : la ligne Youtrust etait ECRASEE (le defaut existe)", !/youtrust/.test(sigDe(a1, L_YOU)), sigDe(a1, L_YOU));
    controle("1. fusion -- APRES : la ligne Youtrust est INTACTE", sigDe(n1, L_YOU) === JSON.stringify(SIG_YOU), sigDe(n1, L_YOU));
    controle("1. fusion -- AVANT : la marque « a la main » etait EFFACEE (D18)", !/manuscrite/.test(sigDe(a1, L_MAN)), sigDe(a1, L_MAN));
    controle("1. fusion -- APRES : la marque « a la main » est INTACTE", sigDe(n1, L_MAN) === JSON.stringify(SIG_MAN), sigDe(n1, L_MAN));
    controle("1. fusion -- APRES : les autres champs de la ligne Youtrust suivent la synchro (console_url…)", ligne(n1, L_YOU).metadata_json.technical_name === "H2.pdf");

    const [a2, n2] = [await scene2(srcAvant, lignes), await scene2(srcNeuf, lignes)];
    controle("2. suivi -- ImmoSign : IDENTIQUE avant / apres (signe + telechargement)", sigDe(a2.faux, L_IMM) === sigDe(n2.faux, L_IMM)
      && a2.journal.includes(`telecharge:${L_IMM}`) && n2.journal.includes(`telecharge:${L_IMM}`), `${sigDe(n2.faux, L_IMM)} ${n2.journal}`);
    controle("2. suivi -- AVANT : la ligne Youtrust etait reecrite « to_send »", /to_send/.test(sigDe(a2.faux, L_YOU)), sigDe(a2.faux, L_YOU));
    controle("2. suivi -- APRES : la ligne Youtrust est INTACTE", sigDe(n2.faux, L_YOU) === JSON.stringify(SIG_YOU), sigDe(n2.faux, L_YOU));
    controle("2. suivi -- AVANT : la ligne « a la main » etait reecrite", /to_send/.test(sigDe(a2.faux, L_MAN)), sigDe(a2.faux, L_MAN));
    controle("2. suivi -- APRES : la ligne « a la main » est INTACTE", sigDe(n2.faux, L_MAN) === JSON.stringify(SIG_MAN), sigDe(n2.faux, L_MAN));

    const [a3, n3] = [await scene2(srcAvant, lignesScene3), await scene2(srcNeuf, lignesScene3)];
    controle("3. rattachement -- AVANT : la ligne Youtrust etait prise pour le signe ImmoSign D9", /"procedure_id":999/.test(sigDe(a3.faux, L_YOU)), sigDe(a3.faux, L_YOU));
    controle("3. rattachement -- APRES : la ligne Youtrust n'est PAS prise", /youtrust/.test(sigDe(n3.faux, L_YOU)) && !/999/.test(sigDe(n3.faux, L_YOU)), sigDe(n3.faux, L_YOU));
    controle("3. rattachement -- APRES : D9 part en ligne synthetique, comme prevu ailleurs", n3.journal.includes("synthetique:D9"), n3.journal.join(","));

    const [a4, n4] = [await scene4(srcAvant), await scene4(srcNeuf)];
    controle("4. purge -- AVANT : les lignes Youtrust ET « a la main » etaient SUPPRIMEES", !ligne(a4.faux, L_YOU) && !ligne(a4.faux, L_MAN), `n=${a4.n}`);
    controle("4. purge -- APRES : la ligne Youtrust est GARDEE", Boolean(ligne(n4.faux, L_YOU)));
    controle("4. purge -- APRES : la ligne « a la main » est GARDEE", Boolean(ligne(n4.faux, L_MAN)));
    controle("4. purge -- TEMOIN INVERSE : la ligne ImmoSign disparue est TOUJOURS purgee", !ligne(n4.faux, L_IMM) && n4.n === 1, `n=${n4.n}`);
    controle("4. purge -- TEMOIN INVERSE : les 10 voisines sont intactes", n4.faux.lignes.filter((l) => l.document_name.startsWith("Voisin")).length === 10);
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
