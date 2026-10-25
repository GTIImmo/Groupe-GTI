# Audit des alertes rouges et orange du monitoring — 24/10/2026

**Lecture seule. Rien n'a été modifié, ni en base, ni dans le code.** Seul geste exécuté : l'**essai à vide**
de `menage_orphelins_recherche.py` (`--essai-a-vide`), qui n'appelle pas la base.

Question de Frédéric : *« de quoi il s'agit, récent ou pas, et si je peux les retirer — l'alerte, pas le
garde-fou »*.

## 0. Pourquoi « Résolu » ne tient pas

La vue `alerts_governed` ne garde la réponse de l'humain que si `acted_at >= updated_at`. **Or le moniteur
réécrit `updated_at` de chaque alerte à chaque passage, même si rien n'a changé.** Un « Résolu » est donc
effacé au passage suivant. Preuve dans `app_alert_state` : « Résolu » sur le résumé et sur
`console.jobs.errors` le 14/10, « Pris en charge » sur `data.travaux_en_erreur` le 15/10. **Toutes sont
revenues.**

➡ Pour qu'un « Résolu » tienne **sans éteindre le garde-fou**, la vue devrait comparer la réponse à la
**dernière fois que le CONTENU de l'alerte a changé** (son message ou son compte), et non à sa dernière
réécriture. L'alerte resterait muette tant que rien de nouveau n'arrive, puis se rallumerait sur une
nouveauté. **Non fait : c'est une modification de la base, il faut l'accord de Frédéric.**

## 1. Les 10 lignes

| # | alerte | couleur | depuis | de quoi il s'agit | verdict |
|---|---|---|---|---|---|
| 1 | `workers.heartbeat:phase2.adresses_photos` | 🔴 | **cette nuit** (24/10) | l'étape qui écrit **nos adresses de photos** a échoué deux fois (07:09 et 07:10) : **« canceling statement due to statement timeout »** sur `app_photos_remplir_adresses_app`. **Pas le garde-fou** : le parc compte 13 507 annonces, très au-dessus du plancher de 5 000 | **VRAI et RÉCENT. Ne pas retirer.** Les annonces neuves ou modifiées depuis hier montrent les adresses de photos de Hektor pour une journée. Il s'éteint seul si la nuit prochaine passe. ⚠ À surveiller : si le délai coupe encore, la fonction est devenue trop lente |
| 2 | `workers.heartbeat` | 🔴 | rouge aujourd'hui, **orange depuis le 20/09** | rouge à cause de la n° 1. L'orange de fond vient de **5 workers « sans premier signe »** : `backend.fastapi`, `console.worker.matterport`, `console.worker.sync_full`, `contacts.detail_backfill.wrapper` (déclarés le 27/05, **aucun code ne les fait battre**) et `phase2.menage_orphelins_recherche` (voir §2) | le rouge part avec la n° 1. L'orange **ne partira jamais seul** : il faut décider, clé par clé, s'il faut **retirer la déclaration** (worker mort) ou **brancher son battement** (worker vivant) |
| 3 | `monitor.summary` | 🔴 | — | ne fait que **compter** les autres | rien à faire, il suit |
| 4 | `data.travaux_en_erreur` | 🔴 | 16/10 | **6 travaux en erreur non tranchés** (sur 11 en 30 jours, 5 déjà tranchés) : **5 relectures de contact** échouées à l'ouverture d'une fiche (Gladys 10059959 le 16/10 ; contacts d'essai 8a 10650744 et 605922 ×2 le 21/10 ; 605973 « ESSAI 8 TROIS » le 23/10, interrompu après 30 min) et **1 modification de l'annonce d'essai 63331** (22/10, worker arrêté net, déjà soldée à la main) | **TOUT EST DE L'ESSAI OU DE LA LECTURE.** On peut le retirer **proprement** : trancher chaque ligne dans l'écran Santé (« J'ai refait »). Le garde-fou ne compte plus les lignes tranchées et repasse au vert, **tout en restant actif** |
| 5 | `data.geste_abandonne` | 🟠 | 16/10 | **les mêmes 6** | part avec la n° 4 |
| 6 | `console.jobs.errors` | 🟠 | cette nuit | 1 erreur sur 48 h = la relecture du contact 605973 (23/10 17:22) | **s'éteint seul** le 25/10 vers 17:22 (fenêtre de 48 h) |
| 7 | `data.transaction_disparue` | 🟠 | 20/10 (1 ligne) ; **11 d'un coup cette nuit** | 10 compromis et 1 vente, **anciens** (2016 à 2024, dates `0000-00-00`), vus au run du 23/10 et absents de celui du 24/10. Les nuits précédentes : 1 ou 2 lignes récentes. Et 59056, « disparu » le 20/10, **est réapparu** | **À VÉRIFIER, ne pas retirer à l'aveugle.** Le profil (11 vieilles lignes d'un coup) fait penser à **un trou dans la descente de cette nuit** plutôt qu'à des suppressions chez Hektor. **Non prouvé** |
| 8 | `data.annonce_naissance_ecart` | 🟠 | 22/10 | **annonce d'essai 63331** (n° app 10000009) : 5 champs que Hektor n'a pas gardés (syndic, diagnostiqueur absents ; TRANSPORT, copropriété, honoraires remplacés). La copropriété est le défaut du secteur, gardé depuis | **c'est l'essai du 22/10.** Pas de geste « j'ai vu » durable aujourd'hui (§0) |
| 9 | `data.contact_modif_ecart` | 🟠 | 22/10 | **contacts d'essai** 20000007 / 20000008 « ESSAI 8A » : ville et CP perdus. **La cause est corrigée** depuis le 22/10 (identifiants de commune) | **essais anciens.** Même limite que la n° 8 |
| 10 | `logs.pipeline.latest` | 🟠 | ce matin | la fin du journal du run contient une erreur : celle de la n° 1 | part avec la n° 1 (il était vert hier) |

## 2. Trouvé en passant — le ménage des orphelins de recherche n'a JAMAIS réussi

L'étape `phase2 menage orphelins de recherche` (ajoutée au run le 14/10) **échoue toutes les nuits depuis le
15/10 : 10 sur 10**. La cause, lue dans les journaux de la base à 07:03:31 : **« DELETE requires a WHERE
clause »**. Appelée **par l'API**, Supabase refuse une suppression sans condition (protection propre à
Supabase), et `app_sweep_search_orphans()` en contient une. **Appelée par la tâche planifiée Supabase**
(cron n° 11, 05:00 UTC), elle **réussit chaque jour**. Donc :

- **le ménage est bien fait** (par le filet) : aucune donnée en souffrance ;
- mais **la raison d'être de l'étape** (passer APRÈS le push pour supprimer la course du 13/10) **n'est pas
  remplie** ;
- et l'étape **ne bat jamais** → elle fait partie des 5 « sans premier signe » de la n° 2.

Correctif possible (non fait, il faut l'accord) : ajouter une condition à la suppression dans la fonction
(par exemple `where true`), ou appeler la fonction autrement que par l'API.

## 2 bis. AUDIT APPROFONDI — l'échec des adresses photos (n° 1)

> Demandé par Frédéric : *« ça m'étonne, nous avons énormément travaillé sur ce problème, audite en profondeur »*.
> Lecture seule : `EXPLAIN ANALYZE` sur des **SELECT** (aucune écriture), journaux de la base, journaux du run.

**Ce n'est pas un retour de l'ancien problème. C'est un effet de bord du correctif du 20/10.**

### La chronologie (journaux du run, 23 nuits)

| nuits | durée de l'étape | essai |
|---|---|---|
| 02/10 → 20/10 | **2 à 5 s** | 1er essai, chaque nuit |
| **21/10** | 46 s au total | ⚠ **1er essai raté**, 2e réussi |
| 22/10 | 9 s | 1er |
| **23/10** | 48 s au total | ⚠ **1er essai raté**, 2e réussi |
| **24/10** | — | ⛔ **les deux ratés** : `canceling statement due to statement timeout` (07:09:53 et 07:10:31) |

⚠ **Le 21 et le 23, la 2e tentative a MASQUÉ l'échec** : le battement disait « succès », personne n'a été
prévenu. La dégradation a commencé **le lendemain de la pose** du patch
`supabase/patch_chantier7_8_galerie_photo_retiree_2026-10-20.sql` (commit `6b8ca6e`).

### La cause, prouvée

Le patch du 20/10 (la galerie suit le **retrait** d'une photo chez Hektor, mémoire
`galerie-app-perimee-photo-retiree-ne-declenche-pas`) a remplacé, dans la table `tmp_maj` :

    where p.derives_generes_le >= now() - 48 h                                   -- avant
    where greatest(p.derives_generes_le, p.absent_depuis) >= now() - 48 h        -- depuis le 20/10

L'index `app_console_photo_derives_le_idx` porte sur `derives_generes_le` seul : **il ne sert plus**. Mesure
du 24/10, sur la production, en lecture seule :

| version | plan | durée |
|---|---|---|
| avant | Index Only Scan `app_console_photo_derives_le_idx` | **43 ms** |
| depuis le 20/10 | **Seq Scan** des 442 142 photos (783 Mo), **73 118 blocs lus sur disque** | **3 486 ms** (×80) |

Ce n'est qu'**une** des six requêtes de la fonction. À 07:09, juste après le run, la table est en grande
partie hors mémoire : **le total dépasse les 8 s** que Supabase accorde à un appel par l'API (`authenticator` :
`statement_timeout=8s`). Le volume réel est minuscule : 384 photos, 27 annonces bougées en 48 h.

⚠ Facteur aggravant, **non causal** : la table a **69 107 lignes mortes** et **aucun nettoyage automatique
depuis le 27/09** (`last_autovacuum`). Ça grossit la lecture complète.

### Ce que ça coûte aujourd'hui

- Les annonces dont les photos ont bougé depuis le 23/10 (27 en 48 h) **gardent leur ancienne galerie** chez nous.
- Les adresses encore **vides** ne sont pas remplies (28 vivantes, 68 brouillons, 6 archives, 3 historiques) :
  elles montrent les photos de Hektor.
- **Le verrou des photos masquées** (⑦-8 marche 1) passe **par cette fonction** : une masquée découverte depuis
  le 23/10 n'est pas retirée de **notre** galerie publique. ❔ **Non mesuré** : combien de cas réels.

### Le correctif proposé (NON appliqué — écriture en base = accord de Frédéric)

**Écrire la même condition autrement, pour que les index servent**, sans rien perdre du correctif du 20/10 :

    where p_tout
       or p.derives_generes_le >= quand - make_interval(hours => greatest(1, p_heures))
       or p.absent_depuis      >= quand - make_interval(hours => greatest(1, p_heures))

+ **un petit index** `on app_console_photo (absent_depuis) where absent_depuis is not null` (**462 lignes**).

C'est **strictement équivalent** : `greatest(a, b) >= X` ⇔ `a >= X ou b >= X` (`greatest` ignore les NULL,
et un `OR` avec un NULL ne retient pas la ligne). Postgres combine alors les deux index (BitmapOr).
Attendu : quelques dizaines de millisecondes. **À prouver** par `EXPLAIN ANALYZE` avant et après, comme ici.

Patch + inverse + répétition à écrire dans `supabase/`, comme les autres. **Pas besoin de toucher au run ni au
worker.**

### ⚠ CONTRE-AUDIT DU CHANTIER PHOTOS (18 → 20/10) — demandé par Frédéric avant toute proposition

**1. Le délai de 8 s était DÉJÀ connu (27/09).** `notice/patch_photos_adresses_app_2026-09-27.sql` l. 133-136 :
mettre le registre dans la même fonction recalculait 23 800 annonces chaque nuit, et *« PostgREST expirait à
8 s (57014) »* → on l'avait sorti dans `app_photos_remplir_adresses_registre` (0,4 s). Le script de nuit
**chronomètre chaque appel** depuis (`Console/remplir_adresses_photos.js` l. 45) : c'est ce chrono qui date la
bascule, dans `logs/scheduled/quotidien_*.log` :

| nuits | `app_photos_remplir_adresses_app` |
|---|---|
| 04/10 → 20/10 | **0,5 à 1,5 s** (le run du 20/10 à 07:09 : 0,6 s, AVANT la pose du patch dans la journée) |
| 21/10 | **57014**, puis 5,8 s au 2e essai |
| 22/10 | **7,4 s** — à 0,6 s du plafond |
| 23/10 | **57014**, puis 8,0 s |
| 24/10 | **57014 deux fois** |

⚠ Et quand cet appel tombe, le script s'arrête : **le registre et le « sans photo » n'ont pas tourné non plus le
24/10**.

**2. Les autres appelants — LE POINT LE PLUS GRAVE.** Le **worker** appelle la même fonction, par l'API (8 s),
juste après **masquer / afficher** (`console_job_worker.js` ~l. 9326, ⑦-8 marche 4) et après **réordonner /
couverture** (~l. 9458, ⑦-3c pièce 4). Son repli est écrit : *« s'il échoue (8 s de budget PostgREST) [...] le
run de nuit remettra la boîte d'aplomb »*. **Le run de nuit étant lui-même en échec, le filet n'existe plus** :
une photo masquée depuis l'app resterait dans la boîte publique. Aucun geste de ce type depuis le 20/10 au
matin : **pas encore de victime**, mais **le prochain clic en ferait une**. Les deux RPC
(`app_console_photo_visibilite_optimistic`, `app_console_photos_reordonner_optimistic`) ne la citent qu'en
**commentaire** : **le clic lui-même n'est pas menacé**. Aucune tâche planifiée Supabase ne l'appelle.

**3. Les versions de la fonction.** Pièce A (18/10, clé `visible`), deux boîtes (19/10, `visible is not false`
×2), galerie retirée (20/10, `greatest` ×2). Empreinte en production le 24/10 :
**`ec8066616381cdb90df38ec561f1441f` = exactement celle attendue après le patch du 20/10** → personne n'est
passé depuis. Le patch du 20/10 a modifié **deux lignes** : le `select … max(greatest(…))` (sans effet sur la
durée) et le `where greatest(…)` (la cause).

**4. Les jumeaux.** Parmi toutes les fonctions de la base, **une seule** utilise `greatest(…derives_generes_le…)`
ou `greatest(…absent_depuis…)` : celle-ci. Pas de jumeau.

**5. L'équivalence, prouvée sur la production (lecture seule).** `greatest(a,b) >= X` contre
`a >= X or b >= X`, sur 48 h / 168 h / 720 h : **27 / 73 / 48 579 dossiers des deux côtés, 0 manquant, 0 en
trop, même date `dernier`**.

**6. ⛔ LA RÉÉCRITURE SEULE NE SUFFIT PAS — mesuré.** `a >= X or b >= X` **sans index sur `absent_depuis`** :
encore un **Parallel Seq Scan, 4 271 ms**. Ma première proposition n'aurait rien réparé sans l'index. **Il
faut un index, c'est lui le correctif.**

### Les deux formes possibles du correctif (à choisir par Frédéric — rien n'est appliqué)

| | **B — un index sur la formule actuelle** ⭐ recommandé | **A — réécrire la condition + petit index** |
|---|---|---|
| geste | `create index concurrently … on app_console_photo ((greatest(derives_generes_le, absent_depuis)))` | patch par ancre sur la ligne `where` + `create index … (absent_depuis) where absent_depuis is not null` |
| la fonction | **INTACTE** (empreinte `ec806661` inchangée) | modifiée (nouvelle empreinte) |
| taille | ~440 000 entrées (quelques Mo) | 462 entrées |
| retour arrière | `drop index` | inverse par ancre + `drop index` |
| risque | ⚠ **à prouver** : que le planificateur reconnaisse l'expression telle qu'elle est écrite dans la fonction (`EXPLAIN` avant/après dans la répétition) | ⚠ à prouver : que Postgres combine les deux index (BitmapOr) |

**Pourquoi B** : c'est **purement additif** (règle « ne pas écraser le code existant »). Il ne touche ni la
fonction, ni le verrou des masquées (`visible is not false`), ni le correctif du 20/10, ni le worker. Et le
patch inverse du 20/10 resterait applicable tel quel.

**Conditions de pose (les deux formes)** : `concurrently` (pas de verrou d'écriture sur la table), **en dehors
de 05:00 → 07:45** (run et descente), **et en dehors d'un geste photo**. Puis **relancer UNE fois le script
complet** (`node Console/remplir_adresses_photos.js`) : il refait les galeries en retard **et** le registre
et le « sans photo » qui n'ont pas tourné le 24/10. Fenêtre par défaut de 48 h : suffisante jusqu'au 25/10 vers
07:04 (dernier succès le 23/10 à 07:04). Au-delà, l'appeler sur une fenêtre plus large.

**La répétition doit cette fois CHRONOMÉTRER** la fonction **dans les conditions de la nuit** : l'appeler par
l'API (`rpc`), pas depuis l'éditeur SQL, et exiger **< 2 s**, avec `EXPLAIN ANALYZE` avant et après.

**Hors correctif, noté :** la table a 69 107 lignes mortes et pas de nettoyage automatique depuis le 27/09.

### ✅ APPLIQUÉ LE 24/10 À 22:05, AVEC L'ACCORD DE FRÉDÉRIC (forme B)

Fichiers : `supabase/patch_photos_index_derniere_date_2026-10-24.sql` (+ `_INVERSE`, `_REPETITION`), commit `b95bcbd`.
Vérifié avant : l'entretien de 22:00 ne traite plus que les documents (ligne photos retirée le 19/10), file
de travaux vide.

| étape | résultat |
|---|---|
| répétition (transaction annulée) | avant : lecture complète **5 360 ms** · après : **index, 31 ms** · **mêmes dossiers (26 = 26)** · fonction entière **ok en 419 ms** · empreinte **inchangée** · retour : index retiré |
| ① contrôles | tous OK (22:05, aucun geste photo) |
| ② index `concurrently` | **valide, prêt, 4 752 kB** |
| ② bis `analyze` | fait (la précédente datait du 27/09) |
| ③ plan | **Index Scan using app_console_photo_derniere_bouge_idx, 1,2 ms** · empreinte `ec806661` **inchangée** |
| ④ rattrapage **par l'API** (`node Console/remplir_adresses_photos.js`) | **`app_photos_remplir_adresses_app : 0,3 s`** (contre 57014 à 8 s) · 115 cibles, 15 vivantes remplies · registre 2,1 s ok · sans photo 0,2 s ok · code 0 |
| contrôle des dégâts | **0** galerie en retard · **0** photo masquée exposée (les 2 de 59203 sont sorties) · **0** photo retirée encore affichée (les 86) · **0** vivante vide |

⚠ **Reste à voir** : le battement `workers.heartbeat:phase2.adresses_photos` n'est écrit **que par le run** →
l'alerte rouge reste jusqu'au run du **25/10 vers 07:05**. Contrôle du matin : l'étape doit être `DONE … attempt 1/2`
dans `.tmp/full_pipeline_20261025_050002.log`, et le chrono `(app_photos_remplir_adresses_app : …)` sous 1 s
dans `logs/scheduled/quotidien_2026-10-25_05-00-02.log`.

### Les leçons

1. **Un correctif se mesure aussi en TEMPS** — la répétition du 20/10 a vérifié le résultat, pas la durée.
   (Mémoire `mesurer-le-temps-pas-seulement-le-resultat`, déjà payée une fois.)
2. **Une fonction autour d'une colonne indexée tue l'index** : `greatest(col, …)`, `coalesce(col, …)`,
   `col::date`… → écrire la condition sur la colonne nue.
3. **Une 2e tentative qui réussit cache une dégradation** : le battement devrait dire « réussi au 2e essai ».

## 2 ter. AUDIT — les 11 « transactions disparues » (n° 7) — 24/10 au soir

**Verdict : AUCUNE n'a été supprimée chez Hektor, et ce N'EST PAS lié aux correctifs du registre des
transactions. Ce sont 11 transactions que la liste de Hektor a SAUTÉES pendant sa lecture.** Lecture seule
(base, miroir `data/hektor.sqlite` en `mode=ro`, journaux).

**1. Le profil.** 10 compromis + 1 vente, tous sur des biens **vendus ou archivés**, tous vus au run du 23/10
(04:46 UTC) et absents de celui du 24/10. **Chacun de ces biens a une autre transaction du même type encore
présente**, vue depuis le 31/07 (ex. 9247 : 12629 « disparu », 12627 présent).

**2. Ce n'est pas l'app.** Aucun travail de l'app sur ces 11 biens depuis juin (seulement des synchros de
documents). Le **patch V** (23/10 18:54, « compromis verrouillé par sa vente ») **refuse des gestes**, il ne
marque rien. La logique d'absence de `phase2/sync/affaire_ledger.py` (l. 940-974) n'a pas bougé ; la pièce 2
du 24/10 est arrivée **après** le run, et **éteinte**.

**3. Ce n'est pas le registre : c'est la LISTE de Hektor.** Le miroir local (réécrit chaque nuit, 06:27) ne
contient plus les 11 numéros. Et la liste brute de cette nuit (`raw_api_response`, run 5207) le prouve :

| liste (nuit du 24/10) | total annoncé par Hektor | reçus | distincts | doublons | manquants |
|---|---|---|---|---|---|
| `list_compromis_update` | **10 626** | 10 646 | **10 616** | 30 | **10** |
| `list_ventes_update` | **9 267** | 9 287 | **9 266** | 21 | **1** (la vente « 2 ») |
| `list_offres_update` | 11 193 | 11 213 | 11 193 | 20 | 0 |

**Toutes les listes ont 20 doublons, même celles de mars et de mai** : une page lue deux fois à chaque passage,
sans conséquence. **Ce qui dépasse ces 20 correspond exactement aux manquants** (10 et 1) : la liste, triée
par date de mise à jour et lue en **10 minutes** (06:02 → 06:12), a **glissé** pendant la lecture. Des lignes
ont été lues deux fois, d'autres jamais. Les 11 « disparues » sont **exactement** les lignes sautées : Hektor les
compte encore dans son propre total.

**4. Ce n'est pas nouveau.** `normalize_source.py` l. 1269-1311 décrit le même phénomène le 16/09 (compromis
22976 : *« la liste de Hektor ne le compte pas »*). La relecture une par une, qui l'aurait évité, a été **coupée
le 18/09 par décision de Frédéric** : elle faisait bloquer notre IP. D'habitude, 1 ou 2 lignes sont sautées par
nuit ; cette nuit, 11.

**5. Conséquence et durée de vie.** Le registre **ne supprime rien** : il marque `present_in_hektor = false`,
et la ligne **revient d'elle-même** quand Hektor la relistera. L'alerte compte les absentes **vues il y a moins
de 48 h** : ces 11 en sortent **seules** le 25/10 vers 06:46, même si elles restaient absentes. Le compromis
59056, « disparu » le 20/10, est d'ailleurs **revenu** depuis.

### ⭐ CONTRE-AUDIT EN DIRECT CHEZ HEKTOR (24/10, ~22:40, demandé par Frédéric)

Une seule connexion, 1,5 à 2 s entre appels, arrêt prévu au premier 403 : **15 appels en lecture, 0 refus**.
Scripts : `scratchpad/verifier_11_transactions.py`, `scratchpad/tester_tri_liste.py` (hors dépôt).

**A. Les 11 EXISTENT chez Hektor** (`CompromisById` / `VenteById`) : 12629, 21551, 21465, 43345, 19472,
20235, 14411, 16197, 15028, 14269 répondent tous, **même bien, même date, même prix, même état** que notre
registre (status 1 = actif ×4, 2 = annulé ×6) ; la vente « 2 » répond aussi. **AUCUNE SUPPRESSION.**

**B. LA CAUSE EXACTE : un tri qui n'est pas unique.**
1. La nuit demande `ListCompromis` avec `sort=dateStart&way=DESC` (`sync_raw.py` l. 1550). **Hektor ignore ce
   tri** (constaté le 23/10 dans `transactions_annonce_from_api.py` : changement chez Hektor entre le 18/09 et
   le 22/10) et range la liste **par numéro d'annonce décroissant** (page 0 : 63046, 63037, 62967…).
2. **Plusieurs compromis partagent le même numéro d'annonce** (un compromis annulé puis un nouveau sur le même
   bien). Pour ces ex-aequo, la base de Hektor ne garantit **aucun ordre** d'une page à l'autre.
3. Quand un groupe d'ex-aequo tombe **à cheval sur deux pages**, la page N le finit avec un compromis, la page
   N+1 le recommence **avec le même**, et le voisin **n'est jamais lu**.
4. **Preuve dans la liste de la nuit, pour les 10 compromis, sans exception** : le voisin du même bien est en
   **position 19 de la page N ET en position 0 de la page N+1**, le « disparu » n'est nulle part. Ex. bien
   9247 : 12627 en 185/19 et 186/0, 12629 absent.
5. **Preuve en direct** : pages 185 et 186 redemandées avec les paramètres exacts de la nuit → 185 finit par
   12627, 186 commence par 12627, **12629 n'apparaît pas** (idem 24781).
6. **Pourquoi la liste change d'une nuit à l'autre** : chaque compromis créé ou retiré décale tous les suivants,
   donc les frontières de pages bougent. Un compromis peut être sauté une nuit, relu la suivante → il
   « disparaît » puis « revient » (59056 le 20/10). C'est aussi l'explication probable du « fantôme » 22976 du
   16/09, que les huit hypothèses de l'époque n'expliquaient pas : **elles ne testaient pas les frontières de
   pages**.
7. **Les 20 doublons fixes** : la nuit commence à `page=0`, et Hektor rend **la même chose pour 0 et 1**. Inoffensif
   (533 appels au lieu de 532).
8. **Ventes** : même mécanisme (la vente « 2 » de 45672, dont le bien porte aussi la vente 2713). Et
   `ListVentes` **ignore aussi `sort=id`** (testé en direct : non trié) — le bon paramètre reste à trouver
   (`transactions_annonce_from_api.py` utilise `order=` et non `way=` pour les ventes).

**C. Le tri qui marche.** `ListCompromis` avec **`sort=id&way=ASC`** est **respecté** (testé en direct :
strictement croissant, total 10 626). Le numéro de transaction est **unique** : plus d'ex-aequo, plus de
frontière ambiguë. Et en **croissant**, un compromis créé pendant la lecture s'ajoute **à la fin** : il ne
décale rien.

**D. L'ampleur aujourd'hui.** Le registre porte **28 lignes marquées absentes** (21 compromis, 5 offres,
2 ventes) depuis le 07/09. Après cette mesure, **une partie d'entre elles sont probablement des fantômes du même
mécanisme** : non vérifié une à une.

### Le remède, en deux pièces (NON fait — code du run, il faut un « vas-y »)

| pièce | où | quoi | effet |
|---|---|---|---|
| **1 — la cause** | `sync_raw.py` l. 1550-1551 | compromis : `sort=id`, `way=ASC` au lieu de `dateStart`/`DESC` | plus d'ex-aequo → plus de compromis sauté. Sans effet sur la couverture : la nuit lit TOUTES les pages (`CompromisRecentLimit=999999`) |
| **2 — le filet** | `normalize_source.py`, `aligner_miroir_sur_hektor` ~l. 1394 | ne rien retirer du miroir quand **distincts reçus < `metadata.total`** | protège aussi les ventes (dont le tri n'est pas encore réglé) et tout autre glissement. **Zéro appel de plus chez Hektor** |
| (plus tard) | — | trouver le tri unique des ventes ; vérifier une à une les 28 absentes (prudemment) | — |

Ce que ça pourrait casser ailleurs : la pièce 1 change l'ORDRE de lecture, pas la couverture — à vérifier que
rien ne s'appuie sur « les premières pages = les plus récents » pour les compromis en mode update (le plafond de
pages vaut 999999/20, donc non bloquant aujourd'hui). La pièce 2 peut retarder d'une nuit une vraie suppression.

### ⭐⭐ AUDIT DU CORRECTIF — code, notes, historique (24/10, ~23:30, demandé par Frédéric)

> Code relu par moi ; notes et historique relus par un agent (rapport intégré ici) ; mesures sur
> `raw_api_response` ; **18 lectures de plus chez Hektor** (sort=id DESC sur 8 pages, 3 essais de tri des
> ventes), 0 refus. **Le remède ci-dessous REMPLACE celui du §6 plus bas**, sur deux points (le sens du tri, et
> le filet qui ne regarde qu'une nuit).

**1. La meilleure preuve était déjà dans le projet.** Les **listes d'annonces** sont lues **par numéro**
(`sort=id`) : la nuit dernière, **10 listes, ~61 000 lignes, 0 doublon, 0 manquant**. Mesure de toutes les
listes paginées du 24/10 :

| liste | tri demandé | total annoncé | distincts | manquants |
|---|---|---|---|---|
| annonces (10 variantes) | **id** | ~61 000 | identiques | **0** |
| offres | date (ignoré : rangé par numéro décroissant, uniques) | 11 193 | 11 193 | 0 |
| **compromis** | dateStart (ignoré : rangé par **annonce**) | 10 626 | 10 616 | **10** |
| **ventes** | aucun | 9 267 | 9 266 | **1** |

Précédent écrit : en **mars 2026**, les relectures complètes des annonces et des contacts sont passées de
`datemaj` à **`sort=id&way=ASC`** parce que *« sur un run long, ce tri est instable »* (REPRISE_SYNC_2026-03-21.md
l. 320-345). **Même défaut, même remède, déjà appliqué ailleurs.**

**2. Pourquoi `dateStart` : jamais vérifié.** Choisi le 19/03 (`notice/SYNC_UPDATE_TRANSACTIONS_NOTE.md`
l. 60-77), avec un point resté ouvert : *« vérifier en pratique le comportement sur ListCompromis avec
sort=dateStart »* (l. 140). Personne ne l'a clos. Le refus de `sort=id` écrit dans `sync_raw.py` l. 1536 vaut
**pour les mandats seulement** (deux espaces de numéros) ; il ne s'applique pas aux compromis.

**3. ⚠ LE SENS DU TRI : DÉCROISSANT, PAS CROISSANT (je corrige ma proposition).** Le code suppose « premières
pages = plus récents » : en mode update, le plafond de pages vaut `ceil(compromis_recent_limit / 20)`, et la
**valeur par défaut est 1 000** (`sync_raw.py` l. 1623). La nuit passe 999 999 (lecture complète depuis le 07/09,
commit `aa361fb`), mais **un lancement sans ce paramètre lirait, en croissant, les 1 000 PLUS ANCIENS**.
**`sort=id&way=DESC`** garde l'ordre « récents d'abord » : **vérifié en direct** sur 8 pages (début, milieu,
fin) — strictement décroissant, jonctions exactes (50110→50109, 21082→21081, 15664→15663, 12563→12562), aucun
doublon, de 50137 à 12556. C'est aussi le tri du worker depuis le 23/10 (commit `2704dee`).

**4. Ventes : AUCUN tri par numéro possible.** `ListVentes` ignore `sort=id` (avec `way=` ou `order=`, testé en
direct). Elles reposeront **sur le filet seul**.

**5. Deux risques trouvés par l'audit, qui changent le filet.**
- `fetch_latest_raw_payloads` (`hektor_pipeline/common.py` l. 983) prend **pour chaque page sa version la plus
  récente, toutes nuits confondues**. Une nuit **interrompue**, ou une liste qui **raccourcit**, laisserait des
  pages d'une nuit précédente — rangées autrement. Ce matin, 533 pages sur 533 venaient de la même nuit (pas de
  mélange) ; le risque existe pourtant, avec ou sans changement de tri. ➡ **Le filet doit compter UNIQUEMENT les
  pages de la dernière nuit.**
- **Un refus qui se répéterait chaque nuit gèlerait le miroir sans bruit** (cas possible pour les ventes, dont le
  tri n'est pas réglable). La mesure d'une seule nuit ne dit pas la fréquence. ➡ **Le refus doit être écrit au
  journal ET compté par le moniteur** (alerte si plusieurs nuits d'affilée).

**6. Ce que les notes confirment.** La nuit lit tout (le tri ne change pas la couverture) · `metadata.total` a
déjà été proposé deux fois (L10-8 et L10-8a, jamais codé) · la relecture une par une reste interdite sans mémoire
des verdicts ni arrêt net au 403 (18/09) · le registre ne supprime jamais, il marque et la ligne revient · le
filet va dans le sens de *« le miroir témoigne, il n'exécute pas »* et de *« un numéro ne se perd jamais »*.
**Ce qu'elles contredisent** : la conclusion du 16/09 (`ba7679d`), *« notre lecture est complète »*, qui ne
testait pas les frontières de pages.

### ✅ LE CORRECTIF RETENU APRÈS AUDIT (NON fait — code du run, il faut un « vas-y »)

| pièce | où | quoi |
|---|---|---|
| **1** | `sync_raw.py` l. 1550-1551 (mode update) | compromis : **`sort=id`, `way=DESC`** au lieu de `dateStart`/`DESC`. Couverture inchangée, ordre « récents d'abord » gardé |
| **2** | `normalize_source.py`, `aligner_miroir_sur_hektor` (~l. 1394) | ne compter que les pages de **la dernière nuit** (`run_id` le plus récent de l'endpoint) ; **si distincts < `metadata.total` de cette nuit → aucune suppression**, et le dire au journal. Vaut pour offres, compromis, ventes. 0 appel Hektor |
| **3** | moniteur | compter les refus du filet ; **alerte si 3 nuits de suite** sur un même type (sinon le miroir gèlerait en silence) |
| essais | — | rejouer la liste brute du 24/10 : le filet doit refuser compromis et ventes, accepter offres ; témoin inverse : une liste complète doit passer |

**Ce que ça pourrait casser ailleurs** : une vraie suppression attendra une nuit complète (au moins une nuit) ;
les ventes pourraient être refusées souvent (fréquence inconnue — c'est ce que le moniteur dira) ; le mode
bootstrap (`run_phase1_safe.ps1`, manuel) n'a aucun tri et garde le défaut : à traiter à part s'il resservait.

### 🔧 ÉCRIT ET ÉPROUVÉ LE 24/10 À ~23:55 — RANGÉ SUR LA BRANCHE `filet-listes` (commit `bce8c4e`), PAS SUR `main`

⚠ **Changement de conception pendant l'écriture** : le filet « on ne retire rien si la liste est incomplète »
était **mauvais**. La boucle d'upsert relit aussi l'instantané de mars, qui réinjecte chaque nuit ~10 compromis
**vraiment supprimés** ; tout bloquer les aurait fait « revenir » au registre pour un jour, puis « redisparaître »
→ fausses alertes. Le filet **ne garde que les candidats dont le bien a un voisin lu en double** (signature de
l'ex-aequo sauté), et ne refuse tout que si des manquants restent **inexpliqués** ou si la liste **mélange deux
nuits**.

| pièce | interrupteur (`.env`) | éteint (défaut) |
|---|---|---|
| tri des compromis `sort=id&way=DESC` (`sync_raw.py`) | `APP_COMPROMIS_TRI_ID=1` | `dateStart`, comme avant |
| filet (`normalize_source.filet_liste_incomplete`) | `APP_MIROIR_FILET_LISTE=1` | **JOURNAL SEUL** : écrit `[miroir] FILET … AURAIT garde …`, ne garde rien |
| alerte `data.miroir_filet` (`check_gti_health.py`) | — | warning si un type est refusé 3 nuits de suite |

**Épreuves** (`phase2/checks/test_filet_liste_incomplete.py`) : **18/18** sur une liste fabriquée (complète,
sautée, journal seul, inexpliqué, deux nuits, sans total ; tri éteint/allumé, offres intactes) · **rejeu de la
vraie nuit du 24/10** (`--nuit-reelle`, base temporaire) : compromis **10 gardés = exactement les 10 « disparus »**,
10 retirés = les fantômes de mars ; ventes **la vente « 2 » gardée**, 1 retirée ; offres **COMPLETE**, 5 retirées ·
alerte **6/6** sur journaux fabriqués · moniteur complet en `--dry-run` : sans erreur, la ligne
`data.miroir_filet` apparaît · compilation OK · fins de ligne homogènes · diff **purement additif** (402 +, 0 −).

**Trouvé en passant, NON lié** : `phase2/checks/test_alignement_suppression.py` (6 échecs) et
`phase2/checks/test_c6_miroir_propre.py` (3 échecs) échouent **déjà sur le code d'avant** (vérifié en remettant
les fichiers à HEAD). À regarder à part.

**Rangé sur une branche** pour tenir la promesse faite à Frédéric : *« te les montrer avant qu'elles tournent
la nuit »*. Le run de 05:00 lit le dossier principal : **la nuit du 25/10 tourne exactement comme celle du 24/10**.

### ✅ MIS EN SERVICE LE 25/10 VERS 00:05 — « vas-y, maintenant » de Frédéric

- Commit `9dc69ae` sur `main` (reprise de `bce8c4e` ; la branche `filet-listes` est supprimée).
- `.env` (non suivi par git) : **`APP_COMPROMIS_TRI_ID=1`** et **`APP_MIROIR_FILET_LISTE=1`**, ajoutés en fin de
  fichier avec un commentaire. Vérifié par `Settings.from_env()` comme le run : compromis demandés en
  `sort=id, way=DESC, withCompromisStatus=false`, offres inchangées ; essais verts sur `main`.
- **Retour arrière : remettre les deux interrupteurs à 0** (le code éteint = le comportement d'avant, prouvé par
  l'essai). Aucun redémarrage de service : `sync_raw` et `normalize_source` relisent `.env` à chaque run.
- ⏰ **À vérifier au run du 25/10** (`logs/scheduled/quotidien_2026-10-25_05-00-02.log`) :
  `[miroir] FILET compromis (ACTIF) : … manquants 0 … -> COMPLETE` (le tri par numéro ne doit plus sauter
  personne) ; pour les ventes, `COMPLETE` ou `SAUTES EXPLIQUES` ; le nombre de `retiree(s)` des compromis doit
  tomber à ~10 (les fantômes de mars) au lieu de ~20 ; `data.transaction_disparue` ne doit plus compter de
  compromis sautés ; et les 11 du 24/10 doivent **revenir** présents au registre (`present_in_hektor = true`).

**6. Le remède proposé (NON fait — c'est du code du run, il faut un « vas-y »).** *(⚠ remplacé par le
correctif retenu ci-dessus.)* Un garde-fou **sans aucune
requête de plus chez Hektor** (donc sans risque de blocage d'IP) : **ne rien retirer du miroir pour un type
quand le nombre de distincts reçus est inférieur au total annoncé par Hektor** (`metadata.total`). Cette nuit,
il aurait refusé 2 suppressions (compromis, ventes), et les 11 seraient restées présentes. Les vraies
suppressions passeraient la nuit suivante, quand la liste serait complète. À écrire dans
`aligner_miroir_sur_hektor` (`normalize_source.py` ~l. 1394), à côté du garde-fou « liste tronquée < 50 % ».

## 2 quater. TRAITÉ DANS LA NUIT DU 24 AU 25/10, AVEC L'ACCORD DE FRÉDÉRIC

**Les 6 travaux d'essai (n° 4 et 5) sont TRANCHÉS « J'ai refait »** (~00:40). Même ligne que
`app_action_resolve(mode='refait')` — un `INSERT` dans `app_pending_resolution`, gardes comprises (en erreur,
> 3 h, pas déjà tranché) — écrite directement parce que la fonction vérifie la session de l'app.
`resolved_by` = « claude (accord de Frederic, 25/10/2026 …) ». Aucune donnée touchée, rien chez Hektor.
Moniteur (dry-run) : `travaux_en_erreur` **0** (11/11 tranchés), `geste_abandonne` **0**.

**Les 8 écarts d'essai (n° 8 et 9) sont marqués « VUS »** (~00:51). ⚠ **Je m'étais trompé** en écrivant qu'il
n'existait aucun « j'ai vu » durable : les deux sondes se taisent dès que `traite_le` est posé, par
`app_annonce_naissance_ecart_traiter(app_dossier_id)` et `app_contact_modif_ecart_traiter(job_id)` (admin). **Mais
AUCUN bouton de l'app ne les appelle** (0 occurrence dans le front) : c'est pourquoi je l'avais manqué.
Fait par la même mise à jour que ces fonctions : `app_annonce_saisie_naissance` (10000009 / 63331) et
`app_contact_saisie_modif` (jobs `816b4427…` = 20000007, `7f050b73…` = 20000008). `traite_par` laissé vide
(aucune session d'app). Sondes : **0 / 0**.

**Reste au monitoring (dry-run 25/10 ~00:55) : 4 alertes, toutes à extinction automatique** — photos (×2 rouges)
et journal du run au run de 05:00 ; transactions disparues vers 06:46. Plus l'orange de fond du battement
(5 workers « sans premier signe »), qui demande une décision.

➡ **À proposer** : un bouton « Vu » sur la fiche annonce et la fiche contact, qui appelle ces deux fonctions.

## 2 quinquies. LE RUN DU 25/10 (04:00 → 06:22, passage à l'heure d'hiver) — CONTRÔLE

`Pipeline finished successfully` à 06:22:40.

| point | résultat |
|---|---|
| adresses photos | ✅ **DONE au 1er essai** (06:17:36 → 39) ; par l'API **0,7 s** (à froid) ; registre 1,6 s ; sans photo 0,1 s ; battement « Retour à la normale » |
| filet compromis | ✅ **COMPLETE** : 10 626 distincts = 10 626 annoncés, **0 doublon hors page 0** → le tri par numéro tient sur TOUTE la liste ; 10 retirées = les fantômes de mars (au lieu de ~20) |
| filet ventes | ✅ **SAUTES EXPLIQUES** : la vente « 2 » encore sautée par Hektor, **gardée** |
| filet offres | ✅ COMPLETE |
| les 11 du 24/10 | ✅ **toutes revenues présentes** au registre (vues 06:01:17) |
| balayage des masquées | ✅ 0 masquée dans une boîte publique ; 7 520 restantes (8 nuits) ; 2 points déjà connus (plafond 922, 63073) |
| ménage des orphelins | ❌ toujours en échec (DELETE sans WHERE) — c'est lui qui laisse `logs.pipeline.latest` en orange (mot « failed » en fin de journal) |

⛔ **INCIDENT CAUSÉ PAR MOI : le moniteur n'a rien écrit de 01:48 à ~07:35.** Ma nouvelle ligne
`data.miroir_filet` portait `domain = "data"`, que la contrainte `app_monitor_status_domain_check` refuse
(liste : system, business, mixed, data_quality, workers, cron, surface, scheduledtasks, email). **Une seule
ligne refusée fait tomber tout le lot** : 23514 à 01:48, 02:48, 04:48, 06:48 — la tâche rendait pourtant le
code 0. Le `--dry-run` ne pouvait pas le voir (il n'écrit pas), et j'avais affirmé « une nouvelle clé se crée
seule » **sans lire les contraintes de la table**. Corrigé (`9bb5b4c`) : `data_quality` ; tous les domaines
littéraux du fichier vérifiés contre la contrainte. Second défaut corrigé au passage : le journal du run coupe
les lignes longues, le verdict du filet tombait sur la ligne suivante. Moniteur relancé pour de vrai :
**« Monitor results written to Supabase », 0 critical, 2 warning** (`console.jobs.errors` jusqu'à ~17:22 ;
`logs.pipeline.latest` à cause du ménage).

## 2 sexies. AUDIT — POURQUOI LE MÉNAGE DES ORPHELINS DE RECHERCHE ÉCHOUE CHAQUE NUIT (25/10)

> Lecture seule (fonction, journaux, historique git, notes). Une relance du script par l'API m'a été refusée par le
> garde-fou de la session (écriture en production) : non contournée — les journaux de 9 nuits la remplacent.

**1. La ligne fautive.** `app_sweep_search_orphans()` (empreinte `be11efc3e8134afa50ba7ca47b0681e8`), 2ᵉ instruction :

    create temporary table if not exists _cible_sweep (...) on commit drop;
    delete from _cible_sweep;          <- SANS WHERE

C'est le vidage d'une **table temporaire de travail** (défensif : si la fonction était appelée deux fois dans la
même transaction). Toutes les autres écritures de la fonction ont une condition.

**2. Pourquoi seulement par l'étape du run.** Le rôle de l'API (`authenticator`) charge **`safeupdate`** à chaque
connexion (`rolconfig : session_preload_libraries=safeupdate`), qui refuse tout `DELETE`/`UPDATE` sans `WHERE`
(code `21000`). Le compte `postgres` (éditeur SQL, `pg_cron`) ne le charge pas (`session_preload_libraries =
supautils`) — d'où : **la tâche planifiée Supabase n° 11 réussit chaque jour, l'étape du run échoue chaque nuit**.
Vérifié : `load 'safeupdate'` est interdit depuis l'éditeur (« access to library not allowed ») et, sans lui, les
trois formes (`delete` nu, `where true`, `truncate`) passent.

**3. La preuve, chaque nuit, dans le journal du run** (`logs/scheduled/quotidien_*.log`) depuis le **16/10** :
`!! menage des orphelins impossible : ... HTTP 400: {"code":"21000", ... "DELETE requires a WHERE clause"}`. Le
journal principal (`.tmp/full_pipeline_*.log`) ne dit que `failed ... (exit code 1)` : **le message existait, il
n'était pas lu.**

**4. L'histoire — une réserve non traitée devenue le bug.**
- `d8bd405` (20/08) : la fonction naît, avec ce `delete` nu ; elle tourne par `pg_cron` (pas de safeupdate) — elle
  n'a jamais été appelée par l'API avant le 14/10.
- `2dd9ee5` (14/10, go de Frédéric) : l'étape du run est ajoutée pour **supprimer une course** (le cron de 05:00 UTC
  passait 48 s avant le push des contacts). Le script n'a **pas** été lancé avant (il écrit en production) ; seuls
  les droits ont été lus.
- `87e7548` (15/10) : 1ʳᵉ nuit, échec sur un autre défaut (`TypeError`, corrigé + `--essai-a-vide`). Même commit :
  l'étape était « inutile » **pour ce rattrapage-là** mais « garde un intérêt pour l'AUTRE porte (la clé qui
  change) », et **⬜ RESTE : « demain, vérifier que l'étape corrigée tourne et que logs.pipeline.latest redevient
  vert »**. **Cette vérification n'a jamais été faite.** L'`--essai-a-vide` s'arrête AVANT l'appel : il ne pouvait
  pas voir un refus de la base.
- Du 16/10 au 25/10 : 10 nuits sur 10 en échec.

**5. Ce que ça a coûté — mesuré.**
- **Aucune donnée** : le cron n° 11 tourne chaque jour, et **depuis le 16/10 il n'a rien eu à faire** (0 rattachée,
  0 supprimée, `app_sweep_search_orphans_log`).
- **Du bruit permanent** : `logs.pipeline.latest` en orange (le mot « failed » est dans la fin du journal) ; le
  battement `phase2.menage_orphelins_recherche` n'a **jamais** de succès (`last_success_at` vide) → il fait partie
  des 5 « sans premier signe » de `workers.heartbeat`.
- ⚠ **La course est REVENUE avec l'heure d'hiver** : le cron (05:00 UTC) passe désormais à **06:00** Paris, et le push
  des contacts a eu lieu à **06:11** le 25/10 — le ménage repasse AVANT le push, exactement ce que l'étape devait
  empêcher. Sans effet tant qu'il n'y a rien à nettoyer.

**6. Les jumeaux.** Dans toute la base, seules 3 fonctions ont un `DELETE` sans condition : celle-ci, et
`app_bascule_identite_contact` / `…_annuler` (vraies tables, opération **ponctuelle** du 23/09, lancée **à la main
depuis l'éditeur** selon `notice/PROCEDURE_BASCULE_CONTACT.md`, aucun appel par l'API → non touchées). **Aucun
`UPDATE` sans `WHERE`** dans la base.

**7. Le correctif proposé (NON fait — écriture en base, il faut un « vas-y »).**

| | quoi | effet |
|---|---|---|
| **A** ⭐ | une ligne : `delete from _cible_sweep where true;` (patch par ancre unique, empreinte `be11efc3` vérifiée avant, inverse, répétition) | l'étape du run passe → la course disparaît, le battement a son premier succès (« sans premier signe » 5 → 4), `logs.pipeline.latest` repasse au vert. Le cron reste le filet |
| B | retirer l'étape du run (le cron seul) | plus de bruit, mais la course reste (aggravée l'hiver) et la clé de registre reste sans succès |

⚠ **Ce que A pourrait casser ailleurs** : rien dans la fonction (le `where true` vide exactement la même table) ;
mais l'étape va enfin **écrire chaque nuit** après le push — c'était la décision du 14/10, et la fonction est
idempotente (0 ligne touchée ces 10 derniers jours). **Preuve possible seulement APRÈS la pose** : la répétition
peut prouver que la fonction modifiée rend le même résultat (en transaction annulée, compte `postgres`), mais pas
le passage de `safeupdate` — c'est le run suivant qui le prouvera (`DONE … attempt 1/2`, battement `success`).

### ⚠ CONTRE-AUDIT DU CORRECTIF (25/10, demandé par Frédéric) — LA LIGNE SEULE NE SUFFIT PAS

**1. La durée réelle, par le cron (`cron.job_run_details`, job 11, 20 jours)** : 1,5 à 4,3 s en général, mais
**5,6 s** (12/10), **10,5 s** (11/10) et **8,5 s ce matin à 06:00, pendant le run**. Par l'API, la limite est
**8 s** (`authenticator : statement_timeout=8s, lock_timeout=8s`). ➡ **Avec la seule ligne corrigée, l'étape aurait
été coupée ce matin** (57014), comme les adresses photos le 24/10. Sa répétition, jouée dans l'éditeur (sans
limite), ne l'aurait pas vu — le piège exact du 20/10.

**2. Pourquoi c'est lent la nuit, pas le jour.** Mesuré à froid de jour (lecture seule) : la grosse suppression
(`app_rapprochement`, 53 624 lignes, 186 Mo) **0,94 s**, l'historique (`app_rapprochement_score_history`, 150 Mo)
**0,13 s**, le reste négligeable. La nuit, d'autres tâches planifiées travaillent **sur les mêmes tables au même
moment** : `app_process_rapprochement_dirty` **11,3 s à 06:09**, `app_generate_rapprochement_alerts` **7,3 à 7,6 s
toutes les 5 min** (06:05, 06:10, 06:15) — l'étape passe à ~06:11. Attente de verrous + charge = le temps en plus.

**3. Le remède existe, et il est officiel.** Doc Supabase « Timeouts », *Function level* : un `set statement_timeout`
posé **sur la fonction** *« works with the Database REST API »* (plafond client 60 s), *« for recurring functions
that need a special exemption »*. Aucune fonction du projet ne l'utilise encore (mesuré : 0). Le script attend
300 s côté client : pas de coupure de son côté.

**4. Le reste est vérifié** : `service_role` a le droit d'exécuter ; la fonction n'appelle aucune autre fonction ;
aucune autre écriture sans `WHERE` dedans ; le journal `app_sweep_search_orphans_log` (clé `run_at`) accepte deux
passages par nuit (`on conflict do nothing`).

### ✅ LE CORRECTIF RETENU (NON fait — écriture en base, il faut un « vas-y »)

| pièce | quoi |
|---|---|
| 1 | `delete from _cible_sweep where true;` (au lieu de `delete from _cible_sweep;`) — ancre unique, empreinte de départ `be11efc3…` vérifiée |
| 2 | `alter function public.app_sweep_search_orphans() set statement_timeout = '60s';` **et** `set lock_timeout = '30s';` |
| 3 | `notify pgrst, 'reload schema';` — l'API relit les réglages des fonctions |
| inverse | remettre la ligne nue, `reset statement_timeout`, `reset lock_timeout`, recharger le schéma |
| répétition | en transaction annulée : patch, empreinte, `proconfig` lu, appel de la fonction (résultat `ok`), retour |

**Ce que la répétition ne peut PAS prouver** (comme le 24/10) : le passage par l'API avec `safeupdate` et le délai.
**La preuve sera le run suivant** : `DONE phase2 menage orphelins de recherche attempt 1/2` dans
`.tmp/full_pipeline_*.log`, une réponse `{"ok": true, ...}` dans `logs/scheduled/quotidien_*.log`, le battement
`phase2.menage_orphelins_recherche` avec un `last_success_at`, et `logs.pipeline.latest` au vert.

**Ce que ça pourrait casser ailleurs** : le cron n° 11 appelle la même fonction — 60 s reste sous son plafond de
2 min, rien ne change pour lui ; l'étape écrira chaque nuit après le push (décision du 14/10), fonction idempotente,
0 ligne touchée ces 10 derniers jours. Un `lock_timeout` de 30 s peut faire attendre la fonction derrière le
recalcul des rapprochements : c'est voulu (attendre plutôt qu'échouer), et elle reste non bloquante pour le run.

**Noté en passant** : à 06:48, le moniteur a eu un **57014 sur `rpc/app_cron_health`** (même délai de 8 s) —
c'est la sonde des tâches planifiées. Non traité.

## 3. Ce qu'on peut retirer tout de suite, sans toucher à aucun garde-fou

- **n° 4 et n° 5** : trancher les 6 lignes dans l'écran Santé. Elles sortent du compte, la sonde reste.
- **n° 6** : rien à faire, elle s'éteint d'elle-même le 25/10.
- **n° 1, 2 (rouge), 3, 10** : s'éteignent si la nuit prochaine passe.

**Ce qui demande une décision :** la vue (§0), les 5 workers « sans premier signe » (n° 2), la vérification
des transactions (n° 7), et l'étape de ménage (§2).
