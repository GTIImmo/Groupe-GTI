# Audit — de quoi répondre aux 5 questions du registre des relations

> **Demandé par Frédéric le 10/10/2026** : *« un audit pourrait m'aider à répondre aux
> 5 questions et ainsi finir le chantier »*.
> **Audit en LECTURE SEULE.** Aucune écriture, aucun appel à Hektor, aucune fonction `app_*`.
> Complète — et corrige — `notice/AUDIT_REGISTRE_RELATIONS_AUTONOME_2026-09-30.md`,
> vieille de 10 jours et **périmée sur six points**.

---

## 0. En une page

```
Q1  tous les liens montent-ils dans Supabase ?        DEJA REPONDUE (30/09) : TOUT MONTE
                                                      -> chiffres a rafraichir, voir §1
Q2  acquereurs : projection ou copie ?                MESUREE -> la projection ne perd RIEN
                                                         (0) et gagne 24. Recouvrement 100 %
Q3  « retirer un mandant » part chez Hektor ?         DEJA REPONDUE (30/09) : OUI
                                                      -> ET DEJA FAIT depuis le 03/10
Q4  les mandants d'une affaire : liens au bien        MESUREE -> LES DEUX, melanges :
    ou parties de la transaction ?                       28 967 copies de proprietaires
                                                         + 609 vraies parties + 16 trous
Q5  les 5 defauts d'abord, ou le registre ?           MESUREE -> 4 sur 5 sont deja traites
```

⚠ **Les chiffres de Q2 et Q4 ont été CORRIGÉS le 10/10 après une erreur de ma part** : j'avais
traduit les identités avec `app_contact_identite_app` (62 172 paires, le périmètre descendu de
Supabase) au lieu de `app_contact` (**356 452 paires, la vraie source**). Les écarts annoncés
étaient 3 fois trop grands, et l'obstacle « 1 348 mandants sans identité » **n'existe pas**.

**Il ne reste donc que deux décisions de fond (Q2, Q4) et une d'ordre (Q5).**

---

## 1. Q1 — répondue, mais les chiffres ont bougé

La réponse du 30/09 fait foi : **tout monte.** *« Le registre porte tout, les écrans
filtrent »* — le même montage que le mandat.

**Ce qui a changé en 10 jours**, mesuré le 10/10 :

```
                                    30/09         10/10        ecart
liens cote serveur                167 547       167 669        +122
liens dans le cloud                81 379        85 260      +3 881
ce qui monterait en plus           86 168        82 409      -3 759
```

➡ **La décision ne change pas**, et son coût est **un peu plus faible** qu'annoncé.
Le risque reste le même et il reste entier : **la descente de nuit, pas le poids.**
*(Rappel : la descente a déjà mis Supabase par terre une fois.)*
**À vérifier sur cette table-là, pas à supposer.**

---

## 2. Q2 — les acquéreurs : **la projection est la bonne réponse, et c'est mesuré**

### ⚠ DEUX PIÈGES DE MESURE, écartés dans cet ordre

**Piège 1** — `app_affaire_ledger.acquereurs_json` **mélange nos numéros et ceux de Hektor** :

```
affaire compromis 16712   acquereurs = ['10190331', '346990', '347548']
                                        ^^^^^^^^^^   ^^^^^^   ^^^^^^
                                        le notre     numeros HEKTOR
```

**Piège 2, et il m'a coûté deux comptages faux** — j'ai d'abord traduit avec
`app_contact_identite_app` (**62 172 paires**). **C'est la mauvaise source** : cette table est
celle **descendue de Supabase**, et elle ne connaît que le « périmètre éligible ».
**La vraie source est `app_contact` : 356 452 paires**, et le code le dit lui-même —
*« le défaut que ceci ferme a coûté 294 179 doublons le matin du 24 »*
(`build_contacts_layer.py`, `charger_identites_app`).

### Le résultat, avec la BONNE traduction

```
COUPLES (contact, bien) ACQUEREUR
   connus du registre des RELATIONS                 16 258
   connus du registre des AFFAIRES                  16 282
   dans les deux                                    16 258      = 100 %

   une projection les PERDRAIT                           0      <- AUCUN
   une projection les AJOUTERAIT                        24
```

### Ce que ça dit

- ⭐ **Une projection ne perdrait RIEN. Zéro.** Le registre des affaires contient **la totalité**
  des 16 258 couples acquéreur du registre des relations.
- Et il en connaît **24 de plus**.
- ➡ **Q2 est tranchée sans réserve : la projection.** La recommandation du 30/09 est confirmée,
  et le seul risque que j'avais signalé *(les 177 perdus)* **n'existait pas** : c'était mon
  erreur de table.
- ⚠ **Reste 11 acquéreurs sans identité chez nous.** Mesuré : les 11 sont **absents du miroir
  Hektor** — ce sont des contacts que Hektor n'a plus *(même problème que le contact fantôme
  145561 du 09/10)*. Ils portent **18 affaires**. C'est le seul résidu, et il est connu.

---

## 3. Q3 — répondue **et déjà faite**

La réponse du 30/09 : **oui**, le geste part chez Hektor, et la ligne **reste chez nous, datée**.

**Ce que la note du 30/09 ne pouvait pas savoir : le geste existe depuis le 03/10.**

```
Console/console_job_worker.js      "unlink_hektor_mandant" dans la liste des metiers (l. 87)
                                   case "unlink_hektor_mandant" (l. 20405)
                                   cibleHektorContact(identite, ...) (l. 15291)
supabase/patch_claim_unlink_mandant_2026-10-03.sql
                                   la file « actions » reclame le metier, avec garde-fou
                                   d'auto-verification et retour arriere documente
```

➡ **La ligne du tableau §2 de la note — *« retirer un mandant : LE GESTE N'EXISTE PAS »* —
est périmée.** ⏳ *Non mesuré : que le geste ait déjà été joué en vrai.*

---

## 4. Q4 — les mandants d'une affaire : **ce sont des parties de la transaction**

C'était la question la plus ouverte. **Chiffres corrigés avec la bonne table de traduction
(`app_contact`) :**

```
lignes d'affaire au total                                31 058
   qui portent au moins un mandant                       19 858
couples (mandant, bien) distincts                        29 592

   DEJA proprietaire du bien                             28 967      97,9 %
   PAS proprietaire du bien                                 625       2,1 %
      ... le bien a d'autres proprietaires                  609      <- parties de la transaction
      ... le bien n'a AUCUN proprietaire                     16      <- trou du registre

mandants sans identite chez nous                               0      <- AUCUN
```

### ⚠ Ce que ça change par rapport à ma première lecture

Je t'avais dit *« les mandants d'une affaire sont des parties de la transaction »*.
**C'était trop simple, et mes chiffres étaient gonflés par la mauvaise traduction.**

➡ **`mandants_json` mélange DEUX choses de nature différente :**

```
28 967  (97,9 %)  sont DEJA proprietaires du bien  ->  une COPIE de la relation
   609  ( 2,1 %)  ne le sont pas                   ->  de VRAIES parties de la transaction
                                                        (conjoint, indivisaire, heritier...)
    16            sur un bien sans aucun proprietaire ->  un vrai trou, a traiter a la main
```

➡ **La réponse n'est donc pas « l'un ou l'autre », c'est « les deux, à séparer » :**
les 28 967 doivent devenir une **référence** vers la relation *(aujourd'hui recopiée)* ;
les 609 **restent dans la transaction**, où ils sont à leur place.

➡ ✅ **Et l'obstacle que j'avais annoncé — « 1 348 mandants sans identité » — n'existe pas.**
C'était mon erreur de table. Le vrai chiffre est **zéro**.

---

## 5. Q5 — où en sont les 5 défauts

| | défaut | état au 10/10 |
|---|---|---|
| **R-1** | fiche contact vide ouverte depuis une annonce | ✅ **CORRIGÉ ET DÉPLOYÉ** — `93cc01b` est dans `origin/main`. La note disait *« reste à déployer »* |
| **R-2** | `update_hektor_mandant_contact` écrase l'identité par la cible | ✅ **CORRIGÉ** — *« deux numéros, deux variables […] on ne l'écrase plus »* (l. 18090). ⏳ le rafraîchissement du CONTACT lui-même reste à vérifier |
| **R-3** | un lien en attente invisible hors de `DossierDetailLayoutBase` | ⏳ **NON VÉRIFIÉ** — le front a été refondu depuis, les lignes citées ont bougé |
| **R-4** | `constaterLesPersonnes` range un n° Hektor dans `contact_id` | ⏳ **NON VÉRIFIÉ** — la fonction existe toujours (l. 13943) |
| **R-5** | `link_hektor_mandant` ne rafraîchit pas le contact | ⏳ **NON VÉRIFIÉ** — passe bien par `cibleHektorContact(identite, …)` (l. 14927) |

➡ **Les deux qui touchaient aux données sont réglés.** Il reste trois vérifications d'écran,
petites et sans risque.

---

## 6. ⚠ La note du 30/09 est périmée sur SIX points

C'est le résultat le plus utile de cet audit : **le chantier a beaucoup avancé sans que sa
note soit relue.**

| ce que dit la note du 30/09 | la réalité au 10/10 |
|---|---|
| *« la table durable : PAS ENCORE EXÉCUTÉE SUR LA PRODUCTION »* | ✅ **exécutée** — `app_relation` porte **132 727 lignes** |
| *« retirer un mandant : LE GESTE N'EXISTE PAS »* | ✅ **existe depuis le 03/10**, bout en bout |
| *« les fonctions SQL des gestes mandant ne sont versionnées nulle part »* | ✅ **les quatre sont dans `supabase/`** |
| *« bug ① : RESTE À DÉPLOYER »* | ✅ **déployé** |
| *« SENTINELLE : AUCUNE »* | ✅ **deux** : `relation_disparue.py`, `fiche_annonce_mandants.py` |
| *« carnet 167 583 clés, 36 absentes »* | **335 249 clés, 167 580 absentes** *(nuit du 09→10/10)* |

---

## 7. Ce qui reste vraiment du chantier

La piste du 30/09 avait 8 points. Leur état réel :

```
1  un numero de lien FRAPPE, jamais calcule       ✅ deux distributeurs, deux plages
2  deux robinets, une table, delete-never         ✅ depuis les 02-03/10
3  LE FAIT BRUT, PAS LE LIBELLE                   ❌ PAS FAIT  <-- la cause de cette nuit
4  les acquereurs se PROJETTENT                   ❌ pas fait   <-- Q2
5  retirer devient un geste                       ✅ depuis le 03/10
6  les deux fiches lisent la meme table           🟡 fait autrement (le numero transmis)
7  les sentinelles                                🟡 deux sur trois ; « lien app non adopte
                                                     apres N jours » n'existe pas
8  versionner les fonctions SQL                   ✅ les quatre sont la
```

➡ **Il reste le point 3, le point 4, et une sentinelle.** Le reste est fait.

---

## 8. Ce que la nuit du 09 au 10/10 vient de prouver

Le point 3 n'est pas une élégance : **son absence a coûté une nuit.**

La conception disait, le 30/09 :

> *« le registre stocke le fait brut, le libellé se dérive — **sinon chaque mandat signé
> change l'identité du lien**. »*

**C'est arrivé.** Le rattrapage des fiches d'archives a fait basculer **6 259 liens** de
« mandant » à « propriétaire ». Le libellé étant dans la recette de l'identifiant, les
6 259 identifiants ont changé → le garde-fou s'est déclenché (seuil 1 000) → **et son repli,
cassé, a rebasculé les 167 483 identifiants du parc en une nuit.**

```
mesure du 25/09, redoutee : « SEUL, ce changement refabriquerait 167 487 identifiants »
nuit du 09->10/10, arrivee :                                     167 483
```

Aucune donnée perdue *(34 liens d'écart sur 167 703)*, mais le push a retiré puis reposé
tous les liens — **le scénario qui a saturé Supabase le 22/08**. On est passés au travers.

➡ **Le point 3 est donc devenu le plus urgent des trois.**

⏳ *La note détaillée de l'incident (le mécanisme ligne par ligne, le défaut du garde-fou, les
quatre correctifs envisagés puis trois retirés) reste à écrire — en attente du choix de
Frédéric sur le correctif A.*

---

## 8-bis. ⛔ FAUSSE ALERTE — les 7 764 transactions sans mandat étaient DÉJÀ tranchées

> **Frédéric, 10/10 : *« relis l'historique de mon projet, ce n'est pas ça »*. Il avait raison.**
> J'ai annoncé comme une trouvaille un sujet **mesuré, expliqué et classé le 04/09**, et j'ai
> même présenté comme une fuite nouvelle un comportement de Hektor documenté le 03/09.
>
> **La réponse est dans `notice/LISTE_TACHES_A_COCHER_2026-08-29.md`, tâche 2.7 :**
> *« ⚠ LE PLAFOND RÉEL EST ~75 %, PAS 100 % : les **7 770 sans mandat** sont des affaires
> **closes depuis quinze ans**. **Ce n'est pas une dette.** »*
> ➡ Mes 7 764 d'aujourd'hui, dont **7 427 antérieures à 2015**, confirment ce chiffre.
>
> **Et le « taux qui triple » (5,0 % en 2025-2026) n'existe pas non plus** : les 101 récentes
> sont à **71 % des offres**, et c'est documenté depuis le 03/09 sur l'offre 33046 —
> *« envoyé `numero_mandat = 11939` → Hektor garde `id_mandat = 0` ; cohérent avec les 98 %
> d'offres sans mandat du parc : **ce n'est pas une anomalie de nos données, c'est Hektor qui ne
> retient pas le mandat sur une offre** »*.
>
> ⭐ **LA LEÇON, ET ELLE EST POUR MOI** : une trouvaille se vérifie **contre l'historique du
> projet AVANT** d'être annoncée. Deux fois dans la même journée, j'ai ouvert un faux sujet
> *(celui-ci, et les « 1 348 mandants sans identité »)*.
>
> *Ce qui suit est conservé comme mesure, pas comme alerte.*

```
A QUEL MANDAT APPARTIENT CHAQUE TRANSACTION ?   (colonne mandat_origine)

   1  HEKTOR L'A DIT                         14 938    48,1 %
   2  L'ANNONCE N'A QU'UN SEUL MANDAT          8 356    26,9 %
   3  LA PERIODE                                   0
   4  LE MANDANT (mandants_json)                   0     <- rendement ZERO, structurel
   5  AUCUN MANDAT CONNU POUR CE BIEN          7 764    25,0 %
```

**Les 7 764 portent sur 2 765 biens, dont 2 744 HORS DU PARC VIVANT** (vendus, clos, archivés).

### L'information n'existe NULLE PART — vérifié sous quatre angles

```
leur fiche detail a bien ete rattrapee            2 751 / 2 751   (0 manquante)
   ... mais son mandats_json est VIDE             2 751 / 2 751
present dans hektor_mandat (le miroir qui accumule)       0
un numero sur hektor_annonce.no_mandat                    0
la transaction porte elle-meme un numero                 14 / 7 764
   ... et dans le payload brut de Hektor                   0
```

➡ **Quand un bien quitte le parc actif, Hektor cesse de rendre son mandat.** Ce n'est pas un
défaut de notre côté : notre registre des mandats est bien `delete-never`, mais on ne peut pas
garder ce qu'on n'a jamais vu.

➡ **C'est la version MANDAT du chiffre du 30/09** : *« le jour où un bien se vend, 82 386 fois,
on a cessé de savoir qui en était le mandant »*. La table durable des relations a réparé la
propriété. **Le mandat n'a pas eu la même réparation — et pour lui, c'est trop tard.**

### Historique ou fuite active ? — **les deux**

```
                sans mandat / total          taux
avant 2015        7 427 / 13 062            56,9 %     <- le gros du trou, irrecuperable
2015 a 2024         236 / 15 973             1,5 %     <- regle
2025-2026           101 /  2 023             5,0 %     <- ⚠ TRIPLE par rapport a 2015-2024
```

⚠ **Le taux remonte.** 56,9 % avant 2015 est un retard historique borné. Mais **1,5 % → 5,0 %**
sur les deux dernières années n'est pas expliqué. **Non mesuré :** pourquoi.

---

## 9. Ce que je n'ai PAS mesuré

- **Les 609 vraies parties de transaction** : je n'ai pas vérifié ce qu'elles sont
  *(conjoint, indivisaire, héritier, représentant ?)*. Un échantillon de quelques fiches le
  dirait.
- **Les 16 biens sans aucun propriétaire** : à regarder un par un.
- **Les 11 acquéreurs absents du miroir** : identifiés, mais leur sort dépend du sujet
  « contact fantôme » que Frédéric a reporté le 09/10.
- **R-3, R-4, R-5** : localisés, pas vérifiés.
- **Que le geste `unlink_hektor_mandant` ait déjà été joué** en vrai.
- **La descente** : je n'ai pas mesuré ce que +82 409 lignes lui feraient. C'est **le seul
  vrai risque de Q1** et il mérite sa propre mesure avant la bascule.
- **Les autres objets** : audit limité à la relation, comme le 30/09.
