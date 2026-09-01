# La liste complète — 62 tâches, item par item

*Posée le 29/08/2026. Le plan dit le **pourquoi** en 1 700 lignes ; cette liste dit le **quoi**.*

> **RÈGLE** *(plan, 29/08)* : une tâche n'est cochée que si son **énoncé** est couvert, et la
> mesure qui le prouve doit répondre à la question que la tâche posait.

**Légende** `[x]` fait et vérifié · `[ ]` à faire · `[—]` annulé ou dissous

*Première version incomplète : elle ne couvrait que la session des 28-29/08. Corrigée le jour
même sur remarque de Frédéric — « il manque des étapes… saisir dans l'app, retirer les calques
optimistes, A.1 A.2 A.3 ». **Les 62 tâches du plan sont désormais toutes ici.***

---

# ① CE QUI RESTE À FAIRE — dans l'ordre décidé le 29/08

## 1. C.4 — LES 16 WORKERS *(5 convertis sur 16)*

Principe : *« écrire d'abord, envoyer, comparer au retour »*.

```
> ⚠ **CE BLOC ETAIT FAUX JUSQU'AU 31/08 AU SOIR.** Il annonçait 9 workers « a
> convertir » dont TROIS etaient faits depuis le 30/08, avec la mention trompeuse
> « insert direct -- verifie » qui decrivait l'etat d'AVANT leur conversion.
> Corrige en LISANT LE CODE (les RPC `app_*_optimistic` et leurs appelants dans
> `api.ts`), pas les notes. C'est de la que venait l'impression de refaire les
> memes choses.

C.4 EST TERMINE : 14 CONVERTIS + 2 SANS OBJET = 16/16      cloture le 01/09

> ⚠ **L'INVENTAIRE DE C.4 A ETE FAUX QUATRE FOIS.** Il annoncait 5/16 le matin
> du 31/08 ; trois workers etaient deja faits depuis le 30/08 et portaient encore
> la mention trompeuse « insert direct -- verifie » ; un quatrieme
> (delete_hektor_contact_search) l'etait aussi et personne ne l'avait vu.
> **La liste ne suivait pas le code.** C'est de la que venait l'impression de
> refaire les memes choses -- et c'est ce qui a fait naitre la regle « auditer le
> CODE avant chaque etape », entree en memoire projet le 31/08.

CONVERTIS (14 sur 16)                        mesure dans le code le 31/08
[x] update_hektor_annonce_fields        app_edit_annonce_optimistic
[x] update_hektor_contact               app_edit_contact_optimistic
[x] update_hektor_contact_search        app_edit_search_optimistic
[x] change_hektor_annonce_status        app_change_annonce_status_optimistic
[x] create_hektor_draft_annonce         app_create_annonce_job_optimistic
[x] archive_hektor_annonce              app_archive_annonce_optimistic     30/08
[x] restore_hektor_annonce              app_restore_annonce_optimistic     30/08
[x] assign_hektor_annonce_negotiator    app_assign_negotiator_optimistic   30/08
[x] create_hektor_contact               app_create_contact_optimistic      31/08
                                        eprouve a l'ecran : badge, 20 s, erreur
[x] add_hektor_contact_search           app_create_search_optimistic       31/08
                                        eprouve a l'ecran : cycle complet

[x] delete_hektor_contact_search   DEJA CONVERTI LE 30/08 -- constate le 01/09
                                   app_console_create_delete_contact_search_job
                                   ecrit archive=true, is_active=false DANS LA
                                   MEME TRANSACTION, garde une photo d'avant
                                   (base_snapshot) et pose un verrou portant le
                                   numero du travail (le balayage l'efface au
                                   succes, le rearme a l'echec).
                                   ⚠ CE N'EST PAS UNE SUPPRESSION mais un
                                   ARCHIVAGE : le worker appelle
                                   archiveHektorContactSearch et rend
                                   « status: archived ». Hektor ne sait pas
                                   supprimer une recherche, il pose une date.

[x] create_hektor_mandant_contact  FAIT 31/08   app_create_mandant_contact_optimistic
[x] link_hektor_mandant            FAIT 31/08   app_link_mandant_optimistic
                                   (+ le garde-fou de role qui MANQUAIT : le
                                   front inserait le travail en direct)
[x] update_hektor_mandant_contact  FAIT 31/08   app_update_mandant_contact_optimistic
                                   « modifier un mandant » EST « modifier un
                                   contact » : on APPELLE app_edit_contact_optimistic
                                   au lieu de recopier sa logique, et on designe
                                   notre travail au balayage pour qu'une meme
                                   modification ne parte pas DEUX fois.

[—] delete_hektor_annonce          SANS OBJET -- decision du 15/05, a revoir
[—] delete_hektor_contact          APRES la coupure des workers

    POURQUOI SANS OBJET, et ce n'est pas un renoncement.
    notice/NOTE_SUPPRESSION_ANNONCE_HEKTOR_2026-05-15.md le dit deja :
       « Le nettoyage Supabase/local est lance seulement APRES l'appel de
         suppression Hektor. Si Hektor refuse la suppression ou si la session
         admin n'est pas active, les donnees locales ne sont pas nettoyees. »
    C'est une DECISION, pas un oubli -- et elle est juste : une suppression est
    IRREVERSIBLE. Effacer chez nous d'abord et voir Hektor refuser, c'est
    detruire pour rien.

    ET LE PRINCIPE DE C.4 NE S'Y APPLIQUE PAS. « Ecrire d'abord » protege LA
    SAISIE. Or :
       creer un contact       ->  un nom, un telephone   <- du CONTENU a sauver
       modifier une annonce   ->  un prix, une surface   <- du CONTENU a sauver
       supprimer un contact   ->  RIEN
    Une suppression n'a rien a sauvegarder : il n'y a qu'une intention, deja
    conservee dans le travail, qui depuis C.1' ne se perd plus.

    ET L'OPTIMISME Y SERAIT NUISIBLE : afficher « supprime » avant la reponse
    de Hektor, c'est montrer une chose FAITE qui peut echouer. Si Hektor refuse,
    l'objet REVIENT -- exactement le mensonge d'ecran que ce projet corrige
    partout ailleurs.

    MESURE QUI CONFORTE : 114 suppressions d'annonces + 8 de contacts entre mai
    et aout, TOUTES « done ». Aucun echec. Et toutes journalisees dans
    app_console_deleted_*_log avec l'etat complet d'avant (before_json).

    A REVOIR APRES LA COUPURE DES WORKERS -- decision de Frederic, 01/09 : quand
    Hektor ne repondra plus, une suppression devra bien s'ecrire quelque part.

    ⚠ ET TOUT CECI EST DORMANT, PAR CONSTRUCTION.
    contrat_autorite.py : CHAMPS_APP_ANNONCE = ()   -- VIDE
    Le carnet se remplit, RIEN NE L'APPLIQUE. C'est l'interrupteur du chantier,
    et le laisser eteint ne change rien en production. Convertir les six
    derniers ne changera donc rien non plus tant qu'il est eteint.

LA BRANCHE MANQUANTE DU CHANGEMENT DE STATUT
[x] Actif · Offre · Compromis · Clos    14 executions depuis mai
[x] VENDU                               EPROUVEE le 31/08 (voir C.4-Vendu)
```

## 2. C.19 — LES GESTES DE TRANSACTION *(finir)*

```
[x] refuser une offre      eprouve chez Hektor    33027 : bouton disparu, temoin intact
[x] accepter une offre     eprouve chez Hektor    33026
[ ] ANNULER un compromis                          JAMAIS EXECUTE
[ ] SUPPRIMER une vente                           JAMAIS EXECUTE
[ ] le RETOUR EN ARRIERE sur refus                JAMAIS TESTE -- garde-fou de l'instantane
[x] redemarrer les workers                        fait plusieurs fois le 31/08
[x] deployer le front                             en ligne, bundle index-BLZWZur4
```

## 3. C.4-bis-0 — VÉRIFIER LA DÉTECTION *(préalable au filet)*

> **On ne rejoue pas ce qu'on ne sait pas raté.** Un travail marqué `done` n'est jamais
> repris : poser le filet avant la détection, c'est le tendre sous un trou qu'on ne voit pas.

```
[x] le defaut prouve par un essai       offre inexistante -> travail "done", etat faux affiche
[x] la cause relevee chez Hektor        "[]" = echec, "1" = succes -- il DIT quand il echoue
[x] le principe corrige sur mes 3 gestes  on EXIGE la preuve du succes
[x] verifier les 18 handlers un par un   FAIT le 01/09 -- ET C'ETAIT DEJA FAIT
                                        Demande de Frederic : « mais on avait
                                        deja fait les 18 ». Verifie dans le code.

    20 handlers ecrivent chez Hektor
    18 EXIGENT UNE PREUVE  -- ils levent une erreur explicite quand Hektor ne
                              confirme pas : « non confirmee », « non modifiee »,
                              « introuvable », « pas lie »
     2 NE L'EXIGENT PAS    -- voir ci-dessous

    ⚠ CINQUIEME MESURE FAUSSE PAR RECHERCHE DE MOTIF. Ma premiere passe n'en
    trouvait que 15 : la preuve est souvent dans la fonction APPELEE, pas dans le
    handler lui-meme. Exemple -- handleCreateHektorContact parait aveugle, mais
    createHektorContact fait :
        const contactId = parseHektorCreatedContactId(response.text);
        if (!contactId) throw new Error("Creation contact Hektor non confirmee");
    Il a fallu suivre les appels sur deux niveaux pour voir juste. C'est
    exactement l'avertissement que le plan portait -- et je suis retombe dedans.

[ ] corriger ceux qui deduisent          DEUX handlers, tous deux SIGNATURE
    handleRelanceSignature          relance d'une signature
    handleCancelSignatureProcedure  annulation d'une signature

    Tous deux envoient leur ordre puis rendent « reminded » / « cancelled » SANS
    verifier que la procedure a bouge. Ils gardent les 160 premiers caracteres de
    la reponse sans les lire.

    ➡ LE PLAN DU 20/08 AVAIT VU JUSTE : « Seul indice a confirmer :
      handleRelanceSignature ne semble verifier que son message d'entree ».
      L'indice etait bon, et il vaut aussi pour l'annulation.

    ⏸ NE PAS Y TOUCHER -- decision de Frederic, 01/09. Ces deux gestes dependent
      de l'abonnement ImmoSign de Hektor : ils disparaitront le jour du contrat
      de signature en propre (A.2). Corriger un geste voue a disparaitre n'a pas
      de sens tant que A.2 n'est pas tranche.

    ➡ C.4-bis-0 N'EST DONC PAS « 1 a 2 jours de relecture » mais DEUX handlers,
      tous deux hors du chemin critique. Le filet C.4-bis peut etre pose : la
      detection est bonne sur 18 gestes sur 20, et les 2 restants ne sont pas
      des gestes metier courants.
```

> ### ⚠ ET UN SECOND SENS, QUE C.4-bis-0 N'AVAIT PAS PREVU *(constate le 31/08)*
>
> La tache ne cherchait qu'un defaut : **deduire du silence** -- un echec qui
> passe pour un succes. L'essai du 31/08 a montre **le cas symetrique**, et il
> est tout aussi couteux :
>
> ```
>    deduire du silence   ->  un echec passe pour un succes  ->  le filet ne le voit pas
>    relire a l'aveugle   ->  un succes passe pour un echec  ->  le filet le rejoue pour rien
> ```
>
> Le rattachement du mandant du 28/08 avait **REUSSI** et s'est declare en echec,
> parce que la relecture etait filtree par l'agence du compte. Sans correction,
> le filet aurait rejoue un rattachement deja pose.
>
> **Quand on posera C.4-bis, chercher les DEUX sens.**

## 4. C.4-bis — LE FILET DE REJEU *(geste (c) de C.1', rouvert)*

```
[x] le defaut mesure                    6 en erreur, 0 rejoue, tentatives=1 partout
[ ] file app_affaire_pending
[ ] balayage a la minute                rejeu 5 / 10 / 15 / 20 / 25 min
[ ] abandon a 5 -> conflict
[ ] bandeau sur la fiche
[ ] perimetre : les 3 gestes + le changement de statut
```

## 5. C.16 — LES CONTACTS QUI N'EXISTENT PLUS
```
[x] remesuree                           825 fiches actives, pas 284 269
[ ] marquer disparues les 825 actives   jamais supprimer -- regle du projet
[ ] traiter les 5 454 archivees
[ ] poser le mecanisme "un contact a quitte le listing"   patron : reconcile_annonce_scope
```

## 6. C.9 — LA CRÉATION PART DE L'APP  ·  7. 26bis-③
```
[ ] C.9      creer un bien SANS passer par Hektor         1 a 2 sem.
[ ] 26bis-3  le serveur tient une annonce que le miroir ignore
             -> trancher les 46 colonnes (37 dans un seul blob)   collee a C.9
```

## 8. C.11 — MÉNAGE
```
[ ] supprimer les tables mortes
```

## 9. A.3-TECHNIQUE — LE REGISTRE DES MANDATS
```
[ ] un vrai registre, plus une vue des annonces    1 105 mandats invisibles
[ ] trois couches de numerotation                  Hektor / Protexa / la tienne
                                                   3 a 5 j, TANT QUE HEKTOR VIT
```

## 10. D — RAPATRIER LES FICHIERS *(irréversible)*
```
[ ] D.1a  MESURER d'abord                  combien de cloud_available sans fichier local -- 1 h
[ ] D.1   documents                        40 493 a redimensionner
[ ] D.2   photos                           1 397
```

## 11. FIN DE PLAN
```
[ ] C.13-c  rattraper les 23 715 dates de cloture     avec les 3 regles validees
[ ] 0.3     finir 19-R1                               rattrapage acquereurs, 4 h 35
[ ] B.3     le declencheur de descente                en attente du journal
[ ] E.1     19-R2, la veille de la bascule            DERNIERE OCCASION
[ ] E.2     bascule des negociateurs sur l'app        decision d'organisation
[ ] E.3     les workers deviennent invisibles
[ ] E.4     le jour J                                 distributeur a 100 000
[ ] F.1     utilisateurs, roles et droits             APRES la coupure
```

## 12. CE QUI NE DÉPEND PAS DU CODE — et qui bloque la coupure
```
[ ] A.1  PORTAILS      sortie en nom propre + reprise des ~350 annonces en ligne
[ ] A.2  SIGNATURE     ton propre contrat (ImmoSign appartient a Hektor)
[ ] A.3  REGISTRE      obligation legale, aujourd'hui adosse a Hektor
```
> **Aucun travail technique ne permet de couper Hektor tant que A.1 et A.2 ne sont pas réglés.**
> Ils sont **à zéro**, et chaque semaine de retard s'ajoute intégralement à la date de coupure.

---

# ② LES CINQ GESTES QUI T'APPARTIENNENT

```
[ ] redemarrer les workers
[ ] deployer le front sur Vercel        n'a pas pu etre verifie (403 sur l'API)
[ ] choisir l'annonce pour "Vendu"      la vente sera definitive
[ ] choisir le compromis a annuler      tous les actifs sont de vraies affaires
[ ] retirer la trace d'essai            affaire 9 : 123 456 au lieu de 79 000
                                        (ta decision : en fin de chantier)
```

---

# ③ CE QUI EST FAIT — 37 tâches

## Protéger l'existant *(bloc 0)*
```
[x] 0.1  sauvegarde de app_search_registry et app_affaire_ledger   verifie en decompressant
[x] 0.2  regle : le miroir ne se supprime jamais
[x] 0.4  acces public ferme sur app_dossiers_current
[x] 0.5  les 5 vues de surveillance fermees
[x] 0.6  tmp_etape12_avant supprimee
[x] 0.7  audit des fonctions appelables sans etre connecte   36 restent : DETTE ASSUMEE
[x] 0.8  le correctif conflict=false sur les 3 balayages
```

## Les recherches acquéreur *(1 à 4sexies)*
```
[x] 1         rattacher l'irremplacable          15 lignes, 0 perdue
[x] 2         supprimer le recalculable          13 339 lignes
[x] 2bis      balayage nocturne des orphelins
[x] 2ter      sentinelle sur les non rattachables
[x] 2quater   le balayage tient un carnet
[x] 3         le numero Hektor d'annonce peut etre vide + sentinelle
[x] 4         identite des transactions          28 980 affaires numerotees
[x] 4bis      archivee, toujours -- Hektor ne sait pas supprimer une recherche
[x] 4bis-A    les archivees ne sont plus supprimees   6 777 recuperees
[x] 4bis-B    le verrou du moteur de rapprochement
[x] 4ter      un numero propre pour la recherche
[x] 4quater   observer la doublure
[x] 4quinquies  figer le nom                     76 841 noms, 0 doublon
[x] 4sexies   sentinelle "une recherche ne disparait jamais"
```

## Le serveur apprend de l'app *(bloc B)*
```
[x] B.1  la descente                     124 tables, 1 530 973 lignes
[x] B.2  la descente des fiches          10 doublures
[x] B.4  le comparateur + 2 sondes       dans run_descente.ps1
[x] B.5  la tache planifiee GTI Descente 07:30
```

## L'app devient l'auteur *(bloc C)*
```
[x] C.2a  identite des contacts, la relecture
[x] C.2b  identite des contacts, le code       355 769 numeros, 19 tables
[x] C.3   fermer la porte sortante des recherches
[x] C.6   le domicile de l'annonce             app_annonce_champ_app
[x] C.7   le serveur lit sa base               contrat d'autorite branche
[x] C.12  la sortie de conflit, contacts
[x] C.13-a  le domicile du mandat
[x] C.13-b  le contrat s'allume                premier champ app-owned
[x] C.13    la cloture ne passe plus par Hektor + elle ecrit vraiment
[x] C.14  le titre francais cote serveur
[x] C.15  les 6 types d'offre + immo pro       4 165 annonces qui n'entraient jamais
[x] C.17  le monitoring voit le reseau tomber
[x] C.17-bis  le moniteur ne meurt plus en parlant
[x] C.18  bug agence multi-agences             3 occurrences depuis juin
[x] C.19  etapes 1 a 3 + le code de l'etape 4
[x] E.0   audit : que ne peut-on PAS faire dans l'app ?
```

## Fait le 29/08, hors tâches numérotées
```
[x] l'analyse des transactions de bout en bout   29 293, multiplicite normale
[x] le releve des appels de Hektor sur ecran     updateOffre / clotureCompromis / deleteVente
[x] l'audit du plan face a la realite            4 derives trouvees
[x] la regle du "fait" posee dans le plan
[x] C.1' rouverte, C.4 corrigee, ordre revu
[x] le correctif anon consigne dans un fichier   il manquait
[x] cette liste
```

---

# ④ ANNULÉ OU DISSOUS — à ne pas rechercher

```
[—] C.5   registre d'affaires et mandat des transactions   ANNULEE le 25/08, retour arriere
[—] C.8   LE CALQUE DISPARAIT + la barriere                DISSOUTE le 25/08 :
          "ses deux moities n'etaient pas des taches"
[—] C.1   la regle d'arbitrage et ses 3 cas d'ecart        SUPPRIMEE le 24/08 -- l'etape 2
                                                            fait disparaitre le cas (3)
[—] C.10  corriger le modele "au moins" de la modale       SUPPRIMEE le 24/08
[—] 5a    renommer les 11 parametres ambigus               RAYEE le 20/08 -- Postgres refuse
```

> **« Retirer les calques optimistes » n'est plus une tâche** : c'est C.8, dissoute le 25/08
> après mesure. Les calques restent, et c'est voulu — ils sont le mécanisme *« écrire d'abord »*
> que C.4 généralise.

---

# ⑤ LE COMPTE

```
   62 taches au total
   37 faites et verifiees
    5 annulees ou dissoutes
    4 partielles          C.1' · C.4 · C.13 · C.19
    1 neuve               C.4-bis
   15 ouvertes
```

**Et les trois qui commandent tout — A.1, A.2, A.3 — ne dépendent pas du code.**

---

*Cette liste se tient à jour avec le plan. Une case ne se coche que sur une mesure, et la mesure
est écrite à côté.*

---

# AJOUTS DU 29/08 — issus de l'essai reel sur Hektor

*Trois taches nees d'un essai qui a trouve un verbe faux et deux faux succes.*

| | tache | etat |
|---|---|---|
| **C.19-a** | verbe du compromis corrige *(`annonce-SuiviVente-cloture`)*, vocabulaire du refus elargi, arbitre par geste | ✅ **fait** — 6/6 appliques, syntaxe validee, regex eprouvee sur les 5 refus mesures |
| **C.19-b** | eprouver l'annulation d'un compromis **ACTIF**, et la suppression d'une vente posee **sur** ce compromis actif | ⏳ **bloque** — le compte admin ne peut pas creer de compromis *(mode `ajoutebien` -> refus)*. **Demande un compte negociateur** |
| **C.19-c** | **le choix « laisser actif » / « archiver » a l'enregistrement d'une vente** | ✅ **CLOS le 01/09 — le choix est RETIRE** *(voir plus bas)* |

## Sur C.19-c, et pourquoi ca compte

L'enregistrement d'une vente chez Hektor offre **deux boutons**, releves sur ecran le 29/08 :

```
   « Enregistrer & laisser actif »     ->  le bien reste dans Biens actuels, affiche BIEN VENDU
   « Enregistrer & archiver »          ->  NON EPROUVE
```

Ce choix **agit sur le statut de l'annonce**, donc il ne peut pas rester implicite : c'est une
decision metier que l'app doit porter, pas un defaut cable dans le worker.

Il n'appartient **pas** aux trois gestes corriges ci-dessus — il appartient a la **branche
« Vendu » de C.4**, celle qui cree la vente. A traiter avec elle, une fois la seconde issue
eprouvee.

## Une observation a verser au dossier de la modale de statut

Cliquer « SOUS COMPROMIS » dans le statut du bien a change **le statut sans creer de
compromis** — alors que le meme clic, sur un bien qui n'en avait aucun, avait ouvert
l'assistant et cree le compromis 50044.

➡ **Le statut de l'annonce et la transaction sont decouples chez Hektor.** La modale n'est pas
un createur de transaction : elle en ouvre un *quand il n'y a rien*. C'est une reponse directe
a la question posee le 29/08 *(« le statut change et une transaction se cree en fonction, c'est
bien ca ? »)* : **non, pas toujours**.

---

# MISE À JOUR DU 29/08 AU SOIR — après les essais réels

## C.19 — ce qui est désormais éprouvé, et par quel canal

```
[x] refuser une offre         eprouve chez Hektor          33027
[x] accepter une offre        eprouve chez Hektor          33026
[x] ANNULER un compromis      eprouve A LA MAIN            50044, 50045, 50046
[x] SUPPRIMER une vente       eprouve A LA MAIN            23287
[x] le retour en arriere      job en erreur sur id bidon   14:45, apres correctif
[x] redemarrer les workers    fait par Frederic
[ ] un VRAI travail par le worker    cancel_hektor_compromis : 0 travail, JAMAIS
[ ] un VRAI travail par le worker    delete_hektor_vente     : 0 travail, JAMAIS
[ ] pousser les 53 commits           sinon le front reste fige au 28/08
[ ] deployer le front
```

> **La distinction qui compte** : *éprouvé à la main* ≠ *éprouvé par la chaîne*. Les verbes sont
> justes, les réponses connues, le code corrigé — mais **aucun travail n'est jamais passé par
> `cancel_hektor_compromis` ni `delete_hektor_vente`**. C'est la première chose à faire.

## LA PREUVE QUE LA SUPPRESSION D'UNE VENTE MARCHE

*Frédéric a douté — « as-tu déjà réussi à supprimer une vente ? ». Doute fondé : la fiche
n'affichait qu'un seul compromis alors que 50044 et 50045 existaient tous deux, donc le bloc
« Vente du bien » pouvait masquer de la même façon. **Vérifié par l'AUTRE porte, l'API v2 :***

```
   /Api/Vente/VenteById/  id=23287  ->  404 Not Found   SUPPRIMEE
   /Api/Vente/VenteById/  id=23288  ->  404 Not Found   SUPPRIMEE (par l'enregistrement desarchivant)
   /Api/Vente/VenteById/  id=23289  ->  200, 3822 car   EXISTE
```

Le 404 contre le 200 est un témoin propre : l'endpoint répond, et il ne trouve plus les deux
premières. **`ventes-deleteVente` fonctionne**, et la destruction de 23288 était bien réelle.

## C.19-b et C.19-c — réévaluées

| | |
|---|---|
| **C.19-b** | ✅ **fait** — le blocage que j'avais annoncé *(« l'admin ne peut pas créer de compromis »)* était **faux** : `ajoutebien` est un appel annexe. Frédéric l'a vu avant moi |
| **C.19-c** | ✅ **CODÉ le 30/08** *(`6bd5b04`)* — le choix est à l'écran, défaut « laisser actif ». ⚠ **L'archivage NE passe PAS par leur bouton** : la capture du 28/08 ne couvre que la popin d'offre, donc **je n'ai pas la mesure** de ce qu'envoie « Enregistrer & archiver » — et cette issue a **détruit la vente 23288** *(404 à l'API)*. On compose donc deux gestes éprouvés : créer la vente, puis `archive_hektor_annonce` *(127 exécutions)*, **et seulement si la vente est confirmée**. Reste le passage réel |

## Le compte, corrigé

```
   7 travaux en erreur (etait 6)      tentatives max = 1        toujours 0 rejoue
   5 workers convertis sur 16         inchange
   53 commits non pousses             origin/main au 28/08
```

---

# ✅ POINT 1 DE L'AUDIT — TERMINÉ le 29/08 au soir

*« Faire passer un VRAI travail par le worker. » C'était la première tâche de l'ordre retenu,
et elle a trouvé ce qu'aucun essai à la main n'aurait montré.*

## Ce que le premier passage a révélé — un défaut dans mon propre correctif

```
   travail 1   cancel_hektor_compromis, compromis 50047
               Hektor a repondu "true"          <- le jeton de SUCCES
               clotures sur la fiche : 0 -> 0   <- ma relecture n'a RIEN vu
               -> ERROR, alors que l'annulation avait REUSSI
```

**Cause** : le bloc suivi-vente n'est pas dans le HTML de la fiche, il est monté côté client.

```
   ?page=/mes-biens/mon-bien       208 274 car  ->  0 marqueur
   mode=chargeannonce_Accueil      217 397 car  ->  cloture:1 clore:1 supprimerVente:1
```

> **L'enseignement, et il vaut pour tout le reste du chantier.** Dans le navigateur le bloc
> **est** là — c'est le JavaScript qui l'a mis. Le worker ne voit que ce que le **serveur**
> envoie. **Aucun essai à la main ne pouvait révéler ce défaut.** C'est exactement pourquoi ce
> point passait avant tout le reste.

Corrigé (`a4e7600`), workers redémarrés, essai rejoué.

## Les deux handlers ont désormais tourné, et l'effet est vérifié

| travail | résultat | preuve |
|---|---|---|
| `cancel_hektor_compromis` — compromis **50048** | ✅ **done** | `Compromis clôturé` sur la fiche |
| `delete_hektor_vente` — vente **23289** | ✅ **done** | `/Api/Vente/VenteById/` → **404** |

*La preuve de la vente vient de l'**API v2**, canal indépendant de la console — pas de la fiche,
dont on sait maintenant qu'elle peut masquer.*

## La vente ne disparaît que dans UN cas — mesuré quatre fois

```
   desarchivage par l'assistant de vente   ->  vente 23288 DETRUITE
   desarchivage propre par upval (worker)  ->  vente 23289 intacte
   suppression du compromis 50046          ->  vente 23289 intacte
   suppression du compromis 50047          ->  vente 23289 intacte
```

## Ce qui reste du point 1

```
[ ] pousser les 53 commits      sinon le front reste fige au 28/08
[ ] deployer le front           les 4 boutons existent dans le code, pas dans l'app
```

## État du bac à sable après l'essai

```
   annonce 62774     active (archive=0), statut Vendu
   compromis 50048   cloture      <- a retirer
   ventes            AUCUNE       23287, 23288, 23289 toutes supprimees et verifiees
   affaire 9         123 456 au lieu de 79 000   <- a retirer en fin de chantier
```

> ⚠ **CET INSTANTANÉ EST PÉRIMÉ — relu par l'API le 30/08 :**
>
> ```
>    62774   statut 2 = Actif   archive 0   negociateur 23
> ```
>
> Il ne porte plus « Vendu ». La suppression de la dernière vente (23289) l'a ramené à
> Actif — ce qui **confirme au passage le découplage** : le statut avait suivi la
> transaction à la création, et il l'a suivie à la suppression. Le dossier porte un
> acquéreur utilisable sur ses trois affaires — **603800** — et le mandat **18836**.

```
```

---

# C.4-bis-0 — PREMIÈRE PASSE : lecture des handlers, un par un

*29/08 au soir. **Lu dans le code**, jamais par recherche de motif — cette méthode m'a trompé
quatre fois la veille. Chaque verdict ci-dessous cite la ligne qui le fonde.*

## 🔴 AUCUNE VÉRIFICATION — le geste est déclaré réussi quoi qu'il arrive

| handler | ce qu'il fait |
|---|---|
| **`change_hektor_annonce_status`** | relit l'état d'après *(l. 10428)*, **le met dans son journal** *(l. 10445-10450)*, et **ne le compare jamais**. Retourne `status: "changed"` inconditionnellement |
| **`assign_hektor_annonce_negotiator`** | même chose *(l. 10549, 10572-10576)* : lit, journalise, ne conclut pas |
| **`relance_signature`** | la réponse `res` n'est **jamais examinée** ; le journal passe à `done` quoi qu'il arrive, et un **403 est explicitement avalé** *(`if (!isHektorForbiddenError(error)) throw`)* |

> **`change_hektor_annonce_status` est le worker le plus utilisé du projet** — c'est lui qui porte
> tout le cycle de statut et les transactions qui en découlent. Il ne vérifie rien.

## 🟠 VÉRIFIE, MAIS LA VÉRIFICATION S'OUVRE QUAND LA RELECTURE RATE

```js
   const after = await fetchHektorPropertyByIdBestEffort(...);   // « best effort »
   if (after && after.archived === false) { throw ... }          // after nul -> on PASSE
```

| handler | ligne |
|---|---|
| `archive_hektor_annonce` | `if (after && after.archived === false)` |
| `restore_hektor_annonce` | `if (after && after.archived === true)` |
| `delete_hektor_annonce` | `if (after && after.archived === false)` — et son journal dit « envoyée et **vérifiée** » |
| `delete_hektor_contact` | `if (hektorDeleteSent && after.exists === true)` |

**Le défaut est le même partout** : une relecture qui échoue vaut acquittement. C'est *« conclure
du silence »*, exactement ce que C.4-bis-0 cherchait — mais déguisé en vérification, donc plus
difficile à voir qu'une absence de contrôle.

## ✅ VÉRIFIENT CORRECTEMENT — la relecture ratée est un échec

| handler / contrôle | ligne |
|---|---|
| impersonation négociateur | `if (!after \|\| after.userId !== String(target.idUser))` *(l. 2347, 2361)* |
| impersonation agence | `if (!after \|\| after.userId !== targetId \|\| after.role !== "AGENCE")` *(l. 3028, 3042)* |
| rattachement d'un prospect | `if (!hektorProspectLinkedInHtml(after.text, ...))` *(l. 12775, 12784, 12932)* |
| `update` / `add` / `delete_hektor_contact_search` | délèguent à un aide qui rend un **motif d'échec explicite**, et lèvent dessus |
| **les 3 gestes de transaction** | corrigés le 29/08 : réponse pour l'offre, relecture de `chargeannonce_Accueil` pour compromis et vente |

*La différence tient à un caractère : `if (!after || ...)` échoue proprement, `if (after && ...)`
laisse passer. Les deux se ressemblent à la lecture rapide.*

## Ce qui reste à lire — seconde passe

```
[ ] create_hektor_contact        [ ] update_hektor_contact
[ ] create_hektor_mandant_contact [ ] update_hektor_mandant_contact
[ ] create_hektor_mandat_auto_number
[ ] create_hektor_draft_annonce
[ ] upload_document_to_hektor    [ ] delete_document_from_hektor
[ ] upload_hektor_photo          [ ] sync_hektor_photos
[ ] cancel_signature_procedure   [ ] link_hektor_mandant (partiellement lu)
```

## Le correctif à prévoir

Trois familles, trois remèdes :

1. **les trois qui ne vérifient rien** → comparer l'état d'après à la cible, et lever sinon ;
2. **les quatre qui s'ouvrent** → transformer `if (after && …)` en `if (!after || …)` : *une
   relecture impossible n'est pas un succès* ;
3. **`relance_signature`** → cesser d'avaler le 403, et lire la réponse.

> **Et la règle générale, tirée du point 1** : la relecture doit interroger la **bonne source**.
> Le HTML de la fiche ne contient pas le bloc transaction — c'est `chargeannonce_Accueil` qui
> le porte. Un contrôle qui lit la mauvaise page ne vaut pas mieux qu'une absence de contrôle,
> et il coûte plus cher : il rassure.

---

# C.4-bis-0 — LES SIX CONTRÔLES FERMÉS, ET DEUX ÉPROUVÉS

*29/08 au soir. Frédéric a écarté `relance_signature` — « pas vraiment vérifiable » — donc six.*

## La contrainte qui a décidé de la forme du correctif

Elle était **écrite dans le code lui-même** *(`console_job_worker.js:2700`)* :

> *« l'annonce 62962 a bien été créée, et le job a quand même fini en error — après six
> tentatives et **seize pages inutiles** chez Hektor […] Une annonce créée mais déclarée en
> échec, c'est le pire des deux mondes. »*

Fermer les contrôles **sur la lecture GraphQL** aurait rejoué cet incident : elle ne cherche que
la famille `SALE`, pagine jusqu'à 8 pages, et nous avons **deux bannissements d'IP** à
l'historique. On a donc d'abord donné aux contrôles une **source exacte**.

## La source : `phase2/sync/annonce_etat_from_api.py`

Une seule requête par la porte 2, aucune famille, un 404 franc si l'annonce n'existe plus.

```
   id reel   ->  {"trouve": true, "archive": "0", "negociateur": "23", "agence": "12"}
   id bidon  ->  {"trouve": false}
```

## Les six

| handler | avant | maintenant |
|---|---|---|
| `archive_hektor_annonce` | passait si la relecture ratait | exige `archive="1"` — **✅ éprouvé, 38 s** |
| `restore_hektor_annonce` | idem | exige `archive="0"` — **✅ éprouvé, 45 s** |
| `delete_hektor_annonce` | testait un drapeau, journal « vérifiée » sans le savoir | **la suppression se prouve par l'absence** |
| `delete_hektor_contact` | `exists: null` valait acquittement | exige la preuve de l'absence |
| `change_hektor_annonce_status` | lisait, journalisait, **ne comparait jamais** | compare le statut à la cible |
| `assign_hektor_annonce_negotiator` | `confirmed_negotiator_id` valait **toujours `null`** | compare `keyData.NEGOCIATEUR` |

## La nuance sur le changement de statut

C'est le worker le plus utilisé. On ne **lève pas** quand la relecture est muette — ce serait
l'incident du 27/08. Trois issues, désormais distinguées **et écrites** :

```
   verifie: true    l'etat d'apres porte bien le statut vise
   verifie: false   la relecture n'a rien rendu -- on ne sait pas, et on le DIT
   echec            Hektor CONTREDIT la cible
```

*La différence avec avant : on ne prétend plus avoir vérifié.*

## Reste

```
[ ] eprouver les 4 autres            delete annonce, delete contact, statut, negociateur
[ ] seconde passe                    contacts, documents, photos, mandat auto, brouillon
[ ] pousser les commits + deployer   le front reste fige au 28/08
```

---

# ✅ C.4-bis — LE FILET DE REJEU DES ACTIONS *(30/08)*

*Le geste (c) de C.1', coché en août sur les seules éditions de champs, jamais posé sur les
actions. Mesure qui l'a rouvert : **7 travaux en erreur, `attempt_count` à 1 partout, aucun
jamais rejoué**.*

## Ce qu'il a fallu faire AVANT — et ce n'était pas prévu

Un filet qui rejoue exige des vérifications **absolues**. La mienne comparait la fiche avant et
après : rejouée sur un compromis déjà annulé, elle aurait déclaré en échec un geste **réussi**,
à chaque tentative, jusqu'à l'abandon. **Le filet aurait fabriqué de faux échecs en série.**

```
   /Api/Vente/CompromisById/  ->  status 1 = actif (9 206)   2 = annule (1 367)
   /Api/Vente/VenteById/      ->  200 existe   404 supprimee
```

*La répartition recoupe exactement `active`/`cancelled` du registre d'affaires — les deux
sources se confirment.* Éprouvé : annuler le compromis **50048 déjà annulé** rend `done` en 3 s.

## Le filet

| | |
|---|---|
| **rejoue** | 9 gestes idempotents à vérification absolue, attente 5/10/15/20 min |
| **exclut** | les **créations** et les **dépôts** — rejouer une création la **double** ; et les `update_hektor_*`, déjà couverts par l'autre filet |
| **abandonne** | à 5 tentatives — sans nouvel état : `attempt_count >= 5` suffit, le travail reste en `error`, visible |
| **ne ressuscite pas** | au-delà de **24 h** : un statut décidé avant-hier ne doit pas écraser un état plus récent |
| **montre** | `app_console_action_abandonnees`, avec le motif d'abandon |
| **tourne** | `app-action-retry-due`, toutes les minutes *(jobid 13)* |

## La limite de fraîcheur — trouvée en regardant avant de lancer

Le filet allait rejouer un `change_hektor_annonce_status` du **28/08** tombé sur un « Hektor
500 ». Deux jours après, l'intention n'est plus sûre. **Un filet rattrape un incident, il ne
ressuscite pas une décision oubliée.**

## Éprouvé pour de vrai

```
   retry:running   Rejeu automatique apres echec (tentative 2 sur 5)
   claim:running   repris par le worker
   ...error        « Le compromis 50047 n'existe plus du tout » -- dit, pas cache
   finish:done     resolu
```

**Premier rejeu automatique du projet** — sur un travail bloqué depuis la veille par le défaut
de relecture corrigé entre-temps.

## Le trio est complet

```
   detecter   les 6 controles fermes + les 3 gestes de transaction
   prouver    par une source absolue, la porte 2
   rattraper  le filet, toutes les minutes
```

---

# 🔄 ORDRE CORRIGÉ — arbitrage de Frédéric, 30/08

*« demain matin on reprend à C.4 […] déplace C.16 […] ajoute le rattrapage photo, documents,
et pense un run de rattrapage sur les recherches. »*

**Ce qui change** : C.16 quitte la 3ᵉ place et rejoint un **bloc rattrapages** créé pour
l'occasion. Les quatre tâches qui s'y trouvent ont la même nature — *aller rechercher ce qui
manque, en masse, une bonne fois* — et le même risque : elles tapent fort chez Hektor.

---

## 1. C.4 — LES 11 WORKERS · *on reprend là demain matin* · 1 à 2 sem.

```
[ ] archiver / desarchiver / supprimer une annonce
[ ] affecter le negociateur          [ ] lier un mandant
[ ] supprimer un contact             [ ] creer un contact
[ ] ajouter / supprimer une recherche
[ ] creer un mandant                 [ ] mettre a jour un mandant
[ ] LA BRANCHE « VENDU »             jamais executee depuis mai
```

*La lecture des handlers documents / photos / signature se replie ici.*

## 2. C.19-c — ✅ CLOS le 01/09 : le choix est RETIRE

```
[x] C.19-c   LE CHOIX « LAISSER ACTIF / ARCHIVER » DISPARAIT DE L'ECRAN

    LA MESURE QUI A TRANCHE, sur le parc de Frederic :
       8 767 ventes NON archivees   ·   423 archivees      95 % / 5 %

    Les deux cartes codees le 30/08 presentaient A EGALITE une option prise dans
    un cas sur vingt. Et l'option minoritaire enchainait un SECOND geste chez
    Hektor -- celui-la meme dont l'essai du 29/08 a montre qu'il pouvait
    DETRUIRE la vente precedente (23288, 404 a l'API ensuite).

    A LA PLACE : une phrase qui DIT ce qui va se passer, au lieu d'une question.
       « Le bien restera dans les biens actuels avec le statut Vendu. Pour le
         sortir du portefeuille, utilisez l'archivage depuis la fiche. »

    RETIRE DE L'ECRAN, PAS DU MECANISME : apresVente reste envoye a 'actif', et
    toute la chaine (RPC + enchainerArchivageApresVente, conditionne a une vente
    CONFIRMEE par les deux portes) demeure intacte.

    ⚠ CE QUE J'AVAIS RECOMMANDE LE MATIN MEME ETAIT L'INVERSE : mettre
    « archiver » en avant, « parce qu'un bien vendu qui reste actif encombre le
    portefeuille ». Une intuition, pas une mesure. Frederic m'a repris avant que
    je code, et ses donnees disent exactement le contraire.
```

## 2bis. LE STATUT D'UNE ANNONCE — l'etude du 01/09

> **notice/ETUDE_STATUT_ANNONCE_TRANSACTIONS_MANDAT_2026-09-01.md**
> Demandee par Frederic avant de decider : *« les interactions de statut manuel,
> suite transaction, suite mandat »*.

**LE FAIT CENTRAL, qui n'etait nomme nulle part :** dans l'app on ne cree pas une
transaction, on CHANGE LE STATUT et Hektor cree la transaction.
`HEKTOR_STATUS_CONFIG` le dit : `offer -> createOffre`,
`compromise -> createCompromis`, `sold -> createVente`.

```
   CREATION     le STATUT est la cause       ->  Hektor CREE la transaction
   ANNULATION   la TRANSACTION est la cause  ->  Hektor REDESCEND le statut
```

**Consequence pour la coupure, et elle est rassurante : le trou est PLUS PETIT
qu'on ne le croyait.** La creation survit -- c'est l'utilisateur qui pose le
statut, l'app le sait au clic. Seule la REDESCENTE disparait.

**L'EFFET DE BORD JAMAIS NOMME :** le statut pilote la DIFFUSION.
`Actif -> diffusable=1` (le bien repart sur les portails), `Clos -> diffusable=0`.

**LES TROIS ARBITRAGES DE FREDERIC (01/09) :**

```
[x] un bien dont le compromis echoue ne repart PAS en diffusion automatiquement
[x] « Clos » reste MANUEL -- aucune transaction ne le produit
[x] l'archivage reste INDEPENDANT du statut, et jamais deduit
```

**CE QUI RESTE A FAIRE :**

```
[x] LA REGLE DE REDESCENTE -- CODEE le 01/09
       reste-t-il une vente vivante ?  -> Vendu
       sinon un compromis actif ?      -> Sous compromis
       sinon une offre acceptee ?      -> Sous offre
       sinon                           -> Actif
    (une affaire a TROIS etapes : offre -> compromis -> vente. Definition de
     Frederic, 01/09. Regle extraite des donnees, pas supposee.)

    OU ELLE ECRIT, et pourquoi aux deux endroits :
       app_dossier_current.statut_annonce   pour que ce soit VISIBLE tout de suite
       app_annonce_champ_app ('statut')     pour que ca SURVIVE a la coupure

    ELLE NE TOUCHE JAMAIS diffusable.

    ⚠ LA MESURE A CORRIGE LA REGLE AVANT TOUT USAGE. Elle demandait une offre
    ACCEPTEE ; le passage a vide sur 13 380 biens a trouve UN contre-exemple
    (VT9514, offre 'proposed' et statut « Sous offre »). Hektor passe le bien
    « Sous offre » des que l'offre est POSEE : une offre proposee est VIVANTE,
    seule une offre refusee est morte.

    ETAT DE LA DOUBLURE : 716 accords / 720 biens de l'echelle. Les 4 ecarts sont
    tous des REMONTEES, bloquees par la borne 2 -- et ce sont de vraies
    incoherences DU COTE HEKTOR (VS046 : une vente, affichee « Sous offre »).
    La regle est plus juste que la donnee. Elle les montre, elle ne les corrige pas.

    LA DATE DE CLOTURE DES MANDATS n'y changerait rien d'utile : 87 sur 23 837
    (0,4 %), et aucune sur les 8 fiches en cause. La borne les protege deja, sans
    dependre d'une donnee absente. Voir l'etude, section 7ter.

[x] LA SENTINELLE D'ECART regle / Hektor -- POSEE le 01/09 (seuil 4) -- comparer a chaque resynchronisation
    ce que la regle a calcule et ce que Hektor renvoie. Le jour de la bascule, la
    regle sera deja eprouvee au lieu d'etre allumee a l'aveugle. Methode de la
    doublure, celle du registre des recherches et du numero de contact.

[ ] ⬛ POINT DE DEV OUVERT LE 01/09 -- LE TEST REEL DES STATUTS
    >>> notice/PROTOCOLE_TEST_STATUTS_TRANSACTIONS_2026-09-01.md

    DECIDE PAR FREDERIC : « il faut etre sur de l'interaction des statuts chez
    Hektor ». Tous les gestes faits DEPUIS L'APP, par lui en compte admin -- pas
    de comparaison avec des gestes faits dans Hektor : on sait deja, par le releve
    DOM du 28/08, que le worker envoie EXACTEMENT l'appel de leur ecran. Si Hektor
    ne reagit pas a un geste venu de l'app, ce n'est pas notre route.

    POURQUOI CE TEST EXISTE : mes deux dernieres reponses sur le comportement
    d'Hektor se sont revelees trop larges, et chacune reposait sur UN SEUL CAS.

    LE PRINCIPE : trois releves par geste. T0 avant, T1 juste apres (ce que
    l'app a pose), T2 apres la resynchronisation (ce qu'Hektor dit). L'ecart
    T1/T2 EST la reponse. Sans les trois temps on ne voit rien.

    ON RELEVE AUSSI L'ETAT DE CHAQUE TRANSACTION, pas seulement le statut du
    bien -- ajout de Frederic, et il est decisif : sa question « annuler un
    compromis met-il l'offre en refused ? » n'aurait eu aucune reponse sinon.
    (Deja mesure sur le parc : NON. 1 194 paires, 60 % restent 'accepted'.)

    BIEN NEUF, chez GONZALEZ / Firminy. PAS 62774 : 25 changements de statut a
    la main et six transactions empilees, on ne distinguerait pas le geste de
    l'accumulation. Il reste comme temoin.

    ⚠ DEUX GESTES SONT HORS D'ATTEINTE, et Frederic l'a confirme : deleteOffre
    et deleteCompromis n'ont JAMAIS eu de worker -- annuler seulement. Or c'est
    precisement SUPPRIMER un compromis qui, le 28/08, a fait redescendre le
    statut tout seul. Si le bloc descente ne redescend jamais, cette lacune
    devient le point de dev central.

    CE QUE LE TEST TRANCHE : la regle de redescente est-elle indispensable ou
    fait-elle double emploi ? faut-il renvoyer le statut A Hektor sans toucher
    la diffusion (« C+ », Frederic y est favorable) ? faut-il coder la
    suppression d'une offre et d'un compromis ?

[x] LE POUSSEUR PRENAIT LES ENVELOPPES VIDES -- CORRIGE le 01/09
    Trouve en testant, sur EM28412 / annonce 24933. Le bien passe « Actif » a
    12:25 ; a 12:27 un pending apparait ; a 12:38 puis 12:44 deux travaux partent
    et echouent sur « Aucun champ annonce modifiable fourni ». Toutes les six
    minutes, indefiniment.

    CE PENDING N'ETAIT PAS UNE SAISIE, C'ETAIT UN VERROU. hektor_bridge.py
    ::_arm_diffusion_lock pose EXPRES une ligne vide pour dire au read-through
    « ne reverte pas la diffusion pendant dix minutes ». Bon mecanisme, et il se
    leve tout seul (diffusion_lock_expired + clear_annonce_pending).

    L'ERREUR TENAIT DANS UN MOT, dans app_annonce_enqueue_due_pushes() :
       push_fields is not null    « ce qui n'est pas absent »
    au lieu de                    « ce qui a du contenu ».
    Or {} n'est PAS null : une enveloppe vide est presente, donc prise.

    POURQUOI JAMAIS VU AVANT : le verrou ne vit que dix minutes, le pousseur ne
    passe que sur les lignes dues -- il faut tomber pile dedans. Le passage a
    « Actif » a reuni les conditions, parce qu'il touche la diffusion.

    LE DANGER EVITE : a la 5e tentative le pending serait passe conflict = true,
    donc remonte dans app_en_attente_humain -- une alerte demandant de trancher
    UNE SAISIE QUI N'EXISTE PAS.

    ⚠ CE N'ETAIT NI LE READ-THROUGH NI LE DELAI DE 10 MIN. Frederic soupconnait
    ces deux-la et voulait les retirer ; ils font tous deux leur travail (le
    read-through est deja bride a 1 rafraichissement / 5 min par annonce). C'est
    le TROISIEME acteur qui se trompait. Les deux s'eteindront d'eux-memes a la
    coupure, quand il n'y aura plus d'Hektor a relire.

[x] L'ECRAN RECONNAIT UNE AFFAIRE NEE DANS L'APP -- CORRIGE le 01/09
    Question de Frederic, et elle a mis le doigt dessus : « les contrats
    d'autorite sont complets dans les transactions, pourquoi ce probleme ? on
    devrait avoir l'offre enregistree chez nous !! » -- Il avait raison.

    L'OFFRE ETAIT BIEN CHEZ NOUS. app_affaire_id 1 001 324, avec son montant,
    son acquereur, son mandat. Et loadAffairesForDossier ne filtre RIEN : elle
    etait meme deja chargee par l'ecran.

    CE QUI BLOQUAIT : affaireCourantePourStatut() la cherchait UNIQUEMENT par le
    numero d'HEKTOR -- deux fois. D'abord dossier.offre_id (vide tant que le run
    n'est pas passe), puis a.hektor_affaire_id (vide aussi). L'affaire etait
    sous les yeux du front, qui ne la reconnaissait pas parce qu'il la cherchait
    par la cle de l'autre. Un reste de l'ancien monde.

    ⚠ J'AVAIS DIT « c'est C.4 inachevee, il faut attendre le retour ». C'ETAIT
    FAUX. C.4 est a 16/16, les contrats d'autorite contact/mandat/affaire sont
    allumes, et rien de tout cela n'etait en cause.

    LE CORRECTIF : un REPLI, additif. Le chemin par le numero Hektor est
    inchange ; s'il ne trouve rien, on prend l'affaire nee chez nous -- a
    condition qu'elle soit UNIQUE et VIVANTE (ni refused ni cancelled). En cas
    d'ambiguite on ne rend rien : mieux vaut aucun bouton qu'un bouton qui agit
    sur la mauvaise affaire.

    CE QUE CA CHANGE POUR LE NEGOCIATEUR : il cree une offre, et il peut
    l'accepter ou la refuser DANS LA FOULEE. Avant, il devait attendre le run de
    nuit sans que rien ne le lui dise.

[ ] LE FRONT DE LA MODALE DE STATUT -- vu le 01/09 en testant
    La modale porte 15 champs et n'en repose que 4 (montant, date, date d'acte,
    sequestre). Deux qu'on a DEJA en base ne sont jamais reposes : l'ACQUEREUR
    (hektor_acquereur_id + acquereur_json) et le MANDAT (numero_mandat).

    ⚠ ET SURTOUT : la modale ne dit JAMAIS quelle transaction le geste va
    toucher. Le bien de test portait DEUX offres ; Frederic a clique « Refuser
    l'offre » sans voir laquelle. Pour « Supprimer la vente », irreversible,
    c'est plus grave. affaireCourantePourStatut() designe pourtant une affaire
    precise : il suffit de la NOMMER a l'ecran (n° Hektor, acquereur, montant,
    date) au-dessus des boutons de geste.
```

## 3. C.9 + 26bis-③ — **la création part de l'app** · 1 à 2 sem. — *le vrai basculement*

## 4. A.3-technique — le registre des mandats en propre · 3 à 5 j

---

## 5. 🔄 LES RATTRAPAGES — *bloc créé le 30/08*

> **Pourquoi ensemble.** Quatre courses de fond, même nature, même danger : elles interrogent
> Hektor en masse. **Le rattrapage des documents nous a déjà fait bannir l'IP** — débit trop
> soutenu, 403 répétés. Aucune ne se lance sans frein, et **jamais deux en même temps**.

```
[ ] C.16   LES CONTACTS DISPARUS          descendu de la 3e place
           825 fiches actives a marquer disparues -- jamais supprimer
           5 454 archivees a traiter
           poser le mecanisme « un contact a quitte le listing »

[ ] D.1a   MESURER AVANT DE COURIR        1 h -- combien de fichiers au cloud
           sans copie locale ? Le chiffre commande les deux suivants

[ ] D.1    RATTRAPAGE DOCUMENTS           40 493 a redimensionner
           ⚠ NE JAMAIS rejouer les annonces deja en echec
           ⚠ verifier depuis une AUTRE IP avant de conclure a une panne Hektor

[ ] D.2    RATTRAPAGE PHOTOS              1 397

[ ] R.rech RATTRAPAGE DES RECHERCHES      ← demande de Frederic, 30/08
           Une PREMIERE recherche n'entre dans aucun run : ni le listing ni le
           delta de date_maj ne la voient. ~270 invisibles mesurees sur 249 fiches.
           L'outil existe : run_rattrapage_acquereurs.ps1
              71 337 fiches, 4 h 35, pause de 20 s OBLIGATOIRE
           C'est le 19-R1 (tache 0.3), a finir. Et le 19-R2 la veille de la
           bascule reste la DERNIERE OCCASION de rattraper.
```

---

## 6. FIN DE PLAN

```
[ ] C.11    menage des tables mortes
[ ] C.13-c  rattraper 23 715 dates de cloture
[ ] B.3     le declencheur de descente
[ ] E.2     bascule des negociateurs sur l'app
[ ] E.3     les workers deviennent invisibles
[ ] E.4     le jour J
[ ] F.1     utilisateurs, roles et droits -- APRES la coupure
```

## 7. CE QUI NE DÉPEND PAS DU CODE — et commande la date

```
[ ] A.1  PORTAILS     sortie en nom propre + reprise des ~350 annonces en ligne
[ ] A.2  SIGNATURE    contrat Yousign en propre
[ ] A.3  REGISTRE     obligation legale, aujourd'hui adossee a Hektor
```

---

## ✅ COCHÉ LE 30/08

```
[x] pousser les commits          2c5a074..9f79b4a, 55 commits partis
[x] deployer le front            Vercel a redeploye -- confirme par Frederic
                                 les 4 boutons de transaction sont en ligne
[x] C.4-bis  le filet de rejeu   pose, eprouve, programme a la minute
[x] C.4-bis-0  les 6 controles   fermes ; 5 eprouves en conditions reelles
[x] C.19 point 1                 les 2 handlers eprouves par la chaine
```

---

# C.4 — LA FAMILLE ANNONCE, TERMINÉE *(30/08)*

## Ce qui a été converti

```
[x] archiver              RPC app_archive_annonce_optimistic    eprouve, done en 35 s
[x] desarchiver           RPC app_restore_annonce_optimistic    eprouve
[x] affecter le negociateur  RPC app_assign_negotiator_optimistic
```

Chacune écrit **le carnet et le travail dans la même transaction**. Avant, le front insérait le
travail et attendait : si Hektor refusait, l'intention n'existait nulle part.

## Deux qui ne se convertissent PAS — et c'est mesuré, pas supposé

### `delete_hektor_annonce` — déjà saine

```
   passe deja par une RPC                       verifie
   sa RPC echoue FERMEE                         verifie : 0 travail cree sans session
   le worker refuse de supprimer a l'aveugle    corrige le 30/08
   le filet rend l'intention durable            pose le 30/08
   ecrire au carnet                             SANS OBJET
```

Une suppression n'est pas un champ corrigé, c'est une disparition : il n'y a **rien à
comparer**. L'audit la comptait comme « à convertir » sur le critère *« écrit-elle chez
nous »*, qui ne s'applique pas ici.

### `link_hektor_mandant` — ni domicile, ni trou à boucher

```
   un mandant est une RELATION, pas un champ  ->  le carnet (dossier, champ, valeur)
                                                  ne sait pas porter une liste
   aucune table de mandants cote app          ->  ils vivent dans un bloc JSON
   trou de droits ?                           ->  NON, verifie
```

**La convertir ajouterait du risque sans rien apporter.** Elle reste telle quelle.

## 🔴 LA DÉCOUVERTE QUI JUSTIFIE CES DEUX DÉCISIONS

La table `app_console_job` porte **elle-même** son contrôle de droits, en politique RLS :

```sql
   INSERT autorise si  requested_by = auth.uid()
                   ET  status = 'pending'
                   ET  app_console_can_request_job(job_type, app_dossier_id, hektor_annonce_id)
```

Deux conséquences, et elles renversent ce que je croyais :

**①** Toute insertion directe depuis le front **était déjà contrôlée**. Il n'y a jamais eu de
trou de droits sur ce chemin.

**②** Une politique RLS traite `NULL` comme un **refus** — contrairement au `if not (...)` du
PL/pgSQL, où `not NULL` ne déclenche rien. Le trou trouvé ce matin ne concernait donc **que le
chemin RPC**, parce qu'une fonction `SECURITY DEFINER` **contourne la RLS** et doit refaire le
contrôle elle-même.

> **Autrement dit : en convertissant un geste en RPC, on sort du garde-fou de la table et on
> reprend la responsabilité du contrôle.** C'est précisément ce qui m'a mordu sur l'archivage.
> Toute conversion future doit refaire ce contrôle — et le faire échouer fermé.

## Le compte de C.4

```
   convertis          3   archiver, desarchiver, affecter le negociateur
   sans objet         2   supprimer une annonce, lier un mandant  (mesure)
   restants           6   les 4 contacts, les 2 recherches
   + la branche « Vendu », jamais executee
```

---

# 🔴 LE CONSTAT DU 30/08 — POURQUOI « VENDU » N'A JAMAIS PU MARCHER

*Deux passages réels sur 62774. L'arbitre a mordu au premier essai, et le second a donné
la cause. Ce n'était ni un droit, ni un champ manquant, ni un compromis absent.*

## Ce que les deux passages ont montré

```
   statut Hektor          2 -> 5  « Vendu »        ACCEPTE
   journal                « Transaction Vendu envoyee »
   ventes sur la fiche    avant []   apres []      AUCUNE
   /Api/Vente/ListVentes/ du 29 au 31/08           0
```

Les **deux portes** concordent : Hektor accepte le changement de statut et **ne crée aucune
vente**. Sans l'arbitre, ce travail rendait « vérifié, statut 5 » — et l'app aurait affiché un
bien vendu qui ne l'est pas. **C'est exactement l'état dans lequel 62774 se trouvait déjà, sans
qu'on ait jamais su pourquoi.**

## La cause, sur pièce

La réponse à l'**enregistrement** est le **formulaire lui-même** *(`{"success":true,
"data":{"defaultTemplate": …}}` — du CSS de popin)*. Hektor **ré-ouvre la popin au lieu
d'enregistrer**. Et l'ouverture nous tend des cases vides : `forme_mandat: (vide)`,
`forme_negociateur: (vide)`.

Le formulaire a été déposé et lu. **Il ne contient aucun champ** :

| popin | taille | champs `name=` | ce que c'est |
|---|---|---|---|
| **offre** *(28/08)* | 208 541 car | **22** | un vrai formulaire, plat |
| **compromis** *(28/08)* | 85 921 car | **0** | `compromisStepHost` · `compromisStepper` · `mustacheLoader` |
| **vente** *(30/08)* | 85 822 car | **0** | `venteStepHost` · `venteStepper` · `mustacheLoader` |

➡ **L'offre est un formulaire ; le compromis et la vente sont des ASSISTANTS PAR ÉTAPES.** Leurs
champs n'existent pas dans la page reçue : ils arrivent ensuite, par gabarits Mustache montés en
JavaScript. Le CSS déposé porte d'ailleurs `/* VENTE STEP 3 */` et `.recapVente`.

`submitHektorTransactionStatus` a été écrit **pour l'offre** — un POST plat avec
`actionContainer[] = save, treat`. Appliqué à un assistant, il ne déclenche rien : Hektor rend
la popin, et c'est tout.

## Ce que ça explique d'un coup

- **`compromis` : 0 travail. `sold` : 0 travail.** Ce n'était pas un oubli de dev — **ces deux
  branches n'auraient pas pu marcher**. Elles étaient du code mort qui n'avait jamais tourné.
- L'observation du 29/08 — *« cliquer Sous compromis a changé le statut sans créer de
  compromis »* — n'était pas une bizarrerie : **c'est ce comportement-là**, vu de l'écran.
- Et le compromis 50044, créé « par le même clic » sur un bien qui n'en avait aucun, l'a été par
  **l'assistant piloté à la main dans le navigateur**, pas par la chaîne.

## Ce qui MARCHE, et qui n'est pas rien

```
   changement de statut chez Hektor      OK, verifie (2 -> 5, puis 5 -> 2)
   cloture du mandat CHEZ NOUS           OK, 1 ligne ecrite, registre rafraichi
   l'arbitre                             OK -- il a attrape le defaut du 1er coup
   la garde anti-doublement              posee, non sollicitee (rien n'a ete cree)
   le retour a « Actif »                 OK, verifie deux fois
```

## ⚠ ET UN EFFET DE BORD MESURÉ, QUI N'ÉTAIT ÉCRIT NULLE PART

Passer une annonce à « Vendu » la fait **SORTIR de `app_dossier_current`** — elle part dans
`app_historical_annonce_index_current`. C'est le **même filtrage par statut** que celui trouvé le
28/08 sur le registre des mandats, et il touche ici la table principale de l'app.

Conséquence pratique : **le dossier disparaît au moment précis où le geste réussit**. Tout code
qui relit `app_dossier_current` après une vente ne trouve rien — mon propre script d'essai s'y
est cassé les dents avant d'être corrigé.

---

## LA DÉCISION QUI REVIENT À FRÉDÉRIC

| | |
|---|---|
| **A — piloter l'assistant** | Relever la séquence d'étapes au navigateur, enregistreur armé, puis la coder. C'est faisable, mais c'est **un vrai chantier** — et le projet a déjà buté sur le même mur : *« modifier un compromis chez Hektor passe par un module ES impilotable »* |
| **B — ne pas créer la vente chez Hektor** | L'app enregistre la vente **chez nous** *(la ligne d'affaire existe déjà)*, pose le statut chez Hektor *(ça marche)*, clôt le mandat chez nous *(ça marche)*. Hektor apprend **le statut**, pas la transaction |

**B est déjà la direction du projet**, arbitrée le 28/08 : *« tous les champs de la modale changer
statut doivent pouvoir se modifier dans l'app puis le serveur SANS envoyer à Hektor — sauf
refuser/accepter pour l'offre, annuler pour le compromis, supprimer pour la vente »*. **Créer une
vente n'a jamais figuré dans la liste des gestes qui partent.**

⚠ **Ce que B coûte, et il faut le dire** : une vente née dans l'app n'existe pas chez Hektor,
donc le run de nuit ne la trouvera jamais et la sentinelle `app_affaires_sans_numero_hektor`
*(seuil 0)* lèvera la main **tous les jours**. Choisir B oblige à lui apprendre la différence
entre « affaire perdue » et « affaire qui n'appartient qu'à nous ».

---

# 🔴 UN TROU TROUVÉ LE 30/08 — le filet de rejeu pouvait DOUBLER une création

*Trouvé en préparant « Vendu », et il existait depuis le matin même. Personne ne l'avait vu
parce que la branche concernée n'avait jamais tourné.*

`change_hektor_annonce_status` figure dans la liste des travaux que le filet de rejeu reprend
*(c4bis, 30/08)*. Le commentaire de ce filet **prévient lui-même** :

> « toute addition à cette liste doit s'accompagner d'une vérification absolue : sans elle, le
> rejeu transforme un succès en échec, **ou double une création** »

Les gestes **destructeurs** de la liste relisent tous l'état avant d'agir — « on ne supprime pas
ce qu'on ne voit pas ». Les branches **créatrices** de ce worker *(offre, compromis, vente)*, elles,
ne le faisaient pas.

**Le correctif** *(`4aa1f43`)* : si la ligne d'affaire du travail porte déjà un numéro Hektor, la
transaction a été créée par une tentative précédente — **on ne recrée pas**. La vérification est
**absolue** *(elle ne dépend d'aucun ordre, d'aucun compte, d'aucune date)*, ce que le rejeu exige.

Et **on n'échoue pas** quand la vente n'est pas prouvée : lever ferait passer le travail en
`error`, donc le filet le reprendrait — et un rejeu qui recrée est exactement ce qu'il ne faut
pas sur une vente. C'est la sentinelle `app_affaires_sans_numero_hektor` *(seuil 0)* qui porte
l'alerte dès le lendemain.

---

# 🔄 LISTE REFONDUE — 30/08 au soir

*Refaite après une journée qui a beaucoup appris. Ce qui change par rapport à la version du
matin : **quatre tâches de C.4 sortent de C.4** — elles ne dépendent pas de lui mais de la
bascule de clé — et **une recommandation oubliée** revient en tête.*

---

## MAINTENANT

```
[x] C.2b-reste   LE REGISTRE DES RECHERCHES                    FAIT 30/08
                 app_search_registry :
                    + app_contact_id                     pose
                    hektor_contact_id -> nullable        pose
                    les DEUX index d'unicite -> PARTIELS
                 Un couple ne protege rien quand sa colonne est vide : l'index
                 Hektor ne contraint plus que les lignes qui portent un numero
                 Hektor, et son jumeau app fait pareil de son cote.

                 MESURE : 76 924 lignes avant, 76 924 apres, 0 sans numero de
                 contact. Table d'avant conservee (app_search_registry_avant_c2b).

                 TROIS PIECES, pas une : la base migree (script), le DDL des
                 bases neuves (build_contacts_layer), et la PROPAGATION chaque
                 nuit (registre_contacts) -- sans la troisieme, toute recherche
                 nouvelle serait nee sans numero de contact.

                 Pourquoi la propagation est dans registre_contacts et pas dans
                 build_contacts_layer, qui pourtant ecrit le registre : build
                 tourne AVANT (ligne 370 contre 380). Un contact tout neuf n'a
                 pas encore son numero quand sa recherche recoit le sien.

                 EPROUVE : case videe sur la recherche 76924 (contact Hektor
                 605088, numero app 355770 -- les trois nombres differents pour
                 qu'une coincidence ne puisse pas passer pour une preuve), run
                 rejoue, case remise. Premier essai fait sur la ligne 1 : les
                 trois valaient 1, la preuve ne valait rien, refaite.

[x] C.4-Vendu    LA BRANCHE JAMAIS EXECUTEE          EPROUVEE le 31/08
                 ET AVEC ELLE LE COMPROMIS, qui n'avait jamais tourne non plus.

                 EPROUVE DE BOUT EN BOUT, chaine complete :
                    compromis 50052   cree, confirme par les DEUX portes
                    vente     23292   cree, confirme par les DEUX portes
                    numero Hektor ecrit dans l'app IMMEDIATEMENT
                    (app_affaire 1000326 et 1000327)

                 TROIS CAUSES, toutes MESUREES, aucune devinee :

                 1. LE PROTOCOLE. Ce n'est pas un formulaire, c'est un
                    ASSISTANT a etapes. Le verbe n'est pas createVente mais
                    getStepVente / getStepCompromis, et un « basket »
                    (etat serialise PHP) se transporte d'appel en appel.
                    actionContainer[]=save,treat va DANS L'URL.
                    Releve sur le reseau -> PROTOCOLE_ASSISTANT_VENTE_HEKTOR

                 2. LE COMPTE. Hektor l'a dit en clair, en 114 caracteres :
                    « Vous n'avez pas les droits pour creer un compromis lie
                      a cette annonce. »
                    Les trois genres veulent TROIS COMPTES DIFFERENTS :
                       offre       l'admin est REFUSE  -> negociateur
                       vente       le negociateur convient
                       compromis   le negociateur REFUSE -> admin

                 3. LA SOURCE DE L'ARBITRE. La fiche ne montre QU'UN
                    compromis a la fois, et pas toujours le dernier. Elle a
                    fait declarer « rien cree » sur DEUX gestes reussis
                    (50050 et 50051). L'arbitre juge desormais sur l'API,
                    la fiche n'est plus qu'un secours.

                 ⚠ CE QUI A COUTE LE PLUS CHER : la reponse de Hektor etait
                 JETEE des lors qu'elle ne portait pas le mot « error ».
                 Trois allers-retours perdus pour cela. Elle est desormais
                 conservee partout sur ce chemin -- c'est probablement la
                 correction la plus utile de la nuit, plus que le protocole.

                 LA CONDITION DE BLOCAGE, ETABLIE PAR EXPERIENCE le 31/08
                 (Frederic l'avait enoncee, je l'avais contredit A TORT) :

                    C1  aucun compromis actif   ->  CREE 50053   reference
                    C2  50053 ACTIF present     ->  RIEN CREE    le test
                        annulation de 50053                      done
                    C3  juste apres             ->  CREE 50054   contre-epreuve
                    V1  aucune vente            ->  CREE 23293   reference
                    V2  23293 presente          ->  RIEN CREE    le test

                    compromis  un ACTIF bloque    -> l'ANNULER (reversible)
                    vente      TOUTE vente bloque -> la SUPPRIMER (DEFINITIF)

                 Le geste qui debloque une VENTE est irreversible : il ne peut
                 pas etre automatise sans decision humaine.

                 POURQUOI JE M'ETAIS TROMPE : j'avais objecte qu'un compromis
                 actif ne peut pas bloquer, puisque 9 075 annonces Vendues en
                 portent un. La mesure etait juste, LE RAISONNEMENT ETAIT FAUX
                 -- ces dossiers sont TERMINES, personne n'y cree un nouveau
                 compromis. Une mesure exacte ne protege pas d'une conclusion
                 fausse : il fallait l'experience, pas le raisonnement.

                 PRECISION DE FREDERIC, VERIFIEE (et j'avais classe cela en
                 « faiblesse » a tort) : ListCompromis rend les compromis EN
                 COURS -- ceux dont l'annonce n'a pas encore de vente. Mesure
                 sur les 97 : ZERO n'a de vente sur son annonce. C'est ce qui
                 explique la disparition de 50054, sortie de la liste des que
                 la vente 23293 a ete creee.
                 « Actif » et « en cours » sont deux choses differentes :
                 9 206 actifs au miroir, dont 1 689 seulement sur une annonce
                 sans vente. Pour l'arbitre c'est LA bonne liste.

                 BAC A SABLE SOLDE : 12 lignes d'affaire d'essai retirees,
                 la date de cloture du mandat 18836 retiree, vente et
                 compromis d'essai supprimes chez Hektor, 62774 remise en
                 « Actif » (verifie). Reste 50048, anterieur a la nuit.
                 Sentinelle app_affaires_sans_numero_hektor : 0.
```

---

## ENSUITE — LE VERROU QUI COMMANDE TOUT LE RESTE

```
[ ] TACHE 5      BASCULER LA CLE DES CONTACTS                      3 a 5 j
                 La doublure est POSEE et REMPLIE (19 tables).
                 ⚠ CHIFFRE CORRIGE LE 30/08 -- il etait sous-estime 6 fois :
                    355 770  numeros dans la doublure locale (app_contact)
                     58 732  contacts que l'app embarque (les « eligibles »)
                 Les 58 731 ecrits ici mesuraient la portee APP, pas la
                 doublure. Verifie : 58 732 est exactement le compte local de
                 supabase_sync_eligible = 1, et exactement celui de Supabase.
                 Ce n'est donc PAS un trou de synchro -- c'est un filtre voulu.
                 Mais la bascule de cle porte sur les 355 770, pas sur 58 731.
                 Reste a designer laquelle des deux cases fait foi.
                    4 tables portent 95 % des lignes, 6 sont vides
                    701 points de code -- 40 % de l'echelle des annonces
                    3 fonctions basculent, 8 gardent le numero Hektor
                 ⚠ NE PAS y attacher le changement de cle primaire de
                   app_contact_current : c'est un SECOND chantier.

[ ] 4-suite      BASCULER LA CLE DES RECHERCHES
                 La doublure tourne depuis le 21/08 et s'observe.

[ ] 26bis-CONTACTS  LE CORPS DU CONTACT             AJOUTEE LE 31/08
                 ⚠ CETTE TACHE N'EXISTAIT PAS. Le plan la croyait sans objet.

                 CE QUE LE PLAN AFFIRMAIT :
                    « Le contact possede tout. L'annonce possede son
                      identite, pas son corps. »
                 C'EST FAUX POUR LA MOITIE, et la lecture du code le dit :

                    ANNONCES  app_view_generale     DROP + CREATE AS
                    CONTACTS  app_contact_current   DELETE + INSERT
                                                    (replace_table_rows)

                 load_contacts() lit « FROM hektor_contact » -- LE MIROIR.
                 Le corps du contact est donc refait chaque nuit depuis
                 Hektor, EXACTEMENT comme celui de l'annonce.

                 L'inventaire du 25/08 avait lu la DECLARATION des tables
                 (CREATE IF NOT EXISTS) et non le CHEMIN DES DONNEES.

                 CE QUI SURVIT A LA COUPURE, et c'est rassurant : le miroir
                 GELE, il ne disparait pas. La reconstruction reproduit le
                 meme contenu. Les 355 770 contacts gardent leur corps,
                 comme les 61 099 annonces.

                 CE QUI NE SURVIT PAS : un contact NE DANS L'APP n'a aucune
                 ligne dans le miroir -> son corps est efface a la premiere
                 reconstruction. Son identite survit dans app_contact, mais
                 elle ne pointe plus sur rien.

                 Mesure : app_contact    355 770, dont 0 sans numero Hektor
                          app_dossier     61 099, dont 0 sans numero Hektor
                 Le patron existe pour les deux. Il n'a JAMAIS servi.

                 MEME NATURE QUE 26bis, MEME URGENCE : le remplissage ne
                 peut se faire que PENDANT QUE HEKTOR VIT ENCORE.
                 Aujourd'hui un contact cree dans l'app finit dans le miroir
                 parce que Hektor le confirme ; le jour ou il ne repond
                 plus, ce filet disparait.

                 A FAIRE AVANT C.9, comme 26bis.

[ ] 26bis-RELATIONS  LE LIEN ENTRE UNE PERSONNE ET UN BIEN   AJOUTEE LE 31/08
                 ⚠ TROUVEE PAR UNE QUESTION DE FREDERIC, pas par l'audit :
                 « est-ce que cela va tenir apres la coupure ? »

                 LA RUBRIQUE « MANDANTS » N'A PAS DEUX SOURCES, ELLE EN A UNE.
                 Verifie dans build_contacts_layer.py :

                    la liste affichee     <- proprietaires_json
                    app_contact_relation_current <- proprietaires_json
                                                    <- hektor_annonce_detail
                                                       (LE MIROIR)

                 La table des relations n'est pas une source independante : elle
                 est FABRIQUEE a partir du detail Hektor, chaque nuit.

                 CE QUI SE PASSERA A LA COUPURE : le miroir GELE. La liste des
                 mandants d'un bien reste figee au jour J. Un mandant rattache
                 apres n'y entrera JAMAIS, et la ligne provisoire posee le 31/08
                 resterait « En creation… » A VIE, puisque rien ne viendra la
                 confirmer.

                 CONSEQUENCE SUR LE CHOIX D'AFFICHAGE DU 31/08 : mettre le
                 mandant en attente A COTE de la liste plutot que DEDANS est
                 NEUTRE vis-a-vis de la coupure. Les deux affichages remontent au
                 meme miroir. Le probleme n'est pas ou l'on affiche.

                 MEME NATURE QUE 26bis ET 26bis-CONTACTS, TROISIEME DU NOM :
                    26bis            le corps de l'ANNONCE
                    26bis-contacts   le corps du CONTACT
                    26bis-relations  le LIEN entre les deux      <- celle-ci

                 A FAIRE AVANT C.9, comme les deux autres.

                 ── PERIMETRE REEL, mesure le 31/08 apres deux questions de
                    Frederic. IL EST DEUX FOIS PLUS PETIT QUE JE NE L'AI ECRIT.

                 ① « pourquoi pas une table relation comme pour les annonces ? »
                 Verifie : les QUATRE doublures existent, la cinquieme manque.

                    app_dossier            61 099   les annonces
                    app_contact           355 770   les contacts
                    app_search_registry    76 928   les recherches
                    app_affaire_ledger     29 296   les affaires
                    ------------------------------------------------
                         (rien)                 -   les LIENS

                 Ce n'est pas une decision, c'est un OUBLI : chaque doublure est
                 nee d'un chantier precis (le numero de l'annonce, la tache 5, la
                 cle instable des recherches, le ledger). La relation n'a jamais
                 eu son chantier -- elle est passee entre les mailles, exactement
                 comme cette tache n'etait pas au plan il y a une heure.

                 ET C'EST PLUS SIMPLE QUE POUR LES RECHERCHES :
                    relation_key = hash(contact, annonce, role, source, transaction)
                 La cle NE DEPEND PAS DU CONTENU. Contrairement a celle des
                 recherches -- qui changeait a chaque modification et a demande
                 des semaines pour etre figee -- celle-ci est DEJA STABLE.
                 Modifier un mandant ne change pas la cle de son lien.
                 Mesure : 165 286 lignes uniques sur (contact, annonce, role)
                 sur 165 836 -- 513 doublons a regarder, marginaux.

                 ② « et les relations acheteurs sur les transactions ? »
                 DEJA COUVERTES, et par toi, en aout. app_affaire_ledger porte
                 hektor_acquereur_id ET acquereur_json :

                    offre       11 116  }  28 910 / 29 296 avec l'acquereur
                    compromis   10 574  }  identifie -- 98,7 %
                    vente        7 606  }

                 C'est le BON endroit : l'acquereur est lie au bien PAR une
                 transaction, donc il vit la ou vit la transaction. Le mandant,
                 lui, est lie au bien DIRECTEMENT, sans transaction -- il n'a
                 donc jamais eu de vehicule.

                 ── DONC LE CHANTIER PORTE SUR DEUX ROLES, PAS CINQ :

                    mandant        74 037   ❌ aucune doublure
                    proprietaire   58 365   ❌ aucune doublure
                    ------------------------
                                  132 402   liens sans domicile

                    acquereur ×3   33 434   ✅ app_affaire_ledger

                 ── ET LA TACHE EST DOUBLE, ce que je n'avais pas vu :
                    L'IDENTITE   la doublure qui manque -- une table jamais
                                 reconstruite, qui garde le lien meme quand le
                                 miroir gele. C'EST LE PREALABLE.
                    LE CORPS     ce que 26bis et 26bis-contacts traitent pour
                                 l'annonce et le contact.
                 Sans l'identite, il n'y a rien a quoi accrocher le corps.

[ ] INVENTAIRE   TOUT VERIFIER AVANT LA COUPURE      demande de Frederic, 31/08
                 « il faudra tout verifier a ce moment »

                 POURQUOI CETTE TACHE EXISTE : on decouvre ces trous UN PAR UN,
                 et toujours par accident.
                    21/08  le corps de l'annonce      (26bis)
                    31/08  le corps du contact        (26bis-contacts)
                    31/08  le lien mandant            (26bis-relations)
                 Trois fois le meme mecanisme, trouve trois fois separement. Il
                 faut le chercher UNE fois, exhaustivement.

                 PREMIERE MESURE, faite le 31/08 -- CE QUI EST REFAIT CHAQUE NUIT
                 et gelera donc a la coupure :

                    REMPLACEES en local (delete + insert)
                       app_contact_current
                       app_contact_relation_current
                       app_contact_search_current
                       app_contact_duplicate_group_current
                       app_contact_duplicate_member_current

                    RECONSTRUITES (drop + create as)
                       app_view_generale
                       app_view_demandes_mandat_diffusion

                    VIDEES au push Supabase
                       app_dossier_current
                       app_dossier_detail_current      <- porte proprietaires_json
                       app_mandat_register_current
                       app_mandat_broadcast_current
                       app_archive_annonce_index_current
                       app_historical_annonce_index_current
                       app_brouillon_annonce_index_current
                       app_work_item_current
                       app_filter_catalog_current_store

                 => 16 tables au moins. Chacune doit recevoir la meme question :
                    « qu'arrive-t-il a un objet ne dans l'app quand cette table
                      est refaite, et Hektor ne repond plus ? »

                 CE QUI SURVIT, et qu'il ne faut pas confondre avec le reste :
                 les tables de DOUBLURE, jamais reconstruites --
                    app_dossier · app_contact · app_search_registry
                    app_affaire_ledger · app_*_champ_app
                    app_*_provisional (les quatre posees en aout)
                 Elles gardent l'IDENTITE. C'est le CORPS qui manque.
```

**Ce verrou leve, quatre tâches de C.4 se debloquent d'un coup :**

```
[x] ajouter une recherche   FAIT 31/08   [x] creer un contact   FAIT 31/08
[ ] creer un mandant                     [ ] mettre a jour un mandant
```

*Elles etaient comptees dans C.4 ce matin. C'etait une erreur de ma part : elles n'attendent
pas du code de worker, elles attendent une identite.*

**CORRECTION DU 31/08 :** elles n'attendaient pas 26bis-contacts non plus. L'essai le
prouve -- le contact 605095 et la recherche du contact 605030 sont bien redescendus dans
le miroir, parce que Hektor les a confirmes. **26bis / 26bis-contacts ne DEBLOQUENT pas ces
taches : ils les feront SURVIVRE a la coupure.** Ce n'est pas le meme calendrier.

```
[x] C.9-recherche  AJOUTER UNE RECHERCHE ECRIT CHEZ NOUS D'ABORD   FAIT 31/08
                   Table app_search_provisional + RPC app_create_search_optimistic
                   (ligne provisoire ET travail dans une seule transaction, la RPC
                   APPELLE les garde-fous existants au lieu de les recopier).
                   Le worker relie, marque l'erreur, enchaine la resynchro.
                   La ligne s'efface quand cette resynchro est TERMINEE -- un fait,
                   pas un compte de recherches qu'une suppression ferait mentir.

                   EPROUVE A L'ECRAN, cycle complet (contact 605030, Firminy) :
                     ligne provisoire posee -> badge « En creation… »
                     worker -> status linked, resynchro enchainee
                     resynchro done -> la ligne s'efface, la vraie recherche
                     s'affiche « Active », rapprochement calcule (7 biens)
                   Et l'etat d'echec : badge « Erreur de creation », rouge.

                   CE QUE L'ESSAI A CORRIGE EN COURS DE ROUTE :
                   le try/catch ne couvrait que l'appel de creation. Le premier
                   essai a echoue AVANT, sur la bascule de contexte negociateur --
                   la ligne est restee « En creation… » pour toujours, soit
                   exactement le defaut qu'elle devait supprimer. Enveloppe posee
                   sur la recherche ET sur le contact (meme trou), avec le garde
                   « status <> linked » pour ne jamais dementir une reussite.
```

**LA CONSOLE HEKTOR EST FILTREE PAR L'AGENCE DU COMPTE — etabli le 31/08**

```
[x] LE FAIT, lu sous DEUX comptes sur la MEME page          ETABLI 31/08
    annonce 62964, mandant 603953
       lu en ADMIN (idUser 4)      ->  visible, « Bien ajoute le 28-08-2026 »
       lu en GONZALEZ (idUser 48)  ->  ABSENT

    Le worker agit sous le negociateur du BIEN (preferDossierOwner: true),
    jamais du CONTACT. Un mandant d'une autre agence lui est invisible, et il
    conclut « pas lie ».

    PAS REPARABLE EN CHANGEANT DE COMPTE : le geste touche deux objets qui
    peuvent appartenir a deux agences. Quel que soit le compte, l'un des deux
    sort du perimetre.

[x] LA PARADE : CHANGER DE SOURCE                            FAIT 31/08
    L'API s'authentifie par JETON, pas par session de negociateur -- elle n'est
    pas filtree. Pont phase2/sync/annonce_proprietaires_from_api.py, sur le
    modele d'annonce_etat_from_api.py (29/08).
    Les DIX lectures du lien mandant y sont adossees, la console en repli.
    L'arbitre rend TROIS issues : lie / non_lie / inconnu -- « inconnu » retombe
    sur le scrape, jamais sur un succes suppose.

    EPROUVE EN CONDITIONS REELLES le 31/08 au soir :
       modifier un mandant   ->  done, « Firminy » arrive chez Hektor,
                                 pending efface, un seul envoi
       rattacher un mandant  ->  « already_linked » par l'API, RIEN de reecrit
                                 (avant : echec, puis rattachement rejoue)

[ ] CE QUI RESTE                                             a faire un jour
    . waitForHektorMandantLink interroge la console 4 fois AVANT l'API. Pour un
      contact hors agence ces 4 appels sont perdus d'avance -- perte de debit,
      pas de justesse. A inverser si le debit devient un sujet.
    . les autres garde-fous par scrape (documents, photos, transactions) n'ont
      pas ete traites : la mesure ne le justifiait pas. A reprendre si un echec
      inexplique apparait la-bas.
```

> ### ⚠ CE QUE J'AI RACONTE DE TRAVERS, ET QUE LA CHRONOLOGIE CORRIGE
>
> Frederic : *« le worker generer le n° de mandat a FONCTIONNE, c'est le compte
> formation qui pose probleme, pas le worker »*. **Il avait raison sur le worker
> -- et j'avais tort sur la cause, deux fois de suite.**
>
> **CE QUI S'EST REELLEMENT PASSE sur l'annonce 62964, lu dans l'ordre des
> travaux :**
>
> ```
>    27/08 23:02   creation de l'annonce                    ->  OK
>    28/08 05:47   « generer le n° de mandat »              ->  ERREUR
>    28/08 05:48   « rattacher le mandant 603953 »          ->  ERREUR
> ```
>
> **L'ordre est inverse.** On a demande le numero AVANT de rattacher le mandant.
> A 05:47 l'annonce n'en avait aucun, et le worker a repondu « le contact 603953
> n'est pas confirme comme mandant » -- **la stricte verite**. Ce n'est pas un
> defaut, c'est un garde-fou qui fait son travail : on ne genere pas un mandat
> sans mandant.
>
> **La preuve par comparaison, le meme matin :**
>
> ```
>    28/08 05:53   creation de l'annonce 62966 AVEC son mandant integre
>    28/08 05:55   « generer le n° de mandat »              ->  REUSSI
> ```
>
> Six minutes plus tard, meme worker, meme compte GONZALEZ. Ca marche parce que
> le mandant etait deja la.
>
> **LE VRAI DEFAUT est ailleurs -- dans le travail de 05:48 :**
>
> ```
>    05:48:51   « Association mandant/proprietaire dans Hektor »   l'ecriture PART
>    05:48:57   ERREUR « association non confirmee »               la relecture echoue
> ```
>
> **L'association a ete FAITE** -- c'est pour cela qu'Hektor affiche aujourd'hui
> « Bien ajoute le 28-08-2026 ». Ce qui a echoue, c'est la RELECTURE, filtree par
> l'agence du compte. Le travail a ete marque en erreur alors qu'il avait reussi,
> et on a cru le rattachement non passe.
>
> ```
>    generer le n° de mandat   OK -- l'echec du 28/08 etait JUSTIFIE
>    rattacher un mandant      a reussi mais s'est declare en echec  <- LE defaut
>    modifier un mandant       faux negatif avere le 31/08 a 17:09   <- LE defaut
> ```
>
> **La parade par l'API reste donc justifiee, mais pour DEUX gestes sur trois,
> pas trois.** Et les 9 504 liens inter-agences decrivent une CONFIGURATION A
> RISQUE, pas un taux d'echec : j'avais ecrit « 47 % du parc » dans un commit,
> c'est mal formule.
>
> Ce n'est pas non plus que le compte formation : l'annonce 24113 (Firminy)
> porte un mandant de **Groupe GTI Saint-Etienne**. Une vraie agence sur le bien
> d'une autre -- c'est ce qui justifie la parade malgre si peu d'echecs constates.
>
> **LA LECON DE METHODE, la troisieme de la journee :** j'ai explique un echec
> par la derniere cause trouvee (le filtrage par agence) sans lire l'ORDRE des
> travaux. La chronologie disait tout, et je ne l'avais pas regardee.

---

**CE QUE L'ESSAI DU 31/08 A LAISSE SUR LA TABLE :**

```
[—] SUPPRIMER UN CONTACT LAISSE SES RAPPROCHEMENTS ORPHELINS
    CLOS LE 31/08 -- LE MENAGE EXISTE DEJA, ET IL TOURNE.

    Avant de coder quoi que ce soit (consigne de Frederic : « verifie ce qui
    existe deja comme systeme de purge pour ne rien casser »), j'ai cherche.
    Il y a app_sweep_search_orphans(), et elle fait EXACTEMENT ce travail :
       - rattache ce qui peut l'etre (propositions, relances, retours
         acquereur, envois email) a la recherche evidente du contact
       - SUPPRIME app_rapprochement et app_rapprochement_score_history
         dont la cle n'existe plus
       - refuse d'ecrire si un conflit d'unicite se presente, et le journalise
       - laisse une trace dans app_sweep_search_orphans_log

    ELLE TOURNE TOUS LES JOURS A 05:00, sans interruption. Elle a nettoye
    10 rapprochements + 15 historiques le 28/08.

    => mes 138 lignes du matin auraient disparu d'elles-memes le lendemain.
       Le nettoyage manuel n'a rien casse, mais il etait inutile.

    RESTE UNE MIETTE, pas un trou : app_rapprochement_search_state n'est pas
    dans le balayage -- 114 lignes orphelines. Une ligne d'etat de
    rafraichissement qui decrit une recherche disparue ne fait rien de mal ;
    elle occupe de la place. A ajouter au sweep un jour, sans urgence.
    (app_notification : 13 orphelines, abandonnees par decision -- « c'est pas
    grave de perdre les notifications ».)

    LA LECON, deuxieme fois dans la meme journee : regarder ce qui existe
    AVANT de conclure a un manque. Les deux « trous » signales le 31/08
    etaient l'un un chemin mort, l'autre un terrain deja couvert.

    ANCIEN ENONCE, conserve :

    handleDeleteHektorContact purge app_contact_search_current (son resultat le
    dit : « app_contact_search_current: 1 ») mais NE TOUCHE PAS a
        app_rapprochement                 (la ligne de rapprochement)
        app_rapprochement_score_history   (son historique de score)
        app_rapprochement_search_state    (l'etat de la recherche)

    MESURE : 3 contacts d'essai supprimes le matin du 31/08 (605093, 605094,
    605095) ont laisse 279 lignes derriere eux -- 138 + 138 + 3. Les huit autres
    tables portant contact_search_key etaient vides pour ces cles.

    POURQUOI CA N'AVAIT JAMAIS ETE VU : personne n'avait encore supprime un
    contact QUI PORTAIT UNE RECHERCHE. Le seul contact supprime auparavant
    (604135, juin) n'en avait pas.

    NETTOYE le 31/08 (0 orphelin restant) mais LE HANDLER N'EST PAS CORRIGE :
    la prochaine suppression d'un contact avec recherche refera le trou.

    OU CORRIGER : Console/console_job_worker.js, le bloc « cleanup » de
    handleDeleteHektorContact -- la ou app_contact_search_current est deja purge.
    Ajouter les trois tables, dans le meme geste et par la meme cle.

[ ] LES LIGNES PROVISOIRES RECONCILIEES NE SONT JAMAIS PURGEES
    Voulu (regle C.1' : une saisie ne se perd jamais, la sortie est un geste
    humain). Mais rien ne les retire une fois « linked » et la resynchro passee :
    elles s'accumulent. Quelques lignes par jour, donc pas urgent -- mais a
    trancher, pas a laisser filer par oubli.

[—] LISTE DES RECHERCHES SCRAPEE          CLOS LE 31/08 -- SANS SUITE
    J'avais signale un risque sur resolveContactSearchTargetCritereId.
    Frederic a corrige : AUCUN WORKER NE PART PLUS pour les modifications de
    recherche. C'est ecrit dans app_edit_search_optimistic :

        push_search = null   /* C.3 24/08 : plus d'envoi vers Hektor */

    et le ciblage ne passe jamais par la console :

        select * into cur from app_contact_search_current
         where hektor_contact_id = clean_id and search_index = v_index;

    L'app cible par (contact, search_index) dans SA table -- celle que l'ecran
    affiche, avec le meme index. Elle trouve toujours la bonne recherche.
    Le defaut existe dans le code mais RIEN NE L'APPELLE. Rien a corriger.

    LA LECON : les 26 traces de jobs n'etaient pas un faible usage, c'etait la
    marque d'une porte fermee exprès (dernier job le 21/08, C.3 le 24/08).
    Mesurer qu'un chemin ne sert plus ne dit pas POURQUOI. Il faut aller lire.
    Voir notice/AUDIT_RECHERCHES_ETAT_REEL_2026-08-31.md
```

---

## PUIS, dans l'ordre du plan

```
[ ] C.19-c    le choix actif / archive remonte jusqu'a l'ecran     2 j
[ ] C.9       la creation part de l'app  + 26bis-3                 1 a 2 sem.
[ ] A.3-tech  le registre des mandats en propre                    3 a 5 j
```

## LE BLOC RATTRAPAGES *(inchange)*

```
[ ] C.16    825 contacts actifs disparus + 5 454 archives
[ ] D.1a    MESURER avant de courir                                1 h
[ ] D.1     documents  40 493        [ ] D.2  photos  1 397
[ ] R.rech  les ~270 premieres recherches invisibles
```

> ⚠ **Jamais deux en meme temps, jamais sans frein.** Le rattrapage des documents nous a deja
> fait bannir l'IP.

## FIN DE PLAN

```
[ ] C.11 · C.13-c · B.3 · E.2 · E.3 · E.4 · F.1
```

## HORS CODE — ce qui fixe la date

```
[ ] A.1  PORTAILS     [ ] A.2  SIGNATURE     [ ] A.3  REGISTRE
```

---

## ✅ FAIT LE 30/08

```
[x] C.4-bis          le filet de rejeu, pose, eprouve, programme a la minute
[x] C.4-bis-0        6 controles fermes, 5 eprouves
[x] C.19 point 1     les 2 handlers de transaction eprouves par la chaine
[x] C.4              archiver · desarchiver · affecter · supprimer une recherche
[—] C.4              supprimer une annonce · lier un mandant  -> SANS OBJET, mesure
[x] carnet annonce   table Supabase + descente + branchement au run  (dormant)
[x] droits           app_console_can_request_job ne rend plus jamais NULL
[x] recherches       les criteres FUSIONNENT au lieu de se remplacer
[x] mesure           1 045 recherches (9,6 %) portent un critere invisible de l'app
[x] commits pousses  origin/main a jour
```

## ✗ DEUX FAUSSES ALERTES DE MA PART, corrigees le jour meme

```
   « les recherches perdent 15 criteres a la saisie »
      FAUX -- la modale n'expose que 7 champs, et l'app garde les sept.
      J'avais lu un convertisseur generique, pas le formulaire.

   « un contact orphelin, cause inconnue »
      FAUX -- decalage d'une nuit, documente le 25/08, avec une sonde a
      seuil 150 et non 0. Il y en avait 15 a la pose, il y en a 1.
```

*Les deux ont ete trouvees parce que Frederic a demande de verifier avant de corriger.*
