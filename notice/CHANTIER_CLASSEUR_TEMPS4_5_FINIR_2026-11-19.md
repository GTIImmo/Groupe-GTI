# TEMPS 4 ET 5 — FINIR LE CHANTIER : CORRIGER LE CHAÎNAGE, PUIS ÉCRIRE NOS IDENTIFIANTS DANS LE SHEET
### 19/11/2026 · chantier classeur · les neuf questions de Frédéric, dans son ordre

> ⛔ **RIEN N'EST ÉCRIT** ni en base, ni chez Hektor, ni dans le Sheet. Le seul code neuf est une
> règle de chaînage **posée ÉTEINTE** (`APP_CHAINAGE_SANS_DATE_VISIBLE`, absente de `.env`).
>
> **L'ordre, imposé par Frédéric parce que c'est une dépendance** : corriger d'abord ce que le
> registre seul sait corriger ; puis se servir du classeur pour trancher ce qu'il ne sait pas ;
> puis écrire. *Une correction de chaînage déplace une transaction d'un dossier à l'autre, donc
> change QUELLE étiquette est la bonne pour une ligne du Sheet.*
>
> **Acquis, à ne pas rouvrir** : on ne défait pas nos refus · l'offre 14420 reste refusée · le
> fichier des rattachements manuels est SA décision · le gel est l'échafaudage, le registre le mur ·
> l'étiquette ne bouge pas, l'appartenance bouge · les temps 1, 2, 3 sont faits (`f04c511`,
> `f7a2d18`, `ecb2c6f`).

## ⭐ LE TABLEAU DE MARCHE — mis à jour à chaque fin de question, AVANT la suivante

> Demandé par Frédéric le 19/11 : *« c'est ce qui survivra quand ta conversation sera résumée »*.
> ⭐ **Le BUT est ⑧ : écrire nos identifiants dans le Sheet.** Le reste est le chemin.
> Dernière mise à jour : 19/11, ses quatre décisions du jour appliquées (les 10 lignes écrites).
>
> **Ses quatre décisions du 19/11** : ① les 10 lignes VALIDÉES → écrites (§ 2.7) ; ② la règle E
> **n'est PAS allumée** — *« UN GESTE PAR NUIT, on verra demain, après le contrôle des 10 »* ; ③ 26613
> **exclue de la règle E, et l'exclusion DÉCLARÉE** ; ④ le patch du gel : je le redemande à ⑦.

```
Q  SUJET                         ETAT        VERDICT EN UNE LIGNE                          ATTEND SA DECISION
①  compromis annule sans date    FAIT        regle E + garde, ETEINTE, rejouee ; 26613     l'allumage -- PAS cette
                                             EXCLUE ET DECLAREE (§ 1.10) : 34 reunions     nuit ; demain, APRES le
                                             sur 33 dossiers, temoins verts                controle des 10
②  les 10 « meme nom »           FAIT,       des menages -> R1 : les 10 lignes ECRITES,    -- (decide). ⏰ demain :
                                 ECRIT       rejouees : 10 dossiers bougent, pas un de     controler la nuit
                                             plus ; 11 590 -> 11 580                       (§ 2.7)
③  les 2 offres du bien 61672    FAIT        le run ne marque jamais absente une           --
                                             transaction « possedee par l'app » ; 12
                                             portent un « sans objet », UNE SEULE en
                                             depend (30712) ; le vrai reservoir est la
                                             plage app : 340 presentes ; touche 2
                                             transactions aujourd'hui
④  la « fusion » du 18/11        FAIT        un TRANSFERT compte comme fusion (1 sur 6) ;  --
                                             la RPC garde l'etiquette du plus petit
                                             numero, pas la plus ancienne
⑤  les 48 « a juger »            FAIT        le Sheet tranche 14 des 48 : 8 CASSES, 5      les 8 lignes « pures »
                                             corrections, 1 mixte ; 34 n'ont AUCUNE ligne  (§ 5.6) -- je n'en
                                             au Sheet (sans effet sur ⑧). Il renverse 5    ecris aucune ;
                                             « corrections » du temps 3. 6 dossiers        les 6 melanges : quel
                                             MELANGES demandent une SCISSION               outil (⑨)
⑥  les 255 a plusieurs etiquettes FAIT     255 -> 251 cette nuit -> 229 au bout de       la decision C5 deja
                                             TOUT (E, les 8, le patch). Le noyau : 128 C5, posee (pour ⑧ : choisir
                                             74 que le Sheet tient (66 MELANGES), 26 liens a l'export)
                                             du gel seul. + 207 dossiers sur 2-3 lignes
⑦  le patch du gel               FAIT        il TIENT : 4 gardes a 0 aujourd'hui, temoins  le « vas-y » du patch V2
                                             semes 1/1/1 ; il corrige EXACTEMENT les 2     (je recommande : demain,
                                             erreurs du gel de 5.4 ; ⑥ : 16 reglees, 4      apres le controle des
                                             revelees (pas des regressions)                10, pas cette nuit)
⑧  ECRIRE DANS LE SHEET          A FAIRE     ⭐ LE BUT                                      le critere de fin, AVANT
                                                                                           la 1re ligne
⑨  ce qu'il ne m'a pas demande   A FAIRE
```

---

## ① LE COMPROMIS ANNULÉ SANS DATE — la règle E, mesurée sur tout le registre

### 1.1 Le mécanisme exact — et il corrige ce que j'avais écrit au temps 3

Rejoué **bien par bien** avec la vraie fonction, avec et sans nos gestes
(`scratchpad/q/diag_bien.py`, lecture seule) : la cause n'est pas « la règle A a perdu sa cible ».
C'est plus général, et c'est **un trou du code** :

```
une transaction SANS DATE recoit sa propre chaine (attribution[app_id] = app_id)
MAIS N'ENTRE JAMAIS dans `toutes`, la liste des dossiers du bien.
   -> la regle D (« meme acheteur, meme bien ») ne la compare a RIEN
   -> le fichier des rattachements manuels la dit « introuvable »
Seuls les replis § 2.6 / § 2.9 et la regle A peuvent la rattacher. Quand ils s'abstiennent,
elle reste seule ET INVISIBLE.
```

Avant nos refus, la règle A ou le repli par le nom rattrapaient les quatre compromis cassés (DEBARD,
POCHELON, THEVENON, GENOUX) ; après, le contexte du bien avait changé, ils se sont abstenus, et la
règle D — qui aurait réuni ces transactions au même numéro d'acquéreur — **ne les voyait pas**.
C'est le « trou de règle » du § 8.4 du dossier, maintenant localisé à la ligne près.

### 1.2 La proposition : la règle E, et rien de plus

`phase2/sync/affaire_ledger.py`, **après** la règle A, **avant** la règle D : chaque transaction sans
date encore seule entre dans `toutes` comme un dossier d'un seul membre. **Elle ne réunit rien
elle-même** ; c'est la règle D, avec ses deux gardes (jamais deux ventes, jamais deux compromis
vivants), qui décide. Aucun nom, aucune date devinée. ⚠ Après A et pas avant : A saute ce qui est
déjà dans `toutes`.

```
POSEE ETEINTE        APP_CHAINAGE_SANS_DATE_VISIBLE absent de .env -> la nuit fait exactement ce
                     qu'elle faisait. PROUVE : regle eteinte, la vraie fonction rend la base a
                     0 ecart sur 31 359 ; compilation OK ; 4 tests du chainage verts.
⚠ LE 5e TEST         test_chainage_v2 est ROUGE -- et ce n'est PAS la regle E : il ecrit lui-meme
                     « la base EST le resultat de la regle (0 ecart) » ; ce qui rougit, ce sont
                     ses comptes ATTENDUS figes le 12/11 (11 428 dossiers) et depasses par les
                     135 creations C5 du 16/11 (11 575). Rouge PREEXISTANT, a recaler a part.
```

### 1.3 La mesure sur tout le registre — `notice/TEMPS4_REGLE_E_REUNIONS_2026-11-19.csv`

`phase2/checks/temps4_regle_e_sans_date_visible_2026-11-19.py` (lecture seule, l'interrupteur
n'est posé que dans son propre processus) :

```
REGLE E ETEINTE    11 590 dossiers, 0 ecart avec la base           ✅ temoin positif de la fonction
REGLE E ALLUMEE    11 550 dossiers
   84 transactions sans date etaient seules ; la regle les rend visibles
   40 sont reunies par la regle D, sur 39 dossiers (le bien 9483 en porte deux)
      TOUTES des compromis, 39 annules et 1 actif (16197, bien 33458)
   44 restent seules : aucun dossier du meme numero d'acquereur, ou pas d'acquereur du tout
LES TEMOINS
   positif   les 5 casses du temps 3 sont TOUTES reunies : 20088 DEBARD . 19070 POCHELON .
             1335 THEVENON . 14110 GENOUX . 16197 (bien 33458)
   inverse   0 bien qui bouge sans porter une transaction sans date seule
   sens      0 dossier coupe : la regle ne fait que reunir
   gardes    apres E : 0 dossier a deux ventes, 0 a deux compromis vivants
```

### 1.4 ⭐ MA LECTURE DES 40, À LA MAIN — et mon classement automatique s'est trompé 4 fois

Le script classait 25 « à raison » et 15 « à vérifier ». En lisant chaque dossier (membres, états,
dates, montants, acquéreurs), **4 de ses « à raison » sont À TORT** :

```
32 A RAISON
   21 des « a raison » du script
   11 des « a verifier » : meme acheteur, et soit le meme prix, soit une autre tentative
      du meme acheteur (detail en 1.5)
 4 A TORT -- LA VENTE PORTE LE NOM DU MAUVAIS ACQUEREUR
   bien 15220  GENILLON  le compromis annule 7499 (204 000) rejoindrait le dossier de COUDOUR
                         (offre 203 400, compromis 202 700) parce que la VENTE 7502, au prix de
                         COUDOUR, porte le nom de GENILLON -- c'est le « cas GENILLON » du plan :
                         deux lignes du Sheet, deux affaires
   bien 17536  Rouchon   compromis 8845 (225 000) -> dossier de CLOUVET (215 000), vente 8847
                         « Rouchon » a 215 000
   bien 23238  Simonyan  compromis 11103 -> dossier de MARGOTAT, vente 11106 « Simonyan »
   bien 54867  PLANCHE   compromis 28214 (48 000) -> dossier de CANU (45 000), vente 28216
                         « PLANCHE » a 45 000
   ⭐ Les QUATRE sont dans la liste du plan (§ 4 F) des « 11 VENTES qui portent le nom du
     MAUVAIS acquereur (celui du compromis ANNULE) ». Aujourd'hui ces compromis sont seuls,
     et SEULS ILS ONT RAISON : c'est la tentative echouee d'un autre acheteur.
 3 A JUGER -- LE DOSSIER CIBLE EST DEJA UN MELANGE (voir 1.6)
 1 QUESTION OUVERTE -- bien 52166, compromis 26613 : c'est la transaction de la ligne SHN6RKDI,
   la 33e question, la « muette », INCERTAINE. Une regle ne la tranche pas avant sa reponse.
```

### 1.5 Les 15 « à vérifier » — ce que j'en pense

Le script les marquait parce que le dossier d'arrivée **porte déjà un compromis annulé du même
acheteur**. Ce n'est pas un signe d'erreur : c'est le cas normal d'une affaire qui a connu
plusieurs compromis.

```
A RAISON, MEME AFFAIRE, MEME PRIX (6)
   3481  THEVENON   38 500 = SON offre (38 500) ; puis un compromis renegocie a 37 500
   28653 GENOUX     113 000 partout (offre, deux compromis, vente)
   39745 POCHELON   159 000 = SON offre ; puis un compromis a 160 000
   40977 CHEVALLET  69 000 = son compromis annule date -> probablement LE MEME saisi deux fois
   9483  LAMBINET   deux compromis annules (230 000 puis 237 500), puis compromis, offre et
         (x2)       vente a 225 000 -- deux tentatives renegociees, la meme vente au bout
A RAISON, MEME ACHETEUR, UNE AUTRE TENTATIVE (5) -- la regle D de Frederic : « un acheteur + un
bien = une affaire ; un compromis annule est une ETAPE de l'affaire »
   3155  BEDRE      56 000 contre 53 000
   23562 KERROUM    280 000 contre 265 000
   50356 MUNOZ      39 000 contre 35 000
   28548 DUVERT     262 000 contre 295 000 -- ⭐ verifie a part : la regle reunit les DEUX
                    compromis de DUVERT avec SON offre refusee, et NE TOUCHE PAS au dossier de
                    COURCELLE, l'acheteur de 2026. DUVERT est l'exemple de la memoire « vieux
                    contact reutilise » ; ici il ne fait rien de faux.
   36320 GALLONET   47 500 contre 37 000-38 000 -- l'ecart est grand ; meme acheteur quand meme
A JUGER, LE DOSSIER EST DEJA UN MELANGE (3) -- voir 1.6
   15087 GUERIN / MASSARD . 53342 ALONSO / DE MATOS-DE FARIA . 9993 DUVET / BERCOT
QUESTION OUVERTE (1)
   52166 CARRET + LUTTENBACHER, compromis 26613 = ligne SHN6RKDI
```

### 1.6 Les 4 « à plus d'un an » — la durée n'est pas faite par la règle E

⚠ L'étendue mesurée est celle du dossier **d'arrivée**, entre ses membres **datés** : une transaction
sans date ne peut pas l'allonger. Les 4 sont donc des dossiers qui duraient déjà plus d'un an.

```
28653 GENOUX   405 j  UNE SEULE AFFAIRE : offre 01/2021, compromis 04 et 05/2021, vente 02/2022,
                      tout a 113 000. Une longue affaire, pas un melange. -> A RAISON.
15087 GUERIN   367 j  DEUX ACHETEURS DEJA COLLES PAR LA REGLE D : GUERIN offre 143 000 (05/2020)
                      et signe un compromis a 143 000 (06/2020), annule ; MASSARD offre 140 000
                      (12/2020) et achete (05/2021) -- mais le compromis ACTIF de 140 000
                      (01/2021) porte le nom de GUERIN. C'est le defaut connu « le contact de
                      l'acheteur PRECEDENT reste sur le compromis du suivant ». La regle D a donc
                      reuni les deux affaires par ce contact reutilise.
53342 ALONSO   417 j  le meme dessin : ALONSO offre 98 000 (07/2023), compromis a 90 000 annule ;
                      compromis ACTIF « ALONSO » a 89 000 (05/2024) ; la vente a 89 000 est a
                      DE MATOS - DE FARIA (08/2024).
9993  DUVET    427 j  le meme dessin, plus flou : DUVET offre 36 200 (07/2020), compromis 32 000
                      annule (01/2021), compromis ACTIF « DUVET » 32 000 (05/2021) ; offre acceptee
                      d'OSTRE ET OLIVIERI a 32 000, vente a BERCOT a 32 000 (09/2021).
```
➡ **Pour les trois derniers, la règle E place le compromis sans date à côté des autres tentatives du
même acheteur — c'est juste. Mais le dossier d'arrivée est déjà faux en amont** : la règle D a collé
l'échec d'un acheteur à la vente d'un autre, par un contact réutilisé. Ce n'est pas la règle E qu'il
faut corriger, c'est ce collage — et c'est le classeur qui peut le trancher (question ⑤).

### 1.7 Ce que je propose — la règle E avec sa garde, REJOUÉE

**La garde « l'acheteur du compromis vivant »** est dans le code (règle D, ne joue que si E est
allumée) : un dossier fait seulement de transactions sans date rendues visibles ne rejoint pas un
dossier dont le compromis vivant est à un autre numéro d'acquéreur. **Rejouée sur tout le registre**
(`notice/TEMPS4_REGLE_E_REUNIONS_2026-11-19.csv`, `..._SANS_DATE_RESTANTES_2026-11-19.csv`) :

```
LES TEMOINS NOMINATIFS -- tous verts
   bloques par la garde   7499 GENILLON (15220) . 8845 Rouchon (17536) . 11103 Simonyan (23238)
                          . 28214 PLANCHE (54867) -> RESTENT SEULS
   abstention voulue      4385 PYOT (9629) -> RESTE SEUL, comme aujourd'hui
   toujours reunis        les 5 casses du temps 3 : 20088, 19070, 1335, 14110, 16197
   inverse . sens         0 bien sans transaction sans date seule qui bouge . 0 dossier coupe
   gardes du projet       0 dossier a deux ventes . 0 a deux compromis vivants
LE COMPTE FINAL, APRES GARDE
   dossiers               11 590 -> 11 555
   reunions               35 transactions sans date, sur 34 dossiers (34 biens)
                          = les 40 d'avant moins les 4 a tort et PYOT
                          -> 20 « a raison » du script + les 15 « a verifier » lus en 1.5
CE QUI RESTE DES 84 SANS DATE SEULES : 49
   42  aucun autre dossier de cet acheteur sur le bien -- rien a rejoindre, c'est juste
    5  la garde : le compromis vivant du dossier est a un autre acheteur (les 4 + PYOT)
    2  aucun numero d'acquereur : rien a comparer
   ⚠ le compteur du run dit « garde : 10 » pour 5 transactions -- la boucle de la regle D
     recommence apres chaque reunion et recompte une abstention a chaque passage (c'est deja
     le cas des autres abstentions de D) : on compte par transaction, pas par signal.
ETIQUETTES (simulation de la RPC)
   34 fusions la nuit de l'allumage ; dans 16, c'est l'etiquette du DOSSIER D'ARRIVEE qui
   disparait (le compromis sans date a le plus petit numero), dans 19 celle du compromis
```
LA QUESTION OUVERTE (26613) : la regle E la reunirait au dossier CARRET + LUTTENBACHER. Une regle
   ne doit pas trancher une question ouverte : je propose de NE PAS allumer avant sa reponse sur
   SHN6RKDI, ou d'ajouter a la regle une exclusion DECLAREE de cette seule transaction, qu'on
   retire quand il aura repondu. Les deux sont SA decision.
L'ALLUMAGE : apres son « vas-y », une nuit, suivie du REJEU qui nomme chaque dossier qui bouge
   (le gabarit du temps 3) et d'une sauvegarde datee AVANT.
```

### 1.8 Ce que ça pourrait casser ailleurs

```
L'ETIQUETTE   ⭐ la RPC app_poser_etiquettes_dossier garde, dans un groupe a plusieurs
              etiquettes, celle de la transaction AU PLUS PETIT NUMERO (et non « la plus
              ancienne », comme le dit son commentaire). Simule sur les 40 : dans 19 cas, le
              compromis sans date a le plus petit numero -> c'est l'etiquette DU DOSSIER
              D'ARRIVEE qui serait absorbee, et elle disparaitrait. Sans consequence tant que
              rien n'est publie dans le Sheet (c'est POURQUOI l'ordre « corriger avant
              d'ecrire » compte) -- mais la nuit de l'allumage fera 34 fusions (39 sans la
              garde), et le seuil de 10 criera.
              A annoncer, pas a craindre. Voir question ④.
LA NUIT       une regle de plus dans la boucle du bien : cout negligeable (le recalcul complet
              prend une fraction de seconde).
L'ECRAN       il affiche les dossiers par app_chaine_id : 35 dossiers gagneront un compromis
              annule de plus dans leur historique.
LE GEL        aucun effet : il pointe des transactions, pas des dossiers.
LE FICHIER    les rattachements manuels VERRONT desormais les transactions sans date seules
   MANUEL     (aujourd'hui « introuvables ») -- c'est un effet voulu, et c'est SA decision
              d'y ajouter des lignes.
```

### 1.9 Ce que je n'ai pas mesuré

```
. les 42 « aucun autre dossier de cet acheteur » : comptes, pas lus un par un
. les 3 dossiers deja melanges : qui a raison, le Sheet le dira (question ⑤)
. la datation d'un compromis sans date : ⛔ le numero Hektor NE DATE PAS -- sur 10 447
  compromis dates, 52 % des numeros voisins ont une date qui RECULE (numerotation d'import,
  pas chronologique). Ecarte comme preuve.
```
⚠ La session a coupé pendant le premier passage de la mesure : le CSV était écrit, la sortie écran
perdue. Le second passage (identique, lecture seule) a rendu les témoins ci-dessus, tous verts.

### 1.10 ✅ 26613 EXCLUE DE LA RÈGLE E — l'exclusion est DÉCLARÉE (sa décision du 19/11)

**Ses mots** : *« Exclus-la, et DÉCLARE l'exclusion dans le code et dans ton fichier. Une exclusion
tacite s'oublie. »* Et pour la règle : *« ne l'allume PAS. UN GESTE PAR NUIT — on verra demain, après
le contrôle des 10. Le code reste commité et éteint, c'est tout. »*

```
LE CODE     phase2/sync/affaire_ledger.py, juste apres chainage_sans_date_visible_actif :
              EXCLUES_DE_LA_REGLE_E = {26613: "bien 52166, compromis ANNULE SANS DATE (maison
              CHANUT, 210 000) = la ligne SHN6RKDI ... a retirer apres sa reponse."}
            dans le bloc de la regle E : une transaction de ce dictionnaire n'est PAS rendue
            visible (elle reste seule, comme avant E), ET le compte rendu le DIT a chaque run :
              « [E] exclusion declaree -- laissee seule (EXCLUES_DE_LA_REGLE_E) »
            ⭐ tant que E est eteinte, la ligne ne joue pas : RIEN ne change cette nuit
A RETIRER   quand il aura repondu a SHN6RKDI (prepare pour MOSNIER, ou brouillon de
            CREPINGE/LAROUX ou de LUTTENBACHER/CARRET ?) -- pas avant, pas en silence
REJOUE      phase2/checks/temps4_regle_e_sans_date_visible_2026-11-19.py, temoin de
            l'exclusion AJOUTE, sur le fichier a 16 decisions :
              N (E eteinte) 11 580 dossiers ; ecart avec la base 10 = EXACTEMENT les 10 offres
                du 19/11 que la nuit n'a pas encore appliquees (le temoin le sait, et
                rougirait sur toute autre transaction)
              E (allumee)   11 546 dossiers
              positifs 5/5 REUNIS . gardes 5/5 SEULS . 26613 RESTE SEUL . exclusion DITE 1 fois
              inverse 0 . dossiers coupes 0 . deux ventes 0 . deux compromis vivants 0
              33 reunions (34 transactions) au lieu de 34 (35) : 26613 et son dossier en moins,
                rien d'autre ; [D] 761 -> 760 ; sans date restantes 49 -> 50 (la 50e est 26613,
                raison « exclusion declaree »)
              etiquettes : 19 cas normaux, 15 absorbent l'etiquette du dossier cible ; 33
                fusions en une nuit si on l'allume
TESTS       relances, verts : test_chainage_offre_proposee, test_chainage_vente_ferme,
            test_chainage_offre_regularisee. (test_chainage_v2 : rouge PREEXISTANT, comptes
            du 12/11, non relance.)
⚠ CSV       TEMPS4_REGLE_E_REUNIONS / _SANS_DATE_RESTANTES sont REECRITS par ce rejeu : ils
            portent l'etat a 16 decisions + l'exclusion. Ceux de la question ① sont dans 67eed58.
```

---

## ② LES 10 « MÊME NOM » — ce sont des COUPLES

### 2.1 Ce qui les explique vraiment

Lu fiche par fiche (`acquereurs_json` du registre, puis `app_contact_current.couple_json` par le
numéro Hektor — ⚠ dans les tables de contacts, `hektor_contact_id` porte NOTRE numéro et le numéro
Hektor est dans `hektor_target_id`, le piège des « deux numéros » déjà payé) :

```
TOUS LES 10 SONT DES MENAGES : l'offre au nom d'un conjoint, le compromis au nom de l'autre,
au meme prix.
   3 LIES PAR UN NUMERO   l'offre est sur la fiche « couple » de Hektor, dont refCouple pointe
                          la fiche du compromis ; notre couple_json le dit aussi
                          DZAMAN (27037) . ARSAC ET DUMAS (36712) . VERILHAC (42883)
   7 RELIES PAR RIEN,     chaque conjoint a SA fiche, et sa case « conjoint » est VIDE (une
     SAUF LE NOM          coquille sans nom) : aucun numero ne relie les deux
                          RIGHI Philippe / Ghislaine (10955) . SOULEZ Gilles / Isabelle (11014)
                          . BOUGEARD Marina / Kevin (35702) . GAGNE Sebastien / Sylvie (41584)
                          . MILHAS Jacques / Maud (44276) . PARIS Noemie / Christophe (52724)
                          . HAHNEL Sandrine / Nicolas (55040)
POURQUOI ILS ETAIENT ENSEMBLE AVANT LE 11/11 : l'offre ACCEPTEE attirait le compromis sans
regarder le nom (branche compromis : « l'unique chaine a offre acceptee »). Refusee, elle ne
l'attire plus, et la regle § 2.3 exige le MEME NUMERO. Ces menages ne tenaient que par l'etat.
```

### 2.2 Les remèdes, et ce que chacun coûte

```
R1  LE FICHIER DES RATTACHEMENTS MANUELS -- 10 lignes
    regle les 10, exactement, des la nuit suivante, et survit a chaque recalcul
    COUT : aucun code ; SA decision, ligne par ligne (le fichier est une decision)
    LIMITE : ne protege pas l'avenir -- le prochain menage coupe ne sera pas vu
R2  UNE REGLE « LE COUPLE PAR SON NUMERO » -- dans la regle D, deux numeros que notre base
    relie comme conjoints comptent pour un meme acheteur
    MESURE SUR TOUT LE REGISTRE (lecture seule, 106 617 liens de couple lus) : elle reunirait
    5 paires de dossiers, 0 bloquee par les gardes :
       les 3 lies ci-dessus + GASMI (15439 : compromis 330 000 du 17/07/2023, offre 330 000 du
       05/06/2023) + FOUVET (48923 : compromis 29 000 du 21/09/2012, offre 29 000 du 11/09/2012)
       -- les 5 au meme prix, a quelques semaines : A RAISON
    COUT : du code dans la regle D, derriere un interrupteur ; lire les liens de couple des
    contacts au moment du chainage (une dependance de plus pour la nuit) ; un rejeu complet
    LIMITE : ne regle PAS les 7 (rien ne les relie)
R3  UNE REGLE PAR LE NOM DE FAMILLE sur le meme bien
    regle les 10 d'un coup
    COUT : contraire au principe du projet (« les numeros, jamais les noms » : un nom partage
    est un couple OU un homonyme, 109 cas mesures) ; portee NON MESUREE, forcement bien plus
    large que les 10. ⛔ Je ne le recommande pas.
R4  REPARER LES 7 CHEZ HEKTOR (« transformer en couple », le geste prouve le 02/11)
    puis R2 les rattrape la nuit d'apres
    COUT : 7 ecritures chez Hektor (SON accord), un geste dont le formulaire suivant ne doit
    pas etre enregistre (le piege E6), et R2 ecrite
```

### 2.3 Ce que je recommande

**R1 pour les 10, maintenant** — dix lignes, aucune règle, aucun risque hors des dix, et c'est le
seul remède qui règle les 7. **R2 ensuite, si tu veux protéger l'avenir** : elle ne rapporte que 5
paires aujourd'hui (dont GASMI et FOUVET, que R1 ne voit pas), mais elle recollera seule le prochain
ménage dont la fiche « couple » porte l'offre. R3 non. R4 seulement si le chantier des couples
reprend un jour pour d'autres raisons.

### 2.4 Ce que ça pourrait casser ailleurs

```
R1   rien hors des 10 dossiers ; chaque reunion fera une fusion d'etiquette (10 la nuit)
R2   5 reunions mesurees ; la nuit lirait une table de contacts de plus -- si sa lecture
     echoue, la regle doit se taire (comme R2 du registre, « lecture ratee = on ne touche a
     rien »), sinon une panne de contacts changerait des dossiers
```

### 2.5 Ce que je n'ai pas mesuré

```
. R2 n'est PAS ecrite : les 5 paires sont comptees par une lecture des donnees, pas rejouees
  par la vraie fonction
. R3 : sa portee sur tout le registre
. si d'autres menages coupes existent dont AUCUN des deux n'a ete touche par nos gestes
  (R2 en trouve 2 de plus ; pour les menages sans lien, seul un nom les trahirait)
```

### 2.6 ⭐ LA LISTE À VALIDER — les 10 ménages, ligne par ligne, sur les faits

**Sa décision du 19/11 : R1 pour les 10. R2 « bonne idée, mais pas aujourd'hui » (pas rejouée, 2 paires
de plus seulement). R4 non : « on n'écrit pas chez Hektor pour ça ».** ⛔ Aucune ligne n'est écrite
dans `phase2/sync/rattachements_manuels.csv` avant qu'il ait validé CETTE liste.

Lu dans le registre local le 19/11. Les **deux numéros de fiche** sont les numéros Hektor des
acquéreurs ; les dates de l'offre viennent de son journal chez Hektor (`propositions_json`) ; « refus
11/11 » est notre geste B (temps 1).

```
BIEN   OFFRE (transaction . fiche . nom)              COMPROMIS (transaction . fiche . nom)          MONTANT
       proposee et acceptee le / refusee le           signe le / etat
10955  5356  . fiche 184328 . RIGHI Ghislaine         5355  . fiche 184420 . RIGHI Philippe           60 000
       07/08/2015 / 11/11/2026 (nous)                 27/10/2015 / annule                (81 jours)
11014  5408  . fiche 166305 . SOULEZ Isabelle         5407  . fiche 167011 . SOULEZ Gilles           293 000
       22/09/2016 / 11/11/2026 (nous)                 20/10/2016 / annule                (28 jours)
27037  13056 . fiche 257676 . DZAMAN (fiche couple)   13055 . fiche 257677 . DZAMAN Nicolas           68 000
       06/05/2011 / 11/11/2026 (nous)                 21/06/2011 / annule                (46 jours)
       ⭐ la fiche couple 257676 pointe 257677 (refCouple) : le lien est un NUMERO
35702  16866 . fiche 92724  . BOUGEARD Kevin          16865 . fiche 313360 . BOUGEARD Marina         110 000
       07/10/2020 / 11/11/2026 (nous)                 06/11/2020 / annule                (30 jours)
36712  17278 . fiche 545406 . ARSAC ET DUMAS (couple) 17277 . fiche 545402 . ARSAC ET DUMAS          134 000
       07/04/2023 / 11/11/2026 (nous)                       Romain et Aurelie
                                                      02/06/2023 / annule                (56 jours)
       ⭐ la fiche couple 545406 pointe 545402 (refCouple)
41584  20196 . fiche 157385 . GAGNE Sylvie            20195 . fiche 347976 . GAGNE Sebastien         136 000
       14/03/2017 / 11/11/2026 (nous)                 02/06/2017 / annule                (80 jours)
42883  21339 . fiche 542934 . VERILHAC (fiche couple) 21337 . fiche 542932 . VERILHAC               127 000
       24/11/2017 / 11/11/2026 (nous)                       Jean-Paul et Francoise
                                                      13/12/2017 / annule                (19 jours)
       ⭐ la fiche couple 542934 pointe 542932 (refCouple)
       ⚠ le bien porte AUSSI : un 1er compromis VERILHAC 21338 (124 000, 08/11/2017, annule), DEJA
         dans le dossier 21337 ; et l'offre refusee 21340 de FORESTA Solange (124 000, 06/10/2017),
         une AUTRE acheteuse, qui reste a part
44276  22069 . fiche 92138  . MILHAS Maud             22068 . fiche 355886 . MILHAS Jacques          135 000
       24/04/2021 / 11/11/2026 (nous)                 19/06/2021 / annule                (56 jours)
52724  26825 . fiche 142429 . PARIS Christophe        26824 . fiche 400256 . PARIS Noemie             40 000
       20/02/2020 / 11/11/2026 (nous)                 21/05/2020 / annule                (91 jours)
55040  28328 . fiche 179729 . HAHNEL Nicolas          28327 . fiche 391398 . HAHNEL Sandrine          35 000
       16/11/2015 / 11/11/2026 (nous)                 22/12/2015 / annule                (36 jours)
```

**Ce qui ressort des faits** : sur les 10, **le montant est identique** entre l'offre et le compromis ;
le compromis suit l'offre de **19 à 91 jours** ; **9 biens sur 10 ne portent AUCUNE autre transaction**
(VERILHAC, la seule exception, est détaillé ci-dessus). Chaque offre a été acceptée le jour même de sa
proposition chez Hektor, et c'est NOTRE refus du 11/11 qui l'a détachée.

**Les 10 lignes que je propose d'ajouter au fichier** — format du fichier : *transaction à rattacher ;
transaction cible ; bien attendu ; date ; pourquoi* — l'offre rejoint le dossier de son compromis :

```
5356;5355;10955;2026-11-19;RIGHI -- offre de Ghislaine (184328) et compromis de Philippe (184420), 60 000 EUR, menage sur deux fiches
5408;5407;11014;2026-11-19;SOULEZ -- offre d'Isabelle (166305) et compromis de Gilles (167011), 293 000 EUR, menage sur deux fiches
13056;13055;27037;2026-11-19;DZAMAN -- offre de la fiche couple 257676 et compromis de Nicolas (257677, son refCouple), 68 000 EUR
16866;16865;35702;2026-11-19;BOUGEARD -- offre de Kevin (92724) et compromis de Marina (313360), 110 000 EUR, menage sur deux fiches
17278;17277;36712;2026-11-19;ARSAC ET DUMAS -- offre de la fiche couple 545406 et compromis de 545402 (son refCouple), 134 000 EUR
20196;20195;41584;2026-11-19;GAGNE -- offre de Sylvie (157385) et compromis de Sebastien (347976), 136 000 EUR, menage sur deux fiches
21339;21337;42883;2026-11-19;VERILHAC -- offre de la fiche couple 542934 et compromis de 542932 (son refCouple), 127 000 EUR
22069;22068;44276;2026-11-19;MILHAS -- offre de Maud (92138) et compromis de Jacques (355886), 135 000 EUR, menage sur deux fiches
26825;26824;52724;2026-11-19;PARIS -- offre de Christophe (142429) et compromis de Noemie (400256), 40 000 EUR, menage sur deux fiches
28328;28327;55040;2026-11-19;HAHNEL -- offre de Nicolas (179729) et compromis de Sandrine (391398), 35 000 EUR, menage sur deux fiches
```

**Ce qu'elles feront** (lu dans le code, non rejoué) : chaque offre quitte son dossier d'une seule
transaction et rejoint celui de son compromis. La RPC des étiquettes garde celle du plus petit numéro :
**dans les 10, c'est le compromis** (5355 < 5356, etc.), donc **l'étiquette du compromis reste** et celle
de l'offre seule disparaît — 10 fusions la nuit suivante, le seuil de 10 criera. ⚠ Après les avoir
écrites, le **rejeu** (le gabarit du temps 3) nommera chaque dossier qui bouge : 10 attendus, pas un de
plus.

### 2.7 ✅ ÉCRITES ET REJOUÉES — sa décision du 19/11 : « VALIDÉES, les dix »

**Ses mots** : *« Écris-les dans rattachements_manuels.csv et commite. Le fichier doit passer de 6 à 16
décisions, pas une de plus. Je sais qu'elles agiront dès le run de cette nuit, et je l'accepte. »*

Les 10 lignes sont dans `phase2/sync/rattachements_manuels.csv`, sous un en-tête daté qui dit
pourquoi. Rejeu : `phase2/checks/temps4_rattachements_10_menages_2026-11-19.py` (lecture seule, la vraie
fonction, le fichier SANS les 10 fabriqué dans un dossier temporaire) →
`notice/TEMPS4_RATTACHEMENTS_10_MENAGES_REJEU_2026-11-19.csv`.

```
FICHIER    16 decisions (attendu 16) ; les 10 du 19/11 presentes a l'identique
BASE       le fichier SANS les 10 rend la base a 0 ecart (11 590 dossiers)
APRES      11 580 dossiers
POSITIF    10 offres sur 10 rejoignent le dossier de leur compromis
INVERSE    transactions qui bougent HORS des 10 offres : 0
GARDES     deux ventes 0 . deux compromis vivants 0 (avant comme apres)
ETIQUETTE  la RPC garde celle du COMPROMIS, 10 sur 10 ; celle de l'offre disparait
COMPTEUR   [M] rattachement decide a la main : 6 -> 16
LES DIX DOSSIERS QUI BOUGENT (l'offre quitte son dossier d'une transaction) :
   10955 5356->5355 . 11014 5408->5407 . 27037 13056->13055 . 35702 16866->16865
   36712 17278->17277 . 41584 20196->20195 . 42883 21339->21337 (3 membres) . 44276 22069->22068
   52724 26825->26824 . 55040 28328->28327
```

⏰ **CE QUE LA NUIT DOIT MONTRER** (le contrôle de demain matin, avant tout autre geste) : 11 580 dossiers
au lieu de 11 590 ; dans le journal du run, « 16 rattachement(s) à la main » ; à la pose des
étiquettes, **10 fusions** — ⚠ le cri `SEUIL_FUSIONS_QUI_INQUIETE = 10` (`>=`) **sonnera, et c'est
attendu** ; chacune des 10 offres porte l'étiquette de son compromis. Tout autre écart est un rouge.
⚠ **Non mesuré** : la RPC elle-même n'est pas rejouée (simulée : « le plus petit numéro garde ») ; et si
une autre écriture de la journée change le registre avant le run, le compte de 11 580 bougera avec elle.

---

## ③ LES DEUX OFFRES DU BIEN 61672 — protégées pour toujours

**Ce que j'ai fait** (une ligne) : lu le code qui pose `present_in_hektor`, et le carnet de ces deux
offres. Rien de plus.

```
LE CODE   affaire_ledger.py l. 1058-1096 : en fin de lecture, une transaction NON REVUE est
          marquee absente -- SAUF si l'app la « possede » : nee dans la plage app (>= 1 000 000),
          ou une ligne au CARNET (app_affaire_champ_app, local ou descendu), ou un travail en cours.
          Le commentaire le dit : « la resolution attend C.7 ».
LES DEUX  30712 (offre Hektor 33094) : 2 lignes au carnet, prix public 180 000 et 10 jours de
          retractation, origine modification_app du 13/10, etat « sans_objet »
          1001361 (offre Hektor 33098) : nee dans la plage app, ET les 2 memes lignes, creation_app
          du 13/10, « sans_objet »
          ⛔ une ligne « sans objet » ne quitte JAMAIS le carnet (rien a envoyer chez Hektor) : la
          protection ne tombe donc jamais. Chez Hektor elles ont ete remplacees le 27/10 (offre
          30767 et compromis 30769, revus chaque nuit).
CE QUE CA TOUCHE   aujourd'hui : CES 2 transactions et rien d'autre (temps 2 : 2 transactions
          presentes non relues). Mais le mecanisme est general : toute transaction saisie ou
          modifiee dans l'app, puis supprimee chez Hektor, restera « presente » et VIVANTE pour le
          chainage -- c'est elle qui fait le seul dossier « a deux offres acceptees ».
PISTE (rien n'est fait) : qu'une ligne « sans objet » ne compte plus comme possession ; ou que la
          protection ait une duree. C'est la decision C.7, deja nommee dans le code.
NON MESURE : combien de transactions portent aujourd'hui une ligne « sans objet » (donc seraient
          protegees si Hektor les supprimait demain).  ➡ MESURE le 19/11, ci-dessous.
```

**⭐ LA MESURE DEMANDÉE (19/11) — « 2 transactions ou 2 000 ? » : 12, et une seule en dépend.**
Lue deux fois, et les deux disent la même chose : le carnet LOCAL (`app_affaire_champ_app__sb`, descendu
ce matin) et Supabase EN DIRECT (`app_affaire_champ_app`).

```
LE CARNET ENTIER    48 lignes sur 12 transactions -- c'est tout. 46 « sans_objet », 2 « arrivee »
« SANS OBJET »      12 transactions (46 lignes) : 11 offres nees dans l'app (plage >= 1 000 000)
                    et UNE SEULE hors plage, 30712. Temoin positif : 30712 et 1001361 y sont.
                    Biens : 24113 (6 offres), 61672 (2), 62965 (2), 24933 (1), 61398 (1).
                    (Je n'ai PAS verifie si ce sont des biens d'essai.)
CE QUI EN DEPEND    la ligne « sans objet » ne protege SEULE qu'UNE transaction : 30712. Les 11
                    autres sont nees dans l'app : la PLAGE les protege deja, avec ou sans carnet.
LE VRAI PERIMETRE   c'est donc la PLAGE, pas le carnet : 530 transactions nees dans l'app, dont
                    340 presentes. Toutes sont « possedees pour toujours ». Aujourd'hui, une
                    seule n'a pas ete relue au dernier passage (1001361), et au total 2
                    transactions presentes non relues (30712 et 1001361 -- les deux de 61672).
REPONSE             le defaut touche 2 transactions aujourd'hui. Il en touchera une de plus a
                    chaque transaction nee dans l'app (ou passee par le carnet) que Hektor
                    supprimera : le reservoir est de 340, pas de 2 000.
NON MESURE          combien des 340 Hektor supprimera, et a quel rythme (2 en un mois, les deux
                    du meme bien d'essai).
```

---

## ④ LA « FUSION » DU 18/11 — un transfert compté comme une fusion

**Ce que j'ai fait** (une ligne) : lu la RPC `app_poser_etiquettes_dossier`, et compté dans le journal
les fusions dont l'étiquette « absorbée » vit encore. Rien de plus.

```
L'EXPLICATION   la RPC fait pose -> propagation -> FUSION -> scission. Sa fusion se declenche des
                qu'UN GROUPE porte plusieurs etiquettes, et garde celle de LA TRANSACTION AU PLUS
                PETIT NUMERO (son commentaire dit « la plus ancienne » : c'est faux, le code
                trie par app_affaire_id). Le 18/11, le dossier 14006 a recu UNE transaction venue
                d'ailleurs (1001593, la copie C5 de l'offre 14008) portant l'etiquette a633d3ec
                d'un autre dossier (14007-14009) : la RPC a « fusionne », c'est-a-dire reetiquete
                1001593 -- alors que a633d3ec continuait de vivre sur 14007-14009.
LE COMPTEUR     OUI, IL PEUT ENCORE SE TROMPER, de deux facons :
   PEUT-IL      . il compte un TRANSFERT comme une fusion : 1 « fusion » sur 6 dans le journal
   ENCORE SE      (celle du 18/11) n'a fait disparaitre aucune etiquette ;
   TROMPER ?    . a l'inverse, quand la transaction qui ARRIVE a le plus petit numero, c'est
                  l'etiquette DU DOSSIER ENTIER qui est absorbee -- 16 des 35 reunions de la
                  regle E seraient dans ce cas.
CE QU'IL FAUT EN TIRER POUR ⑧ : compter les etiquettes qui disparaissent ne suffit pas ; le
                controle apres l'ecriture du Sheet devra comparer, LIGNE PAR LIGNE, l'UUID publie
                a l'etiquette que portent AUJOURD'HUI les transactions de la ligne.
NON MESURE      la frequence d'un transfert hors de nos gestes (un seul en 7 jours, et c'etait C5).
```

---

## ⑤ LES 48 « À JUGER » — tranchés par le classeur, colonne indépendante nommée

**Le script** : `phase2/checks/temps5_q5_les_48_a_juger_par_le_classeur_2026-11-19.py` (lecture seule : la
base en `mode=ro`, le Sheet par un GET en direct — 4 797 lignes ce 19/11). Sorties :
`notice/TEMPS5_Q5_PAIRES_JUGEES_PAR_LE_CLASSEUR_2026-11-19.csv` (62 paires) et
`notice/TEMPS5_Q5_LES_48_DOSSIERS_VERDICT_2026-11-19.csv` (48 dossiers).

### 5.1 Les colonnes du juge — et pourquoi elles ne sont pas circulaires

```
LUES (jamais recopiees dans les colonnes de Hektor qu'elles jugent) :
   S  « Offre Achat »          contre la PROPOSITION ou l'ACCEPTATION de l'offre (propositions_json,
                               le journal de Hektor) -- jamais la colonne `date` (nos refus l'ont bougee)
   T  « Compromis »            contre la date du compromis chez Hektor
   V W X « Vente Prevue / Fixee / Signee »   contre la date de la vente chez Hektor
   AB « Acquereur »            contre les noms de acquereurs_json (Hektor)
   AF « Prix »                 contre `montant` (Hektor), a 1 %
   C  « Mandat »               contre `numero_mandat` (Hektor ; notre numero_mandat_app n'est PAS lu)
JAMAIS LUES (nous les avons posees, C1 a C9) : Y Vente Reglee . Z Annulee . AA facture . P Commission .
   Q Charge . F . G . AH-AJ avis . R Etat Actuel (nos refus en derivent). Toute date >= 11/11/2026
   est ignoree (nos gestes) ; les 190 transactions creees depuis le Sheet sont ignorees.
LE GEL n'est lu qu'APRES le verdict, pour comparer.

UNE LIGNE DESIGNE UNE TRANSACTION si DEUX colonnes independantes au moins s'accordent :
   DATEE      la date du genre (a un jour pres) + le nom (AB) OU le prix (AF) OU le mandat (C)
   SANS DATE  la case du genre VIDE au Sheet : mandat + nom + prix, les trois ensemble
VERDICT     MEME LIGNE (une seule affaire) . DEUX LIGNES (deux affaires) . AMBIGU (une ligne designe
            deux transactions du meme genre, ou une transaction est designee par deux lignes) .
            UNE SEULE / AUCUNE (non tranche)
```

**Comment le juge a été construit — et ce que ça vaut.** La première version (date + nom ou prix)
a fait **échouer son témoin** : 5 paires « correction » du temps 3 tenues sur une seule ligne. Je ne
l'ai pas cru : je les ai **lues à la main** sur le Sheet. Résultat : deux défauts du JUGE (une
ambiguïté — deux offres le même jour au même prix, bien 47815 — et le prix AF qui n'est souvent pas le
montant), et un défaut du TEMPS 3 : sa famille « correction » avait été classée **sur les noms**, et
le Sheet en renverse une partie. Le juge a gagné l'ambiguïté et la colonne C (mandat), et la famille
« correction » n'est plus un témoin.

```
LE TEMOIN, rejoue sur la version finale -- tout vert :
   ⭐ INDEPENDANT du juge : la ligne 8Q3LHGZ4, jugee FAUSSE par l'audit V2 (une affaire CHEVALIER de
      2023, mandat 16239, que le gel relie au compromis 8321 et a l'offre 8322 de 2014) -> AUCUNE.
      Le juge ne se laisse pas prendre la ou le gel s'est trompe.
   les 10 menages (valides le 19/11) -> 3 MEME LIGNE, 6 absents du Sheet, 1 UNE SEULE, 0 DEUX LIGNES.
      La « une seule » est PARIS (26825-26824) : la ligne WUQ5445T porte l'offre du 20/02/2020, une case
      compromis VIDE, un prix tape « 43 », et s'annule le 20/06/2020 -- un mois apres le compromis du
      21/05/2020. ⭐ RIEN NE CONTREDIT TA DECISION SUR LES 10.
   relus a la main, rejoues pour qu'il ne regresse pas (ils ont SERVI a le construire, ils ne prouvent
      pas son independance) : 10374, 28673 (x3), 47815 (AMBIGU), 36794, 43114, 1950, 12728 (AMBIGU)
```

### 5.2 Le verdict des 48

```
PAR DOSSIER     8 CASSES CONFIRMEES par le Sheet   (une ligne porte les deux transactions separees)
                5 CORRECTIONS CONFIRMEES           (deux lignes : le geste a separe deux affaires)
                1 MIXTE -- lu a la main (15722)
               34 NON TRANCHES : 32 paires dont NI le juge NI le gel ne trouvent la moindre ligne
                  (deux methodes independantes : le Sheet ne porte pas ces affaires, de 2008 a 2025) ;
                  3 dont l'autre cote est une creation C5 (circulaire par construction) ; 3 a une seule
                  ligne ou ambigus (11820, 35716, 49941)
PAR PAIRE (62)  AUCUNE 34 . MEME LIGNE 9 . DEUX LIGNES 9 . UNE SEULE 7 . AMBIGU 3
LE GEL, APRES   les desaccords avec le juge sont lus en 5.4
```

⭐ **Ce que ça change pour l'écriture du Sheet (⑧)** : les 34 non tranchés **n'ont aucune ligne au
Sheet** — on n'y écrira donc aucune étiquette, et leur sort ne peut pas fausser la colonne
`affair_uuid`. Ils restent tels que nos gestes les ont laissés, et ce n'est pas un risque pour le BUT.

### 5.3 ⭐ Ce que le Sheet RENVERSE ailleurs — 5 « corrections » du temps 3 sont des CASSES

Le temps 3 rangeait en « correction » un dossier coupé entre **deux noms à plus d'un mois**. Le Sheet,
lui, porte **une seule ligne** pour ces 5-là — c'est **la même affaire**, et Hektor porte sur le
compromis le contact d'un AUTRE (le défaut connu « l'acheteur précédent reste sur le compromis
suivant ») :

```
10374  ligne VUNYM8UV  offre VIALLE 04/07/2020 + compromis 25/09/2020 (au nom de MEYRAND chez Hektor)
10396  ligne NTLQIZLO  offre URBAIN 15/06/2019 + compromis 01/08/2019 (au nom de PLAY)
15439  ligne 7PBRZJD8  offre sans acquereur 05/06/2023 + compromis GASMI 17/07/2023
28673  ligne EC977D21  offre CHARLES 23/08/2021 + compromis 30/09/2021 (au nom de LYONNET, l'acheteur
                       d'avril, ligne 6D1WSAK8)
35735  ligne 80OY9IUH  offre BOUCHARD 29/11/2019 + compromis 18/05/2020 (au nom de CHARRA MEILLER)
```
⚠ **Et une question ouverte reçoit un élément, sans être tranchée** : le compromis DEBARD 20088 (sans
date, 50 000) est désigné par le **prix** de la ligne ZW7MKTWH (la 2ᵉ offre, 50 000), pas par 5QE9107L
(la 1ʳᵉ, 55 000) où le gel l'a mis. C'est TA question `5QE9107L` : le Sheet penche pour la 2ᵉ offre. Je
ne touche à rien — « un patch ne tranche pas une question ouverte ». (Pour le chaînage, c'est sans
effet : les deux offres DEBARD sont dans le même dossier.)

### 5.4 Les 13 casses (8 + 5) — 8 se réparent d'une ligne, 5 demandent une SCISSION

```
PURES -- le dossier du compromis ne porte QUE cette affaire : UNE LIGNE du fichier la repare.
   bien   offre -> compromis      la ligne du Sheet
   1950    988 -> 987    566d1a48  offre sans acquereur 27/06/2025 + compromis EL FAQRAOUI, 66 000
   10374  4907 -> 4906   VUNYM8UV  VIALLE 04/07/2020, 16 000
   10396  4932 -> 4931   NTLQIZLO  URBAIN 15/06/2019, 119 000
   15439  7600 -> 7599   7PBRZJD8  offre sans acquereur 05/06/2023 + compromis GASMI, 330 000
   30678 14928 -> 14927  05e8ddb5  offre sans acquereur + compromis BEZIER GUILLEMIN (sans date), 120 000
   35735 16879 -> 16878  80OY9IUH  BOUCHARD 29/11/2019, 58 000
   43432 21799 -> 21798  26283bf9  offre sans acquereur + compromis BESSET 10/11/2025, 56 000
   50165 25992 -> 25991  600f4e1c  offre sans acquereur + compromis MAGAND 10/12/2025, 153 000
MELANGEES -- Hektor a laisse le contact de l'acheteur PRECEDENT sur le compromis du suivant, et la
   regle D (« meme numero d'acheteur ») a COLLE ce compromis dans le dossier du precedent. Une ligne du
   fichier completerait l'affaire mais garderait le melange : il faut SEPARER, et le fichier ne sait
   que REUNIR.
   28673  {14142 CHARLES + 14141}              colle a LYONNET {14143}
   36794  {17322 FAUVET + 17320 + vente 17324} colle a CREVON {17321, 17323}
   37192  {17435 MORSI BARAKAT + 17432}        colle a THOMAS {17433, 17436} ET a LEONE {17434} --
          3 lignes du Sheet (IT0BF6M4, D96KSCYQ, 3ID282Y1) pour un seul dossier
   43114  {21586 BIGONNET + 21585}             colle a BEIKES {21584, 21587}
   43126  {21600 ZEMMA + 21598}                colle a FERRARI {21597, 21599, vente 21601}
   + le MIXTE 15722 : {7780 DE OLIVEIRA + 7778 + vente 7782} colle a COLOMBET {7779, 7781}
```
⛔ **Je n'ajoute AUCUNE ligne au fichier** (ta consigne). Les 8 lignes « pures » sont prêtes, au format
du fichier, pour ta décision (§ 5.6). Pour les 6 mélangés, il n'existe aucun outil : voir ⑨.

**Le gel, lu après coup — deux erreurs qu'il porte** (pour ⑦) : **15722**, l'offre 7780 (DE OLIVEIRA,
04/05/2021) est liée à VEP1DVQ4 (la ligne COLOMBET) au lieu de 2SCBZXMH, et l'offre 7781 (COLOMBET,
01/04/2021) n'est liée à rien ; **12728**, les deux compromis du 30/04/2021 (6554 à 90 000 annulé, 6555 à
87 000 actif) sont liés « à l'envers » au regard de l'état et du prix (la ligne vendue EGR8KXOL à
87 000 a reçu l'annulé à 90 000) — le juge, lui, les déclare AMBIGUS et ne tranche pas.

### 5.5 Ce que je n'ai pas mesuré

```
. les 34 non tranches : le Sheet ne les porte pas ; le REGISTRE seul ne sait pas les trancher (temps 3).
  Ils restent comme nos gestes les ont laisses. Non mesure : s'ils etaient reunis AVANT nos gestes a raison.
. l'ampleur du MELANGE « contact de l'acheteur precedent + regle D » sur TOUT le registre : je l'ai vu
  sur 6 dossiers des 79 coupes par nos gestes. ⑥ en donne une mesure par l'autre bout (une etiquette
  sur plusieurs lignes du Sheet).
. le juge a un jour de tolerance sur les dates ; une date du Sheet decalee de plus (saisie tardive)
  rate la ligne -- le sens de l'erreur est « non tranche », jamais « tranche a tort ».
```

### 5.6 Les 8 lignes « pures » — PROPOSÉES, NON écrites (ta décision)

```
988;987;1950;2026-11-19;EL FAQRAOUI -- ligne 566d1a48 : offre (sans acquereur chez Hektor) du 27/06/2025 et compromis, 66 000 EUR
4907;4906;10374;2026-11-19;VIALLE -- ligne VUNYM8UV : offre du 04/07/2020 et compromis du 25/09/2020 (au nom de MEYRAND chez Hektor), 16 000 EUR
4932;4931;10396;2026-11-19;URBAIN -- ligne NTLQIZLO : offre du 15/06/2019 et compromis du 01/08/2019 (au nom de PLAY chez Hektor), 119 000 EUR
7600;7599;15439;2026-11-19;GASMI -- ligne 7PBRZJD8 : offre (sans acquereur) du 05/06/2023 et compromis du 17/07/2023, 330 000 EUR
14928;14927;30678;2026-11-19;BEZIER GUILLEMIN -- ligne 05e8ddb5 : offre (sans acquereur) et compromis sans date, 120 000 EUR
16879;16878;35735;2026-11-19;BOUCHARD -- ligne 80OY9IUH : offre du 29/11/2019 et compromis du 18/05/2020 (au nom de CHARRA MEILLER chez Hektor), 58 000 EUR
21799;21798;43432;2026-11-19;BESSET -- ligne 26283bf9 : offre (sans acquereur) et compromis du 10/11/2025, 56 000 EUR
25992;25991;50165;2026-11-19;MAGAND -- ligne 600f4e1c : offre (sans acquereur) et compromis du 10/12/2025, 153 000 EUR
```
⚠ Non rejouées : elles ne sont pas dans le fichier. Si tu les valides, le rejeu (gabarit du § 2.7)
nommera 8 dossiers qui bougent, pas un de plus — et **pas la même nuit que la règle E** (un geste par
nuit).
⛔ **Lu dans le code, une réserve sur 30678** : le compromis 14927 est **SANS DATE**. Tant que la règle E
est éteinte, il n'entre pas dans `toutes`, et le fichier dirait la ligne « transaction introuvable »
(c'est le trou du § 1.1). Cette ligne-là ne jouera **qu'après l'allumage de E** — les 7 autres jouent
avec E éteinte.
⭐ **Rejoué depuis, en simulation (⑥)** : avec la règle E allumée, les 8 lignes réunissent bien 8 dossiers
(11 546 → 11 538), 30678 compris.

---

## ⑥ LES 255 LIGNES À PLUSIEURS ÉTIQUETTES — ce qu'elles deviennent après les corrections

**Le script** : `phase2/checks/temps5_q6_les_lignes_a_plusieurs_etiquettes_2026-11-19.py`, **découpé en
étapes** (`rejeu 1`, `rejeu 2`, `rejeu 3`, `compte`, `classer`) — la première mesure, d'un seul bloc, a
été tuée par son délai à 13 h et sa sortie était vide (Python retenait tout en mémoire). Chaque étape
écrit maintenant son résultat sur le disque (`C:\Hektor\chantier_classeur_q6_cache\`, hors du dépôt)
et imprime au fil de l'eau. Durées réelles : 7 s, 11 s, 13 s par rejeu ; le classement, Sheet compris,
moins de 10 minutes. Sorties : `notice/TEMPS5_Q6_COMPTES_PAR_SCENARIO_2026-11-19.md` et
`notice/TEMPS5_Q6_LIGNES_A_PLUSIEURS_ETIQUETTES_2026-11-19.csv`.

### 6.1 Le compte, scénario par scénario

**Pourquoi on peut compter par dossiers** : après la pose de nuit, une étiquette = un dossier. ⭐ **Vérifié
sur la base d'aujourd'hui** : 255 lignes à plusieurs étiquettes, 255 lignes à plusieurs dossiers, **0 de
différence**. Et le scénario 1 ne diffère de la base que par **les 10 offres du 19/11, aucune autre**.

```
LIGNES DU SHEET A PLUSIEURS ETIQUETTES          gel tel quel   gel apres le patch V2
   0 la base d'aujourd'hui                           255              243
   1 + les 10 menages (CETTE NUIT, decide)           251              239
   2 + la regle E avec l'exclusion (simulee)         249              237
   3 + les 8 lignes pures de ⑤ (simulees)            241              229
CHAQUE CORRECTION NE FAIT QUE REGLER -- aucune ne cree une ligne nouvelle :
   les 10 menages : 4 lignes reglees (les 6 autres menages n'ont pas de ligne au Sheet -- cf. ⑤)
   la regle E     : 2 . les 8 lignes de ⑤ : 8
   LE PATCH V2    : 16 reglees, MAIS 4 NOUVELLES -- 2SCBZXMH, 3W10AEIK, TRJ5Y59U, f90b0418 (⑦)
```

### 6.2 Ce qui reste au bout — 229 lignes, classées par le juge de ⑤

```
128  C5 -- une transaction creee depuis le Sheet est coupee de son dossier (la scission du 18/11)
        105 PURES : la creation est seule dans son dossier, le reste de la ligne dans UN autre
         23 dans un dossier qui porte aussi une autre ligne
 74  LE SHEET LES TIENT -- la ligne designe, par ses propres colonnes, une transaction de CHAQUE
     dossier : le chainage coupe une affaire que le Sheet tient en une ligne
          8 PURES : chaque dossier ne porte que cette ligne -> UNE ligne du fichier la reparerait
         66 MELANGEES : un des dossiers porte AUSSI une autre ligne du Sheet -- c'est la famille de ⑤
            (« le contact de l'acheteur precedent » + la regle D) : il faudrait SEPARER
            dont 2SCBZXMH (15722), 5GZVT548 (36794), 9K4Y3S4N (43126), 3ID282Y1 (37192)...
 26  LE GEL DEBORDE -- un des dossiers n'a AUCUNE transaction que la ligne designe : le lien vient
     du gel seul, a relire comme une erreur possible du gel (12 pures, 14 melangees)
  1  NON TRANCHE (f90b0418, une des 4 nouvelles du patch V2)
```

### 6.3 L'autre bout — une même étiquette sur PLUSIEURS lignes

Une ligne à plusieurs étiquettes empêche d'écrire **une** étiquette. L'inverse empêche d'écrire une étiquette
**qui ne désigne qu'une affaire** : au bout (scénario 3, gel V2), **207 dossiers sont tenus par 2 ou 3
lignes du Sheet** (431 lignes ; 190 dossiers à 2 lignes, 17 à 3). Écrire leur étiquette mettrait le MÊME
`affair_uuid` sur deux ou trois affaires. Certains sont légitimes (le classeur a des doublons :
« annulée » puis re-saisie, 6 groupes connus), la plupart sont les mélanges de ⑤. ➡ **C'est le second
bouchon de ⑧, aussi lourd que le premier.**

### 6.4 Le verdict de ⑥

```
LE NOYAU DUR NE BOUGE PAS AVEC LES CORRECTIONS DU REGISTRE. Elles reglent 26 lignes sur 255 (10 %).
Ce qui reste a trois natures, et AUCUNE ne se regle par une regle de chainage :
   C5 (128)       une decision deja posee et en attente (« rattacher a la main, ou choisir
                  l'etiquette a l'export ? ») -- ⭐ pour ⑧, la seconde suffit : une creation C5 ne
                  decide JAMAIS de l'etiquette d'une ligne ; on prend celle des transactions de Hektor
   MELANGES (66+) une SCISSION, que rien ne sait faire aujourd'hui (⑨)
   GEL (26)       une relecture de ces liens, comme l'ont fait les deux audits
➡ POUR ⑧ : on n'ecrit PAS ces lignes. On ecrit d'abord les lignes qui n'ont AUCUN de ces defauts
  (⑧ les compte), et le noyau attend ses decisions.
```

### 6.5 Ce que je n'ai pas mesuré

```
. les 74 « le Sheet les tient » ne sont pas relus a la main un par un : le classement ne teste pas
  l'ambiguite (deux offres le meme jour au meme prix) que le juge de ⑤ teste paire par paire
. les 207 dossiers a plusieurs lignes : ni compte des doublons legitimes, ni des melanges
. la RPC de nuit n'est pas rejouee : « une etiquette = un dossier » est verifie sur la base
  d'aujourd'hui, et suppose pour les scenarios
```

---

## ⑦ LE PATCH DU GEL V2 — relu par moi : il tient, et je te redemande ton « vas-y »

`supabase/patch_correction_gel_audit_v2_2026-11-19.sql` (45 retraits, 78 ajouts, 12 787 → 12 820), son
inverse et sa répétition. **Rien n'a été joué** : toutes les vérifications ci-dessous sont des lectures
(Supabase en direct, le Sheet par un GET, la copie locale).

### 7.1 Tient-il toujours ? — OUI, ses quatre gardes passeraient aujourd'hui

```
GARDE 1  le gel est celui qu'ont lu les audits : 12 787 liens, empreinte 8084e535f51ba904a839bfe0bcc88a55
         -> IDENTIQUE chez Supabase ce 19/11 apres-midi (dernier lien gele le 18/11 10:53) ;
         la sauvegarde app_classeur_lien_avant_audit_v2_20261119 n'existe pas (jamais joue)
GARDE 2  chaque lien a retirer existe avec son role ........................ manque   0
GARDE 3  chaque cible existe au registre et porte le genre de son role ...... cible_ko 0
GARDE 4  chaque cible sera libre (aucune autre ligne ne la tient) ........... deja     0
⭐ LE ZERO A SON TEMOIN : trois fautes semees, une par garde (un lien inexistant ; 7778, un
  compromis, seme en offre ; 7778, tenu par 2SCBZXMH, seme sur une autre ligne) -> 1, 1, 1.
  Les gardes savent mordre ; leur zero d'aujourd'hui est vrai.
```
Les gardes ont été rejouées **en lecture**, extraites du fichier lui-même (le bloc `do $$` réécrit en
trois `select`, contrôlé : aucun mot d'écriture), pas recopiées à la main.

### 7.2 Les deux erreurs du gel trouvées en 5.4 — le patch les corrige, EXACTEMENT

C'est une **confirmation indépendante** : le juge de ⑤ a été construit sans lire le patch, et le patch
sans connaître le juge.
```
15722  le juge : l'offre 7780 (DE OLIVEIRA, 04/05/2021) appartient a 2SCBZXMH ; 7781 (COLOMBET,
       01/04/2021) a VEP1DVQ4, ou elle n'etait pas
       le patch : retire VEP1DVQ4 <- 7780, ajoute 2SCBZXMH <- 7780 ET VEP1DVQ4 <- 7781        ✅
12728  le juge : les deux compromis du 30/04/2021 sont lies a l'envers (la ligne vendue EGR8KXOL
       a 87 000 tenait l'annule a 90 000) -- il les disait AMBIGUS, sans trancher
       le patch : EGR8KXOL <- 6555 (87 000, actif) et Q602VZJX <- 6554 (90 000, annule)       ✅
et 8Q3LHGZ4 (le temoin independant de ⑤) : le patch retire 8321 et 8322                       ✅
```

### 7.3 Ce qu'il change au compte de ⑥ — 16 lignes réglées, 4 révélées

```
sur chaque scenario de ⑥ : 16 lignes a plusieurs etiquettes REGLEES, 4 NOUVELLES
   (0 : 255 -> 243 . cette nuit : 251 -> 239 . au bout : 241 -> 229)
LES 4 NOUVELLES NE SONT PAS DES REGRESSIONS : le gel devient VRAI, et un gel vrai montre une casse
du chainage que le lien faux cachait.
   2SCBZXMH  7780 rejoint sa vraie ligne -> on VOIT le melange de 15722 (⑤ 5.4)
   3W10AEIK  l'offre de la ligne est 4748 (VINCENT, 21/01/2021), pas 4747 (BELLAT) : 4748 est seule
             dans son dossier, le compromis 4746 est dans celui de BELLAT (4745)
   TRJ5Y59U  la copie C5 1001561 sort, la vraie offre 23995 (GAY) entre : nos refus du 11/11 l'ont
             laissee seule
   f90b0418  l'offre 19050 (POULY et CHARTOIR) rejoint la ligne de son compromis 19049 -- meme
             acquereur 544474 ; 19049 est SANS DATE et reste seul meme avec la regle E -- a lire
```

### 7.4 Ce que j'ai encore vérifié

```
. il ne touche AUCUNE transaction decidee ou proposee aujourd'hui : 26613, les 20 des 10 menages,
  les 16 des 8 lignes de ⑤ -- ni 30767 / 30769 (⭐ il retire de la ligne 45225170 les deux offres
  perimees du bien 61672, 30712 et 1001361 : la question ③ vue du gel)
. les NUMEROS DE LIGNE qu'il ecrit sont justes : le Sheet a pris des lignes depuis cette nuit (4 797,
  les dernieres en 4801-4803), mais A LA FIN -- 0 des 78 ajouts n'a une ligne_classeur differente de
  la ligne actuelle de son ID Unique, et 0 des 4 703 couples du gel n'est perime
. sa repetition attend 71 lignes sans lien : simule, 91 - 26 (premier lien) + 6 (videes : 1ESJE28Q,
  Y51UMZHY, 8Q3LHGZ4, WJ3KA32F, NEFHS7JI, a8aaeb2b) = 71
. son INVERSE ne juge que SA part (lecon 31) : il retire ce que gele_par = 'audit_independant_v2_
  2026-11-19' a pose, remet les 45 retraits a l'identique depuis la sauvegarde, et DIT un ecart venu
  d'un autre geste sans refuser de tourner. Il porte son commit;, comme le patch.
. ⚠ le patch porte son `commit;` : joue « pour voir », il se commite. Il ne se colle qu'avec ton accord.
```

### 7.5 Ce qu'il NE fait pas — le geste suivant, à enchaîner

```
. 10 transactions detachees d'une ligne portent une valeur que NOUS avons posee depuis le Sheet
  (honoraires, dates d'annulation...), et 15 une note « classeur » : elles doivent DESCENDRE vers la
  bonne transaction -- la repetition les compte (attendu 10 et 15 avant ce nettoyage)
. les copies C5 detachees se retirent ensuite, des DEUX cotes (le local est maitre de la plage app)
. ni Hektor, ni les 8 lignes incertaines, ni les 18 lignes a question ouverte (sorties du patch)
```

### 7.6 Mon avis, et ce que je te demande

**Il tient, et je recommande de le jouer** — mais **pas cette nuit** : cette nuit est celle des 10 ménages
(un geste par nuit). Le patch ne dépend pas du chaînage (gel et chaînage sont indépendants), il s'écrit chez
Supabase **en plein jour**, et sa répétition le juge en une minute : demain, **après** le contrôle des 10,
puis la règle E une nuit suivante. ⛔ **Je ne le joue pas sans ton « vas-y ».**

### 7.7 Ce que je n'ai pas mesuré

```
. l'effet du patch sur les VALEURS posees (honoraires, notes) au-dela du compte de sa repetition
. f90b0418 : pourquoi 19049 (compromis SANS DATE, meme acquereur que 19050) reste seul avec E
. l'ordre de collage contre la descente de 07:45 : le gel est maitre chez Supabase et la descente le
  RECOPIE en local -- un collage avant 07:45 serait recopie le matin meme, apres, le lendemain
```