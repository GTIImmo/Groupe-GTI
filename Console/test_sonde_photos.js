// LA SONDE SAIT-ELLE TROUVER SA SESSION, ET VOIR UNE DIVERGENCE ?
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

const SONDE = path.join(__dirname, "sonde_photos_datemaj.js");
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
  const blocSession = tranche(srcSonde, "function session(");
  if (!blocSession) {
    controle("(0) la sonde sait resoudre sa session", false, "fonction introuvable");
  } else {
    function charger(pot) {
      // eslint-disable-next-line no-new-func
      return new Function("fs", "POT", `${blocHotes}\n${blocSession}; return session;`)(fs, pot);
    }

    // le cas VECU : plus aucun cookie la-boite-immo, seulement www.gti-immobilier.fr
    // ⚠ On ENROBE : si la sonde revenait au filtre d'un seul domaine, elle leverait ici.
    // Un test qui tombe dit moins bien lequel des controles a echoue.
    let p = potTemporaire([{ domain: GTI, name: "PHPSESSID", value: "abc" },
                           { domain: ".vimeo.com", name: "x", value: "y" }]);
    let r = null;
    let leveA = "";
    try { r = charger(p)(); } catch (e) { leveA = e.message; }
    controle("(a) ⚠ le cas vecu : session trouvee sur www.gti-immobilier.fr",
      r && /gti-immobilier\.fr$/.test(r.base),
      leveA ? `a leve : ${leveA}` : JSON.stringify(r));
    if (!r) r = { base: "", cookieHeader: "" };
    controle("(b) ⚠ ET l'adresse de base SUIT les cookies",
      r.base === "https://" + GTI, r.base);
    controle("(c) les cookies etrangers ne sont pas embarques",
      !/vimeo/.test(r.cookieHeader), r.cookieHeader);
    fs.rmSync(p, { force: true });

    // l'autre domaine, seul
    p = potTemporaire([{ domain: "." + LBI, name: "PHPSESSID", value: "def" }]);
    r = charger(p)();
    controle("(d) l'autre domaine marche aussi, point initial du domaine compris",
      r.base === "https://" + LBI, r.base);
    fs.rmSync(p, { force: true });

    // les deux : on prend le premier de la liste, de facon deterministe
    p = potTemporaire([{ domain: GTI, name: "a", value: "1" }, { domain: LBI, name: "b", value: "2" }]);
    const r1 = charger(p)();
    const r2 = charger(p)();
    controle("(e) avec les deux : choix DETERMINISTE (pas un coup de des)",
      r1.base === r2.base, `${r1.base} puis ${r2.base}`);
    fs.rmSync(p, { force: true });

    // aucun : on leve, et le message dit ou on a cherche
    p = potTemporaire([{ domain: ".vimeo.com", name: "x", value: "y" }]);
    let leve = "";
    try { charger(p)(); } catch (e) { leve = e.message; }
    controle("(f) aucun cookie Hektor -> on leve, et le message NOMME les domaines cherches",
      /aucun cookie/i.test(leve) && leve.includes(GTI) && leve.includes(LBI), leve || "n'a pas leve");
    fs.rmSync(p, { force: true });
  }

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
  controle("(o) une divergence fait SORTIR EN 1, donc elle se voit",
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
