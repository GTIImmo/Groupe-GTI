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
   DPC    DEPOT du permis de construire ✅ CONFIRME 17/11    11 fois, 55 % datée
   OPC    OBTENTION du permis ✅ CONFIRME 17/11               2 fois, 100 % datée
   PC     permis de construire                               34 fois, 29 % datée
   cpmis  compromis                                          30 fois, 30 % datée
   copie  copie d'une pièce reçue                            31 fois, 26 % datée

MENTIONS, jamais datées
   Me     Maître -- le notaire (« Me Chalet », « Me Bougon »)   168 fois
   PA     PERMIS D'AMENAGER           ✅ CONFIRME PAR LUI 17/11     112 fois
   pb     problème (« pb infiltrations cave », « pb amiante »)   92 fois
   BV     bon de visite ?        BVok = bon de visite reçu ?      66 / 37 fois
   CI     CARTE D'IDENTITE attendue   ✅ CONFIRME PAR LUI 17/11      47 fois
   SRU    le délai légal de rétractation                           34 fois
   CNI    carte nationale d'identité                                7 fois
   AVNT   avenant ?                                                 3 fois
   dossOk dossier complet ?
```

✅⭐⭐ **QUATRE SIGNES CONFIRMES PAR LUI LE 17/11**, et ils ne sont plus des
hypotheses : `DPC` = **DEPOT** du permis de construire · `OPC` = **OBTENTION** du
permis · `CI` = **carte d'identite attendue** · `PA` = **permis d'amenager**.

⭐⭐ **ET UNE TROUVAILLE EN PASSANT** : `CNI` etait deja decode « carte nationale
d'identite » (7 fois) -- donc **`CI` et `CNI` sont DEUX ECRITURES DE LA MEME
ATTENTE**, et elle revient **54 fois** (47 + 7), pas 47. Deux lignes du meme tableau
disaient la meme chose sans se reconnaitre.

⬜ **RESTE A CONFIRMER** : `BVok`, `AVNT`, `dossOk`, `cpmis`, `copie`.

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

## 8. ⛔⛔ CE VERDICT A ETE RENVERSE LE JOUR MEME -- VOIR LA SECTION 9

> ⛔ **CE QUI SUIT EST CONSERVE PARCE QU'IL EXPLIQUE UNE FAUTE DE RAISONNEMENT**, pas
> parce qu'il est vrai. J'ai bloque les 86 lignes au nom de sa regle du chantier ; il
> a repondu : **« MA REGLE SUR LES DONNEES DES TRANSACTIONS EN COURS NE PORTAIT PAS
> SUR LES NOTES »**, et la mesure lui a donne raison. Le verdict juste est en
> section 9.

## 8bis. ⛔ L'ANCIEN VERDICT (FAUX) : « LES 86 CONDITIONS NE SE RAPATRIENT PAS »

La section 5 annoncait les 86 lignes « en cours » comme destinees a
`app_affaire_condition`. **L'audit du 17/11 dit NON**, et c'est sa propre regle du
chantier qui le dit : *« on ne reprend que ce que Hektor ne rendra plus : le bien est
SORTI du parc vivant, OU la date a plus d'un an. Et JAMAIS une date dans le futur. »*

```
   89 abreviations datees -> 0 POSABLE
      71  echeance DANS LE FUTUR          <- sa regle l interdit
       9  echeance indatable (pas d ancre)
       8  affaire ENCORE VIVANTE et recente
       1  un DB, qui va en note par sa decision du 17/11
```

⛔⛔ **ET LE ZERO EST VRAI, PROUVE PAR TROIS TEMOINS POSITIFS** -- on relache une
seule condition a la fois pour verifier que le filtre sait dire OUI : sans (b) il laisse
passer **38**, sans (c) **9**, sans la reserve DB/DPC/OPC **1**.

⭐⭐⭐ **LA RAISON, EN UNE PHRASE** : une affaire « en cours » du classeur est **le
PRESENT**, pas de l'historique. Chez nous, **42** ont un compromis ACTIF, **38** n'ont
qu'une offre, **5** ne sont reliees a rien, et **1 seule** est tombee depuis. Les
echeances sont dans le futur parce qu'elles courent encore.

➡ Ces conditions relevent du **DEVELOPPEMENT** (la saisie dans l'app), pas du
rapatriement. `app_affaire_condition` porte 5 lignes, toutes `origine = 'saisie'`, et
**aucune ne porte de `date_echeance`** : l'ecran pose le libelle et les `jours`.

### ⛔⛔ LE TROU TROUVE EN PASSANT : 47 TEXTES NE SONT NULLE PART

Le generateur de notes du 2e patch ne prend `F` que pour les etats **« Annulée »** et
**« Vente réglée »**, plus la date butoir. Une ligne « en cours » **sans `DB`** n'est
donc partie nulle part :

```
   parties en note par leur DB               39
   parties en note par leur colonne G         0   (aucune de ces 86 n a de G)
   ⛔ NULLE PART, ni note ni condition       47
```

Et c'est **le carnet de bord vivant de l'agence** : « 23/11 copie C20/11 Me Latour »,
« 17/11 att. fonds notaire V », « 20/11 accord transfert fonds Binga-Hanto »,
« 19/11 rdv PUA accord du juge habilitation Sauret ».

⬜ **A TRANCHER PAR LUI.** ⚠ Reserve a dire : ce suivi **bouge chaque semaine**, donc
le poser, c'est figer une photo.

### ⭐⭐ DEUX SIGNES QUE LA SECTION 4 NE CONNAISSAIT PAS

```
   C<date>   la date du COMPROMIS prevu. « copie C20/11 » = copie recue, compromis
             le 20/11. Elle revient dans 20 des 47 textes orphelins.
   DP<date>  vu dans « 16/12 dDP16/12ADP ODP05/1 DP31/1 31/3 » -- ni DPC, ni ODP.
```

⛔ **Mes cinq abreviations datees (ADP, ODP, DPC, OPC, DB) ne les connaissaient pas.**
Ce decodage n'est donc pas complet, et il ne pretend pas l'etre.

### LE FICHIER DE L'AUDIT

```
phase2/checks/c4_auditer_les_86_conditions_2026-11-17.py   LECTURE SEULE, 9 mesures
notice/C4_LES_86_CONDITIONS_AUDIT_2026-11-17.csv           les 89 abreviations, une
   par ligne : etat au classeur, etat chez nous, echeance ancree, et POURQUOI
```

---

## 9. ✅⭐⭐⭐ LE VERDICT JUSTE -- 80 TEXTES ET 28 CONDITIONS, 17/11

### ⭐⭐⭐ POURQUOI SA REGLE NE S'APPLIQUAIT PAS

Sa regle protege contre **LE CONFLIT** : ne pas poser a la main une valeur que le run
de nuit ecrasera, ou qui contredira Hektor. La bonne question n'est donc pas
« l'affaire est-elle en cours ? » mais **« HEKTOR PORTE-T-IL CETTE DONNEE ? »**.

```
   une NOTE                   Hektor n en a AUCUNE, nulle part
   une CONDITION SUSPENSIVE   app_affaire_console.conditions_suspensives
                              est REMPLIE 0 FOIS SUR 18 591
                              (il ne rend qu un CATALOGUE de 2 choix, 17 lignes)
```

➡ Aucun ecrasement possible, aucune contradiction possible. **Sa regle n'avait rien a
proteger ici**, que l'affaire soit vivante ou morte.

### ⛔⛔ ET MON « 47 TEXTES PERDUS » ETAIT FAUX : ILS SONT 80

```
   1  `entetes.index("G")` -- « G » est la LETTRE de la 7e colonne (entete
      « COMMENTAIRES »), pas un nom d entete. La recherche echouait -> « 0 ligne
      sauvee par sa colonne G » : UN ZERO PAR CONSTRUCTION. Et le projet a
      index_de() depuis le 16/11 : je ne l ai pas utilisee.
   2  Et meme corrigee, « la ligne a-t-elle un G ? » NE REPOND PAS A LA QUESTION :
      une ligne avec un G a bien une note, mais cette note porte LE COMMENTAIRE DE
      G, PAS LE TEXTE DE F. Deux textes differents, confondus.
```

⭐⭐⭐ **LE SEUL CRITERE HONNETE** : le texte de F est-il, **mot pour mot**, dans la
note de sa transaction ?

```
   le texte de F EST dans la note         1
   il N Y EST PAS                        80   <- le lot 1
   aucune transaction reliee              5
   -------------------------------------------
                                         86
```

⛔⛔ **ET LE TEMOIN DE LA METHODE** : sur 60 lignes **annulees** dont F *est* posee par
le 2e patch, la comparaison en retrouve **28**. Elle sait donc dire OUI -- les
80 absences sont **vraies**.

### ⭐⭐ LE LOT 1 EST UN COMPLEMENT, ET C'EST LA CLE PRIMAIRE QUI LE COMMANDE

`app_affaire_note` a pour clef **`app_affaire_id` SEUL**, et **81** des transactions
visees portent deja une note : on ne peut pas en creer une seconde.

```
   on AJOUTE un paragraphe marque « [classeur F, suivi en cours au 17/11/2026] »
   l UPDATE est IDEMPOTENT         -> rejoue, il n ajoute pas deux fois
   une SAUVEGARDE DATEE garde le texte d avant
   le PATCH *et* l INVERSE controlent que le texte d origine est toujours la
   ⛔ l ORIGINE des notes completees NE BOUGE PAS -- sinon les controles des
     4 325 notes du 2e patch deviendraient faux. La marque est le PREFIXE.
```

### ✅⭐⭐⭐ LE CATALOGUE PASSE A SIX CLAUSES -- SA DECISION DU 17/11

« je veux que DPC/OPC c'est bien le depot et l'obtention du permis devienne deux
conditions suspensives en + ».

```
   1  Preemption mairie                    0 j   <- de Hektor
   2  Obtention Credit                    45 j   <- de Hektor
   3  Permis de construire                 0 j   <- pose le 17/11 (motif « refus PC »)
   4  Delai de retractation SRU           10 j   <- pose le 17/11
   5  Depot du permis de construire        0 j   <- NEUVE, le depot est un ACTE
   6  Obtention du permis de construire   91 j   <- NEUVE
```

⭐⭐ **ET LES 91 JOURS SONT MESURES, PAS INVENTES** : sur les 2 lignes du classeur qui
portent `DPC` **et** `OPC`, l'ecart est de **90 et 91 jours** -- exactement les 3 mois
d'instruction d'un permis de construire.

⚠ **UNE REDONDANCE, DITE ET NON CACHEE** : « Permis de construire » (id 3) reste au
catalogue. Les deux clauses neuves en sont les **deux etapes**, pas un remplacement --
un compromis attend le depot, PUIS l'obtention.

### ✅ LES 28 CONDITIONS POSEES

```
   ODP -> « Obtention Credit »                     23
   DPC -> « Depot du permis de construire »         3
   OPC -> « Obtention du permis de construire »     2
   -----------------------------------------------------
                                                   28
   le delai ADP->ODP, mesure ligne par ligne : de 30 a 60 jours, median 36
   les echeances : 17 en 2026, 11 en 2027 . deja passees 3, a venir 25
   ECARTEES : 3 ODP dont la chaine n a pas UN SEUL compromis
```

⭐ **ETAT TOUJOURS `attente`, JAMAIS `levee`** : on affirme « attendue a cette date »,
ce que le classeur dit, et rien de plus. **L'ecran reste maitre** : la saisie d'un
humain ecrasera la notre, pas l'inverse.

### LES FICHIERS

```
phase2/checks/c4_le_texte_de_f_est_il_vraiment_pose_2026-11-17.py   le bon critere
phase2/checks/c4_generer_lots_1_et_2_2026-11-17.py                  le generateur
supabase/patch_c4_lots_1_et_2_2026-11-17.sql                        le patch
supabase/patch_c4_lots_1_et_2_2026-11-17_INVERSE.sql                le retour arriere
supabase/patch_c4_lots_1_et_2_2026-11-17_REPETITION.sql             les controles
notice/C4_TEXTE_DE_F_NON_POSE_2026-11-17.csv                        les 80, une par ligne
notice/C4_LOTS_1_ET_2_2026-11-17.csv                                tout ce qui est pose
⭐ les trois patchs sont en LF PUR (0 retour chariot, verifie AVANT d ecrire) --
  lecon 30 : un patch est COLLE, un CR egare y fait des degats.
```

---

## LES FICHIERS DE MESURE

```
notice/C4_LES_CLAUSES_DE_LA_COLONNE_F_2026-11-16.csv   les 3 100 cases, une par ligne :
   le brut, le pictogramme séparé, le texte seul, la famille, l'état de l'affaire
notice/C4_CATALOGUE_PROPOSE_2026-11-16.csv             les regroupements, par fréquence,
   avec la part « Annulée » de chacun
phase2/checks/c4_mesurer_les_clauses_2026-11-16.py     le script, LECTURE SEULE
```
