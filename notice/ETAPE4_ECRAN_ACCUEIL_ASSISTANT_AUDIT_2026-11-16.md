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
