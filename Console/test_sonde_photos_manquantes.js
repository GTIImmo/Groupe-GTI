// LA SONDE SAIT-ELLE TROUVER SA SESSION, ET VOIR UNE PHOTO MANQUANTE ?
//                                                                  26/09/2026
// ⚠⚠ LE DEFAUT QU'ELLE A REVELE, et qui depassait la sonde : LA CONSOLE HEKTOR REPOND
//    SUR DEUX NOMS DE DOMAINE. `groupe-gti-immobilier.la-boite-immo.com` ET
//    `www.gti-immobilier.fr` servent la meme application. Le pot de cookies du worker
//    porte l'un OU l'autre, selon le dernier utilise. Apres l'envoi d'une photo (qui
//    passe par www.gti-immobilier.fr), storage_state_documents.json ne contenait PLUS
//    AUCUN cookie la-boite-immo.com -- et la detection documentaire, qui filtrait sur ce
//    seul domaine, aurait rendu « aucun cookie Hektor » sur une session valide.
//
// ⚠ LE COUPLAGE CRITIQUE : l'adresse de base doit SUIVRE les cookies. Un cookie de
//   www.gti-immobilier.fr n'est pas envoye a la-boite-immo.com -- Hektor rendrait la page
//   de login, et la sonde conclurait « contenu vide » sur tout le parc.
//
//   node Console/test_sonde_photos.js
// N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT RIEN.

const fs = require("fs");
const os = require("os");
const path = require("path");

const SONDE = path.join(__dirname, "sonde_photos_manquantes.js");
const ENQ = path.join(__dirname, "enqueue_console_sync_jobs.js");
const srcSonde = fs.readFileSync(SONDE, "utf8");
const srcEnq = fs.readFileSync(ENQ, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function tranche(src, marque) {
  const i = src.indexOf(marque);
  if (i < 0) return null;
  const f = src.indexOf("\n}", i);
  return f < 0 ? null : src.slice(i, f + 2);
}

const LBI = "groupe-gti-immobilier.la-boite-immo.com";
const GTI = "www.gti-immobilier.fr";

function potTemporaire(cookies) {
  const p = path.join(os.tmpdir(), `pot_essai_${process.pid}_${Math.random().toString(36).slice(2)}.json`);
  fs.writeFileSync(p, JSON.stringify({ cookies }));
  return p;
}

(async () => {
  // ═══ ① LA RESOLUTION DE SESSION, DANS LA SONDE ══════════════════════════
  // ⚠ Jusqu'au point-virgule, pas « 200 caracteres » : une coupe arbitraire tombait
  // en plein milieu de la declaration (1re version de ce test, SyntaxError).
  const iH = srcSonde.indexOf("const HOTES =");
  const blocHotes = iH < 0 ? "" : srcSonde.slice(iH, srcSonde.indexOf(";", iH) + 1);
  const blocSessions = tranche(srcSonde, "function sessions(");
  if (!blocSessions) {
    controle("(0) la sonde sait lister ses entrees", false, "fonction introuvable");
  } else {
    function charger(pot) {
      // eslint-disable-next-line no-new-func
      return new Function("fs", "POT", `${blocHotes}\n${blocSessions}; return sessions;`)(fs, pot);
    }
    const essai = (cookies) => {
      const pot = potTemporaire(cookies);
      try { return { out: charger(pot)(), leve: "" }; }
      catch (e) { return { out: null, leve: e.message }; }
      finally { fs.rmSync(pot, { force: true }); }
    };

    // le cas VECU : plus aucun cookie la-boite-immo, seulement www.gti-immobilier.fr
    let r = essai([{ domain: GTI, name: "PHPSESSID", value: "abc" },
                   { domain: ".vimeo.com", name: "x", value: "y" }]);
    controle("(a) ⚠ le cas vecu : l'entree www.gti-immobilier.fr est trouvee",
      r.out && r.out.length === 1 && r.out[0].base === "https://" + GTI,
      r.leve ? `a leve : ${r.leve}` : JSON.stringify(r.out));
    controle("(b) ⚠ ET l'adresse de base SUIT les cookies",
      r.out && r.out[0] && r.out[0].base === "https://" + GTI, JSON.stringify(r.out));
    controle("(c) les cookies etrangers ne sont pas embarques",
      r.out && r.out[0] && !/vimeo/.test(r.out[0].cookieHeader),
      r.out && r.out[0] ? r.out[0].cookieHeader : "-");

    r = essai([{ domain: "." + LBI, name: "PHPSESSID", value: "def" }]);
    controle("(d) l'autre entree marche aussi, point initial du domaine compris",
      r.out && r.out[0] && r.out[0].base === "https://" + LBI, JSON.stringify(r.out));

    // ⚠ LE POINT APPRIS LE 26/09 : avoir un badge ne veut pas dire qu'il est VALIDE.
    // La sonde doit rendre LES DEUX entrees pour que l'appelant puisse essayer.
    r = essai([{ domain: GTI, name: "a", value: "1" }, { domain: LBI, name: "b", value: "2" }]);
    controle("(e) ⚠ avec les deux badges, LES DEUX entrees sont rendues",
      r.out && r.out.length === 2, JSON.stringify(r.out && r.out.map((x) => x.base)));
    controle("(e2) et dans un ordre DETERMINISTE",
      r.out && r.out[0].base === "https://" + LBI, JSON.stringify(r.out && r.out.map((x) => x.base)));

    r = essai([{ domain: ".vimeo.com", name: "x", value: "y" }]);
    controle("(f) aucun badge Hektor -> on leve, et le message NOMME les entrees cherchees",
      /aucun cookie/i.test(r.leve) && r.leve.includes(GTI) && r.leve.includes(LBI),
      r.leve || "n'a pas leve");
  }

  // ═══ ①bis LE CHOIX DE L'ENTREE ══════════════════════════════════════════
  // Vecu le 26/09 : la-boite-immo.com avait un badge et a rendu 403 ; www.gti a repondu.
  controle("(a2) l'entree est choisie AVANT la boucle, pas pendant",
    /async function choisirEntree\(/.test(srcSonde), "aucun choix d'entree");
  controle("(a3) ⚠ chaque entree n'est essayee QU'UNE FOIS -- pas une boucle d'essais",
    /for \(const s of candidates\)/.test(srcSonde) && !/while/.test(
      srcSonde.slice(srcSonde.indexOf("async function choisirEntree("),
                     srcSonde.indexOf("async function choisirEntree(") + 600)),
    "un nouvel essai en boucle apres un refus prolongerait un bannissement");
  controle("(a4) si AUCUNE entree ne repond : on s'arrete et on ne conclut RIEN",
    /on n'a pas pu regarder/.test(srcSonde) && /aucune entree Hektor ne repond/.test(srcSonde),
    "un echec d'acces serait pris pour « aucune photo manquante »");

  // ═══ ② LA COMPARAISON DES LISTES ════════════════════════════════════════
  // C'est le coeur de la sonde : une photo presente chez Hektor et absente du miroir
  // signifie que le delta date_maj l'a manquee.
  const compare = (chezHektor, chezNous) => ({
    absentes: [...chezHektor].filter((x) => !chezNous.has(x)),
    disparues: [...chezNous].filter((x) => !chezHektor.has(x)),
  });
  let c = compare(new Set(["1", "2", "3"]), new Set(["1", "2", "3"]));
  controle("(g) listes identiques -> aucune divergence",
    !c.absentes.length && !c.disparues.length, JSON.stringify(c));
  c = compare(new Set(["1", "2", "3"]), new Set(["1", "2"]));
  controle("(h) ⚠ une photo en plus chez Hektor est DETECTEE",
    c.absentes.length === 1 && c.absentes[0] === "3", JSON.stringify(c));
  c = compare(new Set(["1"]), new Set(["1", "2"]));
  controle("(i) une photo retiree chez Hektor est signalee aussi",
    c.disparues.length === 1, JSON.stringify(c));

  // ═══ ③ LES REGLES DE PRUDENCE ═══════════════════════════════════════════
  controle("(j) un refus ARRETE la sonde (401/403/429/503)",
    /\[401, 403, 429, 503\]\.includes\(res\.status\)\) throw new Arret/.test(srcSonde),
    "un 403 n'arrete pas");
  controle("(k) une page de login arrete aussi",
    /session Hektor expiree/.test(srcSonde), "la session morte n'est pas detectee");
  controle("(l) la cadence est celle de HEKTOR (1 s), pas celle du CDN",
    /opt\("--intervalle", 1000\)/.test(srcSonde), "cadence trop rapide pour Hektor");
  controle("(m) elle n'ecrit RIEN",
    !/method:\s*"(POST|PATCH|PUT|DELETE)"/.test(srcSonde) && !/writeFileSync/.test(srcSonde),
    "une ecriture existe");
  controle("(n) elle vise les annonces les PLUS ANCIENNEMENT modifiees",
    /ORDER BY COALESCE\(s\.date_maj, ''\) ASC/.test(srcSonde),
    "un echantillon recent ne prouverait rien");
  controle("(o) une photo MANQUANTE fait SORTIR EN 1, donc elle se voit",
    /process\.exitCode = 1;/.test(srcSonde), "la divergence passerait inapercue");
  controle("(p) la lecture de galerie est IMPORTEE du worker, pas recopiee",
    /extractConsolePhotoEntries \} = require\("\.\/console_job_worker\.js"\)/.test(srcSonde),
    "deux extractions divergeraient");

  // ═══ ④ LE MEME CORRECTIF DANS LA DETECTION DOCUMENTAIRE ═════════════════
  controle("(q) la detection documentaire accepte les DEUX domaines",
    /HOTES_HEKTOR/.test(srcEnq), "elle filtrerait encore un seul domaine");
  controle("(r) et son adresse de base suit ses cookies",
    /session\.base \+ "\/admin\/xmlrpc\.php/.test(srcEnq),
    "elle appellerait un domaine pour lequel elle n'a pas de cookie");

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
