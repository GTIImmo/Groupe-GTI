# L3 · chantier classeur · ㉑ quater · 22/11 soir — le patch prouvé sur copie, la coupe écrite, dix cicatrices, le filet du lot

**Ton mot :** `C:\Hektor\mot_du_22_11_reponses_21quater.md`.

**Rien n'est écrit en base, dans ton Sheet ni chez Hektor. Rien n'est poussé.** Le Postgres a tourné sur la machine,
joignable seulement depuis elle, sans service, et il est arrêté (0 processus).

---

## 1. Le Postgres portable : la 17.6 FINALE, vérifiée avant le rejeu

**Le téléchargement.** `@embedded-postgres/windows-x64@17.6.0-beta.15`, venu du registre npm :
- l'archive pèse 37,7 Mo (101 Mo une fois déballée), dans `C:\Hektor\outils\postgres17` ;
- son empreinte sha512 est **celle que publie le registre** (`sha512-zzoF/J8N…`), et son sha1 aussi (`b744988e…`).

**Le moteur est bien la 17.6 finale, la même version que la production :**
- `postgres --version` répond « PostgreSQL 17.6 », comme `initdb` et `pg_ctl` ;
- la fiche du fichier dit 17.6, « PostgreSQL Global Development Group » ;
- au démarrage, le serveur écrit « starting PostgreSQL 17.6 on x86_64-windows ».

Le mot « beta » est dans le numéro **du paquet npm** (son emballage en est à sa 15e version), pas dans celui du moteur.
PostgreSQL ne publie jamais de préversion d'une version mineure : ses préversions s'appellent `17beta1` ou `17rc1`, et
n'existent qu'avant la 17.0. Les binaires viennent de « embedded-postgres-binaries » de zonky (lu dans le README du paquet).

⚠ **Ce qui diffère de la production, je ne le cache pas :**
- le système : Windows x86_64 ici, Linux aarch64 chez Supabase ;
- l'ordre des textes : collation « C » ici, en_US.UTF-8 chez Supabase ;
- la signature : les binaires ne sont pas signés, leur intégrité ne repose que sur l'empreinte du registre.

Pourquoi cela ne fausse pas la preuve :
- la comparaison se fait **avant et après, sur le même moteur** ;
- l'état S0 rejoue la nuit sur la copie de la production : **0 écart sur 31 368 pièces** contre le registre réel. Le
  moteur local reproduit donc exactement ce que fait la production ;
- en S1, les numéros neufs sont égaux à la prédiction : 275 sur 275.

## 2. LE CHIFFRE, brut, avec le témoin inverse

**La copie** a été prise à 20:12, en lecture seule. Elle est relue **identique à Supabase** :
- 31 368 pièces, 27 511 mandats, 5 dates convenues, le compteur, les 11 657 lignes du journal ;
- les 5 fonctions, empreinte par empreinte (la pose : 815e956f…).

**Le patch, joué tel que tu le colleras :**
- la fonction passe à l'empreinte e695bf7e… ;
- **190 lignes** du journal reçoivent leur ancien numéro ;
- **la répétition : 9 contrôles sur 9 disent oui** ;
- **l'inverse**, joué sur une copie du patch, ramène la fonction à **815e956f** et retire la colonne : retour exact.

**Les cinq états,** chacun joué avec la fonction d'aujourd'hui et la fonction modifiée, à partir du même départ :
- **S0, aujourd'hui** : 0 pièce ne bouge, 0 écart, et **0 écart sur 31 368 contre le registre réel**.
- **S1, l'arrivée du protocole** : 728 pièces bougent.
  - 0 écart de pièce, 0 au compteur, 0 ligne du journal différente (493 lignes neuves de chaque côté).
  - La valeur rendue est identique.
  - L'ancien numéro est juste sur les 493 lignes (0 faux).
  - **275 numéros neufs sur 275 sont égaux à la prédiction.**
- **S2, des dossiers défaits** (ils exercent la pose et la propagation) : 3 302 pièces bougent. 0 écart de pièce, au
  compteur et au journal (1 933 lignes) ; ancien numéro 0 faux.
- **S3, l'arrivée à blanc** : rien ne bouge, des deux côtés. 0 écart.
- **S4, S2 avec la limite de 25** : 1 501 pièces bougent. 0 écart de pièce, au compteur et au journal (1 260 lignes) ;
  ancien numéro 0 faux.

⭐ **Le témoin inverse est attrapé.** Je fausse exprès le patch (le rang d'une scission + 1) : la comparaison crie,
**571 écarts de pièce et 10 au compteur**. Le zéro n'est donc pas aveugle.

⚠ **Je te dois deux aveux sur l'outil :**
- **Il s'est d'abord bloqué au démarrage.** Sous Windows, le serveur lancé par `pg_ctl` garde les tuyaux de sortie
  ouverts, et l'outil attendait leur fermeture. C'est corrigé : la sortie du serveur va à son propre journal.
- **Le premier rejeu complet a donné ROUGE sur le journal** : 42 lignes sur 493 en S1, 718 sur 1 933 en S2, 50 sur 1 260
  en S4. Ce n'était **pas le patch**.
  - La pose écrit ses lignes du journal dans l'ordre de l'uuid du dossier, et cet uuid est **tiré au hasard**. Deux
    passages de la même fonction écrivent donc les mêmes lignes dans un autre ordre. Mon outil, lui, comparait ligne à
    ligne, par position.
  - Je n'ai pas touché au patch. J'ai changé la comparaison, qui se fait maintenant en ensemble, après avoir nommé chaque
    uuid neuf par sa plus petite pièce.
  - Et j'ai ajouté **le témoin du hasard** : la fonction d'aujourd'hui, rejouée contre elle-même. Résultat : 0 écart de
    pièce, 0 ligne en ensemble, **29 lignes déplacées par position**. L'ordre du journal est du hasard ; son contenu est
    stable.
  - La première sortie est gardée : `rejeu_1re_version_comparaison_par_position.json`.

➡ **Le patch pose exactement les mêmes numéros et les mêmes étiquettes que la fonction d'aujourd'hui**, sur cinq états,
et le témoin inverse prouve que la comparaison voit un écart quand il y en a un. Tu peux le coller, dans l'ordre :
1. `supabase/patch_journal_ancien_numero_2026-11-22.sql`. Il vérifie lui-même l'empreinte 815e956f, et s'arrête si
   quelqu'un est passé avant.
2. Puis sa répétition, `..._REPETITION.sql` : ses 9 contrôles doivent dire oui.
3. En cas de problème : `..._INVERSE.sql`.

⚠ Le compte de 190 lignes est celui de 20:12. La nuit n'est pas passée, donc il doit être le même quand tu colleras.

Outil : `phase2/checks/rejeu_patch_journal_sur_copie.py`. Sortie : `rejeu.json` dans la copie.

## 3. La coupe des 4 lignes : écrite, par une règle, et rejouée sur tout

**La règle « C5 aux portes »**, entrée dans `protocole_portes.py` : une ligne juste aujourd'hui (porte RIEN ou
MISE_DE_COTE), mais que le chaînage **sans les 190 copies** ne tient plus juste, ne doit sa séparation qu'à une copie.
Elle devient COUPE_NEUVE, et son morceau s'écrit au brouillon des coupes.

**Rejouée sur les 4 573 lignes tranchées :**
- elle trouve **exactement les 4 lignes, et aucune autre** : 535 et 3540 (bien 5262), 2388 et 4113 (bien 24733) ;
- les portes passent de RIEN 4 010 à 4 006, et de COUPE_NEUVE 122 à 126. Rien d'autre ne bouge ;
- **0 verdict ne change.** La porte n'est pas un verdict : les 4 573 TRANCHÉES et les 225 EN ATTENTE sont les mêmes ;
- le brouillon passe de 559 à 563 morceaux. Les 4 nouveaux sont **mot pour mot** ceux de la variante mesurée hier soir :
  - `1875 1876 1878` (A07EC3DH) ;
  - `1874 1877` (FLPUUSY3) ;
  - `11956 11958 11960` (3S4ZWOFK) ;
  - `11957 11959` (9UO5NUN6).
- **l'arrivée ne change pas** :
  - 0 pièce sur 31 368 change de dossier entre l'ancien rejeu E et le nouveau ;
  - 0 numéro et 0 étiquette d'arrivée changent ;
  - les 4 573 lignes restent justes à l'arrivée, l'étiquette est exacte sur les 4 573, et 0 pièce bouge hors des biens.

⚠ Un défaut d'affichage, corrigé en passant : G2 se juge sur un chaînage qui contient encore les copies. Il comptait
donc ces 4 lignes comme « mises justes par G2 ». Elles sont retirées de son compte.

Le brouillon est dans le cache, pas dans `phase2/sync` : rien ne joue la nuit. Les sorties d'avant sont gardées
(`*_AVANT_C5_AUX_PORTES.*`).

➡ **Ta ligne 535 a maintenant une porte nommée : COUPE_NEUVE**, et la 2388 aussi. L'outil de la demande B les relit
ainsi. Il crie encore (code 1), et c'est voulu : la nuit d'aujourd'hui tient toujours ces séparations par la copie, et il
le dira tant que la coupe ne sera pas écrite pour de bon, à la fin du protocole.

## 4. La cause racine : ta chaîne est juste. Mais je te contredis sur le compte : il y en a DIX, pas sept

**Ta chaîne est juste, à la minute**, et je l'ai mesurée dans le journal des travaux :
- l'offre **1876** a été refusée par la cascade le 11/11 à 19:01, puis réacceptée le 12/11 à 15:26:38 ;
- l'offre **11958** a été refusée le 11/11 à 19:01, puis réacceptée le 12/11 à 15:27:32 ;
- leurs colonnes `date` portent depuis le 12/11, et leur vraie date (le journal de l'offre) est le 12/01/2024 et le
  12/06/2020 ;
- les copies 1001563 et 1001580 portent exactement ces vraies dates.

⭐ **Et j'ai trouvé le lecteur qui lisait la date brute : c'est le lot lui-même.** Sa garde ⑤ (« une offre existe-t-elle
déjà à la même date ? ») comparait la date du classeur à la colonne `date` **brute**. Elle ne pouvait donc pas retrouver
une offre dont nos gestes avaient déplacé la date. C'est ta règle : celui-là se répare (§ 6).

⛔ **« Exactement 2, il n'y en a pas une troisième » : la mesure dit 5.** Une cicatrice, c'est une copie qui a sur son
bien une vraie pièce du même genre, à la même vraie date, dont la colonne `date` a été déplacée par un de nos gestes.
J'en compte cinq encore en base.

Trois sont **seules dans leur propre chaîne** (ta forme) :
- 1001563 (A07EC3DH, bien 5262) : sa jumelle est l'offre 1876 ;
- 1001580 (3S4ZWOFK, bien 24733) : sa jumelle est l'offre 11958 ;
- ⭐ **1001482 (UTLG66LE, bien 10527), la troisième.** Sa jumelle est l'offre 5055, du 18/12/2019. Elle a été refusée par
  le lot « table » le 11/11 à 18:21 et est restée refusée ; sa date brute porte le 11/11/2026.

Deux sont **sur une autre chaîne que leur jumelle** :
- 1001561 (TRJ5Y59U, bien 47557) : sa jumelle est l'offre 23995, du 25/03/2024, refusée par la cascade le 11/11 à 19:01 ;
- 1001593 (1cc703d9, bien 28422) : sa jumelle est l'offre 14008, du 28/06/2025, refusée par la cascade le 11/11 à 19:01.

**Pourquoi ton compte s'arrête à 2.** Il tient si l'on ne regarde que les 19 RÉACCEPTATIONS du 12/11. Mais **les refus
aussi ont déplacé la date** : 642 offres portent le 11/11. Avec tous nos gestes :
- 13 copies sont sur un bien dont une offre a été touchée ;
- 5 de ces 13 sont la même transaction posée deux fois.

⚠ **1001561, c'est « la 6e, une autre cause » du 18/11.** C'est la même cause. Sa jumelle vit sur une autre chaîne, et
c'est ce qui a trompé la lecture du 18/11.

⚠ **Un fait que je ne tranche pas.** Pour 1001561 et 1001593, ton classeur dit « Vente réglée » d'une offre que **notre
cascade a refusée le 11/11** et que personne n'a réacceptée. Les deux biens portent bien une vente (23997 et 14009).
Chez Hektor, c'est ta décision : je n'ai rien touché, et je n'ai pas cherché s'il y en a d'autres.

**Le total des cicatrices est donc DIX :**
- les 5 retirées le 18/11, qui étaient sur la chaîne de leur jumelle ;
- les 5 encore en base : 3 seules dans leur chaîne, 2 sur une autre chaîne.

**Et une famille voisine, à ne pas confondre :** **20 autres copies ont une jumelle sans cicatrice** (leur date brute est
la vraie). Je les ai rapprochées de **l'audit indépendant du 18/11, § 4.3** :
- « au jour près », je retrouve ses 25 copies exactement (10 offres, 15 compromis) ;
- à la date exacte, j'en compte 24 : les 5 cicatrices et 19 autres.

C'est une autre cause : la jumelle est tenue par une ligne sœur. Leur retrait y est marqué « à décider » depuis le 18/11.

## 5. Le détecteur : il attrape les deux formes, et il CRIE

**L'outil** : `phase2/checks/classeur_detecteur_cicatrices.py`. Il est en lecture seule, et la vraie date est calculée
**par la base** (`app_dossier_jour_date_transaction`) : aucune règle n'est recopiée.

**Ce qu'il regarde :**
- **nos gestes**, avec la même définition que l'inventaire du 19/11 : les travaux sans auteur, plus la cascade ;
- **la jumelle**, c'est-à-dire le même bien, le même genre et la même vraie date ;
- **la forme du 18/11** : une copie sur une chaîne qui porte déjà une vraie pièce du même genre ;
- **ta forme**, mot pour mot : une copie seule dans sa chaîne, sur un bien dont nos gestes ont touché une offre.

**Sur les 190 copies en base :**
- ta forme crie sur **11 copies**, dont les 3 cicatrices. Les 8 autres n'ont pas de jumelle :
  - 5 copies de COMPROMIS (1001524 à 1001527, 1001534), sur un bien où c'est une OFFRE qui a été touchée ;
  - 3 offres à une autre date que l'offre touchée (1001455, 1001498, 1001568) ;
- la forme du 18/11 crie sur 1 copie : 1001561 ;
- la signature de la cicatrice en trouve 5.

**Le témoin positif :** les 5 copies retirées le 18/11, relues dans leur sauvegarde datée, sortent **toutes les 5** par la
forme du 18/11, et 3 sur 5 par la signature. Les 2 autres ont au classeur une date différente de celle de Hektor
(1290IIOC le 20/12/2020, bdb548a3 le 06/02/2026).

**Dans le lot** (`poser_offres_annulees_classeur_2026-11-16.py`), c'est la nouvelle étape ⑦, juste avant de générer le
patch. Une ligne à poser ne se voit pas encore dans une chaîne : celle-ci n'existe qu'après la nuit. L'étape regarde donc
**le bien entier**. Quand une ligne a une jumelle, ou tombe sur un bien dont nos gestes ont touché une offre :
- elle est **nommée**, avec la pièce en cause ;
- **le lot s'arrête et ne génère rien** (code 3) ;
- c'est toi qui décides : tu déclares la ligne hors jeu (`app_classeur_ligne_exclue`, avec son pourquoi), ou tu
  relances avec `--entendu=ID` après l'avoir regardée.

Le filet **ne corrige rien tout seul**.

**Rejoué comme il aurait tourné le 16/11 :** il aurait crié sur **36 des 195 copies**, dont **les 10 cicatrices** (les 5
du 18/11 : 5 sur 5).

**Essayé ce soir dans le vrai script**, sa sortie détournée vers mon dossier de travail :
- il crie sur 2 lignes (1290IIOC et bdb548a3) et rend le code 3 ;
- il n'écrit aucun fichier ;
- les 3 patchs du 16/11 sont intacts, empreinte comprise.

⚠ **Ton motif est large**, je te le dis franchement : 8 des 11 copies qu'il nomme n'ont pas de jumelle. Dans le lot, cela
ne coûte qu'un regard, puisqu'il ne crie que quand on fabrique un lot. Le passage sur la base est une mesure, pas une
alarme de chaque matin.

## 6. Le lecteur réparé : la garde ⑤ du lot lit la VRAIE date

Ta règle : « on corrige les lecteurs, jamais la donnée ». La garde ⑤ du lot lit maintenant la vraie date, calculée par la
base. **La colonne `date` n'est corrigée nulle part, ni en base ni chez Hektor.**

**L'effet, rejoué ce soir :** des 5 copies du 18/11, **la garde réparée en arrête 3** (H6CTRVR6, 0GV2LNV2, c08ff7cb).
Avec la date brute, elle les avait laissées passer le 16/11. Le filet ⑦ arrête les 2 autres. Aucune des 5 ne serait
reposée.

⚠ Le lot a maintenant besoin de psycopg2, donc du python du système. Sans lui, il rend 2 et ne génère rien : une lecture
ratée n'est jamais un vert.

## 7. La note des cicatrices : corrigée

La mémoire `reparer-un-geste-de-masse-laisse-une-cicatrice` dit maintenant **dix** :
- forme A, sur la chaîne de sa jumelle : 5, retirées le 18/11 ;
- forme B, seule dans sa chaîne : 3, à traiter ;
- forme C, sur une autre chaîne : 2, à traiter.

Elle nomme chaque copie et sa jumelle, distingue la famille des 20 jumelles sans cicatrice, et décrit le filet.

## 8. Ce qui n'est pas fait, et ce qui n'est pas mesuré

- **Les 5 cicatrices sont encore en base.** Les retirer est une écriture en production, des deux côtés, comme le 18/11.
  Rien n'est fabriqué.
  - ⚠ Pour 1001482, 1001561 et 1001593, il faut d'abord mesurer ce que leur retrait fait aux dossiers. Hier soir, le
    chaînage sans les copies déplaçait 14008, la jumelle de 1001593.
  - Pour 1001563 et 1001580, la coupe tient désormais sans elles.
- **Les 20 jumelles sans cicatrice** : non traitées. C'est ta décision, ouverte depuis l'audit du 18/11.
- **Les offres que notre cascade a refusées et que ton classeur dit « Vente réglée »** : 2 nommées (23995, 14008). Je n'ai
  pas mesuré s'il y en a d'autres parmi les 642. Chez Hektor, c'est ta décision.
- **Demain matin : la mesure de la nuit D'ABORD.** Puis l'image, le passage, les avis, les lignes en attente, et la
  comparaison 20 contre le nouveau passage.
- **Le reste à vider : 225 lignes.** Ton verrou tient.

## Ce qui attend ta décision

1. **Le patch du journal : le chiffre est là.** Tu le colles toi-même, dans l'ordre du § 2. Je n'ai rien à trancher.
2. **Les 5 cicatrices encore en base :** je fabrique, sans le jouer, le patch qui les met de côté (comme le 18/11 : garde,
   sauvegarde datée, inverse, répétition), en mesurant d'abord ce que chaque retrait fait aux dossiers ? Ou tu veux
   d'abord regarder 1001561 et 1001593, à cause de leur offre refusée par nous ?
