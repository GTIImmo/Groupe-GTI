# Audit — intégrer les 45 mandats absents, et la fiche du registre

**15/10/2026.** Deux questions de Frédéric, dans le même message :

> *« audit comment on peut intégrer ces 45 mandats dans mon projet, nous l'avions déjà fait
> pour la liste des 80 de février — cherche, mais attention il faut que cela s'adapte à mes
> codes actuels. Et je pose la question : dans le registre des mandats, la fiche qui s'ouvre
> ne peut pas, puisque le mandat est lié à un contact et pas à une annonce ? »*

**Lecture seule. Rien n'a été modifié, rien n'a été décidé.**

---

## 1. La porte de février existe bien — et je l'ai mesurée

`phase2/sync/manual_mandat_corrections.py`, écrit le 05/10 (commit `8f77f62`).
Elle est branchée à **quatre endroits** : `normalize_source.py` l. 732 et 829,
`phase2/sync/refresh_single_annonce.py` l. 287 et 471.

**Ce qu'elle fait exactement, en trois gestes :**

```
1  elle lit le .xlsx « liste mandat », INDEXE PAR NUMERO DE MANDAT
2  elle prend le detail d'UNE ANNONCE, et y lit keyData.NO_MANDAT
3  si ce numero est dans le .xlsx ET que l'annonce n'a AUCUN mandat,
   elle pose le mandat du .xlsx dans la liste de l'annonce
```

Le code, mot pour mot *(l. 137-151)* :

```python
mandats = data.get("mandats")
if isinstance(mandats, list) and mandats:
    return data                     # <- elle RENONCE des qu'un mandat existe
...
patched["mandats"] = [correction]   # <- elle REMPLACE la liste par UN element
```

⭐ **Et les codes que j'avais déduits des exports sont les siens, à l'identique** :
`EXCLUSIVITY_LABELS = {"1": "EXCLUSIF", "3": "ACCORD", "5": "SIMPLE"}`. La déduction
du 15/10 est donc confirmée par le projet lui-même, indépendamment.

### Son résultat réel sur février — mesuré, pas supposé

| | |
|---|---|
| lignes du fichier de février | **80** |
| numéros entrés au registre | **77** |
| lignes de registre portant la marque `manual_xlsx:` | **78** |
| numéros restés dehors | **3** — `18383`, `18404`, `18408` |

⚠ **78 lignes pour 77 numéros** : le mandat **18390** a été posé sur **deux** annonces
(59458 **et** 59669). La porte injecte **par numéro** : si deux annonces portent ce
`NO_MANDAT`, elle le duplique. Ce n'est pas grave ici, mais c'est son comportement.

⭐ **Et les 3 qui ont échoué disent exactement POURQUOI** : leurs références produit
(`VI3321`, `VM71618`, `VA32707`) **ne correspondent à aucune annonce chez nous**. Sans
annonce, la porte n'a rien où poser. *(`18404` est l'un des 9 mandats vivants introuvables
du classeur.)*

---

## 2. Les 45 absents : combien passent par cette porte ? **ZÉRO**

Mesure du 15/10 sur les deux exports, face aux 26 859 lignes de `app_mandat` :

```
45 absents distincts -- tous issus du fichier « ancien » (fevrier est fait)
   23 de type 1 (VENTE)       dont 10 : la reference EST une annonce chez nous
                              dont 13 : reference INCONNUE chez nous
   22 de type 3 (RECHERCHE)   AUCUNE n'a de reference produit  -> aucune annonce
```

**Trois murs différents, et la porte de février ne franchit aucun des trois :**

| | combien | ce que la porte fait | pourquoi elle échoue |
|---|---|---|---|
| **A** mandat **ANTÉRIEUR** d'une annonce qu'on a | **10** | `if mandats: return data` | l'annonce porte **déjà** son mandat courant |
| **B** annonce **inconnue** de nous | **13** | rien | il n'y a pas de détail d'annonce à patcher |
| **C** mandat de **RECHERCHE**, lié à un contact | **22** | rien | il n'y a **pas d'annonce du tout** |

### ⭐ Le mur A est le plus instructif — mesuré sur les 10

Hektor ne met **qu'un seul mandat** dans le détail d'une annonce : le **courant**.
Les 10 absents sont tous des mandats **plus anciens** du **même bien** :

```
   cherche    ref        annonce    ce que le detail de l'annonce porte
     14433    VM9272      53519     17874   (2025-06-19)
     16421    VM1576      33343     17846   (2023-11-12)
     16701    VI054       41559     16705   (2024-03-01)
     17153    VM66658     54680     17600   (2025-03-03)
     17176    VI3166      52931     18014   (2025-09-02, RECHERCHE)
     17283    VM66188     11691     17487   (2025-01-13)
     17349    VM66242     32558     17479   (2025-01-09)
     17460    VM33178     25204     12115   (2019-06-11)   <- « GERPHAGNON Test »
     17493    VM68724     11782     17496   (2025-01-16)
     17542    VM68814     54781     17789   (2025-05-15)
```

**10 sur 10 : le numéro cherché n'est dans AUCUN détail d'annonce.** Il n'y sera jamais.

⚠⚠ **Et la « ligne à changer » annoncée par le commit 8f77f62 ne suffirait pas.**
Ce commit écrit : *« `inject_manual_mandat_if_missing()` renonce dès qu'un mandat existe —
il doit pouvoir CORRIGER un corps suspect, pas seulement combler un vide. »* C'est vrai
pour **corriger**. Mais pour **ajouter** un second mandat, retirer ce garde-fou serait
**destructeur** : la ligne suivante fait `patched["mandats"] = [correction]` — elle
**écraserait** le mandat courant de l'annonce par l'ancien. ➡ **Ce n'est pas une ligne à
changer, c'est une fonction qui ne sait pas faire ce travail-là.**

---

## 3. ⭐ LA RÉPONSE À LA QUESTION DE FRÉDÉRIC

> *« la fiche qui s'ouvre ne peut pas, puisque le mandat est lié à un contact et pas à une
> annonce ? »*

**Trois réponses différentes, parce qu'il y a trois étages — et elles ne vont pas dans le
même sens.**

### Étage 1 — LA TABLE : non, c'est impossible *(c'est le vrai blocage)*

```sql
hektor_annonce_id   TEXT   NOT NULL
numero_mandat       TEXT   NOT NULL
sqlite_autoindex_app_mandat_1   UNIQUE (hektor_annonce_id, numero_mandat)
```

**26 859 lignes sur 26 859 ont une annonce. Zéro NULL, zéro vide.** Un mandat sans annonce
**ne peut littéralement pas être écrit** dans `app_mandat`. ⚠ C'est la même contrainte que
celle déjà notée le 07/10 : *« n° Hektor NOT NULL partout »*.

### Étage 2 — LE FABRICANT DU REGISTRE : non, il ne le verrait pas

`build_mandat_register_rows` *(`phase2/sync/export_app_payload.py` l. 2105)* **part des
annonces**, pas des mandats. Et `charger_mandats_depuis_app_mandat` *(l. 866)* écarte
explicitement ce qui n'en a pas :

```python
if not annonce or not numero:
    continue
```

Même écrite en base, une ligne sans annonce **ne sortirait pas** dans le registre.

### Étage 3 — L'ÉCRAN : ⭐ **lui, il saurait faire** *(contrairement à ce que Frédéric craint)*

La fiche du registre **n'ouvre pas l'annonce** : elle affiche **la ligne du registre
elle-même** *(`App.tsx` l. 24286 : `detailOpen && selectedDetail`, nourri par
`register_detail_payload_json`, `register_history_json`, `register_avenants_json`)*.
L'annonce ne sert qu'à **trois agréments, tous déjà protégés** :

| ce qui a besoin de l'annonce | garde déjà en place |
|---|---|
| l'éditeur d'avenant *(pré-remplissage)* | `if (editorDossierId == null) return` |
| le bouton **« Fiche bien »** | `register_detail_available` |
| le bouton **« Hektor »** | `openHektorAnnonce(hektor_annonce_id)` — partirait vide |

➡ **Sur l'écran de bureau, une fiche de mandat sans annonce s'ouvrirait et serait lisible.**

⚠ **Sauf sur MOBILE** *(`App.tsx` l. 21707)*, où le clic fait l'inverse — il ouvre
l'annonce, et **ne fait rien du tout** sans elle :

```js
if (row?.app_dossier_id) openDossierDetailPage(row.app_dossier_id)
```

Pas de message, pas d'erreur : **rien ne s'ouvre**. *(C'est la même famille que la photo
qui ne s'affichait pas du tout, 14/10 : une absence est pire qu'une erreur.)*

### ⭐⭐ ET SURTOUT : le registre sait DÉJÀ porter plusieurs mandats sur une annonce

La clé est `(annonce, numéro)`, pas `(annonce)`. Mesure :

```
26 776 annonces portent 1 mandat
    40 annonces en portent 2
     1 annonce  en porte  3   <- 63200 : 18919 VENTE + 18937 et 18938 RECHERCHE
```

➡ **Le mur A (les 10 mandats antérieurs) n'est donc PAS un mur de structure** : la table
les accepterait tels quels. C'est seulement `inject_manual_mandat_if_missing` qui ne sait
pas les poser. **Le mur C (les 22 recherches) est le seul mur de structure.**

---

## 4. Ce qu'il faudrait, par mur — rien n'est décidé

```
MUR A -- 10 mandats anterieurs d'annonces connues
   La table les accepte DEJA. Ce qu'il manque : un poseur qui AJOUTE au lieu de
   remplacer. Ce n'est PAS la porte de fevrier (elle ecraserait le mandat courant).
   Cout : un script a part, additif, hors du run. Risque : faible.
   ⚠ Verifier d'abord que 17460 (« GERPHAGNON Test ») n'est pas un essai.

MUR B -- 13 mandats dont l'annonce nous est inconnue
   Rien a faire tant que l'annonce manque : la cle EXIGE une annonce. Ce sont
   probablement des biens d'avant la migration, jamais descendus.
   ➡ QUESTION DE FAIT pour Frederic : ces biens existent-ils encore chez Hektor ?

MUR C -- 22 mandats de RECHERCHE, lies a un contact
   C'est une DECISION DE STRUCTURE, pas un correctif. Trois formes possibles,
   je n'en choisis aucune :
     C1  rendre hektor_annonce_id facultatif (toucher la cle primaire de la
         table du registre LEGAL -- lourd, et le fabricant part des annonces)
     C2  un registre a part pour les mandats de recherche, avec sa propre cle
         (contact, numero) -- additif, ne touche a rien d'existant
     C3  une annonce fictive par mandat de recherche -- ⛔ contraire a la regle
         du projet « un numero ne se perd jamais / ne pas inventer d'identifiant »
   ⚠ Et le MOBILE devra etre repare dans tous les cas (clic muet).

⚠ RAPPEL : la loi Hoguet veut ces mandats au registre, et le projet l'a deja admis
   le 29/09 (« les 63 RECHERCHE sont toutes dans le perimetre »).
```

### Et la porte CONSOLE reste la vraie source

Les exports s'arrêtent au **26/02/2026**. La console (§ 6 de
`AUDIT_MANDATS_RECHERCHE_PAR_CONTACT_2026-10-15.md`) rapporte les mandats de recherche
**vivants**, eux. Les 22 de l'export sont un **rattrapage du passé** ; la console est le
**robinet du présent**. Les deux chantiers partagent le même mur C.

---

## 5. Ce qui n'a pas été fait, et pourquoi

- **Aucun code écrit, aucune écriture.** La question posée est une question de structure :
  elle appartient à Frédéric *(mémoire : « ne pas décider seul un périmètre »)*.
- **La porte de février n'a pas été touchée.** Elle fait correctement son travail
  (77/80) ; l'élargir dans sa forme actuelle écraserait des mandats courants.
