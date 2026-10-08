# Journal de bord — l'historique de la page de tête

> Ce fichier existe pour une raison simple : **la page de tête de `CLAUDE.md` avait grossi
> à 467 lignes sur 609**, et elle portait quatre états datés dont trois étaient marqués
> *« ne jamais relire comme un ordre du jour »*. Un document qui se contredit lui-même ne
> tient plus le fil.
>
> **Ce qui est ici est de l'HISTOIRE, pas un ordre du jour.** On l'ouvre pour comprendre
> *pourquoi* une décision a été prise, jamais pour savoir quoi faire. Le présent est dans
> `CLAUDE.md` §2 ; le détail par tâche est dans `notice/LISTE_TACHES_A_COCHER_2026-08-29.md`.
>
> Déplacé ici le 26/09/2026. Rien n'a été récrit : les blocs sont tels quels, du plus
> récent au plus ancien.

---

## 08/10/2026 — *l'ancien §2 de `CLAUDE.md` (état du 07/10 : audit complet, 46 chapitres)*

> ⚠ **Cette section porte LE PRÉSENT, et rien d'autre.** Règle : en fin de session, on la
> **RÉÉCRIT**, on ne l'empile pas ; ce qui en sort descend dans **`notice/JOURNAL_DE_BORD.md`**
> *(l'état du 03/10 au 06/10 y est descendu le 07/10 : run réparé, retirer un mandant, L9…)*.

**Réécrit le 07/10/2026, après l'audit complet** —
`notice/AUDIT_AUTONOMIE_COMPLET_2026-10-07.md` *(10 dimensions, chaque constat grave remesuré
par un contradicteur, puis un contrôle de complétude ; lecture seule)*.

### Le verdict, en quatre lignes

```
L0 ✅  L1 🟡  L2 🟡  L3 ✅  L4 🟡  L5 ⛔  L6 ⛔  L7 🟡  L8 ⛔  L9 🟡  L10 ⬜
L'ETAPE 2 N'EST PAS TERMINEE. La memoire est a nous, et MODIFIER marche sans Hektor.
CREER, mettre sous mandat, ajouter un fichier, valider pour la diffusion : encore Hektor.
Personne ne saisit dans l'app : 0 travail demande par un commercial en 120 jours.
```

### Le chantier : l'audit est DANS le plan, pas à côté *(décision du 07/10)*

| où | quoi |
|---|---|
| plan, section « 🔎 L'AUDIT COMPLET DU 07/10 » | où va chaque point · **les 8 questions à Frédéric** · **🧭 LES 46 CHAPITRES**, la liste que le dev suit *(proposée le 07/10, à valider)* |
| `notice/CHAPITRES_AUTONOMIE_PROPOSITION_2026-10-07.md` | le détail de chaque chapitre (ordre interne, prérequis, feu vert, critère de fin) |
| plan, lots | **L1 et L2 rouverts** · lot **`L10` « Préparer la coupure »** créé |
| liste, section 13 | les 16 tâches de `L10` |
| liste, section 12 | hors code : A.1 → A.5 *(A.4 DNS et site, A.5 leads : neufs)* |
| liste, cases existantes | G.1→G.6, 26bis-3, C.9-couple, C.13-c, E.0-bis, E.1, E.2, F.1, 11bis ①, A.3 : annotées « ↳ 07/10 » |

### Les fronts

| front | où c'en est | ce qui reste |
|---|---|---|
| **① IDENTITÉ / NAISSANCE** *(L4 · L10-1 · L10-2)* | le stock est 100 % sous nos numéros ; contact et annonce savent naître (e3 allumé) | n° Hektor de l'annonce `NOT NULL` dans 16 tables ; recherche seulement provisoire ; C.9-couple : sonde prête, geste humain |
| **② LES DOCUMENTS** *(`D.0`, l. 963 · G.1→G.6)* | rattrapage à 21 h, lots de 2 500, 0 erreur | ≈ 10 650 annonces (≥ 6 nuits) ; **G.1-b les brouillons échoueront** ; parc vivant figé depuis le 20/08 (G.2 puis G.6) ; G.5 devenu bloquant |
| **③ LES PHOTOS** *(section **10bis**, l. 1163)* | affichage 100 % chez nous (74 992 photos du parc vivant) | ajouter / retirer / réordonner chez nous (G.5, E.0-bis) ; 350 retraits faits dans Hektor non remontés |
| **④ LE REGISTRE DES MANDATS** *(L9, liste section 9)* | phase 1 faite ; mandants et prix chez nous depuis le 06/10 | série légale, inaltérabilité, export, avenants et mandats de recherche, export PROTEXA, 2 défauts dormants de l'étape D |
| **⑤ LA COUPURE** *(L10, liste section 13)* | ouvert le 07/10 | 16 tâches ; ordre proposé dans le plan, **pas décidé** |

### ⛔ Ce qui attend Frédéric

```
⓪ AVANT LE 08/10 A 21:00     fixer la taille du lot des VENTES (proposition 400) et
                             dire « vas-y » pour G.1-e (ch.1) -- sinon un lot de 2 500
                             ventes (20 a 36 h) fait refuser le run du matin
① HORS CODE, sans attendre   A.4 la zone DNS de gti-immobilier.fr est servie par
                             La Boite Immo (MX Google de toute l'agence) : export
                             de la zone, puis OVH -- GARDER l'adresse de www
                             (l'admin Hektor et le worker passent par elle)
                             A.5 ou arrivent les leads depuis le 01/02 ?
                             l'export PROTEXA · les contrats A.1 et A.2 · le juriste
② LES 8 QUESTIONS            plan, section « 🔎 L'AUDIT COMPLET DU 07/10 »
③ C.9-couple                 creer un menage d'essai sur une cible choisie (sonde prete)
④ POUSSER                    git push origin main -- ⚠ pousser = DEPLOYER (Render et
                             Vercel se deploient seuls, ~1 min)
⑤ G.6                        NE PAS allumer -EnqueueConsoleDocuments tel quel : G.2 d'abord
```

### ⚠⚠ Ce qui a une DATE DE PÉREMPTION — *à finir tant que Hektor vit*

```
G.1-b    les 508 brouillons du rattrapage -- AVANT qu'il les atteigne
G.2      rebalayer le PARC VIVANT, fige depuis le 20/08
L10-8    les planchers « Hektor repond vide » (l'index des archives peut tomber sur
         un simple hoquet : ils protegent DES MAINTENANT)
C.9-couple · C.13-c · N.4 (26bis-3) · E.1 (recherches, visites, documents, signatures)
A.3      l'export PROTEXA     ·     A.4 la zone DNS, AVANT tout preavis
```

### Ce qui reste vrai de l'exploitation

- **Le run de nuit** a été réparé le 03/10 (l'étape des liens : 79 min → 46 s). Le
  `busy_timeout` de la descente (`a86a800`) et la garde d'ordonnancement (`5cfd576`) sont
  **faits et poussés**. Nuit du 07/10 : 54 étapes sur 54, 05:00 → 07:20.
- **Reprise** : `.\scheduled\run_quotidien.ps1 -StartAtLabel "<étiquette exacte>"`. Lire le
  journal dans les 30 s : chercher `REPRISE a partir de`, compter les `SAUTEE (reprise)`.
- **Render et Vercel se déploient seuls** sur un push vers `main` : `/health` rend le commit
  qui tourne.
- **Une autre session** travaille parfois en parallèle sur le même dépôt (07/10 : la sonde
  C.9-couple). Relire `git log` avant d'écrire dans les documents.

---

## 07/10/2026 — *l'ancien §2 de `CLAUDE.md` (état du 03/10 au 06/10)*

> Descendu le 07/10/2026, quand le §2 a été réécrit après l'audit complet
> (`notice/AUDIT_AUTONOMIE_COMPLET_2026-10-07.md`). Tel quel ; seul son titre « ## 2. » est retiré.


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


---

## 07/10/2026 — *l'ancienne page de tête de la liste (état au 27/09)*

> Descendue le 07/10/2026, quand la page de tête a été réécrite après l'audit complet.
> Telle quelle ; seul son titre de niveau 1 est retiré.


> ⚠ Elle annonçait *« 15 lignes, rien de plus »* et en faisait **192**, arrêtées au
> 25/09 à 00 h 10. Réécrite le 26/09 : la carte `L0`→`L9` ci-dessous, puis l'état par
> front. L'historique est dans `notice/JOURNAL_DE_BORD.md`.

> ## 🔑 LE PLAN ET CETTE LISTE NE PARLENT PAS LA MÊME LANGUE — *table posée le 25/09*
>
> Le **plan** raisonne en **lots** `L0`…`L9`. Cette **liste** raisonne en **tâches**
> `C.9`, `D.0`, `E.0-bis`, `A.2`… Aucun des deux ne portait la correspondance : d'où la
> question de Frédéric, *« mais e3 et L5 ne sont pas dans le plan ? »* — ils y sont, sous
> d'autres noms. ➡ audit : `notice/AUDIT_CORRESPONDANCE_PLAN_LISTE_2026-09-25.md`
>
> ```
> L0 ✅  C.1' la relecture · le renvoi partiel · C.4 · C.17-ter
> L1 ✅  5b · 4-suite · cle des relations · E.4/6.1-6.3 le distributeur
>        (« E.4 le jour J » reste ouvert : c'est un GESTE, pas du code)
> L2 ✅  26bis-CONTACTS · -RELATIONS · -COUPLES · -RECHERCHES · INVENTAIRE
> L3 ✅  la carte des champs · protection par champ · chantier 2 · C.16
> L4-b' ✅ les 9 sortants · normalizeMandatContactIds · la qualification
> L4-c  ✅ la bascule d'identite du contact (jouee le 23/09)
> L4 🟡  L4-a · L4-b · C.9 (a->f CODES) · C.9-couple · 26bis-TRANSACTIONS · 4.3
>          ⚠ « e3 » = la 3e piece de C.9-e (l. 414) -- codee, ETEINTE
> L5     E.0-bis (l. 2346)   ⛔ les « 102 champs d'annonce et 40 de contact » = MESURE
>          REFUTEE le 25/09 : 0 creable sans etre corrigible (audit AUDIT_L5_...)
>          reste EN VRAI : mandat existant · photos (suppr/reordonner/principale) ·
>          fusion de doublons -> 6 a 10 j, pas 2-3 sem.
>          + C.13 · supprimer une annonce · brouillons · retirer « Ouvrir Hektor »
>
> ⭐ FINIR L'ANNONCE — pose le 28/09, plan maitre section « FINIR L'ANNONCE »
>        Le niveau a atteindre = ce que contact / recherche / transaction ont DEJA.
>        N.1  LA CAMPAGNE DES CHAMPS (A/B/C)     mesure seule — BLOQUANTE
>             !! LA CLASSIFICATION EXISTE DEJA : A1_CHAMPS_PROPRIETE_APP_2026-08-19
>             189 champs en COULEURS (VERT/BLEU/ORANGE), 189 remesure le 28/09.
>             Les COULEURS commandent la DESCENTE, les LETTRES A/B/C le PUSH.
>             A/B/C fait sur l'AFFAIRE, jamais sur l'annonce. Reste les 136
>             champs d'EQUIPEMENT + la correspondance nom worker <-> colonne.
>        N.2  LE VERDICT AU CARNET               les 4 colonnes de l'affaire
>        N.3  LE FRONT ECRIT AU CARNET           il ne capte que 3 GESTES
>        N.4  LE CORPS LOCAL PERSISTANT (26bis-3) ⚠ DATE DE PEREMPTION
>        Ordre N.1 -> N.2 -> N.3 ; N.4 en parallele.
>        ✅ DEJA FAIT et souvent oublie : l'OEIL (C.9-b, 0 ecart sur 13 439) et les
>           4 sentinelles (un_numero · conflit · partielle · push_bloque), toutes a 0.
>           data.annonce_partielle detecte deja un champ IGNORE par Hektor = classe A.
>
> L6     D.0 (l. 963) documents et mandats signes · signature · diffusion · n° mandat
> L7     D.1a · D.1 · D.2 · garder la copie des photos
> L8     C.4-bis elargi · E.3 · 0.3 / E.1 rattrapages · E.2
> L9     A.3-technique · les 3 couches de numerotation · C.13-c   ⚠ AVANT la coupure
>        (il se remplit depuis le MIROIR : impossible apres)
>
> ⚠⚠ TROIS TRAVAUX ONT UNE DATE DE PEREMPTION, pas seulement une priorite :
>    · L9        le registre se remplit depuis le MIROIR
>    · C.9-couple (l. 911) seul moment ou l'on peut comparer NOTRE paire a celle
>                 de Hektor
>    · LA VITRINE ET LES LIENS PUBLICS DE RDV (section 11bis) : les liens deja
>                 DIFFUSES portent le numero Hektor. Il faut servir l'ancienne ET
>                 la nouvelle forme EN PARALLELE pendant que Hektor vit --
>                 un recouvrement, pas un remplacement.
>    · N.4 (26bis-3) LE CORPS LOCAL DE L'ANNONCE : son remplissage vient du
>                 MIROIR, donc il exige que Hektor vive encore.
>    Ils doivent etre finis AVANT la coupure, pas pendant.
> hors lot  A.1 portails · A.2 signature · A.3 juridique  -> FIXENT LA DATE, a zero
>           C.19 transactions · C.11 menage · B.3 · F.1 (apres la coupure)
> ```
>
> **LE COMPTE, au 27/09** — recompté, pas reporté :
>
> ```
> 40   cases ouvertes dans la LISTE VIVANTE (avant « 11. FIN DE PLAN »)
> -11  section 10 (D) : REPRISE par la 10bis -> doublons, bandeau en tete de la section
> ---
> 29   reellement ouvertes, plus les gestes de Frederic
>
> OU ELLES SONT   identite 11 · documents 5 · photos 3 · C.19 4 · A.3 2 · C.4-bis-0 1
>                 C.4-bis 1 · C.16 1 · C.11 1                          = 29
>
> 81 cases FAITES dans cette meme liste vivante. Et 102 autres ouvertes APRES
> « 11. FIN DE PLAN » : archive repetee, elle ne se traite pas.
> ```

> **Réécrite le 26/09/2026.** Cette page remplace la lecture du document : le reste est une
> archive qu'on ouvre **par numéro de ligne**, jamais en entier (6 700 lignes).
> ⚠ **On la RÉÉCRIT, on ne l'empile pas** — c'est l'empilement qui l'avait portée à 192
> lignes pour une promesse de 15. L'historique est dans `notice/JOURNAL_DE_BORD.md`.

```
OU ON EST, PAR FRONT -- ils avancent separement          etat au 27/09 au matin

  ① IDENTITE     L4/C.9        la bascule contact est faite (23/09) ; une annonce NAIT
                 (L4-c l. 121) dans l'app depuis le 25/09 (e3 allume) ; C.9-f en service.
                               RESTE 11 cases : C.9-couple (perissable) · 26bis-3 ·
                                 supprimer les annonces d'essai 63146/63147 · A.3 · C.16

  ② DOCUMENTS    D.0 l. 963    ⚠ LE FRONT LE PLUS EN RETARD : 5 cases sur 6 ouvertes.
                 G.1->G.6      Le rattrapage TOURNE (nuit 1 reussie : 3 000 faits, 0 en
                 l. 1132       erreur, 8 h 17) -> 37 988 restantes, 12,7 nuits.
                               RESTE : G.2 --detect plafonne · G.3 le menage des 3 Go ·
                                 G.4 l'etat doit suivre · G.5 la RPC d'ajout autonome ·
                                 G.6 (Frederic, APRES le rattrapage)

  ③ PHOTOS       section 10bis ⭐ 8 CASES SUR 10 FAITES en deux jours. Le coffre public
                 l. 1135       est PLEIN (74 550 photos, 149 163 fichiers, 17,7 Go) et il
                               S'ENTRETIENT : etape dans le run (le filet) + le worker
                               fabrique des qu'il range (l'immediat, prouve en reel).
                               RESTE : G.15 rebrancher les 44 points ⚠ ECHEANCE COUPURE ·
                                 G.9 la purge (rien a purger avant mars 2027) ·
                                 G.16 deux photos sans fichier
```

> ⛔ **LES 5 GESTES DE FRÉDÉRIC** *(détail : `CLAUDE.md` §2)* — ① redémarrer les 4 services
> *(en journée 06 h – 22 h)* ② pousser ③ `npm install sharp` ④ allumer
> `-EnqueueConsoleDocuments` **après** le rattrapage ⑤ relancer le rattrapage s'il décroche.

> ⚠⚠ **QUATRE TRAVAUX ONT UNE DATE DE PÉREMPTION** *(la table ci-dessus en listait trois ;
> `G.15` est le quatrième)* : `L9` · `C.9-couple` · la vitrine et les liens publics de RDV ·
> et **`G.15`**, parce que les 48 points d'affichage lisent les photos **chez Hektor** — le
> jour de la coupure elles disparaissent **toutes** de l'écran en même temps, même avec les
> 169 Go rapatriés. *Rapatrier remplit le coffre ; ça n'a jamais suffi à afficher.*


---

## 25/09/2026 — *l'ancienne page de tête de la liste (`C.9` / `L4-c-bis`, jour par jour)*

> Déplacée ici le 26/09. Elle annonçait *« tenir à jour, 15 lignes, rien de plus »* et en
> faisait **192**, dont 130 de journal — et elle était arrêtée au **25/09 à 00 h 10**,
> donc elle ignorait le chantier des documents et des photos. Le détail par tâche vit
> dans la section `C.9` de la liste ; ceci est la trace des mesures, dans l'ordre.


> **Mis à jour le 25/09/2026 (00 h 10).** Cette page remplace la lecture du document. Le reste est une
> archive qu'on ouvre **par numéro de ligne**, jamais en entier.

```
OU ON EST, EN TROIS NIVEAUX

  ETAPE 2       L0 OK  L1 OK  L2 OK  L3 OK  L4 EN COURS   puis L5 L6 L7 L8 L9
  L4            L4-a OK  L4-b OK  L4-b' OK  L4-c OK  C.9 EN COURS
  L4-c          (0) OK (1) OK (2) OK (3) OK (4) OK  (5) OK -- BASCULE FAITE 23/09 19h05
  C.9           a OK  b OK  c OK  e1 OK  e2 OK  e3 OK (eteint) -- ESSAI REEL OK 24/09
                RUN DE JOUR 12:35 + descente : OK (1 numero des deux cotes, 0 ecart)
                d OK + D6 OK : PROUVES au RUN DE JOUR 24/09 16:05-18:09 (code 0, 0 403)
                SECONDE PASSE du build : 1re nuit 25/09 -> « 0 contact a traduire, rien
                  n'est ecrit » en 1 s (aucun contact neuf chez Hektor cette nuit : le
                  registre annonce « a numeroter 0 »). Le chemin inerte est prouve ; le cas
                  AVEC un contact neuf reste a voir en reel (sur copie le 24/09 : 8/8)
                ORDRE DECIDE 24/09 soir (Frederic : « Oui, d'abord le plan ») :
                  (1) ✅ FAIT : les rapprochements n'etaient PAS rattaches -> audit
                      (notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md),
                      fonction de retraduction des 13 tables satellites + appel de nuit
                      + sonde ; APPLIQUEE 25/09 00:07 : 72 lignes retraduites, 0
                      rapprochement sans contact (bloc L4-c-bis ci-dessous)
                  (2) ✅ FAIT le 25/09 : C.9-f code, 15/15, repete sur copie -> 0 cle
                      changee ; EN SERVICE a la nuit du 26/09 (le run de 05:00 lit le
                      fichier). (ancien libelle ci-dessous)
                  (2) C.9-f : audit -> explication -> code -> repetition sur COPIE
                      (le carnet EXISTE dans la vraie base depuis le run de 16:05 :
                      plus besoin d'attendre une nuit). Attendu : 0 cle changee.
                      Si 0 sur la copie -> en service DES LA NUIT du 25/09, en meme
                      temps que la seconde passe (chacune sa ligne au journal).
                  (3) 25/09 matin : controle de la nuit (seconde passe, carnet, D6,
                      retraduction satellites = les 30 des 8 neufs, sonde
                      data.contacts_satellites, sondes a 0)
                  (4) decision de Frederic : allumer e3 pour de bon
                ➡ notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md · detail : bloc C.9
  L4-c-bis      ✅ CORRIGE 24/09 (code e414fe0 + 23 fiches reparees 15:4x, go de Frederic)
                repetition sur COPIE de la vraie base : registre -> build -> registre :
                23 traduits, 5 liens et 4 recherches suivent (cles IDENTIQUES), 0 second
                numero, controles a 0. Reel : 23 lignes reparees en transaction verifiee ;
                le build traduira cette nuit (605491 -> 10650346). Sonde data.contacts_
                identite INSCRITE (critical, prouvee : mal rangee / bloque > 36 h / ok).
                ✅ VERIFIE au run de jour du 24/09 (16:05-18:09) : dans Supabase, les 10
                qui y sont (contacts eligibles) sont sous leur identite, 0 sous l'ancien
                numero, 0 ancienne cle de lien ; les 13 autres n'y ont jamais ete (non
                eligibles). Regles mal rangee / desaccord : 0 / 0. 8 contacts NEUFS du jour
                (605514-605521) passent une nuit sous leur n° Hektor -- ⛔ PAS « normal » :
                ➡ SECONDE PASSE DU BUILD (24/09 soir, « Oui » de Frederic). Le run fait
                  build -> registre -> push : le registre numerote les contacts neufs
                  APRES le build, qui les a ecrits sous leur n° Hektor ; ils partaient
                  vers Supabase sous ce numero et changeaient d'identite le lendemain,
                  laissant derriere eux ce que l'app leur avait accroche (mesure : 67
                  rapprochements des contacts L4-c-bis encore sous l'ancien numero ;
                  30 pour les 8 neufs). Depuis la bascule du 23/09 seulement.
                  Correctif : le run relance le build APRES le registre, AVANT le push,
                  avec --seulement-si-contacts-a-traduire (0 -> s'arrete sans rien ecrire).
                  Non bloquante, 1 essai. ~4 min les jours ou il y a des contacts neufs.
                  test_seconde_passe_contacts_neufs.py 7/7 ; PREUVE sur cc9010f : echoue.
                  REPETITION sur COPIE de la vraie base (8 neufs a traduire) : 211 s,
                  8/8 traduits, leurs 5 recherches gardent LEUR cle, 0 autre lien ni
                  recherche change, carnet 100 % / 0 conflit ; registre derriere : 0
                  second numero ; 2e passe : « 0 a traduire », rien ecrit. Vraie base
                  intacte. EN SERVICE a la nuit du 25/09.
                  [ ] A COCHER apres la nuit : ligne « [seconde passe] » au journal,
                      et au run suivant « contacts a traduire » = 0 avant le build.
                  [x] MESURE (lecture, 24/09 soir) : NON, ils ne sont PAS rattaches.
                      - app_upsert_one_rapprochement : ON CONFLICT met a jour le score,
                        JAMAIS hektor_contact_id -> un rapprochement ne sous le n° Hektor
                        le garde pour toujours.
                      - app_get_rapprochements_for_dossier : LEFT JOIN contact PAR CE
                        NUMERO -> ligne affichee SANS nom/email/tel/nego ;
                        app_count_rapprochements_for_contact : filtre PAR CE NUMERO ->
                        le compteur « N biens » de la fiche ne les compte pas ;
                        app_generate_rapprochement_alerts : meme jointure.
                      - Parc entier : 69 lignes / 5 contacts sous un ANCIEN n° Hektor
                        (tous eligibles), 0 action de negociateur dessus ; 50 135 bons.
                        + les 30 des 8 neufs deviendront orphelins CETTE NUIT (traduits).
                      - C'etait une table « figee » de la bascule du 23/09 (13 tables
                        traduites a la main, que le build ne refait pas).
                  [~] REPARATION CODEE 24/09 soir (« Oui ») -- audit complet :
                      notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md
                      supabase/patch_retraduire_satellites_2026-09-24.sql : fonction
                      app_contact_retraduire_satellites(p_appliquer) sur les 13 tables
                      figees ; a blanc par defaut ; saute+compte ambigus / contradictoires
                      / collisions (4 index uniques) ; « le compte doit tomber juste »
                      (ecarts) ; trace app_contact_retraduction_log ; service_role seul.
                      PREUVE sur copies temporaires annulees (vraies donnees + 6 cas
                      pieges) : 1re passe a trouve MON defaut (17 lignes ni traduites ni
                      comptees : app_contact_id VIDE sur 10 fiches -> NULL) ; corrigee ;
                      2e passe : 74 traduites (69 + 3 compteurs + 2 pieges), 3 sautees,
                      0 ecart, rejeu = rien, 0 rapprochement sans contact ; prod intacte.
                      Appel de nuit : propager_numeros_contact.py AVANT la propagation,
                      protege (fonction absente -> l'etape continue). Sonde
                      data.contacts_satellites (a blanc : ecart critical, reste warning).
                      test_retraduire_satellites.py 9/9 ; PREUVE sur cb711df : echoue.
                      [x] APPLIQUE 24/09 ~23:50 par Frederic (empreinte du corps installe
                          = celle du fichier, 50c8da99…, aux fins de ligne pres). A blanc :
                          72 traduisibles, 0 saute, 0 ecart. Pour de bon (00:07, go de
                          Frederic, l'etape de nuit elle-meme) : 72 traduits (69 + 3).
                          Apres : 0 rapprochement sans contact sur 50 204, 0 desaccord de
                          colonnes, rejeu a blanc = 0, trace 1 ligne ; l'ecran du bien
                          1379038 affiche de nouveau « M. Jeremy KUPKOWSKI » (10650346).
                      [x] NUIT DU 25/09 (run 05:00-06:55, exit 0) : « retraduction
                          satellites (applique) : a traduire 30, traduits 30, sautes 0,
                          ecarts {} » -> 0 rapprochement sans contact sur 50 207 ; sonde
                          a blanc = 0 ; trace 2 lignes (72 le 24/09, 30 le 25/09).
                          ⚠ NOTE : la propagation qui suit a rempli 4 app_contact_id (dont
                            3 rapprochements) -- les DEUX etapes servent, dans cet ordre.
                      ⚠ HORS PLAN NOTE : 10 fiches de app_contact_current (Supabase) sous
                        identite ont app_contact_id VIDE (les contacts L4-c-bis) --
                        pousser_numeros_contact ne les a pas remplies. Non traite.
                  (ancien) REPARATION a decider par Frederic (ecriture prod = son geste) :
                      UPDATE app_rapprochement -> identite, via hektor_target_id, APRES
                      la nuit du 25/09 (couvre 69 + 30). + garde durable a discuter
                      (le moteur met a jour hektor_contact_id, ou re-traduction des
                      tables figees apres le push). La seconde passe empeche les
                      NOUVEAUX cas ; elle ne repare pas les anciens.
                ⚠ HORS PLAN, trouve en passant : C.16 et le registre se contredisent --
                  le registre leve chaque nuit les 7 658 marques « disparu » de C.16
                  (contacts supprimes chez Hektor mais toujours dans la couche), C.16
                  les repose aussitot : etat final juste, mais la date « absent depuis »
                  est reecrite chaque nuit. Preexistant (l'ancienne regle faisait pareil).
  (historique)  TROUVE 24/09 14:35
                Tout contact cree chez Hektor DEPUIS LA BASCULE reste sous son numero
                Hektor, indefiniment : 23 au 24/09 (~10 de plus par jour).
                Cause : registre_contacts.py l. 232 inscrit le n° Hektor dans la colonne
                hektor_contact_id (qui porte l'IDENTITE depuis le 23/09) et l'identite
                dans app_contact_id ; build_contacts_layer.py l. 357 ne lit QUE
                hektor_contact_id -> pour eux cible = identite -> jamais traduits.
                ⚠ Correctif naif (lire app_contact_id) = la couche passe sous 10650346,
                  le registre ne la reconnait plus (il cherche 605491) -> SECOND numero :
                  le mecanisme exact du 294 179 du matin. Registre ET couche d'un geste.
                ⚠ Le controle de nuit est AVEUGLE a ce cas (il ne cherche que les
                  doublons) : ajouter « n° d'app attribue mais n° Hektor en identite ».
                ⚠ Ce matin j'avais dit « decalage de 24 h » : c'etait faux.
```

> **24/09/2026 — `L4-c` EST FAIT, `C.9` EST OUVERT (audit fait, AUCUN code écrit).**
> ➡ `notice/AUDIT_C9_ANNONCE_NEE_DANS_APP_2026-09-24.md` — lire **§4** *(ce que la seconde
> passe a réfuté de la première)* et **§5** *(l'ordre C.9-a → C.9-f et le feu vert de chacun)*.
> **24/09 fin de matinée — C.9 : a, b, c, e1, e2, e3 EN SERVICE, et l'ESSAI RÉEL A RÉUSSI.**
> « ESSAI C9 bis » créée depuis l'app (interrupteur `app_setting.c9_annonce_nait_dans_app`,
> **éteint** hors essai) : ligne **10 000 000**, Hektor **63147**, **un seul numéro** des deux
> côtés, adoptée par le serveur. Détail et chiffres : bloc C.9 de la liste.
> ⚠ **L'ORDRE A CHANGÉ** *(accord de Frédéric)* : **e avant d** — d et f préparent la coupure ;
> **d doit vivre DANS le build** (la clé d'un lien ne se recalcule que pour 57 % des lignes).
> ⚠ **D8** trouvé en auditant e : le rafraîchissement effaçait le numéro de l'app une minute
> après la création → corrigé par e1 + e2.
> ⚠ **Les patchs SQL de production, c'est Frédéric qui les applique** (l'outil est bloqué).
> **EN COURS : le run de jour lancé à 12 h 35, puis la descente** — faire le bilan (C.9-a avant
> le bootstrap, push avec C.9-c, sonde C.9-b après la descente). **Puis C.9-d, dans le build
> (go obligatoire), puis C.9-f.** Deux annonces de test à supprimer plus tard : 63146, 63147.
> ✅ **L4-c-bis CORRIGÉ le 24/09 après-midi** (répété sur copie, 23 fiches réparées, sonde
> `data.contacts_identite` en service) — **à vérifier le 25/09** : les 23 sous leur identité dans
> Supabase. Hors plan noté : C.16 et le registre se contredisent (date « absent depuis » réécrite).
> ✅ **C.9-d CODÉ le 24/09 au soir** — le build tient **le carnet des liens** (`app_relation_registry`,
> recette exacte de chaque clé, doublure lue par personne). Répété sur copie : 100 % des recettes
> refabriquent leur clé. **1re nuit = 24→25 : vérifier la ligne `[carnet des liens]` du build.**
> ✅ **D6 CODÉ aussi** : le recensement « connu de l'app seule » marque ses départs (26 lignes
> périmées ce soir). **Run de jour 16:05-18:09 : C.9-d, D6, L4-c-bis PROUVÉS en réel.**
> ✅ **SECONDE PASSE DU BUILD** (24/09 soir) : un contact neuf ne passe plus une nuit sous son
> numéro Hektor (le run relance le build après le registre, avant le push). Répétée sur copie,
> **en service à la nuit du 25/09** — vérifier la ligne `[seconde passe]`. Reste une mesure : les
> 97 rapprochements laissés sous un ancien numéro sont-ils bien rattachés dans les écrans ?
> ✅ **TABLES SATELLITES** : 13 tables figeaient le numéro du contact (69 rapprochements sans nom).
> Fonction de réparation + appel de nuit + sonde — **APPLIQUÉE le 25/09 à 00 h 07 : 72 lignes
> retraduites, 0 rapprochement sans contact.** Cette nuit : les 30 des 8 contacts neufs.
> ➡ `notice/AUDIT_RAPPROCHEMENTS_NUMERO_CONTACT_2026-09-24.md`
> **25/09 MATIN, À CONTRÔLER** : journal du run (lignes `[seconde passe]`, `[carnet des liens]`,
> « retraduction satellites », « départs marqués »), sondes `data.contacts_satellites`,
> `data.contacts_identite`, `data.annonce_un_numero` à 0. **Puis C.9-f.**
> ✅ **C.9-f CODÉ le 25/09** — l'identifiant d'un lien se fabrique avec **notre** numéro de bien ;
> le carnet fige les existants. **Répétition sur copie : 0 identifiant changé sur 167 496.**
> Deux garde-fous (carnet trop court, trop d'identifiants disparus → le build recommence sans
> substituer). **EN SERVICE à la nuit du 26/09** — vérifier la ligne `[numero de bien dans la cle]`.
> ⭐ **e3 ALLUMÉ LE 25/09 À 08 h 15 PAR FRÉDÉRIC** — `c9_annonce_nait_dans_app = 'on'`.
> **Une annonce créée dans l'app naît désormais avec NOTRE numéro** (la prochaine : 10 000 001).
> Retour arrière : la même requête avec `'off'`, immédiat.
> **IL RESTE : (1) contrôle de la nuit du 26/09 (C.9-f) ; (2) surveiller la 1re annonce réelle
> d'un négociateur ; (3) supprimer les annonces de test 63146 et 63147.**
> ⚠ Connus : le compte formation n'est proposable que depuis l'écran Estimations · un refus
> consomme un numéro.
> ⛔→✅ **L5 AUDITÉ le 25/09 : son gros morceau n'existait pas.** Les « 102 champs d'annonce et
> 40 de contact » sont une **mesure réfutée** — 0 créable sans être corrigible, fait depuis le
> 02/06. **L5 = 6-10 j, pas 2-3 sem** : restent **les photos** *(supprimer, réordonner,
> principale)*, **le mandat existant** *(dates, durée, avenant)*, **la fusion de doublons**
> *(ton arbitrage : app ou admin ?)*. ➡ `notice/AUDIT_L5_GESTES_MANQUANTS_2026-09-25.md`
> ⚠ **Les autres chiffrages du plan n'ont pas été revérifiés** : ordres de grandeur, pas mesures.
> ⛔ **DÉCISION DE FRÉDÉRIC (25/09) : LES DOCUMENTS D'ABORD, LES PHOTOS ENSUITE.**
> · **`D.0`** — arrêté depuis le **23/08** *(33 j)*, 0 en erreur : **arrêté, pas cassé**. Deux
>   trous : blocs **ImmoSign** et **« Mes documents »** sans `force_transfert` *(jamais indexés)* ;
>   signature masquée en connexion **administrateur**. Reprise **déjà conçue** *(empreinte de
>   contenu + « procédure en cours » = 242 annonces)*, derrière le frein anti-bannissement.
>   ⚠ **Ne jamais rejouer les annonces en échec · cadence lente · un 403 arrête tout.**
> ✅ **`D.0 ①` LE MANDAT / L'ANNEXE EST RÉGLÉ (25/09).** Sous le nom « Mandat », 88 annonces
>   n'affichaient que l'**annexe** (197 Ko) ou le **barème** : l'archive ImmoSign contient DEUX
>   pdf et `extractPdfFromZip` prenait **le premier**. Correctif `19d7a33` *(on écarte
>   annexe/barème, sinon le plus gros)*, prouvé sur **120 archives réelles** — l'ancienne
>   version en choisissait 28, la nouvelle 0. **4 services redémarrés à 13 h 09.**
>   Rattrapage `Console/rattrapage_mandat_signe.js` passé par Frédéric : **88 rattrapés,
>   0 restant**, taille moyenne 1,00 Mo, 0 écart taille ↔ métadonnée, l'ancien PDF tracé dans
>   `annexe_ecartee`. ⚠ **Il doit tourner dans un PowerShell ADMINISTRATEUR** : ces fichiers
>   appartiennent au service (LocalSystem), `BUILTIN\Utilisateurs` n'a que `(RX)` dessus —
>   créer un fichier passe, l'écraser non. *(Ce n'était PAS le bac à sable : même refus sans lui.)*
> ⛔⛔ **`D.0 ②` — LE VRAI CHANTIER : LE RATTRAPAGE EST À 29,5 %, PAS À 97 %.**
>   ⚠ **Ma 1re mesure était fausse par omission** — elle ne portait que sur `daily-cloud`
>   (13 437 annonces) alors que le parc en fait **58 140**. *Frédéric l'a relevé : « tu es
>   juste sur le périmètre des annonces de l'app et pas les archives ».* **Même classe
>   d'erreur que L5 : une liste partielle prise pour la liste entière.**
>   ➡ `notice/AUDIT_RATTRAPAGE_DOCUMENTS_2026-09-25.md`
>
>   | périmètre | annonces | empreinte | lue sans empreinte | **jamais lue** |
>   |---|---:|---:|---:|---:|
>   | archive | 35 299 | 4 055 | 4 531 | **26 713** |
>   | courant | 13 437 | 13 068 | 17 | 352 |
>   | historique | 8 920 | 26 | 0 | **8 894** |
>   | brouillon | 484 | 0 | 0 | **484** |
>   | **total** | **58 140** | **17 149** | 4 548 | **36 443** |
>
>   Le rattrapage a tourné du 18 au 23/08 (scope `archive`, **10 786 jobs**, `lot: empreinte`)
>   puis s'est **arrêté** — pas échoué : **0 en erreur**. Le 20/08 à 10 h 08, `7143a1a` posait
>   le frein : *« notre IP a été bannie »*.
>   **Débit mesuré** : 877/h avant le frein, **594/h après** → **36 443 ÷ 594 ≈ 61 h**.
>   ⭐ **L'OUTIL EST `Console/enqueue_empreinte_lot.js`** *(21/08, lots de 3 000)*, PAS
>   `enqueue_console_sync_jobs.js` sans `--detect` — celui-ci ne saute que les jobs
>   `pending`/`running`, jamais les `done`, et ré-empilerait les 3 000 premières déjà faites.
>   Ses 3 exclusions : empreinte posée · **job en erreur = NE JAMAIS REJOUER** · déjà en file.
>   Reprise **par identifiant**, jamais par position.
> ✅ **① FAIT (25/09, `3f2c203`) — l'empreinte porte enfin NOTRE numéro.**
>   `app_console_document_fingerprint` était la **seule** table de la chaîne documents sans
>   numéro d'app *(sa clé primaire EST `hektor_annonce_id`)* et **absente de `REPOINT_TABLES`**,
>   alors que document / photo / job y sont. C'est **le carnet du rattrapage** : une ligne
>   laissée sous un dossier fantôme ferait refaire les 61 h.
>   ⚠ **GARDE DE FRÉDÉRIC : « ne pas casser les workers qui ont besoin des id hektor ».**
>   Tout est **additif** : clé de conflit inchangée, numéro Hektor toujours envoyé, les 3 autres
>   points d'appel intacts, appel à 2 arguments n'écrase rien. Patch appliqué par Frédéric :
>   **17 149/17 149 remplies, 0 incohérence**, clé primaire toujours `hektor_annonce_id`.
>   Garde-fou `Console/test_empreinte_numero_app.js` *(12 contrôles, prouvé au rouge)*.
>   **Workers redémarrés à 14 h 13, APRÈS le patch.**
> ✅ **② FAIT (25/09) — la détection freine et s'arrête au 403.**
>   `enqueue_console_sync_jobs.js` lisait Hektor avec un `fetch` **nu** : **aucune cadence**
>   *(mesuré : 0 ms entre 3 lectures)* et un **403 avalé** puis `continue` — la mécanique exacte
>   du bannissement. Désormais : même frein que le worker, **piloté par les mêmes variables
>   d'environnement** *(un seul réglage, pas deux vérités)*, et `ArretBalayage` sur
>   401/403/429/503, session morte, connexion refusée. Un **500 ou un timeout isolé** continue
>   de passer sans rien conclure. Ce qui est déjà trouvé **est quand même enfilé**.
>   Garde-fou `Console/test_frein_detection.js` *(15 contrôles, prouvé au rouge deux fois)*.
> ⭐⭐ **25/09 SOIR — L'AJOUT DEVIENT AUTONOME (lots 1, 2a, 2b faits, DORMANTS).**
>   *Remarque de Frédéric : « les documents photos attendent toujours une confirmation de
>   Hektor avant de sauvegarder, contrairement au reste du dev comme contact ». Exact.*
>   Contacts, annonces et recherches ont leur couche optimiste ; **documents et photos
>   étaient les deux SEULES entités à exiger Hektor pour exister**. À la coupure, ajouter
>   un document depuis l'app aurait **cessé de fonctionner** — absent des 3 exceptions.
>   **L'INVERSION** : notre serveur d'abord, Hektor ensuite. Si Hektor ne répond pas, le
>   document existe quand même — dans l'app et chez nous.
>   · **lot 1** (`7428303`) : base *(3 colonnes + index partiel × 2 tables, appliquées)* +
>     `completerEnvoiDocumentDiffere`. L'envoi Hektor **extrait et partagé** ; l'ordre du
>     chemin d'origine **préservé à l'identique**. 18 contrôles, rouge prouvé 2×.
>   · **lot 2a** (`db5c38c`) : la jumelle photo. ⚠ Préalable levé : `hektor_photo_id` était
>     **NOT NULL** — l'app ne pouvait pas créer une photo avant l'envoi. Contrainte retirée,
>     unicité conservée *(les NULL y sont distincts)*, 1 397 photos intactes. 25 contrôles.
>   · **lot 2b** (`ec838b2`) : `Console/reprendre_envois_hektor.js`. **Il ne s'acharne pas** —
>     respiration 15 min, pas de repose par-dessus une file, et un échec de +24 h est
>     **signalé et sort en 1**. Le tri est une fonction pure. 14 contrôles.
>   ⚠⚠ **VÉRIFIÉ AVANT D'ÉCRIRE, c'était le risque qui pouvait tout arrêter** : une ligne
>   **sans numéro Hektor SURVIT à la synchro de nuit**. Les deux nettoyages ne suppriment
>   que des lignes qui *ont* un numéro Hektor devenu obsolète.
> ⛔ **LOT 2c BLOQUÉ SUR UN PRÉALABLE DE SÉCURITÉ (25/09 au soir)** : le front n'a que
>   **SELECT** sur `app_console_document` et `app_console_photo` — il ne peut créer qu'un
>   *travail*. **C'est précisément pourquoi le schéma est « Hektor d'abord ».** Il faut une
>   **RPC SECURITY DEFINER** *(patron de la signature manuscrite)* qui crée la ligne pour le
>   front — **et qui vérifie que le négociateur a accès à l'annonce**, sinon n'importe qui
>   dépose un document sur n'importe quel bien. **À faire de tête reposée.**
> ✅ **ET LA FUITE EST BOUCHÉE** (`c95cb9b`) : une photo ajoutée depuis l'app est enfin
>   **gardée sur le serveur** (+ Supabase si l'annonce est vivante), comme les documents le
>   font depuis des mois. Best-effort et bruyant : lever ferait rejouer le travail donc
>   **renvoyer la photo**, et Hektor en aurait deux. Explique les 42 photos « en attente ».
> ✅ **MATTERPORT** (`80676d0` + patch appliqué) : 4 484 groupes portent nos deux numéros,
>   **0 incohérence**, l'identifiant **intact** *(les 5 049 scans y pendent)*, et le run le
>   recalcule à chaque passage. ⚠ Il ne parle JAMAIS à Hektor — vérifié.
> ⭐ **PHOTOS — le rapatriement est prêt** (`3c17057` + `f27f9b5`) : **444 431 photos**, dont
>   **435 166 à faire**, **~110 Go**, **~7 h** à 17/s. ⚠⚠ **LES ADRESSES SONT DÉJÀ CHEZ NOUS**
>   (miroir local, `hektor_annonce_detail.images_json`) → **le rapatriement ne touche JAMAIS
>   Hektor** et peut tourner en parallèle du rattrapage documents. *(Les « 13 nuits de quota »
>   que j'annonçais n'existent pas — je n'avais pas appliqué la règle « chercher d'abord en
>   local ».)* Calibré sur 900 téléchargements, **0 refus**. ⚠ **Échéance : AVANT la coupure**,
>   après quoi le CDN ne sert plus rien. ➡ `notice/AUDIT_PHOTOS_2026-09-25.md`
> ⚠⚠ **ET LA LEÇON DU JOUR, écrite parce qu'elle se répétera** : j'ai corrigé l'empreinte
>   documentaire le matin *(numéro Hektor seul)*, puis écrit l'après-midi un script créant
>   435 126 lignes **avec le seul numéro Hektor**. *« Comment as-tu pu oublier alors qu'on a
>   tout fait pour que tu ne perdes pas le fil ? »* → **j'applique la règle quand j'INSPECTE
>   l'existant, pas quand j'ÉCRIS.** Les garde-fous du projet sont tous tournés vers l'audit.
>   **Il manque une sonde nocturne** : « une table porte-t-elle un numéro Hektor sans le
>   nôtre ? ». ➡ `notice/AUDIT_DEUX_NUMEROS_PARTOUT_2026-09-25.md`
> ⛔⛔ **LE POINT LE PLUS GRAVE, TROUVÉ LE 25/09 AU SOIR : L'APP AFFICHE LES PHOTOS
>   DEPUIS HEKTOR.** Le front lit `photo_url_listing` et `images_preview_json` — des
>   adresses `staticlbi`, donc l'abonnement Hektor. **30 occurrences dans `App.tsx`.**
>   ➡ **Le jour de la coupure, TOUTES les photos disparaissent de l'écran en même temps**
>   *(fiches, listes, vitrine publique)* — **même avec les 110 Go rapatriés sur le serveur.**
>   **Rapatrier remplit le coffre ; ça n'a jamais suffi à afficher.** Preuve côté documents :
>   les 22 023 poussés dans Supabase sont visibles, les 22 493 restés sur le serveur non.
>   ➡ **DEUX gestes** : `P1` verser les vivantes dans Supabase *(~29 Go → 62 sur 100 inclus)*
>   et `P2` faire lire l'app chez nous *(30 points, derrière un interrupteur, repli sur
>   l'adresse Hektor tant qu'elle répond)*. **`P2` est le seul point dont l'échéance est la
>   coupure elle-même — il ne se rattrape pas après.**
>   ➡ **LA LISTE COMPLÈTE, D1→D8 et P1→P8** : `notice/RESTE_A_FAIRE_DOCUMENTS_PHOTOS_2026-09-25.md`
>   *(ajouter et supprimer exigent encore Hektor · l'état ne suit pas dans les deux sens :
>   2,2 Go bloqués, ×4 en 5 semaines · le repassage n'est branché nulle part · supprimer /
>   réordonner / photo principale n'existent NI chez nous NI comme commandes Hektor connues)*
> ⛔ **IL RESTE :**
>   ③ **relancer le rattrapage** — `enqueue_empreinte_lot.js`, lots de 3 000, archive →
>      historique → brouillon. **~61 h.** *(go de Frédéric obligatoire)*
>   ④ `run_full_pipeline.ps1:1033` n'appelle **jamais `--detect`** → le drapeau ajouté tel quel
>      empilerait tout le périmètre chaque nuit ; et l'étape est **bloquante** (`throw`) alors
>      que ses voisines sont en `Invoke-OptionalStepWithRetry` : une session morte tuerait
>      Matterport, les **liens publics de RDV**, **la vitrine**, l'export Android ;
>   ⑤ **Frédéric** : allumer `-EnqueueConsoleDocuments` dans `run_quotidien.ps1`.
>   ▫ petit : **53 documents sur 4 annonces** (49540, 33151, 61654, 35884) portent un
>      `app_dossier_id` absent des 4 index.
>   ✅ Vérifié sain : les 4 séries d'index partagent **une seule** numérotation, **0 collision
>      sur 58 140** ; documents et photos portent les deux numéros à 100 % ; le front lit par
>      `app_dossier_id` ; les actions vers Hektor passent par `hektor_annonce_id`.
> · **Les photos** *(noté au plan, après)* : **13 437 vignettes pointent chez Hektor**, 1,7 %
>   rapatriées — et **le serveur n'est lisible ni par Vercel ni par Render**, donc rapatrier ne
>   suffit pas à afficher. **Le chemin d'affichage est un arbitrage de Frédéric.**
> ✅ **Le reste du plan fonctionne** : 36 types de travaux, **0 en erreur**. Les 3 exceptions
>   restent **numéro de mandat** *(`L9`)*, **signature** *(`A.2`)*, **portails** *(`A.1`)*.
> ⚠⚠ **LA VITRINE PUBLIQUE ET LES 2 SYSTÈMES DE RDV** *(signalés par Frédéric le 25/09,
>   absents de tous mes audits alors que ce sont 2 étapes du run)* : hébergement GitHub sain,
>   **2 227 liens publics ont déjà jeton + notre numéro**, RDV Google aux deux numéros. Mais la
>   vitrine fabrique ses liens avec le **n° Hektor**, le service **retombe sur `hektor_annonce_id`**
>   après le jeton, et la **fiche visite PDF vient de Hektor**. ⚠⚠ **Liens PUBLICS déjà diffusés
>   (QR, imprimés) : recouvrement, PAS remplacement** ➡ `notice/AUDIT_VITRINE_ET_RDV_2026-09-25.md`
> ⚠⚠ **TROIS TRAVAUX ONT UNE DATE DE PÉREMPTION, pas seulement une priorité** : **`L9`**
>   *(le registre se remplit depuis le miroir)* et **`C.9-couple`** *(seul moment où l'on peut
>   comparer NOTRE paire à celle de Hektor — l'app envoie le conjoint, c'est **Hektor** qui crée
>   la 2ᵉ fiche et pose le lien ; à la coupure, personne ne le fera)*. **Son 1er pas est une
>   MESURE d'1 h** : créer un couple d'essai et regarder si Hektor fait une fiche ou deux.
>   **Et la vitrine / les liens publics de RDV** *(ci-dessus)* : l'ancienne forme doit survivre
>   pendant que Hektor vit. *(Les deux rappelés par Frédéric le 25/09 — je les avais omis.)*
> ➡ `notice/AUDIT_DOCUMENTS_ET_ETAT_DES_FONCTIONS_2026-09-25.md` · `notice/AUDIT_PHOTOS_2026-09-25.md`
> *(historique)* **L4-c-bis, trouvé à 14 h 35** : les contacts créés chez Hektor **depuis la bascule** restent
> sous leur numéro Hektor (23 au 24/09) — le registre met l'identité dans `app_contact_id`, le
> build ne lit que `hektor_contact_id`. **DÉCISION DE FRÉDÉRIC (14 h 45) : on le corrige AVANT de reprendre C.9**, registre et
> couche d'un seul geste, répété sur copie : le correctif naïf refait le doublement du 24/09.
>
> · la bascule contact a été jouée le **23/09 à 19h05** *(61 985 contacts sur notre numéro)* ;
> · le premier run d'après a **doublé 294 179 identités** dans le registre local — réparé,
>   cause fermée, contrôle chaque nuit *(`f974ef9`, `376dc7b`)* ; Supabase jamais touché ;
> · vérification complète le 24/09 : **rien de perdu, rien de cassé** *(§6 de la note)*.
>   ⚠ **À revérifier le 25/09 au matin** : 3 contacts encore sous leur numéro Hektor dans
>   Supabase, et l'alarme « critères différents : 1 » de la descente.
>
> ⛔ La section ci-dessous date du 22/09 : elle décrit une bascule **faite depuis**.

> **22/09/2026 (soir) — IL NE RESTE QU'À ALLUMER LA BASCULE** *(`L4-c ⑤`)* : remplir
> `app_contact_identite_app` avec les **356 147 paires**. **Plus une ligne de code à écrire.**
> ⚠ **Trois conditions, toutes écrites dans la liste** : code et données **la même nuit**
> *(le push remplace les 167 459 clés de relation en une fois)* · les **9 liens d'agenda**
> dans la même fenêtre · et **écrire la commande complète et la MONTRER avant de l'exécuter**.
> ➡ `notice/AUDIT_L4C_PORTE_ET_IDENTITE_2026-09-22.md`
>
> **FAIT LE 22/09 :**
> · **`L4-b′` la porte est fermée** *(`a19d9c5`)* — 9 sortants envoyaient un numéro à Hektor
>   sans traduction, dont 5 sans garde-fou ; la traduction était **calculée puis jetée**, et
>   le filtre des mandants **écartait en silence**. Garde-fou : `Console/test_porte_contacts.js`.
> · **`L4-c ⓪` la doublure est montée dans la plage de l'app** *(`2a4e0f0`)* — **194 683
>   numéros** existaient dans les deux séries en désignant des personnes **différentes**.
>   244 834 lignes côté serveur + 463 543 en local, build complet par-dessus, **0 clé changée**.
>   Désormais : **sous 10 M c'est Hektor, au-dessus c'est nous.**
>
> **ET LE 22/09 APRÈS-MIDI, DEUX DE PLUS** *(run réel, 121 min, résultat 0)* :
> · ⛔ **le décalage avait cassé le couloir du registre** — le prochain contact aurait reçu
>   le numéro **1**, et l'INSERT aurait réussi. Puis, le filtre retiré, le registre local et
>   le distributeur Supabase auraient donné **le même numéro à deux personnes**.
>   ➡ **trois étages** : `< 10 M` Hektor · `10 M–20 M` la doublure · `≥ 20 M` l'app.
>   **Prouvé** : 12 contacts livrés ont reçu 10 356 138 à 10 356 149.
> · ⛔ **le run mourait d'impatience** : 4 tentatives en **2,5 secondes**, et un unique 500
>   sur une page d'archives tuait 2 heures de travail. ➡ **2 s · 8 s · 30 s**. Le run
>   relancé est passé. ⚠ **les 403 lèvent toujours immédiatement** — la patience ne vaut que
>   pour les 5xx.
>
> ⚠ **LA LEÇON DE CES DEUX JOURS, et elle vaut pour la suite** : **sept défauts** trouvés —
> par des **essais réels**, des **répétitions sur copie** et les **questions de Frédéric**.
> **Aucun n'aurait planté. Les sept auraient fait des dégâts muets.** Ici, un défaut ne crie
> jamais : il faut aller le chercher. ➡ Ne jamais conclure sans mesurer, ne jamais déployer
> sans éprouver, et **répéter sur une copie avant tout geste irréversible**.
>
> ⚠ **CE QUI COMMANDE CE LOT** : le registre des recherches **bouge avec le contact, pas
> après** — son ancrage est la paire `(hektor_contact_id, rang)`, donc une **position**. Si
> l'identité change sans lui, aucune recherche n'est reconnue le lendemain : 11 368 clés
> neuves, et tout ce qui pend dessous orphelin, **sans un bruit**.
>
> **LE SOCLE EST ÉPROUVÉ.** Run complet + descente rejoués en vrai le 21/09 au soir
> *(20 h 23 → 23 h 14, résultat 0)* :
> couloir des annonces **+7 pour 7 annonces** *(l'ancien défaut donnait +61 235)* ·
> les deux témoins nés dans l'app **ont survécu** alors que leurs jumelles chez Hektor
> n'existent plus · **aucune clé perdue** · **aucun 403 neuf** · **toutes les sondes à zéro**.
>
> ⚠ **DEUX DÉFAUTS INVISIBLES TROUVÉS LE MÊME SOIR**, tous deux dans des étapes
> `Invoke-OptionalStepWithRetry` — qui **n'arrêtent pas le run** et le laissent finir en
> « succès » : un chemin de script coupé par un `\r` (`ab94c9d`), et une colonne manquante
> qui faisait tomber le recensement (`8ee966f`). **Vérifier que ces étapes ont une sonde**
> *(tâche C.17-ter)* — c'est la classe de défaut la plus dangereuse ici.
>
> **`C.9`, la création d'annonce, vient après.** Son audit est déjà fait *(voir le journal
> du plan)* : l'annonce vit déjà sous **son** numéro, donc elle ne peut pas fabriquer deux
> fiches ; ses trous sont `app_mandat_champ_app` et les empreintes de relation.
>
> **Ce qui vient d'être fait, et qui sert de patron.** Un contact **naît dans l'app**, prouvé
> deux fois en réel : identité `10 000 002` tirée de la plage de l'app, case cible `605 453`
> rapportée par le worker, **une seule fiche**. L'essai a trouvé **deux défauts que rien
> d'autre n'aurait trouvés** — la case cible ne partait pas *(un `updated_at` inexistant
> faisait rejeter tout le PATCH)*, et le retour fabriquait **une seconde fiche**.
> ⚠ **La leçon du second, elle vaut pour C.9** : la substitution d'un numéro se fait **à
> l'entrée du build**, jamais au push — les clés des relations et des recherches sont des
> **empreintes calculées sur ce numéro**, et traduire après coup ferait supprimer ces lignes
> au run suivant. `4e82f25` · `13ecedc` · `6cbb59a` · `21565cb`.
>
> ~~**Deux fiches d'essai sont gardées exprès** — `10000001` et `10000002`~~ — **supprimées le
> 22/09** pour libérer la plage *(liste, bloc L4-c ⓪)*. Ces deux numéros sont aujourd'hui la
> **doublure** des contacts Hektor 1 et 2 — ce ne sont plus des fiches d'essai.
>
> ⛔ **Ne jamais relire la section ci-dessous comme un ordre du jour** : elle date d'avant
> le 19/09 et décrit le chantier des transactions, terminé.

> **18/09/2026 — LES TRANSACTIONS SONT PRÊTES.** L'audit global du 18/09 a relu la liste
> `① CE QUI RESTE À FAIRE` contre le code, **rubrique par rubrique, sous les mêmes numéros**
> (C.4, C.4-bis/C.1', C.19-d 3.5, C.17-ter, D.0, 0.3, E.0-bis, A.2). L'ordre avant E.2 est dans
> la **page de tête de la liste** ; on commence par **C.4 : archiver une recherche vise la
> mauvaise** quand le contact en a plusieurs.
> Ce qui suit dans cette section date d'avant le 18/09 : il reste vrai, il n'est plus l'ordre.

**Chantier : `C.19-d` — LE REGISTRE DES TRANSACTIONS.**
⚬ **LA PAGE DE TÊTE DE LA LISTE REMPLACE SA LECTURE** : `notice/LISTE_TACHES_A_COCHER_2026-08-29.md`,
les **57 premières lignes**. Elle porte la tâche en cours, les trois suivantes, ce qui attend
Frédéric, et les renvois par numéro de ligne. Le reste du document est une **archive** : on
l’ouvre à la ligne indiquée, jamais en entier (6 500 lignes).

Cinq phases, à partir de la **ligne 1372**.

```
PHASE 0  mesurer, bloquante        l. 1912   0.1 quasi finie  ·  0.2 0.3 0.4 faites
PHASE 1  le registre, invisible    l. 2328   terminee
PHASE 2  l'ecran                   l. 2903   reste 2.4 (l. 3333), 2.6, 2.7 COTE ECRAN (l. 3556), 26bis-TRANSACTIONS (l. 2906)
PHASE 3  l'ecriture part chez Hektor  l. 3635   EN COURS
PHASE 4  menage                    l. 5290   reste 4.1 (l. 5293), 4.2 (l. 5297)  ·  4.3 faite le 07/09
```

**Au 08/09/2026 — LES TROIS GENRES SONT MODIFIABLES, ET PROUVÉS EN RÉEL.**

```
compromis  50078   165 000 → 175 000, quatre fois · aucun doublon · fiche vérifiée
vente      23301   créée, modifiée 175 000 → 176 500, supprimée · annonce rendue intacte
offre      33050   165 000 → 167 000  ·  33048 REFUSÉE re-acceptée puis re-refusée
```

**Au 10/09/2026 — CE QUE L'API CACHE, LE WORKER LE LIT MAINTENANT.**

Le registre a gagné quatre colonnes tirées de `payload_json` (`mandants_json`,
`notaires_json`, `propositions_json`, `commission_agence`) et le worker ne jette
plus le formulaire de Hektor : à chaque écriture il en tire ce que l'API ne rend
jamais, **sans une requête de plus**, dans `app_affaire_console`.

```
notairesAcquereur[] · notairesMandant[]     0 sur 10 586 par l'API
unitesEntreePercent / unitesSortiePercent   le partage de la commission
conditions suspensives : retenues + CATALOGUE de l'agence
montantHonoraireEntree / tauxHonoraireEntree   le TAUX VENDEUR (manque n°1 de 0.1)
```

Prouvé trois fois en réel sur le compromis 50078, et rejouable hors ligne :
`node Console/test_lecture_console.js` — onze assertions sur du HTML capturé.

⭐ **`2.6` A CHANGÉ DE NATURE.** La piste « la typologie du contact filtre » venait
de quatre mesures ; **le parc la dément à 39 %** — sur 12 446 acquéreurs réels de
compromis, 4 886 ne portent PAS la typologie et sont pourtant attachés. Et la
comparaison console/API sur 649 compromis donne **zéro écart** : l'API ne cache
rien, le défaut est bien à l'ÉCRITURE. L'instrumentation que le dossier réclamait
depuis le 06/09 est posée (ce qui part vraiment, ce que le formulaire garde, ce
que `findProspect` rend). ⚠ Reste l'essai avec deux contacts, jamais fait.

⚠ **LES TROIS ESSAIS « DEUX ACQUÉREURS » (02, 06 et 07/09) UTILISAIENT LE MÊME
  COUPLE**, dont un contact que Hektor n'a jamais attaché. Ils ne prouvent donc
  pas que Hektor n'en garde qu'un.

### Les outils du 10/09

```
Console/lecture_assistant.js                  le lecteur, PARTAGE (extrait du worker)
Console/test_lecture_console.js               11 assertions, N'APPELLE PAS HEKTOR
Console/extract_hektor_compromis_console.js   le rattrapage, LECTURE SEULE
phase2/sync/sync_hektor_compromis_console.py  son pilote, cadence de reference
```

⚠ **LA CADENCE N'EST PAS NEGOCIABLE** : 1 requête par compromis, 0,5 s entre deux,
lots de 100 avec 60 s, vagues de 2 000 avec 300 s. C'est la méthode de
`notice/NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md`, la seule qui n'ait jamais
rien déclenché (56 926 lectures). La coquille est écartée pour lire — mesuré le
10/09 : le formulaire arrive identique sans elle, ce qui divise le flux par deux.

**LA TÂCHE OUVERTE est `3.5` — L'ESSAI RÉEL DE LA SUPPRESSION** (liste, l. 5163).

Les cinq pièces sont codées depuis le 07/09 et le journal a été ajouté le 16/09 —
mais il n'avait **jamais été lu** (`request` au lieu de `_request`, corrigé le 17/09
par `bcb05fe`). Sans ce correctif, une suppression ordonnée par l'app **revenait au
run suivant**. Il ne reste que la preuve de bout en bout. ⚠ **Elle écrit chez Hektor
et demande un go explicite.**

**Les deux suivantes** : les **mandants depuis l'app** (lot 3, l. 4018), puis
**2.7 côté écran** (l. 3556) et **2.6** (l. 3412).

⛔ **CE QUE FRÉDÉRIC A MIS DE CÔTÉ**, et qu'on cesse de remonter à chaque tour : les
**2 dettes** (la surveillance qui crie depuis juillet · le numéro de contact qui ne
voyage pas avec sa fiche).

### `3.2e` — la répartition de commission *(détail : liste, section 3.2e)*

⛔ **RIEN NE PART CHEZ HEKTOR** (Frédéric, 14/09, 06bd38b) : leur modèle ne sait pas
exprimer un quart des répartitions réelles — l'acquéreur est suivi par une AUTRE agence
dans 26,6 % des cas. *« Mieux vaut un champ absent qu'un champ menteur. »*
La table existe et elle est remplie ; le reste est **garé**. ✅ Le point 1 — lever
`VenteDateStart` à 2000 — est fait (993dcc5). ⛔ L'étape de conversion reste
**désactivée dans le run** (8456e9f).

**Au 17/09 — LA JOURNÉE QUI A TOUT ÉPROUVÉ D'UN COUP.** `2.7` (couverture mandat
48 % → 74,9 %), `3.3` (le contrat d'autorité vidé), `3.1` (le verdict du carnet), le
chaînage (12 670 chaînes, les 4 copies de la règle d'accord, test ⑤ à 0 écart) et la
note libre d'une transaction. ⚠ **Et un bannissement d'IP à 06:34** : le balayage du
miroir fabriquait un client neuf par pièce, donc 17 logins OAuth en 22 s. Corrigé
(`c524f7e`), **pas encore éprouvé en réel** — le run de 5 h est son juge.

> ⭐ **`0.1` est quasi finie.** Sa phrase *« l'assistant refuse d'avancer sous
> automatisation »* était **fausse** : il refuse un formulaire qu'on ne lui rend pas
> fidèlement. **23 champs de données classés sur 24** ; le dernier,
> `agenceReseauSelected` (la rétrocession), est **hors périmètre par décision de Frédéric**,
> pas par oubli. Reste le relevé de l'offre.
>
> ⚠ **« C » NE VEUT PAS DIRE « il refuse l'écriture ».** Hektor *calcule* le net vendeur et
> la commission si on n'envoie rien — mais **il garde ce qu'on lui envoie, sans vérifier**.
> Il a accepté une fiche à *« 177 345 € »* pour un prix public de 175 000 sans broncher.
> **Rien ne rattrape une incohérence : l'alerte de la modale est le seul filet.**
>
> ⚠ Le risque des **conditions suspensives est LEVÉ** (mesuré le 08/09) : une modification
> les préserve. Le principe *« on repose ce que Hektor a rendu »* les protège sans code.

### Les outils du 08/09 — tous rejouables

```
Console/releve_assistant_etapes.js      l'inventaire des étapes    N'ÉCRIT JAMAIS
Console/mesure_reprise_compromis.js     le formulaire pré-rempli ? N'ÉCRIT JAMAIS
Console/mesure_reprise_panier.js        le panier retient-il l'id ? N'ÉCRIT JAMAIS
Console/campagne_champs_compromis.js    ⚠ LE SEUL QUI ÉCRIT CHEZ HEKTOR
phase2/checks/verifier_regle_chainage.py       les 3 copies de la règle, confrontées
phase2/checks/test_chainage_vente_ferme.py     le correctif du run, sur registre jetable
```

> ⚠ **Il existe deux tâches nommées `0.1`** — celle de la phase 0 (l. 1919) et une autre,
> sans rapport, l. 340.

---

---

## Descendus du §2 de CLAUDE.md le 03/10/2026

> Le §2 avait regrossi a **832 lignes sur 989** -- la maladie exacte contre laquelle
> sa propre regle a ete ecrite. Ces blocs sont CLOS ou portaient deja la mention
> *« ancien cadre, garde pour le pourquoi »* : c'est la definition de ce journal.
> On l'ouvre pour comprendre **un pourquoi**, jamais pour savoir quoi faire.

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

