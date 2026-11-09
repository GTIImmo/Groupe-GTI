# LES 38 COLONNES DU CLASSEUR — REPRISE OU NON, UNE PAR UNE

**09/11/2026.** Demandé par Frédéric : *« Donne moi la liste de colonnes du sheet et
notre décision de reprise ou non. »*

⛔ **CE DOCUMENT NE DÉCIDE RIEN.** Il RASSEMBLE ce qui est déjà décidé, et nomme ce qui
ne l'est pas. La source de vérité des décisions reste
**`DECISIONS_CHAMP_PAR_CHAMP_CLASSEUR_2026-11-02.md`**.

**Les chiffres sont ceux du gel relancé le 09/11** (`A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-11-09.csv`),
sur 4 783 lignes lues et 4 679 reliées.

**Trois marques, et trois seulement :**

```
PRISE     la decision est prise, avec sa date et par qui
PROPOSEE  je l'ai recommandee, elle attend un oui ou un non
OUVERTE   personne n'a rien decide, et je ne sais pas trancher seul
```

---

# LA LISTE, DANS L'ORDRE DU CLASSEUR

## A — `affair_uuid` · 0 remplie sur 4 783

**PRISE le 05/11, par Frédéric** : *« pour l'instant on la laisse vide »*.
**On ne touche pas.** Le pont existe déjà par « ID Unique ». Un second pont serait une
occasion de divergence.

## B — `product_ref` · 694 remplies · 69 écarts

**PRISE le 29/10** (A5 §5) : **ON NE FAIT PAS**. Confirmée le 05/11 (*« pas utile »*).
⭐ Mais elle garde **trois usages en lecture** (A4bis) : 599 confirmations indépendantes
du gel · 12 lignes « à créer » dont le bien est identifié · 69 écarts à regarder.

## C — `Mandat` · 4 783 remplies · 134 écarts · 33 « le classeur seul »

**PRISE le 29/10** (A5 §9) : **LES 33 VIDES SEULEMENT**. Les 134 écarts **ne s'écrasent
pas** — quand l'affaire passe par un mandat de recherche, le classeur porte le numéro de
recherche et nous celui de vente : **les deux sont justes**.

⛔ **CONTREDITE LE 05/11, PAR MA FAUTE — À ROUVRIR.** J'ai présenté le piège de la
classe C (le run de nuit relit `numero_mandat`) comme un obstacle, et obtenu *« on n'y
touche pas »*. Or le remède était écrit le 29/10 (A5 §6 n°3) : **une colonne « à nous »**.
➡ Le rattrapage des 33 est **possible**. Il demande une colonne, pas un refus.

## D — `Nature` · 4 783 remplies · 1 650 écarts

**PRISE le 29/10** (A5 §5) : **ON NE FAIT PAS**. Et A4bis insiste : ne pas aligner.
⭐ Mesure du 05/11 qui le confirme : sur 1 650 écarts, **1 623 sont « le classeur dit
Autre et nous savons »** — une absence au classeur, pas un désaccord. **27 vrais
désaccords** seulement.

## E — `Lien CRM` · 4 689 remplies

**PROPOSÉE** : **rien à reprendre**. La Carte des champs (29/10) la rangeait déjà dans
*« ce qui appartient au classeur seul — ne jamais toucher »*.
⭐ **La question « qu'est-ce que Netty, ça sert encore ? » est répondue (05/11)** : la
colonne est une **archéologie** — cinq logiciels successifs. Neosphere 1 976 · Sphere /
Rodacom 1 826 · Netty 505 · La Boîte Immo 301 · **Hektor 79**. Quatre des cinq sont morts.
Elle **date** l'affaire, elle ne la décrit pas.

## F — `En attente de` · 3 089 remplies · 944 valeurs distinctes

**OUVERTE — et elle demande un TRAITEMENT avant toute intégration.**

A4bis §5 la classe *« à ne pas récupérer — vos notes et votre process »*, **mais ne
recommande pas de l'oublier**. L'option écrite le 31/10, jamais tranchée :
**reprendre les textes EN BLOC, tels quels, dans une note libre attachée à l'affaire,
SANS AUCUNE INTERPRÉTATION.** *« Coût faible, perte zéro. »*

⭐ **Ce que la mesure du 05/11 a ajouté, et qui change la valeur de cette colonne** :

```
« V » SEUL             1 537 lignes, et 1 537 sur 1 537 sont « Vente reglee ».
                       V = VENDU. Certain, zero exception.
le rond VERT             549 lignes -> « Vente reglee » 96 %
le rond ROUGE            153 lignes -> « Annulee »      99 %
le P encercle            378 lignes -> PAS un etat (64 %). Suit le FINANCEMENT :
le sac d'argent          167 lignes    le texte libre porte « 260K 25a », « 145K 20a »,
                                       « relais » -> montant et duree du PRET.
la petite maison          30 lignes -> aucune piste
```

⭐⭐ **Et le vrai contenu utile : LA CAUSE DES ANNULATIONS.** Chaque motif pointe vers
« Annulée » à 100 % :

```
retractation / SRU   129 lignes -> Annulee 129 / 129
pret refuse          107 lignes -> Annulee 107 / 107
annulation            70 lignes -> Annulee  70 /  70
travaux               11 . succession ou divorce 10 . changement d'avis 8 . tous a 100 %
```

➡ **C'est une information que le projet n'a NULLE PART ailleurs** : nous savons qu'une
vente tombe, jamais pourquoi. Environ **383 des 896 annulations** ont un motif
identifiable tout de suite ; 734 lignes de texte restent à regrouper.

⚠ **Les traitements nécessaires avant toute intégration**, mesurés :
```
① SEPARER le pictogramme du texte : ils sont melanges dans la meme case.
② NORMALISER : « refus pret » (31) et « refus de pret » (24) sont la MEME chose ;
  « annule » (7) et « annulee » (9) aussi. Aucune normalisation au classeur.
③ ECARTER ce qui n'est pas un etat : « V Sarah », « V Anne », « V Tatiana » portent
  des PRENOMS ; « 260K 25a » porte un financement.
④ LE CLASSEUR CONTIENT DES EMOJI, et un script naif meurt dessus (vu le 05/11).
```

## G — `COMMENTAIRES` · 4 120 remplies · 2 598 distinctes

**OUVERTE — même traitement que F, et c'est la même proposition du 31/10.**

A4bis : *« `COMMENTAIRES` porte 4 116 textes du genre "Annulation offre car budget
travaux trop important". **C'est la seule trace du POURQUOI**, et nous ne l'avons nulle
part. ⬜ Option à trancher : les reprendre **en bloc, tels quels**, dans une note libre
attachée à l'affaire — **sans aucune interprétation**. Coût faible, perte zéro. »*

⬜ **Cette décision est listée comme « SA DÉCISION » depuis le 31/10. Elle attend.**

## H — `Agence` · 4 766 remplies · 498 écarts

**OUVERTE.** ⚠ **La cause des 498 écarts n'est TOUJOURS pas mesurée** — réserve du
29/10, répétée le 31/10 (*« mesure courte »*) et le 02/11. **À comprendre avant de
classer.** 498 écarts inchangés en onze jours.

## I — `Négociateur 1` · 4 778 remplies · 430 écarts

**PRISE le 02/11, par Frédéric : LE CLASSEUR FAIT FOI sur les 432 écarts. Sur conflit :
ÉCRASER.**

Ce qu'il savait : 99 noms distincts ; dans **213** des 432 c'est **nous** qui ne savons
pas (91 « cet utilisateur a été supprimé », 122 « Groupe GTI » = l'agence au lieu de la
personne) ; les **219 autres désignent deux personnes différentes**, et **il a choisi de
les écraser aussi, au-delà de ma recommandation** qui proposait de les lister.

## J · L · N — les trois `Pourcentage` · 4 777 / 684 / 14

**PRISE le 02/11, par Frédéric : LE CLASSEUR FAIT FOI PARTOUT, SANS EXCEPTION** — y
compris sur nos 501 lignes d'origine « hektor » et nos 20 « saisie », **au-delà de ma
recommandation** qui proposait de les protéger.

```
⭐⭐⭐ LA SOMME DES TROIS FAIT EXACTEMENT 100 dans 4 768 cas sur 4 780 (99,75 %).
     C'est LA COLONNE LA MIEUX TENUE DES 38. Lisibles a 100 % : 4 773 / 4 773.
     Les 5 anomalies : 2 lignes a 50, 2 a 200, 1 a 150. Plus 7 sans pourcentage 1.
⛔  En face, app_affaire_repartition porte 16 106 lignes dont 15 581 marquees
     « hektor_partage_suppose » (96 %) -- UN CALCUL PAR DEFAUT, PAS UNE DONNEE.
```

⚠ **PIÈGE DE FORMAT À CODER** : `Pourcentage 3` porte **« 12,5 » avec une virgule**. Une
conversion naïve rend 125, ou zéro. **Un seul cas, et il suffit à fausser une paie.**

## K et M — `Négociateur 2` et `Négociateur 3` · 687 et 13 remplies · 375 et 9 écarts

**PRISE le 02/11, par Frédéric : LE CLASSEUR FAIT FOI PARTOUT. Sur conflit : ÉCRASER.**

Ce qu'il savait : le classeur porte **687** seconds et **13** troisièmes ; nous portons
**209** valeurs et 15 lignes de rang > 1. Sur les 374 écarts, 117 sont des cases où nous
ne savons pas et 257 désignent deux personnes. Le risque lui a été dit, il a tranché.

⚠⚠ **UN POINT NON CONFIRMÉ, ET IL COMPTE** :
```
« Faire foi » s'applique a une VALEUR, pas a une ABSENCE. J'applique donc : le
classeur gagne PARTOUT OU IL PORTE QUELQUE CHOSE, et la ou il est VIDE nous gardons
ce que nous avons. Sinon ses 687 valeurs EFFACERAIENT nos 209 sur les lignes ou il
n'a rien ecrit -- une destruction qu'aucune source ne demande.
⬜ A CONFIRMER PAR LUI.
```

## ⛔ LES QUATRE PRÉALABLES DU LOT DES NÉGOCIATEURS — aucun n'est fait

```
1. LES 14 ANCIENS NEGOCIATEURS crees dans l'annuaire d'abord, sinon 213 cases
   pointent vers quelqu'un qui n'existe pas chez nous.
   ⚠ ET LE RAPPORT DU 09/11 EN COMPTE 24, pas 14 : dix de plus sont apparus.
2. LA TABLE D'ALIAS : GIRAUD = Aline VALETTE (158 cas) · ALVES MENDES = Lucie
   DECHANDON (118 cas). Sans elle on ajoute la meme personne deux fois et ON COUPE
   SA COMMISSION EN DEUX, sur 282 cases.
   ⚠ Ce n'est PAS une table aujourd'hui : 2 entrees EN DUR dans un script.
   ⭐ Elle est enfin FAISABLE : le registre des negociateurs est pose depuis le 04/11.
3. « meilleursagents », « GTI », « DENOPCE 1/2 » EXCLUS -- ce ne sont pas des
   personnes (meilleursagents : 17 fois sur 17 en negociateur 2, c'est un apporteur).
4. LES 30 DOSSIERS « notre nom est etranger aux deux » ECARTES.
```

## O — `Notaire` · 2 567 remplies · 1 370 écarts · 483 vides chez nous

**PROPOSÉE** : **les 480 vides seulement**, rien d'autre.
⛔ **Les 1 370 ne sont PAS des écarts** : nous portons **deux** notaires (acquéreur et
vendeur), le classeur **un seul**.
⬜ **SA DÉCISION, attendue depuis le 31/10** : le notaire du classeur va **dans lequel
des deux** ?

## P — `Commission TTC` · 4 778 remplies · 83 écarts · 377 vides chez nous

**PROPOSÉE** : **les 378 vides**. ⚠ Et A5 §2 prévient : *« possible, mais PAS dans la
colonne évidente »* — le rapport la lit par `honoraires_entree` (TTC), 4 302 fois.

## Q — `Charge Commission` · 960 remplies

**PRISE le 02/11 — ET FAITE le 04/11.** ✅ **23 474 valeurs posées**, couverture 95,5 %,
dont **837 venues du classeur** (origine = classeur, elle fait foi), 14 contrôles verts.

⛔⛔ **MAIS LE RAPPORT DE GEL ANNONCE ENCORE « 933 À PRENDRE ». C'EST FAUX, et c'est le
défaut trouvé le 09/11** : il lit `app_affaire_ledger.charge_commission_app` (7 lignes
remplies sur 31 143) alors que la charge vit dans
`app_mandat_register_current.mandat_charge_honoraires_app` (**23 474 sur 24 579**).
**La charge est un attribut du MANDAT, pas de l'affaire.**
⬜ **Correction à faire, non faite : j'attends l'accord**, parce qu'elle change un
chiffre de référence du chantier.

## R — `Etat Actuel` · 4 783 remplies · 172 écarts

**PROPOSÉE** : **nous faisons foi, mais on LISTE, on n'écrase pas.**
⚠ Parce que c'est **un état CALCULÉ**, pas une donnée saisie : corriger n'a pas de sens.

## S — `Offre Achat` · 4 745 remplies · 211 écarts · 178 vides

**PROPOSÉE** : **les 178 vides seulement**. ⚠ C'est **la moins fiable des trois dates**.

## T — `Compromis` · 4 231 remplies · 44 écarts · 113 vides

**PROPOSÉE** : **les vides seulement** (106 au 29/10, 113 aujourd'hui). 98,7 % de
concordance ailleurs.

## U et X — `Signé` et `Signée` · 4 783 remplies chacune

**OUVERTES — jamais analysées.** Deux valeurs seulement : `TRUE` / `FALSE`.

## V — `Vente Prévue` · 4 027 remplies · 1 768 écarts

**PROPOSÉE** : **PERSONNE ne fait foi — ne PAS aligner.** 56 % des comparables : c'est
une date qui **bouge par nature**. ⭐ Mais **les 44 vides + les 13 en cours** se posent
sans risque.

## W — `Vente Fixée` · 3 777 remplies · 61 écarts · 39 vides

**PROPOSÉE** : **les vides seulement** (31 au 29/10, 39 aujourd'hui). 98 % de concordance.

## Y — `Vente Réglée` · 3 752 remplies · 3 723 « le classeur seul »

⛔ **NOUS N'AVONS AUCUN CHAMP, NULLE PART.**
⚠ Et **ce n'est PAS notre date d'acte** : +3 jours de médiane (mesure du 19/10). Ce n'est
pas « le classeur a tort », **c'est un AUTRE champ**.
⬜ **SA DÉCISION : créer le champ, ou ignorer ?** En attente depuis le 29/10.

## Z — `Annulée` · 896 remplies

**OUVERTE.** ⬜ **Mesure courte jamais faite** : *avons-nous une date d'annulation ?*
Listée le 31/10, toujours pas mesurée.

## AA — `Numéro de facture` · 3 730 remplies

⛔ **AUCUN CHAMP CHEZ NOUS.** Et ⚠ **ce n'est pas un simple numéro** :
*« GGTI00004147 / 14.10 relance parrainage Jerome Matte »* — **du numéro ET du texte dans
la même case**. Donc un traitement serait nécessaire.
⬜ **SA DÉCISION : créer, ou ignorer ?**

## AB et AD — `Acquéreur` et `Vendeur` · 4 783 remplies · 119 et 68 écarts

**PROPOSÉE** : **EN AJOUT SEULEMENT, jamais en remplacement.**
⚠ Et **en sautant les transactions au chaînage douteux** : elles étaient 2 212 le 31/10,
elles sont **2 209 aujourd'hui**.

## AC et AE — `Adresse Acquéreur` et `Adresse Vendeur` · 60 et 799 remplies

AC : **1,3 %, négligeable**. AE : **OUVERTE, jamais analysée.**

## AF — `Prix` · 4 778 remplies · 207 écarts

**PROPOSÉE — et c'est le SEUL champ dans ce cas : propriété PARTAGÉE PAR ANNÉE.**
**NOUS à partir du 01/01/2025 · LE CLASSEUR avant.**
⭐ C'est lui qui justifie la colonne `depuis_quand` de la table de propriété.
⚠ Deux notes du rapport : 2 668 lignes sont hors périmètre (année < 2025), et **1 020
lignes où le classeur porte un DÉPARTEMENT** (1 à 3 chiffres) au lieu d'un prix.

## AG — `Ville` · 4 771 remplies · 1 644 écarts

**PRISE le 29/10** (A5 §5) : **ON NE FAIT PAS.** Le classeur est saisi à la main.

## AH · AI · AJ — `Avis à envoyer` · `Commentaire Avis` · `Avis envoyé` · 2 255 · 392 · 2 401

**OUVERTES.** Classées *« vos notes et votre process »* par A4bis §5.
⬜ **SA DÉCISION : créer les champs, ou ignorer ?**

## AK — `Divers` · 12 remplies

**0,3 %, négligeable.**

## AL — `ID Unique` · 4 783 remplies

⭐⭐⭐ **LA CLÉ DU PONT. NE JAMAIS TOUCHER.** C'est par elle que les 12 413 liens du gel
sont attachés — **et pas par le numéro de ligne**, ce qui est exactement ce qui rend le
gel durable quand le classeur grandit ou se trie.

---

# LE COMPTE

```
PRISES, et executees         1 colonne    Q (04/11)
PRISES, pas encore faites   10 colonnes   A B C D I J K L M N
PROPOSEES, attendent un oui 11 colonnes   E O P R S T V W AB AD AF + AG (prise)
OUVERTES, rien decide       12 colonnes   F G H U X Y Z AA AE AH AI AJ
SANS OBJET                   4 colonnes   AC AK (negligeables) . AL (la cle) . et B en lecture
```

⭐ **Ce qui est récupérable SANS AUCUN ARBITRAGE** (des cases VIDES chez nous), chiffré le
29/10 et toujours vrai : **~2 276 cases** — notaire 480 · commission 378 · dates 326 ·
mandat 33 · négociateurs à poser 126 · et la charge, qui est faite.

⛔ **Ce qu'il ne faut PAS faire, même si c'est tentant** : aligner Vente Prévue (1 768),
Ville (1 644) et Nature (1 650). **5 062 écarts qui ne valent rien à corriger**, et dont
une large part serait même à corriger **dans l'autre sens**.
