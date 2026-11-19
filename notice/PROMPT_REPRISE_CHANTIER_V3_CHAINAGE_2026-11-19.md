# ⭐⭐⭐ REPRISE DU CHANTIER CLASSEUR — V3, PAR LE CHAÎNAGE
### Dossier écrit le 19/11/2026 par la conversation qui tient le chantier

> ⛔⛔⛔ **QUI TIENT LE CHANTIER.** Le chantier classeur est conduit par **cette**
> conversation, et c'est d'elle que tu prends la suite. **Deux AUTRES sessions**, en
> parallèle, ont produit **des pièces versées au chantier, pas la conduite du chantier** :
> un rapport d'audit et un patch le 18/11, un second audit et un patch affiné le 19/11.
> **Aucun des deux patchs n'a jamais été joué.** Ils se vérifient, ils ne se recopient pas.
>
> ⭐⭐ **ET L'ORDRE A CHANGÉ, SUR DEMANDE DE FRÉDÉRIC (19/11) :** *« mon projet a une chaîne
> de transactions qui peut bouger toutes les nuits, c'est ce chaînage que je voulais
> améliorer, et ensuite oui il y a le gel qui lie ces chaînes aux lignes du Sheet »*.
> **Le chaînage est le socle. Le gel vient par-dessus.** Les deux sessions précédentes ont
> travaillé uniquement sur le gel ; aucune n'a touché au chaînage.

---

## 0. ⭐⭐⭐ LE PROMPT À COLLER DANS LA CONVERSATION NEUVE

```
Tu reprends le chantier classeur du projet Hektor (depot C:\Hektor\Projet).

C'EST CE CHANTIER-LA QUE TU REPRENDS, celui conduit par la conversation qui a ecrit le
dossier ci-dessous. DEUX AUTRES sessions ont seulement produit DES PIECES : un rapport
d'audit + un patch du gel (18/11), un second audit + un patch AFFINE (19/11). Aucun des
deux patchs n'a ete joue. Elles se verifient, elles ne se recopient pas.

AVANT TOUT : lis notice/PROMPT_REPRISE_CHANTIER_V3_CHAINAGE_2026-11-19.md EN ENTIER,
puis les sept pieces qu'il liste au paragraphe 2, dans l'ordre qu'il donne.

LE BUT DU CHANTIER, EN DEUX LIGNES : (1) le classeur Google Sheet FAIT FOI, on met notre
base en conformite avec lui -- il remplit les vides ET corrige les divergences ;
(2) puis LA BASCULE : on saisit dans l'app, plus dans le classeur. Le classeur ne ferme
pas, il change d'ecrivain.

LA CHAINE DE CORRESPONDANCE, et c'est la clef de tout :
    ligne du Sheet --(LE GEL, app_classeur_lien)--> numero de transaction (ne bouge jamais)
    transaction ----(LE CHAINAGE, rededuit CHAQUE NUIT)--> le dossier --> l'etiquette
    etiquette (app_dossier_uuid) --(etape 5.2)--> la colonne affair_uuid du Sheet
Le gel est un ECHAFAUDAGE : il sert une fois de plus, pour l'etape 5.2, puis il dort.
Le CHAINAGE, lui, est le MUR : il est rededuit chaque nuit et il peut bouger.

TA MISSION, DANS CET ORDRE, ET IL NE S'INVERSE PAS.

TEMPS 1 -- L'ETAT DU CHAINAGE DES TRANSACTIONS. Tu l'audites pour lui-meme, avant tout
le reste. Tu t'appuies sur les rapports existants (ils portent des mesures reelles) MAIS
tu remesures : ils se trompent tous les deux sur la cause, et le paragraphe 5 du dossier
dit ou. Tu regardes en priorite LES CHAINES TOUCHEES PAR NOS PROPRES SCRIPTS DE MASSE --
le refus des offres mortes du 11/11 (1 166 offres) et les 136 transactions creees depuis
le Sheet le 18/11 (138 scissions la meme nuit). ⛔ ATTENTION, DEUX FAITS DEJA MESURES QUI
T'EVITENT UNE FAUSSE PISTE : (a) le geste du 11/11 n'a PAS casse le chainage par la date
-- les 113 offres suspectes ont TOUTES leurs propositions lisibles, et le chainage trie
sur la premiere proposition ; leur isolement vient de l'ETAT « offre morte », qui est le
DESSIN ; (b) l'etiquette est nee le 12/11, soit APRES le geste, donc le journal ne sait
rien d'avant. Commence par la soustraction du § 5.3 : la croissance du GEL explique-t-elle
les ~80 lignes a cheval inexpliquees ? Puis tu dis, chiffre a l'appui : ce qui est casse,
par quoi, combien, et ce qui est SAIN -- le chainage a souvent RAISON de separer, deux
acheteurs successifs font deux affaires.

TEMPS 2 -- FINIR LE CHANTIER. Tu le reprends EN GLOBALITE : tu REAUDITES sa faisabilite
etape par etape (1 a 5), tu dis ce qui est fait, ce qui reste, ce qui est BLOQUE et par
quoi, et tu REFLECHIS A LA MEILLEURE METHODE pour y arriver -- la tienne, argumentee,
pas la recopie d'un plan. Tu presentes deux ou trois chemins quand il y a un choix, avec
leur cout et leur risque, et tu recommandes. Tu ne decides pas un perimetre seul.

CE QUI NE SE DISCUTE PAS :
  . tu ecris UNIQUEMENT en francais, et JAMAIS de tableaux dans tes messages ;
  . ACCORD OBLIGATOIRE avant toute ecriture en base de production, toute ecriture chez
    Hektor, tout run, tout redemarrage, tout deploiement, tout geste irreversible ;
  . tu MESURES avant de conclure, et tu dis ce que tu n'as pas mesure ;
  . un patch porte son `commit;` : joue « pour voir », IL SE COMMITE ;
  . tu stages fichier par fichier (jamais git add .), tu relis le stage juste avant le
    commit et la liste a pousser juste avant le push ; `git commit -m` n'existe plus,
    tout message passe par un fichier et -F ;
  . tu n'ecrases rien : additif et chirurgical.

COMMENCE par le temps 1, et explique-moi clairement ce que tu trouves avant d'agir.
```

---

## 1. ⛔ CE QUI NE SE DISCUTE PAS — les interdits du chantier

```
. le classeur FAIT FOI, mais il NE FERME PAS : il change d'ecrivain (plan § 2)
. on ne cree NI table NI colonne pour ce chantier (plan § 6)
. la colonne `date` d'une offre NE SE CORRIGE PAS : le run la relit chaque nuit chez
  Hektor et la protection est NOMMEMENT refusee pour ce couple
  (R2_JUGES_SUR_LE_REGISTRE, affaire_ledger.py l. 1718). ON CORRIGE LES LECTEURS.
  ⚠ le plan cite « l. 1671 » et « l. 1517 » : ces deux renvois ont GLISSE, les vrais
    sont 1718 et 1564. Un renvoi ne se calcule pas, il se trouve.
. phase2/sync/rattachements_manuels.csv est UNE DECISION DE FREDERIC, pas une donnee :
  « on n'en ajoute JAMAIS une sans lui »
. un numero de chaine ne sert JAMAIS de point d'accrochage (il bouge, ~35 dossiers par
  semaine) : on pointe des app_affaire_id
. les 8 lignes INCERTAINES et les 18 lignes A QUESTION OUVERTE sont intouchables tant
  qu'il n'a pas repondu
```

---

## 2. L'ORDRE DE LECTURE — les sept pièces

```
1  notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md     LE PLAN QUI FAIT FOI. Lire le § 0
   (plan actif, reecrit le 12/11), le § 2 (le but), le § 6 (les interdits), et le
   « PLAN DETAILLE DU 15/11 » -- il remplace les listes des jours precedents.
   ⚠ 367 000 caracteres : NE JAMAIS le lire en entier, ouvrir par numero de ligne.
2  phase2/sync/affaire_ledger.py                   LE CODE DU CHAINAGE. Les 9
   interrupteurs vivent entre les lignes 1156 et 1500 ; recalculer_les_chaines
   l. 1888 ; poser_les_etiquettes_de_dossier l. 2691.
3  notice/AUDIT_INDEPENDANT_CLASSEUR_2026-11-18.md      le rapport de la 1re session
   (+ son CSV de verdicts, et son § 5 ter genere le 19/11)
4  notice/AUDIT_INDEPENDANT_V2_2026-11-19.md            le rapport de la 2e session
   (+ ses CSV : MON_APPARIEMENT, GEL_CONTRE_MOI, SES_OPERATIONS_JUGEES,
    OPERATIONS_AFFINEES, TRACES_A_REPOSER)
5  supabase/patch_correction_gel_audit_v2_2026-11-19.sql   le patch AFFINE, DORMANT
   (+ _INVERSE et _REPETITION). Il remplace celui du 18/11.
6  notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_V2_2026-11-19.md   le dossier precedent :
   ses 13 arbitrages, les 32 questions ecrites, les donnees en dur du gel (§ 13)
7  la memoire projet       C:\Users\admin\.claude\projects\C--Hektor\memory\
   -- commencer par chainage-255-lignes-deux-causes.md
```

---

## 3. ⛔⛔⛔ LES DEUX PIÈGES QUI ONT DÉJÀ MORDU

**① L'ACCORD CIRCULAIRE.** 15 211 valeurs du classeur sont **déjà posées** dans notre
registre. Comparer le Sheet au registre mesure donc un accord **fabriqué** : 874 des 897
« accords » du 17/11 étaient circulaires. Un appariement indépendant **ne lit ni le gel,
ni aucune colonne `*_app`**, et écarte les 190 transactions `transaction_origine='classeur'`.

**② LE NOM N'EST PAS UNE PREUVE, DES DEUX CÔTÉS.**

- Chez Hektor, **le contact change à l'intérieur d'une chaîne** (501 lignes mesurées par
  la 2ᵉ session) : offre au nom de l'un, compromis et vente au nom de l'autre, les trois
  dates au jour près. Un apparieur qui juge le nom transaction par transaction **coupe
  ces affaires en morceaux**.
- À l'inverse, **le même acheteur porte parfois DEUX fiches contact** chez Hektor
  (26 paires mesurées le 12/11). C'est pour ça que la règle « même acheteur » compare
  **les numéros, jamais les noms** — un nom de famille partagé est un couple ou un
  homonyme dans 109 cas mesurés.

➡ **Ce qui tranche, c'est la date au jour près, et la preuve interne.**

---

## 4. CE QUE CETTE CONVERSATION A FAIT, ET CE QUE LES DEUX AUTRES ONT PRODUIT

### Ce que cette conversation a fait (18-19/11)

```
. lu EN ENTIER le rapport du 18/11 (341 l.) et son patch (293 l.), et les a controles
  en lecture seule contre la base vivante : 55 retraits et 109 ajouts comptes, garde
  « 12 787 liens » vraie, 0 transaction prise par deux lignes, 0 doublon, les deux
  listes de retraits de MEME empreinte md5 -> le patch tournerait
. TROUVE TROIS RESERVES, toutes reprises par la 2e session :
    1 il detournait `etage` (phrase tronquee) et `preuves` (0, qui veut deja dire
      « creee par C5 ») -- deux colonnes de MESURE
    2 il renvoyait 6 fois a un « § 5 ter » qui n'existait pas
    3 il touchait 18 lignes portant une question ouverte
. CONFRONTE les 13 arbitrages de Frederic au rapport : 1 identique, 2 doutes confirmes,
  2 A MOITIE FAITS (« defaire ET creer » : le patch ne defait que), 3 non jugees mais
  non contredites, 5 PAS ABORDEES
. COMBLE le trou du « § 5 ter » : les 32 questions ecrites extraites du CSV (la 33e,
  SHN6RKDI, est muette) -- elles sont au § 13 F du dossier V2
. ECRIT le dossier V2 (861 l.) avec les donnees en dur, pour ne rien redecouvrir
. CONTROLE le travail de la 2e session, et MESURE LE CHAINAGE -- c'est le § 5 ci-dessous
```

### Ce que la 1ʳᵉ session a produit (18/11)

Un rapport d'audit indépendant du Sheet contre le registre — **appariement fait sans le
gel** : 4 402 lignes en accord prouvé, 350 lignes jugées, 107 contre-expertises. Le pont
le plus fort qu'elle a trouvé : **la référence Netty de l'agence (VM…/VA…) est le numéro
de dossier Hektor**, donc l'annonce, pour 646 lignes. Quatre familles d'erreurs nommées,
dont **les affaires croisées entre acheteurs successifs** (11 paires) et **25 copies de
transactions Hektor créées par C5**. Et un **patch du gel** : 55 retraits, 109 ajouts.

⛔ **Ce patch est remplacé par celui du 19/11. Ne pas le jouer.**

### Ce que la 2ᵉ session a produit (19/11)

Un second audit indépendant, en quatre temps imposés : son propre appariement arrêté
**avant** toute lecture du gel (4 796 lignes : 4 567 certaines, 159 solides, 68 biens
sans transaction, 2 sans rien ; 12 621 rattachements), puis la comparaison avec la 1ʳᵉ
session (133 de ses 141 opérations soutenues), puis **le patch affiné**, puis
l'explication. Elle a trouvé seule les 501 lignes où le contact change dans la chaîne,
et six défauts de sa propre méthode.

**Le patch affiné** — `supabase/patch_correction_gel_audit_v2_2026-11-19.sql`, **DORMANT,
jamais joué** : 45 retraits, 78 ajouts, le gel passe de 12 787 à 12 820, les lignes sans
lien de 91 à 71. Mes trois réserves sont corrigées, et il ajoute trois renforts : la
garde lit l'**empreinte** du gel et pas seulement son compte, elle vérifie avant toute
écriture que **chaque cible sera libre**, et le retour arrière ne juge que sa part.

✅ **Contrôlé le 19/11 : 45 et 78 recomptés dans le fichier, le compte 12 787 − 45 + 78 =
12 820 est juste, la simulation en lecture seule passe.** Il attend son « vas-y ».

⛔ **CE QUE LES DEUX SESSIONS ONT MANQUÉ, ET C'EST LE SUJET DE CE DOSSIER :** aucune n'a
touché au chaînage. Dans les 569 lignes du rapport V2, le mot « rapatriement »
n'apparaît **pas une fois**, « 5.2 » **pas une fois**, et « chaîne » n'y est que dans le
sens « la chaîne Hektor ». La suite qu'elle propose compte six gestes, tous du ménage
autour du gel.

---

## 5. ⭐⭐⭐ L'ÉTAT DU CHAÎNAGE — mesuré le 19/11 en lecture seule

> ⛔ **Tout ce qui suit a été mesuré chez Supabase, son maître, le 19/11, gel à 12 787
> liens. Les deux rapports se trompent sur ce point, et c'est le cœur de ta mission 1.**

### 5.1 Ce que les deux rapports disent, et pourquoi c'est faux

Le rapport du 18/11 (§ 4.5) écrit que **255 lignes du Sheet portent plusieurs étiquettes
de dossier**, et attribue cela à la **seule** scission du 17-18/11 — les 136 transactions
créées depuis le Sheet, coupées de leur dossier. Il en déduit un remède : rattacher les
136 à la main. Le dossier V2 (§ 9) a repris ce diagnostic.

⛔ **La décomposition mesurée dit autre chose :**

```
4 703 lignes liees
  255 portent PLUSIEURS etiquettes                       (le bouchon de l'etape 5.2)
    136 ont une transaction transaction_origine='classeur'   <- la scission du 18/11
    119 n'en ont AUCUNE : 100 % Hektor                       <- une AUTRE cause
  si on rattachait les 136 a la main : il resterait 119
```

➡ **Le remède écrit dans les deux rapports ne couvre que 53 % du bouchon.**

### 5.2 ⭐⭐ La dégradation est RÉCENTE, et elle vient de nous

Le plan du chantier porte la mesure du 12/11, faite avec le chaînage corrigé :

```
12/11  lignes du Sheet qui tombent dans UN SEUL dossier   4 655   (99,3 %)
       lignes a cheval sur DEUX dossiers                     33
19/11  lignes a cheval                                      255
```

**33 → 255 en sept jours.** Le journal `app_dossier_etiquette_journal` dit exactement
quand, et il garde tout :

```
12/11   pose initiale         11 441 dossiers . 31 151 transactions
13/11   5 fusions . 4 poses . 2 scissions . 1 propagation
14/11   2 scissions
17/11   2 poses . 2 propagations
18/11   138 SCISSIONS . 142 transactions        <- nos 136 creations depuis le Sheet
19/11   1 scission . 1 propagation . 2 poses
```

⭐ **Hors nos propres gestes, le chaînage est STABLE** : deux à neuf transactions par
nuit. Il « peut bouger toutes les nuits », mais en pratique il ne bouge que **quand on
le secoue**.

### 5.3 ⭐⭐⭐ NOS SCRIPTS DE MASSE ET LE CHAÎNAGE — ce qui est mesuré, et ce qui reste ouvert

Le refus des offres mortes du 11/11 a touché **1 166 offres** :

```
offres refusees portant la date 2026-11-11                     1 166
   dont SEULES dans leur dossier                                 589
   dont seules ALORS QUE LEUR BIEN porte d'autres transactions    113   <- les suspectes
   dont seules et leur bien n'a qu'elles                          476   (normal)
```

⛔⛔ **J'AI D'ABORD CRU QUE LE GESTE AVAIT CASSÉ LE CHAÎNAGE PAR LA DATE. C'EST FAUX, ET
LA MESURE LE TRANCHE.** Le chaînage ordonne une offre sur **sa première proposition**, pas
sur la colonne `date` (`_date_de_tri`, affaire_ledger.py **l. 1564**, corrigé le 16/09),
avec un repli sur la colonne seulement si les propositions sont illisibles ou vides.
**Or les 113 suspectes ont TOUTES un `propositions_json` rempli — 113 sur 113.** Le repli
ne joue donc jamais, et le plan a raison : *« le chaînage n'est pas touché »*.

➡ **Leur isolement vient de l'ÉTAT, pas de la date** : une offre `refused` est une offre
morte (`ETATS_OFFRE_MORTS`, l. 1539), et une offre morte ne porte pas de compromis — elle
ouvre et ferme sa propre chaîne. **C'est le dessin du chaînage, pas un accident.** Ce que
le geste a changé, c'est l'état de 1 166 offres ; le chaînage n'a fait qu'en tirer les
conséquences.

⛔⛔ **ET VOICI LA QUESTION QUI RESTE OUVERTE, C'EST LA PREMIÈRE DE TON TEMPS 1 :**
l'étiquette de dossier est née **le 12/11**, soit **le lendemain** du geste. Le journal ne
peut donc pas dire ce que le geste a défait — *« un journal ne sait rien d'avant sa
naissance »*. Et les comptes ne se rejoignent pas :

```
12/11  lignes a cheval                                33
19/11  lignes a cheval                               255      -> +222
explique par le journal : 138 scissions (18/11) + 4   142
NON EXPLIQUE                                          ~80
```

⚠ **Piste à vérifier d'abord, avant d'accuser le chaînage** : le gel a GROSSI sur la même
période (12 422 liens le 29/10, 12 595, puis 12 787 aujourd'hui). Chaque lien neuf peut
ajouter une étiquette à une ligne et la faire basculer dans les « à cheval » **sans que
le chaînage ait bougé d'un pouce**. Mesure-le avant tout : c'est une soustraction, pas une
enquête. **Non tranché.**

### 5.4 ⭐⭐⭐ Les 119 lignes, ouvertes une à une

96 des 119 ont **exactement la même forme** : une offre `refused` + un compromis
`cancelled`, **sur le même bien**. Classées par les noms et les numéros d'acquéreur :

```
65   DEUX ACHETEURS DIFFERENTS -> le chainage a RAISON de separer. C'est le GEL qui
     tient deux affaires sur une seule ligne du Sheet. Memes exemples : offre SINTEZ
     refusee le 10/01/2020 + compromis CHABROT annule le 13/03/2020 (ligne 0IS41BM1) ;
     offre TRIOMPHE + compromis BOUAMAR (13KBCS85) ; offre PENY + compromis ISSARTEL
     (1X9W3VUF). C'est la famille « affaires croisees » : la 1re session en avait vu 11.
24   l'offre porte la date 2026-11-11 (notre geste), nom different ou absent -> a juger
 5   le geste du 11/11 ET LE MEME NOM des deux cotes -> une affaire coupee en deux :
     BHMANOK7 (BOUGEARD) . H3SQXY47 (ARSAC ET DUMAS) . R2U574AC (ROCHELEMAGNE)
     U258U4CX (MILHAS) . WUQ5445T (PARIS)
     ⚠ MAIS leurs NUMEROS d'acquereur DIFFERENT (ex. BOUGEARD 313360 contre 92724) :
       c'est le MEME acheteur sous DEUX fiches Hektor. La regle « meme acheteur »
       s'abstient donc A JUSTE TITRE -> ces cas relevent du fichier manuel, pas d'une
       regle nouvelle.
 2   MEME nom ET MEME numero d'acquereur, et pourtant separes : 5QE9107L (DEBARD,
     acquereur 338966, bien 41481) et 8SZDU4F5 (POCHELON, 546711, bien 39745).
     ⭐ DANS LES DEUX CAS le compromis est SANS DATE (0000-00-00) -> VRAI TROU DE REGLE
23   les 23 autres lignes, de formes diverses : NON CLASSEES, a faire
```

### 5.5 ⭐⭐⭐ LE TROU DE RÈGLE, mesuré sur TOUT le registre

La règle « même acheteur » (`APP_CHAINAGE_MEME_ACHETEUR`) réunit deux chaînes du même
bien qui partagent un acquéreur, avec deux gardes : jamais deux ventes, jamais deux
compromis vivants. Mais **une transaction SANS DATE n'entre jamais dans la liste des
chaînes du bien** — c'est écrit noir sur blanc pour la règle A — donc la règle « même
acheteur » **ne la voit pas**. Mesure sur tout le registre :

```
13 439 couples (bien, acquereur Hektor)
    63 portent PLUSIEURS etiquettes          <- la regle devrait les avoir reunis
       41 ont au moins une transaction SANS DATE   <- la cause probable
       22 sont toutes datees                       <- autre cause, a trouver
    41 des 41 se reuniraient SANS violer les deux gardes
       (ni deux ventes, ni deux compromis vivants)
```

➡ **41 réunions franches à gagner**, mesurées, et derrière un interrupteur comme les
règles A, B, C et D. ⛔ **À vérifier dans le code avant de l'écrire** : que la cause est
bien l'absence de date, et non une abstention volontaire.

### 5.6 Ce que le chaînage a déjà, et qu'il ne faut pas réinventer

**Les 9 interrupteurs sont TOUS allumés dans `.env`** — le chaînage tourne déjà dans sa
version améliorée :

```
APP_CHAINAGE_V2=1                      APP_CHAINAGE_OFFRE_ACCEPTEE_SEULE=1   (regle B)
APP_CHAINAGE_SANS_DATE=2               APP_CHAINAGE_COMPROMIS_ANNULE_SEUL=1  (regle A)
APP_CHAINAGE_OFFRE_PROPOSEE=1          APP_CHAINAGE_MEME_ACHETEUR=1          (regle D)
APP_CHAINAGE_OFFRE_SANS_DATE=1         APP_CHAINAGE_RATTACHEMENT_MANUEL=1
APP_CHAINAGE_VENTE_SEULE=1  (regle C)  APP_ETIQUETTE_DOSSIER=1
```

Et `phase2/sync/rattachements_manuels.csv` est **branché et vivant** : il porte
**6 décisions** de Frédéric (4 biens où l'acheteur a deux ventes, 1 vente sans acquéreur
chez Hektor, 1 même acheteur sous deux numéros). Il refuse une ligne dont les deux
transactions ne sont pas sur le même bien, et l'écrit au journal. **C'est la seule
mémoire qui survit au recalcul de chaque nuit.**

### 5.7 ⛔ Gel et chaînage sont INDÉPENDANTS

Un lien ligne→transaction ne dépend pas de l'étiquette ; le gel s'accroche à la
**transaction**, qui ne bouge jamais. C'est pour ça que le chaînage a pu être refait sans
casser un lien. **Rien n'oblige donc à retarder le patch du gel pour le chaînage.** Ce
qui dépend des deux, c'est **l'étape 5.2** — et elle seule.

⚠ Mesuré : la simulation du patch V2 fait passer les multi-étiquettes de **255 à 243**.
Il en règle 12, par ricochet.

---

## 6. OÙ EN EST LE RAPATRIEMENT — mesuré le 19/11

```
4 293 transactions portent au moins une valeur venue de l'app
        vente_reglee_app        3 729       date_annulation_app      450
        numero_facture_app      3 671       motif_annulation_app     169
        honoraires_entree_app      66       charge_commission_app      7
        honoraires_sortie_app       6       numero_mandat_app          0
```

Le gros est passé. Ce qui reste est **la partie honoraires et commissions** — et c'est
exactement là que vivent **les 36 lignes tranchées le 18/11 et non posées** et **les 207
non posées**. La pose attend son « vas-y », et trois questions l'ont précédée (sur quelle
transaction de la chaîne poser, le cas 61OW86CS, et NEFHS7JI non tranché en entier).

---

## 7. LES ÉTAPES DU CHANTIER — à RÉAUDITER, c'est ta mission 2

```
ETAPE 1   le gel : poser les liens ligne <-> transaction            . 12 787 liens
          reste : le patch V2 (dormant), les 91 sans lien, les 277 « a valider »
ETAPE 2   poser les valeurs du Sheet dans le registre               . 15 211 posees
          reste : les 36 tranchees + les 207 . les honoraires et la charge
ETAPE 3   juger les divergences, une par une                        . 350 lignes jugees
          reste : 8 INCERTAINES . 18 a question ouverte . 32 questions ecrites
ETAPE 4   la porte d'ecriture et les vagues de reprise
          ⛔ app_modifier_affaire_optimistic EXIGE un utilisateur admin connecte
            (is_app_manager_or_admin() lit auth.uid()), un numero Hektor, et une
            transaction ENCORE PRESENTE chez Hektor. Une « porte sans ecran » appelee
            par un script n'a pas d'utilisateur -> QUI SIGNE est a trancher avec lui.
          ⚠ ce que la reprise enverrait vraiment chez Hektor n'est PAS mesure :
            commission, charge, facture, reglement et annulation n'ont pas de case
            chez lui.
          ⛔ 14 chaines du classeur sont ENTIEREMENT MORTES chez Hektor : une reprise
            qui exige « presente chez Hektor » ne les touchera jamais.
ETAPE 5   la bascule
          5.1 LES APPS SCRIPT DU SHEET -- c'est SON geste, 10 min, et il BLOQUE P4
          5.2 ecrire nos UUID dans la colonne affair_uuid
              ⛔ BLOQUE par les 255 lignes a plusieurs etiquettes (§ 5) + les 14
                chaines mortes. Deux options a lui soumettre : rattacher a la main,
                ou CHOISIR l'etiquette a l'export.
          5.3 le routeur : l'app lit le Sheet par l'UUID, le gel DORT pour toujours
```

---

## 8. LES ADRESSES UTILES

```
phase2/sync/affaire_ledger.py            le chainage et les etiquettes
phase2/sync/rattachements_manuels.csv    les decisions manuelles (branchees)
phase2/sync/pull_from_supabase.py        la descente : Supabase -> local
app_dossier_etiquette_journal            le journal des mouvements d'etiquette
app_classeur_lien                        le gel (Supabase est le MAITRE)
app_affaire_ledger                       le registre (le LOCAL est le maitre)
app_classeur_ligne_id                    les lignes du Sheet connues
monitoring/check_gti_health.py:817       sentinelle data.classeur_ligne_sans_lien,
                                         seuil 92 -> a suivre apres tout geste sur le gel
Console/apply_sql_patch.js               jouer un patch
Console/enqueue_refus_offres_mortes_lot.js        le geste de masse du 11/11
Console/enqueue_reaccepter_offres_refusees_a_tort.js
Console/enqueue_fermeture_dossiers_impossibles.js
```

**Les horaires réels** (le CLAUDE.md en annonce d'autres, il est périmé sur ce point) :
**GTI Quotidien 04:00**, **GTI Descente 06:45**. ⭐ **Aucun run de nuit, aucune tâche
planifiée n'écrit dans le gel** — il n'y a donc aucune fenêtre qui se ferme pour le patch.

---

## 9. ⛔ LES TROIS DÉCISIONS QUI L'ATTENDENT, ET QUI N'ONT PAS BOUGÉ

```
1  LES DEUX DATES D'OFFRE (QH6672TZ, 74IL9C8F) : creer une colonne chez nous, ou
   corriger chez Hektor ? ⚠ le journal Hektor porte lui-meme la mauvaise annee
   (23488 -> 2002-01-31, 24448 -> 2020-08-07).
2  LA REGLE « TOUTES » : repasse-t-on sur les 66 valeurs deja posees ?
3  JOUER OU NON LE PATCH DU GEL V2 (45 retraits, 78 ajouts). Il est pret et controle.
```

Et **cinq arbitrages du 18/11 ne sont traités par personne** : la règle « toutes »,
l'offre 4281 à réparer chez Hektor, l'audit REFUS5 (à refaire, son script est antérieur
à la demande), et la moitié « créer » de `1ESJE28Q` et `8Q3LHGZ4` (il a dit « défaire ET
créer », les deux patchs ne défont que).
