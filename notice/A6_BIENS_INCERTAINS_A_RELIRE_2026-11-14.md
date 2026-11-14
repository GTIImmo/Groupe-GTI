# LES BIENS INCERTAINS DU CLASSEUR — à relire

> **39 lignes.** Produit le 14/11/2026 par `phase2/checks/liste_mandats_prefixes_a_relire.py`.

## Pourquoi je te demande de les relire

Le numéro de mandat écrit sur ces lignes **n'existe pas chez nous** — c'est le
chiffre ajouté devant. Faute de mandat, notre programme a cherché le bien
**par les noms de l'acheteur et du vendeur**, ce qui est moins sûr.

Or ces lignes disent **qui a gagné la commission**. Si le bien retenu n'est pas
le bon, c'est le mauvais négociateur qui est crédité.

J'ai épuisé les mesures : enlever le chiffre de devant donne un numéro à
4 chiffres, et **95 % des numéros à 4 chiffres existent déjà** chez nous. Donc
« ce numéro existe » ne prouve pas que c'est le bon bien. L'information qui
manque est **humaine** : reconnaître le bien.

## Comment répondre

Pour chaque ligne, une seule question : **le bien retenu est-il le bon ?**

- **oui** → il n'y a rien à faire, la commission est bien attribuée ;
- **non** → dis-moi lequel est le bon (l'autre candidat est proposé quand il existe) ;
- **je ne sais pas** → je retire la répartition de ce dossier, et personne n'est
  crédité à tort.

Tu peux répondre en vrac, par numéro de ligne : « 3 oui, 7 non, 12 sais pas ».

## Ce que j'ai déjà pu trancher sans toi

```
   4 ligne(s)  CONFIRMEES par le prix -- rien a verifier
   6 ligne(s)  prix comparable, a confirmer d un coup d oeil
  29 ligne(s)  AUCUNE verification possible -- c est la que j ai besoin de toi
```

Le prix est ma seule vérification **indépendante** : notre programme a
choisi le bien par les noms, donc revérifier les noms ne prouverait rien.
Le prix, lui, n'entre pas dans ce choix — s'il correspond, c'est une
confirmation qui vient d'ailleurs.


## ✅ Déjà confirmées par le prix — tu peux les survoler

*Le prix du classeur est exactement celui de la transaction retenue.*

### 1. mandat écrit **11935**  →  sans le chiffre : **1935**

**Le classeur dit :**

```
  acheteur  LAFFONT
  vendeur   VIVIER VASSY
  ville     - Annonay -
  prix      75000          commission  5000
  etat      Vente réglée   offre       08/07/2020
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 34645    mandat —        
     compromis 2020-07-27   acheteur : Cédric LAFFONT
     vendeur : Suzanne VASSY / Jacques VIVIER / Mr./Mme
  annonce 34645    mandat —        
     offre 2020-07-08   acheteur : Cédric LAFFONT
  annonce 34645    mandat —        
     vente 2020-11-09   acheteur : Cédric LAFFONT
     vendeur : Suzanne VASSY / Jacques VIVIER / Mr./Mme
```

**L'autre candidat** *(le mandat 1935, une fois le chiffre enlevé)* **:**

```
  annonce 1153     Saint-Étienne
  annonce 10738    Saint-Bonnet-le-Bourg
  annonce 1153     Saint-Étienne
```

✅ **Le prix confirme** : le prix du classeur est **celui de la transaction** (75000 €)

**Crédité aujourd'hui :** Pierrick MARTINEZ 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 2. mandat écrit **15512**  →  sans le chiffre : **5512**

**Le classeur dit :**

```
  acheteur  BOYER LEPIECK
  vendeur   SOUCHE LAFARGE
  ville     - Issoire -
  prix      160000         commission  10000
  etat      Vente réglée   offre       14 février24
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 12414    mandat 16127    Le Broc
     compromis 2024-03-07   acheteur : Mr./Mme Anais et Maxime AUZARY ET LAMBELIN
     vendeur : M. Jean-marc LAFARGE / Isabelle SOUCHE / Mr./Mme
  annonce 12414    mandat 16127    Le Broc
     offre 2024-02-14   acheteur : Mr./Mme Jeremy et Julie BOYER - LEPIECK
  annonce 12414    mandat 16127    Le Broc
     vente 2024-05-25   acheteur : Mr./Mme Jeremy et Julie BOYER - LEPIECK
     vendeur : M. Jean-marc LAFARGE / Isabelle SOUCHE / Mr./Mme
```

**L'autre candidat** *(le mandat 5512, une fois le chiffre enlevé)* **:**

```
  annonce 29030    La Tourette
  annonce 29030    La Tourette
```

✅ **Le prix confirme** : le prix du classeur est **celui de la transaction** (160000 €)

**Crédité aujourd'hui :** LAURE CAVARD 25.0% · LAURE CAVARD 50.0% · VIVIEN BERGER 25.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 3. mandat écrit **218611**  →  sans le chiffre : **18611**

**Le classeur dit :**

```
  acheteur  M. BARRIOL Anthony
  vendeur   Mme GUICHARD Christine
  ville     Saint-Maurice-de-Lignon
  prix      134000         commission  9000
  etat      Vente fixée    offre       13/07/2026
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 58930    mandat 18611    Saint-Maurice-de-Lignon
     offre 2026-07-15   acheteur : M. Anthony BARRIOL
  annonce 58930    mandat 18611    Saint-Maurice-de-Lignon
     compromis 2026-08-24   acheteur : M. Anthony BARRIOL
     vendeur : Mme. Christine GUICHARD épouse GONIN
```

**L'autre candidat** *(le mandat 18611, une fois le chiffre enlevé)* **:**

```
  annonce 58930    Saint-Maurice-de-Lignon
  annonce 58930    Saint-Maurice-de-Lignon
```

✅ **Le prix confirme** : le prix du classeur est **celui de la transaction** (134000 €)

**Crédité aujourd'hui :** Nicolas BOUCHET 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 4. mandat écrit **24247**  →  sans le chiffre : **4247**

**Le classeur dit :**

```
  acheteur  SCI PARADISUS
  vendeur   CHAPUIS
  ville     NON TROUVÉ
  prix      15000          commission  1800
  etat      Annulée        offre       18 décembre20
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 43787    mandat 4247     Saint-Bonnet-le-Château
     offre 2020-12-18   acheteur : M. Maxime Corgié Masson SCI PARADISUS VARADERO
  annonce 43787    mandat 4247     Saint-Bonnet-le-Château
     compromis 2021-01-28   acheteur : M. Maxime Corgié Masson SCI PARADISUS VARADERO
     vendeur : SAS CHAPUIS ARMES - DAVID CHAPUIS
```

**L'autre candidat** *(le mandat 4247, une fois le chiffre enlevé)* **:**

```
  annonce 48185    La Chaise-Dieu
  annonce 49968    Montbrison
  annonce 43787    Saint-Bonnet-le-Château
```

✅ **Le prix confirme** : le prix du classeur est **celui de la transaction** (15000 €)

**Crédité aujourd'hui :** CLAUDIE FERNANDEZ 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---

## Prix comparable — un coup d'œil suffit

*L'écart de prix correspond à une négociation ordinaire. Si l'acheteur
et le vendeur te parlent, c'est bon.*

### 5. mandat écrit **15132**  →  sans le chiffre : **5132**

**Le classeur dit :**

```
  acheteur  CORDONNIER
  vendeur   LE PRADO
  ville     - Issoire -
  prix      155005         commission  9729
  etat      Vente réglée   offre       16 décembre22
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 12440    mandat 15306    Lamontgie
     compromis 2023-01-13   acheteur : Amandine CORDONNIER
     vendeur : Clara LE PRADO / Mr./Mme
  annonce 12440    mandat 15306    Lamontgie
     offre 2022-12-16   acheteur : Amandine CORDONNIER
  annonce 12440    mandat 15306    Lamontgie
     vente 2023-02-27   acheteur : Amandine CORDONNIER
     vendeur : Clara LE PRADO / Mr./Mme
```

**L'autre candidat** *(le mandat 5132, une fois le chiffre enlevé)* **:**

```
  annonce 21504    Saint-Étienne
  annonce 21504    Saint-Étienne
```

Prix comparable : prix affiché 155005 € contre 150729 € vendu (-2.8 %) — une négociation ordinaire

**Crédité aujourd'hui :** LAURE CAVARD 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 6. mandat écrit **15512**  →  sans le chiffre : **5512**

**Le classeur dit :**

```
  acheteur  AUZARY LAMBELIN
  vendeur   SOUCHE LAFARGE
  ville     - Issoire -
  prix      187075         commission  10000
  etat      Annulée        offre       26/06/2023
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 12414    mandat 16127    Le Broc
     compromis 2023-07-25   acheteur : Mr./Mme Anais et Maxime AUZARY ET LAMBELIN
     vendeur : M. Jean-marc LAFARGE / Isabelle SOUCHE / Mr./Mme
  annonce 12414    mandat 16127    Le Broc
     offre 2023-06-26   acheteur : Mr./Mme Anais et Maxime AUZARY ET LAMBELIN
```

**L'autre candidat** *(le mandat 5512, une fois le chiffre enlevé)* **:**

```
  annonce 29030    La Tourette
  annonce 29030    La Tourette
```

⚠ **Attention** : prix affiché 187075 € contre 160000 € vendu (-14.5 %) — l'écart est **gros**

**Crédité aujourd'hui :** LAURE CAVARD 25.0% · LAURE CAVARD 50.0% · VIVIEN BERGER 25.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 7. mandat écrit **15823**  →  sans le chiffre : **5823**

**Le classeur dit :**

```
  acheteur  GORD DUGUET
  vendeur   MAGAND
  ville     NON TROUVÉ
  prix      249000         commission  12000
  etat      Vente réglée   offre       11 août23
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 18861    mandat 16104    Sury-le-Comtal
     compromis 2023-08-22   acheteur : Mr./Mme Romain et Floraine GORD DUGUET
     vendeur : M. Pierre MAGAND / Lucie MAGAND PALANDRE / Mr./Mme
  annonce 18861    mandat 16104    Sury-le-Comtal
     offre 2023-08-11   acheteur : Mr./Mme Romain et Floraine GORD DUGUET
  annonce 18861    mandat 16104    Sury-le-Comtal
     vente 2023-10-31   acheteur : Mr./Mme Romain et Floraine GORD DUGUET
     vendeur : M. Pierre MAGAND / Lucie MAGAND PALANDRE / Mr./Mme
```

**L'autre candidat** *(le mandat 5823, une fois le chiffre enlevé)* **:**

```
  annonce 48867    Saint-Bonnet-le-Château
  annonce 48867    Saint-Bonnet-le-Château
```

Prix comparable : prix affiché 249000 € contre 242000 € vendu (-2.8 %) — une négociation ordinaire

**Crédité aujourd'hui :** SABRINA NICOLOSI 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 8. mandat écrit **16463**  →  sans le chiffre : **6463**

**Le classeur dit :**

```
  acheteur  LIBERCIER
  vendeur   BINEAU
  ville     - Issoire -
  prix      99000          commission  6750
  etat      Vente réglée   offre       31/01/2024
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 12277    mandat 16569    Saint-Gervazy
     compromis 2024-02-13   acheteur : Lucile LIBERCIER
     vendeur : M. Alexis BINEAU / Mr./Mme
  annonce 12277    mandat 16569    Saint-Gervazy
     offre 2024-01-31   acheteur : Lucile LIBERCIER
  annonce 12277    mandat 16569    Saint-Gervazy
     vente 2024-05-28   acheteur : Lucile LIBERCIER
     vendeur : M. Alexis BINEAU / Mr./Mme
```

**L'autre candidat** *(le mandat 6463, une fois le chiffre enlevé)* **:**

```
  annonce 45377    Usson-en-Forez
  annonce 45377    Usson-en-Forez
```

Prix comparable : prix affiché 99000 € contre 93000 € vendu (-6.1 %) — une négociation ordinaire

**Crédité aujourd'hui :** LAURE CAVARD 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 9. mandat écrit **22042**  →  sans le chiffre : **2042**

**Le classeur dit :**

```
  acheteur  CUOQ
  vendeur   VINSON
  ville     NON TROUVÉ
  prix      156500         commission  8500
  etat      Annulée        offre       16/06/2017
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 42288    mandat 2042     Rosières
     compromis 2017-06-29   acheteur : Mathieu / Julie CUOQ / PLOTTON
     vendeur : Nicolas VINSON / Mr./Mme Christine GUES / Mr./Mme
  annonce 42288    mandat 2042     Rosières
     offre 2026-11-11   acheteur : Mathieu / Julie CUOQ / PLOTTON
```

**L'autre candidat** *(le mandat 2042, une fois le chiffre enlevé)* **:**

```
  annonce 20560    Saint-Germain-Laval
  annonce 13780    Rentières
  annonce 42288    Rosières
```

Prix comparable : prix affiché 156500 € contre 165000 € vendu (+5.4 %) — une négociation ordinaire

**Crédité aujourd'hui :** Nicolas BOUCHET 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 10. mandat écrit **3982**  →  sans le chiffre : **982**

**Le classeur dit :**

```
  acheteur  BILLAMBOZ
  vendeur   SENN
  ville     - Tence -
  prix      180000         commission  8000
  etat      Vente réglée   offre       2 août20
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 37307    mandat 3817     Tence
     compromis 2020-10-10   acheteur : M. Edouard BILLAMBOZ / Cathy BILLAMBOZ / Mr./Mme
     vendeur : Bernadette JARZAGUET / M. René JARZAGUET / Michèle SENN
  annonce 37307    mandat 3817     Tence
     offre 2020-08-02   acheteur : M. Edouard BILLAMBOZ
  annonce 37307    mandat 3817     Tence
     vente 2020-12-29   acheteur : M. Edouard BILLAMBOZ / Cathy BILLAMBOZ / Mr./Mme
     vendeur : Bernadette JARZAGUET / M. René JARZAGUET / Michèle SENN
```

**L'autre candidat** *(le mandat 982, une fois le chiffre enlevé)* **:**

```
  annonce 58723    Domaize
  annonce 1200     Saint-Jean-Bonnefonds
  annonce 58157    
```

Prix comparable : prix affiché 180000 € contre 166000 € vendu (-7.8 %) — une négociation ordinaire

**Crédité aujourd'hui :** JEAN VALLA 25.0% · SYLVIE TEYSSONNIER 25.0% · SYLVIE TEYSSONNIER 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---

## ⚠ Ici j'ai besoin de toi — aucune vérification possible

*Ces lignes n'ont pas de prix exploitable (leur auteur a écrit
« NON TROUVÉ »), donc je n'ai aucun moyen de confirmer le bien.*

### 11. mandat écrit **16097**  →  sans le chiffre : **6097**

**Le classeur dit :**

```
  acheteur  CHARVOLIN VALLENTIN
  vendeur   BERTIN
  ville     NON TROUVÉ
  prix      220000         commission  13000
  etat      Vente réglée   offre       1 décembre23
```

**Nous n'avons retenu aucun bien pour cette ligne.**

**L'autre candidat** *(le mandat 6097, une fois le chiffre enlevé)* **:**

```
  annonce 38692    Retournac
  annonce 38692    Retournac
```

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 12. mandat écrit **16231**  →  sans le chiffre : **6231**

**Le classeur dit :**

```
  acheteur  DELAUNAY
  vendeur   BARRI ZIEGLER
  ville     NON TROUVÉ
  prix      270000         commission  14000
  etat      Vente réglée   offre       17/11/2023
```

**Nous n'avons retenu aucun bien pour cette ligne.**

**L'autre candidat** *(le mandat 6231, une fois le chiffre enlevé)* **:**

```
  annonce 7630     Polignac
  annonce 7630     Polignac
```

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 13. mandat écrit **18967**  →  sans le chiffre : **8967**

**Le classeur dit :**

```
  acheteur  SCI ROYALE représentée par M. Martins et Mme Mareuges
  vendeur   M. LAUREMBOURLE Roger
  ville     Champeix 63320 1 route de Neschers
  prix      485000         commission  20000
  etat      Offre d'achat  offre       04/11/2026
```

**Nous n'avons retenu aucun bien pour cette ligne.**

**L'autre candidat** *(le mandat 8967, une fois le chiffre enlevé)* **:**

```
  annonce 38472    Le Pertuis
  annonce 38472    Le Pertuis
```

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 14. mandat écrit **21963**  →  sans le chiffre : **1963**

**Le classeur dit :**

```
  acheteur  STAUFFER
  vendeur   VERNET
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  500
  etat      Annulée        offre       20/01/2020
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 11927    mandat —        
     offre 2026-11-11   acheteur : Mr./Mme Gilbert Christine STAUFFER
```

**L'autre candidat** *(le mandat 1963, une fois le chiffre enlevé)* **:**

```
  annonce 26875    La Ricamarie
  annonce 26875    La Ricamarie
```

**Crédité aujourd'hui :** Joel CHAMPAGNAC 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 15. mandat écrit **27874**  →  sans le chiffre : **7874**

**Le classeur dit :**

```
  acheteur  Mme EYRAUD PAGES Elisabeth
  vendeur   Mme VIDAL Alexandra
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  7800
  etat      Vente réglée   offre       04/10/2024
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 5617     mandat 17253    Le Puy-en-Velay
     compromis 2024-10-22   acheteur : Elisabeth PAGÈS EYRAUD
     vendeur : Alexandra VIDAL / Mr./Mme
  annonce 5617     mandat 17253    Le Puy-en-Velay
     offre 2024-10-04   acheteur : Elisabeth PAGÈS EYRAUD
  annonce 5617     mandat 17253    Le Puy-en-Velay
     vente 2025-01-22   acheteur : Elisabeth PAGÈS EYRAUD
     vendeur : Alexandra VIDAL / Mr./Mme
```

**L'autre candidat** *(le mandat 7874, une fois le chiffre enlevé)* **:**

```
  annonce 38571    Montfaucon-en-Velay
  annonce 38571    Montfaucon-en-Velay
```

**Crédité aujourd'hui :** CHRISTELE GENTES 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 16. mandat écrit **31741**  →  sans le chiffre : **1741**

**Le classeur dit :**

```
  acheteur  BONNAMAIN André
  vendeur   IND. BONNAMAIN
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  2000
  etat      Vente réglée   offre       09/04/2019
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 10293    mandat 3495     Arlanc
     compromis 2019-04-09   acheteur : M. Andre BONNAMAIN
     vendeur : M. Didier BONNAMAIN / M. Andre BONNAMAIN / Marie Claude CHAPELLE
  annonce 10293    mandat 3495     Arlanc
     offre 2019-04-09   acheteur : M. Andre BONNAMAIN
  annonce 10293    mandat 3495     Arlanc
     vente 2019-06-03   acheteur : M. Andre BONNAMAIN
     vendeur : M. Didier BONNAMAIN / M. Andre BONNAMAIN / Marie Claude CHAPELLE
```

**L'autre candidat** *(le mandat 1741, une fois le chiffre enlevé)* **:**

```
  annonce 39951    Tence
  annonce 32314    Vernet-la-Varenne
  annonce 32314    Vernet-la-Varenne
```

**Crédité aujourd'hui :** Joel CHAMPAGNAC 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 17. mandat écrit **41206**  →  sans le chiffre : **1206**

**Le classeur dit :**

```
  acheteur  GERPHAGNON
  vendeur   IND. JOINAUX
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  6000
  etat      Vente réglée   offre       07/05/2019
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 24774    mandat 12560    Saint-Étienne
     compromis 2019-07-17   acheteur : M. Frédéric GERPHAGNON
     vendeur : Jacqueline JOINAUX / M. Patrick LE VAGUERESSE / Mr./Mme
  annonce 24774    mandat 12560    Saint-Étienne
     offre 2019-05-07   acheteur : franck GERPHAGNON
  annonce 24774    mandat 12560    Saint-Étienne
     vente 2019-12-27   acheteur : M. Frédéric GERPHAGNON
     vendeur : Jacqueline JOINAUX / M. Patrick LE VAGUERESSE / Mr./Mme
```

**L'autre candidat** *(le mandat 1206, une fois le chiffre enlevé)* **:**

```
  annonce 39969    Tence
  annonce 39969    Tence
```

**Crédité aujourd'hui :** MAGALI DIMARIA MARIA 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 18. mandat écrit **42490**  →  sans le chiffre : **2490**

**Le classeur dit :**

```
  acheteur  HARBOUCHE
  vendeur   TRANCHARD
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  3500
  etat      Vente réglée   offre       11/06/2018
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 16133    mandat 11540    Aurec-sur-Loire
     compromis 2018-06-14   acheteur : Sabrina HARBOUCHE
     vendeur : Paulette TRANCHARD / M. Marc TRANCHARD / Mr./Mme
  annonce 16133    mandat 11540    Aurec-sur-Loire
     offre 2018-06-12   acheteur : Sabrina HARBOUCHE
  annonce 16133    mandat 11540    Aurec-sur-Loire
     vente 2018-07-06   acheteur : Sabrina HARBOUCHE
     vendeur : Paulette TRANCHARD / M. Marc TRANCHARD / Mr./Mme
```

**L'autre candidat** *(le mandat 2490, une fois le chiffre enlevé)* **:**

```
  annonce 17776    Sainte-Sigolène
  annonce 25586    Blanzat
  annonce 7791     Ceyssac
```

**Crédité aujourd'hui :** CORENTIN DAUDET 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 19. mandat écrit **45633**  →  sans le chiffre : **5633**

**Le classeur dit :**

```
  acheteur  CHELLES
  vendeur   PELLET
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  7000
  etat      Vente réglée   offre       16/11/2019
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 54125    mandat 3479     Tours-sur-Meymont
     compromis 2020-01-25   acheteur : Claire LEMAIRE
     vendeur : Martine PELLET / Alexia GHAZAL / Anne GHAZAL
  annonce 54125    mandat 3479     Tours-sur-Meymont
     offre 2019-11-16   acheteur : Mr./Mme Frederic et Eulalie CHELLES
  annonce 54125    mandat 3479     Tours-sur-Meymont
     vente 2020-06-05   acheteur : Mr./Mme Frederic et Eulalie CHELLES
     vendeur : Martine PELLET / Alexia GHAZAL / Anne GHAZAL
```

**L'autre candidat** *(le mandat 5633, une fois le chiffre enlevé)* **:**

```
  annonce 26511    Saint-Chamond
  annonce 26511    Saint-Chamond
```

**Crédité aujourd'hui :** NICOLAS COUDERT 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 20. mandat écrit **47006**  →  sans le chiffre : **7006**

**Le classeur dit :**

```
  acheteur  VERNOIS
  vendeur   SAVINEL
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  5700
  etat      Vente réglée   offre       18/05/2018
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 10708    mandat 2118     Arlanc
     compromis 2018-06-13   acheteur : Mr./Mme VERNOIS
     vendeur : M. davier CORNILLON / M. pascal CORNILLON / M. laurent CORNILLON
  annonce 10708    mandat 2118     Arlanc
     offre 2018-05-18   acheteur : Mr./Mme VERNOIS
  annonce 10708    mandat 2118     Arlanc
     vente 2018-09-07   acheteur : Mr./Mme VERNOIS
     vendeur : M. davier CORNILLON / M. pascal CORNILLON / M. laurent CORNILLON
```

**L'autre candidat** *(le mandat 7006, une fois le chiffre enlevé)* **:**

```
  annonce 9017     Saint-Germain-Laprade
  annonce 9017     Saint-Germain-Laprade
```

**Crédité aujourd'hui :** CELINE HERITIER 50.0% · Joel CHAMPAGNAC 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 21. mandat écrit **54111**  →  sans le chiffre : **4111**

**Le classeur dit :**

```
  acheteur  ANDRE
  vendeur   PIERI
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  28000
  etat      Vente réglée   offre       14/05/2019
```

**Nous n'avons retenu aucun bien pour cette ligne.**

**L'autre candidat** *(le mandat 4111, une fois le chiffre enlevé)* **:**

```
  annonce 24513    Saint-Jean-Lachalm
  annonce 21650    Saint-Étienne
  annonce 9885     Ambert
```

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 22. mandat écrit **54311**  →  sans le chiffre : **4311**

**Le classeur dit :**

```
  acheteur  BARRIER
  vendeur   RYMARSKI
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  8250
  etat      Vente réglée   offre       29 août19
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 10153    mandat 3695     Marat
     compromis 2019-10-29   acheteur : M. Alexandre BARRIER
     vendeur : Odette RYMARSKI / Mr./Mme
  annonce 10153    mandat 3695     Marat
     offre 2019-08-29   acheteur : Lucie / Alexandre JARROUX/ BARRIER
  annonce 10153    mandat 3695     Marat
     vente 2020-01-15   acheteur : M. Alexandre BARRIER
     vendeur : Odette RYMARSKI / Mr./Mme
```

**L'autre candidat** *(le mandat 4311, une fois le chiffre enlevé)* **:**

```
  annonce 37123    Saint-Agrève
  annonce 12749    Le Breuil-sur-Couze
  annonce 46926    Saint-Pal-de-Mons
```

**Crédité aujourd'hui :** CELINE HERITIER 50.0% · Joel CHAMPAGNAC 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 23. mandat écrit **57084**  →  sans le chiffre : **7084**

**Le classeur dit :**

```
  acheteur  LEGE
  vendeur   SERVANTON REYNEBEAU
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  2000
  etat      Vente réglée   offre       24/05/2018
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 43180    mandat 2944     Queyrières
     compromis 2018-07-06   acheteur : Sarah LEGE / Manuel LEGE
     vendeur : Bernadette REYNEBEAU / Joel SERVANTON / Dominique GAUTHIER
  annonce 43180    mandat 2944     Queyrières
     offre 2018-05-24   acheteur : Sarah LEGE
  annonce 43180    mandat 2944     Queyrières
     vente 2018-11-14   acheteur : Sarah LEGE
     vendeur : Bernadette REYNEBEAU / Joel SERVANTON / Dominique GAUTHIER
```

**L'autre candidat** *(le mandat 7084, une fois le chiffre enlevé)* **:**

```
  annonce 7588     Firminy
  annonce 7588     Firminy
```

**Crédité aujourd'hui :** ARNAUD VALLA 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 24. mandat écrit **58006**  →  sans le chiffre : **8006**

**Le classeur dit :**

```
  acheteur  JOLY GUILIANI
  vendeur   SAVET
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  10000
  etat      Vente réglée   offre       20/03/2018
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 48456    mandat 10588    Saint-Nizier-de-Fornas
     compromis 2018-04-23   acheteur : Mr./Mme Pascaline et Vincent JOLY-GUILIANI
     vendeur : Mr./Mme PHILIPPE SAVET / Mr./Mme PHILIPPE SAVET
  annonce 48456    mandat 10588    Saint-Nizier-de-Fornas
     offre 2018-03-20   acheteur : Mr./Mme Pascaline et Vincent JOLY-GUILIANI
  annonce 48456    mandat 10588    Saint-Nizier-de-Fornas
     vente 2018-07-12   acheteur : M. Sébastien POUZOLS
     vendeur : Mr./Mme PHILIPPE SAVET / Mr./Mme PHILIPPE SAVET
```

**L'autre candidat** *(le mandat 8006, une fois le chiffre enlevé)* **:**

```
  annonce 45212    La Tourette
  annonce 45212    La Tourette
```

**Crédité aujourd'hui :** ERIC KUPKOWSKI 50.0% · MORGANE SANGUIN 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 25. mandat écrit **60411**  →  sans le chiffre : **411**

**Le classeur dit :**

```
  acheteur  AGRAPHIOTY LE BELLEC
  vendeur   CARRON
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  4500
  etat      Vente réglée   offre       16/10/2019
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 10207    mandat 3653     Saint-Martin-des-Olmes
     compromis 2019-12-12   acheteur : M. Pierre LE BELLEC
     vendeur : Dominique CARRON / Mr./Mme
  annonce 10207    mandat 3653     Saint-Martin-des-Olmes
     offre 2019-10-16   acheteur : Sophie AGRAPHIOTY
  annonce 10207    mandat 3653     Saint-Martin-des-Olmes
     vente 2020-03-16   acheteur : M. Pierre LE BELLEC
     vendeur : Dominique CARRON / Mr./Mme
```

**L'autre candidat** *(le mandat 411, une fois le chiffre enlevé)* **:**

```
  annonce 41555    Yssingeaux
  annonce 8704     Saint-Christophe-sur-Dolaison
  annonce 57240    
```

**Crédité aujourd'hui :** Joel CHAMPAGNAC 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 26. mandat écrit **64245**  →  sans le chiffre : **4245**

**Le classeur dit :**

```
  acheteur  MARTOS HUYSMANS
  vendeur   RAYMOND
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  4800
  etat      Vente réglée   offre       30/03/2018
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 37853    mandat 2737     Saint-Jeures
     compromis 2018-04-11   acheteur : Pierre MARTOS
     vendeur : Eliee RAYMOND / M. Antoine RAYMOND / Mr./Mme
  annonce 37853    mandat 2737     Saint-Jeures
     offre 2018-03-30   acheteur : Yvette HUYSMANS
  annonce 37853    mandat 2737     Saint-Jeures
     vente 2018-06-15   acheteur : Pierre MARTOS
     vendeur : Eliee RAYMOND / M. Antoine RAYMOND / Mr./Mme
```

**L'autre candidat** *(le mandat 4245, une fois le chiffre enlevé)* **:**

```
  annonce 49966    Montbrison
  annonce 37141    Saint-André-en-Vivarais
  annonce 9756     Ambert
```

**Crédité aujourd'hui :** JEAN VALLA 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 27. mandat écrit **66284**  →  sans le chiffre : **6284**

**Le classeur dit :**

```
  acheteur  MOUNIER BOUVIER
  vendeur   BETTON
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  6000
  etat      Vente réglée   offre       28 février18
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 35772    mandat 11788    Davézieux
     compromis 2018-03-22   acheteur : Mr./Mme Laurie & Cédric MOUNIER ET BOUVIER
     vendeur : Kevin BETTON / Stephane BETTON / Steven BETTON
  annonce 35772    mandat 11788    Davézieux
     offre 2018-02-28   acheteur : Mr./Mme Laurie & Cédric MOUNIER ET BOUVIER
  annonce 35772    mandat 11788    Davézieux
     vente 2018-11-26   acheteur : Mr./Mme Laurie & Cédric MOUNIER ET BOUVIER
     vendeur : Kevin BETTON / Stephane BETTON / Steven BETTON
```

**L'autre candidat** *(le mandat 6284, une fois le chiffre enlevé)* **:**

```
  annonce 43570    Montregard
  annonce 43570    Montregard
```

**Crédité aujourd'hui :** Pierrick MARTINEZ 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 28. mandat écrit **73058**  →  sans le chiffre : **3058**

**Le classeur dit :**

```
  acheteur  FONTVIEILLE FREYCON
  vendeur   CLOUPET
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  9700
  etat      Vente réglée   offre       7 février19
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 6908     mandat 3252     Saint-Étienne-Lardeyrol
     compromis 2019-02-19   acheteur : Marion FREYCON / Clément FONTVIEILLE
     vendeur : Isabelle CLOUPET-MARTIN / Jean Claude CLOUPET / Mr./Mme
  annonce 6908     mandat 3252     Saint-Étienne-Lardeyrol
     offre 2019-02-07   acheteur : Marion FREYCON
  annonce 6908     mandat 3252     Saint-Étienne-Lardeyrol
     vente 2019-04-26   acheteur : Marion FREYCON
     vendeur : Isabelle CLOUPET-MARTIN / Jean Claude CLOUPET / Mr./Mme
```

**L'autre candidat** *(le mandat 3058, une fois le chiffre enlevé)* **:**

```
  annonce 42079    Le Pertuis
  annonce 31328    Vergongheon
  annonce 2022     Saint-Étienne
```

**Crédité aujourd'hui :** CHRISTELE GENTES 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 29. mandat écrit **78006**  →  sans le chiffre : **8006**

**Le classeur dit :**

```
  acheteur  RICHOT
  vendeur   FOURNET-FAYARD
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  7000
  etat      Vente réglée   offre       30/04/2019
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 10264    mandat 3548     Ambert
     compromis 2019-06-14   acheteur : M. Pierre RICHOT
     vendeur : Sylvette FOURNET FAYARD / Agnes DIGONNET / M. Eric DIGONNET
  annonce 10264    mandat 3548     Ambert
     offre 2019-04-30   acheteur : M. Pierre RICHOT
  annonce 10264    mandat 3548     Ambert
     vente 2019-08-29   acheteur : M. Pierre RICHOT
     vendeur : Sylvette FOURNET FAYARD / Agnes DIGONNET / M. Eric DIGONNET
```

**L'autre candidat** *(le mandat 8006, une fois le chiffre enlevé)* **:**

```
  annonce 45212    La Tourette
  annonce 45212    La Tourette
```

**Crédité aujourd'hui :** Joel CHAMPAGNAC 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 30. mandat écrit **80761**  →  sans le chiffre : **761**

**Le classeur dit :**

```
  acheteur  PROUX
  vendeur   IND. CHELLE
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  5200
  etat      Vente réglée   offre       16/03/2020
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 10160    mandat 3858     Vertolaye
     compromis 2020-06-29   acheteur : Alisson PROUX
     vendeur : M. Patrick NOUVET / M. Eric NOUVET / Madeleine NOUVET
  annonce 10160    mandat 3858     Vertolaye
     offre 2020-03-16   acheteur : Alisson PROUX
  annonce 10160    mandat 3858     Vertolaye
     vente 2020-09-14   acheteur : PEGGY BOUSEHABA
     vendeur : M. Patrick NOUVET / M. Eric NOUVET / Madeleine NOUVET
```

**L'autre candidat** *(le mandat 761, une fois le chiffre enlevé)* **:**

```
  annonce 17106    Malvalette
  annonce 38335    Retournac
  annonce 17106    Malvalette
```

**Crédité aujourd'hui :** Joel CHAMPAGNAC 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 31. mandat écrit **91892**  →  sans le chiffre : **1892**

**Le classeur dit :**

```
  acheteur  BEYSSAC
  vendeur   BESSET ind
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  5000
  etat      Vente réglée   offre       16/04/2018
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 44770    mandat 11842    Estivareilles
     compromis 2018-05-15   acheteur : Corinne BEYSSAC / Jean marc BEYSSAC / Mr./Mme
     vendeur : Sylvie DIAS / M. Marc BESSET / Valerie BESSET
  annonce 44770    mandat 11842    Estivareilles
     offre 2018-04-16   acheteur : Corinne BEYSSAC
  annonce 44770    mandat 11842    Estivareilles
     vente 2018-07-10   acheteur : Corinne BEYSSAC / Jean marc BEYSSAC / Mr./Mme
     vendeur : Sylvie DIAS / M. Marc BESSET / Valerie BESSET
```

**L'autre candidat** *(le mandat 1892, une fois le chiffre enlevé)* **:**

```
  annonce 16327    Bas-en-Basset
  annonce 29102    Arlanc
  annonce 16327    Bas-en-Basset
```

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 32. mandat écrit **92560**  →  sans le chiffre : **2560**

**Le classeur dit :**

```
  acheteur  nan
  vendeur   nan
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  —
  etat      Annulée        offre       —
```

**Nous n'avons retenu aucun bien pour cette ligne.**

**L'autre candidat** *(le mandat 2560, une fois le chiffre enlevé)* **:**

```
  annonce 49140    Chomelix
  annonce 25082    Le Puy-en-Velay
  annonce 28962    Pont-du-Château
```

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 33. mandat écrit **96219**  →  sans le chiffre : **6219**

**Le classeur dit :**

```
  acheteur  TOURON
  vendeur   IND CHEVALIER
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  4000
  etat      Annulée        offre       12/03/2020
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 43138    mandat 3874     Yssingeaux
     compromis 2020-06-24   acheteur : Robert et Marie-Claire TOURON
     vendeur : Marie-Hélène PASCAL / Marie-Françoise COUPAT / Pierre-Marie CHEVALIER
  annonce 43138    mandat 3874     Yssingeaux
     offre 2020-03-12   acheteur : Robert et Marie-Claire TOURON
```

**L'autre candidat** *(le mandat 6219, une fois le chiffre enlevé)* **:**

```
  annonce 58526    Le Chambon-sur-Lignon
  annonce 58526    Le Chambon-sur-Lignon
```

**Crédité aujourd'hui :** ARNAUD VALLA 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 34. mandat écrit **NON TROUVÉ**

**Le classeur dit :**

```
  acheteur  SERVAJEAN
  vendeur   CHARLES
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  9000
  etat      Vente réglée   offre       14 février20
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 53875    mandat —        
     compromis 2020-04-21   acheteur : Blandine SERVAJEAN
     vendeur : Michelle CHARLES / M. Sébastien BECQUET / Mr./Mme
  annonce 53875    mandat —        
     offre 2020-02-14   acheteur : Blandine SERVAJEAN
  annonce 53875    mandat —        
     vente 2020-09-11   acheteur : Blandine SERVAJEAN
     vendeur : Michelle CHARLES / M. Sébastien BECQUET / Mr./Mme
```

**Crédité aujourd'hui :** CELINE HERITIER 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 35. mandat écrit **NON TROUVÉ**

**Le classeur dit :**

```
  acheteur  VICARD ARSAC
  vendeur   ARNAUD NOTON
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  13000
  etat      Vente réglée   offre       27/01/2020
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 24576    mandat —        
     compromis 2020-02-13   acheteur : Lucie ARSAC / M. Florian VICARD / Mr./Mme
     vendeur : LEA ESPEL / Stéphanie NOTON / Xavier ARNAUD
  annonce 24576    mandat —        
     offre 2020-01-27   acheteur : Lucie ARSAC
  annonce 24576    mandat —        
     vente 2020-06-09   acheteur : Lucie ARSAC / M. Florian VICARD / Mr./Mme
     vendeur : LEA ESPEL / Stéphanie NOTON / Xavier ARNAUD
```

**Crédité aujourd'hui :** CHRISTELE GENTES 50.0% · NICOLAS ROUANNET 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 36. mandat écrit **NON TROUVÉ**

**Le classeur dit :**

```
  acheteur  SCI MADEVA
  vendeur   IND CHAPAT
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  6000
  etat      Vente réglée   offre       22/10/2019
```

**Nous n'avons retenu aucun bien pour cette ligne.**

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 37. mandat écrit **NON TROUVÉ**

**Le classeur dit :**

```
  acheteur  LEMAIRE
  vendeur   PHILIPON
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  10000
  etat      Vente réglée   offre       14 août19
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 53907    mandat —        
     compromis 2019-09-13   acheteur : Claire LEMAIRE
     vendeur : Anne-Marie PHILIPON
  annonce 53907    mandat —        
     offre 2019-08-14   acheteur : Claire LEMAIRE
  annonce 53907    mandat —        
     vente 2019-11-28   acheteur : Claire LEMAIRE
     vendeur : Anne-Marie PHILIPON
```

**Crédité aujourd'hui :** CELINE HERITIER 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 38. mandat écrit **NON TROUVÉ**

**Le classeur dit :**

```
  acheteur  SALZET
  vendeur   IND. ROUCHON
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  7500
  etat      Vente réglée   offre       16 août19
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 15869    mandat —        
     compromis 2019-10-25   acheteur : M. Andre SALZET
     vendeur : M. Olivier BOUCHE / Juliette ROUCHON / Eva ROUCHON
  annonce 15869    mandat —        
     offre 2019-08-16   acheteur : M. Andre SALZET
  annonce 15869    mandat —        
     vente 2019-12-27   acheteur : M. Andre SALZET
     vendeur : M. Olivier BOUCHE / Juliette ROUCHON / Eva ROUCHON
```

**Crédité aujourd'hui :** LUDOVIC LEGER 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
### 39. mandat écrit **NON TROUVÉ**

**Le classeur dit :**

```
  acheteur  RESIDENCE AMPERE - BOURGIN
  vendeur   CROIX ind
  ville     NON TROUVÉ
  prix      NON TROUVÉ     commission  7500
  etat      Vente réglée   offre       26/11/2018
```

**Le bien que nous avons retenu** *(trouvé par les noms)* **:**

```
  annonce 35764    mandat —        
     compromis 2018-11-26   acheteur : Guy BOURGIN SARL RESIDENCE AMPERE
     vendeur : Dominique RANCHON / Jeanne CROIX / Mr./Mme
  annonce 35764    mandat —        
     offre 2018-11-26   acheteur : Guy BOURGIN SARL RESIDENCE AMPERE
  annonce 35764    mandat —        
     vente 2021-03-29   acheteur : Guy BOURGIN SARL RESIDENCE AMPERE
     vendeur : Dominique RANCHON / Jeanne CROIX / Mr./Mme
```

**Crédité aujourd'hui :** Pierrick MARTINEZ 50.0%

**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas

---
