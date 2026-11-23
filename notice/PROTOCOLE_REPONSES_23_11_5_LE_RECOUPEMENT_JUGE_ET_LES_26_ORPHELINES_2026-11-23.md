L3 · chantier classeur · ㉑ decies · 23/11 : le recoupement est jugé dans les deux sens, et ses deux témoins inverses
sortent rouges. Les 11 vraies nuits du 13 au 23/11 sortent vertes. Ma mesure des 26 confirme le mot sur l'essentiel et le
contredit sur trois points. Rien n'est écrit, ni en base ni chez Hektor, et rien n'est poussé.

# Le mot (8), que tu as repris à ton compte : le recoupement jugé, et ma mesure des 26

Le mot : `C:\Hektor\mot_du_23_11_ta_question_l_alerte_rouge_et_le_motif_qui_revient.md`. Carnet : § 20.20.

Ta réserve reste ouverte, comme tu l'as écrit : la fonction de nuit n'a pas encore écrit elle-même un ancien numéro en
production. Le mode `matin` jugera la première ligne de fusion ou de scission quand elle viendra.

## 1. Le recoupement, jugé

Dans `phase2/checks/controle_patch_journal_en_production.py`, le mode `matin` a un point neuf, « b ter ». Il juge ta règle
asymétrique, nuit par nuit :
- **pose, propagation et scission** : chaque compteur doit être égal à ses lignes au journal ;
- **fusion** : le compteur doit être égal au nombre de dossiers gardés distincts, et le nombre de lignes doit être au
  moins égal au compteur ;
- **les compteurs « _lignes »** sont des transactions : ils sont affichés, et jamais recoupés.

Il y a deux sens :
- **sens 1**, un geste compté sans ses lignes au journal : un rouge, « trace perdue » ;
- **sens 2**, des lignes qu'aucun geste ne réclame : un rouge franc, « écrivain inconnu ». Ce sens couvre aussi une ligne
  écrite hors de la fenêtre d'un run, et un événement inconnu.

La fenêtre d'un run va de l'heure de son journal à sa ligne de fin. Si le run n'est pas fini, elle va jusqu'à maintenant.
Les lignes « restauration » sont nommées, exclues, et le contrôle le dit. Une nuit dont le témoin de l'appel est rouge
n'est pas jugeable, et elle sort donc en rouge.

**Les essais hors ligne : 31 sur 31, dont 12 neufs.**
- **Tes deux témoins inverses sortent rouges.** Une fusion à 31 au lieu de 30 donne un rouge de sens 1, parce qu'il y a
  30 dossiers gardés. Une scission à 136 au lieu de 138 donne un rouge de sens 2, parce qu'il y a 138 lignes.
- **Six autres témoins inverses sortent rouges** : une pose de trop, une propagation de moins, une ligne écrite à 14:00 hors
  du run, une fusion de trop, un événement inconnu, et un run pas fini avec une pose qu'aucun geste ne réclame.
- **Les verts restent verts** : les deux nuits telles quelles, une restauration exclue, et un fusion_lignes à 999, qui
  n'est pas jugé.

**Les vraies nuits, en lecture seule (mode `nuits`) : 11 sur 11 en vert.**
- Ce sont les runs du 13/11, le premier qui écrit un compte rendu, au 23/11. Ils portent 216 lignes au journal.
- Aucune ligne n'a été écrite hors d'un run, et il n'y a aucune restauration.
- Les 11 441 lignes d'avant ne sont pas jugées : c'est la pose initiale du 12/11 à 23:08.
- Ta règle tient donc sur 7 nuits qui ont bougé (13, 14, 17, 18, 19, 20 et 21/11), et pas seulement sur 4.

Le mode `matin`, relancé, sort en code 0, avec « b ter » en vert.

## 2. Ma mesure des 26 (je connaissais son résultat, donné dans son message, mais pas sa mesure)

Le script est `phase2/checks/mesurer_les_26_orphelines_2026-11-23.py`, en lecture seule. Le résultat, ligne par ligne, est
dans `notice/LES_26_ORPHELINES_MA_MESURE_2026-11-23.csv`. Je trouve chaque dossier d'arrivée comme la purge de nuit le
trouve : le numéro du dossier disparu est celui de sa plus petite transaction.

- **26 parts sur 13 dossiers disparus**, et la vue en compte aussi 26. Toutes sont d'origine `classeur_reconstitue`, et
  toutes ont été écrites le 13/11 à 22:56.
- **12 dossiers sont des doublons de notre copie, soit 24 parts** : 3670, 11709, 14034, 14052, 14913, 19070, 19576,
  19737, 20089, 24011, 28179 et 28547. Des deux côtés, on trouve le même côté, le même rang, le même négociateur, le même
  nom et le même pourcentage, 50 %.
- **Un seul dossier diverge, 27135 → 27133.** L'entrée est la même des deux côtés (COUDERT 50). La sortie diffère :
  l'orpheline porte COUDERT 50, et la part en place porte HERITIER 50.
- **Aucune part ne peut être ramenée, et aucune n'est perdue.**
- **Chaque dossier d'arrivée porte au journal sa fusion du 21/11 à 06:20, avec l'ancien numéro absorbé.** Exemple : 3669
  est D2025-0410, et il a absorbé D2025-0316. La colonne du patch dit donc déjà d'où vient chaque orpheline.

**Ce qui confirme le mot :**
- D8 est posé : `app_repartition_purger_orphelines`, empreinte df20fc00, sans retour chariot.
- Son compte rendu de cette nuit dit 0 saisie ramenée, 26 orphelines gardées, aucune orpheline sans transaction, et 13
  conflits.
- Rien n'est perdu.
- La seule divergence est bien 27135 → 27133, côté sortie.

**Ce qui le contredit, mesuré :**
- **« 22 lignes, 21 doublons » :** je compte 26 parts sur 13 dossiers, soit 25 côtés identiques et 1 divergent, la sortie
  de 27135. Je ne sais pas d'où vient son 22.
- **« 27135 → 27133 est la fusion triple du 21/11 » : non.**
  - Le journal du 21/11 n'a qu'un seul dossier gardé à deux lignes : D2023-0562, celui des transactions 4267 à 4273. Il
    a absorbé D2025-0014 et D2023-0563 (lignes 34522 et 34523).
  - Le dossier de 27133, D2023-0316, n'a absorbé qu'une étiquette, D2023-0568 (ligne 34520).
  - L'écart de 2 est seulement la différence entre les deux plus petites transactions. Il ne compte pas les étiquettes
    absorbées. Le journal, lui, les compte, et il en trouve une.
- **« Deux négociateurs, celle-là demande un humain » : c'est déjà mesuré depuis le 22/11 (carnet § 18.3).**
  - Ce ne sont pas deux avis sur une même affaire, mais les parts de deux affaires du bien 53342.
  - L'orpheline de 27135 est celle de GENESTAS : COUDERT à 100 %, donc 50 + 50.
  - La part en place sur 27133 est celle de DE MATOS DE FARIA : HERITIER 50 et COUDERT 50.
  - La règle E a réuni 27135 à 27133. La V3 fait revenir le dossier 27135, et le conflit tombe de lui-même.

**Deux choses que le projet avait déjà établies.**
- **« L'anomalie, c'est que cette fois elle ne retombe pas » :** 26, c'est le nombre que tu attendais (carnet § 20.1,
  point 11 : « il attend 26 orphelines demain (la V3 ne joue pas) »). La purge s'arrête par construction quand le dossier
  d'arrivée porte déjà une part qui ne vient pas de Hektor (§ 18.3). L'alerte ne retombera qu'avec la V3, qui fait
  revenir 4 dossiers, et avec le patch des orphelines.
- **La règle que le mot propose est déjà la tienne : c'est la règle 6 du 22/11 (§ 19.5), que tu as validée.**
  - Les parts identiques se mettent de côté avec leur ancien numéro ; les parts différentes te remontent.
  - Le patch est déjà fabriqué et éprouvé à blanc sur ces mêmes 26 (`temps13_orphelines_mises_de_cote_2026-11-22.py`).
  - Son moment est déjà décidé : après le protocole (§ 20.2), refabriqué sur l'état de ce jour-là.
  - Une seule différence : le mot exige la même origine des deux côtés, alors que ta règle du 22/11 montre l'origine sans
    la comparer. Aujourd'hui cela ne change rien, puisque les 26 et leurs vis-à-vis sont tous `classeur_reconstitue`.

Je n'ai rien écrit : ni les 26, ni la mise de côté, ni l'inverse. Rien n'est fait chez Hektor, et rien n'est poussé.

## Ce qui attend ta décision

1. **La condition « même origine »** : veux-tu l'ajouter à ta règle 6 ? Aujourd'hui, elle ne change rien.
2. Le reste attend le protocole, comme tu l'as décidé : le patch des orphelines, les onze offres sûres, les cinq à
   examiner et les huit réacceptations douteuses.
