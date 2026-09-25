// LE COMPOSEUR DE LOTS SAIT-IL REFUSER, ET S'ARRETER TOUT SEUL ?
//                                                                  25/09/2026
// La tache de 23:00 tournera SEULE pendant 15 nuits. Trois garde-fous la tiennent :
//   - plus rien a faire       -> elle ne pose rien (succes)
//   - la file n'est pas vide  -> code 3. Poser par-dessus un lot non digere ferait
//                                grossir le retard nuit apres nuit, EN SILENCE.
//   - >= N erreurs en 24 h    -> code 4. Regle du projet : un 403 arrete tout, on ne
//                                rejoue JAMAIS une annonce en echec (bannissement 20/08).
//
// Il fait tourner LES VRAIES FONCTIONS du fichier avec un faux client Supabase.
// N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT RIEN.
//
//   node Console/test_lot_rattrapage_garde_fous.js

const fs = require("fs");
const path = require("path");

const FICHIER = path.join(__dirname, "enqueue_empreinte_lot.js");
const TACHE = path.join(__dirname, "..", "scheduled", "run_rattrapage_documents.ps1");
const src = fs.readFileSync(FICHIER, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function tranche(debutMarque, finMarque) {
  const d = src.indexOf(debutMarque);
  const i = src.indexOf(finMarque);
  if (d < 0 || i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(d, f + 2);
}

// ── piece A : SOURCES + parseArgs (n'a pas besoin du client) ─────────────────
const blocA = tranche("const SOURCES = {", "function parseArgs(");
// ── piece B : les garde-fous (le client `rest` est INJECTE, pas celui du fichier)
const blocB = tranche("// REFUS 1 :", "async function premierReste(");

(async () => {
  if (!blocA || !blocB) {
    controle("(0) les fonctions sont dans le fichier", false, "tranche introuvable");
  } else {
    // eslint-disable-next-line no-new-func
    const A = new Function(`${blocA}; return { parseArgs, SOURCES };`)();

    // ── ① LES OPTIONS ──────────────────────────────────────────────────────
    let a = A.parseArgs(["node", "x", "--scope", "auto", "--limit", "3000",
                         "--exiger-file-vide", "--max-erreurs-recentes", "20"]);
    controle("(a) --scope auto est accepte", a.scope === "auto", a.scope);
    controle("(b) les deux garde-fous sont lus",
      a.exigerFileVide === true && a.maxErreursRecentes === 20, JSON.stringify(a));

    a = A.parseArgs(["node", "x"]);
    controle("(c) SANS option : comportement d'origine (archive, 3000, aucun refus)",
      a.scope === "archive" && a.limit === 3000 && a.exigerFileVide === false && a.maxErreursRecentes === 0,
      JSON.stringify(a));

    let leve = false;
    try { A.parseArgs(["node", "x", "--scope", "nimporte"]); } catch (_) { leve = true; }
    controle("(d) un perimetre inconnu est refuse", leve, "accepte a tort");

    // ── ② LES REFUS ────────────────────────────────────────────────────────
    function charger(fauxRest) {
      // eslint-disable-next-line no-new-func
      return new Function("rest", "JOB_TYPE", `${blocB}; return { refusEventuel, premierReste };`)(
        fauxRest, "sync_console_documents");
    }

    const options = { exigerFileVide: true, maxErreursRecentes: 20 };
    let B = charger(async () => []);
    controle("(e) file vide + 0 erreur -> on passe (code 0)",
      (await B.refusEventuel(options, new Set())) === 0, "refus a tort");

    controle("(f) file NON vide -> code 3, rien n'est pose",
      (await B.refusEventuel(options, new Set(["1", "2"]))) === 3, "n'a pas refuse");

    B = charger(async () => new Array(25).fill({ hektor_annonce_id: "1" }));
    controle("(g) 25 erreurs en 24 h (seuil 20) -> code 4",
      (await B.refusEventuel(options, new Set())) === 4, "n'a pas refuse");

    B = charger(async () => new Array(19).fill({ hektor_annonce_id: "1" }));
    controle("(h) 19 erreurs (sous le seuil) -> on passe",
      (await B.refusEventuel(options, new Set())) === 0, "a refuse a tort");

    // RETRO-COMPATIBILITE : sans les options, on ne refuse JAMAIS -- l'usage manuel
    // d'un lot reste possible meme si la file tourne.
    B = charger(async () => new Array(500).fill({ hektor_annonce_id: "1" }));
    controle("(i) sans les options : aucun refus, meme file pleine et erreurs",
      (await B.refusEventuel({ exigerFileVide: false, maxErreursRecentes: 0 }, new Set(["1", "2"]))) === 0,
      "a refuse alors qu'aucune option n'etait demandee");

    // ── ③ « RESTE-T-IL DU TRAVAIL ? » ──────────────────────────────────────
    const source = { table: "t", idColumn: "app_archive_id" };
    const lignes = [
      { app_archive_id: 1, hektor_annonce_id: "100" },   // deja une empreinte
      { app_archive_id: 2, hektor_annonce_id: "200" },   // en erreur : a NE JAMAIS rejouer
      { app_archive_id: 3, hektor_annonce_id: "300" },   // deja en file
      { app_archive_id: 4, hektor_annonce_id: "400" },   // <- le seul vrai reste
    ];
    B = charger(async (p) => (String(p).includes("offset=0") ? lignes : []));
    controle("(j) il reste du travail -> vrai",
      (await B.premierReste(source, new Set(["100"]), new Set(["200"]), new Set(["300"]))) === true,
      "n'a rien trouve");
    controle("(k) tout est deja marque / en erreur / en file -> faux",
      (await B.premierReste(source, new Set(["100", "400"]), new Set(["200"]), new Set(["300"]))) === false,
      "a trouve du travail a tort");
    B = charger(async () => []);
    controle("(l) perimetre vide -> faux",
      (await B.premierReste(source, new Set(), new Set(), new Set())) === false, "a trouve du travail");
  }

  // ── ④ LA TACHE TRADUIT BIEN LES CODES ──────────────────────────────────────
  const ps = fs.readFileSync(TACHE, "utf8");
  controle("(m) la tache passe les 3 options", /--scope" "auto"/.test(ps)
    && /--exiger-file-vide/.test(ps) && /--max-erreurs-recentes" "20"/.test(ps), "options manquantes");
  controle("(n) code 3 et code 4 font ECHOUER la tache (pas d'arret muet)",
    /3 \{[^}]*runFailed = \$true/.test(ps) && /4 \{[^}]*runFailed = \$true/.test(ps),
    "un arret passerait inapercu");
  controle("(o) l'echec est propage au Planificateur",
    /if \(\$runFailed\) \{ exit 1 \}/.test(ps), "bloc final absent");
  controle("(p) code 0 (rien a faire) n'est PAS un echec",
    /0 \{ Write-Output "--- lot pose/.test(ps), "le succes est traite comme un echec");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
