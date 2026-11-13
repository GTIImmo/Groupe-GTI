# Assistant IA — étape 2 : l'agent qui répond (audit et explication)

> **12/11/2026 · lecture seule** : rien n'a été écrit en base ni dans le code.
> Plan : `notice/PLAN_DEV_ACCUEIL_ASSISTANT_IA_2026-10-29.md` · cadrage : `notice/SPEC_ETAPE0_ASSISTANT_IA_2026-10-29.md` · étape 1 : `notice/ETAPE1_SOCLE_ASSISTANT_IA_2026-11-12.md`.
> ⭐ **L'objectif, dans les mots de Frédéric (12/11)** : « le but du développement final est que l'agent répond à n'importe quelle question avec périmètre etc... ».
> **Audit limité à LIRE** : l'étape 2 n'écrit rien. Les colonnes créer / modifier / supprimer du tableau sont celles de l'étape 3, **non mesurées ici**.
> ✅ **Les 3 questions du §7 sont répondues le 12/11.** ✅ **« Vas-y » le 12/11 → codé le 12/11, en local (§9).** En attente : ses accords pour la base et la mise en ligne.

## 1. Le verdict

- **La base sait déjà dire « qui voit quoi » pour les objets principaux.** Biens, contacts, recherches, rapprochements, relances, mandats, transactions et documents portent le périmètre dans leurs règles de lecture (RLS) : lecteur global, ou périmètre `reseau / agence / portefeuille`, ou « ses biens » pour les transactions, mandats et documents. Lire **avec le jeton de la personne** (ce que fait l'étape 1) suffit pour ces objets-là.
- ⛔ **Mais on ne peut pas laisser l'agent lire « n'importe quelle table » ni appeler « n'importe quelle fonction ».** Trois fuites sont mesurées :
  1. **~50 tables sont lisibles par tout compte connecté** (règle `true` ou « utilisateur actif »). Parmi elles : les notes et les conditions de transaction, les écarts de personnes, les affaires supprimées, **toutes les notifications**, les propositions, les statuts bien ↔ acquéreur. L'écran ne les lit qu'à travers un objet parent, ou les filtre après lecture.
  2. **20 des 24 fonctions de lecture que l'écran appelle** (rapprochements, relances, historiques, activité, propositions, photos, notifications d'un bien…) tournent avec les droits du propriétaire **sans vérifier l'appelant**. Les appeler, c'est sortir du périmètre. Seules les 4 du pilotage et du registre des transactions contrôlent.
  3. **15 tables n'ont aucune règle** et sont lisibles : toutes des **sauvegardes datées** (`…_avant_…`, `app_sauvegarde_…`), plus 4 tables du classeur et de chaînage. Et 2 vues de contrôle sans les droits du lecteur.
- **L'écran calcule beaucoup de choses en mémoire** : le statut d'un mandat (Actif / Vendu / Clos / Échu), tous les compteurs de mandats, la « dernière demande par bien », le registre des transactions (mois, agence, part), le pilotage (sans les annonces d'essai). Ce ne sont pas des colonnes : l'agent doit refaire **les mêmes calculs**, sinon il dira un autre chiffre que l'écran.

## 2. Les mesures

**Comptes** : 6 actifs (4 admins, 2 commerciaux), **tous au périmètre `reseau`**. Les périmètres `agence` et `portefeuille` existent dans les règles, personne ne les utilise aujourd'hui. Pour un commercial, la différence avec l'admin porte donc surtout sur les transactions, les mandats et les documents (« ses biens »), et sur les gestes.

**Objets lisibles** : 151 tables et 24 vues lisibles par `authenticated` ; `anon` ne lit rien. Les vues de lecture principales sont en `security_invoker` (elles appliquent la RLS du lecteur).

**Les limites de l'API de lecture** :
- délai de 8 s par requête pour un compte connecté ;
- jeton de session valable 1 h ;
- **pas de sommes ni de moyennes** par l'API (`db-aggregates` non activé) : seul le **compte** de lignes est possible ;
- plafond de lignes par lecture : réglage du projet, **non mesuré** (le code de l'écran parle de 1 000).

**Les colonnes** : `app_dossiers_current` 70, `app_registre_mandats_current` 74, `app_contacts_current` 50, `app_affaire_ledger` 49 (29 commentées), `app_mandat` 29 (13 commentées). Les vues de l'écran n'ont **aucun commentaire de colonne** : il faudra écrire nous-mêmes ce que veut dire chaque colonne utile, en français.

**Comment l'écran lit** (relevé dans `apps/hektor-v1/src/lib/api.ts`, 13 055 lignes) :
- les biens : la vue `app_dossiers_current`, plus les index des archives, de l'historique et des brouillons, fusionnés et triés en mémoire ;
- la fiche : `app_dossier_details_current` (un bloc JSON) ;
- les contacts : `app_contacts_current` — ⚠ `loadContactsPage` ignore son paramètre de périmètre (`api.ts:3616`), seule la RLS borne l'annuaire ;
- les relations : `app_contact_relations_current` ; les recherches : `app_contact_searches_current` ;
- rapprochements, relances, historiques : **uniquement par des fonctions** (celles du point 2 ci-dessus) ;
- mandats : `app_registre_mandats_current`, et le statut calculé en mémoire (`api.ts:75`, `93`) ;
- demandes : `app_diffusion_requests_current` lue **en entier**, filtrée en mémoire ;
- transactions : `app_affaire_ledger`, réordonnées sur la date effective de l'offre (`api.ts:2021`), et les notes ou conditions lues par `app_dossier_id` ;
- agenda : la route du backend `GET /google-workspace/calendar/events`, qui force l'agenda de la personne hors admin ;
- notifications : la table, filtrée par l'écran sur l'e-mail de la session ;
- comparables DVF : la fonction `app_dvf_comparables` (données publiques).

**Deux routes du backend lisent sans le périmètre** (vérifié dans le code) :
- `GET /emails/rapprochement/tracking` (`emails.py:306`) lit le suivi des e-mails **avec la clé de service**, pour n'importe quel contact, dès qu'on est connecté ;
- `GET /public/appointments/annonce/{id}/summary` (`appointments.py:70`) ne vérifie que la connexion.

Ce n'est pas le chantier de l'assistant : c'est noté au §8, et **l'agent ne les appellera pas**.

**La lenteur de l'étape 1** : 5,2 s avant le premier événement.
- Avant d'appeler l'IA, le serveur fait 8 allers-retours vers Supabase, l'un après l'autre.
- La base est à Londres (`eu-west-2`) ; la région du serveur Render n'est **pas mesurée**.
- Le journal ne garde aucune durée : il faudra les mesurer.

## 3. Le tableau objets × gestes (étape 2 : la colonne « lire »)

| | lire : d'où | périmètre par la base | à refaire comme l'écran |
|---|---|---|---|
| **annonce** | `app_dossiers_current` + index archives / historique / brouillons | ✅ RLS | fusion et tri ; statut « Estimation » exclu par défaut |
| **contact** | `app_contacts_current` | ✅ RLS | fiches de ménage masquées |
| **recherche** | `app_contact_searches_current` | ✅ RLS (par le contact) | — |
| **relation** | `app_contact_relations_current` | ✅ vue du lecteur | — |
| **rapprochement / relance** | tables `app_rapprochement`, `app_relance_rapprochement` | ✅ RLS | ⛔ jamais par les fonctions de l'écran |
| **transaction** | `app_affaire_ledger` | ✅ ses biens | date effective ; notes et conditions **seulement par l'affaire lue** |
| **mandat** | `app_mandat`, `app_registre_mandats_current` | ✅ ses biens / le registre | statut Actif / Vendu / Clos / Échu calculé |
| **document / photo** | `app_console_document`, `app_console_photo` | ✅ ses biens (documents) ; photos non mesuré | — |
| **RDV / visite** | route agenda du backend | ✅ garde du backend | événements supprimés retirés |

Créer, modifier, supprimer : **étape 3, non mesuré ici**.

## 4. Ce que je propose — un « lecteur » sur un catalogue d'objets, pas 14 fonctions figées

Pour « n'importe quelle question », 14 fonctions figées ne suffiront jamais : chaque nouvelle question demanderait du code. Je propose à la place :

1. **Un catalogue d'objets** (biens, contacts, recherches, rapprochements, relances, mandats, transactions, demandes, documents, notifications…). Chaque objet nomme :
   - sa source, uniquement une vue ou une table dont la RLS porte le périmètre (§3) ;
   - ses colonnes utiles, décrites en français ;
   - ses champs calculés, avec **les mêmes règles que l'écran**.
2. **Trois fonctions génériques pour l'agent** :
   - `decrire(objet)` : les colonnes et ce qu'elles veulent dire ;
   - `chercher(objet, filtres, colonnes, tri, limite)` ;
   - `compter(objet, filtres, regrouper_par)`.

   Elles lisent **avec le jeton de la personne** : le périmètre est appliqué par la base, sans que l'agent puisse le contourner. Les sommes et moyennes sont calculées par notre serveur sur les lignes lues, avec un plafond, et la réponse **dit** quand le plafond est atteint.
3. **Quelques fonctions métier** là où il faut une jointure ou un calcul : fiche complète d'un bien, fiche d'un contact, notes et conditions d'une transaction (lues **après** l'affaire), agenda (par la route existante), comparables DVF.
4. **Une liste blanche, jamais une liste noire** : un objet absent du catalogue ne se lit pas. Les sauvegardes, les tables du classeur, le journal, les réglages, les tables « lisibles par tous » et les 20 fonctions sans contrôle en sont **exclus**.
5. **Les consignes** : ton GTI, tutoiement, force de proposition. Toujours dire d'où vient un chiffre et sur combien de lignes. Ne jamais inventer. Demander de préciser quand c'est ambigu.
6. **La mesure des durées** de chaque tour au journal (sans texte), pour traiter la lenteur avec des chiffres.

**L'option écartée pour l'instant : laisser l'IA écrire du SQL.** C'est la plus puissante, avec des jointures et des sommes à volonté. Mais en SQL, l'agent pourrait lire les ~50 tables « lisibles par tous » et appeler les fonctions sans contrôle (les 20 ci-dessus, et plus largement les 38 du cadrage). Il faudrait un rôle et un schéma dédiés, rien que des vues sûres : c'est un chantier en soi, à rouvrir si le lecteur ne suffit pas.

## 5. Ce que ça touche

- **Code neuf seulement**, dans le backend : le catalogue, le lecteur, les consignes, les essais. Rien dans le front, le worker ou le run de nuit.
- Le serveur ne fait **que lire**, avec le jeton de la personne. Aucune clé de service pour une lecture d'objet.
- **Base** : rien d'obligatoire. Une seule option, à trancher (question 2) : une vue qui calcule le statut des mandats comme l'écran.
- L'interrupteur reste `admin` : seuls les admins y ont accès.

## 6. Comment on vérifiera

- **Hors ligne** :
  - chaque objet du catalogue lit avec le jeton ;
  - un objet hors catalogue est refusé ;
  - les champs calculés donnent le même résultat que les fonctions de l'écran, sur les mêmes lignes.
- **Les 30 questions témoins** du cadrage (§6 de la spécification), rejouées en réel avec un compte admin, réponse comparée à l'écran.
- **Les témoins de droits avec un compte commercial** : les ventes d'un collègue, les notes d'une transaction qui n'est pas sur ses biens. ⚠ Je n'ai la session d'aucun commercial (question 3).
- **Les témoins d'absence et d'ambiguïté** : pas d'invention, et une demande de précision.

## 7. Les questions pour Frédéric

1. **La forme** : le lecteur sur un catalogue d'objets (ma recommandation), plutôt que les 14 fonctions figées du 29/10 ou le SQL libre ?
   ✅ **Réponse de Frédéric, 12/11 : « oui »** (à la question reformulée : « une liste fermée de ce que l'assistant peut lire, et à l'intérieur il cherche librement »).
2. **Les calculs de l'écran** (statut des mandats, compteurs) : les recopier dans le serveur (deux copies de la même règle, risque d'écart), ou les poser **une fois** dans une vue de la base que l'écran pourra reprendre plus tard (un patch, avec ton accord) ?
   ✅ **Réponse de Frédéric, 12/11 : « B »** — le calcul est posé **une seule fois dans la base** (une vue, par un patch soumis à son accord), l'assistant s'en sert, l'écran pourra le reprendre plus tard. *(Question reformulée simplement avant sa réponse : A = recopier le calcul dans l'assistant, B = le poser une fois dans la base.)*
3. **La preuve des droits d'un commercial** : qui fait l'essai, et avec quel compte ? Je ne me connecte pas à la place de quelqu'un.
   ✅ **Réponse de Frédéric, 12/11 : « oui »** — un commercial fera l'essai avec son propre compte. ⚠ **La personne n'est pas nommée** : à lui demander au moment de la preuve en réel.

## 8. Trouvé en passant (NON traité, hors chantier)

- `GET /emails/rapprochement/tracking` rend le suivi des e-mails de **n'importe quel contact** à tout compte connecté (clé de service, `emails.py:306`).
- `GET /public/appointments/annonce/{id}/summary` ne vérifie que la connexion (`appointments.py:70`).
- 15 tables lisibles sans règle, dont 11 sauvegardes datées : à fermer ou à supprimer quand on fera le ménage.
- 20 fonctions de lecture de l'écran sans contrôle de l'appelant. Elles font **probablement partie** des 25 lectures sans contrôle comptées le 29/10 (non recoupé un par un) ; la décision du 29/10 (« Non, plus tard ») vaut pour la famille.
- `RapprochementMandat.tsx:269` demande 200 événements d'agenda, alors que le backend plafonne à 100 (non vérifié en réel).

## 9. Codé le 12/11 (en local) — ce qui existe et ce qui est prouvé

**Rien n'est posé en base, rien n'est en ligne, rien n'est commité.**

**Le statut des mandats posé une fois dans la base (décision « B »)** — `supabase/patch_assistant_ia_etape2_statut_mandat_2026-11-12.sql` + `_INVERSE` + `_REPETITION` :
- 4 fonctions de calcul pur (statut normalisé, date de fin valide, Actif / Vendu / Clos / Échu, En cours / Annulé) et la vue `app_v_mandat_statut` = le registre + `statut_mandat` + `etat_mandat`, avec les droits du lecteur.
- ⭐ **La preuve que la base dit comme l'écran** : `backend/tests/cas_statut_mandat_ecran.cjs` extrait les VRAIES fonctions de `api.ts` (pas une recopie), les fait tourner sur **4 080 cas** croisés, et la répétition compare. Vérification faite le 12/11 avec des fonctions **temporaires** (rien de public créé, transaction annulée) : **4 080 cas, 0 écart**. Témoin inverse : un attendu faussé exprès → 1 écart attrapé.
- ⚠ **Une bizarrerie de l'écran reproduite exprès** : une date de fin impossible n'est pas rejetée, elle **déborde** (le 30 février = le 2 mars) ; un mois 13 ou un jour 32 sont « illisibles » donc le mandat reste valide. 2 dates de ce genre existent dans le registre.
- ⚠ **Mon erreur, attrapée** : un premier essai a donné 1 768 écarts — j'avais **recopié à la main** la chaîne de 8 160 lettres des attendus. Envoyée telle quelle depuis le fichier (par le pooler, comme le script DVF) : 0 écart. Leçon : un attendu ne se recopie jamais à la main.
- ⚠ La vue **dépend** du registre : un futur patch qui fait `drop view app_registre_mandats_current` devra la retirer puis la reposer — comme il doit DÉJÀ le faire pour `app_filter_catalog_registre`. Sans `cascade`, l'oubli échoue bruyamment.

**Le code** (backend, neuf sauf 3 retouches) :
- `assistant_contexte.py` (neuf) — les définitions communes. ⭐ Le témoin inverse a fait planter l'import en chargeant le lecteur avant le catalogue (deux modules qui s'importaient l'un l'autre) : corrigé à la racine.
- `assistant_objets.py` (neuf) — **la liste fermée : 14 objets** (biens, biens_historique, biens_archives, mandats, contacts, recherches, relations, rapprochements, relances, transactions, demandes, documents, notifications, negociateurs), chacun avec sa source protégée, ses colonnes décrites en français et ses filtres imposés (notifications = les siennes ; contacts = sans les fiches de ménage, comme l'écran).
- `assistant_lecteur.py` (neuf) — `decrire`, `chercher` (total exact, 50 lignes au plus), `compter` (regroupement et somme sur 5 000 lignes au plus, et la réponse dit « tronqué »), et 3 fonctions métier : `fiches_biens` (un EXTRAIT : surfaces, pièces, terrain, diagnostics, texte — ⛔ **jamais** les téléphones, e-mails ni noms des propriétaires, qui sont dans la fiche), `notes_transaction` (la transaction lue D'ABORD avec le jeton, ses notes seulement si elle est visible), `agenda` (la route de l'écran appelée telle quelle, sa garde décide).
- `assistant_catalogue.py` — les 6 lectures rejoignent « qui suis-je » ; un refus de la liste fermée part au modèle en clair, pour qu'il se corrige.
- `assistant_service.py` — les consignes de l'étape 2 (la liste des objets, ne rien inventer, dire d'où vient un chiffre, demander quand c'est ambigu, force de proposition sans prétendre agir).
- `routers/assistant.py` — les **durées** de chaque tour au journal (préparation, premier mot, total), sans texte.

**Les essais** (sans réseau) :
- `test_assistant_lecteur.py` : **43 verts**. Deux témoins inverses tombent au rouge comme il faut : la fiche avec le téléphone des propriétaires, et les notes lues sans contrôle de la transaction.
- `test_assistant_ia.py` : **54 verts** avec le SDK réel. Il prouve aussi que le SDK accepte les 7 schémas de fonctions, et que les durées vont au journal.
- Essai GED voisin : **28 verts**.

**⚠ Limites connues de cette version** :
- Les montants et budgets stockés en **texte** (budget des recherches, montant des transactions) ne se comparent pas. Pour « les recherches à plus de 200 000 € », l'assistant devra lire puis raisonner. À corriger un jour par des vues typées, dans la base.
- La « date effective » d'une offre (la première proposition), que l'écran recalcule, n'est pas reprise. L'assistant lit la colonne `date`.
- Les comparables DVF ne sont pas encore branchés.

**Les gestes qui restent, chacun avec ton accord** :
1. ~~Poser le statut des mandats~~ ✅ FAIT le 12/11 (voir ci-dessous).
2. Commiter et pousser : Render redéploie.
3. La preuve en réel : les 30 questions témoins avec ton compte, puis les témoins de droits avec un commercial (personne à nommer).

**✅ Le statut des mandats est POSÉ en base le 12/11**, avec l'accord de Frédéric (« Oui vas y », après l'explication simple de ce que fait le patch).
- Répétition jouée **depuis le fichier** (par le pooler, sans recopie) : **7 OK, 0 KO** — 4 080 cas sans écart, autant de lignes que le registre pour un admin et pour un négociateur (24 589), compter par statut en 1,9 s, rien pour `anon`, dépendance au registre déclarée. Vérifié ensuite qu'elle n'avait rien laissé.
- Patch posé, ses gardes et vérifications internes vertes.
- **Mesure à part, juste après** : vue en `security_invoker`, les 4 fonctions présentes, `SELECT` pour `authenticated` seulement, `anon` n'exécute rien, 24 589 / 24 589 lignes. Répartition : **Actif 624, Échu 238, Vendu 6 775, Clos 16 952** ; En cours 640, Annulé 23 949. Deux vues dépendent désormais du registre : `app_filter_catalog_registre` (déjà là) et `app_v_mandat_statut`.
- ⭐ **La preuve sur les VRAIES données** : les 24 589 mandats exportés en lecture seule, passés au code de l'écran (extrait de `api.ts`) → **0 écart** avec la vue.
- Sans effet sur l'écran ni sur personne : rien ne lit encore cette vue tant que le code de l'étape 2 n'est pas en ligne.
