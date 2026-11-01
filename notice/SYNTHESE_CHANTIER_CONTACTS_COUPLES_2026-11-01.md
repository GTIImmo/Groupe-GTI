# SYNTHÈSE — LE CHANTIER DES CONTACTS ET DES COUPLES (29/10 → 01/11/2026)

**Demande de Frédéric (01/11)** : « un nouvel audit en regroupant toutes les découvertes sur ce chantier, propose-moi comment
faire, et on en profite pour faire du tri si possible ». Et : « ce champ famille existe déjà ? ou on le crée ? »

> Cette note **regroupe** ; elle ne remplace pas les notes de détail (liste au §7). En cas de désaccord : le code, puis les mesures
> datées des notes de détail, puis cette page. ⛔ Rien n'est codé par cette note. Les chiffres viennent du serveur
> (`data/hektor.sqlite`, `phase2/phase2.sqlite`) et de Supabase, mesurés en lecture seule le 01/11.

---

## 0. EN UNE PAGE

- **Ton ancien logiciel** ne savait pas relier deux fiches : un couple, c'était **une fiche** « M. et Mme » avec deux prénoms.
- **La migration vers Hektor (~01/03/2026)** a recopié les fiches une par une, **perdu « Madame »**, et, selon un réglage **par
  agence**, fabriqué des **cases de conjoint vides** : pour chaque couple partout, et pour **chaque fiche** dans 4 agences
  (Firminy, Ambert, Saint-Just-Saint-Rambert, Saint-Didier-en-Velay). Elle n'a ni séparé les deux prénoms, ni dédoublonné.
- **Résultat sur 356 762 fiches** : **210 269 vraies personnes** (dont 14 860 doublons en trop) et **146 493 cases vides**.
- **Le lien de couple de Hektor ne prouve donc rien** pour une fiche d'avant mars ; seul ce qu'un agent a écrit le prouve.
- **Chez nous, déjà fait** : les cases vides sont masquées de l'annuaire (11/09), un couple créé dans l'app naît en deux fiches
  (31/10), les codes de couple sont traduits (P1) et la première fiche connaît son conjoint (P2, posé le 01/11).
- **Proposition** : ajouter une **« nature »** à chaque fiche, calculée la nuit au serveur, lue par l'app — et en profiter pour
  **trier** : Madame rendue, cases vides rangées, fiches supprimées chez Hektor signalées, doublons en revue.

---

## 1. LE CHAMP « NATURE » N'EXISTE PAS — ON LE CRÉE

Vérifié dans Supabase (`app_contact_current`, 46 colonnes) et dans le code de la nuit. Ce qui existe de proche :

- `couple_role` : seulement 3 valeurs — `menage_resolu` (case vide dont la principale est connue), `menage_orphelin` (principale
  disparue), `conjoint` (P2) — et vide pour tout le reste. **Lu par 3 endroits** (le filtre de l'écran `SANS_FICHE_DE_MENAGE`,
  `conjoints_des_couples.py`, la fonction de la paire `app_contact_creer_conjoint` qui l'écrit).
- `couple_json` (P2) : seulement sur les premières fiches de couple.
- `typologies_json` / `relation_roles_json` : le **type métier** (acquéreur, mandant, partenaire…). **C'est un autre axe** : une
  « personne seule » peut être acquéreur ET mandant. On n'y touche pas.
- `marital_status` : connu pour 17 couples seulement.
- `duplicate_*` : le drapeau doublon, calculé chaque nuit.

**Conseil : une colonne neuve `nature_fiche`** (7 valeurs), plus `civilite_app` (la civilité corrigée). **Pas** une extension
de `couple_role` : ses lecteurs actuels changeraient de sens sans le savoir (une nouvelle valeur passerait le filtre de l'écran,
et la fonction de la paire l'écrit). Additif : personne ne la lit tant que l'écran n'est pas branché.

**⭐ DÉCISION DE FRÉDÉRIC, 01/11 — la civilité corrigée va dans `civilite_app` (choix « A »).** Sa question : « nos champs
saisis dans l'app ne s'écrasent pas normalement ? » — **mesuré** : une civilité saisie dans l'app tient **parce qu'elle part
AUSSI chez Hektor** (le worker la met dans le formulaire, `console_job_worker.js` ~l. 18487 et 21066 ; pendant l'envoi,
`app_contact_pending` protège la fiche, `push_contacts_to_supabase.py:494`). La nuit ne protège pas la colonne : les seuls
champs « à nous » sont `birth_date`, `birth_place`, `marital_status` (`phase2/identite/contrat_autorite.py:63`). Notre
« Madame » est un CALCUL, pas une saisie : écrit dans `civilite` sans partir chez Hektor, il serait remis à vide la nuit suivante.
- écartés : **B** écrire et envoyer chez Hektor (≥ 19 290 envois, plusieurs semaines de quota, chaque envoi renvoie toute la
  fiche — villes perdues le 22/10) ; **C** mettre la civilité dans les champs « à nous » (une correction faite dans Hektor ne
  redescendrait plus ; c'est le seul de ces champs que Hektor renvoie).
- la suite prévue : quand un agent **confirme** la civilité sur une fiche, elle passe par le chemin normal (saisie → Hektor).

---

## 2. CE QU'ON A DÉCOUVERT, REGROUPÉ

### 2.1 L'ancien logiciel (classeurs du 27/02/2026, `AUDIT_MIGRATION_C3…` §1-2)
202 218 fiches. Couple = civilité `gender` 4 (« M. et Mme », 21 653), 5 et 6 (deux hommes / deux femmes, 265) ; deux prénoms tapés
dans le même champ. Les relations ne lient une fiche qu'à une **affaire** (vendeur, acquéreur, notaires, apporteurs) : **aucun
lien entre deux fiches**.

### 2.2 La migration vers Hektor (`AUDIT_COUPLES_ANCIENS…` §9-10)
- **Recopie une pour une** : 96 % retrouvées par le nom et la date de création, recopiée au jour près.
- **Civilité** : Monsieur → « M. » (74 %) ; **Madame → vide (99,7 %)** ; M. et Mme → « Mr./Mme » (98 %).
- **Cases de conjoint, par agence** : un couple reçoit une case partout ; une personne seule en reçoit une dans 4 agences
  (96-99 %), presque jamais ailleurs. Preuve de l'import **par lots** : les cases de chaque agence ont des numéros en blocs serrés.
- **Firminy (agence 12)** porte **137 152 fiches nommées (65 %)**, dont **121 241 sur le compte « accueil »** (rattaché à
  Saint-Étienne, d'où leur affichage « Saint-Étienne » dans l'app). Pourquoi : non établi.
- **Prénoms non séparés** (9 071 sur 9 104 « Marcel et Pierrette ») ; **doublons hérités** (~94 %).
- **633 fiches jamais migrées**, dont 305 créées en janvier-février 2026 (la copie de migration date d'avant le 27/02).

### 2.3 Le mécanisme de couple de Hektor (`COUPLES_ERGONOMIE…` §9-10, essais E0-E6 du 30/10)
- Une case `refCouple` : la principale y porte **son propre numéro**, la deuxième fiche **le numéro de la principale**.
- Un couple créé dans Hektor = deux fiches à numéros consécutifs, civilité `M_Mme` (depuis février 2026) ; le foyer s'édite d'un
  bloc ; archiver ou supprimer la principale emporte la deuxième.
- ⛔ « Transformer en couple » a **fait disparaître une fiche** (30/10). « Dissocier le couple » existe.

### 2.4 Ce qui est déjà fait chez nous
- 11/09 : les cases vides à principale connue sont **masquées** (annuaire, recherche, choix d'un mandant) ; règle « une personne,
  une ligne ».
- 21/09 : le lien de couple posé dans notre série de numéros (`app_couple_contact_id`) — ⚠ lu par aucun code.
- 31/10 : **un couple créé dans l'app naît en deux fiches** (pièces A-B-C, essai réel 20000028/29 ↔ 606094/95).
- P1 (31/10) : les codes `M_Mme`… traduits dans le nom affiché. P2 (posé le 01/11) : `couple_json` et le rôle `conjoint`.

### 2.5 Les chiffres de tout le serveur (`AUDIT_NATURE…` §1-2 bis)
Serveur · actives · dans l'app :
1. Personne seule 181 290 · 68 623 · 39 891 (dont 113 894 mises en couple par l'import sans raison) ;
2. Couple 28 473 · 11 302 · 4 788 ; 3. Conjoint 506 · 451 · 67 ;
4. Conjoint sans prénom 13 150 · 12 033 · 1 540 ; 5. Case conjoint vide 96 889 · 53 287 · 12 111 ;
6. Case vide orpheline 36 454 · 26 863 · 3 777 ;
7. Doublons : 14 860 fiches en trop (1 102 dans l'app).
Les couples : 422 avec un vrai conjoint, 13 135 au nom recopié, 11 298 à case vide, 1 142 sans deuxième fiche (la principale
pointe sur elle-même), 2 475 sans lien du tout (dont 602 supprimées chez Hektor). 12 206 couples ont les deux prénoms écrits.

### 2.6 Les défauts encore ouverts (audit du 29/10, §5)
- **n° 1, toujours là (vérifié le 01/11, `App.tsx:4415`)** : le document de mandat déplie les membres d'un couple sans écarter la
  case vide → une case vide peut devenir un mandant sans nom, et une case de signature. **Le seul qui touche un acte signé.**
- n° 2 à n° 9 (conjoint jeté en silence à certaines créations, case vide qui reste quand on retire la principale, ville du conjoint
  en texte seul, « Mr./Mme » absent du formulaire, trois détections différentes de la case vide, `app_couple_contact_id` jamais lu,
  `menage_orphelin` mal nommé) : **état du 29/10, non re-mesuré**.

---

## 3. LE TRI PROPOSÉ — CHEZ NOUS SEULEMENT

Rien n'est supprimé, rien n'est écrit chez Hektor. Chaque tri est une **étiquette** posée la nuit, réversible.

- **T1 — la nature de chaque fiche** (les 7 natures) : base de tout le reste.
- **T2 — rendre « Madame »** : 51 672 fiches, **19 290 actives**, d'après le classeur ; dans `civilite_app`, jamais dans `civilite`.
- **T3 — les cases vides qui survivent à leur principale** : **17 346 cases ACTIVES dont la principale est ARCHIVÉE**. Chez nous, elles
  suivent l'état de leur principale (affichées archivées) ; Hektor n'est pas touché.
- **T4 — les fiches supprimées chez Hektor** : **611** (nous gardons leur nom parce qu'une annonce ou une offre les cite).
  Étiquette « supprimée chez Hektor », jamais proposées dans un choix de contact.
- **T5 — les cases orphelines** (36 454) : retirées de l'annuaire, de la recherche et du choix d'un mandant ; « Conjoint non
  identifié » sur leur bien (le bien lit ses mandants sans le filtre de l'annuaire, vérifié).
- **T6 — les doublons** : une liste de revue pour un admin, en commençant par les **1 102 fiches en trop de l'app** ; la fiche
  écartée est masquée avec « doublon de… » et garde ses biens, recherches et mandats. Chantier à part.
- **T7 — les 633 fiches jamais migrées** : une liste tirée du classeur, pour ressaisie si Frédéric le veut (décision métier).
- **T8 — les 121 241 fiches du compte « accueil »** : une réaffectation d'agence ou de négociateur est une **décision métier** (et
  Hektor seul sait pourquoi l'import les y a mises) — à poser à Hektor, pas à coder.

---

## 4. COMMENT FAIRE — LE PLAN PROPOSÉ

- **Étape 0 (déjà en cours)** : ⏰ 02/11 matin, juger la première nuit de P2 (étape « conjoints des couples » en code 0, ~1 900
  conjoints, poids du push).
- **Étape 1 — le défaut n° 1 du document de mandat** : indépendant de tout le reste, il touche un acte signé. Petit correctif d'écran.
- **Étape 2 — N1 : la nuit calcule `nature_fiche` et `civilite_app`, au serveur seulement** (T1, T2, T3, T4). Essai à blanc :
  les chiffres du §2.5 doivent ressortir. Modification du run de nuit → **« vas-y » requis**.
- **Étape 3 — N2 : la colonne chez Supabase + l'envoi**, derrière un interrupteur `.env`. Écriture en production → **accord requis**.
  ⚠ La première nuit renvoie les 62 174 fiches de l'app une fois.
- **Étape 4 — N3 : l'écran**, derrière un interrupteur, ordinateur ET téléphone : la règle A (P3), les libellés des cases (T5),
  « Madame », les archivées de fait (T3), les supprimées chez Hektor (T4).
- **Étape 5 — les doublons** (T6), chantier à part avec sa grille de gestes.
- **Étape 6 — « compléter le conjoint »** : remplir la case qui existe (24 433 couples), créer la deuxième fiche quand il n'y en a
  pas (1 142), et, pour les 1 873 sans lien, poser le lien sur la principale — **à éprouver d'abord sur une fiche d'essai**.
- **Hors code** : demander à Hektor (le compte « accueil », le réglage d'import, un éventuel ménage de leur côté) ; décider des 633.

---

## 5. CE QUE ÇA POURRAIT CASSER AILLEURS

1. La colonne neuve doit exister chez Supabase **avant** la nuit, sinon le push échoue (même piège que P2).
2. Une clé neuve dans la charge du push peut être jetée : le push doit nommer la colonne (à éprouver hors ligne).
3. `couple_role` et `display_name` **ne changent pas** : le worker (22 lectures), l'espace client, les rendez-vous et l'administration
   lisent `display_name` ; les nouveaux libellés sont composés à l'écran.
4. Masquer les orphelines et les supprimées chez Hektor des listes : un agent ne les trouvera plus par la recherche ; elles restent
   sur leur bien.
5. T3 (cases archivées de fait) : n'est qu'un affichage ; si la principale est réactivée, la case redevient active la nuit suivante.
6. Le classeur contient des données personnelles : chargé une fois dans une table du serveur, jamais dans git ni dans Supabase.
7. Le téléphone a son propre rendu (`MobileLayout`) : chaque libellé à vérifier des deux côtés.

---

## 6. NON MESURÉ

- Les défauts n° 2 à n° 9 depuis le 29/10 ; le comportement de Hektor quand on pose un lien sur une fiche existante ;
  la part de faux positifs de « deux prénoms écrits » ; les fiches robots ou de formulaire passées dans Hektor ; pourquoi le
  compte « accueil » et les 4 agences « foyer pour tous ».

## 7. LES NOTES DU CHANTIER (le détail)

- `AUDIT_COUPLES_CONJOINTS_MENAGES_2026-10-29.md` — l'audit de départ : mécanisme, défauts n° 1-9, décisions.
- `COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md` — essais E0-E6, la paire à la création (A-B-C), P1, P2, réponses du 31/10.
- `AUDIT_COUPLES_ANCIENS_AFFICHAGE_2026-11-01.md` — les couples anciens, la règle A, les doublons (§8), la migration (§9-10).
- `AUDIT_MIGRATION_C3_COUPLES_DOUBLONS_2026-11-01.md` — les deux classeurs (§1-2) ; sa §3 est corrigée par la note précédente.
- `AUDIT_NATURE_DES_FICHES_CONTACT_2026-11-01.md` — les 7 natures, ce qu'on fait de chaque famille, les cas d et e.
