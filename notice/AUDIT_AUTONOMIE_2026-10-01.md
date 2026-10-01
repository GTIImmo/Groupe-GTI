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

### ✅ LA SAUVEGARDE — j'avais tiré une alarme FAUSSE, Frédéric m'a fait revérifier

**Ma première conclusion était : « `hektor.sqlite` (3,9 Go) n'a aucune
sauvegarde ». C'EST FAUX.** Je n'avais regardé que `backup_critical.py` et le
dossier `C:\Hektor\Backups`. Il existe un second mécanisme, et il couvre tout.

```
VEEAM AGENT -> OVH CLOUD          vspc-cgw31.prod01.eu-west-rbx.backup.ovhcloud.com
   Backup mode: entire computer   ExcludeMasks : <vide>, aucune exclusion
   30/09 22:23  status: Success   894,5 Go / 894,5 Go
   retention 14 jours             snapshot VSS actif
```

**La machine entière part chaque nuit.** `data/hektor.sqlite` est dedans. La
question ouverte du plan — *« à trancher : l'ajouter à --full, ou confirmer que
l'agent OVH le prend »* — **a sa réponse : l'agent le prend.**

**Les deux mécanismes sont complémentaires, et le partage est cohérent :**

```
backup_critical.py   18 tables NON re-telechargeables, chaque jour 08:15, 32 Mo
                     + instantane phase2 hebdomadaire (597 Mo, dernier 27/09)
                     -> restauration CHIRURGICALE, granularite table
Veeam / OVH          la machine entiere, chaque nuit 22:00, 14 jours
                     -> restauration COMPLETE, granularite machine
```

**Ce qui reste vrai, et qui est plus petit mais réel :**

```
⚠ 14 JOURS DE RETENTION      une corruption decouverte au-dela est irrecuperable
⚠ AUCUNE RESTAURATION TESTEE  ni Veeam ni backup_critical n'ont jamais ete
                              eprouves en restauration. Une sauvegarde jamais
                              restauree est une sauvegarde supposee.
⚠ app_relation ET app_mandat  les deux registres nes le 30/09 ne sont PAS dans
                              CRITICAL_TABLES -- couverts seulement par l'hebdo
                              et Veeam, donc jusqu'a 7 jours d'exposition sur le
                              chemin chirurgical. C'est exactement le raisonnement
                              qui avait fait ajouter app_affaire_ledger en aout.
```

➡ **Leçon pour moi, et c'est la sixième fois aujourd'hui** : j'ai conclu sur
**une** source *(le script de sauvegarde)* sans chercher s'il en existait une
autre. « Il n'y a pas de sauvegarde » et « je n'ai pas trouvé de sauvegarde » ne
sont pas la même phrase.

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
② app_relation et app_mandat absents de la liste de sauvegarde quotidienne
   (la sauvegarde globale existe : Veeam -> OVH, machine entiere, verifie)
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

> **Le code n'est plus le frein.** Ce qui reste est : **une restauration jamais éprouvée**, **quatre gestes à écrire**, **trois gardes à poser** — et deux
> choses qui ne dépendent pas de moi : un juriste, et des contrats de diffusion.

---

# 10. LES CONTRÔLES PASSÉS EN RÉEL — 01/10, 00h30

*Tous lancés, aucun supposé.*

## Les quatre sentinelles de fond : **vertes**

```
mandat_un_numero     deux_numeros 0 · croisements 0 · absents 0 · plage 0
annonce_un_numero    deux_numeros 0 · croisements 0 · inconnus 0 · plage 0
mandat_disparu       0 absents sur 24 909
relation_disparue    doublons 0 · hors plage 0 · plage envahie 0
```

## Les 7 tâches planifiées : **toutes à 0**

```
GTI Quotidien             30/09 05:00   0     prochaine 01/10 05:00
GTI Descente              30/09 07:30   0
GTI Recherches Actives    30/09 03:00   0
GTI Rattrapage Documents  30/09 23:00   0
GTI Sauvegarde            30/09 08:15   0
GTI Relances Email        01/10 00:00   0
GTI Health Monitor        30/09 23:48   0     toutes les 2 h
```

## L'état de santé réel : **1 critique, 5 alertes**

```
⛔ data.travaux_en_erreur        2 (seuil 0)   -- ROUGE DEPUIS LE 28/09
⚠ cron app_contact_push_due     dernier run en echec
⚠ data.ecart_statut_regle       6 (seuil 4)
⚠ data.notif_non_lues           1 433 (seuil 300)
⚠ data.notif_orphelines         148 (seuil 20)
⚠ data.orphelins_recherche      1 (seuil 0)
⚠ data.recherche_disparue       1 (seuil 0)
```

---

# 11. TROIS INCIDENTS RÉELS, NOMMÉS

## ① Une saisie de négociateur perdue depuis le 23/09 — **huit jours**

```
contact 10355711 · recherche Firminy, appartement
   dans l'app     prix_max = 255 000
   chez Hektor    l'ancienne valeur
   app_search_pending : push_search = NULL, push_attempts = 0
```

**Et ce n'est pas un trou de surveillance — c'est un trou de LECTURE.** Trois
gardes en voient chacune une facette, aucune ne nomme l'incident :

```
data.recherche_divergente    critical, seuil 0   -> la voit
data.recherche_disparue      warning, 1          -> la voit
data.orphelins_recherche     warning, 1          -> la voit
data.recherche_push_bloque   ne se declenche qu'a push_attempts >= 3
                             -> une ligne JAMAIS TENTEE lui est invisible
```

⚠ **Et la mémoire du projet explique pourquoi personne n'a réagi** :
`recherche_divergente` est connue pour crier faux entre le run de nuit et la
Descente de 07:30. **Le bruit d'une garde a masqué une vraie perte.**

## ② Deux travaux en erreur depuis le 28/09 — l'alarme critique

```
refresh_console_data sur les annonces 63157 (BRIOUDE) et 54673 (COURPIERE)
   sqlite3.OperationalError: database is locked
   dans bootstrap_phase2.ensure_schema, appele par push_single_annonce
```

L'appelant pose pourtant `timeout=30` : **le verrou a donc tenu plus de 30
secondes**, à 08:54 le 28/09. *(L'écrivain qui le tenait n'est pas identifié —
non mesuré.)*

✅ **Conséquence limitée** : les deux annonces sont bien dans Supabase, actives.
Le run de nuit les a rattrapées. **Mais l'alarme reste rouge trois jours après**,
parce qu'un travail en erreur n'est jamais rejoué *(règle assumée)* et que rien
ne l'éteint.

## ③ Une sentinelle compare la mauvaise paire

`relation_disparue` affiche « retard du cloud : 82 392 ». Elle compare le
registre **neuf** (`app_relation`, 132 628) à la doublure de l'**ancienne** table
(`app_contact_relation_current__sb`). La doublure `app_relation__sb` n'existe pas
encore côté serveur — elle descendra au prochain run.

C'est marqué *« information, jamais une alerte »*, donc rien ne casse. **Mais le
chiffre est faux et personne ne peut le savoir en le lisant.**


---

# 12. ⛔ CORRECTIONS — RDV, PHOTOS, DOCUMENTS

**Frédéric m'a arrêté : « tu te trompes pour le RDV, l'adresse n'est pas la
bonne, vérifie mes codes, mon historique ».** Il avait raison. Trois fois.

## ① LE RDV FONCTIONNE — j'avais testé la mauvaise adresse

J'ai testé `groupe-gti.vercel.app/rdv/annonce/{token}` et conclu « 404, la page
n'existe pas ». **La vraie adresse est ailleurs, et elle est écrite dans le
projet depuis le 25/09 :**

```
https://gtiimmo.github.io/vitrine/rdv/index.html?ref=<hektor_annonce_id>
   un site STATIQUE dedie : apps/rdv-public/ (index, estimation, app.js, styles)
   publie sur GITHUB PAGES, depot GTIImmo/vitrine
   ⚠ le parametre est ?ref= , PAS un segment de chemin
```

**Éprouvé en vrai, page ouverte le 01/10 :** elle charge le bien *(Appartement,
50 000 €, réf. 63158)*, l'agence, le négociateur *(Mélanie LEGRAND, tél, mail)*,
**le calendrier d'octobre avec ses créneaux**, la fiche contact, les quatre
actions *(Visiter · Télécharger · Contacter · Estimer)*. Assets 200, aucune
erreur bloquante.

**Et la chaîne a produit de vrais rendez-vous :**

```
82 emails de rapprochement envoyes (80 reels) · 29 ouverts · 6 cliques
2 RENDEZ-VOUS PRIS          dernier envoi le 24/07
```

➡ **Ce que je prenais pour une panne était une adresse que je n'avais pas
cherchée.** J'avais dans les mains l'audit du 25/09 qui donne l'URL exacte, et
je ne l'ai ouvert qu'après m'être trompé. **`notice/` avant le navigateur.**

**Ce qui reste vrai sur le RDV — et c'est son propre audit qui le dit :**

```
⏳ le `ref` est le NUMERO HEKTOR, pas le jeton
   -> a la coupure, TOUS les QR et affiches deja imprimes meurent
   -> le jeton existe deja pour les 2 235 liens : il suffit de l'exporter
   (point ① de notice/AUDIT_VITRINE_ET_RDV_2026-09-25.md, toujours ouvert)
⏳ la fiche visite PDF pointe sur admin/pdf.php de HEKTOR -> meurt aussi
⚠ app_appointment_request = 0 alors que 2 RDV ont ete pris par email
   -> les deux chemins ne partagent peut-etre pas la meme table. NON MESURE.
```

ℹ **Une piste écartée, et c'est une bonne nouvelle** : 12 agences affichent la
boîte mail d'une autre *(Saint-Étienne → firminy@, Issoire → brioude@…)*. Ce
n'est **pas** un défaut : les paires sont **exactement** les 8 regroupements
d'agences des anciennes passerelles. Une boîte et un téléphone par binôme —
c'est l'organisation réelle du réseau, et c'est pourquoi Hektor avait groupé ses
passerelles ainsi.

## ② LES DOCUMENTS — mon « 48 % » était trompeur

```
PARC VIVANT           20 162 / 20 345 documents au coffre   = 99,1 %  ✅
                      13 059 / 13 453 annonces scannees     = 97,1 %  ✅
HORS PARC (archives)   1 796 / 33 583                        =  5,3 %
```

**Le 48 % mélangeait le parc et les archives.** Or la règle du projet est
explicite : *« serveur = tout / cloud = biens vivants »*. Les archives **ne
doivent pas** monter au cloud. **Le périmètre qui compte est à 99 %.**

```
⬜ 394 annonces du parc pas encore scannees
⬜ le rattrapage des ARCHIVES continue, ~10,6 nuits, tourne seul
⛔ ZERO sentinelle document dans check_gti_health
```

## ③ LES PHOTOS — le parc vivant est complet

```
10 229 / 13 453 annonces du parc ont des photos
74 786 / 74 786 de leurs photos ont leurs derives   = 100 %  ✅
derives entretenus par le run (dernier : 30/09 05:08)
coffre public EPROUVE en vrai : w400.jpg servi, 400x534
```

```
⛔ la sonde photo tourne DANS LE RUN mais n'est branchee sur AUCUNE alerte
   (check_photo_listing_push.py n'est pas dans check_gti_health)
   -> si elle rougit, seul le journal le sait
⬜ gestes manquants : supprimer une photo, reordonner
⬜ 3 224 annonces du parc sans aucune photo -- NON MESURE si c'est normal
```

## ⚠ Ce que ces trois corrections m'apprennent

**Sept fois en 24 h j'ai conclu sur une source incomplète.** Le motif est
toujours le même : *j'ai mesuré ce que j'avais sous la main, pas ce que l'écran
ou le client voit réellement.*

```
la sauvegarde     j'ai lu le script, pas les services de la machine
le RDV            j'ai teste une URL que j'avais deduite, pas celle du projet
les documents     j'ai divise par le total, sans separer parc et archives
```

➡ **Avant de déclarer une panne : ouvrir `notice/`, et tester l'adresse RÉELLE.**

---

# 13. `app_contact_relation_current` — LA RÉPONSE CERTAINE

**01/10/2026.** J'avais annoncé : *« elle est déjà remplacée, 85 173 lignes poussées
pour rien — le gain le plus facile du projet »*. **C'était faux.** Frédéric a
demandé une vérification à fond, puis une réponse **certaine**. La voici.

## La méthode : on ne cherche pas où l'on pense

Balayage de **toutes** les couches, y compris celles que je n'avais pas ouvertes :
vues · fonctions · **politiques RLS** · déclencheurs · worker · backend · phase2 ·
front · tâches planifiées.

## Les lecteurs, tous, et ce qu'ils risquent

| # | lecteur | ce qu'il fait | si les liens disparaissent |
|---|---|---|---|
| **1** | **politique RLS** `app_contact_current_select_scoped` | **qui peut VOIR un contact** | ⛔⛔ un négociateur **ne voit plus** les propriétaires de ses propres biens |
| **2** | fonction `app_console_can_request_contact_job` | **qui peut AGIR sur un contact** | ⛔⛔ il **perd le droit** de modifier ces contacts |
| **3** | worker `console_job_worker.js` l. 2107 | retrouve les biens d'un contact (5 max) | ⛔ le geste se fait sans contexte |
| **4** | vue `app_contact_relations_current` | **les ACQUÉREURS** (ce que l'écran affiche) | ⛔ 34 926 liens disparaissent de l'écran |
| 5 | worker `cleanupSupabaseAnnonceRows` | ménage à la suppression d'une annonce | 🟡 sans objet |
| 6 | fonction `app_contact_id_propager` | propage notre numéro sur 18 tables, **chaque nuit** | 🟡 générique |
| 7 | fonction `app_decaler_doublure` | décale la doublure sur une liste de tables | 🟡 générique |
| 8 | fonctions `app_bascule_identite_contact` (+ annuler) | la bascule d'identité | 🟡 ponctuelle, faite |
| 9 | vue `app_contacts_sans_numero` | diagnostic sur 18 tables | 🟡 |
| — | `contact_sync_status` · `relation_disparue` · `photo_avant_c15` · `comparer_doublures` | contrôles phase2 | 🟡 |
| ✅ | **le front** | **ne l'interroge JAMAIS en direct** | — les 2 occurrences du code sont des **commentaires** |

## La politique RLS, mot pour mot

```sql
-- QUI PEUT VOIR UN CONTACT
   is_app_global_reader()                                   OU
   can_access_negotiator_email(negociateur_email)           OU
   EXISTS (SELECT 1 FROM app_contact_relation_current r
           WHERE r.hektor_contact_id = app_contact_current.hektor_contact_id
             AND r.app_dossier_id IS NOT NULL
             AND can_access_current_dossier(r.app_dossier_id))
```

**Ce sont exactement les 50 247 liens mandant/propriétaire que je proposais de ne
plus pousser.** Les retirer aurait coupé la visibilité des négociateurs sur les
propriétaires de leurs biens — **silencieusement**, et ça aurait ressemblé à un
bug de droits, jamais à une régression de push.

## Le verdict

```
85 173 lignes poussees chaque nuit
   34 926 acquereurs       -> SERVIS par la vue du front
   50 247 mandant/proprio  -> SERVIS par les DROITS (voir + agir)
----------------------------------------------------------------
        0 ligne inutile
```

**Il n'y a aucun gain gratuit ici.** Il y a un chemin, en trois temps, et chacun
doit être prouvé avant le suivant :

```
1. la politique RLS et le garde-fou lisent app_relation au lieu de la vieille
   table. Le registre porte les MEMES liens, avec le MEME app_dossier_id.
   ⚠ la cle n'est pas la meme : la vieille table met NOTRE numero dans une
     colonne nommee `hektor_contact_id` ; app_relation a `app_contact_id`.
2. le worker (l. 2107) fait de meme.
3. ALORS SEULEMENT la vieille table se reduit aux acquereurs : 85 173 -> 34 926.
   Et elle ne disparait pas : les ACQUEREURS n'ont pas encore de registre.
```

## ⚠ La leçon, et c'est la troisième fois dans la même journée

```
la sauvegarde   « aucune sauvegarde »  -> Veeam sauvegardait la machine entiere
le RDV          « la page n'existe pas » -> elle etait a une adresse que je
                                            n'avais pas cherchee
cette table     « plus personne ne la lit » -> deux politiques de DROITS en vivent
```

➡ **Avant de déclarer qu'une donnée ne sert plus : chercher TOUS ses lecteurs —
vues, fonctions, POLITIQUES RLS, déclencheurs, worker, étapes de nuit — pas
seulement l'écran.** Les lecteurs les plus critiques sont les plus silencieux :
une politique RLS ne s'appelle nulle part, elle s'applique.
