# AUDIT — LES COUPLES ANCIENS : QUI AFFICHER EN « COUPLE » ? *(01/11/2026)*

> **Demande de Frédéric (01/11)** : *« Pour trancher comment afficher les couples anciens, je dois avoir une analyse précise de ma
> data contact. Audit et conseille-moi. »* Suite de sa consigne du 31/10 : *« Il faudra traiter cela avant P3, c'est très
> important !!! »* (note couples §23).
>
> **Lecture seule.** Registre local `phase2/phase2.sqlite`, table `app_contact_current` (356 762 fiches, état du run du 01/11).
> Rien écrit, 0 appel à Hektor. Scripts de mesure : bloc-notes de la session (`audit_couples_anciens.py`, `audit_couples_2.py`,
> `audit_couples_3.py`). Aucun nom de personne : les échantillons ont été regardés en initiales seulement.
> **Audit limité à l'AFFICHAGE du couple** (objet contact, geste « lire »). Créer, modifier, compléter, dissocier : non mesurés ici.

---

## 1. EN UNE PAGE

- **Le marqueur de couple de Hektor (`refCouple`) ne dit PAS si la personne vit en couple.** Avant 2021, Hektor a mis presque
  **tout le monde** en foyer : 96 % des « M. » créés en 2005-2010, 98 % en 2011-2014, contre **2 % en 2026**. C'est une époque
  du logiciel, pas un choix de l'agence.
- **La seconde fiche vide est une place créée par la machine**, jamais remplie : sur les 10 758 secondes vides des contacts
  vivants, **0 téléphone, 0 e-mail**, **10 757 nées le même jour que leur première**, **10 076 numérotées en 400 000 – 599 999**
  (la vague de rétro-création mesurée le 11/09).
- ⭐ **SUR TOUT LE SERVEUR (section 4 bis, demandée par Frédéric) : 139 897 foyers**, dont **26 067 (18,6 %) portent un signe
  écrit par une personne** et **101 492 (72,5 %) n'en portent AUCUN**. Seuls **14 779** sont aujourd'hui dans l'app.
- ⭐⭐ **Le « conjoint nommé » est presque toujours un NOM RECOPIÉ** : sur 13 562 secondes fiches nommées du serveur, **13 129 portent
  le même nom que la première, sans prénom, sans téléphone ni e-mail, nées le même jour**. **Seuls 421 foyers sur 139 897 ont un
  conjoint avec un prénom** (371 avec un téléphone ou un e-mail). Le couple y est écrit (civilité « Mr./Mme »), le conjoint non.
- **Les signes écrits par une PERSONNE existent, et ils sont fiables** : un conjoint nommé, une civilité de couple, deux prénoms
  dans la fiche. Dans l'app, ils couvrent **2 991 couples vivants sur 14 779 (20 %)**.
- **9 278 « couples » vivants (63 %) n'ont AUCUN signe de couple** : ni conjoint, ni civilité de couple, ni deux prénoms, ni
  conjoint possible ailleurs dans le fichier. Les afficher « Couple » serait faux pour une grande partie d'entre eux.
- ⭐ **Même les « conjoints nommés » sont minces** : sur 1 900, **1 598 n'ont qu'un NOM, sans prénom** (souvent le même nom que la
  première), 234 ont un téléphone, 269 un e-mail. Le couple est sûr, mais le conjoint n'a presque jamais d'identité complète.
- **Conseil** : n'afficher « Couple » que là où une personne l'a écrit (section 5, règle A). Le lien de ménage reste dans les
  données, rien n'est supprimé.

---

## 2. LE MARQUEUR DE COUPLE SUIT L'ÂGE DU LOGICIEL, PAS LA VIE DES GENS

**Part des fiches nommées (hors secondes) mises en foyer, selon la civilité et la période de création :**
- 2005-2010 : « M. » **96 %** · sans civilité **72 %** · « Mr./Mme » 100 %
- 2011-2014 : « M. » **98 %** · sans civilité **73 %** · « Mr./Mme » 100 %
- 2015-2020 : « M. » **89 %** · sans civilité **58 %** · « Mr./Mme » 93 %
- 2021-2025 : « M. » **55 %** · sans civilité **36 %** · « Mr./Mme » 77 %
- 2026 : « M. » **2 %** · sans civilité **11 %** · « Mr./Mme » 95 % · codes de couple (`M_Mme`…) 391 fiches

**Ce que ça prouve** : une agence ne vend pas à 96 % de couples en 2008 et à 2 % en 2026. Le foyer était posé par défaut ; depuis
février 2026 (audit du 29/10, §10.2) il ne l'est plus que si l'agent choisit un couple.

**La civilité « Mme. » n'existait pas avant 2026** : 3 fiches en 2005-2010, 3 en 2011-2014, 15 en 2015-2020, 41 en 2021-2025, puis
1 441 en 2026. ⇒ avant 2026, la civilité ne disait pas le sexe ; « M. » et « vide » étaient des valeurs par défaut. Elles ne disent
rien du couple.

**Le cas « aucune seconde fiche » est lui aussi une époque** : 8 000 par an en 2011-2014 (des foyers sans seconde fiche), presque
aucun avant ou après. Ce n'est pas un signe de plus ou de moins de couple.

---

## 3. LES SIGNES ÉCRITS PAR UNE PERSONNE

- **« Mr./Mme »** : c'était la civilité du formulaire « couple » de Hektor jusqu'en janvier 2026. **97 %** des couples à conjoint
  nommé la portent (13 108 sur 13 562), contre **2,2 %** des personnes sans foyer (1 569 sur 69 872). C'est un vrai signe.
  ⚠ La seconde fiche rétro-créée la porte aussi (110 872 secondes vides en « Mr./Mme ») : le signe ne vaut que sur la PREMIÈRE.
- **Les codes de couple** (`M_Mme`, `Mme_M`, `Mme_Mme`, `M_M`) : ne viennent que du formulaire couple depuis 2026. Signe sûr.
- **Deux personnes écrites dans la fiche** : « A. et T. », « O./C. », « M et Mme … », « époux … ». 4,3 % des premières à conjoint
  vide ont « et » dans le prénom, contre 0,8 % des personnes seules. Échantillon regardé à l'œil (initiales) : ce sont bien deux
  prénoms.
- **Un conjoint possible AILLEURS dans le fichier** : une autre fiche, hors du foyer, au même nom, avec un autre prénom, à la même
  adresse, au même téléphone ou au même e-mail. Indice seulement : ce peut être un enfant, un parent, un frère. 2 098 couples vivants,
  dont 1 259 où l'autre fiche est elle aussi dans l'app (adresse 1 414, téléphone 1 046, e-mail 799).

**Ce qui n'est PAS un signe** :
- les rôles : la seconde vide est rattachée aux biens comme la première (4 633 « mandant », 3 366 « propriétaire ») parce que
  Hektor rattache le foyer entier ;
- la civilité « M. » ou vide (section 2) ;
- « vide » contre « aucune seconde » (section 2).

---

## 4. LES 14 779 COUPLES VIVANTS DE L'APP, CLASSÉS

*(premières fiches envoyées vers l'app et non archivées ; chaque fiche dans la PREMIÈRE catégorie qui la prend, dans cet ordre)*

- **1. SÛR — conjoint nommé** : **1 900** (12,9 %). Dont 1 598 sans prénom, 156 à nom différent de la première, 79 au même nom ET
  même prénom que la première (doublon probable plutôt que conjoint), 234 avec téléphone, 269 avec e-mail ; 1 893 portent
  « Mr./Mme » ou un code.
- **2. SÛR — code de couple sans conjoint** : **9**.
- **3. PROBABLE — deux personnes dans le prénom ou le nom** : **695** (4,7 %), presque tous aussi en « Mr./Mme ».
- **4. PROBABLE — civilité « Mr./Mme » seule** : **387** (2,6 %).
- **5. INDICE — conjoint possible ailleurs dans le fichier** : **2 098** (14,2 %).
- **6. COLLECTIF — indivision, consorts, succession, société…** : **412** (2,8 %). Plusieurs personnes, mais pas un couple.
- **7. RIEN — aucun signe de couple** : **9 278** (62,8 %), dont 7 666 « seconde vide » et 1 612 « aucune seconde ». Créées de 2005 à
  2026, sans période dominante.

**Total sûr ou probable (1 + 2 + 3 + 4) : 2 991, soit 20 %.**

---

## 4 bis. TOUT LE SERVEUR : LES 356 762 FICHES ET LES 139 897 FOYERS *(question de Frédéric, 01/11)*

**L'inventaire des 356 762 fiches du registre du serveur :**
- 139 891 premières de foyer nommées (+ 6 vides) ;
- 96 889 secondes vides, et 13 989 autres secondes vides dont la première n'est plus sur le serveur ;
- 13 565 secondes nommées (+ 91 dont la première n'est plus sur le serveur) ;
- 69 872 fiches nommées sans foyer (11 362 dans l'app, 16 224 actives hors app, 42 286 archivées) ;
- 22 459 fiches vides sans foyer.

**Les 139 897 foyers, classés comme à la section 4** *(total · dans l'app · actifs hors app · archivés)* :
- **1. SÛR — conjoint nommé** : **13 562** (9,7 %) · 1 900 · 3 520 · 8 142 — ⚠ dont **13 141 sans prénom** (voir plus bas) ;
- **2. SÛR — code de couple** : **16** · 9 · 3 · 4 ;
- **3. PROBABLE — deux personnes écrites** : **6 793** (4,9 %) · 695 · 1 820 · 4 278 ;
- **4. PROBABLE — « Mr./Mme » seule** : **5 696** (4,1 %) · 387 · 1 164 · 4 145 ;
- **5. INDICE — conjoint possible ailleurs** : **10 899** (7,8 %) · 2 098 · 3 378 · 5 423 ;
- **6. COLLECTIF** : **1 439** (1,0 %) · 412 · 650 · 377 ;
- **7. RIEN — aucun signe** : **101 492 (72,5 %)** · 9 278 · 27 027 · 65 187.
- **Total** : 139 897 · 14 779 dans l'app · 37 562 actifs hors app · 87 556 archivés.

⇒ **Sur tout le serveur, 26 067 foyers (18,6 %) portent un signe de couple écrit ; 101 492 (72,5 %) n'en portent aucun.** La
proportion est la même dans l'app (20 % / 63 %) : l'app n'est pas un cas à part, c'est un échantillon du serveur.

**⭐⭐ Le « conjoint nommé » est presque toujours un NOM RECOPIÉ.** Sur les 13 562 secondes fiches nommées :
- **13 129** portent **le même nom que la première, sans prénom** ; les 13 141 sans prénom sont **toutes nées le même jour** que leur
  première, et **17** seulement ont un téléphone ou un e-mail ;
- **421** seulement ont un prénom (371 d'entre elles avec un téléphone ou un e-mail) : **ce sont les seuls vrais conjoints connus
  du serveur** (dans l'app : 302).
- La première porte « Mr./Mme » dans 97 % des cas : **le couple a bien été choisi par l'agent** (formulaire couple), mais **le
  conjoint, lui, n'a jamais été saisi** — Hektor a recopié le nom de famille dans la place du second membre (comme sur 1078 / 1079,
  audit du 29/10, §10.1).
- **Conséquence pour l'écran** : un « Couple · prénoms » n'aura un second prénom que pour **421 foyers sur tout le serveur**.
  Partout ailleurs, l'orange « conjoint à compléter » est juste.

## 5. LES RÈGLES POSSIBLES, ET CE QU'ELLES AFFICHENT

**Règle A — « Couple » seulement si une personne l'a écrit** *(CONSEILLÉE)*
- « Couple » : catégories 1 à 4, **2 991 fiches**.
- Orange « conjoint à compléter » **sur la fiche seulement** (réponse 2 du 31/10, gardée) : quand le conjoint n'a pas de prénom ou
  n'existe pas, soit environ **2 690** des 2 991 (sur tout le serveur : ~25 630 des 26 067).
- **Sur tout le serveur** : « Couple » sur **26 067** foyers, personne seule sur **113 830**.
- Tout le reste (**11 788**, catégories 5, 6 et 7) : affiché comme **une personne seule**, comme aujourd'hui ; la seconde fiche vide
  reste masquée, comme aujourd'hui.
- Ce qu'elle rate : un vrai couple dont personne n'a rien écrit. Il le reste aujourd'hui de toute façon : l'écran n'aurait rien
  d'autre à montrer qu'une pastille orange vide.

**Règle B — « Couple » partout où Hektor a mis un foyer** *(la réponse 1 du 31/10, donnée avant cette mesure)*
- « Couple » sur les **14 779** ; orange sur ~12 900.
- Ce qu'elle casse : **9 278 fiches sans aucun signe** porteraient « Couple », la plupart pour une personne seule ; et l'étiquette
  ne voudrait plus rien dire pour les agents.

**Règle C — « Couple » seulement si le conjoint est nommé**
- « Couple » sur **1 909** (1 + 2) dans l'app, **13 578** sur le serveur — mais 13 141 de ces « nommés » n'ont qu'un nom recopié :
  la règle C ne vaut donc guère mieux que « civilité Mr./Mme ».
- Ce qu'elle rate : **1 082 couples écrits en clair** (« A. et T. », « Mr./Mme ») qui s'afficheraient en personne seule.

---

## 6. LE CONSEIL

1. **Prendre la règle A.** Elle n'affiche « Couple » que sur ce qu'une personne a écrit, et elle garde les deux réponses du 31/10
   qui restent vraies (l'orange seulement sur la fiche ; montrer la première seconde nommée et signaler les autres). Elle **remplace
   la réponse 1** (« les 2 122 couples sans seconde fiche en couple vide ») : ils suivent la même règle que les autres.
2. **Calculer le signe la nuit, pas à l'écran.** L'étape de nuit P2 (`conjoints_des_couples.py`) connaît déjà le foyer ; elle
   ajouterait une clé `signe` dans `couple_json` (« sûr », « probable », « aucun »). L'écran n'aurait qu'à la lire. Une seule règle,
   au même endroit, testable. *(Modification de code existant : elle attend ton « vas-y ».)*
3. **Ne rien supprimer, ne rien réécrire chez Hektor.** Le lien de ménage reste dans `couple_json` même quand l'écran affiche une
   personne seule : le jour où un agent ajoute le conjoint (décision 3, « Compléter le conjoint »), le foyer est déjà là.
4. **Les 2 098 « conjoints possibles ailleurs » sont un sujet à part.** Proposer « cette fiche est peut-être son conjoint » touche aux
   doublons et aux liens entre deux foyers : ce n'est pas P3. À décider plus tard, s'il le veut.
5. **Les 79 « conjoints » identiques à la première** (même nom, même prénom) sont probablement des doublons. À regarder avec les
   doublons, pas dans P3.

**Ce que ça pourrait casser ailleurs** : rien n'est écrit par cet audit. La règle A ne change que l'étiquette de l'écran (P3) ;
la recherche générale, le choix d'un mandant, le registre et la signature lisent déjà les fiches sans tenir compte de
l'étiquette. La clé `signe` serait une clé de plus dans `couple_json` : la première nuit, toutes les premières concernées
repartiraient une fois vers l'app (~15 000 lignes).

**Comment on vérifiera** : les mêmes comptes après la nuit (2 991 « sûr ou probable », 11 788 « aucun »), et le témoin
inverse : aucune fiche sans foyer ne prend de `signe`.

---

## 7. CE QUI N'EST PAS MESURÉ

- La **date de la vague de rétro-création** chez Hektor : on voit ses traces (numéros 400 000 – 599 999, date recopiée), pas le
  jour.
- Le **bloc « membre 2 » du formulaire Hektor** fiche par fiche : il n'est pas dans l'API ; E0 (30/10) l'a lu sur 31 foyers, et
  33 660 des 35 914 secondes vides pendaient à une première SANS bloc membre 2. La seconde fiche en est le miroir (audit du 29/10,
  §10.1), donc elle suffit.
- La **qualité des 2 098 indices** : un échantillon regardé par une personne dirait combien sont des conjoints.
- ✅ *(levé le 01/11)* Les archivés et les fiches hors de l'app : mesurés à la section 4 bis, tout le serveur.
- Les 22 459 fiches vides sans foyer et les 14 080 secondes dont la première n'est plus sur le serveur : leur nom est perdu chez
  nous (audit du 29/10, §4) ; elles ne s'affichent pas comme couple, cet audit ne les traite pas.

---

## 8. LES DOUBLONS DE CONTACTS ET LES COUPLES *(question de Frédéric, 01/11 : « peut-être que c'est lié ou pas »)*

**D'où ils viennent.** Le détecteur est né avec le registre des contacts (commit `915f6cd`, 27/05/2026 ;
`RAPPORT_EXPLICATIF_CONTACTS_HEKTOR_2026-05-25.md` §5 : 36 427 groupes sur 354 293 fiches, « revue métier, aucune suppression
automatique »). Il tourne chaque nuit (`build_contacts_layer.py`, `duplicate_key_groups`, l. 1645) avec 4 règles : même e-mail ·
même e-mail + tél + nom · même tél + nom · même nom + prénom + lieu. **Aucune fusion n'a jamais été faite** (L5 / E.0-bis, reportée).

**Aujourd'hui (calcul du 01/11 04:44)** : 37 715 groupes, 48 333 fiches. Lus nom par nom, ils sont de quatre sortes :

- **27 500 groupes = la même personne** → **12 950 personnes en 27 810 fiches, 14 860 fiches en trop**. 5 877 personnes toutes
  archivées, 4 949 actives + archivées (le soupçon « archivage par erreur » de mai), 2 124 toutes actives. Dans l'app : 2 868
  personnes touchées, **444 avec deux fiches vivantes ou plus** (ce qu'un agent voit en double).
- **4 132 groupes = même nom, prénoms différents** (3 696 par le même e-mail) → très probablement des **conjoints ou une famille,
  chacun sur sa fiche**. Ce ne sont PAS des doublons.
- **3 888 groupes = noms et prénoms différents, même e-mail** → adresse partagée (couple non marié, famille, société, notaire).
- **2 195 groupes = même prénom, noms différents** → nom de jeune fille ou nom mal saisi, non tranché.

**Le lien avec les couples, mesuré :**

1. **Les doublons ont multiplié les foyers automatiques.** Chaque fois que la même personne a été recréée, Hektor lui a refait un
   foyer : **9 232 premières de foyer en trop, qui portent 6 727 places de conjoint vides en trop**.
2. **La même personne existe une fois « en foyer » et une fois seule** dans 8 334 groupes. La civilité de la fiche en foyer :
   vide 4 801, M. 3 770, Mr./Mme 1 632, M_Mme 114 — encore le foyer automatique dans la majorité.
3. **Le vrai conjoint existe souvent déjà, sur une fiche à part** (les ~3 700 « même nom, même e-mail, prénom différent ») : c'est
   une bonne part de la catégorie 5 « conjoint possible ailleurs » (10 899 foyers).
4. **Le détecteur ne voit pas les fiches de couple** : 3 places de conjoint vides et 368 secondes nommées seulement dans ses
   groupes (il exige un prénom, ou un e-mail, ou un téléphone — les places vides et les noms recopiés n'en ont pas).

**Ce que ça change.** La règle d'affichage (A, B ou C) n'écrit rien : les doublons ne la changent pas. ⚠ Mais **« compléter le
conjoint » (décision 3) doit d'abord CHERCHER une fiche existante** (même e-mail, même nom) et la RELIER, sinon il fabriquera de
nouveaux doublons. Et un futur chantier « fusion de doublons » touchera les mêmes fiches que les couples : à ordonner avec Frédéric.

**Non mesuré** : la part de faux positifs dans « même personne » (homonymes au même lieu) ; un échantillon lu par une personne le
dirait. Scripts : `audit_doublons_couples*.py` (lecture seule, aucun nom affiché).
