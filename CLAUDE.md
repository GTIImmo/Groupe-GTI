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

### ✅ A.3-TECHNIQUE EST CLOS — *30/09/2026* (c'est `L9`, pas `L6` : j'ai mal
###    etiquete mes messages toute la session, le plan fait foi)

```
A ✅ 26 826 mandats dans le cloud + doublure     de7c57b · c560955
B ✅ deux sentinelles, DEUX AXES                 44c2e9b
     mandat_disparu   serveur <-> Hektor    mandat_un_numero  serveur <-> cloud
C ✅ le registre tire sa matiere de app_mandat   f4c4f5a · 2ed0538
     24 025 -> 24 478 lignes, +451 murs commerciaux, SANS vider la table
D ✅ le mandat entre au registre A LA SECONDE    b45f36a
     4 services redemarres 09:25, verifies par la date des PROCESSUS
```

⚠ **CE QUI RESTE DE `L9` N'EST PAS TECHNIQUE** : les trois couches de
numerotation et la serie propre appartiennent a la PHASE 2 (registre
electronique legal) -- juriste + horodatage tiers. Le numero vient toujours de
PROTEXA, et c'est la decision de Frederic du 29/09.

⭐ **ET LE MANDAT N'EST PAS AU NIVEAU DE L'ANNONCE, mesure du 30/09** : il l'a
rattrapee sur la MEMOIRE, il est loin derriere sur les GESTES.
```
                    ANNONCE  contact  MANDAT
gestes du worker          9        9       2
RPC du front              9       17       1
sentinelles               5       11       2
carnet de champs app     oui      oui   1 champ, 2 lignes
```
On sait CREER un mandat, pas le CORRIGER. C'est `L5` / `E.0-bis`, ou le geste
est deja inscrit -- la mesure y a ete ajoutee le 30/09, la ligne PAS dupliquee.

### 🗄 L'ANCIEN CADRE DU CHANTIER — *pose le 29/09, garde pour le pourquoi*

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
   G ✅ LA TABLE SAIT REFAIRE LE REGISTRE                30/09  cccaeac · 0522f4a · 2bc628d
        4 colonnes neuves -- versions_json / version_count / avenants_json /
        avenant_count -- parce que L'ECRAN LES LIT DEJA (« +N versions »,
        les avenants). Sans elles la bascule ferait perdre deux fonctions.
        ⚠⚠ ET LA SOURCE ETAIT FAUSSE, l'outil de controle l'a montre :
           app_mandat lisait hektor_mandat, qui ACCUMULE ; le registre lit le
           tableau `mandats` du DETAIL (« les mandats de CE bien, MAINTENANT »).
           Sur 28 couples la table voyait deux VERSIONS la ou il y a deux
           MANDATS DIFFERENTS partageant un numero (n° 14856 : 2011/59 000 EUR
           et 2022/160 000 EUR) -- et choisissait entre deux dossiers etrangers.
        TROIS SOURCES, de la plus riche a la plus pauvre, la pauvre ne COMBLE :
           detail 24 666 · hektor_mandat 88 (ce que le detail a oublie) ·
           no_mandat 2 072 = 26 826 lignes, 0 neuf, 0 renumerotation.
        ⚠ « 0 » VAUT VIDE (171 montants, 189 dans l'historique) -- piege du DPE.
          MAIS LE NETTOYAGE NE VOTE PAS : nettoyer avant le score changeait le
          CLASSEMENT donc la version retenue (annonce 59279). Le score note la
          matiere brute, le « 0 » ne tombe qu'a l'ecriture.
        MESURE, registre_depuis_app_mandat.py sur les 24 025 lignes :
           ce qu'on PERDRAIT 0 · le GAIN 453 · ecart sur 13 colonnes / 14 : 0
           la 14e (historique) : 189 ecarts, 189 sur 189 sont « 0 » -> vide
        sentinelle inchangee : doublons 0 · plage 0 · miroir_absents 0
        ==> IL RESTE : le push (⛔), l'oeil serveur<->cloud, la bascule des
            11 colonnes de la vue (⛔), la doublure, l'ecriture worker (⛔).
            LA VUE ET SES 4 FONCTIONS NE SONT PAS TOUCHEES : elle lit UNE
            table, on change seulement d'ou le fabricant tire ses colonnes.

   A ✅ LE PUSH -- FAIT LE 30/09                          de7c57b · c560955
        mandat_ledger.py --push (delete-never) + --push-a-blanc.
        ⛔ GARDE-FOU DANS LE CODE : --push sans --refresh est REFUSE (lecon du
          07/09, ledger d'affaires : un push seul a efface une annulation de
          compromis faite une heure plus tot). Levable, assume.
        Essai a blanc sur la table reelle : 26 826 lignes, 25 colonnes remplies.
        PATCH COLLE PAR FREDERIC : 25 colonnes, les 5 presentes.
        POUSSE : 26 826 lignes, verifiees EN LIGNE -- numeros distincts 26 826,
        plage envahie 0, sans versions_json 0, plusieurs versions 121, avenant 1.
        DOUBLURE descendue en 16 s (app_mandat__sb), sans une ligne de code.
        LES DEUX SENTINELLES SONT VERTES.
        ⚠ CORRECTIF DANS L'OEIL : mesure EN MEMOIRE, plus en SQL. Un CAST des
          deux cotes d'une jointure ecarte TOUT index -- la sonde tournait plus
          de DEUX MINUTES et finissait coupee. 0,209 s desormais.

   D ✅ LE MANDAT NAIT DANS L'APP -- EN SERVICE LE 30/09 a 09h25   b45f36a
        ① patch COLLE : le defaut vaut nextval('app_mandat_id_app_seq'),
          sequence a 1 000 001. Eprouve avant : sans numero -> plage app,
          avec numero -> conserve tel quel.
        ② 4 SERVICES REDEMARRES le 30/09 a 09:25:45-47 -- et VERIFIE autrement
          que par « Running » : date de creation des 4 processus (CIM), toutes
          POSTERIEURES a la modification du fichier (09:17:42). Les quatre
          rendent `idle`, sans erreur, battement a la minute.
          ⚠ « Running » ne prouve RIEN sur le code charge : un service jamais
            redemarre est Running lui aussi. C'est l'heure du PROCESSUS qui
            prouve, pas l'etat du service.
        ⭐ L'ADOPTION est posee, et sans elle LE RUN S'ARRETERAIT : le run
          reprend le numero du cloud au lieu d'en fabriquer un second pour le
          meme couple (l'arret sur index unique des 01 et 02/09).
        Le worker n'ecrit QUE annonce/numero/type/date -- famille et nature sont
        des regles Python, les recopier en JS en ferait une copie qui derive.

   ⭐ LE REGISTRE EST POSE -- 30/09 a 09h42, EN PLEINE JOURNEE      2ed0538
      registre_mandats_upsert.py, et le choix de l'outil EST le sujet :
      `--rebuild-register-only` VIDE la table puis la refait (« jamais quand
      l'agence consulte »). Or register_row_id est la CLE PRIMAIRE : un UPSERT
      fait le meme travail sans fenetre noire -- 453 en INSERT, 24 025 en
      UPDATE, et a aucun instant le registre n'est vide.
      Ce qui l'autorise est MESURE : « vue locale MOINS fabricant = 0 », aucune
      ligne orpheline, donc rien a supprimer.
      ⚠ NE REMPLACE PAS la reconstruction : elle reste la bonne reponse quand le
        registre est CORROMPU -- seule une table videe garantit qu'il ne reste
        rien de l'ancien etat.
      AVANT -> APRES, en ligne :
         lignes         24 025 -> 24 478    offre_type 10   74 -> 525
         montant « 0 »     171 ->      0    « 0 » en historique -> 0
         sans search_text          0        cles distinctes 24 478
      LA VUE DU FRONT : 24 478 lignes, 121 a plusieurs versions, 1 avenant,
      groupes de tri 0 et 1. Ses 70 colonnes et ses 4 fonctions n'ont pas bouge.
      ℹ La copie LOCALE du registre reste a 24 025 : elle se realignera au run.
        Seul registre_depuis_app_mandat.py la lit -- sans consequence.

   B ✅ L'OEIL SERVEUR <-> SUPABASE                               30/09  44c2e9b
        phase2/checks/mandat_un_numero.py + data.mandat_un_numero dans la sonde.
        Pendant exact de annonce_un_numero (C.9-b).
        ⚠ PAS LA MEME GARDE QUE mandat_disparu, et les deux servent :
             mandat_disparu    serveur <-> Hektor (l'etape de nuit passe-t-elle ?)
             mandat_un_numero  serveur <-> Supabase (le push passe-t-il ?)
        ROUGE tant que le push n'a pas eu lieu -- voulu, comme mandat_disparu.
        ⭐ LA DOUBLURE NE DEMANDE AUCUN CODE : pull_from_supabase lit le SCHEMA
          et descend tout ; app_mandat -> app_mandat__sb. La tache n'existait pas.

   C ✅ LE REGISTRE PREND SA MATIERE DANS app_mandat              30/09  f4c4f5a
        LA VUE N'EST PAS TOUCHEE -- elle lit UNE table et ignore d'ou vient la
        donnee. Ses 70 colonnes et ses 4 fonctions front ne changent pas.
        LE DEFAUT REPARE : le fabricant filtrait sur le STATUT de l'annonce ; une
        annonce sans detail sortait du registre AVEC SON MANDAT.
        GAIN +453, dont 451 MURS COMMERCIAUX (offre 10 / idtype 23), avec prix et
        numero -- 452 des 453 annonces archivees ET sans detail.
        MESURE des deux constructions : 24 025 -> 24 478, 0 PERDUE ; les seules
        colonnes qui bougent sont celles ou « 0 EUR » devient vide (171 + 189 +
        189, la meme regle trois fois). Aucune identite, version ni tri ne change.
        DEUX PIEGES FERMES : le push CIBLE emprunte le meme socle (sinon il
        effacait en journee ce que la nuit gagnait) ; le fabricant RETRIAIT des
        versions deja triees, et le nettoyage se remettait a voter.
        INTERRUPTEUR APP_REGISTRE_DEPUIS_APP_MANDAT=0 pour revenir en arriere.

   D 🟡 le worker ecrit apres step5  <- la table Supabase est POSEE (53aa132),
        reste : le push, l'adoption, l'ecriture worker, la doublure
        ⚠ L'ARCHITECTURE A CHANGE, SUR UNE REMARQUE DE FREDERIC : app_mandat ne
          vient PAS s'ajouter a cote du registre -- LE REGISTRE DEVIENT SA
          PROJECTION. Une source, deux robinets (le miroir et l'app), jamais
          deux copies. C'est le patron de app_affaire_ledger : j'en avais copie
          la FORME sans copier sa PLACE.
        audit des 68 colonnes de la vue : 11 seulement viennent du mandat,
        27 de l'annonce, 15 techniques -> on ne remplace pas la vue, on change
        la source de ses 11 colonnes.
   D-bis  LA TAXONOMIE, mesuree le 29/09 (3f99c13)
        VENTE 23 521 · LOCATION 2 084 · INCONNUE 883 · GESTION 271 · RECHERCHE 63
        ⚠ `nature` (ce qu'EST le mandat) n'est PAS `famille` (de quel REGISTRE
          vient le numero : HEKTOR / PROTEXA) -- deux axes, comme les couleurs
          et les lettres de la carte A1.
        ✅ LE PERIMETRE EST DEJA JUSTE, ET FREDERIC L'A CONFIRME JURIDIQUEMENT :
           les 271 GESTION relevent de la CARTE G (registre-repertoire), pas du
           registre des mandats de la carte T -- elles doivent donc etre exclues,
           et elles LE SONT deja : toutes sur des annonces de LOCATION.
           Les 63 RECHERCHE sont sur vente ou commerce, donc DEDANS. Le filtre
           sur le type d'offre les separe tout seul, sans le savoir.
           ➡ RIEN A CHANGER AU PERIMETRE.
        ✅ LA FAMILLE : C'ETAIT DEJA AUDITE, ET J'AI EU TORT DE LA DIRE FRAGILE.
           Feuille de route du 24/08 : `params[typeMandat]` vaut « mandat » ou
           « protexaMandat » -- « faux ami : ce n'est PAS le type juridique mais
           LA FAMILLE DE REGISTRE ». Et plan l. 1170 : « les deux familles de
           registre (SIMPLE/EXCLUSIF/ACCORD -> HEKTOR ; libelle francais ->
           PROTEXA), VERIFIE 10/10 » (25/08).
           _famille() code EXACTEMENT cette regle. Elle n'est pas inventee.
        ⚠ Le doute ne porte QUE sur les lignes SANS TYPE : 3 263, dont 2 342
          locations (hors perimetre, sans importance) et 921 dedans. Pas sur
          les 24 000. Et il ne bloque RIEN : au moment d'une offre, le worker
          LIT la valeur chez Hektor au lieu de la deduire (correctif du 25/08).
        ⛔ J'AVAIS ECRIT « l'export PROTEXA est bloquant des DEUX phases » :
          FAUX, DEUX FOIS. (1) c'etait une urgence fabriquee ; (2) ce n'est meme
          pas « un mail » -- PROTEXA a SES PROPRES IDENTIFIANTS, enregistres DANS
          Hektor (protexa-login / protexa-mdp / protexa-saveProtexa). C'est un
          compte A TOI, pas un tiers a qui ecrire.
          ==> il ne sert qu'a UNE chose : savoir OU REPRENDRE LA SERIE le jour ou
              notre registre remplacera PROTEXA -- donc au DERNIER temps.

   ⭐⭐ LE PRINCIPE, GRAVE PAR FREDERIC LE 29/09 :
      LE REGISTRE ELECTRONIQUE EST LE DERNIER TEMPS. La phase 1 GARDE le principe
      actuel sans exception : PROTEXA fabrique le numero, le worker ne change pas,
      notre table ENREGISTRE et ne decide de rien.
      -> tout ce qui touche au NUMERO (continuite de la serie, export PROTEXA,
         compteur verrouille) appartient a ce dernier temps. Pas avant.

   ℹ ET LA DIRECTION ETAIT DEJA PRISE LE 28/08, dans le worker (C.13) :
      « la cloture du mandat n'ajoute rien de son cote, c'est une ecriture dans
        SON registre a lui. LE NOTRE DEVIENT LE REGISTRE QUI FAIT FOI. »
      « ce que ca coute, et c'est assume : tant que Hektor vit, son registre dira
        le mandat ouvert quand le notre le dira clos. »
      app_mandat ne fait que donner un CORPS a cette decision.
   F ⛔ (devenue) LA REPARATION est FAITE -> voir plus bas
   F ✅ LA REPARATION, FAITE le 29/09 a 13 h -- ACCORD DE FREDERIC
        push_upgrade_to_supabase.py --rebuild-register-only
        elle VIDE le registre puis le refait DEPUIS LE MIROIR ENTIER
        (verifie : dossier_ids=None -> aucun filtre ; c'est elle qui a produit
         l'etat du 31/07). Les 635 reviennent ET les 23 091 lignes figees se
         rafraichissent du meme coup.
        ⚠ pendant l'operation le registre est VIDE : jamais pendant le run de
          nuit, jamais quand l'agence consulte.
        RESULTAT : 23 839 -> 24 021 lignes, et PLUS AUCUNE ligne figee au 31/07.
        77 des 80 mandats en cours recuperes. exit 0.
        ⭐ ET UNE SECONDE PREUVE DU CORRECTIF DU COPIEUR : la descente de cette
          table a ajuste sa page deux fois (8 Mo -> 500 lignes, 4 Mo -> 250) --
          LE SCENARIO EXACT qui le cassait -- et a ramene les 24 021 completes.
        ⚠ LES 3 « EN COURS » RESTANTS NE SONT PAS DES PERTES : 1 mandat
          ANTERIEUR sur une annonce qui en a un plus recent, 2 annonces
          ARCHIVEES dont la date de fin n'est pas encore passee.

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

   C 🔺 LA PROJECTION DES ACQUEREURS -- REMONTEE, mon refus reposait sur un
        chiffre FAUX. J'avais annonce « projeter perdrait 791 lignes ».
        ⛔⛔ TROIS ERREURS DANS MA MESURE, dont une grosse :
          `acquereurs_json` est tantot une LISTE, tantot un OBJET SEUL, et mon
          code faisait `if not isinstance(items, list): continue` -- il
          SAUTAIT EN SILENCE 11 151 affaires sur 30 358 (37 %).
          parties lues 23 798 -> 34 949 en realite.
        LE VRAI CHIFFRE : le ledger connait 16 080 des 16 253 couples (98,9 %),
        CO-ACQUEREURS COMPRIS (affaires a 2, 3, 4, 5 et 6 acquereurs).
        RESTE 180 couples, TOUS des compromis -- non compris a ce jour.
        ⚠ ET LA TRADUCTION S'ENRICHIT : le ledger connait des correspondances
          que app_contact_identite_app ignore (ex. 458 -> 10000231).
          62 038 -> 63 222 ; non traduisibles 828 -> 189.
        ➡ LECON : « un total ne se compare pas, il se DEPLIE ». J'ai compare
          23 798 a 34 925, vu un ecart, et conclu -- sans deplier d'ou il
          venait. Il venait de MON code.

   D ⬜ LES 45 LIENS « APP SEULE » Y ENTRENT (app_relation_app_seule, le filet
        existe et dit lui-meme « jamais reinjectes »).

   E ⬜ LES 3 FONCTIONS RESTANTES AU DEPOT (app_update_mandant_contact_optimistic
        + les 2 fabriques de travail) -- elles n'existent qu'EN PRODUCTION.

⭐ AJOUTE PAR FREDERIC LE 30/09 -- « CREER UN CONTACT ET LE RATTACHER »
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
   LE CHANTIER : que app_create_mandant_contact_optimistic fasse NAITRE le
   contact d'abord (notre numero), PUIS pose le lien durable avec ce numero,
   PUIS le travail pour le worker -- qui ne change pas d'une ligne.
   ⚠ ORDRE IMPOSE : le contact AVANT le lien. Un lien ne se pose pas sur
     quelqu'un qui n'existe pas encore.
   ⚠ ET « RETIRER UN MANDANT » N'EXISTE TOUJOURS NULLE PART -- c'est un ecran
     a faire, pas une table. Frederic a tranche le 30/09 : le retrait PART chez
     Hektor tant qu'il vit, et la ligne RESTE chez nous, datee.
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
