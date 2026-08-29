# Audit — le plan de dev face à la réalité mesurée

*29/08/2026. Demandé par Frédéric : « le plan a dérivé et est devenu erroné à première vue ».*
*Méthode : les 117 notes de mars à août, les 12 retirées du git, le code, la base, et les
conversations des 28-29/08. **Tout ce qui est affirmé ici est mesuré.***

---

# AVERTISSEMENT DE MÉTHODE — je me suis trompé trois fois pendant cet audit

Et ça compte, parce que c'est exactement le défaut que l'audit cherche.

| | |
|---|---|
| **①** | J'ai cru que C.6 et B.4 n'étaient pas branchés au run. **Faux** : ils sont dans `run_descente.ps1` (07:30), pas dans le run principal. Je cherchais dans un seul fichier |
| **②** | J'ai cru que `--injecter` de 26bis était branché. **Faux** : c'était un commentaire |
| **③** | J'ai mesuré **deux fois** la conversion des 16 workers avec une heuristique de texte, et obtenu deux résultats faux *(« 10 sur 26 », puis « 0 sur 16 »)*. Il a fallu lire les définitions **côté serveur** pour obtenir le vrai chiffre |

> **Une mesure approximative vaut une mesure fausse.** Les chiffres ci-dessous sont ceux
> obtenus par lecture directe des définitions, jamais par recherche de motif.

---

# I. CE QUI EST VRAI — le plan tient sur l'essentiel

Vérifié un par un, sur la machine :

| | affirmé | mesuré |
|---|---|---|
| **0.1** sauvegarde des 2 tables clés | faite | ✅ présentes dans `backup_critical.py` |
| **0.4** accès public fermé | fait | ✅ `anon` retiré, `authenticated` seul |
| **0.6** table temporaire supprimée | fait | ✅ absente |
| **0.8** correctif sur les 3 balayages | fait | ✅ les 3 le portent |
| **B.1/B.2** la descente | 110 tables | ✅ **124 suivies, 92 remplies, 1 530 973 lignes** |
| **B.5** tâche planifiée | 07:30 | ✅ a tourné ce matin |
| **C.2b** identité des contacts | 355 687 | ✅ **355 769** |
| **C.7** contrat d'annonce | branché | ✅ dans le run |
| **C.13** magasin de mandat | posé | ✅ 4 lignes |
| **C.19** magasin d'affaire | posé | ✅ branché, éprouvé contre un vrai run |
| **26bis** annonces app-seules | 0 | ✅ 0, et `--injecter` reste débranché |

**Le socle est réel.** Ce n'est pas un plan qui raconte des choses ; c'est un plan dont les
tâches ont produit du code qui tourne.

---

# II. LES QUATRE DÉRIVES

## ① C.1' geste (c) — déclaré fait sur un périmètre plus étroit que son énoncé

C.1' portait **trois** gestes :

| a | une saisie dont l'envoi a échoué n'est jamais écrasée |
| b | l'échec est **visible** |
| **c** | **et il se reprend. Aujourd'hui il ne repart jamais** |

C.1' est **✅ FAIT le 24/08**. Mais son livrable ne cite que *« les 3 fonctions »* — les
**éditions de champs**. Le geste (c) n'a **jamais** couvert les actions.

**Mesure du 29/08 : 6 travaux en erreur, 0 rejoué.** Six types différents. `attempt_count`
reste à **1** partout. Un « Hektor 500 » du 28/08 n'a jamais été retenté, et personne ne l'a su.

> Ce n'est pas une erreur de conception. C'est **une case cochée sur la moitié de son énoncé**.

## ② C.4 — mesurée par ce qui tourne, pas par ce qui reste à convertir

C.4 est marquée **🟡 « terminé sauf la vente »**, sur la foi des **exécutions** *(127 archivages,
14 affectations)*.

Or son principe fondateur, écrit dans l'étude du 20/08, est *« **écrire d'abord**, envoyer,
comparer au retour »*, applicable *« entièrement »* aux 16 workers B1+B2.

**Mesure, lue dans les définitions serveur : 5 des 16 écrivent chez nous d'abord.**

```
   convertis (5)     update_hektor_annonce_fields      app_edit_annonce_optimistic
                     update_hektor_contact             app_edit_contact_optimistic
                     update_hektor_contact_search      app_edit_search_optimistic
                     change_hektor_annonce_status      ecrit l'affaire
                     create_hektor_draft_annonce       ligne provisoire

   NON convertis     archiver · desarchiver · supprimer une annonce
        (11)         affecter le negociateur · lier un mandant
                     supprimer un contact · ajouter/supprimer une recherche
                     creer un contact · creer un mandant · maj mandant
```

**Quand tu archives un bien, rien n'est écrit chez toi.** Le travail part, et tu attends.

## ③ La tâche 13 avait disparu du plan

Le patch d'identité des transactions du 20/08 renvoie explicitement à *« la tâche 13 (saisie
directe dans l'app) »*. La fiche **1.4** dit *« Débloque la modale de statut (tâche 13) »*. Le
moniteur la cite aussi.

Or la table de correspondance des anciens numéros donne ex-19, ex-23/24/25, ex-26, ex-29, ex-31
— **aucun ex-13**.

> **Un socle avait été posé pour une tâche qui n'existait plus.** Retrouvée le 28/08 sous le
> nom C.19, et faite depuis.

## ④ Le plan ne couvre pas tout le projet — et ne le dit pas

Comptage des mentions dans le plan :

```
   agenda / RDV          0-1     projet VALIDE (note du 31/07)
   espace proprietaire     0     plan ecrit le 23/06
   email rapprochement     0     Lot A fait, DKIM/DMARC bloquants
   Matterport              0     4 workers en production
   vitrine Android       0-1     note de reprise du 07/04
```

Le plan s'annonce comme *« établi après quatre audits »* — identifiants, workers, diffusion,
contacts. **C'est le plan du chantier d'indépendance**, pas la feuille de route du produit.

Ce n'est pas une erreur, mais **ça devient une erreur quand on l'appelle « plan de dev global »**
et qu'on y cherche ce qui n'y a jamais été.

---

# III. OÙ ON EN EST RÉELLEMENT

## Ce qui est fini et éprouvé

**La sécurité** *(0.4 à 0.8)* · **la descente** *(B.1 à B.5, 1,53 M de lignes)* · **l'identité**
des contacts, des transactions, des annonces · **le contrat d'autorité** sur trois familles
*(contact, mandat, affaire)* · **les six types d'offre** *(C.15)* · **le moniteur** ·
**la clôture de mandat chez nous** *(C.13)* · **les champs de transaction app-owned** *(C.19)*.

## Ce qui est ouvert, par ordre de dépendance

| | | |
|---|---|---|
| 🟡 **C.4** | la branche « Vendu », jamais exécutée · **et 11 workers à convertir** | 1 à 2 sem. |
| 🆕 **C.4-bis** | le filet de rejeu pour les actions *(geste c de C.1')* | 2 à 3 j |
| ⏳ **C.16** | 825 contacts actifs qui n'existent plus chez Hektor | 1 à 2 j |
| ⏳ **C.9** | la création part de l'app | 1 à 2 sem. |
| ⏳ **26bis-③** | collée à C.9 | 1 j |
| ⏳ **C.11** | ménage des tables mortes | court |
| 🏛 **A.3-technique** | le registre des mandats en propre | 3 à 5 j |
| ⏳ **D.1 → D.2** | rapatrier documents et photos | à chiffrer |

## Ce qui ne dépend pas du code

**A.1 les portails · A.2 la signature.** À zéro. **Aucun travail technique ne permet de couper
Hektor tant qu'ils ne sont pas réglés.**

---

# IV. LE PLAN PROPOSÉ — trois corrections de structure

## ① Renommer, pour cesser de chercher ce qui n'y est pas

`PLAN_DEV_ACTUALISE` → **`PLAN_INDEPENDANCE_HEKTOR`**, et poser à côté un
**`PLAN_PRODUIT`** qui recense les chantiers hors indépendance *(agenda RDV, espace
propriétaire, email rapprochement, vitrine, Matterport)*. Aujourd'hui ils ne vivent que dans
des notes, et rien ne dit s'ils sont finis.

## ② Une tâche n'est « faite » que si son ÉNONCÉ est couvert

C'est la leçon de C.1' et de C.4. Proposition : **toute tâche cochée porte la mesure qui le
prouve**, et cette mesure doit couvrir l'énoncé, pas un sous-ensemble.

*Le plan le fait déjà souvent — « 127 exécutions », « 0 incohérence ». Il faut que ce soit la
règle, et que la mesure réponde à la question posée par la tâche.*

## ③ Rouvrir les deux tâches à demi faites

- **C.1'** → son geste (c) devient **C.4-bis**, déjà consigné ;
- **C.4** → sa couverture réelle est **5 sur 16**, à écrire dans le plan.

---

*Sources : `PLAN_DEV_ACTUALISE_2026-08-20.md` · `ETUDE_WORKERS_EXISTANT_ET_FAISABILITE_2026-08-20`
· `ETUDE_FAISABILITE_DECOUPLAGE_HEKTOR_APP_FIRST_2026-08-08` (git) ·
`patch_identite_transactions_2026-08-20.sql` · définitions `pg_proc` lues en direct ·
`app_console_job` · `sb_pull_state` · `run_full_pipeline.ps1` · `scheduled/run_descente.ps1`.*
