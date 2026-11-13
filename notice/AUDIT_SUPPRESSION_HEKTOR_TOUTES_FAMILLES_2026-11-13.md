# AUDIT — « UNE SUPPRESSION CHEZ HEKTOR DOIT-ELLE SUPPRIMER CHEZ NOUS ? »

**13/11/2026** — demandé par Frédéric :

> *« J'ai souhaité protéger mon app d'éventuelle suppression de masse ou coupure, mais je
> pense que je dois changer le mécanisme pour simplifier les choses : une suppression chez
> Hektor supprime aussi dans l'app, mais sous conditions pour éviter problème à la coupure
> ou erreur de masse. »*
>
> *« Audite en profondeur pour ne pas faire d'erreur. »*

> ⛔ **LECTURE SEULE.** Rien n'a été écrit en base, ni chez Hektor, ni dans le classeur.
> Les seuls appels chez Hektor sont des lectures (7 au total), avec témoin positif.

---

## 0. LA RÉPONSE EN UNE PAGE

**Le mécanisme que tu veux poser existe déjà, en grande partie, et il est bien fait.**
Ce qui manque n'est pas la suppression : c'est **l'uniformité**. Cinq familles sont
protégées, deux ne le sont pas du tout, et le drapeau sur lequel tu voudrais brancher le
`DELETE` ne veut pas dire ce qu'il a l'air de dire.

**Les trois chiffres de cet audit :**

```
1. le coût actuel de « conserver »        966 lignes sur 836 000   (0,1 %)
2. le rythme réel des suppressions        3 en deux mois
3. le drapeau est AMBIGU                  sur les mandats, 567 des 568 lignes
                                          « absentes » n'ont JAMAIS ete chez Hektor
```

⛔⛔ **Le point 3 est la trouvaille de cet audit, et il condamne la forme simple.** Un
`DELETE WHERE present_in_hektor = false` sur les mandats effacerait **567 mandats du
registre légal 2014-2024 et de Modelo** — des mandats qui n'ont jamais eu de rapport avec
Hektor, et que Hektor n'a donc jamais pu « supprimer ».

---

## 1. CE QUE CHAQUE FAMILLE FAIT AUJOURD'HUI — le tableau des objets

**Méthode du projet (21/09)** : un audit balaie les objets *et* les gestes. Voici les huit
familles, et ce qui se passe quand **Hektor ne rend plus l'objet**.

### Groupe A — protégées : la ligne est CONSERVÉE, marquée

```
transactions   app_affaire_ledger     present_in_hektor         + alignement protege
mandats        app_mandat             present_in_hektor
relations      app_relation           present_in_hektor + absent_depuis + retire_le
documents      app_console_document   present_in_hektor + absent_depuis + delai 15 min
photos         app_console_photo      present_in_hektor + absent_depuis + delai 15 min
```

Plus, hors périmètre Hektor direct : `app_negociateur_fiche`, `app_registre_agence`,
`app_partenaire_*`.

### Groupe B — SUPPRIMÉES, avec un plafond

```
annonces       app_dossier_current + 3 tables soeurs
               -> delete_rows_by_ids(stale_ids), push_upgrade_to_supabase.py l. 1710
```

Trois protections, et elles sont sérieuses :

```
--allow-stale-deletes      ETEINT par defaut (« Disabled by default as a safety guard »)
--max-stale-deletes 500    au-dela, RuntimeError : « Safety stop » -- LE RUN S'ARRETE
separer_annonces_app_...   les annonces nees dans l'app (>= 10 000 000) sont EPARGNEES
```

⭐ **Et le registre des mandats a été SORTI de cette liste le 29/09** — elles étaient cinq.
Le commentaire du code dit pourquoi, et c'est un précédent capital :

> *« un registre CONSERVE, c'est sa définition. Il effaçait les mandats des annonces vendues
> ou archivées, et personne ne les réécrivait — **635 mandats de vente perdus, dont 80 en
> cours**. »*

### Groupe C — SUPPRIMÉES, SANS AUCUN PLAFOND ⛔

```
contacts       push_contacts_to_supabase.py : find_stale_row_keys -> delete_rows_by_key
recherches     idem (meme chemin)
```

Mesuré mot à mot : **aucun `max_stale`, aucun `allow_stale`, aucun « Safety stop »** dans
`push_contacts_to_supabase.py`. La seule protection est l'épargne des objets nés dans l'app
(`est_ne_dans_l_app`).

⚠ **Et cette famille a déjà payé**, c'est écrit dans le code (l. 800-830) : la nuit du
**13 au 14/10**, une recherche passée inactive chez Hektor a fait sortir **24 recherches de
Supabase et laissé 4 022 lignes** de rapprochement, de score et de relance accrochées dans
le vide. Le remède retenu a été, mot pour mot :

> *« Le remède est celui que le projet applique déjà ailleurs : **la ligne ne disparaît
> jamais**. Les recherches étaient le seul objet qu'on EFFAÇAIT au lieu de RANGER. »*

### Groupe D — non mesuré dans cet audit

```
RDV / visites        non mesure
diffusion portails   app_diffusion_target est bien efface (hektor_diffusion_writeback)
                     mais c'est un ETAT recalcule, pas un objet metier -- hors sujet
```

---

## 2. ⭐⭐ CE QUI EXISTE DÉJÀ, ET QUE TU CROYAIS DEVOIR ÉCRIRE

C'est la partie la plus utile de l'audit : **trois des quatre conditions que tu demandes
sont déjà codées**, pour les transactions.

### ① « ne jamais conclure d'une lecture ratée » — ÉCRIT, et après un incident réel

`normalize_source.py`, `aligner_miroir_sur_hektor`, posé le **07/09/2026** :

```
SEUIL_MIROIR_COMPLET = 0.5
    si la liste fraiche contient moins de la MOITIE de ce qu'on connait
    -> on REFUSE d'aligner
```

Le commentaire dit son origine :

> *« Le garde-fou est recopié de `reconcile_active_annonce_scope`, écrit après un incident
> réel : on ne supprime jamais sur un balayage qu'on soupçonne tronqué. **Le 02/09, sept
> erreurs HTTP 500 de Hektor ont interrompu un balayage en cours.** »*

⭐ **Et c'est l'explication du pic du 07/09** que j'ai d'abord pris pour un incident : les
15 transactions « disparues » cette nuit-là sont l'**arriéré historique** découvert au
premier passage du mécanisme, le jour de sa naissance. Pas une panne.

### ② « confirmer, ne pas croire une liste » — ÉCRIT, allumé, et il couvre un vrai défaut

`filet_liste_incomplete` (24/10/2026) compare les distincts reçus **au total que Hektor
annonce lui-même**. Il a son interrupteur :

```
APP_MIROIR_FILET_LISTE    absent ou 0 -> JOURNAL SEUL (il calcule, ne garde rien)
                          1           -> il garde vraiment
```

✅ **Mesuré dans le `.env` du 13/11 : `APP_MIROIR_FILET_LISTE=1`. Il est ALLUMÉ.**

Il a son essai dédié, `phase2/checks/test_filet_liste_incomplete.py`, six cas, qui rejoue
la vraie nuit sur une copie sans écrire ni appeler Hektor.

### ③ la lecture absolue par identifiant — ÉCRITE depuis le 16/09

`phase2/sync/transaction_etat_from_api.py` rend l'existence d'une transaction **par son
numéro**, pas par sa présence dans une liste. Éprouvée aujourd'hui, avec témoin positif :

```
compromis 46189 (58979)   trouve: false      offre 32919 (62097)   trouve: false
compromis 23342 (8494)    trouve: false      TEMOIN + : compromis 50157  trouve: TRUE
compromis 49911 (43437)   trouve: false      TEMOIN + : offre 33140      trouve: TRUE
compromis 15680 (49584)   trouve: false
```

⭐ Les cinq absences sont donc **réelles** : le drapeau ne ment pas sur les transactions.

### ④ le chemin inverse — le journal des suppressions

`app_affaire_supprimee` + `serveur_aligne` : quand **l'app** ordonne une suppression chez
Hektor, le miroir local se nettoie, *journal à l'appui*, et seulement après confirmation.
⭐ **Le patron « journal + alignement » que tu veux existe donc déjà — dans l'autre sens.**

Il vise la **transaction**, pas le numéro d'app — leçon du 17/09 : un même `app_affaire_id`
porte parfois deux compromis successifs, et effacer « au numéro » retirait le survivant.

---

## 3. ⛔ LES CINQ TROUS RÉELS

### ⛔⛔ ① LE DRAPEAU DIT DEUX CHOSES INCOMPATIBLES

```
                   « HEKTOR L'A RETIREE »   « ELLE N'A JAMAIS ETE CHEZ HEKTOR »
mandats                      1                           567
transactions                18                             0
relations                   62                             0
```

Les 567 sont des mandats du **registre légal 2014-2024** et de **Modelo** (`origine:
modelo`, `registre_legal_2014_2024`), importés le 27/10 à 14:57, `hektor_mandat_id` à NULL.
Ils naissent `present_in_hektor = false` : **c'est leur état normal.**

⚠ Le code le sait déjà et s'en protège, à un seul endroit (`affaire_ledger.py` l. 1944) :

> *« ET LE FILTRE NAÏF EST FAUX. `WHERE present_in_hektor` exclurait aussi les transactions
> NÉES DANS L'APP. »*

⛔ **Un `DELETE` branché sur ce drapeau détruirait 567 mandats du registre légal.** C'est le
risque de masse que tu veux éviter, et il ne viendrait même pas de Hektor : il viendrait de
nous.

### ⛔ ② CONTACTS ET RECHERCHES N'ONT AUCUN PLAFOND

Les annonces s'arrêtent à 500 et font échouer le run. Les contacts et les recherches
suppriment sans compter. C'est l'asymétrie la plus dangereuse du projet aujourd'hui —
**indépendamment de ta décision**, et elle mérite d'être corrigée dans tous les cas.

### ⛔ ③ AUCUN INTERRUPTEUR DE COUPURE

Recherché mot à mot : `HEKTOR_HORS_SERVICE`, `MODE_AUTONOME`, `HEKTOR_MUET`, `coupure_hektor`
— **aucun n'existe**. (`sans_hektor` existe, mais c'est un statut d'envoi de document.)

Le jour de la coupure, Hektor se tait. Le silence est **indiscernable** de « tout a été
supprimé ». Les seuils de 0,5 et de 500 mordraient, donc le run s'arrêterait — mais par
accident, pas par dessein, et avec un run en échec chaque nuit.

### ⛔ ④ L'ALIGNEMENT PROTÉGÉ NE COUVRE QUE TROIS OBJETS

`aligner_miroir_sur_hektor` n'est appelé que pour `hektor_offre`, `hektor_compromis`,
`hektor_vente`. Les mandats, relations, documents et photos ont le drapeau, mais pas le
seuil ni le filet.

### ⛔ ⑤ L'ÉTIQUETTE DE DOSSIER NE LIT PAS LE DRAPEAU

Mesuré le 12/11 : **0 fonction d'étiquette** lit `present_in_hektor`. Sans conséquence
aujourd'hui (personne ne lit l'étiquette), mais bloquant à l'**étape 5.2**.

⭐ **Vu en vrai aujourd'hui sur le bien 62049** : son offre morte 33013 porte l'étiquette
`D2026-0251`, à côté de la vivante 33140 qui porte `D2026-0367`. Un bien, deux numéros de
dossier, dont un sur une transaction que Hektor a effacée.

---

## 4. ⭐ LE DOSSIER 62049, OBSERVÉ AUJOURD'HUI — le mécanisme pris sur le fait

Frédéric a corrigé le statut à la main. Vérification demandée : aucun compromis ajouté.

```
chez Hektor   statut 4 « Sous compromis »   compromis : 50157 et lui seul   ventes : 0
```

✅ **Aucun compromis n'a été créé.** Et l'histoire du bien se lit dans le registre :

```
offre 33013   acceptee 05/08    11 000 €    present_in_hektor = FALSE
offre 33140   acceptee 12/11   110 000 €    present_in_hektor = true, nee chez nous 13/11 05:20
```

Il manquait un zéro. Hier à 17:30, quelqu'un chez Hektor a supprimé l'offre fausse et
recréé la bonne au prix du compromis. **Ce n'est pas nous** : le seul travail de l'app sur
ce bien le 12/11 est une relecture (`refresh_console_data`, 14:29), trois heures avant.

⭐ **Le mécanisme a parfaitement fonctionné** : la fausse a été marquée, la vraie adoptée,
en une nuit, sans intervention. **C'est ce comportement-là que tu voudrais remplacer.**

---

## 5. ⭐⭐ LES TROIS PRÉCÉDENTS — le projet a déjà payé TROIS FOIS

```
29/09   635 mandats de vente perdus (dont 80 en cours)
        -> le registre SORTI de la liste des tables effacees
13-14/10  24 recherches sorties, 4 022 lignes orphelines
        -> « la ligne ne disparait jamais »
20/10   15 403 fiches de documents supprimees, 17 120 recreees, 17 118 fichiers
        retelecharges chez Hektor sous quota, avec un bannissement d'IP a l'historique
        -> on ARRETE de supprimer, on RE-CLE, plus deux garde-fous chiffres
```

⭐⭐ **Trois incidents, trois causes différentes, et la même conclusion à chaque fois :
cesser de supprimer sur une absence.** Aucun de ces trois remèdes n'a été « mieux
détecter ». Tous ont été « ne plus détruire ».

---

## 6. ⭐⭐⭐ MA RECOMMANDATION

### Ce que je NE recommande pas : brancher un `DELETE` sur `present_in_hektor`

Pour trois raisons mesurées, dans l'ordre de gravité :

```
1. le drapeau est AMBIGU          567 mandats du registre legal seraient detruits
2. le gain est NUL                966 lignes conservees sur 836 000 (0,1 %)
3. le projet a deja paye 3 fois   635 mandats, 24 recherches, 15 403 documents
```

### Ce que je recommande : **le même effet, sans le risque**

**« Supprimer » et « ne plus compter » sont la même chose pour l'utilisateur, et l'opposé
pour la réversibilité.** La ligne disparaît de l'écran, du statut, du chaînage, des
étiquettes, du classeur. Elle n'existe plus — sauf pour qui va la chercher.

Remplacer le booléen par un **état**, qui lève l'ambiguïté du trou ① :

```
vivante                   Hektor la rend
jamais_chez_hektor        nee dans l'app, ou importee (les 567)  -- COMPTE
absente_a_confirmer       pas vue une fois                        -- COMPTE ENCORE
retiree_par_hektor        confirmee absente PAR IDENTIFIANT       -- NE COMPTE PLUS
ignoree_par_nous          geste humain, avec motif et auteur      -- NE COMPTE PLUS
```

Et **un seul prédicat**, appelé par les six portes — registre, règle de statut, chaînage,
pose d'étiquette, pilotage, table des parties :

```
app_affaire_compte_encore(ligne) = etat IN ('vivante','jamais_chez_hektor','absente_a_confirmer')
```

⭐ **C'est ça, la simplification que tu cherches.** Ce qui est compliqué aujourd'hui n'est
pas la conservation : ce sont les 23 lectures dispersées du drapeau, plus une famille qui
l'oublie. Un prédicat unique simplifie davantage qu'un `DELETE`.

⛔ **Et le piège, déjà payé avec les brouillons (20/10)** : une exclusion rangée à côté sans
être appelée partout recrée le défaut. Ce n'est pas « ajoutée quelque part » : appelée par
les six.

### Les quatre conditions — trois existent, il faut les ÉTENDRE, pas les écrire

```
① ne pas conclure d'une lecture ratee    EXISTE (seuil 0,5)  -> ETENDRE aux 4 autres familles
② confirmer par identifiant               EXISTE (16/09)      -> APPELER avant tout marquage definitif
③ plafond de masse qui refuse et crie     EXISTE pour les annonces (500)
                                          ⛔ MANQUE pour contacts et recherches -> A POSER
④ interrupteur de coupure                 ⛔ N'EXISTE PAS     -> A POSER
```

### Et le geste qui manque vraiment

Il n'y a **aucun chemin** pour dire « cette transaction ne compte plus chez nous » quand
Hektor la garde encore. `delete_hektor_compromis` supprime **chez Hektor**,
`cancel_hektor_compromis` annule **chez Hektor**. C'est le cas du bien **8494** (compromis
3699, actif et présent chez Hektor, mais faux).

⭐ Et pour le **58979**, l'audit du matin l'a montré : il n'a besoin de **rien**. Hektor a
déjà retiré son compromis, notre règle dit « Sous offre » comme Hektor, il n'est même pas
dans la vue des écarts.

---

## 7. L'ORDRE QUE JE PROPOSE

```
1. le plafond contacts/recherches     ⛔ le plus urgent, et INDEPENDANT de ta decision
2. l'etat a 5 valeurs + le predicat unique appele par les 6 portes
3. l'extension du seuil et du filet aux mandats, relations, documents, photos
4. l'interrupteur de coupure
5. le geste « je l'ecarte » (8494), et la sentinelle des 18
```

⚠ Le **1** doit se faire quoi qu'il arrive : aujourd'hui, une nuit où Hektor rend mal les
contacts peut en effacer un nombre illimité, sans alerte et sans plafond.

---

## 8. CE QUE CET AUDIT N'A PAS MESURÉ, et que je ne suppose pas

```
. les RDV / visites : aucune mesure
. si le seuil de 0,5 a deja MORDU en vrai (le journal du run le dirait)
. ce que le filet a GARDE depuis son allumage (ligne « [miroir] FILET » du journal)
. le comportement des 4 autres familles sous une panne longue
. si Hektor rend un total fiable pour les mandats et les relations
  (le filet en depend : sans total, il ne garde rien, par dessein)
```

---

## 9. ⛔ CE QUE J'AI CORRIGÉ DANS MES PROPRES MESURES, EN COURS D'AUDIT

**J'ai d'abord lu « 15 transactions disparues la même nuit du 07/09 » comme un incident de
lecture**, et j'allais le présenter comme la preuve du danger. Deux vérifications l'ont
démenti : la lecture par identifiant (les cinq sont vraiment absentes chez Hektor) et
`git log`, qui date du 07/09 la **naissance** du mécanisme. C'était l'arriéré historique.

**Puis j'ai lu « 567 mandats disparus le 27/10 » comme la panne Hektor du 27-28/10.** Faux
également : en ouvrant les lignes, ce sont des mandats du registre légal et de Modelo,
importés ce jour-là à 14:57, qui n'ont jamais été chez Hektor.

⭐ *Leçon : un pic dans une colonne de dates ne dit pas ce qui s'est passé — il dit quand
quelque chose a été écrit. Les deux fois, la bonne réponse était dans les lignes, pas dans
le compte.* Et la seconde erreur, en se corrigeant, a produit la trouvaille centrale de
l'audit : **le drapeau est ambigu**.
