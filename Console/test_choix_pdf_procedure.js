// LE PDF TIRE D'UNE PROCEDURE IMMOSIGN EST-IL LE MANDAT, OU SON ANNEXE ?
//                                                                  25/09/2026
// Trouve par Frederic : dans l'app, sous le nom « Mandat », certaines annonces
// n'affichaient que l'ANNEXE. Cause : extractPdfFromZip prenait LE PREMIER pdf
// de l'archive, et l'annexe y precede souvent le mandat.
//
// CE TEST FAIT TOURNER LA VRAIE FONCTION DU WORKER sur :
//   (1) des archives fabriquees ici -- les cas limites, y compris ceux qu'on
//       n'a pas sous la main (un seul pdf, noms trompeurs, tailles proches) ;
//   (2) LES VRAIES ARCHIVES DU SERVEUR, si elles sont la : on verifie qu'aucune
//       ne rend un fichier nomme ANNEXE/BAREME.
//
// ⚠ LA PREUVE D'ABORD : sur la version d'avant, le cas (a) doit ECHOUER.
//      node Console/test_choix_pdf_procedure.js --worker <fichier>
// N'APPELLE JAMAIS HEKTOR. N'ECRIT RIEN.

const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

const args = process.argv.slice(2);
const iw = args.indexOf("--worker");
const CHEMIN_WORKER = iw >= 0 ? args[iw + 1] : path.join(__dirname, "console_job_worker.js");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

// ── on extrait la fonction du worker sans executer le reste du fichier ───────
function chargerExtracteur() {
  const src = fs.readFileSync(CHEMIN_WORKER, "utf8");
  const i = src.indexOf("function extractPdfFromZip(");
  if (i < 0) return null;
  // la fonction se termine a la 1re accolade fermante en colonne 0 (style du worker)
  const fin = src.indexOf("\n}", i);
  if (fin < 0) return null;
  const corps = src.slice(i, fin + 2);
  // eslint-disable-next-line no-new-func
  return new Function("zlib", `${corps}; return extractPdfFromZip;`)(zlib);
}

// ── un ZIP minimal, non compresse (methode 0) ────────────────────────────────
function crc32(buf) {
  let c, crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    c = (crc ^ buf[i]) & 0xff;
    for (let k = 0; k < 8; k++) c = c & 1 ? (c >>> 1) ^ 0xedb88320 : c >>> 1;
    crc = (crc >>> 8) ^ c;
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function fabriquerZip(fichiers) {
  const locaux = [];
  const centraux = [];
  let offset = 0;
  for (const { nom, contenu } of fichiers) {
    const n = Buffer.from(nom, "utf8");
    const d = Buffer.from(contenu);
    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(20, 4); lh.writeUInt16LE(0, 8);
    lh.writeUInt32LE(crc32(d), 14); lh.writeUInt32LE(d.length, 18); lh.writeUInt32LE(d.length, 22);
    lh.writeUInt16LE(n.length, 26); lh.writeUInt16LE(0, 28);
    locaux.push(lh, n, d);
    const ch = Buffer.alloc(46);
    ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(20, 6); ch.writeUInt16LE(0, 10);
    ch.writeUInt32LE(crc32(d), 16); ch.writeUInt32LE(d.length, 20); ch.writeUInt32LE(d.length, 24);
    ch.writeUInt16LE(n.length, 28); ch.writeUInt32LE(offset, 42);
    centraux.push(ch, n);
    offset += lh.length + n.length + d.length;
  }
  const corpsLocal = Buffer.concat(locaux);
  const corpsCentral = Buffer.concat(centraux);
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0);
  eocd.writeUInt16LE(fichiers.length, 8); eocd.writeUInt16LE(fichiers.length, 10);
  eocd.writeUInt32LE(corpsCentral.length, 12); eocd.writeUInt32LE(corpsLocal.length, 16);
  return Buffer.concat([corpsLocal, corpsCentral, eocd]);
}

const pdf = (taille, marque) => Buffer.concat([Buffer.from(`%PDF-1.4 ${marque} `), Buffer.alloc(Math.max(0, taille - 20), 0x20)]);

// ═══════════════════════════════════════════════════════════════════════════
const extraire = chargerExtracteur();
console.log(`worker teste : ${CHEMIN_WORKER}`);
if (!extraire) {
  controle("(0) extractPdfFromZip est dans le worker", false, "fonction introuvable");
} else {
  // (a) LE CAS REEL : l'annexe D'ABORD, le mandat ensuite
  let r = extraire(fabriquerZip([
    { nom: "ANNEXEMAND_69e9c199.pdf", contenu: pdf(177423, "ANNEXE") },
    { nom: "mandatGras_69e9c16a.pdf", contenu: pdf(795742, "MANDAT") },
  ]));
  controle("(a) annexe en premier -> on prend LE MANDAT", /MANDAT/.test(r.buffer.toString("latin1", 0, 40)), r.name);

  // (b) l'ordre inverse : on prend toujours le mandat
  r = extraire(fabriquerZip([
    { nom: "MANDAT_AVEC.pdf", contenu: pdf(795742, "MANDAT") },
    { nom: "ANNEXEMAND_x.pdf", contenu: pdf(177423, "ANNEXE") },
  ]));
  controle("(b) mandat en premier -> on prend toujours le mandat", /MANDAT/.test(r.buffer.toString("latin1", 0, 40)), r.name);

  // (c) le cas 62794 : un BAREME, pas une annexe
  r = extraire(fabriquerZip([
    { nom: "BAREMEtran_6a6c933a.pdf", contenu: pdf(107899, "BAREME") },
    { nom: "BALTUSdupl_6a6c92ea.pdf", contenu: pdf(1225212, "MANDAT") },
  ]));
  controle("(c) bareme en premier -> on prend le mandat", /MANDAT/.test(r.buffer.toString("latin1", 0, 40)), r.name);

  // (d) DEUX noms quelconques : c'est la TAILLE qui tranche
  r = extraire(fabriquerZip([
    { nom: "18726_1782.pdf", contenu: pdf(120000, "PETIT") },
    { nom: "18629_1779.pdf", contenu: pdf(900000, "MANDAT") },
  ]));
  controle("(d) noms quelconques -> le plus gros gagne", /MANDAT/.test(r.buffer.toString("latin1", 0, 40)), r.name);

  // (e) UN SEUL pdf : on le prend, meme s'il s'appelle ANNEXE
  r = extraire(fabriquerZip([{ nom: "ANNEXE_seule.pdf", contenu: pdf(50000, "SEUL") }]));
  controle("(e) un seul pdf -> on le prend quand meme", /SEUL/.test(r.buffer.toString("latin1", 0, 40)), r.name);

  // (f) pdf melange a d'autres fichiers
  r = extraire(fabriquerZip([
    { nom: "preuve.xml", contenu: Buffer.alloc(900000, 0x41) },
    { nom: "mandat.pdf", contenu: pdf(300000, "MANDAT") },
  ]));
  controle("(f) un .xml plus gros n'est jamais choisi", /MANDAT/.test(r.buffer.toString("latin1", 0, 40)), r.name);

  // (g) LES VRAIES ARCHIVES DU SERVEUR
  const racine = "C:\\Hektor\\HektorConsoleDocuments\\annonces";
  let lues = 0, annexes = 0;
  if (fs.existsSync(racine)) {
    for (const a of fs.readdirSync(racine)) {
      const d = path.join(racine, a, "documents");
      if (!fs.existsSync(d)) continue;
      for (const sous of fs.readdirSync(d)) {
        const dossier = path.join(d, sous);
        let noms = [];
        try { noms = fs.readdirSync(dossier); } catch (_) { continue; }
        for (const f of noms) {
          if (!/^immosign_procedure-.*\.zip$/i.test(f)) continue;
          try {
            const res = extraire(fs.readFileSync(path.join(dossier, f)));
            lues += 1;
            if (/(annexe|bareme)/i.test(res.name)) annexes += 1;
          } catch (_) { /* archive illisible : hors sujet ici */ }
        }
        if (lues >= 120) break;
      }
      if (lues >= 120) break;
    }
  }
  if (lues === 0) {
    console.log("  -- (g) aucune archive reelle sur cette machine : controle saute");
  } else {
    controle(`(g) ${lues} VRAIES archives du serveur -> 0 annexe choisie`, annexes === 0, `${annexes} annexe(s) encore choisie(s)`);
  }
}

console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
process.exit(echecs ? 1 : 0);
