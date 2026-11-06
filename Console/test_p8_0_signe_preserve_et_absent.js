// A.2 P8-0 (06/11/2026) -- G2 : UN PDF SIGNE N'EST JAMAIS REMPLACE PAR SON ORIGINAL ; G3 : UN DOCUMENT PARTI EN SIGNATURE
// N'EST PAS MARQUE « SUPPRIME CHEZ HEKTOR ».
// Sur LE CODE REEL du worker (fonctions decoupees, doublures). N'appelle rien, n'ecrit rien.
//   node Console/test_p8_0_signe_preserve_et_absent.js            -> le code du disque
//   node Console/test_p8_0_signe_preserve_et_absent.js --avant    -> TEMOIN INVERSE : le worker de HEAD (doit echouer)
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const avant = process.argv.includes("--avant");
const src = avant
  ? execSync("git show HEAD:Console/console_job_worker.js", { cwd: path.join(__dirname, ".."), encoding: "utf8", maxBuffer: 64 * 1024 * 1024 })
  : fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const tranche = (d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n}", i) + 2); };

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail || ""}`}`);
  if (!ok) echecs += 1;
}

function monterPersist(appels) {
  const bloc = tranche("async function persistConsoleDocumentFile(");
  const D = {
    safeFilename: (n, f) => String(n || f), storageSafeFilename: (n, f) => String(n || f),
    localDocumentPath: (a, id, f) => `C:/serveur/${a}/${id}/${f}`,
    isReadableFile: () => true,
    readLocalArchiveFile: (p) => { appels.push(`LIT ${p}`); return { buffer: Buffer.from("%PDF original"), mimeType: "application/pdf" }; },
    writeLocalArchiveFile: () => {}, fetchModeloDocumentPdf: async () => null, hektorFetch: async () => ({ buffer: Buffer.from("x") }),
    normalizeMimeType: () => "application/pdf", sha256Buffer: () => "S",
    uploadStorageObject: async (p) => { appels.push(`MONTE ${p}`); },
    refusDefinitifDuCoffre: () => null,
    localArchiveMetadata: () => ({}),
    STORAGE_BUCKET: "hektor-console-documents",
    supabaseRequest: async (c, o) => { appels.push(`BASE ${(o && o.method) || "GET"}`); return null; },
  };
  // eslint-disable-next-line no-new-func
  return new Function(...Object.keys(D), `${bloc}; return persistConsoleDocumentFile;`)(...Object.values(D));
}

const signeDepose = () => ({
  id: "doc-1", hektor_annonce_id: "61398", document_name: "Mandat de vente - 18420.pdf",
  storage_path: "annonces/61398/documents/doc-1/signed/Mandat de vente - 18420 - signe.pdf", storage_status: "cloud_available",
  metadata_json: {
    console_url: "https://x/doc", local_archive_path: "C:/serveur/61398/doc-1/Mandat de vente - 18420.pdf",
    signed_document: { provider: "youtrust", storage_path: "annonces/61398/documents/doc-1/signed/Mandat de vente - 18420 - signe.pdf", local_archive_path: "C:/serveur/61398/doc-1/signed_Mandat - signe.pdf", filename: "Mandat de vente - 18420 - signe.pdf" },
    signature: { provider: "youtrust", status: "signed" },
  },
});

(async () => {
  // ── G2 : la synchro ne remonte JAMAIS l'original sur le chemin du signe ──
  {
    const appels = [];
    const r = await monterPersist(appels)(null, signeDepose(), { cloud: true });
    controle("G2-1. ⭐⭐ ligne DEPOSEE signee (non modele) : RIEN n'est monte au coffre", !appels.some((a) => a.startsWith("MONTE")), appels.join(" | "));
    controle("G2-1. ...et l'original n'est meme pas relu ; le compte rendu dit « signe preserve »", !appels.some((a) => a.startsWith("LIT")) && r && r.skipped === "signe_preserve", JSON.stringify(r));
  }
  {
    const appels = [];
    const d = signeDepose(); d.metadata_json.modelo = { kind: "immosign", hektor_doc_id: "1" };
    const r = await monterPersist(appels)(null, d, { cloud: true });
    controle("G2-2. modele Hektor signe : inchange (deja preserve avant)", r && r.skipped === "signe_preserve" && !appels.some((a) => a.startsWith("MONTE")));
  }
  {
    const appels = [];
    const d = signeDepose(); delete d.metadata_json.signed_document;
    await monterPersist(appels)(null, { ...d, storage_path: "annonces/61398/documents/doc-1/Mandat.pdf" }, { cloud: true });
    controle("G2-3. TEMOIN : ligne NON signee -> rangee comme avant (relue, montee)", appels.some((a) => a.startsWith("LIT")) && appels.some((a) => a.startsWith("MONTE")), appels.join(" | "));
  }
  // ── G2 bis : « preparer au coffre » un document signe monte LE SIGNE ──
  {
    const bloc = tranche("async function monterSigneAuCoffre(");
    controle("G2-4. la preparation d'un signe existe (monterSigneAuCoffre)", Boolean(bloc));
    if (bloc) {
      const appels = [];
      const patches = [];
      const D = {
        isReadableFile: (p) => /signe/.test(String(p)),
        readLocalArchiveFile: (p) => { appels.push(`LIT ${p}`); return { buffer: Buffer.from("%PDF signe"), mimeType: "application/pdf" }; },
        storageSafeFilename: (n, f) => String(n || f), sha256Buffer: () => "S-SIGNE", STORAGE_BUCKET: "hektor-console-documents",
        uploadStorageObject: async (p, buf) => { appels.push(`MONTE ${p} ${buf.toString()}`); },
        supabaseRequest: async (c, o) => { patches.push(JSON.parse(o.body)); return null; },
      };
      // eslint-disable-next-line no-new-func
      const monter = new Function(...Object.keys(D), `${bloc}; return monterSigneAuCoffre;`)(...Object.values(D));
      const d = signeDepose();
      d.storage_path = null; d.storage_status = "local_only"; d.metadata_json.signed_document.storage_path = null;
      const r = await monter(d);
      controle("G2-5. signe resté sur le serveur seul : c'est LE SIGNE qui monte, sous signed/",
        appels.some((a) => /^MONTE annonces\/61398\/documents\/doc-1\/signed\/.* %PDF signe$/.test(a)) && !appels.some((a) => /original/.test(a)), appels.join(" | "));
      controle("G2-5. ...la colonne pointe le signe, et signed_document aussi", patches[0] && patches[0].storage_status === "cloud_available"
        && patches[0].storage_path === patches[0].metadata_json.signed_document.storage_path && /\/signed\//.test(patches[0].storage_path), JSON.stringify(patches[0]));
      let leve = null;
      const d2 = signeDepose(); d2.storage_path = null; d2.metadata_json.signed_document = { filename: "x.pdf" };
      try { await monter(d2); } catch (e) { leve = e.message; }
      controle("G2-6. TEMOIN : signe introuvable sur le serveur -> refus, et l'ORIGINAL n'est jamais monte a sa place", /introuvable/.test(String(leve)) && appels.filter((a) => a.startsWith("MONTE")).length === 1, String(leve));
    }
    controle("G2-7. le travail « preparer » aiguille un signe vers monterSigneAuCoffre",
      /if \(document\.metadata_json && document\.metadata_json\.signed_document\) \{\s*return monterSigneAuCoffre\(document\);/.test(src));
  }
  // ── G3 : un document parti en signature n'est pas « supprime chez Hektor » ──
  {
    const bloc = [tranche("function signatureProtegee("), tranche("function signatureSuivieOuSigne(")].filter(Boolean).join("\n");
    controle("G3-1. la garde existe (signatureSuivieOuSigne)", /function signatureSuivieOuSigne\(/.test(bloc));
    if (/function signatureSuivieOuSigne\(/.test(bloc)) {
      // eslint-disable-next-line no-new-func
      const f = new Function(`${bloc}; return signatureSuivieOuSigne;`)();
      const md = (m) => ({ metadata_json: m });
      controle("G3-2. procedure ImmoSign en cours / signee / refusee : protegee",
        f(md({ signature: { procedure_id: 556, status: "pending" } })) && f(md({ signature: { procedure_id: 556, status: "signed" } })) && f(md({ signature: { procedure_id: 9, status: "refused" } })));
      controle("G3-3. signe rapatrie, Youtrust, a la main : proteges",
        f(md({ signed_document: {} })) && f(md({ signature: { provider: "youtrust", status: "pending" } })) && f(md({ signature: { source: "manuscrite", status: "signed" } })));
      controle("G3-4. TEMOIN : « a envoyer » sans procedure, ou annulee, ou rien : PAS protegee (le marquage d'avant joue)",
        !f(md({ signature: { status: "to_send", procedure_id: null } })) && !f(md({ signature: { status: "cancelled", procedure_id: null } })) && !f(md({})) && !f({}));
    }
    controle("G3-5. le marquage « absent chez Hektor » appelle la garde",
      /&& !duplicateIds\.includes\(row\.id\)[^\n]*\n(?:\s*\/\/[^\n]*\n)*\s*&& !signatureSuivieOuSigne\(row\)\);/.test(src));
  }
  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT EST VERT"}${avant ? "  (version d'avant : des echecs sont ATTENDUS)" : ""}`);
  process.exit(echecs ? 1 : 0);
})().catch((e) => { console.log("ECHEC  " + (e && e.stack || e)); process.exit(2); });
