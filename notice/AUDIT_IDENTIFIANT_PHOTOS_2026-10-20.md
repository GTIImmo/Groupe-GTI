# Les photos ont-elles le même défaut que les documents ? — audit

*20/10/2026. **Lecture seule** : le code, la base Supabase (requêtes `SELECT` uniquement), les
journaux de travaux, et le miroir local `data/hektor.sqlite` ouvert en lecture seule.
Rien n'a été écrit, aucun run lancé, aucun service redémarré, **aucun appel vers Hektor**.*

**Audit limité aux PHOTOS d'annonce** (table `app_console_photo`). Les documents sont déjà
traités par `AUDIT_DOMAINE_DOCUMENTS_2026-10-20.md` ; les autres objets du tableau de
`CLAUDE.md §0` ne sont pas mesurés ici.

---

## ⭐ LA RÉPONSE : **NON**

> **Une photo n'a pas le défaut des documents.** Son numéro n'est **pas calculé sur une adresse** :
> c'est **le numéro que la base de Hektor donne elle-même à la photo**. L'adresse de la photo
> n'est qu'une information rangée à côté ; elle ne sert jamais à reconnaître la photo.

| | documents | photos |
|---|---|---|
| d'où vient le numéro | `sha1(adresse complète)` — **calculé par nous** | **numéro de la base Hektor** — *reçu, jamais calculé* |
| si le domaine change | le numéro change → double + suppression | **le numéro ne bouge pas** |
| lignes supprimées depuis le départ des compteurs | **15 404** | **2** *(dont l'essai du 14/10, journalisé)* |
| fichiers retéléchargés depuis le 11/09 | **17 118** *(chez Hektor, sous quota)* | **0** *(129 téléchargements, des photos NEUVES, sur le CDN public)* |
| même fichier présent sous deux numéros | **17 paires** sur la seule annonce 59578 | **0 sur 441 627 photos** |

⚠ **Une correction à ce qu'on t'a dit.** *« Il vient du CDN »* **n'est pas exact** : le numéro ne vient
**ni du CDN, ni de l'adresse**. Il vient de la **page Console** de Hektor (porte ①) ou du champ `id`
de l'**API** (porte ②). L'immunité est réelle, mais **pour une meilleure raison** que celle qu'on
t'avait donnée — et c'est justement ce qui rend la mesure nécessaire : une raison fausse aurait
pu cacher un défaut.

---

## 1. DANS LE CODE — où le numéro d'une photo est posé

**Trois portes écrivent dans `app_console_photo`. Aucune ne calcule de haché.**

| porte | fichier : ligne | **valeur exacte du numéro** | clé de reconnaissance |
|---|---|---|---|
| **① la page Console** (travail `sync_hektor_photos`) | `Console/console_job_worker.js:1292-1297` | l'attribut **`id="item_NNN"`** de la balise `<li class="classementPhoto">` de la page `mode=vignettes` / `vignettes_hidden` → `hektorPhotoId = match[1]` | `:4730` pose `hektor_photo_id`, `:4758` `on_conflict=hektor_annonce_id,hektor_photo_id` |
| **② l'API via le miroir local** (étape nocturne du run) | `Console/rattrapage_photos.js:159-168` | le champ **`id`** de chaque entrée de `hektor_annonce_detail.images_json` → `pid = String(e.id)` | `:284` pose `hektor_photo_id`, `:303` même `on_conflict` |
| **③ une photo envoyée depuis l'app** | `Console/console_job_worker.js:8764-8767` puis `:8827-8844` | la ligne naît **sans** numéro (`hektor_photo_id` vide), puis reçoit **le numéro que la galerie Hektor lui donne** (différence galerie avant / après l'envoi) | `:8844` l'upsert « la reconnaît au lieu d'en créer une seconde » |

**Preuves qu'aucun numéro de photo n'est calculé** :
- `grep sha1` dans le worker : **3 usages dans le code** — `:928` (la fonction), `:1075` (**les documents**), `:1232` (l'empreinte documentaire) — plus un commentaire (`:4915`). **Aucun dans le chemin des photos.**
- `rattrapage_photos.js`, `accorder_photos_miroir.js` : **0 `sha1` / `md5`.**

**Ce que ce numéro est, mesuré dans la base** *(`SELECT count(*), …  FROM app_console_photo`)* :

```
441 627 photos · 441 627 numéros DISTINCTS (même entre annonces) · 0 non numérique
plus petit 22 · plus grand 488 280 · croissant avec la date (478 030 le 29/05 → 488 269 le 20/10)
```

➡ C'est le **compteur de la base de Hektor** (un haché d'adresse ferait 40 caractères
hexadécimaux, et ne croîtrait pas avec le temps).

**Où l'adresse sert — et elle ne sert JAMAIS de clé** *(recherche de `url_hd` / `url_preview` dans
tout le dépôt)* :
1. **écrite** : `console_job_worker.js:4732-4733`, `rattrapage_photos.js:286-287` ;
2. **lue comme source de téléchargement** : `console_job_worker.js:5433` (`sourceUrl`) ;
3. **affichée** : `apps/hektor-v1/src/lib/api.ts:8019-8022` *(nos adresses d'abord, celles de
   Hektor en repli)* et `App.tsx`.
Jamais comparée, jamais hachée, jamais dans un `on_conflict`.

**Les deux autres choses qui portent la photo ne dépendent pas non plus d'une adresse** :
- le **fichier sur le serveur** : `localPhotoDir` (`:861-866`) range sous l'`id` **uuid de la ligne**
  *(et `metadata_json.local_archive_path` le fige au premier téléchargement, `:5440`)* ;
- l'**adresse publique des dérivés** : `cheminDerivePhoto` (`:6320-6322`) =
  `{app_dossier_id}/{uuid}/{nom}.jpg`, *« elle ne porte AUCUN numéro Hektor »* (commentaire
  `:6315-6319`).

**`phase2/`** ne pose aucun numéro de photo : `pull_from_supabase.py` ne fait que **recopier** la
table vers le miroir local (par date de modification, `:450`).

**Clé d'unicité en base** *(`pg_indexes`)* : `UNIQUE (hektor_annonce_id, hektor_photo_id)` ;
la ligne a son propre `id` uuid, jamais recalculé.

⚠ **Le domaine de la page** : `Console/.env:72` donne `HEKTOR_BASE_URL=https://www.gti-immobilier.fr`
(le **nouveau**) ; le worker charge ce fichier **en premier** (`console_job_worker.js:10`, et
`dotenv` n'écrase pas). Donc les pages d'où vient la porte ① sont lues **sur le nouveau domaine**.
*(Le `.env` de la racine, lui, porte encore l'ancien — voir §9.)*

---

## 2. DANS LA BASE — l'adresse des photos, sur quel domaine ?

```sql
select substring(coalesce(url_hd,url_preview) from '^https?://([^/]+)') as hote,
       present_in_hektor, count(*) n, count(distinct hektor_annonce_id) annonces
  from app_console_photo group by 1,2;
```

| hôte de l'adresse | présente chez Hektor | photos | annonces |
|---|---|---:|---:|
| `groupe-gti-immobilier.staticlbi.com` | oui | **441 256** | 49 198 |
| `groupe-gti-immobilier.staticlbi.com` | non *(retirée)* | **371** | 60 |
| `groupe-gti-immobilier.la-boite-immo.com` *(ANCIEN portail)* | — | **0** | 0 |
| `www.gti-immobilier.fr` *(NOUVEAU portail)* | — | **0** | 0 |

➡ **Aucune photo n'a jamais porté le domaine du portail.** Les 441 627 portent **un seul hôte : le
CDN `staticlbi.com`**. Même chose dans `metadata_json.source_url` : 441 622 sur le CDN, 5 vides
*(0 sur un portail)*.

**Et le CDN, lui, n'a pas bougé avec le portail** — c'est la mesure qui compte :

| | photos | adresse sur le CDN `staticlbi` | adresse sur un portail |
|---|---:|---:|---:|
| créées **avant** le 11/09, **non relues** depuis | 1 357 *(225 annonces)* | 1 357 | 0 |
| créées avant le 11/09, **relues après** | 40 *(4 annonces)* | 40 | 0 |
| créées **après** le 11/09 *(donc lues après le déménagement)* | 440 230 *(48 970 annonces)* | 440 230 | 0 |

➡ Avant comme après le 11/09, **même hôte CDN**. Le déménagement du portail ne l'a pas touché.

---

## 3. ⭐ LA PREUVE DÉCISIVE — trois preuves indépendantes

### 3A. Le même chemin sous deux numéros : **aucun**

La question posée : *« une même annonce + un même chemin sous les deux domaines »*. Comme aucune photo
n'a l'ancien ni le nouveau domaine (§2), la question se pose en sa **forme générale** : **un même
fichier (même annonce, même chemin) porté par DEUX numéros ?** — c'est la signature exacte du défaut.

```sql
select count(*) groupes
  from (select hektor_annonce_id, regexp_replace(url_hd,'^https?://[^/]+','') chemin
          from app_console_photo
         group by 1,2 having count(distinct hektor_photo_id) > 1) g;
-- résultat : 0 groupe  (sur 441 627 lignes)
```

⭐ **Le témoin positif** *(sans lui, un zéro ne prouve rien — leçon du 12/10)* : **la même forme de
requête sur les documents de l'annonce 59578** — là où on sait que le défaut existe :

```sql
-- même requête, sur app_console_document, adresse = metadata_json->>'console_url', annonce 59578
-- résultat : 17 groupes · 34 lignes · hôtes vus : groupe-gti-immobilier.la-boite-immo.com ET www.gti-immobilier.fr
```

➡ L'instrument **voit** le défaut quand il existe (17 contre 17 de la note du matin) ; il en voit
**0** sur les photos.

### 3B. Des photos AVANT / APRÈS le déménagement : **le numéro n'a pas bougé**

**Quatre annonces ont des photos créées avant le 11/09 ET relues après** *(40 photos — une ligne par
annonce, nommée)* :

| annonce | photos | créées le | dernière relecture | relue par | numéros | résultat |
|---|---:|---|---|---|---|---|
| **24113** | 30 | 22/05 | 19/10 22:15 | travail `sync_hektor_photos` *(page Console)* | 115 564 … 479 892 | **30 lues · 0 téléchargée · 30 inchangées · 0 échec** |
| **62774** | 2 *(+2 plus récentes)* | 23/07 | 19/10 22:16 | idem *(2 travaux ce jour-là)* | 482 253 – 482 254 | **4 lues · 0 téléchargée · 4 inchangées** |
| **62853** | 4 | 05/08 | 19/10 22:16 | idem | 482 916 – 482 919 | **4 lues · 0 téléchargée · 4 inchangées** |
| **24935** | 4 | 30/06 | 26/09 01:50 | rattrapage nocturne *(API, porte ②)* | 125 159 – 480 827 | reconnues : aucune ligne en plus |

*(requêtes : `app_console_photo` filtré `created_at < '2026-09-11' and synced_at >= '2026-09-11'`,
puis `app_console_job` pour les trois annonces lues par la page.)*

➡ **36 photos créées avant le déménagement (30 de 24113 + 2 de 62774 + 4 de 62853) ont été relues par
la page Console APRÈS lui : toutes reconnues**, aucune téléchargée de nouveau, aucune ligne en double
*(pour 62774 la page a lu 4 photos, dont 2 seulement datent d'avant le 11/09)*. Les 4 de 24935 ont été
reconnues par l'API. Total d'avant le 11/09 relu après : **30 + 2 + 4 + 4 = 40**. Chez les documents la
même situation donnait *« créer un double, supprimer l'ancienne »*.

### 3C. Les deux portes donnent LE MÊME numéro : **4 276 photos le prouvent**

Les deux portes (page / API) pourraient donner deux numéros différents pour la même photo — c'est
exactement ce qui créerait des doublons. **Mesure** : des photos créées par la porte ② (API, source
`miroir_local`, **le 25/09**) ont ensuite été **relues par la porte ① (page)**, qui a **repris la même
ligne** (la source est passée à `hektor_console`, la date de création est restée celle du 25/09) :

```sql
select count(*), count(distinct hektor_annonce_id) from app_console_photo
 where source='hektor_console' and created_at >= '2026-09-25' and created_at < '2026-09-26';
-- 4 276 photos · 614 annonces · relues entre le 19/10 09:48 et le 20/10 03:27 · toutes sur le CDN
```

Exemples nommés *(les 5 plus récentes)* : annonce **12616** photo **71207** · **12615** / **71205** ·
**12612** / **71206** · **12611** / **71204** · **12610** / **71202** — créées le 25/09 21:08:48,
relues par la page le 20/10 entre 03:26 et 03:27.

Preuve dans l'autre sens : **229 annonces** ont des photos créées par la page **avant** le 25/09. Le
rattrapage API de la nuit du 25/09 n'a créé **aucune ligne** sur elles (**0**). Et le miroir local, lu
**en lecture seule**, donne pour **227 de ces 229 annonces exactement le même nombre de photos
visibles que notre base** (0 différence). *Les 2 autres — **62354** et **62356** — ne sont pas dans le
miroir du tout* (ce sont aussi les deux seules photos « en attente », voir §9).

**Limite** : cette égalité des deux portes est **prouvée sur 4 276 + 227 annonces**, pas sur les 435 804
photos que la porte ② est la seule à avoir vues. Voir §7.

### 3D. Trois photos « retirées » ont un jumeau de même contenu — et ce n'est pas le défaut

Sur les 371 photos retirées, **3** ont une photo **présente** de **même contenu** (même `sha256`) dans
la **même annonce**, mais **pas le même nom de fichier** *(0 nom en commun sur les 371)* :

| annonce | photo retirée | jumelle présente | note |
|---|---|---|---|
| **47132** | 486 084 | 486 982 | jumelle plus **récente** |
| **47132** | 486 100 | 486 081 | jumelle plus **ancienne** |
| **47132** | 486 106 | 486 617 | jumelle plus **récente** |

Hektor donne un **numéro neuf et un nom de fichier neuf à chaque envoi** : c'est quelqu'un qui a
renvoyé la même image (ou retiré un doublon) **côté Hektor**. Ce n'est pas un déménagement d'adresse
— les numéros n'ont pas changé *pour la même photo*, il y a deux photos. *(Distinguer « renvoi
volontaire » de « doublon retiré » demanderait d'interroger Hektor : non mesuré.)*

---

## 4. L'ÉQUIVALENT DE `pruneDeletedDocuments` pour les photos

**Il y en a deux, et aucun ne supprime une ligne.** Les deux **marquent** `present_in_hektor = false` ;
la ligne, le fichier et l'adresse publique **restent** (règle « delete-never », 26/09).

| | **documents** (`pruneDeletedDocuments`, *avant le correctif c82d973*) | **photos — le travail** (`upsertConsolePhotos`) | **photos — le passage nocturne** (`accorder_photos_miroir.js`) |
|---|---|---|---|
| geste | **SUPPRIME** la fiche | **marque** « plus chez Hektor » (`console_job_worker.js:4798-4808`) | **marque** (`accorder_photos_miroir.js:379-382`) |
| retour possible | non | **oui** : une photo qui revient est remise `present_in_hektor=true, absent_depuis=null` (`:4743-4744`) | oui, même mécanisme |
| garde-fou « liste vide » | oui — *le seul* | oui : `:4752-4756` (rien lu → rien touché) **et** `:4793-4797` (liste vide alors que nous avons des photos → on ne marque rien) | oui, verrou 3 (`:268-273`) |
| **garde-fou de MASSE** | **aucun** *(c'est le défaut)* | **aucun** ⚠ | **oui** : plafond 2 000 photos (`:321-329`), plancher 5 000 annonces lues (`:226-235`), lecture fraîche < 48 h (`:254`), photos de l'app intouchables (`:260`), « masquée ≠ supprimée » ×2 (`:290`, `:376-378`) |
| clé de reconnaissance | `sha1(adresse)` ⛔ | numéro Hektor ✅ | numéro Hektor ✅ |

**Qui a marqué les 371 photos retirées aujourd'hui ?** *(déduit des heures, pas lu dans un journal)* :
une seule fournée par nuit, à 21:17–21:23 — c'est le passage nocturne (ligne 4/4 de « GTI Entretien
Documents »), pas le travail :

| marquées le | photos | annonces |
|---|---:|---:|
| 15/10 21:23 | 337 | 53 |
| 16/10 21:20 | 20 | 4 |
| 17/10 21:17 | 12 | 4 |
| 18/10 21:17 | 2 | 1 |

*(la liste nommée des 60 annonces est en annexe A ; la somme des annonces dépasse 60 parce que certaines
reviennent d'une nuit à l'autre).* Le commentaire du script `:281-284` dit que les
337 du 15/10 étaient *« vraiment »* disparues *(reportages remplacés, vérifié en direct le 18/10 sur
13/13, 25/25, 25/25)* et que **103** autres, **masquées**, avaient été déclarées disparues à tort puis
réparées (`patch_reparer_103_masquees_2026-10-19.sql`). **Je n'ai pas re-vérifié ces 337 chez Hektor**
(interdit ici) : je les cite.

**Le seul endroit qui SUPPRIME une ligne de photo** : `console_job_worker.js:9656`, dans
`handleDeleteHektorPhoto`, **après** que Hektor a confirmé la suppression, sur demande explicite. Journal
`app_console_deleted_photo_log` : **1 ligne** — annonce 62774, photo 487 926, essai du 14/10.

---

## 5. LE COMPTEUR — des photos supprimées puis recréées depuis le 11/09 ? **NON**

### 5A. Les compteurs de la base

```sql
select n_tup_ins, n_tup_upd, n_tup_del from pg_stat_user_tables where relname='app_console_photo';
-- photos    : 440 232 insérées · 928 501 modifiées · 2 SUPPRIMÉES
-- documents : 163 519 insérées · 180 326 modifiées · 15 404 SUPPRIMÉES   (la même requête)
```

⭐ **Les compteurs bouclent à l'unité** *(ce qui prouve qu'ils couvrent toute la période utile)* :

```
1 397 lignes d'avant le 25/09  +  440 232 insérées  −  2 supprimées  =  441 627  = le nombre de lignes d'aujourd'hui
```

⚠ Je ne connais pas la date de remise à zéro des compteurs ; c'est l'égalité ci-dessus, et non une
date, qui justifie de les croire.

### 5B. Le recensement par date de création

Rien n'est créé entre le **17/08** (1 355 lignes) et le **25/09 21:05**. **Les 1 397 photos d'avant le
déménagement existent toutes encore, toutes `present_in_hektor = true`.** Aucune n'a été supprimée puis
recréée (une recréation aurait une date de création récente).

La grande date, **25/09 : 435 126 lignes créées en 3 minutes** (21:05:48 → 21:08:52, 48 235 annonces) :
c'est la **première population** de la table par `rattrapage_photos.js` *(la table n'avait que 1 397
lignes)* — **pas** un cycle supprimer / recréer. Elle a eu lieu **après** le déménagement.

### 5C. Les journaux de travaux (`app_console_job`, `sync_hektor_photos`)

| jour | travaux | annonces | photos lues | **téléchargées** | inchangées | échecs |
|---|---:|---:|---:|---:|---:|---:|
| 05/08 | 1 | 1 | 4 | — | — | — |
| 17/08 | 305 | 300 | 1 430 | 1 355 | 75 | 0 |
| *(11/09 → 26/09)* | **0** | | | | | |
| 27/09 | 1 | 1 | 1 | 1 | 0 | 0 |
| 19/10 | 1 003 *(+1 en erreur)* | 1 002 | 4 446 | **127** | **4 319** | 0 |
| 20/10 | 1 | 1 | 19 | 1 | 18 | 0 |

**Les 129 téléchargements depuis le 11/09 sont des photos NEUVES, pas des retéléchargements** : 12
travaux — **11843 (28)**, **11847 (27)**, **11828 (19)**, **63073 (14)**, **11832 (14)**, **11857 (11)**,
**11854 (4)**, **12104 (4)**, **62189 (3)**, **11695 (3)**, **63289 (1, le 20/10)**, **63157 (1, le 27/09)**
= **129**. Pour les 11 premiers, le nombre téléchargé est **égal** au nombre de lignes **créées** sur
l'annonce depuis le 19/10 *(des photos masquées que seule la page Console voit — passage du balayage du
19/10)*. Le 12ᵉ, **63157**, n'a qu'**une** photo (n° 486 316), **créée le 27/09 à 05:05 par ce même
travail**. **4 319 sur 4 446 lues le 19/10 ont été reconnues « inchangées »** — la signature inverse de
celle des documents.

*(Les photos viennent du CDN public, **hors quota Hektor** — mesuré à 0 refus sur 435 000
téléchargements, `AUDIT_ETAPE_PHOTOS_DANS_LE_RUN_2026-09-26.md §3`. Même un retéléchargement massif n'aurait
donc pas eu le coût qu'ont eu les 17 118 des documents.)*

⚠ **Une seule erreur depuis le 11/09** : annonce **63073**, 19/10 15:10, *« Job interrompu
automatiquement : exécution running trop ancienne (> 30 minutes) »*. Sans rapport avec l'identifiant.
*(Les erreurs de travaux ont été purgées le 15/10 ; pour `sync_hektor_photos` l'archive ne contient que
3 échecs du 03/06, « fetch failed » — rien depuis le 11/09.)*

---

## 6. TABLEAU OBJETS × GESTES — pour la photo *(CLAUDE.md §0)*

| geste | par quelle porte | **clé de reconnaissance** | l'adresse sert de clé ? | état de la mesure |
|---|---|---|---|---|
| **créer** | ① page Console `:4758` · ② rattrapage API `rattrapage_photos.js:303` · ③ envoi depuis l'app `:8827-8844` | numéro Hektor (+ l'annonce) | **non** | ✅ code lu + base mesurée |
| **modifier — visibilité** | `set_hektor_photo_visibility`, `:9148-9210` | `payload.hektor_photo_id` | **non** | ⚠ trouvé par mots-clés, handler non relu ligne à ligne |
| **modifier — ordre / couverture** | `reorder_hektor_photos`, `:9384-9490` | `hektor_photo_id` | **non** | ⚠ idem |
| **modifier — légende** | aucun geste (`sync_hektor_photos` la lit seulement) | — | — | non mesuré : je n'ai pas cherché de geste caché |
| **supprimer — une photo** | `delete_hektor_photo`, `:9540-9660` | `photo.id` → `hektor_photo_id` | **non** | ✅ lu ; 1 essai réel (14/10) |
| **supprimer — retirée chez Hektor** | marquage : travail `:4798-4808` · passage nocturne `accorder_photos_miroir.js:379` | numéro Hektor | **non** | ✅ §4 |
| **lire / remonter** | page `fetchConsolePhotoEntries` `:4698-4723` · miroir `rattrapage_photos.js:142-180` · front `api.ts:8031` | numéro Hektor | **non** | ✅ |

**Les autres objets** *(annonce, contact, recherche, relation, transaction, mandat, document, RDV)* :
**non mesurés dans cet audit.**

---

## 7. ⛔ CE QUE JE N'AI PAS PU MESURER — et je ne le suppose pas

1. **L'égalité « numéro de la page = numéro de l'API » sur les 435 804 photos que la seule porte ②
   (API) a vues** *(430 850 créées le 25/09 + 4 954 créées depuis, jamais relues par la page ; ce total
   compte les 371 retirées)*. Elle est **prouvée sur 4 276 photos** (3C) et sur 227 annonces. Si elle était fausse,
   la **conséquence** serait des doubles à la première lecture par la page (pas une perte d'identité) —
   mais je n'ai **pas** de preuve directe pour ces 435 804.
2. **Les 1 357 photos d'avant le 11/09 jamais relues depuis** (225 annonces) : aucun « après » côté
   page. Elles sont `present_in_hektor = true`, et la comparaison miroir/base ci-dessus couvre 227 de
   ces annonces, mais je n'ai pas de relecture par la page.
3. **Si le CDN `staticlbi` déménage un jour.** Je n'ai aucune mesure là-dessus (il n'a pas bougé avec le
   portail). Voir §8.
4. **Les 337 photos du 15/10 « vraiment remplacées »** : je cite le commentaire du script, je ne les ai
   pas re-vérifiées chez Hektor (appel interdit).
5. **Les handlers de visibilité et d'ordre** : trouvés par recherche de mots, pas relus ligne à ligne.
6. **Le deuxième des 2 enregistrements supprimés** (`n_tup_del = 2`) : le journal n'en a qu'un
   (62774 / 487 926). Le second n'est pas identifié.
7. **Les journaux de travaux d'avant le 15/10 pour les erreurs** : purgés ; l'archive est un résumé.
8. **Le moment exact où les compteurs de la base ont été remis à zéro** : inconnu (voir 5A).
9. **Les autres objets** (§6).

---

## 8. CE QUI RESTE FRAGILE — *ce n'est pas le même défaut*, et rien n'est urgent

*Je ne code rien. Ces trois points sont des décisions, donc les tiennes.*

1. **Le marquage du travail n'a aucun garde-fou de masse** (§4). Si la page Console de Hektor renvoyait
   un jour une liste **tronquée mais non vide** (3 photos sur 40), `upsertConsolePhotos` marquerait les
   37 autres « retirées ». Conséquence : elles **disparaissent de l'écran** *(le front filtre
   `present_in_hektor`)* — **mais** rien n'est supprimé, ni le fichier, ni l'adresse publique, et la
   prochaine lecture complète les remet. **Jamais observé** : d'après les heures de marquage, aucune des 371
   ne vient du travail (§4). Le passage nocturne, lui, a plafond et plancher. *Option, si tu veux : y mettre le même
   plafond.*
2. **Si le CDN `staticlbi` changeait d'adresse.** Le **numéro** ne bougerait pas (preuve ci-dessus), mais
   **327 273 photos présentes (327 170 visibles) n'ont pas encore leurs adresses à nous** et
   s'affichent donc avec l'adresse Hektor (`api.ts:8019-8022`) ; `rattrapage_photos.js` ne **réécrit
   pas** l'adresse d'une ligne qui existe déjà. Les fichiers, eux, sont chez nous
   (**441 493 `local_only` + 132 `cloud_available`**). C'est un **raisonnement**, pas une mesure : je n'ai
   aucune observation d'un déménagement du CDN.
3. **Une photo, deux portes** (§7.1) : à confirmer sur un échantillon de la porte ② le jour où la page
   relira de nouvelles annonces (le balayage du 19/10 l'a fait pour 614 annonces, sans écart).

**Recommandation : AUCUN correctif sur l'identifiant des photos.** Il n'y a rien à corriger. Le défaut
des documents ne se rejoue pas ici. *(Aucun code n'est modifié par cet audit, donc la rubrique
« ce que ça pourrait casser ailleurs » est sans objet.)*

---

## 9. HORS SUJET — noté, pas traité

- **Deux `.env` se contredisent sur le domaine** : `C:\Hektor\Projet\.env` donne encore
  `HEKTOR_BASE_URL=https://groupe-gti-immobilier.la-boite-immo.com` (l'ancien), `Console/.env:72` le
  nouveau. Le worker lit `Console/.env` en premier, donc il est sur le nouveau ; tout autre programme qui
  ne lirait que la racine reste sur l'ancien. À vérifier, sans rapport avec les photos.
- **Deux photos « en attente » depuis le 29-30/05** sans fichier chez nous : annonce **62354** photo
  **478 030** et annonce **62356** photo **478 062** *(source `hektor_console`)*. Ce sont aussi les deux
  annonces absentes du miroir.
- **Ma mémoire disait faux** : *« les photos ont un identifiant qui vient d'une adresse — celle du CDN »*
  (`identifiant-calcule-sur-une-valeur-qui-bouge`). Corrigée.

---

## Annexe A — les 60 annonces qui ont des photos retirées *(371 photos, une ligne par annonce)*

Format : `annonce (photos retirées)`. Toutes marquées le **15/10 21:23** sauf mention.

**47132 (55)** · **63156 (32)** · **63081 (26)** · **63066 (25 — du 15/10 au 17/10)** · **63214 (14)** ·
**61541 (12 — 16/10)** · **61676 (12)** · **62316 (12)** · **63041 (12)** · **63088 (12)** · **61656 (10)** ·
**61680 (9)** · **62349 (9)** · **62495 (8)** · **63193 (8 — du 16/10 au 18/10)** · **30414 (7)** ·
**58903 (7)** · **62858 (7)** · **63244 (7)** · **61904 (6)** · **58902 (5)** · **63167 (5)** ·
**63248 (5 — 17/10)** · **62599 (4)** · **63240 (4)** · **2004 (3)** · **58948 (3)** · **62806 (3)** ·
**62820 (3)** · **62840 (3)** · **63200 (3)** · **63222 (3)** · **17516 (2)** · **20873 (2)** · **26299 (2)** ·
**28483 (2 — 17/10)** · **62847 (2)** · **62934 (2)** · **63114 (2)** · **63149 (2)** · **63197 (2)** ·
**14446 (1 — 16/10)** · **18680 (1)** · **59277 (1)** · **59653 (1)** · **62115 (1)** · **62486 (1)** ·
**62543 (1)** · **62972 (1)** · **62991 (1)** · **63011 (1)** · **63036 (1)** · **63064 (1)** ·
**63065 (1)** · **63108 (1 — 16/10)** · **63145 (1)** · **63168 (1)** · **63234 (1)** ·
**63296 (1 — 17/10)** · **8419 (1)**.

*(total : 371, contrôlé par somme.)*

## Annexe B — comment relire ces mesures

Toutes les requêtes sont des `SELECT` sur `app_console_photo`, `app_console_job`,
`app_console_deleted_photo_log`, `pg_stat_user_tables` et `pg_indexes` ; la seule lecture hors Supabase
est celle du miroir `data/hektor.sqlite` en **lecture seule** (`mode=ro`, `PRAGMA query_only`), par un
script jetable laissé hors du dépôt. Les formes à rejouer :

```sql
-- 3A  le même fichier sous deux numéros (doit rendre 0 ; témoin : même forme sur app_console_document, annonce 59578 -> 17)
-- 5A  les compteurs : select n_tup_ins, n_tup_upd, n_tup_del from pg_stat_user_tables where relname in ('app_console_photo','app_console_document');
-- 5C  select date_trunc('day',requested_at), status, count(*), sum((result_json->>'photos_downloaded')::int)
--       from app_console_job where job_type='sync_hektor_photos' group by 1,2;
```
