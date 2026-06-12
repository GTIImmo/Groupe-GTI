# Fiche état ESTIMATION — champs à alimenter (« En construction » en attendant)

> La fiche estimation est en place côté **design/front** (rail + Synthèse + onglets, conforme maquette).
> Les données ci-dessous **ne sont pas câblées** : le front affiche **« En construction »** tant
> qu'elles ne sont pas fournies. Dès qu'un champ est exposé dans la réponse du **détail annonce**
> (backend / sync Hektor), le bloc correspondant l'affiche automatiquement.
>
> Constat vérifié sur EM18604 (134 champs du détail + JSON brut) : aucun montant ni champ
> d'estimation n'est actuellement renvoyé au front (`prix = 0`, `mandat_montant = 0`, pas de
> `ESTIMATION_MONTANT`).

## Légende
- **Source** = d'où doit venir la donnée (champ Hektor connu, ou champ à créer côté détail).
- **Calculé** = dérivé d'autres champs, marche automatiquement dès que ses dépendances arrivent.

---

## 1. Rail — Avis de valeur
| Champ UI | Source à câbler | État |
|---|---|---|
| Valeur retenue | `ESTIMATION_MONTANT` (champ Hektor, **non exposé dans le détail**) | En construction |
| Fourchette basse | `prix_min` / champ estimation bas | En construction |
| Fourchette haute | `prix_max` / champ estimation haut | En construction |
| €/m² | **Calculé** = valeur retenue ÷ surface | OK dès valeur dispo |
| Tag « À confirmer » | statut de l'avis (brouillon / confirmé) | placeholder fixe |

## 2. Rail — Suivi du lead
| Champ UI | Source à câbler | État |
|---|---|---|
| Probabilité de signature (%) | score lead — **champ à créer** | En construction |
| Prochaine action | prochaine action planifiée — **champ à créer** | En construction |
| Relance (date) | date de relance — **champ à créer** | En construction |

## 3. Synthèse — Bandeau « Transformation du lead »
| Champ UI | Source à câbler | État |
|---|---|---|
| Étape courante du pipeline | stade du lead (qualifié / R1 / avis / mandat) | statique (illustratif) |
| R1 — Visite estimation (date) | RDV R1 (agenda) | En construction |
| R2 — Présentation (date/statut) | RDV R2 (agenda) | En construction |

## 4. Synthèse — Montant de l'estimation
| Champ UI | Source à câbler | État |
|---|---|---|
| Valeur retenue | `ESTIMATION_MONTANT` | En construction |
| Fourchette (basse – haute) | `prix_min` / `prix_max` | En construction |
| Prix au m² | **Calculé** = valeur ÷ surface | OK dès valeur dispo |
| Prix souhaité vendeur | champ « prix souhaité » (ou `prix_net_vendeur` ?) | En construction |
| Écart vendeur (%) | **Calculé** = souhaité vs retenue | dépend des 2 ci-dessus |
| Document d'estimation (statut) | statut doc (à générer / généré) | placeholder « À générer » |

## 5. Synthèse — Qualification
| Champ UI | Source à câbler | État |
|---|---|---|
| Origine du lead | champ à créer | En construction |
| Motivation | champ à créer | En construction |
| Échéance projet | champ à créer | En construction |
| Mandat visé (simple / exclusif) | champ à créer | En construction |
| Concurrence (agences, exclusivité, proba) | champs à créer | En construction |

## 6. Onglet « Estimation »
| Champ UI | Source à câbler | État |
|---|---|---|
| Avis de valeur — basse / retenue / haute | idem §1 / §4 | En construction |
| Prix au m² | **Calculé** | OK dès valeur dispo |
| Biens comparables (3 réf. : prix, €/m², distance, statut) | source comparables — **à créer** | En construction |
| Suivi commercial (RDV + relances) | agenda / relances | En construction |

## 7. Onglets profonds — à réorienter « prospect » (étape suivante)
| Onglet | Contenu attendu | État |
|---|---|---|
| **Leads** | flux conversion (génération N° mandat — *existe déjà*) + prospects (*existe*) + diagnostiqueur | réutilise l'existant, à réorienter |
| **Contenu annonce** | brouillon (photos / descriptif à rédiger) | réutilise l'existant |
| **Historique** | journal du lead (chronologie) | réutilise l'historique existant |
| **Reporting** | suivi prospect (4 stats + timeline) | à réorienter |

---

## Déjà câblé (OK, pas « En construction »)
- Identité : titre / **[Sans titre]**, adresse, badge **Estimation** (or), réf., photo.
- Diagnostics (vignettes DPE/GES réelles).
- **Propriétaires (prospects)** : liste réelle des contacts mandants.
- Responsable / **À affecter**.
- €/m² : calculé dès que la valeur retenue est fournie.
