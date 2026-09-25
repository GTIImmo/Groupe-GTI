// L'EMPREINTE PORTE-T-ELLE NOTRE NUMERO -- SANS CASSER CE QUI MARCHE ?
//                                                                  25/09/2026
// app_console_document_fingerprint est le CARNET DU RATTRAPAGE documentaire : elle dit
// quelles annonces ont deja ete regardees. Elle etait la seule table de la chaine a
// n'avoir AUCUN numero de l'app, et elle manquait a REPOINT_TABLES.
//
// ⚠ LA GARDE POSEE PAR FREDERIC : « attention a ne pas casser les workers qui ont besoin
//   des id hektor ». Ce test la verifie point par point -- la cle de conflit, le numero
//   envoye, et les trois autres points d'appel qui interrogent par numero Hektor.
//
// IL FAIT TOURNER LA VRAIE FONCTION DU WORKER, avec un faux client Supabase qui capture
// la charge utile. Il ne rejoue pas la regle : casser le worker doit faire ECHOUER ce test.
//
//   node Console/test_empreinte_numero_app.js
// N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT RIEN.

const fs = require("fs");
const path = require("path");

const WORKER = path.join(__dirname, "console_job_worker.js");
const ENQUEUE = path.join(__dirname, "enqueue_console_sync_jobs.js");
const LOT = path.join(__dirname, "enqueue_empreinte_lot.js");
const REPOINT = path.join(__dirname, "..", "phase2", "sync", "push_single_annonce_to_supabase.py");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

// ── on extrait la vraie fonction du worker, sans executer le reste du fichier ──
function chargerEnregistreur(captures) {
  const src = fs.readFileSync(WORKER, "utf8");
  const i = src.indexOf("async function saveDocumentContentFingerprint(");
  if (i < 0) return null;
  const fin = src.indexOf("\n}", i);
  if (fin < 0) return null;
  const corps = src.slice(i, fin + 2);
  const faux = async (chemin, options) => {
    captures.push({ chemin, options, corps: JSON.parse(options.body) });
  };
  // eslint-disable-next-line no-new-func
  return new Function("supabaseRequest", `${corps}; return saveDocumentContentFingerprint;`)(faux);
}

(async () => {
  const captures = [];
  const enregistrer = chargerEnregistreur(captures);

  if (!enregistrer) {
    controle("(0) saveDocumentContentFingerprint est dans le worker", false, "fonction introuvable");
  } else {
    // (a) APPEL COMPLET : notre numero doit partir
    await enregistrer("62087", "abc123", 4724);
    let c = captures.pop();
    controle("(a) le numero de l'app part avec l'empreinte",
      c && c.corps[0].app_dossier_id === 4724, c ? JSON.stringify(c.corps[0]) : "rien capture");

    // (b) LE NUMERO HEKTOR RESTE, en texte -- c'est lui qui designe la fiche chez Hektor
    controle("(b) le numero Hektor reste dans la charge utile, en texte",
      c && c.corps[0].hektor_annonce_id === "62087", c ? JSON.stringify(c.corps[0]) : "-");

    // (c) LA CLE DE CONFLIT N'A PAS CHANGE. C'est le coeur de la garde de Frederic :
    //     si elle basculait sur app_dossier_id, chaque passage creerait un doublon.
    controle("(c) la cle de conflit reste hektor_annonce_id",
      c && /on_conflict=hektor_annonce_id(&|$)/.test(c.chemin), c ? c.chemin : "-");

    // (d) APPEL D'AVANT (2 arguments) : la colonne ne doit PAS etre dans la charge utile.
    //     Absente => PostgREST ne la met pas dans l'INSERT, donc la valeur deja en base
    //     est conservee. Un null explicite l'effacerait.
    await enregistrer("62505", "def456");
    c = captures.pop();
    controle("(d) appel a 2 arguments : la colonne n'est PAS envoyee (pas de null qui efface)",
      c && !("app_dossier_id" in c.corps[0]), c ? JSON.stringify(c.corps[0]) : "-");

    // (e) VALEUR ABERRANTE : on n'ecrit pas n'importe quoi
    await enregistrer("62794", "ghi789", "pas-un-nombre");
    c = captures.pop();
    controle("(e) un numero d'app non numerique est ignore, pas ecrit",
      c && !("app_dossier_id" in c.corps[0]), c ? JSON.stringify(c.corps[0]) : "-");

    // (f) LE GARDE-FOU D'ORIGINE tient toujours : pas d'annonce, pas d'empreinte
    const avant = captures.length;
    await enregistrer("", "jkl", 1);
    await enregistrer("62087", "", 1);
    controle("(f) sans numero Hektor ou sans empreinte : rien n'est ecrit",
      captures.length === avant, `${captures.length - avant} ecriture(s) de trop`);

    // (g) LE POINT D'APPEL passe bien le dossier
    const src = fs.readFileSync(WORKER, "utf8");
    controle("(g) le worker transmet dossier.app_dossier_id",
      /saveDocumentContentFingerprint\(\s*dossier\.hektor_annonce_id,\s*lecture\.fingerprint,\s*dossier\.app_dossier_id\s*\)/.test(src),
      "appel non mis a jour");
  }

  // (h) LES TROIS AUTRES POINTS D'APPEL interrogent TOUJOURS par numero Hektor.
  //     C'est la garde de Frederic : les workers en ont besoin, on ne leur retire rien.
  const enq = fs.readFileSync(ENQUEUE, "utf8");
  const lot = fs.readFileSync(LOT, "utf8");
  controle("(h1) loadFingerprints lit toujours hektor_annonce_id",
    /app_console_document_fingerprint\?select=hektor_annonce_id/.test(enq), "select modifie");
  controle("(h2) touchFingerprintChecked filtre toujours sur hektor_annonce_id",
    /app_console_document_fingerprint\?hektor_annonce_id=eq\./.test(enq), "filtre modifie");
  controle("(h3) le composeur de lots lit toujours hektor_annonce_id",
    /app_console_document_fingerprint\?select=hektor_annonce_id/.test(lot), "select modifie");

  // (i) LA TABLE EST DANS LE REPOINTAGE -- la raison d'etre de tout ceci
  const rep = fs.readFileSync(REPOINT, "utf8");
  // ⚠ Le bloc se termine a une ligne valant exactement ")", PAS a la premiere parenthese
  // fermante : les commentaires de la liste en contiennent. Premiere version de ce test
  // faussement au rouge pour cette raison -- le code, lui, etait juste.
  const lignes = rep.split(/\r?\n/);
  const debut = lignes.findIndex((l) => l.startsWith("REPOINT_TABLES = ("));
  const fin = debut < 0 ? -1 : lignes.findIndex((l, i) => i > debut && l.trim() === ")");
  const bloc = debut < 0 || fin < 0 ? "" : lignes.slice(debut, fin).join("\n");
  controle("(i) app_console_document_fingerprint est dans REPOINT_TABLES",
    bloc.includes('"app_console_document_fingerprint"'), "absente de la liste");
  controle("(i2) les 3 autres tables de la chaine y sont toujours",
    ["app_console_document", "app_console_photo"].every((t) => bloc.includes(`"${t}"`))
      && rep.includes('"app_console_job"'), "une table a disparu de la liste");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
