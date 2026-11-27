/* P5-a (27/11/2026) -- le parcours de l'AVIS DE VALEUR : ses cases sont-elles EXACTEMENT celles de l'éditeur ?
 *   ① les 23 cases du serveur (backend/app/services/parcours_avis.json) = celles que l'écran des questions sait montrer
 *     (CATALOGUE_AVIS de ParcoursGuide.tsx) + la grille des postes ;
 *   ② chacune est une case du BROUILLON de l'éditeur (initialDraft d'EstimationDocumentEditor, App.tsx), sauf
 *     « destinataire » (un choix, jamais une adresse) ; le brouillon n'a en plus que le propriétaire et son e-mail
 *     (24 = 22 + 2), que le parcours ne touche jamais ;
 *   ③ les postes et les niveaux : les mêmes clés, dans le même ordre de niveaux, que ESTIM_POSTES et ESTIM_NIVEAUX ;
 *   ④ les listes (contexte, DPE, GES, étoiles, destinataire) : les mêmes valeurs des deux côtés.
 * Lecture seule. Lancer : node test_etape4_parcours_avis.cjs (sortie 0 = vert).
 */
const fs = require("fs");
const path = require("path");

let ok = 0;
function voir(vrai, libelle) {
  if (!vrai) { console.error("  ROUGE " + libelle); process.exit(1); }
  ok += 1;
  console.log("  VERT  " + libelle);
}

const src = path.join(__dirname, "src");
const guide = fs.readFileSync(path.join(src, "ParcoursGuide.tsx"), "utf8");
const app = fs.readFileSync(path.join(src, "App.tsx"), "utf8");
const donnees = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "..", "backend", "app", "services", "parcours_avis.json"), "utf8"));

// l'écran des questions : le bloc CATALOGUE_AVIS
const bloc = guide.slice(guide.indexOf("const CATALOGUE_AVIS"), guide.indexOf("// = ESTIM_POSTES"));
const casesEcran = [...bloc.matchAll(/\{ nom: '([A-Za-z]+)', libelle: '((?:[^'\\]|\\.)*)'|\{ nom: '([A-Za-z]+)', libelle: "([^"]*)"/g)].map((m) => m[1] || m[3]);
const serveur = Object.keys(donnees.cases);
voir(casesEcran.length === 22 && new Set(casesEcran).size === 22, "l'écran des questions connaît 22 cases, sans doublon");
voir(JSON.stringify([...casesEcran, "etatPostes"].sort()) === JSON.stringify([...serveur].sort()),
  "① les cases du serveur = celles de l'écran + la grille des postes (23)");
const nommees = new Set(donnees.questions.flatMap((q) => q.champs));
voir(serveur.every((c) => nommees.has(c)) && nommees.size === serveur.length, "chaque case est posée par une question, une seule fois");

// le brouillon de l'éditeur
const debut = app.indexOf("const initialDraft = useMemo(() => ({", app.indexOf("function EstimationDocumentEditor"));
const brouillon = app.slice(debut, app.indexOf("}), [", debut));
const clesBrouillon = [...brouillon.matchAll(/^\s+([A-Za-z]+):/gm)].map((m) => m[1])
  .concat([...brouillon.matchAll(/,\s*([A-Za-z]+):\s*''/g)].map((m) => m[1]));
const brouillonSet = new Set(clesBrouillon);
voir(brouillonSet.size === 24, `② le brouillon de l'éditeur a 24 cases (lu : ${brouillonSet.size})`);
const horsDestinataire = serveur.filter((c) => c !== "destinataire");
voir(horsDestinataire.every((c) => brouillonSet.has(c)), "② chaque case du parcours (sauf « destinataire ») est une case du brouillon de l'éditeur");
const reste = [...brouillonSet].filter((c) => !serveur.includes(c)).sort();
voir(JSON.stringify(reste) === JSON.stringify(["ownerName", "recipient"]),
  "② le brouillon n'a en plus que le propriétaire et son e-mail -- jamais touchés par le parcours");

// les postes et les niveaux
const postesApp = [...app.slice(app.indexOf("const ESTIM_POSTES"), app.indexOf("const ESTIM_NIVEAUX")).matchAll(/key: '([a-z]+)'/g)].map((m) => m[1]);
const niveauxApp = [...app.slice(app.indexOf("const ESTIM_NIVEAUX"), app.indexOf("\n", app.indexOf("const ESTIM_NIVEAUX"))).matchAll(/\['([a-z]+)'/g)].map((m) => m[1]);
const postesEcran = [...guide.slice(guide.indexOf("const POSTES_AVIS"), guide.indexOf("const NIVEAUX_AVIS")).matchAll(/\['([a-z]+)'/g)].map((m) => m[1]);
const niveauxEcran = [...guide.slice(guide.indexOf("const NIVEAUX_AVIS"), guide.indexOf("type PostesAvis")).matchAll(/\['([a-z]+)'/g)].map((m) => m[1]);
voir(postesApp.length === 8 && JSON.stringify([...postesEcran].sort()) === JSON.stringify([...postesApp].sort())
  && JSON.stringify(Object.keys(donnees.postes).sort()) === JSON.stringify([...postesApp].sort()), "③ les 8 postes : les mêmes clés dans l'éditeur, l'écran et le serveur");
voir(JSON.stringify(niveauxEcran) === JSON.stringify(niveauxApp) && JSON.stringify(Object.keys(donnees.niveaux)) === JSON.stringify(niveauxApp),
  "③ les 4 niveaux : les mêmes, dans le même ordre");

// les listes
function optionsEcran(nom) {
  const i = bloc.indexOf(`nom: '${nom}'`);
  const ligne = bloc.slice(i, bloc.indexOf("\n", i));
  if (ligne.includes("LETTRES")) return ["A", "B", "C", "D", "E", "F", "G"];
  if (ligne.includes("['1', '2', '3', '4', '5']")) return ["1", "2", "3", "4", "5"];
  return [...ligne.matchAll(/value: '([a-z]+)'/g)].map((m) => m[1]);
}
for (const [nom, spec] of Object.entries(donnees.cases).filter(([, s]) => s.genre === "choix")) {
  voir(JSON.stringify(optionsEcran(nom)) === JSON.stringify(spec.valeurs), `④ « ${nom} » : les mêmes choix (${spec.valeurs.join(", ")})`);
}
const variantesEditeur = [...app.slice(app.indexOf("<span>Contexte de l'email</span>"), app.indexOf("</select>", app.indexOf("<span>Contexte de l'email</span>"))).matchAll(/option value="([a-z]+)"/g)].map((m) => m[1]);
voir(JSON.stringify(variantesEditeur) === JSON.stringify(donnees.cases.variante.valeurs), "④ le contexte de l'e-mail : les mêmes choix que la liste de l'éditeur");

console.log(`\nTOUT EST VERT (${ok} contrôles)`);
