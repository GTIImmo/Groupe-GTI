// TEST DES DEUX NOTAIRES : creation, modification, et NON-modification.
//                                                                  15/09/2026
// Frere de `test_worker_prix_compromis.js`, dont il reprend la charge a
// l'identique -- pour ne rien eprouver d'autre que ce qu'on veut eprouver.
//
// ⚠ IL ECRIT CHEZ HEKTOR. Sur le compromis de TEST 50078 (annonce 24933).
//
// CE QU'IL DOIT PROUVER, dans cet ordre :
//   b)  --acq 122190 --vend 300465        les DEUX notaires arrivent chez Hektor
//   c)  --prix 177500                     sans notaire affirme : ils restent INTACTS
//   a)  (creation : voir --creer, apres suppression du compromis)
//
// Le (c) est le plus important : il verifie qu'on n'a pas casse la regle de
// l'assistant -- « ne rien poser, c'est CONSERVER » -- en ouvrant l'envoi.
//
//   node Console/test_worker_notaires.js --acq 122190 --vend 300465
//   node Console/test_worker_notaires.js --prix 177500

const path = require("path");
const crypto = require("crypto");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const URL_SB = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

const CIBLE = {
  app_dossier_id: 1352132,
  hektor_annonce_id: "24933",
  app_affaire_id: 1001347,
  compromis_id: "50078",
  numero_mandat: "11939",
  acquereur: "605030",
  date: "2026-09-04",
};

/** Rend null quand l'option est ABSENTE -- a distinguer d'une valeur vide. */
function argOption(nom) {
  const t = process.argv.find((a) => a.startsWith(`--${nom}=`) || a === `--${nom}`);
  if (!t) return null;
  if (t.includes("=")) return t.split("=")[1];
  const i = process.argv.indexOf(t);
  return process.argv[i + 1] || "vide";
}

function arg(nom, defaut) {
  const t = process.argv.find((a) => a.startsWith(`--${nom}=`) || a === `--${nom}`);
  if (!t) return defaut;
  if (t.includes("=")) return t.split("=")[1];
  const i = process.argv.indexOf(t);
  return process.argv[i + 1] || defaut;
}

(async () => {
  if (!URL_SB || !KEY) {
    console.error("Manque SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY");
    process.exit(1);
  }
  const prix = String(arg("prix", "177000")).trim();
  const notaireAcq = String(arg("acq", "")).trim();
  const notaireVend = String(arg("vend", "")).trim();
  const creer = process.argv.includes("--creer");
  // --mandants 141053,485955   ou   --mandants vide   pour affirmer une liste VIDE.
  // ⚠ ABSENT N'EST PAS VIDE : sans l'option, la cle ne part pas du tout et Hektor
  //   garde les mandants qu'il deduit du mandat. C'est tout l'objet du test.
  // --acquereurs 605030,605029  : 2.6, l'essai qui manque depuis le 02/09.
  // ⚠ LES TROIS ESSAIS PRECEDENTS UTILISAIENT LE MEME COUPLE, dont un contact
  //   (605075) que Hektor n'a JAMAIS attache et qui n'est que « mandant ». Ils
  //   ne prouvaient donc pas que Hektor n'en garde qu'un.
  const acquereursBrut = argOption("acquereurs");
  const acquereurs = acquereursBrut && acquereursBrut !== "vide"
    ? acquereursBrut.split(",").map((x) => x.trim()).filter(Boolean)
    : [];
  const mandantsBrut = argOption("mandants");
  const mandantsAffirmes = mandantsBrut !== null;
  const mandants = mandantsAffirmes && mandantsBrut !== "vide"
    ? mandantsBrut.split(",").map((x) => x.trim()).filter(Boolean)
    : [];
  if (!/^\d+$/.test(prix)) { console.error("--prix doit etre un entier"); process.exit(1); }

  // ⚠ « AFFIRME » NE VEUT PAS DIRE « PRESENT ». C'est tout l'objet du test :
  //   en reprise, le worker ne pose que ce que l'utilisateur a DESIGNE dans la
  //   modale. Ici, ce sont les options --acq / --vend qui jouent ce role.
  const affirmes = {};
  if (notaireAcq) affirmes.acquereur = true;
  if (notaireVend) affirmes.mandant = true;

  // ⚠ LA CIBLE SE REDESIGNE : 50078 a ete supprime le 16/09, 50084 l'a remplace.
  //   `--compromis 50084` evite de recopier ce script a chaque essai.
  const compromisId = arg("compromis", CIBLE.compromis_id);

  const jobId = crypto.randomUUID();
  const payload = {
    target_status: "compromise",
    negociateur_email: String(arg("negociateur", "")).trim() || null,
    numero_mandat: CIBLE.numero_mandat,
    selected_mandat: CIBLE.numero_mandat,
    transaction_date: CIBLE.date,
    amount: prix,
    sale_price: prix,
    buyer_contact_id: acquereurs[0] || CIBLE.acquereur,
    // La regle du front, reproduite a l'identique : la cle ne part QU'A PARTIR
    // DE DEUX. En dessous, la charge du cas courant ne change pas d'un octet.
    buyer_contact_ids: acquereurs.length > 1 ? acquereurs : null,
    // ─── LES DEUX NOTAIRES, comme la modale les envoie ───
    notaire_id: notaireAcq || null,
    seller_notary_id: notaireVend || null,
    notaires_affirmes: Object.keys(affirmes).length ? affirmes : null,
    mandant_contact_ids: mandantsAffirmes ? mandants : null,
  };
  if (!creer) {
    payload.reprendre_transaction = true;
    payload.app_affaire_id = CIBLE.app_affaire_id;
    payload.compromis_id = compromisId;
    payload.compromis_state = "active";
  }

  const row = {
    id: jobId,
    job_type: "change_hektor_annonce_status",
    app_dossier_id: CIBLE.app_dossier_id,
    hektor_annonce_id: CIBLE.hektor_annonce_id,
    payload_json: payload,
    priority: 7,
  };

  const r = await fetch(`${URL_SB}/rest/v1/app_console_job`, {
    method: "POST",
    headers: {
      apikey: KEY,
      authorization: `Bearer ${KEY}`,
      "content-type": "application/json",
      prefer: "return=representation",
    },
    body: JSON.stringify(row),
  });
  console.log("statut         ", r.status);
  console.log("job            ", jobId);
  console.log("geste          ", creer ? "CREATION" : `reprise du compromis ${compromisId}`);
  console.log("prix           ", prix);
  console.log("notaire acq.   ", notaireAcq || "(non envoye)");
  console.log("notaire vendeur", notaireVend || "(non envoye)");
  console.log("affirmes       ", JSON.stringify(payload.notaires_affirmes));
  console.log("acquereurs     ", acquereurs.length ? JSON.stringify(acquereurs) : `(defaut ${CIBLE.acquereur})`);
  console.log("mandants       ", mandantsAffirmes ? JSON.stringify(mandants) : "(non affirmes -- Hektor garde les siens)");
  const t = await r.text();
  if (r.status >= 300) console.log(t.slice(0, 400));
})().catch((e) => { console.error(e); process.exit(1); });
