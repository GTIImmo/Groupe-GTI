# Combien coûte vraiment la bascule de la clé du contact ?

*Mesuré le 21/09/2026, à la demande de Frédéric : « le chiffre de 6 à 9 jours date d'août,
avant l'option B ; mesure-le à nouveau ».*

---

## Le désaccord qu'on cherche à fermer

Une personne porte **deux numéros** qui ne se ressemblent pas et ne se ressembleront jamais :

```
Mme X chez Hektor   hektor_contact_id  439425    <- et c'est LA CLE de la table
Mme X chez nous     app_contact_id     232955    <- la doublure, notre serie
```

La doublure est **complète** : 61 956 contacts, 81 287 relations, 11 368 recherches,
50 152 rapprochements — **zéro trou**. Et **personne ne la lit** : `app_contact_id`
apparaît 63 fois dans `phase2/` (la machinerie qui la remplit) et **0 fois** dans le front,
le worker et le backend.

L'annonce, elle, a fait le chemin complet le 19/08 : `app_dossier_id` **est** sa clé. C'est
pour ça qu'elle ne peut pas fabriquer deux fiches — ce que le contact a fait le 21/09.

---

## La mesure

### Ce qui cite le numéro de Hektor, couche par couche

```
front      234 occurrences   6 fichiers
worker     121                2
serveur    290               24
backend    118               12
sql        275               46
                           -----
                           1 038 occurrences
```

⚠ **Ce chiffre ne mesure pas le travail.** Une bonne part de ces endroits doivent GARDER le
numéro de Hektor — ce sont ceux qui lui parlent, et ils passent déjà par la porte
(`cibleHektorContact` / `hektor_target_id`, option B du 21/09).

### Ce qui coûte vraiment, dans la base

| | |
|---|---|
| tables dont la **clé primaire** porte le numéro de Hektor | **6** |
| index uniques (hors clé) | **0** |
| **clés étrangères** qui le pointent | **0** — *rien n'est protégé, mesure déjà faite le 24/08* |
| **vues** qui le citent | **18** *(dont 4 posées le 21/09)* |
| **fonctions RPC** qui le citent | **46**, dont **22 le prennent en paramètre** |

Les 6 tables : `app_contact_current`, `app_contact_duplicate_member_current`,
`app_contact_override`, `app_contact_pending`, `app_search_count_high_water`,
`app_search_pending`.

### ⭐ LE VRAI CENTRE DE COÛT : les empreintes

`contact_search_key` et `relation_key` ne *contiennent* pas le numéro du contact —
elles sont **calculées dessus** (`stable_hash({"contact_id": ...})`). Changer le numéro
change donc **toutes les clés**, et tout ce qui pend dessous :

```
app_rapprochement_score_history   450 882
app_contact_relation_current       81 287
app_rapprochement                  50 152
app_contact_search_current         11 368
app_rapprochement_search_state      4 176
app_notification                    1 243
+ 6 tables plus petites               113
                                 --------
                                  599 221 lignes, sur 12 tables, SANS aucun filet
```

---

## Ce que la mesure change par rapport au chiffre d'août

**Le coût du CODE s'est effondré, et il est déjà payé.** L'option B a fait passer les
endroits qui parlent à Hektor par une porte unique ; et la **substitution d'identité**
écrite le 21/09 (`identite_app()` dans `build_contacts_layer.py`, alimentée par
`app_contact_identite_app`) **est mécaniquement la bascule** : elle a aujourd'hui **1 ligne**
de correspondance ; remplie avec 356 111, elle bascule le parc entier sans une ligne de code
de plus.

**Le coût des DONNÉES, lui, est entier** : 599 221 lignes accrochées à des empreintes qui
changeraient toutes.

### ⭐⭐ CORRECTION — *Frédéric, 21/09 : « pourquoi ne pas faire les 599 000, c'est risqué ? »*

La question était la bonne. **Les 599 221 lignes ne sont pas 599 221 lignes de travail.**
Décomposées par NATURE, et non par table :

```
505 210   DERIVEES      rapprochements, historique de scores, etat de recherche
                        -> deux RPC les RECALCULENT (app_refresh_rapprochements_*)
                           on ne les migre pas : on les refait

 92 655   REFAITES CHAQUE NUIT   relations (81 287) + recherches (11 368)
                        -> build_contacts_layer les DETRUIT et les REECRIT depuis le
                           miroir a chaque run. Leurs cles se recalculeront toutes
                           seules, par construction. Preuve : l'essai du 21/09 --
                           la recherche du contact d'essai a ete reposee sous la
                           nouvelle cle sans qu'on y touche

  1 356   SAISIES PAR DES HUMAINS    notifications, emails envoyes, propositions,
                        relances, statuts acquereur, demandes de visite
                        -> IRREMPLACABLES. Les SEULES a repointer a la main.
```

**Le travail reel porte donc sur 1 356 lignes** — assez peu pour etre verifiees une par une.

**Et le risque n'est pas le volume.** Il tient a trois choses :

1. **Aucune cle etrangere** (mesure : 0). Une ligne oubliee ne casse rien : elle pointe dans
   le vide, en silence.
2. **La reconstruction nocturne est un DELETE puis un INSERT.** Si le code et les donnees se
   contredisent une seule nuit, tout s'orpheline -- et le run suivant *repare* dans le
   mauvais sens. C'est exactement l'incident du 01/08 : une repose refusee (PGRST102) a
   laisse **1 104 recherches absentes et 13 384 rapprochements orphelins**.
3. Donc le danger est le **COUPLAGE** : le changement de code et celui des donnees doivent
   tomber la meme nuit, pas a un run d'ecart. C'est la regle deja ecrite en tete de la liste
   -- *« un commit pousse APRES le run de 5 h n'est pas eprouve »*.

➡ **Cette correction change la recommandation** : faire la vraie bascule devient PREFERABLE
a l'astuce ci-dessous, puisqu'elle ne coute que 1 356 lignes et qu'elle supprime la dette
pour de bon.

---

## La piste qui éviterait ces 599 221 lignes — *écartée par la correction ci-dessus*

**Une empreinte n'a pas besoin de vouloir dire quelque chose : elle a besoin d'être stable.**
Rien n'oblige à la recalculer sur le nouveau numéro. On peut :

- continuer à hacher sur le numéro de **Hektor** — il ne change jamais pour une fiche venue
  de lui, et pour une fiche née dans l'app on hache sur son numéro à elle, tout aussi stable ;
- ne basculer que la **colonne visible**.

Les 599 221 lignes ne bougeraient alors pas d'un pouce.

⚠ **À VÉRIFIER AVANT DE S'Y FIER**, et ce n'est pas fait : il faut s'assurer qu'aucun code ne
**recompose** l'empreinte à partir de la colonne (au lieu de la lire telle quelle). S'il en
existe un seul, il fabriquerait une clé qui ne correspond à rien — et, comme d'habitude ici,
sans rien signaler.

---

---

## ⚠⚠ AUDIT DES RECHERCHES — *Frédéric : « les recherches ne fonctionnent pas comme le reste »*

Il avait raison, et l'audit a trouvé **le piège qui aurait fait tomber la bascule**.

### Comment une recherche est nommée

```python
key_payload = {"contact_id": contact_id, "index": index, "search": search}
search_key  = stable_hash(key_payload)[:24]
```

**Le contenu ENTIER de la recherche est dans son nom.** Changer un seul critère change la
clé primaire : la ligne est détruite et recréée, emportant tout ce qui pendait dessous.

### Ce qui la sauve aujourd'hui — un mécanisme À PART

`app_search_registry` (77 070 lignes, **jamais vidée**) **FIGE le nom** à la première
rencontre, et le **redonne** à chaque run au lieu du nom recalculé. La clé est donc stable
*en pratique* — mais par un mécanisme extérieur à la table, pas par sa nature.

**Son ancrage est la paire `(hektor_contact_id, search_index)`** — c'est-à-dire **une
POSITION**, pas une identité.

### ⛔ LE PIÈGE POUR LA BASCULE

`assign_search_ids` cherche ses lignes ainsi :

```sql
SELECT ... FROM app_search_registry WHERE hektor_contact_id IN (...)
```

Si l'identité du contact change et que **le registre n'est pas migré dans le même geste**,
la recherche du lendemain ne sera **plus reconnue** : numéro neuf, nom neuf figé,
**les 11 368 clés changent d'un coup** — et les 1 356 lignes humaines, les rapprochements et
les notifications pendent dans le vide. Sans un bruit, puisqu'il n'y a aucune clé étrangère.

➡ **La recherche ne vient donc PAS « après » le contact : son registre doit bouger AVEC lui,
la même nuit.** C'est la correction majeure de cet audit.

### La bonne nouvelle : le registre est déjà prêt

```
lignes                      77 070
avec hektor_contact_id      77 070
avec app_contact_id         77 065      <- la doublure y est deja
nom fige                    77 070      (100 %)
index unique (app_contact_id, search_index)   DEJA POSE
```

**Le changement tient en une ligne** : chercher par `app_contact_id` au lieu de
`hektor_contact_id`. L'index qui le rend possible existe déjà.

### Les 5 lignes sans doublure — ce que c'est

```
76925 / 76926 / 76927   contacts 605093-605095   essais supprimes le 31/08
77069 / 77070           contacts 605450 / 605453  essais supprimes le 21/09
```

Toutes des **résidus d'essais** : le registre **n'oublie jamais**, même quand le contact est
supprimé — c'est voulu (« on ne supprime jamais »), mais il accumule des lignes orphelines.
Aucun contact réel n'est concerné : **77 065 / 77 065**.

---

## Ce qu'il reste à décider *(pour le journal du plan)*

**Quel numéro est LE numéro du contact après la coupure ?** Aujourd'hui le projet ne le dit
nulle part, et `hektor_contact_id` contient déjà un numéro que Hektor n'a jamais donné
(10 000 001) : **le nom de la colonne ment**.

Trois issues :

| | |
|---|---|
| **A. la doublure gagne** *(ce qu'a fait l'annonce)* | cohérent, et le mécanisme existe déjà — reste la question des empreintes |
| **B. on garde `hektor_contact_id` comme identité** et on le renomme | le moins cher, mais la doublure devient un poids mort |
| **C. statu quo** | l'ambiguïté reste, et elle se paiera le jour de la coupure |

Non mesuré : le **backend** (118 occurrences, 12 fichiers) n'a pas été classé endroit par
endroit ; et l'espace acquéreur n'a pas été regardé du tout.
