# Protocole de test — comment Hektor réagit aux transactions

**Décidé par Frédéric le 01/09/2026.** Tous les gestes sont faits **depuis l'app**, par lui, en
compte admin. Je relève à chaque étape, je n'écris rien.

> *« il faut être sûr de l'interaction des statuts chez Hektor… ce test permettra aussi de valider
> la chaîne et de faire une analyse et un audit de la situation »*

---

## 1. La question à trancher

**Hektor recalcule-t-il le statut d'un bien quand une transaction naît, change d'état, ou meurt ?**

Elle est ouverte parce que mes deux dernières réponses se sont révélées trop larges, et qu'elles
reposaient chacune sur **un seul cas**. Ce protocole existe pour ne plus conclure d'un cas unique.

### Ce qui en dépend

```
   la regle de redescente     deja codee (7e035e7). Est-elle indispensable, ou fait-elle
                              double emploi avec un mecanisme d'Hektor ?
   la decision « C+ »         faut-il renvoyer le statut corrige A Hektor, sans toucher
                              la diffusion ? Frederic y est favorable.
   un point de dev nouveau    faut-il apprendre a l'app a SUPPRIMER une offre et un
                              compromis ? Aucun worker ne l'a jamais fait.
```

---

## 2. Ce qui est DÉJÀ établi — à ne pas retester

| fait | comment on le sait | solidité |
|---|---|---|
| Le worker envoie **exactement** l'appel de l'écran Hektor : un seul, `annonce-SuiviVente-updateOffre` | relevé DOM du 28/08, session admin | **sûr** |
| **Supprimer** un compromis fait redescendre le statut tout seul | observé le 28/08 | 1 cas |
| **Refuser** une offre n'a pas fait redescendre le statut | 01/09, API relue à 1 h 30 | 1 cas |
| **Annuler un compromis ne refuse PAS l'offre** | 1 194 paires : 60 % restent `accepted` | **mesuré** |
| L'app ne sait **ni** supprimer une offre **ni** supprimer un compromis | code + confirmation de Frédéric | **sûr** |
| Hektor stocke un **historique d'événements**, pas un état | écran du 01/09 : 6 badges sur une offre | **sûr** |
| Notre base est **fidèle** à Hektor | comparaison écran/base du 01/09 | **sûr** |

---

## 3. Le principe de mesure — c'est lui qui fait tout le test

**Trois relevés par geste.** Sans les trois, on ne voit rien : c'est exactement ce qui m'a échappé
le 01/09 au matin.

```
   T0   avant le geste                     l'etat de depart
   T1   ~10 s apres, job « done »          ce que NOTRE APP a pose
   T2   ~90 s apres, resynchro passee      ce que HEKTOR dit
```

```
   T2 different de T1   ->  HEKTOR A RECALCULE. On note quoi, et dans quel sens.
   T2 identique a T1    ->  HEKTOR NE RECALCULE RIEN. Notre regle est indispensable.
```

### Ce qu'on relève, à chacun des trois temps

```
   1  le STATUT du bien                 API Hektor (statut + statut_nom) et ecran
   2  l'etat de CHAQUE transaction      offre(s), compromis, vente -- pas seulement
                                        celle qu'on vient de toucher : les CASCADES
                                        sont invisibles autrement (ajout de Frederic)
   3  diffusable                        il ne doit JAMAIS bouger tout seul
   4  ce que le worker a envoye         payload du job + ses logs
```

**L'ajout n° 2 vient de Frédéric**, et il est décisif : sa question *« annuler un compromis met-il
l'offre en refusée ? »* n'aurait pas eu de réponse si on n'avait relevé que le statut.

---

## 4. La liste des actions, dans l'ordre

### Étape 0 — le bien neuf

```
[ ]  creer un bien de test DEPUIS L'APP, chez GONZALEZ / Firminy
     nom propose : « TEST STATUTS 01-09 »
```

**On ne teste pas sur 62774.** Il a reçu 25 changements de statut à la main et six transactions
empilées ; on ne saurait pas distinguer le geste de l'accumulation. Il reste comme **témoin**,
sans qu'on y touche.

> ⚠ **Inconnue à lever dès l'étape 0** : la création passe par `create_hektor_draft_annonce`,
> donc un **brouillon**. Faut-il un mandat pour poser une offre dessus ? On le découvre à
> l'étape 1 ; si ça bloque, on ajuste — le cœur du test est ailleurs.

### La montée — comment naît une transaction

| # | geste depuis l'app | ce qu'on cherche à savoir |
|---|---|---|
| **1** | statut → **Sous offre** | l'offre est-elle créée ? le statut tient-il en T2 ? |
| **2** | **accepter** l'offre | le statut bouge-t-il ? |
| **3** | statut → **Sous compromis** | l'offre acceptée est-elle liée au compromis, ou ignorée ? |
| **4** | statut → **Vendu** | et le compromis, que devient-il ? |

### La descente — le bloc décisif

| # | geste depuis l'app | ce qu'on cherche à savoir |
|---|---|---|
| **5** | **supprimer la vente** | redescend-il ? à « Sous compromis » ou à « Actif » ? **le compromis se rouvre-t-il ?** |
| **6** | **annuler le compromis** | redescend-il à « Sous offre » ? **l'offre passe-t-elle en refusée toute seule ?** |
| **7** | **refuser l'offre** | redescend-il à « Actif » ? *(c'est le cas du 01/09, rejoué proprement)* |

```
   AUCUN des trois ne redescend  ->  la regle est indispensable, et C+ s'impose
   L'UN des trois redescend      ->  on saura lequel, et la regle se borne aux autres
```

### Les cas particuliers

| # | geste | ce qu'on cherche à savoir |
|---|---|---|
| **8** | deux offres, une acceptée une refusée | quel statut Hektor retient-il ? |
| **9** | poser **« Sous compromis »** à la main, sans compromis | l'observation du 28/08 se reproduit-elle ? |
| **10** | créer une offre alors qu'un compromis existe | Hektor l'accepte-t-il ? le statut bouge-t-il ? |

### Hors d'atteinte depuis l'app — et c'est un résultat en soi

```
   supprimer une OFFRE       deleteOffre        jamais code
   supprimer un COMPROMIS    deleteCompromis    jamais code
```

Or c'est précisément **supprimer** un compromis qui, le 28/08, a fait redescendre le statut. Les
deux gestes qu'on soupçonne d'être les seuls déclencheurs sont exactement les deux que l'app ne
sait pas faire. **Si le bloc descente ne redescend jamais, cette lacune devient le point de dev
central.**

---

## 4bis. CE QUI A ETE FAIT LE 01/09 — et pourquoi on s'arrete la

**SUSPENDU par Frederic le 01/09**, et la raison est juste : *« ce test est tres complique
puisque nous sommes en plein plan dev sur l'autonomie de l'apps et il n'est pas fini »*.

### Le bien

```
   EM28412  ·  annonce Hektor 24933  ·  app_dossier_id 1352132
   proprietaire « Test SELL AND SIGNE » -- c'est deja un bien d'essai
   mandat 11939, echu depuis le 29/03/2020
   acquereur retenu : 605075 « Test CLOTURE », Firminy / GONZALEZ
```

### Etape 0bis — Estimation -> Actif  ✅

Faite par Frederic. Le parcours reel passe par « Actif » avant l'offre ; mon protocole
voulait l'eviter pour ne pas allumer la diffusion, c'etait une entorse au realisme.

```
   T0   API statut 1 « Estimation »   ·  app Estimation  ·  diffusable 0  ·  0 transaction
   T2   API statut 2 « Actif »        ·  app Actif       ·  diffusable 1
        le bien change de LISTE dans l'ecran : Estimations -> Annonces actives
```

Chaine app -> worker -> Hektor -> resynchronisation **validee**, une seule tentative.
`diffusable` passe bien de 0 a 1, comme la table du worker l'annonce. Aucune passerelle sur
ce bien : rien n'est parti sur les portails.

### Etape 1 — Actif -> Sous offre  ✅

```
   T1  +10 s   job « running » ; ledger 1 001 324 cree
               kind offre · state « en_cours » · hektor_affaire_id VIDE
               present_in_hektor FALSE · 175 000 € · acquereur 605075 · mandat 11939
   T2  +90 s   API Hektor statut 3 « Sous offre »        ✓
               app « Sous offre »                         ✓
               offre_id du dossier : VIDE                 ✗
               ledger : hektor_affaire_id VIDE, present_in_hektor FALSE   ✗
```

**RESULTAT N° 1 — Hektor MONTE bien le statut a la creation.** Verifie en direct :
`createOffre` fait passer le bien « Sous offre » tout seul. La moitie HAUTE de l'asymetrie
decrite en section 1 de l'etude est confirmee.

**RESULTAT N° 2 — la reprise ciblee ne rapproche PAS la transaction.** Le
`refresh_console_data` s'execute entierement, sans erreur, et l'offre reste orpheline. Le
projet notait deja que le read-through ignore la couche transaction ; **c'est plus large que
note** : ce n'est pas seulement qu'un refus fait chez Hektor n'est pas rattrape, c'est
qu'une offre creee DEPUIS L'APP ne revient pas non plus.

➡ **Consequence pour l'utilisateur** : il cree une offre, voit le statut passer, mais
l'offre n'apparait pas dans sa fiche -- il ne peut ni l'accepter ni la refuser avant le run
de nuit. **Ce n'est pas un bug : c'est C.4 inachevee.** « Ecrire d'abord, envoyer, comparer
au retour » -- l'ALLER est fait, le RETOUR n'existe que par le run.

### Les deux pannes trouvees en chemin, et corrigees

```
1  LE COMPTEUR D'AFFAIRES ETAIT EN RETARD DE 306.
   app_affaire_id_app_seq a 1 000 017, plus grand numero pris 1 000 323. Il distribuait
   des numeros DEJA OCCUPES -> violation de cle -> « duplicate key » -> que le front
   traduisait en « Une action Hektor est deja en cours pour cette annonce ».
   AUCUNE creation de transaction ne pouvait aboutir, SUR AUCUN BIEN, DEPUIS LE 27/08.
   Recale a 1 001 323 (+1 000 de marge). Cause de fond NON corrigee : le run ecrit dans
   la plage de l'app sans faire avancer le compteur -> le decalage reviendra.

2  LE POUSSEUR PRENAIT LES VERROUS POUR DU TRAVAIL.  (voir le plan)
```

### Ce qui reste testable TOUT DE SUITE, sans attendre C.4

**Le bloc DESCENTE (etapes 5-6-7) sur le bien 62774.** Ses transactions sont deja
rapprochees, avec leurs numeros Hektor : il n'a pas besoin du retour qui manque. C'est la
que se trouve la seule question encore ouverte -- *Hektor redescend-il le statut ?* -- et
elle ne depend d'aucun chantier en cours.

### L'etat du bien EM28412, a la reprise

```
   statut « Sous offre » (app et Hektor)   ·   diffusable 0
   ledger : 1 001 324, offre « en_cours », ORPHELINE (pas de numero Hektor)
   le run de nuit devrait l'adopter -- regle (annonce, type, acquereur) du 25/08,
   jamais eprouvee en vrai. A VERIFIER AU PROCHAIN RUN : c'est un test gratuit.
```

---

## 4ter. LA SEQUENCE DE FREDERIC — celle qu'on suit desormais

**Elle remplace les etapes 2 a 10 de la section 4.** Elle est meilleure : au lieu de
monter puis descendre en bloc, elle eprouve CHAQUE interaction dans les DEUX SENS, et
revient a zero entre chaque cycle. C'est ainsi qu'on saura ce qui produit quoi.

> *« il faut aussi verifier offre annulee avant de faire compromis pour verifier
> l'interaction du state chez Hektor et s'il repasse sur state actif »*

```
CYCLE 1 -- L'OFFRE SEULE, ET SA MORT
  1.1  REFUSER l'offre 33037 (deja en place)
       ? le statut redescend-il de « Sous offre » a « ACTIF » ?
       C'EST LA QUESTION CENTRALE DU PROTOCOLE. Le 01/09 sur 62774, Hektor n'avait
       PAS redescendu -- mais ce bien avait recu 25 changements de statut a la main.
       Ici le bien est propre : la reponse vaudra.

CYCLE 2 -- L'OFFRE ACCEPTEE
  2.1  CREER une nouvelle offre        ? statut -> Sous offre
  2.2  ACCEPTER cette offre            ? le statut BOUGE-T-IL ? (attendu : non)

CYCLE 3 -- LE COMPROMIS, ET SON ANNULATION
  3.1  CREER un compromis              ? statut -> Sous compromis
  3.2  ANNULER le compromis            ? le statut redescend-il, et A QUOI ?
                                         « Sous offre » (l'offre acceptee vit encore)
                                         ou « Actif » ?
                                       ? ET L'OFFRE LIEE PASSE-T-ELLE EN REFUSEE
                                         TOUTE SEULE ?
       ⚠ DEJA MESURE SUR LE PARC, a confirmer en direct : NON. Sur 1 194 paires
         (compromis annule + offre du meme acquereur), 60 % des offres restent
         ACCEPTEES. Si c'etait automatique, ce serait 100 %.

CYCLE 4 -- LA CHAINE COMPLETE
  4.1  CREER une offre                 ? statut -> Sous offre
  4.2  ACCEPTER
  4.3  CREER un compromis              ? statut -> Sous compromis
  4.4  CREER une vente                 ? statut -> VENDU
                                       ? et le compromis, que devient-il ?
```

**A CHAQUE GESTE, LES TROIS TEMPS** (T0 / T1 / T2) et les quatre releves de la
section 3 -- dont l'etat de CHAQUE transaction, pas seulement celle qu'on touche.

### La reponse a la question posee le 01/09

> *« si Hektor lors du run nous remonte une transaction par le miroir, est-ce que
> cette transaction sera aussi enregistree dans le registre et memorisee par l'app
> puis le serveur comme une saisie dans l'app ? »*

**NON, et c'est voulu.** Verifie : `affaire_ledger.py` ne mentionne jamais
`app_affaire_champ_app` (0 occurrence), et les seules origines presentes au carnet
sont `creation_app` et `essai_nuit_c19` -- aucune ne vient du run.

Une affaire remontee par le miroir entre au registre avec TOUT ce qui l'identifie :
son `app_affaire_id`, son acquereur par notre numero, ses cinq colonnes, son
`payload_json` brut. **Mais sans carnet.**

**Pourquoi c'est juste :** le carnet repond a « qu'est-ce que l'APP detient ? ». Sur
une affaire saisie chez Hektor, l'app ne detient rien -- il n'y a pas eu de saisie.
Y inscrire les valeurs de Hektor ferait croire l'inverse, et le contrat d'autorite
les ferait alors GAGNER contre Hektor au prochain run. On rendrait faux ce qui est
vrai.

**La consequence reelle, en revanche :** pour une affaire nee chez eux, l'app ne
connaitra que les cinq colonnes plus le payload brut -- et rien de tout cela n'est
lu par l'ecran aujourd'hui.

⚠ **CORRECTION DE CE QUE J'AI D'ABORD ECRIT ICI.** J'avais dit que la validite et
le taux « n'y seront pas, parce que l'API de Hektor ne les renvoie pas ». **C'est
faux pour la validite** : elle dort dans `propositions[0].validite` pour **11 068
offres sur 11 121**, et le delai de retractation dans `compromis.dateEnd` pour les
10 577 compromis. Mesure exacte :

```
   genre        lignes    validite      honoraires   notaire    taux
   offre        11 121    11 068 ✓      11 121 ✓        0        0
   compromis    10 577    10 577 ✓      10 577 ✓        0        0
   vente         7 606       --         7 606  ✓     7 606 ✓     0
```

Seuls manquent vraiment le NOTAIRE (absent des offres et compromis) et le TAUX
(absent partout -- celui-la, Hektor ne le renvoie jamais).

➡ La correction a venir est donc un chantier de **LECTURE**, pas de collecte :
composer les trois sources dans l'ordre -- le carnet (ce que l'app detient, qui
prime), les colonnes, puis le payload (le fond de tiroir). Voir la partie C du
chantier « registre des affaires » au plan. **A faire APRES ce test**, qui peut
encore changer ce qu'on croit savoir.

---

## 5. La fiche de relevé

Une ligne par temps, à remplir au fur et à mesure.

| # | temps | statut Hektor | offre(s) | compromis | vente | diffusable | job / envoi |
|---|---|---|---|---|---|---|---|
| 0 | T0 | | | | | | |
| 1 | T0 | | | | | | |
| 1 | T1 | | | | | | |
| 1 | T2 | | | | | | |
| 2 | T0 | | | | | | |
| 2 | T1 | | | | | | |
| 2 | T2 | | | | | | |
| 3 | T0 | | | | | | |
| 3 | T1 | | | | | | |
| 3 | T2 | | | | | | |
| 4 | T0 | | | | | | |
| 4 | T1 | | | | | | |
| 4 | T2 | | | | | | |
| 5 | T0 | | | | | | |
| 5 | T1 | | | | | | |
| 5 | T2 | | | | | | |
| 6 | T0 | | | | | | |
| 6 | T1 | | | | | | |
| 6 | T2 | | | | | | |
| 7 | T0 | | | | | | |
| 7 | T1 | | | | | | |
| 7 | T2 | | | | | | |
| 8 | T0 | | | | | | |
| 8 | T1 | | | | | | |
| 8 | T2 | | | | | | |
| 9 | T0 | | | | | | |
| 9 | T1 | | | | | | |
| 9 | T2 | | | | | | |
| 10 | T0 | | | | | | |
| 10 | T1 | | | | | | |
| 10 | T2 | | | | | | |

---

## 6. Les règles de conduite pendant le test

```
[ ]  UN GESTE, UN RELEVE COMPLET, ON NOTE, ON PASSE AU SUIVANT
     meme quand le resultat parait evident -- c'est en sautant cette etape qu'on
     conclut d'un cas unique.

[ ]  NE PAS ENCHAINER VITE
     refresh_console_data met ~45 s. Cliquer avant, c'est melanger deux gestes et
     perdre le releve.

[ ]  DISCIPLINE DE DEBIT MAINTENUE
     1 requete API par releve, ~35 requetes en tout. Sans commune mesure avec les
     rattrapages qui ont fait bannir l'IP. Aucun changement aux reglages.

[ ]  SI UN GESTE ECHOUE, ON S'ARRETE ET ON REGARDE
     un job en erreur est un resultat, pas un incident a contourner.

[ ]  RIEN N'EST CODE PENDANT LE TEST
     on releve, on conclut, on decide ensuite.
```

---

## 7. Ce que ce test produit

```
   la table de verite « geste -> reaction d'Hektor », qui manque au projet
   la validation de bout en bout : app -> worker -> Hektor -> resynchro
   la decision sur C+, fondee au lieu d'etre supposee
   la reponse sur deleteOffre / deleteCompromis : faut-il les coder ?
   et, si Hektor ne recalcule rien : la confirmation que la regle deja ecrite
   n'est pas un filet pour l'apres-coupure, mais un correctif pour aujourd'hui
```

Voir `ETUDE_STATUT_ANNONCE_TRANSACTIONS_MANDAT_2026-09-01.md` *(l'étude qui a mené ici)*,
`ACTIONS_TRANSACTION_HEKTOR_2026-08-28.md` *(le relevé DOM des verbes)*,
`LISTE_TACHES_A_COCHER_2026-08-29.md` *(C.19)*.
