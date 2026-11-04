# A11 — LA CHARGE DE LA COMMISSION : CLORE LE REGISTRE DES MANDATS,
# ET PRÉPARER LE RATTRAPAGE DES TRANSACTIONS PAR LE CLASSEUR

> **Demande de Frédéric, 03/11** : *« audit analyse toutes nos découvertes et mes demandes
> pour me faire la proposition adaptée pour clore le sujet de la charge de la commission sur
> le registre des mandats et préparer le rattrapage par le sheet du registre des
> transactions »*.
>
> ⬜ **Lecture seule. Rien n'est codé, rien n'est posé.** Ce document est une proposition.
>
> ⚠ **Il périme A10 sur trois points** : la couverture (98,4 % et non 76,6 %), le « trou
> 2012-2014 » (il n'existe pas), et l'étape ⑤ (pas d'écriture chez Hektor — il n'a pas de
> case pour recevoir la charge).

---

# ⛔⛔⛔ LE JUGE A RENDU — 03/11, ET IL PÉRIME MA PROPRE RECOMMANDATION

**L'étape 0 a été exécutée** (`phase2/checks/juge_charge_classeur_contre_hektor_2026-11-03.py`,
rapport : `notice/JUGE_CHARGE_CLASSEUR_HEKTOR_2026-11-03.md`). Verdict :

```
comparables 380 :  classeur vendeur 363  ·  classeur acquereur 17

HEKTOR juste                      368   96,84 %
« TOUJOURS VENDEUR » juste        363   95,53 %   <- LE TEMOIN INVERSE
gain reel de Hektor                     +1,32 point

HEKTOR MUET sur                   552 / 956 lignes renseignees = 57,7 %
```

⛔ **DONC : HEKTOR N'EST PAS UNE VALEUR DE RÉFÉRENCE.** Un code qui répondrait
« vendeur » à tout le monde ferait 95,5 %. Remplir 25 800 mandats depuis Hektor
n'apporterait **1,3 point** — pour 775 Mo lus chaque nuit, une sentinelle de
libellé à tenir, et les 51 divergences à arbitrer. **Ça ne vaut pas le prix.**

✅ **MAIS IL A UN USAGE PRÉCIS ET RÉEL** :

```
quand Hektor DIT acquereur, il a raison    7 / 9  = 77,8 %   PRECISION
des acquereurs du classeur, il en trouve   7 / 17 = 41,2 %   RAPPEL
```

→ « Hektor dit acquéreur » est un **signal fort sur la classe rare**, celle que
le défaut « vendeur » rate toujours. « Hektor dit vendeur » n'apprend rien.

## ⭐ LA PROPOSITION RÉVISÉE — plus courte, et moins chère

```
① POSER LES 955 DU CLASSEUR          ~2 h    ILS FONT FOI   ACCORD OBLIGATOIRE
② L ECRAN : la valeur AVEC sa source  ~1/2 j
③ LE PRE-REMPLISSAGE (son palier 2)   ~1/2 j
      ordre : SAISIE > CLASSEUR > « Hektor dit acquereur » > defaut vendeur
④ LES ETIQUETTES                      ~2 h    une a reconfirmer
⑤ HEKTOR, EN SIGNALEMENT SEULEMENT    ~2 h    une LISTE des acquereurs
      probables que le classeur ne couvre pas -> a confirmer a la main,
      JAMAIS ecrite d office
                                      ------
                                      ~1 journee et demie
```

⭐⭐ **CE QUI TOMBE** : l'étape ① d'origine (l'exportateur lit Hektor chaque nuit),
et avec elle les 5,64 s de run, la sentinelle de libellé, le risque d'exception
dans un registre reconstruit en entier, et l'arbitrage des 51 divergences.
**Le juge a fait économiser le plus gros morceau du chantier.**

⚠ **ET UNE DÉCOUVERTE QUI COMPTE** : Hektor est muet sur **58 %** des lignes du
classeur. Explication probable — le classeur suit **les ventes**, et un bien vendu
ou archivé n'a plus de détail frais chez nous (le run ne relit le détail que si la
datemaj change). ⬜ **NON MESURÉ.** Donc ma couverture de 98,4 % vaut pour les
mandats du registre, mais tombe à **42 %** sur les affaires conclues.

⚠ Tout ce qui suit a été écrit **avant** ce verdict. Les mesures des § 1 à 2 restent
vraies ; la proposition du § 3 est **remplacée** par celle ci-dessus.

---

## 1. CE QUI EST ÉTABLI — les mesures, et rien d'autre

### 1.1 ⭐⭐⭐ Hektor PORTE la charge, et la mesure du 02/11 disait le contraire

Deux champs, dans le **texte** de `hektor_annonce_detail.raw_json` :

```
" Honoraires vendeur ou bailleur montant : 5000.0 "
" Honoraires acquereur ou locataire     : 3665.0 "

couverture : 26 713 / 27 148 mandats datés  =  98,4 %
2012 : 99,2 %   2013 : 99,1 %   2014 : 99,4 %   -> LE TROU N'EXISTE PAS
```

⛔ **L'en-tête du patch du 02/11 affirme** : *« La charge, Hektor n'en porte RIEN : mesure du
02/11 sur les raw_json — mandat 17 clés, compromis 16, vente 19, AUCUNE charge »*.
**Cette mesure a compté les CLÉS JSON.** La charge n'est pas une clé — elle est dans le
texte. C'est la seule erreur de ce patch ; **sa décision, elle, reste juste** (§ 1.6).

### 1.2 ⭐⭐ La charge CHANGE, et c'est un nouveau mandat — sa règle est prouvée

`honoraires_json` est un **historique** (jusqu'à 6 lignes), ids croissants.
**14 annonces montrent la charge qui bascule**, et le montant avec elle :

```
annonce 11842 :  2235, 15167, 15168   vendeur    18 500
                 67806, 67807, 67808  Acheteur   16 000
annonce 33164 :  5506                 Acheteur   10 000
                 27988, 27989         vendeur    10 000
```

➡ **Donc : toujours LA DERNIÈRE LIGNE** (id le plus grand). Et 99,4 % des annonces n'ont
qu'**un seul** mandat (26 692 / 26 850) ; 158 en portent deux ou plus.

### 1.3 ⛔ Ce qui n'est PAS la charge — trois pistes fermées par la mesure

```
① entree + sortie == honoraires        9 275 / 9 275, ZERO exception
   entree seule 9 253 (99,8 %) · sortie seule 19 · les deux 1 · aucune 2
   -> contre une charge reelle a 77 / 23, le ratio 99,8 / 0,2 est DEFINITIF :
      ce sont deux MORCEAUX d'une commission, PAS deux payeurs.

② le principe des montants (public / prix de vente / net) DISTINGUE la charge,
   mais exige la TROISIEME valeur, et Hektor ne la rend JAMAIS :
      hektor_compromis -> prixPublique + prixNetVendeur seulement
      hektor_vente     -> prix seulement
      au carnet        -> prix_publique n'existe que 11 fois
   applique a 2 valeurs sur 10 635 compromis, croise avec les deux cases :
      pub = net + honoraires  <->  mandat dit VENDEUR     7 962
      pub = net + honoraires  <->  mandat dit ACQUEREUR      82
   -> LA MEME EQUATION. Aucune discrimination. Et c'est normal : la somme est la
      meme, seul le VERSEUR change.

③ le formulaire d'offre de Hektor : 0 occurrence de « charge » sur 208 541
   caracteres, temoin positif a cote (selectedMandatId et
   offre_montant_honoraires_0 trouves chacun une fois).
```

⭐ **Et ça lève l'inquiétude du 14/10** : *« sur 25 lignes où le classeur dit Acquéreur, 13
sont rangées côté vendeur chez Hektor »*. Cette mesure déduisait la charge **des montants
entrée/sortie** — la piste ① ci-dessus. Elle ne condamne donc **pas** les deux cases.

### 1.4 ⭐⭐ Les transactions ne portent la charge NULLE PART

```
app_affaire_ledger.charge_commission_app :  31 120 VIDE  ·  6 remplis
   et les 6 sont NOS ESSAIS : 1001339, 1001378, 1001381, 1001384, 1001390, 1001393
   (cinq sur l'annonce 24113, mandat 18787, 115 000 a 120 000)

hektor_offre      -> honoraire_acquereur, rempli 33 / 11 200, valeurs aberrantes
                     (179 000, 30 000 : c'est un PRIX) => INEXPLOITABLE
hektor_compromis  -> honorairesEntree + honorairesSortie (meme profil que la vente)
hektor_vente      -> 6 cles d'argent, aucune charge

le mot « charge » : 62 compromis / 10 635 = 0,6 %, et c'est DU TEXTE LIBRE :
   . compromis 23475 -> la phrase vient du DESCRIPTIF COMMERCIAL de l'annonce
   . compromis 21754 -> « Commentaireprestation : Honoraires agence a la charge
     de l'acquereur d'un montant de 13000 EUR » = un commentaire TAPE A LA MAIN
   -> des negociateurs ecrivent la charge a la main FAUTE DE CASE.
      C'est un signal d'usage, pas une source.
```

### 1.5 ⭐⭐⭐ Le lien passe par L'ANNONCE, jamais par le mandat

```
                      hektor_mandat_id        hektor_annonce_id
hektor_offre          2,6 %  (287/11 200)     100 %
hektor_compromis     74,6 %                   100 %
hektor_vente         73,1 %                   100 %

parmi les offres dont LE BIEN a un mandat : 287 / 8 607 = 3,3 %
```

⚠ **Ne pas sur-conclure** : ces offres sont surtout historiques, saisies à la main dans la
console, pas par notre worker. Le chiffre dit l'usage, pas un défaut de notre code.

**Et le worker, lui, envoie bien le mandat** (`console_job_worker.js:13541`, troisième
terme = `selectedMandatId` du formulaire) : 17 transactions sur 20 l'ont rempli **sans que
personne ne le saisisse**. ⛔ Mais Hektor **ne refuse pas** sans lui — preuve par sa propre
réponse : offres **33119** et **33120** créées avec `"id_mandat":null`, travail `done`.
`appendIfValue` (l. 13504) n'envoie simplement pas un champ vide.
⭐ **Sauf « Clos »**, qui l'exige vraiment (`l. 15144`, erreur explicite).

### 1.6 ⭐⭐⭐ Le dispositif de SAISIE existe déjà — palier 1, posé le 02/11

```
colonne   app_mandat_register_current.mandat_charge_honoraires_app
carnet    app_mandat_champ_app  (champ 'charge_commission', origine 'mandat_app')
          cle (annonce, numero_mandat, champ) -- UNE SEULE LIGNE PAR CHAMP
RPC       app_set_mandat_charge_optimistic(annonce, numero_mandat, charge)
          app_reposer_charge_mandat_app(annonce, plancher_registre)
front     apps/hektor-v1/src/lib/api.ts:7100  -- il l'appelle deja

remplissage : 0 / 24 572   -> NORMAL : ca memorise A LA GENERATION DU DOCUMENT
                              de mandat, et le dispositif date du 02/11.
```

**Ses quatre décisions du 02/11, toujours en vigueur** : on mémorise dès la génération du
document · l'avenant n'écrase pas · défaut « vendeur » des deux côtés · deux paliers, la base
puis le pré-remplissage de la modale.

⛔ **L'interdit à respecter absolument** : *« JAMAIS une colonne de Hektor — le suffixe `_app`
n'est pas une décoration »*, parce que la cause racine fermée le 13/10 était *« nous
relisions notre propre écriture comme si elle faisait autorité »*.
➡ Et comme le carnet n'a **qu'une ligne par champ**, y écrire une valeur lue chez Hektor
**écraserait une saisie humaine** au passage suivant.

⚠ **La leçon du patron** : *« le carnet fait foi, la colonne du registre est un reflet qu'on
repose »* — la ligne du registre est détruite puis refaite par le worker à chaque push
d'annonce. ⭐ Mais **le run de nuit ordinaire ne touche pas cette table** (le
`delete_all_rows` est sous `--rebuild-register-only`).

### 1.7 ⭐⭐ Le classeur : colonne Q, et le pont est déjà construit

```
colonne Q « Charge Commission » :  955 lignes  ·  894 Vendeur  ·  61 Acquereur
notre champ correspondant       :  0 ligne sur 12 413  (VIDE a 100 %)

app_classeur_lien, TOUS GELES :
   « sure »       12 106      « a valider »  281      « bonne »  26
   lignes 1 a 4 779, cle « ID Unique »
```

⭐ **Déjà classé PRIORITÉ 2** dans `A4bis_LES_38_COLONNES_DU_CLASSEUR_2026-10-31.md` :
*« Risque strictement nul : il n'y a rien à écraser. C'est le seul champ du classeur dont on
peut dire ça. »*

**Et le classeur est LISIBLE à la demande** — `phase2/checks/rapport_gel_tous_les_champs.py`
le lit par l'API Google Sheets (clé de service Workspace, `Sheet1!A1:AL6000`), relie par
« ID Unique », et compare la charge **sur les trois premières lettres en minuscules**
(« ven » / « acq »), au niveau de la transaction la plus avancée.

⛔ **Mais il compare le classeur à une colonne VIDE.** Personne n'a jamais comparé le
classeur à Hektor. C'est la réserve écrite dans A9 : *« ce serait un troisième témoin, et il
arbitrerait le classeur »*.

### 1.8 L'écran est déjà prêt, et deux étiquettes mentent

```
App.tsx:29646   un bloc « A la charge de » EXISTE sur la fiche affaire
App.tsx:33927   charge: ''  EN DUR  -> la condition est toujours fausse,
                le bloc ne s'affiche JAMAIS. Il attend la donnee, rien de plus.

App.tsx:30884   ajout(lignesOffre,     'Honoraires acquereur', honoraires_sortie...)
App.tsx:30909   ajout(lignesCompromis, 'Honoraires acquereur', honoraires_sortie)
                -> l'etiquette est posee sur LA SORTIE, qui n'est pas un payeur (§1.3 ①).
                   DEUX endroits, pas un.
```

⛔ **Et ce qui N'EST PAS un défaut** : `honorairesCharge: 'mandant'` (`App.tsx:4573`) est **sa
décision du 02/11** — *« Vendeur par défaut des deux côtés »*, parce que le classeur mesure
894 contre 61, soit 93,6 %, et que l'ancien code *« était faux 9 fois sur 10, et il cochait
une case du contrat »*. ⭐ Retiré de la liste des défauts.

### 1.9 Le coût sur le run de nuit — mesuré, pas estimé

```
raw_json  775,4 Mo / 61 470 lignes (moyenne 12,6 Ko, max 92,5 Ko)
   aujourd'hui (mandats_json seul)              0,18 s
   A  tout raw_json + regex Python              5,64 s
   C  extraction COTE BASE (instr + substr)     2,14 s   <- RECOMMANDEE

etape « phase2 registre des mandats »   05:56:50 -> 05:58:01  =  71 s
le run entier                           04:00:01 -> 06:18:23  = 2 h 18
la descente suit a 06:45                -> 27 MINUTES DE MARGE
option C : +3 % sur l'etape, +0,03 % sur le run
```

⛔ **Jamais `fetchall()` sur `raw_json`** (775 Mo en mémoire d'un coup) — on itère au curseur.
⚠ L'option C dépend d'un **libellé** : si Hektor le change, le champ devient muet **sans
erreur** → **sentinelle sur le compte**, 40 484 lignes aujourd'hui.

### 1.10 ⬜ Les réserves, déclarées

```
51   annonces ou les DEUX occurrences du meme champ divergent (7 100 puis 6 000,
     toujours a la baisse) -> laquelle vaut ? NON TRANCHE
533  annonces portent LES DEUX cases ; souvent le MEME montant des deux cotes
     (3 600 / 3 600) = double saisie plutot qu'un partage. NON TRANCHE
82   mandats de 2026 sans charge chez Hektor -> anomalie de SAISIE a l'agence,
     A SIGNALER, rien a coder
524  compromis ou public != net + honoraires, dont 179 a charge vendeur.
     Visible depuis le 27/10 (665 / 689). NON EXPLIQUE, sans rapport avec la charge
435  lignes de registre (1,6 %) sans aucune source
38   lignes de registre sans id d'annonce
⬜   si ces champs existent pour les LOCATIONS (vocabulaire locatif different)
⬜   ce que porte commissionAgence (different de la somme dans 9 272 / 9 275)
```

---

## 2. SES DÉCISIONS, QUI CADRENT LA PROPOSITION

```
1. « la charge peut changer mais alors il faut refaire un mandat »      -> §1.2, PROUVE
2. « je ne veux pas corriger des montants ou charges sur le registre
    des transactions, uniquement pour les prochains : un pre-remplissage »
3. « on recuperera la charge a partir du sheet »
4. « lorsqu'on edite un mandat pour signature le choix de la charge doit
    etre memorise dans le registre des mandats » (02/11)                -> FAIT
5. « a la saisie de la modale offre ou compromis il faudrait que la charge
    se pre-remplisse mais reste modifiable » (02/11)                    -> PALIER 2
6. « clore le sujet sur le registre des mandats »
7. « preparer le rattrapage par le sheet du registre des transactions »
```

---

## 3. LA PROPOSITION

### ⭐⭐⭐ Le principe, en une phrase

**Trois sources, un ordre de préséance qui ne change jamais, et chacune garde sa place :**

```
① LA SAISIE (carnet, _app)   fait foi, toujours.            deja en place (02/11)
② LE CLASSEUR (955)          la verite comptable.            a poser, une fois
③ HEKTOR (26 713)            le reste, en REPLI seulement.   l'exportateur le lit
```

⛔ **Jamais de mélange** : ② et ③ ne touchent **jamais** `mandat_charge_honoraires_app` ni le
carnet. Ils vivent dans **leurs propres colonnes**, et l'écran dit toujours **d'où vient** la
valeur qu'il montre.

### ÉTAPE 0 — LE JUGE *(~2 h, lecture seule)* ⬅ **à faire AVANT tout le reste**

Ajouter au script `rapport_gel_tous_les_champs.py` un **troisième témoin** : pour chaque
ligne du classeur, remonter à l'annonce de l'affaire (`hektor_annonce_id`, rempli à 100 %) et
lire les deux cases du mandat. Trois colonnes côte à côte : **classeur · nous · Hektor**.

```
AUCUNE ecriture : ni chez nous, ni chez Hektor, ni dans le classeur.
Sortie : un rapport dans notice/.
Une seule execution (il lit la plage entiere du classeur).
```

**Ce que le rapport décide :**

```
accord classeur <-> Hektor ELEVE   -> on remplit les 25 800 autres en confiance (etape 3)
accord FAIBLE                      -> on ne garde QUE les 955 du classeur, et Hektor
                                      ne sert qu'a AFFICHER avec sa provenance, jamais
                                      comme valeur de reference
```

⭐ **C'est le seul moyen honnête de clore le sujet** : sans ce rapport, remplir 25 800
mandats depuis Hektor serait un acte de foi. La mesure du 14/10 nous a déjà montré qu'une
source plausible peut se tromper une fois sur deux.

### ÉTAPE 1 — L'EXPORTATEUR LIT HEKTOR *(~1/2 journée)*

`phase2/sync/mandat_ledger.py` :

- élargir le `SELECT` de la ligne 750, **extraction côté base** (`instr` + `substr`) ;
- une fonction qui rend **le mot ET sa source**, et qui **ne lève jamais d'exception** sur une
  forme inconnue — elle rend vide. ⚠ Le registre est reconstruit **en entier** chaque nuit :
  une exception ferait tomber **tout** le registre, pas une ligne ;
- sur `honoraires_json`, **la dernière ligne** (§ 1.2) ;
- deux colonnes locales neuves via `_ajouter_colonne_si_absente` (elle existe, l. 448) :
  `mandat_charge_honoraires_lue` et `mandat_charge_honoraires_lue_origine` ;
- une **sentinelle** sur le compte (40 484 aujourd'hui).

⭐⭐ **Et c'est l'exportateur qui les produit, donc elles reviennent toutes seules** à chaque
reconstruction — **pas besoin de fonction de re-pose** pour elles, contrairement à `_app`.
C'est ce qui rend ce chemin plus robuste que le carnet.

⭐ **Épreuve à blanc d'abord** : retrouver 26 713 / 27 148 **sans rien écrire**. Témoin
positif : le mandat **18836** de l'annonce 62774 (capture en main). Témoin inverse : un bien
sans charge.

⛔ **Pas de lecture du classeur dans le run de nuit** : ce serait une dépendance réseau neuve
dans un run qui n'en a pas. Le classeur se pose par un geste séparé (étape 4).

### ÉTAPE 2 — LES DEUX COLONNES AU CLOUD *(~1 h)* ⛔ **accord obligatoire**

`ALTER TABLE app_mandat_register_current ADD COLUMN IF NOT EXISTS` × 2, avec `_INVERSE` et
`_REPETITION`.

⚠ **Avant le premier push** : `_retirer_colonnes_absentes_du_cloud` (`mandat_ledger.py:1166`)
écarte **en silence** une colonne absente du cloud. On verrait un run vert et des colonnes
vides.

⚠ Et **vérifier d'abord** que les cinq fonctions qui lisent cette table rendent un type fixe
— le patch du 02/11 l'a mesuré pour sa colonne, **la mesure doit être refaite** pour celles-ci.

### ÉTAPE 3 — L'ÉCRAN DU MANDAT *(~1/2 journée)*

Fiche mandat et registre V3. **La valeur avec sa provenance**, toujours :

```
« Acquereur »  (saisi le 03/11 par frederic)       <- _app, fait foi
« Vendeur »    (d'apres le classeur)               <- les 955
« Vendeur »    (d'apres le mandat Hektor)          <- le repli
«  »           (non renseigne)
```

Traduire `Acheteur` en `Acquéreur`. Un libellé propre pour « les deux ».
`npm run build`, et ⭐ **contrôler aussi le téléphone**.

### ÉTAPE 4 — LE CLASSEUR : POSER LES 955 *(~2 h)* ⛔ **accord obligatoire**

Un geste **unique**, pas une tâche de nuit : lire la colonne Q, poser la valeur sur les
affaires reliées, et **remonter au mandat** par l'annonce.

```
GARDE 1  ne poser QUE la ou notre champ est VIDE (c'est 100 % aujourd'hui -> risque nul)
GARDE 2  les liens « sure » SEULEMENT en premiere passe (12 106) ;
         les 281 « a valider » et 26 « bonne » dans un second temps, s'il le veut
GARDE 3  sauvegarde datee AVANT (app_..._avant_charge_classeur_20261103)
GARDE 4  patch + _INVERSE + _REPETITION, et un garde-fou d'empreinte
```

⬜ **À trancher par lui** : la valeur du classeur va-t-elle dans le **carnet** (donc elle fait
foi, comme une saisie humaine) ou dans **sa propre colonne** ? ⭐ Je recommande **le carnet,
avec `origine = 'classeur'`** — parce que le classeur **est** la vérité comptable, et que la
colonne `origine` existe déjà pour dire qui a écrit. Mais c'est sa décision, pas la mienne.

### ÉTAPE 5 — LE PRÉ-REMPLISSAGE DES PROCHAINES TRANSACTIONS *(~1/2 journée)*

Le **palier 2** du 02/11, enfin. À l'ouverture d'une modale d'offre ou de compromis, la charge
arrive **du mandat du bien**, par l'annonce, et **reste modifiable**.

```
. la charge est marquee « reprise du mandat », jamais comme une saisie
  ⭐ lecon du 08/09, ecrite a cote du code : « en reprise, un champ prerempli
     n'est pas une intention » (sale_price portait le prix d'annonce que
     personne n'avait tape)
. si le negociateur la change, SA valeur est gardee
. plusieurs mandats sur le bien (158 cas) -> LE PLUS RECENT.  ⬜ a confirmer
. aucune ecriture chez Hektor : il n'a pas de case pour la recevoir (§1.3 ③)
```

⭐ **Et ça ne peut rien écraser** : le registre des transactions est vierge — 31 120 cases
vides et 6 essais (§ 1.4).

### ÉTAPE 6 — LES ÉTIQUETTES *(~2 h)*

- remplir le `charge: ''` de `App.tsx:33927` → le bloc « À la charge de » **s'allume seul** ;
- corriger « Honoraires acquéreur » aux **deux** endroits (`30884`, `30909`).
  ⬜ ⚠ **Hektor lui-même appelle ce champ ainsi** dans son formulaire — donc le renommer
  nous éloigne de son vocabulaire. Et le 27/10 il avait tranché : *« garde les libellés de
  Hektor en attendant »*. **À reconfirmer par lui.**

---

## 4. LE RATTRAPAGE DES TRANSACTIONS — CE QUE « PRÉPARER » VEUT DIRE

Sa décision est claire : **on ne corrige pas le passé des transactions**. Donc « préparer »
signifie : **tout mettre en état, et ne rien poser**.

```
LIVRABLES DE LA PREPARATION, tous en lecture seule :
  a) le rapport de l'ETAPE 0 : les 955 lignes, classeur contre Hektor contre nous
  b) la LISTE NOMMEE des affaires concernees, avec leur lien et sa confiance
     (jamais un compte agrege : un controle qui agrege perd ce qui sert a agir)
  c) un patch de pose + _INVERSE + _REPETITION, ECRIT ET EPROUVE DANS UNE
     TRANSACTION ANNULEE, mais NON COLLE
  d) la liste des cas que le patch REFUSERA, et pourquoi
```

⭐ **Et le rattrapage des transactions devient presque inutile** si l'étape 5 est faite : les
affaires **à venir** hériteront de la charge du mandat, et le mandat l'aura par le classeur ou
par Hektor. Le rattrapage ne servirait qu'à habiller les 31 120 affaires **déjà closes** —
ce qui n'a d'intérêt que pour un historique, pas pour le travail quotidien.

➡ **Ma recommandation : préparer, puis ne poser que s'il le demande.**

---

## 5. ⚠ CE QUE ÇA POURRAIT CASSER AILLEURS

```
. LE REGISTRE EST RECONSTRUIT EN ENTIER chaque nuit -> une exception dans la
  lecture ferait tomber TOUT le registre. La fonction rend vide, jamais une erreur.
. _retirer_colonnes_absentes_du_cloud ECARTE EN SILENCE une colonne absente du
  cloud -> poser le SQL AVANT le push, sinon run vert et colonnes vides.
. LA LIGNE DU REGISTRE EST DETRUITE ET REFAITE par le worker a chaque push
  d'annonce. Les colonnes « lues » reviennent seules (l'exportateur les calcule) ;
  _app a besoin de sa fonction de re-pose, qui existe deja.
. L'OPTION C DEPEND D'UN LIBELLE de Hektor -> sentinelle sur le compte, sinon
  panne silencieuse.
. LA MODALE DE STATUT PORTE CINQ CRANS (Actif, Offre, Compromis, Vendu, Clos) :
  un seul champ de charge pour les cinq. Y toucher touche les cinq.
. LE DEFAUT « vendeur » DOIT RESTER LE DEFAUT (sa decision du 02/11) : le
  pre-remplissage le REMPLACE par une vraie valeur quand elle existe, il ne
  change pas le comportement quand elle manque.
. 5 FONCTIONS lisent app_mandat_register_current. Le 02/11 a mesure qu'aucune ne
  fait `select *` : LA MESURE DOIT ETRE REFAITE pour les colonnes neuves.
```

---

## 6. L'ORDRE, ET CE QUE JE RECOMMANDE

```
0  LE JUGE (classeur contre Hektor)            ~2 h     lecture seule
   ⬇ IL COMMANDE TOUT LE RESTE
1  l'exportateur lit Hektor                    ~1/2 j   epreuve a blanc d'abord
2  les deux colonnes au cloud                  ~1 h     ACCORD OBLIGATOIRE
3  l'ecran du mandat, avec la provenance       ~1/2 j
4  poser les 955 du classeur                   ~2 h     ACCORD OBLIGATOIRE
5  le pre-remplissage des prochaines           ~1/2 j   son palier 2
6  les etiquettes                              ~2 h     une a reconfirmer
                                               ------
                                               ~2 journees
```

⭐ **Je recommande de commencer par 0 SEUL**, et de ne rien décider avant son rapport.
C'est deux heures, ça n'écrit rien, et ça peut changer les étapes 1 et 3 du tout au tout.

**Puis 1-2-3 ensemble**, puis 4, puis 5 une fois qu'il aura **vu** la donnée à l'écran, puis 6.

---

## 7. ⬜ LES QUATRE DÉCISIONS QUI SONT À LUI

```
1. LE CLASSEUR VA-T-IL DANS LE CARNET (il fait alors foi, origine = 'classeur')
   ou dans sa propre colonne ?          ⭐ je recommande LE CARNET
2. LES 51 doubles occurrences divergentes : la derniere ?  (a eprouver avant)
3. LES 533 « les deux cases » : quel mot afficher ?
4. LES ETIQUETTES « Honoraires acquereur » : les renommer, alors qu'il avait
   tranche le 27/10 « garde les libelles de Hektor en attendant » ?
```

⬜ **Rien n'est codé. Rien n'est posé. Aucun « go » n'a été donné.**
