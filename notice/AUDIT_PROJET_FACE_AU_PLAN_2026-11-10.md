# AUDIT DU PROJET FACE AU PLAN — ET LA LISTE DES ACTIONS JUSQU'À LA COUPURE — 10/11/2026

*Frédéric (10/11) : « un audit de mon projet par rapport au plan dev, ensuite redonne-moi les étapes 2, le passage à l'étape 3,
etc. ; je veux la liste, si possible, des actions ». Lecture seule. Sources : le plan maître
`notice/PLAN_DEV_ACTUALISE_2026-08-20.md` (charte, journal, dix lots, chantiers, 46 chapitres du 07/10), la liste
`notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (sections 12 et 13), `CLAUDE.md` §2, l'audit d'hier
`notice/AUDIT_FIN_ETAPE2_2026-11-09.md` (et ses mesures dans Supabase), les plans de la signature, du registre des mandats et
de la publicité, la mémoire du projet. Rien n'est codé, rien n'est écrit en base.*

> ⚠ **Ce qui n'est pas remesuré aujourd'hui** est écrit « non remesuré ». Les durées sont celles du plan du 07/10
> (fourchettes), **pas** une nouvelle estimation.

---

## 0. EN BREF

- **Les trois étapes** (Frédéric, 24/08 puis 08/10) :
  - **étape 1** : tout se fait dans Hektor ;
  - **étape 2** : les négociateurs travaillent dans l'app ; Hektor vit, il fournit les numéros, les workers lui envoient
    les mises à jour ; **il est interdit aux négociateurs d'ouvrir Hektor en même temps** ;
  - **étape 3** : notre registre électronique des mandats, puis la signature, puis la publicité, plus le site, le DNS et
    l'e-mail ; « tant que les trois ne sont pas chez nous, impossible de couper Hektor ». Puis la coupure.
- **Où on est vraiment** : **entre l'étape 1 et l'étape 2**. Le code de l'étape 2 est fait, mais personne d'autre que les
  admins ne travaille dans l'app (30 jours : 1 196 travaux, tous de 4 comptes admin ; 2 comptes commerciaux, 0 connexion).
- **L'étape 3 a déjà commencé, en avance** : la signature Youtrust (lots 1 à 5 codés), le registre des mandats (registre
  V3 en ligne), la publicité (lecture des passerelles réparée), le registre des négociateurs. C'est voulu pour ce qui a une
  date de péremption ; pour le reste, cela veut dire que **deux étapes avancent en même temps**.
- **Le chemin critique n'est pas technique** : c'est la mise en service auprès des négociateurs (étape 2), puis trois
  contrats et choix externes (signature, publicité, DNS).

---

## 1. L'AUDIT, LOT PAR LOT *(les dix lots du 20/09 et le lot L10 du 07/10)*

- **L0 — ne plus rien perdre** : ✅ fait le 20/09.
- **L1 — les numéros à la naissance** : 🟡. Le contact et l'annonce naissent avec notre numéro depuis le 21/09.
  **La recherche ne naît toujours pas dans l'app** (rouvert le 07/10, renvoyé à L10-2). Non remesuré depuis.
- **L2 — les corps chez l'app** : 🟡. Contacts, relations, couples, recherches : faits ; ⑧ a ajouté la nature des fiches,
  la nuit des contacts et les 31 533 contacts du registre (01 → 05/11). **Le corps de l'annonce est encore refait chaque
  nuit depuis le miroir** (26bis-3, décision du 13/10 : `CHAMPS_APP_ANNONCE` reste éteint jusqu'à la coupure).
- **L3 — la règle de récence par champ** : ✅ fait le 21/09.
- **L4-b′, L4-c, L4 — la création part de l'app** : ✅ pour le contact et l'annonce (C.9, 25/09) ; une personne = un
  numéro (bascule du 23/09). **C.9-couple** (le geste humain) n'a pas été remesuré ; **4.3** (contact + recherche + mandant
  d'un coup) non remesuré.
- **L5 — les gestes manquants** : ✅ par le chantier ⑦ (clos le 21/10). Deux gestes fermés par décision : modifier ou
  prolonger un mandat (18/10), renommer un document (19/10).
- **L6 — ce que Hektor fait remonter** : ✅ par le chantier ⑥ (14-16/10) pour les documents, les photos et les
  passerelles ; la publicité a été réparée le 04/11 (5 pages lues sur 80 depuis le 26/10).
- **L7 — les fichiers chez l'app** : 🟡. Les documents et photos redescendent et sont gardés (8f : un document retiré
  chez Hektor reste chez nous). Le rapatriement complet des binaires (D.1a, D.1, D.2) n'est pas remesuré ici.
- **L8 — exploitation et bascule** : ⬜ **c'est le lot qui manque**. Son critère de fin : « les négociateurs travaillent
  dans l'app ». **0 commercial en 30 jours.**
- **L9 — le registre électronique des mandats** : 🔧 commencé. La table `app_mandat` et sa sonde existent (A.3-technique,
  30/09) ; le registre V3 est en ligne (29/10) ; le registre des mandats de recherche a son étape 1 sur 5 (15/10). **La
  série propre, l'inaltérabilité, l'export, les 23 715 dates de clôture (C.13-c) et l'étude juridique restent à faire.**
  ⚠ La question « continuer la série PROTEXA ou repartir de 0 » n'est toujours pas au journal des décisions.
- **L10 — préparer la coupure** (16 tâches) : la plupart ⬜. Avancées partielles, venues d'autres chantiers :
  - L10-16 sécurité : ✅ (chantier ①) ;
  - L10-11 les négociateurs : 🔧 registre des négociateurs posé le 04/11 (restent la répartition et les droits) ;
  - L10-9 la sauvegarde : 🔧 copie complète du dimanche et registres dans la sauvegarde du jour (8c, 8d) ;
  - L10-3 les statuts chez nous : 🔧 chantier ③, mais l'interrupteur reste éteint ;
  - L10-12 visites et documents-modèles : ➡ 8e (notre bon de visite) rangé à l'étape 3.

## 2. LES HUIT CHANTIERS DE L'ÉTAPE 2 *(posés le 08/10)*

① sécurité ✅ · ② droits du négociateur ✅ (restes reportés par Frédéric) · ③ chez nous d'abord ✅ · ④ aucun échec
silencieux ✅ · ⑤ gestes cassés ✅ · ⑥ ce qui ne redescend pas ✅ · ⑦ gestes qui manquent ✅ · ⑧ gardé chez nous 🔧
(il ne reste que des décisions). Détail : l'audit d'hier, §3.

## 3. LES PIÈCES DE L'ÉTAPE 3 *(liste, section 12)*

- **A.3 — le registre des mandats** : voir L9 ci-dessus. Hors code : l'export PROTEXA, le juriste, l'horodatage tiers,
  l'arbitrage de la série.
- **A.2 — la signature (Youtrust)** : 🔧 bien avancée. Audit et lot 1 le 26/10 ; lots 2, 3, 4 et 4 bis codés le 26/10
  (lot 3 posé en base) ; lot 5 (recevoir les avis, rapatrier le signé, prévenir) codé le 05/11 et commité (`781110d`).
  **Tout est dormant** (interrupteur éteint, services pas redémarrés pour ça). ⚠ **L'essai gratuit finissait vers le
  09/11** : la preuve complète en sandbox (Frédéric signe 3 fois) **n'est pas vérifiée ici**. Restent les lots 6a
  (l'ergonomie), 6b (les écrans), 6 bis (la tablette), 7 (le filet de nuit), 8 (la production, après le contrat), et les
  décisions D5 (l'offre) et D12 (déposer le signé chez Hektor).
- **A.1 — la publicité (passerelles)** : 🟡. La **lecture** de l'état par portail est réparée (04/11). **Le flux à nous
  n'existe pas (0 ligne)** : il faut choisir un prestataire de diffusion (agrégateur) et reprendre les 346 annonces.
  Un plan de l'écran Annonces vue Publicité existe (03/11), rien codé.
- **A.4 — DNS, site, e-mail** : ⬜ hors code. La zone DNS est chez La Boîte Immo (elle porte la messagerie Google,
  les e-mails de l'app et le site www). Action : demander l'export complet de la zone, la recréer chez OVH, garder
  l'adresse de www tant que Hektor vit.
- **A.5 — les leads** : ⬜ hors code. Depuis le 01/02/2026, les demandes des portails ne s'écrivent plus dans les fiches.
  Canal actuel inconnu. Action : demander aux négociateurs où ils voient une demande LBC aujourd'hui.

## 4. LES CHANTIERS OUVERTS À CÔTÉ *(dans leurs propres sessions, non audités ici)*

- L'annuaire des partenaires (lots 4 à 7 allumés, la suite attend Frédéric).
- Le classeur et le suivi d'affaire (le gel A3 fait, A6 « créer les 188 transactions absentes » à faire, spécification de
  l'annulation du 09/11).
- Le registre des négociateurs (répartition, droits, 14 anciens).
- L'accueil assistant IA (plan validé le 29/10, étape 0 faite, rien codé).
- Matterport : la lecture de nuit passe par la console depuis le 04/11 (`9cfeace`) ; non remesuré ici.

---

## 5. ⭐ LA LISTE DES ACTIONS, DANS L'ORDRE

*Légende : **[F]** décision ou geste de Frédéric · **[C]** du code (audit → explication → « vas-y » → code → contrôle) ·
**[H]** hors code (un prestataire, un contrat, une personne) · **⏳** à faire tant que Hektor vit.*

### A. FINIR L'ÉTAPE 2 — d'abord réparer ce qui est ouvert

1. **[C]** Chercher pourquoi « modifier un mandant » a échoué 3 fois sur 3 le 05/11 (« Formulaire édition contact Hektor
   introuvable », fiches 115527 et 140142). Un négociateur tombera dessus dès le premier jour.
2. **[C]** Le journal du run perd les sorties Python des dernières étapes depuis le 05/11 : en trouver la cause.
3. **[C]** Les 4 essais automatiques du front en échec : mesurer s'ils échouaient déjà avant, puis les corriger.
4. **[C]** Remesurer deux corrections non revues : le balayage des documents (arrêt sur un refus 403) et la relecture
   d'un mandat saisi après coup (02/11).
5. **[C]** Remesurer la grille objet × geste du 08/10, case par case, pour avoir une liste exacte avant d'ouvrir l'app
   aux négociateurs.

### B. FINIR L'ÉTAPE 2 — les décisions qui restent

6. **[F]** Les décisions de ⑧ : les 9 388 personnes seules à deuxième place vide · les 680 coquilles · les doublons (T6) ·
   le RGPD de l'index global · les 633 fiches jamais migrées · les 121 241 fiches du compte « accueil » (question à poser à
   Hektor) · les 36 vendeurs + 20 acquéreurs sans notre numéro · les acheteurs d'avant le 17/07 (A / B / C) · les 4
   mandants à localité perdue.
7. **[F]** Les restes reportés du chantier ② : ce que voit exactement un agent commercial ; que peut faire un négociateur
   seul, que doit-il demander ?
8. **[F]** Les questions de fait du 07/10 : les négociateurs utilisent-ils les SMS, les tâches et rappels, l'envoi de
   fiches de Hektor ? Les automatismes du CRM (nouveau mandat, échéance, anniversaire) sont-ils allumés ? *(si oui, il
   faut les refaire dans l'app avant d'interdire Hektor)*

### C. LE PASSAGE À L'ÉTAPE 2 POUR DE VRAI — la mise en service *(lot L8, chapitres 9, 10 et 14 du 07/10)*

9. **[F]** Choisir les pilotes : 1 à 3 négociateurs, et la date.
10. **[C]** Préparer leurs comptes et leurs droits (les 2 comptes commerciaux existent, les autres négociateurs n'en ont
    pas ; le registre des négociateurs relie déjà une personne à son compte).
11. **[F]** Un essai réel d'un geste chez Hektor par un négociateur (reporté au chantier ②).
12. **[F]** Une courte formation, et la règle : **pendant le pilote, les pilotes n'ouvrent plus Hektor**.
13. **[C]** Le suivi du pilote, 2 à 4 semaines : chaque matin, les travaux en erreur et les gestes des pilotes (chaque
    geste retrouvé dans les travaux ou un carnet).
14. **[F]** Le bilan du pilote, puis **tous les négociateurs**. ➡ **C'est ici que l'étape 2 est finie.**

### D. CE QUI A UNE DATE DE PÉREMPTION ⏳ — en parallèle, tant que Hektor vit

15. **⏳ [F]** La signature : vérifier si la preuve complète en sandbox a été faite avant la fin de l'essai (~09/11) ;
    sinon, décider de l'abonnement Youtrust (D5) pour pouvoir la faire.
16. **⏳ [C]** C.13-c : rattraper les 23 715 dates de clôture des mandats (après avoir corrigé l'applicateur, qui choisit
    par annonce et non par mandat : 39 annonces ont plusieurs mandats).
17. **⏳ [C]** C.9-couple (le geste humain) et E.1 : ce qui ne vit que chez Hektor (recherches, visites, documents,
    signatures en cours) à capturer.
18. **⏳ [C]** Les photos masquées : le balayage vendus/clos puis archives (~45 nuits depuis le 03/11) doit aller au bout.
19. **⏳ [H]** A.4 : demander à La Boîte Immo l'export complet de la zone DNS **avant tout préavis**.
20. **⏳ [H]** A.3 : obtenir l'export PROTEXA.

### E. L'ÉTAPE 3 — dans l'ordre fixé par Frédéric : registre → signature → publicité

**E1. Le registre électronique des mandats (L9 / A.3)**
21. **[F]** Trancher : continuer la série PROTEXA ou repartir de 0 (à écrire au journal).
22. **[H]** Consulter un juriste (inaltérabilité, horodatage tiers, avenants et mandats de recherche dans la même série).
23. **[C]** Le registre lit nos tables et le mandat est complet (A.3-c, A.3-d) ; finir le registre des mandats de
    recherche (étapes 2 à 5).
24. **[C]** La série légale de nos numéros et l'avenant complet (A.3-e) ; puis l'inaltérabilité (A.3-f) et l'export.
25. **[C]** Le négociateur manquant sur 3 318 lignes du registre.
    ➡ **Fini quand** : un mandat neuf s'enregistre sans Hektor. La 1re des 3 exceptions tombe.

**E2. La signature en propre (A.2, Youtrust)**
26. **[F]** Signer le contrat Youtrust (offre D5) ; décider D12 (déposer le mandat signé chez Hektor tant qu'il vit).
27. **[C]** Lot 6a : l'ergonomie (vérifier que le gabarit de l'app couvre les modèles Hektor utilisés, et l'état de
    l'interrupteur Mandat V3 sur Vercel).
28. **[C]** Lots 6b et 6 bis : les écrans, la signature sur tablette.
29. **[C]** Lot 7 : le filet de nuit et la surveillance.
30. **[C]** Lot 8 : la production — d'abord Frédéric seul, puis tous ; solder les procédures ImmoSign en cours.
31. **[F]** Former les négociateurs à **rédiger** le mandat dans l'app (498 mandats sur 499 étaient rédigés dans Hektor).
    ➡ **Fini quand** : plus aucune signature ne passe par ImmoSign.

**E3. La publicité en propre (A.1)**
32. **[F]** Choisir le prestataire de diffusion (agrégateur) et signer.
33. **[C]** Notre flux d'annonces (0 ligne aujourd'hui), puis la reprise des 346 annonces diffusées, puis le retrait de
    l'API Hektor.
34. **[C]** L'écran Annonces vue Publicité (plan du 03/11, rien codé).
    ➡ **Fini quand** : une annonce part sur les portails sans Hektor.

**E4. Le reste de l'étape 3**
35. **[H]** A.4 : recréer la zone DNS chez OVH, basculer, décider où héberger le site public.
36. **[F] puis [C]** A.5 : les leads entrent dans l'app (d'abord savoir par où ils arrivent).
37. **[C]** Notre bon de visite et l'offre d'achat (8e, L10-12), avec la prise de rendez-vous.
38. **[C]** R5 : l'état d'une transaction chez nous (décision du 26/10).
39. **[C]** L'annuaire des négociateurs devient le nôtre, avec les agences et les menus (chapitre 26).
40. **[F]** Les questions du 07/10 encore ouvertes : le numéro de dossier EM/VA (continuer ou notre numéro) ; qui pose
    « diffusable » sans Hektor ; les suppressions et fusions de doublons (app ou admin seul) ; les 2 locations vivantes.

### F. PRÉPARER LA COUPURE *(L10, chapitres 17 à 46 du 07/10)*

41. **[C]** Le numéro Hektor devient facultatif partout (17 tables, 7 clés), puis les gestes et les transactions sans
    numéro Hektor (L10-1, 26bis-TRANSACTIONS).
42. **[C]** Créer sans Hektor : la recherche et les mandants naissent chez nous (L10-2).
43. **[C]** Le corps de l'annonce chez nous ; diffusable et baisse de prix sur nos valeurs (26bis-3, L10-4, L10-5).
44. **[C]** Une seule porte vers Hektor, dormante : l'interrupteur et l'ordre d'extinction (L10-6).
45. **[C]** Le run d'après, la sauvegarde d'après, la surveillance d'après (L10-7, L10-9, L10-10).
46. **[C]** Le côté public stable (liens RDV, vitrine, DPE : L10-15, 11bis).
47. **[F]** Ce que Hektor envoyait aux clients : à refaire ou non (L10-13).
48. **[C]** L'écran sans Hektor : retirer les liens « Ouvrir Hektor » (E.3).

### G. LA COUPURE

49. **[C]** La fenêtre finale : copie figée du miroir, derniers rattrapages (E.1, E.4a).
50. **[C] + [F]** Répétition complète sur une copie, une semaine sans Hektor, sans perte ni fausse alerte.
51. **[F]** Le jour J, puis la fin de l'abonnement Hektor.
52. **[C]** Après : purge du coffre des documents (G.3), l'état cloud qui suit l'annonce (G.4).

---

## 6. LE CALENDRIER *(non réestimé)*

- Le plan du 07/10 comptait 145 à 215 jours de code pour les 46 chapitres, avec un pilote vers la 2e quinzaine de
  novembre « si les décisions suivent » et **une coupure au plus tôt au printemps 2027**.
- Au 10/11, le pilote n'est pas ouvert (actions 9 à 14). Chaque semaine sans pilote décale la fin de l'étape 2 d'autant.
- La signature, elle, a pris de l'avance (lots 1 à 5 codés), mais son passage en production attend un contrat.

## 7. NON MESURÉ AUJOURD'HUI

- La grille objet × geste du 08/10, case par case (action 5).
- La preuve sandbox de la signature avant la fin de l'essai (action 15).
- Le volume de travail fait directement dans Hektor par les négociateurs.
- L'état réel des chapitres 15 à 46 dans le code : la liste ci-dessus suit le plan, pas une relecture du code.
