# Données fausses chez Hektor, trouvées en passant

> **Ce n'est plus du classeur.** Cette liste range les données que nos mesures trouvent fausses **chez Hektor** (donc dans
> notre miroir), quand elles ne changent aucun verdict du chantier en cours. Chaque entrée dit où est la donnée, pourquoi
> elle est fausse, la valeur probable, ce qu'elle touche, et qui l'a vue.
> ⛔ **Rien n'est corrigé d'ici.** On n'écrit pas chez Hektor sans l'accord de Frédéric. Le remède est une correction de
> saisie dans Hektor, par l'agence ; la nuit la ramènera alors toute seule.

---

## 1. Le compromis 16806 : un net vendeur avec un zéro de trop

*Trouvé le 23/11/2026 par la mesure de l'hypothèse des avoirs (chantier classeur, carnet § 20.29). Nommé à Frédéric.*

- **Où** : le compromis Hektor n° 14573, sur le bien 35538 (mandat 17645). Il est actif et daté du 14/05/2025. Dans notre
  registre, c'est la pièce `app_affaire_ledger` 16806, lue chez Hektor la nuit du 23/11.
- **La donnée fausse** : `prix_net_vendeur = 1 650 000`. Le montant est de 175 000 € et les honoraires d'entrée de
  10 000 €.
- **Pourquoi elle est fausse** : le net vendeur devrait être le montant moins les honoraires, soit 175 000 − 10 000 =
  **165 000 €**. La valeur saisie est exactement dix fois plus grande. La vente du même dossier (pièce 16808, 03/09/2025)
  porte bien 175 000 € et 10 000 € d'honoraires, et la ligne du classeur 75EZY5GJ dit Prix 175 000 €, Commission 10 000 €.
- **Ce que ça touche** : tout calcul qui déduit les honoraires du net vendeur donne **-1 475 000 €**. Dans le chantier
  classeur, la ligne 75EZY5GJ est tranchée par la date, et **son verdict n'en dépend pas**. Ailleurs, tout ce qui lirait ce
  net vendeur (une somme, une moyenne, un export) serait faux d'environ 1,5 M€.
- **Sa famille, mesurée** : sur les 10 637 compromis qui portent les trois montants, 10 125 tombent juste (montant = net
  vendeur + honoraires). Un seul écart s'explique par un facteur 10 : celui-ci. **C'est un cas isolé, pas une famille.**
- **Le remède** : corriger le net vendeur du compromis 14573 dans Hektor (165 000 €).

## 2. À juger, pas encore dit faux

- **Le compromis 7176** (Hektor n° 21797, bien 14674, mandat 17350, annulé, sans date « 0000-00-00 ») porte trois montants
  qui ne tombent pas juste : un montant de 100 000 €, un net vendeur de 103 000 € et des honoraires d'entrée de 7 000 €.
  C'est l'autre compromis aux honoraires calculés négatifs (-3 000 €), celui de la ligne BR8ZTN5F. Ses honoraires d'entrée,
  7 000 €, sont égaux à la Commission de BR8ZTN5F. Aucun facteur simple n'explique l'écart. Ce n'est donc pas une faute
  évidente, et je ne la dis pas fausse.
- **Le constat d'ensemble** : 512 compromis sur 10 637 ont un montant différent du net vendeur plus les honoraires. Pour
  510 d'entre eux, l'écart est positif. Ce n'est pas jugé : les honoraires de sortie, la TVA ou une renégociation peuvent
  l'expliquer. C'est un sujet à part, à ouvrir seulement s'il le demande.
