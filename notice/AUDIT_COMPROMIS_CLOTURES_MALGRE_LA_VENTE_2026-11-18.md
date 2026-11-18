# Les compromis « clôturés » alors que la vente s'est faite — audit du 18/11/2026

> **Demandé par Frédéric le 18/11**, après le cas 43091 : *« audit d'abord »*.
> **Lecture seule de bout en bout.** Rien n'a été écrit, ni chez nous ni chez Hektor.

## 1. D'où vient la question

Sur l'annonce **43091** (terrain à Yssingeaux, mandat 16992), le compromis **17016**
porte `status 2` chez Hektor — que nous traduisons `cancelled` — alors que **la vente
23266 a bien eu lieu** le 30/07/2026, au même prix, avec le même acquéreur.

C'est cette marque qui a fait refuser l'offre 32791 par le rattrapage du 11/11.

## 2. ⛔ L'ÉCRAN DE HEKTOR NE TRANCHE PAS — mesuré le 18/11 dans Chrome

Hektor n'écrit nulle part « annulé ». Il écrit **« Compromis clôturé »**.

Et il écrit **exactement le même mot** sur un compromis vraiment tombé : vérifié sur le
bien **61521**, dont la chaîne ne porte **aucune vente**. Le libellé ne distingue donc
rien, et on ne peut pas juger un cas à l'œil.

⭐ **Ce qui tranche est le repère statistique** : sur **9 267** compromis `active`,
**98,9 %** ont une vente dans leur chaîne. Autrement dit, **chez Hektor un compromis qui
aboutit RESTE actif** — la vente ne le clôt pas. Un compromis clôturé sur une chaîne
vendue est donc bien une anomalie.

## 3. ⭐⭐ LE PÉRIMÈTRE RÉEL : 8, PAS 384

```
compromis 'cancelled' dont la chaine porte une vente            384
  dont un AUTRE compromis de la chaine est ACTIF et a abouti    376   <- NORMAL
    (le 1er est tombe, le 2e a pris le relais -- ex. 8454, 10165, 24119)
  SEUL compromis de leur chaine                                   8   <- l'anomalie
    et les 8 ont LE MEME ACQUEREUR que la vente                   8
    acquereur different                                           0
```

**376 des 384 sont parfaitement normaux.** Le vrai sujet tient en **8 compromis, sur
7 biens**.

## 4. Les 8, nommés

```
bien    compromis  acquereur   compromis     vente        ligne(s) du Sheet
43091   17016      CHAPUIS     09/03/2026    30/07/2026   bdb548a3
48093   15197      PROST       04/12/2020    25/05/2023   RF9KYWSY
36794   17456      CREVON      30/09/2022    24/03/2023   5GZVT548, J1C9PJJP
36794   17454      CREVON      12/12/2022    24/03/2023   5GZVT548, J1C9PJJP
46585   15827      BRUNON      0000-00-00    25/02/2022   FVLMAQ63, W79RISV0
48311   15227      DENAUX      24/10/2019    18/06/2021   0OO1BEZD, XH5KZ9LI
34048   14420      GERBAUD     03/03/2020    25/02/2021   1290IIOC, FS22QU5G
52790   15281      SANCHEZ     12/12/2017    17/05/2018   (aucune)
```

## 5. ✅ CE N'EST PAS NOUS, ET C'EST MESURÉ

**Aucun des 8 n'a été touché par un geste de l'app.** Le projet compte 27
`cancel_hektor_compromis` et 19 `delete_hektor_compromis` depuis le 29/08 : **aucun** ne
vise ces compromis.

⭐ Et les dates s'étalent de **2017 à 2026** : ce n'est pas un incident, c'est un fond
ancien. L'explication la plus simple — **non tranchée** — est une habitude de saisie :
quelqu'un clôt le compromis à la main après la vente, alors que l'usage courant (98,9 %)
est de le laisser actif.

## 6. ⭐⭐ CE QUE ÇA A RÉELLEMENT CASSÉ : UNE SEULE OFFRE RESTE À RÉPARER

Croisement des 7 biens avec le rattrapage du 11/11 :

```
34048   offre 5248   refusee le 11/11   -> ✅ REPAREE le 12/11 (accepted)
43091   offre 32791  refusee le 11/11   -> ✅ REPAREE le 12/11 (accepted)
36794   offre 4281   refusee le 11/11   -> ⛔ TOUJOURS REFUSEE
46585 . 48093 . 48311 . 52790           -> jamais touchees : sans consequence
```

⛔ **Il reste UNE offre à réparer : la 4281 du bien 36794.** Et elle était déjà dans les
6 refus que le classeur contredit (`C_REFUS_11_11_JUGES_PAR_LE_CLASSEUR_2026-11-18.csv`,
facture GGTI00003061, vente réglée au 28/03/2023).

## 7. Ce que je recommande, et ce que je ne recommande pas

⛔ **NE PAS « dé-annuler » les 8 compromis chez Hektor.** Le libellé ne prouve pas
l'erreur, aucun geste du worker ne sait le faire, et toucher une transaction d'un bien
vendu est exactement le schéma qui a remis **15 biens vendus « Sous offre »** le 12/11.

✅ **Réparer l'offre 4281 du bien 36794**, par le chemin déjà éprouvé le 12/11
(`Console/enqueue_reaccepter_offres_refusees_a_tort.js`, 19/19 `done`, témoin inverse).
C'est le seul dégât vivant.

⬜ **À décider par Frédéric** : faut-il corriger la marque des 8 compromis chez Hektor,
à la main, pour que l'historique soit juste ? Ce n'est pas urgent — ils dorment depuis
des années — mais ils continueront de faire croire à une affaire échouée.

⚠ **Et la vraie leçon est sur NOTRE MOT** : nous appelons `cancelled` ce que Hektor
appelle « clôturé ». C'est sur ce mot que 661 offres ont été refusées le 11/11.
