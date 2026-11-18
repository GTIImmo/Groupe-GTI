# PROMPT DE REPRISE — LE CHANTIER CLASSEUR (Sheet → registre des transactions)

> **Écrit le 18/11/2026 au soir, à la demande de Frédéric**, pour être lu EN ENTIER
> par une session neuve avant le premier geste. Tous les chiffres ci-dessous ont été
> **mesurés ce soir-là, en lecture seule**. Le parc bouge : les rejouer avant de
> conclure quoi que ce soit.
>
> ⛔ **La source de vérité du chantier reste `notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md`.**
> Ce document est une PORTE D'ENTRÉE, pas un second registre de décisions.
> **Ne jamais ouvrir un second registre de décisions.**

---

## 0. CE QUE FRÉDÉRIC DEMANDE À LA SESSION NEUVE

Dans ses mots, le 18/11 :

> « d'abord faire un audit de la situation actuelle de ma base, serveur et apps au sujet
> de ce chantier ; ensuite un audit par lui-même entre le Sheet et mon registre des
> transactions pour qu'il me donne son verdict. Il doit être capable, avec ma data, le
> Sheet et le classeur MODELO, de trouver pour chaque ligne du Sheet son dossier de
> transactions — donc trouver nos erreurs — et finir le rapatriement. »

Puis **l'étape 4, puis l'étape 5**, jusqu'à la fin (voir § 9).

⭐ Et il a ajouté : *« attention au geste, consulte le projet, nous avons rencontré
beaucoup de problèmes avec certaines écritures »* → **§ 11 est la section la plus
importante de ce document.**

---

## 1. ⛔ CE QUI NE SE DISCUTE PAS

Ces règles sont permanentes. Elles ne se renégocient pas.

- **Écrire UNIQUEMENT en français**, même les petites phrases.
- **Aucun tableau dans les messages** : phrases et listes courtes.
- **L'identité d'un administrateur ne va JAMAIS sur un document.**
- **Accord OBLIGATOIRE, toujours**, avant : une écriture en base de production · une
  écriture chez Hektor (créer, modifier, supprimer) · lancer un run ou un rattrapage ·
  redémarrer un service · déployer · tout geste irréversible.
- **Stager fichier par fichier.** Jamais `git add .` : 73 fichiers non suivis traînent.
- **Relire le STAGE juste avant le commit**, et **la liste à pousser juste avant le push**.
- **`git commit -m` n'existe plus** : tout message passe par un fichier et `-F`.
- ⛔ **Jamais de backquote dans un heredoc bash** : le shell l'exécute. Et un document
  long truffé d'apostrophes passe par l'outil d'écriture, pas par un heredoc.
- **Ne pas décider seul un périmètre.** Un message court, en cadrage, est une question.
- **Jamais `tail -f` sur un journal du run.** Ne jamais lancer le worker pour l'inspecter.
- **Ne rien écraser** : additif et chirurgical, jamais de remplacement massif.
- **Une autre session travaille en parallèle** : relire `git log` avant d'écrire.

---

## 2. OÙ EN EST LE CHANTIER — mesuré le 18/11/2026 au soir

### L'appariement (étape 1) — quasiment fermé

```
4 794   lignes au Sheet          (table app_classeur_ligne_id)
4 703   lignes appariees         98,1 %
   91   lignes SANS AUCUN LIEN   (vue app_v_classeur_ligne_sans_lien)
12 787  liens                    sur 12 787 affaires DISTINCTES
                                 -> aucune affaire n'est prise deux fois
   confiance : 12 484 sure . 26 bonne . 277 A VALIDER
   roles     :  4 676 offre . 4 376 compromis . 3 735 vente
    9   liens « casses »         BENINS : Hektor ne porte plus la transaction,
                                 nous la gardons, le lien tient
    1   ligne declaree HORS JEU  (53ZS73KW, GIBERT -- voir § 6)
```

### Le rapatriement (étape 3) — ce qui est EN PRODUCTION

```
C8   3 729  dates de reglement   + 3 671 numeros de facture, sur leur VENTE
C3     450  dates d'annulation   sur leur COMPROMIS
C4     169  motifs d'annulation  en SIX libelles valides par lui
     4 325  notes                (origines classeur:F, classeur:G, classeur:F+G)
        28  conditions suspensives . catalogue a SIX clauses
C2      66  honoraires d'entree  + 6 de sortie
C1       7  charges au registre  + 853 au carnet des mandats
C9   2 588  avis                 + 2 560 etiquettes de dossier
C5     195  transactions creees  96 offres refused . 35 compromis cancelled
                                 . 64 offres accepted . 0 partie creee
B1       3  colonnes de classe A + la table des avis
B2 B3       les 2 sentinelles posees, avec temoin positif
D1     195  liens pour les transactions creees (elles n'en avaient AUCUN)

4 515   affaires portent une note nee du classeur
31 356  transactions au registre (app_affaire_ledger)
```

⚠ **`etat_au_classeur` n'est PAS une colonne** : c'est une clé dans le `payload_json`
d'un travail. Aucun code ne la lit — c'est une trace, pas une donnée qui décide.

### Ce qui reste

```
202   lignes du classeur NON POSEES  (notice/CLASSEUR_CE_QUI_MANQUE_2026-11-17.csv)
        146  aucun lien                   88 offres . 37 compromis . 21 ventes
         56  la chaine existe, la transaction NON
 36   lignes tranchees « le classeur a raison »  -> ⛔ RIEN N'EST POSE EN BASE
        (notice/LISTE_LIGNES_CLASSEUR_A_POSER_2026-11-18.md)
 13   arbitrages du 18/11                        -> § 6
277   liens « a valider » + 91 lignes sans lien  -> L'APPARIEMENT QUI RESTE
```

Non tranchés : **C6** les ventes en conflit (la règle est à refaire) · **C10** le prix
(la colonne mélange 1 008 départements) · **AA** à l'écran ou non · **U/X** « Signé » et
« Signée » — à quoi servent-ils ? · **AC / AE / AK** jamais mesurées · et les signes
**`BVok`, `AVNT`, `dossOk`, `cpmis`, `copie`** de la colonne F, **toujours non décodés**.

---

## 3. ⛔⛔⛔ LE PIÈGE N° 1 — L'ACCORD CIRCULAIRE

**C'est le piège qui ruinerait exactement l'audit indépendant que Frédéric demande.**

Nous avons **déjà posé 15 211 valeurs du classeur dans la base** (§ 2). Comparer le
Sheet à notre registre AUJOURD'HUI mesure donc, pour une large part, **un accord que
nous avons fabriqué nous-mêmes**.

C'est arrivé le 17/11 : **874 des 897 « accords » annoncés étaient circulaires.**

⭐ **LE REMÈDE, et il est disponible** : les sauvegardes datées sont le témoin d'AVANT.

```
app_affaire_ledger_avant_doublons_classeur_20261118
app_affaire_ledger_avant_inversion_honoraires_20261102
app_affaire_ledger_avant_numero_50128_20261022
app_affaire_note_avant_doublons_classeur_20261118
app_classeur_lien_avant_correction_20261117
app_classeur_lien_avant_doublons_classeur_20261118
app_classeur_lien_avant_rattachement_43091_20261118
app_classeur_lien_avant_regel_20261113   (12 422 liens)
app_classeur_lien_avant_regel_20261117   (12 595 liens)
app_affaire_repartition_avant_classeur_20261113 / _20261114
```

➡ **Tout verdict « le Sheet et notre base sont d'accord » doit dire SUR QUOI il porte** :
une valeur que Hektor nous a donnée, ou une valeur que nous avons posée depuis le Sheet.
Les colonnes `*_app` du registre — `honoraires_entree_app`, `honoraires_sortie_app`,
`charge_commission_app`, `date_annulation_app`, `motif_annulation_app`,
`numero_facture_app`, `vente_reglee_app`, `numero_mandat_app` — **sont les nôtres** :
elles ne prouvent jamais un accord, elles le racontent.

---

## 4. LES TROIS RÈGLES DE FRÉDÉRIC — elles tranchent tout

1. **« On ne reprend que ce que Hektor ne rendra plus »** : le bien est SORTI du parc
   vivant, OU la date a plus d'un an. ⛔ **JAMAIS une date dans le futur.**
2. **« La date d'annulation du Sheet est celle du COMPROMIS. »** ⭐ Elle a fait tomber
   446 cas ambigus à ZÉRO — *une règle juste supprime les cas douteux, elle ne les
   déplace pas.*
3. **La forme suit la question** : une donnée qui qualifie **une transaction** est une
   **colonne du registre** ; une donnée qui qualifie **le dossier** est une **table
   accrochée par l'étiquette**.

⭐⭐⭐ **ET SA CORRECTION DU 17/11, qui vaut pour tout le chantier** :

> « Ma règle sur les données des transactions en cours ne portait PAS sur les notes. »

Sa règle n° 1 protège contre **LE CONFLIT**. La bonne question n'est donc pas
« l'affaire est-elle en cours ? » mais **« HEKTOR PORTE-T-IL CETTE DONNÉE ? »** — et la
mesure dit NON pour les notes comme pour les conditions suspensives (0 sur 18 591).

---

## 5. LA RÈGLE DU CHANTIER, ET LES SEPT GARDES

⭐⭐⭐ **Pourquoi la règle n° 1 existe** : 24 compromis « en attente » allaient être posés
avec des dates **dans le futur**. Le classeur servait là de carnet de rendez-vous, pas
d'archive. Le croisement qui la justifie :

```
   statut du bien   futur  <3 mois  3-12 m  1-3 ans  >3 ans
   Actif               38        9       0        0       0
   Vendu                1        1       7       33      36
```

**Aucun bien « Actif » ne porte une date de plus de trois mois.** Les deux populations
ne se mélangent pas.

### ⛔⛔ LES SEPT LECTEURS QU'UNE TRANSACTION SANS NUMÉRO HEKTOR RÉVEILLE

Toutes gardées par `transaction_origine`, vérifiées une par une le 16/11 :

```
   1  vue app_affaires_sans_numero_hektor        crie
   2  sentinelle data.transaction_disparue       crie
   3  filet du worker poserNumerosManquants      ecrirait un numero FAUX
   4  l'ecran                                    SANS OBJET : il exige un numero
   5  filet du cockpit export_app_payload.py     affichait « plus dans Hektor »
   6  enqueue_refus_offres_mortes_lot.js         ⛔ IL ECRIT CHEZ HEKTOR
   7  fonction app_statut_redescente_calcule     ⛔ ELLE REDESCEND UN STATUT
```

⭐⭐⭐ **LA LEÇON, PAYÉE DEUX FOIS LE MÊME JOUR** : le 6e a été manqué le matin parce que
le balayage cherchait `present_in_hektor`, alors qu'il se déclenche sur **l'ÉTAT d'une
autre transaction de la chaîne**. **Une famille de lecteurs ne se balaie pas par UN
critère : avant chaque nouvelle famille, refaire le balayage AVEC LE CRITÈRE DE CETTE
FAMILLE**, et avant de générer le patch.

⭐ **`app_affaire_compte_encore` explique tout le 7e** : elle rend VRAI quand le numéro
est VIDE — c'est son dessein. Mais une reprise du classeur n'attend aucun numéro.
Témoins : `compte_encore(null,false) = true` · `compte_encore('4320',false) = false`.

### ⭐ L'état choisi décide ce qui se déclenche

```
   offre 'refused'       aucune des 4 regles de chainage
   compromis 'cancelled' la regle [A] ne vise que les compromis SANS DATE
   offre 'accepted'      la regle [B] -- mais elle S'ECARTE si la chaine porte
                         autre chose qu'une offre (95,9 % des cas, mesure)
   vente                 state = NULL : aucune de nos 9 281 ventes n'a d'etat
```

### ⭐⭐ ET L'EXCLUSION DÉLIBÉRÉE SE DÉCLARE

Une ligne du classeur qu'on ne veut plus voir revenir se met dans
**`app_classeur_ligne_exclue`** (clé `id_unique`, avec le `pourquoi`), et la garde est
branchée en étape ①bis de `phase2/checks/poser_offres_annulees_classeur_2026-11-16.py`.
⛔ **Un avertissement en tête d'un patch n'arrête pas un script : une exclusion se
DÉCLARE.** Et la garde s'éprouve par un **témoin positif** — un « 0 écartée » a la même
tête quand la garde ne marche pas.

---

## 6. SES 14 ARBITRAGES, ET SES MOTS

Ils vivent dans la page d'arbitrage, toujours en ligne :
**https://claude.ai/artifact/PRXmPfRhMSX77Cm9F5WcL7**
Ses choix sont dans la base de cette page, collection `reponses2` (lisible avec l'outil
de base de données d'artefact). **Ce qui suit est l'état au 18/11 au soir.**

### Les quatre liens faux du gel

**1. Ligne 3464, `1ESJE28Q`** — Ambert, mandat 16758 au classeur. Le gel pointe
l'annonce 26801 (BRUET, mandat 2816, 2012) ; le classeur décrit RECAMIER, 2024.
→ **« Le défaire et créer l'affaire sur l'annonce 9194 »** (le bon bien est chez nous,
mandants « Patrick, Stéphanie et Michèle RECAMIER », mais sans aucune transaction).
> Son mot : « Je pense que cela n'est peut-être pas le bon, apparaissent 2012 apps et le sheet 2024 »

**2. Ligne 3579, `8Q3LHGZ4`** — Saint-Pal-de-Mons, mandat 16239. Le gel pointe
l'annonce 16831 (CHAPELON, 2014) ; le classeur décrit ROQUES, annulée le 23/10/2023.
⭐ **Son propre apparieur refusait de le lier** (confiance « aucune »).
→ **« Le défaire et créer l'affaire sur l'annonce 46472 »**.

**3. Ligne 227, `53ZS73KW`** — Yssingeaux, mandat 16992. ✅ **TRANCHÉ ET FAIT le 18/11.**
Le compromis 17016 et l'offre 32791 sont repartis sur la ligne 4505 (`bdb548a3`,
CHAPUIS), qui porte désormais ses trois rôles. L'affaire GIBERT n'est pas créée, et la
ligne 227 est **déclarée hors jeu** pour qu'aucun lot ne la recrée.
⬜ **Reste ouvert** : chez Hektor le compromis de CHAPUIS est marqué « clôturé » alors
que le 16/07/2025 est l'annulation de GIBERT.
> Son mot : « Problème, ce n'est pas le bon lien, je pense à vérifier affaires entre le sheet et apps les dates »

**4. Ligne 173, `TR42PT5H`** — Vollore-Ville, annonce 53398. Le gel pointe la chaîne
27196 ; quatre valeurs du classeur tombent sur la **27195**. Le mandat a été réattribué
sur ce bien : 15482 jusqu'au 06/02/2025, puis 18176.
→ **« Déplacer le lien vers la chaîne 27195 »**.
> Son mot : « Erreur, pas la bonne, apparaissent offres, les dates sont différentes »

### Les deux dates d'offre

**5. Ligne 1401, `74IL9C8F`** — classeur 31/01/2022, nous 2002. Preuve interne : le
compromis tombe au jour exact des deux côtés (25/04/2022).
→ **« Poser 31/01/2022 »**. ⛔ **MAIS VOIR § 7 : CE GESTE EST IMPOSSIBLE EN L'ÉTAT.**

**6. Ligne 1135, `QH6672TZ`** — classeur 07/08/2019, nous 2020. La vente tombe au jour
exact (19/12/2023).
→ **« Poser 07/08/2019 »**. ⛔ **MÊME RÉSERVE.**

### Les quatre lignes douteuses de la pose

**7. Ligne 3991, `NEFHS7JI`, commission** — classeur 2 974 €, nous 18 000 €.
→ **« Non : la chaîne est annulée, on ne pose pas »**.
> Son mot : « Il y a une erreur sur l'annonce, c'est pas le bon bien » — ⭐ **ET IL A RAISON, c'est mesuré : notre affaire porte 383 000 €, le classeur 25 000 €.**

**8. Ligne 3991, `NEFHS7JI`, date d'offre** — classeur 18/02/2021, nous 30/03/2012.
→ **« L'appariement lui-même est douteux : à auditer »**.

**9. Ligne 17, `Y8O4NJSY`, commission** — classeur 6 000 €, nous 10 000 €, sur un prix
de 340 000 € (donc 1,8 % contre 2,9 %). La chaîne est saine : compromis 3660 actif,
offre 3661 acceptée, vente 3662.
→ **« Oui, poser 6 000 € »**. ✅ **Faisable : `honoraires_entree_app` est libre.**

**10. Ligne 3938, `61OW86CS`, commission** — classeur 1 800 €, nous 9 800 €.
→ **« Écarter cette ligne : les deux valeurs sont suspectes »**.
> Son mot : « et donne moi le dossier et annonce chez nous rattaché »
>
> ⭐ **RÉPONDU LE 18/11, ET C'EST PIRE QUE PRÉVU : ce lien pointe sur DEUX BIENS
> DIFFÉRENTS.** Le compromis 4496 est sur l'annonce **9769** (dossier 1392268,
> 155 000 €, honoraires 9 800 €) ; l'offre 19130 sur l'annonce **39836** (dossier
> 1368491, **12 000 €**). Le classeur parle du second. **Aucun des deux dossiers n'est
> dans la table des dossiers vivants** : vendus ou archivés.
> ⚠ Et l'offre 19130 est une des 661 du 11/11 : son journal dit **acceptée le
> 27/02/2021, refusée par nous le 11/11 à 18:50:50**.

### La règle de fond

**11. `REGLE-transaction-cible`** — sur quelle transaction de la chaîne pose-t-on la
valeur du classeur ?
→ **« Sur toutes les transactions de la chaîne »**.
⛔ **VOIR § 7 : CE CHOIX CONTREDIT LE SCRIPT DÉJÀ JOUÉ.**

### Ce que la journée du 18/11 a ouvert

**12. `OFF4281-36794-reparer`** — la seule offre encore cassée par le geste du 11/11.
Le classeur dit vente réglée le 28/03/2023, facture GGTI00003061 ; chez Hektor l'offre
est refusée depuis le 11/11 à 19:22. Son compromis 17456 est « clôturé » alors que la
vente du 24/03/2023 a eu lieu avec le même acquéreur CREVON.
→ **« Oui, la réaccepter »** — chemin éprouvé :
`Console/enqueue_reaccepter_offres_refusees_a_tort.js` (19/19 le 12/11, témoin inverse).
⛔ **C'est une écriture chez Hektor : accord explicite requis au moment du geste.**

**13. `REFUS5-classeur-contredit`** — les 5 autres offres que le classeur contredit
(biens 34296, 11820, 28653, 12728, et 17724 ambigu). Leur compromis n'est PAS dans les
8 clôturés à tort : **leur refus a une autre cause, non élucidée.**
→ **« Les auditer une par une avant tout geste »**.
Liste nommée : `notice/C_REFUS_11_11_JUGES_PAR_LE_CLASSEUR_2026-11-18.csv`.

**14. `CP8-clotures-malgre-vente`** — les 8 compromis « clôturés » alors que la vente
s'est faite (biens 43091, 48093, 36794 ×2, 46585, 48311, 34048, 52790).
→ **« À reprendre plus tard »**.
Audit complet : `notice/AUDIT_COMPROMIS_CLOTURES_MALGRE_LA_VENTE_2026-11-18.md`.

---

## 7. ⛔ CE QUE L'AUDIT DU 18/11 AU SOIR A CORRIGÉ — À LIRE AVANT DE POSER

### ⛔⛔ Les deux dates d'offre (fiches 5 et 6) ne peuvent PAS être posées en l'état

**Il n'existe aucune colonne pour une date d'offre venue du classeur.** Les colonnes du
classeur dans `app_affaire_ledger` sont : `honoraires_entree_app`,
`honoraires_sortie_app`, `charge_commission_app`, `date_annulation_app`,
`motif_annulation_app`, `numero_facture_app`, `vente_reglee_app`, `numero_mandat_app`.
**Pas de date d'offre.**

La seule cible serait la colonne `date` — et **le run la relit chez Hektor chaque nuit** :
`R2_CHAMP_VERS_COLONNE` la recopie (`phase2/sync/affaire_ledger.py:1707`) et la
protection lui est **nommément refusée** par
`R2_JUGES_SUR_LE_REGISTRE = {("offre","date"), ...}` (l. 1718), pour que R3 puisse
comparer. **Une valeur posée là serait effacée.**

⭐ **ET LE JOURNAL DE L'OFFRE PORTE LUI-MÊME LA MAUVAISE ANNÉE — mesuré :**

```
offre 23488 (74IL9C8F)  colonne 2002-01-31 23:00  journal 2002-01-31  -> faute CHEZ HEKTOR
offre 24448 (QH6672TZ)  colonne 2020-08-07 22:00  journal 2020-08-07  -> faute CHEZ HEKTOR
offre 19130 (61OW86CS)  colonne 2026-11-11 18:50  journal 2021-02-27  -> CICATRICE DE NOTRE GESTE
offre  3661 (Y8O4NJSY)  colonne 2025-04-28 22:00  journal 2025-04-28  -> saine
offre 26397 (NEFHS7JI)  colonne 2012-03-30 22:00  journal 2012-03-30  -> saine
```

➡ **Donc poser la date chez nous ne corrigerait RIEN de visible** : les cinq lecteurs
alignés le 12/11 lisent le journal, et le journal est faux. **La décision à prendre par
Frédéric est : créer une colonne dédiée, ou corriger chez Hektor.** Les deux sont des
écritures, aucune n'est faite.

### ⛔ La règle « sur toutes les transactions » contredit le script déjà joué

`phase2/checks/c2_generer_commissions_2026-11-17.py` pose sur **la transaction la PLUS
AVANCÉE de la chaîne** (vente > compromis > offre), et c'est écrit en tête du script
(l. 128) et dans le patch (l. 280). **66 lignes sont déjà posées ainsi** : 14 sur une
vente, 8 sur un compromis, 44 sur une offre.

➡ **La règle « toutes » triple le périmètre et change l'existant.** À faire trancher :
on repasse sur les 66, ou « toutes » ne vaut que pour la suite ?

### ⚠ Deux de mes propres fiches d'arbitrage étaient fautives

- **Fiche 10 (`61OW86CS`)** : le « 81,7 % » comparait **le prix d'un bien aux honoraires
  d'un autre**. Sa décision d'écarter était juste, ma raison était fausse.
- **Fiche 7 (`NEFHS7JI`)** : le « 72 % » était calculé avec les honoraires de notre bien
  sur le prix du classeur. Le vrai taux est **18 000 sur 383 000, soit 4,7 %** — rien
  d'anormal. L'anomalie est l'appariement, et **c'est lui qui l'a vu.**

➡ ⭐⭐ **LA LEÇON : un ratio entre deux sources ne vaut rien tant qu'on n'a pas vérifié
que les deux nombres parlent du MÊME bien.**

---

## 8. CE QUI RESTE, DANS L'ORDRE LOGIQUE ÉTABLI LE 16/11

Le critère n'est pas « du plus facile au plus dur » : **ce qui dit ce que les autres ne
verront pas passe d'abord ; ce qui a un préalable non tranché passe en dernier.**

```
A   les 13 arbitrages du § 6, dans l'ordre : les 3 lectures d'abord
      (REFUS5 auditer . NEFHS7JI auditer . 61OW86CS deja repondu),
      puis les 3 gestes en base (2 liens a defaire+creer, 1 a deplacer),
      puis la pose de Y8O4NJSY, puis l'ecriture chez Hektor (OFF4281)
B   les 36 lignes tranchees « le classeur a raison » -- RIEN N'EST POSE
C   les 277 liens « a valider » et les 91 lignes sans lien
      ⭐ LE CRITERE QUI TRANCHE : la PREUVE INTERNE -- une autre transaction de
        la chaine qui tombe AU JOUR PRES. Un seul signal faible (un nom, ou un
        n° de mandat seul) ne suffit pas : c'est le motif des liens faux du gel.
D   les 202 lignes non posees (146 sans lien . 56 chaine sans transaction)
E   la lecture tolerante de Y (2e geste de C8)
F   A5 : 967 lignes sans role vente, dont 311 sans rien
G   C6 . C10 . AA . U/X . AC/AE/AK . les signes non decodes de la colonne F
H   l'ETAPE 4 puis l'ETAPE 5 (§ 9)
```

---

## 9. LES ÉTAPES 4 ET 5 — ce qu'il veut enchaîner

Elles sont dans `notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md`, l. 6071 et 6080.

### ÉTAPE 4 — la porte et les vagues

```
4.1 ⬜ ACCORD   la porte sans ecran : une RPC qui APPELLE
                app_modifier_affaire_optimistic, JAMAIS une copie
4.2 ⬜ ACCORD   une affaire qu'il choisit
4.3 ⬜ ACCORD   la reprise complete, LA NUIT (~2 a 3 h, arret sur conflit)
```

### ÉTAPE 5 — la bascule

```
5.1 ⬜ FREDERIC  lire les Apps Script du classeur (10 min) -- ⛔ IL BLOQUE 5.3
5.2 ⬜ ACCORD    ecrire nos UUID dans la colonne affair_uuid du Sheet
                 ⭐ LE GEL SERT ICI, UNE FOIS -- puis il DORT
5.3 ⬜ ACCORD    le routeur : l'app ecrit dans le classeur, par l'uuid
```

⛔⛔ **RÉSERVE POSÉE LE 13/11, À LIRE AVANT D'OUVRIR 5.2 : l'export doit IGNORER les
chaînes entièrement mortes.** 14 chaînes (16 transactions) portent un numéro de dossier
alors qu'aucune de leurs transactions ne compte encore — Hektor les a supprimées, les 18
confirmées une par une le 13/11 avec témoin positif. Biens : 1970, 8494, 35467, 39607,
39684, 40318, 40519, 43437, 49584, 58979, 61534, 62049, 62097.
Le filtre : `public.app_affaire_compte_encore(hektor_affaire_id, present_in_hektor)`.

⚠ **ET NE RIEN RETIRER EN BASE** : l'étiquette est posée sur une CHAÎNE entière, et
2 chaînes sont MIXTES (2 transactions mortes + 5 vivantes, biens 47146 et 58932).
Retirer l'étiquette des mortes casserait le numéro de 5 transactions valides.
**« Un numéro ne se perd jamais » : on FILTRE À LA LECTURE, on n'efface pas.**

⚠ **À partir de 5.3 le chantier change de nature : nous devenons ÉCRIVAINS du Sheet.**
Ce n'est plus du rapatriement. Le dire avant de commencer.

---

## 10. LES ADRESSES

### Les documents

```
le plan du chantier       notice/PLAN_CHANTIER_CLASSEUR_2026-10-28.md  (la source)
les 38 colonnes           notice/A4bis_LES_38_COLONNES_DU_CLASSEUR_2026-10-31.md
la colonne F decodee      notice/C4_LE_DECODAGE_DE_LA_COLONNE_F_2026-11-16.md
l'apparieur v2            notice/A19_APPARIEUR_V2_CONTRE_LE_GEL_2026-11-13.md
l'audit de situation      notice/A15_AUDIT_SITUATION_CHANTIER_CLASSEUR_2026-11-09.md
la regle d'appariement    notice/REGLE_APPARIEMENT_2026-10-23.md
ce qui manque             notice/CLASSEUR_CE_QUI_MANQUE_2026-11-17.csv      (202)
les 36 tranchees          notice/LISTE_LIGNES_CLASSEUR_A_POSER_2026-11-18.md
les 6 refus contredits    notice/C_REFUS_11_11_JUGES_PAR_LE_CLASSEUR_2026-11-18.csv
les 8 compromis           notice/AUDIT_COMPROMIS_CLOTURES_MALGRE_LA_VENTE_2026-11-18.md
le dernier appariement    notice/APPARIEMENT_CLASSEUR_2026-11-18_...csv
la porte d'entree projet  CLAUDE.md  (la METHODE, section 0)
```

### Les scripts

```
l'apparieur               phase2/checks/apparier_classeur.py
le re-gel additif         phase2/checks/regel_additif_liste.py
le rapport du gel         phase2/checks/rapport_gel_tous_les_champs.py
C2 les commissions        phase2/checks/c2_generer_commissions_2026-11-17.py
C3 les dates d'annulation phase2/checks/c3_generer_patch_dates_annulation_2026-11-16.py
C4 motifs et conditions   phase2/checks/c4_generer_motifs_et_conditions_2026-11-17.py
C8 vente reglee           phase2/checks/c8_generer_vente_reglee_facture_2026-11-16.py
C9 les avis               phase2/checks/c9_generer_avis_classeur_2026-11-16.py
C5 la pose (avec garde)   phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
les refus juges           phase2/checks/c_refus_11_11_contre_le_classeur_2026-11-18.py
ce qui manque             phase2/checks/classeur_ce_qui_manque_encore_2026-11-17.py
```

### Les tables

```
app_classeur_ligne_id      les lignes du Sheet et leur id_unique     4 794
app_classeur_lien          le gel : ligne <-> affaire               12 787
app_classeur_avis          C9                                        2 588
app_classeur_ligne_exclue  les lignes declarees hors jeu                 1
app_classeur_alias_negociateur
app_affaire_ledger         le registre des transactions             31 356
app_affaire_note           les notes (porte la colonne `origine`)
app_affaire_repartition    les repartitions
vue app_v_classeur_ligne_sans_lien    les lignes orphelines            91
vue app_v_classeur_lien_casse         les liens dont la cible a bouge   9
```

### Écrire en production

⭐⭐ **Quand le connecteur Supabase tombe, le chemin de secours est :**

```
node Console/apply_sql_patch.js <fichier.sql>
```

Il passe par le pooler `aws-1-eu-west-2.pooler.supabase.com` ; l'hôte direct est
injoignable. ⛔ **Et un patch porte son propre `commit;`** : joué « à blanc », il se
commite quand même. Lire le fichier avant de le jouer.

**Tout patch vient avec son `_INVERSE.sql` et son `_REPETITION.sql`**, et une
**sauvegarde datée** avant tout geste destructif.

---

## 11. ⛔ LES PIÈGES DÉJÀ PAYÉS — la section à ne pas survoler

1. ⛔⛔⛔ **L'accord circulaire** (§ 3). 874 faux accords sur 897.
2. ⛔⛔ **UN BIEN N'EST PAS UNE LIGNE DU CLASSEUR.** Le mandat 16992 en porte DEUX.
   **195 chaînes sur 4 751 portent plusieurs lignes**, jusqu'à 3. Ne jamais supposer
   l'unicité.
3. ⛔⛔ **UN COMPTE D'IDENTIFIANTS N'EST PAS UN COMPTE DE LIGNES.** Le 18/11 : 41 clés
   pour 43 lignes, et une décision perdue en silence — parce qu'un identifiant portait
   deux lignes (une commission ET une date).
4. ⛔⛔ **PostgREST plafonne à 1 000 lignes sans le dire**, et un curseur sur
   `created_at` **saute les ex-aequo** au bord de page. Paginer par décalage sur un
   ordre stable `(created_at, id)` — et **mettre un témoin chiffré dans le script**
   (« si j'en lis moins de N, je sors en erreur »). C'est ce témoin qui a attrapé deux
   lectures incomplètes le 18/11, pas la relecture humaine.
5. ⛔⛔ **Réparer un geste de masse laisse une CICATRICE.** Chez Hektor, `date` d'une
   offre = son **dernier mouvement**. Les 661 refus du 11/11 et les 19 ré-acceptations
   du 12/11 y ont écrit la date de NOTRE geste — et le lot du 16/11, croyant l'offre
   manquante, a posé **5 doublons**. Avant tout geste de masse : **le chaînage d'abord.**
6. ⛔⛔ **Hektor écrit « Compromis clôturé », jamais « annulé »** — et **le même mot** pour
   un compromis vraiment tombé (vérifié sur 61521). L'écran ne tranche pas. Le repère
   qui tranche : **98,9 % des 9 267 compromis actifs ont une vente**, donc un compromis
   qui aboutit RESTE actif. ⭐ **C'est sur notre traduction de ce mot que 661 offres ont
   été refusées le 11/11.**
7. ⛔⛔ **MODIFIER une offre acceptée : Hektor refuse EN SILENCE.** Et toucher une
   transaction d'un bien vendu a remis **15 biens vendus « Sous offre »** le 12/11.
8. ⛔⛔ **Une table de gel sans clé primaire : la descente SAUTE des lignes.**
9. ⛔⛔ **SQLite n'exige pas la clé `INTEGER PRIMARY KEY`** : il invente un numéro.
10. ⚠⚠ **Une mesure LOCALE avant la descente porte l'état de LA VEILLE.** Le 18/11,
    197 liens du classeur manquaient à 06:46 : `phase2.sqlite` n'est à jour qu'après
    ~07:31. Mesurer chez Supabase, ou attendre.
11. ⚠⚠ **`montant` du registre est en EUROS**, pas en centimes.
12. ⚠ **La date « vide » de Hektor est `0000-00-00`** : un `timestamptz` la refuse.
13. ⛔ **Le mur de Hektor est un quota de VOLUME** (13 000 à 17 000 requêtes par
    période), pas un débit. La règle : rester 40 % en dessous. La nuit en consomme
    déjà ~4 500. **Et un script `test_*` de `Console/` peut écrire chez Hektor.**
14. ⛔ **Une lecture ratée n'est JAMAIS un vert.** **Un zéro ne se croit pas sans témoin
    positif** : un « 0 écarté » a la même tête quand la garde ne marche pas.
15. ⭐⭐⭐ **Une réserve d'audit non traitée devient le bug.** Le défaut des documents
    était écrit le 25/09 ; la première vague est du 26/09, **le lendemain**.
16. ⭐⭐ **Un « faux » se qualifie AVANT d'être corrigé.** Sur 11 liens « faux » du gel,
    **neuf n'en étaient pas** : corriger en masse aurait abîmé neuf liens justes.
17. ⛔ **Un faux rouge est aussi grave qu'un faux vert.** Un témoin ne vérifie pas un
    **cas** (qui se corrige) mais une **capacité** : la méthode mesure-t-elle encore
    les deux côtés ?
18. ⚠ **Pour parler à Frédéric d'un bien, l'adresse d'administration est**
    `https://www.gti-immobilier.fr/admin/?page=/mes-biens/mon-bien&id=<n>` — jamais
    l'URL de l'API.

---

## 12. LA MÉTHODE, À CHAQUE PAS

Elle est en section 0 de `CLAUDE.md`, posée par Frédéric le 20/09 :

**AUDITER** (le code et la base d'abord, les notes ensuite — en cas de désaccord, le code
gagne) → **EXPLIQUER** clairement : ce que j'ai trouvé, ce que je vais faire, ce que ça
touche, comment on revient en arrière, comment on vérifiera — **et TOUJOURS « ce que ça
pourrait casser ailleurs »** → attendre le **« vas-y »** → **CODER** en additif →
**CONTRÔLER**, et dire aussi ce qui a raté → **METTRE À JOUR LE PLAN** → passer au
suivant.

**Une seule tâche en code à la fois.** Les audits peuvent tourner en parallèle.
**Rien n'est fini tant que ce n'est pas écrit dans les documents** : la conversation
sera résumée, les fichiers survivent.
