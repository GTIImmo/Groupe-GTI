# AUDIT — LA DATE D'ANNULATION : OÙ LA METTRE, ET COMMENT LA FAIRE AGIR ?

**09/11/2026.** Demande de Frédéric : *« Audit, et as-tu aussi la solution pour la date
d'annulation ? Mesure et analyse. »*

⛔ **Lecture seule. Rien n'est codé, rien n'est écrit en base.**

## CE QU'IL A DEMANDÉ, DANS SES MOTS

```
09/11  « Annulee tout avec un nouveau champ »
09/11  « c'est la date annulation qui fait l'etat actuel annule »
09/11  « une date d'annulation permettrait de cloturer la chaine comme une vente
         afin d'en ouvrir une autre »
09/11  « jai pas dit de supprimer, uniquement on recupere la date d'annulation, on
         cloture le dossier, on passe compromis en annule et offre d'achat en refuse
         en meme temps »
```

➡ **La date n'est donc pas une case à ranger : elle doit AGIR.** Ranger la date est réglé
*(table `app_affaire_suivi`, patch du 09/11)*. Cette note traite **l'action**.

---

# 1. ⭐⭐ LE TROU, MESURÉ — *et il est exactement celui qu'il décrit*

Chez Hektor et chez nous, **seules l'offre et le compromis ont un état. Une vente n'en a
aucun :** 9 277 ventes sur 9 277 ont un `state` **vide**. Une vente annulée n'est donc pas
*marquée* annulée — **elle est supprimée**, et rien ne reste.

**Conséquence, mesurée sur les 4 688 lignes du classeur, croisée avec ce qui ferme la
chaîne :**

```
ce qui ferme la chaine chez nous    ce que dit le classeur         lignes
la vente                            Vente reglee                    3 713   ✅
un compromis annule                 ANNULEE avec une date             494   ✅
une offre refusee                   ANNULEE avec une date             236   ✅
⛔ RIEN -- la chaine est OUVERTE    ANNULEE avec une date             100   ⛔ LE TROU
⛔ RIEN -- la chaine est OUVERTE    Vente prevue / fixee / en cours   138   ✅ normal
la vente                            ANNULEE avec une date               3   ⚠ a regarder
un compromis annule                 Vente reglee                        4   ⚠ a regarder
```

⭐ **Les deux systèmes sont d'accord à 99,7 %.** Le désaccord réel tient en **100 lignes** :
le classeur sait l'affaire annulée, et chez nous **rien ne ferme le dossier**.

## ⭐ ET CES 100 SONT LES DOSSIERS FANTÔMES

Mesure du 09/11 : **595 affaires chez nous ne contiennent qu'une offre acceptée, toute
seule** — acceptées puis plus rien, **545 sans mouvement depuis plus de 18 mois**, la plus
ancienne de **2006**. Sur les 136 de ces 595 qui sont reliées au classeur, **95 sont
déclarées annulées avec une date**.

➡ **Le classeur détient la réponse que l'app n'a pas.** C'est tout l'intérêt du rattrapage.

---

# 2. LES TROIS VOIES — *deux sont ÉLIMINÉES PAR LA MESURE*

## ⛔ VOIE A — écrire les états chez Hektor : **IMPOSSIBLE**

Ce qu'il faudrait changer, transaction par transaction, sur les 100 dossiers :

```
offre      accepted -> refused     97   (95 %)
compromis  active   -> cancelled    5
                                  ---
                                  102 ecritures chez Hektor
```

⛔⛔ **ET LES 97 NE PEUVENT PAS ABOUTIR. C'EST MESURÉ DEPUIS LE 13/10** *(mémoire
`offre-acceptee-hektor-refuse-en-silence`, 12 offres réelles)* :

```
offre accepted   ->  HTTP 200, 0 OCTET            9 sur 9
offre proposed   ->  HTTP 200, ~230 000 octets    2 sur 2
offre refused    ->  HTTP 200, ~230 000 octets    1 sur 1
```

**Hektor refuse d'ouvrir le formulaire d'une offre acceptée.** Il ne rend rien, et le refus
est **silencieux**. ➡ **95 % de la voie A échouerait sans le dire.** Et les 5 % restants
seraient 5 écritures irréversibles sur des affaires closes depuis des années.

⛔ **Voie A éliminée.**

## ⛔ VOIE B — écrire les états chez nous seulement : **ÉCRASÉE CHAQUE NUIT**

`phase2/sync/affaire_ledger.py:909`, dans le `ON CONFLICT DO UPDATE SET` du registre :

```
state=excluded.state, montant=excluded.montant, date=excluded.date, ...
```

➡ **Le run recopie l'état de Hektor sur le nôtre, toutes les nuits.** Un état changé chez
nous ne tiendrait pas 24 heures.

⚠ **Et le « remède » serait pire** : retirer `state` de cette liste protégerait notre
écriture, mais **aveuglerait la relecture pour les 31 143 transactions** — on ne verrait
plus un vrai changement d'état chez Hektor. ⛔ **Voie B éliminée.**

## ✅ VOIE C — la date d'annulation FERME LA CHAÎNE, sans toucher aucun état

**C'est littéralement ce qu'il a dit** : *« une date d'annulation permettrait de clôturer la
chaîne comme une vente »*. La règle de chaînage ferme aujourd'hui sur trois critères *(règle
du 04/09)* : la vente · le compromis annulé · l'offre refusée sans autre offre vivante.
**On en ajoute un quatrième : une date d'annulation dans `app_affaire_suivi`.**

```
✅ RIEN n'est ecrit chez Hektor               -> aucun risque, aucun refus silencieux
✅ RIEN n'est ecrase par le run               -> app_affaire_suivi n'est pas relue
✅ RIEN n'est falsifie                        -> l'offre reste « acceptee » chez Hektor,
                                                 parce que c'est la VERITE de Hektor ;
                                                 nous AJOUTONS ce que nous savons
✅ CA S'APPLIQUE A TOUT LE PASSE D'UN COUP    -> la chaine est une DEDUCTION refaite
                                                 chaque nuit (0,09 s sur 29 321 lignes),
                                                 pas une donnee a migrer
✅ RETOUR ARRIERE GRATUIT                     -> un interrupteur, comme APP_CHAINAGE_V2 :
                                                 « il n'y a rien a migrer, donc rien a
                                                 defaire »
```

### ⭐⭐ ET LE TÉMOIN INVERSE EST PARFAIT — *la règle ne ferme QUE ce qu'il faut*

Les chaînes du classeur restées ouvertes **sans** date d'annulation, que la règle **ne
toucherait pas** :

```
Vente prevue          67        Offre d'achat         17
Vente fixee           26        Vente reglee           7
Compromis en attente  20        Compromis signe        1
                             -------
                                138  -> de VRAIES affaires en cours
```

➡ **100 fermées, 138 laissées ouvertes, et le partage est exactement le bon.** La règle ne
ferme que ce que le classeur déclare annulé.

### ⭐ CE QUE ÇA RÈGLE, ET QU'IL AVAIT ANNONCÉ

> *« afin d'en ouvrir une autre »*

Une chaîne fermée ne reçoit plus rien *(règle du 04/09)*. Donc une nouvelle offre sur le même
bien **ouvrira un nouveau dossier** au lieu de rejoindre celui de 2006. ⚠ **L'effet passé est
petit** — mesure du 09/11 : seules **2 chaînes** sur 753 ont absorbé une affaire plus tardive
*(plus d'un an d'écart entre leur première et leur dernière transaction)*. **C'est donc une
prévention, pas une réparation de masse.** Mais elle ferme **595 dossiers fantômes**, ce qui
est l'autre moitié du gain.

---

# 3. ⚖ LA SOLUTION COMPLÈTE, EN TROIS PIÈCES

```
① RANGER   table app_affaire_suivi, colonne `date_annulation`
           ✅ le patch est ecrit (supabase/patch_affaire_suivi_2026-11-09.sql)
② REMPLIR  les 896 dates du classeur, par le rattrapage (P1.4)
           ⬜ a faire, avec la liste sous les yeux, apres la relance du rapport
③ AGIR     la regle de chainage lit `date_annulation` et FERME la chaine
           ⬜ a faire, DERRIERE UN INTERRUPTEUR, et en DEUX endroits qui doivent
              dire la meme chose :
                recalculer_les_chaines()   phase2/sync/affaire_ledger.py  (le run)
                app_chaine_pour()          Supabase                        (entre deux runs)
              ⚠ « Deux copies d'une formule divergent tot ou tard : toute correction
                ici doit etre reportee la-bas, et l'inverse. » (patch du 05/09)
```

⭐ **L'ordre compte** : ② avant ③. Allumer la fermeture avant d'avoir les dates ne fermerait
rien ; les ranger sans allumer la fermeture ne ferait aucun mal. **Les deux gestes sont donc
indépendants et réversibles séparément.**

## ⛔ CE QUE JE NE RECOMMANDE PAS

```
. NE PAS changer les etats, ni chez Hektor (impossible) ni chez nous (ecrase).
. NE PAS retirer `state` du ON CONFLICT du run : ca aveuglerait 31 143 transactions.
. NE PAS toucher aux trois criteres de fermeture existants. On en AJOUTE un quatrieme.
. NE PAS allumer la fermeture sans l'interrupteur : la regle touche 12 138 dossiers.
```

---

# 4. ⚠ CE QUI RESTE À REGARDER — *petit, mais nommé*

```
. 3 LIGNES ou une VENTE existe chez nous ALORS QUE le classeur dit « annulee avec une
  date ». Soit la vente a ete passee puis l'affaire defaite, soit le classeur se trompe.
  ⛔ La voie C fermerait DEJA ces chaines par la vente : la date d'annulation n'y
  changerait rien. A auditer une par une, c'est 3 cas.
. 4 LIGNES ou un compromis est annule chez nous et le classeur dit « Vente reglee ».
  Le symetrique. Meme traitement.
. L'ECRAN ne sait pas lire `date_annulation`. Tant qu'il ne le sait pas, une affaire
  fermee par cette regle n'affichera aucune raison. A traiter avec l'affichage.
. ⬜ NON MESURE : si une chaine fermee par une date d'annulation puis REOUVERTE (la
  date retiree du classeur) retrouve exactement sa forme d'avant. La deduction devrait
  le garantir -- elle n'a aucun etat -- mais je ne l'ai pas eprouve.
```
