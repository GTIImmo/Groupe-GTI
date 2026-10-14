# CHANTIER ⑥ — CE QUI NE REDESCEND PAS DE HEKTOR

*Ouvert le 14/10/2026. Sources : plan l. 288 (suivi du chantier), audit par objet du 08/10 §6
(l. 179-197) et §3 (Documents l. 310, Photos l. 323, RDV l. 336, Recherches l. 271), liste
`D.0` (l. 970) et section **10bis** (l. 1170). Méthode : `notice/PROMPT_CHANTIER_ETAPE2.md`.*

---

## LES POINTS DU CHANTIER — état au 14/10/2026

| # | point | d'où il vient | état |
|---|---|---|---|
| **6a** | **G.1-b** — les **527 brouillons** feront **tous** échouer le rattrapage des documents, et seront **exclus pour toujours** | liste 10bis l. 1224 · péremption CLAUDE.md l. 533 | 🔎 **audit approfondi le 14/10 : CONFIRMÉ, mais le correctif n'est PAS celui qui était écrit** — ⏰ nuit du 16 au 17/10 |
| **6a-bis** | **le 4ᵉ index dans les 3 fonctions de droits** *(ajouté le 14/10 sur décision de Frédéric : « A, on le traite »)* | trouvé par l'audit de 6a | ✅ **FINI le 14/10 — SANS AUCUN PATCH** : rien à ouvrir *(le panneau photos n'est pas affiché sur une fiche légère, la RLS n'est jamais testée)*, et l'ouvrir aurait **ouvert 10 gestes d'écriture** |
| **6b** | **G.2** — le **parc vivant** n'est plus relu depuis le 20/08 : `--detect` n'est jamais appelé par le run | liste 10bis l. 1235 · audit §6 | 🔎 **audit en cours** |
| **6c** | **G.6** — allumer `-EnqueueConsoleDocuments` (⛔ après le rattrapage **et** après 6b) | liste 10bis l. 1302 | ⬜ *(geste de Frédéric)* |
| **6d** | **photos** — les ajouts remontent, **ni les retraits ni l'ordre** | audit §6 · §3 Photos C5 | ⬜ |
| **6e** | **agenda des visites Hektor** — importé nulle part (~115 bons/mois) | audit §6 · §3 RDV C5 | ⬜ **question de fait à Frédéric** |
| **6f** | **recherche créée dans Hektor** — le carnet « devenu acquéreur » est aveugle | audit §6 · §3 Recherche C5 | ⬜ |
| **6g** | **2 recherches archivées disparues du cloud** (74680, 76218), 7 lignes accrochées | audit §6 · §3 Recherche C6/C7 | ⬜ |
| **6h** | **RDV déplacé directement dans Google** — ne revient pas chez nous | audit §6 · §3 RDV C2 | ⬜ |
| **6i** | **piste reçue du chantier ③** — les **fiches détail des biens clos** ne seraient plus rafraîchies (49624 : `hektor_mandat` dit 13/10, le détail dit 19/08) | `CHANTIER_3_HEKTOR_DABORD_2026-10-12.md` l. 3944 | ⬜ à mesurer ici |

**Ordre retenu : 6a d'abord** (seul point avec une date de péremption).

**⚠ Hors périmètre écrit, même famille — à trancher par Frédéric** : `G.1-c` (111 annonces lues
vivantes en août puis vendues : leurs pièces de fin de vie ne seront jamais relues, l'empreinte
est déjà posée) et `G.1-d` (230 documents indexés **sans fichier**, seul Hektor les a).

---

# 6a — G.1-b : LES 527 BROUILLONS

> **Frédéric, 14/10** : *« les brouillons sont des cas à part, il faut reprendre mon projet et les
> codes pour bien comprendre… on n'arrive pas à les modifier, il faut que tu comprennes avant
> d'y toucher. »* ➡ Audit **repris à zéro**. Ce qui suit remplace ma première lecture, qui
> traitait un brouillon comme une annonce ordinaire mal indexée. **C'est faux : c'est un monde
> à part, et la correction écrite dans la liste (« ajouter le 4ᵉ index à `loadDossier` ») n'est
> pas suffisante en soi.**

## ÉTAPE 1 — L'AUDIT (14/10/2026, lecture seule, aucun appel à Hektor)

### A. CE QU'EST UN BROUILLON — et pourquoi il n'entre pas par la même porte

| | |
|---|---|
| **marqueur** | `isDraft: true`, exposé **uniquement** par la **GraphQL de la Console** (`PropertyListing`). **L'API REST ne le dit pas** — `AnnonceById` / `ListAnnonces` sont aveugles *(note du 22/06 §1, confirmée en direct : 7 candidats Tence tous `isDraft=true`, 2 témoins à `false`)* |
| **statut trompeur** | un brouillon **porte quand même un statut** : « Actif » 234, « Estimation » 225, **vide** 68 *(mesuré le 14/10)*. Donc ni le statut ni `valide` ne le distinguent — c'est pour ça que ~189 brouillons s'affichaient « Actif » à tort avant juin |
| **sa porte d'entrée** | **une chaîne dédiée**, séparée du run REST : `phase2/sync/sync_hektor_drafts.py` (balayage GraphQL, **lecture seule**) → table locale `hektor_annonce_draft_state` → `build_brouillon_annonce_index` (`export_app_payload.py`) → `app_brouillon_annonce_index_current` |
| **et elle tourne** | dernier balayage **14/10 04:24**, dernier balayage complet le 09/10 *(table `hektor_draft_sweep_meta`)*. Local : **527** `is_draft=1`, **73** déjà démis (brouillons finalisés). Supabase : **527**. Les deux comptes coïncident |
| **l'interrupteur** | `APP_BROUILLON_BUCKET_ENABLED = "1"`, posé par le run (`run_full_pipeline.ps1:353`) |
| **sortis du parc vivant EXPRÈS** | activation du 22/06 (`dcf1128`) : **301** brouillons retirés de `app_dossier_current` (13 391 → 13 090), chevauchement actif ∩ brouillon = **0**. Mesure du 14/10 : toujours **0** |

### B. POURQUOI « ON N'ARRIVE PAS À LES MODIFIER » — c'est une DÉCISION, pas une panne

1. **Le front les met en lecture seule, exprès.** `App.tsx:411` — `isReadOnlyLightweightDetail`
   rend **vrai** dès que `is_brouillon === true`. La fiche est une **fiche légère**, et le bouton
   ne propose pas de modifier mais **« Reprendre la saisie »**, qui **ouvre Hektor**
   (`openHektorAnnonce`, l. 23528). Décision du 23/06, lot 4.3 (`7ea8a02`).
2. **Dans Hektor, un brouillon vit dans le WIZARD de création**, pas dans la fiche normale
   (`Console/RAPPORT_TECHNIQUE_CONSOLE_HEKTOR.md` §4.1 et §5.3 : `chargeWizardAjouteBien`,
   `mode=ajoutebien_wizardBien`, `saveWizardLiteAnnonce`).
3. **Et la pièce qui manque pour le FINALISER n'a jamais été éprouvée** *(note du 22/06 §7)* :
   le **prix** est refusé hors du workflow mandat, et `link_hektor_mandant` n'a **jamais tourné
   en production**. Or sans mandat ni prix, un brouillon ne devient pas une annonce.
4. **Mesure qui le confirme** : dans **toute** l'histoire de `app_console_job`, les seuls travaux
   jamais exécutés sur un brouillon sont **8 `refresh_console_data`, tous réussis** (22/06 →
   07/10). **Aucune modification n'a jamais été tentée.** Ce n'est donc pas « ça échoue », c'est
   « l'app ne le propose pas ».

➡ **Conséquence pour 6a** : un brouillon ne doit recevoir **que de la lecture**. Tout correctif
qui lui ouvrirait un geste d'écriture vers Hektor irait contre la décision du 23/06.

### C. CE QU'ILS CONTIENNENT — des coquilles, pour l'essentiel (mesuré le 14/10)

```
527 brouillons
    0  avec un NUMERO DE MANDAT        <-- aucun n'est sous mandat
   16  avec un prix > 0
   11  avec un mandant
  507  avec un negociateur
  194  SANS AUCUNE date de mise a jour (les « coquilles » que le REST n'atteint pas)
   91  touches depuis le 1er septembre  ·  154 plus touches depuis avant juin
  168  ont des PHOTOS (956 photos, toutes sur le serveur)
```

### D. ⭐ LA DÉCOUVERTE QUI CHANGE LE RAISONNEMENT : les photos sont DÉJÀ rapatriées, SANS Hektor

**956 photos de 168 brouillons sont sur le serveur**, toutes avec leur fichier
(`local_archive_path` présent sur 956/956), **0 au cloud**, de la première le 25/09 à la
dernière le **13/10** — donc **ça continue chaque nuit**.

**Par quel chemin ?** `Console/rattrapage_photos.js`, qui porte en tête :
*« ⚠⚠ CE SCRIPT NE PARLE JAMAIS À HEKTOR »* — il lit les adresses dans le **miroir local**
(`data/hektor.sqlite`, `hektor_annonce_detail.images_json`) et télécharge sur le **CDN public**.
Et il lit **les quatre index**, brouillons compris (l. 216-229).

**➡ Les documents, eux, n'ont AUCUNE source locale.** Les colonnes du détail REST local sont :
`localite_json, mandats_json, proprietaires_json, honoraires_json, notes_json, zones_json,
particularites_json, pieces_json, images_json, textes_json, terrain_json, copropriete_json,
raw_json` — **aucune colonne de documents**. Les documents n'existent que dans la **Console web**
(`mode=chargeannonce_Documents`, `mode=UploadedDocument_list`, worker l. 4385-4418).

**Donc, pour les documents d'un brouillon, il faut forcément demander à Hektor.** C'est la
différence de fond avec les photos — et c'est pour ça que le point 6a n'est pas gratuit.

### E. LE DÉFAUT TECHNIQUE — confirmé, et il est à QUATRE endroits, pas un

`loadDossier` (`console_job_worker.js:1927`) cherche dans **trois** index puis abandonne
(l. 1977, `Dossier introuvable`) :

| ordre | table lue | ligne |
|---|---|---|
| 1 | `app_dossier_current` | 1935 |
| 2 | `app_historical_annonce_index_current` | 1945 |
| 3 | `app_archive_annonce_index_current` | 1960 |
| — | ⛔ `app_brouillon_annonce_index_current` | **absent** |

Et **les 527 ne sont nulle part ailleurs** (mesuré) : 0 dans le parc vivant, 0 dans les
vendus/clos, 0 dans les archives, 0 sans numéro Hektor, **0 collision d'identifiant** entre
`app_brouillon_id` et les trois autres clés. Donc **527 échecs sur 527**.

**⭐ Le même oubli existe dans trois fonctions SQL** *(lues en base le 14/10)* :

| fonction | ce qu'elle oublie | conséquence mesurée |
|---|---|---|
| `app_console_can_access_dossier` | le 4ᵉ index | la RLS de `app_brouillon_annonce_detail_cache` refuse un **négociateur** ; seuls admin/manager passent *(le cache est de toute façon **vide** : 0 ligne)* |
| `app_mes_biens_portefeuille()` | le 4ᵉ index | un négociateur ne verrait **jamais** les **documents** d'un brouillon (RLS de `app_console_document`) |
| `app_mes_biens_selon_perimetre()` | le 4ᵉ index | il ne voit pas non plus ses **photos** — **les 956 déjà rapatriées lui sont invisibles aujourd'hui** |

➡ Réparer `loadDossier` seul ferait descendre des documents que **seul un admin** pourrait voir.
Ce n'est pas absurde (le but d'ici la coupure est le **serveur**), mais il faut le dire.

### F. CE QUE COÛTERAIT L'INACTION — les trois dégâts, chacun vérifié dans le code

1. **Exclusion définitive.** `enqueue_empreinte_lot.js:10` : *« job en erreur sur cette annonce →
   NE JAMAIS REJOUER »* (appliqué l. 144 puis l. 190). Les 527 sortiraient du rattrapage **pour
   toujours**.
2. **Le rattrapage s'arrête.** `run_rattrapage_documents.ps1:101` passe `--max-erreurs-recentes
   20` : au-delà de 20 erreurs en 24 h, le script **refuse de poser** (sortie 4).
3. **Un rouge qui ne s'éteint pas.** `check_gti_health.py:220` — `data.travaux_en_erreur`,
   **seuil 0**, `critical` (donc **e-mail**), et un travail en erreur **ne se résout jamais** :
   rouge pendant **30 jours**.

**Pas de risque de bannissement de ce côté** : `loadDossier` échoue **avant** la première requête
Hektor. Et le filet de rejeu ne les touche pas : `sync_console_documents` n'est pas dans les
10 `types_rejouables` de `app_console_action_enqueue_due_retries` → **1 échec par annonce, pas 5**.

### G. QUAND ? — la date remesurée

| périmètre | total | déjà marquées | en erreur | en file | **reste** |
|---|---|---|---|---|---|
| archive | 35 322 | 35 320 | 0 | 0 | **2** |
| historical (vendus/clos) | 8 944 | 6 548 | 0 | 0 | **2 396** |
| **brouillon** | 527 | 0 | 0 | 0 | **527** |

Lot réel **1 000/nuit à 21:00**, et depuis `e693e42` (14/10) `--scope auto` **enchaîne** les
périmètres :

```
nuit 14→15   1 000 (2 archive + 998 vendus/clos)    reste ≈ 1 398
nuit 15→16   1 000                                   reste ≈   398
nuit 16→17     398 + ~602 BROUILLONS   <-- premier contact
```

➡ **nuit du 16 au 17/10**. `CLAUDE.md` disait « 15 au 16 » : corrigé le 14/10.

### H. CE QUI N'A PAS PU ÊTRE MESURÉ — et c'est le cœur du risque

- **La Console répond-elle `chargeannonce_Documents` pour un brouillon ?** **NON MESURÉ** : un
  audit n'appelle pas Hektor. Et **les 956 photos ne le prouvent pas** — elles sont venues du
  miroir local et du CDN, *sans* Hektor.
- **Témoin indirect, faible** : 8 `refresh_console_data` ont réussi sur des brouillons, mais ce
  gestionnaire n'utilise ni `loadDossier` ni la page documents.
- **Population suspecte** : les **68** brouillons au statut vide ont **0 détail REST local** —
  c'est exactement ceux dont la note du 22/06 dit que `AnnonceById` rend vide. Eux peuvent
  échouer **même après** le correctif, et chaque échec coûte une exclusion définitive + le rouge.
- **Combien de documents ?** Inconnu. Repères : 4,20 par annonce vivante, 5,82 par archive,
  13,03 par vente. Mais **0 brouillon sous mandat** → la pièce principale d'un bien n'existe pas
  chez eux. Attente raisonnable : **peu de documents, voire aucun**.

**Bonne nouvelle, vérifiée dans le code** : un brouillon **sans aucun document** ne casse rien.
`upsertConsoleDocuments` fait `if (!rows.length) return []` (l. 4654) — rien écrit, rien
supprimé ; le garde-fou de liste vide (3e, 13/10) refuse de marquer des documents existants
depuis une liste vide ; et l'empreinte est **quand même posée** (l. 5680) → l'annonce sort
proprement du rattrapage, sans erreur.

## ÉTAPE 2 — LA DÉCISION DE FRÉDÉRIC (14/10)

Trois options lui ont été présentées : **A** le frein (sortir les brouillons du rattrapage),
**B** apprendre le 4ᵉ index à `loadDossier` pour faire descendre les documents, **C** les deux
dans l'ordre, avec un relevé en lecture seule entre les deux.

Sa réponse, après avoir d'abord répondu « C » : **« NON, il n'y a pas de documents dans les
brouillons, donc pas nécessaire — il faut juste le savoir. »**

➡ **Donc : A, et c'est DÉFINITIF, pas un provisoire.** Pas de 4ᵉ index dans le worker, pas de
relevé chez Hektor, pas de redémarrage. Le travail restant est de **l'écrire** pour que
personne ne refasse le chemin — c'est le sens de « il faut juste le savoir ».

**Ce que les mesures disent dans le même sens** : 0 des 527 sous mandat · 0 document indexé ·
194 sans détail REST · 154 plus touchés depuis avant juin.

## ÉTAPE 3 — LE CODE (fait le 14/10)

**Un seul fichier : `Console/enqueue_empreinte_lot.js`.** Aucun patch SQL, aucune ligne de
front, **le worker n'est pas touché** — donc **aucun redémarrage**.

1. **`HORS_AUTO`** — une liste **déclarée** des périmètres hors rattrapage, avec la raison et sa
   date, posée à côté de `SOURCES`.
2. **`scopes`** — `--scope auto` filtre sur `HORS_AUTO` ; la liste des trois périmètres reste
   écrite en entier pour qu'on voie l'ordre complet. **`--scope <un seul>` n'est pas filtré** :
   une demande explicite reste explicite.
3. **Les deux alarmes ignorent les périmètres déclarés** (`restantSansDecision`). Le périmètre
   reste affiché dans `reste_a_faire` — on le **voit** — mais il ne déclenche rien.
4. **Le message `rien_a_faire`** ne dit plus « tous les périmètres sont rattrapés » quand c'est
   faux : il **nomme** ce qui n'est pas compté.
5. **L'en-tête du fichier** est corrigé : il annonçait l'enchaînement vers `brouillon`.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS — le piège, et il était cher

**Retirer `brouillon` de la liste de `auto` SANS le déclarer coûtait un e-mail rouge par nuit.**
Deux alarmes de ce fichier balaient **tous** les périmètres de `SOURCES` et sortent en **code 1** :

| alarme | quand elle aurait crié | conséquence |
|---|---|---|
| **PÉRIMÈTRE OUBLIÉ** | **dès cette nuit** : `brouillon` a du travail et n'est plus visité | code 1 → tâche en échec |
| **LOT MAIGRE** | **à la fin des vendus/clos** : il ne reste que 1 ou 2 archives du jour (< 1/10 du lot) et « du travail ailleurs » = les brouillons | code 1 → tâche en échec |

Or `check_gti_health.py` suit **« GTI Rattrapage Documents » en `critical`** → **un e-mail rouge
chaque nuit**. Une décision écrite doit donc être **déclarée** dans le code, pas seulement
retirée d'une liste.

**Le reste, vérifié un par un** : le **run de nuit** n'appelle pas ce script *(il est lancé par
la tâche de 21:00 seule — `scheduled/run_rattrapage_documents.ps1:101`)* · `enqueue_console_sync_jobs.js`
*(l'étape `-EnqueueConsoleDocuments` du run, éteinte, G.6)* a sa **propre** liste de périmètres,
en portée `daily-cloud` : **non touchée** · le **worker** : pas une ligne · la **base** : rien ·
le **front** et les **pages publiques** : rien · **aucune décision écrite renversée** — au
contraire, celle du 23/06 *(un brouillon est en lecture seule)* est respectée.

**Le retour arrière** : vider `HORS_AUTO` *(`const HORS_AUTO = {};`)* — l'enchaînement d'origine
revient à la ligne près. ⚠ Et dans ce cas il faudra **d'abord** apprendre le 4ᵉ index à
`loadDossier`, sinon c'est 527 exclusions définitives.

## ÉTAPE 4 — L'ÉPREUVE (14/10, 15:30-15:45, aucune écriture)

Trois `--dry-run` *(ce script ne parle jamais à Hektor : il ne lit que Supabase)* plus un
**témoin inverse** :

| épreuve | attendu | obtenu |
|---|---|---|
| `--scope auto --dry-run --limit 1000` | le lot de ce soir, sans brouillon | `archive 2 + historical 998`, `reste_a_faire: [historical, brouillon]`, `hors_rattrapage` affiché, **code 0** ✅ |
| `--scope auto --dry-run --limit 100000` *(= la dernière nuit du rattrapage)* | lot « maigre », il ne reste QUE les brouillons, **aucune alarme** | `retenus 2 398` *(2 + 2 396)*, `reste_a_faire: [brouillon]`, **code 0** ✅ |
| **témoin inverse** : filtre des alarmes retiré | le rouge que le frein naïf aurait coûté | `PERIMETRE OUBLIE : brouillon`, **code 1** ✅ — puis fichier remis à l'identique *(md5 `76297010…` vérifié, 0 marqueur résiduel, parseur node vert)* |
| `--scope brouillon --dry-run` | la porte reste ouverte | `brouillon: 527`, **code 0** ✅ |

## ÉTAPE 5 — LE CONTRÔLE DU RÉSULTAT

**Fait** : les 4 épreuves ci-dessus, dont le témoin inverse *(le patch a bien changé quelque
chose, et dans les deux sens)*.

**À vérifier le 15/10 au matin** *(la seule preuve par le vrai chemin)* : le journal
`logs/scheduled/rattrapage_documents_2026-10-14_21-00-*.log` doit montrer un lot de **1 000**
*(2 archives + 998 vendus/clos)*, **0 brouillon**, **sortie 0**, et le Planificateur en succès.
Et **aucune alerte** `data.travaux_en_erreur` dans l'e-mail du matin.

**Ce qui n'a pas été fait, et ne le sera pas** : le relevé chez Hektor, et le 4ᵉ index dans
`loadDossier`. **Par décision.** On ne sait donc **toujours pas** si la Console répondrait pour
un brouillon — et on n'a plus besoin de le savoir.

---

# 6a-bis — LE 4ᵉ INDEX DANS LES TROIS FONCTIONS DE DROITS

*Frédéric, 14/10 : « **A** » (on le traite ici) « **puis enchaîne sur 6b** ».*

## ÉTAPE 1 — AUDIT (14/10, lecture seule)

### VERDICT : ⛔ **IL N'Y A RIEN À OUVRIR — et l'ouvrir serait DANGEREUX.**

J'avais présenté ce point comme « un négociateur ne voit ni la fiche ni les photos de ses
propres brouillons ». **C'était vrai des fonctions, et faux de l'écran.** Trois mesures.

### ① Ce qu'un négociateur voit DÉJÀ d'un brouillon

| | |
|---|---|
| **la liste** | l'index des brouillons a pour RLS `is_app_user_active()` → **tout utilisateur actif voit les 527**, pas seulement les siens |
| **la vignette** | `photo_url_listing_app` est posée sur **510 des 527** — l'image vient **de notre serveur**, et elle est dans la ligne d'index, donc **déjà visible** |
| **la fiche** | elle s'ouvre en **fiche légère** depuis la ligne d'index, avec « Reprendre la saisie » |

### ② Le panneau photos n'est PAS affiché sur une fiche légère — la RLS n'est jamais testée

`App.tsx:29014` : si la fiche est légère, l'écran rend un avis *« Les photos ne peuvent pas être
modifiées depuis une fiche d'index léger »* **à la place** de `ConsolePhotosPanel`. Et
`App.tsx:34990` ne le rend pas du tout. Le seul endroit qui montre des photos sur une fiche
légère (`App.tsx:30990`) les prend dans `props.images` — **le détail**, pas `app_console_photo`.

➡ `loadConsolePhotos()` **n'est jamais appelé** pour un brouillon. Ouvrir la RLS de
`app_console_photo` ne changerait donc **rien à l'écran**.

### ③ ⚠⚠ ET L'OUVRIR SERAIT DANGEREUX — `app_console_can_access_dossier` est la porte de 12 fonctions

Mesuré en base : **les 12 fonctions** qui consomment une de ces trois fonctions passent **toutes**
par `app_console_can_access_dossier`, et **10 sont des fonctions d'ÉCRITURE** :

```
app_console_creer_document_optimistic     <- creer un document
app_console_creer_photo_optimistic        <- creer une photo
app_console_mark_document_signed_manual · app_console_touch_document
app_affaire_note_ecrire · app_conditions_affaire_ecrire · app_affaire_personne_ecart_fermer
app_edit_affaire_optimistic · app_geste_affaire_optimistic · app_modifier_affaire_optimistic
+ app_console_can_request_job   <- LA PORTE QUI AUTORISE A DEMANDER UN TRAVAIL HEKTOR
+ app_voit_ce_dossier_selon_perimetre
```

➡ Ajouter l'index des brouillons à cette fonction **ouvrirait d'un coup 10 gestes d'écriture et
le droit de demander un travail Hektor sur un brouillon** — exactement contre la décision du
23/06 *(un brouillon est en lecture seule)* et contre ce que Frédéric a dit aujourd'hui
*(« on n'arrive pas à les modifier »)*.

**Et les deux autres fonctions ne servent à rien ici** *(mesuré)* : `app_mes_biens_portefeuille()`
alimente les documents *(sans objet)*, `app_mandat` *(**0** ligne sur un brouillon)* et
`app_affaire_ledger` *(**1** ligne)*. `app_mes_biens_selon_perimetre()` alimente les photos
*(jamais lues, cf. ②)*, `app_contact_current` et `app_contact_relation_current` *(**26** relations
— les ouvrir élargirait l'accès aux contacts, pour rien)*.

### ④ ⭐ ET LE SYSTÈME SE RÉPARE TOUT SEUL À LA FINALISATION — le témoin

Les **73** brouillons déjà finalisés *(`is_draft=0` dans la table locale)* :

```
66  revenus dans le PARC VIVANT      ·  2 dans les archives  ·  5 disparus de Hektor
 0  encore dans l'index brouillon     (la transition marche)
638 photos de ces annonces, dont 602 pointent le BON app_dossier_id
 0  photo MAL pointee                 (les 36 autres sont celles des 7 non vivantes)
```

➡ **L'invisibilité dure exactement le temps du brouillon.** Dès que la saisie est terminée dans
Hektor, l'annonce rejoint le parc vivant **et ses photos deviennent visibles, bien rattachées**.
Il n'y a **pas d'orphelin** à craindre : la ligne photo est reposée sur la bonne clé à chaque
passage du rattrapage *(`rattrapage_photos.js` recalcule la correspondance depuis les 4 index)*.

## ÉTAPE 2 — CE QUE JE PROPOSE : NE RIEN CHANGER, ET L'ÉCRIRE

**Aucun patch.** Le point est traité par la mesure : il n'y a pas de manque visible, et le
correctif « évident » aurait ouvert dix gestes d'écriture sur des brouillons.

**Si un jour on veut vraiment qu'un négociateur voie les photos d'un brouillon dans l'app**, le
maillon qui manque n'est pas un droit, c'est **le détail** : `app_brouillon_annonce_detail_cache`
est **vide (0 ligne)** et **rien ne la remplit** — il n'existe pas de type de travail
`prepare_brouillon_annonce_detail` *(ses deux sœurs existent : `prepare_archived_…` et
`prepare_historical_…`)*. Ce serait **un nouveau type de travail = les 3 verrous**
*(contrainte, droits, distribution)* + 5 endroits dans le worker. **C'est du chantier ⑦**, et
ça ne vaut la peine que si Frédéric en a l'usage. ⚠ **Question posée, non tranchée.**
