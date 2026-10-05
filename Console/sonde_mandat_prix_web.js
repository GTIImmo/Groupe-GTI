// SONDE : l'ecran web « mandat-prix » rend-il le VRAI montant du mandat ? 05/10/2026
//
// L'IDEE EST DE FREDERIC : faire un rattrapage console comme celui du chauffage, mais
// pour recuperer les donnees « mandat prix » directement sur le WEB de Hektor a partir
// de l'id annonce. Parce que c'est l'API qui resout mal l'identifiant (voir
// notice/AUDIT_REGISTRE_MANDATS_2026-10-05.md §12) -- l'interface, elle, affiche le
// bon mandat au negociateur.
//
// LES POINTS D'ENTREE sont deja connus du worker (console_job_worker.js, geste
// « generer un numero de mandat »), qui les appelle EN LECTURE avant d'ecrire :
//     ?mode=chargeannonce_MandatPrix&id=<annonce>
//     ?mode=protexa-mandat&mandat=0&idann=<annonce>
//
// ⛔ LECTURE SEULE, ET C'EST ESSENTIEL. On ne fait QUE les deux GET de preparation.
//   On ne touche PAS aux etapes suivantes (step1/step2 en POST) qui, elles, CREENT un
//   mandat et consomment un numero NON ANNULABLE.
//
//   node Console/sonde_mandat_prix_web.js 61811 62049 62567
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.HEKTOR_BASE_URL || "https://www.gti-immobilier.fr";
const ADMIN_URL = `${BASE.replace(/\/+$/, "")}/admin/`;
const XMLRPC_URL = `${BASE.replace(/\/+$/, "")}/admin/xmlrpc.php`;
const IDS = process.argv.slice(2).filter((x) => /^\d+$/.test(x));

(async () => {
  if (!IDS.length) throw new Error("donner au moins un idAnnonce");
  // ⚠ LA SESSION DU DEPOT A EXPIRE LE 29/06 : les deux GET rendaient 403. Le worker,
  //   lui, garde une session FRAICHE par service dans Console/sessions/.
  //   On prend la plus recente, en EVITANT celle du worker Documents quand il drame
  //   une file -- on ne lui prend pas son souffle.
  const dossier = path.resolve(__dirname, "sessions");
  const candidats = fs.existsSync(dossier)
    ? fs.readdirSync(dossier)
        .filter((f) => f.startsWith("storage_state_") && f.endsWith(".json"))
        .filter((f) => !/documents/.test(f) || process.env.AUTORISER_SESSION_DOCUMENTS === "1")
        .map((f) => ({ f: path.join(dossier, f), t: fs.statSync(path.join(dossier, f)).mtimeMs }))
        .sort((a, b) => b.t - a.t)
    : [];
  const storageState = candidats.length ? candidats[0].f : path.resolve(__dirname, "storage_state.json");
  if (!fs.existsSync(storageState)) throw new Error("session console introuvable");
  console.log("session : " + path.basename(storageState) + "  ("
    + new Date(fs.statSync(storageState).mtimeMs).toISOString().slice(0, 16) + ")");

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ storageState });
  const page = await context.newPage();
  await page.goto(ADMIN_URL, { waitUntil: "domcontentloaded" });

  for (const id of IDS) {
    console.log("######## annonce " + id + " ########");
    // ⭐ chargeannonce_MandatPrix est un ONGLET : « Mandat N° 18466 » avec rel="49|0".
    //   49 est l'identifiant PROTEXA du mandat. C'est avec LUI qu'on ouvre son ecran.
    //   Le 2e argument accepte donc un identifiant de mandat (MANDAT_ID), sinon 0 = neuf.
    const mandatId = process.env.MANDAT_ID || "0";
    for (const mode of [
      `mode=chargeannonce_MandatPrix&id=${encodeURIComponent(id)}&lang=fr`,
      `mode=protexa-mandat&mandat=${encodeURIComponent(mandatId)}&idann=${encodeURIComponent(id)}`,
    ]) {
      const out = await page.evaluate(async ({ url, referer }) => {
        const res = await fetch(url, { credentials: "include", headers: { Referer: referer } });
        return { status: res.status, text: await res.text() };
      }, {
        url: `${XMLRPC_URL}?${mode}`,
        referer: `${ADMIN_URL}?page=/mes-biens/mon-bien/mandat-prix&id=${encodeURIComponent(id)}`,
      });
      console.log("  --- " + mode.split("&")[0] + "  HTTP " + out.status + " (" + out.text.length + " car.) ---");
      // On GARDE la page : une regex sur du HTML inconnu ne prouve rien, on la lit.
      const sortie = path.resolve(__dirname, "exports", `mandatprix_${id}_${mode.split("&")[0].replace(/[^a-z0-9]/gi, "_")}.html`);
      fs.mkdirSync(path.dirname(sortie), { recursive: true });
      fs.writeFileSync(sortie, out.text, "utf-8");
      console.log("       ecrit : " + path.basename(sortie));
      // On cherche ce qui ressemble a un montant, un numero, des honoraires.
      const t = out.text;
      const interessant = [];
      for (const re of [
        /"?(montant|prix|honoraires|numero|no_mandat|NO_MANDAT|mandant|type_mandat)"?\s*[:=]\s*"?([^",;}\n<]{1,40})/gi,
        /name="([^"]*(?:montant|prix|honoraire|mandat)[^"]*)"[^>]*value="([^"]{0,40})"/gi,
      ]) {
        let m;
        while ((m = re.exec(t)) !== null && interessant.length < 24) {
          interessant.push(`${m[1]} = ${String(m[2]).trim()}`);
        }
      }
      if (interessant.length) {
        for (const x of [...new Set(interessant)].slice(0, 18)) console.log("       " + x);
      } else {
        console.log("       (rien de reconnaissable) debut : " + t.slice(0, 160).replace(/\s+/g, " "));
      }
    }
    console.log("");
  }
  await browser.close();
})().catch((e) => { console.error("ECHEC :", e.message); process.exit(1); });
