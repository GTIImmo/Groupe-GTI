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

---

# 6b — G.2 : LE PARC VIVANT N'EST PLUS RELU DEPUIS LE 20/08

## ÉTAPE 1 — AUDIT (14/10/2026, lecture seule, aucun appel à Hektor)

### VERDICT : CONFIRMÉ, et c'est PIRE que ce que disait l'audit du 07/10

**L'âge de la dernière lecture documentaire du parc vivant, mesuré en base le 14/10 :**

| statut | annonces | jamais lues | dernière lecture | relues en 30 j |
|---|---|---|---|---|
| **Actif** | 595 | **132** | **20/08** | **0** |
| **Sous compromis** | 89 | **6** | **20/08** | **0** |
| **Sous offre** | 43 | **5** | 14/10 | 1 *(mon essai 62774)* |
| Estimation | 12 757 | **313** | 28/09 | 1 |
| **total vivant** | **13 484** | **456** | — | **2** |

**Deux annonces relues en trente jours sur 13 484** — et les deux sont des essais. Les biens
**en vente** (727) n'ont pas été relus depuis le **20 août**. Tout ce qui a été déposé chez
Hektor depuis — bons de visite, mandats, **compromis** — n'est pas chez nous.

### POURQUOI : l'étape n'est pas « mal réglée », elle est ÉTEINTE

`run_full_pipeline.ps1:1484` : l'étape n'existe que derrière `-EnqueueConsoleDocuments`. Et
`scheduled/run_quotidien.ps1:39` **ne passe pas ce drapeau** → **l'étape ne tourne jamais**.
C'est `G.6`, le point que Frédéric doit allumer — mais il ne doit PAS l'être tel quel :
sans `--detect`, elle empile **tout** le périmètre chaque nuit.

### ⭐ CE QUE LE CODE SAIT DÉJÀ FAIRE — et c'est beaucoup

`--detect` existe depuis le 20/08 (`enqueue_console_sync_jobs.js:372`, `runDetection`) et il est
bien construit :

- il compare une **empreinte du contenu** documentaire, pas une date — *parce que la date de
  mise à jour d'une annonce ne bouge pas quand on y dépose un document : 91 % des documents sont
  plus récents que la MAJ déclarée de leur annonce* ;
- ⭐ **il trie le périmètre : jamais contrôlées d'abord, puis les plus anciennement contrôlées**,
  « sans cet ordre, un plafond atteint verrouillerait le balayage sur les mêmes annonces » ;
- une annonce **sans empreinte** est empilée **sans aucune lecture Hektor** ;
- il ajoute l'**ensemble 2** : les annonces dont un cycle de **signature est en cours** — mesuré
  aujourd'hui : **75** — parce que l'empreinte ne voit pas passer « en attente → signé » ;
- il **s'arrête net** sur 401/403/429/503 ou sur une page de login, et il **ne conclut rien**
  d'une lecture ratée isolée ;
- il **porte le même frein que le worker**, lu dans les mêmes variables d'environnement ;
- il **ne double pas** un travail déjà en file (`loadPendingJobs`) ;
- et il **rafraîchit `checked_at`** sur les inchangées — donc la rotation s'entretient seule.

### LES TROIS MANQUES RÉELS

1. ⛔ **LE PLAFOND NE PLAFONNE QUE LES TRAVAUX, PAS LES LECTURES.** `--cap` (3 000 par défaut)
   arrête la boucle quand *assez de travaux sont retenus*. Si peu d'annonces ont bougé — le cas
   normal — la boucle lit **tout le périmètre**. Or `daily-cloud` = **13 484** annonces
   (`DAILY_STATUSES` inclut *Estimation*), et avec le frein (1 s par requête, +60 s toutes les
   100, +300 s toutes les 2 000) cela fait **≈ 6 h 23 de lecture**. Impossible dans le run.
   ⚠ **La limite n'est plus le bannissement** (≈ 18 000 requêtes/nuit depuis 12 nuits, 0 ban)
   **mais le TEMPS.**
2. ⛔ **L'ÉTAPE EST BLOQUANTE ET SANS SURVEILLANCE.** `& $nodeExe … ; if ($LASTEXITCODE -ne 0)
   { throw }` : une session Hektor morte **tuerait le reste du run** (Matterport, les liens
   publics de RDV, la vitrine, l'export Android). Et elle n'a **aucun `-WorkerKey`** — donc
   aucun battement, aucune sentinelle *(c'est exactement la leçon 4j du 13/10)*. Sa voisine
   immédiate, elle, en a un (`hektor.carnet_acquereurs`).
3. ⚠ **AUCUNE EXCLUSION DES ÉCHECS.** Contrairement au rattrapage (« on ne rejoue jamais »), la
   détection ré-empile une annonce **sans empreinte** à chaque passage. C'est voulu pour un bien
   vivant — mais une annonce qui échoue **toujours** reviendrait **chaque nuit**. Aujourd'hui le
   risque est nul (**0** travail `sync_console_documents` en erreur), il ne l'est pas demain.

### LA CONTRAINTE D'HORAIRE — mesurée, et elle commande tout

Le run finit **07:18-07:34** et **la descente part à 07:45** (elle l'attend jusqu'à 45 min).
L'étape est à la **fin** du run. Lui donner 1 200 lectures = **+32 min** → le run finirait
**07:50-08:06**, donc **après** l'heure de la descente.

Et trois étapes du run **refusent de démarrer s'il reste un travail console en attente**
(`require_no_console_jobs`, `sync_hektor_chauffages.py:251` — chauffage l. 786, entretien
compromis l. 1118, entretien ventes l. 1149). Elles sont **toutes avant** l'étape d'enfilement :
pas de conflit dans le même run. Mais les travaux posés vers 07:00 doivent être **digérés avant
21:00**, sinon le rattrapage refuse son lot (`--exiger-file-vide`, sortie 3).

### CE QUI EST DÉJÀ DÉCIDÉ — à ne pas re-trancher

📜 **Journal du 07/10** : *« G.2 se fera sur **toutes** les annonces vivantes, estimations
comprises »* (décision de Frédéric). ➡ Donc **pas de périmètre réduit** : toutes les vivantes,
mais **pas toutes la même nuit**.

### ⚠ LA QUESTION DE FRÉDÉRIC (14/10) ET SA MESURE

> *« Non, il faut d'abord finir le rattrapage, sinon toutes les empreintes ne seront pas posées
> et on va tout repasser au lieu de ne faire que les MAJ, non ? »*

**Sa conclusion est juste — mais pas pour cette raison.** Trois mesures.

**① Le rattrapage ne posera JAMAIS les empreintes du parc vivant.** Ses périmètres sont
`archive`, `historical` et `brouillon` — **jamais** `app_dossier_current`. Mesure : **7 750
empreintes posées ces 7 derniers jours, dont ZÉRO sur une annonce vivante**. Et les **456**
vivantes sans empreinte ne sont **dans aucun autre index** (0 archive, 0 vendu/clos, 0
brouillon) → le rattrapage **ne peut pas** les atteindre. Attendre ne les posera pas.

**② « On va tout repasser » : non, 3,4 %.** **13 028 des 13 484** vivantes ont **déjà** leur
empreinte, celle du 19-20/08. Pour elles la détection ne fait que **comparer** — exactement
« que les MAJ ». Seules les **456** sans empreinte seront repassées en entier, et ce sera vrai
quel que soit le jour où on commence.

**③ MAIS LA VRAIE RAISON D'ATTENDRE EST SOLIDE** — un seul service worker `documents`, une
seule file : les travaux de la détection feraient **refuser le lot de 21:00**
(`--exiger-file-vide`, sortie 3 + rouge) et se disputeraient le worker avec les 1 000/nuit du
rattrapage (4,8 à 7,9 h). ➡ **On démarre après la nuit du 16 au 17/10**, quand les 2 396
vendus/clos restants sont finis.

### ⭐⭐ ET CE QUE SA QUESTION A FAIT TROUVER — l'inverse de ce qu'il craignait (G.1-c)

**L'empreinte a DEUX sens contradictoires selon qui la lit :**

| qui | ce que « l'annonce a une empreinte » veut dire |
|---|---|
| le **rattrapage** (`enqueue_empreinte_lot.js`) | « **déjà faite, ne jamais y revenir** » |
| la **détection** (`--detect`) | « j'ai une **référence** à comparer » |

Donc quand une annonce **vivante** (avec son empreinte) devient **vendue**, elle entre dans
`historical` et le rattrapage **la saute** — ses pièces de fin de vie (**compromis, acte**) ne
seront **jamais** lues. C'est **G.1-c**, et c'est mesurable :

```
vendus/clos avec une empreinte                       6 548
  dont empreinte posee AVANT la reprise du 25/09        49   <-- posee quand l'annonce etait VIVANTE
  dont empreinte du lot d'aout                          48
```

➡ **49 aujourd'hui** *(la liste disait 111, comptés autrement le 26/09)*, et la détection en
fabriquera **~34 de plus par mois** (le rythme des changements d'état) **si on ne traite pas la
cause**. ⚠ **Question posée à Frédéric : G.1-c entre-t-il dans ce chantier ?**

---

# G.1-c — L'AUDIT DEMANDÉ PAR FRÉDÉRIC (« oui, mais audit avant pour être sûr de toi »)

## VERDICT : ⚠ **LE MÉCANISME EST CERTAIN. L'EFFET, JE NE PEUX PAS LE PROUVER D'ICI.**

### ① Le mécanisme — confirmé dans le code

`enqueue_empreinte_lot.js` : exclusion n° 1, *« empreinte déjà posée → déjà rattrapée »*
(l. 9, appliquée l. 190 `if (empreintes.has(id)) { stats.deja_marquees += 1; continue; }`).
L'empreinte est une **clé par numéro d'annonce**, pas par index : une annonce qui change
d'index **emporte son empreinte**, donc le rattrapage la saute.

### ② La population — **49**, pas 111

```
vendus/clos avec une empreinte                        6 548
  dont empreinte posee AVANT la reprise du 25/09         49   (48 du lot du 19-20/08)
  leur derniere lecture documentaire                20/08/2026
```
*(la liste annonçait 111, compté autrement le 26/09 — le chiffre d'aujourd'hui est 49)*

### ③ L'EFFET — ⛔ **NON PROUVÉ, et il penche même dans l'autre sens**

J'avais écrit « leurs compromis et leurs actes ne seront jamais lus ». **C'était une déduction,
pas une mesure.** La mesure dit :

| | les 6 499 lues par le rattrapage | **les 49 sautées** |
|---|---|---|
| documents en moyenne | 8,54 | **23,67** |
| avec un compromis | 30 % | 22 % |
| avec un **acte** | 7 % | **29 %** |
| avec un mandat | 35 % | **94 %** |
| dernière lecture | 12/10 | **20/08** |

Les 49 sont **mieux documentées**, pas moins. L'explication tient : ce sont des biens qui
étaient **en vente en août** — donc sous mandat, avec un dossier complet — tandis que les 6 499
vendus/clos comprennent beaucoup de vieilles fiches maigres (**2 200 n'ont aucun document**).

⚠ **Et c'est précisément pour ça qu'on ne peut pas conclure d'ici : on ne voit pas une absence.**
Ce qui manquerait, c'est ce qu'on n'a jamais téléchargé. Les 14 actes qu'elles portent ont été
lus **en août**, avant la vente.

### ④ Ce qui rendrait sûr — un relevé en lecture seule, ~5 requêtes

Lire la page documents de **5 des 49** chez Hektor et comparer le compte avec le nôtre. Écrit
**zéro** ligne. ⛔ **Demande l'accord de Frédéric** (un audit n'appelle pas Hektor).

### ⑤ Et si c'est confirmé : il n'y a AUCUN moyen de rattraper à la main aujourd'hui

`createSyncConsoleDocumentsJob` existe dans `api.ts:8082` mais **n'a aucun appelant** : il
n'y a **pas de bouton « resynchroniser les documents »** dans l'app. Le seul recours serait de
retirer leur empreinte pour que le rattrapage les reprenne — un geste en base.

## ⭐⭐ 6b — LA PREUVE MÉTIER, SANS APPELER HEKTOR (14/10)

*Demande de Frédéric : « continue tes mesures et explique-moi clairement quel problème tu
souhaites corriger par rapport au chantier ».*

**Le raisonnement** : un **mandat signé est un acte**. Son document existe donc **forcément**
chez Hektor. On n'a pas besoin de le demander à Hektor pour savoir qu'il nous manque — il suffit
de regarder les biens **sous mandat** et de voir si on a le document.

### Les biens EN VENTE sous mandat, selon la date de signature du mandat

| mandat signé | biens sous mandat | document chez nous | **manquant** | % |
|---|---|---|---|---|
| **avant le 20/08** | 472 | 399 | 73 | **15,5 %** |
| **après le 20/08** | **97** | **4** | **93** | **95,9 %** |
| sans date | 2 | 0 | 2 | 100 % |

➡ **Avant le 20 août on a 84 % des mandats. Après, on en a 4 %.** La bascule est nette, et elle
tombe exactement au jour où la relecture s'est arrêtée. **93 mandats signés n'existent que chez
Hektor.**

*(Le filtre a été contrôlé : les mandats s'appellent bien « Mandat (Avec saisie du numéro)
(Vente) » — 377 exemplaires —, « mandat_simple_de_vente… », « mandat_exclusif… »,
« Mandat de vente 2026… ». Tous portent le mot. Et les **4** qui sont chez nous sont
vraisemblablement ceux que **notre app a générés** elle-même, arrivés par un autre chemin.)*

### Le reste du dossier des biens en vente

```
595 biens ACTIFS           ->  199 n'ont AUCUN document chez nous
 89 biens SOUS COMPROMIS   ->   76 n'ont aucun document « compromis »
 43 biens SOUS OFFRE       ->    6 n'ont aucun document
```
⚠ Pour le compromis la preuve est **plus faible** que pour le mandat : seuls 30 % des
vendus/clos relus par le rattrapage en portent un, donc son absence ne prouve pas à elle seule
qu'il manque.

### LE COÛT DE L'ATTENTE, mesuré

**97 mandats signés en 8 semaines ≈ 12 par semaine.** Chaque semaine sans relecture ajoute donc
**~12 mandats qui n'existent plus que chez Hektor** — et le jour de la coupure, ils sont perdus.

### CE QUE JE VEUX CORRIGER, EN UNE PHRASE

**Rallumer la relecture des dossiers chez Hektor, en la plafonnant** pour qu'elle ne dure pas
6 h et ne casse ni le run ni le rattrapage. Le **budget de lectures** codé aujourd'hui est
exactement la pièce qui manquait pour pouvoir la rallumer sans danger.

### ⚠ « ON AVAIT POURTANT DÉJÀ RÉCUPÉRÉ TOUS LES DOCUMENTS DES VIVANTS » (Frédéric, 14/10)

**Il a raison, et ma formulation était trompeuse.** Vérifié dans l'historique et en base :

- **La récupération d'août a bien été complète** : **13 028** des 13 484 annonces vivantes
  portent une empreinte **du 19 ou du 20/08**. C'est la campagne des commits `220026a`
  *(« Rattrapage empreintes : composeur de lot qui ne rejoue jamais une annonce »)* et
  `652c962` *(le frein posé après le bannissement du 20/08)*.
- **Donc rien n'« échoue à redescendre ».** Ce qui existait le 20 août est chez nous.
  **La photo était complète — elle a simplement huit semaines.**

**Les 93 mandats manquants ne contredisent pas sa mémoire : ils sont nés APRÈS la photo.**

```
93 mandats signes depuis le 20/08 et absents de chez nous :
   71  biens NES APRES LE 20/08       -> ils n'existaient pas lors de la recuperation
                                         (aucune empreinte, et AUCUN DOSSIER sur le serveur :
                                          verifie a la main sur 63280, 63200, 63285, 63184, 63105)
   22  biens DEJA LUS les 19-20/08    -> leur mandat a ete signe APRES la lecture
                                         (ex. 14429, lu le 19/08, mandat du 12/10, 1 seul fichier)
```

➡ **Il y a donc DEUX fuites, pas une**, et il faut les nommer séparément :
 ① les **annonces neuves** que personne n'est jamais allé lire *(**456** sans aucune empreinte)* ;
 ② les **documents ajoutés après la lecture** sur des biens déjà récupérés *(invisibles sans
 relecture, puisque la date de mise à jour d'une annonce ne bouge pas quand on y dépose une
 pièce)*.

**La formule juste n'est donc pas « les documents ne redescendent pas »** — c'est :
**« depuis le 20 août, plus personne ne va voir s'il y a du nouveau. »**

---

## ✅ LE RELEVÉ EN LECTURE SEULE (14/10, 15:55 — accord de Frédéric : « 1. ok »)

**Une seule commande a répondu aux DEUX questions, en 5 requêtes Hektor et 0 écriture :**

```
node Console/enqueue_console_sync_jobs.js --scope historical --detect --dry-run --max-lectures 5
```

*Pourquoi ce périmètre : le tri de `runDetection` lit « les plus anciennement contrôlées »
d'abord, et les 49 annonces de G.1-c sont précisément les plus anciennes (19-20/08) parmi les
vendus/clos — toutes les autres ont été relues après le 25/09.*

### Résultat

```
balayees            5        lectures           5
inchangees          1        budget_lectures    5
changees            4        budget_atteint  true
sans_empreinte  2 396        arret           null     <- arret NORMAL, pas un refus de Hektor
suivi_signature     7        jobs_empiles   2 407     <- dry-run : RIEN n'a ete pose (verifie : 0 travail cree)
```

### ① LE BUDGET DE LECTURES FONCTIONNE — éprouvé

Il s'est arrêté **exactement** à 5 lectures, avec son propre témoin `budget_atteint: true` et
`arret: null` — donc la distinction entre « budget atteint » (normal) et « Hektor nous écarte »
(anormal) tient. **Sortie 0.** Et **0 travail créé** (contrôlé en base après coup).

### ② ⭐⭐ G.1-c EST CONFIRMÉ — 4 sur 5

**4 des 5 annonces vendues que le rattrapage saute ont des documents NOUVEAUX chez Hektor.**
C'est la preuve que je ne pouvais pas obtenir de notre côté — on ne voit pas une absence, mais
Hektor, lui, la montre.

➡ Sur les **49** concernées, cela représente **≈ 39 biens vendus** dont il nous manque des
pièces : **compromis, actes**. ⚠ Et ces 49 **ne seront jamais reprises** par le rattrapage
(« empreinte déjà posée = déjà faite »), ni par la détection (qui ne couvre que le parc vivant).

### ⚠ AU PASSAGE, UN AVERTISSEMENT TROUVÉ PAR LE RELEVÉ

`jobs_empiles: 2 407` en dry-run sur `historical` : lancée **pour de vrai** sur ce périmètre,
la détection poserait **2 407 travaux d'un coup** (les 2 396 sans empreinte + 7 signatures + 4
changées) — elle doublerait le travail du rattrapage et noierait le worker.
➡ **Ne jamais lancer `--detect` sur `historical` sans `--cap` serré.** Le périmètre de la
détection, c'est le **parc vivant**.

---

## ÉTAPE 3 — LE PÉRIMÈTRE « EN VENTE » (14/10, « vas-y » de Frédéric)

**3 lignes utiles, additives**, dans `enqueue_console_sync_jobs.js` : un périmètre `vente`
(`Actif`, `Sous offre`, `Sous compromis`, non archivées) et un `source.statuses || DAILY_STATUSES`
dans la construction de la requête — donc `daily-cloud` et `all-local` sont **inchangés au
caractère près**.

**Pourquoi il fallait un périmètre et pas seulement un budget** : les 13 028 empreintes du parc
vivant portent **toutes la même date** (19-20/08). Le tri « les plus anciennement contrôlées
d'abord » **ne peut donc pas les distinguer**, et sert les lignes dans l'ordre où elles
arrivent : sur 13 484 annonces dont **12 757 estimations**, un budget de 1 200 lectures en
dépenserait **~1 140 sur des estimations qui dorment**. ➡ **Le tri ne remplace pas un périmètre
quand toutes les dates sont égales.**

### ÉTAPE 4 — LES ÉPREUVES (14/10, 16:10)

| épreuve | appels Hektor | attendu | obtenu |
|---|---|---|---|
| `--scope vente --dry-run` | **0** | le périmètre = 595 + 89 + 43 | **727** ✅ |
| **témoin inverse** `--scope daily-cloud --dry-run` | **0** | **inchangé** | **13 484** ✅ |
| `--scope vente --detect --dry-run --max-lectures 5` | 5 | 142-143 sans empreinte, budget respecté | `sans_empreinte 142` · `suivi_signature 31` · `lectures 5` · `budget_atteint true` · `arret null` · `jobs_empiles 174` *(= 142+31+1, cohérent)* ✅ |

**Et une mesure utile au passage** : sur les 5 biens en vente relus, **1 a changé, 4 non**.
Le taux de changement du parc vivant est donc **bien plus bas** que celui des vendus/clos
*(4 sur 5)* — ce qui se comprend : un bien vendu reçoit son compromis et son acte, un bien en
vente qui attend ne reçoit rien.

➡ **Estimation du lot de rattrapage du parc vivant : ~350 travaux**, pas 1 000
*(142 sans empreinte + 31 signatures + ~20-30 % des 584 relues)*.

### ⭐ LA TROUVAILLE QUI REND LA PREMIÈRE PASSE QUASI GRATUITE

Une annonce **sans empreinte** est empilée **avant toute lecture** (le tri la met en tête, et le
code l'empile sans comparer). Donc :

> **`--scope daily-cloud --detect --max-lectures 1 --cap 600` ramasse les 456 annonces jamais
> lues du parc vivant entier — estimations comprises — pour UNE SEULE requête Hektor.**

C'est là que sont les **71 mandats manquants** de biens nés après le 20/08.

## LES DEUX COMMANDES DE LA PASSE DE RATTRAPAGE — ⛔ accord de Frédéric requis (elles POSENT des travaux)

```
A) les 456 JAMAIS LUES, tout le parc vivant, pour ~1 requete de lecture :
   node Console/enqueue_console_sync_jobs.js --scope daily-cloud --detect --max-lectures 1 --cap 600
      -> ~531 travaux (456 + 75 signatures) · worker ~1 h 20

B) les 584 biens EN VENTE deja lus, pour voir ce qui a bouge depuis aout :
   node Console/enqueue_console_sync_jobs.js --scope vente --detect --max-lectures 800 --cap 400
      -> detection ~15 min · ~175 travaux · worker rapide (les documents deja la ne sont PAS retelecharges)
```

**Quand** : le matin, après le run et la descente, vers **10:00**. ⚠ **La file doit être vide à
21:00** sinon le rattrapage refuse son lot (sortie 3 + un rouge) : avec ~700 travaux au total et
~2 h 30 de worker, on finit vers 12:30-13:00. Large.
**Dans quel ordre** : **A d'abord** (c'est là que sont les mandats manquants, et ça ne coûte
rien), on regarde le résultat, puis **B**.

---

## LE MEILLEUR MOMENT — 22:00 (choix délégué par Frédéric : « tous les soirs, trouve le meilleur moment »)

**Pourquoi pas dans le run** — l'étranglement du matin, mesuré :

```
05:00  le run        finit 07:18-07:34
07:45  la descente   attend le run jusqu'a 45 min, puis dure 18 a 64 min
09:00  la sauvegarde
```

19 min de plus dans le run → il finit **07:37-07:53**, la descente part vers 07:53 et, au pire,
se termine à **08:57** : **trois minutes** avant la sauvegarde. C'est exactement l'empilement qui
a déjà coûté un décalage-pansement le 12/10.

**22:00** : agence fermée, Hektor calme, **rien d'autre ne tourne** *(03:00, 05:00, 07:45, 08:00,
09:00, 12:30, 18:00, 21:00)*, travail digéré vers 23:00 — loin des recherches actives de 03:00 et
du run de 05:00.

⛔ **Deux conditions avant d'enregistrer la tâche**, écrites en tête du script :
 ① **retirer la tâche de 21:00** quand le rattrapage est fini *(nuit du 16 au 17)* — sinon ses
 1 000 travaux occupent le worker jusqu'à 01:47-04:57 et les nôtres passent derrière ;
 ② **l'ajouter à la LISTE du moniteur**, pas seulement à la table des gravités *(voir ci-dessous)*.

**Le script est écrit et dormant** : `scheduled/run_detection_documents.ps1` — aucune tâche ne
l'appelle. Éprouvé `-DryRun -Lectures 2 -Cap 10` : parseur PowerShell vert, A et B tournent,
sortie 0, **0 écriture**. ⭐ **A a ramassé les 455 annonces jamais lues du parc vivant entier
pour UNE SEULE requête Hektor** (455 + 25 signatures + 1 changée = 481 travaux).
*(La 456ᵉ était dans l'ensemble « signature », compté en premier : les chiffres se recoupent.)*

---

# ⚠⚠ DEUX TROUS TROUVÉS EN PRÉPARANT — ILS BLOQUENT L'ALLUMAGE

## ① LA SURVEILLANCE DES TÂCHES : 6 SUIVIES SUR 8 — *5ᵉ fois le même trou*

Mesuré dans `app_monitor_status` à 17:50 : *« Tâches planifiées : **6 suivies**, 0 en anomalie »*.

`check_gti_health.py` ne regarde **que** les noms de son argument `--scheduled-tasks`
(l. 3138) : `GTI Quotidien, GTI Recherches Actives, GTI Health Monitor, GTI Relances Email,
GTI Sauvegarde, GTI Descente`. **Deux tâches existantes sont absentes :**

| tâche | déclarée `critical` ? | réellement suivie ? |
|---|---|---|
| **GTI Rattrapage Documents** | ✅ oui, le **26/09** | ⛔ **NON** |
| **GTI Reprise Envois Hektor** | ⛔ non | ⛔ **NON** |

➡ Le 26/09, le correctif a été **appliqué à moitié** : la gravité a été posée dans
`TASK_CRITICALITY` — avec le commentaire *« QUATRIÈME FOIS LE MÊME TROU »* — mais **le nom n'a
jamais été ajouté à la liste des tâches regardées**. Donc **la tâche de 21:00 n'a jamais été
surveillée**, et la cinquième occurrence du même trou dure depuis dix-huit jours.

## ② ⚠⚠ LA PAGINATION SANS TRI : LA DÉTECTION NE VOIT QUE LA MOITIÉ DES SIGNATURES

`enqueue_console_sync_jobs.js` pagine ses deux chargements avec `limit` + `offset` et **sans
aucun `order=`** : `loadFingerprints` (l. 384, **55 pages**) et `loadSignatureFollowSet`
(l. 402, **163 pages**).

**C'est le défaut corrigé le 25/09 dans l'AUTRE fichier** (`enqueue_empreinte_lot.js`, commit
`461a66c` — *« mon rapatriement a perdu 40 % de son travail, en silence »*, 174 433 photos sur
435 126 déclarées absentes à tort). **Il a été laissé entier ici.**

**Preuve indépendante** — la vérité calculée en base avec la règle *exacte* du code, contre ce
que le script a vu :

| | vérité (SQL) | vu par le script |
|---|---|---|
| biens **en vente** avec une signature en cours | **58** | **31** *(53 %)* |
| **parc vivant** | **59** | **25** *(42 %)* |

➡ **La moitié du suivi de signature est perdue, en silence.** Et c'est grave précisément ici :
l'empreinte **ne peut pas** voir passer « en attente → signé » *(les identifiants de procédure
sont les mêmes avant et après)* — cet ensemble est **le seul moyen** de voir une signature
aboutir. *(`loadFingerprints` s'en est tiré ce soir — 455 = 456 − 1 — mais c'est de la chance,
pas de la conception : 55 pages jouées au même jeu.)*

**Le correctif existe déjà dans le projet** : le curseur de `enqueue_empreinte_lot.js`
(`loadSet`, l. 92-116) — « les 1 000 suivants APRÈS cet identifiant », trié sur une clé unique.
Il suffit de le recopier *(clé : `hektor_annonce_id` pour les empreintes, `id` pour les
documents — et il faut alors SÉLECTIONNER `id`, sinon le curseur saute des lignes)*.

⛔ **Tant que ② n'est pas corrigé, allumer la détection chaque soir ferait deux dégâts** :
des annonces déclarées « sans empreinte » à tort *(donc resynchronisées en entier pour rien,
avec des téléversements cloud inutiles)*, et **des signatures qui n'aboutissent jamais chez
nous**.
