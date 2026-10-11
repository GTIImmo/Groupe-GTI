# CHANTIER ④ — AUCUN ÉCHEC SILENCIEUX

> Ouvert le **09/10/2026**. Méthode : *audit du sujet → explication → « vas-y » → code →
> contrôle du résultat → documents*. Source des points : `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md`
> §2 ④, plus les deux restes du chantier ⑤.
>
> ⚠ **Les numéros de ligne de l'audit du 08/10 ont bougé** : `console_job_worker.js` a été
> édité depuis. Toujours re-localiser par `grep`, jamais par le numéro.

## LE TABLEAU DE TÊTE — *l'état, en un coup d'œil*

| # | Le point | État |
|---|---|---|
| **4a** | la **suite** d'une création (champs, mandant) rate, mais le travail est marqué « réussi » | ✅ **FINI le 09/10** — patch appliqué et contrôlé (empreinte `e2c015e1…`, 0 ligne, droits intacts, moniteur vert) · épreuve hors ligne **19/19** · **les 4 workers redémarrés à 17:30:49** (battement `startup` en base) |
| **4b** | **aucun nouvel essai** pour 6 familles de travaux, et le worker écrit quand même « Le travail sera repris » | 🧪 **audit fait (PARTIEL)** · **option A codée le 09/10**, 11/11 hors ligne : les **5 messages** ne promettent plus · attend le redémarrage du worker · ⏳ **options B et C en question** (brancher le repreneur, prévenir) |
| **4c** | « Annonce en création » en échec **sans marque d'erreur** (le marqueur lit une table plus remplie) | 🧪 **audit fait (CONFIRMÉ)** · **A1 codée le 11/10**, épreuve **21/21** : la sentinelle qui existait déjà sait enfin juger · aucune écriture, aucun déploiement |
| **4d** | une **recherche créée en échec** disparaît au bout de 24 h, sans bouton « réessayer » | 🧪 **audit fait (PARTIEL)** · **A et B codés le 11/10** : on compte (3ᵉ branche) et les erreurs durent **7 jours** · répétition **assemblée depuis les vrais fichiers**, attend le collage |
| **4e** | les **photos de la création** attendent dans la mémoire du navigateur → onglet fermé = perdues | ⬜ |
| **4f** | l'alarme **« travaux en erreur » figée au rouge à 15** ; gestes mandant et transaction jamais dans `geste_abandonne` ; 4 types de transaction absents de `JOB_TYPES_A_NOTIFIER` | ⬜ |
| **4g** | *(reste de ⑤ : 5f)* l'**abandon réel** (5 tentatives ou abandon humain) ne rend pas l'état — 2 fonctions SQL | ⬜ |
| **4h** | *(reste de ⑤ : 5h B/C)* **marqueur à l'écran** et **bouton « réessayer »** pour un mandant créé en échec | ⬜ |
| **4i** | `--missing-only`, passé **chaque soir par le run**, est **sans appelant depuis le 21/07** : l'option ne fait rien, et personne ne le dit *(journal des décisions, 09/10)* | ⬜ |

**Ordre retenu** : celui de l'audit (4a → 4f), puis les deux restes de ⑤ (4g, 4h), qui touchent
les mêmes fonctions. Frédéric peut le changer.

---

# POINT 4a — LA SUITE D'UNE CRÉATION QUI RATE

## ① AUDIT — *09/10/2026, lecture seule*

**Verdict : CONFIRMÉ comme structure, ÉTEINT comme panne.**

### Le code d'aujourd'hui

`Console/console_job_worker.js`, `handleCreateHektorDraftAnnonce` (l. 19924-20166). Le travail
fait trois choses et **attrape** les échecs des deux dernières :

| Le morceau | Où | À l'échec |
|---|---|---|
| les champs saisis à la création | l. 19951-19962 | `catch` → `initial_fields_update.status = "error"`, le travail continue |
| rattacher un mandant **existant** | l. 20025-20039 | `catch` par contact → `partial_error`, le travail continue |
| créer **et** rattacher un mandant | l. 20088-20097 | `catch` → `status = "error"`, le travail continue |

Puis la fonction rend son résultat : le travail finit **« done »**. Or l'avertissement
(`notifyJobFailureBestEffort`) n'est appelé **que dans le `catch` du lanceur** (`processOnce`,
l. 20370) : **un travail qui ne tombe pas ne prévient personne.** Et **personne ne relit** le
compte rendu — seul lecteur hors du worker : `Console/build_inventory_from_exports.js:146`,
un script d'inventaire hors ligne.

### La base, mesurée le 09/10

```
79 creations du 15/05 au 24/09 -- TOUTES « done », aucune « error », jamais.
  3 echecs des champs   07/06 bien 62437  « Champ numerique invalide: pool »
                        07/07 bien 62637  « Date Hektor invalide pour DATE_LIBER »
                        08/07 bien 62657  « Date Hektor invalide pour DATE_DISPO »
  1 echec de mandant    28/08 bien 62965  « Association mandant non confirmee, contact 603953 »
  0 cas « partial »     (quelques groupes ecrits, d'autres non : jamais arrive)
```

**Quand ça rate, c'est TOUTE la fiche qui est perdue, pas un champ.** Preuve : pour les 3 cas,
`app_console_job_log` ne porte **aucune ligne « running »** pour l'étape
`hektor_annonce_initial_fields`, seulement la ligne « error » → le worker s'est arrêté **pendant
la préparation**, rien n'a été envoyé. Une seule case mal remplie faisait tomber les **167**
champs de la création.

**Aucun dégât réel.** Les 4 cas sont des **annonces d'essai** : « TEST CODEX AUDIT »,
« TEST C13 clôture mandat », et deux maisons de Firminy du compte d'essai. Et le geste n'a
presque jamais servi pour du vrai : sur 79 créations, **45** titrées « TEST… », **49** à
Firminy, **5 villes**, **3 demandeurs**, **9** encore au parc vivant.

### L'historique — les quatre causes sont déjà bouchées

| Le cas | La cause | Bouchée |
|---|---|---|
| 07/06 `pool` | un nombre invalide faisait tout tomber | `f6b3711` **09/06** — `skipInvalidNumbers`, le champ est sauté |
| 07/07, 08/07 | une date invalide faisait tout tomber | `a49055b` **10/07** — `try/catch` l. 9153-9161, le commentaire nomme le cas (`DATE_DISPO`) |
| 28/08 mandant | la console Hektor est **filtrée par agence** | `e3799d3b` **31/08** — l'API tranche avant de déclarer l'échec (l. 15030-15036) |

Et le 28/08 **n'a rien perdu** : `app_relation` **107234**, contact 603953 sur l'annonce 62965,
`present_in_hektor = true` → **faux négatif**.
*Non mesuré : si c'est notre geste ou un humain qui a posé ce lien (notre registre ne l'a vu
qu'au 30/09).*

**Donc le trou qui reste n'est pas la cause, c'est LE SILENCE** : les trois causes connues sont
bouchées, la quatrième on ne la connaît pas encore. Et à l'étape 2 (« l'app fait tout le travail
quotidien »), 43 négociateurs créeront leurs annonces ici.

### La décision à ne pas renverser

Le commentaire du **22/09** (`a19d9c5`, l. 20012-20017) : *« ici on NE refuse PAS le lot :
l'annonce est déjà créée chez Hektor »*. Trois raisons, vérifiées :
1. l'enveloppe `handleCreateHektorDraftAnnonceWithProvisional` (l. 20168) marque **« Erreur de
   création »** dès que le travail jette → on l'afficherait sur une annonce bien créée ;
2. rejouer une **création** la **doublerait** (règle **C.4-bis**) ;
3. `create_hektor_draft_annonce` est **absent de `types_rejouables`** (relu en base).

## ② LE CORRECTIF — *expliqué le 09/10, « OPTION A » de Frédéric*

> **On ne change rien à ce que fait le worker. On ajoute seulement de quoi le DIRE.**

**Moitié 1 — le worker prévient le négociateur** *(`Console/console_job_worker.js`, +123 lignes,
0 suppression)*
`bilanSuiteCreationIncomplete` + `avertirSuiteCreationIncompleteBestEffort`, appelées **juste
avant le `return` final** de la création. Si l'un des trois morceaux a raté : une ligne de
journal qui résume (`suite_creation_incomplete`) et **un message dans la cloche de l'app**
(`app_notification`, type `creation_suite_incomplete`), au négociateur retrouvé par la chaîne
**qui existe déjà** (`resolveJobFailureRecipient`). Texte : *« L'annonce VA2501 est bien créée
dans Hektor, mais les champs saisis à la création n'ont pas été enregistrés. »*
Interrupteur **`CONSOLE_ALERTE_SUITE_CREATION`** (allumé par défaut, `=false` pour l'éteindre).
**Le travail reste « done »** : rien n'est écrit vers `app_console_job`.

**Moitié 2 — la surveillance le voit** *(`supabase/patch_4a_suite_creation_visible_2026-10-09.sql`)*
Une branche `UNION ALL` ajoutée à **`app_en_attente_humain`** : les créations « done » dont le
compte rendu porte un échec, de moins de 30 jours, pas soldées dans `app_pending_resolution`.
La sentinelle **`data.geste_abandonne`** (seuil 0, `monitoring/check_gti_health.py:342`) les voit
**sans une ligne de code en plus**. `objet = 'geste'` est conservé pour que le mécanisme
« c'est traité » marche à l'identique.

### Ce que ça pourrait casser ailleurs — chacun vérifié

| Ce que ça touche | Vérifié | Preuve |
|---|---|---|
| l'état du travail | inchangé : aucun `throw` ajouté | `processOnce` l. 20361-20372 ; épreuve (2i) |
| « Erreur de création » au front | inchangée : elle ne vient que d'un `throw` | l. 20168-20181 |
| le filet de rejeu (cron 13) | ce type est absent de `types_rejouables` → aucun rejeu, aucune annonce doublée | `pg_get_functiondef` relu en base |
| le compte rendu `result_json` | non touché ; seul lecteur extérieur : un script hors ligne | `build_inventory_from_exports.js:146` |
| la cloche du front | charge `app_notification` **sans liste blanche de types** (`type: string`) | `apps/hektor-v1/src/lib/api.ts:3837-3855` |
| l'index unique des non-lues | `(négociateur, dossier, type) WHERE read_at IS NULL` + `ignore-duplicates` → un seul non-lu par bien, jamais d'erreur | `app_notif_unread_uq` relu en base |
| les lecteurs de la vue | un seul : `monitoring/check_gti_health.py:344`. 7 colonnes, même ordre, mêmes types | grep complet du dépôt |
| le chantier ① (sécurité) | ACL = `postgres` + `service_role` (anon et authenticated retirés le 08/10), `reloptions` vide. `create or replace view` **conserve** l'ACL ; jamais de `drop view` | `relacl` relu + `patch_chantier1_...sql:163` ; contrôle de sortie dans le patch |
| le bruit de la sentinelle | **4 lignes au total, 0 sur 30 jours** → elle reste verte aujourd'hui | mesure du 09/10 |
| les décisions écrites | 22/09 (« on ne refuse pas le lot ») et C.4-bis (« jamais rejouer une création ») : **respectées** | commentaires l. 20012-20017 |
| run de nuit, crons, phase2, pages publiques | rien : aucun ne lit cette vue ni ce compte rendu | grep |

### Retour arrière
- Moitié 1 : `CONSOLE_ALERTE_SUITE_CREATION=false` + redémarrage des 4 workers, ou `git revert`.
- Moitié 2 : `patch_4a_suite_creation_visible_2026-10-09_INVERSE.sql` — empreinte attendue après
  retour : **`2ef0749361e2bb309df7cb7cdab9cbec`** (celle d'aujourd'hui).

## ③ LE CODE — *09/10*

| Fichier | Quoi |
|---|---|
| `Console/console_job_worker.js` | +123 lignes, **0 suppression** : l'interrupteur, les libellés, `bilanSuiteCreationIncomplete`, `avertirSuiteCreationIncompleteBestEffort`, et l'appel avant le `return` |
| `Console/test_suite_creation_avertie.js` | l'épreuve hors ligne (n'appelle ni Hektor ni Supabase) |
| `supabase/patch_4a_suite_creation_visible_2026-10-09.sql` | la branche neuve + garde-fou d'entrée (empreinte) + contrôle de sortie (7 colonnes, droits) |
| `..._INVERSE.sql` | remet la vue d'aujourd'hui, au caractère près |
| `..._REPETITION.sql` | vrai patch + vrai inverse + erreur volontaire qui annule tout |

## ④ L'ÉPREUVE

**Hors ligne, le worker : 19 contrôles, 19 verts** (`node Console/test_suite_creation_avertie.js`).
Il fait tourner **les vraies fonctions** du worker avec un faux Supabase. Ce qu'il prouve :
tout va bien → **pas un mot, pas une requête** · les champs ratés → **une** ligne de journal et
**un** message, au bon négociateur, avec le repère du bien · `partial` compte aussi · les deux
sortes de mandant · deux manques → **un seul** message qui porte les deux · le cas du 28/08 garde
**lequel** des contacts a raté · l'interrupteur éteint → **rien** · pas de destinataire → la trace
reste au journal · **si l'avertissement casse, la création réussie n'est PAS mise en échec** ·
et **rien n'est écrit vers `app_console_job`**.

**En base, la branche neuve éprouvée seule, en lecture** (le garde-fou interdit la répétition
complète depuis la session) : elle rend **exactement les 4 cas connus**, avec le bon texte —
```
annonce 62437  annonce creee chez Hektor, mais : champs saisis a la creation
annonce 62637  annonce creee chez Hektor, mais : champs saisis a la creation
annonce 62657  annonce creee chez Hektor, mais : champs saisis a la creation
annonce 62965  annonce creee chez Hektor, mais : mandant choisi non rattache
```
et le libellé retombe sur le titre demandé quand l'annonce n'est plus au parc vivant.

**Ce qui ne sera PAS prouvé en réel** : je ne peux pas provoquer un vrai échec de création sans
salir Hektor. 4a reste prouvé **hors ligne et par la mesure**, pas par un essai réel.

### La répétition — *jouée par Frédéric le 09/10, EXACTE sur les 13 mesures*

```
empreinte_avant=2ef0749361e2bb309df7cb7cdab9cbec   lignes_avant=0   colonnes_avant=7
acl_avant={postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres}   <- ni anon ni authenticated
empreinte_apres=e2c015e16d1339fee080b6b2cc7bcb2b   <- LA NOUVELLE REFERENCE
lignes_apres=0  branche1_apres=0  branche2_apres=0  colonnes_apres=7
acl_apres=IDENTIQUE        commentaire_pose=oui
branche2_sans_fenetre=4    <- LA PREUVE : la branche neuve retrouve les 4 cas
exemple=annonce 62657 -> annonce creee chez Hektor, mais : champs saisis a la creation
empreinte_retour=2ef0749361e2bb309df7cb7cdab9cbec  <- le retour arriere rend la vue au caractere pres
acl_retour=IDENTIQUE       commentaire_retour=vide
```

`lignes_apres = 0` est **voulu** : les 4 cas datent du 07/06 au 28/08, hors de la fenêtre de
30 jours — d'où la mesure sans fenêtre. L'erreur finale était bien `P0001 ESSAI ANNULE` :
**rien n'a été écrit**. L'empreinte d'après a été inscrite dans le patch comme **contrôle de
sortie** : un patch qui ne donnerait pas `e2c015e16d1339fee080b6b2cc7bcb2b` refuse de
s'enregistrer.

### ✅ LE PATCH EST APPLIQUÉ — *par Frédéric le 09/10, contrôlé en base*

| Contrôlé | Attendu | Mesuré |
|---|---|---|
| empreinte de la vue | `e2c015e16d1339fee080b6b2cc7bcb2b` *(celle de la répétition)* | **identique** ✅ |
| 7 colonnes, **dans l'ordre** | `objet, reference, libelle, nature, cause, tentatives, depuis` | **identique** ✅ |
| lignes de la vue | 0 | **0** (branche 1 : 0 · branche 2 : 0) ✅ |
| droits *(chantier ①)* | `postgres` + `service_role`, ni `anon` ni `authenticated` | **identique** ✅ |
| commentaire de la vue | posé | **oui** ✅ |
| rien d'autre n'a bougé | 79 créations toutes « done » · 2 gestes soldés · 0 source pour la branche 1 | **identique** ✅ |

La vue installée est **au caractère près** celle que la répétition a jouée (même empreinte).
**Ce que le contrôle ne prouve pas** : la branche rend 0 ligne *aujourd'hui*, et c'est normal
(les 4 cas sont hors de la fenêtre de 30 jours, les 2 créations récentes ont réussi). La preuve
qu'elle **trouve** reste `branche2_sans_fenetre = 4` de la répétition. Aucun faux échec n'a été
fabriqué en production pour l'afficher.

### Le moniteur, passé en lecture seule après le patch *(`--no-alerts --dry-run`)*

**71 contrôles. La cible est VERTE :**
```
data.geste_abandonne   ok   « Gestes abandonnes en attente d'un humain: 0 (seuil 0) »
```
→ le moniteur **lit toujours la vue** à travers l'API, avec la clé de service : le patch n'a
cassé ni l'accès ni la lecture. `data.envois_en_attente_hektor` : ok également.

**11 contrôles non verts, AUCUN causé par 4a** — vérifié un par un :
`scheduledtasks:gti_descente` (code 1, déjà connu les 08 et 09/10) · **`data.travaux_en_erreur`
17 (seuil 0)** → c'est le point **4f** · `data.mandat_disparu` **1 sur 27 004** *(était 0 au run
du 09/10 — nouveau, à signaler, hors chantier ④)* · `data.recherche_disparue` 3 ·
`data.ecart_statut_regle` **illisible (délai dépassé)** · `data.notif_orphelines` 154 ·
`data.notif_non_lues` 1 527 (seuil 300) · `data.orphelins_recherche` 8 · `console.jobs.errors` 2.

### ⭐ MESURE D'AVANCE POUR 4f *(prise au passage, le 09/10)*

Les **17** travaux en erreur, par genre — **aucune création, aucun d'aujourd'hui** (donc 4a n'en
a ajouté aucun) :
```
refresh_console_data        14   du 01/10 au 05/10   tentatives max = 1
sync_console_documents       1      08/10            tentatives max = 1
refresh_console_contact_data 1      08/10            tentatives max = 1
unlink_hektor_mandant        1      03/10            tentatives max = 1
```
⚠ **`tentatives max = 1` PARTOUT** : cela confirme, chiffres en main, ce que l'audit du 08/10
annonçait pour 4f — **aucun geste n'atteint jamais 5 tentatives**, donc **aucun n'entre jamais
dans `geste_abandonne`**. L'alarme `travaux_en_erreur`, elle, est saturée (17 au lieu de 15 le
08/10) : un échec neuf s'y noie.

### ⚠ INCIDENT DE MA PART, SANS CONSÉQUENCE — *09/10, 15:16*

J'ai tapé `node Console/console_job_worker.js --help` pour lire ses options : **il n'y a pas
d'option `--help`, cette commande LANCE un worker**. Un **cinquième** processus a tourné
2 min 30 (PID 13008), en genre `actions`, avant que je l'arrête.

**Ce qu'il a fait : rien**, mesuré point par point —
```
0 travail reclame       0 ligne de app_console_job_log entre 13:14 et 13:26 UTC
0 travail modifie       0 travail « pending » dans toute la file
Hektor NON APPELE       storage_state_actions.json date de 15:02, AVANT le lancement
les 4 services intacts  verrous v9 retouches a 15:19, battement « idle » a 13:20 UTC
```
Il a créé son **propre** verrou (`console_worker_actions_manual.lock`, génération `manual`),
donc il n'a **pas** touché celui des services (`..._v9`). Il reste ce fichier de verrou avec un
PID mort : inoffensif *(le code remplace un verrou périmé tout seul)*, à retirer sur demande.

⚠ **La leçon, pour les prochaines fois : `console_job_worker.js` ne se lance JAMAIS pour
l'inspecter.** Pour lire ses options ou ses listes : `grep`. Pour éprouver une fonction :
un `Console/test_*.js` qui découpe le bloc et le fait tourner avec un faux Supabase.

*(Et une alerte que j'ai criée trop fort : mon écriture Python avait mis CLAUDE.md et la note en
CRLF. Le dépôt n'a jamais été touché — `core.autocrlf = true`, les blobs commités sont en LF ;
seule ma copie de travail l'était, et c'est réparé.)*

## ⑤ ✅ 4a EST CLOS — *09/10/2026*

```
moitie 2 (la surveillance)  patch applique, empreinte e2c015e1... conforme a la
                            repetition, 7 colonnes, 0 ligne, droits inchanges,
                            moniteur vert (data.geste_abandonne ok, 0 / seuil 0)
moitie 1 (l'avertissement)  les 4 workers REDEMARRES par Frederic a 17:30:49-51
                            (fichier modifie a 14:50:57 -> les quatre processus
                            sont posterieurs) + battement « startup » en base
                            a 15:30:49-51 UTC pour les quatre
```

**Aucun déploiement** : ni front, ni Render, ni Vercel. Rien n'a été poussé.

**Ce qui n'est PAS prouvé, et ne le sera pas** : l'avertissement n'a jamais été vu en réel. Il
faudrait un vrai échec de création, donc salir Hektor. Ce qui est prouvé : les vraies fonctions
du worker rendent le bon message (19/19 hors ligne), et les processus qui tournent portent bien
ce code (dates mesurées). **Le premier échec réel sera la preuve** — et il laissera deux traces :
la cloche du négociateur, et une ligne dans `app_en_attente_humain` que la sentinelle verra.


---

# POINT 4b — AUCUN NOUVEL ESSAI, ET CINQ MESSAGES QUI MENTAIENT

## ① AUDIT — *09/10/2026, lecture seule.* Verdict : **PARTIEL**

L'audit du 08/10 avait raison sur le fond, mais il mêlait **une décision juste** et
**cinq messages faux**.

### A. Ce qui est rejoué : 10 types, et le choix est le bon

`app_console_action_enqueue_due_retries`, relue en base — la liste complète :
```
archiver · desarchiver · supprimer l'annonce · supprimer le contact · changer le statut
affecter le negociateur · statut d'offre · annuler le compromis · supprimer la vente
supprimer le compromis  (ajoute le 17/09)
```
**Les dix sont des gestes d'état « absolus »** : les refaire donne le même résultat final.
Les créations, les dépôts et les gestes mandant en sont absents **à dessein** (C.4-bis du
29/08 : rejouer une création la **doublerait**).

**Et le filet marche quand il s'applique** : **19** travaux ont eu ≥ 2 tentatives, **tous
finis « réussi »** — dont 9 changements de statut (jusqu'à 4 tentatives, 13/09).

### B. Le message qui mentait : CONFIRMÉ — mais jamais lu par personne

Trois messages promettaient une reprise (`console_job_worker.js:2004`, `:2012`, `:2056`,
dans `cibleHektorContact`). Leurs **11 appelants** relevés : **un seul**
(`delete_hektor_contact`) est réellement rejouable → la promesse était fausse **10 fois
sur 11** (rattacher ou retirer un mandant, modifier un contact, ajouter une recherche,
modifier un mandant, la suite d'une création).

**Mesuré : 0 occurrence** — jamais dans `app_console_job.error_message`, jamais au journal,
jamais en notification. Défaut **latent**.

### C. Ce que l'audit n'avait pas vu — deux promesses de plus, et la structure de 4a

`:7821` (document) et `:8087` (photo) : *« gardé chez nous, envoi Hektor en échec — sera
repris »*, suivi de **« PAS DE LEVÉE »** → le travail finit **« réussi »**, donc **aucun
avertissement**. Exactement 4a, sur un autre objet.

Le repreneur **existe et est testé** (`Console/reprendre_envois_hektor.js`, il relit
`envoi_hektor_statut in (a_envoyer, echec)`) **mais il est orphelin** :
```
12 taches planifiees Windows listees le 09/10 -> AUCUNE ne l'appelle
deja ecrit le 25/09 : notice/RESTE_A_FAIRE_DOCUMENTS_PHOTOS_2026-09-25.md, point D3
   « existe et est teste -- aucun run ne l'appelle. A brancher »
```
Même motif que **4i** (`--missing-only` sans appelant) et que les archives du 09/10 :
*l'outil existe, il n'est branché nulle part.*
**Mesuré : 0 ligne** porte un statut d'envoi (ni « échec » ni « envoyé ») sur les deux
tables — le chemin n'a **jamais** servi, **rien n'est perdu**.

### D. Une bonne nouvelle : le piège du « pending à vie » est fermé

C'est le bug du 03/10 (`unlink_hektor_mandant` réclamé par personne, **sans erreur**).
Trois listes comparées :
```
42 types traites par le repartiteur du worker
42 types presents dans les 6 files JS
42 types distribues par app_console_claim_next_job (SQL, relue en base)
-> AUCUN ECART, dans les deux sens
```

### E. Une alerte à nuancer, et ce qui n'est pas mesuré

Trois créations portent jusqu'à **6 tentatives** — ce qui contredirait « jamais rejoué ».
Elles datent du **15-16/05**, les premiers jours du geste, bien avant C.4-bis : « TEST »,
aucun numéro retenu, 0 ou 1 finalisation → **aucune annonce n'a été doublée**. Aujourd'hui,
les **24** travaux en erreur de types non rejouables portent tous **1 seule** tentative.

**Non mesuré** : par quel chemin `refresh_console_data` (10/09) et `update_hektor_contact`
(24/06) ont atteint 2 tentatives sans être rejouables ; le comportement réel à l'écran.

## ② LE CORRECTIF — *« A » choisie par Frédéric le 09/10*

> **On ne touche à aucune logique. On arrête seulement de promettre.**

Les **5 messages** reprennent la formule **déjà employée** par le garde-fou des 30 minutes
(`app_console_claim_next_job`) : *« Relancer la demande si nécessaire »* — elle ne promet
rien et elle dit quoi faire. Les deux messages de dépôt disent
*« A REPRENDRE (le repreneur n'est pas branché) »*.
**27 lignes ajoutées, 5 retirées** — les 5 retirées sont exactement les 5 messages.

### Ce que ça pourrait casser ailleurs — vérifié

| Ce que ça touche | Vérifié | Preuve |
|---|---|---|
| le filet C.4-bis (cron 13) | **intact** : ni la liste SQL ni le cron ne sont touchés, et le worker ne recopie pas la liste | contrôle (4a) de l'épreuve |
| la cloche du négociateur | `notifyJobFailureBestEffort` recopie le motif dans le corps du message → **elle dira la vérité elle aussi**, c'est le but | l. 17244-17251 |
| les lecteurs de ces textes | **aucun** : `sera repris` n'existait que dans le worker et ses tests — aucun front, aucune fonction SQL, aucun script | grep complet |
| `delete_hektor_contact` *(le seul vraiment rejouable)* | la nouvelle phrase reste **vraie**, seulement prudente : le filet rejoue en plus, en silence | liste des 10 types |
| le front, les pages publiques | **rien**, aucune ligne, aucun déploiement | — |

### L'épreuve, hors ligne : **11 contrôles, 11 verts**
`node Console/test_aucune_fausse_promesse.js`. Il lit le source **et** fait tourner la vraie
`cibleHektorContact` avec un faux Supabase. ⭐ Son contrôle **(2c)** est un garde-fou pour
plus tard : **il tombera en échec le jour où le repreneur sera branché**, pour rappeler de
remettre le mot « repris » dans les deux messages de dépôt.

### Retour arrière
`git revert` du commit, puis redémarrage du worker. Aucun patch SQL, aucun déploiement.

## ③ CE QU'IL RESTE — *au 09/10*

1. **le redémarrage du worker** pour que les nouveaux messages sortent *(les 5 messages
   touchent les files `actions` et `documents` — donc **deux** services au minimum)* ;
2. ⏳ **B et C sont REPORTÉS — décision de Frédéric du 09/10** (« on ne fait pas b et c et on
   passe a 4c »). **Reportés, pas abandonnés** :
   **B** brancher `reprendre_envois_hektor.js` — il reste **orphelin**, donc un envoi de document
   ou de photo en échec **n'est repris par personne**. Risque aujourd'hui **nul** (0 ligne porte un
   statut d'envoi), réel le jour où les négociateurs déposeront des pièces depuis l'app. Il faudra
   décider **où** (run de nuit ou tâche Windows) et **à quelle fréquence**.
   **C** prévenir le négociateur quand un envoi échoue — à ne faire **qu'après B** (sinon on
   avertit sans pouvoir réparer).
   ⭐ Le message du worker **dit désormais la vérité** (« A REPRENDRE »), et le contrôle **(2c)** de
   l'épreuve **tombera en échec** dès qu'on branchera le repreneur : le report est **gardé par le
   code**, il ne peut pas se perdre.

---

# POINT 4c — UNE CRÉATION EN ÉCHEC NE SE VOYAIT NULLE PART

## ① AUDIT — *11/10/2026, lecture seule.* Verdict : **CONFIRMÉ**

### Le mécanisme

La création d'une annonce passe par `app_create_annonce_job_optimistic`, qui a **deux branches**,
pilotées par l'interrupteur `c9_annonce_nait_dans_app` :

```
ETEINT  -> une ligne provisoire dans app_annonce_provisional + le travail.
           L'ecran lit cette ligne et sait afficher « En creation... »
           puis « Erreur de creation ».
ALLUME  -> l'annonce nait DIRECTEMENT dans app_dossier_current, avec un numero
           a nous, et AUCUNE ligne provisoire.
```

**L'interrupteur est ALLUMÉ depuis le 25/09 à 06:15** (relevé en base). Donc quatre conséquences,
toutes vérifiées :

1. `app_annonce_provisional` **n'est plus jamais remplie** — **0 ligne** *(et déjà 0 le 31/08, un
   commentaire du front le disait)*. Le marqueur du front est correct… et **ne peut plus jamais
   s'allumer**.
2. `markProvisionalCreationError` du worker **ne fait plus rien** : il modifie cette table par
   jeton → **0 ligne touchée**, et comme l'appel est en « best effort », **l'échec de l'échec est
   avalé en silence**.
3. **Le filet des 15 minutes est hors-jeu** : `app_sweep_stale_provisionals` transforme une
   provisoire qui traîne en **erreur visible** au bout de 15 min — il n'a plus rien à surveiller.
4. Une création en échec laisse **une ligne de dossier d'apparence normale**, et **rien ne la
   nettoie** : le balayage ne fait que *lire* `app_dossier_current`.

### Les mesures

```
app_annonce_provisional                          0 ligne
la sequence des numeros de l'app : tiree UNE fois -> dossier 10 000 000,
   « ESSAI C9 bis - ne pas diffuser » (Tence), qui a REUSSI (Hektor 63147)
dossiers sans numero Hektor                      0
dossiers titres « Annonce en creation »          0
derniere creation par ce chemin                  24/09
```

**Structure cassée, zéro occurrence** — troisième fois dans ce chantier : le geste de création ne
sert quasiment pas encore.

### Deux points de l'audit du 08/10 à corriger

- « **la fiche saisie ne vit que dans la charge du travail** » → **plus vrai depuis le 25/09** :
  elle vit dans une vraie ligne durable. *(La purge du 21/08 et ses 19 créations datent de
  l'ancienne branche ; non re-mesurées.)*
- « **sans marque d'erreur** » → vrai **pour la ligne dans la liste**, mais **le négociateur est
  averti** : quand le travail tombe en erreur, un message part dans sa cloche *(mécanisme du
  20/08)*. Ce n'est pas un silence total — c'est **l'écran** qui ne dit rien, et **personne ne
  compte** les orphelines.

### ⭐ L'audit approfondi, demandé par Frédéric — cinq trouvailles qui ont changé le correctif

**1. La question de Frédéric a invalidé ma première proposition.** Il a demandé : *« à la
création, il faut forcément attendre au moins une minute le numéro Hektor ; est-ce que ça risque
de faire sonner le garde-fou ? »* Mesuré sur les 79 créations réelles :

```
le travail lui-meme     28,2 s mini · 52,7 s median · 63,8 s au pire
l'attente dans la file   3,4 s median · 2 646 s AU PIRE  =  44 MINUTES
bout en bout            59,7 s median · 2 669 s AU PIRE  =  44 min 29 s
```

→ **tout délai (5, 15 ou 30 min) aurait sonné faussement** au moins une fois dans l'histoire
réelle. J'avais écrit « ou plus vieux que 30 min » : **retiré**. On tranche sur **l'état du
travail**, jamais sur l'horloge.

**2. La jointure que je croyais avoir n'existe pas.** La colonne `app_console_job.app_dossier_id`
est **vide sur les 79 créations** (0/79). Le numéro n'est que dans la **charge**, où il est **par
construction** dans la branche allumée. Et `source_hash` (`c9e3:<jeton>`) est inutilisable : **la
synchro le réécrit** dès que tout va bien.

**3. La plage tient** : le plus grand numéro venu de Hektor est **7 589 248**, un seul dossier est
au-dessus de 10 M. Marge 2,4 M — *à surveiller, elle se mange avec le temps.*

**4. La ligne est bien VISIBLE à l'écran** : la vue de la liste **n'exige pas** de numéro Hektor
(13 475 lignes = toute la table). La saisie n'est donc pas perdue de vue ; il ne manque que la
marque. **Moins grave que l'audit ne le laissait croire.**

**5. ⭐ L'ŒIL EXISTAIT DÉJÀ, ET IL REFUSAIT DE JUGER — EXPRÈS.**
`phase2/checks/annonce_un_numero.py` (C.9-b, 24/09) **comptait déjà exactement cette population**,
sous `en_attente`. Il est **déjà lu par le moniteur**, qui importe **la formule elle-même**
(`a1n.mesurer`), et a **déjà** sa clé d'alerte à seuil 0. Son auteur l'avait rangé dans « ce qui
n'est pas grave » **parce que rien ne permettait alors de distinguer une attente normale d'un
échec**. C'est exactement ce qui manquait — et ce que la question de Frédéric a fait trouver.

**Et le miroir local porte `app_console_job`** (91 609 lignes, toutes les colonnes utiles) → la
coupure est calculable en local, sans toucher à la production.

## ② LE CORRECTIF — *« A1 » choisie par Frédéric le 11/10*

> **On n'ajoute pas une sentinelle. On apprend à juger à celle qui existe.**

`en_attente` est coupé en deux, **dans la formule unique** :

```
en_attente        >= 10 M, inconnue du serveur, ET AUCUN travail de creation en
                  erreur  ->  NORMAL, ne sonne jamais, meme apres 44 minutes
creation_echouee  >= 10 M, inconnue du serveur, ET le travail de creation est en
                  ERREUR  ->  GRAVE (ajoute a GRAVES, seuil 0)
```

**Zéro fausse alerte par construction** : aucun délai nulle part, donc aucune fenêtre où se
tromper. **Et le moniteur n'a pas une ligne à changer** : il importe la formule et passe au rouge
dès que le total des graves dépasse 0.

**Le prix de cette sûreté** : l'alerte peut arriver ~30-40 min après le fait *(le temps que le
travail soit déclaré en erreur : levée immédiate, ou minuteur de 10 min du worker, ou garde-fou
des 30 min de `app_console_claim_next_job`)*, puis à la prochaine descente. **Le négociateur, lui,
est averti sur le moment.**

**Si la doublure des travaux manque**, on **ne rend pas un zéro** — un zéro dirait « rien n'a
échoué » : `creation_echouee` vaut `None`, `creation_echouee_mesurable` vaut `false`, la ligne de
commande dit « NON MESURABLE » et rend le code **2**.

### Ce que ça pourrait casser ailleurs — vérifié

| Ce que ça touche | Vérifié | Preuve |
|---|---|---|
| **le moniteur** | **pas une ligne** : il importe `a1n.mesurer` et lit `graves`, `supabase`, `en_attente` — les trois sont là. Le détail part en JSON avec les 2 clés neuves | simulation du 11/10 : verdict « ok », JSON sérialisable |
| les **2 autres fichiers** qui nomment la sentinelle | **de simples commentaires** : ni `apres_run_2026-10-01.py` ni `push_single_annonce_to_supabase.py` n'importent la formule | grep |
| **le run de nuit** | **aucun `.ps1` n'appelle cette sentinelle** → impossible de faire échouer le run | grep |
| **le compte `en_attente`** | il se rétrécit *(il exclut les échecs)* : le message du moniteur le nomme, son sens est précisé dans la docstring. **La somme des deux est celle d'avant** | épreuve (8c) |
| **son test** | **étendu, pas réécrit** : les 11 contrôles d'avant passent toujours | 21/21 |
| **la base, le front, Hektor, les pages publiques** | **rien** : fichier de lecture seule, aucune écriture nulle part | — |

### L'épreuve — **21 contrôles, 21 verts** *(11 d'avant + 8 neufs + les 2 sur la vraie base)*

`python phase2/checks/test_c9b_annonce_un_numero.py`, sur le patron du 24/09 (éprouver **dans les
deux sens**). Les neufs :

```
(8a) travail pending / running / done  -> ON SE TAIT  (le CAS PIEGE de Frederic)
(8b) travail error                     -> COMPTEE, et GRAVE
(8c) la somme est conservee : 1 echouee + 2 en attente = 3 nees dans l'app
(8d) un autre genre de travail, ou un autre dossier -> ne fait pas crier
(8e) en TEXTE aussi, la creation echouee est comptee
(8f) sans app_console_job -> « non mesurable », PAS un zero
```

Et sur la **vraie base**, en lecture seule : 0 partout, **0,18 s**.

### Retour arrière
`git revert` du commit. **Aucune écriture nulle part**, aucun patch SQL, aucun déploiement, aucun
redémarrage.

## ③ CE QU'IL RESTE — *au 11/10*

1. ⏳ **A2 n'est pas faite** *(et n'a pas été demandée)* : une 3ᵉ branche dans la vue de 4a
   donnerait la même alerte **en direct** (minutes au lieu de ~24 h). À reprendre si le délai gêne
   un jour.
2. ⏳ **B n'est pas faite** : remettre la marque « Erreur de création » **sur la ligne à l'écran** —
   demande une modification du front, donc **un déploiement**. La vue porte déjà une colonne
   `alerte_principale` qui pourrait servir de véhicule.
3. ⏳ **Un 3ᵉ compteur en question** : un dossier né dans l'app **sans aucun travail de création**
   *(travail purgé des mois plus tard)*. Il faut d'abord mesurer **quelle date le miroir porte** sur
   ces lignes pour ne sonner qu'au-delà de 24 h.
4. ⏳ **Le périmètre** : le même schéma à deux branches existe pour le **contact**, la **recherche**
   et le **lien**. À mesurer — c'est la matière de **4d**, pas élargie sans Frédéric.
5. `markProvisionalCreationError` **n'est pas touché** : il reste juste si l'interrupteur repasse à
   l'arrêt. ⚠ **À annoter** pour que personne ne le croie actif.

---

# POINT 4d — UNE RECHERCHE CRÉÉE EN ÉCHEC S'EFFAÇAIT AU BOUT DE 24 H

## ① AUDIT — *11/10/2026, lecture seule.* Verdict : **PARTIEL**

Les faits de l'audit du 08/10 sont exacts, mais il appelle « défaut » **une décision écrite et
raisonnée**, et il manque le point le plus important : **rien n'est physiquement perdu**.

### Ce qui se passe vraiment

**1. La table provisoire de la recherche est vide — et c'est SAIN.** ⚠ Piège : vide ne veut pas
dire jamais remplie. Le balayage efface la ligne **dès que la vraie recherche arrive**. Mesuré :
**2 créations optimistes** (31/08 et 17/09), **toutes deux réussies**. C'est donc **l'inverse du
cas de l'annonce** (4c), où la table n'est **plus jamais** remplie.

**2. Aucune création de recherche n'a JAMAIS échoué** : 4 travaux `add_hektor_contact_search`,
**tous « réussis »**, 1 seule tentative, du 12/06 au 17/09. **0 cas réel.**

**3. La chaîne en cas d'échec** (cron **jobid 9**, **chaque minute**, actif) :

```
la ligne traine « en cours » plus de 15 min  ->  elle devient une ERREUR VISIBLE
la ligne est en « erreur » depuis 24 h       ->  elle est EFFACEE  (branche c)
une ligne encore « en cours »                ->  JAMAIS effacee (ecrit en clair)
```

**4. Aucun nouvel essai** : ce type est absent des 10 types rejouables — et c'est **juste**,
rejouer une création **doublerait** la recherche *(trouvaille de 4b)*.

**5. Aucun bouton « réessayer »** dans le front.

**6. ⭐ La saisie n'est pas détruite.** Les critères vivent **en entier** dans la charge du travail
(`payload_json->search` : budget, pièces, DPE, équipements, communes…), et les travaux **ne sont
jamais purgés** (91 609 conservés). Après 24 h la saisie devient **invisible**, pas **perdue**.

**7. C'est une décision, pas une négligence.** Le patch du **25/09** est né d'une question de
Frédéric, et ses règles sont argumentées par écrit. La purge des erreurs à 24 h est la branche
(c), justifiée ainsi : *« les erreurs anciennes : l'utilisateur a eu le temps de les voir »*. Et
la règle C.1' a retiré la purge des `*_pending` **en gardant** celle des `*_provisional`.

**Le seul vrai reproche** : cette prémisse est **fausse** si le négociateur est absent deux jours.
Et **personne ne compte** ces échecs.

### ⭐ Une trouvaille au passage : le 15 minutes est trop court pour UN objet

Le balayage déclare « erreur » au bout de **15 minutes** d'après `created_at`. J'ai mesuré le bout
en bout réel de chaque geste, file d'attente comprise :

```
add_hektor_contact_search        32 s au pire     -> 28 fois de marge, aucun risque
create_hektor_contact            46 s au pire     -> large
link_hektor_mandant              39 s au pire     -> large
create_hektor_mandant_contact   452 s = 7 min 32  -> marge 2x seulement
create_hektor_draft_annonce    2 669 s = 44 min   -> AU-DELA DES 15 MINUTES
```

⚠ **Pour l'annonce, le balayage pourrait donc marquer « Erreur de création » sur une création
parfaitement en vol.** Ça ne peut pas arriver aujourd'hui *(sa table provisoire n'est plus
remplie — c'est 4c)*, **mais ça redeviendrait vrai si l'interrupteur `c9_annonce_nait_dans_app`
repassait à l'arrêt.** Noté, non corrigé, **hors périmètre de 4d**.

## ② LE CORRECTIF — *« A et b » choisis par Frédéric le 11/10*

**A. ON COMPTE** — une **3ᵉ branche** dans `app_en_attente_humain` : les recherches dont le travail
de création est **en erreur**. La sentinelle `geste_abandonne` (seuil 0) sonne **seule**. La
coupure est **l'état du travail, jamais l'horloge** *(règle de 4c)*. Et comme la charge du travail
garde les critères, **l'alerte les redonne** : `contact 605030 -> recherche 120000 a 250000 EUR` —
le négociateur n'a pas à les retrouver de mémoire.

**B. ON LAISSE PLUS DE TEMPS** — la purge des **erreurs** passe de **24 h à 7 jours**, ce qui
couvre un week-end et une absence courte.

> ⚠ **PÉRIMÈTRE DE B, signalé à Frédéric avant le collage** : la branche (c) traite les **quatre**
> tables provisoires d'un seul geste (annonce, contact, recherche, lien) et sa justification est
> **la même pour les quatre**. Les quatre passent donc à 7 jours. Si Frédéric ne veut **que** la
> recherche, c'est **une ligne à retirer**. Volume en jeu : **aucun** (0 ligne `error` aujourd'hui
> sur les 4 tables).

### Ce que ça pourrait casser ailleurs — vérifié

| Ce que ça touche | Vérifié | Preuve |
|---|---|---|
| **les 7 colonnes** de la vue, leur ordre, leurs types | inchangés → le `sample` du moniteur lit pareil | contrôle de sortie du patch |
| **les branches 1 et 2** de la vue | **recopiées au caractère près**, aucune condition touchée | la répétition est **assemblée depuis le vrai fichier** |
| **le 15 minutes** qui rend l'erreur visible | **pas touché** — et pour la recherche il a **28 fois** de marge | mesure ci-dessus |
| **les purges `linked` à 24 h** | **pas touchées** : le contrôle de sortie exige **4 fois 24 h, 4 fois 15 min, 4 fois 7 jours** — impossible de se tromper de branche | contrôle de sortie |
| **le cron jobid 9** | pas touché, il appelle la même fonction | — |
| **le chantier ①** | `create or replace` conserve l'ACL de la vue **et** de la fonction ; jamais de `drop` | `relacl` relu, contrôle de sortie |
| **le bruit de la sentinelle** | **0 travail de recherche en erreur depuis toujours** → elle reste **verte** | mesure |
| **la décision du 25/09** | **amendée explicitement**, pas écrasée : l'ancienne phrase et la raison du changement sont écrites dans le code | commentaire (c) |
| **le front, le worker, le run, phase2, les pages publiques** | **rien** : un seul lecteur de la vue, `monitoring/check_gti_health.py` | grep |

### L'épreuve, avant la production
- La **branche 3 éprouvée seule, en lecture** : avec `status='done'` *(le contournement que la
  répétition utilise pour prouver la plomberie)* elle rend **4 lignes** correctes, critères
  compris, y compris le cas où `priceMin` manque (`recherche ? a 123456 EUR`).
- La **répétition est ASSEMBLÉE depuis les deux vrais fichiers** par un générateur
  *(`scratchpad/faire_repetition_4d.py`)*, et non recopiée : elle joue donc, au caractère près,
  ce qui sera collé. Structure vérifiée : 1 `BEGIN`, **0 `COMMIT`**, 1 `ROLLBACK`, 20 mesures,
  1 erreur volontaire.

### Retour arrière
`..._INVERSE.sql` remet **les deux** objets dans leur état du 11/10 — empreintes attendues
`e2c015e16d1339fee080b6b2cc7bcb2b` (vue) et `8031dd042d33e3785a27da0c4e106498` (balayage), toutes
deux contrôlées par le script lui-même.

## ③ CE QU'IL RESTE

1. Frédéric colle **la répétition** → il me recopie le message `ESSAI ANNULE -- 4d`, je compare
   aux valeurs attendues (écrites en tête du fichier).
2. Si c'est le bon : il colle **le vrai patch**, et je contrôle en base.
3. ⏳ **Le 15 minutes trop court pour l'annonce** (marge négative) et **pour le mandant**
   (marge 2×) : noté ci-dessus, **non corrigé**, à décider — ce n'est pas 4d.
4. ⏳ **Le bouton « réessayer »** (option C, écartée le 11/10) : il demande d'abord de **demander à
   l'API de Hektor si la recherche existe déjà**, sinon on la double. Patron connu : celui du
   mandant, 31/08.
