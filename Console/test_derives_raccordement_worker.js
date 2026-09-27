// LE RACCORDEMENT DES DERIVES AU WORKER -- B                          27/09/2026
//
// Jusqu'au 27/09, genererDerivesPhoto n'etait appelee QUE par le script de lot :
// CONSOLE_DERIVES_PHOTO_ENABLED ne commandait donc RIEN. Ce fichier tient le
// raccordement, et surtout LA propriete qui compte :
//
//   ⚠⚠ IL NE DOIT JAMAIS LEVER. persistProvidedPhotoFile est dans le chemin d'un AJOUT
//   DEPUIS L'APP : une exception ferait rejouer le travail, donc RENVOYER la photo a
//   Hektor, qui en aurait DEUX. Un derive manquant se rattrape la nuit suivante ; un
//   doublon chez Hektor, non.
//
// Il fait tourner LA VRAIE fonction du worker. N'APPELLE RIEN : ni Hektor, ni le CDN,
// ni Supabase. N'ECRIT RIEN.

const fs = require("fs");
const path = require("path");

const WORKER = process.env.TEST_WORKER_FILE || path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(WORKER, "utf8");
const FIN = String.fromCharCode(10) + "}";

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}
function tranche(marque) {
  const d = src.indexOf(marque);
  if (d < 0) return null;
  const f = src.indexOf(FIN, d);
  return f < 0 ? null : src.slice(d, f + 2);
}

const bloc = tranche("async function fabriquerDerivesApresRangement(");
if (!bloc) { console.error("fabriquerDerivesApresRangement introuvable -- test non concluant"); process.exit(1); }

// ── le banc : on injecte un faux generateur et un faux interrupteur ────────────
function banc({ allume = true, leve = false } = {}) {
  const appels = [];
  const avertissements = [];
  const genererDerivesPhoto = async (ligne) => {
    appels.push(ligne);
    if (leve) throw new Error("Supabase Storage 504 on gti-photo/...");
    return { derives: {}, coffre: "gti-photo" };
  };
  // eslint-disable-next-line no-new-func
  const fn = new Function("DERIVES_PHOTO_ENABLED", "genererDerivesPhoto", "console",
    `${bloc}; return fabriquerDerivesApresRangement;`)(
    allume, genererDerivesPhoto,
    { warn: (m) => avertissements.push(String(m)), log: () => {} });
  return { fn, appels, avertissements };
}

const ligne = (extra = {}) => ({
  id: "71ff6473-0173-4a47-84d0-221fb05337a4",
  app_dossier_id: 1354344,
  hektor_annonce_id: "100",
  hektor_photo_id: "347",
  filename: "photo.jpg",
  metadata_json: { ancien: "vrai" },
  ...extra,
});
const MASTER = "C:/Hektor/HektorConsoleDocuments/annonces/100/photos/71ff.../photo.jpg";

(async () => {
  console.log("\nLE RACCORDEMENT DES DERIVES AU WORKER\n");

  console.log("① l'interrupteur commande vraiment quelque chose, maintenant");
  {
    const { fn, appels } = banc({ allume: false });
    await fn(ligne(), MASTER, true);
    controle("(a) eteint -> le generateur n'est PAS appele", appels.length === 0, String(appels.length));
  }
  {
    const { fn, appels } = banc({ allume: true });
    await fn(ligne(), MASTER, true);
    controle("(b) allume + annonce vivante -> il EST appele", appels.length === 1, String(appels.length));
  }

  console.log("\n② seules les annonces VIVANTES ont des derives (regle G.8)");
  {
    const { fn, appels } = banc({ allume: true });
    await fn(ligne(), MASTER, false);   // annonce archivee
    controle("(c) annonce non vivante -> rien n'est fabrique", appels.length === 0, String(appels.length));
  }

  console.log("\n③ ⚠⚠ IL NE LEVE JAMAIS -- sinon la photo repart chez Hektor");
  {
    const { fn, appels, avertissements } = banc({ allume: true, leve: true });
    let aLeve = false;
    try { await fn(ligne(), MASTER, true); } catch (_) { aLeve = true; }
    controle("(d) le generateur leve -> le raccordement N'AVALE PAS l'erreur en silence "
      + "mais NE LEVE PAS", !aLeve, "il a leve : le travail serait rejoue et Hektor aurait 2 photos");
    controle("(e) et il le DIT (console.warn)", avertissements.length === 1, String(avertissements.length));
    controle("(f) l'avertissement nomme la photo", avertissements[0] && avertissements[0].includes("71ff6473"),
      avertissements[0] || "-");
    controle("(g) il a bien essaye avant d'echouer", appels.length === 1, String(appels.length));
  }

  console.log("\n④ le chemin du master est celui qu'on VIENT d'ecrire");
  {
    const { fn, appels } = banc({ allume: true });
    await fn(ligne(), MASTER, true);
    controle("(h) local_archive_path est impose",
      appels[0].metadata_json.local_archive_path === MASTER, appels[0].metadata_json.local_archive_path);
    controle("(i) et le reste du metadata_json est preserve",
      appels[0].metadata_json.ancien === "vrai", JSON.stringify(appels[0].metadata_json));
  }

  console.log("\n⑤ ⚠ LES DEUX NUMEROS -- la ligne transmise porte le NOTRE");
  {
    const { fn, appels } = banc({ allume: true });
    await fn(ligne(), MASTER, true);
    controle("(j) app_dossier_id est transmis", Number(appels[0].app_dossier_id) === 1354344,
      String(appels[0].app_dossier_id));
    controle("(k) et l'id de la ligne aussi (il porte l'adresse publique)",
      appels[0].id === "71ff6473-0173-4a47-84d0-221fb05337a4", String(appels[0].id));
  }

  console.log("\n⑥ LES SOURCES : les selects demandent-ils NOTRE numero ?");
  controle("(l) la descente de Hektor le demande",
    /select: "id,app_dossier_id,hektor_annonce_id/.test(src),
    "sans lui, genererDerivesPhoto REFUSE chaque photo descendue");
  controle("(m) le rattrapage differe le demande",
    /select=id,app_dossier_id,hektor_annonce_id/.test(src),
    "sans lui, refus sur chaque photo reprise");
  controle("(n) et le raccordement est appele aux DEUX rangements",
    (src.match(/await fabriquerDerivesApresRangement\(/g) || []).length === 2,
    String((src.match(/await fabriquerDerivesApresRangement\(/g) || []).length));

  console.log(`\n${echecs ? `⛔ ${echecs} controle(s) en echec` : "✅ tout passe"}\n`);
  process.exit(echecs ? 1 : 0);
})();
