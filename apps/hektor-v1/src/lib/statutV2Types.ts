// Modale « Changer le statut » V2 — les TYPES dont la vue a besoin, et rien d'autre.
// ModaleStatutV2.tsx n'importe rien de lib/api (contrôle de parité de test_statut_v2_empreintes.cjs) :
// ses types passent par ici. Aucun code, aucune fonction.
export type {
  AffaireCondition,
  AffairePersonneEcart,
  ConditionCatalogueRow,
  DataScope,
  MandantContactSearchOption,
  RepartitionLigne,
  RepartitionPersonne,
} from './api'
