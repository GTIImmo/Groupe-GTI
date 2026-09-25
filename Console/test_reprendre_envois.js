// LE REPASSAGE S'ACHARNE-T-IL, OU SAIT-IL ATTENDRE ?
//                                                                  25/09/2026
// Depuis le lot 1, un document ou une photo ajoute depuis l'app existe des sa creation,
// et l'envoi chez Hektor n'est qu'un ETAT de la ligne. Ce script remet en file ce qui
// attend -- mais il ne doit PAS tourner en boucle quand Hektor est indisponible : c'est
// exactement ce qui a fait bannir notre IP en aout (403 repetes sur les memes lignes).
//
// CE QUE CE TEST PROUVE :
//   ① une ligne deja en file n'est pas reposee par-dessus ;
//   ② une ligne retentee a l'instant est laissee respirer ;
//   ③ une ligne jamais tentee part tout de suite ;
//   ④ un echec qui DURE est signale -- et fait sortir en 1, donc il se voit ;
//   ⑤ rien de ce qui vient de Hektor n'est touche.
//
// Il fait tourner LA VRAIE fonction de tri. N'APPELLE NI HEKTOR NI SUPABASE.

const fs = require("fs");
const path = require("path");

const SCRIPT = path.join(__dirname, "reprendre_envois_hektor.js");
const src = fs.readFileSync(SCRIPT, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

const i = src.indexOf("function trier(");
const f = i < 0 ? -1 : src.indexOf("\n}", i);
const bloc = f < 0 ? null : src.slice(i, f + 2);

const MINUTE = 60 * 1000;
const HEURE = 3600 * 1000;
const T0 = Date.parse("2026-09-25T20:00:00Z");
const ilYA = (ms) => new Date(T0 - ms).toISOString();

(async () => {
  if (!bloc) {
    controle("(0) la fonction de tri est dans le script", false, "introuvable");
  } else {
    // eslint-disable-next-line no-new-func
    const trier = new Function(`${bloc}; return trier;`)();

    const lignes = [
      { id: "a", hektor_annonce_id: "1", document_name: "jamais tentee",
        envoi_hektor_statut: "a_envoyer", envoi_hektor_at: null },
      { id: "b", hektor_annonce_id: "2", document_name: "retentee il y a 2 min",
        envoi_hektor_statut: "echec", envoi_hektor_at: ilYA(2 * MINUTE) },
      { id: "c", hektor_annonce_id: "3", document_name: "retentee il y a 1 h",
        envoi_hektor_statut: "echec", envoi_hektor_at: ilYA(1 * HEURE) },
      { id: "d", hektor_annonce_id: "4", document_name: "deja en file",
        envoi_hektor_statut: "a_envoyer", envoi_hektor_at: null },
      { id: "e", hektor_annonce_id: "5", document_name: "en echec depuis 30 h",
        envoi_hektor_statut: "echec", envoi_hektor_at: ilYA(30 * HEURE),
        envoi_hektor_erreur: "Session Hektor expiree" },
    ];
    const options = { limite: 50, respirationMs: 15 * MINUTE, alerteMs: 24 * HEURE,
                      libelle: "document_name" };

    const r = trier(lignes, new Set(["d"]), T0, options);
    const ids = r.retenus.map((l) => l.id);

    controle("(a) une ligne jamais tentee part tout de suite", ids.includes("a"), ids.join(","));
    controle("(b) ⚠ une ligne retentee il y a 2 min est laissee RESPIRER",
      !ids.includes("b"), `retenue a tort : ${ids.join(",")}`);
    controle("(c) une ligne retentee il y a 1 h repart", ids.includes("c"), ids.join(","));
    controle("(d) ⚠ une ligne DEJA EN FILE n'est pas reposee par-dessus",
      !ids.includes("d"), `reposee a tort : ${ids.join(",")}`);
    controle("(e) les comptes sont justes",
      r.stats.en_attente === 5 && r.stats.deja_en_file === 1 && r.stats.trop_recentes === 1,
      JSON.stringify(r.stats));

    controle("(f) ⚠ un echec de 30 h est SIGNALE, pas juste retente",
      r.aSignaler.length === 1 && r.aSignaler[0].id === "e", JSON.stringify(r.aSignaler));
    controle("(g) le signalement porte le motif et l'anciennete",
      r.aSignaler[0].depuis_h === 30 && /Session Hektor/.test(r.aSignaler[0].erreur),
      JSON.stringify(r.aSignaler[0]));
    controle("(h) mais il repart quand meme -- signaler n'est pas abandonner",
      ids.includes("e"), ids.join(","));

    // le plafond
    const beaucoup = Array.from({ length: 120 }, (_, n) => ({
      id: `x${n}`, hektor_annonce_id: "9", envoi_hektor_statut: "a_envoyer", envoi_hektor_at: null }));
    const r2 = trier(beaucoup, new Set(), T0, { ...options, limite: 50 });
    controle("(i) le plafond est respecte", r2.retenus.length === 50, String(r2.retenus.length));

    // ⚠ un echec ANCIEN mais au-dela du plafond doit quand meme etre signale : sinon
    // un incident durable resterait invisible derriere une file pleine.
    const melange = [...beaucoup, lignes[4]];
    const r3 = trier(melange, new Set(), T0, { ...options, limite: 10 });
    controle("(j) un echec durable est signale MEME au-dela du plafond",
      r3.aSignaler.length === 1, JSON.stringify(r3.aSignaler));
  }

  // ── ⑤ CE QUI VIENT DE HEKTOR N'EST JAMAIS TOUCHE ──────────────────────────
  controle("(k) seules les lignes a_envoyer/echec sont lues",
    /envoi_hektor_statut=in\.\(a_envoyer,echec\)/.test(src),
    "le filtre prendrait aussi ce qui vient de Hektor");
  controle("(l) le script ne parle pas a Hektor : il pose des travaux",
    !/hektorFetch|la-boite-immo|xmlrpc/.test(src), "une requete Hektor existe");
  controle("(m) un echec durable fait SORTIR EN 1, donc il se voit",
    /if \(aSignaler\.length\) process\.exitCode = 1;/.test(src),
    "un incident durable passerait inapercu");
  controle("(n) les lectures sont paginees",
    /offset=\$\{offset\}|offset=/.test(src) && /async function tout/.test(src),
    "PostgREST plafonnerait a 1 000 lignes");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
