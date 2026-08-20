# Étude — les 34 workers : existant mesuré, faisabilité du plan, plan corrigé

Date : 2026-08-20. **Lecture seule.** Méthode : fermeture transitive des appels de chaque
gestionnaire dans `console_job_worker.js` (profondeur 4), puis comptage des appels Hektor
(`hektorFetch`, `XMLRPC_URL`, `CONSOLE_URL`, `protexa`, `ImmoSign`) et des accès au stockage de l'app.

> **Correction d'une erreur de la version précédente.** J'avais classé les trois générations de PDF
> comme « seul Hektor sait les produire ». **C'est faux, et l'inverse est vrai** : elles ne font
> AUCUN appel à Hektor. C'est l'app qui les fabrique.

---

# PARTIE 1 — L'EXISTANT

## 1.1 Quatre familles, établies par la mesure

| Famille | Workers | Appels Hektor |
|---|---|---|
| **A — L'app seule** | 3 | **0** |
| **B — Vers Hektor** | 19 | 2 à 27 |
| **C — Aller-retour** | 8 | 2 à 30, plus le stockage app |
| **D — Interne** | 4 | 0 (script local ou file) |

## 1.2 Famille A — l'app fait tout, Hektor n'est pas appelé

| Worker | Ce qu'il produit |
|---|---|
| `generate_mandat_document` | le PDF du mandat |
| `generate_estimation_pdf` | le PDF de l'avis de valeur |
| `generate_cadastre_document` | le plan cadastral |

**Zéro appel Hektor.** Ils lisent les données de l'app, produisent un PDF, l'écrivent dans le
stockage. Le dépôt du PDF dans Hektor, quand il a lieu, est un **travail séparé**
(`upload_document_to_hektor`).

> **Ces trois-là sont déjà indépendants. Ils survivront à la coupure sans une ligne de code.**

## 1.3 Famille B — l'app envoie, Hektor reçoit

Deux natures très différentes à l'intérieur :

**B1 — Ils modifient un état que l'app connaît déjà** *(13)*

`change_hektor_annonce_status` · `archive_hektor_annonce` · `restore_hektor_annonce` ·
`delete_hektor_annonce` · `assign_hektor_annonce_negotiator` · `update_hektor_annonce_fields` ·
`update_hektor_contact` · `add/update/delete_hektor_contact_search` · `link_hektor_mandant` ·
`update_hektor_mandant_contact` · `delete_hektor_contact`

**B2 — Ils créent un objet neuf** *(3)*
`create_hektor_draft_annonce` · `create_hektor_contact` · `create_hektor_mandant_contact`

**B3 — Ils obtiennent une chose que seul Hektor produit** *(3)*
`create_hektor_mandat_auto_number` (19 appels) · `relance_signature` (3) ·
`cancel_signature_procedure` (3)

## 1.4 Famille C — aller-retour, surtout du rapatriement

`sync_console_documents` (30 appels Hektor, **37 000 travaux/mois**) · `sync_hektor_photos` ·
`upload_hektor_photo` · `upload_document_to_hektor` · `delete_document_from_hektor` ·
`prepare_document_cloud` · `refresh_console_data` · `delete_hektor_annonce`

## 1.5 Famille D — interne

`prepare_archived_annonce_detail` et `prepare_historical_annonce_detail` (lancent un script
Python local) · `refresh_console_contact_data` · `matterport_reactivate`

---

# PARTIE 2 — FAISABILITÉ DU PLAN

## 2.1 Le principe « écrire d'abord, envoyer, comparer au retour »

| Famille | Applicable ? | Pourquoi |
|---|---|---|
| **B1** (13) | ✅ **oui, entièrement** | l'app connaît le résultat avant de partir |
| **B2** (3) | ✅ oui, avec le distributeur de numéros | |
| **B3** (3) | ❌ **non** | la valeur n'existe pas avant la réponse |
| **A** (3) | **sans objet** | déjà app-only, rien n'est envoyé |
| **C** (8) | ❌ non | ils vont chercher, ils ne décident rien |
| **D** (4) | sans objet | |

**Le gisement réel : 16 workers** (B1 + B2), et ils se traitent tous avec la même mécanique.

## 2.2 Ce qui reste vraiment dépendant de Hektor

**Trois workers, et trois seulement :**

| Worker | Ce que Hektor fournit | Remplacé par |
|---|---|---|
| `create_hektor_mandat_auto_number` | le numéro de mandat | le registre en propre |
| `relance_signature` | la relance de signature | Yousign |
| `cancel_signature_procedure` | l'annulation de signature | Yousign |

**Ce sont exactement les deux contrats du chemin critique.** Les 31 autres workers ne dépendent
de Hektor que parce que Hektor détient encore la donnée — pas parce qu'il produit quelque chose.

## 2.3 Ce que devient chaque famille à la coupure

| Famille | Devenir |
|---|---|
| **A** (3) | **survivent tels quels** |
| **D** (4) | survivent, ou disparaissent avec le pipeline |
| **B** (19) | **disparaissent** — plus rien à envoyer |
| **C** (8) | disparaissent, sauf la partie stockage de l'app |

> **7 workers sur 34 fonctionnent déjà sans Hektor.**

## 2.4 Les points durs, mesurés

1. `sync_console_documents` : **97 % du volume**. Invisible et silencieux par nature, mais c'est
   lui qui sature la file — 4 h d'attente moyenne.
2. `assign_hektor_annonce_negotiator` : à convertir **en dernier**, l'identifiant sert à
   l'impersonation du worker.
3. `change_hektor_annonce_status` : le plus riche — statut **et** affaire **et** liaisons contact.
   Il faut le traiter comme une création d'affaire, pas comme un statut.
4. Le mandat d'une transaction est parfois **deviné dans le HTML de Hektor** si l'app ne le fournit pas.

---

# PARTIE 3 — LE PLAN CORRIGÉ

## Tout de suite, sans dépendance

| | |
|---|---|
| **1** | Les **trois recherches acquéreur** écrivent enfin dans l'app *(seul cas de perte réelle)* |
| **2** | **Un échec prévient** l'utilisateur et le monitoring |
| **3** | Le numéro Hektor a le droit d'être vide |
| **★** | **Yousign + registre de mandats** — ce sont les 3 seuls workers réellement dépendants |

## Ensuite

| | |
|---|---|
| **4** | **Hektor confirme au lieu d'écraser** (la traduction des valeurs existe déjà) |
| **5** | Convertir **B1**, dans l'ordre : recherches → statut/affaire → archiver/restaurer/supprimer → mandant → affectation en dernier |
| **6** | Donner une clé propre au **registre des affaires** |
| **7** | Fiabiliser le mandat des transactions |
| **8** | Un travail sans numéro Hektor **attend** au lieu d'échouer |

## Plus tard

| | |
|---|---|
| **9** | La création écrit la vraie fiche |
| **10** | Le calque disparaît |
| **11** | Les workers deviennent invisibles — **une fois l'avertissement d'échec éprouvé** |
| **12** | La coupure |
