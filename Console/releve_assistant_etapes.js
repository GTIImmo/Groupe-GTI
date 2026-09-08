/**
 * RELEVÉ DES ÉTAPES DE L'ASSISTANT — tâche 0.1, l'inventaire manquant
 * ═══════════════════════════════════════════════════════════════════════════════
 * 08/09/2026.
 *
 * POURQUOI CE SCRIPT EXISTE. La tâche 0.1 (« LA CAMPAGNE DES CHAMPS ») est la
 * phase BLOQUANTE du chantier -- « rien ne se code avant cette phase, c'est elle
 * qui décide de la forme des trois autres ». Elle est restée à `[~]` depuis le
 * 03/09 avec cette phrase :
 *
 *     « les étapes 2, 3 et 4 n'ont pas pu être inventoriées -- l'assistant REFUSE
 *       D'AVANCER sous automatisation. Il faudra soit un relevé fait à la main
 *       par Frédéric, soit lire les définitions du module
 *       Modules/GenericPopinStepperManager. »
 *
 * ⚠ CETTE PHRASE N'EST PLUS VRAIE. Le 08/09, le worker a franchi les étapes
 *   0 → 2 → 3 TROIS FOIS sous automatisation (travaux 8461bd33, 6d2853ea,
 *   2652884b), en reposant à chaque étape ce que Hektor venait de rendre. Ce
 *   n'est donc pas l'automatisation que l'assistant refuse : c'est un formulaire
 *   qu'on ne lui rend pas fidèlement. Le relevé du 03/09 se heurtait à ça.
 *
 * CE QU'IL FAIT : il refait exactement le trajet du worker, en REPOSANT ce que
 * Hektor rend, et il dépose le contenu de chaque étape avec la liste de ses
 * champs -- name, type, valeur, et les options des <select>.
 *
 * ⚠ IL N'ENREGISTRE JAMAIS, ET C'EST STRUCTUREL, PAS UNE PRÉCAUTION.
 *   L'enregistrement chez Hektor n'existe que si l'URL porte
 *   `actionContainer[]=save&actionContainer[]=treat` (worker, `pas.enregistre`).
 *   Ce script ne construit JAMAIS ces paramètres -- il n'y a pas de drapeau à
 *   oublier, pas de branche à se tromper. Le dernier pas est parcouru comme les
 *   autres : on lit ce que l'étape rend, et on s'arrête.
 * ⚠ LECTURE DE LA SESSION, JAMAIS D'ÉCRITURE : storage_state_admin.json est lu,
 *   jamais réécrit -- quatre services le partagent.
 *
 *   node Console/releve_assistant_etapes.js [genre] [idAnnonce] [idTransaction]
 *      genre = compromis (défaut) | vente
 */
const fs = require("fs");
const path = require("path");

const GENRE = String(process.argv[2] || "compromis").toLowerCase();
const ANNONCE = String(process.argv[3] || "24933");
const TRANSACTION = String(process.argv[4] || "50078");

// Recopié du worker (ASSISTANTS_HEKTOR) -- volontairement, pour qu'un outil de
// mesure ne dépende pas du code qu'il sert à instruire.
const ASSISTANTS = {
  compromis: {
    coquille: "annonce-SuiviVente-compromis-createCompromis",
    etape: "annonce-SuiviVente-compromis-getStepCompromis",
    conteneur: "PopinCompromis",
    cleId: "idCompromis",
    pas: [
      { de: "0", vers: "2", modules: ["infosFinancieresCompromis",
          "acquereurNotaireAutresProspectsCompromis", "annonceMandatCompromis",
          "agenceInterkabCompromis"] },
      { de: "2", vers: "3", modules: ["commissionsCompromis"] },
      { de: "3", vers: "3", modules: ["conditionsSuspensives"] },   // ⚠ SANS save/treat
    ],
  },
  vente: {
    coquille: "annonce-SuiviVente-vente-createVente",
    etape: "annonce-SuiviVente-vente-getStepVente",
    conteneur: "PopinVente",
    cleId: "idVente",
    pas: [
      { de: "0", vers: "2", modules: ["infosFinancieresVente",
          "acquereurNotaireAutresProspectsVente", "annonceMandatVente",
          "agenceInterkabVente"] },
      { de: "2", vers: "3", modules: ["commissionsVente"] },
      { de: "3", vers: "3", modules: ["recapitulatifVente"] },      // ⚠ SANS save/treat
    ],
  },
};

const A = ASSISTANTS[GENRE];
if (!A) { console.error("genre inconnu : " + GENRE); process.exit(1); }

const BASE = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${BASE.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const SESSION = path.resolve(__dirname, "sessions", "storage_state_admin.json");
const SORTIE = path.resolve(__dirname, "exports", "releve_assistant");

const etat0 = JSON.parse(fs.readFileSync(SESSION, "utf8"));
const maintenant = Date.now() / 1000;
const COOKIES = (etat0.cookies || [])
  .filter((c) => !c.expires || c.expires < 0 || c.expires > maintenant)
  .map((c) => `${c.name}=${c.value}`).join("; ");

const ENTETES = {
  Cookie: COOKIES,
  Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(ANNONCE)}`,
  Accept: "application/json, text/javascript, */*; q=0.01",
  "User-Agent": "Mozilla/5.0",
};

function attr(balise, nom) {
  const m = String(balise).match(new RegExp(`\\b${nom}\\s*=\\s*["']([^"']*)["']`, "i"));
  return m ? m[1] : "";
}

/** Recopie fidèle de extractHektorFormValues du worker. */
function champsDuFormulaire(html) {
  const valeurs = new URLSearchParams();
  const regex = /<textarea\b[^>]*>[\s\S]*?<\/textarea>|<select\b[^>]*>[\s\S]*?<\/select>|<input\b[^>]*>/gi;
  let m;
  while ((m = regex.exec(String(html || "")))) {
    const champ = m[0];
    const nom = attr(champ, "name");
    if (!nom) continue;
    const bas = champ.toLowerCase();
    if (bas.startsWith("<input")) {
      const type = (attr(champ, "type") || "text").toLowerCase();
      if (["button", "submit", "file", "image", "reset"].includes(type)) continue;
      if ((type === "radio" || type === "checkbox") && !/\bchecked\b/i.test(champ)) continue;
      valeurs.append(nom, attr(champ, "value") || "");
      continue;
    }
    if (bas.startsWith("<textarea")) {
      const corps = (champ.match(/<textarea\b[^>]*>([\s\S]*?)<\/textarea>/i) || [])[1] || "";
      valeurs.append(nom, corps.replace(/&amp;/g, "&").replace(/&lt;/g, "<")
                              .replace(/&gt;/g, ">").replace(/&quot;/g, '"').trim());
      continue;
    }
    const options = Array.from(champ.matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((o) => o[0]);
    const choisie = options.find((o) => /\bselected\b/i.test(o)) || options[0];
    if (choisie) valeurs.append(nom, attr(choisie, "value") || "");
  }
  return valeurs;
}

/** L'inventaire lisible d'une étape : chaque champ, son type, sa valeur. */
function inventaire(html) {
  const lignes = [];
  const regex = /<textarea\b[^>]*>[\s\S]*?<\/textarea>|<select\b[^>]*>[\s\S]*?<\/select>|<input\b[^>]*>/gi;
  let m;
  while ((m = regex.exec(String(html || "")))) {
    const champ = m[0];
    const nom = attr(champ, "name");
    if (!nom) continue;
    const bas = champ.toLowerCase();
    if (bas.startsWith("<select")) {
      const options = Array.from(champ.matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((o) => o[0]);
      const choisie = options.find((o) => /\bselected\b/i.test(o));
      lignes.push({ nom, type: "select", valeur: choisie ? attr(choisie, "value") : "",
                    options: options.length,
                    apercu: options.slice(0, 6).map((o) => attr(o, "value") + "="
                            + o.replace(/<[^>]+>/g, "").trim().slice(0, 22)) });
      continue;
    }
    if (bas.startsWith("<textarea")) {
      const corps = (champ.match(/<textarea\b[^>]*>([\s\S]*?)<\/textarea>/i) || [])[1] || "";
      lignes.push({ nom, type: "textarea", valeur: corps.replace(/<[^>]+>/g, "").trim().slice(0, 60) });
      continue;
    }
    const type = (attr(champ, "type") || "text").toLowerCase();
    lignes.push({ nom, type, valeur: attr(champ, "value"),
                  coche: /\bchecked\b/i.test(champ) || undefined });
  }
  return lignes;
}

function lireEtape(texte) {
  let j = null;
  try { j = JSON.parse(texte); } catch (_) { j = null; }
  const d = (j && j.data) || {};
  return {
    basket: typeof d.basket === "string" ? d.basket : "",
    contenu: typeof d.stepContent === "string" ? d.stepContent : "",
    index: d.currentStepIndex == null ? null : String(d.currentStepIndex),
    succes: j ? j.success !== false : null,
    brut: texte,
  };
}

(async () => {
  fs.mkdirSync(SORTIE, { recursive: true });
  console.log(`RELEVÉ ${GENRE.toUpperCase()} · annonce ${ANNONCE} · transaction ${TRANSACTION}`);
  console.log(`session : ${COOKIES.split("; ").length} cookies vivants`);
  console.log("⚠ AUCUN ENREGISTREMENT : le paramètre actionContainer[] n'est jamais construit.");
  console.log("");

  // ── ouverture ──
  await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(A.coquille)}`, { headers: ENTETES });
  const ouverture = new URLSearchParams();
  ouverture.set("idAnnonce", ANNONCE);
  ouverture.set(A.cleId, TRANSACTION);
  ouverture.set("basket", "");
  ouverture.set("initBasket", "true");
  let rep = await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(A.etape)}`, {
    method: "POST", body: ouverture,
    headers: { ...ENTETES, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
  });
  let etat = lireEtape(await rep.text());
  if (!etat.basket) { console.error("l'ouverture n'a rendu aucun panier -- on s'arrête"); process.exit(1); }

  const releve = { genre: GENRE, annonce: ANNONCE, transaction: TRANSACTION,
                   pris_le: new Date().toISOString(), etapes: [] };

  const montrer = (titre, etatCourant) => {
    const champs = inventaire(etatCourant.contenu);
    console.log(`─── ${titre} ─── index=${etatCourant.index} · ${etatCourant.contenu.length} car · ${champs.length} champs`);
    for (const c of champs) {
      const v = c.type === "select"
        ? `${c.valeur}   (${c.options} options : ${(c.apercu || []).join(", ")})`
        : c.valeur;
      console.log(`   ${c.nom.padEnd(34)} ${c.type.padEnd(9)} ${String(v).slice(0, 96)}`);
    }
    console.log("");
    releve.etapes.push({ titre, index: etatCourant.index, champs });
    fs.writeFileSync(path.join(SORTIE, `${GENRE}_${titre.replace(/[^\w]+/g, "_")}.html`),
                     etatCourant.contenu, "utf8");
  };

  montrer("ouverture", etat);

  for (const pas of A.pas) {
    const corps = new URLSearchParams();
    for (const [cle, val] of champsDuFormulaire(etat.contenu).entries()) {
      if (cle === "basket" || cle === "idAnnonce") continue;
      corps.append(cle, val);
    }
    for (const m of pas.modules) corps.append("containerModule[]", m);
    corps.set("containerName", A.conteneur);
    corps.set("fromStep", pas.de);
    corps.set("step", pas.vers);
    corps.set("idAnnonce", ANNONCE);
    corps.set("basket", etat.basket);

    // ⚠ URL SANS actionContainer[] : c'est ce qui sépare « avancer » d'« enregistrer ».
    rep = await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(A.etape)}`, {
      method: "POST", body: corps,
      headers: { ...ENTETES, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
    });
    etat = lireEtape(await rep.text());
    if (!etat.contenu) {
      console.log(`─── etape ${pas.de} -> ${pas.vers} : AUCUN CONTENU RENDU (succes=${etat.succes})`);
      console.log(`    reponse (300 premiers car) : ${etat.brut.replace(/\s+/g, " ").slice(0, 300)}`);
      console.log("");
      releve.etapes.push({ titre: `etape ${pas.de}->${pas.vers}`, vide: true,
                           reponse: etat.brut.slice(0, 1000) });
      continue;
    }
    montrer(`etape ${pas.de} -> ${pas.vers} [${pas.modules.join("+")}]`, etat);
    await new Promise((r) => setTimeout(r, 1200));   // on reste poli
  }

  const fichier = path.join(SORTIE, `releve_${GENRE}_${ANNONCE}_${TRANSACTION}.json`);
  fs.writeFileSync(fichier, JSON.stringify(releve, null, 1), "utf8");
  console.log("relevé déposé : " + fichier);
  const tous = new Set();
  for (const e of releve.etapes) for (const c of e.champs || []) tous.add(c.nom);
  console.log(`TOTAL : ${tous.size} champs distincts sur ${releve.etapes.length} vues`);
})().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
