# Les deux registres, en clair — relations et mandats

> **Écrit le 10/10/2026 à la demande de Frédéric** : *« je veux bien comprendre le registre des
> relations et le registre des mandats […] donne-moi un état de la situation, le mécanisme et
> le principe actuel et à venir. »*
> **Tous les chiffres sont mesurés le 10/10**, après le run de la nuit. Lecture seule.

---

## 0. La seule chose à retenir avant tout le reste

**Pour les relations, il n'y a pas UNE table, il y en a DEUX.** Et c'est là que tout se
brouille, parce qu'elles se ressemblent et ne font pas le même métier.

```
┌─ LA PHOTOCOPIE ─────────────────────┐   ┌─ LE CAHIER ───────────────────────┐
│ app_contact_relation_current        │   │ app_relation                      │
│                                     │   │                                   │
│ 167 669 lignes                      │   │ 132 727 lignes                    │
│ JETEE ET REFAITE chaque nuit        │   │ ECRITE UNE FOIS, JAMAIS EFFACEE   │
│ 6 sources, TOUTES chez Hektor       │   │ chaque ligne a SON numero a nous  │
│                                     │   │                                   │
│ proprietaires ET acquereurs         │   │ les PROPRIETAIRES seulement       │
│                                     │   │ (4 acquereurs sur 132 727)        │
│ -> c'est ce que l'APP AFFICHE       │   │ -> c'est le vrai REGISTRE         │
└─────────────────────────────────────┘   └───────────────────────────────────┘
```

⭐ **La réponse directe à ta question** : *« normalement il doit y avoir les propriétaires et
les acquéreurs »* — **oui, et c'est le cas dans la photocopie, pas encore dans le cahier.**
Les acquéreurs sont **encore entièrement dépendants de Hektor.**

---

## 1. LE REGISTRE DES RELATIONS — qui est lié à quel bien

### 1.1 La photocopie de nuit — ce que l'app affiche aujourd'hui

Chaque nuit, le run **vide la table entièrement et la refait** depuis six fenêtres de Hektor :

```
api_annonce_detail_proprietaires    72 061     la fiche du bien, rubrique proprietaires
sync_annonce_contact_link           60 419     la liste des liens annonce <-> contact
api_list_compromis                  13 279     les compromis
api_list_offres                     11 153     les offres
api_list_ventes                     10 526     les ventes
api_contact_detail_annonces            231     la fiche du contact, rubrique annonces
                                   ───────
                                   167 669
```

Et par rôle :

```
mandant               74 238  ┐
proprietaire          58 473  ┘  132 711 proprietaires du bien
acquereur_compromis   13 279  ┐
acquereur_offre       11 153  ├─  34 958 acquereurs
acquereur_vente       10 526  ┘
```

⚠ **« Mandant » et « propriétaire » sont la MÊME chose chez Hektor** : « propriétaire du bien ».
C'est **nous** qui faisons la différence, et sur un seul critère :

```
le bien a un numero de mandat   ->  on l'appelle MANDANT
le bien n'en a pas              ->  on l'appelle PROPRIETAIRE
```

➡ **C'est le pont entre les deux registres.** Et c'est exactement ce pont qui a cassé la nuit
du 09 au 10 : quand un bien change de numéro de mandat, la personne change de nom de rôle —
et comme le rôle sert à fabriquer l'identifiant du lien, **l'identifiant change aussi.**

### 1.2 Le cahier durable — le vrai registre

Depuis les 02-03/10, il existe une **table durable** à côté de la photocopie :

```
app_relation                              132 727 lignes
   venues du RUN                          132 726    numeros 1 .. 132 727
   posees par l'APP                             1    numero 1 000 008
   marquees « plus chez Hektor »                16    JAMAIS supprimees, juste datees
```

Elle applique les trois règles des registres qui marchent :

```
DEUX DISTRIBUTEURS, DEUX PLAGES   le run prend les numeros sous 1 000 000
                                  l'app prend les siens au-dessus — ils ne se croisent jamais
ON NE RENUMEROTE JAMAIS           une ligne connue garde son numero a vie
ON NE SUPPRIME JAMAIS             un lien que Hektor ne montre plus est MARQUE absent, et date
```

⚠ **Mais elle ne porte que les propriétaires.** Ses sources :

```
api_annonce_detail_proprietaires    72 062
sync_annonce_contact_link           60 423
api_contact_detail_annonces            232
app_seule                               10
                                   ───────
                                   132 727     <- aucun compromis, aucune offre, aucune vente
```

➡ **Les 34 958 acquéreurs n'ont pas encore de ligne durable.** Le jour de la coupure, ils
disparaîtraient. **C'est le trou principal du registre des relations aujourd'hui.**

### 1.3 Le carnet des badges — ne pas le confondre avec les deux autres

```
app_relation_registry                     335 249 lignes
   badges en cours                        167 669
   anciens badges, barres                 167 580
```

Ce n'est **pas** un registre de liens. C'est un **cahier de bord des étiquettes** : chaque lien
porte un badge calculé, et ce cahier note quel badge a été donné à quoi, **sans jamais rien
effacer**. Il sert à ce qu'un lien ne change pas de badge sans raison.

⚠ **Il est purement local. Le cloud n'en a aucune trace.**

### 1.4 Ce que le cloud porte

```
app_relation__sb                   132 728     le cahier : TOUT monte
app_contact_relation_current__sb    85 260     la photocopie : les biens ACTIFS seulement
```

➡ **La photocopie ne monte que pour les biens vivants.** C'est la question Q1, à laquelle tu as
répondu le 30/09 : **tout doit monter**. Ce n'est pas encore fait.

---

## 2. LE REGISTRE DES MANDATS — quel mandat sur quel bien

Beaucoup plus simple, et en meilleur état.

```
app_mandat                                 26 851 lignes
   venues du RUN                           26 851      numeros 1 .. 26 851
   posees par l'APP                             0      <- un seul robinet aujourd'hui
   marquees « plus chez Hektor »                1

   source : le DETAIL de la fiche bien     26 846
            l'annonce                           4
            le miroir                           1

   ouverts                                 26 760
   clos                                        91

   avec un numero de mandat                26 851      100 %
   avec un mandant nomme                   26 716      (135 sans)
```

➡ **C'est déjà un vrai registre** : durable, numéroté par nous, delete-never, et **tout monte
dans le cloud** (26 851 côté serveur, 26 851 côté cloud). La règle *« le registre porte tout,
les écrans filtrent »* est appliquée ici — c'est elle qui sert de modèle aux relations.

⚠ **Mais il n'a qu'UN robinet** : aujourd'hui, un mandat naît toujours chez Hektor. L'app sait
en créer un *(codé au chantier ⑤, point 5c)*, mais **aucun ne l'a encore été** — d'où le `0`.

---

## 3. LE MÉCANISME, AUJOURD'HUI — d'où vient chaque ligne

### Quand un négociateur ajoute un mandant sur un bien

```
1  l'ecran pose une ligne PROVISOIRE                        (chez nous, tout de suite)
2  la RPC ecrit AUSSI la ligne DURABLE                      (depuis le 02-03/10)
3  le worker va creer le lien CHEZ HEKTOR
4  la nuit, le run relit Hektor et ADOPTE la ligne          (il ne la recree pas)
5  le lien existe partout, avec le MEME numero qu'a l'etape 2
```

✅ **Ce chemin fonctionne.** C'est le patron des registres qui marchent.

### Quand un acquéreur est ajouté à un compromis

```
1  la transaction est ecrite durablement dans app_affaire_ledger     ✅
2  ... et c'est tout, cote relations
3  la nuit, le run RECOPIE l'acquereur depuis Hektor dans la photocopie
4  aucune ligne durable n'est posee dans le registre des relations   ❌
```

⚠ **Le jour de la coupure, l'étape 3 n'arrive plus.** Les acquéreurs du registre des relations
s'arrêtent. *(Les transactions elles-mêmes, en revanche, sont bien tenues chez nous.)*

### Quand un bien se vend

```
le bien sort du parc actif  ->  la photocopie ne monte plus ses liens dans le cloud
                            ->  AVANT la table durable, on perdait qui en etait le mandant
                                82 386 fois
```

✅ **C'est ce que la table durable a réparé.** Elle garde les liens des biens vendus.

---

## 4. LE PRINCIPE À VENIR — ce que le chantier prévoit

Le même patron, appliqué quatre fois déjà (annonce, contact, transaction, mandat) :

```
UN NUMERO FRAPPE PAR NOUS       jamais calcule, jamais recalcule
DEUX ROBINETS, UNE TABLE        l'app ecrit au geste · le run ADOPTE et ne cree que l'inconnu
ON NE SUPPRIME JAMAIS           absent_depuis + present_in_hektor
LA SAISIE EN ATTENTE GAGNE      Hektor confirme, il n'ecrase pas
DES SENTINELLES                 qui crient quand ca ne marche plus
```

**Appliqué aux relations, il reste trois choses à faire :**

| | ce qu'il reste | pourquoi |
|---|---|---|
| **1** | **le fait brut, pas le libellé** : stocker « propriétaire du bien », et **dériver** « mandant » à l'affichage | 🔴 **le plus urgent.** Son absence a coûté la nuit du 09→10 : 6 259 liens ont changé de libellé, donc d'identifiant, et le parc entier a basculé |
| **2** | **les acquéreurs se projettent** depuis le registre des affaires, au lieu d'être recopiés de Hektor | 🔴 c'est le trou de la coupure. Mesuré : la projection **gagne 1 407 liens et en perd 177** |
| **3** | **une sentinelle** « lien posé par l'app, jamais adopté après N jours » | 🟡 deux sentinelles existent, celle-là manque |

**Et pour les mandats, une seule :** que l'app puisse en créer un pour de vrai — le code est là,
il attend le premier mandat né chez nous.

---

## 5. Le tableau d'ensemble, pour s'y retrouver

| | **relations — photocopie** | **relations — cahier** | **mandats** |
|---|---|---|---|
| la table | `app_contact_relation_current` | `app_relation` | `app_mandat` |
| combien | 167 669 | 132 727 | 26 851 |
| durable ? | ❌ refaite chaque nuit | ✅ | ✅ |
| numérotée par nous ? | ❌ badge calculé | ✅ | ✅ |
| l'app peut écrire ? | ❌ | ✅ *(1 ligne à ce jour)* | 🟡 codé, jamais utilisé |
| supprime-t-elle ? | ❌ tout, chaque nuit | ✅ jamais | ✅ jamais |
| propriétaires | ✅ 132 711 | ✅ 132 723 | — |
| acquéreurs | ✅ 34 958 | ❌ **4** | — |
| monte dans le cloud | 🟡 biens actifs : 85 260 | ✅ tout : 132 728 | ✅ tout : 26 851 |
| sentinelles | 2 | 2 | ✅ |

---

## 6. Ce que je n'ai pas mesuré

- **Ce que ferait la descente** si la photocopie montait en entier (+82 409 lignes). C'est le
  seul vrai risque de la décision Q1, et il n'est pas chiffré.
- **Pourquoi 1 348 mandants d'affaire** n'ont aucune identité chez nous.
- **Les 177** acquéreurs qu'une projection perdrait, un par un.
- **Les 135 mandats sans mandant nommé.**
- Les autres objets : ce document ne parle que des relations et des mandats.
