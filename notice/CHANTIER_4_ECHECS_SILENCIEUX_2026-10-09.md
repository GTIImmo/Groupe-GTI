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
| **4a** | la **suite** d'une création (champs, mandant) rate, mais le travail est marqué « réussi » | 🧪 **patch SQL APPLIQUÉ et contrôlé le 09/10** (empreinte `e2c015e1…`, 0 ligne, droits intacts) · épreuve hors ligne **19/19** · **reste le redémarrage du worker** pour l'avertissement |
| **4b** | **aucun nouvel essai** pour 6 familles de travaux, et le worker écrit quand même « Le travail sera repris » | ⬜ |
| **4c** | « Annonce en création » en échec **sans marque d'erreur** (le marqueur lit une table plus remplie) | ⬜ |
| **4d** | une **recherche créée en échec** disparaît au bout de 24 h, sans bouton « réessayer » | ⬜ |
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

## ⑤ CE QU'IL RESTE À FAIRE — *au 09/10*

1. Frédéric colle **la répétition** → il me recopie le message `ESSAI ANNULE -- 4a` ; je compare
   aux valeurs attendues (écrites en tête du fichier) ;
2. si c'est le bon : il colle **le vrai patch** → je relis la vue (0 ligne), les 7 colonnes, les
   droits, et je fais tourner le moniteur (`geste_abandonne` doit rester **verte**) ;
3. **redémarrage des 4 workers** (en journée, file documents vide, avec son accord) pour la
   moitié 1 — `console_job_worker.js` est partagé par les quatre services ;
4. aucun déploiement : ni front, ni Render, ni Vercel.
