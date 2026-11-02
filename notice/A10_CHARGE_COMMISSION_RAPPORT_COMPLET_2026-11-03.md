# RAPPORT — LA CHARGE DE LA COMMISSION : TOUT CE QU'ON SAIT AU 03/11/2026

**Demandé par Frédéric** : *« fais un audit sur toutes les découvertes sur la
charge commission et mon projet, dans un rapport »*.

**Périmètre** : qui paie les honoraires d'agence — le vendeur ou l'acquéreur —
sur les **mandats** et sur les **transactions**.
**Méthode** : le code et la base d'abord, les notes ensuite.
**LECTURE SEULE DE BOUT EN BOUT.** Miroir ouvert en `mode=ro`, 12 appels de
lecture à l'API Hektor, **aucune écriture** en base, chez Hektor ou au classeur.

Notes qui précèdent celle-ci : `A8_AUDIT_CHARGE_DE_COMMISSION_2026-11-02.md`
(la cause racine du vide) · `A9_LA_CHARGE_EST_DANS_LE_DETAIL_ANNONCE_2026-11-03.md`
(la source, et ce qu'A8 avait manqué) ·
`DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md` § 3 quater → 3 octies
(le décodage de l'export Modelo) ·
`SPEC_CHARGE_HONORAIRES_MANDAT_2026-11-02.md` (le palier 1, en production).

---

## § 1. LA RÉPONSE EN UNE PAGE

```
AVONS-NOUS LA CHARGE ?

  SUR LES MANDATS     oui, a 76,6 %  --  mais INVISIBLE a l'ecran
                      La valeur descend chaque nuit dans notre miroir et
                      s'y arrete. Aucune colonne du registre ne la porte,
                      aucun ecran ne la montre, aucun worker ne la remonte.

  SUR LES TRANSACTIONS  non  --  8 lignes sur 31 124
                      La colonne EXISTE (charge_commission_app) mais ne se
                      remplit presque jamais, pour une raison connue et
                      mesuree (§ 5-A). Et elle NE SE DEDUIT PAS des montants.
```

⭐ **Le fait central de ce rapport** : l'information n'est pas à fabriquer, elle
est **déjà chez nous**. Il manque un tuyau, pas une donnée.

---

## § 2. OÙ ELLE EST — la source, trouvée le 02/11 au soir

C'est Frédéric qui a indiqué où chercher : *« cette information doit bien être
quelque part dans mon projet, vérifie les données récupérées par un appel id
annonce dans le détail bloc mandat »*.

```
data/hektor.sqlite  ->  table hektor_annonce_detail  ->  colonne honoraires_json

   [{"id": "31", "taux": "5000", "charge": "vendeur"}]
                                  ^^^^^^^^^^^^^^^^^^
                       le mot est ECRIT, ce n'est pas un code a decoder
```

```
MESURE :
  61 459 lignes de detail, 14 302 portent un bloc honoraires
  valeurs rencontrees : « vendeur » 62 571 lignes · « acheteur » 19 352
  AUCUNE valeur vide ; les 3 cles sont toujours la (id, taux, charge)
  par annonce : 11 030 vendeur · 3 258 acheteur · 14 se contredisent
```

⚠ **Hektor dit « acheteur »** là où notre vocabulaire dit « acquéreur ».
⚠ `taux` est **un montant en euros**, pas un pourcentage — le backend le savait
déjà (`rapprochement_email.py:129`), le front l'ignore (§ 5-C).

---

## § 3. COMBIEN ELLE COUVRE — et la clé qui a tout débloqué

**Frédéric, le 03/11** : *« mon projet a une clé dans son registre : numéro de
mandat + id annonce = la clé »*. **Vérifié, et il a raison** :

```
app_mandat_register_current : 24 568 lignes
                              24 568 couples (numero_mandat + hektor_annonce_id)
                              -> LA CLE EST UNIQUE
                              18 260 numeros de mandat · 24 476 annonces
                              un mandat porte jusqu'a 10 lignes (ex. 10249)
```

⭐⭐ **Conséquence** : chaque ligne du registre porte **son** annonce, donc **sa**
charge. La question « quelle annonce fait foi » que je posais n'avait pas de
sens, et c'est elle qui donnait deux comptes différents selon la façon de
compter. **Le rattrapage se fait ligne par ligne.**

```
LA COUVERTURE VRAIE, LIGNE PAR LIGNE DU REGISTRE

annee   lignes   Hektor   Modelo   AUCUNE   couvert
2009        30        0       23        7    76,7 %
2010       260        0      233       27    89,6 %
2011     2 548        0    2 270      278    89,1 %
2012     2 045        0    1 064      981    52,0 %
2013     2 278        2      185    2 091     8,2 %   <- LE TROU
2014     2 171        2       84    2 085     4,0 %   <- LE TROU
2015     1 766       13    1 734       19    98,9 %
2016     1 786       11    1 755       20    98,9 %
2017     1 750      730    1 004       16    99,1 %
2018     1 525    1 339      182        4    99,7 %
2019     1 434    1 377       53        4    99,7 %
2020     1 207    1 054      134       19    98,4 %
2021     1 182    1 051      123        8    99,3 %
2022     1 108    1 036       63        9    99,2 %
2023     1 082    1 021       53        8    99,3 %
2024       907      866       34        7    99,2 %
2025       789      730        0       59    92,5 %
2026       683      590        0       93    86,4 %
TOTAL   24 568    9 836    8 994    5 738    76,6 %

repartition des 18 830 lignes couvertes : 11 853 vendeur · 6 977 acquereur
```

**Les deux sources sont complémentaires, pas concurrentes** : Hektor tient
2017→2026, l'export Modelo bouche 2009→2016 où Hektor est muet. De 2015 à 2024,
la couverture réunie est de **98,4 à 99,7 %**.

### ⬜ LE TROU 2012-2014 — expliqué le 03/11, avec son témoin inverse

```
les 6 494 lignes de 2012-2014 :
   detail present mais honoraires VIDE        6 490   (99,9 %)
   honoraires renseigne                           4   ( 0,1 %)

TEMOIN INVERSE, les 1 434 lignes de 2019 :
   honoraires RENSEIGNE                       1 377   (96,0 %)
   detail present mais honoraires vide           57   ( 4,0 %)
```

⭐ Donc **ce n'est pas un défaut de notre lecture** : le détail descend bien, et
**Hektor lui-même n'a pas les honoraires de ces années**. L'export Modelo ne les
a pas non plus (8,2 % et 4,0 %). **La donnée n'existe nulle part.**
⬜ **Hypothèse non prouvée** : la migration depuis l'ancien logiciel (les lignes
`M<numéro>` / `external_key` « sphere… » de l'export Modelo) n'a pas repris les
honoraires. ⚠ Et **1 264 de ces lignes ne sont pas archivées** : des biens
encore vivants sans charge connue.

---

## § 4. POURQUOI ON PEUT LA CROIRE — trois témoins indépendants

### Témoin 1 — l'export Modelo, décodé par l'arithmétique

```
mandat 16699 : prix 134 000 · net vendeur 124 700 · honoraires 9 300
               134 000 - 124 700 = 9 300 EXACTEMENT    -> LE VENDEUR PAIE
mandat 16662 : prix 34 000 · net vendeur 34 000 · fees_paid_by_buyer 3 500
               le vendeur touche TOUT                  -> L'ACQUEREUR PAIE
```

⛔ **Et le code `fees_paid_by_who` ne doit PAS servir** : le code 3 mélange
1 703 **locations** aux ventes, et le code 1 n'a aucun sens stable.
⛔ **Le fichier n'est pas une liste de mandats** : `product_ref` est quasi unique
(26 180 / 26 209) — c'est un **bien** par ligne. Et **deux numérotations se
superposent** : 9 319 lignes `M<numéro>` / « sphere… » viennent de l'ancien
logiciel, dont Hektor a **réattribué** les numéros. Filtre retenu : la ligne doit
porter « Num mandat » dans ses observations **et** ce numéro doit égaler la
colonne B → 14 364 lignes, 11 676 mandats.

### Témoin 2 — le croisement des deux sources

```
8 314 mandats presents dans Hektor ET dans l'export Modelo
   accord      7 777   =  93,5 %
   desaccord     537   -> a trancher un par un ; Hektor est la source vivante
```

Chacune a été établie **sans** l'autre : c'est une épreuve, pas une confirmation
de confort.

### Témoin 3 — l'API, interrogée en direct le 02/11 au soir

```
11 mandats de 2026 reputes sans charge  ->  honoraires = null
TEMOIN POSITIF 61398                    ->  [{"id":"84962","taux":"12000",
                                              "charge":"vendeur"}]
```

Le même appel, la même seconde, rend la donnée pour un bien qui l'a. Donc le
`null` n'est ni une erreur de lecture, ni un miroir périmé.

### ⭐⭐ ET LA DÉCOUVERTE QUI CHANGE LA RÈGLE PAR DÉFAUT : LA BASCULE DE 2017

```
% de mandats de VENTE a charge VENDEUR, par annee de creation (export Modelo)
  2015    0,5 %      <- c'etait l'ACQUEREUR qui payait
  2016    0,8 %
  2017   43,8 %      <- LA BASCULE
  2018   90,0 %
  2019   97,2 %
  2020   97,2 %
  2022   94,2 %
  2024   95,1 %
```

⛔⛔ **La règle de Frédéric — *« un mandat de vente est 90 % du temps chargé
vendeur »* — est juste À PARTIR DE 2018, et à l'envers avant 2017.** L'appliquer
à l'historique inverserait la charge sur environ 3 700 mandats.

```
LA REGLE PAR DEFAUT, SI ON DOIT DEDUIRE :
   vente >= 2018   -> « vendeur »
   vente <= 2016   -> « acquereur »
   vente de 2017   -> AUCUN defaut (43,8 / 56,2 : on ne devine pas)
   mandat de recherche -> « acquereur » (sa regle, inchangee)
⛔ ET CHAQUE LIGNE REMPLIE PORTE SA SOURCE : « hektor » · « fichier_modelo » ·
   « deduite_par_defaut ». Une valeur deduite n'est pas une valeur constatee.
```

---

## § 5. LES QUATRE DÉFAUTS — un connu, trois neufs

### A — ⭐ La modale de statut n'écrit que si on touche *(trouvé par A8, 02/11)*

```
l'ecran ouvre sur « Vendeur » (useState('vendeur'))
et la RPC n'est appelee QUE `if (statusChangeCommissionTouchee)`
=> voir « Vendeur », qui est juste, et envoyer : RIEN N'EST ECRIT

PREUVE PAR LA DONNEE : 8 lignes de charge dans toute la base,
                       8 « acquereur », 0 « vendeur »
```

Le seul cas qui **oblige** à toucher le menu est le seul qui existe en base.
C'est la cause racine du vide des transactions, et elle est juste.

### B — ⛔ L'éditeur du PDF de mandat ouvre sur « Mandant », EN DUR *(neuf)*

```
App.tsx:4571    honorairesCharge: 'mandant',
App.tsx:4677    const chargeAcquereur = payload.honoraires.charge === 'acquereur'
                -> LE PDF COCHE UNE CASE SELON CETTE VALEUR
```

C'est le **jumeau exact** du défaut A, sur une autre porte, et A8 ne l'avait pas
vu. La valeur de Hektor existe pour le bien : elle n'est **jamais lue**. Pour les
3 258 annonces à charge acquéreur, le PDF coche « Mandant » si le négociateur ne
corrige pas — **sur un document signé par le client**.

⭐ **L'impact réel est faible aujourd'hui, et il faut le dire** : **18 PDF** de
mandat générés en tout, du **29/06 au 24/07/2026**, aucun depuis. Mais il mordra
dès qu'on ouvrira cette porte — et c'est précisément celle que ce chantier veut
ouvrir.

### C — ⛔ Le repli du PDF lit les mauvaises clés *(neuf)*

```
App.tsx:4543
  valueFromJsonList(detail.honoraires_json,
                    ['montant_ttc','montant','honoraires','value'])
  les VRAIES cles sont : id · taux · charge
  -> ce repli ne peut JAMAIS rien trouver. Le montant vit dans `taux`.
```

### D — ⛔ Une étiquette trompeuse *(neuf)*

`App.tsx:30778` affiche **« Honoraires acquéreur »** en prenant
`honoraires_sortie_app` (la nôtre) puis **`honoraires_sortie` en repli** — une
colonne de Hektor qui ne veut pas dire cela (§ 6).

---

## § 6. ⛔ CE QUI NE MARCHE PAS : DÉDUIRE LA CHARGE DES MONTANTS

Frédéric : *« il y a une colonne honoraires vendeur et honoraires acquéreur, donc
on la déduit déjà, pas la peine d'ajouter une colonne non ? »* — **la colonne
existe bien déjà** (`charge_commission_app`), mais la déduction ne tient pas.

**Mesure 1, par dénombrement — imparable :**

```
app_affaire_ledger, 31 124 lignes :
   honoraires_entree  (vendeur)   renseigne 19 860
   honoraires_sortie  (acquereur) renseigne     79        <- SOIXANTE-DIX-NEUF
   par nature : offre 11 206 (0 / 33) · compromis 10 642 (10 605 / 26)
                vente 9 276 (9 255 / 20)
or Hektor dit « acquereur » pour 3 258 annonces
-> il manquerait plus de 3 000 valeurs. La colonne ne peut pas porter l'info.
```

**Mesure 2, par croisement avec la vérité connue — et le résultat est l'inverse :**

```
charge dite par Hektor   verdict arithmetique du compromis      lignes
  acquereur              « le prix inclut les honoraires »          81
  acquereur              non mesurable / autre                       9
  vendeur                « le prix inclut les honoraires »       4 307
  vendeur                autre                                      56
honoraires_sortie rempli :  acquereur 8  ·  vendeur 9
```

⭐⭐ **81 des 90 compromis à charge ACQUÉREUR donnent le même profil que les
4 307 à charge vendeur.** Donc `prix_net_vendeur` est calculé par Hektor comme
*prix − honoraires* **quelle que soit la charge** : le témoin qui avait tranché
l'export Modelo **ne discrimine rien ici**.

⚠ **ET C'EST UNE CORRECTION DE MA PART** : le 02/11 au soir j'ai dit à Frédéric
que ces deux colonnes étaient « honoraires vendeur / acquéreur » au sens de qui
paie, en me fiant aux libellés du front. **A8 disait l'inverse, et A8 avait
raison.** La mesure du 14/10 (commit `b957636`) l'avait déjà écrit : *sur 25
lignes où le classeur dit « Acquéreur », 13 sont rangées côté vendeur chez
Hektor.*

---

## § 7. CE QUE CET AUDIT A CORRIGÉ DANS LE PROJET

```
A8 (02/11, 16:48) a conclu « IL N'Y A RIEN SUR LA CHARGE ».
  Il a deballe TROIS objets : hektor_mandat, hektor_compromis, hektor_vente.
  La charge est sur le QUATRIEME : l'ANNONCE.
  Le mot « honoraires_json » n'apparait pas une fois dans A8, ni dans aucune
  des 9 notes du domaine. Le champ n'etait pas cache : il n'etait pas cherche la.
  -> sa conclusion ④ (« le classeur est la seule source, 955 lignes ») est FAUSSE.
     La source est chez nous, 15 fois plus large, et elle se met a jour seule.
```

**Et trois de mes propres mesures ont été fausses en route, toutes attrapées par
un témoin, jamais par une relecture :**

```
1. « la cle honoraires est ABSENTE de la reponse » (75 fois sur 75)
   -> FAUX : ma fonction s'arretait a 4 niveaux de profondeur. La cle est dans
      100 % des 61 462 reponses. Un LIKE sur le texte brut m'a dementi.
2. « honoraires_entree/sortie = qui paie »
   -> FAUX, voir § 6. A8 avait raison.
3. « quelle annonce fait foi pour un mandat ? » (verrou que je posais)
   -> QUESTION SANS OBJET : la cle du registre est le COUPLE. Frederic l'a dit,
      la base l'a confirme.
```

⛔ **La leçon, qui est celle d'A8 retournée contre lui** : *une réserve d'audit
non traitée devient le bug* — ici, **un audit qui a cru un zéro** sans balayer
les quatre objets, alors que la règle du projet dit qu'un audit balaie les objets
*et* les gestes, et que « annonce » est un objet du tableau.

---

## § 8. CE QUI RESTE À FAIRE — rien n'est codé, aucun « go » demandé

```
① REMONTER LA VALEUR DE HEKTOR JUSQU'AU REGISTRE DES MANDATS
     une colonne mandat_charge_honoraires_hektor, alimentee par l'exporteur
     depuis honoraires_json, A COTE de la saisie humaine
     (mandat_charge_honoraires_app, posee le 02/11, vide).
     Precedence a l'ecran : la saisie d'abord, Hektor en repli.
     ⭐ C'est le patron DEJA EPROUVE de la date de cloture (13/10) : il protege
       le carnet du push de nuit, qui detruit et refait la ligne du registre.

② L'AFFICHER sur la fiche du mandat et au registre.

③ LA REPRENDRE A LA TRANSACTION : l'offre nait avec la charge de SON mandat
     (meme couple mandat + annonce), modifiable ensuite.
     ⭐ C'est exactement la phrase de Frederic du 02/11 -- « les transactions
       recuperent la charge saisie sur le mandat mais qui peut changer » --
       qui decrit aujourd'hui quelque chose QUI N'EXISTE PAS. Avec la valeur de
       Hektor, elle devient vraie sans aucune ressaisie.

④ CORRIGER LES DEFAUTS B, C et D du § 5 (les deux portes qui s'ouvrent sur une
     constante, la cle du repli, l'etiquette trompeuse).

⑤ LE RATTRAPAGE HISTORIQUE : Hektor pour 2017->2026, Modelo pour 2009->2016,
     chaque ligne portant SA SOURCE. 18 830 lignes sur 24 568 (76,6 %).

⬜ A SIGNALER, PAS A CODER : 116 mandats de 2026 n'ont pas de charge chez
   Hektor -- dont 3 Actif (un EXCLUSIF a 192 400 €), 2 sous compromis, 1 Vendu.
   C'est une anomalie de SAISIE a l'agence.
   Liste : notice/CHARGE_MANQUANTE_116_MANDATS_2026-11-02.csv

⬜ NON TRANCHE : les 537 desaccords Hektor/Modelo · les 14 annonces dont les
   lignes d'honoraires se contredisent · les 38 lignes de registre sans id
   annonce (mandats de recherche) · le trou 2012-2014 (5 157 lignes, la donnee
   n'existe nulle part) · si honoraires_json existe pour les LOCATIONS et ce
   que « charge » y signifie.
```

---

## § 9. LES FICHIERS DE CE CHANTIER

```
notice/A8_AUDIT_CHARGE_DE_COMMISSION_2026-11-02.md        la cause racine du vide
notice/A9_LA_CHARGE_EST_DANS_LE_DETAIL_ANNONCE_2026-11-03.md  la source
notice/DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md   § 3 quater -> 3 octies
notice/SPEC_CHARGE_HONORAIRES_MANDAT_2026-11-02.md        le palier 1 (en prod)
notice/CHARGE_HONORAIRES_PAR_MANDAT_HEKTOR_2026-11-02.csv 10 188 mandats, Hektor
notice/CHARGE_HONORAIRES_MANDATS_DECODES_2026-11-02.csv   11 676 mandats, Modelo
notice/CHARGE_MANQUANTE_116_MANDATS_2026-11-02.csv        les 116 de 2026
supabase/patch_charge_honoraires_mandat_2026-11-02.sql    + _INVERSE, _REPETITION
```

⚠ **Ce qui est DÉJÀ en production** (palier 1, posé le 02/11 avec son accord) :
la colonne `mandat_charge_honoraires_app`, le carnet
`app_mandat_champ_app` (champ `charge_commission`), la fonction de re-pose et la
RPC de saisie. **Éprouvé sur 7 témoins, sans laisser de trace.** Il manque
**l'écran** : personne ne peut encore saisir ni voir cette valeur.
