// ⑧ TYPES, ETAPE 2 -- LE TYPE APRES UNE ECRITURE DU WORKER, essai hors ligne.      27/10/2026
//
// Le worker ecrit dans nos registres SANS passer par les 6 portes de la base : apres chacune de
// ces ecritures, il doit redemander le calcul du type (note des types, §47).
// CE QU'ON EPROUVE, sur LE CODE REEL (fonctions decoupees dans le worker, montees dans un bac a
// sable avec une FAUSSE BASE qui note les appels -- meme technique que test_garde_copropriete.js) :
//   (1) la preuve d'abord : les 5 ecritures appellent le calcul
//   (2) retrait defait -> calcul du bien, APRES la remise du lien
//   (3) rattachement defait -> calcul du bien ; TEMOIN INVERSE : rien defait -> pas d'appel
//   (4) suppression defaite -> calcul du bien de la transaction relue
//   (5) liste retenue par Hektor -> les parties d'AVANT sont recalculees aussi (l'ecarte perd son role)
//   (6) TEMOIN INVERSE : un report sans personnes -> ni lecture ni calcul
//   (7) suppression confirmee -> les parties lues AVANT l'effacement sont recalculees
//   (8) la base refuse, ou le journal tombe -> JAMAIS d'exception, et c'est ecrit
//   (9) MUTANT : on retire l'appel du retrait defait -> le controle (2) rougit
//
//     node Console/test_type_apres_ecriture_worker.js
//     sortie 0 = tout vert · 1 = un controle en echec · 2 = n'a pas pu mesurer

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const echecs = [];

function controle(nom, ok, detail) {
  console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`);
  if (!ok) echecs.push(nom);
}

function tranche(texte, debut) {
  const i = texte.indexOf(debut);
  if (i < 0) return null;
  const f = texte.indexOf("\n}", i);
  return f < 0 ? null : texte.slice(i, f + 2);
}

const NOMS = {
  journal: "async function journalDuType(",
  bien: "async function recalculerTypeDuBien(",
  parties: "async function contactsDeLAffaire(",
  contacts: "async function recalculerTypeDesContacts(",
  retrait: "async function annulerRetraitOptimiste(",
  rattachement: "async function annulerRattachementOptimiste(",
  filet: "function leFiletVaRejouer(",
  restaurer: "async function restaurerEtatAffaire(",
  reporter: "async function reporterAuRegistre(",
  retirer: "async function retirerAffaireDuRegistre(",
  clean: "function cleanString(",
};

function decouper(texte) {
  const m = {};
  for (const [k, debut] of Object.entries(NOMS)) m[k] = tranche(texte, debut);
  return m;
}

const morceaux = decouper(src);
const manquants = Object.keys(morceaux).filter((k) => !morceaux[k]);
const branchements = {
  retrait: /recalculerTypeDuBien\(job, annonceId, "retrait_annule"\)/,
  rattachement: /recalculerTypeDuBien\(job, annonceId, "rattachement_annule"\)/,
  restaurer: /recalculerTypeDuBien\(job, majes\[0\]/,
  reporter: /recalculerTypeDesContacts\(job, \[\.\.\.partiesAvant/,
  retirer: /recalculerTypeDesContacts\(job, partiesAvant, "suppression_confirmee"\)/,
};
const nonBranches = Object.keys(branchements).filter((k) => !branchements[k].test(morceaux[k] || ""));
controle("(1) LA PREUVE D'ABORD : les 5 ecritures du worker appellent le calcul du type",
  !manquants.length && !nonBranches.length,
  manquants.length ? `manquent : ${manquants.join(", ")}` : `non branchees : ${nonBranches.join(", ")}`);
if (manquants.length) {
  console.log("\n⛔ Une piece manque : les controles suivants ne prouveraient RIEN. On s'arrete.");
  process.exit(2);
}

// ── le bac a sable : une fausse base qui note chaque appel, dans l'ordre ──
function monter(m, base) {
  const appels = [];
  const journal = [];
  const bac = {
    appels, journal, console, Number, String, Boolean, Array, Set, Object, JSON, Date, Math, encodeURIComponent,
    REGISTRE_PAR_HEKTOR: { prix: ["montant"] },
    GARDER_NOS_NUMEROS_A_LA_RELECTURE: false,
    GESTES_REJOUES_PAR_LE_FILET: new Set(),
    FILET_MAX_TENTATIVES: 5,
    FILET_FRAICHEUR_MS: 86400000,
    restaurerStatutRedescendu: async () => {},
    tableDeNosNumeros: async () => new Map(),
    poserNosNumerosDansLaListe: (l) => l,
    logJob: async (id, step, status, message, charge) => {
      if (base.journalCasse && step === "type_des_contacts") throw new Error("journal en panne");
      journal.push({ step, status, message, charge });
    },
    supabaseRequest: async (chemin, options = {}) => {
      const methode = options.method || "GET";
      const corps = options.body ? JSON.parse(options.body) : null;
      appels.push({ chemin, methode, corps });
      if (chemin.startsWith("rpc/")) {
        if (base.rpcCasse) throw new Error("Supabase 500");
        return base.rpcRend ?? 1;
      }
      if (chemin.startsWith("app_affaire_partie?") && methode === "GET") {
        const lectures = appels.filter((a) => a.chemin.startsWith("app_affaire_partie?")).length;
        return lectures === 1 ? base.partiesAvant || [] : base.partiesApres || [];
      }
      if (chemin.startsWith("app_relation?") && methode === "PATCH") return base.relationsTouchees || [];
      if (chemin.startsWith("app_affaire_ledger?") && methode === "PATCH") return base.ledgerTouche || [];
      return [];
    },
  };
  vm.createContext(bac);
  vm.runInContext(Object.values(m).join("\n\n")
    + "\nthis.f = { recalculerTypeDuBien, recalculerTypeDesContacts, annulerRetraitOptimiste,"
    + " annulerRattachementOptimiste, restaurerEtatAffaire, reporterAuRegistre, retirerAffaireDuRegistre };", bac);
  return bac;
}

const rpc = (bac) => bac.appels.filter((a) => a.chemin.startsWith("rpc/"));
const job = { id: "job-essai", hektor_annonce_id: "62774", requested_at: new Date().toISOString() };

async function essaiRetrait(m) {
  const bac = monter(m, {});
  const r = await bac.f.annulerRetraitOptimiste(job, "20000008", "62774", "refus Hektor");
  const i = bac.appels.findIndex((a) => a.chemin.startsWith("app_relation?") && a.methode === "PATCH");
  const j = bac.appels.findIndex((a) => a.chemin === "rpc/app_recalculer_type_du_bien");
  return { r, i, j, corps: j >= 0 ? bac.appels[j].corps : null };
}

(async () => {
  // (2)
  {
    const { r, i, j, corps } = await essaiRetrait(morceaux);
    controle("(2) retrait defait -> calcul du type du bien 62774, APRES la remise du lien",
      r.annule === true && i >= 0 && j > i && corps && corps.p_hektor_annonce_id === "62774",
      JSON.stringify({ r, i, j, corps }));
  }
  // (3) + temoin inverse
  {
    const bac = monter(morceaux, { relationsTouchees: [{ relation_key: "k" }] });
    await bac.f.annulerRattachementOptimiste(job, "62774", "604831", "refus Hektor");
    const bac0 = monter(morceaux, { relationsTouchees: [] });
    await bac0.f.annulerRattachementOptimiste(job, "62774", "604831", "refus Hektor");
    controle("(3) rattachement defait -> calcul du bien ; TEMOIN INVERSE : aucune ligne defaite -> aucun calcul",
      rpc(bac).length === 1 && rpc(bac)[0].corps.p_hektor_annonce_id === "62774" && rpc(bac0).length === 0,
      `avec ligne : ${rpc(bac).length} appel(s) ; sans : ${rpc(bac0).length}`);
  }
  // (4)
  {
    const bac = monter(morceaux, { ledgerTouche: [{ app_affaire_id: 77, hektor_annonce_id: 63131 }] });
    await bac.f.restaurerEtatAffaire({ ...job, job_type: "delete_hektor_vente" }, "hektor_vente_delete",
      { app_affaire_id: 77, geste: "supprimer" });
    const a = rpc(bac);
    controle("(4) suppression defaite -> calcul du bien de la transaction RELUE (63131, pas celui du travail)",
      a.length === 1 && a[0].chemin === "rpc/app_recalculer_type_du_bien" && a[0].corps.p_hektor_annonce_id === "63131",
      JSON.stringify(a));
  }
  // (5)
  {
    const bac = monter(morceaux, { partiesAvant: [{ app_contact_id_texte: "10354352" }, { app_contact_id_texte: "20000008" }],
      partiesApres: [{ app_contact_id_texte: "10354352" }] });
    await bac.f.reporterAuRegistre(job, 77, { acquereurs: [{ id: "123" }] });
    const iPatch = bac.appels.findIndex((a) => a.chemin.startsWith("app_affaire_ledger?") && a.methode === "PATCH");
    const lectures = bac.appels.map((a, k) => (a.chemin.startsWith("app_affaire_partie?") ? k : -1)).filter((k) => k >= 0);
    const a = rpc(bac);
    const liste = a.length ? a[0].corps.p_contacts : [];
    controle("(5) liste retenue par Hektor -> parties lues AVANT et APRES, l'acquereur ecarte (20000008) recalcule aussi",
      a.length === 1 && a[0].chemin === "rpc/app_recalculer_type_contacts" && lectures.length === 2
        && lectures[0] < iPatch && lectures[1] > iPatch
        && liste.includes("20000008") && liste.includes("10354352") && liste.length === 2,
      JSON.stringify({ lectures, iPatch, liste }));
  }
  // (6)
  {
    const bac = monter(morceaux, {});
    await bac.f.reporterAuRegistre(job, 77, { prix: "250000" });
    controle("(6) TEMOIN INVERSE : un report sans personnes (le prix seul) -> ni lecture des parties ni calcul",
      rpc(bac).length === 0 && !bac.appels.some((a) => a.chemin.startsWith("app_affaire_partie?"))
        && bac.appels.some((a) => a.chemin.startsWith("app_affaire_ledger?") && a.methode === "PATCH"),
      JSON.stringify(bac.appels.map((a) => a.chemin.slice(0, 40))));
  }
  // (7)
  {
    const bac = monter(morceaux, { partiesAvant: [{ app_contact_id_texte: "20000008" }] });
    await bac.f.retirerAffaireDuRegistre(job, { app_affaire_id: 77 }, "preuve", "vente", "4242");
    const iDel = bac.appels.findIndex((a) => a.chemin.startsWith("app_affaire_ledger?") && a.methode === "DELETE");
    const iLu = bac.appels.findIndex((a) => a.chemin.startsWith("app_affaire_partie?"));
    const a = rpc(bac);
    controle("(7) suppression confirmee -> parties lues AVANT l'effacement, puis recalculees",
      iLu >= 0 && iDel > iLu && a.length === 1 && a[0].corps.p_contacts.join() === "20000008"
        && bac.appels.indexOf(a[0]) > iDel,
      JSON.stringify({ iLu, iDel, a }));
  }
  // (8)
  {
    let jete = null;
    const bacs = [monter(morceaux, { rpcCasse: true }), monter(morceaux, { rpcCasse: true, journalCasse: true }),
      monter(morceaux, { rpcRend: -1 })];
    const resultats = [];
    for (const bac of bacs) {
      try {
        resultats.push(await bac.f.recalculerTypeDuBien(job, "62774", "essai"));
        resultats.push(await bac.f.recalculerTypeDesContacts(job, ["20000008"], "essai"));
      } catch (e) { jete = e; }
    }
    const erreursEcrites = bacs[0].journal.filter((l) => l.step === "type_des_contacts" && l.status === "error").length;
    const refusEcrit = bacs[2].journal.some((l) => l.step === "type_des_contacts" && l.status === "error");
    controle("(8) la base refuse, ou le journal tombe -> JAMAIS d'exception ; l'echec est ECRIT (et -1 = refus)",
      jete === null && resultats.every((r) => r && typeof r === "object") && erreursEcrites === 2 && refusEcrit
        && resultats[0].recalcule === false && resultats[4].recalcule === false,
      jete ? `exception : ${jete.message}` : JSON.stringify({ resultats, erreursEcrites, refusEcrit }));
  }
  // (9) MUTANT
  {
    const mutant = src.replace(/\n\s*await recalculerTypeDuBien\(job, annonceId, "retrait_annule"\);[^\n]*/, "");
    const mm = decouper(mutant);
    const { j } = await essaiRetrait(mm);
    controle("(9) MUTANT : l'appel du retrait defait retire -> le controle (2) le voit (aucun calcul)",
      mutant !== src && j === -1, mutant === src ? "le mutant n'a pas ete applique" : `calcul trouve en ${j}`);
  }

  console.log(echecs.length ? `\n${echecs.length} controle(s) en ECHEC` : "\nTOUT VERT (9/9)");
  process.exit(echecs.length ? 1 : 0);
})().catch((e) => { console.log("⛔ ESSAI INTERROMPU :", e && e.stack ? e.stack : e); process.exit(2); });
