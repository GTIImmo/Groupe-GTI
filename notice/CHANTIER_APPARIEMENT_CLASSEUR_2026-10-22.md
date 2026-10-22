# CHANTIER — LA CORRESPONDANCE CLASSEUR ⇄ REGISTRE

**22/10/2026.** Règle validée par Frédéric le 20/10, d'après
`notice/AUDIT_METHODE_APPARIEMENT_2026-10-20.md`.

> **La règle retenue** : deux étages *(le bien, puis l'affaire)*, une cascade **par
> précision** et non par score, et **l'exclusivité** — une chaîne prise n'est plus
> candidate.

---

## 0. OÙ ON EN EST, MESURÉ LE 22/10

```
31 088 lignes au registre · 12 186 chaines
APP_CHAINAGE_V2=1  ·  APP_CHAINAGE_SANS_DATE=1   (le cran 2 reste ETEINT)
classeur : 4 766 lignes · 4 403 appariees par l'ANCIENNE cascade (92,4 %)
```

⚠ **Les chiffres de l'audit datent du 20/10 et le parc a bougé** *(31 084 → 31 088)*.
L'étape 1 les remesure de toute façon : **aucun chiffre de ce document ne doit être
recopié sans être rejoué.**

---

## 1. LES QUATRE ÉTAPES

### Étape 1 — LA CASCADE, EN LECTURE SEULE ⏱ 1 j · **aucun risque**

Un script de mesure, `phase2/checks/apparier_classeur.py`, qui applique la règle et
**n'écrit nulle part**. Il rend :

```
le taux reel, etage par etage
quel signal a decide chaque ligne
la liste des ABSTENTIONS, nommees
la liste des lignes SANS BIEN et SANS CHAINE
```

**Les contrôles de l'étape 1 :**

| | |
|---|---|
| **le témoin inverse** | l'ancienne cascade reste appelable *(un drapeau)* et doit rendre **exactement 4 403** — sinon la comparaison ne vaut rien |
| **l'exclusivité tient** | **0 chaîne ne reçoit deux lignes** *(aujourd'hui : 21 chaînes pour 43 lignes)* |
| **le cas GENILLON** | bien 15220 : `L40 → 7500` et `L3405 → 7499`, **chacune la sienne** |
| **aucune régression** | toute ligne appariée par l'ancienne et **perdue** par la nouvelle est **nommée**, une par une |

⛔ **Le dernier contrôle est le plus important.** Un taux qui monte peut cacher des
appariements justes qu'on a perdus en route.

### Étape 2 — GELER LE RÉSULTAT ⏱ 0,5 j · *première écriture, son accord*

Une table chez nous — **rien dans le classeur** :

```
app_classeur_lien
   sheet_id_unique   TEXT    <- SA cle (4 766 valeurs distinctes, deja presentes)
   app_affaire_id    INTEGER <- NOTRE ancre : cle primaire, jamais recalculee
   app_chaine_id     INTEGER <- confort de lecture, JAMAIS une ancre
   signal            TEXT    <- « date de compromis », « etat »... qui a decide
   etage             TEXT    <- « mandat », « vendeur », « ville »...
   apparie_le        TIMESTAMP
```

⭐ **Pourquoi `app_affaire_id` et pas `app_chaine_id`** : la chaîne est une **déduction
refaite chaque nuit** ; l'affaire est une **clé primaire attribuée une fois**
*(`app_affaire_id intact. Seules les affaires nouvelles prennent un numero`)*. Le lien
survit donc à toute évolution du chaînage.

⚠ **C'est cette table qui rend tout rejouable.** Sans elle, chaque mesure repart de zéro
et on ne sait pas ce qui a bougé entre deux passages.

### Étape 3 — LE RAPPORT DES ÉCARTS ⏱ 0,5 j · *lecture seule*

Sur la base saine, le même tableau qu'au 19/10, **champ par champ**, mais cette fois sur
un appariement fiable. Et surtout : **une sentinelle** *« une ligne du classeur a perdu
son affaire »* — aujourd'hui **1** *(l'affaire 1001347 disparue)*.

### Étape 4 — LE PATCH D'ALIGNEMENT ⏱ 1 j · *son accord, famille par famille*

Celui du 19/10, mais **seulement la famille ① : le classeur remplit un vide chez nous**.

```
notaire              -> notaire_id              (⚠ apres resolution du NOM en identifiant)
charge commission    -> charge_commission_app
commission           -> honoraires_entree_app
negociateur manquant -> app_affaire_repartition, origine='classeur'
```

⛔ **Rien d'autre.** Les conflits se **listent**, ils ne se corrigent pas.

---

## 2. L'ORDRE, ET LES FEUX VERTS

```
Etape 1  la cascade en lecture seule .... ✅ additif et inerte -- j'enchaine
Etape 2  geler le lien ................... ⛔ son accord (ecriture en base)
Etape 3  le rapport des ecarts ........... ✅ lecture seule
Etape 4  le patch d'alignement ........... ⛔ son accord, champ par champ

taille : ~3 jours
```

---

## 3. LA SUITE DU CHANTIER, APRÈS L'APPARIEMENT

L'appariement n'est **pas le but** : c'est le socle. Ce qu'il débloque, dans l'ordre :

### A — LA LIAISON PERMANENTE *(le vrai objectif de Frédéric)*

> *« pouvoir ajouter des nouvelles lignes dans le Google Sheet, les modifier, et modifier
> les anciennes »*

```
VERROU 0  coller app_sheet_ecrit (le patch du 16/10, JAMAIS colle)
            -> sans lui, on relit nos propres ecritures comme des saisies humaines
VERROU 1  LOT 0 : lire les Apps Script deja presents dans le classeur
            ⛔ Sheet1 nourrit la PAIE. BLOQUE TOUTE ECRITURE tant que ce n'est pas fait.
            -> il faut que Frederic ouvre l'editeur de scripts

puis   le journal du classeur : un declencheur Apps Script -> onglet `_journal`
         (qui · quoi · quand · l'ancienne valeur) + sa sentinelle
       l'arbitre : le plus recent gagne, sinon personne n'ecrit
       les colonnes de classe A manquantes
```

*(Détail : `notice/ANALYSE_LIAISON_REGISTRE_CLASSEUR_2026-10-19.md`, § B.)*

### B — LA QUESTION D'ARCHITECTURE QUI BLOQUE LE SENS CLASSEUR → APP

**Cinq champs du classeur n'ont aucune maison chez nous** : numéro de facture *(3 502)*,
vente prévue *(2 995)*, vente fixée *(2 814)*, date d'annulation *(756)*, vente réglée.

> Notre registre suit la vie **juridique**. Le classeur suit la vie **financière**.
> **Veut-on que le registre porte aussi le financier ?** 5 colonnes, et un changement
> de nature. **Décision de Frédéric, rien ne se code avant.**

### C — LES DEUX FILS OUVERTS PAR LES AUDITS, INDÉPENDANTS

```
⚠ 11 VENTES PORTENT LE NOM DU MAUVAIS ACQUEREUR
  Celui dont le compromis a ete ANNULE. Preuve : le MONTANT de la vente est
  toujours celui du compromis ACTIF. Le montant est juste, le nom est faux.
  -> reste a savoir si Hektor l'a comme ca, ou si notre lecture pioche le mauvais
     acquereur quand un bien porte deux compromis. Se mesure en lisant le BRUT
     d'une de ces ventes. 1 j.

⚠ 1 BIEN VIVANT AFFICHE UNE OFFRE MORTE
  62106, Bessamorel, ACTIF : offre acceptee le 04/08, annulee le 28/09 selon le
  classeur. Un refus d'offre DANS Hektor suffit -- 30 secondes, aucun code.
```

### D — ET CE QUI RESTE DU CHAÎNAGE

```
§ 2.7 (cran 2)  ECRIT, EPROUVE, ETEINT -- 10 compromis actifs sans date
                il suffit de passer APP_CHAINAGE_SANS_DATE de 1 a 2
103             sans-date qui restent seules, et c'est juste
```

---

## 4. ⛔ CE QUE JE NE FAIS PAS

```
- ecrire quoi que ce soit DANS le classeur : l'appariement se range CHEZ NOUS,
  et `ID Unique` suffit comme cle (4 766 valeurs distinctes, deja la).
- deviner : les abstentions restent SANS LIEN, et NOMMEES.
- corriger un conflit : la famille ③ se LISTE.
- toucher au chainage : il est stable, mesure, et la V2 tient depuis le 20/10.
```
