# AUDIT — QUAND HEKTOR SUPPRIME UNE VENTE OU UN COMPROMIS

**13/11/2026** — demandé par Frédéric :

> *« Si une vente ou un compromis est supprimé dans Hektor, mon app protège son écriture.
> Ces gestes chez Hektor sont réguliers, il faut pouvoir le gérer aussi. Nous avons déjà
> fait plusieurs chantiers sur ce sujet, donc peux-tu faire un audit. »*

> ⛔ **LECTURE SEULE.** Rien n'a été écrit en base, ni chez Hektor, ni dans le classeur.

---

## 1. CE QUI EXISTE DÉJÀ, ET QUI MARCHE

**La doctrine est écrite** dans `phase2/sync/affaire_ledger.py`, en tête :

> *« en UPSERT sur l'id stable […] mais **jamais supprimée** : si Hektor retire une
> affaire, on la conserve avec `present_in_hektor = false`. […] ici on ne fait que
> **sécuriser la donnée**. »*

⭐ **Le drapeau est posé automatiquement**, chaque nuit, en mode full : les lignes non revues
passent à `present_in_hektor = 0` (`affaire_ledger.py` l. 584 et 1060).

**Et il est respecté là où ça compte** — mesuré fonction par fonction :

```
app_registre_dossiers            en tient compte   ✅
app_statut_redescente_calcule    en tient compte   ✅ aux TROIS niveaux
app_chaine_pour (2 signatures)   en tient compte   ✅
app_ecart_statut_regle (la vue)  en tient compte   ✅
+ 19 autres fonctions le lisent (photos, parties, gestes optimistes…)
```

⭐⭐ **PREUVE PAR L'EXEMPLE, et c'est la trouvaille de cet audit :** le bien **58979** porte
un compromis `active` que Hektor a supprimé. **Notre règle rend « Sous offre », exactement
comme Hektor** — et le bien **n'apparaît pas** dans la vue des écarts. Le mécanisme
fonctionne : la transaction est **conservée** mais **ne décide plus**.

---

## 2. ⛔ LE TROU — et il n'est pas où on l'attend

### ⛔ ① LA POSE D'ÉTIQUETTE NE REGARDE PAS LE DRAPEAU

```
fonctions d'etiquette qui lisent present_in_hektor :  0
```

Les **18** transactions retirées par Hektor sont **toutes encore chaînées et étiquetées** :

```
compromis active      8      offre accepted   5      compromis cancelled  3
offre proposed        1      vente            1
                                                            TOTAL  18
```

⚠ **Ce n'est pas grave aujourd'hui** (l'étiquette n'est lue par personne, mesuré le 12/11)
**mais ça le deviendra à l'étape 5.2**, quand les UUID partiront dans le classeur : une
transaction morte y porterait un numéro de dossier vivant.

### ⛔⛔ ② IL N'EXISTE AUCUN GESTE POUR DIRE « CETTE TRANSACTION EST MORTE »

C'est **le vrai trou**, et il est exactement celui que Frédéric a rencontré :

```
Hektor retire la transaction   ->  present_in_hektor = false, AUTOMATIQUE   ✅
NOUS voulons la retirer        ->  AUCUN CHEMIN                             ⛔
   alors que Hektor la garde
```

Le cas **8494** le montre : son compromis `3699` est **actif ET présent chez Hektor**, mais
il est **faux** (sans date, et la vente du bien a disparu de chez eux). Frédéric veut le
retirer **de l'app seulement**. Aujourd'hui il n'y a pas de bouton pour ça.

⚠ **Et les gestes existants ne conviennent pas :**

```
delete_hektor_compromis   SUPPRIME CHEZ HEKTOR -- ce n'est pas ce qu'on veut
cancel_hektor_compromis   l'ANNULE chez Hektor -- non plus
le carnet app_affaire_champ_app  porte des CHAMPS, pas une EXISTENCE
```

⭐ **La mémoire du projet le disait déjà**, sans qu'on en ait tiré la conséquence :
*« Aucun travail ne corrige un CHAMP chez Hektor — les 4 types d'affaire ne changent qu'un
ÉTAT. »* Il manque le cinquième verbe : **« ne compte plus chez nous »**.

### ⚠ ③ ET LA SENTINELLE NE VOIT QU'UN SENS

`data.ecart_statut_regle` ne surveille que `sens = remontee` — les cas où **Hektor est en
retard**. Les **redescentes** (notre règle dit moins avancé que Hektor) ne sont pas
comptées. Mesuré aujourd'hui : **1 cas**, le bien `55086` (« Actif » contre « Sous offre »,
une offre refusée seule). C'est un choix délibéré et documenté — à savoir, pas à corriger.

---

## 3. LES TROIS BIENS DU JOUR, ET CE QU'ILS DEMANDENT CHACUN

```
58979   compromis RETIRE PAR HEKTOR, conserve chez nous
        notre regle dit deja « Sous offre » = Hektor
        ➡ RIEN A FAIRE POUR LE STATUT. Il n'est meme pas dans la vue des ecarts.
        ⬜ reste : il compte encore dans le CHAINAGE et porte une ETIQUETTE.

8494    compromis 3699 ACTIF ET PRESENT chez Hektor, mais faux (sans date,
        et la vente du bien a disparu de chez eux)
        notre regle dit « Sous compromis », Hektor dit « Sous offre »
        ➡ C'EST LUI QUI DEMANDE LE GESTE MANQUANT.

62049   le compromis 50157 est actif ET present : notre regle a RAISON
        ➡ C'est HEKTOR qui est en retard. Correction a la main (Frederic).
```

---

## 4. ⭐ CE QUE JE PROPOSE — et pourquoi dans cet ordre

### ① LE GESTE MANQUANT : « cette transaction ne compte plus chez nous »

Une colonne `app_ignoree_le` / `app_ignoree_par` / `app_ignoree_pourquoi` sur
`app_affaire_ledger`, et **un seul prédicat partagé** — le patron du projet, déjà éprouvé
pour les coquilles d'offre (`app_affaire_est_coquille`, 02/11) :

```
app_affaire_compte_encore(l)   =  present_in_hektor  ET  app_ignoree_le IS NULL
```

⭐⭐ **POURQUOI UNE EXCLUSION À PART ET PAS UNE SUPPRESSION :** la règle du projet est
« un numéro ne se perd jamais », et la doctrine du registre est « jamais supprimée ». On
**marque**, on ne détruit pas — et la ligne reste visible avec son motif.

⛔ **ET LE PIÈGE À ÉVITER, il a déjà coûté** (les brouillons, 20/10) : *une exclusion rangée
à côté sans être appelée partout recrée le défaut.* Le prédicat doit être appelé par
**chaque porte** : le registre, la règle de statut, le chaînage, la pose d'étiquette, le
pilotage, la table des parties.

### ② BOUCHER LE TROU DE L'ÉTIQUETTE

La pose doit ignorer ce qui ne compte plus. **Avant 5.2**, pas après.

### ③ ET UN CONTRÔLE, parce que ce cas se reproduira

Une sentinelle « transactions que Hektor a retirées et qui comptent encore » — avec son
témoin positif. Aujourd'hui elle dirait **18**.

---

## 5. ⛔ CE QUE CET AUDIT A CORRIGÉ DANS MES PROPRES MESURES

**J'ai appelé `app_statut_redescente_calcule(hektor_annonce_id)` alors que son paramètre
est `app_dossier_id`.** Elle ne trouvait donc aucune transaction et rendait « Actif » par
son `ELSE` — pour les 15 biens vendus **et** pour les 3 d'aujourd'hui.

⛔ **J'en avais tiré une conclusion fausse, annoncée à Frédéric** : *« elle rend Actif, donc
elle aurait republié 15 biens vendus sur les portails »*. **C'était faux.** Avec le bon
paramètre elle rend « Vendu », correctement. Le piège n'existait pas.

⭐ *Leçon : une fonction qui rend une valeur plausible ne prouve pas qu'on l'a bien
appelée. Vérifier la signature avant de conclure — surtout quand la réponse confirme ce
qu'on soupçonnait.*
