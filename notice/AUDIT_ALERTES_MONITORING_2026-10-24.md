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

### 🔍 CE QUE LE CORRECTIF POURRAIT CASSER AILLEURS (25/10, demandé par Frédéric) — 4 trouvailles

| # | trouvaille | gravité | conséquence pour le correctif |
|---|---|---|---|
| 1 | **Le script prend un refus pour un succès** (`menage_orphelins_recherche.py` l. 95-102) : si la fonction rend `{"ok": false, "raison": "conflit_unicite"}`, il rend 0 → `DONE` + battement `success`. Jamais arrivé (70 passages depuis le 21/08, tous `ok`), mais **invisible tant que l'étape échouait** | moyenne | **corriger le script** : sortir en 1 et écrire la raison quand `ok` est faux |
| 2 | **Le compte écrit au journal est faux** (l. 98) : il additionne les valeurs entières du premier niveau — c'est-à-dire `ok` (True = 1) — et pas les comptes, rangés dans `rattachees` / `supprimees`. Il écrirait **toujours « 1 ligne rattachée »** | faible (trompeur) | corriger le calcul |
| 3 | **Le délai de verrou s'appliquerait aussi à la tâche planifiée n° 11** (rôle `postgres` : `statement_timeout` 2 min, **`lock_timeout` illimité**). Un `SET lock_timeout` sur la fonction la fait passer d'illimité à la valeur posée. Le délai d'exécution (60 s) reste sous ses 2 min : sans effet | faible | prendre **45 s** (marge sous les 60 s ; plus longue attente observée ~11 s) ; dans le pire cas la tâche échoue ce jour-là, c'est écrit, et l'étape du run prend le relais |
| 4 | ⚠ **Aucun plancher avant de supprimer** : la fonction efface tout rapprochement et tout historique de score dont la recherche est **absente** de `app_contact_search_current`. Le push des contacts vide puis réécrit les recherches **contact par contact** (`delete_before_upsert`, l. 790) ; s'il plantait en route, le run s'arrête (étape bloquante, le ménage n'est pas appelé) — **mais le cron de 06:00 du lendemain tournerait sur une table abîmée**. Risque **déjà présent aujourd'hui**, indépendant du correctif ; les rapprochements se recalculent, l'**historique de score, non** | moyenne (rare, irréversible) | ajouter un **plancher** à la fonction, comme pour les photos : refuser si `app_contact_search_current` < **5 000** (11 544 aujourd'hui) — protège le cron ET l'étape |

**Vérifié sans problème :**
- **conflits avec les autres tâches** : 3 tâches planifiées touchent les mêmes tables (`app_process_rapprochement_dirty`,
  `app_generate_rapprochement_alerts`, `app_bulk_recompute_chunk`), mais sur les recherches **vivantes** ; le ménage ne
  touche que les **orphelines** — lignes disjointes. Le cron n° 11 tourne à côté d'elles depuis 70 jours sans échec ;
  **0 deadlock et 0 `lock timeout`** dans les journaux de la base sur 24 h ;
- **la relecture du schéma de l'API** (`notify pgrst, 'reload schema'`) : déjà pratiquée par le projet (16/06), sans
  coupure ;
- **l'étape tourne deux fois par nuit avec le cron** : la fonction est idempotente, son journal accepte deux passages ;
- **l'heure d'hiver** : le cron passe à 06:00, l'étape vers 06:11 après le push — l'ordre voulu le 14/10 est rétabli.

### ✅ LE CORRECTIF COMPLET APRÈS CETTE ANALYSE — **POSÉ LE 25/10 vers 08:30** (« Oui avec plancher », Frédéric)

| pièce | où | quoi |
|---|---|---|
| 1 | fonction (base) | `delete from _cible_sweep where true;` |
| 2 | fonction (base) | **plancher** : si `app_contact_search_current` < 5 000 → `{"ok": false, "raison": "plancher"}`, rien n'est touché, et c'est écrit au journal du ménage |
| 3 | fonction (base) | `alter function … set statement_timeout = '60s'` et `set lock_timeout = '45s'` ; puis `notify pgrst, 'reload schema'` |
| 4 | script du run | `ok` faux → sortie 1 avec la raison ; le compte réel (`rattachees` + `supprimees`) |
| — | inverse + répétition | répétition en transaction annulée : patch, plancher éprouvé (témoin positif ET témoin du refus), empreinte, `proconfig`, appel de la fonction, retour |

**Fichiers** : `supabase/patch_menage_orphelins_api_2026-10-25.sql` (+ `_INVERSE`, `_REPETITION`) ·
`phase2/sync/menage_orphelins_recherche.py`.

**La répétition (25/10 ~08:27, transaction annulée) — 12 mesures, toutes vertes :**

| étape | mesure | résultat |
|---|---|---|
| avant | empreinte · délais | `be11efc3…` · `search_path=public` seul |
| pose | ligne corrigée + plancher · délais · empreinte | oui · `+ statement_timeout=60s | lock_timeout=45s` · **`f39dc33f…`** |
| témoin positif | table pleine (11 544) | `{"ok": true, …}`, tous les comptes à 0, **744 ms** |
| témoin du refus | table réduite à 100 dans la transaction | `{"ok": false, "raison": "plancher", "recherches": 100}` · rapprochements **53 624 / 53 624** · historique **456 616 / 456 616** — rien effacé |
| retour | l'inverse | empreinte **revenue à `be11efc3`**, délais retirés (`search_path` gardé) |

Puis contrôle hors transaction : empreinte `be11efc3`, 11 544 recherches, journal du ménage 70 lignes — **rien n'a fui**.

**La pose (même matin)** : 5 contrôles verts — `where true` OK, plancher OK,
`search_path=public | statement_timeout=60s | lock_timeout=45s`, empreinte **`f39dc33f…`** (= celle de la
répétition), 11 544 recherches. `notify pgrst, 'reload schema'` joué.

**Le script (pièce 4)**, éprouvé avec un faux client, sans réseau, 5 cas : `ok` → code 0, « 3 ligne(s)
rattachée(s), 228 supprimée(s) » · vide → 0 / 0 · **plancher → code 1** + raison sur stderr · **conflit d'unicité →
code 1** · réponse texte → code 0 (inchangé). ⚠ Le journal du ménage n'a **jamais** porté de refus
(70 lignes, toutes `ok`) : un `conflit_unicite` sortait AVANT d'écrire au journal — inchangé.

⛔ **PAS ENCORE PROUVÉ : le passage par l'API.** L'appel du script depuis ici a été refusé par la garde de session
(écriture en production) — pas contourné. **La preuve sera le run de la nuit du 25 au 26/10** (critères plus haut).
⚠ Le script modifié n'est actif au run que s'il est sur le disque — il l'est (le run lit `C:\Hektor\Projet`), pas
besoin de pousser pour lui ; pousser reste à faire pour l'historique.

**Noté en passant** : à 06:48, le moniteur a eu un **57014 sur `rpc/app_cron_health`** (même délai de 8 s) —
c'est la sonde des tâches planifiées. Non traité.

## 2 septies. LE RUN DU 26/10 (04:00 → 06:11) — CONTRÔLE DES TROIS CORRECTIFS ✅

| point | mesure | verdict |
|---|---|---|
| **ménage des orphelins** (§2 sexies) | `DONE phase2 menage orphelins de recherche attempt 1/2` (06:01:03 → 06:01:04) ; réponse `{"ok": true, …}` et « 0 ligne(s) rattachée(s), 0 supprimée(s) » au journal `quotidien_2026-10-26_04-00-01.log` ; battement `phase2.menage_orphelins_recherche` `success` à 06:01:04 ; **journal du ménage : 2 lignes `ok` cette nuit** — le cron (06:00:00) **et, pour la première fois, l'étape du run par l'API** (06:01:03) ; aucun `plancher` | ✅ **PROUVÉ PAR L'API** |
| **adresses photos** (§2 bis) | 1re tentative, 0,6 s + 1,8 s + 0,1 s | ✅ |
| **filet des listes** (§2 ter) | offres COMPLETE (5 retirées) · compromis **COMPLETE** 10 626/10 626 (10 retirées, les fantômes de mars) · ventes SAUTES EXPLIQUES, 1 gardée | ✅ comme le 25/10 |
| **les 11 transactions** | registre : **31 086** lignes vues à 05:xx, **toutes présentes** = 11 193 + 10 626 + 9 267 ; 0 marquée absente depuis le 24/10 | ✅ |
| **moniteur 06:48** | `logs.pipeline.latest` ok ; `data.transaction_disparue` ok (0) ; **reste 1 rouge** : le balayage des photos masquées | voir dessous |

**Le seul rouge : `GTI Balayage Photos Masquees`, résultat 1.** Pas lié à ces correctifs : la tâche est partie à **23:00**
(heure d'hiver, décalage figé `+01:00`, décision du 25/10 « laisse comme cela ») et sa garde horaire (« refus après 1 h »)
a refusé : 23 > 1. Une nuit de balayage perdue, rien posé. ✅ **Déjà corrigé par une autre session** (`fdc2d33`, poussé :
fenêtre « du soir à 1 h »). Le rouge tombera après le passage de **ce soir 23:00**.

**Passager, non traité** : à 04:49 (pendant la lecture des listes Hektor), la sentinelle `data.transaction_disparue` a été
coupée à 8 s (57014) — **1re fois** pour elle ; revenue ok à 06:49 (requête mesurée à 42 ms). Même famille que
`data.rapprochement_sur_archivee` (15 coupures depuis le 04/09) et `rpc/app_cron_health` (25/10).

## 3. Ce qu'on peut retirer tout de suite, sans toucher à aucun garde-fou

- **n° 4 et n° 5** : trancher les 6 lignes dans l'écran Santé. Elles sortent du compte, la sonde reste.
- **n° 6** : rien à faire, elle s'éteint d'elle-même le 25/10.
- **n° 1, 2 (rouge), 3, 10** : s'éteignent si la nuit prochaine passe.

**Ce qui demande une décision :** la vue (§0), les 5 workers « sans premier signe » (n° 2), la vérification
des transactions (n° 7), et l'étape de ménage (§2).

## 4. AUDIT DU 26/10 — LES COUPURES À 8 s ET LE « RÉSOLU » (lecture seule, rien modifié)

*Frédéric : « audit d'abord ces points avant de proposer un correctif ».* Sources : les **362 journaux locaux** du
moniteur (`monitoring/logs/`, 26/09 → 26/10, un par passage), `app_monitor_event`, la base, le code, la doc Supabase,
et **l'audit du 14/10** (`notice/AUDIT_MONITORING_ALERTES_2026-10-14.md` §11-13), qui avait déjà traité le « Résolu ».

### 4.1 Les coupures à 8 s — sonde par sonde, sur 362 passages

| sonde | passages aveugles | ce que l'écran montre alors | cause mesurée |
|---|---|---|---|
| ⛔ **`cron.health`** (santé des 12 tâches pg_cron) | **146 / 362 (40 %)**, depuis le 26/09, **tous** `57014` sur `rpc/app_cron_health` — **y compris ce matin 06:49** | **VERT** « Santé pg_cron en attente de migration » | voir ci-dessous |
| `data.rapprochement_sur_archivee` | 13 / 362 (3,6 %), à toute heure | « illisible » (unknown) — **visible** | la vue fait 2,0 s au calme : `app_rapprochement` (53 624 lignes, 186 Mo) relue avec 32 747 retours au tas (vacuum en retard, mises à jour à la minute par 2 crons) |
| `data.actives_sans_nego` | 2 / 362 | « illisible » — visible | ponctuel |
| `data.transaction_disparue` | 1 / 362 (26/10 04:49) | « illisible » — visible | ponctuel ; 42 ms au calme. ⚠ `app_affaire_ledger` pèse **226 Mo pour 31 103 lignes** (1,25 M mises à jour) |

**⛔ LE VRAI DÉFAUT : la sonde pg_cron ment.** `check_cron_health` (`check_gti_health.py` l. 2107-2120) transforme
**toute** erreur en `ok` / « en attente de migration » — un repli écrit en juillet pour une migration posée depuis.
Même repli dans `check_worker_heartbeats` (l. 1518-1529), aujourd'hui sans effet (sa lecture est rapide).
Ex. du 22-23/10 : `cron.health` était en **warning** (1 tâche en anomalie), et le passage suivant, coupé, l'a remis **vert**.

**Pourquoi `app_cron_health` est lente :** elle relit `cron.job_run_details` **24 fois** (2 sous-requêtes × 12 tâches).
Cette table n'est **jamais purgée** (la doc Supabase le dit : *« not cleaned up automatically »*) : **1 226 263 lignes,
225 Mo**, depuis le 13/06, **+10 372 par jour**, et **aucun index sur `jobid`** — seulement la clé `runid`. **3,6 s au calme,
plus de 8 s sous charge, et ça s'aggrave chaque jour.** `postgres` peut y supprimer, pas y créer d'index (propriétaire
`supabase_admin`).

**⭐ Mesuré (lecture seule) :** la même réponse en remontant la clé `runid` à l'envers, tâche par tâche, dans une fenêtre
de N derniers passages → **3,4 ms au lieu de 3 585 ms**.

**Ce que l'aveuglement a caché :** sur les 14 derniers jours, les seuls échecs pg_cron sont ceux du **12/10 08:20-09:00**
(« job startup timeout » sur 8 tâches, incident Supabase). **Rien de grave n'est passé inaperçu — par chance.**

**Effet de bord d'un « illisible »** : il interrompt la règle d'e-mail (« passe AU rouge ») — une sentinelle rouge qui
devient illisible puis redevient rouge **renvoie un e-mail**. Sans effet aujourd'hui (celles qui sautent sont vertes).

### 4.2 Le « Résolu » qui ne tient pas — état au 26/10

- **Déjà audité le 14/10** (§11-13) : option **A** recommandée (« sourdine de 7 jours » via `snoozed_until`, + retirer le
  résumé de « Alertes à traiter »), **jamais tranchée**. `snoozed_until` est toujours vide partout.
- La vue `alerts_governed` : `lifecycle = clic si acted_at >= updated_at`. Le moniteur réécrit `updated_at` **à chaque
  passage** (`status_row()`, l. 1085) → un clic tient **au plus 2 h**.
- ⛔ **On ne peut PAS changer `updated_at` côté moniteur** : la purge des statuts obsolètes (`purge_stale_status`, l. 1195)
  s'en sert pour savoir qu'une clé n'est plus émise. Le correctif doit vivre **dans la vue**.
- **Un seul lecteur** : l'écran Santé (`loadAlertsCurrent`, filtre `alertsToTreat`). Ni fonction ni vue n'en dépend ;
  la descente l'exclut. **L'e-mail ne la lit pas** (il ne part que sur une bascule, §0 du 14/10).
- ⭐ **Le moniteur tient déjà le journal qu'il faut** : `app_monitor_event` reçoit une ligne **seulement quand une alerte
  change d'état** (l. 3576-3585 ; 15 en 24 h, 3 465 en 5 mois). « Aucun événement depuis le clic » = « l'alerte n'a pas
  bougé depuis que tu l'as vue ».
- Mesure sur tes anciens clics : « Notifications non lues » (03/09) n'a changé d'état que le **01/10** — elle aurait tenu
  28 jours ; avec un plafond de 7 jours, elle revient le 10/09.
- Simulation sur les 3 alertes d'aujourd'hui : **aucun ancien clic ne ferait taire une alerte actuelle** (règle actuelle
  et règle proposée donnent toutes deux « new »).
- Au passage : `acted_by` est **vide sur les 16 clics** (le front n'envoie pas l'auteur).

### 4.3 Les correctifs proposés — NON faits, il faut un « vas-y »

| # | quoi | où | ce que ça pourrait casser | retour |
|---|---|---|---|---|
| **A1** ⭐ | **la sonde pg_cron dit la vérité** : une erreur → `unknown` « illisible » (plus jamais `ok`) ; même chose pour `workers.heartbeat` | `check_gti_health.py`, 2 blocs | rien côté données ; l'écran montrera « illisible » au lieu d'un faux vert **tant que A2 n'est pas posé** (c'est voulu) | revenir au texte |
| **A2** ⭐ | **`app_cron_health` rapide** : même signature, mêmes colonnes ; lecture par `runid` à l'envers dans une fenêtre de **200 000 passages (~19 jours)** | base, 1 fonction (propriétaire et droits gardés : `postgres` + `service_role`) | une tâche **sans passage dans la fenêtre** rendrait `last_run` vide — et la sonde **ignore** aujourd'hui un `last_run` vide (l. 2134 : `age is not None`, trou déjà présent pour une tâche jamais lancée) → **A1 doit aussi dire : tâche active sans passage connu = anomalie** | patch inverse (empreinte) |
| A3 | **purger `cron.job_run_details`** au-delà de 30 jours (915 147 lignes) + une tâche quotidienne | base | ⚠ **perte d'historique** : on s'en est servi pour des audits (durées du ménage depuis le 11/10). 30 jours suffisent à ces audits. Recommandé par Supabase (et avant toute montée de version) | **irréversible** — sauvegarde datée d'abord, ou 90 jours |
| **B** | **le « Résolu » tient** : dans la vue seulement, pour les alertes du moniteur — le clic vaut **tant que l'alerte ne change pas d'état, et au plus 7 jours** ; les autres sources (notifications, relances, Pauline) gardent leur règle | base, 1 vue | une alerte qui **empire sans changer de couleur** (warning 5 → warning 50) reste muette jusqu'à 7 jours — l'e-mail est déjà dans ce cas aujourd'hui | patch inverse |
| C | une **2e lecture** (après 5 s) avant de déclarer une sentinelle « illisible » | `check_gti_health.py` | passage du moniteur plus long de ≤ 13 s quand ça arrive (≈ 4 % des passages) | revenir au texte |

**Recommandation : A1 + A2 ensemble** (la sonde est aveugle 4 fois sur 10 et le cache), puis **B**. A3 et C sont du
confort. Le reste de l'option A du 14/10 (retirer le résumé de « Alertes à traiter ») est **toujours ouvert**.

### 4.4 ✅ A1, A2 ET B POSÉS LE 26/10 (~07:45, « A1 a2 et b vas y », Frédéric)

**Contre-étude d'abord** (« refais une étude du projet pour être sûr ») — ce qu'elle a trouvé et changé :
- ⭐ **Le défaut avait une famille** (leçon 9) : le même repli « ok, en attente de migration » existait dans **3** sondes —
  `cron.health`, `workers.heartbeat` et **`data.contacts_satellites`** (non citée au §4.3). Les deux dernières n'ont
  **jamais** menti en 362 passages, mais portaient le même défaut, dormant. **A1 couvre les trois.**
- ⚠ Les deux vues sont en **`security_invoker`** : la vue lit `app_monitor_event` avec les droits de l'écran. Vérifié :
  même politique que `app_monitor_status` (admin/manager) — qui voit l'alerte voit son journal.
- ⚠ Le principe du patch du 05/07 (« jamais masquée à tort ») est **gardé** : une alerte qui repart est une transition,
  donc un événement, donc « new » — témoin 5 de la répétition.
- Fenêtre de A2 ramenée de 200 000 à **50 000 passages** (~4,8 jours) : pire cas mesuré 1,25 s → ~0,3 s par tâche
  morte ; une tâche quotidienne n'a jamais plus de ~10 000 passages de retard ; au-delà, A1 la fait sonner.
- `app_cron_health` n'a **qu'un appelant** (le moniteur) ; `alerts_governed` **qu'un lecteur** (l'écran Santé) ; ni
  vue ni fonction n'en dépend ; `CREATE OR REPLACE` garde propriétaire, droits et options (vérifié après pose).
- Les CHECK de `app_monitor_status` acceptent `unknown` (statut et sévérité) et les domaines utilisés.
- La 2e session avait modifié le moniteur ce matin (`a683709`, R4) : elle est dans ma copie, aucune collision.

| pièce | fichiers | épreuve | posé | preuve |
|---|---|---|---|---|
| **A1** | `monitoring/check_gti_health.py` (3 replis + « aucun passage connu ») | `monitoring/test_sonde_illisible_jamais_verte.py` **18/18**, et **8 rouges avec l'ancien code** (témoin inverse) ; les 4 autres épreuves du moniteur inchangées | actif au prochain passage (script sur le disque) | — |
| **A2** | `supabase/patch_cron_health_rapide_2026-10-26*.sql` | répétition : mêmes 12 tâches, **0 écart**, **3 967 ms → 6 ms** (10 396 ms à la 1re répétition), droits et `security definer` gardés, retour **exact** à `ac303763` | empreinte **`193cd0a3`** (= répétition) | **par l'API, la sonde A1 + A2 : 108 ms, « 12 jobs suivis, 0 en anomalie »** (lecture seule, rien écrit) |
| **B** | `supabase/patch_alerte_resolu_tient_2026-10-26*.sql` | répétition : **0 réponse changée sur 1 819 lignes** ; clic + repassage → ancienne règle `new` / nouvelle `resolved` ; transition après le clic → `new` ; clic de 8 jours → `new` ; vue lue en 2 ms ; retour **exact** à `13f1ee80` | empreinte **`0e06e8ae`** (= répétition) | à voir à l'écran au prochain clic « Résolu » |

⚠ **1re répétition de A2 « STOP » à tort** : 6 passages « connecting » étaient devenus « succeeded » pendant les 10 s de
l'ancienne lecture. Règle de comparaison corrigée (un passage *en cours* a le droit de finir), rejouée verte.

⚠ **Trouvé au passage, pas traité** : `monitoring/test_recherche_divergente_fraicheur.py` échoue (cas 8, « piège du
fuseau ») — **aussi avec l'ancien code**, donc pas lié ; probablement le passage à l'heure d'hiver (l'épreuve suppose
UTC+2). Et `cron.health:<tâche>` n'est pas dans les familles « retour à la normale » : une ligne de tâche résolue reste
jusqu'à la purge.

⏰ **À voir au passage de 08:48** : `cron.health` lu (plus jamais « en attente de migration ») ; et le rouge du balayage
photos tombera après **23:00**.

### 4.5 L'essai `test_recherche_divergente_fraicheur.py` qui échoue — analysé le 26/10 : **l'ESSAI se trompe, pas le moniteur**

Le cas 8 (« piège du fuseau ») compare une copie descendue le `2026-10-13T08:00:00` (heure **locale**, sans fuseau) à un
natif écrit le `2026-10-13T07:00:00+00:00`. Pour savoir ce qu'il attend, l'essai prend le décalage de la machine
**AUJOURD'HUI** (`datetime.now().astimezone().utcoffset()`, l. 211) — mais la date du scénario est le **13/10, en heure
d'été**.

| | le 13/10 (date du scénario) | lu par le moniteur | ce que l'essai croit |
|---|---|---|---|
| `08:00` locale | UTC+2 → **06:00 UTC** | 06:00 < 07:00 → copie **plus vieille** → `warning` ✅ juste | décalage d'aujourd'hui UTC+1 → 07:00 UTC = 07:00 → pas plus vieille → `critical` ❌ |

Mesuré : `parse_iso_locale_si_sans_fuseau('2026-10-13T08:00:00')` → **06:00 UTC** ; le même texte daté du 26/10 → 07:00 UTC.
Le moniteur applique **le décalage valable à la date lue** — c'est exactement ce qu'il doit faire. L'essai passait
jusqu'au 24/10 (même décalage UTC+2 ce jour-là et le 13/10) ; il échoue depuis le passage à l'heure d'hiver, et
repasserait seul fin mars.

**La sentinelle réelle n'est pas touchée** : `data.recherche_divergente` est `ok` (0) au passage de 06:49.

**Correctif de l'ESSAI seulement** (1 ligne, l. 211) : prendre le décalage **de la date du scénario** —
`datetime(2026, 10, 13, 8, 0).astimezone().utcoffset()` — au lieu de celui d'aujourd'hui. Non fait : il faut un « vas-y ».
