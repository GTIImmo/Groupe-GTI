// METTRE NOTRE REGISTRE DE PHOTOS D'ACCORD AVEC CE QUE HEKTOR LISTE
//                                                   15/10/2026 — chantier 6, point 6d
//
// ⚠⚠ IL TOURNE CHAQUE NUIT, AVEC `--appliquer`. Depuis le 15/10 12:35 il est la
//    LIGNE 4/4 de la tache « GTI Entretien Documents » (22:00) --
//    run_entretien_documents.ps1 : `if (-not $DryRun) { $argsPhotos += "--appliquer" }`.
//    ⛔ CE COMMENTAIRE A DIT « DORMANT : aucune tache ne l'appelle » PENDANT TROIS
//      JOURS APRES AVOIR ETE BRANCHE, et il a trompe une relecture du 18/10. Un
//      commentaire qui dit autre chose que le planificateur est la derive que ce
//      projet paie en boucle. Corrige le 18/10.
//    `--dry-run` reste le DEFAUT quand on le lance A LA MAIN.
//
// ⭐ POURQUOI A 22:00 ET PAS DANS LE RUN DE 05:00, ou vivent les 4 autres etapes
//    photos : il compare DEUX COPIES LOCALES -- le miroir Hektor (rafraichi par le
//    run vers 06:47) et NOTRE registre (phase2.sqlite, rafraichi par la DESCENTE de
//    07:45). A 05:00 aucune des deux n'est a jour ; a 22:00 les deux le sont.
//    ⚠ ET IL EST LE SEUL DES CINQ A RETIRER : les 4 etapes du run AJOUTENT
//      (telecharger, fabriquer les derives, poser nos adresses, sonder). Lui seul
//      marque `present_in_hektor = false`. C'est le dangereux : il merite d'etre
//      nomme, pas cache dans une tache appelee « Documents ».
//
// POURQUOI. Mesure du 15/10 :
//     440 photos que nous affichons et que Hektor NE LISTE PLUS  (67 annonces)
//   1 662 photos dans un ORDRE different                         (290 annonces)
//      56 annonces du site public avec LA MAUVAISE PHOTO D'ACCROCHE
//      34 annonces du site public qui montrent encore des photos retirees
//   Le marquage existe pourtant (upsertConsolePhotos, console_job_worker.js:4510) --
//   mais il ne tourne que dans un travail `sync_hektor_photos`, et il n'en a plus ete
//   pose depuis le 27/09. Personne ne compare donc notre liste a celle de Hektor.
//
// ⚠ CE SCRIPT NE PARLE JAMAIS A HEKTOR. Tout est deja chez nous : le miroir local
//   (data/hektor.sqlite, hektor_annonce_detail.images_json) porte l'id de chaque photo,
//   son ORDRE et son drapeau visible, et il est relu chaque nuit par le balayage normal
//   (mesure du 15/10 : 23 547 des 23 567 annonces non archivees relues le jour meme).
//   Meme principe que rattrapage_photos.js, dont ce fichier est le frere.
//
// ⚠ IL NE SUPPRIME RIEN, JAMAIS. « delete-never » : une photo retiree chez Hektor se
//   MARQUE (present_in_hektor = false + absent_depuis). La ligne reste, le fichier reste
//   sur le serveur, et l'adresse publique de son derive continue de servir -- c'est tout
//   le sens de G.10bis : l'id de la ligne est load-bearing.
//
// ═══════════════════════════════════════════════════════════════════════════════════
// LES SIX VERROUS — et deux d'entre eux viennent de questions de Frederic (15/10)
// ═══════════════════════════════════════════════════════════════════════════════════
//
// ⭐ 1. UNE LECTURE FRAICHE EST EXIGEE  (« j'ai peur du jour de la coupure »)
//    On ne conclut l'absence d'une photo que si la fiche detail de SON annonce a ete
//    relue dans les N dernieres heures (48 par defaut). Pas de lecture fraiche = AUCUNE
//    conclusion.
//    ➡ LE JOUR DE LA COUPURE, PLUS AUCUNE ANNONCE N'A DE LECTURE FRAICHE, DONC CE
//      SCRIPT NE MARQUE PLUS RIEN, TOUT SEUL. Personne n'a a penser a le desactiver.
//
// ⭐ 2. LES PHOTOS AJOUTEES DEPUIS L'APP SONT INTOUCHABLES  (« attention, ton correctif
//    ne doit pas retirer les photos ajoutees a partir de l'app »)
//    Le piege a DEUX formes :
//      a) l'envoi en cours : app_console_creer_photo_optimistic cree la ligne avec
//         source = 'app', envoi_hektor_statut = 'a_envoyer' et hektor_photo_id NULL --
//         elle ne peut donc correspondre a rien dans images_json ;
//      b) LA FORME SOURNOISE : une photo deja confirmee par Hektor DANS LA JOURNEE porte
//         bien un hektor_photo_id, mais le miroir ne la connait pas encore (il ne se
//         rafraichit qu'au run de 05:00). Elle RESSEMBLE a une photo retiree.
//    ➡ D'ou trois conditions, toutes necessaires, pour marquer :
//         . la photo porte un hektor_photo_id         (Hektor l'a connue un jour)
//         . elle est PLUS ANCIENNE que la lecture du miroir de son annonce
//         . ce n'est pas une ligne `app` dont l'envoi n'est pas abouti
//    ⚠ Et le drapeau n'est pas anodin : le front CACHE ce qui est a false
//      (loadConsolePhotos filtre present_in_hektor = true). Marquer a tort, c'est faire
//      DISPARAITRE de l'ecran la photo qu'un negociateur vient de deposer.
//
// 3. JAMAIS DEPUIS UNE LISTE VIDE. Si images_json est vide alors que nous avons des
//    photos, on ne marque RIEN et on le DIT (garde-fou 3e du 13/10, meme regle que le
//    worker). Une annonce peut legitimement n'avoir aucune photo : on ne refuse donc pas
//    « vide » dans l'absolu, on refuse de marquer DES PHOTOS EXISTANTES depuis une liste
//    vide.
//
// 4. UNE ANNONCE SANS FICHE DETAIL EST SAUTEE. Pas de detail = aucune information, et
//    une absence d'information n'est pas une absence de photos.
//
// 5. UN PLAFOND. Au-dela de --plafond photos a marquer (2 000 par defaut), on REFUSE et
//    on sort en 1. La mesure du 15/10 est 440 : un nombre qui explose veut dire que le
//    miroir est casse, pas que l'agence a vide ses reportages.
//
// 6. UN PLANCHER. Si moins de --plancher annonces (5 000) ont une lecture fraiche, on
//    REFUSE : c'est la signature d'un run a moitie mort. (Patron du plancher de G.8,
//    26/09, qui a empeche d'horodater tout le parc depuis un app_dossier_current vide.)
//
// ═══════════════════════════════════════════════════════════════════════════════════
// ⚠ ON NE TOUCHE PAS AU DRAPEAU `visible`. Mesure du 15/10 : 0 divergence sur 441 238.
//   Moins de colonnes touchees, moins de surprises ; si un ecart apparait un jour, il se
//   verra dans le compte rendu (`visible_divergent`).
//
// ⭐ ET LE RESTE SE CORRIGE TOUT SEUL. notice/patch_photos_adresses_app_2026-09-27.sql
//   recalcule photo_url_listing_app et images_preview_json_app depuis present_in_hektor
//   et sort_order. Donc la vignette du listing, celle du registre des mandats et LA
//   GALERIE DU SITE PUBLIC redeviennent justes au passage suivant du run, sans toucher
//   une ligne de front.
//
// ⚠ APRES LA COUPURE, CE SCRIPT EST SANS OBJET : notre registre sera seul et souverain,
//   present_in_hektor gelera a sa derniere valeur, et on gardera ce qu'on avait. Il n'est
//   pas dangereux a ce moment-la (verrou 1), il est inutile.
//
//   node Console/accorder_photos_miroir.js                      <- compte, n'ecrit RIEN
//   node Console/accorder_photos_miroir.js --appliquer
//   options : --fraicheur-heures 48 · --plafond 2000 · --plancher 5000 · --limite N

const fs = require("fs");
const path = require("path");

require("dotenv").config({ path: path.resolve(__dirname, ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", ".env") });
require("dotenv").config({ path: path.resolve(__dirname, "..", "apps", "hektor-v1", ".env") });

const SUPABASE_URL = (process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "").replace(/\/+$/, "");
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const MIROIR = process.env.HEKTOR_SQLITE_PATH || path.resolve(__dirname, "..", "data", "hektor.sqlite");
const INDEX_LOCAL = process.env.PHASE2_SQLITE_PATH || path.resolve(__dirname, "..", "phase2", "phase2.sqlite");

const argv = process.argv.slice(2);
const opt = (nom, defaut) => { const i = argv.indexOf(nom); return i >= 0 ? Number(argv[i + 1]) || defaut : defaut; };
const APPLIQUER = argv.includes("--appliquer");
const FRAICHEUR_H = opt("--fraicheur-heures", 48);
const PLAFOND = opt("--plafond", 2000);
const PLANCHER = opt("--plancher", 5000);
const LIMITE = opt("--limite", 0);

// Les lignes `app` dont l'envoi n'est pas abouti : leur sort depend du worker, pas du
// miroir. On les laisse INTACTES, quel que soit leur etat d'envoi.
const ENVOI_NON_ABOUTI = new Set(["a_envoyer", "en_cours", "erreur", "echec"]);

function ouvrir(chemin) {
  let Database;
  try { Database = require("node:sqlite").DatabaseSync; }
  catch (_) { throw new Error("node:sqlite indisponible -- Node 22+ requis"); }
  if (!fs.existsSync(chemin)) throw new Error(`Base introuvable : ${chemin}`);
  return new Database(chemin, { readOnly: true });
}

async function rest(pathname, options = {}) {
  if (!SUPABASE_URL || !KEY) throw new Error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents");
  const reponse = await fetch(SUPABASE_URL + "/rest/v1/" + pathname.replace(/^\/+/, ""), {
    ...options,
    headers: {
      apikey: KEY, Authorization: "Bearer " + KEY, "Content-Type": "application/json",
      ...(options.prefer ? { Prefer: options.prefer } : {}),
    },
  });
  if (!reponse.ok) throw new Error("Supabase " + reponse.status + " " + (await reponse.text()).slice(0, 300));
  return options.prefer === "return=minimal" ? null : reponse.json();
}

// Une date SQLite ('2026-10-15T04:24:13Z' ou '2026-10-15 04:24:13') -> millisecondes.
function instant(texte) {
  const t = String(texte || "").trim();
  if (!t) return null;
  const iso = t.includes("T") ? t : t.replace(" ", "T");
  const ms = Date.parse(iso.endsWith("Z") || /[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z");
  return Number.isFinite(ms) ? ms : null;
}

function lireLeMiroir() {
  const db = ouvrir(MIROIR);
  const lignes = db.prepare(
    "select hektor_annonce_id, images_json, synced_at from hektor_annonce_detail"
  ).all();
  const parAnnonce = new Map();
  for (const l of lignes) {
    const aid = String(l.hektor_annonce_id);
    let arr = [];
    try { arr = JSON.parse(l.images_json || "[]"); } catch (_) { arr = []; }
    if (!Array.isArray(arr)) arr = arr ? [arr] : [];
    const photos = new Map();
    for (const e of arr) {
      if (!e || typeof e !== "object" || e.id == null) continue;
      const ordre = Number.parseInt(String(e.order ?? ""), 10);
      photos.set(String(e.id), {
        ordre: Number.isFinite(ordre) ? ordre : null,
        visible: String(e.visible ?? "1").trim(),
      });
    }
    parAnnonce.set(aid, { photos, luA: instant(l.synced_at) });
  }
  db.close();
  return parAnnonce;
}

// LA VERITE DU DRAPEAU -- UNE SEULE REGLE, TROIS ETATS (18/10/2026)
//
// ⚠ Elle existait DEJA, en ligne, pour la statistique `visible_divergent`. On la
//   sort ici pour que le VERROU 7 et la statistique lisent LA MEME chose : deux
//   copies divergeraient au premier ajustement.
//
// LES FORMES REELLEMENT PRODUITES par nos deux chemins d'ecriture :
//   booleen true/false -> rattrapage_photos.js  |  "1"/"0" -> le miroir Hektor
//   "true"/"false"     -> un aller-retour JSON
//
// ⚠⚠ ET L'INCONNU EST UN TROISIEME ETAT, PAS UNE MASQUEE. Un drapeau absent ou
//   vide ne doit PAS proteger la ligne : une photo dont on ignore l'etat et que
//   Hektor ne liste plus est, selon toute vraisemblance, vraiment supprimee. Le
//   verrou ne couvre QUE ce qu'on SAIT masque -- sinon il cesserait de marquer
//   des photos legitimement retirees, et notre registre divergerait en silence.
function drapeauVisible(r) {
  if (r.visible === true || String(r.visible) === "1" || String(r.visible).toLowerCase() === "true") return "visible";
  if (r.visible === false || String(r.visible) === "0" || String(r.visible).toLowerCase() === "false") return "masquee";
  return "inconnu";
}

function lireNotreIndex() {
  const db = ouvrir(INDEX_LOCAL);
  const lignes = db.prepare(
    `select id, hektor_annonce_id, hektor_photo_id, sort_order, visible, source,
            envoi_hektor_statut, created_at, present_in_hektor
       from app_console_photo`
  ).all();
  db.close();
  return lignes;
}

async function main() {
  const miroir = lireLeMiroir();
  const maintenant = Date.now();
  const seuilFraicheur = maintenant - FRAICHEUR_H * 3600 * 1000;

  // ── VERROU 6 : LE PLANCHER ────────────────────────────────────────────────────
  let fraiches = 0;
  for (const { luA } of miroir.values()) if (luA && luA >= seuilFraicheur) fraiches += 1;
  if (fraiches < PLANCHER) {
    console.log(JSON.stringify({
      refus: "pas_assez_de_lectures_fraiches",
      annonces_lues_depuis_h: FRAICHEUR_H, fraiches, plancher: PLANCHER,
      message: "le miroir n'a pas ete relu assez largement -- on ne conclut RIEN. "
             + "C'est aussi ce qui se passera le jour de la coupure : ce script s'eteint seul.",
    }, null, 2));
    process.exitCode = 1;
    return;
  }

  const lignes = lireNotreIndex();
  const stats = {
    lignes_lues: lignes.length, annonces_du_miroir: miroir.size, lectures_fraiches: fraiches,
    sautees_annonce_inconnue: 0, sautees_lecture_pas_fraiche: 0, sautees_liste_vide: 0,
    sautees_sans_numero_hektor: 0, sautees_photo_de_l_app: 0, sautees_plus_recente_que_le_miroir: 0,
    sautees_deja_marquees: 0, sautees_masquee: 0, a_marquer: 0, a_reordonner: 0, visible_divergent: 0,
    manquantes_chez_nous: 0,
  };
  const listesVides = [];
  const aMarquer = new Map();     // annonce -> [id de ligne]
  const candidatesNommees = [];   // "annonce/photo" -- pour les NOMMER au compte rendu
  const aReordonner = [];         // { id, ordre }

  for (const r of lignes) {
    const aid = String(r.hektor_annonce_id);
    const m = miroir.get(aid);
    if (!m) { stats.sautees_annonce_inconnue += 1; continue; }                 // verrou 4
    if (!m.luA || m.luA < seuilFraicheur) { stats.sautees_lecture_pas_fraiche += 1; continue; }  // verrou 1
    if (r.present_in_hektor === 0 || r.present_in_hektor === false) { stats.sautees_deja_marquees += 1; continue; }

    const pid = String(r.hektor_photo_id ?? "").trim();
    if (!pid) { stats.sautees_sans_numero_hektor += 1; continue; }             // verrou 2a
    const envoi = String(r.envoi_hektor_statut ?? "").trim();
    if (String(r.source ?? "") === "app" && (envoi === "" || ENVOI_NON_ABOUTI.has(envoi))) {
      stats.sautees_photo_de_l_app += 1; continue;                             // verrou 2
    }
    const nee = instant(r.created_at);
    if (nee && nee > m.luA) { stats.sautees_plus_recente_que_le_miroir += 1; continue; }  // verrou 2b

    const chezEux = m.photos.get(pid);
    if (!chezEux) {
      // VERROU 3 : liste vide -> on ne marque RIEN sur cette annonce, et on le dit.
      if (m.photos.size === 0) {
        stats.sautees_liste_vide += 1;
        if (!listesVides.includes(aid)) listesVides.push(aid);
        continue;
      }
      // ⚠⚠ VERROU 7 (18/10/2026) : UNE MASQUEE N'EST PAS UNE SUPPRIMEE.
      //   Le miroir vient de l'API detail de Hektor, QUI NE LISTE QUE LES
      //   VISIBLES. Une photo masquee n'y figure donc pas -- et elle ressemble
      //   trait pour trait a une supprimee : elle a un hektor_photo_id, elle est
      //   plus ancienne que la lecture du miroir, et ce n'est pas un envoi `app`
      //   en cours. Les trois verrous precedents ne la protegent pas.
      //
      //   CE QUE CA A COUTE, le 15/10 a 23:23 : sur 440 photos declarees
      //   disparues, 337 l'etaient vraiment (reportages remplaces -- verifie en
      //   direct le 18/10 : 13/13, 25/25, 25/25) mais 103 ETAIENT MASQUEES, et
      //   toujours chez Hektor (verifie sur 6 annonces, 75 photos).
      //
      // ⭐ ET C'EST LE PREALABLE AU BOUTON « MASQUER » (chantier (7)-8) : sans ce
      //   verrou, masquer une photo la ferait declarer disparue la nuit suivante,
      //   elle sortirait du panneau de l'app (loadConsolePhotos filtre
      //   present_in_hektor) et ON NE POURRAIT PLUS LA DEMASQUER. A sens unique.
      if (drapeauVisible(r) === "masquee") {
        stats.sautees_masquee += 1;
        continue;
      }
      if (!aMarquer.has(aid)) aMarquer.set(aid, []);
      aMarquer.get(aid).push(r.id);
      // ⭐ ON NOMME LES CANDIDATES (19/10/2026). Le compte rendu disait « a_marquer: 2 »
      //   sans dire LESQUELLES -- regle du projet : un controle qui AGREGE perd ce qui
      //   sert a agir. En essai a blanc, c'est la seule facon de savoir a l'avance ce
      //   que le passage de 21:00 va retirer, et donc de verifier que le verrou 8
      //   protegera bien ce qu'il doit proteger.
      candidatesNommees.push(`${aid}/${pid}`);
      stats.a_marquer += 1;
      continue;
    }
    const notre = Number.isFinite(Number(r.sort_order)) ? Number(r.sort_order) : null;
    if (chezEux.ordre != null && notre !== chezEux.ordre) {
      aReordonner.push({ id: r.id, ordre: chezEux.ordre });
      stats.a_reordonner += 1;
    }
    if ((chezEux.visible === "1") !== (drapeauVisible(r) === "visible")) stats.visible_divergent += 1;
  }

  // Information seulement : ce que Hektor a et que nous n'avons pas -> c'est le travail
  // de rattrapage_photos.js, pas celui-ci.
  const nos = new Set(lignes.map((r) => `${r.hektor_annonce_id}|${String(r.hektor_photo_id ?? "").trim()}`));
  for (const [aid, m] of miroir) for (const pid of m.photos.keys()) {
    if (!nos.has(`${aid}|${pid}`)) stats.manquantes_chez_nous += 1;
  }

  // ── VERROU 5 : LE PLAFOND ─────────────────────────────────────────────────────
  if (stats.a_marquer > PLAFOND) {
    console.log(JSON.stringify({
      refus: "trop_de_photos_a_marquer", a_marquer: stats.a_marquer, plafond: PLAFOND,
      message: "un nombre pareil veut dire que le miroir est casse, pas que l'agence a "
             + "vide ses reportages -- on ne touche a RIEN.",
    }, null, 2));
    process.exitCode = 1;
    return;
  }

  let marquees = 0;
  let reordonnees = 0;
  // ⚠⚠ VERROU 8 (19/10/2026) : combien de lignes la BASE a refuse de marquer parce
  //   qu'elles y sont masquees. Ce n'est pas un ecart, c'est le verrou qui joue --
  //   donc ca se COMPTE et ca se DIT, sinon le compte rendu final crierait a tort.
  let refuseesCarMasqueesEnBase = 0;
  const refuseesNommees = [];
  if (APPLIQUER) {
    const maintenantIso = new Date().toISOString();
    for (const [aid, ids] of aMarquer) {
      if (LIMITE && marquees >= LIMITE) break;
      const lot = LIMITE ? ids.slice(0, Math.max(0, LIMITE - marquees)) : ids;
      if (!lot.length) continue;
      // ⚠ LE GARDE-FOU EST AUSSI DANS LA REQUETE : `present_in_hektor=is.true`. Notre
      //   comparaison vient d'une COPIE locale ; si Supabase a deja marque la ligne
      //   entre-temps, on ne re-date pas sa sortie.
      // ⚠⚠ VERROU 8 (19/10/2026) : LE DRAPEAU `visible` SE LIT DANS LA BASE, PAS DANS
      //   LA COPIE. C'est la suite logique du garde-fou ci-dessus, et il a ete paye le
      //   19/10 au soir.
      //
      //   CE QUE CA A COUTE. Frederic a masque la photo 485375 de l'annonce 63073
      //   depuis l'app a 14:31. A 21:00:05 ce script l'a declaree DISPARUE. Elle est
      //   alors sortie du panneau (`loadConsolePhotos` filtre `present_in_hektor`) :
      //   invisible, donc IMPOSSIBLE A REAFFICHER. Exactement le « a sens unique »
      //   que le verrou 7 annonce dans son propre commentaire.
      //
      //   POURQUOI LE VERROU 7 N'A PAS JOUE. Il fait
      //   `if (drapeauVisible(r) === "masquee") continue;` -- mais `r` vient de
      //   `lireNotreIndex()`, c'est-a-dire de la COPIE LOCALE (INDEX_LOCAL), qui ne se
      //   rafraichit qu'a la DESCENTE DE 07:45. Mesure du 19/10 a 23:27 dans cette
      //   copie : la photo 485375 y etait encore `visible = 1`, et l'annonce 63073 n'y
      //   avait que 10 photos dont 0 masquee (la production : 24 dont 15).
      //   Le verrou a donc lu « visible » et n'a pas protege.
      //   ⭐ La fenetre est ouverte TOUS LES JOURS, de 07:45 (la copie) a 21:00 (ici).
      //
      //   AMPLEUR MESUREE LE 19/10 : 1 seule photo touchee. Le verrou 7 a bien protege
      //   les 121 autres masquees -- leur masquage est anterieur a la derniere copie,
      //   donc la copie les connait. Le defaut ne frappe QUE le masquage du jour,
      //   c'est-a-dire exactement le bouton de ⑦-8 marche 4, livre la veille. Il est
      //   passe inapercu parce que personne ne s'en etait encore servi en reel.
      //
      // ⭐ LE REMEDE EST UNE CONDITION, PAS UN APPEL : `visible=is.true`. C'est la BASE
      //   qui refuse, donc aucune lecture de plus, aucune requete chez Hektor, et le
      //   reste du script est intact. Une photo masquee en production ne peut plus etre
      //   declaree disparue, quoi que dise la copie.
      const cible = `app_console_photo?id=in.(${lot.map((i) => encodeURIComponent(i)).join(",")})`
                  + `&present_in_hektor=is.true`
                  + `&visible=is.true`;
      const ecrites = await rest(cible, {
        method: "PATCH", prefer: "return=representation",
        body: JSON.stringify({ present_in_hektor: false, absent_depuis: maintenantIso, updated_at: maintenantIso }),
      });
      const n = Array.isArray(ecrites) ? ecrites.length : 0;
      marquees += n;

      // ⭐ ET SI LA BASE A REFUSE DES LIGNES, ON DIT LESQUELLES ET POURQUOI.
      //   Regle du projet : un controle qui AGREGE perd ce qui sert a agir -- un
      //   « 1 sur 2 » ne dit pas quelle photo a ete sauvee. Une seule lecture, et
      //   seulement quand il y a un refus (donc jamais les soirs ordinaires).
      if (n < lot.length) {
        const ecritsIds = new Set((Array.isArray(ecrites) ? ecrites : []).map((l) => String(l.id)));
        const refuses = lot.filter((i) => !ecritsIds.has(String(i)));
        try {
          const detail = await rest(
            `app_console_photo?id=in.(${refuses.map((i) => encodeURIComponent(i)).join(",")})`
            + `&select=id,hektor_annonce_id,hektor_photo_id,visible,present_in_hektor`
          );
          for (const l of Array.isArray(detail) ? detail : []) {
            if (l.visible === false) {
              refuseesCarMasqueesEnBase += 1;
              refuseesNommees.push(`${l.hektor_annonce_id}/${l.hektor_photo_id}`);
              console.error(JSON.stringify({
                etape: "verrou_8",
                verdict: "SAUVEE -- masquee en base, la copie locale disait visible",
                annonce: l.hektor_annonce_id, photo: l.hektor_photo_id,
              }));
            } else {
              console.error(JSON.stringify({
                etape: "marquage_refuse",
                verdict: "deja marquee entre-temps (normal)",
                annonce: l.hektor_annonce_id, photo: l.hektor_photo_id,
                visible: l.visible, present_in_hektor: l.present_in_hektor,
              }));
            }
          }
        } catch (erreur) {
          // ⚠ On ne fait pas tomber l'entretien pour un compte rendu : le marquage,
          //   lui, a bien eu lieu (ou a bien ete refuse). Mais on le DIT.
          console.error(JSON.stringify({
            etape: "verrou_8",
            avertissement: "refus non detailles -- la relecture a echoue",
            annonce: aid, refuses: refuses.length,
            erreur: erreur && erreur.message ? erreur.message : String(erreur),
          }));
        }
      }
      console.error(JSON.stringify({ etape: "marquage", annonce: aid, demandees: lot.length, ecrites: n }));
    }
    for (const { id, ordre } of aReordonner) {
      if (LIMITE && reordonnees >= LIMITE) break;
      const ecrites = await rest(`app_console_photo?id=eq.${encodeURIComponent(id)}&present_in_hektor=is.true`, {
        method: "PATCH", prefer: "return=representation",
        body: JSON.stringify({ sort_order: ordre, updated_at: maintenantIso }),
      });
      reordonnees += Array.isArray(ecrites) ? ecrites.length : 0;
      if (reordonnees % 200 === 0) console.error(JSON.stringify({ etape: "ordre", faites: reordonnees }));
    }
  }

  console.log(JSON.stringify({
    mode: APPLIQUER ? "applique" : "dry-run",
    fraicheur_heures: FRAICHEUR_H, plafond: PLAFOND, plancher: PLANCHER,
    ...stats,
    annonces_a_marquer: aMarquer.size,
    annonces_a_liste_vide: listesVides.length,
    exemples_liste_vide: listesVides.slice(0, 5),
    photos_marquees: marquees, photos_reordonnees: reordonnees,
    // ⭐ VERROU 8 : ce que la base a refuse de marquer parce que c'etait masque chez
    //   elle. Un zero est la normale ; un nombre non nul veut dire « le verrou a
    //   servi ce soir », et les photos sont NOMMEES pour qu'on puisse aller voir.
    sauvees_par_le_verrou_8: refuseesCarMasqueesEnBase,
    sauvees_nommees: refuseesNommees.slice(0, 20),
    // ⭐ LES CANDIDATES, NOMMEES : en essai a blanc c'est la seule facon de savoir
    //   A L'AVANCE ce que le passage de 21:00 va retirer.
    candidates_nommees: candidatesNommees.slice(0, 20),
  }, null, 2));

  // Un compte rendu qui ne colle pas doit se VOIR, pas se deviner.
  // ⚠ VERROU 8 : UNE PHOTO SAUVEE N'EST PAS UN ECART. Sans cette addition, le
  //   premier masquage fait dans la journee ferait sortir l'entretien en code 1
  //   chaque soir -- une fausse alerte repetee, et la surveillance finirait par
  //   etre ignoree. Les sauvees sont donc COMPTEES comme traitees ici, et DITES
  //   dans le compte rendu ci-dessus.
  if (APPLIQUER
      && ((marquees + refuseesCarMasqueesEnBase) !== stats.a_marquer
          || reordonnees !== stats.a_reordonner)
      && !LIMITE) {
    console.error(`ECART : ${stats.a_marquer} a marquer / ${marquees} ecrites `
      + `(+ ${refuseesCarMasqueesEnBase} sauvees par le verrou 8), `
      + `${stats.a_reordonner} a reordonner / ${reordonnees} ecrites. `
      + `Une ligne a pu etre marquee entre-temps par le worker (c'est normal) -- a verifier.`);
    process.exitCode = 1;
  }
}

main().catch((error) => { console.error(error.message); process.exit(1); });
