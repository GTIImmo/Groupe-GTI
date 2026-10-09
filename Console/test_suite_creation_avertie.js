// LA SUITE DE LA CREATION A RATE : EST-CE QUE QUELQU'UN EST PREVENU ?
//                                                     chantier 4, point 4a, 09/10/2026
// Jusqu'ici : NON. La creation d'une annonce fait trois choses (creer chez Hektor,
// remplir la fiche, rattacher le mandant) ; les deux dernieres sont attrapees par un
// `catch` et le travail CONTINUE -- il finit donc « done ». Or l'avertissement du
// worker n'existe que dans le `catch` du lanceur : un travail qui ne tombe pas ne
// previent personne. Mesure du 09/10 sur 79 creations : 3 fiches perdues EN ENTIER
// (07/06, 07/07, 08/07) et 1 faux negatif de mandant (28/08), zero avertissement.
//
// ⚠ CE QUE CE TEST PROTEGE SURTOUT, C'EST LE CHOIX DE NE PAS FAIRE TOMBER LE TRAVAIL :
//   l'annonce EXISTE deja chez Hektor. Faire tomber le travail afficherait « Erreur de
//   creation » sur une annonce bien creee (enveloppe ...WithProvisional), et rejouer une
//   creation la DOUBLERAIT (regle C.4-bis). On n'ajoute donc QUE la parole.
//
// Il fait tourner LES VRAIES fonctions du worker avec un faux Supabase.
// N'APPELLE NI HEKTOR NI SUPABASE. N'ECRIT AUCUN FICHIER. N'ECRIT RIEN EN PRODUCTION.

const fs = require("fs");
const path = require("path");

const WORKER = path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(WORKER, "utf8");

let echecs = 0;
function controle(nom, ok, detail) {
  console.log(`  ${ok ? "OK " : "KO "} ${nom}${ok ? "" : `  -- ${detail}`}`);
  if (!ok) echecs += 1;
}

// Decoupe un bloc du worker : du marqueur jusqu'a la premiere accolade en colonne 0.
function tranche(debutMarque, fermeture = "\n}") {
  const i = src.indexOf(debutMarque);
  if (i < 0) return null;
  const f = src.indexOf(fermeture, i);
  return f < 0 ? null : src.slice(i, f + fermeture.length);
}

const blocLibelles = tranche("const SUITE_CREATION_LIBELLES = {", "\n};");
const blocBilan = tranche("function bilanSuiteCreationIncomplete(");
const blocAvertir = tranche("async function avertirSuiteCreationIncompleteBestEffort(");

(async () => {
  if (!blocLibelles || !blocBilan || !blocAvertir) {
    controle("(0) les trois blocs de 4a sont dans le worker", false,
      `libelles=${!!blocLibelles} bilan=${!!blocBilan} avertir=${!!blocAvertir}`);
    process.exit(1);
  }
  controle("(0) les trois blocs de 4a sont dans le worker", true);

  // ── le faux monde : on capture, on n'ecrit rien ────────────────────────────
  let journal = [];
  let envois = [];
  let supabaseJette = false;

  function fabrique(interrupteur, emailRendu) {
    journal = []; envois = [];
    const faux = {
      ALERTE_SUITE_CREATION: interrupteur,
      cleanString: (v) => String(v == null ? "" : v).trim(),
      logJob: async (jobId, step, status, message, payload) => {
        journal.push({ jobId, step, status, message, payload });
      },
      resolveJobFailureRecipient: async () => emailRendu,
      supabaseRequest: async (chemin, options) => {
        if (supabaseJette) throw new Error("Supabase indisponible");
        envois.push({ chemin, corps: JSON.parse(options.body), prefer: options.prefer });
      },
    };
    // eslint-disable-next-line no-new-func
    return new Function(...Object.keys(faux),
      `${blocLibelles};\n${blocBilan}\n${blocAvertir}\n return avertirSuiteCreationIncompleteBestEffort;`,
    )(...Object.values(faux));
  }

  const job = { id: "job-uuid-4a", job_type: "create_hektor_draft_annonce", app_dossier_id: 904321 };
  const payload = { title: "Maison 5 pieces lumineuse", numero_dossier: "VA2501" };
  const base = { hektor_annonce_id: "62657", folder_number: "VA2501" };
  const tousOk = {
    ...base,
    initial_fields_update: { status: "updated" },
    initial_mandant_links: { status: "linked", links: [] },
    initial_mandant_create: { status: "skipped", reason: "not_requested" },
  };

  // ── (1) TOUT VA BIEN : PAS UN MOT, PAS UNE REQUETE ────────────────────────
  let avertir = fabrique(true, "nego@gti-immobilier.fr");
  await avertir(job, payload, tousOk);
  controle("(1) creation complete -> aucun avertissement, aucune requete",
    journal.length === 0 && envois.length === 0,
    `journal=${journal.length} envois=${envois.length}`);

  // ── (2) LES CHAMPS ONT RATE : LE CAS REEL DU 08/07 ────────────────────────
  avertir = fabrique(true, "nego@gti-immobilier.fr");
  await avertir(job, payload, {
    ...tousOk,
    initial_fields_update: { status: "error", error: "Date Hektor invalide pour DATE_DISPO: format attendu jj-mm-aaaa" },
  });
  controle("(2a) une ligne de journal resume le cas",
    journal.length === 1 && journal[0].step === "suite_creation_incomplete" && journal[0].status === "error",
    JSON.stringify(journal));
  controle("(2b) le journal nomme le manque et garde le motif technique",
    journal[0].payload.manques.join(",") === "champs"
    && String(journal[0].payload.details.champs.error).includes("DATE_DISPO"),
    JSON.stringify(journal[0].payload));
  controle("(2c) un seul message part, dans app_notification",
    envois.length === 1 && envois[0].chemin === "app_notification",
    JSON.stringify(envois.map((e) => e.chemin)));
  const msg = envois[0].corps[0];
  controle("(2d) au bon negociateur, sous un type a lui",
    msg.negociateur_email === "nego@gti-immobilier.fr" && msg.type === "creation_suite_incomplete",
    JSON.stringify({ email: msg.negociateur_email, type: msg.type }));
  controle("(2e) le texte dit d'abord CE QUI EST ACQUIS, puis ce qui manque",
    msg.body.includes("est bien creee dans Hektor")
    && msg.body.includes("les champs saisis a la creation n'ont pas ete enregistres"),
    msg.body);
  controle("(2f) il porte le repere du bien (numero de dossier)",
    msg.body.includes("VA2501"), msg.body);
  controle("(2g) il est rattache au dossier, pour l'index des non-lues",
    msg.app_dossier_id === 904321, String(msg.app_dossier_id));
  controle("(2h) les doublons non lus sont ignores, jamais une erreur",
    String(envois[0].prefer).includes("resolution=ignore-duplicates"), String(envois[0].prefer));
  controle("(2i) RIEN n'est ecrit vers app_console_job : le travail reste « done »",
    envois.every((e) => !String(e.chemin).startsWith("app_console_job")),
    JSON.stringify(envois.map((e) => e.chemin)));

  // ── (3) « partial » COMPTE AUSSI (jamais arrive sur 79, mais c'est un trou) ─
  avertir = fabrique(true, "nego@gti-immobilier.fr");
  await avertir(job, payload, { ...tousOk, initial_fields_update: { status: "partial" } });
  controle("(3) des champs ecrits et d'autres non -> on previent quand meme",
    envois.length === 1 && journal.length === 1, `envois=${envois.length}`);

  // ── (4) LE MANDANT CREE A LA CREATION ─────────────────────────────────────
  avertir = fabrique(true, "nego@gti-immobilier.fr");
  await avertir(job, payload, {
    ...tousOk,
    initial_mandant_create: { status: "error", error: "Creation contact OK mais association mandant non confirmee" },
  });
  controle("(4) mandant cree non rattache -> message dedie",
    envois.length === 1
    && envois[0].corps[0].body.includes("le mandant saisi a la creation n'a pas ete rattache"),
    envois.length ? envois[0].corps[0].body : "(rien)");

  // ── (5) LE MANDANT EXISTANT : LE CAS REEL DU 28/08 ────────────────────────
  avertir = fabrique(true, "nego@gti-immobilier.fr");
  await avertir(job, payload, {
    ...base,
    initial_fields_update: { status: "updated" },
    initial_mandant_create: { status: "skipped" },
    initial_mandant_links: {
      status: "partial_error",
      links: [
        { status: "linked", hektor_contact_id: "603952" },
        { status: "error", hektor_contact_id: "603953", error: "Association mandant non confirmee pour contact 603953" },
      ],
    },
  });
  controle("(5a) le lien rate previent",
    envois.length === 1
    && envois[0].corps[0].body.includes("le mandant choisi n'a pas pu etre rattache"),
    envois.length ? envois[0].corps[0].body : "(rien)");
  controle("(5b) le journal retient LEQUEL des contacts a rate, pas le lot",
    journal[0].payload.details.mandant_lie.erreurs.length === 1
    && journal[0].payload.details.mandant_lie.erreurs[0].hektor_contact_id === "603953",
    JSON.stringify(journal[0].payload.details.mandant_lie));

  // ── (6) DEUX MANQUES A LA FOIS : UN SEUL MESSAGE ──────────────────────────
  avertir = fabrique(true, "nego@gti-immobilier.fr");
  await avertir(job, payload, {
    ...tousOk,
    initial_fields_update: { status: "error", error: "boum" },
    initial_mandant_create: { status: "error", error: "boum" },
  });
  controle("(6) deux manques -> UN message qui les porte tous les deux",
    envois.length === 1
    && envois[0].corps[0].body.includes("champs saisis")
    && envois[0].corps[0].body.includes("mandant saisi")
    && envois[0].corps[0].payload.manques.length === 2,
    envois.length ? envois[0].corps[0].body : "(rien)");

  // ── (7) L'INTERRUPTEUR ETEINT : LE RETOUR ARRIERE ─────────────────────────
  avertir = fabrique(false, "nego@gti-immobilier.fr");
  await avertir(job, payload, { ...tousOk, initial_fields_update: { status: "error", error: "boum" } });
  controle("(7) interrupteur eteint -> rien du tout (retour arriere sans redeploiement)",
    journal.length === 0 && envois.length === 0,
    `journal=${journal.length} envois=${envois.length}`);

  // ── (8) AUCUN DESTINATAIRE : LA TRACE RESTE ───────────────────────────────
  avertir = fabrique(true, null);
  await avertir(job, payload, { ...tousOk, initial_fields_update: { status: "error", error: "boum" } });
  controle("(8) pas de destinataire -> aucun message, mais la trace est au journal",
    journal.length === 1 && envois.length === 0,
    `journal=${journal.length} envois=${envois.length}`);

  // ── (9) AVERTIR NE DOIT JAMAIS FAIRE TOMBER LA CREATION ───────────────────
  supabaseJette = true;
  avertir = fabrique(true, "nego@gti-immobilier.fr");
  let aJete = false;
  try {
    await avertir(job, payload, { ...tousOk, initial_fields_update: { status: "error", error: "boum" } });
  } catch (_) {
    aJete = true;
  }
  supabaseJette = false;
  controle("(9) si l'avertissement casse, la creation reussie n'est PAS mise en echec",
    aJete === false, "la fonction a jete");

  console.log(echecs === 0 ? "\nTOUT EST VERT" : `\n${echecs} CONTROLE(S) EN ECHEC`);
  process.exit(echecs === 0 ? 0 : 1);
})();
