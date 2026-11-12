# LE CHANTIER CLASSEUR — où on en est, le but, le plan, les tâches

---

# 0. ⭐⭐ LE PLAN D'ACTION ACTIF — **réécrit le 12/11/2026, tout est mesuré**

> ⛔ **CETTE SECTION EST LE PLAN D'ACTION EN COURS.** Le reste du document garde
> **le but** (§ 2), **les tâches d'origine** (§ 4) et **les interdits** (§ 6) : ils ne
> changent pas. On ne duplique pas ce fichier, on met CETTE section à jour.
>
> ⚠ **Ce qui a dû être corrigé pour arriver à cette version, à ne pas refaire :**
> j'ai donné « le plan » quatre fois en lisant mes propres audits (A15, A17, A18) au
> lieu d'ouvrir ce fichier. Deux conséquences : j'ai proposé **de créer une table
> `app_affaire_suivi` et des colonnes**, ce que le § 6 interdit, et j'ai annoncé « puis
> le classeur ferme », alors que le § 2 dit l'inverse — **il change d'écrivain**.

## Le but, en deux lignes *(§ 2, inchangé)*

```
① le classeur FAIT FOI  -> on met notre data en conformite avec lui
                           il REMPLIT les vides ET CORRIGE les divergences
② puis LA BASCULE       -> on saisit dans l'app, plus dans le classeur
                           ⚠ le classeur NE FERME PAS : il change d'ecrivain
```

## ⭐ La correspondance : comment une ligne du Sheet trouve son dossier

```
id_unique du Sheet
      |  LE GEL  (app_classeur_lien, 29/10 -- 12 422 liens)
numero de transaction        <- il ne change JAMAIS
      |  le chainage, chaque nuit
le dossier
      |  l'etiquette
D2026-0431  +  un UUID
```

⭐ **Le gel s'accroche à la TRANSACTION, pas à la chaîne** — règle du 28/10 : *« un
numéro de chaîne ne doit jamais servir de point d'accrochage, il bouge »*. C'est pour
ça que le chaînage a pu être refait sans casser un seul lien.

⭐⭐ **ET LE GEL EST UN ÉCHAFAUDAGE, PAS LE MUR.** Il sert **une seule fois de plus** :
à écrire notre UUID dans la colonne `affair_uuid` du Sheet (étape 5). Après ça, chaque
ligne porte elle-même l'identifiant de notre dossier, la correspondance est écrite des
deux côtés, et **le gel devient une archive**.

**Mesure du 12/11, avec le chaînage corrigé :**

```
lignes du Sheet qui tombent dans UN SEUL dossier   4 655   (99,3 %)
lignes a cheval sur DEUX dossiers                     33
dossiers portant UNE SEULE ligne du Sheet          4 715
dossiers portant DEUX lignes                           3
```

➡ **Aucune règle nouvelle à inventer.** Restent 36 cas à trancher à la main — et la
décision du 04/09 interdit de les régler par une règle.

## ⚠⚠ LE DÉFAUT TROUVÉ LE 12/11 — **la date d'une offre refusée**

```
offres portant la date du 11/11/2026              1 185   = nos refus de la veille
   heures : 07:52:36 -> 19:37:07
```

**Pour une OFFRE, Hektor met dans `date` son DERNIER mouvement, pas la proposition.**
Nos 1 185 refus ont donc déplacé la date de 1 185 offres au 11/11/2026. Relevé sur
l'offre 14112 : proposition le 25/03/2021, acceptation le 25/03/2021, refus le
11/11/2026 — et `date` porte le refus.

⭐ **Rien n'est perdu** : la vraie date vit dans `propositions_json`.
⭐ **Le chaînage n'est pas touché** : il ordonne une offre sur sa première proposition.
⛔ **ON NE CORRIGE PAS LA COLONNE** — classe C, le run la relit chaque nuit (ce serait
le gel du 03/09) ; et la corriger chez Hektor demanderait de réenregistrer les offres,
c'est-à-dire de redéplacer la date. **On corrige les LECTEURS.**

```
l'apparieur                        ✅ REPARE le 12/11 -- reparation « propositions »
le chainage                        ✅ deja bon
l'historique de l'offre a l'ecran  ✅ bon (il lit propositions_json)
rapport_gel_tous_les_champs.py     ⬜ MEME DEFAUT, l. 572 ("Offre Achat","offre","date")
la date affichee sur la ligne      ⚠ non verifie
« derniere date » de l'avancement  ⚠ une offre refusee hier parait RECENTE
```

⚠ **Et le phénomène n'est pas né hier** : 263 offres l'avaient déjà. En revanche
**1 061 offres refusées ont leur date intacte** — il y a donc une différence entre un
refus fait à la main chez Hektor et le nôtre. **NON MESURÉ, c'est une hypothèse.**

## 📋 LES ÉTAPES

### ÉTAPE 1 — fermer l'appariement *(P1)*

```
1.1 ✅ FAIT 12/11   l'apparieur repare : 4 691 / 4 786 reconnues (98,0 %)
                    sure 4 569 . bonne 11 . a valider 111 . aucune 95
                    temoins : 0 ligne perdue . 17 des 20 regressions revenues
                    ⭐ et 3 des 5 cibles changees S'ALIGNENT SUR LE GEL
1.2 ⬜              reparer rapport_gel_tous_les_champs.py (meme defaut)
1.3 ⬜              regarder 2dfa6ef3 (seule divergence avec le gel) et les
                    3 lignes restantes : 8Q3LHGZ4 . I847SPN3 . UTLG66LE
1.4 ⬜ FREDERIC     trancher les 2 « a valider » : 6a259cce . ME6S0TR9
1.5 ⬜ ACCORD       le RE-GEL ADDITIF des gains -- 3 lignes neuves sures
                    (4790/4791/4792) + Z3DYDC4X, + les 2 ci-dessus s'il dit oui
                    ⛔ ADDITIF : on ne retouche aucun des 12 422 liens
1.6 ⬜              git : apparier_classeur.py n'est PAS suivi, ni les notes
```

### ÉTAPE 2 — l'étiquette de dossier *(B2/B3 du plan du 29/10)*

```
2.1 ⬜              ecrire la REPETITION qui manque au patch
2.2 ⬜              la pose A BLANC -> le compte attendu est 12 174
2.3 ⬜ ACCORD       coller patch_etiquette_dossier_2026-11-09.sql, INVERSE sous la main
2.4 ⬜ ACCORD       B3 le remplissage + la sentinelle de la nuit suivante
⭐ le format est deja valide (« Oui » aux deux, 09/11) : D2026-0431 + un UUID
⭐ le code local est PRET : les 2 colonnes sont deja dans
  COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (affaire_ledger.py l. 2561)
```

### ÉTAPE 3 — le rapatriement *(P1.4)*

```
3.1 ⬜              refaire le rapport des ecarts avec l'apparieur repare
3.2 ⬜              fermer les 2 reserves : 413 ecarts contre 211 du rapport (lot 3)
                    et charge_commission, 23 480 valeurs
3.3 ⬜ ACCORD       les 7 colonnes qui ONT une case : P S T W AB AD (+ AF comparer)
3.4 ⬜ ACCORD       Y le reglement et AA la facture -> app_affaire_champ_app,
                    sur la transaction de role 'vente'
                    ⚠ MESURER D'ABORD les 1 062 lignes sans role 'vente'
3.5 ⬜ FREDERIC     le carnet des 5 colonnes de dossier (F G AH AI AJ), cle id_unique
                    + la case du numero de mandat (C, « les vides », ~9 utiles)
```

⛔⛔ **CE QU'IL NE FAUT PAS FAIRE, ET J'ALLAIS LE FAIRE** : créer la table
`app_affaire_suivi`. Mon propre audit du 09/11 l'avait déjà déclarée **inutile**
(*« ne pas l'appliquer »*), et `app_registre_champ_app` **ne convient pas** — mesuré le
12/11 : son `CHECK` n'accepte que `societe / agence / personne`, son `objet_id` est un
`bigint`, et son seul lecteur est `registreUtilisateurs.ts`. **C'est la table du
registre des agences, le chantier de l'autre session.**

### ÉTAPE 4 — la porte et les vagues *(P2/P3)*

```
4.1 ⬜ ACCORD       P2 la porte sans ecran : une RPC qui APPELLE
                    app_modifier_affaire_optimistic, jamais une copie
4.2 ⬜ ACCORD       P3a une affaire qu'il choisit
4.3 ⬜ ACCORD       P3b la reprise complete, LA NUIT (~2 a 3 h, arret sur conflit)
```

### ÉTAPE 5 — la bascule *(V1/P4)*

```
5.1 ⬜ FREDERIC     V1 lire les Apps Script du classeur (10 min) -- BLOQUE P4
5.2 ⬜ ACCORD       ecrire nos UUID dans la colonne affair_uuid du Sheet
                    ⭐ LE GEL SERT ICI, UNE FOIS -- puis il dort
5.3 ⬜ ACCORD       P4 le routeur : l'app ecrit dans le classeur, par l'uuid
```

### EN PARALLÈLE, indépendant du chantier

```
R-A ⬜              le frein Hektor PARTAGE (par processus : 4 workers = 4 req/s)
                    ⚠ il a mordu les 27-28/10
R-B ⬜              le balayage qui relance une commande morte depuis le carnet
```

---

**28/10/2026.** Écrit à la demande de Frédéric, **sans aucune mesure** : le run quotidien
tourne *(relancé après un échec, fin vers 9 h 30)* et ni `phase2.sqlite` ni Supabase ne
doivent être sollicités.

> ⚠ **Tous les chiffres de ce document ont été mesurés le 26/10 et doivent être rejoués.**
> Le parc bouge tous les jours.

---

# 1. OÙ ON EN EST

## Le projet, en deux étapes *(définies par Frédéric le 08/10)*

```
ETAPE 2   l'app fait tout le travail quotidien ; Hektor vit, il FOURNIT LES NUMEROS,
          les workers lui ENVOIENT les mises a jour              <- ON EST ICI
ETAPE 3   notre registre electronique des mandats -> la signature -> la pub,
          plus le site, le DNS, l'e-mail
```

## Les deux chantiers qui tournent en parallèle

```
⑧ GARDE CHEZ NOUS      une AUTRE conversation          🔧 EN COURS
   tous les champs saisis chez nous des le clic, et le controle au retour
   pieces 1-4 + R3 en production (25/10) · restent la piece 5, R2, R4, R5

LE CLASSEUR            cette conversation              ⏸ EN PAUSE, par sa decision
   relier le classeur Google au registre, puis inverser le sens des ecritures
```

## ⭐ Ce que ⑧ nous a déjà débloqué

Le 23/10 je disais : *« la reprise du classeur a besoin de R3, et R3 n'est pas posé —
sinon on tire 200 corrections dans le noir. »*

```
MESURE DU 26/10        le carnet      10 -> 56 lignes
                       avec VERDICT    5 -> 33
                       dont « arrivee », origine creation_app, 11 lignes avec la
                       valeur relue chez Hektor
```

✅ **R3 rend des verdicts. Le verrou est levé.**

## ⚠ Et ce que ⑧ n'a PAS changé

```
ancienne methode / donnees du 23/10   94,9 %
ancienne methode / donnees du 26/10   94,9 %    <- a methode constante, RIEN n'a bouge
nouvelle methode / donnees du 26/10   96,8 %    <- le gain vient de LA METHODE
```

C'est normal : **l'appariement dépend du classeur et des mandats**, que ⑧ ne touche pas.

---

# 2. LE BUT DU CHANTIER — ⚠ RÉÉCRIT LE 28/10, DANS LES MOTS DE FRÉDÉRIC

> *« Le classeur Sheet est notre **data officielle de vente** depuis quelques années, et
> actuellement. Le but est donc de **mettre à jour ma data pour correspondre à mon Sheet**.
> Puis **pouvoir ajouter et modifier les lignes à partir de l'app**. »*

```
① LE CLASSEUR FAIT FOI
     c'est la data OFFICIELLE des ventes depuis des annees, et encore aujourd'hui
     -> on met NOTRE data en conformite avec LUI

② ENSUITE on ajoute et on modifie les lignes DEPUIS L'APP
     et on ne saisit plus dans le classeur
```

⛔ **Ma formulation précédente — « trois sources, personne ne détient l'affaire entière » —
était une DESCRIPTION, pas un but.** Le but, c'est **la conformité, puis la bascule**.

## ⛔⛔ CE QUE ÇA CORRIGE DANS CE PLAN

J'avais écrit *« P1.4 : le patch d'alignement, **famille ① seulement** — là où le classeur
remplit un VIDE chez nous. RIEN D'AUTRE, les conflits se LISTENT. »*

**C'est contraire à sa demande du 22/10 :**

> *« les données **manquantes ET AUSSI DIVERGENTES** — c'est le classeur qui a raison si on
> est sûr de la correspondance »*

⛔ **J'avais rétréci son périmètre sans le dire.** Corrigé : **le patch corrige aussi les
divergences**, le classeur faisant foi.

```
AVANT (faux)   le classeur remplit un VIDE          -> les conflits se LISTENT
APRES (juste)  le classeur FAIT FOI                 -> il remplit ET il corrige
```

## Les deux seules réserves, et elles ne portent pas sur « qui a raison »

```
① ON NE CORRIGE QUE CE QU'ON A SUREMENT APPARIE
   ce n'est pas un doute sur le classeur : c'est que poser la BONNE valeur sur la
   MAUVAISE affaire est pire que ne rien faire (43 lignes se telescopaient --
   le cas GENILLON).  -> c'est tout l'objet de P1.

② CERTAINS CHAMPS NE PEUVENT PAS SE CORRIGER MECANIQUEMENT
   « Vente reglee » du classeur est une date de REGLEMENT, pas notre date d'acte
   (+3 jours de mediane, mesure du 19/10). Elle ne remplace donc pas la notre :
   ELLE A SA PROPRE PLACE.  Ce n'est pas « le classeur a tort », c'est
   « ce n'est pas le meme champ ».
```

## Ce qu'on produira

```
AVANT   le negociateur saisit dans l'app PUIS quelqu'un retape dans le classeur
APRES   il saisit UNE FOIS, dans l'app
          -> l'app envoie a HEKTOR ce qui le concerne
          -> l'app ecrit dans le CLASSEUR ce qui concerne la vente et la paie
          -> plus personne ne tape dans le classeur
```

⚠ **Le classeur ne disparaît pas** — il reste la référence officielle, et la paie s'en sert.
**Il change d'écrivain.**

⭐ **Le gain** : la data officielle sera enfin **dans l'app aussi** — donc retrouvable,
contrôlable, explicable. Une commission tapée dans une case Google n'a ni auteur, ni date,
ni trace.

---

# 3. LE PLAN, EN DEUX PHASES *(décidé par Frédéric le 22/10)*

```
PHASE A   UNE SEULE FOIS       le Sheet  ──>  le serveur + l'app
                               on rattrape TOUT ce qui est possible

PHASE B   ENSUITE, DEFINITIF   l'app  ──>  le Sheet
                               plus personne ne saisit dans le classeur
```

⭐ **Ce n'est PAS une synchronisation permanente à double sens.** Cette précision a retiré
**deux mécanismes délicats** du chemin critique : l'arbitre *(« qui gagne ? »)* et le journal
Apps Script.

## Et le mécanisme : la correction du classeur est **un geste de l'app comme un autre**

```
1  LE CARNET      on note : « affaire X, champ Y, valeur Z, origine = classeur »
2  LA COMMANDE    un travail est pose -- LES DEUX DANS LA MEME TRANSACTION
3  LE FACTEUR     le worker porte chez Hektor ce qui a une case chez lui
4  IL RELIT       et ecrit chez nous CE QUE HEKTOR A RETENU, jamais notre intention
5  LE VERDICT     arrivee / en_attente / conflit
6  CE QUI RESTE   commission · charge · notaire · facture · reglement
                  -> restent au carnet, c'est LEUR place : Hektor n'a pas de case
```

⭐ **Rien de neuf à inventer** : cette route existe, elle s'appelle **la classe B**, et elle
est en production.

---

# 4. 📋 LA LISTE DES TÂCHES

## T0 — DEUX GESTES RAPIDES, ET ILS SONT À TOI

| | tâche | taille |
|---|---|---|
| **T0.1** | mettre `scheduled/push_suivi_appsheet.py` **sous git** — il porte mon correctif du 22/10 et n'a **aucune histoire** | 2 min |
| **T0.2** | commiter les documents de `notice/` produits depuis le 22/10 | 2 min |

## P1 — RELIER ⏱ 3 j · **le préalable à tout**

| | marche | taille | risque |
|---|---|---|---|
| **P1.1** | la cascade **en lecture seule** — `phase2/checks/apparier_classeur.py` | 1 j | ✅ aucun |
| **P1.2** | geler le lien — table `app_classeur_lien` | 0,5 j | ⛔ ton accord |
| **P1.3** | le rapport des écarts, champ par champ | 0,5 j | ✅ lecture seule |
| **P1.4** | le patch de **mise en conformité** — le classeur **remplit** les vides **ET corrige** les divergences *(il fait foi)*. ⚠ Famille par famille, avec la liste sous les yeux avant d'écrire | 1 j | ⛔ ton accord |

**La règle appliquée** *(mise au point ensemble les 20 et 23/10)* :

```
0.  le mandat est-il un MANDAT DE RECHERCHE ? -> pas de bien, c'est NORMAL
1.  LE MANDAT                                     65 %
2.  + LA DATE                                     92 %    <- ton idee du 23/10
3.  + LA DATE LA PLUS PROCHE                      94 %
4.  + LE VENDEUR                                  95 %
5.  + LA VILLE                                    96 %
6.  + LE RATTRAPAGE par l'acquereur + le montant  96,8 %
    sinon -> ABSTENTION, et elle est NOMMEE
```

⚠ **Ces 96,8 % répondent à « quel BIEN ».** Il manque **« quelle AFFAIRE dans ce bien »**
— l'étage 2. **Ce taux-là, personne ne le connaît.** C'est P1 qui le dira.

**Les 4 contrôles, et le dernier est le plus important :**

```
le TEMOIN INVERSE    l'ancienne cascade doit rendre EXACTEMENT 4 527 (26/10, a rejouer)
l'EXCLUSIVITE        0 affaire ne recoit deux lignes
le cas GENILLON      bien 15220 : L40 -> 7500 et L3405 -> 7499, chacune la sienne
⛔ AUCUNE REGRESSION  toute ligne appariee par l'ANCIENNE et PERDUE par la nouvelle
                     est NOMMEE, une par une
```

## P2 à P4 — LA REPRISE, PUIS LE SENS INVERSE

| | tâche | taille | dépend de |
|---|---|---|---|
| **P2** | **la porte sans écran** — une RPC qui *appelle* `app_modifier_affaire_optimistic`, jamais une copie | 1 j | ⛔ ton accord |
| **P3a** | **la première vague : UNE affaire que tu choisis** — *Hektor accepte-t-il de corriger une affaire close ?* | 0,5 j | ✅ R3 est posé |
| **P3b** | **la reprise complète** — par vagues, **la nuit**, avec arrêt automatique sur conflit | 1 j | P3a concluant |
| **P4** | **le routeur + la destination classeur** | 2 j | ⛔ **V1** |

⚠ **Le débit de P3b** : ~200 corrections × 30-50 s = **2 à 3 heures**. ⛔ **La nuit
uniquement** — en journée, ça bloquerait les gestes de tes collaborateurs, même file.

## V — LES DEUX VERROUS, ET ILS SONT À TOI

```
V1  LIRE LES APPS SCRIPT DU CLASSEUR            10 min   ⛔ BLOQUE P4
      Sheet1 nourrit LA PAIE. Les onglets CA Mensuel, Reporting, 12 mois lissants
      et Agence n'ont AUCUNE formule -- un script les remplit, jamais ouvert.
V2  COLLER app_sheet_ecrit (le patch du 16/10)  15 min
      sans lui, on relit nos propres ecritures comme des saisies humaines
```

## R — LES RISQUES ACTIFS, INDÉPENDANTS DU CHANTIER

| | tâche | taille | urgence |
|---|---|---|---|
| **R-A** | **le frein Hektor PARTAGÉ** — il est par processus : 4 workers = 4 req/s, au-dessus du seuil qui a banni | 0,5 j | ⚠⚠ **et il a encore mordu les 27-28/10** |
| **R-B** | **le balayage qui relance une commande morte** depuis le carnet | 0,5 j | ⚠ sinon la reprise n'a aucun filet |
| **R-C** | **le geste écrit chez nous d'abord** — le mur est vers **16 utilisateurs**, pas 30 | ? | le gros morceau |

## F — LES FILS OUVERTS, À REGARDER QUAND TU VOUDRAS

```
11 VENTES portent le nom du MAUVAIS acquereur (celui du compromis ANNULE)       1 j
   biens 9340 · 11786 · 15220 · 17534 · 17536 · 23238 · 36344 · 41672 · 46585
         48311 · 54867

1 BIEN VIVANT affiche une offre morte : 62106 Bessamorel                        30 s
   -> un refus d'offre DANS Hektor suffit, aucun code

LES 56 ABSTENTIONS ont un air de famille : mandats ~4000-4300, TOUS en 2021,
   deux biens aux periodes QUI SE CHEVAUCHENT -- un lot reattribue en bloc ?

LES ~78 MANDATS INTROUVABLES, dont 17 hors de nos plages (27 000 a 91 000)
   -> une autre numerotation. PROTEXA ? un autre logiciel ? NON MESURE.
```

---

# 5. L'ORDRE, ET CE QUI DÉPEND DE QUOI

```
T0      git                        2 min   TOI
P1      RELIER                     3 j     ✅ ne depend de RIEN
P2      la porte                   1 j
P3a     une affaire                0,5 j   ✅ R3 est pose, le verrou est leve
P3b     la reprise, la nuit        1 j
──      LA BASCULE : la saisie passe par l'app  ──
V1      tu lis les Apps Script     10 min  ⛔ BLOQUE P4
P4      le routeur + le classeur   2 j

R-A     le frein Hektor partage    0,5 j   ⚠ EN PARALLELE, et c'est urgent
```

**Taille du chantier, hors R-C : ~8 jours.**

---

# 6. ⛔ CE QUI NE SE FAIT PAS

```
- ecrire dans le classeur avant que V1 soit fait
- rallumer CHAMPS_APP_AFFAIRE : vide EXPRES depuis le 16/09 (« le gel »)
- creer des colonnes au registre pour les champs financiers -> ils vont AU CARNET
- corriger l'acquereur : « changer qui achete n'est pas une correction,
  c'est une AUTRE affaire. Elle se cree, elle ne se rectifie pas. »
- deviner : une ligne non appariee reste SANS LIEN, et NOMMEE
- lancer P1 pendant le run de nuit ou la descente
```
