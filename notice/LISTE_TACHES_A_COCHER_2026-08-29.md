# La liste — ce qui est fait, ce qui ne l'est pas, item par item

*Posée le 29/08/2026, à la demande de Frédéric : le plan explique très bien le **pourquoi**,
mais n'a jamais listé le **quoi**. 1 700 lignes, 0 case à cocher, 0 nom de worker — alors que
C.4 en couvre 16.*

> **RÈGLE** *(plan, 29/08)* : une tâche n'est cochée que si son **énoncé** est couvert, et la
> mesure qui le prouve doit répondre à la question que la tâche posait.

**Légende** — `[x]` fait ET vérifié · `[~]` fait, pas encore éprouvé en vrai · `[ ]` à faire

---

## C.19 — LES CHAMPS ET GESTES DE TRANSACTION *(ex-tâche 13, retrouvée le 28/08)*

### Étape 1 — le magasin
```
[x] table app_affaire_champ_app dans Supabase        RLS fermee, service_role seul
[x] table locale + magasin_affaire_app.py            branche au run de nuit
[x] cle sur app_affaire_id, pas le numero Hektor     29 293 numeros, 0 manquant
[x] eprouve de bout en bout                          affaire 3, 123 456 vs 75 000
```

### Étape 2 — la règle
```
[x] CHAMPS_APP_AFFAIRE dans le contrat d'autorite    10 champs
[x] appliquer_contrat_affaire.py                     pose ledger + vue
[x] branche au run, APRES affaire_ledger.py          defaut d'ordre trouve et corrige
[x] repose ses corrections dans Supabase             ecriture bornee aux affaires corrigees
[x] EPROUVE CONTRE UN VRAI RUN                       journal du 29/08, 06:19:47
```

### Étape 3 — l'écran
```
[x] RPC app_edit_affaire_optimistic                  gardes eprouves
[x] anon retire de la RPC                            trouve pendant l'audit
[x] loadAffairesForDossier                           lit toutes les affaires d'un bien
[x] bouton "Corriger sans envoyer a Hektor"          dans la modale
[x] pre-remplissage par les valeurs REELLES          sinon "Corriger" ecrasait la vraie date
[ ] DEPLOYE SUR VERCEL                               a confirmer par Frederic
```

### Étape 4 — les trois gestes
```
[x] les appels releves sur l'ecran de Hektor         updateOffre / clotureCompromis / deleteVente
[x] conformite exacte aux appels reels               isCloture vaut TOUJOURS 1, fromContact ajoute
[x] les 3 types dans la contrainte Supabase
[x] les 3 types dans ADMIN_JOB_TYPES                 worker
[x] les 3 types dans app_console_claim_next_job      seconde liste, oubliee d'abord
[x] relecture apres ecriture                         comme les 13 autres handlers
[x] RPC app_geste_affaire_optimistic                 instantane + etat precedent
[x] retour en arriere si Hektor refuse               code pose
[x] anon retire de la RPC

[x] REFUSER une offre    eprouve chez Hektor         offre 33027, bouton disparu, temoin intact
[x] ACCEPTER une offre   eprouve chez Hektor         offre 33026
[ ] ANNULER un compromis                             JAMAIS EXECUTE -- cible a choisir ensemble
[ ] SUPPRIMER une vente                              JAMAIS EXECUTE -- definitif, en dernier
[ ] le RETOUR EN ARRIERE sur refus                   JAMAIS TESTE -- c'est le garde-fou de
                                                     l'instantane, le plus important des trois
[ ] REDEMARRER LES WORKERS                           ils tournent 2 correctifs en retard :
                                                     ni le reflet d'etat, ni l'instantane
[ ] trace d'essai a retirer                          affaire 9 : 123 456 au lieu de 79 000
                                                     (decision de Frederic : en fin de chantier)
```

---

## C.4 — LES 16 WORKERS *(couverture réelle : 5 sur 16)*

### Le principe : « écrire d'abord, envoyer, comparer au retour »

```
CONVERTIS (5)
[x] update_hektor_annonce_fields          app_edit_annonce_optimistic
[x] update_hektor_contact                 app_edit_contact_optimistic
[x] update_hektor_contact_search          app_edit_search_optimistic
[x] change_hektor_annonce_status          ecrit l'affaire
[x] create_hektor_draft_annonce           ligne provisoire

A CONVERTIR (11)
[ ] archive_hektor_annonce                insert direct -- verifie
[ ] restore_hektor_annonce                insert direct -- verifie
[ ] delete_hektor_annonce
[ ] assign_hektor_annonce_negotiator      insert direct -- verifie
[ ] link_hektor_mandant                   insert direct -- verifie
[ ] delete_hektor_contact
[ ] add_hektor_contact_search
[ ] delete_hektor_contact_search
[ ] create_hektor_contact
[ ] create_hektor_mandant_contact
[ ] update_hektor_mandant_contact
```

### Les branches de `change_hektor_annonce_status`
```
[x] Actif · Offre · Compromis · Clos                 14 executions depuis mai
[ ] VENDU                                            JAMAIS EXECUTEE (0 sur 16)
                                                     debloquee par C.13 et C.19
```

*Les 3 workers B3 — numéro de mandat auto, relance et annulation de signature — sont hors C.4 :
ce sont exactement A.1 et A.2.*

---

## C.4-bis — LE FILET DE REJEU DES ACTIONS *(geste (c) de C.1', rouvert)*

```
[x] le defaut mesure                       6 travaux en erreur, 0 rejoue, tentatives=1 partout
[ ] file app_affaire_pending               sur le modele des 3 autres
[ ] balayage a la minute                   rejeu 5 / 10 / 15 / 20 / 25 min
[ ] abandon a 5 tentatives -> conflict     un humain tranche
[ ] bandeau sur la fiche
[ ] perimetre : les 3 gestes + le changement de statut
```

---

## CE QUI A ÉTÉ FAIT LES 28-29/08, HORS C.19

```
[x] C.15   les 6 types d'offre + immo pro            61 093 miroir / 61 094 serveur
[x] C.18   bug agence multi-agences                  3 occurrences depuis juin, corrige
[x] C.17-bis  le moniteur ne meurt plus en parlant
[x] C.13-a magasin de mandat                         3 divergences observees
[x] C.13-b contrat de mandat                         premier champ app-owned jamais inscrit
[x] C.13   statut et cloture decouples               Hektor n'apprend plus la cloture
[x] C.13   la cloture ecrivait dans le vide          corrige, eprouve (ce57749)
[x] 26bis  la carte des 163 colonnes                 139 detenues, 2 vraiment absentes
[x] C.16   remesuree                                 825 fiches, pas 284 269
[x] A.3-technique consignee                          3 couches de numerotation
[x] l'analyse des transactions de bout en bout        29 293, multiplicite normale
[x] l'audit du plan                                   4 derives trouvees
[x] la regle du "fait" posee dans le plan
[x] C.1' rouverte, C.4 corrigee, ordre revu
[x] le correctif anon consigne dans un fichier        il manquait
```

---

## LES CINQ GESTES QUI T'APPARTIENNENT

```
[ ] redemarrer les workers                 2 correctifs en retard
[ ] deployer le front sur Vercel           dernier commit : c484c28
[ ] choisir l'annonce pour "Vendu"          la vente sera definitive
[ ] choisir le compromis a annuler          tous les actifs sont de vraies affaires
[ ] 0.3 finir 19-R1                        le rattrapage acquereurs, 4 h 35
```

---

*Cette liste se tient à jour en même temps que le plan. Une case ne se coche que sur une mesure,
et la mesure est écrite à côté.*
