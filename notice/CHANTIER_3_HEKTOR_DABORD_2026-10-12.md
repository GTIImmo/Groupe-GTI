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

### ⭐⭐ ET LA VÉRITÉ COMPLÈTE : **LES TROIS CLÔTURES ÉTAIENT DES ESSAIS**

En rangeant, un fichier non suivi m'a mis sur la piste :
`notice/SUPPRESSION_ESSAIS_3_2_24933_2026-09-07.json` — une **sauvegarde datée avant un geste
destructif** *(la règle de la maison)*, qui dit : *« Deux lignes d'essai de la tâche 3.2 »*.
Il y en a **quatre** de cette famille, tous sur **24933**.

Et `notice/CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md` le dit **trois fois** :
> *« la preuve A.3-a sur **l'annonce d'essai 62966** »* · *« sur l'annonce d'essai 62966 »* ·
> *« le patron de la clôture (C.13-a et b) […] **Essai sur l'annonce 62966 (mandat 660)** »*

⭐ **Et c'est exactement notre ligne** : 62966, mandat Hektor **660**, n° **18842**.

| annonce | ce que c'est |
|---|---|
| **62966** | **l'annonce d'essai**, désignée explicitement pour éprouver la clôture |
| **62774** | **le bac à sable** *(« Bac a sable 62774 : propre »)* |
| **24933** | **le bien d'essai des tâches 3.2 / 3.4** *(4 fichiers de suppression)* |

➡ **AUCUN UTILISATEUR RÉEL N'A JAMAIS CLOS UN MANDAT DANS L'APP.** Ce qui colle mot pour mot
à Frédéric : *« tous les mandats n'ont pas de date de clôture. **Ce sera** mon app qui va le
gérer »* — **au futur**.

**Ce que ça corrige dans ce que j'ai écrit :**
- « **3 clôtures faites dans l'app** » laissait croire à des gestes métier. **C'étaient 3
  essais.** Le défaut mesuré était réel *(la date ne tenait pas)*, mais **il n'a jamais perdu
  une donnée de production** — on l'a réparé **avant** que ça compte. C'est une meilleure
  nouvelle que celle que j'ai annoncée.
- l'alerte du 62774 est **définitivement close** : la pratique de suppression des essais est
  **documentée quatre fois**, avec sauvegarde datée.
- ⚠ **Les 2 dates que le patch vient de reposer sont donc des données d'essai**, affichées au
  registre sur deux biens d'essai. ⭐ **Je propose de les LAISSER** : ce sont précisément les
  **témoins** qui prouveront la **pièce 4** demain matin — si elles survivent à la nuit, la
  re-pose marche. À retirer quand la pièce 4 sera prouvée.

---

## 3c — PIÈCE 4, ÉTAPE 2 : LA RE-POSE *(présentée le 13/10, EN ATTENTE DU « VAS-Y »)*

### L'AUDIT CHANGE LE PÉRIMÈTRE : IL Y A **DEUX** CHEMINS QUI EFFACENT, PAS UN

| chemin | ce qu'il fait au registre | notre colonne |
|---|---|---|
| **le run de nuit** *(`push_upgrade`, l. 1726-1737)* | `delete` par annonce **puis** `insert` | ⛔ **effacée** |
| **le chemin immédiat du worker** *(`push_single_annonce`, l. 358-360 puis 630)* | `delete_target_remote` **efface toujours** les lignes de registre de l'annonce, puis `upsert` | ⛔ **effacée, ~1 min après n'importe quel geste sur cette annonce** |

⭐ **Et le commentaire du run explique tout** *(l. ~1495)* : *« les colonnes sœurs SURVIVENT
(PostgREST en merge-duplicates ne touche que les colonnes du payload — vérifié le 27/09 sur
table jetable) »*. ➡ **Vrai pour la fiche et les index** *(upsert)*, **faux pour le registre**
*(delete+insert)*. C'est précisément pourquoi
`app_photos_remplir_adresses_registre` existe : *« le registre RECOPIE ce que les index savent »*.

⚠ **Le patron des photos a donc le MÊME trou sur le chemin immédiat, et le projet l'accepte** :
*« Inoffensif tant que Hektor vit, INACCEPTABLE après la coupure. »* Pour la clôture, le trou se
voit tout de suite : clore un mandat puis faire **n'importe quel** geste sur l'annonce, et la
date part pour la journée.

### CE QUE JE PROPOSE — **un RPC, deux appelants**

**① Le RPC `app_reposer_cloture_mandat_app(target_annonce default null, plancher_registre default 10000)`**
`SECURITY DEFINER`. **Le registre reflète le carnet** : il pose `mandat_date_cloture_app` là où
le carnet dit *(`champ='mandat_date_cloture'`, `origine='cloture_app'`, valeur non vide)*, et il
**efface** là où le carnet ne dit plus rien — sinon une clôture annulée resterait affichée pour
toujours. Sans portée = tout le parc ; avec portée = une seule annonce.
⚠ **Garde-fou en base, copié des photos** : il **REFUSE** si le registre est sous son plancher
*(10 000 ; il en porte 24 505)* — sans lui, un push cassé **viderait nos clôtures**.
⭐ Le plancher est un **paramètre** pour que la répétition puisse **prouver le refus** sans rien
supprimer *(on l'appelle avec 1 000 000)*.

**② Appelant « nuit » — le run**, une étape après le push, sur le modèle **exact** de la l. 1510
*(`Invoke-OptionalStepWithRetry`, `WorkerKey` pour le heartbeat, **non bloquante**)*, via
`Console/reposer_cloture_mandat.js`. Script séparé et pas greffé sur les photos : un heartbeat
par sujet, sinon on ne sait plus qui a échoué.

**③ Appelant « immédiat » — `push_single_annonce_to_supabase.py`**, un appel RPC **ciblé sur
l'annonce**, juste après son upsert du registre.
⭐⭐ **AUCUN REDÉMARRAGE DE WORKER** : le worker lance ce fichier **en sous-processus**
*(`console_job_worker.js` l. 4042-4047 : `args: ["phase2/sync/push_single_annonce_to_supabase.py", "--hektor-annonce-id", id]`)* → la correction prend effet **au travail suivant**.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

| | |
|---|---|
| **le run** | une étape de plus, **non bloquante** *(comme les photos)* : un échec sort en `WARN` + heartbeat, il n'arrête pas le run. Coût mesuré côté photos : **~1 s**. |
| **le chemin immédiat** | **+1 appel réseau** (~100 ms) dans un script qui en fait déjà des dizaines. ⚠ Si l'appel échoue, **le push ne doit pas échouer** : on l'enveloppe et on le journalise. |
| ⚠ **l'effacement** | **le registre suivra le carnet** : effacer une clôture au carnet la fait disparaître du registre. **C'est voulu** — mais c'est un geste destructif, et c'est pour ça qu'il est **borné par le plancher**. |
| les colonnes sœurs des **photos** | ⛔ **pas touchées** : le RPC n'écrit **qu'une** colonne. |
| **l'alerte « Mandat échu »** | suit **automatiquement** *(elle lit déjà notre colonne depuis les pièces 1-2)*. |
| `mandat_date_cloture` *(à Hektor)* | ⛔ **jamais touchée.** |
| le worker, les 4 services | ⛔ **aucun redémarrage** *(mesuré ci-dessus)*. |
| **la nuit du 14/10** | c'est le **premier essai réel** : les **2 dates d'essai doivent survivre**. Si elles sont là demain matin, la pièce 4 est prouvée. |

### RETOUR ARRIÈRE
`…_INVERSE.sql` supprime le RPC · on retire l'étape du run *(une ligne)* · on retire l'appel du
script Python *(additif, enveloppé)*. **Aucun schéma touché.** La colonne reste, avec ce qu'elle
porte.

### CONTRÔLE PRÉVU
1. **répétition SQL** : poser → compter · effacer une ligne du carnet → **la colonne doit se
   vider** · reposer → **la valeur revient** · appeler avec un plancher impossible → **refus
   prouvé** · et le **témoin inverse figé AVANT les épreuves** *(ma leçon du jour)*.
2. **`--dry-run` du script Python** pour vérifier qu'il n'écrit rien de plus.
3. ⏰ **l'épreuve qui compte : demain matin.** Les 2 dates d'essai encore là = la nuit ne les
   efface plus.

## 3c — PIÈCE 4, ÉTAPE 4 : CODÉE (13/10) — **en attente du collage**

| morceau | fichier |
|---|---|
| **la fonction** + l'enregistrement du battement de cœur | `supabase/patch_chantier3_3c_piece4_repose_cloture_2026-10-13.sql` |
| le retour arrière | `…_INVERSE.sql` *(le RPC, la ligne de registre ; **aucun schéma touché**)* |
| la répétition | `…_REPETITION.sql` *(8 épreuves, tout défait, tout annulé)* |
| **l'étape de nuit** | `Console/reposer_cloture_mandat.js` + `run_full_pipeline.ps1` **l. 1515-1539** *(après le push de la l. 1282)* |
| **le chemin immédiat** | `phase2/sync/push_single_annonce_to_supabase.py` — appel ciblé après l'upsert du registre, **enveloppé** |

### ⚠⚠ CE QUE L'AUDIT A RATTRAPÉ : **MON GARDE-FOU ALLAIT ÊTRE DÉCORATIF**

J'allais écrire *« un refus sort en 1 → heartbeat en erreur → le moniteur le dit »*.
**C'est faux par défaut, et je l'ai mesuré avant de le promettre** *(la leçon du matin : l'alerte
« Mandat échu » lisait la table et non la vue)* :

| | |
|---|---|
| `monitoring/heartbeat.py` l. 105-120 | écrit en **`PATCH` FILTRÉ** sur `app_worker_registry`. Clé sans ligne → **0 ligne touchée**, **204**, et `200 <= status < 300` **compte un succès** |
| `check_gti_health.check_worker_heartbeat` l. 1276 | **énumère la table**. Une clé sans ligne **n'est jamais regardée** |

➡ **Une clé non enregistrée = un battement qui part dans le vide, en silence.**
D'où l'`insert` dans le patch, calqué sur `phase2.reappliquer_saisies` — même esprit *(« repose,
après le push, les champs saisis dans l'app »)*, donc **medium / optional_pipeline_step**.

### ⚠ ET CE N'EST PAS QUE MOI — **9 DES 40 CLÉS DU RUN N'ONT AUCUNE LIGNE**

`phase1.archived_details` · **`phase2.adresses_photos`** · `phase2.correspondance_annonces` ·
`phase2.correspondance_identite` · `phase2.derives_photos` · `phase2.doublure_mandat` ·
`phase2.doublure_relation` · `phase2.rattrapage_photos` · `phase2.sonde_photos`

⚠ **Le commentaire du run promet le contraire pour les photos depuis le 27/09.** C'est un sujet
du **chantier ④ (échecs silencieux)**, pas celui-ci : **signalé à Frédéric, non corrigé.**
La répétition **recompte les 9** pour que le chiffre soit daté.

### LES 8 ÉPREUVES
① plancher impossible → **refus** · ② appel normal → **0 posée, 0 effacée** *(idempotent)* ·
③ ⭐ **on simule la nuit** *(colonne vidée)* → **2 posées, les dates reviennent** · ④ une clôture
annulée au carnet → **1 effacée, et seulement celle-là** · ⑤ on remet la ligne → **1 posée** ·
⑥ **portée sur une annonce** → 1 posée, l'autre reste vide · ⑦ sans portée → l'autre revient ·
⑧ **le battement de cœur** 0 → 1 → 0.
⭐ **Le témoin inverse est FIGÉ dans une table temporaire AVANT toute épreuve** — ma leçon du
jour, après le `117 / 117 / 118`.

**Contrôles statiques** : balises paires · 1 `BEGIN`/1 `COMMIT` · 0 CRLF ·
**31 emplacements pour 31 arguments** · Python `py_compile` **OK** · `node --check` **OK** ·
`run_full_pipeline.ps1` **0 erreur de syntaxe** *(parseur PowerShell)*.

## 3c — PIÈCE 4, ÉTAPE 5 : LA RÉPÉTITION, PUIS LE CONTRÔLE EN BASE (13/10)

**Les 8 épreuves, toutes tenues :**

| | mesure |
|---|---|
| ① le garde-fou | `statut: refus` sur un plancher de 1 000 000 — **rien écrit** |
| ② appel normal | **0 posée, 0 effacée** — il est **idempotent** |
| ③ ⭐ **on simule la nuit** | **2 posées**, et les deux dates **reviennent** *(28/08 et 18/09)* |
| ④ une clôture annulée | **1 effacée** — 62966 se vide, **24933 reste intacte** |
| ⑤ on remet la ligne | **1 posée**, la valeur revient |
| ⑥ la portée | `portee: "24933"`, **1 posée**, 62966 **reste vide** |
| ⑦ sans portée | l'autre revient |
| ⑧ le battement de cœur | **0 → 1 → 0** |
| **le témoin inverse** *(figé avant)* | **118 / 118** et **la même empreinte `7356099ce0b968c7170d80ced4d10fa5`** |
| le retour arrière | fonction **0**, état de départ rendu |

*(Le 118 compte les dates **de Hektor** dans la table ; l'écran en montre **119** = 118 + 62966,
qui n'a que la nôtre. L'arithmétique boucle.)*
⚠ Confirmé par la mesure : **9 clés du run sur 9 n'ont aucune ligne de registre.**

### CONTRÔLE EN BASE APRÈS APPLICATION

| | |
|---|---|
| la fonction | ✅ posée |
| **la clé `phase2.repose_cloture_mandat`** | ✅ `medium / optional_pipeline_step / active` — **le moniteur la regardera** |
| nos dates | ✅ **2** · l'écran affiche **119** |

### ⚠ UN ÉCART ENTRE MON COMMENTAIRE ET LA BASE, CORRIGÉ LE MÊME SOIR

Mon patch annonçait *« droits : `service_role` seulement »*. La base répondait
**`authenticated=X`** en plus. Ce n'était pas une faute du patch : c'est un **droit par défaut**
que Supabase pose sur toute nouvelle fonction, et qu'un `revoke ... from public` **n'enlève pas**
*(ce n'est pas PUBLIC, c'est un grant direct)*.
⚠ **Risque réel faible** — la fonction ne fait que rendre le registre **conforme au carnet** —
et ⭐ **`anon` ne l'avait pas** *(le point du chantier ①)*. Corrigé quand même : un commentaire
qui dit une chose et une base qui en dit une autre, c'est la dérive qui mord dans six mois.

`supabase/patch_chantier3_3c_piece4_droits_2026-10-13.sql` — un `revoke`, puis **trois
contrôles** qui refusent si `authenticated` reste, si **`service_role` a perdu son droit**
*(le run ne pourrait plus reposer)*, ou si `anon` en a un. **Appliqué et vérifié** :

| fonction | droits |
|---|---|
| `app_reposer_cloture_mandat_app` | `postgres` + **`service_role` seulement** ✅ |
| `app_set_mandat_cloture_optimistic` | `postgres` + `authenticated` + `service_role` ✅ *(voulu : l'écran l'appelle)* |

### ⏰ CE QUI RESTE À PROUVER : **LA VRAIE NUIT**
La répétition a prouvé le mécanisme **en simulant** la nuit. L'épreuve qui compte est le run de
**05:00 le 14/10** : si les **2 dates sont encore là au réveil**, la pièce 4 est prouvée par le
vrai chemin. ⚠ **À vérifier en premier demain**, avec le heartbeat
`phase2.repose_cloture_mandat` et la ligne `phase2 re-pose cloture mandat` du journal du run.

---

## 3c — PIÈCE 3, ÉTAPE 1-2 : LE CHAMP À L'ÉCRAN *(présentée le 13/10, EN ATTENTE DU « VAS-Y »)*

### CE QUE L'AUDIT TROUVE, POINT D'ENTRÉE PAR POINT D'ENTRÉE

| point d'entrée | ce qui existe | ce qui marche |
|---|---|---|
| **① le registre des mandats** *(la liste et sa fiche)* | lit `mandat_date_cloture` de la vue, et en **dérive le statut Actif / Clos / Échu** *(`mandatStatutForRegisterRow`, api.ts l. 85)* | ✅ **déjà juste depuis cet après-midi** : la vue lui sert **notre** date d'abord. Rien à changer pour l'affichage |
| **② la rubrique « Mandat source » de l'annonce** *(App.tsx l. 18267)* | une ligne `['Cloture', detail.mandat_date_cloture]` | ⛔ **elle n'a JAMAIS pu s'afficher** — voir ci-dessous |
| **③ la modale de changement de statut** *(App.tsx l. 19796-19828)* | 3 cartes d'état + une raison + un texte libre | ⛔ **aucun champ de date**. ⚠ Et elle affiche **« Motif transmis à Hektor »** — ce qui est **faux depuis le 28/08** |

### ⛔ SURPRISE 1 — LA LIGNE « CLÔTURE » DE L'ANNONCE N'A JAMAIS FONCTIONNÉ

`props.detail` vient de `loadDossierDetail` *(api.ts l. 4863-4877)* : c'est **la fiche**
*(`select('*')`)* plus le `detail_payload_json`. Or, mesuré :

| table | colonnes `mandat%` |
|---|---|
| `app_dossier_current` *(la fiche)* | **5** — mais **pas** `mandat_date_cloture` |
| `app_dossier_detail_current` | **0** |
| `app_mandat_register_current` | **10**, dont les deux clôtures |

➡ `detail.mandat_date_cloture` est **toujours `undefined`**, donc `.filter((entry) => entry[1])`
**retire la ligne** : **« Clôture » n'a jamais paru dans la rubrique Mandat de l'annonce.**
➡ Et `pClotureMandat` *(App.tsx l. 26824)*, qui sert à décider `pClos` dans **le parcours du
cockpit** *(Avis → Mandat → Offre → Compromis → Vente)*, est **toujours vide** : le parcours
retombe depuis toujours sur l'expression régulière `/clos|clotur/` du **statut de l'annonce**.

### ⛔ SURPRISE 2 — LA MODALE PROMET CE QU'ELLE NE FAIT PLUS

> **« Motif transmis à Hektor · mandat <n°> »**

C'est **faux depuis le 28/08** *(la clôture chez Hektor est débranchée — elle échouait sur
98,8 % du parc)*. Depuis cet après-midi le motif est **gardé chez nous** *(`clos_motif`)*.
**Le texte doit dire la vérité.**

### CE QUE JE PROPOSE

**① La saisie, au même endroit que le motif** — dans la modale, branche « Clos » : un champ
**date**, pré-rempli à aujourd'hui, à côté de l'état et de la raison. À la validation, en plus
du travail Hektor, un appel à **`app_set_mandat_cloture_optimistic`** *(déjà posé, déjà éprouvé,
`authenticated` a le droit)*.
⚠ **Et un échec de la saisie ne doit pas faire échouer le changement de statut** — même règle
que la répartition juste à côté *(l. 16682 : « un échec ici ne fait pas échouer le geste »)*.

**② La fiche du mandat** *(la rubrique de l'annonce)* : la ligne « Clôture » **réparée** — on lit
la date **dans le registre** pour ce couple (annonce, n° de mandat), au lieu d'une colonne qui
n'existe pas sur la fiche. Avec un **crayon** qui appelle le même RPC.

**③ Le texte de la modale**, corrigé : le motif et la date sont **gardés chez nous**, Hektor ne
reçoit que le statut.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

| | |
|---|---|
| **le parcours du cockpit** | ⚠ `pClos` se mettrait à voir une vraie date. **Conséquence : un bien dont le mandat est clos mais dont le statut ne dit pas « clos » basculerait de jalon.** Mesuré : **2 biens** aujourd'hui *(62966 « Clos » — déjà d'accord — et 24933 « Clos »)*. **Aucun bien en contradiction.** Mais c'est le genre d'effet qui se voit, donc **c'est une question pour Frédéric** |
| le registre des mandats | ⛔ **rien à changer** : il affiche déjà la bonne date |
| les filtres et le tri du registre | ⛔ inchangés |
| la modale pour les autres statuts *(Actif, Offre, Compromis, Vendu)* | ⛔ **pas touchée** : le champ ne vit que dans la branche « Clos » |
| ce qui part chez Hektor | ⛔ **inchangé** : le statut, comme aujourd'hui |
| **le déploiement** | ⚠ **le front se déploie seul sur Vercel au push.** Je code et je commite **en local** ; **c'est toi qui pousses** |
| le build | à vérifier avec `tsc -b` *(règle du projet)* avant de commiter |

### RETOUR ARRIÈRE
`git revert` du commit. Rien en base, rien chez Hektor, aucun worker.

### LA QUESTION POUR FRÉDÉRIC
**Le parcours du cockpit doit-il se fier à ta date de clôture** *(aujourd'hui il ne regarde que
le statut de l'annonce)* — ou **on ne touche qu'à l'affichage et à la saisie** ?

### 3c PIÈCE 3 — AUDIT ÉLARGI À LA DEMANDE DE FRÉDÉRIC (13/10)

> *« Dans le front cockpit prendre la date de début et la date de fin "restant ou échu ou clos",
> je crois c'est là qu'il faudrait interagir. Et dans la rubrique mandat au niveau du cycle du
> mandat, et audit s'il n'y a pas d'autre endroit. »*

⭐ **Il a visé juste : la logique existe déjà, et elle est BONNE. Elle lit la mauvaise source.**

### LES 5 ENDROITS DU FRONT QUI DISENT « RESTANT / ÉCHU / CLOS »

| | où | ce qu'il fait | source |
|---|---|---|---|
| **①** | `ckCycles` *(l. 26867-26880)* | ⭐ **la FRONTIÈRE entre deux cycles** = `m.cloture \|\| m.fin` — *« toute activité APRÈS la clôture bascule sur le cycle suivant »* | `detail.mandats_json` *(**Hektor**)* |
| **②** | `ckCycleBadge` *(l. 26911-26914)* | **Vendu → Clos → Échu → Actif** — ⭐ **la bonne règle, déjà écrite** | idem *(**Hektor**)* |
| **③** | `mandatEchu` + `computeMandatTiming` *(l. 26859, 25224)* | « Jours restants », la barre de temps, le rouge si échu | **n'a AUCUNE notion de clôture** |
| **④** | l'historique de la rubrique Mandat V3 *(l. 27597, 27630)* | la pastille **« Clôturé »** par version | `detail.mandats_json` *(**Hektor**)* |
| **⑤** | la rubrique « Mandat source » *(l. 18221-18273)*, dans **un autre composant** *(`DetailAdminPilotPanel`)* | la ligne **« Clôture »** | `detail.mandat_date_cloture` → ⛔ **colonne qui n'existe pas sur la fiche** |

Plus, **déjà justes** : le **registre des mandats** *(`mandatStatutForRegister`, l. 7667 — il lit
la vue, donc **notre** date depuis cet après-midi)* et son filtre « Échu » *(l. 22094)*.

### ⭐⭐ ET LE COCKPIT A DÉJÀ NOTRE DATE SOUS LA MAIN

`loadRegisterCycleAffaires` *(api.ts l. 6156)* lit **`app_registre_mandats_current`** et
sélectionne **`mandat_date_cloture`** — qui porte **notre date d'abord** depuis les pièces 1-2.
Elle arrive dans **`ckCycleAff`**, une table **par numéro de mandat**, chargée pour l'annonce
affichée *(l. 26724, 26780)*.

➡ **Elle est là, chargée, par cycle. Elle n'est simplement pas utilisée.**
➡ Et `ckCycleAff` vit dans **`CockpitDetail`**, qui contient **①②③④** : **une seule
superposition** y suffit. Seul **⑤** est dans un autre composant.

### CE QUE JE PROPOSE — **un fichier, cinq points, zéro base, zéro run, zéro worker**

**A. Une seule superposition dans `CockpitDetail`** : un `useMemo` qui reprend la liste des
mandats et remplace `cloture` par **`notre clôture (ckCycleAff) sinon celle de Hektor`**.
➡ **①②④ deviennent justes sans être modifiés** — la frontière des cycles, la pastille, et
l'historique.

**B. `mandatClos`, à côté de `mandatEchu`** : un mandat **clos** n'est ni « échu » ni
« 120 jours restants ». Priorité à l'affichage : **Vendu → Clos → Échu → restant**.
*(C'est déjà l'ordre que le badge du cycle applique — on l'aligne partout.)*

**C. La ligne « Clôture » de la rubrique Mandat source** : on lit le registre *(le même appel,
déjà écrit)* au lieu d'une colonne absente.

**D. La saisie** : un champ **date** dans la modale, branche « Clos », à côté de l'état et de la
raison, pré-rempli à aujourd'hui + un **crayon** dans la rubrique Mandat → les deux appellent
**`app_set_mandat_cloture_optimistic`**. ⚠ Un échec de la saisie **ne fait pas échouer** le
changement de statut *(même règle que la répartition, l. 16682)*.

**E. Le texte faux** : « Motif transmis à Hektor » → la vérité *(le motif et la date restent
chez nous ; Hektor ne reçoit que le statut)*.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

| | |
|---|---|
| ⚠⚠ **la frontière des cycles (①)** | **c'est le point le plus structurant** : déplacer la frontière **reclasse les activités** d'un cycle à l'autre *(offres, compromis, documents, fil d'activité)*. Aujourd'hui **2 mandats** portent une date de nous ; les deux sont **déjà « Clos »** et **Hektor en porte une pour un des deux** *(24933 : la sienne au 05/10, la nôtre au 18/09)* → **la frontière de ce cycle avancerait de 17 jours**, et une activité datée entre les deux changerait de cycle |
| **③ les « jours restants »** | ⚠ **ils changent d'affichage** sur un mandat clos : au lieu d'un compte à rebours, « Clos ». **C'est le but** |
| le registre des mandats, ses filtres, son tri | ⛔ **rien à changer** — déjà justes |
| la modale pour Actif / Offre / Compromis / Vendu | ⛔ **pas touchée** : le champ ne vit que dans la branche « Clos » |
| ce qui part chez Hektor | ⛔ **inchangé** |
| la base, le run, les workers | ⛔ **rien** |
| **le déploiement** | ⚠ **Vercel se déploie seul au push.** Je code et je commite **en local** ; **c'est Frédéric qui pousse** |
| le build | `tsc -b` **avant** de commiter *(règle du projet)* |

### RETOUR ARRIÈRE
`git revert` du commit. Rien en base, rien chez Hektor, aucun worker, aucun schéma.

### LA SEULE QUESTION QUI RESTE
**La frontière des cycles (①) doit-elle bouger**, c'est-à-dire : une activité datée **après ta
date de clôture** doit-elle basculer sur **le cycle suivant** ? *(C'est la règle déjà écrite,
mais avec la date de Hektor.)* Si tu préfères, je fais **②③④⑤ + la saisie** et **je laisse la
frontière sur la date de Hektor** pour l'instant — c'est séparable.

## 3c — PIÈCE 3, ÉTAPE 4-5 : CODÉE ET BÂTIE (13/10) — **un seul fichier de front**

> **Décision de Frédéric** : *« Oui elle doit basculer sur le cycle suivant s'il existe »*
> ⭐ **Et son « s'il existe » était DÉJÀ la règle du code** : le dernier cycle est laissé ouvert
> à +∞, donc une activité après la dernière clôture reste sur son cycle.

### LA MESURE QUI DIT CE QUE ÇA DÉPLACE AUJOURD'HUI

| | |
|---|---|
| annonces au registre | **24 466** |
| à **plusieurs** cycles | **39** *(2 au maximum)* |
| parmi elles, **avec une clôture de nous** | **0** |
| ➡ activités reclassées aujourd'hui | **0** |

**62966** et **24933** n'ont **qu'un seul cycle** → il est le dernier → ouvert → **leur frontière
ne bouge pas**. Le changement est **inerte sur le parc actuel** ; il jouera le jour où on clôra
un mandat sur une annonce à deux cycles.

### ⭐ UNE SEULE SOURCE, DÉJÀ CHARGÉE, ET SIX CONSOMMATEURS

`ckClotureDe(numero)` lit **`ckCycleAff`** — la table par n° de mandat que
`loadRegisterCycleAffaires` remplit déjà pour l'annonce affichée, et qui porte
`mandat_date_cloture` = **notre date d'abord** depuis les pièces 1-2. **Aucun chargement
ajouté.**

| | ce qui est corrigé | comment |
|---|---|---|
| **①** la **frontière** des cycles | `endStr = m.cloture \|\| m.fin` | ⭐ **le `cloture` de la liste est superposé** → ① et ② corrigés **sans toucher à leur code** |
| **②** la **pastille** du cycle *(Vendu → Clos → Échu → Actif)* | `ckCycleBadge` | idem |
| **③** le **parcours** du cockpit | `pClotureMandat` lisait **la fiche**, qui n'a pas la colonne → **toujours vide depuis toujours** | branché sur la même source → `pClos` fonctionne enfin, et `ckStage` tombe sur **`'clos'`** *(il était déjà 2ᵉ dans la chaîne, avant `mandatEchu`)* |
| **④** l'**historique** de la rubrique Mandat V3 | `h.cloture` | superposé → la pastille **« Clôturé »** et le badge des lignes d'historique suivent |
| **⑤** **« Jours restants »** × **2** | ⚠ `mandatEchu` ne connaissait **aucune** clôture | **`mandatClos`** posé **une fois** *(`mandatEchu` l'exclut désormais)* → **Clos** avant **Échu** avant **restant**, partout |
| **⑥** la **jauge** « Mandat · restant » | idem | « **Mandat clos** », barre éteinte, infobulle qui donne la date de clôture **et** l'échéance initiale |

⚠ **Le 6ᵉ a été trouvé en recomptant APRÈS avoir cru avoir fini** *(un second `md-fig`
« Jours restants », dans un autre bloc du même composant)*. **Cinq, c'était faux.**

### LA SAISIE
Un champ **date** dans la modale, branche « Clos », à côté de l'état et de la raison,
**pré-rempli à aujourd'hui**. À la validation : `setMandatClotureApp` →
**`app_set_mandat_cloture_optimistic`**.
⚠ **Un échec n'empêche pas le changement de statut** — même règle que la répartition juste en
dessous : *« la transaction est partie chez Hektor, une répartition manquante se ressaisit »*.
⚠ **Seulement pour « Clos »**, et seulement avec un n° de mandat *(la RPC refuse un couple
inconnu — on ne la dérange pas pour rien)*.
**Vider le champ efface notre date** et fait réapparaître celle de Hektor.

### LE TEXTE QUI DISAIT FAUX
> ~~« Motif transmis à Hektor »~~ → **« Mandat <n°> · motif et date gardés chez nous »**

Faux depuis le **28/08**, quand la clôture chez Hektor a été débranchée *(elle échouait sur
98,8 % du parc)*.

### ⬜ CE QUI N'EST PAS FAIT, ET POURQUOI — À DIRE À FRÉDÉRIC

1. **Le crayon dans la rubrique Mandat** *(saisie hors modale)*. **Non fait.** Le champ de la
   modale s'insère dans un formulaire existant et éprouvé ; un bloc d'édition neuf dans une
   rubrique demande une **vérification à l'œil** que je ne peux pas faire ce soir *(il faudrait
   une session connectée — je ne me connecte pas à sa place)*. **À faire ensuite, avec captures.**
2. **La rubrique « Mandat source »** *(`['Cloture', current.cloture]`)* : **laissée sur la
   version de Hektor, volontairement** — elle s'appelle « Mandat **source** », elle montre ce
   que Hektor dit. **Décision à confirmer.** *(Sa branche de repli lit une colonne qui n'existe
   pas : ligne morte, inoffensive, laissée.)*
3. **La vérification visuelle.** `tsc -b` est **vert**, la logique est mesurée — mais **personne
   n'a encore vu l'écran**. ⚠ **Vercel se déploie seul au push : c'est Frédéric qui pousse.**

### CE QUI N'EST PAS TOUCHÉ
Le **registre des mandats** *(déjà juste)*, ses filtres et son tri · la modale pour **Actif /
Offre / Compromis / Vendu** · ce qui part **chez Hektor** · la **base** · le **run** · les
**workers**. **Un seul fichier de code front** *(`App.tsx`)* **plus la fonction d'appel**
*(`api.ts`)*.

---

## 3c — PIÈCE 5, ÉTAPE 1-2 : LE WORKER *(présentée le 13/10, EN ATTENTE DU « VAS-Y »)*

### ⭐ LE WORKER CLÔT DÉJÀ, PAR **DEUX** CHEMINS VIVANTS

| | |
|---|---|
| `submitHektorClosedStatus` *(l. 13256)* | quand le statut passe à **« Clos »** |
| le chemin **« Vendu »** *(l. 14670)* | ⭐ **toute vente clôt le mandat chez nous**, avec la **date de la vente** — inconditionnel |

### ⭐⭐ ET LE JOURNAL CLÔT L'HISTOIRE DES CLÔTURES

**24 lignes** `cloture_mandat_locale` depuis le 28/08 : **19 « done », 5 « error »**. Et elles ne
concernent que **TROIS annonces** :

| annonce | passages | ce que c'est |
|---|---|---|
| **24933** | **11** *(03/09 → 18/09)* | le bien d'essai des tâches 3.2 / 3.4 |
| **62774** | **7** *(29/08 → 31/08)* | le bac à sable |
| **62966** | **2** *(28/08)* | l'annonce d'essai de la clôture |
| **62963** | 1 *(12/10, erreur)* | mon propre essai de 3a, hier |

➡ **Troisième preuve indépendante : aucune clôture réelle, jamais.** Le journal, le carnet et
les notes disent la même chose.

### LES 5 ERREURS, LUES

| | |
|---|---|
| **4 ×** *« Clôture locale impossible : aucun numéro de mandat dans la demande »* | ⛔ **ce n'est PAS un bug** : c'est le garde-fou qui **refuse de deviner** le mandat cible. ⚠ Mais il journalise en **`error`**, donc **une annonce sans n° de mandat qui passe en « Clos » fait du bruit** *(c'est arrivé hier sur 62963)* |
| **1 ×** *« STATUT CHANGE, MAIS CLOTURE LOCALE NON ECRITE -- à reprendre »* + `Supabase 400 … Empty or invalid json` | 📜 **le bug du 28/08 au matin**, déjà corrigé *(« le corps doit être du TEXTE — un objet donne Empty or invalid json »)*. Historique |

### ⭐ UNE MESURE QUI CHANGE LE CORRECTIF : `registre_lignes_rafraichies: 0`

Elle apparaît **4 fois** *(62966 le 28/08, 62774 le 30 et le 31/08, 24933 le 17/09 ×2)* : le
`PATCH` du registre **n'a touché AUCUNE ligne**. Le worker le dit lui-même — *« il peut ne
correspondre à aucune ligne, et c'est sans conséquence, la valeur qui fait foi est déjà
écrite »*.

➡ ⛔ **DONC REMPLACER LES DEUX ÉCRITURES DU WORKER PAR UN APPEL AU RPC SERAIT UNE RÉGRESSION** :
le RPC **refuse** un couple absent du registre *(`mandat_introuvable`)*, et ces **4 clôtures
auraient été perdues** au lieu d'être gardées au carnet.
C'était ma première idée. **La mesure l'a écartée.**

### CE QUE JE PROPOSE — **option A, une seule ligne**

Dans `cloturerMandatLocalement`, le `PATCH` du registre change de **colonne** :
```js
body: JSON.stringify({ mandat_date_cloture: date })        // ❌ celle de HEKTOR
body: JSON.stringify({ mandat_date_cloture_app: date })    // ✅ la NÔTRE
```
Et son commentaire, qui dit *« confort d'affichage, SANS AUTORITÉ »*, devient vrai : il écrit
désormais **dans notre colonne**, et la **pièce 4** la repose de toute façon depuis le carnet.

⭐ **L'écriture du carnet ne change pas d'un octet** — c'est elle qui fait foi, et c'est elle qui
garde les cas où le registre n'a pas la ligne.

| | option A *(recommandée)* | option B *(appeler le RPC)* |
|---|---|---|
| taille | **une ligne** | le worker **et** le RPC |
| les 4 cas sans ligne de registre | ✅ **gardés** | ⛔ **perdus** |
| un seul chemin d'écriture | non | oui |
| risque | **minimal** | il faudrait **assouplir un RPC déjà éprouvé** |

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

| | |
|---|---|
| **le carnet** | ⛔ **pas touché** — l'écriture qui fait foi est inchangée |
| **la colonne de Hektor** | ✅ le worker **cesse de l'écrire** — c'est exactement la demande de Frédéric *(« maj éventuellement par Hektor mais surtout pas l'app »)*, et ça **ferme la boucle** qui nous faisait relire notre propre écriture |
| **le magasin de nuit** | ⭐ **il arrêtera de fabriquer de fausses « valeur_app »** : il lit le registre comme « ce que dit l'app » ; comme le worker n'y écrira plus, les lignes `observe` redeviendront **vraies** |
| l'affichage | ⛔ **inchangé** : la vue sert déjà `_app` d'abord |
| le chemin « Vendu » | ⛔ **inchangé** dans sa logique — il clôt toujours le mandat à la vente, mais **dans notre colonne** |
| ⚠ **les 4 services** | **À REDÉMARRER.** Sans ça, le worker en mémoire continue d'écrire l'ancienne colonne. ⚠ Et **mesure du 08/10** : les processus avaient été lancés **1 h 24 après** la modification du fichier — un redémarrage qu'on croit fait et qui ne l'est pas, ça s'est déjà vu |
| le run, la base, le front | ⛔ **rien** |

### RETOUR ARRIÈRE
`git revert` *(une ligne)* **+ un nouveau redémarrage des 4 services**. Aucune base, aucun schéma.

### CONTRÔLE PRÉVU
1. `grep` de la ligne avant / après *(le témoin : la nouvelle apparaît **et** l'ancienne disparaît)*.
2. ⛔ **Je ne lance JAMAIS le worker pour l'inspecter** *(ça démarre un 5ᵉ)* — contrôle par lecture, puis par les **processus** et l'**heure de modification du fichier**.
3. **L'essai réel** : un passage en « Clos » sur un bien d'essai avec n° de mandat, puis vérifier
   que **`mandat_date_cloture_app`** bouge et que **`mandat_date_cloture` ne bouge pas**.
   ⚠ **Accord de Frédéric nécessaire** *(ça écrit chez Hektor)*.

### LA QUESTION POUR FRÉDÉRIC
Les **4 journaux en `error`** pour *« aucun numéro de mandat »* : c'est un **refus voulu**, pas une
panne — mais il crie. **On le passe en avertissement** *(le geste a réussi, seule la clôture est
sautée)*, ou **on le laisse en erreur** pour que ça se voie ?

## 3c — PIÈCE 5, ÉTAPE 4-5 : CODÉE (13/10) — ⚠ **INERTE JUSQU'AU REDÉMARRAGE**

**Décision de Frédéric** : *« 1. Vas y. 2 nettoie. »*

| geste | fait |
|---|---|
| le `PATCH` du registre écrit **`mandat_date_cloture_app`** *(la nôtre)* au lieu de `mandat_date_cloture` *(celle de Hektor)* | ✅ une ligne |
| le refus *« aucun numéro de mandat »* passe de **`error`** à **`done`**, avec la vérité dans le message et `saute: true` dans la charge | ✅ |

**Témoin dans les deux sens** *(ma règle)* :
`mandat_date_cloture_app: date` **apparaît** *(l. 13229)* · `mandat_date_cloture: date`
**ne figure plus nulle part** · `node --check` **OK**.

⭐ **Et la vraie erreur, elle, reste une erreur** : *« STATUT CHANGÉ, MAIS CLÔTURE LOCALE NON
ÉCRITE — à reprendre »* *(l. 13252)*. Le nettoyage ne touche **que les 4 fausses alertes**, pas
la seule vraie panne du journal.

**Pourquoi `done` et pas un statut neuf** : la colonne n'a **aucune contrainte**, mais seuls
`running / done / error` existent *(mesuré : 201 370 / 109 551 / 147)*, et inventer une 4ᵉ valeur
risquerait de surprendre un lecteur. **Le seul lecteur programmatique du journal filtre une
AUTRE étape** *(`hektor_qualification_acquereur`)* — vérifié avant de choisir.

**Pourquoi PAS le RPC** *(ma première idée, écartée par la mesure)* : il **refuse** un couple
absent du registre, et le journal montre **4 clôtures** où `registre_lignes_rafraichies` valait
**0** — c'est le **carnet** qui les avait sauvées. Le RPC les aurait **perdues**.

### ⛔ CE QUI MANQUE POUR QUE ÇA SERVE : **LE REDÉMARRAGE DES 4 SERVICES**
Le worker en mémoire continue d'écrire l'ancienne colonne. ⚠ **Mesure du 08/10** : les processus
avaient été lancés **1 h 24 après** la modification du fichier — *un redémarrage qu'on croit
fait et qui ne l'est pas, c'est déjà arrivé ici*. **À contrôler par l'heure des processus, pas
par la croyance.**
⚠ **Accord de Frédéric NON DONNÉ sur le redémarrage** : il a dit « vas-y » pour le code. **Je ne
redémarre rien.**

### ✅ REDÉMARRAGE CONFIRMÉ PAR LA MESURE (13/10, 16:55)

| | |
|---|---|
| `Console/console_job_worker.js` modifié | **16:52:28** |
| les **4** processus `node` démarrés | **16:55:05 · 16:55:06 · 16:55:07 · 16:55:07** |
| écart | **2 min 37** — le redémarrage porte bien la nouvelle ligne |
| nombre de processus | **4**, pas 5 → **aucun worker orphelin** |

⚠ **Première mesure non concluante, et je ne l'ai pas prise pour un échec** :
`Get-Process | Select StartTime` rend la colonne **vide** *(droits)*, ce qui faisait
« démarré après la modif = False » pour les quatre. **Refait avec
`Get-CimInstance Win32_Process`**, qui donne `CreationDate` sans élévation.
➡ **Une colonne vide n'est pas un « non ».** *(Le 08/10, le même contrôle avait révélé
**1 h 24** d'écart : c'est pour ça qu'on le refait à chaque fois.)*

### ⏳ CE QUI RESTE POUR PROUVER LA PIÈCE 5 : UN ESSAI RÉEL
Il faut un passage en **« Clos »** sur un bien d'essai **qui porte un n° de mandat**, puis
vérifier que **`mandat_date_cloture_app`** bouge et que **`mandat_date_cloture` ne bouge pas**.
⚠ **Ça écrit chez Hektor → accord de Frédéric.**
| bien | utilisable ? |
|---|---|
| **62963** *(le bien d'essai courant)* | ⛔ **non** — c'est précisément lui qui a journalisé *« aucun numéro de mandat »* le 12/10 |
| **62774** *(bac à sable, « Sous offre », mandat 18836)* | ✅ utilisable — réversible par « Actif » |
| **62966** *(annonce d'essai, mandat 18842)* | déjà « Clos » |
⭐ **Et la preuve viendra de toute façon seule** : le chemin « Vendu » clôt le mandat **à chaque
vente**. La prochaine vente réelle avec un n° de mandat écrira dans notre colonne.

---

## 3e — SUPPRIMER UN DOCUMENT : AUDIT (13/10) · **ÉTAPE 2, EN ATTENTE DU « VAS-Y »**

*Ordre choisi par Frédéric : **3e avant 3d**, « par gravité ».*

### LA SÉQUENCE, LUE LIGNE PAR LIGNE *(`handleDeleteDocumentFromHektor`, l. 8257-8320)*

| | |
|---|---|
| 1-3 | charge le dossier et le document, **vérifie qu'il appartient bien à l'annonce** ✅ |
| 4 | exige l'**ID Hektor supprimable** — ⚠ **sinon le geste ÉCHOUE** |
| 5 | vérifie que le document existe **chez Hektor** |
| **6** | **`UploadedDocument_delete` → SUPPRIME CHEZ HEKTOR** |
| 7 | relit et **confirme** la suppression chez Hektor ✅ |
| **8** | ⛔ `deleteStorageObject(storage_path)` → **détruit NOTRE fichier cloud** |
| **9** | ⛔ `fs.unlinkSync(local_archive_path)` → **détruit NOTRE fichier serveur** |
| **10** | ⛔ `DELETE app_console_document` → **détruit NOTRE ligne** |

➡ **« Hektor d'abord » au sens le plus littéral : on supprime chez lui, puis on détruit nos
TROIS copies. Et il ne reste RIEN.**

### CE QUE ÇA DÉTRUIT, MESURÉ

| | |
|---|---|
| documents chez nous | **162 543** · **~229 Go** |
| avec un **fichier serveur** | **162 328** |
| avec un **fichier cloud** | **21 839** |
| ⛔ une **corbeille** / table des supprimés | **0** — mesuré sur tout le schéma |
| l'empreinte `app_console_document_fingerprint` | ⛔ **une par ANNONCE**, pas par document → **aucune trace** qu'un document a existé |

### ⚠⚠ ET L'ÉCRAN DIT AUTRE CHOSE QUE CE QU'IL FAIT

> `window.confirm(`**Supprimer ce document dans Hektor ?**`)` — *App.tsx l. 11104*

**L'utilisateur croit supprimer chez Hektor.** Rien ne lui dit que **nos trois copies partent
avec**. C'est le même défaut que le « Motif transmis à Hektor » trouvé ce matin — **mais ici
c'est irréversible.**

### CE QUI A DÉJÀ ÉTÉ DÉTRUIT
**34 suppressions réussies**, du **14/05** au **22/07**, sur **11 annonces réelles** — dont
**19 sur la seule 24113** *(22/05 → 29/06)*. **Ce ne sont pas des biens d'essai.**

### ⭐ LE FEU VERT TECHNIQUE : LA NUIT NE DÉTRUIRA PAS À NOTRE PLACE
`upsertConsoleDocuments` *(l. 4634-4644)* ne supprime que les **DOUBLONS** : sa condition exige
`selectedEntries.some(entry => entry.hektor_document_id === row.hektor_document_id)` — donc
**le document doit être ENCORE chez Hektor**, sous une autre clé. Et un `preservedIds` protège
en plus certaines lignes.
➡ **Un document absent de chez Hektor n'est PAS supprimé par la synchro.** Si on cesse de
détruire dans le geste, **la ligne survit toute seule.**

### ⭐ ET LE BON PRINCIPE N'EST PAS « CHEZ NOUS D'ABORD »
Pour une **écriture**, « chez nous d'abord » veut dire *écrire chez nous avant Hektor*. Pour une
**suppression**, ça voudrait dire *détruire chez nous avant* — **l'inverse de ce qu'on veut.**
⭐ **Le principe du projet pour une suppression est : CHEZ NOUS, ON NE DÉTRUIT PAS, ON MARQUE.**
Il a deux précédents : *« la ligne de la photo ne disparaît jamais »* et le `retire_le` des
relations.

### CE QUE JE PROPOSE
**① On cesse de détruire.** Les trois destructions deviennent **une marque** : le document est
**retiré de chez Hektor**, et chez nous il reste — fichier serveur, fichier cloud, et ligne —
avec **qui** l'a retiré et **quand**.
**② L'écran dit la vérité** : « Supprimer ce document **dans Hektor** ? **Notre copie est
conservée.** »
**③ Le travail reste confirmé par Hektor** *(l'étape 7 ne change pas)* : on ne marque que si
Hektor a bien supprimé.

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS
| | |
|---|---|
| **la liste des documents à l'écran** | ⚠⚠ **LA question** : un document retiré chez Hektor mais gardé chez nous — **l'utilisateur le voit encore ?** S'il le voit, il re-cliquera « supprimer » et **ça échouera** *(plus d'ID Hektor)*. S'il ne le voit pas, il est « conservé » mais **invisible**. ➡ **décision de Frédéric** |
| **l'espace** | ⚠ conserver sans jamais détruire = **229 Go qui ne décroissent plus**. Il existe une colonne `archive_policy` et une purge cloud des archives → **décision de Frédéric** |
| la synchro de nuit | ⛔ **ne détruira pas** *(mesuré ci-dessus)* |
| le compte des documents | ⚠ il **n'baissera plus** après une suppression. À dire, sinon ça ressemble à un bug |
| ce qui part chez Hektor | ⛔ **inchangé** : on supprime toujours chez lui, et on le vérifie |
| ⚠ **le worker** | **4 services à redémarrer** |
| la base | selon la forme de la marque — **une colonne** *(patch SQL, filtrable)* ou **`metadata_json`** *(aucun patch)*. **Décision de Frédéric** |

### ⚠ UN DÉFAUT DE BORD, TROUVÉ AU PASSAGE
Le geste **exige** `hektor_uploaded_document_id` : ➡ **un document qui n'est QU'À NOUS ne peut
pas être supprimé du tout.** Inoffensif aujourd'hui, **bloquant après la coupure.** Noté, non
corrigé.

### LES 3 QUESTIONS POUR FRÉDÉRIC
1. **Un document retiré chez Hektor, l'écran le montre encore ?** *(visible avec une mention
   « retiré de Hektor » · caché · ou dans un onglet « retirés »)*
2. **La marque : une colonne** *(propre, filtrable, patch SQL)* **ou `metadata_json`**
   *(immédiat, sans patch)* ?
3. **L'espace** : on garde **tout** pour toujours, ou on prévoit une purge *(ex. le fichier
   cloud après N mois, en gardant la ligne et l'empreinte)* ?

### ⭐ LA RÈGLE DE FRÉDÉRIC (13/10) — ET ELLE CORRIGE LA MIENNE

> *« Si il est supprimé dans Hektor donc supprimé du run, alors on garde dans l'app avec
> mention "supprimé chez Hektor", une purge sera possible. Mais si supprimé par l'app, alors on
> demande la suppression chez Hektor et on supprime dans l'app aussi, on peut garder une
> corbeille si possible. »*

| cas | ce qui se passe | **ce qu'on fait** |
|---|---|---|
| **A** | le document disparaît **dans Hektor** *(constaté par le run)* | **on GARDE chez nous**, avec la mention **« supprimé chez Hektor »** · une **purge sera possible** |
| **B** | le document est supprimé **par l'app** *(geste voulu)* | on supprime **chez Hektor** **et chez nous** · **une corbeille si possible** |

⭐ **C'est plus juste que ma proposition** : j'avais dit « on ne détruit jamais ». Sa règle
distingue **une disparition subie** *(on garde, c'est une perte qu'on ne décide pas)* d'une
**suppression voulue** *(elle doit faire ce qu'elle dit — avec un filet)*.

### LE CAS A, MESURÉ : IL EST MINUSCULE AUJOURD'HUI

| | |
|---|---|
| documents que nous avons et que Hektor n'a plus *(repère : `synced_at` resté en arrière sur une annonce revue depuis)* | **1** à 7 jours · **12** à 1 jour |
| sur combien | **162 543** |
| fiabilité du repère | **bonne** : **23 850** annonces portent des documents, **toutes revues depuis le 18/08** *(6 102 sur 7 jours, 17 282 sur 30)*, **0** non revue depuis 90 j |
| ⚠ limite | le repère ne voit une disparition que si l'annonce est **revue après**. Il **sous-estime**, mais la couverture est large |

➡ **Aujourd'hui, presque personne ne supprime de documents directement dans Hektor.** Le
mécanisme du cas A sert donc surtout **pour après la coupure** — et pour ne plus être aveugle.

### CE QUE CHAQUE CAS DEMANDE

**CAS A — la ligne survit DÉJÀ, mais en silence.**
`upsertConsoleDocuments` ne supprime que les **doublons** *(mesuré)*, donc un document absent de
chez Hektor **reste**. ⛔ Mais **aucune mention**, et **rien ne le détecte**.
⭐ **Le code pour le détecter est déjà là, à une condition près** : la règle des doublons exige
`selectedEntries.some(entry => entry.hektor_document_id === row.hektor_document_id)` —
**retirer cette exigence donne exactement les absents**. Au lieu de les supprimer : **on les
marque**.
⚠⚠ **ET IL FAUT UN GARDE-FOU, SANS QUOI C'EST UNE CATASTROPHE** : cette fonction tourne à
**chaque** synchro d'annonce. Si la liste de Hektor revient **vide ou tronquée** *(réseau, page
partielle)*, on marquerait **tous les documents de l'annonce** comme supprimés. ➡ **on ne marque
JAMAIS depuis une liste vide**, et jamais au-delà d'une proportion plausible.

**CAS B — ça détruit déjà tout, sans filet.** → **la corbeille** : la ligne et les fichiers sont
**conservés**, marqués « corbeille », **retirés de la liste normale**, et **restaurables**.

### LA FORME : UNE COLONNE EST NÉCESSAIRE
Sa règle demande **deux états distincts** *et* **une purge** → `metadata_json` ne suffit pas
*(on ne filtre ni ne purge proprement un JSON)*. Je propose **trois colonnes** sur
`app_console_document` *(et leurs jumelles sur `app_console_photo`, puisqu'il dit « photos et
documents »)* :
`retire_le` *(quand)* · `retire_motif` *(**`absent_hektor`** ou **`corbeille_app`**)* ·
`retire_par` *(qui, pour le cas B)*.

### LES 3 PALIERS QUE JE PROPOSE *(on peut s'arrêter après chacun)*
| | |
|---|---|
| **① la base** | les 3 colonnes sur les documents **et** les photos · la vue/les filtres qui écartent les retirés · **rien ne change à l'écran** |
| **② le worker** | **cas B** : au lieu de détruire, on marque `corbeille_app` *(fichiers conservés)* · **cas A** : on marque `absent_hektor`, **avec le garde-fou de liste vide** · ⚠ **4 services** |
| **③ l'écran** | la mention **« supprimé chez Hektor »** · la **corbeille** avec **Restaurer** · et le texte du `confirm` qui dit la vérité · ⚠ **c'est Frédéric qui pousse** |

### ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS
| | |
|---|---|
| **le compte des documents** | ⚠ il **n'baissera plus** sur une suppression *(ils vont en corbeille)*. À dire, sinon ça ressemble à un bug |
| **l'espace** | ⚠ **229 Go qui ne décroissent plus** tant qu'aucune purge n'existe |
| la liste à l'écran | les retirés **en sortent** → il faut que les filtres l'appliquent partout, sinon un document en corbeille réapparaîtrait |
| ⚠ **le garde-fou de liste vide** | **c'est le risque n° 1 du cas A.** Sans lui, une page Hektor tronquée marquerait tout un dossier comme supprimé |
| ce qui part chez Hektor | ⛔ **inchangé** dans les deux cas |
| la synchro de nuit | ⛔ ne détruit pas *(mesuré)* |

### LES QUESTIONS QUI RESTENT
1. **La corbeille garde-t-elle les fichiers** *(serveur + cloud)*, ou seulement la ligne et
   l'empreinte ? *(Garder les fichiers = restauration vraie ; garder la ligne seule = on sait ce
   qui a existé, sans pouvoir le rendre.)*
2. **La purge** : au bout de combien de temps, et sur quoi — le **cloud** seulement, ou aussi le
   **serveur** ? *(Elle viendra après ; il faut juste savoir si on prévoit la place.)*
3. **On commence par le palier ①** *(la base seule, rien ne change)* **ou les trois d'un coup ?**

---

## 3e — AUDIT REFAIT SUR LES **QUATRE** CASES (13/10) · *« photos ET documents »*

J'avais audité **une case sur quatre**. Il y a **deux objets** et **deux façons de disparaître**.

| | **PHOTOS** *(441 117)* | **DOCUMENTS** *(162 543 · ~229 Go)* |
|---|---|---|
| **① disparu CHEZ HEKTOR** | ✅ **DÉJÀ EXACTEMENT CE QUE FRÉDÉRIC DEMANDE** *(G.10bis)* : la ligne **reste**, marquée `present_in_hektor = false` **+ `absent_depuis`** | ⛔ **la ligne reste, mais SANS AUCUNE MENTION** — on ne sait pas que Hektor ne l'a plus |
| **② supprimé PAR L'APP** | ⛔ **le geste N'EXISTE PAS** — on ne peut pas supprimer une photo depuis l'app | ⛔ **détruit TOUT** : Hektor, notre cloud, notre serveur, **et la ligne**. Aucune corbeille |

### ⭐ LA SOLUTION EST DÉJÀ ÉCRITE, DANS LE PROJET, POUR LES PHOTOS
`upsertConsolePhotos` l. 4485-4506, et son commentaire dit **pourquoi** :
> *« L'id de cette ligne porte deux choses irréversibles : le chemin du fichier sur le serveur
> et, dès G.11, **l'adresse PUBLIQUE de ses dérivés, qu'un portail met en cache et qu'un email
> intègre**. Un id supprimé ne revient jamais. […] **Même patron que
> `app_affaire_ledger.present_in_hektor`.** »*

Et il a un **détail de qualité** : `.filter(row => row.present_in_hektor !== false)` →
**il n'écrase pas une date d'absence déjà posée.**
➡ **C'est un patron du projet, utilisé 3 fois** *(photos, affaires, et bientôt documents)*.

### LES MESURES

| | |
|---|---|
| photos marquées « plus chez Hektor » | **0** sur **441 117** — et **toutes** portent `present_in_hektor = true`, donc **le mécanisme TOURNE**, il n'a simplement **jamais rien eu à marquer** |
| documents que Hektor n'a plus *(repère `synced_at`)* | **1** à 7 jours · **12** à 1 jour, sur 162 543 |
| suppressions de documents **par l'app** | **34 réussies**, 14/05 → 22/07, sur **11 annonces réelles** *(19 sur la seule 24113)* |
| une corbeille | **0** table, sur tout le schéma |
| trace qu'un document a existé | **aucune** — l'empreinte est **par annonce**, pas par document |

### ⚠ DEUX TROUS DE BORD, TROUVÉS EN REFAISANT L'AUDIT
1. ⚠⚠ **LE GARDE-FOU DE LISTE VIDE N'EXISTE NULLE PART** — ni pour les photos, ni pour les
   documents. Le seul filet est qu'une **erreur** soit levée *(un 403 est même rattrapé et
   rejoué)*. Mais une réponse **vide sans erreur** passerait : **toutes** les photos d'une
   annonce seraient marquées absentes d'un coup. **Jamais arrivé en 2 mois** *(0 marquée)*,
   **mais le filet n'est pas là.** Et si on recopie le patron sur les documents **sans ce
   garde-fou, on importe le risque sur 229 Go.**
2. ⚠ **On ne peut pas supprimer** une photo depuis l'app, ni un document **qui n'est qu'à nous**
   *(le geste exige l'id Hektor)*. Inoffensif aujourd'hui, **bloquant après la coupure.**

### LA SOLUTION PROPOSÉE — **recopier ce qui marche, et poser le filet qui manque**

| palier | ce qu'il fait | risque |
|---|---|---|
| **①** *(base)* | sur `app_console_document` : `present_in_hektor` + `absent_depuis` *(les mêmes noms que les photos — un seul vocabulaire)*, et `corbeille_le` / `corbeille_par` pour le cas ②. **Rien ne change à l'écran.** | nul |
| **②** *(worker)* | **cas ①** : les documents absents de la liste Hektor sont **marqués**, pas supprimés — **avec le garde-fou de liste vide**, posé **aussi pour les photos** · **cas ②** : la suppression par l'app **met en corbeille** *(ligne + fichiers gardés)* au lieu de détruire, **après** confirmation de Hektor | ⚠ **4 services** |
| **③** *(écran)* | la mention **« supprimé chez Hektor »** · la **corbeille** avec **Restaurer** · et le `confirm` qui dit la vérité au lieu de *« Supprimer ce document dans Hektor ? »* | ⚠ **Frédéric pousse** |

⭐ **Le palier ② corrige aussi un risque qui existe déjà sur les photos** — le garde-fou de liste
vide. C'est le genre de chose que ce chantier doit attraper au passage.

### ⚠ LA QUESTION DE FRÉDÉRIC QUE MA PROPOSITION NE COUVRAIT PAS (13/10)

> *« Mais tu me dis pas si après on peut supprimer une photo de mon app ? »*

**NON — et il a raison de le relever.** Mes trois paliers couvraient **les documents**, plus le
garde-fou des photos. **Supprimer une photo depuis l'app n'existe pas, et je ne l'avais pas
proposé.** C'est la 4ᵉ case du tableau, laissée vide.

### CE QU'IL FAUDRAIT, ET C'EST PLUS PETIT QUE PRÉVU

⭐ **Le worker sait déjà tout ce qu'il faut.** `fetchConsolePhotoEntries` extrait, pour chaque
photo lue sur la page console de Hektor *(l. 1272-1280)* :
`delete_filename` · `delete_annonce_id` · `delete_photo_id` · et **`actions.can_delete`**
*(est-ce que Hektor autorise la suppression)*.

⚠ **MAIS CE N'EST GARDÉ QUE SUR 1 401 PHOTOS SUR 441 117 — 0,3 %.** Les autres viennent d'un
chemin plus léger qui ne lit pas la page console, donc sans bouton de suppression.

⭐ **Et ça n'a aucune importance pour le correctif** : le worker **relira la page au moment du
geste** — exactement ce que fait déjà la suppression de document *(« `before = hektorFetch(listUrl)`
… introuvable avant suppression »)*. **On ne dépend donc pas de ce qui est stocké.**

### LE PALIER ④ QUE J'AJOUTE À LA PROPOSITION
**Supprimer une photo depuis l'app**, sur le patron **exact** de la suppression de document,
mais **avec la règle de Frédéric dès le départ** :
1. le geste à l'écran, avec un `confirm` **qui dit la vérité** ;
2. un travail `delete_hektor_photo` : le worker **relit la page console**, trouve l'id de
   suppression, **refuse si Hektor ne l'autorise pas** *(`can_delete`)*, supprime chez Hektor,
   **confirme** ;
3. puis **chez nous : CORBEILLE**, jamais de destruction.
⚠⚠ **ET LA RAISON D'ÊTRE PRUDENT EST ÉCRITE DANS LE CODE DES PHOTOS** : *« l'id porte le chemin
du fichier sur le serveur **et l'adresse PUBLIQUE de ses dérivés, qu'un portail met en cache et
qu'un email intègre**. Un id supprimé ne revient jamais. »* ➡ **une photo supprimée casse des
adresses publiques déjà diffusées.** La corbeille n'est pas un luxe ici, c'est une nécessité.

### ⭐ CORRECTION DE FRÉDÉRIC (13/10) : **PAS DE CORBEILLE, UN JOURNAL**

> *« Non, retire l'idée de la corbeille. Garde le code actuel qui détruit le fichier cloud, le
> fichier serveur et la ligne. Donc il faudrait juste une ligne, une forme de journal des
> suppressions : qui, quoi, quand. »*

**C'est plus simple et ça règle le vrai manque** : ce qui gênait n'était pas la destruction
*(elle est voulue)*, c'était **l'absence de trace**. Et ça supprime les deux problèmes de ma
proposition : **l'espace** *(229 Go qui ne décroissent plus)* et **la liste à l'écran**
*(que montrer ?)*.

### ⭐⭐ ET CE JOURNAL EXISTE DÉJÀ DANS LE PROJET — **DEUX FOIS**

| | lignes | colonnes |
|---|---|---|
| `app_console_deleted_annonce_log` | **78** | 9 |
| `app_console_deleted_contact_log` | — | 9 |

**Le patron, mot pour mot :**
`id` · `job_id` *(quel travail)* · `app_dossier_id` · `hektor_annonce_id` · **`requested_by`
(QUI)** · `reason` *(pourquoi)* · ⭐ **`before_json` (TOUT ce qu'on savait AVANT)** ·
`result_json` · **`created_at` (QUAND)**.

**Éprouvé sur une vraie ligne** *(annonce 62741, 21/07)* : `before_json` garde **17 champs**
— adresse, prix, surface, statut, ville, n° de dossier… — et `requested_by` est rempli.
⚠ **Mais pas toujours** : la ligne du 29/08 *(annonce d'essai 99999999)* a `before_json` **vide**
et **aucun demandeur**. ➡ **le patron est bon, son remplissage doit être garanti.**

### LE MÉCANISME PROPOSÉ, VERSION CORRIGÉE

**① Deux journaux**, sur le patron exact *(un par objet, comme annonce et contact)* :
`app_console_deleted_document_log` et `app_console_deleted_photo_log`, plus l'id de l'objet.

**② Cas B — supprimé par l'app** *(documents, et photos au palier ④)* :
1. le worker vérifie que l'objet existe **chez Hektor** *(déjà fait)*
2. il **supprime chez Hektor** et **confirme** *(déjà fait)*
3. ⭐ **AVANT de détruire chez nous : il écrit la ligne de journal** — `before_json` = la ligne
   entière *(nom, type, empreinte sha256, taille, chemins cloud et serveur, id Hektor,
   visibilité)*, plus **qui** et **quand**
4. ⚠⚠ **ET SI LE JOURNAL ÉCHOUE, ON NE DÉTRUIT PAS.** L'ordre est tout : écrire après, c'est
   risquer de détruire sans trace — exactement le défaut qu'on répare
5. puis la destruction, **comme aujourd'hui** : cloud, serveur, ligne

**③ Cas A — disparu chez Hektor** *(inchangé par rapport à la proposition)* : la ligne **reste**,
marquée **« plus chez Hektor » + la date**, patron des photos recopié — **avec le garde-fou de
liste vide**, posé aussi pour les photos.

**④ L'écran** : le `confirm` dit **la vérité** — *supprimé chez Hektor **et chez nous**,
définitivement ; une trace est gardée* — et la mention « plus chez Hektor » pour le cas A.

### ⚠ CE QU'IL FAUT ACCEPTER EN CONNAISSANCE
| | |
|---|---|
| une suppression reste **définitive** | ⛔ **pas de restauration**. Le journal dit **ce qui a existé**, il ne le rend pas |
| ⚠⚠ **pour une PHOTO** *(palier ④)* | le code dit : *« l'id porte l'adresse PUBLIQUE de ses dérivés, qu'un portail met en cache et qu'un email intègre »* → **supprimer une photo casse définitivement des adresses déjà diffusées**. Sans corbeille, **c'est irréversible**. **À dire à Frédéric avant de construire le geste** |
| l'espace | ✅ **inchangé** — c'était l'avantage de sa correction |

### ⭐⭐ L'AUDIT DES DÉRIVÉS CHANGE LE GESTE PHOTO — à trancher avant de coder

`app_console_photo` porte **déjà** : `present_in_hektor` · `absent_depuis` · `derives_json` ·
`derives_generes_le` · **`hors_vitrine_depuis`**.

⚠ **Et `hors_vitrine_depuis` n'est pas « retirée par l'utilisateur »** — c'est **l'ANCRE DES SIX
MOIS D'UNE PURGE DÉJÀ CONÇUE** *(`notice/patch_ancre_six_mois_2026-09-26.sql`,
`app_photo_marquer_sortie_vitrine`)* : quand l'annonce cesse d'être en vente, ses photos
prennent la date, et la purge effacera leurs dérivés publics **six mois plus tard**. Avec deux
règles fines déjà écrites : *« on ne re-date jamais une photo déjà marquée, sinon l'horloge des
six mois repartirait chaque nuit »* et *« une annonce qui redevient vivante libère ses photos »*.

| mesure | |
|---|---|
| photos | **441 117** |
| **hors vitrine** *(annonce plus en vente)* | **365 946** — ancre la plus ancienne : **26/09** |
| avec des **dérivés publics** | **113 812** |
| hors vitrine **ET** avec dérivés | **38 641** ← la cible de la purge |
| **déjà purgeables** | **0** — la purge ne mordra pas avant **mars 2027** |

### ⛔ LA CONTRADICTION QU'IL FAUT RÉSOUDRE
Frédéric veut **détruire la ligne**. Mais la ligne **porte l'ancre des six mois et la liste des
dérivés**. ➡ **détruire la ligne rend les dérivés publics ORPHELINS POUR TOUJOURS** : des
fichiers publics que plus rien ne référence et que la purge ne trouvera jamais.

### ⭐ LA RÉSOLUTION PROPOSÉE — et elle donne le meilleur des deux
Le geste « supprimer une photo » :
1. supprime **chez Hektor** *(et refuse si Hektor ne l'autorise pas — `can_delete`)* ;
2. **journalise** — et `before_json` **emporte `derives_json`**, donc le journal devient
   **l'ancre de remplacement** pour une purge future ;
3. détruit **le fichier serveur** et **la ligne** *(comme Frédéric le demande)* ;
4. ⭐ **mais ne touche PAS aux fichiers dérivés publics.**
   ➡ **la photo disparaît immédiatement de la vitrine et des listes** *(la ligne n'existe plus,
   donc rien ne la liste)*, **et les adresses déjà diffusées** — portails en cache, emails
   envoyés — **continuent de répondre au lieu de tomber en erreur.**
   C'est exactement ce que le code des photos redoutait : *« l'adresse tomberait et le dérivé
   deviendrait orphelin »*.

### CE QUE ÇA DONNE, CAS PAR CAS — **LE MÉCANISME FINAL**
| | **document** | **photo** |
|---|---|---|
| **disparu chez Hektor** | la ligne **reste**, marquée `present_in_hektor=false` + `absent_depuis` *(nouveau, patron des photos)* | ✅ **déjà le cas** |
| **supprimé par l'app** | **journal** *(qui/quoi/quand)* **PUIS** destruction cloud + serveur + ligne *(comme aujourd'hui)* | **journal** *(dérivés inclus)* **PUIS** destruction serveur + ligne · **dérivés publics conservés** |
| garde-fou | **liste vide → on ne marque rien** *(nouveau, posé aussi pour les photos)* | idem |
| si le journal échoue | ⛔ **on ne détruit pas** | ⛔ **on ne détruit pas** |

## 3e — CODÉ ET APPLIQUÉ (13/10) · **sauf le geste photo, et je me corrige**

### ⚠⚠ D'ABORD, UNE ERREUR QUE J'AI FAITE
J'ai écrit *« c'est plus petit que je ne le craignais »* pour le geste
« supprimer une photo », parce que le worker capture `delete_photo_id`.
**C'était faux** : capturer les **arguments** de `delete_img(filename, annonceId, photoId)`
dans le HTML **n'est pas** connaître **l'adresse qui l'exécute**. Le worker ne connaît que
**deux** modes photo chez Hektor — `vignettes` et `vignettes_hidden` — **tous deux en lecture**.

⭐ **Et l'audit du 25/09 le disait déjà** *(`notice/AUDIT_PHOTOS_2026-09-25.md`)* :
> *« Aucun mode de suppression, de réordonnancement ou de choix de la photo principale n'a
> jamais été relevé. […] C'est le vrai travail : **les trouver d'abord**. »*
> Son plan, en trois étapes : ① **relever** les commandes de la page Photos **en lecture seule**
> sur une annonce d'essai *(~0,5 j, patron `Console/releve_assistant_etapes.js` — il n'écrit
> jamais ; ⚠ cadence 0,5 s, un 403 = arrêt)* · ② **coder** *(~1,5-2 j)* · ③ **éprouver avec
> l'accord de Frédéric** — *« supprimer une photo est irréversible »*.

➡ **Le palier ④ n'est donc pas un refus, c'est une reconnaissance à faire avant.**
`insertDeletedPhotoLog` est **écrite et prête**, avec un commentaire qui dit pourquoi elle
n'est appelée par personne — pour qu'on ne la prenne pas pour un oubli.

### CE QUI EST FAIT

| | |
|---|---|
| **la base** *(appliquée et contrôlée)* | 2 journaux · 4 politiques · 2 colonnes · **0 document sans mention** sur 162 544 · 3 index |
| **le journal AVANT la destruction** | `insertDeletedDocumentLog`, appelée avant les trois destructions. `before_json` = **toute la ligne** |
| ⭐ **et elle JETTE** | ⚠ ses deux aînées *(`insertDeletedAnnonceLog`, `insertDeletedContactLog`)* **avalent l'erreur** et laissent la suppression continuer — **c'est mesurable** : une ligne du journal des annonces a un `before_json` **vide**. Ici : **si la trace ne s'écrit pas, on ne détruit pas.** Un document gardé une heure de trop se resupprime ; détruit sans trace, non |
| **la mention « plus chez Hektor »** | posée par la synchro sur les documents absents de la liste Hektor — patron des photos recopié, **sans jamais re-dater** une ligne déjà marquée |
| ⭐⭐ **le garde-fou de liste vide** | posé **pour les documents ET pour les photos**, où il manquait depuis G.10bis. ⚠ Il ne refuse pas « liste vide » dans l'absolu *(une annonce peut n'avoir aucun document)* : il refuse de **marquer des lignes existantes** depuis une liste vide, **et il le dit** |
| **l'écran** | le `confirm` dit enfin la vérité — *« supprimé CHEZ HEKTOR et CHEZ NOUS, sans retour possible ; une trace est conservée »* — et la mention s'affiche sur la ligne, **en ambre** *(un constat, pas une panne)* |
| ⚠ **le `select` du front** | `present_in_hektor` et `absent_depuis` **ajoutés** : il nomme ses colonnes, donc sans ça la mention **n'arriverait jamais**, en silence — **le même piège que la clôture de mandat ce matin** |

**Contrôles** : `node --check` **OK** · `tsc -b` **vert** · témoins : le journal appelé **avant**
les destructions *(1 appel)*, **2** garde-fous de liste vide, la mention lue par le front.

### ⛔ CE QU'IL RESTE
1. ⚠ **4 services à redémarrer** — sans ça le worker en mémoire ne journalise rien et ne marque rien.
2. ⚠ **Frédéric pousse** le front.
3. ⬜ **Le geste « supprimer une photo »** : le relevé chez Hektor d'abord *(plan du 25/09)*.
4. ⬜ L'**écran du journal** *(qui a supprimé quoi)* : la table et les droits existent, la vue
   d'écran n'est pas faite. ⚠ **Réservée aux admins** par la politique.

---

## LES PREUVES PAR LE VRAI CHEMIN (14/10, matin) — **le bien d'essai 62774**

**62774 = « TEST C4 du 25-08 Villa Bellecour »** : **vivant** *(archive=0, « Sous offre »)*,
mandat **18836**, échéance 2027-09-24, **13 documents**. ⭐ Le seul bien d'essai qui permette
les trois preuves.

### ✅ PREUVE DE 3e — le code du worker a tourné pour de vrai
Travail `sync_console_documents` créé comme l'écran le crée *(`priority 45`,
`reason: preuve_3e_14_10_2026`)*. Le worker **redémarré hier à 21:28** l'a pris en **4 s** et
fini en **77 s**.

| | |
|---|---|
| documents de l'annonce | **13** |
| **marqués « plus chez Hektor »** | **0** — et **0 dans tout le parc** |
| le **garde-fou de liste vide** | ⛔ **ne s'est PAS déclenché** → la liste de Hektor n'était pas vide, **donc la comparaison a bien eu lieu** |
| erreurs du worker | **aucune** |

⭐ **0 marqué sur 13 existants, c'est la preuve que la comparaison a tourné ET qu'elle est
juste** : un défaut de ma boucle aurait marqué les 13.

### ✅ PREUVE DU RPC DE SAISIE (3c pièce 2) — en production
`app_set_mandat_cloture_optimistic('62774','18836','2026-10-14')` →
`{"ok": true, "ecrit_par": "frederic.gerphagnon@…", "avant_app": null, "date_hektor": null}`

| | |
|---|---|
| **le carnet** *(fait foi)* | **2026-10-14** · `origine=cloture_app` · **écrit par l'email de Frédéric** |
| **la vitrine** | `mandat_date_cloture_app` = 2026-10-14, et **l'écran montre 2026-10-14** |
| ⭐ `refreshed_at` de la ligne | **2026-10-14 05:00:36** — **elle a été réécrite cette nuit** |

### ⭐⭐ LE TÉMOIN DE LA PIÈCE 4 EST DONC EN PLACE, ET IL EST VALIDE
Contrairement à 62966 et 24933 *(archivés → lignes **gelées**, elles auraient survécu sans la
re-pose)*, **62774 est vivant : sa ligne SERA détruite et réinsérée cette nuit.**
➡ **Si la date du 14/10 est encore là demain matin, la pièce 4 est prouvée par le vrai chemin.**
Sinon, la re-pose ne marche pas — et on le saura.

### ⚠⚠ UNE INTERACTION QUI CHANGE L'ORDRE DES PREUVES
La preuve de la **pièce 5** *(le worker écrit NOTRE colonne)* demandait de passer un bien en
« Clos » **avec un n° de mandat**. ⛔ **Mais passer 62774 en « Clos » le ferait SORTIR du parc
vivant → sa ligne de registre GÈLERAIT → et ça détruirait le témoin de la pièce 4.**

➡ **Les deux preuves s'excluent sur le même bien.** Ordre retenu :
1. **aujourd'hui** : le témoin de la pièce 4 reste sur 62774, intact ;
2. **demain, après le run** : une fois la pièce 4 prouvée, on passe 62774 en « Clos »
   *(réversible par « Actif »)* et on vérifie que le worker écrit `mandat_date_cloture_app`
   **et non** `mandat_date_cloture`.
3. **possible aujourd'hui sans rien casser** : passer **62963** en « Clos ». Il **n'a pas de n°
   de mandat** *(c'est lui qui a journalisé « aucun numéro » le 12/10)* → ça éprouve **l'autre
   moitié de la pièce 5** : le faux cri doit être devenu un `done` *« clôture SAUTÉE »*, plus
   un `error`. **Demande l'accord de Frédéric** *(ça écrit un statut chez Hektor)*.

### ✅ PREUVE DU NETTOYAGE (3c pièce 5, moitié « ne plus crier ») — EN RÉEL, 14/10

Bien d'essai **62963** *(« TEST C15 entrepot depuis l app - a supprimer »)* : **aucun numéro de
mandat**, **0 ligne au registre** *(logique : le registre est rangé par couple annonce + n° de
mandat)*. État de départ relevé **avant** d'agir : `Actif`, `diffusable = 1`.

**Le journal du travail, mot pour mot :**
```
hektor_status         = done   « Statut Hektor Mandat clos envoye »   (status_value 6, diffusable 0)
cloture_mandat_locale = done   « Cloture du mandat SAUTEE : aucun numero de mandat
                                 dans la demande (le changement de statut, lui, a reussi) »
                               { "saute": true, "reason": "numero_mandat_absent" }
```
**Avant le 13/10 : `error` + « Clôture locale impossible ». Maintenant : `done` + « SAUTÉE ».**
➡ **Le témoin dans les deux sens.** Et la vraie panne reste une erreur *(code inchangé)*.

**Puis remis en `Actif`** : la fiche est revenue à `Actif` / `diffusable = 1`
**instantanément**, avant que Hektor ne soit informé — **3a en direct**.

### ⚠⚠ ET DEUX ERREURS DE MA PART, PENDANT CE TEST

**① Mon premier appel était incomplet, et j'ai failli accuser le code.**
J'ai appelé le RPC avec `target_status` **en argument** mais **pas dans la charge du travail**.
Le worker lit `payload.target_status || payload.status || payload.targetStatus` *(l. 14591)* →
il a répondu **« Statut Hektor non supporté : undefined »** et le travail est tombé en erreur.
⭐ **L'écran, lui, le met aux DEUX endroits** *(api.ts l. 9876 **et** l. 9966)*. **C'était donc
mon essai qui était faux, pas le code** — et je l'ai vérifié avant de conclure.
⚠ **Conséquence qu'il a fallu réparer** : 62963 était alors **`Clos` chez nous et `Actif` chez
Hektor**. Le second appel, correct, a aligné les deux. **Une divergence créée par un essai doit
être refermée par l'essai suivant, pas laissée.**

**② J'ai cru un compte rendu plutôt qu'une mesure.**
Le RPC rend `champs_au_carnet: 0`, et j'ai annoncé *« mon bloc de 3a/3b n'a rien écrit »*.
**Faux** : le carnet portait bien **3 lignes** —
`statut=Clos` · `diffusable=0` · ⭐ **`clos_motif=choiceAutre · autre · <le texte complet>`**,
toutes en `origine=geste_statut`. **3a et 3b marchent ; c'est ce compteur qui mesure autre
chose.** *(Leçon déjà écrite : un compte rendu n'est pas une mesure.)*

**✅ 62963 RENDU À SON ÉTAT DE DÉPART** *(06:19:32)* : travail `done` — `hektor_status=done ·
sync_queue=done · finish=done` — **`Actif / diffusable=1` au parc vivant**, et **0 ligne à
l'index historique**. ⭐ **Et son aller-retour a prouvé le repli de 3b en direct** : en « Clos »
elle a quitté le parc vivant pour l'index historique, et c'est **seulement parce que le repli
existe** que le geste « Actif » a pu la ramener de là. **Hier, il aurait répondu
`dossier_not_found`.**
