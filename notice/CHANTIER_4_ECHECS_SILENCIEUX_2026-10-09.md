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
| **4b** | **aucun nouvel essai** pour 6 familles de travaux, et le worker écrit quand même « Le travail sera repris » | 🧪 **audit fait (PARTIEL)** · ✅ **FINI** : option A codée le 09/10 (11/11 hors ligne), **4 workers redémarrés le 11/10 à 15:37** → les 5 messages ne promettent plus rien · **B et C reportés** par Frédéric |
| **4c** | « Annonce en création » en échec **sans marque d'erreur** (le marqueur lit une table plus remplie) | 🧪 **audit fait (CONFIRMÉ)** · **A1 codée le 11/10**, épreuve **21/21** : la sentinelle qui existait déjà sait enfin juger · aucune écriture, aucun déploiement |
| **4d** | une **recherche créée en échec** disparaît au bout de 24 h, sans bouton « réessayer » | ✅ **FINI le 11/10 (A et B)** : patch appliqué et contrôlé — empreintes `8ae7e3ab…` (vue) et `6a9c2efe…` (balayage) conformes à la répétition, 7 colonnes, 0 ligne, droits intacts, **4×7 jours / 4×24 h / 4×15 min**, cron 9 actif |
| **4e** | les **photos de la création** attendent dans la mémoire du navigateur | 🧪 **audit fait — BEAUCOUP plus petit qu'annoncé** *(fermer la modale ne perd rien)* · **« informer » codé le 11/10** : compte dans la vignette + avertissement avant fermeture/rechargement + confirmation modale · build vert, app démarrée sans erreur · ⏳ **attend un déploiement** |
| **4f** | l'alarme « travaux en erreur » figée au rouge ; gestes mandant et transaction jamais dans `geste_abandonne` ; 4 types de transaction non notifiés | ✅ **CLOS le 11/10 SANS CORRECTIF** *(décision de Frédéric)* — l'alarme n'était **pas cassée** : seuil 0 **voulu**, et l'humain a tranché **deux fois** en écrivant pourquoi (01/10, 11/10) · **0 geste de transaction n'a jamais échoué** · **rien n'est perdu**, seulement du bruit |
| **4g** | *(reste de ⑤ : 5f)* l'**abandon réel** ne rend pas l'état | 🔎 **audité le 11/10, NOTÉ NON FAIT** *(décision de Frédéric)* — **auto-réparant** : le registre des affaires est refait chaque nuit depuis Hektor (31 040/31 058 aujourd'hui), donc ≤ 24 h · jamais déclenché par le filet (max **4** tentatives), **2 fois à la main** en 5 mois sur un bien d'essai · ⚠ **et « rendre l'état d'avant » serait DEVINER** : le bon geste est **relire chez Hektor** |
| **4h** | *(reste de ⑤ : 5h B/C)* **marqueur à l'écran** et **bouton « réessayer »** pour un mandant créé en échec | 🔎 **audité le 11/10, NOTÉ NON FAIT** *(décision de Frédéric)* — le scénario n'est **jamais arrivé** (17 créations de mandant, **0 en erreur** ; **0 contact sans numéro Hektor** sur 62 189) et la **sentinelle de l'option A alerte le jour même** · **B** la pastille = ~10 lignes, un **confort** · ⛔ **C le bouton « réessayer » : NON**, il **doublerait le contact** chez Hektor |
| **4i** | `--missing-only`, passé **chaque soir par le run**, est **sans appelant depuis le 21/07** : l'option ne fait rien, et personne ne le dit | ✅ **MARQUÉ le 11/10** *(choix de Frédéric : marquer, pas supprimer)* — **+36 lignes de commentaires, 1 ligne d'aide**, et **zéro changement de comportement** : l'option reste passée, mais `--help` dit désormais « SANS EFFET depuis le 21/07/2026 » |

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

### La répétition — *jouée par Frédéric le 11/10, EXACTE sur les 18 mesures*

```
vue_empreinte_avant=e2c015e16d1339fee080b6b2cc7bcb2b
balayage_empreinte_avant=8031dd042d33e3785a27da0c4e106498
vue_lignes_avant=0   colonnes_avant=7
acl_avant={postgres=arwdDxtm/postgres,service_role=arwdDxtm/postgres}   <- ni anon ni authenticated
vue_empreinte_apres=8ae7e3abdf139acf519027762539ce58        <- NOUVELLE REFERENCE
balayage_empreinte_apres=6a9c2efeac87f68a25c5462451083828   <- NOUVELLE REFERENCE
vue_lignes_apres=0  branche3_apres=0  colonnes_apres=7  acl_apres=IDENTIQUE
erreurs_a_7_jours=4   linked_a_24h=4   visible_a_15min=4
   ^ B n'a change QUE la branche voulue : les purges « linked » et le delai des
     15 minutes n'ont PAS bouge
branche3_sans_fenetre=0        <- normal : aucune recherche n'a jamais echoue
plomberie_si_erreur=4          <- LA PREUVE : la branche trouve, extrait et affiche
exemple=contact 605075 -> recherche 120000 a 250000 EUR
vue_empreinte_retour=e2c015e16d1339fee080b6b2cc7bcb2b        <- identique a « avant »
balayage_empreinte_retour=8031dd042d33e3785a27da0c4e106498   <- identique a « avant »
acl_retour=IDENTIQUE
```

Erreur finale `P0001 ESSAI ANNULE` : **rien n'a été écrit**. Le retour arrière rend **les deux**
objets au caractère près. Les **deux empreintes d'après** ont été inscrites dans le patch comme
**contrôles de sortie** : un patch qui ne les donnerait pas refuse de s'enregistrer.


### ✅ 4d EST CLOS — *patch appliqué par Frédéric le 11/10, contrôlé en base*

| Contrôlé | Attendu | Mesuré |
|---|---|---|
| empreinte de la **vue** | `8ae7e3abdf139acf519027762539ce58` | **identique à la répétition** ✅ |
| empreinte du **balayage** | `6a9c2efeac87f68a25c5462451083828` | **identique à la répétition** ✅ |
| 7 colonnes, dans l'ordre | `objet, reference, libelle, nature, cause, tentatives, depuis` | identique ✅ |
| lignes de la vue | 0 *(dont branche 3 : 0)* | **0** ✅ |
| droits *(chantier ①)* | `postgres` + `service_role` | identique ✅ |
| les trois délais | **4× 7 jours**, 4× 24 h, 4× 15 min | **4 / 4 / 4** ✅ |
| le cron du balayage | jobid 9 actif | **actif** ✅ |

**Le moniteur, passé en lecture seule après le patch** *(`--no-alerts --dry-run`, 70 contrôles)* :
```
data.geste_abandonne   ok   « Gestes abandonnes en attente d'un humain: 0 (seuil 0) »
```
→ il lit toujours la vue à travers l'API avec la clé de service : le patch n'a cassé ni l'accès
ni la lecture. ⭐ Et l'état général s'est **beaucoup amélioré** depuis le 09/10 : **0 critique**
au lieu de 4 *(la tâche « GTI Descente », `travaux_en_erreur`, `mandat_disparu` et
`ecart_statut_regle` ne crient plus)*. Restent **5 avertissements**, tous antérieurs et aucun de
4d : `recherche_disparue` 6 · `ecart_statut_regle` 6 (seuil 4) · `notif_orphelines` 154 ·
`notif_non_lues` **1 551** *(1 527 le 09/10 : +24 — c'est la famille de 4f, une alarme saturée)* ·
`orphelins_recherche` 11.

**Ce que le contrôle ne prouve pas** : la branche rend 0 ligne, et c'est normal — **aucune
création de recherche n'a jamais échoué**. La preuve qu'elle trouve reste `plomberie_si_erreur = 4`
de la répétition. Aucun faux échec n'a été fabriqué en production.

## ③ CE QU'IL RESTE

1. Frédéric colle **la répétition** → il me recopie le message `ESSAI ANNULE -- 4d`, je compare
   aux valeurs attendues (écrites en tête du fichier).
2. Si c'est le bon : il colle **le vrai patch**, et je contrôle en base.
3. ⏳ **Le 15 minutes trop court pour l'annonce** (marge négative) et **pour le mandant**
   (marge 2×) : noté ci-dessus, **non corrigé**, à décider — ce n'est pas 4d.
4. ⏳ **Le bouton « réessayer »** (option C, écartée le 11/10) : il demande d'abord de **demander à
   l'API de Hektor si la recherche existe déjà**, sinon on la double. Patron connu : celui du
   mandant, 31/08.

---

# POINT 4e — LES PHOTOS DE LA CRÉATION DANS LA MÉMOIRE DU NAVIGATEUR

## ① AUDIT — *11/10/2026, lecture seule.* Verdict : **CONFIRMÉ, mais BEAUCOUP plus petit que l'audit ne le disait**

### Où vivent les photos — deux moments, deux comportements

```
AVANT de valider la creation   ->  memoire de la MODALE
                                   fermer la modale = efface (volontaire)
APRES avoir valide             ->  memoire de L'APPLICATION, rangee sous le
                                   numero du travail de creation
                                   fermer la modale = AUCUN EFFET
```

Et la modale **refuse même de se fermer** pendant l'envoi (`closeDraftAnnonceModal` :
`if (draftAnnoncePending || draftAnnonceScanPending) return`).

### Ce qui ne perd RIEN — *question de Frédéric du 11/10, et il avait raison*

```
fermer la modale · changer d'ecran, de filtre, de bien · ouvrir une autre annonce
laisser l'onglet ouvert 10 minutes          ->  AUCUN RISQUE
```

**Ce qui perd, et c'est tout** : fermer l'onglet · recharger la page (F5) · un plantage ·
partir sur un autre site. Ces quatre cas détruisent la mémoire de **l'application**.

### ⚠ ET J'AI DÛ CORRIGER MON PROPRE ALARMISME

J'avais écrit « la création dure jusqu'à 44 minutes ». **Faux comme généralité** — et c'est
Frédéric qui m'a reprise (« je crois que le worker est immédiat »). Mesure complète :

```
le worker interroge la file toutes les 5 SECONDES (reglage lu dans le code)
attente dans la file, sur les 79 creations :
   63 sur 79  ->  moins de 10 s        <- « immediat », il avait raison
    5 sur 79  ->  entre 10 et 60 s
   11 sur 79  ->  PLUS d'une minute (14 %)
   mediane 3,4 s · p95 190 s · maximum 2 646 s (un seul cas, le 15/05)
bout en bout : 66 sur 79 finissent en moins de 2 min · p95 353 s
```

⭐ Et **deux** des 11 cas longs ont une **explication structurelle** que je n'avais pas vue :
le **07/06, deux fois**, deux créations lancées **dans la même minute** — la seconde a attendu
la première (65 s, puis 146 s), parce qu'il n'y a **qu'un seul worker « actions »** et que les
travaux passent **un par un**. Ça se reproduira dès que deux négociateurs créeront en même temps.

**Ce que ça change** : pour **4c et 4d**, la règle « on tranche sur l'état du travail, jamais sur
l'horloge » **reste juste et mieux fondée** *(un délai de 5 ou 15 min aurait crié 11 fois sur 79)*.
Pour **4e**, le risque est **réel mais petit** : fermer ou recharger pendant la minute d'attente.

### Le précédent qui éclaire tout — *cinq lignes plus bas dans la même fonction*

Le scan d'estimation, lui, reçoit un **dépôt durable** :

> *« Dépôt DURABLE immédiat : survit à un refresh. La file en mémoire est ré-hydratée depuis ces
> clés au démarrage. »*

**Le geste existe déjà pour un objet voisin.** Pas pour les photos — parce que le scan est du
**texte** (il entre dans la mémoire persistante) et une photo un **fichier binaire** (il n'y entre
pas). Ce n'est donc **pas un oubli, c'est une limite technique**.

### Ce qui informe déjà, et ce qui ne dit rien

- **Si la création échoue**, l'écran **prévient déjà** : *« Les photos n'ont pas été envoyées car
  la création de l'annonce Hektor a échoué. »* — mais les photos sont jetées.
- **L'onglet fermé ne disait rien** : aucun `beforeunload` dans tout le front.
- **La perte est rattrapable à la main** : le négociateur peut rajouter les photos sur la fiche
  — s'il s'en aperçoit.
- **Le chemin fonctionne** : **14 travaux photo sur 16** viennent de là, tous réussis.

**Ce que je ne peux pas mesurer, et je le dis** : une photo qui n'a jamais atteint le cloud **ne
laisse aucune trace**. Je mesure la fenêtre et l'absence de filet, **pas le nombre de pertes**.

---

## ⭐ LA DEMANDE DE FRÉDÉRIC : PLUSIEURS PHOTOS À LA FOIS

### Ce qui existe déjà

**À la création, le multiple EST là** : le champ accepte plusieurs fichiers d'un coup, **jusqu'à
20 photos**, avec tri des formats et messages pour ce qui est refusé.
**Ce qui manque, c'est sur la fiche annonce** : un seul fichier à la fois (`files[0]`).

### Mais derrière, elles partent une par une

```
1 photo = 1 travail = 1 session de navigateur ouverte sur la console Hektor
duree mesuree : 15 s mini · 21,4 s en general · 56,5 s au pire
-> 20 photos = ~7 MINUTES de worker et 20 ouvertures de la console
et elles font la queue derriere le rattrapage des documents :
   attente mesuree pour un travail photo : jusqu'a 857 s = 14 MINUTES
```

### ⭐ HEKTOR ACCEPTE LE MULTIPLE — *et je l'ai su SANS l'appeler*

Frédéric avait donné son accord pour ouvrir la page photos d'un bien d'essai. **Ça n'a pas été
nécessaire** : nous avons **11 captures de la vraie page** (`.tmp/annonce_groups_*/photos_lecture.html`).

```html
<input id="fileupload" type="file" name="files[]"
       accept="image/gif, image/jpg, image/jpeg, image/png, image/x-png" multiple/>
<input id="fileuploadHidden" type="file" name="files[]" ... multiple/>
```

**Les DEUX champs portent `multiple`, et `name="files[]"` est un tableau** : l'interface de Hektor
est bâtie pour recevoir plusieurs fichiers en une fois. Et notre outil sait les envoyer
(`setInputFiles` accepte une liste). **Aucun appel à Hektor n'a été fait.**

**Deux réserves, à ne pas oublier avant de coder l'envoi groupé :**
1. ⚠ **La confirmation devra compter N, pas 1.** Aujourd'hui elle exige « au moins une photo de
   plus dans la galerie ». Avec N fichiers il faut exiger **N de plus** — sinon un envoi partiel
   passerait pour réussi : **exactement le défaut 4a, sur un autre objet.**
2. ⚠ **L'`accept` de Hektor ne liste PAS le WebP** (gif, jpg, jpeg, png, x-png), alors que notre
   app ET notre worker l'acceptent. **Mesuré : aucun WebP n'a jamais été envoyé** (11 PNG,
   5 JPEG). `accept` ne filtre que le sélecteur de fichiers du navigateur, pas le serveur — donc
   **on ne sait pas** ce que Hektor ferait d'un WebP. **Non mesuré, non corrigé.**

---

## ② LE CORRECTIF — *« informer », choisi par Frédéric le 11/10*

> **On ne change rien au mécanisme — il est bon. On ajoute la parole.**

Trois ajouts, **84 lignes ajoutées, 0 supprimée** dans `App.tsx` + **10 lignes** de style :

1. **Le compte dans la vignette de suivi** *(celle qui existe déjà)* : *« 3 photos partiront dès
   que Hektor aura rendu le numéro — ne fermez pas et ne rechargez pas cet onglet. »* Un
   paramètre neuf et facultatif (`photosEnAttente`), passé aux **deux** endroits qui affichent la
   vignette.
2. **L'avertissement du navigateur** (`beforeunload`), qui couvre **la fermeture ET le
   rechargement** — c'est le même événement. ⚠ **Conditionné à « des photos attendent
   vraiment »** : un avertissement qui sort tout le temps est un avertissement qu'on n'écoute plus.
3. **Une confirmation avant de vider la modale** quand des photos y sont choisies — le seul
   reproche du premier moment : jusqu'ici un clic suffisait à perdre 20 photos sélectionnées,
   sans un mot.

### Ce que ça pourrait casser ailleurs — vérifié
| Ce que ça touche | Vérifié |
|---|---|
| le mécanisme d'envoi des photos | **pas une ligne** : ni la file, ni l'effet qui envoie, ni le worker |
| la vignette de suivi | paramètre **facultatif** → les deux appels le passent, et un appelant qui l'oublierait afficherait simplement 0 |
| la fermeture normale de la modale | la confirmation ne sort **que** s'il y a des photos choisies ; sinon fermeture immédiate — **essayé en réel en mode local** |
| l'avertissement du navigateur | enregistré **seulement** quand des photos attendent, et retiré dès qu'elles partent |
| le reste du front | **0 suppression**, build vert, app démarrée en mode local **sans une erreur** |

### L'épreuve
- `npm run build` **vert** *(la règle du projet)* ;
- app **démarrée en mode local** et lue : l'accueil s'affiche, **aucune erreur de console** ;
  la modale de création s'ouvre et **se ferme normalement** (pas de confirmation, 0 photo).
  *(La seule erreur vue, un 500 sur `/api/hektor-diffusion/broadcasts`, est l'API de diffusion
  absente en mode local — sans rapport.)*
- ⚠ **Ce qui n'est PAS prouvé** : le bandeau et l'avertissement **n'ont pas été vus**. Il faudrait
  joindre un vrai fichier et lancer une vraie création, donc **écrire chez Hektor**. À faire sur
  un bien d'essai, avec l'accord de Frédéric — ou par lui, après déploiement.

### Retour arrière
`git revert` du commit. Aucune écriture, aucun patch SQL, aucun redémarrage.

### ✅ 4e-bis — *PLUSIEURS PHOTOS SUR LA FICHE ANNONCE, codé le 11/10*

Frédéric : « **fais 2** ». Le formulaire de la fiche annonce ne prenait qu'**un** fichier
(`files[0]`) ; il accepte maintenant **plusieurs photos**, **jusqu'à 20**, avec **le même tri que
la création** (mêmes formats, même plafond, mêmes messages) — pour que les deux écrans refusent
la même chose.

⚠ **UN TRAVAIL PAR PHOTO, comme aujourd'hui** : le worker et sa preuve de réussite ne sont
**pas touchés**. Et le bilan **dit la vérité** : on ne s'arrête pas au premier échec, chaque photo
est comptée, et un envoi partiel est annoncé comme tel *(« 3 photo(s) envoyée(s), mais 1 n'a pas
pu être préparée : salon.jpg »)* — **leçon de 4a**.

**Épreuve** : build vert, et **vérifié à l'écran** en mode local sur une vraie fiche — le libellé
dit « Choisir une ou plusieurs photos » et le champ porte bien `multiple: true` (lu dans le
navigateur). Aucune erreur nouvelle.

### ✅ ESSAI RÉEL — *11/10 à 17:31, en production, bien d'essai 62774*

*Accord de Frédéric (« Oui test »). Fait dans SON Chrome, où il est connecté — le navigateur
intégré ne sait pas joindre un fichier.*

**À l'écran** : « Choisir une ou plusieurs photos » → 2 fichiers joints → « **2 photos
choisies** » et « **Envoyer 2 photos** » → le suivi affiche **les deux** → la galerie passe de
**2 à 4 visibles**.

**En base** :
```
2 travaux crees a 17:31:45, LA MEME SECONDE
  essai_multi_photo_1.png   demarre 17:31:52   fini 17:32:14   21,6 s   done
  essai_multi_photo_2.png   demarre 17:32:14   fini 17:32:35   20,6 s   done
                            ^ il a ATTENDU que le premier finisse
bout en bout : 29 s pour la premiere, 49 s pour la seconde · 0 erreur
```

**Arrivées des deux côtés** : `hektor_photo_id` **487603** et **487604**,
`present_in_hektor = true`, **et gardées chez nous** *(les deux photos plus anciennes du même
bien, du 25/08, ne le sont pas — elles datent d'avant ce geste)*.

⚠ **Et l'essai CONFIRME la limite annoncée** : les deux sont partis **l'un après l'autre**,
**~21 s chacun**. Pour 20 photos, compter **~7 minutes**. C'est exactement pourquoi **l'envoi
groupé** reste le vrai gain à faire *(Hektor l'accepte ; la preuve de réussite devra compter N)*.

⏳ **Les 2 images d'essai sont restées sur le bien 62774** — retrait proposé à Frédéric,
en attente de sa réponse.

## ③ CE QU'IL RESTE

1. ⏳ **Déployer** : c'est du front, donc **pousser** — décision de Frédéric, elle déborde 4e.
2. ⏳ **Le multiple sur la fiche annonce** (un fichier à la fois aujourd'hui) — petit ajout.
3. ⏳ **L'envoi groupé** (1 travail pour N photos : ~30 s au lieu de ~7 min) — **possible, Hektor
   l'accepte**, mais la confirmation devra **compter N**.
4. ⏳ **Le WebP** : notre app l'accepte, l'`accept` de Hektor ne le liste pas, **jamais essayé**.
5. ⏳ **Un seul worker « actions »** : deux créations simultanées se mettent en file. Noté, c'est
   un sujet de capacité, pas de 4e.

---

# POINT 4f — L'ALARME « TRAVAUX EN ERREUR » FIGÉE AU ROUGE

## ① AUDIT — *11/10/2026, lecture seule.* Verdict : **RIEN N'EST VRAIMENT NÉCESSAIRE**

*Décision de Frédéric le 11/10 : on ferme 4f en écrivant ce qu'on a mesuré, et on passe à 4g.*

### L'histoire complète des erreurs — 592 depuis le 14/05

```
466 sur 592  (79 %)  INFRASTRUCTURE, jamais un geste de negociateur
     dont 196  « Hektor 403 »   14/05 -> 20/08  = le bannissement d'IP (TERMINE)
     dont  47  push_single_annonce_to_supabase.py  02/06 -> 09/10  ENCORE ACTIF
126 sur 592  (21 %)  des gestes de negociateur
     update_hektor_annonce_fields 45 · create_hektor_draft_annonce 19
     update_hektor_contact_search 11 · update_hektor_contact 11 · le reste < 7
```

⭐ **ZÉRO geste de transaction n'a JAMAIS échoué** — ni offre, ni compromis, ni vente, en cinq mois.

### 1. « L'alarme est bloquée au rouge » : c'est **voulu**, et ce n'est pas un défaut

Le seuil 0 est une décision écrite, avec son histoire *(monitoring/check_gti_health.py:182-199)* :

> *« Posée le jour où on a trouvé 37 travaux en erreur dormant depuis le 27/08 — triés un par un,
> c'étaient TOUS des essais, pas un seul geste client perdu. Mais **personne ne le savait** :
> 37 erreurs mortes garantissent que la 38ᵉ, la vraie, passe inaperçue. »*
>
> *« SEUIL 0, PAS "PEU". Une erreur qui reste est une erreur qu'on a décidé de ne pas traiter.
> **Soit on rejoue, soit on purge en écrivant pourquoi.** »*

**Et l'action a été faite deux fois** : purges documentées le **01/10** et le **11/10 à 07:42**, chaque
erreur lue une par une. Les erreurs ne sont pas perdues : `app_console_job_error_archive` garde
**type, motif, combien, période**. **Aujourd'hui : 0 travail en erreur.**

⭐ **Et une règle que je ne connaissais pas**, trouvée dans le patch du 11/10 :
> *« job en erreur sur cette annonce → **NE JAMAIS REJOUER** (les 403 répétés ont fait **bannir
> l'IP**) »* — le refus de rejouer a une raison **chèrement payée**.

### 2. Les deux trous réels, et pourquoi aucun n'est urgent

**Trou n° 1 — les gestes de transaction n'avertissent personne.** Mesuré : la liste des travaux qui
envoient un message au négociateur compte **25 types**, et les **cinq** gestes de transaction en
sont **absents** (`change_hektor_offre_status`, `cancel_hektor_compromis`,
`delete_hektor_compromis`, `delete_hektor_vente`, `submit_hektor_transaction_status`).
➡ **Mais 0 occurrence en cinq mois.** C'est une assurance, pas un trou qui saigne.

**Trou n° 2 — la sentinelle est aveugle à la moitié des familles.** Les deux constantes, relues en
base : on rejoue **5 fois au plus**, et **seulement pendant 24 h** ; or `geste_abandonne` exige
**5 tentatives**. Donc tout ce qui n'est **pas** rejouable reste à **1 tentative pour toujours** et
**ne peut jamais** y entrer *(mesuré : `tentatives max = 1` sur toutes les erreurs jamais
enregistrées)*.

| famille | rejouée ? | vue par `geste_abandonne` ? | négociateur averti ? |
|---|---|---|---|
| gestes d'état **annonce** | ✅ | ✅ | ✅ |
| gestes d'état **transaction** | ✅ | ✅ | ❌ *(trou n° 1, 0 cas)* |
| **mandant** (lier, délier, créer, modifier) | ❌ | ❌ **jamais** | ✅ |
| **créations, dépôts, recherches** | ❌ | ❌ **jamais** | ✅ |

➡ **Mais ces familles sont déjà couvertes** par `travaux_en_erreur` (seuil 0), qui a bien sonné et
a bien été traité. Et le négociateur, lui, **est prévenu** pour toutes.

### 3. ⚠ DEUX CORRECTIONS DE MA PART, à garder en mémoire

**(a) J'ai présenté le trou n° 1 comme une urgence.** C'était faux : **0 geste de transaction n'a
jamais échoué**. Je l'avais mis en tête de liste sans avoir compté.

**(b) J'ai affirmé que deux scripts n'avaient « aucun `busy_timeout` ».** **FAUX.** J'avais cherché
**le mot** dans les fichiers, alors que le réglage s'y écrit autrement :
```python
sqlite3.connect(PHASE2_DB, timeout=30)   # <- c'est EXACTEMENT le busy_timeout, en secondes
```
**Les trois connexions attendent déjà 30 secondes.** *Chercher un mot n'est pas mesurer un
comportement* — la faute que le projet me reproche depuis le début.

### 4. Ce que `database is locked` veut vraiment dire ici

La base est en **mode WAL** *(relevé : `journal_mode = wal`, 6,1 Go)*. En WAL, **un lecteur ne
bloque jamais un écrivain** : le message ne peut donc venir que de **deux écrivains** qui se
croisent, le second ayant attendu ses 30 s en vain.

```
01/10 a 13:45   refresh_console_data
05/10 a 06:44   refresh_console_data          <- PENDANT le run (05:00 -> 07:34)
08/10 a 06:32   refresh_console_contact_data  <- PENDANT le run
```

**Deux fois sur trois, c'est le run de nuit**, qui tient le verrou d'écriture plusieurs minutes
*(la mémoire du projet note 8 min 30 une fois)*. Ce n'est donc **pas un réglage manquant, c'est un
réglage trop court pour la réalité du run**.

## ② LA DÉCISION — *4f est CLOS sans correctif*

```
3 erreurs « locked » en 11 jours
toutes les 3 sur des travaux d'INFRASTRUCTURE (rafraichir une fiche), jamais un geste client
et ces rafraichissements sont REFAITS : la nuit suivante, le run remet tout a jour
-> RIEN n'est perdu. Le seul degat, c'est du BRUIT dans l'alarme.
```

**L'alarme n'était pas cassée** : elle est faite pour rester rouge jusqu'à ce qu'un humain tranche,
et l'humain a tranché deux fois en écrivant pourquoi.

### ⏳ Ce qui reste noté, non fait, et pourquoi

| | Ce que c'est | Pourquoi on ne le fait pas aujourd'hui |
|---|---|---|
| **C** | passer `timeout=30` à `timeout=300` dans `push_single_annonce_to_supabase.py` (2 connexions) et `refresh_contact_inproc.py` (1) | **du rangement, pas une réparation** : ça enlève la dernière cause active de bruit, mais **rien n'est perdu**. ⚠ Et pendant qu'il attend, le worker est **immobilisé** jusqu'à 5 min |
| **A** | les 5 gestes de transaction dans la liste des avertissements | **0 occurrence en 5 mois** · 5 lignes à glisser **le jour où on touchera le worker pour autre chose** — ne justifie pas un redémarrage des 4 services |
| **B** | une branche « familles non rejouables » dans la vue | ⛔ **retirée** : le signal existe déjà, et elle **frôle une décision écrite** qui refuse de séparer les lectures des gestes |
| — | `sync_console_documents` : **402 erreurs**, le plus gros producteur du système *(dont 196 du bannissement d'IP, terminé le 20/08)* | **signalé, pas traité** : c'est déjà lui qui a fait sauter 3 étapes du run le 09/10. Le point fragile à surveiller |

---

# POINT 4g — L'ABANDON RÉEL NE REND PAS L'ÉTAT *(reste du chantier ⑤ : 5f)*

## ① AUDIT — *11/10/2026, lecture seule.* Verdict : **CONFIRMÉ, petit, et AUTO-RÉPARANT**

*Décision de Frédéric le 11/10 : **on note et on passe à 4h**, pour finir le chantier et revenir
sur ces petits rangements d'un bloc.*

### Ce que fait vraiment l'abandon

`app_action_resolve(target_job_id, mode)`, relue en base. Elle vérifie les droits *(le même
contrôle que le geste lui-même)*, exige `status = 'error'` **et au moins 5 tentatives**
— *« on ne tranche que ce qui attend vraiment »* — puis **archive** le travail et toute sa charge
dans `app_pending_resolution`.

**Et c'est tout.** Elle ne touche **pas** à l'état de l'affaire. Et `refait` et `abandon` font
**exactement la même chose** : le mode est seulement **enregistré**.

> **L'abandon est un classement, pas un geste.** Il range le dossier et ferme la ligne d'alerte ;
> il ne corrige pas ce qui est affiché.

### Quand ça se déclenche — mesuré

```
par epuisement du filet :  JAMAIS. Sur les 10 types rejouables, le maximum jamais
                           atteint est 4 tentatives (le seuil est 5).
a la main :                DEUX FOIS, par Frederic, le 01/09, toutes deux sur le
                           bien d'essai 62774, toutes deux change_hektor_offre_status.
```

La charge archivée garde **`etat_avant: "proposed"`** — l'information pour restaurer **est là**.

### ⭐ Mais l'état se corrige tout seul, et c'est structurel

```
31 040 affaires sur 31 058 ont ete revues AUJOURD'HUI par le run de nuit
```

Le registre des affaires est **reconstruit chaque nuit depuis Hektor** : un état faux se répare
**en 24 h au plus**, sans que personne n'intervienne.

**Vérifié sur le cas réel** : l'affaire **1000002**, dont le geste « accepté » a été abandonné le
01/09, affiche aujourd'hui **`refused`** — exactement ce que dit la liste des propositions de
Hektor *(dernier mouvement : refus, 01/09 à 12:03)*. **Aucun mensonge ne subsiste.**

### ⚠ Un défaut latent trouvé au passage

Quand un travail est **« dépassé par un plus récent »**, le filet lui **force `attempt_count = 5`**
pour le sortir de la file. Or `geste_abandonne` sélectionne *« erreur **et** au moins
5 tentatives »* : un travail **légitimement dépassé** apparaîtrait donc comme **« en attente d'un
humain »** — une **fausse alerte**. *(Aujourd'hui : 0 ligne, donc aucun bruit réel.)*

## ② CE QUI EST VRAIMENT NÉCESSAIRE — *et pourquoi le correctif imaginé en ⑤ était mauvais*

**Rien d'urgent** : jamais déclenché automatiquement, deux fois à la main en cinq mois, sur un
bien d'essai, et l'écran se répare seul en moins de 24 h.

⚠ **Et la correction que le chantier ⑤ avait imaginée — « rendre l'état d'avant » — serait une
mauvaise idée.** La cause écrite le 01/09 dit : *« le geste n'a **probablement** RIEN fait »*.
**Probablement.** Remettre `etat_avant`, c'est **deviner**. La vérité est chez Hektor, pas dans
notre charge de travail.

### Le bon geste, s'il faut en faire un : **ne pas restaurer, RELIRE**

Une ligne à ajouter dans `app_action_resolve` : quand on tranche *(abandon **ou** refait)*, créer
un travail **`refresh_console_data`** sur l'annonce concernée. La fenêtre de mensonge passe de
**≤ 24 h à ~1 minute**, et **rien n'est inventé**.

| | |
|---|---|
| **Coût** | un patch SQL avec répétition et inverse. **Aucun worker, aucun front, aucun déploiement, aucun redémarrage** |
| **À vérifier avant** | la fonction est appelée depuis **trois** endroits du front (action, annonce, contact) |
| **Risque** | un travail de plus par abandon — **2 abandons en 5 mois**, le débit n'est pas un sujet |
| **Ce que ça ne fait pas** | la fausse alerte du « dépassé par un plus récent » reste — sujet séparé, 0 occurrence |

**⏳ NOTÉ, NON FAIT** — à reprendre avec les autres rangements de fin de chantier *(le `timeout`
de 4f, les 5 gestes de transaction à notifier)*.

---

# POINT 4h — LE MARQUEUR ET LE BOUTON « RÉESSAYER » *(reste du chantier ⑤ : 5h, options B et C)*

## ① AUDIT — *11/10/2026, lecture seule.* Verdict : **le scénario n'est JAMAIS arrivé**

*Décision de Frédéric le 11/10 : **on note 4h** et on finit le chantier avec 4i.*

### Le geste, en clair

Quand on ajoute un mandant depuis l'app, **deux choses sont écrites tout de suite** : le
**contact**, durablement, avec notre numéro ; et le **lien**, en provisoire. Puis l'app demande à
Hektor de créer le contact et de rendre **son numéro**.

```
si Hektor echoue :
   le LIEN     passe en ROUGE a l'ecran        -> cette moitie FONCTIONNE
   le CONTACT  reste dans l'annuaire, comme un vrai -> et PERSONNE ne dit qu'il est orphelin
```

⚠ **Garder le contact est VOULU** (C.1', *« une saisie ne se perd jamais »*). **Le défaut n'est
pas qu'il reste : c'est qu'on ne le dit pas.**

### Les chiffres — le cas ne s'est jamais produit

```
contacts sans numero Hektor aujourd'hui :  0   sur 62 189
creations de MANDANT  17  -> 0 en erreur, JAMAIS (verifie aussi dans l'archive)
creations de CONTACT  16  -> 2 en erreur, toutes deux le 29/05 :
      l'une un STOP volontaire de Frederic pendant l'episode du bannissement d'IP,
      l'autre « contact_id Hektor numerique requis »
      -> les deux AVANT que le contact soit garde durablement (bascule du 23/09)
derniere creation : 21/09
```

### Ce qui couvre déjà le cas

- **L'option A est faite** *(08/10)* : la sentinelle `contact_sans_numero_hektor`, **lue par le
  moniteur**, seuil 0, **critique** — Frédéric serait averti **le jour même**. Elle lit la
  **doublure Supabase** : une sentinelle posée sur la couche locale aurait rendu 0 **en mentant**.
- **Le négociateur serait prévenu aussi, mais tard et de biais** : chaque geste suivant sur ce
  contact échouerait, avec le message de 4b *(« pas encore créé chez Hektor : rien à viser »)*.

**Et le marqueur n'existe toujours pas** : vérifié dans le front, **aucun affichage** ne distingue
un contact sans numéro Hektor — alors que l'information est là, `hektor_target_id` vide **est** la
signature *(pas de colonne, pas de migration)*.

## ② CE QU'IL FAUDRAIT — *et ce qu'il ne faut surtout pas faire*

**B — la pastille « en attente de Hektor »** : ~10 lignes de front, aucune donnée nouvelle, aucun
risque. Elle transforme un échec **tardif et de biais** en information **immédiate**.
➡ **Un confort utile, pas une réparation** — 0 occurrence, sentinelle critique déjà en place.

**C — le bouton « réessayer » : NON.** Rejouer une création **doublerait le contact chez Hektor**
(règle C.4-bis). Pour le faire sans danger il faudrait d'abord **demander à l'API de Hektor si le
contact existe déjà** *(le patron du mandant, 31/08)* : cher, risqué, pour un cas jamais survenu.
**Je ne le propose pas.**

**⏳ NOTÉ, NON FAIT** — à reprendre avec les autres rangements de fin de chantier *(le `timeout`
de 4f, le « relire » de 4g, les 5 gestes de transaction à notifier)*.

---

# POINT 4i — UNE OPTION QUI NE FAIT RIEN, PASSÉE CHAQUE NUIT

## ① AUDIT — *11/10/2026, lecture seule.* Verdict : **CONFIRMÉ**

Chaque nuit, le run lance `sync_raw.py` avec **`--missing-only`**. L'option est déclarée
*(« Pour les détails génériques, ignorer les IDs déjà présents »)*, elle est **parsée**… et :

```
args.missing_only                                 -> LU NULLE PART (0 occurrence)
sa seule lectrice, sync_generic_details           -> AUCUN APPELANT
sa jumelle, resolve_generic_detail_limit          -> AUCUN APPELANT
```

⭐ **Et le code le disait déjà lui-même**, dans `resolve_generic_detail_limit` :
> *« **SANS APPELANT depuis le 21/07/2026**, en même temps que `sync_generic_details`. »*

### Ce que ça coûte : **rien de fonctionnel**

Les fiches de détail « génériques » **ne passent plus par ce chemin**, et c'est voulu — le run le
documente : *« la fraîcheur des mandats vient entièrement de `MandatsByIdAnnonce`, appelé avec le
détail de chaque annonce, ainsi que du read-through »*. **Rien n'est perdu, rien n'est ralenti.**

### Ce que ça coûte en vrai : **un mensonge dans la ligne de commande du run**

C'est le même motif que tout le chantier, à l'envers : **ce n'est pas un échec silencieux, c'est
un NO-OP silencieux.** Qui lit le run croit qu'un filtre s'applique. Le jour où quelqu'un
cherchera pourquoi une fiche est re-téléchargée, il perdra une heure sur cette ligne.

*(À ne pas confondre : `run_contact_details_backfill.ps1` passe aussi un `--missing-only`, mais à
**un autre script**, où il est déclaré « compatibilité : comportement par défaut » — inoffensif.)*

## ② LE CORRECTIF — *« marquer », choisi par Frédéric le 11/10*

> **On retire le mensonge, pas le code.**

```
run_full_pipeline.ps1   +11 lignes, QUE DES COMMENTAIRES -- l'option RESTE passee
sync_raw.py             +25 lignes de commentaires, et 1 ligne d'aide reecrite :
                        « SANS EFFET depuis le 21/07/2026 : voir sync_generic_details »
```

**Zéro changement de comportement** : la seule différence visible est le texte de `--help`. On ne
touche **pas** à la ligne d'arguments du run — la retirer ne changerait rien, mais toucher le run
pour un no-op serait **un risque gratuit**.

**Pourquoi marquer et non supprimer** *(choix de Frédéric)* : le projet n'écrase pas du code
existant, et ces deux fonctions documentent un chemin qui a servi.

### L'épreuve
- `sync_raw.py` : **syntaxe Python valide** *(analyse du fichier entier)* ;
- `run_full_pipeline.ps1` : **syntaxe PowerShell valide** *(analyseur officiel, 0 erreur)* ;
- `sync_raw.py --help` : l'option **existe toujours** — donc la ligne du run reste valable — et
  son aide dit désormais **« SANS EFFET depuis le 21/07/2026 »**.

### Retour arrière
`git revert`. **Aucune écriture, aucun patch SQL, aucun déploiement, aucun redémarrage.**

### Contrôle
Le **run du 12/10** doit se dérouler **à l'identique** : mêmes étapes, même durée. Aucune raison
qu'il bouge — rien de ce qui s'exécute n'a changé.

---

# ✅ CLÔTURE DU CHANTIER ④ — *11/10/2026, les 9 points traités*

## Ce qui a été fait

| | | |
|---|---|---|
| **4a** | la suite d'une création marquée « réussie » malgré l'échec | ✅ **corrigé** — avertissement au négociateur + branche de sentinelle · patch appliqué, 4 workers redémarrés · épreuve **19/19** |
| **4b** | **cinq** messages promettaient une reprise inexistante | ✅ **corrigé** — ils disent la vérité · épreuve **11/11** · *(B et C reportés)* |
| **4c** | « Annonce en création » sans marque d'erreur | ✅ **corrigé** — la sentinelle qui **comptait déjà** sait enfin **juger** · épreuve **21/21** |
| **4d** | une recherche en échec effacée au bout de 24 h | ✅ **corrigé** — on **compte** et les erreurs durent **7 jours** · patch appliqué et contrôlé |
| **4e** | les photos de la création dans la mémoire du navigateur | ✅ **corrigé** — on **informe** sans toucher au mécanisme · **déployé** · ➕ **plusieurs photos à la fois** sur la fiche annonce |
| **4f** | l'alarme « travaux en erreur » figée | ✅ **clos sans correctif** — elle n'était **pas cassée** |
| **4g** | l'abandon réel ne rend pas l'état | 🔎 **noté** — **auto-réparant** en ≤ 24 h |
| **4h** | marqueur et bouton « réessayer » | 🔎 **noté** — **jamais arrivé**, et le bouton serait **dangereux** |
| **4i** | `--missing-only` sans appelant | ✅ **marqué** — le mensonge est retiré, pas le code |

## ⭐ Les cinq leçons de ce chantier

1. **Chercher l'œil qui existe avant d'en poser un neuf.** En 4c, la sentinelle `annonce_un_numero`
   **comptait déjà** la bonne population — elle **refusait de juger**, faute de pouvoir séparer
   l'attente normale de l'échec. En 4h, l'option A était déjà posée. En 4e, le chemin différé
   dormait dans le worker. **Trois fois sur neuf.**
2. **On tranche sur l'état du travail, jamais sur l'horloge** *(née d'une question de Frédéric)* :
   l'attente normale d'une création monte à **44 minutes** — tout délai aurait sonné faux.
3. **Ne jamais faire d'un maximum une généralité.** Ces mêmes 44 minutes étaient **un seul cas**
   sur 79 ; la médiane est de **3,4 secondes**. Donner la médiane **et** la queue.
4. **Chercher un mot n'est pas mesurer un comportement** (4f) : j'ai affirmé qu'un `busy_timeout`
   manquait alors qu'il s'écrivait `timeout=30`.
5. **Le plus souvent, le défaut n'était pas une négligence** : une décision à moitié appliquée
   (4b), une décision **écrite et raisonnée** (4d, 4f), ou une limite technique (4e).

## ⏳ Ce qui reste noté, et pourquoi

| | Ce que c'est | Pourquoi pas maintenant |
|---|---|---|
| **4b-B / 4b-C** | brancher `reprendre_envois_hektor.js`, puis prévenir | reporté par Frédéric · le report est **gardé par le code** : le contrôle (2c) de l'épreuve tombera en échec dès qu'on branchera le repreneur |
| **4c-A2 / 4c-B** | la même alerte **en direct** · la marque « Erreur de création » **à l'écran** | A2 : le délai de ~24 h ne gêne pas · B : demande un déploiement |
| **4f-C** | `timeout=30 → 300` sur deux scripts | **du rangement, pas une réparation** — rien n'est perdu |
| **4f-A** | les 5 gestes de transaction à notifier | **0 occurrence en 5 mois** — à glisser quand on touchera le worker |
| **4g** | **relire** chez Hektor au moment où l'on tranche *(ne jamais restaurer : ce serait deviner)* | auto-réparant en ≤ 24 h |
| **4h-B** | la pastille « en attente de Hektor » | **un confort** — 0 occurrence, sentinelle critique déjà en place |
| **4e** | l'**envoi groupé** des photos *(1 travail pour N : ~30 s au lieu de ~7 min)* · le **WebP** jamais essayé | ⚠ la confirmation devra **compter N et non 1**, sinon un envoi partiel passerait pour réussi — le défaut 4a sur un autre objet |
| — | `sync_console_documents` : **402 erreurs**, le plus gros producteur du système | **signalé** : c'est déjà lui qui a fait sauter 3 étapes du run le 09/10 |
