# La chaîne des mandats — enquête du 25/08/2026

Demandée par Frédéric : *« tu dois faire une analyse plus approfondie… tu dois vérifier
l'app, Supabase, le serveur, le miroir Hektor, les runs pour bien comprendre car tu te
trompes. »*

Il avait raison sur les deux points qu'il contestait. Cette note garde ce que la
vérification a établi, pour ne pas le refaire.

---

## 1. La chaîne, vérifiée bout à bout

```
   run Hektor (list_mandats)  ->  h.hektor_mandat        24 125 lignes
   detail de chaque annonce   ->  mandats_json
                                     |
                                     v
   serveur : app_view_generale  (1 ligne par annonce, LE mandat courant)
             app_mandat_register_current  (1 ligne par annonce+numero)  23 816
                                     |
                                     v
   Supabase  ->  front (registre des mandats, fiche annonce)
```

**`mandat_source_id` EST `hektor_mandat_id`.** Vérifié : **23 814 / 23 814 (100 %)**, et le
numéro concorde aussi à 100 %.

> ⚠ **Ma première mesure disait « 0 correspondance ».** Elle était fausse : le registre stocke
> `hektor_annonce_id` en **entier**, le miroir en **texte** — la jointure comparait `10003` à
> `'10003'`. Même classe d'erreur que la comparaison des prix le matin même. **Toujours
> convertir avant de joindre deux supports.**

---

## 2. Le registre ne se nourrit PAS de `hektor_mandat` — et c'est délibéré

La raison est écrite dans `phase2/pipeline/view_generale.py` :

> *« la table `hektor_mandat` dépend d'un rapatriement global séparé (`list_mandats`) qui peut
> cesser de tourner **sans rien signaler** — c'est arrivé le 30/03/2026, et le LEFT JOIN
> échouait alors **EN SILENCE**, laissant les dates à NULL sur 147 dossiers. Le détail, lui,
> arrive avec chaque annonce : il est toujours là. »*

**C'est une défiance envers la source, pas un oubli.** Toute comparaison entre `hektor_mandat`
et le registre part donc d'un malentendu si on l'ignore.

### Les 311 mandats du miroir absents du registre

| | | |
|---|---|---|
| **94** | sans numéro d'annonce | orphelins côté Hektor |
| **146** | même annonce, **même numéro**, autre identifiant | **déduplication voulue** |
| **71** | sur 62 annonces réellement absentes | **0,26 %** — anomalie résiduelle, non expliquée |

Les 62 : 50 archivées « Actif », 8 vendues, 3 closes, 1 sous compromis. **Aucune perte de
donnée** — la vue générale les porte toutes.

---

## 3. Deux formes de multiplicité, à ne pas confondre

### ① Même numéro, plusieurs versions — **112 annonces**

```
   annonce 1972, numero 17925 :
      source_id 555     is_current = true
      source_id 66487   is_current = false
      source_id 32312   is_current = false
```

C'est **le même mandat amendé**. Une seule ligne au registre, les autres dans
`register_history_json`, avec un `is_current` explicite. **Aucune ambiguïté.**

### ② Numéros différents — **24 annonces**

Deux mandats réellement distincts → **deux lignes** au registre.

---

## 4. `register_source_kind` décrit l'ANNONCE, pas le mandat

```python
"register_source_kind": "historique" if status in {"Vendu","Clos"} or not detail_available
                        else "actif"
```

D'où **23 091 « historique » contre 725 « actif »** : ce sont les annonces vendues ou closes.
**Ce champ ne peut donc pas départager deux mandats d'une même annonce** — sur les 24, les deux
lignes portent « actif », parce que l'annonce est active.

*(Je l'avais d'abord lu comme un statut de mandat. C'est faux.)*

---

## 5. Et la fiche annonce, elle, tranche — **24 fois sur 24**

```
   fiche annonce  ->  numero 18787  (id 553)     <== LE COURANT
   registre       ->  numero 1      id 9887   fin 2023-03-14  clôturé le 30/07/2026
   registre       ->  numero 18787  id 553    fin 2027-07-27  non clôturé
```

`app_view_generale` prend le mandat que **l'annonce elle-même désigne** (`src.mandat_id` ou
`src.no_mandat`). Sur les 24 annonces à deux mandats, elle pointe **toujours l'un des deux**,
et c'est le bon.

> ❗ **J'avais annoncé « 10 annonces où le négociateur devra trancher ». C'est faux.** Ma mesure
> regardait les dates du registre en ignorant que la fiche désigne déjà le courant. **Il n'y a
> pas de problème de choix aujourd'hui.**

---

## 6. Un identifiant de mandat ne vaut RIEN seul

**342 identifiants sont partagés entre annonces différentes** — Hektor réutilise les numéros bas :

```
   id 10  ->  annonce 29     numero 16564
          ->  annonce 61650  numero 18427
```

En revanche, **jamais deux fois le même identifiant sur la même annonce : 0 cas.**

> **Règle** : toujours interroger par le **couple (annonce, numéro)**, jamais par l'identifiant
> seul. C'est ce que fait `resoudreMandatAClore` (repli de clôture), et c'est pourquoi elle aboutit à
> **100 % sur les 23 816 couples**.
>
> ⚠ **Corrigé le 25/08 au soir.** Cette même résolution avait été posée sur les **transactions**
> par C.5 le matin : **annulée le jour même**. Sur le formulaire d'offre, Hektor n'attend pas un
> numéro mais un couple **`<id>-<FAMILLE>`** — `648-PROTEXA` ou `9887-HEKTOR` — et une valeur
> amputée est **ignorée sans erreur** : l'offre part alors sans mandat *(constaté sur l'offre
> 33026)*. Le worker **recopie de nouveau la valeur de Hektor telle quelle**.

---

## 7. Ce qui reste à faire — rattaché à C.4

| | |
|---|---|
| **a** | Quand le négociateur changera un statut **depuis l'app**, l'app doit **transmettre le numéro de mandat de la fiche** — pas laisser le worker chercher. La résolution existe déjà côté worker ; il suffit que le formulaire l'envoie |
| **b** | ⚠ **Si un négociateur crée un nouveau mandat et que la fiche Hektor ne bascule pas tout de suite**, le numéro de la fiche pointerait encore l'ancien. Ce n'est pas théorique : le même défaut a été corrigé le 28/07 sur les dates *(bug VA6482 — numéro neuf + date de fin échue, annonce bloquée en « échu »)* |

*(La modale de changement de statut est aujourd'hui **réservée aux admins** —
`isAdmin ? openStatusChangeModal : undefined`. Le négociateur n'a pas encore ce chemin ;
c'est C.4 qui le construira.)*
