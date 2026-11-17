# ⭐⭐⭐ LE DÉCODAGE DE LA COLONNE F DU CLASSEUR — 16/11/2026

> **Pourquoi cette note existe.** Frédéric, le 16/11 : *« cherche dans ce chantier nous
> avions découvert la colonne contient les abréviations exemple odp offre de prêt etc…
> donc audit de nouveau cherche les précédents audits sur cette colonne cela pourrait
> te faire gagner du temps »*.
>
> ⛔⛔ **J'AI CHERCHÉ, ET CE DÉCODAGE N'ÉTAIT ÉCRIT NULLE PART** : ni dans les 160
> notes de `notice/`, ni dans le plan du chantier, ni dans le journal de bord, ni dans
> la mémoire du projet. « ODP » n'apparaît dans **aucun** document du chantier
> classeur. La découverte vivait dans son souvenir, pas dans les documents — c'est
> exactement ce que le projet combat. **Cette note est là pour qu'elle ne se reperde
> pas une troisième fois.**

---

## 1. CE QUE LES AUDITS PRÉCÉDENTS DISAIENT DE F, ET LEUR ERREUR

```
A5   29/10   « En attente de » rangée avec « Tes notes de travail et les clés du
             classeur. ELLES NE NOUS REGARDENT PAS. »
A4bis 31/10  « à ne pas récupérer — vos notes et votre process », mais sans
             recommander de l'oublier. Option écrite, jamais tranchée : reprendre
             les textes EN BLOC, sans aucune interprétation.
A16  09/11   ⭐ RENVERSE le jugement en MESURANT le contenu : « le vrai contenu
             utile : LA CAUSE DES ANNULATIONS ». 383 des 896 annulations ont un
             motif identifiable. Et nomme les 4 traitements nécessaires.
```

⚠ **Aucun des trois n'a décodé les abréviations.** A16 s'est arrêté aux motifs
d'annulation — la partie répétitive — et a laissé de côté les lignes des affaires **en
cours**, qui sont écrites dans un langage abrégé.

⛔ **Et moi, le 16/11, j'ai fait pire** : j'ai classé ces lignes en « carnet de bord,
des rendez-vous et des relances, pas des clauses ». **C'était faux.** Frédéric a dû me
corriger deux fois avant que je décode.

---

## 2. LA STRUCTURE RÉELLE D'UNE LIGNE « EN COURS »

Elle est **régulière**, et les exemples la montrent mieux qu'une explication :

```
19/11 ADP30/10 PTZ ODP15/12  fact. chaudière  achat17383 DB30/1 Me Labidoire
14/12 ADP13/12 ODP13/01 DB13/2  Me Bougon / Me Besse
01/12 ADP27/11 ODP27/12 DB30/4 Me Bonnichon/Poyet relais
15/12 ADP15/12 ODP31/1 DB05/3 Me Barre 290K 25a lié 18711
30/11 DPC30/11 OPC01/3 DB15/6 Me BDH / Me Damas  18393 à archiver après vente
08/12ADP08/12 ODP08/01 DB05/02  Me Bérinchy
```

➡ **`<date> ADP<date> ODP<date> DB<date> Me <notaire> [montant durée] [renvoi]`**

**C'est un ÉCHÉANCIER DE CONDITIONS SUSPENSIVES**, pas une note libre. Et c'est
exactement ce que `app_affaire_condition` attend : `libelle`, `jours`,
`date_echeance`, `etat`, `date_levee`.

**24 lignes** portent l'échéancier complet (ADP + ODP + DB ensemble).

---

## 3. ⭐ LA MESURE QUI SÉPARE LES DEUX FAMILLES D'ABRÉVIATIONS

Le test est simple et il ne se discute pas : **l'abréviation est-elle suivie d'une
date ?** Si oui, c'est une **pièce attendue avec une échéance**. Si non, c'est une
**mention**.

```
   abrev    occurrences   suivie d'une date    part
   DB            66              66           100 %   ⭐⭐⭐ TOUJOURS
   OPC            2               2           100 %
   ODP           57              47            82 %
   ADP           41              24            59 %
   DPC           11               6            55 %
   cpmis         30               9            30 %
   PC            34              10            29 %
   copie         31               8            26 %
   ----------------------------------------------------
   Me           168               0             0 %
   PA           112               0             0 %
   pb            92               0             0 %
   BV            66               0             0 %
   CI            47               0             0 %   (1 cas, 2 %)
   BVok          37               0             0 %
   SRU           34               0             0 %
   CNI            7               0             0 %
   AVNT           3               0             0 %
```

⭐ **`DB` est à 100 % — 66 sur 66.** C'est donc certainement une date, et « date
butoir » est la lecture naturelle.

---

## 4. ⬜ LE DÉCODAGE — CE QUI EST CONFIRMÉ, CE QUI RESTE UNE HYPOTHÈSE

⛔ **Je ne décode pas seul le vocabulaire d'une agence.** Voici l'état exact :

```
CONFIRMÉ PAR FRÉDÉRIC ET MESURÉ
   ODP    offre de prêt                 (16/11)             57 fois, 82 % datée
   ADP    ATTESTATION DE DÉPÔT DE PRÊT  (17/11)             41 fois, 59 % datée

⭐⭐⭐ **ET LA MESURE DU 17/11 LE PROUVE, 24 FOIS SUR 24** : sur les 24 lignes qui
portent les deux, **ADP est TOUJOURS avant ODP, jamais l'inverse**, et l'écart médian
est de **31 jours** — le MÊME JOUR DU MOIS, un mois plus tard :

```
   ADP 27/11 -> ODP 27/12   (+31 j)      ADP 08/12 -> ODP 08/01   (+31 j)
   ADP 13/12 -> ODP 13/01   (+31 j)      ADP 30/10 -> ODP 30/11   (+31 j)
   ADP 15/11 -> ODP 15/12   (+31 j)
   ADP AVANT ODP, 1 a 45 j   20 (83 %)   46 a 120 j   4 (17 %)
   ADP le meme jour qu ODP    0           ADP APRES ODP   0  <- JAMAIS
```

➡ **C'est un DÉLAI CONTRACTUEL** : un mois pour obtenir l'offre après le dépôt du
dossier. Donc **ADP et ODP ne sont PAS deux conditions** : ce sont le **DÉPART** et
l'**ÉCHÉANCE** de la même clause « Obtention Crédit », qui existe déjà au catalogue
(id 2, `jours_defaut` 45 — alors que le classeur montre **31 jours** en pratique).

⛔ **ET MA MESURE DU 16/11 ÉTAIT FAUSSE** : j'avais écrit « 10 lignes dans l'ordre,
14 hors ordre ». Elle mélangeait DB dans le test et ne gérait pas le passage au
1ᵉʳ janvier. Corrigée le 17/11.

HYPOTHÈSE À CONFIRMER -- la mesure dit qu'elles portent une date,
elle ne dit pas ce que les lettres veulent dire
   DB     DATE BUTOIR -- ⬜ VA EN NOTE (sa decision du 17/11)  66 fois, 100 % datée
          ⭐ MESURE : elle vaut « Vente Prevue » (colonne V) dans **60 cas sur
            65** (92 %). Nous l'avons donc DEJA. 4 divergent, 1 V est vide.
            ➡ ce n'est pas une condition : c'est l'echeance du compromis.
   DPC    dépôt ou déclaration de permis de construire ?     11 fois, 55 % datée
   OPC    obtention du permis de construire ?                 2 fois, 100 % datée
   PC     permis de construire                               34 fois, 29 % datée
   cpmis  compromis                                          30 fois, 30 % datée
   copie  copie d'une pièce reçue                            31 fois, 26 % datée

MENTIONS, jamais datées
   Me     Maître -- le notaire (« Me Chalet », « Me Bougon »)   168 fois
   PA     permis d'aménager ?                                  112 fois
   pb     problème (« pb infiltrations cave », « pb amiante »)   92 fois
   BV     bon de visite ?        BVok = bon de visite reçu ?      66 / 37 fois
   CI     ?                                                       47 fois
   SRU    le délai légal de rétractation                           34 fois
   CNI    carte nationale d'identité                                7 fois
   AVNT   avenant ?                                                 3 fois
   dossOk dossier complet ?
```

⚠ **CE QUE JE N'AI PAS PU ÉTABLIR** : l'ordre des échéances. Sur les 24 lignes
mesurables, **10 sont dans l'ordre `ADP ≤ ODP ≤ DB` et 14 ne le sont pas**. Mon test
est fragile — les dates du classeur ne portent pas d'année, donc un passage au 1ᵉʳ
janvier le casse. **Je n'affirme donc aucune règle d'ordre.**

---

## 5. ⭐⭐ LA LECTURE JUSTE DE F, ENFIN — ET ELLE EST TRIPLE

```
   708 lignes   l'affaire est TOMBEE (Annulée)
                -> LE MOTIF : refus prêt 59 . rétractation écrite 17 .
                   rétractation acq 16 . SRU 24 . annulé 18 . trop de travaux 5
                -> destination : motif_annulation_app  (VIDE aujourd'hui)
                ⭐ et 357 de ces motifs tombent sur les 450 dates posées le 16/11
                   par C3 : le « quand » et le « pourquoi » enfin réunis

    86 lignes   l'affaire est EN COURS
                -> LA CONDITION EN ATTENTE, avec sa pièce et son échéance
                -> destination : app_affaire_condition
                   (libelle + date_echeance + etat), 5 lignes aujourd'hui

    82 lignes   l'affaire est RÉGLÉE
                -> remarques d'après-vente : « V pb après vente » 14,
                   « protocole » 4, « vente directe » 4, « PTZ » 2
                -> destination : app_affaire_note
```

Et le tri général de la colonne, mesuré le 16/11 :

```
   3 100 cases de F remplies
      1 537  « V » seul = VENDU (déjà connu)          -> ECARTE
        876  clause ou motif                          -> les trois familles ci-dessus
        427  pictogramme seul                         -> ECARTE
        232  financement (« 260K 25a », « relais »)   -> remplit `jours`, pas `libelle`
         28  prénom derrière un V                     -> ECARTE
   et G porte 4 132 commentaires libres               -> app_affaire_note
```

---

## 6. ⚠ LES PICTOGRAMMES, SÉPARÉS DU TEXTE (traitement ① de A16)

```
   🟢  560   LARGE GREEN CIRCLE        -> « Vente réglée » à 96 % (A16)
   🅿  382   SQUARED LATIN CAPITAL P   -> suit le FINANCEMENT, pas un état (64 %)
   💰  172   MONEY BAG                 -> le texte porte le montant et la durée du prêt
   🔴  154   LARGE RED CIRCLE          -> « Annulée » à 99 % (A16)
   +   114   PLUS SIGN
   🏡   30   HOUSE WITH GARDEN         -> aucune piste
   ❗   16   HEAVY EXCLAMATION MARK
```

⛔ **Et un script naïf MEURT sur ces caractères** (vu le 05/11). Le script de mesure
les reconnaît par leur **catégorie Unicode**, jamais par une liste — une liste oublie
toujours le caractère suivant.

---

## 7. ⛔ CE QUE F NE CONTIENT PAS, ET QUI MANQUE DONC PARTOUT

F ne dit **jamais** « condition suspensive de prêt » comme un libellé de clause. Il dit
`ODP15/12` — la pièce et sa date — ou `refus prêt` après coup. **Le catalogue des
clauses types n'existe nulle part** : ni au classeur, ni chez Hektor (0 condition
suspensive sur 18 589 lignes de `app_affaire_console`).

➡ `app_condition_catalogue` porte **2 lignes** aujourd'hui, et il devra être **écrit à
la main** à partir de ce décodage : offre de prêt, accord de prêt, permis de
construire, délai SRU, bon de visite…

---

## LES FICHIERS DE MESURE

```
notice/C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv   les 3 100 cases, une par ligne :
   le brut, le pictogramme séparé, le texte seul, la famille, l'état de l'affaire
notice/C4_CATALOGUE_PROPOSE_2026-11-16.csv             les regroupements, par fréquence,
   avec la part « Annulée » de chacun
phase2/checks/c4_mesurer_les_clauses_2026-11-16.py     le script, LECTURE SEULE
```
