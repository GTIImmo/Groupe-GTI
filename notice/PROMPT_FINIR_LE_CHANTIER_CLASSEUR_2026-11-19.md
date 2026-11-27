# ⭐⭐⭐ FINIR LE CHANTIER CLASSEUR — le dossier de reprise COMPLET
### Écrit le 19/11/2026 par la conversation qui tient le chantier. Il remplace les dossiers V2 et V3.

> ⛔⛔⛔ **QUI TIENT LE CHANTIER.** Il est conduit par **cette** conversation, et c'est d'elle
> que tu prends la suite. **Deux AUTRES sessions** ont produit **des pièces, pas la conduite** :
> un rapport d'audit + un patch du gel (18/11), un second audit + un patch affiné (19/11).
> **Aucun des deux patchs n'a jamais été joué.** Ils se vérifient, ils ne se recopient pas.
>
> ⭐⭐ **L'ORDRE EST CELUI DE FRÉDÉRIC, posé le 19/11 :** *« j'aimerais que nos écritures de
> script de masse soient recontrôlées afin de vérifier si elles n'ont pas perturbé ou cassé du
> chaînage. Pour cela il faudrait faire une vérification de tout mon registre des transactions
> dans mon app. Pas le gel, mais vérifier mon registre. Et ensuite, oui, le gel qui a été fait
> et refait pour être utilisé et finir enfin ce chantier. »*
> ➡ **Le REGISTRE d'abord, le GEL ensuite, la BASCULE pour finir.**

---

## 0. ⭐⭐⭐ LE PROMPT À COLLER DANS LA CONVERSATION NEUVE

```
Tu reprends le chantier classeur du projet Hektor (depot C:\Hektor\Projet) et tu le FINIS.

C'EST CE CHANTIER-LA QUE TU REPRENDS, celui conduit par la conversation qui a ecrit le
dossier ci-dessous. DEUX AUTRES sessions ont seulement produit DES PIECES : un rapport
d'audit + un patch du gel (18/11), un second audit + un patch AFFINE (19/11). Aucun des
deux patchs n'a ete joue. Elles se verifient, elles ne se recopient pas.

AVANT TOUT : lis notice/PROMPT_FINIR_LE_CHANTIER_CLASSEUR_2026-11-19.md EN ENTIER, puis
les pieces qu'il liste a son paragraphe 3, dans l'ordre qu'il donne.

LE BUT DU CHANTIER : (1) le classeur Google Sheet FAIT FOI, on met notre base en
conformite avec lui -- il remplit les vides ET corrige les divergences ; (2) puis LA
BASCULE : on saisit dans l'app, plus dans le classeur. Le classeur ne ferme pas, il
change d'ecrivain.

LA CHAINE DE CORRESPONDANCE, et c'est la clef de tout :
   ligne du Sheet --(LE GEL, app_classeur_lien)--> numero de transaction (ne bouge jamais)
   transaction ---(LE CHAINAGE, rededuit CHAQUE NUIT)--> le dossier --> l'etiquette
   etiquette (app_dossier_uuid) --(etape 5.2)--> la colonne affair_uuid du Sheet
Le gel est un ECHAFAUDAGE : il sert une fois de plus, pour la 5.2, puis il dort. Le
REGISTRE DES TRANSACTIONS (app_affaire_ledger) et son CHAINAGE sont le MUR.

⛔⛔ ET NE CONFONDS PAS LES DEUX, C'EST LE PIEGE N° 1 (je m'y suis fait prendre le 19/11,
Frederic m'a corrige) : LE CHAINAGE BOUGE, L'ETIQUETTE NE BOUGE PAS. Les quatre gestes de
la pose la preservent : une scission donne une etiquette NEUVE a la part DETACHEE et le
dossier d'origine GARDE la sienne ; une fusion garde LA PLUS ANCIENNE ; une propagation
fait PRENDRE l'etiquette existante. Ce qui bouge, c'est l'APPARTENANCE d'une transaction
a un dossier -- jamais l'identifiant du dossier. Le § 13 ① le prouve, journal a l'appui.

TA MISSION, EN CINQ TEMPS, ET L'ORDRE NE S'INVERSE PAS. Tu m'expliques clairement
a la fin de CHAQUE temps, et tu ecris ton resultat dans un fichier de notice/ avant de
passer au suivant (sinon tout meurt avec la conversation : c'est deja arrive).

TEMPS 1 -- L'INVENTAIRE DE NOS ECRITURES DE MASSE. Tu ne me crois pas, tu ne crois pas
les notes : tu lis app_console_job, c'est la source de verite. Pour chaque campagne :
le script d'origine, la date, le nombre, l'etat_avant et l'etat_apres (la charge les
porte, je l'ai verifie), et ce qui a echoue. Tu me rends la liste complete, y compris
les campagnes que personne n'a encore nommees.

TEMPS 2 -- LE REGISTRE JUGE SUR LUI-MEME, SANS LE GEL. Tu auditees app_affaire_ledger
par ses INVARIANTS (le § 6 du dossier donne l'etat de depart et les six invariants
deja mesures). Tu ne compares RIEN au classeur a ce stade : le registre doit se tenir
debout seul. Tu chiffres chaque anomalie, tu la nommes, et tu dis ce que tu n'as pas
mesure. ⛔ Et tu balaies les GESTES autant que les OBJETS : creer, modifier, supprimer,
lire -- pour l'offre, le compromis, la vente, le dossier et l'etiquette.

TEMPS 3 -- CE QUE NOS GESTES ONT FAIT AU CHAINAGE, PROUVE. Il n'existe AUCUNE photo
complete du registre d'avant (verifie : les sauvegardes datees ne portent que les lignes
touchees). Mais l'etat d'avant est RECONSTITUABLE depuis app_console_job, et le chainage
est une fonction REJOUABLE : le projet l'a deja fait quatre fois (« vraie fonction, copie
en memoire, temoin 31 145/31 145 »). Donc : tu reconstitues l'etat d'avant des 1 233
gestes, tu REJOUES le chainage dessus EN MEMOIRE, EN LECTURE SEULE, et tu compares les
chaines d'avant a celles d'aujourd'hui. Tu me dis combien de chaines ont change, dans
quel sens, et lesquelles sont une CASSE et non une correction. Avec temoin positif ET
temoin inverse. ⛔ Lis d'abord le § 8.3 : deux fausses pistes y sont deja eteintes, ne
les refais pas.

TEMPS 4 -- LE GEL. Il a ete fait et refait ; il reste a s'en servir. Tu reprends le patch
affine (45 retraits, 78 ajouts, dormant, deja controle par moi), tu le revalides contre
la base du jour, tu traites ce qui l'accompagne (les 16 traces a reposer, les copies de
C5 des deux cotes, le 4e tour, le seuil de la sentinelle), et tu me soumets GROUPEES les
questions qui restent -- il y en a 32 ecrites, plus une muette.

TEMPS 5 -- FINIR. Tu REAUDITES la faisabilite des etapes 4 et 5 (le § 10), tu dis ce qui
est BLOQUE et par quoi, et tu me proposes LA MEILLEURE METHODE pour arriver au bout --
la tienne, argumentee, avec deux ou trois chemins quand il y a un choix, leur cout et
leur risque, et ta recommandation. Tu ne decides pas un perimetre seul.

CE QUI NE SE DISCUTE PAS :
  . tu ecris UNIQUEMENT en francais, et JAMAIS de tableaux dans tes messages ;
  . ACCORD OBLIGATOIRE avant toute ecriture en base de production, toute ecriture chez
    Hektor, tout run, tout redemarrage, tout deploiement, tout geste irreversible ;
  . tu MESURES avant de conclure, et tu DIS ce que tu n'as pas mesure ;
  . un patch porte son `commit;` : joue « pour voir », IL SE COMMITE ;
  . tu stages fichier par fichier (jamais git add .), tu relis le stage juste avant le
    commit et la liste a pousser juste avant le push ; `git commit -m` n'existe plus,
    tout message passe par un fichier et -F ;
  . tu n'ecrases rien : additif et chirurgical, derriere un interrupteur quand c'est
    possible.

COMMENCE PAR LE TEMPS 1 et explique-moi ce que tu trouves avant d'aller plus loin.
```

---

## 1. ⭐⭐ MON CONSEIL DE MÉTHODE — pourquoi cet ordre, et les six questions qui tranchent

**Pourquoi un seul chat, et pas deux.** Deux sessions ont travaillé en parallèle les 18 et
19/11. Résultat : deux rapports, deux patchs dont le second refait le premier, et une
réconciliation à faire par une troisième. Le travail était bon, mais une partie a été payée
deux fois. **Un seul fil, et des pièces écrites.**

**Pourquoi le registre AVANT le gel.** Le gel s'accroche à la **transaction**, qui ne bouge
jamais ; le chaînage, lui, est redéduit chaque nuit. Si le registre ou son chaînage est faux,
tout ce qu'on bâtit par-dessus — les valeurs posées, l'étiquette, et surtout l'écriture de nos
UUID dans le Sheet à l'étape 5.2 — est faux aussi. **Le registre est le mur, le gel est
l'échafaudage.**

**Pourquoi « sans le gel » est la bonne consigne.** 15 211 valeurs du classeur sont déjà
posées dans le registre. Juger le registre en le comparant au classeur mesure donc un accord
**fabriqué** (874 des 897 « accords » du 17/11 étaient circulaires). Un registre se juge sur
**ses invariants** : jamais deux ventes dans un dossier, jamais deux compromis vivants, une
chaîne qui s'ordonne dans le temps. Ça, aucun classeur n'est nécessaire pour le voir.

**Les six questions qui tranchent, dans l'ordre.** Elles valent mieux qu'un plan détaillé :

```
1  QUELLES ecritures de masse ont eu lieu ? -> app_console_job, jamais les notes
2  Le registre respecte-t-il SES PROPRES INVARIANTS, aujourd'hui, sans le classeur ?
3  Pour chaque anomalie : est-elle NEE d'un de nos gestes, ou etait-elle deja la ?
     (c'est le rejeu du chainage sur l'etat d'avant qui repond, pas une intuition)
4  Ce qui a change est-il une CASSE ou une CORRECTION ? (le chainage a souvent RAISON
     de separer : deux acheteurs successifs font deux affaires)
5  Ce qui est casse se repare-t-il par une REGLE, ou seulement A LA MAIN ?
     (une regle derriere un interrupteur, mesuree avant d'etre ecrite ; sinon le
      fichier des rattachements manuels, qui est SA decision)
6  Qu'est-ce qui reste BLOQUE pour la bascule, et par quoi exactement ?
```

**Et les trois pièges de méthode à lui imposer**, parce qu'ils ont tous les trois déjà coûté :

```
. UN ZERO NE SE CROIT PAS SANS TEMOIN POSITIF. « 0 anomalie » peut vouloir dire « ma
  requete ne mesure rien ». Toute mesure a son temoin inverse.
. UN JOURNAL NE SAIT RIEN D'AVANT SA NAISSANCE. L'etiquette est nee le 12/11 : le
  journal des etiquettes ne peut pas juger le geste du 11/11.
. RIEN N'EST FINI TANT QUE CE N'EST PAS ECRIT DANS notice/. Les scripts et les donnees
  de l'audit du 18/11 n'ont survecu que par son rapport ; le reste est perdu.
```

---

## 2. ⛔ CE QUI NE SE DISCUTE PAS

```
. le classeur FAIT FOI, mais il NE FERME PAS : il change d'ecrivain (plan § 2)
. on ne cree NI table NI colonne pour ce chantier (plan § 6)
. la colonne `date` d'une offre NE SE CORRIGE PAS : le run la relit chaque nuit chez
  Hektor, et la protection est NOMMEMENT refusee pour ce couple
  (R2_JUGES_SUR_LE_REGISTRE, affaire_ledger.py l. 1718). ON CORRIGE LES LECTEURS.
  ⚠ le plan cite « l. 1671 » et « l. 1517 » : ces renvois ont GLISSE. Les vrais sont
    1718 et 1564. Un renvoi ne se calcule pas, il se trouve.
. phase2/sync/rattachements_manuels.csv est UNE DECISION DE FREDERIC, pas une donnee :
  « on n'en ajoute JAMAIS une sans lui »
. un numero de chaine ne sert JAMAIS de point d'accrochage (il bouge) : on pointe des
  app_affaire_id
. les 8 lignes INCERTAINES et les 18 lignes A QUESTION OUVERTE sont intouchables tant
  qu'il n'a pas repondu
. une transaction de la plage app se retire DES DEUX COTES (Supabase ET local), dans la
  meme fenetre : le LOCAL est maitre du registre, il la renverrait au push de 04:00
```

---

## 3. L'ORDRE DE LECTURE

```
1  notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md   LE PLAN QUI FAIT FOI. Le § 0 (plan
   actif, reecrit le 12/11), le § 2 (le but), le § 6 (les interdits), et le « PLAN
   DETAILLE DU 15/11 » qui remplace les listes precedentes.
   ⚠ 367 000 caracteres : NE JAMAIS lire en entier, ouvrir par numero de ligne.
2  phase2/sync/affaire_ledger.py                 LE CODE DU REGISTRE ET DU CHAINAGE.
   Les 9 interrupteurs entre 1156 et 1500 . _date_de_tri 1564 . ETATS_OFFRE_MORTS 1539
   R2_JUGES_SUR_LE_REGISTRE 1718 . recalculer_les_chaines 1888
   poser_les_etiquettes_de_dossier 2691
3  notice/AUDIT_INDEPENDANT_CLASSEUR_2026-11-18.md   le rapport de la 1re session
   (+ AUDIT_INDEPENDANT_CLASSEUR_VERDICTS_2026-11-18.csv, et son § 5 ter)
4  notice/AUDIT_INDEPENDANT_V2_2026-11-19.md         le rapport de la 2e session
   (+ ses CSV : MON_APPARIEMENT, GEL_CONTRE_MOI, SES_OPERATIONS_JUGEES,
    OPERATIONS_AFFINEES, TRACES_A_REPOSER)
5  supabase/patch_correction_gel_audit_v2_2026-11-19.sql  le patch AFFINE, DORMANT
   (+ _INVERSE, _REPETITION). Il remplace celui du 18/11.
6  notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_V2_2026-11-19.md  les 13 arbitrages de
   Frederic, les 32 questions ecrites, et les donnees en dur du gel (son § 13)
7  notice/TABLE_DE_CONTROLE_REGISTRE_2026-11-10.csv et _APRES_CHAINAGE.csv
   693 et 726 lignes : la table qui a SERVI A DECIDER le geste du 11/11
8  la memoire projet    C:\Users\admin\.claude\projects\C--Hektor\memory\
   commencer par chainage-255-lignes-deux-causes.md
```

---

## 4. LE CHANTIER EN GLOBALITÉ — les cinq étapes

```
ETAPE 1   LE GEL : poser les liens ligne du Sheet <-> transaction      12 787 liens
          fait et refait (12 422 le 29/10, 12 595, 12 787 aujourd'hui)
          reste : le patch V2 dormant . 91 lignes sans lien . 277 liens « a valider »
ETAPE 2   POSER LES VALEURS du Sheet dans le registre                  15 211 posees
          reste : les 36 lignes tranchees le 18/11 . les 207 non posees . les
          honoraires et la charge de commission
ETAPE 3   JUGER LES DIVERGENCES, une par une                        350 lignes jugees
          reste : 8 INCERTAINES . 18 a question ouverte . 32 questions ecrites + 1 muette
ETAPE 4   LA PORTE D'ECRITURE et les vagues de reprise                       non commencee
ETAPE 5   LA BASCULE : 5.1 les Apps Script (SON geste) . 5.2 nos UUID dans la colonne
          affair_uuid . 5.3 le routeur, et le gel DORT pour toujours
```

⭐⭐ **Et voilà pourquoi l'étiquette vit sur chaque transaction** et non dans une table par
dossier : son rôle n'est pas d'être un point d'accrochage interne, c'est **d'être la clef
partagée avec le Sheet**, celle qu'on écrira dans sa colonne A et qui remplacera
l'appariement pour toujours. Un dossier d'affaire n'est pas un objet chez nous, c'est un
**regroupement** ; ce qui est stable, c'est l'étiquette.

---

## 5. CE QUE CETTE CONVERSATION A FAIT, ET CE QUE LES DEUX AUTRES ONT PRODUIT

### Cette conversation (18-19/11)

```
. lu EN ENTIER le rapport du 18/11 et son patch, et les a controles en lecture seule
  contre la base vivante : 55 retraits et 109 ajouts comptes, garde « 12 787 liens »
  vraie, 0 transaction prise par deux lignes, 0 doublon, les deux listes de retraits
  de MEME empreinte md5 -> le patch tournerait
. TROUVE TROIS RESERVES, toutes reprises ensuite : il detournait `etage` et `preuves`
  (deux colonnes de MESURE) . il renvoyait 6 fois a un « § 5 ter » absent . il touchait
  18 lignes a question ouverte
. CONFRONTE les 13 arbitrages de Frederic : 1 identique, 2 doutes confirmes, 2 A MOITIE
  FAITS (« defaire ET creer » : les patchs ne defont que), 3 non contredites, 5 absentes
. EXTRAIT les 32 questions ecrites du CSV (la 33e, SHN6RKDI, est muette)
. CONTROLE le patch V2 de la 2e session : 45 et 78 recomptes, 12 787 - 45 + 78 = 12 820
. MESURE le chainage, le registre et nos ecritures de masse -- les § 6, 7 et 8
```

### La 1ʳᵉ session (18/11) — un rapport et un patch

Audit du Sheet contre le registre, **appariement fait sans le gel** : 4 402 lignes en accord
prouvé, 350 jugées, 107 contre-expertises. Le pont le plus fort : **la référence Netty de
l'agence (VM…/VA…) est le numéro de dossier Hektor**, donc l'annonce, pour 646 lignes. Quatre
familles d'erreurs, dont **les affaires croisées entre acheteurs successifs** (11 paires) et
**25 copies de transactions Hektor créées par C5**.
⛔ **Son patch (55 retraits, 109 ajouts) est remplacé. Ne pas le jouer.**

### La 2ᵉ session (19/11) — un second audit et le patch affiné

Son propre appariement arrêté **avant** toute lecture du gel : 4 796 lignes (4 567 certaines,
159 solides, 68 biens sans transaction, 2 sans rien), 12 621 rattachements. Puis la
comparaison (133 de ses 141 opérations soutenues), puis le patch affiné. Elle a trouvé seule
**les 501 lignes où le contact acquéreur change à l'intérieur d'une chaîne Hektor** — une
trouvaille majeure, qui invalide tout appariement jugeant le nom transaction par transaction.

**Le patch affiné** — `supabase/patch_correction_gel_audit_v2_2026-11-19.sql`, **DORMANT** :
45 retraits, 78 ajouts, le gel de 12 787 à 12 820, les lignes sans lien de 91 à 71. Mes trois
réserves corrigées, plus trois renforts : la garde lit l'**empreinte** du gel, elle vérifie
avant d'écrire que **chaque cible sera libre**, et le retour arrière ne juge que sa part.
✅ **Contrôlé le 19/11, il attend son « vas-y ».**

⛔ **CE QUE NI L'UNE NI L'AUTRE N'A FAIT : le registre et le chaînage.** Dans les 569 lignes
du rapport V2, « rapatriement » n'apparaît pas une fois, « 5.2 » pas une fois. Leurs six
gestes suivants sont tous du ménage autour du gel.

---

## 6. ⭐⭐⭐ LE REGISTRE JUGÉ SUR LUI-MÊME — état de départ, mesuré le 19/11

**`app_affaire_ledger` : 31 359 transactions, 11 590 dossiers.** Les invariants :

```
dossiers a DEUX VENTES ou plus                    0   ✅ l'invariant dur tient
dossiers a DEUX COMPROMIS VIVANTS                 0   ✅ l'invariant dur tient
dossiers a cheval sur DEUX BIENS                  0   ✅
dossiers a DEUX OFFRES ACCEPTEES                  2   ⚠ a juger
dossiers a UNE SEULE transaction              1 472   ⚠ dont 589 offres du 11/11
ventes SANS AUCUNE OFFRE                        461   ⚠ a juger (normal ? ancien ?)
dossiers a DEUX ACQUEREURS ou plus            2 246   ⭐ NORMAL : le contact change
                                                       dans la chaine chez Hektor
transactions prises par DEUX lignes du Sheet       0   ✅ l'exclusivite du gel tient
transactions creees depuis le Sheet              190   dont 135 SEULES dans leur dossier
```

⭐ **Les deux invariants durs du projet tiennent à zéro.** Le registre n'est pas en ruine :
ce qu'il faut juger, ce sont les solitaires, les 461 ventes sans offre et les 2 doubles
acceptations. **Et cette liste n'est pas exhaustive — c'est un point de départ, pas un
audit.** Six invariants de plus restent à écrire : l'ordre des dates dans une chaîne, une
offre refusée postérieure à sa vente, un compromis sans mandat, une transaction sans bien,
un acquéreur absent, une chaîne dont tous les membres sont morts.

---

## 7. ⭐⭐⭐ NOS ÉCRITURES DE MASSE — l'inventaire, et comment reconstituer l'« AVANT »

### 7.1 Ce que le journal des travaux porte

```
11/11  change_hektor_offre_status   1 185  done   <- le refus des offres mortes
12/11  change_hektor_offre_status      36  done
12/11  cancel_hektor_compromis         12  done   <- JAMAIS NOMMEE DANS AUCUN RAPPORT
18/11  creation de 136 transactions depuis le Sheet (C5) -> 138 scissions la meme nuit
```

⛔ **Les 12 compromis annulés du 12/11 n'apparaissent dans aucun rapport.** C'est le genre de
campagne que le temps 1 doit trouver : **le journal, jamais les notes.**

### 7.2 ⭐⭐⭐ L'« AVANT » EXISTE, ET VOICI OÙ

**Il n'y a AUCUNE photo complète du registre d'avant** — vérifié : les sauvegardes datées ne
portent que les lignes touchées (178, 5, 2 et 1 lignes), pas les 31 359.

**Mais chaque travail porte son propre avant.** Relevé sur le premier geste du 11/11 :

```json
{"type":"refus","origine":"enqueue_refus_offres_mortes_lot","decide_par":"fichier 27/02",
 "etat_avant":"accepted","etat_apres":"refused","app_affaire_id":473,
 "hektor_offre_id":"10174","hektor_annonce_id":"1309","sans_resynchro":true,
 "table_de_controle":"TABLE_DE_CONTROLE_REGISTRE_2026-11-10_APRES_CHAINAGE.csv"}
```

➡ **`etat_avant`, `etat_apres`, `app_affaire_id` et le script d'origine, pour chacun des
1 233 gestes.** L'état d'avant du registre est donc **reconstituable en lecture seule**.

### 7.3 ⭐⭐ Et le chaînage est REJOUABLE — la méthode existe déjà dans le projet

`recalculer_les_chaines` (affaire_ledger.py l. 1888) recalcule tout depuis le registre. Les
quatre règles A, B, C et D ont **toutes** été éprouvées comme ça avant d'être écrites :
*« simulation du 10/11, vraie fonction, copie en mémoire, témoin 31 145 / 31 145 »*.

**La méthode du temps 3, donc :** reconstituer l'état d'avant depuis `app_console_job` →
rejouer la vraie fonction de chaînage sur cette copie **en mémoire, sans écrire une ligne** →
comparer la composition des chaînes d'avant à celle d'aujourd'hui → compter, nommer, et
distinguer la **casse** de la **correction**. Avec témoin positif et témoin inverse.

⭐ Et il reste trois photos utilisables pour recouper : `app_etiquette_journal_avant_20261112`,
`app_etiquette_avant_repose_20261112` et `app_etiquette_compteur_avant_20261112`.

---

## 8. L'ÉTAT DU CHAÎNAGE — ce qui est déjà mesuré, et les deux fausses pistes éteintes

### 8.1 Il est stable, hors nos gestes

Journal `app_dossier_etiquette_journal` :

```
12/11   pose initiale              11 441 dossiers . 31 151 transactions
13/11   5 fusions . 4 poses . 2 scissions . 1 propagation
14/11   2 scissions
17/11   2 poses . 2 propagations
18/11   138 SCISSIONS . 142 transactions      <- nos 136 creations depuis le Sheet
19/11   1 scission . 1 propagation . 2 poses
```

⭐ Deux à neuf transactions par nuit. Il *peut* bouger chaque nuit ; en pratique **il ne bouge
que quand on le secoue.**

### 8.2 Les 255 lignes à plusieurs étiquettes — le bouchon de la 5.2, décomposé

```
4 703 lignes du Sheet liees
  255 portent PLUSIEURS etiquettes
    136 ont une transaction creee depuis le Sheet       <- la scission du 18/11
    119 n'en ont AUCUNE
         96 de la forme offre/refused + compromis/cancelled, MEME BIEN :
              65  DEUX ACHETEURS DIFFERENTS -> le CHAINAGE A RAISON. C'est le GEL qui
                  tient deux affaires sur une seule ligne. (La 1re session en avait
                  vu 11 : il y en a 65.) Exemples : offre SINTEZ refusee le 10/01/2020
                  + compromis CHABROT annule le 13/03/2020 (ligne 0IS41BM1) ; offre
                  TRIOMPHE + compromis BOUAMAR (13KBCS85) ; PENY + ISSARTEL (1X9W3VUF)
              24  l'offre porte la date du geste du 11/11, nom different -> a juger
               5  le geste du 11/11 ET LE MEME NOM : BHMANOK7 (BOUGEARD) . H3SQXY47
                  (ARSAC ET DUMAS) . R2U574AC (ROCHELEMAGNE) . U258U4CX (MILHAS) .
                  WUQ5445T (PARIS) -- mais leurs NUMEROS d'acquereur DIFFERENT, donc
                  c'est le meme acheteur sous DEUX fiches Hektor : la regle « meme
                  acheteur » s'abstient A JUSTE TITRE -> fichier manuel, pas une regle
               2  MEME nom ET MEME numero, et pourtant separes : 5QE9107L (DEBARD,
                  acquereur 338966, bien 41481) et 8SZDU4F5 (POCHELON, 546711, 39745)
                  -> dans les deux cas le compromis est SANS DATE : VRAI TROU DE REGLE
         23 autres formes : NON CLASSEES, a faire
```

⚠ **Le remède écrit dans les deux rapports — rattacher les 136 à la main — ne couvre donc
que 53 % du bouchon.** Et la simulation du patch du gel fait passer les 255 à **243** : il en
règle 12, par ricochet.

### 8.3 ⛔⛔ LES DEUX FAUSSES PISTES — déjà suivies, déjà éteintes. Ne pas les refaire.

**① « Le geste du 11/11 a cassé le chaînage par la date. » FAUX.** Le chaînage ordonne une
offre sur **sa première proposition** (`_date_de_tri`, l. 1564, corrigé le 16/09), et ne
retombe sur la colonne `date` que si les propositions sont illisibles. **Les 113 offres
suspectes ont TOUTES un `propositions_json` rempli — 113 sur 113.** Le repli ne joue jamais.
Leur isolement vient de l'**ÉTAT** : une offre `refused` est une offre morte
(`ETATS_OFFRE_MORTS`, l. 1539), et une offre morte ne porte pas de compromis — elle ouvre et
ferme sa propre chaîne. **C'est le dessin, pas un accident.** ➡ La vraie question n'est donc
pas « la date a-t-elle cassé la chaîne » mais **« avions-nous raison de refuser ces offres »**
— et ça, seule la table de contrôle du 10/11 et sa décision du 27/02 peuvent le dire.

**② « 33 lignes à cheval le 12/11, 255 aujourd'hui, donc le chaînage s'est dégradé. »** Pas
établi. Le journal n'explique que 142 des 222 : il reste **~80 lignes inexpliquées**. ⚠ Et
le GEL a grossi sur la même période (12 422 → 12 787 liens) : **un lien neuf peut faire
basculer une ligne dans les « à cheval » sans que le chaînage ait bougé d'un pouce.**
➡ **Commencer par cette soustraction.** C'est une mesure, pas une enquête.

### 8.4 ⭐ LE TROU DE RÈGLE, mesuré sur tout le registre

La règle « même acheteur » réunit deux chaînes du même bien qui partagent un acquéreur, avec
deux gardes (jamais deux ventes, jamais deux compromis vivants). Mais **une transaction SANS
DATE n'entre jamais dans la liste des chaînes du bien** — c'est écrit pour la règle A — donc
la règle « même acheteur » **ne la voit pas** :

```
13 439 couples (bien, acquereur Hektor)
    63 portent PLUSIEURS etiquettes        <- la regle devrait les avoir reunis
       41 ont au moins une transaction SANS DATE   <- la cause probable
       22 sont toutes datees                       <- autre cause, a trouver
    41 des 41 se reuniraient SANS violer les deux gardes
```

➡ **41 réunions franches à gagner.** ⛔ À confirmer dans le code avant d'écrire quoi que ce
soit : que la cause est bien l'absence de date, et non une abstention volontaire.

### 8.5 Ce qui existe déjà, et qu'il ne faut PAS réinventer

**Les 9 interrupteurs sont TOUS allumés dans `.env`** — le chaînage tourne déjà dans sa
version améliorée, règles A, B, C et D comprises :

```
APP_CHAINAGE_V2=1                      APP_CHAINAGE_OFFRE_ACCEPTEE_SEULE=1   (regle B)
APP_CHAINAGE_SANS_DATE=2               APP_CHAINAGE_COMPROMIS_ANNULE_SEUL=1  (regle A)
APP_CHAINAGE_OFFRE_PROPOSEE=1          APP_CHAINAGE_MEME_ACHETEUR=1          (regle D)
APP_CHAINAGE_OFFRE_SANS_DATE=1         APP_CHAINAGE_RATTACHEMENT_MANUEL=1
APP_CHAINAGE_VENTE_SEULE=1  (regle C)  APP_ETIQUETTE_DOSSIER=1
```

Et `phase2/sync/rattachements_manuels.csv` est **branché et vivant**, avec **6 décisions** de
Frédéric. Il refuse une ligne dont les deux transactions ne sont pas sur le même bien, et
l'écrit au journal. **C'est la seule mémoire qui survit au recalcul de chaque nuit.**

---

## 9. ⛔⛔ LES DEUX PIÈGES DE FOND DU CHANTIER

**① L'ACCORD CIRCULAIRE.** 15 211 valeurs du classeur sont déjà posées dans le registre.
Comparer le Sheet au registre mesure un accord **fabriqué** : 874 des 897 « accords » du
17/11 l'étaient. Un appariement indépendant **ne lit ni le gel, ni aucune colonne `*_app`**,
et écarte les 190 transactions `transaction_origine='classeur'`.

**② LE NOM N'EST UNE PREUVE DANS AUCUN DES DEUX SENS.**
Chez Hektor **le contact change à l'intérieur d'une chaîne** (501 lignes mesurées) : offre au
nom de l'un, compromis et vente au nom de l'autre, les trois dates au jour près. À l'inverse,
**le même acheteur porte parfois DEUX fiches contact** (26 paires mesurées) — c'est pourquoi
la règle « même acheteur » compare **les numéros, jamais les noms** (un nom de famille partagé
est un couple ou un homonyme dans 109 cas mesurés).
➡ **Ce qui tranche, c'est la date au jour près, et la preuve interne.**

---

## 10. FINIR LE CHANTIER — les étapes 4 et 5, et leurs blocages connus

```
ETAPE 4 -- LA PORTE ET LES VAGUES DE REPRISE
  ⛔ app_modifier_affaire_optimistic EXIGE un utilisateur admin ou gestionnaire connecte
    (is_app_manager_or_admin() lit auth.uid()), un numero Hektor, et une transaction
    ENCORE PRESENTE chez Hektor. Une « porte sans ecran » appelee par un script n'a pas
    d'utilisateur -> QUI SIGNE LE GESTE est a trancher avec lui avant d'ecrire 4.1.
  ⚠ Ce que la reprise enverrait REELLEMENT chez Hektor n'est pas mesure : commission,
    charge, facture, reglement et annulation n'ont pas de case chez lui.
  ⛔ 14 chaines du classeur sont ENTIEREMENT MORTES chez Hektor : une reprise qui exige
    « presente chez Hektor » ne les touchera jamais.

ETAPE 5 -- LA BASCULE
  5.1  LES APPS SCRIPT DU SHEET -- c'est SON geste, 10 min, et il BLOQUE le reste
  5.2  ecrire nos UUID dans la colonne affair_uuid
       ⛔ BLOQUE par les 255 lignes a plusieurs etiquettes (§ 8.2) ET par les 14 chaines
         mortes. Deux options a lui soumettre, chiffrees : rattacher a la main, ou
         CHOISIR l'etiquette a l'export.
  5.3  le routeur : l'app lit le Sheet par l'UUID, et LE GEL DORT POUR TOUJOURS
```

---

## 11. LES ADRESSES — contrôlées une par une le 19/11

```
phase2/sync/affaire_ledger.py             le registre, le chainage, les etiquettes
phase2/sync/rattachements_manuels.csv     les decisions manuelles (branchees, 6 lignes)
phase2/sync/pull_from_supabase.py         la descente Supabase -> local
app_affaire_ledger                        le registre -- le LOCAL est maitre
app_classeur_lien                         le gel -- SUPABASE est maitre
app_dossier_etiquette_journal             le journal des mouvements d'etiquette
app_console_job                           LE JOURNAL DES TRAVAUX : payload_json porte
                                          etat_avant / etat_apres de chaque geste
monitoring/check_gti_health.py:817        sentinelle data.classeur_ligne_sans_lien,
                                          seuil 92 -- a suivre apres tout geste sur le gel
Console/apply_sql_patch.js                jouer un patch
Console/enqueue_refus_offres_mortes_lot.js             le geste du 11/11
Console/enqueue_reaccepter_offres_refusees_a_tort.js
Console/enqueue_fermeture_dossiers_impossibles.js
notice/TABLE_DE_CONTROLE_REGISTRE_2026-11-10.csv       la table qui a servi a decider
notice/TABLE_DE_CONTROLE_REGISTRE_2026-11-10_APRES_CHAINAGE.csv
```

**Les horaires réels** (le CLAUDE.md en annonce d'autres, il est périmé) : **GTI Quotidien
04:00**, **GTI Descente 06:45**. ⭐ **Aucun run, aucune tâche planifiée n'écrit dans le gel** —
aucune fenêtre ne se ferme pour le patch. ⚠ En revanche **le push de 04:00 renvoie le registre
LOCAL vers Supabase** : une transaction retirée d'un seul côté revient.

---

## 12. ⛔ LES DÉCISIONS QUI L'ATTENDENT

```
1  LES DEUX DATES D'OFFRE (QH6672TZ, 74IL9C8F) : creer une colonne chez nous, ou corriger
   chez Hektor ? ⚠ le journal Hektor porte lui-meme la mauvaise annee (23488 ->
   2002-01-31, 24448 -> 2020-08-07)
2  LA REGLE « TOUTES » : repasse-t-on sur les 66 valeurs deja posees ?
3  JOUER OU NON LE PATCH DU GEL V2 (45 retraits, 78 ajouts), pret et controle
4  LES 136 TRANSACTIONS COUPEES : rattacher a la main, ou choisir l'etiquette a l'export ?
5  LES 32 QUESTIONS ECRITES + la muette (SHN6RKDI), a lui soumettre GROUPEES
```

Et **cinq arbitrages du 18/11 ne sont traités par personne** : la règle « toutes », l'offre
4281 à réparer chez Hektor, l'audit REFUS5 (à refaire : son script est antérieur à la
demande), et la moitié « créer » de `1ESJE28Q` et `8Q3LHGZ4` — il a dit « défaire ET créer »,
les deux patchs ne défont que.

---

## 13. ⭐⭐ SEPT PROPOSITIONS POUR LE CHANTIER — **rien n'est décidé, elles sont à lui**

> ⛔ Écrites le 19/11 à sa demande (*« as-tu des idées pour améliorer ma demande et le futur
> chantier ? »*). **Aucune n'est engagée** : un périmètre ne se décide pas sans lui.

### ① ⭐⭐⭐ L'ÉTIQUETTE NE BOUGE PAS — **c'est le chaînage qui bouge.** La distinction est capitale

> ⛔⛔ **J'AI ÉCRIT LE CONTRAIRE LE 19/11, ET FRÉDÉRIC M'A CORRIGÉ** : *« il y a déjà une
> étiquette posée, le chaînage peut bouger, l'id dossier étiquette ne bouge pas, revérifie »*.
> **Il avait raison.** J'avais lu « 138 scissions » comme « 138 étiquettes changées ». C'est
> faux, et le code le dit en quatre lignes. **Cette confusion est le piège n° 1 de l'étape 5.2 :
> ne la refais pas.**

**Les quatre gestes de la pose d'étiquette** (`poser_les_etiquettes_de_dossier`, l. 2691) sont
tous construits pour **préserver l'étiquette existante** :

```
pose          un groupe SANS AUCUNE etiquette en recoit une neuve
propagation   une transaction NUE arrive dans un dossier deja etiquete -> elle PREND
              l'etiquette du dossier, qui ne change pas
scission      une etiquette sur deux groupes -> LA PART DETACHEE recoit une etiquette
              NEUVE, et le dossier d'origine GARDE LA SIENNE
fusion        deux etiquettes dans un groupe -> ON GARDE LA PLUS ANCIENNE
```

**Le journal depuis sa naissance (12/11) le confirme, événement par événement :**

```
pose            11 452 evenements . 31 163 transactions
scission           143 evenements .    147 transactions   <- la part DETACHEE change
propagation          6 evenements .      6 transactions
fusion               6 evenements .      9 transactions   <- LA SEULE EXCEPTION
```

Relevé sur une scission du 18/11 : `dossier = 027e832e (D2020-0605)` garde son étiquette,
`autre_uuid = d555f86a` est la neuve, et la transaction détachée est **`1001543` — une de nos
créations depuis le Sheet**. Autrement dit : nos 136 créations ont été détachées et **ce sont
elles qui ont reçu une étiquette neuve** ; aucun dossier d'origine n'a changé d'identifiant.

➡ **CE QUI BOUGE, C'EST L'APPARTENANCE D'UNE TRANSACTION À UN DOSSIER, jamais l'identifiant du
dossier.** Pour l'étape 5.2, cela change tout : **un UUID écrit dans le Sheet reste valide.**
Le vrai sujet n'est pas la stabilité de l'étiquette, c'est de savoir **laquelle écrire quand une
ligne pointe vers des transactions réparties sur deux étiquettes** — ce sont les 255 lignes du
§ 8.2, et c'est un problème connu et borné.

⚠ **IL RESTE UNE SEULE EXCEPTION, ET LE CODE LA TRAITE DÉJÀ** : une **fusion** garde la plus
ancienne des deux étiquettes, donc **l'absorbée disparaît** et ne vit plus que dans le journal.
C'est irréversible, et c'est écrit : *« un matin où le chaînage a beaucoup bougé, on doit le
voir TOUT DE SUITE »* — d'où le cri au-delà de `SEUIL_FUSIONS_QUI_INQUIETE = 10` par nuit.
**Mesure : 6 fusions en sept jours, sur 11 590 dossiers.**

➡ **Proposition, réduite à sa vraie taille :** après 5.2, ajouter **une seule ligne de
contrôle** — un UUID écrit dans le Sheet qui n'existe plus chez nous (étiquette absorbée par
une fusion) doit être signalé. Rien de plus. Le reste est déjà protégé par la conception.

### ② ⭐⭐ NE PAS LAISSER 9 % BLOQUER 91 % — écrire les UUID par vagues

Mesure du 19/11 :

```
4 794 lignes du Sheet connues
4 703 liees
4 448 a ETIQUETTE UNIQUE
4 346 a etiquette unique ET TOUS LEURS LIENS SURS, toutes avec une transaction vivante
  102 a etiquette unique mais UN LIEN « a valider »
  255 a PLUSIEURS etiquettes          <- le bouchon
```

➡ **4 346 lignes, soit 90,7 % du classeur, pourraient recevoir leur UUID dès que la question
① est tranchée.** Aujourd'hui le plan attend que les 255 soient résolues pour commencer.
**Proposition :** faire 5.2 en vagues — la vague 1 sur les 4 346, puis les 102, puis les 255
une fois jugées. Le chantier avance de 91 %, et le problème restant est **isolé et nommé**.

### ③ ⭐⭐ UN CRITÈRE DE FIN, ET UN SEUL CONTRÔLE QUI LE MESURE

Le chantier n'a **aucun critère de fin mesurable** : c'est pour ça qu'il dure. **Proposition :**
un contrôle versionné sur le patron du projet (`controle_balayage_photos_masquees.py`,
`controle_domaine_documents.py`) — `phase2/checks/controle_chantier_classeur.py`, sortie 0
vert / 1 un rouge / 2 pas pu mesurer — qui rend **le reste-à-faire en un chiffre** :

```
lignes sans lien non justifiees . liens « a valider » . lignes a plusieurs etiquettes
valeurs du classeur non posees non justifiees . lignes sans UUID dans le Sheet
questions ouvertes non repondues
```

Chaque séance le rejoue, et **le reste-à-faire doit décroître**. C'est aussi ce qui dira « le
chantier est fini », sans débat.

### ④ ⭐⭐ LE GABARIT OBLIGATOIRE D'UN GESTE DE MASSE

Nos campagnes écrivent déjà `etat_avant` / `etat_apres` dans la charge — **c'est très bien, et
c'est ce qui rend le temps 3 possible.** Mais il manque deux marches, et leur absence est
exactement ce qui nous coûte cette enquête :

```
a  ecrire etat_avant / etat_apres dans la charge          ✅ DEJA FAIT
b  prendre une PHOTO des lignes visees AVANT              ~ partiel (178, 5, 2, 1 lignes)
c  REJOUER le chainage apres, et comparer                 ⛔ JAMAIS FAIT
```

➡ **Proposition :** aucune campagne ne part sans les trois. La marche (c) coûte une fonction
déjà écrite et rejouable, et elle aurait répondu en dix minutes à la question qui nous occupe
depuis deux jours.

### ⑤ ⭐ INTERDIRE UN QUATRIÈME APPARIEMENT COMPLET

Trois appariements indépendants du Sheet existent déjà (29/10, 18/11, 19/11), et ils
s'accordent très largement. Un quatrième coûterait une nuit et n'apprendrait rien.
**Proposition :** le prochain chat n'a le droit de refaire un appariement complet **que s'il
prouve d'abord que les trois précédents sont faux**, cas par cas. Sinon, il les **recoupe**.

### ⑥ ⭐ GROUPER SES ARBITRAGES SUR UNE SEULE PAGE, ET LA RÉUTILISER

Il reste **32 questions écrites + 1 muette + 5 décisions + 5 arbitrages non traités**. Posées
une par une au fil des séances, elles se perdent et elles le fatiguent. **Proposition :** les
regrouper par famille sur **la page d'arbitrage qui existe déjà** (celle qui a servi aux 41
lignes, dont les réponses vivent dans sa base) plutôt que d'en refaire une. Il tranche en
série, une fois, et les décisions survivent à la conversation.

### ⑦ UNE SENTINELLE SUR LE BOUCHON

`data.classeur_ligne_sans_lien` existe (seuil 92) ; **rien ne surveille les lignes à plusieurs
étiquettes** — elles sont passées de 33 à 255 en sept jours sans qu'aucune alerte ne sonne.
**Proposition :** une sentinelle de plus, seuil posé sur la mesure du jour, relue après chaque
geste. Elle aurait nommé le problème le 18/11 au matin.
