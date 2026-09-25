// RATTRAPAGE : REMETTRE LE VRAI MANDAT A LA PLACE DE SON ANNEXE
//                                                                  25/09/2026
// TROUVE PAR FREDERIC : dans l'app, sous le nom « Mandat », certaines annonces
// n'affichaient que l'ANNEXE (« informations precontractuelles ») ou le BAREME
// d'honoraires. Verifie en ouvrant les PDF : 3 a 8 pages au lieu de 11.
//
// LA CAUSE (corrigee le meme jour dans extractPdfFromZip) : l'archive d'une
// procedure ImmoSign contient DEUX pdf -- le document signe et son annexe --
// et le worker prenait LE PREMIER. L'annexe y precede souvent le mandat.
//
// ⚠⚠ CE RATTRAPAGE NE DEMANDE RIEN A HEKTOR.
//    Le vrai mandat est DEJA sur le serveur, dans immosign_procedure-NNN.zip,
//    telecharge en meme temps que l'annexe. On l'extrait, c'est tout.
//    -> aucun risque de bannissement, aucune cadence a respecter.
//
// CE QU'IL ECRIT : le fichier sur le serveur, l'objet dans Supabase Storage, et
// la ligne app_console_document (storage_path, file_size, sha256, metadata).
// L'ANCIEN PDF N'EST JAMAIS EFFACE : il reste a cote, et son chemin est garde
// dans metadata_json.annexe_ecartee -- on peut donc revenir en arriere.
//
//   node Console/rattrapage_mandat_signe.js --dry-run     <- n'ecrit RIEN
//   node Console/rattrapage_mandat_signe.js --appliquer
//   node Console/rattrapage_mandat_signe.js --appliquer --limite 5

const fs = require("fs");
const path = require("path");
const zlib = require("zlib");
const crypto = require("crypto");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const BUCKET = "hektor-console-documents";
const ANNEXE = /(annexe|bareme)/i;

const argv = process.argv.slice(2);
const APPLIQUER = argv.includes("--appliquer");
const LIMITE = (() => {
  const i = argv.indexOf("--limite");
  return i >= 0 ? Number(argv[i + 1]) || 0 : 0;
})();

if (!SUPABASE_URL || !SERVICE_KEY) {
  console.error("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.");
  process.exit(2);
}

async function rest(chemin, options = {}) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${chemin}`, {
    ...options,
    headers: {
      apikey: SERVICE_KEY,
      Authorization: `Bearer ${SERVICE_KEY}`,
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`REST ${res.status} sur ${chemin.slice(0, 60)}`);
  const t = await res.text();
  return t ? JSON.parse(t) : null;
}

// ── extraction : LA MEME REGLE que le worker (prouvee sur 279 archives) ──────
function pdfsDuZip(buf) {
  if (!Buffer.isBuffer(buf) || buf.length < 22) throw new Error("ZIP vide/invalide");
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 22 - 65536); i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("ZIP EOCD introuvable");
  const count = buf.readUInt16LE(eocd + 10);
  let off = buf.readUInt32LE(eocd + 16);
  const files = [];
  for (let n = 0; n < count && off + 46 <= buf.length; n++) {
    if (buf.readUInt32LE(off) !== 0x02014b50) break;
    const method = buf.readUInt16LE(off + 10);
    const compSize = buf.readUInt32LE(off + 20);
    const uncompSize = buf.readUInt32LE(off + 24);
    const nameLen = buf.readUInt16LE(off + 28);
    const extraLen = buf.readUInt16LE(off + 30);
    const commentLen = buf.readUInt16LE(off + 32);
    const lhOff = buf.readUInt32LE(off + 42);
    const name = buf.toString("utf8", off + 46, off + 46 + nameLen);
    files.push({ name, method, compSize, uncompSize, lhOff });
    off += 46 + nameLen + extraLen + commentLen;
  }
  return { buf, files: files.filter((f) => /\.pdf$/i.test(f.name)) };
}

function lire(buf, f) {
  const lh = f.lhOff;
  if (buf.readUInt32LE(lh) !== 0x04034b50) throw new Error("ZIP local header invalide");
  const debut = lh + 30 + buf.readUInt16LE(lh + 26) + buf.readUInt16LE(lh + 28);
  const data = buf.subarray(debut, debut + f.compSize);
  return f.method === 0 ? Buffer.from(data) : zlib.inflateRawSync(data);
}

function choisir(pdfs) {
  if (pdfs.length <= 1) return pdfs[0] || null;
  const utiles = pdfs.filter((f) => !ANNEXE.test(f.name));
  const candidats = utiles.length ? utiles : pdfs;
  return candidats.reduce((a, b) => ((b.uncompSize || b.compSize || 0) > (a.uncompSize || a.compSize || 0) ? b : a));
}

(async () => {
  console.log(APPLIQUER ? "MODE : APPLIQUER (ecrit)" : "MODE : A BLANC (n'ecrit rien)");

  const lignes = await rest(
    "app_console_document?select=id,hektor_annonce_id,document_name,file_size,storage_path,metadata_json" +
    "&metadata_json->signature->>status=eq.signed&order=hektor_annonce_id.asc&limit=1000");

  const aFaire = [];
  let sansArchive = 0;
  let dejaBon = 0;

  for (const l of lignes || []) {
    const md = l.metadata_json || {};
    const sd = md.signed_document;
    if (!sd) continue;
    const zipLocal = md.immosign_files && md.immosign_files.procedure_zip
      && md.immosign_files.procedure_zip.local_archive_path;
    if (!zipLocal || !fs.existsSync(zipLocal)) { sansArchive += 1; continue; }
    let contenu;
    try {
      contenu = pdfsDuZip(fs.readFileSync(zipLocal));
    } catch (e) { sansArchive += 1; continue; }
    const bon = choisir(contenu.files);
    if (!bon) { sansArchive += 1; continue; }
    // ⚠ 25/09 : ON REGARDE LES DEUX COTES. Le premier essai a mis Supabase a jour
    // mais PAS le fichier du serveur (mon catch avalait l'erreur en silence) :
    // la metadonnee disait 1 359 168 o et le disque gardait l'annexe a 197 443 o.
    // Une ligne est donc « a faire » si la metadonnee OU le fichier local est perime.
    const metaPerimee = Number(sd.size) !== Number(bon.uncompSize);
    const local = String(sd.local_archive_path || "");
    let localPerime = false;
    if (local) {
      try { localPerime = !fs.existsSync(local) || fs.statSync(local).size !== Number(bon.uncompSize); }
      catch (_) { localPerime = true; }
    }
    if (!metaPerimee && !localPerime) { dejaBon += 1; continue; }
    aFaire.push({ ligne: l, sd, zipLocal, contenu, bon, metaPerimee, localPerime });
  }

  console.log(`\n  documents signes lus        : ${(lignes || []).length}`);
  console.log(`  deja le bon pdf             : ${dejaBon}`);
  console.log(`  sans archive exploitable    : ${sansArchive}`);
  console.log(`  ⚠ A RATTRAPER               : ${aFaire.length}`);
  console.log(`      dont metadonnee perimee  : ${aFaire.filter((x) => x.metaPerimee).length}`);
  console.log(`      dont fichier serveur     : ${aFaire.filter((x) => x.localPerime).length}`);
  if (!aFaire.length) { console.log("\nRien a faire."); return; }

  console.log("\n  (annonce)  actuel -> remplace par");
  for (const x of aFaire.slice(0, 8)) {
    console.log(`   ${String(x.ligne.hektor_annonce_id).padEnd(8)} ${String(x.sd.size).padStart(9)} o (${x.sd.filename || "?"})`);
    console.log(`            -> ${String(x.bon.uncompSize).padStart(9)} o (${x.bon.name})`);
  }
  if (aFaire.length > 8) console.log(`   ... et ${aFaire.length - 8} autre(s)`);

  if (!APPLIQUER) {
    console.log("\n  --dry-run : RIEN n'a ete ecrit. Relancer avec --appliquer.");
    return;
  }

  let faits = 0, rates = 0;
  for (const x of (LIMITE ? aFaire.slice(0, LIMITE) : aFaire)) {
    try {
      const pdf = lire(x.contenu.buf, x.bon);
      const sha = crypto.createHash("sha256").update(pdf).digest("hex");
      const chemin = String(x.sd.storage_path);          // on remplace EN PLACE : l'app pointe deja dessus
      const local = String(x.sd.local_archive_path || "");

      const up = await fetch(`${SUPABASE_URL}/storage/v1/object/${BUCKET}/${encodeURI(chemin)}`, {
        method: "PUT",
        headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}`, "Content-Type": "application/pdf", "x-upsert": "true" },
        body: pdf,
      });
      if (!up.ok) throw new Error(`storage ${up.status}`);

      // LE SERVEUR : on ecrit, PUIS ON VERIFIE. Une erreur n'est plus avalee --
      // c'est exactement ce qui a masque l'echec du premier essai.
      if (local) {
        fs.mkdirSync(path.dirname(local), { recursive: true });
        fs.writeFileSync(local, pdf);
        const taille = fs.statSync(local).size;
        if (taille !== pdf.length) throw new Error(`serveur : ${taille} o ecrits au lieu de ${pdf.length}`);
      } else {
        console.log(`\n  NOTE annonce ${x.ligne.hektor_annonce_id} : pas de chemin local connu, seul Supabase est mis a jour`);
      }

      const md = x.ligne.metadata_json || {};
      await rest(`app_console_document?id=eq.${encodeURIComponent(x.ligne.id)}`, {
        method: "PATCH",
        headers: { Prefer: "return=minimal" },
        body: JSON.stringify({
          file_size: pdf.length,
          sha256: sha,
          metadata_json: {
            ...md,
            signed_document: { ...x.sd, size: pdf.length, sha256: sha, source_zip_entry: x.bon.name,
                               rattrape_le: new Date().toISOString() },
            annexe_ecartee: { filename: x.sd.filename || null, size: x.sd.size || null, sha256: x.sd.sha256 || null,
                              raison: "extractPdfFromZip prenait le 1er pdf de l'archive (corrige le 25/09)" },
          },
          updated_at: new Date().toISOString(),
        }),
      });
      faits += 1;
      process.stdout.write(`\r  rattrapes : ${faits}/${LIMITE || aFaire.length}   `);
    } catch (e) {
      rates += 1;
      console.log(`\n  ECHEC annonce ${x.ligne.hektor_annonce_id} : ${e.message}`);
    }
  }
  console.log(`\n\nTERMINE : ${faits} rattrape(s), ${rates} en echec.`);
})().catch((e) => { console.error("ERREUR :", e.message); process.exit(1); });
