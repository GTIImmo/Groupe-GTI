# Porte d'entrée du projet

> Ce fichier ne contient **aucune connaissance**. Il contient des **adresses**.
> Le savoir est dans le plan, la liste, les notes et le code. En cas de désaccord,
> **c'est le code qui gagne, puis le plan, puis cette page.**
> Il se lit en trois minutes. Il ne remplace rien.

---

## 0. LA METHODE — *posee par Frederic le 20/09/2026, elle ne s'oublie jamais*

> **A chaque chapitre du plan, dans cet ordre, sans qu'il ait a le redemander :**
>
> 1. **AUDITER** le sujet — le code et la base d'abord, les notes ensuite. En cas de
>    desaccord, le code gagne.
> 2. **EXPLIQUER** clairement et simplement : ce que j'ai trouve, ce que je vais faire,
>    ce que ca touche, comment on revient en arriere, comment on verifiera.
>    ⚠ **Et TOUJOURS « ce que ca pourrait casser ailleurs »** *(Frederic, 08/10)* : avant de
>    corriger, controler que le correctif n'ecrase pas un RAISONNEMENT GLOBAL de l'app --
>    tous les appelants, les chemins de secours, les usages publics, les decisions ecrites.
> 3. **CODER**, en additif, derriere un interrupteur quand c'est possible.
> 4. **CONTROLER** : essais hors ligne, puis preuve en reel si necessaire. Dire aussi
>    ce qui a rate.
> 5. **METTRE A JOUR LE PLAN** : la case cochee AVEC sa mesure, la page de tete, le
>    journal des decisions, le commit qui porte l'identifiant de la tache.
> 6. **PASSER A L'ETAPE SUIVANTE** et recommencer.
>
> **LE FEU VERT, au cas par cas selon le risque** *(arbitrage du 20/09)* :
>
> | | |
> |---|---|
> | **J'enchaine sans attendre** | tache additive et reversible : code neuf dormant, lecture, mesure, audit, mise a jour des documents |
> | **J'attends le « vas-y »** | modification de code existant, du run de nuit, des workers |
> | **Accord OBLIGATOIRE, toujours** | ecriture en base de production · ecriture chez Hektor (creer / modifier / supprimer) · lancer un run ou un rattrapage · redemarrer un service · deployer · tout geste irreversible |
>
> ⚠ **UN AUDIT BALAIE LES OBJETS *ET* LES GESTES — regle posee par Frederic le 21/09**,
> apres un audit qui n'avait mesure QUE la modification d'une annonce et avait manque les
> 167 champs de la CREATION. « Tu vas trop vite dans tes audits, il faut les rendre plus
> approfondis. »
>
> **Avant de conclure quoi que ce soit, dresser le tableau, meme s'il est vide :**
>
> |  | creer | modifier | supprimer / archiver | lire / remonter |
> |---|---|---|---|---|
> | **annonce** | | | | |
> | **contact** | | | | |
> | **recherche** | | | | |
> | **relation** (mandant, proprietaire, acquereur) | | | | |
> | **transaction** (offre, compromis, vente) | | | | |
> | **mandat** | | | | |
> | **document / photo** | | | | |
> | **RDV / visite** | | | | |
>
> Une case qu'on ne sait pas remplir se DIT (« non mesure »), elle ne se saute pas. Et si
> l'audit ne porte que sur un objet, l'ecrire en tete : « audit limite a X, les autres ne
> sont pas mesures ».
>
> **Une seule tache en code a la fois.** Les audits peuvent tourner en parallele.
> **Chaque message de travail commence par une ligne de position** : `L0 · C.1' · 2 sur 4`.
> **Rien n'est fini tant que ce n'est pas ecrit dans les documents** : cette conversation
> sera resumee, les fichiers survivent.

---

## 1. Où tu es

Le dépôt est **`C:\Hektor\Projet`**. `C:\Hektor` n'est pas un dépôt git : si une commande
git répond *« not a git repository »*, tu es au mauvais endroit.

| | |
|---|---|
| front | `apps/hektor-v1/` — valider avec `npm run build`, **jamais** `tsc --noEmit` |
| worker | `Console/console_job_worker.js` |
| synchro | `phase2/` |
| API | `backend/` |
| tâches planifiées | `scheduled/` |
| documents de travail | `notice/` — 160 notes *(compté le 07/10)* |

---

## 2. Où on en est — *une page, pas une archive*

> ⚠ **Cette section porte LE PRÉSENT, et rien d'autre.** Règle : en fin de session, on la
> **RÉÉCRIT**, on ne l'empile pas ; ce qui en sort descend dans **`notice/JOURNAL_DE_BORD.md`**.

**Réécrit le 19/10/2026.** ⚠ Il pesait **79 966 caractères, 91 % du fichier** — « Ce qui attend
Frédéric » en faisait **47 % à lui seul**, rempli d'items déjà marqués ✅ FAIT. Tout est descendu
dans le journal de bord *(rien n'est perdu)*, et les **31 leçons** ont leur propre note :
**`notice/LECONS_DE_METHODE.md`**, numéros conservés. **Règle tenue pendant la réécriture : en cas
de doute sur un item, on le GARDE** — un item gardé coûte une ligne, un item perdu coûte une
décision.

### Les deux étapes — *définies par Frédéric le 08/10*

```
ETAPE 2   l'app fait tout le travail quotidien ; Hektor vit, il FOURNIT LES NUMEROS
          (y compris le n° de mandat via PROTEXA), les workers lui ENVOIENT les mises a jour
ETAPE 3   notre registre electronique des mandats (nos numeros) -> la signature -> la pub ;
          « tant que les 3 ne sont pas chez nous, impossible de couper Hektor » ;
          plus site web, DNS, e-mail
```

### Les 8 chantiers *(plan, section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 »)*

**La méthode, à chaque chantier** : **audit** → **explication** des correctifs, avec « ce que ça
pourrait casser ailleurs » → « vas-y » → code → **contrôle** → plan, liste et cette page à jour.
Prompt de reprise : **`notice/PROMPT_CHANTIER_ETAPE2.md`**.

| # | chantier | état |
|---|---|---|
| ① | sécurité : 136 fonctions ouvertes à la clé publique | ✅ **FINI le 08/10** |
| ② | les droits du négociateur *(`notice/CHANTIER_2_DROITS_NEGOCIATEUR_2026-10-09.md`)* | ✅ **FINI le 12/10** — 8 patchs, 1 déploiement. Restes **reportés par lui** *(voir « ce qui attend »)* |
| ③ | Hektor d'abord → chez nous d'abord *(`notice/CHANTIER_3_HEKTOR_DABORD_2026-10-12.md`)* | ✅ **FINI le 14/10**, éprouvé en réel sur 62774. ⛔ **L'interrupteur `CHAMPS_APP_ANNONCE` reste ÉTEINT** *(tranché le 13/10)* |
| ④ | aucun échec silencieux — 10 points *(`notice/CHANTIER_4_ECHECS_SILENCIEUX_2026-10-09.md`)* | ✅ **FINI le 11/10** · + **4j** le 13/10 *(23 battements partaient dans le vide)* |
| ⑤ | les gestes cassés *(`notice/CHANTIER_5_GESTES_CASSES_2026-10-08.md`)* | ✅ **FINI le 09/10** |
| ⑥ | ce qui ne redescend pas de Hektor *(`notice/CHANTIER_6_REDESCENTE_HEKTOR_2026-10-14.md` · liste : `D.0`, l. 974 · photos, section **10bis**, l. 1174)* | ✅ **TRAITÉ les 14-16/10** — les 9 points. 6e et l'historique des visites **sortis du chantier** *(sujets à part)* |
| ⑦ | **les gestes qui manquent** *(`notice/CHANTIER_7_GESTES_QUI_MANQUENT.md`)* | ✅ **CLOS le 21/10/2026** — **10 points finis, 2 fermés par décision** *(⑦-7 modifier/prolonger un mandat, ⑦-9 renommer un document)*. ⭐ **Trois réserves sont tombées le 21/10 par la MESURE, aucune par une décision nouvelle** · ⛔ **le dernier point ouvert — « les deux portes pour clôturer » — a été SORTI de ⑦ par Frédéric** : *« ce n'est pas du chapitre 7 »*, c'est un chantier à part avec sa propre spécification *(voir « LES DEUX PORTES » dans les chantiers à part)*. ⛔ **NE PAS ROUVRIR ⑦** |
| ⑧ | **gardé chez nous en entier** *(`notice/CHANTIER_8_GARDE_CHEZ_NOUS_2026-10-21.md` · audit transversal `notice/AUDIT_PORTES_DE_CREATION_2026-10-21.md`)* | 🔧 **OUVERT le 21/10** — 7 points (8a → 8g). ⭐ **Frédéric : « le but est d'anticiper la coupure »** → la méthode du 07/10 *(L10-2d, N.2 : « naître complet, Hektor complète »)* est **reprise dans ⑧**. **8a pièce 1 EN PRODUCTION** : un contact créé dans l'app a **ses 16 champs chez nous à la seconde** *(interrupteur `contact_nait_complet` **allumé** 15:37)*, prouvé en réel. ⚠⚠ **L'essai a trouvé un défaut dormant depuis le 23/09** : la relecture d'après-création fabriquait un **doublon** *(numéro Hektor au lieu du nôtre)* → **corrigé le 21/10 à 16:40** *(`refresh_contact_inproc.py` apprend la paire tout de suite ; 13/13 + essai réel)*. Doublon et contact d'essai **supprimés**. ⭐ **8a pièce 2 EN PRODUCTION (21/10, 23:47, interrupteur `annonce_nait_complete` allumé, gardé allumé par Frédéric le 22/10)** : une annonce créée dans l'app a **toute sa saisie chez nous à 1,3 s** (116 champs sur 116, essai réel 10000006 / 63330 par l'écran), elle est **visible en liste et sa fiche remplie AVANT le retour de Hektor**. Tableau des 173 champs : `notice/ESSAI_173_CHAMPS_ANNONCE_2026-10-22.md`. ⚠ **La relecture REMPLACE la fiche** : ce que Hektor ne rend pas (texte de l'étape 7, ~18 champs « console seule ») repart. ⚠ **Le bloc console n'existe chez nous que pour 103 annonces vivantes sur 13 497** — à trancher pour la coupure. ⭐ **8a pièce 3 EN PRODUCTION (22/10, interrupteur `annonce_saisie_gardee` allumé 07:03:47)** : la saisie de création **survit à la relecture** (table `app_annonce_saisie_naissance`, les champs « console seule » reposés sur la fiche), **verdict** champ par champ au retour, écarts **affichés** et **signalés** (sentinelle `data.annonce_naissance_ecart`). Essai réel 10000009 / 63331 : 118 champs gardés. ⭐⭐ **Il a trouvé un vrai défaut : la sauvegarde du SECTEUR chez Hektor remet la copropriété à NON / 0** (côté serveur Hektor, depuis une date entre le 05/08 et le 22/10) → **garde de la copropriété dans le worker, ACTIVE et prouvée en réel le 22/10 à 12:02** *(`Console/test_garde_copropriete.js` 16/16)*. Tout est **poussé** le 22/10. ⚠ Noté : le worker **s'arrête net** de temps en temps (`0xC0000409`, 42 fois depuis septembre) et laisse un travail « running » qui bloque l'annonce 30 min. ⭐ **Modification de contact (22/10) — A et B EN PRODUCTION, prouvés par l'écran** : **A** le commentaire s'écrit au clic (interrupteur `contact_commentaire_au_clic`) ; **B** le contrôle au retour (`contact_retour_controle`, table `app_contact_saisie_modif`, vue `app_v_contact_modif_ecarts`, sentinelle `data.contact_modif_ecart`) — il a attrapé une ville perdue (Firminy + 42000 → l'ANCIENNE ville du contact) — ⚠ *corrigé le 22/10 : ce n'est pas Hektor qui recalcule, c'est notre worker qui n'a pas trouvé les identifiants de commune et a envoyé le texte seul, que Hektor ignore*. ⏰ Mesurer la durée du push contacts à la 1ʳᵉ nuit. ⭐ **8a CLOS côté contrôle (22/10 après-midi)** : **1** (création de contact, `8a6`) et **2** (modification d'annonce, `8a7`, interrupteur `annonce_retour_controle`, sentinelle `data.annonce_modif_ecart`) **en production, prouvés par l'écran** — 1 a vu un contact créé **perdre ville et CP** (même cause : identifiants de commune non trouvés → texte seul ignoré). ⛔ **Et les portes du MANDANT n'envoient JAMAIS les identifiants** : toute localité de mandant est perdue chez Hektor depuis mai (603486, 604831, 604832, 605030). Les 4 gestes (annonce/contact × créer/modifier) ont maintenant **chez nous à l'instant + contrôle au retour**. ⏰ Mesurer la nuit (push contacts, détails d'annonces). ⭐ **C EN PRODUCTION (22/10 fin d'après-midi)** : les portes du **mandant** envoient enfin les identifiants de commune (C-1, prouvé : mandant d'essai 605947 garde Firminy/42700), un échec de résolution est **écrit au journal** (C-2), l'écran **propose les communes du code postal** et prévient sans bloquer (C-3, vu à l'écran). Les mandants déjà perdus (603486, 604831, 604832, 605030) **ne sont pas réparés** — rattrapage à décider. ➡ **Reste D** (*reporté par Frédéric*). ⭐ **ÉTAT AU 26/10 SOIR : voir la ligne ⑧ du plan** — 8b clos, registre des transactions (R1-R4, §46) et types de contact + table des parties **en production**, R5 à l'étape 3 ; **la suite : §58 point 5 (les boutons, §42), puis 6, puis 7**, ensuite 8c → 8g |

**Ordre de Frédéric : ① ⑤ ④ ② puis ③ → ⑥ → ⑦ ⑧.** ➡ **Le chantier en cours est ⑧** *(⑦ clos le 21/10)*.
⚠ Un périmètre, une taille, un ordre ou un report **ne se décident jamais sans lui**.

### 🔧 LE CHANTIER ⑦ — les 12 points, et ce qui reste

> Le détail vit dans **`notice/CHANTIER_7_GESTES_QUI_MANQUENT.md`** *(4 100 lignes, à jour)*.
> Ici : l'état, et **seulement ce qui reste**.

| # | le point | état |
|---|---|---|
| ⑦-1 | archiver / désarchiver un contact | ✅ **COMPLET** — base, worker et écran en production le 16/10, **et le geste prouvé par Frédéric le 16/10 dans les deux sens** *(3 jobs `done` : 07:29 reactivated, 07:56 archived, 08:14 reactivated, sur le contact 10059959 = Gladys DURIEUX)* · ✅ **ET LA QUESTION DU RISQUE EST TRANCHÉE le 21/10, sans écrire chez Hektor** : **OUI, archiver un contact archive AUSSI ses recherches** — sur 11 525 recherches, **0 recherche active sur 6 157 contacts archivés**, règle absolue · ⚠⚠ **et l'aller-retour n'est PAS symétrique : 163 contacts ACTIFS portent 184 recherches ARCHIVÉES** *(réactiver ne rend pas les recherches)* → ➡ **voir ① quater, c'est un sujet à part** |
| ⑦-2 | le cas Gladys DURIEUX | ✅ **RÉACTIVER réussi le 16/10 à 07:29** — et ses 2 recherches sont **inchangées** |
| ⑦-3a | clôturer un mandat à la main, le crayon, les droits | ✅ **les 4 pièces en production** *(la 2 poussée par l'autre session, `8676855`)* · ✅ **L'ÉCRAN A ÉTÉ VU le 21/10** — il se voit très bien, il n'est **pas** caché sous la jauge *(⚠ par le menu **Annonces**, pas « Mandats » qui est le registre)* · ✅ **L'ESSAI RÉEL EST FAIT le 21/10** — saisi 01/10/2026 un 21/10 sur 62774/18836, le carnet **et** le registre portent `2026-10-01` *(détail en ① bis)* · ⛔ **LE POINT DES « DEUX PORTES » A ÉTÉ SORTI DE ⑦ LE 21/10, PAR DÉCISION DE FRÉDÉRIC** — *« la demande et la modale changer statut Clos, ce n'est pas du chapitre 7 »*, **« on va laisser les choses comme aujourd'hui »**. Il a une spécification, et elle demande de retoucher les modales de validation de Pauline → **chantier à part, voir « LES DEUX PORTES » plus bas**. ⭐ *(Pour mémoire : j'avais levé cette réserve à tort le 21/10 — j'avais vérifié que le négociateur ne peut pas, alors que la consigne disait « MÊME EN ADMIN ». Mon propre essai de ⑦-3a l'a prouvée vraie.)* · ➡ **⑦-3a EST COMPLET** |
| ⑦-3b | l'écran du journal des suppressions | ✅ **écrit le 16/10** — Santé, admin strict, témoin inverse 128/0 |
| ⑦-3c | réordonner / choisir la photo principale | ✅ **TERMINÉ** — la **couverture** *(`7727f66`, 16/10)* **et réordonner** *(20/10 ; forme « A » choisie par Frédéric : un clic = un échange avec la voisine, pas de glisser-déposer, réversible)*. **Utilisés en production** : 63289 par Frédéric *(18 photos)*, 63299 par Pauline · **9 jobs, tous `done`, 0 erreur**, témoin inverse fait *(permutation **et** retour arrière sur 62774)* |
| ⑦-4 | le bandeau qui ment | ✅ **traité le 16/10** — ⚠ la production ne mentait pas, c'était le **mobile** sur les 527 brouillons |
| ⑦-5 | relancer / abandonner depuis le monitoring | ✅ **fait le 15/10** |
| ⑦-6 | « Abandonner » défait le geste | ✅ **fait le 15/10** |
| ⑦-7 | modifier ou prolonger un mandat | ⛔ **FERMÉ PAR DÉCISION le 18/10** — *« je ne souhaite pas pouvoir modifier un mandat ou prolonger »*. **Ne pas relancer** |
| ⑦-8 | **photos : rendre visible / masquer** | ✅ **COMPLET le 19/10** — les **4 marches**, dont le bouton **prouvé en réel deux fois** *(voir ci-dessous)* |
| ⑦-9 | renommer un document | ⛔ **FERMÉ PAR DÉCISION le 19/10** — *« je pense qu'il ne faut rien changer donc il faut que l'utilisateur puisse mettre un libellé au début donc rien à changer »*. ⭐ **Et le champ existe déjà** *(`App.tsx:11378` « Libellé », → nom du fichier envoyé à Hektor, `api.ts:8169`)*. **Ne pas relancer** |
| ⑦-10 | **les brouillons : rendre l'index vivant** | ✅ **① FAITE** · ✅ **② EN PRODUCTION** *(16:23, fiche ouverte sur 63131)* · ✅ **④ EN PRODUCTION le 20/10 à 19:02** — ⭐ **chaîne entière prouvée en réel : 63131 est passée du brouillon au catalogue « Actif » en 1 min 13 s, en gardant son numéro 7 589 119 et avec `diffusable 0`** · ✅ **④b ouvert aux négociateurs sur LEURS biens** *(prouvé sur pereira : il peut le sien, pas celui d'un autre, et toujours ni statut ni archivage)* · ✅ **③ FERMÉE PAR DÉCISION le 21/10** — *« A »* : **on ne lève pas la lecture seule**. ⚠ **Ce n'est pas un défaut, c'est le dessin** : `ro: true` sur le cran `brouillon` *(App.tsx:28633)*, et le bandeau dit déjà *« Activez-la pour pouvoir la travailler »*. ⭐ **Le chemin prévu est d'ACTIVER**, et il marche *(1 min 13 s, prouvé le 20/10 à 19:02)*. ⭐ Frédéric l'a vérifié lui-même sur **V670062775** *(brouillon `Estimation`, fiche complète bien chargée — la pièce ② a marché)* : modification impossible, **comme voulu**. ⛔ **NE PAS RELANCER.** ⭐ Le geste technique reste prouvé *(20/10, 62554, dans les deux sens)* si le jour venait — il ne manquerait que l'écran. ➡ **⑦-10 EST COMPLET.**

**⑦-8, les 4 marches** *(19/10)* :

| | |
|---|---|
| **1 — le verrou de publication** | ✅ **EN PRODUCTION**. `app_photos_remplir_adresses_app` exclut les masquées des **deux** boîtes *(couverture + galerie)*. Empreinte `682e3860` → **`b87f6c68`**, 7 contrôles verts. ⭐⭐ **L'idée des deux boîtes est de Frédéric**, et elle a rendu les pièces A et B inutiles. ⚠ **Le témoin inverse a prouvé qu'elle a servi le jour même** : sans elle, 3 masquées partaient le soir sur la vitrine, l'espace client et le portail |
| **2 — le balayage** | ✅ **écrit, éprouvé, la tâche est enregistrée** — `GTI Balayage Photos Masquees`, **00:00**, lot de **1 000/nuit**, **~14 nuits** pour les 13 491 vivantes. ⭐ Il **passe par le worker** *(un seul service, un seul frein)* : `Console/enqueue_photos_masquees_lot.js` + `scheduled/run_balayage_photos_masquees.ps1`. **Essai réel vert le 19/10** : 4 → 7 photos sur 62189, `hidden: 3` comme prédit |
| **3 — le run de mise à jour** | ⭐ **rien à écrire** : c'est **le même lot**, rempli « les modifiées d'abord, les jamais-vues ensuite ». Quand le balayage finira, il tombera à **~29/nuit** et deviendra le run de MAJ **tout seul** |
| **4 — le bouton masquer/afficher** | ✅ **EN PRODUCTION, PROUVÉ DEUX FOIS LE 19/10**. RPC `app_console_photo_visibilite_optimistic` → travail `set_hektor_photo_visibility` → `mode=vignette_visibilite&id=…&idann=…&visible=0|1`, et le handler **EXIGE le basculement** en relisant les deux galeries *(jamais un 200)*. ⭐ Essai sur le bac à sable **62774** : `masquees: 1`, boîte publique **4 → 3 en secondes**, 8 contrôles verts. ⭐⭐ Et le clic de Frédéric sur **63073** a **découvert 14 photos masquées** qu'on n'avait jamais eues — d'où le remède : le geste pose un `sync_hektor_photos` quand il découvre. ⚠ **Personne n'a encore VU le bouton à l'œil** *(3ᵉ pastille en haut à droite de chaque tuile)* |

### ⛔ Ce qui attend Frédéric

```
⓿ ✅ LA 1re NUIT DU BALAYAGE EST PASSEE (controle du 20/10 a 07:18, code 1).
   TOUTE LA NUIT EST EN CODE 0 : balayage 00:00 · recherches 03:00 · run 05:00 ·
   moniteur 05:48 · relances 07:00.
     ⭐⭐ LE VERROU TIENT, ET IL A ETE VRAIMENT EPROUVE : les masquees AVEC UN DERIVE
        (la vanne) sont passees de 3 a 129, et ZERO n'est sortie dans une boite
        publique.
     ⭐ LA RECOLTE EST 3,6x MA PREVISION : 126 masquees ramenees contre ~35
        annoncees -> 232 connues sur 25 annonces. Reste 12 492, soit 13 nuits.
     ⭐ LE RYTHME EST CELUI PREDIT : mediane 10,0 s (reference 10).
   ⚠ LE ROUGE EST UN FANTOME, prouve : la seule erreur est le travail orphelin du
     19/10 17:10, tue par le redemarrage des services et REPARE A LA MAIN le 19/10
     a 23:38. La reparation a tenu la nuit (63073 : 24 photos, 0 disparue, 0 sans
     fichier, 24 avec derive).
   ⚠ LA COMMANDE RESTE A RELANCER CHAQUE MATIN :
        python phase2/checks/controle_balayage_photos_masquees.py
     Sortie 0 = vert · 1 = un rouge · 2 = pas pu mesurer. Un refus sort en 1 EXPRES :
     code 3 « file non vide » (baisser -Limite), code 4 « >= 10 erreurs en 24 h »
     (Hektor nous rejette -> ne RIEN rejouer).

⓿ bis ⏰ CE SOIR APRES 21:00 -- LE JUGE DU VERROU 8 (photos masquees dans la journee).
   Lire le compte rendu de l'entretien photos, et y chercher :
        sauvees_par_le_verrou_8 : 2
        candidates_nommees      : ["62774/482253", "63073/485375"]
        photos_marquees         : 0        code de sortie : 0, AUCUN ecart
   ⛔ SI sauvees vaut 0 ET marquees vaut 2, LE VERROU N'A PAS MORDU -- regarder tout
     de suite : une photo masquee serait sortie du panneau, sans retour possible.

⓿ ter ✅ LE DOMAINE DES DOCUMENTS : POSE LE 20/10 A 20:30. RESTE A LE JUGER.
   LE DEFAUT : le numero d'un document est le sha1 de son ADRESSE COMPLETE, domaine
   compris (console_job_worker.js:1075). Le portail a demenage le 11/09 -> meme
   fichier, autre numero -> le worker cree un double et SUPPRIME l'ancienne fiche.
   ⚠⚠ LE DEFAUT ETAIT ECRIT LE 25/09 dans notice/AUDIT_RATTRAPAGE_DOCUMENTS_2026-09-25.md
     §5 reserve 2. La premiere vague est du 26/09, LE LENDEMAIN. Jamais traitee.
   L'AMPLEUR : 2 330 travaux, 15 403 fiches supprimees, 17 120 recreees ; 33 annonces
     ces 48 h ; restent 28 363 fiches / 6 199 annonces a l'ancien domaine.
   ⚠⚠ ET 17 118 FICHIERS RETELECHARGES CHEZ HEKTOR (781 ces 48 h) -- contre un
     quota de VOLUME, avec un bannissement d'IP a notre historique (19-20/08).
   ⭐ AUCUN DOCUMENT N'EST PERDU : 17 148 des 17 150 portent leur fichier, 0 annonce
     n'a tout perdu, 207 fiches signees intactes. Ce qui est perdu = l'identifiant de
     l'app, et 7,4 Go de DOUBLONS dans le coffre (du menage, pas une recuperation).
   LE CORRECTIF, ACTIF DEPUIS 20:30 -- il n'ecrit RIEN en base de son propre chef :
     A reconcilierParChemin() RE-CLE la fiche existante par un PATCH avant l'upsert,
       quand le CHEMIN est le meme sous un autre numero. Le chemin est une cle
       PARFAITE : 192 592 fiches, 0 collision, des deux cotes du demenagement.
     B pruneDeletedDocuments a deux garde-fous : NIVEAU 1 EXACT (ne jamais supprimer
       une fiche dont le chemin est dans la liste qu'on vient de lire) et NIVEAU 2
       chiffre (>= 2 ET >= la moitie -> refus ecrit au journal).
     ⭐ PAS DE MIGRATION DE MASSE : une fiche ne s'abime qu'au MOMENT de la synchro,
       donc chaque annonce se repare d'elle-meme a son prochain passage.
   ✅ LES 2 GESTES SONT FAITS : pousse (c82d973 est le sommet de origin/main) et
     LES 4 SERVICES ont redemarre a 20:30:46-47, file vide (0 pending, 0 running).
     ⚠ Le PREMIER redemarrage etait alle sur Admin, pas Documents : seule la mesure
       l'a vu (journal d'admin coupe a 20:16:41, celui de documents intact). On exige
       LA PREUVE DU SUCCES, jamais l'absence d'erreur.
     ⭐ Ce redemarrage general solde la note « 3 services sur 4 sur du code ancien ».
   ⏰ IL RESTE A LE JUGER -- UNE COMMANDE, apres le balayage de la nuit :
        python phase2/checks/controle_domaine_documents.py
     7 points, sortie 0 vert / 1 un rouge / 2 pas pu mesurer. ⭐⭐ LE TEMOIN : une fiche
     RE-CLEE garde sa date de naissance, une fiche RECREEE en porte une neuve. Avant la
     pose : 716 sur 164 229 (0,4 %) seulement avaient survecu -- donc 163 513 avaient ete
     RECREEES. Ce 716 doit MONTER, et il ne peut que monter.
   ⭐⭐ AUCUN RISQUE A PRENDRE POUR L'EPROUVER : la resynchro est posee par un SCRIPT qui
     repasse chaque nuit (41 231 travaux depuis le 25/09 a 12:57, ~330 par nuit). Le
     correctif sera donc exerce tout seul. ⚠ Et c'est la REPONSE a la reserve 3 du 25/09 :
     le rattrapage a ete lance LE JOUR MEME ou la reserve disait « a traiter AVANT ».
   ✅ LES SIGNATURES SONT INTACTES -- MESURE LE 21/10, et j'avais dit le contraire :
     428 des 429 documents signes ont leur DOSSIER DE PREUVES SUR LE SERVEUR (les 32
     fiches recreees par le bug : 32 sur 32). Le seul absent est l'annonce 24113,
     procedure 556, et sa fiche n'a JAMAIS ete recreee -- aucun rapport avec le bug.
     ⛔ MES DEUX FAUTES : j'ai cherche « preuves-*.zip » et obtenu 0 alors que
       safeFilename remplace le / (le fichier est « immosign_preuves-33.zip ») ; et
       j'ai mesure l'absence AU COFFRE alors que le projet garde tout SUR LE SERVEUR
       et ne met au coffre qu'une copie POUR LES BIENS VIVANTS (shouldKeepCloud).
     ⭐ Au passage, deux choses eprouvees pour de vrai : ImmoSign sert encore les
       vieilles procedures (essai sur la 33, vrai ZIP, 3 pistes d'audit), et la
       synchro documents accepte un bien vendu ou archive.
     ⛔ NE PAS POSER DE TRAVAUX DE RECUPERATION : il n'y a rien a recuperer.
   ✅ L'ANNONCE 59578 EST DEDOUBLONNEE (21/10) : 35 fiches pour 18 documents -> 18.
     Les 17 neuves retirees, les 17 anciennes gardees AVEC LEUR DATE DU 17 AOUT
     (« un numero ne se perd jamais »). 9 controles verts des DEUX cotes : la
     repetition collee par Frederic et ma propre mesure independante disent la meme
     chose, temoin inverse compris (192 637 documents hors 59578).
     Sauvegarde datee : app_console_document_avant_dedoublonnage_59578_20261021.
     ⚠ IL FALLAIT UN GESTE EXPRES : mon propre verrou n° 1 les rendait permanents
       (il refuse de supprimer une fiche dont le chemin est dans la liste lue).
     ⭐ Les 17 neuves etaient nees le 20/10 a 12:22, HUIT HEURES AVANT la pose de
       20:30:47 : les dernieres victimes, pas une fuite. Zero doublon apres.
     ⏰ A VOIR AU PROCHAIN BALAYAGE : le correctif doit RE-CLER les 17 anciennes par
       leur chemin -> le temoin du controle doit monter de 17.
     ⚠ +17 fichiers orphelins au coffre (34 Mo) : ils rejoignent le menage des 7,2 Go.
     Patch, inverse et repetition : supabase/patch_dedoublonnage_59578_2026-10-21*.sql
   ⚠ NON MESURE, et je ne le suppose pas :
     si les PHOTOS ont le meme defaut (leur id vient du CDN) ; ce qui declenche la
     resynchro d'une annonce (reserve 3 du 25/09, toujours ouverte).
   ⚠ COORDINATION : une conversation a ete ouverte sur ce chantier avec
     notice/PROMPT_CHANTIER_DOMAINE_DOCUMENTS_2026-10-20.md. Ces correctifs sont SES
     pieces A et C, dans l'ordre INVERSE, et sa migration devient optionnelle.
   ✅ LE MENAGE DU COFFRE EST FAIT -- LOT 1 (21/10, 07:21-07:42) : 4 075 fichiers
     retires, LE COFFRE PASSE DE 42,057 A 36,816 Go -> 5,24 Go LIBERES.
     4 controles verts a l'unite : orphelins 1 016 (= 5 091 - 4 075) · ⭐⭐ ZERO
     document vivant sans son fichier (sur 24 120) · ⭐⭐ 388 ZIP de preuves de
     signature INCHANGES · 26 427 fichiers (= 30 402 - 3 975).
     ⭐ Chaque fichier supprime avait sa jumelle SUR LE SERVEUR, par construction :
       la liste est deduite du disque (phase2/checks/fabriquer_liste_menage_coffre.py).
     ⭐ Le script a QUATRE garde-fous, et le 4e REFUSE de tourner pendant le run.
       Console/menage_coffre_documents.js -- EN BLANC par defaut.
     ⚠ DEUX de mes gardes ont MENTI a l'epreuve, et seul un TEMOIN POSITIF les a
       attrapees : (a) le garde-fou anti-run lisait le texte FRANCAIS de schtasks et
       disait « ne tourne pas » pendant que le run tournait ; (b) un objet absent fait
       un HTTP 400 dont le CORPS dit 404/NoSuchKey, donc « deja absent » comptait comme
       une ERREUR (d'ou les 100 du compte rendu : ce sont les 100 du 1er passage).
     ⏰ LA MINUTERIE DURE A SERVI : coupure a 07:42:44, DEUX MINUTES avant la descente.
     ⛔ RESTE LE LOT 2 : 988 fichiers, 1,6 Go, A TRANCHER PAR LUI -- leur appartenance
       ne tient que sur une comparaison de COMPTES par annonce, pas fichier par fichier.
       Plus 28 orphelins non expliques, ecartes volontairement.
     Tout est dans notice/AUDIT_MENAGE_COFFRE_DOCUMENTS_2026-10-21.md.
   ✅ LE MENAGE EST FINI, LES DEUX LOTS (21/10) : 5 062 fichiers retires, le coffre
     passe de 42,057 a 35,254 Go -> 6,80 Go LIBERES. Restent 29 orphelins (les 28
     non expliques + 1). Zero document vivant sans son fichier, 388 ZIP de preuves
     INCHANGES, 1 205 compagnons INCHANGES.
     ⭐⭐⭐ ET LE LOT 2 A PROUVE LA CONCEPTION : 377 refuses, dont 365 « SA FICHE EST
       VIVANTE ». Entre la fabrication de la liste et la suppression, LE CORRECTIF A
       RE-CLE DES FICHES : leurs dossiers sont redevenus vivants et le garde-fou les a
       protegees. Sans la reverification a la volee, 365 fichiers de fiches VIVANTES
       auraient ete supprimes. C'est pour ca que le script ne croit pas une liste gelee.

   ⛔⛔ DECISION DU 21/10 -- PAS DE REMEDE SUR LA CLE. NE PAS RELANCER.
     La question de Frederic : « si Hektor ne change pas, pas besoin de remede ? ».
     J'ai cherche l'argument contraire et je ne l'ai pas trouve. LES TROIS MESURES :
     1. LE RISQUE EST BIEN LIMITE A L'HOTE. Sur toute l'histoire de la base (mai ->
        octobre), le CHEMIN et le FLAG n'ont JAMAIS bouge : une seule forme
        (/admin/documents/biens/<annonce>/<fichier>?flag=lbiDocumentsSecure), deux
        hotes. 162 876 fiches sur le neuf, 27 944 sur l'ancien. Je craignais que le
        flag ou le chemin puissent changer aussi : ce n'est jamais arrive.
     2. LES 28 343 ADRESSES MORTES NE FONT MAL A PERSONNE. L'ecran ouvre un document
        par storage_path, JAMAIS par l'adresse Hektor (verifie : 2 appels dans tout le
        front, les deux par storage_path, zero usage de console_url pour ouvrir). Et le
        verrou n° 1 compare les CHEMINS sans l'hote, donc il les protege. Une adresse
        morte DORT, elle ne casse rien.
     3. ET SI HEKTOR REDEMENAGEAIT, LE CORRECTIF ABSORBERAIT LE COUP -- c'est exactement
        pour ca qu'il existe. On ne reperdrait RIEN ; on repasserait par la reparation.
     ⚠ CE QUE LA MESURE A TROUVE, et qui ne change pas la decision : la reparation est
       LENTE -- +20 fiches en ~12 h sur 70 travaux, pour 28 343 restantes (6 209
       annonces). A ce rythme il faudrait des annees. Mais comme elle ne protege de rien
       d'urgent, ce n'est pas un probleme : c'est juste lent, et chaque annonce se repare
       gratuitement a son prochain passage.
     ⭐ LE REMEDE, SI ON LE FAISAIT UN JOUR, est connu et mesure : prendre
       hektor_uploaded_document_id (le numero que HEKTOR donne, lu 3 lignes au-dessus
       de la cle dans extractDocumentEntries) -- 190 840 fiches, 0 collision, et 17/17
       inchange au demenagement -- AVEC le hache de l'adresse en REPLI (il manque sur
       0,9 % des cas). Changer la cle = toucher au coeur de la synchro des documents.
     ⛔ CONCLUSION : CAUSE RACINE COLMATEE, DELIBEREMENT. Ce n'est PAS un oubli.

   ⚠⚠ IL RESTE UNE SEULE CHOSE NON CORRIGEE, ET ELLE EST D'UNE AUTRE NATURE :
     LA RESERVE 3 DU 25/09 -- le balayage nocturne des documents n'a NI CADENCE NI
     ARRET SUR UN REFUS 403, et notre IP a deja ete bannie les 19-20/08. Ce n'est pas
     une assurance contre un evenement rare : c'est un RISQUE ACTIF CHAQUE NUIT.
     Rien n'a ete decide -- a reprendre S'IL LE DEMANDE.
   Tout est dans notice/AUDIT_DOMAINE_DOCUMENTS_2026-10-20.md.

① ✅ LA PIECE ④ (SORTIR DU BROUILLON) EST POSEE ET EPROUVEE (20/10 19:02) --
   63131 est passee du brouillon au catalogue en 1 min 13 s, en gardant son numero
   7 589 119, avec diffusable 0. Les 5 gestes ci-dessous sont FAITS :
   1. COLLER supabase/patch_chantier7_piece4_sortir_du_brouillon_2026-10-20.sql
   2. COLLER ..._REPETITION.sql  -> les 6 controles verts
   3. POUSSER : git -C C:/Hektor/Projet push
   4. ⏰ REDEMARRER HektorConsoleWorkerAdmin (c'est LUI qui porte ce type),
      et SEULEMENT file vide : 0 pending ET 0 running.
   5. EPROUVER en reel sur une cible que Frederic choisit.
   ⛔ EN CAS DE PROBLEME : ..._INVERSE.sql (il solde d'abord les travaux pending).
   ⭐ etatAnnonce=1 n'est PAS neuf : c'est la commande d'activation de chaque
     annonce que nous creons (createHektorAnnonceWithHttpDirect) -- eprouve.

① bis ✅ LA PIECE ② DES BROUILLONS EST POSEE ET EPROUVEE (20/10 16:23).
   Patch colle, pousse, worker DOCUMENTS redemarre a 15:32:35 (prouve : code
   ecrit a 14:50:32). Clic reel sur 63131 -> travail done en 8 s, cache de
   89 876 octets, app_brouillon_id 7 589 119, peremption +24 h, et le
   chevauchement parc ∩ brouillon est RESTE A 1 (la garde de la piece ① tient).
   ⛔ RESTE : PERSONNE N'A VU LA FICHE S'OUVRIR (bouton « Ouvrir la fiche
     complete », puis la fiche EN LECTURE SEULE -- option A).
   ⚠ Et les 3 AUTRES services worker tournent encore sur le code du 14:15 : sans
     consequence (seul DOCUMENTS reclame ce type), mais leur loadDossier ignore
     encore la 4e branche. A reprendre au prochain redemarrage general.

   1. COLLER supabase/patch_chantier7_piece2_detail_brouillon_2026-10-20.sql
      (3 verrous + les droits ; chaque bloc verifie son empreinte et S'ARRETE
       si quelqu'un est passe avant)
   2. COLLER ..._REPETITION.sql -- les 9 controles doivent etre verts, dont
      « un negociateur voit SES brouillons, et seulement les siens »
   3. POUSSER : git -C C:/Hektor/Projet push
   4. ⏰ REDEMARRER HektorConsoleWorkerDocuments, ET SEULEMENT FILE VIDE :
        0 pending ET 0 running (le 19/10 a 17:10 un redemarrage a tue 14 photos)
        powershell -Command "Restart-Service HektorConsoleWorkerDocuments; Get-Service HektorConsoleWorker*"
   5. EPROUVER en reel sur 63131 (brouillon propre, deja eprouve en dry-run).
   ⛔ EN CAS DE PROBLEME : ..._INVERSE.sql (il verifie qu'aucune trace ne reste
      ET que les deux familles soeurs sont intactes).

① bis LES ESSAIS REELS DU CHANTIER ⑦ -- AUDIT DU 21/10 : PRESQUE TOUS DEJA FAITS.
   ⭐ LECON : cette liste etait fausse sur QUATRE points. Frederic a dit « je crois
   que certains tests ont deja ete faits » -- il avait raison. AVANT d'ecrire un
   essai a faire, MESURER app_console_job : requested_by dit QUI, result_json dit QUOI.
   · ⑦-1 ARCHIVER un contact : ✅ LE GESTE EST FAIT ET PROUVE le 16/10 PAR LUI --
     3 jobs `archive_hektor_contact` tous `done`, et le TEMOIN INVERSE y est :
     07:29 reactivated, 07:56 archived, 08:14 reactivated, Hektor repondant chaque
     fois « Modification archivage ok ».
     ✅ ET LA QUESTION DU RISQUE EST TRANCHEE LE 21/10, SANS ECRIRE CHEZ HEKTOR :
       OUI, archiver un contact archive AUSSI ses recherches (0 recherche active
       sur 6 157 contacts archives). ⚠ Et le retour n'est pas symetrique -> ① quater.
       ⑦-1 EST DONC COMPLET.
   · ⑦-3a CLOTURER avec une date DIFFERENTE d'aujourd'hui : ✅ PROUVE LE 21/10 sur
     62774 / mandat 18836, par moi dans le Chrome de Frederic, avec son accord.
     Saisi 01/10/2026 un 21/10 -> le carnet porte `2026-10-01`. Le compte rendu du
     worker le confirme de bout en bout : `cloture_locale.date_cloture = 2026-10-01`,
     `magasin_lignes_ecrites: 1`, `registre_lignes_rafraichies: 1` (la piece 4 joue).
     ⭐ ET LA DATE NE PART PAS CHEZ HEKTOR : `closure: {reason:
       "cloture_locale_uniquement", status: "skipped"}`. Seul le STATUT y va, et il
       est VERIFIE (`verifie: true`, `statut_hektor_apres: "6"`). Le texte de la
       modale (« la cloture d'un mandat est definitive cote Hektor ») est donc a
       nuancer : c'est le statut qui est definitif, pas la date.
     ⚠ EFFET DE BORD QUE LA MODALE N'ANNONCE PAS : la charge portait aussi
       `offre_state: refused` et `compromis_state: cancelled` -- la cloture a refuse
       l'offre 33027 et annule le compromis 50048 du bien.
   · ⑦-3a L'ECRAN : ✅ VU LE 21/10, et il se voit tres bien -- il n'est PAS cache
     sous la jauge. Fil « VIE DU MANDAT », parcours en 6 etapes, bloc « Mandat clos »
     et bandeau ambre « lecture seule, reactivez le mandat ». ⚠ Et c'est le menu
     « Annonces » qu'il faut prendre, pas « Mandats » (= le registre) : la memoire
     « l'ecran mandats EST le menu Annonces » a mordu une fois de plus.
   · ⑦-8 marche 4 : ✅ FAIT ET PROUVE le 19/10, ET LE BOUTON A ETE VU : PAULINE
     l'a utilise en production le 20/10 a 11:56 sur 63289, dans LES DEUX SENS a
     2 secondes d'intervalle (17 visibles -> 18), `boite_publique` suivant (79->78).
     La reserve « personne n'a vu le bouton » tombe.

① ter ⚠⚠ TROUVAILLE DU 21/10, NOTEE, PAS TRAITEE -- LE WORKER EFFACE L'AUTEUR.
   `app_mandat_champ_app.ecrit_par` valait `frederic.gerphagnon@...` sur la ligne
   du 14/10, et vaut NULL apres mon essai du 21/10 -- alors que le geste venait de
   l'app, dans sa session, avec son jeton. Cause : DEUX chemins ecrivent ce carnet,
   et un seul retient l'auteur. Le RPC `app_set_mandat_cloture_optimistic` ecrit
   `ecrit_par` ; le WORKER, lui, fait sa `cloture_locale` sans utilisateur et
   ECRASE la trace de l'humain. ⭐ Ca explique aussi la ligne de 24933 (ecrit_par
   vide) que j'allais prendre pour un script. ⬜ A decider : le worker doit-il
   reporter l'auteur de la ligne d'origine plutot que de l'effacer ?

① quater ⚠⚠ 21/10 -- ARCHIVER UN CONTACT ARCHIVE SES RECHERCHES, ET LE RETOUR
   N'EST PAS SYMETRIQUE. C'etait LA question ouverte de ⑦-1, et elle se mesurait
   en base, sans ecrire une seule fois chez Hektor.
   Sur les 11 525 recherches de `app_contact_search_current`, jointes aux contacts :
     contact actif   + recherche active    : 4 203 recherches / 3 983 contacts
     contact actif   + recherche ARCHIVEE  :   184 recherches /   163 contacts
     contact ARCHIVE + recherche ARCHIVEE  : 7 138 recherches / 6 157 contacts
     contact ARCHIVE + recherche active    :       0          ⭐ AUCUNE, regle absolue
   ⭐ ZERO sur 6 157 contacts : archiver propage aux recherches. Reponse OUI.
   ⚠⚠ MAIS LA LIGNE DU MILIEU EST LE VRAI SUJET : 163 contacts ACTIFS portent des
     recherches ARCHIVEES -- donc REACTIVER NE REND PAS les recherches. Gladys
     DURIEUX (10059959) en est l'exemple vivant : reactivee le 16/10 a 08:14, sa
     recherche index 0 est restee `archive: true`, l'index 1 est active.
   ⭐⭐ ET L'IMPACT SE CHIFFRE : 150 contacts ACTIFS n'ont QUE des recherches
     archivees -- 150 acquereurs vivants dans le fichier sans une seule recherche
     active. ⚠ NE PAS SUR-CONCLURE : beaucoup peuvent avoir abandonne leur projet
     et leur recherche avoir ete archivee expres. Le chiffre dit l'ampleur a
     regarder, pas le nombre de victimes.
   ⛔ CE QUI N'EST PAS PROUVE : que notre geste du 16/10 soit la cause pour Gladys.
     Sans photo d'avant, je ne peux pas distinguer « notre archivage a casse sa
     recherche » de « elle etait deja archivee ». La note du 16/10 disait « ses
     2 recherches sont inchangees », ce qui est ambigu. ⭐ La REGLE, elle, est sure.
   ⬜ A DECIDER : faut-il que REACTIVER un contact propose de reactiver aussi ses
     recherches ? Et faut-il regarder les 150 ? C'est un sujet A PART, pas ⑦.

① quinquies 📜 « LES DEUX PORTES » -- SORTI DU CHANTIER ⑦ LE 21/10 PAR FREDERIC.
   ⛔ ON LAISSE LES CHOSES COMME AUJOURD'HUI. NE PAS RELANCER DANS ⑦.

   LE CONSTAT (mesure du 21/10) : il y a DEUX portes pour cloturer un mandat.
     ① fiche mandat du registre -> passe TOUJOURS par la demande d'annulation,
       ADMIN COMPRIS, et l'ecran le DIT : « Clôturer passe toujours par une
       demande, meme pour toi : c'est ce qui en garde la trace » (App.tsx:25637,
       2e consigne de Frederic du 16/10) ;
     ② modale de statut (Annonces -> « Faire evoluer le statut » -> « Clos »)
       -> clot DIRECTEMENT, sans aucune demande.
   ⭐⭐ PROUVE EN REEL le 21/10 : mon essai de ⑦-3a a clos le mandat 18836 de
     62774 par la porte ②, en admin, sans demande. Je demontrais le defaut sans
     le voir.

   SA SPECIFICATION, DANS SES MOTS (21/10) : « il faut que les renseignements
   saisis sur la modale changer statut "clos" soient RECUPERES dans la demande
   d'annulation afin que Pauline ait JUSTE A VALIDER OU REFUSER, et a ce moment
   le job est accepte -- ce qui evite de tout refaire. Donc il faut AMELIORER LES
   MODALES DE VALIDATION DE PAULINE, et cela est encore un autre chantier. »

   ⭐ POURQUOI IL NE VEUT PAS DU SIMPLE RENVOI : aligner la porte ② sur la ① sans
     rien d'autre ferait saisir DEUX FOIS (date, motif, raison a la demande, puis
     de nouveau a l'acceptation) et ajouterait UN GESTE A CHAQUE CLOTURE, admin
     compris. Son dessin supprime la double saisie au lieu de l'imposer.

   CE QUE L'AUDIT A DEJA ETABLI, pour le jour ou ce chantier s'ouvrira :
     . l'acceptation fait DEJA tout le travail : elle decoche Valide + Diffuse
       chez Hektor, PUIS cree le meme job change_hektor_annonce_status avec
       targetStatus 'closed' et `closeDate` (chainage « A5 » du 30/07,
       App.tsx:17834) -- le commentaire nomme Pauline : « LA DATE QUE PAULINE
       VIENT DE FIXER » ;
     . la demande n'a PAS de destinataire : app_diffusion_request porte
       requested_by / processed_by / request_status, c'est une FILE que les
       admins traitent (Pauline EST admin, verifie) ;
     . ⚠ LE CIRCUIT DORT : 4 demandes d'annulation en tout, toutes du 13-14/05,
       demandees ET traitees par Frederic pour des essais. Pauline n'a JAMAIS
       traite une demande. Le rouvrir, c'est le remettre a l'epreuve.
     . ⚠ NE TOUCHER QUE LA BRANCHE « Clos » : la meme modale porte Actif / Offre
       / Compromis / VENDU, et « Vendu » clot sur la DATE DE VENTE, volontairement.
     . ⚠ la demande exige un app_dossier_id -> les 38 mandats de recherche
       (ni annonce ni dossier) ne peuvent pas passer par elle.

② A TRANCHER PAR LUI -- je n'ai rien choisi :
   · ✅ LE REDEMARRAGE DU SERVICE DOCUMENTS (⑦-3c piece 4) EST FAIT -- PLUS RIEN A
     TRANCHER ICI. Les 4 services ont demarre le 20/10 a 20:30:46-47 pour le
     correctif des documents, soit 4 jours APRES le code de `reorder_hektor_photos`
     (`7727f66`, 16/10 15:14:21) : le service tourne donc avec. Mesure du 21/10 par
     l'HEURE DES PROCESSUS (`Win32_Process.CreationDate`), pas par la croyance.
     La vitrine suit donc en quelques secondes, comme voulu.
     ⚠⚠ MAIS CE REDEMARRAGE NE REGLAIT PAS LE MOT, et cette note l'a cru a tort :
       « le journal dit couverture pour un reordonnancement » venait d'un LIBELLE
       FIGE DANS LE CODE (`JOB_LIBELLES`, console_job_worker.js l. 18794), ecrit le
       16/10 quand seule la couverture existait. Aucun redemarrage ne change une
       chaine de caracteres. Corrige le 21/10 sur la forme deja tranchee pour ⑦-1
       (« L'archivage (ou la reactivation) du contact ») -- et ce libelle ne sert
       qu'a la notification d'ECHEC, un seul lecteur, jamais compare (l. 18833).
     ⛔ POUR TOUT PROCHAIN REDEMARRAGE, LE CRITERE RESTE : 0 pending ET 0 running.
       Le 19/10 a 17:10 un redemarrage a tue le travail du clic de Frederic
       (14 photos perdues, annonce 63073 ecartee du balayage A VIE).
         powershell -Command "Restart-Service HektorConsoleWorkerDocuments; Get-Service HektorConsoleWorker*"
   · ⭐ LE PLAFOND DU BALAYAGE : 1 000 ou 903 ? Mesure de la 1re nuit (20/10) --
     mediane 10,0 s mais la plus lente a pris 307 s, donc seules 903 annonces
     tiennent dans la fenetre de 2 h 30. Les 1 000 sont passees, SANS MARGE.
     Le plafond vit dans scheduled/run_balayage_photos_masquees.ps1 (-Limite).
   · ⚠ L'EXCLUSION POUR ERREUR DU BALAYAGE EST A VIE, et elle ne devrait pas
     l'etre (enqueue_photos_masquees_lot.js:231, AUCUN filtre de date -- alors que
     le frein global l. 198 regarde 24 h : asymetrie dans un seul fichier).
     Mesure du 20/10 : UNE SEULE annonce ecartee a vie, 63073, et sa cause est
     NOTRE PROPRE REDEMARRAGE, pas un refus de Hektor. Zero ecartee pour un vrai
     refus. Ca grossira sans bruit : chaque redemarrage pendant un balayage en
     ecarte une de plus, pour toujours.
     A -- une FENETRE DE DATE (7 jours), deux mots, le patron est 12 lignes plus
          haut, et une fenetre protege AUSSI du bannissement.   <- RECOMMANDE
     B -- trier par CAUSE : n'ecarter a vie que les refus definitifs (415, 413).
     « Note pour plus tard » (20/10). Voir la memoire
     exclusion-pour-erreur-est-a-vie.md.
   · ⛔ SORTI DU CHANTIER ⑦ LE 21/10, PAR DECISION DE FREDERIC -- voir « LES DEUX
     PORTES » plus bas. ON LAISSE LES CHOSES COMME AUJOURD'HUI. NE PAS RELANCER
     dans ⑦ : c'est un chantier a part, avec sa propre specification.
   · LA SENTINELLE DU REGISTRE (13/10) : elle ne crie plus au loup, mais la cause
     reste -- app_mandat__sb descend une heure APRES le push (table 97 sur 110).
         A descendre app_mandat__sb en PREMIER      B decaler le moniteur
   · L'HISTORIQUE DES VISITES (sorti du chantier ⑥ le 15/10, autoportant dans
     notice/HISTORIQUE_VISITES_HEKTOR_2026-10-15.md) : 1 721 bons de visite sont
     DEJA sur notre serveur (1 089 lisibles). Trois chemins chiffres, A / B / C,
     et un PREMIER PAS GRATUIT : relire les 1 089 textes pour dire la vraie
     periode et le vrai rythme. NE PAS RELANCER DE SOI-MEME.
   · LES 8 WARNINGS de l'e-mail du matin : ils NE SONNENT PAS (seuls les critical
     envoient). Chacun a un seuil pose pour une raison. A reprendre un par un
     S'IL LE DEMANDE -- rien n'a ete decide.
   · LA LIMITE `MAX_EXPORTED_IMAGES = 5` (export_app_payload.py:32) : elle ne mord
     pas aujourd'hui (0 annonce tronquee) mais elle DORT. La monter, ou retirer la
     troncature du payload ? Sans urgence.

③ ⛔ RESTES DU CHANTIER ③, SANS URGENCE :
   · redemarrer les 4 services un jour (les 2 messages du worker promettent
     desormais la reprise, mais ce texte n'est pas encore dans les processus) ;
   · le dossier serveur VIDE de la photo d'essai (le geste efface le fichier, pas
     le dossier) ;
   · appliquer_contrat_mandat.py : INUTILE depuis le 28/08. Trois options
     presentees le 13/10 (A le retirer du run / B le redresser / C le commenter),
     RECOMMANDE A. Il n'a pas tranche.
   · ⛔ L'INTERRUPTEUR CHAMPS_APP_ANNONCE RESTE ETEINT (tranche le 13/10). Le
     critere du projet n'est pas rempli : on n'allume qu'un champ que l'APP CREE
     et que HEKTOR N'ENTRETIENT PAS. C'est LA COUPURE qui nous rendra prets.

④ NE SE DECIDENT PAS SANS LUI (sortis des chantiers ② et ③) :
   · ce que doit voir exactement un AGENT COMMERCIAL (l'essai du 12/10 a prouve
     que tout abaisser casse le rapprochement : 93 % de lignes mortes) ;
   · la fonction de SECOURS admin-users, a deployer A PART chez Supabase
     (npx supabase functions deploy admin-users --project-ref dwaqxfrinihnychuoptk)
     -- inutile tant que Render repond ;
   · un essai REEL d'un geste chez Hektor par un negociateur ;
   · MODIFIER LES CHAMPS d'un bien vendu/clos : ce n'est PAS un repli, c'est un
     autre chantier, et l'ecran l'interdit deliberement ;
   · 📜 LES NEGOCIATEURS INACTIFS : 1 522 biens vivants (11 %) sont a leur nom.
     DECISION DU 13/10 : ON NE TOUCHE A RIEN. Ne pas relancer.

⑤ 📜 SUJETS A PART, OUVERTS PAR LUI -- NE PAS RELANCER DE SOI-MEME :
   · UN AUTO-ARCHIVAGE CONFORME RGPD (16/10, « c'est un autre dev »). Mesure du
     16/10 : Hektor pose une date d'auto-archivage a CREATION + 2 ANS sur chaque
     recherche, et CETTE DATE NE NOUS PARVIENT PAS (ni l'API ni notre table ne la
     portent -- elle n'existe que dans la page HTML). On CONSTATE le basculement
     apres coup, on ne l'anticipe pas.
   · LE CARNET DES LIENS : cause racine NOTEE ET REPORTEE le 10/10 (un lien
     s'identifie par un badge CALCULE alors que son numero existe).

⑥ NOTE, NON RELANCE (trouve en passant, hors perimetre) :
   · LE `if pending is not None:` DU PUSH D'UNE SEULE ANNONCE EST DU CODE MORT
     depuis le 21/09 : les 3 branches au-dessus remettent TOUTES pending a None,
     donc `dirty_annonce_skipped` ne peut plus jamais valoir 1 (mesure du 20/10) ;
   · phase2/sync/test_dirty_guards.py n'ajoute pas la racine au sys.path : il ne
     tourne qu'avec `PYTHONPATH=.` (il est vert ainsi, 4 tests) ;
   · 202 biens EN VENTE a mandat echu, dont 43 sans negociateur ;
   · 150 notifications sur 150 non lues ;
   · les 22 403 photos de LOCATION ecartees chaque nuit -- l'exclusion n'est pas
     declaree dans le code (elle devrait l'etre, regle du 14/10) ;
   · ⑩ trancher le geste du bien VENDU 47824 depuis l'ecran Sante (les boutons y
     sont depuis le 15/10).

⑦ HORS CODE (etape 3) : A.4 zone DNS (La Boite Immo -> OVH, garder www) · A.5 les
   leads · l'export PROTEXA · contrats A.1 et A.2 · C.9-couple (creer un menage
   d'essai, la sonde est prete).
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *à finir tant que Hektor vit*

```
G.1-b · G.2   ✅ PLUS DE PEREMPTION -- clos les 14 et 15/10 (chantier ⑥).
C.9-couple · C.13-c · E.1 (recherches, visites, documents, signatures) · A.3 · A.4
⭐ ET DEPUIS LE 19/10 : LES PHOTOS MASQUEES ont leur balayage (⑦-8 marche 2). Le
   jour de la coupure, elles seraient perdues -- ~1 100 photos sur le parc vivant.
   14 nuits. C'est la seule peremption qui AVANCE TOUTE SEULE.
```

### Ce qui reste vrai de l'exploitation

- ⏰ **La nuit, au 19/10** : `22:00` entretien documents *(3 lignes, fin 23:17-23:25)* · ⭐ **`00:00`
  le balayage des photos masquées** *(nouveau, lot de 1 000)* · `03:00` recherches actives · `05:00`
  le run *(fin 07:03-07:34)* · **`07:45` la descente** · `08:00` les relances e-mail ·
  **`09:00` la sauvegarde** · `12:30` reprise envois · `21:00` entretien photos.
  ⚠ **Le creux de la nuit va de ~23:18 à 03:00** — c'est le seul budget disponible.
  Reprise du run : `.\scheduled\run_quotidien.ps1 -StartAtLabel "<étiquette exacte>"`.
- ⚠ **Le mur de Hektor est un quota de VOLUME, pas de débit** : **13 000 à 17 000 requêtes par
  période**, et *« ralentir ne fait que retarder l'échéance »* *(mesure du 20/08)*. La règle de
  Frédéric : **rester 40 % en dessous**. ⭐ La nuit en consomme déjà **~4 500** *(mesuré)*.
  Les 4 freins du projet sont dans `console_job_worker.js` : **1 s** entre appels · **60 s** toutes
  les 100 · **300 s** toutes les 2 000 · **15 s** de recul après un refus, et **arrêt net**.
- **Render et Vercel se déploient seuls** sur un push vers `main` : `/health` rend le commit.
  ⚠ **La fonction Supabase `admin-users` NE se déploie PAS par un push.**
- ⚠ **Une autre session travaille en parallèle** : relire `git log` avant d'écrire, et stager
  **fichier par fichier**.
- ⚠ **Les alertes n'ont qu'UN seul canal** : `WHATSAPP_ALERT_WEBHOOK` n'a jamais été posé.
- ⚠ **11 tâches sont surveillées** par `check_gti_health.py` ; une tâche neuve se **déclare AVANT**
  d'être enregistrée, et se **compare réglage par réglage** à une sœur qui marche.

### ⭐ Les leçons

> **Les 31 leçons ont déménagé le 19/10** dans **`notice/LECONS_DE_METHODE.md`** — *numéros
> conservés*, parce que le code et les commits y renvoient *(« leçon 30 », « la règle n° 4 »)*.
> Elles pesaient **14 576 caractères** dans une section qui doit porter le présent.

**Les six qui servent au chantier en cours :**

| n° | en une ligne |
|---|---|
| **9** | ⭐⭐ **une cause structurelle se balaie dans TOUTE sa famille** — ce que Frédéric signale est un symptôme, jamais le périmètre |
| **30** | ⚠⚠ **dans un patch destiné à être COLLÉ** : `replace(…, chr(13), '')` autour de **chaque** ancre et de **chaque** texte inséré, et **des ancres sur UNE SEULE LIGNE** — une ancre sans retour chariot dedans est **immunisée** *(prouvé le 19/10 : trouvée 2 fois dans les 4 cas)* |
| **31** | **un retour arrière ne juge que SA part** — il vérifie d'abord qu'il ne reste aucune trace de ce qu'il devait retirer |
| **1** | ⭐ **mesurer LE GESTE DE L'ÉCRAN**, pas un geste plausible — lire comment l'écran lit, avant de crier |
| **23** | ⭐⭐ **une alerte doit écouter la réponse de l'humain** — et on croise sur les **identifiants**, jamais sur les nombres |
| **15** | ⭐⭐ **chercher si le projet a DÉJÀ tranché** avant de proposer une forme — deux fois le 19/10, la bonne réponse était déjà écrite *(le verrou des photos, et le passage par le worker)* |

---

## 3. Avant de coder — la liste de relecture *(plan, l. 1110 « ⛔ AVANT DE COMMENCER UN CHANTIER »)*

Elle existe *« parce que le 20/08 j'ai oublié trois fois un point déjà documenté »*.

1. La **section du plan** qui concerne la tâche — et ses voisines, les pièges y sont.
2. Les **notes citées** par cette section : elles portent les décisions déjà prises.
3. `notice/*.md` **et la racine**, par mot-clé — 160 notes au 07/10, la plupart citées nulle part.
4. `git log --all --diff-filter=D -- 'notice/*'` — 12 notes supprimées le 19/08 portent
   encore de la doctrine active. **À lancer depuis `C:\Hektor\Projet`.**
5. La **mémoire projet** : `C:\Users\admin\.claude\projects\C--Hektor\memory\`.

**Les trois questions, avant de dire qu'une chose est cassée :**
**Est-ce documenté ?** (ici, ce qui ressemble à une négligence est presque toujours une
décision écrite) · **Est-ce mesuré ?** (mesurer, *puis* conclure) · **Qu'est-ce que j'oublie ?**
(les cas voisins : la recherche supprimée, les contacts, les affaires…)

---

## 4. Ce qui ne se discute pas

- **Lire le CODE, pas les notes**, pour établir un état. *L'inventaire de `C.4` a été faux
  quatre fois parce que la liste ne suivait pas le code — c'est de là que vient l'impression
  de refaire les mêmes choses.*
- **Une mesure approximative vaut une mesure fausse.**
- **Une tâche n'est cochée que si son ÉNONCÉ est couvert**, et la mesure doit répondre à la
  question posée — pas montrer que « ça marche ». *(plan, l. 759 « ⚖ LA RÈGLE DU FAIT »)*
- **Ne rien écraser.** Additif et chirurgical, jamais de remplacement massif.
- **Pas de code sans « go » explicite.** Un message court, en cadrage, est une **question**.
- **Stager fichier par fichier.** Jamais `git add .` : 73 fichiers non suivis traînent
  dans le dépôt.
- **Les 5 règles du projet** et **la règle des identifiants** : plan, sections « LA RÈGLE DES
  IDENTIFIANTS » (l. 2970) et « LES CINQ RÈGLES » (l. 2981).
  *(un numéro ne se perd jamais · Hektor confirme, il n'écrase pas · une action a une fin
  visible · Hektor reste à jour tant qu'il diffuse · le miroir se met à jour, il ne se
  remplace pas)*

---

## 5. Les adresses

| | |
|---|---|
| le **pourquoi** | `notice/PLAN_DEV_ACTUALISE_2026-08-20.md` (3 092 l. au 08/10) |
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (9 469 l. au 08/10 — lire la page de tête, l. 1-75) |
| le **dernier audit** | `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md` — l'étape 2, objet par objet *(celui du 07/10, `AUDIT_AUTONOMIE_COMPLET_2026-10-07.md`, reste utile pour l'étape 3)* |
| l'**historique** de la page de tête | `notice/JOURNAL_DE_BORD.md` — *un pourquoi, jamais un ordre du jour*. ⭐ **Le §2 du 19/10 y est descendu EN ENTIER** *(79 966 caractères, verbatim)* |
| ⭐ les **31 leçons de méthode** | `notice/LECONS_DE_METHODE.md` *(déménagées du §2 le 19/10)* — ⚠ **numéros conservés**, le code et les commits y renvoient par leur numéro. **Ne jamais renuméroter** : une leçon neuve prend le 32. Les **six** qui servent au chantier en cours sont rappelées au §2 |
| le protocole de test en cours | `notice/PROTOCOLE_TEST_STATUTS_TRANSACTIONS_2026-09-01.md` |
| les pièges déjà payés | la mémoire projet (voir §3.5) |

> Ces deux documents pèsent 116 k tokens. **Ne jamais les lire en entier** : ouvrir la
> section concernée par son numéro de ligne, comme ci-dessus.

---

## 6. Pièges d'outillage

- **4 services worker** partagent `console_job_worker.js` : redémarrer **un seul ne suffit
  pas**. Un correctif non redémarré n'est pas actif — plusieurs essais ont été perdus comme ça.
- Le front se valide par `npm run build` dans `apps/hektor-v1` (c'est ce que fait Vercel).
- Vérifier un écran qui « plante » : **la console du déployé d'abord**, la base ensuite.
- **Les renvois `l. N` se décalent en silence** dès qu'on insère ailleurs dans la liste.
  Un renvoi ne se *calcule* pas, il se *trouve* — le 26/09, quatre étaient faux, dont
  trois depuis des jours *(`C.9-couple` pointait la section `C.4`)*. Après toute édition
  de la liste ou de cette page :

  ```bash
  python phase2/checks/verifier_renvois_liste.py --reparer
  ```

  Puis **relancer sans `--reparer`** : une correction change la taille du texte, donc
  peut décaler les suivants.

---

## 7. En fin de session — deux gestes, deux minutes

1. **RÉÉCRIRE le §2** de cette page — *réécrire, pas ajouter un bloc en haut.* C'est
   l'empilement qui l'avait porté à **732 lignes sur 895 — 91 % du fichier** le 19/10
   *(et à 467 sur 609 le 12/10 : l'empilement revient si on ne réécrit pas)*, avec des états datés marqués
   *« ne jamais relire comme un ordre du jour »* : un document qui se contredit ne tient
   plus le fil. Ce qui sort du présent descend dans `notice/JOURNAL_DE_BORD.md`.
2. **Réécrire la mémoire de reprise** (`reprise-…` dans le dossier mémoire), toujours la même,
   jamais une nouvelle par date. *Elle datait du 02/09 alors que 68 commits avaient suivi.*
