// A.2 LOT 6b P2 -- l'ENVOI lit les signataires dans la PHOTO du PDF (D31), jamais dans la liste de
// l'ecran ; l'ecran ne corrige que l'e-mail et le portable d'un rang (D33).              05/11/2026
// Sur LE CODE REEL du worker (bloc du lot 4 decoupe) contre une fausse base ET un FAUX Youtrust :
// n'appelle rien, ne consomme aucun credit.
//     node Console/test_envoi_lit_la_photo.js   (0 = vert · 1 = un echec · 2 = pas pu mesurer)
// ⭐ TEMOIN INVERSE : le worker d'avant P2 fait signer LES NOMS DE L'ECRAN (le trou) ; celui du travail,
//   ceux du PDF.
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
  const introduit = git(["log", "--format=%H", "-S", "function signatairesDepuisLaPhoto(", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }

const DOC = "dddddddd-0000-4000-8000-0000000000p2";
const BOITE = "frederic.gerphagnon@gti-immobilier.fr";
const mandantPhoto = (rang, extra = {}) => ({ rang, civilite: "M.", prenom: `PrenomPdf${rang}`, nom: `NOMPDF${rang}`, email: `pdf${rang}@exemple.fr`, telephone: "", hektor_contact_id: `60010${rang}`, ...extra });
const photo = (n, extra = {}) => ({ version: 1, valide: true, problemes: [], reperes_attendus: 2 * n + 1, reperes_trouves: 2 * n + 1, mandants: Array.from({ length: n }, (_, i) => mandantPhoto(i + 1)), ...extra });
const listeEcran = [
  { prenom: "Intrus", nom: "ECRAN1", email: "intrus1@exemple.fr", telephone: "" },
  { prenom: "Intrus", nom: "ECRAN2", email: "intrus2@exemple.fr", telephone: "" },
];

function monter(src, metadata, anchors) {
  const debut = src.indexOf("// A.2 -- SIGNATURE YOUTRUST, LOT 4");
  const fin = src.indexOf("async function handleSyncConsoleDocuments(");
  if (debut < 0 || fin < 0) throw new Error("bloc du lot 4 introuvable");
  const bloc = src.slice(src.lastIndexOf("// ═", debut), fin);
  const tranche = (d) => { const i = src.indexOf(d); return src.slice(i, src.indexOf("\n}", i) + 2); };
  const yt = { appels: [], signataires: [] };
  const base = { demandes: [], doc: { id: DOC, app_dossier_id: 9000001, hektor_annonce_id: "70001", document_name: "Mandat de vente - 24517", storage_path: "annonces/70001/x.pdf", metadata_json: metadata } };
  const fauxYoutrust = {
    sandbox: true,
    creerDemande: async () => { yt.appels.push("creerDemande"); return { id: "sr-1", status: "draft" }; },
    lireDemande: async () => ({ id: "sr-1", status: "draft", name: "x" }),
    supprimerBrouillon: async () => { yt.appels.push("supprimerBrouillon"); },
    ajouterDocument: async () => { yt.appels.push("ajouterDocument"); return { id: "ydoc-1", total_anchors: anchors }; },
    ajouterSignataire: async (_sr, corps) => { yt.appels.push("ajouterSignataire"); yt.signataires.push(corps); return { id: `sig-${yt.signataires.length}`, status: "initiated" }; },
    activer: async () => { yt.appels.push("activer"); return { id: "sr-1", status: "ongoing" }; },
    listerChamps: async () => yt.signataires.map((_, i) => ({ type: "signature", signer_id: `sig-${i + 1}` })),
    annuler: async () => { yt.appels.push("annuler"); return { status: "canceled" }; },
  };
  async function supabaseRequest(chemin, options = {}) {
    const m = options.method || "GET";
    if (chemin.startsWith("app_setting")) return [{ value: "on" }];
    if (chemin.startsWith("app_hektor_negotiator_agency_directory")) return [{ prenom: "Paul", nom: "NEGO", display_name: "Paul NEGO", email: BOITE, portable: "", telephone: "", is_active: true }];
    if (chemin.startsWith("app_user_profile")) return [];
    if (chemin.startsWith("app_console_document")) {
      if (m === "GET") return [JSON.parse(JSON.stringify(base.doc))];
      if (m === "PATCH") { Object.assign(base.doc, JSON.parse(options.body)); return null; }
    }
    if (chemin.startsWith("app_signature_request")) {
      if (m === "POST") { const row = { id: `req-${base.demandes.length + 1}`, ...JSON.parse(options.body) }; base.demandes.push(row); return [row]; }
      if (m === "PATCH") { const id = decodeURIComponent(chemin.match(/id=eq\.([^&]+)/)[1]); Object.assign(base.demandes.find((r) => r.id === id), JSON.parse(options.body)); return null; }
      if (m === "GET") return [];
    }
    throw new Error(`appel de base non prevu : ${m} ${chemin}`);
  }
  const doublures = {
    supabaseRequest,
    logJob: async () => {},
    safeJsonParse: (v) => (typeof v === "string" ? JSON.parse(v) : v || {}),
    downloadStorageObject: async () => ({ buffer: Buffer.from("%PDF-1.4 essai"), mimeType: "application/pdf" }),
    isReadableFile: () => false,
    readLocalArchiveFile: () => { throw new Error("pas de copie serveur"); },
    loadDossier: async () => ({ app_dossier_id: 9000001, hektor_annonce_id: "70001", commercial_id: "N-ESSAI", commercial_nom: "Paul NEGO" }),
    resolveEstimNegotiatorContact: async () => ({ nom: "Paul NEGO", email: BOITE, telephone: null }),
    MARQUE_REFUS_ETAT: "[REFUS D'ETAT]",
    require: (mod) => (mod === "./youtrust_client" ? { creerClientYoutrust: () => fauxYoutrust } : require(mod)),
  };
  // eslint-disable-next-line no-new-func
  const H = new Function(...Object.keys(doublures),
    `${tranche("function cleanString(")}\n${tranche("function safeFilename(")}\n${tranche("function storageSafeFilename(")}\n${bloc}
     return { handleYoutrustSendSignature };`)(...Object.values(doublures));
  return { H, yt, base };
}
const job = (payload) => ({ id: "job-p2", requested_by: null, payload_json: { app_console_document_id: DOC, document_kind: "mandat", numero_mandat: "24517", bien_adresse: "12 rue des Essais", ...payload } });
async function refus(promesse) { try { await promesse; return null; } catch (e) { return e.message; } }
const noms = (yt) => yt.signataires.map((s) => `${s.info.first_name} ${s.info.last_name}`);

(async () => {
  try {
    controle("(0) LA PREUVE D'ABORD : signatairesDepuisLaPhoto existe dans le code du travail", srcNeuf.includes("function signatairesDepuisLaPhoto("));
    controle("(0) …et PAS dans la version d'avant (sinon le temoin ne temoigne de rien)", !srcAvant.includes("function signatairesDepuisLaPhoto("));

    // 1. LE TROU, puis sa fermeture : l'ecran donne 2 AUTRES personnes, de meme nombre.
    const avant = monter(srcAvant, { signataires_du_pdf: photo(2) }, 5);
    await avant.H.handleYoutrustSendSignature(job({ mandants: listeEcran }));
    controle("1. TEMOIN INVERSE : le worker d'avant fait signer les noms de L'ECRAN (le trou existe)", noms(avant.yt).slice(0, 2).join(",") === "Intrus ECRAN1,Intrus ECRAN2", noms(avant.yt).join(","));
    const neuf = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    await neuf.H.handleYoutrustSendSignature(job({ mandants: listeEcran }));
    controle("1. APRES : ce sont les mandants DU PDF qui signent, dans l'ordre des cases", noms(neuf.yt).join(",") === "PrenomPdf1 NOMPDF1,PrenomPdf2 NOMPDF2,Paul NEGO", noms(neuf.yt).join(","));
    controle("1. APRES : leurs e-mails sont ceux du PDF", neuf.yt.signataires.slice(0, 2).map((s) => s.info.email).join(",") === "pdf1@exemple.fr,pdf2@exemple.fr");
    const dem = neuf.base.demandes[0];
    controle("1. APRES : notre ligne garde la fiche de chaque mandant (numero de la photo)", dem.signers.filter((s) => s.role === "mandant").map((s) => s.hektor_contact_id).join(",") === "600101,600102");

    // 2. Pas de photo, photo invalide : refus AVANT tout appel a Youtrust.
    const sans = monter(srcNeuf, { signature: { status: "to_send" } }, 5);
    const r2 = await refus(sans.H.handleYoutrustSendSignature(job({ mandants: listeEcran })));
    controle("2. PDF sans photo : REFUS D'ETAT « regenerez le mandat », Youtrust jamais appele", /REFUS D'ETAT/.test(r2 || "") && /regenerez/.test(r2 || "") && sans.yt.appels.length === 0, r2);
    const inval = monter(srcNeuf, { signataires_du_pdf: photo(2, { valide: false, problemes: ["mentions du PDF [], attendu 1..2"] }) }, 5);
    const r2b = await refus(inval.H.handleYoutrustSendSignature(job({})));
    controle("2. photo invalide : REFUS D'ETAT qui dit pourquoi, Youtrust jamais appele", /mentions du PDF/.test(r2b || "") && inval.yt.appels.length === 0, r2b);

    // 3. Les corrections de l'ecran : e-mail et portable seulement, par rang.
    const cor = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    await cor.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 2, email: "corrige2@exemple.fr", telephone: "06 12 34 56 78" }] }));
    const s2 = cor.yt.signataires[1];
    controle("3. rang 2 : l'e-mail corrige part chez Youtrust", s2.info.email === "corrige2@exemple.fr", s2.info.email);
    controle("3. rang 2 : le portable corrige donne le code par SMS (+33…)", s2.info.phone_number === "+33612345678" && s2.signature_authentication_mode === "otp_sms", JSON.stringify(s2));
    controle("3. rang 2 : le NOM reste celui du PDF", s2.info.last_name === "NOMPDF2");
    controle("3. rang 1 : intact (e-mail du PDF, code par e-mail)", cor.yt.signataires[0].info.email === "pdf1@exemple.fr" && cor.yt.signataires[0].signature_authentication_mode === "otp_email");
    controle("3. notre ligne dit ce que l'ecran a corrige (rang 2 : email, telephone)", JSON.stringify(cor.base.demandes[0].signers[1].corrige) === JSON.stringify(["email", "telephone"]));
    const nomChange = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    const r3 = await refus(nomChange.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 1, nom: "AUTRE" }] })));
    controle("3. corriger le NOM a l'envoi : REFUS « le reste est imprime », Youtrust jamais appele", /Seuls l'e-mail et le portable/.test(r3 || "") && nomChange.yt.appels.length === 0, r3);
    const horsRang = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    const r3b = await refus(horsRang.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 3, email: "x@exemple.fr" }] })));
    controle("3. corriger un rang 3 sur un PDF a 2 mandants : REFUS (pas d'ajout de signataire)", /ce PDF a 2 mandant/.test(r3b || "") && horsRang.yt.appels.length === 0, r3b);

    // 4. Un e-mail manquant dans le PDF, sans correction : refus avant Youtrust (D33 : il se complete a l'envoi).
    const sansMail = monter(srcNeuf, { signataires_du_pdf: { ...photo(2), mandants: [mandantPhoto(1), mandantPhoto(2, { email: null })] } }, 5);
    const r4 = await refus(sansMail.H.handleYoutrustSendSignature(job({})));
    controle("4. mandant 2 sans e-mail et sans correction : REFUS, Youtrust jamais appele", /mandant 2/.test(r4 || "") && /e-mail/.test(r4 || "") && sansMail.yt.appels.length === 0, r4);
    const complete = monter(srcNeuf, { signataires_du_pdf: { ...photo(2), mandants: [mandantPhoto(1), mandantPhoto(2, { email: null })] } }, 5);
    await complete.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 2, email: "complete@exemple.fr" }] }));
    controle("4. …complete a l'envoi : il part, avec l'e-mail saisi", complete.yt.signataires[1].info.email === "complete@exemple.fr");

    // 5. Le controle des reperes reste : un PDF a 3 mandants (7 reperes) avec une photo a 2 -> refus avant activation.
    const reperes = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 7);
    const r5 = await refus(reperes.H.handleYoutrustSendSignature(job({})));
    controle("5. reperes du PDF (7) differents de la photo (5) : REFUS avant activation, brouillon supprime", /repere/.test(r5 || "") && !reperes.yt.appels.includes("activer") && reperes.yt.appels.includes("supprimerBrouillon"), r5);

    // 6. A.2 (06/11/2026) : LE CODE PAR E-MAIL CHOISI A L'ENVOI, meme quand le signataire a un portable (Frederic).
    const NEGO_PORTABLE = { prenom: "Paul", nom: "NEGO", email: BOITE, telephone: "06 11 22 33 44" };
    const defaut = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    await defaut.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 1, telephone: "06 12 34 56 78" }], mandataire: NEGO_PORTABLE }));
    controle("6. PAR DEFAUT rien ne change : mandant avec portable -> SMS, negociateur avec portable -> SMS",
      defaut.yt.signataires[0].signature_authentication_mode === "otp_sms" && defaut.yt.signataires[2].signature_authentication_mode === "otp_sms",
      defaut.yt.signataires.map((s) => s.signature_authentication_mode).join(","));
    const choisi = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    await choisi.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 1, telephone: "06 12 34 56 78", code: "email" }], code_mandataire: "email", mandataire: NEGO_PORTABLE }));
    const c1 = choisi.yt.signataires[0];
    const cn = choisi.yt.signataires[2];
    controle("6. mandant 1 a un portable MAIS code choisi par e-mail -> otp_email, et le numero NE PART PAS chez Youtrust",
      c1.signature_authentication_mode === "otp_email" && !("phone_number" in c1.info), JSON.stringify(c1));
    controle("6. le negociateur aussi : code par e-mail, numero non transmis", cn.signature_authentication_mode === "otp_email" && !("phone_number" in cn.info), JSON.stringify(cn));
    controle("6. TEMOIN dans le meme envoi : le mandant 2 sans choix garde la regle (e-mail, faute de portable)", choisi.yt.signataires[1].signature_authentication_mode === "otp_email");
    const lignes = choisi.base.demandes[0].signers;
    controle("6. notre ligne garde la trace du choix (code_choisi = email) pour le mandant 1 et le negociateur, pas pour le mandant 2",
      lignes[0].code_choisi === "email" && lignes[2].code_choisi === "email" && lignes[1].code_choisi === undefined, JSON.stringify(lignes.map((s) => s.code_choisi)));
    const inconnu = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    const r6 = await refus(inconnu.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 1, code: "sms" }] })));
    controle("6. une autre valeur que « email » (ici « sms ») : REFUS clair, Youtrust jamais appele", (r6 || "").includes("Mode du code inconnu") && inconnu.yt.appels.length === 0, r6);
    const inconnuNego = monter(srcNeuf, { signataires_du_pdf: photo(2) }, 5);
    const r6b = await refus(inconnuNego.H.handleYoutrustSendSignature(job({ code_mandataire: "fax" })));
    controle("6. idem pour le negociateur : REFUS, Youtrust jamais appele", (r6b || "").includes("Mode du code inconnu pour le mandataire") && inconnuNego.yt.appels.length === 0, r6b);
    // La version d'AVANT le choix : le commit qui l'introduit, moins un (HEAD tant qu'il n'est pas commite).
    const introduitCode = git(["log", "--format=%H", "-S", "codeParEmail: c.code === \"email\"", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
    const srcHead = git(["show", `${introduitCode ? `${introduitCode}~1` : "HEAD"}:Console/console_job_worker.js`]);
    const ancien = monter(srcHead, { signataires_du_pdf: photo(2) }, 5);
    const r6c = await refus(ancien.H.handleYoutrustSendSignature(job({ corrections: [{ rang: 1, telephone: "06 12 34 56 78", code: "email" }] })));
    controle("6. TEMOIN INVERSE : le worker d'avant (HEAD) refuse la cle « code » (d'ou : redemarrer AVANT d'utiliser le choix)", (r6c || "").includes("Seuls l'e-mail et le portable"), r6c);
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
