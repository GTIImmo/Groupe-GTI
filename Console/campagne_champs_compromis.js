/**
 * CAMPAGNE DES CHAMPS — tâche 0.1, ce qui ne se mesure qu'en écrivant
 * ═══════════════════════════════════════════════════════════════════════════════
 * 08/09/2026.
 *
 * ⚠⚠ CE SCRIPT ÉCRIT CHEZ HEKTOR. C'est le seul du dossier `Console/` qui le
 *    fasse délibérément, et c'est écrit ici pour qu'on ne l'oublie jamais.
 *
 * POURQUOI IL EXISTE. Le tableau « champ Hektor / modale / registre / classe »
 * est incomplet : 14 champs classés sur 27. La distinction B/C ne se lit pas —
 * elle demande de répondre à « si je lui envoie X, le garde-t-il ou le
 * remplace-t-il ? ». C'est la méthode du 03/09, appliquée d'un coup au lieu d'un
 * champ à la fois.
 *
 * LES TROIS GARDE-FOUS, dans cet ordre :
 *   ① L'ANNONCE ET LE COMPROMIS SONT EN DUR. Le script refuse de démarrer sur
 *     autre chose. Pas de paramètre, pas d'option, pas de « juste cette fois ».
 *   ② L'ÉTAT D'AVANT EST CAPTURÉ ET DÉPOSÉ avant la moindre écriture, dans le
 *     format que ce même script relit. Revenir en arrière, c'est le relancer
 *     avec `--valeurs <le fichier déposé>`.
 *   ③ RETOUR ARRIÈRE ULTIME : le geste « supprimer le compromis » existe dans
 *     l'app et il est éprouvé (tâche 3.4, essai réel du 07/09).
 *
 * CE QU'IL NE TESTE PAS, ET POURQUOI :
 *   `agenceReseauSelected` (la rétrocession, 20 agences en radio) — AUCUNE n'est
 *   cochée aujourd'hui. En cocher une n'est pas trivialement réversible : un
 *   bouton radio ne se décoche pas en le repostant vide. Ça demande un arbitrage,
 *   pas une campagne. Laissé de côté DÉLIBÉRÉMENT.
 *
 *   node Console/campagne_champs_compromis.js [--valeurs fichier.json]
 *
 * ═══════════════════════════════════════════════════════════════════════════════
 * ✅ DEUX DÉFAUTS, CONSTATÉS AU PREMIER VRAI PASSAGE (08/09) ET CORRIGÉS LE MÊME
 *    JOUR. Gardés écrits : ils disent comment relire les rapports déjà produits.
 *
 *  ① SA SORTIE MENTAIT SUR LES ÉTAPES 2 ET 3. Le tableau final relisait les
 *    champs dans le formulaire d'OUVERTURE, où `unitesEntreePercent`,
 *    `unitesSortiePercent`, `notesCompromis` et les conditions suspensives
 *    N'EXISTENT PAS — ils appartiennent aux étapes suivantes. Il en concluait
 *    « IGNORE ou vide », ce qui était FAUX (vérifié : 60/40 et la note étaient
 *    bien enregistrés).
 *    ✅ CORRIGÉ : le script fait maintenant TROIS parcours — lecture avant,
 *      écriture, lecture après — et compare CHAQUE CHAMP À SON ÉTAGE.
 *    ⚠ Les rapports produits AVANT ce correctif gardent leurs lignes fausses :
 *      n'en retenir que prixDeVente, sequestre, montantHonoraireEntree, mandants[].
 *
 *  ② IL REPOSAIT UN NET VENDEUR PÉRIMÉ. Comme le worker avant son correctif du
 *    matin même, il recopiait `prixNetVendeur` tel que le formulaire le rend — or
 *    Hektor le recalcule à l'AFFICHAGE, depuis les valeurs d'AVANT notre
 *    écriture. Mesure : le retour arrière du 08/09 a laissé 162 655
 *    (= 175 000 − 12 345, les honoraires d'essai) au lieu de 165 000.
 *    ➡ Le décalage d'une modification, reproduit par mon propre outil : la
 *      troisième confirmation indépendante du diagnostic.
 *    ✅ CORRIGÉ : même règle que le worker — quand le prix de vente est posé et
 *      que le net ne l'est pas, on écrit `net = prix de vente − honoraires
 *      d'entrée`, avec les honoraires TELS QU'ILS SERONT après ce passage.
 * ═══════════════════════════════════════════════════════════════════════════════
 */
const fs = require("fs");
const path = require("path");

// ─── ① LE GARDE-FOU, EN DUR ───
const ANNONCE = "24933";        // dossier d'essai : mandants « TEST », mandat échu en 2020
const COMPROMIS = "50078";      // le compromis d'essai, quatre fois modifié le 08/09

const BASE = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${BASE.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const COQUILLE = "annonce-SuiviVente-compromis-createCompromis";
const ETAPE = "annonce-SuiviVente-compromis-getStepCompromis";
const CONTENEUR = "PopinCompromis";
const SESSION = path.resolve(__dirname, "sessions", "storage_state_admin.json");
const SORTIE = path.resolve(__dirname, "exports", "campagne_champs");

const PAS = [
  { de: "0", vers: "2", modules: ["infosFinancieresCompromis",
      "acquereurNotaireAutresProspectsCompromis", "annonceMandatCompromis",
      "agenceInterkabCompromis"] },
  { de: "2", vers: "3", modules: ["commissionsCompromis"] },
  { de: "3", vers: "3", modules: ["conditionsSuspensives"], enregistre: true },
];

// ─── LES VALEURS D'ESSAI, choisies pour être RECONNAISSABLES et PLAUSIBLES ───
//
// `prixDeVente` est le test le plus fin : on l'envoie DIFFÉRENT du prix public
// alors que les honoraires acquéreur valent 0. Si Hektor le garde -> B. S'il le
// ramène au prix public -> C. Le relevé du 03/09 penchait pour C sans trancher.
const VALEURS_DEFAUT = {
  etape0: {
    prixDeVente: "170000",
    sequestre: "4321",
    montantHonoraireEntree: "12345",
    // ⚠ ON EN RETIRE UN DES TROIS (605030). S'il revient, Hektor les recalcule
    //   depuis le mandat (C) ; s'il disparaît, l'app peut les piloter (B).
    "mandants[]": ["141053", "485955"],
  },
  etape2: { unitesEntreePercent: "60", unitesSortiePercent: "40" },
  etape3: {
    // Catalogue relevé dans le formulaire : 1 = Préemption mairie, 2 = Obtention
    // Crédit, 9 = Autre. Les tableaux sont PARALLÈLES : même longueur, même ordre.
    // ⚠ LA CLEF DOIT ETRE LE LIBELLE EXACT DU CATALOGUE, ACCENT COMPRIS.
    //   Le 08/09 j'avais ecrit « Obtention Credit » sans accent : deux fautes
    //   d'un coup, la forme du tableau ET la clef.
    conditions: [{ id_condition: "2", clef: "Obtention Crédit",
                   jours_validites: "45", note: "ESSAI 0.1 du 08/09", etat: "1" }],
    notesCompromis: "ESSAI 0.1 du 08/09 -- classement des champs A/B/C",
  },
};

const argVal = process.argv.indexOf("--valeurs");
const VALEURS = argVal > 0 && process.argv[argVal + 1]
  ? JSON.parse(fs.readFileSync(process.argv[argVal + 1], "utf8"))
  : VALEURS_DEFAUT;

const etatSession = JSON.parse(fs.readFileSync(SESSION, "utf8"));
const maintenant = Date.now() / 1000;
const COOKIES = (etatSession.cookies || [])
  .filter((c) => !c.expires || c.expires < 0 || c.expires > maintenant)
  .map((c) => `${c.name}=${c.value}`).join("; ");
const ENTETES = {
  Cookie: COOKIES,
  Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${ANNONCE}`,
  Accept: "application/json, text/javascript, */*; q=0.01",
  "User-Agent": "Mozilla/5.0",
};

const attr = (b, n) => {
  const m = String(b).match(new RegExp(`\\b${n}\\s*=\\s*["']([^"']*)["']`, "i"));
  return m ? m[1] : "";
};

function champsDuFormulaire(html) {
  const v = new URLSearchParams();
  const re = /<textarea\b[^>]*>[\s\S]*?<\/textarea>|<select\b[^>]*>[\s\S]*?<\/select>|<input\b[^>]*>/gi;
  let m;
  while ((m = re.exec(String(html || "")))) {
    const c = m[0]; const nom = attr(c, "name");
    if (!nom) continue;
    const bas = c.toLowerCase();
    if (bas.startsWith("<input")) {
      const t = (attr(c, "type") || "text").toLowerCase();
      if (["button", "submit", "file", "image", "reset"].includes(t)) continue;
      if ((t === "radio" || t === "checkbox") && !/\bchecked\b/i.test(c)) continue;
      v.append(nom, attr(c, "value") || ""); continue;
    }
    if (bas.startsWith("<textarea")) {
      const b = (c.match(/<textarea\b[^>]*>([\s\S]*?)<\/textarea>/i) || [])[1] || "";
      v.append(nom, b.replace(/&amp;/g, "&").trim()); continue;
    }
    const opts = Array.from(c.matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((o) => o[0]);
    const sel = opts.find((o) => /\bselected\b/i.test(o)) || opts[0];
    if (sel) v.append(nom, attr(sel, "value") || "");
  }
  return v;
}

const valeurDe = (html, nom) => {
  for (const m of String(html || "").matchAll(/<input\b[^>]*>/gi)) {
    if (attr(m[0], "name") === nom) return attr(m[0], "value");
  }
  return null;
};
const toutesLesValeurs = (html, nom) => {
  const out = [];
  for (const m of String(html || "").matchAll(/<input\b[^>]*>/gi)) {
    if (attr(m[0], "name") === nom) out.push(attr(m[0], "value"));
  }
  return out;
};

function lireEtape(texte) {
  let j = null; try { j = JSON.parse(texte); } catch (_) {}
  const d = (j && j.data) || {};
  return { basket: typeof d.basket === "string" ? d.basket : "",
           contenu: typeof d.stepContent === "string" ? d.stepContent : "",
           index: d.currentStepIndex == null ? null : String(d.currentStepIndex),
           brut: texte };
}

/** Un parcours complet. `valeurs` = null -> LECTURE SEULE (aucun save/treat).
 *  Rend le contenu de CHAQUE etage, pour comparer chaque champ la ou il VIT.
 *  ✅ C'est le correctif ① : comparer dans le formulaire d'ouverture des champs
 *    qui appartiennent aux etapes suivantes ne prouve RIEN. */
async function parcourir(valeurs) {
  const ecrit = valeurs !== null;
  let etat = await ouvrir();
  if (!etat.basket) throw new Error("ouverture sans panier");
  const vues = { ouverture: etat.contenu };

  for (const pas of PAS) {
    const corps = new URLSearchParams();
    for (const [k, v] of champsDuFormulaire(etat.contenu).entries()) {
      if (k === "basket" || k === "idAnnonce") continue;
      corps.append(k, v);
    }
    if (ecrit) injecter(corps, pas, valeurs, etat.contenu);
    for (const m of pas.modules) corps.append("containerModule[]", m);
    corps.set("containerName", CONTENEUR);
    corps.set("fromStep", pas.de); corps.set("step", pas.vers);
    corps.set("idAnnonce", ANNONCE); corps.set("basket", etat.basket);

    // ⚠ C'EST CE SUFFIXE, ET LUI SEUL, QUI ECRIT CHEZ HEKTOR. En lecture il
    //   n'est jamais construit : un parcours de lecture ne peut pas deraper.
    const url = `${XMLRPC_URL}?mode=${encodeURIComponent(ETAPE)}`
      + (ecrit && pas.enregistre ? "&actionContainer%5B%5D=save&actionContainer%5B%5D=treat" : "");
    const r = await fetch(url, { method: "POST", body: corps,
      headers: { ...ENTETES, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" } });
    etat = lireEtape(await r.text());
    vues[`${pas.de}->${pas.vers}`] = etat.contenu;
    if (ecrit) console.log(`   etape ${pas.de} -> ${pas.vers}`
      + `${pas.enregistre ? "  [ENREGISTREMENT]" : ""}  index=${etat.index} · ${etat.contenu.length} car`);
    await new Promise((x) => setTimeout(x, 1200));
  }
  return vues;
}

/** Pose les valeurs d'essai a l'etage qui les porte. */
function injecter(corps, pas, valeurs, contenu) {
  const poser = (cle, val) => { corps.delete(cle); corps.set(cle, String(val)); };
  if (pas.de === "0") {
    const v = valeurs.etape0 || {};
    for (const [cle, val] of Object.entries(v)) {
      if (Array.isArray(val)) { corps.delete(cle); for (const x of val) corps.append(cle, x); }
      else poser(cle, val);
    }
    // ✅ CORRECTIF ② : LE NET VENDEUR SUIT LE PRIX.
    // Hektor le recalcule a l'AFFICHAGE depuis ce qu'il a en base ; le reposter
    // tel quel, c'est ecrire la valeur d'AVANT notre modification. Meme regle que
    // le worker : net = prix de vente - honoraires d'entree, avec les honoraires
    // TELS QU'ILS SERONT apres ce passage.
    if (v.prixDeVente != null && v.prixNetVendeur == null) {
      const honos = v.montantHonoraireEntree != null
        ? String(v.montantHonoraireEntree)
        : String(valeurDe(contenu, "montantHonoraireEntree") || "");
      const net = Number(v.prixDeVente) - Number(honos || "0");
      if (honos !== "" && Number.isFinite(net) && net > 0) {
        poser("prixNetVendeur", String(net));
        console.log(`   net vendeur recalcule : ${v.prixDeVente} - ${honos} = ${net}`);
      }
    }
  } else if (pas.de === "2") {
    for (const [cle, val] of Object.entries(valeurs.etape2 || {})) poser(cle, val);
  } else {
    const v = valeurs.etape3 || {};
    const conds = Array.isArray(v.conditions) ? v.conditions : [];

    // ═══ LA CLEF DU TABLEAU EST LE NOM DE LA CONDITION ═══
    //
    // MESURE DU 08/09, faite EN OUVRANT LEUR PROPRE INTERFACE et en cliquant le
    // « + » d'une condition, puis en fermant SANS ENREGISTRER. Ce que leur
    // JavaScript fabrique n'est pas ce que le gabarit laisse croire :
    //
    //     AVANT le clic   (rien -- aucun champ nomme)
    //     APRES le clic
    //         conditionsSuspensivesSelected[Obtention Credit][id_condition]  = 2
    //         conditionsSuspensivesSelected[Obtention Credit][clef]          = Obtention Credit
    //         conditionsSuspensivesSelected[Obtention Credit][jours_validites] = 60
    //         conditionsSuspensivesSelected[Obtention Credit][note]          = ""
    //         conditionsSuspensivesSelected[Obtention Credit][etat]          = case a cocher
    //
    // ➡ VOILA POURQUOI LA CAMPAGNE DU 08/09 N'A RIEN CREE. J'avais poste des
    //   tableaux paralleles `[]`, que PHP indexe 0, 1, 2... alors que Hektor
    //   indexe PAR LE LIBELLE. Les `[]` visibles dans le formulaire sont le
    //   GABARIT que leur JavaScript clone et renomme -- pas le format d'envoi.
    //
    // ⚠ `etat` EST UNE CASE A COCHER, decochee par defaut : un navigateur ne
    //   poste PAS une case decochee. On ne l'envoie donc que si elle vaut 1,
    //   sinon on ecrirait un etat que l'utilisateur n'a pas donne.
    //
    // ⚠⚠ QUESTION NON TRANCHEE -- L'ENCODAGE. Leur page est en ISO-8859-1 (le
    //   relevé lu en UTF-8 rend « Pr�emption », « Cr�dit »), donc leur
    //   navigateur poste la clef en latin-1. URLSearchParams, lui, encode
    //   TOUJOURS en UTF-8. Pour une clef accentuee -- « Obtention Credit » en
    //   porte une -- les deux ne coincident pas.
    //   >>> SI LA CONDITION N'EST TOUJOURS PAS CREEE AU PROCHAIN ESSAI, CHERCHER
    //       LA D'ABORD, et pas ailleurs.
    for (const k of Array.from(corps.keys())) {
      if (k.startsWith("conditionsSuspensivesSelected[")) corps.delete(k);
    }
    for (const c of conds) {
      const clef = String(c.clef ?? "");
      for (const champ of ["id_condition", "clef", "jours_validites", "note"]) {
        corps.set(`conditionsSuspensivesSelected[${clef}][${champ}]`, String(c[champ] ?? ""));
      }
      if (String(c.etat ?? "") === "1") {
        corps.set(`conditionsSuspensivesSelected[${clef}][etat]`, "1");
      }
    }
    if (v.notesCompromis != null) poser("notesCompromis", v.notesCompromis);
  }
}

async function ouvrir() {
  await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(COQUILLE)}`, { headers: ENTETES });
  const c = new URLSearchParams();
  c.set("idAnnonce", ANNONCE); c.set("idCompromis", COMPROMIS);
  c.set("basket", ""); c.set("initBasket", "true");
  const r = await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(ETAPE)}`, {
    method: "POST", body: c,
    headers: { ...ENTETES, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" } });
  return lireEtape(await r.text());
}


/** Les conditions suspensives REELLEMENT retenues : on lit toute clef nommee
 *  `conditionsSuspensivesSelected[<libelle>][id_condition]`. Le gabarit, lui,
 *  porte `[]` vide -- il ne compte pas. */
const conditionsRetenues = (html) => {
  const out = [];
  for (const m of String(html || "").matchAll(/<input\b[^>]*>/gi)) {
    const nom = attr(m[0], "name");
    const g = nom && nom.match(/^conditionsSuspensivesSelected\[(.+)\]\[id_condition\]$/);
    if (g && g[1] !== "" && attr(m[0], "value")) out.push(`${g[1]}=${attr(m[0], "value")}`);
  }
  return out;
};

/** Le contenu d'un <textarea> (notesCompromis en est un). */
const texteDe = (html, nom) => {
  for (const m of String(html || "").matchAll(/<textarea\b[^>]*>[\s\S]*?<\/textarea>/gi)) {
    if (attr(m[0], "name") === nom) {
      return (m[0].match(/<textarea\b[^>]*>([\s\S]*?)<\/textarea>/i) || [])[1].trim();
    }
  }
  return null;
};

(async () => {
  fs.mkdirSync(SORTIE, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  console.log(`CAMPAGNE DES CHAMPS -- annonce ${ANNONCE} · compromis ${COMPROMIS}`);
  console.log("⚠ CE SCRIPT ECRIT CHEZ HEKTOR.");
  console.log("");

  // ─── ① UN PARCOURS DE LECTURE D'ABORD, POUR VOIR CHAQUE ETAGE ───
  // C'est le correctif du defaut n°1 : on capture les etapes 2 et 3 LA OU ELLES
  // VIVENT, au lieu de les chercher dans le formulaire d'ouverture.
  console.log("--- lecture AVANT (aucune ecriture) ---");
  const vAvant = await parcourir(null);

  // L'etat d'avant, au format que ce script relit pour le retour arriere.
  const avant = {
    etape0: {
      prixDeVente: valeurDe(vAvant.ouverture, "prixDeVente"),
      sequestre: valeurDe(vAvant.ouverture, "sequestre"),
      montantHonoraireEntree: valeurDe(vAvant.ouverture, "montantHonoraireEntree"),
      "mandants[]": toutesLesValeurs(vAvant.ouverture, "mandants[]"),
    },
    etape2: {
      unitesEntreePercent: valeurDe(vAvant["0->2"], "unitesEntreePercent"),
      unitesSortiePercent: valeurDe(vAvant["0->2"], "unitesSortiePercent"),
    },
    etape3: { conditions: [], notesCompromis: texteDe(vAvant["2->3"], "notesCompromis") || "" },
    _releve: {
      prixPublique: valeurDe(vAvant.ouverture, "prixPublique"),
      prixNetVendeur: valeurDe(vAvant.ouverture, "prixNetVendeur"),
      tauxHonoraireEntree: valeurDe(vAvant.ouverture, "tauxHonoraireEntree"),
      acquereurs: toutesLesValeurs(vAvant.ouverture, "acquereurs[]"),
      conditions_brut: toutesLesValeurs(vAvant["3->3"], "conditionsSuspensivesSelected[][id_condition]"),
    },
  };
  const fichierAvant = path.join(SORTIE, `avant_${stamp}.json`);
  fs.writeFileSync(fichierAvant, JSON.stringify(avant, null, 1), "utf8");
  console.log(`⚠ ETAT D'AVANT DEPOSE (retour arriere) : ${fichierAvant}`);
  console.log("");

  // ─── L'ECRITURE ───
  console.log("--- ECRITURE ---");
  await parcourir(VALEURS);
  console.log("");
  await new Promise((x) => setTimeout(x, 3000));

  // ─── ET UN PARCOURS DE LECTURE APRES ───
  console.log("--- lecture APRES (aucune ecriture) ---");
  const vApres = await parcourir(null);
  console.log("");

  // ─── LA COMPARAISON, CHAQUE CHAMP A SON ETAGE ───
  const lignesRapport = [];
  const juger = (nom, envoye, retenu) => {
    let verdict;
    if (envoye == null) verdict = "-";
    else if (retenu == null) verdict = "CHAMP ABSENT de cette vue";
    else if (retenu === "" ) verdict = "IGNORE (revenu vide)";
    else {
      const na = Number(envoye); const nr = Number(retenu);
      const pareil = (Number.isFinite(na) && Number.isFinite(nr)) ? na === nr : String(envoye) === String(retenu);
      verdict = pareil ? "GARDE  -> B" : `REMPLACE par ${retenu}  -> C`;
    }
    lignesRapport.push({ nom, envoye, retenu, verdict });
  };

  const v0 = VALEURS.etape0 || {}; const v2 = VALEURS.etape2 || {}; const v3 = VALEURS.etape3 || {};
  for (const cle of ["prixDeVente", "sequestre", "montantHonoraireEntree"]) {
    if (v0[cle] != null) juger(cle, v0[cle], valeurDe(vApres.ouverture, cle));
  }
  if (v0["mandants[]"]) {
    const ap = toutesLesValeurs(vApres.ouverture, "mandants[]");
    lignesRapport.push({ nom: "mandants[]", envoye: v0["mandants[]"].join(","), retenu: ap.join(","),
      verdict: ap.length === v0["mandants[]"].length ? "GARDE  -> B (l'app peut les piloter)"
        : `REMPLACE (${ap.length} au lieu de ${v0["mandants[]"].length})  -> C` });
  }
  // ✅ A LEUR ETAGE, pas dans l'ouverture.
  for (const cle of ["unitesEntreePercent", "unitesSortiePercent"]) {
    if (v2[cle] != null) juger(cle, v2[cle], valeurDe(vApres["0->2"], cle));
  }
  if (v3.notesCompromis != null) juger("notesCompromis", v3.notesCompromis, texteDe(vApres["2->3"], "notesCompromis"));
  if (Array.isArray(v3.conditions) && v3.conditions.length) {
    // On cherche N'IMPORTE QUELLE clef -- c'est le libelle, pas un index.
    const ids = conditionsRetenues(vApres["3->3"]);
    lignesRapport.push({ nom: "conditions suspensives", envoye: v3.conditions.map((c) => c.id_condition).join(","),
      retenu: ids.join(",") || "(aucune)",
      verdict: ids.length ? "CREEE -> B" : "NON CREEE -- mecanisme non compris" });
  }

  console.log("=== ENVOYE CONTRE RETENU (chaque champ lu a son etage) ===");
  for (const l of lignesRapport) {
    console.log("   " + String(l.nom).padEnd(24) + " envoye=" + String(l.envoye).padEnd(14)
      + " retenu=" + String(l.retenu).padEnd(16) + " " + l.verdict);
  }
  console.log("");
  console.log("--- ce que le formulaire rend aussi (information) ---");
  for (const n of ["prixPublique", "prixNetVendeur", "tauxHonoraireEntree", "montantHonoraireSortie"]) {
    console.log("   " + n.padEnd(24) + " avant=" + String(valeurDe(vAvant.ouverture, n)).padEnd(12)
      + " apres=" + String(valeurDe(vApres.ouverture, n)));
  }

  const rapport = path.join(SORTIE, `campagne_${stamp}.json`);
  fs.writeFileSync(rapport, JSON.stringify({ avant, envoye: VALEURS, lignes: lignesRapport }, null, 1), "utf8");
  for (const [nom, html] of Object.entries(vApres)) {
    fs.writeFileSync(path.join(SORTIE, `apres_${nom.replace(/[^\w]+/g, "_")}_${stamp}.html`), html, "utf8");
  }
  console.log("");
  console.log("rapport : " + rapport);
  console.log("RETOUR ARRIERE : node Console/campagne_champs_compromis.js --valeurs " + fichierAvant);
})().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
