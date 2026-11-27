L3 · chantier classeur · ㉑ septies · 23/11, nuit : les 15 sont « Vendu » aujourd'hui, ta règle est dans le détecteur, le
bien 28653 a sa réponse. Rien réparé chez Hektor, rien écrit en base, rien poussé. Le patch : j'attends ton mot.

# Ton mot du 23/11 (2) : tes onze, les six, les 15 lus

Ton mot : `C:\Hektor\mot_du_23_11_les_onze_sures_et_les_six_a_examiner.md`.

## 1. Les 15 lectures, en lecture seule : 15 sur 15 « Vendu » aujourd'hui

Lu chez Hektor le 23/11 à 00:48 :
- **15 sur 15 en statut 5 « Vendu »**, aucun archivé ;
- la date de modification de chacun est restée celle de tes corrections du 13/11, entre 08:44 et 08:57 : rien n'a
  bougé depuis ;
- **le témoin positif a mordu** : le bien 55086, que notre sentinelle dit « Sous offre », a été lu en statut 3
  « Sous offre ». Le lecteur distingue donc bien les statuts, et le « 15 sur 15 » vaut quelque chose.

Une seule lecture par bien (`AnnonceById`), un seul client pour les 16, une lecture toutes les 1,2 s. Aucun upval, aucune
écriture. Script : `phase2/checks/lire_statut_des_15_biens_2026-11-23.py`. Sortie :
`C:\Hektor\chantier_classeur_q6_cache\garde_du_bien\statut_des_15_2026-11-23_004836.json`.

## 2. Ta règle est dans le détecteur, et il rend ton classement exactement

`phase2/checks/detecteur_offre_de_la_vente.py`, en lecture seule. Son juge est une fonction que le prochain lot appellera
telle quelle. Il ne répare rien : il classe.

**Le résultat**, sur tes 17 (CSV : `notice/LES_ONZE_SURES_ET_LES_SIX_A_EXAMINER_2026-11-23.csv`) :
- tes onze sortent « sûre », 11 sur 11 ;
- tes six sortent « à examiner », 6 sur 6 : 14420 et 18600 par « acceptée après la vente » ; 5126, 21600 et 17025 par
  ta règle ; 16421 par « seule candidate » ;
- 23139 sort hors de la famille : elle n'a jamais été acceptée ;
- ses 3 essais fabriqués sont verts : une autre offre acceptée au même montant déclenche ton arbitrage, et ta règle mord
  bien sur un montant faux.

**⚠ Deux faits mesurés qui ont fixé la forme du juge, et je te les dois.**
- **« L'autre offre au montant vendu » n'a jamais été acceptée.** Sur les 17 biens, ces offres sont 12, et toutes les
  12 ont été proposées puis refusées le jour même (leur journal dit seulement « proposition | refus »). Pour tes six,
  ta règle prouve donc un doute, pas que « c'est l'autre qui a mené à la vente ». Le juge ne rend jamais « réaccepter
  l'autre » : il rend « à examiner ». Un prochain lot ne doit jamais réaccepter l'autre sur cette seule règle.
- **6 de tes onze ont aussi une autre offre au montant exact** : 531, 14112 (deux), 17322, 22446, 24159 et 23995. Elles
  n'ont jamais été acceptées non plus. Ce qui rend tes onze sûres, c'est d'être la seule offre du bien jamais acceptée au
  montant de la vente. Le juge l'exige, et le nomme.

**Ta borne « 1 à 11 mois » est écrite à un an.** 14112 a été acceptée 340 jours avant la vente, soit 11 mois et 3
jours, et elle est dans tes onze. Avec une borne stricte à 11 mois, ton propre témoin aurait été rouge.

## 3. Le bien 28653 : c'est 14112

Des trois offres à 113 000, **14112 est la seule jamais acceptée** :
- acceptée le 25/03/2021 ;
- compromis 12 jours après (le 06/04/2021, puis un second le 17/05/2021) ;
- vente le 28/02/2022.

Les deux autres ont été proposées et refusées le jour même : 14114 le 05/11/2020, et 14113 le 19/01/2021. Je n'en
réaccepte aucune. C'est à toi de valider 14112 avant le geste.

## 4. 16421 : à mon sens, l'offre d'une affaire tombée

Tu la dis « la plus plausible ». La mesure dit autre chose :
- son propre compromis (16420, 40 000 €, le 06/03/2019, 22 jours après l'acceptation, dans le même dossier) est
  **annulé** ;
- la vente (35 000 €, le 19/06/2020) passe par un autre compromis (16419, le 13/02/2020), qui n'a aucune offre.

Pour cette offre, la cascade du 11/11 avait donc fait son travail. Elle reste dans tes six, à examiner.

## 5. ⚠ Fait neuf, dans la même famille : 8 des 19 réparées le 12/11 tombent sous ta règle

J'ai passé au même juge les 19 offres réacceptées le 12/11 avec le critère du nom. **11 sortent « sûre » et 8 « à
examiner »**, toutes pour la forme de 16421 : leur montant n'est pas celui de la vente, et aucune autre offre du bien ne
le porte. Ce sont 2087, 3427, 8018, 13984, 16363, 18957, 19951 et 21137.

Certaines sont sans doute des prix renégociés (3427 : 260 000 → 253 000 ; 18957 : 173 000 → 171 000). D'autres
s'écartent beaucoup (16363 : 53 200 → 35 000 ; 19951 : 94 000 → 80 000). Je ne propose rien chez Hektor. Je te le dis
parce que ta règle demande de ne pas écrire une fausse histoire, et que le 12/11 en a peut-être écrit.

## 6. 1001568 : dans la famille 2, et elle attendra plus longtemps

C'est écrit au carnet (§ 20.17). Elle rejoint 1001561 et 1001593 en attente. Mais son offre d'origine, 17025, est une
de tes six à examiner : 67 000 € acceptés, une vente à 67 500 €, et 17026 porte 67 500. Tant que 17025 n'est pas
tranchée, la copie reste la seule trace d'une acceptation sur le bien 36165, et elle ne se met pas de côté.

## 7. Ce qui ne change pas

- Rien n'est réparé chez Hektor : les onze réacceptations attendent ton mot, et le bien 28653 d'abord.
- Le jour venu, ce sera deux gestes par offre : réaccepter, puis remettre « Vendu » par `redescendreStatutHektor()`, avec
  le statut fourni explicitement.
- La colonne `date` n'est corrigée nulle part.
- Rien ne se pousse.

## Ce qui attend ta décision

1. **Le patch du journal** : dès ton mot, je lance `apres-collage` et je te donne tes trois points.
2. **Le bien 28653** : tu valides 14112 comme l'offre de la vente ?
3. **Les 8 réparées du 12/11 qui tombent sous ta règle** : tu veux leur preuve bien par bien, ou on les laisse telles
   quelles pour l'instant ?
