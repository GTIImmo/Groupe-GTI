# DÉCISIONS CHAMP PAR CHAMP — LES 38 COLONNES DU CLASSEUR

**02/11/2026.** Revue menée avec Frédéric, colonne par colonne, **avant le
rattrapage**. Sa consigne : « champ par champ on va décider et mémoriser le
choix avant le rattrapage ».

⛔ **CE FICHIER EST LA SOURCE DE VÉRITÉ DES DÉCISIONS.** La table
`app_champ_propriete` sera remplie à partir d'ici, pas l'inverse. Tant qu'une
colonne est marquée ⬜, **rien ne s'écrit pour elle**.

---

## § 1. L'ÉTAT DE LA REVUE

```
TRANCHEES          6 colonnes   I J K L M N
EN ATTENTE DE LUI  1 colonne    Q  (audit fait, question reposee)
RESTE A VOIR      31 colonnes
                 -------------
                  38 colonnes
```

---

## § 2. ⭐ LES DÉCISIONS PRISES — LOT 1, LA RÉPARTITION ET LA PAIE

### ✅ I — Négociateur 1 · **LE CLASSEUR FAIT FOI**

```
decision        le classeur fait foi SUR LES 432 ECARTS
prise le        02/11/2026, par Frederic
sur conflit     ecraser (le classeur gagne)
```

**Ce qu'il savait en décidant** : 4 774 cases remplies au classeur, 99 noms
distincts, 432 écarts. Dans 213 de ces 432, **c'est nous qui ne savons pas**
(91 « cet utilisateur a été supprimé », 122 « Groupe GTI » c'est-à-dire
l'agence au lieu de la personne). Les **219 autres désignent deux personnes
différentes**, et il a choisi de les écraser aussi, au-delà de ma
recommandation qui proposait de les lister.

⛔ **PRÉALABLES OBLIGATOIRES, non optionnels** :
```
. les 14 anciens negociateurs CREES dans l'annuaire d'abord
  (sinon 213 cases pointent vers un negociateur qui n'existe pas chez nous)
. la table d'ALIAS : GIRAUD = Aline VALETTE (68) · ALVES MENDES = Lucie
  DECHANDON (178) -- sans elle on ajoute la meme personne deux fois et on
  coupe sa commission en deux, sur 282 cases
. « meilleursagents », « GTI », « DENOPCE 1/2 » EXCLUS -- ce ne sont pas des
  personnes (meilleursagents : 17 fois sur 17 en negociateur 2, c'est un
  apporteur)
. les 30 dossiers « notre nom est etranger aux deux » ECARTES
```

### ✅ K et M — Négociateurs 2 et 3 · **LE CLASSEUR FAIT FOI PARTOUT**

```
decision        le classeur fait foi PARTOUT
prise le        02/11/2026, par Frederic
sur conflit     ecraser (le classeur gagne)
```

**Ce qu'il savait en décidant** : le classeur porte **687** seconds
négociateurs et **13** troisièmes ; nous portons **209** valeurs et **15**
lignes de rang supérieur à 1. Sur les 374 écarts, 117 sont des cases où nous
ne savons pas et 257 désignent deux personnes. Le risque de la liste blanche
lui a été dit : il a tranché quand même.

⚠⚠ **UNE PRÉCISION QUE JE N'AI PAS ENCORE SA CONFIRMATION** — et elle compte :
```
« faire foi » s'applique a une VALEUR, pas a une ABSENCE. J'applique donc :
le classeur gagne PARTOUT OU IL PORTE QUELQUE CHOSE, et la ou il est VIDE
nous gardons ce que nous avons.
Sinon ses 687 valeurs effaceraient nos 209 sur les lignes ou il n'a rien
ecrit -- une destruction qu'aucune source ne demande.
⬜ A LUI CONFIRMER. S'il veut aussi vider nos cases quand le classeur est
   vide, il le dira et je corrigerai cette ligne.
```

### ✅ J, L, N — les trois Pourcentages · **LE CLASSEUR PARTOUT, SANS EXCEPTION**

```
decision        le classeur fait foi PARTOUT, SANS EXCEPTION
prise le        02/11/2026, par Frederic
sur conflit     ecraser (le classeur gagne), y compris sur nos origines
                « hektor » (501 lignes) et « saisie » (20 lignes)
```

**Ce qu'il savait en décidant** :
```
⭐⭐⭐ LA SOMME DES TROIS POURCENTAGES FAIT EXACTEMENT 100 dans 4 768 cas sur
     4 780, soit 99,75 %. C'est la colonne la MIEUX TENUE des 38.
     Les 5 anomalies : 2 lignes a 50, 2 a 200, 1 a 150. Plus 7 lignes sans
     pourcentage 1.
⭐  Les pourcentages sont LISIBLES A 100 % : 4 773 / 4 773.
⛔  En face, app_affaire_repartition porte 16 106 lignes dont 15 581
     marquees « hektor_partage_suppose » (96 %) -- un calcul par defaut, pas
     une donnee. Et 15 lignes seulement de rang > 1.
     Le classeur en porte 687 + 13.
```
Il a choisi d'écraser **aussi** nos 501 lignes d'origine « hektor » et nos 20
« saisie », au-delà de ma recommandation qui proposait de les protéger.

⚠ **PIÈGE DE FORMAT, à coder** : `Pourcentage 3` porte **« 12,5 »** avec une
**virgule**. Une conversion naïve rend 125, ou zéro. Un seul cas, mais il
suffit à fausser une paie.

---

## § 3. ⬜ EN ATTENTE — Q, Charge Commission

**AUDIT FAIT le 02/11, à sa demande** (« il va falloir auditer avant car il y a
la charge de la commission ou similaire déjà dans mon projet »). Il avait
raison, et voici ce qui existe :

```
. apps/hektor-v1/src/App.tsx:5735 -- un menu « Charge des honoraires »
  (Acquereur / Mandant), champ honorairesCharge
  ⛔ MAIS c'est un champ du BROUILLON DE DOCUMENT DE MANDAT, pas une donnee
     d'affaire : il sert a cocher la case du PDF (« la totalite des honoraires
     sera a la charge du : MANDANT / ACQUEREUR », App.tsx:4803)
. ⛔ IL N'EST PAS PERSISTE : aucune colonne en base, rien dans supabase/
. ⛔ SA VALEUR EST UN DEFAUT AUTOMATIQUE :
     honorairesCharge: rawHonoraires ? 'acquereur' : ''
     -- des qu'il y a des honoraires on ecrit « acquereur », personne ne l'a dit
. ⛔ HEKTOR NE PORTE RIEN : les 1 847 payloads du registre contenant le mot
     ont ete deballes, ZERO cle de charge
. charge_commission_app : la colonne existe, VIDE A 100 % (0 / 12 413)
. le classeur : 955 lignes -- Vendeur 894, Acquereur 61
```

⚠ **DEUX PIÈGES à traiter si on remplit** :
```
① LE VOCABULAIRE : le classeur dit « Vendeur », l'app dit « mandant ».
  Meme notion, deux mots -- et notre « Mandant » est POLLUE depuis le 17/07
  (l'acheteur y est range a tort).
② DEUX OBJETS : la charge du MANDAT (signee au depart) n'est pas forcement
  celle de la VENTE (ce qui s'est passe).
```

---

## § 4. ⬜ LES 31 COLONNES QUI RESTENT À TRANCHER

```
LOT 2  LE FINANCIER        P Commission TTC · AF Prix · AA Numero de facture
                           (+ Q, reposee)
LOT 3  LES DATES           S Offre Achat · T Compromis · W Vente Fixee
                           · Y Vente Reglee
LOT 4  DATES ET ETAT       V Vente Prevue · Z Annulee · R Etat Actuel
                           · U Signe + X Signee
LOT 5  LES IDENTITES       AB Acquereur · AD Vendeur · O Notaire · H Agence
LOT 6  LE BIEN             C Mandat · B product_ref · D Nature · AG Ville
                           · AC Adresse Acquereur · AE Adresse Vendeur
LOT 7  NOTES ET TECHNIQUE  F En attente de · G COMMENTAIRES · AH Avis a
                           envoyer · AI Commentaire Avis · AJ Avis envoye
                           · AK Divers · E Lien CRM · A affair_uuid
                           · AL ID Unique
```

---

## § 5. ⛔ DEUX RÉSERVES QUI VALENT POUR TOUTE LA REVUE

### ⛔ L'apparieur ne lit que la plage `A1:AL6000`

Les 38 colonnes vont **exactement de A à AL**. Donc **toute colonne ajoutée à
droite de AL est invisible, en silence**. Réserve écrite le 31/10, jamais
corrigée. ⬜ **Relire jusqu'à `BZ`** — deux caractères à changer, mais un appel
à l'API Google, donc son accord.

### ⚠ Les chiffres d'écart viennent du rapport du 29/10

Le classeur lui-même est mesuré sur le cache du **01/11 18:47** (4 780 lignes,
38 colonnes), sans appel réseau. Les verdicts d'écart, eux, viennent de
`notice/A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-10-29.csv`. Le gel a gagné 2 lignes
depuis. ⛔ Le rapport n'a **pas** été relancé : son script écrit par-dessus les
fichiers du 29/10 (noms de sortie en dur) et demande un login Google.
