# TEMPS 1 — L'INVENTAIRE DE NOS ÉCRITURES DE MASSE, lu dans le journal des travaux
### 19/11/2026 · chantier classeur, conduit par `notice/PROMPT_FINIR_LE_CHANTIER_CLASSEUR_2026-11-19.md`

> ⛔ **LECTURE SEULE DE BOUT EN BOUT.** Aucune écriture en base, chez Hektor ni dans le Sheet.
> La source est **`app_console_job` chez Supabase**, lue le 19/11 entre ~10:00 et ~11:30,
> recoupée par le **journal de l'offre que tient Hektor** (`propositions_json`) et par le code
> des scripts. Les notes n'ont servi qu'à nommer, jamais à compter.
>
> **Rejouer la mesure** (lecture seule, ~1 min) :
> ```
> .venv\Scripts\python.exe -X utf8 phase2\checks\temps1_inventaire_gestes_de_masse_2026-11-19.py
> ```
> Sortie 0 tout mesuré et cohérent · 1 une anomalie nommée · 2 pas pu mesurer. **Le 19/11 : 0.**
> Il produit **`notice/TEMPS1_GESTES_DE_MASSE_2026-11-19.csv`** — **une ligne par geste (1 236)**,
> l'état d'avant, l'état d'après, l'état d'aujourd'hui, la chaîne et l'étiquette d'aujourd'hui.
> ⭐ **C'est l'entrée du temps 3** (le rejeu du chaînage sur l'état d'avant).

---

## 0. EN UNE PAGE

```
LE JOURNAL          132 083 travaux (14/05 -> 19/11), 49 types, 127 166 sans auteur
CEUX QUI ONT TOUCHE 1 236 gestes, du 10/11 16:13 au 12/11 15:28, sur 1 217 transactions,
  LE REGISTRE       1 211 biens . 0 travail en erreur
  
  A  10-11/11  refus des offres mortes (la table)        526   accepted/proposed -> refused
  B  11/11     rattrapage de la cascade d'annulation     661   accepted -> refused
  C  11/11     cascade d'UN geste humain (pas un script)   1   accepted -> refused
  D  12/11     fermeture des dossiers impossibles         29   12 compromis -> cancelled
                                                               17 offres    -> refused
  E  12/11     reacceptation des refus a tort             19   refused -> accepted (sur B)

CE QUI A ECHOUE     AUCUN geste. 1 224 gestes sur des offres (1 205 offres) : HEKTOR porte
                    CHACUN dans son propre journal de l'offre. 1 217 etats sur 1 217 tiennent
                    (les 19 de B defaits l'ont ete par E, volontairement).
CE QUI A COUTE      ce que le geste a fait EN PLUS du champ vise -- § 4 :
                    1 205 dates d'offre deplacees au jour du geste . 6 dates FABRIQUEES
                    . 15 biens vendus remis « Sous offre » par E (note du 13/11)
LE 1 233 DU DOSSIER  devient 1 236 : il manquait LES 3 ESSAIS DU 10/11 (§ 3 A)
```

⭐ **Aucune campagne inconnue n'a touché le registre** — mais le journal **ne voit pas tout** : les
patchs SQL du chantier ont écrit en masse dans le registre **sans passer par lui** (§ 6). Et il a
rendu une trouvaille : **les « 3 transactions disparues sans trace » ont une trace** (§ 7).

---

## 1. LA MÉTHODE, ET SES DEUX TÉMOINS

**Ce qui est une « campagne »** : des travaux posés **sans auteur** (`requested_by` vide, donc par un
script en `service_role`), sur un même type de geste, dans une même fenêtre, avec une même
`origine` dans la charge. Les gestes humains (un clic dans l'app) n'en sont pas — **sauf** la cascade
C, gardée parce que le dossier du 19/11 la comptait dans ses 1 233.

**Les familles de travaux balayées** : toutes les 49 (§ 5). Celles qui écrivent une **transaction**
sont `change_hektor_offre_status`, `cancel_hektor_compromis`, `delete_hektor_compromis`,
`delete_hektor_vente` et `change_hektor_annonce_status` (« Vendu » crée une vente, « Clos » peut
refuser l'offre et annuler le compromis). **Hors du 10-12/11, aucune n'a de campagne** : leurs
travaux sans auteur sont des **essais**, tous sur les biens d'essai 24113, 62774 et 24933 (§ 5).

**Le juge qui ne vient pas de nous.** Le script de refus **pose lui-même** `state` au registre
(étape 7 de `enqueue_refus_offres_mortes_lot.js`, un `PATCH`) : l'état du registre ne prouve donc
rien seul. Le **journal de l'offre** (`propositions_json`) n'est écrit **que par Hektor** et relu la
nuit : une entrée `refus` ou `accepte` datée du 10/11 ou après **est** la preuve du geste.
⚠ **Un compromis n'a pas ce journal** : pour les 12 de D, la seule preuve est l'état du registre,
relu chez Hektor chaque nuit (`state` n'est **pas** protégé par R2 : `R2_CHAMP_VERS_COLONNE`,
`affaire_ledger.py` l. 1707, ne le contient pas). **Preuve plus faible, dite telle.**

```
TEMOIN POSITIF  les 19 offres reacceptees le 12/11 sortent « defaites par un geste suivant »
                sur leur geste du 11/11 : 19 sur 19 -> la mesure SAIT voir un etat qui n'a
                pas tenu.
TEMOIN INVERSE  les 1 225 offres refusees que nos campagnes N'ONT PAS touchees :
                  1 128 portent un refus ANCIEN seulement      -> « pas nous »
                     96 n'ont aucune entree refus              -> ce sont les 96 offres
                                                                  CREEES depuis le classeur
                      1 porte un refus depuis le 10/11         -> un geste HUMAIN : l'essai
                                                                  du 16/11 sur le bien d'essai
                                                                  62965 (affaire 1001409)
                -> la mesure SAIT dire « ce n'est pas notre geste ».
FERMETURE       toute offre aujourd'hui refusee dont le journal porte un refus du 10/11 ou
                apres a SON travail au journal des travaux : 0 orpheline (requete du 19/11).
```

---

## 2. LE JOURNAL EN ENTIER — les 132 083 travaux

```
sync_console_documents     94 887   les documents : lots d'aout-octobre + la resynchro de nuit
sync_hektor_photos         30 321   dont le balayage des photos masquees (30 000)
refresh_console_data        3 388   relectures (3 150 humaines)
change_hektor_offre_status  1 255   1 228 sans auteur  <- A B D E
refresh_console_contact     816
change_hektor_annonce_st.   181     63 sans auteur : ESSAIS sur biens d'essai
upload_document_to_hektor   170
delete_hektor_annonce       127     79 sans auteur : nettoyages d'annonces d'essai
update_hektor_annonce_f.    101
... (49 types en tout)
cancel_hektor_compromis      27     17 sans auteur  <- 12 de D + 5 essais d'aout-septembre
delete_hektor_compromis      19     2 sans auteur (essais du 16/09)
delete_hektor_vente          15     3 sans auteur (essais du 30/08, 08/09, 13/09)
```

---

## 3. LES CAMPAGNES QUI ONT TOUCHÉ LE REGISTRE DES TRANSACTIONS

### A — Le refus des offres mortes, par la table de contrôle · 10-11/11 · **526**

```
SCRIPT        Console/enqueue_refus_offres_mortes_lot.js  (--source table, le defaut)
              origine « enqueue_refus_offres_mortes_lot » dans la charge
DECIDE PAR    notice/TABLE_DE_CONTROLE_REGISTRE_2026-11-10_APRES_CHAINAGE.csv :
                fichier 27/02 410 . classeur (son dossier) 94 . statut du bien (Clos) 20
                . classeur (le bien, meme acheteur) 1 . statut du bien (Estimation) 1
QUAND         ⭐ 3 ESSAIS LE 10/11 (16:13 x2 : offres 10014 et 10136 ; 18:49 x1)
              puis 523 le 11/11, poses en 5 vagues de 07:52 a 18:38, executes jusqu'a 19:00
ETATS         accepted -> refused 524 . proposed -> refused 2
LA CHARGE     etat_avant ET etat_apres : 526 / 526
CE QUI TIENT  526 / 526 refused aujourd'hui . journal Hektor 526 / 526
ECHECS        0 travail en erreur
```
⚠ **Le 20ᵉ « refus à tort »** (la règle D du 12/11 a révélé que l'affaire avait abouti) est dans A :
**affaire 14420, offre Hektor 7722, posée le 11/11 à 18:38**. Elle est **laissée refusée par
décision** (son offre est datée après sa vente : deux défauts superposés, sujet à part).

### B — Le rattrapage de la cascade d'annulation · 11/11 · **661**

```
SCRIPT        LE MEME FICHIER, Console/enqueue_refus_offres_mortes_lot.js --source cascade
              origine « rattrapage_cascade_annulation »
DECIDE PAR    « coherence : compromis annule » -- AUCUN juge exterieur : la chaine a un
              compromis annule, pas de compromis vivant, pas de vente, et une offre acceptee
              (garde : if (cpAnnule && !cpVivant && !vente && offreAcceptee))
QUAND         ⚠ 661 travaux POSES EN 1,3 SECONDE (19:01:04 -> 19:01:05), executes jusqu'a
              19:37 -- le plafond par defaut du script est 25 : il a ete leve a la main
ETATS         accepted -> refused 661
LA CHARGE     etat_avant ET etat_apres : 661 / 661
CE QUI TIENT  642 refused . 19 accepted -> DEFAITS PAR E le 12/11 . journal Hektor 661 / 661
ECHECS        0 travail en erreur . ⛔ 19 refus FAUX : la garde interrogeait le chainage
              d'AVANT la regle D (posee le 12/11 a 11:59, elle a reuni 727 dossiers)
```

### C — La cascade d'un geste humain · 11/11 08:57 · **1** (pas une campagne)

Un utilisateur de l'app a annulé le compromis de l'affaire 28121 (bien 54684) ; la règle posée le
matin même dans `app_geste_affaire_optimistic` (`supabase/patch_cascade_annulation_2026-11-11.sql`)
a refusé **automatiquement** l'offre 28122 (origine `cascade_annulation_compromis`). Tenu, journal
Hektor 1 / 1. **Comptée parce que le dossier la comptait** ; c'est la règle de l'avenir, B en est
le rattrapage du passé.

### D — La fermeture des dossiers « impossibles » · 12/11 · **29 gestes, 23 dossiers**

```
SCRIPT        Console/enqueue_fermeture_dossiers_impossibles.js
              origine « enqueue_fermeture_dossiers_impossibles »
DECIDE PAR    Frederic, dossier par dossier, tableau « Chainage a trancher » du 12/11
              (22 « fermer », puis 14137 LEJEUNE ajoute sur sa decision en fin de matinee)
QUAND         12/11 12:03:19 -> 12:16:51 . les compromis D'ABORD (priorite 55), les offres
              ensuite (60) -- et APRES la regle D (11:59)
ETATS         12 compromis active -> cancelled
              17 offres  accepted -> refused 9 . proposed -> refused 2
                         (vide) -> refused 6   <- des offres SANS ETAT chez Hektor
LA CHARGE     29 / 29 portent etat_avant ; 6 le portent VIDE (l'etat etait reellement vide)
CE QUI TIENT  29 / 29 . journal Hektor 17 / 17 offres (les compromis n'ont pas de journal)
ECHECS        0 travail en erreur
```
⚠ Le commit `0f2235e` dit « 28 gestes » : c'était avant l'ajout de 14137 (29ᵉ, à 12:16).

### E — La réacceptation des refus à tort · 12/11 · **19**

```
SCRIPT        Console/enqueue_reaccepter_offres_refusees_a_tort.js
              ⚠ PAS de cle « origine » : la charge porte source = « Frederic -- alerte du
              12/11/2026 sur le dossier 3676 », et une raison par offre
QUAND         12/11 15:14:53 -> 15:28:14
ETATS         refused -> accepted 19 -- les 19 sont TOUTES des offres de B
LA CHARGE     ⛔ AUCUNE ne porte etat_avant. Il est RECONSTITUE ici depuis le geste B de la
              meme transaction (refused), et le CSV le dit (etat_avant_source)
CE QUI TIENT  19 / 19 accepted . journal Hektor 19 / 19 (une entree « accepte » du 12/11)
ECHECS        0 travail en erreur
```

### Les totaux, et la réconciliation avec le dossier

```
1 236 gestes = 526 + 661 + 1 + 29 + 19
1 217 transactions distinctes (19 touchees deux fois : B puis E) . 1 211 biens
1 211 chaines et 1 211 etiquettes AUJOURD'HUI : 6 dossiers portent DEUX transactions
      touchees -- les 6 paires compromis + offre de D (395/396, 1609/1610, 2993/2994,
      10749/10750, 14669/14670, 18663/18664)

LE DOSSIER DISAIT 1 233 = 1 185 (11/11) + 36 (12/11) + 12 (12/11)
   11/11 : 523 (A) + 661 (B) + 1 (C) = 1 185   ✅ au chiffre pres
   12/11 : 17 (D) + 19 (E)           =    36   ✅
   12/11 : 12 compromis (D)          =    12   ✅
   ⚠ MANQUAIENT les 3 essais de A du 10/11 -> 1 236
« LA CHARGE PORTE etat_avant POUR CHACUN » : vrai pour 1 217 sur 1 236. Les 19 de E ne le
   portent pas (reconstituable sans ambiguite depuis B) ; 6 de D le portent VIDE (vrai vide).
```

---

## 4. CE QUE CHAQUE GESTE A ÉCRIT — pas seulement le champ visé

```
CHEZ HEKTOR   l'etat . UNE ENTREE de plus au journal de l'offre . et la colonne `date`,
              ou Hektor met le DERNIER MOUVEMENT d'une offre
                -> 1 205 offres sur 1 205 portent aujourd'hui une `date` du 10, 11 ou 12/11
                -> 6 offres de D n'avaient AUCUNE entree datee avant le geste : leur seule
                   date est NOTRE refus (une date FABRIQUEE). ⚠ La note du 12/11 en compte 8 ;
                   l'ecart de 2 n'est pas mesure (les 2 « proposed » avaient une entree datee
                   au journal, peut-etre une colonne `date` vide)
                -> E a remis 15 BIENS VENDUS « Sous offre » (mesure du 13/11, repares a la
                   main chez Hektor 15/15). ⚠ NON REMESURE le 19/11 : ces biens ne sont pas
                   dans app_dossier_current (un bien vendu ou clos n'y est plus)
CHEZ NOUS     le script pose LUI-MEME `state` au registre (PATCH, hors journal des travaux
              mais lie a chaque travail) . le worker ecrit registre_lignes = 1 (1 236 / 1 236)
              . « sans_resynchro » : pas de relecture individuelle, la nuit relit tout
              (sauf les 2 premiers essais de A et les 19 de E, qui ont pose une relecture)
LE CHAINAGE   rien d'ecrit par le geste lui-meme -- mais il est REDEDUIT chaque nuit sur
              l'etat final : c'est l'objet du temps 3
```

⛔ **Pour le temps 3, l'ordre des événements compte, et il est maintenant établi :**

```
10/11 14:27  les regles A, B, C du chainage ecrites (commit 8ee4950), chacune derriere son
             interrupteur -- ⚠ la date ou chacune a ete ALLUMEE n'est dans aucun journal
10/11 16:13  A commence (3 essais)
11/11 07:52  A (523) . 08:57 C . 19:01 B (661)
12/11 11:59  LA REGLE D + rattachements_manuels.csv (commit 518b08b)
12/11 12:03  D (29) . 15:14 E (19)
12/11 23:08  L'ETIQUETTE EST POSEE (11 441 dossiers) -- APRES LE DERNIER GESTE
             -> le journal des etiquettes ne sait RIEN des 1 236 gestes
```

---

## 5. LES CAMPAGNES DE MASSE QUI NE TOUCHENT PAS LE REGISTRE — pour que la liste soit complète

```
balayage des photos masquees   30 000   19/10 -> 18/11 . 1 003 erreurs, toutes en octobre
documents, par lots            16 279 + 865 (aout) . 14 997 (septembre) . 23 749 (octobre)
documents, resynchro de nuit   34 424 (aout) . 3 292 (octobre) . 1 261 (novembre)
nettoyages d'annonces d'essai  22 « Assainissement annonces test » (08/06) . 21 « Nettoyage
                               brouillons vides » (07/07) . et une trentaine a l'unite
envois de 12:30                20 photos + 4 documents le 24/10
signatures                     19 youtrust_sync_signature (05-06/11)
ESSAIS SUR BIENS D'ESSAI       63 change_hektor_annonce_status sans auteur (24113, 62774,
                               24933 -- juillet a novembre) + 5 annulations, 2 suppressions
                               de compromis, 3 suppressions de vente, 2 refus (aout-sept.)
                               -> ils creent ou suppriment des transactions DE LA PLAGE APP,
                               sur ces trois biens seulement
```

---

## 6. ⛔ CE QUE LE JOURNAL NE VOIT PAS — les écritures de masse faites par PATCH SQL

**Le journal des travaux ne connaît que ce qui passe par le worker.** Le chantier a aussi écrit en
masse **directement** dans le registre, par patch (`Console/apply_sql_patch.js`, qui n'écrit aucun
journal). Comptés **dans le registre aujourd'hui** (19/11), datés **par git** :

```
16/11  C5    195 transactions CREEES depuis le Sheet (transaction_origine = classeur)
18/11        5 retirees (doublons), des deux cotes                     -> 190 aujourd'hui
16/11  C3    date_annulation_app                                       450
17/11  C4    motif_annulation_app 169 (+ notes et conditions, autres tables)
16/11  C8    vente_reglee_app 3 729 . numero_facture_app 3 671
17/11  C2    honoraires_entree_app 66 . honoraires_sortie_app 6 . charge 7
12/11  B2    l'etiquette posee (11 441), l'annee reparee, deux reposes du numero
12/11        patch_date_convenue : une date DECIDEE pour 5 offres
15-16/11     le cobaye de A2 (une transaction pose puis retiree)
12/11 11:59  la regle D et phase2/sync/rattachements_manuels.csv (un fichier, pas un patch)
?            les interrupteurs du chainage dans .env : AUCUN journal ne date leur allumage
```

➡ **Pour le temps 3, une question à trancher dans le code, pas à supposer** : lesquelles de ces
écritures **nourrissent le chaînage** ? Les 190 de C5, **oui** (les 138 scissions du 18/11 le
prouvent). Les colonnes `*_app` et la date décidée : **non mesuré** — il faut lire ce que
`recalculer_les_chaines` (l. 1888) et `_date_de_tri` (l. 1564) lisent.

---

## 7. ⭐ UNE TROUVAILLE : LES « 3 TRANSACTIONS DISPARUES » ONT UNE TRACE

Le plan (§ « LES FAITS ÉTABLIS ») écrit : *« 1001388, 1001391, 1001394 ont DISPARU des deux bases,
sans sauvegarde, sans journal, sans trace de qui »*. **Le journal dit le contraire** :

```
1001388  compromis 50135  bien d'essai 24113  delete_hektor_compromis  23/10 17:59  done
1001391  compromis 50136  bien d'essai 24113  delete_hektor_compromis  23/10 19:24  done
1001394  compromis 50137  bien d'essai 24113  delete_hektor_compromis  03/11 10:12  done
```

Chacun est un **geste humain** (auteur renseigné), et chacun est **inscrit au journal des
suppressions** `app_affaire_supprimee` avec sa preuve (*« relecture API après le geste,
trouve=false »*) et `serveur_aligne = true`. C'est le dessin du worker : il inscrit au journal
**puis** efface la ligne du registre (`console_job_worker.js`, ~l. 24894-24917). **Ce ne sont pas
des disparitions, ce sont des suppressions d'essai, faites par l'app, sur le bien d'essai.**
⚠ Ce qui reste vrai : leurs **5 conditions et 6 notes** sont orphelines (le worker vide le carnet,
pas `app_affaire_condition` ni `app_affaire_note`). C'est un sujet du temps 2 (le geste
« supprimer »), pas une perte.

---

## 8. CE QUE JE N'AI PAS MESURÉ

```
. l'etat CHEZ HEKTOR des 12 compromis de D, autrement que par notre registre relu la nuit
. les 15 biens « Sous offre » de E aujourd'hui (hors de app_dossier_current)
. l'ecart 8 / 6 des dates fabriquees de D
. la date d'allumage de chaque interrupteur du chainage (aucun journal)
. si les colonnes *_app et la date decidee nourrissent le chainage (-> temps 3, dans le code)
. le contenu exact de chaque patch SQL : je les ai DATES et COMPTES, pas relus un par un
```
