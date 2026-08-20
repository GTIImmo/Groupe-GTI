# Audit — les identifiants Hektor dont l'app dépend encore, et le plan qui en découle

Date : 2026-08-20. **Audit en lecture seule. Aucun code modifié.**
Commandé par Frédéric : « vérifie le worker changement de statut, les idoffre/idcompromis/idvente,
et si l'app utilise les idmandat ».

---

## 1. Le worker « changer le statut » fait bien plus que changer un statut

`handleChangeHektorAnnonceStatus` (`console_job_worker.js:9564`). Cinq cibles, deux natures :

| Cible | Valeur Hektor | Nature |
|---|---|---|
| Actif | 2 | statut simple |
| **Sous offre** | 3 | **crée une TRANSACTION** (`annonce-SuiviVente-offre-createOffre`) |
| **Sous compromis** | 4 | **crée une TRANSACTION** (`...-compromis-createCompromis`) |
| **Vendu** | 5 | **crée une TRANSACTION** (`...-vente-createVente`) + peut clôturer le mandat |
| Mandat clos | 6 | statut simple |

**Trois statuts sur cinq ne sont pas des statuts : ce sont des créations d'affaire.**

Et la transaction transporte des liaisons (`submitHektorTransactionStatus:9310`) :

```
mandat / selectedMandat  -> l'ID MANDAT Hektor
instigateur              -> l'ID NEGOCIATEUR Hektor
acquereurs[]             -> l'ID CONTACT Hektor de l'acquéreur
notairesAcquereur[]      -> l'ID CONTACT Hektor du notaire
+ montant, date, honoraires, séquestre, prix net vendeur
```

Le front les fournit : `selected_mandat`, `buyer_contact_id`, `buyer_notary_id` sont dans la
charge utile du travail.

> ⚠️ **Point de fragilité** : si l'app ne fournit pas `mandat`, le worker le lit **dans le
> formulaire HTML de Hektor** (`htmlInputValue(initHtml, "id_mandat")`). Il dépend alors de ce que
> l'écran Hektor a pré-rempli. Silencieux, et non vérifié.

---

## 2. Oui, Hektor renvoie des identifiants d'affaire — et l'app les stocke

| Identifiant | Où | Volume |
|---|---|---|
| `offre_id` | `app_dossier_current` | **158** *(affaires en cours)* |
| `compromis_id` | idem | **115** |
| `vente_id` | idem | **9** |
| `hektor_affaire_id` | **`app_affaire_ledger`** — clé primaire avec `hektor_annonce_id` + `kind` | **28 980** lignes, 3 types |
| `hektor_acquereur_id` | ledger | **28 614** — soit **99 %** |
| `hektor_mandat_id` | ledger | **14 681** — soit 51 % |

Les colonnes de la fiche portent l'affaire **courante**. Le ledger porte **l'historique complet**,
et sa clé primaire est **entièrement composée d'identifiants Hektor**.

---

## 3. Oui, l'app utilise l'ID mandat de Hektor — mais pas là où on croit

| | |
|---|---|
| Front (`api.ts`) | **0 usage** de `hektor_mandat_id` |
| Registre de mandats | clé = `"annonce:numéro"`, **pas** l'ID Hektor |
| Base locale | `app_dossier.hektor_mandat_id` rempli sur **23 840 / 56 883** (42 %) |
| Ledger d'affaires | 14 681 lignes |
| **Worker** | **9 usages** — transactions et clôture de mandat |

**Conclusion : l'ID mandat n'est pas un identifiant d'affichage, c'est un identifiant d'action.**
L'app le stocke uniquement pour pouvoir agir dans Hektor. Il disparaît naturellement à la coupure.

---

## 4. Ce que ça change pour l'indépendance

| Objet | Clé aujourd'hui | À la coupure |
|---|---|---|
| Annonce | `app_dossier_id` **aligné** (fait le 19/08) | ✅ prêt |
| Dossier d'affaire | `(hektor_annonce_id, kind, hektor_affaire_id)` | ⚠️ **entièrement Hektor** — le ledger devra recevoir une clé propre |
| Mandat | `"annonce:numéro"` | ✅ le numéro reste, même sans Hektor |
| Acquéreur d'une affaire | `hektor_acquereur_id` | ⚠️ = `hektor_contact_id`, gelé à la coupure |
| Négociateur | `idUser` Hektor | ⚠️ sert à l'impersonation, à garder jusqu'au bout |

**Le ledger d'affaires est le seul objet dont l'identité est 100 % Hektor.** Il n'a pas de clé à lui.
À traiter comme les annonces l'ont été : lui donner une clé propre avant la coupure.

---

## 5. Quels workers doivent rester visibles

Critère : **l'utilisateur a besoin du résultat pour continuer son travail, et seul Hektor peut le produire.**

| Worker | Visible ? | Pourquoi |
|---|---|---|
| **`create_hektor_mandat_auto_number`** | **OUI** | le numéro n'existe pas avant que Hektor le rende. Attente structurelle |
| Génération de documents (mandat, avis de valeur, cadastre) | **semi** | l'utilisateur attend le document — mais un avertissement à la fin suffit |
| Transactions (offre / compromis / vente) | **semi** | l'affaire est créée chez Hektor ; l'app peut l'afficher optimiste et confirmer après |
| Tout le reste — 33 types | **NON** | rapatriements, photos, documents, champs, archivage, affectation |

> **Règle à écrire : un worker est invisible par défaut. Il ne devient visible que s'il produit une
> valeur que l'utilisateur attend. En cas d'échec, il prévient toujours — l'utilisateur ET le monitoring.**
