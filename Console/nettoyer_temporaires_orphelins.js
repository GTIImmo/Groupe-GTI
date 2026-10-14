#!/usr/bin/env node
/**
 * NETTOYER LA SALLE D'ATTENTE -- les fichiers restes sous temp/ du coffre documents.
 * 14/10/2026. Chantier ③ / 3d, lot 2c. Demande de Frederic : « NETTOIE ».
 *
 * POURQUOI ILS SONT LA. Quand l'app ajoute un document ou une photo, le fichier passe
 * d'abord par une salle d'attente -- temp/uploads/<travail>/ ou temp/photos/<travail>/.
 * Le worker l'y prend, le range pour de bon (serveur + coffre), et devrait vider la
 * salle d'attente. UN SEUL chemin le fait : la photo en envoi immediat
 * (console_job_worker.js, « else { await deleteStorageObject(tempPath) } »).
 * Les documents ne l'ont JAMAIS fait, et les trois generateurs de PDF (estimation,
 * mandat, cadastre) non plus.
 *
 * ETAT MESURE LE 14/10/2026 -- 109 fichiers, 196 Mo, coffre hektor-console-documents :
 *     37  generate_estimation_pdf      137 Mo   (le gros morceau)
 *     38  generate_cadastre_document    19 Mo
 *     11  upload_document_to_hektor     23 Mo
 *     18  generate_mandat_document     2,4 Mo
 *      5  sans aucun travail            15 Mo   (des essais : le logo, un PDF « TEST
 *                                                signatures API », une image ChatGPT...)
 *   Le plus ancien : 14/05 (jour de l'ouverture). Le plus recent : 05/10.
 *   ⭐ LES 104 TRAVAUX SONT TOUS `done`. Aucun en attente, aucun en erreur : rien n'est
 *     en vol, donc rien ne peut etre perdu.
 *   ⭐ ET AUCUNE LIGNE VIVANTE N'Y POINTE : 0 sur 162 544 documents, 0 sur 441 199 photos.
 *
 * ⚠⚠ MAIS LE SCRIPT NE CROIT PAS CETTE MESURE : il la REFAIT, fichier par fichier, a
 *   chaque passage. Elle etait vraie le 14/10 ; elle peut etre fausse le jour ou on le
 *   relancera, et c'est precisement ce jour-la qu'un nettoyage ferait des degats.
 *
 * LES QUATRE GARDES, chacune peut retenir un fichier a elle seule :
 *   ① le chemin DOIT commencer par temp/uploads/ ou temp/photos/ -- jamais rien d'autre
 *   ② AUCUNE ligne de document ni de photo ne doit pointer dessus
 *   ③ le travail attache ne doit pas etre `pending` ni `running` -- ce serait un envoi
 *      EN COURS, et son fichier est la seule copie connue
 *   ④ le fichier doit avoir au moins --age-min jours (2 par defaut)
 *   ⭐ Un travail en `error` est RETENU par defaut : le repreneur des envois pourrait
 *     en avoir besoin. --inclure-echecs leve cette retenue, en connaissance.
 *
 * IL NE SUPPRIME RIEN SANS --supprimer. Par defaut il ne fait que compter et ecrire la
 * liste datee dans logs/ -- cette liste EST la trace de ce qui existait.
 *
 *   node Console/nettoyer_temporaires_orphelins.js                 (compte, ne touche a rien)
 *   node Console/nettoyer_temporaires_orphelins.js --supprimer     (supprime pour de vrai)
 */

const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const COFFRE = "hektor-console-documents";

const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const valeur = (n, d) => {
  const i = args.indexOf(n);
  return i >= 0 && args[i + 1] ? args[i + 1] : d;
};
const SUPPRIMER = flag("--supprimer");
const INCLURE_ECHECS = flag("--inclure-echecs");
const AGE_MIN = Number(valeur("--age-min", "2"));

if (!SUPABASE_URL || !KEY) {
  console.error("SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY manquant.");
  process.exit(2);
}
if (!Number.isFinite(AGE_MIN) || AGE_MIN < 0) {
  console.error(`--age-min doit etre un nombre de jours (recu : ${valeur("--age-min", "")}).`);
  process.exit(2);
}

const entetes = { apikey: KEY, Authorization: `Bearer ${KEY}` };

async function appel(url, options = {}) {
  const r = await fetch(url, {
    ...options,
    headers: { ...entetes, "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!r.ok) throw new Error(`${options.method || "GET"} ${url} -> ${r.status} ${await r.text()}`);
  const txt = await r.text();
  return txt ? JSON.parse(txt) : null;
}

/** Liste recursive : l'API rend les dossiers du niveau courant avec id = null. */
async function lister(prefixe, trouves = []) {
  let decalage = 0;
  for (;;) {
    const lot = await appel(`${SUPABASE_URL}/storage/v1/object/list/${COFFRE}`, {
      method: "POST",
      body: JSON.stringify({ prefix: prefixe, limit: 100, offset: decalage,
                             sortBy: { column: "name", order: "asc" } }),
    });
    if (!Array.isArray(lot) || lot.length === 0) break;
    for (const e of lot) {
      const complet = `${prefixe}${e.name}`;
      if (e.id === null || e.id === undefined) await lister(`${complet}/`, trouves);
      else trouves.push({ name: complet, octets: Number(e.metadata?.size ?? 0),
                          cree: e.created_at || e.updated_at || null });
    }
    if (lot.length < 100) break;
    decalage += lot.length;
  }
  return trouves;
}

/** Les chemins encore references par une ligne vivante -- garde ②. */
async function cheminsReferences(noms) {
  const refs = new Set();
  for (const table of ["app_console_document", "app_console_photo"]) {
    for (let i = 0; i < noms.length; i += 40) {
      const tranche = noms.slice(i, i + 40);
      const liste = tranche.map((n) => `"${n.replace(/"/g, '\\"')}"`).join(",");
      const lignes = await appel(
        `${SUPABASE_URL}/rest/v1/${table}?select=storage_path&storage_path=in.(${encodeURIComponent(liste)})`);
      for (const l of lignes || []) if (l.storage_path) refs.add(l.storage_path);
    }
  }
  return refs;
}

/** L'etat des travaux cites par les chemins -- garde ③. */
async function etatDesTravaux(ids) {
  const etats = new Map();
  const uniques = [...new Set(ids)];
  for (let i = 0; i < uniques.length; i += 40) {
    const tranche = uniques.slice(i, i + 40);
    const lignes = await appel(
      `${SUPABASE_URL}/rest/v1/app_console_job?select=id,status,job_type&id=in.(${tranche.join(",")})`);
    for (const l of lignes || []) etats.set(l.id, l);
  }
  return etats;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const poids = (o) => (o >= 1048576 ? `${(o / 1048576).toFixed(1)} Mo` : `${Math.round(o / 1024)} ko`);

(async () => {
  console.log(`\nSalle d'attente du coffre ${COFFRE} -- lecture...`);
  const fichiers = await lister("temp/");
  if (fichiers.length === 0) {
    console.log("Rien sous temp/. Il n'y a rien a nettoyer.");
    process.exit(0);
  }

  const refs = await cheminsReferences(fichiers.map((f) => f.name));
  const idsCites = fichiers.map((f) => f.name.split("/")[2]).filter((s) => s && UUID.test(s));
  const travaux = await etatDesTravaux(idsCites);

  const limiteAge = Date.now() - AGE_MIN * 86400000;
  const aSupprimer = [];
  const retenus = [];

  for (const f of fichiers) {
    const morceaux = f.name.split("/");
    const famille = morceaux[1];
    const jobId = UUID.test(morceaux[2] || "") ? morceaux[2] : null;
    const job = jobId ? travaux.get(jobId) : null;

    let retenu = null;
    // ① la forme du chemin
    if (famille !== "uploads" && famille !== "photos") retenu = `chemin inattendu (temp/${famille}/)`;
    // ② une ligne vivante pointe dessus
    else if (refs.has(f.name)) retenu = "une ligne vivante pointe sur ce fichier";
    // ③ un envoi en cours
    else if (job && (job.status === "pending" || job.status === "running"))
      retenu = `le travail est ${job.status} -- envoi EN COURS`;
    else if (job && job.status === "error" && !INCLURE_ECHECS)
      retenu = "le travail est en erreur (le repreneur pourrait en avoir besoin)";
    // ④ l'age
    else if (f.cree && Date.parse(f.cree) > limiteAge) retenu = `moins de ${AGE_MIN} jour(s)`;

    (retenu ? retenus : aSupprimer).push({ ...f, famille, job, retenu });
  }

  const total = fichiers.reduce((s, f) => s + f.octets, 0);
  const gain = aSupprimer.reduce((s, f) => s + f.octets, 0);

  // Le compte par type de travail, pour reconnaitre ce qu'on regarde.
  const parType = new Map();
  for (const f of aSupprimer) {
    const k = f.job ? f.job.job_type : "(aucun travail)";
    const v = parType.get(k) || { n: 0, o: 0 };
    parType.set(k, { n: v.n + 1, o: v.o + f.octets });
  }

  console.log(`\n${fichiers.length} fichier(s), ${poids(total)} en tout.`);
  console.log(`  a supprimer : ${aSupprimer.length} (${poids(gain)})`);
  console.log(`  retenus     : ${retenus.length}`);
  for (const [k, v] of [...parType].sort((a, b) => b[1].o - a[1].o)) {
    console.log(`      ${String(v.n).padStart(4)}  ${k.padEnd(28)} ${poids(v.o)}`);
  }
  if (retenus.length) {
    console.log("\n  POURQUOI CEUX-LA SONT RETENUS :");
    const motifs = new Map();
    for (const f of retenus) motifs.set(f.retenu, (motifs.get(f.retenu) || 0) + 1);
    for (const [m, n] of motifs) console.log(`      ${String(n).padStart(4)}  ${m}`);
  }

  // LA LISTE DATEE -- elle est la trace de ce qui existait, et elle s'ecrit AVANT toute
  // suppression (regle du projet : une sauvegarde datee avant un geste destructif).
  const dossierLogs = path.resolve(__dirname, "..", "logs");
  fs.mkdirSync(dossierLogs, { recursive: true });
  const horodatage = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const fichierListe = path.join(dossierLogs, `temporaires_avant_nettoyage_${horodatage}.tsv`);
  fs.writeFileSync(fichierListe,
    "decision\tchemin\toctets\tcree_le\ttype_de_travail\tetat_du_travail\tmotif_de_retenue\n" +
    [...aSupprimer, ...retenus].map((f) => [
      f.retenu ? "RETENU" : "A_SUPPRIMER", f.name, f.octets, f.cree || "",
      f.job ? f.job.job_type : "", f.job ? f.job.status : "", f.retenu || "",
    ].join("\t")).join("\n") + "\n", "utf8");
  console.log(`\nListe datee ecrite : ${fichierListe}`);

  if (!SUPPRIMER) {
    console.log("\n--- RIEN N'A ETE SUPPRIME (ajouter --supprimer pour le faire).");
    process.exit(0);
  }
  if (aSupprimer.length === 0) {
    console.log("\n--- Rien a supprimer.");
    process.exit(0);
  }

  console.log(`\nSuppression de ${aSupprimer.length} fichier(s)...`);
  let faits = 0;
  const rates = [];
  for (let i = 0; i < aSupprimer.length; i += 50) {
    const lot = aSupprimer.slice(i, i + 50).map((f) => f.name);
    try {
      await appel(`${SUPABASE_URL}/storage/v1/object/${COFFRE}`, {
        method: "DELETE", body: JSON.stringify({ prefixes: lot }),
      });
      faits += lot.length;
      console.log(`  ${faits}/${aSupprimer.length}`);
    } catch (e) {
      rates.push(`${lot.length} fichier(s) : ${e.message}`);
    }
  }

  // ⚠ ON RECOMPTE A LA SOURCE. « L'appel a rendu 200 » n'est pas « le fichier n'est
  //   plus la » -- lecon du 13/10 : un 204 sur 0 ligne comptait pour un succes.
  const restants = await lister("temp/");
  console.log(`\nSupprimes : ${faits}. Il reste ${restants.length} fichier(s) sous temp/ `
            + `(attendu : ${retenus.length}).`);
  for (const r of rates) console.log(`  RATE : ${r}`);
  if (restants.length !== retenus.length || rates.length) {
    console.log("⚠ L'ecart n'est pas celui attendu -- relire la liste datee avant de conclure.");
    process.exit(1);
  }
  console.log("OK : la salle d'attente ne contient plus que ce qui devait etre retenu.");
})().catch((e) => {
  console.error(`\nECHEC : ${e.message}`);
  process.exit(1);
});
