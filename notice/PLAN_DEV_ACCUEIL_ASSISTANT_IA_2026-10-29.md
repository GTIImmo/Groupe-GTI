# Accueil assistant IA (plusieurs agents) — plan de développement

> **Statut au 29/10/2026 : PLAN VALIDÉ PAR FRÉDÉRIC (« ok, mets à jour »), RIEN N'EST CODÉ.**
> Chantier **mené en même temps que ⑧**. Il commence par l'étape 0 (cadrage), et chaque étape suit
> la méthode du projet (audit → explication → « vas-y » → code → contrôle → plan).
> Présentation (privée) : https://claude.ai/artifact/2hGps6HiPXCYbUnpg3bRYu ·
> maquette : `maquettes/accueil-assistant-chatgpt-2026-10-29.html` (+ `.png`).

## Le but

Ouvrir bienvu sur une conversation façon ChatGPT, et plus sur un tableau. D'abord **un agent,
l'assistant, qui répond ET agit**, puis d'autres agents sur le même socle.

## Les décisions de Frédéric (29/10)

1. **Chat d'abord**, façon ChatGPT, en **gardant le rail vertical actuel** ; les détails graphiques se décideront à l'écran.
2. **Ton propre écran** (composants à nous) : **ChatKit écarté** (voir l'audit plus bas).
3. **Moteur : l'Agents SDK d'OpenAI** (`openai-agents`), version figée, traces coupées.
4. **Modèle : `gpt-4.1-mini`**, un modèle par agent, montée en gamme sur demande, pas d'aiguilleur automatique. **Pas de MCP au départ.**
   ⭐ **CHANGÉ LE 13/11 par Frédéric**, après la preuve des 30 questions (5 réponses fausses) et la relecture de l'étude du 29/10 (« un modèle par type de travail + montée en gamme sur demande », jamais construite) : à ma proposition « gpt-6.1-terra par défaut, gpt-6.1-sol en montée en gamme », il répond **« Assistant. Ta reco »**. Et pour la GED : **« on garde son modèle luna, ni touché pas »** — la GED reste sur `gpt-6-luna`, on n'y touche pas. ⛔ **Précisé le 13/11 juste après : « non garde un seul model pour assistant »** — PAS de montée en gamme : l'assistant n'a qu'UN modèle, `gpt-6.1-terra` (le défaut de la recommandation), sans relance automatique sur sol.
5. **Droits = comme l'écran** : tout, sauf les **transactions, uniquement les siennes**, et seulement **les fonctions des écrans de son rôle**. ✅ Précisé le 29/10 (question 1 de l'étape 0) : pour un commercial, les biens = **« Tout le réseau »** (la règle de la base, pas le filtre de sa liste) ; le détail des mandats, les documents et les transactions restent limités à ses biens par la base.
6. **Agent 1 = l'assistant, qui répond ET agit dès sa première version.** Mon conseil (le point du jour d'abord) est noté, **pas retenu**.
7. **Actions : toutes les écritures de l'écran du rôle**, chacune **validée d'un clic**, exécutées par **la même fonction que l'écran** ; pas de liste de gestes réservés posée d'avance — **on retirera à l'usage** celles qui ne doivent pas l'être (ma proposition « sauf les gestes lourds » n'est **pas** retenue).
8. **« Faire », c'est vraiment faire** : préparer le **bon de visite**, **envoyer les e-mails** (depuis l'adresse du négociateur, après le clic), caler les **rendez-vous dans Google Agenda**, et être **force de proposition** (proposer la suite après chaque réponse, remarquer ce qui se répète, regrouper les actions dans une carte « Tout valider / Choisir »).
9. **Agent 2 = le point du jour**, dans l'app ET par e-mail.
10. **Plus tard** : le contrat RGPD et la durée de garde des conversations ; le commercial qui testera après Frédéric.

⛔ **Rappel de doctrine (correction de Frédéric, 29/10)** : « tout est chez nous, les écritures sont instantanées, on attend juste les id Hektor pour communiquer avec lui, nous sommes indépendants ». L'agent appelle la fonction de l'écran ; l'écriture est chez nous à l'instant ; le circuit existant (worker) recopie chez Hektor quand il le faut. Ne jamais opposer « chez nous » et « chez Hektor » pour les actions.

## Les étapes

**0. Le cadrage** — *feu vert : j'enchaîne (lecture, documents)* — ✅ **FAIT le 29/10, les 5 questions tranchées le même jour** (biens d'un commercial : « Tout le réseau » · les 38 fonctions sans contrôle : « Non, plus tard » · vagues A/B/C : « Oui, il me va » · vrais e-mails : « Oui, en interne » · gestion des utilisateurs : « oui exclure ») : `notice/SPEC_ETAPE0_ASSISTANT_IA_2026-10-29.md` (droits mesurés, 41 fonctions sans contrôle, catalogue, 30 témoins, 10 scénarios, 4 questions). ⭐ Trouvaille : les droits « comme l'écran » sont déjà dans la RLS ; l'agent doit lire **avec le JWT de l'utilisateur** (le backend utilise aujourd'hui la clé de service). Python ≥ 3.12 sur Render (déduit).
- Le catalogue de l'agent 1 : 10 à 15 fonctions de lecture + les fonctions d'écriture de l'écran, rôle par rôle, chacune décrite.
- La règle des droits mesurée en base, et la liste des contrôles d'identité manquants (déjà repérés : `app_create_relance_for_contact`, `app_relance_set_status`).
- 30 questions témoins (lecture) et 10 scénarios d'action, avec le résultat attendu (modèle : `backend/evals/scan_fiche/`).
- Les vérifications techniques : Python sur Render, version de l'Agents SDK à figer, stockage des conversations dans Supabase, **envoi d'un e-mail libre au nom de chaque négociateur** (compte de service Google), **bon de visite en PDF côté serveur**.

**1. Le socle du backend, dormant** — *accord : base de production et déploiement* — 🔎 **AUDIT ET EXPLICATION FAITS le 12/11** : `notice/ETAPE1_SOCLE_ASSISTANT_IA_2026-11-12.md`. ✅ **« Vas-y » le 12/11 → CODÉ LE 12/11, EN LOCAL ET ÉTEINT** (§9 de la note) : 4 fichiers neufs, la route, la dépendance figée, le patch SQL avec son inverse et sa répétition ; **53 contrôles verts hors ligne** (`backend/tests/test_assistant_ia.py`, SDK réel, faux OpenAI). ✅ **Base posée le 12/11** avec son accord (répétition 9 OK / 0 KO, puis le patch ; interrupteur `off`). ✅ **En ligne le 12/11 à 18:37** (`d3ff4b3`, `/health` le rend ; 3 routes publiées, 401 sans jeton). ✅ **PROUVÉE EN RÉEL le 12/11 à 17:59** (son accord, sa session Chrome) : 403 interrupteur `off` ; puis `admin` → « Tu es Frederic Gerphagnon, admin… », en flux, via `qui_suis_je` ; 1 conversation, 2 messages, 1 ligne de journal sans texte, 0,00026 $. ⭐ **ÉTAPE 1 FAITE.** Interrupteur laissé à `admin` (décision de Frédéric le 12/11 : « Laisse pour admin »). Non prouvé : traces OpenAI (tableau de bord à regarder), témoin commercial (à l'étape 2). ⚠ 5,2 s avant le premier événement : à remesurer à chaud. ⚠ Le SDK 0.24.0 est incompatible avec notre FastAPI (starlette) : **0.22.0** proposée. Patron repris de la GED du 12/11 (interrupteur `app_setting`, plafond du jour, `store: false`, journal sans texte, tarifs par modèle).
- Agents SDK installé, version figée, `OPENAI_AGENTS_DISABLE_TRACING=1`.
- Tables des conversations et des messages ; prix de chaque modèle (remplace les prix fixes du rédacteur).
- Registre d'agents complété : fonctions autorisées, rôles, plafond de questions, étapes maximum.
- Module du catalogue avec sa couche de droits (identité et rôle dans le contexte local, vérifiés dans chaque fonction).
- Route de conversation en flux ; journal des coûts dans `app_agent_run`. Interrupteur éteint.

**2. L'agent 1 qui répond (lecture)** — *accord pour l'ouvrir* — 🔎 **AUDIT ET EXPLICATION FAITS le 12/11** sur son « Oui vas y » : `notice/ETAPE2_AGENT_QUI_REPOND_AUDIT_2026-11-12.md`. Proposé : un **lecteur générique sur un catalogue d'objets** (liste blanche, jeton de la personne) plutôt que 14 fonctions figées ; ⛔ ~50 tables « lisibles par tous » et 20 fonctions de lecture de l'écran sans contrôle de l'appelant en sont exclues. ✅ Les 3 questions répondues le 12/11 : liste fermée « oui », calculs de l'écran posés une fois dans la base « B », essai par un commercial avec son compte « oui » (personne à nommer). ✅ **« Vas-y » le 12/11 → CODÉ LE 12/11, EN LOCAL** (§9 de la note) : 14 objets en liste fermée, decrire/chercher/compter + fiches_biens/notes_transaction/agenda, consignes, durées au journal ; patch du statut des mandats (**4 080 cas, 0 écart** avec le code de l'écran) ; essais 43 + 54 verts, témoins inverses rouges. ✅ **Statut des mandats POSÉ en base le 12/11** (son accord ; répétition 7/0, puis 0 écart sur les 24 589 vrais mandats contre le code de l'écran). ✅ **En ligne le 13/11 à 08:07** (son « Vas y » ; `5c062f4`, poussé avec 9 commits du classeur sur son accord ; `/health` le rend ~60 s après ; les 3 routes répondent 401 sans jeton). ⚠ **30 questions rejouées en réel le 13/11 (§10 de la note) : 0,12 $, 8,7 s médiane, mais 5 réponses FAUSSES (valeurs devinées, numéro d’annonce pris pour une ville, Clos lu comme vendu) et l’e-mail de la personne inventé** → 5 correctifs codés et **terra en ligne le 13/11 à 09:10** (`bc421e9`). ✅ **Seconde preuve des 30 questions : 0 réponse fausse** (Q13 11 exclusifs, Q18 292 ventes, Q22 1 demande, 63330 = annonce, 62774 clos pas vendu — tous vérifiés en base), 10,2 s médiane, 1 appel refusé sur 30. ⚠ Restent : les noms sensibles aux majuscules (80 DURAND, 4 trouvés), pas de négociateur sur les transactions, le coût affiché sans le cache (0,67 $ affichés pour ~0,2 $ réels estimés) → ✅ **A et B en ligne le 13/11 à 09:23** (`1e0c20a`) : 82 Durand trouvés (exact), coût ~1 centime par question avec le cache (~300 questions/jour sous le plafond). ✅ **C en ligne et prouvé le 13/11 à 10:12** (`75de676`) : 15e objet `dossiers` = le registre des transactions de l'écran (sans écriture en base) ; ventes 2026 par négociateur du bien identiques à la base, 2 207 298 € d'honoraires sur 292 ventes. ⏸ **Le témoin commercial est REPORTÉ par Frédéric le 13/11 : « AUCUN ON FERA PLUS TARD ENCHAÎNE »** — on passe à l'étape 3. ⚠ L'étape 2 n'est donc pas « prouvée avec un vrai compte commercial » (son énoncé) : à faire avant d'ouvrir l'assistant aux commerciaux. ⭐ **L'OBJECTIF FINAL, dans ses mots (12/11) : « le but du développement final est que l'agent répond à n'importe quelle question avec périmètre etc... »** — l'étape 2 doit être pensée pour ça, pas seulement pour les 30 questions témoins.
- Consignes : ton GTI, tutoiement, **force de proposition**.
- Fonctions de lecture branchées ; 30 questions témoins rejouées.
- **Droits prouvés avec un vrai compte commercial.** Ouvert à Frédéric seul.

**3. L'agent 1 qui agit** — *accord : essais réels* — 🔎 **AUDIT FAIT le 13/11** (sur « ENCHAÎNE ») : `notice/ETAPE3_AGENT_QUI_AGIT_AUDIT_2026-11-13.md`. Il manque la carte de validation (une table des actions proposées + valider / refuser) ; 16 fonctions d'écriture sur 22 contrôlent l'appelant, ⚠ 6 non (relances, bien ↔ recherche, proposition, mandant, brouillon d'annonce) → le serveur vérifie le droit avant ; bon de visite PDF à construire ; envoi réel d'e-mail non mesuré sur Render. ⭐ **Catalogue COMPLET le 13/11** à sa demande (« la liste la plus complète possible, ex. les demandes à la direction ») : `notice/ETAPE3_CATALOGUE_COMPLET_DES_ACTIONS_2026-11-13.md` — chaque geste de l'écran avec rôle, conditions et usage réel sur 90 j ; le circuit des demandes existe en entier mais dort (9 demandes, toutes des essais) ; 249 actifs non diffusables, 259 sur aucun portail, 59 biens vivants à mandat échu, 26 offres en attente. ✅ Ordre validé (« Oui enchaîne »). **Lot 1 CODÉ le 13/11, en local** (§6 de la note d'audit) : table des cartes (répétition 8/0, non posée), 3 gestes (demande à la direction, créer une relance, statut de relance), routes valider / refuser ; 36 essais verts. ⚠ Trouvé : un négociateur ne peut pas corriger une demande renvoyée (règle d'écriture réservée à la direction). ✅ **Table posée et code en ligne le 13/11 à 11:16** (`7dcb6d4`, son « Vas y »). ✅ **Première carte prouvée en réel à 11:19** (contact d'essai) : relance n° 20 proposée → rien écrit avant le clic → validée → créée ; second clic refusé (409) ; report proposé puis ANNULÉ → rien n'a bougé ; « faite » validée → faite. ⏳ Reste à éprouver : une demande à la direction sur un bien vivant choisi par lui.
- Cartes de validation (une action ou plusieurs regroupées).
- Fonctions d'écriture de l'écran branchées, contrôle d'identité ajouté là où il manque.
- **E-mails envoyés depuis l'adresse du négociateur**, **rendez-vous Google Agenda**, **bon de visite** (même modèle que l'écran, imprimable ou joint à un e-mail).
- 10 scénarios d'action éprouvés sur le bien d'essai (62774) ; chaque action au journal (qui, quoi, quand).

**4. L'écran d'accueil (le nôtre)** — *« vas-y », puis accord pour déployer*
- Fichier à part (pas dans `App.tsx`), rail gardé, historique, chat, cartes d'action, boutons qui ouvrent les fiches.
- Version téléphone (`MobileLayout`), bouton « Tableau de bord » vers l'accueil actuel.
- Ouverture progressive : Frédéric, puis un commercial, puis tout le monde.

**5. L'agent 2, le point du jour** — *accord : tâche planifiée*
- Liste calculée en base, sans IA ; tâche de nuit déclarée à `check_gti_health.py`.
- L'IA trie et formule (par lots) ; e-mail de 8 h ; « Fait / Demain » en base.

**6. Les coûts**
- Modèle par agent, montée en gamme, cache (consignes + catalogue en tête), tableau de suivi par agent / modèle / personne, un mois de mesures.

**7. La suite**
- Agents suivants, un par un : rédacteur d'annonces (existe), préparation de rendez-vous, compte rendu dicté à la voix, avis de valeur (DVF), Pauline.
- Recherche par le sens dans les textes (`pgvector`), règles de la maison.

**Option : le MCP** — le même catalogue habillé en serveur MCP, connexion par personne, si un jour bienvu doit être interrogé depuis ChatGPT ou Claude.

## Mesures (28-29/10)

- Backend : `auth.py` vérifie le JWT et lit le rôle ; OpenAI appelé par `/v1/responses` en **un seul aller-retour avec `json_schema`**, **aucun `tools`**, pas de flux, pas de multi-tour (`openai_listing_writer_service.py`, `openai_listing_sheet_service.py`).
- Registre `app_agent_prompt` (modèle par agent déjà prévu, `agent_registry.py`) ; journal `app_agent_run` : 16 exécutions du rédacteur (juillet), ~1 centime au total. ⚠ `_estimate_cost_usd` utilise des **prix fixes du rédacteur** (`_REDACTEUR_PRICE_IN/OUT`).
- ⚠⚠ **Les fonctions de lecture ne filtrent pas par personne** : `app_list_relances`, `app_get_rapprochements_for_dossier`, `app_contact_activite`, `app_get_search_timeline`, `app_get_rapprochement_stats`, `app_searches_to_complete`, `app_list_relances_for_contact` sont `SECURITY DEFINER`, fermées à `anon`, ouvertes à `authenticated`, **sans contrôle d'identité**.
- Transactions : RLS de `app_affaire_ledger` = `is_app_global_reader()` OU bien dans `app_mes_biens_portefeuille()`. ⚠ `app_affaire_note`, `_repartition`, `_condition`, `_personne_ecart`, `_supprimee` sont en lecture `true` : ne jamais les lire seules.
- Écritures : `app_create_relance_for_contact` et `app_relance_set_status` **sans contrôle d'identité** ; `app_affaire_note_ecrire`, `app_create_contact_optimistic`, `app_edit_contact_optimistic`, `app_create_search_optimistic`, `app_edit_search_optimistic`, `app_console_archiver_contact_optimistic` contrôlent l'identité.
- Ce qui existe pour « faire » : **bon de visite** généré par l'écran (`openVisitVoucherPrint`, fenêtre d'impression, `App.tsx`) ; **rendez-vous Google Agenda** créés par le backend (`routers/visite.py` → confirmer, DWD) ; **envoi d'e-mails** Gmail (`notification_service.py`, envois de rapprochement et d'estimation) avec **suivi des ouvertures et clics** (`email_tracking.py`). À construire : e-mail libre au nom du négociateur, bon de visite en PDF côté serveur.
- Utilisateurs : 6 actifs (4 admins, 2 commerciaux). Relances : 14 lignes (3 « à faire » en retard depuis juin). Notifications : **1 836 non lues sur 1 866**.
- Front : `App.tsx` = 46 769 lignes ; rail > 1 180 px, `MobileLayout` en dessous.
- Prix officiels relevés le 28/10 (par million de tokens, entrée/sortie) : gpt-4.1-nano 0,10/0,40 · gpt-4.1-mini 0,40/1,60 (cache 0,10) · gpt-5-nano 0,05/0,40 · gpt-5-mini 0,25/2,00 (cache 0,025). Estimation : ~0,5 centime par question en mini, ~19 $/mois pour 6 utilisateurs à 30 questions/jour.

## Audit des outils tout faits (29/10, doc officielle lue, rien installé)

**Agents SDK d'OpenAI (`openai-agents`) — RETENU.**
- Apporte la boucle, les **handoffs** (agents qui se passent la main), les **sessions** (SQLite, Redis, SQLAlchemy…), les garde-fous, un modèle par agent, `Runner.run_sync` (backend synchrone).
- ⭐ Le **contexte local** (`RunContextWrapper`, `Runner.run(..., context=…)`) **n'est pas envoyé au modèle** : identité et rôle y vont, **chaque fonction vérifie le droit** (`is_enabled` ne suffit pas).
- ⚠⚠ **Les traces partent chez OpenAI par défaut, entrées et sorties comprises** : `OPENAI_AGENTS_DISABLE_TRACING=1` (ou `trace_include_sensitive_data=False`).
- ⚠ Non mesuré : Python sur Render (pas de `runtime.txt`), session SQLAlchemy sur Supabase. Nouvelle dépendance `openai` (le backend appelle aujourd'hui OpenAI avec `requests`).

**ChatKit d'OpenAI — ÉCARTÉ par Frédéric (« propre écran »).** Raisons de l'audit : interface en **iframe servie par OpenAI** avec `domainKey` (dépendance à leur CDN), **style limité** (accent, police, arrondi, densité, pas de CSS libre), **français non confirmé**, `Store` Supabase à écrire quand même, produit jeune (Agent Builder ferme le 30/11/2026). Ses bonnes idées sont reprises dans notre écran : salutation et suggestions, cartes à boutons, boutons qui pilotent l'app, mentions @.

## Ce qui reste à décider

Le contrat RGPD et la durée de garde des conversations · le commercial testeur · les détails graphiques (à l'écran).
