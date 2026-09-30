# AUDIT EXPERT — OÙ EN EST L'AUTONOMIE VIS-À-VIS DE HEKTOR

**01/10/2026, 00h30.** Audit demandé par Frédéric : *« fais un audit expert et un
rapport complet, il faut tout vérifier en profondeur »*.

> **Tout ce qui suit est MESURÉ** — dans le code et dans les deux bases, le
> 30/09 au soir et le 01/10 à minuit. Aucun chiffre ne vient d'une note.
> Ce qui n'a pas été mesuré est **écrit comme tel**.

---

## 0. La réponse en une page

```
L'APP POSSEDE SA MEMOIRE       ████████████████████  ~95 %
L'APP SAIT AGIR SANS HEKTOR    ██████████████░░░░░░  ~70 %
L'APP EST SURVEILLEE           ████████████████░░░░  ~80 %
```

**Si Hektor s'arrêtait cette nuit**, l'agence garderait : ses 13 453 annonces
vivantes avec leurs 189 champs, ses 62 059 contacts, ses 132 628 liens, ses
31 017 affaires, ses 26 826 mandats, ses 436 886 photos — et pourrait continuer à
lire, chercher, rapprocher, estimer, éditer.

**Elle perdrait, le jour même** : le numéro de mandat *(PROTEXA)*, la signature
électronique *(abonnement Hektor)*, la diffusion portails *(contrats Hektor)*, et
la moitié de ses documents *(le rattrapage n'est qu'à 48 %)*.

---

## 1. LA GRILLE IMPOSÉE — objets × gestes

> Méthode CLAUDE.md §0 : *« un audit balaie les objets ET les gestes »*.
> ✅ = l'app écrit **d'abord chez elle** une ligne durable, puis Hektor suit ·
> 🟡 = ça marche, mais l'app ne garde rien avant la réponse de Hektor ·
> ⛔ = le geste n'existe pas · — = sans objet

| | créer | modifier | supprimer / archiver | lire / remonter |
|---|---|---|---|---|
| **annonce** | ✅ | ✅ | 🟡 *(volontaire)* | ✅ |
| **contact** | ✅ | ✅ | 🟡 *(volontaire)* | ✅ |
| **recherche** | ✅ | ✅ | 🟡 *(volontaire)* | ✅ |
| **relation** *(mandant)* | ✅ *(30/09)* | ⛔ | ⛔ **« retirer un mandant » n'existe nulle part** | ✅ |
| **transaction** | ✅ | ✅ | ✅ | ✅ |
| **mandat** | ✅ *(30/09)* | ⛔ **on sait créer, pas corriger** | 🟡 clôture | ✅ |
| **document** | 🟡 | — | 🟡 | 🟡 **48 % seulement** |
| **photo** | 🟡 | ⛔ *(ordonner, supprimer)* | ⛔ | ✅ |
| **diffusion** | ✅ *(sans worker)* | ✅ | ✅ | ⛔ **figée jusqu'au run** |
| **RDV / visite** | 🟡 | **non mesuré** | **non mesuré** | 🟡 *2 235 liens publics, 11 liens agenda* |

### Ce que la grille dit, et qu'aucun total ne dirait

- **Les trois piliers** *(annonce, contact, recherche)* sont **complets**, y compris
  la file d'attente qui retient la saisie si Hektor ne répond pas.
- **Les suppressions sont 🟡 par décision**, pas par oubli *(arbitrage du 30/08)* :
  on ne veut pas qu'une suppression vive dans l'app avant que Hektor l'ait actée.
- **Trois trous réels** : *retirer un mandant* · *corriger un mandat* · *les photos*.
- **Le RDV est la zone la moins mesurée du projet.** Je l'écris au lieu de la sauter.

---

## 2. LES GESTES DU WORKER — 36 exercés, et ils passent

```
36 genres de travaux ont REELLEMENT tourne en production
67 610 travaux au total   ·   0 erreur, sauf 2 sur refresh_console_data
2 689 en attente          ·   TOUS du rattrapage documents (voulu)
```

**Aucun geste bloqué. Aucune file en souffrance.** Le mécanisme worker est sain.

⚠ **Jamais exercés** : les 4 `matterport_*` et `archive_cloud_documents`. Ce
n'est pas une panne — personne ne les a déclenchés. **Non éprouvés en réel.**

---

## 3. LA CHAÎNE OPTIMISTE — 71 RPC appelées par le front

```
71 RPC appelees depuis le front   ·   16 sont des `*_optimistic`
AUCUNE insertion directe dans app_console_job   <- la porte est unique
```

**Les 16 gestes qui écrivent chez nous d'abord :**

```
annonce      creer · editer · statut · archiver · restaurer · affecter nego
contact      creer · editer · creer-mandant · editer-mandant
recherche    creer · editer · editer-espace
relation     lier un mandant                          (30/09)
transaction  geste · modifier · editer
```

**Les gestes SANS ligne durable préalable, et pourquoi :**

| geste | raison |
|---|---|
| supprimer annonce / contact / recherche | **décision du 30/08** — assumée |
| envoyer un document / une photo | le fichier part au serveur, **rien n'est inscrit avant** |
| numéro de mandat | **PROTEXA décide** — décision de Frédéric du 29/09 |
| diffusion portails | passe par l'**API Hektor**, pas par un travail |

---

## 4. LA MÉMOIRE — ce que l'app possède en propre

| objet | tables | lignes (cloud) | verdict |
|---|---|---|---|
| photo | 1 | **436 886** | ✅ + coffre public, dérivés, delete-never |
| relation | 2 | **132 628** | ✅ *(30/09)* les QUATRE numéros |
| contact | 13 + 7 vues | **62 059** | ✅ |
| document | 2 | **53 315** | ⛔ **48 % des annonces seulement** |
| transaction | 9 + 1 | **31 017** | ✅ |
| mandat | 4 + 2 | **26 826** | ✅ *(30/09)* |
| annonce | 16 + 5 | **13 453** vivantes | ✅ 189/189 champs |
| recherche | 5 + 2 | 10 282 | ✅ |
| RDV | 5 + 2 | 2 235 + 11 | 🟡 |
| diffusion | 4 + 1 | 1 388 | ⛔ contenu du 07/07 |

### ⛔⛔ LE RISQUE LE PLUS LOURD DE TOUT L'AUDIT — et il n'est dans aucun plan

**`data/hektor.sqlite` (3,9 Go) n'a AUCUNE sauvegarde. Pas une seule, jamais.**

Vérifié en regardant le dossier `C:\Hektor\Backups` lui-même, pas le code :

```
critical/   quotidien     32 Mo/jour, dernier le 30/09   ✅ tourne
phase2/     hebdomadaire  597 Mo,     dernier le 27/09   ✅ tourne
documents/  desactive le 18/08                            (assume)
hektor.sqlite (3,9 Go)    AUCUN FICHIER, AUCUNE DATE     ⛔⛔
```

`run_backup.ps1` passe `--weekly` (ligne 41) et **jamais `--full`** — or le
niveau 4, seul à copier le miroir, est marqué *« sur demande »*. Personne ne l'a
jamais demandé.

**Ce que ce fichier est seul à porter, mesuré :**

```
34 520 annonces ARCHIVEES avec leur detail complet
       -> phase2 n'en garde qu'un INDEX de 35 colonnes (35 305 + 8 924)
       -> le « cache de detail » de phase2 contient SEPT lignes
470 037 reponses brutes de l'API Hektor
       -> c'est la matiere qui permet de TOUT refabriquer
```

**Un disque qui lâche, et vingt ans d'archives de l'agence disparaissent** — avec
la seule matière qui permettrait de les reconstruire. Aucune sentinelle, aucune
ligne de plan ne le dit.

---

## 5. LES GARDES — 35 + 5, et une faille

```
35 sentinelles dans check_gti_health.py
 5 controles phase2 branches : annonce_un_numero · mandat_disparu ·
   mandat_un_numero · relation_disparue · comparer_doublures
```

**Couverture par objet :** contact 11 · annonce 5 · recherche 6 · mandat 2 ·
relation 1 · transaction 2 · diffusion 1 · **document 0** · **photo 0** ·
**RDV 0**.

### ⛔ DEUX FAILLES TROUVÉES PAR CET AUDIT

**① Une saisie attend depuis 8 jours, et aucune garde ne le dit.**

```
app_search_pending : 1 ligne, du 23/09 18h39
   push_search = NULL   push_attempts = 0   conflict = false
```

La sentinelle `data.recherche_push_bloque` ne se déclenche qu'à
`push_attempts >= 3`. **Une ligne jamais tentée est invisible pour toujours.**
Cela contredit le principe du projet : *« une saisie ne se perd jamais »*.

**② La garde de diffusion lisait une table figée.**

`data.diffusion_erreur` lit `has_diffusion_error`, dérivé d'une table gelée
depuis le 7 juillet. **Sa valeur ne pouvait pas bouger, donc elle ne pouvait pas
rougir.** *(Corrigé le 30/09 côté données ; la garde reste à repenser.)*

> **Une garde dont l'entrée est figée, ou dont le seuil exclut le cas réel,
> n'est pas une garde.**

---

## 6. LES EXCEPTIONS — et une révision importante

Le plan en annonçait **trois**. La mesure du 30/09 en ramène **deux**.

| | état réel |
|---|---|
| **le numéro de mandat** *(L9)* | ⛔ **vraie exception.** PROTEXA fabrique le numéro. Décision de Frédéric du 29/09 : le registre électronique légal est **le dernier temps** *(juriste + horodatage tiers)*. |
| **la signature** *(A.2)* | ⛔ **vraie exception.** ImmoSign est un **abonnement Hektor** ; le jeton se lit dans une iframe Hektor. Rien ne peut le remplacer sans un contrat à nous. |
| ~~**les passerelles**~~ *(A.1)* | ⭐ **CE N'EST PAS UNE EXCEPTION TECHNIQUE.** Hektor expose une **vraie API d'écriture** *(`PUT addAnnonceToPasserelle`, `DELETE remove`)*. L'app s'en sert **déjà**, sans worker. La dépendance qui reste est **commerciale** : les contrats LeBonCoin / BienIci appartiennent à l'abonnement Hektor. |

⭐ **Pourquoi la nuance compte** : on croyait devoir *construire* l'autonomie
portails. Elle est **déjà là**. Ce qui reste à obtenir n'est pas du code, ce sont
**des contrats de diffusion au nom de GTI**.

---

## 7. CE QUI RESTE AVANT LA COUPURE — chiffré

```
⛔ BLOQUANT
   les documents          31 842 annonces non scannees (48 % faits)
                          ~10,6 nuits au rythme actuel, tourne seul
   la sauvegarde --full   le detail des 34 515 archives n'a qu'UN exemplaire
                          -> a trancher : l'ajouter, ou confirmer l'agent OVH

⚠ GESTES MANQUANTS (L5) -- 6-10 j
   corriger un mandat     type, dates, montant, mandants : aucun ecran
                          (l'avenant ne sait changer QUE le prix)
   retirer un mandant     n'existe nulle part -- un ecran a dessiner
   les photos             supprimer, reordonner
   fusion de doublons

⚠ FIABILITE
   la file bloquee        1 saisie perdue depuis 8 jours, invisible
   les gardes manquantes  document 0 · photo 0 · RDV 0
   l'etat de diffusion    l'app enregistre le SOUHAIT, pas la CONFIRMATION
                          (correctif = 1 ligne, la bonne version dort a cote)

⏳ DATES DE PEREMPTION -- a faire AVANT, pas pendant
   C.9-couple             1 h de mesure, exige d'ecrire chez Hektor
   les liens publics      QR et imprimes portent le n° Hektor (section 11bis)

⛔ HORS CODE
   registre electronique legal   juriste + horodatage tiers (~3-4 sem)
   contrats de diffusion         LeBonCoin / BienIci au nom de GTI
```

---

## 8. CE QUE CET AUDIT A TROUVÉ ET QUI N'ÉTAIT NULLE PART

```
① une saisie de recherche bloquee depuis 8 jours, INVISIBLE des gardes
② la base miroir (3,9 Go) n'a AUCUNE sauvegarde -- 34 520 archives
   et 470 037 reponses brutes tiennent sur un seul disque
③ les passerelles ne sont PAS une exception technique -- l'API existe
④ document / photo / RDV : ZERO sentinelle
⑤ 5 genres de travaux worker jamais exerces en reel
⑥ le RDV est la zone la moins mesuree du projet
```

---

## 9. L'ORDRE QUE JE RECOMMANDE

```
1. LA SAUVEGARDE --full      ⛔⛔ ZERO copie de 3,9 Go -- c'est LE risque du projet
2. la file bloquee           1 ligne, mais le principe est en cause
3. les gardes document/photo elles manquent la ou le volume est le plus gros
4. L5, les 4 gestes          6-10 j, et ils ferment la grille
5. les dates de peremption   C.9-couple, les liens publics
6. les documents             tournent seuls, ~10,6 nuits
```

> **Le code n'est plus le frein.** Ce qui reste est : **une sauvegarde qui n'existe pas**, **quatre gestes à écrire**, **trois gardes à poser** — et deux
> choses qui ne dépendent pas de moi : un juriste, et des contrats de diffusion.
