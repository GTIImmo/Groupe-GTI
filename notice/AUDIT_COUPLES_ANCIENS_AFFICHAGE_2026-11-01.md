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
- **Les signes écrits par une PERSONNE existent, et ils sont fiables** : un conjoint nommé, une civilité de couple, deux prénoms
  dans la fiche. Ils couvrent **2 991 couples vivants sur 14 779 (20 %)**.
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

## 5. LES RÈGLES POSSIBLES, ET CE QU'ELLES AFFICHENT

**Règle A — « Couple » seulement si une personne l'a écrit** *(CONSEILLÉE)*
- « Couple » : catégories 1 à 4, **2 991 fiches**.
- Orange « conjoint à compléter » **sur la fiche seulement** (réponse 2 du 31/10, gardée) : quand le conjoint n'a pas de prénom ou
  n'existe pas, soit environ **2 690** des 2 991.
- Tout le reste (**11 788**, catégories 5, 6 et 7) : affiché comme **une personne seule**, comme aujourd'hui ; la seconde fiche vide
  reste masquée, comme aujourd'hui.
- Ce qu'elle rate : un vrai couple dont personne n'a rien écrit. Il le reste aujourd'hui de toute façon : l'écran n'aurait rien
  d'autre à montrer qu'une pastille orange vide.

**Règle B — « Couple » partout où Hektor a mis un foyer** *(la réponse 1 du 31/10, donnée avant cette mesure)*
- « Couple » sur les **14 779** ; orange sur ~12 900.
- Ce qu'elle casse : **9 278 fiches sans aucun signe** porteraient « Couple », la plupart pour une personne seule ; et l'étiquette
  ne voudrait plus rien dire pour les agents.

**Règle C — « Couple » seulement si le conjoint est nommé**
- « Couple » sur **1 909** (1 + 2).
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
- Les **archivés et les fiches hors de l'app** : les chiffres de la section 4 ne portent que sur les 14 779 couples vivants. Sur
  tout le registre, les proportions vont dans le même sens (section 2).
