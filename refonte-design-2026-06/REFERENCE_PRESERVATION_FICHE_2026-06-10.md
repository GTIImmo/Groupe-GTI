# Référence de préservation — Fiche annonce (à NE PAS casser)

Date : 2026-06-10
But : éviter toute perte de fonction ou de comportement visuel lors de la refonte. À vérifier **avant ET après chaque étape de dev**. Complète `PLAN_ERGONOMIQUE_FICHE_ANNONCE_2026-06-10.md` (fonctions/boutons) en se concentrant sur les **comportements dynamiques** (état → couleur / texte / icône / message).

---

## 1. Systèmes « état → visuel » à conserver intégralement

### 1.1 Actions métier (le point sensible)
- Composant `ActionButton` (~5430) + modèle `buildMandatActionModel` (~5593).
- Chaque action porte : **icône par type** (`typeTone`: diffusion / price-drop / cancellation / validation / hektor), **libellé d'état** (`stateLabel`: Ajouter / Corriger / Envoyée / En cours / Modifier…), **couleur par état** (`stateTone`: request / progress / correction / rejected / accepted / diffusion), **message d'aide** (`actionMenuHelperText`).
- Couleurs **scopées** : `.detail-action-console-list .action-menu-state-*` et `.row-actions .action-menu-item` (**99 règles CSS**). ⇒ tout conteneur d'actions doit garder la classe `detail-action-console-list` (ou `row-actions`) pour conserver les couleurs.
- `onClick(event)` attend un événement (`run` appelle `event.stopPropagation()`) → toujours `item.onClick({ stopPropagation(){} })`.
- ✅ Déjà respecté dans la rangée horizontale de l'en-tête.

### 1.2 Pills de statut (`StatusPill` ~25758)
- États colorés : active (vert) · offer (bleu) · compromis (violet) · sold (orange) · closed / archived / history (gris). **36 règles CSS** `status-pill-state-*`.
- En-tête sombre : variantes colorées lisibles ajoutées (active/offer/compromis/sold/closed) — à conserver.

### 1.3 Tonalités timeline / cycles (`tone-*`, `cycleTone`)
- Historique des demandes : `request-cycle-card tone-{n}`, `request-group tone-{cycleTone}` (**96 règles CSS** `tone-*`). Couleur par cycle de demande. À conserver dans l'onglet Historique.

### 1.4 Diffusion / portails
- `PortalStatusMark` (~25780), badges portails `detail-portal-badge` + `portalBrandClass`. États : Actif / En attente / Inactif. Pastilles couleur par portail (LBC, SeLoger, Bien'ici…).
- Validation & diffusable : états `draft` / `observed` / `saved` → **sync pending** (badges « en attente de synchro »). Logique `validationSyncPending`, `hektorSyncPending`, `portalSyncPending`. NE PAS perdre l'indicateur de synchro.

### 1.5 Matterport
- `matterportStateLabel`, `matterportVisibilityLabel` → StatusPill d'état + visibilité par modèle. `MatterportModelActions` (actions par modèle).

### 1.6 Contacts (onglet Mandat & contacts)
- `contactToneFromRoles`, `contactToneLabel`, `contactToneBadgeLabel`, `contactToneIcon`, `contactDuplicateTone`, `contactSeverityLabel` → marqueurs colorés par type de contact (owner/buyer/notary/search…), badges doublon, sévérité.

---

## 2. Rendu conditionnel à préserver (les 3 variantes + rôles)
- `isReadOnlyLightweightDetail` → variantes B/C : masque édition/actions, affiche bandeau « index léger » + Désarchivage/Réintégrer.
- `actionModel.hasMandat` → message « Sans mandat : aucune action… ».
- Rôle `nego` vs `pauline` → actions différentes (`paulineActionLabel`).
- `canManageContacts`, `allowMarkValidation`, `allowMarkDiffusable`, `adminPilotSurface` (none/sidebar/diffusion/both) → panneaux admin/pilote (`DetailAdminPilotPanel`).
- « Prochaine action » contextuelle (`nextActionLabel` / `nextActionDetail`).

---

## 3. Inventaire des fonctions (rappel — voir PLAN_ERGONOMIQUE pour le détail)
En-tête : Fermer · Réaffecter · Statut · Modifier (annonce/contacts/Hektor) · Archiver · Supprimer · Ouvrir Hektor.
Actions métier : Validation · Diffusion · Baisse de prix · Annulation mandat.
Onglets : Synthèse · Commercialisation · Mandat & contacts · Diffusion · Contenu annonce · Historique (+ futur Reporting).
Onglet Contenu (9 sections) : Outils Hektor + Modifier · Photos (`ConsolePhotosPanel`) · Documents (`ConsoleDocumentsPanel`) · Visite virtuelle (Matterport) · Descriptif · **Champs Hektor X/56** (`HektorAnnonceFieldDetailPanel`) · Caractéristiques (+ secteur/chauffage/composition) · **Notes et commentaires**.
Modales : changement statut · suppression · modif annonce · contact/mandant · éditeur mandat · email · agenda · demandes (diffusion/baisse/annulation).

---

## 4. ✅ Checklist de contrôle — à exécuter AVANT et APRÈS chaque étape de dev
1. **Compilation** : 0 erreur console (`preview_console_logs`).
2. **Fonctions** : chaque bouton/action de la §3 toujours présent et atteignable (rien supprimé, juste déplacé).
3. **Couleurs d'état** : les actions gardent icône + `stateLabel` + couleur (`action-menu-state-*`) + message (vérifier via DOM : `.action-menu-item-state`, `.action-menu-item-helper`, classe `action-menu-state-*`).
4. **Pills de statut** : couleurs d'état présentes.
5. **Variantes** : tester une fiche **active** (toutes actions) ET une fiche **index léger** (lecture seule, bandeau désarchivage). Vérifier le bon masquage.
6. **Pas de doublon** : une action = une seule place.
7. **Mobile** : vérifier que la version mobile n'est pas cassée (largeur 390).
8. **Capture avant/après** sur fiche active pour comparaison visuelle.

> Règle d'or : on **déplace/restyle**, on ne **supprime jamais** une fonction ni un comportement d'état. En cas de doute, on garde et on signale.
