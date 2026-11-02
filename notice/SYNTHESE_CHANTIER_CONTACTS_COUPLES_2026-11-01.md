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
