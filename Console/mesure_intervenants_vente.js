/**
 * LA COMMISSION D'UNE VENTE EST-ELLE ATTRIBUÉE À QUELQU'UN ?          12/09/2026
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * LA QUESTION, ET POURQUOI ELLE SE POSE MAINTENANT. En lisant en direct les trois
 * pages de l'assistant de vente (bien 24933, 12/09), la page 3 dit ceci, mot pour
 * mot :
 *
 *     « Vous n'avez pas d'intervenant sélectionné. »
 *     « Commission administrateur   8 333 €/HT   soit 10 000 €/TTC »
 *
 * Or la page 2 PROPOSE un négociateur (Mme Emmanuelle PEREIRA, des deux côtés,
 * 50 % / 50 %) -- mais ce nom n'est pas une valeur, c'est un BOUTON : il appelle
 * `addIntervenantRow(...)`, qui injecte alors les champs `intervenants[...]`.
 * Tant que personne ne clique, aucun champ n'existe, donc rien n'est envoyé.
 *
 * ⚠ ET LE WORKER NE CLIQUE JAMAIS. Il repose fidèlement le formulaire que Hektor
 *   lui rend -- c'est sa règle, et c'est une bonne règle. Mais un bouton ne se
 *   repose pas. Donc toute vente née dans l'app partirait avec sa commission non
 *   attribuée, et le négociateur qui a vendu n'y figurerait pas.
 *
 * ⚠ CE SCRIPT NE PROUVE PAS CELA. Il répond à la question d'AVANT : est-ce que
 *   les ventes faites À LA MAIN dans Hektor, elles, portent un intervenant ? Si
 *   elles n'en portent pas non plus, il n'y a rien à corriger et la page 3 dit
 *   simplement comment cette agence travaille. Si elles en portent, alors l'app
 *   perd une information que tout le monde saisit. On mesure, PUIS on conclut.
 *
 * POURQUOI LA CONSOLE ET PAS L'API. Mesuré le 12/09 sur les 7 612 ventes du
 * miroir : `partAdmin` vaut 0 sur 7 612, `retro_idUser` sur 7 612. L'API ne rend
 * JAMAIS cette information -- exactement comme les notaires (0 sur 10 586).
 * La colonne `intervenants_json` de app_affaire_console existe et vaut NULL sur
 * les 9 218 transactions relues : le rattrapage s'arrête à la page 1.
 *
 * ⚠ IL N'ENREGISTRE JAMAIS, ET C'EST STRUCTUREL, PAS UNE PRÉCAUTION.
 *   L'enregistrement n'existe chez Hektor que si l'URL porte
 *   `actionContainer[]=save&actionContainer[]=treat`. Ces deux mots ne sont
 *   construits NULLE PART dans ce fichier : il n'y a pas de drapeau à oublier.
 * ⚠ LECTURE DE LA SESSION, JAMAIS D'ÉCRITURE : storage_state_admin.json est lu,
 *   jamais réécrit -- quatre services le partagent.
 *
 * ─── LA CADENCE N'EST PAS NÉGOCIABLE ───
 * Celle de NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09, la seule méthode console
 * qui n'ait jamais rien déclenché (56 926 lectures). Ici une vente coûte TROIS
 * requêtes au lieu d'une, donc on compte en REQUÊTES, pas en ventes :
 *     0,5 s entre deux requêtes  ·  pause de 60 s tous les 90  ·  2 s entre ventes
 * ⚠ UN 403 EST LE DÉBUT D'UN BANNISSEMENT, PAS UN INCIDENT À REESSAYER. On
 *   s'arrête net, code de sortie 3, et on vérifie depuis une AUTRE IP. Notre IP a
 *   déjà été bannie une fois, en juillet, pour l'avoir ignoré.
 * ⚠ JAMAIS DEUX FLUX CONSOLE EN MÊME TEMPS : le script refuse de démarrer si un
 *   travail worker tourne. C'est le doublement de débit qui coûte cher.
 *
 *   node Console/mesure_intervenants_vente.js [nombre]
 *      nombre = combien de ventes échantillonner (défaut 40)
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const RACINE = path.resolve(__dirname, "..");
const COMBIEN = Math.max(1, Math.min(400, Number(process.argv[2] || 40)));

// ─── LE DOMAINE SE LIT DANS .env, IL NE SE DEVINE PAS ───
// Leçon du 11/09 : la porte web est passée à www.gti-immobilier.fr tandis que la
// porte API restait sur l'ancienne adresse. Un outil qui code le domaine en dur
// interroge le mauvais serveur et rend un 403 qu'on prend pour un bannissement.
function lireEnv(fichier) {
  const out = {};
  if (!fs.existsSync(fichier)) return out;
  for (const ligne of fs.readFileSync(fichier, "utf8").split(/\r?\n/)) {
    const m = ligne.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!m) continue;
    out[m[1]] = m[2].trim().replace(/^["']|["']$/g, "");
  }
  return out;
}
const ENV = { ...lireEnv(path.join(__dirname, ".env")), ...process.env };
const BASE = (ENV.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr").replace(/\/+$/, "");
const ADMIN_URL = `${BASE}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const SESSION = path.join(__dirname, "sessions", "storage_state_admin.json");
const SORTIE = path.join(__dirname, "exports", "mesure_intervenants");

const etat0 = JSON.parse(fs.readFileSync(SESSION, "utf8"));
const maintenant = Date.now() / 1000;
// ⚠ LE PIÈGE DU 11/09 : deux domaines dans le même bocal, et un pot commun indexé
//   par NOM SEUL -- deux PHPSESSID, le mauvais gagnait. Ici on ne garde que les
//   cookies du domaine visé.
const HOTE = new URL(BASE).hostname;
const COOKIES = (etat0.cookies || [])
  .filter((c) => !c.expires || c.expires < 0 || c.expires > maintenant)
  .filter((c) => {
    const d = String(c.domain || "").replace(/^\./, "");
    return !d || HOTE === d || HOTE.endsWith("." + d);
  })
  .map((c) => `${c.name}=${c.value}`).join("; ");

const ENTETES = {
  Cookie: COOKIES,
  Accept: "application/json, text/javascript, */*; q=0.01",
  "User-Agent": "Mozilla/5.0",
};

const PAS = [
  { de: "0", vers: "2", modules: ["infosFinancieresVente",
      "acquereurNotaireAutresProspectsVente", "annonceMandatVente", "agenceInterkabVente"] },
  { de: "2", vers: "3", modules: ["commissionsVente"] },
];

const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
let requetes = 0;

function attr(balise, nom) {
  const m = String(balise).match(new RegExp(`\\b${nom}\\s*=\\s*["']([^"']*)["']`, "i"));
  return m ? m[1] : "";
}

/** Recopie fidèle de extractHektorFormValues du worker : on repose ce qu'il rend. */
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
      valeurs.append(nom, corps.replace(/&amp;/g, "&").trim());
      continue;
    }
    const options = Array.from(champ.matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((o) => o[0]);
    const choisie = options.find((o) => /\bselected\b/i.test(o)) || options[0];
    if (choisie) valeurs.append(nom, attr(choisie, "value") || "");
  }
  return valeurs;
}

function lireEtape(texte) {
  let j = null;
  try { j = JSON.parse(texte); } catch (_) { j = null; }
  const d = (j && j.data) || {};
  return {
    basket: typeof d.basket === "string" ? d.basket : "",
    contenu: typeof d.stepContent === "string" ? d.stepContent : "",
    index: d.currentStepIndex == null ? null : String(d.currentStepIndex),
    brut: texte,
  };
}

class Banni extends Error {}

async function appel(corps, annonce) {
  // La cadence se compte en REQUÊTES : une vente en coûte trois.
  if (requetes && requetes % 90 === 0) {
    process.stdout.write(`\n   … pause de 60 s après ${requetes} requêtes\n`);
    await dormir(60000);
  }
  requetes += 1;
  const rep = await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(
    "annonce-SuiviVente-vente-getStepVente")}`, {
    method: "POST", body: corps,
    headers: { ...ENTETES,
      Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(annonce)}`,
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
  });
  if (rep.status === 403) throw new Banni("403");
  const t = await rep.text();
  await dormir(500);
  return lireEtape(t);
}

/** Ce qu'on cherche : un intervenant RETENU, pas un intervenant PROPOSÉ. */
function verdictEtape2(html) {
  const noms = new Set();
  const regex = /<input\b[^>]*>|<select\b[^>]*>/gi;
  let m;
  while ((m = regex.exec(String(html || "")))) {
    const n = attr(m[0], "name");
    if (n && /interven/i.test(n)) noms.add(n);
  }
  const pct = (cle) => {
    const r = new RegExp(`<input\\b[^>]*\\bname\\s*=\\s*["']${cle}["'][^>]*>`, "i");
    const b = String(html || "").match(r);
    return b ? attr(b[0], "value") : "";
  };
  return {
    champs_intervenant: [...noms],
    entree_percent: pct("unitesEntreePercent"),
    sortie_percent: pct("unitesSortiePercent"),
  };
}

function verdictEtape3(html) {
  const texte = String(html || "").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ")
    .replace(/&#039;|&rsquo;/g, "'").replace(/\s+/g, " ").trim();
  const aucun = /n'avez pas d'intervenant/i.test(texte);
  const admin = (texte.match(/Commission administrateur\s*([\d\s.,]+)\s*.\/?HT/i) || [])[1] || "";
  return { aucun_intervenant: aucun, commission_administrateur: admin.trim(), texte };
}

(async () => {
  fs.mkdirSync(SORTIE, { recursive: true });

  // ─── COURTOISIE : jamais deux flux console en même temps ───
  let occupe = "";
  try {
    occupe = execFileSync(path.join(RACINE, ".venv", "Scripts", "python.exe"),
      ["-c",
       "import os,sys;sys.path.insert(0,r'" + path.join(RACINE, "phase2", "sync") + "');"
       + "from push_contacts_to_supabase import DEFAULT_ENV_FILES,SupabaseRestClient,load_env_file;"
       + "[load_env_file(f) for f in DEFAULT_ENV_FILES];"
       + "c=SupabaseRestClient(base_url=os.environ.get('SUPABASE_URL') or os.environ['VITE_SUPABASE_URL'],"
       + "service_role_key=os.environ['SUPABASE_SERVICE_ROLE_KEY']);"
       + "r=c.request(method='GET',path='app_console_job?select=id,status&status=eq.running&limit=3');"
       + "print(len(r))"],
      { encoding: "utf8", timeout: 60000 }).trim();
  } catch (_) { occupe = "?"; }
  if (occupe !== "0" && occupe !== "?") {
    console.error(`REFUS : ${occupe} travail(aux) worker en cours. Deux flux console en même `
      + "temps, c'est le doublement de débit qui a fait bannir notre IP en juillet.");
    process.exit(2);
  }

  // ─── L'ÉCHANTILLON : des ventes FAITES À LA MAIN dans Hektor ───
  // On écarte le bien témoin 24933 : ses ventes viennent de l'app, ce sont elles
  // qu'on instruit. Les plus récentes d'abord -- si une pratique a changé, c'est
  // la pratique actuelle qui nous intéresse.
  const sql = "SELECT hektor_vente_id, hektor_annonce_id, date_vente, prix, honoraires "
    + "FROM hektor_vente WHERE hektor_annonce_id <> '24933' AND hektor_vente_id IS NOT NULL "
    + `ORDER BY date_vente DESC LIMIT ${COMBIEN}`;
  const brut = execFileSync(path.join(RACINE, ".venv", "Scripts", "python.exe"),
    ["-c", "import json,sqlite3,sys;c=sqlite3.connect('file:" +
      path.join(RACINE, "data", "hektor.sqlite").replace(/\\/g, "/") +
      "?mode=ro',uri=True);c.row_factory=sqlite3.Row;"
      + "print(json.dumps([dict(r) for r in c.execute(sys.argv[1])]))", sql],
    { encoding: "utf8", maxBuffer: 8e6 });
  const ventes = JSON.parse(brut);

  console.log("MESURE : LA COMMISSION D'UNE VENTE EST-ELLE ATTRIBUÉE ?");
  console.log(`   domaine   ${BASE}`);
  console.log(`   session   ${COOKIES.split("; ").filter(Boolean).length} cookies vivants pour ${HOTE}`);
  console.log(`   échantillon ${ventes.length} ventes réelles, les plus récentes, bien témoin exclu`);
  console.log("   ⚠ AUCUN ENREGISTREMENT : actionContainer[] n'est construit nulle part.");
  console.log("");

  const lignes = [];
  let avecIntervenant = 0, sansIntervenant = 0, illisibles = 0;

  for (const v of ventes) {
    const annonce = String(v.hektor_annonce_id);
    const id = String(v.hektor_vente_id);
    try {
      const ouverture = new URLSearchParams();
      ouverture.set("idAnnonce", annonce);
      ouverture.set("idVente", id);
      ouverture.set("basket", "");
      ouverture.set("initBasket", "true");
      let etat = await appel(ouverture, annonce);
      if (!etat.basket) {
        illisibles += 1;
        lignes.push({ vente: id, annonce, verdict: "ouverture sans panier" });
        console.log(`   vente ${id.padEnd(7)} annonce ${annonce.padEnd(7)} — ouverture sans panier`);
        await dormir(2000);
        continue;
      }
      let e2 = null, e3 = null;
      for (const pas of PAS) {
        const corps = new URLSearchParams();
        for (const [cle, val] of champsDuFormulaire(etat.contenu).entries()) {
          if (cle === "basket" || cle === "idAnnonce") continue;
          corps.append(cle, val);
        }
        for (const m of pas.modules) corps.append("containerModule[]", m);
        corps.set("containerName", "PopinVente");
        corps.set("fromStep", pas.de);
        corps.set("step", pas.vers);
        corps.set("idAnnonce", annonce);
        corps.set("basket", etat.basket);
        etat = await appel(corps, annonce);
        if (pas.vers === "2") e2 = etat;
        if (pas.vers === "3") e3 = etat;
      }
      const c2 = e2 ? verdictEtape2(e2.contenu) : { champs_intervenant: [] };
      const c3 = e3 ? verdictEtape3(e3.contenu) : { aucun_intervenant: null };
      // Deux signaux INDÉPENDANTS, et on exige qu'ils concordent : les champs
      // injectés à l'étape 2, et la phrase du récapitulatif. Un seul des deux
      // suffirait à se tromper.
      let verdict;
      if (c3.aucun_intervenant === true) { verdict = "AUCUN intervenant"; sansIntervenant += 1; }
      else if (c3.aucun_intervenant === false) { verdict = "intervenant RETENU"; avecIntervenant += 1; }
      else { verdict = "illisible"; illisibles += 1; }
      lignes.push({ vente: id, annonce, date: v.date_vente, honoraires: v.honoraires,
                    verdict, ...c2, commission_administrateur: c3.commission_administrateur,
                    extrait: String(c3.texte || "").slice(0, 220) });
      console.log(`   vente ${id.padEnd(7)} annonce ${annonce.padEnd(7)} ${String(v.date_vente).padEnd(11)} `
        + `${verdict.padEnd(20)} entree=${c2.entree_percent || "-"} sortie=${c2.sortie_percent || "-"} `
        + `champs=${c2.champs_intervenant.length}`);
    } catch (e) {
      if (e instanceof Banni) {
        console.error("\n⛔ 403 — ON S'ARRÊTE. Ne pas relancer. Vérifier depuis une AUTRE IP.");
        fs.writeFileSync(path.join(SORTIE, "mesure_partielle.json"),
                         JSON.stringify(lignes, null, 1), "utf8");
        process.exit(3);
      }
      illisibles += 1;
      lignes.push({ vente: id, annonce, verdict: "erreur", erreur: String(e && e.message || e) });
      console.log(`   vente ${id.padEnd(7)} annonce ${annonce.padEnd(7)} — erreur : ${e && e.message}`);
    }
    await dormir(2000);
  }

  const fichier = path.join(SORTIE, `mesure_${new Date().toISOString().slice(0, 10)}.json`);
  fs.writeFileSync(fichier, JSON.stringify(lignes, null, 1), "utf8");
  const total = avecIntervenant + sansIntervenant;
  console.log("");
  console.log("─── LE VERDICT ───");
  console.log(`   ventes lues                    ${total + illisibles}`);
  console.log(`   un intervenant EST retenu      ${avecIntervenant}`
    + (total ? `   ${(100 * avecIntervenant / total).toFixed(1)} %` : ""));
  console.log(`   AUCUN intervenant              ${sansIntervenant}`
    + (total ? `   ${(100 * sansIntervenant / total).toFixed(1)} %` : ""));
  console.log(`   illisibles                     ${illisibles}`);
  console.log(`   requêtes envoyées              ${requetes}`);
  console.log("");
  console.log("relevé déposé : " + fichier);
})().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
