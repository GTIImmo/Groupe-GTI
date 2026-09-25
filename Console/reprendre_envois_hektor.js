// REPRENDRE LES DOCUMENTS ET PHOTOS QUI N'ONT PAS PU PARTIR CHEZ HEKTOR
//                                                                  25/09/2026
// Depuis le lot 1, un document ou une photo ajoute depuis l'app EXISTE des sa creation :
// le fichier est sur le serveur, la ligne est dans l'app. L'envoi chez Hektor est un
// ETAT de cette ligne, plus une condition de son existence.
//
//   envoi_hektor_statut = a_envoyer   creee, pas encore partie
//                       = echec       Hektor a refuse ou n'a pas repondu
//                       = envoye      confirmee chez Hektor
//                       = NULL        vient de Hektor, rien a envoyer
//
// CE SCRIPT REMET EN FILE ce qui attend. Il ne parle pas a Hektor lui-meme : il pose
// des travaux, et c'est le worker qui envoie, a sa cadence et derriere son frein.
//
// ⚠ TROIS REFUS, pour ne pas s'acharner :
//   1. une ligne deja en file (pending/running) n'est pas reposee ;
//   2. une ligne retentee il y a moins de RESPIRATION minutes est laissee tranquille --
//      sinon un Hektor indisponible ferait tourner la boucle en continu ;
//   3. une ligne en echec depuis plus de ALERTE heures est SIGNALEE : ce n'est plus un
//      incident passager, quelqu'un doit regarder.
//
//   node Console/reprendre_envois_hektor.js --dry-run
//   node Console/reprendre_envois_hektor.js --appliquer [--limite 50]

const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

const argv = process.argv.slice(2);
const opt = (nom, defaut) => { const i = argv.indexOf(nom); return i >= 0 ? Number(argv[i + 1]) || defaut : defaut; };
const APPLIQUER = argv.includes("--appliquer");
const LIMITE = opt("--limite", 50);
const RESPIRATION = opt("--respiration", 15);   // minutes avant de retenter
const ALERTE = opt("--alerte", 24);             // heures avant de signaler

const SORTES = [
  { nom: "document", table: "app_console_document", cle: "app_document_id",
    travail: "upload_document_to_hektor", libelle: "document_name" },
  { nom: "photo", table: "app_console_photo", cle: "app_photo_id",
    travail: "upload_hektor_photo", libelle: "filename" },
];

async function rest(chemin, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${chemin.replace(/^\/+/, "")}`, {
    ...options,
    headers: { apikey: KEY, Authorization: `Bearer ${KEY}`, "Content-Type": "application/json",
               ...(options.prefer ? { Prefer: options.prefer } : {}) },
  });
  if (!res.ok) throw new Error(`Supabase ${res.status} : ${(await res.text()).slice(0, 200)}`);
  const txt = await res.text();
  return txt ? JSON.parse(txt) : null;
}

// Pagination systematique : sans elle PostgREST plafonne a 1 000 lignes et on croirait
// que les lignes non rendues n'ont rien a envoyer.
async function tout(chemin) {
  const out = [];
  const page = 1000;
  for (let offset = 0; ; offset += page) {
    const rows = await rest(`${chemin}&limit=${page}&offset=${offset}`);
    if (!Array.isArray(rows) || !rows.length) break;
    out.push(...rows);
    if (rows.length < page) break;
  }
  return out;
}

// LE TRI, sorti expres : une fonction pure, donc eprouvable sans Supabase ni Hektor.
// C'est ici que se joue le « on ne s'acharne pas » -- le reste n'est que de la plomberie.
function trier(lignes, enFile, maintenant, { limite, respirationMs, alerteMs, libelle }) {
  const retenus = [];
  const aSignaler = [];
  const stats = { en_attente: lignes.length, deja_en_file: 0, trop_recentes: 0 };
  for (const l of lignes) {
    if (enFile.has(String(l.id))) { stats.deja_en_file += 1; continue; }
    const depuis = l.envoi_hektor_at ? maintenant - Date.parse(l.envoi_hektor_at) : Infinity;
    if (depuis < respirationMs) { stats.trop_recentes += 1; continue; }
    if (l.envoi_hektor_statut === "echec" && depuis > alerteMs) {
      aSignaler.push({ id: l.id, annonce: l.hektor_annonce_id, nom: l[libelle],
                       depuis_h: Math.round(depuis / 3600000), erreur: l.envoi_hektor_erreur });
    }
    if (retenus.length < limite) retenus.push(l);
  }
  return { retenus, aSignaler, stats };
}

(async () => {
  console.log(APPLIQUER ? "MODE : APPLIQUER" : "MODE : A BLANC (ne pose rien)");
  console.log(`respiration ${RESPIRATION} min · alerte apres ${ALERTE} h · limite ${LIMITE}\n`);

  const maintenant = Date.now();
  let posesTotal = 0;
  const aSignaler = [];

  for (const sorte of SORTES) {
    const lignes = await tout(
      `${sorte.table}?select=id,app_dossier_id,hektor_annonce_id,${sorte.libelle},envoi_hektor_statut,envoi_hektor_at,envoi_hektor_erreur`
      + "&envoi_hektor_statut=in.(a_envoyer,echec)&order=envoi_hektor_at.asc.nullsfirst");

    // deja en file : on ne repose pas par-dessus
    const enFile = new Set();
    for (const j of await tout(`app_console_job?select=payload_json&job_type=eq.${sorte.travail}&status=in.(pending,running)`)) {
      const v = j.payload_json && j.payload_json[sorte.cle];
      if (v) enFile.add(String(v));
    }

    const tri = trier(lignes, enFile, maintenant, {
      limite: LIMITE,
      respirationMs: RESPIRATION * 60 * 1000,
      alerteMs: ALERTE * 3600 * 1000,
      libelle: sorte.libelle,
    });
    const { retenus, stats } = tri;
    for (const s of tri.aSignaler) aSignaler.push({ sorte: sorte.nom, ...s });

    console.log(`  ${sorte.nom.padEnd(9)} en attente ${String(stats.en_attente).padStart(4)}`
      + ` · deja en file ${String(stats.deja_en_file).padStart(3)}`
      + ` · trop recentes ${String(stats.trop_recentes).padStart(3)}`
      + ` · A REPOSER ${String(retenus.length).padStart(3)}`);

    if (APPLIQUER && retenus.length) {
      for (let i = 0; i < retenus.length; i += 50) {
        const paquet = retenus.slice(i, i + 50).map((l) => ({
          job_type: sorte.travail,
          app_dossier_id: l.app_dossier_id,
          hektor_annonce_id: String(l.hektor_annonce_id),
          payload_json: { [sorte.cle]: l.id, repris_le: new Date().toISOString() },
          status: "pending",
          priority: 85,
        }));
        await rest("app_console_job", { method: "POST", prefer: "return=minimal", body: JSON.stringify(paquet) });
        posesTotal += paquet.length;
      }
    }
  }

  if (aSignaler.length) {
    console.log(`\n  ⚠ ${aSignaler.length} en echec depuis plus de ${ALERTE} h -- ce n'est plus passager :`);
    for (const s of aSignaler.slice(0, 10)) {
      console.log(`     ${s.sorte} ${s.id} (annonce ${s.annonce}, ${s.nom || "?"}) `
        + `depuis ${s.depuis_h} h : ${String(s.erreur || "").slice(0, 80)}`);
    }
    if (aSignaler.length > 10) console.log(`     ... et ${aSignaler.length - 10} autre(s)`);
  }

  console.log(`\n${APPLIQUER ? `${posesTotal} travail(aux) pose(s).` : "  --dry-run : RIEN n'a ete pose."}`);
  // ⚠ Sortie 1 si des echecs durent : ils DOIVENT se voir dans le Planificateur et dans
  // check_gti_health.py. Un document qui n'arrive jamais chez Hektor, en silence, serait
  // exactement le defaut qu'on cherche a ne plus produire.
  if (aSignaler.length) process.exitCode = 1;
})().catch((e) => { console.error("ERREUR :", e.message); process.exit(2); });
