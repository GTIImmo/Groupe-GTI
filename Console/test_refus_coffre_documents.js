// UN DOCUMENT REFUSE PAR LE COFFRE NE DOIT PLUS COULER SON ANNONCE
//                                                     15/10/2026, chantier 6 / point 6b
//
// CE QUI SE PASSAIT, mesure du 15/10 : 33 travaux `sync_console_documents` en erreur,
// dont 31 refuses par Supabase Storage -- le coffre `hektor-console-documents` porte une
// liste blanche de 10 types et REFUSE le reste (68 .odt de biens en vente, des .ods, des
// .html, un document sans extension) ainsi que tout fichier de plus de 50 Mo.
// La boucle de synchro ne tolerait que les PDF « modelo » : UN SEUL .odt faisait tomber
// TOUTE l'annonce. Ses voisins n'etaient jamais telecharges (89 PDF et 4 photos
// parfaitement normaux manquaient dans l'app pour cette seule raison), aucune empreinte
// n'etait posee, et le composeur exclut « pour toujours » une annonce en erreur.
//
// CE TEST FAIT TOURNER LES VRAIES FONCTIONS DU WORKER avec un faux disque, un faux
// Supabase et un faux Hektor. IL N'APPELLE RIEN, N'ECRIT AUCUN FICHIER.
//
// Il verifie les deux sens, comme l'exige la regle du projet :
//   · ce qui doit MAINTENANT passer (un refus definitif est garde, marque, journalise) ;
//   · et ce qui doit TOUJOURS LEVER (un accroc passager, un autre appelant) -- sans quoi
//     le correctif transformerait des pannes en silences.

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const WORKER = path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(WORKER, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function tranche(debutMarque) {
  const i = src.indexOf(debutMarque);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

// Les messages EXACTS releves dans app_console_job aujourd'hui (aucun invente).
const MSG_415 = 'Supabase Storage 400 on hektor-console-documents/annonces/40470/documents/69c4/estimationrocher.odt: {"statusCode":"415","error":"invalid_mime_type","message":"mime type application/vnd.oasis.opendocument.text is not supported","code":"InvalidMimeType"}';
const MSG_413 = 'Supabase Storage 400 on hektor-console-documents/annonces/23327/documents/7cd6/tp.pdf: {"statusCode":"413","error":"Payload too large","message":"The object exceeded the maximum allowed size","code":"EntityTooLarge"}';
const MSG_RESEAU = "fetch failed";
const MSG_SESSION = `Unexpected token '<', "<!DOCTYPE "... is not valid JSON`;
const MSG_403 = 'Supabase Storage 403 on hektor-console-documents/annonces/1/documents/2/x.pdf: {"statusCode":"403","error":"Unauthorized"}';

(async () => {
  const blocHelper = tranche("function refusDefinitifDuCoffre(");
  const blocPersist = tranche("async function persistConsoleDocumentFile(");
  const blocBoucle = tranche("async function handleSyncConsoleDocuments(");

  // ── ① LE JUGE : qui est definitif, qui est passager ──────────────────────────
  if (!blocHelper) {
    controle("(0) refusDefinitifDuCoffre est dans le worker", false, "introuvable");
  } else {
    // eslint-disable-next-line no-new-func
    const juge = new Function(`${blocHelper}; return refusDefinitifDuCoffre;`)();
    const r415 = juge(new Error(MSG_415));
    const r413 = juge(new Error(MSG_413));
    controle("(a) 415 type hors liste blanche -> refus DEFINITIF",
      r415 && r415.code === "type_refuse" && r415.http === 415, JSON.stringify(r415));
    controle("(b) 413 fichier trop gros -> refus DEFINITIF",
      r413 && r413.code === "trop_gros" && r413.http === 413, JSON.stringify(r413));
    controle("(c) ⚠ accroc reseau -> PAS un refus (il faut rejouer)",
      juge(new Error(MSG_RESEAU)) === null, "reconnu a tort");
    controle("(d) ⚠ session Hektor expiree -> PAS un refus",
      juge(new Error(MSG_SESSION)) === null, "reconnu a tort");
    controle("(e) ⚠⚠ 403 du coffre -> PAS un refus (droits/ban : on ne se taira pas)",
      juge(new Error(MSG_403)) === null, "reconnu a tort");
  }

  // ── le faux monde, partage par les epreuves qui suivent ──────────────────────
  function fauxMonde(options = {}) {
    const etat = { ecrits: [], versLeCloud: [], patches: [], journal: [], empreintes: [] };
    const doubles = {
      safeFilename: (n, f) => String(n || "").trim() || f,
      storageSafeFilename: (n, f) => String(n || "").trim() || f,
      localDocumentPath: (annonce, id, nom) => `C:/serveur/annonces/${annonce}/documents/${id}/${nom}`,
      isReadableFile: () => false,
      readLocalArchiveFile: () => { throw new Error("ne doit pas etre appele"); },
      fetchModeloDocumentPdf: async () => null,
      hektorFetch: async () => ({ buffer: Buffer.alloc(2048, 3), mimeType: options.mimeHektor || "application/pdf" }),
      writeLocalArchiveFile: (p, b) => etat.ecrits.push({ chemin: p, octets: b.length }),
      normalizeMimeType: (m) => m || "application/octet-stream",
      sha256Buffer: (b) => crypto.createHash("sha256").update(b).digest("hex"),
      localArchiveMetadata: (p) => ({ local_archive_path: p }),
      uploadStorageObject: async (p, b, m) => {
        if (options.refuser) throw new Error(options.refuser);
        etat.versLeCloud.push({ chemin: p, octets: b.length, type: m });
      },
      supabaseRequest: async (chemin, opts) => {
        etat.patches.push({ chemin, corps: JSON.parse(opts.body) });
      },
      STORAGE_BUCKET: "hektor-console-documents",
    };
    return { etat, doubles };
  }

  function fabriquerPersist(doubles) {
    // ⚠ LE JUGE EST LE VRAI : on concatene son code, on ne le double pas. Sinon
    //   l'epreuve mesurerait ma doublure, pas le worker.
    // eslint-disable-next-line no-new-func
    return new Function(...Object.keys(doubles),
      `${blocHelper}\n${blocPersist}\n; return persistConsoleDocumentFile;`)(...Object.values(doubles));
  }

  const ligneOdt = {
    id: "doc-1", hektor_annonce_id: "40470", document_name: "estimationrocher.odt",
    storage_bucket: null, storage_path: null, storage_status: "local_only",
    mime_type: null, metadata_json: { console_url: "https://hektor/doc/1" },
  };

  if (!blocPersist) {
    controle("(0b) persistConsoleDocumentFile est dans le worker", false, "introuvable");
  } else {
    // ── ② LE REFUS EST TOLERE *QUAND LA BOUCLE LE DEMANDE* ────────────────────
    {
      const { etat, doubles } = fauxMonde({ refuser: MSG_415, mimeHektor: "application/vnd.oasis.opendocument.text" });
      const persist = fabriquerPersist(doubles);
      let leve = null;
      let r = null;
      try {
        r = await persist({ hektor_annonce_id: "40470" }, ligneOdt, { cloud: true, tolererRefusCoffre: true });
      } catch (error) { leve = error; }

      controle("(f) ⭐ le travail ne tombe PLUS en erreur", leve === null, leve && leve.message);
      controle("(g) le fichier est quand meme sur NOTRE SERVEUR",
        etat.ecrits.length === 1 && etat.ecrits[0].octets === 2048, JSON.stringify(etat.ecrits));
      controle("(h) rien n'est monte au cloud", etat.versLeCloud.length === 0, JSON.stringify(etat.versLeCloud));
      const corps = etat.patches.length === 1 ? etat.patches[0].corps : null;
      controle("(i) la ligne retient local_only",
        corps && corps.storage_status === "local_only", JSON.stringify(corps));
      controle("(j) ⭐ la MARQUE DURABLE est posee (pour un rattrapage sans Hektor)",
        corps && corps.metadata_json.cloud_refuse
          && corps.metadata_json.cloud_refuse.code === "type_refuse"
          && corps.metadata_json.cloud_refuse.http === 415,
        JSON.stringify(corps && corps.metadata_json));
      controle("(k) le chemin serveur est note : la ligne n'est plus muette",
        corps && corps.metadata_json.local_archive_path === etat.ecrits[0].chemin,
        JSON.stringify(corps && corps.metadata_json));
      controle("(l) taille et empreinte enregistrees",
        corps && corps.file_size === 2048 && /^[0-9a-f]{64}$/.test(corps.sha256), JSON.stringify(corps));
      controle("(m) aucun chemin cloud n'est inscrit",
        corps && corps.storage_path === null, JSON.stringify(corps && corps.storage_path));
      controle("(n) la fonction DIT le refus a son appelant",
        r && r.cloud_refuse && r.cloud_refuse.code === "type_refuse", JSON.stringify(r));
      controle("(o) et elle ne pretend pas que le document est au cloud",
        r && r.cloud_available === false, JSON.stringify(r));
    }

    // ── ③ TEMOIN INVERSE : SANS l'option, le refus leve comme avant ───────────
    {
      const { doubles } = fauxMonde({ refuser: MSG_415 });
      const persist = fabriquerPersist(doubles);
      let leve = null;
      try {
        await persist({ hektor_annonce_id: "40470" }, ligneOdt, { cloud: true });
      } catch (error) { leve = error; }
      controle("(p) ⚠⚠ TEMOIN INVERSE : sans l'option, le refus LEVE (prepare_document_cloud, l'humain qui clique, ne mentira pas)",
        leve !== null && String(leve.message).includes("InvalidMimeType"), "le refus a ete avale");
    }

    // ── ④ UN ACCROC PASSAGER LEVE, MEME AVEC L'OPTION ─────────────────────────
    for (const [nom, msg] of [["403 du coffre", MSG_403], ["reseau", MSG_RESEAU]]) {
      const { doubles } = fauxMonde({ refuser: msg });
      const persist = fabriquerPersist(doubles);
      let leve = null;
      try {
        await persist({ hektor_annonce_id: "40470" }, ligneOdt, { cloud: true, tolererRefusCoffre: true });
      } catch (error) { leve = error; }
      controle(`(q) ⚠ ${nom} : LEVE quand meme -> le travail se rejoue`, leve !== null, "avale a tort");
    }

    // ── ⑤ LA MONTEE QUI REUSSIT N'A PAS CHANGE, ET LA MARQUE S'EFFACE ─────────
    {
      const { etat, doubles } = fauxMonde({});
      const persist = fabriquerPersist(doubles);
      const ligneGuerie = { ...ligneOdt, metadata_json: {
        console_url: "https://hektor/doc/1",
        cloud_refuse: { code: "type_refuse", http: 415, le: "2026-10-15T09:00:00.000Z" },
      } };
      const r = await persist({ hektor_annonce_id: "40470" }, ligneGuerie, { cloud: true, tolererRefusCoffre: true });
      const corps = etat.patches[0].corps;
      controle("(r) montee reussie -> cloud_available, comme avant",
        corps.storage_status === "cloud_available" && r.cloud_available === true, JSON.stringify(corps));
      controle("(s) ⭐ la vieille marque DISPARAIT (sinon on rattraperait dans le vide)",
        !("cloud_refuse" in corps.metadata_json), JSON.stringify(corps.metadata_json));
      controle("(t) et le chemin cloud est inscrit",
        corps.storage_path === "annonces/40470/documents/doc-1/estimationrocher.odt", String(corps.storage_path));
    }
  }

  // ── ⑥ LA BOUCLE : L'ANNONCE VA JUSQU'AU BOUT, ET L'EMPREINTE EST POSEE ──────
  if (!blocBoucle) {
    controle("(0c) handleSyncConsoleDocuments est dans le worker", false, "introuvable");
  } else {
    async function jouerBoucle(scenario) {
      const etat = { journal: [], empreintes: [], refusesVus: [] };
      let appels = 0;
      const doubles = {
        safeJsonParse: () => ({}),
        loadDossier: async () => ({ hektor_annonce_id: "40470", app_dossier_id: 123 }),
        logJob: async (id, canal, niveau, message, detail) => etat.journal.push({ message, detail }),
        fetchConsoleDocumentEntries: async (annonce, lecture) => { lecture.fingerprint = "empreinte-xyz"; return [1, 2, 3]; },
        isHektorForbiddenError: () => false,
        ensureHektorExecutionContext: async () => {},
        upsertConsoleDocuments: async () => ([
          { id: "doc-a", document_name: "mandat.pdf", metadata_json: {} },
          { id: "doc-b", document_name: "estimation.odt", metadata_json: {} },
          { id: "doc-c", document_name: "dpe.pdf", metadata_json: scenario.modelo ? { modelo: { updated_on: "1" } } : {} },
        ]),
        shouldKeepCloud: () => true,
        persistConsoleDocumentFile: async (dossier, row) => {
          appels += 1;
          if (row.id === "doc-b" && scenario.refus) {
            return { document_id: row.id, local_path: "C:/serveur/x", storage_path: null,
                     cloud_available: false, bytes: 2048, sha256: "a".repeat(64),
                     cloud_refuse: { code: "type_refuse", http: 415 } };
          }
          if (row.id === "doc-c" && scenario.modelo) throw new Error("MODELO_PDF_INDISPONIBLE");
          if (row.id === "doc-b" && scenario.passager) throw new Error(MSG_RESEAU);
          return { document_id: row.id, local_path: "C:/serveur/y", storage_path: "annonces/40470/x",
                   cloud_available: true, bytes: 1024, sha256: "b".repeat(64), cloud_refuse: null };
        },
        persistImmoSignCompanionFiles: async () => null,
        reconcileSignatureStates: async () => 0,
        pruneDeletedDocuments: async () => 0,
        saveDocumentContentFingerprint: async (annonce, empreinte) => etat.empreintes.push({ annonce, empreinte }),
      };
      // eslint-disable-next-line no-new-func
      const boucle = new Function(...Object.keys(doubles),
        `${blocBoucle}; return handleSyncConsoleDocuments;`)(...Object.values(doubles));
      let leve = null;
      let resultat = null;
      try { resultat = await boucle({ id: "job-1", payload_json: "{}" }); } catch (error) { leve = error; }
      return { etat, resultat, leve, appels };
    }

    // (A) un .odt refuse au milieu de deux PDF normaux
    const a = await jouerBoucle({ refus: true });
    controle("(u) ⭐⭐ un document refuse ne fait PLUS tomber l'annonce",
      a.leve === null, a.leve && a.leve.message);
    controle("(v) ⭐ ses VOISINS sont traites : les 3 documents sont passes",
      a.appels === 3, `appels = ${a.appels}`);
    controle("(w) 2 sur 3 arrivent au cloud, le refuse reste sur le serveur",
      a.resultat && a.resultat.cloud_stored === 2 && a.resultat.local_stored === 3,
      JSON.stringify(a.resultat));
    controle("(x) ⭐ L'EMPREINTE EST POSEE (divergence voulue : le refus ne guerira pas)",
      a.etat.empreintes.length === 1 && a.etat.empreintes[0].empreinte === "empreinte-xyz",
      JSON.stringify(a.etat.empreintes));
    controle("(y) le compte rendu du travail dit combien ont ete refuses",
      a.resultat && a.resultat.coffre_refuses === 1, JSON.stringify(a.resultat));
    controle("(z) ⚠ et le journal le NOMME (jamais un echec muet)",
      a.etat.journal.some((l) => /refuse par le coffre/i.test(l.message)
        && l.detail && l.detail.document_name === "estimation.odt"),
      JSON.stringify(a.etat.journal.map((l) => l.message)));

    // (B) TEMOIN INVERSE : la regle voisine (PDF modelo) n'a pas bouge
    const b = await jouerBoucle({ modelo: true });
    controle("(aa) ⚠ TEMOIN INVERSE : un PDF modelo saute -> PAS d'empreinte (il peut guerir)",
      b.leve === null && b.etat.empreintes.length === 0 && b.resultat.modelo_skipped === 1,
      JSON.stringify({ empreintes: b.etat.empreintes.length, r: b.resultat && b.resultat.modelo_skipped }));

    // (C) TEMOIN INVERSE : un accroc passager fait toujours tomber le travail
    const c = await jouerBoucle({ passager: true });
    controle("(bb) ⚠⚠ TEMOIN INVERSE : une panne passagere fait TOUJOURS tomber le travail",
      c.leve !== null && c.etat.empreintes.length === 0, "avalee a tort");
  }

  // ── ⑦ LE CORRECTIF EST BRANCHE LA OU IL FAUT, ET NULLE PART AILLEURS ────────
  controle("(cc) la boucle de synchro arme la tolerance",
    /persistConsoleDocumentFile\(dossier, row, \{ cloud, tolererRefusCoffre: true \}\)/.test(src),
    "la boucle ne l'arme pas");
  const iPrepare = src.indexOf("async function handlePrepareDocumentCloud(");
  const blocPrepare = iPrepare < 0 ? "" : src.slice(iPrepare, src.indexOf("\n}", iPrepare));
  controle("(dd) ⛔ le clic humain « preparer » ne l'arme PAS (pas de bouton menteur)",
    blocPrepare && !blocPrepare.includes("tolererRefusCoffre"), "prepare_document_cloud l'arme");
  controle("(ee) l'envoi app -> Hektor n'est pas touche",
    !tranche("async function persistProvidedDocumentFile(").includes("tolererRefusCoffre"),
    "persistProvidedDocumentFile l'arme");

  console.log(echecs === 0 ? "\nTOUT EST VERT" : `\n${echecs} CONTROLE(S) ROUGE(S)`);
  process.exit(echecs === 0 ? 0 : 1);
})();
