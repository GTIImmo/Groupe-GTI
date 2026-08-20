# Audit — tous les identifiants du projet et leur provenance

Date : 2026-08-20. **Lecture seule.**
Question posée par Frédéric : *« tous les id générés par Hektor devront être générés par mon
serveur avant de couper. Fais l'audit, anticipe les problèmes. »*

Méthode : inventaire de toutes les colonnes d'identifiant des tables Supabase, puis recherche de
la source de chacune dans le code du pipeline et du worker.

---

## 1. GÉNÉRÉS PAR HEKTOR — à reprendre avant la coupure

| Identifiant | Tables | Volume | État |
|---|---|---|---|
| `hektor_annonce_id` | **35** | 13 215 courantes | ✅ **l'app a déjà `app_dossier_id`** |
| `hektor_contact_id` | **17** | 57 523 / 355 641 local | ❌ **aucune case à l'app** |
| `hektor_affaire_id` + `offre_id`/`compromis_id`/`vente_id` | 4 | 28 980 | ❌ **aucune case** |
| **`numero_dossier`** | **11** | **13 206** | ❌ **jamais anticipé — voir §1.1** |
| `numero_mandat` + `hektor_mandat_id` + `mandat_source_id` + `mandat_numero_reference` | 15 | 23 838 | ⚠️ couvert par le registre en propre |
| `hektor_negociateur_id` / `hektor_user_id` / `commercial_id` | **14** | **40 négociateurs** | ❌ **voir §1.2** |
| `hektor_agence_id` / `agence_nom` | 2+ | **19 agences** | ❌ idem |
| `hektor_broadcast_id` / `passerelle_key` / `portal_key` | 5 | 1 558 états | ⚠️ disparaît avec le contrat portails |
| `hektor_document_id` | 2 | 40 493 documents | ⚠️ voir §1.3 |
| `hektor_photo_id` | 1 | 1 397 photos | ⚠️ idem |

### 1.1 `numero_dossier` — le trou le plus discret

`view_generale.py:229` : `src.no_dossier AS numero_dossier`. **C'est Hektor qui le fabrique.**

C'est pourtant **ta référence métier lisible** — `EM66580`, `VA1946` — présente dans 11 tables,
affichée partout, utilisée dans les messages, les documents, les emails.

> **Le jour de la coupure, plus personne ne numérote un dossier neuf.**
> Il faut donc reprendre la série, comme pour l'identifiant technique : comprendre la règle
> (préfixe par type ? par agence ?) et la continuer. **Ce n'est dans aucun plan à ce jour.**

### 1.2 Les négociateurs et les agences

40 négociateurs, 19 agences, identifiés par des numéros Hektor présents dans **14 tables**.
Et l'identifiant du négociateur ne sert pas qu'à afficher un nom : **le worker s'en sert pour
s'impersonner** dans Hektor.

À la coupure, les workers disparaissent — donc l'impersonation aussi. Mais `commercial_id` reste
dans 9 tables comme **référence de l'affectation**. Il faut un annuaire à toi.
*(Trois tables d'annuaire existent déjà : `app_user_directory`, `app_hektor_negotiator_agency_directory`.)*

### 1.3 Documents et photos

`hektor_document_id` et `hektor_photo_id` **pointent vers le stockage de Hektor**. Ce ne sont pas
des identifiants métier : ce sont des adresses. Tant que les binaires ne sont pas tous rapatriés,
ils restent des liens vers un serveur qui va s'éteindre.
**Le rapatriement doit être terminé AVANT la coupure**, pas pendant.

---

## 2. DÉRIVÉS — calculés par l'app, mais à partir de données Hektor

| Clé | Composition | Risque |
|---|---|---|
| **`contact_search_key`** | hachage de *(contact, position, contenu)* | 🔴 **change à chaque édition — 1 270 rapprochements déjà orphelins** |
| `register_row_id` | `"annonce:numéro de mandat"` | 🟢 survit si les deux survivent |
| `relation_key` | structurelle *(annonce + contact + rôle)* | 🟢 |
| `duplicate_group_id` | groupe de doublons | 🟢 |

---

## 3. SERVICES EXTERNES — survivent à la coupure

`google_event_id`, `gmail_message_id`, `gmail_thread_id` (Google Workspace) ·
`matterport_model_id`, `matterport_internal_id` · `envoi_id`, `public_link_id`, `token` (emails et
liens publics, générés par l'app).

---

## 4. DÉJÀ À TOI

`id` (**44 tables**, compteur Postgres) · `app_dossier_id`, `app_archive_id`, `app_brouillon_id`,
`app_historical_id` · `sync_run_id`, `job_id`, `push_job_id` · `creation_token` ·
`app_user_id` (authentification Supabase).

---

## 5. CE QUE L'AUDIT AJOUTE AU PLAN

| | Sujet | Pourquoi c'est nouveau |
|---|---|---|
| **A** | **`numero_dossier`** | référence métier lisible, fabriquée par Hektor, dans 11 tables. Personne ne la numérote après la coupure |
| **B** | **Annuaire négociateurs et agences** | 40 + 19, dans 14 tables. L'app doit tenir son propre annuaire |
| **C** | **Rapatriement des binaires** | 40 493 documents et 1 397 photos pointent encore vers Hektor. **À terminer avant, pas pendant** |
| **D** | **Clé de recherche** | la seule clé structurellement fausse : elle change à chaque édition |

---

## 6. LA RÈGLE GÉNÉRALE QUI EN DÉCOULE

> **Pour chaque identifiant que Hektor fabrique, il faut répondre à trois questions avant la coupure :**
> **1.** Qui le fabriquera après ?
> **2.** Que deviennent les valeurs déjà émises ? *(elles restent — un numéro écrit reste valide)*
> **3.** Qu'est-ce qui casse s'il est vide ? *(clé primaire, jointure, affichage, ciblage worker)*
>
> Les annonces ont eu leurs trois réponses. Les contacts et les affaires les auront au chantier 1.
> **`numero_dossier`, l'annuaire et les binaires n'ont encore aucune réponse.**
