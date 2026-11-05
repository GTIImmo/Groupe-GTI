# LA TABLE DE PROPRIÉTÉ DU CLASSEUR — proposition du 05/11/2026

**Sa demande** : *« peux-tu me donner la table de propriété que tu as ? »*

⛔ **ELLE N'EXISTE PAS ENCORE EN BASE.** Ce document est une **proposition à valider
colonne par colonne**. Rien n'est posé, rien n'est codé.

---

## 0. À QUOI ELLE SERT — une seule question par colonne

> **QUI FAIT FOI ?** Tout le reste en découle mécaniquement.

```
CAS 1  vide chez nous . rempli au classeur    -> ON PREND      (deja decide le 29/10)
CAS 2  rempli chez nous . vide au classeur    -> ON POUSSE     (phase B)
CAS 3  rempli des deux . IDENTIQUE            -> RIEN
CAS 4  rempli des deux . DIFFERENT            -> selon le PROPRIETAIRE  <- la decision
```

⛔⛔ **LA RÈGLE DE SÛRETÉ, proposée comme non négociable : un écart ne se résout
JAMAIS tout seul.** Toute colonne non déclarée vaut `personne` / `lister` par défaut.
Sans ce défaut, une colonne oubliée se fait écraser en silence — risque **prouvé** sur
Négociateur 2 : nous en avons 209, le classeur 685 ; une liste blanche effacerait nos 209.

⭐ **Et elle rend tout réversible sans déploiement** : changer d'avis sur une colonne =
changer une ligne.

---

## 1. LA TABLE PROPOSÉE — 38 colonnes, mesurées le 05/11

Les quatre champs : `qui_fait_foi` (nous | classeur | personne) · `sur_conflit`
(ecraser | prendre | lister) · `depuis_quand` (une date, pour le seul cas du prix) ·
la raison.

### ✅ LE CLASSEUR FAIT FOI — il est seule source, nous n'avons rien à opposer

```
col  colonne               remplies   ecarts   sur_conflit   pourquoi
Q    Charge Commission        959        0     prendre       notre champ etait VIDE a 100 %
                                                             ⭐ DEJA FAIT le 04/11 (837 posees)
K    Negociateur 2            687      374     prendre       il en sait 685, nous 209
M    Negociateur 3             13        9     prendre       idem, 13 lignes
L    Pourcentage 2            684        ?     prendre       va avec Negociateur 2
N    Pourcentage 3             14        ?     prendre       va avec Negociateur 3
Y    Vente Reglee           3 752        0     prendre       NOUS N AVONS AUCUN CHAMP
AA   Numero de facture      3 729        0     prendre       NOUS N AVONS AUCUN CHAMP
Z    Annulee                  896        0     prendre       ⬜ avons-nous une date d annulation ?
```

⚠ **Préalable bloquant pour K · L · M · N** : la **table d'alias** des négociateurs.
GIRAUD = Aline VALETTE (163 cases), ALVES MENDES = Lucie DECHANDON (119 cases), confirmé
par Frédéric le 29/10. Sans elle, on ajoute la même personne deux fois et **sa commission
est coupée en deux**. ⛔ Ne pas poser ces quatre colonnes avant.

### ✅ NOUS FAISONS FOI — la donnée vient de Hektor, relue chaque nuit

```
col  colonne               remplies   ecarts   sur_conflit   pourquoi
AG   Ville                  4 770    1 644     ecraser       le classeur est saisi a la main
D    Nature                 4 778    1 653     ecraser       idem
R    Etat Actuel            4 778      160     lister (!)    ⚠ c est un ETAT CALCULE, pas une
                                                             donnee : ecraser n a pas de sens
C    Mandat                 4 778      134     lister (!)    ⛔ les 134 ecarts sont LEGITIMES :
                                                             sur un mandat de recherche, le
                                                             classeur porte le n° de recherche
                                                             et nous celui de vente (A4bis)
B    product_ref              694       69     ecraser       c est NOTRE numero de dossier
```

⚠ **Noter l'exception** : R et C sont « nous faisons foi » **mais** `lister` sur conflit —
parce que l'écart n'est pas une erreur du classeur. On ne corrige pas ce qui est juste.

### ⬜ PERSONNE NE FAIT FOI — on liste, on n'écrit pas

```
col  colonne               remplies   ecarts   pourquoi
V    Vente Prevue           4 026    1 767     56 % des comparables : une date qui bouge
                                               par nature. ⛔ A4bis : ne PAS aligner
O    Notaire                2 566    1 373     ⛔ CE NE SONT PAS DES ECARTS : nous portons
                                               DEUX notaires, le classeur UN SEUL
H    Agence                 4 765      498     ⚠ CAUSE NON MESUREE -- a comprendre d abord
I    Negociateur 1          4 777      432     demande la table d ALIAS avant toute decision
S    Offre Achat            4 744      210     la moins fiable des trois dates
AB   Acquereur              4 778      120     ⚠ EN AJOUT seulement, jamais en remplacement
AD   Vendeur                4 778       68     idem
P    Commission TTC         4 777       85     ⬜ non analyse
W    Vente Fixee            3 776       61     98 % de concordance : on pose les 31 vides
T    Compromis              4 230       44     98,7 % : on pose les 106 vides
J    Pourcentage 1          4 776        ?     va avec Negociateur 1 -> alias d abord
```

### ⭐ LE CAS À PART — le PRIX, propriété PARTAGÉE PAR ANNÉE

```
AF   Prix                   4 777      208     NOUS a partir de 2025 . LE CLASSEUR avant
                                               depuis_quand = 2025-01-01
```

⭐ **C'est le seul champ dans ce cas**, et c'est lui qui justifie la 3ᵉ colonne de la table.

### ⬜ NI L'UN NI L'AUTRE — colonnes sans maison chez nous

```
col  colonne                    remplies   ce qu on en fait
A    affair_uuid                     0     VIDE sur 4 778 lignes -- une place qui nous attend
E    Lien CRM                    4 687     ⬜ SA REPONSE : qu est-ce que Netty, ca sert encore ?
F    En attente de               3 087     ⬜ non analyse
G    COMMENTAIRES                4 119     ⬜ SA DECISION : les reprendre en bloc dans une note ?
U    Signe                       4 778     ⬜ non analyse
X    Signee                      4 778     ⬜ non analyse
AC   Adresse Acquereur              60     1,3 % -- negligeable
AE   Adresse Vendeur               798     ⬜ non analyse
AH   Avis a envoyer              2 254     ⬜ SA DECISION : creer le champ, ou ignorer ?
AI   Commentaire Avis              392     idem
AJ   Avis envoye                 2 401     idem
AK   Divers                         12     0,3 % -- negligeable
AL   ID Unique                   4 778     ⭐ LA CLE DU PONT -- ne jamais toucher
```

⚠ **Les 4 champs sans maison** (facture, vente prévue, vente fixée, date d'annulation)
vont **AU CARNET**, ⛔ jamais en colonnes du registre — décision déjà prise le 22/10,
parce que le registre suit le JURIDIQUE.

---

## 2. CE QUI EST DÉJÀ ACQUIS, ET QU'ON NE REFAIT PAS

```
le pont gele           12 413 liens, cle « ID Unique »
                       reverifie le 02/11 : 4 679 lignes concordent, 0 divergence
la charge (Q)          23 474 valeurs posees le 04/11, couverture 95,5 %
les exclusions         2 mandats declares (classeur contradictoire)
```

## 3. ⛔ LES DEUX VERROUS QUI N'ONT PAS BOUGÉ

**① Les Apps Script du classeur** — c'est à Frédéric. Bloque **l'écriture vers le
classeur**, donc toute la **phase B**. ⭐ Ne bloque PAS la phase A (lire le classeur).

**② La table d'alias des négociateurs** — bloque les colonnes I · J · K · L · M · N,
c'est-à-dire **le poste 1, celui qui touche la paie**.
⭐ **Et la bonne nouvelle du 05/11** : l'autre session construit en ce moment le **registre
des négociateurs** (185 personnes, 242 fiches, dont 36 qui ne sont plus chez Hektor).
Attendre qu'il soit fini pour bâtir les alias dessus est **la bonne décision** — ce serait
du travail perdu de les deviner maintenant.

---

## 4. ⬜ CE QUE J'ATTENDS DE LUI

1. **Valide-t-il la forme** : quatre colonnes, défaut `personne` / `lister` ?
2. **Valide-t-il mes recommandations** colonne par colonne, ou veut-il en changer ?
3. **Les trois questions ouvertes** : Lien CRM (Netty) · COMMENTAIRES en bloc ?
   · les trois colonnes « Avis » — créer les champs ou ignorer ?
