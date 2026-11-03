# Audit — le cycle de vie d'une annonce et de son mandat, jusqu'aux portails (03/11/2026)

> **Audit limité** à l'annonce, au mandat, à la validation, à « diffusable », aux passerelles et aux demandes.
> Contacts, recherches, RDV, documents hors mandat : **non mesurés ici**.
> Lecture seule : code (App.tsx, api.ts, worker, backend) + base Supabase. Rien écrit, rien appelé chez Hektor.
> Sert de socle à la refonte du listing Annonces (maquette https://claude.ai/artifact/1ASo32rVwFg5aS1PUJu2k2).

## 1. Le parcours, dans l'ordre (ce que le CODE calcule)

Référence : `ckStage` du cockpit (App.tsx ~31635-31660), libellés `CK_STAGES` (~31663-31740),
barre « Vie du mandat » V3 (~31912-31942 : Numéro · Édité · Envoyé · Signé · Validé).

1. **Sans numéro de mandat** — `numero_mandat` vide → « Créer le mandat ».
2. **Numéro attribué, à éditer** — numéro, pas de document de mandat signable.
3. **Édité, à envoyer** — document Console `metadata_json.signature.status = to_send`.
4. **En signature** — `pending` (ImmoSign) → « Suivre / relancer ».
5. **Signé, à faire valider** — `signed` et `validation_diffusion_state` non validé → démarche vers la Direction.
6. **Validé** — `isValidationApproved()` (valeurs '1','oui','valide','ok'…). C'est un contrôle administratif.
7. **Diffusable** — drapeau « Diffuse » chez Hektor (`diffusable = '1'`). C'est l'autorisation de publier.
8. **En ligne** — au moins une passerelle `broadcasted` (`nb_portails_actifs > 0`, détail dans `app_mandat_broadcasts_current`).
9. **Transaction** — Sous offre (offre vivante, `proposed` comprise), Sous compromis (non annulé), Vendu (`vente_id`).
10. **Terminal** — Clos (statut 6 ou date de clôture), Archivé, et à part : Brouillon (lecture seule), Estimation (autre écran).

Modificateurs qui se superposent : **mandat échu** (`mandat_date_fin` < aujourd'hui), **annulation demandée**,
**avenant** (même escalier que le mandat, validé par le workflow `demande_baisse_prix`).

## 2. Valider ≠ Diffusable ≠ En ligne

- **Validé sans diffusable** : un admin a décoché Diffuse, ou Hektor n'a pas confirmé (`waiting_on_hektor`).
- **Diffusable sans validé** : le geste « Actif » remet `diffusable = 1` sans regarder la validation (worker
  `HEKTOR_STATUS_CONFIG.active`) ; la Console tente Diffuse même si validation = non ; le panneau Pilotage agit séparément.
- **Diffusable sans portail** : « Diffusable non publié ».
- **Portail sans diffusable** : « Publication active non autorisée ».
- Le **site GTI** n'est pas une passerelle : il est déduit de `Actif && diffusable`.
- Accepter une `demande_diffusion` = UN enchaînement : validation = 1 → relecture Hektor → si oui : Diffuse + portails
  par défaut de l'agence (`_accept_validation_first`, hektor_bridge.py ~818-866).

## 3. Les droits (code)

- Rôles : admin, manager, commercial, lecture (`types.ts` 340). « Agent commercial » = commercial avec un périmètre.
- Demander (validation, baisse, annulation) : tout utilisateur actif ayant accès au dossier.
- Valider / cocher diffusable / appliquer les portails : **admin ou manager** (`assert_admin`, supabase_admin.py 216-224,
  appliqué à `/apply`, `/diffusable`, `/validation`, `/persist-state`, `/accept`).
- ⚠ **La règle voulue par Frédéric (03/11)** : *un négociateur peut cocher / décocher les portails dès qu'un admin a
  validé sa demande et coché diffusable, et pour toutes les annonces déjà diffusables.* **Le code ne le permet pas
  aujourd'hui** : `/apply` refuse le commercial (403). → à ouvrir côté backend, sous condition `diffusable = 1`.

## 4. Mesures en base (03/11, annonces vivantes non archivées : Actif + Sous offre + Sous compromis = 705)

Même ordre que le cockpit (transaction d'abord, puis échu, puis l'escalier du mandat) :

- sans numéro de mandat : **159**
- numéro, à éditer (pas de document signable) : **34**
- en signature : **7**
- signé, à faire valider : **21**
- validé, non diffusable : **10**
- diffusable, aucun portail : **16**
- en ligne : **300**
- sous offre : **39** · sous compromis : **93**
- mandat échu (hors transaction) : **26**

Portails (annonces Actif visibles) : paper 278 (+2 err) · etreproprio 278 (+2) · superimmo 276 (+2) ·
leboncoinDirect 257 (+7) · bienicidirect 213.

## 5. Ce que l'audit a trouvé (non corrigé)

1. **Le circuit des demandes dort** : 9 demandes en tout dans `app_diffusion_request`, toutes de mai-juin (essais),
   **1 seule demande de validation** (02/06, encore `pending`). Les validations se font donc ailleurs (chez Hektor).
2. **`has_diffusion_error` vaut 0 partout** alors que 9 annonces actives ont un portail `is_error`.
   ⚠ **CORRIGÉ PAR LE LOT 0 (même jour)** : ce zéro est JUSTE. Hektor dit `exported` pour ces 9 annonces ; les lignes
   `is_error` sont de vieilles erreurs restées chez nous. Voir `PLAN_DEV_LISTING_ANNONCES_LISTE_PUBLICITE_2026-11-03.md`,
   résultats du lot 0. Et la diffusion par portail est **figée au 26/10** (5 pages lues sur 80).
3. **La Console passerelles s'ouvre pour un négociateur** : `saveDiffusionTargets` réussit (règle base ouverte),
   puis `/apply` répond 403 → des cibles changées en base sans être appliquées.
4. **Le menu Action du listing est figé en `role="nego"`** (App.tsx ~27170), même pour un admin.
5. **Le listing ne montre ni la signature, ni « validé », ni « échu » passé J-0, ni la date de clôture** :
   la signature n'existe que dans la fiche (`loadConsoleDocuments`) ; `mandat_date_cloture` n'est pas dans la vue.
6. **12 annonces sous offre ou sous compromis sont encore en ligne** : notre code ne coupe pas les portails au compromis.
7. **Le listing actuel n'affiche que LBC / BI / GTI** : paper, etreproprio, superimmo n'y apparaissent pas.
8. Les id passerelle Hektor de paper / etreproprio / superimmo ne sont pas dans `defaultDiffusionAgencyTargets`
   (superimmo = 21 dans `NOTE_REPRISE_DIFFUSION_API_2026-04-01.md`). Libellé humain de `paper` inconnu.

## 6. Ce qu'il faudrait pour l'afficher dans le listing

- Ajouter à la ligne (vue `app_dossiers_current`) l'**état de signature du mandat courant** (to_send / pending / signed),
  calculé comme `ckSigStatus` — sinon les crans Édité / Envoyé / Signé restent invisibles en liste.
- Ajouter `mandat_date_cloture` à la vue.
- L'état par portail (`app_mandat_broadcasts_current`) se charge pour la page affichée (50 lignes), pas ligne par ligne.
