// EPREUVE DU VERROU 8 -- EN LECTURE SEULE, AVEC SON TEMOIN INVERSE
//                                                      19/10/2026, apres l'incident
//
// CE QU'ON EPROUVE. Le verrou 8 ajoute UNE CONDITION a la requete qui retire une
// photo :
//       app_console_photo?id=in.(...)&present_in_hektor=is.true&visible=is.true
//                                                              ^^^^^^^^^^^^^^^^
// C'est la BASE qui refuse, donc toute la protection tient dans ce bout de texte.
// Si la condition ne mordait pas -- faute de frappe, mauvaise syntaxe PostgREST --
// le script continuerait a retirer des photos masquees SANS QUE RIEN NE LE DISE.
//
// ⭐ ON NE PEUT PAS SE CONTENTER DU CAS QUI PASSE. La regle du projet : la nouvelle
//   condition doit EXCLURE la masquee **et** l'ancienne doit l'INCLURE. Sans le
//   second, un filtre qui ne rend jamais rien (parce qu'il est casse) passerait
//   pour un filtre qui protege.
//
// ⚠ AUCUNE ECRITURE : on remplace le PATCH par un GET avec LE MEME filtre. C'est
//   la meme chaine de caracteres, donc la meme semantique -- on eprouve le filtre,
//   pas une imitation du filtre.
//
//   node Console/test_verrou8_photo_masquee.js

const path = require("path");
// ⚠ LES TROIS MEMES CHARGEMENTS, DANS LE MEME ORDRE que accorder_photos_miroir.js
//   (l. 109-111). Le 3e porte les variables Supabase -- ma 1re version n'en chargeait
//   que deux et l'epreuve a echoue sur « SUPABASE_URL absents ». Une epreuve qui ne
//   lit pas le meme environnement que le code n'eprouve pas le code.
require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// La meme aide que le script corrige, recopiee a l'identique.
async function rest(pathname) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const reponse = await fetch(SUPABASE_URL + "/rest/v1/" + pathname.replace(/^\/+/, ""), {
    headers: { apikey: KEY, Authorization: "Bearer " + KEY, "Content-Type": "application/json" },
  });
  if (!reponse.ok) throw new Error("Supabase " + reponse.status + " " + (await reponse.text()).slice(0, 300));
  return reponse.json();
}

(async () => {
  let rouges = 0;
  const dire = (ok, texte) => { if (!ok) rouges += 1; console.log(`  ${ok ? "[ OK ]" : "[ROUGE]"} ${texte}`); };

  console.log("EPREUVE DU VERROU 8 -- lecture seule\n");

  // ── ① LA CIBLE : une photo MASQUEE et encore chez Hektor ────────────────────
  //   On la cherche, on ne la suppose pas. C'est celle du 19/10 si elle est encore
  //   dans cet etat, sinon n'importe quelle autre -- le verrou ne la connait pas.
  const masquees = await rest(
    "app_console_photo?visible=is.false&present_in_hektor=is.true"
    + "&select=id,hektor_annonce_id,hektor_photo_id&limit=1"
  );
  if (!Array.isArray(masquees) || !masquees.length) {
    console.log("  [ROUGE] AUCUNE photo masquee et presente en base : rien a eprouver.");
    console.log("          (ce n'est pas un succes : l'epreuve n'a PAS eu lieu)");
    process.exitCode = 2;
    return;
  }
  const cible = masquees[0];
  const id = encodeURIComponent(cible.id);
  console.log(`① LA CIBLE : annonce ${cible.hektor_annonce_id}, photo ${cible.hektor_photo_id}`);
  console.log(`   (masquee en base, et toujours chez Hektor)\n`);

  // ── ② LE TEMOIN INVERSE : L'ANCIEN FILTRE LA PREND ──────────────────────────
  //   Sans ce point, un filtre casse (qui ne rend jamais rien) passerait pour bon.
  const ancien = await rest(`app_console_photo?id=in.(${id})&present_in_hektor=is.true&select=id`);
  console.log("② TEMOIN INVERSE -- l'ANCIEN filtre (sans `visible=is.true`)");
  dire(Array.isArray(ancien) && ancien.length === 1,
       `il prend bien la photo : ${Array.isArray(ancien) ? ancien.length : "?"} ligne(s) -- `
       + `donc elle ETAIT a la portee du marquage`);

  // ── ③ LE VERROU : LE NOUVEAU FILTRE LA LAISSE ───────────────────────────────
  const neuf = await rest(`app_console_photo?id=in.(${id})&present_in_hektor=is.true&visible=is.true&select=id`);
  console.log("\n③ LE VERROU 8 -- le NOUVEAU filtre (avec `visible=is.true`)");
  dire(Array.isArray(neuf) && neuf.length === 0,
       `il la LAISSE : ${Array.isArray(neuf) ? neuf.length : "?"} ligne(s) -- `
       + `la base refuse de la retirer`);

  // ── ④ ET IL NE PROTEGE PAS TROP : une VISIBLE reste a portee ────────────────
  //   Un filtre qui bloquerait TOUT serait aussi faux : les 371 vrais reportages
  //   remplaces doivent continuer a sortir.
  const visibles = await rest(
    "app_console_photo?visible=is.true&present_in_hektor=is.true&select=id&limit=1"
  );
  console.log("\n④ ET IL NE BLOQUE PAS TOUT -- une photo VISIBLE reste a portee");
  if (Array.isArray(visibles) && visibles.length) {
    const vid = encodeURIComponent(visibles[0].id);
    const portee = await rest(`app_console_photo?id=in.(${vid})&present_in_hektor=is.true&visible=is.true&select=id`);
    dire(Array.isArray(portee) && portee.length === 1,
         `elle est bien prise : ${Array.isArray(portee) ? portee.length : "?"} ligne(s) -- `
         + `les vrais reportages remplaces sortiront toujours`);
  } else {
    dire(false, "aucune photo visible trouvee -- point NON EPROUVE");
  }

  // ── ⑤ LA SYNTAXE EST-ELLE BIEN COMPRISE ? ───────────────────────────────────
  //   ⚠ Un filtre que PostgREST ne comprend pas rend une ERREUR, pas une liste
  //     vide -- et `rest()` leve. Si on arrive ici, les trois requetes ont ete
  //     acceptees : la syntaxe `visible=is.true` est valide. C'est dit, pas suppose.
  console.log("\n⑤ LA SYNTAXE");
  dire(true, "les 3 requetes ont ete ACCEPTEES par Supabase -- `visible=is.true` est valide");

  console.log(`\n${rouges === 0 ? "✅ TOUT EST VERT" : "⛔ " + rouges + " ROUGE(S)"}`);
  console.log("⚠ CE QUE CETTE EPREUVE NE COUVRE PAS : le chemin d'ECRITURE du script");
  console.log("  (il ne tourne qu'avec --appliquer). Son juge est le passage reel de");
  console.log("  21:00, et la ligne `sauvees_par_le_verrou_8` de son compte rendu.");
  process.exitCode = rouges === 0 ? 0 : 1;
})().catch((e) => {
  console.error("\n⛔ " + (e && e.message ? e.message : String(e)));
  process.exitCode = 1;
});
