// LA LOCALITE DU MANDANT -- essai hors ligne de 8a C-1 et C-2.          22/10/2026
//
// LE DEFAUT (mesure le 22/10) : chez Hektor la localite d'un contact est TYPEE (idVille/idCode) ;
// le texte seul est ignore. Les deux portes du MANDANT n'envoyaient jamais les identifiants
// (miroir : 603486, 604831, 604832, 605030 ont ville et code vides). Et quand la commune n'est
// pas trouvee, l'echec etait AVALE.
//
// CE QU'ON EPROUVE, sur LE CODE REEL (fonctions decoupees dans console_job_worker.js, montees
// avec un faux Hektor qui enregistre ce qui lui est POSTE) :
//   (2) creation de mandant, ville + CP coherents : idVille/idCode PARTENT chez Hektor
//   (3) modification de mandant, idem
//   (4) modification sans ville ni CP : rien n'est cherche, rien n'est ajoute (non-regression)
//   (5) commune introuvable : le travail continue, l'echec est ECRIT au journal et RENDU
//   (6) une erreur de la recherche (ex. 503) : meme chose, avec l'erreur
//   (7) TEMOIN INVERSE : la version d'AVANT n'envoie pas les identifiants (le faux Hektor est fidele)
//   (8) la porte du CONTACT (deja equipee) rend maintenant un compte rendu, et n'a pas change d'envoi
//
//     node Console/test_localite_mandant.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const echecs = [];
function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}
function tranche(debut) {
  const i = src.indexOf(debut);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

const morceaux = {
  apply: tranche("async function applyContactLocalityIds("),
  creer: tranche("async function createHektorMandantContact("),
  modifier: tranche("async function updateHektorMandantContact("),
  clean: tranche("function cleanString("),
  replaceParam: tranche("function replaceParam("),
  replaceFirst: tranche("function replaceFirstArrayParam("),
  decode: tranche("function decodeHtmlEntities("),
  attr: tranche("function attrValue("),
  extract: tranche("function extractHektorFormValues("),
};
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
controle("(1) LA PREUVE D'ABORD : les deux portes du mandant appellent la recherche d'identifiants",
  !manquants.length && /applyContactLocalityIds\(values, \{ city, postalCode \}/.test(morceaux.creer || "")
    && /applyContactLocalityIds\(values, \{ city, postalCode \}/.test(morceaux.modifier || ""),
  manquants.length ? `manquent : ${manquants.join(", ")}` : "un appel manque");
if (manquants.length) { console.log("\n⛔ Une piece manque : on s'arrete."); process.exit(2); }

const FORM_EDIT = `<input name="nom" value="ANCIEN" group="mefContacts/contacts_full_accueil" />
<input name="ville" value="Saint-Étienne" group="mefContacts/contacts_full_accueil" />
<input name="code" value="42000" group="mefContacts/contacts_full_accueil" />
<input name="idVille" value="2" group="mefContacts/contacts_full_accueil" />
<input name="idCode" value="4" group="mefContacts/contacts_full_accueil" />
<input name="email[]" value="a@b.c" group="mefContacts/contacts_full_accueil" />`;

function monter({ resoudre, versionAvant = false } = {}) {
  const posts = [];
  const journal = [];
  const contexte = {
    console, URLSearchParams, JSON,
    ADMIN_URL: "https://faux.hektor/admin/", XMLRPC_URL: "https://faux.hektor/admin/xmlrpc.php",
    logJob: async (id, step, status, message, data) => { journal.push({ step, message, data }); },
    resolveHektorPublicLocality: async (cp, ville) => resoudre(cp, ville),
    fetchHektorManualMandantForm: async () => `<input name="nom" value="" /><input name="ville" value="" /><input name="code" value="" />`,
    fetchHektorContactEditForm: async () => FORM_EDIT,
    hektorFetch: async (url, options) => {
      const corps = options.body instanceof URLSearchParams ? options.body : new URLSearchParams(String(options.body || ""));
      posts.push(corps);
      return { text: corps.get("mode") === "contacts-saveDataEditContact" ? '"content_mefContacts ok"' : '"606000"' };
    },
  };
  vm.createContext(contexte);
  let creer = morceaux.creer, modifier = morceaux.modifier;
  if (versionAvant) {
    creer = creer.replace(/const localite = await applyContactLocalityIds\([^;]*\);/, "const localite = undefined;");
    modifier = modifier.replace(/const localite = await applyContactLocalityIds\([^;]*\);/, "const localite = undefined;");
  }
  vm.runInContext([morceaux.clean, morceaux.replaceParam, morceaux.replaceFirst, morceaux.decode, morceaux.attr,
    morceaux.extract, morceaux.apply, creer, modifier,
    "this.creer = createHektorMandantContact; this.modifier = updateHektorMandantContact; this.apply = applyContactLocalityIds;"].join("\n"), contexte);
  return { contexte, posts, journal };
}

const JOB = { id: "essai" };
const FIRMINY = async (cp, ville) => (cp === "42700" && /firminy/i.test(ville || "")) ? { name: "42700 (Firminy)", code: "42700", idVille: "1", idCode: "1" } : null;

(async () => {
  // (2) creation de mandant coherente
  {
    const m = monter({ resoudre: FIRMINY });
    const r = await m.contexte.creer(JOB, "62774", { last_name: "ESSAI", email: "e@x.invalid", city: "Firminy", postal_code: "42700" });
    const p = m.posts[0];
    controle("(2) creation de mandant : idVille / idCode PARTENT chez Hektor, la ville est celle de Hektor",
      p.get("idVille") === "1" && p.get("idCode") === "1" && p.get("ville") === "42700 (Firminy)" && r.localite.status === "resolue",
      JSON.stringify({ idVille: p.get("idVille"), idCode: p.get("idCode"), ville: p.get("ville"), localite: r.localite }));
  }
  // (3) modification de mandant coherente
  {
    const m = monter({ resoudre: FIRMINY });
    const r = await m.contexte.modifier(JOB, "62774", "605030", { last_name: "ESSAI", email: "e@x.invalid", city: "Firminy", postal_code: "42700" });
    const p = m.posts[0];
    controle("(3) modification de mandant : les identifiants de Firminy REMPLACENT ceux de Saint-Etienne",
      p.get("idVille") === "1" && p.get("idCode") === "1" && r.localite.status === "resolue",
      JSON.stringify({ idVille: p.get("idVille"), idCode: p.get("idCode"), localite: r.localite }));
  }
  // (4) modification sans ville ni CP
  {
    let appels = 0;
    const m = monter({ resoudre: async () => { appels += 1; return null; } });
    const r = await m.contexte.modifier(JOB, "62774", "605030", { last_name: "ESSAI", email: "e@x.invalid" });
    const p = m.posts[0];
    controle("(4) sans ville ni CP : rien n'est cherche, les identifiants d'avant restent tels quels",
      appels === 0 && p.get("idVille") === "2" && p.get("idCode") === "4" && r.localite.status === "sans_objet",
      JSON.stringify({ appels, idVille: p.get("idVille"), localite: r.localite }));
  }
  // (5) commune introuvable
  {
    const m = monter({ resoudre: FIRMINY });
    const r = await m.contexte.modifier(JOB, "62774", "605030", { last_name: "ESSAI", email: "e@x.invalid", city: "Firminy", postal_code: "42000" });
    controle("(5) commune introuvable : le travail CONTINUE, l'echec est ECRIT au journal et RENDU",
      m.posts.length === 1 && r.localite.status === "non_resolue" && r.localite.ville === "Firminy" && r.localite.code === "42000"
        && m.journal.some((j) => j.step === "contact_locality_unresolved" && /NON resolue/.test(j.message)),
      JSON.stringify({ posts: m.posts.length, localite: r.localite, journal: m.journal.map((j) => j.step) }));
  }
  // (6) une erreur de la recherche
  {
    const m = monter({ resoudre: async () => { throw new Error("HTTP 503 simule"); } });
    const r = await m.contexte.creer(JOB, "62774", { last_name: "ESSAI", email: "e@x.invalid", city: "Firminy", postal_code: "42700" });
    controle("(6) la recherche plante : le mandant est cree quand meme, l'erreur est ecrite et rendue",
      r.contactId === "606000" && r.localite.status === "non_resolue" && /503/.test(r.localite.erreur || "")
        && m.journal.some((j) => j.step === "contact_locality_unresolved"),
      JSON.stringify({ r }));
  }
  // (7) TEMOIN INVERSE
  {
    const m = monter({ resoudre: FIRMINY, versionAvant: true });
    await m.contexte.creer(JOB, "62774", { last_name: "ESSAI", email: "e@x.invalid", city: "Firminy", postal_code: "42700" });
    const p = m.posts[0];
    controle("(7) TEMOIN INVERSE : la version d'avant n'envoie PAS les identifiants (texte seul)",
      !p.has("idVille") && !p.has("idCode") && p.get("ville") === "Firminy",
      JSON.stringify({ idVille: p.get("idVille"), ville: p.get("ville") }));
  }
  // (8) la fonction partagee, appelee comme la porte du CONTACT
  {
    const m = monter({ resoudre: FIRMINY });
    const values = new URLSearchParams();
    const ok = await m.contexte.apply(values, { city: "Firminy", postalCode: "42700" }, JOB, "605925");
    const vide = await m.contexte.apply(new URLSearchParams(), { city: "", postalCode: "" }, JOB, "605925");
    controle("(8) la porte du contact : memes identifiants qu'avant, et un compte rendu en plus",
      values.get("idVille") === "1" && values.get("ville") === "42700 (Firminy)" && ok.status === "resolue" && vide.status === "sans_objet",
      JSON.stringify({ ok, vide, idVille: values.get("idVille") }));
  }

  console.log(echecs.length ? `\n⛔ ${echecs.length} controle(s) en echec.` : "\n✅ Tous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`\n⛔ L'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`); process.exit(2); });
