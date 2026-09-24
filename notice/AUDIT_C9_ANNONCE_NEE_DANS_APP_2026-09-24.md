# 🧭 AUDIT `C.9` — l'annonce naît dans l'app

**24/09/2026.** Deux passes le même jour ; la seconde à la demande de Frédéric : *« consulte en
totalité le code actuel, les doublures… et confirme ou pas ta proposition »*. Mesuré dans le
code et dans les deux bases. **Aucune donnée modifiée, aucune ligne de code écrite.**

> ⚠ **La première passe (matin) proposait un ordre faux sur quatre points, et elle n'avait pas
> vu le défaut le plus grave** *(D1 ci-dessous)*. Ce que la seconde passe a réfuté est en §4 :
> c'est la partie à relire avant de reprendre le chantier.

---

## 0. Portée

Le geste **« créer un bien depuis l'app, et qu'il vive même si Hektor ne l'a pas encore vu »**.
Documents, photos, RDV : **non mesurés ici**. Numéro de mandat, signature, portails : **hors
étape 2** *(charte)*.

## 1. Le tableau objets × gestes

| | créer | modifier | archiver | lire |
|---|---|---|---|---|
| **annonce** | ✅ **via Hektor** — 77 créations, 0 échec, la dernière le 28/08 · calque optimiste allumé · ❌ **aucun numéro d'app avant la réponse de Hektor** | ✅ 53 champs · ⚠ 102 créables non corrigeables *(L5)* | ✅ RPC optimiste | ✅ |
| **contact** (mandant) | ✅ naît dans l'app *(L4-b)* | ✅ | ✅ | ✅ |
| **recherche** | ✅ naît dans l'app *(31/08)* | ✅ autonome *(décision 20/08)* | ✅ | ✅ |
| **relation** mandant / propriétaire | ⚠ ligne **provisoire** sur jeton, que la descente remplace | ❌ | — | ✅ |
| **mandat** | ✅ numéro auto — **reste à Hektor** | ✅ prix, honoraires, surface | ✅ clôture *(seul champ app)* | ✅ |
| **document / photo · RDV** | *non mesuré* | | | |

## 2. Ce qui existe déjà — c'est presque tout

| pièce | depuis | état mesuré le 24/09 |
|---|---|---|
| `hektor_annonce_id` **nullable** (fiche + détail) | 20/08 | ✅ *« une autorisation, pas un comportement »* ; sonde `app_annonces_sans_numero_hektor` à 0 |
| clé primaire de `app_dossier_current` = **`app_dossier_id`** | origine | ✅ le verrou qui bloquait le contact **n'a jamais existé** pour l'annonce |
| distributeur **`app_dossier_id_app_seq`** (départ 10 000 000) | 21/09 *(L4-a)* | ✅ créé · **jamais appelé** *(last_value NULL)* |
| la barrière **`app_annonce_pending`** | juillet | ✅ pivotée sur `app_dossier_id`, branchée worker + push + sondes + front |
| le recensement **`annonces_app_seule.py --recenser`** | 26/08 | ✅ dans le run (l. 421), 0 ligne, **expire bien** ses lignes *(l. 212)* · `--injecter` **non branché, exprès** |
| l'adoption **`adopter_numeros_app.py`** | 21/09 | ❌ **zéro appelant** — voir D2 |

Le patch du 20/08 nomme lui-même ce qui manque : *« Rien ne produira de valeur vide avant la
**tâche 22** (la création écrit la vraie fiche). »*

---

## 3. Les défauts, mesurés

### D1 ⛔ Dans le cas NORMAL, le run de nuit donnerait à l'annonce un SECOND numéro

La chaîne, quand Hektor répond en 30 s comme aujourd'hui (77 fois sur 77) :

```
jour J      l'app donne 10 000 001  ·  le worker cree chez Hektor : 63 200
            Supabase : app_dossier_id 10 000 001, hektor_annonce_id 63 200
nuit J+1    le run tire Hektor : le miroir connait 63 200
  l. 369    bootstrap_phase2 : LEFT JOIN app_dossier deja ON deja.hektor_annonce_id = 63 200
            -> aucune ligne (le serveur ne connait pas 10 000 001)
            -> INSERT d'un NUMERO SERVEUR : 7 589 129
  l. 421    le recensement voit 10 000 001 « connu de l'app seule »  -> DEUX NUMEROS
```

C'est **le jumeau exact** du défaut trouvé par l'essai réel du contact le 21/09 *(« le retour
fabriquait une seconde fiche »)*, réglé pour le contact par **L4-b ②** : le serveur apprend la
correspondance **avant** le build. **Pour l'annonce, cette étape n'existe pas.**
⚠ Il ne se produit pas aujourd'hui **uniquement** parce que l'app ne donne encore aucun numéro.

### D2 ⛔ `adopter_numeros_app.py` : jamais branché, et faux sur trois points

Recherche sur tout le dépôt (`.py .ps1 .sql .js .ts`) : **aucun appelant**. Et s'il l'était :

1. il **ne complète jamais** le numéro Hektor d'une ligne déjà adoptée *(`continue` si l'id
   existe)* — donc D1 se produit quand même ;
2. il lit `app_annonce_app_seule` **sans filtrer `absent_depuis`** — une annonce supprimée dans
   l'app serait **ressuscitée** sur le serveur ;
3. il insère un numéro de la plage de l'app dans une colonne **AUTOINCREMENT** : à la première
   adoption, `sqlite_sequence` saute à 10 000 00x **et SQLite refuse de le redescendre**.
   Inoffensif tant que tout INSERT nomme son `id` *(les deux chemins le font :
   `bootstrap_phase2.py:112`, `push_single_annonce_to_supabase.py:90`)* — mais rien ne l'impose.

### D3 ⛔ Le push du matin EFFACE une annonce que le serveur ne connaît pas

`push_upgrade_to_supabase.py:1236` : `stale = remote_ids − effective_local_ids`, puis
`delete` sur `app_dossier_current`, le détail, les work items et la diffusion *(l. 1492)*.
**Aucun filtre de plage** ; seul le frein « plus de 500 » existe. Une annonce née dans l'app
que Hektor n'a pas confirmée *(Hektor en panne — et toujours après la coupure)* **disparaît
la première nuit**. Le contact avait exactement ce défaut : fermé par **C-4** *(`est_ne_dans_l_app`)*.

### D4 ⚠ L'annonce n'a PAS d'œil : aucun contrôle d'accord serveur ↔ Supabase

13 doublures `__sb` existent, le relevé de nuit en compare 10 *(contacts, relations,
recherches, doublons, affaires, diffusion)* — **aucune pour l'annonce**. Rien ne compare
`app_dossier` (serveur) et `app_dossier_current` (Supabase) sur le couple
*(app_dossier_id, hektor_annonce_id)*. Le push réconcilie les écarts **en silence**
*(`id_rewrites`, l. 1223)*. C'est précisément ce contrôle, côté contact
*(`registre_couche_desaccord`)*, qui manquait le 24/09 au matin.

### D5 ⚠ La clé de relation est à moitié traduite, et sans registre

`build_contacts_layer.py:886` — **seul endroit du dépôt** qui la calcule :
`contact_id` passe par `identite_app()` *(22/09)*, **`annonce_id` reste le numéro Hektor**.
Aucun registre ne gèle les clés de relation *(les recherches en ont un : `app_search_registry`,
77 095 lignes)*. Et la protection du push *(C-4)* ne regarde **que le contact** : une relation
vers une annonce née dans l'app n'est couverte, depuis la bascule, **que par coïncidence**
*(tous les contacts sont dans la plage de l'app)*.

### D6 (hors chemin critique) Le recensement des contacts n'expire jamais rien

`contacts_app_seuls.py:239` insère et met à jour, **n'écrit jamais `absent_depuis`**. D'où
**8 relations en double** dans `app_relation_app_seule` (20 lignes) : même relation sous l'ancien
numéro Hektor (vue le 22/09) et sous l'identité (vue le 24/09) — annonces 6, 27, 9371, 17640,
59057, 59125, 59269, 59629. **Personne ne lit cette table aujourd'hui.**

### D7 (information) Le compteur SQLite de `app_dossier`

```
20/09 08:15   sqlite_sequence 7 589 098   lignes 61 237
24/09 07:35   sqlite_sequence 7 654 438   lignes 61 267   max(id) 7 589 128
```

+65 340 pour +30 lignes : un **pic unique**, pas une dérive *(max(id) ne bouge que de +30)*.
La sonde `app_v_plages_numeros` lit `max(app_dossier_id)` : **aveugle au compteur**.

---

## 4. Ce que la seconde passe a RÉFUTÉ de la première

| j'avais dit le matin | mesuré l'après-midi |
|---|---|
| l'adoption est « en place et prête » | **zéro appelant** et trois défauts (D2) |
| il faut une **porte** comme `cibleHektorContact` | **sans objet** : numéro de l'app et numéro Hektor vivent dans **deux colonnes séparées** — aucune confusion possible *(le lot L4-b′ n'a pas d'équivalent annonce)* |
| le compteur **marche vers la plage** de l'app | **faux** : max(id) +30 en 4 jours. Le danger est le **saut** à la première adoption (D2-3) |
| corriger les 8 fantômes **en 2e position** | **pas sur le chemin critique** (D6) |
| la substitution réécrira **167 000 clés** en une nuit | **pas forcément** : avec un registre à clé gelée *(modèle `app_search_registry`)*, les relations existantes gardent leur clé. Et **tant que Hektor vit**, la relation d'une annonce née dans l'app revient par le miroir avec le numéro Hektor : la clé fonctionne dès que D1 est réglé. La substitution ne sert qu'aux relations **que Hektor n'a jamais vues** — c'est de la préparation de coupure |
| *(non vu)* | **D1, D3, D4** |

---

## 5. L'ordre retenu

| | quoi | touche | feu vert |
|---|---|---|---|
| **C.9-a** | **Le serveur apprend le numéro de l'annonce AVANT le bootstrap** — le jumeau de L4-b ②. Adoption placée **avant** `bootstrap_phase2`, qui **complète** le numéro Hektor quand il arrive et **ignore** les lignes expirées ; + contrôle « tout INSERT dans `app_dossier` nomme son id » ; + sonde sur `sqlite_sequence` | le run | **go** |
| **C.9-b** | **L'œil** : contrôle d'accord annonce serveur ↔ Supabase, *« une annonce, un numéro »*, dans `quality_checks` et la santé | additif | j'enchaîne |
| **C.9-c** | **Le push n'efface plus une annonce née dans l'app** — filtre de plage sur `stale_ids`, patron C-4 | le push | **go** |
| **C.9-d** | **Le registre des clés de relation**, en doublure *(on observe)* + l'expiration du recensement contacts/relations (D6) | additif · l'expiration écrit en base locale | j'enchaîne · **go** pour l'expiration |
| **C.9-e** | **La « tâche 22 »** : la RPC qui donne le numéro (`app_dossier_id_app_seq`) et écrit la vraie fiche, **drapeau éteint** ; + le retour du worker qui pose le numéro Hektor sur la ligne existante | code neuf OFF, puis déploiement | j'explique avant · **go** pour déployer |
| **C.9-f** | **La substitution du numéro d'annonce dans la clé de relation**, par le registre — attendu : **0 clé existante changée**, à prouver sur copie | le build de nuit | **go obligatoire** · répétition sur copie |

Puis **C.9-couple** *(son premier pas est une mesure)* et l'essai **26bis-TRANSACTIONS**.

**Reste NON MESURÉ, à auditer au moment de la tâche concernée** : le chemin de retour du worker
*(`linkProvisionalCreation`, `rememberCreatedHektorAnnonceId`)* → à C.9-e · la sémantique exacte
de `id_rewrites` dans le push → à C.9-b · pourquoi `app_contact_identite_seq` a lui aussi un
`last_value` NULL alors que deux contacts sont nés par la RPC le 21/09 *(supprimés le 22/09 ;
séquence recréée ?)* → à C.9-e.

---

## 6. La vérification des données du 24/09 (avant d'ouvrir C.9)

Référence : `backups/critical/critical_20260920_081503.sqlite.gz`. **18 tables : toutes ont
grossi ou tenu, aucune n'a baissé** — `app_contact` +63, `app_dossier` +30,
`app_search_registry` +27, `app_affaire_ledger` +7. Supabase : 0 orphelin sur les quatre
jointures contact. Santé : **0 critique**. App (session Chrome) : **zéro erreur console** sur
accueil, estimations, annuaire, deux fiches ; une recherche **d'avant la bascule** garde ses
12 rapprochements *(clé gelée)*.

**Deux choses à revérifier le 25/09 au matin :**
- 3 contacts restés sous leur numéro Hektor dans Supabase *(312969, 411105, 414472 ; identités
  10172256, 10213796, 10215521)* — **aucun doublon** ; le run de nuit doit les basculer ;
- l'alarme *« critères différents : 1 »* — fiche d'essai « TEST CHAINE 25-08 », écart du 25/08
  **devenu visible** quand les deux côtés ont pris la même clé ; ce n'est pas une saisie perdue.

**Hors plan, notés** : le compteur de l'annuaire lit un instantané figé au 06/06
*(« 170 494 » pour 61 993)* · les 9 compteurs des filtres répondent 503 *(`count: 'planned'`,
code du 28/05)* · deux lignes provisoires de contact du 18/09 restent affichées « En création »
alors qu'elles sont `linked` · les assertions « PREUVE » de deux contrôles lisent
`git show HEAD:` et échouent désormais à tort.

## 7. Refaire les mesures

```
python phase2/checks/test_registre_ne_double_pas.py        une personne, un numero
python monitoring/check_gti_health.py                      sondes
grep -rn "adopter_numeros_app" --include=*.ps1 --include=*.py .     appelants (attendu : 0 avant C.9-a)
# compteur : SELECT seq FROM sqlite_sequence WHERE name='app_dossier'
# distributeurs : SELECT pg_sequence_last_value('public.app_dossier_id_app_seq'::regclass)
```
