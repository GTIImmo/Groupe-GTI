# Les gestes de transaction chez Hektor — relevé sur écran, 28/08/2026

*Lu dans le navigateur de Frédéric, sur sa session admin, **sans cliquer sur quoi que ce soit**.
Fiche du bien **62774**. Aucune donnée touchée.*

---

## Pourquoi cette note

L'app sait **lire** les offres refusées et les compromis annulés — la statistique, le filtre et
les badges existent — mais elle ne sait **en poser aucun**. Pour les coder il fallait le nom exact
des appels, et deviner était exclu : **un mauvais nom n'écrit rien et ne dit rien**, exactement le
défaut corrigé le matin même sur la clôture de mandat.

**Deux tentatives ont échoué avant celle-ci**, et c'est instructif :

| | |
|---|---|
| chercher dans nos captures | le JavaScript capturé le 12/06 est celui de l'**en-tête** ; il ne connaît que `createOffre`, `createCompromis`, `addOffre` |
| demander les formulaires au serveur | ✅ fait, en lecture seule, **avec témoin** — et le témoin a montré que **Hektor ignore l'identifiant à l'ouverture** *(réponses identiques octet pour octet)*. Aucune commande d'annulation dans ces formulaires |

> **C'est Frédéric qui a trouvé la bonne méthode** : *« pourquoi ne pas utiliser ta session Hektor
> ouverte avec administrateur sur Chrome ? »*. Les boutons sont **sur l'écran**, et leur `onclick`
> porte le nom de la fonction. Une lecture du DOM, rien de plus.

---

## Ce qui a été relevé, tel quel

```js
offre_bien_change_status('refus',   '33027')   // REFUSER une offre
offre_bien_change_status('accepte', '33027')   // ACCEPTER une offre
delete_offre_suivi('33027')                    // supprimer une offre
launchPopinCompromis(62774)                    // ouvrir le compromis
launchPopinVente(62774)                        // ouvrir la vente
add_offre('62774')                             // ajouter une offre
```

### Les appels derrière ces boutons

| Geste | Mode Hektor | Paramètres |
|---|---|---|
| **refuser une offre** | `annonce-SuiviVente-updateOffre` | `id` *(l'offre)*, `type` = `refus` |
| **accepter une offre** | `annonce-SuiviVente-updateOffre` | `id`, `type` = `accepte` |
| **supprimer une offre** | `deleteOffre` | l'identifiant |
| **clore un compromis** | `annonce-SuiviVente-compromis-popinClotureCompromis` | ouvre une **popin** *(donc un formulaire derrière)* |
| **supprimer un compromis** | `deleteCompromis` | l'identifiant |
| **supprimer une vente** | `ventes-deleteVente` | l'identifiant |

---

## 🔴 UNE CORRECTION AU PROJET — la vente n'est pas ce qu'on croyait

Le projet affirme **trois fois** *« la vente : pas d'annulation possible »* — commits `cfe3483`
et `b8fc48e` du 25/06, et un commentaire dans `App.tsx`. Et j'ai répété cette phrase toute la
soirée du 28/08 pour justifier de ne pas éprouver la branche « Vendu ».

**C'est à moitié faux.** Hektor porte bien :

```js
annuleVente()        ->  mode  ventes-deleteVente
supprimerVente(id)   ->  confirmation "Voulez_vous_vraiment_supprimer_cette_vente"
                         puis  mode  ventes-deleteVente
```

**Une vente ne s'annule pas : elle se SUPPRIME.** C'est pour ça que `hektor_vente` ne porte aucune
colonne d'état — il n'y a rien à marquer, l'enregistrement disparaît. L'observation d'origine
était juste, sa conclusion trop large.

> **Conséquence directe** : la branche « Vendu » de C.4 **peut être éprouvée**. Une vente d'essai
> se retire *(`supprimerVente`)*. Ce n'est pas sans conséquence — la suppression est définitive —
> mais ce n'est plus le point de non-retour qui bloquait l'essai.

---

## Une contrainte trouvée en passant, et elle compte

Sur la même fiche, un bouton porte :

```js
$j.msgbox('Un compte administrateur ne peux pas saisir une offre.')
```

**Un compte administrateur ne peut pas saisir une offre chez Hektor.** À rapprocher du même
phénomène déjà connu sur les documents *(les blocs de signature invisibles en root admin, idUser 4)*
et de l'impersonation utilisée pour l'affectation du négociateur.

➡ **Le worker devra passer par un compte négociateur** pour ces gestes, comme il le fait déjà
ailleurs. À vérifier avant de coder.

---

## Ce que ça débloque

Les **trois gestes** que l'app ne savait pas faire sont désormais spécifiés :

1. **refuser une offre** — et c'est le plus sûr des trois : une offre est **une conversation**
   *(11 061 propositions, 9 988 acceptations, 1 096 refus)*, refuser **ajoute un événement** et
   n'écrase rien ;
2. **accepter une offre** — même mécanisme ;
3. **clore un compromis** — passe par une popin, dont le formulaire reste à relever.

Tous appartiennent à **C.4**, et tous sont des **branches** de `change_hektor_annonce_status`,
pas de nouveaux workers.

---

## Ce qui reste à relever

- le **formulaire de clôture de compromis** *(popin `popinClotureCompromis`)* — ses champs et ses
  motifs, comme on l'a fait pour la clôture de mandat ;
- le **compte** à utiliser : admin refusé pour saisir une offre, à confirmer pour refuser/accepter.

---

*Méthode : `mcp__claude-in-chrome`, lecture du DOM et des fonctions globales sur la fiche 62774.
Aucun clic, aucune écriture. Voir aussi `Console/capture_transaction_actions.js` (lecture serveur)
et ses captures `Console/exports/transaction_actions_*`.*
