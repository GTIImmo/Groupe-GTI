// LE WORKER NE PROMET PLUS UNE REPRISE QUI N'EXISTE PAS
//                                                     chantier 4, point 4b, 09/10/2026
// Cinq messages disaient « le travail sera repris » / « sera repris ». Mesure du 09/10 :
//   · les 3 messages de cibleHektorContact ont 11 appelants, et UN SEUL
//     (delete_hektor_contact) figure dans les 10 types rejouables de
//     app_console_action_enqueue_due_retries (liste relue en base) -> faux 10 fois sur 11 ;
//   · les 2 messages du document et de la photo promettent un repreneur ORPHELIN
//     (Console/reprendre_envois_hektor.js : teste, mais aucune des 12 taches planifiees
//     Windows ne l'appelle -- deja ecrit le 25/09, point D3).
// Aucune occurrence reelle n'a jamais ete mesuree (0 dans app_console_job.error_message,
// 0 au journal, 0 en notification) : le defaut etait LATENT. Ce test l'empeche de revenir.
//
// Il lit le source et fait tourner LA VRAIE fonction avec un faux Supabase.
// N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT AUCUN FICHIER.

const fs = require("fs");
const path = require("path");

const WORKER = path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(WORKER, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function tranche(debutMarque) {
  const i = src.indexOf(debutMarque);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

// Les lignes de CODE, commentaires retires : une promesse citee dans un commentaire
// (« il disait... ») est legitime, une promesse dans une chaine ne l'est pas.
const lignesDeCode = src.split("\n").filter((ligne) => !ligne.trim().startsWith("//"));

(async () => {
  // ── (1) ET (2) : LA PROMESSE DOIT CORRESPONDRE A LA REALITE ───────────────
  //
  // ⚠⚠ REECRIT LE 14/10/2026 -- ET LE DECLENCHEUR, C'EST CE TEST LUI-MEME.
  //   Le 14/10 la piece 4 de 3d a ecrit `scheduled/run_reprise_envois_hektor.ps1`.
  //   Le controle (2c) d'alors cherchait « un fichier de scheduled/ qui cite le
  //   repreneur » : il est donc passe au rouge aussitot, en disant « remettre le mot
  //   repris dans les 2 messages ». ⭐ Il a fait son travail.
  //
  // ⭐ MAIS IL MESURAIT LA MAUVAISE CHOSE, et le suivre aurait cree exactement la
  //   fausse promesse qu'il interdit : un `.ps1` dans scheduled/ NE TOURNE PAS. Mesure
  //   du 14/10 : 7 taches planifiees Windows portent « GTI », et AUCUNE n'appelle le
  //   repreneur. Ecrire « il sera repris » aurait donc promis une reprise qui n'a
  //   toujours pas lieu. (Lecon du projet : les horaires et les appels se lisent dans
  //   les taches Windows, jamais dans un fichier ni dans un commentaire.)
  //
  // ➡ DESORMAIS ON MESURE LA TACHE, et le controle marche DANS LES DEUX SENS :
  //     pas de tache  -> les messages DOIVENT dire « le repreneur n'est pas branche »
  //     une tache     -> les messages DOIVENT promettre la reprise
  //   Le jour ou Frederic enregistre la tache, ce test redevient rouge et dit quoi
  //   changer. Et si la tache est un jour retiree, il le dit aussi.
  function tachePlanifieeDuRepreneur() {
    const ps = [
      '$a = Get-ScheduledTask -ErrorAction Stop | ForEach-Object {',
      '  ($_.Actions | ForEach-Object { [string]$_.Execute + " " + [string]$_.Arguments }) -join " " };',
      '@($a | Where-Object { $_ -match "reprendre_envois_hektor|run_reprise_envois_hektor" }).Count',
    ].join(" ");
    try {
      const sortie = require("child_process").execFileSync(
        "powershell", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        { encoding: "utf8", timeout: 60000, stdio: ["ignore", "pipe", "ignore"] });
      const n = Number(String(sortie).trim());
      return Number.isFinite(n) ? n > 0 : null;   // null = pas mesurable
    } catch (_) {
      return null;
    }
  }

  const tache = tachePlanifieeDuRepreneur();
  // ⚠ « pas mesurable » est traite comme « pas de tache » : on exige alors le message
  //   PRUDENT. On ne promet jamais sur une mesure qu'on n'a pas pu faire.
  const repreneurTourne = tache === true;
  console.log(`  ..  la tache planifiee du repreneur : ${
    tache === null ? "NON MESURABLE (on exige donc le message prudent)"
      : tache ? "ELLE EXISTE" : "aucune (7 taches GTI, aucune ne l'appelle)"}`);

  const promesses = lignesDeCode.filter((l) =>
    /sera\s+repris|seront\s+repris|sera\s+rejou|seront\s+rejou/i.test(l));

  if (repreneurTourne) {
    controle("(1) une tache reprend -> les messages PROMETTENT la reprise",
      promesses.length >= 2,
      `seulement ${promesses.length} message(s) promettent une reprise : ${promesses.join(" | ")}`);
    controle("(2a) le document dit qu'il sera repris",
      /Document garde chez nous[^"]*repris/.test(src),
      "le message n'annonce pas la reprise alors qu'une tache reprend");
    controle("(2b) la photo dit la meme chose",
      /Photo gardee chez nous[^"]*repris/.test(src),
      "le message n'annonce pas la reprise alors qu'une tache reprend");
  } else {
    controle("(1) personne ne reprend -> aucune chaine ne promet une reprise",
      promesses.length === 0, promesses.join(" | "));
    controle("(2a) le document dit « A REPRENDRE (le repreneur n'est pas branche) »",
      src.includes("Document garde chez nous, envoi Hektor en echec -- A REPRENDRE (le repreneur n'est pas branche)"),
      "le message ne dit plus la verite");
    controle("(2b) la photo dit la meme chose",
      src.includes("Photo gardee chez nous, envoi Hektor en echec -- A REPRENDRE (le repreneur n'est pas branche)"),
      "le message ne dit plus la verite");
  }

  // Le script existe-t-il, au moins ? S'il manque, la tache ne pourrait rien lancer.
  const scriptPret = fs.existsSync(path.join(__dirname, "..", "scheduled", "run_reprise_envois_hektor.ps1"));
  controle("(2c) le script de reprise est pret a etre branche",
    scriptPret, "scheduled/run_reprise_envois_hektor.ps1 est absent");
  if (scriptPret && !repreneurTourne) {
    console.log("  ..  ⚠ LE SCRIPT EST PRET MAIS AUCUNE TACHE NE L'APPELLE : il ne tourne pas.");
    console.log("  ..    A enregistrer par Frederic. Ce test passera alors au rouge et dira");
    console.log("  ..    quoi changer dans les deux messages du worker.");
  }

  // ── (3) LA VRAIE FONCTION, DANS SES DEUX CAS D'ECHEC ──────────────────────
  const bloc = tranche("async function cibleHektorContact(");
  if (!bloc) {
    controle("(3) cibleHektorContact est dans le worker", false, "introuvable");
  } else {
    controle("(3) cibleHektorContact est dans le worker", true);

    function fabrique({ supabaseJette = false, cibleRendue = "" } = {}) {
      const faux = {
        // La vraie borne du worker (l. 1969) : < 10 M = numero de Hektor,
        // >= 10 M = numero de l'app ([[deux-numeros-reconnaitre-par-la-plage]]).
        PLAGE_NUMEROS_APP: 10000000,
        supabaseRequest: async () => {
          if (supabaseJette) throw new Error("Supabase muet");
          return cibleRendue ? [{ hektor_target_id: cibleRendue }] : [];
        },
      };
      // eslint-disable-next-line no-new-func
      return new Function(...Object.keys(faux), `${bloc}; return cibleHektorContact;`)(
        ...Object.values(faux));
    }

    // a) un numero A NOUS (>= 10 000 000) et Supabase muet
    let message = "";
    try {
      await fabrique({ supabaseJette: true })("10355757", { contexte: "link_hektor_mandant" });
    } catch (e) { message = e.message; }
    controle("(3a) Supabase muet : le message ne promet rien et dit quoi faire",
      /Relancer la demande si necessaire/.test(message) && !/sera repris/.test(message), message);
    controle("(3b) il nomme le contact et le contexte",
      message.includes("10355757") && message.includes("link_hektor_mandant"), message);

    // b) un numero A NOUS, pas encore cree chez Hektor (Supabase repond, sans cible)
    message = "";
    try {
      await fabrique({ cibleRendue: "" })("10355757", { contexte: "add_hektor_contact_search" });
    } catch (e) { message = e.message; }
    controle("(3c) pas encore cree chez Hektor : « Relancer la demande quand... »",
      /Relancer la demande quand le numero Hektor sera rapporte/.test(message)
      && !/travail sera repris/.test(message), message);

    // c) UN NUMERO DE HEKTOR (< 10 000 000) : il se vise lui-meme, aucun message
    const cible = await fabrique({ cibleRendue: "" })("603953", { contexte: "test" });
    controle("(3d) un numero de Hektor se vise lui-meme, sans erreur",
      String(cible) === "603953", String(cible));
  }

  // ── (4) RIEN D'AUTRE N'A BOUGE ────────────────────────────────────────────
  // La liste des 10 types rejouables vit en SQL, et NULLE PART AILLEURS : la dupliquer
  // ici la ferait deriver en silence. Un commentaire qui la nomme est legitime, du code
  // qui la recopie ne l'est pas -- d'ou la lecture sur les lignes de CODE seules.
  controle("(4a) le filet C.4-bis n'est pas touche : la liste SQL n'est pas recopiee ici",
    !lignesDeCode.some((l) => l.includes("types_rejouables")),
    "le worker s'est mis a dupliquer la liste SQL");
  controle("(4b) la formule est celle du garde-fou des 30 minutes (SQL), pas une nouvelle",
    src.includes("Relancer la demande si necessaire"));

  console.log(echecs === 0 ? "\nTOUT EST VERT" : `\n${echecs} CONTROLE(S) EN ECHEC`);
  process.exit(echecs === 0 ? 0 : 1);
})();
