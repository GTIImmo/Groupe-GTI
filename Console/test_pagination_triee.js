// UNE LECTURE PAGINEE EST-ELLE TRIEE SUR UNE CLE UNIQUE ?
//                                                                  25/09/2026 (soir)
// DEFAUT VECU LE SOIR MEME, et il a coute 40 % d'un travail de 7 heures.
//
// Le rapatriement des photos a relu 436 000 lignes par pages de 1 000, avec un simple
// decalage et SANS ORDER BY. Postgres n'est pas tenu de rendre les lignes dans le meme
// ordre d'une page a l'autre : certaines reviennent deux fois, d'autres JAMAIS.
// Resultat : 174 433 photos sur 435 126 absentes de la table de correspondance, comptees
// « en echec » alors que le CDN n'avait rien refuse. Aucun message d'erreur, aucun refus.
// Un defaut parfaitement muet -- exactement la classe qu'on traque dans ce projet.
//
// LA PARADE, verifiee ici sur LES TROIS scripts concernes :
//   - la cle de tri est OBLIGATOIRE (on refuse de lire sans elle) ;
//   - elle doit etre UNIQUE ;
//   - si un ordre metier existe deja, elle s'ajoute en DERNIER critere -- « plus ancien
//     d'abord » ne departage pas deux lignes de meme date.
//
//   node Console/test_pagination_triee.js
// N'APPELLE NI HEKTOR NI SUPABASE.

const fs = require("fs");
const path = require("path");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

// Compte les arguments d'un appel en EQUILIBRANT les parentheses. Une expression
// reguliere simple echoue ici : les chemins contiennent « in.(pending,running) », et
// certains appels tiennent sur trois lignes. Premiere version du test faussement rouge
// pour ces deux raisons -- le code, lui, etait juste.
function appels(src, nom) {
  const out = [];
  let i = 0;
  while ((i = src.indexOf(nom + "(", i)) >= 0) {
    let prof = 0, args = 1, j = i + nom.length;
    for (; j < src.length; j += 1) {
      const c = src[j];
      if (c === "(") prof += 1;
      else if (c === ")") { prof -= 1; if (prof === 0) break; }
      else if (c === "," && prof === 1) args += 1;
    }
    out.push(args);
    i = j + 1;
  }
  return out;
}

function extraire(fichier, marque) {
  const src = fs.readFileSync(path.join(__dirname, fichier), "utf8");
  const i = src.indexOf(marque);
  if (i < 0) return { src, bloc: null };
  const f = src.indexOf("\n}", i);
  return { src, bloc: f < 0 ? null : src.slice(i, f + 2) };
}

(async () => {
  // ── ① rattrapage_photos.js et reprendre_envois_hektor.js : tout() ──────────
  for (const fichier of ["rattrapage_photos.js", "reprendre_envois_hektor.js"]) {
    const { src, bloc } = extraire(fichier, "async function tout(");
    if (!bloc) { controle(`(${fichier}) tout() est present`, false, "introuvable"); continue; }

    const vus = [];
    // eslint-disable-next-line no-new-func
    const tout = new Function("rest", `${bloc}; return tout;`)(async (chemin) => {
      vus.push(chemin);
      return vus.length === 1 ? [{ id: 1 }] : [];
    });

    let refuse = false;
    try { await tout("app_x?select=id"); } catch (_) { refuse = true; }
    controle(`(a) ${fichier} : lire SANS cle de tri est REFUSE`, refuse,
      "une lecture non triee passe encore");

    vus.length = 0;
    await tout("app_x?select=id", "id");
    controle(`(b) ${fichier} : le tri est ajoute quand il n'y en a pas`,
      /[?&]order=id\.asc/.test(vus[0] || ""), vus[0] || "aucune lecture");

    // ⚠ Le curseur impose SON ordre. Un ordre metier dans le chemin produirait deux
    // « order= » concurrents -> on le refuse, et l'appelant trie apres lecture.
    let refuseOrdre = false;
    try { await tout("app_x?select=id&order=date.asc", "id"); } catch (_) { refuseOrdre = true; }
    controle(`(c) ${fichier} : un ordre metier dans le chemin est REFUSE`, refuseOrdre,
      "deux ordres concurrents seraient envoyes");

    // ⚠ LE CONTROLE CENTRAL : on avance PAR CURSEUR, pas par decalage. Le decalage sur
    // 400 000 lignes fait expirer la requete -- defaut vecu le 25/09 au soir.
    vus.length = 0;
    let n2 = 0;
    // eslint-disable-next-line no-new-func
    const tout3 = new Function("rest", `${bloc}; return tout;`)(async (chemin) => {
      vus.push(chemin);
      n2 += 1;
      return n2 === 1 ? new Array(1000).fill(0).map((_, k) => ({ id: k + 1 })) : [];
    });
    await tout3("app_x?select=id", "id");
    controle(`(d) ${fichier} : la page suivante demande « apres le dernier », pas un decalage`,
      /id=gt\.1000/.test(vus[1] || "") && !/offset=/.test(vus[1] || ""), vus[1] || "une seule page");

    // la pagination elle-meme continue de fonctionner
    vus.length = 0;
    let page = 0;
    // eslint-disable-next-line no-new-func
    const tout2 = new Function("rest", `${bloc}; return tout;`)(async () => {
      page += 1;
      return page <= 2 ? new Array(1000).fill({ id: page }) : [];
    });
    const r = await tout2("app_x?select=id", "id");
    controle(`(e) ${fichier} : la pagination va jusqu'au bout`, r.length === 2000, String(r.length));

    // et plus aucun appel non trie ne subsiste dans le fichier
    const lectures = appels(src, "await tout").filter((n) => n > 0);
    controle(`(f) ${fichier} : les ${lectures.length} lectures passent toutes une cle`,
      lectures.every((n) => n >= 2), `arguments par appel : ${lectures.join(", ")}`);
  }

  // ── ② enqueue_empreinte_lot.js : loadSet() ────────────────────────────────
  const { src, bloc } = extraire("enqueue_empreinte_lot.js", "async function loadSet(");
  if (!bloc) {
    controle("(g) enqueue_empreinte_lot : loadSet() est present", false, "introuvable");
  } else {
    const vus = [];
    // eslint-disable-next-line no-new-func
    const loadSet = new Function("rest", `${bloc}; return loadSet;`)(async (chemin) => {
      vus.push(chemin);
      return vus.length === 1 ? [{ hektor_annonce_id: 7, id: "z9" }] : [];
    });
    await loadSet("app_y?select=id,hektor_annonce_id", "hektor_annonce_id", "id");
    controle("(g) enqueue_empreinte_lot : le tri est pose",
      /[?&]order=id\.asc/.test(vus[0] || ""), vus[0] || "aucune lecture");
    vus.length = 0;
    await loadSet("app_y?select=hektor_annonce_id", "hektor_annonce_id");
    controle("(h) enqueue_empreinte_lot : a defaut, la colonne lue sert de tri",
      /[?&]order=hektor_annonce_id\.asc/.test(vus[0] || ""), vus[0] || "-");
    const lectures = appels(src, "await loadSet");
    controle(`(i) enqueue_empreinte_lot : les ${lectures.length} lectures passent une cle`,
      lectures.length === 3 && lectures.every((n) => n >= 3),
      `arguments par appel : ${lectures.join(", ")}`);
  }

  console.log(`\n${echecs ? `${echecs} ECHEC(S)` : "TOUT VERT"}`);
  process.exit(echecs ? 1 : 0);
})();
