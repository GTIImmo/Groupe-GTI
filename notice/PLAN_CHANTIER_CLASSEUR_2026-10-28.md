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
   ⛔⛔ ET « 241 » N'EST PAS UN NOMBRE DE CREATIONS — note du 16/11, apres avoir
      dit « les 241 » toute une journee comme s'il s'agissait d'un seul lot :
        C5 lot B  215 creations franches  144 offres + 62 compromis + 9 ventes
        C6 lot C   26 ventes  dont NOTRE compromis porte DEJA une autre date
                   d acte -> ⛔ C'EST UN CONFLIT, PAS UN VIDE -> SA DECISION
      215 + 26 = 241. Le total est juste, le mot « creations » ne l'est pas.
   ⚠ ET LE DECOUPAGE SUR est donne par A4 lui-meme : « les offres et compromis
      n'ont pas ce risque » -> 144 + 62 = 206 posables apres A2 (fait), et les
      9 ventes du lot B attendent A4 (l'effet de bord d'une vente creee).
   ⛔⛔ ET CETTE NOTE-CI ETAIT FAUSSE, retiree le 16/11 : j'avais ecrit « ce
      comptage date du 31/10, a remesurer ». NON -- le plan dit lui-meme, plus bas,
      « ✅ LE RESTE EST STABLE : les chiffres de 3.3 sont CONFIRMES AU 15/11 ».
      Les 241 (144 + 62 + 35) sont donc a jour. J'ai fabrique une peremption qui
      n'existait pas, et c'est exactement ce que Frederic a senti en disant
      « tu dois te melanger ».
                        + 10 transactions presentes SANS leur date (4 offres, 6 compromis)
```

### PHASE A — MESURER. **Rien d'ecrit en base.**

```
A0 ✅  RELANCER LE RAPPORT DU GEL -- FAIT LE 16/11, voir « A0 EST FAIT ».
       ⭐ IL A FAIT EXACTEMENT SON TRAVAIL : les « 241 » venaient du rapport du
       13/11, pris PENDANT la pose du lot 1. Le chiffre a jour est 281
       (174 offres + 68 compromis + 39 ventes), STABLE depuis 3 jours.
       ⛔ ET LES 48 ECARTS DE Pourcentage 1 SONT CONFIRMES : le soupcon etait
       juste dans l'autre sens -- le rapport n'etait pas premature, les ecarts
       sont REELS. LE LOT 1 N'EST DONC PAS CLOS A 100 %.
       ⚠ le lancer avec `-X utf8`, sinon il tombe (UnicodeEncodeError l. 587).
A1 ✅  FAIT LE 16/11 -- voir « A1 EST FAIT ». Les huit sont lues et pesees.
       ✅ Z propre : 896 valeurs, 896 DATES -> C3 peut etre construite.
       ⚠ Y porte le defaut des DEUX FORMATS : 794 textes sur 3 756 (21 %,
         « une sur cinq ») -> la meme tolerance qu'au 14/11 AVANT C8.
       ⚠ F est MIXTE : 1 536 « V », 753 emojis, 810 textes (les motifs reels)
         -> « reprendre en bloc » emporterait les pastilles. SA DECISION.
       ⚠ AH casse melangee (oui/OUI/non/NON) . AJ porte des PRENOMS.
       ⭐ et la contradiction AH/AJ s'explique : « a envoyer » vs « envoye »,
         deux etapes et non deux versions.
A2 ✅  FAIT -- pose le 15/11, JUGE le 16/11 au matin (1 . 340 . 30 817, voir
       « LE VERDICT DU MATIN »). C'est lui qui a debloque tout le reste.
       L'ESSAI D'UNE NUIT (= 3.3zero). Une transaction dans la plage app, SANS
       numero Hektor, sur un bien NON VIVANT. Mesure au matin **sur LES DEUX
       bases** (Supabase ET phase2.sqlite). ⛔ OBLIGATOIRE : aucune ligne de la
       plage n'a jamais vecu sans numero Hektor, et 3 ont disparu sans trace.
A3 ✅  MESUREE LE 16/11 : le Sheet porte **4 791** lignes au soir (4 790 le matin,
       4 789 la veille -- il GROSSIT d une a deux lignes par jour) et 38 colonnes lues,
       donc 1 210 de marge sous 6000, et AL est bien la derniere colonne.
       ⚠ MAIS L AUDIT DU SOIR A TROUVE AUTRE CHOSE : 4 790 au Sheet contre
         4 773 dans app_classeur_ligne_id -> 17 LIGNES ABSENTES de notre base.
         Ce n'est pas la fenetre, c'est la table. Voir A6.
       LA FENETRE DU SHEET : l'apparieur ne lit que `A1:AL6000`. Le classeur en
       portait 4 783 -> ~1 200 lignes de marge, puis PERTE SILENCIEUSE du bas.
       Idem pour toute colonne a droite de AL. Ecrit le 31/10, jamais corrige.
A4 ✅  L'EFFET DE BORD D'UNE VENTE CREEE -- FAIT LE 16/11, voir « A4 EST FAIT ».
       LE MECANISME : App.tsx:8321, `vente_id` SUFFIT a afficher « Vendu ».
       L'AMPLEUR : vivier 967 lignes / 856 annonces, dont 706 deja hors du parc
       (aucun effet) et 150 VIVANTES -- dont 111 affichees « Actif ».
       ⛔ CONCLUSION : les ventes NE SE POSENT PAS EN MASSE. Les lister, poser
       celles dont le bien est hors du parc, soumettre les autres une par une.
       ⭐ Les offres et compromis n'ont pas ce risque -> les 206 restent posables.
A5 ⬜  MESURE DU 16/11 : **967**, et non 1 062 -- dont **311 sans vente NI
       compromis**. Le chiffre du plan datait d'un etat anterieur.
       LES LIGNES SANS ROLE 'vente' -- prealable de 3.4 : ou va la valeur
       de Y / AA quand la transaction qui devrait la porter n'existe pas ?
A6 ⬜  MESURE DU 16/11 AU SOIR : **85 non rattachees** + **18 ABSENTES** (4 773 en
       base contre 4 791 au Sheet -- c'etait 17, le Sheet a gagne une ligne dans la
       journee). Ancienne mesure : **17 ABSENTES** de
       app_classeur_ligne_id (4 773 en base contre 4 790 au Sheet) = **102**.
       ⛔ Les 17 n'etaient nulle part au plan. Et le rapport du gel compte 87
         non rattachees la ou la base en compte 85 : ecart de 2, non explique.
       LES LIGNES NON RATTACHEES : notre base n'en garde que l'identifiant.
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

⛔⛔ **CE PARAGRAPHE EST FAUX, ET IL EST DEMOLI PLUS BAS** — voir « RECTIFICATION DU
15/11 — LE "DEFAUT DU POINT 2" ETAIT FAUX, ET L'ECRAN SAIT DEJA ». Le test du **numero**
passe AVANT celui de `present_in_hektor`, donc le message rendu est le BON ; et l'ecran
exige **un numero** pour afficher « plus dans Hektor ». Le renvoi est pose le 16/11 :
les deux textes cohabitaient, et qui lisait celui-ci sans lire l'autre croyait au defaut.

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

⚠ **RELU LE 16/11 : CETTE PHRASE EST ANTERIEURE A LA SIMPLIFICATION.** La piece 4 est
devenue **« cosmetique, pas bloquant »** (voir « LA PROPOSITION SE SIMPLIFIE DONC
BEAUCOUP » : elle se reduit a UN MOT, « n'existe pas *encore* chez Hektor » ->
« n'existe pas chez Hektor »). L'ordre reellement contraint est donc **1, 2, 3 avant
toute ecriture**, et les pieces 1-2-3 sont POSEES depuis le 15/11.

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

⛔⛔ **ATTENTION, NUMEROTATION — note posee le 16/11, et ON NE RENUMEROTE PAS.** Dans la
liste des cinq pieces (« LA SOLUTION PROPOSEE — DECLARER L'EXCLUSION »), **26bis est la
PIECE 5**, et la **PIECE 4** est *le message de l'ecran*. Cette section et celles qui
suivent l'appellent « la piece 4 » — c'est le nom sous lequel elle a ete travaillee les
15 et 16/11, et il est garde parce que le code, la memoire et les messages de commit y
renvoient. **Quand on lit « la piece 4 » apres cette ligne, il s'agit de 26bis.**
⭐ L'ETAT REEL DES CINQ, mesure le 16/11 :

```
   1 la marque                 POSEE 15/11      3 le filet du worker   POSE 15/11
   2 la sentinelle (la vue)     POSEE 15/11      5 26bis, la recopie    POSEE 15-16/11
   4 le message de l ecran      ⏰ RESTE -- « cosmetique, pas bloquant » : un seul MOT,
     « n existe pas ENCORE chez Hektor » -> « n existe pas chez Hektor », et seulement
     pour une ligne marquee. A TRANCHER PAR FREDERIC, rien ne l'attend.
```

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
   recopie_app_seule_active()                  l'interrupteur -- ETEINT par defaut
      ⚠ relu le 16/11 : le CODE est a 0 par defaut, mais `.env` le porte a 1
        depuis le 15/11 a 17:46. Ce bloc decrit la POSE, pas l'etat du jour.
   recopier_ce_que_hektor_ne_rendra_jamais()   la recopie, AUCUN appel reseau
   l'appel : APRES le push (le 1er passage n'ecrit rien chez Supabase)
             AVANT la redescente (un seul chemin pour les colonnes de classe A)
   PLAFOND_RECOPIE_APP_SEULE = 500 -- au-dela, REFUS ecrit, rien n'entre
   phase2/sync/test_recopie_app_seule.py              39/39 verts a la POSE
      (44/44 depuis le garde-fou du 15/11 au soir -- voir plus bas)
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
   essai_reel_sur_copie_26bis.py       15/15   A LA POSE, sur les VRAIES lignes
      ⛔⛔ RELU LE 16/11 : IL SORT EN CODE 1 DEPUIS LA 1re NUIT, ET C'EST NORMAL.
        Il juge « 1 recopiee, cles [1001424] » -- mais la recopie n'admet que ce qui
        n'est PAS DEJA EN LOCAL (affaire_ledger.py:2796). La ligne y est depuis le
        16/11 a 06:17, donc l'essai obtient 0 et tombe ensuite sur un KeyError.
        ⭐ SON ROUGE EST DONC LA PREUVE QUE LA NUIT A MARCHE : il n'y a plus rien a
          recopier. Mesure : la version de HEAD sort deja en code 1, le rouge n'a
          pas ete introduit par une edition.
        ⭐ ET PERSONNE NE L'APPELLE : ni le run, ni le moniteur, ni une tache --
          il ne crie donc nulle part tout seul. Pas d'urgence.
        ⏰ A TRANCHER PAR FREDERIC, et je ne choisis pas :
           A  le laisser, avec cette note datee                    (cout zero)
           B  lui apprendre la nuit passee : s'il voit la ligne deja en local, il
              le DIT et juge l'inverse (« 0 recopiee, resultat attendu »)  <- je
              recommande B, parce que les 241 demanderont de re-eprouver sur les
              vraies donnees
           C  le retirer -- on perd l'epreuve sur les vraies lignes
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

### ✅✅ 4bis -- LA GARDE DE L'ORIGINE EST POSEE SUR LES DEUX LECTEURS (16/11)

**L'AUDIT A BALAYE TOUTE LA FAMILLE, pas seulement la sentinelle** -- lecon 9, « une
cause structurelle se balaie dans TOUTE sa famille ». Six lecteurs regardent « cette
transaction n'est pas chez Hektor » :

```
   DEJA PROTEGES (4), verifies un par un
     le filet du worker       console_job_worker.js:24124   &transaction_origine=is.null
     l app, 8 endroits        App.tsx:19884,31829,32242,... exige UN NUMERO EN PLUS
     3 gestes de masse        enqueue_fermeture_dossiers_impossibles.js:172
                              enqueue_refus_offres_mortes_lot.js:162
                              enqueue_reaccepter_offres_refusees_a_tort.js:247
     le moteur du moniteur    params passes aux DEUX portes (l. 1845 et 1923)
   SANS GARDE (2) -- ce sont eux
     A la sentinelle          check_gti_health.py, data.transaction_disparue
     B le filet du cockpit    export_app_payload.py -- LE PLUS GRAVE
```

⭐⭐ **CE QUE L'APP DIT D'ELLE-MEME, et qui explique pourquoi elle est sure** :
`App.tsx:31823` -- « Hektor l'a SUPPRIMEE : elle porte un numero ET
present_in_hektor = false ». Une ligne **sans** numero est « nee chez nous ». Les 241
n'auront pas de numero : l'ecran ne les prendra donc jamais pour des suppressions.

#### ⛔⛔ B EST PLUS GRAVE QUE A, ET CE N'EST PAS UNE ALARME

`export_app_payload.py` ressortait toute ligne absente de Hektor avec `_dropped`, et le
cockpit AFFICHE alors « **· plus dans Hektor depuis \<date\>** », infobulle « Vu pour la
derniere fois dans Hektor le ... » (`App.tsx:31502`). Pour les 241 c'est **faux** : elles
n'y ont jamais ete. Ce n'est pas du bruit dans un journal, **c'est une phrase mensongere
montree a l'utilisateur**.

⭐ Le plan l'avait **deja repere** (« dont export_app_payload.py:2383 ... notre cas
exact ») : je l'ai redecouvert au lieu de le lire. Lecon 15, une fois de plus.

⚠ **ET LA MESURE A CORRIGE MON ALERTE** : le defaut est **DORMANT** aujourd'hui. La ligne
d'essai 1001424 n'a **aucun acquereur**, et `build_affaires_dossiers` saute toute ligne
sans acquereur -- rien ne s'affiche donc a tort. Mesure du 16/11 : **20 lignes** a
`present_in_hektor = 0`, dont **19 avec un acquereur** -- et ces 19 sont de **VRAIES**
disparitions, avec numero : elles doivent continuer de s'afficher.

#### ⭐ LE PIEGE QUE LA PRUDENCE A EVITE

`export_app_payload.py` entoure sa lecture d'un `try` qui, sur `OperationalError`, rend
une liste **VIDE**. Si l'on avait colle le filtre sans verifier la presence de la colonne,
un appel sur une base fraiche aurait leve « no such column », le `except` aurait vide la
liste, et **les 19 affichages legitimes auraient disparu sans un mot**. La garde mesure
donc la colonne avant (`PRAGMA table_info`, patron de la l. 2107 du meme fichier).

⭐ **L'ORDRE DU RUN EST FAVORABLE, mesure** : le ledger pose la marque par sa redescente
a **06:18:26**, et « push upgrade to supabase » -- qui importe ce module -- part a
**06:22:39**. La marque est la le soir meme.

#### ✅ L'EPREUVE : `phase2/checks/test_garde_origine_classeur.py`, **22/22**

⭐ **L'essai ne recopie rien** : il EXTRAIT la vraie requete et la vraie garde du fichier
source par expression reguliere, puis les joue sur une base SQLite en memoire. Il ne peut
pas rester vert sur une copie perimee.

```
   1   les 2 lignes MARQUEES `classeur` ne sortent plus
   1b  exactement QUI sort : le cobaye et la vraie disparition, RIEN D'AUTRE
   1e  ⛔ une marque VIDE est traitee comme MARQUEE (le choix prudent)
   1c  ⭐ LA VRAIE DISPARITION HEKTOR (50128) SORT TOUJOURS
   2   TEMOIN INVERSE : sans la garde, les 2 lignes du classeur RESSORTENT
   2b  la garde retire exactement 3 lignes (les 2 marquees + la vide)
   3   ⛔ colonne absente -> la liste n'est PAS videe (les 19 survivent)
   4   la garde est bien DANS le fichier, et le danger y est ECRIT
   5   ⛔ la sentinelle : la garde est posee ET les DEUX portes l'heritent
   6   ⭐⭐ LES TROIS PORTES disent la MEME chose, mot pour mot
```

#### ✅✅ ET LA PREUVE EN REEL, PARCE QU'UN ESSAI HORS LIGNE NE SUFFISAIT PAS

Un essai hors ligne ne peut pas dire si **PostgREST** accepte `or=(...)` combine aux deux
autres filtres. S'il le refusait, la sentinelle sortirait en « unknown » -- et **une
lecture ratee n'est jamais un vert**. Mesure en lecture seule :

```
   AVEC la garde : 1       SANS la garde : 1      l echantillon repond, 1 ligne
   -> offre . annonce 28351 . 2006-04-01   (le cobaye, comme avant)
```

⛔⛔ **MAIS « 1 = 1 » NE SE CROIT PAS SANS TEMOIN POSITIF** : c'est compatible avec « la
garde marche et ne retire rien » ET avec « PostgREST ignore le parametre ». Quatre
reglages, sur le critere tel qu'il est maintenant :

```
   transaction_origine=is.null       -> 1   (la sentinelle telle qu'elle est)
   transaction_origine=not.is.null   -> 0   TEMOIN POSITIF : on EXIGE une marque
   kind=eq.zzz                       -> 0   reglee pour exclure
   kind=eq.offre                     -> 1   reglee pour inclure le cobaye
```

⭐⭐ **La forme FILTRE donc vraiment.** Le « 1 = 1 » veut bien dire « la garde ne retire
rien AUJOURD'HUI parce que rien n'est marque » -- 31 158 lignes NULL des deux cotes, zero
chaine vide.

#### ✅ NON-REGRESSION, ET AUCUN SERVICE A REDEMARRER

Les deux fichiers compilent. Les **9 essais voisins** ont tourne : 5 verts, **3 rouges
PREEXISTANTS** (mesures en restaurant le code de HEAD, puis en reposant mes versions --
empreintes md5 identiques au retour : fuseau horaire, libelles d'erreur changes, fonction
Postgres absente), et 1 qui exigeait un argument `--base` (c'est moi qui l'avais mal
lance, pas un echec).

⭐ **Rien a redemarrer** : le moniteur est un script relance a chaque passage (toutes les
2 h), et le payload est relu par le run chaque nuit. **Aucun worker touche.**

**Le retour arriere** : retirer les deux clauses. Aucune ecriture en base, aucun geste
chez Hektor.

#### ⛔⛔ J'AVAIS ECRIT CETTE RESERVE A L'ENVERS -- CORRIGE SUR SA QUESTION

J'avais note : « le worker emploie un critere plus etroit que le mien, les deux sont
d'accord aujourd'hui », et j'en avais tire que « si une chaine vide apparaissait, le
worker chercherait un numero a une ligne du classeur ». **Les deux moities etaient
fausses.** Frederic a demande « c'est a dire ? », et la relecture a donne ceci :

Une case est sans contenu de **deux** facons que la base ne confond jamais : **NON
RENSEIGNEE** (personne n'y a rien ecrit) ou **VIDE** (on y a ecrit une chaine de longueur
zero). Mon premier critere gardait « non renseignee **ou** vide » ; le worker ne traite
que « non renseignee ».

```
   si l'insert des 241 posait une marque VIDE au lieu de `classeur` :
      le worker    -> les ECARTE de son filet   (vide n'est pas non renseignee)  OK
      ma sentinelle-> les aurait fait CRIER 241 fois par nuit                    MAL
      mon cockpit  -> aurait affiche 241 phrases FAUSSES                         MAL
```

⭐ **Donc son critere etait le bon, et le mien le plus PERMISSIF -- pas le plus etroit.**
Le plus prudent est le plus etroit. **Alignement fait le 16/11** : `is.null` seul aux
**trois** endroits, et le controle 6 de l'essai le verifie fichier par fichier.
**Il n'y a plus de divergence a surveiller** -- une divergence se supprime, elle ne se
surveille pas. Voir [[deux-portes-meme-table-seuils-divergents]].

⭐ **Et le worker n'a pas ete touche** : c'est lui qui avait raison. Aucun service a
redemarrer.

### ✅✅✅ 5 -- LE COBAYE EST RETIRE DES DEUX COTES (16/11, 08:57-08:58)

⛔⛔ **ET L'AUDIT DES NOTES, DEMANDE PAR FREDERIC, A SAUVE LE GESTE.** Sa phrase :
« audit de nouveau car nous avons peut-etre laisse des notes erronees sur ce sujet,
nous avons change plusieurs fois, il faut etre sur ». **Six notes periment**, dont une
qui changeait le geste :

```
   1  l'ORDRE du retrait          l'argument etait mort depuis l'allumage de 26bis
   2  « ETEINT par defaut »       vrai pour le code, faux pour le .env
   3  « 39/39 » (x2)              on est a 44/44
   4  « l'etat d'AUJOURD'HUI »    designait l'etat de la VEILLE
   5  « essai_reel 15/15 »        il sortait en code 1 depuis la 1re nuit
```

⭐⭐ **LA NOTE QUI COMPTAIT** : le script disait « le local d'abord ; un local vide avec
Supabase rempli, c'est l'etat d'avant la piece 4, connu, mesure, sans danger ».
**C'etait vrai le 15/11, quand l'interrupteur etait eteint.** Depuis le 15/11 a 17:46 il
est allume, et `recopier_ce_que_hektor_ne_rendra_jamais` admet « la plage app ET sans
numero ET PAS DEJA EN LOCAL » : **une ligne retiree du local mais encore chez Supabase
est RECREEE au run suivant.** Le retrait local seul ne tient donc pas une nuit. Ce qui
compte n'est pas l'ordre mais **LA FENETRE** : les deux gestes avant le run de 04:00.

⭐ **DEUX FAUSSES ALARMES LEVEES PAR LA MESURE** : « SUPABASE D'ABORD »
(`affaire_ledger.py:2772`) ne contredit pas « le local d'abord » -- l'un parle de la
**creation** (Supabase frappe les numeros), l'autre du **retrait**. Et il ne reste
**aucune** trace de l'ancien critere de garde : les seules occurrences sont dans
l'essai, qui verifie justement leur absence.

#### LES DEUX GESTES, ET LEURS PREUVES

```
   GESTE 1  le LOCAL, 08:57:39
      sauvegarde datee : phase2_avant_retour_26bis_20261116_085739.sqlite
      1 retiree . 0 restante . voisines INTACTES (340 + 30 817)
   GESTE 2  SUPABASE, 08:58 -- patch_essai_a2_plage_app_2026-11-15_INVERSE.sql
      joue DEPUIS LE FICHIER (node Console/apply_sql_patch.js) pour qu'aucune
      recopie a la main ne puisse introduire une faute
      ⚠ l'hote direct est injoignable (l'IPv4 y a ete retiree) -> le repli par le
        POOLER a joue tout seul : aws-1-eu-west-2.pooler.supabase.com
```

#### ✅ LE CONTROLE, ET PAS SEULEMENT L'ABSENCE D'ERREUR

```
   chez Supabase            avant        apres
     lignes marquees essai     1            0      OK
     la ligne 1001424          1            0      OK
     les 2 origines du dossier 2            2      OK INTACTES (20217, 6544)
     la plage app            341          340      OK
     dont sans numero          1            0      OK
     le registre total     31 158       31 157     OK
   en local
     a retirer                 1            0      OK
     voisines                340 + 30 817          OK PAS BOUGE
     le dossier 28351     compromis 20217 + vente 6544  OK
   LES DEUX SENTINELLES
     data.transaction_disparue        -> 0   (avec la garde posee en 4bis)
     data.affaire_sans_numero_hektor  -> 0   (la VUE)
```

⚠ **LA DOUBLURE LOCALE GARDE ENCORE LA LIGNE** (31 158), et c'est ATTENDU : elle est
l'image du serveur de cette nuit. **Risque ecarte par le code** (`pull_from_supabase.py`
l. 755-757) : la descente ecrit dans une table temporaire, verifie que la copie est
complete, puis **DROP l'ancienne et renomme** -- la doublure est donc REMPLACEE EN
ENTIER demain a 06:45, et le run la rafraichit **avant** la recopie (06:15 puis 06:16).
⛔ Seul interdit d'ici la : **ne pas lancer `affaire_ledger.py` a la main**, il relirait
la doublure et reposerait la ligne.

#### ✅ L'ESSAI SUR LES VRAIES DONNEES EST REECRIT -- choix « B » de Frederic

Il **sortait en code 1 depuis la 1re nuit**, et son echec etait **la preuve que la nuit
avait marche** : il attendait « 1 recopiee » alors qu'il n'y avait plus rien a recopier.
Mesure : la version de HEAD sortait **deja** en 1 -- le rouge n'etait pas une
regression. Et personne ne l'appelle (ni run, ni moniteur), donc il ne criait nulle part.

⭐⭐ **LA FORME JUSTE NE DECRIT PAS UN ETAT, ELLE LE FABRIQUE.** Il MESURE son etat de
depart (passage 0), puis **retire de SA COPIE** les candidates pour recreer « l'instant
d'avant la recopie ». Il est donc vrai n'importe quel jour, et **il servira tel quel
pour les 241**. **18/18 verts.**

⭐ **ET SES DEUX CHEMINS SONT EPROUVES**, pas supposes : avec un candidat, 18/18 ; sans
candidat (fabrique dans une copie), il **sort en 0**, DIT « rien a eprouver », renvoie a
`test_recopie_app_seule.py` et **ne pretend aucun vert**. Demain, apres la descente, il
se taira proprement au lieu de crier.

**Le retour en arriere** : la sauvegarde datee pour le local, et
`patch_essai_a2_plage_app_2026-11-15.sql` pour Supabase.

### ✅⭐⭐ A4 EST FAIT -- L'EFFET DE BORD D'UNE VENTE CREEE (16/11, lecture seule)

**Son enonce** : « chez nous c'est la vente qui fait passer un dossier a l'etat VENDU.
Mesurer ce que deplacent 35 ventes neuves (etat affiche, pilotage, statistiques,
chainage) AVANT de les poser. ⭐ Les offres et compromis n'ont pas ce risque. »

#### 1. LE MECANISME : UNE SEULE LIGNE DE CODE, ET ELLE NE REGARDE RIEN D'AUTRE

```
   App.tsx:8321   if (item.vente_id || status.includes('vendu') || ...) return 'Vendu'
```

⛔ **`vente_id` SUFFIT.** Pas besoin d'un statut Hektor, pas besoin d'une date : la
seule EXISTENCE d'une ligne `kind='vente'` fait afficher « Vendu ». C'est exactement le
risque que A4 devait nommer, et il est **structurel**, pas conditionnel.

#### 2. LES LECTEURS, LES QUATRE DIMENSIONS

```
   etat affiche    App.tsx:8321 (MandatStatutValue) + la vue app_v_mandat_statut
                   App.tsx:433 « Vendu ou Clos » = historique
                   audit_annonce_detail_coverage.py:23 HISTORICAL_STATUSES
   pilotage        patch_pilotage_par_nego_2026-11-04 . patch_pilotage_limites_
                   2026-11-03 . patch_pilotage_acquereurs_affaires_2026-11-03
   statistiques    portees par ces memes vues de pilotage
   chainage        une vente REJOINT la chaine de son compromis quand il existe,
                   sinon elle en cree une (regle C « vente seule », V2)
   + CINQ VUES lisent une vente : app_annonces_current . app_dossiers_current
     app_contact_relations_current . app_registre_mandats_current . app_v_mandat_statut
```

#### 3. L'AMPLEUR, MESUREE -- ET C'EST LA QUE A4 TRANCHE

⚠ **LE VIVIER N'EST PAS LES 35** : on ne peut pas lister les 35 ventes manquantes sans
le Sheet. On mesure donc le MAJORANT -- toutes les lignes du classeur qui n'ont pas de
vente chez nous -- et les 35 en sont un sous-ensemble.

```
   lignes du classeur liees                         4 702
     dont elles ont DEJA une vente                  3 735
     dont SANS vente chez nous                        967   <- le vivier
          avec un compromis 656 . offre seule 311
   annonces concernees                                856
     deja HORS du parc vivant                         706   <- aucun effet de bord
     ENCORE VIVANTES                                  150   <- tout le risque est la
          et AUCUNE n'a de vente (c'est coherent :
          un bien vivant n'est pas vendu)
```

⛔⛔ **CE QUE CES 150 AFFICHENT AUJOURD'HUI, et qui changerait** :

```
   Actif            111   <- EN VENTE AUJOURD'HUI
   Echu              31
   (aucun statut)     5
   Clos               5
```

⭐ **ET LE DETAIL DE CE QUE PORTE CHAQUE LIGNE** (⚠ ici l'unite est LA LIGNE DU
CLASSEUR, pas l'annonce : 124 lignes pour 111 annonces « Actif », car une annonce peut
porter plusieurs lignes -- ne pas additionner les deux tableaux) :

```
   bien « Actif »  + la ligne a un COMPROMIS chez nous      70 lignes
   bien « Actif »  + la ligne n a qu une OFFRE              54 lignes
   bien « Echu »   + compromis 29 . offre seule 11
   bien « Clos »   + compromis  5 . offre seule  1
```

#### ⛔⛔ LA CONCLUSION DE A4 : LES VENTES NE SE POSENT PAS EN MASSE

Une vente posee sur un bien affiche **« Actif »** le fait sortir du parc actif, des
listes de biens a vendre et du pilotage -- d'un seul coup, sans qu'aucun humain l'ait
decide. Et deux lectures opposees sont possibles pour chacune :

```
   SOIT le classeur a raison -> le bien EST vendu, notre base est EN RETARD, et poser
        la vente est une CORRECTION precieuse
   SOIT le lien est FAUX     -> on abime un bien VIVANT, et personne ne le verra
```

⛔ **On ne peut pas trancher sans regarder ligne par ligne.** C'est la reponse de A4 :
les 9 ventes du lot B (et les 26 du lot C) **ne sont pas posables en masse**. Il faut
les LISTER, puis ne poser que celles dont le bien est deja hors du parc vivant, et
soumettre les autres a Frederic une par une.

⭐⭐ **ET A4 CONFIRME LE DECOUPAGE** : les **144 offres + 62 compromis = 206** n'ont
aucun de ces lecteurs -- aucune de ces vues ne bascule sur une offre ou un compromis.
Elles restent posables des que le comptage aura ete remesure.

#### ⛔⛔ ET J'AI PRESENTE UN MAJORANT COMME SI C'ETAIT L'EFFET -- corrige le 16/11

**Mon tort, dit simplement** : j'ai annonce « 111 biens Actif basculeraient », alors que
**les ventes manquantes ne sont que 35 EN TOUT**. Mon 111 est un majorant **trois fois
plus grand que la population entiere** : il compte TOUTES les lignes du classeur sans
vente chez nous, que le Sheet en porte une date ou pas. C'etait alarmiste et faux comme
prevision.

```
   ce que j ai mesure (le vivier)     967 lignes . 856 annonces . 150 vivantes . 111 « Actif »
   ce dont on parle vraiment           35 ventes au total (9 en C5 + 26 en C6)
   -> L EFFET REEL est donc entre 0 et 35 annonces, et au plus 35 - (celles deja
      hors du parc). Le 111 ne borne rien d utile : il est plus grand que 35.
```

⭐ **CE QUE LA MESURE GARDE DE VALABLE, et c'est l'essentiel de A4** :
  . LE MECANISME est prouve -- `vente_id` seul suffit a afficher « Vendu » ;
  . les LECTEURS sont nommes (etat, 3 vues de pilotage, 5 vues `current`, chainage) ;
  . et le risque EXISTE bel et bien, puisque **82 % du vivier est deja hors du parc
    vivant** (706 / 856) mais **18 % ne l'est pas** -- donc une vente du classeur PEUT
    tomber sur un bien vivant, et il faut le verifier ligne par ligne.
  ⛔ La conclusion de A4 ne change pas : **on ne pose pas les ventes en masse.** Ce qui
    change, c'est l'ampleur annoncee : au plus 35, pas 111.

⏰ **CE QUI RESTE A MESURER, ET QUI DEMANDE LE SHEET** : lesquelles des 35 ventes
touchent un bien encore « Actif ». C'est un comptage exact, pas un majorant.

### ✅⭐⭐⭐ A0 EST FAIT -- 16/11, ET IL EXPLIQUE L'ECART SUR LES 241

**Frederic : « pourquoi tu reviens sur le plan ? s'il y a une difference, mesure,
analyse, audite et explique-moi ».** Il a raison : je n'avais pas a douter du plan, mais
a executer A0, qui dit lui-meme « il remet a jour TOUS les chiffres ». C'est fait, et
l'explication est nette.

#### LA MESURE : LE MEME COMPTAGE, SUR TOUS LES RAPPORTS DU GEL

```
   date        lignes    « classeur seul »          A CREER (le role manque)
                        offre  compro  vente      offre  compro  vente  TOTAL
   29/10        4680      188    106     32        188     99     32    319
   09/11        4679      178    113     39        178    106     39    323
   13/11        4702      151     66     37        147     58     37    242   <- LES « 241 »
   14/11        4702      178     75     38        174     67     38    279
   15/11        4702      178     75     38        174     67     38    279
   16/11        4702      178     76     39        174     68     39    281   <- AUJOURD HUI
```

#### ✅ 1. LE PLAN ET MOI MESURONS LA MEME CHOSE -- aucun desaccord de methode

Le plan ecrit « Offre Achat 178 . Compromis 75 . Vente Fixee 38 ». C'est **exactement**
la ligne du 14/11 et du 15/11. La mesure du plan est donc juste, et la mienne aussi :
nous lisons le meme rapport, le meme champ.

#### ⭐⭐ 2. LES « 241 » VIENNENT DU RAPPORT DU 13/11 -- un etat TRANSITOIRE

Mon comptage sur le rapport du 13/11 rend **242**, a une unite des 241 annonces. Or le
rapport du 13/11 a ete produit **a 16:28, PENDANT la pose du lot 1** (posee les 13 et
14/11). C'est donc une photo prise au milieu du geste.

⭐ **ET LE PLAN LE SOUPCONNAIT DEJA**, c'est ecrit dans A0 lui-meme : *« Pourcentage 1
affiche encore 48 ecarts et Negociateur 1 dix-huit, alors que le lot 1 a ete pose les
13-14/11 : le rapport du 14/11 a pu etre produit AVANT la pose. Tant qu'il n'est pas
relance, LE LOT 1 N'EST PAS CLOS A 100 %. »* **A0 existait exactement pour ca.**

#### ✅ 3. LE CHIFFRE EST STABLE DEPUIS TROIS JOURS -> IL EST FIABLE

279 le 14/11, 279 le 15/11, **281 le 16/11**. Deux de plus en deux jours, et le classeur
a gagne 6 lignes dans le meme temps. Ce n'est pas un chiffre qui derive : c'est un
chiffre vivant, et **281 est celui d'aujourd'hui**.

```
   LE CHIFFRE A JOUR, 16/11/2026
      174 offres + 68 compromis + 39 ventes = 281 transactions a creer
      dont 2 a SAUTER pour chainage douteux (1 offre, 1 vente) -> 279 nettes
      et le decoupage de A4 tient toujours :
         174 offres + 68 compromis = 242 posables (aucun lecteur risque)
          39 ventes                = a regarder une par une (effet « VENDU »)
```

⚠ **LE LOT B / LOT C RESTE A REDECOUPER** : les « 215 + 26 » de C5/C6 ont ete etablis
sur le rapport du 13/11. Le tri fin (« 9 ventes : 5 a la meme date d'acte, 2 sans date,
2 sans compromis ») doit etre refait sur les 39 ventes d'aujourd'hui. **C'est le seul
travail qui reste avant d'ecrire**, et il est en lecture seule.

#### ⛔⛔ 4. UNE QUESTION OUVERTE, DECLAREE ET NON TRANCHEE

Entre le 13/11 (242) et le 14/11 (279), le nombre a creer a **monte de 37**, alors qu'on
venait de POSER le lot 1. Poser devrait faire BAISSER les manques, pas les augmenter.
Trois pistes, aucune mesuree :

```
   a  le rapport du 13/11 est pris AU MILIEU de la pose -> ses 242 sont incomplets
   b  les 20 offres refusees a tort le 11/11 et le chainage corrige le 12/11 ont
      deplace des dates d'offre (« la date d'une offre refusee EST la date du refus »)
   c  le re-gel additif du 13/11 a rattache 23 lignes de plus (4 679 -> 4 702)
```

⚠ Cette question ne bloque pas les offres et compromis, mais elle doit etre tranchee
avant de toucher aux ventes.

#### ✅ 5. CE QUE A0 CONFIRME PAR AILLEURS

```
   Pourcentage 1   48 ecarts   -> CONFIRMES : le lot 1 n'est PAS clos a 100 %
   Negociateur 1   19 ecarts   (le plan en annoncait 18)
   lignes NON RATTACHEES  87   -> identique au plan ✅
   anciens negociateurs    13 des 14 sont DESORMAIS dans l'annuaire ;
                           ⛔ seul PITIOT reste vraiment hors registre
```

⚠ **ET UNE RESERVE D'OUTILLAGE** : `rapport_gel_tous_les_champs.py` **tombe** si on le
lance sans `-X utf8` (`UnicodeEncodeError` sur un ⛔ a la l. 587). C'est le meme defaut
que celui retire du garde-fou de 26bis le 15/11. Il faut le lancer ainsi :

```
   .venv\Scripts\python.exe -X utf8 phase2\checks\rapport_gel_tous_les_champs.py
```

### ✅⭐⭐ LE TRI FIN DU LOT B / LOT C EST REFAIT -- 16/11, lecture seule

**La regle est celle du plan**, pas une invention : LOT C = « notre compromis porte DEJA
une AUTRE date d'acte -> c'est un CONFLIT, pas un vide -> sa decision » ; LOT B = le
reste, en trois familles (meme date d'acte, sans date, sans compromis).

⛔⛔ **ET CE TRI A ETE RETIRE LE 16/11 : IL COMPARAIT DEUX CHOSES DIFFERENTES.**
Frederic : *« la date prevue et la date de vente fixee ce n'est pas la meme chose,
pourquoi tu dis cela ??? »*. Il a raison, et **le code du rapport le prouve**
(`rapport_gel_tous_les_champs.py` l. 788-791) : chaque date du classeur est comparee
**A SA PROPRE TRANSACTION** --

```
   « Offre Achat »   <->  notre OFFRE      . date
   « Compromis »     <->  notre COMPROMIS  . date
   « Vente Prevue »  <->  notre COMPROMIS  . date_acte   (la date PREVUE a l acte)
   « Vente Fixee »   <->  notre VENTE      . date        (la vente REELLE)
```

Mon tri mettait « Vente Fixee » (la vente reelle du classeur) en face de « notre date
d'acte PREVUE au compromis ». Ces deux dates n'ont aucune raison d'etre egales : un acte
se signe rarement le jour prevu. **Les « 33 conflits » n'existaient donc pas** -- c'etait
un artefact de ma comparaison, pas un etat de la base.

```
   CE QUI RESTE VRAI, ET MESURE : les 39 ventes a creer
      le classeur porte une date de vente, et NOUS N AVONS PAS DE VENTE   39
      dont le role « vente » manque vraiment au gel                       39
      dont 1 porte un chainage DOUTEUX -> a sauter                         1
   ⛔ ET LE DECOUPAGE LOT B / LOT C RESTE A ETABLIR : je ne sais pas reconstituer
     la regle qui a produit « 9 + 26 » le 13/11, et je ne la devine pas. Les trois
     familles du LOT B, elles, se mesurent sans ambiguite :
        sans compromis chez nous            2   (le plan en annoncait 2 -- IDENTIQUE)
        notre compromis SANS date d acte    5   (3 « les deux vides » + 2 « classeur seul »)
        notre compromis AVEC une date d acte 32
```

⭐⭐ **LE TEMOIN QUI VALIDE LA GRILLE** : « sans compromis » vaut **2** au plan et **2**
aujourd'hui. La regle de tri est donc bien celle-la -- ce ne sont pas les criteres qui
ont change, ce sont les donnees.

⚠ **ET LA NOUVELLE EST MAUVAISE DANS LE BON SENS** : il y a **PLUS de conflits** (33 au
lieu de 26) et **MOINS de ventes creables** (6 au lieu de 9). Le travail d'ecriture est
plus petit, mais la part qui demande un arbitrage humain a grossi.

#### ⛔⛔ L'OBSERVATION CI-DESSOUS EST CELLE QUI AURAIT DU M'ARRETER AVANT D'ECRIRE

Les ecarts des 33 conflits vont de **2 jours a 7 mois** :

```
   84c91bb8  mandat 18060   classeur 2026-11-17   nous 2026-11-15    2 jours
   c67855b1  mandat 18491   classeur 2026-12-21   nous 2026-12-31   10 jours
   a75aef8c  mandat 17158   classeur 2026-10-26   nous 2026-08-28    2 mois
   AYIHPHF5  mandat 13168   classeur 2022-02-28   nous 2021-07-06    7 mois
   a2b6e193  mandat 17712   classeur 2026-11-20   nous 2026-06-06    5 mois + DOUTEUX
```

⚠ **ET LES DEUX DATES NE SONT PAS DE MEME NATURE.** « Vente Fixee » du classeur est la
date **REELLE** de la vente ; notre « Vente Prevue » est la date d'acte **PREVUE au
compromis** (`compromis.date_acte`, = « Signature acte auth. PREVU le » chez Hektor). Un
acte signe 2 ou 10 jours apres la date prevue n'est donc **pas un conflit** : c'est la
vie normale d'un dossier. Un ecart de 7 mois, lui, en est probablement un.

⛔⛔ **J'AI ECRIT CETTE OBSERVATION, PUIS J'AI QUAND MEME PUBLIE LES 33 CONFLITS.**
C'est la faute, et elle est de methode : j'avais sous les yeux la raison pour laquelle
ma comparaison n'avait pas de sens -- « les deux dates ne sont pas de meme nature » -- et
j'ai presente le resultat comme un etat de la base. **Quand une mesure contredit la
nature de ce qu'elle compare, c'est la mesure qu'il faut jeter, pas nuancer.**
⭐ Il n'y a donc **aucune tolerance a decider** : la question n'existait pas.

#### ✅ LES 6 VENTES DU LOT B, NOMMEES (elles sont creables en l'etat)

```
   meme date d acte    d77d9ae1  mandat 18077  2026-11-27 = 2026-11-27
   sans date d acte    LWZL8V5M  mandat 3277   2020-10-29
                       1W2O0DSU  mandat 17593  2025-12-22
                       a5cb141f  mandat 17888  2026-01-13
   sans compromis      b6ddee9b  mandat 18698  2026-12-04
                       90e99ae5  mandat 18673  2026-11-25
```

#### ⛔⛔ ET MON ERREUR, PAYEE PUIS ATTRAPEE -- la decouverte 5 du rapport, en vrai

Ma premiere version du tri convertissait `c_Vente Fixee` de jj/mm/aaaa vers aaaa-mm-jj.
**Or le rapport normalise DEJA ses colonnes** : elles sont toutes en aaaa-mm-jj. Ma
conversion rendait donc `None`, la condition de conflit ne pouvait jamais etre vraie, et
**les 39 ventes tombaient TOUTES dans « meme date »** -- 0 conflit, ce qui aurait ete une
tres bonne nouvelle, et parfaitement fausse.

⭐ **C'est mot pour mot le piege que le rapport annonce lui-meme** (sa decouverte 5 :
« melanger les deux conversions donne un signal MUET qui passe pour un signal VERT »).
⭐⭐ **Et ce n'est pas mon temoin de conversion qui l'a attrape** -- il verifiait seulement
que les deux fonctions ne se confondent pas -- **c'est l'AFFICHAGE DU DETAIL** : voir
« meme date » en face de « classeur 2022-02-28 / nous 2021-07-06 » ne laissait aucun
doute. ⛔ Un comptage ne se croit pas sans un echantillon lisible a cote.

### ✅⭐⭐ AUDIT DES 63 OFFRES ORPHELINES DU GEL -- 16/11, lecture seule

**Frederic : « fais d'abord les 63 orphelines, ca merite sa propre tache ».** Il a eu
raison deux fois : la mesure a trouve un cas que je ne connaissais pas, et elle a
prouve que le lot des 96 est indemne.

#### POURQUOI LE GEL « SE TROMPE » : IL NE SE TROMPE PAS, IL EST INCOMPLET

L'audit de `60CLRO51` donne le mecanisme. Chaine 17387, annonce 37032, mandat 13739,
**et le MEME acquereur (NICOUD, id 322158) sur toutes les transactions** :

```
   compromis cancelled  2021-11-03   -> ligne 60CLRO51   (la tentative ANNULEE)
   compromis active     2022-02-04   -> ligne TFK7BD9K   (celle qui a ABOUTI)
   offre     refused    2021-12-13   -> AUCUN LIEN       ⛔
   offre     accepted   2022-01-10   -> ligne TFK7BD9K
   vente                2022-05-14   -> ligne TFK7BD9K
```

Le classeur porte **DEUX lignes pour ce dossier**. Le gel a correctement donne le
compromis annule a l'une et tout le reste a l'autre -- mais il a laisse **l'offre
refusee orpheline**, alors qu'elle appartient visiblement a la tentative annulee : sa
date, 2021-12-13, est **exactement** celle que le classeur porte pour `60CLRO51`.

⭐⭐ **ET L'ENSEIGNEMENT VAUT POUR TOUT LE CHANTIER** : comparer les NOMS d'acquereur ne
protege de rien ici, puisqu'ils sont identiques sur toute la chaine. **C'est la DATE qui
departage** -- c'est pour ca que la garde du patch des 96 est « une offre existe deja a
la meme date », et non « la chaine porte deja une offre ».

#### LA MESURE : CE QUE LES ORPHELINES RECOUVRENT VRAIMENT

```
   offres sur des chaines que le classeur connait          4 583
   reliees au classeur                                     4 520   (98,6 %)
   ORPHELINES                                                 63   (1,4 %)
      refused 55 . accepted 7 . proposed 1 (sans date)
      ⭐ TOUTES portent un numero Hektor, AUCUNE ne vient du classeur
   mesurables (chaine nette)                                  56

   et ce qu'elles recouvrent :
      49  aucune ligne du classeur ne reclame d'offre sur cette chaine -> SANS OBJET
       2  ⛔ MEME DATE  -> c'est un LIEN manquant, PAS une donnee manquante
       3  ⚠ a moins d'un mois (3, 15, 26 jours) -> probablement des offres DISTINCTES
       2  une ligne reclame une offre, mais a une autre date
```

⛔⛔ **J'AVAIS DIT « UN DEFAUT DU GEL, PAS UN ACCIDENT » -- C'ETAIT ALARMISTE.** Sur
56 orphelines mesurables, **49 n'ont aucune consequence** : aucune ligne du classeur ne
reclame d'offre sur leur chaine. Le vrai sujet se reduit a **2 liens manquants** et
3 cas a regarder.

#### LES 5 CAS, NOMMES

```
   ligne       mandat   date classeur   notre offre                 ecart   etat classeur
   60CLRO51    13739    2021-12-13      2021-12-13 refused  n°17389   0 j   Annulee
   6QDR3G7V     2959    2019-03-06      2019-03-06 accepted n°17721   0 j   Vente reglee
   LWZL8V5M     3277    2020-08-08      2020-08-05 accepted n°20673   3 j   Vente reglee
   3S4ZWOFK    12864    2020-06-12      2020-05-28 refused  n°11959  15 j   Vente reglee
   TRJ5Y59U    16628    2024-03-25      2024-02-28 refused  n°23996  26 j   Vente reglee
```

#### ✅ LE LOT DES 96 EST INDEMNE -- et ca valide le decoupage par etat

```
   4 des 5 cas sont en « Vente reglee »  -> HORS du lot (famille non traitee)
   1 est en « Annulee » (60CLRO51)       -> MA GARDE L A ECARTE
```

⭐⭐ **Les cas delicats se concentrent dans la famille « Vente reglee »**, celle qu'on a
justement mise de cote. Le decoupage par etat, decide pour une raison de CHAINAGE, se
revele juste pour une seconde raison qu'on n'avait pas vue.

⚠ **ET C'EST UN AVERTISSEMENT POUR LA SUITE** : le jour ou l'on traitera les 69 offres
« Vente reglee », **4 des 5 liens manquants y seront**. La garde « meme date » y sera
donc beaucoup plus sollicitee, et il faudra regarder les ecarts de 3 a 26 jours un par un.

⏰ **LA TACHE QUI RESTE, A PART** : relier les 2 offres a date exacte (`60CLRO51` ->
offre 17389, `6QDR3G7V` -> offre 17721) a leur ligne du classeur. ⛔ C'est un geste sur
le GEL, donc il releve de D1 (le re-gel additif), et D1 dit « ADDITIF, on ne retouche
aucun des 12 595 liens ». Deux liens a AJOUTER, aucun a modifier.

### ⛔⛔⛔ AUDIT DE SITUATION DU 16/11 -- POURQUOI CE CHANTIER N'AVANCE PAS

**Frederic : « fais moi un audit de la situation, je comprends pas, ce chantier est
pourtant documente ».** La mesure donne la reponse, et elle est dure.

```
   LE PLAN        234 489 caracteres, 4 298 lignes
   LES TACHES     23 au total  ->  2 cochees, 21 a faire
   phase A  mesurer         7 taches
   phase B  emplacements    3 taches, 0 posee
   phase C  POSER          10 taches, UNE SEULE a pose quelque chose
   phase D  fermer          3 taches, 0 posee
```

#### LA CAUSE N'EST PAS QUE RIEN N'EST FAIT -- C'EST QUE LE PLAN NE LE DIT PAS

```
   A2  l essai d une nuit     FAIT le 15/11, juge le 16   -> etait marque ⬜
   C1  la charge, 16 lignes   POSEE le 14/11 a 06:42      -> etait marquee ⬜
       « patch DEJA ECRIT et non joue » -- faux depuis deux jours
```

⛔ **J'ai moi-meme annonce a Frederic que la charge « attendait depuis deux jours ».
C'etait faux**, et c'est la mesure en base qui l'a dit : les 16 lignes portent les
`ecrit_par` exacts du patch, horodatees au 14/11 a 06:42.

#### L'ETAT REEL DE LA PHASE C, MESURE EN BASE LE 16/11

```
   C1  la charge                   853 lignes origine 'classeur'      ✅ POSEE
   C5  lot B, 1re famille           96 offres marquees 'classeur'     ✅ POSEES le 16/11
   C2  lot A : 303 commissions       0
   C3  Z : 896 dates d annulation    0
   C4  F et G                        0 du classeur
   C6  lot C : 26 ventes             0
   C9  le numero de mandat           0
   C7 / C8 / C10                     non mesurees ici
```

#### ⭐ LA REGLE DE METHODE QUI EN DECOULE, ET QUE FREDERIC A VALIDEE

**Un geste pose, puis TROIS LIGNES au plan** -- pas trois pages d'audit avant chaque
geste. Un plan de 234 000 caracteres qui n'est pas coche fait perdre l'etat du chantier,
et c'est exactement ce qui s'est passe entre le 14 et le 16/11.

### ⛔⛔⛔ ARRET AVANT LES COMPROMIS ANNULES -- UN 6e LECTEUR, ET IL ECRIT CHEZ HEKTOR

**16/11, en enchainant sur la famille suivante.** Les 38 compromis « Annulee » du
classeur etaient prets a etre poses : la regle [A] du chainage ne les vise pas (elle
n'itere que sur `sans_date_du_bien`, et les notres portent la date du classeur), et
l'ecran ne change pas d'etat sur un compromis (`mandatStatutForRegister` ne lit que
`vente_id`, les statuts clos/vendu et la cloture).

⛔⛔ **MAIS `Console/enqueue_refus_offres_mortes_lot.js` SELECTIONNE LES DOSSIERS SUR
« COMPROMIS ANNULE » (l. 217 et 226), ET IL N'A AUCUNE GARDE `transaction_origine`.**

```
   ce que ce script fait : il REFUSE DES OFFRES CHEZ HEKTOR
   sa source « coherence : compromis annule » retient un dossier des qu'il porte
     un compromis annule et une offre encore acceptee
   -> poser 38 compromis annules venus du CLASSEUR, puis relancer ce script, ferait
      refuser 38 offres CHEZ HEKTOR a cause d'une reprise d'historique
```

⭐⭐ **C'EST LE 6e LECTEUR DE LA FAMILLE, ET LE PLUS GRAVE DE TOUS.** L'audit du matin
en avait trouve cinq (la sentinelle, le cockpit, le filet du worker, l'app, les gestes
de masse) et les avait juges proteges ou corriges. **Celui-ci a ete manque**, et pour une
raison precise : je cherchais les lecteurs de `present_in_hektor = false`, alors que
celui-la se declenche sur `state = 'cancelled'` D'UN COMPROMIS. Un critere different,
donc invisible a ma recherche.

```
   les autres lecteurs      CRIENT (une alarme) ou AFFICHENT (une phrase fausse)
   celui-ci                 ECRIT CHEZ HEKTOR
```

⚠ **ET CE SCRIPT A DEJA FAIT UN DEGAT** : les 20 offres refusees a tort le 11/11
viennent de lui (« geste de masse sur un chainage incomplet »).

#### L'ETAT MESURE, ET CE QUI RASSURE MALGRE TOUT

```
   le script est-il PLANIFIE ?        NON -- aucun .ps1 du projet, aucune tache GTI
                                      -> c'est un geste A LA MAIN, donc rien ne part tout seul
   declencheurs sur app_affaire_ledger  3, tous pour le calcul des parties
                                      -> AUCUNE cascade automatique en base
   dossiers DEJA « compromis annule + offre acceptee »   348
   offres acceptees concernees                            348
```

⭐ Donc le danger n'est pas immediat : rien ne se declenche tout seul. **C'est un effet
de bord DIFFERE** -- il attend qu'un humain relance le lot.

#### ⏰ CE QUI DOIT ETRE FAIT AVANT DE POSER UN SEUL COMPROMIS ANNULE

```
   poser la garde `transaction_origine` sur enqueue_refus_offres_mortes_lot.js,
   exactement comme les 5 autres lecteurs : un compromis annule venu du classeur
   ne doit JAMAIS faire refuser une offre chez Hektor.
```

⛔ **ET LES 96 OFFRES DEJA POSEES NE SONT PAS CONCERNEES** : elles sont des OFFRES
`refused`, pas des compromis annules. Le script les ignore (il cherche des offres
`accepted` a refuser, et une offre refusee n'est pas sa cible). Mesure du 16/11 : les
11 controles du lot sont restes justes.

⭐ **LA LECON, ET ELLE EST GENERALE** : une famille de lecteurs ne se balaie pas par UN
critere. J'avais cherche `present_in_hektor`, et le 6e lecteur se declenche sur l'ETAT
d'une autre transaction de la chaine. **Avant chaque nouvelle famille, il faut refaire
le balayage AVEC LE CRITERE DE CETTE FAMILLE** -- ici `state = 'cancelled'` pour un
compromis, `state = 'accepted'` pour une offre « Vente reglee », et l'existence d'une
vente pour les 39 ventes.

### ✅⭐⭐ A1 EST FAIT -- LES HUIT COLONNES NON COUVERTES (16/11, lecture seule)

`phase2/checks/a1_lire_les_huit_colonnes_2026-11-16.py` -- aucun ecrit en base, un
seul fichier produit : `notice/A1_LES_HUIT_COLONNES_2026-11-16.csv`.
⭐ **Pourquoi A1 maintenant** : les 96 offres venaient d'etre posees et n'avaient pas
encore vecu une nuit. Poser autre chose avant leur premiere epreuve aurait double la
surface sans savoir si la premiere moitie tient. A1 n'ecrit rien, et il debloque
**quatre taches** de la phase C a la fois.

```
   lettre  libelle                      rempli / 4 790   formes
   Z       Annulee                         896  (19 %)   DATE a 100 %
   F       En attente de                 3 099  (65 %)   texte, mais MIXTE (voir plus bas)
   G       COMMENTAIRES                  4 131  (86 %)   texte, 2 613 distinctes
   Y       Vente Reglee                  3 756  (78 %)   2 962 dates + 794 TEXTE
   AA      Numero de facture             3 741  (78 %)   3 735 distinctes
   AH      Avis a envoyer (oui / non)    2 266  (47 %)   120 distinctes
   AI      Commentaire Avis                392   (8 %)   dont 115 valent « 1 »
   AJ      Avis envoye                   2 405  (50 %)   « ok » 1 700, puis des PRENOMS
```

#### ✅ Z EST PROPRE -- C3 PEUT ETRE CONSTRUITE

**896 valeurs, et 896 sont des dates.** Le plan annoncait 896 : confirme a l'unite,
et sans une seule forme douteuse. C'est la colonne la plus simple du chantier.

#### ⚠⚠ Y PORTE LE DEFAUT DES DEUX FORMATS -- et dans la proportion connue

```
   2 962 dates lisibles  +  794 TEXTE  =  3 756
   exemples du texte : « 29 decembre23 » . « 8 decembre23 »
   794 / 3 756 = 21 %  -> « une sur cinq perdue en silence »
```

⭐⭐ **C'est MOT POUR MOT le defaut deja paye sur une autre colonne** le 14/11 (« 5
decembre23 rendait None, donc 940 lignes "nous seuls" dont 924 avaient une date »).
⛔ **Il faut donc la MEME tolerance de lecture pour Y avant de toucher a C8**, sinon on
perdra 794 valeurs en silence -- et C8 est l'un des deux plus gros postes du chantier.

#### ⚠ F EST UNE COLONNE A TROIS USAGES MELANGES -- a trancher par Frederic

Le plan dit « F et G se reprennent EN BLOC, SANS INTERPRETER -- sa consigne ». La
mesure montre ce que « en bloc » emporterait :

```
   « V » tout seul                        1 536  (50 %)  un marqueur de suivi
   contient un EMOJI                        753  (24 %)  🟢 🔴 💰 🅿 -- des pastilles
   texte, hors V et hors emoji              810  (26 %)  LES MOTIFS REELS
```

⭐ **ET LES MOTIFS SONT BIEN LA, le plan avait raison** -- j'ai verifie avant d'affirmer
le contraire :

```
   refus (toutes formes)   149      « refus pret » 31 . « refus de pret » 24
   pret / prêt             109      SRU 12 . « trop de travaux » 5
   retractation (+accent)   92      « retractation ecrite » 12 . « retractation SRU » 10
   financement              23      « a change d avis » 3
```

⏰ **LA QUESTION POUR LUI** : reprendre F « en bloc » mettrait aussi 1 536 « V » et
753 pastilles dans `app_affaire_condition`. Faut-il tout reprendre, ou seulement les
810 valeurs textuelles ? ⛔ Je ne tranche pas : c'est sa consigne qui est en jeu.

#### ⚠ AH / AI / AJ : un suivi d'envoi d'avis, avec des prenoms

```
   AH  « oui » 1 830 . « non » 129 . « NON » 112 . « OUI » 8  -> CASSE MELANGEE
       et « pas acq. » 18, « pas vend. » 8 -> ce ne sont pas des oui/non
   AJ  « ok » 1 700 . « X » 219 . puis Marion 192, Nico 59, Claire 24  -> des PERSONNES
   AI  392 valeurs, dont 115 valent « 1 » et 195 « ok »
```

⚠ Avant C9, il faudra decider ce qu'on garde : un booleen normalise, ou le texte brut
avec son prenom. ⛔ Et la contradiction annoncee entre AH et AJ sur 229 lignes s'explique
simplement -- AH dit « a envoyer », AJ dit « envoye » : ce sont deux etapes, pas deux
versions de la meme information.

### ⛔⛔⛔ AUDIT APPROFONDI DE C5 (16/11) -- LE 7e LECTEUR DECIDE DU DECOUPAGE

**Frederic : « pourquoi on saute des etapes, on a juste fait les offres refused 96 ?
refais un audit » puis « approfondis, ne t'arrete pas a une note, verifie ».** Il avait
raison deux fois : je m'etais disperse sur A1 au lieu de finir le lot B, et mon premier
tableau disait « RIEN ne bloque les compromis » -- **c'etait leger**.

#### LA MESURE : 18 FONCTIONS ET 4 VUES REAGISSENT A UN COMPROMIS

Le balayage avec LE CRITERE DE CETTE FAMILLE (et non `present_in_hektor`, celui des
offres) en trouve beaucoup plus que les cinq du matin :

```
   app_statut_redescente_calcule   app_mandat_etat          app_statut_rang
   app_change_annonce_status_...   app_pilotage_stock       app_pilotage_acquereurs
   app_pilotage_affaires_plus      app_registre_dossiers    app_cockpit_activite
   app_get_dossier_timeline        app_chaine_pour          app_geste_affaire_...
   app_notaire_fiche               ... + 4 vues « current » et app_v_mandat_statut
   ⛔ ET AUCUNE N'A LA GARDE `transaction_origine`.
```

#### ⛔⛔ LE 7e LECTEUR : `app_statut_redescente_calcule` -- ET SON NOM DIT TOUT

```
   SI une VENTE    + compte_encore()                     -> « Vendu »
   SI un COMPROMIS + compte_encore() + state IN (active, en_cours) -> « Sous compromis »
   SI une OFFRE    + compte_encore() + state <> 'refused' -> « Sous offre »
   SINON                                                  -> « Actif »
```

⭐⭐ **TOUT REPOSE SUR `app_affaire_compte_encore`, ET ELLE DIT CECI** :

```
   ignoree_le IS NULL  ET  ( numero VIDE  OU  present_in_hektor = true )
   -> « NUMERO VIDE » REND VRAI
   TEMOINS mesures le 16/11 :
      compte_encore(null,   false) = TRUE   <- NOS lignes comptent
      compte_encore('4320', false) = FALSE  <- une ligne Hektor supprimee, non
```

⭐ **Et c'est son DESSEIN** : une transaction nee dans l'app, en attente de son numero,
doit compter. ⛔ Mais une reprise du classeur n'attend aucun numero -- et une offre
acceptee de 2019 ne doit pas faire passer un bien a « Sous offre » aujourd'hui.

⚠ **CE N'EST PAS AUTOMATIQUE** : la fonction est appelee par des RPC de GESTE
(`patch_supprimer_compromis_2026-09-07.sql:123`,
`patch_offre_verrouillee_2026-09-16.sql:159`), qui calculent `statut_apres` et le font
redescendre. Tant que personne ne touche au dossier, rien ne part. **C'est un effet de
bord differe, comme celui du 6e lecteur.**

#### ✅ LES 96 DEJA POSEES SONT INDEMNES, ET C'EST MESURE

```
   93 dossiers touches par les 96
   leur statut redescendu AUJOURD HUI : « Actif . Sous compromis . Vendu »
   -> ce sont les statuts qu ils avaient DEJA, dus a leurs propres transactions
   ⭐ POURQUOI : la 3e condition exige `state <> 'refused'`, et les 96 sont REFUSED
```

#### ⭐⭐⭐ LE DECOUPAGE REEL DE C5, ET IL EST PLUS FIN QUE PREVU

```
   SANS RISQUE -- l etat les exclut des trois conditions
      96  offres « Annulee »            -> refused     ✅ POSEES le 16/11
      38  compromis « Annulee »         -> cancelled   ✅ POSABLES : la condition
          exige active/en_cours, donc un compromis ANNULE n est pas vu
          (+ la garde du 6e lecteur, posee le 16/11, couvre le lot de refus)

   ⛔ A GARDER AVANT DE POSER -- ils changeraient le statut redescendu
      24  compromis « Compromis en attente » -> active  -> « Sous compromis »
       6  compromis (Vente reglee 4, fixee 1, prevue 1) -> active -> idem
      70  offres (Vente reglee 69, prevue 1)  -> accepted -> « Sous offre »
          ⚠ et 4 des 5 liens manquants du gel sont dans « Vente reglee »

   ⛔ TA DECISION (A4)
      39  ventes -> effet « VENDU », une par une
```

⏰ **CE QU'IL FAUT POSER SUR `app_statut_redescente_calcule`** : la meme garde que les
six autres -- une ligne marquee `classeur` ne doit entrer dans aucune des trois
conditions. ⛔ C'est une fonction de PRODUCTION lue par plusieurs RPC : elle se modifie
par patch, avec son inverse et sa repetition.

⭐ **LA LECON SE CONFIRME, ET ELLE EST MAINTENANT PAYEE DEUX FOIS** : le balayage du
matin avait cherche `present_in_hektor` et manque le 6e lecteur (qui se declenche sur
l'etat d'une autre transaction) ; ce balayage-ci, fait avec le critere « compromis », en
trouve un 7e qui se declenche sur `state` ET sur l'ABSENCE de numero. **Chaque famille
demande son propre balayage, et il se fait AVANT de generer le patch.**

### ✅⭐⭐ LE 18/11 AU SOIR -- LES 5 DOUBLONS RETIRES AUSSI DU REGISTRE LOCAL (session neuve)

> ⛔⛔ **TROUVE EN REJOUANT LES MESURES DU § 2.** `supabase/patch_retirer_doublons_offres_classeur_2026-11-18.sql`
> a retire les 5 offres doublons (1001575, 1001576, 1001577, 1001604, 1001619) **CHEZ
> SUPABASE SEULEMENT**. Le registre LOCAL -- qui est le MAITRE d'`app_affaire_ledger`
> (`pull_from_supabase.py:29`) -- les portait encore : **31 361 lignes contre 31 356**, l'ecart
> valant exactement ces 5. Et elles n'etaient PAS au journal `app_affaire_supprimee` (28 lignes,
> aucune des 5), que le run applique en local AVANT de pousser (`affaire_ledger.py:3444`).
>
> ⛔ **SANS GESTE, LE RUN DE 04:00 LES RECREAIT** : `ledger_rows_for_push` fait `SELECT *` sur
> le local puis un upsert (l. 3211 et 3460). Elles remontaient **SANS leur marque `classeur`**
> (`transaction_origine` est dans `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS`) -- donc visibles du
> filet du worker (`transaction_origine=is.null`), celui qui le 15/11 avait colle a une ligne du
> classeur le numero d'une offre Hektor EXISTANTE. Le projet l'avait ecrit
> (`retour_arriere_recopie_app_seule.py`) : retire d'un seul cote, « le push remonte ».
>
> ✅ **GESTE ACCORDE PAR FREDERIC LE 18/11 (« Oui, retire-les »), JOUE A 16:31** :
> `phase2/checks/retirer_doublons_classeur_du_local_2026-11-18.py --pour-de-vrai` (a blanc par
> defaut ; gardes : les 5 cles, toutes `classeur`, toutes absentes chez Supabase avec un temoin
> positif lu). Sauvegarde datee DANS la base locale :
> `app_affaire_ledger_avant_doublons_classeur_20261118_local` (5 lignes).
>
> ```
>    APRES   local 31 356 = Supabase 31 356 . les 5 : 0 . classeur 190
>            plage app avec numero 340 . hors plage 30 826    (voisines intactes)
>    controle INDEPENDANT refait apres coup, meme resultat
>    retour arriere : INSERT INTO app_affaire_ledger
>                     SELECT * FROM app_affaire_ledger_avant_doublons_classeur_20261118_local;
> ```
>
> ⏰ **LE CONTROLE DE DEMAIN MATIN (19/11), APRES LE RUN ET LA DESCENTE** :
> ① local ET Supabase a 31 356, les 5 absentes DES DEUX COTES ;
> ② au journal du run, l'etape « phase2 doublure du ledger d affaires » EN SUCCES -- ⚠ elle
>   est OPTIONNELLE (`run_full_pipeline.ps1` l. 979) : en echec, la recopie 26bis relirait la
>   doublure de ce matin, qui les porte encore, et les remettrait en local ; elles remonteraient
>   alors la nuit SUIVANTE ;
> ③ compte rendu 26bis : `recopiees 0`.
> Les copies locales du gel et des notes (5 liens, 5 notes de trop) se refont seules a la
> descente : ce sont des tables de `sb_pull_state`, rien ne les pousse.
>
> ⭐ **LA LECON** : retirer une transaction de la plage app se fait **DES DEUX COTES, DANS LA
> MEME FENETRE** -- c'est le patron du cobaye du 16/11. Un patch Supabase seul ne tient pas
> une nuit, dans ce sens comme dans l'autre.

### ✅⭐⭐⭐ LE 18/11 -- SON ARBITRAGE DES 41 LIGNES EST FAIT, ET LA DATE D'OFFRE EST AUDITEE

> ⭐ Il a juge les **41 identifiants** de la page d'arbitrage un par un, dans la nuit
> du 17 au 18/11 entre 23:25 et 23:40. **Ses decisions sont dans la base de la page**
> (collection `decisions`), relevees et croisees avec le dossier par
> `phase2/checks/arbitrage_ce_qu_il_a_tranche_2026-11-18.py`. **41 identifiants
> affiches, 41 juges, aucun laisse de cote.**
>
> ⛔⛔ **ET LE CONTROLE DU 18/11 A 06:46 A TROUVE CE QUE CE COMPTE CACHAIT** : la page
> portait **43 LIGNES** pour 41 identifiants, parce que **NEFHS7JI et 1ESJE28Q en
> portent DEUX chacun** (commission ET date d'offre) -- et la base de la page est
> indexee **par identifiant**, donc un seul clic pour deux questions. ➡ **Une ligne
> reste donc a trancher** : la date d'offre de NEFHS7JI, 3 247 jours d'ecart. Voir D4.
> ⭐ LA LECON : **un compte d'identifiants n'est pas un compte de lignes** -- et c'est
> l'identifiant qui portait la decision.

#### ✅ SON VERDICT : 35 FOIS « LE CLASSEUR A RAISON », 6 ECARTEES

```
   « le classeur a raison »  35      dont  32 COMMISSIONS . 3 DATES D OFFRE
   « rien »                   6      dont  3 avec SA NOTE : « l appariement est FAUX »
```

#### ⛔⛔ CE QUE LA POSE DEMANDE, ET CE QUI N'EST PAS ENCORE TRANCHE

```
   ① LA COLONNE EXISTE ET ELLE EST LIBRE -- mesure du 18/11 sur les 32 lignes :
        les 32 id_unique touchent 75 transactions (32 offres, 31 compromis, 12 ventes)
        honoraires_entree      remplie  43 fois   <- CE QUE HEKTOR CALCULE
        honoraires_entree_app  remplie   0 fois   <- LA NOTRE, CLASSE A, VIDE PARTOUT
      ➡ poser le classeur dans honoraires_entree_app est ADDITIF et ne detruit RIEN.
        C'est le chemin deja ouvert par C2 le 17/11 (62 commissions posees).
   ② ⭐⭐ CE N'EST PAS UNE TVA, ET JE L'AI VERIFIE AVANT DE POSER : si le classeur
      etait TTC et nous HT, les 32 ecarts vaudraient x1,2. **UN SEUL** le vaut, et les
      ratios vont de 0,18 a 1,70 DANS LES DEUX SENS (le classeur est plus BAS 21 fois,
      plus HAUT 11). Ce sont donc 32 vrais ecarts de valeur, pas un decalage de regle.
   ③ ⚠ UNE SEULE DE CES 32 MERITE UN REGARD : 61OW86CS, classeur 1 800 contre nos
      9 800 (ratio 0,18, le seul en dessous de 0,6). Un chiffre change ressemble a une
      faute de frappe -- DANS UN SENS OU DANS L'AUTRE. A lui montrer avant de poser.
   ④ ⬜ SUR QUELLE TRANSACTION DE LA CHAINE POSER : une ligne du Sheet touche jusqu'a
      3 transactions. C2 a tranche ce point pour ses 62 ; **il faut relire comment**,
      pas reinventer. Et 27 des 75 sont ANNULEES ou REFUSEES -- or SA DECISION DU
      17/11 sur C2 etait precisement « les 270 annulees NE SONT PAS POSEES ». ⛔ Donc
      cette regle doit etre reportee ici, ou explicitement levee par lui.
   ⛔ RIEN N'EST POSE : c'est une ecriture en production, elle attend son « vas-y ».
```

#### ⛔ LES 6 ECARTEES -- ET MA MESURE EN CONTREDIT DEUX

Sa demande du 18/11 : *« il y a 3 ou 4 appariements qui semblent faux que nous devons
auditer »*. Les voici, **avec ce que le dossier lui-meme prouve** :

```
   ⛔ SUSPECTS, SA NOTE EST CORROBOREE PAR LES DATES (3) :
     1ESJE28Q  commission, ligne 3464 . Sheet « 27 aout24 » <-> nous 2012-11-28
               ➡ DOUZE ANS d'ecart, et aucune autre date pour recoller. Sa note :
                 « 2012 apps et le sheet 2024 ».
     53ZS73KW  date d offre, ligne 227 . Sheet offre 22/10/2024 + compromis dec.24
               <-> nous offre ET compromis au 2026-03-09 . ~17 MOIS d'ecart sur LES
                 DEUX transactions a la fois.
     TR42PT5H  date d offre, ligne 173 . Sheet 16 decembre24 <-> nous 2026-06-18
               549 jours, et le Sheet n'a NI compromis NI vente pour arbitrer.
   ⭐⭐ MAIS DEUX DE SES « RIEN » ONT UNE PREUVE INTERNE QUE L'APPARIEMENT EST **BON** :
     74IL9C8F  Sheet : offre 31/01/2022 . compromis 25/04/2022 . vente 09/09/2022
               nous  : compromis **2022-04-25** (LE MEME JOUR) . vente 2022-09-07
                       . offre 2002-01-31
               ➡ le compromis COLLE A L'EXACT -> le dossier est le bon, et c'est
                 NOTRE date d'offre qui porte une faute de frappe (2002 pour 2022).
     QH6672TZ  Sheet : offre 7 aout19 . vente 19 decembre23
               nous  : offre 2020-08-07 . vente **2023-12-19** (LE MEME JOUR)
               ➡ la vente COLLE A L'EXACT -> le dossier est le bon, et l'ecart est
                 de 366 JOURS PILE sur l'offre : une annee mal saisie.
   ⬜ ET UNE N'A AUCUNE DATE POUR JUGER :
     8Q3LHGZ4  commission, ligne 3579 : classeur 11 000 contre nos 5 400 (x2,04), et
               le Sheet ne porte NI offre NI compromis NI vente. Rien pour arbitrer
               l'appariement -- ni pour le confirmer.
```

⭐⭐⭐ **LA LECON DE CES DEUX CAS, ET ELLE VAUT POUR TOUT L'ARBITRAGE** : un ecart de
date ne dit PAS que l'appariement est faux. Quand une AUTRE transaction de la meme
chaine tombe au jour pres sur le Sheet, le dossier est le bon et l'ecart est une faute
de saisie. **C'est une preuve interne, pas un avis** -- et c'est ce critere que
`alleger_le_dossier_2026-11-18.py` applique pour sa recommandation.

#### ✅⭐⭐⭐ L'AUDIT DES 6 ECARTEES EST FAIT -- 18/11, ET IL TRANCHE LES SIX

> Sa demande : *« il y a 3 ou 4 appariements qui semblent faux que nous devons
> auditer »*. ⭐ **Il en avait 3 sur 4 justes, et deux de ses « rien » etaient a tort.**
> L'audit : `phase2/checks/audit_appariements_suspects_2026-11-18.py`, LECTURE SEULE
> (le Sheet + phase2.sqlite en `mode=ro` + MODELO), et **confronte a l'apparieur
> relance le 18/11**, qui apparie INDEPENDAMMENT du gel.

```
   LA METHODE, et elle ne regarde PAS que l'ecart de date :
     ① la ligne du Sheet EN ENTIER (mandat, vendeur, acquereur, prix, commission)
     ② notre chaine EN ENTIER, dates VRAIES (la cascade, pas la colonne `date`)
     ③ ⭐⭐ LA PREUVE INTERNE : une AUTRE transaction colle-t-elle au jour pres ?
     ④ ⭐⭐⭐ Y A-T-IL UN MEILLEUR CANDIDAT ? dire « faux » n'avance a rien,
       il faut NOMMER le bon -- et l'audit le nomme dans 4 cas sur 4.
```

**⛔⛔ TROIS APPARIEMENTS SONT BIEN FAUX, ET LE GEL S'EST ACCROCHE SUR UN SEUL NOM**

```
   1ESJE28Q  le gel pointe l'annonce 26801 : vendeur BRUET, mandat 2816, prix
             168 000, dates 2012. LE SHEET dit mandat 16758, vendeur RECAMIER,
             prix 119 000, offre du 27/08/2024. Seul point commun : LACROIX.
             ⭐ LE BON BIEN EST CHEZ NOUS : mandat 16758 -> annonce 9194,
               mandants « Patrick RECAMIER Stephanie RECAMIER Michele RECAMIER ».
             ⛔ MAIS AUCUNE TRANSACTION dessus : l'affaire du classeur n'existe pas.
             ⭐⭐ ET L'APPARIEUR NE LA DONNAIT MEME PAS POUR SURE : confiance « A
               VALIDER », cle « 9 sans mandat (acquereur + vendeur) » -- son signal
               LE PLUS FAIBLE -- et il ECRIT « mandat different ? OUI ».
   8Q3LHGZ4  le gel pointe l'annonce 16831 : vendeur CHAPELON, mandat 6732, prix
             199 900, dates 2014. LE SHEET dit mandat 16239, vendeur ROQUES, prix
             181 000, annulee le 23/10/2023. Seul point commun : CHEVALIER.
             ⭐ LE BON BIEN EST CHEZ NOUS : mandat 16239 -> annonce 46472, mandants
               « Maryse ROQUES Bernard ROQUES ». ⛔ Aucune transaction dessus.
             ⭐⭐ ET L'APPARIEUR REFUSAIT DE LE LIER : confiance « AUCUNE »,
               « a trancher (2 pistes) ». LE GEL A LIE CE QUE L'APPARIEUR REFUSAIT.
   53ZS73KW  ⭐ LE BIEN EST LE BON, L'AFFAIRE NE L'EST PAS. Annonce 43091, mandat
             16992, prix 65 000, commission 5 000, vendeurs identiques -- mais notre
             affaire est CHAPUIS (offre et compromis au 09/03/2026, vente 30/07/2026)
             quand le Sheet decrit GIBERT (offre 22/10/2024, compromis 18/12/2024,
             annulee 16/07/2025).
             ⭐⭐⭐ MODELO PROUVE QUE L'AFFAIRE GIBERT A EXISTE : mandat 16992, debut
               13/06/2024, **compromis 17/12/2024** -- a UN JOUR du Sheet. Hektor
               l'a connue, et elle n'est PLUS chez nous.
             ⭐⭐ ET L'APPARIEUR LE DISAIT DEJA, EN UNE PHRASE : confiance « aucune »,
               **« chaine 21551 deja prise par L4505 »**. Le gel a donc mis DEUX
               lignes du Sheet sur UNE SEULE chaine.
```

**⛔ ET UN QUATRIEME EST FAUX, QUE NI LUI NI L'APPARIEUR N'AVAIENT CORRIGE**

```
   TR42PT5H  le gel pointe la chaine 27196 : offre refusee, acquereur
             HALLAERT-THEYS, montant 199 000, mandat 15482.
             ⭐⭐⭐ LE BON DOSSIER EST LA CHAINE 27195, MEME BIEN (annonce 53398) :
                 acquereur   MORAND ZIMMER        = « ZIMMER Emma et MORAND Thomas »
                 vendeur     BELONJE BELONJE BIEL = « Indivision BELONJE-BIEL »
                 montant     209 000              = le prix du Sheet
                 honoraires    9 000              = la Commission TTC du Sheet
                 compromis   24/01/2025, annule   = coherent avec offre 16/12/2024
                                                    et annulation 20/05/2025
             ⛔⛔ ET L'APPARIEUR SE TROMPE ICI AUSSI, EN DISANT « SURE » : sa cle est
               **« 1 mandat seul »** (15482), or UN NUMERO DE MANDAT N'IDENTIFIE PAS
               UNE AFFAIRE -- 4 142 doublons, et ici le mandat a ete REATTRIBUE :
                 mandat 15482  annonce 53398  du 06/02/2023 au 06/02/2025  BIEL/BELONJE
                 mandat 18176  annonce 53398  du 06/11/2025 au 06/11/2026  BELONJE
               ⭐ QUATRE preuves (noms, prix, commission, chronologie) contre UNE
                 (le numero de mandat) : le lien doit pointer 27195.
```

**✅⭐⭐ ET DEUX DE SES SIX « RIEN » SONT A REVOIR -- L'APPARIEMENT EST CERTAIN**

```
   74IL9C8F  mandat 13555 = 13555 . vendeur DEMEESTERE . acquereur ABDALLAOUI .
             prix 67 000 . commission 5 000 -- TOUT COLLE, et surtout :
                compromis   le Sheet 25/04/2022 . nous 25/04/2022   -> 0 JOUR
                vente       le Sheet 09/09/2022 . nous 07/09/2022   -> 2 jours
             ➡ seule la date d'OFFRE derive : 31/01/**2002** chez nous pour
               31/01/**2022** au Sheet. UN CHIFFRE D'ANNEE. Le classeur a raison.
             L'apparieur : confiance « sure », 6 preuves.
   QH6672TZ  mandat 3947 = 3947 . vendeur MALFANT . acquereur VIGNAL . prix 46 500 .
             commission 4 346 = 4 346 -- TOUT COLLE, et :
                vente       le Sheet 19/12/2023 . nous 19/12/2023   -> 0 JOUR
             ➡ l'offre est a **366 JOURS PILE** : une annee mal saisie, rien d'autre.
             L'apparieur : confiance « sure », 6 preuves.
```

⭐⭐⭐ **LE MOTIF COMMUN DES QUATRE FAUX, ET C'EST LA VRAIE TROUVAILLE** : le gel s'est
accroche a **un seul signal faible** -- un nom de famille partage (LACROIX, CHEVALIER),
ou un numero de mandat seul. Les quatre portent la meme marque, et dans trois cas sur
quatre **l'apparieur le disait deja** (« a valider », « aucune », « deja prise »). ⛔ Le
gel a donc retenu des liens que son propre apparieur ne donnait pas pour surs.
➡ ⬜ **A FAIRE, ET C'EST PLUS LARGE QUE CES 6** : balayer les liens du gel dont la
confiance de l'apparieur est « aucune » ou « a valider » -- c'est la FAMILLE, pas le cas
(lecon 9). Les 9 « suspects » du 17/11 en font probablement partie.

⛔⛔ **ET RIEN N'EST CORRIGE EN BASE** : ce sont 4 liens a defaire ou deplacer, plus 2
dates a poser. C'est une ecriture en production, elle attend son « vas-y ».

#### ✅⭐⭐ LE CONTROLE DE MON PROPRE TRAVAIL -- 18/11 06:46, AVANT LA FIN DU RUN

> Sa demande : *« avant que le run de nuit soit fini, controle ton travail »*.
> ⛔ **Il a bien fait de le demander : trois de mes chiffres etaient faux.**

```
   CE QUI ETAIT FAUX, ET C'EST MOI :
     ⛔ « 41 lignes »          -> 41 IDENTIFIANTS pour **43 LIGNES** (NEFHS7JI et
                                 1ESJE28Q en portent 2 chacun)
     ⛔ « 32 commissions »     -> **33**, et 35 verdicts couvrent **36 lignes**
     ⛔ « 27 des 75 annulees » -> **78** transactions, **14 annulees + 15 refusees**
     ⭐⭐ ET LA CONSEQUENCE N'EST PAS UN CHIFFRE : une ligne n'est PAS tranchee
       (la date d'offre de NEFHS7JI, 3 247 jours) parce que la page enregistrait
       un clic PAR IDENTIFIANT. Voir D4, point 3.

   CE QUI EST VERT, ET MESURE :
     ✅ git          HEAD = origin/main (f1fa5e1), rien en attente de poussee, et
                     mes 2 commits ne portent QUE mes 3 fichiers
     ✅ le plan      CRLF pur (0 LF seul), aucune insertion en double
     ✅ mes renvois  les 4 lignes du classeur que je cite (3464, 227, 173, 3579)
                     sont justes, controlees contre LIGNES_A_TRANCHER_ECRAN
     ✅ les scripts  compilent, **aucune ecriture** (ni INSERT/UPDATE/DELETE, ni
                     requete HTTP), sqlite ouvert en `mode=ro`
     ✅ LA BASE      **rien n'a ete ecrit** : les liens des 6 affaires auditees sont
                     INTACTS (1ESJE28Q 2 . 8Q3LHGZ4 2 . 53ZS73KW 2 . TR42PT5H 1 .
                     74IL9C8F 3 . QH6672TZ 2), et TR42PT5H pointe toujours 27196
     ✅ la colonne   `honoraires_entree_app` est **libre sur les 78** (0 remplie) --
                     elle est utilisee ailleurs (66 lignes d'un chantier anterieur),
                     donc la pose reste bien ADDITIVE
```

⚠ **TROUVE EN PASSANT, ET CE N'EST PAS DE MON FAIT** : **10 renvois de ce plan vers
`affaire_ledger.py` sont PERIMES**, le code ayant bouge (derniere retouche le 17/11).
Mesure par le symbole, pas par le calcul : `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` est
**l. 3117** (le plan dit 2875 et 3108) · `colonnes = list(…)` **l. 3019** (dit 3002)
· `for interdite in …` **l. 3213** (dit 3175) · `ledger_rows_for_push` **l. 3208**
(dit 3413) · et `refresh_ledger` **l. 582** quand le plan dit 3396. ⬜ Les corriger
est un geste A PART, il touche 10 endroits du plan -- **je ne l'ai pas fait seul**.
⭐ Les renvois aux lignes du CLASSEUR, eux, sont tous justes : ils ne bougent pas.

#### ✅⭐⭐ LA DATE D'OFFRE : LE MECANISME DU 12/11 EST PROUVE, ET LE PIEGE EST UN NOM

Sa remarque : *« la date de l'offre d'achat du 61OW86CS est erronee, c'est la date de
notre script de masse. Normalement on avait corrige la date !!! »*. **Juste deux fois.**

```
   ⭐⭐⭐ LE TEMOIN POSITIF, sur les 1 206 offres portant une date de script :
        1 198 rendent la VRAIE date par la cascade . **0** rend encore celle du script
        exemple : offre 19130, colonne `date` = 2026-11-11 18:50:50
                  app_dossier_jour_date_transaction() = **2021-02-27**
   ⛔⛔ LA FAUTE ETAIT A MOI : mon script du dossier lisait la colonne `date` BRUTE au
     lieu de la cascade. Corrige, ET l'ecran porte desormais un DRAPEAU sur chaque date
     rendue par la cascade, disant ce qu'elle remplace -- sans ca on ne sait pas d'ou
     vient le chiffre affiche, et c'est ce qui lui a fait perdre du temps.
   ⚠⚠ ET UN NOM M'A FAIT CRIER AU LOUP : app_controle_date_offre() rend une colonne
     `date_lue_journal_non_vide` **qui vaut 0**, et j'ai annonce le controle casse. Son
     propre commentaire dit l'inverse : elle compte LES ANOMALIES. **0 EST UN VERT.**
     ⬜ A renommer (`date_sans_source`) -- ca change la signature, donc ses appelants :
       un geste a part, pas un effet de bord.
   ⭐ LES 8 QUI RENDENT VIDE ONT RAISON : leur propositions_json ne porte QUE notre
     refus du 12/11 (une entree, montant 0) ou des `0000-00-00`. Ce sont les « sans
     aucun recours » du patch du 12/11 : aucune date n'est recuperable, et NULL vaut
     mieux qu'une date inventee.
   ⚠ SIGNAL NOTE, NON TRAITE : 6 de ces 8 n'ont QUE notre refus dans leur journal,
     montant 0, initiateur 0 -- une offre que notre geste a peut-etre FABRIQUEE. A
     rapprocher des « 20 offres refusees a tort le 11/11 ».
```

---

### ✅⭐⭐⭐ LE SOIR DU 17/11 -- D1, LES SENTINELLES, ET SES DECISIONS

#### ✅ B2 ET B3 -- LES DEUX SENTINELLES POSEES

```
   B2  app_v_classeur_ligne_sans_lien . data.classeur_ligne_sans_lien . WARNING
       85 lignes au depart, 92 apres la table remise a jour, 91 apres le lien pose
       ⚠ LE SEUIL SUIT LA MESURE, et il doit BAISSER quand un re-gel rattachera
   B3  app_v_affaire_note_condition_orpheline . CRITICAL . seuil 0 VRAI
       6 notes + 5 conditions orphelines, TOUTES DECLAREES (`deja_declaree`)
       ⭐⭐⭐ et la mesure a corrige ce que j'allais ecrire : ce ne sont pas des
         donnees metier perdues mais des RESTES D'ESSAIS du 23/10, dont l'une
         porte « a garder pour la preuve » -> ON NE SUPPRIME RIEN
   ⛔⛔ TEMOIN POSITIF sur B3 : filtre RETOURNE -> 11, en CRITICAL, et elle NOMME
     chaque ligne. Le 0 venait donc de la base, pas d'un filtre mal lu.
```

#### ✅⭐⭐ SES DECISIONS DU 17/11 -- LES COLONNES SONT TRANCHEES

```
   C10 « Prix »       ⛔ ECARTEE. ⭐⭐⭐ ET UNE MESURE L'A TRANCHEE SEULE : 9 280 de
      nos 9 281 ventes portent DEJA leur montant. Il en manque UNE.
      ⛔⛔ Et la colonne n'est meme pas un prix : 1 008 de ses 4 726 valeurs sont
        des DEPARTEMENTS (43, 42, 63) -- elle a CHANGE D'USAGE vers 2021
        (2019 : 94 % de departements . 2022 : 0,6 %).
   U / X « Signe » / « Signee »   ⛔ ECARTEES. Le croisement dit ce qu'elles
      sont : U = le compromis est signe, X = l'acte est signe -- et nous avons
      deja cette information dans l'etat de nos transactions.
      ⚠ 68 lignes restent curieuses : ventes reglees SANS compromis signe.
   AC « Adresse Acquereur »   ⛔ ECARTEE (62 lignes, texte multiligne)
   AE « Adresse Vendeur »      ⛔ ECARTEE (804 lignes, DEUX formats melanges)
   AK « Divers »               ⛔ ECARTEE (12 lignes de notes comptables)
   AA « Numero de facture »    deja rapatriee par C8 -> la question est l'ECRAN
   ME6S0TR9 et 6a259cce        ⛔ ON NE GELE RIEN
```

#### ✅ C6 -- MESUREE, ET IL N'Y A PRESQUE RIEN

```
   3 756 ventes affirmees par le classeur
      3 728  DEJA chez nous                    99,3 %
         21  sans aucun lien
          4  a creer, SANS conflit
          3  « conflit » de date d'acte -- et AUCUN n'en est un :
             AYIHPHF5 notre compromis est ANNULE (deux affaires distinctes)
             df0ce30c et a56ce827 : compromis ACTIFS, leur `date_acte` est une
               date PREVUE, le classeur donne le REEL -- c'est ce qui a fait
               ecarter C7 le matin meme. Et HEKTOR LES RENDRA.
   ⭐ Les ventes posables : S0GH1R74 (24/09/2020, chaine n'ayant qu'une offre
     refusee) et a5cb141f (17/01/2026) -- ⚠ mais a5cb141f a un compromis ANNULE
     et une offre REFUSEE dans sa chaine : poser une vente dessus serait
     incoherent. A REGARDER.
```

#### ⛔⛔⭐ LES 2 LIENS MAL CIBLES DU GEL -- CORRIGES, ET NEUF « FAUX » N'EN ETAIENT PAS

Sa demande : *« il faut corriger l'erreur du regel et comprendre pourquoi !! »*.
⚠ Ce n'etait pas le re-gel du 17/11 (mes 195 liens sont deterministes) mais
**le gel initial du 29/10**. L'audit a balaye **les 12 791 liens** (lecon 9).

```
   ✅ la date COLLE a l exact                      7 986   62,4 %
   ecart, mais aucun meilleur candidat             4 504   35,2 %
   ⛔ un candidat a ECART ZERO existe                  11
```

⛔⛔ **ET SUR LES 11, NEUF ETAIENT DES FAUX POSITIFS. Corriger en masse aurait
abime neuf liens justes.**

```
   ① HUIT = LA CONSEQUENCE DE NOS PROPRES GESTES. Les transactions pointees
     portent des dates du 11/11 a 19:03-19:30 et du 12/11 a 15:26-15:27 -- des
     HEURES GROUPEES, donc nos gestes de masse (« la date d'une offre refusee EST
     la date du refus », 1 435 offres). Le gel pointait LA BONNE offre ; c'est SA
     DATE qui a change. LE LIEN EST JUSTE, LA DATE NE L'EST PLUS.
   ② UN = f1aedc01 porte DEUX liens (une offre chacun) : je comparais le moins bon.
```

⭐⭐ **LES DEUX VRAIS, soit 0,016 % des liens** :

```
   AYIHPHF5 -> 14111 alors que 14109 colle a ZERO JOUR
     ⭐ LA LIGNE VOISINE EXPLIQUE TOUT : Z3DYDC4X porte LE MEME MANDAT 13168, le
       meme terrain, le meme negociateur, le meme prix 113 000 -- et son compromis
       est du 06/04/2021, ANNULE, acquereur GENOUX. C'est EXACTEMENT 14111.
     ➡ DEUX AFFAIRES SUCCESSIVES : GENOUX qui tombe, puis BLANC MOURETTE qui
       achete. L'apparieur a donne a la seconde le compromis de la premiere.
     ⛔ POURQUOI, ET JE NE LE DEVINE PAS : les TROIS compromis du bien portent
       GENOUX chez Hektor -- le nom ne departageait pas. Et 14111 est DANS la
       chaine 14109 : il a pris une transaction de la bonne chaine, pas la bonne.
   fa06e4e5 -> 28931 (offre du 27/07) alors que le classeur dit le 15/07 et que
     28930 porte exactement cette date, libre.
```

✅ **CORRIGES** -- le SEUL geste non additif du chantier (la clef primaire porte
`app_affaire_id`, donc un deplacement est un DELETE + INSERT). 8 controles.
⭐⭐⭐ **LA PREUVE** : « date exacte » 7 986 -> **7 989**, « liens faux » 11 -> **0**.

⚠ **IL RESTE 9 « SUSPECTS »** (un candidat colle mieux, mais pas a zero jour) --
a regarder UN PAR UN, surtout pas en masse : l'audit vient de montrer pourquoi.

#### ⛔⛔ ET DEUX FAUTES A MOI, TOUTES DEUX TROUVEES PAR SES QUESTIONS

**1. MES TROIS SAUVEGARDES DU JOUR ETAIENT OUVERTES** a `authenticated` --
SELECT, DELETE **et TRUNCATE**. Or le patron avait change LA VEILLE : « toute
nouvelle sauvegarde NAIT FERMEE ». Trois fois la meme faute, dans le meme
chantier. ✅ Fermees (public, anon ET authenticated nommement), `service_role`
garde la lecture -- verifie par un temoin, sinon le retour arriere deviendrait
impossible.

**2. MON TEMOIN EST DEVENU UN PIEGE ET A FAIT UN FAUX ROUGE.** Il exigeait de
retrouver AYIHPHF5 parmi les liens faux : juste avant la correction, absurde
apres -- le script sortait en CODE 2 alors que tout allait bien. **Un faux rouge
est aussi grave qu'un faux vert.** ➡ Le temoin juste ne verifie pas un CAS mais
une CAPACITE : la methode mesure-t-elle encore les deux cotes ?

---

### ✅✅⭐⭐⭐ C4, 3e PATCH -- POSE EN PRODUCTION LE 17/11 A 13:03

```
   patch applique via le POOLER (l'hote direct n'a plus d'IPv4), code 0
   LOT 1   80 textes de F ajoutes aux notes existantes
   LOT 2   28 conditions suspensives
              Obtention Credit                     23
              Depot du permis de construire          3
              Obtention du permis de construire      2
   CATALOGUE  4 -> 6 clauses
   21 CONTROLES JUSTES, dont les quatre qui comptent :
      . LE TEXTE D AVANT EST INTACT                      0 perdu sur 80
      . chaque condition pointe une clause EXISTANTE      0 orpheline
      . les 195 notes de C5 . les 4 325 du 2e patch . les 5 conditions saisies
      . TEMOINS INVERSES : 0 condition en « levee », 0 echeance hors 2024-2027
```

#### ⭐⭐ LE TEMOIN A L'OEIL, ET IL CONFIRME SON DECODAGE

Une note completee, telle qu'elle se lit maintenant (annonce 58958) :

```
   G : le commentaire -- 12.11 OFFRE ok 💰pc
   CI ok
   [classeur F, suivi en cours au 17/11/2026] 20/11 rdv Me Lucht-Rocher pc
```

⭐ **Le commentaire de G est intact, le texte de F est dessous.** Et on y lit
« **CI ok** » puis, sur une autre affaire, « **CI-A en attente** » -- ce qui confirme
sa lecture du 17/11 (`CI` = carte d'identite) **et** ajoute un signe : **`CI-A` est la
carte d'identite de l'ACQUEREUR**.

Une condition posee (annonce 59491, compromis du 31/07/2026) :

```
   « Depot du permis de construire »  echeance 2026-11-30  etat attente
   texte d origine : « 30/11 DPC30/11 OPC01/3 DB15/6 Me BDH / Me Damas »
```

⚠ **Et une reserve a dire** : sur les 23 conditions de credit, **8 n'ont pas de
delai** (`jours` vide) parce que leur ligne ne porte **pas d'ADP** -- on ne connait
donc que l'echeance, pas le depart. On ne l'invente pas.

---

### ⛔⛔ C4, 3e PATCH -- MON 1er VERDICT, RENVERSE LE JOUR MEME

> ⛔ **GARDE PARCE QU'IL EXPLIQUE UNE FAUTE**, pas parce qu'il est vrai. Le verdict
> juste : **80 textes de F et 28 conditions**, catalogue a SIX clauses. Voir la
> section 9 de `notice/C4_LE_DECODAGE_DE_LA_COLONNE_F_2026-11-16.md`.
>
> ⭐⭐⭐ **SA CORRECTION** : « MA REGLE SUR LES DONNEES DES TRANSACTIONS EN COURS NE
> PORTAIT PAS SUR LES NOTES ». Sa regle protege du CONFLIT ; la bonne question est
> « HEKTOR PORTE-T-IL CETTE DONNEE ? » -- et la mesure dit NON deux fois.
>
> ⛔⛔ **ET MES DEUX FAUTES DE CRITERE** : `entetes.index("G")` cherchait un nom
> d'entete alors que « G » est la LETTRE de la 7e colonne (entete COMMENTAIRES) --
> un zero par construction ; puis, corrigee, elle confondait « la ligne a un
> commentaire G » avec « LE TEXTE DE F est pose ». **47 est devenu 80.**

#### l'ancien verdict, pour memoire


Le 2e patch annoncait : *« reste le 3e : les 86 CONDITIONS en attente, dont l'echeance
se lit dans les abreviations »*. **L'audit dit NON, et c'est sa propre regle qui le
dit.** Aucune ligne de code n'a ete ecrite en base.

#### ⭐⭐⭐ LE VERDICT : 0 SUR 89

```
   les lignes « en cours » du classeur                  86
      dont elles portent au moins une abrev datee       40
      dont AUCUNE abreviation datee                     46
   les abreviations datees, au total                    89
      DB 40 . ODP 26 . ADP 18 . DPC 3 . OPC 2

   LES TROIS CONDITIONS DE SA REGLE, toutes exigees :
      a  l echeance est ANCREE (sinon on ignore l annee)
      b  elle n est PAS dans le futur
      c  l affaire est SORTIE du vivant, OU sa date a plus d un an

      ECARTEE  b -- echeance DANS LE FUTUR                    71
      ECARTEE  a -- echeance indatable                          9
      ECARTEE  c -- affaire ENCORE VIVANTE et recente           8
      ECARTEE  DB -- sa decision du 17/11 : elle va en NOTE      1
      ---------------------------------------------------------------
      ✅ POSABLES                                               0
      ✅ et le compte boucle : 89 ecartees + 0 = 89
```

#### ⛔⛔ UN ZERO NE SE CROIT PAS SANS TEMOIN POSITIF -- EN VOICI TROIS

Un « 0 posable » peut vouloir dire « le filtre refuse tout par un defaut ». On relache
donc **une seule condition a la fois** et on regarde si le code sait dire OUI :

```
   sans (b) : on accepte les echeances dans le futur        38  <- il sait dire OUI
   sans (c) : on accepte les affaires encore vivantes        9
   sans la reserve DB/DPC/OPC                                1
```

➡ **Le zero est donc VRAI** : il vient de la regle, pas d'un defaut de mesure.

#### ⭐⭐⭐ POURQUOI, EN UNE PHRASE

**Une affaire « en cours » du classeur est le PRESENT, pas de l'historique.** Chez nous :

```
   42  ont un compromis ACTIF        <- Hektor les rend encore
   38  n ont qu une OFFRE, pas de compromis
    5  ne sont reliees a aucune transaction
    1  est tombee depuis     <- la SEULE qui passerait... et c est un DB
```

Et c'est pour ca que 71 echeances sur 89 sont dans le futur : **ce sont les echeances
d'affaires qui courent**. Les reprendre, ce serait ecrire dans le present que Hektor
entretient -- exactement ce que sa regle interdit depuis le debut du chantier.

➡ Ces conditions ne relevent donc pas du RAPATRIEMENT, mais du **DEVELOPPEMENT** :
la saisie des conditions suspensives dans l'app. `app_affaire_condition` porte
**5 lignes**, toutes `origine = 'saisie'`, toutes **sans `date_echeance`** -- l'ecran
pose le libelle et les `jours`, jamais la date.

#### ⛔⛔ LE TROU QUE L'AUDIT A TROUVE EN PASSANT : 47 TEXTES NE SONT NULLE PART

Le generateur de notes du 2e patch ne prend `F` que pour les etats **« Annulée »** et
**« Vente réglée »**, plus la date butoir. **Une ligne « en cours » sans `DB` n'est donc
partie nulle part** :

```
   les 86 lignes en cours :
      parties en note par leur DB               39
      parties en note par leur colonne G         0   (aucune n a de G)
      ⛔ NULLE PART, ni note ni condition       47
```

Et ce ne sont pas des miettes -- c'est **le carnet de bord vivant de l'agence** :

```
   « 23/11 copie C20/11 Me Latour »            « 20/11 rdv Me Champelovier »
   « 17/11 att. fonds notaire V »              « 19/11 CI-A  Me Poyet/Chazotte »
   « 20/11 accord transfert fonds Binga-Hanto »
   « 28/11 copie C27/11 liée vente 18786 DEGROOTE / IMAW C18/11 »
   « 19/11 rdv PUA accord du juge habilitation Sauret »
```

⬜ **A TRANCHER PAR LUI** : les poser en note (`origine = 'classeur:F-en-cours'`,
additif, sans toucher a une condition), ou ne rien faire parce que c'est le present que
l'app doit porter. ⚠ Une reserve a dire : ces textes sont un suivi **qui bouge chaque
semaine**, donc les poser, c'est figer une photo.

#### ⭐⭐ ET LE DECODAGE DE F S'ENRICHIT DE DEUX SIGNES

```
   C<date>   la date du COMPROMIS prevu -- « copie C20/11 » = copie recue,
             compromis le 20/11. Elle revient dans 20 des 47 textes.
   DP<date>  vu dans « 16/12 dDP16/12ADP ODP05/1 DP31/1 31/3 » -- ni DPC ni ODP.
             ⛔ Mes cinq abreviations ne la connaissaient pas : le decodage du
             16/11 n'est donc pas complet, et il ne pretend pas l'etre.
```

#### LE FICHIER

```
phase2/checks/c4_auditer_les_86_conditions_2026-11-17.py   l'audit, LECTURE SEULE
notice/C4_LES_86_CONDITIONS_AUDIT_2026-11-17.csv           les 89 abreviations,
   une par ligne : son etat au classeur, son etat chez nous, son echeance ancree
   et POURQUOI elle est ancree ainsi
```

---

### ✅⭐⭐ C4, 2e PATCH -- 4 325 NOTES POSEES LE 17/11

Sa consigne, depuis le 31/10 : **« en bloc, tels quels, sans aucune interpretation »**.
Aucun texte n'est reformule ni resume.

```
   ce qui a ete LU, par source           5 050 textes
      G : le commentaire                 4 132
      F : le texte de l annulation         539   (hors des six motifs)
      F : le financement                   232
      F : remarque d apres-vente            82
      F : la DATE BUTOIR                    65   sa decision du 17/11
   ce qui est POSE                       4 325 notes, 4 936 textes fusionnes
      classeur:G                         3 484
      classeur:F+G                         585   une note qui porte les deux
      classeur:F                           256
   ecartees                                  89 sans aucun lien au gel (A6)
                                              0 parce que la chaine etait prise
```

#### ⭐⭐⭐ LE PREALABLE DE L'AUDIT DU 16/11 A PAYE, ET VOICI COMMENT

L'audit avait trouve que `app_affaire_note` portait **DEJA 195 lignes
`origine = 'classeur'`** -- les notes d'acquereur de C5. Si C4 avait utilise la meme
valeur, **un retour arriere sur l'un aurait emporte l'autre**.

➡ Ce patch pose donc `classeur:F`, `classeur:G` et `classeur:F+G`, **jamais
`classeur` seul**. Et son INVERSE vise ces trois valeurs : il ne PEUT PAS toucher
C5. Le controle l'exige a chaque passage : **les 195 de C5 doivent rester a 195**.

#### ⛔⛔ ET LA CLE PRIMAIRE A FAIT ECHOUER MA PREMIERE VERSION

`app_affaire_note` a pour clef primaire **`app_affaire_id` SEUL** : donc **UNE SEULE
NOTE PAR TRANSACTION**. Je voulais poser F et G separement sur la meme transaction ->
« duplicate key value violates unique constraint app_affaire_note_pkey ».
✅ Rejete AVANT le commit, verifie : 195 notes de C5, 0 de C4, rien n'avait bouge.

⭐ **TROIS CONSEQUENCES, TOUTES TRAITEES** :

```
   1  les textes d une meme ligne sont FUSIONNES en UNE note, chacun PREFIXE de
      sa source -- rien n est perdu (4 936 textes dans 4 325 notes), rien n est
      melange, et l ordre est stable pour que deux executions donnent le MEME texte
   2  on vise une transaction LIBRE de la chaine quand la plus avancee porte deja
      une note (les 195 de C5, les 9 saisies) -- additif, JAMAIS un ecrasement
   3  si toute la chaine est prise, on ECARTE et on COMPTE -> **0 cas**, le repli
      a suffi partout
```

#### ✅ LES ONZE CONTROLES

```
   F 256 . G 3 484 . F+G 585          tous justes
   LES 195 DE C5 INTACTES               195 = 195
   les 9 saisies de l app                 9 = 9
   aucune note vide . toutes rattachees a une CHAINE      0 = 0
   une seule note par transaction : 4 529 notes pour 4 529 transactions
   VOISINES : 169 motifs . 450 dates . 2 588 avis
```

⚠ **UN SIGNAL, POSE TEL QUEL PAR SA CONSIGNE** : la note la plus longue fait
**17 129 caracteres**. C'est une cellule du Sheet qui porte tout un historique
d'affaire. On ne l'interprete pas, mais il faut savoir qu'elle existe -- un ecran qui
l'afficherait sans la replier serait illisible.

---

### ✅⭐⭐⭐ C4, 1er PATCH -- 169 MOTIFS D'ANNULATION ET 2 CLAUSES, 17/11

#### ⛔⛔ MA PREMIERE NORMALISATION N'EN ETAIT PAS UNE, ET IL L'A VU A L'OEIL

Il avait tranche : « Les 216 motifs normalises, les 492 phrases uniques partant en
note ». Ma premiere version prenait **l'ecriture la plus frequente de chaque groupe**
comme libelle. Resultat :

```
   « retractation SRU »  12   et   « SRU »              12   <- la MEME chose
   « annule »             9   et   « annulee »           9   <- le MEME mot
   « refus pret »        55   et   « 2 refus de pret »   4
   -> 41 libelles, dont des doublons EVIDENTS. Ce n'etait PAS normalise.
```

⭐⭐ **GROUPES PAR THEME, les 41 ecritures disent SIX causes** -- et il les a
validees :

```
   1  Pret refuse                        70 lignes posees
   2  Retractation                       61
   3  Annule sans motif precise          20
   4  Changement de situation acquereur   9
   5  Travaux ou etat du bien             7
   6  Permis refuse                       2
   -----------------------------------------
                                        169
```

⛔ **Et j'avais mal range « refus PC »** dans le pret : un refus de PERMIS n'est pas
un refus de PRET. Il a son propre motif.

⭐ **ON S'EN EST TENU AUX CLEFS QU'IL A VUES.** Plusieurs des « non classees » y
entreraient logiquement (`refus financement`, `2refus pret`, `montant travaux trop
eleve`), mais les ajouter aurait change un compte qu'il avait valide. **36 lignes
partent donc en note, et le script les NOMME** -- une absence se declare.

#### ✅ CE QUI EST POSE

```
   le CATALOGUE passe de 2 a 4 clauses :
      3  Permis de construire       ( 0 j)  rang 3
      4  Delai de retractation SRU  (10 j)  rang 4   <- le delai legal
   ⛔ RIEN pour le pret : « Obtention Credit » (id 2, 45 j) EXISTAIT DEJA, et
     ADP/ODP n'en sont pas deux clauses mais le DEPART et l'ECHEANCE de celle-la
     (24 fois sur 24, ecart median 31 jours). J'ai failli creer un doublon.
   169 MOTIFS dans motif_annulation_app, sur LA MEME transaction que leur date
```

#### ⭐⭐⭐ LE CONTROLE QUI DONNE SON SENS A TOUT LE CHANTIER

```
   LA DATE *ET* LE MOTIF SUR LA MEME LIGNE :  111
   motifs sans date (perimetre different)  :   58
```

**111 affaires disent maintenant QUAND elles sont tombees et POURQUOI.** C'est ce que
C3 (450 dates, 16/11) et C4 (169 motifs, 17/11) devaient produire ensemble -- et A16 le
disait des le 09/11 : « nous savons qu'une vente tombe, JAMAIS POURQUOI ».

#### ⚠ DEUX DEFAUTS DE SQL, TOUS DEUX REJETES AVANT LE COMMIT

```
1  `cross join lateral (select row_number() over ())` -- la colonne n'y est pas
   visible : « column v.ordre does not exist ». row_number() se met dans le SELECT.
2  `id` du catalogue est TEXT, NOT NULL, et SANS AUCUN DEFAUT -- ce n'est pas une
   sequence mais un identifiant choisi a la main ('1', '2'). Il faut le FOURNIR :
   le maximum numerique + 1, en ne lisant que les ids numeriques.
```

✅ **Et les deux fois, la verification a montre que RIEN n'avait ete ecrit** :
catalogue a 2, 0 motif, pas de sauvegarde. Le `begin/commit` du patch a tenu.

---

### ✅⭐⭐⭐ LE DEFAUT DE B1 EST REPARE -- 17/11, ET IL ETAIT DORMANT

Trouve en analysant le run a sa demande : « il faut analyser le run et la descente pour
corriger ces erreurs ». **B1 a pose trois colonnes de CLASSE A chez Supabase et les a
oubliees dans LES DEUX listes de `phase2/sync/affaire_ledger.py`.**

#### ⛔⛔ RIEN N'AVAIT CASSE, MAIS PAR ACCIDENT

Le push n'envoie que ce que **le LOCAL** possede -- et le local ne possedait pas ces
colonnes non plus. **Les deux moities manquantes s'annulaient.** Le jour ou l'une des
deux aurait ete reparee SEULE :

```
   1  refresh_ledger (l. 3396) cree la colonne en local   -> VIDE
   2  ledger_rows_for_push (l. 3413) l'envoie             -> DU VIDE
      ⛔ et EFFACE chez Supabase les 3 729 reglements et 3 671 factures de C8
   3  redescendre_ce_que_l_app_possede (l. 3481) arrive APRES : elle ramene
      le vide qu'on vient d'ecrire
```

⭐ « LA CAUSE N'EST PAS LE PUSH, C'EST L'ORDRE » -- lecon du 07/09, ecrite juste
au-dessus de `ledger_rows_for_push`. ⚠ **Et c'est exactement le remede que j'avais
propose vingt minutes plus tot**, avant de mesurer l'ordre du run : « ajouter les trois
colonnes a la liste du local ». Il aurait ouvert la porte.

#### ⭐⭐ L'AUDIT A TROUVE QUE LA LISTE SERT DEUX FOIS

```
   l. 3175   for interdite in COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS   exclut du PUSH
   l. 3002   colonnes = list(COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS)   dans la REDESCENTE
```

Son nom ne le dit pas : c'est **le registre des colonnes de CLASSE A**, et c'est la
redescente qui les REMPLIT. Avec deux filets d'ordre deja poses le 16/10 (colonne
absente de Supabase -> non demandee ; absente du local -> non ecrite).

#### CE QUI EST FAIT, ET SEULEMENT CA

```
   vente_reglee_app     ajoutee aux DEUX listes   (3 729 valeurs)
   numero_facture_app   ajoutee aux DEUX listes   (3 671 valeurs)
   numero_mandat_app    ⬜ VOLONTAIREMENT ABSENTE -- sa decision du 17/11 de ne pas
                        rapatrier la colonne C (33 numeros recycles). Elle reste vide.
   la clause d'execution posee dans le COMMENTAIRE des deux colonnes en base,
      la ou B1 l'avait oubliee
   creees en local 29 -> 31 . protegees 10 -> 12 . symetrie : PARFAITE
```

#### ⭐⭐⭐ LE REMEDE DE FOND : UN ESSAI, ET SA LECON DE METHODE

`phase2/checks/test_colonnes_classe_a_dans_les_deux_listes.py` -- **4 verts, code 0**.

⚠⚠ **ET VOICI CE QUI A RENDU CET ESSAI DIFFICILE A ECRIRE** : j'ai d'abord voulu
controler la SYMETRIE des deux listes. **Elle n'aurait RIEN attrape** -- les trois
colonnes de B1 manquaient dans les DEUX listes, donc SYMETRIQUEMENT.
➡ **Un controle interne au code ne peut pas voir ce que le code ignore.** Il faut
comparer **a la BASE**, seule a savoir quelles colonnes de classe A existent vraiment.

✅ **TEMOIN INVERSE FAIT, et il nomme les deux formes du defaut** :

```
   A  colonne retiree DES DEUX listes    -> code 1, « colonne de classe A OUBLIEE »
   B  colonne retiree de la BOUCLE seule -> code 1, « protegee jamais creee en local »
   source RESTAURE a l'octet (207 336) et l'essai redevient code 0
```

⭐ Et **les absences se DECLARENT** : `ABSENCES_DECLAREES` porte `numero_mandat_app`
avec SA raison et SA date -- sinon l'essai rougirait pour une decision prise, et on
apprendrait a ignorer son rouge.

#### ✅ ET LE SECOND « DEFAUT » N'EXISTAIT PAS

J'avais annonce que la table des avis n'etait pas descendue en local. **Faux** : j'avais
juge AVANT la descente, qui tourne a **06:45** et non 07:45 comme je l'avais dit -- et
le run de 04:00 tournait encore (`SCHED_S_TASK_RUNNING`, code 267009, que j'ai failli
prendre pour un echec). Mesure apres 06:45 : `app_classeur_avis` porte bien **2 588
lignes en local**.

#### ⛔⛔ ET UNE FAUTE D'OUTIL, LA TROISIEME DE LA SEMAINE

Ce bloc a d'abord ete ecrit **par Bash**, qui a interprete les backticks comme des
substitutions de commandes : tous les noms de fichiers et de fonctions ont ete MANGES,
les quatre blocs de code ont disparu, et Bash a meme tente d'EXECUTER
`affaire_ledger.py` comme un script shell. Le fichier source est intact (207 336
octets, syntaxe verifiee) -- mais le bloc du plan a du etre retire et reecrit.
➡ **REGLE : tout texte portant des backticks passe par un FICHIER, jamais par Bash.**
C'est en memoire depuis deux fois ; cette fois-ci est la troisieme.

---

### ✅⭐⭐ C8 EST FAIT -- LES DEUX PLUS GROS POSTES, POSES LE 16/11

#### LA CIBLE EST LA VENTE, ET LA MESURE EST D'UNE NETTETE PARFAITE

```
   lignes du classeur reliees a UNE vente       3 735
   lignes reliees a PLUSIEURS ventes                0   ⭐ AUCUNE ambiguite
```

C'est logique : « vente reglee » date le REGLEMENT d'une vente, et une facture suit
une vente. Ni l'offre ni le compromis ne portent cela. **Zero cas a trancher** -- le
lot le plus propre du chantier.

#### LE TRI DES 3 802 LIGNES

```
   ✅ 3 730  UNE vente, rien de pose  -> POSEES (Y 3 729 . AA 3 671)
   ⚠      0  plusieurs ventes
   ⚠     72  aucune vente chez nous   -> emportent Y 27 . AA 70
   ·      0  deja pose
   partition  3 802 = 3 802
```

#### ⭐⭐⭐ LE PIEGE DE Y EST DESARME, ET SANS PARSEUR

Le classeur ecrit ses dates sous DEUX formes, et ce defaut a coute **924 lignes en
silence le 14/11**. Mesure de ce lot : **2 962 dates `jj/mm/aaaa` et 794 TEXTES**
(« 29 decembre23 »).

⭐ **CE PATCH N'EN PERD AUCUNE, PARCE QU'IL NE CONVERTIT RIEN** : la colonne est en
TEXT (decision de A1) et on pose le **BRUT**. Le parseur tolerant sert a LIRE et a
COMPARER, pas a POSER.

**La preuve, apres la pose** :
```
   Y au format jj/mm/aaaa         2 938   sur 2 962 au classeur
   Y en TEXTE                       791   sur 794
```
Et l'ecart s'explique a l'unite : les 72 lignes hors de portee emportaient 24 dates et
3 textes. **2 962 - 24 = 2 938 . 794 - 3 = 791.**

⛔ **IL RESTE DONC LA LECTURE TOLERANTE**, et c'est le commentaire de la colonne qui
l'exige : « Lecture tolerante : charge de C8 ». ➡ Un SECOND geste, une fonction de
lecture qui normalise quand elle peut. On a pose d'abord ce qui ne se perd pas.

#### ✅ LES ONZE CONTROLES

```
   vente_reglee_app             3 729 = 3 729
   numero_facture_app           3 671 = 3 671
   hors-type (pas une vente)        0 = 0
   numeros de facture distincts 3 665   (quasi uniques, comme A1 le disait)
   la sauvegarde porte le lot   3 730 = 3 730
   la sauvegarde est FERMEE         0 = 0
   VOISINES : 450 dates . 2 588 avis . 195 du classeur -- tous justes
```

#### ⭐⭐⭐ ET LA LECON DU SOIR EST DEJA APPLIQUEE : LA SAUVEGARDE NAIT FERMEE

`app_affaire_avant_c8_20261116` est la **PREMIERE sauvegarde du projet a naitre
fermee** : le patch fait suivre son `create table ... as` d'un
`revoke all ... from authenticated, anon`.

⛔⛔ **POURQUOI, et c'est la mesure du 16/11 au soir** : une sauvegarde creee par
`create table ... as select` **herite du droit par defaut du schema ET NAIT SANS RLS**.
Resultat mesure : **18 sauvegardes du projet** etaient REELLEMENT ouvertes a
`authenticated`, TRUNCATE comprise -- et elles portent **les memes donnees** que les
tables protegees (31 151 etiquettes, 7 346 repartitions, 841 lignes de charge...).

```
   189 tables du schema public
   188 portent un droit pour authenticated
   ⛔  18 REELLEMENT ouvertes : droit ET pas de RLS  -> TOUTES des sauvegardes
   ⚠  15 droit + RLS sans politique : fermees en pratique
   ✅ 126 le regime normal du projet
        0 table pour anon   ⭐ l'acquis du chantier ①
```

⭐ **AUCUNE TABLE EN SERVICE N'EST OUVERTE** : les 126 tables que l'app utilise ont
bien RLS plus une politique. Ce qui est ouvert, ce sont les **photos d'avant**.
⬜ **FREDERIC, 16/11 : « Non enchaine »** -- les 18 existantes ne sont PAS fermees, par
sa decision. Le patron, lui, est change : toute nouvelle sauvegarde nait fermee.

---

### ⭐⭐⭐ LE MECANISME D'ENSEMBLE -- app, serveur, Sheet et Hektor (16/11)

Ecrit a sa demande : « explique moi le mecanisme je veux bien comprendre [...] dans le
chantier on avait deja tout vu ». **Il avait raison : tout etait deja ecrit**, aux
etapes 4 et 5. Ce bloc ne decide rien, il rassemble.

```
   AUJOURD HUI -- ON RAPATRIE, ET ON DEVINE
     le Sheet ---(le GEL : appariement par noms + dates + prix)---> notre base
     Hektor ----(le run de nuit)----------------------------------> notre base
     notre base --(la descente 07:45)----------------------------> le serveur local

   ETAPE 5.2 -- ON ECRIT NOTRE IDENTIFIANT DANS LE SHEET
     notre base --(app_dossier_uuid)-----------------------------> colonne A du Sheet
     ⭐ a partir de la, CHAQUE LIGNE DU CLASSEUR PORTE NOTRE NUMERO

   ETAPE 5.3 -- PLUS BESOIN DE DEVINER
     l app ------(par l UUID, directement)-----------------------> le Sheet
     ⛔ LE GEL NE SERT PLUS : « il sert ici, UNE FOIS -- puis il DORT »
```

⭐⭐⭐ **ET C'EST POURQUOI L'ETIQUETTE VIT SUR CHAQUE TRANSACTION, ET NON DANS UNE
TABLE PAR DOSSIER.** Son role n'est pas d'etre un point d'accrochage interne : c'est
d'etre **la clef partagee avec le Sheet**, celle qu'on ecrira dans sa colonne A et qui
remplacera l'appariement pour toujours. Un dossier d'affaire n'est pas un objet chez
nous, c'est un REGROUPEMENT ; ce qui est stable, c'est l'etiquette.

⚠ **SA QUESTION ETAIT JUSTE, ET LA REPONSE EST MESUREE** : « nous n'avons aucune base
avec une ligne par etiquette ??? » -- exact, et au 16/11 **PERSONNE** ne portait
`app_dossier_uuid` a part `app_affaire_ledger`. L'etiquette etait posee partout et
**utilisee par rien**. La table des avis est la **premiere** a s'en servir.

#### ✅⭐⭐ LE VERROU DES QUATRE TABLES -- POSE LE 16/11

Son ordre : « il faut aussi faire ce verrou », puis « Les quatre ».

⛔⛔ **JE VENAIS SIGNALER UN OUBLI, L'AUDIT EN A TROUVE TROIS AUTRES, PLUS GRAVES** :

```
   table                     RLS          politiques   authenticated
   app_classeur_lien         DESACTIVEE        0        TOUT, TRUNCATE comprise
   app_classeur_ligne_id     DESACTIVEE        0        TOUT
   app_charge_exclusion      DESACTIVEE        0        TOUT
   app_classeur_avis         active            0        TOUT
```

⭐ **LA DIFFERENCE EST CAPITALE** : sans RLS il n'y a aucun gardien, donc le droit
suffit. Les trois premieres etaient **reellement ouvertes** -- n'importe quel compte de
l'app pouvait lire, modifier ou **VIDER** le gel (12 595 liens) et le pont (4 773
identites), **le socle du chantier**. `app_classeur_avis`, elle, a RLS active sans
politique : fermee en pratique. **Mon oubli etait le MOINS grave des quatre.**

⛔⛔⛔ **ET LA FAUTE EST DEJA DANS LA MEMOIRE DU PROJET** sous le nom « `revoke all
from public` NE FERME PAS `authenticated` ». Mon patch B1 faisait
`revoke ... from public` et je l'ai cru suffisant. **Je l'ai refaite le lendemain de
l'avoir notee.**

```
   6 controles apres la pose :
     droits restants pour authenticated/anon      0 = 0
     service_role lit toujours les 4              4 = 4   <- le run ne tombe pas
     les 4 voisines du registre intactes          4 = 4
     donnees intactes : gel 12 595 . pont 4 773 . avis 2 588
```

⭐ **AUCUN RISQUE FONCTIONNEL, ET C'EST MESURE** : aucune des quatre n'est citee dans
`apps/` ni `backend/`. Seuls les scripts du chantier les lisent, par la CLE DE SERVICE.

#### ✅⭐⭐ L'ETIQUETTE SUR LA TABLE DES AVIS -- POSEE LE 16/11

Son choix, apres que je lui ai propose de tout mettre en colonnes du registre :
**« Table avec etiquettes »**.

⛔⛔ **ET L'ACCROCHAGE EST L'ETIQUETTE, JAMAIS LE NUMERO DE CHAINE** -- regle du
28/10 : *« un numero de chaine ne doit JAMAIS servir de point d'accrochage, il
bouge »*. Ce n'est pas theorique : **6 chaines ont bouge** depuis le 12/11 (journal des
etiquettes). `app_dossier_uuid`, elle, ne bouge jamais. Un avis accroche par
l'etiquette survit a une FUSION de dossiers ; par la chaine, il se perdrait en silence.

```
   avis au total                        2 588 = 2 588
   etiquettes posees                    2 560 = 2 560
   laissees vides ET COMPTEES              28 = 28   (20 a cheval + 8 sans lien)
   UUID sans numero court                   0 = 0
   etiquettes ORPHELINES                    0 = 0
   l index de jointure existe               1 = 1
   TOUJOURS fermee a authenticated          0 = 0   <- le front ne la voit pas
   ⭐ ESSAI DE JOINTURE REELLE : 7 356 lignes . 2 556 dossiers atteints
```

⭐ **L'essai de jointure est le temoin qui compte** : ce n'est pas une colonne posee en
esperant qu'elle serve, elle sert. Et la table reste **fermee au front**, exactement ce
qu'il a demande : « dans l'apps et le serveur mais pas visibles tout de suite dans le
front ».

⚠ **UN DEFAUT, REJETE AVANT LE COMMIT** : `min(uuid)` n'existe pas en PostgreSQL. Le
patch etant dans `begin/commit`, **rien n'a ete ecrit** -- verifie : 0 colonne ajoutee,
2 588 avis intacts. Corrige en `(array_agg(distinct ...))[1]`.

#### ⚠ UNE DETTE QUE L'AUDIT REVELE, NON CORRIGEE

Trois tables s'accrochent par `app_chaine_id`, donc portent le risque que la regle du
28/10 decrit : `app_affaire_note` (204), `app_affaire_condition` (5),
`app_affaire_repartition` (17 905). Rien n'a casse jusqu'ici, mais **si un dossier
fusionne, leurs liens peuvent se perdre en silence**. ⬜ A trancher a part.

#### LES DECISIONS DE FREDERIC, 16/11 AU SOIR

```
   Y   « Vente Reglee »       VISIBLE dans la vue transaction
   C   « Mandat »             NE PAS RAPATRIER DU TOUT
   AH AI AJ  les avis         en base et au serveur, PAS visibles au front,
                              dans une TABLE accrochee par l ETIQUETTE
   le verrou                  LES QUATRE tables
   AA  « Numero de facture »  ⬜ PAS ENCORE TRANCHE
```

⭐ **ET L'AUDIT QU'IL A DEMANDE SUR « REGLEE » CONFIRME SA LECTURE** : il n'y a
**qu'une seule** colonne « reglee » au classeur, `Y Vente Reglee`. `AA Numero de
facture` est une colonne DIFFERENTE, qui ne parle pas de reglement -- ma question les
presentait comme allant ensemble, ce qui etait trompeur.

---

### ✅⭐⭐ C9 PREMIERE MOITIE FAITE -- 2 588 LIGNES D'AVIS POSEES LE 16/11

#### ⭐⭐⭐ POURQUOI ELLE EST PASSEE EN PREMIER, ET CE N'EST PAS « parce qu'elle etait facile »

`app_classeur_avis` a pour clef **`id_unique` -- LA LIGNE DU CLASSEUR, PAS LA
TRANSACTION** -- et **aucune clef etrangere** vers le pont (mesure du 16/11 au soir :
une seule contrainte, `PRIMARY KEY (id_unique)`). Trois consequences :

```
   . elle NE DEPEND PAS DU GEL : un re-gel ne peut pas la deplacer
   . donc elle n a AUCUN TROU : les lignes sans lien entrent comme les autres
   . et la table etait VIERGE : aucun conflit possible
```

⭐ **LE TEMOIN QUI LE PROUVE** : **8 lignes posees n'ont AUCUN LIEN dans le gel**.
Ce sont 8 avis que C8 et C4, qui passent par une transaction, **perdront**. C'est
exactement la raison de l'ordre : *ce qui ne depend de rien passe d'abord.*

#### CE QUI EST POSE, ET LES COMPTES TOMBENT SUR A1 A L'UNITE

```
   2 588 lignes du classeur
      avis_a_envoyer     2 266   A1 annoncait 2 266
      commentaire_avis     392   392
      avis_envoye        2 405   2 405
   0 doublon d id_unique . 0 ligne sans identifiant
```

**LES VALEURS SONT BRUTES, ET C'EST LA DECISION DU PLAN** -- 120, 72 et 69 valeurs
distinctes : c'est un vocabulaire humain, pas une enumeration. Normaliser
« oui / OUI / non / NON / pas acq. » serait INTERPRETER, et une interpretation ne se
defait pas.

```
   AH  « oui » 1 830 . « non » 129 . « NON » 112 . « pas acq. » 18 . « OUI » 8
   AI  « ok » 195 . « 1 » 115 . « oui » 5 . « Claire s'en occupe » 4
   AJ  « ok » 1 700 . « X » 219 . « Marion » 192 . « Nico » 59 . « Claire » 24
```

#### ✅ LES TREIZE CONTROLES, JOUES APRES LE COLLAGE

```
   lignes posees                           2 588 = 2 588
   avis_a_envoyer / commentaire / envoye    2 266 . 392 . 2 405  ✓ tous les trois
   aucune ligne entierement vide                0 = 0
   toutes portent la marque du lot              0 = 0
   origine = classeur partout                   0 = 0
   posees SANS identite dans le pont            0 = 0 (les 18 absentes n ont pas d avis)
   posees SANS AUCUN LIEN dans le gel           8 = 8 (ce que C8 perdra)
   valeurs distinctes AH / AJ               120 . 69  ✓ A1
   VOISINES les 450 dates de C3               450 = 450
   VOISINES les 195 du classeur               195 = 195
```

#### ⛔ UN DEFAUT DE MA PROPRE REPETITION, ATTRAPE AVANT DE COLLER

Elle annoncait « **doit etre > 0** » pour les deux controles hors-pont. La mesure rend
**0** (les 18 absentes de A6 ne portent aucun avis) et **8**. ➡ **Un controle qui
attend une valeur FAUSSE est pire qu'aucun controle : il rougit pour rien, et on
apprend a ignorer ses rouges.** Corrige avec les deux chiffres mesures, et la date de
la mesure ecrite a cote.

#### ⚠ L'AUTRE MOITIE DE C9 N'EST PAS FAITE, ET C'EST VOULU

`C` (le numero de mandat) se pose dans `numero_mandat_app`, **sur une TRANSACTION** --
donc elle **depend du gel**, et les 33 numeros du classeur sont **RECYCLES a charges
divergentes** (commentaire de la colonne 53). Elle attend le re-gel. Ne pas melanger
les deux moities, ni cocher C9 en entier.

---

### ✅⭐⭐⭐ AUDIT DES GESTES RESTANTS ET L'ORDRE LOGIQUE -- 16/11 AU SOIR

Demande par Frederic : « il faut faire ces gestes mais aussi mettre d'abord a jour le
plan du chantier et faire un audit des gestes restants de maniere logique ».
**Chaque chiffre ci-dessous est mesure en base ce soir, aucun ne vient d'un souvenir.**

#### L'ETAT REEL DE CHAQUE CASE CIBLE

```
   C3   date_annulation_app          450 / 31 352   ✅ POSEE le 16/11
   C3bis motif_annulation_app          0            ⬜ sa source est F -> depend de C4
   C8   vente_reglee_app (Y)           0            ⬜ 3 756 au classeur, DONT 794 NON-DATES
   C8   numero_facture_app (AA)        0            ⬜ 3 741 au classeur
   C9   app_classeur_avis (AH AI AJ)   0            ⬜ table VIERGE, creee par B1
   C9   numero_mandat_app (C)          0            ⬜ 33 recycles au classeur
   C4   app_affaire_condition (F)      5            ⬜ 3 099 cellules MIXTES au classeur
   C4   app_affaire_note (G)         204            ⬜ 4 131 commentaires au classeur
   C1   app_mandat_champ_app         853 origine 'classeur'  ✅ POSEE le 14/11, confirmee
   C5   transaction_origine          195            ✅ POSEES le 16/11
   D1   app_classeur_lien         12 595            (le gel ; A13 disait 12 413, +182 au re-gel)
   A6   app_classeur_ligne_id      4 773 / 4 791 au Sheet -> **18 ABSENTES**
```

⚠ **UN FAUX ECART QUE J'AI FABRIQUE PUIS CORRIGE DANS LA MINUTE** : j'ai d'abord mesure
C1 sur `charge_commission_app` (7 lignes) et failli crier a l'ecart avec les 16 du plan.
**La charge ne vit pas la** : elle est dans `app_mandat_champ_app`, 853 lignes
`origine = 'classeur'` -- exactement ce que le plan dit. **Mesurer la mauvaise colonne
fabrique une alerte, pas une mesure.**

#### ⛔⛔ LA TROUVAILLE DE CET AUDIT, ET ELLE DECIDE D'UN ORDRE

`app_affaire_note` porte **195 lignes `origine = 'classeur'`** : ce sont les notes
d'acquereur posees avec les 195 transactions, le 16/11. Et **C4 doit y poser les 4 131
commentaires de G avec la MEME valeur d'origine.**

➡ **Sans origine distincte, les deux lots deviennent indiscernables** -- et un retour
arriere sur l'un emporterait l'autre. C'etait une reserve declaree hier « distinguables
par leur texte, mais fragile » ; elle est maintenant **chiffree**.
⭐ **LE PREALABLE DE C4** : poser les commentaires de G sous une origine propre
(`classeur:G`), ou marquer les 195 avant. **A trancher AVANT C4, jamais apres.**

#### ⭐⭐⭐ L'ORDRE LOGIQUE, ET SON CRITERE

Le critere n'est pas « du plus facile au plus dur ». C'est : **ce qui dit ce que les
autres ne verront pas passe d'abord ; ce qui a un prealable non tranche passe en
dernier.**

```
①  A6   LES 18 LIGNES ABSENTES ET LES 85 NON RATTACHEES
       Lecture seule, gratuit. ⭐⭐ ET C'EST LUI QUI DOIT OUVRIR : il dit ce que
       C8 et C9 NE VERRONT PAS. Rapatrier d'abord, puis decouvrir que 18 lignes
       du Sheet n'ont jamais eu de place chez nous, c'est rapatrier avec un trou
       et ne le savoir qu'apres.

②  C9   AH AI AJ -> app_classeur_avis, et C -> numero_mandat_app
       Table VIERGE (0 ligne), colonnes vierges, valeurs BRUTES, aucun piege de
       format connu. Le meme patron que C3, qui vient de marcher.
       ⚠ les 33 numeros de mandat du classeur sont RECYCLES a charges divergentes
         (commentaire de la colonne 53) -> ne pas les traiter en bloc.

③  C8   Y ET AA -- les deux plus gros postes
       ⛔⛔ LE PIEGE EST CONNU ET MESURE : Y porte 794 NON-DATES sur 3 756 (21 %),
         du genre « 29 decembre23 ». C'est exactement ce qui a fait perdre 924
         lignes EN SILENCE le 14/11. `date_du_classeur_tolerante` est OBLIGATOIRE,
         et la colonne est en TEXT pour cette raison precise (decision de A1).

④  A5   967 lignes sans role vente, dont 311 sans vente NI compromis
       Lecture seule. Elle eclaire ce qui reste vraiment hors de portee.

⑤  C4   F ET G -- mais SON PREALABLE D'ABORD (l'origine distincte, ci-dessus),
       et sa decision sur F (« en bloc » emporterait 1 536 « V » et 753 pastilles).
       ➡ C3bis (les motifs) EN DEPEND : elle ne peut pas passer avant.

⑥  B2 B3  LES DEUX SENTINELLES -- apres A6 et C4, parce qu'une sentinelle qui
       surveille un perimetre encore mouvant crie pour rien.

⑦  SES DECISIONS, aucune prise : C2 (303 commissions) · C6 (26 ventes en conflit)
       · C7 (2 303 ecarts « Vente Prevue », decidee « tout », on ecrase) · C10 (AF
       prix : on LISTE, on n'ecrit rien) · le reste de C5 (10 anciennes + 24
       compromis « en attente » + 33 ventes « Vente fixee », arrets volontaires).

⑧  LES DEVELOPPEMENTS : la SAISIE DE LA DATE A L'ANNULATION (nee de C3 ce soir,
       demandee par lui) · D2 (la porte sans ecran) · D1 (le re-gel additif, 6 lignes).

⑨  SON GESTE : D3 / 5.1 -- lire les Apps Script du classeur (verrou V1), 10 min.
       Et les 14 lignes a verifier a la main dans Hektor
       (notice/A_VERIFIER_DANS_HEKTOR_2026-11-16.csv, les 3 plus anciennes d'abord).
```

#### ⚠ LES DEUX DEFAUTS DU PLAN QUE CET AUDIT A CORRIGES

```
1  DEUX lignes C3 cohabitaient : la mienne, cochee, et l'ancienne restee ⬜.
   ⭐ Et ce n'etait pas qu'un doublon : l'ancienne portait LES MOTIFS, que C3
     n'a PAS faits. Elle devient C3bis, et elle reste ouverte.
2  A6 annonçait 17 absentes ; elles sont 18 (4 773 contre 4 791). Le Sheet a
   gagne une ligne dans la journee -- d'ou la regle : un ecart avec le Sheet se
   REMESURE le jour ou on l'utilise, il ne se recopie pas.
```

---

### ✅⭐⭐⭐ C3 EST FAIT -- 450 DATES D'ANNULATION POSEES LE 16/11

**LA REGLE, DE FREDERIC** : « La date d'annulation dans le Sheet represente la date
d'annulation du **COMPROMIS**. » Perimetre arrete par lui le meme jour : **450**.
Patch colle par moi, avec son accord explicite (« colle toi meme », « tu as mon accord »),
via `node Console/apply_sql_patch.js` -- le pooler, l'hote direct n'ayant plus d'IPv4.

#### ⭐⭐⭐ SA REGLE A FAIT DISPARAITRE TOUTE L'AMBIGUITE, ET C'EST LA PREUVE QU'ELLE EST JUSTE

Mon tri d'avant acceptait « toute transaction morte » -- compromis annule OU offre
refusee. Il rendait **446 lignes a plusieurs cibles**, que j'allais lui demander de
trancher une par une. Avec sa regle :

```
   AVANT (ma regle a moi)        APRES (la sienne)
   252 nettes                    450 nettes
   446 A TRANCHER                  0        ⭐ toutes resolues
```

**Une regle juste supprime les cas douteux ; elle ne les deplace pas.**

⭐⭐ **ET L'AUDIT LUI A DONNE UNE SECONDE RAISON, QUE JE N'AVAIS PAS VUE** : pour une
offre refusee, `date` porte **DEJA** la date du refus (regle du 12/11) ; pour une vente,
il n'y a pas d'annulation (0 des 9 281 ventes n'a d'etat : une vente DISPARAIT). **Le
compromis est le SEUL cas ou `date` porte la signature et ou la date d'annulation n'a
nulle part ou aller.** Une colonne, un geste, aucun doublon.

#### LE TRI DES 896, ET LA PARTITION BOUCLE

```
   ✅ 450  un seul compromis annule, date coherente  -> POSEES
       107  date anterieure au compromis               -> laissees
       272  aucun compromis, seulement une offre       -> hors de sa regle
        63  aucun lien dans le gel
         4  un compromis, mais `active`
         0  plusieurs compromis annules . 0 deja datee . 0 date future
   partition  896 = 896
   par annee  2020 68 . 2021 81 . 2022 66 . 2023 78 . 2024 62 . 2025 73 . 2026 22
```

#### ✅ LES DOUZE CONTROLES, JOUES SANS LA LISTE DU PATCH

Volontairement independants : des controles qui reprennent la liste du patch ne font
que repeter ce que le patch croit.

```
   dates d annulation posees                   450 = 450
   toutes sur un COMPROMIS (hors-type)           0 = 0
   toutes sur un compromis ANNULE                0 = 0
   aucune mal formee ni future                   0 = 0
   aucune ANTERIEURE a la date du compromis      0 = 0
   annees distinctes couvertes                     7 = 7
   la sauvegarde datee                         450 = 450
   VOISINES transactions au total           31 352 = 31 352
   VOISINES compromis annules                1 425 = 1 425
   VOISINES aucun motif pose par erreur          0 = 0
   VOISINES les 195 du classeur intactes       195 = 195
   VOISINES etiquettes toujours 1 pour 1      true = true
```

#### ⛔⛔ CE QUE L'AUDIT A TROUVE SUR LES 107, ET CE N'EST PAS NOUS

J'ai d'abord cru que notre date etait fausse (le geste de masse du 11/11). **Mesure :
non.** Nos deux dates de compromis sont IDENTIQUES dans **82 cas sur 86**.

```
   83  le classeur est INCOHERENT AVEC LUI-MEME (annulation < son propre compromis)
         dont 77 ou l annulation tombe ENTRE son offre et son compromis
   21  le classeur n a PAS de date de compromis
    3  le classeur est coherent, c est NOTRE date qui diverge
```

⭐ L'explication la plus probable, **non tranchee** : la colonne « Compromis » du
classeur porterait une date **PREVUE** (le rendez-vous), l'affaire etant morte avant.
⛔ C'est du metier : **je ne le tranche pas**. Les 21 ont ete proposees en plus (471) et
Frederic a repondu **450**.

#### ⛔⛔ LA RESERVE QUE C3 REVELE, ET ELLE EST IMPORTANTE

**L'APP NE DEMANDE AUCUNE DATE QUAND ON ANNULE.** Mesure de bout en bout :

```
   l ecran     gesteAffaireOptimistic(app_affaire_id, 'annuler')     3 parametres
   la RPC      app_geste_affaire_optimistic(target_affaire_id, geste, job_priority)
   son corps   ecrit date_annulation_app  ⛔ NON . motif_annulation_app ⛔ NON
```

➡ **L'historique est juste, le PRESENT est muet** : des la premiere annulation faite
dans l'app, la colonne commence a vieillir. Frederic, 16/11 : « il faut pour etre
logique ajouter une date lors de l'annulation d'une transaction dans l'apps dans le
front etc... mais pas dans hektor ».

⭐ **ET CE SERA SIMPLE, PARCE QUE LA BASE EST PRETE** -- trois pieces :

```
   1  la base   la RPC gagne DEUX parametres a defaut NULL (date, motif) : additif,
                les appels existants continuent ; elle les ecrit dans le MEME UPDATE
                que l etat, et NE LES MET PAS dans la charge du travail
   2  l appel   gesteAffaireOptimistic gagne deux arguments optionnels
   3  l ecran   le champ sur la seule branche « annuler le compromis »
```

⚠ **RIEN NE PARTIRA CHEZ HEKTOR, PAR CONSTRUCTION** : la charge du travail ne porte
que `hektor_annonce_id`, `numero_dossier`, `titre_bien`, `app_affaire_id`, `etat_avant`,
`geste` et l'id Hektor -- **aucune date** (lu dans la RPC). Et la colonne est dans
`COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` depuis le 10/11.

⛔⛔ **LA SEULE VRAIE DIFFICULTE N'EST PAS TECHNIQUE** : la modale a ete **REFONDUE** --
`ModaleStatutV2.tsx` est EN PRODUCTION depuis le 06/11 derriere
`VITE_APP_STATUT_V2_ENABLED`. Il y a donc **DEUX blocs** et un outil de parite a 35/35
(`apps/hektor-v1/test_statut_v2_empreintes.cjs`). Ajouter un champ = le mettre dans le
bon composant (ou les deux, ou declarer l'ecart) et relancer l'outil AVANT et APRES.
Plus l'index git partage avec l'autre session sur `App.tsx`.

#### ⭐ L'AUDIT DE LA CASCADE, DEMANDE PAR FREDERIC

Sa question : « dans mon projet la date d'annulation du dossier est liee a l'annulation
d'une transaction, donc audite le fait que les 3 transactions vont etre annulees plus
tard ». Mesure :

```
   cascade_annulation_compromis = 'on'  (app_setting), dans app_geste_affaire_optimistic
   -> declenchee par L ECRAN seulement ; AUCUN declencheur de cascade sur la table,
      donc UN PATCH SQL NE LA REVEILLE PAS
   elle passe l offre `accepted` de la chaine a `refused` + un travail chez Hektor
   ⛔ ELLE N ECRIT AUCUNE DATE D ANNULATION

   1 373 chaines portent un compromis annule
   dont 1 125 portent AUSSI une offre refusee (82 %)
   dont   349 une offre encore ACCEPTEE -> la cascade les refusera plus tard
   dont   362 une VENTE -> la cascade ne touche pas ces chaines
   TOTAL 1 145 offres refusees dans ces chaines, toutes sans date
```

✅ **Frederic a tranche : « ce n'est pas un probleme »** -- la date reste celle du
compromis, et les offres refusees n'en ont pas besoin (leur `date` EST leur refus).

#### ⚠ LES DEUX DEFAUTS DE MES PROPRES SCRIPTS, ATTRAPES AVANT DE POSER

```
1  `lire_classeur` rend un TUPLE (entetes, lignes), chaque ligne etant un COUPLE
   (rang, cellules) -- PAS une grille. Ma 1re version a lu « 1 ligne de corps »,
   rendu DES ZEROS PARTOUT et SORTI EN CODE 0.
   ➡ deux gardes posees : un PLANCHER de lignes lues (3 000) et un TEMOIN POSITIF
     sur Z (700 minimum, A1 en comptait 896). Une lecture ratee n'est jamais un vert.
2  `dates_des_propositions` rend du **jj/mm/aaaa** : `sorted()` sur ces chaines NE
   TRIE PAS dans le temps. On convertit d'abord, puis on prend le minimum.
```

#### ⏰ A JUGER DEMAIN MATIN, EN PLUS DES CINQ POINTS DES 195

```
   les 450 dates doivent etre EN LOCAL apres la descente
     -> `date_annulation_app` est bien dans la liste des colonnes que le local
        CREE et RECOIT a la redescente (affaire_ledger.py l. 637), donc la
        sauvegarde de nuit l emportera
   et toujours 450 chez Supabase (le push ne l envoie pas : l. 3124)
```

Fichiers : `supabase/patch_c3_dates_annulation_2026-11-16.sql` (+ `_INVERSE`,
`_REPETITION`) · mesures `phase2/checks/c3_mesurer_les_dates_annulation_2026-11-16.py`,
`c3_pourquoi_107_anterieures_2026-11-16.py`, `c3_generer_patch_dates_annulation_2026-11-16.py`
· rapports `notice/C3_OU_SE_POSENT_LES_DATES_ANNULATION_2026-11-16.csv` et
`notice/C3_LES_107_ANTERIEURES_2026-11-16.csv`.

---

### ✅⭐⭐⭐ AUDIT DE L'ID UNIQUE DU REGISTRE -- 16/11, DEMANDE PAR FREDERIC

**SA QUESTION, EN DEUX TEMPS** : d'abord « le registre des affaires va se trier par
id affaires uniquement au gel, tu es sur ? », puis -- apres une premiere reponse
incomplete de ma part -- « il y a quelque chose qui cloche, nous avons ajoute meme je
crois DEUX COLONNES dans le registre des transactions chez nous pour mettre un ID
Unique. Retrouve ce chantier, ce n'est pas juste un gel. AUDIT ».

⛔⛔ **IL AVAIT RAISON, ET MON BALAYAGE ETAIT FAUTIF** : j'avais cherche les colonnes
par QUATRE MOTIFS QUE J'AVAIS CHOISIS (classeur, chaine, origine, payload) -- une
colonne nommee `app_dossier_uuid` ne pouvait pas en sortir. C'est, le meme jour, la
troisieme fois que la lecon mord : **une famille ne se balaie pas par un critere qu'on
choisit ; on liste TOUT, puis on trie.**

#### LES DEUX COLONNES EXISTENT, ET C'EST L'ETIQUETTE DE DOSSIER (posee le 09/11)

```
   48  app_dossier_uuid     uuid   l etiquette LONGUE
   49  app_dossier_numero   text   l etiquette COURTE (forme D2026-0431)
```

⭐⭐⭐ **ET LE COMMENTAIRE DE LA 48 PORTE TOUT LE SUJET** : « posee par Supabase
seulement, jamais par le push ni par le clic. Toutes les transactions d'un meme
dossier la partagent. **C'est elle qui va dans la colonne `affair_uuid` du
classeur.** Elle ne bouge JAMAIS une fois posee. »

#### ELLE EST POSEE PARTOUT, ET L'UNICITE EST PARFAITE

```
   transactions au total                      31 352
   avec etiquette (uuid ET numero)            31 352     <- toutes
   sans etiquette                                  0
   LES 195 DU CLASSEUR : avec etiquette       195 / 195
   LES 195 : sans                                  0

   chaines distinctes                         11 444
   etiquettes distinctes                      11 444     ⭐ UN POUR UN, EXACTEMENT
   chaines portant PLUSIEURS etiquettes            0
   etiquettes couvrant PLUSIEURS chaines           0
   numero court en double sur deux dossiers        0
```

⚠ **ET UNE ERREUR DE CLE QUE J'AI FAITE, PUIS CORRIGEE DANS LA MINUTE** : groupe par
`app_dossier_id` (= L'ANNONCE), le controle rendait **607 dossiers a plusieurs
etiquettes** et j'ai failli crier. La bonne cle est `app_chaine_id` (le dossier
d'affaire) : les 607 sont des BIENS a deux acquereurs successifs, donc deux dossiers
d'affaire, donc deux etiquettes -- **le dessein, pas un defaut**. Temoin : annonce
54771, 5 transactions, 2 chaines, 2 etiquettes.

#### ⭐ LES 195 N'ONT CREE AUCUNE ETIQUETTE NEUVE -- ELLES ONT HERITE

195 sur 195 portent **exactement** l'etiquette de leurs voisines du meme dossier ;
0 divergente ; 0 dossier ou elles seraient seules. Et ce n'est pas le run qui l'a
posee : **c'est le patch**, qui recopie l'etiquette du dossier (lignes 235-247 et 444
de `poser_offres_annulees_classeur_2026-11-16.py`). Verifie dans le script, pas
suppose. Trois temoins :

```
   1001425  annonce 54771  offre refused  08/05/2025  D2025-0432  classeur S13Z3PIN
   1001426  annonce 41672  offre refused  25/04/2025  D2025-0169  classeur 1P6VET6U
   1001427  annonce 42981  offre refused  30/04/2025  D2025-0186  classeur 7Q6O044E
```

#### ✅ LE MECANISME EST BRANCHE AU RUN -- ET LA MEMOIRE DISAIT LE CONTRAIRE

```
   .env ligne 213                APP_ETIQUETTE_DOSSIER=1
   affaire_ledger.py l. 2709     rpc/app_poser_etiquettes_dossier
   affaire_ledger.py l. 1216     « APP_ETIQUETTE_DOSSIER=1 le run appelle ... »
```

⛔ La fiche memoire `etiquette-dossier-posee-mais-pas-branchee` etait **PERIMEE**,
chiffre compris (31 151 contre 31 352). Corrigee le 16/11.

#### ⛔⛔ LA REPONSE A SA QUESTION : OUI, LE GEL EST LE SEUL PONT -- ET C'EST SA DECISION

La place existe dans le classeur : **colonne A, `affair_uuid`, vide sur 4 778 lignes**
(une seule cellule remplie, un « E » ligne 77), et A4bis l'appelle « une place qui
nous attend ». Mais :

```
A  | affair_uuid | ON NE TOUCHE PAS. Laissee vide volontairement.
   | decide le 05/11/2026 par Frederic : « Pour l'instant on la laisse vide
   |   c'est a l'etape B pour l'instant on ecrit rien dans le classeur »
   | motif : le pont existe deja par « ID Unique » ;
   |   UN SECOND PONT SERAIT UNE OCCASION DE DIVERGENCE
   | ⛔ NE PAS la remplir « parce qu'elle est vide »
```

Et **D2** recommandait : « oui, mais APRES V1, et en phase B. Le lien vit d'abord
CHEZ NOUS. » → **ce n'est donc pas un trou, c'est un choix date**, et le second pont
est pret des deux cotes mais deliberement debranche.

⚠ **UN CHIFFRE A RECONCILIER** : A13 parlait de **12 413** liens geles, la base en
compte **12 595** (+182). C'est l'effet du re-gel additif du 13/11, pas une anomalie.

#### ⚠ CE QUE SA QUESTION A FAIT DECOUVRIR : `payload_json` N'EST PAS PROTEGEE

`transaction_origine` figure dans `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` ;
**`payload_json` NON** -- et c'est elle qui porte `classeur_id_unique`, la marque des
195. J'ai suivi la chaine entiere plutot que de supposer :

```
   la descente refait la doublure __sb par un select=*   -> la marque DESCEND
   26bis copie LES COLONNES COMMUNES                     -> payload_json TEXT existe
                                                            en local (l. 263) : elle ENTRE
   le push renvoie payload_json depuis le local          -> IDENTIQUE, rien n est perdu
```

⭐ **ELLE SURVIT** -- mais parce que la colonne existe des deux cotes, **pas** parce
qu'une garde la protege. ➡ d'ou le **6e point a juger demain matin**, gratuit :
*les 195 portent-elles toujours leur `classeur_id_unique` apres la nuit ?*

#### ⛔ ET UNE TROUVAILLE QUI N'EST PAS DE CE CHANTIER -- RANGEE AILLEURS

En balayant les lecteurs de C3 j'ai trouve un desaccord entre `assistant.ts`
(`transactionPourLien`, lot 3b du 16/11) et le registre sur l'annee d'une chaine :
**1 814 chaines sur 11 383 (15,9 %)**, dont 608 par `date_acte` et 1 206 par le jour
vrai de l'offre (partition propre). **FREDERIC, 16/11 : « cela n'a rien a voir c'est
un autre chantier. »** ➡ ecrit dans `notice/PROJET_ASSISTANT_IA_RESERVES.md`,
**non traite ici**, deux decisions en attente.

---

### ✅⭐⭐⭐ L'ETAT DU CHANTIER AU 16/11/2026 AU SOIR -- TOUT EST MESURE

**Demande de Frederic** : « beaucoup de choses ont ete faites ou notees sans mettre a
jour ce plan -- il faut un travail minutieux ». ⛔ **Aucun chiffre de cette section ne
vient d'un souvenir** : tout a ete mesure en base ou lu dans le code le 16/11 au soir.

#### ① CE QUI EST POSE EN BASE, MESURE

```
   C1  la charge, origine 'classeur'                853 lignes   (dont les 16 du 14/11)
   C5  transactions reprises du classeur            195 lignes
         C5 lot B -- offres annulees                  96
         C5 lot B -- compromis annules                35
         C5 lot B -- offres vente reglee              64
   leurs notes (app_affaire_note, origine classeur) 195
   parties creees par ces 195                         0   ⭐ la decision « l acquereur
                                                           va en note » tient
   B1  les colonnes neuves                          3 + une table de 7 colonnes
         vente_reglee_app . numero_facture_app . numero_mandat_app  (toutes TEXT)
         app_classeur_avis (cle id_unique, RLS active, aucun droit public)
   C2 C3 C4 C8 C9  posees                             0   (rien, et c'est exact)
   D1  liens du gel                              12 595   INCHANGES
```

#### ② LES SEPT GARDES DE LA FAMILLE `transaction_origine` -- TOUTES VERIFIEES

Le chantier a trouve **sept** lecteurs qui reagissent a « cette transaction n'est pas
chez Hektor ». Etat mesure le 16/11 au soir, un par un :

```
   1  vue app_affaires_sans_numero_hektor        GARDE   (crie)
   2  sentinelle data.transaction_disparue       GARDE   (crie)
   3  filet du worker poserNumerosManquants      GARDE   (ecrirait un numero FAUX)
   4  l ecran                                    SANS OBJET : il exige un numero
   5  filet du cockpit export_app_payload.py     GARDE   (affichait « plus dans Hektor »)
   6  enqueue_refus_offres_mortes_lot.js         GARDE   ⛔ IL ECRIT CHEZ HEKTOR
   7  fonction app_statut_redescente_calcule     GARDE   ⛔ ELLE REDESCEND UN STATUT
```

⭐⭐ **ET LA LECON EST PAYEE DEUX FOIS** : le 6e a ete manque le matin parce que le
balayage cherchait `present_in_hektor`, alors qu'il se declenche sur l'ETAT d'une autre
transaction ; le 7e a ete trouve en balayant avec le critere « compromis ». **Chaque
famille demande son propre balayage, et il se fait AVANT de generer le patch.**

#### ③ ⭐⭐⭐ LA REGLE DU CHANTIER, VALIDEE PAR FREDERIC LE 16/11

> **« On ne reprend que ce que Hektor ne rendra plus : le bien est SORTI du parc vivant,
> OU la date a plus d'un an. Et JAMAIS une date dans le futur. »**

Elle est nee de l'arret des 24 compromis « en attente » : bien **Actif**, offre acceptee
d'aout-septembre venue de Hektor, et un compromis annonce du 13/11 au 10/12 -- dont des
dates **dans le futur**. Le classeur servait la de carnet de rendez-vous, pas d'archive.

⭐ **ET LE CROISEMENT QUI LA JUSTIFIE EST SANS AMBIGUITE** (139 lignes restantes) :

```
   statut du bien   futur  <3 mois  3-12 m  1-3 ans  >3 ans   TOTAL
   Actif               38        9       0        0       0      47
   Echu                 6        3       0        0       0       9
   Clos                 1        1       1        0       0       3
   Vendu                1        1       7       33      36      78
```

**Aucun bien « Actif » ne porte une date de plus de trois mois.** Les deux populations
ne se melangent pas : « Vendu » = l'historique, « Actif » = le present.

#### ④ LES ECARTS QUE L AUDIT A TROUVES ENTRE LE PLAN ET LA BASE

```
   A5   le plan annonce 1 062 lignes sans role 'vente'   ->   MESURE : 967
   A6   le plan annonce 85 lignes non rattachees         ->   MESURE : 85  ✅
        (le rapport du gel en compte 87 -- ecart de 2, non explique)
   ⛔⛔ ET UNE TROUVAILLE QUI N ETAIT NULLE PART : le Sheet porte 4 790 lignes
      (A1 du 16/11) et notre table app_classeur_ligne_id en porte 4 773.
      -> 17 LIGNES DU CLASSEUR SONT ABSENTES DE NOTRE BASE, en plus des
         85 non rattachees. A6 porte donc sur 102 lignes, pas 85.
```

#### ⑤ ⚠ DEUX RESERVES NEUVES, A NE PAS PERDRE

**a) LES 195 NOTES ET C4 VONT SE MELANGER.** Les notes d'acquereur posees par C5
utilisent `origine = 'classeur'` -- **exactement ce que C4 prevoit** pour les 4 131
commentaires de la colonne G. Elles sont aujourd'hui distinguables par leur texte
(« Acquereur au classeur : ... », 195 sur 195 verifie), mais c'est **fragile**.
⏰ Avant C4 : decider comment on les separe (un champ, ou une origine distincte).

**b) LES 5 VENTES DU RESTE N ONT PAS ETE MESUREES « UNE PAR UNE ».** A4 a trouve DEUX
chemins vers « Vendu » : le statut redescendu (garde posee) **et l'ecran**
(`App.tsx:8321`, `vente_id`) -- que la garde NE couvre PAS. J'ai affirme que les 5 biens
sont deja affiches « Vendu » donc sans effet : **c'est probable, ce n'est pas mesure**.
⛔ A4 disait « une par une ». A faire avant de poser une seule vente.

#### ⑥ CE QUI RESTE, AVEC SON ETAT REEL

```
   PRET, ET SANS RISQUE CONNU
      C3   896 dates d annulation  -- Z est propre (896 dates sur 896, A1)
      10 lignes anciennes du lot B -- 2018 a mars 2026, biens Vendu/Clos
           5 ventes (⚠ reserve b) . 4 compromis . 1 offre
   DEBLOQUE MAIS A CONSTRUIRE
      C8   Y et AA  -- B1 est posee. ⚠ la tolerance des DEUX FORMATS est
           OBLIGATOIRE : 794 textes sur 3 756 (21 %), le defaut du 14/11
      C9   AH AI AJ -- la table existe. ⚠ valeurs BRUTES, AH a 120 formes
   A MESURER D ABORD
      A5   967 lignes sans role vente, dont 311 sans vente NI compromis
           -> prealable de C8 : ou va la valeur quand la transaction manque ?
      A6   85 non rattachees + 17 absentes = 102 lignes au contenu inconnu
           -> jusqu'a ~250 transactions HORS de tous les chiffres du chantier
   SA DECISION
      C6   26 ventes en conflit de date d acte
      C7   2 303 ecarts « Vente Prevue » -- il avait dit « tout », a confirmer
      C4   F : « en bloc » emporterait 1 536 « V » et 753 pastilles
      C10  AF Prix : on liste, on n ecrit rien
      D3   5.1 EST SON GESTE : lire les Apps Script, 10 minutes
   SON GESTE DANS HEKTOR
      14 lignes a verifier a la main -- notice/A_VERIFIER_DANS_HEKTOR_2026-11-16.csv
         (13 dont la date est PASSEE, + la vente du 05/11 des 11 anciennes)
         ⭐ les 46 autres n ont RIEN a verifier : leur date est dans le futur
   LAISSE VOLONTAIREMENT
      59 lignes  -- affaires EN COURS, Hektor les rendra tout seul
```

#### ⑦ CE QUI N A PAS ETE JUGE : LA NUIT DES 195

⛔ **Les 195 transactions n'ont pas encore vecu un seul run.** Le critere du matin :

```
   le compte rendu du run, cle `recopie_app_seule` :  recopiees 195
   le retour arriere joue a blanc :
      a retirer 195 . plage AVEC numero 340 . hors plage 30 817
   le moniteur : data.transaction_disparue 0 . data.affaire_sans_numero_hektor 0
   GTI Descente en code 0
   ⭐ ET LE CHAINAGE : 0 statut deplace (mesure ce soir, a reverifier au matin)
```

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
 4bis LA GARDE DE       ✅✅ POSEE ET EPROUVEE le 16/11 -- 22/22 + preuve en reel
     L ORIGINE           DEUX lecteurs n'avaient pas la garde, pas un :
                           A check_gti_health.py  data.transaction_disparue
                           B export_app_payload.py LE COCKPIT -- plus grave : il
                             AFFICHAIT « plus dans Hektor depuis ... », une phrase
                             FAUSSE montree a l'utilisateur
                         les 4 autres lecteurs de la famille etaient DEJA proteges
                         ⭐ PostgREST accepte le filtre, et un TEMOIN POSITIF prouve
                           qu'il mord (`not.is.null` -> 0)
                         ⛔ ET SA QUESTION A CORRIGE LE CRITERE : je tolerais la
                           chaine vide, donc j'etais PLUS PERMISSIF que le worker
                           (et j'avais note l'inverse). `is.null` seul partout :
                           LES TROIS PORTES SONT ALIGNEES, plus de divergence.
                         ⭐ rien a redemarrer, 3 rouges voisins PREEXISTANTS mesures
 5  retirer l essai A2  ✅✅✅ FAIT LE 16/11 a 08:57-08:58, LES DEUX COTES
                        local : 1 retiree, voisines intactes, sauvegarde datee
                        Supabase : 0 marquee, 341->340, 31 158->31 157, les 2
                          transactions d origine du dossier INTACTES
                        ⭐ LES DEUX SENTINELLES VOIENT 0
                        ⭐ l'audit des notes a sauve le geste : l'ordre reposait
                          sur un argument mort depuis l'allumage de 26bis
                        ⚠ la doublure garde la ligne jusqu'a la descente de
                          demain -- NE PAS lancer affaire_ledger.py a la main
 6  LES 241             marquees `classeur` DES L'INSERT, jamais apres
```







### PHASE B — LES EMPLACEMENTS ET LES GARDIENS

```
B1 ✅  POSEE LE 16/11 -- migration b1_colonnes_classeur_2026_11_16, 11 controles
       justes. vente_reglee_app . numero_facture_app . numero_mandat_app (TEXT)
       + app_classeur_avis (7 colonnes, cle id_unique, RLS active, 0 droit public).
       ⭐ Y EST EN **TEXT** ET C EST UNE DECISION DE A1 : 794 non-dates sur 3 756
         (21 %) -- une colonne `date` les perdrait a l'insertion, en silence.
       ⭐ numero_mandat (classe C) et transaction_origine INTACTS, registre non touche.
       ➡ C8 ET C9 SONT DEBLOQUEES.
       Fichiers : supabase/patch_b1_colonnes_classeur_2026-11-16.sql (+ INVERSE,
       + REPETITION). ⛔ L'INVERSE REFUSE DE SE JOUER si une valeur a ete posee.
       L ENONCE D ORIGINE : CREER LES 6 COLONNES MANQUANTES (9 = 3 qui existent + 6) :
         Y Vente Reglee . AA N0 de facture      -> colonnes de CLASSE A
         AH Avis a envoyer . AI Commentaire Avis . AJ Avis envoye -> table a part,
            cle id_unique (aucune colonne « avis » n'existe dans TOUTE la base)
         C numero_mandat_app -> ⛔ PREALABLE DU 29/10 JAMAIS FAIT. `numero_mandat`
            est de CLASSE C : une ecriture y est EFFACEE au run suivant.
       ⭐ Les carnets n'ont AUCUNE contrainte CHECK sur le nom d'un champ.
B2 ✅  POSEE LE 17/11 -- vue `app_v_classeur_ligne_sans_lien` + la sentinelle
       `data.classeur_ligne_sans_lien`. **85 lignes sur 4 773** n'ont AUCUN lien :
       ni date, ni motif, ni note ne les atteindra jamais.
       ⚠ LE SEUIL EST 85, PAS 0, ET C'EST DELIBERE : un seuil 0 crierait des le
         premier passage pour un fait CONNU -- le defaut reproche le matin meme a
         `data.negociateur_registre_signal`. Ce qu'on veut voir est une HAUSSE.
       ⏰ ET LE SEUIL DOIT BAISSER apres le re-gel (D1), qui va en rattacher une
         partie -- sinon la sentinelle tolere un trou qui s'est referme.
       WARNING et non critical : c'est un ETAT ancien, pas un evenement.
B3 ✅  POSEE LE 17/11 -- vue `app_v_affaire_note_condition_orpheline` + la
       sentinelle `data.affaire_note_condition_orpheline`, **CRITICAL, seuil 0**.
       UNE SEULE vue pour les deux objets (colonne `objet`) : deux vues jumelles,
       c'est deux endroits a corriger le jour ou la regle change.
       ⭐⭐⭐ ET LA MESURE A CORRIGE CE QUE J'ALLAIS ECRIRE. Les 11 orphelines ne
         sont pas des donnees metier perdues : ce sont des **restes d'essais du
         23/10**, tous sur le dossier 1068399, tous `origine = 'saisie'`. Leurs
         textes le disent : « Essai 3 du 23/10 ... (a nettoyer) » -- et l'une porte
         **« a garder pour la preuve »**.
       ⛔ JE NE LES AI DONC PAS SUPPRIMEES : l'une demande expressement d'etre
         gardee, et nettoyer un essai est une decision de Frederic. On les
         **DECLARE** (colonne `deja_declaree`, liste figee des 6 transactions) et la
         sentinelle ne compte que les orphelines NEUVES -- donc seuil 0 VRAI des le
         premier jour. « Exclure est une decision, et elle se declare. »
       ⛔⛔ LE TEMOIN POSITIF, et il etait indispensable : un 0 pouvait venir d'un
         filtre mal interprete par PostgREST. Filtre RETOURNE (`is.true`) -> la
         sentinelle rend **11, en CRITICAL, et elle NOMME chaque ligne**. Le filtre
         mord donc dans les deux sens. Source restauree a l'identique apres l'essai.
       ✅ 9 CONTROLES JUSTES : 85 . 11 . 0 non declarees . 11 declarees . 6 notes +
         5 conditions . les 11 sur le dossier 1068399 . anon ne lit rien .
         repartitions orphelines 0 . et LES 80 NOTES + 28 CONDITIONS DU 17/11 INTACTES.
       ⛔ AUCUNE DONNEE ECRITE : deux vues, deux lignes de code, rien d'autre.
       Fichiers : supabase/patch_b2_b3_sentinelles_2026-11-17.sql (+ INVERSE,
       + REPETITION) . monitoring/check_gti_health.py
```

### PHASE C — POSER, DU PLUS SUR AU PLUS DELICAT

```
C1 ✅  3.2bis LA CHARGE -- POSEE. Mesure en base le 16/11 : les 16 lignes sont
       ECRITES, le 14/11 a 06:42, avec les `ecrit_par` exacts du patch
       (classeur:c67ccc6a ...). La table porte 853 lignes origine 'classeur'.
       ⛔⛔ ET LE PLAN LA DISAIT « non jouee » PENDANT DEUX JOURS -- c'est la cause
         de la confusion du 16/11 : on ne savait plus ce qui etait fait.
       ⏰ RESTE LE LOT 2 : 25 lignes de confiance « a valider »/« bonne »
         -> SA DECISION (je ne les poserais pas).
C2 ✅ FAIT LE 17/11 -- **62 commissions posees**, 442 017 EUR, dans
       honoraires_entree_app (CLASSE A). 10 controles justes.
       ⭐⭐⭐ L AUDIT QU IL A DEMANDE A RENVERSE LE CHIFFRE : le classeur porte
         **4 782** commissions pour **34 280 276 EUR**, et NOUS AVONS DEJA 4 363
         (91 %) -- Hektor les calcule. « 303 » n etait pas peu : c etait LE TROU.
         Remesure le 17/11 : **332**, pas 303.
       ⛔⛔ ET LE VRAI BLOCAGE N ETAIT PAS TECHNIQUE, IL ETAIT COMPTABLE :
         **270 des 332 trous sont des affaires ANNULEES** -- commission PREVUE,
         JAMAIS PERCUE. Les poser dans « les honoraires VENDEUR saisis dans
         l app » fausserait tout calcul de chiffre d affaires. ⬜ SA DECISION du
         17/11 : « Les 62 seules » -> les 270 NE SONT PAS POSEES.
       ⭐ ET LE BLOCAGE DU PLAN (« LA CASE EXISTE, MAIS LE ROBINET EST FERME »,
         CHAMPS_APP_AFFAIRE vide) NE CONCERNE QUE LE CARNET, qui ecrit
         honoraires_entree de CLASSE C. honoraires_entree_app est de CLASSE A,
         protegee du push (l. 3108) ET creee en local (l. 620) : la section du
         plan est ANTERIEURE a cette colonne, son avertissement etait PERIME.
       ⚠ RESERVE : 42 des 62 sont des affaires EN COURS, que SA PROPRE REGLE
         ecarterait (« on ne reprend que ce que Hektor ne rendra plus »). Le patch
         les a separees en lot 3b ; il a tranche « Les deux lots ».
       ⛔ ET UN CONTROLE VIDE ATTRAPE AVANT DE LUI MONTRER : ma repetition portait
         « and false » sur les annulees -- elle rendait 0 PAR CONSTRUCTION. Un
         controle vide est pire qu aucun controle. Corrige : il liste les 270 ids.
       (ancien enonce) 3.3 LOT A : 303 commissions (1 886 204 EUR, dont 77 lignes 2026 pour
       539 070 EUR) + 10 dates de case vide. En CLASSE A. Les 24 « zeros deguises »
       (217 250 EUR) comptent comme des vides -- un zero n'est pas une saisie.
C3 ✅✅ FAIT LE 16/11 -- 450 DATES POSEES, 12 controles justes. BALAYAGE DE SES LECTEURS FAIT (16/11) : en base, AUCUNE vue, AUCUNE fonction,
   AUCUN declencheur ne lit `date_annulation_app` ni `motif_annulation_app`.
   Les deux seuls lecteurs sont dans l'ASSISTANT (assistant_objets.py:276 et
   assistant.ts:164) -- autre chantier. ⚠ En face : 3 836 affaires annulees sans
   date (1 425 compromis cancelled + 2 411 offres refused), dont 1 296 RELIEES au
   gel, donc atteignables par Z. date_annulation_app et motif_annulation_app sont
   VIDES sur toute la table (0 et 0).
C3bis ⬜ LES MOTIFS D'ANNULATION -- LA SECONDE MOITIE DE C3, PAS FAITE.
       `motif_annulation_app` = 0 sur 31 352 (mesure du 16/11 au soir).
       ⭐ SA SOURCE EST F, et le commentaire du code se trompe en disant
         qu'elle n'en a aucune (retractation 129, pret refuse 107).
       ⛔ MAIS F EST MIXTE (A1 : 3 099 cellules -- des « V », des pastilles,
         et 810 textes seulement) -> ELLE DEPEND DONC DE C4, qui tranche F.
       ⚠ NE PAS la cocher avec C3 : Z est faite, les motifs ne le sont pas.
C4 ✅✅⬜ DEUX PATCHS SUR TROIS FAITS LE 17/11 :
       1er : **169 MOTIFS + 2 CLAUSES AU CATALOGUE**, 10 controles justes.
             ⭐⭐⭐ **111 lignes portent LA DATE ET LE MOTIF** -- le « quand »
             et le « pourquoi » reunis.
       2e  : **4 325 NOTES** (4 936 textes fusionnes), 11 controles justes.
             classeur:G 3 484 . classeur:F+G 585 . classeur:F 256
       3e  : ✅✅ **POSE EN PRODUCTION LE 17/11 A 13:03** -- 80 textes de F,
             28 conditions, le CATALOGUE PASSE A SIX. **21 controles justes.**
             ⛔⛔ MON 1er VERDICT (« rien a poser ») ETAIT FAUX : sa regle
             protege du CONFLIT, et Hektor ne porte NI note NI condition
             (`conditions_suspensives` : 0 sur 18 591). Elle n'avait rien a
             proteger. ⛔ Et mon « 47 textes » etait faux : ILS SONT 80.
       ⭐⭐⭐ **F EST DECODEE LE 16/11** -- voir
       `notice/C4_LE_DECODAGE_DE_LA_COLONNE_F_2026-11-16.md`.
       ⛔ CE DECODAGE N'ETAIT ECRIT NULLE PART : ni dans les 160 notes, ni au
         plan, ni au journal, ni en memoire. « ODP » n'apparaissait dans AUCUN
         document du chantier. Frederic a du me corriger DEUX FOIS.
       LA STRUCTURE REELLE d'une ligne « en cours », regulière :
         `<date> ADP<date> ODP<date> DB<date> Me <notaire> [montant duree]`
         -> UN ECHEANCIER DE CONDITIONS SUSPENSIVES, pas une note libre.
       LE TEST QUI SEPARE LES DEUX FAMILLES : l'abreviation est-elle suivie
         d'une DATE ?  DB 66/66 = 100 % . OPC 100 % . ODP 82 % . ADP 59 % .
         DPC 55 % -- contre Me 168, PA 112, pb 92, BV 66, SRU 34 : JAMAIS.
       ✅ CONFIRME ET MESURE : ODP = offre de pret (16/11) . ADP = **ATTESTATION
         DE DEPOT DE PRET** (17/11). ⭐⭐⭐ ADP AVANT ODP 24 FOIS SUR 24, jamais
         l'inverse, ecart median 31 JOURS -- le MEME JOUR DU MOIS, un mois plus
         tard : c'est un DELAI CONTRACTUEL. Donc ADP et ODP ne sont PAS deux
         conditions : ce sont le DEPART et l'ECHEANCE de « Obtention Credit »,
         deja au catalogue (id 2, jours_defaut 45 -- le classeur montre 31).
       ⛔ MA MESURE DU 16/11 ETAIT FAUSSE (« 10 dans l'ordre, 14 hors ordre ») :
         elle melangeait DB et ne gerait pas le passage au 1er janvier.
       ⬜ DB VA EN NOTE (sa decision du 17/11) : mesuree, elle vaut « Vente
         Prevue » dans 60 cas sur 65 (92 %) -- nous l'avons deja.
       ⬜ A CONFIRMER : ADP, DB, DPC, OPC, BVok, PA, CI, AVNT, dossOk.
       LA LECTURE JUSTE EST TRIPLE : 708 MOTIFS (affaire annulee) ->
         motif_annulation_app . 86 CONDITIONS EN ATTENTE (affaire en cours)
         -> app_affaire_condition . 82 remarques d'apres-vente -> note.
       ⭐ 357 des 708 motifs tombent sur les 450 dates posees par C3 :
         le « quand » et le « pourquoi » enfin reunis.
       ⛔ ET LE CATALOGUE DES CLAUSES N'EXISTE NULLE PART : ni au classeur
         (F donne la PIECE et sa date, jamais un libelle de clause), ni chez
         Hektor (0 condition sur 18 589). Il devra etre ECRIT A LA MAIN.
       F ET G dans leurs cases existantes (apres A1, qui dira le volume) :
       F -> app_affaire_condition, G -> app_affaire_note, origine « classeur ».
       ⛔ F et G se reprennent EN BLOC, SANS INTERPRETER -- sa consigne.
C5 🔧 EN COURS -- ✅ **195 TRANSACTIONS POSEES LE 16/11**, par famille :
        96 offres « Annulee »      -> state 'refused'   (lot « offres annulees »)
        35 compromis « Annulee »   -> 'cancelled'       (lot « compromis annules »)
        64 offres « Vente reglee » -> 'accepted'        (lot « offres vente reglee »)
      Chaque lot a son patch, son INVERSE et sa REPETITION, et 10 controles justes.
      ⭐ 0 PARTIE CREEE sur les 195, et 0 STATUT DEPLACE (mesure ce soir).
      ⭐ LES GARDES ONT MORDU : 16 doublons evites au total (meme date), dont
        60CLRO51 et 6QDR3G7V -- les deux liens manquants du gel trouves le 16/11.
      ⛔ ARRETS VOLONTAIRES : 24 compromis « en attente » (affaires EN COURS,
        dates dans le futur) et 33 ventes « Vente fixee » -> voir LA REGLE.
      ⏰ RESTENT 10 lignes anciennes (5 ventes, 4 compromis, 1 offre), 2018 a
        mars 2026, sur des biens Vendu/Clos -- apres la mesure « une par une »
        des 5 ventes (reserve b de l'etat du soir).
      Generateur : phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
        (parametre par FAMILLE ; relance pour une famille deja posee, il REFUSE).
      L ENONCE D ORIGINE : LES 96 PREMIERES OFFRES SONT POSEES LE 16/11.
       11 controles justes : 96 en offre/refused, sans numero, dans la plage app,
       toutes rattachees a une chaine, 96 notes, **0 partie creee** (le temoin de
       la decision « l'acquereur va en note »), voisines 340 + 30 817 INTACTES,
       et LES DEUX SENTINELLES A 0 -- les gardes du matin ont enfin leur temoin
       positif. Patch : supabase/patch_offres_annulees_classeur_2026-11-16.sql
       (+ _INVERSE, + _REPETITION). Generateur :
       phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
       ⏰ RESTE DANS C5 : 69 offres « Vente reglee » + 2 autres etats, 68 compromis,
         6 ventes. ⚠ et 4 des 5 liens manquants du gel sont dans « Vente reglee ».
       3.3 LOT B -- CHIFFRES REFAITS LE 16/11 (voir « LE TRI FIN ... REFAIT ») :
       **174 offres + 68 compromis + 6 ventes = 248**, dans la plage app, sans
       numero Hektor. A2 ✅ et A4 ✅ sont faits.
       ⚠ les anciens « 215 (144+62+9) » venaient du rapport du 13/11, pris
         PENDANT la pose du lot 1 -- voir « A0 EST FAIT ».
       ⭐ les 242 offres+compromis n'ont AUCUN lecteur risque (A4) -- c'est la
         partie SURE du lot.
       ⛔ LE NOMBRE DE VENTES CREABLES N'EST PLUS ETABLI : mon tri du 16/11
         comparait deux dates de nature differente (voir C6). Les 39 ventes
         restent a decouper, et seules 2 familles sont sures : 2 « sans
         compromis » et 5 « notre compromis sans date d'acte ».
C6 ⬜  3.3 LOT C : **26 ventes** dont notre compromis porte DEJA une autre date
       d'acte. ⛔ C'est un CONFLIT, pas un vide -> SA DECISION.
       ⛔⛔ LE CHIFFRE DU PLAN EST CONSERVE : mon « 33 » du 16/11 etait FAUX, il
         comparait la date de vente du classeur a notre date d'acte PREVUE --
         deux choses differentes (sa correction, et le code du rapport le
         confirme, l. 788-791). Voir « LE TRI FIN ... REFAIT ».
       ⏰ LA REGLE EXACTE DES « 26 » RESTE A RETROUVER : je ne sais pas la
         reconstituer sur le rapport du jour, et je ne la devine pas.
C7 ⛔ ECARTEE LE 17/11 -- **ON NE RECUPERE PAS LES DATES PREVUES.**
       ⭐⭐⭐ ET C'EST SA QUESTION QUI A TRANCHE, pas mes arguments : « est-ce que
         les date butoir de mon apps correspondent deja avec le sheet sur annee
         2026 ? ». Mesure : **OUI, 84 % d'accord sur 2026 et 82 % sur 2027**,
         contre 23 a 44 % sur 2018-2025. L'accord MONTE avec l'annee.
           2018 23 . 2019 25 . 2020 30 . 2021 37 . 2022 36 . 2023 37
           2024 44 . 2025 43 . **2026 84** . **2027 82**  (% identiques)
         ➡ le desaccord est un probleme DU PASSE : les vieilles affaires
           divergent parce que le classeur etait le seul outil, les recentes
           concordent parce que les deux systemes travaillent ensemble.
       ⭐ ET LES 1 402 OU LE CLASSEUR A RAISON SONT CLOSES A 100 % : Vente
         reglee 1 401, Annulee 1, VIVANTES 0. Ecart median 20 jours. Corriger
         la date PREVUE d'un rendez-vous qui a eu lieu il y a des mois n'a
         aucun usage qu'on puisse nommer.
       ⛔⛔ ET LES DEUX CHEMINS SONT DISQUALIFIES PAR ECRIT (fiche du 12/11) :
         le carnet -> `date` y est surveille par R3, conflit PERMANENT ;
         une colonne du registre -> le run la pousse avec SELECT * et
         L'ECRASERAIT A NULL sur 31 151 lignes. Et app_affaire_date_convenue
         porte la date DE LA TRANSACTION, pas la date d'ACTE prevue.
       ⚠ ET RIEN N'A JAMAIS ETE POSE (son audit du 17/11) : 3 migrations pour
         ce chantier, 0 `date_acte` au carnet, apparieurs en lecture seule.
       ✅ CE QUI RESTE ET QUI COMPTE : **LES 48 ECARTS DU VIVANT** (43 en 2026
         + 5 en 2027) -- des affaires EN COURS ou une date butoir fausse peut
         faire MANQUER UNE ECHEANCE. Liste :
         `notice/C7_LES_48_ECARTS_DU_VIVANT_2026-11-17.csv`
       (ancien enonce) 3.3bis V : 2 303 ecarts + 21, decidee « tout », on ecrase.
       ⭐ Arbitre INDEPENDANT (notre date de vente, qui vient de Hektor) : le
       classeur tombe plus pres du reel 1 402 fois contre 714. -> SA DECISION.
       ⚠ Ne jamais arbitrer V par W : les deux sortent du MEME classeur (accord
         circulaire -- l'erreur que j'ai faite et rattrapee le 15/11).
C8 ✅⬜ FAIT LE 16/11 -- **3 729 dates de reglement + 3 671 numeros de
       facture** poses sur leur VENTE, 11 controles justes. ⛔ RESTE LA LECTURE
       TOLERANTE (2e geste : une fonction, le brut est pose et rien n'est perdu)
       et 72 lignes hors de portee (Y 27 . AA 70) que le re-gel rattrapera.
       3.4 Y ET AA : **3 756 + 3 741** valeurs (A1 du 16/11 ; le plan disait
       3 735 + 3 719), les DEUX plus gros postes du
       chantier, et les deux sans aucune case aujourd'hui. Apres B1 et A5.
C9 ✅⬜ 1re MOITIE FAITE LE 16/11 -- **2 588 lignes d'avis posees** dans
       app_classeur_avis (2 266 AH . 392 AI . 2 405 AJ), 13 controles justes.
       ⛔ RESTE `C` le numero de mandat (33 au classeur, ~9 utiles) : elle se
         pose sur une TRANSACTION, donc elle DEPEND DU GEL -> apres le re-gel.
       ⚠ AH et AJ se contredisent sur 229 lignes -- a reprendre tels quels.
       ⚠ 33 numeros de mandat sont RECYCLES aux charges divergentes : un numero
         n'identifie pas un mandat (4 142 doublons).
C10 ⬜ AF PRIX : 161 ecarts -> on LISTE, on n'ecrit RIEN. Sa decision « comparer ».
```

### PHASE D — FERMER

```
D1 ✅✅ FAIT LE 17/11, ET IL ETAIT BIEN PLUS LARGE QUE « 6 LIGNES » :
       • **195 liens** pour les transactions creees le 16/11, qui N'EN AVAIENT
         AUCUN -- donc invisibles a toute lecture passant par le gel. ⭐ C'est
         SA QUESTION (« on a pas deja ajoute les offres 195 ? ») qui l'a revele,
         et mon audit annoncait 233 manquantes la ou il n'y en avait 42.
       • **21 lignes** ajoutees a `app_classeur_ligne_id`, PERIMEE (4 773 pour
         4 794 au Sheet) -- et ma sentinelle B2 sous-comptait a cause d'elle.
       • **1 lien franc** : b7439331 -> 30809. Le gel passe a 12 792.
       • **2 liens MAL CIBLES corriges** (AYIHPHF5 et fa06e4e5) + Z3DYDC4X qui
         recupere le compromis qui est le sien. Voir « LES 2 LIENS MAL CIBLES ».
       ⛔ SA DECISION DU 17/11 sur ME6S0TR9 et 6a259cce : **ON NE GELE RIEN**.
       (l'enonce d'origine) 1.5 LE RE-GEL ADDITIF : 6 lignes. ⭐ Les deux
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
D4 ⬜⭐⭐ L'ARBITRAGE DU CLASSEUR -- **IL A TRANCHE LE 18/11, RIEN N'EST POSE** :
       35 verdicts, qui couvrent **36 LIGNES** : 33 commissions + 3 dates d'offre.
       6 ecartees. ⚠ 43 lignes etaient a trancher pour 41 IDENTIFIANTS -- voir la
       reserve NEFHS7JI au point 3. (⛔ MES CHIFFRES DU 18/11 AU MATIN ETAIENT FAUX :
       « 32 commissions », « 41 lignes », « 27 des 75 annulees » -- corriges par le
       controle de 06:46, qui a compte les LIGNES et non les identifiants.)
       ⛔ LA POSE ATTEND SON « VAS-Y », et TROIS questions avant :
         1. sur quelle transaction de la chaine poser -- **78** transactions sont
            visees, dont **14 ANNULEES et 15 REFUSEES** (mesure du 18/11 06:46 en
            local, colonne `state`), et sa decision du 17/11 sur C2 ecartait les
            annulees ;
         2. 61OW86CS (classeur 1 800 / nous 9 800, le seul ratio sous 0,6 -- une
            faute de frappe possible des deux cotes) ;
         3. ⛔⛔ **NEFHS7JI N'EST PAS TRANCHE EN ENTIER.** Cet identifiant porte DEUX
            lignes du classeur -- commission (ecart 15 026 EUR, x0,17) ET date
            d'offre (ecart **3 247 JOURS**) -- et la page d'arbitrage enregistrait
            **un clic PAR IDENTIFIANT, pas par ligne**. Son « le classeur a raison »
            ne dit donc pas s'il visait la commission, la date, ou les deux.
            ⭐ 1ESJE28Q est dans le meme cas (2 lignes), mais son « rien » et son
            commentaire (« apparait 2012 app et le sheet 2024 ») couvrent les deux
            sans ambiguite -- et l'audit lui a donne raison (lien FAUX).
       ✅⭐⭐⭐ ET L'AUDIT DES 6 ECARTEES EST FAIT (18/11) -- IL TRANCHE LES SIX :
         QUATRE liens sont FAUX (1ESJE28Q, 8Q3LHGZ4, 53ZS73KW, TR42PT5H) et l'audit
         NOMME le bon bien dans les quatre cas ; DEUX de ses « rien » sont a revoir
         (74IL9C8F et QH6672TZ : une autre transaction colle au JOUR EXACT, l'ecart
         est une faute d'annee). ⭐⭐⭐ LE MOTIF COMMUN : le gel s'est accroche a UN
         SEUL signal faible, et dans 3 cas sur 4 l'apparieur le disait deja (« a
         valider », « aucune », « deja prise par L4505 »).
         ⬜ A FAIRE, PLUS LARGE QUE CES 6 : balayer les liens du gel dont la
           confiance de l'apparieur est « aucune » ou « a valider » (lecon 9).
       Detail complet : « L'AUDIT DES 6 ECARTEES EST FAIT -- 18/11 ».
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
