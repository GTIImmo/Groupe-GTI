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

**État des questions** : ① lue, jugée, et sa garde REJOUÉE (§ 1.7) · ② en cours · ③ à ⑨ à suivre.

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

---

## ④ LA « FUSION » DU 18/11 — ce qui est déjà établi (la suite au tour de ④)

La RPC procède dans l'ordre pose → propagation → **fusion** → scission. Sa fusion se déclenche dès
qu'**un groupe porte plusieurs étiquettes**, et garde celle de **la transaction au plus petit numéro**.
Le 18/11, le dossier 14006 a reçu une seule transaction venue d'ailleurs (1001593, la copie C5 de
l'offre 14008), qui portait l'étiquette a633d3ec d'un autre dossier (14007-14009). La RPC a « fusionné »
— c'est-à-dire réétiqueté 1001593 — **alors que a633d3ec continuait de vivre sur 14007-14009**.
➡ **Le compteur de fusions compte un TRANSFERT comme une fusion.** Et il peut aussi absorber
l'étiquette d'un dossier entier quand c'est la transaction qui arrive qui a le plus petit numéro.
