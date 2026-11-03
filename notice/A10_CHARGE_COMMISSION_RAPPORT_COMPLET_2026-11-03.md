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

> ⭐⭐⭐ **CORRIGÉ LE 03/11 APRÈS-MIDI — et la correction vient d'une question de
> Frédéric** : *« dans Hektor il y a deux questions sur le mandat : Honoraires
> charge Acquéreur Oui/Non, Honoraires charge Vendeur Oui »*. **Il avait raison, et
> ce rapport ne connaissait qu'UNE des deux sources.** Trois chiffres de la
> première version sont donc faux, et ils sont corrigés sur place :
>
> • la couverture n'est pas **76,6 %** mais **98,4 %** ;
> • le « trou 2012-2014 » **n'existe pas** (99 % couvert) ;
> • l'export Modelo **ne sert plus** : Hektor couvre tout seul 2009→2026.
>
> ⛔ Et une structure que j'avais mal lue : `honoraires_json` est un **HISTORIQUE**
> (six lignes pour un seul mandat), pas une valeur. Voir § 2 bis.

## § 1. LA RÉPONSE EN UNE PAGE

```
AVONS-NOUS LA CHARGE ?

  SUR LES MANDATS     oui, a 98,4 %  --  mais INVISIBLE a l'ecran
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
  valeurs rencontrees : « vendeur » 62 573 LIGNES · « Acheteur » 19 352
  ⛔ CE SONT DES LIGNES, PAS DES ANNONCES -- et une annonce en porte SIX.
     Par annonce, derniere ligne : 11 044 vendeur · 3 260 acquereur.
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
LA COUVERTURE VRAIE -- LES DEUX SOURCES DE HEKTOR (corrige le 03/11)

Source A  honoraires_json.charge          14 304 annonces
Source B  « Honoraires vendeur ou bailleur montant »   dans raw_json
          « Honoraires acquereur ou locataire »        dans raw_json
                                           31 259 annonces  (+18 570)
Les deux sources s'accordent a 99,7 % (12 116 accords, 40 desaccords).

sur les 27 148 lignes de hektor_mandat, par annee de DEBUT :

annee   lignes  couvert      %     dont source A / source B
2009        96       90   93,8 %        60   /    30
2010       371      358   96,5 %        98   /   260
2011     2 893    2 883   99,7 %       335   / 2 548
2012     2 480    2 459   99,2 %       415   / 2 044
2013     2 648    2 623   99,1 %       348   / 2 275
2014     2 474    2 460   99,4 %       290   / 2 170
2015     1 992    1 960   98,4 %       231   / 1 729
2016     1 980    1 962   99,1 %       202   / 1 760
2017     1 867    1 831   98,1 %       838   /   993
2018     1 641    1 618   98,6 %     1 444   /   174
2019     1 499    1 492   99,5 %     1 438   /    54
2020     1 233    1 215   98,5 %     1 066   /   149
2021     1 216    1 185   97,5 %     1 054   /   131
2022     1 131    1 108   98,0 %     1 038   /    70
2023     1 096    1 080   98,5 %     1 022   /    58
2024       942      915   97,1 %       880   /    35
2025       912      879   96,4 %       874   /     5
2026       674      592   87,8 %       591   /     1
TOTAL   27 148   26 713   98,4 %

verdict sur les 32 874 annonces couvertes : 29 614 vendeur · 3 260 acquereur
⭐ ET 533 ANNONCES PORTENT LES DEUX CASES A LA FOIS :
     VENDEUR seul 28 182 · ACQUEREUR seul 2 544 · LES DEUX 533 · aucun 30 211
   520 de ces 533 sont rangees « acheteur » par la source A, qui n'a qu'UNE
   valeur : elle PERD l'information. La colonne devra pouvoir dire « les deux ».
```

**Les deux sources de HEKTOR sont complémentaires, pas concurrentes** : les deux
cases du mandat tiennent 2009→2017, le bloc honoraires_json tient 2017→2026.
Toutes les années sont au-dessus de **93 %**, sauf 2026 à 87,8 % (saisie en cours).

⛔⛔ **L'EXPORT MODELO NE SERT PLUS** : la première version de ce rapport s'appuyait
sur lui pour 2009→2016. Hektor couvre ces années à **96-99 %** tout seul. Le
fichier reste utile comme **témoin de contrôle**, plus comme source.

### ⛔⛔ LE TROU 2012-2014 N'EXISTE PAS — corrigé le 03/11 après-midi

```
les 6 494 lignes de 2012-2014 :
   detail present mais honoraires VIDE        6 490   (99,9 %)
   honoraires renseigne                           4   ( 0,1 %)

TEMOIN INVERSE, les 1 434 lignes de 2019 :
   honoraires RENSEIGNE                       1 377   (96,0 %)
   detail present mais honoraires vide           57   ( 4,0 %)
```

⭐ Donc **ce n'est pas un défaut de notre lecture** : le détail descend bien, et
**Hektor n'a pas les honoraires de ces années DANS CE BLOC-LÀ.**

⛔⛔ **MAIS IL LES A AILLEURS, ET J'AVAIS CONCLU TROP VITE.** La mesure du 03/11
après-midi, sur la seconde source : **2012 à 99,2 %, 2013 à 99,1 %, 2014 à
99,4 %**. Ce sont les deux cases du mandat qui portent la donnée — 2 044,
2 275 et 2 170 lignes contre 415, 348 et 290 pour le premier bloc.

⭐ **La leçon** : mon témoin inverse était juste, et ma conclusion fausse. Le
témoin prouvait que `honoraires_json` est vide pour ces années ; j'en ai déduit
que **la donnée** était absente. Un bloc vide ne dit rien des autres blocs.
C'est [[un-zero-ne-se-croit-pas-sans-temoin-positif]] à l'échelle d'une SOURCE :
il fallait chercher un témoin positif **ailleurs que dans le champ mesuré**.
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

## § 8. LE DÉROULÉ DU CHANTIER — et quand le registre sera complet

### ⭐⭐⭐ LA RÉPONSE À « QUAND » : À LA PREMIÈRE NUIT. Et voici pourquoi.

**Trois mesures du 03/11, et elles rendent le chantier court :**

```
1. L EXPORTEUR DU REGISTRE LIT DEJA LE DETAIL
      phase2/sync/mandat_ledger.py:750
      "SELECT hektor_annonce_id, mandats_json FROM hektor.hektor_annonce_detail"
   -> il faut ELARGIR ce SELECT a honoraires_json et raw_json. Rien de neuf.

2. LE MECANISME D AJOUT DE COLONNE EXISTE DEJA
      phase2/sync/mandat_ledger.py:448  _ajouter_colonne_si_absente()
   -> une ligne de plus, comme pour origine et offre_type.

3. LE RUN DE NUIT L APPELLE DEJA, CHAQUE NUIT
      run_full_pipeline.ps1:1113   "phase2\sync\mandat_ledger.py"
```

⭐⭐ **Donc AUCUN rattrapage n'est nécessaire, et aucun appel à Hektor non plus.**
Les 61 470 lignes de détail sont **déjà dans notre miroir local**. L'exporteur
relit **tout** le registre à chaque passage. Donc **la nuit qui suit la pose, les
26 713 lignes portent leur charge** — historique compris, 2009 inclus.

⚠ **Ce que ça ne couvre pas** : les 435 lignes (1,6 %) dont aucune des deux
sources ne parle, et les 82 mandats de 2026 à charge non saisie à l'agence.
Celles-là attendent une **saisie humaine**, pas un rattrapage.

---

### ⭐⭐ LE COÛT SUR LE RUN DE NUIT — mesuré le 03/11, question de Frédéric

*« le volume de lignes va pas planter le run de nuit ? »* — la bonne question, et
`raw_json` est effectivement un gros blob. **Chronométré pour de vrai, pas estimé.**

```
CE QU IL Y A A LIRE :
   61 470 lignes de detail
   raw_json         775,4 Mo   (moyenne 12,6 Ko, max 92,5 Ko)
   mandats_json      11,75 Mo  <- ce que le run lit DEJA
   honoraires_json    4,62 Mo

LES TROIS FACONS DE LIRE, CHRONOMETREES :
   aujourd hui (mandats_json seul)                 0,18 s
   A  tout raw_json + les 2 regex en Python        5,64 s   (x30)
   B  filtre SQL en amont (LIKE), 40 484 lignes    3,58 s
   C  extraction COTE BASE (instr + substr)        2,14 s   <- RECOMMANDEE

CE QUE CA PESE DANS LE RUN REEL (journal du 03/11) :
   etape « phase2 registre des mandats »   05:56:50 -> 05:58:01   =  71 s
   le run entier                           04:00:01 -> 06:18:23   = 2 h 18
   la descente suit a 06:45                -> 27 MINUTES DE MARGE

   option A : +5,64 s  =  +8 % sur l etape,  +0,07 % sur le run
   option C : +2,14 s  =  +3 % sur l etape,  +0,03 % sur le run
```

✅ **Verdict : non, ça ne plantera pas.** Cinq secondes sur un run de deux heures
dix-huit, avec vingt-sept minutes de marge avant la descente.

⭐ **Et le débit mesuré écarte le soupçon du cache chaud** : 775 Mo en 5,64 s font
**137 Mo/s**, un débit de SSD. Un cache mémoire aurait donné plusieurs Go/s. La
mesure n'est donc pas flattée par mes lectures précédentes. ⚠ Ce n'est pas une
preuve absolue — c'est un indice fort.

⛔⛔ **LES DEUX PIÈGES À TENIR, et ils sont dans l'écriture du code :**

```
1. JAMAIS DE fetchall() SUR raw_json -- ce serait 775 Mo en memoire d un coup.
   On itere au curseur, ligne par ligne, comme le fait deja mandat_ledger.

2. L OPTION C NE REMONTE QUE ~130 CARACTERES PAR LIGNE au lieu de 12,6 Ko :
      substr(raw_json, instr(raw_json, 'onoraires vendeur ou bailleur montant'), 60)
   SQLite fait l extraction, Python ne voit jamais le blob. C est ce qui
   divise le temps par deux ET supprime le risque memoire.
   ⚠ Mais elle depend d un LIBELLE. Si Hektor le change, le champ devient
     muet SANS ERREUR -> il faut une SENTINELLE sur le compte (40 484 lignes
     aujourd hui) qui crie si le nombre s effondre.
```

⚠ **Le push ne bouge pas** : deux colonnes TEXT courtes sur 27 464 lignes font
environ **300 Ko de plus**, sur un push qui dure déjà 5 min 01 (05:59:10 →
06:04:11). Aucune ligne nouvelle n'est créée, seulement deux champs par ligne.

---

### LE DÉROULÉ, ÉTAPE PAR ÉTAPE

```
ETAPE 1  LIRE LA CHARGE, ET LA POSER AU REGISTRE LOCAL            ~1/2 journee
  ou   phase2/sync/mandat_ledger.py
  quoi . elargir le SELECT de la l. 750 : + honoraires_json, + raw_json
       . une fonction charge_du_mandat(detail) qui rend un mot et SA SOURCE :
             "vendeur" | "acquereur" | "les_deux" | ""
             source : "cases_mandat" | "honoraires_json" | ""
         PRECEDENCE : les deux cases d'abord (98,4 %), honoraires_json en appoint
       . sur honoraires_json : prendre LA DERNIERE LIGNE (id max), jamais la 1re
       . deux colonnes neuves via _ajouter_colonne_si_absente :
             mandat_charge_honoraires_hektor   TEXT
             mandat_charge_honoraires_source   TEXT
  risque RIEN n'est ecrase : deux colonnes NEUVES a cote de la saisie humaine
         mandat_charge_honoraires_app, qui vit dans app_mandat_champ_app et que
         le push ne touche pas (patron de la date de cloture, 13/10).
  preuve a blanc d'abord : compter les lignes remplies par annee SANS ecrire,
         et retrouver 26 713 / 27 148. Temoin positif nomme : le mandat 18836.

ETAPE 2  LA POUSSER AU CLOUD                                      ~1 heure
  ou   supabase : ALTER TABLE app_mandat_register ADD COLUMN (x2)
       + patch, _INVERSE et _REPETITION, comme les 8 precedents
  quoi la colonne descend toute seule : lignes_a_pousser() fait SELECT *
       (mandat_ledger.py:1123) et _retirer_colonnes_absentes_du_cloud l. 1166
       ECARTE une colonne que le cloud n'a pas -- donc poser le SQL AVANT.
  ⛔ ACCORD OBLIGATOIRE : ecriture en base de production.

ETAPE 3  L AFFICHER                                               ~1/2 journee
  ou   apps/hektor-v1/src/App.tsx (fiche mandat + registre V3)
  quoi . la valeur, avec SA SOURCE en clair : « saisi par l'agence » /
         « vu chez Hektor » -- une valeur sans provenance n'est pas crue
       . precedence : la saisie humaine d'abord, Hektor en repli
       . traduire : Hektor dit « Acheteur », on affiche « Acquereur »
       . le cas « les deux » a son propre libelle (533 annonces)
  preuve npm run build, puis l'ecran EN LIGNE sur un bien nomme a l'avance.
       ⚠ Et le TELEPHONE : le rendu mobile est un composant separe.

ETAPE 4  LES TROIS DEFAUTS DU § 5                                 ~1/2 journee
  B  App.tsx:4571  honorairesCharge: 'mandant' EN DUR -> lire la vraie valeur
     (18 PDF concernes, aucun depuis le 24/07 : impact faible, enjeu fort --
      c'est le document que le client SIGNE)
  C  App.tsx:4543  le repli cherche montant_ttc/montant : CODE MORT, les vraies
     cles sont id/taux/charge
  D  App.tsx:30778 l'etiquette « Honoraires acquereur » -> la clarifier
     ⚠ Hektor l'appelle AINSI lui-meme (son formulaire d'offre) : c'est une
       clarification de NOTRE cote, pas la correction d'une erreur.

ETAPE 5  LA TRANSACTION HERITE DE SON MANDAT                      ~1 journee
  quoi . l'offre nait avec la charge de SON mandat (meme couple numero+annonce),
         marquee « reprise du mandat », modifiable au compromis
       . ET le defaut A : la modale n'enregistre QUE si on touche le menu
         -> enregistrer la valeur AFFICHEE, touchee ou pas
  ⛔ LE GARDE-FOU, ecrit juste a cote dans le code (lecon du 08/09) : « en
     reprise, un champ prerempli n'est PAS une intention » -- sale_price portait
     LE PRIX DE L'ANNONCE (180 000) que personne n'avait tape. D'ou le marquage
     de la SOURCE : on doit toujours savoir qui a dit la valeur.
  ⛔ ACCORD OBLIGATOIRE : ecriture chez Hektor.
```

### ⭐ L'ORDRE QUE JE RECOMMANDE

**Étapes 1 → 2 → 3 d'abord**, ensemble. C'est le patron déjà éprouvé, rien n'est
détruit, et ça fait apparaître **98,4 % de l'information d'un coup, en une nuit**.
L'étape 4 peut suivre immédiatement : trois corrections indépendantes.
L'étape 5 vient **après** que tu aies vu la donnée à l'écran et jugée juste.

### ⬜ CE QUI RESTE NON TRANCHÉ

```
⬜ LES 533 « LES DEUX » : beaucoup portent LE MEME montant des deux cotes
   (3 600/3 600, 7 100/7 100) -> saisie en double plutot que vrai partage ;
   d'autres diffèrent vraiment (4 000/3 665, 10 000/504). A regarder.
⬜ OUI/NON ou MONTANT ? Chez nous ce sont des MONTANTS. Une case cochee « Oui »
   SANS montant serait invisible. NON MESURE -- il faut voir l'ecran du mandat.
⬜ les 38 lignes de registre sans id annonce (mandats de recherche)
⬜ si ces champs existent pour les LOCATIONS, et ce que « charge » y signifie
⬜ A SIGNALER, PAS A CODER : 82 mandats de 2026 sans charge chez Hektor --
   anomalie de SAISIE a l'agence, pas un defaut technique.
✅ TOMBES depuis la 1re version : le trou 2012-2014 · les 537 desaccords
   Hektor/Modelo (Modelo ne sert plus) · les 14 « contradictions » (ce sont des
   bascules dans le temps, la derniere ligne tranche).
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
