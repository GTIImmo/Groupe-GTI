/**
 * MESURE — L'ASSISTANT DE HEKTOR PRE-REMPLIT-IL QUAND ON LUI DONNE idCompromis ?
 * ═════════════════════════════════════════════════════════════════════════════
 * 08/09/2026, tache 3.2.
 *
 * CE QU'ON VEUT SAVOIR, ET RIEN D'AUTRE. Le worker envoie une modification en
 * trois temps : il OUVRE l'assistant, il RENVOIE ce que Hektor lui a tendu, il
 * ENREGISTRE. Le deuxieme temps recopie -- il ne reconstruit pas. Tout depend
 * donc de ce que Hektor rend au premier :
 *
 *     formulaire REMPLI   -> on ne change que le montant, le reste est preserve
 *                            parce que c'est Hektor lui-meme qui l'a rendu
 *     formulaire VIERGE   -> le worker comble avec ses valeurs par defaut
 *                            (prixNetVendeur 170 000 -> 180 000) et
 *                            l'enregistrement CREE un second compromis
 *
 * CE QU'ON SAIT DEJA : leur interface envoie `idCompromis` a l'ouverture --
 * releve du 03/09, requete de 75 octets. Voir qu'ils l'envoient N'EST PAS savoir
 * ce que Hektor en fait. Les trois gardes de la nuit du 07 au 08/09 nous ont
 * arretes avant ce point : le formulaire n'a jamais ete ouvert avec cet
 * identifiant, pas une fois.
 *
 * ⚠ LECTURE SEULE, ET C'EST STRUCTUREL : on s'arrete APRES l'ouverture. Aucune
 *   etape, aucun `actionContainer[]=save,treat`. Rien ne s'enregistre. C'est
 *   exactement ce que fait un negociateur qui ouvre la popin puis la ferme.
 * ⚠ ON NE REND JAMAIS LA SESSION. storage_state_admin.json est lu, jamais
 *   reecrit : quatre services le partagent.
 * ⚠ AVEC ET SANS. Une mesure sans contre-epreuve ne prouve rien -- si le
 *   formulaire arrive rempli dans les DEUX cas, ce n'est pas idCompromis qui
 *   remplit, et la conclusion serait fausse.
 *
 *   node Console/mesure_reprise_compromis.js [idAnnonce] [idCompromis]
 */
const fs = require("fs");
const path = require("path");

const ANNONCE = String(process.argv[2] || "24933");
const COMPROMIS = String(process.argv[3] || "50078");

const BASE = process.env.HEKTOR_BASE_URL || "https://groupe-gti-immobilier.la-boite-immo.com";
const ADMIN_URL = `${BASE.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${ADMIN_URL}xmlrpc.php`;
const COQUILLE = "annonce-SuiviVente-compromis-createCompromis";
const ETAPE = "annonce-SuiviVente-compromis-getStepCompromis";
const SESSION = path.resolve(__dirname, "sessions", "storage_state_admin.json");

// Les champs qui decident. Ce sont ceux que le worker « pose » a l'etape 0 --
// donc ceux qu'un formulaire vierge lui ferait ecraser.
const CHAMPS = ["prixPublique", "prixNetVendeur", "prixDeVente", "sequestre",
                "dateCompromis", "dateSignatureActe", "nbJoursRetractation",
                "montantHonoraireSortie", "selectedMandatId"];

function cookiesDeLaSession() {
  const etat = JSON.parse(fs.readFileSync(SESSION, "utf8"));
  const maintenant = Date.now() / 1000;
  return (etat.cookies || [])
    .filter((c) => !c.expires || c.expires < 0 || c.expires > maintenant)
    .map((c) => `${c.name}=${c.value}`).join("; ");
}

// Lit la valeur d'un <input>, quel que soit l'ordre des attributs. Le worker a
// le meme besoin (htmlInputValue) ; on ne partage pas le code pour ne rien
// dependre du worker dans un outil de mesure.
function valeurInput(html, nom) {
  const balises = String(html || "").match(/<input\b[^>]*>/gi) || [];
  for (const b of balises) {
    const n = b.match(/\bname\s*=\s*["']([^"']+)["']/i);
    if (!n || n[1] !== nom) continue;
    const v = b.match(/\bvalue\s*=\s*["']([^"']*)["']/i);
    return v ? v[1] : "";
  }
  return null;   // null = le champ n'existe pas ; "" = il existe et il est vide
}

async function ouvrir(cookies, avecIdentifiant) {
  const entetes = {
    Cookie: cookies,
    Referer: `${ADMIN_URL}?page=/mes-biens/mon-bien&id=${encodeURIComponent(ANNONCE)}`,
    Accept: "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Mozilla/5.0",
  };
  // 1. la coquille, comme le navigateur
  await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(COQUILLE)}`, { headers: entetes });

  // 2. l'ouverture
  const corps = new URLSearchParams();
  corps.set("idAnnonce", ANNONCE);
  if (avecIdentifiant) corps.set("idCompromis", COMPROMIS);
  corps.set("basket", "");
  corps.set("initBasket", "true");
  const rep = await fetch(`${XMLRPC_URL}?mode=${encodeURIComponent(ETAPE)}`, {
    method: "POST",
    body: corps,
    headers: { ...entetes, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
  });
  const texte = await rep.text();
  let json = null;
  try { json = JSON.parse(texte); } catch (_) { json = null; }
  const data = (json && json.data) || {};
  return {
    http: rep.status,
    taille: texte.length,
    succes: json ? json.success !== false : null,
    basket: typeof data.basket === "string" ? data.basket.length : null,
    contenu: typeof data.stepContent === "string" ? data.stepContent : "",
    brut: texte,
  };
}

(async () => {
  const cookies = cookiesDeLaSession();
  console.log(`session lue : ${cookies.split("; ").length} cookies vivants`);
  console.log(`annonce ${ANNONCE} · compromis ${COMPROMIS}`);
  console.log("");

  const sorties = path.resolve(__dirname, "exports", "mesure_reprise");
  fs.mkdirSync(sorties, { recursive: true });

  const resultats = {};
  for (const [nom, avec] of [["AVEC idCompromis", true], ["SANS idCompromis (contre-epreuve)", false]]) {
    const r = await ouvrir(cookies, avec);
    resultats[avec ? "avec" : "sans"] = r;
    const fichier = path.join(sorties, `ouverture_${avec ? "avec" : "sans"}_${ANNONCE}_${COMPROMIS}.html`);
    fs.writeFileSync(fichier, r.contenu || r.brut, "utf8");

    console.log(`--- ${nom} ---`);
    console.log(`   http ${r.http} · reponse ${r.taille} car · success=${r.succes} `
                + `· panier ${r.basket} car · contenu ${r.contenu.length} car`);
    for (const c of CHAMPS) {
      const v = valeurInput(r.contenu, c);
      console.log(`   %s %s`.replace("%s", c.padEnd(24)).replace("%s",
        v === null ? "(champ absent du formulaire)" : v === "" ? "(vide)" : v));
    }
    const acq = (r.contenu.match(/acquereurs\[\]/g) || []).length;
    console.log(`   ${"acquereurs[] presents".padEnd(24)} ${acq}`);
    console.log(`   depose : ${fichier}`);
    console.log("");
    if (avec) await new Promise((r2) => setTimeout(r2, 1500));  // on reste poli
  }

  // ─── LA CONCLUSION SE LIT, ELLE NE SE DEVINE PAS ───
  const a = resultats.avec.contenu;
  const s = resultats.sans.contenu;
  const rempliAvec = CHAMPS.some((c) => { const v = valeurInput(a, c); return v && v !== "0" && v !== "0.00"; });
  const rempliSans = CHAMPS.some((c) => { const v = valeurInput(s, c); return v && v !== "0" && v !== "0.00"; });
  console.log("=== CE QUE CA VEUT DIRE ===");
  if (rempliAvec && !rempliSans) {
    console.log("   REPRISE RECONNUE : idCompromis pre-remplit le formulaire.");
    console.log("   -> le worker recopiera les valeurs de Hektor, la modification est sure.");
  } else if (rempliAvec && rempliSans) {
    console.log("   ⚠ LES DEUX SONT REMPLIS : ce n'est PAS idCompromis qui remplit.");
    console.log("   -> la mesure ne conclut pas ; comparer les deux fichiers deposes.");
  } else if (!rempliAvec) {
    console.log("   ⚠ FORMULAIRE VIERGE MALGRE idCompromis.");
    console.log("   -> l'ouverture ne suffit pas. NE PAS relancer l'essai : il creerait");
    console.log("      un second compromis a 180 000. Remettre la garde de blocage d'abord.");
  }
})().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });
