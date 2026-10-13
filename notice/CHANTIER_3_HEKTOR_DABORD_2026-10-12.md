# CHANTIER ③ — « HEKTOR D'ABORD » → « CHEZ NOUS D'ABORD »

**Ouvert le 12/10/2026.** Source du périmètre : `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md` §2 ③
*(et le suivi du plan, section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 », ligne ③ — renvois `L10-3`, `G.5`)*.

La méthode est celle de `CLAUDE.md` §0 : audit → explication (avec « ce que ça pourrait casser
ailleurs ») → « vas-y » → code → contrôle → documents.

---

## LES 5 POINTS

| # | Le point | État |
|---|---|---|
| **3a** | **Annonce : mise sous mandat (Estimation → Actif) et « Mandat clos »** — rien n'est écrit chez nous | 🔎 **audit fait le 12/10 : CONFIRMÉ** |
| **3b** | **Annonce : archiver et changer de négociateur** — l'intention va au carnet `app_annonce_champ_app`, que personne ne lit | ⬜ |
| **3c** | **Mandat : clôture** — Hektor d'abord, et la date de clôture n'arrive ni au registre ni dans `app_mandat` | ⬜ |
| **3d** | **Documents et photos : ajout** — la ligne n'existe chez nous qu'après Hektor ; le chemin « chez nous d'abord » existe mais dort (G.5) | ⬜ |
| **3e** | **Document : suppression** — Hektor d'abord, puis notre copie est détruite | ⬜ |

---

## 3a — MISE SOUS MANDAT ET « MANDAT CLOS »

### ÉTAPE 1 — AUDIT (12/10, lecture seule) — verdict : **CONFIRMÉ**

**Ce que fait la fonction aujourd'hui.** `app_change_annonce_status_optimistic`
*(lue dans la base, `pg_get_functiondef`, 8 446 caractères, empreinte sans CR
`302852e8dc23c44d6e0442b81e6cb577`)* commence par :

```
v_kind := case target_status
            when 'offer'      then 'offre'
            when 'compromise' then 'compromis'
            when 'sold'       then 'vente'
            else null end;
```

Tout ce qu'elle écrit chez nous — la ligne d'affaire (`app_affaire_ledger`) et le carnet
(`app_affaire_champ_app`) — est **à l'intérieur de `if v_kind is not null then`**. Pour
`target_status = 'active'` (mise sous mandat) et `'closed'` (Mandat clos), `v_kind` vaut `null` :
**la fonction ne crée QUE le travail Hektor.** Aucune ligne, aucun carnet, aucun statut.

**Ce que ça donne à l'écran.** Le front (`apps/hektor-v1/src/lib/api.ts:9917`, seul appelant de
la fonction hors script d'essai) referme la modale et affiche
« Changement vers Actif demandé pour … » (`App.tsx:16763`). Le travail est inscrit au suivi des
actions en cours (`rememberHektorActionJob`, `App.tsx:12702`) et un second geste sur la même
annonce est refusé (`App.tsx:16640`). **Mais la pastille de statut ne bouge pas** : elle est
calculée sur les colonnes plates de `app_dossier_current`, que rien n'a touchées.

**Combien de temps.** Le travail part chez Hektor, puis le worker demande une relecture
(`console_job_worker.js:14647`, `refresh_console_data`, priorité 72). Mesure sur le dernier cas
réel — annonce **62963**, le 08/10 :

| | heure | durée |
|---|---|---|
| clic (travail créé) | 18:48:23 | |
| statut posé chez Hektor (travail `done`) | 18:49:00 | 37 s |
| relecture terminée → notre base porte « Actif » | 18:49:41 | **78 s au total** |

**Donc ce n'est pas une perte, c'est une fenêtre.** Dit honnêtement : pendant ~1 à 2 minutes,
notre base porte l'ancien statut, et **si Hektor refuse définitivement, notre base n'a JAMAIS
su que quelqu'un avait demandé le changement** (seul `app_console_job` le garde).

**Le filet existe, lui.** `change_hektor_annonce_status` est bien dans la liste des types
rejouables de `app_console_action_enqueue_due_retries` (5 tentatives, 24 h, cron chaque minute) —
lu dans la base. **Et aucun de ces travaux n'a jamais échoué** :

| cible | état | nombre | premier | dernier |
|---|---|---|---|---|
| `active` | `done` | **19** | 22/05 | **08/10** |
| `closed` | `done` | **9** | 21/05 | 29/08 |
| `offer` / `compromise` / `sold` | `done` | 10 / 74 / 20 | 25/08 | 18/09 |

*(0 ligne en `error` ou `pending`. L'audit du 08/10 disait « 18, la dernière le 03/09 » : il y en a
une de plus depuis, le 08/10.)*

**L'enjeu, en nombres d'aujourd'hui.** `app_dossier_current` : **12 747 Estimation**, 592 Actif,
90 Sous compromis, 46 Sous offre. La mise sous mandat est le geste qui fait passer un bien des
12 747 aux 592 — le geste le plus structurant du quotidien de l'agence. Il a été fait **19 fois**
depuis l'app, et le chantier ② vient d'ouvrir 21 gestes aux négociateurs : l'usage va monter.

**Le pourquoi — ce n'est pas un oubli, c'est un lot jamais construit.** `notice/ETUDE_FAISABILITE_STATUT_OPTIMISTE_2026-06-29.md`
(29/06) répond déjà « oui, faisable, et même plus simple que l'édition de champs », et propose
deux colonnes transitoires `optimistic_status_target` / `optimistic_status_at` + lecture par la
pastille + nettoyage à la relecture. **Mesuré : ces colonnes n'existent nulle part dans la base**
(0 colonne `%optimistic_status%` dans `information_schema.columns`). Le lot 1 de l'étude n'a
jamais été fait ; seule la partie « affaire » de la RPC l'a été (C.4, 25/08).

**Et le patron à copier existe, éprouvé.** `supabase/patch_offre_verrouillee_2026-09-16.sql:169-182`
(et `patch_supprimer_compromis_2026-09-07.sql:141`) font exactement le geste « chez nous d'abord »
pour le statut, avec ses garde-fous :

```
UPDATE app_dossier_current SET statut_annonce = statut_apres ...     -- visible tout de suite
INSERT INTO app_annonce_champ_app (... 'statut', ..., 'redescente_transaction')  -- survit à la coupure
```

bornés par `app_statut_rang` *(Actif 1 · Sous offre 2 · Sous compromis 3 · Vendu 4 ;
**Estimation, Clos et vide sont hors échelle**)*, et **on ne touche ni `diffusable` ni `archive`**.
Le commentaire du worker le dit mot pour mot : *« l'app pose l'état avant que Hektor ait répondu —
c'est l'instantané voulu par Frédéric »* (`console_job_worker.js:18941`).

**La contrepartie manque, et le code le dit.** `console_job_worker.js:19016` :
*« Le changement de statut d'annonce non plus : il n'appelle pas `restaurerEtatAffaire` — seule
`restaurerStatutRedescendu` le fait, depuis ici. »* Donc si on pose le statut chez nous d'abord
**sans** rien d'autre, un refus de Hektor laisserait un statut faux jusqu'à la prochaine relecture
ou au run de nuit. Tout correctif doit emporter la contrepartie.

**L'état du carnet, mesuré.** `app_annonce_champ_app` ne contient que **3 lignes** :
`archive` (30/08, `geste_archiver`), `negociateur_email` (01/09, `geste_affecter_negociateur`),
`statut` (18/09, `redescente_transaction`). C'est le sujet du point **3b**.

### CE QUE JE N'AI PAS PU MESURER

- **L'écran en réel** : je n'ai pas fait de mise sous mandat depuis l'app (ça écrit chez Hektor —
  accord obligatoire). La pastille « ne bouge pas » est déduite du code, pas vue.
- **Ce que Hektor rend comme `diffusable`** après `active` / `closed` : le worker le pose
  (`setHektorAnnonceStatusValue`, `1` et `0`), mais je n'ai pas mesuré ce que la relecture
  redescend chez nous.
- **La durée d'attente quand le worker est occupé** : les 78 s mesurées sont un cas, un soir,
  file vide.

---

### ÉTAPE 1-bis — SECOND AUDIT (12/10, 17 h) — demandé par Frédéric

> *« continue sur 3a mais refais un audit car tous les workers fonctionnent, mais tu as raison il
> faut d'abord écrire sur l'app puis envoyer à Hektor, ne pas dépendre »*

**Frédéric a raison sur les workers, c'est mesuré.** Les 4 services ont écrit leur battement il y
a 0 à 1 minute (`app_worker_registry`, 12/10 15:35 UTC) : `console.worker.documents`,
`sync_light`, `actions`, `admin`. Le défaut n'est **pas** une panne.

**Ma première question était la mauvaise.** J'avais demandé « est-ce qu'on perd quelque chose ? » —
réponse non. La bonne question est celle de Frédéric : **« notre base sait-elle dans quel état est
notre propre bien, sans demander à Hektor ? »** — et la réponse est **non**.

#### Le tableau : ce que chaque geste écrit CHEZ NOUS *avant* d'appeler Hektor

| Le geste | La fonction | Colonne chez nous | Carnet | État d'avant *(pour revenir)* | La pastille bouge ? |
|---|---|---|---|---|---|
| **Mise sous mandat** (Estimation → Actif) | `app_change_annonce_status_optimistic` | ❌ **rien** | ❌ | ❌ | **non** |
| **Mandat clos** | idem | ❌ **rien** | ❌ | ❌ | **non** |
| Offre / compromis / vente | idem | ❌ *(la ligne d'affaire, oui)* | ✅ carnet d'affaire | ❌ | **non** |
| Archiver / restaurer | `app_archive_annonce_optimistic` | ❌ | ✅ `archive` | ❌ | non |
| Changer de négociateur | `app_assign_negotiator_optimistic` | ❌ | ✅ `negociateur_email` | ❌ | non |
| Refuser une offre · annuler un compromis · supprimer une vente | `app_geste_affaire_optimistic` | ✅ `statut_annonce` | ✅ `statut` | ✅ `statut_avant` + restauration | **oui** |

**⭐ Le seul geste qui écrit chez nous d'abord est celui qui fait DESCENDRE le bien.** Tous ceux qui
le font monter — et la clôture — dépendent de Hektor. *(Fonctions lues dans la base le 12/10 ;
`app_archive_annonce_optimistic` porte même le commentaire « 1. CHEZ NOUS D'ABORD » au-dessus
d'une écriture qui ne va qu'au carnet.)*

**Et la pastille ne bouge pour AUCUN des 5 statuts** — découverte du second audit. Elle est
calculée sur `vente_id` → `compromis_id` → `offre_id` → `statut_annonce` (`App.tsx:23554-23560`),
quatre colonnes de `app_dossier_current` que la fonction ne touche jamais. Pour les trois
transactions, l'étude du 29/06 l'avait **interdit à raison** : ces numéros servent à l'annulation
et aux jointures, les falsifier serait pire.

#### Pourquoi c'est resté comme ça — trois choses écrites, aucun oubli

1. **L'étude du 29/06** (`notice/ETUDE_FAISABILITE_STATUT_OPTIMISTE_2026-06-29.md`) propose le
   travail en 3 lots. **Lot 1 jamais construit** : 0 colonne `%optimistic_status%` dans la base.
2. **Le run le dit lui-même** (`run_full_pipeline.ps1:1272-1277`) : *« Le carnet n'a PAS de pendant
   "appliquer" pour l'instant, et c'est voulu : la liste `CHAMPS_APP_ANNONCE` du contrat
   d'autorité est VIDE. Hektor garde la main jusqu'à ce que Frédéric allume l'interrupteur. »*
   Et `phase2/identite/contrat_autorite.py:66-68` : *« VIDE, ET C'EST VOULU — c'est l'interrupteur
   du chantier »*. **L'interrupteur existe et il attend Frédéric.** *(Son frère mandat en porte
   déjà un : `CHAMPS_APP_MANDAT = ("mandat_date_cloture",)`.)*
3. La contrepartie manque et le worker l'écrit (`console_job_worker.js:19016`).

#### Ce qui ne risque RIEN si on écrit le statut chez nous d'abord — chacun vérifié

| Ce que ça pourrait toucher | Vérification | Verdict |
|---|---|---|
| **La vitrine publique** | `Ecrans Android/export_project_vitrine.py:445` : la liste publiée vient de la base **LOCALE** (`ATTACH hektor`), pas de Supabase. Supabase n'y sert qu'à retrouver les **photos** (l. 170). | **rien** |
| **La page RDV publique** | `backend/app/services/appointment_service.py:128` : exige `archive=0` **ET** `diffusable=1` **ET** statut ∈ {actif, sous offre, sous compromis}. Or **les 12 747 Estimation ont TOUTES `diffusable='0'`** *(mesuré)*. Poser « Actif » seul n'ouvre **rien**. | **rien**, si on ne touche pas `diffusable` |
| **Le run de nuit** | `push_upgrade_to_supabase.py` réécrit `statut_annonce` depuis le miroir chaque nuit, et `fetch_dirty_annonce_ids` **ne gèle plus aucun bien depuis le 21/09**. | **retour arrière automatique** la nuit suivante |
| **La protection champ par champ** | `app_annonce_reappliquer_saisies` (lue dans la base) lit **`app_annonce_pending`**, jamais le carnet. | écrire au carnet ne repose rien par erreur |
| **Les portails** | diffusion gelée depuis le 07/07 *(décision)*. | **rien** |
| **L'espace client** | `espace_client.py:459` : le statut n'y est qu'un **libellé** affiché. | cosmétique |
| **Les appelants de la fonction** | `apps/hektor-v1/src/lib/api.ts:9917` **seul** (plus `Console/test_worker_vente.js`, script d'essai). Aucun appel depuis le backend Render, le worker, `phase2`, un cron ou une autre fonction SQL. | **1 appelant** |

#### Ce qui demande une décision de Frédéric

Le geste chez Hektor pose **deux** valeurs : `status` **et** `diffusable`
(`setHektorAnnonceStatusValue`, `console_job_worker.js:11371-11389`) — `1` pour Actif, `0` pour
Mandat clos. Donc :
- **poser le statut seul** : notre base reste à moitié juste pendant ~78 s, mais **rien ne devient
  public** avant Hektor ;
- **poser les deux** : notre base est exacte tout de suite ; la page RDV publique s'ouvre ~78 s
  plus tôt pour « Actif » — et se **ferme** ~78 s plus tôt pour « Mandat clos » (plus sûr).

#### Non mesuré

- L'écran en réel (une mise sous mandat écrit chez Hektor : accord obligatoire).
- Ce que la relecture redescend comme `diffusable` après le geste.
- Les 78 s sont **un** chronométrage (annonce 62963, 08/10 au soir, file vide).

#### 📜 DÉCISION DE FRÉDÉRIC (12/10) — « il faut que mon app se comporte comme actuellement »

Ma question A/B était mal posée : elle lui demandait d'arbitrer un détail technique
(`diffusable`) alors que sa règle est plus simple et plus forte. **C'est donc l'option A** :

- on écrit **le statut** chez nous d'abord, rien d'autre ;
- **on ne touche pas `diffusable`** : donc **rien ne devient public plus tôt qu'aujourd'hui** ;
- Hektor reçoit exactement le même geste, le run de nuit garde le dernier mot.

**Le seul changement voulu : l'app n'a plus besoin de Hektor pour savoir dans quel état est son
propre bien.** Tout le reste se comporte comme aujourd'hui.

#### 📜 PRÉCISION DE FRÉDÉRIC (12/10) — « il faut aussi que l'on garde chez nous les diffusable ou non »

Il a raison, et ça lève ma confusion : **« garder chez nous »** et **« changer le comportement »**
sont deux choses différentes, parce qu'il y a **deux endroits** chez nous :

| | Son rôle | L'écrire change-t-il le comportement ? |
|---|---|---|
| **La colonne** `app_dossier_current.statut_annonce` / `.diffusable` | ce dont l'app **se sert** : l'écran, le rapprochement, les pages publiques | **oui** |
| **Le carnet** `app_annonce_champ_app` | ce que l'app **détient**, champ par champ — *« un carnet d'EXCEPTIONS, une ligne par champ dont l'app est l'auteur »* (`magasin_annonce_app.py`) | **non — personne ne le lit** *(mesuré : 0 lecteur dans `api.ts`, dans le run, dans `app_annonce_reappliquer_saisies`)* |

**La règle retenue** :

| Ce que le geste pose chez Hektor | Au carnet *(on le garde)* | En colonne *(l'app s'en sert)* |
|---|---|---|
| le statut (`Actif` = 2, `Mandat clos` = 6) | ✅ | ✅ — pour que l'écran ne mente pas |
| **`diffusable`** (1 pour Actif, 0 pour Clos) | ✅ **gardé** | ❌ — c'est elle qui ouvre les pages publiques |

Donc : **le `diffusable` est bien gardé chez nous**, et **les pages publiques continuent d'attendre
Hektor**, exactement comme aujourd'hui. 78 s plus tard, la relecture
(`push_single_annonce_to_supabase.py`, appelé en fin de `refresh_console_data`) pose la colonne
`diffusable` comme elle le fait déjà — et réconcilie le statut au passage.

C'est aussi **le patron déjà en place** : le geste « archiver » écrit `archive` au carnet et jamais
en colonne (`app_archive_annonce_optimistic`). On ne fait que l'étendre au statut et au
`diffusable`, en ajoutant la colonne du statut — la seule que l'écran lit et qui n'ouvre aucune
porte publique à elle seule *(mesuré : les 12 747 Estimation ont toutes `diffusable='0'`)*.

Le jour de la coupure, l'interrupteur `CHAMPS_APP_ANNONCE` *(`contrat_autorite.py`)* fait du carnet
la vérité, sans rien réécrire.

#### ⚠ CORRECTION (12/10) — la restriction sur `diffusable` est ABANDONNÉE

La règle de Frédéric, posée en deux fois, est **« sur tous les gestes »** : tout ce que le geste
pose chez Hektor s'écrit chez nous d'abord. Ma restriction « `diffusable` au carnet seulement »
est donc **retirée** : `diffusable` est écrit **au carnet ET en colonne**, comme le statut.

**Pourquoi j'avais hésité** — la colonne `diffusable` est l'une des deux conditions qui rendent
une **page publique de RDV** servable (`appointment_service.py:128` : `archive=0` **ET**
`diffusable=1` **ET** statut actif). L'écrire ouvre donc cette porte ~78 s plus tôt.

**Pourquoi ça ne tient pas** :
1. **le lien n'existe pas encore.** La page publique se rejoint par un lien publié par la
   **vitrine**, et la vitrine est refaite la nuit, depuis la base **locale**
   (`export_project_vitrine.py:445`). Personne n'a le lien d'un bien mis sous mandat il y a
   78 secondes.
2. **la valeur est VRAIE.** Mettre un bien sous mandat le rend diffusable : écrire `1` n'est pas
   une avance, c'est la réalité qui arrive plus tôt.
3. **pour « Mandat clos », ça FERME la porte 78 s plus tôt** — c'est plus sûr qu'aujourd'hui.
4. le run de nuit garde le dernier mot, et 28 gestes sur 28 ont réussi depuis mai.

Le seul effet interne mesuré reste le **rapprochement** (déclencheur `trg_dossier_dirty` sur
`statut_annonce` et `diffusable`, crons chaque minute) : le bien y entre ~78 s plus tôt, et ces
crons n'écrivent que dans `app_notification` — **aucun e-mail ne part**.

### ÉTAPE 3 — CODE (12/10) — « avant relis ton travail et vas-y »

**Relecture faite avant d'écrire** *(toutes les mesures refaites le 12/10 à 17 h)* :

| Ce que j'ai revérifié | Résultat |
|---|---|
| empreinte de la fonction, sans les retours chariot | `302852e8dc23c44d6e0442b81e6cb577`, **8 446** caractères |
| l'ancre d'insertion, avec ses 2 espaces | **1 seule** occurrence |
| le marqueur `@3a` et la variable `v_statut_cible` déjà présents ? | **0** et **0** |
| `v_payload` est-il initialisé **avant** le point d'insertion ? | oui, caractère 1 382 |
| `app_annonce_champ_app` | table, clé primaire `(app_dossier_id, champ)` → l'`ON CONFLICT` est correct |
| `app_dossier_current` | table, `statut_annonce` / `diffusable` / `archive` en `text`, RLS active mais la fonction est `SECURITY DEFINER` propriété `postgres` |
| `app_setting` | table `(key, value, description, updated_at)`, clé primaire sur `key` |
| triggers sur `app_console_job`, `app_annonce_champ_app`, `app_setting`, `app_affaire_ledger` | **aucun** |
| le seul trigger concerné | `trg_dossier_dirty` sur `statut_annonce` / `diffusable` → il appelle `app_enqueue_dirty`, **tout reste dans la base, aucun appel HTTP** |
| les 4 workers | vivants, dernier battement il y a **0 à 1 minute** |
| le dépôt | `git log` relu : dernier commit `b2bb4ac` (clôture de session), rien en cours sur ces fichiers |

**Les trois fichiers écrits** *(aucun n'a été exécuté : ma session ne peut pas écrire en
production)* :

| Fichier | Ce qu'il fait |
|---|---|
| `supabase/patch_chantier3_3a_etat_chez_nous_2026-10-12.sql` | pose l'interrupteur `etat_annonce_ecrit_chez_nous` ('on'), **lit** la fonction dans la base, vérifie empreinte + ancre unique + bloc absent, insère **un** bloc avant l'ancre, réexécute, puis **contrôle qu'en retirant le bloc on retombe sur l'empreinte d'avant** |
| `…_INVERSE.sql` | deux retours arrière : éteindre (1 ligne) ou retirer le bloc, avec le même contrôle d'empreinte **avant** de réexécuter |
| `…_REPETITION.sql` | le vrai patch + les **trois essais réels** (62774 « Actif », 62963 « Mandat clos », et le **témoin interrupteur éteint**) + le vrai inverse + une erreur volontaire finale qui **annule tout** et imprime 24 mesures |

**Ce que le bloc écrit, et seulement ça** : `statut_annonce` et `diffusable` sur la fiche ·
les deux mêmes au carnet avec l'origine `geste_statut` · `statut_avant` et
`diffusable_avant` dans la charge du travail. **Il ne touche ni `archive`, ni `offre_id`,
ni `compromis_id`, ni `vente_id`.**

### ÉTAPE 4 — RÉPÉTITION (12/10) : **24 mesures sur 24, exactes**

Collée par Frédéric. Les deux sens sont prouvés : le bloc **apparaît** (+3 896 caractères,
8 446 + 3 896 = 12 342) *et* **disparaît** à l'inverse (empreinte revenue à l'identique,
0 marqueur restant) ; et en retirant le bloc on retombe sur `302852e8…` **au caractère près**.

| Essai | Mesure | Attendu | Résultat |
|---|---|---|---|
| A — 62774 « Actif » | statut · diffusable · carnet | Sous offre→Actif · 0→1 · +2 | ✅ exact |
| A — ce qu'on ne touche pas | `archive` · `offre_id` | inchangés | ✅ inchangés |
| A — la charge | `statut_avant` · `diffusable_avant` | Sous offre · 0 | ✅ |
| B — 62963 « Mandat clos » | statut · diffusable · carnet | Actif→Mandat clos · 1→0 · +2 | ✅ exact |
| **C — le témoin, interrupteur ÉTEINT** | statut · diffusable · carnet | **inchangés** | ✅ inchangés |
| C — le geste part quand même | travaux Hektor | +1 | ✅ 28 → 29 |

### ÉTAPE 5 — CONTRÔLE DU RÉSULTAT (12/10, 18 h) — **le patch est appliqué et il est bon**

⚠ **Ce qui s'est passé** : Frédéric a collé le patch **deux fois**. Le premier passage a
réussi (le message final est un `NOTICE`, que l'éditeur Supabase n'affiche pas en évidence —
il écrit « Success. No rows returned »). Le second a été **refusé par le garde-fou d'entrée** :
*« la fonction n'est pas celle mesurée le 12/10 (empreinte 1f9e987f…, attendue 302852e8…,
taille 12342 contre 8446) »*. **C'est exactement son travail** : sans lui, le bloc aurait été
inséré une seconde fois.

| Ce que j'ai contrôlé en base | Résultat |
|---|---|
| taille de la fonction | **12 342** = 8 446 + 3 896, le compte exact |
| le bloc est-il **le mien**, octet pour octet ? | **oui** — `md5` du bloc en base = `1c01d673b178e40985e0d9e77c4b423b` = `md5` du bloc du fichier relu |
| le reste a-t-il bougé ? | **non** — en retirant le bloc : `302852e8dc23c44d6e0442b81e6cb577`, la fonction d'avant au caractère près |
| repères | 1 début, 1 fin — pas de double insertion |
| attributs | `SECURITY DEFINER` · propriétaire `postgres` · `search_path=public` — **intacts** |
| ⭐ **les droits** | `postgres`, `authenticated`, `service_role` — **`anon` toujours absent** : `CREATE OR REPLACE` a conservé l'ACL, **le verrou du chantier ① n'a pas été rouvert** |
| l'interrupteur | `etat_annonce_ecrit_chez_nous` = **`on`**, posé le 12/10 à 18:07 |
| **la répétition a-t-elle laissé quelque chose ?** | **non** : carnet toujours **3 lignes** (aucune `geste_statut`), 62774 toujours « Sous offre / diffusable 0 », 62963 toujours « Actif / diffusable 1 », **aucun travail de statut créé** (le dernier date du 08/10) |
| activité de l'app depuis le patch | 5 travaux, tous `done` : 1 modification de contact et 4 relectures — **l'usage normal**, rien d'anormal |

**Ce qui reste à contrôler** : un **essai réel depuis l'écran** (il écrit chez Hektor → accord
de Frédéric obligatoire), en chronométrant : la pastille doit bouger **tout de suite** au lieu
de 78 s, et la relecture doit reposer la valeur de Hektor ensuite.

#### L'ESSAI RÉEL (12/10, 18:19, accord de Frédéric) — **concluant**

Bien d'essai **62963** *(« TEST C15 entrepot depuis l app - a supprimer »)*, geste **« Clos »**
depuis l'écran, motif « Mandat non renouvelé · Confié à la concurrence ». Choisi parce qu'il
était `Actif / diffusable=1` : le geste **retire** de la diffusion au lieu d'y ajouter, donc
**aucune exposition nouvelle** pendant l'essai.

| Heure (UTC) | Ce qui s'est passé |
|---|---|
| **16:19:06** | clic — le travail est créé **et notre base porte déjà `Mandat clos / diffusable=0`** |
| 16:19:20 | mesure : le travail est encore **`running`** *(Hektor n'a pas répondu)* — et chez nous : fiche `Mandat clos / diffusable=0`, **carnet 0 → 2 lignes** (`statut=Mandat clos`, `diffusable=0`, origine `geste_statut`), charge du travail `statut_avant=Actif` / `diffusable_avant=1` |
| 16:19:49 | Hektor confirme (43 s) |
| 16:20:19 | relecture terminée (73 s) |

**⭐ La preuve est là : notre base était juste pendant que Hektor travaillait encore.**
**73 secondes gagnées**, et surtout : la valeur ne dépend plus de sa réponse.

**À l'écran** : « Changement vers Clos demandé pour 62963 », le bien **sort immédiatement** de la
liste « Annonces actives » (1 → 0), et il réapparaît avec le badge **CLOS** en étendant la
recherche. Le suivi Hektor affiche ensuite « Hektor a accepté le statut ».

#### ⚠ CE QUI A RATÉ, OU QUI RESTE À SAVOIR — trois choses, dites

1. **La fiche déjà OUVERTE ne se rafraîchit pas d'elle-même.** Elle a continué d'afficher
   « Actif » jusqu'à ce que je revienne à la liste. C'est **la liste** qui suit l'état tout de
   suite, pas le détail ouvert. *(Sans rapport avec le patch : rien n'a été ajouté côté écran.)*
2. **`cloture_mandat_locale : error`** dans le journal du travail — **attendu** : ce bien
   d'essai n'a **aucun numéro de mandat**, il n'y avait rien à clôturer chez nous. Le travail
   s'est quand même terminé `done`. C'est le sujet du **point 3c**.
3. 🔴 **UN « CLOS » NE SE RÉACTIVE PAS DEPUIS L'APP — et la modale promet le contraire.**
   Elle écrit : *« Elle reste consultable et réactivable via "Actif" »*. Mesuré : après la
   relecture, la ligne **sort de `app_dossier_current`** (le parc vivant). Or
   `app_change_annonce_status_optimistic` commence par
   `select … from app_dossier_current … if not found then raise 'dossier_not_found'` : le geste
   « Actif » **ne peut plus partir**. Le détail allégé n'offre que « Télécharger le détail ».
   ⚠ **Ce n'est PAS causé par le patch** — le bloc n'écrit que des `update` et des `insert`, il
   n'efface rien ; c'est la relecture (inchangée) qui retire la ligne du parc vivant.
   ➡ **À porter au chantier ⑦ (« les gestes qui manquent ») : réactiver un bien clos.**
   **62963 reste donc « Clos ».** Pour un bien d'essai marqué « à supprimer », c'est sans
   dommage — et même plus propre, puisqu'il était `diffusable=1`. **Question à Frédéric** :
   le laisser ainsi, ou le remettre en « Actif » directement chez Hektor ?

#### 🔴 RÉPONSE À LA QUESTION DE FRÉDÉRIC (12/10, 19:53) — **NON, un bien clos ne se réactive PAS**

*« 1 si un bien clos se réactive a partir de la modal changer statut »* → **la condition est
fausse, donc 62963 reste « Clos ».** Éprouvé pour de vrai, pas déduit :

1. la recherche étendue trouve le bien, badge **CLOS** ;
2. « Charger » puis « Télécharger le détail » → **depuis le serveur local, sans appeler Hektor**
   *(« Serveur local disponible »)* ;
3. la fiche complète s'ouvre et affiche : *« Mandat clos — lecture seule. **Réactivez le mandat
   pour reprendre la commercialisation.** »* ;
4. le bouton **« Faire évoluer le statut de l'annonce » EST bien là**, la modale s'ouvre, « Actif »
   se choisit, elle annonce *« Le statut Actif est envoyé directement à Hektor »* ;
5. clic sur **« Envoyer vers Actif »** → **`dossier_not_found`** s'affiche en bandeau, **aucun
   travail n'est créé** *(vérifié en base : le dernier travail reste celui de 16:19, cible
   `closed`)*.

**La cause, déjà établie** : la relecture retire la ligne de `app_dossier_current`, et
`app_change_annonce_status_optimistic` commence par y chercher le dossier —
`if not found then raise exception 'dossier_not_found'`.

**Trois défauts, à porter au chantier ⑦ :**
- l'écran **promet deux fois** une réactivation qui n'existe pas *(la modale de clôture et la
  bannière « Réactivez le mandat »)* ;
- le message rendu à l'utilisateur est le **code technique brut `dossier_not_found`** ;
- le geste manquant : **réactiver un bien clos** *(le statut est pourtant un simple `upval`
  status=2 chez Hektor — c'est la garde d'entrée de la fonction qui bloque, pas Hektor)*.

⚠ **Rien de tout cela n'est causé par le patch 3a** : le bloc n'écrit que des `update` et des
`insert`, il n'efface aucune ligne, et la garde `dossier_not_found` existe depuis l'origine de la
fonction *(elle est dans l'empreinte `302852e8…` d'avant)*.

**Précision de Frédéric** : *« il faut d'abord upload l'annonce close pour pouvoir avoir accès »* —
c'est **exactement ce qui a été fait**, et ça ne suffit pas. Mesuré :

| | |
|---|---|
| le chargement a bien tourné | travail `prepare_historical_annonce_detail`, 17:52:06 → 17:52:09, **3 secondes**, `done`, **depuis notre serveur local — aucun appel à Hektor** |
| ce qu'il remplit | `app_historical_annonce_index_current` : **1 ligne** *(l'index historique — de quoi AFFICHER la fiche)* |
| ce qu'il ne remplit pas | `app_dossier_current` : **0** · `app_dossier_detail_current` : **0** · `app_archive_annonce_index_current` : **0** |

➡ **Le chargement donne le droit de LIRE, pas celui d'AGIR.** Un bien clos part dans l'index
**historique** ; la fonction de statut, elle, exige le **parc vivant**. D'où `dossier_not_found`
même après le chargement.

**Les deux formes possibles du correctif** *(⑦, à arbitrer par Frédéric)* : ① la préparation
repose aussi la ligne dans le parc vivant ; ② la fonction de statut accepte un bien trouvé dans
l'index historique *(le geste chez Hektor est un simple `upval status=2`)*.

#### ⭐ FRÉDÉRIC AVAIT RAISON : le mécanisme de réintégration EXISTE (12/10, 20 h)

*« regarde l'annonce, normalement les index vendu et archivé peuvent être réintégrés dans l'app »*
→ **vrai**, et c'est **nous** qui l'avons écrit, le **08/10**, au point **5a** du chantier ⑤.

`app_restore_annonce_optimistic` (lue dans la base) porte exactement ce patron :

```
1. LE BIEN VIVANT   select * from app_dossier_current ... if found then ...
2. sinon, LE BIEN ARCHIVE  (5a, 08/10)
   select ... from app_archive_annonce_index_current where app_archive_id = target_dossier_id
   if not found then raise 'dossier_not_found'
```

Son commentaire dit déjà tout : *« Une archive n'est JAMAIS dans `app_dossier_current` : 35 317
archives, 0 présente. L'index des archives n'a pas de numéro de dossier ; l'écran envoie donc son
`app_archive_id` à cette place. Sans ce chemin, le geste levait `dossier_not_found` pour TOUTES
les archives depuis le 30/08. »* **C'est mot pour mot notre situation, un index plus loin.**

| Ce qui existe déjà | Mesure |
|---|---|
| l'index **historique** (vendu / clos) a la même forme que celui des archives | colonne **`app_historical_id`**, jumelle de `app_archive_id` |
| **l'écran envoie déjà le bon numéro** | `api.ts:2624` : `app_dossier_id: Number(row.app_archive_id ?? row.app_historical_id ?? …)` |
| le cas 62963 | `app_historical_id = 5880239` — exactement le numéro que la modale a envoyé |
| le repli existe pour le **désarchivage** | `app_restore_annonce_optimistic`, chemin 2 |
| il **manque** pour le **changement de statut** | `app_change_annonce_status_optimistic` n'a que le chemin 1 → `dossier_not_found` |

➡ **Le correctif est petit, additif, et il a un modèle éprouvé** : ajouter à la fonction de statut
le même repli (index historique par `app_historical_id`, et index des archives par
`app_archive_id`). Rien à changer dans l'écran.

#### 🔴 ET CET ESSAI A TROUVÉ UN DÉFAUT DANS LE PATCH 3a — l'étiquette « Mandat clos »

Mon bloc écrit `statut_annonce = 'Mandat clos'` pour la cible `closed`, parce que j'ai repris
`config.label` du worker. **C'est l'étiquette de l'écran, pas la valeur de la donnée.** Mesure :

| Où | « Clos » | « Mandat clos » |
|---|---|---|
| index des archives | **34 781** | **0** |
| index historique | **135** | **0** |

*(et `app_statut_rang` range déjà « Estimation, Clos, vide » hors échelle — c'est bien `Clos`.)*
Le worker lui-même le dit : l'API rend `annonce.statut = {"id":"6","name":"Clos"}`.

**Ce que ça abîme, et ce que ça n'abîme pas** *(chacun vérifié)* :

| | |
|---|---|
| la fiche, pendant ~73 s | affiche « Mandat clos » au lieu de « Clos » — **cosmétique**, la relecture corrige |
| la vitrine, la page RDV publique, l'échelle des statuts, le déclencheur du rapprochement | **aucun effet** : les quatre excluent `Clos` **et** `Mandat clos` de la même façon |
| 🔴 **le CARNET** | il **garde** « Mandat clos » pour toujours *(la relecture ne le touche pas)* — or c'est lui qui doit faire foi après la coupure. **2 lignes concernées aujourd'hui, sur 62963.** |

➡ **Correctif à faire** : dans le bloc, `'closed' → 'Clos'` *(une seule chaîne)*, et remettre la
ligne de carnet de 62963 à `Clos`. Les quatre autres cibles sont justes
*(Actif · Sous offre · Sous compromis · Vendu)*.

#### 🔎 AUDIT ÉLARGI (12/10, 20 h 30) — *« avant on pouvait réactiver une annonce vendue »* : **VRAI**, et voici quand ça s'est cassé

Frédéric a refusé ma conclusion et m'a demandé de chercher. Il avait raison **deux fois** : le
mécanisme existe, et **ça marchait avant**. Les dates, prises dans `git log -S` :

| Date | Ce qui a changé | Effet |
|---|---|---|
| **20/05/2026** | `f71d41d` « Add lightweight historical listing index » — les **Vendu** et **Clos** non archivés sortent du parc vivant pour aller dans l'index **historique** *(filtre : `COALESCE(detail_statut_name, statut_annonce,'') IN ('Vendu','Clos')`)* | ils ne sont plus dans `app_dossier_current`… mais à l'époque les gestes **n'avaient pas de garde** : l'écran insérait le travail directement |
| **25/08/2026** | `dbaf979` C.4 lot 1 — le changement de statut passe par la **RPC** `app_change_annonce_status_optimistic`, qui commence par `select … from app_dossier_current … if not found then raise 'dossier_not_found'` | 🔴 **c'est là que ça casse** : depuis le 25/08, un bien vendu ou clos ne peut plus changer de statut |
| **30/08/2026** | `e7b9df7` C.4 — archiver / désarchiver passent à leur tour par une RPC | même effet pour les **archives** *(le worker le dit : « dernier désarchivage réussi : 30/08 à 07:42 »)* |
| **08/10/2026** | **5a** — on ajoute à `app_restore_annonce_optimistic` le **repli sur l'index des archives** | ✅ le désarchivage est réparé — **pour les archives seulement** |

➡ **Le défaut d'aujourd'hui est EXACTEMENT celui de 5a, dans une autre case du tableau.**

#### Le tableau complet — 8 fonctions lèvent `dossier_not_found`, **une seule** a un repli

| Fonction | geste | repli index **archives** | repli index **historique** |
|---|---|---|---|
| `app_restore_annonce_optimistic` | désarchiver | ✅ **oui** *(5a)* | ❌ NON |
| `app_change_annonce_status_optimistic` | changer le statut | ❌ NON | ❌ NON |
| `app_archive_annonce_optimistic` | archiver | ❌ NON | ❌ NON |
| `app_assign_negotiator_optimistic` | changer de négociateur | ❌ NON | ❌ NON |
| `app_edit_annonce_optimistic` | modifier les champs | ❌ NON | ❌ NON |
| `app_action_status` · `app_annonce_edit_status` · `app_annonce_pending_resolve` | lectures de service | ❌ NON | ❌ NON |

**Le volume concerné** *(mesuré le 12/10)* :

| | annonces | ce qu'on peut en faire |
|---|---|---|
| index des **archives** | **35 318** *(dont 34 781 Clos, 425 Vendu)* | **désarchiver** seulement |
| index **historique** | **8 941** *(8 806 Vendu, 135 Clos)* | **rien** |
| **total hors parc vivant** | **44 259** | |

**Et l'écran ne prévient pas** : pour un bien historique il affiche quand même « Faire évoluer le
statut de l'annonce », la modale s'ouvre, le bouton part — et rend `dossier_not_found` brut.

**Ce que ça ne remet pas en cause** : rien du patch 3a *(la garde est d'origine, antérieure au
25/08 ; elle est dans l'empreinte `302852e8…`)*. Mais ça change la **taille** du sujet, et c'est
à Frédéric d'arbitrer le périmètre.

#### ❓ « POURQUOI AVONS-NOUS CASSÉ CELA ? » — la réponse, en quatre temps

**1. La garde n'est pas une bêtise, elle est nécessaire.** Ces fonctions existent pour écrire
**chez nous d'abord** ; pour ça elles doivent lire la ligne du bien — son n° Hektor, son n° de
dossier, son titre — et, depuis le chantier ②, vérifier les droits dessus. `select … into d from
app_dossier_current … if not found then raise 'dossier_not_found'` est l'ouverture **normale** des
8 fonctions, et elle protège d'un numéro inventé.

**2. Ce qu'on a cassé, c'est une HYPOTHÈSE, pas du code** : *« tout bien que l'écran peut montrer
est dans `app_dossier_current` »*. Elle est devenue fausse le **20/05**, quand **44 259** biens
sont partis dans deux index annexes pour alléger l'app — **trois mois AVANT** que la première de
ces fonctions soit écrite (**25/08**). Les deux chantiers ne se sont jamais rencontrés : celui de
mai ne pouvait pas prévoir les RPC d'août, et celui d'août a hérité d'une hypothèse déjà périmée.

**3. Pourquoi personne ne l'a vu pendant six semaines.** Le geste est **rare** *(15 désarchivages
en trois mois)*, l'échec n'est pas silencieux mais il est **incompréhensible** — le code brut
`dossier_not_found` — et **aucune sonde** ne surveille ça. Un geste qu'on ne fait pas souvent, qui
échoue en jargon, ne remonte pas.

**4. Et pourquoi je ne l'ai pas vu le 08/10, moi.** Frédéric avait signalé *« désarchiver est
impossible »* ; j'ai audité **ce geste-là**, trouvé **cette cause-là**, et réparé **cette case-là**
— une fonction, un index. Je n'ai pas balayé les **sept autres cases** du tableau, alors que la
cause était manifestement commune. C'est exactement la règle que Frédéric avait posée le 21/09 et
qui est en tête de `CLAUDE.md` : **« UN AUDIT BALAIE LES OBJETS *ET* LES GESTES »**. Je l'ai
appliquée à un geste, pas à la famille.

➡ **La leçon, à retenir pour les chantiers suivants** : quand une cause est **structurelle**
*(ici : « la fonction suppose que le bien est dans le parc vivant »)*, le correctif doit balayer
**toutes les fonctions qui partagent cette supposition**, pas seulement celle qui a été signalée.
Le signalement désigne un symptôme, jamais le périmètre.

---

## ③-REPLI — « VAS-Y B » (12/10, 21 h) : rendre les 44 259 biens manipulables

### ÉTAPE 1 — audit des 5 fonctions (lecture seule) — **B se fait en 3, pas en 5**

| Geste | Fonction | Faisable avec le patron 5a ? |
|---|---|---|
| **changer le statut** | `app_change_annonce_status_optimistic` | ✅ **oui** — le travail n'a besoin que du n° Hektor |
| **archiver** | `app_archive_annonce_optimistic` | ✅ **oui** — idem *(le worker n'utilise `app_dossier_id` que pour le journal, l. 19953)* |
| **changer de négociateur** | `app_assign_negotiator_optimistic` | ✅ **oui** — le worker rattrape déjà l'absence de dossier *(l. 14737-14746)* |
| désarchiver | `app_restore_annonce_optimistic` | ⚪ **sans objet** pour l'index historique : un bien vendu/clos **non archivé** porte déjà `archive='0'`, il n'y a rien à désarchiver. Le repli sur les archives existe déjà *(5a)*. |
| modifier les champs | `app_edit_annonce_optimistic` | ❌ **non — ce n'est pas un repli, c'est un autre chantier.** Toute la fonction est bâtie sur le n° de dossier : le **calque** (`app_dossier_detail_current`), la **file d'attente de 10 min** (`app_annonce_pending`, dont le n° de dossier est la **clé primaire**) et le **rapprochement**. Et **l'écran l'interdit délibérément** : *« Lecture seule jusqu'à désarchivage »* (`App.tsx:30621`, `:30022`). |

➡ **B = 3 patchs, un par geste** *(règle `CLAUDE.md` §0 : « une seule tâche en code à la fois »)*.
Celui-ci est **le 1er : le statut**. ⚠ **Question qui reste à Frédéric** : veut-il qu'on ouvre
aussi la **modification des champs** d'un bien hors parc ? C'est un vrai sujet, pas un repli.

### ÉTAPE 2/3 — le correctif du geste « statut » (écrit, **pas appliqué**)

**Ce qu'il fait** : 7 remplacements, chacun vérifié **unique** avant d'être fait.

| | |
|---|---|
| **R1** | la garde d'entrée : parc vivant → sinon index des **archives** (`app_archive_id`) → sinon index **historique** (`app_historical_id`) → sinon `dossier_not_found` comme avant |
| **R2** | le contrôle des droits reçoit `d.app_dossier_id` *(NULL hors parc ; admin/manager ne s'en sert pas)* |
| **R3** | ⚠ **ma correction** : `'Mandat clos'` → **`'Clos'`** |
| **R4** | l'écriture de la fiche vise `d.app_dossier_id` → **0 ligne** touchée hors parc, rien ne casse |
| **R5-R6** | le carnet vise `d.app_dossier_id` **et ne s'écrit que si ce numéro existe** |
| **R7** | le travail Hektor porte `d.app_dossier_id` *(NULL hors parc)*, **jamais un faux numéro** |

**⭐ La règle de 5a, reprise mot pour mot** : hors parc vivant, `d.app_dossier_id` **reste NULL**.
Y écrire le numéro d'index serait poser un **faux identifiant** — la faute même de 5d et 5g.

**⚠ Le repli ne sert que « Actif » et « Mandat clos ».** Une offre, un compromis ou une vente
créent une ligne d'affaire qui exige un vrai numéro de dossier : hors parc, ces trois cibles sont
refusées avec un message qui le **dit** (`transaction_hors_parc_vivant`) au lieu du
`dossier_not_found` d'avant.

#### ⚠ Ce que ça pourrait casser ailleurs — chacun vérifié le 12/10

| | |
|---|---|
| le chemin du bien **vivant** (13 475 biens) | les 2 lignes d'origine sont **conservées mot pour mot** → comportement inchangé *(éprouvé par l'essai B de la répétition)* |
| **les droits** | `app_console_can_request_job('change_hektor_annonce_status', …)` rend vrai pour admin/manager **sans se servir du n° de dossier** *(lu dans la base)* — un négociateur reste refusé |
| **le worker** | `handleChangeHektorAnnonceStatus` rattrape déjà l'absence de dossier *(l. 14389-14399)* et n'a besoin que du n° Hektor → **AUCUN redémarrage** |
| **la base** | aucune contrainte de clé étrangère sur `app_console_job.app_dossier_id` ; il accepte `NULL` *(déjà le cas pour les désarchivages depuis le 08/10)* |
| **l'écran** | rien à changer : il envoie déjà `app_archive_id` / `app_historical_id` *(`api.ts:2624`)* |
| **les numéros** | ⭐ mesuré : **0 collision** archives×historique, archives×parc, historique×parc *(35 318 et 8 941 lignes)* → l'ordre de recherche est sans ambiguïté |
| **le registre des affaires** | protégé : les 3 cibles de transaction restent interdites hors parc vivant |
| **le filet de rejeu** | inchangé *(il rejoue par `job_type`, pas par dossier)* |

**Retour arrière** : `…_INVERSE.sql` refait les 7 remplacements à l'envers et ne réexécute que si
l'on retombe **exactement** sur `1f9e987f…`. *(⚠ il remet aussi « Mandat clos » : pour garder la
correction d'étiquette, retirer la paire R3 des deux tableaux avant de le lancer.)*

**Le contrôle** : `…_REPETITION.sql` — patch + **6 essais réels** (hors parc, bien vivant, archive
réelle, refus d'un compromis hors parc, numéro inventé, et l'étiquette) + le vrai inverse + une
erreur finale qui annule tout.

---

## 🔎 AUDIT DEMANDÉ PAR FRÉDÉRIC (12/10, 21 h 30) — *« il nous manque quelque chose »*

> *« normalement les 3 index sont dans l'app mais sans les détails donc l'id etc. Avant un bien
> en index vendu pouvait être modifié… cherche dans mon historique, il nous manque quelque
> chose. »*

**Il avait raison, et la pièce manquante était dans l'écran.** Je l'ai trouvée en lisant
`isReadOnlyLightweightDetail` (`App.tsx:406-411`) :

```
if (item.archive === '1')      return true   // une ARCHIVE est toujours en lecture seule
if (item.is_brouillon === true) return true   // un BROUILLON aussi
return isHistoricalListingStatus(item.statut_annonce)   // Vendu ou Clos …
       && !hasDetailCacheAvailable(item)                // … MAIS SEULEMENT TANT QUE LE DÉTAIL
                                                        //     N'EST PAS TÉLÉCHARGÉ
```

➡ **La règle voulue, posée le 21/05/2026** *(`5faf38a`, `079ce84`, `08b73ae`)* :

| Famille | État | Comment on en sort |
|---|---|---|
| **archivée** (35 318) | **lecture seule, toujours** | « Désarchiver » — ✅ réparé le 08/10 (5a) |
| **brouillon** (~485) | lecture seule, toujours | — |
| **vendue / close** (8 941) | lecture seule **tant que le détail n'est pas téléchargé** ; **une fois téléchargé, la fiche redevient PLEINEMENT manipulable** *(2 h, le TTL du cache)* | — *(c'est la règle elle-même)* |

**C'est exactement ce que Frédéric se rappelait**, et c'est exactement ce que j'ai observé à
l'écran : après « Télécharger le détail », la bannière « lecture seule » disparaît et le bouton
**« Faire évoluer le statut de l'annonce » est là**.

### ⛔ CE QUI MANQUE : L'ÉCRAN A TROIS ÉTATS, LA BASE N'EN A QU'UN

```
L'ECRAN (depuis le 21/05)              LA BASE (depuis le 25/08)
  1. bien vivant        -> tout         dans app_dossier_current  -> tout
  2. index, sans detail -> lecture seule
  3. index, AVEC detail -> TOUT         <-- cet etat n'existe pas cote base
                                            -> « dossier_not_found »
```

**Le contrat de l'écran n'a jamais été appris par les fonctions.** Les RPC « optimistes » ont été
écrites les **25/08** *(statut, `dbaf979`)* et **30/08** *(archiver / désarchiver, `e7b9df7`)*,
trois mois après la règle de l'écran, et elles ne connaissent qu'une seule question : *« ce bien
est-il dans le parc vivant ? »*. Le bouton reste affiché, il part, et il échoue — en jargon.

### ❓ « Pourquoi alors les workers ne fonctionnent pas sur les 2 index ? »

**Ils fonctionneraient.** Mesuré, les trois gestionnaires n'ont besoin que du **numéro Hektor** :

| Worker | Preuve |
|---|---|
| `handleChangeHektorAnnonceStatus` | l. 14389-14399 : `loadDossier` dans un `try/catch`, repli sur le seul `hektor_annonce_id` |
| `handleAssignHektorAnnonceNegotiator` | l. 14737-14746 : même repli, `app_dossier_id: … || null` |
| `handleArchiveHektorAnnonce` | l. 19952-19953 : `app_dossier_id` n'est utilisé **que pour le journal** |
| `handleRestoreHektorAnnonce` | déjà prouvé par 5a : 15 travaux réussis, `app_dossier_id` toléré nul |

➡ **Le worker n'est jamais appelé.** Le refus a lieu **avant lui**, dans la fonction qui crée le
travail. Ce n'est pas un problème de worker : c'est **une porte fermée devant la porte**.

### La chronologie complète

| Date | | |
|---|---|---|
| **20/05** | `f71d41d` | les Vendu/Clos sortent du parc vivant → index historique |
| **21/05** | `5faf38a` + `079ce84` + `08b73ae` | la règle de l'écran : **télécharger le détail rend le bien manipulable** ; et les gestes marchent, car le front **insère le travail directement** |
| **25/08** | `dbaf979` | le statut passe par une RPC qui exige le parc vivant → 🔴 **cassé pour les 8 941 vendus/clos** |
| **30/08** | `e7b9df7` | archiver/désarchiver passent par une RPC → 🔴 cassé aussi pour les 35 318 archives |
| **08/10** | 5a | repli sur l'index des archives — ✅ **mais pour le seul désarchivage** |
| **12/10** | *aujourd'hui* | on mesure le reste : 4 gestes sur 5, et l'index historique entier |

### Ce que ça change pour le correctif

Le repli que j'avais écrit **va dans le bon sens mais ne dit pas la bonne règle**. La règle de la
maison n'est pas *« on accepte un bien hors parc »*, c'est :

> **un bien vendu/clos DONT LE DÉTAIL A ÉTÉ TÉLÉCHARGÉ redevient manipulable ;
> une archive, elle, reste en lecture seule jusqu'au désarchivage.**

⚠ Donc le repli ne devrait PAS traiter les deux index pareil : l'index des **archives** doit
**rester refusé** pour le statut *(la lecture seule y est voulue, et la sortie s'appelle
« Désarchiver »)*, et seul l'index **historique** doit passer — en vérifiant, comme l'écran, que
le détail est bien là *(`app_historical_annonce_detail_cache`, `expires_at > now()`)*.

**➡ Mon patch écrit ce soir est donc à REFAIRE sur cette règle. Rien n'a été appliqué.**

### ⭐⭐ LE NOM DE LA COLONNE MENTAIT — ET ÇA CORRIGE LA NOTE 5a DU 08/10

Frédéric : *« on est d'accord, on a bien les deux id du bien sur tous les index »*. **Oui** — et
c'est **mesuré**, pas déduit. Les trois index sont fabriqués par la même ligne de SQL :

```
export_app_payload.py:316   CAST(app_dossier_id AS INTEGER) AS app_archive_id
export_app_payload.py:363   CAST(app_dossier_id AS INTEGER) AS app_historical_id
export_app_payload.py:451   CAST(app_dossier_id AS INTEGER) AS app_brouillon_id
```

**`app_archive_id`, `app_historical_id` et `app_brouillon_id` NE SONT PAS des séries à part :
c'est NOTRE `app_dossier_id`, simplement renommé.** Preuve croisée par un chemin indépendant —
le numéro de dossier que portaient les ANCIENS travaux du même bien :

| annonce Hektor | numéro dans l'index | `app_dossier_id` de ses anciens travaux | |
|---|---|---|---|
| 24933 *(archivée)* | **1 352 132** | **1 352 132** | ✅ identique |
| 62963 *(historique)* | **5 880 239** | **5 880 239** | ✅ identique |

➡ **Les quatre ensembles (vivant · archives · historique · brouillons) PARTAGENT la même série de
numéros** et se partagent le parc sans recouvrement. Les « 0 collision » mesurés plus haut ne sont
donc pas une chance du jour : c'est **structurel**.

#### ⚠ CE QUE ÇA CORRIGE DANS LA NOTE 5a (08/10)

Elle écrivait : *« L'index des archives n'a pas de numéro de dossier ; l'écran envoie donc son
`app_archive_id` à cette place »*, et la fonction pose en conséquence `v_dossier := null`, avec ce
commentaire : *« nous n'avons AUCUN numero de dossier pour une archive »*.

**La prémisse est fausse.** Le numéro de dossier est là, dans la colonne, sous un autre nom. La
mesure qui avait servi — *« 0 des 35 317 `app_archive_id` n'existe comme `app_dossier_id` »* — ne
disait pas *« ce n'est pas un numéro de dossier »* ; elle disait seulement *« aucune archive n'est
dans la table des vivants »*, ce qui est la définition d'une archive. **J'ai lu une tautologie
comme une preuve.**

**Conséquences, deux :**
1. les travaux de désarchivage posés depuis le 08/10 portent `app_dossier_id = NULL` **alors qu'on
   avait le vrai numéro** → le bandeau « geste abandonné » ne les voit pas *(la « limite connue »
   écrite dans la note 5a n'était pas une fatalité, c'était cette erreur)* ;
2. le repli n'a **pas** besoin de la gymnastique « marqueur NULL » que j'avais prévue ce soir :
   `target_dossier_id` **est** notre numéro de dossier, on l'écrit normalement, partout. **Le
   correctif devient plus simple et plus juste.**

### 📜 LA RÈGLE ARRÊTÉE PAR FRÉDÉRIC (12/10)

> *« base-toi sur les règles actuelles : vendu, on peut modifier le statut etc. comme
> actuellement ; les archives, uniquement désarchivage et lecture seule. »*

| Index | Ce qui est permis | Ce qui reste refusé |
|---|---|---|
| **historique** (vendu / clos, 8 941) | **les gestes, comme aujourd'hui à l'écran** | — |
| **archives** (35 318) | **désarchiver seulement** *(déjà fait, 5a)* | tout le reste : lecture seule, c'est voulu |
| **brouillons** (~485) | — | lecture seule, c'est voulu |

➡ **Le repli ne porte donc que sur l'index HISTORIQUE** — l'index des archives n'y entre pas.
C'est plus petit, plus sûr, et c'est la règle de la maison.

### ÉTAPE 3 — LE PATCH RÉÉCRIT SUR LA RÈGLE DE FRÉDÉRIC (12/10, 22 h)

Les fichiers de 21 h sont **remplacés** *(ils n'avaient jamais été appliqués)*. Le correctif est
**beaucoup plus petit** qu'annoncé, grâce à la découverte sur les numéros :

| | Avant *(version de 21 h, jetée)* | Maintenant |
|---|---|---|
| remplacements | **7** | **2** |
| index acceptés | archives **et** historique | **historique seul** *(l'archive reste en lecture seule)* |
| numéro de dossier | mis à **NULL** *(« faux identifiant »)* | **gardé tel quel** — c'est le vrai |
| carnet, droits, travail | à réécrire | **inchangés**, ils fonctionnent déjà |

**R1 — la garde.** parc vivant → sinon **index historique** → sinon, si c'est une **archive**, un
refus qui le dit (`annonce_archivee_lecture_seule`) → sinon `dossier_not_found`, comme avant. Et
hors parc vivant, **Offre / Compromis / Vendu** restent refusés (`transaction_hors_parc_vivant`) :
ils créent une ligne au registre des affaires, qui se tient sur un bien en vie.

**R2 — l'étiquette** : `'Mandat clos'` → `'Clos'`.

**Ce que la garde remplit en plus** : `statut_annonce`, `diffusable` et `archive` sont lus dans
l'index → l'**état d'avant** rangé dans la charge du travail est enfin **juste** pour un bien
vendu/clos *(il aurait été vide sinon)*.

#### Les 7 essais de la répétition

| | Essai | Attendu |
|---|---|---|
| **A** | vendu/clos 62963 → « Actif » | **marche** : travail avec **5880239** *(notre vrai numéro)* et 62963 ; carnet `statut=Actif / diffusable=1` ; charge `statut_avant=Clos / diffusable_avant=0` |
| **B** | bien vivant 62774 → « Actif » | **inchangé** : travail avec 3828957, fiche `Actif / diffusable=1`, carnet 3 lignes |
| **C** | archive 49544 → « Mandat clos » | **refusé**, `annonce_archivee_lecture_seule` |
| **D** | vendu/clos → « Compromis » | **refusé**, `transaction_hors_parc_vivant` |
| **E** | numéro inventé | **refusé**, `dossier_not_found` *(comme avant)* |
| **F** | bien vivant → « Clos » | carnet `statut = Clos` *(témoin de la correction d'étiquette)* |
| **G** | **désarchiver** l'archive 49544 | **marche toujours** — preuve qu'on n'a pas fermé la seule sortie des archives |

⚠ L'essai **G** imprimera aussi `app_dossier_id = NULL` : c'est le **défaut 5a** décrit plus haut
*(le vrai numéro était disponible)*. **Il n'est PAS corrigé ici** — c'est une autre fonction, et
une autre tâche.

#### ⚠ LA RÉPÉTITION S'EST ARRÊTÉE — et la cause est un piège déjà payé le 08/10

`ESSAI IMPOSSIBLE -- ancre R1 trouvee 0 fois`, **alors que la garde d'empreinte était passée**.

**Cause, mesurée en lecture seule** : `v_def` est lu **sans** les retours chariot
*(`replace(…, chr(13), '')`)*, mais **le script collé depuis Windows en porte**. Le même texte,
cherché dans le corps de la fonction :

| forme de l'ancre | occurrences |
|---|---|
| **LF** | **1** |
| **CRLF** | **0** |

L'ancre **R2** tient sur **une seule ligne** → elle matchait (1). L'ancre **R1** fait **deux
lignes** → elle portait un `\r` que le corps n'a pas. ⚠ **C'est pour ça que le patch 3a était
passé du premier coup** : toutes ses ancres tenaient sur une ligne. *L'absence de symptôme ne
prouvait pas que le script était insensible aux fins de ligne.*

**Correctif** *(appliqué aux trois fichiers)* : on normalise **les deux côtés**, pas seulement la
fonction —

```sql
FOR i IN 1 .. array_length(a, 1) LOOP
  a[i] := replace(a[i], chr(13), '');
  b[i] := replace(b[i], chr(13), '');
END LOOP;
```

➡ mémoire élargie : `empreinte-md5-faussee-par-fins-de-ligne-windows`.

#### ✅ RÉPÉTITION (12/10, 22 h 30) — **20 mesures sur 20, exactes**

| | Mesure | Résultat |
|---|---|---|
| avant | empreinte `1f9e987f…`, taille **12 342**, ancres **R1=1 R2=1** | ✅ |
| après | taille **14 685** *(+2 343)* — et le chemin **inverse** rend `1f9e987f…` | ✅ **rien d'autre n'a changé** |
| **A** vendu/clos 62963 → Actif | travail `app_dossier_id=`**5880239** *(notre vrai numéro)*, hektor **62963**, charge `statut_avant=Clos / diffusable_avant=0`, carnet `diffusable=1 \| statut=Actif`, 0 ligne de fiche | ✅ **le geste marche** |
| **B** bien vivant 62774 → Actif | travail `3828957`, fiche `Actif / diffusable=1`, carnet 3 lignes | ✅ **inchangé** |
| **C** archive 49544 → Mandat clos | `annonce_archivee_lecture_seule` | ✅ **refusé, et ça le dit** |
| **D** vendu/clos → Compromis | `transaction_hors_parc_vivant` | ✅ refusé |
| **E** numéro inventé | `dossier_not_found` | ✅ conservé |
| **F** l'étiquette | carnet `statut = Clos` | ✅ **corrigé** |
| **G** désarchiver l'archive | travail créé, hektor 49544 | ✅ **la sortie des archives est intacte** |
| après l'inverse | empreinte `1f9e987f…`, **0 marqueur** | ✅ **le repli disparaît** |

*(G confirme au passage le défaut 5a : `app_dossier_id = NULL` alors que le vrai numéro existe —
noté, non corrigé ici.)*

### ÉTAPE 5 — CONTRÔLE (12/10, 22 h 25) — **appliqué, et prouvé en réel**

**Le patch en base** : taille **14 685**, 2 marqueurs, lit bien l'index historique, refus d'archive
clair, étiquette corrigée *(« Mandat clos » ne subsiste que dans deux **commentaires**)* ·
`SECURITY DEFINER`, propriétaire `postgres`, `search_path` intacts · droits
`postgres / authenticated / service_role` — **`anon` toujours absent**.

**L'essai réel : le geste qui était IMPOSSIBLE il y a deux heures a réparé le bien d'essai.**

| 20:23:39 | clic « Actif » sur **62963**, alors **Clos et hors du parc vivant** |
|---|---|
| tout de suite | travail créé avec **`app_dossier_id = 5880239`** *(notre vrai numéro, pas NULL)*, `hektor = 62963`, état d'avant **`Clos / 0`**, carnet déjà à `statut=Actif \| diffusable=1` |
| +31 s | Hektor confirme |
| +45 s | relecture terminée |
| **au final** | **le bien est revenu au parc vivant** : `Actif / diffusable=1` — **son état d'origine, au caractère près** · il est sorti de l'index historique (0) · badge **Actif** à l'écran |

➡ **62963 est réparé.** Le geste de 18:19 qui l'avait laissé en Clos est annulé par le geste que
ce patch vient de rendre possible.

#### Vérification demandée par Frédéric : « vérifie les autres gestes »

**① Aucune autre fonction n'a bougé** — empreintes comparées à celles de ce matin, **identiques
au caractère près** :

| Fonction | ce matin | maintenant |
|---|---|---|
| `app_archive_annonce_optimistic` | `b9bf9d40…` | **`b9bf9d40…`** ✅ |
| `app_assign_negotiator_optimistic` | `275f8d9d…` | **`275f8d9d…`** ✅ |
| `app_edit_annonce_optimistic` | `5eb2c1a4…` | **`5eb2c1a4…`** ✅ |
| `app_restore_annonce_optimistic` | `70957146…` | **`70957146…`** ✅ |

**② Ce qui marche aujourd'hui sur un bien VENDU / CLOS** *(mesuré dans la base)* :

| Geste | marche sur vendu/clos ? |
|---|---|
| **changer le statut** | ✅ **OUI — depuis ce soir** |
| archiver | ❌ non — **reste à faire** |
| changer de négociateur | ❌ non — **reste à faire** |
| modifier les champs | ❌ non — *autre chantier (file d'attente bâtie sur le n° de dossier)* |
| désarchiver | ⚪ sans objet *(un vendu/clos n'est pas archivé)* |

**③ Et les archives n'ont rien perdu** : `app_restore_annonce_optimistic` est intacte, et l'essai
**G** de la répétition a prouvé que le désarchivage crée toujours son travail.

### ÉTAPE 3 (suite) — LES DEUX GESTES QUI RESTENT : **archiver** et **changer de négociateur**

**Un seul patch pour les deux fonctions**, et c'est justifié : elles portent la **même garde au
caractère près**, et on y insère le **même bloc**. Les séparer n'ajouterait aucune sécurité —
chacune garde **sa propre empreinte d'entrée et son propre contrôle de sortie** — et obligerait à
coller deux fois. Si l'une échoue, la transaction annule **les deux**.

| Fonction | empreinte d'entrée | taille | ancre |
|---|---|---|---|
| `app_archive_annonce_optimistic` | `b9bf9d40d32be0a16959ee4a35548ac9` | 1 909 | **1** |
| `app_assign_negotiator_optimistic` | `275f8d9d1000fb4100889c10314c8cf5` | 2 563 | **1** |

**Le bloc est le même qu'au geste « statut »**, moins la garde des transactions *(elle n'a pas
d'objet ici)*, plus un message de refus **adapté au geste** :

- **archiver** une archive → `annonce_deja_archivee` *(elle l'est déjà)* ;
- **négociateur** sur une archive → `annonce_archivee_lecture_seule`.

**Ce qui ne change pas** : le chemin du bien vivant *(deux lignes conservées mot pour mot)* · les
archives *(refusées avant, refusées après — seul le message change)* · le désarchivage · les
droits *(admin/manager, sans se servir du n° de dossier)* · les workers
*(`handleArchiveHektorAnnonce` n'utilise `app_dossier_id` que pour le journal,
`handleAssignHektorAnnonceNegotiator` rattrape déjà son absence)* → **aucun redémarrage** ·
l'écran.

**Les 8 essais de la répétition** : archiver un **vendu** *(bien 284 / annonce 107)* → doit
marcher avec le vrai numéro et écrire `archive=1` au carnet · archiver une **archive** → refusé ·
archiver un bien **vivant** → inchangé · les trois mêmes pour le **négociateur** · et deux numéros
inventés qui doivent rester refusés. Puis le vrai inverse, et une erreur finale qui annule tout.

#### ✅ RÉPÉTITION des gestes 2 et 3 (13/10, 00 h 10) — **16 mesures sur 16, exactes**

| | Résultat |
|---|---|
| empreintes d'entrée · ancres | `b9bf9d40…` et `275f8d9d…` · **1 et 1** ✅ |
| **empreintes NUES après le patch** | **identiques à celles d'avant** → rien d'autre n'a changé ✅ |
| **A1** archiver un **vendu** (107) | travail `app_dossier_id=`**284** *(notre vrai numéro)*, hektor **107**, carnet `archive=1` ✅ |
| **A2** archiver une archive | `annonce_deja_archivee` ✅ |
| **A3** archiver un bien vivant | `3828957` — **inchangé** ✅ |
| **B1** négociateur sur le vendu | **284**, hektor **107**, carnet `negociateur_email=…` ✅ |
| **B2** négociateur sur une archive | `annonce_archivee_lecture_seule` ✅ |
| **B3** négociateur sur un bien vivant | `3828957` — **inchangé** ✅ |
| **C1 / C2** numéros inventés | `dossier_not_found` des deux côtés ✅ |
| après l'inverse | **les deux empreintes reviennent**, 0 marqueur ✅ |

---

## 🔧 LE DÉFAUT 5a — « les désarchivages posent un numéro vide alors que le vrai existe »

### ÉTAPE 1 — AUDIT (13/10, lecture seule) — verdict : **CONFIRMÉ**, et la prémisse est fausse à grande échelle

**La prémisse de 5a, éprouvée sur TOUT le parc** *(et non plus sur un cas)* : pour chaque archive,
on compare son `app_archive_id` au `app_dossier_id` que portent ses **anciens travaux** —

| | |
|---|---|
| archives recoupées | **35 318** *(toutes : le rattrapage documents leur a créé des travaux)* |
| `app_archive_id` = le numéro de dossier de leurs travaux | **35 312** |
| écarts | **6** — et ce sont des **fantômes déjà réconciliés** : ces 6 biens ont **deux** numéros dans leur histoire, et **le plus récent est bien `app_archive_id`** |

➡ **35 318 sur 35 318. `app_archive_id` EST notre `app_dossier_id`.** La phrase de la note 5a —
*« nous n'avons AUCUN numéro de dossier pour une archive »* — est fausse, et avec elle la
justification *« y écrire le numéro d'archive serait poser un FAUX identifiant »*.

**Ce que ça coûte aujourd'hui — mesuré, et c'est petit** : `restore_hektor_annonce` compte
**16 travaux** depuis le 21/05, tous `done`, dont **1 seul** sans numéro de dossier *(l'essai réel
du 08/10)*. **Le défaut est donc surtout devant nous**, pas derrière.

**Les deux conséquences, vérifiées dans le code :**

1. **Le bandeau « geste abandonné » ne voit rien.** `GesteAbandonneBanner` (`App.tsx:32925-32939`)
   appelle `loadActionStatus(dossier.app_dossier_id)` : un travail sans numéro lui est invisible.
2. **Le filet de rejeu ne peut pas détecter un geste dépassé.** Sa boucle 0 compare
   `plus_recent.app_dossier_id = j.app_dossier_id` : `NULL = NULL` n'est jamais vrai, donc un
   désarchivage qu'un geste plus récent a déjà mené à bien **serait rejoué** au lieu d'être
   abandonné.

### ÉTAPE 2 — LE CORRECTIF PROPOSÉ (écrit, **attend le « vas-y »**)

**Une seule ligne de code** *(plus deux commentaires devenus faux, corrigés en même temps —
laisser un commentaire qui contredit le code, c'est préparer la prochaine erreur)* :

```
    v_dossier := null;              -- « nous n'avons AUCUN numero de dossier »   ← faux
    v_dossier := target_dossier_id; -- le numero recu EST notre app_dossier_id (35 318/35 318)
```

Tout le reste suit **tout seul** : le `if v_dossier is not null` plus bas écrit alors la ligne de
carnet `archive='0'` *(aujourd'hui sautée pour toute archive)*, et le travail porte le vrai numéro.

#### ⚠ Ce que ça pourrait casser ailleurs — chacun vérifié

| | |
|---|---|
| **les droits d'un négociateur** ⚠ *(le vrai point)* | `restore_hektor_annonce` est **dans la liste des gestes ouverts au commercial**, donc le numéro part dans `app_console_can_access_dossier`. **Lue dans la base** : elle teste `(le numéro de dossier correspond) OU (le numéro Hektor correspond)`, sur **les trois sources** *(vivants, archives, historique)*. Aujourd'hui, avec un numéro vide, c'est la branche Hektor qui tranche ; demain les deux branches désigneront **le même bien** *(0 collision sur les séries)*. ➡ **le résultat ne peut pas devenir plus permissif sur un autre bien** |
| le worker | `handleRestoreHektorAnnonce` tolère les deux *(prouvé par 5a)* — et recevra enfin le vrai numéro |
| le filet de rejeu | **il s'améliore** : la détection du « geste dépassé » redevient possible |
| le carnet | 1 ligne de plus par désarchivage, `origine='geste_desarchiver'` — **relue par personne** aujourd'hui *(`CHAMPS_APP_ANNONCE` est vide)* → aucun changement de comportement |
| le chemin du bien **vivant** | **pas touché** : la ligne modifiée est dans la branche « archive » |
| les 16 travaux existants | **pas touchés** — on ne réécrit pas le passé |

**Retour arrière** : script inverse qui repose la ligne d'origine, avec contrôle que l'empreinte
revient à **`709571469083a76b1be384e879ca523b`**.

**Le contrôle** : une répétition — désarchiver une **vraie archive** *(15633 / annonce 49544)* doit
créer un travail portant **`app_dossier_id = 15633`** et écrire `archive=0` au carnet · un bien
**vivant** doit rester **inchangé** · un numéro inventé reste refusé · et l'empreinte doit revenir
après l'inverse.

### ÉTAPE 4 et 5 — le défaut 5a : **répétition exacte, puis essai réel CHEZ HEKTOR**

**Répétition** — et son premier essai est **le témoin d'avant** :

| | Mesure | Résultat |
|---|---|---|
| **A0** *(avant le patch)* | désarchiver l'archive 49544 | travail `app_dossier_id = `**NULL** — **le défaut, en direct** ✅ |
| **A** *(après)* | le même geste | **15633**, hektor **49544**, carnet **`archive=0 (geste_desarchiver)`** ✅ |
| **B** | un bien vivant | `3828957`, **inchangé** ✅ |
| **C** | numéro inventé | `dossier_not_found` ✅ |
| empreinte **retour** | 3 557 → 4 167 puis retour | **`709571469083a76b1be384e879ca523b`** des deux côtés ✅ |

**Patch appliqué**, contrôlé en base : 4 167 caractères, la correction est là, **plus aucun
`v_dossier := null`**, et **le commentaire faux a disparu**.

#### L'ESSAI RÉEL — un aller-retour complet chez Hektor, sur un bien d'essai (12/10, 22 h 33 → 22 h 44)

Bien **62965** *(« TEST C13 cloture mandat - a supprimer »)*, état de départ **`Actif /
diffusable=0 / archive=0`**.

| | |
|---|---|
| **22:35:35** | **archiver** depuis l'écran → travail `dossier=`**5941336**, hektor 62965 ; carnet `archive=1 (geste_archiver)` · Hektor accepte en **98 s** |
| **22:38** | le bien **sort du parc vivant** et entre dans l'index des archives — **sous `app_archive_id = 5941336`**, c'est-à-dire **notre numéro de dossier** *(une preuve de plus, sur un bien qu'on vient d'archiver)* |
| **22:41:35** | **désarchiver** depuis l'écran → ⭐ travail `dossier=`**5941336** *(et non `NULL`)*, hektor 62965, `cible_source = index_archives` · carnet **`archive=0 (geste_desarchiver)`** — **la ligne qui était purement sautée avant** |
| **22:42** | Hektor accepte en **38 s** |
| **22:44** | **le bien est revenu : `Actif / diffusable=0 / archive=0`** — **son état de départ, au caractère près** · sorti de l'index des archives |

➡ **Le défaut 5a est corrigé, et les deux gestes sont prouvés de bout en bout chez Hektor.**
Le bien d'essai finit exactement comme il a commencé.

---

## 3b — LE CARNET QUE PERSONNE NE LIT · ÉTAPE 1, AUDIT (13/10, 06 h 45, run en cours)

### ⚠ D'ABORD, JE CORRIGE CE QUE J'AI ÉCRIT HIER

J'ai écrit plusieurs fois que *« le carnet de l'annonce n'a PAS de pendant "appliquer" »*, sur la
foi du commentaire de `run_full_pipeline.ps1:1272-1277`. **C'était une lecture incomplète** : il y
a **DEUX mécanismes**, et un seul manque.

| | Ce qu'il lit | Ce qu'il écrit | Dans le run ? |
|---|---|---|---|
| **`appliquer_contrat.py`** *(C.7, 25/08)* | **la COLONNE** de `app_dossier_current`, dans Supabase, en direct | la base locale (`app_view_generale`) | ✅ **OUI, chaque nuit** — étape « phase2 appliquer le contrat d autorite », l. 571 |
| **`magasin_annonce_app.py`** *(C.4, 30/08)* | — | descend le **CARNET** `app_annonce_champ_app` chez nous | ✅ oui, l. 1279 — mais **il n'applique rien** |

➡ **La machinerie « l'app gagne » existe, elle est branchée, et elle tourne toutes les nuits.**
Elle ne fait rien pour une seule raison : `CHAMPS_APP_ANNONCE` est **vide**. Et son garde-fou est
déjà écrit : *« si la relecture Supabase échoue, on ne touche à rien »*.

### CE QUE ÇA CHANGE POUR L'ÉNONCÉ DE 3b

L'audit du 08/10 disait : *« l'intention va dans le carnet, que ni l'écran ni le run ne lisent »*.
C'est vrai **du carnet**. Mais le vrai nœud est ailleurs, et il est plus précis :

> **Pour « archiver » et « changer de négociateur », l'app n'écrit QUE le carnet — jamais la
> colonne.** Or c'est **la colonne** que `appliquer_contrat.py` lirait si on allumait
> l'interrupteur. **Allumer la liste ne suffirait donc pas : il n'y aurait rien à appliquer.**

*(À comparer avec ce qu'on a fait hier pour le statut : la fonction écrit **la colonne ET le
carnet**. Pour ces deux gestes-là, l'interrupteur aurait de la matière.)*

**État du carnet au 13/10, 06 h 45 — 6 lignes**, dont **3 posées hier soir par les nouveaux
patchs** *(`geste_statut` ×2, `geste_desarchiver` ×1)* :

| champ | origine | n |
|---|---|---|
| `archive` | `geste_archiver` (30/08) · `geste_desarchiver` (**12/10, nouveau**) | 1 + 1 |
| `statut` | `redescente_transaction` (18/09) · `geste_statut` (**12/10, nouveau**) | 1 + 1 |
| `diffusable` | `geste_statut` (**12/10, nouveau**) | 1 |
| `negociateur_email` | `geste_affecter_negociateur` (01/09) | 1 |

**⏳ Suite de l'audit à faire** *(après le run et la descente)* : ce que devient le **motif
d'archivage** *(il ne vit que dans la charge du travail)* · ce que `appliquer_contrat.py` ferait
exactement si on allumait `archive` et `negociateur_email` · et **la question à Frédéric** :
allume-t-on l'interrupteur, et pour quels champs ?

### ⭐ FRÉDÉRIC A RAISON : les CHAMPS de l'annonce sont bien déjà chez nous

*« pour moi tous les champs de l'annonce étaient déjà saisis chez nous »* — **oui**, et c'est
mesuré. Quand on modifie une annonce à l'écran, `app_edit_annonce_optimistic` écrit **tout de
suite, chez nous, avant Hektor** :

| Où | Quoi |
|---|---|
| **la colonne** de la fiche | `prix`, `ville`, `code_postal`, `numero_mandat` |
| **le grand bloc** du détail | `surface`, `nb_pieces`, `nb_chambres`, terrain, latitude, longitude, garage |
| **le calque** `app_optimistic_overlay` | ⭐ **TOUS les champs saisis**, quels qu'ils soient |
| **la file d'attente** `app_annonce_pending` | les mêmes, avec la photo d'avant (`base_snapshot`) |

Et **le run les repose chaque nuit** : étape « phase2 reappliquer les saisies de l app »
*(L3, 21/09, `run_full_pipeline.ps1:1299`)*, **après** le push, pour que le prix saisi survive à la
réécriture depuis le miroir — *« le prix reste à l'app, la surface arrive de Hektor »*.

**Mesuré le 13/10 à 06 h 50** : **69 envois de champs, 69 réussis**, **0 en conflit**, **1 saisie
en attente**. La chaîne fonctionne.

➡ **Le trou de 3b n'est donc PAS sur les champs. Il est sur les champs d'ÉTAT.**

### LE VRAI ÉNONCÉ DE 3b, APRÈS CET AUDIT

Il reste **deux gestes** qui n'écrivent **que le carnet**, jamais la fiche :

| Geste | fiche | carnet | ce que ça donne |
|---|---|---|---|
| **archiver / désarchiver** | ❌ | ✅ `archive` | notre base dit « actif » tant que Hektor n'a pas répondu *(mesuré hier sur 62965 : ~2 à 3 minutes)* |
| **changer de négociateur** | ❌ | ✅ `negociateur_email` | idem *(4 gestes depuis juillet, tous réussis ; la colonne n'a jamais été juste avant la réponse de Hektor)* |

**C'est exactement le défaut de 3a, sur deux gestes de plus — et le correctif a la même forme**
que celui d'hier soir : écrire **aussi la colonne**, et ranger **l'état d'avant** dans la charge du
travail pour pouvoir revenir.

*(Le statut et le diffusable, eux, sont réglés depuis hier soir : la fonction écrit la colonne
**et** le carnet.)*

**⏳ Reste à mesurer avant l'étape 2** : le **motif d'archivage** *(il ne vit que dans la charge du
travail — faut-il le garder chez nous ?)* · et la question de l'**interrupteur**
`CHAMPS_APP_ANNONCE`, qui ne se pose vraiment qu'une fois la colonne écrite.

### Les deux dernières mesures de l'audit 3b (13/10, 07 h)

**① Le motif d'archivage — il n'est pas perdu, mais il est mal rangé.** Il voyage bien dans la
charge du travail, et on l'y retrouve *(archivage de 62965 hier soir)* :
`archive_main_choice`, `archive_sub_choice`, `archive_other_text`, `archive_confrere`,
`archive_price`. Et **rien ne purge les travaux** : **93 631 lignes gardées depuis le 14/05**.
➡ L'information **existe chez nous**, mais elle n'est **attachée à l'annonce nulle part de
lisible** : il faut aller la chercher dans la table des travaux. Elle n'est pas au carnet — qui
est pourtant *« ce que l'app détient »*.

**② ⚠ L'INTERRUPTEUR DU CONTRAT N'EST PAS PRÊT À ÊTRE ALLUMÉ, et c'est une découverte.**
`appliquer_contrat.py` pose la valeur de Supabase **sans aucun filtre** :

```
for champ in CHAMPS_APP_ANNONCE:
    couples = [(row["app_dossier_id"], row[champ]) for row in distant ...]
    UPDATE app_view_generale SET "champ" = (valeur du couple) ...
```

Il **n'importe même pas** `VIDE_NE_GAGNE_PAS` *(qui vaut pourtant `True` dans
`contrat_autorite.py:182` et sert à ses frères mandat et affaire)*. ➡ **« l'app gagne »
y est INCONDITIONNEL** : allumer un champ aujourd'hui reposerait aussi les **vides** sur la base
locale. C'est exactement le danger que le commentaire du contrat annonce pour le mandat — *« un
"l'app gagne" aveugle aurait effacé les 94 clôtures dès la première nuit, en silence »*.

➡ **Ma recommandation : NE PAS allumer l'interrupteur aujourd'hui.** D'abord écrire la colonne
*(c'est 3b)* ; la règle « vide ne gagne pas » viendra avec, si Frédéric veut l'allumer un jour.

### ÉTAPE 2 — LE CORRECTIF PROPOSÉ POUR 3b (écrit, **attend le « vas-y »**)

**Même forme qu'hier soir, sur deux fonctions** *(un seul remplacement chacune, comme pour le
statut : la colonne, et l'état d'avant dans la charge)* :

| Fonction | ce qu'on ajoute |
|---|---|
| `app_archive_annonce_optimistic` | `app_dossier_current.archive = '1'` · `archive_avant` dans la charge |
| `app_assign_negotiator_optimistic` | `app_dossier_current.negociateur_email = <le nouveau>` · `negociateur_avant` dans la charge |

#### ⚠ Ce que ça pourrait casser ailleurs — à vérifier avant de coder

| | |
|---|---|
| **`archive='1'` sur la fiche** | le bien **sort des listes actives tout de suite** — c'est le geste voulu, et ça arrive de toute façon 2-3 min plus tard. La page RDV publique exige `archive=0` → elle se **ferme** plus tôt : **plus sûr** |
| ⚠ **`negociateur_email`** | c'est **le champ du périmètre du négociateur (chantier ②)** : changer la colonne change **immédiatement qui voit le bien**. Même raisonnement — c'est le geste voulu — mais **ça se dit** |
| le run | il réécrit les deux colonnes depuis Hektor chaque nuit → **retour arrière automatique** |
| la protection L3 | elle lit `app_annonce_pending`, pas ces champs → **pas touchée** |
| les workers | aucun changement → **aucun redémarrage** |

#### ⬜ TROIS QUESTIONS POUR FRÉDÉRIC

1. **Le motif d'archivage** : le poser **au carnet** pour qu'il reste attaché à l'annonce, ou le
   laisser dans la charge du travail *(où il est conservé, mais introuvable sans fouiller)* ?
2. **L'interrupteur** `CHAMPS_APP_ANNONCE` : **on ne l'allume pas aujourd'hui** *(recommandation
   ci-dessus)*. D'accord ?
3. **Le motif de désarchivage** n'existe pas *(le geste n'en demande pas)* — on laisse ainsi ?

### 🔎 AUDIT DEMANDÉ : LE MOTIF D'ARCHIVAGE, dans l'app ET chez Hektor (13/10, 07 h 15)

> *« s'il n'y a pas de motif d'archivage, pourquoi rajouter la colonne ? Il y a, et c'est sûr, des
> motifs pour clore un mandat, clore une annonce. Fais un audit... il faut comprendre pourquoi on
> est dans cette situation. »*

**Frédéric a raison, et je me suis mal exprimé hier soir.** Le motif existe — il est même plus
riche que je ne l'ai dit. Ce qui n'existe pas, c'est **sa conservation chez nous**.

| Geste | Motif à l'écran ? | Part-il chez Hektor ? | Gardé chez nous ? |
|---|---|---|---|
| **ARCHIVER** | ✅ **riche** : 2 motifs principaux *(Vendu · Autre)*, **9 causes**, + **prix** et **confrère** *(`App.tsx:19131-19176`)* | ✅ **OUI** — un appel **dédié** : `mode=popins-StatutBien-statutBienDispatcher`, `context=validerArchivage`, avec `params[etat]`, `params[raison]`, `params[autre]`, `params[prix]`, `params[confrere]`, `params[id_confrere]` *(`console_job_worker.js:19979-19993`)* | ❌ **NON** |
| **CLORE le mandat** *(statut « Mandat clos »)* | ✅ 3 états *(non renouvelé · vendu · autre)* + **7 raisons** *(`App.tsx:8675-8690`)* | ❌ **NON** — `CONSOLE_HEKTOR_CLOTURE_MANDAT` vaut **`false`** et n'est **posé nulle part** : Hektor **n'est jamais informé** *(décision C.13 du 28/08)* | ❌ **NON** — seule **la DATE** est écrite *(`mandat_date_cloture` au carnet du mandat, `console_job_worker.js:13094-13105`)* |
| **DÉSARCHIVER** | ❌ aucun motif demandé | — | — |

**Mesure décisive** : **aucune colonne** de la base ne porte un motif d'annonce. Recherche sur
tout le schéma *(`%motif%`, `%raison%`, `%reason%`, `%cause%`)* : 26 colonnes trouvées, **aucune**
sur la fiche, les index ou le carnet de l'annonce. Le motif ne vit que dans
`app_console_job.payload_json` — où il est **conservé** *(93 631 travaux depuis le 14/05, rien
n'est purgé)*, mais **introuvable sans fouiller**.

#### POURQUOI ON EN EST LÀ — deux raisons, toutes les deux écrites

1. **L'app a été construite pour TRANSMETTRE le motif, pas pour le DÉTENIR.** Le libellé de la
   modale le dit lui-même : *« Motif principal **Hektor** »*, et les listes sont **celles du
   formulaire de Hektor** *(`choiceVendu`/`choiceAutre`, `agence`/`confrere`/`concurence`…)*.
   À l'étape 2 c'est cohérent : **Hektor est le maître, c'est lui qui garde le motif.**
2. **Pour la clôture, c'est pire — et c'est une décision assumée.** Le 28/08 (C.13), on a décidé
   que **Hektor ne serait pas informé** d'une clôture de mandat. Le motif saisi ne part donc
   **nulle part** : ni chez Hektor, ni dans nos tables. **Un négociateur choisit « Confié à la
   concurrence » et cette phrase n'est écrite nulle part de lisible.**

#### CE QUE ÇA COÛTERA À LA COUPURE

Le jour où Hektor s'arrête, on garde **la date** et **le geste**, mais on perd **la raison** pour
laquelle chaque bien a été archivé. Et pour les **clôtures de mandat**, on ne l'a **déjà pas** —
c'est le registre légal des mandats qui s'en trouve amputé.

**Volume d'aujourd'hui** : 6 archivages et 9 « Mandat clos » depuis l'app — petit, **parce que les
négociateurs le font encore dans Hektor**. C'est le volume d'aujourd'hui, pas celui de demain.

➡ **Ma recommandation : garder les deux motifs chez nous**, au carnet, dans la même fonction et la
même transaction que le geste. C'est deux lignes de plus par geste, et ça ne change rien à ce qui
part chez Hektor.

### 🔎 AUDIT RECADRÉ PAR FRÉDÉRIC (13/10, 07 h 35) — **le STATUT « Clos » de l'annonce**, pas le mandat

> *« Le mandat clos est une action uniquement dans notre app, pas dans Hektor, et c'est normal.
> Tous les mandats n'ont pas de date de clôture — ce sera mon app qui va le gérer, mais c'est un
> AUTRE chantier. Là on est sur les statuts d'annonce. Je parlais du statut Clos. »*

**Sa mesure, vérifiée** : `app_mandat` porte **26 855 mandats**, dont **91 seulement** ont une date
de clôture — **0,3 %**. *(Registre : 24 505 lignes, 118 closes. Carnet du mandat : 2 lignes,
toutes `mandat_date_cloture / cloture_app`.)* ➡ **la date de clôture est à construire, et c'est un
autre chantier.** Noté, pas lancé.

#### LE STATUT « CLOS » DE L'ANNONCE — ce que j'ai trouvé

**Hektor a UN SEUL mécanisme pour les deux gestes**, le même point d'entrée
`popins-StatutBien-statutBienDispatcher`, avec deux contextes :

| Geste | Point d'entrée Hektor | Appelé ? |
|---|---|---|
| **archiver** | `context=validerArchivage` + `etat`, `raison`, `autre`, `prix`, `confrere` | ✅ **OUI, toujours** |
| **statut « Clos »** | `context=validerClos` + `etat`, `raison`, `idMandat` | ❌ **NON** — derrière `CONSOLE_HEKTOR_CLOTURE_MANDAT`, **éteint et jamais posé** |

➡ **Le motif du statut « Clos » est saisi, validé par le worker… et n'est envoyé à personne.**
`normalizeHektorClosureMotif` *(l. 12677)* le normalise, `HEKTOR_CLOSURE_RAISONS` le contrôle —
puis la seule fonction qui l'utilise est derrière l'interrupteur éteint. **Et il n'est stocké nulle
part chez nous** *(0 colonne motif sur l'annonce, vérifié sur tout le schéma)*.

⚠ **Et la modale le PROMET** : elle affiche *« CLÔTURE MANDAT — Motif transmis à Hektor »*. **Il
n'est transmis à rien.**

#### POURQUOI ON EN EST LÀ — c'est écrit, et c'est une décision de bon sens

`console_job_worker.js:13177-13186`, C.13 du **28/08** :

> *« AVANT : clôture chez Hektor PUIS changement de statut. **La clôture échouant sur 98,8 % du
> parc, LE STATUT NE CHANGEAIT PAS NON PLUS** — constaté le 28/08 sur l'annonce 62966 : "Mandat
> clos" demandé, l'annonce est restée "Actif". **Un geste qui marche était pris en otage par un
> geste qui échoue.** MAINTENANT : le statut d'abord, chez Hektor. Puis la clôture CHEZ NOUS. »*

**Et pourquoi la clôture échouait sur 98,8 % du parc ?** Parce que le formulaire de Hektor exige
un **`idMandat`**, et que *« la clôture est IRRÉVERSIBLE côté Hektor → on refuse de deviner le
mandat cible »*. Or **99,7 % des mandats n'ont pas de date de clôture** chez nous — le même trou,
vu de l'autre bout.

➡ **Le motif n'a pas été oublié : il est tombé avec le geste qu'on a débranché le 28/08**, pour
une bonne raison. Mais personne n'a décidé qu'il devait **disparaître** — il a juste suivi.

#### ⭐ ET IL Y A UN CIRCUIT QUI, LUI, GARDE LE MOTIF CHEZ NOUS

`app_diffusion_request` — **les demandes du négociateur**, avec `request_reason`,
`request_comment`, `refusal_reason`, `processing_comment`, le demandeur et le traiteur :

| Type de demande | n | avec une raison |
|---|---|---|
| `demande_baisse_prix` | 4 *(acceptées)* | **4** |
| **`demande_annulation_mandat`** | 4 *(acceptées)* | 1 |
| `demande_diffusion` | 1 *(en attente)* | 0 |

➡ **Le modèle « garder le motif chez nous » existe déjà dans l'app, et il est meilleur** : il porte
le motif, le demandeur, la réponse et le traiteur. C'est le circuit prévu par la **spéc. du 30/07**
pour qu'un négociateur demande une annulation de mandat.

#### ⚠ CORRECTION IMMÉDIATE (Frédéric : « c'est faux, nous l'avons testé »)

Ma table ci-dessus était **ambiguë et se lisait de travers**. Il faut distinguer **deux choses qui
partent par deux chemins différents** :

| | Chez Hektor | Preuve |
|---|---|---|
| **LE STATUT « Clos » lui-même** | ✅ **ENVOYÉ, toujours** — `setHektorAnnonceStatusValue` : `upval champ=status val=6`, puis `upval champ=diffusable val=0` | **éprouvé hier soir sur 62963** : travail `done` en 43 s, journal `hektor_status: done`, et l'état relu par l'API rend bien le statut **6** · idem ce matin dans l'autre sens *(« Actif », 31 s)* |
| **LE MOTIF de la clôture** *(état + raison + n° de mandat)* | ❌ **non envoyé** — c'est le formulaire `validerClos`, derrière `CONSOLE_HEKTOR_CLOTURE_MANDAT`, éteint depuis le 28/08 | `console_job_worker.js:13192-13195` |

➡ **Le geste marche et il arrive chez Hektor. C'est le MOTIF, et lui seul, qui ne va nulle part.**
La ligne « statut Clos → validerClos → non appelé » de la table précédente parlait **du formulaire
du motif**, pas du changement de statut — c'est à corriger dans la lecture de ce document.

### 🔎 « REGARDE S'IL N'EXISTE PAS DÉJÀ QUELQUE CHOSE POUR LA CLÔTURE DES MANDATS » (13/10, 07 h 50)

**Oui — presque tout existe.** La chaîne est construite, son interrupteur est **allumé** *(c'est le
seul qui le soit)*, et elle tourne chaque nuit. **Un seul maillon est au mauvais grain.**

| Ce qui existe | État |
|---|---|
| le geste à l'écran *(statut « Clos » + motif)* | ✅ |
| le worker écrit la date **chez nous** : `cloturerMandatLocalement` → `app_mandat_champ_app` *(clé : annonce + n° de mandat)* | ✅ |
| **l'interrupteur** `CHAMPS_APP_MANDAT = ("mandat_date_cloture",)` | ✅ **ALLUMÉ depuis le 28/08** — le seul contrat allumé du projet |
| le magasin descend le carnet chaque nuit *(`magasin_mandat_app.py`, run l. 590)* | ✅ |
| l'applicateur tourne chaque nuit *(`appliquer_contrat_mandat.py`, run l. 593)* | ✅ |
| la règle « **vide ne gagne pas** » y est appliquée | ✅ *(l. 84 — elle protège les clôtures que Hektor porte et que l'app ignore)* |
| la colonne existe dans `app_mandat` *(`date_cloture`)* et dans le registre *(`mandat_date_cloture`)* | ✅ |

#### ⛔ LE MAILLON CASSÉ : L'APPLICATEUR ÉCRIT SUR L'ANNONCE, PAS SUR LE MANDAT

`appliquer_contrat_mandat.py:50` → **`CIBLE = "app_view_generale"`**, et l'`UPDATE` est fait
`WHERE hektor_annonce_id = …`. **Il pose donc la date sur l'ANNONCE** *(une date par annonce)*,
alors que le carnet, lui, est rangé par **couple (annonce, n° de mandat)** — et c'est ce couple
qui fait foi dans le projet *(« la clé : le couple », 24 939 sur 24 939)*.

Et de l'autre côté, `mandat_ledger.py` **exclut volontairement `date_cloture` de son
`ON CONFLICT`** — sa « **protection par omission** », écrite en tête du fichier :

> *« Ce que le run ne réécrit pas, il le préserve. `date_cloture` est donc HORS du ON CONFLICT :
> **l'app la possède déjà** (CHAMPS_APP_MANDAT), le carnet la porte, et le run n'a pas à
> l'écraser. »*

➡ **Les deux moitiés se font confiance l'une à l'autre, et personne n'écrit.** Le ledger s'efface
devant l'app ; l'applicateur de l'app écrit ailleurs. **La date reste au carnet, et n'arrive
jamais au mandat.**

#### LA MESURE QUI LE PROUVE — les 2 clôtures faites par l'app

| annonce / mandat | au carnet | dans `app_mandat` | dans le registre |
|---|---|---|---|
| **62966 / 18842** | **2026-08-28** | ❌ **NULL** | ❌ **NULL** |
| **24933 / 11939** | **2026-09-18** | ❌ **NULL** | ⚠ **2026-10-05** — **une AUTRE date**, qui ne vient pas de nous |

*(Et au total : 26 855 mandats, **91** avec une date — 0,3 % ; registre : 118.)*

➡ **Ce n'est donc pas « il n'existe rien » : il existe presque tout, et ça ne se rejoint pas.**
Le correctif est petit — faire écrire l'applicateur **au grain du mandat** — mais c'est un geste
sur le **run de nuit**, donc : **chantier 3c, et avec le « vas-y » de Frédéric.**

### ÉTAPE 2/3 DE 3b — LE CORRECTIF (écrit le 13/10, **attend le « vas-y »**)

**Trois remplacements, sur deux fonctions** *(dans leur état d'aujourd'hui — elles ont reçu le
repli vendu/clos hier soir : empreintes `04dfcb30…` et `85bde9eb…`)* :

| | Fonction | Ce qu'on ajoute |
|---|---|---|
| **R1** | archiver | la **fiche** reçoit `archive='1'` · et le **carnet** reçoit **le MOTIF** (`archive_motif`) à côté de `archive` |
| **R2** | archiver | `archive_avant` voyage dans la charge du travail |
| **R3** | négociateur | la **fiche** reçoit le nouvel email · l'ancien part dans la charge |

**Les 3 ancres sont uniques** *(vérifié dans la base : R1=1, R2=1, R3=1)*.

**⚠ Le motif est inclus** — c'est ma réponse à l'audit du matin : il est demandé à l'écran,
envoyé à Hektor, et **perdu chez nous**. Il est rangé au carnet sous la forme
`choiceVendu · agence` *(ou avec le texte libre si « Autre »)*. **Si Frédéric n'en veut pas, c'est
la paire R1 qu'on remplace par sa version sans motif — le reste tient sans elle.**

**La règle « on n'invente pas » est conservée mot pour mot** pour le négociateur : sans email, ni
la fiche ni le carnet ne bougent, et le travail part quand même. **C'est l'essai D de la
répétition** *(le témoin)*.

**Les 5 essais** : archiver un bien **vivant** avec motif · archiver un bien **vendu** *(la fiche
touche 0 ligne, le carnet reçoit quand même)* · négociateur **avec** email · négociateur **sans**
email *(rien ne doit bouger)* · et le retour des deux empreintes après l'inverse.

#### ✅ RÉPÉTITION 3b (13/10, 10 h) — **toutes les mesures exactes**

| | Mesure | Résultat |
|---|---|---|
| avant | les 2 empreintes · les 3 ancres | `04dfcb30…` · `85bde9eb…` · **R1=1 R2=1 R3=1** ✅ |
| après | **empreintes NUES** *(chemin inverse)* | **identiques à celles d'avant** → rien d'autre n'a changé ✅ |
| **A** archiver un **vivant** | fiche `archive=1` · carnet **`archive=1 \| archive_motif=choiceVendu · agence`** · charge `archive_avant=0` | ✅ **le motif est enfin gardé** |
| **B** archiver un **vendu** | fiche **0 ligne** *(il n'y est pas)* · carnet `archive=1 \| archive_motif=choiceAutre · autre · essai repetition` | ✅ **le texte libre passe aussi** |
| **C** négociateur **avec** email | fiche = le nouvel email · charge `negociateur_avant = gonzalez@…` | ✅ |
| **D** négociateur **SANS** email *(le témoin)* | fiche **avant = après** · carnet : **aucune ligne `negociateur_email` ajoutée** | ✅ **la règle « on n'invente pas » est intacte** |
| après l'inverse | les 2 empreintes | **revenues à l'identique** ✅ |

### ÉTAPE 5 DE 3b — CONTRÔLE ET ESSAI RÉEL (13/10, 10 h 15)

**Le patch en base** : archiver **3 845 → 5 415**, négociateur **4 508 → 5 187** · le bloc 3b posé
**une fois** dans chacune · ⭐ **le repli vendu/clos d'hier soir est CONSERVÉ** dans les deux ·
`SECURITY DEFINER`, propriétaire et droits intacts, **`anon` toujours absent**. Et le patch a
vérifié lui-même, avant de valider, qu'en défaisant ses 3 remplacements on retombait exactement
sur les fonctions d'avant.

#### ✅ L'ESSAI RÉEL DE L'ARCHIVAGE — aller-retour complet chez Hektor, bien d'essai 62965

État de départ : `Actif / diffusable=0 / archive=0`, négociateur GONZALEZ.

| Heure (UTC) | |
|---|---|
| **08:14:35** | clic « Archiver », motif **« Parti à la concurrence »** |
| **08:14:44** *(+9 s)* | le travail est encore **`running`** — Hektor n'a pas répondu — et **chez nous** : fiche **`archive=1`** · carnet **`archive=1 \| archive_motif=choiceAutre · concurence`** · charge **`archive_avant=0`** |
| 08:16 | Hektor confirme *(114 s)*, puis la relecture *(32 s)* |
| | le bien sort du parc vivant, entre dans l'index des archives sous **5941336** · ⭐ **et le carnet garde le motif : la relecture ne le touche pas** |
| **08:19:54** | clic « Désarchiver » → travail avec **`app_dossier_id = 5941336`** *(la correction 5a)*, carnet passé à `archive=0`, **motif conservé** |
| 08:21 | Hektor confirme *(47 s)*, relecture *(34 s)* |
| **au final** | **`archive=0 / statut=Actif / diffusable=0 / nego=gonzalez@…`** — **l'état de départ, au caractère près** |

⭐ **Le motif d'archivage est gardé chez nous pour la première fois du projet.**

#### ⛔ L'ESSAI DU NÉGOCIATEUR : ARRÊTÉ AVANT D'ÉCRIRE, ET VOICI POURQUOI

J'ai ouvert « Réaffecter le négociateur » et **vérifié d'abord que je pourrais revenir**. Je ne
peux pas : la liste des négociateurs de la modale ne propose **qu'un seul nom**, *Emmanuelle
PEREIRA*, et **changer d'agence ne change pas la liste** *(essayé : Firminy → Saint-Étienne, même
liste)*. **Vincent-Lucas GONZALEZ, le négociateur actuel du bien, n'y est pas.**

➡ Faire l'essai, c'était réaffecter le bien **sans savoir le remettre**. J'ai **annulé sans rien
envoyer**. *(Règle : accord obligatoire pour tout geste irréversible — et je n'ai pas d'accord pour
celui-là.)*

**Ce qui reste donc prouvé pour le négociateur** : la **répétition**, essais C et D — la fiche
reçoit le nouvel email, l'ancien part dans la charge, et **sans email rien ne bouge**. Le chemin
de code est **le même** que celui de l'archivage, éprouvé en réel ci-dessus.

**⬜ Deux questions pour Frédéric** : ① la modale ne propose **qu'un négociateur** — est-ce voulu,
ou est-ce un défaut à part ? ② veut-il quand même un essai réel du négociateur, sur un bien de son
choix et avec une cible qu'il pourra reprendre ?

---

## LES TROIS POINTS LAISSÉS EN SUSPENS — traités le 13/10 sur demande de Frédéric

### ① ✅ FAIT — « vide ne gagne pas » posé dans le contrat d'annonce

`appliquer_contrat.py` posait la valeur de Supabase **sans aucun filtre**, et **n'importait même
pas** la constante `VIDE_NE_GAGNE_PAS` *(qui vaut pourtant `True` et que ses **deux frères**
appliquent depuis le 28/08)*. Un champ vide côté app aurait donc **effacé la valeur de Hektor**
dans la base locale, en silence — exactement ce que le commentaire du contrat de mandat annonce :
*« un "l'app gagne" aveugle aurait effacé les 94 clôtures dès la première nuit, en silence »*.

**La règle est maintenant posée** *(import + filtre + une ligne au journal qui dit combien de
vides ont été ignorés)*. ⭐ **Et elle est posée AVANT d'allumer l'interrupteur, pas après — c'est
tout l'intérêt.**

**Preuve d'inertie, exécutée** : `python phase2/identite/appliquer_contrat.py --dry-run` →
*« contrat d'annonce : (aucun) · Le contrat est VIDE : Hektor garde l'autorité sur tous les
champs. Rien à arbitrer — comportement identique à aujourd'hui. »*, **code de sortie 0**. La
fonction sort **avant** la boucle modifiée : le run de cette nuit se comportera à l'identique.

➡ **L'interrupteur `CHAMPS_APP_ANNONCE` peut désormais être allumé sans danger** — mais c'est une
décision de Frédéric, et elle reste à prendre.

### ② ✅ AUDITÉ — la modale n'est PAS cassée, c'est la DONNÉE qui parle

La liste vient de `app_hektor_negotiator_agency_directory`, filtrée sur `is_active` **et sur
l'agence choisie**. Mesure :

| | |
|---|---|
| lignes de l'annuaire | **219** |
| **négociateurs actifs** | **30**, répartis sur **18 agences** |
| **Groupe GTI Firminy** | **1 seul actif : Emmanuelle PEREIRA** |
| Groupe GTI Saint-Étienne | 2 : Lucille FORLICO, Mélanie LEGRAND |

➡ **La modale affichait exactement la vérité.** Elle ne pouvait pas proposer GONZALEZ parce que
**Vincent-Lucas GONZALEZ est INACTIF** : il figure **trois fois** dans l'annuaire *(Firminy,
Monistrol, Saint-Étienne)* et **`is_active = false` sur les trois**.

#### ⚠ CE QUE CET AUDIT A SORTI, ET QUI EST PLUS IMPORTANT

**1 522 biens vivants sur 13 480 (11 %) sont au nom d'un négociateur INACTIF** — et **4 227 (31 %)
n'ont aucun négociateur**.

| négociateur inactif | biens vivants | dont *Actif* | dont **diffusés** |
|---|---|---|---|
| valette@ | **508** | 1 | 0 |
| gonzalez@ | **309** | 9 | **2** |
| berger@ | 217 | 0 | 0 |
| accueil@ | 171 | 0 | 0 |
| p.girinon@ | 158 | 0 | 0 |
| martinez@ | 129 | 0 | 0 |

➡ **L'essentiel est historique** *(des estimations au nom de gens partis)*, et l'urgence est
petite : **12 biens actifs** et **2 diffusés**. Mais c'est une **décision de Frédéric** : réaffecter,
ou laisser. **Ce n'est pas du code.**

### ③ ⬜ LE MOTIF DU STATUT « CLOS » — ma recommandation, et elle attend son mot

**Le carnet**, comme on vient de le faire pour l'archivage. Pourquoi, et pas le circuit des
demandes :

- le statut « Clos » est un **geste direct**, pas une **demande** : `app_diffusion_request` sert à
  **demander** quelque chose à un administrateur *(avec réponse, refus, relance, traiteur)* — ce
  n'est pas le même objet ;
- le carnet, lui, est fait pour *« ce que l'app détient »*, et c'est **la même transaction, 2
  lignes**, exactement comme `archive_motif` ce matin ;
- et le jour de la coupure, c'est le carnet qui devient la vérité.

➡ **Un mot de Frédéric et je le pose.** *(Le geste du statut est déjà patché ; ce serait une
quatrième ligne dans le même bloc.)*

### 📜 DÉCISIONS DE FRÉDÉRIC (13/10) + réponse à « sommes-nous prêts ? »

1. **Le motif du statut « Clos » → au CARNET.** *(« ok pour le carnet »)* — patch écrit :
   `supabase/patch_chantier3_3b_motif_clos_2026-10-13.sql`.
2. **Les 1 522 biens au nom d'un négociateur inactif → ON NE TOUCHE À RIEN.** *(« ok donc ne
   touche rien »)*. Noté, à ne pas relancer de moi-même.
3. **« Sommes-nous prêts à allumer l'interrupteur ? » → NON**, et ce n'est pas une question de
   maturité du code : **nos quatre champs ne passent pas le critère que le projet s'est donné.**

#### Le critère est écrit dans `contrat_autorite.py`, et il est le même deux fois

| Champ allumé | La raison écrite |
|---|---|
| contacts : `birth_date`, `birth_place`, `marital_status` | *« Hektor ne renvoie JAMAIS ces trois-là : seule l'app les écrit. **Aucun arbitrage possible, donc aucun risque.** »* |
| mandat : `mandat_date_cloture` | *« C'est un champ que **l'app CRÉE**, pas un champ que **Hektor entretient**. »* |

➡ **On allume un champ que l'app CRÉE et que Hektor N'ENTRETIENT PAS.**

Or `statut_annonce`, `diffusable`, `archive` et `negociateur_email` sont **tous entretenus par
Hektor** — c'est même lui qui les **confirme**, à chaque geste, ~70 s après. Les allumer ferait
gagner l'app sur des champs dont Hektor est encore le maître.

**Et il y a pire, précis** : la valeur que nos patchs écrivent est **provisoire** pendant la fenêtre
d'attente, et **rien ne la marque « confirmée »**. L'interrupteur promouvrait donc **un affichage
transitoire en autorité** — exactement l'inverse du but.

**Ce qui nous rendra prêts : la coupure.** Quand Hektor n'entretiendra plus rien, le critère sera
rempli de lui-même. D'ici là, **le carnet est le bon véhicule** : il garde ce que l'app a décidé
*sans* contredire Hektor. C'est d'ailleurs ce qu'on a fait toute la journée.

⚠ **La règle « vide ne gagne pas » posée ce matin reste utile** : elle enlève le risque **le jour
où** un champ remplira le critère. On ne l'allume pas, mais on ne laissera plus un piège derrière.

#### ✅ LE MOTIF DU « CLOS » EST POSÉ (13/10)

Répétition exacte : empreinte et ancre conformes · **chemin inverse = empreinte d'avant** ·
essai **A** → carnet `clos_motif=choiceNonRenouv · concurence`, à côté de `statut=Clos` et
`diffusable=0` · essai **B, le témoin** → « Actif » ne pose **aucun** `clos_motif`.

Patch appliqué, contrôlé : **14 685 → 16 044**, `clos_motif` une seule fois, et ⭐ **le bloc 3a
et le repli vendu/clos sont tous deux conservés**.

➡ **Les trois motifs que l'app connaît sont désormais gardés chez nous** : l'archivage
*(`archive_motif`)*, le désarchivage *(le geste, `archive=0`)* et la clôture *(`clos_motif`)*.

---

## 📋 ÉTAT DU CHANTIER ③ AU 13/10, 11 h

| Point | État |
|---|---|
| **3a** — statut et diffusable chez nous d'abord | ✅ **fini**, prouvé en réel *(73 s gagnées)* |
| **le repli vendu/clos** *(hors périmètre d'origine, ouvert par Frédéric)* | ✅ **fini** — **8 941** biens débloqués, les 35 318 archives restant en lecture seule |
| **le défaut 5a** *(trouvé en chemin)* | ✅ **corrigé**, aller-retour réel chez Hektor |
| **3b** — archiver et négociateur écrivent la fiche | ✅ **fini**, + ⭐ **les motifs gardés chez nous** |
| « vide ne gagne pas » dans le contrat d'annonce | ✅ **posé** *(et inerte, prouvé par exécution)* |
| **3c** — la clôture de mandat | ⬜ **audité** : tout existe, un seul maillon est au mauvais grain |
| **3d / 3e** — documents et photos | ⬜ pas commencé |

**Total : 6 patchs SQL · 0 déploiement · 0 redémarrage de worker · 0 ligne de front.**

### ❓ « Et pour les CONTACTS, a-t-on fait pareil ? » (13/10) — **oui, et avant l'annonce**

| Geste du contact *(appelé par l'écran)* | écrit la fiche chez nous ? |
|---|---|
| créer un contact *(`app_create_contact_optimistic`)* | ✅ |
| modifier un contact *(`app_edit_contact_optimistic`)* | ✅ + **file d'attente** + les champs app |
| créer un mandant *(`app_create_mandant_contact_optimistic`)* | ✅ |
| modifier un mandant *(`app_update_mandant_contact_optimistic`)* | ✅ + file d'attente |
| modifier *(voie console)* · supprimer | ✅ · ✅ |

⚠ **Trois fonctions n'écrivent PAS la fiche** — `app_console_create_contact_job`,
`app_console_create_mandant_contact_job`, `app_console_create_update_mandant_contact_job` —
**mais l'écran n'en appelle AUCUNE** *(mesuré : 0 occurrence dans `api.ts`)*. Ce sont les voies
d'avant, mortes.

**Et le contact a quelque chose que l'annonce n'aura pas avant la coupure :** son interrupteur
est **allumé**, sur 3 champs — `birth_date`, `birth_place`, `marital_status` — **parce qu'ils
remplissent le critère** : *« Hektor ne renvoie JAMAIS ces trois-là : seule l'app les écrit.
Aucun arbitrage possible, donc aucun risque. »* **261 contacts portent déjà une date de
naissance.**

**L'architecture est différente, et plus simple** : pas de carnet ni d'applicateur nocturne — la
protection vit **dans le push lui-même** *(`push_contacts_to_supabase.py:483-505`, il relit les
3 champs dans Supabase et les réinjecte pour qu'un push ciblé ne les perde pas)*.

**Et le motif de suppression d'un contact était déjà gardé** : `app_console_deleted_contact_log`,
**13 suppressions tracées, 4 avec un motif** *(et 114 pour les annonces)*.

➡ **Le contact n'était pas en retard : c'est l'annonce qui l'était.** Ce qu'on a fait ces deux
jours la met au même niveau — et au-delà, puisque ses motifs sont désormais gardés aussi.

---

## 3c — LA CLÔTURE DE MANDAT · ÉTAPE 1, AUDIT COMPLET (13/10) — verdict : **CONFIRMÉ**

### Ce qui existe déjà, et qui marche

| | |
|---|---|
| le geste à l'écran *(statut « Clos » + motif)* | ✅ |
| le worker écrit la date **chez nous** : `cloturerMandatLocalement` → carnet `app_mandat_champ_app`, **clé (annonce, n° de mandat)** | ✅ |
| **l'interrupteur `CHAMPS_APP_MANDAT = ("mandat_date_cloture",)`** | ✅ **ALLUMÉ depuis le 28/08 — le seul du projet** |
| `magasin_mandat_app.py` descend le carnet chaque nuit | ✅ *(run l. 590)* |
| `appliquer_contrat_mandat.py` tourne chaque nuit, avec « vide ne gagne pas » | ✅ *(run l. 593)* |
| les colonnes existent | `app_mandat.date_cloture` · `app_mandat_register_current.mandat_date_cloture` · la vue |

### ⛔ LA CHAÎNE EST COUPÉE EN DEUX ENDROITS

**① L'applicateur écrit au mauvais grain, et dans une colonne qui ne voyage pas.**
`appliquer_contrat_mandat.py:50` → `CIBLE = "app_view_generale"`, `UPDATE … WHERE hektor_annonce_id = …`
➡ il pose la date **sur l'ANNONCE** *(une par annonce)*, alors que le carnet est rangé par
**couple (annonce, n° de mandat)** — la clé du projet. ⚠ **Et `app_dossier_current` n'a même pas
de colonne `mandat_date_cloture`** *(mesuré : elle n'existe que dans `app_mandat`, le registre et
sa vue)* : ce qu'il écrit localement **ne monte nulle part**.

**② Le fabricant du registre ne la reprend jamais.**
`mandat_ledger.py` prend la date dans **la version de Hektor**
*(`_texte(courante.get("cloture")) or _texte(_du_plat("date_cloture"))`, l. 579)* — **jamais dans
le carnet** — et `date_cloture` est **hors de son `ON CONFLICT`**, par sa « **protection par
omission** » :

> *« Ce que le run ne réécrit pas, il le préserve. `date_cloture` est donc HORS du ON CONFLICT :
> **l'app la possède déjà**, le carnet la porte, et le run n'a pas à l'écraser. »*

➡ **Les deux moitiés se font confiance, et personne n'écrit.** Et comme la date n'est posée qu'à
la **première insertion**, un mandat déjà connu **ne peut plus jamais la recevoir** — **ni de
l'app, ni de Hektor**.

### LA MESURE QUI PROUVE LES DEUX

| annonce / mandat | au carnet *(l'app)* | dans `app_mandat` | dans le registre |
|---|---|---|---|
| **62966 / 18842** | **2026-08-28** | ❌ vide | ❌ vide |
| **24933 / 11939** | **2026-09-18** | ❌ vide | ⚠ **2026-10-05** — **la date de HEKTOR**, pas la nôtre |

Et à l'échelle : **26 855 mandats, 91 avec une date — 0,3 %** · le registre en porte **118**.
⭐ **Cet écart de 27 s'explique par la même cause** *(l'audit du 08/10 le soupçonnait sans le
prouver)* : les clôtures faites **dans Hektor** après la première insertion ne peuvent pas entrer
non plus.

### CE QUE JE N'AI PAS MESURÉ

Lequel des deux consommateurs gagne exactement quand les deux écrivent *(je n'ai pas rejoué une
nuit)*. **Mais le résultat, lui, est mesuré : 0 sur 2.**

### ⚠ CORRECTION DE MON PROPRE AUDIT, LE MÊME JOUR

J'avais écrit « **0 sur 2** » en regardant `app_mandat` — **une table que l'écran ne lit pas**.
Mesuré à la bonne source *(`app_mandat_register_current`, celle que lit `api.ts`)* :

| annonce | mandat | notre date | **ce que l'écran montre** | statut |
|---|---|---|---|---|
| 11810 | 17770 | 2026-06-05 | ✅ 2026-06-05 | Actif |
| 1951 | 17988 | 2026-07-14 | ✅ 2026-07-14 | Actif |
| 11824 | 17946 | 2026-08-24 | ✅ 2026-08-24 | Actif |
| **62966** | 18842 | 2026-08-28 | ❌ **vide** | Clos |
| **62774** | 18836 | 2026-08-30 | ❌ **vide** | Sous offre |
| 41433 | 18038 | 2026-09-14 | ✅ 2026-09-14 | Sous offre |
| **24933** | 11939 | 2026-09-18 | ⚠ **2026-10-05** | Clos |

➡ **4 sur 7 tiennent.** Et le geste, lui, est **complet** : `cloturerMandatLocalement`
écrit le carnet *(« l'écriture qui fait foi », vérifiée)* **puis `PATCH` le registre tout de
suite** — « le registre montre la date tout de suite, au lieu d'attendre le run de nuit ».

### ⭐ LE VRAI DÉFAUT : **LA DATE TIENT PAR CHANCE**

Le `PATCH` du worker survit **tant que la ligne du registre n'est pas réécrite**. Le push est
un **delta par empreinte** : il ne réécrit une ligne que si l'annonce a bougé. Donc

> **la date de clôture survit tant que l'annonce ne bouge plus ; dès qu'elle bouge, le
> constructeur la remplace par celle de Hektor — c'est-à-dire par du vide.**

Les 3 perdues sont les 3 qui ont bougé. ⚠ **Et pour 62966, c'est MOI** : je l'ai archivée
puis désarchivée hier pour éprouver 5a — ce qui a réécrit sa ligne et effacé sa date.
**Une épreuve a détruit une donnée réelle.** Je ne l'avais pas vu.

➡ Ce n'est donc **pas** « écrire chez nous d'abord » qui manque. C'est :
**la nuit ne doit pas effacer ce que nous détenons.**

### LE PRÉCÉDENT : LE PROJET A DÉJÀ TRANCHÉ CE CHOIX

`export_app_payload.py` l. 1909-1917, écrit le 06/10 pour **les mandants**, exactement le même
problème :

> *« Et sa place dans le run est le point délicat. […] Corriger dans `mandat_ledger.py` aurait
> réintroduit **l'erreur classique du projet : lire la couche de la veille**. ⭐ Et le même
> constructeur sert `push_single_annonce_to_supabase.py` — donc **le chemin IMMÉDIAT du worker
> (~1 min) en profite aussi**, sans code en plus. »*

➡ Le bon endroit est **`build_mandat_register_rows`**, pas `mandat_ledger.py`.
Et l'ordre du run le permet : le carnet est descendu **l. 590**, le push est **l. 1159**.

---

## 3c — ÉTAPE 2 : LE CORRECTIF PROPOSÉ *(présenté le 13/10, EN ATTENTE DU « VAS-Y »)*

### Ce que je changerais — **un seul fichier, deux endroits, zéro table nouvelle**

`phase2/sync/export_app_payload.py` — le constructeur du registre. Au lieu de

```python
"mandat_date_cloture": normalize_text(current_version.get("cloture")) or None,   # Hektor seul
```

on prend **la nôtre quand nous en avons une**, et celle de Hektor sinon :

```python
"mandat_date_cloture": nos_clotures.get((annonce, numero))                      # ⭐ l'app d'abord
                       or normalize_text(current_version.get("cloture")) or None
```

`nos_clotures` étant lu **une seule fois**, au début, dans le carnet local
`app_mandat_champ_app` *(descendu à l. 590, donc frais au moment du push l. 1159)* :
`where champ='mandat_date_cloture' and trim(valeur_app) <> ''`.

C'est **« vide ne gagne pas »**, la règle déjà écrite trois fois dans le projet. Et c'est le
**même patron que les mandants**, au même endroit, pour la même raison.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

| | |
|---|---|
| **le statut du mandat à l'écran** *(Actif / Clos / Échu)* | ⚠ **IL CHANGE, ET C'EST LE BUT.** Il est dérivé de `mandat_date_cloture`. Les 3 dates qui manquent reviennent → **3 mandats passeront de « Actif / Sous offre » à « Clos »** au registre. **C'est une correction, pas une régression — mais tu dois le savoir avant.** |
| **le tri et le filtre serveur** sur le statut du mandat | les 3 lignes changent de groupe. Rien d'autre. |
| **les 93 clôtures de HEKTOR** que `app_mandat` ne porte pas | ⛔ **CE PATCH N'Y TOUCHE PAS.** Elles sont déjà au registre *(elles viennent de `current_version`)*. Voir la question ② ci-dessous. |
| **le chemin immédiat du worker** *(`push_single_annonce`, ~1 min)* | ⚠ le carnet **local** a jusqu'à 24 h de retard. Donc une clôture faite **aujourd'hui**, suivie d'un re-push de **la même annonce dans la même journée**, retomberait à vide **jusqu'à la nuit**. C'est le cas qui reste, et c'est la question ③. |
| **la chaîne des mandats / les avenants / les versions** | aucune autre colonne touchée, aucun `ON CONFLICT` modifié. |
| **les affaires, le rapprochement, les pages publiques** | ne lisent pas cette colonne — mesuré : `mandat_date_cloture` n'apparaît que dans le registre et sa vue. |
| **`appliquer_contrat_mandat.py`** *(l. 593, aujourd'hui mal visé)* | ⚠ je **n'y touche pas** dans ce patch. Il continue d'écrire dans `app_view_generale`, où ça ne sert à rien — **inoffensif, mais trompeur**. À redresser ou à retirer : question ④. |
| **la nuit du 14/10** | le patch ne s'applique qu'au prochain run. **Rien ne change d'ici là.** |

### RETOUR ARRIÈRE
Un seul fichier Python, additif : on remet la ligne d'origine *(ou `git revert` du commit)*.
**Aucune écriture de schéma, aucun patch SQL, aucun redémarrage de worker.** La colonne existe
déjà et est refaite chaque nuit : il n'y a rien à défaire en base.

### CONTRÔLE PRÉVU *(avant tout run réel)*
1. `--dry-run` : le constructeur tourne, on compte combien de lignes prennent **notre** date
   *(attendu : 7)* et combien gardent celle de Hektor *(attendu : les 118 autres, inchangées)*.
2. **Le témoin inverse** : les 3 dates perdues **apparaissent** *(62966, 62774, 11939→09-18)*
   **et** aucune des 118 autres ne **disparaît**.
3. On recompte le registre entier avant / après : **aucune autre colonne ne doit bouger**.

### 🛑 CE QUE JE NE DÉCIDE PAS — 4 QUESTIONS POUR TOI

1. **Le périmètre du patch** : seulement ce qui est écrit ci-dessus *(le registre, l'écran)* —
   ou bien ?
2. **`app_mandat` et les 93 clôtures de Hektor.** La table `app_mandat` *(le futur registre,
   que l'écran ne lit pas encore)* porte 91 dates sur 26 855, et **93 dates que Hektor détient
   n'y entrent pas** — figées à la première insertion. Je peux l'ouvrir en une ligne
   *(`date_cloture = COALESCE(excluded.date_cloture, app_mandat.date_cloture)` — qui ne peut
   qu'**ajouter**, jamais effacer)*. **Maintenant, pour préparer la bascule — ou plus tard ?**
3. **Le trou résiduel du chemin immédiat** *(une clôture + un re-push le même jour)*. Je peux le
   fermer en faisant lire le carnet **dans Supabase** sur ce chemin-là. Ça ajoute une lecture
   réseau au worker. **On le ferme maintenant, ou on l'accepte ?**
4. **`appliquer_contrat_mandat.py`**, qui écrit depuis le 28/08 dans une table où ça ne sert à
   rien. **On le redresse, on le retire du run, ou on le laisse en l'état avec un commentaire ?**

*(Le **motif** de clôture du mandat : tu as dit « c'est un autre chantier ». Il n'est pas ici.)*

---

## 3c — AUDIT REFAIT À LA DEMANDE DE FRÉDÉRIC (13/10) : **IL AVAIT RAISON, J'AVAIS 3 ERREURS**

> *« audit de nouveau tu trompe il y a deja une vue registre des mandats et une table registre
> de mandat chez nous »* — et c'est exact. Mesuré dans Supabase, pas dans le front :

| objet | nature | colonnes | lignes | porte la date de clôture |
|---|---|---|---|---|
| `app_mandat_register_current` | **TABLE** | 69 | 24 505 | ✅ `mandat_date_cloture` |
| `app_registre_mandats_current` | **vue** | 71 | — | ✅ *(elle ne lit que la table ci-dessus)* |
| `app_mandat` | TABLE | 24 | 26 855 | `date_cloture` — ⚠ **rien ne la lit à l'écran** |

➡ **Ma question ② était trompeuse** : j'ai appelé `app_mandat` « le futur registre » et parlé de
« préparer la bascule ». Faux : **le registre existe, table ET vue, et il tourne.** `app_mandat`
est une **troisième** table, citée par **un seul** RPC *(`app_unlink_mandant_optimistic`)* et par
aucun écran. Ce n'est pas le registre.

### ❌ ERREUR 2 — « delta par empreinte » : FAUX

Le registre n'est pas mis à jour, il est **supprimé puis réinséré**
*(`push_upgrade_to_supabase.py` l. 1726-1737)* : chaque nuit on efface les lignes des annonces
**du parc vivant** qu'on va réécrire, puis on réinsère. Donc :

> ⭐ **notre date survit seulement quand l'annonce a QUITTÉ le parc vivant.** Sa ligne est alors
> **gelée** *(correctif du 29/09 : « un registre CONSERVÉ, c'est sa définition même »)* et
> personne ne la réécrit. Tant que l'annonce est **vivante**, sa ligne est effacée et refaite
> depuis la version de Hektor chaque nuit — et notre date part avec.

### ❌ ERREUR 3 — « 4 sur 7 » : FAUX AUSSI, et c'est la plus grave

`valeur_app` du carnet **ne veut pas dire « décision de l'app »**. Le magasin lit **le registre**
comme « ce que dit l'app » : pour les lignes `origine='observe'`, `valeur_app` est donc
**ce que le registre affichait**, d'origine inconnue. Les **vraies** clôtures de l'app sont
celles marquées `origine='cloture_app'`, avec `ecrit_par` : **il y en a 3.**

| annonce | mandat | notre date *(l'app)* | Hektor | **ce que l'écran montre** | parc |
|---|---|---|---|---|---|
| **62966** | 18842 | 2026-08-28 | — | ❌ **vide** | vivant → refait chaque nuit |
| **62774** | 18836 | 2026-08-30 | — | ❌ **vide** | vivant → refait chaque nuit |
| **24933** | 11939 | 2026-09-18 | **2026-10-05** | ⚠ **2026-10-05** *(Hektor)* | archivé → gelé |

➡ **0 sur 3.** Mon premier chiffre était le bon ; ma « correction » l'avait abîmé.

### ⚠ ERREUR 4 (la tienne et la mienne) — HEKTOR **A** DES DATES DE CLÔTURE

Mesuré dans le miroir : **212 dates de clôture sur 27 103 mandats (0,8 %)**. Donc « tous les
mandats n'ont pas de date de clôture » est vrai à 99,2 %, **pas à 100 %**. Et sur nos 3, Hektor
en a une pour **24933** — **15 jours après la nôtre** — et c'est **la sienne** qui s'affiche.
⚠ **Piège** : `hektor_mandat` porte plusieurs versions du même couple, dont une à `NULL` *(1951,
11824, 41433)*. Une lecture naïve prendrait la vide.

### ⭐ CONSÉQUENCE POUR LE CORRECTIF

Mon patch de l'étape 2 lisait `valeur_app` **sans filtre**. Il aurait donc **réinjecté 4 restes
de Hektor en les faisant passer pour nos décisions** — exactement le genre de blanchiment que
ce chantier combat. **Le patch doit ne faire confiance qu'à `origine='cloture_app'`.**

### CONSOMMATEUR OUBLIÉ DANS MA RUBRIQUE

`app_generate_mandat_echu_alerts` **supprime** l'alerte « Mandat échu » dès que le registre porte
une date de clôture. Donc effacer notre date peut **faire revenir une alerte sur un mandat que tu
as clos**. Mesuré aujourd'hui : **0 alerte** sur les 7 *(dates de fin en 2027, ou statut clos)* —
**pas de dégât constaté**, mais la dépendance existe et doit figurer dans la rubrique.

---

## 3c — DÉCISION DE FRÉDÉRIC, 13/10 : **« 1 celle de l'app »**

Quand les deux dates existent, **c'est la nôtre qui gagne**. *(Cas mesuré : 24933 — nous
18/09, Hektor 05/10 ; c'est 18/09 qui doit s'afficher.)* Le patch applique donc :
`clôture de l'app (origine='cloture_app') d'abord, Hektor ensuite, jamais du vide`.

## 3c — QUESTION 2 EXPLIQUÉE : `appliquer_contrat_mandat.py`, OÙ VA SON ÉCRITURE ?

**Ce qu'il a été construit pour faire** *(son en-tête, 28/08)* :
> *« C.13-b — L'ENDROIT OÙ LA CLÔTURE DE MANDAT CESSE D'APPARTENIR À HEKTOR. […] Il n'écrit que
> la colonne `mandat_date_cloture`, et seulement pour le mandat COURANT de l'annonce. **Les
> mandats des cycles passés se traitent dans le constructeur du registre, qui lit le même
> magasin.** »*

⭐ **Donc le correctif que je propose était prévu dès le départ — il n'a jamais été écrit.**

**Ce qu'il fait réellement.** Mesuré, chaînon par chaînon :

| étape | mesure |
|---|---|
| il lit le carnet, garde les valeurs non vides | ✅ la règle « vide ne gagne pas » est bien là |
| il écrit `app_view_generale.mandat_date_cloture` | ✅ la colonne **existe** localement *(163 colonnes)* — donc **il n'échoue pas, il écrit** |
| le push envoie-t-il cette colonne sur la fiche ? | ❌ **non** |
| la colonne existe-t-elle sur la fiche Supabase ? | ❌ **non** — `mandat_date_cloture` n'existe **que** dans `app_mandat_register_current`. Ni `app_dossier_current`, ni l'index archive, ni l'index historique ne l'ont *(tous les trois ont `mandat_date_fin`, pas celle-ci)* |
| le constructeur du registre la relit-il sur la fiche ? | ❌ **non** — l. 1817 et 2401 prennent `current_version.get("cloture")`, **la version de Hektor** |

➡ **Son écriture meurt dans la base locale, qui est détruite et refaite la nuit suivante.**
Il tourne chaque nuit depuis le 28/08 et **ne produit rien**. Ce n'est pas un bug bruyant :
c'est un échec silencieux, le genre que le chantier ④ traque.

### ⚠ ET UN SECOND DÉFAUT, LATENT

Sa table de travail a pour clé **`hektor_annonce_id` seul** *(`TEXT PRIMARY KEY`)*, avec
`INSERT OR REPLACE`. Si une annonce portait **deux** mandats clos, **le dernier lu écraserait
l'autre en silence**, et la date d'un mandat se retrouverait sur un autre.
Mesuré aujourd'hui : **0 annonce concernée** — donc **ça ne mord pas**. Mais c'est exactement
la situation que ce chantier va créer, puisqu'il s'agit de se mettre à clore des mandats.

### LES TROIS OPTIONS, ET CE QU'ELLES COÛTENT

| | |
|---|---|
| **A — le retirer du run** *(recommandé)* | Une ligne retirée de `run_full_pipeline.ps1` *(l. 593)*. Le fichier **reste sur le disque**, avec son en-tête mis à jour : « remplacé le 13/10 par le constructeur du registre, qui écrit là où la donnée va vraiment ». On ne perd pas l'histoire, et plus rien ne fait semblant de marcher. ⚠ **Touche le run → ton accord.** |
| **B — le redresser** | Il faudrait qu'il écrive au grain **(annonce, n° de mandat)**… or il n'existe aucune table locale à ce grain qui monte chez nous : le registre est **fabriqué au moment du push**. Le redresser revient donc à **refaire le correctif une seconde fois, ailleurs**. Deux endroits à maintenir pour un seul résultat. |
| **C — le laisser avec un commentaire** | Coût : quelques secondes par nuit et une colonne locale morte. Inoffensif. ⚠ Mais il reste **trompeur** : son en-tête dit « l'endroit où la clôture cesse d'appartenir à Hektor », et le prochain qui le lira — moi compris — le croira encore. |

---

## 3c — AUDIT REFAIT (3ᵉ fois), SUR LA DEMANDE DE FRÉDÉRIC DU 13/10

> *« il y a donc le registre des mandats avec date de début et date de fin ; la date de clôture
> doit donc être une colonne supplémentaire, et cette colonne doit être maj éventuellement par
> Hektor mais **surtout pas l'app** — mais cette demande n'a pas à être transmise à Hektor. »*

### ⭐ CE PATRON EXISTE DÉJÀ DANS LE REGISTRE — POUR LES PHOTOS

La vue `app_registre_mandats_current`, aujourd'hui, fait **exactement** ce que Frédéric décrit :

```sql
COALESCE(NULLIF(btrim(photo_url_listing_app), ''), photo_url_listing) AS photo_url_listing,
...
photo_url_listing_app,                      -- la nôtre, nue
photo_url_listing AS photo_url_listing_hektor   -- celle de Hektor, nue
```

Et la mécanique complète, mesurée :

| | |
|---|---|
| la colonne `_app` est-elle écrite par le run ? | ❌ **zéro occurrence** dans `export_app_payload.py` **et** dans `push_upgrade_to_supabase.py` |
| survit-elle au `delete`+`insert` de la nuit ? | ❌ **non** — elle revient à `NULL` sur les lignes refaites |
| alors comment est-elle pleine à **24 497 / 24 505** ? | ⭐ **une étape de re-pose APRÈS le push** : `run_full_pipeline.ps1` **l. 1510** → `Console/remplir_adresses_photos.js` → RPC `app_photos_remplir_adresses_registre` |
| déclencheurs sur la table ? | **0** — rien de caché |

➡ **Le projet a donc déjà un patron éprouvé pour « une colonne qui est à nous, dans une table
que la nuit détruit ».** Il n'y a rien à inventer : colonne `_app` + re-pose après le push + la
vue qui donne la nôtre d'abord, et expose les deux séparément.

### ⛔ ET LA MESURE QUI TRANCHE LA FORME : LES DROITS

| table | RLS | politiques |
|---|---|---|
| `app_mandat_champ_app` *(le carnet)* | **activée** | ⛔ **0 politique — personne ne peut la lire** |
| `app_mandat_register_current` | activée | 1 *(SELECT, utilisateurs actifs)* |

➡ J'avais envisagé une vue qui **joindrait le carnet** *(aucune re-pose nécessaire)*. **C'est
impossible** : la vue est `security_invoker=on`, le carnet n'a **aucune** politique de lecture,
donc la date serait **vide pour tout le monde**. **L'intuition de Frédéric est la seule qui
tienne : il faut une colonne.**

### ⭐⭐ LA CAUSE RACINE, ENFIN TROUVÉE — ET ELLE EXPLIQUE MON ERREUR 3

Aujourd'hui, le worker écrit notre date **dans la colonne de Hektor** :
```js
// console_job_worker.js -- « confort d'affichage, SANS AUTORITE »
PATCH app_mandat_register_current ... { mandat_date_cloture: date }
```
Puis `magasin_mandat_app.py` relit **ce même registre** comme « ce que dit l'app »
*(l. 204 : « CE QUE DIT L'APP. Relu EN DIRECT dans Supabase »)*.

➡ **La boucle est fermée : nous relisons notre propre écriture comme si elle faisait autorité.**
C'est pour ça que 4 lignes du carnet portaient une `valeur_app` qui n'était la décision de
personne — et c'est pour ça que je me suis trompé en les comptant comme des clôtures de l'app.
**La demande de Frédéric supprime la cause, pas le symptôme.**

### CE QUE ÇA DONNE, POINT PAR POINT

| | aujourd'hui | après |
|---|---|---|
| `mandat_date_cloture` | ⚠ écrite par **Hektor** *(la nuit)* **ET par l'app** *(le worker)* | **Hektor seul**. L'app n'y touche plus jamais. |
| notre date | nulle part de durable | **`mandat_date_cloture_app`**, à nous seuls |
| ce que l'écran affiche | tantôt la nôtre, tantôt celle de Hektor, tantôt rien | la nôtre si elle existe, celle de Hektor sinon — **et les deux lisibles séparément** |
| envoyé à Hektor | non | **non** *(inchangé — c'est voulu)* |
| le carnet | source de vérité, illisible par l'écran | **inchangé** : il reste la source, et c'est lui qui alimente la re-pose |

---

## 3c — « JE VEUX QUE LA DATE DE CLÔTURE SOIT SAISISSABLE DANS MON APP » (13/10)

### CE QUI EXISTE DÉJÀ À L'ÉCRAN — mesuré

Le front **lit** `mandat_date_cloture` en **4 endroits** :
`mandatStatutForRegister` *(App.tsx l. 7667)* et son jumeau *(api.ts l. 85)* en dérivent le
**statut du mandat** — Actif / Clos / Échu ; l. 18267 l'affiche dans le détail *(« Cloture »)* ;
l. 26752 la relit. Elle est demandée dans deux `select` du registre *(api.ts l. 6162, 6221)*.

⛔ **Mais il ne l'écrit NULLE PART.** Aucun champ, aucun formulaire. Le seul chemin actuel est
la modale « changer le statut → Clos », qui passe par le worker.

### ⚠ ET UN OBSTACLE À CONNAÎTRE : LE FRONT NE PEUT PAS ÉCRIRE LE CARNET

`app_mandat_champ_app` a **RLS activée et 0 politique** : le front ne peut **ni la lire ni
l'écrire**. Une saisie ne peut donc PAS taper directement dans le carnet.
➡ Il faut un **RPC `SECURITY DEFINER`**, exactement comme tous les autres gestes du projet
*(`app_change_annonce_status_optimistic`, `app_archive_annonce_optimistic`…)*.

### LE MODÈLE À RETENIR : **LE COFFRE ET LA VITRINE**

| | **le coffre** `app_mandat_champ_app` | **la vitrine** `app_mandat_register_current` |
|---|---|---|
| à quoi ça sert | **la date y VIT** | la date s'y **AFFICHE** |
| qui la voit | personne *(RLS, 0 politique)* | l'écran |
| la nuit | **intacte, jamais touchée** | ⚠ **détruite et refaite** pour le parc vivant |
| qui l'écrit | le RPC *(notre geste)* | le RPC *(tout de suite)* **+ la re-pose** *(après le push)* |

⭐ **C'est le point à comprendre** : la table du registre est **détruite chaque nuit**. Une date
écrite là-dedans et nulle part ailleurs **disparaît**. D'où le coffre. Et c'est précisément le
patron déjà en service pour les photos *(24 497 lignes)*.

### LES 5 PIÈCES DU CHANTIER

| | pièce | touche | accord |
|---|---|---|---|
| **1** | **SQL** : colonne `mandat_date_cloture_app` + la vue sur le modèle des photos *(la nôtre d'abord, Hektor sinon, les deux lisibles)* | Supabase | tu colles |
| **2** | **RPC** `app_set_mandat_cloture_optimistic(annonce, n° mandat, date)` : écrit **le coffre ET la vitrine** dans la même transaction. Refuse une date illisible, refuse un couple inconnu. | Supabase | tu colles |
| **3** | **Le champ à l'écran** : saisie de la date sur la fiche du mandat → appelle le RPC | front *(Vercel se déploie seul)* | ton go |
| **4** | **La re-pose après le push** : relit le coffre, repose notre colonne — comme `remplir_adresses_photos.js` l. 1510 | **le run** | ton go |
| **5** | **Le worker** : son `PATCH` quitte la colonne de Hektor pour la nôtre *(ou appelle le RPC n° 2)* | ⚠ **4 services à redémarrer** | ton go |

### CE QUE ÇA DONNE, CONCRÈTEMENT

> Tu ouvres un mandat, tu tapes **28/08/2026**, tu valides.
> → le RPC écrit **le coffre** *(ça fait foi)* **et la vitrine** *(tu le vois tout de suite)*
> → le statut du mandat passe à **Clos** à l'écran, tri et filtre compris *(le front le dérive déjà)*
> → l'alerte « Mandat échu » **disparaît** *(`app_generate_mandat_echu_alerts` la supprime dès qu'une clôture existe)*
> → **rien ne part chez Hektor** *(voulu)*
> → la nuit refait le registre, **la re-pose remet ta date**
> → si Hektor en ajoute une plus tard, **la tienne reste affichée** *(décision du 13/10)*, et la
>   sienne reste lisible à côté.

---

## 3c — DÉCISIONS DE FRÉDÉRIC, 13/10 (suite)

- **L'ordre est validé** : **1 + 2** *(SQL)* → **4** *(la re-pose)* → **3 + 5** *(l'écran, le worker)*.
- **La saisie va sur la FICHE DU MANDAT** — et il précise : *« il y a des liens aussi dans la
  rubrique mandat de l'annonce et aussi dans le modal changement de statut »*.
  ➡ **3 points d'entrée** à couvrir en pièce 3 : la fiche du mandat, la rubrique « Mandat » de
  l'annonce, la modale de changement de statut. *(Noté pour la pièce 3, pas pour maintenant.)*

## 3c — ÉTAPE 2 : PIÈCES 1 + 2 *(présenté le 13/10, EN ATTENTE DU « VAS-Y »)*

### MESURES PRÉALABLES, FAITES

| | |
|---|---|
| le couple (annonce, n° de mandat) est-il unique au registre ? | ✅ **24 505 lignes = 24 505 couples**, 0 sans numéro, 0 sans annonce |
| la clé du coffre **côté Supabase** | **`(hektor_annonce_id, numero_mandat, champ)`** — le couple. `hektor_mandat_id` est **facultatif** |
| ⚠ piège | la table **locale** du même nom a une **autre clé** : `(hektor_annonce_id, hektor_mandat_id, champ)`. Même nom, clé différente. |
| qui lit `mandat_date_cloture` dans la base ? | **exactement deux** : la vue, et `app_generate_mandat_echu_alerts` *(SECURITY DEFINER)* |

### PIÈCE 1 — LA COLONNE, LA VUE, ET L'ALERTE

1. `alter table app_mandat_register_current add column if not exists mandat_date_cloture_app text;`
2. la vue refaite **à l'identique** *(ses 71 colonnes, mêmes noms, même ordre)*, avec **trois**
   changements seulement — le patron exact des photos :
   ```sql
   COALESCE(NULLIF(btrim(mandat_date_cloture_app), ''), mandat_date_cloture) AS mandat_date_cloture,
   mandat_date_cloture_app,                              -- la nôtre, nue
   mandat_date_cloture AS mandat_date_cloture_hektor     -- celle de Hektor, nue
   ```
   → **71 colonnes deviennent 73.** Aucun nom retiré, aucun renommé.
3. ⚠ **`app_generate_mandat_echu_alerts` lit la TABLE, pas la vue.** Sans la toucher, l'alerte
   « Mandat échu » **ne disparaîtrait pas** sur un mandat que tu clos — **la promesse que j'ai
   faite serait fausse.** On y applique le même `COALESCE`.
4. **la re-pose des 3 clôtures déjà faites**, depuis le coffre *(`origine='cloture_app'`)* :
   62966 → 2026-08-28 · 62774 → 2026-08-30 · 24933 → 2026-09-18.

### PIÈCE 2 — LE RPC `app_set_mandat_cloture_optimistic`

`SECURITY DEFINER`, propriétaire `postgres`, sur le modèle des gestes de 3a/3b :
- **refuse** une date qui n'est pas `AAAA-MM-JJ`, **refuse** un couple absent du registre
  *(`mandat_introuvable`)* — on n'écrit jamais à côté ;
- écrit **le coffre** *(upsert sur le couple, `origine='cloture_app'`, `ecrit_par` = l'utilisateur)*
  **et** la colonne `mandat_date_cloture_app` du registre, **dans la même transaction** ;
- une date **vide efface la nôtre** → celle de Hektor réapparaît. C'est le retour arrière de
  l'utilisateur quand il s'est trompé.
- **n'envoie rien à Hektor.**

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

| | |
|---|---|
| **le statut du mandat à l'écran** *(Actif / Clos / Échu)* | ⚠ **IL CHANGE, ET C'EST LE BUT** : le front le dérive de `mandat_date_cloture` *(App.tsx l. 7667, api.ts l. 85)*. **3 mandats** passeront à **Clos**. |
| le tri et le filtre serveur du registre | suivent ces 3 lignes. Rien d'autre. |
| **les alertes « Mandat échu »** | couvertes par le point 3 ci-dessus. Mesuré aujourd'hui : **0 alerte** sur ces 3 *(dates de fin en 2027, ou statut clos)* → **aucune notification ne bougera**. |
| le front qui lit la vue | il demande des colonnes **nommées** *(api.ts l. 6162, 6221)*, jamais `select *` → **ajouter deux colonnes ne casse rien**. |
| le run de nuit | ⛔ **pas touché par les pièces 1-2.** Le push ne connaît pas la nouvelle colonne, donc il ne l'écrit pas — mais il **efface la ligne** du parc vivant : d'où la **pièce 4**. ⚠ **Sans la pièce 4, les 3 dates reposées repartiront à la prochaine nuit.** Je le dis net. |
| le worker | ⛔ **pas touché.** Il continue d'écrire dans la colonne de Hektor jusqu'à la pièce 5. Conséquence : le `COALESCE` affichera la **nôtre** *(colonne `_app`)*, donc son écriture devient **sans effet visible** — inoffensive, mais à nettoyer en pièce 5. |
| `app_photos_remplir_adresses_registre` | ne touche que les colonnes photo. Aucun lien. |
| les affaires, le rapprochement, les pages publiques | ne lisent pas cette colonne — **mesuré : 2 consommateurs en tout**. |

### RETOUR ARRIÈRE
`supabase/patch_chantier3_3c_cloture_mandat_app_2026-10-13_INVERSE.sql` : remet la vue
d'aujourd'hui *(empreinte vérifiée)*, remet l'alerte d'aujourd'hui, supprime le RPC, et vide la
colonne. ⚠ **La colonne elle-même est conservée** *(un `drop column` détruirait la saisie ; on la
laisse, vide et inerte — elle n'est lue que par la vue et l'alerte, revenues à leur état)*.

### CONTRÔLE PRÉVU *(dans la répétition, tout annulé à la fin)*
1. **le témoin inverse** : les 3 dates **apparaissent** dans la vue *et* les **118** autres
   lignes à date de clôture **ne changent pas** — comptées avant / après.
2. le RPC éprouvé **pour de vrai** : une saisie sur un mandat, relue dans la vue ; un couple
   bidon → refus `mandat_introuvable` ; une date `32/13/2026` → refus.
3. **l'effacement** : date vide → la nôtre part, celle de Hektor réapparaît.
4. l'alerte « Mandat échu » recomptée avant / après : **doit rester à l'identique**.
5. la vue recomptée : **73 colonnes**, et les 71 anciens noms **tous présents**.

## 3c — ÉTAPE 4 : CODÉ (13/10) — pièces 1 et 2, **en attente du collage**

| fichier | ce qu'il fait |
|---|---|
| `supabase/patch_chantier3_3c_cloture_mandat_app_2026-10-13.sql` | la colonne · la vue refaite **depuis elle-même** · l'alerte · la re-pose · le RPC + les droits |
| `…_INVERSE.sql` | la vue **détruite et recréée** à l'identique *(un `CREATE OR REPLACE` ne sait pas retirer une colonne)* **+ les droits rendus** *(`authenticated=r`, `service_role=all`, relevés avant)* · l'alerte rendue · le RPC supprimé · la colonne **vidée, conservée** |
| `…_REPETITION.sql` | tout, éprouvé pour de vrai, puis tout défait, puis **annulé** |

**Contrôles statiques faits** : balises `$tag$` toutes paires · 1 `BEGIN` / 1 `COMMIT` par
fichier · **0 CRLF** · le message final porte **34 mesures pour 34 emplacements**.

**Les 6 épreuves du RPC dans la répétition** : une saisie sur un mandat choisi
*(`ORDER BY` — un `LIMIT` sans ordre ne prouve rien)*, relue **dans la vue ET au carnet** avec
son auteur · **l'effacement sur 24933**, qui doit faire réapparaître **la date de Hektor
(2026-10-05)** · et quatre refus : mandat inconnu, `13/10/2026`, `2026-13-32`, anonyme.

⚠ **À dire à Frédéric** : refaire la vue prend un verrou exclusif dessus. Pendant la répétition
*(quelques secondes)*, l'écran **Registre des mandats** attend. À lancer quand personne n'y est.

### ⚠ DÉFAUT CORRIGÉ AVANT APPLICATION — 42601, LE MESSAGE FINAL

Premier collage de la répétition : `ERROR: 42601: syntax error at or near "E'\n  ── LA VUE…"`.

**La cause, et elle est à retenir.** Deux règles de Postgres se cumulent :
1. le **format d'un `RAISE` doit être un littéral** — pas une expression, donc pas de `||` ;
2. un littéral **`E'…'` ne peut pas CONTINUER une concaténation implicite** *(celle qui colle
   deux littéraux séparés par un retour à la ligne)*.

➡ Un message long avec des `\n` est donc **impossible** en concaténation implicite.
**La parade** : bâtir le message dans une variable avec **`format()`** — dont le premier
argument est une **expression**, donc les `E'…'` s'y joignent par `||` — puis
`RAISE EXCEPTION '%', v_msg;`. Les emplacements passent de `%` à **`%s`**.

⚠ **Et un second piège, du shell celui-là** : ma première réparation est passée par un heredoc
Bash, qui a **mangé les `\n`** — le message est devenu une seule ligne de 1 523 caractères.
*(Leçon déjà connue : écrire des fichiers à travers le shell détruit les échappements. J'ai
refait la réparation par un script sur disque.)*

**Contrôles statiques repassés** : balises paires · 1 `BEGIN` / 1 `COMMIT` · 0 CRLF ·
**34 emplacements pour 34 arguments** · et **aucun autre `RAISE` à plusieurs littéraux** dans
les trois fichiers.

## 3c — ÉTAPE 5 : LE CONTRÔLE, RÉPÉTITION PASSÉE (13/10)

| mesure | résultat |
|---|---|
| **la vue** | `5c64469d…` → `57ec4573…` → **`5c64469d…`** — rendue **à l'identique** |
| ses colonnes | **71 → 73 → 71**, et les **71 anciens noms tous là, dans l'ordre** |
| **l'alerte « Mandat échu »** | `d45b9290…` → `67918ee6…` → **`d45b9290…`** — rendue à l'identique |
| dossiers dont le sort change à cause de notre colonne | **0** *(comme prévu)* |
| les autres lignes à date de clôture | **117 avant = 117 après** ✅ |
| **62966/18842** | écran **(vide)** → **2026-08-28** *(la nôtre)* |
| **24933/11939** | écran **2026-10-05** *(Hektor)* → **2026-09-18** *(la nôtre)* — la décision du 13/10 |
| **(a) la saisie** | `ok:true` · relue **2026-10-13** dans la vue **et** au carnet, `origine=cloture_app`, auteur = l'email de Frédéric |
| **(b) l'effacement** | `ok:true` · l'écran montre **2026-10-05** — **la date de Hektor réapparaît**, prouvé |
| **(c→f) les 4 refus** | `mandat_introuvable` · `date_illisible` · `date_inexistante` · `non_authentifie` |
| **le retour arrière** | le RPC : **1 → 0** |

### ⚠ LA SEULE LIGNE QUI N'EST PAS ÉGALE, ET POURQUOI CE N'EST PAS UN DÉFAUT

`avant 117 / apres 117 / rendue 118`. **C'est mon test (b) qui l'a produite**, pas le patch :
l'effacement de 24933 **supprime sa ligne du carnet**. Or mon décompte des « autres » exclut
les couples qui ONT une ligne au carnet. Après le retour arrière, 24933 n'est plus « à nous »
→ elle rejoint les autres → **117 + 1 = 118**. L'arithmétique boucle : le registre porte
**118** dates de clôture en tout, dont **1** à nous.
➡ **La preuve utile est intacte : 117 avant = 117 après.** Le patch ne touche aucune autre
ligne. ⚠ Mais c'est un **défaut de ma mesure**, pas du patch : un témoin ne devrait pas
dépendre d'une table que l'épreuve modifie. Noté.

### ⚠⚠ UNE PERTE QUE JE NE M'EXPLIQUE PAS — **62774**

La répétition annonce **2 clôtures au carnet**, pas 3. Mesuré :

| | |
|---|---|
| le carnet **Supabase** | **2 lignes seulement** : 62966 *(28/08, par `gonzalez@…`)* et 24933 *(18/09)* |
| le carnet **local** | **3** — dont **62774/18836 = 2026-08-30**, `origine='cloture_app'`, **vue une seule fois : le 31/08 à 04:30**, jamais depuis |
| d'où vient la copie locale ? | **uniquement de la lecture du carnet Supabase** *(`magasin_mandat_app.py`, seconde source)* — donc **la ligne Y ÉTAIT le 31/08** |
| 62774 est-elle encore dans le miroir ? | ✅ **oui** *(mandat 648, n° 18836)* — le magasin saurait donc la rafraîchir si elle existait |
| qui, dans le code, supprime dans ce carnet ? | ⛔ **personne.** Aucun `delete`, aucun `truncate` — ni le run, ni le worker, ni un patch |
| la clé primaire a-t-elle changé ? | ❌ non — `(annonce, numero_mandat, champ)` **depuis sa naissance le 28/08** |
| et le 30/08, le patch C.4 mesurait | **« `app_mandat_champ_app` 1 ligne »** — la chronologie colle : 1 le 30/08, 2 le 31/08, 3 le 03/09, **2 aujourd'hui** |

➡ **Une ligne du coffre a disparu entre le 31/08 et aujourd'hui, et rien dans le code ne
l'explique.** Je ne sais pas pourquoi. Hypothèses non prouvées : une suppression à la main
dans le tableau de bord Supabase, ou un script hors dépôt.
⚠ **Conséquence directe** : le patch reposera **2** clôtures, pas 3. **La clôture de 62774 du
30/08 ne reviendra pas** — elle n'existe plus nulle part. Le nouveau champ permettra de la
ressaisir.
⚠ **Et ça nuance ce que j'ai affirmé** : « le coffre, la nuit ne le touche jamais » est vrai
**du code**. Ça ne veut pas dire que rien ne peut l'effacer. **1 clôture sur 3 perdue en six
semaines**, par une route inconnue. Une sentinelle sur ce carnet est à prévoir.

### ⭐ L'ALERTE DU 62774 : LEVÉE PUIS REFERMÉE PAR MOI-MÊME

J'étais parti écrire « 1 clôture sur 3 perdue, route inconnue, sentinelle à poser ».
**Ma propre mémoire a tranché : 62774 EST LE BAC À SABLE DU PROJET** — essais des 25/08,
28/08, 29/08, 01/09 et 11/10 — et la note `ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md` se
termine par **« Bac a sable 62774 : propre »**, suivie de trois suppressions.

➡ **C'était une clôture d'ESSAI, retirée avec les autres traces. Les 2 clôtures réelles sur 2
sont intactes. Rien n'a été perdu, et il n'y a pas de sentinelle à poser.**
⚠ **Non prouvé** : je n'ai pas retrouvé l'acte de suppression. L'explication est très forte,
pas démontrée.

**LEÇON (CLAUDE.md n° 18)** : avant de crier à la perte, **écarter les biens d'essai** —
62963, 62774, 284/107, 15633/49544, contact 10355757.

## 3c — ÉTAPE 6 : PATCH APPLIQUÉ ET CONTRÔLÉ EN BASE (13/10)

| contrôle | mesure |
|---|---|
| la colonne `mandat_date_cloture_app` | ✅ posée |
| la vue | ✅ **73 colonnes**, empreinte **`57ec45730c9cdd536178b211cc19234d`** — *exactement celle que la répétition avait annoncée* |
| l'alerte « Mandat échu » | ✅ empreinte **`67918ee68dae6168f60887b9f90abf84`** — *idem* |
| le RPC | ✅ posé · droits **`postgres=X · authenticated=X · service_role=X`** — **`anon` absent**, `PUBLIC` retiré |
| nos dates reposées | ✅ **2** |
| total affiché au registre | **119** *(118 + 62966 qui n'en avait aucune ; 24933 change de valeur, pas de compte)* |

**Ce que l'écran montre maintenant :**

| annonce | mandat | l'écran | la nôtre | celle de Hektor |
|---|---|---|---|---|
| **62966** | 18842 | **2026-08-28** | 2026-08-28 | (vide) |
| **24933** | 11939 | **2026-09-18** | 2026-09-18 | **2026-10-05** *(lisible à côté)* |

⚠ **PROCHAINE PIÈCE, ET ELLE EST URGENTE : la 4 (la re-pose après le push).** Sans elle, ces
deux dates **repartent à la prochaine nuit** — la nuit efface et réinsère la ligne de registre
des annonces du parc vivant. Modèle à recopier : run **l. 1510**,
`Console/remplir_adresses_photos.js` → RPC `app_photos_remplir_adresses_registre`.
