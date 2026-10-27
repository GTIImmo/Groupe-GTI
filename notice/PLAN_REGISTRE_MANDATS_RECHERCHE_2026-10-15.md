# Un registre dédié aux mandats de recherche — comment faire

**15/10/2026.** Frédéric :

> *« Il y a déjà aujourd'hui des mandats de recherche. Ces mandats doivent être reliés à un
> contact et pas à une annonce, et donc s'il faut avoir un registre dédié, explique-moi
> comment nous pouvons faire. »*

**Audit en lecture seule, suivi d'une proposition. Aucun code écrit, aucune décision prise.**

---

## 1. ⭐⭐ IL A RAISON, ET C'EST PIRE QUE PRÉVU — mesuré, 65 sur 65

Nous avons **65 mandats de recherche** au registre. Tous sont accrochés à une annonce.
J'ai cherché **qui** ils affichent comme mandant.

```
sur les 65 mandats de RECHERCHE :
   le « mandant » affiche est un PROPRIETAIRE/MANDANT DE L'ANNONCE    65
   c'est le vrai chercheur (celui qui nous a mandate pour chercher)    0
```

**Exemple**, mandat **3428** sur l'annonce **10331** :

| | |
|---|---|
| ce que le registre affiche comme mandant | *Christian HERITIER, Marie Rose GARDES HÉRITIER* |
| les personnes liées à l'annonce 10331 | *Christiane TEYSSIER VALON, Eliane HÉRITIER…* — **les mêmes** |
| le véritable acquéreur de cette annonce | *MONTEILHET Loïc* — **personne d'autre** |

➡ **Aujourd'hui, un mandat de recherche du registre légal porte le nom du PROPRIÉTAIRE
d'un bien, pas celui de la personne qui nous a mandatés pour chercher.**

### Et ce n'est pas un bug qu'on peut corriger : c'est la conséquence de la clé

Les **deux** sources du nom sont indexées sur l'annonce, donc **aucune des deux** ne peut
donner le chercheur :

```
source 1   payload.mandants, tel que Hektor le sert    -> 65/65 donnent le nom de l'annonce
source 2   notre registre des liens, en repli          -> indexe PAR ANNONCE (app_relation)
```

⚠ **Tant que le mandat est accroché à une annonce, il affichera le mauvais nom.**
Ce n'est pas une colonne à remplir, c'est un rattachement à changer.

---

## 2. ⭐ LE PATRON EXISTE DÉJÀ DANS TON PROJET

Tu n'inventes rien : **`app_search_registry`** est exactement ça — un registre accroché à
un **contact**, pas à une annonce.

```
app_search_registry          77 203 lignes
   app_search_id        PK
   hektor_contact_id          <- le numero de Hektor
   app_contact_id             <- NOTRE numero
   search_index
   first_seen_at / last_seen_at
   DEUX index uniques :  (app_contact_id, search_index)
                         (hektor_contact_id, search_index)
```

C'est **le même besoin, déjà résolu** : une chose qui appartient à une personne, numérotée,
durable, avec notre numéro **et** celui de Hektor. On recopie cette forme.

---

## 3. ⭐⭐ UNE SEULE TABLE — révision du 15/10, après la question de Frédéric

> *« Mais je souhaite avoir une seule table registre des mandats, pourquoi on ne peut pas
> la modifier ? »*

**On peut. Ma première réponse visait le mauvais obstacle** : j'ai parlé de coût, alors que
le vrai obstacle est précis, technique, et **contournable**.

### Le vrai obstacle : un NULL détruit la protection contre les doublons

Épreuve, faite en mémoire sur une copie du schéma :

```
UNIQUE (hektor_annonce_id, numero_mandat)
   doublon ('53519','17874')  -> REFUSE    l'index protege
   doublon (NULL,  '18741')   -> ⚠ ACCEPTE  L'INDEX NE PROTEGE PLUS
   (identique en PostgreSQL : NULL est toujours distinct d'un autre NULL)
```

Et **on ne peut pas se rabattre sur le numéro seul** comme clé :

```
26 859 lignes pour 18 743 numeros distincts
   -> 8 116 numeros sont portes par PLUSIEURS annonces
   le pire : le numero 1311 existe sur 13 annonces
```

*(C'est le dossier déjà connu : « Hektor recycle ses id de mandat ».)* Un mandat de
recherche sans annonce pourrait donc être inséré **cinquante fois** sans que rien ne crie.

### ⭐ LA SOLUTION QUI GARDE UNE SEULE TABLE : le vide, pas le NULL

```
hektor_annonce_id = ''   au lieu de NULL
```

Épreuve, sur le même schéma :

```
   doublon ('', '18741')  -> ⭐ REFUSE   L'INDEX PROTEGE TOUJOURS
   ('', '18741') et ('', '18747') : acceptes, ce sont deux mandats differents
   (identique en PostgreSQL : '' est une VALEUR, pas un NULL)
```

**Et la valeur est libre** : **0** des 26 859 lignes porte une annonce vide aujourd'hui.
⭐ **Le projet l'avait même anticipé** : `phase2/checks/mandat_corps_recopie.py` l. 198
teste déjà `TRIM(COALESCE(CAST(hektor_annonce_id AS TEXT),'')) <> ''`.

### Ce qu'il faut ajouter à `app_mandat` — deux colonnes, rien d'autre

```
app_contact_id       INTEGER   facultatif   <- NOTRE numero du chercheur
hektor_contact_id    TEXT      facultatif   <- celui de Hektor
```

**La clé ne bouge pas. `NOT NULL` ne bouge pas. L'index unique ne bouge pas.**
C'est exactement le patron que Frédéric a lui-même trouvé le 13/10 pour la clôture :
*une colonne supplémentaire, pas une refonte.*

### Pourquoi ça tient, vérifié

| | |
|---|---|
| l'index unique protège toujours | ✅ éprouvé (`''` refuse le doublon) |
| la valeur `''` est libre | ✅ 0 ligne sur 26 859 |
| les 91 mandats de recherche *(65 + 26 de l'export)* | ✅ **91 numéros distincts, aucune répétition** |
| l'écrivain `mandat_ledger.py` | ✅ `ON CONFLICT(hektor_annonce_id, numero_mandat)` — fonctionne tel quel |
| `app_dossier_id` | ✅ déjà facultatif |
| sentinelle `mandat_disparu` | ✅ compte et groupe par le couple — indifférente |
| sentinelle `mandat_un_numero` | ✅ compare registre et doublure sur le couple — indifférente |

⚠ **Ce qui reste à écrire — et c'était à écrire DANS LES DEUX FORMES** : le fabricant du
registre **part des annonces** *(`build_mandat_register_rows`, et
`charger_mandats_depuis_app_mandat` fait `if not annonce: continue`)*. Il faut lui ajouter
une seconde source. **C'est le vrai travail, et une table de plus ne l'aurait pas évité.**

### ➡ Conclusion : une seule table, et c'est MOINS de travail

L'idée d'une table jumelle `app_mandat_recherche` **est abandonnée**. Elle aurait doublé
les sentinelles, la doublure `__sb`, l'écrivain et le push — pour le même travail au
fabricant. **Frédéric a raison : une seule table.**

### ⭐⭐ Et UN SEUL registre à l'écran, parce que la loi en veut un seul

C'est le point important, et **c'est déjà possible sans rien casser** : la table que
l'écran lit, `app_mandat_register_current`, **n'est pas un registre, c'est une vue de
travail** *(décision du 29/09)*, et sa clé est **une chaîne de caractères** :

```python
"register_row_id": f"{annonce_id}:{numero}"      # export_app_payload.py l. 2350
```

Il suffit donc que le fabricant produise **deux familles de lignes dans la même vue** :

```
mandat de vente      register_row_id = "53519:17874"      (annonce:numero)
mandat de recherche  register_row_id = "C604355:18741"    (contact:numero)
```

*(Les deux viennent désormais de la **même table** `app_mandat` : la première famille a une
annonce, la seconde a `hektor_annonce_id = ''` et un `app_contact_id`.)*

**L'écran ne fait AUCUNE différence** : j'ai vérifié les 18 endroits qui touchent
`register_row_id` — personne ne le découpe, il sert uniquement de clé d'égalité et de tri.
➡ **Un seul registre chronologique à l'écran, comme la loi Hoguet le demande**, alimenté
par deux tables.

⭐ **Et la numérotation ne pose aucun problème** : les mandats de recherche prennent leurs
numéros dans la **même série Hektor** que les autres (18741 est unique, tous mandats
confondus). Une seule série, un seul registre.

---

## 4. Ce qui remplit cette table — deux robinets, déjà identifiés

```
LE PRESENT   la porte CONSOLE, trouvee et prouvee le 15/10 :
   /admin/xmlrpc.php?mode=contacts-contactProfile-setContactContent
      &idContact=<contact>&toCall=mandatSuivi&fromSearch=false
   -> HTTP 200, 126 035 octets, le mandat 18747 ET « mandat de recherche » dedans
   ⭐ Et elle donne LE NUMERO DU CONTACT -- c'est exactement la cle qui manque.
   ⚠ Par PETITS LOTS, en partant des acquereurs d'affaires : le projet a deja paye
     un BANNISSEMENT D'IP sur un rattrapage trop rapide.

LE PASSE     les 22 mandats de recherche de l'export `mandats_extraits.xlsx`
   Ils portent le NOM du chercheur (contact_full_name), pas son numero -- il
   faudra le rapprocher dans app_contact. Un script a part, hors du run.
```

---

## 5. ⚠ Ce que ça pourrait casser ailleurs — la rubrique obligatoire

| | |
|---|---|
| `app_mandat` : clé, `NOT NULL`, index unique | **rien** — seulement **2 colonnes facultatives en plus** |
| les 26 859 lignes existantes | **rien** : elles gardent leur annonce |
| les 2 sentinelles mandats | **rien** : elles travaillent sur le couple, éprouvé |
| l'écrivain `mandat_ledger.py` | **rien** : son `ON CONFLICT` porte déjà sur le couple |
| la doublure `app_mandat__sb` | ⚠ les 2 colonnes doivent descendre aussi, sinon `mandat_un_numero` criera |
| le run de nuit, le worker | **rien** tant que l'étape 3 n'est pas branchée |
| le **tri** du registre | ⚠ `register_row_id` sert de **clé de tri** et de pagination : un préfixe `C…` grouperait les recherches à part dans l'ordre par défaut. **À regarder à l'écran** avant de choisir la forme du préfixe |
| la fiche du registre, **bureau** | ✅ **elle marche déjà sans annonce** — elle lit la ligne du registre, pas l'annonce. Les 3 boutons qui ont besoin de l'annonce sont déjà gardés |
| la fiche du registre, **MOBILE** | ⛔ **clic muet** : `if (row?.app_dossier_id) openDossierDetailPage(...)` — sans annonce, **rien ne s'ouvre, sans message**. À réparer dans tous les cas |
| les 65 mandats de recherche **actuels** | ⚠ **QUESTION POUR TOI** : on les laisse où ils sont (avec le mauvais nom), ou on les déplace vers la nouvelle table ? Déplacer, c'est retirer 65 lignes d'`app_mandat`, et « rien n'en sort jamais » |

---

## 6. ⛔ Ce qu'il ne faut PAS faire

```
- une ANNONCE FICTIVE par mandat de recherche : contraire a la regle du projet
  (« un numero ne se perd jamais », on n'invente pas d'identifiant)
- mettre hektor_annonce_id a NULL : ca DETRUIT la protection contre les doublons
  (epreuve du § 3) -- le vide '' la garde, le NULL non
- elargir manual_mandat_corrections.py : elle REMPLACE la liste des mandats d'une
  annonce (`patched["mandats"] = [correction]`), elle ecraserait le mandat courant
- une seconde table jumelle : abandonnee le 15/10, voir § 3
```

---

## 7. L'ordre, et où on en est — *« vas-y », 15/10*

```
1  ✅ FAIT  2 colonnes facultatives sur app_mandat    additif, 0 ligne touchee
2  ⬜       la lecture CONSOLE d'un contact           lecture seule, petits lots
3  ⬜       le fabricant produit les deux familles    la vue de travail seulement
4  ⬜       le clic MOBILE repare                     1 ligne
5  ⬜       le rattrapage des mandats de l'export     script a part, hors du run
6  ⛔ BLOQUE la bascule des 65 -- voir § 8
```

---

## 8ter. ⭐⭐ LA LISTE DE HEKTOR — l'autorité, donnée par Frédéric le 15/10

Fichier : **`liste des mandats de recherche protexa.xlsx`** (racine du projet).
C'est l'écran « mandats de recherche » de Hektor, exporté. **16 mandats**, du
**02/04/2026** au **13/10/2026** — c'est-à-dire **tous après la frontière de l'API gelée**
(n° 18339 / 30-01-2026). Tout concorde.

| n° | date | agence | chez nous ? | contact retrouvé |
|---|---|---|---|---|
| 18502 | 02/04 | Issoire | ⚠ « INCONNUE » ann. 62038 | 2 homonymes |
| 18567 | 28/04 | Tence | ABSENT | ⭐ 10353643 FAYARD |
| 18576 | 30/04 | St-Didier | ABSENT | 3 homonymes |
| 18579 | 30/04 | St-Didier | ABSENT | 3 homonymes |
| 18596 | 11/05 | Issoire | ABSENT | ⭐ 10353471 ETCHEVERZE |
| 18612 | 18/05 | Brioude | ABSENT | ⭐ 10042859 RASPAIL |
| **« 8 682 »** | 08/06 | Issoire | ⚠⚠ **voir le piège** | ⭐ 10354437 JOUM |
| 18730 | 29/06 | Courpière | ABSENT | 2 homonymes |
| 18747 | 06/07 | St-Didier | ABSENT | 3 homonymes |
| 18790 | 30/07 | Courpière | ABSENT | ⭐ 10199241 CHATAIGNER |
| 18804 | 04/08 | Ambert | ABSENT | 5 homonymes |
| 18852 | 07/09 | St-Étienne | ABSENT | ⭐ 10355867 CURSOUX |
| 18854 | 07/09 | Craponne | ABSENT | ⭐ 10355908 LEFEUVRE |
| 18858 | 08/09 | Firminy | ABSENT | ⭐ 10355856 PALAZON |
| 18937 | 13/10 | Issoire | ✅ « RECHERCHE » ann. 63200 | ⭐ 10355480 GIRARD |
| 18938 | 13/10 | Issoire | ✅ « RECHERCHE » ann. 63200 | ⭐ 10355480 GIRARD |

```
AU REGISTRE  4   dont 2 bien classes (18937/18938) et 1 mal classe (18502)
ABSENTS     12
CONTACT     10 sur 16 identifies sans ambiguite
```

### ⚠⚠ LE PIÈGE DU FICHIER : « 8 682 » a perdu un « 1 »

Le fichier écrit **8 682** pour le mandat de M. JOUM, Issoire, 08/06/2026. Or :

```
8682  EXISTE chez nous : une VENTE de 2014, annonce 16703, Sylvia HEROT
18682 n'existe pas chez nous
```

Un mandat de **juin 2026** ne peut pas porter le n° 8682 : la série était à ~18 600.
**C'est 18682.** ⛔ **Importer le fichier tel quel ECRASERAIT une vente de 2014.**
➡ Tout import de cette liste doit **refuser** un numéro qui existe déjà avec une autre
nature et une date incompatible, au lieu de le poser.

### ⭐ ET ELLE CONFIRME TOUT

**Aucun** des 63 que nous appelions « RECHERCHE » n'est dans cette liste. La liste de
Hektor, le code `mandate_type` du tableur ancien, et les annotations « MDR » du classeur
disent **la même chose**, par trois chemins indépendants.

### ⚠ IL MANQUE UNE PAGE

La liste commence au **02/04/2026**. L'exemple que Frédéric citait le 15/10 au matin —
**18487**, contact 41625 — est **antérieur** et n'y figure pas. Entre le dernier du
tableur ancien (**18297**, 26/02) et le premier d'ici (**18502**, 02/04), il y a un trou.
➡ **À demander à Frédéric : le même écran, sans filtre de date.**

---

## 8bis. ⚠⚠ LE TABLEUR ANCIEN A RENVERSÉ LE DIAGNOSTIC — *correction du 15/10*

Frédéric : *« mais le nom du contact est bien dans mon tableur ? »* — **oui, et c'est ce
qui a tout changé.** Le tableur ne porte pas qu'un nom : il porte un **CODE**,
`mandate_type`, là où notre registre déduit la nature d'une **note en texte libre**.

### Ce que le code dit des 65

```
nos 65 lignes « RECHERCHE », face au tableur :
   mandate_type = 1 (VENTE)       63
   mandate_type = 3 (RECHERCHE)    0
   hors tableur (apres le 26/02)   2   <- 18937 et 18938, classes par le TYPE du mandat
```

**63 sur 63.** Notre `nature = RECHERCHE` est **fausse** pour elles. La cause est visible
à l'œil sur la note du mandat **3428** :

> *« Objet mandat : MANDAT DE RECHERCHE 4165 **remplacé par** MDR 4210 »*

Ce n'est pas un mandat de recherche : c'est un mandat de **vente** dont le champ « objet »
contient une phrase **parlant d'un autre mandat**. `_nature()` cherche
`"MANDAT DE RECHERCHE" in note` et tombe dedans — exactement le piège 7133.

➡ **Et donc « le registre affiche la mauvaise personne » était FAUX.** Pour 63 de ces
lignes, le propriétaire du bien **est** le bon mandant : ce sont des ventes. Les chiffres
étaient justes, la conclusion ne l'était pas.

### L'erreur inverse existe aussi

```
les 26 VRAIS mandats de recherche du tableur (code type=3) :
   ABSENTS du registre                    22
   PRESENTS mais classes « VENTE » par nous 4   -> 17704, 17807, 18057, 18297
```

⭐ **Double confirmation indépendante du code 3** : les numéros **17758, 17651, 17627,
17705, 17856** sont exactement ceux que le classeur de suivi, écrit à la main, annote
« **MDR** ». Deux sources qui ne se connaissent pas disent la même chose.

### ⭐ Et le nom s'apparie à nos contacts

```
26 mandats de recherche du tableur -> notre registre des contacts (356 515 noms)
   UN SEUL contact trouve directement        14
   ⭐ ambiguite LEVEE par « a une recherche »  6   <- un chercheur a une recherche
   reste ambigu                                5
   sans nom dans le tableur                    1
   ───────────────────────────────────────────────
   TRANCHES                                   20 sur 26
```

➡ **La question du contact est donc résolue pour 20 des 26** — sans console, sans
hypothèse. Le § 8 ci-dessous reste vrai **pour les 2 vrais mandats de recherche
postérieurs au tableur** (18937, 18938), pas pour les autres.

### Ce qu'il faut faire, revu

```
A  NE PAS basculer les 65.  63 sont des mandats de VENTE mal etiquetes.
B  Corriger _nature() : la note en texte libre n'est pas une autorite ; le
   TYPE du mandat l'est. -> 63 lignes reviennent a VENTE, 4 passent a RECHERCHE.
C  Ajouter les 22 absents, avec leur contact (20 identifies).
D  Les 2 colonnes posees aujourd'hui servent a C, inchangees.
```

---

## 8. ⛔ LA BASCULE EST BLOQUÉE POUR CE QUI N'EST PAS DANS LE TABLEUR

Frédéric a dit « bascule les 65 ». **Je ne peux pas, et le faire quand même serait pire
qu'aujourd'hui.** Pour poser `annonce = ''`, il faut mettre le contact à la place —
sinon la ligne n'a **ni annonce ni contact**, et on a perdu le seul lien qui existait.

**Or nous n'avons nulle part l'identité du chercheur.** Mesuré le 15/10 :

| source | ce qu'elle porte |
|---|---|
| `app_mandat.payload_json` | `mandants` = **du texte libre**, aucun identifiant |
| `app_mandat.mandants_texte` | idem, et c'est le nom lié à **l'annonce** |
| `hektor_mandat` (matière brute) | 13 colonnes, **aucune** pour une personne |
| `app_affaire_console` | indexée par **annonce** |
| `app_contact_search_current` | ne porte **aucun numéro de mandat** |

### ⭐ UNE PISTE, à prouver avant d'y toucher

Hektor semble raccrocher le mandat de recherche **au bien trouvé**, au moment de la vente
*(44 des 64 portent sur un bien déjà vendu)*. Si c'est vrai, **le chercheur est
l'acquéreur de cette annonce** — et nous l'avons :

```
sur les 65, l'annonce porte :
   UN SEUL acquereur identifie   53   <- candidat sans ambiguite
   PLUSIEURS acquereurs           8   <- il faudrait choisir
   AUCUN                          4   <- rien a proposer
```

⚠ **C'est une hypothèse, pas une mesure.** La prouver coûte **une lecture console** sur
2 ou 3 des 65 : si le mandat y apparaît bien sur la fiche de l'acquéreur, on bascule les
53 sans risque. Sinon on aurait écrit 53 fausses identités **dans le registre légal**.

➡ **La bascule attend l'étape 2 (la lecture console).** Ce n'est pas un report : c'est
l'ordre qui la rend possible.

⚠ Et la lecture console attend une **session de navigateur fraîche** :
`Console/storage_state.json` est périmé depuis le **29/06** et pointe encore l'ancien
domaine `la-boite-immo.com`.

---

## 9. ⭐ LE VOLUME DE CORRECTIONS, PAR SOURCE — mesuré le 15/10

### A — Le registre LÉGAL certifié *(`Certif_Export_RT14405_12586.pdf`, mars→oct 2026)*

| | volume | détail |
|---|---|---|
| ① mandats de **recherche** absents | **16** | 18462 · 18487 · 18491 · 18567 · 18576 · 18579 · 18596 · 18612 · 18682 · 18730 · 18747 · 18790 · 18804 · 18852 · 18854 · 18858 |
| ② mandats de **vente** absents | **4** | 18455 · 18500 *(avenant au 18499)* · 18941 · 18942 *(ces 2 datés d'aujourd'hui, ils descendront seuls)* |
| ③ **natures** à corriger | **3** | 18502 → RECHERCHE · 18831 et 18928 → VENTE |
| ④ **dates** fausses ou vides | **9** | dont **18536** : chez nous `2026-11-16`, le légal dit `2026-04-16` — **7 mois d'écart** ; et **18570** : `2026-01-28` contre `2026-04-30` |
| ⑤ **mandants** vides chez nous | **4** | 18502 · 18831 · 18842 · 18928 |
| ⑥ **réservations** à marquer | **5** | 18424 · 18647 · 18651 · 18787 · 18894 — numéros brûlés, sans mandat |

### B — Les deux tableurs Excel *(Modelo, jusqu'au 26/02/2026)*

| | volume | détail |
|---|---|---|
| ① mandats de **recherche** absents | **22** | 17555 → 18297 |
| ② mandats de **vente** absents | **23** | dont 10 dont nous avons l'annonce, 13 dont l'annonce nous est inconnue |
| ③ ⭐⭐ nos **INCONNUE** que le tableur tranche | **491** sur 503 | **toutes en VENTE** — c'est de loin le plus gros apport |
| ④ nos RECHERCHE que le tableur contredit | 63 | ✅ **déjà corrigé** par le patch `_nature()` du 15/10 |
| ⑤ **noms de chercheurs** fournis | **25** sur 26 | dont **20 appariés** à un contact de notre base |
| ⑥ **mandants** vides chez nous | **14** | |

### Ce que ça donne en tout

```
MANDATS A AJOUTER       38 recherche (16 + 22)  +  25 vente (2 + 23)   =  63
LIGNES A CORRIGER      491 INCONNUE -> VENTE
                         3 natures (registre legal)
                         9 dates
                        18 mandants vides
                         5 reservations a marquer
```

⚠ **Le piège à ne pas oublier** : le fichier protexa écrit « 8 682 » là où le registre
légal dit **18 682**. Or 8682 existe chez nous — une **vente de 2014**. Tout import doit
refuser un numéro déjà présent avec une autre nature et une date incompatible.

---

## 10. ADAPTER LES TROIS ÉCRANS — un mandat de recherche ne marche pas comme une vente

### ① La table `app_mandat` — ✅ **FAIT le 15/10**

`app_contact_id` + `hektor_contact_id`, et `hektor_annonce_id = ''`. La clé ne bouge pas.

### ② La vue « Registre des mandats » — ⬜ à faire

Les 9 colonnes de l'écran sont **toutes pensées pour un bien**. Ce qu'elles deviennent :

| colonne | mandat de VENTE | mandat de RECHERCHE |
|---|---|---|
| N° de mandat | le numéro + le n° de dossier | le numéro + **rien** *(pas de dossier)* |
| Statut du mandat | Actif / Échu / Clos, sur les dates | ✅ **identique** |
| État | l'état de l'**annonce** | ⛔ pas d'annonce → **l'état de la recherche** (active / archivée) |
| Date de début / fin | ✅ | ✅ **identique** |
| Montant | le prix de l'annonce | ⛔ → le **budget** de la recherche |
| Mandant(s) | les propriétaires | → **l'acquéreur** qui nous mandate |
| Nature et situation | type de bien + adresse | ⛔ → **critères + communes cherchées** |
| Actions | « Fiche bien » · « Hektor » | → « **Fiche contact** » · « Hektor » |

⚠ Et le clic : sur **bureau** la fiche s'ouvre déjà sans annonce ; sur **mobile** elle est
**muette** (`if (row?.app_dossier_id)`), à réparer.

### ③ Le registre des contacts — ⬜ à faire

Mesure du 15/10 : la fiche contact porte **4 rubriques** — *Activité récente*,
*Annonces liées*, *Coordonnées CRM*, *Recherches acquéreurs*. **Aucune rubrique
« Mandats ».** Un mandat de recherche appartient pourtant au contact : il doit y figurer,
à côté de « Recherches acquéreurs » dont il est l'acte juridique.

---

## 11. CE QUI A ÉTÉ FAIT LE 15/10 — et la décision de Frédéric

### Écrit en base

| | volume | où |
|---|---|---|
| **5 colonnes** sur `app_mandat` | — | local **et** Supabase · `app_contact_id`, `hektor_contact_id`, `nature_app`, `type_app`, `source_app` |
| **`_nature()`** ne devine plus sur la note | 63 lignes au run | `phase2/sync/mandat_ledger.py` |
| **natures retrouvées** | **502** (+119 types) | `nature_app` / `type_app`, source `modelo` |
| **mandats de recherche ajoutés** | **38** | `hektor_annonce_id = ''` + `app_contact_id` · 32 contacts retrouvés |
| **mandats de vente ajoutés** | **9** | mandats **antérieurs** d'annonces qu'on a · 8 contacts |

```
registre : 26 859  ->  26 906 lignes
```

### ⛔ LA DÉCISION DE FRÉDÉRIC, 15/10 : *« non il ne faut pas »*

> **Un mandat de vente dont nous n'avons pas le bien N'ENTRE PAS avec `annonce = ''`.**

Le vide garde **un seul sens** — *« ce mandat n'a pas de bien »*, c'est-à-dire un mandat
de recherche. Lui faire dire aussi *« le bien nous est inconnu »* mélangerait deux choses
différentes dans la clé du registre légal.

➡ **14 mandats restent dehors, et c'est assumé** :

```
B  13  la reference produit nous est inconnue (biens d'avant la migration)
C   1  18455 — Mme FERRIER Karine, aucune reference
D   1  18500 — un AVENANT avec son propre numero d'ordre au registre legal
```

**Le registre porte un trou connu et documenté plutôt qu'une ambiguïté de structure.**
À rouvrir le jour où ces biens descendront, ou si la forme des avenants est tranchée.

⭐ **Et un bien d'essai a été écarté à la main** : `17460`, *« M. GERPHAGNON Test Franck »*,
annonce 25204 archivée. Écrit dans le code, pas seulement décidé.

### Les pièges payés dans la journée — pour qu'ils ne reviennent pas

```
① « 8 682 »            le fichier protexa a perdu un « 1 » ; 8682 existe chez nous,
                       c'est une VENTE DE 2014. Un import naif l'ecrasait.
② le PDF colle         nom ET adresse dans la meme cellule -> 0 contact retrouve sur 16.
                       L'EXCEL du meme registre a des COLONNES : 29 sur 38.
③ xlrd rend des FLOTTANTS  18420.0 -> « 184200 » en retirant les non-chiffres.
                       Tous les temoins sortaient ABSENT, le fichier etait bon.
④ famille ecrite EN DUR    mes 22 sortaient en PROTEXA alors que les 716 mandats de
                       la meme epoque sont TOUS en HEKTOR. Le type ne s'invente pas :
                       l'export donne `exclusivity` (SIMPLE/EXCLUSIF/ACCORD).
⑤ garde d'idempotence posee TROP TOT   le script refusait les lignes qu'il avait
                       posees -> aucun correctif ne pouvait plus les atteindre.
                       L'idempotence vient du ON CONFLICT, pas d'un refus en amont.
⑥ offre_type a NULL    la ligne est ECRITE mais JAMAIS VUE : le registre n'affiche
                       que offre_type IN ('0','10','6').
⑦ hektor_annonce_id    text dans app_console_job, bigint dans app_dossier_current.
                       PostgREST convertit tout seul, le SQL non : sonde verte, patch casse.
```

---

## 12. LE LOT ① « CORRIGER LE RESTE » — CLOS LE 15/10, SANS RIEN ÉCRIRE

Frédéric a demandé de le faire. **L'audit l'a vidé de trois quarts de son contenu, et la
décision finale est « laisse ».** Ce n'est pas un report : c'est une mesure.

### ⛔ 1e — les réservations : IL N'Y A RIEN À MARQUER

Le registre légal montre 10 numéros comme de simples « RESERVATION ». Mesure : **5 d'entre
eux sont chez nous comme de VRAIS mandats, avec leurs mandants** —

```
18424 ann.11705 VENTE  M. Laurent LIVEBARDON        18787 ann.24113 VENTE  PHILIBERT x5
18647 ann.62328 VENTE  SEIGNIER / FABRE             18894 ann.63132 VENTE  HERRMANN x2
18651 ann.59574 INCONNUE  MONNERET x3
```

⭐ **Sur ces 5 lignes, NOTRE registre est plus complet que le PDF certifié.** Les 5 autres
(18566, 18578, 18745, 18746, 18862) sont absentes de chez nous : ce sont de vraies
réservations sans corps de mandat. **Aucun geste.**

### ⛔ 2f — les honoraires : CE N'EST PAS UNE CORRECTION

`app_mandat` n'a **aucune colonne de montant** : `montant` a été retiré le 06/10 (recopie
exacte de `versions_json[0].montant`). Les poser demanderait une **colonne neuve** — c'est
un ajout, hors de ce lot.

### ⛔ 2e — les mandants vides : LE PROJET LES REMPLIT DÉJÀ

134 lignes sans `mandants_texte`, dont 4 que le registre légal pourrait remplir. Mesure :
**3 sur 4 sont déjà couvertes par notre registre des liens** (mécanisme du 05/10,
`charger_mandants_du_registre_des_liens` va chercher dans `app_relation` quand la colonne
est vide) :

```
18502  nos liens donnent  ANDREE VAUX · CHRISTIANE BOHER · STEPHANIE VAUX · AMANDINE VAUX
18831  nos liens donnent  Petra COSTE · M. Guy COSTE
18928  nos liens donnent  Manuel MARTINS FERNANDES + 3
18842  ⛔ RIEN -- et c'est 62966, LE BIEN D'ESSAI
```

**Le seul vide réel est un bien d'essai. Aucun geste.**

### 2d — les dates : 6 écarts RÉELS, et c'est tout ce qui restait

```
  n°      chez nous      le legal       mandant             ecart
18437     2026-03-10  -> 2026-03-09     BONNEFOY = BONNEFOY   1 jour
18502     (vide)      -> 2026-04-02     VAUX ANDREE
18536     2026-11-16  -> 2026-04-16     EYMARD  = EYMARD      ⚠ 7 MOIS
18570     2026-01-28  -> 2026-04-30     RABY    = RABY        ⚠ 3 MOIS
18911     2026-10-05  -> 2026-10-01     CHALEAT = CHALEAT     4 jours
18928     (vide)      -> 2026-10-07     MARTINS FERNANDES
```

⭐ **Les mandants concordent sur les 6** : aucune collision de numéro, ce sont bien les
mêmes mandats. **18536 porte novembre 2026 là où le registre légal dit avril** — une faute
de saisie chez Hektor, sur une date qui a une valeur juridique.

**Deux façons, présentées le 15/10 :**

```
A  une colonne `date_debut_app`, meme patron que nature_app
   -> coherent, mais une colonne de plus pour 6 lignes
B  corriger CHEZ HEKTOR, a la main, depuis la fiche mandat
   -> la date redescend seule, le defaut disparait A LA SOURCE
```

### ➡ DÉCISION DE FRÉDÉRIC, 15/10 : **« Laisse »**

Aucune des deux. Les 6 écarts restent, **connus et écrits ici**. 18536 et 18570 sont de
vraies fautes de Hektor : si elles gênent un jour, la voie **B** est la bonne — ce n'est
pas à nous de recouvrir une erreur de saisie par une colonne de compensation.

**Le lot ① est clos. Rien n'a été écrit.**

---

## 13. 27/10/2026 — LES 518 RECHERCHES DU REGISTRE LÉGAL 2014-2024 SONT ENTRÉES

Décision de Frédéric (27/10) : *« oui »* aux recherches 2014-2024, locations et gestions exclues ;
les ventes sans bien connu restent dehors (**décision du 15/10 confirmée**, choix B).

- `importer_mandats_recherche.py` lit `Ancien registre des mandat.csv` (objet « recherche », réservés et
  annulés écartés) : **518 posées**, même patron qu'au 15/10 (`hektor_annonce_id = ''`, plage du run,
  `present_in_hektor = 0`, piège « 8 682 » : 59 numéros refusés). Contact retrouvé 381 / 556.
- Défaut corrigé dans les deux portes : les dates Modelo (UTC) étaient prises **la veille** → `date_paris()`.
- Détail, chiffres et retour arrière : `notice/ETUDE_CORRESPONDANCES_APP_CLASSEURS_2026-10-27.md` §11 sexies.
- ⚠ **L'étape 4 de ce plan reste à faire** : le clic MOBILE sur un mandat sans bien est toujours muet
  (`App.tsx:24277`, `if (row?.app_dossier_id)`) — il touche maintenant 556 lignes au lieu de 38.
