// MENAGE DU COFFRE DES DOCUMENTS -- les fichiers dont la fiche n'existe plus
//                                                                      21/10/2026
// ════════════════════════════════════════════════════════════════════════════════
// POURQUOI. Le bug du domaine (corrige le 20/10 a 20:30) remplacait une fiche de
// document au lieu de la reconnaitre : 15 403 fiches remplacees. Chaque remplacement
// a laisse son fichier derriere lui dans le coffre, dans un dossier que plus aucune
// fiche ne lit. Mesure du 21/10 : 5 091 fichiers, 7 120 Mo.
// Audit complet : notice/AUDIT_MENAGE_COFFRE_DOCUMENTS_2026-10-21.md
//
// ⚠⚠ CE SCRIPT SUPPRIME DES FICHIERS DU COFFRE, ET C'EST IRREVERSIBLE.
//   Il ne reste alors que la copie du SERVEUR (C:\Hektor\HektorConsoleDocuments),
//   qui porte tout (461 Go). Il n'y a PAS de rehydratation possible pour ces
//   fichiers : prepare_document_cloud part d'une FICHE, et ils n'en ont plus.
//   ⭐ En revanche, et c'est ce qui rend le geste sans danger pour l'app : AUCUN
//     ECRAN NE PEUT LES DEMANDER, justement parce qu'aucune fiche ne les porte.
//
// ────────────────────────────────────────────────────────────────────────────────
// LES TROIS GARDE-FOUS, ET ILS SONT REVERIFIES JUSTE AVANT CHAQUE SUPPRESSION
// ────────────────────────────────────────────────────────────────────────────────
// ⭐⭐ LA LISTE N'EST QU'UNE LISTE DE CANDIDATS. Frederic a signale le 21/10 que le
//   run de 5 h tournait : pendant un run, des fiches naissent et meurent, donc une
//   liste gelee PERIME. Le script ne lui fait donc pas confiance : pour chaque
//   fichier, il interroge la base AU MOMENT DE SUPPRIMER, et passe son tour si l'un
//   des trois garde-fous a change d'avis.
//
//   (1) LE DOSSIER N'EST PLUS UNE FICHE VIVANTE.
//       Le chemin est annonces/<annonce>/documents/<ID-DE-LA-FICHE>/<nom>. Si cet
//       identifiant est encore une ligne de app_console_document, ON NE TOUCHE PAS.
//       ⭐ C'est CE garde-fou qui protege les 1 129 fichiers COMPAGNONS (774 Mo) --
//         dont les ZIP de preuves de signature et les PDF signes, qui vivent DANS le
//         dossier de la fiche mais ne sont PAS la valeur de storage_path, donc
//         paraissent orphelins alors qu'ils ne le sont pas.
//
//   (2) NI immosign/, NI signed/, NI temp/.
//       Ceinture par-dessus (1). Et temp/ a deja ete traite le 14/10 (chemin bouche,
//       0 fichier aujourd'hui) : voir Console/test_nettoyage_temporaire.js.
//
//   (3) LE MEME NOM EST ENCORE PORTE PAR UNE FICHE VIVANTE DE LA MEME ANNONCE.
//       C'est la preuve que le fichier est un DOUBLON et pas la derniere copie d'un
//       document. ⚠ 988 fichiers (1 606 Mo) NE passent PAS ce garde-fou : ce sont des
//       documents reellement retires chez Hektor. Ils sont DELIBEREMENT hors lot --
//       decision de Frederic, pas la mienne.
//
// ⛔ ET UN QUATRIEME, QUI VIENT DE LUI : LE SCRIPT REFUSE DE TOURNER SI LE RUN DE
//   NUIT (« GTI Quotidien ») EST EN COURS. Meme esprit que « ne redemarrer un service
//   que file vide » : on ne touche pas au coffre pendant qu'un run y ecrit.
//   --meme-si-le-run-tourne passe outre, et il faut une bonne raison.
//
// ────────────────────────────────────────────────────────────────────────────────
//   node Console/menage_coffre_documents.js --blanc            (par defaut : ne supprime RIEN)
//   node Console/menage_coffre_documents.js --supprimer --limite=100
//   node Console/menage_coffre_documents.js --supprimer
//
//   --liste=<fichier.csv>   la liste des candidats (defaut : notice/MENAGE_COFFRE_LOT1_<date>.csv)
//   --limite=N              s'arrete apres N suppressions
//   --blanc                 verifie et compte, ne supprime pas (defaut)
//   --supprimer             supprime pour de vrai
//   --meme-si-le-run-tourne passe outre le garde-fou n°4
//
// Sortie 0 = tout s'est bien passe · 1 = au moins un refus ou une erreur ·
//        2 = il n'a pas pu travailler (liste, configuration, run en cours).
// ════════════════════════════════════════════════════════════════════════════════

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");
// ⚠ LES MEMES QUATRE FICHIERS QUE LE WORKER, dans le meme ordre (l. 10-13 de
//   console_job_worker.js). N'en charger que deux suffit a ne pas trouver
//   SUPABASE_URL : il vit dans apps/hektor-v1/.env. Vecu le 21/10 au 1er lancement.
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "matterport", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const args = Object.fromEntries(
  process.argv.slice(2).filter((x) => x.startsWith("--")).map((x) => {
    const [k, ...v] = x.slice(2).split("=");
    return [k, v.join("=") || "1"];
  }));

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const CLE = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
const COFFRE = process.env.CONSOLE_STORAGE_BUCKET || "hektor-console-documents";
const SUPPRIME = args.supprimer === "1" && args.blanc !== "1";
const LIMITE = args.limite ? Number(args.limite) : Infinity;
const RACINE = path.resolve(__dirname, "..");

if (!SUPABASE_URL || !CLE) {
  console.log("ARRET : SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY introuvable.");
  process.exit(2);
}

// ── GARDE-FOU n°4 : le run de nuit ne doit pas tourner ──────────────────────────
// ⚠⚠ NE PAS LIRE LE TEXTE DE schtasks. Vecu le 21/10 : ma premiere version faisait
//   `schtasks /query /FO LIST` et cherchait « Running » -- or schtasks repond EN
//   FRANCAIS et dans un jeu de caracteres different, donc le motif ne mordait pas :
//   LA GARDE DISAIT « le run ne tourne pas » ALORS QU'IL TOURNAIT. Une garde qui
//   rassure sans proteger est pire que pas de garde.
// ⭐ Get-ScheduledTask rend un ETAT ENUMERE dont le nom est « Running » quelle que
//   soit la langue de Windows. On compare ca, et on n'imprime qu'un mot a nous.
function leRunTourne() {
  try {
    const sortie = execSync(
      'powershell -NoProfile -Command "$t = Get-ScheduledTask -TaskName \'GTI Quotidien\' '
      + '-ErrorAction Stop; if ($t.State -eq \'Running\') { \'OUI\' } else { \'NON\' }"',
      { encoding: "utf8" }).trim();
    if (sortie === "OUI") return true;
    if (sortie === "NON") return false;
    return null;            // reponse inattendue : on ne devine pas
  } catch (_e) {
    return null;            // on n'a pas pu savoir
  }
}

// ── les helpers base et coffre ──────────────────────────────────────────────────
const ENTETES = { apikey: CLE, Authorization: `Bearer ${CLE}` };

async function base(chemin) {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${chemin}`, { headers: ENTETES });
  if (!r.ok) throw new Error(`base ${r.status} sur ${chemin} : ${(await r.text()).slice(0, 200)}`);
  return r.json();
}

function encoderChemin(valeur) {
  return String(valeur).split("/").map(encodeURIComponent).join("/");
}

async function supprimerDuCoffre(chemin) {
  const r = await fetch(`${SUPABASE_URL}/storage/v1/object/${COFFRE}/${encoderChemin(chemin)}`,
    { method: "DELETE", headers: ENTETES });
  if (!r.ok) throw new Error(`coffre ${r.status} : ${(await r.text()).slice(0, 200)}`);
}

// ── les trois garde-fous, revérifiés POUR CE FICHIER, MAINTENANT ────────────────
async function pourquoiOnNeTouchePas(chemin) {
  const bouts = chemin.split("/");
  // annonces / <annonce> / documents / <id de fiche> / <reste...>
  if (bouts[0] !== "annonces" || bouts[2] !== "documents" || bouts.length < 5) {
    return "forme de chemin inattendue";
  }
  const annonce = bouts[1];
  const idFiche = bouts[3];
  const reste = bouts.slice(4).join("/");

  // (2) la ceinture, d'abord : elle ne coute aucun appel
  if (reste.startsWith("immosign/") || reste.startsWith("signed/")) return "compagnon (immosign/ ou signed/)";
  if (bouts[0] === "temp") return "temporaire -- traite le 14/10, on n'y touche pas";

  // (1) le dossier est-il encore une fiche VIVANTE ?
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(idFiche)) {
    return "l'identifiant du dossier n'est pas une fiche";
  }
  const fiche = await base(`app_console_document?id=eq.${idFiche}&select=id&limit=1`);
  if (fiche.length) return "SA FICHE EST VIVANTE -- c'est un compagnon, pas un dechet";

  // ⚠ et le chemin exact est-il reclame par une fiche (meme sous un autre dossier) ?
  const reclame = await base(
    `app_console_document?storage_path=eq.${encodeURIComponent(chemin)}&select=id&limit=1`);
  if (reclame.length) return "une fiche reclame EXACTEMENT ce chemin";

  // (3) le meme NOM est-il encore porte par une fiche vivante de la meme annonce ?
  const nom = bouts[bouts.length - 1];
  const jumelles = await base(
    `app_console_document?hektor_annonce_id=eq.${encodeURIComponent(annonce)}`
    + `&storage_path=like.*${encodeURIComponent("/" + nom)}&select=id&limit=1`);
  if (!jumelles.length) {
    return "AUCUNE fiche de l'annonce ne porte ce nom -- ce serait la DERNIERE COPIE (lot 2)";
  }
  return null;   // les trois garde-fous sont d'accord : c'est un doublon
}

(async () => {
  console.log("=".repeat(78));
  console.log("MENAGE DU COFFRE DES DOCUMENTS");
  console.log(`  coffre : ${COFFRE}`);
  console.log(`  mode   : ${SUPPRIME ? "⚠ SUPPRESSION REELLE" : "EN BLANC (rien ne sera supprime)"}`);
  if (LIMITE !== Infinity) console.log(`  limite : ${LIMITE} fichier(s)`);
  console.log("=".repeat(78));

  // ── garde-fou n°4 ─────────────────────────────────────────────────────────────
  const tourne = leRunTourne();
  if (tourne === null) {
    console.log("\n⚠ je n'ai pas pu savoir si « GTI Quotidien » tourne (schtasks indisponible).");
    if (SUPPRIME && args["meme-si-le-run-tourne"] !== "1") {
      console.log("⛔ ARRET : je ne supprime pas sans savoir. Relance avec --meme-si-le-run-tourne");
      console.log("   si tu es sur que le run est fini.");
      process.exitCode = 2; return;
    }
  } else if (tourne) {
    console.log("\n⛔ « GTI Quotidien » EST EN COURS.");
    console.log("   Pendant un run, des fiches naissent et meurent : une liste perime, et on");
    console.log("   ne touche pas au coffre pendant qu'un run y ecrit. Le run finit d'habitude");
    console.log("   entre 07:03 et 07:34.");
    if (SUPPRIME && args["meme-si-le-run-tourne"] !== "1") {
      console.log("⛔ ARRET. (--meme-si-le-run-tourne passe outre, et il faut une bonne raison.)");
      process.exitCode = 2; return;
    }
    console.log("   ⚠ On continue EN BLANC : lire pendant le run ne derange personne.");
  } else {
    console.log("\n✅ « GTI Quotidien » ne tourne pas.");
  }

  // ── la liste de candidats ─────────────────────────────────────────────────────
  const parDefaut = path.join(RACINE, "notice",
    `MENAGE_COFFRE_LOT1_${new Date().toISOString().slice(0, 10)}.csv`);
  const fichierListe = args.liste ? path.resolve(args.liste) : parDefaut;
  if (!fs.existsSync(fichierListe)) {
    console.log(`\n⛔ ARRET : la liste de candidats est introuvable.`);
    console.log(`   attendue ici : ${fichierListe}`);
    console.log(`   Elle se fabrique APRES le run, depuis storage.objects, et elle est`);
    console.log(`   DATEE : c'est elle la trace de ce qui a ete propose a la suppression.`);
    process.exitCode = 2; return;
  }
  const lignes = fs.readFileSync(fichierListe, "utf8").split(/\r?\n/)
    .map((l) => l.trim()).filter((l) => l && !l.startsWith("#") && l !== "chemin");
  console.log(`\nliste   : ${path.basename(fichierListe)}  (${lignes.length} candidat(s))`);

  // ── le travail ────────────────────────────────────────────────────────────────
  const journal = [];
  let supprimes = 0, refuses = 0, erreurs = 0;
  const motifs = new Map();

  for (const chemin of lignes) {
    if (supprimes >= LIMITE) break;
    let motif;
    try {
      motif = await pourquoiOnNeTouchePas(chemin);
    } catch (e) {
      erreurs += 1;
      console.log(`  ⛔ ${chemin}\n     la verification a echoue : ${e.message}`);
      continue;
    }
    if (motif) {
      refuses += 1;
      motifs.set(motif, (motifs.get(motif) || 0) + 1);
      journal.push(`REFUSE;${chemin};${motif}`);
      continue;
    }
    if (!SUPPRIME) { supprimes += 1; journal.push(`A SUPPRIMER;${chemin};`); continue; }
    try {
      await supprimerDuCoffre(chemin);
      supprimes += 1;
      journal.push(`SUPPRIME;${chemin};`);
      if (supprimes % 50 === 0) console.log(`  ... ${supprimes} supprime(s)`);
    } catch (e) {
      erreurs += 1;
      console.log(`  ⛔ ${chemin}\n     la suppression a echoue : ${e.message}`);
    }
  }

  // ── le compte rendu, et la trace ──────────────────────────────────────────────
  console.log("\n" + "=".repeat(78));
  console.log(SUPPRIME ? `SUPPRIMES          : ${supprimes}` : `A SUPPRIMER        : ${supprimes}`);
  console.log(`REFUSES par un garde-fou : ${refuses}`);
  for (const [m, n] of [...motifs.entries()].sort((a, b) => b[1] - a[1])) {
    console.log(`   ${String(n).padStart(5)}  ${m}`);
  }
  console.log(`ERREURS            : ${erreurs}`);

  const trace = path.join(RACINE, "notice",
    `MENAGE_COFFRE_TRACE_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.csv`);
  fs.writeFileSync(trace, "geste;chemin;motif\n" + journal.join("\n") + "\n", "utf8");
  console.log(`\ntrace ecrite : ${path.relative(RACINE, trace)}`);
  console.log("=".repeat(78));

  // ⚠ pas de process.exit() : appele pendant qu'une connexion fetch se referme, il
  //   fait planter libuv sur Windows et rend un code MENTEUR (vecu le 21/10).
  process.exitCode = (erreurs || (SUPPRIME && supprimes === 0 && lignes.length)) ? 1 : 0;
})();
