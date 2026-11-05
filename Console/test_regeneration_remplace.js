// A.2 LOT 6b P5 -- « CORRIGER LE MANDAT » : la regeneration MARQUE l'ancien PDF « remplace, jamais envoye »,
// elle ne l'efface pas ; un PDF remplace ne part plus en signature ; le nouveau PDF garde ce qu'il imprime
// (pour « ce qui a change »).                                                                   05/11/2026
// Sur LE CODE REEL du worker (enregistrerMandatChezNous entier, decoupe, doublures) : n'appelle rien.
//     node Console/test_regeneration_remplace.js   (0 = vert · 1 = un echec · 2 = pas pu mesurer)
// ⭐ TEMOIN INVERSE : le worker d'avant P5 recoit le meme travail et NE marque RIEN (l'essai sait voir un manque).
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
const racine = path.join(__dirname, "..");
const git = (args) => execFileSync("git", args, { cwd: racine, encoding: "utf8", maxBuffer: 128 * 1024 * 1024 });
const srcNeuf = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
let srcAvant;
try {
  const introduit = git(["log", "--format=%H", "-S", "async function marquerDocumentRemplace(", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }

const tranche = (src, d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n}", i) + 2); };
const ligne = (src, d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n", i) + 1); };

const ANCIEN = "aaaaaaaa-0000-4000-8000-0000000000p5";
const DOSSIER = 9000005;
const photo = { version: 1, valide: true, problemes: [], mandants: [{ rang: 1, nom: "DUPOND", prenom: "Jean" }] };
const ancienDoc = (meta = {}, extra = {}) => ({ id: ANCIEN, app_dossier_id: DOSSIER, document_name: "Mandat de vente - 24517.pdf",
  metadata_json: { cree_par_app: true, generation_job_id: "job-ancien", signataires_du_pdf: photo, ...meta }, ...extra });
const RENDU = {
  mandat: { numero: "24517", type: "Simple", date_signature: "05/11/2026", clause_particuliere: "" },
  mandants: [{ id: "detail-contact-1-603953", civilite: "M.", prenom: "Jean", nom: "DUPONT" }],
  mandants_libelle: "M. Jean DUPONT",
  bien: { titre: "Maison", adresse_complete: "12 rue des Essais 42700 Firminy", prix_vente: "199000", prix_net_vendeur: "190000", surface_habitable: "95" },
  honoraires: { montant_ttc: "9000", charge: "mandant" },
  options: { inclure_couverture: true, execution_anticipee_demandee: null },
};
const HTML = "<p>{{s1|signature|}}{{s1|mention|}}{{s2|signature|}}</p>";

function monter(src, { ancien, erreurLecture = false, statutAuPatch = null } = {}) {
  const lignes = ["const MARQUE_REFUS_ETAT = "].map((d) => ligne(src, d)).filter(Boolean);
  const blocs = ["function cleanString(", "function refusEtatYoutrust(", "function ficheDuMandantImprime(", "function photoSignatairesDuPdf(",
    "function contenuImprimeDuPdf(", "async function marquerDocumentRemplace(", "function signatairesDepuisLaPhoto(",
    "async function enregistrerMandatChezNous("].map((d) => tranche(src, d)).filter(Boolean);
  const trace = { ordre: [], postes: [], patchs: [], journal: [] };
  let base = ancien ? JSON.parse(JSON.stringify(ancien)) : null;
  const D = {
    crypto: { randomUUID: () => "nnnnnnnn-0000-4000-8000-0000000000p5" },
    STORAGE_BUCKET: "gti-documents",
    shouldKeepCloud: () => false,
    persistProvidedDocumentFile: async () => { trace.ordre.push("fichier"); return { storage_path: "annonces/70005/m.pdf" }; },
    logJob: async (_id, etape, statut, message, details) => { trace.journal.push({ etape, statut, message, details }); },
    supabaseRequest: async (chemin, options = {}) => {
      const methode = options.method || "GET";
      if (methode === "GET" && chemin.includes("generation_job_id=eq.")) return [];
      if (methode === "POST" && chemin === "app_console_document") { trace.ordre.push("nouveau"); trace.postes.push(JSON.parse(options.body)[0]); return null; }
      if (methode === "GET" && chemin.startsWith(`app_console_document?id=eq.${ANCIEN}`)) {
        trace.ordre.push("lecture_ancien");
        if (erreurLecture) throw new Error("HTTP 503 simule");
        return base ? [base] : [];
      }
      if (methode === "PATCH" && chemin.startsWith(`app_console_document?id=eq.${ANCIEN}`)) {
        trace.ordre.push("marque_ancien");
        trace.patchs.push({ chemin, corps: JSON.parse(options.body) });
        const statut = statutAuPatch !== null ? statutAuPatch : (base && base.metadata_json.signature && base.metadata_json.signature.status) || null;
        const filtreOk = chemin.includes("or=(metadata_json->signature->>status.is.null,metadata_json->signature->>status.not.in.(signed,pending))");
        if (!filtreOk || statut === "signed" || statut === "pending") return [];
        base = { ...base, ...JSON.parse(options.body) };
        return [base];
      }
      throw new Error(`appel non prevu : ${methode} ${chemin}`);
    },
  };
  // eslint-disable-next-line no-new-func
  const f = new Function(...Object.keys(D), `${lignes.join("")}\n${blocs.join("\n")}\nreturn { enregistrer: enregistrerMandatChezNous, signataires: typeof signatairesDepuisLaPhoto === "function" ? signatairesDepuisLaPhoto : null, contenu: typeof contenuImprimeDuPdf === "function" ? contenuImprimeDuPdf : null };`)(...Object.values(D));
  return { ...f, trace, base: () => base };
}

const job = { id: "job-regen" };
const dossier = { app_dossier_id: DOSSIER, hektor_annonce_id: "70005" };
const charge = (extra = {}) => ({ html: HTML, render_payload: RENDU, ...extra });
const regen = async (m, extra) => m.enregistrer(job, dossier, charge(extra), "Mandat de vente - 24517", "Mandat de vente - 24517.pdf", Buffer.from("%PDF"));

(async () => {
  try {
    controle("(0) LA PREUVE D'ABORD : la marque est dans le worker du travail", srcNeuf.includes("async function marquerDocumentRemplace("));
    controle("(0) …et PAS dans la version d'avant (sinon le temoin ne temoigne de rien)", !srcAvant.includes("async function marquerDocumentRemplace("));

    // 1. Le chemin nominal
    {
      const m = monter(srcNeuf, { ancien: ancienDoc() });
      const r = await regen(m, { remplace_document_id: ANCIEN });
      const neuf = m.trace.postes[0];
      const a = m.base();
      controle("1. le nouveau PDF nait, et porte le numero de celui qu'il remplace", neuf && neuf.metadata_json.remplace_document_id === ANCIEN);
      controle("1. l'ancien est MARQUE : par le nouveau, jamais envoye, avec l'heure et le travail",
        a.metadata_json.remplace && a.metadata_json.remplace.par_document_id === neuf.id && a.metadata_json.remplace.jamais_envoye === true
          && a.metadata_json.remplace.par_generation_job_id === "job-regen" && !Number.isNaN(Date.parse(a.metadata_json.remplace.le)), JSON.stringify(a.metadata_json.remplace));
      controle("1. l'ancien n'est pas efface : sa photo et ses autres cles restent telles quelles",
        JSON.stringify(a.metadata_json.signataires_du_pdf) === JSON.stringify(photo) && a.metadata_json.generation_job_id === "job-ancien" && a.document_name === "Mandat de vente - 24517.pdf");
      controle("1. ORDRE : on marque APRES la naissance du nouveau PDF et de son fichier",
        JSON.stringify(m.trace.ordre) === JSON.stringify(["nouveau", "fichier", "lecture_ancien", "marque_ancien"]), JSON.stringify(m.trace.ordre));
      controle("1. le compte rendu et le journal disent « marque »", r.remplacement && r.remplacement.marque === true
        && m.trace.journal.some((j) => j.etape === "mandat_pdf" && j.details.remplacement && j.details.remplacement.marque === true));
      const ci = neuf.metadata_json.contenu_imprime;
      controle("1. le nouveau PDF garde ce qu'il imprime (prix, honoraires, charge, mandants)",
        ci && ci.prix_vente === "199000" && ci.honoraires_ttc === "9000" && ci.honoraires_charge === "mandant" && ci.mandants_libelle === "M. Jean DUPONT"
          && ci.numero_mandat === "24517" && ci.inclure_couverture === true && ci.execution_anticipee === null, JSON.stringify(ci));
    }

    // 2. Les refus : la generation reussit TOUJOURS, l'ancien n'est pas touche, l'avertissement est ecrit
    const refus = [
      ["l'ancien est SIGNE", { ancien: ancienDoc({ signature: { status: "signed" } }) }, "signature_signed"],
      ["l'ancien est EN SIGNATURE", { ancien: ancienDoc({ signature: { status: "pending", provider: "youtrust" } }) }, "signature_pending"],
      ["l'ancien est d'un AUTRE bien", { ancien: ancienDoc({}, { app_dossier_id: 1234 }) }, "autre_bien"],
      ["l'ancien n'a pas ete fait par l'editeur", { ancien: ancienDoc({ signataires_du_pdf: undefined }) }, "pas_fait_par_l_editeur"],
      ["l'ancien est introuvable", { ancien: null }, "introuvable"],
      ["une demande est partie ENTRE la lecture et la marque", { ancien: ancienDoc(), statutAuPatch: "pending" }, "signature_partie_entre_temps"],
      ["la lecture de l'ancien plante (503)", { ancien: ancienDoc(), erreurLecture: true }, "erreur: HTTP 503 simule"],
      ["l'ancien est deja remplace par un AUTRE", { ancien: ancienDoc({ remplace: { par_document_id: "autre" } }) }, "deja_remplace"],
    ];
    for (const [nom, opts, raison] of refus) {
      const m = monter(srcNeuf, opts);
      const avant = JSON.stringify(m.base());
      const r = await regen(m, { remplace_document_id: ANCIEN });
      controle(`2. ${nom} : pas de marque (${raison}), le nouveau PDF est la quand meme, un avertissement est ecrit`,
        r.ok === true && m.trace.postes.length === 1 && r.remplacement && r.remplacement.marque === false && r.remplacement.raison === raison
          && JSON.stringify(m.base()) === (opts.statutAuPatch ? avant : avant)
          && m.trace.journal.some((j) => j.etape === "mandat_remplace" && j.statut === "warning"), JSON.stringify(r.remplacement));
    }
    {
      const m = monter(srcNeuf, { ancien: ancienDoc({ signature: { status: "cancelled" } }) });
      const r = await regen(m, { remplace_document_id: ANCIEN });
      controle("2. une signature ANNULEE ne bloque pas : l'ancien est marque", r.remplacement && r.remplacement.marque === true);
    }
    {
      const m = monter(srcNeuf, { ancien: ancienDoc({ remplace: { par_document_id: "nnnnnnnn-0000-4000-8000-0000000000p5" } }) });
      const r = await regen(m, { remplace_document_id: ANCIEN });
      controle("2. travail REJOUE : la marque deja posee par ce PDF vaut marque, sans second PATCH",
        r.remplacement && r.remplacement.marque === true && r.remplacement.deja === true && m.trace.patchs.length === 0);
    }

    // 3. Sans correction : rien d'autre ne bouge
    {
      const m = monter(srcNeuf, { ancien: ancienDoc() });
      const r = await regen(m, {});
      controle("3. une generation ordinaire ne lit ni ne marque aucun autre document",
        !m.trace.ordre.includes("lecture_ancien") && !m.trace.patchs.length && !("remplacement" in r) && !("remplace_document_id" in m.trace.postes[0].metadata_json));
      controle("3. …et sans rendu, contenu_imprime vaut null (pas d'invention)", m.contenu({ html: HTML }) === null);
    }

    // 4. L'envoi refuse un PDF remplace
    {
      const m = monter(srcNeuf, {});
      let refusEnvoi = null;
      try { m.signataires({ document_name: "Mandat X", metadata_json: { signataires_du_pdf: photo, remplace: { par_document_id: "n" } } }, []); } catch (e) { refusEnvoi = e.message; }
      let sansMarque = null;
      try { sansMarque = m.signataires({ document_name: "Mandat X", metadata_json: { signataires_du_pdf: photo } }, []); } catch (e) { sansMarque = e.message; }
      controle("4. l'envoi REFUSE un PDF remplace (refus d'etat, message clair)", /remplace par une version regeneree/.test(refusEnvoi || "") && /^\S+ /.test(refusEnvoi || ""), refusEnvoi);
      controle("4. …et accepte toujours le meme PDF sans la marque", Array.isArray(sansMarque) || (sansMarque && typeof sansMarque === "object" && !(sansMarque instanceof Error)), String(sansMarque));
    }

    // 5. TEMOIN INVERSE
    {
      const m = monter(srcAvant, { ancien: ancienDoc() });
      await regen(m, { remplace_document_id: ANCIEN });
      controle("5. TEMOIN INVERSE : le worker d'avant ne marque PAS l'ancien PDF (le meme travail ne laisse aucune trace)",
        !m.trace.patchs.length && !m.base().metadata_json.remplace);
    }
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
