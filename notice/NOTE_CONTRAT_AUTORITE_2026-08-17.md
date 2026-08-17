# Contrat d'autorité — qui possède quoi entre l'app et Hektor

**Date : 2026-08-17. Proposition Claude à valider par Frédéric. AUCUN code.**
**Pilote la Phase 0c / correctif C6 de `AUDIT_GLOBAL_ET_METHODE_INDEPENDANCE_2026-08-08.md`.**
**Préfixe `NOTE_` volontaire (le motif `AUDIT_*.md` est exclu de git, cf. C1).**

---

## 1. À quoi sert ce document

C'est **la règle d'arbitrage** : quand l'app et Hektor ont deux valeurs différentes pour le même champ, qui gagne ?
Sans cette règle écrite, l'import de nuit et la migration 2×/jour se battent. Avec elle, chacun sait ce qu'il n'a pas le droit de toucher.

**Trois catégories, et trois seulement :**

| Catégorie | Définition | Comportement de l'import de nuit |
|---|---|---|
| 🟢 **APP** | Saisi/modifié par le négociateur **dans l'app**. L'app en est propriétaire. | **Ne réécrit jamais.** Seed une fois à la première apparition, puis ne touche plus. |
| 🔵 **HEKTOR** | **Produit** par Hektor ou par un des services externes (numéro de mandat, diffusion, signature). L'app ne sait pas le fabriquer. | **Rafraîchit librement.** C'est le retour de service. |
| ⚪ **SYSTÈME** | Identité, horodatage, champs dérivés/calculés. Personne ne les « saisit ». | Géré par la mécanique, hors arbitrage. |

**Rappel du mécanisme (précision C de la revue externe)** — il existe déjà **deux** protections dans `push_contacts_to_supabase.py` :
- ① **temporaire, par ligne** (`fetch_dirty_*`) : protège pendant l'aller-retour, **puis relâche** (la l. 446-449 dit explicitement « Hektor gagne ») ;
- ② **permanente, par champ** (`fetch_app_owned_contact_fields`) : ne couvre aujourd'hui que naissance / lieu / matrimonial.

⇒ **Appliquer ce contrat = faire passer tous les champs 🟢 du mécanisme ① au mécanisme ②**, et retirer la ligne 446-449.

---

## 2. ANNONCE / BIEN — `app_dossier_current`

### 🟢 APP (l'app gagne — le négociateur les saisit)
| Champ | Remarque |
|---|---|
| `prix` | Le champ emblématique. Déjà édité en optimiste. |
| `titre_bien` | |
| `adresse_detail`, `code_postal`, `ville` | Édition d'adresse = re-géocodage app (lat/lon). |
| `adresse_privee_listing`, `code_postal_prive_detail`, `ville_privee_detail` | |
| `type_bien` | |
| `commentaire_resume` | |
| `date_relance_prevue` | Purement app (aucun équivalent Hektor). |
| ~~**Tout le contenu descriptif du blob**~~ | 🔴 **LIGNE INVALIDÉE le 2026-08-17 — NE PAS APPLIQUER.** Voir §9. |

### 🔵 HEKTOR (Hektor renseigne — retour de service)
| Champ | Pourquoi |
|---|---|
| `numero_mandat` | Produit par le moteur registre Hektor (jusqu'à l'API partenaire, Phase 4). |
| `diffusable`, `nb_portails_actifs`, `has_diffusion_error`, `portails_resume` | **Retour de la diffusion portails.** |
| `validation_diffusion_state` | Idem. |
| `images_preview_json` | **Tant que les photos ne sont pas rapatriées (C9).** Bascule en 🟢 après. |
| `offre_id`, `compromis_id`, `vente_id`, `offre_state`, `compromis_state`, `offre_last_proposition_type` | Les affaires naissent côté Hektor aujourd'hui. |

### 🟠 PARTAGÉ — à trancher explicitement (le point délicat)
| Champ | Enjeu |
|---|---|
| `statut_annonce`, `archive` | Le négociateur change le statut **dans l'app** (🟢), mais Hektor peut aussi l'archiver. **Proposition : 🟢 APP**, car c'est un geste métier de l'app, et le push le répercute. À valider. |
| `negociateur_email`, `commercial_id`, `commercial_nom`, `agence_nom` | L'affectation se fait dans l'app (`assign_hektor_annonce_negotiator`) mais l'annuaire vient de Hektor. **Proposition : 🟢 APP pour l'affectation**, 🔵 pour l'annuaire (`app_user_directory`). |
| `mandat_type`, `mandat_date_debut`, `mandat_date_fin`, `mandat_montant` | Saisis dans l'app (éditeur de mandat/avenant) **mais** le mandat officiel est numéroté par Hektor. **Proposition : 🟢 APP** (sauf `numero_mandat` qui reste 🔵). |
| `mandants_texte` | Dérivé des relations contacts. **Proposition : ⚪ SYSTÈME** (recalculé). |

### ⚪ SYSTÈME (hors arbitrage)
`app_dossier_id`, `hektor_annonce_id`, `source_hash`, `source_updated_at`, `refreshed_at`, `search_text`, `statut_global`, `sous_statut`, `alerte_principale`, `priority`, `has_open_blocker`, `dernier_event_type`, `dernier_work_status`, `etat_visibilite`, `numero_dossier`, `date_enregistrement_annonce`, `photo_url_listing`, les `price_change_*` (journal de变化 calculé).

---

## 3. CONTACT — `app_contact_current`

### 🟢 APP
`civilite`, `nom`, `prenom`, `email`, `phone_primary`, `phone_secondary`, `adresse`, `code_postal`, `ville`, `birth_date`, `birth_place`, `marital_status`
→ Ce sont **exactement les 12 colonnes** déjà écrites par `app_edit_contact_optimistic`. Les 3 dernières sont **déjà** en mécanisme ② ; les 9 autres sont à y faire passer.
→ Ajouter aussi : commentaires, source, catégorie, préférences RGPD/CRM (dans `app_contact_override`).

### 🔵 HEKTOR
`hektor_negociateur_id`, `hektor_agence_id`, `commercial_nom`, `agence_nom` (annuaire Hektor) — jusqu'au remplacement de la source d'identité.

### ⚪ SYSTÈME
`hektor_contact_id` (+ le futur `app_contact_id`), `display_name`, `search_text`, `completeness_score`, `duplicate_*`, `linked_annonce_count`, `active_search_count`, `total_search_count`, `supabase_sync_eligible`, `date_maj`, `refreshed_at`, `has_contact_detail`, `contact_detail_synced_at`, `archive`.

---

## 4. RECHERCHE ACQUÉREUR — `app_contact_search_current`

### 🟢 APP — **tous les critères, sans exception**
`offre`, `villes_json`, `types_json`, `criteres_json`, `prix_min`, `prix_max`, `surface_min`, `surface_max`, `pieces_min`, `pieces_max`, `chambre_min`, `chambre_max`, `surface_terrain_min`, `surface_terrain_max`, `is_active`

**Justification** : c'est la matière première du moteur de rapprochement, qui est **100 % à toi**. Et l'édition de recherche est déjà l'un des trois flux optimistes.

⚠ **Prérequis bloquant** : tant que C3 (clé stable) et C4 (ciblage par `idCritere`) ne sont pas faits, déclarer ces champs 🟢 **ne suffit pas** — la ligne entière est supprimée puis réinsérée chaque nuit sous une clé potentiellement différente (C5). **Le contrat recherche n'est applicable qu'après C3+C4.**

### ⚪ SYSTÈME
`contact_search_key`, `search_index`, `contact_date_maj`, `refreshed_at`, `archive`.

---

## 5. BINAIRES

| Objet | Autorité | État |
|---|---|---|
| **Documents** (mandats, estimations, cadastre) | 🟢 **APP** | ✅ **Déjà le cas** — écrits d'abord dans `C:\Hektor\HektorConsoleDocuments`. |
| **Photos** | 🔵 HEKTOR → 🟢 APP après C9 | ❌ 100 % sur le CDN Hektor aujourd'hui. |
| **PDF signé** | 🔵 HEKTOR | Retour du service signature (jusqu'à Yousign). |

---

## 6. La règle en une phrase

> **L'app possède ce que le négociateur saisit. Hektor ne renseigne que ce qu'il produit lui-même : le numéro de mandat, l'état de diffusion, l'état de signature — et, provisoirement, les photos et les affaires.**

Tout le reste est soit à l'app, soit calculé.

---

## 7. Ce que ça implique concrètement (C6)

1. **Établir la liste blanche** des champs 🟢 dans `push_upgrade_to_supabase.py` et `push_contacts_to_supabase.py` : ne plus les inclure dans le payload de nuit **après le seed initial** (l'UPSERT « merge-duplicates » préserve alors automatiquement la valeur de l'app — mécanisme déjà éprouvé sur naissance/matrimonial).
2. **Retirer la ligne 446-449** de `push_contacts_to_supabase.py` (le « Hektor gagne » explicite en cas de conflit).
3. **Inverser le garde-fou anti-écrasement** pour les champs 🟢 : aujourd'hui un `date_maj` Hektor plus récent fait gagner Hektor ; pour un champ app-owned, c'est l'app qui doit gagner. Pour les champs 🔵, statu quo.
4. **Gérer le « seed une fois »** : un champ 🟢 n'est écrit par l'import que si la ligne est nouvelle ou n'a jamais été éditée dans l'app.

---

## 8. Les 4 arbitrages — TRANCHÉS (Frédéric, 2026-08-17)

| # | Champ | Décision | Effet |
|---|---|---|---|
| 1 | `statut_annonce`, `archive` | 🟢 **APP** | Le changement de statut est un geste métier de l'app ; le lot 2×/jour le répercute vers Hektor. |
| 2 | `negociateur_email`, `commercial_id`, `commercial_nom`, `agence_nom` (affectation) | 🔵 **HEKTOR pour l'instant → 🟢 APP à la DERNIÈRE phase** | **Décision de prudence, techniquement fondée** (voir encadré ci-dessous). |
| 3 | `mandat_type`, `mandat_date_debut`, `mandat_date_fin`, `mandat_montant` | 🟢 **APP** — `numero_mandat` reste 🔵 **HEKTOR** | L'éditeur de mandat/avenant est dans l'app ; seul le numéro officiel vient du moteur registre. |
| 4 | `images_preview_json` | 🔵 **HEKTOR jusqu'à C9 → 🟢 APP après rapatriement** | Cohérent avec le trou binaire photos. |

> **Pourquoi la décision n°2 est juste (et pas seulement prudente).**
> L'affectation du négociateur n'est pas un champ d'affichage : c'est **ce qui pilote l'authentification des workers**. Le worker se connecte avec un compte privilégié puis **prend l'identité du négociateur cible** (`switchHektorUserContextWithPlaywright`, autologin par `idUser` — `console_job_worker.js:1647`).
> Si l'app devenait propriétaire de l'affectation **avant** la coupure, une divergence app/Hektor ferait cibler la **mauvaise identité** — au mieux un 403, au pire une action exécutée sous le mauvais négociateur.
> ⇒ Tant que les workers d'écriture existent, **l'affectation doit rester alignée sur Hektor**. Elle bascule en 🟢 APP à la dernière phase, quand plus aucun worker n'a besoin de s'impersonner.
> *(L'affectation reste bien sûr modifiable depuis l'app via `assign_hektor_annonce_negotiator` — c'est l'**autorité au moment de l'import** qui reste à Hektor, pas le geste utilisateur.)*

**Le contrat d'autorité est désormais COMPLET** et peut piloter C6.

**Décisions déjà prises (2026-08-17)** : identité contact = **surrogate `app_contact_id`** ; stockage = **statu quo (local maître, cloud sélectif)** ; worker = **variante A puis B** ; orphelins = *à confirmer* (proposition : delete-never façon ledger d'affaires) ; ordre journalier = *à confirmer* (proposition : push puis pull).

---

## 9. 🔴 CORRECTION IMPORTANTE (2026-08-17) — le volet BLOB est invalidé

**Ce document affirmait au §2 que « tout le contenu descriptif du blob » appartenait à l'app.
C'est FAUX et cette règle ne doit pas être appliquée.**

**Ce qui s'est passé** : le contrat a été rédigé en supposant que
`app_dossier_detail_current.detail_payload_json` était un blob purement descriptif — sur la foi
de son nom, sans en inspecter le contenu. Vérification faite ensuite (~130 clés listées en base) :
le blob transporte AUSSI des données Hektor **vivantes** :

| Nature | Clés concernées |
|---|---|
| Diffusion | `diffusable`, `has_diffusion_error`, `nb_portails_actifs`, `portails_resume` |
| Affaires | `offre_*`, `compromis_*`, `vente_*` (états, montants, acquéreurs) |
| Mandats | `mandats_json`, `mandat_numero_reference`, `mandat_numero_source`, `mandat_source_id` |
| Photos | `images_json`, `images_preview_json`, `nb_images`, `photo_url_listing` |
| Propriétaires | `proprietaires_json`, `proprietaires_contacts`, `nb_proprietaires` |
| Notes Hektor | `notes_json`, `nb_notes_hektor`, `note_hektor_principale` |
| Brut | `detail_raw_json`, `annonce_list_raw_json` |

**Conséquence si la règle avait été appliquée** : gel de la diffusion, des affaires, des mandats et
des photos — perte silencieuse et large de remontées Hektor.

**Ce qui reste valide** : les **colonnes** de `app_dossier_current` (§2, listes 🟢/🔵/⚪), lues une par
une dans le code, ainsi que les volets **CONTACT** (§3, 12 colonnes plates, aucun blob) et
**BINAIRES** (§5). Le volet **RECHERCHE** (§4) reste par ailleurs subordonné à C4 puis C3.

**Ce qu'il faut faire avant de réécrire ce volet** : un **inventaire exhaustif des ~130 clés du blob**,
classées APP / HEKTOR / SYSTÈME, avec pour chacune sa source d'écriture (wizard front, scrape
Console, API Hektor) — puis validation par Frédéric. Sans cet inventaire, toute règle sur le blob
est une supposition.

**Leçon de méthode** : ne pas déduire la nature d'une donnée de son nom. Inventorier le contenu
avant d'écrire une règle d'autorité dessus.

---

## 10. ✅ BLOCAGE LEVÉ — volet BLOB réécrit clé par clé (2026-08-17)

Le §9 invalidait la règle « le blob appartient à l'app ». L'inventaire des 130 clés
(`NOTE_AUDIT_MAITRE_2026-08-17.md` §1) permet de la remplacer par une règle **par clé**.
Les 4 arbitrages du §8 sont appliqués.

### 🟢 APP — l'import ne les réécrit plus après le seed

**Textes et descriptif plat**
`texte_principal_titre`, `texte_principal_html`, `corps_listing_html`, `textes_json`, `nb_textes`

**Dimensions et composition**
`surface`, `surface_habitable_detail`, `surface_terrain_detail`, `nb_pieces`, `nb_chambres`,
`etage_detail`, `terrasse_detail`, `garage_box_detail`, `ascenseur_detail`, `copropriete_detail`,
`pieces_json`

**Adresse et géolocalisation**
`adresse_detail`, `adresse_privee_listing`, `ville_privee_detail`, `code_postal_prive_detail`,
`ville_publique_detail`, `ville_publique_listing`, `code_postal_detail`, `code_postal_public_listing`,
`code_postal`, `latitude_detail`, `longitude_detail`, `localite_json`

**Les 9 blobs de groupe** (ils portent ~150 champs du wizard — c'est le gros du volume)
`ag_interieur_json`, `ag_exterieur_json`, `terrain_json`, `equipements_json`,
`diagnostiques_json`, `copropriete_json`, `mandat_infofi_json`, `mandat_mandatdispo_json`,
`organiser_visite_json`

**Statut et mandat** *(arbitrages n°1 et n°3)*
`detail_statut_name`, `mandat_type`, `mandat_date_debut`, `mandat_date_fin`, `mandat_montant`,
`date_enregistrement_annonce`

### 🔵 HEKTOR — doivent continuer à se rafraîchir

**Diffusion** `diffusable`, `valide`, `nb_portails_actifs`, `has_diffusion_error`, `portails_resume`

**Offres** `offre_id`, `offre_state`, `offre_raw_status`, `offre_event_date`, `offre_montant`,
`offre_acquereur_nom`, `offre_acquereur_portable`, `offre_acquereur_email`, `offre_last_proposition_type`

**Compromis** `compromis_id`, `compromis_state`, `compromis_date_start`, `compromis_date_end`,
`date_signature_acte`, `compromis_part_admin`, `compromis_sequestre`, `compromis_acquereurs_resume`,
`prix_publique`, `prix_net_vendeur` ⚠️ *(ces 2 dernières viennent du COMPROMIS — cf. bug §11)*

**Ventes** `vente_id`, `vente_date`, `vente_prix`, `vente_honoraires`, `vente_part_admin`,
`vente_commission_agence`, `vente_acquereurs_resume`, `vente_notaires_resume`, `etat_transaction`

**Mandat (partie Hektor)** `mandats_json`, `mandat_source_id`, `mandat_numero_reference`,
`mandat_numero_source`, `mandat_date_cloture`, `mandat_date_enregistrement`, `mandat_note`,
`mandants_texte`

**Notes Hektor** `notes_json`, `note_hektor_principale`, `nb_notes_hektor`

**Propriétaires** `proprietaires_json`, `proprietaires_resume`, `proprietaires_contacts`, `nb_proprietaires`

**Photos** *(arbitrage n°4 — jusqu'à C9)* `images_json`, `images_preview_json`, `nb_images`, `photo_url_listing`

**Scrapes Console** `console_missing_fields_json/_status/_extracted_at`, `secteur_console_json`,
`diagnostics_contacts_console_json`, `honoraires_detail_console_json`, `location_rendement_console_json`,
`pieces_detail_console_json`, `chauffage_console_json/_status/_extracted_at`,
`dpe_image_url`, `ges_image_url`, `dpe_image_urls_json`

**Référentiel** `agence_nom`, `honoraires_json`, `honoraires_resume`, `zones_json`

### ⚪ SYSTÈME — hors arbitrage
`detail_raw_json`, `annonce_list_raw_json`, `date_maj`, les 7 `price_change_*`,
`responsable_affichage`, `responsable_type`, `internal_status`, `next_action`,
`date_entree_file`, `date_derniere_action`, `motif_blocage`, `is_blocked`, `is_followup_needed`,
`particularites_json`, `app_optimistic_overlay`

### Règle d'implémentation
Le blob est un **TEXT JSON**, pas une colonne : on ne peut pas « retirer une colonne ».
⇒ **Fusion par clé** (option (a)) : à la reconstruction, relire le blob existant et
**réinjecter les clés 🟢** par-dessus la version Hektor, en laissant les 🔵 et ⚪ être écrasées.
C'est l'inverse exact de l'option (b) initialement — et fausse — retenue.

### ⚠️ Trois pièges à respecter
1. `particularites_json` est classé ⚪ **parce que sa saisie est aujourd'hui jetée** par le worker (bug §11). Il devra passer 🟢 une fois le bug corrigé.
2. `detail_raw_json` et `annonce_list_raw_json` **ré-embarquent tout l'état vivant** : ils restent système, jamais figés.
3. Le seed initial reste obligatoire : un champ 🟢 n'est écrit que si la ligne est **nouvelle**.

## 11. Bugs à corriger séparément (chantier parallèle)
- `prix_publique` / `prix_net_vendeur` : remplis depuis le **compromis** mais lus comme prix d'annonce → NULL sans compromis, faux avec. Le vrai prix est dans `mandat_infofi_json`.
- `Particularites` : champ du wizard absent de tous les groupes de push worker → **saisie silencieusement perdue**.
- `images_json` tronqué à 5 alors que `nb_images` compte le total.
