/**
 * ESSAI REEL DE LA VENTE — la verification que la tache 3.2e reclame  13/09/2026
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * CE QUE 3.2e DEMANDE, MOT POUR MOT : « une vente creee ET modifiee depuis l'app,
 * relue chez Hektor, avec le meme journal de preuve que le compromis 50078 ».
 * Le seul essai reussi datait du 08/09 (vente 23301) -- donc AVANT le retrait du
 * carnet apres preuve (11/09), AVANT l'ecriture du registre a chaud (12/09) et
 * AVANT l'attribution de la commission (13/09). La vente n'a jamais parcouru la
 * chaine complete.
 *
 * ⚠⚠ IL ECRIT CHEZ HEKTOR, ET IL CREE UNE VRAIE VENTE. Sur le bien de TEST
 *   24933 uniquement, deja porteur de sept ventes d'essai creees puis supprimees
 *   (23289, 23291, 23292, 23293, 23294, 23298, 23299, 23301) sans dommage.
 *   La creation passe l'annonce en « Vendu » et clot son mandat -- c'est le
 *   comportement normal, et `--supprimer` remet tout en place.
 *
 * ⭐ CE QUE CET ESSAI REPOND, ET QU'AUCUN AUTRE NE PEUT REPONDRE. Le correctif du
 *   13/09 attribue la commission a « celui que Hektor propose ». Sur 24933, en
 *   session administrateur, il propose PEREIRA (51) -- qui n'est PAS le
 *   negociateur du dossier (GONZALEZ). Les trois essais du 13/09 ont tous tourne
 *   en session administrateur, et le troisieme n'a rien pu dire de plus : le
 *   compromis portait DEJA ses intervenants, donc la garde a (correctement)
 *   empeche d'y toucher.
 *   ➡ UNE VENTE NEUVE N'EN PORTE AUCUN. La ligne `hektor_commission` de son
 *     journal nommera donc, enfin, celui que Hektor propose DANS LES CONDITIONS
 *     REELLES. C'est la seule facon de savoir si la bonne personne est payee.
 *
 * ⚠ ON PASSE PAR LE RPC, PAS PAR UN INSERT. `app_change_annonce_status_optimistic`
 *   cree l'affaire ET le travail dans la MEME transaction, et le travail emporte
 *   le numero d'affaire. Inserer le travail a la main sauterait cette etape : la
 *   vente naitrait chez Hektor sans exister chez nous, et la reconciliation en
 *   fabriquerait une seconde. C'est le correctif C.4 du 25/08, on ne le contourne
 *   pas pour un essai -- sinon on eprouve un chemin que personne n'emprunte.
 *
 * ⚠ LA DATE ENVOYEE EST CELLE DU JOUR, ET C'EST DELIBERE. La modale propose
 *   aujourd'hui la date du COMPROMIS (04/09) la ou Hektor propose le jour : c'est
 *   un defaut deja mesure et ecrit au plan, qui sera corrige a part. Fabriquer
 *   ici une vente mal datee ne prouverait rien de plus et salirait l'essai.
 *
 *   node Console/test_worker_vente.js                      (creer)
 *   node Console/test_worker_vente.js --prix 185000
 *   node Console/test_worker_vente.js --supprimer 23305    (retour arriere)
 */
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const URL_SB = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// La cible, relevee dans le registre le 13/09. Le prix et le net viennent du
// compromis 50078 -- c'est exactement ce que l'heritage de la modale reprend.
const CIBLE = {
  app_dossier_id: 1352132,
  hektor_annonce_id: "24933",
  numero_mandat: "11939",
  acquereur: "605030",
  prix: "184000",
  net_vendeur: "174000",
  honoraires_entree: "10000.00",
};

function arg(nom, defaut) {
  const t = process.argv.find((a) => a.startsWith(`--${nom}=`) || a === `--${nom}`);
  if (!t) return defaut;
  if (t.includes("=")) return t.split("=")[1];
  return process.argv[process.argv.indexOf(t) + 1] || defaut;
}

async function appelSupabase(chemin, corps) {
  const r = await fetch(`${URL_SB}${chemin}`, {
    method: "POST",
    headers: { apikey: KEY, authorization: `Bearer ${KEY}`,
               "content-type": "application/json", prefer: "return=representation" },
    body: JSON.stringify(corps),
  });
  const t = await r.text();
  return { statut: r.status, texte: t };
}

(async () => {
  if (!URL_SB || !KEY) { console.error("Manque SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY"); process.exit(1); }

  // ─── LE RETOUR ARRIERE, ECRIT AVANT L'ALLER ───
  // Une vente n'a AUCUN etat chez Hektor : elle ne s'annule pas, elle DISPARAIT.
  // Le worker exige donc `confirmer` explicitement, et on le lui donne ici parce
  // que c'est le geste demande -- jamais par defaut.
  const aSupprimer = String(arg("supprimer", "")).trim();
  if (aSupprimer) {
    if (!/^\d+$/.test(aSupprimer)) { console.error("--supprimer attend un numero de vente"); process.exit(1); }
    const crypto = require("crypto");
    const jobId = crypto.randomUUID();
    const r = await appelSupabase("/rest/v1/app_console_job", {
      id: jobId,
      job_type: "delete_hektor_vente",
      app_dossier_id: CIBLE.app_dossier_id,
      hektor_annonce_id: CIBLE.hektor_annonce_id,
      payload_json: { hektor_vente_id: aSupprimer, confirmer: true },
      priority: 7,
    });
    console.log("statut ", r.statut);
    console.log("job    ", jobId);
    console.log("SUPPRESSION DEFINITIVE de la vente", aSupprimer, "-- rien ne la remet.");
    if (r.statut >= 300) console.log(r.texte.slice(0, 400));
    return;
  }

  const prix = String(arg("prix", CIBLE.prix)).trim();
  if (!/^\d+$/.test(prix)) { console.error("--prix doit etre un nombre entier"); process.exit(1); }
  const jour = new Date();
  const date = `${jour.getFullYear()}-${String(jour.getMonth() + 1).padStart(2, "0")}`
    + `-${String(jour.getDate()).padStart(2, "0")}`;

  // La charge que la modale « Vendu » construit, champ pour champ (api.ts).
  // ⚠ PAS DE `reprendre_transaction` NI DE `vente_id` : c'est une CREATION. La
  //   charge de la modale porte toujours le courant du dossier, et c'est
  //   precisement pour cela que le worker exige l'INTENTION avant de reprendre.
  const payload = {
    target_status: "sold",
    amount: prix,
    sale_price: prix,
    transaction_date: date,
    numero_mandat: CIBLE.numero_mandat,
    selected_mandat: CIBLE.numero_mandat,
    buyer_contact_id: CIBLE.acquereur,
    buyer_contact_ids: null,
    net_seller_price: CIBLE.net_vendeur,
    close_mandat_on_sale: true,
    apres_vente: "actif",          // arbitrage de Frederic du 01/09 : on n'archive pas
    close_price: prix,
    close_etat: "choiceAutre",
    close_raison: "autre",
    // Vide des deux cotes = on laisse le worker prendre CE QUE HEKTOR PROPOSE.
    // C'est tout l'objet de cet essai : lire ce nom dans le journal.
    intervenant_entree_id: String(arg("intervenant-entree", "")).trim() || null,
    intervenant_sortie_id: String(arg("intervenant-sortie", "")).trim() || null,
  };

  const r = await appelSupabase("/rest/v1/rpc/app_change_annonce_status_optimistic", {
    target_dossier_id: CIBLE.app_dossier_id,
    target_status: "sold",
    job_payload: payload,
    job_priority: 7,
  });
  console.log("statut  ", r.statut);
  if (r.statut >= 300) { console.log(r.texte.slice(0, 600)); process.exit(1); }
  let rep = null; try { rep = JSON.parse(r.texte); } catch (_) {}
  const info = Array.isArray(rep) ? rep[0] : rep;
  console.log("job     ", (info && info.job_id) || "(non rendu)");
  console.log("affaire ", (info && (info.app_affaire_id || info.affaire_id)) || "(non rendu)");
  console.log("prix    ", prix, "  date", date, "  acquereur", CIBLE.acquereur);
  console.log("");
  console.log("A LIRE DANS LE JOURNAL : la ligne `hektor_commission` -- elle nomme");
  console.log("celui que Hektor propose dans les conditions reelles.");
  console.log("Retour arriere : node Console/test_worker_vente.js --supprimer <numero>");
})().catch((e) => { console.error(e); process.exit(1); });
