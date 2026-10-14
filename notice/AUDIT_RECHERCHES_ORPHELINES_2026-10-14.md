# AUDIT — LA FAMILLE « RECHERCHES » · 3 alertes · 14/10/2026

*« NON REFAIT UN AUDIT PLUS POUSSÉ IL Y A UNE RAISON PRÉCISE À CET ÉCART CHERCHE »* — Frédéric.
**Il avait raison. La voici, de bout en bout.** Lecture seule, rien n'a été touché.

---

## LA RAISON PRÉCISE — une chaîne de 7 maillons

```
1.  HEKTOR ARCHIVE une recherche                         archive = 1
2.  le build recopie                                     is_active = int(not archive) = 0
         phase2/contacts/build_contacts_layer.py l. 1475
3.  ce contact n'a alors PLUS AUCUNE recherche active,
    et pas d'annonce active non plus
4.  -> IL PERD SON ELIGIBILITE                           supabase_sync_eligible = 0
         l. 1750-1754 : eligible SI (annonce active) OU (recherche active)
5.  le push ne charge que les recherches
    DES CONTACTS ELIGIBLES                               push_contacts_to_supabase.py l. 639-644
6.  -> et « ce qui n'est pas dans `loaded` est declare
    DISPARU, DONC SUPPRIME chez Supabase »                l. 670-676, commentaire du projet
7.  -> tout ce qui pointait vers cette recherche
    reste accroche DANS LE VIDE                           4 022 lignes
```

### La preuve en une égalité

| | |
|---|---|
| recherches des contacts **éligibles**, en local | **11 453** |
| recherches **dans Supabase** | **11 453** |

**À l'unité près.** Le filtre du push n'est donc pas « actives » *(il n'y en a que 4 250)* : c'est
bien **« les recherches des contacts éligibles »**.

### Et la contradiction qui l'a révélée

| les 35 contacts | `supabase_sync_eligible` |
|---|---|
| dans **notre base locale** *(celle qui décide du push)* | **0** |
| dans **Supabase** *(resté sur l'ancienne valeur)* | **vrai** |

Le contact n'est pas supprimé de Supabase — **il n'est simplement plus mis à jour**. Seules ses
**recherches** sont retirées.

---

## Les mesures, dans l'ordre où elles sont tombées

| | mesure | ce que ça a éliminé |
|---|---|---|
| 1 | **4 022 lignes = 35 recherches** *(l'historique des scores en traîne 3 791 à lui seul)* | le chiffre mesurait un **volume**, pas une gravité |
| 2 | les lignes orphelines ont été **calculées en août-septembre** | ce ne sont pas elles qui sont nées hier |
| 3 | journal des doublures : **11 477 → 11 453** la nuit du 13 au 14, et « Hektor seul » **+28** | **elles existent toujours chez Hektor** |
| 4 | les 35 contacts sont **présents et éligibles dans Supabase** | ⛔ la piste « contact sorti du périmètre » |
| 5 | leurs **36 recherches sont bien dans notre base locale** | ⛔ la piste « le build ne les fabrique plus » → **le défaut est au push** |
| 6 | ces 36 ont **`archive = 1`, `is_active = 0`** | ✅ elles ont été **archivées chez Hektor** |
| 7 | le run passe bien `-IncludeArchivedContactSearches` | ⛔ la piste « le push filtre sur actif » |
| 8 | **recherches des contacts éligibles = 11 453 = Supabase** | ✅ **le filtre est l'ÉLIGIBILITÉ DU CONTACT** |
| 9 | les 35 sont **`eligible = 0` en local** mais **vrai dans Supabase** | ✅ **ils ont perdu leur éligibilité cette nuit** |

---

## ⭐ CE N'EST PAS UNE PERTE DE DONNÉES — c'est un défaut de MÉNAGE

Le cycle est **normal et voulu** : une recherche archivée chez Hektor sort du périmètre, et un
contact sans rien d'actif cesse d'être synchronisé. **Rien n'est perdu chez Hektor.**

⚠ **Le défaut est au maillon 7** : on retire la recherche, **mais on laisse tout ce qui s'y
accrochait**. Et le volume est brutal — **une seule recherche archivée laisse jusqu'à 238 lignes
d'historique orphelines**.

Le projet le savait à moitié : le code dit *« la cause a été corrigée dans le worker (il lit les
clés AVANT de supprimer les recherches) et 146 orphelins ont été purgés »*. ➡ **Ce correctif ne
couvre que le chemin du worker. Il ne couvre pas l'archivage chez Hektor**, qui passe par le run.

---

## ⚠ DEUX AGGRAVANTS, trouvés en chemin

### A. La clé d'une recherche est un **hash de son contenu**

```python
key_payload = {"contact_id": contact_id, "index": index, "search": search}
search_key   = stable_hash(key_payload)[:24]        # l. 1476-1477
```

➡ **Si un seul critère change — un prix, une ville — la clé change.** L'ancienne disparaît, une
neuve apparaît, et **tout l'historique de rapprochement se détache de la même façon**.
*Non mesuré aujourd'hui, mais c'est le même effet par une autre porte.*

### B. Et ce que Frédéric a signalé pendant l'audit

> *« les modifications de recherche ne sont pas envoyées à Hektor »*

➡ Une recherche **affinée dans l'app** n'est pas connue de Hektor. Si Hektor l'archive ensuite,
**le maillon 1 se déclenche sur une recherche que l'app croyait à elle** — et l'affinage sort du
périmètre sans que personne ne soit prévenu. **À vérifier : c'est la suite logique de cet audit.**

---

## Ce qu'il reste à décider

| | | |
|---|---|---|
| **1** ⭐ | **nettoyer derrière une recherche qui sort du périmètre** — étendre au run ce que le worker fait déjà | c'est **la** correction de fond |
| **2** | vérifier l'aggravant **B** *(l'affinage de l'app face à un archivage Hektor)* | ~1 h |
| **3** | décider du sort des **4 022** lignes actuelles | ⛔ **pas avant 1** : ce sont des historiques de rapprochement |
| **4** | la clé-hash *(aggravant A)* | gros sujet, à part |

⛔ **Rien n'est décidé, rien n'a été touché, rien n'a été purgé.**
