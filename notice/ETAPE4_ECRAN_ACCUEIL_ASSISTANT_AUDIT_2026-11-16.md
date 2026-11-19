# Étape 4 — l'écran d'accueil de l'assistant : audit (16/11/2026)

> Audit limité à l'ÉCRAN (le front). Les gestes et les lectures de l'assistant sont dans les notes des étapes 2 et 3.
> Rien n'est codé. Plan : `notice/PLAN_DEV_ACCUEIL_ASSISTANT_IA_2026-10-29.md`, étape 4. Maquette du 29/10 :
> `maquettes/accueil-assistant-chatgpt-2026-10-29.html` (+ `.png`).

## 1. Ce que le serveur sait déjà faire (`backend/app/routers/assistant.py`, en ligne `4e8acd0`)

- `POST /assistant/message` : la question, la réponse EN FLUX, une ligne par événement :
  `debut` (n° de conversation), `texte` (morceau de réponse), `outil` (nom de la lecture en cours),
  `carte` (id, geste, résumé, expiration), `fin` (n° du message, coût, enregistré ou non), `erreur` (phrase).
- `GET /assistant/conversations` : les 50 dernières de la personne (titre, dates).
- `GET /assistant/conversations/{id}` : une conversation et ses messages.
- `GET /assistant/conversations/{id}/actions` : ses cartes et leur état.
- `POST /assistant/actions/{id}/valider` et `/refuser` : le clic sur une carte.
- Tout est derrière l'interrupteur `assistant_ia` (aujourd'hui `admin`) : un compte non ouvert reçoit 403.

## 2. Ce que le front a : RIEN

Aucun écran, aucun appel. Les preuves des étapes 1 à 3 ont été faites par des appels directs dans le navigateur.

## 3. Comment l'application range ses écrans

- `App.tsx` : `type Screen` (l. 411), un `screen === …` par écran (bureau ~l. 27070, téléphone ~l. 26066),
  le rail l. ~26374. Les écrans récents vivent dans leur fichier (`PilotageScreen.tsx`, `SanteSystemeScreen.tsx`,
  `RegistreTransactionsScreen.tsx`).
- L'accueil actuel = `HomeDashboardScreen` (le tableau de bord).
- La barre d'adresse sait déjà rouvrir une annonce ou un contact (`CLES_ADRESSE` : ecran, annonce, contact, vue).

## 4. Écarts entre la maquette du 29/10 et ce qui existe

- « J'ai regardé ta journée pendant la nuit » : c'est l'ÉTAPE 5 (le point du jour), rien n'existe.
- Le micro et le « + » (pièces jointes) : rien n'existe.
- « Rechercher » dans les conversations : le serveur ne donne que les 50 dernières.
- Pouces, régénérer : rien n'existe.
- Les boutons « Écrire aux deux / Proposer une visite » de la maquette sont des SUGGESTIONS ; nos cartes sont
  des gestes à valider (résumé + Valider / Refuser + état).
- L'historique est dans le rail sur la maquette, alors que la décision n° 1 du 29/10 dit « rail gardé ».

## 5. Proposition

- Un fichier à part `AccueilAssistant.tsx` (+ sa feuille de style), sur la maquette du 29/10.
- `App.tsx` touché à 3 endroits : l'import, la branche « accueil » (l'assistant pour un compte ouvert, le tableau
  de bord sinon, exactement comme aujourd'hui), un bouton « Tableau de bord » dans l'écran de l'assistant.
- Contenu : le champ de question, la réponse qui s'écrit au fil de l'eau, la ligne « je lis… » pendant les
  lectures, les cartes Valider / Refuser avec leur état, l'historique (Aujourd'hui / Cette semaine / Plus ancien),
  « Nouvelle conversation », la mention « l'assistant peut se tromper ».
- Liens vers les fiches : les consignes demandent d'écrire « annonce n° X » / « contact n° Y » ; l'écran en fait
  des liens par la barre d'adresse qui existe déjà.
- Téléphone : la même chose sur une colonne, l'historique dans un tiroir.
- Hors étape 4 (rien côté serveur) : micro, pièces jointes, recherche dans l'historique, pouces, point du jour.

## 6. Ce que ça pourrait casser ailleurs

- Pour un compte NON ouvert : rien ne change, le tableau de bord reste l'accueil (l'écran demande au serveur ; un
  403 = tableau de bord).
- ⚠ L'interrupteur est à `admin` : 4 comptes, dont Pauline. Ouvrir l'écran à `admin`, c'est changer SON accueil.
  Le plan dit « Frédéric, puis un commercial, puis tout le monde » → question 1.
- Le tableau de bord n'est pas modifié ; il charge ses données comme aujourd'hui.
- Retour arrière : une constante dans `App.tsx` remet le tableau de bord pour tout le monde.
- Mise en ligne : Vercel se déploie seul au push → accord obligatoire.

## 7. Questions posées le 16/11

1. Qui voit l'écran d'abord : toi seul (recommandé) ou les 4 admins ?
2. L'historique : dans une colonne de l'écran, rail inchangé (recommandé) ou dans le rail comme la maquette ?
3. L'écran vide : quelques exemples de questions cliquables (recommandé) ou le champ seul ?

✅ **Réponse du 16/11, ses mots : « Je souhaite uniquement la page d'accueil pas le bandeau gauche »** → le bandeau
gauche de la maquette (historique, Nouvelle conversation, Rechercher…) N'EST PAS fait ; le rail de l'application
reste tel quel ; on ne fait que la page centrale. Questions 1 et 3 : pas encore répondues. Reste à savoir si les
anciennes conversations doivent rester accessibles autrement (question posée).

⛔ **CORRIGÉ le 16/11, ses mots : « Non il faut adapter le bandeau gauche mais j'ai toute une mise en page avec ce
bandeau, il donc s'adapter et garder quand même un peu d'existant comme le fait que ce bandeau se réduise ; en fait
un audit graphique design et ergonomique de mon app, puis je souhaite garder l'idée de base de ce chantier, à savoir
avoir une mise en page CRM et IA type GPT et Claude, mais adaptée à l'immobilier et à mes fonctionnalités actuelles.
Fais-moi des propositions de maquette. »** → le bandeau gauche EST adapté (pas remplacé) : il garde la réduction et
la mise en page existante. Travail demandé : audit graphique et ergonomique de l'app, puis PLUSIEURS propositions de
maquette. Rien à coder avant son choix.

## 8. Audit graphique et ergonomique (17/11, app en ligne, sa session Chrome, 1280 × 665, lecture seule)

- Rail : 68 px replié (icônes seules), ~260 px ouvert ; fond #1d1e20, accent magenta #c5005f ; recherche « / » en
  tête, groupes « Travail » (7 entrées) et « Pilotage » (3, admin) ; pied = avatar + cloche. Ouvert, il occupe déjà
  ~560 px sur 665 : il reste la place de 2 ou 3 conversations, pas plus. ⇒ c'est la contrainte de toute proposition.
- L'accueil actuel répète la recherche (rail + en-tête), range les compteurs dans 7 cadres identiques ; ses chiffres
  (50, 708, 1 demande, 432 diffusions, 737 recherches à compléter, 0 alerte) sont repris tels quels dans les maquettes.
- Téléphone : barre du haut (menu, recherche, avatar) + barre du bas (`MobileLayout`) ; non revu à l'écran (la
  fenêtre de Chrome ne descend pas à 390 px), dessiné d'après le code.

## 9. Les maquettes (17/11) : https://claude.ai/artifact/E9oissiQis3wcn6gWyEmG8 (privée)

- **A** : le rail garde tout et accueille les conversations (« Nouvelle conversation » sous la recherche ; Pilotage,
  Suivi, Santé repliés en une ligne pour faire la place ; 3 conversations + « Toutes »). L'accueil = l'assistant,
  les compteurs réels en dessous ; « Tableau de bord » en haut à droite.
- **B** : le rail reste EXACTEMENT celui d'aujourd'hui, replié tout seul sur l'accueil ; une colonne blanche des
  conversations à côté (Aujourd'hui / Cette semaine / Plus ancien) ; en conversation, « Ta journée » (les compteurs de
  l'accueil actuel) à droite.
- **C** : l'accueil reste le tableau de bord ; l'assistant est un panneau à droite, ouvrable sur chaque écran, qui
  sait ce qu'on regarde (exemple sur Annonces).
- Une vue téléphone commune à A et B.
- Comportements nouveaux, à trancher : A replie le groupe Pilotage ; B replie le rail tout seul ; C = un panneau sur
  toute l'app et « montrer dans la liste » (l'assistant qui pilote l'écran).

✅ **Sa réponse du 17/11, ses mots : « Non je trouve que cela ne fonctionne pas bien ; si je te donne un peu plus de
souplesse, la possibilité de plus modifier la colonne de gauche. Je préfère le visuel de la 1 pour l'accueil mais il
faut pousser l'optimisation et l'harmonie du projet. Peux-tu me faire de nouveau une maquette plus élaborée ? »** →
B et C écartés ; on part du VISUEL de A pour l'accueil ; la colonne de gauche PEUT être plus modifiée ; v2 à faire,
plus élaborée, en travaillant l'harmonie de toute l'app (pas seulement l'accueil).

## 10. Maquette v2 (17/11) : https://claude.ai/artifact/8fQVty1R8QvSZ4oo5op3rx (privée) — CONFIÉE À UNE SESSION ANNEXE

Faits ici : 1 accueil rail ouvert, 2 conversation avec carte à valider, 3 Annonces rail replié, 4 couleurs et
composants, 5 téléphone accueil. Restent 6 et 7 (téléphone).
⭐ **17/11, ses mots : « Donne cette étape à un chantier annexe pour permettre d'avancer sur le chantier de base et
bien garder en mémoire le plan de base »** → session « maquette-accueil-ia » (design et ergonomie expert), qui écrit
sa propre note `notice/ETAPE4_MAQUETTE_ACCUEIL_DESIGN_2026-11-17.md`. Aucun code de l'écran avant son choix et son « vas-y ».

## 11. Le plan de code de l'étape 4 (17/11, sur « Attaque étape 4 ») — proposé, rien codé

Référence : la maquette VALIDÉE (« Je valide », 17/11) — `notice/ETAPE4_MAQUETTE_ACCUEIL_DESIGN_2026-11-17.md` §5 sexies,
planches de la toile https://claude.ai/artifact/8fQVty1R8QvSZ4oo5op3rx (version 19). Chaque lot se suit capture contre
capture (règle du 12/11), sur bureau 1280 × 665, téléphone 390 et tablette 768, thème bienvu.

**Un seul interrupteur, lu au démarrage** (comme `registre_transactions_ecran`) : `accueil_assistant` = off / une liste
de comptes / admin / on. Éteint = l'application d'aujourd'hui, à l'identique. Le serveur garde en plus sa propre garde
(`assistant_ia`, aujourd'hui `admin`).

- **Lot 1 — le rail (bureau)** : Rechercher ou demander ; Accueil (maison) avec « 1 à valider » et ses 3 conversations +
  « Toutes » ; Annonces, Estimations, Mandats, Transactions ; trait fin ; Contacts, Agenda ; Suivi puis Pilotage (admins) ;
  pied : menu du compte (Santé, Utilisateurs, Déconnexion), compteur des actions Hektor, cloche avec un point. Replié :
  chiffre sur la maison, bulle au survol. `App.tsx` (le rail) + une feuille de style à part.
- **Lot 2 — l'écran de l'assistant** (fichier à part `AccueilAssistant.tsx`) : l'accueil (question, champ, phrase de
  garde, « À traiter » et « Demande-lui par exemple »), la conversation en flux (« je lis… », Arrêter), les cartes
  Valider / Refuser et leurs fins (le sceau), « Tableau de bord » à un clic, les phrases de blocage, « Renvoyer ».
  Serveur : le nombre de cartes à valider par conversation (le point / le chiffre du rail).
- **Lot 3 — relier l'écran** : la relecture après « Valider », les liens vers les fiches (annonce, contact, mandat,
  transaction, recherche, rendez-vous, demande), le retour à la conversation.
- **Lot 4 — Rechercher ou demander** (la ligne « Demander à l'assistant » dans la fenêtre d'aujourd'hui) et « Citer un
  bien ou un contact ».
- **Lot 5 — le téléphone** : le menu ☰ (conversations sous l'Accueil, Santé au pied) et « Reprendre ».
- **Lot 6 — les gestes par l'écran** (§32 de la note de l'étape 3) : la carte qui ouvre la fenêtre de l'écran déjà
  remplie (créer une offre / un compromis / une vente, traiter une demande).

**Ce que ça pourrait casser ailleurs** : le rail est sur TOUS les écrans (un défaut se voit partout) → derrière
l'interrupteur, éteint par défaut ; `App.tsx` est partagé avec la session GED → petits lots, commités vite, rien d'autre
dans le stage ; le téléphone a un rendu séparé (`MobileLayout`) → contrôlé à chaque lot ; retour arrière = interrupteur
à off (sans redéploiement).

## 12. Lot 1 — le rail : CODÉ et CONTRÔLÉ dans l'aperçu (17/11, sur « Moi seul »), rien poussé

**Fichiers** : `apps/hektor-v1/src/RailAssistant.tsx` (neuf : l'interrupteur, la lecture des 3 dernières conversations et
des cartes en attente, les branches de l'Accueil), `apps/hektor-v1/src/rail-assistant.css` (neuf, tout sous
`.app-shell.app-shell-modern.menu-net.rail-assistant`), `App.tsx` (le bloc du rail, la classe, le menu du compte),
`lib/api.ts` (le mode maquette connaît `accueil_assistant`). `npm run build` vert.

**L'interrupteur** : `app_setting.accueil_assistant` — absent / off = le rail d'aujourd'hui À L'IDENTIQUE (aucune règle de
la feuille ne s'applique sans la classe) ; une liste d'adresses ; `admin` ; `on`. Décision du 17/11 : « Moi seul » →
la valeur sera son adresse seule. ⛔ La ligne n'existe pas encore en production (écriture en base : son accord).

**Lecture des conversations** : avec la session de la personne, filtrée sur SON user_id (un admin relit celles des autres
dans Santé, pas dans son rail). Une lecture ratée garde l'affichage d'avant (pas de zéro inventé). Relue toutes les 60 s et
sur l'évènement `assistant:change` (que le lot 2 émettra).

**Contrôlé dans l'aperçu (mode maquette, 1280 × 665)** :
- rail ouvert, admin : Rechercher ou demander ; Accueil (maison) + « 1 à valider » ; 3 conversations, point magenta sur
  celle qui attend ; Toutes les conversations ; Annonces, Estimations, Mandats, Transactions ; trait fin ; Contacts, Agenda,
  Suivi, Pilotage. Tient en 665 px sans défiler. **Mêmes entrées, même ordre, mêmes textes que la planche 20.**
- rail replié : le chiffre sur la maison ; la bulle « Assistant / Nouvelle conversation / 3 conversations / Toutes » —
  ⚠ vue par le CLAVIER (focus), le survol simulé par l'outil ne déclenche pas `:hover` ; c'est la même règle CSS.
- menu du compte, admin : « Administration » → Santé, Utilisateurs (puis Se déconnecter en production) ; Santé s'ouvre.
- négociateur (profil maquette passé en `commercial` le temps de la mesure, remis ensuite) : Accueil commercial, ni Suivi,
  ni Pilotage ; rail 526 px sans défiler.
- téléphone 375 et tablette 768 : aucun élément du rail de l'assistant (MobileLayout inchangé).
- console : seules les erreurs 500 de `/api/hektor-diffusion` du mode maquette sans serveur (sans rapport).

**Ce qui n'est pas encore là (lots suivants)** : cliquer une conversation ouvre l'Accueil et émet `assistant:ouvrir`, que
personne n'écoute encore (lot 2) ; l'Accueil reste le tableau de bord d'aujourd'hui jusqu'au lot 2.

**Retour arrière** : `accueil_assistant` à off (sans redéploiement), ou revenir sur le commit.

**En ligne (17/11)** : commit `1127cde` poussé (avec `4db80ff` de la session classeur, poussé par elle), Vercel prêt.
Réglage de production `accueil_assistant` = son adresse seule (créé avec son accord, relu). Vu dans son Chrome, en
lecture seule : la classe `rail-assistant` posée, les 9 entrées dans l'ordre, et ses 3 dernières conversations
**identiques à la base** (témoin SQL, mêmes titres, même ordre). Aucun « à valider » : la base n'a aucune carte en attente
(2 cartes « proposées » sont périmées, donc à juste titre non comptées). Le chiffre lui-même n'est vu qu'en mode maquette.

## 13. Lot 2 — l'écran de l'assistant : AUDIT (17/11, sur « Oui »), rien codé

**Périmètre de l'audit** : le front (`App.tsx`, `lib/`), l'API de l'assistant (`backend/app/routers/assistant.py`,
`assistant_service.py`), les vraies réponses en base, les planches 1, 2, 3, 6 et 23. Pas mesuré : le téléphone (lot 5).

**Ce que le code dit**
- ⭐ **Aucun écran de l'assistant n'existe dans le front** : zéro appel à `/assistant/` dans `apps/hektor-v1/src`. Les
  étapes 1 à 3 ont été prouvées par des appels directs à l'API. Le lot 2 écrit donc l'écran EN ENTIER.
- **Le serveur a déjà tout** (aucune ligne serveur dans ce lot) :
  `POST /assistant/message` {question, conversationId?} → flux NDJSON : `debut` {conversationId}, `texte` {delta},
  `outil` {nom}, `carte` {id, geste, resume, expire_le}, puis `fin` {messageId, enregistre} ou `erreur` {detail} ;
  les refus avant le flux sont de vrais codes (403 éteint, 404 conversation d'un autre, 429 plafonds) ;
  `GET /assistant/conversations` (50, les miennes) ; `GET /assistant/conversations/{id}` (messages) ;
  `GET /assistant/conversations/{id}/actions` (cartes et leur état) ; `POST /assistant/actions/{id}/valider|refuser`
  (409 avec la phrase exacte : expirée, déjà validée… ; un échec revient en 200 `ok:false` « Non fait : … »).
- Le chiffre « à valider » par conversation : **déjà calculé dans le rail** (lot 1, lecture sous RLS) — pas de serveur.
- Les réponses réelles portent du **gras `**…**`** et des **paragraphes** (relu en base) → un petit rendu sans
  `innerHTML` : paragraphes, gras, listes « - » et « 1. ». Rien d'autre.
- Les traces « Annonce trouvée / Mandat lu » : le serveur n'envoie que le NOM de la fonction (36 noms) → une table de
  libellés dans le front (« Je lis l'agenda… », puis « Agenda lu »), repli « Recherche faite ».
- L'Accueil d'aujourd'hui = `HomeDashboardScreen` (App.tsx ~27113) : il devient la vue « Tableau de bord », **rendu tel
  quel**, derrière la bascule « Assistant | Tableau de bord » de la planche 1.
- Appel à Render : le modèle de `lib/gedClassementIa.ts` (jeton de session, `VITE_BACKEND_API_URL`), dans un fichier à
  part `lib/assistant.ts`.

**Le plan du lot 2** (front seul, deux fichiers neufs + quelques lignes d'App.tsx)
1. `lib/assistant.ts` : les 6 appels, la lecture du flux ligne à ligne, le bouton Arrêter (coupe la lecture).
2. `AccueilAssistant.tsx` + `accueil-assistant.css` :
   - l'accueil (planche 1) : date, bascule, « Bonjour Frédéric, on commence par quoi ? », le champ, la phrase de garde,
     « À traiter » (les MÊMES chiffres que le tableau de bord d'aujourd'hui, seulement ceux qui ne sont pas à zéro, et une
     ligne « Rien d'autre : … » pour les zéros), « Demande-lui par exemple » (un clic remplit le champ, n'envoie pas) ;
   - la conversation (planche 3) : la question, les traces, la réponse qui s'écrit, les cartes (planche 6 : attend,
     en cours, validée avec le sceau, refusée, non faite, expirée), « Rien ne part avant ton clic. » ;
   - « Toutes les conversations » : la liste des 50 dernières (titre, date, point magenta) — non dessinée, forme simple ;
   - les blocages (planche 23) : une phrase par cas, « Renvoyer » quand le flux est coupé.
3. `App.tsx` : si l'interrupteur est allumé pour la personne, l'Accueil rend `AccueilAssistant` (qui garde le tableau
   de bord à un clic) ; il écoute `assistant:ouvrir` (le rail) et émet `assistant:change` (le rail se relit).

**Hors du lot 2** (déjà prévus) : les liens vers les fiches, la relecture de l'écran après « Valider », le retour à la
conversation (lot 3) ; « Citer un bien ou un contact » et la ligne dans la recherche (lot 4) ; le téléphone (lot 5).
⚠ Donc au lot 2, une carte validée fait bien son geste, mais la fiche ouverte ailleurs ne se relit qu'au prochain
chargement.

**Ce que ça pourrait casser ailleurs**
- L'Accueil de la personne allumée change : derrière l'interrupteur (toi seul), retour = off sans redéploiement ; le
  tableau de bord est rendu par le même composant, avec les mêmes données.
- Chaque question coûte (OpenAI) : les plafonds du serveur restent les gardes (100 questions par jour, budget du jour).
- Un geste validé écrit pour de vrai (production, Hektor) : c'est déjà le cas par l'API ; l'écran ne fait qu'y donner
  accès, avec les mêmes contrôles au clic.
- `App.tsx` partagé avec la session GED : quelques lignes seulement, stage fichier par fichier.
- Téléphone : `MobileLayout` ne rend pas cet Accueil → inchangé (contrôlé).

**Comment on vérifiera** : dans l'aperçu (mode maquette : un faux flux pour dessiner chaque état, capture contre
capture avec les planches 1, 3, 6, 23), puis en ligne chez toi : une question de lecture, puis une carte sans
conséquence (une relance sur un contact d'essai) validée et une refusée.

## 14. Lot 2 — l'écran de l'assistant : CODÉ et CONTRÔLÉ dans l'aperçu (17/11, sur « Vas-y »), rien poussé

**Fichiers** : `lib/assistant.ts` (neuf : les 6 appels, la lecture du flux, le faux flux du mode maquette),
`AccueilAssistant.tsx` + `accueil-assistant.css` (neufs : l'écran), `RailAssistant.tsx` (la demande du rail GARDÉE jusqu'à
ce que l'Accueil soit monté, et l'évènement « change »), `App.tsx` (l'Accueil rend l'assistant quand l'interrupteur est
allumé, le tableau de bord d'aujourd'hui passé tel quel ; `chiffresAccueilAssistant`, les mêmes calculs que le tableau
de bord). Rendu du téléphone (`MobileLayout`, App.tsx ~26073) NON touché. `npm run build` vert.

⚠ **Trouvé en contrôlant** : le préfixe « aa- » était DÉJÀ celui des affaires apportées (`affaires-apportees.css`,
17 classes, dont `.aa-texte`, `.aa-liste`, `.aa-note`, `.aa-vide` en commun) : la réponse s'affichait dans un cadre qui
n'était pas le sien. Tout l'écran est passé en « asi- » (0 collision mesurée). Leçon : chercher un préfixe libre AVANT.

**Contrôlé dans l'aperçu (mode maquette, faux flux, 1280 × 665, Chrome)** :
- accueil = planche 1 : date, bascule, « Bonjour …, on commence par quoi ? », champ, phrase de garde, « À traiter »
  (zéros sur une ligne), « Demande-lui par exemple » (un clic remplit le champ sans envoyer) ;
- une question → la conversation = planche 3 : la question, les traces (« Recherche faite », « Carte préparée »), la
  réponse en gras et listes, la carte « Relance … à valider avant 12:54 », Valider / Refuser, « Rien ne part avant ton clic » ;
- Valider → « En cours » (ambre) puis « Validée à 12:27 » avec le sceau et « Relance créée. » (planche 6) ;
- une conversation rouverte depuis le rail (historique + sa carte) ; Refuser → « Refusée à … », « Rien n'a été fait. » ;
- coupure → « La connexion s'est coupée… » + Renvoyer ; erreur → « L'assistant n'a pas pu répondre. » ; 429 →
  « Tu as posé 100 questions aujourd'hui. », champ grisé, la question rendue au champ ; Arrêter → « Réponse arrêtée » ;
- « Toutes les conversations » (titre et date) ; un clic sur une conversation DEPUIS l'écran Annonces l'ouvre bien ;
- « Tableau de bord » = l'écran d'aujourd'hui, mêmes chiffres que « À traiter ».

**Pas encore vérifié** : le vrai serveur (le flux réel de Render, une vraie carte) — c'est la preuve en ligne, chez lui
seul. Pas fait au lot 2 (prévu au lot 3) : les liens vers les fiches, la relecture de l'écran après « Valider ».

## 15. Lot 2 — EN LIGNE et PROUVÉ chez lui (16/11, « Oui les deux »)

**Le commit** : mes 6 fichiers, mis au stage puis laissés ~10 s le temps d'un build, sont partis dans le commit de la session
GED (`7e6bf40`, « GED morceau 10 ») — un commit emporte TOUT l'index. Rien n'était poussé. Sur « Oui, sépare » : remis en
deux commits, `fa24105` (GED, sa note seule, son message et son auteur) puis `4f620fe` (le lot 2) ; **arbre final identique
octet pour octet** (`737395fe…` des deux côtés) ; poussés ensemble. Leçon en mémoire : `git add` et `git commit` dans la
MÊME commande, les contrôles avant.

**La preuve, dans son Chrome, sur https://groupe-gti.vercel.app (interrupteur : lui seul)** :
- l'accueil s'affiche (« Bonjour Frederic… », À traiter : la demande en attente du 02/06 avec « Ouvrir Suivi ») ;
- question de lecture « Qu'est-ce que j'ai dans mon agenda lundi ? » → le VRAI flux de Render : « Je réfléchis… »,
  la trace « Agenda lu », la réponse en gras, le bouton Arrêter pendant le flux ;
- « Crée une relance pour demain pour le contact d'essai 10354641… » → la carte « Relance, à valider avant 13:38 » ;
  ⭐ **le chiffre « 1 » s'est allumé sur la maison du rail** (le témoin positif qui manquait au lot 1) ;
  Valider → « Validée à 13:09 », sceau, « Relance créée. », et le chiffre s'éteint ;
  témoin SQL : carte `executee`, `resultat` {relance_id 23, échéance 2026-11-17} ; `app_relance_rapprochement` id 23,
  contact 10354641, « essai de l'écran de l'assistant », `a_faire`, à son nom ;
- une seconde carte « essai refus » → Refuser → « Refusée à 13:09 », « Rien n'a été fait. » ; témoin : carte `refusee`,
  AUCUNE relance « essai refus » en base ;
- la conversation rouverte depuis l'écran ANNONCES (clic dans le rail) : 3 questions, la carte validée sous la 2e, la
  refusée sous la 3e — l'historique se reconstruit juste.
⚠ Reste en production : la relance 23 (contact d'essai CLAUDE TESTCLAUDE, demain), à clore depuis l'écran s'il le veut.

**⚠ Trouvé en ligne, CORRIGÉ en local, PAS ENCORE POUSSÉ** : « 0 recherche à compléter » à l'accueil, contre 737 au
tableau de bord. Cause : l'écran monte AVANT que le profil soit chargé ; le rôle vaut alors « négociateur », donc la
lecture ne prenait que SES recherches. Correctif : la portée est `undefined` tant que le profil n'est pas là (l'écran
attend), puis relue si elle change (`porteeRecherches`, App.tsx et AccueilAssistant.tsx). Build vert.
✅ **Correctif poussé (`e7620f6`) et vu en ligne le 16/11** : l'accueil affiche « 737 Recherches à compléter », comme le
tableau de bord, sous « 1 Demande en attente » ; « Rien d'autre : 0 mandat qui expire, 0 diffusion bloquée, 0
synchronisation en erreur ». ➡ **Lot 2 CLOS.** Suivant : lot 3 (liens vers les fiches, relecture après « Valider »,
retour à la conversation), sur son « vas-y ».

## 16. Lot 3 — relier l'écran : AUDIT (16/11, sur « Oui vas y »), rien codé

**Périmètre** : `App.tsx` (adresse, ouverture d'une fiche, relecture après un geste, fil de navigation, bouton Retour),
les consignes de l'assistant (`assistant_service.py`), les 123 réponses en base, les travaux posés par l'assistant.
Pas mesuré : le téléphone (lot 5).

**1. La relecture après « Valider »** — le mécanisme EXISTE (App.tsx ~14505) : `signalerGeste()` émet
`hektor:geste-fait`, App relit ses données et relaie aux rubriques de la fiche ; `relireQuandLeTravailFinit(job)` attend
la fin d'un travail Hektor (relu toutes les 3 s, 2 min au plus) puis relit. L'écran de l'assistant ne l'appelle pas.
Mesuré : les gestes qui posent un travail rendent son numéro dans `resultat.travail` (transaction, créer un contact,
ajouter une recherche…) ou `resultat.job_id` (photos) ; ces travaux portent `requested_by` = SON identifiant
(2 vérifiés : `change_hektor_offre_status`, `create_hektor_contact`) → ils entrent bien dans « Mes actions envoyées à
Hektor ». ➡ À faire : après une carte validée, `signalerGeste()` tout de suite, et `relireQuandLeTravailFinit` si un
numéro de travail revient.

**2. Les liens vers les fiches** — l'adresse n'ouvre que l'annonce (`?annonce=` = **app_dossier_id**) et le contact
(`?contact=` = notre numéro). Portes existantes : `openDossierDetailPage(app_dossier_id)`, `openContactDirectory(id)`.
⚠ L'assistant, lui, cite le **numéro d'annonce Hektor** (consignes : « l'annonce 63330 » = hektor_annonce_id) : il faut
le traduire en app_dossier_id (listes en mémoire, sinon une lecture de `app_dossier_current`).
Mesure des 123 réponses enregistrées : **23 citent un bien par son numéro** (« bien 62965 », « annonce **24935** »,
« bien d'essai **62965** » : formes variées, parfois en gras), **1 seule cite un contact par son numéro** (les contacts
sont cités par leur NOM), 0 mandat. Deux façons de faire :
- A — l'écran REPÈRE les formes « annonce / bien + numéro » dans le texte : rien côté serveur, marche sur l'historique,
  mais ne trouve jamais un contact cité par son nom, et peut se tromper de forme ;
- B — les consignes demandent au modèle d'écrire chaque objet sous une forme fixe, `[CLAUDE TESTCLAUDE](contact:10354641)`,
  `[annonce 63289](annonce:63289)` ; l'écran en fait un lien bleu canard : sûr, contacts compris, mais une ligne de
  consignes (serveur, Render) et seulement pour les nouvelles réponses. ⭐ Recommandé : **B, avec A en repli pour
  l'historique et les oublis** (seulement « annonce / bien + numéro »).
- Et les **cartes** : leur résumé est écrit par le serveur. Le serveur connaît le bien / le contact de la carte
  (`parametres`) : il peut joindre une « cible » à la carte (dans le flux et la relecture) → un lien « Ouvrir la fiche »
  sur la carte. Petit ajout serveur.

**3. Le retour à la conversation** — la fiche s'ouvre PAR-DESSUS l'écran : l'écran de l'assistant est démonté, et
revient vide à la fermeture. Le bouton Retour de la fiche dit « Aux annonces » (ou « Fiche contact » au retour d'un
contact, App.tsx ~27423 `backSynthLabel`). ➡ À faire : garder la conversation ouverte pour l'onglet (sessionStorage) et
la rouvrir au retour, à la même réponse ; le bouton dit « À la conversation » quand la fiche vient de l'assistant. Le
morceau « ‹ Conversation » dans le FIL de navigation (planche 23) demande un 3e type d'entrée dans le fil (aujourd'hui :
annonce, contact seulement) : faisable, mais il touche un mécanisme partagé par toutes les fiches.

**4. Les cinq autres objets** (mandat, transaction, recherche, rendez-vous, demande) : AUCUN écran ne sait s'ouvrir sur
l'un d'eux par un numéro (pas d'entrée dans l'adresse, ni de porte « ouvrir sur ») ; chacun demande une petite porte dans
un AUTRE écran (registre, registre des transactions, agenda à une date, Suivi sur une demande). ⭐ Recommandé : un
lot 3b à part, objet par objet.

**Le plan proposé du lot 3 (3a)**
1. Relecture après « Valider » (front seul).
2. Liens annonce et contact : consignes B (serveur, + un essai), rendu des liens et repli A (front), la « cible » des
   cartes (serveur, + essais) et « Ouvrir la fiche » sur la carte.
3. Retour à la conversation : conversation gardée, bouton « À la conversation » ; le fil de navigation en option.

**Ce que ça pourrait casser ailleurs** : les consignes changent la FORME de toutes les réponses (un lien mal écrit
s'afficherait tel quel → le rendu ne transforme que les deux formes reconnues, le reste reste du texte) ; la cible ajoutée
aux cartes ne change ni le geste ni ses contrôles (lecture seule) ; `signalerGeste` relit l'app comme après un geste fait à
la main (déjà le cas partout) ; le bouton Retour ne change que quand l'écran de l'assistant est allumé ; push du serveur =
redéploiement Render (file des services à vérifier vide n'est pas concernée : Render seul).

## 17. Lot 3a — CODÉ et CONTRÔLÉ (16/11, sur « Vas y »), rien poussé

**Serveur** (`assistant_gestes.py`, `assistant_service.py`) :
- `cibles_carte(parametres)` : sur quoi porte une carte, tiré des paramètres que le SERVEUR a préparés — le contact
  (`hektor_contact_id`) d'abord, puis le bien (numéro d'annonce, sinon app_dossier_id). Joint à la carte du flux
  (`ranger_carte`) et à la relecture (`lister_cartes`, qui lit `parametres` pour la calculer puis les RETIRE de la réponse :
  le texte d'un e-mail ou des critères ne sortent pas). Mesuré sur les 24 gestes réels : e-mail interne, transaction,
  notifications, rendez-vous déplacé / supprimé → aucune cible (pas de lien inventé).
- Une ligne de consignes : un bien ou un contact LU s'écrit `[l'annonce 63330](annonce:63330)` (numéro d'annonce) ou
  `[M. MARTIN](contact:10012345)` ; seulement avec un numéro lu ; aucune autre sorte de lien. (Exemples fictifs.)
- Essais : 218 verts (+7, section 11), 60 (+1 : la consigne), 73. **Témoin inverse** : retirer le filtre des paramètres →
  rouge « les paramètres (le texte de l'e-mail) ne sortent PAS », puis vert une fois rétabli.

**Écran** (`AccueilAssistant.tsx`, `lib/assistant.ts`, `accueil-assistant.css`, `App.tsx`) :
- les deux formes deviennent un lien bleu canard ; REPLI pour l'historique : « annonce / bien (d'essai) (n°) **NNNN** »
  (4 à 6 chiffres) ; tout le reste reste du texte ;
- « Ouvrir le contact / l'annonce N / le bien » sous chaque carte qui a une cible ;
- l'annonce : numéro Hektor → app_dossier_id (listes en mémoire, sinon `loadDossierByHektorAnnonceId`), fiche ouverte
  PAR-DESSUS l'Accueil (la conversation reste montée), bouton **« Retour · À la conversation »** ; introuvable parmi les
  vivants → la liste des annonces étendue aux archives sur ce numéro ; le contact → l'écran Contacts (comme partout) ;
- après une carte validée : `signalerGeste()` (l'app se relit comme après un geste à la main), et
  `relireQuandLeTravailFinit` quand le geste a posé un travail Hektor (`resultat.travail` ou `job_id`) ;
- la conversation est gardée pour l'onglet (sessionStorage `gti_assistant_conversation`) : au retour par « précédent »
  ou F5, elle se rouvre ; un clic sur « Accueil » dans le rail en ouvre toujours une nouvelle ; une conversation qui ne se
  relit plus (404) est oubliée ;
- le flux n'est PLUS coupé quand l'écran se démonte (ouvrir un contact pendant une réponse la perdait) ;
- au passage, le titre du bouton Retour de la fiche suit son libellé (il disait « Retour aux annonces » même pour
  « Fiche contact » — défaut d'avant, une ligne).

**Contrôlé dans l'aperçu (Chrome, mode maquette)** : lien écrit et lien de repli dans une réponse ; un numéro absent
→ liste étendue aux archives ; « précédent » → la conversation se rouvre ; « Ouvrir le bien » d'une carte → la fiche
par-dessus, « Retour · À la conversation » → la conversation intacte (2 questions) ; Valider → 1 signal
`hektor:geste-fait` et 1 `assistant:change`. Build vert.

**Pas encore fait / vérifié** : en ligne (le vrai modèle écrit-il bien la forme ?) ; le morceau « ‹ Conversation » du
fil de navigation (option) ; les cinq autres objets (lot 3b).

## 18. Lot 3a — EN LIGNE et PROUVÉ chez lui (16/11, « Oui les deux »), lecture seule

`fc8933b` poussé (seul dans la liste relue) ; Render `/health` = fc8933b9a40c, Vercel servi. Dans son Chrome :
- « Où en est le bien d'essai 63330 ? Et qui est son mandant ? » → le VRAI modèle a écrit le lien : « bien d'essai 63330 »
  en bleu (« Ouvrir l'annonce 63330 ») ; clic → le numéro Hektor 63330 traduit en **app_dossier_id 10000006** (« ESSAI
  8A2B TOUS CHAMPS »), fiche par-dessus l'Accueil, bouton **« Retour · À la conversation »** → retour, la conversation
  intacte ;
- l'ancienne conversation « Sur l'annonce 24935, masque la photo… » (lot 4, avant les liens) : **4 liens de repli** dans le
  texte (annonce 24935, 62963) et **8 « Ouvrir l'annonce … »** sous les cartes relues — la cible vient du serveur ;
- « Pose un rendez-vous … CLAUDE TESTCLAUDE » : « Ouvrir le contact » → la fiche 10354641 dans l'écran Contacts (on y voit
  la relance du lot 2) ; « précédent » du navigateur → la conversation se rouvre (2 questions).
⚠ Constaté : depuis un contact, il faut **deux** « précédent » (l'ouverture d'un contact pose la liste des contacts PUIS
la fiche dans l'historique — comportement d'avant, de `showContactInDirectory`). Rien écrit en production pendant la preuve.
➡ **Lot 3a CLOS.** Restent : le fil « ‹ Conversation » (option), le lot 3b (mandat, transaction, recherche, RDV, demande),
puis 4 (Citer un bien, Rechercher ou demander), 5 (téléphone), 6 (gestes par l'écran).

## 19. Lot 3b — les cinq autres objets : AUDIT (16/11, sur « Lot 3b, les 5 objets »), rien codé

**Périmètre** : ce que l'assistant LIT de chaque objet (`assistant_objets.py`), les paramètres de ses cartes (mesurés
en base au §17), et la porte de chaque écran dans `App.tsx` / `RegistreTransactionsScreen.tsx`. Pas mesuré : téléphone.

| objet | ce que l'assistant connaît | la porte qui existe | ce qui manque |
|---|---|---|---|
| mandat | `numero_mandat` (+ app_dossier_id, hektor_annonce_id) | le registre filtré sur un numéro (`rechercheOuvrirMandat`, recherche globale) | rien : même geste, sans la ligne exacte |
| transaction | `app_affaire_id` (+ app_dossier_id, hektor_annonce_id, app_chaine_id) | le registre des transactions cherche déjà par numéro d'annonce et par chaîne | une recherche DE DÉPART (prop) — la recherche y est interne, et la période gardée peut cacher la ligne |
| recherche | `contact_search_key` (+ hektor_contact_id) | la fiche du contact (ses recherches en tête) | la clé → le contact (une lecture) |
| rendez-vous | sa date (lue par `lire_mon_agenda`) | l'agenda | une DATE DE DÉPART (prop) — la date y est interne |
| demande | `id`, `app_dossier_id` | direction : Suivi + la fiche du bien en mode « suivi » ; négociateur : la fiche du bien | rien |

**Mesures** : 25 145 lignes de mandats pour **18 836 numéros** (tous numériques) → un numéro de mandat n'identifie pas un
mandat (déjà su : 4 142 doublons) ; le lien mène au registre filtré sur ce numéro, qui peut montrer plusieurs lignes.
Cartes : la transaction porte `app_affaire_id` ; archiver / modifier une recherche, `contact_search_key` ; créer un
rendez-vous / rendez-vous client, `debut` ; la demande à la direction, `hektor_annonce_id`.

**Le plan proposé**
1. Serveur : la consigne gagne cinq formes — `(mandat:NUMERO)`, `(transaction:APP_AFFAIRE_ID)`, `(recherche:CLE)`,
   `(rdv:AAAA-MM-JJ)`, `(demande:APP_DOSSIER_ID)` — toujours « seulement un numéro lu » ; `cibles_carte` ajoute
   transaction, recherche, rendez-vous (sa date) et demande ; essais + témoin inverse.
2. Écran : les cinq formes deviennent des liens ; les portes : mandat → registre filtré ; transaction → registre des
   transactions sur sa chaîne (la période est ignorée tant que cette recherche de départ est là, SANS toucher à la
   période gardée par l'écran) ; recherche → la fiche de son contact ;
   rendez-vous → l'agenda à cette date ; demande → Suivi sur le bien (direction) ou la fiche du bien (négociateur).
3. Deux ajouts de propriétés dans deux écrans PARTAGÉS : `rechercheDepart` (registre des transactions) et `dateDepart`
   (agenda), lus seulement quand ils sont donnés.

**Ce que ça pourrait casser ailleurs** : le registre des transactions et l'agenda sont utilisés par tous ; les deux
propriétés sont absentes partout ailleurs, donc sans effet (comportement d'aujourd'hui) ; la période gardée par
l'écran n'est pas modifiée (elle est seulement ignorée pour la recherche de départ) ; les consignes changent encore la forme des réponses
(même garde : seules les formes reconnues deviennent des liens).

## 20. Lot 3b — CODÉ et CONTRÔLÉ (16/11, sur « Vas-y »), rien poussé

**Serveur** : `cibles_carte(parametres, geste)` ajoute la transaction (`app_affaire_id`), la recherche (sa clé, quand le
contact n'est pas déjà là), le rendez-vous (le JOUR de `debut`, jamais inventé si illisible) et la demande (seulement pour
`demande_direction`, par le numéro d'annonce) ; la consigne gagne les cinq formes (`mandat:`, `transaction:`,
`recherche:`, `rdv:`, `demande:`, exemples fictifs). Essais 223 + 61 + 73. **Témoin inverse** : la « demande » posée
pour tout geste sur un bien → rouge (« un bien modifié… »), puis vert.

**Écrans partagés (propriétés absentes = comme avant)** :
- `RegistreTransactionsScreen` : `chaineDepart` — la liste ne montre que cette chaîne, toutes années, et ouvre sa fiche ;
  les filtres gardés ne sont PAS modifiés (seulement ignorés) ; un filtre changé, une recherche tapée ou « Tout voir » la
  retire ; bannière « Une transaction, ouverte depuis l'assistant · Tout voir » (style ajouté à registre-transactions.css) ;
- `GoogleAgendaGlobalScreen` : `dateDepart` — l'agenda s'ouvre en vue jour à cette date.

**Écran de l'assistant** : les cinq formes deviennent des liens (une valeur qui n'a pas la forme de son genre reste du
texte) ; « Ouvrir la transaction / la recherche / l'agenda au JJ/MM / la demande » sous les cartes ; les portes dans App :
mandat → registre filtré sur le numéro ; transaction → sa chaîne (registre ouvert à la personne) sinon la fiche du bien ;
recherche → la fiche de son contact ; rendez-vous → l'agenda ce jour-là ; demande → Suivi + fiche (direction), la fiche
sinon.

**Contrôlé dans l'aperçu (mode maquette)** : mandat → registre, recherche « 18787 » ; transaction → registre des
transactions avec la bannière (la maquette n'a aucune ligne : la fiche ouverte n'y est PAS vérifiée) ; « Tout voir » → la
bannière part ; recherche → Contacts ; rendez-vous → agenda au 2026-11-18 ; demande → Suivi, fiche du bien 7801.
⚠ Noté : sous la bannière, l'en-tête du registre affiche encore la période gardée (« 2026 ») alors qu'elle est ignorée.

**Pas encore vérifié** : en ligne (le vrai modèle écrit-il ces formes ? la fiche d'une vraie chaîne s'ouvre-t-elle ?).

## 21. Lot 3b — EN LIGNE (`c633b10`), preuve PARTIELLE chez lui : deux défauts trouvés, corrigés en local, PAS poussés

`c633b10` poussé (seul dans la liste relue) ; Render `/health` = c633b100b417, Vercel servi.
Question de lecture : « Sur le bien d'essai 62965 : quel est son mandat, et quelles transactions a-t-il ? Et qu'ai-je dans
mon agenda mercredi 18 novembre ? » → le vrai modèle a écrit **les liens de transaction** (« Offre de 79 000 € »,
« Offre de 80 000 € ») et le lien du bien ; **pas de lien de mandat** (le bien n'a pas de numéro de mandat — juste) ; **pas
de lien de rendez-vous** (il a listé l'agenda sans la forme `rdv:` : la consigne n'est pas suivie à chaque fois).
⛔ **Défaut 1 (le mien)** : clic sur « Offre de 79 000 € » → le registre des transactions affiche « Les dossiers n'ont pas
pu être chargés » ; console : `canceling statement due to statement timeout`. J'avais fait lire TOUTES les années pour
ignorer la période ; la base coupe. **Corrigé** : `transactionPourLien` rend l'année du DERNIER évènement de la chaîne
(c'est elle que `app_registre_dossiers` filtre : `left(date_dernier_evenement, 4) = p_annee`) et le registre ne lit que
celle-là ; si la ligne n'y est pas : « Transaction introuvable dans le registre AAAA » (vu en maquette).
⚠ **Trouvé, PAS à moi, non touché** : le choix « Toutes les années » du registre fait la même lecture (4 paquets de
1 000 en parallèle, `p_annee` vide) : il dépasse très probablement le délai pour tout le monde. Non vérifié à l'écran (ça
changerait sa période gardée). À traiter à part.
⛔ **Défaut 2 (affichage)** : le vrai modèle écrit des titres « ### … » et une liste « - … » juste sous une phrase, sans
ligne vide → affichés bruts. **Corrigé** : la réponse est lue ligne par ligne (un titre = une ligne en gras, une liste
commence à sa première puce). Build vert.
Reste à prouver après le push : la fiche d'une vraie chaîne qui s'ouvre, et les liens recherche / rendez-vous / demande en vrai.

## 22. Lot 3b — la preuve FINIE chez lui (16/11), un 3e défaut trouvé et corrigé en local

`a2812ba` (année de la chaîne ; titres et listes) est parti avec les commits GED (`c77ca7e` dessous, poussés par la
session GED avec son `b5f390c` au-dessus, sur son « Oui, les deux »). Vercel servi. Dans son Chrome, en lecture seule :
- la conversation 62965 rouverte : titres en gras, offres et agenda EN LISTES (le rendu ligne à ligne marche sur le vrai
  texte) ; « Offre de 79 000 € » → le registre des transactions ouvre **la fiche de la chaîne 1001409** (« Offre refusée ·
  26/10/2026 · 79 000 € », acquéreur M. Cinquieme ESSAI 8 CINQ) — plus de délai dépassé ;
- « Trois choses, avec leurs liens : mon rendez-vous « Essai assistant 3c », la recherche du contact 10354641, et la
  demande à la direction en attente » → le vrai modèle a écrit les TROIS formes (`rdv:`, `recherche:`, `demande:`) et le
  contact ; clics : agenda au **2026-11-18** ; recherche → fiche du contact **10354641** ; demande → **Suivi**, fiche
  `annonce=1068399` (VA6482, la demande du 02/06).
⚠ L'agenda affiche « Agenda non chargé » — IDENTIQUE quand on l'ouvre par le rail : comportement de l'écran (Actualiser),
pas du lien.
⛔ **Défaut 3 (le mien)** : rouvert ensuite par le rail, l'agenda restait au 18/11 — le jour du lien restait en mémoire
d'App et l'écran le relit à son montage (même risque pour la chaîne du registre). **Corrigé** : le point de départ
s'oublie dès qu'on quitte l'écran visé (App.tsx, effet sur `screen`). Vérifié en maquette : lien → 18/11, puis Contacts,
puis Agenda par le rail → la date par défaut de l'écran (17/11), plus le 18. Build vert. Rien écrit en production.
✅ `e8ae253` poussé avec `b936e9d` (GED, dessous, sur « Oui, les deux ») ; Vercel READY sur e8ae253. ➡ **Lot 3b CLOS.**
Restent : 4 (Citer un bien, Rechercher ou demander), 5 (téléphone), 6 (gestes par l'écran) ; options : le fil
« ‹ Conversation » ; la consigne des liens pas suivie à chaque fois (agenda listé sans `rdv:` une fois sur deux).

## 23. Lot 4 — Citer un bien ou un contact, Rechercher ou demander : AUDIT (16/11, sur « Lot 4, Citer »), rien codé

**Périmètre** : la planche 5 (« Rechercher partout » avec « Demander à l'assistant »), la planche 1 (le bouton « Citer un
bien ou un contact » du champ), `RechercheGlobale.tsx` (365 lignes) et son branchement dans App (une seule fenêtre, ouverte
par le rail, le « / », et les boutons de recherche du tableau de bord et du téléphone). Pas de serveur.

**Ce que le code dit** : la fenêtre « Rechercher partout » cherche dès 3 caractères dans les annonces (vivantes et
archives), les contacts et les mandats ; ↑ ↓ pour choisir, ↵ pour OUVRIR la fiche (props `onOuvrirAnnonce`,
`onOuvrirContact`, `onOuvrirMandat`…). Elle sert à TOUS, sur tous les écrans, téléphone compris (bouton de recherche du
`MobileLayout`).

**Le plan proposé**
1. « Demander à l'assistant » (planche 5) : une ligne en tête des résultats dès qu'un mot est tapé — « « Chaise-Dieu » :
   il cherche, compte, ou prépare un geste à valider » — et Ctrl ↵. Clic : la fenêtre se ferme, l'Accueil s'ouvre sur une
   NOUVELLE conversation, et la question part. Seulement si l'écran de l'assistant est allumé pour la personne ET au
   bureau (le téléphone n'a pas encore l'écran de l'assistant : lot 5).
2. « Citer un bien ou un contact » (planche 1) : un bouton dans le champ de l'assistant qui ouvre LA MÊME fenêtre en mode
   « citer » (titre « Citer un bien ou un contact », ↵ « citer ») : choisir une fiche INSÈRE dans la question
   « l'annonce 63289 », « Mme CLAUDE TESTCLAUDE (contact 10354641) » ou « le mandat 18787 » — les formes que les consignes
   font déjà comprendre au modèle ; rien n'est envoyé tout seul.
3. `RechercheGlobale` reçoit deux propriétés optionnelles (`onDemander`, `mode`) ; absentes = la fenêtre d'aujourd'hui,
   à l'identique.

**À trancher par lui** : « Demander à l'assistant » envoie-t-il la question TOUT DE SUITE (planche 5, recommandé) ou
seulement la met-il dans le champ ?

**Ce que ça pourrait casser ailleurs** : la fenêtre de recherche est celle de tout le monde — ses deux ajouts ne jouent
que si on les lui donne ; Ctrl ↵ n'existe que quand la ligne « Demander » est là ; le téléphone ne reçoit pas la ligne.

**⚠ Trouvé en passant (sa question du 16/11 : « est-ce normal que l'assistant ne peut pas faire un bon de visite ? »)** :
c'est une DÉCISION écrite, mais mon plan de l'étape 4 (§11) l'a OUBLIÉE. Le bon de visite n'existe qu'à l'écran : une page
HTML construite dans le navigateur et imprimée (`visitVoucherHtml` / `openVisitVoucherPrint`, App.tsx ~45710), sans PDF
ni rien d'enregistré côté serveur. L'audit du lot 3c (note de l'étape 3, §26 option E) avait dit : « le bouton qui ouvre
le bon de visite de l'écran arrivera avec l'écran (étape 4) ; un PDF fabriqué par le worker serait un nouveau type de
travail (à décider) ». Les consignes le disent au modèle (« le bon de visite : dis que tu ne peux pas encore »).
➡ À remettre au plan : soit A, une carte « Bon de visite » qui ouvre le bon de l'écran (même modèle, impression) après un
rendez-vous de visite — avec le lot 6 (gestes par l'écran) ; soit B, un vrai PDF fabriqué côté serveur, joignable à un
e-mail (plus lourd, nouveau type de travail).

## 24. Bon de visite, estimation, mandat : ce que l'assistant ne fait pas, et pourquoi (16/11, ses questions)

Ses mots : « Mais le bon de visite existe déjà je veux juste réutiliser la fonction ; et faire une estimation ou faire un
mandat, l'assistant ne sait pas faire ? »
- **Bon de visite** : ✅ **tranché = A**, réutiliser la fonction de l'écran (`openVisitVoucherPrint`, même modèle,
  impression), pas de PDF serveur.
- **Estimation (créer une annonce)** : NON aujourd'hui, par décision du 15/11 (note de l'étape 3, §22) : parmi A (retirer
  la carte « activer un brouillon » + AJOUTER « créer une annonce / une estimation »), B (retirer seulement), C, il a
  répondu « B » — rien n'a été ajouté. (Ses mots ce jour-là : « uniquement ajout annonce ou estimation cela suffit ».)
- **Mandat** : NON aujourd'hui, par le plan de l'étape 3 (§13, « 4c — pas par l'assistant pour l'instant ») : le numéro de
  mandat est officiel et irréversible, le document de mandat et l'avenant sont rendus par le navigateur, et l'envoi en
  signature part vers un signataire.
➡ Les trois ont la même forme : des gestes que l'ÉCRAN orchestre (fenêtre, document rendu par le navigateur). Proposé :
les mettre au **lot 6** (« gestes par l'écran ») — la carte de l'assistant ouvre la fenêtre de l'écran DÉJÀ REMPLIE
(création d'une estimation ; éditeur du mandat du bien ; bon de visite après un rendez-vous), la personne relit et valide
DANS la fenêtre, comme aujourd'hui. Rien ne s'écrit sans elle, les gardes de l'écran restent les mêmes.

## 25. ⛔ CORRECTION du §24 — l'inventaire, GESTE PAR GESTE, de ce que l'assistant fait (16/11)

Ses mots : « ajouter une annonce ou ajouter une estimation, ce n'est pas la même chose que générer l'estimation PDF ;
c'est comme générer le numéro de mandat, ce n'est pas la même chose qu'éditer le document et même l'envoyer en
signature. On a pourtant fait un audit des gestes de mon app : l'assistant, c'est faire quoi ? »
⛔ Mon §24 MÉLANGEAIT des gestes distincts (créer la fiche ≠ générer l'avis de valeur ; numéro de mandat ≠ document ≠
signature). Le voici refait, geste par geste, sur le catalogue de l'audit
(`notice/ETAPE3_CATALOGUE_COMPLET_DES_ACTIONS_2026-11-13.md` §1-3) croisé avec le CODE (`assistant_gestes.py` : 26 gestes ;
`assistant_lecteur.py` + 5 lectures). Légende : FAIT (en ligne, prouvé) · NON (décision, citée) · PAS FAIT (jamais
décidé ni codé) · ÉCRAN (le geste est orchestré par l'écran : carte qui ouvre sa fenêtre remplie, lot 6).

**Demandes à la direction** : demander validation / baisse / annulation = FAIT · corriger une demande renvoyée = NON (la
base le réserve à la direction, même à l'écran) · traiter (accepter / refuser) [DIR] = ÉCRAN.
**Diffusion** : publier / retirer UN portail = FAIT · « Validation » et « Diffusable » [DIR] = PAS FAIT.
**Annonce** : CRÉER une annonce ou une estimation (la fiche) = PAS FAIT (la carte « activer un brouillon » a été retirée le
15/11 sur « B » ; l'AJOUT de la création n'avait pas été retenu ce jour-là) · modifier les champs (23, liste fermée, prix
exclu) = FAIT · rédiger titre et texte = FAIT (proposition) · activer un brouillon = NON (15/11) · statut offre /
compromis / vente = ÉCRAN · Vendu, Clos, archiver, désarchiver, supprimer, réaffecter le négociateur = PAS FAIT.
**Photos** : couverture, masquer / afficher, déplacer = FAIT · synchroniser = PAS FAIT · supprimer = NON (lot 4c) · ajouter
(un fichier) = PAS FAIT.
**Documents** : GÉNÉRER l'avis de valeur PDF (l'estimation) = PAS FAIT · plan cadastral = PAS FAIT · préparer / ouvrir /
supprimer = PAS FAIT · déposer (un fichier) = PAS FAIT.
**Mandat** : GÉNÉRER LE NUMÉRO = PAS FAIT (laissé « pour l'instant », lot 4c : officiel, irréversible) · ÉDITER le document /
l'avenant = PAS FAIT (lot 4c ; rendu par le navigateur → ÉCRAN) · ENVOYER en signature, relancer, annuler, « signé à la
main » = PAS FAIT (lot 4c) · clôture par la demande d'annulation = FAIT · corriger une date de clôture [DIR] = PAS FAIT ·
modifier / prolonger = NON (⑦-7).
**Mandants** : rattacher, créer, modifier, retirer = PAS FAIT.
**Transactions** [DIR] : accepter / refuser une offre, annuler un compromis = FAIT · note de transaction = FAIT · créer
une offre / un compromis / une vente = ÉCRAN · supprimer un compromis ou une vente, commission, répartition, conditions =
PAS FAIT.
**Contacts** : créer (avec sa 1re recherche) = FAIT · modifier téléphone / e-mail / commentaire = FAIT · archiver /
réactiver = FAIT · ajouter un conjoint, supprimer = PAS FAIT.
**Recherches** : créer, modifier, archiver = FAIT.
**Rapprochements** : bien proposé par téléphone, écarter / rétablir = FAIT · e-mail de rapprochement (aperçu puis envoi
réel) = FAIT.
**Relances** : créer, faite, reportée = FAIT.
**Agenda** : créer dans SON agenda, déplacer / supprimer ceux posés par l'app sans invité = FAIT · rendez-vous avec le
client invité = FAIT · l'agenda d'un collègue = PAS FAIT · BON DE VISITE = ÉCRAN (tranché « A » : réutiliser
`openVisitVoucherPrint`).
**E-mails** : interne (collègues) = FAIT · au client (adresse de sa fiche, sans pièce jointe) = FAIT · pièces jointes,
e-mail d'estimation = PAS FAIT.
**Espace client** (confirmer un créneau) = NON pour l'instant (lot 3c option D, 3 demandes en tout).
**Partenaires, Santé, Matterport** = PAS FAIT. **Notifications** : marquer lues = FAIT. **Utilisateurs** = NON (29/10).
**Lectures** (ce qu'il sait lire) : 15 objets (biens, historique, archives, mandats, contacts, recherches, relations,
rapprochements, relances, transactions, dossiers, demandes, documents, notifications, négociateurs), les fiches des
biens, les notes de transaction, son agenda, les photos et les portails d'un bien, l'aperçu d'un rapprochement.

**En résumé** : l'assistant fait **26 gestes** (dont 3 réservés à la direction) ; quelques-uns sont **fermés par
décision** (cités ci-dessus) ; les « ÉCRAN » vont au lot 6 ; tout le reste n'a **jamais été décidé** — dont ceux qu'il cite : créer
une annonce / une estimation, générer l'avis de valeur PDF, générer le numéro de mandat, éditer le document de mandat,
l'envoyer en signature.

## 26. Annonce et mandat, geste par geste : AUDIT (16/11, sur « Annonce et mandat »), rien codé

**Périmètre** : créer une annonce / une estimation, générer l'avis de valeur PDF, générer le numéro de mandat, éditer le
document de mandat / l'avenant, l'envoyer en signature (relancer, annuler). Lu dans `lib/api.ts`, le worker
(`Console/console_job_worker.js`) et la base. Pas mesuré : « signé à la main », les mandants, le cadastre.

1. **Créer une annonce ou une estimation (la fiche)** — l'écran appelle `app_create_annonce_job_optimistic(p_token,
   p_fields, draft_payload, draft_priority)` (lib/api.ts ~13072) : la ligne provisoire chez nous À L'INSTANT et le travail de
   création chez Hektor, dans UNE transaction ; `creation_status` = estimation ou actif ; la charge (~60 champs) est
   construite dans `createHektorDraftAnnonceJob`. ➡ **Faisable en CARTE DIRECTE** (même fonction, avec le jeton de la
   personne) : type, famille d'offre, adresse / CP / commune, prix, surface, pièces, négociateur, mandant initial ; le reste
   vide (complété ensuite à l'écran ou par la carte « modifier le bien »). Réversible (supprimer = direction). ⚠ À éprouver
   avant d'ouvrir (le worker de création exige des champs — « Nom contact requis », l'orpheline après `ajoutebien`).
2. **Générer l'avis de valeur PDF** — travail `generate_estimation_pdf` (worker), dont la charge est ASSEMBLÉE PAR
   L'ÉCRAN : valeurs basse / estimée / haute, état, points forts et de vigilance, charges, comparables DVF, cadre de vie
   (carte IGN, commodités, risques), cadastre, argumentaire (lib/api.ts ~9340). ➡ **Par l'ÉCRAN** : la carte ouvre l'éditeur
   de l'avis de valeur du bien, prérempli de ce que l'assistant sait (valeurs, commentaire) ; la personne relit et génère.
3. **Générer le numéro de mandat** — `app_console_create_mandat_auto_number_job(target_app_dossier_id,
   target_hektor_annonce_id, mandat_payload, job_priority)` (lib/api.ts ~12272) : type / sous-type, date de début, durée
   (12 par défaut), tacite reconduction, mandants, négociateur → réservation officielle chez Hektor (Protexa),
   **IRRÉVERSIBLE**. ➡ **Faisable en CARTE DIRECTE** (même fonction), la carte disant en clair « numéro officiel, ne se défait
   pas » ; mêmes conditions que l'écran (à relire au code de l'écran avant de coder).
4. **Éditer le document de mandat / l'avenant** — travail `generate_mandat_document` ; le worker EXIGE le HTML rendu
   côté écran (« payload_json.html requis (HTML du mandat rendu cote front) », worker ~9310). ➡ **Par l'ÉCRAN** : la carte
   ouvre l'éditeur du mandat du bien.
5. **Envoyer en signature, relancer, annuler** — travaux `youtrust_send_signature` (le numéro du document + corrections
   d'e-mail / portable par rang), `relance_signature`, `cancel_signature_procedure` (lib/api.ts ~10290-10534). ➡ **Faisable
   en CARTES DIRECTES** (mêmes travaux), MAIS ça part VERS LES SIGNATAIRES (e-mails, SMS) : même prudence que le lot 3c
   (preuve sur un document d'essai à adresse interne).

**À trancher par lui** : l'ordre ; et pour 1, 3 et 5 : carte directe (recommandé) ou, comme 2 et 4, par la fenêtre de
l'écran. Ces gestes complètent l'ÉTAPE 3 (serveur) pour 1, 3, 5 et le LOT 6 de l'étape 4 (écran) pour 2 et 4 ; le bon de
visite (A) rejoint le lot 6.

## 27. Lot 4 — CODÉ et CONTRÔLÉ (16/11, sur « Je suis ta reco pour le lot 4 et ensuite enchaîne les cartes »), rien poussé

Tranché : « Demander à l'assistant » ENVOIE la question tout de suite (planche 5).
- `RechercheGlobale.tsx` (fins de ligne Windows gardées) : deux propriétés OPTIONNELLES — `onDemander` (la ligne « Demander
  à l'assistant » en tête dès qu'un mot est tapé, Ctrl ↵, pied « Ctrl ↵ demander à l'assistant ») et `onCiter` (mode
  « citer » : titre « Citer un bien ou un contact », ↵ « citer », choisir = insérer « l'annonce N », « NOM (contact N) »,
  « le mandat N », ou « le bien « titre » » sans numéro Hektor) ; absentes = la fenêtre d'aujourd'hui. Style dans
  `recherche-globale.css`.
- `RailAssistant.tsx` : `demanderAssistant` (la question GARDÉE jusqu'à ce que l'Accueil soit monté) et `citerDansAssistant`.
- `AccueilAssistant.tsx` : le champ de l'accueil suit la planche 1 (le champ, puis « Citer un bien ou un contact » à gauche
  et l'envoi à droite ; pas dans le champ de la conversation, comme la planche 3) ; la question venue de la recherche ouvre
  une NOUVELLE conversation et part ; la citation s'ajoute au champ sans rien envoyer.
- `App.tsx` : `onDemander` seulement si l'écran de l'assistant est allumé ET au bureau (`responsiveExperience.isDesktop`) ;
  `onCiter` seulement quand la fenêtre est ouverte par le bouton « Citer ».
⛔ **Trouvé en contrôlant (le mien), corrigé** : la question partait, puis la conversation GARDÉE (sessionStorage) était
rouverte par-dessus et la coupait — l'effet de démarrage, rejoué par le mode strict de React, la retrouvait. Une conversation
gardée ne se rouvre plus que si l'écran n'en a pas déjà une.
**Contrôlé (maquette)** : planche 5 à l'identique ; Ctrl ↵ depuis Annonces → Accueil, conversation « Chaise-Dieu »,
réponse ; « Citer » → la fenêtre en mode citer, ↵ → « Prépare une relance pour l'annonce 21 » dans le champ, rien envoyé ;
la recherche normale reste « Rechercher partout » ; au format téléphone (375 px) : pas de ligne « Demander », pied
d'aujourd'hui. Build vert. **Pas encore vérifié** : en ligne.

## 28. Carte « créer une annonce ou une estimation » : AUDIT FIN (16/11, sur « Oui enchaîne »), rien codé

Lot 4 commité en local `0286cdb` ; PAS poussé : deux commits d'autres sessions sont dessous (`8af44f1` classeur,
`c0f09fa` GED) — sa décision.

**Ce que fait la fenêtre de création de l'écran** (`handleCreateDraftAnnonce`, App.tsx ~18446) — 4 étapes, et elle exige :
l'AGENCE ; le NÉGOCIATEUR Hektor (`idUser` + `hektorNegociateurId` + libellé + e-mail ; un négociateur ne peut choisir
que lui-même) ; la NATURE (`draftAnnonceTypeId` → un PROFIL de règles : surface habitable / terrain / garage, pièces,
chambres, niveaux, jardin et piscine, exposition, vue — `draftAnnonceTypeProfile`) et la variante immo pro (idType 23 +
sous-type) ; adresse / CP / ville ; prix ; les champs « avancés » de la nature ; la composition des pièces ; les PHOTOS
(des fichiers) ; un mandant initial (existant, ou nouveau : nom + e-mail au minimum). Tout part en noms de cases Hektor
(`hektor_wizard_fields`). Mesuré : **21 créations en 90 jours, 2 en erreur**, la dernière le 08/11.

**Deux façons de faire**
- A — **carte directe** : le serveur refait un SOUS-ENSEMBLE de la fenêtre (liste fermée de natures avec leurs règles,
  négociateur = la personne ou un nom de l'annuaire pour la direction, adresse vérifiée comme pour un contact, prix,
  surface, pièces, chambres, terrain, mandant existant) puis appelle `app_create_annonce_job_optimistic`. ⚠ Cela RECOPIE les
  règles par nature côté serveur : deux portes sur la même création, qui peuvent diverger (leçon déjà payée) ; ni photos,
  ni composition, ni champs avancés.
- B — **par la fenêtre de l'écran** (lot 6) : la carte ouvre « Nouvelle annonce / estimation » DÉJÀ REMPLIE de ce que
  l'assistant a compris (nature, adresse, prix, surfaces, mandant…) ; la personne complète (photos, mandant, composition)
  et clique « Créer » : les MÊMES règles, la même validation, rien de recopié.
⭐ **Recommandé : B** — je reviens sur ma recommandation du §26 (« carte directe ») après avoir lu la fenêtre : la création
est trop liée aux règles par nature et aux fichiers pour être refaite sans risque côté serveur.
Les cartes directes qui restent : 3 (numéro de mandat) et 5 (signature) ; 2, 4, le bon de visite et la création (B) vont
au lot 6.

## 29. Lot 4 — EN LIGNE et PROUVÉ chez lui (16/11, « Oui les trois »)

Les deux commits d'autres sessions avaient été poussés par elles entre-temps : seul `0286cdb` restait, poussé. Vercel
servi. Dans son Chrome, en lecture seule :
- écran Annonces → « Rechercher partout » → « Chaise-Dieu » : la ligne « Demander à l'assistant … Ctrl ↵ » en tête, puis
  15 résultats — la planche 5 à l'identique ; clic → l'Accueil, NOUVELLE conversation « Chaise-Dieu », le vrai modèle
  répond (il demande une précision : « les biens en vente, les mandats ou autre chose ? ») ;
- Nouvelle conversation → « Citer un bien ou un contact » → la fenêtre « Citer… » → « 63330 » → la fiche « ESSAI 8A2B
  TOUS CHAMPS » → le champ contient « l'annonce 63330 », RIEN envoyé ; l'accueil a son bouton « Citer » (planche 1).
Rien écrit en production. ➡ **Lot 4 CLOS.**
**En attente de lui** : la création d'une annonce / estimation par la fenêtre de l'écran (B, recommandé, §28) ou en
carte directe ; puis les cartes directes « numéro de mandat » et « signature ».
✅ **Tranché le 16/11 (« Par la fenêtre »)** : créer une annonce / une estimation passera par la FENÊTRE de l'écran, déjà
remplie (lot 6), pas par une carte directe.

## 30. Carte « numéro de mandat » : CODÉE (16/11, sur « enchaîne les cartes »), rien poussé

**Audit fin** : l'écran (`HektorMandatNumberForm`, App.tsx ~3920) exige : pas de numéro déjà présent (sauf son mode « nouveau
mandat », à part), au moins un mandant, un négociateur ; il demande une confirmation (« action officielle, non annulable ») ;
puis `createHektorMandatAutoNumberJob` → `app_console_create_mandat_auto_number_job` (contrôle des droits par
`app_console_can_request_job`), travail `create_hektor_mandat_auto_number` → le worker réserve le numéro chez Hektor
(Protexa) et retrouve LUI-MÊME les mandants du bien si la liste est vide (worker ~19182).
**La carte** (`assistant_gestes.py`, `numero_mandat`, tous les rôles) : à la carte ET au clic, les gardes de l'écran
(numéro absent, mandant, négociateur) ; Mandat de vente et ses 12 sous-types seulement ; date de début (défaut aujourd'hui),
durée 1-120 mois (défaut 12), tacite reconduction (défaut oui) ; le résumé NOMME les mandants et dit « NE SE DÉFAIT PAS » ;
au clic, la même fonction de la base avec le jeton de la personne, la même charge que l'écran (mandants laissés au worker,
négociateur du bien). Consignes à jour (et la liste de ce qu'il ne fait pas : document de mandat, avenant, nouveau mandat,
créer une annonce, avis de valeur). Écran : titre « Numéro de mandat (irréversible) », fin « Numéro demandé à Hektor ».
⛔ **Trouvé en mesurant (le mien), corrigé AVANT tout essai réel** : un bien SANS numéro porte ses vendeurs en
« proprietaire », jamais en « mandant » (mesuré le 08/10 : « mandant » = déjà numéroté). Ma garde ne cherchait que
« mandant » : elle aurait refusé TOUS les biens. Elle prend maintenant les deux rôles, comme `ROLES_MANDANT` du push.
**Essais** : 234 + 61 + 73 verts ; témoin inverse (garde « déjà un numéro » retirée → rouge). Build vert.
**Pas éprouvé en réel** : le clic réserve un VRAI numéro officiel, irréversible — sa décision (bien et moment).

## 31. Carte « numéro de mandat » — EN LIGNE (`5d730d0`) et PROUVÉE SANS VALIDER (16/11, « Oui sans valider »)

Les commits GED dessous avaient été poussés par leur session : seul `5d730d0` est parti. Render `/health` = 5d730d0f4328,
Vercel servi. Dans son Chrome : « Prépare la carte pour générer le numéro de mandat du bien d'essai 62965 (mandat de vente,
à partir d'aujourd'hui, 12 mois). C'est un essai : je vais la refuser. » → la carte « Numéro de mandat (irréversible) » :
« Générer le NUMÉRO DE MANDAT officiel de l'annonce 62965 « TEST C13 cloture mandat - a supprimer » — Mandat de vente, à
partir du 16/11/2026, 12 mois, avec tacite reconduction ; mandant(s) : Mme. CLAUDE TESTCLAUDE. ⚠ … cela NE SE DÉFAIT
PAS. » + « Ouvrir l'annonce 62965 » ; le « 1 » sur la maison du rail. ⭐ Le mandant a été trouvé en rôle
« proprietaire » (la correction du §30 a servi). Le modèle a lui-même redit que c'est irréversible.
**Refuser** (jamais Valider) → « Refusée à 17:57 », le « 1 » s'éteint. Témoins en base : la carte `refusee`, sans
résultat ; **0 travail `create_hektor_mandat_auto_number`** depuis 24 h (témoin positif : la même requête en trouve 3 sur
120 jours, le dernier le 28/08) ; 62965 toujours SANS numéro. Rien réservé chez Hektor, rien écrit en production.
Le clic « Valider » réel reste à faire le jour d'un vrai mandat, sur sa décision.

## 32. Cartes « signature » (envoyer, relancer, annuler) : AUDIT (16/11, sur « Vas y »), rien codé

**Périmètre** : l'envoi Youtrust, la relance et l'annulation (Youtrust et ImmoSign), dans `lib/api.ts` (~10250-10545),
`SuiviSignatairesYoutrust.tsx`, `lib/suiviSignataires.ts`, et la base. Pas mesuré : « signé à la main ».
**Ce que fait l'écran**
- **Envoyer (Youtrust)** — la FENÊTRE D'ENVOI (A.2 lot 6b) : les signataires viennent de la « photo » du PDF
  (`metadata_json.signataires_du_pdf`, valide / problèmes / repères attendus), la personne corrige au plus l'e-mail et le
  portable d'un rang, accepte des écarts, choisit le code du mandataire ; puis le travail `youtrust_send_signature`.
- **Relancer UN signataire (Youtrust)** — `youtrust_remind_signer` (demande + signataire), seulement si la demande est
  `ongoing` ET le signataire `notified` (`lib/suiviSignataires.ts`) ; confirmation « Renvoyer le lien de signature à X ».
- **Annuler la signature (Youtrust)** — `youtrust_cancel_signature`, demande `ongoing` ou `approval` ; le document redevient
  « à signer ». Les gestes Youtrust ne s'affichent que si l'interrupteur `signature_youtrust` est allumé — **aujourd'hui
  `admin`** — et le worker les refuse sinon.
- **ImmoSign** (l'ancien prestataire) : relance `relance_signature`, annulation `cancel_signature_procedure`.
**Mesuré** : `app_signature_request` = **3 demandes en tout** (2 annulées, 1 signée), la dernière le 06/11 ; en 90 jours :
4 envois, 2 relances, 2 annulations Youtrust (tous des essais du 05-06/11), 2 annulations ImmoSign, **0 relance ImmoSign** ;
**aucune demande en cours aujourd'hui**.
**Le plan proposé**
- ENVOYER → **par la fenêtre de l'écran** (lot 6) : elle porte la photo du PDF, les corrections et les écarts.
- RELANCER et ANNULER (Youtrust) → **cartes directes** : mêmes règles (`ongoing` + `notified` ; `ongoing` / `approval`),
  MÊME interrupteur (`signature_youtrust`, donc admins seuls aujourd'hui), mêmes travaux, la carte NOMME le signataire et
  le document. ⚠ Ça part chez le signataire (e-mail Youtrust).
- ImmoSign : laissé (ancien prestataire, 0 relance en 90 jours).
**Comment on prouvera** : il n'y a AUCUNE demande en cours ; une preuve en réel demande d'abord un envoi de test (un
document d'essai, signataire à adresse interne), sur sa décision. Sinon : essais hors ligne seulement, preuve plus tard.

## 33. Cartes « relancer un signataire » et « annuler la signature » (Youtrust) : CODÉES (16/11, « on finit les cartes »)

Il a d'abord demandé « pourquoi la nouvelle vue n'est pas sur téléphone ? » : c'est le lot 5 (affichage téléphone à part,
`MobileLayout`, planches 7-9 bis), pas encore fait ; il a choisi de finir d'abord les cartes.
**Serveur** (`assistant_gestes.py`, `relance_signature` et `annulation_signature`, tous les rôles SOUS l'interrupteur) :
`signature_youtrust` relu à chaque carte et au clic (`on` = tous ; `admin` = les admins ; aujourd'hui `admin`) ; les
signatures Youtrust EN COURS du bien (documents dont `metadata_json.signature.provider = youtrust`, demande
`app_signature_request` en `ongoing` / `approval`), un morceau du nom du document départage ; relancer = le seul signataire
`notified` d'une demande `ongoing` (un morceau du nom départage) ; annuler = la demande. Au clic : tout est relu (même
document, même demande, même signataire encore `notified`), puis le travail de l'écran (`youtrust_remind_signer` /
`youtrust_cancel_signature`, charge de `poserTravailYoutrust`) avec le jeton de la personne. ⛔ L'e-mail d'un signataire
n'est JAMAIS dans la carte (le résumé repart au modèle). ImmoSign non ouvert ; l'ENVOI passe par la fenêtre (lot 6).
Consignes à jour. Écran : titres et fins des deux cartes.
**Essais** : 244 + 61 + 73 verts (section 13 : interrupteur, choix du signataire, `approval` = annuler mais pas relancer,
signature finie, charge du travail, témoin « a signé entre la carte et le clic → rien envoyé ») ; témoin inverse (la règle
`notified` retirée → rouge). Build vert. **Pas éprouvé en réel** : AUCUNE signature n'est en cours (3 demandes en tout,
dernière le 06/11) ; une preuve demande d'abord un envoi de test, sur sa décision.

## 34. ⭐ AUDIT : TOUS les gestes de l'app sont-ils accessibles à l'assistant ? (16/11, sa demande avant le lot 5)

**Périmètre et méthode** : recensé depuis le CODE, pas seulement depuis le catalogue du 13/11 — toutes les fonctions
d'écriture du front (`lib/api.ts`, `lib/ged.ts`, `lib/pilotage.ts`, et les appels directs des écrans : partenaires,
affaires apportées, syndic…), soit ~125 fonctions, dont une partie TECHNIQUE (relectures, synchronisations, aperçus,
lignes provisoires, ouverture d'un document) qui n'est pas un geste de la personne. Restent **76 gestes métier** (certaines
lignes en regroupent plusieurs proches), croisés avec les 29 gestes de l'assistant. Légende : FAIT · ÉCRAN (la carte ouvrira
la fenêtre de l'écran, lot 6) · NON (décision écrite) · PAS FAIT (jamais décidé ni codé).

**demandes**
- Demander validation / baisse de prix / annulation de mandat — FAIT
- Corriger une demande renvoyée — NON (décision)
- Traiter une demande (accepter / refuser, vérifications Hektor, e-mail de décision) [DIR] — ÉCRAN (lot 6)
**diffusion**
- Publier / retirer UN portail — FAIT
- Choisir PLUSIEURS portails et appliquer d'un coup — PAS FAIT
- Basculer « Validation » chez Hektor [DIR] — PAS FAIT
- Basculer « Diffusable » chez Hektor [DIR] — PAS FAIT
**annonce**
- Créer une annonce ou une estimation — ÉCRAN (lot 6)
- Remplir une annonce depuis la photo d'une fiche papier (scan) — PAS FAIT
- Modifier les champs (23, liste fermée, prix exclu) — FAIT
- Rédiger titre et texte (rédacteur) — FAIT
- Changer le statut : offre / compromis / vente — ÉCRAN (lot 6)
- Changer le statut : Actif, Estimation, Vendu, Clos (hors transactions) [DIR] — PAS FAIT
- Archiver une annonce [DIR] — PAS FAIT
- Désarchiver une annonce — PAS FAIT
- Supprimer une annonce [DIR] — PAS FAIT
- Réaffecter le négociateur [DIR] — PAS FAIT
- Activer un brouillon — NON (décision)
**photos**
- Couverture, masquer / afficher, déplacer — FAIT
- Ajouter une photo (un fichier) — PAS FAIT
- Supprimer une photo — NON (décision)
**estimation**
- Saisir les éléments de l'estimation (source, comparables, rédaction IA) — ÉCRAN (lot 6)
- Générer l'avis de valeur PDF — ÉCRAN (lot 6)
- Envoyer l'e-mail d'estimation au client — PAS FAIT
**documents**
- Générer le plan cadastral — PAS FAIT
- Déposer un document (un fichier) — PAS FAIT
- Supprimer un document — PAS FAIT
- GED : classer, décider, juger une pièce — PAS FAIT
**mandat**
- Générer le numéro de mandat — FAIT
- Éditer le document de mandat / l'avenant — ÉCRAN (lot 6)
- Clôturer par la demande d'annulation — FAIT
- Corriger une date de clôture [DIR] — PAS FAIT
- Écrire la charge des honoraires (qui paie) — PAS FAIT
- Modifier ou prolonger un mandat — NON (décision)
**signature**
- Envoyer en signature (Youtrust) — ÉCRAN (lot 6)
- Relancer un signataire (Youtrust) — FAIT
- Annuler la signature (Youtrust) — FAIT
- Relancer / annuler (ImmoSign, ancien prestataire) — PAS FAIT
- Marquer « signé à la main » — PAS FAIT
**mandants**
- Rattacher un mandant à un bien — PAS FAIT
- Retirer un mandant d'un bien — PAS FAIT
- Créer un mandant — PAS FAIT
- Modifier un mandant (dont son e-mail / portable pour la signature) — PAS FAIT
**transactions**
- Accepter / refuser une offre, annuler un compromis [DIR] — FAIT
- Note de transaction [DIR] — FAIT
- Créer une offre / un compromis / une vente [DIR] — ÉCRAN (lot 6)
- Modifier les champs d'une transaction [DIR] — PAS FAIT
- Conditions suspensives [DIR] — PAS FAIT
- Commission [DIR] — PAS FAIT
- Répartition des honoraires [DIR] — PAS FAIT
- Supprimer un compromis ou une vente [DIR] — PAS FAIT
- Trancher un écart (carnet, personnes) [ADMIN] — PAS FAIT
**contacts**
- Créer un contact (avec sa 1re recherche) — FAIT
- Modifier téléphone / e-mail / commentaire — FAIT
- Modifier l'adresse d'un contact existant — PAS FAIT
- Archiver / réactiver — FAIT
- Ajouter / modifier un conjoint — PAS FAIT
- Supprimer un contact [DIR] — PAS FAIT
**recherches**
- Créer, modifier, archiver une recherche — FAIT
- Supprimer une recherche — PAS FAIT
**rapprochement**
- Bien proposé par téléphone, écarter / rétablir — FAIT
- E-mail de rapprochement (aperçu puis envoi réel) — FAIT
**relances**
- Créer, faite, reportée — FAIT
**agenda**
- Rendez-vous dans SON agenda : créer, déplacer, supprimer — FAIT
- Rendez-vous avec le client invité — FAIT
- L'agenda d'un collègue [DIR] — PAS FAIT
- Bon de visite — ÉCRAN (lot 6)
**emails**
- E-mail interne aux collègues — FAIT
- E-mail au client (sans pièce jointe) — FAIT
- Pièces jointes (documents, photos) — PAS FAIT
**espace**
- Espace client : confirmer un créneau, répondre — NON (décision)
**partenaires**
- Syndic / diagnostiqueur d'un bien, métier, apporteur / courtier, notaire — PAS FAIT
**notifications**
- Marquer lues — FAIT
**sante**
- Alertes : prendre en charge, résoudre ; « j'ai refait » / abandonner un geste [ADMIN] — PAS FAIT
**matterport**
- En ligne, privé, archiver, réactiver — PAS FAIT
**utilisateurs**
- Gérer les utilisateurs — NON (décision)

**Compte** : 23 FAIT · 9 ÉCRAN (lot 6) · 6 NON · **38 PAS FAIT** (sur 76).

**Les « PAS FAIT », rangés par ce qu'il faudrait** :
- **Cartes directes possibles** (une fonction de la base ou une route du serveur existe et contrôle déjà) : réaffecter le
  négociateur, archiver / désarchiver une annonce, statut Actif / Estimation (⚠ Clos = les DEUX PORTES, chantier à part),
  Validation et Diffusable [DIR], plusieurs portails d'un coup, ajouter / modifier un conjoint, l'adresse d'un contact
  (communes vérifiées), supprimer une recherche, rattacher / retirer / créer / modifier un mandant, « signé à la main »,
  les champs, conditions, commission et répartition d'une transaction [DIR], corriger une date de clôture [DIR], la charge
  des honoraires, le plan cadastral, supprimer un document, l'e-mail d'estimation, l'agenda d'un collègue [DIR], les
  partenaires, les alertes de Santé [ADMIN], ImmoSign.
- **Demandent un FICHIER** (une photo, un document, une fiche papier, une pièce jointe) : impossible tant que la
  conversation ne reçoit pas de pièce jointe — un chantier à part (« déposer un fichier dans la conversation »).
- **Suppressions définitives** [DIR] (annonce, contact, compromis, vente) : le catalogue du 13/11 les mettait « plus
  tard » ; à décider une par une.
- **GED** (classer, décider, juger) : le chantier de la session GED, en cours — à voir avec elle.
- **Matterport** : l'API est hors service depuis le 03/11.

**Réponse à sa question** : NON, tous les gestes ne sont pas accessibles aujourd'hui — 23 le sont, 9 le seront par les
fenêtres (lot 6), 6 sont fermés par décision, 38 restent à décider. Ordre proposé : les cartes directes « sûres » par
famille (mandants, conjoint et adresse, annonce : négociateur / archivage / statut simple, transactions : champs et
conditions, documents simples), puis le lot 6 (fenêtres), puis le lot 5 (téléphone) — OU le lot 5 d'abord : SA décision.

## 35. Cartes directes, familles 1 à 3 (mandants, contacts, annonce) : AUDIT (16/11, sur « Carte directe »), rien codé

**Périmètre** : les fonctions de la base de ces gestes (définition lue en base le 16/11), leurs règles de droits
(`app_console_can_request_job` / `app_console_can_request_contact_job`), et ce que l'écran envoie. Pas mesuré : le volume.
**Règles de droits relues** (`app_console_can_request_job`) : archiver et changer le statut = admin / manager SEULEMENT ;
réaffecter le négociateur = admin / manager (absent de la liste du négociateur) ; rattacher / retirer / créer / modifier un
mandant, désarchiver = le négociateur sur SES biens.

**Famille 1 — mandants**
- rattacher un contact EXISTANT comme mandant : `app_link_mandant_optimistic` (contrôle de la base) ;
- retirer un mandant : `app_unlink_mandant_optimistic` (contrôle ; la base REFUSE si le mandat est numéroté) ;
- créer un mandant / modifier son e-mail ou portable : `app_create_mandant_contact_optimistic`,
  `app_update_mandant_contact_optimistic` — ⛔ **trouvé : ces deux fonctions NE CONTRÔLENT PAS l'appelant** (aucun appel
  de règle de droits dans leur définition ; le catalogue du 13/11 le signalait déjà pour « modifier »). Défaut EXISTANT,
  aussi vrai pour l'écran. La carte vérifierait le bien avec le jeton de la personne (elle ne le voit que si elle y a
  droit), mais le vrai remède est dans la base : ajouter le même contrôle que les autres (patch, son accord).
**Famille 2 — contacts**
- l'adresse d'un contact existant : `app_edit_contact_optimistic` (contrôle) avec adresse / code postal / ville, la ville
  vérifiée dans les communes du code postal (comme la création, lot 2c) — sinon Hektor garde l'ancienne (leçon du 22/10) ;
- ajouter un conjoint (deux contacts existants) : `app_ajouter_conjoint_optimistic` (contrôle) ; ⚠ le chantier des
  couples (fiches de couple, conjoints muets) est délicat : seulement « rattacher un conjoint existant », pas le modifier ;
- supprimer une recherche : ⛔ NON proposé — défaut CONNU « supprimer la 2e recherche vise la première » (index) ;
  l'archivage existe déjà (carte FAITE).
**Famille 3 — annonce** (direction)
- réaffecter le négociateur : `app_assign_negotiator_optimistic` (contrôle ; numéro Hektor du négociateur, pris dans
  l'annuaire) ;
- archiver / désarchiver : `app_archive_annonce_optimistic`, `app_restore_annonce_optimistic` (contrôle ; « déjà
  archivée » refusé par la base) ;
- statut Actif ↔ Estimation : `app_change_annonce_status_optimistic` (contrôle) ; ⚠ passer « Actif » REMET « diffusable »
  à 1 chez Hektor (mémoire « Le geste Actif remet diffusable à 1 ») : la carte le DIT ; « Clos » exclu (les deux portes),
  « Vendu » et les transactions passent par la fenêtre (lot 6).
**À trancher par lui** : (1) le contrôle manquant des deux fonctions « mandant » — patch de la base d'abord (recommandé),
ou cartes avec le seul contrôle de lecture ; (2) le reste tel que proposé.

## 36. Cartes directes, familles 1 à 3 : CODÉES (16/11, sur « Vas y »), testées hors ligne — pas encore en ligne

**Périmètre** : `assistant_gestes.py` (8 cartes), `assistant_service.py` (consignes), `AccueilAssistant.tsx` (titres et
phrases de fin), tests `test_assistant_gestes.py` §14 et `test_assistant_ia.py`. Rien n'est écrit en base ni chez Hektor.

**⛔ CORRECTION DU §35 — le contrôle des deux fonctions « mandant » EXISTE.** Le §35 disait que
`app_create_mandant_contact_optimistic` et `app_update_mandant_contact_optimistic` ne contrôlent pas l'appelant. C'est
FAUX : je n'avais lu que la fonction du dessus. Chacune appelle d'abord sa fonction interne
(`app_console_create_mandant_contact_job` / `app_console_create_update_mandant_contact_job`, relues en base le 16/11), qui
vérifie `app_console_can_request_job('create_hektor_mandant_contact' | 'update_hektor_mandant_contact', …)` et lève
`forbidden_…` ; l'appel est HORS de tout bloc d'exception, donc un refus annule toute la fonction avant la moindre
écriture. **Aucun patch n'est nécessaire.** (Le catalogue du 13/11 portait la même lecture incomplète pour « modifier ».)
Conséquence : les cartes « créer un mandant » et « modifier l'e-mail / le portable d'un mandant » ne sont plus bloquées —
elles ne sont PAS codées (pas dans le « Vas y »), à décider par lui.

**Les 8 cartes** (chacune appelle LA fonction de la base de l'écran avec le jeton de la personne ; gardes de l'écran
refaites à la carte ET au clic) :
- `rattacher_mandant` (tous) — `app_link_mandant_optimistic`, NOTRE numéro de contact (comme le sélecteur ; le worker
  traduit) ; refusé : contact archivé, fiche de ménage, contact d'un autre négociateur que celui du bien (le sélecteur ne
  montre que les siens), déjà mandant/propriétaire, bien sans négociateur ;
- `retirer_mandant` (tous) — `app_unlink_mandant_optimistic`, le numéro **HEKTOR** (`hektor_target_id`, celui que
  `degroupproprio` exige) ; refusé : mandat numéroté (avec le numéro), pas mandant du bien, contact sans numéro Hektor ;
  le refus `mandat_numerote_N` de la base est traduit en clair ;
- `adresse_contact` (tous) — `app_edit_contact_optimistic` {nom actuel, adresse, code postal, ville} ; la ville est
  vérifiée dans les communes du code postal et remplacée par le nom OFFICIEL (le worker la traduit en identifiants Hektor,
  `applyContactLocalityIds` ; mal écrite, elle partirait en texte seul et se perdrait) ;
- `ajouter_conjoint` (tous) — `app_ajouter_conjoint_optimistic`, deux fiches EXISTANTES, personnes seules ; interrupteur
  `contacts_couples_ajout` respecté ; la base refuse sans lever (ok = false) : la raison est dite en clair ;
- `reaffecter_negociateur` (direction) — `app_assign_negotiator_optimistic`, négociateurs du REGISTRE actifs chez Hektor
  (le menu de l'écran) ; deux fiches du même nom : l'agence départage ; charge identique à l'écran ;
- `archiver_annonce` (direction) — `app_archive_annonce_optimistic`, les 9 causes de la modale (le motif principal en
  découle), précision obligatoire pour « autre », prix et confrère seulement pour « vendu » ;
- `desarchiver_annonce` (tous) — `app_restore_annonce_optimistic` sur le numéro de l'index des archives ;
- `activer_estimation` (direction) — `app_change_annonce_status_optimistic` cible `active`, SEULEMENT depuis Estimation ;
  la carte dit que Hektor rend le bien diffusable. ⚠ **Il n'existe aucune cible « Estimation »** (ni ici ni à l'écran) :
  Actif → Estimation ne se fait pas.
- Garde « une action Hektor déjà en cours sur l'annonce » (celle de l'écran) pour l'archivage, le désarchivage et le statut.
- Limite : négociateur, archivage et statut seulement sur les biens VIVANTS (un vendu / clos passe par sa fiche).

**Contrôles** : `test_assistant_gestes` **288 verts** (dont §14 : 44 nouveaux, 4 témoins « le monde a changé entre la carte
et le clic -> refusé, RIEN envoyé ») ; **témoin inverse du test** : deux sabotages volontaires du code (envoyer notre
numéro au retrait ; retirer la garde « action en cours ») font virer la suite au ROUGE, puis code remis et 288 verts ;
`test_assistant_ia` 61 verts (avec le SDK) ; `test_assistant_lecteur` 73 verts ; `npm run build` vert. 37 gestes.
**Pas encore fait** : la mise en ligne (push, son accord) et la preuve en réel (une carte proposée, refusée « sans
valider », sur un bien d'essai).

## 37. Les droits par rôle : ce que la DIRECTION fait elle-même, ce que le NÉGOCIATEUR ne peut que DEMANDER — AUDIT (17/11)

**Demande de Frédéric** : « l'assistant doit s'adapter aux droits de l'utilisateur ; un admin peut faire certains gestes
que le négociateur peut juste demander ; auditer les demandes de validation, baisse, etc. ».
**Périmètre** : les 3 demandes à la direction (validation / diffusion, baisse de prix, annulation de mandat), leurs gestes
DIRECTS côté direction, leur traitement ; et les 37 cartes de l'assistant croisées avec `app_console_can_request_job` /
`_contact_job` (définitions relues en base le 17/11). Pas mesuré : les écrans hors annonces (agenda, GED, Santé).

**Ce que dit l'application (code et base, 17/11)**
- Les demandes (`app_diffusion_request`) : 3 types. Créer = toute personne sur un bien qu'elle peut voir (règle d'accès
  `requested_by = soi` + bien accessible) ; traiter (mettre à jour) = direction seulement (`is_app_manager_or_admin`).
  À l'écran, le menu des demandes (« Ajouter / Corriger / Envoyée ») est montré à TOUS sur la liste des annonces, admin
  compris ; le traitement est sur l'écran « Suivi », réservé à la direction.
- ⚠ **Le circuit dort** : 9 demandes en tout, toutes de Frédéric (4 baisses et 4 annulations acceptées les 13-14/05,
  1 validation en attente depuis le 02/06). Pauline n'en a jamais traité une. Ce que l'assistant enverra arrivera dans une
  file qui n'a jamais tourné en vrai.
- **Prix** : la base refuse le prix au négociateur (`prix_sur_demande`, décision B1 du 12/10) ; la DIRECTION le change
  DIRECTEMENT (`app_edit_annonce_optimistic`). ⚠ Accepter une demande de baisse NE CHANGE PAS le prix : l'écran vérifie
  que le prix de Hektor est déjà le prix demandé (`verifyPriceDropOnHektor`), puis propose d'activer les passerelles. La
  direction change donc le prix, PUIS accepte.
- **Validation et Diffusable** : la direction les coche DIRECTEMENT (le « Pilotage » de la fiche, `allowMarkValidation` /
  `allowMarkDiffusable` = manager ou admin) ; le négociateur passe par la demande de validation, dont l'acceptation lance
  la validation chez Hektor puis la diffusion et les passerelles (`acceptDiffusionRequestOnHektor`).
- **Annulation de mandat** : le négociateur demande ; la direction peut aussi clore par la modale de statut (« les deux
  portes », décision du 21/10 : on laisse comme aujourd'hui).
- **Réservé à la direction, sans demande possible pour le négociateur** : archiver, changer le statut (Estimation → Actif,
  offre, compromis, vente, clos), réaffecter le négociateur.

**Ce que fait l'assistant aujourd'hui**
- ✅ **Aucun dépassement côté négociateur** : chaque carte ouverte à tous correspond à un travail de sa liste dans la base
  (mandants, champs du bien sans prix, photos, numéro de mandat, désarchiver, signatures, contacts, recherches) ; la carte
  « portail » passe par la même garde que l'écran (bien diffusable ET le sien) ; les cartes de direction (transactions,
  note, réaffecter, archiver, Estimation → Actif) ne sont même pas montrées au négociateur, et la base les refuserait au clic.
- ⛔ **Écart 1 — le prix** : l'assistant interdit le prix à TOUT LE MONDE et ne propose que la demande de baisse. Un admin
  qui dit « baisse le prix à 150 000 » obtiendrait une demande… adressée à lui-même. La base, elle, l'autorise.
- ⛔ **Écart 2 — validation et diffusable** : aucune carte directe pour la direction ; seulement la demande de validation.
- ⛔ **Écart 3 — traiter une demande** (accepter / refuser / renvoyer à corriger) : aucune carte ; c'était prévu « par la
  fenêtre » au lot 6 (l'acceptation enchaîne des vérifications chez Hektor, des confirmations et un e-mail de décision).
- ⚠ **Écart 4 — la consigne** ne dit pas au modèle de proposer la DEMANDE qui correspond quand un négociateur réclame un
  geste de direction (« mets-le en diffusion » → demande de validation ; « baisse le prix » → demande de baisse ;
  « clôture le mandat » → demande d'annulation), ni à l'inverse de préférer le geste DIRECT pour la direction.

**À trancher par lui** (rien n'est codé) :
1. le prix en direct pour la direction (la carte « modifier le bien » accepterait le prix pour admin / manager, la base
   le refuse déjà au négociateur — double verrou) ;
2. validation et diffusable en direct pour la direction (à auditer d'abord : quelle écriture fait le Pilotage) ;
3. traiter une demande : garder « par la fenêtre » (lot 6) ou une carte ;
4. la consigne par rôle (écart 4) — sans risque, recommandé dans tous les cas.

## 38. La consigne par rôle et le prix pour la direction : CODÉS (17/11, sur « Consigne puis prix ») — pas encore en ligne

**Périmètre** : écarts 1 et 4 du §37 seulement. Les écarts 2 (validation / diffusable en direct) et 3 (traiter une
demande) ne sont PAS touchés.
- **La consigne par rôle** (`assistant_service.py`) : la direction FAIT, le négociateur DEMANDE. Au négociateur qui réclame
  un geste de direction, le modèle propose LA demande qui correspond (prix -> baisse de prix ; diffusion, validation,
  diffusable -> demande de validation ; clôture, annulation -> demande d'annulation ; archiver, statut, réaffecter, offre :
  « voir avec la direction », il n'y a pas de demande à l'écran). À la direction, le geste direct, jamais une demande
  adressée à elle-même ; Validation / Diffusable et le traitement des demandes restent dans l'application (Pilotage, Suivi).
  Vérifié : la fiche `assistant` de `app_agent_prompt` est VIDE, c'est donc bien le texte du code qui sert en ligne.
- **La carte `changer_prix`** (direction : admin, manager) : `app_edit_annonce_optimistic` avec la clé `price` de l'écran.
  Trois verrous : la carte n'est montrée qu'à la direction ; le serveur la refuse au clic à tout autre rôle ; la base
  refuse le prix au négociateur (`prix_sur_demande`). La carte dit l'ancien et le nouveau prix, SIGNALE (sans refuser) un
  écart de plus de 30 %, refuse le même prix, et dit qu'une demande de baisse en cours est à accepter ensuite dans Suivi
  (accepter ne change pas le prix). La carte « modifier le bien » n'a toujours pas le prix ; la demande de baisse reste
  ouverte à tous (l'écran la montre à tous), sa description dit que c'est le chemin du négociateur.
**Contrôles** : `test_assistant_gestes` 298 verts (§15 : 10 nouveaux, dont 2 témoins « le monde a changé au clic ») ;
témoin inverse : le 3e verrou saboté -> ROUGE, remis -> 298 ; `test_assistant_ia` 62 (la consigne par rôle, rôle rempli) ;
`test_assistant_lecteur` 73 ; `npm run build` vert. 38 gestes.

## 39. Épreuve en réel des 9 cartes, SANS VALIDER (17/11, 09:32-09:34, sur « Oui, sans valider ») — PROUVÉE

En production (Render `98199c3`), dans le Chrome de Frédéric (admin), 3 questions, 9 cartes, toutes REFUSÉES :
`changer_prix`, `activer_estimation`, `rattacher_mandant`, `archiver_annonce`, `reaffecter_negociateur` (bien d'essai
63330 « ESSAI 8A2B… ne pas diffuser ») ; `retirer_mandant` (62965 « TEST C13… à supprimer », Mme CLAUDE TESTCLAUDE) ;
`adresse_contact` et `ajouter_conjoint` (contacts d'essai 20000009 « Mandant ESSAI CONTACT » et 10354641) ;
`desarchiver_annonce` (24933, archive aux mandants de test). Les vraies personnes dont le nom contient « TEST » (TESTA,
TESTUT, TESTON) ont été écartées.
- Les 9 résumés étaient justes (ancien → nouveau prix, adresse avant → après, l'ancien et le nouveau négociateur, la
  diffusion rallumée par « Actif ») ; le modèle a relevé DE LUI-MÊME le « ne pas diffuser » du titre.
- **Base** : 9 lignes `app_assistant_action` en `refusee`, aucune exécutée ; **0 travail** posé entre 09:25 et la mesure
  (témoin : la même lecture voit 1 113 travaux sur 24 h, le dernier à 09:24:44) ; fiches inchangées (63330 Estimation,
  187 000 €, PEREIRA, non archivée ; adresse de 20000009 inchangée ; aucun couple ; aucune modification en attente ;
  TESTCLAUDE toujours liée à 62965 ; 24933 toujours archivée).
- ⚠ Défaut de forme trouvé : les textes des cartes accordent au masculin (« Mme … est aussi rattaché », « il disparaît »).
- Non prouvé : le chemin du NÉGOCIATEUR (la consigne par rôle, le refus de la carte prix) — il faut le témoin commercial.
- ⚠ Remarqué, hors sujet : Mme CLAUDE TESTCLAUDE (fiche de test) est MANDANT de l'annonce RÉELLE 24113.

## 40. L'inventaire des gestes REMIS À JOUR après §36-39 (17/11, sa demande : « les gestes avec carte et ceux sans »)

Base : l'inventaire du §34 (lu dans le code), plus les cartes posées depuis. 78 lignes au lieu de 76 : le prix pour la
direction est une ligne neuve, « Clos » et « le couple » sont séparés de leur ligne, et la ligne en double « créer une
offre / un compromis / une vente » est fusionnée. [DIR] = direction seulement.

**AVEC CARTE (32)** : demander validation / baisse / annulation (négociateur) ; un portail ; les champs du bien ; le prix
[DIR] ; rédiger titre et texte ; Estimation -> Actif [DIR] ; archiver [DIR] ; désarchiver ; réaffecter le négociateur
[DIR] ; photos (couverture, masquer / afficher, déplacer) ; numéro de mandat ; clôturer par la demande d'annulation ;
relancer un signataire ; annuler une signature Youtrust ; rattacher un mandant ; retirer un mandant ; accepter / refuser
une offre, annuler un compromis [DIR] ; note de transaction [DIR] ; créer un contact ; téléphone / e-mail / commentaire ;
adresse d'un contact ; archiver / réactiver un contact ; ajouter un conjoint existant ; créer / modifier / archiver une
recherche ; bien proposé, écarter / rétablir ; e-mail de rapprochement ; relances ; rendez-vous dans son agenda ;
rendez-vous avec le client ; e-mail interne ; e-mail au client ; notifications lues.
**PAR LA FENÊTRE, lot 6 (8)** : traiter une demande [DIR] ; créer une annonce ou une estimation ; offre / compromis /
vente [DIR] ; saisir l'estimation ; avis de valeur PDF ; document de mandat / avenant ; envoyer en signature ; bon de visite.
**FERMÉ PAR DÉCISION (7)** : corriger une demande renvoyée ; activer un brouillon ; supprimer une photo ; modifier ou
prolonger un mandat ; « Clos » par la modale de statut (les deux portes) ; espace client ; gérer les utilisateurs.
(« Actif -> Estimation » n'existe pas, ni à l'écran ni ici.)
**SANS CARTE, À DÉCIDER (31)** : Pilotage — cocher Validation [DIR], cocher Diffusable [DIR] ; plusieurs portails d'un
coup ; supprimer une annonce [DIR] ; créer un mandant, modifier son e-mail / portable (débloqués : le contrôle existe) ;
champs d'une transaction, conditions suspensives, commission, répartition [DIR] ; supprimer un compromis ou une vente
[DIR] ; trancher un écart [ADMIN] ; créer le conjoint, modifier ou défaire un couple ; supprimer un contact [DIR] ;
supprimer une recherche (défaut connu : l'index vise la 1re) ; corriger une date de clôture [DIR] ; charge des
honoraires ; signé à la main ; ImmoSign ; plan cadastral ; supprimer un document ; e-mail d'estimation ; agenda d'un
collègue [DIR] ; partenaires ; alertes de Santé [ADMIN] ; GED (chantier de sa session) ; Matterport (API hors service) ;
et ceux qui demandent un FICHIER : scan d'une fiche papier, ajouter une photo, déposer un document, pièces jointes.

**⏳ À FAIRE — décidé par Frédéric le 17/11** (sortis de « à décider ») :
1. **Pilotage** [DIR] : cocher Validation, cocher Diffusable — auditer d'abord l'écriture que fait le Pilotage de la fiche
   (`handleSetSelectedDossierValidation` / `handleSetSelectedDossierDiffusable`, App.tsx ~26359).
2. **Diffusion** (choisir plusieurs portails d'un coup) — **UNIQUEMENT si le bien est diffusable** (« voir projet ») : la
   règle existe déjà (la carte « un portail » et la route /apply de l'écran : négociateur = bien diffusable ET le sien).
3. **Ajouter une photo** et 4. **Ajouter un document** — ⚠ supposent que la conversation reçoive un FICHIER (aujourd'hui
   elle n'accepte que du texte) : c'est la première marche, à auditer avec eux.

**Précision du 17/11 (Frédéric)** : **ajouter une photo** et **ajouter un document** passent **PAR LA FENÊTRE de l'écran
(lot 6)** — elle sait déjà choisir le fichier, l'envoyer et le déposer chez Hektor ; une carte supposerait d'abord que la
conversation reçoive des fichiers. Les cartes photo existantes (couverture, masquer / afficher, déplacer) RESTENT des
cartes : en ligne, éprouvées, sans fichier. **Ordre : Pilotage, puis Diffusion (si diffusable).**

## 41. PILOTAGE (cocher Validation, cocher Diffusable) : AUDIT (17/11, « Pilotage d'abord ») — rien codé

**Périmètre** : les deux cases du Pilotage de la fiche (écran, serveur, pont Hektor). Pas mesuré : ce que Hektor fait des
portails déjà cochés quand Diffusable repasse à 1.
**Ce que fait l'écran** (`handleSetSelectedDossierValidation` / `…Diffusable`, App.tsx ~21481) : manager ou admin, biens
VIVANTS seulement (un vendu / clos est refusé avec un message). Deux appels au serveur Render :
- `/hektor-diffusion/validation` -> `HektorBridgeService.set_validation` : PATCH `PropertyValidation` chez Hektor, relit la
  fiche Hektor avant / après et rend la validation ET le diffusable OBSERVÉS ; ⚠ ne vérifie pas que l'observé = le demandé
  (seule une erreur de Hektor remonte) ;
- `/hektor-diffusion/diffusable` -> `set_diffusable` : PATCH Diffuse, relit, et rend une erreur si Hektor ne confirme pas ;
- puis `/hektor-diffusion/persist-state` : recopie l'OBSERVÉ chez nous (`app_dossier_current`) et pose le verrou de
  diffusion (la relecture de nuit ne l'écrase pas avant le délai de grâce).
- Les deux routes : `assert_admin` = rôle admin OU manager, profil actif. **Écriture DIRECTE et SYNCHRONE chez Hektor**,
  pas de travail du worker (déjà éprouvé pour Diffusable le 16/11 sur 61398, 0 -> 1 -> 0).
**Mesures** (biens vivants, 17/11) : 13 092 « à contrôler / 0 » ; 432 « validé / 1 » ; 29 « validé / 0 » ; 3 « à
contrôler / 1 ». Diffusable sans validation est donc RARE mais existe : la carte ne le refuse pas, elle prévient.

**La carte proposée — `pilotage` [DIR]** : sur un bien vivant, Validation (oui / non / inchangé) et Diffusable (oui / non /
inchangé). Au clic, avec la même garde que la route (`assert_admin`, jugée avec le jeton de la personne) : la validation
d'abord, puis le diffusable, par le MÊME pont que l'écran ; puis la recopie chez nous de ce que Hektor MONTRE. La carte
EXIGE que Hektor confirme (validation comprise, ce que l'écran ne fait pas) et dit ce qu'il montre sinon.
La carte DIT : Diffusable = 1 -> le bien peut repartir sur les portails déjà cochés ; Diffusable = 0 -> il sort de tous les
portails ; une demande de validation en cours sur le bien -> elle reste à traiter dans Suivi.
**Ce que ça pourrait casser ailleurs** : rien d'existant n'est modifié (une carte de plus qui appelle le pont de l'écran) ;
c'est un geste RÉEL chez Hektor au clic (la diffusion publique du bien) — d'où la direction seule et la confirmation exigée.
**Épreuve proposée** : d'abord « sans valider » ; un essai réel seulement sur un bien qu'il choisit (61398 a déjà servi).

## 42. La carte PILOTAGE : CODÉE (17/11, sur « Vas-y ») — pas encore en ligne

`pilotage` [DIR] : Validation et / ou Diffusable (oui / non / vide = inchangé), sur un bien vivant. Au clic : 3e verrou
(rôle), la garde des routes (`assert_admin`, jugée avec le jeton), la validation PUIS le diffusable par le pont de
l'écran (`set_validation`, `set_diffusable`, jamais à blanc), pas de second appel si Hektor rend déjà le bien diffusable
en le validant, puis la recopie chez nous de ce que Hektor MONTRE (`persist_state`, verrou de diffusion compris). La
carte EXIGE la confirmation des deux cases ; une validation partie mais pas relue est un REFUS (jamais un vert) ; un
refus de Hektor sur la validation arrête là. Le résumé dit avant -> après, « écrit directement chez Hektor », les
portails cochés qui repartent (Diffusable OUI), la sortie de tous les portails (NON), le cas rare « sans validation », et
une demande de validation en cours (à traiter dans Suivi). Consigne : la direction valide / rend diffusable par
`proposer_pilotage` ; le négociateur garde la demande de validation.
**Contrôles** : `test_assistant_gestes` 312 verts (§16 : 13 nouveaux, dont 3 témoins « rien chez Hektor ») ; témoin
inverse : la vérification de confirmation sabotée -> ROUGE, remise -> 312 ; `test_assistant_ia` 62 ; `test_assistant_lecteur`
73 ; `npm run build` vert. 39 gestes.

## 43. Épreuve de la carte PILOTAGE, SANS VALIDER (17/11, 10:10, sur « Oui, sans valider ») — PROUVÉE

En production (Render `d6566f2`), Chrome de Frédéric (admin), bien d'essai 63330. ⭐ Le modèle a d'abord DEMANDÉ
confirmation de lui-même (« le titre indique ne pas diffuser ; le pilotage écrira directement chez Hektor ; veux-tu quand
même ? ») ; après « c'est un essai », la carte : « Validation NON → OUI ; Diffusable NON → OUI. Écrit DIRECTEMENT chez
Hektor au clic, puis relu. ⚠ Diffusable OUI : le bien peut repartir sur les portails déjà cochés ». REFUSÉE à 10:10.
**Base** : la ligne `pilotage` en `refusee`, `execute_le` vide ; 63330 inchangé (`a_controler`, diffusable 0, aucun
portail) et sa date d'écriture `refreshed_at` toujours au 21/10 — la recopie du clic l'aurait changée (témoin : 7 biens
écrits sur 24 h, le dernier à 06:26). **Pas encore prouvé** : un clic RÉEL (Hektor confirme), sur un bien qu'il choisit.

## 44. DIFFUSION (plusieurs portails d'un coup, SI le bien est diffusable) : AUDIT (17/11, « Oui, la Diffusion ») — rien codé

**Périmètre** : la fenêtre « Diffusion » de l'écran, la route `/hektor-diffusion/apply` et le pont ; la carte « un portail »
déjà en ligne. Pas mesuré : le délai de mise en ligne effective sur chaque portail.
**Ce que fait l'écran** (`handleSaveDiffusionTargets` + `handleApplyDiffusionTargetsOnHektor`, App.tsx ~21339) : il
ENREGISTRE un choix pour CHAQUE portail du bien (coché / décoché, `app_diffusion_target`), puis demande au pont
d'appliquer : `apply` envoie « ajouter » pour chaque choix coché et « retirer » pour chaque décoché (un « déjà publié » est
toléré), relit la fiche et les portails chez Hektor, et l'écran recopie le résumé chez nous. ⚠ Pour la direction, l'écran
passe `ensureDiffusable: true` (il REND le bien diffusable au passage) ; pour le négociateur, la route le force à faux et
exige un bien diffusable ET le sien (`assert_can_apply_portals`, règle du lot 4, 03/11).
**La carte actuelle « un portail »** fait la même chose avec UN seul choix enregistré (les autres portails ne bougent pas).
**Mesures (17/11)** : 5 portails connus (Leboncoin, Bien'ici — numéro propre à chacune des 17 agences —, Paper,
Etreproprio, Superimmo — numéro commun) ; 435 biens diffusables, dont 312 sur plusieurs portails (3,3 en moyenne).

**La carte proposée — `diffusion`** (tous les rôles, comme la carte « un portail ») : sur un bien vivant DÉJÀ DIFFUSABLE
(sa règle « uniquement si diffusable », pour TOUT LE MONDE : la direction rend d'abord le bien diffusable par la carte
Pilotage — la carte ne passe JAMAIS `ensureDiffusable`), une liste « à publier » et une liste « à retirer » ; les portails non
nommés NE BOUGENT PAS. Au clic : la garde de la route (`assert_can_apply_portals`, jugée avec le jeton), les choix
enregistrés comme l'écran, UN SEUL `apply`, chaque refus de Hektor dit portail par portail, le résumé recopié chez nous.
La carte dit avant -> après (« en ligne : Leboncoin, Bien'ici -> Leboncoin, Paper »).
**Forme recommandée** : ÉLARGIR la mécanique de la carte « un portail » (un seul code pour les deux, la carte « un
portail » devient le cas d'une liste d'un élément) plutôt qu'en écrire une seconde — moins de code qui diverge.
**Ce que ça pourrait casser ailleurs** : rien de neuf — même effacement / réécriture des choix du bien que la carte « un
portail » et que l'écran ; geste RÉEL chez Hektor au clic (la publicité du bien), d'où la confirmation portail par portail.
**Épreuve proposée** : sans valider d'abord ; un essai réel sur un bien qu'il choisit.

## 45. La carte DIFFUSION (plusieurs portails) : CODÉE en élargissant la carte « un portail » (17/11, « Vas-y, élargis »)

La carte `portail` prend désormais une liste « à publier » et une liste « à retirer » (noms tolérés : « bienici »,
« Bien'ici », « le bon coin »…) ; les portails non nommés ne bougent pas ; ce qui est déjà dans l'état voulu est écarté et
DIT. Au clic : le bien doit être DÉJÀ diffusable POUR TOUS LES RÔLES (règle du 17/11 — la carte ne passe jamais
`ensure_diffusable`), la garde de la route /apply, les SEULS portails nommés enregistrés (numéro commun ou numéro de
l'agence, l'agence lue une fois), UN SEUL envoi, un refus de Hektor dit portail par portail (rien reporté alors), sinon le
résumé reporté. Une carte proposée sous l'ANCIENNE forme (un portail, publier vrai / faux) reste valable au clic.
**Contrôles** : `test_assistant_gestes` 318 verts (6 nouveaux ; les anciens tests « un portail » passent toujours) ;
témoin inverse : la vérification « déjà diffusable » au clic sabotée -> ROUGE, remise -> 318 ; `test_assistant_ia` 62 ;
`test_assistant_lecteur` 73 ; `npm run build` vert. Toujours 39 gestes (élargi, pas ajouté).

## 46. Épreuve de la carte DIFFUSION, SANS VALIDER (17/11, 10:25, sur « Oui, sans valider ») — PROUVÉE

En production (Render `b5b8fec`), Chrome de Frédéric (admin), bien de TEST 62963 « TEST C15 entrepot depuis l app - a
supprimer » (diffusable, aucun portail ; 63330 ne l'est pas). Demande : publier sur Paper et Bien'ici, retirer de
Leboncoin. Carte : « PUBLIER sur Paper, Bien'ici — en ligne : aucun → Paper, Bien'ici ; les autres portails ne bougent
pas (déjà dans l'état voulu : Leboncoin) » — Leboncoin, déjà hors ligne, écarté et DIT. REFUSÉE à 10:25.
**Base** : la ligne `portail` en `refusee`, `execute_le` vide, paramètres `{paper, bienicidirect}` ; 62963 inchangé
(diffusable 1, aucun portail, `refreshed_at` au 15/11) ; sa ligne de choix inchangée (1, du 15/11 19:50 — la carte
l'aurait effacée et réécrite) ; 0 choix de portail écrit dans la demi-heure (témoin : 7 sur 7 jours, la même lecture).
**Pas encore prouvé** : un clic RÉEL (Hektor publie, le résumé est reporté), sur un bien qu'il choisit.

## 47. L'inventaire des gestes REMIS À JOUR après §41-46 (17/11, sa demande)

Changements depuis le §40 : Pilotage (Validation, Diffusable) et plusieurs portails d'un coup passent AVEC CARTE ; ajouter
une photo et déposer un document passent PAR LA FENÊTRE (sa décision du 17/11). 78 lignes.
**AVEC CARTE (35)** : les 32 du §40, plus cocher Validation [DIR], cocher Diffusable [DIR], plusieurs portails d'un coup
(la carte « un portail » élargie). ⚠ Éprouvées SANS VALIDER seulement (pas de clic réel) : les 8 cartes directes du §36,
le prix, le Pilotage, la Diffusion.
**PAR LA FENÊTRE, lot 6 (10)** : les 8 du §40, plus ajouter une photo, déposer un document.
**FERMÉ PAR DÉCISION (7)** : inchangé.
**SANS CARTE, À DÉCIDER (26)** : supprimer une annonce [DIR] ; créer un mandant, modifier son e-mail / portable ; champs
d'une transaction, conditions suspensives, commission, répartition [DIR] ; supprimer un compromis ou une vente [DIR] ;
trancher un écart [ADMIN] ; créer le conjoint, modifier ou défaire un couple ; supprimer un contact [DIR] ; supprimer une
recherche ; corriger une date de clôture [DIR] ; charge des honoraires ; signé à la main ; ImmoSign ; plan cadastral ;
supprimer un document ; e-mail d'estimation ; agenda d'un collègue [DIR] ; partenaires ; alertes de Santé [ADMIN] ; GED ;
Matterport ; scan d'une fiche papier ; pièces jointes.

## 48. « Ceux qui demandent un fichier » : ce qu'ils sont vraiment (17/11, sa question avant le lot 5) — lu dans le code

- **Scan d'une fiche papier** : c'est une ÉTAPE de la fenêtre « Créer une annonce » (`handleDraftAnnonceScanFile`,
  App.tsx ~18255) — on photographie la fiche (jusqu'à 5 pages, JPEG / PNG / WebP, 12 Mo), la route `/annonces/scan-fiche`
  la fait lire par l'IA (fiche `scan_fiche`) et PRÉ-REMPLIT le formulaire de création. Il a besoin d'une photo par
  nature, et la fenêtre sait déjà la prendre -> il suit la création d'annonce : **par la fenêtre (lot 6)**, pas de carte.
- **Pièces jointes aux e-mails** : ⛔ **MON CLASSEMENT ÉTAIT FAUX** — à l'écran, les pièces jointes ne viennent PAS de
  l'ordinateur : ce sont les documents (déposés au coffre) et les photos DÉJÀ dans l'application, d'un bien lié au
  contact (`buildEmailAttachments`, App.tsx ~45259 : lien signé 15 min pour un document, adresse de la photo), 10 au plus,
  envoyés par la même route Gmail que la carte « e-mail au client » (`attachments`, déjà prévue côté serveur, la carte
  passe aujourd'hui `None`). **Aucun fichier à recevoir** : une carte est possible — l'e-mail au client avec, au choix,
  des documents / photos d'un bien du contact, CHAQUE fichier nommé sur la carte (ce qui part chez un client est réel).

## 49. Décision du 17/11 (« Scan fenêtre, PJ carte ») et AUDIT des pièces jointes — rien codé

**Scan d'une fiche papier** -> PAR LA FENÊTRE (avec la création d'annonce, lot 6). Inventaire : 35 avec carte, **11** par
la fenêtre, 7 par décision, **25** sans carte (le scan quitte « sans carte » ; les pièces jointes y restent jusqu'à leur
carte).
**Pièces jointes — ce que fait l'écran** (fenêtre « e-mail » d'un contact, App.tsx ~45160) : il propose les biens LIÉS
au contact (ses relations), puis pour le bien choisi ses documents (`app_console_document`, SEULEMENT ceux copiés au coffre
`cloud_available`) et ses photos (`app_console_photo`, présentes chez Hektor, visibles ET masquées) ; 10 au plus ; au
départ, un LIEN SIGNÉ de 15 min par document (bucket `hektor-console-documents`, avec le jeton de la personne, et
`app_console_touch_document`) et l'adresse de la photo ; puis la même route Gmail que la carte « e-mail au client ».
**Côté serveur** (`_download_gmail_attachments`) : il télécharge lui-même chaque pièce — 10 au plus, 8 Mo par fichier,
18 Mo en tout. ⚠ Il accepte N'IMPORTE QUELLE adresse web : dans la carte, les adresses seront fabriquées par NOTRE
serveur depuis la base, JAMAIS données par le modèle.
**Mesure** : 25 356 documents au coffre (5 128 biens) ; 168 532 seulement sur notre serveur (`local_only`) — non
joignables, ni à l'écran ni par la carte.
**La carte proposée** : (1) une LECTURE `lire_pieces_jointes(contact)` — les biens du contact, leurs documents joignables
(nom, type, taille) et leurs photos (rang, visible / masquée), avec un numéro chacun ; (2) la carte « e-mail au client »
reçoit en plus `pieces_jointes` (ces numéros, ou vide). À la carte ET au clic : chaque pièce doit appartenir à un bien LIÉ
à ce contact et être lisible avec le jeton de la personne, un document doit être au coffre, 10 au plus, tailles dans les
limites ; la carte NOMME chaque fichier (type, taille, « masquée » pour une photo masquée). Au clic seulement : les liens
signés (15 min) et l'adresse des photos, fabriqués par le serveur.
**Ce que ça pourrait casser ailleurs** : rien d'existant (la carte sans pièce jointe reste identique) ; ce qui part chez
un client est RÉEL et peut être sensible (un mandat, une pièce d'identité) — d'où chaque fichier nommé sur la carte.

## 50. Sa question : déposer des fichiers DE SON ORDINATEUR dans l'assistant (et dans la fenêtre e-mail) — FAISABILITÉ (17/11)

**Réponse : OUI.** Lu dans le code : l'écran dépose aujourd'hui un fichier en DEUX temps — il le range au coffre
(`hektor-console-documents`, sous `temp/uploads/<travail>/` ou `temp/photos/<travail>/`, avec le jeton de la personne),
puis pose le travail (`upload_document_to_hektor`, `upload_hektor_photo`) ; le worker va chercher le fichier à l'adresse
que porte le travail (`temp_storage_path`, Console/console_job_worker.js ~10140). L'assistant peut faire EXACTEMENT pareil.
**La brique commune, à faire d'abord : le trombone de la conversation** — glisser ou choisir des fichiers (photos,
PDF), rangés au coffre sous un dossier temporaire de la conversation AVANT la question ; le modèle ne voit que leur NOM,
TYPE et TAILLE (jamais le contenu — le contenu ne part pas chez OpenAI) ; un fichier non utilisé est purgé (⚠ déjà 109
fichiers / 196 Mo dormaient sous `temp/` le 14/10 : la purge est à prévoir dès le départ).
**Ce qu'elle ouvre** :
1. ajouter une PHOTO à une annonce (carte -> `upload_hektor_photo`, comme l'écran) ;
2. ajouter un DOCUMENT à une annonce (carte -> `upload_document_to_hektor`, avec son type et son libellé) ;
3. les PIÈCES JOINTES d'un e-mail au client : fichiers déposés + documents / photos déjà dans l'app ; et pour un fichier
   déposé, « l'ajouter aussi au bien » proposé dans la même conversation (une 2e carte, pour garder un geste = un clic) ;
4. le SCAN d'une fiche papier : les photos déposées passent par le lecteur de l'écran (`/annonces/scan-fiche`) et
   l'assistant montre les champs lus — la CRÉATION reste à la fenêtre (décision), pré-remplie avec ce scan (lot 6).
**Et dans la fenêtre e-mail de l'écran** (hors assistant) : un bouton « depuis l'ordinateur » à côté des documents et
photos du bien, même mécanique (dépôt au coffre puis lien signé), et la même case « ajouter aussi au bien ».
**Ce que ça change** : la décision « ajouter une photo / un document : par la fenêtre » (§40) devient « par une carte ».
**Ce que ça pourrait casser ailleurs** : rien d'existant ; c'est un NOUVEAU chemin d'entrée de fichiers — tailles et types
à borner comme l'écran (photo : JPEG / PNG / WebP ; scan 12 Mo ; pièce jointe 8 Mo / 18 Mo), et le coffre à purger.

## 51. LE TROMBONE : les règles à respecter (photos, documents, signé à la main, coffre) — ANALYSE (17/11) — rien codé

**Sa consigne** : « le trombone d'abord, mais respecter toutes les règles du serveur et de l'app pour les photos et pour
les documents, signature à la main = règle particulière ; une analyse avant, pour ne pas faire d'erreur ».
**Périmètre** : ajout d'une PHOTO et d'un DOCUMENT depuis l'ordinateur, marquage « signé à la main », coffre (dépôt,
temporaires, purge, droits). Deux analyses en lecture seule (rapports complets, fichier:ligne, dans la conversation du
17/11), puis vérifications en base par moi. Non mesuré : ce que Hektor fait d'un WebP ; l'orientation EXIF en réel.

### A. Le coffre — ⛔ le point qui change le dessin
- Règle d'accès `hektor_console_documents_temp_upload` (lue en base) : un utilisateur ne peut déposer QUE sous
  `temp/uploads/<travail>/` ou `temp/photos/<travail>/`, pour un travail `upload_document_to_hektor` / `upload_hektor_photo`
  EN ATTENTE qu'il a lui-même créé. ⇒ un trombone qui range les fichiers d'une conversation AVANT toute carte est REFUSÉ
  avec le jeton de la personne.
- Types (lus en base) : `hektor-console-documents` = pdf, jpeg, png, webp, doc, docx, xls, xlsx, txt, zip, 50 Mo (un .odt
  est refusé DÉFINITIVEMENT, 415) ; `gti-photo` (dérivés publics) = jpeg, png, webp, 10 Mo.
- Ordre imposé à l'écran : le TRAVAIL d'abord, puis le FICHIER, puis NOTRE LIGNE (`app_console_creer_*_optimistic`, qui
  lit le chemin dans la charge, jamais fourni par le client). Le worker ne réclame le travail que si le fichier existe.
- Un fichier temporaire peut rester orphelin (bien non vivant) : `nettoyer_temporaires_orphelins.js` (4 gardes, âge 2 jours).
### B. Photos
- Droits : `app_console_can_request_job('upload_hektor_photo')` — admin / manager tout ; négociateur sur SES biens.
- Négociateur obligatoire sur le bien ; le worker REFUSE une annonce archivée ou un brouillon (la reprise de 12:30 la
  reposerait chaque jour : l'appelant doit filtrer lui-même) ; vendu / clos acceptés si cache de détail (aucune décision).
- Types : JPEG, PNG, WebP à l'écran ; ⚠ WebP jamais envoyé à Hektor (comportement inconnu). 20 photos par envoi, un travail
  par photo, une à la fois par annonce (15 à 56 s chacune).
- Envoi chez Hektor par le navigateur du worker (Playwright) ; il EXIGE de voir la galerie grossir et de trouver le nouvel
  identifiant. ⚠ Sur le chemin « chez nous d'abord », un refus de Hektor finit en travail `done` avec `envoi_hektor: echec`
  (le vrai résultat est sur la ligne) ; reprise à 12:30, sans renvoi d'une ligne qui a déjà son numéro.
- ⚠⚠ La fonction qui pose NOTRE ligne ne reçoit PAS « masquée » (vérifié en base : elle ne parle pas de `visible`) et les
  dérivés publics sont fabriqués AVANT Hektor : une photo voulue masquée pourrait entrer dans la vitrine au run de nuit
  si Hektor échoue. Jamais arrivé (0 photo de ce chemin en attente ou en échec), mais réel dans le code.
- Une photo neuve arrive EN DERNIER (pas de rang), sans légende ; elle entre dans la vitrine au run de nuit.
### C. Documents
- Droits : `upload_document_to_hektor`, même règle. Négociateur obligatoire. Panneau masqué sur archive / brouillon.
- DEUX portes à l'écran : l'ancien formulaire (un fichier, aucune garde) et la FENÊTRE GED (`DepotDocuments.tsx`,
  cran `ged_depot_multiple` = admin) qui garde : types et 50 Mo, TYPE obligatoire (66 codes `app_ged_type`), NOM sans conflit
  (le worker adopte au réessai le document « du même nom » : un nom qui en contient un autre ferait adopter le mauvais),
  DOUBLON par empreinte sha256, types SENSIBLES forcés PRIVÉS (identité, état civil, financement, renseignements ; RIB
  JAMAIS envoyé), classement `app_ged_classer` après le dépôt (la synchro réécrit le type en « document »).
- Le libellé est le nom DÉFINITIF chez Hektor (renommer : fermé par décision ⑦-9). Anti-doublon G1 du 06/11 en service.
- Règle « un seul endroit » (GED §8.3 ter) : les documents se voient et se déposent dans l'onglet Documents du bien.
### D. Signé à la main — règle PARTICULIÈRE
- Ce n'est PAS un dépôt : c'est un 2e geste, sur un document DÉJÀ déposé (le scan papier), qui pose dans
  `metadata_json.signature` « signed / manuscrite / date ». L'écran : mandat ou avenant seulement, pas déjà signé, pas
  remplacé, avec confirmation « signé À LA MAIN par TOUS les mandants ». La base (patch du 06/11) ne refuse QUE le cas
  « signature électronique en cours » : le reste n'est gardé que par l'écran.
- Une fois marqué, le worker le PROTÈGE (règle R1 : synchro, purge des absents, Youtrust, ImmoSign).
- ⛔ Décision écrite (étape 3, §4c) : « signé à la main : PAS par l'assistant pour l'instant ».
### E. Défauts EXISTANTS trouvés (hors trombone, à décider par lui)
1. ⛔ **Un document SIGNÉ peut être SUPPRIMÉ** : le bouton est sur toutes les lignes et le worker
   (`handleDeleteDocumentFromHektor`, ~10525) ne regarde jamais la signature (vérifié) — contraire à la règle GED §5.3.
2. La photo voulue masquée qui peut fuir sur la vitrine (B).
3. La date de « signé à la main » est écrite en AAAA-MM-JJ, le pilotage ne lit que JJ/MM/AAAA.
4. La base accepte de marquer « signé à la main » un document qui n'est pas un mandat, déjà signé ou remplacé.

### F. Le dessin du trombone qui respecte ces règles (proposé)
1. **Le dépôt passe par NOTRE SERVEUR** (pas de nouvelle règle du coffre) : la personne joint ses fichiers, le serveur
   vérifie qui elle est, le TYPE et la TAILLE (les listes du coffre ; .odt refusé tout de suite, avec la raison), calcule
   l'empreinte, range le fichier sous `temp/assistant/<personne>/<numéro>/` et n'en donne au modèle que le nom, le type,
   la taille (JAMAIS le contenu). Purge des dépôts non utilisés après 2 jours (le nettoyeur existant, étendu).
2. **Ajouter une PHOTO** (carte) : les gardes de l'écran ET celles du worker (bien vivant, ni archive ni brouillon,
   négociateur présent), JPEG / PNG seulement, toujours VISIBLE (masquer ensuite par la carte existante — on évite le
   défaut B), au clic l'ordre de l'écran : le travail (jeton) -> la copie du fichier à sa place (serveur) -> notre ligne
   (jeton). La carte dit « envoi en cours » ; le résultat se lit sur la ligne, pas sur le travail.
3. **Ajouter un DOCUMENT** (carte) : les règles de la FENÊTRE GED, pas de l'ancien formulaire — type obligatoire
   (nomenclature), nom sans conflit, doublon par empreinte signalé, types sensibles forcés privés, RIB refusé, puis
   `app_ged_classer` ; même cran que la fenêtre GED (`ged_depot_multiple`, aujourd'hui admin).
4. **Signé à la main : JAMAIS par l'assistant** (décision écrite) — un mandat signé déposé par le trombone est un dépôt
   ordinaire ; la carte dit de le marquer sur la fiche du bien.
5. **Pièces jointes** : un fichier déposé peut partir en pièce jointe (lien signé fabriqué par le serveur) ; « l'ajouter au
   bien » = la carte 3, proposée à part.

## 52. LE TROMBONE : CODÉ (17/11, sur « Oui, le trombone ») — 1re marche, sans carte qui s'en serve encore

**Le chemin** (la règle du coffre interdit un dépôt libre avec le jeton de la personne, §51.A) :
1. `POST /assistant/fichiers/preparer` (nom, type, taille) : le SERVEUR contrôle (types du coffre ; .odt / .ods / HEIC
   refusés AVEC la raison ; 50 Mo ; vide) et fabrique, avec SA clé, une ADRESSE D'ENVOI SIGNÉE pour UN fichier sous
   `temp/assistant/<la personne>/<numéro>/<nom sans accents>` (la personne = son jeton, jamais fournie) ;
2. l'écran envoie le fichier DIRECTEMENT au coffre (`uploadToSignedUrl`, supabase-js 2.100) — il ne passe pas par Render ;
3. `POST /assistant/fichiers/{n}/confirmer` : le serveur RELIT ce qui est vraiment au coffre (taille, type réels) et le
   SUPPRIME s'il sort des règles ; `DELETE /assistant/fichiers/{n}` : la personne retire SON fichier ;
4. la question porte `fichiers: [numéros]` (10 au plus) : chaque fichier est RELU, et le modèle reçoit à la suite de la
   question « [Fichiers joints … fichier:N « nom » (type, taille)] » — JAMAIS le contenu ; la marque est gardée dans
   l'historique, l'écran la retire de la bulle et montre « Fichiers joints : … ». Consigne : ne jamais prétendre les avoir
   lus ; aucun geste ne les utilise encore.
**Interrupteur** `assistant_fichiers` (off / admin / on ; ABSENT = éteint) : `GET /assistant/fichiers/etat` dit à
l'écran s'il montre le bouton « Joindre » (accueil et conversation, + glisser-déposer). ⏰ À poser en base (son accord).
**Purge** : `Console/nettoyer_temporaires_orphelins.js` accepte désormais `temp/assistant/` (2 jours, mêmes gardes) —
⚠ ce nettoyeur se lance À LA MAIN (aucune tâche planifiée ne l'appelle) : à brancher sur une tâche, décision à prendre.
**Contrôles** : `tests/test_assistant_fichiers.py` 15 verts (types, .odt expliqué, chemin de la personne, relecture,
fichier truqué supprimé, retrait limité à SON dossier, ce que voit le modèle) ; témoin inverse : la suppression d'un fichier
hors règles sabotée -> ROUGE, remise -> 15 ; gestes 318, ia 62, lecteur 73 ; `npm run build` vert ; à l'écran (local,
maquette) le bouton « Joindre », la pastille du fichier et sa croix. **Pas éprouvé en réel** (interrupteur à poser).
**Sa question (17/11)** : « l'ajout des documents par l'assistant doit activer l'agent IA GED ? » — OUI, possible : la
carte « ajouter un document » (marche 3) enchaînera les DEUX agents de la GED (derrière `ged_lecture_ia`) — la PROPOSITION
du type avant l'envoi, puis la LECTURE des valeurs (`/ged/lire`) après le dépôt et le classement — avec leurs règles (RIB
jamais lu, pièces des personnes selon leur interrupteur). À détailler à l'audit de cette carte, avec la session GED.

## 53. LE TROMBONE EN LIGNE ET ÉPROUVÉ EN RÉEL (17/11, sur « Oui, les deux » puis « Oui, essaie »)

- **En ligne** : `b66a64f` poussé (par les autres sessions, avec les leurs) ; Render sert `f3fa65f` qui le contient
  (`/assistant/fichiers/etat` répond 401 sans jeton, une route inexistante 404 -- témoin) ; Vercel sert le bouton
  « Joindre ». **Interrupteur** `assistant_fichiers` = **admin**, posé à 14:11 (`supabase/patch_assistant_fichiers_
  interrupteur_2026-11-17.sql`, qui n'écrase jamais une valeur existante ; `_INVERSE` prêt).
- **Essai réel** (Chrome de Frédéric, admin, 14:13-14:15) :
  1. « Joindre » visible ; un fichier texte d'essai de 21 octets passe « prêt » (préparé, envoyé au coffre, RELU) ;
  2. la question « quel fichier t'ai-je joint, et que contient-il ? » -> « Tu as joint « essai-trombone.txt », un fichier
     texte de 1 Ko. Je ne peux pas voir son contenu, seulement son nom, son type et sa taille » ; la bulle montre
     « Fichiers joints : essai-trombone.txt » ;
  3. au coffre : `temp/assistant/<son compte>/531579c5…/essai-trombone.txt` (21 octets, text/plain) ; en base, la question
     porte la marque « fichier:531579c5… « essai-trombone.txt » (texte, 1 Ko) » — jamais le contenu ;
  4. un 2e dépôt retiré par la croix DISPARAÎT du coffre (`dfdb0e53…`), le 1er reste (il sera purgé : 2 jours, mais le
     nettoyeur se lance À LA MAIN).
- Observé : un dépôt met ~5 s à passer « prêt » (trois allers-retours : préparer, envoyer, relire) ; l'envoi attend.

## 54. La carte AJOUTER UNE PHOTO (avec un fichier du trombone) : AUDIT (17/11, « Oui, la photo ») — rien codé

**Le geste de l'écran** (`createUploadHektorPhotoJob`, lib/api.ts ~9156), relu : ① le travail `upload_hektor_photo`
(numéro tiré d'avance, charge : visible, nom d'origine, nom nettoyé, type, taille, `temp_storage_bucket`,
`temp_storage_path = temp/photos/<travail>/<nom>`, priorité 18, demandeur = la personne) ; ② le fichier déposé à ce chemin
(un échec -> `app_console_fail_own_pending_job(travail, message)`) ; ③ notre ligne
`app_console_creer_photo_optimistic(travail, dossier, annonce, nom, légende NULL, taille)` — un échec ne fait jamais
échouer le dépôt. Les règles complètes sont au §51 B (droits, worker, vitrine, défauts).
**La carte proposée — `ajouter_photo`** (tous les rôles ; la base juge : le négociateur sur SES biens) :
- un bien VIVANT (ni archive, ni brouillon, ni vendu / clos) avec un négociateur ; 1 à 20 photos du TROMBONE de la
  personne (relues au coffre), **JPEG ou PNG seulement** (le WebP n'a jamais été envoyé à Hektor ; le GIF est refusé par le
  coffre) ;
- toujours **VISIBLE** (on évite le défaut « une photo voulue masquée peut fuir sur la vitrine ») ; masquer, couverture,
  déplacer : les cartes photo existantes, une fois la photo arrivée ;
- au CLIC, pour chaque photo, l'ordre de l'écran : le travail (avec le jeton de la personne -> la règle d'insertion juge
  les droits) -> la COPIE du fichier par le serveur, de `temp/assistant/…` vers `temp/photos/<travail>/` (copie au coffre,
  sans renvoi depuis l'ordinateur ; un échec -> le travail est soldé en échec, comme l'écran) -> notre ligne (jeton) ;
- la carte DIT : les noms ; « visible, en DERNIER dans la galerie » ; « envoyée chez Hektor par le worker, une après
  l'autre (15 à 60 s chacune) » ; « sur la vitrine après le traitement de nuit » ; et au résultat « envoi en cours » (un
  travail fini ne veut pas dire « chez Hektor » : le vrai résultat est sur la ligne de la photo).
**Ce que ça pourrait casser ailleurs** : rien d'existant (le chemin de l'écran, à l'identique) ; un lot de 20 photos occupe
la file des documents de ce bien ~7 minutes (un travail à la fois par annonce) et consomme des appels Hektor (navigateur
du worker). La course théorique « réclamation avant notre ligne » (§51 B) est la même qu'à l'écran.
**Épreuve proposée** : sans valider d'abord ; puis un essai réel sur le bien d'essai 63330 (une photo de test, retirée
ensuite par la carte « masquer » ou à l'écran).

## 55. La carte AJOUTER UNE PHOTO : CODÉE (17/11, sur « Vas-y ») — pas encore en ligne

`ajouter_photo` (tous les rôles) : `fichiers` = les numéros du trombone (« fichier: » toléré), 1 à 20, RELUS au coffre
dans SON dossier, JPEG / PNG seulement (un PDF, un WebP refusés en les nommant) ; bien VIVANT avec négociateur. Au clic,
pour CHAQUE photo, l'ordre de l'écran : le travail `upload_hektor_photo` (jeton ; `visible: true`, la charge de l'écran +
`source: assistant`) -> `fichiers_service.copier` (copie AU COFFRE du trombone vers `temp/photos/<travail>/`, source forcée
sous `temp/assistant/`) -> `app_console_creer_photo_optimistic` (jeton, sans faire échouer). Copie ratée : SON travail soldé
par `app_console_fail_own_pending_job`, les autres partent ; toutes ratées : refus. Le résultat dit « envoi en cours ».
Consigne : les photos jointes passent par `proposer_ajouter_photo` ; document et pièces jointes « bientôt ».
**Contrôles** : `test_assistant_gestes` 330 verts (§18 : 12 nouveaux, dont le témoin « fichier retiré entre la carte et le
clic -> rien posé ») ; témoin inverse : la photo envoyée masquée -> ROUGE, remise -> 330 ; `test_assistant_fichiers` 17
(la copie refuse une source hors du trombone) ; ia 62, lecteur 73 ; `npm run build` vert. 40 gestes.

## 56. La carte AJOUTER UNE PHOTO EN LIGNE ET ÉPROUVÉE EN RÉEL (17/11, sur « Vas-y »)

- **En ligne** : `a56a27e` (poussé par la session GED avec les siens ; mon push direct a été refusé car la branche
  distante était déjà plus loin — sans effet) ; Render sert `df0a222`, qui le contient.
- **Bien d'essai 63330** (0 photo, 0 envoi passé, file vide avant l'essai) ; image de TEST fabriquée exprès (« ESSAI
  ASSISTANT — photo de test — à supprimer », JPEG 66 Ko) jointe par le trombone.
  1. **Sans valider** : la carte « Ajouter 1 photo à l'annonce 63330 … « essai-photo-assistant.jpg ». VISIBLE, en dernier
     dans la galerie ; envoyée chez Hektor par le worker … ; sur la vitrine après le traitement de nuit » -> REFUSÉE :
     ligne `refusee`, 0 travail, 0 fichier copié sous `temp/photos/`.
  2. **En réel** : une 2e carte, VALIDÉE -> travail `6894bd1e…` (`source: assistant`, notre ligne posée d'abord :
     `app_photo_id` présent, le chemin de l'écran) -> `done` -> **`envoi_hektor: envoye`, `hektor_photo_id 490558`** ; la
     photo chez nous : visible, `present_in_hektor`, `cloud_available`, rang 1 ; le fichier d'attente nettoyé par le worker.
- ✅ La photo de test SUPPRIMÉE le 17/11 sur sa demande (« par les workers ») : travail `delete_hektor_photo` `e577b613…`
  (le même que le bouton de l'écran, priorité 15, posé avec une garde sur la ligne visée) -> `done` : les deux galeries
  Hektor relues à 0 photo, notre ligne retirée, 2 dérivés supprimés ; 63330 revient à 0 photo.

## 57. AJOUTER UN DOCUMENT avec le NOUVEL AGENT GED : AUDIT (17/11, sa consigne « il faut que cela fonctionne avec le
## nouvel agent GED ») — rien codé

**Périmètre** : le circuit de dépôt de la FENÊTRE GED d'aujourd'hui (`DepotDocuments.tsx`, `lib/ged.ts`,
`lib/gedClassementIa.ts`, `routers/ged.py`, services `openai_ged_*`) ; analyse en lecture seule (rapport complet,
fichier:ligne, dans la conversation du 17/11) + vérifications en base. Non mesuré : la dépense IA du jour.
**Ce que fait la fenêtre, pour UN fichier** : type proposé d'après le nom -> empreinte sha256 et DOUBLON -> type attendu
(« Reçu / Manque ») -> **agent `ged_classement`** (TYPE, NOM proposé — « Prendre ce nom » —, DÉCOUPAGE en pièces —
« Séparer en N fichiers ») -> contrôles (types, 50 Mo, nom sans conflit, type obligatoire, sensibles PRIVÉS) -> envoi par
`createUploadDocumentToHektorJob` (libellé du type comme `documentType`) -> `app_ged_classer` (avec le jeton : il exige
que la personne soit le DEMANDEUR du travail) -> **agent `ged_lecture`** (`/ged/lire` : les valeurs, rangées dans
`app_ged_lecture` / `app_ged_valeur`, pièces d'identité dans leur registre privé) -> plus tard « Ce que dit le compromis »
(Reçu / Manque). Garde RIB à chaque étape ; plafond IA commun de 2 $ par jour.
**⛔ LE POINT QUI DÉCIDE** : les deux agents ne lisent JAMAIS le fichier au coffre. C'est le NAVIGATEUR qui le prépare :
pdf.js lit le texte (garde RIB sur TOUT le texte, jusqu'à 150 pages) et DESSINE les pages en vignettes (512 px pour le
classement, 1 600 px pour la lecture) ; pdf-lib découpe ; et la lecture se fait APRÈS l'envoi, avec le fichier encore
dans le navigateur. **Le serveur n'a AUCUN outil PDF ni image** (`requirements.txt`). Aucune route ne propose type ou nom
à partir d'un fichier au coffre. Interrupteurs GED (lus en base) : `ged_depot_multiple`, `ged_lecture_ia`,
`ged_lecture_personnes`, `ged_propositions`, `ged_recu_manque`, `ged_remplir` = **admin**. La fenêtre a changé 5 fois
le 17/11 (session GED).

**Deux chemins** :
- **A (recommandé) — la carte OUVRE LA FENÊTRE GED, déjà garnie des fichiers joints** : l'assistant prépare une carte
  « Déposer 2 documents sur l'annonce N » ; au clic, l'écran ouvre la fenêtre de dépôt du bien et y met les fichiers du
  trombone (relus au coffre par un lien signé, redevenus des fichiers du navigateur) ; TOUT le nouvel agent GED tourne tel
  quel (type, nom, découpage, RIB, sensibles, doublon, envoi, classement, lecture, puis « Ce que dit le compromis ») ; la
  personne vérifie et clique « Envoyer » DANS la fenêtre. Zéro règle recopiée, et chaque amélioration de la GED profite à
  l'assistant le jour même. Il faut une seule porte d'entrée dans la fenêtre (« ouvrir avec ces fichiers ») —
  ⚠ fichier de la session GED : à faire AVEC elle. Hors du cran de `ged_depot_multiple`, la fenêtre n'existe pas : la
  carte le dit au lieu de retomber sur l'ancien formulaire.
- **B — tout côté serveur** : ajouter des bibliothèques PDF / image au serveur, recopier en Python la préparation du
  navigateur (garde RIB complète, vignettes, découpage, choix des pages par type, nom muet, privés…) et appeler les agents
  en interne. Deux copies du même circuit, qui divergeraient à chaque modification de la GED ; déconseillé.
**Ce que ça pourrait casser ailleurs (A)** : rien d'existant si la porte d'entrée est additive (la fenêtre s'ouvre comme
aujourd'hui quand on n'y passe pas de fichiers) ; le dépôt reste le geste de la fenêtre, au nom de la personne.

## 58. Décision du 17/11 : chemin **A** (la carte ouvre la fenêtre GED garnie des fichiers joints) — le partage du travail

- **La session GED** (ses fichiers, en cours de modification) : une entrée optionnelle de `DepotDocuments`
  (`fichiersDepuisAssistant { jeton, fichiers: File[] }` + `onFichiersPris` : à chaque nouveau jeton, UNE fois
  `ajouterFichiers`, le chemin d'un glisser-déposer) ; `ConsoleDocumentsPanel` la passe et OUVRE la fenêtre quand elle
  arrive ; rien si `ged_depot_multiple` est fermé. Message envoyé le 17/11 (« toi ou moi ? ») ; réponse attendue.
- **L'assistant** (sans toucher les fichiers GED) : la carte `deposer_documents` (bien vivant, négociateur, fichiers du
  trombone de la personne, types acceptés par la GED, cran `ged_depot_multiple` pour la personne ; au clic RIEN n'est écrit
  côté serveur : elle rend des liens signés de lecture, courts) ; l'écran retélécharge les fichiers en objets File, ouvre la
  fiche du bien sur ses Documents et les passe à la fenêtre ; la personne finit DANS la fenêtre (agent GED complet).
  La carte dit « la fenêtre GED va s'ouvrir avec N fichiers ; c'est elle qui propose le type et le nom, et c'est toi qui
  cliques Envoyer ».

## 59. La carte DÉPOSER DES DOCUMENTS (chemin A) : CODÉE (17/11, sur « Vas y ») — pas encore en ligne

- **Serveur** : `deposer_documents` (tous les rôles), ajoutée après `ajouter_photo`. La carte exige :
  - le cran `ged_depot_multiple` pour la personne : `on`, ou `admin` avec le rôle admin. Sinon elle refuse : « dépose-les
    depuis la fiche du bien » ;
  - un bien VIVANT avec un négociateur ;
  - les fichiers du trombone (1 à 20), RELUS au coffre dans SON dossier. Les types sont ceux du coffre : un PDF et une
    photo passent tous les deux.

  Au clic, la carte re-vérifie tout et **n'écrit RIEN** : ni travail, ni ligne. Elle rend
  `{ouvrir: "depot_ged", app_dossier_id, hektor_annonce_id, fichiers: [{nom, type, url}]}`, où `url` est un lien signé de
  LECTURE de 10 minutes (`assistant_fichiers.lien_lecture`, source forcée sous `temp/assistant/`). Un lien refusé fait
  échouer la carte : jamais une fenêtre à moitié garnie.
- **Écran** :
  - `AccueilAssistant` retélécharge les fichiers en objets `File`, les pose par `poserDepotAssistant(app_dossier_id,
    fichiers)` (`lib/depotAssistant.ts`, un passage de main dans la page, rien en base) et ouvre la fiche du bien. Un
    téléchargement raté s'écrit sur la carte.
  - La fiche (`CockpitDetail`) passe sur Médias & pièces / Documents ; le panneau ouvre la fenêtre si `gedDepot` est
    ouvert.
  - **`DepotDocuments` lit lui-même le dépôt de SON bien** (`useDepotAssistant`). Il le prend par `ajouterFichiers` (le
    chemin d'un glisser-déposer : garde RIB, sensibles, doublon, classement, lecture), une seule fois par jeton et une
    fois les types lus, puis il le retire.
  - La personne vérifie, puis clique « Envoyer » DANS la fenêtre.
- ⚠ **Ce que mon premier jet cassait** : deux propriétés neuves sur `DepotDocuments` dans App.tsx faisaient passer le
  bloc `formulaireAjout` de 583 à 669 caractères. Le test de la GED le borne à 600, et son contrôle « éteint =
  uploadForm » est passé ROUGE. D'où la lecture par la fenêtre elle-même : App.tsx ne porte plus que l'import et deux
  effets, hors du bloc et hors des lignes de la GED.
- **Coordination** : la session GED a été prévenue avant le commit et a donné son accord (« le passage par
  ajouterFichiers, une fois par jeton et une fois les types lus, me va »).
- **Consigne** : les documents joints passent par `proposer_deposer_documents`. Le modèle ne promet jamais qu'ils sont
  déjà chez Hektor. Les pièces jointes d'un e-mail restent « bientôt ».
- **Contrôles** :
  - `test_assistant_gestes` : 340 verts. La section 19 en apporte 10, dont trois témoins : la fenêtre refermée entre la
    carte et le clic, un fichier retiré entre la carte et le clic, un lien refusé ;
  - ia 62 (41 gestes, ouverte au négociateur), fichiers 17, lecteur 73 ;
  - GED : `test_ged_depot` 33/33 et `test_ged_classement_ia` 37/37 ;
  - `npm run build` vert.
- ⛔ **Pas encore éprouvé à l'écran.** Le cran `ged_depot_multiple` est à `admin` : seul Frédéric verra la fenêtre
  s'ouvrir.

## 60. La carte DÉPOSER DES DOCUMENTS EN LIGNE, éprouvée « sans valider » (17/11, sur « Oui pousse puis test sans valider »)

- **En ligne** : poussé `2250250..51da332`, avec deux notes d'autres sessions (e37dfcf de la GED, a2273d2 du classeur).
  Render a servi `51da332` à 20:28:33 ; Vercel servait la carte (`depot_ged` dans le code) à 20:29:42.
- **Essai dans le Chrome de Frédéric**, avec un PDF d'essai d'une page (622 octets) joint par le trombone :
  - « Dépose ce document sur l'annonce 62774 » -> **refusé**, et le modèle le dit : 62774 est CLOSE (mon essai de ⑦-3a
    du 21/10), on ne prépare un dépôt que pour une annonce vivante. C'est un témoin : la garde du bien vivant mord.
  - « … sur l'annonce 63506 » -> **la carte « Documents » s'affiche** : « Ouvrir la fenêtre de dépôt GED de l'annonce
    63506 « Spécial investisseurs » avec 1 fichier : « essai-document-assistant.pdf » … rien ne part chez Hektor tant que
    tu n'as pas cliqué « Envoyer » DANS la fenêtre ». Elle est valable jusqu'à 21:01.
  - **NON validée.** Preuve : `notice/preuve_carte_deposer_documents_2026-11-17.jpg`.
- ⛔ **Reste à éprouver** : le clic « Valider ». La fiche doit s'ouvrir sur Documents, avec la fenêtre GED garnie du
  fichier. Puis « Envoyer » dans la fenêtre, qui ÉCRIT chez Hektor : sur un bien que Frédéric choisit.
- ✅ **LE CLIC « VALIDER » EST ÉPROUVÉ (17/11, sur « Oui »)** : carte validée sur 63506, sans cliquer « Envoyer ».
  - La fiche s'est ouverte et la fenêtre **« Déposer des documents » s'est ouverte d'elle-même**, avec
    « essai-document-assistant.pdf, 1 Ko, 1 page ». L'aperçu de la page était lu par le navigateur.
  - **Tout l'agent GED a joué**, comme pour un glisser-déposer : « L'IA lit le type… », puis il a proposé le nom
    « Document d'essai » et pensé « Notes, suivi interne (confiance basse) ». Le document reste « Privé ». Le bouton
    « Rien à envoyer » reste grisé tant que le type n'est pas choisi.
  - « Fermer » -> la garde de la GED répond « 1 document n'est pas parti » -> « Fermer sans envoyer ». **La fenêtre ne
    s'est pas rouverte** : le dépôt a bien été retiré après la prise. Le bien affiche toujours 30 documents.
  - **En base** : le seul travail sur 63506 est `refresh_console_data` `{light, reason: read_through_open}`, la lecture
    légère de l'ouverture d'une fiche. **Aucun dépôt, rien chez Hektor.**
  - Preuve : `notice/preuve_fenetre_ged_depuis_assistant_2026-11-17.jpg`.
- ⛔ **Reste** : « Envoyer » dans la fenêtre, qui ÉCRIT chez Hektor. Ce n'est plus la carte de l'assistant, c'est le
  chemin de la GED déjà en production. À faire seulement si Frédéric le veut, sur un bien qu'il choisit.

## 61. La carte PIÈCES JOINTES d'un e-mail au client : AUDIT REMIS À JOUR avec le trombone (17/11, « Donc on enchaîne ») — rien codé

**Périmètre** : l'e-mail AU CLIENT (`email_client`) et ses pièces jointes. L'e-mail interne n'est pas touché. La
fenêtre e-mail de l'écran (bouton « depuis l'ordinateur ») est une étape à part, après.

**Ce que fait l'écran, relu dans le code** (fenêtre e-mail d'un contact, App.tsx ~45380-45520)
- Il propose les biens LIÉS au contact (`contactEmailAttachmentRelations` : toutes ses relations, quel que soit le
  rôle, les biens vivants d'abord).
- Pour le bien choisi, il propose :
  - ses documents, SEULEMENT ceux au coffre (`cloud_available`). Au départ, un lien signé de 15 min par document
    (avec le jeton de la personne), plus `app_console_touch_document` ;
  - ses photos ayant une adresse (`url_hd` ou `url_preview`), visibles ET masquées.
- 10 pièces au plus. Puis la même route Gmail que la carte.
- ⚠ **L'écran ne filtre AUCUNE pièce sensible** : une pièce d'identité, un RIB ou une offre de prêt d'un vendeur peut
  partir chez un acquéreur lié au même bien.

**Côté serveur** (`_download_gmail_attachments`, google_workspace_service.py:471)
- Il télécharge lui-même chaque pièce : 10 au plus, 8 Mo par fichier, 18 Mo en tout.
- ⚠ Il accepte n'importe quelle adresse web. Dans la carte, les adresses seront TOUJOURS fabriquées par notre serveur
  depuis la base ou le trombone, jamais données par le modèle.
- La carte `email_client` passe aujourd'hui `attachments=None` (assistant_gestes.py:1075).

**Mesures**
- Documents : 25 377 au coffre (23 547 privés, 1 830 partagés). 168 532 seulement sur notre serveur : non joignables,
  ni à l'écran ni par la carte.
- ⚠ **Le type GED n'est connu que pour 40 documents** (ceux déposés par la fenêtre GED, dont 18 de type sensible). Les
  25 000 autres n'ont pas de type : leur sensibilité ne se devine qu'à leur NOM. Le repérage par nom
  (`gedTypeParNom`) n'existe que dans le navigateur aujourd'hui.

**Ce que le trombone ajoute**
- Un fichier joint dans la conversation peut partir en pièce jointe : le serveur fabrique un lien de lecture court
  (`assistant_fichiers.lien_lecture`, déjà en service pour la carte Documents). Gmail le télécharge aussitôt.
- « L'ajouter aussi au bien » reste une 2e carte (`ajouter_photo` ou `deposer_documents`) : un geste = un clic.

**La carte proposée**
1. Une LECTURE `lire_pieces_jointes(contact)` : les biens liés au contact, avec pour chacun ses documents joignables
   (nom, taille) et ses photos (rang, visible ou masquée). Chaque pièce porte un numéro. Lue avec le jeton de la
   personne.
2. La carte `email_client` reçoit en plus `pieces_jointes` (numéros de documents, de photos ou de fichiers du
   trombone). À la carte ET au clic, le serveur vérifie :
   - chaque document ou photo appartient à un bien LIÉ à ce contact et reste lisible avec le jeton ;
   - un document est au coffre ; un fichier du trombone est dans SON dossier ;
   - 10 pièces au plus, 8 Mo par fichier et 18 Mo en tout quand la taille est connue.
   La carte NOMME chaque fichier (nom, taille, « masquée » pour une photo masquée).
3. Au clic seulement : les liens signés (documents avec le jeton de la personne, puis `app_console_touch_document` ;
   trombone par le serveur) et l'adresse des photos.

**À DÉCIDER PAR FRÉDÉRIC**
- Les pièces SENSIBLES (identité, état civil, RIB, financement, fiche de renseignements). L'écran les laisse partir.
  - A : la carte les REFUSE, et dit de passer par la fenêtre e-mail si c'est voulu. Le repérage se fait par le type GED
    quand il existe, sinon par le nom (la liste de la GED, recopiée côté serveur). ⬅ recommandé : ce qui part chez un
    client est réel, et la carte est préparée par une IA.
  - B : la carte les accepte, avec un ⚠ « pièce sensible » sur la carte.
- Les photos MASQUÉES : comme l'écran (acceptées, marquées « masquée » sur la carte) — recommandé.

**Ce que ça pourrait casser ailleurs**
- Rien d'existant : sans pièce jointe, la carte reste identique, et la fenêtre e-mail de l'écran n'est pas touchée.
- La route Gmail est partagée avec l'écran, mais elle n'est pas modifiée : la carte lui passe des pièces comme
  l'écran.
- Un lien signé est une clé de lecture : il est fabriqué au clic, vit 15 min au plus, et ne part ni au modèle ni dans
  la carte.

## 62. Pièces jointes de l'e-mail au client : CODÉES le 18/11 (pas poussées)

**Ses décisions**
- 17/11 : « Les accepter comme l'agent GED ». Les pièces sensibles PARTENT, comme la GED les accepte. Elles sont
  marquées sur la carte, et la marque reste dans le résultat de la carte : c'est la trace, comme le journal de l'agent
  GED (`proposal_json.sensible`).
- 18/11 : il a demandé « on envoie des liens ? ». La réponse est NON : le client reçoit de vrais fichiers. Le lien
  signé ne sert qu'au serveur pour télécharger le fichier avant de l'attacher (`_download_gmail_attachments`). Puis
  il a dit « Vas-y ».

**Ce qui est codé** (`assistant_gestes.py`, section « les PIÈCES JOINTES de l'e-mail au client »)
- La lecture `lire_pieces_jointes(contact)` est ouverte à tous les rôles. Elle reprend la logique de l'écran
  (`contactEmailAttachmentRelations`, `loadConsoleDocuments`, `loadConsolePhotos`, `prefererNosPhotos`) :
  - les biens LIÉS au contact, un par dossier, les actifs d'abord, 10 au plus ;
  - pour chaque bien, ses documents au coffre et ses photos encore chez Hektor, numérotés `doc:…` ou `photo:…` ;
  - les sensibles et les masquées sont marquées, et une adresse e-mail dans un nom est masquée avant d'aller au modèle.
- La carte `email_client` reçoit un nouveau paramètre `pieces` : `doc:…`, `photo:…`, ou `fichier:…` pour le
  trombone. Vide, rien ne change, et les cartes d'avant partent comme avant. À la carte ET au clic, le serveur vérifie :
  - que chaque pièce appartient à un bien lié à CE contact, relue avec le jeton ;
  - que le fichier du trombone est dans SON dossier ;
  - les limites de l'envoi : 10 pièces, 8 Mo l'une, 18 Mo en tout.
- Ce que montre la carte : chaque pièce avec son nom, sa taille, « photo masquée » ou « ⚠ PIÈCE SENSIBLE », plus un
  avertissement s'il y a une pièce sensible.
- Au clic seulement :
  - un document est signé avec le JETON de la personne, pour 15 min ; c'est la règle de lecture du coffre qui juge,
    comme dans `createConsoleDocumentSignedUrl`. Il est ensuite marqué lu (`app_console_touch_document`) ;
  - pour une photo : notre grande dérivée, sinon l'adresse Hektor, comme l'écran ;
  - pour un fichier du trombone : `lien_lecture`, 15 min.
  Un refus du coffre fait échouer toute la carte : jamais un e-mail à moitié joint.
- Le résultat garde la trace : `pieces_jointes` avec le numéro, le nom, sensible et masquée, sans lien ni adresse.
  Le journal Gmail garde aussi les noms des fichiers (`attachment_filenames`).
- Comment une pièce devient « sensible » :
  - par le type GED quand le document est classé (`app_ged_classement` et `app_ged_type.sensible`) ;
  - sinon par le NOM, avec les règles des types sensibles de `gedTypeParNom.ts`, normalisation comprise. Prises
    seules, ces règles marquent plus large que la GED (une marque de trop, jamais une de moins).
  - Mesure en lecture le 18/11 : 2 034 des 25 394 documents au coffre seraient marqués par leur nom, surtout des CNI,
    des passeports et des questionnaires vendeur.
- La consigne du modèle (`assistant_service.py`) dit de passer par `lire_pieces_jointes`, que le client reçoit de
  vrais fichiers et jamais un lien, et qu'il faut dire à la personne qu'une pièce sensible part.
- À l'écran, la fin de la carte dit « E-mail envoyé avec N pièces jointes ».

**Contrôles** : 361 verts dans les essais des gestes (21 nouveaux, section 20), dont les témoins :
- document retiré, ou contact délié du bien, entre la carte et le clic : refusé, rien envoyé ;
- coffre qui refuse de signer : refusé ;
- carte sans pièce : identique à avant.
Les autres essais sont verts : IA 62, fichiers 17, lecteur 73, GED classer 36, GED lire 88, et le build passe.
✅ ÉPROUVÉ EN RÉEL le 18/11 à 00:27, sur sa demande (« fais un test sur un contact avec ma boîte mail »). L'essai a
été fait dans son Chrome, sur le contact d'essai 10354641 (Mme CLAUDE TESTCLAUDE, dont la fiche porte SON adresse) :
- Les pièces : le plan cadastral du bien 24113 (793 Ko), la 1re photo du bien, et un fichier du trombone nommé
  « CNI essai.pdf » (le PDF d'essai de 622 octets).
- L'assistant a DEMANDÉ lequel des trois « Plan cadastral.pdf » prendre, et il a signalé de lui-même le fichier
  « CNI » comme sensible.
- La carte nommait les 3 pièces avec leur taille, marquait « ⚠ PIÈCE SENSIBLE » et portait l'avertissement.
- Après le clic, l'écran a affiché « E-mail envoyé avec 3 pièces jointes. ». Capture :
  `notice/preuve_email_pieces_jointes_2026-11-18.jpg`.
- Ce qu'a gardé la base :
  - la carte est `executee`, et `resultat.pieces_jointes` porte les 3 pièces (le fichier CNI `sensible: true`), sans
    lien ni adresse ;
  - le journal Gmail (`app_google_workspace_action_log`) porte `gmail.send` `done` avec 3 pièces, 986 114 octets et
    les 3 noms ;
  - le document est marqué lu (`last_accessed_at` à 23:27:13 UTC, 7 s avant l'envoi).
- ✅ Frédéric a CONFIRMÉ le 18/11 : l'e-mail est arrivé dans sa boîte avec ses 3 pièces jointes.

**Ce que ça pourrait casser ailleurs** : rien d'existant. La route Gmail n'est pas modifiée, la fenêtre e-mail de
l'écran n'est pas touchée, et la carte sans pièce garde exactement le même comportement.

## 63. Le bouton « depuis l'ordinateur » de la FENÊTRE E-MAIL de l'écran : AUDIT (18/11, « vérifie ton travail puis enchaîne ») — rien codé

**Vérification d'abord (18/11, pendant le run de nuit)** : la carte des pièces jointes (§62) tient. Essais : gestes 361
verts, IA 62 verts. Render tourne sur `7e34d0a` (le code ; les commits suivants ne sont que des notes). En base, sur
24 h : aucune carte bloquée « en cours » ni en échec ; la carte de l'essai est `executee` avec ses 3 pièces, et le journal
Gmail porte les 3 noms.

**Ce qu'est la fenêtre aujourd'hui** : `ContactEmailComposerModal` (App.tsx ~45413), ouverte depuis la fiche contact,
pour TOUS les rôles. Elle joint des documents (lien signé 15 min) et des photos (adresse publique) d'UN bien lié au
contact, 10 au plus, puis appelle `/google-workspace/gmail/send`, qui télécharge chaque adresse et joint le fichier.
Rien ne vient de l'ordinateur.

**Mesuré (lecture)** : 80 e-mails partis par cette route depuis le 01/06, par 3 personnes, et UN SEUL avec des pièces
jointes : l'essai de la carte du 18/11. Les pièces jointes de la fenêtre n'ont donc jamais servi en vrai.

**Pourquoi on ne peut pas reprendre le trombone tel quel** :
- ses routes (`/assistant/fichiers/...`) sont fermées à qui n'a pas l'assistant (`_trombone_ouvert`), alors que la
  fenêtre sert à tout le monde ;
- l'écran ne peut pas déposer seul au coffre : la règle du coffre ne laisse déposer que dans le dossier d'un travail
  d'envoi qu'on vient de créer.

**Proposé (forme A)** : la même mécanique que le trombone, sous un autre dossier.
1. Serveur : deux routes ouvertes à toute personne connectée :
   - préparer un dépôt : contrôle du type et de la taille, puis une adresse d'envoi signée pour UN fichier, sous
     `temp/email/<la personne>/<numéro>/` ;
   - rendre un lien de lecture de 15 min, au moment d'« Envoyer », pour SES fichiers seulement.
   Types : ceux du coffre. Taille : 8 Mo par fichier, comme Gmail.
2. Écran : un bouton « Depuis l'ordinateur » dans le bloc « Pièces jointes ». Les fichiers choisis s'affichent avec leur
   nom, leur taille et une croix pour les retirer. Ils comptent dans les 10 pièces, et dans les 8 Mo par pièce et 18 Mo
   au total.
3. La route d'envoi Gmail n'est PAS touchée : elle reçoit un lien, comme pour un document.
4. Le ménage : `Console/nettoyer_temporaires_orphelins.js` apprend le dossier `temp/email/`. ⚠ Ce script n'est
   enregistré dans AUCUNE tâche planifiée (vérifié le 18/11) : les fichiers du trombone ne sont donc purgés par
   personne. À décider avec lui.

**Laissé pour un second temps (à sa décision)** : la case « ajouter aussi au bien » du §50. Ajouter un document passe
par la GED (type, pièce sensible) : c'est un autre geste.

**Écarté (forme B)** : envoyer le fichier lui-même dans la demande d'envoi Gmail. Il faudrait modifier la route Gmail,
partagée par plusieurs écrans, et le fichier transiterait par Render.

**Ce que ça pourrait casser ailleurs** :
- la fenêtre est partagée par tous les rôles : le bloc est ajouté, rien d'existant ne change ;
- la route Gmail, le worker et le run de nuit ne sont pas touchés ;
- au coffre, c'est un nouveau dossier temporaire ; sans le ménage, il grossit.

## 64. Bouton « depuis l'ordinateur » et ménage des temporaires : CODÉS le 18/11 (« Maintenant et aussi le ménage des fichiers temporaires ») — pas poussés

**Serveur**
- `backend/app/services/assistant_fichiers.py` : les fonctions du trombone prennent en option un autre dossier
  (`prefixe`) et une autre limite de taille (`taille_max`). Leurs valeurs par défaut sont celles du trombone, donc
  l'assistant ne voit aucune différence.
- `backend/app/routers/google_workspace.py` : quatre routes, ouvertes à toute personne connectée dont le profil est
  actif. Elles déposent sous `temp/email/<la personne>/<numéro>/`, avec 8 Mo au plus par fichier (la limite de Gmail) :
  - `POST /google-workspace/gmail/pieces/preparer` : contrôle du type et de la taille, puis une adresse d'envoi
    signée pour UN fichier ;
  - `POST .../{numero}/confirmer` : relit ce qui est au coffre ; un fichier hors règles est supprimé ;
  - `POST .../{numero}/lien` : un lien de lecture de 15 min, demandé au moment d'« Envoyer » ;
  - `DELETE .../{numero}` : la croix « Retirer ».
  La route `/gmail/send` n'est pas touchée : elle reçoit un lien, comme pour un document.

**Écran**
- `lib/api.ts` : `deposerPieceEmail`, `lienPieceEmail` et `retirerPieceEmail`.
- `App.tsx`, fenêtre `ContactEmailComposerModal` : dans le bloc « Pièces jointes », une section « Depuis
  l'ordinateur » avec un bouton « Choisir des fichiers » (plusieurs à la fois).
  - Chaque fichier est déposé dès qu'on le choisit, puis il s'affiche avec son nom, son type, sa taille et « Retirer ».
  - Les fichiers comptent dans les 10 pièces. Un fichier de plus de 8 Mo est refusé AVANT le dépôt, avec la raison.
  - « Envoyer » reste grisé tant qu'un dépôt est en cours.
  - Le client reçoit le fichier sous son nom d'origine (le coffre, lui, le range sans accents).
- `layout-overrides.css` : la ligne sans case à cocher, avec « Retirer » à droite.

**Ménage**
- `Console/nettoyer_temporaires_orphelins.js` accepte maintenant le dossier `temp/email/`.
- `scheduled/run_menage_temporaires.ps1` : le lanceur. Il appelle le script avec `--supprimer`, ou à blanc avec
  `-DryRun`, et écrit son journal dans `logs/scheduled/`.
- `scheduled/installer_tache_menage_temporaires.ps1` : il enregistre « GTI Menage Temporaires » à 13:00, recopié de
  l'installeur du balayage des photos, et vérifie la tâche réglage par réglage contre « GTI Entretien Documents ».
  ⚠ À lancer par Frédéric, dans une PowerShell administrateur.
- `monitoring/check_gti_health.py` : la tâche est déclarée AVANT d'être enregistrée, en « warning » (une journée ratée
  se rattrape le lendemain). 12 noms surveillés.
- Essai à blanc le 18/11 à 07:07, par le lanceur : 16 fichiers au coffre (1,2 Mo).
  - 11 à supprimer : les envois de documents d'essai de la GED du 12/11, tous `done`, dont une vraie CNI (recto et
    verso).
  - 5 gardés parce qu'ils ont moins de 2 jours : les fichiers du trombone d'hier.
  - Rien n'a été supprimé.

**Contrôles**
- Essais : fichiers 28 verts (11 nouveaux, section 7), dont les témoins :
  - un fichier de la fenêtre n'est pas lu comme un fichier du trombone, et inversement ;
  - un fichier annoncé petit mais déposé trop gros est refusé ET supprimé ;
  - un lien n'est jamais rendu hors du dossier demandé ;
  - un compte inactif reçoit un 403.
- Gestes 361 verts, IA 62 verts, build OK, les deux scripts PowerShell se lisent sans erreur.
- ⚠ PAS VU À L'ÉCRAN : la maquette locale n'a aucun contact, et aucune fiche n'y porte de propriétaire, donc la fenêtre
  ne s'ouvre pas. À voir en vrai après la mise en ligne, sur le contact d'essai 10354641 (sa propre adresse).

**Ce que ça pourrait casser ailleurs** :
- la fenêtre est partagée par tous les rôles : seul un bloc est ajouté, et les pièces du bien marchent comme avant ;
- la route d'envoi, le worker et le run de nuit ne sont pas touchés ;
- le ménage supprime pour de vrai tous les jours, sous les quatre gardes du script (14/10), qui retiennent un fichier
  d'un envoi en cours ou en échec, et un fichier qu'une ligne vivante cite.

**Mise en ligne et essai réel (18/11)**
- Poussé juste avant 10:07 (`4d64d71`, avec deux commits d'autres sessions dessous, accord de Frédéric). Render sert `4d64d71`
  depuis 10:07, Vercel est READY. La route `/gmail/pieces/preparer` répond 422 sans connexion ; une route inventée,
  essayée au même moment, répond 404 (témoin).
- ✅ ESSAI RÉEL VERT, avec son accord, dans son Chrome, sur le contact d'essai 10354641 (sa propre adresse) :
  - un PDF de 628 octets choisi « Depuis l'ordinateur » : la fenêtre affiche « 1/10 » et « PDF - 628 o » ;
  - au coffre : `temp/email/<son compte>/<numéro>/essai_piece_ordinateur_18-11.pdf`, 628 octets, `application/pdf` ;
  - envoyé à 10:14, l'écran dit « Email envoye. » ;
  - reçu (onglet « Échanges » du contact) avec la pièce `essai_piece_ordinateur_18-11.pdf (628 o)` : le vrai nom et la
    même taille.
- ⚠ Vu à l'écran : dans la ligne du fichier, le bouton « Retirer » était très pâle. CAUSE : il portait la classe
  `request-modal-close`, faite pour l'en-tête NOIR des fenêtres (texte blanc sur 10 % de blanc, styles.css l. 25655).
  ✅ CORRIGÉ le 18/11 : il prend `ghost-button button-subtle`, comme « Choisir des fichiers » juste au-dessus.
- ⛔ L'icône n'était PAS un défaut, je l'avais mal lu : c'est le pictogramme « document » que la fenêtre donne à TOUS
  les PDF (`consoleDocumentIconType` rend `content`) — « Avis de valeur.pdf », dans la liste du bien juste en dessous,
  porte le même. Rien changé.
- ✅ Tâche « GTI Menage Temporaires » enregistrée par Frédéric le 18/11 (prête, 1er passage 13:00). ⚠ Déclarée AVANT
  d'être enregistrée, elle a crié « tâche introuvable » au passage de 08:49 de la surveillance (attendu, mais je ne l'avais
  pas annoncé) ; au passage de 10:50 : « 12 suivies, 0 en anomalie », retour à la normale.

## 65. LOT 6 — les gestes PAR LA FENÊTRE de l'écran : AUDIT (18/11, « Les fenêtres (lot 6) ») — rien codé

**Périmètre** (inventaire §40, moins ce qui est déjà fait : ajouter une photo = carte §56, déposer des documents = carte
§60) : 1 créer une annonce / une estimation (+ le scan d'une fiche papier) · 2 offre / compromis / vente [DIR] · 3
traiter une demande à la direction [DIR] · 4 saisir l'estimation et générer l'avis de valeur · 5 le document de mandat /
l'avenant · 6 l'envoi en signature · 7 le bon de visite. Lu dans le code (App.tsx, AccueilAssistant.tsx, lib/, serveur),
points clés revérifiés à la main.

**Le patron existe déjà** (carte « déposer des documents », §59) : au clic « Valider », le serveur vérifie les droits et
l'objet, n'écrit RIEN, et rend `{"ouvrir": "depot_ged", ...}` (`assistant_gestes.py` ~2131) ; l'écran
(`agirSurCarte`, AccueilAssistant.tsx ~674) pose les fichiers dans un relais en mémoire (`lib/depotAssistant.ts`) et
ouvre la fiche, qui ouvre la fenêtre garnie. La personne finit DANS la fenêtre, avec les gardes de l'écran.

**Où vit chaque fenêtre** (ce qui décide du travail) :
- **Dans l'écran principal, donc ouvrable depuis l'Accueil sans changer d'écran** :
  - 1 création : `openDraftAnnonceModal()` (App.tsx 17991) ; le scan remplit par `applyDraftAnnonceScan(scan)` (18157) ;
    annonce ou estimation selon `draftAnnonceCreationStatus` (15519). Rôles de l'écran : admin, manager, commercial (21824).
  - 2 statut offre / compromis / vente : `openStatusChangeModal(dossier)` (19175), qui REFUSE hors direction (l. 19176).
    ⭐ Une porte extérieure EXISTE DÉJÀ : l'événement `ged:modifier-transaction` (BilanCompromis.tsx 26 ; écouté
    App.tsx 21908-21934 : relit le bien, ouvre la modale sur Offre ou Compromis, pré-remplit montant, dates, validité,
    séquestre, net vendeur).
  - 3 traiter une demande : `openRequestModal(appDossierId, 'pauline')` (17960) ; décision accepter / refuser / en cours,
    puis `handleUpdateDiffusionRequest` ; direction (Suivi).
  - 4 estimation et avis de valeur : `openEstimationEditor(item)` (17814), qui relit le bien et le propriétaire.
- **Dans la fiche du bien, donc il faut d'abord ouvrir la fiche, puis un relais** :
  - 5 document de mandat : `MandatDocumentEditor` (5458), monté dans la fiche et le registre ; porte extérieure
    `hektor:corriger-mandat`, mais elle exige un document DÉJÀ existant.
  - 6 envoi en signature : `EnvoiSignatureYoutrust` exige le PDF du mandat (un document existant) ; pas de porte directe ;
    interrupteur `signature_youtrust`.
- **Pas une fenêtre** : 7 le bon de visite est une page d'IMPRESSION (`openVisitVoucherPrint`, 46294) ; ⚠ elle doit être
  ouverte À L'INSTANT du clic (`window.open('')` avant tout appel au serveur), sinon le navigateur la bloque.

**Le principe proposé (le même pour les 7)** :
- l'assistant PROPOSE une carte « ouvrir la fenêtre X pour le bien Y, pré-remplie de : … » ; chaque valeur pré-remplie est
  ÉCRITE sur la carte (rien de caché) ;
- au clic « Valider », le serveur vérifie le rôle (le même qu'à l'écran) et que le bien est à la portée de la personne,
  n'écrit RIEN, et rend l'ordre d'ouverture ;
- l'écran ouvre la fenêtre pré-remplie ; la personne relit, corrige, et c'est SON clic dans la fenêtre qui fait le geste,
  exactement comme aujourd'hui.

**Ce que ça pourrait casser ailleurs** : les fenêtres sont partagées par tout le monde ; on ajoute seulement une porte
d'entrée, sans toucher à ce qu'elles envoient ni à leurs gardes. Points d'attention : (a) une valeur pré-remplie par
l'assistant peut être fausse — d'où la carte qui les affiche et la fenêtre qui les montre avant l'envoi ; (b) la fenêtre
s'ouvre par-dessus l'Accueil : à la fermeture, il faut revenir à la conversation (déjà fait pour les fiches, « Retour · À
la conversation ») ; (c) 5 et 6 ouvrent la fiche, l'Accueil peut être démonté : la conversation est gardée
(`sessionStorage`, déjà en place) ; (d) bureau seulement tant que le lot 5 (téléphone) n'est pas fait.

**Découpage proposé** (une marche = audit fin → « vas-y » → code → preuve) :
- 6a le mécanisme commun + **créer une annonce / une estimation** (tous les rôles qui l'ont à l'écran), puis le scan ;
- 6b **offre / compromis / vente** [DIR] (la porte existe : le moins de code) et **traiter une demande** [DIR] ;
- 6c **estimation et avis de valeur** ;
- 6d **document de mandat** puis **envoi en signature** (il faut la fiche et un document existant) ;
- 6e **bon de visite** (page d'impression ouverte au clic).

## 66. Marche 6a — la carte « ouvrir la création d'une annonce / d'une estimation » : AUDIT FIN (18/11, « Oui, 6a ») — rien codé

**La fenêtre** (lu dans App.tsx) :
- `openDraftAnnonceModal()` (17991) remet TOUT à zéro (agence et négociateur tirés de la session ; un commercial = lui-même),
  puis ouvre `draftAnnonceModalOpen`, rendu à la RACINE (22973) : elle s'affiche sur l'Accueil sans changer d'écran.
- Annonce ou estimation : `draftAnnonceCreationStatus` = estimation si `draftAnnonceScanEstimation` OU écran
  « estimations », sinon actif (15519) ; ce drapeau ne sert NULLE PART ailleurs (vérifié).
- Les cases : type de bien (`setDraftAnnonceTypeId`, libellé -> code par `draftAnnoncePropertyTypeIdFromLabel`), adresse,
  code postal, ville, note ; titre, prix, surface, pièces, chambres, terrain dans `draftAnnonceWizardFields` (`titre`,
  `prix`, `surfappart`, `nbpieces`, `NB_CHAMBRES`, `surfterrain`) ; mandant : aucun / nouveau / EXISTANT
  (`draftMandantChoice`, `draftExistingMandantId`, liste cherchée DANS LE PÉRIMÈTRE DU NÉGOCIATEUR choisi, 15775 — un id hors
  de cette liste est vidé, 15783).
- Rôles à l'écran : admin, manager, commercial (21824) = `TOUS_LES_ROLES` du serveur.
- ⚠ `applyDraftAnnonceScan` (18157) est fait pour le SCAN (message « champs récupérés depuis la fiche », revue par
  confiance, date d'estimation, et il force l'ESTIMATION) : on ne le réutilise PAS pour la carte ; il resservira tel quel à
  la marche du scan.

**Ce que je propose de coder** :
- **Serveur** (`assistant_gestes.py`) : un geste `ouvrir_creation_annonce` (rôles de l'écran : admin, manager, commercial).
  Paramètres : genre (estimation ou annonce), type de bien (libellé), adresse, code postal, ville, titre, prix, surface,
  pièces, chambres, terrain, note, et un mandant EXISTANT par son numéro de contact (relu avec le jeton de la personne :
  il doit exister et être à sa portée). La carte ÉCRIT chaque valeur. Au clic, tout est re-vérifié, RIEN ne s'écrit, et la
  réponse est `{"ouvrir": "creation_annonce", ...}`.
- ⛔ **Un NOUVEAU mandant ne passe pas par la carte** : son e-mail et son téléphone sont des coordonnées de client, qui ne
  doivent ni aller chez le modèle ni figurer sur une carte. La carte dit « mandant à saisir dans la fenêtre » ; la personne
  le tape dans la fenêtre, comme aujourd'hui.
- **Écran** : `AccueilAssistant.tsx` reconnaît `ouvrir: "creation_annonce"` (comme `depot_ged`) et appelle une nouvelle
  porte `onOuvrirCreation` ; `App.tsx` : `assistantOuvrirCreation(valeurs)` = `openDraftAnnonceModal()`, puis pose les
  valeurs dans les cases ci-dessus, le genre (le drapeau estimation), le mandant existant (recherche par son nom, puis son
  numéro), et un message « Pré-rempli par l'assistant : relis avant de créer ». La personne clique « Créer » DANS la fenêtre.
- **Consigne du modèle** : créer une annonce ou une estimation = cette carte (jamais un geste direct).
- **Essais** : la carte (rôles, valeurs écrites, mandant hors de portée refusé, rien d'écrit au clic, re-vérification),
  le témoin inverse (sans la carte, la consigne ne l'offre pas) ; build ; preuve réelle dans ton Chrome : ouvrir la fenêtre
  pré-remplie et la FERMER sans créer.

**Ce que ça pourrait casser ailleurs** : la fenêtre de création est la même pour tous ; on ne touche ni à ce qu'elle
envoie (`handleCreateDraftAnnonce`), ni à ses contrôles, ni à son ouverture par le bouton de l'écran (qui remet tout à
zéro, comme avant). ⚠ Si le mandant existant n'est pas dans la liste du négociateur choisi, la fenêtre le vide (son
comportement d'aujourd'hui) : la personne le choisit à la main.

**Maquette (18/11)** : https://claude.ai/artifact/5S2owJCDo2HWTBBefakeGo — 3 planches (la carte en fiche lisible, la
fenêtre ouverte pré-remplie, les fins de la carte), faite sur l'écran RÉEL vu dans son Chrome et sur la mesure (24
créations dans l'app en 4 mois, dont 18 estimations, presque toutes ses essais).
**Décision du 18/11** (ses mots : « Ok pour les 4 propositions et ta propo visuel pour la création d'une estimation ou
Annonce ») : ✅ le visuel ; ✅ les 4 points qui changent un comportement — (1) titre « Nouvelle estimation » quand c'en est
une ; (2) les cases remplies par l'assistant MARQUÉES dans la fenêtre, et une pastille par étape ; (3) « Rouvrir la
création » sur la carte ; (4) la carte dit « Estimation créée » quand la fenêtre a créé.
Sa question ensuite : le MÉCANISME du pré-remplissage (« l'utilisateur n'a pas besoin de préciser son nom sauf cas
admin ») — expliqué en détail, pas encore de « vas-y ».
**Sa demande suivante (18/11)** : « tous les champs sont-ils possibles si je dicte d'autres informations ? » et le SCAN
DANS 6a (sources : sa phrase, le contact existant, le négociateur pour l'admin, l'agenda ET les photos de la fiche papier).
Mesuré : le format du scan (`DraftAnnonceSheetScanFieldKey`, lib/api.ts 885) connaît **150 cases**, plus la composition
pièce par pièce et l'état poste par poste ; `applyDraftAnnonceScan` sait toutes les poser dans la fenêtre. Proposé : la
carte parle CE format (un seul remplisseur pour la dictée et le scan) ; le scan des photos jointes est fait PAR LA FENÊTRE
(sa route d'aujourd'hui), jamais par le modèle de la conversation, qui ne voit pas le contenu des fichiers. Hors dictée :
les coordonnées d'un nouveau mandant (e-mail, téléphone, adresse) — tapées dans la fenêtre ou lues par le scan. À
trancher : qui l'emporte quand la dictée et la fiche scannée disent deux choses différentes.
✅ **TRANCHÉ le 18/11 : « Ma dictée prime »** (les désaccords sont listés dans le bandeau de la fenêtre).

**Le périmètre FINAL de 6a, tel que présenté avant le « vas-y »** :
- Serveur : le geste `ouvrir_creation_annonce` (admin, manager, commercial) ; il reçoit le genre, des cases dans le format
  du scan (liste fermée des 150 clés, SANS les coordonnées d'un mandant), la composition, un mandant existant (n° de
  contact relu avec le jeton), un négociateur (admin / manager seulement, relu dans les négociateurs actifs), des photos
  de fiche (fichiers du trombone, images, 5 au plus). Au clic : tout re-vérifié, RIEN écrit, liens de lecture courts des
  photos. Consigne : créer = cette carte ; l'agenda se lit avec la lecture existante.
- Écran : la porte `onOuvrirCreation` ; la fenêtre s'ouvre (remise à zéro comme aujourd'hui), lit les photos par SA route
  de scan si la carte en porte, puis pose la dictée PAR-DESSUS (elle prime) en notant chaque désaccord ; le genre ; le
  mandant existant ; le négociateur. Les 4 points acceptés : titre « Nouvelle estimation » ; les cases de l'assistant
  marquées (point magenta, fond rosé) et une pastille par étape ; bandeau « Pré-rempli par l'assistant : N cases » avec
  les désaccords ; « Rouvrir la création » ; la carte passe à « Estimation créée » quand la fenêtre a créé (le numéro
  provisoire noté sur la carte par le serveur, pour survivre à un rechargement).
- Ce que ça touche chez tout le monde : le titre de la fenêtre (« Nouvelle estimation » aussi pour le scan et l'écran
  Estimations, ce qui est juste) ; le marquage ne s'allume que si l'assistant a pré-rempli — une ouverture par le bouton
  de l'écran remet tout à zéro, la fenêtre reste celle d'aujourd'hui.
- Contrôles : essais serveur (rôles, clés refusées hors liste, coordonnées refusées, contact hors de portée, négociateur
  réservé à la direction, rien d'écrit au clic) + témoin inverse ; build ; dans ton Chrome : ouvrir pré-rempli, regarder,
  FERMER sans créer. Créer pour de vrai (une estimation d'essai chez Hektor) = à ton accord, à part.
- **Ajout demandé le 18/11 (« l'assistant peut-il remettre le PDF vierge de la modale scan IA ? »)** : c'est le lien
  « Télécharger le patron vierge » (App.tsx ~22866) vers `/patron-fiche-saisie.html` (`apps/hektor-v1/public/`), une PAGE
  À IMPRIMER (pas un fichier PDF : on l'imprime ou on l'enregistre en PDF depuis le navigateur). Proposé : un lien de
  plus dans les réponses de l'assistant, `[patron vierge](patron:fiche-saisie)`, rendu en bouton « Ouvrir le patron
  vierge à imprimer » (nouvel onglet), comme les liens `annonce:` ou `contact:` ; une ligne de consigne. Rien d'écrit,
  aucune carte (c'est une lecture).

## 67. Marche 6a : CODÉE le 18/11 (sur « Vas-y ») — pas poussée

**Serveur**
- `assistant_gestes.py` : le geste `ouvrir_creation_annonce` (admin, manager, commercial). Les cases = `FIELD_KEYS` du scan
  (`openai_listing_sheet_service`), MOINS les 16 cases du mandant et agence / négociateur (132 cases), chacune avec son
  libellé ; nombres normalisés (« 245 000 € » -> 245000), oui/non, code postal à 5 chiffres, aucune adresse e-mail
  dans une case ; composition (40 pièces au plus) ; mandant EXISTANT relu avec le jeton (archivé = refusé) ; négociateur
  pour la DIRECTION seulement (fiche active, homonymes = demander) ; photos de la fiche : images JPEG / PNG / WebP,
  5 au plus, 12 Mo (= la route de scan). Au clic : tout re-vérifié, RIEN écrit, liens de lecture courts des photos.
  `fiche_carte` : ce que l'écran affiche (titre, 4 chiffres, lignes, ce qui reste à remplir), rendue avec la carte
  (flux et relecture). Consigne : créer = cette carte (retiré de « pas encore »), l'agenda au retour d'un RDV, le
  mandant cherché (plusieurs = demander), le lien `patron:fiche-saisie`.
- `routers/assistant.py` : `POST /actions/{id}/rouvrir` (re-vérifie comme au clic, liens frais, l'état de la carte ne
  bouge pas) et `POST /actions/{id}/suite` (la carte garde « créée », sans les liens expirés) ; seulement SA carte
  « créer » déjà validée. `assistant_service.noter_suite`.

**Écran**
- `AccueilAssistant.tsx` : la carte « créer » en FICHE (planche 1), « Ouvrir la création » / « Refuser » ; après le
  clic « Fenêtre ouverte à HH:MM » + « Rouvrir la création » ; puis « Estimation créée » + « Ouvrir la fiche ». Le lien du
  patron vierge (nouvel onglet). `lib/assistant.ts` : types, `rouvrirCarte`, `noterCreationCarte`, l'événement
  `gti-assistant-creation-faite`, un exemple en mode maquette (une question contenant « estimation »).
- `App.tsx` : `assistantOuvrirCreation` = la fenêtre remise à zéro (comme au bouton), la fiche papier lue par la route
  de scan de l'écran, puis la dictée PAR-DESSUS en UN SEUL passage du remplisseur du scan (la revue de confiance du scan
  est gardée, la dictée n'y entre pas), désaccords notés ; genre, mandant existant, négociateur (direction). Le MIROIR du
  scan est sorti en constante (`SCAN_MIROIR`, remplissage inchangé) pour savoir quelles cases marquer. Titre « Nouvelle
  estimation » ; bandeau « Pré-rempli par l'assistant : N cases » (+ les désaccords, « Revenir à la conversation ») ; un
  point magenta et un fond rosé sur chaque case remplie (19 cases écrites à la main + les cases des groupes + le type, le
  mandant, la composition) ; une pastille par étape. Après « Créer » : la carte est prévenue (et le serveur le garde).
- Styles : `accueil-assistant.css` (préfixe `asi-cr-`), `layout-overrides.css` (`draft-annonce-assistant`, `is-assistant`).

**Contrôles**
- Essais : gestes **391 verts** (30 nouveaux, section 21, dont 7 témoins : mandant archivé, photo retirée, case interdite
  glissée dans les paramètres, carte de direction cliquée par un commercial, rouvrir hors règle…), IA **63**, fichiers
  28, lecteur 73. Témoin inverse de la consigne : la version en ligne échoue au contrôle, la nouvelle le passe.
- Build OK. Vu dans la maquette locale (Chrome de Frédéric, localhost:5198) : la carte = planche 1 ; « Ouvrir la
  création » -> fenêtre « Nouvelle estimation », bandeau « 11 cases », pastilles 7 / 3 / 1, cases marquées, type « Maison »
  choisi ; fermée -> « Fenêtre ouverte à 12:32 » ; « Rouvrir » rouvre. ⭐ TÉMOIN : la même fenêtre ouverte à la main
  (« Nouvelle annonce » -> « Manuellement ») : titre « Nouvelle annonce », 0 bandeau, 0 marque, 0 pastille.
- ⚠ PAS VU : le scan des photos jointes et « Estimation créée » (il faut créer pour de vrai : chez Hektor, à son accord) ;
  le négociateur choisi par la direction ; le téléphone (lot 5, l'assistant n'y est pas encore).

## 68. AUDIT (18/11, ses trois questions) : les QUESTIONS avant la carte, l'avis de valeur APRÈS la création, et
## « une estimation sur une annonce existante » = ÉDITER L'AVIS DE VALEUR — rien codé, 6a toujours pas poussée

Ses mots : « Est-ce possible que l'assistant pose quelques questions à l'utilisateur pour avoir suffisamment de
renseignements […] Ensuite le geste est la création d'une annonce statut « estimation » : l'assistant doit proposer ensuite
d'éditer le dossier d'estimation. Oui / NON. Et si l'utilisateur demande une estimation sur une annonce déjà existante, cela
veut dire éditer le rapport d'estimation. […] il faut absolument que tu comprennes parfaitement les mécanismes. »

### A. LE MÉCANISME DE L'AVIS DE VALEUR (lu dans le code et la base)

Il y a TROIS endroits, et c'est ce qui compte pour la suite :
1. **La table `app_dossier_estimation`** (une ligne par bien, patch du 01/07) : `sources` (marché DVF, cadre de vie,
   cadastre, BDNB, DPE ADEME, patrimoine, loyers, copropriété, INSEE — chacune `{ok, data, fetched_at}`, fusionnées clé par
   clé par `app_upsert_dossier_estimation_source`) ; `scan_draft` (le BROUILLON de l'avis : valeurs basse / estimée /
   haute, état et barème par poste, points forts / de vigilance, argumentaire, avis, charges, DPE, chauffage… —
   `app_upsert_dossier_estimation_scan_draft`) ; `valeurs` (basse / estimée / haute, écrites par le WORKER après chaque PDF).
   Mesuré : 33 lignes, 25 avec des sources, 11 avec un brouillon, 11 avec des valeurs. ⚠ Lisible par TOUT compte connecté
   (règle « select using (true) ») : noté, hors sujet.
2. **L'éditeur** `EstimationDocumentEditor` (App.tsx 6400) — 6 onglets : Le bien (lecture seule : les données de la
   fiche, « pour les corriger, modifiez la fiche du bien »), Bien & valeur, État, Points, Charges, Marché (DVF) ; « Tout
   générer » charge marché + cadre + cadastre + BDNB, DPE, patrimoine, loyers, copro, INSEE (et les mémorise) ;
   « Améliorer les textes (IA) » (reformule, n'invente pas). Son point de départ : le prix ± 5 % et le propriétaire, PUIS
   le brouillon `scan_draft` par-dessus. Deux portes : la FICHE du bien (onglet Estimation, « Générer le PDF de l'avis »,
   `estimEditorOpen`) et l'écran ESTIMATIONS (« Envoyer le dossier » -> `openEstimationEditor`, état à la RACINE de l'app,
   donc ouvrable depuis l'Accueil). Aucune garde de rôle.
3. **Le PDF** : « Générer » pose le travail `generate_estimation_pdf` (la charge = ce que montre l'éditeur) ; le worker
   complète avec les sources mémorisées, fabrique le PDF (~30 s), le range dans les DOCUMENTS du bien et l'envoie chez
   Hektor (`upload_document_to_hektor`), puis écrit `valeurs`. Option : « Générer + envoyer » = un e-mail au propriétaire
   (`sendEstimationEmail`, depuis la boîte du négociateur) — ce qui part chez un CLIENT.
Mesuré : 37 avis de valeur générés depuis juin (Frédéric 31, Franck 5, 1 sans auteur), le dernier le 30/10 : presque des
essais.

⛔ **TROUVÉ, à trancher (comportement)** : ce qu'on saisit dans l'éditeur N'EST PAS GARDÉ. Fermer sans générer perd
tout ; et même après un PDF, rouvrir l'éditeur repart du prix ± 5 % (+ le brouillon du scan) : il NE relit PAS les
`valeurs` du dernier avis, ni ses textes (état, points, argumentaire), qui ne sont gardés nulle part sauf DANS le PDF.
Donc aujourd'hui, « éditer le rapport d'estimation existant » = le REFAIRE, sauf les sources et le brouillon du scan.

### B. LES QUESTIONS AVANT LA CARTE — réalisable, sans écran nouveau

- C'est une conversation : l'assistant peut déjà demander. Ce qui manque, c'est une RÈGLE : quelles informations sont
  « suffisantes ». La fenêtre elle-même n'exige presque rien (une agence, un négociateur, la cohérence du mandant).
- Proposé : (1) une liste d'ESSENTIELS par genre, que SA décision fixe (proposition : estimation = type, adresse avec code
  postal et ville, surface, pièces, terrain pour une maison, le mandant (existant ou « nouveau ») ; annonce = la même chose
  + le prix) ; (2) le modèle pose les questions manquantes EN UNE FOIS (3 ou 4 au plus, regroupées), saute ce que l'agenda
  ou le contact lui donnent déjà, accepte « je ne sais pas » (la case reste vide) ; (3) une GARDE au serveur : une carte à
  qui il manque un essentiel est refusée avec la liste (« il manque : surface, pièces ») — le modèle doit alors demander.
  C'est la garde qui rend la règle sûre ; la consigne seule ne l'est pas.

### C. APRÈS LA CRÉATION D'UNE ESTIMATION : proposer l'avis de valeur — OUI, avec deux contraintes mesurées

- La carte « Estimation créée » gagne « Préparer l'avis de valeur » (et l'assistant le propose en une phrase).
- ⚠ Les coordonnées GPS viennent de HEKTOR (la relecture d'après-création) : les biens nés dans l'app les ont après
  (63329, 63330, 63331 : oui ; 63147 : 0,0, géolocalisation ratée). Sans elles, marché / cadre / cadastre ne se chargent
  pas -> le bouton attend le numéro Hektor (« en attente de Hektor… »).
- ⚠ Les valeurs et textes dictés pour l'avis (fourchette, points, état…) passent par le brouillon `scan_draft`, écrit
  seulement quand Hektor a confirmé la création (file en mémoire + localStorage, App.tsx ~16409) : même attente.

### D. « UNE ESTIMATION SUR UNE ANNONCE EXISTANTE » = ÉDITER L'AVIS DE VALEUR

- La carte (même patron que 6a) ouvre l'ÉDITEUR du bien (la porte de l'écran Estimations, `openEstimationEditor`),
  PRÉ-REMPLI de ce que la personne dicte : fourchette, état et barème, points forts / de vigilance, argumentaire, avis,
  charges. RIEN n'est écrit par la carte : c'est la personne qui clique « Générer » (ou « Générer + envoyer » au
  propriétaire) DANS l'éditeur.
- Pré-remplir EN MÉMOIRE (une porte de plus vers l'éditeur), PAS dans `scan_draft` : écrire le brouillon écraserait
  celui de la fiche papier et resterait pour tout le monde.
- Les caractéristiques du bien (surface, pièces…) NE se changent PAS dans l'éditeur (onglet en lecture seule) : si la
  personne en dicte, c'est la carte « modifier le bien » (existe) — à dire par l'assistant.
- Dépend du trouvé de A : sans reprise des derniers textes, l'éditeur repart du prix ± 5 %.

### À trancher par lui
1. La liste des ESSENTIELS (estimation / annonce) et la garde au serveur.
2. « Préparer l'avis de valeur » après « Estimation créée » (C).
3. L'éditeur pré-rempli pour une annonce existante (D).
4. Le trouvé de A : faut-il que l'éditeur GARDE sa saisie (et relise le dernier avis) ? C'est un changement de
   l'écran pour tout le monde (aujourd'hui rien n'est gardé).

## 69. Ses réponses (18/11) et l'audit qu'il demande avant le point 4

**Décisions** (ses mots : « 1. OK pour la liste, 2. oui, 3. oui, 4. à auditer avant ») : ✅ la liste des essentiels et la
garde au serveur ; ✅ « Préparer l'avis de valeur » après « Estimation créée » ; ✅ l'éditeur pré-rempli pour une annonce
existante ; ⏳ le point 4 : audit ci-dessous.

**⛔ CORRECTION (il m'a repris : « tu trompes l'app ») — les coordonnées NE dépendent PAS de Hektor.** L'app sait les
calculer elle-même depuis l'adresse : `geocodeAddress` (lib/api.ts 4900, Géoplateforme `data.geopf.fr`, garde-fou score
≥ 0,35), déjà utilisé quand on modifie l'adresse d'un bien (App.tsx ~35231 : lat/lon posées tout de suite dans notre
calque, json_map -> `latitude_detail`). Ce qui est vrai : à la CRÉATION, l'app ne géocode pas aujourd'hui
(`createHektorDraftAnnonceJobOptimistic`, api.ts 13193, ne pose ni latitude ni longitude) ; elles arrivent ensuite par la
relecture Hektor. ➡ Pour l'assistant : si le bien n'a pas encore de coordonnées, l'éditeur géocode l'adresse lui-même
(même fonction) — PAS d'attente de Hektor. (Le brouillon dicté, lui, attend toujours la confirmation de création,
App.tsx ~16409.)

**« L'assistant va-t-il bien générer tous les calculs (DVF, toutes les bases) ? »** — lu dans le code :
- « Tout générer » de l'éditeur (`loadAllEditor`, App.tsx ~6603) lance EN PARALLÈLE : marché DVF (`loadDvfComparables`,
  rayon 12 km, 24 mois, élargi à 48 avant la distance ; terrain comparable pour une maison ; ⚠ seulement maison et
  appartement, par construction), cadre de vie (carte IGN, commodités, risques), cadastre (parcelle, contenance, PLU ; si le
  point tombe sur la voie, un sélecteur de parcelle) ; et MÉMORISE BDNB, DPE ADEME, patrimoine / ABF, loyers, INSEE, et la
  copropriété si le bien est en copro. Tout passe par les coordonnées.
- ⚠ C'est un BOUTON : rien ne se calcule tout seul à l'ouverture. Et le worker, au PDF, recharge les sources mémorisées,
  recalcule commodités et INSEE, va chercher le cadastre s'il manque — mais PAS le marché DVF : sans « Tout générer » (ni
  DVF mémorisé), l'avis sort SANS sa page Marché.
- ➡ Proposé : ouvert par l'assistant, l'éditeur lance « Tout générer » de lui-même (la même fonction que le bouton, qui
  mémorise les sources comme aujourd'hui) ; la carte et l'éditeur disent ce qui a été calculé et ce qui manque.

**Point 4 — l'éditeur ne garde rien : l'audit**
- Le contenu du dernier avis EXISTE DÉJÀ : c'est la charge du travail `generate_estimation_pdf` (valeurs, état et barème,
  points, argumentaire, avis, charges, propriétaire). Mesuré : 13 biens ont un avis, 35 travaux portent les textes. Lisible
  par celui qui l'a demandé ou qui a le droit de travailler sur le bien (règle `app_console_job_select_scope`).
- A — **REPRENDRE LE DERNIER AVIS à l'ouverture** (lecture seule, aucun changement de base) : l'éditeur part du dernier
  avis s'il y en a un, sinon du brouillon (scan / assistant), sinon du prix ± 5 % ; un bandeau dit « repris de l'avis du
  30/10 ». Ce que ça change pour tout le monde : rouvrir l'éditeur montre le dernier avis au lieu de repartir de zéro.
  ⚠ Si le prix a changé depuis, la fourchette reprise est ancienne : le bandeau le dit.   <- RECOMMANDÉ d'abord
- B — **ENREGISTRER LA SAISIE EN COURS** (sans générer) : une colonne de plus dans `app_dossier_estimation` (patch en
  base, son accord) et une écriture à chaque modification. ⚠ La table est lisible par TOUT compte connecté : les textes
  de l'avis le seraient aussi (l'adresse e-mail du propriétaire, jamais). Plus lourd ; à faire seulement si A ne suffit pas.

✅ **TRANCHÉ le 18/11 : « A »** (reprendre le dernier avis ; B non retenu).

## 70. La marche suivante (6b-estimation), telle que présentée avant le « vas-y »

1. **Les essentiels et la garde** (carte « créer », serveur) : estimation = type, adresse (code postal + ville), surface,
   pièces, terrain pour une maison, mandant (existant, ou « nouveau » dit clairement) ; annonce = la même chose + le prix.
   Il en manque -> la carte est refusée avec la liste ; consigne : les demander EN UNE FOIS (3 ou 4 questions au plus),
   sauter ce que l'agenda ou le contact donnent, accepter « je ne sais pas » (le mandant « nouveau » vaut réponse).
2. **« Préparer l'avis de valeur »** sur la carte « Estimation créée » (et l'assistant le propose) : ouvre l'éditeur du
   bien créé (porte de l'écran Estimations, `openEstimationEditor`), dès que la fiche existe chez nous.
3. **La carte « avis de valeur » d'une annonce existante** : ouvre l'éditeur du bien, PRÉ-REMPLI EN MÉMOIRE de la dictée
   (fourchette, état et barème, points, argumentaire, avis, charges) ; rien d'écrit par la carte ; la personne génère
   (ou génère + envoie au propriétaire) dans l'éditeur. Tous les rôles (l'éditeur n'a pas de garde à l'écran).
4. **L'éditeur ouvert par l'assistant lance « Tout générer » de lui-même** (la même fonction que le bouton) et, s'il n'y a
   pas de coordonnées, GÉOCODE l'adresse (`geocodeAddress`) ; il dit ce qui a été calculé et ce qui manque.
5. **Point 4 A, pour tout le monde** : à l'ouverture, l'éditeur part du DERNIER AVIS (la charge du dernier
   `generate_estimation_pdf` « done » du bien, lue avec le jeton), puis le brouillon remplit les cases restées vides, puis
   le prix ± 5 % ; la dictée de l'assistant passe par-dessus tout. Bandeau « repris de l'avis du JJ/MM » (+ « le prix a
   changé depuis » si c'est le cas).
**Ce que ça pourrait casser ailleurs** : l'éditeur est partagé (fiche, écran Estimations) : (5) change ce qu'on voit en le
rouvrant ; (4) ne joue que si l'assistant l'ouvre ; la carte « créer » refusera désormais une demande trop pauvre (c'est
voulu). Rien ne change dans le PDF, le worker, ni la base.
**Contrôles prévus** : essais serveur (essentiels, garde, carte avis de valeur) ; build ; maquette locale (éditeur pré-rempli,
Tout générer lancé, reprise du dernier avis) ; en vrai dans son Chrome : rouvrir l'avis d'un bien qui en a un, SANS générer.

## 71. 6a POUSSÉE ; la marche du §70 CODÉE le 18/11 (sur « Oui, pousse et code ») — pas poussée

**6a en ligne** : `c6a37c3`, poussé avec l'accord de Frédéric pour les 8 commits d'une autre session dessous (GED §12.36-12.39,
classeur « hors jeu », 43091, audit des compromis). Render et Vercel servent `c6a37c3` (vérifié).

**Ce qui est codé (rien poussé) :**
1. **Les essentiels et la garde** (`assistant_gestes.py`, `_exiger_essentiels`) : sans fiche papier jointe, la carte
   « créer » exige type, adresse, code postal, ville, surface, pièces, le terrain pour une maison (`_une_maison` : maison,
   villa, pavillon, longère, ferme, chalet, mas), le mandant (existant, ou `mandant_nouveau`), et le prix pour une annonce.
   Il en manque -> refus avec la liste (« Il manque, pour cette estimation : surface habitable, pièces… Pose ces questions
   EN UNE FOIS »). « Je ne sais pas » = `inconnus` (seulement pour un essentiel), dit sur la carte et mis dans « Restera à
   remplir ». Re-vérifié AU CLIC (et à « Rouvrir »). ⚠ AVEC la fiche papier jointe, la garde s'efface : c'est le scan de la
   fenêtre qui lira ces informations. Consigne : les questions manquantes en une fois, 3 ou 4 au plus.
2. **« Préparer l'avis de valeur »** sur la carte « Estimation créée » (AccueilAssistant, `preparerAvis`) : ouvre l'éditeur
   du bien créé (sans dictée ; le brouillon de la fiche le pré-remplit) ; la consigne fait proposer l'avis après une
   estimation créée.
3. **La carte « avis de valeur »** (geste `ouvrir_avis_de_valeur`, tous les rôles) : `champs` = les clés du brouillon de
   l'éditeur (basse / estimee / haute, etatNote 1-5, etatLabel, etatTexte, toiture, menuiseries, pointsForts,
   pointsVigilance, argumentaire, commentaire, taxeFonciere / energie / eau / assurance) et `postes` = le barème par code
   (`POSTES_AVIS` = ESTIM_POSTES, `NIVEAUX_AVIS` = ESTIM_NIVEAUX). Refusés : une caractéristique du bien (proposer_modifier_bien),
   un e-mail, une fourchette à l'envers, une note hors 1-5, un montant en lettres, un poste inconnu, un bien hors de portée.
   Le clic n'écrit RIEN : `{ouvrir: avis_de_valeur, app_dossier_id, hektor_annonce_id, champs, postes}` -> l'App ouvre
   l'éditeur par `openEstimationEditor(item, assistant)` (la porte de l'écran Estimations). « Rouvrir » ouvert aux deux
   cartes qui ouvrent une fenêtre (`GESTES_QUI_OUVRENT`) ; « suite » reste à la création. Retiré de « pas encore ».
4. **Ouvert par l'assistant, l'éditeur lance « Tout générer » seul** (`autoLance`, une fois) ; sans coordonnées sur la
   fiche, il géocode l'adresse privée puis publique (`geocodeAddress`) EN MÉMOIRE (`coordsSecours`, rien d'écrit sur le
   bien) ; le bandeau dit ce qui est calculé et ce qui manque (`sourcesMemorisees` : ce que « Tout générer » a réussi à
   mémoriser). Les 3 chargements + « Tout générer » lisent la position par `coordsDuBien()` (fiche d'abord, comme avant).
5. **Point 4 A, pour tout le monde** (`loadDernierAvisDeValeur`, api.ts ; `avisVersBrouillonEditeur`) : à l'ouverture,
   couche par couche, chacune n'écrasant que par une valeur non vide : prix ± 5 % -> brouillon (scan) -> DERNIER AVIS
   (charge du dernier `generate_estimation_pdf` « done ») -> dictée de l'assistant. Le propriétaire n'est pas repris (le
   contact de la fiche fait foi). Bandeau `.avd-provenance` : « Repris de l'avis du JJ/MM/AAAA » (+ « le prix du bien n'est
   plus la valeur de cet avis : vérifie la fourchette » si le prix diffère de la valeur estimée de l'avis), « Pré-rempli
   par l'assistant : N cases ». Le barème se fusionne poste par poste (avant : remplacé en bloc par celui du scan).

**⚠ Ce qui reste une écriture, et n'est PAS neuf** : « Tout générer » mémorise les sources (`app_upsert_dossier_estimation_source`),
exactement comme le bouton. Lancé seul quand l'assistant ouvre l'éditeur, il écrit donc ces sources pour le bien.

**Contrôles** : serveur 415 verts (section 22 : 24 nouveaux, dont 3 témoins au clic) ; IA 65 verts ; build vert (types
compris). Maquette locale (sans base : `hasSupabaseEnv` faux, donc rien ne peut s'y écrire) : la carte « Avis de valeur »,
« Valider » -> l'éditeur s'ouvre sur « Bien & valeur », bandeau « Pré-rempli par l'assistant : 3 cases », « Tout générer »
lancé seul (« Calculé : cadre de vie. Manque : marché DVF, cadastre… » — normal sans base), note 4/5, points forts, barème
toiture « neuf / refaite 2019 », les autres postes vides. **PAS VU** : la reprise d'un vrai avis (il faut la base), le
géocodage d'un bien sans coordonnées, « Préparer l'avis de valeur » après une vraie création, le témoin « éditeur ouvert à
la main » à l'écran (la maquette n'a aucune estimation ; par le code, ni bandeau ni calcul sans assistant et sans avis).
**Essai réel prévu** (son accord) : rouvrir l'avis de 62774 (avis du 23/07 : 420 000 / 450 000 / 470 000, « bon état
général », taxe foncière 1 600, énergie 6 000) SANS générer, par l'écran Estimations ou la fiche.

## 72. Marche §70-71 EN LIGNE (`2e1900e`, 18/11) et l'ESSAI RÉEL de la reprise du dernier avis — vert

- Poussé avec l'accord de Frédéric, avec `ce42707` d'une autre session dessous (une note : le dossier de reprise du
  classeur). Render sert `2e1900e` ; Vercel sert le code du bandeau (`avd-provenance` trouvé dans les fichiers en ligne).
- ⚠ 62774 (le témoin prévu) n'est PLUS un bien vivant : clos le 21/10 par l'essai ⑦-3a -> absent d'`app_dossiers_current`.
  Pris à la place : **24935** (EM28570, Firminy, « caroline TEST 1 », négociateur Franck, bien d'essai), avis du 02/07.
- **Essai** (son Chrome, écran Estimations -> « Envoyer le dossier d'estimation » -> l'éditeur ; fermé par « Retour »,
  RIEN généré, rien écrit) : bandeau « Repris de l'avis du 02/07/2026. » ; fourchette 142 501 / 150 001 / 157 501 ;
  5 points forts et 4 de vigilance ; charges 1 000 / 300 / 90 / 90 ; état 5/5. **Recoupé en base** : la charge du dernier
  `generate_estimation_pdf` done (02/07 18:06) porte exactement ces valeurs (nf 5, nv 4, note 5). Ouvert à la main, pas de
  calcul automatique, pas de bandeau « assistant » — comme voulu.
- **PAS VU en réel** : le bandeau « le prix n'est plus la valeur de cet avis » (24113 : prix 128 787, avis 200 000 ; mais
  son mandat est clos, la fiche en lecture seule n'offre pas l'éditeur) ; la carte de l'assistant en vrai (il faut une
  conversation : le modèle, la carte, son clic -> « Tout générer » ÉCRIT les sources du bien, comme le bouton) ; la garde
  des essentiels avec le vrai modèle ; « Préparer l'avis de valeur » après une vraie création.

## 73. ESSAI RÉEL de la carte « avis de valeur » (18/11, « Oui, essaie la carte ») — vert, rien généré

Sur 24935 (bien d'essai), dans son Chrome, par le VRAI modèle. Question : « Prépare l'avis de valeur de l'annonce 24935 :
fourchette 145 000 à 158 000, valeur 152 000, état 4 sur 5, toiture bon état refaite en 2015, point fort : jardin plat au
calme. »
- **La carte** (proposer_ouvrir_avis_de_valeur, du premier coup) : Fourchette basse 145 000 € ; haute 158 000 € ; valeur
  estimée 152 000 € ; État 4 ; Points forts « Jardin plat au calme » ; barème toiture / charpente bon état.
- **Valider (15:56)** -> l'éditeur s'ouvre sur « Bien & valeur » ; bandeau : « Repris de l'avis du 02/07/2026. /
  Pré-rempli par l'assistant : 6 cases, par-dessus l'avis repris. / Calculé : marché DVF, cadre de vie, INSEE, loyers,
  DPE ADEME, bâti (BDNB), patrimoine. Manque : cadastre ». Cases : 145000 / 152000 / 158000, note 4 (l'avis disait 5),
  toiture « bon » + « Refaite en 2015 », points forts = « Jardin plat au calme » (la dictée REMPLACE la case : les 5 de
  l'avis partent, voulu par « ma dictée prime »), points de vigilance et charges REPRIS de l'avis (4 lignes ; 1000/300/90/90).
  Marché : 16 comparables, rayon 1 km, 4 ans, médiane 1 734 €/m², estimation DVF 208 140 €.
- **Recoupé en base** : `app_dossier_estimation` de 1352134 -> 5 sources réécrites à 14:56 (dpe, bdnb, insee, loyers,
  patrimoine, toutes ok) ; dvf / cadre / cadastre NON réécrits (ils restent dans l'éditeur, comme le bouton) ; copro pas
  appelée (pas en copro) ; `valeurs` inchangées (aucun PDF) ; brouillon intact ; 0 travail posé. Fermé par « Retour ».
- **Trouvés (à trancher, rien corrigé)** :
  1. ⚠ Cadastre : « le point du bien ne tombe sur aucune parcelle — choisis la bonne ». Or le bien a une parcelle RETENUE
     (`sources.cadastre`, 02/07) que l'éditeur précharge ; « Tout générer » (le bouton comme l'automatique) la remplace
     dans l'éditeur par le résultat raté du point. Le bandeau dit « Manque : cadastre » alors qu'une parcelle existe. Piste :
     ne pas relancer le cadastre quand une parcelle retenue est chargée, et dire « parcelle à choisir » plutôt que
     « manque ». Comportement du bouton existant, rendu plus fréquent par le lancement automatique.
  2. Cadre de vie : « Firminy · 0 école, 0 commerce » — douteux pour Firminy ; service existant, non audité ici.
  3. La dictée d'un point fort remplace la liste reprise (au lieu de l'ajouter) : conforme à « ma dictée prime », à
     confirmer par lui.

## 74. Cadastre : la parcelle retenue l'emporte, le sélecteur s'ouvre partout — CODÉ (18/11, « corrige ») ; le DPE : AUDIT

Ses mots : « corrige et il faudra demander à l'utilisateur, comme dans la modale, de choisir la bonne parcelle ou le bon
DPE — cela existe déjà, audite ».

**Audit (code lu) :**
- **La parcelle** : le choix EXISTE (`CadastreParcellePicker`, App.tsx ~11045) à deux endroits : l'éditeur de l'avis
  (onglet Marché, quand le point tombe hors parcelle) et le module cadastre de la fiche (`CadastreCommercialSection`,
  ~11112, avec « changer » et la présélection). Le choix est mémorisé (`sources.cadastre`, la parcelle « retenue »).
  L'éditeur la PRÉCHARGE (« pour qu'elle PERDURE dans l'avis de valeur », commentaire d'origine) — mais « Tout générer »
  relançait le cadastre au point et REMPLAÇAIT la parcelle retenue par le résultat, même raté : c'est le trouvé du §73.
  Le PDF, lui, n'était pas faux : le worker reprend la parcelle mémorisée quand la charge n'en porte pas
  (console_job_worker.js 9147). Et le sélecteur ne s'affichait QUE dans l'onglet Marché : ouvert par l'assistant (onglet
  « Bien & valeur »), la personne ne le voyait pas.
- **Le DPE** : ⚠ AUCUN CHOIX N'EXISTE à l'écran. Le serveur (`/geo/dpe`, routers/geo.py ~378) cherche les DPE ADEME à
  l'adresse exacte (id BAN du bâtiment RNB, jusqu'à 30), sinon dans un rayon de 90 m (5), et en RETIENT UN SEUL : la surface
  la plus proche de celle du bien, sinon le plus récent ; il ne renvoie pas les autres. La fiche l'affiche (« N DPE à cette
  adresse — retenu : surface la plus proche » / « DPE le plus proche — à vérifier »). Aucune note ne parle d'un choix de DPE.
  ➡ Le construire = la route renvoie les candidats (étiquette, surface, date, adresse) + une fenêtre de choix sur le patron
  du sélecteur de parcelle + la mémorisation du choix (`sources.dpe`, déjà en place). À décider par lui.

**Codé (App.tsx, rien d'autre) :**
1. `prechargement` (la promesse du préchargement) et `parcelleRetenue` : `loadCadastreElements` attend le préchargement
   et, s'il y a une parcelle retenue, NE relance PAS le cadastre au point (le bouton comme l'automatique).
   `onEstimCadastrePick` la marque retenue.
2. Le sélecteur de parcelle est sorti de l'onglet Marché : il s'ouvre par-dessus l'éditeur quel que soit l'onglet.
3. Bandeau : « cadastre (parcelle retenue) » dans « Calculé » ; « choisis la bonne parcelle dans la fenêtre ouverte »
   quand le point tombe hors parcelle (plus « Manque : cadastre »).
**Ce que ça pourrait casser** : une parcelle retenue FAUSSE ne se corrige plus par « Tout régénérer » dans l'éditeur — elle se
change dans la fiche (module cadastre, bouton changer, qui existe). Rien ne change dans le worker, le PDF ni la base.
**Contrôle** : build vert. Pas vu à l'écran (pas poussé).

## 75. AUDIT EN PROFONDEUR de l'outil d'estimation : où il y a un DOUTE, qui choisit ? (18/11) — rien codé

Ses mots : « audite de nouveau l'outil éditeur d'estimation, il y a plusieurs endroits comme pour le cadastre où il faut
faire un choix en cas de doute, et je suis presque sûr que les DPE ont un truc aussi ; audite en profondeur ».
Lu : l'éditeur et l'onglet Estimation de la fiche (App.tsx), lib/api.ts, routers/geo.py, le worker du PDF
(console_job_worker.js ~8500-9310), la GED, supabase/, l'historique git (toutes branches, stashes), les notes. Mesuré en base.

**Le choix du DPE N'EXISTE PAS, et n'a jamais existé** (aucune branche, aucun commit, aucune table). Ce qui existe :
⭐ SA règle, écrite le 09/11 (notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §28.15, l. 3711-3721) : « Si doute (ex. DPE
ou autre), montrer les choix possibles » ; la recommandation qui suivait : « les DOUTES en cartes à choisir, la plus
probable mise en avant (DPE E · 21/05/2026 · 85,5 m² — le plus proche de vos 85 m² / D · 27/08/2024 · 100,6 m² / Aucun) ;
même forme pour une copropriété voisine ou un syndic » ; et « le DPE théorique de la BDNB n'est jamais proposé comme DPE ».
Puis MIS DE CÔTÉ par lui le 09/11 (« on oublie l'idée ») — jamais codé. Ailleurs : la GED « Ce que dit le DPE » corrige les
cases de la FICHE depuis un DPE déposé (pas le DPE de l'estimation ; elle prend le plus récent sans le dire ; le numéro ADEME
lu, `numero_ademe`, n'est utilisé nulle part).

**Source par source (qui tranche quand il y a doute) :**
- DPE ADEME (`/geo/dpe`, geo.py 376-436) : le SERVEUR, seul. Jusqu'à 30 DPE à l'adresse exacte (id BAN du bâtiment RNB),
  sinon 5 à 90 m ; garde UN seul (surface la plus proche, sinon le plus récent — et si aucun n'a de surface, le plus récent
  sans le dire) ; les autres sont perdus (seul leur nombre remonte). Écran : une phrase « N DPE à cette adresse — retenu :
  surface la plus proche » / « DPE le plus proche — à vérifier », AUCUN bouton. **Mesuré : 17 biens ont un DPE mémorisé ;
  3 avec plusieurs DPE à l'adresse (jusqu'à 10), 3 trouvés seulement « à proximité » (ex. 24935 : DPE de 107 m² pour un bien
  de 120 m², sans doute un voisin), 6 sans DPE.**
- Bâtiment RNB / BDNB (geo.py 251-358) : le serveur, le bâtiment le plus proche à 40 m, première adresse, `limit 1` ;
  distance ni renvoyée ni montrée.
- Copropriété RNIC (geo.py 587-675) : le serveur ; parcelles retenues -> parcelle sous le point -> rue à 80 m / 200 m ; à
  chaque étape `rows[0]` s'il y en a plusieurs ; `match` et `distance_m` renvoyés mais ni déclarés (type CoproRnieData) ni
  montrés. Mesuré : 12 recherches, 3 trouvées (par la parcelle), 9 non trouvées. Le SYNDIC, lui, est choisi par l'humain
  (SyndicDuBien.tsx 141-157).
- Cadastre : le SEUL choix humain (CadastreParcellePicker) — mais seulement quand le point tombe hors parcelle ; sur une
  parcelle (même la mauvaise), elle est prise sans doute affiché ; « Ajuster la parcelle » et le clic sur la carte existent.
- DVF (`app_dvf_comparables` v4) : la base élargit rayon / durée / terrain jusqu'à 10 ventes, écrête p05-p95 ; aucun
  comparable ne s'exclut à la main ; « peu fiable » affiché dans l'éditeur, PAS dans l'onglet de la fiche.
- Cadre de vie, INSEE, loyers : la commune = le premier résultat du géocodage inverse ; aucun doute affiché.
- Patrimoine / ABF : toute la liste, pas de doute ; « GPU incomplet — à confirmer » affiché.
- Géocodage d'adresse : un seul candidat, accepté dès 0,35 ; le score et l'adresse trouvée jamais montrés (mesuré le 09/11 :
  « 12 rue larionov 42000 » -> « 12 Rue de Laharpe », 0,48 : un mauvais point possible).

**Défauts trouvés (vérifiés dans le code, pas à l'exécution) :**
1. Fiche, module cadastre (App.tsx ~11196-11201) : « Générer / Actualiser » réenregistre la parcelle du POINT dans
   `sources.cadastre` par-dessus la parcelle RETENUE (choisie à la main). (L'éditeur est protégé depuis §74, pas poussé.)
2. Worker (9178 + 9285) : en dernier recours il prend la parcelle au point et la MÉMORISE comme retenue, sans geste humain.
3. Onglet de la fiche (11577 / 11618) : la case « DPE réel · ADEME » se replie sur le DPE THÉORIQUE de la BDNB — contraire à
   sa règle du 09/11.
4. PDF (worker 8531-8539, 8693-8696) : si une lettre DPE est saisie dans l'éditeur, la vignette l'affiche avec la conso et
   les émissions du DPE ADEME retenu (peut-être un autre logement) ; la mention ne dit jamais « à proximité / à vérifier ».
5. Fiche (11713-11722) : « Reporter dans la fiche » (conso + GES ADEME -> Hektor) est proposé même pour un DPE « à
   proximité ».
6. Éditeur (6686) : la copropriété part avec `cadastre?.parcelles` lu AU CLIC alors que le cadastre se charge en parallèle.
7. Loyers (11526) : bascule maison <-> appartement sans le dire (le texte dit « pour une maison »).
8. DVF : « peu fiable » absent de l'onglet de la fiche.
**Contre-vérification (18/11, il insiste : « plusieurs DPE à la même adresse, normalement l'app gère et donne le choix »)** :
le code SERVI EN LIGNE par Vercel (index-*.js) ne contient que la phrase « N DPE à cette adresse — retenu : surface la plus
proche » ; un seul appel à la base ADEME dans tout le dépôt (geo.py) ; aucune liste de DPE à l'écran. L'app GÈRE plusieurs DPE
(elle les trouve et en retient un, par la surface) mais NE DONNE PAS le choix. Cas réels : 62774 (10 DPE à l'adresse),
24113 et 1670846 (6 chacun).

## 76. Sa décision sur l'audit du §75, et la marche suivante PROPOSÉE (18/11) — rien codé

Ses mots : « Non, ne touche à rien. Il faut donc juste prévoir la possibilité à l'utilisateur de choisir la parcelle et la
copropriété si nécessaire à partir du bloc assistant, puisque cela est aussi indispensable pour générer un rapport
d'estimation. Également si un utilisateur donne des informations supplémentaires, autres que les quelques exigées, il faut
que l'assistant les intègre aussi, donc tous les champs possibles. »
➡ NON retenus (ne pas relancer de soi-même) : le choix du DPE ; les 8 défauts du §75.

**Mesuré pour « tous les champs possibles » :**
- Carte « créer » : elle prend les 132 cases du scan + la composition. La fenêtre de création a **171 cases** (groupes
  `draftAnnonceWizardGroups`) : **114 se remplissent** par ces clés, **57 non**. Parmi les 57 : les 8 diagnostics avec date et
  commentaire (24 cases), les honoraires acquéreur / vendeur (8), la location (dépôt de garantie, loyer, charge, rendement,
  occupation : 5), les cases DPE « non concerné / vierge / altitude / année de référence » (4), diagnostiqueur, syndic,
  indication d'étage, spécification de la climatisation, moyens de visite, masquer le prix, clearing ; et des cases qui ne se
  dictent pas (n° de dossier, date de création, latitude / longitude, ville et CP publics / privés, diffusable).
- Carte « avis de valeur » : elle prend toutes les cases VISIBLES de l'éditeur, sauf « Contexte de l'e-mail »
  (vente / succession). (dpe, ges, chauffage, exposition existent dans le brouillon de l'éditeur mais n'y ont pas de case.)
  Les caractéristiques du bien ne se changent pas dans l'éditeur : dictées avec l'avis, elles vont à la carte « modifier le
  bien » (existe, liste fermée).

**Proposé :**
1. Carte « créer » : une liste de cases de la FENÊTRE en plus de celles du scan (les 57 moins celles qui ne se dictent pas),
   vérifiées au serveur selon leur forme (nombre, oui / non, liste de choix de la fenêtre, date, texte), posées par
   `updateDraftAnnonceWizardField` après le passage du scan, et marquées comme les autres.
2. Carte « avis de valeur » : + « Contexte » (vente / succession) ; et si la personne dicte des caractéristiques du bien,
   l'assistant propose AUSSI la carte « modifier le bien » (consigne).
3. Parcelle et copropriété depuis le flux de l'assistant, « si nécessaire » :
   - parcelle : le sélecteur existe ; ouvert par l'assistant, l'éditeur le montre par-dessus (fait au §74, pas poussé), et le
     bandeau gagne « Choisir / changer la parcelle » (le même sélecteur, avec les parcelles voisines) ;
   - copropriété : AUCUN choix n'existe aujourd'hui (le serveur prend la première). À construire : la route renvoie les
     candidates quand il y a doute (plusieurs, ou trouvée par la rue / la proximité), un sélecteur sur le patron de celui de
     la parcelle (nom, immatriculation, lots, distance, « Aucune »), le choix mémorisé (`sources.copro`) et repris par le
     PDF ; la recherche attend la parcelle retenue.
   - « Si nécessaire » = seulement en cas de doute ; sinon rien n'est demandé.
**Ce que ça pourrait casser** : (1) la fenêtre de création (partagée avec la saisie à la main) — mêmes fonctions qu'à la
main, rien de neuf côté Hektor ; (3) la route copropriété est aussi appelée par la fiche (onglet Estimation) : il faut que sa
réponse reste lisible par l'ancien écran.

## 77. Maquettes VALIDÉES (« OUI ») ; sa demande suivante : l'éditeur de l'avis ÉCLATÉ EN QUESTIONS, chaque réponse GARDÉE — PROPOSÉ (18/11), rien codé

Toile https://claude.ai/artifact/5S2owJCDo2HWTBBefakeGo : planches 4 à 9 (le bilan de l'IA, la parcelle avec les vraies
voisines IGN de 24935, la copropriété, la dictée rangée, l'éditeur prêt, le téléphone) — validées par « OUI ».
Ses mots ensuite : « il faudrait éclater la modale éditeur du rapport en plusieurs questions afin de le remplir entièrement ;
chaque question répondue est mémorisée dans la modale même si on ferme, et si on passe par l'éditeur on retrouve ces réponses ».

**Mesuré** : sur les 37 avis générés (`generate_estimation_pdf` done), 10 ont un barème d'état, 10 un avis du conseiller,
8 des points forts, 7 un argumentaire, 5 une taxe foncière : le PDF part le plus souvent avec des « à compléter ».
La table `app_dossier_estimation` est lisible par TOUT compte connecté (règle `app_dossier_estimation_read`, `true`).

**Proposé (planches 10-11)** :
1. Le parcours en 10 questions, dans l'ordre du métier : pour quoi faire (vente / succession) · le bien est-il juste (ce que
   dit la fiche ; une correction part par « Modifier le bien ») · la parcelle (et la copropriété si besoin) · l'état général
   (étoiles + libellé + appréciation) · l'état poste par poste (8 postes, 4 boutons, une précision) · points forts et de
   vigilance · les charges de l'année · la valeur (le marché DVF montré, la fourchette, l'argumentaire) · ton avis de
   conseiller · l'envoi (PDF seul, ou au propriétaire). À gauche la liste avec l'état de chaque question (répondue, dictée par
   l'assistant, en cours, à faire) ; « Je ne sais pas » partout ; « Voir tout l'avis » = les 6 onglets d'aujourd'hui sur les
   MÊMES réponses.
2. Chaque réponse ENREGISTRÉE dès le clic, pour le bien ; à la réouverture (fiche, écran Estimations ou assistant) : « Tu en
   étais à la question 6 sur 10 », la liste des réponses (modifiables), et ce que le PDF montrera (pages complètes, en partie,
   à compléter).
3. À l'ouverture : la saisie en cours, sinon le dernier avis, sinon la fiche scannée, sinon le prix ± 5 % ; la dictée de
   l'assistant y répond (marquée « dicté »).
4. Stockage : une TABLE À PART (pas `app_dossier_estimation`), lisible et modifiable seulement par ceux qui ont le droit de
   travailler sur le bien ; une ligne par bien ; qui a répondu et quand. ⚠ Patch en base = son accord.
5. Deux personnes sur le même avis : la dernière réponse gagne ; l'éditeur dit qui et quand.
**Ce que ça pourrait casser** : l'éditeur est partagé (fiche + écran Estimations) — tout le monde aura le parcours ;
l'enregistrement au clic est une ÉCRITURE en base nouvelle (aujourd'hui l'éditeur n'écrit que les sources et le PDF) ; le
PDF et le travail du worker ne changent pas (la charge reste celle de « Générer »).

## 78. Planches 10-11 ÉCARTÉES ; LE PRINCIPE DU CHAPITRE 6 DÉCIDÉ : le parcours GUIDÉ dans la conversation (18/11) — rien codé

**Ses mots** : « Non je veux pas des modal encore différente même plus jolie que celle actuelle, je veux savoir si comme
dans chat gpt des questions réponse orienté » ; puis « si on a demandé crée une estimation puis fais avis de valeur … on
pourrait reprendre en cours ? » ; puis « Oui ce principe avec des boutons de choix etc et peux tu faire de même avec la
création d'une annonce car il faudrait garder ce principe pour les cartes de ce chapitre ».
⛔ **Les planches 10 et 11 (questionnaire dans une fenêtre neuve) sont ÉCARTÉES** — pas de nouvelle fenêtre.

**LE PRINCIPE (décidé, pour TOUTES les cartes du chapitre 6)** :
1. Les questions se posent DANS LA CONVERSATION, une à la fois, avec des BOUTONS DE CHOIX sous la question ; on peut
   aussi répondre en tapant ou en dictant. « Je ne sais pas » est accepté. Ce qui est déjà connu n'est pas redemandé.
2. ⭐ **UN CLIC NE COÛTE AUCUN APPEL AU MODÈLE** : la liste des questions est connue d'avance, c'est le SERVEUR qui pose
   la suivante et enregistre la réponse. Le modèle n'est appelé que pour le bilan de départ, une réponse en phrase
   libre (la comprendre, la ranger), et une proposition de texte (argumentaire, points forts, texte d'annonce).
3. À la fin, la carte récapitulative ; la fenêtre ou l'éditeur D'AUJOURD'HUI s'ouvre rempli ; seul SON clic fait le
   geste (rien ne change à cette règle).
4. **Enchaînement** : création d'une estimation → « On prépare l'avis de valeur ? » → les questions de l'avis.
5. **Reprise en cours** : les réponses sont GARDÉES à chaque réponse (rattachées à la conversation avant la création, au
   bien après) ; le serveur les redonne au modèle à chaque tour. On reprend en rouvrant la conversation, en écrivant « on
   reprend l'avis de 24935 », ou par l'éditeur ouvert depuis la fiche.

**Mesures qui fondent le principe (18/11)** :
- un tour de l'assistant coûte en moyenne 0,0152 $ (médiane 0,0156, max 0,0498) — 177 tours depuis le 12/11, 2,69 $ ;
- plafonds en place : 3 $/jour pour l'agence (`PLAFOND_JOUR_USD`), 100 questions/jour/personne, 8 étapes par tour ;
- tout par le modèle = ~20 tours par parcours création + avis ≈ 0,30 $ ; avec le principe ≈ 3 à 6 appels ≈ 0,05-0,10 $ ;
- le modèle ne relit que les **20 derniers messages** (`MAX_HISTORIQUE_MESSAGES`) → un parcours long l'oublierait :
  d'où la mémoire des réponses, redonnée par le serveur ;
- une carte expire au bout de **30 minutes** et n'est lisible que par celui qui l'a demandée (+ admin)
  (`patch_assistant_ia_etape3_cartes_2026-11-13.sql`, l. 61 et 79-80) → elle ne peut pas servir de mémoire.
- cadastre, DVF, DPE, copropriété : services publics gratuits, appelés UNE fois au bilan ; Hektor n'est pas appelé
  pendant les questions (seulement au clic « Créer » et à « Générer », comme aujourd'hui).

**Les pièces à faire** (rien codé ; chaque pièce = audit fin → « vas-y » → code → preuve) :
- P1 le moteur de questions côté serveur (listes ordonnées, enregistrement, question suivante, sans modèle) ;
- P2 les boutons de choix sous une question dans l'écran de l'assistant (⚠ écran partagé par tous les gestes : les
  autres cartes doivent rester inchangées) ;
- P3 la mémoire des réponses : une petite table nouvelle → **patch en base = son accord**, et **qui la lit** (lui seul /
  ceux qui travaillent sur le bien) **à lui demander avant d'écrire le patch** ;
- P4 la consigne : quand appeler le modèle, l'enchaînement, la reprise ;
- P5 les listes de questions, carte par carte : **estimation (la première)**, avis de valeur, **annonce** (les questions
  de l'estimation + celles propres à l'annonce — prix, mandat, honoraires, texte ; liste exacte à tirer de l'audit des
  7 étapes de la fenêtre), puis offre/compromis/vente, mandat et signature, bon de visite.

**Ce que ça pourrait casser** : l'écran de l'assistant (partagé) ; une écriture en base nouvelle à chaque réponse ;
rien côté coût (les deux plafonds restent).

## 79. AUDIT : les questions MÉTIER du parcours guidé, pour pré-remplir ENTIÈREMENT la fenêtre de création (18/11) — rien codé

**Sa précision** : « l'ergonomie dans le chat devrait être similaire dans créer une annonce estimation ou actif que l'idée
pour éditer le rapport d'estimation, à savoir créer des principes de questions métiers pertinentes pour collecter auprès
de l'utilisateur les éléments nécessaires à pré-remplir entièrement la modal ». Audit limité à la CRÉATION (annonce
estimation / actif) et à l'AVIS ; les autres cartes du chapitre 6 ne sont pas mesurées ici.

**Ce que la fenêtre attend (lu dans App.tsx)** :
- 7 étapes (`draftAnnonceStepOrder`, l. 2613) : 1 Offre (compte, type, prix, titre, surfaces, pièces, options) · 2 Photos ·
  3 Secteur (adresse, transports, environnement) · 4 Composition (pièce par pièce) · 5 Détails (intérieur, extérieur,
  équipements, diagnostics, copropriété, visites) · 6 Mandat / Prix (net vendeur, honoraires, estimation, charges,
  mandant initial, note) · 7 Diffusion (titre, texte, rappel, création du brouillon NON diffusé).
- Ce qui BLOQUE la création (`handleCreateDraftAnnonce`, l. 18804) : l'agence, le négociateur, et un mandant complet si
  « existant » ou « nouveau » (nom + e-mail). Tout le reste est facultatif.
- La fenêtre montre/cache les cases SELON LE TYPE DE BIEN (`DraftAnnonceTypeProfile`, l. 1055 : surfaceMode habitable /
  terrain / garage, showRooms, showBedrooms, showLevels, showGarageCount, showGardenPool, showExposure, showView,
  showInteriorDetails, showOutdoorDetails, showCoproDetails). ⭐ Le parcours doit suivre LES MÊMES RÈGLES : ne jamais
  demander une case que la fenêtre cacherait.
- La carte sait déjà porter 132 cases (format du scan, `FIELD_KEYS`) + la composition ; l'avis 16 cases + 8 postes.

**⭐ LE QUESTIONNAIRE MÉTIER EXISTE DÉJÀ : c'est la FICHE DE VISITE de l'agence** (`public/patron-fiche-saisie.html`),
celle que le scan lit. 10 rubriques, dans l'ordre d'une visite : 1 le vendeur (contexte vente/succession, motivation,
délai) · 2 le bien (type, adresse, construction récente) · 3 extérieur & annexes · 4 intérieur · 5 composition · 6
technique (année, DPE, copropriété, disponibilité) · 7 équipements & confort · 8 état détaillé (intérieur, extérieur, note,
8 postes) · 9 valeur & charges · 10 points & commentaires (forts, vigilance, travaux, argumentaire, avis, note, descriptif).
Proposition : le parcours du chat SUIT CETTE FICHE — le négociateur retrouve l'ordre qu'il connaît, et la dictée, le scan
et le chat remplissent les MÊMES cases.

**Ce qui est réellement rempli sur les 572 biens « Actif » vivants** (mesure du 18/11, lecture seule, groupes intérieur /
extérieur du détail Hektor ; « non » et 0 comptés vides) : surface habitable 75 % · pièces 73 % · chambres 68 % · WC 58 % ·
niveaux 52 % · salles d'eau 40 % · jardin 36 % · exposition 36 % · cuisine 33 % · cave 32 % · salles de bains 31 % ·
terrasse 30 % · séjour 30 % · garages 27 % · piscine 24 % · parkings 16-20 % · balcon 16 % · vue 16 % · Carrez 14 % · …
détails de piscine ~1 %. Texte d'annonce 73 %, titre 72 %. ⚠ NON MESURÉ ici : chauffage, DPE, copropriété (autres blocs du
détail). ⚠ Les terrains et garages sont dans les 572 : les taux « logement » sont un peu plus hauts que ces chiffres.

**LES PRINCIPES DES QUESTIONS (proposés)** :
1. Ne jamais demander ce qu'on sait déjà : la fiche, le dernier avis, le contact, et ce que les services publics donnent
   (cadastre, DVF, DPE ADEME, copropriété) — ceux-là se PROPOSENT (« le DPE trouvé dit D, c'est bien lui ? »).
2. Le type de bien commande la suite (les règles de la fenêtre) : appartement → étage, ascenseur, copropriété ; maison →
   terrain, assainissement, niveaux ; terrain → constructible, viabilisé, raccordements.
3. Regrouper : une liste de oui/non devient UNE question à cases à cocher (« Qu'y a-t-il dehors ? Jardin · Piscine ·
   Terrasse · Cave · Balcon · Garage · Parking ») ; seules les cases cochées amènent leur question de surface.
4. L'essentiel d'abord (ce qui se remplit vraiment, mesuré ci-dessus), le facultatif ensuite, avec « Je complète plus
   tard » : on peut ouvrir la fenêtre à tout moment.
5. Toujours « Je ne sais pas », toujours la réponse libre (tapée ou dictée ; le modèle la range).
6. Les coordonnées d'un NOUVEAU mandant ne passent jamais par le chat (tapées dans la fenêtre).
7. Un repère « question 4 sur ~12 » et « Modifier » sur chaque réponse donnée.
8. La MÊME ergonomie pour la création (estimation ou actif) et pour l'avis de valeur.

**Le parcours proposé (création ; ~10 questions essentielles, ~18 avec le facultatif)** :
1. Estimation ou mise en vente ? · type de bien (boutons). 2. Le vendeur : un contact existant (boutons des contacts
trouvés) ou un nouveau (« à saisir dans la fenêtre ») ; contexte (Vente · Succession · Séparation · Autre) ; délai. 3.
L'adresse (texte ; les communes du code postal en boutons). 4. Intérieur : surface, pièces, chambres (boutons 1 à 6+),
niveaux, salles de bains / d'eau, WC ; étage et ascenseur si appartement ; exposition (8 boutons) ; cuisine. 5. Dehors :
cases à cocher, puis les surfaces des cases cochées (piscine : chauffée, couverte, pool house ; terrain : constructible,
viabilisé…). 6. Technique : année (ou une période : avant 1948 · 1948-1974 · 1975-2000 · après 2000), DPE proposé,
copropriété (lots, charges, statut du syndic), libre ou occupé. 7. Équipements : chauffage (individuel / collectif ;
énergie), assainissement, eau, puis cases à cocher (double vitrage, fibre, volets électriques…). 8. État intérieur et
extérieur (5 boutons chacun). 9. Le prix : pour une ESTIMATION le prix souhaité par le vendeur ; pour un ACTIF le prix,
les honoraires et QUI les paie, taxe foncière, charges. 10. Pour un ACTIF : titre et texte PROPOSÉS par l'assistant
(appel au modèle), boutons Garder · Raccourcir · Réécrire. Fin : la carte récapitulative → la fenêtre s'ouvre remplie →
SON clic « Créer ». Pour une ESTIMATION créée : « On prépare l'avis de valeur ? » → le parcours de l'avis (état poste
par poste, points forts et de vigilance, charges, valeur avec le marché montré, argumentaire, avis du conseiller).
Photos : restent dans la fenêtre (étape 2) ; la composition pièce par pièce se DICTE (« séjour 30 m² au rez-de-chaussée,
cuisine 12 m²… »), le modèle la range.

**Ce que ça pourrait casser** : rien de la fenêtre (elle reçoit les mêmes cases qu'aujourd'hui par la carte) ; les règles
par type sont LUES, pas recopiées (sinon deux listes divergeraient) — à vérifier à l'audit fin du moteur ; l'écran de
l'assistant (partagé) pour les boutons.

## 80. AUDIT MESURÉ et MÉTHODE proposée du parcours guidé, comparée à l'existant ; MAQUETTE planches 12 à 19 (18/11) — rien codé

**Sa demande** : « Fais une maquette d'abord » ; « il faut juste ne pas passer par l'IA pour remplir ces champs » (les
coordonnées du nouveau vendeur) ; « un audit métier et de l'app pour créer des questions intelligentes et une bonne
ergonomie pour les réponses ; réunir les réponses pour limiter les demandes à l'API ; audit, mesure et analyse avant, pour
proposer la meilleure méthode, en comparaison avec l'existant : l'assistant et l'estimation ».

**Périmètre** : objet annonce (créer une estimation ou un actif) et l'avis de valeur. Les autres objets du tableau de la
méthode (contact, recherche, relation, transaction, mandat, document, RDV) ne sont PAS mesurés ici, sauf le contact
mandant créé dans la fenêtre.

### 80.1 Les mesures (lecture seule, 18/11)

L'ASSISTANT (`app_agent_run`, agent `assistant`, 180 tours depuis le 12/11) :
- 0,0152 $ en moyenne par tour, 2,69 $ en tout ; ~28 500 jetons lus par tour.
- ⭐ UN SEUL appel au modèle lit déjà ~11 600 jetons (tours à 1 étape : 11 591 en moyenne, 0,0118 $) : ce sont les
  consignes et les ~40 outils. Un tour fait 3 étapes le plus souvent (77 tours sur 180) : 0,017 $.
- Les petits agents spécialisés coûtent 20 à 30 fois moins : `ged_lecture` 0,0005 $ (3 551 jetons), `redacteur` 0,0007 $,
  `ged_classement` 0,0003 $.
- Question médiane 53 caractères, réponse médiane 226.
- Cartes : 1 carte `ouvrir_avis_de_valeur` exécutée ; 0 carte `ouvrir_creation_annonce` à ce jour (le geste est tout
  récent ; les autres gestes sont bien dans la table, donc la lecture marche).
- La consigne d'aujourd'hui (assistant_service.py, « SANS fiche papier… ») fait poser au modèle « 3 ou 4 questions
  regroupées en une seule fois », au clavier, sur les ~10 essentiels seulement.

LES CRÉATIONS PAR LA FENÊTRE (`app_console_job` `create_hektor_draft_annonce`) : 94 depuis le 15/05 (12 en novembre),
92 réussies ; médiane 37 cases pleines. Au-dessus de 60 % : type, titre, ville, surface, prix, pièces, chambres. Vers
45 % : salles de bains, WC, année, niveaux, DPE, garage, état extérieur. Vers 30 % : terrasse, parkings, cave, cuisine,
état intérieur. La création rapide « Par photo, avec l'IA » (App.tsx, `createFlow`) existe : scan de la fiche, puis
« Créer l'estimation » ou « Détailler dans l'assistant » (⚠ ce bouton ouvre la FENÊTRE, pas l'assistant).

LES 12 849 ESTIMATIONS VIVANTES (détail Hektor) : surface 77 %, pièces 53 %, chambres 50 %, WC 40 %, niveaux 36 %, puis
tout s'effondre (salles d'eau 26 %, cave 24 %, cuisine 18 %, jardin 7 %, piscine 6 %, exposition 5 %, vue 1 %). Une
estimation est aujourd'hui une fiche LÉGÈRE ; elle ne se remplit qu'en devenant un actif (572 actifs : jardin 36 %).

L'AVIS DE VALEUR (`generate_estimation_pdf`, dernier avis par bien) : 37 générés, sur 13 biens seulement, par 2 personnes,
le dernier le 05/10. Sur ces 13 : fourchette 10, note d'état 6, barème par poste 5, avis du conseiller 4, argumentaire 3,
points forts 3, vigilance 3, taxe foncière 2, DPE 0. ⭐ L'outil est peu utilisé, et le PDF sort surtout avec des vides.

### 80.2 Les trois façons, chiffrées

- A. Le modèle pose chaque question (le « ChatGPT » pur) : ~18 questions × 0,015 $ ≈ 0,27 $ par création. ⛔ Et au-delà
  de 20 messages (`MAX_HISTORIQUE_MESSAGES`), le modèle a oublié le début : 18 questions = 36 messages. La reprise est
  impossible.
- B. L'existant : le modèle regroupe 3 ou 4 questions, 2 à 3 tours ≈ 0,04 $, tout au clavier, ~10 cases.
- C. PROPOSÉ : l'app pose les questions (liste connue), un clic n'appelle pas le modèle ; 1 tour pour comprendre la
  demande (0,015 $) ; les phrases libres GARDÉES et lues ENSEMBLE par un petit lecteur dédié (~0,0005 $, comme
  `ged_lecture`, pas le grand assistant) ; le titre et le texte d'un actif par le rédacteur (0,0007 $). ≈ 0,02 $ par
  création, ~34 cases au lieu de ~10. Plafond agence de 3 $/jour : 11 créations par A, 150 par C.

⭐ Recommandation : C. Elle coûte moins que l'existant ET remplit trois fois plus.

### 80.3 Réunir les réponses (sa demande) — trois niveaux

1. UNE QUESTION PORTE PLUSIEURS CASES : l'intérieur = surface proposée + 6 compteurs + la cuisine, une seule validation ;
   le dehors = cases à cocher, puis seulement les surfaces des cochées ; l'état de l'avis = une grille 8 postes × 4 niveaux.
   ~10 écrans pour ~40 cases.
2. LE SERVEUR COMPREND SANS IA tout ce qui est simple : un nombre (« 118 »), oui/non, « je ne sais pas », un bouton.
3. LES PHRASES LIBRES SONT GARDÉES et lues en UNE FOIS à la fin d'une rubrique (ou du parcours), par le petit lecteur,
   avec le format du scan (`FIELD_KEYS`). Une dictée du début (« raconte le bien d'un coup ») est lue tout de suite, une
   fois, et le serveur saute les questions déjà répondues.

### 80.4 Les questions intelligentes (métier, sans IA)

- Ne jamais redemander : l'agenda (adresse, contact), le contact (vendeur), l'ADEME (DPE, surface, année, chauffage), le
  cadastre (parcelle, terrain), la copropriété (registre), les communes du code postal. PROPOSÉ à confirmer, en un clic.
- Le type de bien commande la suite, avec les règles de la fenêtre (`DraftAnnonceTypeProfile`, App.tsx:1055) LUES : pour
  une maison, ni étage ni ascenseur ; pour un appartement, étage, ascenseur, copropriété.
- Le genre commande la suite : estimation = contexte, délai, prix souhaité par le vendeur ; actif = prix, honoraires et
  qui les paie, titre et texte.
- L'ordre suit la fiche de visite de l'agence (§79) et ce qui est vraiment rempli (80.1) : ce que tout le monde sait d'abord.
- Les points forts et de vigilance de l'avis sont PROPOSÉS par des règles écrites, à cocher : jardin, garage, toiture
  refaite, commerces proches (cadre de vie) ; façade ou électricité « à prévoir », DPE F ou G, avant 1997 = amiante,
  avant 1949 = plomb, fosse septique = contrôle de l'assainissement. Jamais inventés par le modèle.

### 80.5 Les formes de réponse (ergonomie)

Boutons à choix unique · puces à cocher + « Valider » · compteurs − / + · nombre avec unité et valeur proposée · grille ·
« proposé, c'est bien ça ? » · phrase libre ou dictée (toujours possible) · cases protégées (nouveau vendeur). Sur
chaque question : « Je ne sais pas », « Je complète plus tard », le repère « question 4 sur ~10 » ; sur chaque réponse
donnée : « Modifier ». Au téléphone : touches de 44 px au moins, le bouton « Valider » en bas, sous le pouce.

### 80.6 Le nouveau vendeur : CORRECTION de la règle (sa phrase du 18/11)

La règle n'est plus « les coordonnées ne passent jamais par la conversation », mais : **elles ne passent jamais par
l'IA**. Elles se saisissent DANS la conversation, dans des cases protégées qui vont droit à la mémoire du parcours puis à
la fenêtre ; le modèle ne voit que « Mme Lefèvre, nouveau vendeur · coordonnées saisies ». ⚠ Ce que ça demande au code :
ces réponses ne doivent PAS entrer dans `app_assistant_message` (que le modèle relit) ni dans le résumé d'une carte ; la
recherche de doublon (même e-mail ou téléphone, `findContactDuplicateCandidates`) et les communes du code postal se
font comme dans la fenêtre.

### 80.7 La maquette — toile https://claude.ai/artifact/5S2owJCDo2HWTBBefakeGo, version 17

12 le départ (ce qu'on sait n'est pas redemandé) · 13 six cases en une question · 14 cocher puis seulement les cochées,
une phrase libre gardée · 15 le nouveau vendeur sans IA · 16 l'avis : la grille des 8 postes et les points proposés ·
17 la fin, la fenêtre remplie, l'enchaînement vers l'avis · 18 au téléphone · 19 les trois façons chiffrées. Planches 10
et 11 marquées ÉCARTÉES. Les noms et l'adresse de la création sont inventés ; Firminy = bien d'essai 24935.

### 80.8 Ce que ça pourrait casser ailleurs

- Rien de la fenêtre ni de l'éditeur : ils reçoivent les mêmes cases qu'aujourd'hui.
- L'écran de l'assistant est partagé par tous les gestes : les nouvelles formes de réponse s'ajoutent sans toucher aux
  cartes existantes.
- La mémoire du parcours = une table neuve, donc un patch en base (son accord). Elle portera des coordonnées de
  particuliers : à DÉCIDER par lui : qui la lit (la personne et l'admin, comme les cartes ?), et quand on l'efface
  (proposé : les coordonnées dès que la fenêtre les a reçues, le reste 30 jours après).
- Le petit lecteur est un agent neuf : il passe par le même compteur de coût (`app_agent_run`) et le même plafond.

**À trancher par lui** : la méthode C ; la grille et les points proposés de l'avis ; la règle 80.6 ; qui lit la mémoire
et quand on l'efface. Ensuite, sur son « vas-y » : l'audit fin du moteur (P1 à P5 du §78), dans l'ordre estimation,
avis, annonce.

## 81. CORRECTION : deux parcours séparés — CRÉER LA FICHE n'est pas ÉDITER LE RAPPORT (18/11) — rien codé

**Sa remarque** : « tu t'embrouilles entre l'ajout d'une annonce type estimation et éditer le rapport ». C'est juste. Au §79
et dans la toile v17, j'avais mis dans la création des questions du RAPPORT (le contexte vente/succession, le délai, le
prix souhaité) et numéroté la planche de l'état poste par poste DANS la suite de la création. Ce sont deux écrans, deux
listes de cases, deux parcours.

### 81.1 A — CRÉER LA FICHE : la fenêtre « Nouvelle annonce » (lu dans le code : `DRAFT_ANNONCE_WIZARD_GROUPS`, App.tsx ~1440-1770)

1. Offre : type, prix public, net vendeur, surfaces (habitable, terrain, garage), pièces, chambres, niveaux, jardin,
   piscine, garages, exposition, vue.
2. Photos.
3. Secteur : adresse privée, code postal, commune, transport, proximité, environnement.
4. Composition (pièce par pièce).
5. Détails : intérieur (salles de bains, WC, Carrez, séjour, cuisine) ; extérieur (étage, cave, balcon, terrasse,
   parkings, mitoyenneté) ; piscine (si piscine) ; terrain ; construction récente ; équipements (chauffage, eau,
   assainissement, sécurité…) ; diagnostics et énergie (année, ÉTAT EXTÉRIEUR et INTÉRIEUR en mots Hektor, DPE, GES,
   diagnostics) ; copropriété ; disponibilité et visite.
6. Mandat / Prix : honoraires et qui les paie, montant et date d'estimation, taxe foncière, charges ; le MANDANT.
7. Diffusion : titre et texte.
⛔ Aucune case du rapport ici. Estimation : pas de question de prix ni de texte. Mise en vente : en plus, le prix, les
honoraires et qui les paie, le titre et le texte (proposés par le rédacteur). Le contexte (succession) et le délai de la
fiche de visite n'ont PAS de case dans la fenêtre : ils ne se demandent pas ici (au plus, la note interne).

### 81.2 B — LE RAPPORT : l'éditeur « Avis de valeur » d'un bien qui EXISTE (`EstimationDocumentEditor`, App.tsx ~6420-7110)

Six onglets. « Le bien » est en LECTURE SEULE (0 case modifiable ; l'écran dit « Pour les corriger, modifiez la fiche du
bien ») : le parcours ne redemande JAMAIS le bien ; une incohérence se signale avec la carte « Modifier le bien ».
Les cases propres au rapport : contexte de l'e-mail (Vente suite à visite / Succession, valeur pour le notaire) ;
fourchette basse, valeur estimée, fourchette haute ; argumentaire de prix ; avis du conseiller ; état en étoiles, libellé,
toiture, menuiseries, appréciation ; état par poste (8 postes × 4 niveaux) ; points forts ; points de vigilance ; taxe
foncière, énergie, eau, assurance par an ; « Marché » = un clic qui calcule tout (DVF, cadre de vie, cadastre, bâti,
ADEME…), aucune question.
Le parcours B en ~6 questions : pour quoi faire · ta valeur · l'état (étoiles + grille) · points forts et de vigilance
(proposés par des règles) · les charges (taxe foncière reprise de la fiche, énergie d'après le DPE) · l'argumentaire et
ton avis (proposés par le rédacteur : Garder, Raccourcir, Réécrire). Puis l'éditeur s'ouvre rempli ; seul « Générer »
fait le PDF.

### 81.3 Le seul pont entre les deux

Après la création d'une ESTIMATION : « on prépare son rapport ? ». C'est un autre écran ; la fiche créée y est reprise
(lecture seule), rien n'est redemandé. Les seules cases communes : la taxe foncière (fiche, étape 6) et le DPE (lu par
l'onglet « Le bien »).

### 81.4 La toile, version 18

Série A, créer la fiche : A1 le départ · A2 l'intérieur en une question · A3 le dehors coché · A4 le nouveau mandant sans
IA · A5 mise en vente seulement : prix, honoraires, texte · A6 la fin, la fenêtre remplie, et la proposition du rapport.
Série B, le rapport : B1 le bien lu sur la fiche, pour quoi faire, la valeur · B2 l'état en étoiles et la grille · B3 les
points, les charges, puis les textes · le téléphone · les coûts (fiche ≈ 0,02 $, rapport ≈ 0,016 $).
Les §79-80 restent valables pour la méthode (clic sans IA, phrases lues ensemble, coûts, nouveau vendeur), mais leurs
listes de questions sont REMPLACÉES par 81.1 et 81.2.

## 82. La toile refaite (version 20) : design rehaussé, et LE SCAN D'ABORD (19/11) — rien codé

**Sa demande** : « remets à jour le fichier maquette et profite pour rehausser le design ; ajoute que l'agent peut
conseiller à l'utilisateur de scanner ses photos du patron, pour le scan IA, pour éviter les questions ».

### 82.1 Le scan d'abord — ce qui existe déjà (lu dans le code)

- La fiche de visite de l'agence (`apps/hektor-v1/public/patron-fiche-saisie.html`) s'imprime depuis la création
  rapide (« Télécharger le patron vierge », App.tsx, `createFlow`) ; sa photo est lue par le scan de la fenêtre
  (`openai_listing_sheet_service.py`), qui rend les cases ET une liste « À vérifier » (`draftAnnonceScanReview`).
- La consigne de l'assistant sait déjà passer les photos de la fiche jointes dans la carte (« fichiers ») ; et
  l'éditeur du rapport reprend déjà le brouillon du scan (`loadEstimationScanDraft`, couche « fiche scannée » sous le
  dernier avis et la dictée).
- ⚠ NON MESURÉ : le coût d'un scan et le nombre de scans faits — le scan n'écrit pas dans `app_agent_run`. Le « 31 cases
  lues » des planches est un EXEMPLE.

### 82.2 Ce que la toile propose

- A1 : quand la demande de création arrive sans fiche jointe, l'assistant CONSEILLE d'abord de photographier la fiche
  (« je la lis d'un coup et je ne te pose que ce qu'elle ne dit pas »), avec « Photographier la fiche », « Joindre des
  photos », « Imprimer le patron vierge », ou « Pas de fiche : les questions ».
- A2 : la fiche lue ; les écritures douteuses (la liste « À vérifier » du scan) deviennent des choix en un clic ; il ne
  reste que les questions que la fiche ne couvre pas.
- B1 : pour le rapport, le même conseil vise les pages 8 à 10 de la fiche (état poste par poste, points, appréciation,
  avis) ; si la fiche a été scannée à la création, l'éditeur la reprend déjà et rien n'est redemandé.
- Un bouton « Scanner la fiche » permanent dans la barre de saisie, et sur le téléphone.
- Les coûts : « C + la fiche scannée » = ~3 questions au lieu de 10 ; le coût du scan est écrit « non mesuré ».

### 82.3 Le design, selon la charte DÉJÀ VALIDÉE de l'assistant (notice/ETAPE4_MAQUETTE_ACCUEIL_DESIGN_2026-11-17.md §3)

Fenêtre 1 280 × 665 (la sienne) ; rail d'aujourd'hui replié (voile magenta, trait magenta, avatar) ; Inter pour
l'interface, Plus Jakarta Sans pour les titres de question et les chiffres ; une couleur, un rôle : magenta = agir (le
bouton qui valide, la réponse choisie), rose doux = ce qui attend ton geste (l'en-tête d'une question), bleu canard =
ouvrir une fiche (Modifier, Ouvrir le contact, le patron), vert = fait (les réponses données) ; arrondis 8, 10, 14, 22.
Nouveau dans la conversation : le fil des rubriques dans l'en-tête de chaque question (« ✓ Le bien · ✓ Intérieur ·
Dehors · Détails · Mandant ») à la place de « question 4 sur ~10 » ; les réponses données en pastilles vertes
« Modifier » ; les propositions par règles en pointillé, les réponses choisies en magenta.

### 82.4 Les planches

Série A, créer la fiche : A1 le conseil du scan · A2 la fiche lue · A3 sans fiche, l'intérieur en une question ·
A4 le dehors coché · A5 le nouveau mandant sans IA · A6 mise en vente seulement : prix, honoraires, texte · A7 la fin et
la proposition du rapport. Série B, le rapport : B1 le bien lu et le conseil du scan des pages 8 à 10 · B2 pour quoi
faire et ta valeur · B3 sans fiche, l'état en étoiles et la grille · B4 les points proposés et les charges. Plus le
téléphone et les coûts. Les planches « Parcours » de la v18 sont retirées de la toile.

**Ce que ça pourrait casser** : rien, c'est une maquette. Pour le code, le conseil du scan touche la consigne de
l'assistant (partagée par tous les gestes) : une phrase de plus, à n'appliquer qu'aux demandes de création et de rapport.

## 83. CORRECTION du §82 : le scan est la 2e FAÇON DE CRÉER une annonce, PAS une étape du rapport (19/11) — rien codé

**Sa remarque** : « tu te trompes ; je disais que l'assistant propose la deuxième façon d'ajouter une annonce, par le
système où l'utilisateur ajoute des scans au lieu de remplir l'annonce à la main ; et ce n'est pas dans le rapport
d'estimation ».

Ce qui est REMPLACÉ dans le §82 :
- Le scan n'a RIEN à faire dans le rapport : la planche B1 ne propose plus de photographier les pages 8 à 10 ; la
  série B garde ses ~6 questions (pour quoi, valeur, état, points, charges, textes), le bien venant de sa fiche.
- Le scan est la 2e des DEUX FAÇONS DE CRÉER que l'écran propose déjà (App.tsx, `createFlow` : « Comment veux-tu la
  créer ? » → « Manuellement » ou « Par photo, avec l'IA : un agent lit ma fiche et pré-remplit »). L'assistant propose
  ces deux mêmes façons dans la conversation, la façon par photo en premier (A1) : « Photographier la fiche »,
  « Joindre », le patron vierge à imprimer ; ou « À la main, par mes réponses » (les questions A3 à A6). A2 reste : la
  fiche lue, les écritures douteuses en un clic, puis seulement ce qu'elle ne dit pas.
- Le bouton permanent « Scanner la fiche » de la barre de saisie est RETIRÉ (fonction ajoutée sans demande) ; la barre
  garde « Joindre », la dictée et l'envoi. Au téléphone : « Je ne sais pas » et « Dicter ».

Toile : version 24 (fusionnée sur ta version enregistrée depuis la page, tailles de planches gardées), mêmes planches A1-A7, B1-B4 (B1 = le bien lu et « pour quoi faire », B2 = ta valeur).

## 84. AUDIT DE COUVERTURE avant le plan de développement : chaque case des deux écrans, la conservation, les photos et les documents ; la toile REFAITE (19/11) — rien codé

**Sa demande** : « il faut être sûr que toutes les questions permettent de remplir entièrement chaque fenêtre ; vérifier
avant les essais ; refaire entièrement les maquettes et nettoyer les obsolètes ; l'exemple : une demande de création
d'estimation, puis le rapport, puis l'envoi au propriétaire ; confirmer que chaque réponse est mémorisée, remplie dans
la fenêtre réelle et conservée comme aujourd'hui ; prévoir l'ajout de documents et de photos (gestes que l'assistant
maîtrise), auditer les workers ; l'ajout de document dans la fenêtre de création n'existe peut-être pas ».

Méthode : trois audits en LECTURE SEULE du code (rien écrit, rien lancé, aucune base lue), puis la couverture.
Périmètre : objet annonce (créer), avis de valeur (créer, envoyer), photo et document (créer, lire, modifier). Les
autres objets ne sont pas mesurés.

### 84.1 La fenêtre « Nouvelle annonce » (App.tsx ; numéros du 19/11)

- 7 étapes (App.tsx:2614). 14 groupes `draftAnnonceWizardGroups` (App.tsx:1482-1765) : 194 apparitions, **172 noms
  techniques** (75 listes, 33 textes courts, 14 longs, 31 décimaux, 19 entiers), + **22 cases hors groupes** (agence,
  négociateur, famille et sous-type, adresse / CP / ville, choix du mandant, 8 cases du nouveau mandant, note…) = **194
  cases fixes**, plus 20 photos au plus et 7 cases par pièce de la composition.
- Par type (DraftAnnonceTypeProfile App.tsx:1056, filtre App.tsx:2384 et 15718, LE MÊME À L'ENVOI App.tsx:2393) :
  maison 136 montrées, appartement 132, terrain 45, garage 43, immeuble 35, autre 51. 8 ne sont JAMAIS montrées (taxe
  d'habitation, 4 de location, fibre, gardien, clearing).
- Exigé pour créer (App.tsx:18882-18914) : agence, négociateur de la liste de l'agence, et un mandant complet s'il y en
  a un (nom + e-mail pour un nouveau). Rien d'autre.
- AUJOURD'HUI la carte (`CASES_CREATION` = 132 clés du scan) et le scan atteignent **114 des 172 noms**. **58 n'ont
  aucune voie** : 8 honoraires, 31 diagnostics et drapeaux du DPE, 7 adresses privée/publique et coordonnées, masquer le
  prix, dépôt de garantie, n° de dossier, date, 4 de location, diagnostiqueur, syndic, étage (floorState), moyens de
  visite, climatisation (détail), clearing, diffusable. Hors groupes : la carte ne porte pas l'agence, ne transmet pas
  « nouveau mandant », ni photos, ni partenaires, ni l'immobilier professionnel, ni les notes privée / inter-agence des
  pièces.
- **La couverture proposée** (planche E17) : honoraires → question « Prix » (mise en vente) ; diagnostics → question
  « Énergie et diagnostics » (E05), l'ADEME propose ; adresses → la question adresse (la publique = la privée par
  défaut), coordonnées calculées ; visite, clés, étage, climatisation → leurs questions ; diagnostiqueur, syndic →
  « Intervenants » ; n° de dossier, date, non diffusée → posés seuls comme aujourd'hui ; nouveau mandant → cases
  protégées (sans IA) ; photos → question « Photos » (E07) vers l'étape 2 ; documents → après la création (84.4) ; les 8
  jamais montrées : sans objet ; laissé à la main : le dépôt de garantie (location). ⇒ **pour une maison, chacune des
  136 cases montrées a une question, une source ou une valeur posée**.
- ⚠ Ce que ça demande au code : la mémoire du parcours doit parler la langue de la FENÊTRE (ses 172 noms + les hors
  groupes), pas seulement les 132 clés du scan.

### 84.2 L'éditeur « Avis de valeur » (EstimationDocumentEditor, App.tsx ~6420-7300)

- 24 cases au brouillon (App.tsx:6440-6455), dont la grille des 8 postes. La carte en remplit 17 (`CHAMPS_AVIS` 16 +
  `POSTES_AVIS`). Il en manque 7 : propriétaire (aucun champ à l'écran), destinataire, vente/succession, DPE, GES,
  chauffage, exposition (ces 4 n'ont AUCUN champ à l'écran : un DPE mal lu ne se corrige pas et revient à chaque avis).
  Hors brouillon : la parcelle (choix humain), « Appliquer à la valeur » (DVF), méthode / validité / nom / visibilité
  (jamais envoyés, valeurs par défaut).
- Couverture proposée : « pour quoi faire », « à qui l'envoyer » (pris sur la fiche par l'app, jamais vu par l'IA),
  DPE/GES/chauffage/exposition confirmés en E10, la parcelle en E10, « prendre la valeur du marché » en E11, un bouton
  « effacer » sur une réponse. ⇒ **24 sur 24**.

### 84.3 La conservation — CE QUI EST VRAI AUJOURD'HUI (sa question « confirme que chaque réponse est mémorisée… »)

- Fenêtre : AUCUN brouillon avant « Créer ». Fermer ne demande confirmation que s'il y a des photos ; toute réouverture
  remet tout à zéro (`openDraftAnnonceModal`, App.tsx:18251). Seule survit la dictée de la carte (« Rouvrir la
  création »). APRÈS « Créer » : la saisie part dans la charge du travail, la fiche naît chez nous et la saisie est
  gardée (`annonce_nait_complete`, `annonce_saisie_gardee` → `app_annonce_saisie_naissance`, 21 champs « console
  seule » reposés). Interrupteurs allumés selon CLAUDE.md, non relus en base.
- Éditeur : AUCUN brouillon ; fermer (un clic à côté, sans confirmation) perd tout. Survivent : les sources calculées,
  la parcelle choisie. APRÈS « Générer » : la charge du PDF devient le « dernier avis », repris à l'ouverture suivante
  (sans destinataire, variante, propriétaire). Le brouillon du SCAN vit dans `app_dossier_estimation.scan_draft`.
- ⇒ Donc aujourd'hui une réponse n'est PAS mémorisée tant qu'on n'a pas cliqué. Le parcours apporte la mémoire qui
  manque : chaque réponse enregistrée au clic (table neuve), la fenêtre et l'éditeur la reçoivent comme une saisie, et à
  « Créer » / « Générer » tout est gardé EXACTEMENT comme aujourd'hui.

### 84.4 Photos et documents (les workers)

- Photos à la création : étape 2, JPEG/PNG/WebP, 20 au plus, visible ou masquée (App.tsx:18443-18475). Elles ne sont
  PAS dans la charge de création : après « Créer », une file en mémoire attend le travail `done`, le numéro Hektor et la
  relecture, puis pose un `upload_hektor_photo` par photo (App.tsx:16531-16611, api.ts:9260-9330), chemin « chez nous
  d'abord » (`completerEnvoiPhotoDifferee`, worker:10323) ; échec Hektor = reprise à 12:30. Perdues si l'onglet se
  recharge avant le retour de Hektor.
- L'assistant ne peut PAS aujourd'hui mettre des photos du bien dans la fenêtre : le paramètre `fichiers` de la carte
  ne sert qu'aux pages de la fiche papier (scan), et l'ouverture vide les photos (App.tsx:18251). À faire : un second
  paramètre « photos du bien », versées dans l'étape 2 APRÈS l'ouverture.
- Après création : `ajouter_photo` (20 par carte, JPEG/PNG — refuse le WebP que la fenêtre accepte —, toujours visible,
  copie serveur du trombone), `couverture_photo`, `deplacer_photo`, `visibilite_photo` : tous exigent le numéro Hektor.
- Documents : `deposer_documents` ne dépose rien lui-même : il ouvre la fenêtre de dépôt GED avec les fichiers (types
  `app_ged_type`, proposition par le nom puis l'IA) ; c'est la personne qui clique « Envoyer ». Interrupteur
  `ged_depot_multiple` (admin le 17/11, non relu) : pour un négociateur, la carte est refusée. Le travail
  `upload_document_to_hektor` (chemin différé + anti-doublon, en production depuis le 19/10).
- ✅ **Sa remarque est juste : la fenêtre de création n'a AUCUN moyen de joindre un document.** Obstacle : le dépôt
  exige le numéro Hektor de l'annonce (`app_console_creer_document_optimistic`), rendu seulement au travail `done`
  (11 créations sur 79 au-delà d'une minute). Deux voies, à trancher par lui : **A** (proposée sur la toile, E09) les
  documents joints dans la conversation sont proposés juste après la création par la carte d'aujourd'hui — toute la GED
  gardée, les fichiers survivent 2 jours au coffre ; il faut ouvrir `ged_depot_multiple` aux négociateurs. **B** une
  étape « Documents » dans la fenêtre, sur le modèle de la file des photos (mêmes fragilités).
- Le modèle ne voit jamais le contenu d'un fichier : garanti par `decrire_pour_le_modele` (assistant_fichiers.py:182)
  et la route (routers/assistant.py:80-102) ; les liens signés vont à l'écran, pas dans l'historique.

### 84.5 L'envoi au propriétaire (estimation_sender.py, estimation_email.py)

- « Générer + envoyer » crée le travail du PDF PUIS envoie aussitôt l'e-mail : ⚠ **l'e-mail part avant que le PDF
  existe**, et le lien `/r/download` sert « le plus récent avis » au moment du clic → « pas encore disponible », ou
  l'ANCIEN avis. Pas de pièce jointe : un lien suivi 60 jours ; trace `app_email_envoi` (⚠ marquée « envoyé » avant
  l'appel Gmail), ouverture et téléchargement notifiés. Envoi réel selon `EMAIL_REAL_SEND_ENABLED` (non lu).
- Aucun geste de l'assistant n'appelle cet envoi ; `email_client` pourrait joindre le PDF, mais sans lien suivi ni trace
  d'estimation. Proposé (E15) : « Envoyer à Mme Durand » ne s'allume qu'une fois CE PDF prêt, le lien vise ce PDF.

### 84.6 Défauts trouvés, à corriger AVANT les essais (lus dans le code, non essayés — planche E19)

Fenêtre : le mandant pré-rempli saute s'il n'est pas dans les 12 contacts trouvés (puis « Créer » refusé) ; le
négociateur saute s'il n'est pas dans la liste de l'agence ; « statut du syndic » dicté en texte dans une liste à codes ;
une pièce inconnue devient « Chambre » ; la date d'estimation posée au jour même pour une mise en vente ; la marque
« pré-rempli » sur la case vide « Adresse privée (rue) », le bandeau compte des cases cachées ; « nouveau mandant » non
transmis. Éditeur et envoi : pas de brouillon ; 4 cases sans champ ; l'e-mail avant le PDF ; la trace « envoyé » avant
Gmail. Photos et documents : WebP refusé par la carte ; tout attend le numéro Hektor ; GED réservée à l'admin ; pas
d'anti-doublon pour une photo reprise (non mesuré).

### 84.7 La toile REFAITE — https://claude.ai/artifact/5S2owJCDo2HWTBBefakeGo, version 25

Les 24 anciennes planches sont RETIRÉES (1-11, A1-A7, B1-B4, Tel, Coûts). Une seule histoire, Mme Durand à Firminy :
1. Créer l'estimation : E01 la demande et les deux façons (par photo conseillée) · E02 la fiche lue, 3 doutes · E03
   l'intérieur · E04 le dehors · E05 l'énergie et les diagnostics · E06 le mandant et la visite · E07 les photos et les
   documents · E08 la fenêtre remplie étape par étape · E09 créée : photos en route, documents et rapport proposés.
2. Le rapport et l'envoi : E10 le bien lu, ce que l'éditeur ne laisse pas saisir, la parcelle, pour quoi faire · E11 la
   valeur face au marché · E12 l'état · E13 points et charges · E14 les textes et à qui l'envoyer · E15 l'éditeur
   rempli, le PDF, l'envoi, le téléchargement · E16 le téléphone.
3. L'audit : E17 la couverture · E18 ce qui est gardé · E19 à corriger avant les essais · E20 le coût (≈ 0,035 $ la
   chaîne complète par le parcours, ≈ 0,40 $ si l'IA posait tout ; 85 contre 7 par jour sous le plafond de 3 $).

**À trancher par lui avant le plan de développement** : (1) la mémoire du parcours — qui la lit, quand on efface les
coordonnées d'un nouveau mandant ; (2) documents à la création, voie A ou B ; (3) ouvrir le dépôt de documents aux
négociateurs ; (4) l'envoi seulement quand CE PDF est prêt ; (5) quels défauts de 84.6 corriger avant les essais.

**Ce que ça pourrait casser** : rien encore (maquette et audit). Pour le code : la fenêtre et l'éditeur sont partagés
par la saisie à la main, le scan et l'assistant — toute nouvelle voie d'entrée doit passer par les mêmes fonctions
(`applyDraftAnnonceScan`, les couches de l'éditeur) pour ne pas créer une deuxième logique.

## 85. SES DÉCISIONS sur le §84 (18/11 au soir) ; le dépôt de documents OUVERT aux négociateurs

**Ses mots** : « La mémoire accessible par le négociateur de l'annonce ou admin. Ouvre le dépôt au négo. »

1. **La mémoire du parcours** (table neuve, patch à écrire) : lisible par le NÉGOCIATEUR DE L'ANNONCE et par l'ADMIN.
   ⚠ À traduire au patch : avant la création, l'annonce n'existe pas encore → la mémoire appartient à la personne qui a
   lancé le parcours (son auteur) ; dès que l'annonce existe, au négociateur de l'annonce, et toujours à l'admin.
   Restent à trancher : quand on efface les coordonnées d'un nouveau mandant (proposé : dès que la fenêtre les a reçues).
2. **Le dépôt de documents ouvert aux négociateurs** : FAIT le 18/11 à 21:26:46 (UTC) —
   `update app_setting set value = 'on' where key = 'ged_depot_multiple' and value = 'admin'` (1 ligne), relu par une
   seconde voie : `on`.
   - Ce que ça change : pour tout compte actif (admin, manager, commercial), l'onglet Documents d'une fiche montre la
     FENÊTRE DE DÉPÔT GED (plusieurs fichiers, pages assemblées en PDF, type proposé d'après le NOM du fichier, doublon
     reconnu, pièces des personnes en privé) à la place du formulaire d'un seul fichier, gardé en secours
     (App.tsx:12740-12753). La carte « Déposer des documents » de l'assistant n'est plus refusée aux négociateurs
     (`_fenetre_ged_ouverte`, assistant_gestes.py:2096).
   - Ce que ça N'OUVRE PAS : AUCUN appel à l'IA. Le classement et la lecture par IA restent derrière `ged_lecture_ia`
     (« admin »), revérifié par le serveur à chaque appel (backend/app/routers/ged.py:54-60, 81-82, 133). Les conditions
     du cran « on » de la GED (DPA, analyse d'impact, registre, clause au mandat — note GED §0 et §12.37) concernent la
     lecture par IA : elles restent dues avant d'ouvrir `ged_lecture_ia`. L'assistant lui-même reste « admin »
     (`assistant_ia`).
   - L'envoi ne change pas : chaque fichier part par `createUploadDocumentToHektorJob` (chemin d'aujourd'hui), puis
     `app_ged_classer` (« on ne classe que ses propres dépôts ») ; les négociateurs peuvent lire l'interrupteur
     (règle `app_setting_select_active_user`).
   - Comptes actifs au 18/11 : 4 admins, 2 commerciaux.
   - ⚠ Pas vu à l'écran par un compte de négociateur (je n'ai pas leur session) : la preuve viendra de leur premier dépôt
     (un travail `upload_document_to_hektor` suivi d'une ligne `app_ged_classement` à leur nom).
   - Revenir en arrière : `update public.app_setting set value = 'admin', updated_at = now() where key = 'ged_depot_multiple';`

Toujours à trancher (§84.7) : les documents à la création, voie A ou B ; l'envoi au propriétaire seulement quand CE PDF
est prêt ; quels défauts du §84.6 corriger avant les essais ; l'effacement des coordonnées d'un nouveau mandant.

## 86. SA DÉCISION : documents à la création = VOIE A (18/11)

**Ses mots** : « Voie A ». Les documents joints dans la conversation pendant le parcours de création sont gardés au
coffre (2 jours, ils survivent à un rechargement) ; quand le travail de création est `done` et que l'annonce a son
numéro Hektor, l'assistant propose la carte « Déposer des documents » d'aujourd'hui sur ce bien (planche E09) ; c'est
la personne qui clique « Envoyer » dans la fenêtre de dépôt GED. Aucune étape « Documents » n'est ajoutée à la fenêtre
de création. Rendu possible pour les négociateurs par l'ouverture du §85.
À prévoir au plan : attendre le numéro (11 créations sur 79 au-delà d'une minute) ; le relais `poserDepotAssistant` ne
tient qu'UN dépôt en attente à la fois et disparaît au rechargement (lib/depotAssistant.ts) — la carte, elle, se rejoue.
Restent à trancher : l'envoi au propriétaire seulement quand CE PDF est prêt ; les défauts du §84.6 ; l'effacement des
coordonnées d'un nouveau mandant.

## 87. SA DÉCISION : l'envoi au propriétaire ATTEND que CE PDF soit prêt (18/11)

**Ses mots** : « Oui, attendre ». Aujourd'hui « Générer + envoyer au propriétaire » (App.tsx:6894-6921) crée le travail
`generate_estimation_pdf` puis appelle AUSSITÔT `sendEstimationEmail` ; le lien `/r/download` (backend/app/routers/
emails.py:144-171) sert « le plus récent avis » au moment du clic → « pas encore disponible » ou l'ANCIEN avis.
Décidé : l'envoi ne part qu'une fois le PDF de CE travail rangé (travail `done` ET son `upload_document_to_hektor`
`done`, fiche `app_console_document` présente au coffre), et le lien vise CE document-là. Vaut pour l'éditeur ET pour
le parcours de l'assistant (planche E15 : « Envoyer à Mme Durand » ne s'allume qu'au PDF prêt).
À prévoir au plan (non tranché, à expliquer avant de coder) : où attendre (l'écran qui relit le travail, ou le worker
qui envoie lui-même à la fin) ; que faire si le dépôt chez Hektor échoue (aujourd'hui pas de fiche ni de copie) ; la
trace d'envoi marquée « envoyé » AVANT Gmail (email_tracking.py:114-121), à corriger dans le même mouvement.
Restent à trancher : les défauts du §84.6 ; l'effacement des coordonnées d'un nouveau mandant.

## 88. RE-VÉRIFICATION case par case (sa demande : « revérifie que tes questions n'oublient pas des champs ») — le §84 était FAUX ; corrigé, toile v27 (19/11) — rien codé

**Ce qui était faux** : le §84 affirmait « chaque case a un chemin » en raisonnant par groupes. Le croisement
mécanique le dément.

**La méthode** (programme en lecture seule, `scratchpad/verif_couverture.py`, sortie `verif_couverture.txt`) : il lit
les cases que la fenêtre MONTRE pour chaque type de bien (extraites d'App.tsx : `draftAnnonceWizardGroups`, le profil
par type, le retrait des cases du haut et de PRIXNETVENDEUR à l'étape 7) et les croise avec la liste exacte des cases
que chaque question remplit. Une question ne compte que pour les types où elle est posée (la copropriété : appartement ;
le terrain à bâtir : terrain ; l'étage : appartement et immeuble).

**La toile v25 oubliait** : maison 86 cases sur 136, appartement 86 sur 132, terrain 41 sur 45, garage 33 sur 43,
immeuble 31 sur 35, autre 35 sur 51 — notamment tout le secteur (transports, proximité, environnement, adresses
publiques), l'exposition, la vue, la surface Carrez, l'équipement de la cuisine, le terrain, la piscine, l'eau et l'eau
chaude, les 13 cases du confort, la construction récente, les intervenants, l'étage et la copropriété, les dates de
libération, la taxe foncière, les charges, les travaux, le prix et les 8 honoraires, le titre et le texte. Hors des
groupes : 18 sur 29 (le nouveau mandant, les 7 cases de la composition, les intervenants, le sous-type professionnel).
Dans le rapport : 2 sur 24 (menuiseries, appréciation de l'état). Et des CHOIX FAUX : la cuisine (la fenêtre propose
Américaine, Kitchenette, Séparée, Sans ; et à part Équipée, Semi équipée), « véranda » et « dépendance » (pas des cases
de la fenêtre), « disponible » (c'est un oui / non, pas libre / occupé / loué).

**Le parcours corrigé : 0 oubli** — maison 136/136, appartement 132/132, terrain 45/45, garage 43/43, immeuble 35/35,
autre 51/51 ; hors des groupes 29/29 ; le rapport 24/24. Ses 19 questions (planche « La vérification ») : le bien ; le
quartier ; l'appartement (étage, résidence) ; la copropriété ; l'intérieur (14 cases) ; la composition (7 par pièce) ;
le dehors (20) ; la piscine (8, si cochée) ; le terrain à bâtir (7, terrain) ; l'énergie (20) ; les diagnostics (24) ; le
confort (13) ; la construction récente (4, moins de 10 ans) ; les intervenants (2) ; la visite (5) ; le mandant (10) ;
l'argent (17) ; les photos ; le titre et le texte. Sans objet : les 8 cases jamais montrées. Laissés à la main,
DÉCLARÉS : le dépôt de garantie (location) et « clearing » (sens inconnu — à éclaircir).

⚠ Ce que la vérification NE prouve PAS : elle prouve que chaque case est NOMMÉE par une question, pas que la question
la remplit bien. Le contrôle de vérité viendra au code : une épreuve qui remplit la fenêtre par le parcours et relit
chaque case (à écrire dans le plan, avec ce même programme versé au dépôt).

**La toile v27** (https://claude.ai/artifact/5S2owJCDo2HWTBBefakeGo) : 26 planches. Série 1, 15 planches : la demande, la
fiche lue, le bien et son quartier, pour un appartement, l'intérieur (corrigé), la composition, le dehors (corrigé),
l'énergie et les diagnostics (corrigé), le confort et les intervenants, la visite et le mandant (corrigé), un nouveau
mandant, l'argent, les photos et documents, la fenêtre remplie, la création. Série 2, 7 planches : le rapport (l'état
porte maintenant les menuiseries et l'appréciation), l'envoi, le téléphone. Série 3, 4 planches : la vérification, ce
qui est gardé, à corriger, le coût. Exemples inventés (Mme Durand, Mme Lefèvre, Diag Expert Loire, Foncia, les adresses).

## 89. SA DÉCISION « Tous » : les 10 défauts corrigés avant les essais ; chaque défaut REVÉRIFIÉ dans le code ; LE PLAN DE DÉVELOPPEMENT (19/11) — rien codé

**Ses mots** : « Tous » (à la question « quels défauts du §84.6 corriger avant les essais ? »). Les 10 défauts ont été
relus dans le code le 19/11 (lecture seule) : **les 10 sont réels**. Trois précisions nouvelles (D2, D6, D10).
Méthode du projet : corriger du code existant = **attendre son « vas-y »** ; la table de mémoire = **patch, son accord** ;
push = **son accord**. Une seule pièce en code à la fois.

### 89.1 Les 10 défauts, revérifiés — la cause, la correction, ce que ça pourrait casser, la preuve

**D1 — le mandant pré-rempli saute.** Cause : App.tsx:16034-16044. La recherche des mandants ne part qu'à l'étape 6, ne
cherche QUE dans les contacts du négociateur choisi, 12 au plus ; si le contact posé par l'assistant (18341-18345)
n'est pas dans ces 12, son numéro est EFFACÉ sans un mot, puis « Créer » refuse (18900). Correction : retenir le
mandant venu de l'assistant (numéro + nom) ; s'il manque dans la liste, l'y AJOUTER en tête au lieu de l'effacer ;
taper dans la recherche l'efface comme aujourd'hui (23736). Si le contact appartient au portefeuille d'un AUTRE
négociateur : le dire dans le bandeau, ne rien effacer. Casse ailleurs : rien à la main (la mémoire est vide quand
la fenêtre est ouverte au bouton). ⚠ À vérifier avant de coder : la recherche de la carte côté serveur est-elle bornée
au même négociateur ? Preuve : ouverture par une carte avec un mandant hors des 12 → « Créer » accepte.

**D2 — le négociateur pré-rempli saute.** Cause : App.tsx:16014-16016 efface tout négociateur absent de la liste de
l'agence (15647-15656) ; la carte ne pose l'agence que si elle la connaît (18348). ⭐ Précision : si la carte ne porte
pas l'agence, ou un nom d'agence écrit autrement, la liste filtrée ne le contient pas → effacé. Correction : prendre
l'agence dans la liste des négociateurs (`hektorNegotiators`, par `idUser`) quand la carte ne la porte pas ; s'il reste
absent, un message visible « X n'est pas dans l'agence Y : choisis-le » au lieu d'un effacement muet. Inchangé : un
commercial est toujours forcé sur lui-même (16009-16012, voulu). Casse ailleurs : rien à la main. Preuve : carte sans
agence → négociateur et agence posés.

**D3 — « statut du syndicat » en texte dans une liste à codes.** Cause : App.tsx:1941, `kind: 'text'` alors que la case
a des options (`wizardProcedureOptions`, 1698). Correction : `kind: 'enum'` avec ces options (le résolveur 1948 rend
vide ce qu'il ne reconnaît pas). Casse ailleurs : touche AUSSI le scan (même table) — dans le bon sens : une valeur
inconnue laisse la case vide au lieu d'y écrire un texte que Hektor ne connaît pas. Preuve : « procédure en cours » →
le code de l'option ; « blabla » → case vide.

**D4 — une pièce inconnue devient « Chambre ».** Cause : App.tsx:18549 (`idTypePiece || '1'`) et 4440 à l'envoi. La
liste des 32 types n'a pas « Autre ». Correction (création seulement) : une pièce dont le type n'est pas reconnu arrive
SANS type, son nom dit gardé ; l'étape Composition la marque « type à choisir » et le bandeau la cite ; à « Créer », si
une pièce n'a toujours pas de type, la fenêtre va à l'étape Composition avec un message (nouveau refus, MAIS seulement
pour une pièce sans type, ce qui n'arrive que par le scan ou l'assistant). Le défaut `'1'` de 4440 reste pour la fiche
existante. Casse ailleurs : le scan change de la même façon (une pièce mal lue demande au lieu de devenir chambre).
Dans le parcours, les pièces se choisissent dans les 32 vrais types : le cas ne vient que d'une phrase libre.

**D5 — date d'estimation posée au jour même pour une mise en vente.** Cause : App.tsx:18576-18580, dans le remplisseur
du scan (le scan est toujours une estimation). Correction : une option du remplisseur « date du jour par défaut », vraie
pour le scan et pour une estimation, fausse pour une mise en vente. Casse ailleurs : rien (le scan garde son défaut).

**D6 — la marque « pré-rempli » ment, le bandeau compte faux.** ⭐ Précision : DEUX cases portent le nom `adresse` —
l'adresse du haut de l'étape 3 (`draftAnnonceAddress`, envoyée en `address`, 18963) et la case Hektor « Adresse privée
(rue) » (1511, dans le groupe Secteur). L'assistant et le scan ne remplissent que la première ; `marqueAssistant('adresse')`
marque les deux. Et le compte (15751-15766, 23343) compte les clés DEMANDÉES, pas les cases réellement remplies ni
montrées pour ce type de bien. Correction : la marque et le compte se calculent sur ce que la fenêtre CONTIENT et
MONTRE (valeur non vide + case visible pour le profil) ; l'adresse du haut prend sa propre clé. Casse ailleurs : rien
(affichage seul). ⚠ À vérifier avant P5 : que fait le worker quand les deux adresses diffèrent (laquelle gagne) — le
parcours remplira les deux de la même rue.

**D7 — « nouveau mandant » non transmis.** Cause : `OuvertureCreation` (lib/assistant.ts:53-62) ne porte qu'un mandant
EXISTANT. Correction : un champ `nouveau_mandant` (civilité, nom, prénom, e-mail, téléphone, adresse, CP, ville) que
l'écran lit DANS LA MÉMOIRE DU PARCOURS (P3) et verse dans les cases de la fenêtre, puis choix « nouveau ». ⛔ Il ne
passe JAMAIS par le modèle ni par `app_assistant_message` ni par le résumé de la carte (règle du 18/11). Dépend de P3.

**D8 — l'éditeur du rapport n'a pas de brouillon.** Cause : fermer l'éditeur (un clic à côté, sans confirmation) perd
tout ; seule la charge du dernier PDF est reprise. Correction en deux temps : (a) fermer demande confirmation s'il y a
une saisie non générée (local, sans base) ; (b) le brouillon de l'éditeur est gardé dans la MÊME table que la mémoire
du parcours (P3), par bien, relu à l'ouverture, soldé à « Générer ». Casse ailleurs : (a) rien ; (b) une écriture en base
à chaque pause de saisie — même règle de lecture que P3 (négociateur du bien + admin).

**D9 — DPE, GES, chauffage, exposition : aucune case dans l'éditeur.** Cause : l'onglet État (App.tsx:7061-7069) n'a que
toiture et menuiseries ; ces 4 valeurs viennent du bien (6396-6400) et partent déjà dans le PDF (6879-6885) sans pouvoir
être corrigées. Correction : 4 cases dans l'onglet État, sur le modèle de « Toiture » (DPE et GES en liste A à G).
Casse ailleurs : rien (les clés existent déjà dans le brouillon et la charge).

**D10 — la carte « Ajouter des photos » refuse le WebP.** Cause : assistant_gestes.py:2013, VOLONTAIRE (« le WebP n'a
jamais été envoyé à Hektor »). ⭐ Mesuré le 19/11 : 62 travaux `upload_hektor_photo`, 0 en WebP — la fenêtre l'accepte
(18446) mais aucun n'est jamais parti : l'acceptation de Hektor n'est PAS prouvée. Correction proposée (sans parier sur
Hektor) : une photo WebP est CONVERTIE en JPEG dans le navigateur au moment où elle entre (trombone de l'assistant ET
étape 2 de la fenêtre) ; la carte reste JPEG/PNG. Casse ailleurs : le fichier gardé est un JPEG (le scan le lit
pareil ; un WebP joint comme DOCUMENT devient JPEG, que la GED accepte). Preuve : un WebP joint → une photo JPEG
déposée, travail `done`.

### 89.2 LE PLAN DE DÉVELOPPEMENT, dans l'ordre (chaque pièce : explication → « vas-y » → code → preuve → note)

- **Lot 0 — les défauts sans base** : D3, D5, D6, D9, puis D1, D2, D4, D10, D8 (a). Front seul (et D10 côté
  navigateur). Validation `npm run build`. Un commit par défaut.
- **P3 — la mémoire** (avant P1, tout en dépend) : une table neuve `app_assistant_parcours` (parcours, auteur,
  conversation, bien quand il existe, genre, réponses en JSON dans la LANGUE DE LA FENÊTRE, étape, dates) et une
  table à part pour les coordonnées d'un nouveau mandant (jamais lue par le serveur de l'assistant pour le modèle).
  Lecture : l'auteur avant la création ; le négociateur de l'annonce et l'admin après ; toujours l'admin. Écriture par
  fonctions dédiées (pas d'accès direct). ⛔ Patch + répétition + inverse = **son accord** pour coller. Reste à trancher
  par lui : QUAND effacer les coordonnées (proposé : dès que la fenêtre les a reçues).
- **P1 — le moteur de questions côté serveur** : les 19 questions du §88 en données (ordre, conditions par type de
  bien, cases remplies, choix réels de la fenêtre), « question suivante » sans modèle, une route qui enregistre une
  réponse. Le programme `verif_couverture.py` versé au dépôt (phase2/checks) et rejoué sur ces données : 0 oubli exigé.
- **P2 — les boutons sous une question** dans l'écran de l'assistant (boutons, cases à cocher, compteurs, « je ne sais
  pas », « modifier », repère « 4 sur 19 ») ; ⚠ écran partagé : les autres cartes ne bougent pas.
- **P5 — les listes** : création (19 questions), puis le rapport (24 cases), puis l'envoi.
- **P4 — la consigne** : quand appeler le modèle (bilan de départ, phrases libres lues ENSEMBLE par un petit lecteur,
  textes proposés), l'enchaînement création → rapport → envoi, la reprise.
- **P6 — les photos du bien depuis la conversation** : un second paramètre « photos du bien » de la carte, versé dans
  l'étape 2 APRÈS l'ouverture (l'ouverture les vide aujourd'hui, 18251).
- **P7 — les documents, voie A** : après le travail `done` et le numéro Hektor, la carte « Déposer des documents »
  proposée sur ce bien avec les fichiers gardés au coffre.
- **P8 — l'envoi attend CE PDF (§87)** + la trace « envoyé » posée APRÈS Gmail. Code du worker / du backend → « vas-y »,
  redémarrage = **son accord**.
- **L'épreuve finale** : remplir la fenêtre par le parcours, puis relire CHAQUE case (pour les 6 types de bien) ; le
  rapport de même ; c'est elle qui prouve que la réponse arrive dans la case, ce que §88 ne prouve pas.

Restent à trancher par lui : l'effacement des coordonnées d'un nouveau mandant (avant P3) ; le sens de « clearing ».

## 90. LOT 0 FAIT : les 10 défauts corrigés (9 dans le code, le 7 attend la mémoire), éprouvés à l'écran et par un essai (19/11) — POUSSÉ le 19/11 avec son accord (0a6abe6 sur main, Vercel prêt)

**Ses mots** : « Vas-y, sois autonome, mais contrôle et vérifie par des tests pour avoir le résultat souhaité. »

**⚠ Où est le code** : une AUTRE session modifiait `App.tsx` dans `C:\Hektor\Projet` au même moment (non commité, 00:07 :
la recherche du mandant élargie à tout le réseau dès qu'on tape, décision « R » du 12/10). Pour ne rien écraser, le lot 0
est fait dans une copie séparée : **`C:\Hektor\Projet-lot0`, branche `etape4-chap6-lot0`**, partie de 4a66147. Les deux
travaux touchent la même recherche (l. ~16050) mais pas les mêmes lignes : la fusion devrait se faire seule, à vérifier
au moment de fusionner.

**Ce qui est corrigé** (front seul ; aucune base, aucun worker, aucun appel à Hektor) :
- **D1** le mandant posé par la carte n'est plus effacé s'il manque dans les 12 lignes de la recherche : il est remis en
  tête ; taper dans la recherche l'efface comme avant. La marque ne reste que si c'est TOUJOURS celui de la carte.
- **D2** sans agence sur la carte, l'agence du négociateur est prise dans la liste ; s'il reste absent, un message le DIT
  (« … n'est pas dans la liste de l'agence … : choisis le négociateur à l'étape 1 ») ; la liste pas encore chargée ne
  l'efface plus. Un commercial reste forcé sur lui-même (inchangé).
- **D3** le statut du syndicat se résout en code de la liste (`kind: 'enum'`), scan compris.
- **D4** une pièce au type non reconnu arrive SANS type (« — type à choisir — », son nom gardé dans le détail) ;
  « Créer » renvoie à l'étape Composition en la nommant. La saisie à la main n'a pas ce choix vide (inchangée).
- **D5** la date d'estimation du jour n'est posée que pour une estimation (le scan garde son défaut).
- **D6** l'adresse du haut de l'étape 3 a sa clé (`adresse_haut`) ; la marque, les pastilles et le compte du bandeau ne
  retiennent que les cases réellement remplies ET montrées pour ce type de bien.
- **D8 (a)** fermer l'éditeur du rapport (« Retour » ou un clic à côté, les 5 portes) demande confirmation s'il porte une
  saisie DE LA PERSONNE non générée ; « Générer » la solde. Le brouillon gardé en base (b) viendra avec la mémoire (P3).
- **D9** DPE et GES (liste A à G ; une valeur hors liste déjà présente reste proposée), chauffage, exposition : 4 cases
  dans l'onglet État de l'éditeur.
- **D10** une photo WebP devient JPEG dans le navigateur (`lib/photoJpeg.ts`) au trombone de l'assistant ET à l'étape 2
  de la fenêtre ; PNG, PDF et autres fichiers inchangés ; un WebP illisible est rendu tel quel.
- **D7** non traité ici : il dépend de la mémoire du parcours (P3).

**Les preuves** :
- `npm run build` vert.
- **À l'écran (mode maquette, sans base ni Hektor)**, deux parcours de l'assistant :
  - une estimation d'appartement avec une pièce « Chaufferie », un négociateur inconnu et un mandant :
    - 13 cases annoncées = 6 + 3 + 1 + 2 + 1 dans les pastilles ;
    - « Adresse privée (rue) » vide et sans marque ;
    - statut syndicat = PROCEDURE_EN_COURS ;
    - date d'estimation du jour ;
    - message du négociateur ;
    - mandant gardé alors que la recherche ne rend rien (avant : effacé) ;
    - « Chaufferie » en « type à choisir », et « Créer » renvoie à la Composition ;
  - une mise en vente sans agence : agence « GTI Saint-Etienne » retrouvée, négociateur gardé, date d'estimation VIDE.
- **L'éditeur** : les 4 cases ; « non » à la confirmation garde l'éditeur et la saisie (DPE D, chauffage) ; « oui »
  ferme ; témoin : sans saisie, aucune question.
- **D10** : un vrai WebP fabriqué devient un vrai JPEG (en-tête ff d8 ff, 40×30). Par le trombone, `facade.webp`
  devient `facade.jpg` ; dans la fenêtre, la photo est rangée en image/jpeg.
- **Témoins inverses** :
  - fenêtre ouverte à la main : aucun bandeau, aucune marque ;
  - taper dans la recherche efface le mandant ;
  - un négociateur choisi à la main n'est pas marqué.
- **Essai hors ligne** `apps/hektor-v1/test_etape4_lot0_defauts.cjs` : 32 contrôles verts. Il exécute le code réel
  pour D3 et D4 et garde les ancres des autres. Une mutation (D3 et D5 remis comme avant) est attrapée.
- **Toute la batterie du front (42 essais)** : 33 verts, 9 non verts DÉJÀ AVANT le lot 0. Ces 9 donnent la même sortie
  sur 4a66147, mesurée dans une copie temporaire, numéros de ligne neutralisés.
- ⚠ **Non éprouvé** : avec la vraie base (vraie liste de 12 mandants, vrais négociateurs, envoi d'une photo convertie
  chez Hektor). Rien n'a été créé ni envoyé.

**Ce que ça pourrait casser ailleurs** : le remplisseur du scan est partagé (D3 et D4 changent aussi le scan, dans le
bon sens) ; l'éditeur de composition est partagé avec la fiche (le choix vide n'y apparaît jamais, une pièce existante a
toujours un type) ; les 4 fonds de l'éditeur passent par `fermerEditeurAvis`.

**Reste à faire par lui** : dire s'il faut fusionner la branche dans `main` (quand l'autre session aura commité), puis
pousser (son accord). Ensuite : P3, la mémoire (patch, son accord), après ses deux réponses (effacement des coordonnées,
« clearing »).

## 91. SES DEUX RÉPONSES (19/11) ; « clearing » audité ; P3, LA MÉMOIRE DU PARCOURS : patch écrit, répété, POSÉ EN PRODUCTION le 19/11

**Ses mots** : « Ok vas-y, je valide ta reco de règle, et non je sais pas, audit pour clearing. »

### 91.1 La règle d'effacement, VALIDÉE

Les coordonnées d'un nouveau mandant s'effacent **dès que la fenêtre les a reçues**. Le reste du parcours s'efface
**30 jours** après son dernier mouvement (proposition du §80.8). Des coordonnées jamais prises (parcours abandonné)
s'effacent aussi à 30 jours, avec leur parcours.
⚠ Conséquence assumée : si la personne ferme la fenêtre sans créer, les coordonnées ne sont plus dans la base (la fenêtre
les avait, elle les perd en se fermant, comme une saisie à la main). Il faudra les ressaisir.

### 91.2 « clearing » : l'audit (lecture seule)

- **Ce que c'est chez Hektor** : une case oui / non / non précisé du bloc des **diagnostics**, entre l'ERP (risques) et
  le plomb (`console_job_worker.js`, `HEKTOR_OUI_NON_EXACT_FIELDS`). Notre fenêtre la montre à l'étape 5 « Diagnostics
  & énergie » sous le libellé brut « Clearing » (App.tsx:1686), le worker l'envoie, la fiche l'affiche (31820).
- **Son sens** : NON TROUVÉ. Aucune note, aucune capture de Hektor ne porte son libellé : la saisie console ne garde que
  le libellé des boutons (« Non précisé », « Oui », « Non »). ⚠ Hypothèse NON prouvée : dans le vocabulaire des
  diagnostics, « clearing » désigne le contrôle de fin de travaux après retrait d'amiante (mesure d'empoussièrement).
  Seul l'écran de Hektor (l'infobulle ou le libellé de la case) le dirait.
- **Son usage, mesuré** sur les 13 565 fiches : la case n'existe que dans les **125** fiches qui ont un relevé de la
  console. **1 seule dit « oui »** (une maison active), **6 disent « non »**, 100 « non précisé », 18 sans valeur.
  Témoin positif : `diag_assainissement` est présent dans 12 942 fiches par la même recherche.
- **Déjà décidé ailleurs** : `clearing` est exclu du contrôle au retour (8a7, « ne se lit pas dans la fiche »).
- **Conclusion** : on garde la décision du §88, « laissé à la main, déclaré ». Aucune question du parcours ne la pose.
  À rouvrir seulement si l'écran de Hektor lui donne un sens utile.

### 91.3 P3 — la mémoire du parcours : ce que pose le patch

Fichiers : `supabase/patch_assistant_parcours_memoire_2026-11-19.sql`, `…_INVERSE.sql`, `…_REPETITION.sql`.
Patron repris : le schéma privé `ged_prive` de la GED (morceau 9, 13/11).

- **`app_assistant_parcours`** : un parcours (genre `creation_estimation` / `creation_annonce` / `avis`), ses réponses
  aux NOMS DES CASES DE LA FENÊTRE, l'étape, l'état, l'annonce quand elle existe. Écrite par le **serveur seul**.
  **Lue par** : son auteur, **le négociateur de l'annonce** dès qu'elle existe (e-mail du profil actif = celui de la
  fiche), l'admin. ⚠ Le manager n'est pas nommé. ⚠ Choix fait par moi, à valider : **l'auteur garde la lecture** après
  la création (c'est sa conversation, qu'il lit déjà). Une contrainte REFUSE les clés `email` / `telephone` dans les
  réponses.
- **Le schéma `assistant_prive`** et sa table `mandant_coordonnees` (civilité, nom, prénom, e-mail, téléphone,
  adresse, CP, ville ; aucune autre case acceptée). Deux portes seulement :
  - `app_assistant_mandant_deposer` : l'**écran de l'auteur**, sur SON parcours de création en cours ;
  - `app_assistant_mandant_prendre` : l'écran qui ouvre la fenêtre (auteur ou admin) ; **rend ET efface** ; une
    seconde prise ne rend rien.
  - ⭐ **La clé de service n'a AUCUNE des deux portes** : le serveur de l'assistant (celui qui parle au modèle) ne peut
    ni les écrire ni les lire, même par erreur. L'API ne voit pas ce schéma, donc **la descente de 07:45 ne les
    recopie pas** sur le serveur local (ni dans la sauvegarde de 09:00).
- **L'effacement à 30 jours** : `app_assistant_parcours_purger()` et la tâche pg_cron `assistant-parcours-purge`
  (03:15 UTC = 04:15 à Paris).
- **Rien ne l'appelle encore** : le moteur (P1), les boutons (P2) et D7 viendront à part. La table naît vide.

### 91.4 Les preuves (sans rien garder)

- **La répétition** jouée en base par `jouer_sql.py` (transaction annulée) : **TOUT EST VERT, 31 contrôles**, patch
  puis inverse. Elle se met à la place de chaque personne (auteur, autre, négociateur réel, admin réel, anonyme, clé de
  service) seulement autour de l'appel testé. Elle prouve notamment :
  - avant l'annonce, le négociateur ne lit pas ; après, il lit (**témoin positif**) ; un autre ne lit jamais ;
  - l'écran n'écrit pas le parcours ; ni l'écran ni la clé de service ne lisent la table privée ;
  - la clé de service ne peut ni prendre ni déposer ;
  - la prise efface, la seconde prise rend vide, un autre ne prend rien et n'efface rien ;
  - un dépôt vide efface ; un parcours fini ne reçoit plus de coordonnées ;
  - la purge efface le vieux parcours AVEC ses coordonnées, garde ceux qui ont bougé (le déclencheur remet `maj_le`) ;
  - l'inverse retire tout et laisse les conversations, les messages et les cartes.
- **Relu après** : aucune table, aucun schéma, aucune fonction, aucune tâche restés en base.
- **Trois mutants, trois rouges** : la prise qui n'efface pas (rouge ⑪) ; la règle sans le négociateur (rouge ④) ; le
  dépôt ouvert à un autre (rouge ⑦).
- ⚠ Mon outil de répétition refusait tout `end;`, même dans un bloc : il ne regarde plus que le texte HORS des blocs
  `$…$`. Témoin : il refuse toujours le patch (qui porte `commit;`).

### 91.5 Ce que ça pourrait casser ailleurs

- La descente recopiera `app_assistant_parcours` (vide au départ) ; rien d'autre ne la lit.
- Une 15e tâche pg_cron : un DELETE d'une petite table par nuit.
- Rien sur les tables métier, les conversations, les cartes, `app_agent_run`.

### 91.6 LA POSE (19/11, son accord : « colle-le toi-même, tu as mon accord »)

- Posé par moi, le fichier TEL QUEL (empreinte md5 `28d28c2e…` vérifiée = celui du commit 713712b et de la répétition),
  ses propres `begin` / `commit` : « PATCH PASSÉ, sans erreur ». Ses vérifications internes ont tenu.
- **Relu par une seconde voie** (le connecteur de la base) : les 2 tables, 0 ligne, 1 règle de lecture, la tâche
  `assistant-parcours-purge 15 3 * * *` active (15 tâches pg_cron en tout) ; la clé de service n'a ni le schéma
  privé ni la porte de prise ; l'écran a la prise mais pas la purge ; anon n'a pas le dépôt ; l'écran n'écrit pas le
  parcours, la clé de service oui.
- **Ce que voit la descente**, lu dans la spec de l'API comme elle la lit : 255 tables ; `app_assistant_parcours` OUI,
  `mandant_coordonnees` NON. Témoin positif : `app_assistant_action` vue.
- Retour arrière s'il le faut : `…_INVERSE.sql` (rien ne l'appelle encore, la table est vide).

**Reste** : P1, le moteur de questions côté serveur (« vas-y »). Question ouverte : l'auteur garde-t-il la lecture après
la création (choix posé par moi) ?

## 92. SA DÉCISION « que le négo et admin » (19/11) : patch écrit, répété, COLLÉ EN PRODUCTION le 19/11

**Ses mots** : « 2. Que le négo et admin » (à ma question : l'auteur garde-t-il la lecture après la création ?).

- **Ce que ça change** (`supabase/patch_assistant_parcours_lecture_nego_2026-11-19.sql`, + `_INVERSE`, + `_REPETITION`) :
  l'auteur lit son parcours SEULEMENT tant qu'aucune annonce n'y est attachée ; dès qu'elle existe, son négociateur et
  l'admin seulement. La prise des coordonnées suit la même règle (l'admin toujours). Rien d'autre ne bouge.
- **Garde** : le patch s'arrête si la règle ou la fonction ne sont plus celles posées le 19/11 (texte de la règle,
  empreinte md5 `1be5c94e…` de la fonction, retours chariot retirés — leçon 30).
- **Répétition** jouée en base puis annulée : **11 contrôles verts + le témoin inverse** (l'inverse rejoué, l'auteur
  relit). Relu après : la base porte toujours la règle du matin (0 ligne dans la table).
- **En pratique** : un commercial crée pour lui-même (la fenêtre le force sur lui, D2) ; il reste le négociateur, donc
  il garde la lecture. Seul l'auteur qui crée POUR un autre la perd après la création.

**Collé le 19/11** par moi, avec son accord (« Oui vas y »), par le même script que P3 (empreinte du fichier vérifiée
avant : md5 `a714cb9a…`, celui du commit 7976217). « PATCH PASSÉ, sans erreur ». **Relu en base** : une seule règle de
lecture, de la forme nouvelle (`user_id = auth.uid() AND app_dossier_id IS NULL` OR admin OR négociateur) ; la prise
porte `app_dossier_id is null` ; elle reste exécutable par `authenticated` SEUL (ni anon, ni service_role) ; 0 ligne.

## 93. P1 — LE MOTEUR DE QUESTIONS CÔTÉ SERVEUR (19/11) : écrit, éprouvé hors ligne, dormant, NON poussé

**Ses mots** : « 1. Oui » (à « je commence P1 ? »).

### 93.1 Ce qui est écrit

- **Les données** `backend/app/services/parcours_creation.json` : les 19 questions du §88, dans la LANGUE DE LA FENÊTRE
  (noms de ses cases), leur forme (cases, compteurs, cocher, grille, pièces, mandant, fichiers, texte), leurs
  conditions (type de bien ; piscine cochée ; construction de moins de 10 ans), le profil de chaque type de bien, les
  cases automatiques et les deux laissées à la main (dépôt de garantie, « clearing »). ⭐ Les OPTIONS des cases ne sont
  pas recopiées : l'écran (P2) les prendra dans la fenêtre elle-même — une seule source.
- **Le moteur** `backend/app/services/assistant_parcours.py`, SANS modèle : la question suivante, le repère « 4 sur
  17 », et l'enregistrement d'une réponse qui ne touche QUE les cases de sa question (« je ne sais pas » et « je
  complète plus tard » font avancer ; vider une case la retire ; la composition et les photos ont leur forme). ⛔ Une
  coordonnée de mandant (e-mail, téléphone…) est REFUSÉE : elle passe par les cases protégées (P3).
- **La table** (`ParcoursStore`) : créer et écrire par la clé de service ; relire pour l'écran avec le JETON de la
  personne (la règle de lecture de la base décide) ; écrire est CONDITIONNEL (même `maj_le`, à lui, en cours, avant la
  création) : deux onglets, un seul passe.
- **Trois routes** dans `routers/assistant.py` : `POST /assistant/parcours` (commencer, dans SA conversation),
  `GET /assistant/parcours/{id}` (relire), `POST /assistant/parcours/{id}/reponse` (répondre). Derrière l'interrupteur
  **`assistant_parcours`** (off / admin / on), **ABSENT en base = éteint** : rien ne change tant qu'on ne l'allume pas.
  Même l'admin ne répond pas dans le parcours d'un autre.

### 93.2 Les preuves (hors ligne)

- **La couverture, versée au dépôt** : `apps/hektor-v1/test_etape4_parcours_couverture.cjs` exécute le CODE RÉEL
  d'App.tsx (groupes, cases par profil, cases du haut, profil de chaque type, type par défaut, clés d'une pièce) et le
  croise avec les données du serveur : **TOUT EST VERT** — maison 136, appartement 132, terrain 59, garage 43,
  immeuble 71, autre 51 cases montrées, **0 oubliée** ; aucune question vide ; les 29 types au bon profil ; aucune
  case posée deux fois ; aucune coordonnée parmi les réponses ; témoin inverse (une case retirée → 1 oubli).
  ⭐⭐ **Il a corrigé le §88** : mon programme de travail sous-comptait le terrain (45 au lieu de 59) et l'immeuble (35 au
  lieu de 71) ; et **la copropriété d'un IMMEUBLE était un vrai oubli** (la fenêtre la montre). Corrigé dans les données.
  Plusieurs questions ont aussi leurs vrais types (piscine : maison seule ; intervenants et construction récente :
  maison et appartement ; pas de diagnostics pour un garage…).
- **L'essai du serveur** `backend/tests/test_assistant_parcours.py` : **58 contrôles verts** (conditions par type,
  refus, parcours complet qui finit pour les 6 types — maison 15 questions, appartement 17, terrain 12, garage 11,
  immeuble 15, autre 12 —, table conditionnelle, routes : interrupteur, conversation d'un autre, parcours d'un autre,
  question non posée, e-mail refusé, écriture concurrente, fiche créée ; aucune requête vers OpenAI).
  **Trois mutants, trois rouges** (case d'une autre question acceptée ; coordonnée acceptée ; piscine toujours posée).
- **Rien de cassé ailleurs** : les essais de l'assistant rejoués — gestes 415, fichiers 28, lecteur 73, socle 30
  (sa partie 5 SAUTÉE comme avant : le SDK de l'agent n'est installé dans aucun Python de cette machine).

### 93.3 Ce que ça pourrait casser ailleurs

- Le routeur de l'assistant gagne 3 routes ; les routes existantes ne sont pas touchées (essais rejoués).
- Render redéploie le serveur au push : les routes y dorment tant que `assistant_parcours` est absent.
- ⚠ Non éprouvé : contre la VRAIE table (seulement contre une fausse table qui imite les conditions de PostgREST).
  L'épreuve réelle viendra avec P2 (l'écran), interrupteur sur « admin ».

**Poussé le 19/11** avec son accord, après fusion de main (11 commits de l'autre session : classeur, GED lot G'),
front construit, essais rejoués verts (couverture, lot 0, serveur 58, gestes 415, lecteur 73, fichiers 28, socle 30).
⚠ Un rouge À L'AUTRE SESSION, pas à moi : `test_ged_remplir_contact.cjs` 79 verts / 1 rouge (« une case changée depuis
l'ouverture n'est pas écrite… ») — ma branche ne change aucun code du front par rapport à main.

**Reste** : P2, les boutons sous une question dans l'écran de l'assistant.

## 94. P2 — LES BOUTONS SOUS UNE QUESTION (19/11) : écrit en 4 morceaux, éprouvé hors ligne et en maquette, dormant, NON poussé

**Ses mots** : « Oui p2 », puis « B, entrée admin » (avant P4, un parcours commence par une entrée d'essai réservée à
l'admin). Puis, en voyant l'entrée sous une conversation d'exemple « baisse de prix » : « Stop … pourquoi tu lances un
formulaire d'ajout d'annonce sur cette question à l'IA ? ». Explication donnée : ce n'est pas l'IA, c'est mon clic d'essai
en maquette ; à la fin (P4) c'est l'IA qui proposera le parcours selon la demande, sans aucun bouton. Sa réponse :
« ah j'ai compris, reprends comme prévu » → l'entrée d'essai est GARDÉE telle quelle (admin, marquée « Essai admin, sans
l'IA »), elle disparaît à P4.

### 94.1 Les 4 morceaux (commits 0452d9a, 7ba4009, 663be48, 21b36b0, 80a7483)

1. **Serveur** (0452d9a) : `GET /assistant/parcours?conversationId=` (une conversation rouverte retrouve ses parcours, relus
   avec SON jeton) et `POST /assistant/parcours/{id}/cree` (la fiche créée termine le parcours, une seule fois, écriture
   conditionnelle). La vue rend aussi la forme et les cases de CHAQUE question posée (pour « Modifier »). Essai serveur :
   **67 verts** (9 nouveaux).
2. **La question à l'écran** (7ba4009) : `ParcoursGuide.tsx`, la carte de la maquette v27 (en-tête rose, fil des rubriques,
   compteurs « − n + », pastilles, champs, pièces une à une ; « Je ne sais pas », « Plus tard », « Valider » ; les réponses
   en pastilles vertes « Modifier »). Les cases et listes viennent de `catalogueParcoursFenetre` (App.tsx) : celles que la
   FENÊTRE montre pour ce type de bien, avec SES libellés et SES listes. La rue / le code postal / la ville du haut sont
   proposés en recopie dans l'adresse privée (§89 D6). Tout dort derrière `assistant_parcours` (sonde : 403 = rien).
3. **Le mandant (D7)** (663be48) : un contact existant (recherche dans tout le réseau, décision « R » ; son NUMÉRO seul part
   dans les réponses) ou un nouveau mandant : civilité, nom, prénom, e-mail, téléphone, adresse, CP, ville dans un état À
   PART, déposé par l'écran au coffre privé (`app_assistant_mandant_deposer`, jeton de la personne) ; JAMAIS au serveur de
   l'assistant. Bandeau au cadenas de la planche 11.
4. **La fin** (21b36b0) : « Ouvrir la fenêtre remplie » → `assistantOuvrirParcours` : la fenêtre remise à zéro comme au
   bouton, chaque réponse dans SA case (aucune traduction), la composition pièce par pièce, le mandant existant retrouvé
   par son numéro, les coordonnées d'un nouveau mandant PRISES au coffre (prendre = effacer) ; une estimation sans date
   porte la date du jour (comme le scan, D5). Le bandeau dit « d'après tes réponses au parcours ». Après « Créer », le
   parcours est noté terminé (avec le bien) et l'écran le montre « créée ».

### 94.2 Les preuves

- **Essai du catalogue contre le vrai App.tsx** (`apps/hektor-v1/test_etape4_parcours_catalogue.cjs`, 80a7483) : **21 verts**.
  Profil par profil, le catalogue montre EXACTEMENT les cases de la fenêtre (maison 136, appartement 132, terrain 59, garage
  43, immeuble 71, autre 51) ; chaque case montrée des 19 questions a son libellé et sa liste ; la liste est l'objet même
  de la fenêtre ; pas de négociateur à choisir pour un commercial ; l'ouverture range chaque case hors des groupes ; la
  réponse envoyée au serveur ne prend jamais une coordonnée. **Deux témoins** : un catalogue qui oublie une case est
  attrapé ; un écran volontairement faux (`corps.email = coordonnees.email`) est attrapé — ⚠ ma première garde le RATAIT
  (elle ne lisait pas `corps.xxx =`), corrigée avant le commit.
- **En maquette** (sans base, données inventées) : le parcours complet joué à l'écran — bien, intérieur (compteurs),
  composition, dehors coché, nouveau mandant —, puis la fenêtre ouverte et relue étape par étape : 10 cases marquées (Offre
  5, Secteur 3, Composition 1, Mandat 1), adresse / code postal / ville, la pièce, Mme. Lefèvre et son e-mail à l'étape
  Mandat, la date d'estimation du jour ; une SECONDE ouverture dit que les coordonnées ne sont plus gardées. L'e-mail tapé
  n'apparaît plus nulle part dans la page après « Valider ».
- **Trois défauts trouvés et corrigés en route** : deux clics rapides sur « + » ne comptaient qu'un (le compteur partait de
  l'ancienne valeur) ; un nombre sans son libellé dans la pastille verte (« 1 » → « Pieces : 1 ») ; la civilité effacée par
  une frappe juste après le clic (même cause que le compteur). Plus une fausse donnée de maquette (type 1 = Maison rangé en
  appartement).
- Rejoués verts : couverture (0 oubli), lot 0, essais serveur de l'assistant (parcours 67, gestes 415, socle 30).

### 94.3 Ce que ça pourrait casser ailleurs

- L'écran de l'assistant : les cartes d'aujourd'hui ne bougent pas ; le parcours n'apparaît que si l'interrupteur
  `assistant_parcours` l'ouvre au compte (ABSENT en base = rien).
- La fenêtre de création : une nouvelle voie d'entrée qui ne fait que POSER des valeurs, comme la carte d'aujourd'hui ;
  la création elle-même n'a gagné qu'un bloc après le succès (noter le parcours terminé), qui n'échoue jamais la création.
- La règle des cases du haut est RECOPIÉE dans le catalogue : l'essai du catalogue exige les mêmes noms que la fenêtre.

### 94.4 Limites dites

- Pas éprouvé contre la vraie table ni la vraie fenêtre connectée : c'est l'essai réel (interrupteur sur « admin », son
  accord).
- « Modifier » une autre question pendant qu'on en remplit une perd la saisie non validée de celle-ci.
- Après un rechargement de la page, l'écran ne sait plus que des coordonnées sont déjà au coffre (il ne peut pas les
  relire sans les effacer) : re-valider « nouveau mandant » sans rien taper est alors refusé ; il suffit de les retaper.
- Les photos (forme « fichiers ») restent à déposer dans la fenêtre (P6).

**Reste** : pousser (son accord) ; l'essai réel en admin (allumer `assistant_parcours` sur « admin » = écriture en base,
son accord) ; puis P5, P4, P6, P7, P8.
