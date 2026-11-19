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

*(§ 7 à § 9 écrits après la lecture du gel et du rapport de l'autre session.)*
