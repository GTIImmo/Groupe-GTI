# Audit — l'identité des contacts (tâche 5, étape 0)

Date : 2026-08-20. **Lecture seule. Aucune ligne de code écrite.**

L'étape 0 que le plan impose avant de toucher à un objet : *« audit complet des points
d'appel, sur les TROIS couches — préalable absolu »*.

---

## 1. Le point de départ : il n'y a rien

| | Annonces | Transactions | **Contacts** |
|---|---|---|---|
| Numéro à l'app avant le chantier | `app_dossier.id`, **existait depuis toujours** | aucun | **aucun** |
| Ce qu'il a fallu faire | *aligner* deux séries qui avaient divergé | *ajouter* une colonne dans **3 fichiers** | **créer une série qui n'existe nulle part** |

Vérifié des deux côtés : **aucune colonne `app_contact_id`**, ni dans les 17 tables Supabase,
ni dans les 7 tables locales. Le contact n'est identifié que par le numéro de Hektor.

**Volumes** : 355 641 contacts en local, 57 523 dans Supabase, **≈ 185 200 lignes** réparties
sur 17 tables (relations 77 394 · contacts 57 523 · rapprochements 46 174 · recherches 3 961 ·
le reste sous la centaine).

---

## 2. L'ampleur, couche par couche

| Couche | Occurrences de `hektor_contact_id` |
|---|---|
| Front (`api.ts`, `App.tsx`, composants) | **169** |
| Pipeline `phase2` | **150** |
| Backend Python | **92** |
| Worker | **87** |
| Fonctions de la base | **34** *(dont 11 au paramètre ambigu, 6 explicites)* |
| **Total** | **≈ 530 points** |

> **Comparaison** : le registre d'affaires, terminé ce matin, n'était touché que par
> **3 fichiers**. Ce n'est pas le même chantier.

### Les 11 fonctions de la base au paramètre ambigu

Toutes prennent `target_contact_id text` — un nom qui ne dit pas de quel numéro il s'agit :

```
   app_console_create_contact_search_job          app_console_create_update_contact_job
   app_console_create_delete_contact_job          app_console_create_update_contact_search_job
   app_console_create_delete_contact_search_job   app_console_create_update_mandant_contact_job
   app_console_request_contact_refresh            app_edit_contact_optimistic
   app_edit_search_optimistic                     app_espace_create_search_update_job
   app_espace_edit_search_optimistic
```

Six d'entre elles fabriquent un travail pour le worker : **le numéro doit y rester celui de
Hektor**, sinon Hektor ne retrouve pas le contact. Les autres écrivent dans les tables de
l'app : **le numéro devra y devenir celui de l'app**. Aujourd'hui, rien ne distingue les deux
cas — parce qu'il n'y a qu'un seul numéro.

### Côté front, c'est étonnamment petit

**12 endroits seulement** appellent ces fonctions. Deux d'entre elles
(`createUpdateHektorContactSearchJob`, `createUpdateHektorContactJob`) n'ont **aucun appelant** :
à vérifier avant de les renommer.

---

## 3. Ce que le plan ne dit pas — et qui commande tout

**Deux clés du projet sont fabriquées en hachant le numéro de contact.**

```
   contact_search_key = hachage( contact_id , index , contenu de la recherche )
   relation_key       = hachage( contact_id , annonce , role , transaction )
```

| Clé | Lignes | Portée |
|---|---|---|
| `relation_key` | 77 394 | **sa propre table uniquement** — rien n'y pend → sans danger |
| **`contact_search_key`** | **3 961** | **11 tables** : rapprochements, historique de score, propositions, relances, notifications, envois, statuts acquéreur, messages espace client, demandes de visite… |

> **C'est exactement la clé dont nous avons réparé les orphelins ce matin.**
> Elle a déjà détaché 1 373 rapprochements et la moitié des propositions commerciales
> entre juin et août, simplement parce qu'elle bouge quand le contenu de la recherche change.

**Donc, la question qui décide de la forme du chantier :**

- Si les clés dérivées **continuent** de hacher le numéro de Hektor → rien ne se détache
  aujourd'hui, mais **le jour de la coupure, un contact neuf n'a pas de numéro Hektor et ne
  peut donc pas avoir de clé de recherche.**
- Si elles **basculent** sur le numéro de l'app → les 3 961 clés changent **toutes en même
  temps**, et tout ce qui y pend se détache. **C'est le sinistre de ce matin, multiplié.**

Aucune des deux options n'est bonne telle quelle. La sortie est celle déjà écrite pour les
recherches : **cesser de hacher**, faire de la clé une identité et non une empreinte de
contenu — ce que la fermeture des quatre portes rend possible (tâches 20-22).

---

## 4. Ce qui rassure quand même

- **Le worker n'a rien à changer** : il lit déjà un champ nommé `hektor_contact_id`.
  Comme pour les annonces, il continue de parler à Hektor avec le numéro de Hektor.
- **Le précédent existe** : **9 des 17 tables portent déjà `app_dossier_id`** à côté du numéro
  d'annonce Hektor. Le même geste, sur la même forme, a déjà été fait.
- **On n'a rien à renuméroter.** Contrairement aux annonces, il n'y a pas deux séries à
  réconcilier : on **ajoute** une colonne et on la remplit. Aucune valeur existante ne change.
  Les ≈ 185 200 lignes sont une **recopie**, pas une renumérotation.

---

## 5. Recommandation — couper la tâche 5 en deux

| | Quoi | Risque | Quand |
|---|---|---|---|
| **5a** | **Le renommage seul** — `target_contact_id` → `hektor_contact_id` dans les 11 fonctions, `contactId` → `hektorContactId` aux 12 appels du front | **nul** : aucun effet fonctionnel, vérifié par la compilation | **tout de suite** |
| **5b** | **L'identité elle-même** — ajouter la colonne aux 17 tables, la remplir, basculer les jointures | **élevé** | **après** que le sort de `contact_search_key` soit tranché |

**Pourquoi 5b doit attendre** : `contact_search_key` est le pivot commun au dossier
« contacts » et au dossier « recherches ». Le traiter deux fois, dans deux chantiers, avec
deux raisonnements différents, c'est la manière la plus sûre de recréer des orphelins.

**5a n'attend pas** : c'est le préalable que le plan exige, il rend visible partout la
différence entre les deux numéros, et il ne peut rien casser.

Voir `PLAN_DEV_ACTUALISE_2026-08-20.md` (tâche 5 / 1.5), le dossier recherches du même plan,
et `RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md`.
