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
| ⑦ | **les gestes qui manquent** *(`notice/CHANTIER_7_GESTES_QUI_MANQUENT.md`)* | 🔧 **EN COURS** — voir le tableau ci-dessous |
| ⑧ | gardé chez nous en entier | ⬜ |

**Ordre de Frédéric : ① ⑤ ④ ② puis ③ → ⑥ → ⑦ ⑧.** ➡ **Le chantier en cours est ⑦.**
⚠ Un périmètre, une taille, un ordre ou un report **ne se décident jamais sans lui**.

### 🔧 LE CHANTIER ⑦ — les 12 points, et ce qui reste

> Le détail vit dans **`notice/CHANTIER_7_GESTES_QUI_MANQUENT.md`** *(4 100 lignes, à jour)*.
> Ici : l'état, et **seulement ce qui reste**.

| # | le point | état |
|---|---|---|
| ⑦-1 | archiver / désarchiver un contact | ✅ **base, worker et écran en production le 16/10** · ⛔ **reste l'essai ARCHIVER sur une fiche JETABLE** *(le sens qui porte le risque ; le contact d'essai 10355757 n'existe plus → il faut une cible)* |
| ⑦-2 | le cas Gladys DURIEUX | ✅ **RÉACTIVER réussi le 16/10 à 07:29** — et ses 2 recherches sont **inchangées** |
| ⑦-3a | clôturer un mandat à la main, le crayon, les droits | ✅ **les 4 pièces en production** *(la 2 poussée par l'autre session, `8676855`)* · ⛔ **reste : PERSONNE N'A VU L'ÉCRAN**, et **l'essai réel** *(clôturer avec une date ≠ aujourd'hui, et vérifier que le carnet porte LA DATE SAISIE)* · ⚠ **À TRANCHER : la modale de statut clôt toujours sans passer par la demande d'annulation** |
| ⑦-3b | l'écran du journal des suppressions | ✅ **écrit le 16/10** — Santé, admin strict, témoin inverse 128/0 |
| ⑦-3c | réordonner / choisir la photo principale | ✅ **la couverture est en production** *(`7727f66`)* · ⬜ **réordonner** reste |
| ⑦-4 | le bandeau qui ment | ✅ **traité le 16/10** — ⚠ la production ne mentait pas, c'était le **mobile** sur les 527 brouillons |
| ⑦-5 | relancer / abandonner depuis le monitoring | ✅ **fait le 15/10** |
| ⑦-6 | « Abandonner » défait le geste | ✅ **fait le 15/10** |
| ⑦-7 | modifier ou prolonger un mandat | ⛔ **FERMÉ PAR DÉCISION le 18/10** — *« je ne souhaite pas pouvoir modifier un mandat ou prolonger »*. **Ne pas relancer** |
| ⑦-8 | **photos : rendre visible / masquer** | 🔧 **marches 1 et 2 faites** *(voir ci-dessous)* · ⬜ **marche 4 : le bouton** |
| ⑦-9 | renommer un document | ⬜ |
| ⑦-10 | `app_brouillon_annonce_detail_cache` vide | ⬜ **question** : seulement si Frédéric en a l'usage |

**⑦-8, les 4 marches** *(19/10)* :

| | |
|---|---|
| **1 — le verrou de publication** | ✅ **EN PRODUCTION**. `app_photos_remplir_adresses_app` exclut les masquées des **deux** boîtes *(couverture + galerie)*. Empreinte `682e3860` → **`b87f6c68`**, 7 contrôles verts. ⭐⭐ **L'idée des deux boîtes est de Frédéric**, et elle a rendu les pièces A et B inutiles. ⚠ **Le témoin inverse a prouvé qu'elle a servi le jour même** : sans elle, 3 masquées partaient le soir sur la vitrine, l'espace client et le portail |
| **2 — le balayage** | ✅ **écrit, éprouvé, la tâche est enregistrée** — `GTI Balayage Photos Masquees`, **00:00**, lot de **1 000/nuit**, **~14 nuits** pour les 13 491 vivantes. ⭐ Il **passe par le worker** *(un seul service, un seul frein)* : `Console/enqueue_photos_masquees_lot.js` + `scheduled/run_balayage_photos_masquees.ps1`. **Essai réel vert le 19/10** : 4 → 7 photos sur 62189, `hidden: 3` comme prédit |
| **3 — le run de mise à jour** | ⭐ **rien à écrire** : c'est **le même lot**, rempli « les modifiées d'abord, les jamais-vues ensuite ». Quand le balayage finira, il tombera à **~29/nuit** et deviendra le run de MAJ **tout seul** |
| **4 — le bouton masquer/afficher** | ⬜ `mode=vignette_visibilite&id=…&idann=…&visible=0|1`, trouvé dans le code de Hektor, **jamais prouvé en écriture**. ⛔ **Son essai sur le bac à sable 62774 demande l'accord de Frédéric** — et il répondra aussi à la question restée ouverte : **masquer une photo bouge-t-il `date_maj` ?** ⭐ **Aucune limite de photos ne le gêne** *(sujet clos le 19/10 : le panneau lit la table, limite 500 ; le « 5 » de `export_app_payload.py` ne mord plus, 0 annonce tronquée)* |

### ⛔ Ce qui attend Frédéric

```
⓿ ⏰⏰ LE 20/10 AU MATIN -- LA PREMIERE NUIT DU BALAYAGE DES PHOTOS MASQUEES.
   UNE COMMANDE, UN VERDICT (elle ne fait que LIRE, aucun appel a Hektor) :
        python phase2/checks/controle_balayage_photos_masquees.py
   Sortie 0 = vert · 1 = un rouge · 2 = pas pu mesurer. Huit points, dont :
     ⭐ LE RYTHME REEL -- c'est LUI qui dit si on peut monter le plafond de 1 000
        (il refuse de conclure sous 20 travaux mesures : « non concluant ») ;
     ⭐⭐ LE VERROU -- ZERO masquee dans une boite publique. Le controle qui compte.
   REFERENCE FIGEE DANS LE FICHIER (19/10 au soir) : 106 masquees sur 15 annonces ·
   3 avec un derive · 0 dans une boite · 13 490 a faire · 305 deja visitees.
   ⚠ UN REFUS SORT EN 1 EXPRES, et il est ROUGE : code 3 « file non vide » (le
     worker est plus lent que le lot -> baisser -Limite), code 4 « >= 10 erreurs
     en 24 h » (Hektor nous rejette -> ne RIEN rejouer).
   TEMOIN INVERSE JOUE LE 19/10 AU SOIR : 5 oranges, 0 rouge.

① LES ESSAIS REELS QUI MANQUENT (chantier ⑦) :
   · ⑦-1 ARCHIVER un contact sur une fiche JETABLE -- le sens qui porte le risque
     (le serveur de Hektor archive-t-il AUSSI les recherches ?). Le contact d'essai
     10355757 N'EXISTE PLUS : en creer un (ecriture chez Hektor = son accord) ou
     qu'il en designe une.
   · ⑦-3a CLOTURER avec une date DIFFERENTE d'aujourd'hui, et verifier que le
     carnet porte LA DATE SAISIE. ⚠ Mesurer sur LA VALEUR, pas sur l'heure (le
     PATCH du worker ne rafraichit pas `ecrit_le`).
   · ⑦-3a PERSONNE N'A VU L'ECRAN : ecran Mandats, ouvrir une fiche, le bloc
     « Cloture du mandat » est SOUS LA JAUGE.
   · ⑦-8 marche 4 : masquer une photo sur le bac a sable 62774 (ecriture Hektor).

② A TRANCHER PAR LUI -- je n'ai rien choisi :
   · ⑦-3a : la MODALE DE STATUT clot toujours sans passer par la demande
     d'annulation, alors que sa consigne du 16/10 etait « toujours par la
     demande ». Elle est deja reservee admin/manager. On la laisse ou on la ferme ?
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
