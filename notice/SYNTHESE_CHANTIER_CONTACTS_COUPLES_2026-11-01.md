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

---

## 14. PHASE 3-B — LA VUE DE L'ÉCRAN : PRÉPARÉE, ÉPROUVÉE, NON POSÉE *(02/11, « Oui prépare »)*

**Mesuré avant** : `app_contacts_current` (la vue que lit l'annuaire) — 43 colonnes, `security_invoker=true`, propriétaire
`postgres`, lecture pour `authenticated` seulement (pas `anon`), **aucune vue n'en dépend**, empreinte `8004d105…`.

**Le patch** `supabase/patch_couple_phase3b_vue_contacts_2026-11-02.sql` : garde sur l'empreinte, puis `create or replace` avec
les 43 colonnes inchangées **+ 7 à la fin** (`couple_json`, `nature_fiche`, `couple_deuxieme`, `civilite_app`, `civilite_source`,
`suit_principale_archivee`, `supprimee_chez_hektor`) ; `security_invoker` redit ; droits redits. **Rien ne change à l'écran**
tant que C et D ne sont pas en ligne (le front ne demande pas ces colonnes).
**L'inverse** `_INVERSE.sql` : une vue ne perd pas de colonne par `create or replace` → `drop` + `create` à l'identique (43
colonnes), droits redits, et **il vérifie lui-même l'empreinte d'origine** (sinon tout est annulé).
**La répétition** `_REPETITION.sql` : fabriquée à partir des deux fichiers ; joue le patch PUIS l'inverse dans une transaction
annulée. **Jouée par moi : 7/7** — colonnes 50, invoker gardé, droits ok, lignes = table, témoin 10000045 (`personne_seule`,
`Mme.`) lu par la vue, retour 43, empreinte d'origine retrouvée. **Contrôle d'après : 43 colonnes, empreinte intacte, invoker.**
*(jouée avec la liste des colonnes sur une ligne : même vue, autre mise en page.)*

⛔ **ORDRE** : ce patch **AVANT** tout front qui demande ces colonnes ; l'inverse **APRÈS** avoir retiré ce front.
⏳ **À poser avec l'accord de Frédéric.** Sans risque pour l'écran actuel (colonnes ajoutées à la fin, non demandées).

## 15. LA PREMIÈRE NUIT JUGÉE, ET L'ESSAI DU 31/10 RETIRÉ *(02/11 matin, « Le run a tourné, vérifie »)*

**La nuit du 01 au 02/11 est verte** (journal `logs/scheduled/quotidien_2026-11-02_04-00-01.log`, fin 06:18:49, code 0) :
- « phase2 nature des fiches contact » : DONE en 10 s ; ligne « rattachement : 7290 case(s) rattachee(s) a 7290 personne(s), 1225 mise(s) de cote ».
- « phase2 push contacts to supabase » : DONE en **1 min 28** (06:05:20 → 06:06:48), 62 915 fiches, 35 052 relations. ⭐ La crainte d'une étape longue et bloquante est levée.
- « phase2 conjoints des couples » : DONE, 1 900 conjoints ; « secondes fiches des couples » : « rien a faire ».
- Battements `phase2.nature_contacts` et `phase2.conjoints_couples` : `success` à 06:05, sans erreur.
- Supabase, chiffres EXACTS : 7 875 couples · 14 112 `civilite_app = 'Mme.'` · 770 orphelines · **0 « Mme. » posée sur une fiche qui avait déjà une civilité Hektor** (la garde tient) · témoin 10000045 vert.
- ⚠ 213 lignes de `app_contact_current` (Supabase) sans nature : de VIEILLES lignes (rafraîchies le 23/09, 03/10, 13/10, 15/10…) que le push ne réécrit plus. Antérieures au chantier ; notées, pas touchées.
- Copie du dimanche (8c) : `hektor_20261101_080001.sqlite.gz`, 3,9 Go → 416 Mo, code 0, `gzip -t` intègre.

**L'essai du 31/10 (§20 de la note COUPLES_ERGONOMIE) est jugé vert** : le registre a adopté 20000028 ↔ 606094 et 20000029 ↔ 606095, aucun numéro neuf, 2 lignes, lien gardé ; la nuit les classe « couple » / « conjoint ».

**Retrait (accord « Oui, par l'app », après la fin de la descente 07:08)** — par le bouton « Supprimer » de la fiche, dans le Chrome de Frédéric :
- 08:46:53 (heure de Paris), **20000028** : travail `a0ab8dfe…` `done` — Hektor relu, suppression envoyée, **relue absente** ; Supabase + local + miroir nettoyés ; registre des liens : rien à effacer.
- 08:48:35, **20000029** : travail `426ab1c2…` `done` — ⭐ **606095 n'existait déjà plus chez Hektor** (`before_found: false`, suppression NON envoyée) : **la cascade du foyer est confirmée en réel**, comme les essais du 30/10 le disaient. Le ménage local et Supabase s'est fait quand même.
- ⚠ Le geste ne nettoie que la fiche visée : sans le second clic, 20000029 serait restée chez nous POUR TOUJOURS (la nuit ne relit que la liste de Hektor, et une fiche née dans l'app est protégée de la purge). **À retenir pour l'écran de suppression d'un couple.**
- Contrôle : 0 reste (Supabase, couche locale, miroir) ; témoins positifs : 9 contacts nés dans l'app ≥ 20 000 000 des deux côtés, 16 fiches voisines au miroir (606080-606110), file 0.
- Sauvegardes : dossier de travail de la session, `sauvegarde_essais_couple_20000028_29_20261102_{supabase,locale}.json`.
- Les 20000021/22 de la liste du matin étaient déjà retirées depuis le 30/10 (ligne périmée).

## 16. PHASE 3-B — LA VUE POSÉE *(02/11 ~08:55, « Oui, pose-la »)*

- Avant : empreinte `8004d105…` identique, 43 colonnes, **0 dépendant**, les 7 colonnes source présentes dans `app_contact_current`.
- Posée par moi (migration `couple_phase3b_vue_contacts_2026_11_02`, corps de `supabase/patch_couple_phase3b_vue_contacts_2026-11-02.sql`).
- Contrôle : **50 colonnes** · `security_invoker=true` gardé · anon ne lit pas, authenticated lit · **63 126 lignes vue = table** ·
  témoin 10000045 : `personne_seule` / `Mme.` / civilité Hektor vide · 7 875 couples visibles par la vue. Nouvelle empreinte `fbaec4cb…`.
- L'annuaire en ligne s'ouvre comme avant (40 268 contacts, 0 erreur console) : le front actuel ne demande pas les 7 colonnes.
- Retour arrière : `…_INVERSE.sql` (vérifie l'empreinte d'origine `8004d105…`) — ⛔ d'abord retirer du front ce qui demanderait les 7 colonnes.
- ➡ SUITE : C (annuaire) puis D (fiche), maquette du 30/10, derrière un interrupteur, ordinateur ET téléphone ;
  **la règle « Couple » = `nature_fiche` reste à confirmer par Frédéric** avant C.

## 17. LA RÈGLE « COUPLE » TRANCHÉE, ET L'AUDIT DE LA PIÈCE C (annuaire) *(02/11 ~09:05, lecture seule, rien codé)*

**✅ DÉCISION DE FRÉDÉRIC (02/11, « Oui, cette règle »)** : dans l'écran, une fiche s'affiche « Couple » **si et seulement si
`nature_fiche = 'couple'`** (la nature calculée la nuit). `couple_json` (P2) ne décide PAS : il fournit seulement le conjoint
(prénom, téléphone, numéro pour l'onglet).

**Pourquoi la règle compte — les deux calculs de la nuit ne disent pas la même chose** (couche locale, fiches envoyées) :
- **16 052 « personne seule » portent un `couple_json` à l'état « vide »** (P2 voit un ménage Hektor à case vide ; la nature, elle,
  applique la règle des couples anciens). Avec la règle : affichées en **personne seule**. 2 236 autres en « aucun », 2 en « nommé ».
- 2 114 « couple » n'ont **pas** de `couple_json` (aucun lien 245, case vide 1 869) → « Couple » sans prénom du conjoint.
- Les conjoints nommés (`couple_role = 'conjoint'`) : 1 898 ont une première « couple » ✅, **2 ont une première « personne seule »**.
- Les 3 007 cases rattachées (§12) sont `case_conjoint_vide` ; la personne qui les reçoit est « couple » mais son `couple_json`
  ne les connaît pas (`rattachee_a` n'est pas envoyé) → « Couple » sans conjoint, et la case reste une ligne vide à part.

**Ce que l'annuaire montre aujourd'hui (fiches non archivées, hors `menage_resolu` déjà masqué)** : 1 597 + 302 lignes « conjoint »
(la seconde personne d'un couple, en double de la première), et ~2 584 lignes vides `case_conjoint_vide` (1 139 sans rôle + 1 445
`menage_orphelin`), dont les cases rattachées.

**Le code (lu)** : liste `loadContactsPage` (`lib/api.ts:3503`, paginée côté serveur, colonnes `contactsListingSelect` l. 202, masque
`SANS_FICHE_DE_MENAGE` l. 200 aussi utilisé par la recherche générale l. 5440 et le choix d'un mandant l. 10385) ; rendu ordinateur
`ContactsScreen` (`App.tsx` ~46907-46944 : un téléphone, `display_name`) ; rendu téléphone `MobileContactCards` (~47147).
Interrupteur à crans existant : `app_setting` + `loadAppSettingValeur` (patron de `registre_transactions_ecran` : admin / on / caché).
Recherche : les 302 couples à conjoint prénommé portent déjà son prénom dans `search_text` (P2) ; les 1 596 « nom recopié » n'ont pas de prénom.

## 18. PIÈCE C — L'ANNUAIRE : ÉCRITE, ÉPROUVÉE, COMMITÉE (72900a1), NON POUSSÉE, INTERRUPTEUR NON POSÉ *(02/11, « Vas-y, masque aussi »)*

**Ce que fait le code** (front seul, derrière `contacts_couples_ecran` dans `app_setting`, crans admin / on / absent) :
- `lib/coupleAffichage.ts` (neuf) : `coupleAffiche(contact)` = null si `nature_fiche ≠ 'couple'` (règle du 02/11) ; sinon
  l'étiquette « Couple · Prénom1 & Prénom2 » (« Couple » seul sans prénom du conjoint, jamais d'orange dans l'annuaire) et un
  téléphone par personne avec son initiale quand le conjoint a un numéro DIFFÉRENT.
- `lib/api.ts` : `loadContactsPage({ couples })` — allumé, lit 4 colonnes de plus (`couple_json, nature_fiche, couple_deuxieme,
  civilite_app`) et masque `couple_role = 'conjoint'` + `nature_fiche = 'case_conjoint_vide'`. Éteint : la requête d'avant, à l'octet.
  La recherche générale et le choix d'un mandant NE sont PAS touchés (ils gardent chaque personne).
- `App.tsx` : lecture du cran (même patron que le registre des transactions ; `profile` et non `isAdmin`, déclaré plus bas) ;
  la liste attend le cran ; ligne ordinateur (`is-couple`, pastille, deux téléphones) et carte téléphone (pastille, téléphones).
- Styles : `annuaire-contacts-v2.css` (règles de la maquette validée, portée `.annuaire-v2`) et `mobile.css` (`.mobile-card-couple`).

**Contrôles** :
- Build vert sur une COPIE PROPRE (mes seuls morceaux), puis sur le commit exact ; l'autre session (registre 4C) modifiait en même
  temps `App.tsx` et `api.ts` : ses morceaux sont restés HORS du commit (trié morceau par morceau, 0 ligne « couple » restée dehors).
- 14/14 essais de `coupleAffiche` (esbuild + node), dont le TÉMOIN de la règle : « personne seule » avec `couple_json` vide → rien.
- Requête réelle PostgREST (lecture seule) : actifs 31 905 → **27 422, soit 4 483 masquées = 1 899 conjoints + 2 584 cases vides,
  au compte près** ; 0 conjoint et 0 case vide restants ; personnes seules 21 533/21 533, couples 4 608/4 608, sans nature 201/201
  gardés ; colonnes lues et conjoint présent. Vitesse : 4,4 ms contre 4,1 ms (même index).
- ⚠ NON VU À L'ÉCRAN : il faut le push (Vercel) puis le cran « admin ».

**⚠ À savoir avant d'allumer** :
- 1 126 des 2 584 cases vides masquées ont leur personne ARCHIVÉE : en vue « actifs », le foyer entier disparaît (la case était la
  seule trace active, sans nom ni coordonnée). Le bien, lui, garde ses mandants.
- Le total en haut de l'annuaire vient de l'instantané de la nuit : il compte encore les lignes masquées (un peu plus haut que la liste).
- Ouvrir un contact par son numéro (`loadContactById`) ne lit pas encore les colonnes du couple : c'est la pièce D (la fiche).

**Pour allumer** : 1) Frédéric pousse ; 2) avec son accord, coller/poser `supabase/patch_couple_phase3c_interrupteur_annuaire_2026-11-02.sql`
(cran « admin ») ; 3) regarder l'annuaire ordinateur ET téléphone ; 4) passer à « on ». Retour arrière : supprimer la clé.

## 19. PIÈCE C EN LIGNE, CRAN « ADMIN » POSÉ, VUE À L'ÉCRAN *(02/11 ~09:35, « Je pousse, puis pose »)*

- Frédéric a poussé (72900a1 sur origin) ; Vercel sert `index-CDT_p-W9.js`, qui contient `contacts_couples_ecran`.
- **Interrupteur posé par moi** : `app_setting.contacts_couples_ecran = 'admin'` (08:35:12 UTC), corps de
  `supabase/patch_couple_phase3c_interrupteur_annuaire_2026-11-02.sql`. Les négociateurs voient l'annuaire d'avant.
- **Vu dans le Chrome de Frédéric (admin)**, annuaire ordinateur, page 1 : 50 lignes, **7 couples** (pastille « Couple · prénoms »
  ou « Couple »), **2 à deux téléphones** (initiale devant chaque numéro), liseré décalé derrière l'avatar, **0 ligne vide** ;
  0 erreur console. Conforme à la maquette du 30/10.
- **Téléphone** : la fenêtre du Chrome du serveur refuse de rétrécir (reste à 1 280 px) → vue par un cadre de 390 px de la même app
  (même session) : rendu `MobileContactCards`, 50 cartes, 7 pastilles, 2 lignes « Y. … · S. … ». Cadre retiré, fenêtre remise.
- ⚠ Petit défaut d'aspect : sur ordinateur, la pastille est coupée par « … » quand les deux prénoms sont longs (colonne étroite) ;
  le texte entier est dans l'info-bulle. Sur téléphone, elle tient.
- ⏭ RESTE : passer le cran à « on » (accord de Frédéric) ; puis la pièce D (la fiche : étiquette, deux onglets, rôles par personne).
- ✅ **OUVERT À TOUT LE MONDE le 02/11 à 09:38** (« Oui, ouvre ») : `contacts_couples_ecran = 'on'`. Contrôle : `authenticated` a le
  droit SELECT sur les 4 colonnes neuves, dans la table ET dans la vue (pas de droit par colonne qui manquerait). Les lignes visibles
  par un négociateur restent celles de sa règle (même vue, `security_invoker`). Retour : remettre « admin », ou supprimer la clé.

## 20. AUDIT DE LA PIÈCE D — LA FICHE DU CONTACT *(02/11 ~09:50, « Oui, audite D », lecture seule, rien codé)*

**Audit limité à l'AFFICHAGE de la fiche d'un couple.** Modifier le conjoint (bloc `_m2`), « compléter le conjoint » (phase 5) et
le ménage des deux fiches à la suppression ne sont pas dans D.

**Le code (lu)** : une seule fiche, `ContactDetailPopupV2` (`App.tsx` ~45436), pour l'annuaire ordinateur, l'annuaire téléphone
(`MobileContactCards` l'ouvre aussi), la fiche ouverte depuis une annonce (`annonceContact`, chargée par `loadContactById`) et
l'acquéreur d'une transaction. En-tête l. ~46122 (`fa-cx-hero`, nom `contactFullName`, pastilles de type) ; coordonnées l. ~46175
(`fa-cx-coords` : mobile, fixe, e-mail, adresse) ; biens liés l. ~46400 (`fa-cx-lk-roles`). Les liens et recherches sont chargés
pour le SEUL numéro ouvert (`loadContactRelations` / `loadContactSearches`). `loadContactById` ne lit pas encore les colonnes du couple.

**La maquette validée (30/10)** : liseré décalé derrière l'avatar, pastille « Couple · mariés », deux onglets sous l'en-tête
(« Paul — fiche N · principal » / « Claire — fiche N ») qui pilotent les coordonnées, rôles par personne dans « Biens & mandats liés ».

**Les mesures (couples actifs du cloud)** :
- 4 608 couples : **1 898 à conjoint nommé** (sa fiche est dans le cloud, 1 898/1 898), **2 710 à case vide ou sans seconde** (→ orange
  « conjoint à compléter », sur la fiche seulement, décision du 31/10) ; 161 ont plusieurs secondes.
- Des 1 898 : **302 seulement ont un prénom** (1 596 « nom recopié ») ; **232 ont un téléphone, 268 un e-mail**.
- **Situation (mariés…) connue pour 16** → l'étiquette sera presque toujours « Couple ».
- Liens du conjoint : 1 157 en ont, mais **21 seulement ont un bien que la première n'a pas**, et **10 seulement un rôle différent**
  sur un même bien. **0 conjoint a une recherche** (toutes sont sur la première).
- On tombe sur une fiche conjoint par la recherche générale ou depuis un bien (1 157 sont liés à un bien).

## 21. PIÈCE D — LA FICHE : ÉCRITE, ÉPROUVÉE, COMMITÉE (b857001), NON POUSSÉE, INTERRUPTEUR NON POSÉ *(02/11, « Vas-y, lecture seule »)*

**Décision de Frédéric (02/11)** : le second onglet est en **LECTURE SEULE** (modifier un conjoint passe chez Hektor par la fiche
principale, bloc `_m2`, geste pas écrit chez nous).

**Le code** (derrière `contacts_couples_fiche`, crans admin / on / absent, lu une fois par chargement de page) :
- `ContactDetailPopup` aiguille désormais vers `FicheContactCouple` (V2 seulement). Il lit le couple (`loadContactCoupleInfo`, une
  ligne) puis : **fiche principale** (nature « couple ») → charge le conjoint nommé (`loadContactById`) et ses liens ; **fiche conjoint**
  (`couple_role = 'conjoint'`) → montre la **principale**, ses recherches et les liens des deux, **sur l'onglet du conjoint** ;
  sinon, lecture ratée ou interrupteur éteint → la fiche d'avant, à l'identique (elle s'affiche aussi pendant la lecture).
- `ContactDetailPopupV2` reçoit `foyer` : liseré `is-couple`, pastille « Couple » / « Couple · mariés » / « Couple · pacsés » / orange
  « Couple · conjoint à compléter », deux onglets (`fa-cx-foyer`) qui ne pilotent QUE les coordonnées (`coordPhone`, `coordEmail`…) ;
  l'e-mail du conjoint est un simple lien `mailto:` (le compositeur écrit à la principale). Boutons, recherches, activité : la principale.
  « Archiver » et « Supprimer » disent « (tout le foyer) » (la cascade de Hektor est prouvée le 02/11, §15).
- `lib/coupleAffichage.ts` : `foyerAffiche` (étiquette, situation married → mariés, civil_union → pacsés, onglets ; sans prénom → « Mme. NOM »,
  les codes Hektor « Mr./Mme » ne servent pas d'étiquette), `conjointNommeId`, `unirLiensDuFoyer` (même bien + même rôle = un seul).
- Styles : `contact-detail-v2.css` (règles de la maquette, portée `#fa-cx-root`).

**Contrôles** : build vert ; 16/16 essais du foyer + 14/14 de l'annuaire (esbuild + node), témoins « personne seule » et « nature absente »
→ rien. Sur de vraies fiches (lecture seule) : la première retrouve son conjoint (tél. compris) et le conjoint sa principale ; **1 000 conjoints
actifs lus sur 1 000 retrouvent une principale « couple »** (la lecture plafonne à 1 000). ⚠ NON VU À L'ÉCRAN : il faut le push puis le cran.

**Limites, dites** :
- le prénom n'est PAS écrit à côté d'un rôle qui diffère (les 10) : les deux rôles s'affichent côte à côte ;
- ouverte sur un conjoint, la fiche ne se rafraîchit pas après une modification de la principale (relire la fiche) ;
- ⚠ notre « Supprimer » ne nettoie toujours que la fiche visée (§15) : la seconde reste chez nous — changement du worker, À PART.

**Pour allumer** : Frédéric pousse ; avec son accord, poser `supabase/patch_couple_phase3d_interrupteur_fiche_2026-11-02.sql` (cran
« admin ») ; regarder une fiche couple nommé, une case vide, un conjoint ouvert depuis la recherche, ordinateur ET téléphone ; puis « on ».

## 22. PIÈCE D EN LIGNE, CRAN « ADMIN » POSÉ, VUE À L'ÉCRAN *(02/11 ~09:56, « Je pousse, puis pose »)*

- Frédéric a poussé (b857001 sur origin) ; Vercel sert `index-z0J1oqHw.js`, qui contient `contacts_couples_fiche`.
- **Interrupteur posé par moi** : `app_setting.contacts_couples_fiche = 'admin'` (08:56:37 UTC). Les négociateurs ont la fiche d'avant.
- **Vu dans le Chrome de Frédéric (admin)**, 0 erreur console :
  - **couple nommé** (10355551) : liseré, pastille « Couple », onglets « prénom · fiche N · principal » / « prénom · fiche N » ; le clic sur le
    second onglet remplace mobile, e-mail et adresse par ceux du conjoint ;
  - **case vide** (10077849) : pastille ORANGE « Couple · conjoint à compléter », second onglet orange « Conjoint · à compléter » ;
  - **conjoint ouvert directement** (10355552) : la fiche principale s'affiche, **sur l'onglet du conjoint**, avec ses coordonnées ;
  - menu : « Archiver ce contact (tout le foyer) », « Supprimer (tout le foyer) » (menu ouvert puis refermé, rien cliqué dedans).
- **Téléphone** (cadre de 390 px, même session) : pastille et deux onglets sur 341 px, aucun débordement horizontal. Cadre retiré.
- ⚠ **Trouvé en regardant** : la case vide prise au hasard est une **étude de notaires** (SCP) classée « couple » par la nuit — sa fiche Hektor
  est de type ménage. Ce n'est pas un défaut de l'écran : c'est la donnée de Hektor. Combien de non-personnes sont ainsi « couple » ? NON MESURÉ.
- ⏭ RESTE : passer le cran à « on » (accord de Frédéric).
- ✅ **FICHE OUVERTE À TOUT LE MONDE le 02/11 à 10:01** (« oui ouvre ») : `contacts_couples_fiche = 'on'`.

## 23. UN NOTAIRE N'EST JAMAIS UN COUPLE — AUDIT *(02/11 ~10:05, demande de Frédéric : « une fiche type notaire ne peut pas être
considérée comme couple, dans l'historique et dans les ajouts »)* — lecture seule, rien codé

**Ce qu'est « type notaire »** : à l'écran, un rôle `notaire_vendeur` / `notaire_acquereur` dans `relation_roles_json` (`estRoleNotaire`) —
calculé CHEZ SUPABASE depuis nos registres (`app_affaire_partie_calculer`) : la couche locale n'envoie pas ce rôle
(`APP_TYPE_PAR_NOS_REGISTRES=1`) et ne le porte pas (0 notaire par rôle en local). La nuit, la source locale est le registre des ventes :
`app_affaire_ledger.notaires_json` (entrée / sortie, numéros Hektor) — 1 280 notaires, dont 1 071 ont une fiche chez nous.

**Ampleur** : **50 notaires sont « couple »** (24 actifs) — mêmes 50 des deux côtés (Supabase par le rôle, local par le registre). Origine :
44 ménage Hektor à case vide, 4 aucun lien, 1 sans seconde fiche, **1 par le rattachement du 01/11** (une case orpheline rattachée à un
notaire). 39 ont un nom d'étude (SCP, SELARL…). 2 ont AUSSI un rôle de client (mandant…) : la règle de Frédéric s'applique quand même.
Les 1 021 autres notaires sont « personne seule » (règle des couples anciens) ; leurs 854 secondes fiches sont des cases vides (masquées
dans l'annuaire, sans conséquence). 0 seconde fiche de notaire n'est marquée « conjoint ». 859 notaires portent un `couple_json` (P2) —
sans effet à l'écran, la nature décide.

## 24. UN NOTAIRE N'EST JAMAIS UN COUPLE — ÉCRIT, ÉPROUVÉ, COMMITÉ (a99f113) *(02/11, « Vas-y »)*

**Écran (les ajouts, et l'immédiat)** — `lib/coupleAffichage.ts` : `estFicheNotaire` (rôle notaire_vendeur / notaire_acquereur, la règle
`estRoleNotaire` de l'écran) ; `coupleAffiche` (annuaire) et `foyerAffiche` (fiche) rendent null pour un notaire. Le rôle est calculé chez
Supabase depuis nos registres : un notaire ajouté sur une vente est couvert À LA SECONDE. ⚠ Actif seulement après le PUSH.

**Nuit (l'historique)** — `phase2/contacts/notaires_registre.py` (neuf) lit `app_affaire_ledger.notaires_json` (entrée / sortie, numéros
Hektor ; table absente = ensemble vide, la nuit continue). `nature_des_fiches.py` : une fiche notaire nommée prend la nature **« notaire »**
(jamais « couple ») ; la seconde NOMMÉE d'un notaire devient « personne_seule » (pas son conjoint) ; sa case vide reste
`case_conjoint_vide` ; le rattachement ne donne JAMAIS de case à un notaire (nouvelle raison `seule_personne_est_un_notaire`).
`conjoints_des_couples.py` (P2) saute la première fiche d'un notaire : son résumé s'efface (l'écriture remet à zéro ce qu'elle lit), sa
seconde n'est pas marquée « conjoint ». Le run lit les fichiers du disque : **effet dès la nuit du 02 au 03/11, sans push.**

**Contrôles** : essais 44/44 (contacts, dont 9 neufs : notaire en ménage, témoin inverse sans registre, notaire seul, seconde nommée, par
le numéro Hektor, rattachement refusé + témoin inverse, lecture du registre) ; front 9/9 (dont 2 témoins inverses) + 16/16 + 14/14 ; build
vert. **À blanc sur les vraies données** : 1 280 notaires → nature « notaire » (1 071 dans l'app) ; **couples de l'app 7 875 → 7 825** (−50) ;
rattachement 7 290 → 7 289 (la case donnée à un notaire part en « personne née un autre jour ») ; P2 : 995 premières de moins, conjoints 1 900
inchangés. ⏰ **03/11 matin** : au journal, « [nature] notaires du registre des ventes : 1280 » et « notaire … app 1071 » ; chez Supabase,
0 fiche au rôle notaire en nature « couple ».
- ✅ **ÉCRAN EN LIGNE le 02/11 vers 10:30** (push de Frédéric ; bundle `index-DRFjz8RH.js`). ⚠ Le premier bundle neuf (`index-0z14WgY4.js`)
  venait d'un push INTERMÉDIAIRE de l'autre session, sans a99f113 : le notaire y affichait encore « Couple ». On n'éprouve que le bundle
  qui porte le commit. Vu dans le Chrome de Frédéric : fiche du notaire 10077849 → **plus de pastille « Couple », plus d'onglets**,
  pastille « Notaire » ; témoin inverse, le couple 10355551 garde « Couple » et ses deux onglets ; annuaire segment Notaires, page 1 :
  50 notaires, **0 pastille « Couple »**.

## 25. MODIFIER LA PERSONNE 2 (LE CONJOINT) — AUDIT *(02/11 ~10:45, « Oui, audite », lecture seule, rien codé)*

**Audit limité à MODIFIER un conjoint NOMMÉ** (1 898 couples actifs). « Compléter » une case vide (2 710) est un autre geste (phase 5).

**Hektor (essais du 30/10, §10 de COUPLES_ERGONOMIE)** : le foyer s'édite d'un bloc depuis la PREMIÈRE fiche (champs `nom_m2`,
`prenom_m2`, `email_m2[]`, `telephone_m2[]`) ; E2 : modifier le conjoint dans ce formulaire → **la seconde fiche suit à l'instant** ;
ouvrir la seconde chez Hektor montre le formulaire du foyer entier. E3-bis (modifier la seconde SEULE par notre worker) : jamais essayé,
et à éviter.

**Le chemin de la modification aujourd'hui (lu)** :
- écran : `HektorContactIdentityForm` en mode modification — les champs du conjoint existent mais ne s'affichent qu'à la CRÉATION
  (`isCouplePerson = isCreateMode && …`) ; l'envoi passe par `editContactOptimistic` (`api.ts`) ;
- ⚠ en modification, `personType` est `undefined` → `hContactPayload` envoie **`person_type = 'personne_seule'` pour TOUTES les fiches** ;
- base : `app_edit_contact_optimistic` écrit À LA SECONDE les colonnes de la fiche visée (nom, prénom, e-mail, téléphones, adresse…),
  garde une photo d'avant, et pose `app_contact_pending` (envoi différé, 600 s). Les clés inconnues (dont `spouse_*`) partent telles quelles
  dans `push_fields` ; RIEN n'est écrit sur la fiche du conjoint ni dans `couple_json` ;
- worker : `handleUpdateHektorContact` → `updateHektorContactIdentity` relit le formulaire de Hektor, ne remplace QUE les champs fournis,
  **ne touche pas au statut** (seule / couple / société) ; `applyHektorContactIdentityValues` n'écrit le bloc `_m2` **que si le statut
  DÉDUIT DE L'ENVOI vaut « 2 »** (`person_type`) — donc jamais en modification aujourd'hui ;
- après l'envoi, seule la PREMIÈRE fiche est relue (`enqueueRefreshConsoleContactDataJobBestEffort(identite)`) ; la seconde attend la nuit.

**Conséquences** : (1) modifier aujourd'hui la première fiche d'un couple n'efface PAS le conjoint (le formulaire relu le garde) — sans
danger ; (2) pour modifier le conjoint, il faut que le worker sache qu'il s'agit d'un couple. ⚠ **Réserve trouvée, NON MESURÉE** : le même
`person_type = 'personne_seule'` vaut pour une **personne morale** (statut 3) modifiée dans l'app → le worker écrit `civilite / nom / prenom`
au lieu de `sociale`. Combien de sociétés ont été modifiées par l'app, et ce qu'en a fait Hektor : à mesurer à part.

**Ce que le worker sait DÉJÀ faire** : avec `person_type = 'couple'` dans l'envoi, il écrit le bloc `_m2` dans le formulaire de la première
(prouvé à la création, E1). Un **essai réel est donc possible SANS CODE** : un travail `update_hektor_contact` sur la première d'un couple
fictif, avec `person_type = couple` et un prénom de conjoint, puis relire les deux fiches chez Hektor.

## 26. ESSAI RÉEL « MODIFIER LE CONJOINT » — IL A TROUVÉ UN DÉFAUT DORMANT *(02/11 ~10:45-10:50, « Oui, essai d'abord »)*

- **Couple fictif créé PAR L'ÉCRAN** (compte formation, Propriétaire, Couple, « ESSAI MODIF Un / Deux », e-mails `@example.com`, sans
  téléphone, sans bien, e-mail RGPD DÉCOCHÉ) : travail `create_hektor_contact` `done`, **paire née d'un coup** — **20000031 ↔ 606104** (Un),
  **20000032 ↔ 606105** (Deux, `couple_role = conjoint`).
  ⚠ Trouvé en passant : le `couple_json` posé sur la première À LA CRÉATION dit `etat: aucun, conjoint: null` alors que la seconde existe
  et est marquée « conjoint » (la nuit le corrige ; à revoir dans la fonction de la paire).
- **Modification envoyée** par la fonction de l'app (`app_console_create_update_contact_job`, session de Frédéric) sur 20000031 avec
  `person_type = couple` et `spouse_first_name = DeuxModifie` → travail `9b94606f…` **en ERREUR, AVANT tout envoi** :
  « **Formulaire edition contact Hektor introuvable pour 606104** ». Rien n'a été écrit chez Hektor ni chez nous.
- **La cause** : `updateHektorContactIdentity` relit le formulaire et exige le champ `nom` dans le groupe `mefContacts/contacts_full_accueil`.
  Pour une fiche de COUPLE, ce champ n'y est pas sous ce nom (ou le groupe diffère). ⇒ **TOUTE modification d'une fiche de couple depuis
  l'app échouerait** — par le bouton « Modifier la fiche » (envoi différé) comme par un travail direct ; et le même contrôle existe pour la
  modification d'un MANDANT (`update_hektor_mandant_contact`, l. ~21086).
- **Pourquoi personne ne l'a vu** : en tout, 26 modifications de contact depuis juin (25 réussies) — **aucune sur une fiche de couple**.
  Le défaut dort ; il mordra au premier couple modifié dans l'app (14 779 couples affichables).
- (La suppression, elle, marche sur un couple : son contrôle d'existence accepte aussi `idContact` dans la page.)
- ⏭ **Pour corriger, il faut VOIR le formulaire d'un couple chez Hektor** (noms des champs du membre 1 et du membre 2) : une lecture, sur
  606104. Le Chrome de Frédéric n'est pas connecté à Hektor ; je ne me connecte pas à sa place. Le couple fictif est GARDÉ pour ça, à
  supprimer ensuite (par l'app : la cascade de Hektor emporte 606105, puis le nettoyage de 20000032).

## 27. LA CAUSE TROUVÉE ET LE GESTE PROUVÉ À LA MAIN *(02/11 ~11:05, Frédéric connecté à Hektor dans son Chrome)*

- **Lecture** du formulaire d'édition de 606104 (la même requête que le worker, `contacts-ihmChargeGroupe … consultMode=editer`) : pour un
  COUPLE, **tous les champs portent `group="mefContacts/contactCoupleAll"`** — `civilite, nom, prenom, email[], telephone[]…` ET
  `nom_m2, prenom_m2, email_m2[], telephone_m2[], adresse_m2, dateNaissance_m2, lieuNaissance_m2, commentaires_m2…` (54 champs). Les NOMS sont
  ceux qu'utilise déjà le worker ; seul le GROUPE diffère. Le worker filtre sur `mefContacts/contacts_full_accueil` → il ne trouve rien
  (« Formulaire edition contact Hektor introuvable »).
- **Écriture d'essai, UNE requête, sur la fiche fictive seulement** (dans le cadre de l'essai accepté) : exactement ce que ferait le worker
  corrigé — relire le groupe `mefContacts/contactCoupleAll`, changer `prenom_m2` (« Deux » → « DeuxModifie »), POST
  `mode=contacts-saveDataEditContact`, `group=mefContacts/contactCoupleAll`, `idContact=606104`, 57 champs → **HTTP 200**.
- **Relecture** : 606104 → `prenom_m2 = DeuxModifie`, nom, prénom et e-mails INCHANGÉS ; **606105 (la seconde) → `prenom = DeuxModifie`** :
  la seconde fiche SUIT, comme E2. ⭐ **Le geste « modifier le conjoint par la première » est prouvé avec notre forme d'envoi.**
- Onglets Hektor FERMÉS après (piste du blocage d'IP du 29/10).
- ⏭ **LE CORRECTIF** (worker, à valider) : dans `updateHektorContactIdentity` (et la sœur `update_hektor_mandant_contact`, l. ~21086),
  reconnaître le groupe du formulaire relu (`contactCoupleAll` si présent, sinon `contacts_full_accueil`), extraire ET renvoyer avec CE
  groupe ; écrire le bloc `_m2` quand le formulaire relu est celui d'un couple (et non plus selon le `person_type` envoyé). Puis l'écran
  (champs du conjoint en modification), l'écriture immédiate chez nous et la relecture de la seconde fiche. Couple fictif 20000031/32 ↔
  606104/05 GARDÉ pour l'essai réel du correctif (sa seconde porte désormais « DeuxModifie » chez Hektor ; chez nous à la relecture).

## 28. PIÈCE E — MODIFIER LE CONJOINT : ÉCRITE ET ÉPROUVÉE, RIEN N'EST POSÉ *(02/11 ~11:40, « Vas-y »)*

**Worker (748383f)** — `hektorContactFormGroup(html)` reconnaît le formulaire d'un couple (`group="mefContacts/contactCoupleAll"`) ;
`updateHektorContactIdentity` et `updateHektorMandantContact` lisent ET renvoient CE groupe (une personne seule garde exactement le chemin
d'avant) ; un couple relu est édité comme un couple (statut 2 → bloc `_m2`), quoi que dise l'envoi ; après une modification du conjoint, la
SECONDE fiche est relue (`sync_job_conjoint`, best-effort). Essai `Console/test_couple_modification.js` **12/12** (dont la preuve du défaut et
deux témoins inverses) ; l'essai voisin de la copropriété reste vert. ⚠ Actif seulement après **redémarrage des 4 services, file vide** — et
le fichier du worker porte ~130 lignes NON COMMITÉES de l'autre session, qu'un redémarrage chargerait aussi : à voir avec elle avant.

**Écran (b27653d)** — `ContactEditModalV2` reçoit `conjoint` (la seconde fiche NOMMÉE du foyer) quand l'interrupteur
**`contacts_couples_modif`** est allumé : partie « Conjoint · fiche N » (nom, prénom, portable, e-mail), pré-remplie ; **seuls les champs
CHANGÉS partent** (écrire un e-mail ou un téléphone remplace TOUTE la liste du conjoint chez Hektor) ; vider un champ n'est pas proposé.
L'envoi part avec la principale (`editContactOptimistic`, bloc `_m2`), puis `editConjointOptimistic` écrit le conjoint chez nous (un échec
y est seulement signalé en console : la relecture rattrape). Crochet d'interrupteur rendu générique (`useCranCouplesVisible`). Build vert.

**Base (non posée)** — `supabase/patch_couple_phase3e_conjoint_optimiste_2026-11-02.sql` : fonction NEUVE `app_edit_conjoint_optimistic`
(mêmes droits que la modification d'un contact) : écrit la fiche du conjoint (seconde NOMMÉE dont le lien pointe la principale,
`couple_json.etat = nomme`) et le résumé `couple_json.conjoint`. **Répétition jouée 6/6** (admin simulé, couple d'essai) : créée, conjoint
écrit, résumé écrit, principale inchangée, témoin « personne seule » refusé sans rien écrire, anon refusé — rien n'est resté. Inverse prêt.

**Dans l'ordre, chaque geste avec son accord** : (1) push ; (2) redémarrer les 4 services worker, file vide (après accord de l'autre
session sur ses lignes) ; (3) poser la fonction ; (4) interrupteur `contacts_couples_modif = admin`
(`supabase/patch_couple_phase3e_interrupteur_modif_2026-11-02.sql`) ; (5) essai réel sur le couple fictif — par l'écran dès que sa nature
est « couple » et son résumé « nommé » (la nuit du 02→03/11 : aujourd'hui il dit encore « aucun ») ; (6) supprimer le couple fictif.

## 29. PIÈCE E POSÉE, ET LE WORKER CORRIGÉ PROUVÉ EN RÉEL *(02/11 ~11:25, « oui j'ai déjà restart les worker »)*

- **Redémarrage** des 4 services par Frédéric : processus nés à **11:21:54-56**, APRÈS l'écriture du correctif (11:10:24) → actif. (Les lignes
  Youtrust non commitées de l'autre session étaient déjà chargées depuis le redémarrage de 10:27 et dorment : `signature_youtrust = off`.)
- **Posé par moi** : la fonction `app_edit_conjoint_optimistic` (migration `couple_phase3e_conjoint_optimiste_2026_11_02`) → existe,
  authenticated l'exécute, anon non ; l'interrupteur **`contacts_couples_modif = 'admin'`** (10:22:39 UTC). File : 0.
- **Essai réel du worker corrigé** (même travail que celui qui avait échoué, sur 20000031, `spouse_first_name = DeuxWorker`, SANS
  `person_type` : le worker doit déduire le couple du formulaire relu) → travail `ae3b3505…` **`done`**, `couple: true`,
  `conjoint_prenom: DeuxWorker` ; relecture de la première ET de la seconde (`sync_job_conjoint` → 20000032) ; chez nous, **20000032 porte
  « DeuxWorker »**. ⭐ La chaîne écran → base → worker → Hektor → relecture est prouvée, sauf l'écran lui-même (voir plus bas).
- Vu au passage : après la relecture, 20000032 n'est plus marqué « conjoint ». Ce n'est pas un défaut : l'étape « conjoint » de la relecture
  (`refresh_contact_inproc.py`) ne marque une seconde fiche que si la PREMIÈRE est envoyée à l'app ; le couple fictif n'a aucun bien, sa
  première n'est pas éligible. Pour un vrai couple, la marque est reposée à la seconde.
- ⏭ **RESTE** : l'essai PAR L'ÉCRAN (« Modifier la fiche » → partie Conjoint) dès que la nuit aura posé `nature = couple` et un résumé
  « nommé » sur 20000031 (03/11 matin) ; puis cran « on » (accord) ; puis supprimer le couple fictif 20000031/32 ↔ 606104/05.

## 30. L'ONGLET DU CONJOINT OUVRE « MODIFIER LE CONJOINT » ; ET « COMPLÉTER LE CONJOINT » : LES CAS *(02/11 ~11:45)*

- **Fait (6143fe0, non poussé)** : depuis l'onglet du conjoint, le crayon ouvre la fenêtre de la fiche principale titrée **« Modifier le
  conjoint »**, placée directement sur la partie « Conjoint ». Build vert.
- **Compléter le conjoint — les cas (couples actifs de l'app, notaires exclus), lecture seule** :
  · **nom recopié, sans prénom : 1 596** — la seconde fiche existe et porte le nom : **c'est DÉJÀ une modification** (pièce E) : ajouter le
    prénom par la partie Conjoint ;
  · **case vide CONNUE de Hektor comme seconde fiche : 975** (`couple_json.etat = vide`) — le formulaire de la première porte un bloc `_m2`
    vide : l'écrire DEVRAIT remplir la seconde existante (comme E2) — **NON PROUVÉ** (§8 : « seuls les essais diront ») ;
  · **case vide rattachée par NOTRE nuit : 1 066 + 462** (`etat = aucun` ou sans résumé) — chez Hektor, cette case n'est PAS la seconde de la
    première (lien absent ou cassé) : écrire le bloc `_m2` risquerait de CRÉER une nouvelle fiche à côté de la case → **à ne pas faire sans essai** ;
  · **couple sans seconde fiche : 60**, **couple sans lien chez Hektor : 123** — le second cas n'est probablement pas un couple chez Hektor
    (« Transformer en couple » a fait disparaître une fiche à l'essai E6) → hors de portée pour l'instant.

## 31. ESSAI « COMPLÉTER LE CONJOINT » *(02/11 ~11:55, « Oui, essai », Frédéric connecté à Hektor ; fiches fictives seulement)*

- **Vider** le conjoint de 606104 (POST groupe `contactCoupleAll` : `nom_m2`, `prenom_m2`, `email_m2[]` vides) → 200 ; Hektor vide le prénom et
  l'e-mail **mais REFUSE un nom vide : il recopie le nom de la première dans `nom_m2`**. La seconde (606105) suit : nom gardé, plus de prénom ni
  d'e-mail. ⭐ **C'est l'origine des 1 596 « nom recopié, sans prénom »** : Hektor fabrique ce nom quand le conjoint n'en a pas.
- **Compléter** (`prenom_m2 = DeuxComplete` + e-mail) → 200 ; **la seconde porte « DeuxComplete » et son e-mail.** ⇒ compléter un « nom recopié »
  = la modification de la pièce E, prouvée.
- **Vraie case vide** (lecture seule d'un vrai couple, `couple_json.etat = vide`, oui/non seulement) : la première a le formulaire de COUPLE avec
  `nom_m2` / `prenom_m2` / `email_m2` VIDES, la seconde est entièrement vide. Ce cas ne peut pas être fabriqué sur une fiche fictive (Hektor
  recopie le nom) : écrire la partie membre 2 DEVRAIT remplir la seconde existante (même mécanisme que ci-dessus), **NON PROUVÉ sur ce cas exact**.
- Onglets Hektor fermés. Couple fictif : la seconde porte « DeuxComplete » chez Hektor.
- ⏭ **PROPOSITION** : un bouton « Compléter le conjoint » sur l'onglet orange, **seulement quand Hektor connaît la case comme seconde fiche**
  (`couple_json.etat = vide`, 975 couples actifs) ; même fenêtre, partie Conjoint vide (nom obligatoire) ; la fonction
  `app_edit_conjoint_optimistic` à élargir à l'état « vide » ; **premier usage réel surveillé** (contrôle au retour : la seconde doit se remplir,
  aucune fiche ne doit naître). Les 1 528 cases rattachées par notre nuit et les 183 couples sans seconde / sans lien : PAS de bouton.

## 32. COMPLÉTER POUR TOUS — CE QUE HEKTOR A VRAIMENT *(02/11 ~12:05, « Oui, audite », lecture seule de 12 formulaires, oui/non seulement)*

- **Cas 3, couple sans seconde fiche (60)** — 3 lus : formulaire de COUPLE ; **1 sur 3 a DÉJÀ la place 2 remplie chez Hektor** (nom ET prénom
  du conjoint) alors que notre app dit « à compléter » : nous ne lisons pas la place 2 du formulaire, seulement les secondes fiches. Les 2 autres :
  place 2 vide → la remplir par le bloc `_m2` (même geste que la pièce E ; création éventuelle de la seconde par Hektor à vérifier au 1er usage).
- **Cas 4, couple sans lien (123)** — 3 lus : **ce sont des PERSONNES SEULES chez Hektor** (formulaire `contacts_full_accueil`, pas de place 2) ;
  notre nuit les dit « couple » par un SIGNE (civilité « Mr./Mme », « et » dans le prénom…) : un couple tenu sur UNE fiche. Pour leur donner
  un conjoint chez Hektor, il faut le geste « Transformer en couple ».
- **Cas 5, cases rattachées par notre nuit (1 528)** — 3 lus : **la case est une COQUILLE DE COUPLE entièrement vide** (formulaire de couple,
  places 1 ET 2 vides) ; **la personne du bien est une PERSONNE SEULE** chez Hektor. Deux fiches séparées, aucun lien.
- ⇒ **Les cas 4 et 5 passent tous deux par « Transformer en couple »** (personne seule → couple) : avec « contact déjà existant : Oui » pour
  rattacher une fiche existante, ou « Non » pour saisir le conjoint. C'est le parcours de l'essai E6 (30/10) qui, avec « Non », a fini sur une
  page blanche et une fiche DISPARUE. ⏭ À ÉPROUVER sur fiches FICTIVES, pas à pas, en relevant chaque requête, AVANT toute décision.
- Cas 5, choix à faire par Frédéric ensuite : (a) remplir la coquille vide avec le conjoint (simple, deux fiches restent séparées chez Hektor),
  (b) transformer la personne en couple et retirer la coquille (propre, dépend de l'essai).

## 33. LE RATTACHEMENT NE FABRIQUE PLUS DE COUPLE *(02/11 ~12:20, « VAS Y sauf les 123 »)*

- **Le constat de Frédéric** (exemple réel : bien EA32621, coquille 10260585 / Hektor 467325 et personne 10260586 / Hektor 467326, nées le
  22/12/2025, numéros Hektor consécutifs) : la personne est une PERSONNE SEULE chez Hektor ; l'app la montrait « Couple · conjoint à compléter ».
  Mesure : **1 530 fiches actives de l'app** dans ce cas, **1 529 avec exactement UNE coquille sur le MÊME bien** (1 529/1 529), 1 sans coquille.
- **Mon erreur du 01/11** : le rattachement faisait DEUX choses — masquer la coquille (utile) ET passer la personne en « couple » (une
  déduction que Hektor ne confirme pas).
- **Corrigé (nature_des_fiches.py)** : la personne reste ce que dit Hektor ; le rattachement ne sert plus qu'à masquer la coquille
  (`case_conjoint_vide`). Les couples écrits dans le nom (« M. et Mme … », « Paul et Anne » — les 123 « sans lien ») restent « couple » (décision).
  Essais 45/45 (dont un neuf avec témoin inverse). **À blanc** : couples de l'app 7 825 → **4 739** (−3 086, archivés compris ; ~1 530 actifs),
  coquilles toujours masquées (case_conjoint_vide app 15 117), orphelines 771. **Effet à la nuit du 02→03/11, sans push.**
- Créer un vrai couple depuis l'app, ou relier la coquille : question pour plus tard (essai « Transformer en couple » sur fiches fictives).

## 34. PIÈCE F — « COMPLÉTER LE CONJOINT » : ÉCRITE (21732cc), FONCTION NON POSÉE *(02/11 ~12:45, « J'AI PUSH CONTINU »)*

- Push de Frédéric vérifié : 6143fe0 en ligne (`index-BS0FFFGr.js`, « Modifier le conjoint » depuis l'onglet).
- **Écran** : sous les onglets d'un couple dont la seconde fiche est VIDE et CONNUE de Hektor comme place 2 (`couple_json.etat = vide`,
  **994** couples actifs), un bouton **« + Compléter le conjoint »** (admins, interrupteur `contacts_couples_modif`, droit de gérer les
  contacts) ouvre la fenêtre de la principale titrée « Compléter le conjoint », partie « Conjoint à compléter » VIDE, **nom obligatoire**.
  Envoi : comme la modification (place 2, bloc `_m2`, worker 748383f déjà actif). `lib/coupleAffichage.ts` : `conjointVideId` (7/7).
  **Pas de bouton** pour les cases rattachées par notre nuit (coquilles séparées chez Hektor) ni pour les couples sans seconde fiche.
- **Base (NON posée)** : `supabase/patch_couple_phase3f_completer_conjoint_2026-11-02.sql` remplace `app_edit_conjoint_optimistic` (garde
  sur l'empreinte posée 77bcfa92…) : accepte l'état « vide » ; écrit la fiche vide SI elle est chez nous (**469 sur 994** seulement) et
  TOUJOURS le résumé, qui passe à « nommé » ; « nommé » inchangé. **Répétition 5/5** (case vide avec fiche, sans fiche, témoin « nommé
  absent » refusé, anon refusé ; nouvelle empreinte 43faf014…) — rien n'est resté. Inverse prêt (remet 77bcfa92…).
- **Premier usage réel À SURVEILLER** : remplir la place 2 d'une VRAIE case vide n'a jamais été prouvé sur ce cas exact (Hektor recopie le
  nom quand on vide, on ne peut pas fabriquer une vraie case vide) — vérifier ensuite que la seconde fiche se remplit et qu'AUCUNE fiche ne naît.
- ⏭ Push du front ; pose de la fonction (accord) ; premier usage surveillé.
- ✅ **FONCTION POSÉE le 02/11 ~12:55** (migration `couple_phase3f_completer_conjoint_2026_11_02`, garde 77bcfa92… passée) : authenticated
  l'exécute, anon non. ⚠ Empreinte posée **e5ac0baa…** (la répétition donnait 43faf014… : même logique, lignes vides en plus dans le texte
  posé) → le retour arrière a été corrigé pour vérifier **e5ac0baa…**. ⏰ Push du front (21732cc) pas encore arrivé à 12:55 ; la fonction
  élargie est compatible avec l'écran en ligne (elle ne fait qu'accepter un état de plus).
- ✅ **FRONT EN LIGNE ~13:05** (push de Frédéric ; `index-D4l9iPnf.js`). **Vu dans son Chrome (admin)** sur un vrai couple à case vide connue
  (10213513) : pastille orange « Couple · conjoint à compléter », onglet orange désactivé, bouton **« + Compléter le conjoint »** ; au clic, la
  fenêtre « Compléter le conjoint », partie « Conjoint à compléter · fiche 10213512 » (la case vide), 4 champs vides, placée sur la partie ;
  **fermée SANS enregistrer** (0 travail créé, 0 en attente).
- ⭐ **Vu sur ce vrai cas** : le prénom de la place 1 est « X et Y » — les DEUX personnes sont écrites sur la place 1, la place 2 est vide.
  Bien compléter = corriger AUSSI le prénom de la place 1 (même fenêtre, partie Identité) : à dire aux utilisateurs.
- ⏭ RESTE : premier usage réel surveillé (la seconde se remplit, aucune fiche ne naît) ; cran « on » de `contacts_couples_modif` (accord) ;
  essai par l'écran de « Modifier le conjoint » sur le couple fictif (03/11, après la nuit) puis suppression du couple fictif.

## 35. LE RESTE, FAIT *(02/11 ~13:00-13:50, « vas y fais le reste »)*

- **Couple fictif préparé sans attendre la nuit** : `nature_des_fiches.py` (table locale entière, comme la nuit — elle porte déjà les
  correctifs notaires et rattachement), `conjoints_des_couples.py --contact-id 20000031`, push des 2 contacts → 20000031 « couple », résumé « nommé ».
- **Essai PAR L'ÉCRAN (Chrome de Frédéric)** : fiche 20000031 → onglet du conjoint → crayon → fenêtre « **Modifier le conjoint** », partie
  « Conjoint · fiche 20000032 » pré-remplie → prénom « DeuxEcran » → Enregistrer. **À la seconde** : 20000032 et le résumé portent « DeuxEcran »
  (`app_edit_conjoint_optimistic`) ; `app_contact_pending` posé (envoi différé 10 min, `spouse_first_name` dans les champs).
  **12:44 UTC** : travail `update_hektor_contact` `done`, `couple: true`, « DeuxEcran » envoyé par la place 2 ; attente vidée. **Relecture chez
  Hektor de 20000032 (12:46:18) → « DeuxEcran »** : Hektor l'a. ⭐ **La chaîne ENTIÈRE est prouvée par l'écran.**
  ⚠ La relecture automatique de la SECONDE fiche ne s'est pas déclenchée : le worker la cherche par `couple_role = conjoint`, absent sur ce couple
  fictif (première non éligible). Pour une case VIDE complétée (rôle `menage_resolu`), même chose : la seconde attendra la nuit (le résumé, lui,
  est écrit à la seconde). Amélioration possible : chercher par `couple_json.conjoint.id` (worker → redémarrage). Non fait.
- **Couple fictif SUPPRIMÉ par l'app** : 20000031 « Supprimer (tout le foyer) » → `done`, Hektor supprime ; 20000032 → « n'existe déjà plus chez
  Hektor » (**cascade confirmée une 2e fois**), ménage fait. **0 reste** Supabase, couche locale, miroir. Sauvegarde : dossier de travail,
  `sauvegarde_essai_modif_20000031_32_20261102.json`. File : 0.
- **Ouvert à tout le monde** : `contacts_couples_modif = 'on'` (12:49:57 UTC). Les trois crans des couples sont sur « on » (annuaire, fiche, modif).
- ⚠ **Réserve, NON MESURÉE, antérieure à ce chantier** : toute modification de contact par l'app envoie `send_rgpd_email: true` →
  `_email_rgpd=1` ajouté au formulaire (`applyHektorContactIdentityValues`), et `contact_kind: acquereur` par défaut. Le formulaire d'ÉDITION d'un
  couple chez Hektor (54 champs lus le 02/11) ne contient PAS `_email_rgpd` : probablement ignoré en modification — à vérifier un jour.
- ⏭ Premier « Compléter le conjoint » réel : à SURVEILLER (la seconde se remplit, aucune fiche ne naît).

## 36. ESSAI « TRANSFORMER EN COUPLE » — LE GESTE PROPRE EST TROUVÉ *(02/11 ~14:10, « Transformer en couple » ; fiches fictives seulement)*

- **Fiches fictives créées par la fonction de l'app** : ESSAI TRANSFO Un (20000033 ↔ 606117), Deux (20000034 ↔ 606118), Trois (20000035 ↔ 606119),
  personnes seules, compte formation, `@example.com`, sans bien, sans e-mail RGPD. Frédéric connecté à Hektor ; requêtes relevées dans la page.
- **Essai « Oui » (rattacher une fiche existante)** sur Un, choix de Deux : la recherche est `mode=contacts-actions-searchContactToCouple`
  (lecture, `valeur`, `idProspect`) ; « Confirmer » envoie **UNE requête GET `mode=contacts-create-transformeContactToConjunct`, `conjoint=606118`,
  `refCouple=606117` → `{"success":"ok"}`** ; puis Hektor OUVRE un formulaire « Ajouter un nouveau contact » (`contacts-create-creationContact`,
  idContact=606117) en Couple, pré-rempli — **NON ENREGISTRÉ**. Relecture : **Un est un COUPLE (formulaire contactCoupleAll), place 2 = Deux**
  (nom, prénom, e-mail) ; **Deux est devenue sa seconde fiche** ; Trois intacte (témoin). ⭐ **La transformation est FAITE par la seule requête GET** ;
  le formulaire qui suit est facultatif — c'est très probablement son enregistrement qui a fait disparaître une fiche le 30/10 (E6).
- **Essai « Non »** sur Trois : aucune écriture ; Hektor ouvre `contacts-create-creationContact` (idContact=606119, step=1, statut=2) en Couple avec
  **une COPIE de Trois en place 2** (le piège d'E6). **Non enregistré** ; Trois relue intacte (personne seule).
- **Nettoyage par la fonction de suppression de l'app** : Un → `done` ; **Deux → « n'existe déjà plus chez Hektor »** (la cascade emporte la seconde :
  3e confirmation, et preuve que le lien posé par la transformation est réel) ; Trois → `done`. 0 reste (Supabase, local, miroir). Onglets Hektor fermés.
- ⭐ **CE QUE ÇA OUVRE** : « ajouter un conjoint à une personne seule » = deux gestes PROUVÉS : (1) créer le conjoint comme un nouveau contact
  (création de l'app) ; (2) le rattacher par `transformeContactToConjunct` (conjoint = le nouveau, refCouple = la personne). Le chemin « Non » de
  Hektor n'est jamais utilisé. Vaut pour les **123** « couples sans lien » (personnes seules chez Hektor) et pour toute personne seule.
- **Cas 5 (coquilles, 1 529)** : rattacher la coquille (fiche de couple VIDE) comme conjoint par la même requête n'est PAS prouvé (impossible de
  fabriquer une coquille fictive : Hektor recopie le nom). Choix à faire par Frédéric : laisser la coquille masquée et utiliser « Ajouter un
  conjoint » sur la personne (puis supprimer la coquille ?), ou essayer le rattachement de la coquille sur un premier vrai cas, surveillé.


## 37. COQUILLES : « LE PLUS PROPRE », PREMIER CAS RÉEL PRÉPARÉ, ESSAI REPORTÉ *(02/11 après-midi, « Le plus propre », « Oui, sur EA32621 »)*

- **Choix de Frédéric** : rattacher la coquille ELLE-MÊME comme conjoint (`transformeContactToConjunct`), sur un premier vrai cas, surveillé.
- **Mesure (lecture seule, couche locale)** : 4 419 coquilles rattachées dont les deux fiches sont actives ; **1 453 dans l'app** (les deux
  éligibles), dont 1 409 avec une personne seule, 461 coquilles portant elles-mêmes un « ménage orphelin ». **680 cas simples** : personne seule,
  coquille sans seconde à elle, les deux liées au MÊME bien et à aucun autre. ⭐ **La coquille porte elle-même la relation au bien**
  (propriétaire 897, mandant 3 286…) : la rattacher garde les deux liens dans le foyer.
- **Premier cas retenu** : EA32621 (bien 59545), coquille 10260585 / Hektor 467325, personne 10260586 / Hektor 467326, toutes deux propriétaires.
- **Essai prévu** : photo d'avant (deux formulaires, liens du bien) → Hektor propose-t-il la coquille dans « Transformer en couple » (lecture) →
  « Confirmer » (UNE écriture), formulaire suivant NON enregistré → relecture (couple, place 2 = coquille, liens intacts, aucune fiche née).
  Risques dits : refus possible (la coquille est une fiche de couple), pas de geste « défaire » connu (pire cas = couple à place 2 vide, déjà géré
  par « Compléter le conjoint »), nom recopié possible, cascade à la suppression.
- **Reporté** : Hektor en MAINTENANCE (mise à jour, dit par Frédéric) — les onglets renvoyaient vers `www.la-boite-immo.com`, lectures en 404.
  **Rien lu, rien écrit.** Onglets fermés. À reprendre quand Hektor revient, depuis la photo d'avant.

## 38. REPRISE APRÈS LA MAINTENANCE : PHOTO D'AVANT FAITE, ARRÊT SUR UN 503 *(02/11 soir, « C'est fait »)*

- **Hektor revenu** : depuis le serveur, `/admin/` répond 200 en 0,15 s ; IP non bloquée. La mise à jour a fermé la session de Frédéric ;
  après reconnexion, l'accueil est une liste « Mon réseau » (19 agences, dont « COMPTE FORMATION », bouton « Accéder à Hektor ») — dans le
  compte formation, la fiche 467326 répond **403 « Accès interdit »** ; dans « GROUPE GTI IMMOBILIER · Administrateur », elle s'ouvre.
- ⚠ **Mes fausses pistes** (sans écriture) : 4 lectures parties sur `ma-boite-immo.com` (adresse relative, l'onglet avait changé de site) ;
  puis des réponses VIDES (200, 0 octet) avec `group=mefContacts/contactCoupleAll` seul — **ce n'est pas Hektor** : la lecture du worker
  (`console_job_worker.js:18260`) passe `group=contacts,pilotage_accueil_contact,mefContacts/accueilContact`, et avec elle tout répond.
- **Photo d'avant (lecture)** : 467326 = personne seule (`contacts_full_accueil`), nom, prénom, e-mail, téléphone remplis, civilité vide,
  propriétaire actuel d'EA32621 (Estimation). 467325 = **fiche de COUPLE vide** (civilité « M./Mme », places 1 et 2 sans nom, prénom,
  e-mail ni téléphone) — conforme au risque déjà dit au §37.
- **Arrêt** : la recherche « Transformer en couple » (`contacts-actions-searchContactToCouple`, `valeur=467325`, `idProspect=467326`)
  a répondu **503** → arrêt net, aucune autre requête, onglet Hektor fermé. ⚠ La recherche se fait par TEXTE (nom) : une coquille sans
  nom ne peut sans doute pas y être trouvée, donc « Hektor la propose-t-il ? » ne se vérifie pas par l'écran.
- **Rien n'a été écrit.** L'unique écriture accordée (`transformeContactToConjunct`, conjoint=467325, refCouple=467326) reste à faire.
- **Deuxième essai, même soir** (« Le service fonctionne, peux-tu tester ? ») : compte GROUPE GTI IMMOBILIER vérifié ; les deux
  lectures de contrôle répondent **200** et la photo est INCHANGÉE (467326 seule, nom et prénom remplis ; 467325 « M./Mme », vide).
  La recherche `searchContactToCouple` répond de nouveau **503** (page « maintenance downtime or capacity problems »), alors que la
  lecture des fiches marche : c'est CETTE action qui ne répond pas, pas tout Hektor. Arrêt net, onglet fermé, **rien écrit**.
  Le code déjà chargé par la fiche ne contient pas cette action (elle vient d'un autre script) : on ne peut pas dire si la mise
  à jour l'a renommée. ⚠ Tant qu'elle répond 503, ne pas lancer `transformeContactToConjunct` : même famille d'actions, risque
  d'écriture à moitié sans confirmation.
- ⛔ **CORRECTION, MÊME SOIR : LE 503 ÉTAIT MA FAUTE, PAS HEKTOR** (Frédéric : « ce n'est sûrement pas lié, vérifie »). Le code de la
  page (`searchContactByTerms`, chargée avec la fenêtre `popins-popinAgTransformationCouple`) envoie la recherche en **POST**
  (`mode`, `valeur`, `idProspect` dans le corps, 3 caractères minimum) ; je l'envoyais en **GET** → Hektor répond 503 « maintenance »
  à une requête mal formée. Rejouée en POST : `valeur=ESSAI` → **200, 14 résultats** ; `valeur=467325` → **200, 0 résultat**.
  ⭐ Confirmé : **la coquille ne peut PAS être proposée par l'écran** (pas de nom, et la recherche ne prend pas le numéro) — le
  rattachement d'une coquille n'est faisable QUE par la requête directe. L'écriture, elle, n'a pas changé avec la mise à jour :
  `transforme()` envoie toujours **GET** `contacts-create-transformeContactToConjunct` (`conjoint`, `refCouple`).
  ⚠ Leçon : un 503 « maintenance » de Hektor peut répondre à une requête MAL FORMÉE ; relire la méthode du vrai bouton avant
  d'accuser le service. Rien écrit, onglet fermé.

## 39. ⭐ COQUILLE RATTACHÉE PAR HEKTOR : LE GESTE MARCHE SUR UN VRAI CAS *(02/11, 23:47, « Vas-y » ; EA32621)*

- **Photo d'avant (23:46, compte GROUPE GTI IMMOBILIER)** : 467326 = personne seule (civilité « Non défini », 37 champs, nom/prénom/
  téléphone/e-mail remplis, page liée à EA32621 / bien 59545) ; 467325 = fiche de couple « M./Mme » VIDE (60 champs, `nom_m2` vide).
- **UNE écriture** : GET `contacts-create-transformeContactToConjunct&conjoint=467325&refCouple=467326` → **200, réponse VIDE**
  (sur les fictives du §36 : `{"success":"ok"}`). Non renvoyée ; aucun formulaire ouvert, donc rien à « ne pas enregistrer ».
- **Relecture (formulaire)** : 467326 est devenue un **COUPLE** (« M./Mme », formulaire de couple, 60 champs) ; sa personne en place 1
  est INTACTE (nom, prénom, téléphone, e-mail) ; place 2 vide — normal, la coquille n'a pas de nom. 467325 inchangée.
- ⭐ **Preuve du lien par l'API officielle** (`sonde_paire_de_menage.py 467326 467325`, `ContactById`, lecture) : **467326 refCouple
  = 467326 (porteuse), 467325 refCouple = 467326**. C'est la forme normale d'un ménage Hektor.
- **Liens au bien** : les pages des DEUX fiches montrent toujours EA32621 (`openPropertyDrawerDetails(59545)`) → les deux propriétaires
  restent dans le foyer. ⚠ Une page lue trop tôt ne montrait pas le bien (chargement différé) : attendre ~5 s avant de conclure.
- ⭐ **CE QUE ÇA PROUVE** : rattacher une coquille vide comme conjoint **est accepté** par Hektor, en une requête, sans fiche née, liens
  gardés. Le chemin vaut pour les **680 cas simples** du §37 — rien n'est décidé pour eux (taille, ordre, écran : à Frédéric).
  ⚠ La réponse vide ne peut pas servir de confirmation : un futur geste automatique devra RELIRE `refCouple` pour savoir si c'est fait.
- ⏰ **À vérifier le 03/11 après la nuit** : notre couche doit voir 467326 en COUPLE, conjoint = 467325 (état « vide » → bouton
  « Compléter le conjoint »), et la coquille ne doit plus apparaître comme une fiche à part dans l'annuaire.

## 40. ⛔ LA NUIT N'A PAS VU LE RATTACHEMENT : LE LISTING DES CONTACTS SUIT UNE AUTRE DATE *(03/11 matin, « Le run a dû finir, vérifie »)*

- **Le run** : fini à 06:18:23, code 0. Étapes couples vertes (« conjoints » : 1 902 conjoints nommés envoyés) ; notaires du registre
  des ventes **1 280** (« jamais couple ») et chez Supabase **1 071 notaires, AUCUN avec un couple** → le contrôle du §24 est ✅.
  Hors chantier : Matterport en échec 2/2 cette nuit (**401 « unauthorized »** de leur API ; il passait le 02/11), non bloquant.
- ⛔ **EA32621 n'est PAS à jour chez nous** : Supabase montre encore 10260586 en `personne_seule` (`couple_json.etat = aucun`) et
  10260585 sans lien de couple. Le miroir local (`data/hektor.sqlite`) porte toujours `date_maj = 2025-12-22` pour les deux.
- **Chez Hektor, tout y est** (`ContactById`, lecture, 2 requêtes) : refCouple 467326 / 467326, et la `datemaj` a BIEN bougé —
  **467326 : 2026-11-02 23:47:29, 467325 : 2026-11-02 23:48:01**.
- ⭐ **LA CAUSE (code, `sync_raw.py`, `sync_contact_listing_variant`)** : la nuit lit `ListContacts` trié par **`dateLastTraitement`
  DESC** et s'arrête à la première page entièrement sous le curseur. Les 3 pages lues à 03:51 vont de 29/10 à 02/11 18:52:57 et
  **ne contiennent pas 467326** alors que sa `datemaj` (23:47) est plus récente que tout ce qu'elles portent → le rattachement
  **change `datemaj` mais PAS `dateLastTraitement`**. La fiche ne remonte jamais en tête du tri : la nuit ne la relira pas, ni
  ce soir ni plus tard. Même famille que le mandat saisi après coup (mémoire « le run de nuit ne relit le détail que si… »).
- ⚠ **CE QUE ÇA CHANGE POUR LES 680** : un rattachement fait chez Hektor n'arrive chez nous que si on RELIT les deux fiches
  nous-mêmes. Un futur geste devra donc relire `ContactById` des DEUX fiches (porteuse ET coquille) puis recalculer le couple —
  c'est ce que fait déjà `phase2/sync/refresh_contact_inproc.py` (détail → normalisation → couche → conjoint → push), fiche par
  fiche. ⚠ Et un couple créé par un négociateur DIRECTEMENT dans Hektor est sans doute invisible de la même façon (non mesuré).
- **Pour réparer EA32621** (écriture chez nous, en attente d'accord) : `refresh_contact_inproc.py --contact-id 10260585`, PUIS
  `--contact-id 10260586` (la coquille d'abord, pour que la porteuse trouve sa place 2). Rien chez Hektor : 2 lectures `ContactById`.
  Le miroir local étant réparé, la nuit suivante recalculera aussi la nature des deux fiches.

## 41. FAUT-IL CORRIGER LA RÈGLE DU BALAYAGE ? MESURES ET OPTIONS *(03/11 matin, « Mais il faut corriger la règle du balayage ??? »)*

- **Essai du tri** (9 lectures `ListContacts`, page 1, actifs) : `sort=datemaj`, `dateMaj`, `date_maj`, `dateModification` rendent
  TOUS la même page que `sort=id DESC` → **Hektor ne sait pas trier par date de modification** (nom inconnu = repli sur le numéro).
  `dateLastTraitement ASC` rend un ordre différent de `id ASC` → ce tri-là est bien appliqué.
- **Les 60 fiches lues cette nuit** (pages 1 à 3) sont exactement les 60 numéros les plus récents (606139 → 606067, créées du 29/10
  au 02/11) : une création compte comme « traitement ». Depuis le 20/10, la liste « actifs » a quand même vu 31 fiches anciennes
  (n° 12787 à 604536) : certains gestes Hektor remontent bien une fiche, le rattachement de couple non.
- **Ampleur, sur un échantillon** : 32 fiches anciennes (n° < 600000) ont une `datemaj` ≥ 20/10 connue par une relecture de fiche ;
  9 seulement portent la même date dans le suivi de la liste. ⚠ Échantillon biaisé (fiches qu'on a ouvertes), pas un taux.
- **Options présentées, rien décidé** :
  A. règle pour nos propres gestes : tout geste couple (les 680) relit lui-même les DEUX fiches (`refresh_contact_inproc.py`) —
     aucun changement à la nuit ; ne couvre pas un couple fait directement dans Hektor ;
  B. relecture tournante la nuit : N `ContactById` par nuit (les plus anciennement relus d'abord, périmètre à choisir) — coûte
     N requêtes sur le quota (nuit ≈ 4 500, règle des 40 %) et allonge le push ;
  C. chercher dans l'API une autre porte (liste filtrée par date de modification) — non mesuré.
- **C explorée (03/11)** : la documentation API v2 (`notice/Hektor API v2 - Documentation…md`, « Listing Contacts ») et la collection
  Postman ne donnent pour `ListContacts` que `agence, archive, page, type, sort, way, version` — **aucun filtre de date**, et le tri
  par date de modification n'existe pas (essai ci-dessus). Le « datemaj » de la console (`labs_contactsRefonte.js` l. 1632) est le
  calendrier du formulaire d'ÉDITION, pas un filtre de liste. → **Par l'API, C est une impasse** ; seul Hektor peut l'ouvrir.
- ⭐ **Ce qui existe déjà** : la tâche des recherches actives (03:00, `sync_active_searches.py`) relit CHAQUE NUIT `ContactById` de
  ~4 000 acquéreurs (variante `targeted`, 4 012 fiches vues le 03/11). Une relecture tournante (B) existe donc déjà pour eux.
  Les propriétaires / mandants n'en font pas partie : 467326 est lié à l'annonce 59545 (active), 131 seulement des 41 847 contacts
  liés à une annonce non archivée ont été relus cette nuit. Taille d'un périmètre « biens en vente » : non mesurée.
- **Lire toute la liste (mesure 03/11)** : actifs 170 040 contacts (metadata Hektor) = ~8 500 pages ; archivés ~9 200 pages ;
  ~17 700 pages en tout. Dernière lecture complète le 23/06 : 8 429 + 8 931 pages en ~33 min, EN PARALLÈLE
  (`refetch_contacts_listing_parallel.py`), avant la mesure du quota (20/08). Aujourd'hui, au rythme de 1 page/s : ~4 h 50
  sans les pauses ; et 17 700 requêtes dépassent à elles seules le quota (13 000 à 17 000 par période). Pas faisable en une nuit.
- 💡 **Idée B' (non décidée)** : une relecture tournante de la LISTE plutôt que des fiches — triée par numéro (ordre stable), N pages
  par nuit. Une page = 20 contacts avec leur `datemaj` ET leur `refCouple` : 20 fois moins cher que `ContactById`. Exemple :
  1 000 pages/nuit (~17 min, 1 000 requêtes) = 20 000 contacts vérifiés, tous les actifs en ~9 nuits ; seules les fiches dont la
  `datemaj` a bougé sont ensuite relues en détail.
- ⚠ **Nuance (Frédéric, 03/11 : « on n'est pas sûr pour le nombre de requêtes »)** : le « quota de volume » n'est qu'une
  ESTIMATION (mémoire du 20/08, 2 blocages à ~13 600 et ~16 700 requêtes, un 3e à 3 450). Les 4 bannissements connus ont eu
  4 déclencheurs : rattrapage documents (débit 1,5 req/s pendant 4 h + 1 300 refus 403 répétés, 19-20/08), mes sondes à
  4 req/s (26/08), 17 connexions en 22 s (17/09), relectures d'objets supprimés en rafale (18/09). ⭐ Contre-témoin : la lecture
  complète du 23/06 (17 360 pages en ~33 min, ~9 req/s) n'a PAS été bannie. Ce qui est sûr : tenir 1 req/s, éviter les longues
  expositions sans pause, ne jamais rejouer des refus, ne jamais multiplier les connexions.
- **Le temps des fiches relues ensuite (Frédéric : « il faut ajouter le traitement des fiches détail »)** — mesures du 03/11 :
  · rythme RÉEL d'une relecture de fiche, traitement compris : la tâche des recherches a relu **4 018 contacts en 6 669 s**
    (02:00 → 03:51) = **1,66 s par fiche** ;
  · combien de vieilles fiches changent : sur 3 701 fiches anciennes relues depuis le 02/11, **1 modifiée en 7 jours, 33 en 30 j,
    192 en 90 j** (0,9 % par mois, 5,2 % en 90 j). ⚠ Échantillon = acquéreurs à recherche active, sans doute PLUS vivants que la
    moyenne : l'estimation est un plafond ;
  · ⇒ PREMIER TOUR (le suivi date surtout du 23/06, ~4 mois de retard) : ~5 % des 170 000 actifs = **~8 500 fiches à relire**,
    ~950 par nuit sur 9 nuits = **~26 min de fiches + ~17 min de liste ≈ 45 min par nuit** ;
  · ENSUITE (régime) : ~0,9 %/mois × 9 nuits ≈ 450 par tour = **~50 fiches par nuit ≈ 1,5 min + 17 min de liste ≈ 20 min**.
  · Les archivés (~9 200 pages) ne sont pas comptés : à décider s'ils en font partie.
- **Une lecture complète des ACTIFS en une fois (question du 03/11)** — ⭐ l'option EXISTE déjà, sans code :
  `phase2/sync/sync_contact_details.py --full-listing-refresh --contact-scope active --listing-max-pages 0` (lecture par numéro,
  toutes les pages), puis la règle de sélection existante relit chaque fiche dont `date_maj` (liste) > `last_detail_sync_at`.
  · liste : ~8 500 pages × ~1 s ≈ **2 h 20**, ~8 500 requêtes, une seule connexion ;
  · fiches : ~8 500 estimées (plafond, voir ci-dessus) × 1,66 s ≈ **3 h 55** si tout d'un coup → **≈ 6 h 15 et ~17 000 requêtes** ;
  · OU laisser le plafond du run (`ContactDetailLimit=1000`) les absorber : ~1 000 par nuit (~28 min), ~9 nuits, sans rien changer.
  · ⚠ lancer cette lecture = lancer un run → accord obligatoire ; durée d'exposition continue de 2 h 20 (le 19/08 : 4 h).
- ⭐ **CORRECTION DE L'ESTIMATION (03/11, idée de Frédéric : « partir de la dernière mise à jour complète »)** :
  · la dernière relecture complète des FICHES est de **mai 2026** (125 023 actifs sur 128 493 relus en 2026-05, ~26/05) ;
  · mesure NON biaisée, sur la liste complète du 23/06 gardée en local (168 575 contacts) : **377 fiches anciennes modifiées
    en 4 semaines** (0,22 %/mois) + 474 créées ⇒ depuis le 26/05 (~5,3 mois) : **~2 000 fiches anciennes modifiées**. Les
    créations remontent déjà chaque nuit en tête de liste ; mon « 8 500 » (échantillon d'acquéreurs actifs) était 4 fois trop haut ;
  · ⇒ liste complète **~2 h 20** (incompressible : Hektor n'a pas de filtre « modifié depuis », la liste est le seul moyen de
    connaître la date de chaque fiche) + **~2 000 fiches × 1,66 s ≈ 55 min** = **~3 h 15, ~10 500 requêtes** ; ou 2 nuits avec
    le plafond actuel de 1 000 fiches. La règle de sélection fait déjà exactement « modifiées depuis la dernière relecture ».
- **La forme retenue par Frédéric (03/11)** : lire la liste de TOUS les contacts (actifs puis archivés), comparer la date de
  modification Hektor à notre date de dernière relecture, ne relire QUE les fiches où Hektor est plus récent. ⭐ C'est exactement
  la règle existante (`date_maj` de la liste > `last_detail_sync_at`). Archivés, mesure sur la liste du 23/06 : 178 618 contacts,
  **41 modifiés en 4 semaines** ⇒ ~200 depuis mai. Bilan : **~2 200 fiches à relire (~1 h)**, mais la liste fait ~17 700 pages
  (**~4 h 55**) : c'est la LISTE qui pèse, pas les fiches. Total ≈ 6 h, ~20 000 requêtes → à couper en deux nuits
  (actifs ≈ 2 h 20 + ~55 min ; archivés ≈ 2 h 35 + ~6 min). Rien de lancé.
- **Le créneau dans la nuit (mesure 03/11, journaux des nuits du 31/10 au 03/11, heure d'hiver)** :
  · ⚠ les tâches tournent **1 h plus tôt** que l'heure affichée par le planificateur depuis le passage à l'heure d'hiver
    (déclencheurs posés en +02:00) : run à 04:00, recherches à 02:00, balayage à 23:00, documents à 21:00 ;
  · occupation réelle de Hektor : photos 20:00-20:05 · documents 21:18-23:17 · balayage photos (1 000 travaux du worker)
    23:00 → 00:18 / 01:01 · recherches 02:00-03:51 (4 000 fiches) · run 04:00-06:18 · descente 06:45-07:08 (Supabase) ;
  · **libre aujourd'hui : ~01:00 → 02:00 (1 h)** — trop court ;
  · ⭐ le balayage des photos annonçait « 2 nuits restantes » le 02/11 : une fois fini (~29 travaux/nuit), **23:20 → 02:00
    ≈ 2 h 40 se libère** → la liste des actifs (~2 h 20) ou des archivés (~2 h 35, juste) y tient, une par nuit ;
  · ⚠ les ~2 000 fiches des actifs ne tiennent pas dans le même créneau : le run de 04:00 les relirait (plafond 1 000/nuit,
    +~28 min) → le run finirait vers 06:46, APRÈS le départ de la descente (06:45). À régler : plafond abaissé (500/nuit,
    4 nuits, +14 min) ou vérifier la garde entre run et descente.
- **La vitesse d'avant le 07/09 (mesure 03/11, `raw_api_response`, minimum car seule la dernière lecture de chaque fiche est
  gardée)** : relecture complète des fiches contacts fin mai / début juin = **26 000 à 65 000 fiches par jour** (29/05 : 64 820
  en 6 h), heures de pointe **4,5 à 5,7 requêtes/s** (29/05 07h : 20 528 en une heure) ; liste du 23/06 : pointes à
  **11 à 12,7 pages/s**. Aucun bannissement à l'époque — le premier est du 19/08 (1,5 req/s pendant 4 h). ⚠ Le pare-feu a pu
  se durcir depuis : ces chiffres disent ce qui passait AVANT, pas ce qui passe aujourd'hui.
- **Le rythme du RUN DE NUIT avant / après le frein du 07/09 (journaux `.tmp/full_pipeline_*.log`, août → septembre)** :
  la lecture Hektor du run (`phase1 sync_raw`) prenait **~30 min** chaque nuit jusqu'au 07/09 (05:30 → 06:00), puis **~1 h 17 à
  1 h 20** dès le 08/09 (05:00 → 06:17), frein d'1 s par requête posé (Lot B). Même travail ⇒ avant ≈ **2,5 requêtes/s**, sans
  qu'aucun bannissement ne vienne du run lui-même (ceux d'août-septembre : rattrapage, sondes, connexions, objets supprimés).
  À ce rythme : liste des actifs **~57 min**, archivés **~61 min** → les deux tiendraient dans le créneau 23:20 – 02:00.

## 42. LES CORRECTIFS À FAIRE — LE PRINCIPE DE FRÉDÉRIC *(03/11, « résume-moi les correctifs à faire »)*

Principe posé : toujours le même — récupérer les fiches NOUVELLES et les fiches MISES À JOUR ; revenir à la vitesse d'avant
(À REVÉRIFIER D'ABORD) ; les archivés le dimanche ; nos gestes chez nous IMMÉDIATEMENT, et ceux qui ont encore besoin de Hektor
pour un numéro sont RELUS TOUT DE SUITE, jamais « à la nuit ». Rien n'est codé ; chaque pièce attend son « vas-y ».

1. **La nuit, du lundi au samedi : la liste ENTIÈRE des contacts actifs** (~8 500 pages, par numéro), puis relecture des seules
   fiches dont la date Hektor est plus récente que notre dernière relecture (règle existante). Option existante
   `--full-listing-refresh --contact-scope active --listing-max-pages 0` ; nouvelle tâche planifiée dans le créneau 23:20 – 02:00
   (libre dès la fin du balayage des photos), déclarée d'abord au moniteur de santé, réglée sur une sœur.
2. **Le dimanche : la liste entière des archivés** (~9 200 pages), même principe.
3. **La vitesse d'avant, revérifiée d'abord** : le run lisait ~2,5 req/s jusqu'au 07/09 (§41). Réglage par processus
   (`HEKTOR_MIN_REQUEST_INTERVAL_MS`) pour CETTE tâche seulement ; montée par paliers ; arrêt net au premier refus ou silence ;
   compte des requêtes de la nuit au journal. Point à surveiller : ~17 000 requêtes par nuit avec le reste.
4. **Le premier rattrapage** : ~2 200 fiches modifiées depuis mai (~1 h) — par la tâche elle-même ou par le run (plafond 1 000).
   ⚠ si c'est le run : il dépasserait 06:45 (départ de la descente) → plafond abaissé ou garde run/descente vérifiée.
5. **Nos gestes contacts : chez nous à l'instant, relus tout de suite quand Hektor donne un numéro.** À AUDITER geste par geste
   (créer, modifier, archiver/réactiver, conjoint/couple, rattachement de coquille, relations au bien) : qui écrit chez nous
   d'abord, qui relit après Hektor, et sur QUELLES fiches. ⭐ Le rattachement d'une coquille (les 680) devra relire les DEUX
   fiches (porteuse et coquille) : c'est ce qui a manqué pour EA32621.
6. **EA32621 lui-même** : réparé par la première nuit du point 1, ou tout de suite par deux relectures (accord demandé).
7. Trouvés en passant, à trancher à part : les tâches partent 1 h plus tôt depuis l'heure d'hiver (déclencheurs en +02:00) ;
   Matterport refusé (401) cette nuit ; la comparaison date Hektor (heure de Paris) / date de relecture (UTC) ne fait que des
   relectures en trop, jamais d'oubli.

## 43. EA32621 RELUE ET CORRIGÉE CHEZ NOUS *(03/11 matin, « il faut juste corriger les derniers regroupements… les gestes ont tous été déjà vérifiés »)*

- Frédéric : les gestes de l'app ont DÉJÀ été vérifiés → le point 5 du §42 (audit des gestes) est RETIRÉ. Reste à corriger les
  regroupements de couples faits chez Hektor que la nuit n'a pas relus. Un seul : EA32621 (les fiches d'essai 606117-606119 du §36
  ont été supprimées, 0 reste).
- `refresh_contact_inproc.py --contact-id 10260585` (coquille) PUIS `--contact-id 10260586` (porteuse) : 2 lectures `ContactById`,
  0 écriture chez Hektor, 13,4 s et 13,7 s, code 0.
- Supabase après : 10260585 `hektor_couple_contact_id = 10260586`, rôle `menage_resolu` ; 10260586 `couple_json.etat = vide`,
  conjoint 10260585 → l'écran doit montrer le bouton « Compléter le conjoint ». ⚠ `nature_fiche` de 10260586 reste
  `personne_seule` jusqu'à l'étape « nature » de la nuit (le miroir local porte maintenant le lien, elle le verra). Non vu à l'écran.
- ⚠ **Rappel de Frédéric (03/11) : à 23:00 tourne le balayage des photos masquées.** Le créneau « 23:20 – 02:00 » du §41/§42
  n'est donc PAS libre d'office : à 23:00 le balayage pose ses travaux au worker (1 000 jusqu'ici, 23:00 → 00:18 / 01:01 ; ~30
  par nuit une fois le parc fini, ~5 min), et l'entretien des documents tourne jusqu'à ~23:17. Deux processus qui lisent Hektor
  en même temps = deux freins séparés = débit doublé. ⇒ La lecture de la liste des contacts devra **démarrer après**, avec une
  **garde au départ** : aucune tâche Hektor du worker en attente ou en cours (sinon attendre, puis renoncer pour la nuit si
  02:00 approche), sur le modèle de la garde « anti-run » du ménage du coffre. Créneau réaliste : ~23:30 → 02:00 une fois le
  balayage terminé, ~01:05 → 02:00 tant qu'il pose 1 000 travaux.
- ⛔ **Correction de Frédéric (03/11) : le balayage des photos masquées va PASSER AUX ARCHIVÉES** → il gardera 23:00 → ~01:00
  chaque nuit ; le créneau 23:30 – 02:00 n'existera pas. Autre créneau à trouver.
- ⭐ **Ce qui libère de la place : la vitesse d'avant.** La tâche des recherches (02:00) se dit elle-même « ~0,3 s/contact,
  ~20 min » (en-tête de `sync_active_searches.py`) ; elle prend aujourd'hui **1 h 51** (4 018 fiches, 1,66 s) à cause du frein du
  07/09. Le run : lecture Hektor 30 min avant le 07/09, 1 h 20 depuis. Elle doit rester (éditer une recherche ne bouge PAS la
  `datemaj` du contact : écrit dans son en-tête).
- **Deux créneaux possibles, MÊME processus que des lectures de contacts déjà en place (un seul frein, pas de débit doublé)** :
  A. **dans la tâche de 02:00** : liste des actifs (~57 min à la vitesse d'avant) + les 4 000 recherches (~20-30 min) + les fiches
     changées → fin vers ~03:30, avant le run de 04:00 ; le run n'est pas touché ;
  B. **dans le run de 04:00** : remplacer la lecture courte des contacts (3 pages) par la liste entière ; le gain de la vitesse
     d'avant sur la lecture Hektor (~50 min) paie la liste (~57 min) → fin du run à peu près inchangée (~06:20-06:30).
  Dans les deux cas : la vitesse d'avant d'abord revérifiée, arrêt au premier refus ; le dimanche, les archivés au même endroit.
- ⛔ **Règle de Frédéric (03/11) : ne changer la vitesse QUE des tâches qui n'appellent QUE l'API, jamais la console.**
  Mesuré dans le code : les deux freins sont SÉPARÉS —
  · API (`/Api/…`, client Python `HektorClient`) : `HEKTOR_MIN_REQUEST_INTERVAL_MS`, défaut 1 000 ms DANS LE CODE
    (`hektor_pipeline/common.py` l. 95), **posé nulle part** (ni `.env`, ni `phase2/.env`, ni les `.ps1`) → réglable pour UN
    processus en le posant dans le `.ps1` de sa tâche, sans toucher aux autres ;
  · console (`xmlrpc.php`, `/admin/`) : `CONSOLE_HEKTOR_MIN_REQUEST_INTERVAL_MS=1000` dans `Console/.env` (worker, mise en file,
    `sync_hektor_drafts.py`, `sync_hektor_immo_pro.py`) → **on n'y touche pas**.
  ⇒ la tâche de 02:00 (`sync_active_searches.py` → `sync_contact_details.py` → `ContactById`, puis étapes locales) n'appelle
    QUE l'API : elle peut être accélérée seule. Le run de 04:00 MÉLANGE l'API et la console (brouillons, immo pro, chauffage,
    champs manquants) : il reste tel quel. ⇒ **Créneau A (tâche de 02:00) seul conforme à la règle.**
- **Frédéric (03/11) : « ne modifier QUE le nouveau run sur les contacts » — et que faire du run actuel des contacts ?**
  Ce qui lit les contacts aujourd'hui, la nuit :
  · la tâche **Recherches actives** (02:00 → 03:51, API seule) : relit ~4 000 fiches d'acquéreurs à recherche active SANS regarder
    la date (éditer une recherche ne bouge pas la `datemaj`) — ce travail doit continuer ;
  · le **run de 04:00** (mixte API + console) : lecture courte de la liste (3 pages) + relecture des fiches changées (36 cette nuit,
    ~1 min).
  Proposition (non décidée) : une **NOUVELLE tâche « contacts », API seule, à la vitesse d'avant**, qui REMPLACE la tâche des
  recherches à 02:00 (l'ancienne est désactivée, son code n'est pas modifié) et fait, dans un seul processus : ① la liste entière
  (actifs du lundi au samedi, archivés le dimanche) ; ② les fiches où Hektor est plus récent ; ③ les ~4 000 fiches à recherche
  active (même code que l'ancienne tâche). Estimation : ~57 min + quelques minutes + ~30-40 min ≈ **1 h 40**, dans le créneau
  actuel 02:00 → 03:50 (première nuit : +~20 min pour ~2 200 fiches). Le run de 04:00 ne bouge pas : sa lecture courte reste un
  filet (contacts créés entre 02:00 et 04:00), elle ne coûte qu'une minute.
- ⚠ **Précision (03/11, Frédéric : « pourquoi tu supprimes les recherches ! »)** : la proposition ci-dessus ne supprime AUCUNE
  recherche ni la relecture des ~4 000 acquéreurs — elle la déplaçait dans la nouvelle tâche. Variante qui ne touche pas du tout
  à la tâche des recherches : la nouvelle tâche contacts tourne SÉPARÉMENT de ~01:05 (après le balayage, garde « worker vide »)
  à 01:58, s'arrête d'elle-même pour laisser partir les recherches à 02:00, et reprend la nuit suivante à la page atteinte
  (~55 min à ~2,5 pages/s ≈ 8 000 pages : presque toute la liste des actifs par nuit).

## 44. AUDIT — « TOUT DANS UNE TÂCHE » : LA NUIT DES CONTACTS *(03/11, « tout dans une tâche, audit de nouveau et explique-moi »)*

Audit limité à : **contact × lire / remonter** (la nuit). Les autres objets et gestes ne sont pas mesurés ici.

**Ce qui existe (code lu le 03/11)**
- Tâche « GTI Recherches Actives » (02:00, surveillée CRITIQUE par `monitoring/check_gti_health.py` l. 116) →
  `scheduled/run_recherches_actives.ps1` → `phase2/sync/sync_active_searches.py` : ① le CARNET des contacts devenus acquéreurs
  (plafond 500) ; ② les ~4 000 contacts à recherche active, relus SANS regarder la date ; UNE session Hektor
  (`sync_contact_details.py --contact-id-file … --skip-listing-refresh`) ; puis étapes LOCALES par lots de 300 (normalize → couche
  → push) ; coupe-circuit après 3 lots en échec ; cède au verrou de la descente (`pull_from_supabase.lock`, 30 min max).
- ⭐ **Pourquoi 1,66 s par fiche** : ce n'est pas seulement le frein du 07/09. La tâche applique la « méthode de référence »
  (lots de 100, 0,5 s entre fiches, **60 s de pause entre lots**, ~45 % d'occupation) ; avec le plancher d'1 s du client, ça fait
  ~1 s + 0,6 s par fiche. L'en-tête « 0,3 s / ~20 min » date d'avant ces règles.
- ⛔ **Cinquième bannissement, à ne pas oublier** (commentaire du code) : le **22/08, 25 800 fiches contacts lues en 1 h 47
  (~4 req/s) ont fait bannir l'IP**. C'est de là que viennent les lots de 100 et les pauses. Accélérer la lecture des contacts
  n'est donc PAS sans précédent de risque.
- Lecture de la liste : `sync_contact_details.py --full-listing-refresh` appelle `sync_contact_listing_variant` de `sync_raw.py`
  (fonction PARTAGÉE avec le run de 04:00) : ~1 page/s (plancher 1 s + 0,1 s), **aucune pause**, écrit `sync_contact_state`
  (variante, `date_maj`, vu le) et le curseur `contact_cursor_<scope>` = la plus grande `datemaj` vue — cohérent avec le run.
- ⚠ Une relecture « ciblée » (recherches) réécrit `sync_contact_state` avec `listing_variant='targeted'` et **`date_maj = NULL`**
  (`upsert_contact_state`, `sync_raw.py` l. 517) : 44 179 lignes sont dans ce cas. Sans gravité (elles sont relues), mais l'ORDRE
  compte : la liste d'abord, la sélection des fiches changées ensuite, les recherches en dernier.
- Les fiches relues par la sélection « changées » n'arrivent chez Supabase QUE par le run de 04:00 (couche reconstruite + push
  chaque nuit) ; seules les recherches font leurs étapes locales elles-mêmes.

**Le dessin proposé (rien codé)** — la tâche garde son NOM, son heure de 02:00 et sa surveillance ; son lanceur enchaîne :
  0. garde de départ (verrou de la descente ; aucune tâche Hektor en cours au worker) ;
  1. **NOUVEAU script de liste** (API seule, sa propre boucle — la fonction partagée du run n'est PAS touchée) : actifs du lundi
     au samedi, archivés le dimanche ; vitesse réglée pour CE processus seulement (`HEKTOR_MIN_REQUEST_INTERVAL_MS`) ; pause
     régulière ; arrêt net au premier refus ; compte des requêtes au journal ; **reprise à la page atteinte** si l'heure limite
     tombe ;
  2. `sync_contact_details.py` existant : les fiches où Hektor est plus récent (plafond par nuit) ;
  3. `sync_active_searches.py` **inchangé** (carnet + ~4 000 recherches, mêmes lots et pauses) ;
  4. **heure limite ~03:50** : on s'arrête proprement pour laisser le run de 04:00.
- Durées à ~2 req/s : liste ~1 h 10 · fiches changées ~1 min (1re nuit ~40 min) · recherches ~1 h 15 au lieu de 1 h 51 →
  **~2 h 25, plus que 02:00 → 04:00**. ⇒ soit démarrer plus tôt (~01:05, après le balayage, garde « worker vide »), soit
  accepter que la liste se termine sur 2 nuits (reprise à la page).
- Ce qui pourrait casser : le run de 04:00 (si la tâche déborde — d'où l'heure limite) ; un bannissement (22/08 !) → vitesse
  modérée, pauses, arrêt au 1er refus ; le volume de la nuit (~8 500 requêtes de plus, ~19 000 en tout, au-dessus de
  l'estimation incertaine du quota) ; la surveillance (même nom de tâche → reste surveillée ; codes de sortie à garder).
- ⛔ **CORRECTION du « ~1 h 15 » des recherches (03/11, question de Frédéric « pourquoi on gagne du temps ? »)** — décomposition
  mesurée de la nuit du 03/11 (6 669 s pour 4 018 fiches ; journal : étapes locales de 1 500/4 018 à 6 489 s jusqu'à la fin à
  6 669 s) : **lecture ~1 h 07** (4 018 × 1 s, le plancher l'emporte sur le délai de 0,5 s + le temps de réponse) +
  **pauses ~40 min** (40 lots de 100 × 60 s) + **étapes locales ~4 min**. Seul le PLANCHER change avec la vitesse : à 2 req/s,
  une fiche = temps de réponse (~0,15 s, déduit des pointes de mai à 5,7 req/s) + délai 0,5 s ≈ 0,65 s → lecture ~44 min ;
  les pauses (40 min) et le délai restent → **~1 h 28, gain ~23 min, pas 36**. Mon « 1 h 15 » oubliait le temps de réponse.
  Total de la tâche à 2 req/s : liste ~1 h 10 + fiches ~1 min + recherches ~1 h 28 ≈ **2 h 40**. Pour gagner davantage, il
  faudrait toucher les pauses ou le délai des recherches = la méthode prudente posée après le bannissement du 22/08 → à lui.
- ⛔ **DÉCISION DE FRÉDÉRIC (03/11) : la vitesse des RECHERCHES ne change pas (« ne touche à rien ») ; seule la LISTE DES
  CONTACTS reprend la vitesse d'avant.** Conséquences sur le dessin :
  · le réglage de vitesse (`HEKTOR_MIN_REQUEST_INTERVAL_MS`) est posé pour le SEUL processus de la liste, et retiré avant les
    recherches (chaque étape du lanceur est un processus Python séparé) ; `sync_active_searches.py`, ses options et son lanceur
    actuel ne changent pas ;
  · durées : liste ~57 min (2,5 req/s) + fiches changées ~1 min + recherches **1 h 51 (inchangé)** ≈ 2 h 50 → ne tient pas de
    02:00 à 04:00 ;
  · proposition : la tâche démarre à **~01:05** (après le balayage, garde « worker vide ») ; la liste a une **heure limite
    (~01:55)** et reprend la nuit suivante à la page atteinte (~7 500 pages par nuit : tous les actifs vus en ~1 nuit et quart) ;
    les recherches partent donc vers 02:00 comme aujourd'hui et finissent vers 03:51 comme aujourd'hui.
- **Deux nuits pour les actifs ? et le balayage des archivées ?** (03/11) — lu dans `scheduled/run_balayage_photos_masquees.ps1`
  et `Console/enqueue_photos_masquees_lot.js` : archives 35 329 + historiques 8 948 = **44 277 annonces**, lot de 1 000 par nuit
  ⇒ **~44 nuits** où le balayage pose 1 000 travaux à 23:00 (fenêtre de pose jusqu'à 01:00, `-HeureLimite 1`) et occupe le worker
  jusqu'à ~00:20 – 01:00 (mesuré : 00:18 le 02/11, 01:01 le 01/11).
  ⇒ Proposition : la tâche part à **00:20** et sa garde ATTEND que le worker n'ait plus de travail Hektor ; la liste démarre donc
  entre ~00:20 et ~01:05 et s'arrête à 01:55 → **50 à 95 min = ~7 500 à ~14 000 pages** : les ~8 500 pages des actifs passent
  en UNE nuit la plupart du temps, sinon le reste la nuit suivante (reprise à la page). Ce n'est pas « deux nuits » fixes mais un
  tour continu : chaque contact actif vu toutes les 1 à 2 nuits. Après les ~44 nuits du balayage (≈ ~30 travaux/nuit), la liste
  partira vers ~23:10 et tiendra toujours en une nuit. Le dimanche : archivés (~9 200 pages), même mécanique.

## 45. ANALYSE EN PROFONDEUR — LA LISTE DES CONTACTS LA NUIT *(03/11, « on garde l'idée mais il faut analyser en profondeur… ne rien casser »)*

Audit limité à : **contact × lire / remonter**, ordonnancement, verrous, surveillance. Trois analyses en lecture seule (0 appel
Hektor/Supabase, 0 écriture), les points lourds REVÉRIFIÉS par moi (marqués ✔).

**A. Ce qui casserait si on réutilisait la mécanique existante (à NE PAS faire)**
1. ✔ **Le run de 04:00 ne relirait plus les annonces des contacts modifiés** : sa liste courte calcule les contacts « changés »
   (date différente de `sync_contact_state`) et relit leurs annonces (`sync_raw.py` l. 1755-1759,
   `find_annonce_ids_by_contact_ids`). Si l'étape de nuit écrit `sync_contact_state` et le curseur `contact_cursor_*`, ce
   déclencheur se vide. ⇒ l'étape doit avoir **SON PROPRE suivi** (table à elle) et ne toucher ni `sync_contact_state`, ni le
   curseur, ni les pages `list_contacts_*`.
2. ✔ **Les pages brutes `list_contacts_*` sont relues CHAQUE NUIT par `normalize_source`** (`CONTACT_ENDPOINTS` l. 52-58, boucle
   l. 1204-1211) ; écrire sous ces noms écraserait l'instantané du 23/06 et changerait le miroir. ⇒ nom de pages À PART (que
   `normalize_source` ne lit pas).
3. **La tâche « GTI Recherches Actives » est coupée par Windows après 2 h** (`ExecutionTimeLimit = PT2H`, ✔ export de la tâche) ;
   elle dure déjà 1 h 50-1 h 52. ⇒ relever la limite (geste sur la tâche, accord) si la liste y entre.
4. **Le run de 04:00 n'a AUCUNE garde au départ** (`run_full_pipeline.ps1` l. 387) : un débordement mettrait deux clients
   Hektor et deux écrivains de `hektor.sqlite` en même temps, et une erreur de `sync_raw` arrête tout le run. ⇒ l'étape s'arrête
   d'elle-même à 01:55 ; les recherches gardent leur durée (fin ~03:51).

**B. Ce qui est sûr (mesuré)**
- Tri `id ASC` respecté et total (pages du 23/06 : 0 doublon, 0 inversion, distincts = `total`) ; `metadata` fiable ; au 03/11
  **8 502 pages actives** (170 040) et **8 955 archivées** (179 083) ; les créations arrivent en fin de liste.
- Chaque ligne de liste porte `datemaj` (heure de Paris), `refCouple`, `archive`, `typologie` (17 clés, 100 % des lignes).
  Paris contre UTC ⇒ seulement des relectures en trop. 19 archivés ont `datemaj = 0000-00-00` (jamais retenus par la date).
- Un seul client = une connexion + un renouvellement du jeton toutes les ~50 min (mesuré) ; aucun code ne supprime ni ne signale
  un contact « disparu » à partir de la liste. Le « 11 028 » du journal = des GROUPES DE DOUBLONS (`build_contacts_layer.py`
  l. 1770), rien à voir avec la liste.

**C. Ce qui est risqué et doit être prévu dans le code**
- **Reprise** : la page N n'est pas stable (mesuré : 44 445 contacts sortis des actifs entre mars et mai ; la page 8430 de mars
  est devenue la page ~6207). Reprendre « à la page N » SAUTE un contact par départ. ⇒ garder (page, dernier id, total), vérifier
  le recouvrement (la page relue doit contenir un id ≤ dernier id, sinon reculer — dichotomie ~13 requêtes au pire), comparer
  distincts et `total` à la fin. Aucune API ne filtre par id.
- **Erreurs** : `sync_contact_details` règle `max_retries = 1` → un seul 500 / délai / jeton expiré tue la lecture. ⇒ la nouvelle
  boucle : arrêt net sur tout 4xx (pas de reconnexion sur 403/429), patience bornée sur 5xx, point de reprise écrit à chaque page.
- **Vitesse** : `HEKTOR_MIN_REQUEST_INTERVAL_MS` est lu À L'IMPORT (`common.py` l. 95), avant le `.env` ⇒ le poser dans
  l'environnement du processus (lanceur), pour la liste SEULE. Pauses périodiques (pas 57 min d'affilée), montée par paliers.
- **Volume** : ~8 500 requêtes de plus ⇒ ~17 000-19 000 par 24 h, au niveau de l'estimation (incertaine) du quota.
- `datemaj` ne bouge pas quand on ARCHIVE un contact (2 778 sur 2 791 passés actif → archivé, même date) : un départ ne se voit
  que par son ABSENCE entre deux lectures complètes (hors périmètre des couples, noté).

**D. Le dessin corrigé (rien codé)**
  la tâche « GTI Recherches Actives » garde son nom et sa surveillance ; départ 00:20 ; limite Windows relevée ; son lanceur :
  0. garde : verrou de la descente absent ; AUCUN travail Hektor en attente/en cours au worker (tous types, avec une sortie si un
     travail est resté bloqué « en cours ») ;
  1. NOUVEAU script de liste (API seule, vitesse à lui, pauses, arrêt 4xx, reprise par id avec recouvrement, heure limite 01:55) ;
     écrit dans SA table (id, datemaj, refCouple, archive, vu le) et ses pages sous un nom à part — rien d'autre ;
  2. la liste des fiches à relire = datemaj (ramenée en UTC) > `last_detail_sync_at` → `sync_contact_details --contact-id-file`
     (le chemin « ciblé » déjà utilisé par les recherches et par l'ouverture d'une fiche) avec un plafond ;
  3. `sync_active_searches.py` INCHANGÉ ;
  le run de 04:00 inchangé : il reconstruit et envoie les fiches relues.

**E. Trouvé en passant (hors de ce chantier, à trancher à part)**
- ✔ **Les vieilles pages de mars** (`list_contacts_active` pages 8430-10759) sont toujours relues chaque nuit par la
  normalisation et, passant APRÈS celles de juin, imposent leur valeur : **32 457 contacts du miroir portent le négociateur de
  MARS** (surtout vide) quand la liste de juin en donne un (souvent « 2 », 16 735 cas). Le nettoyage des pages périmées
  (`prune_raw_listing_pages`, `sync_raw.py` l. 615) n'existe que pour les annonces. Quelle valeur est la bonne : non tranché.
- Le verrou de la descente n'est lu qu'UNE fois par la tâche des recherches (avant la lecture), alors que son commentaire dit
  « entre deux lots » (`sync_active_searches.py` l. 34-37 contre l. 552).
- ⛔ **CORRECTION de ma part (§41)** : les tâches ne partent PAS « 1 h plus tôt ». Leurs déclencheurs sont en **+01:00** (✔ export :
  `2026-06-20T02:00:00+01:00`) : heure écrite en hiver, +1 h en été. Mon affichage convertissait mal. (Un départ à 00:20 sera
  01:20 en été.) Les commentaires « 03:00 », « 05:30 » des scripts sont périmés.
- ⭐ **DÉCISION DE FRÉDÉRIC (03/11) : « c'est le but de les réparer, ces pages ! »** ⇒ le dessin change sur un point :
  · les pages fraîches sont écrites **au VRAI endroit** (`list_contacts_active` / `list_contacts_archived`), pour que la
    normalisation de 04:00 REPARE le miroir ; après un tour COMPLET, les pages au-delà de la dernière (restes de mars) sont
    **purgées** ;
  · le **carnet du run** (`sync_contact_state` + curseur) reste INTACT : sinon le run ne relirait plus les annonces des contacts
    modifiés. La nouvelle étape garde son propre carnet de dates pour choisir les fiches à relire ;
  · ce que la réparation changera au 1er tour : surtout le **négociateur** (la seule valeur où la liste l'emporte sur la fiche,
    `normalize_source.py` l. 1152) — ~32 457 contacts portent celui de mars — et les contacts SANS fiche détaillée (repris de
    la liste). L'état archivé, le nom, etc. viennent de la fiche : inchangés. Aucun contact supprimé (aucun code ne supprime
    d'après la liste). Effet à surveiller : la sentinelle `data.contacts_sans_nego` et la taille du premier envoi à Supabase ;
  · prudence proposée : **un premier tour « à blanc »** (pages rangées à part + rapport des écarts champ par champ), regardé par
    Frédéric, AVANT de les écrire au vrai endroit.
- ⭐ **AUDIT « relire aussi l'annonce » (03/11, Frédéric : « avec le mécanisme proposé cela ne se fera pas, est-ce grave ? »)** —
  il a raison : avec un carnet à part, un contact modifié repéré par la NOUVELLE liste n'a pas son annonce relue par le run.
  · **Ce que l'annonce garde des contacts** : le détail Hektor d'une annonce embarque une COPIE de ses propriétaires
    (`hektor_annonce_detail.proprietaires_json` : nom, prénom, téléphone, e-mail, `datemaj`, `refCouple`…). Elle sert à
    `phase2/pipeline/view_generale.py` l. 205-240 (résumé des propriétaires et leurs coordonnées sur la fiche du bien, et le
    repli de `mandants_texte`) et à `build_contacts_layer.py` l. 1263-1278 (liens « propriétaire » contact ↔ annonce). Si le
    contact change de nom ou de téléphone chez Hektor, cette copie reste ancienne tant que l'annonce n'est pas relue.
  · **Pourquoi le run relit l'annonce** : `sync_raw.py` l. 1755-1759 — contacts « changés » de sa liste courte → leurs annonces
    (`sync_annonce_contact_link`) ajoutées aux annonces à relire. **Volume mesuré cette nuit : 80 contacts vus → 12 annonces
    au plus.** Ce n'est pas journalisé.
  · **Est-ce grave ?** Ce n'est PAS pire qu'aujourd'hui (aujourd'hui ni le contact ni l'annonce ne sont relus pour un contact
    modifié loin dans la liste) ; mais la fiche du BIEN garderait les anciennes coordonnées du propriétaire alors que la fiche du
    CONTACT serait juste — une incohérence visible. ⇒ il FAUT la parade.
  · **Parade** : la tâche des contacts dresse aussi la liste des annonces liées aux contacts qu'elle a relus, et la confie au run
    de 04:00, qui les relit dans sa lecture habituelle. ⭐ Le précédent existe : « [mandat absent du détail] N annonce(s), relue(s)
    en plus » (`sync_raw.py`, interrupteur `APP_RELIRE_DETAIL_MANDAT_ABSENT`, posé le 02/11). Ajout de quelques lignes au run,
    derrière un interrupteur, avec un plafond (1er tour : ~2 200 contacts → peut-être ~1 000 annonces, à étaler).
- **Impact en temps sur le run de 04:00 (mesure du 03/11)** : le run relit une annonce en **2 requêtes** (`annonce_detail` +
  `mandat_by_annonce`, 47 + 47 cette nuit), espacées d'**1 s** (écart médian mesuré) ⇒ **~2 s par annonce** dans sa lecture
  Hektor ; la normalisation, la couche et l'envoi sont refaits en entier chaque nuit (coût fixe, inchangé).
  Combien d'annonces par contact modifié : échantillon de 740 contacts anciens modifiés depuis le 03/08 → **526 annonces liées
  (~0,7 par contact)** ; cette nuit 80 contacts vus → 12 annonces.
  · **en régime** : 15 à 50 contacts/nuit → ~10 à 35 annonces → **+20 s à +70 s** ;
  · **1er rattrapage** : ~2 200 contacts → ~1 550 annonces → **~+52 min** s'il passait d'un coup → le run finirait vers ~07:10 ;
    la descente de 06:45 ATTEND la fin du run (`run_descente.ps1`, garde « Quotidien en cours ») : pas de casse, mais l'app serait
    à jour ~25 min plus tard. ⇒ **plafond, p. ex. 300 annonces/nuit (+10 min)** : rattrapage en ~5 nuits.
- **Sans plafond, la chaîne du matin** (`scheduled/run_descente.ps1` l. 61-100, lu le 03/11) : la descente de 06:45 ATTEND le run
  **45 min au plus** (jusqu'à 07:30), puis RENONCE (exit 1, doublures d'hier, alerte). Run +52 min ⇒ fin ~07:10 ⇒ descente
  ~07:10 → ~07:35 : ça passe, avec **~20 min de marge** seulement ; app à jour ~25 min plus tard. La sauvegarde de 08:00 et les
  relances (Supabase seul) ne sont pas touchées. Un retard de plus le même matin ferait sauter la descente ⇒ plafond recommandé.
- ⭐ **Frédéric (03/11) : « il y a de la marge, et la liste du run des contacts sera elle-même plafonnée »** — exact : les fiches
  relues par la tâche des contacts sont limitées par le TEMPS qui reste avant les recherches (elles doivent partir vers 02:00
  pour finir avant 04:00), soit quelques centaines par nuit pendant le rattrapage (~1-1,6 s par fiche). Les annonces confiées au
  run suivent (~0,7 par contact) : ~200 → **~7 min de plus** pour le run. Le plafond sur les annonces devient un simple
  filet de sécurité (valeur haute), pas un réglage de rythme.

## 46. LE PASSAGE À BLANC EST ÉCRIT ET ÉPROUVÉ HORS LIGNE *(03/11, « Oui, à blanc d'abord » ; commit 214a83e)*

- `phase2/sync/liste_contacts_nuit.py` (neuf, dormant, rien ne l'appelle) : lit `ListContacts` triée par numéro, page après page ;
  vitesse pour CE processus (`--intervalle-ms`, défaut 1 000 = le frein actuel ; refus sous 300 ms) ; pause toutes les 500 pages
  (30 s) ; `--heure-limite` (HH:MM) ; UNE seule tentative de connexion ; arrêt net au premier refus (sortie 3) ou si Hektor ne
  répond plus après la patience habituelle 2/8/30 s (sortie 4) ; reprise par NUMÉRO (relit la dernière page, recule tant
  qu'elle commence après le dernier numéro lu, 60 pages au plus) ; son carnet `liste_nuit_contact`, son tour `liste_nuit_tour`,
  ses pages sous `nuit_liste_contacts_<scope>` ; rapport JSON dans `logs/liste_contacts_nuit/` (numéros seulement) : fiches à
  relire, dont jamais lues, dates `0000`, annonces liées, absents du miroir, négociateurs qui changeraient (principaux couples
  de valeurs), liens de couple et états archivés différents.
- `phase2/sync/test_liste_contacts_nuit.py` : **TOUT VERT** — tour complet ; plafond puis reprise après 25 départs sous la
  position (1 page de recul, **aucun contact sauté**) ; création vue au tour suivant ; refus 403 (arrêt net, reprise gardée,
  aucune page après le refus) ; heure limite (00:20, 01:56, 23:10 la veille) ; rapport ; ⭐ **TÉMOIN : carnet du run, curseur
  et pages `list_contacts_*` INTACTS** ; 3 VRAIES pages du 23/06 relues (60 contacts, ordre respecté).
- ⏰ **Reste : le passage à blanc RÉEL chez Hektor** (~8 500 requêtes) — moment et vitesse à décider par Frédéric. Il crée les
  deux tables dans `data/hektor.sqlite` (additif). Rien d'autre n'est touché.

## 47. LE PASSAGE À BLANC RÉEL : LES ACTIFS LUS EN ENTIER, SANS UN REFUS *(03/11, « FAIS LE TEST A BLANC MAINTENANT A LA VITESSE DE LA NUIT PRÉVUE »)*

- Lancé à 11:15 (heure de Paris), file du worker vide, aucune tâche GTI en cours :
  `liste_contacts_nuit.py --scope active --intervalle-ms 400 --pause-toutes-pages 500 --pause-secondes 30 --nouveau-tour`.
  Journal `logs/liste_contacts_nuit/a_blanc_2026-11-03_actifs.log`, rapport `rapport_active_2026-11-03_12-33-23.json`.
- ⭐ **Sortie 0, tour terminé : 8 503 pages, 170 050 contacts, 0 recul, 0 page hors ordre, aucun refus.**
  **8 503 requêtes (+ la connexion) en 4 676 s = 1 h 18**, soit **0,55 s par page** (400 ms de frein + le temps de
  réponse de Hektor ; ~1,8 req/s, sous les ~2,5 d'avant le 07/09) et 17 pauses de 30 s. ⇒ la nuit, un départ à 00:20 finit
  vers **01:38**, avant l'heure limite prévue de 01:55. Le volume (8 504 requêtes) est celui annoncé.
- **Ce que la liste a trouvé** (comparaison avec notre miroir, aucun appel en plus) :
  - **236 fiches à relire** (Hektor plus récent que notre dernière relecture), **dont 75 jamais relues**, dont 10 absentes
    du miroir ; 0 date `0000` ;
  - **163 annonces au plus** liées à ces fiches (à confier au run de 04:00 : ~2 s chacune ⇒ ~5-6 min) ;
  - 17 liens de couple différents, 58 états « archivé » différents ;
  - ⚠ **32 473 négociateurs différents** — c'est l'ampleur déjà connue des pages de mars (32 457, hors chantier), à
    trancher par Frédéric ; le plus gros : miroir vide → « 2 » (16 263), « 25 » → « 2 » (6 696).
- ⭐ **Témoins positifs** : 352, 4307, 23721, 42552 portent une `datemaj` Hektor du 22 au 29/10 et n'ont pas été relus depuis
  mai — de vraies fiches ratées par la nuit (352 et 23721 sont même encore « archivées » dans notre carnet alors qu'elles sont
  dans la liste des actifs). ⭐ **Témoin négatif** : 467326 / 467325 (EA32621, `datemaj` 02/11 23:47-23:48, relues ce matin à
  08:00) ne sont PAS à relire — la règle juge juste.
- ⭐ **TÉMOINS « RIEN TOUCHÉ »** : `sync_contact_state` (dernière écriture 08:00:43, avant le départ), `contact_cursor_active`
  et `_archived` (écrits à 03:51 par la nuit), pages `list_contacts_*` (dernière 03:51) — **inchangés**. Seules les deux tables
  neuves et 8 503 pages `nuit_liste_contacts_active` ont été écrites.
- 236 au lieu des ~2 000 estimés : l'estimation comptait les fiches modifiées depuis la relecture complète de mai ; la plupart
  ont été relues depuis par la nuit. Les 236 sont le TROU réel.
- ⏰ **Reste, chaque étape sur « vas-y »** : le mode réel (pages au vrai endroit, purge de mars, relecture des fiches,
  annonces confiées au run derrière un interrupteur) ; le lanceur (00:20, garde « worker vide », 01:55) ; la limite PT2H ;
  les archivés le dimanche.

## 48. LE MODE RÉEL EST ÉCRIT ET ÉPROUVÉ HORS LIGNE — RIEN N'EST BRANCHÉ *(03/11, « Oui, prépare-le » ; commit d84f717)*

- **Le précédent existait** : `refetch_contacts_listing_parallel.py` (relecture complète du 23/06) a écrit la liste ENTIÈRE
  sous `list_contacts_active/archived`, `sort=id ASC` : exactement la forme du mode réel. Il n'a pas purgé, d'où les 2 330
  pages du 30/03 restées au-delà de la page 8429. `sync_raw.prune_raw_listing_pages` fait déjà la même purge pour les annonces.
- **`liste_contacts_nuit.py --reel`** (à blanc reste le défaut) : pages au vrai endroit (`list_contacts_<scope>`, type
  `contact_<scope>`, paramètres du 23/06), un tour ne mélange jamais les deux modes ; fiches à relire (Hektor plus récent que
  `last_detail_sync_at` OU notre `relu_le`), les plus récemment modifiées d'abord, **au frein du projet** (1 s + 0,5 s),
  jusqu'à `--heure-limite-fiches`, mêmes écritures que `sync_contact_details` ; 404 et réponse illisible mises de côté ;
  **tout autre refus arrête net** ; chaque fiche relue entre au **panier du run** (`relu_le`, `remis_au_run_le` vide) ; garde
  « worker vide » (lecture ratée = occupée) ; heures à **l'horloge des déclencheurs (+01:00 fixe)** (en heure locale, l'été,
  01:55 tomberait avant le départ 00:20+01:00) ; `--purger-pages-perimees` (à blanc par défaut, `--confirmer`) refusée sans
  tour RÉEL terminé dont chaque page 1..N a été réécrite pendant ce tour.
  ⛔ Jamais touchés : `sync_contact_state.date_maj / listing_variant / last_seen_at`, le curseur, les pages `_update`.
- **`sync_raw.py`** (+63 lignes ; seules les miennes sont commitées, les 45 lignes « mandat absent du détail » de l'autre
  session restent hors commit) : derrière `APP_RELIRE_ANNONCES_CONTACTS_NUIT=1` (**éteint**), le run ajoute les annonces du
  panier (plafond 600, un filet) et marque « remis » **après** leur relecture seulement.
- **`scheduled/run_nuit_contacts_et_recherches.ps1`** : liste + fiches, puis `run_recherches_actives.ps1` **inchangé**, lancé
  comme aujourd'hui, **jamais avant 02:00**. `-SansListe` = ancien comportement. ⚠ **Après un refus de Hektor pendant la
  liste, les recherches ne partent pas** (sauf `-RecherchesMalgreRefus`) — **à trancher par Frédéric**.
- **`scheduled/installer_tache_nuit_contacts.ps1`** : à blanc par défaut (montré : départ `02:00+01:00` → `00:20+01:00`,
  limite `PT2H` → `PT4H`) ; `-Appliquer` en administrateur vérifie chaque réglage ; `-Retour` remet l'ancien.
- **Essais : 62 contrôles VERTS** (`test_liste_contacts_nuit.py`) ; essais existants du run verts.
- ⭐ **SIMULATION SUR UNE COPIE DE LA BASE** (vraie base en lecture seule) : normalisation des contacts avant (37 s), pose des
  8 503 pages fraiches, purge des **2 256 pages** au-delà de 8503, normalisation après (38 s). Sur `hektor_contact` :
  - **32 472 négociateurs changent** (32 470 contacts actifs) : 16 257 vide → compte agence « 2 » ; 6 696 « 25 » → « 2 »
    (deux comptes agence) ; ⚠ **9 334 vide → un négociateur nommé** (n° 41 : 1 716, n° 31 : 1 167, n° 9 : 1 161, n° 17 :
    1 126, n° 7 : 1 066…) ; 162 d'un négociateur à un autre ; 19 deviennent vides ; 4 entre agence et nommé ;
  - **0 état archivé changé, 0 lien de couple changé**, 10 contacts nouveaux au miroir ;
  - ⛔ **NON MESURÉ** : ce que l'app fait d'un négociateur rempli (qui voit ces 9 334 contacts) et la taille du premier envoi
    vers Supabase (~32 000 fiches changées d'un coup). À mesurer avant la bascule.
- ⚠ **TROUVAILLE HORS CHANTIER** : les pages `list_contacts_*_update` du run gardent aussi des pages périmées (24 du 05/06 et
  4 du 30/10 côté actifs, 6 côté archivés). Relues en dernier, elles gagnent : **41 contacts** y ont un négociateur différent
  de Hektor aujourd'hui (ex. 95780 : « 0 » le 05/06, « 2 » aujourd'hui → vide chez nous, même après la simulation). Pages du
  run : non touchées, à trancher.
- ⏰ **Reste, chaque geste sur « vas-y »** : (1) mesurer l'effet des 9 334 dans l'app et la taille de l'envoi ; (2) trancher
  « recherches après un refus » ; (3) basculer la tâche (`-Appliquer`, administrateur) ; (4) allumer l'interrupteur du run ;
  (5) après la 1re nuit et le rapport, la purge ; (6) les archivés le dimanche suivent seuls (`--scope auto`).

## 49. LES 9 342 « SANS NÉGOCIATEUR » : CE QUE LA RÉPARATION CHANGERAIT DANS L'APP *(03/11, « oui fais les mesures » ; lecture seule)*

- **Qui ils sont** : 9 342 contacts actifs (9 334 dans la simulation, à quelques fiches près) qui ont un négociateur nommé chez
  Hektor et AUCUN chez nous. Chacun figure deux fois dans nos pages : page du 23/06 (avec négociateur) et page du 30/03
  (`id_negociateur` NULL, réponse de Hektor en mars). La page de mars gagne à la normalisation. Leur `datemaj` Hektor est
  surtout de 2025 : le négociateur a été posé sans bouger la date, le run ne pouvait pas le voir.
- **Dans la couche envoyée à l'app** (`phase2.sqlite`, lien par `hektor_target_id`) : seuls les contacts « éligibles » partent
  (`-ContactsEligibleOnly`). Sur les 32 473 changements de négociateur, **4 383 sont envoyés à l'app** : 2 602 « vide → nommé »
  (tous liés à une annonce), 799 « vide → agence », 892 « 25 → 2 », 86 « nommé → autre », 4 entre agence et nommé.
  Les 28 090 autres ne sont pas dans l'app aujourd'hui.
- **Qui voit quoi (RLS `app_contact_current_select_scoped`)** : tout utilisateur au périmètre « réseau » voit tous les
  contacts. **Les 6 comptes actifs (4 admin, 2 commerciaux) sont TOUS au périmètre « réseau »** ⇒ **aucun changement de
  visibilité aujourd'hui**. L'annuaire des contacts n'applique pas le filtre « mes contacts » du commercial
  (`applyContactFiltersToQuery`, sans portée ; la portée ne s'applique qu'aux annonces, mandats, archives, brouillons).
- **Ce qui change à l'écran** : la colonne et le filtre « Commercial » (2 602 contacts sortent de « Sans commercial ») et le
  nom d'agence (1 690 passent de Firminy à Saint-Étienne, surtout les « 25 → 2 » ; 358 « Ambert » ne diffèrent que par des
  espaces). Sur les 2 602, **2 140 reçoivent le négociateur de l'annonce à laquelle ils sont liés** ; 79 un autre ; 383 dont
  l'annonce n'a pas de négociateur connu. Seuls 12 contacts tomberaient au nom d'un des 2 commerciaux actifs sans passer par
  leur bien.
- **Le jour où un compte passera au périmètre « agence » ou « négociateur »**, ces contacts suivront leur négociateur Hektor :
  c'est le comportement voulu par la règle, plus le défaut des pages de mars.
- **L'envoi** : la nuit du 03/11 a poussé 8 193 contacts en 48 s ⇒ ~4 400 de plus ≈ moins d'une minute. Pas de risque de durée.

## 50. LES RECHERCHES APRÈS UN REFUS DE HEKTOR : TRANCHÉ *(03/11, « oui » à la recommandation)*

- **La décision** : on tranche selon CE QUE Hektor refuse.
  - **Refus de la liste, de la connexion, ou frein (429)** = blocage du compte ⇒ la liste s'arrête net et **les recherches
    ne partent pas cette nuit** (« un refus arrête tout ») ; elles relisent toutes les recherches actives la nuit suivante, et
    les gestes de l'app partent chez Hektor à l'instant, sans attendre la nuit.
  - **Refus d'UNE fiche (403 sur `ContactById`)** = cas isolé connu (5 fiches mises de côté depuis mai, contre 7 659
    introuvables) ⇒ la fiche est mise de côté (`http_403_forbidden`, comme le fait `sync_contact_details`), les fiches
    s'arrêtent pour la nuit, **les recherches partent**.
  - (Frédéric avait d'abord répondu « elles partent », puis demandé la meilleure option : c'est celle-ci, acceptée.)
- **Le code** : `liste_contacts_nuit.py` sort en **5** pour une fiche refusée (`FicheRefusee`), **3** pour un refus de la liste
  (ou un 429 même sur une fiche), **4** si Hektor ne répond plus. Le lanceur ne retient les recherches **que sur 3**. Tout code
  non nul fait sortir la tâche en 1 (visible au moniteur).
- **Éprouvé** : `test_liste_contacts_nuit.py` **68 contrôles verts** (403 d'une fiche → `FicheRefusee` + mise de côté ; 429 →
  blocage, pas de mise de côté ; le script entier : fiche refusée → 5, page refusée → 3, tout bien → 0). **Le lanceur
  exécuté** sur une copie (faux script de liste, faux script de recherches) : liste 0 → recherches lancées, tâche 0 ; 3 →
  **retenues**, tâche 1 ; 4 → lancées, tâche 1 ; 5 → lancées, tâche 1 ; `-SansListe` → la liste n'est pas appelée, recherches
  lancées, tâche 0.

## 51. LA BASCULE POUR LA NUIT DU 03 AU 04/11 *(03/11, « Oui, pour cette nuit »)*

- ✅ **`.env` : `APP_RELIRE_ANNONCES_CONTACTS_NUIT=1` posé** (copie du fichier gardée avant ; vérifié : le run le lit).
  Sans la liste de nuit, le panier reste vide : l'interrupteur seul ne change rien.
- ⏳ **La tâche** : `scheduled/installer_tache_nuit_contacts.ps1 -Appliquer`, à lancer par Frédéric dans une PowerShell
  ADMINISTRATEUR. Vérifié avant : tâche « Ready », ni elle ni le run ni le balayage ne tournaient ; le moniteur la surveille
  déjà en « critical » sur `LastTaskResult` (même nom de tâche).
- **Ce qui se passera cette nuit** : 00:20 départ ; attente que le worker ait fini le balayage des photos (au plus 01:55) ;
  liste des actifs (~1 h 18, ~8 500 requêtes) ; fiches à relire (~240, ~7 min) ; 02:00 les recherches, inchangées ; 04:00 le
  run relit les annonces du panier (~160, ~5 min) et normalise les pages fraîches. ⚠ **Les pages de mars restent** jusqu'à la
  purge (après lecture du rapport) : l'effet sur les négociateurs ne sera complet qu'après elle.
- ⏰ **À vérifier le 04/11 au matin** : le journal `logs/scheduled/nuit_contacts_*.log` et le rapport
  `logs/liste_contacts_nuit/rapport_active_*.json` (code, pages, fiches relues, panier) ; la ligne « [liste de nuit] » du run ;
  la durée du run et de la descente ; puis décider la purge.
- **Retour arrière** : `installer_tache_nuit_contacts.ps1 -Retour` (administrateur) et retirer la ligne du `.env`.
- ⚠ **Relu le 03/11 au soir (lecture seule) : LA TÂCHE N'EST PAS BASCULÉE.** Action encore sur `run_recherches_actives.ps1`,
  départ `02:00:00+01:00`, limite `PT2H`. **Cette nuit se déroule donc comme avant** : pas de liste, pas de fiches relues.
  L'interrupteur du `.env` est **sans effet** : la table `liste_nuit_contact` de `data/hektor.sqlite` (née au passage à blanc)
  n'a pas encore les colonnes `relu_le` et `remis_au_run_le`, et `load_panier_contacts_nuit` rend alors un panier vide (garde vérifiée
  dans le code). Frédéric : « note le à vérifier ». ⏰ **À reprendre** : lancer l'installeur en administrateur, puis je relis
  la tâche ; le contrôle du matin glisse au lendemain de la première vraie nuit.

## 52. « AJOUTER UN CONJOINT » À UNE PERSONNE SEULE — AUDIT *(03/11 soir, « vas, mais avant audit pour savoir ce qui existe déjà et ce qui a été fait » ; lecture seule, rien codé)*

**Audit limité à l'objet CONTACT et à son lien de couple.** Annonce, recherche, relation au bien, transaction, mandat, document, RDV : non touchés par
ce geste, sauf la question des liens au bien (plus bas, non mesurée).

**Ce qui existe déjà (code et base, relus)** :
- **Créer un couple** depuis l'app : la paire naît chez nous à la seconde (`app_contact_creer_conjoint`, interrupteur `couple_nait_complet = on`) ;
  le worker range la seconde fiche de Hektor (`rangerSecondeFicheDuCouple`, `contact_seconde_fiche_from_api.py`). Prouvé (§26).
- **Modifier le conjoint** d'un couple nommé (pièce E, §28-29) et **compléter** une place 2 vide connue de Hektor (pièce F, §34) : fenêtre
  « Modifier / Compléter le conjoint », `app_edit_conjoint_optimistic`, worker 748383f (groupe `contactCoupleAll`, relecture de la seconde).
  Crans `contacts_couples_fiche` et `contacts_couples_modif` sur « on ».
- **Rattacher** une fiche existante comme conjoint, chez Hektor : UNE requête GET `contacts-create-transformeContactToConjunct`
  (`conjoint`, `refCouple`). Prouvée sur 3 fiches fictives (§36, réponse `{"success":"ok"}`) et sur le vrai cas EA32621 (§39, réponse VIDE,
  lien confirmé par `ContactById`, liens au bien gardés). ⚠ Le formulaire que Hektor ouvre ensuite ne doit JAMAIS être enregistré (E6).
- **Relire deux fiches tout de suite** : `refresh_contact_inproc.py`, prouvé sur EA32621 (§43). Indispensable : un rattachement change
  `datemaj` mais pas `dateLastTraitement`, la nuit ne le voit pas (§40).

**Ce qui n'existe PAS** : aucun bouton « Ajouter un conjoint » sur une personne seule ; aucun travail du worker pour `transformeContactToConjunct`
(la seule trace dans le dépôt est une copie du code de la page Hektor dans `Console/exports/`) ; le rattachement d'EA32621 a été fait à la main.

**Usage réel à ce jour (mesuré)** : depuis le 31/10, 5 créations de contact par l'app, dont 2 couples (les essais) ; 3 modifications de conjoint,
toutes sur le couple d'essai 20000031. « Compléter le conjoint » n'a jamais servi en vrai.

**Les cas** (contacts actifs de l'app, nature calculée la nuit) : personne seule 22 477 ; couple 3 104 (dont les 123 « couple dans le nom »,
personnes seules chez Hektor) ; conjoint sans prénom 1 927 ; coquilles masquées 11 147 (dont les 680 cas simples).

**Le chemin proposé (non décidé)** — deux gestes déjà prouvés, enchaînés :
1. créer le conjoint comme un nouveau contact (création de l'app, il naît complet chez nous à la seconde) ;
2. un **nouveau travail du worker** « rattacher un conjoint » : `transformeContactToConjunct` (conjoint = le nouveau, refCouple = la personne),
   **relire `refCouple` des deux fiches** (la réponse vide ne prouve rien), puis relire les deux fiches chez nous ; et à la seconde, chez nous,
   relier les deux lignes comme la paire de la création.
⭐ **Le même travail sert aux 680 coquilles** (conjoint = la coquille) : un seul geste neuf pour les deux sujets.

**Ce que ça pourrait casser ailleurs** :
- la personne passe chez Hektor au formulaire de COUPLE et à la civilité « M./Mme » (vu sur EA32621) : le worker sait déjà éditer ce
  formulaire (748383f) ; notre nature la verra « couple » à la relecture ;
- un nouveau type de travail = les trois verrous (contrainte, droits, distribution) + le worker + l'écran : oublier la distribution le laisse
  « pending » à vie ;
- un échec entre les deux gestes laisse un conjoint créé mais non rattaché : à afficher, pas à défaire en silence ;
- le dossier du worker porte des lignes non commitées de l'autre session : un redémarrage les charge aussi.

**Non mesuré** : si Hektor relie le nouveau conjoint aux biens de la personne (sur EA32621 la coquille avait déjà son propre lien) ; si la
transformation garde les recherches et l'e-mail RGPD de la personne ; ce que deviennent nom et prénom de la place 2 quand le conjoint a un
e-mail ou un téléphone (vu sur les fictives : recopiés).

**À trancher par Frédéric** : (a) un seul choix « nouveau conjoint », ou aussi « une fiche existante » (recherche par nom, comme Hektor) ;
(b) qui a le bouton (admins d'abord, comme les autres crans) ; (c) les liens au bien du nouveau conjoint (rien, ou les mêmes que la personne) ;
(d) l'ordre : ce geste d'abord, les 680 ensuite avec le même travail.

**Décisions de Frédéric (03/11 soir)** : (a) **les deux** — un nouveau conjoint ET une fiche existante ; (b) **les deux** — compris comme
« admins et négociateurs », c'est-à-dire le même cran que « Compléter le conjoint » (`contacts_couples_modif = on`, droit de gérer les contacts),
à confirmer ; (c) **les mêmes biens** que la personne ; (d) **« tu m'expliques »** — l'ordre est expliqué, pas encore tranché.
⭐ Pour (c), le geste existe déjà : `link_hektor_mandant` (`selectnouveauproprio_sup`, l. 17652), qui sait dire « déjà relié » par l'API
avant d'écrire — il ne doublera donc pas un lien que Hektor aurait posé lui-même au rattachement.

**✅ BASCULE FAITE le 03/11 à ~16:25 par Frédéric (PowerShell administrateur, « TOUT VERT »).** Relue par moi (lecture seule) : action
`run_nuit_contacts_et_recherches.ps1`, départ `00:20:00+01:00`, limite `PT4H`, compte admin, état Ready, **prochain départ 04/11 à 00:20**
(horloge du serveur = UTC+1, cohérente). L'interrupteur `.env` est en place (ligne 118). ⏰ **Le 04/11 au matin** : le journal
`logs/scheduled/nuit_contacts_*.log`, le rapport `logs/liste_contacts_nuit/rapport_active_*.json`, la ligne « [liste de nuit] » du run, les
durées du run et de la descente, EA32621 / 10260586 en couple ; puis décider la purge des pages de mars.

## 53. PIÈCE G — « AJOUTER UN CONJOINT » : ÉCRITE ET ÉPROUVÉE HORS LIGNE, RIEN N'EST POSÉ *(03/11 soir, « Vas-y »)*

**Ce qui est écrit (commits locaux df8dc7e, 80d4006, edbd476), dans l'ordre du geste :**
- **L'écran** (`App.tsx`, fiche contact V2) : un bouton « + Ajouter un conjoint » sur la fiche d'une **personne seule** (nature lue pour la
  fiche ouverte, pas notaire, sans conjoint connu, active, connue de Hektor), derrière le cran **`contacts_couples_ajout`** et le droit de gérer
  les contacts. Fenêtre à deux choix : **un nouveau contact** (nom obligatoire, prénom, portable ou e-mail, e-mail RGPD coché comme à la
  création) ou **une fiche existante** (recherche dans l'annuaire, la fiche elle-même écartée). Nouveau = la création habituelle (personne
  seule), PUIS le rattachement avec son numéro. Chaque refus de la base est dit en clair (13 raisons). Suivi de l'action : les 8 habillages,
  la liste des actions, `ConsoleJobType`, les gestes qui préviennent.
- **La base** (`supabase/patch_couple_phase3g_ajouter_conjoint_2026-11-03.sql`) : le cran (posé « off ») ; le type `link_hektor_conjoint`
  aux **trois verrous** (contrainte, droits = règle de la modification d'un contact, distribution au service `actions`) ;
  `app_ajouter_conjoint_optimistic` (vérifie tout, écrit le couple **chez nous à la seconde** avec la photo d'avant, choisit les biens de la
  personne — mandant ou propriétaire, bien vivant, ni marque d'acheteur ni de vente, droit vérifié **bien par bien** — et pose le travail) ;
  `app_conjoint_relier_biens` et `app_conjoint_annuler_optimiste` (pour le worker seulement).
  **Répétition 10/10** dans une transaction annulée (admin simulé, 3 fiches fictives, bien d'essai 63331) : cran fermé refusé, ajout, couple
  chez nous, travail, refus d'un second ajout, témoins notaire et même fiche, distribution, biens, retour arrière à l'identique, droits.
  **Contrôlé après : rien n'est resté.** Retour arrière écrit (`…_INVERSE.sql`, il remet les trois empreintes d'avant).
- **Le worker** (`handleLinkHektorConjoint`) : (1) **avant** — les deux fiches relues par l'API (`phase2/sync/contact_refcouple_from_api.py`,
  neuf, lecture seule ; éprouvé en vrai sur EA32621 : `467326 → 467326`, `467325 → 467326`, et sur une personne seule : vide) ET leur
  formulaire (une porteuse de couple a aussi `refCouple` = elle-même) ; une lecture ratée = refus ; (2) **une seule écriture**
  `transformeContactToConjunct` (conjoint = la seconde, refCouple = la porteuse) ; (3) **la preuve** — `refCouple` relu trois fois ; sans
  preuve : PAS de renvoi, nos fiches remises comme avant, message « vérifier chez Hektor » ; (4) après la preuve seulement, en best-effort : les
  **biens** (rattachements de mandant en file) et la **relecture des deux fiches** (`phase2/contacts/relire_couple_rattache.py` : conjoint,
  personne, nature, envoi des deux — la séquence d'EA32621). Un conjoint NOUVEAU : on attend son numéro seulement si sa création est en file.
  **Essai hors ligne 24/24** (`Console/test_ajouter_conjoint.js`, dont un mutant « ménage à l'envers » et le témoin inverse : l'ancien worker
  n'a pas le geste) ; l'essai voisin des couples reste vert.
- **Écran** : `npm run build` vert ; essai `apps/hektor-v1/test_ajouter_conjoint_ecran.cjs` **24/24** (dont un mutant « archivée en texte »).

**Ce que ça pourrait casser ailleurs, revu** : la contrainte et la distribution sont élargies d'UN type, rien d'autre ne bouge (gardes
d'empreinte) ; les droits suivent la règle existante ; la porte de création n'est pas touchée (le conjoint naît « personne seule ») ;
« Compléter / Modifier le conjoint » ne sont pas touchés ; le bouton est invisible tant que le cran n'existe pas. ⚠ La relecture lance le
calcul de la nature sur toute la table locale (~8 s) : un geste fait pendant le run de nuit écrirait en même temps que lui dans
`phase2.sqlite` (rare ; même risque que l'ouverture d'une fiche aujourd'hui). ⚠ Le fichier du worker porte ~137 lignes NON COMMITÉES de
l'autre session : un redémarrage les chargerait aussi.

**Non éprouvé** : rien n'a été écrit chez Hektor ni posé chez Supabase ; le geste réel, la confirmation par relecture sur une vraie paire
créée par nous, les biens reliés, et l'écran à l'œil (ordinateur ; le téléphone passe-t-il par la même fiche ? non vérifié).

**Les gestes, dans l'ordre, chacun avec son accord** : (1) pousser (le bouton reste invisible : pas de cran) ; (2) poser le patch (cran
« off ») ; (3) redémarrer les 4 services worker, file vide (avec l'accord de l'autre session sur ses lignes) ; (4) cran « admin » ;
(5) essai réel sur deux fiches FICTIVES (créées par l'app, nature calculée et envoyée comme au §35), Frédéric connecté à Hektor pour
relire ; (6) supprimer les fictives par l'app ; (7) cran « on » quand tu le décides.

**✅ GESTE 1 — POUSSÉ par Frédéric** (86dd65d au sommet de origin/main, vérifié). **✅ GESTE 2 — PATCH POSÉ le 03/11 au soir** (accord :
« FAIS LE TU AS MON ACCORD » ; migration `couple_phase3g_ajouter_conjoint_2026_11_03`, gardes passées) : **6/6 contrôles OK** (cran « off »,
contrainte, distribution, droits, porte de l'écran ouverte aux connectés et fermée à l'anonyme, fonctions du worker fermées). Nouvelles
empreintes : distribution `1d1409b5…`, droits `4e1acaa5…`. File des travaux : 0.
⏭ **GESTE 3 — redémarrage** : le geste n'a besoin que du service **HektorConsoleWorkerActions** (`link_hektor_conjoint` et les rattachements
de mandant y sont). ⚠ Les lignes non commitées de l'autre session touchent la signature Youtrust et la génération du document de mandat :
ce sont des travaux du service **Documents**. Redémarrer SEULEMENT Actions charge notre geste sans mettre leur code en service là où il
s'exécuterait.

**✅ GESTE 3 — REDÉMARRÉ par Frédéric** : vérifié par l'heure des processus — ⚠ **les QUATRE services** ont démarré à 17:49:02-04 (Actions
17:49:02, Admin 17:49:03, Documents 17:49:04, SyncLight 17:49:04), après l'écriture du worker (16:45:03). Le geste est donc chargé. ⚠ Mais
les lignes NON COMMITÉES de l'autre session (signature Youtrust, mandataire du document de mandat) sont désormais EN SERVICE dans
Documents : à signaler à l'autre session (Youtrust reste derrière son interrupteur ; la génération du document de mandat, elle, passe par ce code).

## 54. PIÈCE G — L'ESSAI RÉEL : LA CHAÎNE ENTIÈRE MARCHE *(03/11 ~17:50-18:00, « Oui, sans bien »)*

- **Cran** `contacts_couples_ajout = admin` (16:51:52 UTC).
- **Fiche fictive Un créée par l'écran** (compte formation, Propriétaire, personne seule, `@example.com`, e-mail RGPD décoché — vérifié dans la
  charge : `send_rgpd_email = false`) : **20000036 ↔ 606177** ; nature calculée et envoyée (`nature_des_fiches.py` + envoi de la fiche) →
  `personne_seule`.
- **Par l'écran (Chrome de Frédéric, admin)** : fiche Un → le bouton **« + Ajouter un conjoint »** est là → « Un nouveau contact » : ESSAI AJOUT /
  Deux / e-mail fictif / RGPD décoché → « Ajouter le conjoint ».
- **Le déroulé, relevé au journal du travail** : création de Deux (**20000037 ↔ 606178**, 16:56:10 → 16:56:28) ; `link_hektor_conjoint` pris par
  le service actions à 16:56:29 ; contexte négociateur (compte formation) ; **avant** : `606177 → ""`, `606178 → ""` ; **une** requête de
  transformation (réponse `{"success":"ok"}`) ; **preuve au 1er essai** : `606177 → 606177`, `606178 → 606177` ; biens : 0 (aucun, comme prévu) ;
  **relecture des deux fiches en 41 s** (conjoint 14,4 s, personne 13,6 s, nature 8,2 s, deux envois) ; travail `done` à 16:57:26.
- **Chez nous après** : 20000036 `couple`, résumé « nommé » sur 20000037 (prénom Deux), 20000037 `conjoint` rattaché à 20000036.
  **À l'écran** : la fiche Un montre la pastille « Couple » et les deux onglets Un / Deux ; le bouton a disparu (normal : elle n'est plus seule).
- **Nettoyage par l'app** : Un supprimée (« tout le foyer ») puis Deux supprimée → 2 travaux `done` ; **0 reste** chez Supabase, dans la couche
  locale et dans le miroir. File : 0. Onglet fermé ; les deux onglets de Frédéric non touchés.

**Défauts vus pendant l'essai, NON corrigés (à décider)** :
1. **La civilité devient « _ »** après la transformation (Hektor), et l'écran l'affiche devant le nom : « _ Un ESSAI AJOUT ». Le traducteur des
   codes de civilité (P1) ne connaît pas ce « _ ». Cosmétique, mais visible.
2. **La fenêtre est brute** : le choix « nouveau / existante » ne montre pas lequel est actif, la case RGPD est énorme et son libellé passe sous
   les boutons ; un clic de formulaire automatique ne la décochait pas (un vrai clic, si). À reprendre au propre (style des autres fenêtres).
3. **Après l'envoi, l'écran a ouvert la fiche du nouveau conjoint** (le suivi de la création le fait) : le message de réussite de la fenêtre
   n'est pas vu. Sans gravité, mais pas voulu.
4. Le nouveau conjoint a été affiché « Non affecté · Groupe GTI Firminy » côté négociateur (compte de la session, pas celui de la personne) :
   à vérifier — il devrait sans doute prendre le négociateur de la personne.
**Non éprouvé en réel** : le choix « une fiche existante », les biens reliés, un négociateur, le téléphone.

## 55. CRAN OUVERT À TOUS ET LES 4 DÉFAUTS CORRIGÉS *(03/11 soir, « Ouvre le cran à tout le monde et corrige les défauts, fais une optimisation ergonomique et graphique de la modale »)*

- **Cran** `contacts_couples_ajout = on` (17:13:30 UTC) : le bouton est visible pour tous ceux qui ont le droit de gérer le contact
  (dès que le nouvel écran est en ligne pour la fenêtre refaite ; l'ancienne fenêtre marche déjà).
- **1. Civilité « _ »** : un code de couple à une place vide (« _ », « _Mr/Mme » — 2 fiches) s'affichait tel quel. Règle commune à la nuit
  (`build_contacts_layer.py`, `civilite_affichee`) et à l'écran (`civiliteAffichee`) : on ne garde que les places remplies (« _ » → rien,
  « _Mr/Mme » → « Mr/Mme », « M_ » → « M. ») ; un code aux deux places remplies hors table reste tel quel (témoin « m_mme »). L'import des
  mandats de recherche ne voit aucune différence (empreinte identique, vérifié). Essais 5/5 (serveur) et 3 contrôles écran.
- **2. La fenêtre refaite** (`ajout-conjoint.css`, même famille que l'assistant « Nouveau contact ») : en-tête avec la personne, un vrai
  sélecteur à deux positions (« Un nouveau contact » / « Une fiche existante », état actif visible et dit aux lecteurs d'écran), champs en
  grille, case RGPD de taille normale avec son explication, liste de fiches à choisir comme des boutons radio, encart « ce qui va se
  passer », erreurs en rouge, **réussite qui reste affichée** jusqu'à « Fermer », Échap pour fermer, focus sur le premier champ ; au
  téléphone : feuille plein largeur en bas, une colonne.
- **3. La fiche du conjoint ne s'ouvre plus** : la création du conjoint n'est plus suivie par l'écran (c'est ce suivi qui ouvrait sa fiche) ;
  seul l'ajout du conjoint est suivi.
- **4. Le conjoint naît chez le négociateur de la personne** (son e-mail, son numéro, son agence) ; un négociateur qui n'a pas le droit de
  créer chez ce collègue retombe sur son propre compte, comme la création habituelle.
- Build vert ; essai écran **34/34** ; commit c8e7239 (seules mes lignes de `App.tsx` ; l'autre session y a des modifications en cours,
  laissées dans la copie de travail). **Non poussé, pas vu à l'écran** : à pousser, puis l'ouvrir sur une vraie personne seule SANS enregistrer
  (ordinateur et téléphone). ⚠ La correction de la civilité côté serveur agit à la prochaine nuit (ou à la relecture d'une fiche).

- **Vu en ligne après le push (Chrome de Frédéric, fiche d'une vraie personne seule, RIEN enregistré)** : le bouton et la fenêtre
  s'ouvrent, mais la fenêtre était **écrasée** — marges et retraits à zéro. Cause : la fiche V2 remet à zéro marges et retraits de TOUT
  ce qu'elle contient (`#fcx-root *`, `fiche-contact-v2.css` l. 37, un sélecteur d'identifiant qui l'emporte sur nos classes).
  **Correctif** : la fenêtre est rendue hors de la fiche (`createPortal` sur `<body>`, comme deux autres fenêtres de l'app) ; aperçu
  vérifié dans la page en sortant le bloc de la fiche : en-tête, sélecteur, champs, case RGPD, encart et boutons à leur place. Essai 35/35,
  build vert, commit f58e06f. ⏳ À pousser ; non vu au téléphone (je n'ai pas redimensionné ta fenêtre Chrome).

## 56. « LE FOYER, DEUX PLACES » : LA MAQUETTE VALIDÉE, PUIS CODÉE *(03/11 soir, « hausser le niveau… mettre en forme cette modale et les boutons » ; « Oui, code-la »)*

- **Inventaire de la zone couple de la fiche** (méthode de refonte : aucune fonction perdue) : la pastille « Couple · … », les deux onglets
  du foyer (le second en lecture seule, la place vide non cliquable, le numéro de fiche sous chaque nom), « + Compléter le conjoint »,
  « + Ajouter un conjoint », le crayon de l'onglet du conjoint (« Modifier le conjoint »), la fenêtre d'ajout.
- **Maquette** (artifact privé `E6dUpoN1PWKhxaC3xVpbzW`, 7 planches) : l'idée directrice est la PLACE — chaque personne est une pastille à ses
  initiales ; la place du conjoint est en pointillés ; elle se remplit pendant la saisie ; le lien devient plein et vert quand le couple est
  formé. Palette de la fiche (magenta = l'action, doré = « à compléter », vert = « formé »), police Hanken Grotesk. **Validée telle quelle.**
- **Codé (d4fe8f8)** : sur la fiche, la carte « Ajouter un conjoint » à deux places (remplace la barre beige) ; les onglets du couple avec la
  place de chacun (numéro de fiche gardé) ; le bloc doré « Compléter le conjoint » avec son explication. La fenêtre : le foyer en tête (la
  personne, le lien, la place du conjoint qui se remplit), le choix en deux cartes, les champs en grille, l'e-mail RGPD en interrupteur, les
  biens partagés (ceux que la fiche connaît déjà, aucune lecture de plus), « Former le couple » ; la réussite (« X et Y forment un couple »,
  le lien vert, les biens) avec « Voir la fiche de Y », qui passe par la porte EXISTANTE de l'adresse (précédent / suivant) ; au téléphone,
  une feuille qui monte du bas. Mouvement limité à l'ouverture et au lien de la réussite ; respecte « réduire les animations ».
- **Écart à la maquette, assumé** : l'avatar de l'en-tête de la fiche garde l'icône du type de contact (il porte la couleur du type) ; les
  initiales du couple sont dans les onglets juste en dessous.
- Build vert ; essai écran **43/43** (dont les aides neuves jouées : initiales, biens partagés sans achats) ; essais voisins verts.
  **Non poussé, pas vu en ligne.**

- **Vu en ligne (03/11 soir, Chrome de Frédéric, RIEN enregistré, 0 travail créé — vérifié en base)** : la carte « Ajouter un conjoint »
  sur une vraie personne seule ; la fenêtre (le foyer en tête ; la saisie d'un prénom remplit la place — « EM » — et le lien passe au
  magenta ; l'interrupteur RGPD ; l'encart des biens) ; le mode « fiche existante » (recherche, liste avec initiales, la fiche choisie
  remplit la place, « Former le couple » s'active) ; Échap ferme. Sur un couple nommé et sur un couple à compléter : les places dans les
  onglets, le bloc doré et « Compléter le conjoint ».
- **Trois retouches** (f1ea578, aperçu vérifié en injectant la feuille dans la page) : onglets du couple en COLONNE (sur le volet étroit,
  les noms étaient coupés : « JOLY … », « Conjo… ») ; les initiales de la personne PASSENT au-dessus de la place « + » (elles étaient
  masquées) ; la fiche choisie reste magenta au survol. ⚠ Noté, non changé : la recherche de l'annuaire trouve aussi par le nom du
  négociateur (« durand » ramène les contacts d'une négociatrice de ce nom) — c'est la recherche commune des choix de contact.

- **✅ Retouches EN LIGNE, vues** (déploiement de 1459489, Chrome de Frédéric, rien enregistré) : onglets du couple en colonne, noms entiers
  (« JOLY Cindy » / « Conjoint · place vide ») ; les initiales de la personne devant la place « + » sur la carte. ⏳ Restent non vus en vrai :
  la fenêtre au téléphone, et une vraie réussite (le prochain usage réel la montrera).

## 57. LA PREMIÈRE VRAIE NUIT DES CONTACTS, CONTRÔLÉE *(04/11 matin, « Le run de nuit est fini, vérifie ton travail » ; lecture seule)*

- **La liste** (`nuit_contacts_2026-11-04_00-20-01.log`, code 0) : départ prévu à 00:20, mais la garde « file vide » a attendu
  **26 min** (00:20 → 00:46). Le worker vidait encore les **1 000 photos** posées par le balayage de 23:00 (toutes `done`).
  Le tour REEL est parti à 00:48. Il s'est arrêté sur l'**heure limite de 01:55**, à la page **8 114 sur ~8 504** (162 280 contacts),
  avec 0 recul, 0 page hors ordre et **0 refus**. Le tour n'est donc PAS terminé (`termine_le` vide, dernier numéro lu 596439).
  ⭐ Le code le reprend PAR NUMÉRO la nuit suivante (`lire_la_liste`, « reprise du tour ») : il reste ~390 pages, quelques minutes.
- **Les fiches** : 239 à relire, **180 relues** avant 01:58, 0 introuvable, 0 illisible. Il en reste 59 (dont 35 jamais lues)
  pour la nuit suivante.
- **Les requêtes chez Hektor** : 8 114 pages et 180 fiches, plus la connexion, en 5 878 s. Le volume est celui que Frédéric a accepté au §50.
- **Les recherches** sont parties à 02:00 pile, comme avant : 4 026 contacts en 6 685 s (les nuits d'avant : 6 669 à 6 740 s),
  code 0. Elles n'ont pas changé.
- **Le run de 04:00** : la ligne « [liste de nuit] » indique 180 contacts relus et **132 annonces relues en plus** (plafond 600).
  Le run a fini à 06:19:22, code 0 (les jours d'avant : 06:12 à 06:18), donc sans allongement visible.
  Hors chantier : Matterport est en échec 2/2 pour la 2e nuit, avec un **401 « unauthorized »** de leur API (déjà vu le 03/11, §40), non bloquant.
- **La descente de 06:45** : pas encore finie au moment du contrôle (06:40), donc non mesurée ici.
- **La civilité « _ »** (pièce G) : les 2 fiches « _Mr/Mme » s'affichent maintenant « Mr/Mme … » chez Supabase, sans tiret bas.
  La traduction de la nuit marche.
- **Le couple d'essai** 20000036/37 (606177/78) n'est pas revenu : 0 fiche et 0 lien chez Supabase. Dans la nuit, aucun autre
  `link_hektor_conjoint` que celui de l'essai d'hier : personne n'a encore utilisé le geste pour de vrai.
- ⚠ **EA32621 (10260586) n'est PAS « couple », et c'est la règle, pas une panne.** Ce que la nuit a calculé à 06:05 :
  10260585 = `case_conjoint_vide` (lien vers 10260586, rôle `menage_resolu`) ; 10260586 = `personne_seule`, `couple_json.etat = vide`.
  Hektor a rangé la civilité sous le code **« _Mr/Mme »** (place 1 vide), qui n'est pas un code de couple (`CIVILITES_COUPLE`),
  et la place 2 n'a pas de prénom. Pour la règle de nature, c'est donc une personne seule dont la place 2 est vide :
  la coquille est masquée, la personne reste seule (décision du 02/11, §33).
  ⛔ Mon attente du §39 (« doit voir 467326 en COUPLE ») était donc FAUSSE : je l'avais écrite avant cette règle.
  ⚠ **Ce que ça veut dire à l'écran** : la fiche ne montre ni « Compléter le conjoint » (réservé à la nature `couple` + `vide`)
  ni « Ajouter un conjoint » (réservé à `couple_json` absent ou « aucun » ; la base refuserait de toute façon avec
  `personne_deja_en_couple`, puisqu'une case vide la suit déjà chez Hektor).
  ⭐ **Mesure** : chez Supabase, **9 388 contacts actifs** sont dans ce cas exact (`personne_seule` + état `vide` + lien). Pour eux,
  l'app n'offre AUCUN geste de couple. C'est voulu au sens où ajouter une fiche par-dessus une case existante ferait un doublon.
  Le geste qui leur irait serait « remplir la place 2 existante » (comme « Compléter »), mais ouvert aux personnes seules.
  **Rien n'est décidé : c'est à Frédéric.**
- ⏰ **Reste à faire** : la nuit du 05/11 doit finir le tour (« reprise du tour … à la page 8114 » puis `tour_termine`). Ensuite
  seulement, la purge des pages de mars devient possible : `--purger-pages-perimees` à blanc, puis `--confirmer` avec accord.
  Avant cela, elle est refusée par construction (« aucun tour REEL terminé »).
  ⚠ Si le balayage des photos pose encore 1 000 travaux à 23:00, chaque nuit perdra ~26 min de liste. Un tour fera alors un peu plus
  d'une nuit, ce qui reste sans gravité grâce à la reprise.

## 57 bis. ⛔ CORRECTION DU §57 : EA32621 EST BIEN UN COUPLE PAR SA CIVILITÉ, LA RÈGLE RATE UNE GRAPHIE *(04/11, « mais EA32621 a pourtant Mr/Mme ?? »)*

- Frédéric a raison. La règle de nature compte la civilité **« Mr./Mme »** comme un signe de couple (`CIVILITES_COUPLE`,
  `nature_des_fiches.py` l. 78). Mesure du miroir local : **25 300 fiches « couple »** portent cette civilité.
- EA32621 porte la même civilité, mais sous une **autre graphie** : **« _Mr/Mme »**, sans point et avec une place 1 vide. C'est la forme
  que Hektor écrit après « Transformer en couple » sur une personne sans civilité. Le test est une égalité exacte : il ne la reconnaît pas.
- ⛔ Le §57 disait « c'est la règle, pas une panne » : c'est FAUX. C'est un trou de la règle, sur une graphie que personne n'avait vue.
  Aujourd'hui il ne touche que **les 2 fiches d'EA32621** (1 porteuse, 1 coquille), mais chaque futur rattachement d'une coquille
  à une personne sans civilité produira la même graphie.
- Les **9 388** personnes seules à place 2 vide du §57 sont un AUTRE sujet : leurs civilités sont vide, « M. » ou « Mme. », jamais « Mr/Mme ».
- Correctif possible (rien n'est fait, il faut un « vas-y ») : reconnaître aussi « _Mr/Mme ». EA32621 passerait alors « couple » + « vide »,
  et la fiche montrerait « Compléter le conjoint ».

## 57 ter. « _Mr/Mme » RECONNU PAR LA RÈGLE DE NATURE : AUDITÉ, CODÉ, ÉPROUVÉ, PAS ENCORE EN SERVICE *(04/11, « Oui, vas-y » puis « audit pour être sûr, normalement on avait déjà repris »)*

- **L'audit : ce qui existait déjà.** « _Mr/Mme » n'était traité que pour l'AFFICHAGE (§55 : `civilite_affichee` de la nuit et
  `civiliteAffichee` de l'écran, « _Mr/Mme » → « Mr/Mme »). Pour la NATURE, rien : `nature_des_fiches.py` est le seul endroit qui juge
  une civilité de couple. Aucune fonction ni vue chez Supabase ne teste « M_Mme » ou « Mr./Mme » (mesuré dans `pg_proc` et `pg_views`).
- **Ce qui était déjà décidé, et que la règle ne tenait pas** : au §37, le pire cas annoncé du rattachement d'une coquille était
  « un couple à place 2 vide, déjà géré par Compléter le conjoint ». Au §39, l'attente était « 467326 en COUPLE, état vide → Compléter ».
  La correction ne fait que tenir ce qui était déjà convenu.
- **Pourquoi le « _ » suffit** : c'est le formulaire de COUPLE de Hektor, avec une civilité par place. Au §39, Hektor montrait bien
  467326 dans un formulaire de couple. Toutes les civilités à « _ » du miroir local sont déjà des couples ou des deuxièmes fiches
  (M_Mme 416 couples, Mme_M 9, Mme_Mme 4, M_M 2…), sauf la porteuse d'EA32621.
- **Le code** : `civilite_de_couple()` (`CIVILITES_COUPLE` OU une civilité qui contient « _ ») remplace l'égalité exacte dans `nature()`.
  L'ordre ne change pas : une deuxième fiche reste jugée d'abord comme deuxième fiche, et un notaire reste notaire.
- **Éprouvé** : `test_nature_des_fiches` donne **29/29** (dont le cas EA32621, le témoin inverse « Mr/Mme » sans « _ » qui reste seule, et le notaire).
  ⭐ Sur la table entière (lecture seule, rattachement allumé comme la nuit), **l'ancienne règle redonne la table de la nuit à l'identique**
  (356 835 sur 356 835). **La nouvelle ne change qu'UNE fiche** : 10260586, `personne_seule` → `couple`, place 2 `case_vide`.
- **En service à la prochaine nuit** (étape « nature » du run de 04:00, puis l'envoi). Rien n'a été écrit chez Supabase ni chez Hektor.
  ⏰ **Le 05/11** : 10260586 en `couple` chez Supabase, et sa fiche doit montrer « Couple · conjoint à compléter » avec le bouton.
- **Retour arrière** : revenir sur ce commit. La nuit suivante recalcule toute la table.

## 58. AUDIT DES GESTES CONTACTS (§42, POINT 5) : CE QUI EST DÉJÀ FAIT, CE QUI MANQUE *(04/11, « avant, audit de ce qu'on a déjà fait, et ensuite les gestes si nécessaire » ; lecture seule, rien codé)*

**Déjà fait** — sources : chantier ⑧ (8a, 8a bis, 8a-A, 8a-B, 8a6, C), `AUDIT_PORTES_DE_CREATION` §2 quinquies, ce chantier (pièces E, F, G).
Remesuré dans le code d'aujourd'hui (`console_job_worker.js`, fonctions chez Supabase) :
- **Créer un contact, créer un mandant** : la fiche est écrite au clic (`app_create_contact_optimistic`, `app_create_mandant_contact_optimistic`).
  Elle est relue après Hektor (`executerCreationContactHektor` l. 19611, `executerCreationMandantContact` l. 21376), et la paire de numéros est apprise
  (8a bis, 21/10). Le contrôle au retour est en place (8a6).
- **Modifier un contact ou un mandant** (une seule fonction, `app_edit_contact_optimistic`) : 12 colonnes et le commentaire sont écrits au clic, et le
  contrôle au retour est en place (8a-A, 8a-B). La fiche est relue après Hektor (l. 19690), et **le conjoint aussi** (l. 19706, pièce E).
- **Archiver ou réactiver** : écrit au clic (`app_console_archiver_contact_optimistic`), relu après (l. 19814).
- **Supprimer** : la fiche disparaît de l'app sans trace (prouvé le 03/11, §54).
- **Recherches (ajouter, modifier, supprimer)** : relues après (l. 19912, 21114, 21233). Le « rafraîchissement perdu » par le numéro Hektor est
  corrigé depuis 8a bis (21/10).
- **Relier ou retirer un mandant d'un bien** : la ligne `app_relation` est posée au clic (30/09).
- **Conjoint** : « Modifier » (E), « Compléter » (F), « Ajouter » (G). Seul « Ajouter » relit les DEUX fiches ET recalcule la nature
  (`relire_couple_rattache.py`).
- **Un couple fait directement dans Hektor par un négociateur** : depuis le 04/11, la nuit des contacts relit les fiches dont la date a bougé (§57).

**Ce qui manque — trois trous, aucun corrigé :**
1. **La nature n'est recalculée que la nuit**, sauf après « Ajouter un conjoint ». Aucune autre fonction au clic ne touche `nature_fiche`
   (mesuré dans `pg_proc`), et une relecture seule renvoie la nature de la veille.
   ⇒ Un contact créé aujourd'hui n'a pas de nature jusqu'au lendemain, donc pas de bouton « Ajouter un conjoint » avant.
   Après « Compléter », la coquille reste `case_conjoint_vide` jusqu'à la nuit : l'effet sur l'écran n'est **pas mesuré**.
2. **Un contact qui n'est pas éligible au cloud n'a jamais de nature chez Supabase.** C'est le cas d'un contact sans bien : la nuit calcule sa nature
   en local, mais l'envoi ne prend que les éligibles. Mesure : **211 fiches chez Supabase sans nature**. Les 211 sont toutes en local, avec une
   nature, et toutes non éligibles (`supabase_sync_eligible = 0`).
   - 209 sont nées chez Hektor et ne sont plus éligibles : elles ne sont plus rafraîchies du tout ;
   - 2 sont nées dans l'app sans aucun lien. **20000007** est l'essai du 21/10, dont la suppression attend un accord. **20000010** n'est pas identifiée.
   Les 7 autres contacts nés dans l'app ont un lien et une nature.
   ⇒ Un contact créé dans l'app sans bien ne pourra JAMAIS recevoir « Ajouter un conjoint ».
3. **Rattacher une coquille (les 680)** : aucun geste dans l'app. Le travail `link_hektor_conjoint` sait déjà relire les deux fiches et recalculer
   la nature : c'est la base toute prête.

**Non mesuré** : pourquoi les 209 fiches ont perdu leur éligibilité ; ce que l'écran montre après « Compléter » avant la nuit.

## 59. « NATURE AU CLIC » — AUDIT EN PROFONDEUR DE CE QUI EXISTE *(04/11, « nature au clic, mais il faut bien auditer notre projet en profondeur pour comprendre ce qui a déjà été fait » ; lecture seule, rien codé)*

**Ce qui était déjà décidé ou écrit** :
- §9 (01/11) : le défaut est CONNU depuis la pose. « Un contact né dans l'app dans la journée n'a pas de nature avant la nuit ; la relecture d'une
  fiche dans la journée renvoie la nature de la nuit précédente. L'écran devra lire vide comme pas encore calculé. »
  ⚠ Ce dernier point n'est PAS fait : une nature vide n'affiche ni foyer ni bouton (`peutRecevoirUnConjoint` exige `personne_seule`).
- Pièce G (§53) : le SEUL geste qui tient déjà la nature. La fonction écrit la nature au clic chez Supabase (personne `couple`, conjoint `conjoint`).
  Après Hektor, `relire_couple_rattache.py` recalcule la nature de toute la table locale (~8 s), puis envoie les deux fiches.

**Le chemin de la nature, dans le code** :
- `nature_des_fiches.py` (étape du run de 04:00) calcule TOUTE la table locale et la REMPLACE (`DROP TABLE` puis recréation, une transaction).
- `push_contacts_to_supabase.py` : `ajouter_nature()` joint cette table locale à chaque ligne envoyée (interrupteur `APP_CONTACT_NATURE`, allumé).
  Une fiche absente de la table part avec une nature VIDE.
- **La relecture d'une fiche** (`refresh_contact_inproc.py` : détail → normalisation → couche → conjoint → envoi) n'a PAS d'étape « nature ».
  Son envoi reprend donc la nature de la nuit d'avant, ou vide pour un contact neuf. ⭐ Le précédent existe pourtant : l'étape « conjoint »
  (`conjoints_des_couples.py --contact-id`, P2 du 31/10) recalcule LE couple de la fiche avant l'envoi, pour la même raison.
- **Les fonctions au clic** (`pg_proc`) : seule `app_ajouter_conjoint_optimistic` écrit `nature_fiche`. Créer, créer un mandant, modifier,
  modifier ou compléter le conjoint, archiver : aucune.
- **Les deux périmètres d'envoi** : la nuit n'envoie que les éligibles (`run_quotidien.ps1` : `-ContactsEligibleOnly`). Une relecture envoie
  les actifs OU éligibles (`active_or_eligible`). ⇒ Un contact actif non éligible n'est rafraîchi chez Supabase QUE par une relecture.
  C'est l'explication des 211 natures vides du §58 : ces fiches ont été envoyées par une relecture avant le 01/11, et la nuit ne les reprend jamais.
- **Ce qui lit la nature** : l'annuaire masque `case_conjoint_vide` (`api.ts:271`, une nature vide reste visible) ; la fiche (foyer si
  `couple`, bouton « Ajouter » si `personne_seule`) ; la fonction d'ajout (refuse cases et conjoints, laisse passer le vide).
  Aucune vue ni aucune autre fonction chez Supabase.

**L'usage réel** (travaux `done`, 30 derniers jours) : 19 créations de contact, 1 création de mandant, 5 modifications, 1 modification de mandant,
3 archivages, 1 ajout de conjoint, 12 suppressions.

**Ce que ça pourrait casser ailleurs** :
- la nature change l'empreinte d'une ligne (renvoi de la ligne, sans danger) ;
- l'annuaire masque ou montre une coquille selon sa nature ;
- la règle « un notaire n'est jamais un couple » et le rattachement des orphelines ne se calculent que sur la table entière ;
- `DROP TABLE` à chaque geste : un lecteur au même moment (l'envoi de la nuit) trouverait une table absente → il n'envoie RIEN de la nature
  (garde existante). C'est sans dommage, mais déjà le cas avec G.

## 60. LA NATURE À LA RELECTURE (« A ») : ÉCRITE, ÉPROUVÉE, ÉTEINTE *(04/11, « vas-y, fais le correctif après un nouvel audit de mon projet pour être sûr »)*

**Le nouvel audit a changé le plan : C est abandonné, A suffit.**
- La création peut faire naître un COUPLE d'un coup : `app_create_contact_optimistic` appelle `app_contact_creer_conjoint` (« la personne 2 naît
  avec la 1 », 31/10, cran `couple_nait_complet`). Et un couple peut être écrit dans le nom (« Paul et Anne »).
- Écrire « personne seule » au clic (C) aurait donc été faux dans ces deux cas. Pour bien faire, il aurait fallu recopier la règle de nature
  en SQL : une deuxième règle à tenir à jour. ⇒ Abandonné.
- A couvre la création : la relecture arrive environ 40 s après le clic.
- Le modèle exact existait déjà : l'étape « conjoint » de la relecture (`conjoints_des_couples.py --contact-id`, P2 du 31/10). Elle a un
  interrupteur, ne lève jamais, et se calcule par ménage.

**Le code** (dormant) :
- `nature_des_fiches.py --contact-id N` : `menage_du_contact`, `calculer_menage`, `ecrire_lignes`, `executer_pour_contact`.
  - Ménage écrit : la principale, la fiche, les secondes de la principale, et les cases que la nuit leur a rattachées.
  - Contexte lu en plus : les secondes de chacun.
  - Le calcul passe par LA MÊME fonction `calculer()` que la nuit.
  - Le rattachement des orphelines garde la valeur de la nuit (`rattachee_a` et `rattachement` relus dans la table).
  - L'écriture se fait par `INSERT OR REPLACE` des seules lignes du ménage, jamais par `DROP`. Si la table est absente, rien n'est écrit.
  - Interrupteur **`APP_NATURE_A_LA_RELECTURE`** (.env), ABSENT donc éteint. Sortie toujours 0 avec `--contact-id`.
- `refresh_contact_inproc.py` : une étape « nature » entre « conjoint » et « push ».
- Hors de ce mode, le calcul de la nuit n'est pas touché.

**Éprouvé** :
- `test_nature_des_fiches` **37/37**, dont 8 neufs : EA32621 relu par la coquille comme par la personne ; seul le ménage est réécrit, une fiche
  hors ménage garde sa valeur ; contact né aujourd'hui ; table absente ; contact inconnu ; principale disparue ; rattachement de la nuit gardé ;
  Madame de l'ancien logiciel.
- ⭐ **Témoin sur la vraie base, en lecture seule** : 416 fiches (250 au hasard, plus les cas difficiles : rattachées et leurs personnes, ménages
  de 3 fiches ou plus, notaires, Madames, EA32621). **779 lignes de ménage comparées au calcul de la table entière : 0 écart.**
- EA32621 : 10260586 `couple` / `case_vide`, 10260585 `case_conjoint_vide`.
- Durée : **0,8 à 1,2 s par relecture**, à comparer aux ~40 s de la relecture. Elle vient de la colonne `hektor_couple_contact_id`, qui n'a pas
  d'index (~190 ms par lecture) ; la couche est refaite chaque nuit, donc on n'en ajoute pas.
- Éteinte, l'étape sort en 0 sans rien faire (vérifié).
- ⚠ Le banc de la relecture (`test_relecture_apprend_la_paire_8a.py`) était **déjà à 12/17 AVANT** ce changement. Il n'avait pas appris l'étape
  « conjoint » du 31/10. Il est mis à jour (les étapes « conjoint » et « nature » reçoivent NOTRE numéro) : **17/17** ; et la version d'avant
  donne 12/17 (témoin inverse).

**Ce que ça pourrait casser ailleurs** :
- La relecture d'une fiche ne peut pas échouer à cause de cette étape (sortie 0, exceptions gardées).
- Un ancien ménage que la fiche vient de quitter n'est pas recalculé : la nuit le refait.
- Une écriture pendant le remplacement de la table par la nuit : la nuit la recouvre avec un calcul complet, ce qui est sans dommage.
- La nature change l'empreinte de la ligne, donc la ligne est renvoyée une fois.
- **Ce que ça ne règle PAS** : les 211 fiches non éligibles (§58, trou 2). Elles n'auront leur nature qu'à leur prochaine relecture
  (ouverture de la fiche).

**Pour l'allumer** (écriture de configuration : ton accord) : ajouter `APP_NATURE_A_LA_RELECTURE=1` dans `C:\Hektor\Projet\.env`.
Aucun redémarrage n'est nécessaire : chaque relecture relit le `.env`.
**Retour arrière** : retirer la ligne du `.env`.

- ✅ **ALLUMÉ le 04/11 vers 08:26** (« Oui, allume ») : `APP_NATURE_A_LA_RELECTURE=1` est ajouté à la fin du `.env`, avec sa ligne de
  commentaire. Une copie datée du `.env` d'avant est dans le dossier de travail de la session.
  Vérifié à blanc : l'interrupteur est lu (ménage d'EA32621 → `couple` ; 20000007 → `personne_seule`), et rien n'est écrit.
  ⏳ **Pas encore vu sur une vraie relecture** : la prochaine ouverture d'une fiche, ou le prochain geste, doit montrer « [nature] … ligne(s) du
  ménage réécrite(s) » dans le compte rendu du travail `refresh_console_contact_data`.

- ✅ **VU EN VRAI le 04/11** : l'interrupteur est posé à 08:26:41. Deux relectures réelles ont suivi, à 08:27:48 et 08:28:26
  (travaux `refresh_console_contact_data` `done`, contacts 10650562 et 10650564). Chacune a réécrit SON ménage dans la table locale :
  10650562 `couple` et 10650563 `conjoint` ; 10650564 `couple` et 10650565 `conjoint`. Chez Supabase, les quatre fiches portent la même
  nature, et la principale a son conjoint « nommé ».
  ⚠ Le compte rendu du travail ne montre pas la ligne « [nature] » : la sortie gardée est coupée avant (~2 100 caractères). La preuve est
  donc l'heure `calcule_le` des lignes de la table locale.
  Hors de ce changement : 2 relectures en erreur ce matin (07:06 et 07:15 UTC, contacts 10651002 et 10650996). Le worker refuse avant toute
  étape Python : « pas encore créé chez Hektor : rien à viser ». C'est son refus normal pour un contact qui n'a pas encore son numéro Hektor.

## 61. ⛔ LES 211 SANS NATURE : LA NUIT NE RETIRE PLUS AUCUN CONTACT DE SUPABASE DEPUIS LE 23/09 *(04/11, « on enchaîne » ; lecture seule, rien codé)*

- **Ce qu'elles sont** : 216 contacts que Supabase a déjà reçus (ils sont dans l'état d'envoi local, dernier envoi entre le 23/09 et le 27/10)
  et qui ne sont plus éligibles. La nuit n'envoie que les éligibles, donc ils ne sont plus jamais rafraîchis. 211 d'entre eux n'ont pas de
  nature, parce que la nature est née le 01/11.
- **Ce qu'ils montrent de faux, mesuré chez Supabase** :
  - **104 sont ARCHIVÉS chez Hektor mais ACTIFS dans l'app** (2 seulement ont un lien au registre) ;
  - 107 sont actifs des deux côtés, dont 96 avec un lien au registre (sans doute des vendeurs ou acquéreurs de biens sortis du parc) ;
  - 5 sont archivés des deux côtés.
- **La cause, dans le code** : `push_contacts_to_supabase.py`, `est_ne_dans_l_app()` (l. 645), et le verrou C-4 (l. ~1003) qui retire
  des « disparues » tout contact né dans l'app. Le verrou les reconnaît à `>= 10 000 000`. Or depuis la bascule du 23/09, TOUTES les identités
  de contact sont dans cette plage : 356 815 sur 356 824 dans la couche, 63 171 sur 63 193 dans l'état d'envoi.
  La vraie plage des contacts nés dans l'app est **>= 20 000 000** : le distributeur `app_contact_identite_seq` a été placé à 20 000 000 le 22/09,
  et en est aujourd'hui à 20 000 037.
  ⇒ Le verrou écarte TOUTES les disparues : la nuit ne retire plus aucun contact de Supabase. Sur les 30 nuits de journaux gardés, il y a
  eu 1 seule suppression de contact (le 22/10).
  Le commentaire du verrou le disait lui-même : « il ne devrait jamais mordre ». Il mord sur tout.
- **Calcul des disparues refait à blanc** : 241, dont 216 encore dans la couche (non éligibles) et 25 absentes de la couche. Ces 25 sont
  déjà absentes de Supabase : les suppressions faites par l'app et les contacts d'essai.
- **Ce qui ne s'est PAS perdu, au contraire** : comme rien n'a été retiré, aucun contact lié à une affaire n'a disparu de l'app. La décision
  du 30/09 (« les liens acquéreur montent toujours ») s'en trouve protégée par accident.
- **Les options, rien n'est décidé** :
  A. remettre le verrou sur 20 000 000 SEUL : la nuit suivante retire les 216 de l'app, dont 96 liés au registre. ⛔ Ça casserait des
     affaires et la règle « un numéro ne se perd jamais ».
  B. ⭐ **la nuit envoie aussi les contacts DÉJÀ ENVOYÉS** (éligibles OU dans l'état d'envoi), sur le modèle exact de la décision B du 14/10
     pour les recherches (« une recherche qui a déjà existé dans Supabase n'en est plus retirée parce que son contact s'est endormi »).
     Les 216 seraient rafraîchis : les 104 archivés passent archivés, la nature arrive. Le coût est de +216 lignes.
     Et le verrou est remis sur 20 000 000, pour qu'il dise ce qu'il veut dire. Il n'aurait alors plus rien à retirer, sauf un contact
     sorti de la couche locale ; or la couche garde même un contact supprimé chez Hektor quand un bien le cite (`supprimee_chez_hektor`).
  C. ne rien faire : 104 contacts restent faussement actifs, et le nombre grandit à chaque contact qui s'endort.

## 61 bis. CE QUE LE PROJET AVAIT DÉJÀ FAIT SUR CE SUJET *(04/11, « attention, nous avons déjà fait un chantier sur ce problème, audite en profondeur pour le retrouver »)*

Recherche dans les notes (accents ignorés), l'historique git et la mémoire. **Cinq chantiers touchent ce sujet ; aucun ne le règle :**
1. **11/09 — l'élargissement du périmètre** (`elargir_perimetre_console.py`) : une personne nommée dans une transaction reste dans l'app
   (règle `console_transaction_party`). Il était FAIT pour que les vendeurs et acquéreurs d'un bien sorti du parc ne disparaissent pas.
2. **21/09 — C.16, les contacts que Hektor ne connaît plus** (`marquer_contacts_disparus.py`) : « ON NE SUPPRIME JAMAIS, ON MARQUE »
   (`absent_depuis`). Sa note disait alors que les fiches qui perdent leur éligibilité « ont quitté l'app d'elles-mêmes ». C'était vrai AVANT
   la bascule.
3. **23/09 — C-4, pendant la bascule** (`AUDIT_COMPLET_AVANT_BASCULE` §C-4) : le verrou « un contact né dans l'app n'est jamais déclaré
   disparu », posé à `>= 10 000 000`. ⇒ **C'est l'origine** : la même bascule a mis tous les contacts dans cette plage, et le distributeur
   des contacts nés dans l'app à 20 000 000 (22/09).
4. **14/10 — les recherches orphelines** (`AUDIT_RECHERCHES_ORPHELINES` et `CORRECTIFS_RECHERCHES_MESURES`). ⭐ **Le symptôme y est déjà
   écrit** : « Le contact n'est pas supprimé de Supabase — il n'est simplement plus mis à jour. Seules ses recherches sont retirées. »
   (35 contacts, `eligible = 0` en local et vrai dans Supabase.) Le correctif posé, **B**, garde les RECHERCHES des contacts déjà envoyés
   (`--garder-recherches-deja-poussees`, allumé dans `run_quotidien.ps1`). Mais il ne rafraîchit pas la FICHE du contact, et la cause
   (le verrou) n'a pas été cherchée.
5. **15/10 — ⑦-1, archiver un contact** : il note le risque « sortir de l'éligibilité → supprimé du cloud la nuit suivante, comme les
   35 fiches du 14/10 ». ⚠ Ce n'était pas le cas : elles n'avaient PAS été supprimées (point 4). Trois sorties y sont proposées (refuser,
   avertir, refuser seulement si c'est la dernière raison) : **rien n'est décidé**.

**Ce que ça change à ma proposition du §61** : rien sur le fond, et deux appuis de plus.
- **B prolonge exactement la décision du 14/10.** On garde déjà les recherches d'un contact déjà envoyé ; on garderait aussi sa fiche, à jour.
- **A est contraire à la règle de C.16** (« on ne supprime jamais, on marque ») et à l'élargissement du 11/09.
- ⚠ Une conséquence pour ⑦-1 : son risque « supprimé du cloud » n'existe pas aujourd'hui. Avec B, il n'existerait plus du tout.

## 62. L'INDEX GLOBAL DES CONTACTS : AUDIT FAIT, À DÉCIDER *(04/11, « pourquoi ne pas faire l'index global des archivés et actifs ? », « oui »)*

- La note à part : `notice/AUDIT_INDEX_GLOBAL_CONTACTS_2026-11-04.md`, en lecture seule, rien n'est codé.
- **Le constat** : les annonces ont trois index légers et une fiche préparée à la demande depuis le serveur ; les contacts n'ont ni l'un ni l'autre.
  C'est le défaut de fond derrière les 216 contacts figés.
- **Les mesures** : 176 417 personnes hors de l'app (64 039 actives, 112 378 archivées, cases vides exclues) ; une ligne légère pèse 336 octets
  (estimation de 120 à 200 Mo) ; une recherche dans l'annuaire prend 16 ms aujourd'hui.
- **Cinq décisions attendues** (§6 de la note) : qui entre dans l'index ; les champs (téléphone et e-mail) ; la forme de la fiche à la demande ;
  le premier envoi ; les garde-fous.
- ⚠ **L'ordre est obligatoire** : l'index et le repli d'abord, le verrou remis sur 20 000 000 ensuite.

## 63. TOUT MESURER AVANT DE CHOISIR : LES 216, LE DÉBIT, ET POURQUOI TANT D'ARCHIVÉS LIÉS AUX ANNONCES *(04/11, « c'est important de tout mesurer correctement, le remède est peut-être plus simple que prévu » ; « cherche pourquoi autant de contacts archivés liés aux annonces, audite l'historique et les codes doublon » ; lecture seule)*

**Les 216 contacts figés** (§61) :
- **Pourquoi ils sont sortis** :
  - leurs recherches sont TOUTES inactives (114 en local, 106 contacts en ont chez Supabase, 0 active) ;
  - leurs liens ne portent que sur des annonces archivées (mandant 139, propriétaire 7, acquéreur 10).
  - Chez Supabase, leur raison d'avant était `active_annonce_relation` ou `active_search`. Aucun n'était « nommé dans une transaction ».
- **Ce qui les cite dans l'app** : 102 sont dans le registre des relations, 106 ont des recherches (inactives, gardées par la décision du 14/10)
  et 10 ont des liens envoyés.
- **Quand** (date de leur dernier envoi, donc à peu près celle de leur sortie) : par paquets. Le 03/10 en compte 89, le 15/10 69 et le 13/10 27,
  le reste est un filet de 1 à 9 par jour. En moyenne, environ 5 par jour sur 42 jours.

**Pourquoi 22 644 contacts archivés sont dans l'app — trois causes, mesurées** :
1. ⭐ **Pour la règle d'envoi, « annonce active » veut dire « annonce NON ARCHIVÉE chez Hektor »** (`load_active_annonce_ids`,
   `build_contacts_layer.py` l. 902 : `archive = '0'`). Les biens VENDUS et les ESTIMATIONS en font partie.
   Pour les contacts archivés (personnes, sans les cases vides), leurs 30 337 liens se répartissent ainsi :
   - Vendu **22 814** ;
   - Estimation **7 067** ;
   - Mandat clos 258, Clos 105 ;
   - Actif **64**, Sous compromis 20, Sous offre 8.
   ⇒ **92 liens seulement sur un bien réellement en vente**. Le reste est de l'affaire passée. Même profil chez les actifs : Vendu 22 267,
   Estimation 7 160, Actif 969. Cela recoupe ⑦-1 (14/10) : 55 contacts archivés sur 52 biens réellement en vente.
2. ⭐ **Trois journées d'archivage EN MASSE chez Hektor** (date `date_maj` des contacts archivés) :
   - le **07/09/2023** : 72 658 contacts archivés, presque tous Saint-Étienne, créés en 2018-2021, entre 10 h 56 et 12 h 33 ;
   - le **26/03/2025** : 51 938, plusieurs agences, créés en 2011-2014, entre 21 h 51 et 22 h 32 ;
   - le **06/10/2021** : 22 773, Le Puy, Firminy, Annonay.
   ⇒ Parmi les 21 690 archivés envoyés à l'app et liés à une annonce non archivée, **15 891 (73 %) viennent de ces trois journées**
   (7 030 + 6 628 + 2 233). Ce sont des purges faites en lot, pas des gestes un par un.
   Le 26/03/2025 a aussi touché 80 212 contacts restés ACTIFS (une mise à jour de masse, et pas un archivage).
   ⚠ Qui les a faites et pourquoi : **non établi**. Aucune note du projet ne les mentionne.
3. **Les doublons, en partie** : 4 374 des 17 675 personnes archivées sont dans un groupe de doublons (high 3 137, medium 685, critical 410,
   low 142). Dans 3 408 des 30 337 liens, un contact ACTIF tient le même rôle sur la même annonce : c'est sans doute l'ancienne fiche et la
   nouvelle. Le code des doublons ne fait que proposer : `CAHIER_CHARGES_DOUBLONS` interdit l'archivage automatique, et il n'existe aucun geste
   de fusion dans l'app.
   ⇒ Les doublons sont une cause MINEURE. La cause majeure, c'est la règle d'envoi et les trois purges.

**Ce que ça change pour le remède** :
- Le flux est petit (~5 contacts par jour, par paquets) et ne touche que des affaires passées.
- ⇒ **Le remède le plus simple tient en une clause** : la nuit envoie aussi les contacts déjà envoyés, comme la décision du 14/10 l'a fait pour
  les recherches. Ensuite, le verrou est remis sur 20 000 000. Il n'aurait alors plus rien à retirer, puisque la couche locale garde tout le monde.
  C'est +216 lignes aujourd'hui, et environ 150 par mois.
- L'index global (§62) n'est PAS nécessaire pour régler les contacts figés. Il reste une amélioration à part : retrouver dans l'annuaire les
  ~176 000 anciens clients jamais envoyés.
- Une question de fond est révélée, à trancher à part : faut-il que « lié à une annonce » veuille dire « annonce non archivée » (vendus et
  estimations compris), ou « bien encore en vente » ? C'est ce qui fait que la majorité des 63 000 contacts de l'app sont des affaires passées.
  Rien n'est proposé ici : ce serait un changement de périmètre (décision de Frédéric, 8b clos « par choix »).

## 64. LE REMÈDE EN UNE CLAUSE : ÉCRIT, ÉPROUVÉ À BLANC, ÉTEINT *(04/11, « oui, prépare-le »)*

- **Le code** (`phase2/sync/push_contacts_to_supabase.py`) :
  - `garder_contacts_deja_pousses_allume()` lit l'interrupteur **`APP_GARDER_CONTACTS_DEJA_POUSSES`** (.env). Il est absent, donc éteint.
  - `elargir_aux_contacts_deja_pousses()` ajoute au périmètre des contacts un `OR` : les contacts déjà envoyés, tels que les connaît l'état
    d'envoi local.
  - La clause se pose APRÈS `stats_contact_where` (les compteurs de l'annuaire restent ceux des éligibles) et AVANT le filtre par contact :
    une relecture d'un contact déjà envoyé le rafraîchit aussi.
  - C'est le même patron que `--garder-recherches-deja-poussees` du 14/10.
  - Aucun changement dans le run de nuit : l'interrupteur suffit.
  - ⚠ Le verrou C-4 n'est PAS touché. Avec ce remède il n'a plus rien à protéger ; le remettre sur 20 000 000 seul retirerait les 216.
- **Éprouvé à blanc** (la commande exacte de la nuit avec `--dry-run`, sur la vraie base ; rien n'est envoyé) :
  - éteint : 62 952 contacts chargés, 11 à envoyer, 241 « disparues » ;
  - **allumé : 63 168 chargés (+216), 227 à envoyer (+216), 25 « disparues »**.
  Ces 25 sont absentes de la couche locale ET déjà absentes de Supabase (suppressions faites par l'app, contacts d'essai). Le verrou les écarte
  de toute façon. Liens et recherches : inchangés.
- **Essais** : `phase2/sync/test_garder_contacts_deja_pousses.py` **4/4** (dont le témoin du périmètre d'avant) ; `test_dirty_guards` vert ;
  `phase2/checks/test_c4_suppressions.py` : ses vrais contrôles passent.
  ⚠ Ses deux « PREUVES » échouent, mais AVANT ce changement aussi : elles comparent à `git show HEAD:…`, qui contient déjà le correctif du 23/09.
  Le banc est périmé sur ce point : c'est noté, pas corrigé.
- **Pour l'allumer** (ton accord) : ajouter `APP_GARDER_CONTACTS_DEJA_POUSSES=1` dans le `.env`.
  La nuit suivante, les 216 partent. Le contrôle du lendemain doit montrer les 104 archivés passés archivés chez Supabase et la nature présente.
  **Retour arrière** : retirer la ligne.
