# Plan ergonomique — Fiche détail annonce (avant tout design)

Date : 2026-06-10
But : cartographier EXHAUSTIVEMENT la page (boutons, actions, modales, pages liées) pour la réorganiser **sans perdre aucune fonction**, sur le modèle ergonomique de la fiche contact. Code source : `apps/hektor-v1/src/App.tsx`.

---

## 1. Les 3 variantes de fiche (selon l'index)

La fiche change selon l'état du bien (`isLightweightDetail` = archivé, ou statut historique sans cache).

| Variante | Condition (code) | Édition possible ? | Particularité |
|---|---|---|---|
| **A — Fiche complète** | bien actif, `has_local_detail` | ✅ Oui | Toutes les actions (Supprimer, Archiver, Statut, Modifier, console métier) |
| **B — Fiche allégée consultable** | statut historique **non archivé** + cache détail (`isHistoricalLightweightRecord`) | ⚠️ Limité | Consultation riche, actions d'édition réduites |
| **C — Index léger / lecture seule** | **archivé** (`archive='1'`) **ou** historique **sans** cache (`isReadOnlyLightweightDetail`) | ❌ Non | Bandeau « consultable depuis un index léger » + bouton **Demander le désarchivage / Réintégrer** ; actions Supprimer/Archiver/Statut/Modifier **masquées** |

> C'est la condition `!isLightweightDetail` (lignes 16848-16865) qui masque Supprimer/Archiver/Statut en B et C. → exactement vos « 3 types, pas les mêmes boutons ».

---

## 2. Inventaire complet (référence anti-perte de fonction)

### 2.1 En-tête actuel (`detail-overview`, ~16820)
| Bouton | Visible si | Action déclenchée |
|---|---|---|
| **Fermer** (`detail-overview-close`) | toujours | retour à la liste |
| **Réaffecter** (`detail-owner-reassign`) | négociateur présent | modale réaffectation négociateur |
| **Supprimer** (`detail-delete-annonce-button`) | variante A | modale suppression → supprime dans Hektor + nettoie Supabase/local (`deleteAnnonce`, ~10186) |
| **Archiver** (`detail-archive-annonce-button`) | A, si non archivé | archive le bien |
| **Statut** (`detail-status-annonce-button`) | A | modale **« Changer le statut annonce »** (~12714) → envoie le statut à Hektor + resync |
| Identité | toujours | titre, adresse, responsable, **prix**, surface, type, référence, **pills de statut** |

### 2.2 Console d'actions métier (`DetailDossierActionPanel`, ~7804 ; modèle `buildMandatActionModel` ~5593)
- **Validation** (diffusion)
- **Diffusion**
- **Baisse de prix**
- **Annulation mandat** (états : à corriger / envoyée / en traitement)
- **Ouvrir dans Hektor**
- **« Plus d'actions »** → `DetailAdminPilotPanel` (actions admin/pilote)
- **« Prochaine action »** (indication contextuelle)
- Si bien **sans mandat** : message « aucune action de validation, diffusion ou baisse de prix disponible »

### 2.3 Les 6 onglets et leurs contrôles
| Onglet | Contenu / boutons principaux |
|---|---|
| **01 Synthèse** | points clés (prix, surface…), visibilité/diffusion, responsable |
| **02 Commercialisation** | suivi commercial, statuts |
| **03 Mandat & contacts** | **Modifier contacts**, mandants, éditeur de mandat (`MandatDocumentEditor`), n° mandat |
| **04 Diffusion** | passerelles/portails actifs, **Diffusable**, dernières demandes |
| **05 Contenu annonce** | **Modifier l'annonce** (`HektorAnnonceUpdateForm`), composition pièces, DPE/GES, **photos** (`ConsolePhotosPanel`), **documents** (`ConsoleDocumentsPanel`), Matterport (`MatterportModelActions`) |
| **06 Historique** | filtre (Tout / Diffusion / Baisse de prix / Annulation) + timelines des demandes |

### 2.4 Les « Modifier » dispersés (à unifier — votre demande)
| Bouton actuel | Où | Édite quoi |
|---|---|---|
| **Modifier l'annonce** (~17241) | onglet Contenu | champs annonce dans Hektor |
| **Modifier contacts** (~17073) | onglet Mandat & contacts | contacts/mandants |
| **Modifier dans Hektor** (~2551) | formulaires | ouvre l'édition Hektor |

### 2.5 Modales / pages liées ouvertes depuis la fiche
Changement de statut · Suppression · Modif annonce · Formulaire contact/mandant · Éditeur de mandat · Actions Matterport · Panneau photos · Panneau documents · Composeur email · Agenda Google · Demandes (diffusion / baisse de prix / annulation).
Pages liées : Liste annonces (retour) · Fiche contact · Agenda · Mandats.

---

## 3. Modèle ergonomique de référence : la fiche CONTACT (`ContactDetailPopup`, ~24403)

Ce que l'utilisateur apprécie (à reproduire) :
- **Hero** clair + **une seule rangée d'actions** : `Appeler · Email · Créer RDV · Modifier · Supprimer · Fermer` — **un seul Modifier, un seul Supprimer**.
- **Onglets** pour le contenu (statut, emails Gmail, RDV/agenda, biens & historique).
- Densité maîtrisée, hiérarchie nette.

À NE PAS reprendre : ses **couleurs** (thème magenta/teal actuel). → On garde le **patron**, on applique la **nouvelle palette premium**.

---

## 4. Plan de réorganisation ergonomique proposé (fiche annonce)

Principe : **une zone d'en-tête unifiée**, calquée sur la fiche contact, en **3 groupes logiques** clairement séparés, **collante** (reste visible au scroll). Les onglets 01→06 sont conservés.

### Zone d'en-tête (sticky)
1. **Identité** (gauche) : miniature photo · titre · prix · type/surface/réf · **pills de statut colorées** · responsable + lien **Réaffecter**.
2. **Actions métier** (centre — proéminentes, ce que vous faites le plus) : **Validation · Diffusion · Baisse de prix · Annulation** + « Prochaine action ».
3. **Gestion de la fiche** (droite — regroupé, fini l'éparpillement) :
   - **Statut** (changer le statut)
   - **Modifier ▾** → menu unique : *L'annonce · Les contacts · Dans Hektor*
   - **⋯ Plus** → menu : *Archiver · Supprimer · Ouvrir dans Hektor*
   - **✕ Fermer**

### Comportement par variante (no-loss automatique)
- **A** : tout est présent.
- **B** : édition limitée → certains items de « Modifier » / « Plus » se grisent ou disparaissent (comme aujourd'hui).
- **C** : bandeau « Index léger » + **Demander le désarchivage / Réintégrer** ; actions d'édition masquées (comportement actuel conservé).

### Tableau anti-perte (chaque fonction garde sa place)
| Fonction actuelle | Nouvelle place |
|---|---|
| Fermer | En-tête, ✕ à droite |
| Réaffecter | Bloc identité (sous responsable) |
| Supprimer | Menu **⋯ Plus** |
| Archiver | Menu **⋯ Plus** |
| Statut | Bouton **Statut** dédié |
| Validation / Diffusion / Baisse de prix / Annulation | Groupe **Actions métier** |
| Ouvrir dans Hektor | Menu **⋯ Plus** |
| Modifier l'annonce / contacts / dans Hektor | Menu unique **Modifier ▾** |
| Désarchivage / Réintégrer (variante C) | Bandeau dédié |
| Onglets 01→06 | Conservés |
| Photos / Documents / Matterport / Mandat / Email / Agenda | Inchangés (dans leurs onglets) |

### Direction design (après validation du plan)
- Palette premium magenta (charte Pantone), neutres dominants, ombres douces, Inter.
- Actions métier codées couleur ; gestion en boutons sobres ; hiérarchie prix/statut forte.
- Desktop ET mobile (mobile = mêmes groupes empilés, barre d'actions condensée).

---

## 5. Prochaine étape
Valider CE plan (organisation des 3 groupes, menu Modifier unique, menu ⋯ Plus pour Archiver/Supprimer/Ouvrir Hektor, comportement par variante). **Ensuite seulement** : maquette moderne fidèle au plan, puis implémentation dans `App.tsx` sans perte de fonction.
