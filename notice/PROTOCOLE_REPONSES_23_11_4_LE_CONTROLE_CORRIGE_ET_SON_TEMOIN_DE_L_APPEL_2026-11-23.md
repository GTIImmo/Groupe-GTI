L3 · chantier classeur · ㉑ nonies · 23/11, matin : mon contrôle est corrigé sur tes deux points. Lancé en production,
en lecture seule, il sort en code 0 dans ses deux modes, et ses chiffres sont les tiens. Pas d'inverse, rien chez
Hektor, rien poussé.

# Ton mot du 23/11 (6) : le contrôle corrigé, et son témoin de l'appel

Ton mot : `C:\Hektor\mot_du_23_11_controle_du_matin_le_patch_a_passe_la_nuit.md`. Carnet : § 20.19.

## 1. Tes mesures, que je reprends sans les refaire

- **(a) ne crie pas.** Ce matin il y a toujours 11 551 dossiers, 11 551 numéros et 11 551 numéros distincts. Le journal
  a toujours 11 657 lignes. L'empreinte sans retours chariot est toujours e695bf7e. On ne joue pas l'inverse, et le
  sujet est clos.
- **(b) a son témoin positif** : `"actif": true` et ses compteurs dans le journal du run. La fonction patchée a donc
  tourné. Elle a rendu le même compte rendu à zéro le 22/11, avant le patch, et le 23/11, après.
- **Ton écart 30 / 31 du 21/11** est noté au carnet pour que personne ne le rouvre. « fusion: 30 » compte les dossiers
  gardés, et le journal compte les étiquettes absorbées, soit 31, parce qu'une fusion en a réuni trois.
- **Ta réserve** est notée, avec sa date. La production n'a encore écrit aucune ligne de fusion ou de scission depuis le
  patch. Le rendez-vous est donc la première vraie fusion ou scission : on regardera la ligne neuve et son ancien numéro.
  Le mode `matin` sait déjà le juger : chaque fusion et chaque scission neuve doit porter l'ancien numéro qui est la
  naissance de l'uuid coupé ou absorbé.

## 2. Ton point 1 : l'empreinte est jugée sans ses retours chariot

Dans `phase2/checks/controle_patch_journal_en_production.py` :
- **le juge compare `md5(replace(pg_get_functiondef(...), chr(13), ''))` à e695bf7e**, la fonction prouvée sur la copie
  par le rejeu du 22/11 (le fichier, en fins de ligne Unix) ;
- **l'empreinte brute est affichée avec son nombre de retours chariot**, à côté de b9fa8dea et 214, la valeur du collage ;
- **les deux attendus sont écrits en dur, et aucun n'est recopié de la production.** b9fa8dea vient du rejeu du 23/11,
  où chaque fichier collé passe en fins de ligne Windows (ligne 14 de `rejeu_sortie_23_11_tel_que_colle_CRLF.txt`) ;
- **la brute ne juge pas.** Le même corps recollé avec d'autres fins de ligne sort en vert, avec un ⚠ qui le nomme. Une
  brute égale à celle du collage, mais sur un autre corps, sort en rouge ;
- **le juge sert à deux endroits** : à `apres-collage` (son point 3), et, c'est neuf, au `matin` (son point « a bis »),
  pour vérifier chaque matin que la fonction est toujours celle du patch.

## 3. Ton point 2 : le témoin de l'appel

Le mode `matin` a un point « b bis ». Il prend chaque journal du run commencé après la photo, et il exige :
- **un seul bloc `"etiquettes"`** ;
- **`actif: true`** ;
- **les huit compteurs** : pose, propagation, fusion et scission, chacun en dossiers et en lignes. Je les ai pris dans le
  code qui les écrit (`affaire_ledger.poser_les_etiquettes_de_dossier`), et relus dans les journaux du 15 au 23/11.

Les rouges sont nommés, un par forme que la fonction sait écrire, plus les cas de lecture :
- `{"actif": false}` seul : l'interrupteur est éteint ;
- un `"echec"`, ou « la pose a échoué » dans le journal du run ;
- un compte rendu illisible ;
- un compteur qui manque ;
- aucun bloc, ou deux blocs dans le même journal ;
- aucun journal du run depuis la photo : sans lui, un zéro ne se croit pas.

**Les essais, hors ligne (mode `essais`) : 19 sur 19.**
- **Le juge de l'empreinte, 6 essais.** Trois sont des témoins inverses : la fonction d'avant, l'inverse collé
  (9581f8d2) et la brute du collage sur un autre corps sortent tous trois en rouge.
- **Le témoin de l'appel, 9 essais** sur des cas fabriqués, dont 7 témoins inverses, un par forme rouge.
- **Les vrais journaux du 20 au 23/11 : 4 sur 4 verts**, et leurs compteurs non nuls sont lus à l'unité. Le 20/11 porte
  propagation 4 et fusion 10 ; le 21/11 porte pose 2, propagation 3, et fusion 30 sur 56 lignes. C'est le témoin
  positif : le juge lit bien une nuit qui a bougé.

## 4. Lancé en production, en lecture seule

**`apres-collage` : code 0.**
- La répétition dit 9 sur 9.
- 190 lignes sur 190 portent leur ancien numéro.
- L'empreinte est verte : e695bf7e sans les retours chariot, et la brute b9fa8dea avec ses 214 retours chariot, celle
  du collage.

**`matin` : code 0.**
- a) 11 551 dossiers hier soir, 11 551 ce matin : 0 disparu, 0 renuméroté, 0 né.
- a bis) La fonction est toujours celle du patch.
- b) 0 ligne neuve au journal.
- b bis) Le journal `quotidien_2026-11-23_04-00-02.log` dit que le run est fini en code 0. Il porte `actif: true` et
  ses huit compteurs à zéro. Le zéro veut donc dire « rien à poser », pas « fonction pas appelée ».

**Mes chiffres sont les tiens.**

## 5. Une règle à te proposer : le recoupement entre le compte rendu et le journal

Pour bâtir le témoin, j'ai mesuré, en lecture seule, le journal de chaque nuit geste par geste, et je l'ai mis en face du
compte rendu. Sur les quatre nuits qui ont bougé (18, 19, 20 et 21/11), il n'y a aucun écart :
- **pose** : le compteur est égal au nombre de lignes « pose » du journal (3 = 3, 2 = 2, 2 = 2) ;
- **propagation** : le compteur est égal au nombre de lignes « propagation » (2 = 2, 1 = 1, 4 = 4, 3 = 3) ;
- **fusion** : le compteur est égal au nombre de dossiers gardés distincts (1 = 1, 10 = 10, 30 = 30). Le 21/11, les
  30 dossiers gardés font 31 lignes : c'est ta lecture du 30 / 31, généralisée ;
- **scission** : le compteur est égal au nombre de lignes « scission » (138 = 138 le 18/11, 1 = 1 le 19/11).

**Le contrôle affiche ce recoupement chaque matin, mais il ne le juge pas.** En faire un juge, c'est-à-dire un rouge
quand un geste compté ne trouve pas ses lignes au journal ou l'inverse, serait une règle nouvelle. Je ne l'ai pas codée.

## Ce qui attend ta décision

1. **Le recoupement** : je le fais juger, ou il reste seulement affiché ?
2. Tout le reste attend ton accord explicite, sans changement : les onze offres sûres, la mise de côté de la famille 1,
   et le push des commits locaux.
