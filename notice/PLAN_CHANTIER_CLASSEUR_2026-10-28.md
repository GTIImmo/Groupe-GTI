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
rapport_gel_tous_les_champs.py     ✅ REPARE le 12/11 -- 536 faux ecarts evites
la date affichee sur la ligne      ✅ REPARE le 12/11 (commit 541f1be)
« derniere date » de l'avancement  ✅ REPARE le 12/11 -- meme commit
```

⭐⭐ **LES QUATRE LECTEURS SONT ALIGNES depuis le 12/11** — commit `541f1be`, non pousse
a l'heure ou ceci est ecrit :

```
le chainage de nuit   _date_de_tri              affaire_ledger.py l. 1517 . deja juste
l'apparieur           dates_des_propositions    apparier_classeur.py . 12/11
le rapport du gel     premiere_proposition      rapport_gel_*.py . 12/11
l'ECRAN               dateOffreFaite            api.ts . 12/11
MESURE : 1 435 offres retrouvent leur vraie date, dans 1 430 dossiers
         dont 1 180 par nos refus . 255 l'avaient DEJA avant nous
         la plus ancienne retrouvee : 18/09/2006
```

⭐ **UNE SEULE DEFINITION** : `dateOffreFaite` existait dans `App.tsx` depuis le
**05/11** mais ne servait qu'a la REGULARISATION d'une offre oubliee. Elle a demenage
dans `api.ts`, a cote du type et des requetes. *(Lecon n° 15 : chercher si le projet a
deja tranche -- j'allais ecrire une fonction qui existait.)*

⛔ **ET LA COLONNE NE SE CORRIGE PAS, c'est prouve par le code** : le run la relit chez
Hektor a chaque nuit (`R2_CHAMP_VERS_COLONNE`, `affaire_ledger.py` l. 1661) et la
protection est **nommement refusee** pour ce couple (`R2_JUGES_SUR_LE_REGISTRE`, l. 1671),
parce que R3 doit pouvoir comparer notre valeur a celle de Hektor.

⚠ **Et le phénomène n'est pas né hier** : 263 offres l'avaient déjà. En revanche
**1 061 offres refusées ont leur date intacte** — il y a donc une différence entre un
refus fait à la main chez Hektor et le nôtre. **NON MESURÉ, c'est une hypothèse.**

## 📋 LES ÉTAPES

## ⭐⭐⭐ LE PLAN DETAILLE DU 15/11 — **LA LISTE QUI FAIT FOI**

> Ecrit a la demande de Frederic : *« redonne le plan detaille en faisant attention
> de rien oublier pour le memoriser »*. **Il remplace mes listes des jours
> precedents**, qui ont oublie quatre taches deja ecrites ailleurs (V, Z, les
> emplacements, la fenetre du Sheet) et portaient une reserve PERIMEE (les
> negociateurs, deja faits — c'est lui qui a eu le doute, et il avait raison).
> ⛔ **LA REGLE, posee par A15 le 09/11 et que je n'avais pas suivie** : avant de
> mesurer une colonne, lire DANS CET ORDRE les decisions du 02/11, A5, A6 § 3,
> A4bis, puis ce plan. **Et ne jamais ouvrir un second registre de decisions.**

### ⭐ LES FAITS ETABLIS, A NE PLUS REPERDRE

```
LA PLAGE APP            app_affaire_id >= 1 000 000, sequence app_affaire_id_app_seq.
                        « une affaire saisie dans l'app existe avant que Hektor ne la
                        numerote, ET PARFOIS SANS QU'IL LA NUMEROTE JAMAIS » (20/08).
                        340 lignes y vivent -- mais TOUTES avec un numero Hektor.
LA CLASSE A             une colonne que LE PUSH N'ENVOIE JAMAIS (liste dans
                        affaire_ledger.py, ~l. 2876-2900). Temoins vivants :
                        jours_validite 358 . taux_honoraires 5.
⛔ LE CARNET DES         app_affaire_champ_app N'EST PAS UN MAGASIN : c'est une FILE
   AFFAIRES             D'ENVOI vers Hektor -- « une saisie cherche a le rejoindre et
                        DISPARAIT une fois arrivee ». NE PAS s'en servir pour garder.
⭐⭐ TROIS CASES         F  -> app_affaire_condition (+ app_condition_catalogue)
   EXISTENT DEJA        G  -> app_affaire_note
                        Z  -> date_annulation_app + motif_annulation_app (10/11, VIDES)
                        ✅ AUCUNE des trois ne descend ni ne remonte : la nuit ne les
                          connait pas. Seuls l'app et les patchs y ecrivent.
                        ⭐ Et HEKTOR NE REND AUCUNE CONDITION SUSPENSIVE : 0 sur 18 589
                          lignes de app_affaire_console -> aucun conflit possible.
⛔ 3 TRANSACTIONS       1001388, 1001391, 1001394 ont DISPARU des deux bases, sans
   DISPARUES            sauvegarde, sans journal, sans trace de qui. Leurs 5 conditions
                        et 6 notes sont restees ORPHELINES.
L ETAT DES ECARTS       8 494 au total sur 4 702 lignes rattachees, dont ~5 480 decides
                        « RIEN » (Nature 1 650, Ville 1 646, Notaire 1 373, Agence 493,
                        Acquereur 113, Vendeur 64, Etat 71, product_ref 70).
LES TRANSACTIONS        le Sheet 12 634 dates . nous 12 393 . IL MANQUE 241
   MANQUANTES           144 offres . 62 compromis . 35 ventes      (98,1 % deja chez nous)
                        + 10 transactions presentes SANS leur date (4 offres, 6 compromis)
```

### PHASE A — MESURER. **Rien d'ecrit en base.**

```
A0 ⬜  RELANCER LE RAPPORT DU GEL -- une commande, et c'est le PREMIER geste.
       Il remet a jour TOUS les chiffres. ⚠ Pourcentage 1 affiche encore 48 ecarts
       et Negociateur 1 dix-huit, alors que le lot 1 a ete pose les 13-14/11 : le
       rapport du 14/11 a pu etre produit AVANT la pose. Tant qu'il n'est pas
       relance, LE LOT 1 N'EST PAS CLOS A 100 %.
A1 ⬜  LIRE LE SHEET sur les 8 colonnes que le rapport NE COUVRE PAS :
       F G Y AA Z AH AI AJ. Le rapport ne porte que 21 colonnes sur 38 -> pour ces
       huit, je n'ai AUCUN ecart mesure, seulement les comptages du 02/11.
A2 ⬜  L'ESSAI D'UNE NUIT (= 3.3zero). Une transaction dans la plage app, SANS
       numero Hektor, sur un bien NON VIVANT. Mesure au matin **sur LES DEUX
       bases** (Supabase ET phase2.sqlite). ⛔ OBLIGATOIRE : aucune ligne de la
       plage n'a jamais vecu sans numero Hektor, et 3 ont disparu sans trace.
A3 ⬜  LA FENETRE DU SHEET : l'apparieur ne lit que `A1:AL6000`. Le classeur en
       portait 4 783 -> ~1 200 lignes de marge, puis PERTE SILENCIEUSE du bas.
       Idem pour toute colonne a droite de AL. Ecrit le 31/10, jamais corrige.
A4 ⬜  L'EFFET DE BORD D'UNE VENTE CREEE : chez nous c'est la vente qui fait
       passer un dossier a l'etat VENDU. Mesurer ce que deplacent 35 ventes neuves
       (etat affiche, pilotage, statistiques, chainage) AVANT de les poser.
       ⭐ Les offres et compromis n'ont pas ce risque.
A5 ⬜  LES 1 062 LIGNES SANS ROLE 'vente' -- prealable de 3.4 : ou va la valeur
       de Y / AA quand la transaction qui devrait la porter n'existe pas ?
A6 ⬜  LES 85 LIGNES NON RATTACHEES : notre base n'en garde que l'identifiant.
       Contenu inconnu -> jusqu'a ~250 transactions de plus, hors de tous mes
       chiffres. (= le prealable n0 4 du 29/10, et le point 4 de A15.)
```

### ✅ A0 FAIT LE 15/11 — LE RAPPORT EST RELANCE, ET IL A TROUVE UN DEFAUT

```
sortie : notice/A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-11-15.csv  (4 702 lignes)
         notice/A4_RAPPORT_GEL_ECARTS_SEULS_2026-11-15.csv     (3 906 lignes)
```

**⛔ LES 48 ET 18 ECARTS NE SONT PAS PERIMES.** Je pensais que le rapport du 14/11
avait pu etre produit avant la pose du lot 1 : **non**. Relance sur les donnees du
jour, `Pourcentage 1` donne **exactement 48** et `Negociateur 1` **exactement 18**.
➡ **LE LOT 1 N'EST DONC PAS CLOS A 100 %.**

**⭐ MAIS LES 48 SE DECOMPOSENT, ET UN TIERS N'EN SONT PAS :**

```
   41  vrai ecart de fond        le classeur dit 75, nous 100
    5  MEMES valeurs, ORDRE different -> FAUX ECART
         ex. QP26TS7E : classeur « 25 », nous « 75 » -- et nos parts sont 75 ET 25
    2  une ligne portant un negociateur de la LISTE EN DUR (ci-dessous)
```

⚠ **ET LA CAUSE PROBABLE DES 41 EST LA MEME, EN PLUS SUBTILE** : le rapport compare
`Pourcentage 1` du classeur a **notre premier pourcentage par RANG**, alors que le
lot 1 a pose par **COTE** (`entree` 4 469 lignes / `sortie` 4 696). Les deux ordres
n'ont aucune raison de coincider. ⬜ **A MESURER avant de toucher a quoi que ce
soit : comparer les ENSEMBLES de parts, pas les positions.**

### ⛔⛔ LE DEFAUT NEUF : UNE LISTE DE NOMS ECRITE EN DUR, ET ELLE EST PERIMEE

`phase2/checks/rapport_gel_tous_les_champs.py:151` porte **`ANCIENS_HORS_REGISTRE`**,
un ensemble FIGE de 14 noms. Le rapport **ne consulte pas l'annuaire** : il range ces
noms en « HORS », donc leurs lignes ne sont **ni comparees ni rapatriables**.

```
MESURE DU 15/11, nom par nom, dans app_negociateur_personne :
   13 des 14 SONT DANS L'ANNUAIRE  -> le script les ecarte A TORT
      ABED . ALLEMAND . BERTRAND . AGRAIN . PETROSINO . BRUNON . LAUGIER
      EXBRAYAT . COMMERE . ADAMO . LEFAURE . BALIQUE . FRANCHINI Marjorie
    1 MANQUE VRAIMENT : **PITIOT** (0 ligne dans l'annuaire)
```

⭐ **C'est la question de Frederic du 15/11 qui a mis ca au jour** (« les negociateurs
ont deja ete faits, verifie ! »). Il avait raison : **ils sont faits**. Ce qui n'etait
pas fait, c'est de **retirer la liste en dur** — et personne ne pouvait le voir, parce
que le rapport continuait a annoncer « 24 anciens absents de notre registre » en
lisant sa propre constante.

⬜ **LE CORRECTIF (additif, lecture seule)** : faire lire `app_negociateur_personne`
au lieu de la constante, et ne garder en « HORS » que ceux qui y manquent vraiment —
soit PITIOT aujourd'hui. Puis relancer : les 24 lignes redeviennent comparables.
⚠ Meme famille que le libelle fige du worker (21/10) : **une liste en dur ne se met
pas a jour toute seule, et elle mentit en silence.**

### ⚠ LES 18 ECARTS DE `Negociateur 1` — NOTRE COTE PORTE L'AGENCE, PAS UNE PERSONNE

```
   classeur CHANTUREAU   nous FIRMINY GROUPE GROUPEGTI GROUPEGTIFIRMINY
   classeur ITIM         nous FIRMINY GROUPE GROUPEGTI GROUPEGTIFIRMINY
   classeur THOMAS       nous ARTHUR ARTHURVIVIER MARTHUR MARTHURVIVIER
   classeur HERITIER     nous COUDERT NICOLAS NICOLASCOUDERT
```
⬜ A instruire : deux cas distincts se melangent — celui ou nous n'avons AUCUNE
personne (le mandat porte l'agence) et celui ou nous avons une AUTRE personne.

### ✅ LE RESTE EST STABLE — les chiffres de 3.3 sont confirmes au 15/11

```
Commission TTC    314 « classeur seul »  (= les 303 utiles + 11)
Offre Achat       178 . Compromis 75 . Vente Fixee 38   -> les 241 inchanges
Vente Prevue    2 303 ecarts
Vente Reglee    3 735 . Numero de facture 3 719   -> aucune case chez nous
Mandat             33 « classeur seul »
lignes NON RATTACHEES : **87** ⚠ ma mesure en base du 15/11 en comptait 85 --
   l'ecart de 2 n'est pas explique, a regarder avec A6.
```

### ✅✅ LE CORRECTIF EST POSE ET MESURE — 15/11, et LE TRAVAIL ETAIT BIEN FAIT

`phase2/checks/rapport_gel_tous_les_champs.py` : la liste figee devient `ANCIENS_REPLI`
(les candidats a tester + le filet), et `charger_anciens_hors_registre(cl)` lit
`app_negociateur_personne` au demarrage. **69 lignes ajoutees, 2 modifiees, un seul
fichier. Aucune donnee touchee.**

**CE QU'IL DIT AU DEMARRAGE** (et il NOMME ses trouvailles, pour qu'un faux positif
se voie a la lecture) :

```
anciens : 13 des 14 noms codes sont DANS l'annuaire (198 personnes lues)
          -> ils redeviennent COMPARABLES
   presents : ABED, ADAMO, AGRAIN, ALLEMAND, BALIQUE, BERTRAND, BRUNON, COMMERE,
              EXBRAYAT, FRANCHINI Marjorie, LAUGIER, LEFAURE, PETROSINO
   ⛔ VRAIMENT HORS REGISTRE : PITIOT
```
⭐ Les 13 sont **exactement** ceux que j'avais verifies un par un en SQL : zero faux
positif. La garde du patronyme a tenu.

**LE MOUVEMENT DES VERDICTS — 24 lignes liberees, et 22 etaient DEJA JUSTES :**

```
                      avant            apres          mouvement
   Negociateur 1   4671 ident . 11 HORS   4680 . 1 HORS   +9 identique . +1 ecart
   Negociateur 2    635 ident . 36 HORS    648 . 23 HORS  +13 identique
   Negociateur 3     12 ident .  1 HORS     12 .  0 HORS  +1 ecart
                      -------------------------------------------------
                      24 lignes liberees -> 22 « identique » . 2 « ECART »
```

➡ ⭐⭐ **LA REPONSE A LA QUESTION OUVERTE : le rapatriement des anciens negociateurs
ETAIT BIEN FAIT.** 22 des 24 lignes sont d'accord avec le classeur ; il ne reste que
**2 vrais ecarts** a instruire. Le rapport nous faisait croire a 24 lignes de travail
en suspens alors qu'il ne restait que deux cas.

**ET LES 24 QUI RESTENT EN « HORS » SONT LES BONS** : 17 « meilleursagents » + 6
« GTI » + 1 « DENOPCE 1/2 » = 24, les apporteurs d'affaires qui ne sont pas des
personnes. Le compte boucle exactement.

**⭐ PITIOT N'A AUCUN EFFET AUJOURD'HUI** : la note « ancien ABSENT de notre registre »
a **disparu** des notes, donc PITIOT n'apparait sur **aucune** ligne rattachee. Son
absence de l'annuaire ne coute rien pour l'instant. ⬜ A creer quand meme un jour,
pour que la liste de repli puisse etre retiree.

**⚠ CE QUI N'A PAS BOUGE : `Pourcentage 1` reste a 48 ecarts.** Les 2 lignes portant
un ancien avaient donc un ecart de pourcentage **independant** de leur mise a l'ecart.
➡ La piste de la comparaison PAR POSITION (le classeur par rang, nous par cote
`entree`/`sortie`) reste la seule explication plausible des 41. **A MESURER.**

**⚠⚠ ET LA FENETRE SE REFERME** : le classeur porte maintenant **4 789 lignes**
(4 783 le 09/11) contre un plafond de `A1:AL6000` -> **il reste 1 211 lignes**.
Voir A3.

### ⭐⭐⭐ LES 48 ECARTS DE `Pourcentage 1` — MESURE DU 15/11, ET CE N'EST PAS CE QUE JE CROYAIS

**Mesures rejouables** : `scratchpad/mesure_pourcentages.py` · `verif_633.py` · `origine_48.py`
(lecture seule, aucune ecriture).

**⛔ D'ABORD, UNE FAUSSE ALARME QUE J'AI MOI-MEME FABRIQUEE ET RETIREE.** J'avais
annonce « 633 lignes declarees identiques ont des parts differentes ». **C'etait mon
parsing** : sur les 4 646 lignes « identique », **ZERO** ne porte la parenthese
« nos parts : ... » -- cette colonne ne contient que notre valeur **du rang 1**. Je
comparais donc 2 parts du classeur a UNE SEULE des notres. Le rapport, lui, compare
les rangs 2 et 3 dans **leurs propres colonnes**. Les 633 n'existent pas.
⭐ *La verification a attrape l'erreur avant qu'elle n'entre au plan. C'est la lecon
du 14/11 : un chiffre qui surprend se verifie DANS LA METHODE avant d'etre cru.*

**LE LOT 1 EST-IL PASSE SUR CES 48 LIGNES ?**

```
   A  POSEE par le lot 1 (origine classeur_reconstitue)   28
   C  JAMAIS posee (origine hektor_partage_suppose)       20
```

**⭐⭐ ET LE CAS D'ECOLE TRANCHE LA NATURE DU DESACCORD. Ligne `2DUPM26R` :**

```
   LE CLASSEUR DIT   Negociateur 1 = JORAND, 100 %        (une seule personne)
   NOUS DISONS       entree  SANDRINE DELAVAUD   50 %     (elle a RENTRE le bien)
                     sortie  FREDERIQUE JORAND   50 %     (elle a VENDU)
   et l origine de NOS DEUX LIGNES est « classeur_reconstitue »
```

➡ **LE CLASSEUR ET NOUS NE DECRIVONS PAS LA MEME CHOSE.** Le classeur repond
« qui touche la commission, et combien » ; notre table repond « qui a rentre et qui
a vendu ». **Meme famille exactement que la decision sur l'AGENCE du 09/11** : *« le
classeur enregistre QUI A VENDU, nous enregistrons OU LE BIEN EST PARQUE. Aucune des
deux n'est fausse. »*

**⚠⚠ MAIS UN POINT SERIEUX RESTE, ET JE NE LE TRANCHE PAS :** nos deux lignes
portent l'origine **`classeur_reconstitue`** alors que **le classeur ne nomme pas
DELAVAUD**. L'etiquette d'origine dit donc « ca vient du classeur » pour une
repartition que le classeur n'enonce pas telle quelle -- elle est **deduite** par la
regle 50 % entree / 50 % sortie. ⛔ **Une etiquette d'origine qui recouvre une
deduction, c'est la porte de l'accord circulaire** (lecon du 14/11 : 874 des 897
« accords » de la charge etaient le classeur contre lui-meme).

⬜ **LA PROCHAINE MESURE, ET ELLE EST PRECISE** : lire
`phase2/checks/rapatrier_repartition_classeur.py` pour etablir **quelle regle** il
applique, et **si une origine distincte** (par exemple `classeur_deduit`) devrait
separer ce que le classeur DIT de ce que nous en DEDUISONS.
⚠ Tant que ce n'est pas fait, **ne pas compter ces 28 lignes comme un ecart a
corriger** : ce sont peut-etre deux lectures legitimes.

⬜ **ET LES 20 AUTRES** (`hektor_partage_suppose`, jamais posees) : savoir si elles
sont restees hors de la 1re passe par confiance du lien, ou si elles ont ete
ecartees pour une autre raison.

```
la forme des 48, comparees par ENSEMBLE de parts :
    6  MEMES parts, ordre different          -> faux ecart de position
   42  MEME SOMME (100), decoupage different -> la question de nature ci-dessus
    0  somme differente                      -> AUCUN ecart arithmetique
```
⭐ **Aucune des 48 ne presente d'erreur de somme.** Les parts bouclent toujours.

### ⏰⏰ A2 EST POSEE LE 15/11 — **LA MESURE QUI COMPTE EST CELLE DE DEMAIN MATIN**

```
patch   : supabase/patch_essai_a2_plage_app_2026-11-15.sql           JOUE le 15/11
inverse : supabase/patch_essai_a2_plage_app_2026-11-15_INVERSE.sql   pret, NON joue
controles : ..._REPETITION.sql  (lecture seule, 7 points)
pose par  : node Console/apply_sql_patch.js -> via le pooler aws-1-eu-west-2
```

**LA LIGNE D'ESSAI : `app_affaire_id = 1001424`**, offre `refused` du 2006-04-01,
sur l'annonce **28351** / chaine **14001** / dossier **D2006-0007**, avec
**`hektor_affaire_id = NULL` et `present_in_hektor = false`** — c'est tout le sujet.

**LA CIBLE A ETE CHOISIE PAR LA MESURE** : vendue en 2006, **hors du parc vivant**
(0 ligne dans `app_dossier_current`), **sans aucune offre** — donc elle reproduit
exactement le cas des 144 offres manquantes — et **absente du classeur** (0 lien),
donc l'essai ne fausse aucune mesure du chantier.

**LES 6 CONTROLES DE LA POSE, TOUS VERTS, avec leur temoin d'AVANT :**

```
                                              avant      apres
   la ligne d essai                              -      1001424 . NUL . false  ✅
   la plage app (>= 1 000 000)                 340          341               ✅
      dont SANS numero Hektor                    0            1               ✅
   parties de la chaine (declencheur AFTER INSERT) 8          8               ✅ rien cree
   transactions de la chaine 14001               2            3               ✅
   les 2 transactions d origine (20217, 6544)    2            2               ✅ intactes
   etiquettes de la chaine                       1            1  D2006-0007   ✅ pas de 2e
```

⭐ Le declencheur des parties n'a **rien** cree, comme prevu : la ligne n'a ni
`acquereurs_json` ni `mandants_json`.
⭐ La chaine porte maintenant `compromis/active | offre/refused | vente/-` : l'offre
**refusee** n'a declenche aucune des 4 regles de chainage, comme voulu.

### ⏰ CE QU'IL FAUT MESURER DEMAIN MATIN, APRES 07:45

Le run tourne a **05:00** (fin 07:03-07:34) et **la descente a 07:45**. L'essai doit
survivre AUX DEUX. ⚠ Et il faut regarder **LES DEUX BASES** : la ligne a ete posee
dans **Supabase seulement** ; `app_affaire_ledger` est « serveur maitre » (la descente
ne la cree pas), mais le run ecrit le SQLite local et un push existe.

```
   LA COMMANDE : rejouer supabase/patch_essai_a2_plage_app_2026-11-15_REPETITION.sql
   PUIS, en local (lecture seule) :
     python -X utf8 -c "import sqlite3;con=sqlite3.connect('file:phase2/phase2.sqlite?mode=ro',uri=True);print(con.execute('SELECT app_affaire_id,kind,hektor_affaire_id,present_in_hektor FROM app_affaire_ledger WHERE app_affaire_id=1001424').fetchall())"
```

```
   ✅ SI la ligne 1001424 est INTACTE dans Supabase (341 lignes, 1 sans numero) :
      le temoin positif existe enfin -> LES 241 TRANSACTIONS DU CLASSEUR PEUVENT
      ETRE CREEES CHEZ NOUS (lot B de 3.3). C'est le deblocage.
   ⛔ SI elle a DISPARU : les protections lues dans le code ne suffisent pas, et il
      faut trouver QUI l'a retiree avant d'ecrire une seule des 241. Chercher dans
      cet ordre : le journal du run, le push (`--push` seul ?), la descente.
   ⚠ SI elle est intacte dans Supabase mais ABSENTE en local : ce n'est pas un echec
      -- le registre est serveur maitre -- mais il faut le DIRE, car le lot B devra
      alors etre pose cote Supabase, jamais cote SQLite.
```

⛔ **NE PAS LAISSER CETTE LIGNE EN PLACE INDEFINIMENT** : son `payload_json` porte
`a_supprimer_apres_mesure`. Une fois la mesure faite, jouer l'INVERSE.
*« Un essai qui crie tous les jours n'est plus un essai. »*

### ✅⭐⭐⭐ A2 EST MESUREE LE 15/11 A 07:58 — **LA LIGNE A SURVECU, LE TEMOIN EST POSITIF**

⚠ **Ma note disait « demain matin » : c'etait FAUX, la nuit etait DEJA passee.**
L'essai a ete pose a **00:35:39**, et les deux epreuves ont eu lieu la nuit meme : le run
**a 04:00** (pas 05:00) et la descente **a 06:45** (pas 07:45), terminee a **07:11:32**.
Les horaires que je recopiais etaient perimes ; ceux-ci sont lus dans `logs/scheduled/`
(`quotidien_2026-11-15_04-00-02.log`, `descente_2026-11-15_06-45-02.log`).

```
                                          a la pose   apres le run ET la descente
   la ligne 1001424 chez Supabase              1                1      OK INTACTE
      last_seen_at                        00:35:39         00:35:39    OK PAS TOUCHEE
      numero Hektor / present_in_hektor   NUL / false     NUL / false  OK
   la plage app (>= 1 000 000)                341              341     OK
      dont SANS numero Hektor                    1                1    OK
   les 2 transactions d origine (20217,6544)    2                2     OK INTACTES
   la chaine 14001                              3                3     compromis/active|offre/refused|vente/-
   parties de la chaine                         8                8     OK rien cree
   etiquettes de la chaine                      1                1     D2006-0007
```

⭐⭐⭐ **LE TEMOIN POSITIF, ET C'EST LUI QUI FAIT LA PREUVE** : **339 des 341 lignes de la
plage app ont ete REVUES cette nuit** (`last_seen_at` au 15/11, le plus recent a
**05:15:05**). Le run a donc bien **traverse la plage app** — il ne l'a pas ignoree — et
il a **conserve** la seule ligne sans numero Hektor. *Un zero ne se croit pas sans temoin
positif* : ici le positif existe.

⚠ La 2e ligne non revue est **1001361** (offre `proposed` #33098, vue pour la derniere
fois le **26/10**, soit il y a 20 jours, `present_in_hektor = true`). Elle survit aussi.
Second temoin, gratuit : une ligne de la plage app non revue depuis 3 semaines **reste**.

### ⛔⛔ ET LA MESURE A CORRIGE UNE ERREUR QUE J'AVAIS ECRITE : LE LOCAL EST LE MAITRE

```
   local  phase2.sqlite  : 31 157 lignes . 0 sans numero Hektor . 1001424 ABSENTE
   Supabase              : 31 158 lignes . 1 sans numero Hektor . 1001424 PRESENTE
   l ecart est de 1, EXACTEMENT notre ligne -- aucune autre divergence
```

⛔ **J'avais ecrit « `app_affaire_ledger` est serveur maitre »**, en m'appuyant sur
`registre_depuis_console.py:23` (« creee par la descente : NON »). **Le code dit le
contraire**, et il le dit en toutes lettres — `pull_from_supabase.py:29` :

> « app_affaire_ledger, app_diffusion_target, [...] **-> le LOCAL en est le maitre,
> Supabase la copie. Les descendre serait a l'envers.** »

Les deux commentaires parlent de deux choses : la descente **ne recree pas** la table
(vrai), **et** le flux normal va **du local vers Supabase** (vrai aussi). Le FAIT mesure :

```
   le flux         : local -> Supabase, par UPSERT (registre_depuis_console.py:408,
                     « app_affaire_ledger?on_conflict=app_affaire_id »)
   -> un UPSERT AJOUTE et MET A JOUR : il n efface JAMAIS ce qu il ne connait pas.
      C est POUR CA que la ligne a survecu. Ce n est pas une bienveillance du run,
      c est LA FORME DE L ECRITURE.
   rien ne redescend : la descente REFUSE d ecrire une table qu elle n a pas creee
                     (garde-fou `sb_pull_state`)
```

⭐⭐ **CE QUE CA CHANGE POUR LE LOT B (les 241 transactions), ET C EST A TRANCHER PAR
FREDERIC** — je ne choisis pas :

```
   POSEES DANS SUPABASE SEULEMENT (ce que l essai vient de prouver faisable) :
     OK  elles survivent au run et a la descente, indefiniment
     OK  l APP les voit (le front lit Supabase)
     NON MAIS tout le LOCAL les ignore : les scripts de nuit, les rapports, les
         sentinelles et les mesures du chantier lisent phase2.sqlite
     !!  dont `export_app_payload.py:2383` qui lit justement
         « app_affaire_ledger WHERE present_in_hektor = 0 » EN LOCAL -- notre cas exact
   POSEES DANS LE LOCAL, puis montees par le push :
     OK  elles sont dans le maitre, donc vues par TOUT LE MONDE
     !!  mais c est une ecriture dans la base du run, pas dans une copie
   POSEES DANS LES DEUX :
     !!  deux ecritures a tenir d accord, et un retour arriere a deux endroits
```

⏰ **LA MESURE QUI MANQUE, ET ELLE EST GRATUITE** : avant de retirer l'essai, regarder si
**l'app affiche** la ligne 1001424 dans le registre des transactions du dossier
**D2006-0007**. C'est la reponse a « une transaction sans numero Hektor est-elle
utilisable ? », et elle ne coute aucune ecriture.

⛔ **L'INVERSE N'EST PAS JOUE** : `..._INVERSE.sql` attend. Le retrait est une ecriture en
production, donc il attend l'accord de Frederic — et il vaut mieux l'attendre apres la
mesure de l'ecran ci-dessus.

### ⭐⭐⭐ ET LA VRAIE REPONSE : L'APP FAIT EXACTEMENT CE QUE L'ESSAI A FAIT

**Question de Frederic (15/11) : « quelle difference avec une ecriture faite dans l'app
sur les transactions ? »** — mesuree dans la fonction du serveur, pas deduite.
**Reponse : AUCUNE DIFFERENCE DE NATURE.**

Une transaction creee depuis l'app (modale « Changer le statut » → Offre / Compromis /
Vendu) passe par **`app_change_annonce_status_optimistic`**, et cette fonction est **LA
SEULE de tout le serveur qui INSERE dans `app_affaire_ledger`** (verifie par expression
reguliere sur les 100+ fonctions : `insert into (public\.)?app_affaire_ledger`).

Ce qu'elle ecrit, lignes 163-195, **avec ses propres commentaires** :

```
v_affaire_id := nextval('public.app_affaire_id_app_seq');   -- LA PLAGE APP
insert into public.app_affaire_ledger (...) values (
   v_affaire_id, ...,
   null,            -- « Hektor ne la connait pas encore : LA CASE RESTE VIDE »
   ...,
   'en_cours',
   now(), now(),
   false);          -- « DELETE-NEVER : LE RUN DE NUIT LA CONSERVERA »
```

⭐⭐⭐ **Donc chaque clic de l'app cree deja une ligne : plage app, SANS numero Hektor,
`present_in_hektor = false`.** C'est mot pour mot l'etat de notre ligne 1001424. L'essai
A2 n'a pas invente un chemin exotique : il a **refait a la main le geste normal de l'app**,
et il a prouve pour la premiere fois l'intention que le code ecrivait depuis le debut
(« delete-never »).

**LES DEUX SEULES DIFFERENCES, et elles sont precises :**

```
1. L APP POSE EN PLUS UN TRAVAIL POUR LE WORKER (app_console_job) :
      -> Hektor cree la transaction, rend son numero, le run le pose sur la ligne
      -> la ligne descend alors en local, et l etat « sans numero » etait TRANSITOIRE
   NOTRE LIGNE n a demande aucun numero : son etat « sans numero » est DEFINITIF.
   C est exactement ce que Frederic a demande (« il faut pas tout creer dans hektor »).
2. L app ecrit aussi la file d envoi (app_affaire_champ_app), l etiquette du dossier,
   les parties, et l etat 'en_cours' (notre essai : 'refused', expres -- une offre
   refusee ne declenche aucune des 4 regles de chainage).
```

⭐⭐ **CE QUE CA CHANGE POUR LE LOT B** : ecrire les 241 **sur le serveur** n'est pas un
detour, **c'est le chemin par lequel l'app ecrit TOUTES ses transactions**. Les 340 lignes
de la plage app sont nees ainsi. Elles ne sont en local que parce que Hektor leur a donne
un numero ensuite.

⚠ **La reserve du matin reste vraie, mais elle change de nature** : « les outils locaux
ne les verront pas » est l'etat NORMAL de toute transaction nee dans l'app entre le clic
et le retour de Hektor. Pour les 241, cet etat serait **definitif** au lieu d'etre
transitoire. C'est **ca** le seul vrai sujet, et il se formule simplement : **quels outils
doivent voir les 241 ?** Si la reponse est « l'app, et les mesures du chantier », il faut
les deux copies ou un lecteur qui lit le serveur.

⛔ **ET UNE FAUTE DE MESURE A SIGNALER** : ma premiere requete cherchait
`insert into app_affaire_ledger` et a rendu **zero** — le code ecrit
`insert into public.app_affaire_ledger`. J'ai failli conclure « l'app ne cree jamais de
transaction », ce qui est faux. *Un zero ne se croit pas sans temoin positif* : ici le
zero venait de mon motif, pas de la base.

### ⭐⭐⭐ « POURQUOI ON NE DESCEND PAS AU SERVEUR, SANS NUMERO HEKTOR ? » — ON LE FAIT DEJA

**Question de Frederic (15/11)**, et elle vise juste : *« pourquoi on ne descend pas au
serveur comme le worker mais sans numero Hektor ? Et trouver comment ne pas faire sonner
les sentinelles. »*

⭐⭐⭐ **LA DONNEE EST DEJA SUR LE SERVEUR LOCAL.** La descente l'a descendue ce matin
dans **`app_affaire_ledger__sb`** — la *doublure*, l'image du serveur :

```
   app_affaire_ledger__sb (local)  : 31 158 lignes . 1 SANS numero Hektor
   et NOTRE LIGNE y est, entiere   : 1001424 . offre . refused . chaine 14001 .
                                     dossier 1355930 . present_in_hektor 0
   plage app dans la doublure      : 341  (contre 340 dans le registre local)
```

**IL NE MANQUE QU'UNE MARCHE : la recopie de la doublure vers `app_affaire_ledger`.**
Le run fait **UPDATE, jamais INSERT** — il *adopte* une ligne de l'app quand Hektor la
lui rend, il ne la *cree* jamais de son propre chef.

⭐⭐ **ET CE N'EST PAS UN OUBLI : LA TACHE EST DEJA ECRITE, ET NON FAITE.**
`notice/LISTE_TACHES_A_COCHER_2026-08-29.md`, chapitre C.19-d (l. ~767) :

> `[ ] 26bis-TRANSACTIONS   une transaction nee dans l'app n'est au registre LOCAL`
> `         qu'une fois retrouvee chez Hektor (UPDATE, jamais INSERT)`

C'est **mot pour mot** la question de Frederic. Le dessein est celui des doublures
(`affaire_ledger.py` l. 1021) : *« DETECTER N'EST PAS RESOUDRE [...] L'ecart n'invente pas
d'alarme : il tombe dans le journal de 07:30 (comparer_doublures.py), colonne « app
seule », qui couvre DEJA app_affaire_ledger__sb. »*

**ET LE JOURNAL A FAIT EXACTEMENT CA CE MATIN** (`app_doublure_journal`, lecture seule) :

```
   releve_le    doublure                 accord   hektor_seul   app_seule
   2026-11-15   app_affaire_ledger__sb   31 157        0            1     <- NOTRE LIGNE
   2026-11-14   app_affaire_ledger__sb   31 157        0            0
   2026-11-13   app_affaire_ledger__sb   31 157        0            0
```

Les DEUX mecanismes d'adoption lisent la doublure (`affaire_ledger.py` l. 749 et 762) :
par **triplet** (annonce, genre, numero Hektor) pour les lignes QUI ont un numero, et par
**(annonce, genre, acquereur Hektor)** pour celles **SANS** numero — mais cette seconde
voie **exige un `hektor_acquereur_id`**, et elle ne sert qu'a FUSIONNER le jour ou Hektor
connait l'affaire. Elle ne fait pas descendre une ligne qui n'ira jamais chez Hektor.

### ⛔⛔ LES SENTINELLES : UNE SEULE EST CONCERNEE, ELLE A LEVE LA MAIN CE MATIN

```
   la vue      app_affaires_sans_numero_hektor
               = SELECT ... FROM app_affaire_ledger WHERE hektor_affaire_id IS NULL
               -> elle rend 1 ligne aujourd hui : LA NOTRE
   la regle    data.affaire_sans_numero_hektor   (monitoring/check_gti_health.py:494-500)
               rule "absolute" . max 0           -> DEPASSE des la premiere ligne
   la gravite  AUCUNE `severity` declaree -> defaut `warning` (l. 1888)
               et SEULS LES CRITICAL ENVOIENT -> AUCUNE ALERTE N EST PARTIE
   le passage  GTI Health Monitor, 15/11 a 06:48:55, resultat 0 . suivant 08:48
```

⭐⭐⭐ **ET LA REPONSE A « COMMENT NE PAS LA FAIRE SONNER » EST ECRITE DANS LE CODE
DEPUIS LE 28/08**, juste au-dessus de la regle :

> *« NB : ce seuil de 0 devra etre revu **quand C.19 etape 4 permettra a l'app de creer
> une transaction sans passer par Hektor** — ce jour-la, ces lignes seront normales. »*

Il n'y a donc **rien a inventer** : le projet avait prevu l'evenement et nomme le remede.

### ⭐ LES DEUX TRAVAUX QUI EN DECOULENT — ADDITIFS, A TRANCHER PAR FREDERIC

```
(a) 26bis-TRANSACTIONS : le run RECOPIE de la doublure vers le registre local les
    lignes « app seule » qui n ont pas de numero Hektor. Elles sont deja protegees
    une fois la-bas : le marquage commence par « app_affaire_id < PLAGE_RESERVEE_APP »
    et le seul DELETE EXIGE un numero Hektor. Rien d autre a garder.
    -> les outils locaux (apparieur, rapports, mesures du chantier) les verraient
(b) LA SENTINELLE, avec son TEMOIN INVERSE : ne plus compter comme anomalie une ligne
    DE LA PLAGE APP (>= 1 000 000) sans numero Hektor, et GARDER le seuil 0 pour les
    autres -- une ligne venue de Hektor sans numero reste une anomalie.
    Temoin d aujourd hui : 1 ligne sans numero, et elle est DANS la plage app ;
    0 hors plage. La sentinelle continuerait donc de proteger ce qu elle protegeait.
```

⛔ **Ce sont des propositions de code : rien n'est ecrit sans son « go ».**

### ⛔⛔⛔ AUDIT DU 15/11 — « L'ID HEKTOR RESTE OBLIGATOIRE TANT QUE LA COUPURE N'A PAS EU LIEU »

**Consigne de Frederic**, en trois points : *« tant que la coupure n'a pas eu lieu avec
Hektor il faut que les gestes dans l'app soient envoyes chez Hektor pour avoir son id
Hektor necessaire aux modifications. Donc nos ecritures ne seront pas modifiables dans
Hektor, il faudra le prevoir. Et il faut garder une securite : si une transaction est
ajoutee dans l'app, il faut toujours qu'elle ait son id Hektor. »*

⛔⛔ **ET IL A ARRETE UNE PROPOSITION FAUSSE DE MA PART.** Ce matin je proposais
« ne plus compter comme anomalie une ligne DE LA PLAGE APP sans numero Hektor ». C'etait
**trop large** : ca aurait eteint la garde pour **tous** les gestes vivants de l'app, donc
aussi pour celui qui aurait **echoue** a partir chez Hektor. La garde doit distinguer
**l'INTENTION**, pas la plage.

#### POINT 1 — « les gestes doivent partir chez Hektor » : C'EST TENU, ET MESURE

```
   les 340 lignes de la plage app : 340 ONT leur numero Hektor, soit 100 %
   TROIS pieces le garantissent, toutes mesurees dans le code :
     a) le RPC pose le travail worker des le clic (app_console_job)
     b) le worker cree chez Hektor et pose le numero
     c) LE FILET : poserNumerosManquants (console_job_worker.js:24109), appele a
        CHAQUE relecture d annonce (l. 4431), ALLUME EN DUR
        (SECONDE_PREUVE_RELECTURE = true, l. 24089)
```

Le filet cible **exactement nos futures lignes** :
`hektor_affaire_id=is.null & present_in_hektor=is.false & app_affaire_id=gte.1000000`.
Il lit Hektor, et pose le numero **seulement** s'il trouve **un seul** candidat par
l'acquereur. Abstention declaree sinon (`sans_acquereur`, `plusieurs_lignes_orphelines`,
`N_candidat(s)`). Il ne devine jamais.

#### POINT 2 — « nos ecritures ne seront pas modifiables » : DEJA PREVU, DEJA EN PLACE

```
   app_modifier_affaire_optimistic (l. 31-39)  « ON NE MODIFIE QUE CE QUE HEKTOR CONNAIT »
     -> sans numero        : raise « modification_sans_numero_hektor »
     -> present_in_hektor false : raise « modification_transaction_effacee »
   app_geste_affaire_optimistic (l. 109-112)   « PAS DE GESTE SANS NUMERO HEKTOR » (P3, 27/10)
     -> raise « sans_numero_hektor: le geste ne peut pas partir »
   l ECRAN le dit deja     App.tsx:24444 et ModaleStatutV2.tsx:941 :
                           « nee dans l app, sans numero Hektor »
                           App.tsx:20027 : le message du refus
```

⭐ **Donc les 241 seraient en LECTURE SEULE dans l'app, sans qu'on ait rien a ecrire.**

⚠⚠ **MAIS UN DEFAUT PRECIS** : pour les 241, c'est le **second** verrou qui mordra
(`present_in_hektor is false`), et **son message est FAUX** — *« Hektor ne la rend plus »*
alors qu'elle **n'y a jamais ete**. Un negociateur y lira une perte de donnee.

#### POINT 3 — « garder la securite » : elle existe, et il ne faut PAS l'eteindre

```
   data.affaire_sans_numero_hektor . vue app_affaires_sans_numero_hektor . seuil 0
   gravite : warning (aucune severity declaree) -> n ENVOIE PAS, mais leve la main
```

### ⛔⛔ LE RISQUE QUE L'AUDIT A TROUVE, ET QUI N'ETAIT NULLE PART AU PLAN

**`poserNumerosManquants` ECRIT UN `error` AU JOURNAL CONSOLE** quand il ne peut pas poser
le numero (`poses === bilan.length ? "done" : "error"`, l. 24159).

**TEMOIN REEL, mesure dans `app_console_job_log`** — une seule trace depuis l'origine :

```
   2026-10-22 21:49 . step hektor_transaction_seconde_preuve . status ERROR
   « Seconde preuve : 0 numero(s) pose(s) sur 1 transaction(s) nee(s) dans l app sans numero »
   annonce 24113 . app_affaire_id 1001375 . compromis . abstention . « 0_candidat(s) »
```

⛔ **Avec les 241, chaque geste du worker sur une annonce qui en porte une ecrirait une
erreur Console** — et le moniteur compte les erreurs Console (orange 48 h, meme tranchee).
C'est *« un essai qui crie tous les jours »*, en production.
⭐ **Volume reel : seulement 3 des biens concernes sont VIVANTS** (40318, 58979, 8494).
Le risque est donc **faible en volume mais certain**, et il se repete a chaque geste.

### ⭐⭐⭐ LA SOLUTION PROPOSEE — DECLARER L'EXCLUSION, JAMAIS ETEINDRE LA GARDE

La regle du projet existe deja : *« Exclure : le DECLARER »* et *« une exclusion a part
doit etre appelee par CHAQUE porte »*. On ne touche donc a aucun seuil : **on marque**.

```
PIECE 1  LA MARQUE -- colonne `transaction_origine` sur app_affaire_ledger
         (l idiome existe deja : mandat_origine, notaires_origine)
         valeur 'classeur' pour les 241 . NULL pour tout le reste
         ⚠ POSEE DANS LE MEME INSERT, jamais apres : la fenetre entre les deux
           serait un faux positif, et le projet a deja paye ca ailleurs.

PIECE 2  LA SENTINELLE, AVEC SON TEMOIN INVERSE -- la vue ne compte plus les
         lignes marquees 'classeur', et GARDE LE SEUIL 0 POUR TOUT LE RESTE,
         plage app comprise. Un geste vivant sans numero leve TOUJOURS la main.
         TEMOIN : aujourd hui la vue rend 1 (notre essai, NON marque) ; apres la
         marque elle rendrait 0 ; en retirant la marque, 1 revient.

PIECE 3  LE FILET DU WORKER -- poserNumerosManquants ajoute
         `&transaction_origine=is.null` a sa requete : il ne cherche plus de numero
         pour une ligne qui n en aura jamais -> plus d `error` au journal, et le
         compte `poses === bilan.length` redevient juste.

PIECE 4  LE MESSAGE DE L ECRAN -- pour une ligne marquee, dire LA VERITE :
         « reprise de l historique : elle n existe pas chez Hektor et n y sera pas
         creee » au lieu de « Hektor ne la rend plus ». Et l etiquette
         « nee dans l app, sans numero Hektor » devient « reprise du classeur ».
         ⚠ C est la correction du defaut du POINT 2.

PIECE 5  26bis-TRANSACTIONS -- la recopie de la doublure vers le registre LOCAL,
         pour que l apparieur, les rapports et les mesures du chantier les voient.
         A part : elle ne depend pas des 4 autres.
```

**L'ORDRE EST CONTRAINT** : la piece 1 **avant toute ecriture des 241**, puis 2, 3, 4.
La piece 5 peut venir avant ou apres.

⚠ **CE QUE JE NE TRANCHE PAS, ET QUI EST A LUI** : faut-il laisser
`present_in_hektor = false` sur les 241 ? C'est ce que fait l'app a chaque clic, donc
c'est coherent. Mais aujourd'hui ce `false` veut dire « Hektor ne la rend plus » (une
disparition), alors que pour les 241 il voudrait dire « elle n'y a jamais ete ».
⭐ **La marque leve l'ambiguite sans toucher a la colonne** — c'est pour ca que je
propose une marque plutot que de bricoler `present_in_hektor`, qui est lu partout.

⛔ **Rien n'est ecrit sans son « go ».**

### ⛔⛔ RECTIFICATION DU 15/11 — LE « DEFAUT DU POINT 2 » ETAIT FAUX, ET L'ECRAN SAIT DEJA

**Frederic a demande d'expliquer plus simplement. En reverifiant, DEUX de mes affirmations
tombent — toutes deux dans le bon sens : le projet avait deja tranche.**

**1) L'ORDRE DES TESTS. J'avais dit que le message « Hektor ne la rend plus » sortirait
pour les 241. C'est FAUX** : dans `app_modifier_affaire_optimistic`, le test du **numero**
est a la ligne **32**, celui de `present_in_hektor` a la ligne **36**. Le premier gagne.
Une ligne sans numero recoit donc :

> *« modification_sans_numero_hektor : cette transaction n'existe pas encore chez Hektor »*

C'est **le bon message**. Il reste une nuance de MOT, pas un defaut : « pas **encore** »
suppose une attente, alors qu'une reprise du classeur n'ira jamais chez Hektor.

**2) L'ECRAN NE DIRA PAS « plus dans Hektor »**, et c'est deja code. La condition est
**`present_in_hektor === false && numero`** (App.tsx:32904 et 41380) : **il faut un
NUMERO** pour afficher cette mention. Et juste a cote, App.tsx:24444 /
ModaleStatutV2.tsx:941 affichent l'autre etiquette, exclusive :

```
   AVEC un numero + present_in_hektor false  ->  « plus dans Hektor »   (une disparition)
   SANS numero                               ->  « nee dans l app, sans numero Hektor »
```

⭐⭐⭐ **LE COUPLE « PAS DE NUMERO + present_in_hektor false » EST DEJA LE LANGAGE DU
PROJET** pour dire « nee chez nous, jamais chez Hektor ». Il n'y a donc **rien a inventer
pour l'affichage**, et surtout **rien a changer sur `present_in_hektor`** — colonne lue
**575 fois dans 150 fichiers** (mesure du 15/11). Y toucher serait un risque enorme pour
un gain nul.

### ⭐ LA PROPOSITION SE SIMPLIFIE DONC BEAUCOUP

```
PIECE 1  la marque `transaction_origine = 'classeur'`            -> GARDEE
PIECE 2  la sentinelle n en tient pas compte, seuil 0 ailleurs   -> GARDEE
PIECE 3  le filet du worker ignore les lignes marquees           -> GARDEE (le vrai risque)
PIECE 4  le message de l ecran                                   -> REDUITE a un MOT :
         « n existe pas encore chez Hektor » -> « n existe pas chez Hektor »
         pour une ligne marquee. Cosmetique, pas bloquant.
PIECE 5  26bis, la recopie vers le registre local                -> GARDEE, a part
```

⭐⭐ **LA MARQUE NE SERT PLUS QU'A UNE SEULE CHOSE, ET C'EST LA BONNE** : distinguer
*« elle ATTEND son numero »* (anormal si ca dure — la securite de Frederic) de
*« elle n'en aura JAMAIS »* (assume, declare). Deux lecteurs seulement en ont besoin :
**le filet du worker** (qui ecrit une erreur) et **la sentinelle** (seuil 0).

### ✅⭐⭐ LES PIECES 1 ET 2 SONT POSEES EN PRODUCTION — 15/11/2026, ET PROUVEES

**Go de Frederic, puis pose par `node Console/apply_sql_patch.js`** (passage par le POOLER,
l'hote direct n'a plus d'IPv4). Trois fichiers, convention du projet :

```
supabase/patch_transaction_origine_2026-11-15.sql             POSE
supabase/patch_transaction_origine_2026-11-15_REPETITION.sql  JOUE, 8 controles
supabase/patch_transaction_origine_2026-11-15_INVERSE.sql     ecrit, NON joue
```

**LA MESURE, faite a part du script — « appliquee » ne dit que « rien n'a leve » :**

```
   colonne          text / nullable                                        OK
   commentaire      pose, il contient « classeur »                         OK
   vue              7 colonnes, memes noms, meme ordre                     OK
   conditions       hektor_affaire_id IS NULL AND transaction_origine IS NULL   OK
   droits           postgres, service_role  (ni anon ni authenticated)     OK
   lignes marquees  0 -- le patch n a marque personne                      OK
   plage app        toujours surveillee (1 ligne : l essai A2)             OK
   TEMOIN INVERSE   avant=1  marquee=0  demarquee=1  -> basculement VRAI   OK
                    (joue dans un bloc qui leve : TOUT est annule, et
                     verifie apres : 0 ligne marquee, sentinelle a 1)
```

⭐ **L'essai A2 (ligne 1001424) a servi de cobaye**, reel et isole, sur un bien mort depuis
2006. ⛔ **IL DOIT RESTER EN PLACE** jusqu'a la fin des pieces 3 et 4 : sans lui, le controle
du temoin inverse n'est plus mesurable.

### ⛔⛔ CE QUE LA MESURE A TROUVE, ET QUI N'ETAIT PAS AU PLAN : LE PUSH FAIT `SELECT *`

`ledger_rows_for_push` (`phase2/sync/affaire_ledger.py:2932`) lit **`SELECT * FROM` la table
LOCALE** et envoie tout, moins `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` (l. 2875).

⭐ **Donc la pose chez Supabase seule est SURE** : tant que la colonne n'existe pas en local,
le push ne peut pas l'ecraser. ⚠⚠ **Mais le jour de 26bis**, la colonne locale devra entrer
dans cette liste **AVANT TOUT REMPLISSAGE** — meme patron que l'etiquette de dossier (09/11) et
l'annulation (10/11), et meme raison : **le 07/09, un `--push` a EFFACE une annulation faite une
heure plus tot**.

⭐ **ET L'ORDRE EST ECRIT DANS LE CODE** (`affaire_ledger.py`, l. 632-637) : *« POSEES CHEZ
SUPABASE DEPUIS CE JOUR -- dans cet ordre, jamais l'inverse : une colonne locale que Supabase
n'a pas est reclamee pour rien a la redescente »*. C'est fait dans le bon sens.

**LE PATRON COMPLET A DONC TROIS GESTES**, et seul le premier est fait :

```
   a) le patch Supabase                                   ✅ FAIT le 15/11
   b) la colonne dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS   ⬜ au moment de 26bis
   c) la colonne dans la liste locale `for neuve in (...)` ⬜ au moment de 26bis
```

⚠ **ET UNE DETTE NEUVE** : une fois l'essai A2 recopie en local par 26bis,
`patch_essai_a2_plage_app_2026-11-15_INVERSE.sql` ne suffit plus — il ne nettoie que le cote
Supabase. Il devra nettoyer **les deux cotes**.

### ✅⭐⭐ LA PIECE 3 EST ECRITE ET EPROUVEE HORS LIGNE — 15/11/2026

**Une ligne dans la requete du filet** (`poserNumerosManquants`, `console_job_worker.js`) :
`&transaction_origine=is.null`. Le filet ne cherche plus de numero a une transaction qui
n'en aura jamais.

**AVANT de toucher au code, DEUX mesures — et la premiere pouvait tout arreter :**

```
   PostgREST voit-il la colonne ? Le patch est passe en SQL DIRECT par le POOLER,
   donc son cache de schema pouvait l ignorer -- et la requete du filet serait
   partie en HTTP 400. MESURE (lecture seule, par l API REST) :
     select transaction_origine      -> HTTP 200
     le filtre exact du filet        -> HTTP 200, et il rend UNE ligne : 1001424
     temoin : lignes marquees        -> HTTP 200, liste VIDE (0 marquee)
   Le cache etait a jour. Rien a recharger.

   L essai hors ligne etait-il vert AVANT ? 13/13. C est la reference.
```

**APRES : 16/16, dont trois controles neufs** (`Console/test_seconde_preuve.js`) :

```
   (14) la requete du filet porte `transaction_origine=is.null`
   (15) une transaction MARQUEE classeur n est pas lue, et RIEN n est ecrit au journal
   (16) TEMOIN INVERSE : la MEME ligne SANS la marque -> le numero est pose
```

⭐⭐ **ET LE TEMOIN DU TEMOIN A ETE FAIT** : sur une COPIE du worker, dans le bac a sable,
filtre retire — (14) et (15) **rougissent**, (16) reste vert. Donc le filtre mord vraiment,
et il ne rejette pas tout.

### ⛔⛔ CE QUE CE TEMOIN A REVELE, ET QUI N'ETAIT PAS AU PLAN

Le risque nomme jusqu'ici etait *« un `error` au journal Console a chaque relecture »*.
**Il est pire que ca.** Sans le filtre, le controle (15) ne donne pas une erreur : il donne
`resultat: "numero_pose"`, `hektor_affaire_id: "50128"` sur la ligne 1001500.

⛔ **LE FILET AURAIT COLLE A UNE TRANSACTION DU CLASSEUR LE NUMERO D'UNE TRANSACTION
HEKTOR EXISTANTE** — des lors qu'un seul candidat chez Hektor porte le meme genre et le
meme acquereur. Ce n'est plus du bruit dans un journal, c'est **une fausse identite posee
en base**, et la regle du projet (« un numero ne se perd jamais ») serait violee dans
l'autre sens : un numero attribue DEUX fois.

⚠ **Volume** : il faut que la ligne du classeur porte un `hektor_acquereur_id`. Sans
acquereur, le filet s'abstient (`sans_acquereur`) et se contente d'ecrire l'erreur. Donc le
risque de fausse identite ne concerne que les lignes du classeur **rattachees a un
acquereur connu de Hektor** — a mesurer au moment des 241, mais la piece 3 le ferme pour
tous les cas d'un coup.

### ✅ LA PIECE 3 EST EN SERVICE -- 15/11/2026 14:22, REDEMARRAGE PAR FREDERIC

```
   LA PREUVE EST L HEURE DE NAISSANCE DES PROCESSUS, jamais l absence d erreur :
     code console_job_worker.js   15/11 13:05:56
     Actions      pid 22984   ne a 14:22:14   -> APRES le code
     Admin        pid 19496   ne a 14:22:14   -> APRES le code
     Documents    pid 21636   ne a 14:22:15   -> APRES le code
     SyncLight    pid 21952   ne a 14:22:16   -> APRES le code
   LES 4, pas un seul : ils partagent le fichier.

   ET LE CODE CHARGE EST BIEN CELUI-LA -- deux controles de plus :
     `transaction_origine=is.null` present l. 24126 du fichier sur disque
     l arbre de travail est PROPRE sur ce fichier = identique au commit 70e947d
     (l autre session n y a pas touche depuis : son dernier passage est 3d30082, 12:56)

   FILE VIDE AU MOMENT DU GESTE (critere du projet) : 0 pending, 0 running,
   avec TEMOIN POSITIF -- la meme requete voit un travail `done` a 14:19:20.
   Les 4 services sont Running, pid stables, journaux de demarrage sans erreur.

   ⚠ LE PREMIER REDEMARRAGE DE FREDERIC (13:01:46-48) ETAIT ARRIVE 4 MINUTES
     TROP TOT -- avant le code de 13:05:56. Seule la mesure de l heure des
     processus l a vu. C est exactement le piege du 20/10 (Admin au lieu de
     Documents), et c est pour ca que le projet exige LA PREUVE DU SUCCES.
```


### ✅⭐⭐ LA PIECE 4 (26bis-TRANSACTIONS) EST ECRITE ET EPROUVEE — 15/11/2026

**L'AUDIT A CHANGE L'ENONCE.** Mesure du 15/11, lecture seule :

```
   registre LOCAL   plage app : 340 lignes, TOUTES avec numero Hektor, 0 sans
   doublure __sb    plage app : 341 lignes, dont 1 SANS numero
   a recopier       1 SEULE LIGNE -- et c'est l'essai A2 (1001424)
   hors plage sans numero : 0 des deux cotes (temoin : 31 157 lignes communes)
```

Ce n'est donc pas « recopier 341 lignes » : les 340 sont deja en local parce que le run
les **adopte** des que Hektor leur donne un numero (`UPDATE, jamais INSERT`). Ce qui reste
dehors, c'est **ce qui n'aura jamais de numero** : 1 ligne aujourd'hui, **242** apres
l'insert des 241.

### ⛔ LE TROU QUE J'AVAIS MANQUE, ET QUI JUSTIFIE TOUTE LA PIECE

**La redescente des colonnes de classe A est un `UPDATE ... WHERE app_affaire_id = ?`.**
Elle ne cree JAMAIS une ligne : devant une transaction que le local ne connait pas, elle
touche zero ligne, **en silence**. Marquer les 241 chez Supabase ne les aurait donc jamais
fait descendre. Il fallait bien un INSERT -- et c'est tout ce qu'est 26bis.

### ⭐ LE SENS, ET POURQUOI IL N'EST PAS NEGOCIABLE

**Supabase d'abord, la machine ensuite.** Trois raisons independantes, chacune suffisante :

```
   1. LE FRAPPEUR DES NUMEROS DE LA PLAGE APP EST SUPABASE, et le projet s'est
      explicitement interdit de frapper en local : une premiere version prenait le
      MAX() de la table locale et « aurait redemarre a 1 pendant que Supabase en
      etait a 13 347 ». Un numero hors plage perdrait TOUTES les protections.
   2. LE CLASSEUR SE POSE DEJA CHEZ SUPABASE -- les deux scripts qui existent
      (rapatrier_repartition_classeur.py, poser_charge_classeur_2026-11-04.py)
      fabriquent du `insert into public....`. Le projet a tranche par la pratique.
   3. UN SEUL EMETTEUR : la marque est ecrite dans la MEME instruction que la ligne,
      donc aucune fenetre ou une ligne vivrait la-haut sans sa marque -- et dans
      cette fenetre, le filet du worker lui collerait un numero Hektor FAUX.
```

### ⭐ CE QUI PROTEGE DEJA CES LIGNES, SANS RIEN AJOUTER (mesure du 15/11)

```
   refresh_ledger est DELETE-NEVER : une ligne non revue est marquee, pas supprimee
   le marquage present_in_hektor=0 a pour PREMIERE garde app_affaire_id < PLAGE
      -> la plage app n'est pas marquee, EN LOCAL AUSSI
   le seul DELETE local EXIGE un numero Hektor (« on ne supprime pas a l'aveugle »)
   le push se resout sur la CLE PRIMAIRE app_affaire_id, des deux cotes
   l'index unique Hektor est PARTIEL (WHERE hektor_affaire_id IS NOT NULL) :
      une ligne sans numero ne peut pas entrer en collision, ni ici ni la-haut
   la doublure est RECREEE chaque nuit (DROP + CREATE d'apres un select=* chez
      Supabase) -> elle recevra `transaction_origine` toute seule
```

### CE QUI A ETE POSE

```
   (b) transaction_origine dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS   ✅
   (c) transaction_origine dans la liste locale `for neuve in (...)` ✅
   recopie_app_seule_active()                  l'interrupteur, ETEINT par defaut
   recopier_ce_que_hektor_ne_rendra_jamais()   la recopie, AUCUN appel reseau
   l'appel : APRES le push (le 1er passage n'ecrit rien chez Supabase)
             AVANT la redescente (un seul chemin pour les colonnes de classe A)
   PLAFOND_RECOPIE_APP_SEULE = 500 -- au-dela, REFUS ecrit, rien n'entre
   phase2/sync/test_recopie_app_seule.py              39/39 verts
   phase2/checks/retour_arriere_recopie_app_seule.py  A BLANC par defaut
```

### ⛔⛔ ET LES EPREUVES ONT TROUVE DEUX DEFAUTS REELS, DONT UN GRAVE

```
   1. present_in_hektor est NOT NULL en local : un vide dans la doublure faisait
      LEVER l'INSERT -- donc TOMBER L'ETAPE DU RUN. Trouve par le TEMOIN DU TEMOIN,
      pas par l'epreuve (les 30 controles etaient verts).
      -> corrige : les colonnes NOT NULL sont LUES dans le DDL, une ligne incomplete
         est ECARTEE, COMPTEE et NOMMEE, et le run continue.
      ⛔ ET ON NE COMBLE PAS avec le defaut du DDL : il vaut 1, « presente chez
        Hektor » -- un MENSONGE pour une ligne du classeur.
   2. ⛔⛔ SQLite NE MARQUE PAS « notnull » UNE COLONNE INTEGER PRIMARY KEY (c'est un
      alias de rowid). Sans garde posee A LA MAIN, une ligne sans numero n'etait pas
      refusee : SQLite lui en INVENTAIT un. Le temoin l'a prouve -- une transaction
      est entree sous le numero **1**. C'etait une SECONDE SERIE de numeros frappee
      en local, exactement la faute contre laquelle toute cette piece est ecrite.
```

### ✅⭐ ET L'ESSAI SUR LES VRAIES DONNEES EST FAIT — 15/11, 15/15, SANS RIEN TOUCHER

`phase2/checks/essai_reel_sur_copie_26bis.py`. La base reelle est ouverte en
**`mode=ro` + `query_only`** et recopiee dans une base NEUVE batie avec le **vrai DDL**
(contraintes et index compris) ; tout se passe dans un fichier temporaire. **LE CRITERE
EST ECRIT DANS LE FICHIER, AVANT le resultat** — sinon on juge apres coup.

```
   PASSAGE 1  l etat d AUJOURD HUI (49 colonnes, personne n a la marque)
              1 recopiee = 1001424 . 0 ecartee . temoin 0 -> 1 . genre et
              annonce suivis (offre / 28351)
   PASSAGE 2  l etat de LA NUIT PROCHAINE (50 colonnes, la marque est la)
              1 recopiee . la colonne entre . les 3 obligatoires sont lues
   PASSAGE 3  LA NUIT D APRES : 0 recopiee, 0 candidate, aucun doublon
   ET DANS LES TROIS : 340 de la plage AVEC numero + 30 817 hors plage,
              INCHANGES. C est le controle qui compte le plus.
```

⚠ Une imprecision de mon critere, dite : au passage 1 j attendais que le code SIGNALE la
colonne manquante. Il ne le fait pas, et c est juste — le message ne sort que si le LOCAL
a une colonne que la doublure n a pas. Ici personne ne l a : il n y a rien a signaler.

### ✅ ELLE EST ALLUMEE -- 15/11/2026 a 17:46, SUR SON « GO »

```
   1. ✅ ALLUME : APP_RECOPIE_APP_SEULE=1 pose en fin de .env (HORS GIT), avec
      son bloc de commentaire (pourquoi, retour arriere, quoi juger au matin).
      Sauvegarde datee AVANT : .env.avant_recopie_app_seule_20261115_174624
      (13 227 octets, md5 875f0ab05959d83e3f4be66ff0c8bdcb -- identique a
       l'original, et le debut du fichier est INTACT apres l'ajout).
      Fins de ligne : 0 CRLF avant, 0 CRLF apres -- le fichier est en LF seuls.
      ⭐ LE CODE LE LIT, DANS LES DEUX SENS : recopie_app_seule_active() rend
        True ; la meme fonction avec la valeur a 0 rend False ; rebranchee, True.
      ⭐ Et l'epreuve reste a 39/39 AVEC l'interrupteur allume dans .env
        (le controle 16c juge justement « elle ne tourne QUE si allume »).
      ⭐⭐ L'ETAT DE DEPART EST MESURE ET ECRIT, pour que demain se juge contre
        un chiffre et non contre un souvenir :
            a retirer 0  .  plage AVEC numero 340  .  hors plage 30 817
        Demain matin, ce doit etre  1  .  340  .  30 817  -- et rien d'autre.
   2. la nuit suivante fait tout dans l'ordre, sans rien lancer a part :
        refresh cree la colonne locale . push . LA RECOPIE . la redescente
   3. JUGER : le compte rendu porte `recopie_app_seule` -- recopiees 1, cles
      [1001424], le temoin passe de 0 a 1, et AUCUNE ecartee
   4. retour arriere : python -X utf8 phase2/checks/retour_arriere_recopie_app_seule.py
      (a blanc d'abord ; il sauvegarde la base et JUGE SA PART)
```

⚠ **ET LE RISQUE QUI RESTE, A SURVEILLER AU MOMENT DES 241** : l'upsert du push
**remplace** la ligne chez Supabase. Toute colonne posee la-haut APRES la recopie, et qui
n'est pas dans la liste interdite, serait effacee a la nuit suivante (lecon du 07/09). Si
un script du classeur doit encore enrichir ces lignes (honoraires, repartition, avis), ces
colonnes-la doivent entrer dans la liste **avant** d'etre remplies.


### ⚠⚠ LES ALERTES DU MONITEUR, LUES LE 15/11 A 17:00 — ET UN DEFAUT TROUVE

Releve de 16:48, **83 lignes mesurees, 76 vertes**. Les sept autres, nommees :

```
   CRITICAL 3, MAIS UNE SEULE CAUSE
     scheduledtasks:gti_descente   « GTI Descente : dernier resultat 1 »
     scheduledtasks                l'agregat  « 11 suivies, 1 en anomalie »
     monitor.summary               le resume
   WARNING 3
     data.transaction_disparue           1 -- offre . 28351 . 2006-04-01
     data.affaire_sans_numero_hektor     1
     data.negociateur_registre_signal   13 changements de la nuit du 14/11
```

**LE ROUGE EST A NOUS, ET C'EST DU CHANTIER CLASSEUR.** La descente du 15/11 sort en
code 1 a cause de **DEUX TABLES DE GEL DU 13/11** qu'elle n'a pas pu recopier en entier :

```
   app_affaire_repartition_avant_classeur_20261113   7 344 lues / 7 346 attendues   (-2)
   app_classeur_lien_avant_regel_20261113           12 413 lues / 12 422 attendues   (-9)
   -> « l'ancienne copie est conservee » : le code est prudent, rien n'est abime
   -> 1 453 680 lignes descendues dans 194 tables sur 196 : TOUT LE RESTE EST PASSE
```

⭐ **ET LA TABLE VITALE POUR LA NUIT EST PASSEE** : `app_affaire_ledger -> __sb` figure
dans la liste des doublures descendues, elle n'est PAS dans les deux echecs. La recopie
de 26bis trouvera donc une doublure a jour (mesure : 341 lignes, dont A2 sans numero).

✅⭐⭐ **LA CAUSE EST TROUVEE ET LE CORRECTIF EST POSE — 15/11, 20/20.** Ce n'est pas un
hasard sur deux tables, c'est **mecanique**, et le tort est de moi : une table creee par
`CREATE TABLE ... AS SELECT` **n'a aucune cle primaire**. Mesure chez Supabase :

```
   app_classeur_lien_avant_regel_20261113       AUCUNE cle   1re colonne ligne_classeur
                                                12 422 lignes pour 4 688 valeurs
   app_affaire_repartition_avant_classeur_...   AUCUNE cle   1re colonne app_chaine_id
                                                 7 346 lignes pour 3 673 valeurs
   app_affaire_ledger                           cle app_affaire_id  -> elle descend juste
```

`pull_from_supabase.py` l. 301 : `cle = cles[0] if cles else colonnes[0]`. Sans cle
primaire, le parcours se fait donc **sur la premiere colonne**, qui se repete, avec un
`gt` STRICT -- la frontiere d'une page tombe au milieu d'une valeur et **ce qui reste de
cette valeur est saute**. C'est le defaut du 15/09, a l'identique, par une autre porte.

⚠ **ET LE RATTRAPAGE EXISTANT NE POUVAIT PAS LES SAUVER** : il ne joue que sous
`RELECTURE_ENTIERE_MAX = 5 000`. 7 346 et 12 422 sont **au-dessus**, d'ou l'erreur levee.

**LE CORRECTIF, DEUX LIGNES** (`phase2/sync/pull_from_supabase.py`) : le parcours par rang
d'emblee **aussi quand il n'y a AUCUNE cle**, exactement comme pour une cle composite --
`composite = (not cles) or len(cles) > 1`, et `ordre_cle = list(cles) if cles else
list(columns)`. Le journal le **dit** desormais (« AUCUNE cle primaire -- ordre sur ses
N colonnes ») au lieu d'annoncer « cle composite ».

⭐ **MESURE AVANT DE L'ETENDRE**, parce que l'offset n'a ici aucun index a suivre :
**36 tables sans cle primaire, 109 201 lignes en tout**, la plus grosse a 31 151 lignes
(32 pages) et au plus 26 colonnes. Negligeable a ces volumes.
⛔ **ET ON NE RETIRE PAS CES GELS** pour faire taire l'alarme : une sauvegarde datee avant
un geste destructif est une regle du projet. Le tort etait de les creer SANS cle primaire.

**L'EPREUVE** : `phase2/sync/test_descente_sans_cle_primaire.py`, **20/20**, sans reseau --
un faux lecteur qui imite PostgREST (`gt` pour la valeur, `offset` + ordre total pour le
rang). Elle porte les deux temoins inverses, et « on ne casse rien » pour une cle simple
et pour une cle composite.

⛔⛔ **DEUX FOIS MON CRITERE ETAIT FAUX, ET JE LE DIS** :
```
   1. LES TROIS TEMOINS INVERSES ETAIENT VERTS A TORT a la premiere ecriture : avec
      4 lignes par valeur et des pages de 100, chaque page tombait PILE sur une
      frontiere de valeur -- le parcours par valeur ne sautait rien. Il faut que la
      taille de page NE SOIT PAS un multiple des lignes par valeur (3 et 100).
   2. J'ATTENDAIS UNE COPIE REFUSEE sous le plafond. C'est le code qui avait raison :
      le rattrapage joue et SAUVE la table (« 1178/1200 -- relecture par rang »). Donc
      sous 5 000 on ne perdait rien, on payait une SECONDE LECTURE COMPLETE chaque
      nuit, en silence. C'est ca que le correctif economise ; la vraie perte etait
      au-dela du plafond.
```

⭐ **AUCUN EFFET SUR LA NUIT QUI VIENT** : la descente passe a 07:45, soit APRES le run
de 05:00. La recopie de 26bis travaillera donc sur la doublure descendue **aujourd'hui a
07:11** -- celle ou `app_affaire_ledger` est passee sans encombre. Rien a redemarrer : la
descente est une tache planifiee, elle prend le fichier tel quel.

⚠ **SIGNALE, HORS PERIMETRE** : `phase2/checks/test_un_seul_verrou.py` est **rouge, et il
l'etait DEJA avant ce correctif** -- mesure par restauration de la version HEAD puis
relance (code 1 avant, code 1 apres, md5 du fichier verifie identique apres remise en
place). Son seul echec est son propre temoin historique : « la version d'avant visait un
AUTRE fichier -- elle visait deja le bon ». Un essai qui crie sur son passe.

⚠ **CE QUE LE ROUGE COUTAIT** : tant qu'il sonne, la sonde dit « 1 anomalie »
chaque jour et **un VRAI echec de descente ne se verrait plus** -- c'est exactement le
defaut contre lequel le code de sortie a ete pose (commentaire de `run_descente.ps1` :
« un exit 0 menteur avait cache 18 jours de lots en echec »). A traiter : soit comprendre
les 2 et 9 lignes manquantes, soit **retirer ces deux gels** -- ce sont des echafaudages
du 13/11, et le chantier dit deja que le gel EST un echafaudage.

**LES ORANGE : DEUX SUR TROIS SONT NOTRE COBAYE.** Mesure sur la doublure (miroir de
Supabase) : la ligne qui declenche `data.transaction_disparue` est **1001424, l'essai A2**
-- `offre`, annonce `28351`, `present_in_hektor = 0`, `last_seen_at` de cette nuit. Et
`data.affaire_sans_numero_hektor` est la **meme ligne** vue par un autre lecteur. Le
troisieme orange (registre des negociateurs) n'a rien a voir avec ce chantier.

### ⛔⛔ LE DEFAUT, ET IL EST DE MOI : J'AI GARDE UNE PORTE SUR DEUX

```
   data.affaire_sans_numero_hektor  lit la VUE app_affaires_sans_numero_hektor
                                    -> la garde transaction_origine Y EST (patch du 15/11)
   data.transaction_disparue        lit la TABLE app_affaire_ledger EN DIRECT, par
                                    present_in_hektor=is.false + last_seen_at>=48h
                                    -> AUCUNE garde sur transaction_origine
```

⭐⭐ **C'est la lecon du projet qui mord : « une exclusion a part doit etre appelee par
CHAQUE porte ».** Je croyais la plage app a l'abri (le marquage `present_in_hektor=0` a
pour premiere garde `app_affaire_id < PLAGE_RESERVEE_APP`). **La mesure dit le contraire
pour cette ligne** : A2 est dans la plage app ET porte `present_in_hektor = 0`. Je ne sais
pas encore par quel chemin -- mais le fait est la, et il suffit.

⚠ **CONSEQUENCE CHIFFREE** : si les 241 entrent avec `present_in_hektor = 0` comme A2,
cette sentinelle criera **241 fois**, chaque nuit, pendant 48 h de fenetre glissante.
⛔ **A TRAITER AVANT LES 241** -- pas avant cette nuit : A2 crie deja, un de plus ou de
moins ne change rien, et la nuit qui vient ne pose aucune des 241.

### ⛔⛔⛔ L'AUDIT DU SOIR (15/11, demande par Frederic) — DEUX DANGERS TROUVES

Il demandait « etre sur que tout se passe bien demain matin ». L'audit, en lecture seule,
a trouve **deux choses qui pouvaient casser la nuit**, et les deux venaient de MOI.

#### ⛔ DANGER 1 — LA PIECE 4 POUVAIT FAIRE TOMBER LE RUN ENTIER

`run_full_pipeline.ps1` l. 988 appelle `affaire_ledger.py` par **`Invoke-Step`**, pas
`Invoke-OptionalStep`. Une exception dans `main()` fait donc tomber **tout ce qui suit**
dans la nuit. Et le precedent est ecrit **vingt lignes au-dessus, dans ce meme fichier** :

```
   « Le run du 02/09 a plante a l'etape suivante : Supabase REST error 409 -- et TOUT
     CE QUI SUIT n'a pas tourne, dont le push principal : l'app est restee 18 h en
     arriere sans que rien ne le dise. »
```

Ma recopie etait placee **juste avant** `redescendre_ce_que_l_app_possede` (ancienne,
essentielle) et **sans aucun try**. Du code neuf et facultatif pouvait emporter le reste.

✅ **CORRIGE** : l'appel est entoure d'un `try/except` qui ecrit l'echec, en dit le
nombre de lignes deja entrees (`deja_entrees`), fait un `rollback` et **laisse le run
continuer**. ⭐ Le rollback est sur : la fonction ne fait qu'**UN** `INSERT ... SELECT`
suivi d'**UN** `commit`. 5 controles neufs (17 → 17e), l'epreuve passe de 39 a **44/44**.

#### ⛔⛔ DANGER 2 — MON CORRECTIF DE LA DESCENTE ETAIT DANGEREUX. JE L'AI RETIRE.

J'avais fait partir le parcours **par rang d'emblee des qu'il n'y a pas de cle primaire**.
C'etait faux, et la mesure le prouve : **les VUES n'ont pas de cle primaire non plus.**

```
   51 vues existent chez Supabase ; VUES_NON_DESCENDUES n'en connait que 41
   -> 10 vues nees depuis le 12/10 DESCENDENT ENCORE (confirme par --dry-run :
      237 exposees, 41 ecartees, 196 a descendre)
   et parmi elles :
      app_v_mandat_statut   24 596 lignes . 76 colonnes . 1re colonne UNIQUE
                            -> elle descend PARFAITEMENT par valeur aujourd'hui
```

Mon correctif l'aurait fait passer a **25 pages d'offset avec un ORDER BY sur 76
colonnes, sur une VUE que Postgres recalcule a chaque page**. C'est mot pour mot ce qui a
mis l'instance par terre le **21/08** (statement timeout), le **15/09** (503 pour toute
l'agence, 07:30 → 09:15) et le **12/10** (08:44 → 09:00).

✅ **LE BON CORRECTIF, ET IL EST PLUS PETIT** : `RELECTURE_ENTIERE_MAX : 5 000 -> 15 000`.
Le rattrapage par rang savait **deja** reparer ce defaut ; il ne jouait pas parce que les
deux gels sont au-dessus de 5 000. Et ce plafond **ne touche que ce qui echoue deja** :

```
   196 tables descendues . 194 passent . 2 echouent -> 2 SEULES tables concernees
   une table qui descend bien ne passe JAMAIS par le rattrapage : chemin inchange
   15 000 couvre les deux gels (12 422 au plus) et laisse app_v_mandat_statut
      (24 596) HORS D'ATTEINTE -- si elle echouait un jour, elle serait REFUSEE
      bruyamment au lieu d'etre relue par offset
```

⭐ **L'epreuve porte desormais cette garde** : son controle 3 verifie qu'une grosse table
sans cle dont la 1re colonne est unique descend **par valeur et JAMAIS par rang**.
`test_descente_sans_cle_primaire.py` : **19/19**.

#### ⛔ ET JE CORRIGE MON PROPRE DANGER 2 : IL ETAIT SURESTIME

J'ai ecrit ci-dessus que mon correctif aurait mis `app_v_mandat_statut` sur l'offset. **La
mesure dit non**, et elle est allee chercher la bonne source -- **ce que POSTGREST declare**,
pas `pg_index` :

```
   app_v_mandat_statut   76 col | PK DECLAREE register_row_id | parcours sur register_row_id
```

PostgREST **lui declare une cle primaire** (une vue simplement modifiable en recoit une).
Mon correctif ne l'aurait donc **pas** touchee. Les 10 vues qui descendent encore, mesurees
une a une : **6 ont une PK declaree**, et les **4 qui n'en ont pas sont minuscules** --
`app_filter_catalog_registre` 93 lignes, `app_v_contact_modif_ecarts` 5,
`app_v_annonce_modif_ecarts` 0, `app_v_affaire_partie_ecarts` 0. Une seule page chacune :
aucune pagination profonde, donc aucun risque de 503.

⭐⭐ **MA DECISION RESTE LA MEME, MAIS POUR UNE RAISON PLUS MODESTE** -- et c'est elle qu'il
faut retenir :

```
   mon correctif aurait change le chemin de 40 tables/vues sans PK declaree,
      dont app_etiquette_avant_repose_20261112 : 31 151 lignes, QUI DESCEND BIEN
      aujourd'hui (sa 1re colonne est unique) -> 32 pages d'offset sur une table
      SANS INDEX, pour rien.
   le plafond ne change le chemin de RIEN qui marche : 194 tables sur 196 intactes,
      exactement les 2 en echec sont visees, et il se defait d'un chiffre.
```

⚠ **Et il a un bon effet de bord mesure** : ces 4 petites vues sans PK, si elles
grossissaient au-dela de 1 000 lignes, perdraient des lignes au parcours par valeur. Sous
15 000, le rattrapage les sauvera -- avant, au-dela de 5 000, elles auraient ete refusees.

⛔ **LA LECON, ET ELLE EST DURE** : j'ai ecrit « mesure avant de l'etendre » dans le
commentaire de mon propre correctif, et j'avais mesure **la mauvaise chose** (`pg_index` au
lieu du schema de l'API). Une mesure qui ne regarde pas la source dont le code se sert ne
mesure rien. ⭐ Le correctif retire restait le mauvais choix, mais je l'ai d'abord condamne
sur un argument faux -- et un argument faux, meme quand il mene a la bonne decision, ne
compte pas comme une preuve.

#### ✅ ET UNE ERREUR QUE J'AVAIS ECRITE CE SOIR, CORRIGEE

J'avais dit que la recopie travaillerait sur la doublure descendue a 07:11. **C'est faux** :
`run_full_pipeline.ps1` l. 979 descend **lui-meme** `app_affaire_ledger` juste avant
d'appeler le ledger (etape **non bloquante**, posee le 02/09 pour cette raison exacte).
La recopie verra donc une doublure **fraiche de cette nuit**. C'est mieux, pas pire.
⭐ Et l'appel est `--refresh --push` : la colonne locale est donc creee **dans le meme
passage**, avant le push et avant la recopie -- l'etat du « passage 2 » de l'essai.

#### ✅ LES WORKERS : MESURES, ET ILS NE SONT PAS CONCERNES

```
   les 4 services              Running
   leurs processus             nes le 15/11 a 14:22:14-16 (Win32_Process.CreationDate)
   le code du worker           ecrit a 13:05:56  -> ils portent bien la piece 3
   rien n'a redemarre depuis   (les memes 4 processus)
   la file                     VIDE : 0 pending, 0 running
   temoin positif              4 travaux depuis 14:22, tous `done`, 0 erreur
```

⚠ **Ni la piece 4 ni le correctif de la descente ne touchent le worker** : ce sont deux
fichiers Python du run. Le seul changement du worker aujourd'hui est la piece 3, **deja en
service et deja prouvee**. Il n'y a donc **rien a redemarrer** pour demain.

#### ✅ L'ETAT CHEZ SUPABASE, MESURE CE SOIR

```
   transaction_origine    text, nullable, aucun defaut        0 ligne marquee / 31 158
   plage app              340 avec numero Hektor  .  1 SANS (le cobaye 1001424)
   hors plage sans numero 0
   la vue de la sentinelle app_affaires_sans_numero_hektor CITE transaction_origine,
      et elle voit 1 ligne -- le cobaye, qui est DEMARQUE expres
```

#### ✅ LES 7 ESSAIS ROUGES : AUCUN N'EST DE MOI (mesure, pas supposition)

Les 16 essais qui citent `affaire_ledger` ou `pull_from_supabase` ont ete lances **deux
fois** : avec mes changements, puis avec la version **`f3a4e85`** (avant la piece 4) remise
en place, puis les miens remis et **l'empreinte md5 verifiee identique** (methode du 15/11
au matin). 9 sont verts. Les 7 autres sont **exactement dans le meme etat des deux cotes** :

```
   test_alignement_suppression            avant 1 / apres 1
   test_mandat_notre_numero_sur_copie     avant 2 / apres 2   (2 = « pas pu mesurer »)
   test_notaires_notre_numero             avant 1 / apres 1
   test_personnes_deux_numeros            avant 1 / apres 1
   test_r2_attente                        avant 1 / apres 1
   test_un_seul_verrou                    avant 1 / apres 1
   test_vendeurs_deux_numeros_sur_copie   avant 2 / apres 2
```

⚠ **Ils criaient donc deja, et ce n'est pas une bonne nouvelle en soi** : c'est la lecon
« un essai qui crie tous les jours n'est plus un essai ». `test_un_seul_verrou` echoue sur
son propre temoin historique (« la version d'avant visait un AUTRE fichier -- elle visait
deja le bon »). Les autres n'ont pas ete ouverts : **hors perimetre**, a reprendre s'il le
demande. Ce qui compte pour cette nuit : **mes changements n'en ont casse aucun**.

#### ✅ L'ETAT FINAL, EPROUVE

```
   test_recopie_app_seule.py           44/44   (39 + les 5 du garde-fou)
   test_descente_sans_cle_primaire.py  19/19   (dont la garde des vues)
   essai_reel_sur_copie_26bis.py       15/15   sur les VRAIES lignes, en lecture seule
   fins de ligne                       0 CRLF dans les deux fichiers (ils sont en LF)
```

#### ⏰ LE PROGRAMME DE LA NUIT, ET CE QU'ON JUGE AU MATIN

```
   04:00  GTI Quotidien   -> ... -> doublure du ledger (non bloquante, ~87 s)
                              -> affaire ledger refresh+push (~103 s hier)
                                   . refresh : cree transaction_origine en local
                                   . push    : 31 157 lignes hier
                                   . LA RECOPIE (26bis)  <- le geste neuf
                                   . redescente des colonnes de classe A
   06:45  GTI Descente    -> les 196 tables, dont les 2 gels que le plafond repare
   08:00  GTI Sauvegarde
```

**Le critere du matin, en deux commandes :**

```
   python -X utf8 phase2/checks/retour_arriere_recopie_app_seule.py
      -> doit dire : 1 a retirer . 340 de la plage AVEC numero . 30 817 hors plage
   et dans le compte rendu du run, cle `recopie_app_seule` :
      recopiees 1 . cles [1001424] . temoin 0 -> 1 . AUCUNE ecartee
      ⛔ si la cle porte `echec`, le garde-fou a joue : le run a continue, et
        `deja_entrees` dit ce qui est entre. RIEN n'est casse, on lit l'erreur.
   et la descente ne doit PLUS sortir en code 1 (les 2 gels passent par rattrapage)
```

### ✅✅✅ LE VERDICT DU MATIN — 16/11/2026, LES TROIS CRITERES SONT TENUS

**1. LE RUN** — demarre 04:00:01, termine **06:42:12**, `Pipeline finished successfully`,
code **0**. Toutes les etapes en DONE, aucune en FAIL.

**2. LA RECOPIE (26bis)** — le journal, a 06:17 :

```
   26bis : 1 transaction(s) que Hektor ne rendra jamais sont entrees dans le
           registre local (50 colonnes) -- 1001424
```

et son compte rendu, critere par critere :

```
   "actif": true          <- l'interrupteur est bien lu
   "candidates": 1, "recopiees": 1, "cles": [1001424]
   "plage_sans_numero_avant": 0  ->  "..._apres": 1      <- le temoin a bascule
   "colonnes_recopiees": 50
   "rows_ecartees": 0,  "cles_ecartees": []               <- aucune ecartee
```

⭐ **La cle `echec` n'apparait pas** : le garde-fou pose la veille au soir n'a pas eu a
jouer. Et aucun `UnicodeEncodeError` dans tout le journal.

**3. LE RETOUR ARRIERE, joue a blanc** — il rend **exactement** les trois chiffres ecrits
la veille AVANT la nuit :

```
   a retirer (plage app, sans numero Hektor) : 1
      1001424
   VOISINES a ne pas toucher : 340 de la plage AVEC numero, 30817 hors plage
```

⭐⭐ **Les voisines n'ont pas bouge d'une ligne.** La recopie n'a touche que sa cible, et
le geste inverse est pret (a blanc par defaut, sauvegarde datee avant d'ecrire).

#### ✅ ET LA DESCENTE EST SORTIE EN CODE 0 (07:11:37) — le correctif a mordu

Le journal montre le mecanisme exactement comme l'essai l'avait predit :

```
   app_affaire_repartition_avant_classeur_20261113 : 7344/7346 -- relecture par rang
   [  4/196] app_affaire_repartition_avant_classeur_20261113     7346 lignes
   app_classeur_lien_avant_regel_20261113 : 12413/12422 -- relecture par rang
   [  8/196] app_classeur_lien_avant_regel_20261113            12422 lignes
```

Le parcours par valeur ramene les **memes** 7 344 que la veille, **puis** le rattrapage
par rang complete. **196 tables, 0 en echec.**

⭐ **LE TEMOIN DE NON-REGRESSION EST DANS LE JOURNAL DE LA VEILLE** : une 3e table passe
aussi par le rattrapage (`app_securite_droits_avant_20261008`, 1 000/2 546) -- et elle y
**etait deja le 15/11**, parce qu'elle est sous l'ANCIEN plafond. Le plafond releve n'a
donc touche **que les 2 tables visees** : **194/196 intactes**, comme annonce.

**Le moniteur de 06:48** ecrit de lui-meme `Retour a la normale : gti_descente` et
`GTI monitor summary: 0 critical, 3 warning, 0 unknown` (son `etat_precedent` etait
`critical`). ⚠ Ce releve est tombe PENDANT la descente, il ne juge donc pas son code de
sortie : **la preuve est la mesure directe du code 0 a 07:11:37**. Le releve de **08:48**
sera la confirmation avec la tache terminee.

#### ⭐⭐ UN RISQUE QUE J'AVAIS SIGNALE LA VEILLE ETAIT DEJA COUVERT PAR LE CODE

J'avais ecrit qu'il fallait surveiller ceci : l'upsert du push **remplace** la ligne, donc
la marque `transaction_origine` posee chez Supabase pourrait etre effacee la nuit suivante.
**C'est faux, et je ne l'avais pas mesure avant de l'ecrire.**

La colonne est dans `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` (`affaire_ledger.py:3137`), avec
ce commentaire deja ecrit le 15/11 : « ⛔ UN SEUL EMETTEUR, ET C'EST SUPABASE ». Et la
redescente redescend **exactement cette meme liste** (`colonnes =
list(COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS)`, l. 3002). La marque est donc protegee **dans les
deux sens** : le push ne peut pas l'effacer, la redescente la ramene.

⚠ **Et la colonne est vide sur les 31 158 lignes locales : c'est l'etat NORMAL**, pas un
defaut. Le local ne l'ecrit jamais, il la **recoit**, et aucune ligne n'est encore marquee
la-haut. Le cobaye A2 n'est volontairement **pas** marque -- c'est ecrit noir sur blanc a
`affaire_ledger.py:2798` : « la marque dit d'ou vient une ligne, elle ne decide pas qui a
le droit d'entrer ».

#### ⚠ LES 3 ORANGE DU MONITEUR, ET AUCUN N'A AUGMENTE

```
   data.transaction_disparue        1  -- offre . 28351 . 2006-04-01   <- LE COBAYE A2
   data.affaire_sans_numero_hektor  1                                  <- LE COBAYE A2
   data.negociateur_registre_signal 13 -- 2026-11-14 . personne        <- AUTRE SUJET
```

Les deux premieres sont **le meme cobaye vu par deux lecteurs differents** : elles sont la
expres et s'eteindront quand on le retirera. La troisieme ne concerne pas ce chantier.

⛔⛔ **MAIS LA 1re N'A AUCUNE GARDE, ET C'EST LE PROCHAIN GESTE.**
`data.affaire_sans_numero_hektor` lit la **VUE** `app_affaires_sans_numero_hektor`, ou la
garde `transaction_origine` est posee. `data.transaction_disparue` lit la **TABLE en
direct** (`present_in_hektor=is.false` + `last_seen_at>=48h`) et n'a **rien**. Avec les
241, elle crierait **241 fois par nuit**. A reparer **AVANT** de poser les 241.

### ⬜ CE QUI RESTE, DANS L'ORDRE CONTRAINT

```
 3  LE FILET DU WORKER  ✅✅ EN SERVICE le 15/11 a 14:22 (commit 70e947d)
                        les 4 processus nes APRES le code -- preuve par leur heure
                        16/16 verts dans Console/test_seconde_preuve.js, dont 3 neufs
                        ⭐ c est la DERNIERE piece avant 26bis : plus rien ne bloque 4
 4  26bis-TRANSACTIONS  ✅✅✅ FAITE, ALLUMEE ET JUGEE EN REEL -- PLUS RIEN A FAIRE ICI
                        44/44 hors ligne . allumee le 15/11 a 17:46 . jugee le 16/11
                        au matin : recopiees 1, temoin 0->1, 0 ecartee, aucun `echec`
                        retour arriere : 1 . 340 . 30 817, EXACTEMENT comme predit
                        ⭐ la marque est protegee dans les deux sens (le push ne
                          l'envoie pas, la redescente la ramene) -- mesure le 16/11
 4bis LA GARDE DE LA 2e ⛔⛔ LE PROCHAIN GESTE, ET IL PASSE AVANT LES 241
     SENTINELLE         `data.transaction_disparue` lit la TABLE en direct, SANS garde
                        `transaction_origine` -- avec les 241 elle crierait 241 fois
                        par nuit. Sa soeur `data.affaire_sans_numero_hektor` a la
                        garde (elle lit la VUE) : c'est le patron a recopier.
 5  retirer l essai A2  seulement apres 3, 4 et 4bis
 6  LES 241             marquees `classeur` DES L'INSERT, jamais apres
```







### PHASE B — LES EMPLACEMENTS ET LES GARDIENS

```
B1 ⬜  CREER LES 6 COLONNES MANQUANTES (9 = 3 qui existent + 6) :
         Y Vente Reglee . AA N0 de facture      -> colonnes de CLASSE A
         AH Avis a envoyer . AI Commentaire Avis . AJ Avis envoye -> table a part,
            cle id_unique (aucune colonne « avis » n'existe dans TOUTE la base)
         C numero_mandat_app -> ⛔ PREALABLE DU 29/10 JAMAIS FAIT. `numero_mandat`
            est de CLASSE C : une ecriture y est EFFACEE au run suivant.
       ⭐ Les carnets n'ont AUCUNE contrainte CHECK sur le nom d'un champ.
B2 ⬜  SENTINELLE DES 85 LIGNES NON RATTACHEES -- sinon elles ne recevront jamais
       rien et personne ne le verra.
B3 ⬜  SENTINELLE DES CONDITIONS ET NOTES ORPHELINES (5 et 6 aujourd'hui). Le
       modele existe : `app_v_repartition_orpheline`. A POSER AVANT d'ecrire, sinon
       le defaut se multiplie par 241.
```

### PHASE C — POSER, DU PLUS SUR AU PLUS DELICAT

```
C1 ⬜  3.2bis LA CHARGE : 16 lignes, patch DEJA ECRIT et non joue
       (patch_charge_classeur_2026-11-14_DONNEES.sql). + LOT 2 : 25 lignes de
       confiance « a valider »/« bonne » -> SA DECISION (je ne les poserais pas).
C2 ⬜  3.3 LOT A : 303 commissions (1 886 204 EUR, dont 77 lignes 2026 pour
       539 070 EUR) + 10 dates de case vide. En CLASSE A. Les 24 « zeros deguises »
       (217 250 EUR) comptent comme des vides -- un zero n'est pas une saisie.
C3 ⬜  3.3ter Z : 896 dates d'annulation dans date_annulation_app, DEJA PRETE.
       En face : 3 705 affaires `cancelled`/`refused` qui ne disent pas QUAND.
       ⭐ ET LES MOTIFS : F du classeur en porte (retractation 129, pret refuse
       107) -> motif_annulation_app a une source, contrairement a ce que dit son
       commentaire dans le code.
C4 ⬜  F ET G dans leurs cases existantes (apres A1, qui dira le volume) :
       F -> app_affaire_condition, G -> app_affaire_note, origine « classeur ».
       ⛔ F et G se reprennent EN BLOC, SANS INTERPRETER -- sa consigne.
C5 ⬜  3.3 LOT B : **215 creations franches** -- 144 offres + 62 compromis
       + 9 ventes (5 a la meme date d'acte, 2 sans date, 2 sans compromis).
       Dans la plage app, sans numero Hektor. APRES A2 et A4.
C6 ⬜  3.3 LOT C : **26 ventes** dont notre compromis porte DEJA une autre date
       d'acte. ⛔ C'est un CONFLIT, pas un vide -> SA DECISION.
C7 ⬜  3.3bis V « Vente Prevue » : 2 303 ecarts + 21, decidee « tout », on ecrase.
       ⭐ Arbitre INDEPENDANT (notre date de vente, qui vient de Hektor) : le
       classeur tombe plus pres du reel 1 402 fois contre 714. -> SA DECISION.
       ⚠ Ne jamais arbitrer V par W : les deux sortent du MEME classeur (accord
         circulaire -- l'erreur que j'ai faite et rattrapee le 15/11).
C8 ⬜  3.4 Y ET AA remplis : 3 735 + 3 719 valeurs, les DEUX plus gros postes du
       chantier, et les deux sans aucune case aujourd'hui. Apres B1 et A5.
C9 ⬜  3.5 AH AI AJ (apres B1) + C le numero de mandat (33 au classeur, ~9 utiles).
       ⚠ AH et AJ se contredisent sur 229 lignes -- a reprendre tels quels.
       ⚠ 33 numeros de mandat sont RECYCLES aux charges divergentes : un numero
         n'identifie pas un mandat (4 142 doublons).
C10 ⬜ AF PRIX : 161 ecarts -> on LISTE, on n'ecrit RIEN. Sa decision « comparer ».
```

### PHASE D — FERMER

```
D1 ⬜  1.5 LE RE-GEL ADDITIF : 6 lignes (4 « sure », 2 « a valider »). ⭐ Les deux
       cas de 1.4 sont RESOLUS par l'audit du 15/11 : leurs transactions n'existent
       pas chez Hektor -> on les cree CHEZ NOUS. ⛔ ADDITIF, on ne retouche aucun
       des 12 595 liens.
D2 ⬜  ETAPE 4 : 4.1 la porte sans ecran (une RPC qui APPELLE
       app_modifier_affaire_optimistic, jamais une copie) . 4.2 une affaire qu'il
       choisit . 4.3 la reprise complete LA NUIT (~2 a 3 h, arret sur conflit).
D3 ⬜  ETAPE 5 : **5.1 EST SON GESTE** -- lire les Apps Script du classeur, 10 min,
       et il BLOQUE P4. Puis 5.2 nos UUID dans la colonne affair_uuid
       (⛔ en filtrant les 14 chaines entierement mortes, via
       app_affaire_compte_encore -- et SANS RIEN retirer en base : 2 chaines sont
       MIXTES) . 5.3 le routeur.
```

### ⚠ LES RESERVES QUI RESTENT OUVERTES

```
les 26 ecarts de date a plus d'un mois, dont 15 sur ventes reglees
Nature 1 650 . Ville 1 646 . Notaire 1 373 . Agence 493  -> « RIEN » par decision
FRANCHINI Marjorie : dans l'annuaire, mais sa ligne de repartition non posee
les 12 numeros d'annonce trouves dans la colonne Mandat
les 31 mandats HEKTOR de vente absents du registre
les 3 biens encore vivants chez Hektor : 40318, 58979, 8494
R-A le frein Hektor PARTAGE (4 workers = 4 req/s) -- il a mordu les 27-28/10
R-B le balayage qui relance une commande morte depuis le carnet
```

### ÉTAPE 1 — fermer l'appariement *(P1)*

```
1.1 ✅ FAIT 12/11   l'apparieur repare : 4 691 / 4 786 reconnues (98,0 %)
                    sure 4 569 . bonne 11 . a valider 111 . aucune 95
                    temoins : 0 ligne perdue . 17 des 20 regressions revenues
                    ⭐ et 3 des 5 cibles changees S'ALIGNENT SUR LE GEL
1.2 ✅ FAIT 12/11   rapport_gel_tous_les_champs.py repare (premiere_proposition)
                    AMPLEUR MESUREE : 536 offres gelees avaient leur date deplacee
                    (306 par nos refus) -> le rapport annoncait 536 FAUX ecarts
                    sur « Offre Achat ». C'ETAIT UN PREREQUIS DE 3.1.
                    temoins : cas reel 14112 -> 2021-03-25 . refus seul -> None
                              8 formes degradees, aucune exception
1.3 ✅ FAIT 12/11   LA « SEULE DIVERGENCE » N'EXISTE PAS : pour 2dfa6ef3,
                    l'apparieur dit la chaine 30656 et le gel la transaction
                    30692 -- QUI EST DANS LA CHAINE 30656. Je comparais un
                    dossier a une transaction. La reserve tombe.
                    8Q3LHGZ4  2 pistes = SERRA et CHEVALIER, deux acheteurs du
                              bien 16831 -> le CLASSEUR melange deux affaires
                    I847SPN3  3 chaines ; le gel pointe le dossier 3699 (celui
                              laisse parmi les 38 impossibles)
                    UTLG66LE  3 chaines ; cause mesuree : sa date est 0000-00-00
1.4 ✅ MESURE 13/11  LES 2 « a valider » SONT INSTRUITES, et la reponse est LA MEME
                    pour les deux : LE BIEN EST JUSTE, MAIS LA TRANSACTION QUE LE
                    CLASSEUR DECRIT N'EXISTE PAS CHEZ HEKTOR.
                      ME6S0TR9 (ligne 3406) -> bien 42976, mandat 17260, Yssingeaux
                        classeur : TROY Pierre, 240 000, offre 06/11/2024,
                        compromis 06/01/2025, annulee 25/04/2025
                        Hektor : les transactions du bien sont a GIBERT puis PEPIER
                        ⚠ l'apparieur la rattachait a la chaine 24256 PAR LE NOM
                          « TROY » (rachel TROY, bien 47955, mandat 14338, 152 000) :
                          deux personnes, rien d'autre ne concorde. Il se trompe,
                          et sa confiance « a valider » etait juste.
                      6a259cce (ligne 4372) -> bien 11729, mandat 18040, Ambert
                        classeur : RIVOLLIER Remi, 160 350, offre 28/10/2025,
                        ANNULEE 30/10/2025 (« pas le financement »)
                        Hektor : le MEME JOUR, offre de VALENTIN CHANTELOUP au MEME
                        PRIX (160 350), qui aboutit a la vente du 03/04/2026
                        ⭐ le prix est EXACTEMENT egal et les vendeurs concordent :
                          le bien est certain, mais l'offre Rivollier n'a jamais ete
                          enregistree chez Hektor.
                    ⬜ LA DECISION RESTE A FREDERIC : on ne gele RIEN (le gel accroche
                      des TRANSACTIONS, pas des biens), ou on cree les transactions
                      manquantes chez Hektor.
1.5 ⬜ ACCORD       le RE-GEL ADDITIF des gains -- LISTE CONFIRMEE A JOUR le 13/11,
                    apres relance de l'apparieur ET avec le chainage de la regle D :
                      « sure »      3990 Z3DYDC4X -> 14111 . 4790 d7cbb8fa -> 30806
                                    4791 b7439331 -> 30809 . 4792 c67ccc6a -> 30808
                      « a valider » 3406 ME6S0TR9 . 4372 6a259cce  (voir 1.4)
                    ⛔ ADDITIF : on ne retouche aucun des 12 422 liens
⭐⭐ 1.5bis ✅ MESURE 13/11 -- LE CHAINAGE N'A RIEN CASSE DANS LE GEL, et c'est
                    desormais MESURE SUR SUPABASE (chainage a jour, regle D incluse),
                    pas seulement affirme :
                      liens du gel                              12 422
                      dont la TRANSACTION a disparu                  0
                      dont la transaction est HORS CHAINE            0
                      lignes dont les liens pointent 2 BIENS         0   ⭐
                      lignes eclatees sur 2 CHAINES                 32
                    ⭐ Les 32 sont sur LE MEME BIEN, deux chaines : c'est le chainage
                      qui coupe le dossier, pas le gel qui se trompe. C'est la famille
                      des « lignes a cheval » (33 le 12/11), deja expliquee.
                    ⭐ Et la sentinelle app_v_classeur_lien_casse n'en compte que 5,
                      tous « ABSENTE_CHEZ_HEKTOR » -- donc VOULUS (le carnet est a
                      nous), et vus pour la derniere fois en septembre/octobre.
                    ➡ IL N'Y A DONC PAS A REFAIRE TOURNER LE GEL. Ce qui etait prevu,
                      c'est le RE-GEL ADDITIF de 1.5, et sa liste est inchangee.
1.6 ✅ FAIT         git : apparier_classeur.py, les 14 apparier_v2_*.py, le rapport
                    A19 et le tableau des 175 sont TOUS SUIVIS (verifie le 13/11)
```

### ⭐⭐⭐ 1.7 — LE SECOND APPARIEMENT (v2), ET CE QU'IL APPORTE AU RE-GEL

> **C'est le travail que Frederic a demande la nuit du 12 au 13/11** : *« reprends
> ligne par ligne le classeur et cherche toi-meme les transactions correspondantes
> SANS utiliser la regle du gel […] ensuite fais-moi un rapport comparatif »*, afin
> d'**ameliorer le re-gel avec**. Rapport complet :
> `notice/A19_APPARIEUR_V2_CONTRE_LE_GEL_2026-11-13.md`.
> ⛔ **Cette section manquait au plan** : le 13/11 au matin, les dates d'offre du
> 11/11 ont pris toute la journee et le plan n'a pas ete mis a jour. C'est repare ici.

**La methode est VRAIMENT independante** : six familles de temoins (mandat, acquereur,
vendeur, dates par genre, lieu, equipe), chacune appariant seule, puis resolution
globale -- contre une cascade de 10 etages entrant par le mandat. ⭐ Le mandat **manque
sur 24,9 %** des transactions : une methode qui entre par lui est aveugle sur un quart
du registre. Et la sortie porte **le meme triplet que le gel**
`(ligne, role, app_affaire_id)` : la comparaison est exacte, sans traduction.

```
LE GEL  12 417 liens / 4 688 lignes      V2  12 635 liens / 4 692 lignes
   identiques 12 195 (95,5 %) . gel seul 130 . v2 seul 348 . divergents 92
L'ECHELLE EST CALIBREE (c'est elle qui rend la liste fiable) :
   6 familles 808 liens -> le gel confirme 99,6 %   . 5 -> 99,2 %
   4 -> 99,7 % . 3 -> 99,2 % . 2 -> 99,2 %
   1 famille : 91-96 %, signalee FAIBLE . 0 : 67,7 %, on ne dit RIEN
```

#### ✅✅ LE RE-GEL ADDITIF EST POSE -- 13/11/2026, 190 gestes, TOUS LES CONTROLES VERTS

```
AVANT  12 422 liens          APRES  12 595 liens   (= 12 422 - 4 + 177)
  A  9 anciens liens retires, 9 nouveaux poses   (anciens restants : 0)
  B  4 liens retires (lignes 3818 et 4100)       (restants : 0)
  C  177 liens ajoutes                            (poses : 177)
INVARIANTS : transaction sur 2 lignes = 0 . liens orphelins = 0
SAUVEGARDE : public.app_classeur_lien_avant_regel_20261113 (12 422, intacte)
PATCH      : supabase/patch_regel_additif_2026-11-13.sql
```

⚠ **Le lot B fait 4 LIENS, pas 2** : ce sont 2 LIGNES (3818, 4100) qui en portent
2 chacune. J'ai annonce 2 puis 188 au total -- le vrai total est **190**.

⛔⛔ **DEUX INCIDENTS PENDANT LA POSE, ET CE QUI LES A RATTRAPES :**

```
1. LE CONNECTEUR MCP SUPABASE EST TOMBE en pleine pose a blanc (7 echecs,
   meme list_projects). ⭐ Il est tombe APRES la sauvegarde et AVANT toute
   ecriture : rien n'etait a moitie fait.
   ➡ LE CHEMIN DE SECOURS EXISTE DEJA DANS LE PROJET : `node
     Console/apply_sql_patch.js <fichier.sql>` (passe par le POOLER, masque le
     mot de passe). ⚠ Il N'AFFICHE PAS les resultats d'un select : pour LIRE,
     envelopper la mesure dans un `raise exception` -- rien n'est ecrit et le
     message remonte.
2. `preuves` EST UN SMALLINT, pas un texte (c'est le NOMBRE de preuves). Mon
   premier patch y mettait une phrase -> « invalid input syntax for type
   smallint ». ⭐⭐ LA TRANSACTION A TOUT ANNULE : verifie juste apres,
   gel=12 422, lot A 9/9 intacts, lot B 4 intacts. RIEN n'avait ete ecrit.
   ➡ C'est pour v2 le NOMBRE DE FAMILLES (3 a 6), et il y est desormais.
```

#### CE QUE V2 APPORTE CONCRETEMENT AU RE-GEL — quatre gains, tous mesures

```
A ⬜ ACCORD   3 LIENS FAUX DANS LE GEL -- ✅ CONTRE-AUDITES LE 13/11, depuis le
              CLASSEUR RELU EN DIRECT (pas depuis le rapport A19). Les trois
              passent par l'etage « 1 mandat seul ». Pour chacun : DEUX NOMS ET
              TROIS DATES AU JOUR EXACT du cote de v2.
                3229 0FFZI3NF  classeur LOTI SUD EST/DESSAGNE 06-10-17 . 20-10-17 . 3 dec 18
                               v2  51140 memes noms, 2017-10-06 . 2017-10-20 . 2018-12-03
                               gel 38358 PASQUIER/JODRILLAT, dates 2016 (18 mois d'ecart)
                3370 HFXW07KA  classeur GRANGE JOAQUIM/SERVANTON REYNEBEAU 24-05 . 06-07 . 19 fev 19
                               v2  43179 JOAQUIM Tiffany/REYNEBEAU, 2018-05-24 . 2018-07-06 . 2019-02-19
                               gel 45946 GRILLET, 2018-04-21 . 2018-05-26 . 2019-03-22
                3390 A6H4MA4O  classeur SCAFIDI/ROUGERON CHERBUT 26-03-18 . 26-04-18 . 23-07-18
                               v2  29784 SCAFIDI Laetitia/ROUGERON ET CHERBUT, dates identiques
                               gel 31561 2018-04-06 . 2018-06-06 . 2018-12-19
              ⚠ C'est le SEUL point qui RETOUCHE des liens existants : tout le
                reste du re-gel est additif. A trancher expressement.
              ⛔ LA CAUSE N'EST PAS ETABLIE, et il ne faut pas en inventer une.
                J'avais ecrit « mandat RECYCLE par Hektor » : MESURE, C'EST FAUX --
                chacun des 6 numeros de mandat en jeu (604, 11870, 2568, 11292,
                2945, 11244) n'est porte que par UN SEUL bien du registre.
                J'ai ensuite soupconne l'ancien CRM (les 3 lignes portent un lien
                `sphere.rodacom.fr`, contre `neosphere.immo` pour le temoin 3826) :
                1 826 lignes sur 4 789 en viennent -- mais l'etage « 1 mandat seul »
                couvre 2 977 lignes et v2 en confirme 95,5 %. Une cause generale
                ferait bien plus de degats. ➡ ON NE SAIT PAS, et ce n'est pas
                genant : v2 a compare TOUTES les lignes, et il n'y a que 5
                divergences sur le bien. La couverture est faite.
B ⬜ ACCORD   6 GROUPES DE DOUBLONS DU CLASSEUR (12 lignes) -- ✅ RELUS DANS LE
              CLASSEUR LE 13/11 : memes mandat, acquereur et DATE D'OFFRE.
                1397 Vente reglee / 3818 Annulee   mandat 13695  ROMEO CLEMENT
                2193 Vente reglee / 4059 Annulee   mandat 13236  NIZIER GUILLARD
                2346 Vente reglee / 4100 Annulee   mandat  3968  BASSET BASTET
                2449 Vente reglee / 4121 Annulee   mandat  3813  CARRIOT
                3785 Annulee      / 3796 Annulee   mandat  4273  VIALLARD
                3856 Annulee      / 3887 Annulee   mandat  4369  PAOLONE
              ⚠ ET ILS NE SONT PAS TOUS IDENTIQUES, contrairement a ce que le
                rapport laissait croire : 2346/4100 ont des commissions
                DIFFERENTES (9 400 contre 10 400), 1397/3818 des dates de
                compromis differentes (28/03/2022 contre 24 fevrier 22).
              ⛔⛔ ET LA MESURE DU 13/11 REDUIT B DE 6 LIGNES A 2 LIENS. J'avais
                ecrit « 6 lignes ne devraient porter aucun lien, le gel leur en a
                donne ». FAUX. Mesure : AUCUNE paire ne partage une transaction,
                et TROIS doublons n'ont DEJA aucun lien -- le gel les a ecartes
                tout seul (4059, 4121, 3796).
                   3818 -> bien 45081  (sa jumelle 1397 -> 9705)   A EXAMINER
                   4100 -> bien 21037  (sa jumelle 2346 -> 48145)  A EXAMINER
                   3887 -> bien 41467  = LE MEME BIEN que 3856, autre transaction
                                       -> plausible (deux offres successives),
                                          NE RIEN FAIRE
                ➡ RESTE 2 LIENS A JUGER, pas 6 lignes a retirer.
C ⬜ ACCORD   LES GAINS « v2 seul » -- ✅ INSTRUITS LE 13/11, LISTE PRETE ET
              CONTROLEE. Source : notice/RAPPORT_V2_CONTRE_GEL_2026-11-13.csv
              ⚠ Le rapport A19 annoncait 348 : LE FICHIER EN CONTIENT 341.
                C'est le fichier qui fait foi (il EST la sortie de la mesure).
```
                341 liens « v2 seul »
                  >= 3 familles independantes          225
                      transaction LIBRE                177   ➡ A GELER
                      transaction DEJA PRISE ailleurs   48   ⛔ A EXAMINER
                  1 a 2 familles                       116   ➡ LAISSER
```
              LES DEUX CONTROLES DE SECURITE, FAITS :
                ① la transaction est-elle deja liee a une AUTRE ligne ?
                   -> 48 oui sur 225. Les geler ferait appartenir une
                      transaction a DEUX lignes du classeur. On les ecarte.
                ② le couple (ligne, role) a-t-il deja un lien ?
                   -> 0 sur 225. Temoin inverse fait : (3229,'offre'),
                      (3370,'compromis'), (3390,'vente') repondent bien
                      « DEJA GELE », et une ligne libre repond « libre ».
                ③ temoin : les 225 transactions existent bien au registre (225/225)
              REPARTITION DES 225 : compromis 113 . offre 76 . vente 36,
              sur 193 lignes du classeur. Familles : 6->9 . 5->47 . 4->70 . 3->99
              ⚠ ET L'ECHELLE NE SE TRANSPOSE PAS TELLE QUELLE : les 99,2 % ont
                ete mesures sur les liens que LES DEUX methodes ont trouves. Ici
                le gel ne les a pas. L'echelle reste le meilleur indicateur
                disponible, ce n'est pas une garantie.
D ✅ CLOS LE 13/11 -- AUCUN GESTE A FAIRE. Mesure ligne a ligne contre le gel :
```
                recommande GARDER LE GEL (109) : 109 ont un lien . 0 n'en ont pas
                recommande NON LIE        (66) :   0 ont un lien . 66 n'en ont pas
```
              ⭐⭐ Le gel est DEJA exactement dans l'etat recommande, pour les
                175 lignes SANS EXCEPTION. Le tableau ne decrivait pas un travail
                a faire : il decrivait un etat, et cet etat est le bon.
              ⬜ Ce qui reste n'est PAS une validation mais une INSTRUCTION, si
                Frederic la veut : les 29 « A VOIR » sont les seules non liees
                ou v2 propose quelque chose. Les 37 autres (34 « a reprendre a
                la main » + 3 doublons) n'ont de candidat chez personne.
              Source : notice/TABLEAU_DECISION_APPARIEMENT_2026-11-13.csv
                54 « les deux, faiblement »      -> recommande GEL (accord)
                43 « meme bien, autre transaction » -> recommande GEL (bien sur)
                29 « v2 seul, faiblement »       -> A VOIR ou laisser NON LIE
                19 « personne ne trouve rien »   -> NON LIE
                15 « bien trouve, aucune transaction libre » -> NON LIE
                12 « le gel seul, faiblement »   -> GARDER LE GEL
                 3 « doublon du classeur »       -> NON LIE
```

⭐ **1 cas n'appartient a personne** : ligne 4393, deux lots d'une meme operation
(biens 59133 et 59136, numeros consecutifs, meme compromis au meme jour). Aucune
methode ne tranchera -- c'est une decision, meme famille que les lignes « a cheval ».
⭐ **Et 1 cas ou v2 se trompe et le gel a raison** : ligne 3826 JL6I6JDG -> le gel
(10195). V2 l'avait lui-meme signale « une seule famille » : l'echelle a joue son role.

### ÉTAPE 2 — l'étiquette de dossier *(B2/B3 du plan du 29/10)*

```
2.1 ✅ FAIT 12/11   la REPETITION ecrite AVANT le collage -- 12 controles, 3 temoins
                    inverses (..._REPETITION.sql, commit cc537ce)
2.2 ✅ FAIT 12/11   la pose A BLANC : 11 441 dossiers, 0 ligne ecrite
2.3 ✅ POSE 12/11   deux migrations : etiquette_dossier_objets_2026_11_12 et
                    etiquette_dossier_pose_et_droits_2026_11_12
                    les 12 controles joues apres le collage : TOUS VERTS
2.4 ✅ B3 FAIT 12/11  le remplissage, en 4 lots (50 d'essai, puis 3 000, 4 000, le reste)
                    31 151 / 31 151 transactions etiquetees -- 0 sans etiquette
                    11 441 dossiers = 11 441 uuid = 11 441 numeros (bijection)
                    invariants 0/0 . journal 11 441 poses, somme 31 151
                    compteur : 25 annees, somme des rangs 11 441
                    ⭐ les 6 dossiers muets (D0000-xxxx) sont TOUS MORTS -- les
                      fermetures du matin ont solde les 2 qui comptaient encore
2.5 ✅ FAIT 12/11   B4 : LA POSE EST BRANCHEE DANS LE RUN DE NUIT **ET ALLUMEE**
                    (`APP_ETIQUETTE_DOSSIER=1` dans `.env`, hors git ; sauvegarde
                    `env_avant_etiquette_2026-11-12.bak`). L'appel est a
                    `affaire_ledger.py` l. 2772, ENTRE `rpc/app_attribuer_chaines_affaire`
                    (l. 2761) et la redescente (l. 2777) -- donc APRES le calcul des
                    groupes, comme C2 du 29/10 l'exige.
                    ⭐ AVEC UN FILET : si la pose echoue, LE RUN CONTINUE. Une
                      etiquette manquante se rattrape la nuit suivante ; un run
                      interrompu coute la nuit entiere.
                    ⭐ ET UNE ALERTE : SEUIL_FUSIONS_QUI_INQUIETE = 10 -- une fusion
                      est DEFINITIVE pour l'etiquette absorbee, qui ne vit plus que
                      dans le journal.
                    essai hors ligne : phase2/checks/test_etiquette_dans_le_run.py
                    32 controles verts, client FAUX, aucune connexion
✅ 2.5bis CONTROLE FAIT LE 13/11 -- LA PREMIERE NUIT DE B4 A TOURNE SEULE.
                    Mesure dans le journal (app_dossier_etiquette_journal), 13/11 05:22 :
                      pose         4 dossiers .  5 transactions (annee 2026)
                      propagation  1 dossier  .  1 transaction
                      fusion       5 dossiers .  8 transactions
                      scission     2 dossiers .  2 transactions
                    ETAT APRES : 31 157 / 31 157 etiquetees . 0 sans etiquette
                                 11 442 uuid = 11 442 numeros (bijection tenue)
                    ⭐ Les 5 fusions sont SOUS le seuil d'alerte (10) : le run n'a
                      rien crie, et c'etait juste.

⚠⚠ 2.6 ⬜ A SAVOIR -- UN NUMERO DE DOSSIER PEUT MOURIR, ET C'EST MESURE.
                    Les 5 fusions de la 1re nuit ont absorbe 5 numeros, qui ne
                    vivent plus que dans le journal (0 ligne restante sur chacun) :
                      D2006-0088 -> D2006-0083 . D2020-0178 -> D2020-0214
                      D2024-0007 -> D2023-0541 . D2025-0131 -> D2024-0316
                      D2025-0075 -> D2025-0035
                    ⚠ UNE SEULE NUIT NE SUFFIT PAS A JUGER LE RYTHME : ce peut
                      etre un rattrapage de premiere nuit ou le regime normal.
                      ➡ RELEVER quelques nuits AVANT d'en tirer quoi que ce soit.
                    ⭐ Sans consequence aujourd'hui (l'etiquette n'est lue par
                      personne). A reprendre AVANT 5.2, pas avant.
⭐ le format est valide (« Oui » aux deux, 09/11) : D2026-0431 + un UUID
⭐ le code local etait PRET avant la pose : les 2 colonnes sont dans
  COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (affaire_ledger.py l. 2561) -- condition C1
```

### ⛔⛔ LE DÉFAUT QUE FRÉDÉRIC A TROUVÉ LE 12/11 AU SOIR — *ma correction était incomplète*

> *« pourquoi les offres du 11/11 sont toujours visibles dans le registre des
> transactions ? et le pilotage forcément »*

Il avait raison. J'avais corrigé les **deux écrans de détail** et conclu trop vite. Le
registre passe par une fonction **EN BASE**, `app_registre_dossiers`, que je n'avais pas
vue — et **le filtre par année s'appuyait sur la date faussée**.

```
MESURE AVANT, sur les 11 424 dossiers du registre
  « date du dernier evenement » fausse        1 277
  CLASSES EN 2026 A TORT                     1 190   <- la plus ancienne : 2006
  date d'offre fausse                        1 412
APRES (3 migrations collees le 12/11)
  dossiers en 2026       1 684  ->  494      1 190 retrouvent leur annee
  dossiers au 11/11/2026 1 185  ->    5      les 5 sans aucun recours
  offres sans date         786  ->   85      701 retrouvent une date
```

⭐ **Et la cascade qu'il a dictée est en service** : journal → compromis → vente.
**56 offres sur 68** retrouvent une date. ⛔ Les crans 4 (le classeur) et 5 (le mandat)
ne sont **pas** dans la fonction : le mandat ne donne qu'une **année**, et on n'invente
jamais un jour. Sans réponse, l'écran affiche « — ».

#### ⛔ ET LE POINT LE PLUS GRAVE, QUE J'AVAIS ÉCARTÉ LE MATIN

Le préremplissage de la modale (`App.tsx:19260`) lisait `affaire.date` brut. Or ce champ
**part chez Hektor** (`console_job_worker.js:15769`, `body.set("dateOffre", tx.date)`).

➡ **Ouvrir puis enregistrer une de ces offres écrivait le 11/11/2026 chez Hektor.**
J'avais écarté ce point « par prudence » : c'était l'inverse, ne pas le toucher laissait
la contamination se propager. **Corrigé le 12/11.**

#### LES QUATRE COUCHES AUDITÉES, ET CE QUI RESTE

```
EN BASE    ✅ app_registre_dossiers . la pose . l'annee d'ouverture
           ✅ app_pilotage_acquereurs    1 408 acquereurs, dont 524 au 11/11
           ✅ app_pilotage_affaires_plus 1 869 -> 702 offres sur 2025-2026, et le
              delai moyen mandat->offre passe de 2 148 jours (5,9 ANS) a 181 jours
           ⭐⭐ LE CHAINAGE EST SAIN, MESURE : app_attribuer_chaines_affaire trie
              par app_affaire_id, et app_chaine_pour (les 2 signatures) groupe sur
              l'annonce, l'acquereur et l'ETAT. AUCUNE date nulle part.
              ⛔ Mon audit l'avait signale A TORT -- ma requete cherchait
                « order by … date » et a crie sur « order by app_affaire_id ».
                Un detecteur qui crie n'est pas une preuve : il faut lire le corps.
           ✅ app_notaire_fiche -- migration notaire_fiche_date_offre_reelle_2026_11_12
AU FRONT   ✅ les 2 tris . la ligne Date . la tuile . le PREREMPLISSAGE
           ✅ le cockpit, le resume et le tri des dossiers d'un bien (App.tsx 32321 .
              32634 . 32753) -- ils passent tous par `dateDeRangement`
PYTHON     ✅ le chainage . l'apparieur . le rapport du gel
           ⚠ export_app_payload.py et transactions_annonce_from_api.py : non mesures
WORKERS    ✅ ils n'ont PAS de lecteur -- ils envoient ce que la modale leur donne
```

### ✅ PROUVÉ À L'ÉCRAN, ET B EST FAIT — *12/11 au soir*

**Le registre des transactions, ouvert dans le navigateur :**

```
« 494 dossiers · 2026 »        <- exactement les 494 mesurés en base (contre 1 684)
291 vendus + 88 compromis + 41 acceptees + 6 proposees + 10 annules + 58 refusees
                              = 494, les compteurs s'additionnent
```

⚠ **Et les 5 offres en tête de liste sont exactement les 5 sans recours**
(24256, 20169, 16330, 16255, 9557) — celles dont Hektor dit `0000-00-00`. Elles sont
les **seules** à rester au 11/11, comme la mesure l'annonçait. ➜ Elles font partie des
**12 à trancher par Frédéric**.

#### ✅ B — L'ÉTIQUETTE POSÉE AU CLIC

```
app_poser_etiquette_du_dossier(p_chaine)   pose + propagation, UN SEUL dossier
la modale l'appelle apres son INSERT       avec un FILET : si la pose echoue,
                                           LE GESTE DE L'UTILISATEUR PASSE QUAND MEME
```

⛔⛔ **Elle ne FUSIONNE ni ne SCINDE jamais** : un clic ne doit pas pouvoir réunir deux
dossiers, une fusion étant irréversible pour l'étiquette absorbée. Fusion et scission
sont des conséquences d'un **recalcul**, et le recalcul n'a lieu que la nuit.

⭐ **Aucune règle dupliquée** : l'année vient du lecteur unique, le rang du **même
compteur que la nuit** — donc aucune série parallèle.

```
EPREUVE, en transactions ANNULEES sur le dossier 3676
  propagation  on retire l'etiquette de la vente -> les 4 la retrouvent (D2025-0254)
  pose         on denude tout le groupe -> un numero neuf D2025-0438, 0 nue,
               1 ligne au journal « AU CLIC », compteur 2025 : 437 -> 438
  apres rollback : tout intact, compteur revenu a 437, 0 ligne « AU CLIC »
```

⚠ **CE QUI N'EST PAS ENCORE PROUVÉ** : personne n'a fait le geste **depuis l'écran**.
L'épreuve appelle la fonction directement. Au premier changement de statut réel, vérifier
que la ligne neuve porte son étiquette à la seconde, et que le journal dit « AU CLIC ».

### ✅ LES 4 ESSAIS DU CHAÎNAGE SONT VERTS — *12/11 au soir*

Ils criaient ROUGE à chaque passage depuis des semaines, et **aucun ne parlait du code**.

```
① l'invariant « bloc date APRES la vente »   11 cas LEGITIMES (offres saisies apres
   coup) presentes comme « ce qui ne doit JAMAIS arriver » -> socle tolere, cri des
   qu'il BOUGE, dans les deux sens . le nombre reste AFFICHE
② les references de compte du 20/10          12 702 / 12 278 / 12 159 / 12 149 avec
   une tolerance de 30, alors que 4 regles ont REUNI 727 dossiers depuis
   -> reetalonnees AVEC la liste des regles sous lesquelles elles valent
   ⭐⭐ + LES RELATIONS, le seul juge qui ne se demode pas : une regle qui REUNIT ne
      peut pas AUGMENTER le nombre de dossiers
      V2 eteinte 11 485 -> V2 11 438 -> cran 1 11 438 -> cran 2 11 428
③ le cran des sans-date IMPOSE a 1           la production est au cran 2
   -> on lit `.env` . ⚠ un setdefault NE SUFFIT PAS (la variable y est chargee PLUS TARD)
```

⛔⛔ **ET DEUX PIÈGES DE MESURE QUI VALENT POUR TOUT LE PROJET :**

```
la base LOCALE porte les chaines du DERNIER RUN -- tout ce qui est pose dans la
   journee n'y est PAS encore. Releve : le dossier 3676 etait encore COUPE EN DEUX
   en local alors que la regle D l'avait reuni chez Supabase, et les 19 offres
   reacceptees y etaient encore « refused ». Un ecart local/Supabase est un RETARD.
⭐⭐ CE QUI COMPTE N'EST PAS LE NUMERO MAIS LE GROUPE : 1 187 numeros differents
   mais 2 854 GROUPES differents. Pour juger un chainage on compare les PARTITIONS
   (qui est avec qui), JAMAIS les numeros.
```

**État : six essais, six verts** — `offre_regularisee` · `vente_ferme` · `v2` (4 sens
+ 3 relations) · `offre_proposee` · `dirty_guards` · `etiquette_dans_le_run`.

### ⚠⚠ LES TROIS TROUVAILLES DE L'APRÈS-MIDI DU 12/11 — *mesurées, pas supposées*

#### ① L'ANNÉE DES ÉTIQUETTES EST FAUSSE POUR 708 DOSSIERS *(le même défaut)*

La pose de 11:00 a daté chaque dossier sur `min(date)`. Donc la date d'une offre
refusée a daté son dossier.

```
dossiers dates                                11 347
dont l'annee est FAUSSE                          708   (6,2 %)
dont etiquetes « 2026 » a tort                   653
part des dossiers « 2026 » qui sont faux   653/1 019   (64 %)
l'annee vraie s'etale de 2006 a 2025
```

⛔ **DEUX lecteurs d'année existaient, aucun n'avait été réparé** — `app_dossier_annee_ouverture`
**et** la CTE « groupes » DANS la fonction de pose. *C'est elle qui a posé les 653.*
*(« Élargir un seuil : chercher ses jumeaux ».)*

⭐⭐ **ET LA FENÊTRE SE FERME** : rien ne lit l'étiquette — `grep` sur `apps/ backend/
Console/ scheduled/` rend **zéro**, 0 clé étrangère, 0 vue, 0 autre fonction. Reposer est
donc gratuit **tant que les UUID ne sont pas partis dans le classeur (5.2)**. Après, le
numéro est public et « un numéro ne se perd jamais » l'interdit.

⚠ **Un piège trouvé à blanc** : 14 offres portent une proposition datée `0000-00-00` ;
sans filtre, leur dossier tombait en `D0000`. **14 régressions évitées.**

```
2.6 ✅ COLLE 12/11  les LECTEURS, en trois migrations :
                    etiquette_annee_lecteur_unique_2026_11_12
                    etiquette_annee_lecteur_durci_2026_11_12
                    etiquette_pose_passe_par_le_lecteur_2026_11_12
2.7 ✅ COLLE 12/11  la REPOSE : etiquette_annee_repose_2026_11_12
                    697 numeros mentaient -> 0 . dont 648 « 2026 » -> 0
                    31 151 etiquettes . invariants 0/0/0 . bijection 11 441
                    compteur 11 441 . journal somme 31 151 . format 0 mal forme
                    de D0000-0001 a D2026-0371 (etait D2026-0550)
                    ⭐ CHRONOLOGIE 100,00 % : 0 desordre sur 11 323 comparaisons
                    sauvegarde : app_etiquette_avant_repose_20261112 (31 151 l.)
2.8 ✅ POSE 12/11   LA DATE DECIDEE pour les 5 offres sans date NULLE PART, en
                    quatre migrations : date_convenue_des_transactions .
                    les_appelants_passent_l_id_v2 .
                    date_convenue_prime_sur_la_colonne . date_convenue_reliee_au_registre
                    + 5 greffes dans api.ts (le front recalculait la regle en TS, et
                      le PREREMPLISSAGE de la modale part CHEZ HEKTOR)
                    9557 -> 11/12/2017 . 16255 -> 11/07/2022 . 16330 -> 08/04/2021
                    20169 -> 01/03/2024 . 24256 -> 25/02/2022
                    ⭐ SOURCE MESUREE, pas devinee : contact 0,95 (mediane 11 j) ;
                      identifiants 0,19 / 0,14 / 0,01 ECARTES -- Hektor recycle ses
                      numeros (prouve sur le mandat 16705, porte par DEUX biens)
                    ⛔ MON ERREUR, trouvee par la mesure en une minute : la date
                      decidee etait APRES la colonne `date` dans le coalesce. Or
                      `date` n'est pas vide : elle porte le 11/11 faux. Le repli ne
                      jouait JAMAIS. Ordre juste : journal -> DECIDEE -> `date`.
                    temoin inverse : compromis 10 653 -> 0 bouge . offre 11 218 -> 5
                      bougent . vente 9 280 -> 0 bouge
                    trace : supabase/patch_date_convenue_2026-11-12.sql
2.9 ✅ POSE 12/11   LA REPOSE N°2 -- les 5 dossiers ayant change d'annee, leur
                    etiquette D2026-0367..0371 etait devenue fausse et l'invariant
                    valait 5 : le controle aurait CRIE chaque jour.
                    migration etiquette_repose2_apres_dates_decidees_2026_11_12
                    l'annee qui ment 5 -> 0 . 1 486 dossiers renumerotes (4 010
                    transactions) . bijection 11 441 = 11 441 . 0 desordre chrono
                    plage D2026-0371 -> D2026-0366
                    ⭐⭐ LES 5 PORTENT EXACTEMENT LES NUMEROS QUE LA SIMULATION EN
                      LECTURE SEULE AVAIT ANNONCES : D2017-0564 . D2022-0335 .
                      D2021-0217 . D2024-0072 . D2022-0098 -- des rangs au MILIEU
                      de leur annee, donc chronologiquement justes
                    ⚠⚠ PIEGE EVITE DE JUSTESSE : le patch de 2.7 cree ses copies en
                      `create table if not exists`. Le relancer n'aurait RIEN
                      sauvegarde et j'aurais detruit en croyant etre couvert. D'ou
                      des tables PROPRES : app_etiquette_avant_repose2_20261112
                      ⭐ LECON : un patch idempotent n'est pas rejouable.
                    trace : supabase/patch_etiquette_repose2_2026-11-12.sql
```

⛔⛔ **ET LE TÉMOIN INVERSE DE MA PROPRE RÉPÉTITION A TROUVÉ UN DÉFAUT DANS MA PREMIÈRE
VERSION DU LECTEUR.** Écrit en SQL pur, il **levait** sur un `propositions_json` qui n'est
pas du JSON (*« invalid input syntax for type json »*) au lieu de retomber sur `date` :
**une seule valeur abîmée aurait fait tomber la pose entière.**

```
le risque est THEORIQUE -- la colonne est de type JSONB, la base ne peut pas
   contenir du non-JSON. MAIS la fonction prend du `text`.
corrige quand meme : plpgsql + bloc exception, 5 lignes
eprouve sur : JSON illisible . tableau de texte . JSON tronque -> repli sur `date`
les 10 temoins sont verts, dont les TROIS qui faisaient lever
```

⭐ **C'est exactement à quoi sert une répétition écrite avant le collage.** Sans elle,
le défaut dormait jusqu'au jour où une ligne aurait été abîmée.

#### ② LES 33 LIGNES À CHEVAL : L'ÉNIGME EST RÉSOLUE

Elles ont **toutes la même forme** — *offre refusée + compromis annulé, même bien* :

```
23 lignes   deux ACHETEURS DIFFERENTS -> LE CLASSEUR melange deux affaires sur
            une ligne. LE CHAINAGE A RAISON, il n'y a rien a corriger chez nous.
 5 lignes   MEME acheteur -> le chainage a rate : reunissables
            8SZDU4F5 . BHMANOK7 . H3SQXY47 . U258U4CX . WUQ5445T
 5 lignes   un nom manque -> a mesurer
            26283bf9 . 566d1a48 . 600f4e1c . 7PBRZJD8 . CA2XNF38
```

⛔ **ET PAS DE RÈGLE AUTOMATIQUE.** Portée mesurée sur tout le registre : **472 paires,
dont 417 avec deux acheteurs DIFFÉRENTS.** Une règle sans la garde du nom aurait fusionné
417 affaires d'acheteurs concurrents. *La décision du 04/09 était juste.*

⚠ **Et ma première mesure disait « 472 sans acquéreur »** : `acquereurs_json` est
**parfois un OBJET, parfois un TABLEAU**. Une lecture ratée n'est jamais un vert.

#### ③ 20 OFFRES REFUSÉES À TORT PAR MON LOT DU 11/11

⛔⛔ **ET MA PREMIÈRE QUALIFICATION ÉTAIT FAUSSE — corrigée le 12/11 après mesure.**
J'avais écrit *« 517 offres refusées à tort, dont 496 l'histoire de Hektor depuis 2007 »*.
**C'est faux, et c'eût été grave de le laisser écrit** : quelqu'un serait allé « réparer »
500 lignes justes dans six mois.

```
offres refusees dont l'acheteur a FINALEMENT achete        220
  leur refus est AVANT ou LE JOUR de la vente              218   ⭐ l'ordre d'une NEGOCIATION
  apres la vente                                             1
  sans refus a leur journal                                  1
  ACCEPTEES puis refusees -- la seule vraie anomalie          2
```

⭐ **« Même acheteur » ne veut pas dire « erreur ».** Une offre refusée n'empêche pas le
même acheteur d'acheter ensuite : il offre 180 000, c'est refusé, on négocie, il revient à
195 000 et la vente se fait. **L'offre à 180 000 reste refusée, et c'est juste.** Les 218
refus antérieurs à la vente le prouvent.

⭐ **La vraie anomalie est « ACCEPTÉE puis refusée alors que l'affaire a abouti »**, et il
n'y en a que **2** :

```
offre 11147  HUGON, bien 23353 . acceptee 19/01/2026, refusee 11/03/2026, vendue 27/03/2026
             ⭐ le refus N'EST PAS DE NOUS (11 mars) : geste humain 16 jours avant la
               vente, l'affaire a ete refaite. RIEN A CORRIGER.
offre 14420  BELLAVIA . refusee le 11/11/2026 PAR MOI -> le seul cas restant, et il
             est a nous (c'est celle qui est LAISSEE de cote plus bas)
```

➡ **Il n'y a pas 500 anomalies chez Hektor. Il y en avait 20, toutes de mon fait, dont
19 sont réparées.** ⚠ Ce qui ne change rien à l'erreur de méthode : j'ai agi en masse sur
un chaînage que je savais incomplet.

⭐ **Le script avait la BONNE garde** (`cpAnnule && !cpVivant && !vente && offreAcceptee`).
⛔ **L'erreur est une erreur d'ORDRE, et elle est à moi** : j'ai refusé sur un chaînage
incomplet, puis j'ai corrigé le chaînage **le lendemain**. Hier soir l'offre 3678 était
seule ; la règle D l'a réunie ce matin aux trois autres transactions de DEFOUR, révélant
que le refus était faux.

➡ **LEÇON : ne jamais poser un geste de masse chez Hektor sur un chaînage qu'on sait
incomplet. Le chaînage d'abord, le geste ensuite.**

```
1.7 ✅ FAIT 12/11   19 offres remises « acceptee » CHEZ HEKTOR ET CHEZ NOUS
                    Console/enqueue_reaccepter_offres_refusees_a_tort.js
                    18 travaux done, 0 erreur . 19/19 « accepted », 0 « refused »
                    ⛔ 1 LAISSEE, DECLAREE : l'offre 14420, dont l'offre est datee
                      APRES sa vente (20/11/2009 contre 25/07/2008) -- deux defauts
                      se superposent, on ne repare pas deux choses d'un geste.
                      TEMOIN INVERSE : elle est bien restee « refused ».
                    ⛔ ET LES 219 AUTRES N'ONT PAS BOUGE -- et c'est JUSTE : ce sont des
                      NEGOCIATIONS NORMALES (refus AVANT la vente), pas des defauts.
                      Voir la correction de ma qualification au § ③ ci-dessus.

⭐⭐ **L'ESSAI SUR UNE SEULE A TROUVE UN TROU, ET C'EST POUR CA QU'ON LE FAIT.**
Le travail finissait `done`, avec `verbe: GET` et `reponse_hektor: 1`, la relecture de
la fiche tournait -- **et notre registre disait toujours « refused », le journal de
l'offre n'avait aucun 4e evenement.** A ce stade je ne POUVAIS PAS dire si Hektor avait
bascule.

```
la cause   le refresh_console_data relit L'ANNONCE, pas les TRANSACTIONS
           (elles ont leur propre listing, list_offres, relu LA NUIT)
le remede  phase2/sync/transaction_etat_from_api.py -- porte 2, ecrite le 16/09
           pour cette raison exacte : « une verification qui ne depend pas de
           l'ordre des choses ». Sur 9886 : « etat: accepte ».
```

⛔ **La seconde passe lit maintenant l'etat CHEZ HEKTOR, offre par offre, et n'ecrit
chez nous que si Hektor dit « accepte ».** Une lecture ratee n'ecrit rien et compte
comme un echec. *Sans l'essai sur une seule, j'aurais pose 19 etats sans preuve.*

⚠ **A VOIR DEMAIN MATIN** : la colonne `date` de ces 19 offres passera au 12/11 (le run
relira leur journal, qui porte maintenant l'acceptation). **Sans effet a l'ecran** depuis
le commit 541f1be -- c'est exactement ce qu'il devait proteger.

⚠ **ET UN SUJET A PART, TROUVE EN PASSANT** : 7 de ces dossiers portent **a la fois une
vente et un compromis encore « actif »**. Un compromis ne devrait pas rester actif apres
la vente. Non traite, pas mesure en ampleur.
```

### ÉTAPE 3 — le rapatriement *(P1.4)*

```
3.1 ✅ FAIT 13/11   rapport refait AVEC LE GEL A JOUR (12 595 liens apres le
                    re-gel additif). 4 702 lignes rattachees (contre 4 688),
                    87 non rattachees.
                    Sorties : notice/A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-11-13.csv
                              notice/A4_RAPPORT_GEL_ECARTS_SEULS_2026-11-13.csv (3 898)

⛔⛔ 3.1bis LA DECOUVERTE ⑦ (« chainage douteux ») NE PREDIT RIEN -- MESURE 13/11

   Le rapport annonce « 1 809 transactions portent un nom etranger a leur
   chaine » contre 219 au 29/10, soit HUIT FOIS PLUS. Ce n'est pas une
   degradation : le chainage reunit beaucoup plus depuis les regles du 10-12/11
   (la regle D a reuni 727 dossiers), donc il y a bien plus de chaines a
   plusieurs membres -- 10 109 chaines portant 29 824 transactions.
   Ces 1 809 transactions se concentrent sur 407 LIGNES du classeur, dont
   406 « Vente reglee » et 403 portant les TROIS roles.

   ⭐⭐⭐ ET CE SONT SURTOUT DES COUPLES. Exemples relus :
```
     classeur GATTET Mathilde ROURE Jimmy  nous GATTET JIMMY MATHILDE ROURE
     classeur COUDOUR Valerie              nous COUDOUR GENILLON RENE VALERIE
     classeur CHAUTARD Pauline             nous CHAUTARD CHEROUGE PAULINE SYLVAIN
```
   Le classeur nomme un acheteur, nous portons le menage complet. Dans la
   chaine, l'offre porte le nom de l'un et le compromis celui de l'autre : le
   test les declare « etrangers » alors que c'est LE MEME FOYER.

   ⛔ LA MESURE QUI TRANCHE -- comparer les deux populations, pas juste compter :
```
     lignes DOUTEUSES (407) : 395 acquereurs identiques = 97,1 %
     lignes saines  (4 295) : 4 166 identiques          = 97,0 %
```
   LE MEME TAUX. Le marqueur ne distingue rien.

   ➡ **NE PAS SAUTER CES 407 LIGNES** a la mise en conformite : on en ecarterait
     395 parfaitement bonnes pour rien. La consigne « la mise en conformite doit
     les SAUTER » de la decouverte ⑦ est a REVOIR -- elle a pu etre juste au
     29/10 sur 219 lignes, elle ne l'est plus avec le chainage actuel.
   ⬜ A trancher : garder le marqueur comme simple signal (il reste vrai que les
     noms varient dans la chaine), mais ne plus en faire un critere d'exclusion.
   Lie : [[contacts-muets-fiches-de-couple]]
⛔⛔ 3.1ter LE RAPPORT A UN CHAMP FAUX -- TROUVE PAR FREDERIC LE 13/11

   Sa question : « attention, la charge de commission est remplie dans l'app, non ? »
   ⭐ IL AVAIT RAISON, et c'etait deja ecrit dans la memoire du projet :
     « La charge des honoraires n'a JAMAIS eu besoin d'etre rattrapee depuis un
      classeur : Hektor nous la livre en clair, chaque nuit. »
```
     data/hektor.sqlite -> hektor_annonce_detail -> honoraires_json -> « charge »
     62 571 lignes « vendeur » . 19 352 « acheteur » . JAMAIS de vide
```
   LE DEFAUT : le rapport lit `charge_commission_app` (colonne du registre que
   l'APP remplit, et que personne n'a jamais remplie). Il annonce donc
   « 950 au classeur seul + 3 752 vides » -- un trou qui N'EXISTE PAS.

   ⭐⭐ AUDIT DES 21 CHAMPS, FAIT LE 13/11 -- UN SEUL EST FAUX :
```
     Mandat, Prix, Commission, dates, Etat, Acquereur, Vendeur, Notaire
        -> app_affaire_ledger                    ✅ bonne source
     Negociateurs 1/2/3 -> repartition + fiches   ✅
     Agence, Ville, Nature -> app_mandat_register_current  ✅
     Vente Reglee, Numero de facture -> AUCUNE source : on ne les a pas ✅ juste
     Charge Commission -> charge_commission_app   ⛔ LE SEUL FAUX
```
   ⚠ ET LA PORTEE EST PLUS LARGE QUE CE CHAMP : le rapport ne lit QUE six
     sources -- le gel, le registre des transactions, la repartition, le registre
     des mandats, les alias et les fiches negociateur. **Il ne lit NI l'annonce
     (`app_dossier_current`) NI son detail (`hektor_annonce_detail`).** Tout champ
     dont la donnee vit la sera declare « vide chez nous » A TORT.

   ⛔⛔⛔ ET J'EN AI TIRE UNE CONCLUSION FAUSSE, QUE FREDERIC A ARRETEE :
     j'ai ecrit « le vrai sujet est de faire remonter la charge de Hektor, pas de
     la rapatrier du classeur » et « retirer Charge Commission du perimetre ».
     **C'EST L'INVERSE DE LA DECISION DEJA PRISE**, et elle tient sur TROIS
     audits que je n'avais pas ouverts : A8 (02/11), A10 et A11 (03/11).

   ✅ CE QUE A11 A ETABLI, PAR LA MESURE (juge_charge_classeur_contre_hektor) :
```
     comparables 380 : classeur vendeur 363 . classeur acquereur 17
     HEKTOR juste                 368   96,84 %
     « TOUJOURS VENDEUR » juste   363   95,53 %   <- LE TEMOIN INVERSE
     gain reel de Hektor                +1,32 point seulement
     HEKTOR MUET sur              552 / 956 lignes renseignees = 57,7 %
```
   ⛔ **HEKTOR N'EST PAS UNE VALEUR DE REFERENCE POUR LA CHARGE.** Il est muet
     plus d'une fois sur deux, et repondre « vendeur » a tout le monde ferait
     95,5 %. ⭐ Son seul usage reel : quand il DIT « acquereur », il a raison
     77,8 % du temps -- un signal fort sur la CLASSE RARE, en SIGNALEMENT.

   ➡ **LE CLASSEUR FAIT FOI SUR CE CHAMP.** Le rapport n'est donc PAS faux ici :
     ses « 950 au classeur seul » sont EXACTEMENT ce qu'il faut rapatrier.
     ⚠ Ce qui reste vrai de mon audit : `charge_commission_app` est la case que
       l'app remplit, et elle est vide -- c'est bien la cible de l'ecriture,
       pas une erreur de lecture.

⛔⛔ 3.1quater LE RAPPORT NE COUVRE PAS TES CHOIX -- AUDIT DU 13/11

   ⭐ LA SOURCE DE VERITE DES 38 CHOIX EST **L'ARTEFACT DE FREDERIC** :
     https://claude.ai/artifact/JFtYqskwiwgWANvgT8nk4S  (collection `choix`)
     ⚠ Le fichier notice/DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md est
       PERIME sur deux colonnes : il compte 7 « les vides », l'artefact 5 --
       **AB (Acquereur) et AD (Vendeur) sont passes de « vides » a RIEN** le
       09/11 a 13:13. L'artefact fait foi, il est plus recent.
     ⛔ Et notice/A13_DECISIONS_COLONNE_PAR_COLONNE.md se declare lui-meme
       SUBORDONNE : il ignore 7 decisions du 02/11. NE PAS s'en servir.

   LES 38 CHOIX, AU 13/11 :
```
     TOUT (16)      I J K L M N Q V Y Z AA F G AH AI AJ
     LES VIDES (5)  C Mandat . P Commission TTC . S Offre . T Compromis . W Vente fixee
     COMPARER (1)   AF Prix
     RIEN (16)      A B D E H O R U X AB AC AD AE AG AK AL
```

   ⛔ CROISEMENT AVEC LE RAPPORT : sur les 22 colonnes ou l'on AGIT,
     **13 sont mesurees, 9 NE LE SONT PAS**. Et les 9 ne se valent pas :

   **A. TROIS VRAIES LACUNES -- LES POURCENTAGES (J, L, N), decides « tout »**
```
     ils touchent LA PAIE
     la somme des trois fait EXACTEMENT 100 dans 4 768 cas sur 4 780
     en face, 96 % de nos chiffres sont un CALCUL PAR DEFAUT
     ⭐ et le rapport CHARGE DEJA la colonne `pourcentage` de
       app_affaire_repartition -- il ne la COMPARE jamais
     ⚠ piege de format : N porte « 12,5 » AVEC UNE VIRGULE
```
     ➡ A AJOUTER AU RAPPORT : 3 champs, la donnee est deja chargee.

   **B. SIX CHAMPS QUI N'EXISTENT PAS ENCORE CHEZ NOUS** (F, G, Z, AH, AI, AJ)
     Decides « tout, SI ON CREE LE CHAMP ». Normal qu'ils ne soient pas
     mesures : il n'y a rien en face. ➡ RIEN a corriger dans le rapport.

   **C. ET UN DEFAUT DE SOURCE, DEJA PROUVE : Q (Charge Commission)**
     Le rapport lit sur l'AFFAIRE (`charge_commission_app`), la donnee vit sur
     le MANDAT. ⭐⭐ ET LE TRAVAIL EST FAIT DEPUIS LE 04/11 : **23 474 valeurs
     posees, dont 837 du classeur** (note de Frederic dans l'artefact).
     ⛔ Le rapport reclame donc un travail ACCOMPLI. ➡ A CORRIGER.

   ➡ **LE RAPPORT A QUATRE CORRECTIONS** : 3 ajouts (pourcentages) + 1 source
     (charge). Les 13 autres colonnes mesurees lisent au BON endroit (verifie
     une par une le 13/11 : registre des transactions, repartition, registre
     des mandats -- voir 3.1ter).

## ⭐⭐ 3.1quinquies LE LOT 1 -- NEGOCIATEURS ET POURCENTAGES, MESURE LE 13/11

   ✅ DECISION CONFIRMEE PAR FREDERIC LE 13/11 : **ON PREND TOUT DU CLASSEUR**,
     sans exception -- y compris le seul vrai desaccord (bien 1993).

   LE VOLUME EXACT, apres l'ajout des 3 pourcentages au rapport :
```
     Negociateur 1    396 ecarts +  171 classeur seul  =    567
     Negociateur 2    378        +   51                =    429
     Negociateur 3     10        +    1                =     11
     Pourcentage 1    570        +  797                =  1 367
     Pourcentage 2      5        +  656                =    661
     Pourcentage 3      0        +   14                =     14
                                              TOTAL    =  3 049 cases
```
   ⚠ NEGOCIATEURS ET POURCENTAGES VONT ENSEMBLE : poser un negociateur 2 sans
     sa part n'a aucun sens, et poser une part sans la personne non plus. C'est
     UN SEUL geste sur app_affaire_repartition.

   ⭐⭐ CE QUE LE CLASSEUR SAIT ET QUE NOUS IGNORONS, mesure du 13/11 :
```
     affaires a PLUSIEURS commerciaux   classeur 652   nous 19
     affaires a TROIS commerciaux       classeur  13   nous  0
     affaires SANS aucune repartition   chez nous 893
```
   ⚠ Et la verification demandee par Frederic a evite 3 faux : 642 lignes du
     classeur portent deux noms, mais 3 repetent LE MEME -- donc 639 a deux
     noms distincts, pas 642.

   ⭐ LE CROISEMENT DES 13 AFFAIRES « nos parts ne font pas 100 » LE CONFIRME :
```
     11 / 13  le classeur APPORTE ce qui manque (le 2e nego, ou la part entiere)
              et NOS chiffres sont des MORCEAUX JUSTES du sien :
              50 = la part exacte de COUDERT . 75 = celle de FLANDIN
      1 / 13  un vrai desaccord : bien 1993 (classeur FORLICO 75 + PEREIRA 25,
              nous PEREIRA 87,5) -> le classeur gagne, par decision
      2 / 13  repartition VIDE chez nous (biens 47347 et 62527)
```

   ✅✅ **LE PREALABLE EST REMPLI -- MESURE DU 15/11, APRES LE DOUTE DE FREDERIC
     (« les negociateurs ont deja ete faits, verifie ! »). IL AVAIT RAISON.**
     Les **13 sont dans `app_negociateur_personne`** (13/13, FRANCHINI Marjorie
     comprise), et **12 sur 13 ont deja leurs lignes dans
     `app_affaire_repartition`** -- 30 lignes posees :
```
     ABED 7 . ALLEMAND 4 . BERTRAND 4 . AGRAIN 2 . BRUNON 2 . EXBRAYAT 2
     COMMERE 2 . LEFAURE 2 . PETROSINO 2 . LAUGIER 1 . ADAMO 1 . BALIQUE 1
     FRANCHINI Marjorie 0   <- la SEULE sans ligne posee (1 ligne au classeur)
```
   ⚠ **CETTE RESERVE ETAIT PERIMEE ET JE L'AI RECOPIEE TELLE QUELLE** dans mon
     plan du 15/11, sans la recouper avec la base. C'est la meme faute que les
     quatre trous : **croire le plan au lieu de mesurer**. Le reste de ce bloc
     garde la liste d'origine, pour l'histoire :
```
     ABED 6 . ALLEMAND 4 . BERTRAND 3 . AGRAIN 2 . BRUNON 1 . EXBRAYAT 1
     COMMERE 1 . LEFAURE 1 . PETROSINO 1 . LAUGIER 1 . ADAMO 1 . BALIQUE 1
     FRANCHINI Marjorie 1
```
   ✅ Les trois autres prealables du 02/11 sont remplis : les alias (GIRAUD ->
     Aline VALETTE 159 fois, ALVES MENDES -> Lucie DECHANDON 118) et les
     exclusions (meilleursagents 17, GTI 6, DENOPCE 1/2 1).
   ⚠ NON VERIFIE : les 30 dossiers « notre nom est etranger aux deux », a ecarter.

## ✅✅ 3.1sexies LE LOT 1 EST POSÉ EN PRODUCTION — **13/11 au soir, accord de Frédéric**

   L'outil : `phase2/checks/rapatrier_repartition_classeur.py` (lecture seule,
   dépose un patch avec `--sql`), commité et poussé — `6eec3ab`.
   Le patch joué : `supabase/patch_repartition_classeur_2026-11-13.sql`.

```
     app_affaire_repartition   16 136  ->  17 890 lignes
        9 100 posees « classeur_reconstitue » sur 4 439 chaines
        7 346 anciennes retirees -> app_affaire_repartition_avant_classeur_20261113
        16 136 - 7 346 + 9 100 = 17 890       l'arithmetique boucle
        cotes faux 0 . saisies humaines 20 INTACTES
        a PLUSIEURS personnes 605 chaines     (nous n'en connaissions que 19)
```

   ⭐⭐⭐ **LA REGLE DE DECOMPOSITION**, mesuree sur les 4 702 lignes rattachees :
     le classeur ne donne qu'un TOTAL par personne, notre table range par COTE.
```
     ENTREE 50 % + SORTIE 50 % = 100 %        4 696 lignes sur 4 702
     celui qui a le plus (toujours >= 50) prend l'ENTREE, pour 50
     son excedent au-dessus de 50 va sur la SORTIE
     tous les autres vont entierement sur la SORTIE
```
     ⚠ Les 409 cas « 50/50 » sont ambigus et c'est INOFFENSIF : les totaux par
       personne sont identiques dans les deux sens. D'ou l'origine
       `classeur_reconstitue`, qui ne doit JAMAIS passer pour une saisie.

   ⭐⭐⭐ **LES REGLES D'ECRITURE DU CLASSEUR, DITES PAR FREDERIC LE 13/11** —
     le nom SEUL designe toujours la meme personne ; un prenom ou une initiale
     ecrits gagnent sur la regle :
```
     « CHAMPAGNAC » seul  = Joel (238)       sinon « Julie CHAMPAGNAC » (153)
     « REYNAUD » avec E   = Corinne (115)    « RAYNAUD » avec A = Nicolas (75)
     « MARTINEZ » seul    = Pierrick (56)    sinon « Stephanie MARTINEZ » (55)
     « BOUCHET » seul     = Nicolas (70)     sinon « Mickael BOUCHET » (193)
```
   ⛔⛔ **ELLES PASSENT AVANT TOUT INDICE TIRE DE LA BASE.** Sans elles, l'indice
     « quelqu'un de ce nom est deja pose sur cette chaine » envoyait **69 lignes
     sur Nicolas REYNAUD (196)** au lieu de Corinne. ⭐ *Une trace dans une base
     n'est pas une regle d'ecriture.* TEMOIN INVERSE apres la pose : **zero ligne
     sur 196**, et Joel CHAMPAGNAC 389 / Julie 19 / Corinne 108 / Nicolas RAYNAUD
     76 / Pierrick MARTINEZ 185 / Stephanie 105 / Nicolas BOUCHET 276.

   ⭐⭐ **LES 205 « CONFLITS » N'EN ETAIENT PAS 205.** Mesure faite AVANT de les
     soumettre a Frederic : **173 paires disent exactement la meme chose** (on
     compare la decomposition RESOLUE — personne + cote + part —, pas le texte
     des cases). Le script les absorbe. Restent **32 vraies divergences**, dans
     `notice/A5_CONFLITS_CLASSEUR_A_TRANCHER_2026-11-13.csv`.
     ➡ LECON : *avant de faire trancher une pile, mesurer combien de cas se
       tranchent seuls.*

   ✅ LE PREALABLE DES 13 ANCIENS EST REMPLI (9001-9013, poses dans
     `data/hektor.sqlite` qui n'est jamais purgee).
     ✅ **ILS ONT SURVECU A LA PURGE** — controle du 14/11 au matin : les 13 sont
       dans `app_hektor_negotiator_agency_directory`, tous `is_active = false`,
       `active_source = local_hektor_negociateur_inactive`. Le dispositif tient.

## ✅✅✅ 3.1septies LES 30 DERNIERES CHAINES SONT POSEES — **14/11, accord de Frédéric**

   ⭐⭐⭐ **LES « 32 DIVERGENCES » NE DEMANDAIENT PAS 32 ARBITRAGES : UNE REGLE.**
     En les regardant une par une, la cause saute aux yeux — ce ne sont PAS deux
     saisies contradictoires du meme fait, mais **DEUX AFFAIRES SUCCESSIVES SUR LE
     MEME BIEN** : meme mandat, acquereurs differents, une offre ou un compromis
     TOMBE puis la vente qui a ABOUTI.
```
     chaine 117, mandat 15323
       A  LEGRAND=50 + FORLICO=50   Vente reglee 21/03/2024   acq. DEBRAY
       B  FORLICO=100               Annulee      23/07/2023   acq. LANGLADE
     B n'a JAMAIS encaisse de commission : il n'y a rien a y repartir.
```
   ⭐⭐ **LA REGLE, ET ELLE EST UNIQUE** :
```
     LA LIGNE DU CLASSEUR DONT LE DERNIER MOUVEMENT EST LE PLUS RECENT
     PORTE LA REPARTITION DE LA CHAINE.
```
     ⭐ **Le temoin qui l'a validee** : j'ai eprouve DEUX formulations — « celle
       qui a abouti » et « la plus recente ». Elles donnent le MEME gagnant
       **29 fois sur 29, zero desaccord**. Les 4 restantes sont des biens qui ne
       se sont JAMAIS vendus (plusieurs tentatives, toutes annulees) : la, « celle
       qui a abouti » ne dit rien et seule la date tranche. D'ou UNE SEULE regle.
     ⚠ Elle reste MUETTE (donc refus) si les deux dates sont illisibles ou egales.
     ⛔ **ELLE A BESOIN DU PARSEUR TOLERANT** (voir 3.2) : les cas mesures
       portaient des dates « 5 decembre23 », que l'ancien parseur rendait `None`.

```
     patch joue : supabase/patch_repartition_classeur_2026-11-14.sql
     17 890 -> 17 905 lignes . classeur_reconstitue 9 100 -> 9 165
     chaines 4 439 -> 4 469 (+30) . saisies humaines 20 INTACTES
     0 cote faux sur 8 938 couples chaine/cote
     sauvegarde : app_affaire_repartition_avant_classeur_20261114 (50 l. / 25 ch.)
     ce qu'on a remplace : 24 « hektor_partage_suppose » . 1 « hektor » . 5 RIEN
```
   ⭐⭐ **LE PATCH EST CHIRURGICAL** (option neuve `--seulement-changees`) : il
     COMPARE chaine par chaine ce qu'on veut poser a ce qui est en base, et sort
     du patch tout ce qui est deja ainsi. **4 439 chaines sont sorties**, le patch
     n'a touche que 30. Sans ca, un second passage rejouait un delete + insert de
     9 100 lignes pour 65 de neuves.
     ⛔ **L'ORIGINE FAIT PARTIE DE LA SIGNATURE**, et l'oublier m'a donne un
       premier filtre trop large : 8 chaines ou Hektor avait DEJA devine la bonne
       repartition en sortaient, et gardaient l'etiquette `hektor_partage_suppose`
       alors que LE CLASSEUR FAIT FOI. Meme valeur, provenance moins sure.

   ⛔⛔ **DEUX DEFAUTS GRAVES TROUVES EN RELISANT LE PATCH AVANT DE LE JOUER** :
```
     ① le controle (4) comptait TOUTE la table : « n <> 65 » voyait les 9 165
       lignes posees la veille -> le patch ECHOUAIT A COUP SUR.
     ② LE RETOUR ARRIERE ETAIT DESTRUCTEUR : « delete where origine =
       'classeur_reconstitue' » TOUT COURT aurait efface LES 9 100 LIGNES DU
       LOT 1 pour n'en remettre que 30 chaines.
```
     ➡ Les deux sont desormais **bornes aux chaines du patch**. ⭐ *Un controle,
       comme un retour arriere, ne juge que SA part — jamais la table.*

   ⭐ **TEMOIN** : la chaine **23802** est la SEULE ou la regle designe l'autre
     ligne que celle retenue la veille (A annulee 02/10/2025 / B VENDUE
     10/11/2026). En base elle porte NICOLAS RAYNAUD 50/50, et le **temoin
     inverse** tient : **zero occurrence de JOURGET** sur cette chaine.

   ⛔ **« BEKCER » : EXCLUSION DELIBEREE, decidee par Frédéric le 14/11.**
     On ne pose rien et on ne cree PAS « BEKCER » dans l'annuaire : si c'est une
     inversion de lettres, le creer figerait la faute pour toujours.
     ⭐ Et l'enjeu avait fondu a la mesure : des 2 lignes, la chaine **16869 est
       DEJA SERVIE** par une autre ligne du classeur (SABRINA BLACHIER 50/50) ;
       ne reste que la **16882**, affaire **annulee en janvier 2020**, aucune
       commission encaissee. Aucun `BECKER` nulle part dans l'annuaire.

   ⬜ CE QUI RESTE DU LOT 1, sans urgence :
```
     87  lignes jamais rattachees par le gel     (connu depuis le 02/11)
     24  apporteur (meilleursagents, GTI) avec une part
      1  « BEKCER » -- EXCLUSION DECLAREE ci-dessus
      2  un total a 50 . personne n'atteint 50 %
```

## ✅✅✅ 3.1nonies LE CHIFFRE AJOUTÉ DEVANT — **règle de Frédéric du 14/11, et les 39 lignes VALIDÉES**

   ⭐⭐⭐ **LA RÈGLE D'ÉCRITURE, DANS SES MOTS (14/11)** : *« certains numéros de
     mandat sur les lignes du Sheet avaient un chiffre qui avait été ajouté devant
     le numéro de son mandat, car une autre ligne du registre existe déjà avec ce
     numéro, donc l'utilisateur ajoutait un chiffre devant. »*
```
     LA FORME EST MESUREE, pas supposee : des trois formes possibles, seule
     « retirer UN chiffre DEVANT » retrouve un mandat du bien reellement
     trouve (3 fois). « Deux chiffres devant » : 0. « Un chiffre a la fin » : 0.
```
   ⛔⛔ **MAIS ELLE NE SE GENERALISE PAS EN REGLE DE CALCUL**, et le temoin inverse
     dit pourquoi : un nombre de **4 chiffres** pris AU HASARD existe deja dans
     notre annuaire de mandats dans **95 %** des cas (2 000 tirages, 14/11).
     « Le de-prefixe existe » ne prouve donc RIEN seul.
     `3 chiffres 100 % . 4 chiffres 95 % . 5 chiffres 8,8 %` — seul
     **218611 -> 18611** est concluant par les chiffres.
   ⛔ Et **25 des 33 lignes portent « NON TROUVE »** dans leur colonne Ville :
     leur auteur ne savait deja pas de quel bien il parlait.
     ⚠ **Au passage, 1 398 lignes du classeur (29 %) portent « NON TROUVE »
       quelque part** — 1 387 en Ville, 66 en Prix, 6 en Mandat.

   ✅✅ **LES 39 LIGNES SONT VALIDÉES PAR FRÉDÉRIC, le 14/11** — 6 une par une dans
     la page, puis « ils sont tous juste », puis « je valide les 7 ».
     ➡ **RIEN A CORRIGER EN BASE** : la repartition posee le 13/11 sur ces
       dossiers est JUSTE. Le sujet est clos sans aucune ecriture corrective.
     ⚠ **Les 7 dernieres reposent sur SON jugement, pas sur une mesure** : nous
       n'avons pas les deux noms de notre cote. Qui relira doit le savoir.
       `16097 CHARVOLIN VALLENTIN . 16231 DELAUNAY . 18967 SCI ROYALE .
        21963 STAUFFER . 54111 ANDRE . 92560 (sans acheteur) . « NON TROUVE » SCI MADEVA`

   ⭐⭐⭐ **LA LEÇON, ET ELLE M'A COUTE 32 RELECTURES INUTILES.** J'ai declare ces
     39 lignes « incertaines » parce que le gel les avait rattachees **par les
     noms**, et que revérifier les noms me semblait circulaire. **C'etait la
     mauvaise frontiere** :
```
     CIRCULAIRE      je compare une valeur QUE J'AI ECRITE a la source dont
                     je l'ai tiree      (la charge, le matin du 14/11)
     PAS CIRCULAIRE  la donnee vient d'ailleurs -- meme si elle a servi a
                     choisir            (les noms, qui viennent de Hektor)
```
     ⭐ **La mesure qui tranchait existait : LA FORCE DE L'INDICE.** Verifier qu'une
       cle est UNIQUE n'est pas repeter la cle.
```
     12 395 couples (acheteur, vendeur) distincts dans le registre
     32 des 39 lignes : LEUR COUPLE NE DESIGNE QU'UN SEUL DOSSIER -> certain
      7 : nous n'avons pas les deux noms -> la, vraiment, il faut un humain
```
     ➡ *Avant d'appeler un rattachement « incertain », mesurer combien de cibles
       l'indice laisse possibles. Et ne demander a l'humain que ce que la mesure
       ne peut pas donner.* **Frederic l'a vu avant moi** : « ils sont tous juste,
       pourquoi tu doutais, a cause du mandat ? »

   La page de relecture : <https://claude.ai/artifact/S7dZk15yuciuByzYXq8uva>
   (39 verdicts enregistres), et le document
   `notice/A6_BIENS_INCERTAINS_A_RELIRE_2026-11-14.md`.

## ⚠⚠ 3.1octies CE QUE LA POSE CHANGE POUR **LE CALCUL** — *mesuré le 14/11*

   **Question de Frédéric : « le calcul a-t-il été réactualisé ? »** Trois réponses,
   parce qu'il y a trois calculs, et ils ne se comportent pas pareil.

   ✅ **① LE CALCUL AFFICHÉ (pilotage, fiches) EST DÉJÀ À JOUR, SANS RIEN FAIRE.**
     `pilotage.ts:148` et `api.ts` (4 endroits) lisent `app_affaire_repartition`
     **en direct**, et il n'existe **AUCUNE vue matérialisée** dans tout
     `supabase/`. Le calcul se refait **à chaque ouverture de l'écran** : les
     9 165 lignes comptent dès la seconde où elles sont posées. Rien à relancer.

   ✅ **② LE CALCUL DU RUN TOURNE, ET IL A RESPECTÉ NOS LIGNES.**
     `phase2/sync/repartition_commission.py` (run de nuit,
     `run_full_pipeline.ps1:1357`) écrit bien dans cette table — mais il passe
     par la RPC `app_repartition_absorber`, **qui porte la garde** :
```sql
     if exists (select 1 from app_affaire_repartition r
                 where r.app_chaine_id = v_chaine
                   and coalesce(r.origine,'') not like 'hektor%')
     then v_protege := v_protege + 1; continue; end if;
```
     ⭐ **Elle protège TOUTE origine qui ne commence pas par « hektor »** — donc
       `classeur_reconstitue` comme `saisie`. Par **conception**, pas par chance.
     ⭐ **Et le témoin réel existe** : le run du 14/11 (06:31, donc AVANT la pose
       des 30) a vu les 9 100 lignes du 13/11 et n'a écrit que **2 lignes**.
       `hektor_partage_suppose` porte bien une écriture du 14/11 : le calcul
       tourne et met à jour les 8 715 lignes dont il a la charge.

   ⚠⚠ **③ MAIS LA CONTREPARTIE EST RÉELLE : CE QUI EST PROTÉGÉ N'EST PLUS
     RECALCULÉ.** Les chaînes que nous possédons sont désormais **SAUTÉES** par
     le calcul du run — leur répartition est **FIGÉE sur le classeur**. Si Hektor
     change les honoraires d'une de ces affaires, **notre répartition ne suivra
     pas**.
```
     chaines PROTEGEES (origine non-hektor)       4 477   = 50,7 %
     chaines que le run peut encore recalculer    4 359
     DONT, parmi les 4 477 :
        3 720  ont une VENTE          -> closes, rien ne bougera jamais
           96  COMPROMIS ENCORE ACTIF -> VIVANTES : LE SEUL VRAI ENJEU
          661  ni vente ni compromis actif (offres tombees, anciennes)
```
   ⬜ **RÉSERVE NOMMÉE, et elle se chiffre à 96, pas à 4 477 ni à 0** : ces 96
     chaînes ont un compromis actif et une répartition figée. ⭐ *C'est le genre
     de chiffre qui rend une inquiétude actionnable* — surveiller 96 chaînes est
     faisable, « surveiller la moitié du registre » ne l'est pas.
     ➡ À trancher par Frédéric : **une sentinelle** qui crie si Hektor change les
       honoraires d'une de ces 96, ou **rien** (le classeur fait foi, point).
   ⛔ **Ce n'est PAS un défaut : c'est la décision du 02/11 (« LE CLASSEUR FAIT
     FOI ») qui s'applique.** On a échangé « suivre Hektor » contre « le classeur
     fait foi » sur ces chaînes. Il faut juste que ce soit **su**, et non découvert
     dans six mois.

## ✅✅ 3.2 LA RESERVE DES 413 ECARTS EST FERMEE — **14/11, et elle cachait un defaut**

   ⛔ **J'ALLAIS LA COCHER SUR LA FOI D'UNE NOTE. Frédéric a demande un VRAI
     audit, et il avait raison** : la note du 09/11 la declarait levee en faisant
     `413 - 211 = 202` puis « ca recoupe mes 265 a moins de sept jours ».
     **202 n'est pas 265** — c'etait une deduction qui ne bouclait pas.

   ✅ **LA MESURE, elle, boucle a l'unite** (14/11, sur le perimetre du rapport) :
```
     LARGE    (tout ecart non nul)   228
     TOLERANT (ecart > 3 jours)      104
     absorbes par la tolerance       124  =  228 - 104     EXACT
     la tolerance est bien dans le code : abs((dc - dn).days) <= 3
```
   ⚠ **ET LES DEUX CHIFFRES D'ORIGINE ETAIENT PERIMES** : la reparation
     « propositions » du 12/11 (lire la PREMIERE PROPOSITION et non le dernier
     mouvement) a servi **549 fois**. Les 413 et 211 avaient ete mesures AVANT,
     sur une date fausse de notre cote.

   ⛔⛔ **LE DEFAUT QUE L'AUDIT A TROUVE, et il etait plus grave que la reserve :
     LE RAPPORT NE LISAIT PAS UNE DATE DU CLASSEUR SUR CINQ.**
```
     le classeur ecrit « 05/12/2023 » MAIS AUSSI « 5 decembre23 »
     date_du_classeur() ne lisait que la premiere forme -> None sur l'autre
        Offre Achat   968 cases PERDUES sur 4 755  (20 %)
        Compromis 745 . Vente Prevue 824 . Vente Fixee 768 . Vente Reglee 794
     A L'ECRAN : 940 lignes rangees en « nous seuls » -- « nous avons une date,
        le classeur rien » -- alors que 924 D'ENTRE ELLES EN PORTENT UNE.
        Il ne comparait que 3 570 lignes au lieu de 4 494.
```
   ✅ **CORRIGE LE 14/11** : `date_du_classeur_tolerante()` essaie l'ancien parseur
     PUIS les mois ecrits en clair. Elle est **additive** (eprouvee sur les deux
     formats) avec son **temoin inverse** (le 31 fevrier, le 5 brumaire et
     « 32/13/2024 » restent refuses), et branchee sur **ses 2 appelants**, les
     seuls (regle des jumeaux appliquee : `date_du_classeur` n'avait pas d'autre
     lecteur dans tout le depot).
```
     L'EFFET MESURE, avant -> apres :
        Offre Achat   nous seuls  940 -> 16   identique 3 466 -> 4 366
                      ECART 104 -> 128 = le decompte tolerant predit, A L'UNITE
        Compromis     nous seuls  790 -> 65
        Vente Fixee   nous seuls  770 -> 7
        Vente Prevue  nous seuls 1 011 -> 201
```
   ⚠ **CE QUE L'AUDIT A AUSSI DEMENTI** : l'argument qui fermait la reserve au
     09/11 — « les vrais ecarts sont tous sur des affaires annulees » — est FAUX.
     Sur les **26 ecarts a plus d'un mois, 15 sont des VENTES REGLEES**, 9
     annulees. ⭐ Et **trois sont des decalages d'ANNEE EXACTS** (un de 7 305
     jours = vingt ans pile : classeur 2022-01-31, nous 2002-01-31 ; deux de
     366 jours) : des fautes de saisie, pas des desaccords de date.
   ⬜ **RESERVE NEUVE, nommee, NON bloquante pour ce qui est pose** : ces 26
     ecarts restent a regarder AVANT de poser le lot 3 (les dates). Les 3
     decalages d'annee se corrigent a l'unite.
   ⚠ L'apparieur (`apparier_classeur.py`) n'a PAS le meme defaut dans le meme
     sens — il convertit NOS dates vers le format du classeur et compare en
     texte — mais il perd l'indice de date sur ces lignes. Mesure : ca n'explique
     que **8 des 87 non rattachees** (9,2 % contre 2,4 % chez les rattachees).
     **Un facteur mineur, PAS la cause des 87.**

   ✅ **ET LA RESERVE 1 DU 09/11 EST CORRIGEE DU MEME COUP** : le rapport lisait
     `charge_commission_app` du LEDGER (7 lignes remplies sur 31 157) au lieu de
     `mandat_charge_honoraires_app` du REGISTRE DES MANDATS (23 473 / 24 596).
     La charge est une donnee DU MANDAT, pas de la transaction.

3.2bis ⬜ ACCORD    LA CHARGE DE COMMISSION -- ⭐⭐⭐ **16 LIGNES A POSER, PAS 955.**

   ⛔ **ET MON PREMIER CHIFFRE DU 14/11 (« 46 ») ETAIT FAUX** : je l'avais deduit
     du rapport du gel au lieu de relancer **le script qui existe deja**,
     `phase2/checks/poser_charge_classeur_2026-11-04.py` -- lequel porte ses
     gardes et la notion de CONFIANCE DU LIEN. ⭐ *Lecon 15 du projet : chercher
     si le projet a DEJA tranche avant de proposer une forme.* Son verdict :
```
     classeur : 971 renseignees (955 au 03/11 -- il a grossi), 0 refusee
     A POSER en 1re passe (confiance « sure ») : 16   (15 vendeur, 1 acquereur)
     ecartees :
        898  le carnet porte DEJA une valeur -- ON N'ECRASE PAS
         25  lien HORS 1re passe (« a valider » / « bonne »)  -> LOT 2, sa decision
         21  la ligne n'est pas reliee par le gel
          4  EXCLU PAR DECISION (classeur contradictoire)
          4  l'affaire ne cite ni annonce ni mandat
          3  le mandat n'est pas au registre
     temoins : VENDEUR annonce 47132 / mandat 18874 . ACQUEREUR 49852 / 17823
     temoin INVERSE : lignes VIDES au classeur qui seraient posees = 0
```
     Patch pret, **NON JOUE** : `supabase/patch_charge_classeur_2026-11-14_DONNEES.sql`
     (16 `insert ... on conflict do nothing`, puis la repose du reflet).

   ⛔⛔ **UN PIEGE OU JE SUIS TOMBE, ET QUI EST CORRIGE** : les deux sorties du
     script etaient **figees au « 2026-11-04 »**. Une simple relecture -- le
     script ne fait QUE mesurer -- a donc **ECRASE LE PATCH DU 04/11**, celui qui
     a ete REELLEMENT JOUE (commit `658a14e`), par un patch de 16 lignes.
     ✅ Restaure par `git restore`, et les sorties portent desormais **le jour de
       la passe**. ⭐ *Une trace historique ne se regenere pas : elle se garde.*

   La mesure du rapport du gel, qui reste utile pour l'ECART :
```
                    identique      904        <- rien a faire
                    classeur seul   44        <- ⚠ PAS « 44 a poser » : le script
                                                 n'en retient que 16 (1re passe),
                                                 le reste est ecarte pour une
                                                 RAISON NOMMEE (voir ci-dessus)
                    ECART            2        <- a redresser, le classeur fait foi
                      KBZR2ND6 mandat 17217  classeur=Acquereur nous=vendeur
                                             VENTE REGLEE -> le seul a enjeu
                      JEK94D31 mandat 24247  classeur=Vendeur   nous=acquereur
                                             annulee -> sans enjeu financier
                    ⭐ Le vocabulaire CONCORDE : « vendeur »/« acquereur » des
                      deux cotes (mesure du 14/11) -- le piege ① du 02/11 tombe.
```
   ⛔⛔⛔ **ET LE « 904 IDENTIQUE » NE PROUVE RIEN : IL EST CIRCULAIRE.** J'ai
     failli en conclure que le classeur et Hektor etaient d'accord a 99,8 %.
     ⭐ **Ce qui m'a arrete : un accord ne passe pas de 96,8 % (le juge du 03/11)
       a 99,8 % sans raison.** La mesure de la provenance, au carnet du mandat :
```
     origine de NOTRE valeur, sur les 897 « identique » du 1er jet
        classeur        874     <- LE CLASSEUR COMPARE A LUI-MEME
        hektor           11     <- le seul vrai accord INDEPENDANT
        pas au carnet    12
     (le carnet en tout : hektor 22 637 . classeur 837 . mandat_app 1)
```
     ⛔ **Cause : `patch_charge_classeur_2026-11-04.sql` a DEJA pose 837 charges
       du classeur le 04/11.** Comparer le classeur a notre base, c'est donc le
       comparer en partie a lui-meme.
     ➡ ⭐⭐ **LE JUGE DU 03/11 RESTE LA SEULE MESURE VALABLE** de l'accord
       classeur <-> Hektor : **368 / 380 comparables = 96,8 %**, parce qu'il
       lisait Hektor **directement**. Ne pas le remplacer par un chiffre tire
       de notre base.

   ⛔ **UN NUMERO DE MANDAT N'IDENTIFIE PAS UN MANDAT** (mesure du 14/11) :
     24 596 mandats pour **18 287 numeros distincts**, **4 142 numeros en
     doublon**, jusqu'a **10 exemplaires** pour le seul 10249. Le rapport ne
     retient donc une charge par numero que si TOUS les exemplaires qui en
     portent une sont **d'accord** -- sinon il ne rend rien et le compte :
     **33 numeros recycles aux charges divergentes**, a regarder avant de poser.
   ⚠ Et l'index par annonce du rapport (`setdefault`) masquait **94 mandats**
     (56 annonces en portent plusieurs) : 7 lignes etaient annoncees
     « classeur seul » a tort, 15 « les deux vides ». Corrige le 14/11.

                    La proposition A11 du 03/11, pour le reste :
                    ① POSER LES 46 DU CLASSEUR (~1/2 h) -- ILS FONT FOI
                    ② l'ecran montre la valeur AVEC sa source (~1/2 j)
                    ③ le preremplissage : SAISIE > CLASSEUR > « Hektor dit
                       acquereur » > defaut vendeur (~1/2 j)
                    ④ les etiquettes (~2 h, une a reconfirmer)
                    ⑤ Hektor en SIGNALEMENT seulement (~2 h)
                    ⛔ A LIRE AVANT TOUTE REPRISE : A8, A10, A11 et le rapport
                      du juge (JUGE_CHARGE_CLASSEUR_HEKTOR_2026-11-03.md)
⭐⭐⭐ 3.0 ⬜ ACCORD  **LES EMPLACEMENTS -- LA TACHE QUI MANQUAIT AU PLAN**, trouvee
                    le 15/11 par la question de Frederic : *« je ne vois pas quand
                    ni comment on cree les emplacements pour les colonnes qui
                    manquent dans l'app »*. ⛔ Le document du 02/11 l'avait DEJA
                    ecrit (§ 4 bis, « CE QUI BLOQUE ENCORE L'EXECUTION -- NEUF
                    CHAMPS ») et le plan d'action ne la portait pas.
                    ⚠ **NEUF champs, pas six.** Et deux FORMES differentes, selon que
                    la donnee appartient a UNE TRANSACTION ou au DOSSIER :
```
   ⛔⛔ **LE COMPTE EXACT, VERIFIE COLONNE PAR COLONNE EN BASE LE 15/11** (ma
   premiere reponse disait « 4 a creer » : c'etait une FAUTE DE SOUSTRACTION,
   j'avais oublie Y, AA et Z). **9 = 3 qui ONT DEJA LEUR CASE + 6 A CREER.**

   A. ⭐⭐ **TROIS ONT DEJA LEUR CASE -- RIEN A CREER**
      Z   Annulee         ->  **date_annulation_app** (+ motif_annulation_app),
                              posees le 10/11 (liste B de A18) « AVANT tout
                              remplissage », **VIDES toutes les deux** (0 ligne),
                              et dans la liste des colonnes QUE LE PUSH N'ENVOIE
                              JAMAIS -> classe A, deja protegee.
                              ⚠ En face : 3 705 affaires `cancelled`/`refused`
                                qui ne disent pas QUAND. Les 896 dates du classeur
                                entrent sans aucun conflit.
                              ⛔ ET LE COMMENTAIRE DU CODE EST A NUANCER : il dit
                                « motif_annulation_app n'a AUCUNE AUTRE SOURCE :
                                ni le classeur ni Hektor ne portent la raison » --
                                or **F du classeur porte les motifs** (retractation
                                129, pret refuse 107, mesure du 02/11).
      F   En attente de   ->  app_affaire_condition  (voir B)
      G   COMMENTAIRES    ->  app_affaire_note       (voir B)

   B. COLONNE AU REGISTRE, de CLASSE A -- **A CREER**
      Y   Vente Reglee       ⚠ 100 % de nos cases vides : VOULU et DECLARE
                             ⭐ verifie le 15/11 : AUCUNE colonne nulle part
      AA  N0 de facture      ⚠ idem, AUCUNE colonne nulle part
      C   numero_mandat_app  ⛔ PREALABLE DU 29/10 JAMAIS FAIT : numero_mandat est
                             de CLASSE C (relu chaque nuit) -> une ecriture y est
                             EFFACEE au run suivant. Verifie le 15/11 : la colonne
                             `numero_mandat_app` N'EXISTE PAS.
   B. ⭐⭐⭐ **F ET G ONT DEJA LEUR CASE -- RIEN A CREER** (piste de Frederic du
      15/11 : « F et G ont deja ete etudiees et pourraient remplir les conditions
      suspensives ». ELLE EST JUSTE, et le plan du Sheet le notait deja :
      « A VOIR les conditions suspensives (G15) -> En attente de ? »)
      F   En attente de   ->  **app_affaire_condition** : libelle, jours,
                              date_echeance, etat, date_levee, note, catalogue_id,
                              **origine** -- la structure complete EXISTE
                              ⭐ et HEKTOR N'EN REMPLIT AUCUNE : conditions_suspensives
                                est vide sur 18 589 lignes de app_affaire_console
                                -> AUCUN CONFLIT POSSIBLE, comme la charge du mandat
                              + app_condition_catalogue pour les libelles
      G   COMMENTAIRES    ->  **app_affaire_note** : 9 lignes, du 23/10 au 02/11
   C. TABLE A PART, cle id_unique -- **A CREER** (verifie le 15/11 : aucune
      colonne « avis » n'existe dans TOUTE la base)
      AH  Avis a envoyer     120 valeurs distinctes, pas une case a cocher
      AI  Commentaire Avis   392 cases
      AJ  Avis envoye        des PRENOMS dedans (Marion 190, Nico 59...)
      ⛔ F et G se reprennent EN BLOC, sans interpreter -- sa consigne
      ⚠ AH et AJ se contredisent sur 229 lignes -- a reprendre tels quels
```
                    ⭐ MESURE DU 15/11 QUI SIMPLIFIE : `app_affaire_champ_app` et
                    `app_mandat_champ_app` n'ont **AUCUNE contrainte CHECK** sur le
                    nom du champ -- rien a modifier de ce cote.
                    ⛔⛔ MAIS LE CARNET DES AFFAIRES N'EST PAS LA BONNE PLACE : c'est
                    une FILE D'ENVOI vers Hektor (« une saisie cherche a le rejoindre
                    et DISPARAIT une fois arrivee »). Voir 3.3quater.
                    ➡ **CETTE TACHE PASSE AVANT 3.3, 3.3ter, 3.4 ET 3.5.** Seule la
                    commission P peut avancer sans elle : sa case existe deja.
⛔⛔ 3.0ter ⬜ ACCORD  **DEUX DEFAUTS TROUVES LE 15/11 EN AUDITANT F ET G.**
```
   a) 5 CONDITIONS SUSPENSIVES ET 6 NOTES SONT ORPHELINES
      app_affaire_condition : 5 lignes, 5 ORPHELINES, 0 rattachee
      app_affaire_note      : 9 lignes, 6 ORPHELINES, 3 rattachees
      Leurs affaires (1001388, 1001391, 1001394) N'EXISTENT PLUS au registre,
      ni dans Supabase ni dans le SQLite local. Les conditions sont restees.
      ➡ RIEN ne nettoie ni ne SIGNALE une condition dont la transaction part.
        Si on pose 241 transactions + leurs conditions, le defaut se multiplie.
        Il faut une sentinelle AVANT d'ecrire (meme forme que
        app_v_repartition_orpheline, qui existe deja pour la repartition).

   b) ⛔⛔ MA RESERVE DU 15/11 N'EST PAS LEVEE, ELLE EST AGGRAVEE
      J'avais ecrit en 3.3quater que le run ne peut pas effacer une ligne de la
      plage app. MESURE DU 15/11 :
         plage app, dans Supabase : 340 lignes, 0 SANS numero Hektor
         plage app, en LOCAL      : 340 lignes, 0 SANS numero Hektor
         et 3 lignes de cette plage ONT DISPARU -- sans sauvegarde, sans
         journal, sans trace de QUI les a retirees
      ➡ Les protections du code sont reelles (je les ai lues), mais AUCUN TEMOIN
        POSITIF n'existe : pas une seule ligne de la plage app n'a jamais vecu
        sans numero Hektor. **L'essai de 3.3zero est donc OBLIGATOIRE**, et il
        doit mesurer les DEUX bases, locale et Supabase.
```

⚠⚠ 3.0bis ⬜ ACCORD  **LA FENETRE DE LECTURE DU SHEET, ET ELLE SE REFERME.**
                    L'apparieur ne lit que `A1:AL6000`. Le classeur portait 4 783
                    lignes le 09/11 -> **~1 200 lignes de marge**. Le jour du
                    depassement, **les lignes du bas disparaissent sans un mot**,
                    comme toute colonne ajoutee a droite de AL. Reserve ecrite le
                    31/10, jamais corrigee. Deux caracteres a changer, mais un appel
                    a l'API Google : son accord.

3.3zero ⬜ ACCORD   ⭐⭐⭐ **LE PREALABLE DE 3.3 : L'ESSAI D'UNE NUIT.** Creer UNE
                    transaction dans la PLAGE APP (>= 1 000 000) SANS numero Hektor,
                    sur un bien NON VIVANT, et la mesurer au matin. Leve la seule
                    reserve de l'audit du 15/11 : les 340 lignes de la plage portent
                    TOUTES un numero Hektor, donc rien ne prouve ENCORE qu'une ligne
                    sans numero survit a une nuit. Un zero ne se croit pas sans
                    temoin positif. ➡ Il debloque 3.3, 3.3ter ET une partie de 3.5.
3.3 ⬜ ACCORD       les colonnes qui ONT une case -- ⭐⭐ AUDITEE LES 14 ET 15/11.
                    Le perimetre du plan etait perime (4 colonnes, pas 7) et MON
                    propre perimetre etait faux : j'avais sorti les 241 transactions
                    a creer, ce qui n'etait PAS la decision de Frederic (rectifie le
                    15/11). LE VOLUME REEL, mesure sur TOUT le Sheet le 15/11 :
```
                      P  Commission TTC    303 valeurs  -> classe A
                      T S W  les cases vides  10 dates  -> classe A
                      offres manquantes          144                        compromis manquants         62   > 241 TRANSACTIONS A CREER
                      ventes manquantes           35  /    (plage app, voir 3.3zero)
                      AF Prix                    161 ecarts -> on LISTE, on n'ecrit pas
```
                    ⚠ LES 3 LOTS NE SE VALENT PAS : les 144 offres et les ~36
                    compromis annules sont des creations franches ; les 26 ventes
                    dont le compromis porte DEJA une autre date d'acte sont un
                    CONFLIT, pas un vide. ➡ Trois lots separes, jamais un seul geste.
                    ⚠ ET 85 LIGNES DU SHEET NE SONT RATTACHEES A RIEN : hors de tous
                    ces chiffres, contenu inconnu depuis notre base. A mesurer.
3.3bis ⬜ FREDERIC  ⛔ **V « Vente Prevue » est decidee « TOUT » et n'est dans
                    AUCUNE tache** -- trou du plan trouve le 14/11. 2 303 ecarts,
                    le plus gros conflit des 38. Voir la section 3.3.
3.3ter ⬜ FREDERIC  ⛔ **Z « Annulee » est decidee « TOUT » et n'est dans
                    AUCUNE tache** -- second trou du plan, trouve le 14/11 en
                    repondant a l'etonnement de Frederic (« il n'y a que ca qui
                    diverge ? »). 896 dates, 100 % lisibles, 2020-2026, et AUCUNE
                    case en face : sa note de l'artefact dit « Annulee tout avec un
                    nouveau champ ». Elle fait partie des SIX champs a creer
                    (F G Z AH AI AJ, voir 3.1quater B) mais la tache 3.5 n'en nomme
                    que CINQ : Z y manque.
3.4 ⬜ ACCORD       Y le reglement et AA la facture, sur la transaction de role
                    'vente'
                    ⛔ **CORRIGE LE 15/11 : CETTE LIGNE DISAIT `app_affaire_champ_app`,
                    ET C'ETAIT FAUX DEUX FOIS.** (a) ce carnet est une file d'envoi
                    vers Hektor, pas un magasin ; (b) le document du 02/11 dit que Y
                    et AA n'ont **aucun champ en face chez nous** -> il faut d'abord
                    les CREER (voir 3.0, forme A).
                    ⚠ MESURER D'ABORD les 1 062 lignes sans role 'vente' : ou va la
                    valeur quand la transaction qui la porte n'existe pas ?
3.5 ⬜ FREDERIC     le carnet des 5 colonnes de dossier (F G AH AI AJ), cle id_unique
                    + la case du numero de mandat (C, « les vides », ~9 utiles)
```

## ⭐⭐⭐ 3.3 LES COLONNES QUI ONT UNE CASE — **AUDIT DU 14/11, LE VOLUME TOMBE DE 605 À 315**

> Mesure rejouable : `python -X utf8 phase2/checks/audit_33_colonnes_qui_ont_une_case.py`
> **Lecture seule de bout en bout.** Il lit le rapport du gel du jour et la base.

## ⭐⭐⭐ 3.3quater PEUT-ON CRÉER UNE TRANSACTION ENTIÈRE CHEZ NOUS ? — AUDIT DU 15/11

> **Question de Frédéric, 15/11** : *« Je n'ai juste dit de ne pas faire le geste
> dans Hektor mais il faut bien remplir offre compromis etc. dans le registre des
> transactions. Peut-on écrire chez nous comme tu me l'as proposé en classe A et
> enregistrer des transactions entièrement ? »**
>
> ✅ **RÉPONSE : OUI, ET LE MÉCANISME EXISTE DÉJÀ.** Lecture seule du code et de la
> base, aucune écriture. Cinq mesures, et une réserve nommée.

### ⭐ ① DEUX OUTILS DIFFÉRENTS, POUR DEUX BESOINS DIFFÉRENTS

J'avais confondu les deux. Ils ne servent pas à la même chose :

```
LA CLASSE A       proteger UNE VALEUR dans une ligne QUI EXISTE
                  -> les 303 commissions, les 12 dates de case vide
LA PLAGE APP      creer LA LIGNE ENTIERE, la transaction elle-meme
                  -> les 241 offres / compromis / ventes absentes
```

### ⭐⭐ ② LA PLAGE EST DÉJÀ RÉSERVÉE, ET ÇA N'EST PAS UN BRICOLAGE

`phase2/sync/affaire_ledger.py:48` — **`PLAGE_RESERVEE_APP = 1_000_000`** :

```
  en dessous : les affaires vues chez Hektor, numerotees par le run (a 28 981)
  au-dessus  : les affaires NEES DANS L'APP, numerotees par la sequence
               Supabase app_affaire_id_app_seq
  « Le run ne distribue JAMAIS au-dessus de cette frontiere. »
```

Et le commentaire d'identité du 20/08 dit la chose en toutes lettres :

> *« Les deux colonnes Hektor deviennent facultatives : une affaire saisie dans
> l'app existe AVANT que Hektor ne la numérote, **et parfois sans que Hektor la
> numérote jamais**. »*

**Mesure du 15/11 : 340 lignes vivent déjà au-dessus du million** (148 offres,
123 compromis, 69 ventes), sur 30 817 dans la plage Hektor.

### ⭐⭐⭐ ③ LE RUN DE NUIT NE PEUT PAS LES EFFACER — QUATRE PROTECTIONS LUES

**a. Le marquage ne les regarde même pas.** La première garde du passage qui met
`present_in_hektor=0` est littéralement `app_affaire_id < 1 000 000`
(`affaire_ledger.py:1033`). Une ligne de notre plage n'est pas candidate.

**b. Et de toute façon, ce passage NE SUPPRIME RIEN.** Son propre commentaire :
*« les lignes non revues ce run passent present_in_hektor=0 (**conservées**) »*
(l. 584). Le drapeau dit « je ne l'ai pas revue », il n'efface pas.

**c. La seule suppression du fichier EXIGE un numéro Hektor**, et refuse d'agir
sans lui : *« on ne supprime pas « au numéro d'app » : ce serait viser large »*
(l. 3080-3094). Une ligne **sans** numéro Hektor est donc **insupprimable par ce
chemin**, par construction.

**d. Trois signaux de possession s'ajoutent** (l. 1033-1053) : une ligne au carnet,
un travail `pending`/`running`, et les deux copies du carnet lues en union. Plus
une règle de méthode déjà posée : *« Une protection muette ne se distingue pas
d'une protection absente »* — le run **dit** combien il a protégé.

### ⭐ ④ ET RIEN NE PART CHEZ HEKTOR

Le seul mécanisme qui regarde vers Hektor est `poserNumerosManquants`
(`console_job_worker.js:24048`). Il cherche les lignes
`hektor_affaire_id=is.null & present_in_hektor=is.false & app_affaire_id=gte.1000000`
et **LIT** l'API pour voir si Hektor porte déjà la transaction. Il **ne crée
rien** : si Hektor n'a rien, il ne trouve rien et laisse la ligne tranquille.

### ⚠⚠ ⑤ LA RÉSERVE, ET ELLE EST HONNÊTE : AUCUN TÉMOIN SUR LA DURÉE

**Les 340 lignes de la plage app portent TOUTES un `hektor_affaire_id`.** Donc la
conception le permet et le code le protège, mais **aucune ligne n'est jamais
restée sans numéro Hektor sur plusieurs nuits**. Le zero ne se croit pas sans
témoin positif (leçon du projet).

➡ **CE QUI LÈVE LA RÉSERVE, ET ÇA COÛTE UNE NUIT** : créer **UNE** transaction
d'essai dans la plage app, sans numéro Hektor, et la mesurer au matin. Si elle est
intacte, les 241 peuvent y aller. ⚠ À ne PAS prendre un bien vivant.

### ➡ LE VOLUME RÉEL DE 3.3, UNE FOIS LE PÉRIMÈTRE RÉTABLI

```
P  Commission TTC   « vides »    303 valeurs   -> classe A, ligne existante
T  Compromis        « vides »      8 cases     -> classe A
                                 + 62 lignes   -> A CREER (plage app)
S  Offre Achat      « vides »      4 cases     -> classe A
                                +144 lignes    -> A CREER (plage app)
W  Vente Fixee      « vides »      0 case
                                 + 35 lignes   -> A CREER (plage app)
AF Prix             « comparer »  161 ecarts   -> AUCUNE ecriture, on LISTE
                                 ----
                     315 valeurs + 241 transactions entieres
```

### ⛔ ① LE PÉRIMÈTRE DU PLAN ÉTAIT PÉRIMÉ — 4 colonnes, pas 7

La ligne du plan disait *« les 7 colonnes qui ONT une case : P S T W AB AD
(+ AF comparer) »*. La **source de vérité est l'artefact des 38 choix**, relu le
14/11 — et il dit, depuis le **09/11 à 13:13** :

```
   P Commission TTC   vides        S Offre Achat   vides
   T Compromis        vides        W Vente Fixee   vides
   AF Prix            comparer
   AB Acquereur       RIEN   <- sorti du perimetre le 09/11
   AD Vendeur         RIEN   <- sorti du perimetre le 09/11
```

➡ **3.3 porte QUATRE colonnes à poser et UNE à comparer.**

### ⛔⛔⛔ ② « classeur seul » NE VEUT PAS DIRE « une case vide à remplir »

**C'est la trouvaille de l'audit, et elle divise le travail par vingt-quatre.**
Le rapport cherche la date de l'offre sur la transaction **offre reliée par le
gel**. Quand cette transaction n'existe pas, il rend « classeur seul » — ce qui se
lit *« il nous manque la donnée »* alors que, le plus souvent, **il nous manque la
transaction entière**. Trois choses très différentes sous un seul mot :

```
                        annonce   A case vide   B existe dans   E aucune
                        au        a remplir     la chaine       transaction
                        rapport                 (gel muet)      de ce role
   S Offre Achat          178          4            30             144
   T Compromis             75          8             5              62
   W Vente Fixee           38          0             3              35
                         ----        ---           ---             ---
                          291         12            38             241
```

- **A — 12 dates, et elles seules, sont une case à remplir.** C'est le vrai volume.
- **B — 38 lignes où le rapport se trompe** : nous avons la transaction ET sa date,
  le gel ne l'a simplement pas reliée à cette ligne. **5 disent la même date**
  (rien à faire), **31 une autre date** → ⬜ réserve, à regarder au fond.
  ⚠ Et **8 de ces 31 portent chez nous le 11 ou le 12/11/2026** : c'est la *date du
  refus* posée par notre propre chaînage ces jours-là. Voir la mémoire
  `date-offre-refusee-est-la-date-du-refus`.
- **E — 241 lignes n'ont AUCUNE transaction de ce rôle**, et ce n'est pas un trou
  au hasard : la chaîne existe, elle s'arrête ailleurs.

```
   S les 144 sans offre        : la chaine porte compromis 87 . compromis+vente 53 . vente 4
   T les  62 sans compromis    : la chaine porte offre 60 ; au classeur, 35 « Annulee »
                                 et 23 « Compromis en attente » (une date PREVUE)
   W les  35 sans vente        : 26 ont une DATE D ACTE au compromis, DIFFERENTE
                                 5 la meme . 2 sans date d acte . 2 sans compromis
```

➡ **Poser ces 241 dates demande de CRÉER 241 transactions** dans notre registre
des affaires.

⛔⛔ **RECTIFIÉ LE 15/11 — J'AVAIS ÉCRIT ICI « hors de la décision les vides »,
ET C'ÉTAIT MA DÉCISION, PAS CELLE DE FRÉDÉRIC.** Ses mots du 15/11 :
*« Non !!!!! J'ai juste dit de ne pas faire le geste dans Hektor mais il faut
bien remplir offre compromis etc. dans le registre des transactions !!! Tu as
changé le plan au pire moment. »*

➡ Donc le périmètre est : **on CRÉE les transactions manquantes CHEZ NOUS**, en
classe A, **sans aucun geste chez Hektor**. Les 241 sont DANS la tâche, pas à
côté. Faisabilité : voir l'audit profond du 15/11 (section 3.3quater).

### ③ P COMMISSION TTC — 279 vrais vides, 1 886 204 €

```
   314 annoncees « classeur seul »
      279   vrai vide : aucune transaction de la chaine ne porte de commission
       22   une VOISINE porte LA MEME -> le rapport se trompe
       13   une voisine en porte une DIFFERENTE
   par annee : 2026 77 (539 070 EUR) . 2022 50 . 2021 51 . 2023 40 . 2020 33 . 2024 17
```

⚠⚠ **ET LE ZÉRO EST UN VIDE DÉGUISÉ** — *un zéro ne se croit pas sans témoin
positif.* **24 lignes de plus** sont rangées « ECART » alors que **nous portons 0**
(217 250 € au classeur). Un 0 n'est pas une saisie, c'est une absence : le compte
des « vides » les rate. ➡ **Mon avis : les traiter comme des vides** → **303**
commissions, et non 279.

### ④ AF PRIX — on ne pose RIEN

`comparer` : 3 780 hors périmètre (avant 2025, le classeur portait un prix
d'annonce), **760 identiques, 161 écarts** à lui montrer. Aucune écriture.

### ⛔⛔ ⑤ LA CASE EXISTE, MAIS LE ROBINET EST FERMÉ — *le point de forme à trancher*

La table d'accueil existe et est éprouvée : **`app_affaire_champ_app`**, et sa
carte `CARNET_VERS_REGISTRE` (`console_job_worker.js:16813`) accepte déjà
**`date`**, **`date_acte`** et **`honoraires_entree`** — exactement nos champs.

⛔ **Mais ce que l'app y écrit n'est reposé par personne aujourd'hui :**

```
   phase2/identite/appliquer_contrat_affaire.py  -- « AUJOURD'HUI CETTE ETAPE NE
       FAIT RIEN, et c'est voulu : la machinerie existe et attend »
   phase2/identite/contrat_autorite.py:180       -- CHAMPS_APP_AFFAIRE = ()   VIDE
   et l'etape n'est PAS dans le run de nuit (0 appel dans scheduled/)
```

Et `affaire_ledger.py` **rafraîchit le registre depuis le miroir à chaque run** :
une valeur écrite au carnet et non reposée serait **invisible le lendemain**.

➡ **Trois chemins, et c'est sa décision :**

```
   A  le chemin PREVU PAR LA CONCEPTION : ecrire au carnet, allumer
      CHAMPS_APP_AFFAIRE sur les 3 champs, mettre l'etape au run.
      ⚠ C'est le PENDANT de CHAMPS_APP_ANNONCE, qui reste ETEINT par decision
        du 13/10 -- donc une decision de meme poids.
   B  le chemin DU LOT 1 : ecrire dans la table du registre avec une origine, et
      une garde du run (comme `not like 'hektor%'` sur la repartition, et comme
      `notaires_origine = 'saisie'` qui fige deja une ligne, affaire_ledger.py:235).
      ⚠ Touche le coeur de la synchro des affaires, champ par champ.
   C  ne rien poser : garder le classeur comme source consultable sur ces colonnes.
```

⭐ **Pour la charge (3.2bis) la question ne s'était pas posée** : elle passe par
`app_mandat_champ_app` **et** la RPC `app_reposer_charge_mandat_app`, qui existe et
tourne. Côté **affaire**, cette RPC n'a pas d'équivalent.

### ⛔ ⑥ RÉSERVE NOMMÉE — V « Vente Prévue » N'EST DANS AUCUNE TÂCHE

Trou du plan trouvé le 14/11. L'artefact la décide **« tout »** ; le plan d'action
ne la cite nulle part (ni 3.3, ni 3.4, ni 3.5). Et c'est **le plus gros conflit
des 38** :

```
   V Vente Prevue : ECART 2 303 . identique 1 682 . les deux vides 495
                    nous seuls 201 . classeur seul 21
```

⭐ **Et l'appariement du rapport est le BON, c'est mesuré** : notre
`compromis.date_acte` colle à **V Vente Prévue 1 445 fois** contre **W Vente Fixée
147 fois**. Les deux colonnes du classeur sont bien **deux notions** — elles
diffèrent dans **3 087 cas sur 3 696** où les deux sont remplies : la prévision,
puis la date fixée. **Nous n'avons qu'une case pour les deux.**

⬜ **À trancher par lui** : « tout » sur V signifierait **écraser 2 303 de nos
dates d'acte** par une date que le classeur lui-même dit prévisionnelle. Le
document du 02/11 le notait déjà : *« il est NORMAL : une date prévisionnelle
bouge »*. **Je ne poserais pas V sans l'entendre.**

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
                    ⛔⛔ RESERVE POSEE LE 13/11, A LIRE AVANT D'OUVRIR 5.2 :
                    L'EXPORT DOIT IGNORER LES CHAINES ENTIEREMENT MORTES.
                      14 chaines (16 transactions) portent un numero de dossier
                      alors qu'AUCUNE de leurs transactions ne compte encore
                      (Hektor les a supprimees -- les 18, toutes confirmees une
                      par une par identifiant le 13/11, avec temoin positif).
                      Biens : 1970, 8494, 35467, 39607, 39684, 40318, 40519,
                              43437, 49584, 58979, 61534, 62049, 62097
                      Le filtre : public.app_affaire_compte_encore(
                                    hektor_affaire_id, present_in_hektor)
                      -> n'exporter que les chaines qui ont AU MOINS une
                         transaction qui compte encore.
                    ⚠ ET NE RIEN RETIRER EN BASE : l'etiquette est posee sur une
                      CHAINE entiere, et 2 chaines sont MIXTES (2 transactions
                      mortes + 5 VIVANTES, biens 47146 et 58932). Retirer
                      l'etiquette des mortes casserait le numero de 5
                      transactions valides. « Un numero ne se perd jamais » :
                      on FILTRE A LA LECTURE, on n'efface pas.
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
