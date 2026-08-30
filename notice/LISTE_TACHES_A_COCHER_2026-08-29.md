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
CONVERTIS (5)
[x] update_hektor_annonce_fields        app_edit_annonce_optimistic
[x] update_hektor_contact               app_edit_contact_optimistic
[x] update_hektor_contact_search        app_edit_search_optimistic
[x] change_hektor_annonce_status        ecrit l'affaire
[x] create_hektor_draft_annonce         ligne provisoire

A CONVERTIR (11)
[ ] archive_hektor_annonce              insert direct -- verifie
[ ] restore_hektor_annonce              insert direct -- verifie
[ ] delete_hektor_annonce
[ ] assign_hektor_annonce_negotiator    insert direct -- verifie
[ ] link_hektor_mandant                 insert direct -- verifie
[ ] delete_hektor_contact
[ ] add_hektor_contact_search
[ ] delete_hektor_contact_search
[ ] create_hektor_contact
[ ] create_hektor_mandant_contact
[ ] update_hektor_mandant_contact

LA BRANCHE MANQUANTE DU CHANGEMENT DE STATUT
[x] Actif · Offre · Compromis · Clos    14 executions depuis mai
[ ] VENDU                               JAMAIS EXECUTEE (0 sur 16)
```

## 2. C.19 — LES GESTES DE TRANSACTION *(finir)*

```
[x] refuser une offre      eprouve chez Hektor    33027 : bouton disparu, temoin intact
[x] accepter une offre     eprouve chez Hektor    33026
[ ] ANNULER un compromis                          JAMAIS EXECUTE
[ ] SUPPRIMER une vente                           JAMAIS EXECUTE
[ ] le RETOUR EN ARRIERE sur refus                JAMAIS TESTE -- garde-fou de l'instantane
[ ] redemarrer les workers                        2 correctifs en retard
[ ] deployer le front                             dernier commit c484c28
```

## 3. C.4-bis-0 — VÉRIFIER LA DÉTECTION *(préalable au filet)*

> **On ne rejoue pas ce qu'on ne sait pas raté.** Un travail marqué `done` n'est jamais
> repris : poser le filet avant la détection, c'est le tendre sous un trou qu'on ne voit pas.

```
[x] le defaut prouve par un essai       offre inexistante -> travail "done", etat faux affiche
[x] la cause relevee chez Hektor        "[]" = echec, "1" = succes -- il DIT quand il echoue
[x] le principe corrige sur mes 3 gestes  on EXIGE la preuve du succes
[ ] verifier les 18 handlers un par un  chacun exige-t-il une PREUVE, ou conclut-il du silence ?
                                        EN LISANT le code, pas par recherche de motif :
                                        cette methode m'a trompe QUATRE fois le 29/08
[ ] corriger ceux qui deduisent
```
*Constate au passage : `handleRelanceSignature` semble ne verifier que son message d'entree,
pas la reponse de Hektor. A confirmer. `handleUpdateHektorContactSearch`, lui, verifie bien --
ma premiere mesure le disait aveugle, elle etait fausse.*

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
| **C.19-c** | **le choix « laisser actif » / « archiver » a l'enregistrement d'une vente** | 🔴 **A FAIRE — juge tres important par Frederic** |

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
| **C.19-c** | 🟡 **mesuré, pas codé** — parcours d'archivage relevé en entier, matrice des trois cas établie. Reste à remonter les **deux décisions** jusqu'à l'écran |

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

## 2. C.19-c — le choix « actif / archivé » · 2 j

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
