# Plan de migration — Rubrique Mandat V3 (cockpit)

Portage de la maquette V3 (design pilotée par l'état + décor détail annonce) sur la rubrique
Mandat du cockpit v2 **en production**, de façon **additive et sécurisée** : rien cassé, juste
déplacé ou ajouté. La rubrique doit devenir **identique à la maquette**, sans risque pour l'app.

Maquette de référence : artifact `mandat-rubrique-v3.html` (8 crans pilotés par `ckStage`).

## Principe de sécurité
- **Flag** `VITE_APP_MANDAT_V3_ENABLED` (OFF par défaut, lu au BUILD par Vite → bascule = variable
  Vercel + rebuild, comme cockpit v2 / contact v2). Flag OFF ⇒ ancienne rubrique **inchangée**.
- **Jumeau non destructif** : dans la branche `activeTab === 'mandat'`,
  `APP_MANDAT_V3_ENABLED ? renderMandatRubriqueV3() : (<ancienne rubrique/>)`. L'ancien rendu
  reste intact et par défaut.
- **Zéro logique dupliquée** : `renderMandatRubriqueV3` est un render local (même scope que la
  rubrique) → accès direct à `ckStage`, `ckDemarches`, `ckMandatTiming`, etc., et réutilise les
  composants existants.
- **CSS scopé** `.fa-ck-mandat-v3` (fichier `fa-mandat-v3.css`), tokens cockpit `--fa-*`, light-only
  (le cockpit n'a pas de dark mode). N'altère jamais `.fa-ck-mandat`.
- **Rollback instantané** : flag OFF.
- Chaque lot : `npm run build` OK + test local flag ON + comparaison maquette + commit isolé
  (staging fichier par fichier).

## Briques existantes réutilisées (à préserver — rien casser)
`ckStage` (18 états) · `HektorMandatNumberForm` (générer n° + garde-fou) · `MandatDocumentEditor`
(éditer mandat/avenant + signataires + PDF) · `MandatSignatureTracker` (suivi signature) ·
`ckDemarches`/`buildMandatActionModel` (demandes validation/baisse/annulation) ·
`DetailAdminPilotPanel` (pilotage validation/diffusion, admin) · `props.mandats`/`mandatDetails`
(historique mandats+avenants) · `PriceChangeHistoryCard` (historique prix) ·
`DiffusionRequestEvent`/`buildRequestGroups` (fils d'échange Pauline).

## Lots
| Lot | Contenu | Statut |
|----|---------|--------|
| 1 | Scaffold : flag + switch + `renderMandatRubriqueV3` + `fa-mandat-v3.css` (invisible tant que OFF) | **FAIT** |
| 2 | Squelette piloté par `ckStage` + cycle de vie 6 crans (Numéro→Diffusé) + rendu conditionnel des blocs | à faire |
| 3 | Sans n° / À éditer / Édité : générer + check complétude (missingFields + champs Hektor) + éditer + UI voie manuscrite | à faire |
| 4 | Envoyé / Signé / Attente : `MandatSignatureTracker` en timeline + demande validation + fils d'échange inline | à faire |
| 5 | Validé / Échu : caractéristiques compact + mandants résumé + avenant + historique prix + historique mandats | à faire |
| 6 | Illustrations + animations + finitions (densité, focus, harmonie tokens cockpit) | à faire |
| 7 (backend, séparé) | Voie manuscrite : marquer doc uploadé `signature.status='signed'` (source manuscrite) → `ckStage` = Signé | à faire |

## États → contenu (cible = maquette)
- **Sans n°** (`man_creer`) : bloc unique « Générer le numéro » (garde-fou registre) + historique permanent.
- **À éditer** (`man_edite`, doc absent) : hero + check complétude + « Éditer le mandat » (un seul bloc).
- **Édité** (`man_edite`, doc `to_send`) : hero 2 col + 2 voies signature (électronique / manuscrite avec dropzone).
- **Envoyé** (`man_signature`) : suivi signature en attente + relance/annuler (pas de demande validation).
- **Signé** (`man_valider`) : signataires repliés + check pré-validation + « Demander la validation ».
- **Attente** (demande envoyée) : fil d'échange Pauline + décision (accepté/à corriger/refusé).
- **Validé** (`dif_*`) : caractéristiques compact + mandants + avenant + historique prix.
- **Échu/clôturé** (`mandat_echu`,`vendu`,`archive`) : lecture seule + regénérer + historique.
- **Historique mandats & avenants** : permanent (visible à chaque étape si données).

## Points d'attention
- Le décor (rail + colonne travail) existe déjà dans le cockpit → **non migré** (contenant).
- Cycle : la voie manuscrite court-circuite `man_signature` (Édité → Signé) — normal.
- 3 autres usages des composants (layout classique, mobile) restent en skin par défaut → pas de régression.
