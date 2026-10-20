// SONDE : ImmoSign sert-il encore le dossier de preuves d'une VIEILLE procedure ?
//                                                                      21/10/2026
// POURQUOI. Le bug du domaine des documents a detruit ~29 dossiers de preuves de
// signature (preuves-N.zip) : ils etaient ranges dans le dossier de la fiche, la fiche
// a ete remplacee, et rien n'est alle les rechercher. Mesure du 21/10, a age egal :
//   anciennes (proc < 400)  fiche RECREEE    32 signes, 29 sans zip -> 90,6 %
//   anciennes               JAMAIS TOUCHEE   46 signes,  0 sans zip ->  0,0 %
// Voir notice/AUDIT_COMMENT_EST_ARRIVE_LE_DOMAINE_DOCUMENTS_2026-10-20.md, partie 5.
//
// LA SEULE INCONNUE : ImmoSign sert-il encore ces vieilles procedures ? Le worker
// ecrit lui-meme qu'elles sont « IMMUABLES une fois la procedure creee » (l. 5295),
// et 388 autres repondent -- mais ca n'a jamais ete verifie sur les 29 perdues.
//
// ELLE SE LEVE AVEC UN SEUL APPEL. C'est tout l'objet de cette sonde.
//
// ⛔ CE QU'ELLE NE FAIT PAS : aucune ecriture en base, aucune ecriture chez Hektor,
//   rien dans l'archive du serveur. Le ZIP est ecrit dans --out et nulle part ailleurs.
// ⚠ ELLE FAIT EXACTEMENT UN APPEL A HEKTOR (ou autant que de --procedure passees).
//   Le mur de Hektor est un quota de VOLUME et notre IP a ete bannie les 19-20/08 :
//   on ne la lance pas en boucle, et on ne rejoue JAMAIS un refus.
//
//   node Console/sonde_preuves_immosign.js --procedure=33 --out=C:\chemin\sortie
//
// Sortie 0 = le ZIP est revenu (recuperable) · 1 = Hektor n'a pas livre de ZIP
// (le detail dit quoi) · 2 = on n'a pas pu mesurer (session, configuration).
//
// ⭐⭐ EPROUVEE EN REEL LE 21/10 SUR LA PROCEDURE 33 -- la PLUS ANCIENNE des 29
//   (annonce 61578, signee le 03/03/2026), donc le cas le plus dur :
//       HTTP 200   application/zip   172 435 octets
//       archive lisible, 3 entrees : « Signature du document Mandat Avec saisie du
//       numero Vente (audit trail for <signataire>).pdf » -- les DEUX MANDANTS et
//       le NEGOCIATEUR, ~84 ko chacun.
//   ➡ ImmoSign sert encore les vieilles procedures : LES 29 SONT RECUPERABLES.
// ⚠ A NOTER, et c'est honnete de le dire : les PDF portent la date du jour de la
//   demande. ImmoSign les RECONSTRUIT donc a la demande depuis la procedure. On
//   recupere un dossier EQUIVALENT, pas les octets d'origine -- ce qui est au
//   passage une meilleure nouvelle, puisque rien ne peut « perimer » comme le
//   ferait un fichier stocke.

const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });

const args = Object.fromEntries(
  process.argv.slice(2).filter((x) => x.startsWith("--")).map((x) => {
    const [k, ...v] = x.slice(2).split("=");
    return [k, v.join("=") || "1"];
  }));

const HEKTOR_BASE_URL = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${HEKTOR_BASE_URL.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;

// La session du worker DOCUMENTS : c'est lui qui porterait le vrai travail.
const STORAGE_STATE_PATH = args.session
  || process.env.CONSOLE_STORAGE_STATE_PATH
  || path.resolve(__dirname, "sessions", "storage_state_documents.json");

const procedures = String(args.procedure || args.procedures || "").split(",").map((s) => s.trim()).filter(Boolean);
const outDir = args.out || path.resolve(__dirname, "..", "..", "sonde_preuves");

if (!procedures.length) {
  console.log("ARRET : passer --procedure=33 (ou --procedure=33,40).");
  process.exit(2);
}

function cookieHeader() {
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    console.log(`ARRET : session introuvable -> ${STORAGE_STATE_PATH}`);
    process.exit(2);
  }
  const state = JSON.parse(fs.readFileSync(STORAGE_STATE_PATH, "utf-8"));
  const cookies = Array.isArray(state.cookies) ? state.cookies : [];
  const now = Date.now() / 1000;
  const vivants = cookies.filter((c) => !c.expires || c.expires < 0 || c.expires > now);
  if (!vivants.length) {
    console.log("ARRET : la session ne porte aucun cookie valide.");
    process.exit(2);
  }
  return vivants.map((c) => `${c.name}=${c.value}`).join("; ");
}

(async () => {
  console.log("=".repeat(74));
  console.log("SONDE : le dossier de preuves d'une vieille procedure revient-il ?");
  console.log(`  domaine  : ${HEKTOR_BASE_URL}`);
  console.log(`  session  : ${path.basename(STORAGE_STATE_PATH)}`);
  console.log(`  appels   : ${procedures.length}  (procedure${procedures.length > 1 ? "s" : ""} ${procedures.join(", ")})`);
  console.log("=".repeat(74));

  const Cookie = cookieHeader();
  fs.mkdirSync(outDir, { recursive: true });
  let recuperables = 0;

  for (const proc of procedures) {
    const url = `${XMLRPC_URL}?mode=ImmoSign-downloadProofsByProcedure&procedureId=${encodeURIComponent(proc)}`;
    console.log(`\nprocedure ${proc}`);
    let res;
    try {
      res = await fetch(url, {
        headers: {
          Cookie,
          Referer: ADMIN_URL,
          Origin: HEKTOR_BASE_URL.replace(/\/+$/, ""),
          "X-Requested-With": "XMLHttpRequest",
          Accept: "*/*",
        },
      });
    } catch (error) {
      console.log(`  ⛔ l'appel n'a pas abouti : ${error.message}`);
      continue;
    }

    const buffer = Buffer.from(await res.arrayBuffer());
    const type = res.headers.get("content-type") || "(aucun)";
    console.log(`  HTTP ${res.status}   type « ${type} »   ${buffer.length} octets`);

    // ⚠ 429/503 = Hektor nous ecarte. On ne rejoue pas, on s'arrete.
    if (res.status === 429 || res.status === 503) {
      console.log("  ⛔ HEKTOR NOUS ECARTE. NE RIEN REJOUER. On s'arrete ici.");
      process.exitCode = 1;
      return;
    }

    // La signature d'un vrai ZIP : "PK\x03\x04" = 0x04034b50 en petit-boutien.
    const estUnZip = buffer.length >= 4 && buffer.readUInt32LE(0) === 0x04034b50;
    if (estUnZip) {
      const cible = path.join(outDir, `preuves-${proc}.zip`);
      fs.writeFileSync(cible, buffer);
      console.log(`  ✅ C'EST UN VRAI ZIP -- ImmoSign sert encore cette procedure.`);
      console.log(`     ecrit dans ${cible}`);
      recuperables += 1;
    } else {
      const apercu = buffer.toString("utf-8").replace(/\s+/g, " ").slice(0, 220);
      console.log("  ⛔ CE N'EST PAS UN ZIP. Les 220 premiers caracteres de la reponse :");
      console.log(`     ${apercu || "(corps vide)"}`);
      if (/connexion|login|identifiant|password/i.test(apercu)) {
        console.log("     ➡ ca ressemble a une PAGE DE CONNEXION : la session est perdue,");
        console.log("       ce n'est donc PAS une preuve que la procedure a disparu.");
      }
    }
  }

  console.log("\n" + "=".repeat(74));
  console.log(`VERDICT : ${recuperables} procedure(s) sur ${procedures.length} ont rendu un vrai ZIP.`);
  console.log("=".repeat(74));
  // ⚠ PAS de process.exit() ici : appele pendant que la connexion fetch se referme, il
  //   fait planter libuv sur Windows (« Assertion failed: !(handle->flags &
  //   UV_HANDLE_CLOSING) ») et rend 127 -- un CODE DE SORTIE MENTEUR, alors que le
  //   travail s'est parfaitement passe. Vecu le 21/10 au premier essai reel.
  //   On pose exitCode et on laisse Node se terminer proprement.
  process.exitCode = recuperables === procedures.length ? 0 : 1;
})();
