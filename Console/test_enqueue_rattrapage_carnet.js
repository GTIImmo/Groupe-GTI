// L'ENFILEUR DU RATTRAPAGE DU CARNET (R3) : essai hors ligne.          25/10/2026
//
// On eprouve LE CODE REEL (choisirLeLot et main de enqueue_rattrapage_carnet.js) avec un
// faux Supabase qui note ce qu'on lui demande. Les valeurs sont celles de l'essai 5 (24113).
//
//     node Console/test_enqueue_rattrapage_carnet.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer
process.env.SUPABASE_URL = "https://faux.supabase.co";
process.env.SUPABASE_SERVICE_ROLE_KEY = "cle-de-test";
delete process.env.APP_AFFAIRE_R3_RATTRAPAGE;

const fs = require("fs");
const echecs = [];
function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}

const MAINTENANT = Date.parse("2026-10-25T08:00:00Z");
const VIEUX = "2026-10-23T17:41:54.678+00:00";          // > 6 h
const RECENT = "2026-10-25T07:00:00+00:00";             // 1 h
function monter({ lignes = [], registres = [], file = [] } = {}) {
  const appels = [];
  global.fetch = async (url, opts = {}) => {
    const chemin = String(url).replace("https://faux.supabase.co/rest/v1/", "");
    const m = (opts.method || "GET").toUpperCase();
    appels.push({ m, chemin, corps: opts.body ? JSON.parse(opts.body) : null });
    let rep = [];
    if (m === "POST") rep = null;
    else if (chemin.startsWith("app_affaire_champ_app")) rep = lignes;
    else if (chemin.startsWith("app_affaire_ledger")) rep = registres;
    else if (chemin.startsWith("app_console_job")) rep = file;
    return { ok: true, status: 200, json: async () => rep, text: async () => "" };
  };
  return appels;
}
const L = (aff, champ, constate = VIEUX, etat = "en_attente") => ({ app_affaire_id: aff, champ, etat, constate_le: constate });
const R = (aff, kind, annonce, hektor = "1") => ({ app_affaire_id: aff, kind, hektor_annonce_id: annonce, app_dossier_id: 1068399, hektor_affaire_id: hektor });

(async () => {
  const mod = require("./enqueue_rattrapage_carnet.js");
  {
    monter({ lignes: [L(1001395, "notaire_id"), L(1001395, "numero_mandat"), L(1001394, "notaire_id")],
             registres: [R(1001395, "vente", "24113", "23358"), R(1001394, "compromis", "24113", "50137")] });
    const c = await mod.choisirLeLot({ limit: 50 }, MAINTENANT);
    controle("(1) essai 5 : une seule annonce (24113), ses 3 lignes, notre numero de dossier",
      c.lot.length === 1 && c.lot[0].annonce === "24113" && c.lot[0].lignes.length === 3 && c.lot[0].dossier === 1068399,
      JSON.stringify(c));
  }
  {
    monter({ lignes: [L(1, "notaire_id", RECENT), L(2, "numero_mandat", null)],
             registres: [R(1, "vente", "100"), R(2, "offre", "200")] });
    const c = await mod.choisirLeLot({ limit: 50 }, MAINTENANT);
    controle("(2) la regle des 6 h : constatee il y a 1 h -> pas visee ; jamais constatee -> visee",
      c.lot.map((a) => a.annonce).join(",") === "200", JSON.stringify(c.lot));
  }
  {
    monter({ lignes: [L(1, "notaire_id"), L(2, "numero_mandat")], registres: [R(1, "vente", "100"), R(2, "offre", "200")],
             file: [{ hektor_annonce_id: "100" }] });
    const c = await mod.choisirLeLot({ limit: 50 }, MAINTENANT);
    controle("(3) une annonce qui a deja une relecture en file n'est pas reposee (elle jugera elle-meme)",
      c.lot.map((a) => a.annonce).join(",") === "200" && c.deja_en_file.join(",") === "100", JSON.stringify(c));
  }
  {
    monter({ lignes: [L(1, "notaire_id"), L(2, "numero_mandat")], registres: [R(1, "vente", "100", null)] });
    const c = await mod.choisirLeLot({ limit: 50 }, MAINTENANT);
    controle("(4) une transaction SANS numero chez Hektor (ou absente du registre) n'est pas visee -- R3 ne la jugerait pas",
      c.lot.length === 0 && c.sans_registre.sort().join(",") === "1,2", JSON.stringify(c));
  }
  {
    monter({ lignes: [L(1, "a"), L(2, "b"), L(3, "c")], registres: [R(1, "vente", "300"), R(2, "vente", "100"), R(3, "vente", "200")] });
    const c = await mod.choisirLeLot({ limit: 2 }, MAINTENANT);
    controle("(5) le plafond : 2 posees (les plus petits numeros), la 3e reportee et NOMMEE",
      c.lot.map((a) => a.annonce).join(",") === "100,200" && c.reportees.join(",") === "300", JSON.stringify(c));
  }
  {
    // (6-7) main() EN VRAI, par un processus fils : le module ne lance main() que s'il est le programme
    //   principal. Le faux reseau est prechage (-r) depuis un fichier temporaire ; il note chaque POST.
    const cp = require("child_process");
    const os = require("os");
    const path = require("path");
    const faux = path.join(os.tmpdir(), "faux_reseau_rattrapage_carnet.js");
    fs.writeFileSync(faux, `
      const posts = [];
      const R = { app_affaire_id: 1001395, kind: "vente", hektor_annonce_id: "24113", app_dossier_id: 1068399, hektor_affaire_id: "23358" };
      global.fetch = async (u, o = {}) => {
        const c = String(u).split("/rest/v1/")[1] || "";
        const m = (o.method || "GET").toUpperCase();
        if (m === "POST") { posts.push(JSON.parse(o.body)); return { ok: true, status: 201, json: async () => null, text: async () => "" }; }
        const r = c.startsWith("app_affaire_champ_app")
          ? [{ app_affaire_id: 1001395, champ: "notaire_id", etat: "en_attente", constate_le: "2026-10-23T17:41:54+00:00" }]
          : c.startsWith("app_affaire_ledger") ? [R] : [];
        return { ok: true, status: 200, json: async () => r, text: async () => "" };
      };
      process.on("exit", () => { process.stderr.write("POSTS=" + JSON.stringify(posts)); });
    `);
    const lancer = (argv, interrupteur) => cp.spawnSync(process.execPath,
      ["-r", faux, path.join(__dirname, "enqueue_rattrapage_carnet.js"), ...argv],
      { encoding: "utf8", env: { ...process.env, APP_AFFAIRE_R3_RATTRAPAGE: interrupteur } });
    const postsDe = (r) => { const m = String(r.stderr || "").match(/POSTS=(.*)$/m); return m ? JSON.parse(m[1]) : null; };
    const blanc = lancer([], "1");
    const eteint = lancer(["--pousser"], "");
    const allume = lancer(["--pousser"], "1");
    fs.unlinkSync(faux);
    const p1 = postsDe(blanc), p2 = postsDe(eteint), p3 = postsDe(allume);
    controle("(6) en blanc (meme interrupteur allume) : sortie 0, AUCUNE ecriture",
      blanc.status === 0 && Array.isArray(p1) && p1.length === 0, blanc.stdout + blanc.stderr);
    controle("(7a) --pousser, interrupteur ETEINT : sortie 0, AUCUNE ecriture, et il le dit",
      eteint.status === 0 && Array.isArray(p2) && p2.length === 0 && /ETEINT/.test(eteint.stdout), eteint.stdout + eteint.stderr);
    const t = p3 && p3[0] && p3[0][0];
    controle("(7b) --pousser, interrupteur ALLUME : UN travail refresh_console_data « carnet seul » pour 24113",
      allume.status === 0 && Array.isArray(p3) && p3.length === 1 && p3[0].length === 1 && t.job_type === "refresh_console_data"
      && t.hektor_annonce_id === "24113" && t.app_dossier_id === 1068399 && t.payload_json.carnet_seul === true
      && t.payload_json.reason === "rattrapage_carnet" && t.priority === 200, allume.stdout + allume.stderr);
  }

  console.log(echecs.length ? `\n${echecs.length} controle(s) en echec.` : "\nTous les controles sont verts.");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log(`\nL'essai n'a pas pu mesurer : ${e && e.stack ? e.stack : e}`); process.exit(2); });
