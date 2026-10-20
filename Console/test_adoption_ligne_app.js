// UNE LIGNE CREEE PAR L'APP DOIT GARDER SON IDENTIFIANT ET RECEVOIR CELUI DE HEKTOR
//                                                                  20/10/2026
// CE QUI S'EST PASSE, mesure du 20/10 : le 19/10 a 11:43, premier vrai ajout de document
// par le chemin differe (AVENANTS 87K, annonce 59578). Hektor a recu le fichier, le worker
// a pose le numero Hektor sur NOTRE ligne (source = 'app'), puis `upsertConsoleDocuments`
// a plante : « duplicate key ... app_console_document_pkey » (409). Resultat : l'app
// affichait « l'envoi a echoue » pour un document pourtant chez Hektor, et la synchro de
// nuit de l'annonce echouait chaque soir de la meme facon.
//
// LA CAUSE : l'indexation retrouve notre ligne par le numero Hektor et REPREND SON id
// (c'est juste : l'identifiant de l'app ne change jamais), mais elle l'ecrit avec la
// source de la LISTE HEKTOR (hektor_console_uploaded_private). La base cherche le conflit
// sur (annonce, source, numero), n'en trouve pas, tente un INSERT -- et l'id est deja pris.
//
// LA REGLE (Frederic, 20/10) : la ligne porte les DEUX identifiants, celui de l'app (id)
// et celui de Hektor (hektor_document_id). Aucun des deux ne se perd, aucun n'est remplace.
//
// CE TEST FAIT TOURNER LA VRAIE `upsertConsoleDocuments` du worker contre un faux Supabase
// QUI APPLIQUE LES VRAIES CONTRAINTES de la base (cle primaire sur id, unicite sur
// annonce+source+numero). C'est ce qui manquait : test_envoi_hektor_differe.js remplace
// cette fonction par une fausse (« upsertConsoleDocuments: async () => [] »), donc il ne
// pouvait pas voir le defaut. IL N'APPELLE RIEN, N'ECRIT RIEN.
//
//   node Console/test_adoption_ligne_app.js        (code 0 = tout vert)

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function tranche(debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

// ── le faux Supabase, avec les VRAIES contraintes ────────────────────────────────
class FauxSupabase {
  constructor(lignes) { this.lignes = lignes.map((l) => ({ ...l })); this.appels = []; }
  async requete(chemin, options = {}) {
    const methode = options.method || "GET";
    this.appels.push(`${methode} ${chemin}`);
    if (methode === "GET") {
      const m = chemin.match(/hektor_annonce_id=eq\.([^&]+)/);
      return this.lignes.filter((l) => !m || String(l.hektor_annonce_id) === decodeURIComponent(m[1]));
    }
    if (methode === "POST" && chemin.startsWith("app_console_document?on_conflict=")) {
      for (const neuve of JSON.parse(options.body)) {
        // « resolution=merge-duplicates » : le conflit se cherche sur (annonce, source, numero)
        const cible = this.lignes.find((l) => l.hektor_annonce_id === neuve.hektor_annonce_id
          && l.source === neuve.source && l.hektor_document_id === neuve.hektor_document_id);
        if (cible) { Object.assign(cible, neuve); continue; }
        // sinon c'est un INSERT : la cle primaire joue
        if (this.lignes.some((l) => l.id === neuve.id)) {
          throw new Error('Supabase 409 on app_console_document?on_conflict=hektor_annonce_id,source,hektor_document_id: duplicate key value violates unique constraint "app_console_document_pkey"');
        }
        this.lignes.push({ ...neuve });
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
      const m = chemin.match(/id=in\.\(([^)]*)\)/);
      const ids = m ? decodeURIComponent(m[1]).split(",") : [];
      for (const l of this.lignes) if (ids.includes(l.id)) Object.assign(l, JSON.parse(options.body));
      return null;
    }
    throw new Error(`appel non prevu : ${methode} ${chemin}`);
  }
}

function monter(faux) {
  const blocs = [
    tranche("function entryPriority("),
    tranche("function dedupeDocumentEntries("),
    tranche("async function loadExistingDocuments("),
    tranche("function adoptExistingImmoSignRows("),
    tranche("function adoptExistingAppRows("),   // absent avant le correctif : le test le dira
    // ⑦ 20/10 : upsertConsoleDocuments appelle desormais reconcilierParChemin
    //   (le domaine des documents). Sans ces deux tranches, le montage leve
    //   « reconcilierParChemin is not defined » -- meme raison que adoptExistingAppRows
    //   ajoute la veille. On AJOUTE, on ne restructure pas.
    tranche("function cheminDocument("),
    tranche("async function reconcilierParChemin("),
    tranche("async function upsertConsoleDocuments("),
  ].filter(Boolean);
  // eslint-disable-next-line no-new-func
  return new Function("supabaseRequest", "crypto", "storageSafeFilename", "logJob",
    `${blocs.join("\n")}; return upsertConsoleDocuments;`)(
    (chemin, options) => faux.requete(chemin, options), crypto, (n, f) => String(n || f),
    async () => {});
}

const ANNONCE = "59578";
const ID_APP = "6b97082e-20fc-4816-9a27-58d6aa06e106";
const NUM_HEKTOR = "716119466cb6d1696be22788a837711d9b9194ab";
const dossier = { app_dossier_id: 1387010, hektor_annonce_id: ANNONCE };

function ligneApp(extra = {}) {
  return {
    id: ID_APP, app_dossier_id: 1387010, hektor_annonce_id: ANNONCE,
    hektor_document_id: NUM_HEKTOR, document_name: "AVENANTS 87K.pdf", source: "app",
    visibility: "private", storage_bucket: "hektor-console-documents",
    storage_path: `annonces/${ANNONCE}/documents/${ID_APP}/AVENANTS 87K.pdf`,
    storage_status: "cloud_available", envoi_hektor_statut: "envoye",
    metadata_json: { cree_par_app: true }, ...extra,
  };
}
function entreeHektor(extra = {}) {
  return {
    hektor_document_id: NUM_HEKTOR, document_name: "AVENANTS 87K.pdf",
    source: "hektor_console_uploaded_private", visibility: "private", document_type: null,
    console_url: "https://hektor/x", technical_name: "t", transfer_name: "tr",
    hektor_uploaded_document_id: "42", modelo: null, signature: null, ...extra,
  };
}

(async () => {
  console.log("\n(1) LE CAS REEL : notre ligne (source app) porte deja le numero Hektor");
  {
    const faux = new FauxSupabase([ligneApp()]);
    let upsert, erreur = null;
    try {
      upsert = monter(faux);
      await upsert(dossier, [entreeHektor()]);
    } catch (e) { erreur = e; }
    controle("(a) l'indexation NE LEVE PAS (le 409 du 19/10)", !erreur, erreur && erreur.message.slice(0, 90));
    const apres = faux.lignes;
    controle("(b) il reste UNE SEULE ligne pour ce document", apres.length === 1, `${apres.length} lignes`);
    const l = apres[0] || {};
    controle("(c) ⭐ l'identifiant de l'APP est INTACT", l.id === ID_APP, `id = ${l.id}`);
    controle("(d) ⭐ le numero HEKTOR est toujours sur la ligne", l.hektor_document_id === NUM_HEKTOR, `n° = ${l.hektor_document_id}`);
    controle("(e) la ligne reste d'origine « app » (la trace n'est pas effacee)", l.source === "app", `source = ${l.source}`);
    controle("(f) le fichier garde sa place (storage_path)", l.storage_path === ligneApp().storage_path, `${l.storage_path}`);
    controle("(g) la ligne est enrichie par Hektor (console_url)", (l.metadata_json || {}).console_url === "https://hektor/x", JSON.stringify(l.metadata_json));
    controle("(h) la marque « cree_par_app » survit", (l.metadata_json || {}).cree_par_app === true, JSON.stringify(l.metadata_json));
  }

  console.log("\n(2) UN SECOND PASSAGE (la synchro de nuit) ne change rien et ne leve pas");
  {
    const faux = new FauxSupabase([ligneApp()]);
    let erreur = null;
    try {
      const upsert = monter(faux);
      await upsert(dossier, [entreeHektor()]);
      await upsert(dossier, [entreeHektor()]);
    } catch (e) { erreur = e; }
    controle("(a) deux passages de suite : pas d'erreur", !erreur, erreur && erreur.message.slice(0, 90));
    controle("(b) toujours une seule ligne, id et numero intacts",
      faux.lignes.length === 1 && faux.lignes[0].id === ID_APP && faux.lignes[0].hektor_document_id === NUM_HEKTOR,
      JSON.stringify(faux.lignes.map((x) => [x.id, x.hektor_document_id])));
  }

  console.log("\n(3) LES AUTRES CAS NE BOUGENT PAS (le correctif ne doit toucher que « app »)");
  {
    // un document qui vient de Hektor : sa source reste celle de la liste
    const faux = new FauxSupabase([]);
    await monter(faux)(dossier, [entreeHektor()]);
    controle("(a) un document venu de Hektor est cree avec la source de la liste",
      faux.lignes.length === 1 && faux.lignes[0].source === "hektor_console_uploaded_private",
      JSON.stringify(faux.lignes.map((x) => x.source)));

    // une ligne « app » SANS numero Hektor (envoi pas encore parti) : on n'y touche pas
    const enAttente = ligneApp({ id: "aaaaaaaa-0000-0000-0000-000000000001", hektor_document_id: null, envoi_hektor_statut: "a_envoyer" });
    const faux2 = new FauxSupabase([enAttente]);
    await monter(faux2)(dossier, [entreeHektor({ hektor_document_id: "autrenumero" })]);
    const intacte = faux2.lignes.find((x) => x.id === enAttente.id);
    controle("(b) une ligne « app » sans numero n'est pas adoptee a tort",
      intacte && intacte.hektor_document_id === null && faux2.lignes.length === 2,
      JSON.stringify(faux2.lignes.map((x) => [x.id.slice(0, 8), x.source, x.hektor_document_id])));

    // un autre document de la meme annonce, venu de Hektor : indifferent
    const faux3 = new FauxSupabase([ligneApp()]);
    await monter(faux3)(dossier, [entreeHektor(), entreeHektor({ hektor_document_id: "voisin", document_name: "autre.pdf" })]);
    const voisin = faux3.lignes.find((x) => x.hektor_document_id === "voisin");
    controle("(c) un document voisin garde la source de la liste",
      voisin && voisin.source === "hektor_console_uploaded_private" && faux3.lignes.length === 2,
      JSON.stringify(faux3.lignes.map((x) => [x.source, x.hektor_document_id])));
  }

  console.log("\n(4) « SUPPRIME CHEZ HEKTOR » : la ligne app est marquee absente, jamais effacee");
  {
    const voisin = ligneApp({ id: "bbbbbbbb-0000-0000-0000-000000000002", hektor_document_id: "voisin", source: "hektor_console_uploaded_private", metadata_json: {} });
    const faux = new FauxSupabase([ligneApp(), voisin]);
    await monter(faux)(dossier, [entreeHektor({ hektor_document_id: "voisin", document_name: "autre.pdf" })]);
    const l = faux.lignes.find((x) => x.id === ID_APP);
    controle("(a) la ligne existe encore", Boolean(l), "effacee");
    controle("(b) elle est marquee « plus chez Hektor »", l && l.present_in_hektor === false, `present = ${l && l.present_in_hektor}`);
    controle("(c) id et numero intacts", l && l.id === ID_APP && l.hektor_document_id === NUM_HEKTOR, JSON.stringify(l));
  }

  console.log(echecs ? `\n${echecs} CONTROLE(S) EN ECHEC` : "\nTOUT EST VERT");
  process.exit(echecs ? 1 : 0);
})().catch((e) => { console.error("ERREUR DU TEST :", e); process.exit(2); });
