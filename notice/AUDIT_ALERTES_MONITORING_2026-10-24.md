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

**6. Le remède proposé (NON fait — c'est du code du run, il faut un « vas-y »).** Un garde-fou **sans aucune
requête de plus chez Hektor** (donc sans risque de blocage d'IP) : **ne rien retirer du miroir pour un type
quand le nombre de distincts reçus est inférieur au total annoncé par Hektor** (`metadata.total`). Cette nuit,
il aurait refusé 2 suppressions (compromis, ventes), et les 11 seraient restées présentes. Les vraies
suppressions passeraient la nuit suivante, quand la liste serait complète. À écrire dans
`aligner_miroir_sur_hektor` (`normalize_source.py` ~l. 1394), à côté du garde-fou « liste tronquée < 50 % ».

## 3. Ce qu'on peut retirer tout de suite, sans toucher à aucun garde-fou

- **n° 4 et n° 5** : trancher les 6 lignes dans l'écran Santé. Elles sortent du compte, la sonde reste.
- **n° 6** : rien à faire, elle s'éteint d'elle-même le 25/10.
- **n° 1, 2 (rouge), 3, 10** : s'éteignent si la nuit prochaine passe.

**Ce qui demande une décision :** la vue (§0), les 5 workers « sans premier signe » (n° 2), la vérification
des transactions (n° 7), et l'étape de ménage (§2).
