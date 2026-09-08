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
 * ⚠⚠ DEUX DÉFAUTS CONNUS — constatés au premier vrai passage, le 08/09/2026.
 *    À CORRIGER AVANT DE S'EN SERVIR POUR LA VENTE.
 *
 *  ① SA SORTIE MENT SUR LES ÉTAPES 2 ET 3. Le tableau final relit les champs
 *    dans le formulaire d'OUVERTURE, où `unitesEntreePercent`,
 *    `unitesSortiePercent`, `notesCompromis` et les conditions suspensives
 *    N'EXISTENT PAS — ils appartiennent aux étapes suivantes. Il en conclut
 *    « IGNORE ou vide », ce qui est FAUX.
 *    ➡ Ces lignes-là ne prouvent rien. Pour les lire, passer par
 *      `releve_assistant_etapes.js`, qui parcourt toutes les étapes et
 *      N'ÉCRIT JAMAIS. Vérifié le 08/09 : 60/40 et la note étaient bien
 *      enregistrés, contrairement à ce que ce script affichait.
 *
 *  ② IL REPOSE UN NET VENDEUR PÉRIMÉ. Comme le worker avant son correctif du
 *    matin même, il recopie `prixNetVendeur` tel que le formulaire le rend — or
 *    Hektor le recalcule à l'AFFICHAGE, depuis les valeurs d'AVANT notre
 *    écriture. Mesure : le retour arrière du 08/09 a laissé 162 655
 *    (= 175 000 − 12 345, les honoraires d'essai) au lieu de 165 000.
 *    ➡ Le décalage d'une modification, reproduit ici par mon propre outil : la
 *      troisième confirmation indépendante du diagnostic. Réparé en passant par
 *      le worker, qui porte le correctif — pas par ce script.
 *    ➡ Correctif à porter ici : quand le prix change, poser
 *      `prixNetVendeur = prix de vente − montantHonoraireEntree`.
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
    conditions: [{ id_condition: "2", clef: "Obtention Credit",
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

(async () => {
  fs.mkdirSync(SORTIE, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  console.log(`CAMPAGNE DES CHAMPS -- annonce ${ANNONCE} · compromis ${COMPROMIS}`);
  console.log("⚠ CE SCRIPT ECRIT CHEZ HEKTOR.");
  console.log("");

  // ─── ② L'ETAT D'AVANT, AVANT LA MOINDRE ECRITURE ───
  let etat = await ouvrir();
  if (!etat.basket) { console.error("ouverture sans panier -- on s'arrete"); process.exit(1); }
  const avantHtml = etat.contenu;
  const avant = {
    etape0: {
      prixDeVente: valeurDe(avantHtml, "prixDeVente"),
      sequestre: valeurDe(avantHtml, "sequestre"),
      montantHonoraireEntree: valeurDe(avantHtml, "montantHonoraireEntree"),
      "mandants[]": toutesLesValeurs(avantHtml, "mandants[]"),
    },
    etape2: {}, etape3: {},
    _releve: {
      prixPublique: valeurDe(avantHtml, "prixPublique"),
      prixNetVendeur: valeurDe(avantHtml, "prixNetVendeur"),
      tauxHonoraireEntree: valeurDe(avantHtml, "tauxHonoraireEntree"),
      acquereurs: toutesLesValeurs(avantHtml, "acquereurs[]"),
    },
  };
  const fichierAvant = path.join(SORTIE, `avant_${stamp}.json`);

  // ─── LE PARCOURS, avec injection au bon etage ───
  const journal = [];
  for (const pas of PAS) {
    const corps = new URLSearchParams();
    for (const [k, v] of champsDuFormulaire(etat.contenu).entries()) {
      if (k === "basket" || k === "idAnnonce") continue;
      corps.append(k, v);
    }
    const poser = (cle, val) => { corps.delete(cle); corps.set(cle, String(val)); };

    if (pas.de === "0") {
      const v = VALEURS.etape0 || {};
      for (const [cle, val] of Object.entries(v)) {
        if (Array.isArray(val)) { corps.delete(cle); for (const x of val) corps.append(cle, x); }
        else poser(cle, val);
      }
      journal.push({ etape: "0", envoye: v });
    } else if (pas.de === "2") {
      const v = VALEURS.etape2 || {};
      for (const [cle, val] of Object.entries(v)) poser(cle, val);
      // Ce que l'etape 2 rendait AVANT qu'on ecrive -- capture ici, c'est le seul
      // moment ou on la voit sans avoir encore enregistre.
      avant.etape2 = { unitesEntreePercent: valeurDe(etat.contenu, "unitesEntreePercent"),
                       unitesSortiePercent: valeurDe(etat.contenu, "unitesSortiePercent") };
      journal.push({ etape: "2", envoye: v });
    } else {
      const v = VALEURS.etape3 || {};
      avant.etape3 = { conditions: [], notesCompromis: "" };
      const conds = Array.isArray(v.conditions) ? v.conditions : [];
      for (const cle of ["id_condition", "clef", "jours_validites", "note", "etat"]) {
        corps.delete(`conditionsSuspensivesSelected[][${cle}]`);
      }
      // ⚠ TABLEAUX PARALLELES : meme longueur, meme ordre. C'est ainsi que leur
      //   formulaire les poste ; s'en ecarter, c'est melanger les conditions.
      for (const c of conds) {
        for (const cle of ["id_condition", "clef", "jours_validites", "note", "etat"]) {
          corps.append(`conditionsSuspensivesSelected[][${cle}]`, String(c[cle] ?? ""));
        }
      }
      if (v.notesCompromis != null) poser("notesCompromis", v.notesCompromis);
      journal.push({ etape: "3", envoye: v });
    }

    for (const m of pas.modules) corps.append("containerModule[]", m);
    corps.set("containerName", CONTENEUR);
    corps.set("fromStep", pas.de); corps.set("step", pas.vers);
    corps.set("idAnnonce", ANNONCE); corps.set("basket", etat.basket);

    if (pas.enregistre) {
      fs.writeFileSync(fichierAvant, JSON.stringify(avant, null, 1), "utf8");
      console.log(`⚠ ETAT D'AVANT DEPOSE (retour arriere) : ${fichierAvant}`);
      console.log("");
    }
    // ⚠ C'EST CETTE LIGNE, ET ELLE SEULE, QUI ECRIT CHEZ HEKTOR.
    const url = `${XMLRPC_URL}?mode=${encodeURIComponent(ETAPE)}`
      + (pas.enregistre ? "&actionContainer%5B%5D=save&actionContainer%5B%5D=treat" : "");
    const r = await fetch(url, { method: "POST", body: corps,
      headers: { ...ENTETES, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" } });
    etat = lireEtape(await r.text());
    console.log(`   etape ${pas.de} -> ${pas.vers}${pas.enregistre ? "  [ENREGISTREMENT]" : ""}`
                + `  index=${etat.index} · ${etat.contenu.length} car`);
    await new Promise((x) => setTimeout(x, 1500));
  }

  // ─── LA RELECTURE, par une ouverture NEUVE ───
  console.log("");
  await new Promise((x) => setTimeout(x, 3000));
  const apres = await ouvrir();
  const A = apres.contenu;

  const lignes = [];
  const cmp = (nom, envoye, retenu) => lignes.push({ nom, envoye, retenu,
    verdict: envoye == null ? "-"
      : (retenu == null || retenu === "" ? "IGNORE ou vide"
      : (String(Number(retenu)) === String(Number(envoye)) || retenu === envoye ? "GARDE  -> B"
      : `REMPLACE par ${retenu}  -> C`)) });

  cmp("prixDeVente", VALEURS.etape0.prixDeVente, valeurDe(A, "prixDeVente"));
  cmp("sequestre", VALEURS.etape0.sequestre, valeurDe(A, "sequestre"));
  cmp("montantHonoraireEntree", VALEURS.etape0.montantHonoraireEntree, valeurDe(A, "montantHonoraireEntree"));
  cmp("unitesEntreePercent", (VALEURS.etape2 || {}).unitesEntreePercent, null);
  cmp("unitesSortiePercent", (VALEURS.etape2 || {}).unitesSortiePercent, null);

  const mandantsApres = toutesLesValeurs(A, "mandants[]");
  lignes.push({ nom: "mandants[]", envoye: (VALEURS.etape0["mandants[]"] || []).join(","),
    retenu: mandantsApres.join(","),
    verdict: mandantsApres.length === (VALEURS.etape0["mandants[]"] || []).length
      ? "GARDE  -> B (l'app peut les piloter)"
      : `REMPLACE (${mandantsApres.length} au lieu de ${(VALEURS.etape0["mandants[]"] || []).length})  -> C` });

  console.log("=== ENVOYE CONTRE RETENU ===");
  for (const l of lignes) {
    console.log("   %s envoye=%s  retenu=%s  %s".replace("%s", String(l.nom).padEnd(24))
      .replace("%s", String(l.envoye).padEnd(12)).replace("%s", String(l.retenu).padEnd(14))
      .replace("%s", l.verdict));
  }
  console.log("");
  console.log("--- ce que le formulaire rend aussi (pour information) ---");
  for (const n of ["prixPublique", "prixNetVendeur", "tauxHonoraireEntree", "montantHonoraireSortie"]) {
    console.log("   %s avant=%s  apres=%s".replace("%s", n.padEnd(24))
      .replace("%s", String(avant._releve[n] ?? valeurDe(avantHtml, n)).padEnd(12))
      .replace("%s", String(valeurDe(A, n))));
  }

  const rapport = path.join(SORTIE, `campagne_${stamp}.json`);
  fs.writeFileSync(rapport, JSON.stringify({ avant, envoye: journal, lignes,
    apres_html_taille: A.length }, null, 1), "utf8");
  fs.writeFileSync(path.join(SORTIE, `apres_${stamp}.html`), A, "utf8");
  console.log("");
  console.log("rapport : " + rapport);
  console.log("RETOUR ARRIERE : node Console/campagne_champs_compromis.js --valeurs " + fichierAvant);
})().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
