# Les transactions de bout en bout — Hektor, serveur, app

*Analyse du 28/08/2026, après la découverte des appels d'action.
Tout est mesuré. Les deux chiffres qui portent une conclusion ont un témoin.*

---

# I. L'ÉTAT DES LIEUX

## Le parc

```
   offres        11 115        sur  10 033 annonces
   compromis     10 573        sur   9 945 annonces
   ventes         7 605        sur   7 598 annonces
                 -------
                  29 293
```

## La multiplicité est réelle, et elle est normale

| | annonces concernées | dont plusieurs | répartition |
|---|---|---|---|
| **offres** | 10 033 | **934 (9,3 %)** | 2× 806 · 3× 110 · 4× 16 · 5× 2 |
| **compromis** | 9 945 | **578 (5,8 %)** | 2× 534 · 3× 38 · 4× 6 |
| **ventes** | 7 598 | **7 (0,1 %)** | 2× 7 |

C'est le métier : plusieurs acquéreurs se succèdent, une offre est refusée, un compromis
tombe. **Sur les 578 annonces à plusieurs compromis, 561 sont une succession légitime** —
un seul actif à la fois.

## Le mandat ne peut pas servir de clé

```
   offre       mandat absent   98,1 %      <-- inutilisable
   compromis   mandat absent   25,5 %
   vente       mandat absent   11,6 %
```

**Une transaction ne se rattache pas au mandat.** Elle se rattache à l'annonce et à
l'acquéreur — ce que le ledger d'affaires avait déjà établi.

---

# II. LE MODÈLE ACTUEL — mono-transaction, et c'est structurel

`case_dossier_source` ne porte **qu'un** identifiant de chaque :

```
   offre_id      compromis_id      vente_id
```

`app_view_generale` en hérite, `app_dossier_current` aussi, et le front raisonne dessus :

```ts
hasOffreAchatEnCours(item)   // item.offre_id + dernier type de proposition
hasCompromisEnCours(item)    // item.compromis_id + compromis_state
item.vente_id                // la vente : l'existence suffit
```

## ✅ Et cette logique est JUSTE — vérifié avec témoin

J'ai d'abord cru que le serveur retenait la mauvaise transaction : en classant les offres
**par identifiant**, 637 des 934 semblaient garder la plus ancienne.

**C'était faux.** Les identifiants d'offre de Hektor ne sont pas chronologiques. Reclassé
**par date** :

```
   la plus RECENTE                                        909 / 934
   la plus ancienne                                         0
   fiche montrant une offre refusee alors qu'une autre vit  0
```

> **Le serveur retient la bonne, et le front la lit bien.** Il n'y a pas de défaut
> d'affichage. La leçon, une fois de plus : le critère de tri EST la mesure.

## La vraie limite est ailleurs : on n'en voit qu'une

```
   offres au miroir                    11 115
   visibles dans la fiche              10 029   (une par annonce au plus)
   -> INVISIBLES                        1 086
```

Idem pour les compromis *(~628)*. **L'historique des acquéreurs précédents n'est nulle part
dans la fiche.** Ce n'est pas une erreur, c'est le modèle.

---

# III. CE QUE LA DÉCOUVERTE CHANGE

Jusqu'au 28/08, l'app savait **créer** une transaction et rien d'autre. Le relevé sur écran
donne le cycle complet :

| Geste | Mode Hektor | Paramètres |
|---|---|---|
| créer une offre | `annonce-SuiviVente-offre-createOffre` | formulaire, 22 champs |
| **refuser une offre** | `annonce-SuiviVente-updateOffre` | `id`, `type='refus'` |
| **accepter une offre** | `annonce-SuiviVente-updateOffre` | `id`, `type='accepte'` |
| **supprimer une offre** | `deleteOffre` | l'identifiant |
| créer un compromis | `annonce-SuiviVente-compromis-createCompromis` | formulaire |
| **annuler un compromis** | `annonce-SuiviVente-clotureCompromis` | `idComp`, `isCloture` |
| **supprimer un compromis** | `deleteCompromis` | l'identifiant |
| créer une vente | `annonce-SuiviVente-vente-createVente` | formulaire |
| **supprimer une vente** | `ventes-deleteVente` | l'identifiant |

## Trois nuances qui comptent

**① Refuser n'écrase rien.** Une offre est **une conversation** : son historique empile
`proposition` (11 061), `accepte` (9 988), `refus` (1 096). Refuser **ajoute** un événement.
C'est le geste le plus sûr des trois.

**② Une vente ne s'annule pas : elle se SUPPRIME.** Voilà pourquoi `hektor_vente` n'a aucune
colonne d'état — il n'y a rien à marquer. Le projet écrivait *« pas d'annulation possible »* :
c'était à moitié faux.

**③ MODIFIER un compromis reste hors de portée.** `launchPopinCompromis` charge un **module ES**
*(`await import(... Modules/Compromis ...)`, `init`, `goToStep`)*, pas un formulaire postable.
**Annuler est simple ; modifier ne l'est pas.** Ne pas confondre.

---

# IV. LA FONDATION EXISTE DÉJÀ

`app_affaire_ledger` — **29 293 lignes, soit exactement 11 115 + 10 573 + 7 605.**

**Toutes les transactions y sont**, chacune avec :

```
   app_affaire_id          sa propre identite, serie de l'app
   hektor_affaire_id       son identifiant Hektor
   kind                    offre | compromis | vente
   hektor_acquereur_id     l'acquereur -- renseigne a ~99 %
   state, montant, date, date_acte, sequestre
   payload_json            le brut, tel que Hektor l'a dit
   present_in_hektor       delete-never : disparu chez eux, garde chez nous
```

**Acquéreur identifié** : offres 11 104/11 115 · compromis 10 273/10 573 · ventes 7 530/7 605.

Et il est **déjà partiellement exposé** : `app_mandat_register_current.affaires_detail_json`
*(7 779 lignes non vides, clés `compromis`/`dossiers`/`vente`)*, **et le front le lit déjà**
— 7 références dans le code.

> **Le magasin qui manque à la fiche existe déjà, il alimente le registre.**
> Il ne manque que de le brancher sur l'annonce.

---

# V. LE RAPPORT DE SITUATION

## Ce qui marche

- la **sélection** de la transaction courante : la plus récente, 909/934, **vérifié** ;
- le **raisonnement du front** : refus et annulation correctement écartés ;
- la **création** des trois transactions : éprouvée en production ;
- le **ledger** : complet, avec l'acquéreur, delete-never.

## Ce qui manque

| | |
|---|---|
| **les gestes de clôture** | refuser/accepter une offre, annuler un compromis — **spécifiés depuis aujourd'hui**, non codés |
| **l'historique dans la fiche** | 1 086 offres et ~628 compromis invisibles ; l'app ne montre que la courante |
| **la modification** | possible pour l'offre *(formulaire + `idOffre`)*, **hors de portée pour le compromis** |
| **le compte** | l'admin ne peut pas *saisir* une offre ; refuser/accepter semblent permis — **à confirmer** |

## Ce qui n'est PAS un problème, contrairement à ce qu'on aurait pu croire

- l'app ne montre pas la mauvaise transaction ;
- les compromis multiples ne sont pas des doublons *(561/578 sont des successions)* ;
- le worker n'a jamais créé de compromis en double *(0 compromis créé à ce jour)*.

**Le seul doublon réel du parc vient de nous** : annonce 62774, offres 33026 et 33027, même
acquéreur, deux demandes de l'app le 25/08.

---

# VI. COMMENT UTILISER LA DÉCOUVERTE

## Lot 1 — les gestes de clôture *(le plus utile, le moins risqué)*

**Refuser une offre** et **annuler un compromis**, depuis la fiche. Un appel chacun, aucun
formulaire, **tous deux réversibles**. Ils débloquent le cycle complet dans l'app et
suppriment le dernier aller-retour obligatoire vers Hektor.

*Préalable : confirmer le compte à utiliser.*

## Lot 2 — la vente devient éprouvable

`supprimerVente` existe. La branche « Vendu » de C.4, jamais exécutée, **peut donc être
essayée** : une vente d'essai se retire. La suppression reste définitive — le choix de
l'annonce se fait avec Frédéric.

## Lot 3 — la fiche montre l'historique

Brancher `app_affaire_ledger` sur l'annonce, comme il l'est déjà sur le registre. La fiche
affiche **toutes** les offres et compromis, avec leur acquéreur et leur issue, au lieu de la
seule courante. **Aucune donnée à produire** : elles sont déjà là.

## Ce qu'il ne faut PAS faire

- **ne pas rendre le worker « intelligent »** sur le choix de la transaction à modifier :
  l'app ne détient pas l'acquéreur de l'offre existante, elle ne peut pas distinguer
  « je corrige la mienne » de « c'est un autre acheteur ». **L'utilisateur désigne, le worker
  exécute** — c'est ce qui rend les gestes de clôture sûrs, et la reprise implicite dangereuse ;
- **ne pas chercher à modifier un compromis** par le worker : module ES, pas un formulaire.

---

*Sources : miroir `data/hektor.sqlite` et serveur `phase2.sqlite` au 28/08 ·
`ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md` (relevé sur écran) ·
`view_generale.py`, `api.ts` (helpers métier) · `NOTE_FILTRES_TRANSACTIONS_OFFRES_2026-04-02`.*
