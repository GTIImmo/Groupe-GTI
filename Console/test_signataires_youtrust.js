// A.2 LOT 4 -- les signataires Youtrust : prenom / nom (on n'invente jamais un prenom) et
// portable (code SMS seulement sur un mobile). Sur le CODE REEL du worker.         26/10/2026
// Cas tires de l'audit du 26/10 sur les 1 495 mandants des biens vivants : 301 fiches de couple
// « Mr./Mme » muettes, 4 societes, 49 fixes seuls, 10 portables etrangers.
//     node Console/test_signataires_youtrust.js     (0 = vert · 1 = un echec · 2 = pas pu mesurer)
const fs = require("fs");
const path = require("path");

const src = fs.readFileSync(path.join(__dirname, "console_job_worker.js"), "utf8");
const tranche = (d) => { const i = src.indexOf(d); return i < 0 ? null : src.slice(i, src.indexOf("\n}", i) + 2); };
const morceaux = ["function cleanString(", "function prenomNomSignataire(", "function portableE164("].map(tranche);
if (morceaux.some((m) => !m)) { console.log("ECHEC  fonctions introuvables dans le worker"); process.exit(2); }
// eslint-disable-next-line no-new-func
const { prenomNomSignataire, portableE164 } = new Function(`${morceaux.join("\n")}; return { prenomNomSignataire, portableE164 };`)();

const echecs = [];
const controle = (nom, ok, detail) => { console.log(`${ok ? "  OK  " : "ECHEC "} ${nom}${ok ? "" : " -- " + (detail || "")}`); if (!ok) echecs.push(nom); };
const pn = (p) => JSON.stringify(prenomNomSignataire(p));

controle("une personne : prenom + nom gardes tels quels", pn({ prenom: "Jean", nom: "DUPONT" }) === '{"prenom":"Jean","nom":"DUPONT"}', pn({ prenom: "Jean", nom: "DUPONT" }));
controle("nom complet d'UNE personne en deux mots : decoupe", pn({ nomComplet: "Jean DUPONT" }) === '{"prenom":"Jean","nom":"DUPONT"}', pn({ nomComplet: "Jean DUPONT" }));
controle("civilite ignoree : « M. Jean DUPONT »", pn({ nomComplet: "M. Jean DUPONT" }) === '{"prenom":"Jean","nom":"DUPONT"}', pn({ nomComplet: "M. Jean DUPONT" }));
controle("fiche de couple « M. et Mme DUPONT » : PAS de prenom invente", JSON.parse(pn({ nomComplet: "M. et Mme DUPONT" })).prenom === "", pn({ nomComplet: "M. et Mme DUPONT" }));
controle("fiche de couple « Mr./Mme DUPONT » : PAS de prenom invente", JSON.parse(pn({ nom: "Mr./Mme DUPONT" })).prenom === "", pn({ nom: "Mr./Mme DUPONT" }));
controle("un mot seul « DUPONT » : PAS de prenom invente (avant : prenom = nom)", JSON.parse(pn({ nom: "DUPONT" })).prenom === "", pn({ nom: "DUPONT" }));
controle("societe « SCI LES TILLEULS » sans representant : PAS de prenom", JSON.parse(pn({ nom: "SCI LES TILLEULS" })).prenom === "", pn({ nom: "SCI LES TILLEULS" }));
controle("prenom compose garde : « Marie-Claire DUPONT »", pn({ prenom: "Marie-Claire", nom: "DUPONT" }) === '{"prenom":"Marie-Claire","nom":"DUPONT"}');

controle("06 12 34 56 78 -> +33612345678", portableE164("06 12 34 56 78") === "+33612345678", portableE164("06 12 34 56 78"));
controle("07.12.34.56.78 -> +33712345678", portableE164("07.12.34.56.78") === "+33712345678", portableE164("07.12.34.56.78"));
controle("0033 6 12 34 56 78 -> +33612345678", portableE164("0033 6 12 34 56 78") === "+33612345678", portableE164("0033 6 12 34 56 78"));
controle("+33 6 12 34 56 78 garde", portableE164("+33 6 12 34 56 78") === "+33612345678", portableE164("+33 6 12 34 56 78"));
controle("fixe 04 77 12 34 56 -> null (code par e-mail, D16)", portableE164("04 77 12 34 56") === null, portableE164("04 77 12 34 56"));
controle("fixe +33 4 77 12 34 56 -> null", portableE164("+33 4 77 12 34 56") === null, portableE164("+33 4 77 12 34 56"));
controle("portable suisse +41 79 123 45 67 garde", portableE164("+41 79 123 45 67") === "+41791234567", portableE164("+41 79 123 45 67"));
controle("vide -> null", portableE164("") === null && portableE164(null) === null);

console.log(echecs.length ? `\n${echecs.length} controle(s) en echec` : "\nTOUT EST VERT");
process.exit(echecs.length ? 1 : 0);
