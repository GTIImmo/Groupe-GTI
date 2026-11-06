// Essai HORS LIGNE (06/11/2026, §55) : qui est imprimé sur l'avis de valeur. Les fonctions sont EXTRAITES du worker
// (jamais lancé), supabaseRequest est remplacé par des tables en mémoire (extraits réels du 06/11). Rien ne sort.
// ⛔ LECTURE SEULE : n'appelle ni Hektor ni Supabase, ne lance pas le worker (il est lu comme un texte).
// Usage : node Console/test_avis_valeur_regle_admin.js [chemin d'un autre worker, pour le témoin]   (sortie 0 = tout vert)
const fs = require("fs");
const src = fs.readFileSync(process.argv[2] || require("path").join(__dirname, "console_job_worker.js"), "utf8").split(String.fromCharCode(13)).join("");
const prendre = (debut) => {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  return src.slice(i, src.indexOf("\n}\n", i) + 3);
};
const noms = ["function cleanString(", "function normalizeEmail(", "function normalizeAgencyName(", "function choisirLigneAnnuaire(",
  "async function loadAgencyDirectoryRowForOwner(", "async function resolveEstimNegotiatorContact(",
  "function cleAgenceRegistre(", "async function conseillerAvisDeValeurSelonRegle("];
const morceaux = noms.map(prendre);
const T = {
  app_user_profile: [
    { id: "u-frederic", role: "admin" }, { id: "u-franck", role: "admin" }, { id: "u-pauline", role: "admin" },
    { id: "u-legrand", role: "commercial" }, { id: "u-pereira", role: "commercial" }, { id: "u-nouveau", role: "commercial" },
  ],
  app_negociateur_personne: [
    { app_personne_id: 1000001, nom: "Frédéric GERPHAGNON", email: "frederic.gerphagnon@gti-immobilier.fr", email_pro: "frederic.gerphagnon@gti-immobilier.fr", portable: "0658770893", actif: true, app_agence_id: 2000007, app_user_id: "u-frederic" },
    { app_personne_id: 1000048, nom: "Pauline GIRINON", email: "p.girinon@gti-immobilier.fr", email_pro: "p.girinon@gti-immobilier.fr", portable: "0477062020", actif: true, app_agence_id: 2000004, app_user_id: "u-pauline" },
    { app_personne_id: 1000042, nom: "Mélanie LEGRAND", email: "legrand@gti-immobilier.fr", email_pro: "legrand@gti-immobilier.fr", portable: "0668413858", actif: true, app_agence_id: 2000015, app_user_id: "u-legrand" },
    { app_personne_id: 1000035, nom: "Emmanuelle PEREIRA", email: "pereira@gti-immobilier.fr", email_pro: "pereira@gti-immobilier.fr", portable: "0666024072", actif: true, app_agence_id: 2000007, app_user_id: "u-pereira" },
    { app_personne_id: 1000060, nom: "Christèle GENTES", email: "gentes@gti-immobilier.fr", email_pro: null, portable: "0600000060", actif: true, app_agence_id: 2000010, app_user_id: null },
    { app_personne_id: 1000070, nom: "Ancien PARTI", email: "parti@gti-immobilier.fr", portable: "0600000070", actif: false, app_agence_id: 2000007, app_user_id: null },
  ],
  app_negociateur_fiche: [
    { sorte: "fiche_negociateur", hektor_negociateur_id: "20", app_personne_id: 1000001, actif_chez_hektor: false },
    { sorte: "fiche_negociateur", hektor_negociateur_id: "16", app_personne_id: 1000048, actif_chez_hektor: false },
    { sorte: "fiche_negociateur", hektor_negociateur_id: "5", app_personne_id: 1000042, actif_chez_hektor: true },
    { sorte: "fiche_negociateur", hektor_negociateur_id: "26", app_personne_id: 1000035, actif_chez_hektor: true },
    { sorte: "fiche_negociateur", hektor_negociateur_id: "33", app_personne_id: 1000060, actif_chez_hektor: true, email_vu: "gentes@gti-immobilier.fr" },
    { sorte: "fiche_negociateur", hektor_negociateur_id: "70", app_personne_id: 1000070, actif_chez_hektor: true },
    { sorte: "fiche_negociateur", hektor_negociateur_id: "99", app_personne_id: 1000001, actif_chez_hektor: true },
  ],
  app_registre_agence: [
    { app_agence_id: 2000007, nom: "Groupe GTI Firminy", telephone: "04 77 06 20 20", email: "firminy@gti-immobilier.fr", responsable: null },
    { app_agence_id: 2000010, nom: "Groupe Gti Le Puy en Velay", telephone: "04 71 00 00 10", email: "lepuy@gti-immobilier.fr" },
    { app_agence_id: 2000015, nom: "Groupe GTI Saint-Etienne", telephone: "04 77 41 86 79", email: "dorian@gti-immobilier.fr" },
    { app_agence_id: 2000016, nom: "Groupe GTI Ambert", telephone: "04 73 82 95 61", email: null },
  ],
  app_registre_agence_alias: [
    { cle: "FIRMINY", app_agence_id: 2000007, ecriture: "Groupe GTI Firminy" },
    { cle: "LE-PUY-EN-VELAY", app_agence_id: 2000010, ecriture: "Groupe Gti Le Puy en Velay" },
    { cle: "SAINT-ETIENNE", app_agence_id: 2000015, ecriture: "Groupe GTI Saint-Etienne" },
    { cle: "AMBERT", app_agence_id: 2000016, ecriture: "Groupe GTI Ambert   " },
  ],
  app_agence_directory: [
    { nom: "Groupe GTI Ambert", tel: "04 73 82 95 61", mail: "ambert@gti-immobilier.fr", responsable: null },
    { nom: "Groupe Gti Le Puy en Velay", tel: "04 71 00 00 10", mail: "lepuy@gti-immobilier.fr", responsable: null },
  ],
  app_hektor_negotiator_agency_directory: [
    { hektor_negociateur_id: "20", hektor_user_id: "46", agence_nom: "Groupe GTI Firminy", display_name: "Frédéric GERPHAGNON", email: "frederic.gerphagnon@gti-immobilier.fr", is_active: false, portable: "0658770893" },
  ],
};
let pannes = new Set();
async function supabaseRequest(chemin) {
  const [table, qs] = chemin.split("?");
  if (pannes.has(table)) throw new Error("panne " + table);
  let rows = (T[table] || []).slice();
  const params = new URLSearchParams(qs || "");
  let limit = 1000;
  for (const [k, v] of params) {
    if (k === "select") continue;
    if (k === "limit") { limit = Number(v); continue; }
    const pos = v.indexOf(".");
    const op = v.slice(0, pos);
    const val = v.slice(pos + 1);
    rows = rows.filter((r) => {
      const x = r[k] == null ? "" : String(r[k]);
      if (op === "eq") return x === val;
      if (op === "ilike") return x.toLowerCase() === val.toLowerCase();
      throw new Error("filtre " + v);
    });
  }
  return JSON.parse(JSON.stringify(rows.slice(0, limit)));
}
eval(morceaux.filter(Boolean).join("\n"));
(async () => {
  if (typeof conseillerAvisDeValeurSelonRegle !== "function") {
    // TÉMOIN : l'ancien worker n'a que le conseiller CONNECTÉ
    const c = await resolveEstimNegotiatorContact(
      { negociateurConnecte: { email: "frederic.gerphagnon@gti-immobilier.fr" }, negociateur: { nom: "Christèle GENTES" } },
      { commercial_id: "33", agence_nom: "Groupe Gti Le Puy en Velay" }, { preferConnected: true });
    console.log("TEMOIN ancien worker, Frédéric génère sur le bien de GENTES -> imprimé :", c && c.nom, "/", c && c.email, "/", c && c.agence);
    process.exit(c && c.nom === "Frédéric GERPHAGNON" ? 3 : 1);
  }
  const R = (who, dossier) => conseillerAvisDeValeurSelonRegle({ requested_by: who }, dossier);
  const cas = [];
  const essai = (nom, ok) => cas.push([nom, !!ok]);
  let r = await R("u-frederic", { commercial_id: "33", agence_nom: "Groupe Gti Le Puy en Velay" });
  essai("1. admin sur le bien de GENTES (active, sans compte) -> GENTES", r.source === "negociateur_du_bien" && r.contact.nom === "Christèle GENTES" && r.contact.telephone === "0600000060");
  essai("1. ... son e-mail (fiche) et l'agence DU BIEN", r.contact.email === "gentes@gti-immobilier.fr" && r.contact.agence === "Groupe Gti Le Puy en Velay" && r.contact.agenceMail === "lepuy@gti-immobilier.fr");
  r = await R("u-franck", { commercial_id: "", agence_nom: "Groupe GTI Firminy" });
  essai("2. admin, bien SANS négo -> agence seule (pas de nom)", r.source === "agence_seule" && r.contact.nom === null && r.contact.telephone === "04 77 06 20 20" && r.contact.email === "firminy@gti-immobilier.fr");
  r = await R("u-pauline", { commercial_id: "70", agence_nom: "Groupe GTI Firminy" });
  essai("3. admin, négo PARTI (personne inactive) -> agence seule", r.source === "agence_seule" && r.contact.nom === null);
  r = await R("u-pauline", { commercial_id: "16", agence_nom: "Groupe GTI Firminy" });
  essai("4. admin, bien sur l'ancienne fiche (éteinte) de Pauline -> agence seule", r.source === "agence_seule" && r.contact.nom === null);
  r = await R("u-pauline", { commercial_id: "99", agence_nom: "Groupe GTI Firminy" });
  essai("5. fiche ACTIVE dont la personne est un compte ADMIN -> jamais imprimée", r.source === "agence_seule" && r.contact.nom === null);
  r = await R("u-legrand", { commercial_id: "33", agence_nom: "Groupe Gti Le Puy en Velay" });
  essai("6. LEGRAND (négo) génère sur le bien d'un collègue -> elle-même, SON agence", r.source === "negociateur_demandeur" && r.contact.nom === "Mélanie LEGRAND" && r.contact.agence === "Groupe GTI Saint-Etienne" && r.contact.telephone === "0668413858");
  r = await R("u-nouveau", { commercial_id: "26", agence_nom: "Groupe GTI Firminy" });
  essai("7. négo absent du registre -> repli (sa session reste permise)", r.repli === "negociateur_absent_du_registre");
  r = await R(null, { commercial_id: "26", agence_nom: "Groupe GTI Firminy" });
  essai("8. pas de demandeur -> traité comme un admin : négo du bien", r.source === "negociateur_du_bien" && r.contact.nom === "Emmanuelle PEREIRA");
  r = await R("u-frederic", { commercial_id: "", agence_nom: "Groupe GTI Ambert   " });
  essai("9. agence aux espaces (Ambert) trouvée par l'alias ; mail manquant pris à l'annuaire", r.contact.agence === "Groupe GTI Ambert" && r.contact.agenceTel === "04 73 82 95 61" && r.contact.agenceMail === "ambert@gti-immobilier.fr");
  pannes = new Set(["app_negociateur_fiche"]);
  let leve = false;
  try { await R("u-frederic", { commercial_id: "33", agence_nom: "Groupe GTI Firminy" }); } catch (_) { leve = true; }
  essai("10. registre en panne -> la règle LÈVE (l'appelant reprend l'ancien chemin sans session d'admin)", leve);
  pannes = new Set();
  let rouges = 0;
  for (const [n, ok] of cas) { if (!ok) rouges++; console.log((ok ? "OK    " : "ROUGE ") + n); }
  console.log(`${cas.length - rouges}/${cas.length} verts`);
  process.exit(rouges ? 1 : 0);
})();
