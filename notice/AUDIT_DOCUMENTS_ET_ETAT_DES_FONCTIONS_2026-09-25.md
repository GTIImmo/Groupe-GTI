# Comment fonctionnent les documents — et ce qui marche ailleurs dans le projet

*25/09/2026, demandé par Frédéric. Établi par **le code et les deux bases**, pas par les
notes — la session « Documents extraction » (07/09) n'a laissé aucun commit, c'était une
session d'exploration.*

---

# ① LES DOCUMENTS — le fonctionnement, en cinq étapes

### 1. Hektor ne donne pas d'API pour ses documents : on lit ses pages

Le worker interroge **trois adresses de la console Hektor**, pas une API :

```
mode=chargeannonce_Documents        les pieces attachees a l'annonce
mode=UploadedDocument_list  privee  les documents prives
mode=UploadedDocument_list  partage les documents partages
```

Il y **repère les liens** par le marqueur `force_transfert(...)` présent dans le HTML.

⚠ **Et c'est là qu'est le trou connu** *(trouvé le 07/09)* : les blocs **ImmoSign** et
**« Mes documents »** n'ont **pas** de `force_transfert`. **Ils ne sont donc jamais indexés.**
S'y ajoute un second effet : les boutons de signature sont **masqués quand on est connecté en
administrateur** — ce qui ferme le suivi de signature. **Ce n'est pas une panne, c'est le
contexte de connexion.**

### 2. L'index : `app_console_document`

Chaque document repéré devient une **ligne** : l'annonce, son identifiant Hektor, le nom, le
type, l'URL, la taille, l'empreinte. **La ligne n'est pas le fichier.**

### 3. Le fichier descend — sur le serveur d'abord

`writeLocalArchiveFile(...)` écrit **systématiquement** dans
`C:\Hektor\HektorConsoleDocuments\annonces\{annonce}\documents\`. **Supabase ne reçoit une
copie que si on la demande** *(le drapeau `cloud`)*. C'est déjà la règle que tu proposais pour
les photos.

### 4. L'état de chaque document

| état | ce que ça veut dire | aujourd'hui |
|---|---|---|
| `local_only` | sur ton serveur seulement | **22 493 documents · 28 Go** |
| `cloud_available` | aussi dans Supabase | **22 023 documents · 32 Go** |
| **total** | | **44 516 · 60 Go · 4 798 annonces** |

Sur le disque : **45 006 fichiers, 60,6 Go**. Dans Supabase : **22 925 fichiers, 33 Go**.

### 5. Comment l'app affiche un document

Le front demande à Supabase un **lien signé temporaire**. ⚠ **Donc seuls les 22 023
`cloud_available` sont visibles dans l'app.** Les 22 493 `local_only` sont **sauvegardés mais
invisibles** — ton serveur n'est joignable ni par le front (Vercel) ni par Supabase.
**C'est exactement le problème qu'on vient de voir pour les photos.**

## Où ça s'est arrêté

| | |
|---|---|
| dernier `sync_console_documents` | **23/08/2026 à 16 h 09** — il y a **33 jours** |
| pourquoi | **l'IP a été bannie le 20/08** par le rattrapage : un frein a été posé (`7143a1a`), la synchronisation n'a jamais repris |
| travaux en erreur | **0** — rien n'est bloqué, c'est **arrêté**, pas cassé |

**Conséquence, en clair : depuis le 23 août, un document ajouté ou signé chez Hektor n'arrive
plus dans l'app.**

**La reprise est déjà conçue** *(mémoire `sync-documents-empreinte-et-suivi-signature`)* :
- une **empreinte de contenu** pour savoir quoi retélécharger — Hektor ne date pas ses
  sous-éléments, donc on ne peut pas se fier aux dates ;
- la règle **« procédure en cours »** pour le suivi de signature : **242 annonces** à surveiller
  au lieu de 2 104 ;
- le tout **derrière le frein anti-bannissement**.

⚠ **Règle absolue, payée le 20/08** : ne jamais rejouer les annonces déjà en échec, cadence
lente, **et un 403 arrête tout**.

## Ce que l'app sait déjà faire des documents

| geste | état |
|---|---|
| lire / indexer | ✅ mais **arrêté depuis le 23/08** |
| télécharger sur le serveur | ✅ systématique |
| copier dans Supabase | ✅ sur demande |
| **envoyer un document à Hektor** | ✅ `upload_document_to_hektor` — 102 fois |
| **supprimer un document chez Hektor** | ✅ `delete_document_from_hektor` — 39 fois |
| générer un PDF *(estimation, cadastre, mandat)* | ✅ |
| suivre une signature | ⛔ **fermé** par le contexte de connexion |

➡ **Pour les documents, supprimer existe. Pour les photos, non.** C'est la différence entre
les deux chantiers.

---

# ② LE RESTE DU PLAN — est-ce que ça marche ?

**Oui, et la preuve est mesurable** : sur les **36 types de travaux** que l'app envoie à
Hektor, **aucun n'a de travail en erreur ou en attente**. 55 509 travaux, tous terminés.

| famille | gestes qui marchent | dernier usage réel |
|---|---|---|
| **annonce** | créer *(brouillon)*, modifier *(182 champs)*, changer le statut, archiver, restaurer, supprimer, affecter un négociateur | 24/09 |
| **contact** | créer, modifier, supprimer, mandant, rattacher | 21/09 |
| **recherche acquéreur** | ajouter, modifier, supprimer | 18/09 |
| **transaction** | offre, compromis, vente : créer, modifier, annuler, supprimer | 18/09 |
| **documents** | envoyer, supprimer, générer des PDF | 26/08 |
| **rafraîchissement** | fiche annonce, fiche contact | 24/09 |

⚠ **« 0 en erreur » ne veut pas dire « tout est prouvé ».** Un geste jamais lancé ne dit rien :
`relance_signature` et `cancel_signature_procedure` n'ont **servi qu'une fois, fin juin**.

## Les trois exceptions que tu cites — confirmées

| | état |
|---|---|
| **numéro de mandat** | `create_hektor_mandat_auto_number` existe *(3 usages)*, mais la **numérotation appartient à Hektor** — c'est `L9`, à finir **avant** la coupure car il se remplit depuis le miroir |
| **signature électronique** | **ImmoSign appartient à l'abonnement Hektor.** À la coupure, la signature **s'arrête**. Il faut **ton propre contrat** *(`A.2`, à zéro)*. Et l'app ne sait pas *lancer* une signature : le bouton ouvre Hektor |
| **passerelles / portails** | **`A.1`, à zéro** : sortie en nom propre + reprise des ~350 annonces en ligne |

## Ce qui ne marche pas, en dehors de ces trois

1. **`D.0` — les documents, arrêtés depuis 33 jours** *(ci-dessus)*. **Le plus urgent.**
2. **Les photos** — ajouter oui ; supprimer, réordonner, choisir la principale : **rien**, et
   les commandes Hektor correspondantes **ne sont pas connues**. ➡ `AUDIT_PHOTOS_2026-09-25.md`
3. **Les fichiers ne survivent pas à la coupure** : 22 493 documents et 1 355 photos ne sont
   que sur ton serveur, **invisibles depuis l'app** ; et **13 437 vignettes d'annonces pointent
   encore vers Hektor**.
4. **~270 recherches** créées chez Hektor restent invisibles *(`0.3`, arrêté le 23/08 aussi)*.
5. **Une annonce**, 63122, n'arrive pas jusqu'à l'app *(son détail n'est jamais lu)*.
