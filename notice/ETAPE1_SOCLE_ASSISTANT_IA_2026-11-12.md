# Assistant IA — étape 1 : le socle dormant (audit et explication)

> **12/11/2026 · lecture seule** : rien n'a été écrit en base ni dans le code, rien n'a été installé.
> Plan : `notice/PLAN_DEV_ACCUEIL_ASSISTANT_IA_2026-10-29.md` · cadrage : `notice/SPEC_ETAPE0_ASSISTANT_IA_2026-10-29.md`.
> **Audit limité au socle** : l'étape 1 ne lit ni n'écrit aucun objet métier (annonce, contact, recherche, relation,
> transaction, mandat, document, RDV). Le tableau objets × gestes sera dressé à l'étape 2 (lecture) et à l'étape 3 (écritures).
> ✅ **« Vas-y » de Frédéric le 12/11 → codé le 12/11, en local et éteint (§9).** **En attente** : son accord pour la base de production et le déploiement.

## 1. Ce qui a bougé depuis le cadrage du 29/10

- ⭐ **Le projet a un nouvel agent IA depuis aujourd'hui** : le classement des documents de la GED (`a61db50`, 12/11,
  `openai_ged_classement_service.py` + `routers/ged.py`). Il pose **le patron à reprendre tel quel** :
  - un interrupteur à trois crans `off / admin / on` dans `app_setting`, **relu à chaque appel**, absent ou illisible = éteint ;
  - un **plafond de dépense par jour** calculé dans `app_agent_run`, et « une lecture ratée n'est jamais un vert » : sans le compte, pas d'appel ;
  - `store: false` sur chaque appel à OpenAI ;
  - un **journal sans contenu** dans `app_agent_run` (le type, le coût, jamais le texte) ;
  - une **table de tarifs par modèle** (`_TARIFS`), au lieu des prix fixes du rédacteur ;
  - la fiche de l'agent dans `agent_registry.DEFAULT_SPECS` (défaut en code), surchargée par `app_agent_prompt`.
- ⚠ **Un nouveau modèle est utilisé dans le projet** : `gpt-6-luna` (0,10 $ / 0,50 $ par million de jetons, entrée / sortie),
  **4 fois moins cher** que `gpt-4.1-mini` (0,40 / 1,60). Ta décision du 29/10 reste `gpt-4.1-mini` ; je n'y touche pas.
  Le registre permet de changer de modèle sans redéployer (une ligne de `app_agent_prompt`) : à regarder à l'étape 6 (coûts).
- Rien d'autre dans le backend ne touche à l'assistant (12 commits backend depuis le 29/10, aucun sur ce sujet).

## 2. Les mesures

**Backend**
- `requirements.txt` : `fastapi==0.116.1`, `uvicorn[standard]==0.35.0`, `requests==2.32.4`, `email-validator`, `google-auth`, `psycopg2-binary`. **Aucune** bibliothèque OpenAI : les 4 services appellent `/v1/responses` avec `requests`.
- Aucun flux (`StreamingResponse`) dans le backend aujourd'hui. Les routes sont synchrones, sauf 7 routes publiques (espace client, visite).
- `auth.py` valide le jeton par `/auth/v1/user` et rend l'identité ; le profil (rôle, actif) se lit par `load_profile`. **Le jeton de l'utilisateur est donc déjà entre nos mains** : il suffit de le passer à la base avec la clé publique (`supabase_anon_key`, déjà dans les réglages) pour que la RLS s'applique.
- Essais : 7 fichiers dans `backend/tests/`, en Python simple, sans réseau (faux `requests`). Modèle : `test_ged_classer.py`.

**Le SDK d'agents d'OpenAI** (lu sur PyPI le 12/11, installation simulée en `--dry-run`, rien d'installé)
- Dernière version : **0.24.0** (15/10/2026). ⛔ **Elle est incompatible avec notre FastAPI** : elle exige `starlette>=1.3.1`, et `fastapi==0.116.1` exige `starlette<0.48`. La simulation répond `ResolutionImpossible`. La même exigence existe depuis 0.22.3.
- **0.22.0** (19/08/2026) s'installe **avec notre FastAPI, sans le toucher** : simulation verte, 22 paquets nouveaux (`openai` 3.49.0, `mcp`, `httpx`, `jsonschema`…), **un seul paquet existant change** : `websockets` 17.4 → 16.1.1 (utilisé par uvicorn, sans effet sur nos routes).
- Python ≥ 3.10 demandé ; Render est en ≥ 3.12 (déduit au cadrage).

**Base** (lue le 12/11)
- `app_agent_run` : 16 colonnes (`agent_key`, `negociateur_email`, `status`, `model`, jetons, `cost_usd`, `proposal_json`, `outcome_json`, `error_text`…). RLS : chacun voit ses lignes, admin et manager voient tout. 16 lignes en tout (le rédacteur, juillet).
- `app_agent_prompt` : `agent_key`, `instructions`, `model`, `max_output_tokens`, `is_active`, `version`… 3 fiches (rédacteur, avis de valeur, scan de fiche).
- `app_setting` : clé / valeur, lisible par tout utilisateur actif. Aujourd'hui `ged_lecture_ia = admin`.
- **Aucune table de conversation n'existe** (seule `app_espace_message`, qui est la messagerie de l'espace client, sans rapport).

**Qui lit le journal des agents** : l'écran **Santé** (`loadAgentRuns`, 7 derniers jours, **500 lignes au plus**) et le report des numéros de dossier de la synchro (`push_single_annonce_to_supabase.py`, sans effet sur des lignes sans dossier).

## 3. Ce que je vais faire — 5 pièces, toutes éteintes

1. **La dépendance** : `openai-agents==0.22.0` ajouté à `requirements.txt`, version figée. Les traces envoyées à OpenAI sont **coupées dans le code** (`set_tracing_disabled(True)`), pas par une variable de Render qu'on pourrait oublier. Chaque appel part avec `store: false`.
   ⚠ **Le SDK n'est chargé qu'au premier appel de l'assistant**, jamais au démarrage du serveur : si la bibliothèque posait un jour problème, seul l'assistant tomberait, pas le reste du backend.
2. **Deux tables neuves** (patch SQL avec son inverse et sa répétition, à coller par toi) :
   - `app_assistant_conversation` : à qui elle est, quel agent, un titre, les dates, archivée ou non ;
   - `app_assistant_message` : le fil (ta question, la réponse, les fonctions appelées et leurs paramètres), relié à la ligne de `app_agent_run` du tour.
   - RLS : **chacun lit SES conversations, et l'admin lit aussi celles des autres** (décision du 12/11, question 2). Écriture par le backend seulement.
   - Et deux lignes : l'interrupteur `assistant_ia = off`, la fiche `assistant` dans `app_agent_prompt` (modèle `gpt-4.1-mini`).
3. **Le registre et les tarifs** : la fiche `assistant` en défaut dans le code (consignes de départ, ton GTI, tutoiement), et un petit module de tarifs partagé, que **seul l'assistant utilise**. Le rédacteur et la GED ne sont **pas** touchés (ce serait modifier du code existant).
4. **Le catalogue et ses droits** : le contexte de chaque tour porte l'identité, le rôle et le jeton de la personne. **Il reste chez nous, il n'est jamais envoyé au modèle.** Chaque fonction lit la base **avec le jeton de la personne** (la RLS fait le tri) et refuse si le rôle ne le permet pas. À l'étape 1, **une seule fonction témoin** : « qui suis-je » (ton nom et ton rôle, lus avec ton jeton). Elle sert à prouver la plomberie ; les vraies lectures viennent à l'étape 2.
5. **Les routes** (préfixe `/assistant`) : envoyer un message et recevoir la réponse **en flux** (les mots arrivent au fur et à mesure), lister ses conversations, en relire une. Chaque tour écrit une ligne dans `app_agent_run` (`agent_key = assistant`, jetons, coût, noms des fonctions appelées, **jamais le texte**).
   Garde-fous repris de la GED : interrupteur relu à chaque appel ; **plafond de dépense par jour** (je propose 3 $, voir la question 3) ; **plafond de questions par personne et par jour** (je propose 100) ; **nombre d'étapes maximum par question** (je propose 8, pour qu'une boucle de l'agent ne tourne pas sans fin).

## 4. Ce que ça touche, et dans quel ordre

- **Code neuf seulement** : 4 fichiers neufs dans `backend/app/` (service, catalogue, tarifs, route), 1 fichier d'essais, 2 lignes dans `main.py` (brancher la route), 1 ligne dans `requirements.txt`.
- **Les gestes qui demandent ton accord**, dans cet ordre :
  1. coller le patch SQL (les deux tables, l'interrupteur `off`, la fiche), puis la répétition ;
  2. pousser : Render réinstalle les dépendances et redéploie le backend (`/health` doit rendre le nouveau commit) ;
  3. passer l'interrupteur à `admin` pour la preuve en réel, toi seul.
- **Rien dans le front, rien dans le worker, rien dans le run de nuit.**

## 5. Comment on vérifiera

- **Hors ligne, avant tout push** : un fichier d'essais sans réseau (faux OpenAI, fausse base) — l'interrupteur et ses trois crans, les deux plafonds, le refus avant tout appel, `store: false`, les traces coupées, le jeton de la personne transmis à la base (et jamais la clé de service pour les lectures), le contexte jamais envoyé au modèle, le journal sans texte.
- **Après le déploiement** : `/health` rend le commit ; les routes existantes répondent comme avant ; `/assistant` répond **403** tant que l'interrupteur est `off`.
- **La preuve en réel** (interrupteur `admin`) : tu poses « qui suis-je ? » depuis l'app (un petit bout de code à coller dans la console du navigateur, l'écran viendra à l'étape 4). Attendu : ton nom et ton rôle, la réponse en flux, une ligne `assistant` dans le journal avec son coût, la conversation dans la table, **et rien dans les traces d'OpenAI**.
- **Le témoin inverse** : la même question avec un compte commercial doit rendre **son** nom, pas le tien.

## 6. Comment on revient en arrière

- **L'interrupteur à `off`** : l'assistant se tait à l'appel suivant, sans redéployer.
- **Le code** : retirer la ligne du routeur dans `main.py` et la dépendance, pousser.
- **La base** : le patch inverse supprime les deux tables et les deux lignes ; il vérifie d'abord qu'il ne reste aucune trace.
- Si Render n'arrive pas à installer les dépendances, **la version en ligne reste celle d'avant** : un build raté ne remplace pas le service qui tourne.

## 7. Ce que ça pourrait casser ailleurs

- **L'installation sur Render** : 22 paquets nouveaux. Mesuré : un seul paquet existant bouge (`websockets`, utilisé par uvicorn). Risque faible, et un build raté ne coupe pas le service.
- **Le démarrage du backend** : écarté par le chargement à la demande (pièce 1). Le nom du module du SDK (`agents`) n'entre en conflit avec rien chez nous (vérifié).
- **L'écran Santé** : il montre les 500 dernières lignes du journal des agents sur 7 jours. Dormant, l'assistant n'en écrit aucune. **Mais à l'usage** (6 personnes × 30 questions par jour ≈ 1 260 lignes par semaine), ses lignes **pousseraient hors de l'écran** celles du rédacteur et de la GED. À traiter **avant l'étape 2** : filtrer l'écran ou grouper par agent. Je le note, je ne le change pas ici.
- **Le plafond du jour de la GED** : il ne compte que ses propres lignes (`agent_key = ged_classement`), il ne voit pas celles de l'assistant. Vérifié dans son code.
- **Le report des numéros de dossier** (`push_single_annonce_to_supabase.py`) : les lignes de l'assistant n'ont pas de dossier, il les ignore.
- **Les 38 fonctions sans contrôle** : l'étape 1 n'en appelle aucune (décision du 29/10 : l'agent les contourne).
- **Le coût** : zéro tant que c'est éteint ; la preuve en réel coûte moins d'un centime.

## 8. Les questions pour Frédéric

1. **La version du SDK** : je prends **0.22.0**, la dernière qui s'installe sans toucher à notre FastAPI. Monter FastAPI pour prendre la 0.24.0, ce serait modifier le socle de tout le backend, pour rien d'utile à l'agent. *(Ma recommandation, sauf avis contraire.)*
2. **Qui peut relire une conversation ?** Je propose : **la personne seule**. L'admin voit le journal (qui a posé combien de questions, pour quel coût, quelles fonctions ont été appelées), **pas le texte des échanges**. L'autre choix : l'admin et le manager lisent aussi le texte.
   ✅ **Réponse de Frédéric, 12/11 : « NON ADMIN AUSSI »** (il avait d'abord cliqué « La personne seule », puis s'est corrigé) → la personne lit ses conversations, **l'admin lit aussi le texte**. ⚠ Le manager n'est pas nommé : aucun compte manager aujourd'hui, la règle du 12/10 est « manager = admin pour l'instant », mais **ne pas l'étendre sans lui demander**.
3. **Les plafonds de départ** : 3 $ par jour pour tout l'assistant, 100 questions par personne et par jour, 8 étapes au plus par question. Modifiables plus tard.
   ✅ **Réponse de Frédéric, 12/11 : « Oui, ils me vont ».**

## 9. Codé le 12/11 (en local, éteint) — ce qui existe et ce qui a été prouvé

**Les fichiers** (rien n'est commité, rien n'est en base, rien n'est en ligne)
- `backend/app/services/agent_tarifs.py` — les tarifs par modèle, lus par l'assistant seul. Un modèle sans tarif = coût inconnu, **jamais zéro**.
- `backend/app/services/assistant_catalogue.py` — le contexte (identité, rôle, jeton : **jamais envoyé au modèle**), la lecture avec le jeton de la personne et la clé publique, le double verrou sur le rôle, la fonction témoin `qui_suis_je` (filtrée sur SON id : un admin lit tous les profils).
- `backend/app/services/assistant_service.py` — l'interrupteur `assistant_ia`, les deux plafonds lus dans `app_agent_run` (refus **avant** d'écrire la question), le fil, la relecture avec le jeton, le tour avec le SDK : `store: false`, traces coupées **deux fois** (`set_tracing_disabled(True)` et `RunConfig(tracing_disabled=True)`), 8 étapes au plus, SDK importé au premier appel seulement. Un modèle sans tarif connu **n'est pas appelé**.
- `backend/app/routers/assistant.py` — `POST /assistant/message` (flux, une ligne JSON par événement : `debut`, `outil`, `texte`, `fin` ou `erreur`), `GET /assistant/conversations`, `GET /assistant/conversations/{id}`. Même l'admin, qui RELIT les conversations des autres, **n'écrit pas** dans celles des autres (404). La question est écrite avant l'appel : une saisie ne se perd jamais. Un onglet fermé en cours de route écrit quand même sa ligne d'échec au journal.
- `backend/app/main.py` (+2 lignes), `backend/requirements.txt` (+1 ligne, `openai-agents==0.22.0` figée et commentée).
- `supabase/patch_assistant_ia_etape1_2026-11-12.sql` + `_INVERSE` + `_REPETITION` (attendu « 9 OK, 0 KO », rien n'est gardé). La fiche `assistant` de `app_agent_prompt` porte des consignes **vides** : le serveur garde alors son défaut en code ; la ligne sert à changer le modèle sans redéployer.
- ⚠ Le journal écrit `status = 'proposed'` pour un tour répondu et `'error'` sinon : la contrainte de `app_agent_run` n'admet que `proposed / accepted / rejected / error`, je ne l'ai pas modifiée.

**Les essais** — `backend/tests/test_assistant_ia.py`, **53 contrôles verts** avec le SDK 0.22.0 réel (installé dans un Python À PART, dans mon dossier temporaire : le `.venv` du projet, qui sert au run de nuit, n'est pas touché). Sans le SDK, 27 verts et la partie 5 est dite **SAUTÉE**, jamais comptée verte. OpenAI est remplacé par un faux serveur HTTP qui rend de vrais flux de l'API Responses ; toute autre sortie réseau fait échouer l'essai. Prouvé : éteint = 403 sans rien écrire ni appeler ; cran `admin` = 403 pour un négociateur ; plafond = 429 avant d'écrire ; journal illisible = 503 ; `store: false` sur chaque appel ; ni jeton, ni e-mail, ni identifiant, ni clé chez OpenAI ; le modèle ne voit que les fonctions du rôle ; la fonction lit avec le jeton ; journal sans texte, jetons des deux appels cumulés ; un agent qui boucle s'arrête à 8 appels et l'échec est écrit ; l'essai GED voisin reste vert (28).

⭐ **Le témoin inverse a attrapé un faux vert dans mon propre essai.** Traces rallumées exprès, le contrôle « aucune trace chez OpenAI » restait VERT : le SDK exporte ses traces par **un paquet à part, `httpx2`**, que ma garde ne surveillait pas. Garde étendue à `httpx2` → le témoin tombe au rouge, l'essai normal reste vert. Sans ce témoin, le contrôle n'aurait rien prouvé.

**Ce qui n'est PAS prouvé** : l'installation sur Render (seulement simulée), le flux à travers le proxy de Render, et le vrai modèle. C'est la preuve en réel du §5.

**Les gestes qui restent, chacun avec ton accord** : ① ~~coller le patch SQL puis la répétition~~ ✅ FAIT le 12/11 (voir ci-dessous) ; ② commiter et pousser (Render redéploie ; `/health` doit rendre le commit, `/assistant/message` doit répondre 403) ; ③ passer `assistant_ia` à `admin` et poser « qui suis-je ? » depuis la console du navigateur ; ④ le témoin inverse avec un compte commercial.

**✅ La base est posée le 12/11**, par moi, avec l'accord de Frédéric (« Vas y collé le toi meme tu as mon accord »).
- ⚠ **Ordre réel : la répétition AVANT le patch.** Sa garde refuse de tourner si les tables existent déjà (« deja pose ») : la note disait « le patch puis la répétition », c'était l'inverse.
- Répétition : **9 OK, 0 KO**, et rien n'est resté (mesuré après : aucune table, aucun interrupteur, aucune fiche).
- Patch collé, ses vérifications internes passées. Mesure indépendante juste après :
  - les deux tables, RLS active ;
  - deux règles, en lecture seule, pour `authenticated` ;
  - droits : `SELECT` pour `authenticated` et rien d'autre (rien pour `anon`) ;
  - `assistant_ia = off` ;
  - fiche `assistant` en `gpt-4.1-mini`, 1 500 jetons, consignes vides (le défaut en code s'applique) ;
  - les 3 autres fiches sont intactes, 0 conversation, `ged_lecture_ia` toujours à `admin`.
- **Sans effet tant que le code n'est pas en ligne** : aucun code déployé ne lit ces tables ni cette clé.
