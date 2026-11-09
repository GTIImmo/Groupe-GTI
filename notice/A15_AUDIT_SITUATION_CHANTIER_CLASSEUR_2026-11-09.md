# AUDIT DE SITUATION — LE CHANTIER CLASSEUR, AU 09/11/2026

**Demandé par Frédéric le 09/11** : *« attention tu tournes en rond !!! nous en sommes
toujours à l'état une, le rattrapage de mon apps des données dans un seul sens
uniquement un rattrapage avant que mon apps devienne le rédacteur de ce classeur. MAIS
NOUS avons déjà étudié toutes les colonnes et plus en détail que dans tes dernières
analyses [...] Un regel a été fait mais je pense qu'il faudrait le reprendre avec les
données actuelles [...] Normalement ce chantier devait être organisé mais tu as perdu
des informations. Fais un audit très approfondi et explique réellement la situation
actuelle. »*

**LECTURE SEULE.** Rien n'a été écrit en base, ni dans le classeur, ni chez Hektor.
Deux fichiers de rapport ont été produits dans `notice/`, datés du jour.

---

# 0. LES QUATRE RÉPONSES, EN HAUT DE PAGE

```
① IL AVAIT RAISON SUR TOUT. Le chantier EST organise, et je l'avais perdu.
   L'organisation vit dans PLAN_CHANTIER_CLASSEUR_2026-10-28.md (taches T0/P1/P2/P3/P4)
   et les DECISIONS dans DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md, qui porte
   en tete : « CE FICHIER EST LA SOURCE DE VERITE DES DECISIONS ».

② NOUS SOMMES A P1.4 -- « le patch de mise en conformite : le classeur remplit les
   vides ET corrige les divergences ». P1.1, P1.2 et P1.3 sont faits. P1.4 attend
   depuis le 28/10, et il attend UNE SEULE CHOSE : la decision du CAS 4 (voir § 4).

③ LE GEL RELANCE AUJOURD'HUI NE BOUGE PAS -- et c'est sa conception. 4 679 lignes
   reliees, les ecarts sont STABLES a 11 jours. MAIS RIEN N'A ETE RATTRAPE : les
   933 charges, les 483 notaires vides, les 33 mandats vides sont TOUJOURS LA.

④ ET LE RAPPORT DE GEL EST FAUX SUR LA COLONNE Q. Il annonce « 933 cases a
   prendre » alors que 23 474 valeurs SONT DEJA POSEES -- il lit la mauvaise case.
   C'est exactement ce qui fait tourner en rond : un rapport qui reclame un travail
   deja fait. Detail au § 5.
```

---

# 1. L'ORGANISATION DU CHANTIER — retrouvée, et elle est bonne

## Les deux phases *(décidées par Frédéric le 22/10)*

```
PHASE A   UNE SEULE FOIS       le Sheet  ──>  le serveur + l'app
                               on rattrape TOUT ce qui est possible
PHASE B   ENSUITE, DEFINITIF   l'app  ──>  le Sheet
                               plus personne ne saisit dans le classeur
```

⭐ **Ce n'est PAS une synchro permanente à double sens.** Et c'est bien ce qu'il
rappelle aujourd'hui : *« un seul sens uniquement, un rattrapage, AVANT que mon app
devienne le rédacteur de ce classeur »*.

## Les tâches, et leur état mesuré le 09/11

```
T0.1  mettre push_suivi_appsheet.py sous git    PAS FAIT (annonce 2 min, le 28/10)
T0.2  commiter les documents de notice/          PAS FAIT
P1.1  la cascade en lecture seule                FAIT (apparier_classeur.py)
P1.2  geler le lien -- app_classeur_lien         FAIT les 29 et 31/10
P1.3  le rapport des ecarts champ par champ      FAIT, et RELANCE aujourd'hui
P1.4  LE PATCH DE MISE EN CONFORMITE             <-- C'EST ICI QUE NOUS SOMMES
P2    la porte sans ecran (une RPC qui APPELLE
      app_modifier_affaire_optimistic)           a faire
P3a   la premiere vague, UNE affaire choisie     a faire
P3b   la reprise complete, par vagues, la nuit   a faire
P4    le routeur + la destination classeur       bloque par le verrou Apps Script
```

⚠ **Et les scripts du chantier vivent HORS git** : `apparier_classeur.py` et
`push_suivi_appsheet.py` sont `??`. Plusieurs notes du chantier aussi (A2, A3, A4...).
Un chantier entier sans filet.

---

# 2. ⛔ CE QUE J'AI FAIT DE MAL — nommé, pour ne pas le refaire

```
J'AI CREE UN SECOND REGISTRE DE DECISIONS. A13_DECISIONS_COLONNE_PAR_COLONNE.md
   (05/11) double DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md, qui se declare
   lui-meme SOURCE DE VERITE. Deux registres = divergence garantie.

J'AI PERDU 7 DECISIONS DEJA PRISES. Au 02/11, 7 colonnes etaient tranchees :
   I J K L M N (lot 1, la repartition et la paie) + Q. A13 n'en connait que 3.

J'AI ABANDONNE L'ORGANISATION PAR LOTS. La revue etait structuree en 7 LOTS
   (repartition/paie, financier, dates, dates+etat, identites, le bien, notes et
   technique). J'ai repris une revue A -> AL, qui perd le sens du regroupement.

A12_TABLE_DE_PROPRIETE (05/11) EST UNE RECOPIE DE A6 § 3 (02/11). Les quatre cas,
   les quatre colonnes (qui_fait_foi / sur_conflit / depuis_quand / la raison), la
   regle de surete « un ecart ne se resout jamais tout seul », le defaut 'lister',
   et jusqu'au MEME exemple (Negociateur 2 : nous 209, le classeur 685) -- tout
   etait deja ecrit le 02/11. Je l'ai presente comme neuf.

J'AI REFAIT DES ANALYSES EXISTANTES, EN MOINS BIEN :
     . colonne D (Nature)  : A5 § 5 disait deja « ON NE FAIT PAS : nature 1 653 ».
     . colonne B (ref)     : A5 § 5 disait deja « ON NE FAIT PAS : reference 69 ».
     . colonnes F et G     : A4bis § 5 les classait deja « A NE PAS RECUPERER --
                             vos notes et votre process », avec leurs chiffres.
     . colonne E (Lien CRM): la CARTE DES CHAMPS § 5 la rangeait deja dans
                             « CE QUI APPARTIENT AU CLASSEUR SEUL -- ne jamais toucher ».

ET LE PLUS GRAVE : SUR LA COLONNE C, J'AI FAIT TRANCHER L'INVERSE DE CE QUI
   ETAIT DECIDE. A5 § 9 disait : « LE MANDAT -- les 33 vides seulement », donc ON
   RATTRAPE les 33. Le 05/11 j'ai presente le piege (numero_mandat est de CLASSE C,
   relu chaque nuit) comme un obstacle, et obtenu « on n'y touche pas ».
   OR LE PIEGE ET SON REMEDE ETAIENT DEJA ECRITS, le 29/10, dans A5 § 0 et § 6 :
     « CLASSE C -- A HEKTOR. Une ecriture locale y est EFFACEE la nuit suivante »
     « 3. POUR CHAQUE CHAMP DE CLASSE C : une colonne "a nous", sur le modele deja
       valide des _app. Sans elle, la nuit efface ce qu'on ecrit. »
   -> Le rattrapage des 33 mandats est POSSIBLE. Il demande une colonne, pas un refus.
```

---

# 3. ⭐ LE GEL RELANCÉ SUR LES DONNÉES DU 09/11

Commande : `python phase2/checks/rapport_gel_tous_les_champs.py`
Sorties : `notice/A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-11-09.csv` (4 679 lignes)
et `notice/A4_RAPPORT_GEL_ECARTS_SEULS_2026-11-09.csv` (3 985 lignes).

⭐ **Correction apportée au script aujourd'hui** : les deux noms de sortie étaient
**gravés au 29/10** dans le code. Relancer le rapport **écrasait la mesure d'origine
en mentant sur sa date**. Il date désormais ses fichiers du jour de la mesure.

## Le mouvement du classeur, et il ne s'arrête pas

```
02/11   4 775 lignes lues    94 non rattachees
05/11   4 778 puis 4 780     99 puis 101
09/11   4 783 lignes        104 NON RATTACHEES
```

⚠ **Le classeur grandit d'environ une ligne par jour, et chaque ligne neuve arrive NON
RELIEE.** Le gel, lui, n'a pas bougé depuis le 31/10 : toujours 12 413 liens,
4 679 lignes. ⛔ **Et aucune alerte ne compte ces 104** (voir § 6, préalable 4).

## Les écarts, 29/10 contre 09/11 — ils sont STABLES

```
champ               29/10    09/11    ce que ca dit
Mandat               134      134     inchange . et 33 « classeur seul » TOUJOURS VIDES
Prix                 208      207
Commission TTC        85       83     et 377 cases vides chez nous, toujours
Charge Commission      0        0     CHIFFRE FAUX -- voir § 5
Offre Achat          210      211
Compromis             44       44
Vente Prevue       1 767    1 768
Vente Fixee           61       61
Etat Actuel          160      172     +12
Acquereur            120      119
Vendeur               68       68
Notaire            1 373    1 370     et 483 vides chez nous, toujours
Negociateur 1        432      430
Negociateur 2        374      375
Negociateur 3          9        9
Agence               498      498     cause TOUJOURS non mesuree (reserve du 29/10)
Ville              1 644    1 644
Nature             1 653    1 650     -3 : la correction de table du 05/11 agit
Vente Reglee       3 752    3 723     aucune case chez nous
Numero de facture  3 729    3 701     aucune case chez nous
product_ref           69       69
```

⭐⭐ **LA LECTURE DE CE TABLEAU EST SIMPLE : EN ONZE JOURS, RIEN N'A ETE RATTRAPE.**
Le gel tient, les mesures sont reproductibles, et **le travail utile n'a pas commencé**.
Les ~2 276 cases « récupérables sans aucun arbitrage » chiffrées le 29/10 (A5 § 5) sont
toujours à prendre — moins les 23 474 charges posées le 04/11, qui n'étaient pas dans ce
compte et qui sont **le seul rattrapage réellement effectué à ce jour**.

---

# 4. ⛔⛔ LA DÉCISION QUI BLOQUE TOUT, ET ELLE EST LA MÊME DEPUIS LE 02/11

A6 § 3 l'a nommée, chiffrée et jamais obtenue. Sur les 21 champs des 4 679 lignes
reliées, soit **98 280 cases** :

```
identiques des deux cotes          49 182   50,0 %   rien a faire
REMPLIES DES DEUX, DIFFERENTES      8 909    9,1 %   <-- LE CAS 4, NON TRANCHE
le classeur sait, nous PAS         10 435   10,6 %   deja decide : on prend
nous savons, le classeur PAS        9 077    9,2 %   phase B
vides des deux cotes               16 912   17,2 %   rien a faire
hors perimetre                      3 765    3,8 %
```

**8 909 cases contre 10 435.** La question non tranchée pèse presque autant que tout
ce qui est décidé. ⭐ **Et c'est le seul verrou de P1.4** : on ne peut pas écrire un
patch de mise en conformité sans savoir, pour chaque champ, qui gagne en cas de conflit.

⭐ **La recommandation du 02/11 existe déjà, complète** (A6 § 3) : 4 champs au classeur
· 4 à nous · 13 en liste · 1 partagé par année (le prix, nous à partir de 2025).
⛔ **Elle n'a jamais été validée ni refusée.** C'est elle qu'il faut reprendre, pas
réinventer.

---

# 5. ⛔⛔ LE DÉFAUT TROUVÉ AUJOURD'HUI — le rapport réclame un travail déjà fait

Le rapport de gel annonce, pour la colonne Q « Charge Commission » :
**0 identique · 0 écart · 933 « le classeur seul » · 3 746 vides des deux côtés.**

Autrement dit : *« il reste 933 charges à prendre au classeur »*.

**C'est faux.** Mesure du 09/11, en base :

```
app_affaire_ledger.charge_commission_app                     7 / 31 143  <- ce que LIT le rapport
app_mandat_register_current.mandat_charge_honoraires_app  23 474 / 24 579  <- ou la charge VIT
```

⭐ **La charge est un attribut du MANDAT, pas de l'affaire.** Les 23 474 valeurs posées
le 04/11 — dont les 837 venues du classeur — sont dans le **registre des mandats**. Le
rapport, lui, lit `charge_commission_app` du **registre des affaires**, qui n'a que
7 lignes d'essai.

➡ **Le rapport de gel est périmé sur cette colonne**, et il ferait refaire un travail
accompli. ⬜ **Correction à faire** : lui faire lire `mandat_charge_honoraires_app` via
`hektor_annonce_id`, comme le fait la pose du 04/11. ⛔ **Non corrigé : j'attends
l'accord**, parce que ça change un chiffre de référence du chantier.

⚠ **Et la même question se pose pour les 20 autres champs** : le rapport lit-il, pour
chaque colonne, la case où la donnée VIT vraiment ? Ce n'est pas mesuré. **C'est la
première chose à vérifier avant d'écrire P1.4** — sans quoi le patch travaillerait sur
de faux écarts.

---

# 6. L'ÉTAT DES QUATRE PRÉALABLES *(A5 § 6, posés le 29/10)*

```
1.  LES 14 ANCIENS NEGOCIATEURS dans l'annuaire        PAS FAIT (mais pas pire)
      14 noms sont codes EN DUR dans le script (ANCIENS_HORS_REGISTRE).
      CORRECTION DU 09/11, APRES MESURE : j'avais ecrit ici que « le rapport en
      compte 24, donc 10 noms de plus sont apparus ». C'ETAIT FAUX. Les 24 sont
      des CASES, pas des personnes : les memes 14 noms portent 24-25 cases du
      classeur (ABED 6, ALLEMAND 4, BERTRAND 3, AGRAIN 2, et 10 noms a 1 case).
      Aucun nom nouveau n'est apparu. Le croisement avec le registre le confirme :
      sur 90 noms distincts au classeur, 87 sont RECONNUS.

2.  LA TABLE D'ALIAS                                   PAS FAIT, ET MOINS UTILE
      QUE PREVU -- mesure du 09/11, voir A17.
      Ce n'est PAS une table : 2 entrees en dur dans le script
      (GIRAUD -> Aline VALETTE, 163 cas . ALVES MENDES -> Lucie DECHANDON, 119 cas).
      MESURE DU GAIN SUR LE GEL : les noms inconnus de notre registre ne portent
      que 59 cases, et ces cases sont deja reliees « sure » 57 fois sur 59.
      -> Les alias ne gagneraient que 2 LIGNES du gel (1 non reliee, 1 a valider).
      LE REGISTRE DU 04/11 A DEJA FAIT LE TRAVAIL : 87 noms sur 90 sont reconnus.
      Et les 3 inconnus ne sont pas des alias mais des noms COLLES :
      DIMARIA = Magali DI MARIA (51 cases) . DEFONSECA = Estelle DE FONSECA (7)
      . DEPERETTI = Lea DE PERETTI DE LA ROCCA (1). C'est une NORMALISATION.
      -> La table reste necessaire POUR LE RATTRAPAGE (qui ne connait pas les
      2 alias codes dans le rapport), mais elle n'ameliorera PAS le gel.
      Tant qu'elle n'existe pas, les 6 colonnes I J K L M N -- celles qui touchent
      LA PAIE -- ne peuvent pas etre rattrapees.

3.  UNE COLONNE « A NOUS » PAR CHAMP DE CLASSE C        PAS FAIT
      Mesure du 09/11 : seuls les 3 champs de CLASSE A ont leur colonne _app
      (charge_commission_app, honoraires_entree_app, honoraires_sortie_app).
      Il n'existe NI numero_mandat_app, NI notaire_app, NI date_app.
      -> C'est CE prealable qui bloque le rattrapage du mandat, du notaire et des
      dates -- les postes les plus nombreux du compte « sans arbitrage ».

4.  UNE SENTINELLE SUR LES LIGNES NON RATTACHEES        PAS FAIT
      Il existe `data.classeur_lien_casse` sur la vue `app_v_classeur_lien_casse`
      (5 lignes aujourd'hui), mais elle surveille les liens CASSES, pas les lignes
      JAMAIS RELIEES. Les 104 non rattachees montent sans que personne ne le voie.
      Et les 5 lignes de cette vue ne sont pas expliquees : 0 lien du gel pointe
      vers une affaire disparue. A mesurer.
```

---

# 7. ⛔ LES VERROUS, INCHANGÉS

```
LIRE LES APPS SCRIPT DU CLASSEUR -- A FREDERIC, depuis le 22/10.
   Sheet1 nourrit LA PAIE, et rien ne dit ce qu'un script declenche quand une case
   change. Bloque la PHASE B (P4) uniquement. Ne bloque PAS le rattrapage.

L'APPARIEUR NE LIT QUE LA PLAGE A1:AL6000 (reserve du 31/10, jamais corrigee).
   Toute colonne ajoutee a droite de AL est invisible, EN SILENCE. Et toute ligne
   au-dela de 6 000 aussi : avec 4 783 lignes, la marge est de 1 217 lignes.
```

---

# 8. ⬜ CE QUI RESTE À DÉCIDER — et c'est court

```
1  LE CAS 4 (§ 4) : la repartition champ par champ deja proposee le 02/11 dans
   A6 § 3 -- 4 champs au classeur, 4 a nous, 13 en liste, 1 partage par annee.
   C'EST LE SEUL VERROU DE P1.4. Tout le reste en decoule.

2  LA CORRECTION DU RAPPORT sur la charge (§ 5), et la verification des 20 autres
   colonnes : le rapport lit-il la bonne case ?

3  LES QUATRE PREALABLES (§ 6). Le 2 (alias) est maintenant FAISABLE grace au
   registre des negociateurs. Le 3 (colonnes _app) est le plus structurant.

4  LES 104 LIGNES NON RELIEES : ajouter leurs liens au gel, et poser la sentinelle.

5  T0.1 et T0.2 : mettre les scripts et les notes du chantier sous git. 4 minutes.
```

## ⛔ ET LA RÈGLE QUE JE ME POSE, POUR NE PLUS TOURNER EN ROND

```
AVANT de mesurer une colonne, LIRE DANS CET ORDRE :
  1  DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md   la SOURCE DE VERITE
  2  A5_CHAMP_PAR_CHAMP_EST_CE_POSSIBLE_2026-10-29.md   « est-ce possible », par CLASSE
  3  A6_SITUATION_CLASSEUR_2026-11-02.md § 3            la doctrine des 4 cas
  4  A7 § 2 et A4bis § 5                                la grille et les 38 colonnes
  5  PLAN_CHANTIER_CLASSEUR_2026-10-28.md               ou on en est dans les taches
ET NE JAMAIS ouvrir un second registre de decisions.
```
