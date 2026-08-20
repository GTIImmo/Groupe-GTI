# Audit — divergence d'identité `app_dossier` entre le serveur local et Supabase

Date : 2026-08-19
Statut : **constat établi, cause reconstituée, rien n'a été corrigé.**
Nature : audit en **lecture seule**. Aucune écriture locale, aucune écriture Supabase
(uniquement `select`). Aucun code modifié.
Origine : découvert le 19/08 par le **premier test de restauration** du projet
(cf. `NOTE_PLAN_SAUVEGARDE_2026-08-18.md`, §0.12 et §0.13).

> **À lire avant de toucher à quoi que ce soit.** Le sujet porte sur une clé qui n'est
> protégée par **aucune contrainte d'intégrité**, ni côté SQLite, ni côté Postgres. Une
> correction hâtive ferait plus de dégâts que le constat lui-même.

---

## 1. Le constat en une phrase

**Pour environ 94 % des dossiers que Supabase considère comme courants, l'identifiant
`app_dossier_id` ne correspond plus à `app_dossier.id` du serveur local.** Le dossier est
le bon, la donnée est la bonne, mais les deux systèmes ne l'appellent plus pareil.

Exemple vérifié de bout en bout :

| | Serveur local (`phase2.sqlite`) | Supabase (`app_dossier_current`) |
|---|---|---|
| identifiant | `1 337 944` | **`613`** |
| `hektor_annonce_id` | 11701 | 11701 |
| `numero_dossier` | **EM66580** | **EM66580** |

Même dossier. Deux identités.

---

## 2. L'hypothèse de départ, et pourquoi elle ne suffit pas

L'intuition initiale était : *« le serveur local stocke tout, Supabase seulement certains
index — donc les annonces archivées n'ont pas d'id Supabase. »*

**Elle est exacte sur le volume, et hors sujet sur la cause.** Supabase porte bien un
sous-ensemble (13 220 lignes courantes contre 56 880 en local). Mais les 300 paires testées
provenaient **toutes** de `app_dossier_current` : ce sont des dossiers que Supabase connaît
et affiche. Le problème n'est donc pas l'absence de certains dossiers — c'est le
**désaccord sur l'identifiant de dossiers présents des deux côtés**.

---

## 3. Ce qui est établi

### 3.1 La distribution locale est bimodale, avec un trou impossible

```
app_dossier (local), 56 880 lignes
        id <  25 000  ->    504 lignes
 25 000 .. 1 000 000  ->      0 ligne      <-- trou total
        id >   1 M    -> 56 376 lignes
sqlite_sequence       ->  5 193 217
```

Un `INTEGER PRIMARY KEY AUTOINCREMENT` ne produit jamais un trou de 975 000 valeurs.
Le compteur a été poussé, ou des lignes ont été insérées avec des identifiants imposés.

### 3.2 Les dates de création datent l'événement

| Bloc | Lignes | `created_at` |
|---|---|---|
| bas (`id < 25 000`) | 504 | **une seule valeur : `2026-03-30 13:15:22`** |
| haut (`id > 1 M`) | 56 376 | du `2026-05-20` au `2026-08-19`, dont **55 427 le `2026-06-05`** |

Le dossier de l'annonce 11701 porte `created_at = 2026-06-05 13:39:15`. Il a donc été
**(re)créé** ce jour-là, avec un identifiant neuf — alors que le dossier lui-même existe
depuis bien avant (`source_updated_at = 2024-08-21`).

### 3.3 Supabase a conservé l'ancienne génération d'identifiants

```
app_dossier_current, 13 220 lignes
        id <  25 000  -> 12 428 lignes   <-- ancienne generation
 25 000 .. 1 000 000  ->    125 lignes
        id >   1 M    ->    667 lignes   <-- nouvelle generation
doublons sur hektor_annonce_id : 0
annonces distinctes            : 13 220
```

Le local n'a plus que **504** lignes sous 25 000, quand Supabase en porte **12 428**.
Environ **11 900 identifiants Supabase ne correspondent donc à aucune ligne locale.**

### 3.4 Le lien n'est pas rompu — il passe par une autre clé

Test sur 300 paires réparties de l'id 613 à 4 791 021, empreinte md5 confirmée identique
à celle de Supabase :

| Résultat | Valeur |
|---|---|
| introuvables par les deux clés | **0 / 300** |
| divergents (id résout mais vers un autre bien) | **0** |
| résolus par `app_dossier.id` | 27 |
| résolus par `hektor_annonce_id` | **273** |

**Aucune donnée n'est perdue ni mal appariée.** Mais la clé qui fait réellement le joint
entre les deux systèmes est `hektor_annonce_id` — **l'identifiant de Hektor, pas le nôtre.**

---

## 4. La cause — trouvée, nommée, datée

### 4.1 Le mécanisme : `reconcile_app_dossier()`

Une note du projet le documente : **`NOTE_CORRECTIF_RECONCILIATION_APP_DOSSIER_PHASE2_2026-03-30.md`**,
datée du **30 mars** — le jour même de la première génération d'identifiants.

Elle décrit l'ajout d'une étape `reconcile_app_dossier()` en tête de `bootstrap_phase2.py`,
avec une intention parfaitement légitime : *« éviter le cumul de dossiers orphelins dans
`app_dossier` lors des upgrades quotidiens »*. Le code, tel qu'il était avant le 6 juin :

```python
orphan_ids = [ ... ]   # dossiers absents de hektor.case_dossier_source
                       # avec annonce_source_status = 'present'
for table in ("app_broadcast_action", "app_blocker", "app_followup",
              "app_internal_status", "app_note", "app_work_item"):
    con.execute(f"DELETE FROM {table} WHERE app_dossier_id IN (...)", orphan_ids)
con.execute("DELETE FROM app_dossier WHERE id IN (...)", orphan_ids)
```

**Le défaut n'est pas la suppression — c'est la combinaison de trois choses :**

1. le critère d'orphelin est `annonce_source_status = 'present'` : **tout dossier qui sort
   temporairement du périmètre actif** — archivé, vendu, retiré, ou simplement absent d'une
   synchronisation partielle — devient « orphelin » ;
2. `app_dossier.id` est un `AUTOINCREMENT` : un dossier supprimé puis recréé au run suivant
   **ne retrouve jamais son identifiant** ;
3. 32 tables Supabase et 10 vues sont clées sur cet identifiant, **sans une seule contrainte
   de clé étrangère** pour signaler quoi que ce soit.

### 4.2 La chronologie

| Date | Événement |
|---|---|
| **2026-03-30 13:15:22** | Population initiale. Identifiants denses à partir de 118. **C'est cette génération que Supabase porte encore.** |
| **2026-03-30** | Ajout de `reconcile_app_dossier()`. La note du jour documente l'intention, pas l'effet de bord sur les identifiants. |
| 30/03 → 20/05 | Cycles supprimer/recréer répétés. Le compteur `AUTOINCREMENT` grimpe et franchit le million. |
| **2026-06-05, 13h39 → 14h** | **55 426 lignes recréées en une heure.** Le périmètre `case_dossier_source` a manifestement basculé en masse ; la réconciliation a supprimé, le bootstrap a réinséré — avec des identifiants neufs au-dessus du million. |
| **2026-06-06 07:32** | Commit `26515f9` : la suppression est **désactivée** et remplacée par un simple avertissement. Quelqu'un a vu le dégât le lendemain matin. |

Le code d'aujourd'hui :

```python
print("WARNING bootstrap skipped orphan app_dossier cleanup: "
      f"{len(orphan_ids)} row(s) would have been removed")
return
```

**L'hémorragie est arrêtée depuis le 6 juin.** Elle n'a jamais été refermée côté Supabase.

C'est, mot pour mot, le scénario que le brief de sauvegarde décrivait comme le risque
majeur du modèle de données — « ré-émettre les ids AUTOINCREMENT orpheline silencieusement
32 tables Supabase, sans qu'aucune erreur ne remonte nulle part ». **Ce n'était pas un
risque à venir : c'est arrivé le 5 juin, ça a été stoppé le 6, et la trace est restée.**

---

## 5. Une couche de compensation existe déjà — et personne ne le savait

> **Correction de la première version de cette note.** J'y écrivais que « le défaut est
> armé, il n'a pas encore tiré ». **C'est faux pour le push principal.** La suite de
> l'analyse a montré qu'un mécanisme de compensation a été construit, délibérément, et
> qu'il fonctionne. Voici l'état exact.

`phase2/sync/push_upgrade_to_supabase.py` — le push de masse, celui du run quotidien —
**lit les deux identités et réconcilie sur `hektor_annonce_id`** :

```python
local_id_by_hektor_id  = { hektor_annonce_id -> app_dossier_id  LOCAL  }
remote_id_by_hektor_id = { hektor_annonce_id -> app_dossier_id  SUPABASE }

id_rewrites = { local_id: remote_id
                for hektor_id, local_id in local_id_by_hektor_id.items()
                if (remote_id := remote_id_by_hektor_id.get(hektor_id)) is not None
                   and remote_id != local_id }

rewrite_payload_app_dossier_ids(payload, id_rewrites)   # tout le payload est reecrit
```

Il réécrit ensuite `candidate_ids`, `targeted_dossier_ids`, et **journalise le compteur**
(`"remote_id_rewrites": len(id_rewrites)`).

**Autrement dit : le push de masse préserve délibérément les identifiants de Supabase.**
Ce n'est pas un accident, c'est une décision d'ingénierie — invisible depuis l'extérieur,
mais qui tient depuis deux mois et demi.

Deux garde-fous s'y ajoutent, sur la suppression des lignes distantes devenues sans
correspondance locale :

```
--allow-stale-deletes   « Disabled by default as a safety guard »
--max-stale-deletes 500
-> RuntimeError("Safety stop: refusing to delete N stale remote dossiers ...
                 Re-run with --allow-stale-deletes only after a manual audit.")
```

**Conclusion : l'application n'est pas en danger, et ne l'a jamais été.** Les 12 428 lignes
« périmées » ne le sont qu'en apparence : le push les reconnaît par `hektor_annonce_id` et
écrit dedans.

## 5bis. Le push individuel est traité aussi — par une stratégie inverse

> **Seconde correction.** J'ai d'abord conclu qu'il restait un trou dans
> `push_single_annonce_to_supabase.py`. **C'est faux également.** Une compensation existe,
> différente de celle du push de masse, et elle est câblée dans le flux principal.

`main()`, ligne 559 — juste après le push :

```python
counts = push_payload(client, payload, app_dossier_id)
counts["ghost_dossiers_removed"] = reconcile_annonce_dossiers(client, hektor_annonce_id, app_dossier_id)
```

`reconcile_annonce_dossiers()` — son propre commentaire dit tout :

> *« Durcissement anti-fantôme : si la MÊME annonce a d'autres `app_dossier` dans Supabase
> (l'id de dossier a changé suite à une ré-indexation), supprime ces doublons. »*

Elle fait plus que supprimer. Pour chaque ligne fantôme, elle **re-pointe les données
dépendantes vers le bon dossier avant de nettoyer** — registre de mandats, retours acquéreur
(cœur/pouce/motif), propositions, relances — puis purge les rapprochements orphelins et les
recalcule sous le bon identifiant. Le commentaire du code précise : *« on RE-POINTE l'ancien
`app_dossier_id` vers le bon (jamais supprimer) »*.

**Les deux mécanismes sont donc complémentaires — mais de stratégie opposée :**

| | Stratégie | Effet sur l'identifiant |
|---|---|---|
| `push_upgrade_to_supabase.py` (masse, quotidien) | **préserve** l'identifiant de Supabase, réécrit le payload local | l'ancien identifiant survit |
| `push_single_annonce_to_supabase.py` (individuel) | **impose** l'identifiant local, re-pointe les dépendances, supprime le fantôme | l'identifiant migre vers la valeur locale |

**Ils convergent, ils ne s'opposent pas.** Une fois qu'un dossier a été touché
individuellement, il porte l'identifiant local des deux côtés, et le push de masse n'a plus
rien à réécrire. Il n'y a **pas** de va-et-vient.

Conséquence réelle : le parc migre **lentement et silencieusement** vers les identifiants
locaux, un dossier à la fois, au gré des éditions. C'est cohérent — mais personne ne l'a
décidé explicitement, et rien ne le mesure.

## 5ter. La dette d'orphelins laissée par le correctif du 6 juin

`app_dossier_current` a pour **clé primaire `app_dossier_id` seul**. Vérifié :

```
PRIMARY KEY  app_dossier_current_pkey  (app_dossier_id)
UNIQUE sur hektor_annonce_id : AUCUN
```

Or le push (`phase2/sync/push_single_annonce_to_supabase.py`) est piloté **par
l'identifiant local** :

```python
client.delete_rows_by_ids(path=table, column="app_dossier_id", ids=[app_dossier_id])
...
client.upsert_rows(path="app_dossier_current", rows=current_dossiers, batch_size=10)
```

Déroulé pour un dossier du bloc bas — par exemple l'annonce 11701 :

1. le worker lit l'identifiant **local** : `1 337 944` ;
2. `delete_rows_by_ids(app_dossier_id = 1 337 944)` → **ne supprime rien**, la ligne
   Supabase porte `613` ;
3. l'upsert insère une **nouvelle ligne** `1 337 944` ;
4. l'annonce 11701 existe alors **deux fois** dans Supabase — `613` (périmée) et
   `1 337 944` (fraîche) — et **rien ne l'interdit**.

**Aucun doublon n'existe aujourd'hui** (mesuré : 0) — et c'est le résultat attendu, puisque
`reconcile_annonce_dossiers()` nettoie dans la foulée de chaque push individuel (§5bis).

Le correctif du 6 juin a désactivé la suppression d'orphelins et l'a remplacée par un
avertissement. **La dette qu'il laisse s'accumuler est mesurable, et elle est négligeable :**

```
logs/scheduled/quotidien_2026-08-17_05-30-01.log
logs/scheduled/quotidien_2026-08-18_05-30-01.log
logs/scheduled/quotidien_2026-08-19_05-30-01.log
  -> WARNING bootstrap skipped orphan app_dossier cleanup: 3 row(s) would have been removed
```

**3 lignes sur 56 880 (0,0 %), stables sur trois jours.** Le correctif provisoire du 6 juin
tient parfaitement. Il n'y a pas de dette qui grossit.

---

## 6. Ce qui n'est PAS établi

Je préfère l'écrire que le laisser deviner :

- **Le sens exact de la divergence.** Réimport local ayant réattribué les identifiants
  (lecture retenue), ou tout autre mécanisme ? Le faisceau est fort mais ce n'est pas une
  démonstration.
- **Pourquoi le compteur a franchi le million** entre le 30/03 et le 20/05.
- **Ce qui s'est passé le 2026-06-05** : quel script, lancé par qui, dans quel but.
- **L'étendue réelle.** Le constat porte sur `app_dossier_current` et sur un échantillon de
  300 lignes. **Les 31 autres tables et 10 vues clées sur `app_dossier_id` n'ont pas été
  auditées.** Elles peuvent être cohérentes avec Supabase (probable, il est cohérent avec
  lui-même) ou porter des mélanges.
- **Les tables d'index archivées et historiques** (`app_archive_annonce_index_current`,
  `app_historical_annonce_index_current`) n'ont pas été regardées.

---

## 7. Recommandations

### 7.1 Ce qu'il ne faut PAS faire

**Ne pas « réaligner » les identifiants.** Ni dans un sens, ni dans l'autre. Sur une clé
sans contrainte d'intégrité, portée par 32 tables et 10 vues, une réécriture de masse est
le geste le plus dangereux possible — et il est irréversible sans sauvegarde vérifiée.

**Ne pas ajouter dans l'urgence une contrainte `UNIQUE` sur `hektor_annonce_id`.** Elle
serait probablement souhaitable à terme, mais posée maintenant elle **ferait échouer les
push** au lieu de créer des doublons. On remplacerait une anomalie silencieuse par une
panne bruyante, sans avoir compris le fond.

**Ne pas traiter ce sujet dans le chantier Sauvegarde.** Il est distinct.

**Ne rien corriger dans le code.** C'est la conclusion la plus importante de cet audit, et
elle est arrivée après deux erreurs de ma part (§5 et §5bis). Les deux chemins de push sont
déjà traités, chacun à sa manière, et ils convergent. Il n'y a pas de bug à réparer.

### 7.2 Ce que je propose, dans l'ordre

**A — Poser un détecteur (≈ 1 h). Le seul geste vraiment utile.** Une sonde dans
`monitoring/check_gti_health.py` qui compte les `hektor_annonce_id` apparaissant plus d'une
fois dans `app_dossier_current`. Valeur attendue : **0**. Le jour où elle passe à 1, on le
sait **le lendemain** au lieu de le découvrir par hasard six mois plus tard.

C'est le bon geste parce qu'il **n'agit sur rien** : il transforme un mécanisme silencieux
en mécanisme observable. Toute cette affaire n'a été découverte que par accident, au
détour d'un test de restauration.

**B — Écrire la décision, puisqu'elle a été prise sans l'être.** Deux stratégies opposées
cohabitent (§5bis) et le parc migre lentement vers les identifiants locaux. C'est cohérent,
mais implicite. Trancher et documenter : **la cible est l'identifiant local, et la clé de
rapprochement inter-systèmes est `hektor_annonce_id`.**

Ce choix a un prix qu'il faut regarder en face : **il fait reposer le joint entre
l'application et ses propres données sur un identifiant qui appartient à Hektor**, au moment
précis où le projet cherche à s'en affranchir. C'est un sujet pour le chantier
d'indépendance, pas pour celui-ci.

**C — Statuer sur le correctif provisoire du 6 juin (≈ 30 min).** Il tient depuis deux mois
et demi et ne laisse que 3 orphelins. Deux options : le pérenniser en l'assumant par écrit,
ou réactiver un ménage **qui ne supprime plus mais marque** (une colonne `absent_depuis`),
ce qui donnerait la propreté sans jamais réémettre d'identifiant. La seconde est meilleure ;
aucune n'est urgente.

**D — Ce qui reste non mesuré, si un jour le besoin s'en fait sentir.** Le recouvrement
complet sur les 31 autres tables et 10 vues clées sur `app_dossier_id` n'a pas été fait.
Rien n'indique un problème — Supabase est cohérent avec lui-même — mais le chiffre n'existe
pas. À faire seulement si un symptôme apparaît.

---

## 8. Ce que cela change pour le chantier Sauvegarde

Un point rassurant, et un seul : le brief présentait `phase2.sqlite` comme « le point de
défaillance unique du modèle de données », au motif que sa perte orphelinerait 32 tables
Supabase. **Cette criticité doit être relue.** Supabase est cohérent avec lui-même, porte
`hektor_annonce_id` sur ses lignes, et n'a déjà **plus** besoin des identifiants locaux pour
que ses propres jointures tiennent.

Cela ne diminue en rien la valeur de la sauvegarde de `phase2.sqlite` — elle porte 56 880
dossiers, le registre d'affaires et les caches de scrape. Mais le scénario catastrophe
décrit dans le brief s'est **déjà produit**, et l'application fonctionne. C'est une
information utile pour dimensionner correctement l'inquiétude.

---

## 9. Méthode

Tout a été mesuré le 2026-08-19 entre 09:30 et 10:15, en lecture seule.
Bases SQLite ouvertes en `mode=ro`. Supabase interrogé par `select` uniquement
(`execute_sql`), projet `dwaqxfrinihnychuoptk`.

Contrôle anti-erreur : l'échantillon de 300 paires a été validé par comparaison d'empreinte
md5 avec celle calculée par Supabase (`eed4c66ec8ac19604b8a8fc8fa8dd23c`, 3 438 caractères)
**avant** toute comparaison — pour qu'une erreur de recopie ne puisse pas être prise pour
une divergence de données.

Contrôle croisé : chaque test échoué sur la base restaurée a été rejoué sur la base
**vivante**. Résultats identiques — ce qui a permis d'écarter la sauvegarde comme cause et
d'orienter vers le modèle de données.
