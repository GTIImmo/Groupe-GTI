#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════
// L4-b' — LA PORTE EST-ELLE FERMEE ?                            22/09/2026
// ═══════════════════════════════════════════════════════════════════════════
// N'APPELLE NI HEKTOR NI SUPABASE. Il lit le source du worker et verifie que
// les neuf sortants trouves par l'audit du 22/09 passent bien par la porte.
//
// POURQUOI UN CONTROLE SUR LE SOURCE ET PAS UN ESSAI REEL. Ces chemins
// n'existent qu'au milieu d'un travail complet (un compromis, un mandat) et
// exigent une session Hektor. Un essai reel couterait une ecriture chez Hektor
// a chaque passage. Le defaut, lui, est TEXTUEL : un numero brut au lieu d'un
// numero traduit. Un controle textuel le voit, et il se rejoue gratuitement.
//
// ⚠ CE QU'IL NE PROUVE PAS : que la traduction rende la bonne valeur. Ca, seul
//   un contact ne dans l'app et utilise comme mandant ou acquereur le dira --
//   c'est l'essai a faire quand C.9 existera.
//
//     node Console/test_porte_contacts.js
// ═══════════════════════════════════════════════════════════════════════════
"use strict";

const fs = require("fs");
const path = require("path");

const FICHIER = path.join(__dirname, "console_job_worker.js");
const src = fs.readFileSync(FICHIER, "utf8");

const controles = [
  {
    nom: "la porte existe, et elle connait la plage de l'app",
    ok: () => /async function cibleHektorContact\(/.test(src)
           && /Number\(brut\) >= PLAGE_NUMEROS_APP/.test(src),
  },
  {
    // C-1, 23/09/2026. LE CONTROLE QUI MANQUAIT. L'ancienne version levait des
    // que l'identite etait dans la plage de l'app, AVANT de lire la cible. Le
    // controle d'au-dessus ne voyait rien : les deux versions contiennent la
    // meme comparaison. Ce n'est pas sa PRESENCE qui compte, c'est sa PLACE.
    //
    // Tant qu'aucun contact n'etait dans la plage, le defaut etait invisible.
    // Le jour de la bascule il aurait arrete TOUS les envois vers Hektor.
    nom: "C-1 la porte LIT la cible AVANT de refuser",
    ok: () => {
      const debut = src.indexOf("async function cibleHektorContact(");
      const fin = src.indexOf("async function ciblesHektorContacts(");
      if (debut < 0 || fin < 0 || fin < debut) return false;
      const corps = src.slice(debut, fin);
      const lecture = corps.indexOf("select=hektor_target_id");
      const refus = corps.indexOf("pas encore cree chez Hektor");
      return lecture > 0 && refus > 0 && lecture < refus;
    },
  },
  {
    // Le repli de panne : Supabase muet ne doit pas nous faire envoyer un
    // numero de l'app a Hektor. Avant C-1 ce cas n'existait pas (on levait
    // plus haut) ; maintenant il existe, et il doit refuser.
    nom: "C-1 Supabase muet ne fait JAMAIS viser un numero de l'app",
    ok: () => /if \(!dansLaPlageDeLApp\) return brut;/.test(src)
           && /cible Hektor illisible \(Supabase muet\)/.test(src),
  },
  {
    nom: "la porte existe aussi pour une LISTE",
    ok: () => /async function ciblesHektorContacts\(/.test(src),
  },
  {
    nom: "la porte des listes REFUSE le lot si un contact manque",
    ok: () => /pas encore cree\(s\) chez Hektor/.test(src),
  },
  {
    nom: "les acquereurs d'un compromis/vente sont traduits",
    ok: () => /const acquereursVoulus = await ciblesHektorContacts\(acquereursDemandes/.test(src),
  },
  {
    nom: "l'acquereur d'un changement de statut est traduit",
    ok: () => /submit_hektor_transaction_status/.test(src)
           && /appendIfValue\(body, "acquereurs\[\]", acquereurCible\)/.test(src),
  },
  {
    nom: "les mandants d'un mandat sont traduits",
    ok: () => /await ciblesHektorContacts\(mandat\.mandantContactIds/.test(src),
  },
  {
    nom: "les mandants d'une creation d'annonce sont traduits",
    // ⚠ On vise la VARIABLE, pas un voisinage de texte : le premier controle
    //   cherchait « hektor_mandant_link_initial » puis cibleHektorContact dans
    //   les 400 caracteres suivants, et tombait sur une autre occurrence du
    //   libelle. Un controle vague rend un faux echec -- aussi genant qu'un
    //   faux succes, parce qu'on finit par ne plus le croire.
    ok: () => /const cibleMandant = await cibleHektorContact\(/.test(src)
           && /linkHektorMandantContact\(job, String\(created\.id\), cibleMandant/.test(src),
  },
  {
    nom: "la qualification utilise le numero TRADUIT (il etait jete)",
    ok: () => /const \{ contactId: cibleQualif, context \} =/.test(src)
           && /listerCriteresBestEffort\(cibleQualif\)/.test(src),
  },
  {
    nom: "l'archivage de qualification utilise le numero TRADUIT",
    ok: () => /const \{ contactId: cibleArchive \} =/.test(src)
           && /archiveHektorContactSearch\(job, cibleArchive/.test(src),
  },
  // ── L4-c ② : IDENTITE ET CIBLE NE SE CONFONDENT PLUS ─────────────────────
  // Le motif fautif etait `contactId = await cibleHektorContact(contactId)` :
  // il ECRASAIT l'identite par la cible, et le resultat servait ensuite aux
  // DEUX usages -- viser Hektor, et interroger NOS tables. Invisible tant que
  // les deux valeurs sont egales ; faux des que l'identite devient celle de
  // l'app.
  {
    nom: "L4-c ② plus aucun ecrasement de l'identite par la cible",
    // ⚠ Le « (?<!const ) » est indispensable : sans lui, l'expression attrapait
    //   aussi `const contactId = await cibleHektorContact(...)`, qui est
    //   justement la forme CORRIGEE. Un controle qui accuse la bonne reponse
    //   se fait desactiver au bout de trois fois -- deuxieme fois aujourd'hui.
    ok: () => !/(?<!const )\bcontactId = await cibleHektorContact\(/.test(src)
           && !/(?<!const )\bhektorContactId = await cibleHektorContact\(/.test(src),
  },
  {
    nom: "L4-c ② ensureContactSearchExecution rend LES DEUX numeros",
    ok: () => /return \{ contactId, identite, contextPayload, context \}/.test(src)
           && /loadContactExecutionContext\(identite\)/.test(src),
  },
  {
    nom: "L4-c ② les bannettes et le garde-fou visent l'identite",
    ok: () => /markContactPendingConflict\(identite\)/.test(src)
           && /clearContactPending\(identite\)/.test(src)
           && /markSearchPendingConflict\(identite, pendingIndex\)/.test(src)
           && /clearSearchPending\(identite, pendingIndex\)/.test(src),
  },
  {
    nom: "L4-c ② le menage de suppression vise l'identite",
    ok: () => /cleanupSupabaseContactRows\(numeroDemande\)/.test(src)
           && /runDeletedContactLocalCleanup\(job, numeroDemande\)/.test(src)
           && /loadSupabaseContactRelationsForCleanup\(numeroDemande\)/.test(src),
  },
  {
    nom: "L4-c ② la ligne provisoire de relation vise l'identite",
    ok: () => /lierRelationProvisoire\(jetonRelation, identite\)/.test(src),
  },
  {
    // LE CONTROLE LE PLUS IMPORTANT. La version du 21/09 retirait en silence
    // les numeros de la plage de l'app de la liste des mandants : le mandat
    // partait ampute, et Hektor l'acceptait sans un mot.
    nom: "AUCUN filtre ne jette plus un numero d'app en silence",
    ok: () => {
      const occurrences = src.split("PLAGE_NUMEROS_APP").length - 1;
      // 2 seulement : la constante, et le test DANS la porte.
      return occurrences === 2;
    },
  },
];

let echecs = 0;
for (const c of controles) {
  const vert = c.ok();
  if (!vert) echecs += 1;
  console.log(`${vert ? "  OK  " : "ECHEC "} ${c.nom}`);
}

console.log("");
if (echecs) {
  console.log(`${echecs} controle(s) en echec -- la porte a une fuite.`);
  process.exit(1);
}
console.log(`${controles.length} controles passes : aucun numero d'app ne peut partir chez Hektor.`);
