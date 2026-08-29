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
