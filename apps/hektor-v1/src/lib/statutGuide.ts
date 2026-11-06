// Modale « Changer le statut », refonte VISUELLE (lot 1, 06/11/2026) — LE GUIDE GTI.
//
// Plan : notice/PLAN_REFONTE_VISUELLE_MODALE_STATUT_2026-11-05.md §2 · sources : audit §4.
//
// Un petit guide pour faire les étapes correctement, dans les mots du métier et de GTI, pas de Hektor.
// ⛔ AUCUNE RÈGLE N'EST INVENTÉE : chaque phrase reprend une règle déjà écrite dans le projet, et sa source
//   est notée à côté. Le guide EXPLIQUE ; il ne bloque rien et ne change aucun geste.
// ⚠ Il ne cite que ce que la modale connaît déjà (plan §1, point 6) : pas de pièces du dossier, pas de noms.

import type { HektorAnnonceStatusTarget } from './api'
import type { CarteParcours, SituationParcours } from './statutParcours'

export type TonGuide = 'info' | 'ok' | 'warn' | 'neutral'

export type Guide = {
  ton: TonGuide
  titre: string
  texte: string
  /** « Comment faire », en trois pas : [ce qu'on fait, la précision] */
  etapes: Array<[string, string]>
}

// Sources (audit §4) :
//  [ETUDE] ETUDE_STATUT_ANNONCE_TRANSACTIONS_MANDAT_2026-09-01.md — offre → compromis → vente ; « la vente est
//          définitive » (App.tsx, rubrique Affaires).
//  [PROTO] protocole du 01/09 — seule la CRÉATION d'une transaction déplace le statut ; après un compromis
//          tombé, le bien reste « Sous compromis » jusqu'à la remise en vente ; la diffusion ne repart pas seule.
//  [DIFF]  AUDIT_MODALE_STATUT_REGLES §3.4 — « Actif » rallume la diffusion (diffusable = 1).
//  [ENG]   bienEngage (08/09) — une offre acceptée ou un compromis ouvert ENGAGE le bien.
//  [FIGE]  offreAccepteeFigeeChezHektor (13/10) et offreVerrouilleeParSonDossier (16/09).
//  [VERR]  compromisVerrouilleParSaVente (23/10) — après la vente, le compromis ne se modifie plus.
//  [DEF]   App.tsx — validité de l'offre et rétractation : 10 jours par défaut.
//  [COND]  catalogue des conditions suspensives — Préemption mairie (0 j), Obtention Crédit (45 j).
//  [REPR]  offreAccepteeAReprendreAuCompromis (26/10) et l'héritage de la vente.
//  [ANNUL] ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md — annuler garde la trace, supprimer efface (erreurs, essais).
//  [CLOS]  modale, rubrique Clos — motif et date gardés chez nous ; « Vendu par l'agence » passe par l'acte (I6).
//  [MAND]  cloturerMandatLocalement (worker) — le mandat est clos chez nous à la date de la vente.
//  [DIR]   demandes à la Direction — baisse de prix (avenant) et annulation de mandat.
//  [USAGE] mesures du 05/11 (audit §3) — 88 % des compromis ont une offre avant ; 5 ventes sur 640 sans rien.

/** Ce que chaque étape veut dire, dans les mots du métier (maquette « version professionnelle »). Remplace, à
 *  l'écran seulement, les descriptions de hektorStatusTargetOptions, qui parlent de la fiche Hektor. */
export const DESCRIPTION_CARTE: Record<HektorAnnonceStatusTarget, string> = {
  active: 'Le bien est en vente.',
  offer: 'Un acquéreur propose un prix.',
  compromise: 'L’avant-contrat est signé.',
  sold: 'L’acte est signé chez le notaire.',
  closed: 'Le mandat s’arrête.',
}

const G = (ton: TonGuide, titre: string, texte: string, etapes: Array<[string, string]>): Guide => ({ ton, titre, texte, etapes })

const ETAPES_CLOS: Array<[string, string]> = [
  ['Vendu par GTI ?', 'Ce n’est pas une clôture : enregistre l’offre, le compromis, puis la vente.'],   // [CLOS]
  ['La date et le motif', 'restent dans notre registre des mandats.'],                                     // [CLOS]
  ['Le mandat se rouvre', 'en remettant le bien en vente.'],                                                // [DIFF]
]

/** Le guide de la carte choisie, dans la situation du bien. */
export function guidePour(statut: HektorAnnonceStatusTarget, s: SituationParcours): Guide {
  const carte: CarteParcours | undefined = s.cartes.find((c) => c.statut === statut)
  const raison = carte?.raison ?? ''
  const n = s.numero

  if (n === 4 && carte?.etat === 'hors') {
    return G('warn', 'Le mandat est échu', raison, [
      ['Vérifie la date de fin', 'sur le mandat signé : toutes ne sont pas fiables.'],                   // audit §10.2
      ['S’il est vraiment échu', 'fais signer un nouveau mandat avant toute transaction.'],
      ['Rien n’est bloqué', 'si tu sais que le mandat court toujours.'],                                  // audit §11
    ])
  }

  if (statut === 'active') {
    if (carte?.etat === 'sans_effet') {
      return G('neutral', 'Le bien est déjà en vente', 'Rien à faire ici pour le statut.', [
        ['Pour baisser le prix', 'fais une demande à la Direction.'],                                   // [DIR]
        ['Pour une offre', 'choisis « Offre ».'],
        ['Pour arrêter', 'choisis « Clos ».'],
      ])
    }
    if (n === 1) {
      return G('warn', 'Un avis de valeur passe en vente par le mandat', raison, [
        ['Fais signer le mandat', 'puis enregistre-le sur le bien.'],
        ['Demande sa validation', 'à la Direction.'],                                                     // [DIR]
        ['La diffusion part', 'à la validation, pas avant.'],
      ])
    }
    if (n === 9) {
      return G('ok', 'L’affaire est tombée : remets le bien en vente', 'Refuser une offre ou annuler un compromis ne change pas le statut. C’est ce geste qui remet le bien en vente.', [   // [PROTO]
        ['Vérifie', 'que les vendeurs veulent toujours vendre.'],
        ['Remets en vente', 'ici, en choisissant « Actif ».'],
        ['Les portails repartent', 'à ce moment-là, pas avant.'],                                         // [DIFF]
      ])
    }
    return G(carte?.etat === 'hors' ? 'warn' : 'info', 'Remettre le bien en vente', raison || 'Le bien repart sur les portails.', [   // [DIFF]
      ['Règle d’abord', 'l’affaire en cours : refuse l’offre ou annule le compromis.'],                     // [PROTO]
      ['Puis remets en vente', 'quand les vendeurs sont prêts.'],
      ['Les portails repartent', 'à ce moment-là, pas avant.'],                                           // [DIFF]
    ])
  }

  if (statut === 'offer') {
    if (carte?.etat === 'lecture' && n === 8) {
      return G('neutral', 'Cette offre ne se modifie plus', 'Son dossier porte un compromis. Pour y revenir, il faudrait d’abord annuler le compromis.', [   // [FIGE]
        ['Une offre acceptée', 'est figée.'],                                                             // [FIGE]
        ['Le compromis', 'vit tant qu’il n’est pas annulé.'],
        ['Aucune nouvelle offre', 'tant que le bien est engagé.'],                                        // [ENG]
      ])
    }
    if (carte?.etat === 'lecture' || carte?.etat === 'hors') {
      return G(carte.etat === 'hors' ? 'warn' : 'neutral', 'Pas d’offre dans cette situation', raison, [
        ['Une affaire', 'suit toujours le même ordre : offre, compromis, vente.'],                        // [ETUDE]
        ['La base refuse', 'une transaction sur un bien vendu, clos ou en estimation.'],                   // etatFermeAuxTransactions
        ['Pour vendre de nouveau', 'il faut d’abord remettre le bien en vente.'],
      ])
    }
    if (n === 7) {
      return G('info', 'Le bien est engagé', 'Une offre est acceptée : plus de nouvelle offre tant que son dossier vit. Refuser une offre concurrente reste possible.', [   // [ENG]
        ['Pour corriger l’offre acceptée', 'refuse-la, corrige-la, puis accepte-la de nouveau.'],       // [FIGE]
        ['Une offre concurrente', 'se choisit dans la liste des affaires, puis se refuse.'],
        ['La suite', 'est le compromis : il reprendra cette offre.'],                                     // [REPR]
      ])
    }
    if (n === 6) {
      return G('ok', 'Une offre attend la réponse des vendeurs', 'Accepte-la ou refuse-la quand ils ont répondu. Une autre offre peut s’ajouter tant qu’aucune n’est acceptée.', [   // [ENG]
        ['Accepter', 'engage le bien : plus de nouvelle offre ensuite.'],                                 // [ENG]
        ['Refuser', 'ne remet pas le bien en vente tout seul.'],                                          // [PROTO]
        ['Une offre acceptée', 'ne se corrige plus directement.'],                                        // [FIGE]
      ])
    }
    return G(s.conseille === 'offer' ? 'ok' : 'info', 'Une offre se saisit une fois signée', 'Plusieurs acheteurs peuvent proposer en même temps. Une seule offre sera acceptée.', [   // [ENG]
      ['Fais signer', 'l’offre écrite et range-la dans les documents.'],
      ['Enregistre-la', 'ici : elle vaut 10 jours par défaut.'],                                          // [DEF]
      ['Accepter', 'est un second geste, quand les vendeurs ont répondu.'],
    ])
  }

  if (statut === 'compromise') {
    if (carte?.etat === 'lecture' || carte?.etat === 'hors') {
      return G(carte.etat === 'hors' ? 'warn' : 'neutral', 'Pas de compromis dans cette situation', raison, [
        ['Une affaire', 'suit toujours le même ordre : offre, compromis, vente.'],                        // [ETUDE]
        ['Un seul compromis', 'à la fois sur un bien.'],
        ['Pour vendre de nouveau', 'il faut d’abord remettre le bien en vente.'],
      ])
    }
    if (n === 8) {
      return G('info', 'Le compromis est en cours', 'Mets-le à jour au fil de l’eau. S’il ne se fait pas, annule-le : la trace reste. Pour l’acte, choisis « Vendu ».', [   // [ANNUL]
        ['Les conditions suspensives', 'se suivent jusqu’à l’acte : crédit, préemption.'],                // [COND]
        ['Annuler', 'ne remet pas le bien en vente tout seul.'],                                          // [PROTO]
        ['« Supprimer »', 'ne sert qu’aux erreurs de saisie.'],                                           // [ANNUL]
      ])
    }
    if (n === 7) {
      return G('ok', 'Le compromis reprend l’offre acceptée', 'Le montant et les acquéreurs de l’offre sont repris. Vérifie-les, puis ajoute les conditions.', [   // [REPR]
        ['Les conditions suspensives', 'crédit (45 jours), préemption : elles se suivront jusqu’à l’acte.'],   // [COND]
        ['La rétractation', 'vaut 10 jours par défaut.'],                                                 // [DEF]
        ['Un seul compromis', 'à la fois sur un bien.'],
      ])
    }
    if (n === 9) {
      return G('info', 'Un nouveau compromis', 'L’affaire précédente est tombée : ce compromis ouvrira un nouveau dossier.', [   // dossiersOuvertsDuBien
        ['Désigne l’acquéreur', 'il sera qualifié « acquéreur » s’il ne l’est pas encore.'],
        ['Ajoute les conditions', 'crédit, préemption : elles se suivront jusqu’à l’acte.'],                // [COND]
        ['Un seul compromis', 'à la fois sur un bien.'],
      ])
    }
    if (n === 6) {
      return G('info', 'Accepte d’abord l’offre', 'Le compromis se rattache à l’offre acceptée de son dossier. Sans elle, il partirait seul.', [   // [REPR]
        ['Accepte l’offre', 'dans l’onglet « Offre ».'],
        ['Puis reviens ici', 'le compromis la reprendra.'],                                               // [REPR]
        ['Un seul compromis', 'à la fois sur un bien.'],
      ])
    }
    return G('info', 'Un compromis sans offre avant', 'C’est possible, mais rare : 88 % des compromis ont une offre avant.', [   // [USAGE]
      ['Désigne l’acquéreur', 'il sera qualifié « acquéreur » s’il ne l’est pas encore.'],
      ['Ajoute les conditions', 'crédit, préemption : elles se suivront jusqu’à l’acte.'],                // [COND]
      ['Un seul compromis', 'à la fois sur un bien.'],
    ])
  }

  if (statut === 'sold') {
    if (n === 8) {
      return G('ok', 'La vente reprend le compromis', 'Vérifie la date de l’acte et le prix. Une vente est définitive : elle ne s’annule pas.', [   // [REPR] [ETUDE]
        ['L’acte est signé', 'chez le notaire : range sa copie dans les documents.'],
        ['Le mandat', 'est clos chez nous à la date de l’acte.'],                                         // [MAND]
        ['Le bien reste', 'dans tes biens, au statut Vendu.'],
      ])
    }
    if (n === 10) {
      return G('neutral', 'La vente est enregistrée', 'Une vente est définitive. La corriger reste possible ; la supprimer ne sert qu’aux erreurs de saisie.', [   // [ETUDE] [ANNUL]
        ['Après la vente', 'le compromis ne se modifie plus.'],                                           // [VERR]
        ['Le mandat', 'est clos chez nous à la date de la vente.'],                                       // [MAND]
        ['Le bien reste', 'dans tes biens, au statut Vendu.'],
      ])
    }
    if (carte?.etat === 'lecture') {
      return G('neutral', 'Pas de vente dans cette situation', raison, [
        ['Une affaire', 'suit toujours le même ordre : offre, compromis, vente.'],                        // [ETUDE]
        ['La base refuse', 'une transaction sur un bien vendu, clos ou en estimation.'],                   // etatFermeAuxTransactions
        ['Pour vendre de nouveau', 'il faut d’abord remettre le bien en vente.'],
      ])
    }
    return G('warn', 'Une vente sans compromis est rare', 'Vérifie qu’il ne s’agit pas plutôt d’une offre ou d’un compromis : 5 ventes sur 640 depuis 2025 n’avaient rien avant.', [   // [USAGE]   // [USAGE]
      ['Le prix', 'est celui de l’acte.'],
      ['Le mandat', 'sera clos chez nous à cette date.'],                                                 // [MAND]
      ['Une vente', 'est définitive.'],                                                                   // [ETUDE]
    ])
  }

  // closed
  if (carte?.etat === 'sans_effet') {
    return G('neutral', 'Le mandat est déjà clos', 'Pour le rouvrir, remets le bien en vente.', ETAPES_CLOS)   // [DIFF]
  }
  if (n === 10) {
    return G('neutral', 'Le mandat est clos par la vente', raison, ETAPES_CLOS)                        // [MAND]
  }
  if (carte?.etat === 'hors') {
    return G('warn', 'Une affaire est en cours sur ce bien', raison, ETAPES_CLOS)
  }
  return G('info', 'Clore le mandat', raison || 'Le bien quitte les portails. La date et le motif restent chez nous.', ETAPES_CLOS)   // [CLOS]
}
