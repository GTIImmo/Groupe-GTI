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
| documents de travail | `notice/` — 123 notes |

---

## 2. Où on en est — *une page, pas une archive*

> ⚠ **Cette section porte LE PRÉSENT, et rien d'autre.** Elle avait grossi à **467 lignes
> sur 609**, avec quatre états datés dont trois marqués *« ne jamais relire comme un ordre
> du jour »*. L'historique est parti dans **`notice/JOURNAL_DE_BORD.md`** le 26/09 : on
> l'ouvre pour comprendre **un pourquoi**, jamais pour savoir quoi faire.
>
> **Règle : en fin de session, on RÉÉCRIT cette section. On ne l'empile pas.**

**Mis à jour le 03/10/2026 (fin de journée).** *334 lignes closes descendues au journal
le même jour : le §2 avait regrossi à 832 lignes sur 989.*

### ⚙ LE RUN DE NUIT — *cassé le 03/10 au matin, réparé et PROUVÉ en production*

```
CE QUI S'EST PASSE                                    journal du 03/10, 05:00 -> 08:21
  l'etape « registre des liens (app_relation) » est passee de 46 s a 79 MINUTES
  -> le run a fini a 08:21 au lieu de 07:41
  -> il tournait donc ENCORE quand la descente a demarre a 08:15
  -> 3 etapes « console » ont echoue (elles ecrivent dans LA MEME base locale)
  -> 17 etapes n'ont JAMAIS demarre, dont TOUTES les montees vers le cloud.
     L'app est restee sur les donnees de la veille jusqu'a 10:17.

LA CAUSE : une sous-requete correlee sur app_relation__sb, qui n'a AUCUN index.
  ~17,6 milliards de lectures de ligne. ⛔ ET POUR RIEN : 0 retrait a adopter.

⛔⛔ ET LE PREMIER CORRECTIF ETAIT FAUX -- c'est LA lecon du jour.
  Poser un index ne suffisait pas : la descente cree les colonnes de la doublure
  SANS TYPE DECLARE, donc sans affinite, et la forme « sous-requete correlee »
  ecarte l'index. Mesure sur donnees reelles : le plan ne bougeait PAS.
  LA BONNE REPARATION N'EST PAS DE FORCER L'OPTIMISEUR, C'EST DE RENDRE LA TABLE
  INTERIEURE PETITE -- un retrait est un geste HUMAIN. On extrait les seuls
  retraits dans une table TEMP typee, et UPDATE..FROM pilote depuis elle.

PROUVE EN PRODUCTION le 03/10 a 14:58 (run complet, lance par la tache elle-meme) :
      ce matin 4 740 s   ->   MAINTENANT 46 s    x103, la ligne de base d'avant
      run complet 2 h 09, 53 etapes DONE, 0 echec, exit 0
      les 3 etapes console : 9 SECONDES a elles trois
      ⭐ donc ce n'etait PAS Supabase, c'etait LE VERROU SUR LA BASE LOCALE.

⭐ ET UNE REPRISE EXISTE DESORMAIS                  scheduled/run_quotidien.ps1
      .\scheduled\run_quotidien.ps1 -StartAtLabel "<etiquette exacte>"
      Le script execute SES PROPRES commandes (les arguments sont CALCULES) --
      jamais une recopie a la main. Garde-fou : une etiquette introuvable LEVE une
      erreur au lieu de finir « successfully » sans rien faire.
      ⚠ LIRE LE JOURNAL DANS LES 30 s : chercher `REPRISE a partir de` et compter
        les `SAUTEE (reprise)`. Le 03/10 a 09:46 la reprise est repartie DU DEBUT
        (un Write-Output dans le garde polluait la valeur de retour) -- arretee en
        90 secondes parce que le journal a ete lu tout de suite.

⬜ CE QUI RESTE, et qui aurait EMPECHE l'incident :
   · `busy_timeout` sur pull_from_supabase.py -- il n'en pose AUCUN, et la descente
     EST ce script : deux ecrivains sur phase2.sqlite, sans filet
   · un garde-fou d'ordonnancement : la descente ne doit pas demarrer si le
     quotidien tourne encore
   · pousser `dbbc99f` et `93a2055` (le serveur tourne dessus, GitHub ne les a pas)
```

### L'étape, en une ligne

```
ETAPE 2 = l'app fait TOUT, sauf trois choses qui restent a Hektor :
          le numero de mandat (L9) · la signature (A.2) · les portails (A.1)

L0 ✅   L1 ✅   L2 ✅   L3 ✅   L4 🟡   puis  L5  L6  L7  L8  L9
```

### ✅ LE SUJET « ANNONCES » EST CLOS (audit final du 28/09)

> **L'annonce n'est pas au niveau des autres objets : elle est AU-DESSUS.** Tout mesuré
> dans le code et les deux bases le 28/09 au soir.

```
                      ANNONCE  contact  recherche  relation  transaction
gestes du worker           15        6          3         1            4
tables Supabase            17       12          6         1            9
RPC optimistes vivantes     6        3          2         2            3
push partiel detecte       OUI      non        non        --      par champ
sentinelles                 5       10          8         0            2
corps durable en local  189/189     oui        oui       oui          oui
```

⭐ **DEUX CHOSES QU'ELLE SEULE SAIT FAIRE** : detecter un envoi PARTIEL (`partial` +
`skipped_fields`, 15 colonnes contre 13), et un OEIL dedie (`C.9-b`, 0 ecart sur 13 439).

⚠ **CHIFFRE PERIME CORRIGE** : « 5 workers sur 16 ecrivent d'abord dans l'app » datait du
29/08. La vraie couverture est **13 sur 16** ; les 3 manquantes sont les SUPPRESSIONS,
exclues volontairement (arbitrage du 30/08). Les 15 RPC sont appelees par le front.

⚠ **UN TOTAL NE SE COMPARE PAS, IL SE DEPLIE.** « 5 sentinelles contre 10 » disait retard ;
depliees, elles disent l'inverse : les 3 de base sont des deux cotes, l'annonce en a DEUX
DE PLUS, et les 7 autres du contact surveillent les doublons et les fiches de couple --
un probleme qui n'existe pas pour l'annonce.

⛔ **SEULE VRAIE FAIBLESSE, ET ELLE N'EST PAS SUR L'ANNONCE : `RELATION`** -- 1 table,
0 sentinelle, pas de file d'attente. Notee, PAS enchainee.

**Ce qui reste sur l'annonce** : 2 gestes de confort (photo : supprimer/reordonner ·
modifier un mandat existant) + les 4 exceptions. **Aucun ne perime.**

➡ **LA SUITE UTILE N'EST PAS L'ANNONCE, C'EST CE QUI PERIME** :
   `L9` le registre des mandats (3-5 j) · les liens publics (11bis) · `C.9-couple`

### 📡 A.1 LES PASSERELLES PUB — *ouvert ET la bascule LeBonCoin a eu lieu, 30/09*

> ⚠⚠ **HEKTOR A BASCULE LEBONCOIN LE 30/09, PENDANT LA SESSION** — entre le run de
> nuit (04:21) et 16h45. Les **9 passerelles groupees sont remplacees par 17
> individuelles (45 a 61)**, une par agence. Seule la 35 survit, en train de se vider.

```
⛔ LE DEBALLEUR RENDAIT ZERO DEPUIS LE 07/07          -> REPARE  02c2c7c
   Hektor a change la forme : `data` liste -> {"platforms": [...]}.
   iter_listing_items testait isinstance(data, list) et rien d'autre.
   list_broadcasts est LE SEUL des 28 listings emballe.
   ⚠ LE PIEGE QUI A FAIT DURER 3 MOIS : la lecture a la volee RECOPIAIT le
     contenu de juillet EN Y TAMPONNANT LA DATE DU JOUR. Tout controle de
     fraicheur disait vert.
   ⭐ LE VRAI CORRECTIF N'EST PAS D'OUVRIR CE CARTON, C'EST `bilan` : un carton
     a la mauvaise cle est COMPTE, jamais rabattu sur `or []`.

⛔ LA TABLE ACCUMULAIT                                 -> REPARE  02c2c7c · 96451dc
   L'upsert ajoute et corrige, il n'enleve jamais -> 208 diffusions fantomes.
   Et l'effacement CIBLE ne suffisait pas : les 8 passerelles SUPPRIMEES
   gardaient leurs lignes (308 lignes mortes au run du soir).
   On efface donc aussi les absentes, MAIS seulement si la reponse fait
   autorite (pas d'erreur, pas de page suivante, au moins une passerelle).
   ⭐ ON EFFACE L'ETAT, JAMAIS LA TRACE : la ligne de hektor_broadcast reste --
     c'est sa date de derniere vue qui a permis de dater la mort de la n° 37.
   4 FILETS EPROUVES CONTRE UN CAS QUI DOIT ECHOUER : tronquee / erreur /
   vide / carton inconnu -> dans les 4 cas, on ne touche a rien.
   MESURE : 2 046 -> 1 660 lignes, 412 annonces, 0 fantome, 0 manquante, rejeu +0.

⛔ LA CARTE AGENCE -> PASSERELLE ETAIT FAUSSE          -> COLLE 18:16  d629257 · 11e1a71
   ⚠ ET UNE PANNE TOURNAIT DEPUIS SIX MOIS : la n° 37 (Montbrison + Saint-Just)
     n'existait plus depuis le 03/04, renumerotee 44. 1 795 annonces (13 % du
     parc) routees dans le vide, en silence. C'etait le PREMIER cas de la serie.
   QUATRE endroits portaient les vieux numeros, pas un :
     ① app_diffusion_agency_target (Supabase)        -> patch, 17 lignes
     ② app_diffusion_target, cibles PAR BIEN
        ⚠ ELLES PASSENT AVANT LA CARTE (_run_apply les lit en 1er)
        1 sur un bien VIVANT : V670062151 Tence 43 -> 53  -> patch
     ③ les tables miroir                             -> le run
     ④ UNE COPIE ECRITE EN DUR DANS LE FRONT (lib/api.ts)
        ⛔ elle vit dans le paquet DEPLOYE : corriger Supabase ne la corrige PAS
        -> 5963b59, deploye le 30/09

✅ L'EPREUVE, DEUX NIVEAUX                             f6c3377 · 0ada1ee · 7a38043
   phase2/checks/passerelle_par_agence.py
   · par defaut : DEDUIT (passerelle -> negociateurs -> agence). A TROUVE la panne.
   · --par-agence : HEKTOR REPOND (ListPasserelles, un appel par agence). L'a PROUVEE.
   RESULTAT : 17 agences · 17 repondues · 0 muette · 17 numeros ET 17 identifiants
   DISTINCTS -> « un numero par agence » est MESURE, pas suppose.
   ⭐ Firminy 48 et Saint-Etienne 49 sont SEPARES (ils partageaient la 39) --
     Frederic l'avait pressenti, la mesure le confirme.
   bienicidirect : 17 sur 17 JUSTES, aucune correction.
   ⚠ DEUX PIEGES : ListPasserelles n'ouvre que sur un bien DIFFUSABLE (18 agences
     sur 19 ont d'abord repondu vide) ; et LE TEMOIN NE DOIT PAS VENIR DU PORTAIL
     MESURE, sinon la reponse est fabriquee par la question.

⚠ LE WORKER N'EST PAS CONCERNE, ET C'EST MESURE
   41 genres de travaux, 0 pour la diffusion. `idPasserelle` : 0 occurrence.
   67 610 travaux en base, 0 de ce type.
   MAIS il fait bien « activer la publication » : change_hektor_annonce_status
   envoie `diffusable=1` avec le statut Actif (et 0 pour Mandat clos).
   ⭐ POURQUOI PAS DE WORKER : Hektor a DEUX PORTES. Le worker pilote l'interface
     web (xmlrpc + cookies) faute d'API. Les passerelles, elles, ONT une vraie
     API d'ecriture (PUT addAnnonceToPasserelle / DELETE remove). C'est la SEULE
     famille de gestes ou l'app ecrit chez Hektor SANS worker.
   ⚠ Le nom trompe : la modale s'appelle « Console passerelles » et dit « la
     console enverra » -- ce n'est PAS le worker Console.

CE QUI RESTE
   ⬜ l'etat enregistre = le SOUHAIT, pas la CONFIRMATION
      handleCommitDiffusionTargets ecrit portails_resume depuis les cases cochees.
      Si Hektor refuse, la modale montre « Erreurs 1 » MAIS la fiche dit diffuse.
      ⭐ LA BONNE VERSION EXISTE ET DORT : handleApplyDiffusionTargetsOnHektor
        lit result.applied -- definie, JAMAIS branchee. Correctif = 1 ligne.
   ⬜ UNE SENTINELLE carte <-> passerelles vivantes -- le vrai remede de fond
   ⬜ la copie LOCALE de la carte (phase2/phase2.sqlite) reste perimee (chemin dev)
   ⬜ hektor_annonce_broadcast_target : 0 ligne, code mort
   ⬜ idPasserelle = le NOM du portail quand aucun numero n'est trouve
      (3 lignes en base : superimmo, etreproprio, paper) -- sans effet, mais muet

⚠⚠ ET LE CONTROLE LUI-MEME A MENTI UNE FOIS : a 18h20, juste apres le patch, il
   a dit « 17 a corriger » -- il lisait la COPIE LOCALE, pas Supabase. Calcul
   juste, SOURCE fausse. Troisieme fois de la journee.
   ➡ LA REPARATION N'EST PAS « changer de table » : la fonction RENVOIE SA
     SOURCE et le controle l'IMPRIME. Un controle qui ne dit pas ce qu'il a lu
     peut affirmer le contraire de la verite sans se tromper d'un chiffre.

L'AUDIT ENTIER : notice/AUDIT_PASSERELLES_PUB_2026-09-30.md
```

### 🔗 LE REGISTRE DES LIENS — *chantier ouvert le 30/09, 1re pierre posee*

```
L'AUDIT, DEUX PASSES               notice/AUDIT_REGISTRE_RELATIONS_AUTONOME_2026-09-30.md
  ⭐ LA DONNEE EST DEJA SUR NOS NUMEROS, et personne ne le savait :
     app_contact_relation_current.hektor_contact_id -> 167 547 sur 167 547 dans
     la plage app, 0 de style Hektor. LE NOM DE LA COLONNE MENT
     (build_contacts_layer.py:1093 fait identite_app() AVANT de la remplir).
     C'est ce mensonge qui a cache le bug pendant une semaine.

✅ LE BUG « Aucune annonce liee » EST REPARE          93cc01b   DEPLOYE 30/09
   La fiche annonce transmettait un numero HEKTOR. On ne change pas ce qu'elle
   LIT, on corrige le numero qu'elle TRANSMET : charger la fiche d'abord, puis
   lire ses liens sous SON numero. api.ts interdit d'elargir le filtre ; sa
   consigne SUPPOSE un contact deja charge -- on rend la supposition vraie.
   2e appelant corrige : le bon de visite (1 numero Hektor sur 11 dans
   app_google_calendar_event_link). Un CONTROLE NEUF verifie la supposition,
   et il a une preuve : il echoue sur la version d'avant.
   ⛔ « ajouter app_contact_id a la vue » etait INUTILE : la vue expose deja
     hektor_contact_id, qui CONTIENT notre numero. Aucun SQL de production.

✅ LA TABLE DURABLE app_relation EST POSEE            fc07443 · d2bada5
   EN PRODUCTION le 30/09 : 132 622 lignes, verrou 3,5 s, integrite ok,
   0 doublon · 0 hors plage app · 0 dans la plage reservee · 9 sans notre
   numero de bien (gardees, leur annonce n'existe nulle part).
   Rejeu sur copie : neufs 0, revus 132 622 -> AUCUNE renumerotation.
   ⭐ LE CHIFFRE : le cloud porte 50 236 liens, la table 132 622.
      82 386 LIENS QU'UN BIEN VENDU EMPORTAIT. C'est cela qu'elle repare.
   ELLE PORTE mandant + proprietaire. Elle NE PORTE PAS les acquereurs
   (34 925) : un acquereur n'est pas un lien au bien, il existe PARCE QU'IL A
   FAIT UNE OFFRE -- app_affaire_ledger le tient deja. Elle les PROJETTERA.
   Elle stocke LE FAIT (« proprietaire du bien »), pas le libelle : sur
   132 622 couples, ZERO ne porte les deux roles -- deux noms d'une chose.

⚠⚠ ET UN INCIDENT QUE J'AI CAUSE, A NE PAS OUBLIER
   Ma 1re version du delete-never a tenu un VERROU D'ECRITURE 8 min 30 sur
   phase2.sqlite (132 000 x 132 000 comparaisons sur une table temporaire sans
   index), puis a ete coupee AVANT le commit : zero ligne, huit minutes de base
   bloquee pour rien. Diagnostic pose par une autre session.
   ⛔ LA FAUTE N'EST PAS LE DEFAUT, C'EST LA METHODE : j'ai ecrit en production
     sans repetition sur copie, en me disant « la table est neuve, rien ne la
     lit ». Vrai pour la TABLE, faux pour le VERROU. J'avais meme LANCE une
     copie et je l'ai ANNULEE pour aller plus vite.
   ➡ memoire `phase2-sqlite-verrou-ecriture-long`

REPONSES DE FREDERIC (30/09) : Q1 TOUT MONTE (registre entier, +116 Mo) ·
Q3 « retirer un mandant » PART chez Hektor et la ligne reste datee.
OUVERTES : Q2 acquereurs (projection recommandee) · Q4 mandants d'affaire
(les deux, ce ne sont pas le meme fait) · Q5 l'ordre.

✅ LA SENTINELLE data.relation_disparue                bebd16f
   4 gardes, seuil zero : source_absents · doublons · hors_plage_app ·
   plage_envahie. Le retard du cloud en INFORMATION, jamais en alerte.
   MESURE EN MEMOIRE, PAS EN SQL : 0,514 s (la version SQL de la sonde du
   mandat tournait 2 min avant d'etre coupee -- une garde qui ne tourne pas
   n'est pas une garde).

✅ L'ETAPE DE NUIT                                     bebd16f
   ⚠ SA PLACE EST APRES « build contacts layer seconde passe » : avant, elle
     lirait la couche de LA VEILLE. 4,2 s dont 3,5 s de verrou.

✅ SUPABASE + LE PUSH                                  543fac2
   132 622 lignes en ligne, identiques au serveur. TOUT MONTE (decision du
   30/09) : le registre porte tout, les ecrans filtrent.

✅ LA BASCULE -- L'ECRAN LIT LE REGISTRE                ff2b98c
   app_contact_relations_current : 81 379 -> 163 765 lignes, +82 386.
   ⭐ LE FRONT N'A PAS BOUGE D'UNE LIGNE : meme nom de vue, memes 18 colonnes.
   TROIS ESSAIS, et les deux rates valent d'etre gardes :
     ① deriver le role du SEUL numero de mandat changeait 4 961 etiquettes,
       toutes mandant -> proprietaire, parce que l'index d'archive a oublie le
       numero. Un homme qui a signe en 2019 EST le mandant de ce bien-la.
       -> repli sur role_hektor : 0 etiquette changee.
     ② PROJETER les acquereurs depuis app_affaire_ledger perdait 791 lignes :
       le ledger ne porte qu'UN app_contact_id par affaire, les CO-ACQUEREURS
       vivent dans acquereurs_json, encore sur numeros HEKTOR. 2 450 affaires
       ont plusieurs acquereurs.
       -> ils restent lus dans la table de nuit jusqu'a ce que ce blob passe
          sur nos numeros. ZERO perte de fonction.
     ③ 6 433 liens sans titre : 3 136 biens qu'aucun index du CLOUD ne nomme,
       alors que le SERVEUR en connait 58 598 sur 58 604. Index incomplet,
       pas une perte. A TRAITER A PART.

CE QUI RESTE -- LES CINQ POINTS, dans l'ordre
   A ✅ LE REGISTRE DISTINGUE DEUX ABSENCES -- FAIT 30/09  e1d9d59
        C'etait MOI
        qui l'ai ouvert : « Hektor ne le montre plus » n'est PAS « on l'a
        supprime ». Quatre chemins effacent un lien (worker : annonce, contact ;
        serveur : delete_local_annonce, delete_local_contact) et AUCUN ne
        connait app_relation. Ma vue ne filtre pas sur present_in_hektor :
        elle montrerait un lien supprime. 0 degat aujourd'hui, le 1er contact
        supprime le produit.

   B ✅ LE NUMERO HEKTOR DE LA PERSONNE -- FAIT 30/09  a574344
        Les autres registres portent les DEUX numeros de CHAQUE objet qu'ils
        nomment. app_relation nomme deux objets et n'a celui de Hektor que
        pour le BIEN. (Trouve par Frederic, 30/09.)
        ⛔⛔ ET J'AVAIS ANNONCE UNE PERTE QUI N'EXISTE PAS : « 50 982 sur
          96 070 ne sont plus traduisibles ». FAUX -- j'interrogeais
          app_contact_identite_app (62 038), LE JOURNAL DE LA BASCULE.
          La correspondance complete est dans app_contact_current COTE SERVEUR :
          356 270 contacts, hektor_contact_id = LE NOTRE (tous >= 10 M),
          hektor_target_id = CELUI DE HEKTOR (tous < 10 M).
          MESURE : 96 070 sur 96 070. 100 %.
        REMPLI ET VERIFIE : 132 622 lignes sur 132 622, 0 sans numero.
        Le run COMBLE, il n'ecrase jamais. La RPC l'ecrira aussi -- elle recoit
        deja ce numero du front (mesure : contact_id = 603953).
        ➡ TROIS FOIS LA MEME FAUTE LE 30/09 : mesurer sur la MAUVAISE SOURCE,
          puis alerter sur un chiffre que mon propre code avait fabrique.
          memoire `mesurer-sur-la-bonne-source`.

   ⚠⚠ DEUX CORRECTIFS D'URGENCE LE 30/09 AU SOIR -- LA VUE ETAIT INUTILISABLE
      cf3e63b  index d'expression   985 ms -> 4 ms
      d5c09bb  LATERAL au lieu du CTE  7 586 ms -> 7 ms
      J'AVAIS RENDU LA VUE 100 A 280 FOIS PLUS LENTE ET JE NE L'AVAIS PAS
      MESURE. J'avais verifie le NOMBRE de lignes, le contenu, l'absence de
      perte -- et PAS UNE FOIS LE TEMPS.
      ⛔ ET MON 1er CORRECTIF NE PROUVAIT RIEN : mesure sur un contact SANS
        lien, ou Postgres n'execute jamais la partie couteuse (« never
        executed »). J'ai mesure LE CAS OU IL N'Y A RIEN A FAIRE.
      LES DEUX DEFAUTS, a reconnaitre dans un plan :
        · « Seq Scan, Rows Removed by Filter: 132628 » alors qu'un index
          existe -> la vue CONVERTIT LA COLONNE (app_contact_id::text) et le
          rend inutilisable -> index D'EXPRESSION
        · « Sort Method: external merge Disk » sur un CTE -> il MATERIALISE
          57 682 lignes a chaque requete -> LATERAL, et convertir LE PETIT
          COTE de la jointure, jamais la colonne indexee d'en face
      VERIFIE SUR 7 PROFILS : 76 liens 7,2 ms · 72 -> 1,9 · 50 -> 1,7 ·
      3 -> 1,1 · 1 -> 0,1. Contenu inchange : 163 765, 0 perdue, 0 ajoutee.
      ➡ memoire `mesurer-le-temps-pas-seulement-le-resultat`

   C 🔺 LA PROJECTION DES ACQUEREURS -- REMONTEE, mon refus reposait sur un
        chiffre FAUX. J'avais annonce « projeter perdrait 791 lignes ».
        ⛔⛔ TROIS ERREURS DANS MA MESURE, dont une grosse :
          `acquereurs_json` est tantot une LISTE, tantot un OBJET SEUL, et mon
          code faisait `if not isinstance(items, list): continue` -- il
          SAUTAIT EN SILENCE 11 151 affaires sur 30 358 (37 %).
          parties lues 23 798 -> 34 949 en realite.
        LE VRAI CHIFFRE : le ledger connait 16 080 des 16 253 couples (98,9 %),
        CO-ACQUEREURS COMPRIS (affaires a 2, 3, 4, 5 et 6 acquereurs).
        ⭐ ET LES 180 N'EXISTAIENT PAS NON PLUS : encore la mauvaise table de
          traduction. Avec app_contact_current (356 270) : le miroir en plus = 0,
          le ledger en plus = 14. LA PROJECTION NE PERD RIEN.
        MESURE COTE CLOUD : 32 979 parties traduisibles sur 34 949 (le cloud n'a
        que 62 059 contacts) -> 0 PERDUE, +1 778 GAGNEES par rapport a l'ecran
        d'aujourd'hui. Les 1 970 intraduisibles sont des contacts absents du
        cloud, donc pas affichables aujourd'hui non plus.
        ⛔ SUSPENDUE : sa 1re version met 7,6 s -- le meme defaut que celui
          repare ci-dessus. A reprendre AVEC UN LATERAL.
        ⚠ ET LA TRADUCTION S'ENRICHIT : le ledger connait des correspondances
          que app_contact_identite_app ignore (ex. 458 -> 10000231).
          62 038 -> 63 222 ; non traduisibles 828 -> 189.
        ➡ LECON : « un total ne se compare pas, il se DEPLIE ». J'ai compare
          23 798 a 34 925, vu un ecart, et conclu -- sans deplier d'ou il
          venait. Il venait de MON code.

   ✅ LA RPC POSE LE LIEN DURABLE -- EN LIGNE le 30/09      5294c2f
        app_link_mandant_optimistic, version 2. Le WORKER NE BOUGE PAS :
        travail, garde-fou et etiquette provisoire intacts, verifie apres
        collage (2 155 -> 4 542 caracteres, toutes les parties d'origine la).
        ⚠ LA VERSION 1 ETAIT PERIMEE AVANT D'ETRE COLLEE : ecrite avant la
          colonne hektor_contact_id, elle aurait creuse le trou a l'endroit
          meme ou on venait de le boucher. Verifie avant de le dire --
          Frederic croyait l'avoir collee, il ne l'avait pas fait.
        UNE SEULE LECTURE REND LES DEUX NUMEROS (app_contact_current porte
        les deux). Eprouve : 603953 -> 10354641+603953 · 10000023 ->
        10000023+41 (retrouve) · inconnu -> AUCUNE ligne.
        ⚠ La ligne neuve porte present_in_hektor = false : la VUE ne la montre
          pas encore. On MONTRE ce qui est etabli, on GARDE ce qui est en
          cours -- l'affichage immediat reste a l'etiquette provisoire.
        ⚠ ATTENDU, PAS UN BUG : `nees_dans_l_app` reste a 0 jusqu'au premier
          mandant rattache, et `adoptes_du_cloud` passe a 1 au run suivant.
          C'est ainsi qu'on saura que la chaine complete tourne.
        ⛔ AUCUN REDEMARRAGE DE SERVICE : le worker n'a pas change.

   D ✅ LES LIENS « APP SEULE » Y ENTRENT -- FAIT 30/09        f8ebc71
        45 au filet, 11 VIVANTES, 5 deja connues, 6 VERSEES. Et 3 des 45 sont
        apparues LE 30/09 : ce n'est pas du vieux bruit.
        ⚠ Ma mesure de « 11 absentes » etait FAUSSE : je cherchais avec une
          cle nulle, la requete rendait 0 pour toutes.
        ⛔⛔ ET UNE FAUTE EXEMPLAIRE DANS LE MEME GESTE : `json` n'etait pas
          importe ; mon `except Exception` a avale le NameError et les 6 lignes
          sont parties SANS LEUR ROLE NI LEUR CLE -- et RIEN NE L'A DIT.
          C'est la faute que j'avais notee en memoire LE MATIN MEME.
          Corrige : except (ValueError, TypeError), et un compteur
          `app_seule_illisibles` au bilan. Un except large est un mensonge
          en puissance.

   E ✅ LES 4 FONCTIONS DES GESTES MANDANT AU DEPOT -- FAIT     814f81f
        supabase/fonctions_gestes_mandant_ETAT_2026-09-30.sql, copie fidele.
        La 5e est versionnee dans son propre patch.
        ET L'ECRITURE A FAIT VOIR TROIS CHOSES :
          · les `_optimistic` ne re-valident PAS, elles s'appuient sur les
            garde-fous des `_job` par recouvrement -- volontaire
          · un contact sans NOM ou sans EMAIL est REFUSE des la fabrique
          · une fabrique pose le numero SOUS DEUX CLES (hektor_contact_id ET
            contact_id) : a NE PAS « nettoyer », le doublon est intentionnel

✅ F -- « CREER UN CONTACT ET LE RATTACHER » : EN SERVICE 30/09 17h33   e926a53
   « Ajouter un mandant est un worker qui doit AUSSI fonctionner. »
   ETAT MESURE :
      le worker SAIT le faire           case create_hektor_mandant_contact  ✅
      la RPC pose le travail            app_create_mandant_contact_optimistic ✅
      la ligne DURABLE                  ❌ RIEN -- « ni contact ni lien avant
                                           Hektor » (audit relations, geste 2)
   POURQUOI : a l'instant du geste, le contact n'a AUCUN numero -- ni le notre
   ni celui de Hektor. Il n'y a rien a quoi rattacher.
   ⭐ ET LA PIECE MANQUANTE EXISTE DEJA : `app_create_contact_optimistic` fait
     NAITRE un contact dans l'app avec NOTRE numero (L4-b, prouve en reel deux
     fois le 21/09 -- identite 10 000 002). Le geste mandant ne s'en sert pas.
   FAIT. ⚠ ET L'ORDRE REEL EST L'INVERSE DE CE QUE J'AVAIS ECRIT : LE TRAVAIL
   D'ABORD, parce que c'est LUI qui porte les garde-fous (nom, email,
   permission). S'il refuse, rien ne s'ecrit -- l'exception annule tout.
   Puis le contact durable, puis le lien, puis l'etiquette provisoire INCHANGEE.
   ⛔ ON NE POUVAIT PAS ENCHAINER DEUX FONCTIONS : app_create_contact_optimistic
     pose AUSSI un travail « cree ce contact chez Hektor ». Enchainee au geste
     mandant, HEKTOR LE CREERAIT DEUX FOIS. Un seul travail : celui du mandant.
   ⚠⚠ ET FREDERIC AVAIT RAISON : « il y a deja un worker qui fait cela ».
     J'avais conclu sur un GREP que le worker ne savait pas ou ranger le numero.
     En lisant la fonction EN ENTIER : il le RAPPORTE DEJA, sur l'etiquette
     provisoire. Ce qui manquait n'etait pas un mecanisme, C'ETAIT UNE ADRESSE.
     ~15 lignes copiees du geste voisin au lieu du gros chantier annonce.
     ➡ LIRE LA FONCTION, PAS LE GREP.
   EPROUVE : contact 20000002, lien n° 1 000 007, present_in_hektor = false
   (la vue attend la confirmation de Hektor -- voulu ; l'affichage immediat
   reste a l'etiquette provisoire). Le CONTACT, lui, existe tout de suite.
   4 services redemarres le 30/09 a 17:33, verifie par la date des PROCESSUS.
   ⚠ ~~ET « RETIRER UN MANDANT » N'EXISTE TOUJOURS NULLE PART~~ -> FAIT LE 03/10.

✅ G -- « RETIRER UN MANDANT » EST EN SERVICE ET PROUVE CHEZ HEKTOR   03/10/2026
   Le geste de Frederic du 30/09 : « le retrait PART chez Hektor tant qu'il vit,
   et la ligne RESTE chez nous, datee. » C'est ce qui tourne.
   LA CHAINE, prouvee de bout en bout a 20:22 et 20:23 :
      bouton -> RPC -> travail -> worker -> Hektor -> preuve -> registre -> ecran
      worker : {"status": "unlinked"}, 0 erreur · Hektor : ids [] sur 62963 ET 62964
      registre : retire_le + retire_par, DATE ET NOMINATIF · vue : 0 ligne
   LA REGLE TIENT : mandat genere -> bouton GRISE avec son motif (vu sur 18882,
   « le mandat n° 18882 a ete genere pour ce bien ») ; sans mandat -> actif.

   ⭐⭐ ET LES DEUX GESTES SONT MAINTENANT IMMEDIATS, DANS LES DEUX SENS.
      La vue exigeait `present_in_hektor` pour MONTRER un lien, mais n'exigeait
      rien pour le CACHER quand il etait retire -- deux poids, deux mesures dans
      la meme ligne de SQL. Un mandant qu'on venait de rattacher n'etait donc pas
      retirable avant le run de NUIT.
      Question de Frederic : « pourquoi 20 secondes ? Normalement c'est instantane
      si on ecrit chez nous. » -> la vue montre desormais aussi les liens nes dans
      l'app, et le worker les DEFAIT si Hektor refuse (annulerRattachementOptimiste,
      miroir exact de annulerRetraitOptimiste).

   ⛔ QUATRE DEFAUTS QUE SEUL L'ESSAI REEL POUVAIT TROUVER :
      · `unlink_hektor_mandant` n'etait reclame par AUCUNE file -- et il y a DEUX
        cartes, une en JS et une dans app_console_claim_next_job. Le travail serait
        reste « pending » A VIE, SANS erreur, pendant que l'ecran disait « retire ».
      · la preuve DEFAISAIT un retrait REUSSI : Hektor dit « aucun proprietaire »
        avec `"proprietaires": null` (cle PRESENTE, valeur nulle) et le script
        lisait ca comme « reponse illisible ».
      · le filet du rattachement ne couvrait QUE l'appel a Hektor -- le contexte
        negociateur (403) et la cible du contact passaient a cote.
      · la RPC ecrivait `role_hektor = 'mandant'` EN DUR : un lien sans mandat
        etait grise a tort. Corrige a la SOURCE -- role_hektor = null, et la vue
        derive le mot du numero de mandat (taxonomie du 24/07, un seul endroit).

   ⚠ CE QUI N'EST PAS PROUVE : le filet du RATTACHEMENT n'a jamais ete declenche
     en vrai. Celui du RETRAIT, si -- Hektor a refuse a 17:05, le lien est revenu.

✅ LE CONTRAT D'AUTORITE CESSE D'ETRE TACITE                        03/10  e284360
   Exigence du plan depuis le 30/09. Il EXISTAIT EN FAIT (l'adoption de retire_le
   depuis la doublure) mais PAS EN DROIT : rien ne verifiait qu'il tenait, et
   `doublure_du` n'etait QU'IMPRIME dans un bilan.
   LA REGLE, ECRITE : `retire_le`/`retire_par` APPARTIENNENT A L'APP -- le miroir
   ne peut pas les produire ; Hektor cesse de montrer un lien, il ne dit jamais
   « retire le 3 a 16h43 par Frederic ».
   DEUX GARDES AJOUTEES A LA SENTINELLE QUI EXISTAIT (relation_disparue.py) :
      ⑤ retraits_perdus    le cloud a un retrait que le serveur ignore
      ⑥ doublure_perimee   LA GARDE DE LA GARDE -- sans elle, ⑤ vaut zero EN MENTANT
   Eprouvees A L'ENVERS : 3 cas, dont 2 ou elles DOIVENT tomber.
   ⛔ Elles SURVEILLENT, elles n'ARBITRENT pas : le trio magasin/contrat/
     applicateur des trois autres objets n'existe toujours pas pour la relation.
```

### L9 LE REGISTRE DES MANDATS — *cinq lots le 06/10, tous eprouves A L'ENVERS*

```
LE DEFAUT, UN SEUL, TRAVERSANT CINQ ENDROITS
  Hektor resout `mandats[]` sur l'identifiant NU du mandat, ambigu entre les
  familles HEKTOR et PROTEXA (referentiel gele au n 18339). Il sert donc le
  corps d'un AUTRE mandat : 457 couples (annonce, numero) atteints.

4ec2e2d  LOT 1  la fiche annonce reprend ses MANDANTS chez nous          87
87364c1  LOT 2  le registre dit le PRIX la ou il ecrivait un montant   0 ecart/24 491
6e76d17  LOT 2b sans prix ET corps emprunte -> on ne dit rien    1 regression rattrapee
308fb70  LOT 3  app_mandat perd `montant`  -- le code
d946cb3         + Supabase (migration app_mandat_sans_montant_2026_10_06)
                + le local, fait par Frederic : 24 colonnes, 26 839 lignes, ok
037d956  LOT 4  le montant emprunte quitte la fiche annonce             88
829f86a         la note de chantier porte l'etat du soir
AUCUN deploiement front : tout se joue dans le PAYLOAD, React n'a pas bouge.

DEUX DE MES CHIFFRES SONT TOMBES SOUS LA MESURE -- a ne pas ressortir
  « 456 mandants empruntes » -> 87. J'avais compte les entrees qui PORTENT un
     mandant, pas celles qui portent le nom d'un AUTRE. 370 designent LA MEME
     personne ecrite autrement, et le texte de Hektor y est PLUS RICHE (adresse,
     parfois un co-mandant). PROUVE PAR UNE 3e SOURCE, le bloc `proprietaires`
     DE L'ANNONCE : il confirme notre nom 86 fois sur 86, celui de `mandats[]` 0.
  « etendre le masque » -> REFUSE par Frederic : « un masque, ce n'est pas une
     rustine ? » Si. Un masque cache sans reparer, et il faut le reposer a chaque
     nouvel endroit qui lit -- celui du 05/10 laissait deja passer deux chemins.
     On a mis LA VRAIE VALEUR a la place : le prix de l'annonce.

LA REGLE N'EST PAS LA MEME D'UN ECRAN A L'AUTRE, ET C'EST VOULU
  LE REGISTRE porte une colonne de NOMS SEULS -> notre liste gagne, rien n'est perdu
  LA FICHE    porte un texte qui contient AUSSI l'adresse -> on ne remplace QUE si
              nos noms n'ont AUCUN nom en commun avec celui de Hektor
  LE MONTANT  mandat COURANT + un prix -> le prix du bien ; mandat ANCIEN ou pas
              de prix -> on EFFACE (un prix d'aujourd'hui ne dit rien d'un mandat
              signe autrefois, et un montant efface n'etait pas celui de ce bien)

LES CONTROLES, tous eprouves A L'ENVERS (ils ECHOUENT sur la version d'avant)
  phase2/checks/fiche_annonce_mandants.py        mandants + montants de la fiche
  phase2/checks/registre_montant_est_le_prix.py  les 3 chemins du registre
  phase2/checks/chemin_immediat_paquet.py        non-regression du chemin immediat

CE QUI RESTE, hors serie
  [ ] 30 lignes dont personne ne connait les mandants
  [ ] mandat n 17842 de l'annonce 41629 : deux CHARBONNIER, 59 000 contre 53 000,
      meme date -- decision HUMAINE
  [ ] le contact d'essai 603953 pollue les mandants de l'annonce 24113
  [ ] rien n'est a l'ecran avant le run de nuit
LE DETAIL : notice/CHANTIER_REGISTRE_MANDATS_2026-10-06.md
```

### Les trois fronts ouverts — *ils avancent séparément*

| front | où c'en est | ce qui reste |
|---|---|---|
| **① L'IDENTITÉ** *(`L4` / `C.9`)* | la bascule contact est faite *(23/09)*, une annonce **naît dans l'app** depuis le 25/09 *(`e3` allumé)*, `C.9-f` en service la nuit du 26/09 | contrôler la ligne `[numero de bien dans la cle]` du run · surveiller la **1re annonce réelle** d'un négociateur · supprimer les annonces d'essai **63146** et **63147** |
| **② LES DOCUMENTS** *(`D.0`, l. 963 · `G.1`→`G.6`)* | 4 défauts fermés *(mandat/annexe, empreinte, frein, ajout autonome dormant)*. Le **rattrapage tourne seul** : tâche « GTI Rattrapage Documents » à 23 h, lots de 3 000 | **40 987 annonces**, ~14 nuits. Puis `G.2` `--detect` plafonné · `G.3` le ménage des 3 Go · `G.4` l'état doit suivre · `G.5` la RPC d'ajout |
| **③ LES PHOTOS** *(section **10bis**, l. 1163)* | **4 cases cochées le 26/09**, tout **dormant** : le coffre, le calibrage, l'adresse qui ne disparaît plus, le générateur | `G.13` générer les dérivés *(~18 Go, ~3 h)* · `G.14` le logo · `G.15` rebrancher les **48 points** avec repli · `G.16` les restes |

**Le détail des trois fronts est dans la liste, par numéro de ligne. Pas ici.**

### Ce que les photos ont appris le 26/09 — *les deux pièges qui ne crient pas*

> ⚠⚠ **La durée de cache doit valoir EXACTEMENT `max-age=N`.** Supabase parse cette forme
> et refabrique l'en-tête ; une forme plus riche *(`public, max-age=N, immutable`)* est
> ignorée **en silence** et le fichier ressort en `no-cache` — chaque affichage par un
> portail ou un email repasserait en **egress facturé**. Aucune erreur, rien dans les logs.
>
> ⚠⚠ **`upsertConsolePhotos` effaçait.** `if (rows.length)` gardait l'ajout mais **pas** la
> suppression : une liste vide rendue par Hektor emportait **toutes les photos de
> l'annonce**. Or l'`id` de cette ligne porte le chemin du fichier sur le serveur **et**
> l'adresse publique de ses dérivés. Corrigé en **delete-never**. *(Le plan parlait d'un
> `app_photo_id` : cette colonne n'existe pas.)*
>
> ➡ mémoire `photos-coffre-public-et-derives` · `photos-ligne-ne-disparait-jamais`

### ⛔ Ce qui attend Frédéric — *réécrit le 03/10, les anciens items étaient faits*

> ⚠ Les ① à ③ d'avant (redemarrer les 4 services · pousser le filtre du front ·
> `npm install sharp`) sont **FAITS et vérifiés le 03/10**. Une consigne périmée dans
> cette liste est pire que pas de liste : on la relit comme un ordre du jour.

```
① POUSSER                      cd C:\Hektor\Projet ; git push origin main
   dbbc99f (l'adoption des retraits) · 93a2055 (la reprise du run)
   ⚠ le serveur tourne DEJA dessus -- le run lit ce dossier. GitHub, lui, ne les a
     pas : rien n'est sauvegarde hors de cette machine.

② LE `busy_timeout` SUR pull_from_supabase.py
   Il n'en pose AUCUN, et la DESCENTE EST CE SCRIPT. Deux ecrivains sur
   phase2.sqlite sans filet -- c'est exactement la panne du 03/10 au matin, et
   elle ne serait pas arrivee avec lui.

③ UN GARDE-FOU D'ORDONNANCEMENT
   la descente (08:15) ne doit pas demarrer si le quotidien tourne encore.
   Depuis le correctif, le quotidien finit vers 07:40 -- mais c'est un FILET,
   pas une reparation : le jour ou une etape rallonge, on repasse dedans.

④ L'ESSAI `degroupproprio` -- JAMAIS EXECUTE A CE JOUR
   ⛔ il faut un VRAI BIEN D'ESSAI. 63175 a ete ecarte par Frederic le 03/10 :
     c'est le dossier d'un client. Les deux biens d'essai (63146, 63147) n'ont
     AUCUN mandant lie -- il faudra d'abord en rattacher un, ce qui eprouvera au
     passage le worker voisin.

⑤ allumer -EnqueueConsoleDocuments      ⛔ SEULEMENT APRES LE RATTRAPAGE
   dans run_quotidien.ps1                  (sinon on double le quota Hektor)
   ⚠ ETAT AU 03/10 : 20 653 marquees sur 23 153, ~2 500 restantes -> UNE nuit.
     La tache de 22 h EMPILE 2 500 travaux en 16 s ; ce sont les WORKERS qui les
     traitent ensuite. Un journal court n'est donc pas un echec.

⑥ relancer le rattrapage si la tache     <- enqueue_empreinte_lot.js
   de 22 h decroche                          ⚠ NE JAMAIS REJOUER une annonce en erreur
```

### Les 26 et 27/09 — *le chantier des fichiers*

```
G.8   ✅ l'ancre des six mois        colonne + fonction + pg_cron a 08 h 30
        13 438 vivantes · 74 550 sans ancre · 361 974 marquees · 0 incoherence
        garde-fou PROUVE au refus · idempotente · l'horloge ne repart pas
        ⚠ la PURGE reste, mais rien a purger avant mars 2027 (G.9)

G.13  ✅ les 74 550 derives fabriques   26/09 20 h 01 -> 22 h 00, 10,7 photos/s
        149 163 fichiers = 2,00 par photo · 17,7 Go · Supabase a 50,6 sur 100
        3 echecs 504 passagers, reprises par une relance

G.14  ✅ le logo des emails quitte Hektor   gti-photo/marque/logo-gti.png
        ⚠ l'enonce de la case etait FAUX : le worker embarquait deja son logo.
          Le vrai trou etait les EMAILS du backend, sans aucun repli.
        ✅ DEPLOYE le 27/09 : RENDER SE DEPLOIE TOUT SEUL sur un push vers main.
          Mesure : commit en ligne 61 s apres le push. La question traînait depuis
          le 26/09 faute de marqueur -- /health rend maintenant le commit qui tourne.

G.17  ✅ l'entretien du coffre        A le filet + B l'immediat
        A  une etape dans le run, apres le rapatriement (aucun redemarrage)
        B  le worker fabrique des qu'il range -- PROUVE EN REEL le 27/09 a 08 h 37 :
           travail pris en 3 s, done en 9 s, les deux derives refaits AUX MEMES
           ADRESSES. ⚠ l'interrupteur ne commandait RIEN avant ce raccordement.
```

⭐ **LE COFFRE PUBLIC EST PLEIN ET IL S'ENTRETIENT.** Ce qui manque n'est plus de le
remplir, c'est de le **lire** : les 44 points d'affichage pointent toujours chez Hektor.

### La nuit du 26 au 27/09 — *les trois runs*

```
23 h  rattrapage documents  ✅ PREMIERE REUSSITE : 3 000 empiles, 3 000 FAITS, 0 erreur,
                               8 h 17. Reste 37 988 annonces -> 12,7 nuits.
03 h  recherches actives    ✅ resultat 0 (elle avait echoue la veille)
05 h  quotidien             ✅ resultat 0, et l'etape photo a tourne POUR LA 1re FOIS :
                               36 photos rapatriees, 0 echec ; sonde : 0 manquante
```

⚠ **Et une nuit a suffi a ouvrir un trou** : ces 36 photos n'avaient aucun derive.
`G.13` etait un coup unique -> d'ou `G.17`. *Remplir le coffre n'a jamais suffi a le
tenir a jour.*

⛔ **CE QUI ATTEND ENCORE FRÉDÉRIC :**

```
① allumer -EnqueueConsoleDocuments  ⛔ APRES les nuits de rattrapage restantes
```

✅ **Les deux autres sont tombés le 27/09** : `G.15` a reçu ses feux verts *(front,
base, backend — tout est en ligne)*, et **le backend n'attend personne** — voir
ci-dessous.

> ⚠⚠ **RENDER SE DÉPLOIE TOUT SEUL sur un push vers `main`** — mesuré le 27/09 :
> **commit en ligne 61 s après le push**. On a cru pendant deux jours qu'un déploiement
> manuel manquait, uniquement parce que **rien ne permettait de le vérifier** : `/health`
> rendait une version écrite en dur, pas de `render.yaml` dans le dépôt, aucune clé API
> Render dans l'environnement. **`/health` rend maintenant le commit qui tourne**, la
> branche et l'heure de démarrage — donc la question ne se reposera plus.
> *(Vercel aussi : même mécanisme, `READY` en ~54 s.)*

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *pas seulement une priorité*

```
L9            ~~le registre se remplit DEPUIS LE MIROIR~~ -> FAIT : il lit app_mandat
              (interrupteur allume le 30/09), et le 06/10 ses MANDANTS et son MONTANT
              ont quitte Hektor. Voir la section L9 plus haut.
C.9-couple    seul moment ou l'on peut comparer NOTRE paire a celle de Hektor (c'est
              HEKTOR qui cree la 2e fiche du couple ; apres, personne ne le fera)
vitrine +     les liens PUBLICS deja diffuses (QR, imprimes) portent le n° Hektor ->
liens RDV     servir l'ancienne ET la nouvelle forme EN PARALLELE. Recouvrement, pas
              remplacement. (section 11bis)
G.15          ✅ FAIT LE 27/09 -- front, base, backend ET vitrine publique lisent nos
              photos, chacun avec repli sur Hektor. Le compte de depart (« 48 points »)
              etait 44 occurrences, puis SIX gestes. Rapatrier remplissait le coffre ;
              ca n'avait jamais suffi a AFFICHER.
```

**Les quatre doivent être finis AVANT la coupure, pas pendant.**

## 3. Avant de coder — la liste de relecture *(plan, l. 378)*

Elle existe *« parce que le 20/08 j'ai oublié trois fois un point déjà documenté »*.

1. La **section du plan** qui concerne la tâche — et ses voisines, les pièges y sont.
2. Les **notes citées** par cette section : elles portent les décisions déjà prises.
3. `notice/*.md` **et la racine**, par mot-clé — 123 notes, dont 111 ne sont citées nulle part.
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
  question posée — pas montrer que « ça marche ». *(plan, l. 27)*
- **Ne rien écraser.** Additif et chirurgical, jamais de remplacement massif.
- **Pas de code sans « go » explicite.** Un message court, en cadrage, est une **question**.
- **Stager fichier par fichier.** Jamais `git add .` : 73 fichiers non suivis traînent
  dans le dépôt.
- **Les 5 règles du projet** et **la règle des identifiants** : plan, lignes 2236 à 2270.
  *(un numéro ne se perd jamais · Hektor confirme, il n'écrase pas · une action a une fin
  visible · Hektor reste à jour tant qu'il diffuse · le miroir se met à jour, il ne se
  remplace pas)*

---

## 5. Les adresses

| | |
|---|---|
| le **pourquoi** | `notice/PLAN_DEV_ACTUALISE_2026-08-20.md` (2 278 l.) |
| le **quoi**, item par item | `notice/LISTE_TACHES_A_COCHER_2026-08-29.md` (6 500 l. — lire la page de tête, l. 1-44) |
| l'**historique** de la page de tête | `notice/JOURNAL_DE_BORD.md` — *un pourquoi, jamais un ordre du jour* |
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
   l'empilement qui l'avait porté à 467 lignes sur 609, avec trois états datés marqués
   *« ne jamais relire comme un ordre du jour »* : un document qui se contredit ne tient
   plus le fil. Ce qui sort du présent descend dans `notice/JOURNAL_DE_BORD.md`.
2. **Réécrire la mémoire de reprise** (`reprise-…` dans le dossier mémoire), toujours la même,
   jamais une nouvelle par date. *Elle datait du 02/09 alors que 68 commits avaient suivi.*
