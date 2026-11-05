// A.2 LOT 5, L5-2 -- la mise a jour d'une demande Youtrust (youtrust_sync_signature), sur LE CODE REEL du worker (bloc
// Youtrust decoupe) contre une fausse base ET un faux Youtrust : n'appelle rien.                       05/11/2026
//     node Console/test_youtrust_sync_signature.js   (0 = vert · 1 = un echec · 2 = pas pu mesurer)
// ⭐ TEMOIN INVERSE : le worker d'avant L5-2 refuse le travail (« pas encore en service »).
const fs = require("fs");
const crypto = require("crypto");
const path = require("path");
const { execFileSync } = require("child_process");

const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
const racine = path.join(__dirname, "..");
const git = (args) => execFileSync("git", args, { cwd: racine, encoding: "utf8", maxBuffer: 128 * 1024 * 1024 });
const srcNeuf = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
let srcAvant;
try {
  const introduit = git(["log", "--format=%H", "-S", "const YOUTRUST_VERS_LANGUE_COMMUNE", "--", "Console/console_job_worker.js"]).trim().split("\n").filter(Boolean).pop();
  srcAvant = git(["show", `${introduit ? `${introduit}~1` : "HEAD"}:Console/console_job_worker.js`]);
} catch (e) { console.log("ECHEC  version d'avant illisible -- " + e.message); process.exit(2); }
// La lecture de la date par le PILOTAGE, tiree du front tel quel (D37 : il ne lit que « jj/mm/aaaa »).
const pilotage = fs.readFileSync(path.join(racine, "apps", "hektor-v1", "src", "lib", "pilotage.ts"), "utf8");
const regexPilotage = new RegExp((pilotage.match(/function dateSignature[\s\S]*?match\(\/(.+?)\/\)/) || [])[1] || "^$");
const datePilotage = (t) => { const m = String(t || "").match(regexPilotage); return m ? `${m[3]}-${m[2]}-${m[1]}` : null; };

const DOC = "dddddddd-0000-4000-8000-00000000l5s2";
const sig = (index, role, id, extra = {}) => ({ index, role, prenom: `P${index}`, nom: `N${index}`, email: `s${index}@exemple.fr`, provider_signer_id: id, status: "notified", ...extra });
const demandeDeBase = (extra = {}) => ({
  id: "req-1", provider: "youtrust", provider_request_id: "yt-sr-1", app_console_document_id: DOC, app_dossier_id: 9000005, hektor_annonce_id: "70005",
  status: "ongoing", signers: [sig(1, "mandant", "yt-s1"), sig(2, "mandant", "yt-s2"), sig(3, "mandataire", "yt-s3", { status: "initiated" })],
  done_at: null, canceled_at: null, expired_at: null, ...extra,
});

function monter({ demande = demandeDeBase(), youtrust = {}, metadata = { signature: { provider: "youtrust", status: "pending", progress: "0/3", sent_at: "2026-11-05T09:00:00.000Z" } }, avis = [], storageStatus = "cloud_available" } = {}, src = srcNeuf) {
  const debut = src.indexOf("// A.2 -- SIGNATURE YOUTRUST, LOT 4");
  const fin = src.indexOf("async function handleSyncConsoleDocuments(");
  if (debut < 0 || fin < 0) throw new Error("bloc Youtrust introuvable");
  const bloc = src.slice(src.lastIndexOf("// ═", debut), fin);
  const tranche = (d) => { const i = src.indexOf(d); return src.slice(i, src.indexOf("\n}", i) + 2); };
  const base = { demande: JSON.parse(JSON.stringify(demande)), doc: { id: DOC, hektor_annonce_id: "70005", document_name: "Mandat de vente - 24517.pdf", storage_path: "annonces/70005/documents/original.pdf", storage_status: storageStatus, file_size: 1000, metadata_json: JSON.parse(JSON.stringify(metadata)) }, avis: JSON.parse(JSON.stringify(avis)), patchsDoc: 0, journal: [], coffre: [], serveur: [], notifs: [], notifPanne: false };
  const yt = { appels: [] };
  const fauxYoutrust = {
    sandbox: true,
    lireDemande: async (id) => {
      yt.appels.push(`lireDemande:${id}`);
      if (youtrust.erreur) throw youtrust.erreur;
      return { id, status: youtrust.status || "ongoing", expiration_date: "2027-05-05T00:00:00+00:00", completed_at: youtrust.completed_at || null, signers: youtrust.signers || [] };
    },
    lireSignataire: async (_sr, id) => { yt.appels.push(`lireSignataire:${id}`); return { id, status: "signed", signed_at: (youtrust.signedAt || {})[id] || null }; },
    telechargerDocuments: async () => { yt.appels.push("telechargerDocuments"); return youtrust.signe || { buffer: Buffer.from("%PDF-1.7 mandat signe"), contentType: "application/pdf" }; },
    telechargerAuditTrail: async (_sr, id) => { yt.appels.push(`telechargerAuditTrail:${id}`); return { buffer: Buffer.from(`%PDF-1.7 preuves ${id}`), contentType: "application/pdf" }; },
    lireAuditTrail: async (_sr, id) => { yt.appels.push(`lireAuditTrail:${id}`); if (youtrust.auditEnPanne) throw new Error("HTTP 500"); return { version: 1, signer: { id, ip_address: "203.0.113.7" }, authentication: { mode: "otp_email" } }; },
  };
  async function supabaseRequest(chemin, options = {}) {
    const m = options.method || "GET";
    if (chemin.startsWith("app_setting")) return [{ value: "off" }]; // D39 : meme ETEINT, le suivi continue
    if (chemin.startsWith("app_signature_request")) {
      if (m === "GET") return [JSON.parse(JSON.stringify(base.demande))];
      if (m === "PATCH") { Object.assign(base.demande, JSON.parse(options.body)); return null; }
    }
    if (chemin.startsWith("app_signature_event")) {
      if (m === "GET") return base.avis.filter((a) => !a.processed_at).map(({ event_id, event_name, event_time, provider_signer_id }) => ({ event_id, event_name, event_time, provider_signer_id }));
      if (m === "PATCH") {
        const ids = decodeURIComponent(chemin.match(/event_id=in\.\(([^)]*)\)/)[1]).split(",").map((x) => x.replace(/"/g, ""));
        const corps = JSON.parse(options.body);
        base.avis.forEach((a) => { if (ids.includes(a.event_id) && !a.processed_at) a.processed_at = corps.processed_at; });
        return null;
      }
    }
    if (chemin.startsWith("app_notification") && m === "POST") {
      if (base.notifPanne) throw new Error("cloche indisponible");
      // l'index unique app_notif_unread_uq : (destinataire, dossier, type) tant que non lu
      const nouvelles = JSON.parse(options.body).filter((l) => !base.notifs.some((n) => n.negociateur_email === l.negociateur_email && n.app_dossier_id === l.app_dossier_id && n.type === l.type));
      base.notifs.push(...nouvelles);
      return nouvelles;
    }
    if (chemin.startsWith("app_console_document")) {
      if (m === "GET") return [JSON.parse(JSON.stringify(base.doc))];
      if (m === "PATCH") { base.patchsDoc += 1; Object.assign(base.doc, JSON.parse(options.body)); return null; }
    }
    throw new Error(`appel de base non prevu : ${m} ${chemin}`);
  }
  const doublures = {
    supabaseRequest,
    logJob: async (_id, etape, statut, message, details) => { base.journal.push({ etape, statut, message, details }); },
    safeJsonParse: (v) => (typeof v === "string" ? JSON.parse(v) : v || {}),
    MARQUE_REFUS_ETAT: "[REFUS D'ETAT]",
    STORAGE_BUCKET: "hektor-console-documents",
    loadConsoleDocumentById: async () => JSON.parse(JSON.stringify(base.doc)),
    uploadStorageObject: async (chemin, buffer, type) => { base.coffre.push({ chemin, taille: buffer.length, type }); },
    localDocumentPath: (a, d, f) => `D:/archive/annonces/${a}/documents/${d}/${f}`,
    writeLocalArchiveFile: (chemin, buffer) => { base.serveur.push({ chemin, taille: buffer.length }); },
    sha256Buffer: (b) => crypto.createHash("sha256").update(b).digest("hex"),
    require: (mod) => (mod === "./youtrust_client" ? { creerClientYoutrust: () => fauxYoutrust } : require(mod)),
  };
  // eslint-disable-next-line no-new-func
  const H = new Function(...Object.keys(doublures),
    `${tranche("function cleanString(")}\n${tranche("function safeFilename(")}\n${tranche("function storageSafeFilename(")}\n${bloc}
     return { handleYoutrustSyncSignature };`)(...Object.values(doublures));
  return { H, yt, base };
}
const job = (payload = { signature_request_id: "req-1" }) => ({ id: "job-l5s2", requested_by: null, payload_json: payload });
async function refus(promesse) { try { await promesse; return null; } catch (e) { return e.message; } }
const signersYt = (s1, s2, s3) => [{ id: "yt-s1", status: s1 }, { id: "yt-s2", status: s2 }, { id: "yt-s3", status: s3 }];

(async () => {
  try {
    controle("(0) LA PREUVE D'ABORD : la mise a jour est dans le worker du travail", srcNeuf.includes("const YOUTRUST_VERS_LANGUE_COMMUNE"));
    controle("(0) …et PAS dans la version d'avant", !srcAvant.includes("const YOUTRUST_VERS_LANGUE_COMMUNE"));
    controle("(0) la lecture du pilotage a ete trouvee dans le front (sinon les controles de date ne prouvent rien)", regexPilotage.source.includes("\\d{2}"), regexPilotage.source);

    // 1. Un mandant a signe
    {
      const m = monter({ youtrust: { status: "ongoing", signers: signersYt("signed", "notified", "initiated"), signedAt: { "yt-s1": "2026-11-05T10:51:00+00:00" } },
        avis: [{ event_id: "e1", event_name: "signer.notified", event_time: "2026-11-05T09:00:03Z" }, { event_id: "e2", event_name: "signer.done", event_time: "2026-11-05T10:51:02Z" }] });
      const r = await m.H.handleYoutrustSyncSignature(job());
      const s1 = m.base.demande.signers[0];
      const sg = m.base.doc.metadata_json.signature;
      controle("1. un mandant signe : la table porte SON statut et SON heure (lue une fois sur le signataire)",
        s1.status === "signed" && s1.signed_at === "2026-11-05T10:51:00+00:00" && m.base.demande.signers[1].status === "notified" && m.base.demande.status === "ongoing", JSON.stringify(m.base.demande.signers));
      controle("1. le miroir : « en attente 1/3 », fournisseur youtrust, sent_at d'origine GARDE (le fil du cockpit le lit)",
        sg.status === "pending" && sg.progress === "1/3" && sg.provider === "youtrust" && sg.sent_at === "2026-11-05T09:00:00.000Z" && !sg.signed_at, JSON.stringify(sg));
      controle("1. les avis vus sont marques traites, et last_event_at = le plus recent",
        m.base.avis.every((a) => a.processed_at) && m.base.demande.last_event_at === "2026-11-05T10:51:02Z" && r.avis_traites === 2, JSON.stringify(m.base.avis));
      controle("1. les transitions sont rendues (pour L5-4) : 0 → 1 signe, mandants pas tous signes",
        r.transitions.signes_avant === 0 && r.transitions.signes_apres === 1 && r.transitions.mandants_tous_signes === false);
      controle("1. ⛔ D39 : interrupteur ETEINT, le suivi a quand meme tourne", r.status === "synced");
    }
    // 2. Tout est signe
    {
      const m = monter({ demande: demandeDeBase({ signers: [sig(1, "mandant", "yt-s1", { status: "signed", signed_at: "2026-11-05T10:51:00Z" }), sig(2, "mandant", "yt-s2", { status: "signed", signed_at: "2026-11-05T11:02:00Z" }), sig(3, "mandataire", "yt-s3", { status: "notified" })] }),
        youtrust: { status: "done", completed_at: "2026-11-05T09:52:00+00:00", signers: signersYt("signed", "signed", "signed"), signedAt: { "yt-s3": "2026-11-05T09:52:00+00:00" } } });
      const r = await m.H.handleYoutrustSyncSignature(job());
      const sg = m.base.doc.metadata_json.signature;
      controle("2. tout signe : « signed », 3/3, done_at = l'heure de Youtrust", sg.status === "signed" && sg.progress === "3/3" && m.base.demande.done_at === "2026-11-05T09:52:00+00:00", JSON.stringify(sg));
      controle("2. ⛔ D37 : signed_at ecrit COMME IMMOSIGN, heure de Paris (« 05/11/2026 à 10:52 »), l'ISO a cote", sg.signed_at === "05/11/2026 à 10:52" && sg.signed_at_iso === "2026-11-05T09:52:00+00:00", sg.signed_at);
      controle("2. ⛔ D37 : le PILOTAGE (sa vraie regex) lit cette date : 2026-11-05", datePilotage(sg.signed_at) === "2026-11-05", String(datePilotage(sg.signed_at)));
      controle("2. les heures deja connues ne sont pas relues (seul le negociateur l'est)", m.yt.appels.filter((a) => a.startsWith("lireSignataire")).join(",") === "lireSignataire:yt-s3", m.yt.appels.join(","));
      controle("2. transitions : mandants tous signes, statut ongoing → done", r.transitions.mandants_tous_signes === true && r.transitions.statut_apres === "done");
      // rejoue : idempotent
      const doneAvant = m.base.demande.done_at;
      const appelsAvant = m.yt.appels.length;
      const r2 = await m.H.handleYoutrustSyncSignature(job());
      controle("2. REJOUE : meme etat, done_at inchange, aucune heure relue", r2.status === "synced" && m.base.demande.done_at === doneAvant
        && m.yt.appels.slice(appelsAvant).every((a) => !a.startsWith("lireSignataire")) && m.base.doc.metadata_json.signature.signed_at === "05/11/2026 à 10:52");
    }
    // 3. Annulee, expiree
    {
      const m = monter({ youtrust: { status: "canceled", signers: signersYt("notified", "notified", "initiated") } });
      await m.H.handleYoutrustSyncSignature(job());
      const sg = m.base.doc.metadata_json.signature;
      controle("3. annulee chez Youtrust : « cancelled », date facon ImmoSign + ISO, canceled_at pose", sg.status === "cancelled" && /^\d{2}\/\d{2}\/\d{4} à \d{2}:\d{2}$/.test(sg.cancelled_at) && m.base.demande.canceled_at, JSON.stringify(sg));
      const e = monter({ youtrust: { status: "expired", signers: signersYt("signed", "notified", "initiated") } });
      await e.H.handleYoutrustSyncSignature(job());
      controle("3. expiree : « expired » (mot neuf du lot 3), 1/3 garde, expired_at pose", e.base.doc.metadata_json.signature.status === "expired" && e.base.doc.metadata_json.signature.progress === "1/3" && e.base.demande.expired_at);
    }
    // 4. Les gardes
    {
      const m = monter({ metadata: { signature: { provider: "youtrust", status: "signed", source: "manuscrite", signed_at: "2026-11-05" } }, youtrust: { status: "ongoing", signers: signersYt("notified", "notified", "initiated") } });
      const r = await m.H.handleYoutrustSyncSignature(job());
      controle("4. ⛔ D18 : un document « signe a la main » garde sa marque (miroir NON reecrit), la table, elle, est a jour",
        r.miroir === "signe_a_la_main_garde" && m.base.patchsDoc === 0 && m.base.doc.metadata_json.signature.source === "manuscrite" && m.base.demande.last_synced_at, JSON.stringify(r));
      const i = monter({ metadata: { signature: { provider: "immosign", status: "pending", procedure_id: 55 } }, youtrust: { status: "done", signers: signersYt("signed", "signed", "signed") } });
      const ri = await i.H.handleYoutrustSyncSignature(job());
      controle("4. ⛔ R1 : un document d'un AUTRE fournisseur n'est pas touche", ri.miroir === "autre_fournisseur" && i.base.patchsDoc === 0 && i.base.doc.metadata_json.signature.procedure_id === 55);
      const j = monter({ demande: demandeDeBase({ provider_request_id: null, status: "failed" }) });
      const rj = await j.H.handleYoutrustSyncSignature(job());
      controle("4. une demande jamais partie : rien a relire, Youtrust jamais appele", rj.status === "jamais_envoyee" && j.yt.appels.length === 0);
      const err = Object.assign(new Error("Youtrust GET -> HTTP 404"), { status: 404 });
      const k = monter({ youtrust: { erreur: err } });
      const rk = await refus(k.H.handleYoutrustSyncSignature(job()));
      controle("4. demande disparue chez Youtrust (404) : REFUS D'ETAT, et l'erreur est ecrite sur la demande", /REFUS D'ETAT/.test(rk || "") && /404/.test(k.base.demande.erreur || ""), rk);
      const p = monter({ youtrust: { erreur: Object.assign(new Error("HTTP 503"), { status: 503 }) } });
      const rp = await refus(p.H.handleYoutrustSyncSignature(job()));
      controle("4. Youtrust en panne (503) : une erreur ORDINAIRE (le travail sera rejoue), rien ecrit", rp && !/REFUS D'ETAT/.test(rp) && p.base.patchsDoc === 0);
      const sans = monter();
      const rs = await refus(sans.H.handleYoutrustSyncSignature(job({})));
      controle("4. sans numero de demande : refus d'etat", /REFUS D'ETAT/.test(rs || ""));
    }
    // 6. L5-3 : le signe et les preuves
    const toutSigne = () => ({ demande: demandeDeBase({ signers: [sig(1, "mandant", "yt-s1", { status: "signed", signed_at: "2026-11-05T10:51:00Z" }), sig(2, "mandant", "yt-s2", { status: "signed", signed_at: "2026-11-05T11:02:00Z" }), sig(3, "mandataire", "yt-s3", { status: "signed", signed_at: "2026-11-05T11:10:00Z" })] }),
      youtrust: { status: "done", completed_at: "2026-11-05T11:10:00+00:00", signers: signersYt("signed", "signed", "signed") } });
    {
      const m = monter({ ...toutSigne(), avis: [{ event_id: "e9", event_name: "signature_request.done", event_time: "2026-11-05T11:10:02Z" }] });
      const r = await m.H.handleYoutrustSyncSignature(job());
      const d = m.base.doc;
      const sd = d.metadata_json.signed_document || {};
      const attendu = crypto.createHash("sha256").update(Buffer.from("%PDF-1.7 mandat signe")).digest("hex");
      controle("6. a `done` : le PDF signe est range sous signed/ AU COFFRE et sur le serveur, et la colonne storage_path pointe vers lui",
        m.base.coffre.some((c) => /\/documents\/[^/]+\/signed\/Mandat de vente - 24517 - signe\.pdf$/.test(c.chemin) && c.type === "application/pdf")
          && d.storage_path === sd.storage_path && d.storage_status === "cloud_available" && d.file_size === sd.size && m.base.serveur.length === 4, JSON.stringify({ coffre: m.base.coffre, sp: d.storage_path }));
      controle("6. signed_document : fournisseur youtrust, empreinte JUSTE, date facon ImmoSign", sd.provider === "youtrust" && sd.sha256 === attendu && sd.signed_at === "05/11/2026 à 12:10", JSON.stringify(sd));
      controle("6. une preuve PDF par signataire (3) sous proofs/, et leurs preuves JSON dans la table",
        m.base.coffre.filter((c) => /\/proofs\/preuves-\d-(mandant|mandataire)\.pdf$/.test(c.chemin)).length === 3
          && m.base.demande.proofs.length === 3 && m.base.demande.proofs[0].audit.signer.ip_address === "203.0.113.7" && sd.preuves.length === 3, JSON.stringify(m.base.demande.proofs && m.base.demande.proofs.map((p) => p.storage_path)));
      controle("6. l'ORIGINAL n'est jamais ecrase (aucun envoi a son chemin) ; signed_storage_path pose", !m.base.coffre.some((c) => c.chemin === "annonces/70005/documents/original.pdf") && m.base.demande.signed_storage_path === sd.storage_path);
      controle("6. le compte rendu le dit, et l'avis est traite APRES le rangement", r.signe && r.signe.preuves === 3 && r.signe.au_coffre === true && m.base.avis[0].processed_at);
      const appels = m.yt.appels.length;
      const r2 = await m.H.handleYoutrustSyncSignature(job());
      controle("6. REJOUE : rien n'est retelecharge (une seule fois)", !m.yt.appels.slice(appels).some((a) => /^telecharger/.test(a)) && !r2.signe, m.yt.appels.slice(appels).join(","));
    }
    {
      const m = monter({ ...toutSigne(), storageStatus: "local_only" });
      await m.H.handleYoutrustSyncSignature(job());
      const sd = m.base.doc.metadata_json.signed_document || {};
      controle("7. ⛔ regle de stockage : original hors coffre → rien au coffre, le signe et les preuves sur le serveur, la colonne storage_path INCHANGEE",
        m.base.coffre.length === 0 && m.base.serveur.length === 4 && m.base.doc.storage_path === "annonces/70005/documents/original.pdf" && sd.storage_path === null && sd.local_archive_path && m.base.demande.signed_storage_path === sd.local_archive_path, JSON.stringify(sd));
    }
    {
      const zip = { buffer: Buffer.from([0x50, 0x4b, 0x03, 0x04, 0x7a]), contentType: "application/zip" };
      const m = monter({ ...toutSigne(), youtrust: { ...toutSigne().youtrust, signe: zip }, avis: [{ event_id: "e9", event_name: "signature_request.done", event_time: "2026-11-05T11:10:02Z" }] });
      const rz = await refus(m.H.handleYoutrustSyncSignature(job()));
      controle("8. Youtrust rend un ZIP : erreur ordinaire (rejouee), RIEN range, l'avis reste « a traiter »",
        /autre chose qu'un PDF/.test(rz || "") && !/REFUS D'ETAT/.test(rz || "") && m.base.coffre.length === 0 && !m.base.doc.metadata_json.signed_document && !m.base.demande.signed_storage_path && !m.base.avis[0].processed_at, rz);
      controle("8. …mais l'ETAT est deja a jour (« signe » 3/3) : le rangement seul reprendra", m.base.doc.metadata_json.signature.status === "signed");
    }
    {
      const m = monter({ ...toutSigne(), youtrust: { ...toutSigne().youtrust, auditEnPanne: true } });
      await m.H.handleYoutrustSyncSignature(job());
      controle("9. preuves JSON indisponibles : les PDF de preuves sont ranges quand meme, l'erreur notee par signataire",
        m.base.demande.proofs.length === 3 && m.base.demande.proofs.every((p) => p.audit && p.audit.erreur && p.storage_path));
    }
    {
      const m = monter({ ...toutSigne(), metadata: { signature: { provider: "youtrust", status: "signed", source: "manuscrite", signed_at: "2026-11-05" } } });
      await m.H.handleYoutrustSyncSignature(job());
      controle("10. ⛔ D18 : document « signe a la main » : rien n'est telecharge ni range", !m.yt.appels.some((a) => /^telecharger/.test(a)) && m.base.coffre.length === 0);
    }

    // 11. L5-4 : les quatre notifications (D38), au mandataire, sur une TRANSITION seulement
    const types = (m) => m.base.notifs.map((n) => n.type).join(",");
    {
      const m = monter({ youtrust: { status: "ongoing", signers: signersYt("signed", "notified", "initiated"), signedAt: { "yt-s1": "2026-11-05T10:51:00Z" } } });
      await m.H.handleYoutrustSyncSignature(job());
      controle("11. un mandant sur deux a signe : AUCUNE notification (pas d'etape franchie)", m.base.notifs.length === 0, types(m));
    }
    {
      const m = monter({ demande: demandeDeBase({ signers: [sig(1, "mandant", "yt-s1", { status: "signed", signed_at: "x" }), sig(2, "mandant", "yt-s2"), sig(3, "mandataire", "yt-s3", { status: "initiated" })] }),
        youtrust: { status: "ongoing", signers: signersYt("signed", "signed", "notified"), signedAt: { "yt-s2": "2026-11-05T11:02:00Z" } } });
      await m.H.handleYoutrustSyncSignature(job());
      const n = m.base.notifs[0] || {};
      controle("11. les mandants viennent TOUS de signer : « a vous de contresigner », au mandataire, sur le bien, avec la demande",
        m.base.notifs.length === 1 && n.type === "signature_a_contresigner" && n.negociateur_email === "s3@exemple.fr" && n.app_dossier_id === 9000005 && n.payload.signature_request_id === "req-1", JSON.stringify(m.base.notifs));
      await m.H.handleYoutrustSyncSignature(job());
      controle("11. REJOUE : pas de seconde notification (plus de transition)", m.base.notifs.length === 1, types(m));
    }
    {
      const m = monter({ demande: demandeDeBase({ signers: [sig(1, "mandant", "yt-s1", { status: "signed", signed_at: "x" }), sig(2, "mandant", "yt-s2", { status: "signed", signed_at: "y" }), sig(3, "mandataire", "yt-s3")] }),
        youtrust: { status: "done", signers: signersYt("signed", "signed", "signed"), signedAt: { "yt-s3": "2026-11-05T11:10:00Z" } } });
      await m.H.handleYoutrustSyncSignature(job());
      controle("12. tout signe : « mandat signe » (et pas « a contresigner », les mandants avaient deja signe)", types(m) === "signature_signee", types(m));
    }
    {
      const m = monter({ youtrust: { status: "ongoing", signers: signersYt("notified", "notified", "initiated") },
        avis: [{ event_id: "f1", event_name: "signer.notification_delivery_failed", event_time: "2026-11-05T09:01:00Z", provider_signer_id: "yt-s2" }] });
      await m.H.handleYoutrustSyncSignature(job());
      const n = m.base.notifs[0] || {};
      controle("13. e-mail non remis : « e-mail non remis », le signataire NOMME", m.base.notifs.length === 1 && n.type === "signature_incident" && /P2 N2/.test(n.body) && /non remis/.test(n.title), JSON.stringify(n));
    }
    {
      const m = monter({ youtrust: { status: "expired", signers: signersYt("signed", "notified", "initiated") } });
      await m.H.handleYoutrustSyncSignature(job());
      controle("14. expiree : « la signature a expire »", types(m) === "signature_expiree", types(m));
    }
    {
      const m = monter({ metadata: { signature: { provider: "youtrust", status: "signed", source: "manuscrite" } }, youtrust: { status: "done", signers: signersYt("signed", "signed", "signed") } });
      await m.H.handleYoutrustSyncSignature(job());
      controle("15. document « signe a la main » : aucune notification", m.base.notifs.length === 0);
    }
    {
      const m = monter({ demande: demandeDeBase({ signers: [sig(1, "mandant", "yt-s1", { status: "signed", signed_at: "x" }), sig(2, "mandant", "yt-s2", { status: "signed", signed_at: "y" }), sig(3, "mandataire", "yt-s3")] }),
        youtrust: { status: "done", signers: signersYt("signed", "signed", "signed") } });
      m.base.notifPanne = true;
      const r = await m.H.handleYoutrustSyncSignature(job());
      controle("16. la cloche en panne : la mise a jour REUSSIT quand meme, l'echec est au journal",
        r.status === "synced" && m.base.journal.some((j) => j.statut === "warning" && /Notification non posee/.test(j.message)));
    }

    // 5. TEMOIN INVERSE
    {
      const a = monter({}, srcAvant);
      const ra = await refus(a.H.handleYoutrustSyncSignature(job()));
      controle("5. TEMOIN INVERSE : le worker d'avant refuse le travail (« pas encore en service »)", /pas encore en service/.test(ra || ""), ra);
    }
  } catch (e) {
    console.log("ECHEC  le montage n'a pas pu tourner -- " + (e && e.stack ? e.stack.split("\n").slice(0, 3).join(" | ") : e));
    process.exit(2);
  }
  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
  process.exit(echecs.length ? 1 : 0);
})();
