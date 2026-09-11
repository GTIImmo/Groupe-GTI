// TEST DE REPRISE DU WORKER : modifier le PRIX d'un compromis, rien d'autre.
//                                                                  11/09/2026
// Pourquoi ce script existe : apres la bascule de domaine du 11/09, il fallait
// prouver que le worker ECRIT encore chez Hektor, pas seulement qu'il lit. Le
// maintien de session prouve la lecture ; seul un vrai travail prouve l'ecriture.
//
// ⚠ IL ECRIT CHEZ HEKTOR. Sur le compromis de TEST 50078 (annonce 24933), deja
//   modifie quatre fois le 08/09 sans dommage.
//
// ⚠ ON ENVOIE L'ACQUEREUR MEME SI ON NE LE CHANGE PAS. Mesure du 10/09 : sans
//   `acquereurs[]`, l'assistant de Hektor refuse d'avancer et repond pourtant
//   `success: true` -- un enregistrement part alors dans le vide.
//
// ⚠ ON N'ENVOIE PAS le net vendeur : ce qu'on ne pose pas, Hektor le CONSERVE.
//   « Ne rien poser = conserver » est le principe de tout l'assistant.
//
//   node Console/test_worker_prix_compromis.js --prix 178000
//   node Console/test_worker_prix_compromis.js --prix 177000    (pour revenir)

const path = require("path");
const crypto = require("crypto");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const URL_SB = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// La cible, relevee dans le registre le 11/09.
const CIBLE = {
  app_dossier_id: 1352132,
  hektor_annonce_id: "24933",
  app_affaire_id: 1001347,
  compromis_id: "50078",
  numero_mandat: "11939",
  acquereur: "605030",
  date: "2026-09-04",
};

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
  const prix = String(arg("prix", "178000")).trim();
  if (!/^\d+$/.test(prix)) {
    console.error("--prix doit etre un nombre entier");
    process.exit(1);
  }

  const jobId = crypto.randomUUID();
  const row = {
    id: jobId,
    job_type: "change_hektor_annonce_status",
    app_dossier_id: CIBLE.app_dossier_id,
    hektor_annonce_id: CIBLE.hektor_annonce_id,
    // Cette charge est celle que `app_modifier_affaire_optimistic` aurait
    // construite : elle porte l'INTENTION (`reprendre_transaction`) *et* la
    // CIBLE (`compromis_id`). Sans les deux, le worker CREE au lieu de modifier
    // -- c'est ce qui a fabrique l'affaire 1001350 ce matin.
    payload_json: {
      target_status: "compromise",
      reprendre_transaction: true,
      app_affaire_id: CIBLE.app_affaire_id,
      compromis_id: CIBLE.compromis_id,
      compromis_state: "active",
      numero_mandat: CIBLE.numero_mandat,
      selected_mandat: CIBLE.numero_mandat,
      transaction_date: CIBLE.date,
      amount: prix,
      sale_price: prix,
      buyer_contact_id: CIBLE.acquereur,
    },
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
  console.log("statut  ", r.status);
  console.log("job     ", jobId);
  console.log("prix    ", prix, "  sur le compromis", CIBLE.compromis_id);
  const t = await r.text();
  if (r.status >= 300) console.log(t.slice(0, 400));
})().catch((e) => { console.error(e); process.exit(1); });
