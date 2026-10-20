# AUDIT — LA RÉPARTITION DES HONORAIRES : QU'AVONS-NOUS VRAIMENT RAPATRIÉ ?

**19/10/2026.** Demandé par Frédéric : *« pour moi nous avions récupéré la répartition
des honoraires chez Hektor… nous avions bien rapatrié l'histo d'Hektor, cherche vraiment
loin si nécessaire »* — après que j'ai écrit, à tort, que le classeur *« porte la
répartition commerciale, que nous n'avons pas »*.

**Audit en LECTURE SEULE. Aucune écriture, aucun appel à Hektor.**

---

## 0. VERDICT — IL A RAISON, ET LA RÉALITÉ EST MEILLEURE QUE SON SOUVENIR

| ce qu'il affirmait | mesure | verdict |
|---|---|---|
| on a rapatrié l'histo d'Hektor | `app_affaire_console`, **18 524 lignes** | ✅ vrai |
| on a la répartition par négociateur | **16 210 lignes-personne** | ✅ vrai |
| le worker ne la synchronise pas | lecture faite par un script, pas par le worker | ✅ vrai |

⭐ **Et il sous-estimait** : la matière porte **le montant en EUROS par personne**
*(16 199 sur 16 210, soit 99 %)*, pas seulement un pourcentage.

⭐ **La couverture est complète ET FRAÎCHE** — ce n'est pas un vieux stock :

```
ventes du registre   9 264   ·   sans aucune lecture de console :  1
lu_le                du 2026-09-10 au 2026-10-18   <- hier

2026  97 %   2025  84 %   2024  98 %   2023  97 %
2022  97 %   2021  98 %   2020  97 %   2019  99 %
```

---

## 1. LA CHAÎNE COMPLÈTE, DE HEKTOR À L'ÉCRAN

```
page « commissions » de la console Hektor
   |
   |  Console/extract_hektor_compromis_console.js   (le lecteur)
   |  phase2/sync/sync_hektor_compromis_console.py  (le pilote)
   v
app_affaire_console .intervenants_json     8 104 affaires · 16 210 personnes
   |                 unites_entree_percent    316 seulement
   |                 unites_sortie_percent    316 seulement
   |
   |  phase2/sync/repartition_commission.py  (la conversion, 15/09)
   |  remplace phase2/identite/convertir_repartition_commission.py
   v
app_affaire_repartition                   16 062 lignes · 8 031 chaînes
   |
   v
le registre des transactions (App.tsx)
```

### Ce que porte une ligne brute d'`intervenants_json`

```json
{"id":"52","nom":"Vivien BERGER","sens":"entree","type":"NEGO",
 "montant":"1875","percent":"50","ca_montant":"1875","ca_percent":"50",
 "typeCommission":"Entree"}
```

Clés présentes sur les 16 210 : `id` · `nom` · `sens` · **`montant`** · `percent` ·
`ca_montant` · `ca_percent` · `typeCommission` · `type` (NEGO 14 844, AGENCE 444) ·
`deletedUser` (1 308).

---

## 2. ⚠ CE QUE LA CONVERSION A PERDU EN CHEMIN

### ① Les euros ne sont pas dans la table

`app_affaire_repartition` n'a **pas de colonne montant** : elle garde `pourcentage` et
rien d'autre. Les 16 199 montants en euros restent **dans le blob brut**, que le front
ne lit pas. Ils ne sont pas détruits — ils sont **hors de portée de l'écran**.

### ② L'étiquette « supposé » dit autre chose que ce qu'on croit

`origine = 'hektor_partage_suppose'` sur **15 578 lignes (97 %)**. On croit lire
*« on a inventé la répartition »*. **Faux.** Le code
(`phase2/sync/repartition_commission.py:196-210`) ne suppose qu'une chose : **les unités
de coupe**, `unites_entree_percent` / `unites_sortie_percent`, renseignées **316 fois
sur 8 104**. Faute de les avoir, il pose 50/50 — *« la valeur que Hektor rend partout
ailleurs, juste dans 205 cas sur 209 là où elle est vérifiable »*.

➡ **Les personnes et leurs parts, elles, viennent bien de Hektor.** L'étiquette porte sur
la coupe entrée/sortie, pas sur les noms.

### ③ Les compromis ne sont pas couverts

```
vente       console 9 268   avec intervenants 7 946   (86 %)
compromis   console 9 255   avec intervenants   158   ( 2 %)
offre       console     1   avec intervenants     0
```

Normal : la page des commissions se lit sur une **vente**. Mais ça veut dire qu'une
affaire encore au compromis **n'a pas sa répartition**.

---

## 3. ⭐⭐ LE SEUL VRAI MANQUE : LE SECOND NÉGOCIATEUR

Le classeur nomme **deux ou trois négociateurs sur 683 lignes** (670 à 2, 13 à 3), avec
des parts réelles : 100 · 75/25 · 50/50 · 12,5 · 40 · 30 · 90.

**Chez Hektor, sur les 649 de ces lignes qui sont appariées :**

| | | |
|---|---|---|
| Hektor n'en connaît **qu'une** | **525** | 80 % |
| Hektor n'a **aucun** intervenant | **109** | 16 % |
| Hektor connaît **aussi les deux** | **15** | 2 % |

```
mandat 17376   classeur BRAVARD + HERITIER     Hektor : BRAVARD Christine (une seule)
mandat 16221   classeur CROIZIER + JEOFFROY    Hektor : CROIZIER Tatiana  (une seule)
mandat 17622   classeur FARGET + JORAND        Hektor : JORAND Frédérique (une seule)
```

⚠ **Ce n'est pas un défaut de notre rapatriement.** Le formulaire Hektor sait recevoir
plusieurs personnes par côté — `intervenantsEntree[115][...]`, **sept champs par
personne** *(relevé du 12/09, `Console/releve_commissions_vente.js`)* — et notre lecteur
sait les lire *(5 affaires à `entree=2` existent, et 19 affaires ont bien 2 personnes
distinctes)*.

➡ **Personne ne saisit le partage inter-négociateurs dans Hektor.** Il se tient
**dans le classeur**, et nulle part ailleurs.

---

## 4. CE QUE ÇA CHANGE POUR LA PASSERELLE

| | source de vérité | pourquoi |
|---|---|---|
| **qui est le négociateur principal** | ✅ **Hektor** *(déjà chez nous)* | 97-99 % de couverture, frais d'hier, avec les euros |
| **le montant d'honoraires par personne** | ✅ **Hektor** *(déjà chez nous)* | 16 199 montants en euros |
| **le partage entre DEUX négociateurs** | ⛔ **le classeur, et lui seul** | 525 cas sur 649 que Hektor ignore |
| **une affaire encore au compromis** | ⛔ **le classeur** | 158 sur 9 255 chez Hektor |

### Les trois travaux qui en découlent — **aucun n'est lancé**

```
A. REMONTER LES EUROS           ajouter montant (et ca_montant) a
                                app_affaire_repartition : la matiere est deja
                                la, c'est une relecture du blob, zero appel Hektor.
B. CORRIGER L'ETIQUETTE         'hektor_partage_suppose' fait croire que les NOMS
                                sont supposes. Seules les UNITES le sont.
                                Un nom d'origine plus juste, ou une colonne a part.
C. ABSORBER LE 2e NEGOCIATEUR   depuis le classeur, origine = 'classeur',
                                sans toucher aux lignes 'hektor' et 'saisie'.
                                525 affaires concernees.
```

⚠ **Et les 921 « négociateurs différents » du croisement ne se recopient pas en
silence** : un changement de nom peut être une reprise de dossier légitime.

---

## 5. CE QUE J'AVAIS ÉCRIT DE FAUX

| ma phrase | la vérité |
|---|---|
| *« il porte la répartition commerciale, que nous n'avons pas »* | **faux** : `app_affaire_repartition`, 16 062 lignes |
| *« 16 054 couples sur 16 058 à UN négociateur »* | **mesure mal posée** : j'ai compté par *(chaîne, côté)*, où il ne peut y en avoir qu'un. Par chaîne : 8 015 à une personne, 16 à deux |
| *« rempli à 97 % d'une supposition »* | **à moitié faux** : la supposition porte sur les **unités de coupe**, pas sur les personnes |

➡ Leçon : **avant de dire « nous n'avons pas », chercher la table ET son alimentation.**
Le nom `app_affaire_repartition` était dans la base, et le mot « répartition » dans
quatre scripts.
