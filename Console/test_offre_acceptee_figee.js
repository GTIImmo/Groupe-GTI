// UNE OFFRE ACCEPTEE EST FIGEE CHEZ HEKTOR -- l'ecran l'eteint, le worker le dit
//                                                                      13/10/2026
// MESURE QUI FONDE CE TEST (lecture seule, 12 offres reelles, 13/10) : l'ouverture du
// formulaire d'offre chez Hektor (`createOffre` + `init=1` + `idOffre`) depend de l'ETAT :
//     accepted   200 + 0 OCTET              9 sur 9
//     proposed   200 + ~230 000 octets      2 sur 2   (et pre-remplie)
//     refused    200 + ~230 000 octets      1 sur 1   (et pre-remplie)
// Hektor n'ouvre meme pas le formulaire d'une offre acceptee, et son refus est MUET.
// Le worker traduisait ce vide en « Reponse Hektor JSON invalide init Sous offre: »,
// rien apres les deux-points, et cette phrase partait telle quelle au negociateur ;
// puis le filet la rejouait 5 fois. 144 des 185 offres vivantes sont acceptees.
// notice/MESURE_MODIFIER_OFFRE_ACCEPTEE_2026-10-13.md
//
// Il lit les DEUX sources (worker et front) et fait tourner LE VRAI CODE qu'il en
// decoupe, avec de faux appels. N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT AUCUN FICHIER.
//
//     node Console/test_offre_acceptee_figee.js

const fs = require("fs");
const path = require("path");

const WORKER = path.join(__dirname, "console_job_worker.js");
const FRONT = path.join(__dirname, "..", "apps", "hektor-v1", "src", "App.tsx");
// ⚠ LES FINS DE LIGNE, PIEGE DEJA PAYE : console_job_worker.js est en CRLF (20 649
//   lignes), App.tsx en LF. Un decoupage qui cherche « \n  } » ne trouve RIEN dans un
//   fichier CRLF -- premiere version de ce test, 13/10. On normalise pour DECOUPER ;
//   le code decoupe tourne pareil.
const src = fs.readFileSync(WORKER, "utf8").replace(/\r\n/g, "\n");
const front = fs.readFileSync(FRONT, "utf8").replace(/\r\n/g, "\n");
const MARQUE = "[REFUS D'ETAT]";

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

function trancheFonction(texte, debutMarque) {
  const i = texte.indexOf(debutMarque);
  if (i < 0) return null;
  const f = texte.indexOf("\n}", i);
  return f < 0 ? null : texte.slice(i, f + 2);
}

// ── (B) LE WORKER ───────────────────────────────────────────────────────────────

// Le garde vit DANS submitHektorTransactionStatus : on le decoupe et on le fait
// tourner avec ses variables libres, plutot que d'en recopier la logique.
const DEBUT_GARDE = `  if (!String(init.text || "").trim()) {`;
const iGarde = src.indexOf(DEBUT_GARDE);
const fGarde = iGarde < 0 ? -1 : src.indexOf("\n  }\n", iGarde);
const blocGarde = iGarde < 0 || fGarde < 0 ? null : src.slice(iGarde, fGarde + 5);

function ouvrir({ texte, payload = {}, genre = "offre", idRepris = "", target = "offer" }) {
  const f = new Function(
    "init", "payload", "genreTransaction", "idRepris", "target", "config", "MARQUE_REFUS_ETAT",
    `${blocGarde}\nreturn "PAS DE LEVEE";`);
  try {
    return { leve: false, valeur: f({ text: texte }, payload, genre, idRepris, target,
      { label: "Sous offre" }, MARQUE) };
  } catch (error) {
    return { leve: true, message: error && error.message ? error.message : String(error) };
  }
}

// ── (A) LE FRONT ────────────────────────────────────────────────────────────────

// La vraie fonction du front, ses annotations de type retirees -- on la FAIT TOURNER
// au lieu de se fier a une relecture.
const blocHelper = trancheFonction(front, "function offreAccepteeFigeeChezHektor(");
const helperJs = blocHelper
  ? blocHelper.replace(/:\s*AffaireLedgerRow \| null \| undefined/, "").replace(/\)\s*:\s*boolean/, ")")
  : null;
const figee = helperJs
  ? new Function(`${helperJs}\nreturn offreAccepteeFigeeChezHektor;`)()
  : null;

(async () => {
  console.log("(B) LE WORKER -- le refus muet devient une phrase\n");

  controle("(B0) le garde est bien present dans le source", Boolean(blocGarde), "bloc introuvable");
  if (!blocGarde) { console.log("\nECHEC : rien a eprouver."); process.exit(1); }

  // ── (B1) l'offre acceptee : la phrase dit l'etat, la cause ET le remede ──
  const r1 = ouvrir({ texte: "", payload: { offre_state: "accepted" }, idRepris: "33094" });
  controle("(B1a) corps vide en reprise d'offre -> ca leve", r1.leve, r1.valeur);
  controle("(B1b) la marque de refus d'etat y est", r1.leve && r1.message.includes(MARQUE), r1.message);
  controle("(B1c) le numero de l'offre y est", r1.leve && r1.message.includes("33094"), r1.message);
  controle("(B1d) l'etat lu y est", r1.leve && /accepted/.test(r1.message), r1.message);
  controle("(B1e) le remede y est (refuser, corriger, accepter)",
    r1.leve && /refuser/i.test(r1.message) && /accepter/i.test(r1.message), r1.message);
  controle("(B1f) il dit que rien n'est parti chez Hektor",
    r1.leve && /[Rr]ien n'a ete envoye/.test(r1.message), r1.message);

  // ── (B2) LE TEMOIN INVERSE : un corps NON VIDE passe comme avant ──
  // C'est le cas des 10 envois d'offre de l'historique : Hektor repond TOUJOURS
  // `error: true`, le formulaire arrive quand meme, et le worker doit continuer.
  const r2 = ouvrir({ texte: '{"error":true,"html":"<form>...</form>"}',
    payload: { offre_state: "proposed" }, idRepris: "33050" });
  controle("(B2) corps NON vide -> aucune levee, le chemin d'avant est intact",
    !r2.leve && r2.valeur === "PAS DE LEVEE", r2.message || String(r2.valeur));

  // ── (B3) on ne donne pas un conseil d'offre pour un compromis ──
  const r3 = ouvrir({ texte: "", payload: { compromis_state: "signed" }, genre: "compromis",
    idRepris: "50043", target: "compromise" });
  controle("(B3a) compromis : ca leve avec la marque", r3.leve && r3.message.includes(MARQUE), r3.message);
  controle("(B3b) compromis : AUCUN conseil propre a l'offre",
    r3.leve && !/refuser/i.test(r3.message), r3.message);

  // ── (B4) une creation (aucune reprise) garde une phrase generique ──
  const r4 = ouvrir({ texte: "", payload: {}, idRepris: "" });
  controle("(B4a) creation : ca leve avec la marque", r4.leve && r4.message.includes(MARQUE), r4.message);
  controle("(B4b) creation : la phrase ne parle pas de rouvrir une transaction",
    r4.leve && /ouvrir le formulaire/.test(r4.message) && !/rouvrir/.test(r4.message), r4.message);

  // ── (B5) LE GARDE PASSE AVANT parseHektorJson -- sinon il ne sert a rien ──
  const iParse = src.indexOf("parseHektorJson(init.text");
  controle("(B5) le garde est AVANT parseHektorJson(init.text)",
    iGarde > 0 && iParse > iGarde, `garde=${iGarde} parse=${iParse}`);

  // ── (B6) LE FREIN DE REJEU : on fait tourner le VRAI finishJob ──
  const blocFinish = trancheFonction(src, "async function finishJob(");
  controle("(B6a) finishJob est decoupable", Boolean(blocFinish), "introuvable");
  if (blocFinish) {
    const envois = [];
    const faire = new Function("supabaseRequest", "REJEU_MAX_TENTATIVES",
      `${blocFinish}\nreturn finishJob;`)(
      async (chemin, options) => { envois.push({ chemin, corps: JSON.parse(options.body) }); },
      5);
    await faire("j1", "error", null, `${MARQUE} refus`, { nePlusRejouer: true });
    await faire("j2", "error", null, "Hektor timeout 45000ms", {});
    await faire("j3", "done", { ok: 1 }, null);
    controle("(B6b) refus d'etat -> attempt_count pose au maximum (sort de la file)",
      envois[0] && envois[0].corps.attempt_count === 5, JSON.stringify(envois[0] && envois[0].corps));
    controle("(B6c) TEMOIN INVERSE : une panne ordinaire garde son rejeu",
      envois[1] && envois[1].corps.attempt_count === undefined, JSON.stringify(envois[1] && envois[1].corps));
    controle("(B6d) un succes n'est pas touche",
      envois[2] && envois[2].corps.attempt_count === undefined && envois[2].corps.status === "done",
      JSON.stringify(envois[2] && envois[2].corps));
  }

  // ── (B7) processOnce lit la marque et la transmet ──
  const lignesCode = src.split("\n").filter((l) => !l.trim().startsWith("//"));
  controle("(B7a) processOnce detecte la marque",
    lignesCode.some((l) => /message\.includes\(MARQUE_REFUS_ETAT\)/.test(l)), "detection absente");
  controle("(B7b) et la transmet a finishJob",
    lignesCode.some((l) => /finishJob\(job\.id, "error", null, message, \{ nePlusRejouer: refusDEtat \}\)/.test(l)),
    "transmission absente");

  console.log("\n(A) LE FRONT -- l'ecran n'offre plus le geste impossible\n");

  controle("(A0) la fonction du front est decoupable et executable", typeof figee === "function",
    "introuvable ou non executable");
  if (typeof figee === "function") {
    controle("(A1) offre acceptee -> figee", figee({ kind: "offre", state: "accepted" }) === true);
    // LE TEMOIN INVERSE, et il porte la decision du 07/09 : on ne bride QUE le cas mesure.
    controle("(A2) offre REFUSEE -> libre (demande de Frederic du 07/09)",
      figee({ kind: "offre", state: "refused" }) === false);
    controle("(A3) offre proposee -> libre", figee({ kind: "offre", state: "proposed" }) === false);
    controle("(A4) etat inconnu -> libre (on laisse Hektor dire)",
      figee({ kind: "offre", state: null }) === false);
    controle("(A5) compromis accepte -> libre (Hektor refuse en clair, lui)",
      figee({ kind: "compromis", state: "accepted" }) === false);
    controle("(A6) vente -> libre", figee({ kind: "vente", state: "accepted" }) === false);
    controle("(A7) rien -> libre", figee(null) === false);
    controle("(A8) la casse et les espaces ne trompent pas",
      figee({ kind: "offre", state: "  ACCEPTED " }) === true);
  }

  // ── (A9) le bouton et le bandeau s'en servent vraiment ──
  controle("(A9) le bouton « Modifier chez Hektor » est eteint par la fonction",
    /disabled=\{statusChangePending \|\| statusChangeCorrectionPending[\s\S]{0,400}?offreAccepteeFigeeChezHektor\(affaireCourantePourStatut\(\)\)\}/
      .test(front), "le disabled du bouton n'appelle pas la fonction");
  controle("(A10) un bandeau explique en clair (pas de bouton gris et muet)",
    /offreAccepteeFigeeChezHektor\(affaire\)[\s\S]{0,900}?status-change-note/.test(front)
    && /son montant ne se corrige plus/.test(front), "bandeau absent");
  controle("(A11) le conseil « refusez l'offre » se tait quand « Refuser » est cache",
    /refusHorsDePortee[\s\S]{0,300}?offreVerrouilleeParSonDossier/.test(front),
    "le cas du verrou par le dossier n'est pas traite");

  console.log(`\n${echecs === 0 ? "TOUT VERT" : `${echecs} ECHEC(S)`}`);
  process.exit(echecs === 0 ? 0 : 1);
})();
