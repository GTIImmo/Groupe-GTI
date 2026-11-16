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
