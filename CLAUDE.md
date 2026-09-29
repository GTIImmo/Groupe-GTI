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

**Mis à jour le 26/09/2026 (après-midi).**

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

### ~~LE FRONT PRINCIPAL~~ — *finir l'annonce* (posé le 28/09, CLOS le soir même)

> **Le niveau à atteindre n'est pas une opinion** : c'est ce que le contact, la recherche et
> la transaction possèdent **déjà**. Tableau comparatif et détail : plan maître, section
> **« FINIR L'ANNONCE »**.

```
N.1  LA CAMPAGNE DES CHAMPS              mesure seule, aucun code -- BLOQUANTE
     !! ELLE RETRECIT : LA CLASSIFICATION EXISTE DEJA, depuis le 19/08.
        notice/A1_CHAMPS_PROPRIETE_APP_2026-08-19.md -- 189 champs, en COULEURS
        (VERT l'app est l'auteur / BLEU Hektor produit / ORANGE 3 arbitrages).
        189 REMESURE dans le worker le 28/09 : 27 + 26 + 136. La carte n'a pas bouge.
     !! DEUX VOCABULAIRES, DEUX AXES, aucun ne remplace l'autre :
        COULEURS = qui est l'auteur   -> commandent la DESCENTE (l'import reecrit-il ?)
        A / B / C = Hektor accepte-t-il -> commandent le PUSH
        A/B/C a ete fait sur l'AFFAIRE (0.1, close 18/09), JAMAIS sur l'annonce.
     (b) LA CORRESPONDANCE : FAITE le 28/09 -- 189 sur 189, ZERO absent (7acebc6)
         correspondance_champs_annonce.py, lecture seule.
         170 un seul / 9 AMBIGUS / 3 par suffixe / 7 a la main.
         TROIS rangements : 163 colonnes + 134 cles de blob + 216 noms sous
         un porteur « props » (API) ou « fields » (capture de console).
         !! LE PIEGE POUR (a) : titre_bien est un COALESCE qui prefere le
            LISTING au DETAIL -> relire texte_principal_titre, pas titre_bien.
            Les 9 AMBIGUS sont le meme risque : relire la mauvaise cible rend
            un verdict faux SANS RIEN SIGNALER.
     (a) DISSOUTE le 28/09 : AUCUN champ n'est creable sans etre corrigible.
         HEKTOR_WIZARD_UPDATE_GROUPS existe depuis le 02/06/2026 (a2e8160).
         Remesure : 177 des 189 couverts par les groupes ; 8 par la voie
         cleanfield, 3 par applyHektorChauffage. RESTE les 4 mandate_*,
         qui sont le geste L5 « modifier un mandat existant ».
         !! Le « 102 champs non modifiables » du plan venait de comparer
            deux listes ECRITES DANS DEUX LANGUES (creation = vocabulaire
            Hektor, modification = vocabulaire app) -> ecart de 136.
            MEME famille d'erreur que « les couleurs ne sont pas des lettres ».
     ==> N.1 EST CLOSE. La protection ne passe pas par A/B/C mais par le
         MODELE B : pousser, RELIRE, montrer le verdict. Donc N.2 puis N.3.
N.2  LE VERDICT AU CARNET                les 4 colonnes que l'affaire a deja
N.3  LE FRONT ECRIT AU CARNET            il ne capte que 3 GESTES, pas les saisies
N.4  LE CORPS LOCAL PERSISTANT           26bis-3
     !! MESURE 28/09 : POUR UN BIEN VIVANT, LA DOUBLURE EST COMPLETE.
        189 champs sur 189 presents = 70 colonnes app_dossiers_current
        + 134 cles du blob + 216 noms sous props/fields.
        Ce qui trompe, c'est les 70 colonnes : le reste est DANS LE BLOB.
     !! LE TROU N'EST PAS OUVERT : 0 annonce de la copie manque a la vue
        (mesure DEUX FOIS, deux chemins). Il s'ouvrira quand Hektor cessera
        de donner un numero a la naissance -- pas avant.
     ==> LE VRAI SUJET EST AILLEURS ET PLUS URGENT :
        le detail des 34 515 ARCHIVES n'existe QU'EN UN EXEMPLAIRE, dans
        data/hektor.sqlite (3,9 Go). La doublure n'en descend qu'un index
        de 35 colonnes. Ce n'est pas un oubli (regle « serveur=tout /
        cloud=biens vivants », et la REGLE 5 protege le miroir).
        !! MAIS il n'entre PAS dans la sauvegarde auto : niveau 4, --full,
           « sur demande ». run_backup.ps1 passe --weekly, JAMAIS --full.
           -> a trancher : l'ajouter, ou confirmer que l'agent OVH le prend.
```

Ordre **N.1 → N.2 → N.3** ; **N.4 en parallèle**.

⚠⚠ **NE PAS REDÉCOUVRIR CE QUI EXISTE** *(erreur commise le 28/09 au matin)* : l'annonce a
**déjà** son œil *(`C.9-b`, `annonce_un_numero` — 0 écart sur 13 439)* et **quatre
sentinelles** *(un_numero · conflit · partielle · push_bloque)*, toutes à 0. Et
`data.annonce_partielle` détecte **déjà** un champ ignoré par Hektor — c'est-à-dire la
classe A, en *critical*, seuil zéro.

**Quand ces quatre-là sont faites, il ne reste que** : le registre des mandats *(`L9`)* · la
génération du numéro de mandat *(`L6`)* · la signature *(`A.2`)* · les passerelles *(`A.1`)*.

### 🔴 LE CHANTIER SUIVANT — *le registre des mandats* (cadre pose le 29/09)

> **DEUX PHASES, dans l'ordre de Frederic** -- il a corrige le mien : je faisais
> dependre le petit chantier du gros.

```
PHASE 1  NOTRE REGISTRE, LA DONNEE SEULE     4 etapes sur 5 FAITES le 29/09
   !! HEKTOR ET PROTEXA NE BOUGENT PAS : le numero vient toujours d'eux.

   A ✅ app_mandat, table durable, DORMANTE            ffee94d · 7183934 · 39374bf
        26 822 lignes = 24 750 fiches mandat + 2 072 numeros portes par
        l'annonce (2e source, trouvee par le 4e controle : le registre en a
        DEUX, je n'en lisais qu'une).
        CLE = (annonce, numero_mandat). ⚠ PAS hektor_mandat_id : Hektor range
        le MEME mandat sous plusieurs ids (annonce 1972/n° 17925 -> 3 ids).
        Controles : 0 doublon · 0 trou · 0 dans la plage reservee ·
        REJEU a empreinte identique (d96c01ec...).
   B ✅ branchee dans le run                                        e26b2e4
        UNE etape neuve, non bloquante, apres le ledger d'affaires.
        ⚠ PAS de doublure pour l'instant : rien n'ecrit encore dans
          app_mandat cote Supabase -- elle viendra AVEC l'etape D.
   C ✅ le registre ne suit plus stale_ids -- il CONSERVE            6c790eb
        LA SEULE modification d'existant. Les QUATRE autres tables la suivent
        toujours. Retour arriere : remettre `set(stale_ids) |`, un jeton.
   E ✅ la sentinelle data.mandat_disparu                           40edc35
        formule en copie unique (phase2/checks/mandat_disparu.py), patron
        de check_annonce_un_numero. Eprouvee hors du moniteur, sans alerte.
        ⚠ ROUGE DES LE 1er JOUR, et c'est voulu : 80 mandats EN COURS absents.
   D ⛔ le worker ecrit apres step5 + la doublure  <- REDEMARRAGE DES 4 SERVICES
   F ⛔ LA REPARATION : reconstruire le registre  <- ACCORD + FENETRE CALME
        push_upgrade_to_supabase.py --rebuild-register-only
        elle VIDE le registre puis le refait DEPUIS LE MIROIR ENTIER
        (verifie : dossier_ids=None -> aucun filtre ; c'est elle qui a produit
         l'etat du 31/07). Les 635 reviennent ET les 23 091 lignes figees se
         rafraichissent du meme coup.
        ⚠ pendant l'operation le registre est VIDE : jamais pendant le run de
          nuit, jamais quand l'agence consulte.
        ⚠ SANS ELLE, LA SENTINELLE RESTE ROUGE ET TU RECOIS UNE ALERTE PAR JOUR.
          C'est elle qui fait passer data.mandat_disparu au vert -- et qui prouve
          la chaine entiere : la table dit vrai, la sentinelle le voit, la
          reparation corrige, la sentinelle le confirme.

   LE CHIFFRE, ET IL A ETE CORRIGE TROIS FOIS PAR FREDERIC :
      2 983 absents du registre ... dont 2 348 LOCATIONS, ecartees par sa
      decision du 26/08 -> LA VRAIE PERTE EST 635, dont 80 EN COURS.
      ⚠ la table porte TOUT ; c'est la VUE qui filtre. Publier la table telle
        quelle mettrait 2 348 locations dans un registre qui les exclut.
   ==> AUCUN RISQUE JURIDIQUE : tant que PROTEXA fait le numero, c'est LUI
       le registre legal. Le notre n'est qu'un outil de travail.

PHASE 2  LE REGISTRE ELECTRONIQUE LEGAL         ~3-4 sem.  ⛔ CONFORMITE
   decret 72-678 art. 65 : « cote sans discontinuite », le numero « reporte
   sur l'exemplaire qui reste en la possession du mandant », forme
   electronique permise « dans les conditions des articles 1365 et suivants
   du code civil » (depuis le decret du 21/10/2005).
   !! AUCUNE regle technique dans les textes : le code civil exige
      (1) identifier de facon certaine l'auteur  (2) garantir l'INTEGRITE
      -> c'est une obligation de PREUVE, pas une liste a cocher.
   !! TROIS CORRECTIONS imposees par la recherche du 29/09 :
      · le prefixe « RE- » est probablement INTERDIT (« ni prefixe ni suffixe »)
      · repartir de 1 est risque -> CONTINUER la serie ou PROTEXA s'arrete
      · l'horodatage tiers n'est PAS optionnel : sans date certaine,
        LE MANDAT EST NUL
   Sanctions : 2 ans + 3 000 € + retrait de carte + mandat nul (pas d'honoraires)
```

⭐ **CE QU'IL NE FAUT PAS TOUCHER** : les 5 etapes du worker SONT l'assistant
PROTEXA, rejoue faute d'API. La note du 18/05 : la separation est VOLONTAIRE,
« Hektor consomme un vrai numero a la validation ». **Et la porte unique existe
deja** : le front appelle UNE RPC, envoie la description du mandat, et ne recoit
JAMAIS de numero -> le jour de la bascule, le front ne change pas d'une ligne.

⛔ **NE DEPEND PAS DE MOI** : l'export de la serie PROTEXA (un mail, bloquant --
23 numeros sans trace chez nous) · la validation par un juriste · le choix du
tiers d'horodatage.

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

### ⛔ Ce qui attend Frédéric — *rien de tout ça ne se fait sans lui*

```
① REDEMARRER LES 4 SERVICES              <- rend G.10bis actif. Tant qu'il n'est pas
   HektorConsoleWorker Actions/Admin/        fait, le worker CONTINUE DE SUPPRIMER.
   Documents/SyncLight                       ⚠ EN JOURNEE 06 h - 22 h, JAMAIS 23 h - 05 h
                                             (un job laisse « running » 30 min passe en
                                             erreur, et les erreurs sont ECARTEES A VIE
                                             du rattrapage)
② POUSSER                                <- deploie le filtre du front (commite, pas pousse)
③ npm install sharp dans Console/        <- avant d'allumer G.11
④ allumer -EnqueueConsoleDocuments       <- ⛔ SEULEMENT APRES LE RATTRAPAGE (sinon on
   dans run_quotidien.ps1                   double la consommation du quota Hektor)
⑤ relancer le rattrapage si la tache     <- enqueue_empreinte_lot.js, lots de 3 000
   de 23 h decroche                          ⚠ NE JAMAIS REJOUER une annonce en erreur
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
L9            le registre des mandats se remplit DEPUIS LE MIROIR -- impossible apres
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
