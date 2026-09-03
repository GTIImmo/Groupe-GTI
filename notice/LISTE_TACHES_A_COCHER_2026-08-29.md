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
[x] ANNULER un compromis    FAIT 02/09 -- compromis 50059 (EM28412) : status 1 -> 2.
    Le statut de l'annonce NE BOUGE PAS, l'offre acceptee NE PASSE PAS refusee.
    'annuler' retire de la redescente ; il ne reste que 'supprimer', non mesure.
[ ] SUPPRIMER une vente     DESORMAIS POSSIBLE : la vente 23294 existe (cycle 4,
    03/09). Geste IRREVERSIBLE -- une vente ne s'annule pas, elle disparait.
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

[x] CONSTATS D'EXPLOITATION DU 02/09 -- deux alertes qui ne sont PAS des defauts
    (note pour ne pas repartir en chasse la prochaine fois)

    ① LA DESCENTE ECHOUE SI LES WORKERS TOURNENT PENDANT.
       02/09 : 131 tables sur 132 descendues, 1 346 158 lignes. Seule
       app_console_job_log a echoue -- « 185 908 lignes lues, 185 913 attendues,
       l'ancienne copie est conservee ». CINQ lignes d'ecart : c'est le journal
       des workers, il grossit PENDANT la copie.
       Le script compte au debut, lit ensuite, et REFUSE une copie incomplete.
       C'est un garde-fou qui marche, pas une panne.
       Frequence : 2 fois sur 8 descentes, et les DEUX fois pendant une periode
       d'activite (27/08 descente lancee a la main en journee ; 02/09 nos
       workers tournaient pour le test des statuts).

       ⚠ J'AI PROPOSE D'EXCLURE CETTE TABLE, PUIS RETIRE MA PROPOSITION.
       pull_from_supabase.py porte un principe pose le 22/08 :
           « La regle n'a plus d'exception. Rien n'est jamais oublie : PAS DE
             LISTE A TENIR, donc aucune table ne passe au travers. Aucun jugement
             a porter sur qui est le maitre -- je me suis trompe DEUX FOIS SUR
             DIX en essayant. »
       Exclure ces tables reintroduirait exactement le defaut corrige ce jour-la.
       Le benefice (eviter une alerte 2 fois sur 8) ne vaut pas ce cout.
       ➡ ON NE TOUCHE A RIEN. On sait pourquoi ca sonne, cela suffit.

    ② LES RECHERCHES ACTIVES S'ARRETENT QUAND HEKTOR TOUSSE.
       02/09 a 03h00 : « Arret securite ContactById: hard_errors=3/3 ».
       Detail du log : SEPT erreurs HTTP 500 -- serveur de Hektor -- plus un 403
       et un 404. Trois erreurs consecutives declenchent l'arret
       (--max-consecutive-hard-errors 3).
       LE GARDE-FOU A FAIT SON TRAVAIL : il s'arrete au lieu de marteler un
       serveur qui repond mal. C'est ce qui evite les bannissements d'aout.
       Premiere fois en 8 jours. « Reprise : aucun lot complet, tout reprendre
       depuis le debut » -> rien de perdu, seulement retarde d'une nuit.

       ⚠ ET LES 403 NE SONT PAS UN BANNISSEMENT : 4 a 5 chaque nuit depuis une
       semaine (28/08→02/09 : 4,5,5,5,5,4). Un ban serait massif et CROISSANT,
       pas constant a quatre. Ce sont quelques fiches protegees.

[ ] ⬛⬛ LE REGISTRE DES AFFAIRES -- CHANTIER OUVERT le 01/09  ·  URGENT AVANT COUPURE
    Souleve par Frederic : « si mon serveur n'importe plus, le registre des
    affaires -- clientele, offres, ventes -- est compromis, et les ids Hektor
    etant les axes, il y aura un probleme lors de la coupure. Ne faut-il pas
    homogeneiser ? »

    A) ✅ FAIT LE 01/09 -- L'IDENTITE DE L'ACQUEREUR
       RESULTAT :  0 %  ->  28 907 / 28 919  soit 100,0 %   ·   12 orphelines
       Les 2 802 que je croyais perdues ont ete RETROUVEES. Explication : la
       doublure locale `app_contact` garde les contacts disparus (delete-never),
       la elle app_contact_current ne montre que les vivants. Le serveur local a
       donc rattrape 2 796 acquereurs que Supabase seul ne pouvait pas.
       ➡ LA DOUBLURE A PROUVE SA VALEUR : c'est elle qui a sauve le registre.

       CE QUI A ETE FAIT, dans cet ordre :
          1  colonne app_contact_id sur app_affaire_ledger (Supabase) + index
          2  remplissage par la jointure Hektor (26 111)
          3  la RPC app_change_annonce_status_optimistic la pose a la CREATION
             -- sinon le rattrapage serait perime des demain
          4  la meme colonne cote serveur local, avec MIGRATION DOUCE :
             CREATE TABLE IF NOT EXISTS n'ajoute RIEN a une table existante --
             sans l'ALTER, le run de nuit serait tombe sur « no such column »
          5  remplissage local (28 906) puis push -> Supabase a 28 907
       ON N'A RIEN EFFACE : hektor_acquereur_id reste a cote, et l'ON CONFLICT
       du script porte un COALESCE (« vide ne gagne pas ») pour qu'un contact
       inconnu n'efface jamais un rattachement etabli.

       LES 12 QUI RESTENT : 6 gardent un nom dans acquereur_json (BOUZENAD,
       Lanfranchi, SAGNARD), 6 n'ont plus rien. Contacts jamais descendus ou
       supprimes avant la doublure. 0,04 % -- on les laisse.

    A-bis) POURQUOI CE TROU EXISTAIT -- le SEUL angle mort du projet
       Frederic avait raison de rappeler que le travail avait ete fait :
          app_contact_relation_current  (mandants)      79 760   100 %  ✓
          app_rapprochement (acquereurs <-> biens)      47 782   99,9 % ✓
          app_contact_search_current    (recherches)    10 910   100 %  ✓
          app_affaire_ledger            (affaires)      29 305     0 %  ✗
       TROIS SUR QUATRE SONT FAITES. La quatrieme manque.

       POURQUOI ELLE A ETE MANQUEE -- ce n'est pas un report :
       le cadrage (RELECTURE_IDENTITE_CONTACTS_2026-08-24) recensait les tables
       portant `hektor_contact_id`. Celle du ledger s'appelle
       `hektor_acquereur_id`. Elle est passee entre les mailles A CAUSE DE SON
       NOM. app_affaire_ledger n'est citee NULLE PART dans cette note.

       ⚠ ET C'EST LE SEUL ANGLE MORT : recherche exhaustive des colonnes
       designant une personne sans s'appeler hektor_contact_id (acquereur,
       mandant, vendeur, proprietaire, signataire, acheteur) -> UN SEUL
       resultat, app_affaire_ledger.hektor_acquereur_id.

       LA FENETRE SE REFERME, mesure :
          28 919 affaires portent un acquereur
          26 111 encore rattachables aujourd'hui par la jointure Hektor
           2 802 DEJA introuvables (9,7 %) -- il ne reste que acquereur_json
                 (nom, prenom), soit l'identite sans le lien
       Apres la coupure, l'identifiant Hektor ne voudra plus rien dire : les
       26 111 deviendront irrattachables a leur tour.

       A FAIRE : ajouter app_contact_id au ledger · le remplir (26 111
       immediatement) · le faire poser a la creation par la RPC, qui connait
       deja buyer_contact_id · les 2 796 orphelins = rapprochement par le nom,
       chantier separe.

    C) ⬛ LES AFFAIRES VENUES DU RUN SONT PLUS PAUVRES  -- A CORRIGER APRES LE TEST
       Souleve par Frederic le 01/09 : « les transactions provenant du run
       manquent d'information ». Il a raison, mais MOINS que ce que je lui ai
       d'abord repondu -- j'avais dit « la validite n'existe nulle part », c'etait
       FAUX. Mesure exacte, sur les affaires venues du miroir :

          genre        lignes    validite      honoraires   notaire    taux
          offre        11 121    11 068 ✓      11 121 ✓        0        0
          compromis    10 577    10 577 ✓      10 577 ✓        0        0
          vente         7 606       --         7 606  ✓     7 606 ✓     0

       ➡ TOUT EST DEJA DANS payload_json, SAUF DEUX CHOSES :
            le NOTAIRE      absent des offres et des compromis (present sur les ventes)
            le TAUX         absent partout -- Hektor ne le renvoie jamais
       La validite dort dans propositions[0].validite pour 11 068 offres ; le
       delai de retractation dans compromis.dateEnd pour 10 577 compromis.

       DONC LA CORRECTION N'EST PAS D'ALLER CHERCHER AILLEURS : c'est d'EXTRAIRE
       du payload ce qui s'y trouve deja, et de le rendre lisible a l'ecran comme
       le carnet l'est. Chantier de LECTURE, pas de collecte.

       ⚠ ET SURTOUT : NE PAS L'ECRIRE DANS LE CARNET. Le carnet dit ce que l'APP
       detient ; une affaire saisie chez Hektor, l'app n'en detient rien. L'y
       inscrire la ferait GAGNER contre Hektor au prochain run, par le contrat
       d'autorite -- on rendrait faux ce qui est vrai. Il faut donc une LECTURE
       qui compose les trois sources dans cet ordre :
            1. le carnet      ce que l'app detient        (prime)
            2. les colonnes   ce que le ledger porte
            3. le payload     ce que Hektor a renvoye     (le fond de tiroir)

       A FAIRE APRES LE TEST DES STATUTS, pas avant : le test peut encore changer
       ce qu'on croit savoir, comme il l'a deja fait trois fois aujourd'hui.

    B) LE REGISTRE DOIT REDONNER TOUS LES CHAMPS SAISIS  (demande de Frederic)
       Le ledger ne porte que CINQ champs en colonne : montant, date, date_acte,
       sequestre, numero_mandat. Le contrat d'autorite CHAMPS_APP_AFFAIRE en
       nomme DIX (les 5 + prix_net_vendeur, prix_publique, honoraires,
       part_admin, commission_agence) -- les cinq derniers n'ont PAS de colonne
       et ne vivent que dans payload_json (cote Hektor) ou le carnet.

       LA MODALE, elle, saisit QUINZE champs. Ceux qui ne reviennent nulle part :
          validite de l'offre       jamais stocke
          taux d'honoraires         jamais stocke
          notaire acquereur         payload de la VENTE seulement, pas du compromis
          delai de retractation     payload du COMPROMIS (dateEnd) seulement

       Frederic veut de plus AJOUTER des champs a la modale -> il faut donc que
       le registre les accueille SANS nouvelle colonne a chaque fois.

    ➡ LES DEUX PARTIES SE TIENNENT : A donne au registre une identite qui
      survit, B lui donne un CONTENU complet. Un registre d'affaires autonome,
      c'est les deux.

[x] LA CAUSE DE FOND DU BLOCAGE -- CORRIGEE le 01/09 (phase2/sync/affaire_ledger.py)
    Frederic : « il y a un probleme avec ces generation d'id, je veux comprendre ».
    Il avait raison d'insister : le recalage du compteur ne tenait qu'un run.

    LE MECANISME, reconstitue :
       25/08  la 1re affaire nee dans l'app prend 1 000 001
              -> LE MAX DE LA TABLE SAUTE A UN MILLION
       le run distribuait  MAX(app_affaire_id) + 1  SUR TOUTE LA TABLE
       27/08  305 vieilles affaires HEKTOR (2021-2026) arrivent d'un coup
              -> elles prennent 1 000 008 ... 1 000 312, DANS NOTRE PLAGE
       la sequence de l'app, restee a 1 000 017, distribue alors des numeros
       DEJA PRIS -> « duplicate key » -> que le front traduit en « une action
       Hektor est deja en cours pour cette annonce ».

    ➡ SEPT TESTS ONT FAIT BASCULER 305 AFFAIRES REELLES dans la plage reservee,
      et bloque TOUTE creation d'offre / compromis / vente DU 27/08 AU 01/09.

    CE QUI N'ETAIT PAS CASSE, verifie :
       ZERO doublon (aucun triplet Hektor porte par deux app_affaire_id)
       empreinte md5 des 323 lignes IDENTIQUE local / Supabase
       AUCUN code ne lit le seuil 1 000 000 -- il n'est que dans des commentaires
       l'ADOPTION marche : 1 000 001 et 1 000 002, nees dans l'app le 25/08, ont
       garde leur numero et gagne le leur chez Hektor (33026, 33027)

    LE CORRECTIF : le run ignore la moitie haute.
       next_affaire_id = MAX(app_affaire_id) WHERE app_affaire_id < 1 000 000  + 1
       prochain numero : 28 982 au lieu de 1 000 324, soit 972 342 d'ecart
    Les 323 deja placees ne bougent pas : l'ON CONFLICT porte sur le triplet
    Hektor et ne touche jamais app_affaire_id. « Un dossier ne perd jamais son
    numero. »

[x] LA PORTEE DES TROIS PANNES DU 01/09 -- audit demande par Frederic
    « Est-ce que les points 1, 2, 3 ne sont pas egalement le cas avec nouveau
    compromis et vente ? »  -- VERIFIE dans le code, et la reponse est OUI pour
    deux d'entre eux :

    PANNE 1, LE COMPTEUR : OUI, et c'est la plus grave. La RPC
    app_change_annonce_status_optimistic fait nextval pour les TROIS genres
    (v_kind = offre / compromis / vente). Donc AUCUNE creation d'offre, NI de
    compromis, NI de vente ne pouvait aboutir depuis le 27/08. Le recalage du
    compteur les debloque toutes les trois d'un coup.

    PANNE 2, LES ENVELOPPES VIDES : sans rapport avec les affaires. Elle porte
    sur app_annonce_pending, donc sur TOUTES les annonces indifferemment.
    Corrigee pour tout le monde.

    PANNE 3, L'ECRAN : OUI pour les trois. affaireCourantePourStatut() traite
    les trois genres via AFFAIRE_PAR_STATUT, et le repli filtre sur
    a.kind === genre. Corrigee pour les trois -- mais voir le patron
    « En creation… » ci-dessus : le correctif est a moitie fait.

    ET POUR « AJOUTER CONTACT » / « AJOUTER ANNONCE » : NON, la panne 3 ne les
    touche pas. Ces deux-la ont deja le bon patron -- « En creation… », aucune
    action proposee. C'est justement d'eux qu'il faut s'inspirer.

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

[x] ⬛ VERIFIE LE 02/09 -- L'ADOPTION FONCTIONNE, ET SUR LES DEUX CHEMINS
    Run quotidien relance a 11h34, alle jusqu'au bout (exit 0), etape du ledger
    passee en 73 s :
        1 001 324  adoptee par le TRIPLET      (annonce, type, n° Hektor)  -> 33037
        1 001 325  adoptee par l'ACQUEREUR     (annonce, type, acquereur)  -> 33038
        sentinelle app_affaires_sans_numero_hektor : 0 ligne
        compteur de la serie du run : 28 983, INCHANGE
    Ce dernier chiffre est la preuve : le run n'a BRULE AUCUN NUMERO. Il a
    reconnu que l'affaire existait deja chez nous au lieu de la dupliquer.
    ⚠ 1 001 325 a d'abord ete adoptee par l'ACQUEREUR -- le chemin qui compte,
    celui qu'emprunteront toutes les transactions nees dans l'app. Frederic a
    exige qu'on retire le numero pose a la main pour que l'epreuve ait lieu ;
    il avait raison, sans quoi le triplet aurait rendu l'essai trivial.

    (libelle d'origine) L'ADOPTION DE L'AFFAIRE 1 001 324 (offre 175 000, EM28412 / annonce 24933).
    Nee dans l'app le 01/09 a 13h18, orpheline : pas de hektor_affaire_id,
    present_in_hektor = false.

    CE QU'ON ATTEND : le run l'ADOPTE -- elle GARDE son numero 1 001 324 et
    gagne celui d'Hektor. Regle du 25/08, cle (annonce, type, acquereur).
    CE QU'IL NE FAUT PAS VOIR : une SECONDE ligne pour la meme offre.

    MESURE DU TROU AU 01/09 -- il est plus petit qu'annonce :
       Supabase   324 affaires dans la plage app, 1 SEULE orpheline (la notre)
       Local      323, ZERO orpheline
    Les 323 precedentes sont donc rapprochees des deux cotes. Le trou n'est pas
    structurel : il dure le temps d'un run.

[ ] LE PATRON « EN CREATION… » MANQUE AUX AFFAIRES
    Mon correctif du 01/09 (5db18e3) rend l'offre nee dans l'app VISIBLE dans la
    modale -- c'etait le trou. Mais il propose « Refuser » et « Accepter », alors
    que handleGesteHektor exige hektor_affaire_id et repondra « Cette
    transaction n'a pas encore de numero Hektor ». DEUX BOUTONS QUI ECHOUENT.

    LE BON PATRON EXISTE DEJA, chez les annonces et les contacts : une ligne
    provisoire affiche « En creation… » et NE PROPOSE AUCUNE ACTION (bouton
    « Retirer » si erreur). L'utilisateur voit, et comprend pourquoi il attend.

    A FAIRE : appliquer ce patron aux affaires -- montrer l'offre, la marquer
    « En creation… », masquer les gestes tant que le numero Hektor manque.

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

    ✅ LA CIBLE EST NOMMEE -- FAIT LE 02/09 (d712d7f). La modale porte desormais
    le releve de TOUTES les affaires du bien (genre, etat, montant, date,
    acquereur), la morte grisee et barree, et la mention « visee par les
    actions » sur celle que les boutons touchent. Chaque ligne se DEPLIE sur ses
    champs, carnet en vert (il prime) et colonnes en gris. Aucune requete
    nouvelle. Reste de cet item : la modale ne REPOSE toujours pas l'acquereur
    ni le mandat dans son FORMULAIRE -- voir la conflation creer/corriger ci-dessous.
```

## 2 bis. 👁 LA VUE DES AFFAIRES — *audit du 02/09, À FAIRE EN UN SEUL PASSAGE*

> **Demande de Frederic, 02/09** : *« dans rubrique affaire ou ailleurs, y a-t-il une vision sur
> les offres proposees / refusees / acceptees ailleurs que la modale, qui sert plutot aux
> actions ? »* — Audit fait sur le code. **Reponse : plusieurs vues, mais aucune ne montre la
> LISTE des offres d'un bien. Toutes n'en montrent qu'UNE.**

```
ou                          ce qu on voit                          source
rubrique Affaires           carte Offre : etat, montant, date      colonnes offre_* AU SINGULIER
bloc Affaires abandonnees   par acquereur, chaine complete         affaires_detail_json
listes Annonces / Registre  badge « Offre en cours »               binaire, derive de offre_id
fiche mandat                « Offre en cours » / « Aucune »        binaire
tuiles de pilotage          compteurs en cours / refusees          filtrent la LISTE DES BIENS
modale de statut            rien a voir -- elle sert a AGIR        la SEULE a lire le ledger
```

**SIX DEFAUTS MESURES SUR LE CODE**

```
D1  une offre refusee FAIT DISPARAITRE la carte
    hasO = pOffre || hasC, et pOffre tombe des que la derniere proposition est un refus.
    Le refus est pourtant connu : il pilote le cran du cockpit (offre_ref).
D2  l etat affiche est DEVINE
    etat: pOffre && !hasC ? 'Proposition' : 'Acceptee'
    des qu un compromis existe, l offre est dite « Acceptee » -- qu elle l ait ete ou non,
    alors que offre_state est disponible sur la meme ligne.
D3  LE PRIX DU BIEN peut s afficher A LA PLACE du montant de l offre
    montant: money('offre_montant') || formatPrice(dossier.prix)
    -> un chiffre FAUX, sans avertissement. Le plus grave : les autres cachent, celui-la ment.
D4  trois champs codes VIDES EN DUR : validite:'' retract:'' notaires:''
    or 11 068 offres portent leur validite dans propositions[0].validite.
D5  une seule offre par acquereur, y compris dans les abandonnees
    build_affaires_dossiers regroupe par acquereur et ne garde que « la plus avancee ».
D6  l historique INTERNE d une offre (propositions[]) n est nulle part -- jusqu a 6 evenements.
```

**CE QUI DORT EN BASE, ET N EST PAS BRANCHE**

```
app_affaire_ledger        29 307 lignes : genre, etat, montant, date, acquereur, app_contact_id
present_in_hektor=false   les affaires que Hektor a retirees (badge deja fait dans le registre)
app_affaire_champ_app     14 champs de saisie, dont validite / retractation / notaire / taux
propositions_json         l historique evenement par evenement
```

**LES LOTS — et pourquoi ils ne se font PAS separement**

```
[ ] lot 1  DIRE LE VRAI AU LIEU DE LE DEDUIRE     corrige D1 D2 D3
           lire offre_state ; ne JAMAIS substituer le prix du bien au montant ;
           afficher la carte meme refusee, avec sa pastille.
[ ] lot 2  LA LISTE DES AFFAIRES DANS LA RUBRIQUE  corrige D5
           deja fait DANS LA MODALE le 02/09 (d712d7f) -- reste a le porter dans la rubrique.
[ ] lot 3  LE CARNET PRIME + LE PAYLOAD            corrige D4
           = LE CHANTIER DE LECTURE deja ecrit plus haut (carnet -> colonnes -> payload).
           Les DEUX PREMIERES sources sont faites dans la modale ; la TROISIEME reste.
[ ] lot 4  L HISTORIQUE D UNE OFFRE                corrige D6 -- le plus lourd, propositions_json
           n est pas remonte jusqu au front.
```

⚠ **UN SEUL PASSAGE, ET APRES LE TEST DES STATUTS.** Trois raisons, toutes verifiees :

1. le bloc « Affaires abandonnees » est rendu a **DEUX endroits** — rubrique Affaires *et*
   Fiche du cycle. Le toucher separement, c est repasser deux fois ;
2. **C.19-c** (poste n° 5 de l ordre retenu : *« le choix actif/archive remonte jusqu a
   l ecran »*) vise la meme modale et la meme rubrique — a grouper ;
3. le plan le dit deja pour le chantier de lecture : *« A FAIRE APRES LE TEST DES STATUTS,
   pas avant : le test peut encore changer ce qu on croit savoir »*. Les cycles 3 et 4
   (compromis annule, vente) diront quels etats existent et comment ils s enchainent —
   c est exactement ce que la vue doit montrer.

⚠ **RESERVE** : la rubrique vit derriere `VITE_APP_COCKPIT_V2_ENABLED` — `true` en local,
**a verifier cote Vercel** avant de compter dessus en production.

---

## 2 ter. 🔴 C.19-d — **LE REGISTRE DES TRANSACTIONS** · EN COURS

> Ouvert le 02/09 en cherchant pourquoi un compromis cree par l'app n'avait pas
> son acquereur. **Le projet n'a jamais su modifier une transaction.**
>
> 🔄 **REQUALIFIE LE 03/09**, apres l'audit complet demande par Frederic
> (« refaire un audit precis du code actuel et de l'ensemble du projet pour ne
> rien oublier ») — checklist des 5 points appliquee, 12 notes supprimees relues
> dans git, et deux essais reels sur 24933.
>
> **Le titre change.** Ce n'est pas « modifier une transaction » : c'est faire du
> registre d'affaires un REGISTRE A PART ENTIERE, au meme titre que l'annonce et
> le contact. La modification n'en est qu'une piece.

### CE QUE LES DEUX ESSAIS DU 03/09 ONT ETABLI

```
ESSAI 1  reouvrir une vente existante   launchPopinVente(24933, 23294)
         -> « Enregistrer & laisser actif »
         UNE seule vente apres, 23294, MODIFIEE. Acquereur 605030 intact.
         Statut inchange. Aucun doublon.
         ➡ Hektor accepte la MODIFICATION : rouvrir par identifiant fait un UPDATE.
            C'est le socle de la brique 0. (Ne prouve PAS que le WORKER peut le
            piloter : j'ai conduit un navigateur, pas poste un formulaire.)

ESSAI 2  annuler le compromis vivant    cancel_hektor_compromis · 50060 · done
         compromis 50060 -> status 2       la vente 23294 -> INTACTE, acquereur inclus
         statut annonce -> reste « Vendu »  le registre a suivi (state = cancelled)
         ➡ LA VENTE NE DISPARAIT PAS AVEC SON COMPROMIS.
            Les trois transactions ne sont PAS une chaine chez Hektor : ce sont
            trois objets independants poses sur la meme annonce. Cela explique
            enfin les 9 075 annonces vendues portant un compromis « actif ».
```

### LE CYCLE COMPLET DU 03/09 — demande par Frederic : « remettre l'annonce d'aplomb »

> *« supprimer la vente cela permettra d'eprouver ce test puis remettre le statut sur
> actif refaire une offre puis un compromis puis une vente cela bouclera le chantier »*

**① SUPPRIMER LA VENTE 23294 — trois questions tranchees d'un coup**

```
[x] ventes-deleteVente FONCTIONNE          le verbe n'avait JAMAIS ete vu passer ; il
                                           venait d'une lecture statique et etait tenu
                                           pour suspect depuis le 29/08.
                                           delete_hektor_vente · confirmer:true · done
                                           -> la vente a disparu (ids: [])

[x] LE COMPROMIS NE REVIT PAS              question de Frederic du 29/08, ouverte
                                           depuis. 50060 et 50059 restent status 2.

[x] 'supprimer' DANS LA REDESCENTE         l'item disait « JAMAIS MESURE ». Mesure :
                                           le statut REDESCEND, de Vendu a Sous compromis.
                                           ⚠ ET C'EST HEKTOR QUI LE FAIT : sa fiche
                                             affiche le badge COMPROMIS et le rail pointe
                                             SOUS COMPROMIS. Notre redescente a calcule
                                             EXACTEMENT la meme chose -> elles sont
                                             d'accord, la regle est JUSTE, l'item est CLOS.
                                           ➡ LA REGLE DES 7 MESURES A DONC UNE EXCEPTION :
                                             « seule la creation fait bouger le statut »
                                             vaut pour le cycle de vie, PAS pour la
                                             SUPPRESSION -- qui retire l'objet justifiant
                                             le statut.

     ⚠ LE BOUTON N'EST PAS CASSE, IL DEMANDE CONFIRMATION. Deux clics automatises ont
       fige le rendu et je m'appretais a signaler un defaut inexistant. Le code dit :
           if (geste === 'supprimer_vente') { const daccord = window.confirm(...) }
       C'est un dialogue NATIF, pose expres sur un geste irreversible -- une automatisation
       ne peut pas y repondre. C'est Frederic qui a clique OK.

     ⚠ CONFIRMATION EN DIRECT DU FILTRE : sitot la vente supprimee, ListCompromis SANS
       withCompromisStatus rend de nouveau ['50059','50060'] pour cette annonce -- ils
       etaient invisibles vingt minutes plus tot. Le filtre veut bien dire « compromis
       dont l'annonce n'a pas encore de vente » (note du 30/08, verifiee causalement).

     ⚠ ET LE REGISTRE FAIT SON TRAVAIL : la vente 23294 y RESTE, marquee
       present_in_hektor = false. Delete-never. Et la modale l'affiche « plus dans Hektor ».

**② REMETTRE EN ACTIF** — `statut_hektor_apres: 2`, app et Hektor d'accord. L'annonce
quitte le cache des vendus (`annonce_now_current`) et revient au portefeuille
(mandats 725 -> 726, diffusions 458 -> 459).

**③④⑤ REFAIRE OFFRE -> COMPROMIS -> VENTE — le meme acquereur, le meme montant**

```
   cible        preuve de l'arbitre                              statut Hektor apres
   active       --                                                2  Bien actif
   offer        confirmee · id 33043 · identite POSEE            3  Sous offre
   compromise   AMBIGU · candidates [50059, 50060, 50064]        4  Sous compromis
   sold         confirmee · id 23298 · identite POSEE            5  Vendu
```

**LE DEFAUT DU COMPROMIS EST ISOLE AU-DELA DU DOUTE.** Trois transactions creees a la
suite, MEME acquereur (605075), MEME montant (176 000), a quatre minutes d'intervalle :

```
   1001330  offre      33043           en_cours  605075   ✅ numero en 17 s
   1001331  compromis  (SANS NUMERO)   en_cours  605075   ❌ orpheline
   1001332  vente      23298           en_cours  605075   ✅ numero pose
```

Rien d'autre ne differe. Et le journal du worker donne la cause EN TOUTES LETTRES :

```
   « offre 33043 nomme par Hektor dans sa reponse et retrouve dans le releve
     -- on ne devine pas par difference (4 candidat(s) sinon) »
     candidats_par_difference : ["33043","33042","33038","33037"]
     ventes_avant : []                    <-- LA LECTURE « AVANT » A RENDU VIDE
```

➡ **La lecture « avant » ne vaut rien**, et pour une raison structurelle : ListOffres ne
rend que la page des 20 plus recentes de L'AGENCE, et les offres de l'annonce en etaient
tombees. L'offre n'a ete sauvee que par le court-circuit `nommeParHektor`. La vente s'en
sort par sa fenetre de dates. Le compromis, que Hektor ne nomme JAMAIS, n'a aucun filet.

➡ **ET LA MESURE DICTE LE CORRECTIF DE LA BRIQUE 1.3** : ne pas comparer deux lectures de
Hektor, mais comparer la lecture d'APRES **a notre propre registre** -- qui sait exactement
ce qu'on connaissait deja. C'est la seule source fiable de « ce qui est nouveau », et elle
est chez nous.

**CE QUE 0.3 GAGNE AU PASSAGE** — la seconde mesure positive qui manquait :

```
   14:22:00   reenregistrement de la vente        -> datemaj = 14:22:00
   15:05:16   SUPPRESSION de la vente             -> datemaj = 15:05:16
   15:09:31   passage en Actif                    -> datemaj = 15:09:31
   15:21:23   creation de la vente 23298          -> datemaj = 15:21:23
   contre-temoins : 4 h sans derive · lecture · ouvrir/fermer sans enregistrer · assistant
                    en echec -> AUCUN mouvement
```
➡ **0.3 EST CLOS** : quatre positifs, quatre contre-temoins. Le garde-fou anti-ecrasement
des annonces est transposable aux transactions en surveillant la date du BIEN.

**UN DEFAUT DE LECTURE VU EN DIRECT, pour la phase 2** — pendant tout le cycle, le cockpit
a affiche « Compromis en cours » alors que les DEUX compromis etaient annules, et la
vignette disait « Actif » en meme temps. Le listing affichait « Sous compromis » quand
`annonces_current` disait « Actif ». C'est exactement la rubrique qui lit le blob au lieu
du registre.

### LE TABLEAU DE VERITE — 03/09, demande par Frederic

> *« il va falloir d'abord verifier toutes les tables et faire un appel api pour savoir
> si Hektor les connait aussi »*. Fait : Hektor (API), registre Supabase, registre local,
> miroir, et les pointeurs du dossier.

⚠ **UN TROISIEME PARAMETRE DE LA MEME FAMILLE** : `ListOffres` avec
`withOfferStatus=false` remonte TOUS les identifiants d'offre de l'annonce, la ou la
page 1 par defaut ne donne que les 20 plus recentes de l'AGENCE. C'est ce parametre qui
manquait a la lecture « avant » de l'arbitre -- voir `ventes_avant: []`.

```
                    HEKTOR              Supabase      LOCAL        miroir   pointeur
   offre  33037     refus               refused       refused        oui
   offre  33038     refus               refused       refused        oui
   offre  33042     refus (3 props)     refused       ACCEPTED ✗     oui     offre_id
   offre  33043     proposition         en_cours      ABSENT ✗     ABSENT ✗
   comp   50059     status 2, acq []    cancelled     cancelled      oui
   comp   50060     status 2, acq 605030 cancelled    ACTIVE ✗       oui     compromis_id
   comp   50064     status 1 ACTIF,acq[] en_cours     ABSENT ✗     ABSENT ✗
   vente  23294     SUPPRIMEE           trace false   absent       absent
   vente  23298     active 180 000,acq[] en_cours     ABSENT ✗     ABSENT ✗  vente_id=NULL
                          176 000 chez nous ✗
```

**CINQ ECARTS, DONT TROIS SEULEMENT SONT DES DEFAUTS**

```
1  le registre LOCAL a un run de retard   5 lignes contre 9.  PAS un defaut : il ne se
   met a jour qu'a 04:31. Mais c'est lui qui alimente le miroir et les vues.
2  le miroir ne connait aucune vente       PAS un defaut : les deux ventes sont nees
   de cette annonce                        apres le dernier run.
3  LES POINTEURS DU DOSSIER DESIGNENT      DEFAUT. offre_id=33042, compromis_id=50060,
   LES ANCIENNES TRANSACTIONS              vente_id=NULL alors que le statut dit VENDU.
                                           ➡ C'est ce qui a fait viser 33042 au lieu de
                                             33043 quand j'ai clique « Refuser l'offre ».
                                             Un geste part sur la mauvaise transaction.
4  la vente vaut 176 000 chez nous et      DEFAUT. La modale envoie `amount` ET
   180 000 chez Hektor                     `sale_price` ; pour la VENTE, Hektor ne retient
                                           que `sale_price`. L'autre est jete en silence.
5  ni 50064 ni 23298 n'ont d'acquereur     DEFAUT, cause CONFIRMEE le 03/09 par un
                                           essai dedie -- voir « LA TYPOLOGIE » ci-dessous.
   (ancien libelle) 605075 n'est pas type
   chez Hektor                             « acquereur » (typologies_json = ["mandant"]).
                                           605030 l'est (["acquéreur","mandant"]), et son
                                           compromis 50060 a bien recu son acquereur.
                                           ➡ L'OFFRE passe quand meme (elle envoie
                                             id_acquereur, sans filtre). Le COMPROMIS et
                                             la VENTE passent par la liste « Mes
                                             acquereurs », FILTREE sur la typologie.
```

### 🟢 LE COMPROMIS EST MODIFIABLE — PROUVE le 03/09, essai distinguable

> Le verdict du 28/08 (« modifier un compromis est hors de portee du worker, c'est un
> module ES ») est DEFINITIVEMENT FAUX. Essai concu pour ne laisser aucune ambiguite :
> ouvrir l'assistant sur un compromis ACTIF, changer UNE valeur, enregistrer, regarder
> qui bouge. C'est Frederic qui a traverse les quatre etapes et enregistre.

```
   AVANT           50065  prixPublique 177 000  honorairesSortie 8 600
   valeur posee    prixPublique -> 177 500  (l'assistant recalcule honorairesSortie -> 500)
   APRES           50065  prixPublique 177 500  honorairesSortie 500  note « test »
                   50064  176 000  INCHANGE
                   50060  172 000  INCHANGE
                   50059  178 000  INCHANGE
   ➡ AUCUN 50066. C'est une MODIFICATION, pas une creation. Et le module n'a pas
     touche au mauvais compromis -- la crainte du « pire cas » est levee.
```

**ET L'INTUITION DE FREDERIC EST VALIDEE** — *« cela pourrait etre la solution pour les
ecritures comme acquereurs »*. Il a profite de l'essai pour AJOUTER un acquereur et un
notaire pendant la modification :

```
   acquereurs AVANT   ['605030']                        Sophie
   acquereurs APRES   ['49234', '605030']               + M. TEST GTI, ajoute a la main
```

➡ **LA MODIFICATION EST LA VOIE D'ECRITURE DE L'ACQUEREUR.** La creation le perd quand
la typologie ne suit pas ; la modification permet de l'attacher APRES COUP. C'est une
sortie possible pour le defaut de typologie -- a condition que le worker sache la piloter.

**LES ETAPES 2, 3 ET 4 — enfin inventoriees, grace aux captures de Frederic**

```
   etape 2  « Retrocession »            grisee, sautee dans ce parcours
   etape 3  « Calcul des commissions »  Honoraires 8 750 EUR HT (10 500 TTC)
                                        Unites d'entrees   50 %  ->  4 375 HT   [+]
                                        Unites de sorties  50 %  ->  4 375 HT   [+]
                                        Part Reseau       100 %  ->  8 750 HT
   etape 4  « Conditions suspensives »  un [+] pour ajouter des conditions
                                        un champ NOTES  -> « test », RETENU par Hektor
   bouton final : « Enregistrer »  (et non « Enregistrer et terminer » comme la vente)
```

**LE NOTAIRE N'EST PAS LISIBLE PAR L'API** — et c'est un constat pour la brique de relecture :

```
   ListCompromis      ne renvoie AUCUNE cle « notaires »  (la VENTE, elle, en a une)
   CompromisById      400 Bad Request sur ?id=  -- et on NE DEVINE PAS un nom de
                      parametre : « un mauvais nom n'ecrit rien ET ne dit rien »
   ➡ un champ qu'on peut ECRIRE mais pas RELIRE echappe a la verification. Il faudra
     le relire par la console, ou l'accepter en aveugle -- a trancher.
```

**TROIS MODIFICATIONS D'AFFILEE — la preuve est refaite trois fois**

```
   177 000  ->  177 500   honorairesSortie 8 600 -> 500     note « test » ajoutee
            ->  178 000   honorairesSortie -> 1 000
            ->  178 500   honorairesSortie -> 1 500
   A CHAQUE FOIS : toujours 50065, aucun 50066, et 50064 / 50060 / 50059 INTACTS.
```

**ET L'ACQUEREUR S'ECRIT PAR LA MODIFICATION — c'est la sortie du defaut de typologie**

```
   acquereurs   ['605030']                        au depart
             -> ['49234', '605030']               Frederic en ajoute un
             -> ['49234', '86793', '605030']      puis un autre
```

➡ Ce que la CREATION perd quand la typologie ne suit pas, la MODIFICATION l'attache.
   C'est la reponse a la question ouverte depuis le 02/09.

⚠ **86793 n'est dans AUCUNE de nos tables de contacts.** Frederic l'a choisi dans la
liste de l'assistant. Hypothese : il vient de l'onglet « Mon reseau » (contact d'une
autre agence) que notre synchro ne rapatrie pas. A verifier -- si des acquereurs nous
sont inconnus, le registre portera des liens vers des contacts qu'il ne connait pas.

⚠ **LE NOTAIRE RESTE INVISIBLE.** Frederic en a ajoute un au premier essai ; il n'est
NI dans `acquereurs`, NI dans aucune cle du listing. Mon hypothese « les notaires sont
ranges parmi les acquereurs » est REFUTEE : 86793 est un acquereur choisi a la main.

**LA ROUTE EST CONNUE — journal reseau du navigateur, 03/09**

```
   GET   xmlrpc.php?mode=annonce-SuiviVente-compromis-createCompromis    <- ouverture
   POST  xmlrpc.php?mode=annonce-SuiviVente-compromis-getStepCompromis   <- les etapes
   POST  xmlrpc.php   (mode dans le CORPS)                               <- enregistrement
   -> le motif se repete exactement trois fois, une par ouverture
```

➡ **MEME FAMILLE QUE LA VENTE** (`createVente` + `getStepVente`), et la vente, elle,
porte `idVente` dans CHAQUE POST. Il reste a verifier que `idCompromis` voyage pareil.

**⚠ MON ERREUR DE MESURE, ET ELLE COUTE UN ESSAI**

```
   SIX sondes JavaScript posees, AUCUNE n'a vu l'enregistrement :
      fetch · XMLHttpRequest · sendBeacon · evenement submit ·
      HTMLFormElement.prototype.submit · beforeunload
   Et pourtant le journal RESEAU DU NAVIGATEUR, lui, a tout vu.
   ➡ LA LECON : pour observer une page qu'on ne maitrise pas, le journal du
     navigateur bat l'instrumentation JavaScript. Mes sondes meurent au
     rechargement et ratent ce qui part par un chemin non prevu ; le journal
     ne rate rien. J'ai perdu trois essais a m'en apercevoir.
   ➡ ET L'OUTIL QUI DONNE LES CORPS EXISTE DEJA : Console/capture_compromis_acquereur.js,
     ecrit le 02/09 pour cette question precise -- vrai navigateur, copie JETABLE de la
     session worker (jamais reecrite), postData de chaque requete, arret immediat sur 403.
     Il filtre deja sur getStepCompromis. Il n'a jamais servi a ca.
```

**➡ CE QUI RESTE AVANT DE CODER LA MODIFICATION DEPUIS L'APP** *(demande de Frederic)*

```
[ ] capturer la requete d'enregistrement de l'assistant compromis (fetch + XHR)
    -> sans elle on sait que le geste MARCHE, mais pas par ou il passe
[ ] verifier que le worker peut la rejouer (il n'a pas de module ES, il poste)
[ ] et pour la VENTE, la route est deja connue : getStepVente + idVente a chaque etape
```

---

### LA TYPOLOGIE DE L'ACQUEREUR — hypothese CONFIRMEE le 03/09

> Cycle refait a la demande de Frederic, avec **Sophie (605030) des l'offre** -- la seule
> des deux contacts d'essai typee « acquereur ». Quatre mesures, correlation parfaite.

```
   compromis 50065  status 1  177 000  ACQUEREURS ['605030']   Sophie   ✅
   compromis 50064  status 2  176 000  ACQUEREURS aucun        605075   ❌
   compromis 50060  status 2  172 000  ACQUEREURS ['605030']   Sophie   ✅
   compromis 50059  status 2  178 000  ACQUEREURS aucun        (aucun envoye)

   app_contact_current.typologies_json
      605030  Sophie TEST MANDANT 25-08   ["acquéreur", "mandant"]   -> PASSE
      605075  M. Test CLOTURE             ["mandant"]                -> PERDU
```

➡ **LA TYPOLOGIE DU CONTACT EST LE DISCRIMINANT.** Sophie passe deux fois sur deux,
CLOTURE echoue une fois sur une. Et l'asymetrie entre les genres est mesuree :

```
   OFFRE               envoie id_acquereur, SANS filtre de typologie
                       -> 33037/33038/33043 ont bien 605075 comme acquereur,
                          alors qu'il n'est QUE mandant
   COMPROMIS / VENTE   passent par la liste « Mes acquereurs », FILTREE sur la
                       typologie -> un contact non type est ABANDONNE EN SILENCE.
                       Le champ acquereurs[] est poste, Hektor l'ignore, personne
                       n'est averti.
```

⚠ **C'est le pire comportement possible** : ni erreur, ni message, ni trace. Exactement
ce que la « relecture immediate » (brique 3) doit rendre visible.

**AUTRES CHAMPS ABANDONNES EN SILENCE, mesures sur l'offre 33046 du 03/09**

```
   envoye numero_mandat = 11939   ->  Hektor garde id_mandat = 0
   (coherent avec les 98 % d'offres sans mandat du parc : ce n'est pas une
    anomalie de nos donnees, c'est Hektor qui ne retient pas le mandat sur une offre)
```

**TROISIEME REPRODUCTION DU DEFAUT DU COMPROMIS, meme cycle**

```
   offre     33046  confirmee · identite POSEE
   compromis 50065  AMBIGU · candidates [50065, 50059, 50060, 50064]  -> aucun numero
```
Les QUATRE compromis de l'annonce sont apparus comme candidats : la lecture « avant »
n'a, une fois de plus, rien rendu. Trois cycles, trois fois le meme resultat.

**LES TROIS CORRECTIONS DE CODE QUE CE RELEVE COMMANDE**

```
[ ] A  le pointeur du dossier ne designe plus la transaction courante -- c'est le
       REGISTRE qui le fait. (deja la brique 2.1, mais on en a maintenant la
       consequence concrete : un geste sur la mauvaise offre)
[ ] B  UN SEUL champ de montant par genre -- arreter d'envoyer deux valeurs dont une
       est jetee sans le dire
[ ] C  VERIFIER LA TYPOLOGIE DE L'ACQUEREUR avant d'envoyer un compromis ou une vente,
       sinon le lien est perdu en silence.  ⚠ BRIQUE NOUVELLE, ABSENTE DU PLAN.
```

**TRACES LAISSEES SUR 24933** *(a nettoyer en fin de chantier)*
```
   offres      33037 refusee · 33038 refusee · 33042 acceptee · 33043 en cours
   compromis   50059 annule · 50060 annule · 50064 ACTIF
   ventes      23294 SUPPRIMEE (trace au registre) · 23298 active
   statut      Vendu
```

### CE QUE L'AUDIT A CORRIGE — trois erreurs de ma part

```
1  LE CARNET N'EST PAS LE REGISTRE
   carnet    app_affaire_champ_app        51 lignes / 7 affaires -- toutes nos tests
   registre  app_affaire_ledger       29 314 lignes -- tout le parc
   « retirer le carnet » (brique 5) ne visait QUE la salle d'attente des 3 a 4
   champs sans colonne. Mesure du 03/09 : sur ses 11 champs, 8 ont DEJA leur
   colonne au registre (pure duplication) ; seuls jours_retractation (5),
   jours_validite (3) et taux_honoraires (5) sont orphelins -- 13 lignes.
   ➡ AUCUN changement de cap. J'avais fait dire a Frederic l'inverse de ce qu'il
     disait, en confondant les deux tables.

2  LA LIGNE ENTRE AU REGISTRE DES LE GESTE, pas au run
   app_change_annonce_status_optimistic frappe deja son numero
   (nextval app_affaire_id_app_seq, plage reservee >= 1 000 000) et pose la ligne,
   hektor_affaire_id = NULL, present_in_hektor = false.
   J'avais lu first_seen_at -- que l'upsert du run ECRASE. Mesure mal lue.
   ➡ Ce qui attend le run, ce n'est pas la ligne : c'est le NUMERO HEKTOR.

3  LE NUMERO MANQUANT A TROIS CAUSES, pas une   (releve dans transaction_preuve)
   offre     33042  confirmee=false, identite skipped
                    -> la 3e lecture (transaction_etat_from_api.py) ne connait
                       que « compromis » et « vente ». Un garde-fou qui ne peut
                       pas passer n'est pas un garde-fou, c'est un mur.
                       (contournement dejaDeuxPortes ecrit, pas en service ce jour-la)
   compromis 50060  ambigu=true, candidates [50059, 50060]
                    -> l'arbitre travaille par DIFFERENCE avant/apres. La lecture
                       « avant » n'a pas conclu, donc les DEUX compromis sont
                       apparus neufs, et la regle a joue : « on ne devine pas
                       lequel est le notre ». REFUS PRUDENT ET CORRECT, pas une panne.
   vente     23294  confirmee=true, identite done -> numero pose immediatement
   ➡ LA FRAGILITE N'EST PAS UN PARAMETRE, C'EST LE PRINCIPE DE LA SOUSTRACTION.
     Elle casse des qu'une annonce porte plusieurs transactions du meme genre :
     936 annonces pour les offres, 579 pour les compromis.

   ⚠ Le parametre manquant reste un VRAI defaut, mais son effet est plus etroit :
     transactions_annonce_from_api.py:111 n'envoie pas withCompromisStatus=false,
     alors que sync_raw.py:231 le fait. Sans lui, Hektor masque les compromis
     d'une annonce DEJA VENDUE -- mesure deux fois le 03/09 : la liste saute
     50060 et 50059 et commence a 50061. L'arbitre declare alors « AUCUN
     compromis nouveau » sur une creation REUSSIE. Faux echec, bruyant.
```

### LA DECISION D'ARCHITECTURE — arretee le 03/09

Le projet a **trois mecanismes distincts**, et je les avais confondus :

| mecanisme | protege quoi | employe pour |
|---|---|---|
| **la doublure** | le **NUMERO** | qu'une ligne ne perde jamais son identite |
| **le contrat d'autorite** | la **VALEUR** | **uniquement** les champs que Hektor **IGNORE** |
| **le pending + garde-fou** | l'**ECRITURE** | tous les champs que Hektor **CONNAIT** |

Les transactions emploient aujourd'hui le **deuxieme** sur 10 champs que Hektor
connait parfaitement (montant, date, date_acte, sequestre, prix_net_vendeur,
prix_publique, honoraires, part_admin, commission_agence, numero_mandat).

**C'etait juste le 29/08** : l'app ne savait pas pousser une correction, et
proteger etait la seule facon de ne pas perdre la saisie. Le fichier le dit
lui-meme avec gene — *« la regle est celle du mandat, pas celle des contacts,
parce que Hektor connait ces champs-la, lui »*.

**Le chantier ouvre la route de la poussee : ces 10 champs doivent passer au
troisieme mecanisme.** Le moment est bon — `appliquer_contrat_affaire.py` NE FAIT
RIEN aujourd'hui (le magasin est vide), donc on corrige la trajectoire avant
qu'elle ne porte des donnees reelles.

> **ON NE PROTEGE PAS LA DONNEE, ON PROTEGE L'ECRITURE.**
> Ce que l'app a saisi n'est pas une valeur qu'elle possede : c'est une
> **ECRITURE EN ATTENTE**, qui verifie avant de partir et qui reste en attente
> tant qu'elle n'est pas partie. Une valeur possedee ecrase Hektor pour toujours ;
> une saisie en attente cherche a le rejoindre, et disparait une fois arrivee.

C'est le patron **deja en production sur l'annonce** — saisie optimiste +
`base_snapshot`, garde-fou `annonce_overwrite_guard` (relire la date_maj fraiche,
comparer a la photo, `held_conflict` si Hektor a bouge), `markAnnoncePartial` si
la poussee est incomplete, puis relecture `refresh_console_data`. Et sur le
contact, dont le code dit lui-meme « miroir du garde-fou contact (Lot B) ».

**Il n'y a rien a inventer. Il y a a PORTER.**

⚠ **ET IL EXISTE MOINS CHER, QUI N'EST PAS TECHNIQUE.** Volume reel mesure le
03/09 : sur 30 jours, **89 offres + 18 compromis + 9 ventes = 116**, soit 4 a 5
gestes par jour pour toute l'agence (1 168 sur l'annee). A ce volume, decider que
*« une transaction se saisit dans l'app »* rend le garde-fou **rare et sans
enjeu** au lieu d'en faire une piece critique. C'est exactement la doctrine du
plan (« on inscrit un champ a l'app quand les negociateurs sont passes sur
l'app »). **A trancher par Frederic — ce n'est pas une decision technique.**

### LES TROIS CLASSES DE CHAMPS — et aucune ne demande de fusion

```
A  Hektor IGNORE le champ       colonne protegee au registre, le run ne l'ecrit jamais
                                jours_validite, jours_retractation, taux_honoraires,
                                notaire_id -- c'est birth_date d'un contact
                                ZERO conflit possible : Hektor n'a rien a dire

B  Hektor ACCEPTE l'ecriture    l'app POUSSE, RELIT, et ecrit ce que Hektor a RETENU
                                -> les deux cotes identiques PAR CONSTRUCTION
                                -> et les refus silencieux deviennent VISIBLES
                                ZERO conflit possible : la valeur de l'app est chez eux

C  Hektor REFUSE l'ecriture     l'app N'EDITE PAS le champ -- lecture seule, avec
                                la mention « se modifie dans Hektor »
                                ZERO conflit possible : l'app ne produit rien
```

**Dans les trois cas il n'y a jamais deux valeurs concurrentes.** C'est ce qui rend
la solution solide : elle ne repose sur AUCUNE regle d'arbitrage, donc aucune
regle ne peut se tromper.

*Ecartees le 03/09, et c'est moi qui les avais proposees : l'empreinte de contenu
+ notre propre date de maj (ajouter un mecanisme la ou le projet en a deja un qui
marche), et les colonnes protegees sur des champs que Hektor connait (c'est le
GEL que Frederic a repere le premier).*

---

## LES PHASES — methode du 21/08 : ce que ca fait · ce que ca touche · retour arriere · verification

### PHASE 0 — MESURER · rien a coder · **BLOQUANTE**

> **Rien ne se code avant cette phase.** C'est elle qui decide de la forme des
> trois autres. Si la campagne dit que Hektor refuse presque tout, la phase 3 se
> reduit a peu de chose et la phase 2 devient l'essentiel du chantier.

```
[~] 0.1  LA CAMPAGNE DES CHAMPS       COMMENCEE le 03/09 -- premier tableau obtenu
         SANS AUCUNE ECRITURE : le cycle complet avait envoye des valeurs connues,
         il suffisait de relire ce que Hektor a RETENU.

   ── ENVOYE CONTRE RETENU, compromis 50064 ──────────────────────────────
      amount 176 000          -> prixPublique 176 000               B accepte
      transaction_date 02/09  -> dateStart 2026-09-02               B
      signature_date 05/12    -> dateSignatureActe 2026-12-05       B
      buyer_fees 8 600        -> honorairesSortie 8 600             B
      retraction_days 10      -> dateEnd 2026-09-12                 B mais CONVERTI
                                 (debut + 10 j : Hektor stocke une DATE, pas un nombre)
      sale_price 180 000      -> aucun champ                        IGNORE
      validity_days 20        -> aucun champ                        A  Hektor l'ignore
      buyer_fees_rate 5       -> aucun champ                        A
      net_seller_price vide   -> prixNetVendeur 170 000             C  Hektor le CALCULE
      (rien envoye)           -> honorairesEntree 10 000            C  pose seul, du mandat
      buyer_contact_id 605075 -> acquereurs []                      ❌ PERDU

      vente 23298 : date OK · honorairesSortie OK · acquereurs [] PERDU
      et Hektor calcule seul honoraires 18 600, honorairesHT 15 500,
      commissionAgence 15 500, honorairesEntree 10 000.

   ➡ LA CLASSE A EXISTE ET ELLE EST MESUREE : validity_days et buyer_fees_rate
     n'ont AUCUNE destination chez Hektor. Ce sont les premiers champs a loger
     en colonne protegee (brique 1.2).
   ➡ LA CLASSE C EST PLUS LARGE QUE PREVU : prix net vendeur, honoraires HT,
     commission agence et honoraires d'entree sont CALCULES par Hektor. Les
     inscrire au contrat les figerait sur une valeur qu'on n'a pas a decider.
   ⚠ UN DES DEUX CHAMPS DE MONTANT EST SILENCIEUSEMENT ABANDONNE, ET PAS LE MEME
     SELON LE GENRE : sur le compromis `amount` devient le prix et `sale_price`
     disparait ; sur la vente c'est `sale_price` qui devient le prix. La modale
     envoie deux champs, Hektor n'en garde qu'un, sans le dire.
   ⚠ ET UNE INCOHERENCE MESUREE : l'assistant affiche prixNetVendeur = 157 400
     (176 000 - 8 600 - 10 000) quand l'API rend 170 000 (180 000 - 10 000).
     Deux calculs pour le meme champ. A trancher avant de s'appuyer dessus.

   ── L'INVENTAIRE DES CHAMPS DE HEKTOR, releve dans l'assistant du COMPROMIS ──
      (compromis 50064 ACTIF, ouvert en modification puis FERME sans enregistrer)

      dateCompromis              nbJoursRetractation        dateSignatureActe
      prixPublique               prixNetVendeur             prixDeVente
      montantHonoraireEntree     tauxHonoraireEntree     <- VENDEUR
      montantHonoraireSortie     tauxHonoraireSortie     <- ACQUEREUR
      sequestre                  mandat (select)            mandants[]
      mandantSearch              addAcquereurSearch         addAcquereurNotaireSearch
      content_pdf (textarea)
      caches : containerName=PopinCompromis · step · fromStep · typeUser=NEGO
               isModePrive · id_compromis

      QUATRE ETAPES :  1 Donnees du compromis  ·  2 Retrocession
                       3 Calcul des commissions  ·  4 CONDITIONS SUSPENSIVES
      BOUTONS :        Etape suivante · Fermer · Annuler
                       « Enregistrer le brouillon »  ·  « Enregistrer et terminer »

   ── CE QUI MANQUE A LA MODALE DE L'APP (demande de Frederic) ───────────────
      1  montantHonoraireEntree   les honoraires VENDEUR (10 000 EUR) -- la modale
                                  n'a que ceux de l'acquereur
      2  tauxHonoraireEntree      le taux VENDEUR (5,974 %) -- la modale n'a qu'un
                                  seul « TAUX HONORAIRES », qui est celui de SORTIE
      3  mandants[]               le choix des mandants ; la modale ne le propose pas
      4  content_pdf              le contenu du document
      5  ETAPE 2 « Retrocession »            entierement absente
      6  ETAPE 3 « Calcul des commissions »  unites d'entree / de sortie / part reseau
      7  ETAPE 4 « Conditions suspensives »  entierement absente
      8  LES DEUX MODES D'ENREGISTREMENT     brouillon / terminer -- la modale n'en a
                                             qu'un, et le « brouillon » n'existe nulle
                                             part chez nous
   ⚠ Le point 2 n'est pas cosmetique : le taux VENDEUR determine les honoraires
     d'entree (10 000 EUR), donc la commission de l'agence. Il est aujourd'hui
     invisible ET non modifiable depuis l'app.

   >>> RESTE A FAIRE : les etapes 2, 3 et 4 n'ont pas pu etre inventoriees --
       l'assistant REFUSE D'AVANCER sous automatisation (meme comportement que
       celui de la vente au second passage). Il faudra soit un relevé fait a la
       main par Frederic, soit lire les definitions du module
       Modules/GenericPopinStepperManager.

[x] 0.2  LE CORPS DE LA REQUETE       FAIT le 03/09 14h20 -- REPONSE : OUI.
         Capture par instrumentation XHR de la page (lecture seule, aucun envoi
         de ma part), sur la reouverture de la vente 23294 :

            ouverture     getStepVente   idAnnonce · idVente=23294 · basket ·
                                         initBasket · idVente        67 o / 5 champs
            etape 1->2    getStepVente   prixDeVente, dateVente, tauxHonoraireEntree,
                                         tauxHonoraireSortie, mandat, selectedMandat,
                                         mandants[], acquereurs[], typeUser,
                                         idAnnonce, idVente, step, basket
                                                                  1 582 o / 26 champs
            etape 2->3    getStepVente   unitesEntreePercent, unitesSortiePercent,
                                         idAnnonce, idVente, step, basket
                                                                  1 936 o / 10 champs
            ENREGISTREMENT getStepVente  containerModule[], containerName, fromStep,
                           + save,treat  idAnnonce, idVente, step, basket
                                                                  2 148 o /  8 champs

         ➡ `idVente` VOYAGE A CHAQUE ETAPE, Y COMPRIS A L'ENREGISTREMENT.
           C'est un formulaire urlencode ordinaire, sur EXACTEMENT la route que le
           worker emploie deja pour CREER une vente. Toute la difference entre
           creer et modifier tient dans ce parametre. PAS de module ES pour la
           vente -> LE WORKER PEUT MODIFIER UNE VENTE.
           Le `basket` grossit 67 -> 1 582 -> 1 936 -> 2 148 : c'est l'etat PHP
           serialise que le worker recopie deja sans le lire.
         ⚠ La chorégraphie est en TROIS temps, comme la creation. Le worker devra
           donc OUVRIR avec idVente, puis enchainer -- pas poster l'enregistrement seul.

[x] 0.3  LA DATE DU BIEN BOUGE-T-ELLE  FAIT le 03/09 -- REPONSE : OUI, a la minute.

            T0  14:19:09   datemaj = 10:28:56   inchangee depuis 4 h  (pas de derive)
                ~14:22     REENREGISTREMENT de la vente 23294
            T1  14:22:32   datemaj = 14:22:00   <- la minute exacte du geste
            T2  14:27:17   datemaj = 14:22:00   apres rechargement de la fiche,
                                                90 s d'attente, puis ouverture de
                                                l'assistant et FERMETURE SANS
                                                ENREGISTRER -> AUCUN mouvement

         ➡ UN POSITIF ET TROIS CONTRE-TEMOINS : elle ne derive pas seule, la
           LECTURE ne la touche pas, OUVRIR SANS ENREGISTRER ne la touche pas --
           seul l'ENREGISTREMENT la deplace. Le garde-fou anti-ecrasement des
           annonces est donc TRANSPOSABLE aux transactions en surveillant la date
           du BIEN.
         ✅ REPETITION PRISE le 03/09 avec le cycle complet : QUATRE positifs
           (14:22 reenregistrement · 15:05 suppression · 15:09 passage en Actif ·
           15:21 creation de la vente 23298) et QUATRE contre-temoins.
           0.3 EST CLOS -- voir « LE CYCLE COMPLET DU 03/09 » plus haut.
         ⚠ ET LE GARDE-FOU SERA LARGE : la date du bien bouge aussi pour une
           photo ou un prix. Il se trompe DU BON COTE -- il bloquera parfois pour
           rien (et montrera un conflit), jamais il ne laissera passer un
           ecrasement en silence.

[x] 0.4  LE COMPTE                    FAIT le 03/09 -- mesure sur le DOM de la
         fiche 24933, en session ADMINISTRATEUR :

            offre_bien_change_status('refus','33042')     90x37   VISIBLE
            offre_bien_change_status('accepte','33038')   98x37   VISIBLE
            offre_bien_change_status('accepte','33037')   98x37   VISIBLE
            add_offre('24933')                          210x45   VISIBLE
                 (mais Hektor refuse au clic pour un admin -- releve du 28/08)
            delete_compromis_vente('50059')              25x25   VISIBLE
            clore_compromis_vente('50059')                 0x0   MASQUE
            supprimerVente(23294)                          0x0   MASQUE

         🔴 J'EN AI TIRE UNE CONCLUSION FAUSSE, ET FREDERIC L'A CORRIGEE :
            « le compromis est annulable a partir du compte admin, mais il faut
              etre sur compromis et pas vente ; et la vente peut etre supprimee
              avec une gomme ».
            Il a raison, et la preuve est dans la journee meme : notre worker a
            ANNULE le compromis 50060 en session admin a 08h40 -- job `done`,
            status passe a 2. Annuler un compromis en admin MARCHE.

         CE QUE LA MESURE DIT VRAIMENT (sonde approfondie, 03/09 14h35) :
            la « gomme » est la classe `icon-effacer`. Elle existe pour TOUT :
            les 3 offres, le compromis, la vente, et le bien lui-meme.

               icon-effacer  delete_offre_suivi('33042'/'33038'/'33037')   0x0
               icon-effacer  delete_compromis_vente('50059')             25x25
               icon-effacer  supprimerVente(23294)                         0x0
               icon-effacer  deleteAnnonceFromListing('24933')           25x25

            Les gommes des OFFRES sont a 0x0 alors que leurs boutons
            accepter/refuser sont VISIBLES -- aucune theorie de compte n'explique
            cela. Et la cause est ecrite en clair dans le HTML :

               gomme VENTE      style="display:none;width:25px;..."   <- le SERVEUR
               gomme COMPROMIS  style="width:25px;..."                <- meme style,
                                                                        sans le none

            Tous les parents sont visibles (div#ventes display=block), et le
            survol ne change rien. C'est donc le SERVEUR qui decide, au cas par
            cas, et RIEN dans cette mesure ne permet de l'imputer au compte.

         ⚠ LA NOTE DU 29/08 PORTE LA MEME ERREUR : « le bouton supprimerVente
           present en DOM mais masque (0x0) POUR LE COMPTE ADMINISTRATEUR ». Le
           masquage est mesure, l'imputation au compte ne l'est pas. A ne pas
           recopier tant qu'un second compte n'a pas ete essaye.

         ➡ CE QUI RESTE ETABLI SUR LE COMPTE : uniquement le message de refus
           A L'EXECUTION releve le 28/08 -- « Un compte administrateur ne peux pas
           saisir une offre ». C'est un refus de Hektor au clic, pas un masquage.
         ➡ ET LA VENTE RESTE SUPPRIMABLE : par le bouton « Supprimer la vente »
           de la modale de l'app, qui passe par le travail `delete_hektor_vente`
           (verbe `ventes-deleteVente` corrige le 29/08, jamais encore tire).
         ➡ EN PASSANT : la fiche expose les commandes des TROIS offres, alors
           qu'elle n'expose que celles d'UN SEUL compromis (50059, deja annule).
           L'asymetrie est reelle et confirme le piege du 29/08.
```

**➡ STOP. On relit ensemble avant de continuer.**

### PHASE 1 — LE REGISTRE · invisible a l'ecran

```
[ ] 1.1  LE LIEN ENTRE LES ETAPES
         Un numero de dossier d'affaire, FRAPPE par une sequence -- JAMAIS
         calcule. Partage par l'offre, le compromis et la vente d'un meme acquereur.
         ⚠ POURQUOI FRAPPE ET NON CALCULE : « deux copies d'une formule divergent
           tot ou tard » -- c'est ce qui a condamne le calcul de la cle de relation
           cote app (26bis-relations). Un numero tire d'une sequence ne peut pas
           diverger, puisqu'il n'est calcule nulle part. Meme lecon que sur les
           recherches : remplacer le NOM par un NUMERO.
         AUJOURD'HUI le lien est REDEVINE CHAQUE NUIT par build_affaires_dossiers
         (export_app_payload.py:957) a partir de l'ACQUEREUR. La logique est
         BONNE -- un dossier par acquereur, chaine complete, classe par l'etape la
         plus avancee, drapeau « courante », affecte a un cycle (annonce, mandat).
         Mais c'est une devinette refaite chaque nuit, et 387 lignes (1,3 %) n'ont
         aucun acquereur -- dont notre 50059. Apres la coupure, plus de nuit chez
         Hektor pour la redeviner.
         touche : une colonne sur app_affaire_ledger + une etape du run
         retour : la colonne se laisse vide, rien ne la lit encore
         verif : les 521 annonces a plusieurs compromis ET plusieurs acquereurs
                 retrouvent EXACTEMENT les memes dossiers qu'aujourd'hui

[ ] 1.2  LES COLONNES DE CLASSE A     3 a 4 a creer (liste arretee par 0.1)
         retour : colonnes inutilisees · verif : le carnet n'a plus d'orphelin

[ ] 1.3  LE NUMERO HEKTOR POSE PAR IDENTITE, PLUS PAR SOUSTRACTION
         + le parametre withCompromisStatus=false corrige au passage
         touche : console_job_worker.js -> REDEMARRAGE DES 4 SERVICES par Frederic
         retour : revenir a la soustraction
         verif : creer un compromis sur une annonce qui en porte DEJA un, et voir
                 le numero arriver dans la minute (aujourd'hui : le lendemain)
```

### PHASE 2 — L'ECRAN · **c'est la que Frederic voit le changement**

```
[ ] 2.1  LA RUBRIQUE AFFAIRES LIT LE REGISTRE
         AUJOURD'HUI elle ne le lit PAS DU TOUT : deriveAffaire() (App.tsx:25829)
         part de trois booleens tires du STATUT de l'annonce, et retombe sur le
         prix du bien quand un montant manque :
             money('vente_prix') || formatPrice(dossier.prix)
         -> d'ou « Vente 180 000 EUR » alors qu'elle est a 172 000, et
            l'impossibilite STRUCTURELLE d'afficher plus d'une affaire par genre.
         Ce n'est pas un bug a corriger : c'est une rubrique jamais branchee.
         ⚠ PLUS LOURD QU'IL N'Y PARAIT : case_dossier_source ne porte QU'UN
           identifiant de chaque (offre_id, compromis_id, vente_id),
           app_view_generale en herite, et le front raisonne dessus. A trancher :
           changer la source, ou lire le registre A COTE.
         C'est le Lot 3 deja specifie le 28/08 : « brancher app_affaire_ledger sur
         l'annonce, comme il l'est deja sur le registre des mandats. AUCUNE donnee
         a produire : elles sont deja la. »
         verif : sur 24933, TROIS offres et DEUX compromis affiches, vente a
                 172 000 et non 180 000, et la saisie visible immediatement

[ ] 2.2  LE CHOIX QUAND PLUSIEURS CHAINES VIVENT
         AUJOURD'HUI affaireCourantePourStatut() rend null en cas d'ambiguite et
         AUCUN bouton n'apparait (« mieux vaut aucun bouton qu'un bouton qui agit
         sur la mauvaise affaire »). Mesure du 03/09 : 17 annonces pour les
         compromis, 16 pour les offres, 7 pour les ventes -- 40 au total.
         Rare, mais apres la coupure ce silence devient une impasse.
         ⚠ DOCTRINE A RESPECTER : « l'utilisateur DESIGNE, le worker EXECUTE ».
           On AFFICHE le choix, on ne devine pas. Rendre le worker « intelligent »
           sur le choix de la transaction est explicitement interdit (28/08).
```

### PHASE 3 — L'ECRITURE PART CHEZ HEKTOR · *conditionnee par 0.1 et 0.2*

```
[ ] 3.1  LE PATRON DES ANNONCES, PORTE AUX TRANSACTIONS
         saisie en attente avec sa photo · garde-fou avant ecriture · conflit
         VISIBLE · poussee partielle marquee · relecture immediate
         ⚠ CE N'EST PAS UNE RECOPIE, C'EST UN PORTAGE : pour l'annonce le pending,
           le conflit et le badge existent ; pour les transactions RIEN n'existe.

[ ] 3.2  LA VENTE D'ABORD (la seule mesuree), L'OFFRE ENSUITE
         (« possible pour l'offre : formulaire + idOffre », releve du 28/08)
         LE COMPROMIS SEULEMENT SI 0.1 L'AUTORISE
         🔄 REVISE LE 03/09. Le 28/08 declarait le compromis hors de portee parce
           que launchPopinCompromis charge un module ES. L'essai du 03/09 montre
           que le module S'OUVRE et que Hektor refuse pour une raison D'ETAT
           (« un compromis cloture ne peut pas etre modifie »), pas de nature.
           Le module s'appelle GenericPopinStepperManager -- vraisemblablement le
           MEME que celui de la vente, qui poste un formulaire ordinaire.
           ➡ LE COMPROMIS N'EST DONC PROBABLEMENT PAS EN CLASSE C. A confirmer sur
             un compromis ACTIF avant de conclure. Si c'est confirme, la seule
             vraie reserve du chantier tombe.

[ ] 3.3  LES 10 CHAMPS QUITTENT LE CONTRAT D'AUTORITE
         CHAMPS_APP_AFFAIRE -> ne garde que la classe A
         retour : remettre la liste (une ligne)
         verif : modifier dans Hektor, le run redescend bien la nouvelle valeur
```

### PHASE 4 — MENAGE

```
[ ] 4.1  LE CARNET DISPARAIT           APRES 2.1 et 3.1, JAMAIS avant : tant que
         l'ecran compose « carnet + colonnes », le carnet est le seul endroit ou
         la saisie est a l'abri. Le retirer avant, c'est perdre des saisies.

[ ] 4.2  LES DEUX POINTS EN SUSPENS    voir « 2 quater. LES STATUTS » ci-dessous
```

### CE QUI EST DEJA FAIT

```
[x] findProspect                mode=annonce-SuiviVente-compromis-findProspect
                                idProspect · typeIntervenant · provenance · newView · nameInput
                                -> 50060 est le PREMIER compromis de l'app avec un acquereur
[x] multi-acquereurs            buyer_contact_ids ; les DEUX appels reussissent,
                                un seul acquereur survit -- TOUJOURS a comprendre
[x] la modification EXISTE      essai 1 du 03/09 : rouvrir par identifiant = UPDATE
[x] le cycle de vie est SANS EFFET sur le statut   7 mesures concordantes : seule
                                la CREATION fait monter le statut ; refuser,
                                accepter, annuler, reenregistrer ne le bougent jamais
```

### LES INCONNUES ASSUMEES

```
la MODIFICATION PAR LE WORKER   REPONDUE le 03/09 par 0.2 : OUI pour la vente.
                                idVente voyage a chaque etape, formulaire ordinaire.
le COMPROMIS                    🟠 A MOITIE REPONDU -- FREDERIC A CORRIGE MA
                                CONCLUSION TROP RAPIDE (03/09).

                                MESURE : l'assistant S'OUVRE en modification, pre-rempli
                                avec les valeurs de 50064 (176 000, acte 05/12 ; 50059
                                etait a 178 000). Le module charge donc le BON compromis.

                                PAS MESURE : que l'ENREGISTREMENT vise 50064.
                                Frederic : « je pense que le compromis que tu ouvres
                                n'est pas le bon, le seul en affichage est cloture ».
                                Verifie : le formulaire de l'assistant ne porte AUCUN
                                identifiant. Ses seuls caches sont containerModule[],
                                containerName=PopinCompromis, step, fromStep. Les deux
                                `id_compromis` de la page (50059 et 0) appartiennent a
                                la FICHE (#chargeannonce_Content), pas a l'assistant.
                                ⚠ La VENTE, elle, porte idVente=23294 dans CHAQUE POST.
                                  L'asymetrie est reelle : pour le compromis, l'identite
                                  ne voyage pas dans le formulaire.
                                ➡ Enregistrer pourrait donc CREER un 50065, ou ecrire
                                  sur 50059 si le module lit le champ de la fiche.
                                  A TRANCHER PAR UN ESSAI DISTINGUABLE : changer UNE
                                  valeur (prixPublique 176 000 -> 176 500) puis
                                  enregistrer.
                                     50064 passe a 176 500      -> MODIFICATION
                                     un compromis NEUF apparait -> CREATION
                                  Sans cet essai, « le compromis est modifiable » reste
                                  une conclusion non mesuree -- et je l'avais ecrite.

                                CE QUI TOMBE DU 28/08, ET CE QUI RESTE :
                                tombe -- « module ES donc hors de portee » : le module
                                  s'ouvre, et Hektor refuse pour une raison D'ETAT, en
                                  clair (« un compromis cloture ne peut pas etre
                                  modifie », Modules/GenericPopinStepperManager.js).
                                reste -- rien ne prouve que le worker puisse piloter
                                  l'enregistrement, faute d'identifiant dans le formulaire.
                                (ancien libelle : LE VERDICT DU 28/08 EST A REVOIR.) Essai du 03/09
                                14h40 : launchPopinCompromis(24933, 50060) OUVRE bien
                                l'assistant -- le module se charge, aucune
                                impossibilite technique. Hektor refuse pour une
                                RAISON D'ETAT, et il le dit en clair :
                                    « Desole, un compromis cloture ne peut pas
                                      etre modifie »
                                    (Modules/GenericPopinStepperManager.js)
                                Or 50060 est annule. Le refus ne porte donc NI sur
                                le compte NI sur la nature du module.
                                ➡ Et le module s'appelle GENERIC...StepperManager :
                                  c'est tres probablement LE MEME qui pilote
                                  l'assistant de la VENTE, dont 0.2 vient de
                                  prouver qu'il poste un formulaire ordinaire.
                                  Le verdict « module ES donc hors de portee »
                                  confondait deux choses : le module est la facon
                                  dont l'INTERFACE OUVRE l'assistant, pas la facon
                                  dont les DONNEES PARTENT.
                                ⏳ RESTE A EPROUVER SUR UN COMPROMIS **ACTIF**.
                                  Ni 24933 ni le bac a sable 62774 n'en portent ;
                                  les 9 211 actifs du parc sont de VRAIS dossiers
                                  clients. Ouvrir puis fermer est inerte (mesure :
                                  4 contre-temoins le 03/09), mais le choix du
                                  dossier revient a Frederic -- « l'utilisateur
                                  designe ».
l'OFFRE                         pas d'assistant ; formulaire + idOffre, non eprouve
supprimer la VENTE              ✅ FAIT le 03/09 -- 23294 supprimee, verbe
                                ventes-deleteVente EPROUVE (jamais vu passer avant).
                                Le bouton passe par window.confirm : une
                                automatisation ne peut pas y repondre.
la vente fait-elle REVIVRE le   ✅ REPONDU : NON. 50059 et 50060 restent annules.
compromis quand on la supprime ? Mais le STATUT redescend (Vendu -> Sous compromis),
                                et c'est HEKTOR qui le fait.
le SECOND ACQUEREUR             pourquoi un seul survit sur 50060
le MEME ACQUEREUR DEUX CYCLES   4 annonces multi-mandats : jamais regarde
```

### LES DONNEES DU PARC — mesurees le 03/09 sur 29 314 lignes

```
                              annonces concernees   dont plusieurs
   offres                          10 017              936   (8,8 %)
   compromis                        9 193              579   (5,5 %)
   ventes                           7 600                7   (0,07 %)
   plusieurs acquereurs                              2 314   (21,8 %)
   MULTI-COMPROMIS + MULTI-ACQUEREURS -- le cas de Frederic    521   (4,9 %)
   PLUSIEURS MANDATS -- la remise en vente                       4   (0,04 %)

   solidite du lien par acquereur      offres   compromis   ventes
      sans identifiant d'acquereur      0,1 %      2,8 %     1,0 %
      sans mandat exploitable          98,0 %     25,5 %    11,6 %
   ➡ le mandat ne peut pas servir de cle. L'acquereur, oui -- a 98,7 %.
```

---

## 2 quater. LES STATUTS — ce qui reste apres la cloture du protocole

Le protocole du 01/09 a repondu a sa question en cinq mesures. Restent deux points.

```
[x] 'supprimer' dans la redescente    ✅ MESURE LE 03/09, ET LA REGLE EST JUSTE.
    'refus' et 'annuler' en avaient ete retires apres mesure ; 'supprimer' restait,
    non par conviction mais pour comparer. La vente 23294 a ete supprimee :
        le statut redescend Vendu -> Sous compromis
        et c'est HEKTOR qui le fait (badge COMPROMIS, rail SOUS COMPROMIS)
        notre redescente calcule EXACTEMENT la meme chose -> aucun ecart
    ➡ On GARDE 'supprimer' dans la redescente. Et la regle des 7 mesures
      (« seule la creation fait bouger le statut ») a donc une EXCEPTION : la
      SUPPRESSION -- logique, elle retire l'objet qui justifiait le statut.

[ ] la sentinelle app_ecart_statut_regle : son SEUIL n a pas de sens.
    Mesure du 03/09 : 6 ecarts, tous REELS et tous expliques par le protocole
    -- 5 « remontees » (quelqu un a redescendu le statut a la main, la transaction
    vit toujours) et 1 « redescente » (offre refusee, personne n a remis en Actif,
    exactement le cycle 1).
    ➡ Ce n est pas une alerte a calibrer, c est une LISTE DE TRAVAIL : chaque ligne
      est un bien dont le statut ment. Sa place est peut-etre dans l app, pas dans
      le monitoring. A trancher par Frederic.
```

---

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
