L3 · chantier classeur · ㉑ octies · 23/11, 01:05 : l'écart d'empreinte est expliqué et reproduit à l'octet : ce sont 214
retours chariot ajoutés par le collage. L'inverse n'est pas joué. Rien chez Hektor, rien poussé.

# Ton mot du 23/11 (3) : le patch est collé, et l'écart a sa cause

Ton mot : `C:\Hektor\mot_du_23_11_patch_colle_et_un_ecart_a_trancher.md`.

## 1. Tes deux chiffres, pris sur ma copie après le rejeu du patch

- **production** : md5(prosrc) 1431b364def1a5cdaf646f5231628dac, length(prosrc) 10 455 (ce que tu lis) ;
- **copie** : md5(prosrc) ea1d0db1e5a70c277fdf3baa2a61c0ca, length(prosrc) 10 241.

**Ils diffèrent. C'est donc ton hypothèse B à la lettre, mais l'écart est tout entier dans 214 retours chariot.** La
mesure (`phase2/checks/comparer_corps_fonction_copie_et_production.py`) :
- **même version** des deux côtés (17.6), comme tu l'as vu ;
- **l'en-tête est identique** : sécurité, volatilité, `search_path`, langage, coût, propriétaire, arguments, résultat.
  Ton hypothèse A ne tient donc pas non plus : l'écart n'est pas dans l'en-tête ;
- **le corps de production porte 214 retours chariot, un au bout de chaque ligne** : 10 455 = 10 241 + 214. Celui de la
  copie et celui du fichier du patch n'en portent aucun ;
- **sans ses retours chariot, le corps de production est identique** à celui de la copie et à celui du fichier ;
- **le diff, ligne à ligne, ne montre rien d'autre** qu'un `\r` en fin de chaque ligne
  (`C:\Hektor\chantier_classeur_q6_cache\rejeu_patch_journal\corps_2026-11-23_005842\diff_corps_copie_production.txt`).

**La preuve en production même**, en lecture seule : `md5(replace(pg_get_functiondef(...), chr(13), ''))` vaut
**e695bf7e**, l'empreinte de la copie, à l'octet près.

**Pourquoi c'est sans effet sur ce que la fonction fait.** Pour PL/pgSQL, un retour chariot est un blanc. Il ne
changerait une valeur que s'il tombait dans une chaîne de caractères écrite sur plusieurs lignes. Le corps a 16 chaînes
`'...'`, aucune sur plusieurs lignes, et aucune chaîne `$...$`. Les 214 retours chariot ne tombent que dans du blanc ou
à la fin d'un commentaire.

**D'où ils viennent : du collage.** Un `CREATE OR REPLACE FUNCTION` collé depuis Windows arrive avec des fins de ligne
Windows, et Postgres les garde telles quelles. C'est l'état normal de la base : 28 fonctions publiques en portent.

## 2. Le collage, reproduit sur la copie : la fonction qui tourne est prouvée

J'ai rejoué tout le rejeu d'hier, mais en passant chaque fichier collé en fins de ligne Windows, comme le fait le collage
(`phase2/checks/rejeu_patch_tel_que_colle_crlf.py`) :
- **la fonction posée sur la copie a l'empreinte b9fa8deae9d73caa7b059918488e7f94, celle de la production, à l'octet
  près.** L'écart n'est donc pas seulement expliqué : il est reproduit ;
- **et cette fonction-là passe tout le rejeu au vert** : de S0 à S4, 0 écart de pièce, de compteur ou de journal ;
  275 numéros neufs sur 275 prédits ; le témoin du hasard à 0 en ensemble ; le témoin inverse attrapé (571 écarts) ;
  la répétition à 9 sur 9.

Le rejeu d'hier prouvait la fonction du fichier. **Celui-ci prouve la fonction qui tourne en production.**

**Le seul rouge est l'inverse, et il est attendu.** Collé lui aussi en fins de ligne Windows, il remet la fonction d'avant
avec ses retours chariot : son empreinte brute est 9581f8d2, et 815e956f une fois les retours chariot retirés. Il retire
bien la colonne. **Il marche donc**, si le matin crie : ses gardes cherchent des bouts de texte d'une seule ligne, que les
retours chariot ne gênent pas.

## 3. Ton contrôle « apres-collage » : ses autres points sont verts

Lancé à 01:02 :
- **la répétition dit 9 sur 9** ;
- **la colonne : 190 lignes de fusion (47) et de scission (143) d'avant le patch, 190 portent leur ancien numéro, aucune
  n'est vide** ;
- **seule l'empreinte est rouge** : b9fa8dea au lieu de e695bf7e.

**On ne garde que cet écart, et il est expliqué.**

## 4. Le défaut est dans mon contrôle, et je le devais savoir

Mon contrôle comparait l'empreinte brute de `pg_get_functiondef`. Or la mémoire du projet le dit depuis le 08/10 : un
`CREATE OR REPLACE` collé garde les retours chariot, et un contrôle doit comparer
`md5(replace(pg_get_functiondef(...), chr(13), ''))`. Elle dit même mot pour mot de ne pas attendre « 0 retour chariot »
dans le contrôle d'un patch qui crée une fonction. C'est la cinquième fois. Et mon rejeu d'hier ne traversait pas le
collage, ce que demande la leçon 30. Le rejeu en fins de ligne Windows le fait maintenant.

**La correction que je propose, et que je n'ai pas faite** (ton « RIEN D'AUTRE ») :
- comparer `md5(replace(pg_get_functiondef(...), chr(13), ''))` à **e695bf7e**, l'empreinte prouvée sur la copie ;
- afficher aussi l'empreinte brute, avec son nombre de retours chariot ;
- ne pas mettre b9fa8dea à la place de e695bf7e. Si l'on voulait porter la valeur brute, ce serait comme « collé en
  fins de ligne Windows, reproduit sur la copie », jamais comme « lu en production ».

**Pour ce matin :** le mode `matin` ne juge pas l'empreinte, il l'affiche seulement. Il ne criera donc pas sur les
retours chariot : ton ordre (a), (b), (c) tient.

⚠ **Pour le prochain patch de cette fonction :** son empreinte d'avant, brute, est b9fa8dea. Sa garde devra retirer les
retours chariot, sinon elle refusera de s'exécuter.

## 5. Tes décisions, notées au carnet (§ 20.18)

- **14112 est l'offre de la vente du bien 28653** : tes onze tiennent.
- **16421 sort de la liste** : il reste onze offres à réparer et cinq à examiner.
- **La borne est d'un an.**
- **Les 8 douteuses des 19 du 12/11** : on ne touche à rien. Elles se trancheront après les onze, par le même
  détecteur, et jamais dans le même lot.

## Ce qui attend ta décision

1. **Le patch** : la différence est du blanc, et le rejeu prouve la fonction telle qu'elle a été collée. Je te
   recommande de le garder et de ne pas jouer l'inverse avant 05:00. Un inverse collé porterait d'ailleurs les mêmes
   retours chariot. Tu le gardes, ou tu veux l'inverse ?
2. **La correction de mon contrôle** (ci-dessus) : je la fais ?
