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

    // ── REFUS n.4 : une ligne qui a DEJA le numero Hektor n'est jamais renvoyee ──
    const optN = { ...options, numero: "hektor_document_id" };
    const deja = [
      { id: "n1", hektor_annonce_id: "59578", document_name: "AVENANTS 87K.pdf",
        hektor_document_id: "716119466cb6d1696be22788a837711d9b9194ab",
        envoi_hektor_statut: "echec", envoi_hektor_at: ilYA(20 * HEURE) },
      { id: "n2", hektor_annonce_id: "7", document_name: "vraiment pas parti.pdf",
        hektor_document_id: null, envoi_hektor_statut: "echec", envoi_hektor_at: ilYA(20 * HEURE) },
      { id: "n3", hektor_annonce_id: "8", document_name: "numero vide.pdf",
        hektor_document_id: "", envoi_hektor_statut: "a_envoyer", envoi_hektor_at: null },
    ];
    const rn = trier(deja, new Set(), T0, optN);
    const idsN = rn.retenus.map((l) => l.id);
    controle("(n) ⭐⭐ une ligne qui porte DEJA le numero Hektor n'est PAS reposee (doublon)",
      !idsN.includes("n1"), `reposee a tort : ${idsN.join(",")}`);
    controle("(o) elle est NOMMEE, pas oubliee en silence",
      rn.dejaChezHektor.length === 1 && rn.dejaChezHektor[0].id === "n1" && rn.stats.deja_chez_hektor === 1,
      JSON.stringify(rn.dejaChezHektor));
    controle("(p) TEMOIN INVERSE : une ligne sans numero (ou numero vide) repart",
      idsN.includes("n2") && idsN.includes("n3"), idsN.join(","));
    // sans la colonne dans les options, l'ancien comportement est inchange
    const rSans = trier(deja, new Set(), T0, options);
    controle("(q) sans l'option « numero », le tri se comporte comme avant",
      rSans.retenus.length === 3, String(rSans.retenus.length));
    controle("(r) le script demande bien la colonne du numero a la base",
      /\$\{sorte\.numero\},envoi_hektor_statut/.test(src), "la colonne ne serait pas lue : le refus ne verrait rien");

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
  // ⚠⚠ CORRIGE LE 14/10/2026 -- L'EPREUVE EXIGEAIT LA TECHNIQUE ABANDONNEE EXPRES.
  //   Elle cherchait « offset= ». Or le 26/09 (461a66c) le script est passe au
  //   CURSEUR, et c'est un PROGRES, pas une regression : une pagination par offset
  //   saute ou duplique des lignes des que l'ensemble bouge entre deux pages -- ce qui
  //   est justement le cas ici, puisque le script POSE des travaux pendant qu'il lit.
  //   L'epreuve etait donc rouge depuis 18 jours en reclamant le defaut.
  //   ➡ On verifie maintenant le curseur, ET le garde-fou qui le rend correct : la
  //     fonction REFUSE un ordre dans le chemin, parce que deux « order= »
  //     concurrents feraient sauter des lignes sans rien dire.
  controle("(n) les lectures sont paginees PAR CURSEUR",
    /async function tout\(/.test(src)
      && /=gt\.\$\{encodeURIComponent/.test(src)
      && /&order=\$\{cleUnique\}\.asc&limit=/.test(src),
    "PostgREST plafonnerait a 1 000 lignes");
  controle("(o) ⭐ et le curseur impose SON ordre : un ordre dans le chemin est REFUSE",
    /pas d'ordre dans le chemin/.test(src),
    "deux order= concurrents feraient sauter des lignes en silence");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
