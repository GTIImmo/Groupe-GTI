// UNE PHOTO AJOUTEE DEPUIS L'APP EST-ELLE GARDEE CHEZ NOUS ?
//                                                                  25/09/2026
// Jusqu'ici : la photo partait a Hektor, on indexait la ligne, on effacait le
// temporaire -- et le fichier n'existait NULLE PART chez nous. C'est ce qui explique
// les 42 photos « en attente » de 6 annonces, jamais traitees.
//
// Les documents font ce geste depuis des mois (persistProvidedDocumentFile). Ce test
// verifie que les photos le font desormais AUSSI, et de la MEME facon.
//
// ⚠ ET IL VERIFIE LE CHOIX DELICAT : la copie est BEST-EFFORT, jamais bloquante.
//   A ce stade la photo est DEJA chez Hektor ; lever ferait rejouer le travail, donc
//   RENVOYER la photo -- et Hektor en aurait deux. Mieux vaut une copie manquante,
//   rattrapable par la synchro, qu'un doublon chez Hektor.
//   En echange, le temporaire N'EST PAS efface et l'echec est ecrit au journal.
//
// Il fait tourner LA VRAIE fonction du worker avec un faux disque et un faux Supabase.
// N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT AUCUN FICHIER.

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

(async () => {
  const bloc = tranche("async function persistProvidedPhotoFile(");
  if (!bloc) {
    controle("(0) persistProvidedPhotoFile est dans le worker", false, "introuvable");
  } else {
    // ── le faux monde : on capture, on n'ecrit rien ──────────────────────────
    const ecrits = [];
    const versLeCloud = [];
    const patches = [];
    const faux = {
      writeLocalArchiveFile: (p, b) => ecrits.push({ chemin: p, octets: b.length }),
      uploadStorageObject: async (p, b, m) => versLeCloud.push({ chemin: p, octets: b.length, type: m }),
      supabaseRequest: async (chemin, options) => {
        patches.push({ chemin, corps: JSON.parse(options.body) });
      },
      localPhotoPath: (annonce, id, nom) => `C:/serveur/annonces/${annonce}/photos/${id}/${nom}`,
      safeFilename: (n, f) => String(n || "").trim() || f,
      storageSafeFilename: (n, f) => String(n || "").trim() || f,
      normalizeMimeType: (m) => m || "application/octet-stream",
      sha256Buffer: (b) => crypto.createHash("sha256").update(b).digest("hex"),
      localArchiveMetadata: (p) => ({ local_archive_path: p }),
      STORAGE_BUCKET: "hektor-console-documents",
    };
    // eslint-disable-next-line no-new-func
    const persist = new Function(...Object.keys(faux),
      `${bloc}; return persistProvidedPhotoFile;`)(...Object.values(faux));

    const ligne = {
      id: "row-uuid-1", hektor_annonce_id: "62087", hektor_photo_id: "77",
      filename: "salon.jpg", storage_bucket: null, storage_path: null, metadata_json: {},
    };
    const buf = Buffer.alloc(4096, 7);

    // ── ① ANNONCE VIVANTE : serveur ET cloud ────────────────────────────────
    let r = await persist(ligne, buf, "image/jpeg", { cloud: true });
    controle("(a) le fichier est ecrit sur le SERVEUR",
      ecrits.length === 1 && ecrits[0].octets === 4096, JSON.stringify(ecrits));
    controle("(b) au chemin du worker, sous l'identifiant de la LIGNE",
      ecrits[0].chemin === "C:/serveur/annonces/62087/photos/row-uuid-1/salon.jpg", ecrits[0].chemin);
    controle("(c) annonce vivante -> copie aussi dans Supabase",
      versLeCloud.length === 1 && versLeCloud[0].octets === 4096, JSON.stringify(versLeCloud));
    controle("(d) l'index retient cloud_available",
      patches.length === 1 && patches[0].corps.storage_status === "cloud_available",
      JSON.stringify(patches[0] && patches[0].corps));
    controle("(e) la taille et l'empreinte sont enregistrees",
      patches[0].corps.file_size === 4096 && /^[0-9a-f]{64}$/.test(patches[0].corps.sha256),
      JSON.stringify(patches[0].corps));
    controle("(f) le chemin serveur est note dans la ligne",
      patches[0].corps.metadata_json.local_archive_path === ecrits[0].chemin,
      JSON.stringify(patches[0].corps.metadata_json));
    controle("(g) la ligne visee est la bonne",
      patches[0].chemin.includes("id=eq.row-uuid-1"), patches[0].chemin);

    // ── ② ANNONCE ARCHIVEE : le serveur SEUL ────────────────────────────────
    ecrits.length = 0; versLeCloud.length = 0; patches.length = 0;
    r = await persist(ligne, buf, "image/jpeg", { cloud: false });
    controle("(h) annonce archivee -> le serveur quand meme",
      ecrits.length === 1, "le serveur ne recoit rien");
    controle("(i) annonce archivee -> RIEN dans Supabase",
      versLeCloud.length === 0, JSON.stringify(versLeCloud));
    controle("(j) l'index retient local_only",
      patches[0].corps.storage_status === "local_only", JSON.stringify(patches[0].corps));
    controle("(k) la fonction rend le chemin ecrit", r && r.local_path === ecrits[0].chemin, JSON.stringify(r));
  }

  // ── ③ LE GESTE EST BRANCHE DANS L'AJOUT ───────────────────────────────────
  controle("(l) l'ajout depuis l'app appelle la copie",
    /persistProvidedPhotoFile\(ligne, temp\.buffer/.test(src), "la copie n'est pas appelee");
  controle("(m) la regle de l'etat est appliquee, comme pour les documents",
    /persistProvidedPhotoFile\([\s\S]{0,160}shouldKeepCloud\(dossier\)/.test(src),
    "le cloud n'est pas conditionne a l'etat de l'annonce");

  // ── ④ LE CHOIX DELICAT : best-effort, et le temporaire suit ───────────────
  const iCopie = src.indexOf("let gardeeErreur = null;");
  const iEfface = src.indexOf("await deleteStorageObject(tempPath);", iCopie);
  controle("(n) le temporaire est efface APRES la copie, pas avant",
    iCopie > 0 && iEfface > iCopie, `copie=${iCopie} efface=${iEfface}`);
  controle("(o) et SEULEMENT si la copie a reussi",
    /if \(gardeeErreur \|\| !gardee\) \{[\s\S]{0,600}?\} else \{\s*await deleteStorageObject\(tempPath\);/.test(src),
    "le temporaire est efface meme en cas d'echec");
  controle("(p) un echec de copie ne LEVE pas (sinon Hektor aurait la photo en double)",
    /catch \(error\) \{\s*gardeeErreur = error/.test(src), "l'echec est relance");
  controle("(q) mais il est ECRIT au journal, pas avale",
    /Photo envoyee a Hektor mais NON copiee sur le serveur/.test(src), "echec silencieux");
  controle("(r) et le compte rendu du travail le porte",
    /copie_erreur: gardeeErreur/.test(src), "invisible dans le resultat");

  // ── ⑤ MEME PATRON QUE LES DOCUMENTS ──────────────────────────────────────
  const doc = tranche("async function persistProvidedDocumentFile(");
  controle("(s) les documents gardent toujours leur fichier",
    !!doc && /writeLocalArchiveFile\(localPath, buffer\)/.test(doc), "le patron des documents a change");
  controle("(t) les deux appliquent la meme regle de cloud",
    !!doc && /cloudWanted \? STORAGE_BUCKET/.test(doc) && /cloudWanted \? STORAGE_BUCKET/.test(bloc || ""),
    "les deux chemins ont diverge");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
