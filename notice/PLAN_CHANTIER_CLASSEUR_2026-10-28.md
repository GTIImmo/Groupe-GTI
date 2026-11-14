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

   ⛔⛔ LE PREALABLE OBLIGATOIRE, ET IL N'EST PAS REMPLI : **13 ANCIENS
     NEGOCIATEURS A CREER** dans l'annuaire. Tant qu'ils n'existent pas, leurs
     24 lignes restent « hors perimetre » et ne seront pas rapatriees :
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

3.2bis ⬜ ACCORD    LA CHARGE DE COMMISSION -- ⭐⭐⭐ **ELLE A CHANGE DE TAILLE LE
                    14/11 : 46 LIGNES, PAS 955.** La correction de la case lue
                    ci-dessus a rendu la mesure possible :
```
                    identique      904        <- rien a faire
                    classeur seul   44        <- a POSER
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
