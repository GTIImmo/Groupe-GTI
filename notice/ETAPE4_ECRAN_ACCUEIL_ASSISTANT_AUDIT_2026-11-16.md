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
