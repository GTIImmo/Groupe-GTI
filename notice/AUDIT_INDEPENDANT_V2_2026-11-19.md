# AUDIT INDÉPENDANT V2 — LE SHEET CONTRE NOTRE REGISTRE, PAR UNE SECONDE MAIN

> **Écrit le 19/11/2026 dans la nuit**, par la session de reprise V2
> (`notice/PROMPT_REPRISE_CHANTIER_CLASSEUR_V2_2026-11-19.md`).
> ⛔ **Lecture seule de bout en bout.** Aucune écriture en base, chez Hektor, ni dans le Sheet.
> ⛔ **La source de vérité reste `notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md`.**
>
> **Les quatre temps, dans l'ordre imposé par Frédéric, et qui ne s'inverse pas :**
> 1. mon propre calcul, sans le gel ni les pièces de l'autre session (§ 1 à § 6) ;
> 2. la comparaison avec le rapport de l'autre session (§ 7, écrit APRÈS) ;
> 3. le patch affiné, toujours dormant (§ 8) ;
> 4. l'explication (§ 9).
>
> ⭐ **L'ORDRE EST PROUVÉ PAR GIT, pas seulement affirmé** : le § 1 à § 6, le CSV et les trois
> scripts sont commités AVANT la première lecture du gel et des fichiers de l'autre session.

---

## 0. ⚠ CE QUE J'AI LU AVANT DE CALCULER, ET QUI N'EST PAS NEUTRE

Le dossier V2 se lit en entier, et son **§ 13 recopie déjà, en résumé, des conclusions de
l'autre session** : la liste des 55 liens retirés et des 109 ajoutés, les 8 lignes incertaines,
les 11 paires croisées, les copies de C5 nommées. **Je les ai donc lues.** Ce que j'ai tenu :

- je n'ai ouvert **ni** `AUDIT_INDEPENDANT_CLASSEUR_2026-11-18.md`, **ni** son CSV de verdicts,
  **ni** son CSV d'opérations, **ni** son patch, **ni** la mémoire `audit-independant-classeur-18-11` ;
- le gel (`app_classeur_lien`) **n'est pas dans la photo** : mon calcul ne peut pas le lire ;
- **aucune liste du § 13 n'entre dans le code** : il part du Sheet et des données de Hektor.

Mes **témoins** (§ 4) viennent des audits du chantier lui-même (V1 § 6, plan l. 2711-2796 :
TR42PT5H, 74IL9C8F, QH6672TZ, 1ESJE28Q, 8Q3LHGZ4, 53ZS73KW, 61OW86CS, NEFHS7JI, Y8O4NJSY),
pas des verdicts de l'autre session. Mais **l'indépendance est de méthode, pas d'ignorance** :
qui relira la comparaison du § 7 doit le savoir.

---

## 1. LES SOURCES — une photo en lecture seule, le 19/11 à 00:47

```
le Sheet             4 796 lignes, 38 colonnes        (API Google, GET seul)
                     ⚠ 2 de plus que app_classeur_ligne_id (4 794) : nees depuis
le registre          31 356 transactions               (phase2.sqlite, mode=ro, WAL)
                     - 190 transaction_origine='classeur'  -> RETIREES (regle 3)
                     = 31 166 candidates
les annonces         60 140 numeros, 5 index unis      (catalogue, archives, historique,
                                                        les deux registres des mandats)
le registre des      27 501 mandats                    - 539 nes de MODELO -> rangés sous MODELO
   mandats                                             (sinon la meme source compterait deux fois)
MODELO               26 484 mandats, 18 290 numeros    (mandats_extraits.xlsx + fevrier 2026)
les contacts         357 048                           (pour les noms portes par un identifiant)
```

La photo vit dans `.tmp/audit_v2_2026-11-19/photo/` (ignoré par git, 400 Mo) ; elle se refait
par `phase2/checks/audit_v2_photo_2026-11-19.py`.

---

## 2. LES QUATRE RÈGLES D'INDÉPENDANCE, ET OÙ LE CODE LES TIENT

```
1  ne jamais lire le gel pour choisir     le gel N'EST PAS DANS LA PHOTO
2  aucune valeur posee par nous           le registre est lu SANS les colonnes *_app,
                                          ni notes, ni conditions, ni repartition, ni
                                          avis ; app_mandat sans ses lignes « classeur »
3  les 190 creees depuis le Sheet         ecartees a la lecture, comptees (190, temoin)
4  la date d'une offre = 1re proposition  propositions_json ; une ACCEPTATION ou un REFUS
                                          date >= 11/11/2026 ne prouve rien ; la colonne
                                          `date` n'est prise qu'en dernier recours et
                                          seulement si elle est AVANT le 11/11/2026
```

⚠ Une source n'est pas « à nous » parce qu'elle est dans notre base : `app_mandat.mandants_texte`
est réécrit par **notre registre des relations**, mais ce registre est nourri par Hektor
(`export_app_payload.py:2058`), pas par le Sheet. Il reste admis. `numero_mandat` du registre
est **déduit** par nous dans 8 361 cas (`mandat_origine = deduit_unique`) — à partir des
mandats de Hektor, jamais du Sheet.

---

## 3. LA MÉTHODE

**Un pont vers le BIEN, puis le choix des TRANSACTIONS, genre par genre.**

```
le BIEN       LIEN    le lien d'administration (id=, 396 lignes) ou la reference Netty
                      (colonne B, ou prod_ref= du lien CRM) -> numero de dossier -> annonce
              MODELO  le n° du Sheet dans MODELO -> sa reference produit -> l'annonce
              MANDAT  le n° du Sheet porte par une transaction ou par le registre
              VEND    un NOM DE FAMILLE de vendeur (mandants de la transaction, de l'annonce)
              VILLE   la ville du bien
les           DATES   une transaction du BON GENRE au JOUR PRES (offre : 1re proposition ;
TRANSACTIONS          compromis : sa date, ou son acte prevu contre « Vente Prevue » ;
                      vente : « Vente Fixee » ou « Vente Reglee » ; offre refusee AVANT le
                      11/11 : son refus contre « Annulee »)
              ACQ     un NOM DE FAMILLE d'acquereur (les prenoms ne comptent pas)
              PRIX    a 1 % pres, ou a la commission pres
```

⚠ Les liens **neosphere** et **rodacom** (3 802 lignes) portent un identifiant **étranger** : ignorés.

**Les règles qui décident** — toutes nées d'un témoin qui a échoué (§ 4) :

1. ⛔ **Le prix ne désigne pas, il confirme.** Seuls DÉSIGNENT une transaction : une date au
   jour près (ou à 3 jours), l'acte prévu au jour près, le refus au jour de l'annulation, un nom
   d'acquéreur. Sur un même bien, deux acheteurs successifs ont presque le même prix.
2. ⛔ **Un acquéreur différent est un veto** quand les deux côtés portent un nom fiable — sauf
   date au jour près, et alors le drapeau le DIT.
3. ⭐ **Le contact change à l'intérieur d'une chaîne Hektor** (offre au nom de l'un, compromis
   et vente au nom de l'autre) : si UNE transaction de l'affaire porte le nom du Sheet, l'écart
   des autres est noté `ACQ_VARIE_DANS_LA_CHAINE`, sans plafond.
4. ⛔ **Une affaire « Annulée » au Sheet ne prend jamais une vente.**
5. ⛔ **La chronologie** : sans aucune date qui colle, une transaction désignée par un nom seul,
   à plus de deux ans de toutes les dates de la ligne, est écartée.
6. ⭐ **Les prénoms se reconnaissent par la mesure** : un mot qui sert au moins trois fois plus
   souvent de prénom que de nom dans les 357 048 contacts est un prénom (1 372 mots). Les mots en
   casse mixte qui n'en sont pas deviennent des noms de second rang (« Desfonds »).
7. ⚠ **Un nom voisin** (STRIPOLLI / STRIPPOLI, ressemblance ≥ 0,85, 5 lettres et plus) désigne
   faiblement et se dit `NOM_VOISIN` — BASTET / BASSET étaient deux personnes.
8. ⛔ **L'exclusivité se tranche SUR LA TRANSACTION** : une transaction disputée va à la ligne
   dont la preuve SUR ELLE est la plus forte, puis à la plus complète ; la perdante est rejugée
   sans elle (4 tours, puis une consolidation contre ce qui est réellement pris). Fin : **0
   transaction à deux lignes**, sinon le script s'arrête.

**La certitude** — un pont vers le bien (fort : LIEN, ou MODELO + VEND ; moyen : MANDAT + VEND,
MODELO + MANDAT) croisé avec la preuve de l'affaire (DATES et ACQ ; ou DATES ; ou ACQ rare) :

```
CERTAINE   date au jour pres ET nom d'acquereur ; ou l'un des deux sur un bien bien designe
SOLIDE     une seule preuve d'affaire, ou un drapeau ACQ_DIFFERENT (jamais certain)
FAIBLE     le reste
BIEN_SANS_TRANSACTION   le bien est trouve, aucune transaction de Hektor ne lui revient
```

---

## 4. LE BANC D'ESSAI — et les SIX défauts qu'il a trouvés dans MA méthode

**16 témoins**, tous établis par le chantier lui-même avant cette session. **Les 16 rendent ce
que le chantier avait établi** :

```
TR42PT5H   -> 53398, compromis 27195 seul (MORAND/ZIMMER)       = sa decision « deplacer-27195 »
739a0db1   -> 53398, offre 27196 (HALLAERT-THEYS, au jour pres)  = l'acheteur suivant
74IL9C8F   -> 46632, 23488 . 23487 . 23489 ; l'offre a 7 305 j    = « 2002 pour 2022 » chez Hektor
QH6672TZ   -> 48153, offre 24448 . vente 24449                     = vente au jour pres
1ESJE28Q   -> annonce 9194, AUCUNE transaction                     = « defaire et creer »
8Q3LHGZ4   -> annonce 46472, AUCUNE transaction                    = « defaire et creer »
53ZS73KW   -> annonce 43091, AUCUNE transaction                    = hors jeu, GIBERT perdue
bdb548a3   -> 43091, 21552 . 21551 . 21553 (CHAPUIS)                = ses trois roles
61OW86CS   -> annonce 39836, offre 19130 (STRIPOLLI ~ STRIPPOLI)   = « le classeur parle du second »
Y8O4NJSY   -> 8421, 3661 . 3660 . 3662                              = chaine saine
NEFHS7JI   -> annonce 55001, AUCUNE transaction                     ⭐ NEUF, voir § 6
23a2a8e1 . M8QJWMBM . GIYHBFP5 . T90Q8ZKA   (temoins des defauts ci-dessous)
```

**Les six défauts de ma propre méthode, aucun trouvé par raisonnement** :

1. ⛔ **le prix désignait** — `739a0db1` raflait le compromis 27195 de TR42PT5H sur le seul
   prix et les honoraires, l'acquéreur étant différent → règles 1 et 2 ;
2. ⛔ **une ligne « Annulée » prenait une vente** — la vente de `M8QJWMBM`, au jour près,
   partait à la ligne de l'acheteur précédent par son nom → règle 4 ;
3. ⛔ **le conflit se tranchait par ligne** — même cas → règle 8 ;
4. ⚠ **les noms en casse mixte étaient perdus** — « SCI FLORANTIN représentée par M. Porcu
   Daniel Mme Desfonds Florence » (`23a2a8e1`) : Desfonds EST l'acquéreur chez Hektor → règle 6 ;
5. ⛔ **un nom seul traversait les années** — `SOF45TS3`, annulée en 2023, s'accrochait à un
   achat DIGONNET de 2018 → règle 5 ;
6. ⚠ **MODELO comptait deux fois** — 539 mandats de notre registre sont nés de MODELO → rangés
   sous MODELO.

Et un défaut de **bord** : deux biens à égalité pour la 2ᵉ place se départageaient au hasard du
hachage de Python. Corrigé (numéro d'annonce, puis de transaction, en dernier départage) :
**deux exécutions à hachages différents rendent un CSV identique à l'octet**, et aucun choix
n'a bougé.

---

## 5. ⭐⭐ LE RÉSULTAT — arrêté le 19/11 vers 01:10, AVANT toute lecture du gel

**Fichier : `notice/AUDIT_INDEPENDANT_V2_MON_APPARIEMENT_2026-11-19.csv`** (séparateur `;`, BOM),
une ligne par ligne du Sheet : l'annonce, l'étiquette de dossier, l'offre, le compromis, la
vente (numéros `app_affaire_id`), les familles, la certitude, les preuves rôle par rôle, le
second candidat, les conflits, les drapeaux.

```
4 796 lignes jugees
   CERTAINE                          4 567
   SOLIDE                              159
   BIEN TROUVE, SANS TRANSACTION        68    (66 certain . 2 faible)
   RIEN                                  2    (JZ9693S0 sans nom ni date . SOF45TS3)

12 621 rattachements ligne -> transaction . 0 transaction a deux lignes
   les familles presentes : DATES 4 653 . VEND 4 645 . MANDAT 4 597 . ACQ 4 508
                            MODELO 4 391 . VILLE 2 732 . PRIX 2 686 . LIEN 888

les drapeaux    ACQ_VARIE_DANS_LA_CHAINE 501   le contact change chez Hektor, l'affaire tient
                ACQ_DIFFERENT            140   aucune transaction ne porte le nom du Sheet
                NOM_VOISIN                67   une faute de frappe probable
                DATE_ELOIGNEE              2   dont 74IL9C8F (2002 pour 2022)

les lignes qui ont perdu une transaction au profit d'une autre           64
les lignes dont les transactions portent PLUSIEURS etiquettes de dossier 112
```

**Ce que le Sheet affirme et que Hektor n'a pas** (hors les 190 de C5) — un rôle porté par une
date au Sheet, sans transaction de ce genre chez nous :

```
offre 241 . compromis 80 . vente 45      (liste : mes_roles_manquants, dans le CSV
                                          colonne roles_sheet contre offre/compromis/vente)
```

Par état du Sheet : les 3 757 « Vente réglée » sont certaines à 97,3 % (3 656) ; les 896
« Annulée » portent presque tous les sans-transaction (66 des 70).

---

## 6. ⭐ CE QUE J'AI TROUVÉ SEUL, AVANT DE COMPARER

1. ⭐⭐ **Chez Hektor, le contact acquéreur change DANS la chaîne** (501 lignes) : offre au nom
   DURIEUX, compromis et vente au nom HERNANDEZ, les trois dates au jour près (`GIYHBFP5`) ;
   vente au nom CRETET après offre et compromis TASKIN (`T90Q8ZKA`). ⛔ **Un apparieur qui juge
   le nom transaction par transaction coupe ces affaires en morceaux.**
2. ⭐ **NEFHS7JI n'a pas de transaction chez nous.** Son bien est l'annonce **55001** (mandat
   3576, vendeur SAS GIM) ; la vente AKSU est sur le lot voisin, annonce **54999** (mandat
   3577, ligne `82TBULHC`, ses trois rôles au jour près). Le Sheet porte donc une **première
   offre AKSU sur l'autre lot**, annulée, que Hektor n'a jamais eue. Frédéric l'avait vu :
   « ce n'est pas le bon bien ».
3. ⭐ **TR42PT5H n'a pas d'offre chez Hektor** : seul le compromis 27195 lui revient. L'offre
   27196 est celle de l'acheteur suivant (`739a0db1`, au jour près, refus au jour de
   l'annulation).
4. ⚠ **140 lignes où aucune transaction ne porte le nom du Sheet** malgré des dates au jour
   près : une société et son gérant (`OAUI9CKR` : DOISEAU contre « Vélo Passion Thiers »), un
   contact faux chez Hektor, ou un vrai doute (`TZ7MOW1S` : compromis annulé du jour, au nom de
   l'acheteur suivant). **Jamais « certaine » chez moi.**

⛔ **Ce que mon calcul ne dit PAS** : il ne juge pas encore le gel (§ 7), il ne propose aucun
geste, et sur une offre RENÉGOCIÉE il prend l'offre dont la 1ʳᵉ proposition tombe au jour du
Sheet — **la question de principe (1ʳᵉ offre ou offre acceptée) reste à Frédéric**.

---

## 6 bis. ⭐⭐ MON VERDICT SUR LE GEL — toujours SANS l'autre session

> Écrit après le commit `ce2301e` (01:07), en lisant le gel **chez Supabase, son maître** :
> relu par tranches, **vérifié à l'empreinte** (`8084e535…`, 12 787 liens, identique).
> ⚠ La copie locale ne suffisait pas : même compte, même somme, mais **empreinte différente** —
> elle date de la descente du 18/11 à 06:45, avant le déplacement de deux liens du bien 43091
> (sauvegarde `app_classeur_lien_avant_rattachement_43091_20261118`).
> Script : `phase2/checks/audit_v2_gel_contre_moi_2026-11-19.py` ;
> fichier : `notice/AUDIT_INDEPENDANT_V2_GEL_CONTRE_MOI_2026-11-19.csv`.

### ⛔ La version 1.1 de mon calcul — UN changement de règle, assumé

La confrontation au gel a montré une faiblesse de **ma** résolution des conflits : je donnais
un compromis disputé à la ligne qui avait **le nom**, contre celle qui avait **la date au jour
exact**. Or j'avais moi-même établi (M8QJWMBM) que **Hektor réutilise le contact de l'acheteur
précédent** sur le compromis du suivant. ➡ **Une date au jour exact bat un nom seul**, puis le
nom, puis le score. **26 choix changent** entre `ce2301e` et la v1.1, tous du même type (un
compromis passe de la ligne « au nom » à la ligne « au jour ») :

```
GQCBSQNY +C27133   2HOL5ISX 27133->27134      N1CUULMN +C4481    YRUF0S9H -C4481
Z0BDVNBZ +C4541    RGCEC677 4541->4542        U4O5Q370 +C24309   KODULWGN -C24309
Q20JKY62 +C4351    VM0FHRB3 -C4351            HPOCWXIR +C19828   M3LQT4JY -C19828
VR1K2NJW +C27685   EHQQU5U7 -C27685           6FQO29C8 +C19131   V3FO5NDA -C19131
87QOXR64 +C17427   OXQSBZ9V -C17427           2FBR2M9U +C1101    E6RLLKMN -C1101
VMWFLLW4 +C23050   SBH4QWDW -C23050           Q602VZJX +C6554    QJ9LLT05 -C6554
8GIIDS5T +C21      CW4IYXO2 -C21
```

⚠ **Ce changement vient d'une confrontation avec le gel**, pas d'un témoin du chantier : il
rapproche mon calcul du gel sur ces 26 lignes, et **ne compte donc pas comme une convergence
indépendante** sur elles. Le calcul arrêté de `ce2301e` reste lisible dans git.

### Le verdict, ligne par ligne (v1.1)

```
JUSTE                    4 549   le gel et moi disons la meme chose
JUSTE_JUMEAU                 2   Hektor a deux compromis jumeaux, le gel a pris l'autre :
                                 aussi juste que moi (0bc98552, 9CQ325R6)
PARTIEL                     64   une partie des liens est contredite ou croisee
PARTIEL_NON_PROUVE           9   une partie des liens n'est prouvee ni dans un sens ni
                                 dans l'autre (dont LQXGFCKH)
FAUX                        17   + 1 avec une copie C5 (739a0db1)
C5_COPIE                    21   + 2 (8RWTD0YX, 739a0db1) : le gel tient une creation de C5
                                 la ou Hektor porte la vraie transaction
INCOMPLET                   21   le gel n'a pas un lien que je prouve
QUESTION                    16   doublon du Sheet a preuve EGALE, ou offre RENEGOCIEE
QUESTION_BIEN                2   c0a73edd (deux lots JUQUET, une ligne) . M2G1Z1K8 (lot voisin)
SANS LIEN AU GEL            93   40 a rattacher . 51 bien sans transaction . 2 rien
                                 (dont les 2 lignes NEES depuis : 54376c72, ffcf30e6)
```

**Rôle par rôle** : 12 466 liens identiques ; le gel a 98 liens que je n'ai pas (33 offres,
52 compromis, 13 ventes), j'en ai 106 qu'il n'a pas (44, 37, 25), 28 divergent, et 23
créations de C5 doublent une vraie transaction de Hektor (8 offres, 15 compromis).

**La qualité de chaque désaccord** (la transaction du gel, jugée par ma règle) :

```
contredit_nom      51   un autre acquereur, et aucune date pour le sauver
croise             31   je la donne a une AUTRE ligne, mieux prouvee sur elle
renegociation      13   meme bien, meme acheteur, deux offres : SA question de principe
egalite             9   doublons du Sheet a preuve EGALE : mon choix est un tri
non_prouve          9   ni date ni nom, sans contradiction
chronologie         5   a plus de deux ans de toutes les dates de la ligne
moins_bien          4   designee, mais moins bien que mon choix
egal_dans_le_bien   3   jumeaux de Hektor
prouve_sans_rival   3   designee, je n'ai rien mis a sa place (biens differents)
MIEUX_QUE_MOI       2   c0a73edd : le gel suit les CHIFFRES du lot 59133, moi le LIEN
                        de l'agence vers 59136 -> QUESTION, rien ne se retire
vente_sur_annulee   1   LQXGFCKH : Hektor porte la vente MEURIN, le Sheet dit annulee
```

⛔ **Un « contredit_nom » n'est pas un « faux » prouvé** : 501 lignes justes montrent que le
contact change dans une chaîne Hektor. Sans date, un autre nom DOUTE, il ne PROUVE pas. Seuls
`croise`, `contredit_date` et un bien différent quand mon bien est certain fondent un retrait.

### Les listes nominatives (v1.1, produites par script)

```
FAUX (17)  1ESJE28Q 1f3d536a 4fc6b33a 5a4371b5 60CLRO51 8Q3LHGZ4 NEFHS7JI P46WN6R6
           SHN6RKDI TR42PT5H WJ3KA32F Y51UMZHY a8aaeb2b caea1510 d2108609 ea6a28a7
           fa06e4e5            + FAUX+C5_COPIE : 739a0db1
QUESTION (16)  045ecde7 2dfa6ef3 3308P0UX 427UDDSF 45225170 5QE9107L 5a956cad E6RLLKMN
               KT0601S6 O6R10ZQA OXQSBZ9V SBH4QWDW V3FO5NDA ce63cee9 d1cb8dd7 f1aedc01
QUESTION_BIEN (2)  M2G1Z1K8 c0a73edd
C5_COPIE (21)  1cc703d9 2FBR2M9U 3S4ZWOFK 6U5DQQ4J 87QOXR64 8NZ6V6XB 9KHYVR1M 9WQ204HP
               A07EC3DH EO8MXFE9 FWCFAN6O JRN2I7TM LKBO1TOH R0JRVFDC S3HOG6UL SWSN80FQ
               T0WL4QE7 T2GZOY5O TRJ5Y59U UTLG66LE VMWFLLW4   + 8RWTD0YX, 739a0db1
A RATTACHER (40)  1eec6575 2U5QPKRC 4G2UHO35 515RUEN3 58I5AO17 5H70KQZA 5e4c8881 6FQO29C8
                  70740f2f 72GQRHVB 7IHI7YTJ 7JXLR3JQ 8ATXF2EZ 91IHSGNC 9706WM9J 9Q0FHAKK
                  CS38OO8R D9MMB7OU DHXRAK9O EJN79TJ1 ESMCO1NC I3TFR2KG J6RGX0CQ JL8GV7RQ
                  KAYC29B7 LUX9SDIL MDOXOBIC MQ6H8TVQ O1099YC0 O8BY6AC8 PPIM4947 QXDW8EQA
                  S8BKB6FL UL12H3AQ YRUF0S9H Z6P7KE5R ZZ5WKMWM b43e76f5 b884cbd4 c6233284
```
(PARTIEL, INCOMPLET, PARTIEL_NON_PROUVE et les 51 biens sans transaction : dans le CSV.)

### ⭐ Ce que la confrontation au gel m'a appris, au-delà des comptes

1. ⭐⭐ **Hektor réutilise le contact de l'acheteur précédent** : un compromis au jour exact
   d'une affaire, au nom de celui qui avait renoncé avant. **Le nom ment plus souvent que le
   jour.** (N1CUULMN : compromis 4481 au jour de MARCHEPOIL, au nom de VIALLARD.)
2. ⭐ **Hektor porte des jumeaux** : deux compromis du même jour, même acheteur, même prix
   (24157/24158, 21803/21804, 27133/27134). Choisir l'un ou l'autre est également juste.
3. ⚠ **Des lignes du Sheet décrivent deux lots** : c0a73edd porte les chiffres du lot 59133 et
   le lien de l'agence vers le lot 59136 ; M2G1Z1K8 le mandat 16559 et l'acheteur du lot 16560.
4. ⛔ **Trois liens du gel sont faux par le BIEN, au-delà des trois déjà vus par Frédéric**
   (1ESJE28Q, 8Q3LHGZ4, NEFHS7JI) : Y51UMZHY (offre CASSARO de 2011 à 81 000 € pour une affaire
   de 2024 à 300 000 €), WJ3KA32F (offre GIMBERT sans date ni montant, sur un autre bien),
   a8aaeb2b (l'achat BOUZENAD du bien 1970, alors que la ligne porte le lien d'administration
   de l'annonce 61592 : une affaire en cours que Hektor n'a pas encore).

---

## 7. ⭐⭐⭐ TEMPS 2 — LA COMPARAISON AVEC L'AUTRE SESSION (ouverte APRÈS `6c2979c`, 01:21)

> Lu en entier : `notice/AUDIT_INDEPENDANT_CLASSEUR_2026-11-18.md` (786 lignes), ses deux CSV.
> Script : `phase2/checks/audit_v2_comparer_autre_session_2026-11-19.py` ; fichier :
> `notice/AUDIT_INDEPENDANT_V2_SES_OPERATIONS_JUGEES_2026-11-19.csv` (ses 141 opérations,
> chacune jugée par mon calcul, avec les deux preuves mesurées par la même règle).

### Les trois trous annoncés par le dossier V2, revérifiés

1. ✅ **Le « § 5 ter » existe désormais** (commit `02db14e`, postérieur à la mesure du dossier V2) :
   la liste des 87 lignes touchées, les 33 questions, les 31 traces, les copies de C5, le run.
2. ✅ **Les 18 lignes à question** : il les classe lui-même (§ 5 ter B1) et recommande déjà d'en
   sortir 4. ➡ Je les sors toutes les 18 (§ 8), comme Frédéric l'a demandé.
3. ⚠ **Ses chiffres bougent** — c'est vrai et il le dit (§ 5 ter I). Remesurés ici : gel 12 787
   (empreinte identique), 55 retraits / 109 ajouts, 20 transactions Hektor à trace.

### Ses 141 opérations contre mon calcul

```
                     ma v1.1     ma v1 ARRETEE (ce2301e, la seule strictement independante)
ajouts       86       86 / 86      85 / 86
deplacements 23       23 / 23      20 / 23
retraits     32       31 / 32      28 / 32
TOTAL       141      140          133
```

- ⭐ **Les 7 écarts entre v1 et v1.1** sont tous des compromis disputés entre deux acheteurs d'un
  même bien (19131, 17427, 23050, 6554). Ma v1 suivait le NOM, comme le gel ; ma v1.1 suit la
  DATE au jour exact, comme son patch. Le principe de la v1.1 vient de lignes où c'était **le gel**
  qui avait raison (N1CUULMN…), pas de son patch, que je n'avais pas ouvert : c'est une
  convergence avec lui, mais elle n'est pas aveugle au gel.
- ⛔ **UNE seule opération est contredite par mes deux versions** : le retrait du compromis
  27512 de `1D7EIYKW` (acquéreurs GANDON/BERAUD, prix et commission collent, seul compromis du
  dossier). **Son propre rapport recommande déjà de la sortir** (§ 5 ter B1). Deux lectures
  indépendantes concordent CONTRE le patch tel qu'il est écrit.

### Ses 350 verdicts contre les miens — qui a la meilleure preuve

**Accord** (deux chemins indépendants mènent au même endroit) : JUSTE 185 sur 190, À RATTACHER
37 sur 38, FAUX 10 sur 12 (+ `739a0db1` et `8RWTD0YX`, même issue), RIEN CHEZ NOUS 50 sur 51,
JUSTE SANS PREUVE FORTE 10 sur 12.

**⭐ Là où IL a la meilleure preuve** — et je le dis :

```
4fc6b33a   le nom DUVERT sur le compromis est un vieux contact de 2016 reutilise par l'agent :
           mon « autre acquereur » n'etait pas une contradiction
NKDC0I1M   l'offre sans date est la SEULE du dossier : sa lecture du contexte tranche
UL12H3AQ   ⛔ MON ERREUR : j'ai donne le compromis 24593 a UL12H3AQ (nom « MONTE » bien ecrit)
           alors que la chaine colle a 7N8A20H5 par la date exacte de l'offre ET la commission
           (3 500). UL12H3AQ est une offre annulee le jour meme, jamais saisie : « rien chez nous »
PPIM4947   deux offres du meme jour sans nom chez Hektor : il les departage par l'ETAT et la
           SUITE (l'acceptee mene a la vente FENON) -- meme issue, meilleure preuve que mon tri
I3R03A11   l'offre 19458 (192 000 = le prix, 1 jour apres) est bien celle de RIOS : mon veto
           (nom HEULIN) etait trop strict, sa copie C5 1001476 est bien une copie
YRUF0S9H . ZW7MKTWH . T2GZOY5O   mon attribution sortait d'un DEPARTAGE (prix ou tri) entre
           deux lignes soeurs : il a raison de les laisser incertaines
c0a73edd   le gel suit les CHIFFRES du lot 59133 (offre, prix, commission) ; moi le lien de
           l'agence vers 59136 : sa lecture est la mieux prouvee, la question reste a Frederic
```

**Là où je le contredis** : `1D7EIYKW` seulement (ci-dessus). Et une règle, qui rejoint sa
pratique : **un nom différent sans date ne fonde jamais un retrait** (`contredit_nom`).

**Ce que j'ai trouvé et que son patch ne couvre pas** — un seul audit, donc **PAS dans le patch** ;
la matière d'un 4ᵉ tour :

```
le 4e TOUR des copies C5   12 des 13 lignes qui tiennent encore une copie sans avoir ete jugees :
                           EO8MXFE9 T0WL4QE7 SWSN80FQ FWCFAN6O LKBO1TOH 9KHYVR1M 8NZ6V6XB
                           S3HOG6UL 6U5DQQ4J 2FBR2M9U JRN2I7TM 1cc703d9 -- je designe pour chacune
                           la vraie transaction de Hektor (I3R03A11 : je m'en remets a lui)
PARTIEL non juges     50   un role croise ou contredit (liste : CSV, verdict PARTIEL)
INCOMPLET non juges   13   un lien que je prouve et que le gel n'a pas
FAUX non juges         6   60CLRO51 P46WN6R6 + 4 du meme motif (1f3d536a d2108609 caea1510
                           5a4371b5 : une offre C5 + un compromis annule d'un AUTRE acheteur,
                           sans date -- « contredit_nom », donc a juger, pas a retirer)
mes erreurs probables  2   VNPQZFM8 . 6W6F4A4R (meme motif que UL12H3AQ) -- a ne PAS appliquer
```

---

## 8. ⭐⭐⭐ TEMPS 3 — LE PATCH AFFINÉ, TOUJOURS DORMANT

**Fichiers** : `supabase/patch_correction_gel_audit_v2_2026-11-19.sql` (+ `_INVERSE`, `_REPETITION`),
générés par `phase2/checks/audit_v2_generer_patch_affine_2026-11-19.py` — **ne pas les retoucher
à la main**. Les opérations, gardées et sorties, avec leur motif :
`notice/AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv`.

⛔⛔ **IL PORTE SON `commit;`** (une seule instruction, la dernière ligne) : il ne se joue JAMAIS
« pour voir ». **Il n'a pas été joué.**

```
CE QU'IL FAIT     45 liens retires . 78 ajoutes . le gel passe de 12 787 a 12 820
                  lignes sans lien 91 -> 71   (le patch du 18/11 : 60)
                  chaque operation est SOUTENUE par les deux audits (le script s'arrete sinon)
CE QU'IL NE FAIT  ni transaction, ni valeur posee, ni Hektor, ni les 8 lignes INCERTAINES,
     PAS          ni les 18 lignes a question
```

**Les trois corrections du § 8 du dossier V2, et ce que j'y ajoute :**

1. ⛔ **Les deux colonnes de mesure ne sont plus détournées** : `etage` = le libellé constant
   « audits independants 18-19/11 » ; `preuves` = **le vrai compte** des familles de preuve du
   lien, mesuré par mon apparieur (2 : 17 liens . 3 : 27 . 4 : 3 . 5 : 8 . 6 : 11 . 7 : 12) —
   jamais 0. ⚠ Les 17 liens à 2 familles sont des lignes que leur numéro de mandat ne menait
   nulle part, rattachées par trois dates au jour exact et le nom du vendeur : trois dates
   exactes restent UNE famille. La phrase du juge reste dans le CSV.
   Confiance écrite : « sûre » (40) seulement si l'autre session dit « certaine » ET mon calcul
   CERTAINE ; sinon « bonne » (38).
2. ⛔ **Les 18 lignes à question sortent** — 33 opérations — avec `QJQ9M4OF` (indivisible de
   `D9MMB7OU`, son propre rapport le dit), puis **EN CASCADE 4 opérations** dont la cible resterait
   tenue par une ligne sortie : `6FQO29C8` ×2 (19131, 19133, tenues par V3FO5NDA), `H6CTRVR6`
   (11415, tenue par E9GL6MUS), `9WQ204HP` (4480, tenue par 3308P0UX). **37 sorties en tout.**
   Un retrait seul ne casse jamais l'exclusivité : il reste (OXQSBZ9V lâche 17427 ; 427UDDSF lâche
   3648 et 3650 — leur destinataire attend ta réponse).
3. ⚠ **La suite est enchaînée** : `notice/AUDIT_INDEPENDANT_V2_TRACES_A_REPOSER_2026-11-19.csv` —
   16 transactions de Hektor portent une trace de nous (8 dates d'annulation, 3 motifs,
   1 commission, 15 notes) : 6 à reposer pour la ligne qui reçoit, 8 à retirer, 2 en attente de
   ta réponse (3650 → 9Q0FHAKK, 17427 → 87QOXR64). La répétition les compte (attendu avant
   nettoyage : 10 et 15).

**Et ce que mon audit ajoute :**

4. ⭐ **La garde lit l'EMPREINTE du gel** (`8084e535…`), pas seulement son compte — c'est le piège
   rencontré cette nuit : la copie locale avait le bon compte et une autre empreinte. Et elle
   vérifie, AVANT toute écriture, que **chaque cible sera libre** (aucune autre ligne ne la tient,
   sauf une ligne qui la lâche dans ce même patch). ⚠ *Ajouté au bord, après le commit `493b21f` :
   mon en-tête le promettait, seul le contrôle final l'aurait vu, après coup.*
5. ⭐ **Le retour arrière ne juge que SA part** (leçon 31) : il retire ses 78 poses, remet ses 45
   retraits à l'identique, et DIT (sans refuser) si le reste du gel a changé depuis. ⚠ L'inverse
   du 18/11 exigeait un gel entier identique à la sauvegarde : il aurait refusé de défaire après
   n'importe quel autre geste légitime.
6. ⭐ **Le témoin inverse compare 7 colonnes** (rôle, confiance, preuves, étage, auteur, ligne,
   date de gel) au lieu de 4, et un **témoin positif** vérifie que les 78 poses sont là et que les
   45 retraits sont partis.

**Prouvé SANS RIEN ÉCRIRE, sur la base vivante, le 19/11 vers 02:15 :**

```
la GARDE COMPLETE, jouee seule (que des lectures)    passe : 12 787 liens, empreinte identique,
                                                     45 retraits presents avec leur role,
                                                     78 cibles presentes avec le bon genre
une SIMULATION de l'etat d'apres (gel - 45 + 78),    12 820 liens . 0 transaction a deux lignes
  par une requete en lecture, avec l'empreinte de    . 0 ligne a deux liens pour un role
  ses propres listes (= celles du fichier)           . 71 lignes sans lien . 78 ajouts presents
la GARDE DE LIBERTE (ajoutee au bord), en lecture    0 cible tenue par une ligne qui ne la lache
                                                     pas ; TEMOIN : 15 cibles sont tenues
                                                     aujourd'hui, toutes lachees par un retrait
                                                     du meme patch (les deplacements)
EXPLAIN de l'insertion (sans execution)              colonnes et types acceptes
temoin apres coup                                    gel inchange : 12 787, meme empreinte,
                                                     0 pose, pas de sauvegarde creee
les rangs du Sheet ecrits dans le patch              0 ecart avec le Sheet de cette nuit
```

**Ce que ça pourrait casser ailleurs** — mesuré par l'autre session côté code (§ 5 ter F),
non contredit : aucun déclencheur, aucune fonction, aucune tâche ne lit le gel ; deux sentinelles
le regardent. `data.classeur_lien_casse` reste à 0. `data.classeur_ligne_sans_lien` (seuil 92)
passera à **71 et restera verte en tolérant 21 lignes de trop** → son seuil doit suivre la mesure
(geste 6, une modification de code, avec son « vas-y »). La descente du matin copiera la
sauvegarde (sans clé primaire) : la relecture par rang l'a déjà fait sans perte pour trois
sauvegardes du gel. ⚠ Et tout script qui poserait des valeurs du Sheet APRÈS le patch suivrait
les nouveaux liens : c'est voulu, mais les 16 traces du point 3 restent sur l'ancienne
transaction tant que le geste 2 n'est pas fait.

---

## 9. TEMPS 4 — L'EXPLICATION À FRÉDÉRIC (le résumé ; le message complet est dans la conversation)

1. **Seul**, j'ai apparié les 4 796 lignes sans le gel : 4 567 certaines, 159 solides, 68 biens
   sans transaction, 2 sans rien ; 16 témoins du chantier tenus ; six défauts de MA méthode
   trouvés et corrigés en route.
2. **Avec l'autre session**, l'accord est très large (133 de ses 141 opérations soutenues par ma
   version arrêtée, 140 par ma version 1.1). Elle a la meilleure preuve sur 9 lignes, moi sur une
   (1D7EIYKW, où son propre rapport me rejoint).
3. **Le patch affiné** garde 104 opérations (45 retraits, 78 ajouts), sort les 18 lignes à
   question et 4 opérations qui en dépendent, ne détourne plus les colonnes, et sa garde comme sa
   simulation passent sur la base vivante. **Il attend ton « vas-y ».**
4. **Après lui, dans l'ordre** : les 16 traces (geste 2), les copies de C5 des deux côtés
   (geste 3), le 4ᵉ tour (geste 4, dont mon audit fournit la matière), créer 1ESJE28Q et 8Q3LHGZ4
   (geste 5), le seuil de la sentinelle (geste 6), puis les 36 / 207 et les 91 / 277.
