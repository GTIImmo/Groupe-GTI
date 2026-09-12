/**
 * LA PAGE DES COMMISSIONS, EN ENTIER : LES VALEURS ET LES CANDIDATS   12/09/2026
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * CE QU'IL RÉPOND, ET POURQUOI CES DEUX QUESTIONS ENSEMBLE.
 *
 *   ① QUE FAUT-IL ENVOYER ? La mesure du 12/09 a montré QUE les champs existent
 *      (`intervenantsEntree[115][...]`, sept champs par personne) mais pas CE
 *      QU'ILS VALENT. On ne code pas contre des noms de champs : « un mauvais nom
 *      de champ n'écrit rien ET ne dit rien » -- leçon du 28/08, payée une soirée.
 *
 *   ② PEUT-ON CHOISIR LA PERSONNE ? Question de Frédéric, 12/09 : « il faut
 *      pouvoir choisir le négociateur si possible mais je sais pas comment Hektor
 *      accepte ou pas ». La réponse est dans la LISTE que la page propose : si
 *      elle ne contient que le négociateur de l'annonce, on ne choisit pas ; si
 *      elle porte toute l'agence, on choisit. Le relevé l'énumère.
 *      ⚠ CE QUE LA LISTE CONTIENT N'EST PAS CE QUE LE SERVEUR ACCEPTE. Une liste
 *        large prouve qu'on PEUT proposer ; seul un envoi réel prouverait qu'il
 *        RETIENT. Ce script ne tranche que la première moitié.
 *
 * ⚠ LA SÉRIE D'IDENTIFIANTS EST UN PIÈGE, ET IL EST DÉJÀ MESURÉ. L'annuaire porte
 *   `hektor_negociateur_id` ET `hektor_user_id`, et le MÊME nombre désigne deux
 *   personnes : 115 vaut ACHON dans la première série, REYNAUD dans la seconde.
 *   La vente 23304 porte l'intervenant 115 et son récapitulatif nomme Corinne
 *   REYNAUD -- c'est donc `hektor_user_id`. Se tromper de série attribuerait la
 *   commission à quelqu'un d'autre, EN SILENCE. Le relevé rapproche donc chaque
 *   candidat de l'annuaire, pour que la concordance soit vue et pas supposée.
 *
 * ⚠ IL N'ENREGISTRE JAMAIS, ET C'EST STRUCTUREL : `actionContainer[]=save` et
 *   `treat` ne sont construits nulle part dans ce fichier.
 * ⚠ LECTURE DE LA SESSION, JAMAIS D'ÉCRITURE : quatre services la partagent.
 *
 *   node Console/releve_commissions_vente.js [genre] [idAnnonce] [idTransaction]
 *      défaut : vente 61943 23304  (une vente réelle, deux négociateurs distincts)
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const RACINE = path.resolve(__dirname, "..");
const GENRE = String(process.argv[2] || "vente").toLowerCase();
const ANNONCE = String(process.argv[3] || "61943");
const TRANSACTION = String(process.argv[4] || "23304");

const ASSISTANTS = {
  vente: {
    etape: "annonce-SuiviVente-vente-getStepVente", conteneur: "PopinVente", cleId: "idVente",
    pas: [{ de: "0", vers: "2", modules: ["infosFinancieresVente",
             "acquereurNotaireAutresProspectsVente", "annonceMandatVente", "agenceInterkabVente"] },
          { de: "2", vers: "3", modules: ["commissionsVente"] }],
  },
  compromis: {
    etape: "annonce-SuiviVente-compromis-getStepCompromis", conteneur: "PopinCompromis",
    cleId: "idCompromis",
    pas: [{ de: "0", vers: "2", modules: ["infosFinancieresCompromis",
             "acquereurNotaireAutresProspectsCompromis", "annonceMandatCompromis",
             "agenceInterkabCompromis"] },
          { de: "2", vers: "3", modules: ["commissionsCompromis"] }],
  },
};
const A = ASSISTANTS[GENRE];
if (!A) { console.error("genre inconnu : " + GENRE); process.exit(1); }

function lireEnv(f) {
  const o = {};
  if (!fs.existsSync(f)) return o;
  for (const l of fs.readFileSync(f, "utf8").split(/\r?\n/)) {
    const m = l.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (m) o[m[1]] = m[2].trim().replace(/^["']|["']$/g, "");
  }
  return o;
}
const ENV = { ...lireEnv(path.join(__dirname, ".env")), ...process.env };
const BASE = (ENV.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr").replace(/\/+$/, "");
const ADMIN_URL = `${BASE}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const HOTE = new URL(BASE).hostname;

const etat0 = JSON.parse(fs.readFileSync(
  path.join(__dirname, "sessions", "storage_state_admin.json"), "utf8"));
const vivant = Date.now() / 1000;
const COOKIES = (etat0.cookies || [])
  .filter((c) => !c.expires || c.expires < 0 || c.expires > vivant)
  .filter((c) => { const d = String(c.domain || "").replace(/^\./, "");
                   return !d || HOTE === d || HOTE.endsWith("." + d); })
  .map((c) => `${c.name}=${c.value}`).join("; ");
const ENTETES = { Cookie: COOKIES, Accept: "application/json, text/javascript, */*; q=0.01",
  "User-Agent": "Mozilla/5.0",
  Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(ANNONCE)}` };

const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const attr = (b, n) => (String(b).match(new RegExp(`\\b${n}\\s*=\\s*["']([^"']*)["']`, "i")) || [])[1] || "";

function champsDuFormulaire(html) {
  const v = new URLSearchParams();
  const re = /<textarea\b[^>]*>[\s\S]*?<\/textarea>|<select\b[^>]*>[\s\S]*?<\/select>|<input\b[^>]*>/gi;
  let m;
  while ((m = re.exec(String(html || "")))) {
    const c = m[0], nom = attr(c, "name");
    if (!nom) continue;
    const bas = c.toLowerCase();
    if (bas.startsWith("<input")) {
      const t = (attr(c, "type") || "text").toLowerCase();
      if (["button", "submit", "file", "image", "reset"].includes(t)) continue;
      if ((t === "radio" || t === "checkbox") && !/\bchecked\b/i.test(c)) continue;
      v.append(nom, attr(c, "value") || ""); continue;
    }
    if (bas.startsWith("<textarea")) {
      v.append(nom, ((c.match(/<textarea\b[^>]*>([\s\S]*?)<\/textarea>/i) || [])[1] || "").trim());
      continue;
    }
    const opts = Array.from(c.matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((o) => o[0]);
    const ch = opts.find((o) => /\bselected\b/i.test(o)) || opts[0];
    if (ch) v.append(nom, attr(ch, "value") || "");
  }
  return v;
}
function lireEtape(t) {
  let j = null; try { j = JSON.parse(t); } catch (_) {}
  const d = (j && j.data) || {};
  return { basket: typeof d.basket === "string" ? d.basket : "",
           contenu: typeof d.stepContent === "string" ? d.stepContent : "",
           index: d.currentStepIndex == null ? null : String(d.currentStepIndex) };
}
async function appel(corps) {
  const r = await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(A.etape)}`, {
    method: "POST", body: corps,
    headers: { ...ENTETES, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" } });
  if (r.status === 403) { console.error("⛔ 403 — ON S'ARRÊTE. Vérifier depuis une AUTRE IP."); process.exit(3); }
  const t = await r.text();
  await dormir(600);
  return lireEtape(t);
}

/** LES CANDIDATS : chaque `addIntervenantRow(this, '{...}')` est une personne
 *  PROPOSÉE. C'est la réponse à « peut-on choisir ? ». */
function candidats(html) {
  const out = [];
  const re = /addIntervenantRow\s*\(\s*this\s*,\s*'([\s\S]*?)'\s*\)/gi;
  let m;
  while ((m = re.exec(String(html || "")))) {
    let brut = m[1];
    // Hektor échappe en \uXXXX dans l'attribut onclick : on déplie avant de lire.
    brut = brut.replace(/\\u([0-9a-fA-F]{4})/g, (_, h) => String.fromCharCode(parseInt(h, 16)))
               .replace(/\\\//g, "/").replace(/&quot;/g, '"').replace(/&amp;/g, "&");
    let o = null; try { o = JSON.parse(brut); } catch (_) { o = null; }
    if (!o) {
      // ⚠ NE PAS SE BATTRE AVEC L'ÉCHAPPEMENT. Les URL d'avatar arrivent en
      //   `\\/` et cassent JSON.parse ; on retente une fois déplié, puis on
      //   tombe sur une lecture au motif -- ce qu'on cherche est UN NUMÉRO, et
      //   il se lit sans analyseur. Un relevé qui rend « 0 candidat » à cause
      //   d'une barre oblique ferait conclure « on ne peut pas choisir ».
      try { o = JSON.parse(brut.replace(/\\+\//g, "/")); } catch (_) { o = null; }
    }
    const lire = (cle) => (brut.match(new RegExp(`"${cle}"\\s*:\\s*"([^"]*)"`)) || [])[1] || "";
    const id = String((o && (o.idUser || o.id)) || lire("idUser") || lire("id") || "");
    if (id) out.push({ idUser: id,
                       nom: String((o && o.nom) || lire("nom") || ""),
                       prenom: String((o && o.prenom) || lire("prenom") || ""),
                       type: String((o && o.type) || lire("type") || ""),
                       cles: o ? Object.keys(o) : [] });
    else out.push({ brut: brut.slice(0, 160) });
  }
  return out;
}

/** LES RETENUS : les sept champs par personne, AVEC LEURS VALEURS. */
function retenus(html) {
  const par = new Map();
  const re = /<input\b[^>]*>|<select\b[^>]*>[\s\S]*?<\/select>/gi;
  let m;
  while ((m = re.exec(String(html || "")))) {
    const nom = attr(m[0], "name");
    const g = nom && nom.match(/^intervenants(Entree|Sortie)\[(\d+)\]\[([a-z_]+)\]$/i);
    if (!g) continue;
    const cle = `${g[1]}[${g[2]}]`;
    if (!par.has(cle)) par.set(cle, { cote: g[1], idUser: g[2], champs: {} });
    let val = attr(m[0], "value");
    if (/^<select/i.test(m[0])) {
      const opts = Array.from(m[0].matchAll(/<option\b[^>]*>[\s\S]*?<\/option>/gi)).map((o) => o[0]);
      const ch = opts.find((o) => /\bselected\b/i.test(o)) || opts[0];
      val = ch ? attr(ch, "value") : "";
    }
    par.get(cle).champs[g[3]] = val;
  }
  return [...par.values()];
}

(async () => {
  console.log(`RELEVÉ DES COMMISSIONS · ${GENRE} ${TRANSACTION} · annonce ${ANNONCE}`);
  console.log(`   ${BASE}   ${COOKIES.split("; ").filter(Boolean).length} cookies vivants`);
  console.log("   ⚠ AUCUN ENREGISTREMENT : actionContainer[] n'existe pas dans ce fichier.");
  console.log("");

  const ouverture = new URLSearchParams();
  ouverture.set("idAnnonce", ANNONCE);
  if (TRANSACTION && TRANSACTION !== "-") ouverture.set(A.cleId, TRANSACTION);
  ouverture.set("basket", "");
  ouverture.set("initBasket", "true");
  let etat = await appel(ouverture);
  if (!etat.basket) { console.error("l'ouverture n'a rendu aucun panier — on s'arrête"); process.exit(1); }

  let page2 = null;
  for (const pas of A.pas) {
    const corps = new URLSearchParams();
    for (const [c, v] of champsDuFormulaire(etat.contenu).entries()) {
      if (c === "basket" || c === "idAnnonce") continue;
      corps.append(c, v);
    }
    for (const mo of pas.modules) corps.append("containerModule[]", mo);
    corps.set("containerName", A.conteneur);
    corps.set("fromStep", pas.de);
    corps.set("step", pas.vers);
    corps.set("idAnnonce", ANNONCE);
    corps.set("basket", etat.basket);
    etat = await appel(corps);
    if (pas.vers === "2") page2 = etat;
  }
  if (!page2 || !page2.contenu) { console.error("la page des commissions n'a rien rendu"); process.exit(1); }

  // ─── ① CE QUI EST RETENU, AVEC LES VALEURS ───
  const gardes = retenus(page2.contenu);
  console.log(`─── ① LES INTERVENANTS RETENUS (${gardes.length}) ───`);
  for (const g of gardes) {
    console.log(`   ${g.cote.toUpperCase().padEnd(7)} idUser ${g.idUser}`);
    for (const [k, v] of Object.entries(g.champs)) console.log(`      ${k.padEnd(16)} ${v}`);
  }
  const pct = (c) => { const b = page2.contenu.match(
    new RegExp(`<input\\b[^>]*\\bname\\s*=\\s*["']${c}["'][^>]*>`, "i")); return b ? attr(b[0], "value") : ""; };
  console.log(`   unitesEntreePercent ${pct("unitesEntreePercent")} · unitesSortiePercent ${pct("unitesSortiePercent")}`);
  console.log("");

  // ─── ② QUI PEUT-ON CHOISIR ───
  const props = candidats(page2.contenu);
  const uniq = new Map();
  for (const p of props) if (p.idUser && !uniq.has(p.idUser)) uniq.set(p.idUser, p);
  console.log(`─── ② LES CANDIDATS PROPOSÉS PAR LA PAGE (${uniq.size} personnes distinctes) ───`);
  if (props.length && !uniq.size) {
    console.log("   (JSON non déplié — extrait brut du premier)");
    console.log("   " + (props[0].brut || "").slice(0, 200));
  }
  const annuaire = JSON.parse(execFileSync(
    path.join(RACINE, ".venv", "Scripts", "python.exe"),
    ["-c",
     "import json,os,sys;sys.path.insert(0,r'" + path.join(RACINE, "phase2", "sync") + "');"
     + "from push_contacts_to_supabase import DEFAULT_ENV_FILES,SupabaseRestClient,load_env_file;"
     + "[load_env_file(f) for f in DEFAULT_ENV_FILES];"
     + "c=SupabaseRestClient(base_url=os.environ.get('SUPABASE_URL') or os.environ['VITE_SUPABASE_URL'],"
     + "service_role_key=os.environ['SUPABASE_SERVICE_ROLE_KEY']);"
     + "r=c.request(method='GET',path='app_hektor_negotiator_agency_directory?"
     + "select=hektor_user_id,hektor_negociateur_id,display_name,agence_nom,is_active&limit=500');"
     + "print(json.dumps(r))"], { encoding: "utf8", maxBuffer: 8e6 }));
  const parUser = new Map(annuaire.map((a) => [String(a.hektor_user_id), a]));
  let concordants = 0;
  for (const [id, p] of uniq) {
    const a = parUser.get(id);
    if (a) concordants += 1;
    console.log(`   idUser ${id.padEnd(5)} ${(p.prenom + " " + p.nom).trim().padEnd(28)}`
      + ` annuaire: ${a ? (a.display_name + " · " + (a.agence_nom || "") + (a.is_active ? "" : " (inactif)")) : "INTROUVABLE"}`);
  }
  console.log("");
  console.log(`   concordance avec hektor_user_id : ${concordants}/${uniq.size}`);
  console.log("");

  const sortie = path.join(__dirname, "exports", "mesure_intervenants",
    `commissions_${GENRE}_${TRANSACTION}.json`);
  fs.mkdirSync(path.dirname(sortie), { recursive: true });
  fs.writeFileSync(sortie, JSON.stringify(
    { genre: GENRE, annonce: ANNONCE, transaction: TRANSACTION, pris_le: new Date().toISOString(),
      retenus: gardes, candidats: [...uniq.values()],
      unites: { entree: pct("unitesEntreePercent"), sortie: pct("unitesSortiePercent") } },
    null, 1), "utf8");
  console.log("relevé déposé : " + sortie);
})().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
