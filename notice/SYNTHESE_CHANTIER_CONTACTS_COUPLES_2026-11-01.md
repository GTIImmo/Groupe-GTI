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
  ✅ **FAITE le 01/11 au soir (« vas-y » de Frédéric)** — voir §8.
- **Étape 3 — N2 : la colonne chez Supabase + l'envoi**, derrière un interrupteur `.env`. Écriture en production → **accord requis**.
  ⚠ La première nuit renvoie les 62 174 fiches de l'app une fois.
  ✅ **POSÉE le 01/11 vers 23:15 (par moi, à la demande de Frédéric)** — voir §9 et §10.
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

---

## 8. PHASE 1 POSÉE — 01/11/2026, 22:30 *(serveur seulement)*

**Ce qui existe maintenant**, dans `phase2/phase2.sqlite` (local, ignoré par git) — rien chez Hektor, rien chez Supabase :
- **`ancien_logiciel_contact`** (202 218 lignes) : numéro de l'ancien logiciel, `gender`, numéro **Hektor** apparié, méthode.
  **Aucun nom ni coordonnée.** Remplie UNE fois par `phase2/contacts/charger_ancien_logiciel.py` (le classeur ne bouge plus) :
  194 170 appariées, 8 048 non trouvées — **les chiffres de l'audit à l'unité**.
- **`contact_nature_current`** (356 762 lignes, une par fiche de la couche) : `nature_fiche`, `couple_deuxieme`, `civilite_app`,
  `civilite_source`, `suit_principale_archivee`, `supprimee_chez_hektor`. Recalculée **chaque nuit** par
  `phase2/contacts/nature_des_fiches.py` (~8 s), étape **« phase2 nature des fiches contact »** de `run_full_pipeline.ps1`,
  juste après « conjoints des couples », **non bloquante**.

**Pourquoi une table à part** et pas des colonnes de `app_contact_current` : le push lit cette couche en `SELECT *`, une colonne
de plus partirait chez Supabase où elle n'existe pas et ferait échouer tout l'envoi. La couche est **inchangée** (38 colonnes).

**Mesures sur les vraies données (serveur · actives · app)** — toutes celles du §2.5 ressortent à l'identique :
personne seule 181 290 · 68 623 · 39 891 ; couple 28 473 · 11 302 · 4 788 ; conjoint 506 · 451 · 67 ; conjoint sans prénom
13 150 · 12 033 · 1 540 ; case conjoint vide 96 889 · 53 287 · 12 111 ; case vide orpheline 36 454 · 26 863 · 3 777.
Couples : a 422, b 13 135, c 11 298, d 1 142, e 2 476 *(compte de la couche ; 2 475 dans la fiche brute de Hektor)*.
**T3** 17 346 actives (992 dans l'app) · **T4** 611 (0 dans l'app).
**T2 « Mme. » rendue : 51 540 fiches, 19 245 actives, 14 112 dans l'app.** L'écart avec 51 672 est mesuré, fiche par fiche :
les 51 672 anciennes fiches visent 51 624 fiches Hektor (48 visées deux fois) ; **83 écartées exprès** (une autre ancienne
fiche appariée à la même dit autre chose) ; 1 sans nom. ⭐ 0 « Mme. » posée là où Hektor a déjà une civilité.

**Essais** : `phase2/contacts/test_nature_des_fiches.py`, 17/17 (natures, cas a-e, T3 avec témoin inverse, T4, Madame seulement
si Hektor n'a rien, contradiction, idempotence, appariement).

**Ce qui reste volontairement absent** :
- **pas de battement** : sa clé s'enregistre chez Supabase (`app_worker_registry`) → avec la phase 2, accord requis. D'ici là,
  un échec ne se voit qu'au journal du run (`WARN  phase2 nature des fiches contact`) ;
- les doublons (famille 3) ne sont pas dans la table : chantier à part (étape 5) ;
- Mademoiselle et les couples de deux hommes / deux femmes perdus (178) : non rendus, non décidés.

**Pour revenir en arrière** : retirer le bloc de `run_full_pipeline.ps1`, puis `DROP TABLE contact_nature_current` et
`DROP TABLE ancien_logiciel_contact`. Personne ne les lit.

⏰ **À voir au journal de la nuit du 02/11** : `DONE  phase2 nature des fiches contact`, et la même ligne de comptes.

---

## 9. PHASE 2 PRÉPARÉE — 01/11/2026, 23:00 *(rien n'est posé chez Supabase)*

**Le code, dormant** (commité en local) :
- `phase2/sync/push_contacts_to_supabase.py` : `ajouter_nature()` joint `contact_nature_current` aux lignes de
  `app_contact_current` **avant** l'empreinte et le calcul des disparues ; mêmes 6 clés sur chaque ligne (PGRST102) ;
  table locale absente → rien n'est ajouté (on n'efface pas chez Supabase). **Interrupteur `APP_CONTACT_NATURE`** (.env),
  **absent = éteint**.
- `run_full_pipeline.ps1` : l'étape porte le battement `phase2.nature_contacts`. Avant le patch, le battement fait un PATCH
  sur une clé qui n'existe pas → 0 ligne, sans erreur (`monitoring/heartbeat.py`).

**Le patch** : `supabase/patch_couple_phase2_nature_2026-11-01.sql` (+ `_REPETITION`, `_INVERSE`) — 6 colonnes neuves vides
(`nature_fiche`, `couple_deuxieme`, `civilite_app`, `civilite_source`, `suit_principale_archivee`, `supprimee_chez_hektor`) et la clé
de battement. Aucune vue touchée (les 13 vues qui lisent la table ne nomment pas ces colonnes), pas de CHECK (une valeur
refusée coulerait tout le push).

**Éprouvé** :
- **répétition jouée par moi dans une transaction annulée** : 7 cases vertes (colonnes 6, battement 1, nature, civilité, booléens,
  vue de l'écran, 0 autre ligne remplie) ; **contrôle d'après : rien n'est resté** (colonnes 0, battement 0, essai 0) ;
- **push à blanc, éteint : 0 contact à envoyer** — le code est inerte ; **allumé : 62 174 sur 62 174** (le renvoi unique prévu) ;
- lignes allumées : 1 seul jeu de clés, 0 nature vide, booléens en vrai/faux, 14 112 « Mme. », ~1 577 octets par ligne
  (max 11 574) → un lot de 300 ≈ 462 ko, sous le 1 Mio ;
- essais : `test_dirty_guards` 4/4, `test_nature_des_fiches` 17/17, `test_conjoints_des_couples` 10/10, `test_contact_seconde_fiche` vert.

**⛔ LES GESTES DE FRÉDÉRIC, DANS CET ORDRE** :
1. coller `supabase/patch_couple_phase2_nature_2026-11-01.sql` (contrôle final : colonnes 6, battement 1, remplies 0) ;
2. **SEULEMENT APRÈS** : ajouter `APP_CONTACT_NATURE=1` dans `C:\Hektor\Projet\.env` ;
3. la nuit suivante : ~62 000 contacts repartent une fois (~207 lots), puis seulement ce qui change.
**Retour arrière** : retirer `APP_CONTACT_NATURE` du `.env` D'ABORD, puis coller `_INVERSE.sql`.

⚠ **Ce que ça ne fait pas** : un contact né dans l'app dans la journée n'a pas de nature avant la nuit (colonnes vides) ;
la relecture d'une fiche dans la journée renvoie la nature de la nuit précédente. L'écran (phase 3) devra lire « vide » comme
« pas encore calculé ».

---

## 10. PHASE 2 POSÉE — 01/11/2026, ~23:15 *(Frédéric : « fais-le toi-même, mais avant contrôle ton travail »)*

**Contrôles AVANT la pose** :
- chez Supabase : 2 déclencheurs et 11 fonctions lisent la table en `%rowtype` ou `to_jsonb()` — tous lisent des champs NOMMÉS
  (`col_map`, verdict de la saisie) : des colonnes en plus ne les touchent pas (`couple_json` a été ajoutée ainsi le 31/10) ;
  13 vues en dépendent, aucune ne nomme les colonnes neuves ;
- dans le code : la descente EXCLUT `app_contact_current` (`pull_from_supabase.py`) ; les autres lecteurs nomment leurs colonnes ;
  l'envoi fait un upsert qui ne réécrit que les colonnes envoyées.

**La pose** : le patch joué tel quel, avec `lock_timeout = 5s` (refus propre plutôt que bloquer l'app si la table est occupée).
Contrôle : **colonnes 6, battement 1, remplies 0, contacts 62 387, vue de l'écran 62 387**.
**Puis** `APP_CONTACT_NATURE=1` ajouté au `.env` (ligne sous `APP_COUPLE_CONJOINT`, 89 → 90 lignes, fin de ligne LF conservée).

**Après la pose** :
- push à blanc avec le vrai `.env` : **62 174 à envoyer** (l'interrupteur est bien lu) ;
- ⭐ **ENVOI RÉEL D'UN SEUL CONTACT, 10000045** (le chemin de la relecture d'une fiche) : code 0, 1 contact + 1 relation ;
  chez Supabase `civilite` **reste vide** (celle de Hektor), `civilite_app = Mme.`, `civilite_source = ancien_logiciel`,
  `nature_fiche = personne_seule`, `source_hash` **inchangé**, relation gardée, visible dans la vue de l'écran.
  → la nuit ne découvrira pas à 05:00 que Supabase refuse les colonnes : c'est prouvé ce soir.

⏰ **À VOIR LE 02/11 AU MATIN** :
- journal : `DONE  phase2 nature des fiches contact`, puis l'envoi des contacts en code 0 — ⚠ **cet envoi est BLOQUANT** dans le run ;
- sa **durée** (~62 174 lignes, ~207 lots) ;
- battement `phase2.nature_contacts` au vert ;
- chez Supabase : ~62 174 fiches avec une nature, ~14 112 « Mme. ».
**Retour arrière** : retirer `APP_CONTACT_NATURE=1` du `.env` D'ABORD, puis `_INVERSE.sql`.

---

## 11. LES 3 777 CASES VIDES « ORPHELINES » DE L'APP — CE QU'ELLES SONT *(01/11, ~23:45, question de Frédéric, lecture seule)*

Sa question : « 3 777 fiches vides avec relations mais sans notion de couple ??? ». **Mesuré sur la base locale :**
- **ce sont bien des cases de couple** : 3 765 sur 3 777 portent « Mr./Mme » ; 3 747 n'ont **aucune** coordonnée ; toutes s'affichent
  « Contact <numéro> » ;
- elles sont dans l'app **parce qu'un bien les cite** : 3 608 par une annonce active, 169 par une transaction ; rôles mandant 2 133,
  propriétaire 1 862, acquéreur 146 ;
- ⭐ **TOUTES les 3 777 ont, sur le même bien, une fiche NOMMÉE à côté d'elles** — créée **le même jour** dans 2 935 cas. Ce voisin est
  presque toujours rangé « personne seule » (3 682) ;
- **deux formes** :
  - **2 393 ont un lien de couple chez Hektor**, mais il pointe vers une fiche **qui n'existe plus** (absente de tout le registre ;
    `refCouple` brut = ce numéro, 2 393 sur 2 393). Leur voisin nommé n'a **aucun foyer** dans 2 204 cas : le couple a été **coupé
    en deux** — la case garde un lien vers une principale disparue, la vraie personne vit sur une autre fiche ;
  - **1 384 n'ont aucun lien de couple** ; leur voisin nommé est un « foyer sur lui-même » dans 1 295 cas (sans seconde fiche).
- **Conséquence directe** : ces cases sont **mandants d'un bien** → c'est exactement le cas du **défaut n° 1** (un mandant sans nom
  dans le document de mandat et une case de signature vide).
- **Cause du lien coupé** : non établie (suppression ou fusion de la principale chez Hektor ?). Les numéros visés sont ≤ 606 098 (le plus
  grand connu) mais absents.

**Proposition (rien codé)** : ne pas les **cacher** à l'aveugle, mais les **rattacher chez nous** à leur voisin nommé du même bien
(même jour de création = sûr ; autre jour = à part) : le voisin devient un couple « conjoint à compléter », la case est masquée comme
les 12 111 cases normales. Rien chez Hektor.

---

## 12. LE RATTACHEMENT DES CASES ORPHELINES — ÉCRIT, ÉPROUVÉ À BLANC, ÉTEINT *(01/11, ~00:15, « Oui rattacher »)*

**La règle** (`phase2/contacts/nature_des_fiches.py`, fonction `rattachements`) : une case « orpheline » qu'un bien cite est
rattachée à la **SEULE** fiche nommée du même bien (première de foyer ou sans foyer — jamais une seconde fiche) **née le même jour**.
La case devient sa `case_conjoint_vide`, la personne devient un `couple` (`couple_deuxieme` = `case_vide`). Le lien n'existe que
dans la table `contact_nature_current` (`rattachee_a`, `rattachement`) : **ni la couche, ni `hektor_couple_contact_id`, ni Hektor**.
Autres cas : mis de côté avec leur raison. **Interrupteur `APP_CONTACT_RATTACHEMENT` (.env), ÉTEINT** ; `--rattacher` pour un essai.

**À blanc sur les vraies données (serveur · actives · app)** :
- **7 290 cases rattachées** (6 594 actives, **3 007 dans l'app** sur les 3 777) à 7 290 personnes (3 141 dans l'app) ;
- ⭐ **contrôle de qualité : 7 286 sur 7 290 ont LE MÊME RÔLE sur le bien** que leur personne (mandant avec mandant…) ;
- mises de côté : **1 211 « plusieurs personnes nées le même jour »** (760 dans l'app — sans doute des couples dont les deux
  membres ont déjà chacun leur fiche, la case est alors en trop), 13 « personne née un autre jour », 1 « aucune personne » ;
- effets : cases orphelines dans l'app **3 777 → 770** ; couples dans l'app **4 788 → 7 875** ; cases suivant une principale
  archivée dans l'app 992 → 2 121 ;
- éteint : chiffres **identiques** à la phase 1 (rien ne change cette nuit) ; essais 20/20 (dont 3 du rattachement, témoin inverse,
  et « la couche n'est pas touchée »).

**Ce que ça pourrait casser** : rien tant qu'aucun écran ne lit la nature. Allumé : les 3 141 personnes concernées passeront
« Couple · conjoint à compléter » à l'écran (phase 3), et leurs cases seront masquées comme les autres. Le push n'envoie pas
`rattachee_a` (colonnes nommées) ; ~6 000 contacts de l'app repartiront une fois (nature ou deuxième fiche changées).
**Pour allumer** : `APP_CONTACT_RATTACHEMENT=1` dans le `.env` (geste à l'accord de Frédéric).

**✅ ALLUMÉ le 02/11 vers 00:25 (Frédéric : « Allume »)** : `APP_CONTACT_RATTACHEMENT=1` ajouté au `.env` (sous `APP_CONTACT_NATURE`,
90 → 91 lignes). Table recalculée sans option (le `.env` est bien lu) : 7 290 rattachées, 3 007 dans l'app ; push à blanc
62 174 à envoyer, 1 seul jeu de clés, `rattachee_a` NON envoyé, couples 7 875 et orphelines 770 dans les lignes envoyées.
⏰ 02/11 au matin : même ligne « rattachement : 7290 … » au journal du run.

---

## 13. PHASE 3-A — LE DÉFAUT N° 1 DU DOCUMENT DE MANDAT, CORRIGÉ *(02/11, « A » de Frédéric)* — commit local, PAS EN LIGNE

**Le défaut** (`buildMandatDocumentMandants`, `App.tsx` ~l. 4415) : la case vide d'un couple devenait un **mandant sans nom** avec sa
case de signature — comme membre d'un couple (les `members` étaient recopiés tels quels) ET comme ligne à part (les 3 777
« orphelines » du §11, à côté de leur personne sur le même bien). Dans le registre, une case vide s'appelle « Mr./Mme » (civilité
seule) ou « Contact <numéro> ».

**Le correctif** (`apps/hektor-v1/src/lib/mandantsDocument.ts`, fonctions pures) :
- `estCaseVideDeMenage` : écartée seulement si elle n'a **rien à elle** (ni prénom, ni nom, ni téléphone, ni e-mail, ni adresse) ET que
  son nom n'est qu'une civilité ou « Contact <numéro> » — un mandant venu du blob avec son seul nom (« DUPONT Paul ») est **gardé** ;
- `sansCasesVides` : si TOUS sont vides, on les garde tous (jamais un document sans mandant, règle du registre) ;
- appliqué aux lignes ET aux membres d'un couple ; un « couple » dont il ne reste qu'**une** personne réelle donne **elle seule**,
  avec son nom (plus « M. et Mme … » sur une seule ligne).

**Éprouvé** : `npm run build` vert ; 12/12 cas de forme (`Mr./Mme`, `Contact 123`, `M. et Mme`, `M_Mme`, vide → écartés ; « DUPONT
Paul », « Mme DUPONT », case avec un téléphone, vraie personne, « Metz » → gardés ; personne + case → la personne ; que des cases →
tout gardé). ⚠ **Pas vu à l'écran** : la génération d'un mandat demande une session connectée ; il sera en ligne **après le push**
(Vercel) — à regarder alors sur un bien à case vide, ordinateur et téléphone.

**Ce que ça pourrait casser** : les 30 « orphelines » qui ont une coordonnée restent des mandants (voulu, critère étroit) ; le
libellé du document (`mandatMandantsLabel`) et les destinataires de signature suivent la même liste, donc perdent aussi la case.
