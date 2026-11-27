# Tes réponses au rapport ㉑ bis — les 63 en clair, le journal, R7b, la sauvegarde qui se relit

**L3 · chantier classeur · ㉑ bis · 22/11 soir : tes trois conditions sont mesurées, la sauvegarde se relit et redonne les 216 étiquettes, et rien n'est écrit.**

Ton mot : `C:\Hektor\mot_du_22_11_reponses_21bis.md`. Tout ce qui suit est en lecture seule. Rien n'a été écrit en base, dans ton Sheet ou chez Hektor, et rien n'est poussé.

Le code a changé sans toucher aucune règle (v3.1). Je l'ai donc rejoué : le passage 22 donne les mêmes verdicts que le 20 (0 change), avec les mêmes écarts de témoins. Les portes redonnent 4 573 lignes justes sur 4 573, avec la même étiquette.

## 1. Les 63 — la règle du plus ancien

### a) L'ancien numéro, tracé au journal

**Ce que j'ai mesuré.** Chaque changement laisse bien sa ligne : 11 454 poses, 13 propagations, 47 fusions et 143 scissions, soit tes 11 657 lignes. Mais **l'ancien numéro n'est pas écrit dans la ligne du changement** :

- **Une scission** écrit l'ancien identifiant du dossier, puis le **neuf** numéro. Sur 143 lignes, 141 portent le numéro neuf et aucune l'ancien.
- **Une fusion** écrit le dossier gardé et l'identifiant du dossier absorbé, **sans son numéro**.

L'ancien numéro se retrouve quand même, par la ligne de naissance de l'ancien dossier : 190 sur 190. Les 11 551 dossiers vivants portent tous le numéro de leur naissance (0 écart). Mais il faut deux lignes pour le lire, pas une.

⚠ C'est aussi un piège pour qui lit le journal : dans une scission, le numéro écrit est le neuf, posé à côté de l'ancien identifiant.

**Le patch qui l'écrit dans sa ligne est fabriqué, et je ne l'ai pas joué.** Il est dans `supabase/patch_journal_ancien_numero_2026-11-22.sql`, avec sa répétition (`_REPETITION`, lecture seule) et son retour arrière (`_INVERSE`).

- Il ajoute au journal une colonne **ancien_numero**.
- La pose de nuit l'écrit à chaque fusion (le numéro absorbé) et à chaque scission (le numéro du dossier coupé). Rien d'autre ne change dans la fonction : 5 remplacements, que j'ai relus.
- Les 190 lignes déjà écrites reçoivent leur ancien numéro, lu dans leur ligne de naissance. À blanc, il les trouve toutes, et aucun n'est égal au neuf.
- Le journal accepte un événement **« restauration »**. Une restauration est aussi un changement de numéro : elle doit pouvoir laisser sa ligne.
- **Il s'arrête seul, sans rien laisser**, si la fonction de nuit n'est plus celle lue aujourd'hui (empreinte 815e956f…), si la colonne existe déjà, si la contrainte a changé, ou si une seule ligne reste vide.

Le patch est fabriqué par un outil à partir du texte de la fonction en production, pas recopié à la main : `phase2/checks/fabriquer_patch_journal_ancien_numero.py`.

⚠ **Il touche la fonction que la nuit appelle pour poser les étiquettes.** C'est donc à toi de le coller, si tu le veux.

### b) Les 63 en clair : ancien numéro → neuf

**Comment je donne le neuf.** L'outil `phase2/checks/protocole_les_numeros_neufs.py` refait exactement ce que fait la pose de nuit :

- **l'année** est celle de la plus ancienne transaction du dossier, à défaut celle du mandat ;
- **le rang** est le compteur de cette année, plus l'ordre du dossier parmi ceux qui naissent la même nuit.

**Son témoin :** ma copie du calcul de l'année donne la même réponse que la vraie fonction sur les 11 551 dossiers.

⚠ **L'hypothèse, dite :** la nuit de la pose ne frappe aucun autre numéro de la même année avant ceux-là, par exemple pour une transaction neuve. Si elle en frappe un, les rangs glissent d'autant. Le numéro réel se lira le lendemain matin, dans le journal.

**Au total,** 275 dossiers recevraient un numéro neuf, pour 247 de tes lignes : les 63, plus 8 autres lignes des 2 560, plus 176 hors des 2 560. Le fichier complet est `notice/PROTOCOLE_LES_NUMEROS_NEUFS_ANCIEN_VERS_NEUF_PASSAGE_20_2026-11-22.csv`.

⭐⭐ **Ce que tu dois savoir avant de les relire.** Les 63 sont 60 ventes réglées et 3 annulées.

- **Aucune des 60 ventes réglées ne garde son numéro.** 56 le laissent à une **tentative annulée** sur le même bien, et 4 à une pièce qu'aucune de tes lignes ne porte. C'est donc la vente, avec sa facture et son avis, qui reçoit le neuf.
- **Les 3 annulées :** 2 laissent le numéro à une vente réglée, 1 à une autre annulée.

C'est la conséquence directe de la règle : le numéro est né de la plus ancienne transaction du dossier mal réuni, donc il reste à elle. En contrepartie, chaque numéro porte l'année de sa propre affaire. Pour les 63, le neuf est de la même année que l'ancien 32 fois, et d'une année plus récente (celle de la vente) 31 fois.

Ton oui tient tant que tu ne dis pas autre chose. Je te le redemande seulement parce que tu le donnes maintenant en le sachant.

**La liste.** Pour chaque ligne : ancien → neuf, la ligne du Sheet (ID Unique), acquéreur / vendeur, la ville, l'état, et qui garde l'ancien numéro.

- **D2025-0102 → D2025-0512** · ligne 12 (OAQDRTNC) · Mme M. COSTA Natalia et Paulo / Ind. DELABRE - Fabrice Delabre, Magali Delabre · Saint Pierre Duchamp · vente réglée · l'ancien reste à 44ZVGG8Q (ligne 3407, annulée)
- **D2025-0007 → D2025-0500** · ligne 61 (USL9H5AJ) · M. ANDRE DE L'ARC Anis / Mme et M. LAC Liliane et Michel · Le Monsastier · vente réglée · l'ancien reste à 515UT1WG (ligne 3410, annulée)
- **D2024-0235 → D2025-0514** · ligne 126 (1TZEGF2D) · Mme et M. TARDY Julie MADAR Nicolas / Mme et M. PETIT Séverine LIMA David · Saint Just Saint Rambert · vente réglée · l'ancien reste à HTFNZ9Z2 (ligne 3416, annulée)
- **D2023-0356 → D2025-0507** · ligne 155 (DKTK22F2) · M. DJEBBOUR Jacques / M. GEST Serge · Mazeyrat d'Allier · vente réglée · l'ancien reste à ZE9WZW22 (ligne 3575, annulée)
- **D2024-0312 → D2025-0499** · ligne 159 (BZDTPD98) · M. JAMON Romain / Mme ISSARTEL Alisson M. ROMEAS Valentin · Le Puy · vente réglée · l'ancien reste à HRC324JH (ligne 3455, annulée)
- **D2024-0358 → D2024-0509** · ligne 196 (ZLY1CLKF) · Mme et M. FOURNEL Dominique et Nicole / Mme et M. VASSIAS Sylvie et Laurent · vente réglée · l'ancien reste à 1W9FJJLB (ligne 3446, annulée)
- **D2024-0302 → D2024-0519** · ligne 261 (A94E7E0K) · JOUVE / PICHARD · Beauzac · vente réglée · l'ancien reste à FTRYKTSC (ligne 3465, annulée)
- **D2024-0088 → D2024-0521** · ligne 401 (UZ7HB9VH) · KARA / ind.BERNARD · Le Chambon-Feugerolles · vente réglée · l'ancien reste à GEQKYZCN (ligne 3511, annulée)
- **D2023-0484 → D2024-0533** · ligne 402 (K013ZH03) · PICHARD / EXBRAYAT · vente réglée · l'ancien reste à EO8MXFE9 (ligne 3508, annulée)
- **D2023-0393 → D2024-0518** · ligne 488 (D5KU9GNT) · DELORME / ind.SIMONET · Sainte-Sigolène · vente réglée · l'ancien reste à WBKHIDHS (ligne 3581, annulée)
- **D2023-0300 → D2024-0516** · ligne 504 (7BPVD7K4) · BOYER LEPIECK / SOUCHE LAFARGE · Issoire · vente réglée · l'ancien reste à TCB4ZNQO (ligne 3608, annulée)
- **D2023-0502 → D2024-0508** · ligne 513 (YPNDHILU) · BENKHELIFA / ind.MAZET · vente réglée · l'ancien reste à une pièce sans ligne (1059)
- **D2023-0036 → D2024-0528** · ligne 517 (SS4I5EZW) · MERSCH / FAVERGEAT · Le Mas-de-Tence · vente réglée · l'ancien reste à 3LMG7EXA (ligne 3651, annulée)
- **D2023-0257 → D2024-0532** · ligne 529 (GWAP2ROG) · ARPIN / SCI DAIKIMMO · Riotord · vente réglée · l'ancien reste à AA797XO0 (ligne 3625, annulée)
- **D2022-0507 → D2023-0586** · ligne 541 (3X3UPF1Q) · POUGET / DOMAINES DGFIP · Marat · vente réglée · l'ancien reste à TZPT6V9Y (ligne 3654, annulée)
- **D2023-0272 → D2023-0581** · ligne 544 (F6XBD2IU) · JACQUIN BECHU / SOURD · Saint-Étienne · vente réglée · l'ancien reste à G1TVNXJ5 (ligne 3614, annulée)
- **D2023-0328 → D2023-0579** · ligne 565 (P0YMQODU) · DEBRAY / ind. Bachelard · Saint-Étienne · vente réglée · l'ancien reste à 7HDK9XOG (ligne 3613, annulée)
- **D2023-0050 → D2023-0584** · ligne 784 (WVMPHHDQ) · CAZAL / IND.POUILLON · Ambert · vente réglée · l'ancien reste à HEQZW1KO (ligne 3636, annulée)
- **D2022-0374 → D2023-0585** · ligne 825 (TL9AFW0O) · MALEYSSON / PASCAL · Dore l'Eglise · vente réglée · l'ancien reste à FWCFAN6O (ligne 3663, annulée)
- **D2023-0029 → D2023-0605** · ligne 845 (305KAY9W) · COLAVITTI / GRANGIER · Craponne-sur-Arzon · vente réglée · l'ancien reste à H75WKJ6X (ligne 3660, annulée)
- **D2022-0053 → D2023-0592** · ligne 906 (U43BNSQW) · MATTIO / ind.BRUCHET · Bas-en-Basset · vente réglée · l'ancien reste à IPTGNTAL (ligne 3793, annulée)
- **D2022-0461 → D2022-0652** · ligne 925 (UHVX3QH1) · CARRONNIER / RODE · Annonay · vente réglée · l'ancien reste à LM6YKKZP (ligne 3704, annulée)
- **D2022-0001 → D2022-0635** · ligne 1003 (AOPBUAOJ) · HENRY / ind.GRANGE · Saint-Étienne · vente réglée · l'ancien reste à une pièce sans ligne (125)
- **D2022-0324 → D2022-0639** · ligne 1017 (ZOJDHHL9) · GIRAUD FAGON / CHENEVOTOT · Vals-près-le-Puy · vente réglée · l'ancien reste à TQYCQNY4 (ligne 3756, annulée)
- **D2022-0058 → D2022-0642** · ligne 1096 (N1CUULMN) · MARCHEPOIL / DUCHOSAL PECCAND · Ambert · vente réglée · l'ancien reste à 9WQ204HP (ligne 3763, annulée)
- **D2021-0340 → D2022-0672** · ligne 1103 (7P1JJ2PP) · PONSON / CARBONNET · Craponne-sur-Arzon · vente réglée · l'ancien reste à D7CZQBZG (ligne 3940, annulée)
- **D2021-0704 → D2022-0651** · ligne 1192 (5VZDGQC3) · BARCZYNSKI / JACOMINO · Brassac-les-Mines · vente réglée · l'ancien reste à U39MLAJD (ligne 3797, annulée)
- **D2020-0558 → D2022-0671** · ligne 1282 (RF9KYWSY) · PROST DILLARD / PRALONG · La Chaise-Dieu · vente réglée · l'ancien reste à 9KHYVR1M (ligne 3788, annulée)
- **D2021-0329 → D2022-0654** · ligne 1311 (DY4JG42E) · PARROT PINATEL / RESIDENCE AMPERE BOURGIN · Annonay · vente réglée · l'ancien reste à 73FOXX2A (ligne 3813, annulée)
- **D2022-0145 → D2022-0675** · ligne 1321 (81LLHEM6) · ELHAJJAM / cts EYRAUD · Saint-Étienne · vente réglée · l'ancien reste à J1JRBV76 (ligne 3794, annulée)
- **D2021-0192 → D2022-0648** · ligne 1375 (YMEKXZK3) · BOUAMAR / RIOCREUX SOUBEYRAND · Firminy · vente réglée · l'ancien reste à 13KBCS85 (ligne 3936, annulée)
- **D2021-0638 → D2022-0673** · ligne 1380 (BETUXDEN) · MEYER / GIRAUD CALVET · Craponne-sur-Arzon · vente réglée · l'ancien reste à 6U5DQQ4J (ligne 3865, annulée)
- **D2021-0506 → D2022-0670** · ligne 1446 (FRROUPY0) · BUFFERNE / MONTELLIMARD AUCOUTURIER · Craponne-sur-Arzon · vente réglée · l'ancien reste à HW5D0412 (ligne 3871, annulée)
- **D2021-0671 → D2022-0646** · ligne 1469 (BLKP7JFQ) · EDANGE / GUYOT · Aurec-sur-Loire · vente réglée · l'ancien reste à GPO3PZ76 (ligne 3849, annulée)
- **D2021-0648 → D2022-0659** · ligne 1471 (TFK7BD9K) · NICOUD / IND RUEL · Mazet-Saint-Voy · vente réglée · l'ancien reste à S3HOG6UL (ligne 3864, annulée)
- **D2021-0690 → D2021-0770** · ligne 1490 (X89SXIQZ) · BOULET / BASTY · Bourg-Argental · vente réglée · l'ancien reste à SXG8691T (ligne 3844, annulée)
- **D2021-0425 → D2021-0802** · ligne 1516 (W79RISV0) · MAIRIE DE ST ROMAIN LACHALM / DELPORTE · Saint-Romain-Lachalm · vente réglée · l'ancien reste à FVLMAQ63 (ligne 3899, annulée)
- **D2021-0559 → D2021-0771** · ligne 1521 (29YBUBYA) · DJOUABRI / BONCHE · Firminy · vente réglée · l'ancien reste à 6NOJ686I (ligne 3860, annulée)
- **D2020-0570 → D2021-0816** · ligne 1593 (MPF7E8N7) · SCI Patrimonial Dassaud / LENOIR · Courpière · vente réglée · l'ancien reste à KBW3J7DF (ligne 3978, annulée)
- **D2021-0399 → D2021-0756** · ligne 1594 (WPGZK930) · GARVEY / CELLE · Olliergues · vente réglée · l'ancien reste à Z1EU0WC6 (ligne 3890, annulée)
- **D2020-0281 → D2021-0810** · ligne 1601 (L4HEO3NF) · MATEUS / KOCA · Sury-le-Comtal · vente réglée · l'ancien reste à RP4HBTQN (ligne 4020, annulée)
- **D2021-0411 → D2021-0774** · ligne 1683 (AIV9UI0I) · SUSSL / MAGNET · Annonay · vente réglée · l'ancien reste à P0YWKL8J (ligne 3904, annulée)
- **D2021-0041 → D2021-0799** · ligne 1707 (DBRDHEGH) · DUPUY / CHAPUIS · La Tourette · vente réglée · l'ancien reste à VMWFLLW4 (ligne 3910, annulée)
- **D2021-0363 → D2021-0789** · ligne 1738 (C0U52ILC) · PAUCHON / ind GRAND · Saint-Julien-Molhesabate · vente réglée · l'ancien reste à YKSL5L2U (ligne 3939, annulée)
- **D2021-0371 → D2021-0801** · ligne 1780 (PB3ASE0N) · JACQUIER / MONTMARTIN · Saint-Didier-en-Velay · vente réglée · l'ancien reste à NOPYBDHI (ligne 3951, annulée)
- **D2020-0227 → D2021-0761** · ligne 1791 (VHE3HXC3) · CHAPELAT / SCI L'ESPOIR · Ambert · vente réglée · l'ancien reste à KCKQMFIL (ligne 4079, annulée)
- **D2021-0314 → D2021-0769** · ligne 1841 (H6CTRVR6) · MERCIER / MATHON · Saint-Étienne · vente réglée · l'ancien reste à E9GL6MUS (ligne 3958, annulée)
- **D2020-0420 → D2021-0809** · ligne 1869 (DKH6IOKA) · PIERA / FLATTIN · Sury-le-Comtal · vente réglée · l'ancien reste à YV95DVKD (ligne 3960, annulée)
- **D2020-0515 → D2021-0779** · ligne 1884 (JUTS27P6) · DU PELOUX / PLASSARD · Annonay · vente réglée · l'ancien reste à R0JRVFDC (ligne 4014, annulée)
- **D2020-0289 → D2021-0759** · ligne 1946 (VX5RZL6B) · OSTRÉ OLIVIERI / COMPTE · Arlanc · vente réglée · l'ancien reste à HHQZC2QP (ligne 3999, annulée)
- **D2020-0418 → D2021-0787** · ligne 2062 (M8QJWMBM) · MEYER ROUVEYROL / BARRALON · vente réglée · l'ancien reste à 39USDYL2 (ligne 4049, annulée)
- **D2019-0404 → D2020-0642** · ligne 2138 (XH5KZ9LI) · WOJNOWITSH BOUTTET / REYNAUD ind · Connangles · vente réglée · l'ancien reste à 0OO1BEZD (ligne 4114, annulée)
- **D2019-0155 → D2020-0643** · ligne 2203 (VNK6GU21) · CRISCOLO / MOLINO BEYSSAC · Craponne-sur-Arzon · vente réglée · l'ancien reste à 1X9W3VUF (ligne 4090, annulée)
- **D2018-0218 → D2018-0538** · ligne 3128 (KTZJRCR2) · BELIC / BAYON ind · vente réglée · l'ancien reste à une pièce sans ligne (16143)
- **D2018-0361 → D2018-0537** · ligne 3169 (QL70KV8I) · SCI LA PETITE VERRIERE / MEZABER · vente réglée · l'ancien reste à une pièce sans ligne (12566 12569)
- **D2022-0523 → D2022-0663** · ligne 3717 (CYZA6GYS) · SOTTON / SAVIN · Dunières · annulée · l'ancien reste à A8LNQDOQ (ligne 1049, vente réglée)
- **D2022-0058 → D2022-0643** · ligne 3785 (3308P0UX) · VIALLARD / DUCHOSAL PECCAND · Ambert · annulée · l'ancien reste à 9WQ204HP (ligne 3763, annulée)
- **D2022-0060 → D2022-0666** · ligne 3815 (RD4LZYW0) · BADEL / MOULIN · Saint-Romain-Lachalm · annulée · l'ancien reste à HMVS1CZT (ligne 1342, vente réglée)
- **D2024-0409 → D2025-0505** · ligne 4173 (U8739KRW) · M. CHAUSSE Philippe / Mme M. COURT Arlette et Paul · Malvalette · vente réglée · l'ancien reste à ABDXFMQC (ligne 3418, annulée)
- **D2025-0254 → D2025-0502** · ligne 4284 (c08ff7cb) · M. DEFOUR Jean-Luc / ind. POUZOULAS _ Réjane Pouzoulas et Wilfried Pouzoulas · Alleyrac · vente réglée · l'ancien reste à 721e650c (ligne 4252, annulée)
- **D2025-0216 → D2025-0510** · ligne 4334 (e48a523c) · Mme M. MARTIN Michel MALIGE Sylvia / Mme M. HENNARD Niyada et Michel · Allègre · vente réglée · l'ancien reste à 8c7725f2 (ligne 4188, annulée)
- **D2025-0360 → D2025-0513** · ligne 4442 (46b0a92c) · Mme HOUPLAIN Véronique / M. PIERSON Daniel · Sauvessanges · vente réglée · l'ancien reste à 64225027 (ligne 4286, annulée)
- **D2026-0002 → D2026-0393** · ligne 4460 (e9260960) · Mme HUGON Fabienne / ind. ESPITALIER CRUZOT : Michel Cruzot, Guillaume Espitalier · Unieux · vente réglée · l'ancien reste à 4f7b9749 (ligne 4418, annulée)

### La réserve : le numéro est-il sorti de la maison ?

**Non, par aucun chemin que la maison possède.** La réserve est levée par la mesure.

- **Le code :** seules la pose et le journal lisent ce numéro. Les écrans ne le demandent même pas : la lecture du registre ne le sélectionne pas. Le serveur, le worker et les tâches : 0. L'historique git : il n'y a jamais été.
- **Ton Sheet :** 0 numéro D20xx-xxxx.
- **Ce qui sort :** j'ai fouillé 8 tables (e-mails envoyés, espace client, notifications, assistant, relances, demandes et événements de signature, avis). Il apparaît 0 fois sur 5 339 lignes.
- **Le « numéro de dossier » imprimé ailleurs** (la fiche notaire, par exemple) est celui de **Hektor** (VT9562, VA6482…). Je n'y trouve aucun D20xx sur 62 557 lignes.
- **Ce que je ne peux pas mesurer :** une recopie à la main, depuis mes fichiers de travail, vers un papier.

## 2. R7b — réversible, et le reste à vider

**a) Réversible : prouvé avec le vrai chaînage.** L'outil est `phase2/checks/protocole_r7b_reversible.py`. Il fait deux rejeux : le brouillon tel qu'il serait posé, et le même brouillon **sans ses 8 lignes « mise de côté »**.

- **Figer ne change rien :** les 12 dossiers sont exactement ceux d'aujourd'hui, pièce pour pièce, chacun avec son numéro.
- **Défaire, c'est retirer ces 8 lignes du fichier.** Aujourd'hui, ça ne déplace aucune pièce et ne change aucune étiquette. Ces lignes servent seulement à protéger ces dossiers les nuits suivantes.

**b) Le reste à vider : ⚠ elles ne sont pas deux, mais trois.** Je t'en avais nommé deux, j'en avais manqué une.

- **3QZ4DAD1** (VACHER PEYRARD, dossier D2021-0326) : en attente.
- **ARF57GC5** (THOURY, D2020-0527) : en attente.
- **86da6949** (ligne 4724, TAVERNIER / BOURSIER, Ambert, annulée) : en attente. Son seul lien est l'offre refusée 29000 du 08/09/2026, qui est elle-même la pièce mise de côté. Son dossier, D2026-0297, ne contient qu'elle.

Les trois ont le motif « ses pièces à part » et restent dans les 225. Chaque passage les nomme désormais : « figées n'est pas réglées ».

## 3. La sauvegarde datée qui se relit

**L'outil :** `phase2/checks/sauvegarde_datee_classeur.py`. Il range ses sauvegardes dans `C:\Hektor\Backups\classeur\<date>\`, hors du dépôt, comme les autres sauvegardes du projet.

**Ce qu'il emporte :**

- le registre (pièce, chaîne, étiquette, numéro) ;
- **le gel en entier** : jusqu'ici, il n'avait aucune copie chez nous ;
- le compteur et le journal ;
- la table des avis, sans le nom de qui l'a écrite ;
- le registre local, ton Sheet entier (dont la colonne A), et les deux fichiers de décisions.

Tout est lu en une seule transaction de lecture, pour avoir une photo cohérente. L'empreinte de chaque table est **calculée par Postgres** au même moment.

**Une répétition, pas la vraie :** `2026-11-22_163632`, prise à 16:36. La vraie se prendra juste avant la première écriture.

**1. La relecture,** dans un processus neuf et depuis le disque :

- les 9 fichiers sont à leur empreinte ;
- le contenu des 5 tables, recompté ligne par ligne, redonne chacun l'empreinte de Postgres ;
- le registre local est identique à Supabase, 31 368 lignes sur 31 368. La même empreinte est calculée par Python d'un côté et par Postgres de l'autre, ce qui prouve que la formule est la même ;
- rien n'a bougé dans la base depuis.

**2. Le témoin inverse :** une sauvegarde abîmée doit être refusée.

- J'ai changé une seule étiquette et recalculé l'empreinte du fichier pour la camoufler : refusée, le contenu ne redonne plus celle de Postgres.
- J'ai changé un octet sans rien recalculer : refusée deux fois.

**3. ⭐ La preuve des 216,** sur une copie :

- **L'arrivée du protocole :** 728 étiquettes changent.
- **On défait sans sauvegarde,** en retirant le fichier : les dossiers reviennent tous (31 368 sur 31 368), mais **216 étiquettes ne reviennent pas**, sur 215 dossiers.
- **La restauration,** fabriquée depuis le fichier relu : 216 instructions, 216 lignes remises. Elle écrit aussi 215 lignes « restauration » au journal, et l'ancien n'est jamais égal au neuf.
- **La copie restaurée** retrouve exactement l'empreinte de Postgres au moment de la sauvegarde. **Les 216 sont revenues, sans exception.**

Le détail, pièce par pièce, est dans `notice/SAUVEGARDE_EPREUVE_LES_216_ETIQUETTES_2026-11-22_163632.csv`.

**4. Contre la base d'aujourd'hui,** il n'y a rien à restaurer : 0 ligne, et aucun patch fabriqué.

⛔ **Le compteur ne recule jamais.** Un numéro donné une fois ne se redonne pas, sinon deux dossiers porteraient le même numéro à deux dates. La sauvegarde garde le compteur comme témoin, et la restauration n'y touche pas. Elle exige aussi que le patch du journal soit posé.

## 4. La sentinelle des 2 560

Je garde ce témoin comme **sentinelle**, et elle le dit en tête : « pas un juge ». Chaque fois qu'elle tourne, elle dit ce qui a bougé depuis la mesure précédente, ligne par ligne : le numéro de la table, ce que le gel désigne, ce que dit le protocole. Depuis le passage 20, les trois comptes sont à 0, et l'empreinte de la table n'a pas changé.

## 5. Ce qui n'est pas fait

- **Le patch du journal :** fabriqué, pas joué.
- **La vraie sauvegarde :** elle se prendra juste avant la première écriture (prendre, relire, éprouver).
- **La mesure du matin :** la nuit n'est pas passée. Demain, je fais l'image, puis je te dis **d'abord** ce que la nuit a déplacé, et seulement ensuite le passage, la sentinelle et la comparaison au passage 20.
- **Le reste à vider :** les 225 lignes en attente, inchangées. G2 reste en attente.

## Ce que j'attends de toi

1. **Le patch du journal** (l'ancien numéro écrit dans sa ligne, et l'événement « restauration ») touche la fonction que la nuit appelle. Le colles-tu ?
2. **Les 63 :** sachant qu'aucune des 60 ventes réglées ne garde son numéro (56 le laissent à une tentative annulée), ton oui à la règle du plus ancien tient-il ?
3. **86da6949 :** ton oui à R7b couvre-t-il aussi cette troisième ligne, figée de la même façon et qui reste en attente ?
