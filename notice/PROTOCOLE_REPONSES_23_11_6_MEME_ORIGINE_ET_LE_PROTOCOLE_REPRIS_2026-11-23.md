L3 · chantier classeur · ㉑ undecies · 23/11, matin : « même origine » est dans la règle 6 et prouvée, aux deux endroits
du code qui comparent. Le protocole est repris : la mesure du matin le retrouve exactement là où on l'a laissé le 22/11.
Rien n'est écrit, ni en base ni chez Hektor, et rien n'est poussé.

# Ton mot du 23/11 (9) : « même origine » dans la règle 6, puis le protocole repris

Carnet : § 20.21.

## 1. La règle 6 complétée : « identiques » veut dire aussi « même origine »

**Elle est écrite partout où elle vit :**
- dans le plan, à la règle 6 de « LES CINQ RÈGLES » ;
- dans la mémoire ;
- dans le patch des orphelines (`temps13_orphelines_mises_de_cote_2026-11-22.py`), à ses deux endroits qui comparent : la
  comparaison qui fabrique la liste, et la garde SQL qui la refait au moment de jouer ;
- dans ma mesure des 26.

**La preuve.**
- **Les essais hors ligne : 7 sur 7.** Ils contiennent le témoin inverse de ton angle mort : une vraie saisie face à notre
  copie, avec le même négociateur et le même pourcentage, te remonte maintenant au lieu d'être mise de côté. L'inverse
  aussi (notre copie face à une saisie) te remonte. Une seule part d'une autre origine fait remonter le dossier entier. Et
  des blancs ou une casse différente ne font pas une autre origine.
- **Sur l'état vivant, en lecture seule, rien ne change : c'est gratuit, comme tu le disais.** Il y a 12 dossiers
  identiques (24 parts), 1 qui te remonte (27135 → 27133), et 0 sans transaction.
- **La garde SQL, rejouée en lecture seule**, trouve 3670 / 3669 égales et 27135 / 27133 différentes.

Les fichiers d'essai du 22/11 ne sont pas refaits, puisque ce patch-là ne se joue jamais. Celui qui se jouera sera
refabriqué après le protocole, et il portera la même origine.

## 2. Le protocole repris : la mesure du matin, dans son ordre écrit

- **L'image** : 4 798 lignes du Sheet, 31 368 pièces au registre, 12 820 liens au gel.
- **Le mouvement, dit d'abord : la nuit n'a rien déplacé.** Il y a 0 ligne, 0 pièce et 0 lien qui bougent.
  - Ce zéro a son témoin positif : sur une copie de l'image, j'ai faussé une case du Sheet, un champ du registre et un
    lien du gel, et la mesure attrape les trois.
- **Le passage 23 boucle** : 4 573 lignes tranchées + 225 en attente = 4 798.
  - Ses 19 écarts de témoins sont les mêmes qu'aux passages 20 et 22, ligne à ligne : aucun nouveau, aucun disparu.
  - Ils sont expliqués depuis le passage 7.
- **La comparaison 22 → 23 : 0 verdict change.**
- **La sentinelle des 2 560 : 0 changement depuis le passage 22**, et l'empreinte de la table est la même.
- **Les portes, avec les rejeux A, B et E :**
  - le rejeu A redonne l'image ;
  - la règle C5 aux portes retrouve exactement ses 4 lignes ;
  - 4 573 lignes sur 4 573 sont justes à l'arrivée, avec la même étiquette ;
  - aucune pièce ne bouge hors des biens tranchés ;
  - la porte de chaque ligne n'a changé sur aucune ligne depuis le passage 22.
- **Les lignes en attente gardent leur numéro** : 153 le gardent, 69 sont sans pièce, et 3 changent de numéro. Ce sont
  les mêmes 3 qu'au passage 22 (3900, 3990, 4005), déjà tranchées par la règle du plus ancien. La case A est vide sur les
  225 lignes, et les 35 lignes des 2 560 gardent toutes leur numéro.

**Une faute d'ordre de ma part, sans effet.** J'ai lancé le rejeu E avant le B, alors que le mode d'emploi dit A, B, E,
puis les comptes. Le brouillon des coupes n'a pas changé, mais il a fallu refaire les comptes après B. Il manquait aussi
au cache un rejeu que le contrôle des lignes en attente demande : je l'ai calculé.

## 3. La suite écrite : le reste à vider

Il reste 225 lignes en attente. On les traite motif par motif, avec une règle par motif mesurée par variante, comme pour
P1, R7a et R7b. Les motifs, avec leur nombre de lignes :
- **le verrou de la pièce plus petite : 69** ;
- **ses pièces à part : 29** ;
- **aucune pièce prouvée : 28** ;
- **plusieurs biens : 23** ;
- **copie seule : 23** ;
- **bien sans pièce : 23** ;
- **sans bien : 11** ;
- **deux lignes dans un dossier : 10** ;
- **pièce supprimée et figée : 6** ;
- **à ta décision (le bien 39845) : 3**.

**Ma recommandation pour commencer : le motif « bien sans pièce » (23 lignes), avec « sans bien » (11 lignes).**
- Ce sont de pures mesures : ces lignes nomment un bien dont nous n'avons aucune pièce, ou ne nomment aucun bien.
- Elles peuvent cacher une seule cause commune, par exemple des biens vendus ou clos qui ne sont plus dans le dossier
  « current », un piège que le projet connaît déjà.
- Le verrou (69 lignes) est plus gros, mais c'est ta règle permanente. Le desserrer demande une règle plus étroite que
  R4, que le témoin DEBARD a déjà refusée.

## Ce qui attend ta décision

1. **Par quel motif je commence le reste à vider** : « bien sans pièce » et « sans bien » (ma recommandation), le verrou,
   ou un autre ?
