# Note — Plan de sauvegarde : recommandations, ordre d'exécution, test de restauration

Date : 2026-08-18 (mardi, 11:50) — **révisée le même jour, voir §0.7**
Statut : **proposition. Rien n'a été codé, rien n'a été modifié.** Aucun fichier du projet
n'a été touché ; aucune écriture n'a eu lieu sur Supabase (lectures seules uniquement).
Entrée : `notice/NOTE_BRIEF_SAUVEGARDE_2026-08-18.md`.
Sortie attendue : un feu vert, question par question, avant le moindre développement.

> **Révision du 18/08, après signalement de Frédéric.** Un service **OVH Backup Agent**
> (Veeam) est **déjà souscrit et actif depuis le 19 mai** — et **l'agent n'a jamais été
> installé sur la machine**. Le §0.7 l'établit ; les §1.1, 1.2, 1.4, §2, §3 (T3), §4 et §5
> sont réécrits en conséquence. Les passages révisés sont signalés en italique.
>
> **Mise à jour du 18/08 à 17:08 — l'étape D1 est FAITE.** L'agent a été installé et
> enregistré auprès d'OVH le jour même. Voir §0.8 pour l'état vérifié. **Il reste D0, D0bis
> et D2** — et le protocole de test du §3, qui n'a rien perdu de son importance : on a
> désormais un dispositif qui tourne, pas encore une restauration prouvée.

Échéance qui commande le calendrier : **dimanche 23/08, dans 5 jours.**

---

## 0. Ce que la vérification a changé par rapport au brief

Le brief est juste sur l'essentiel. Cinq points le complètent ou le corrigent, et **trois
d'entre eux changent la décision**.

### 0.1 Les 33 Go de documents ont déjà une seconde copie — partielle, et non sauvegardée

`C:\Hektor\HektorConsoleDocuments` n'est pas un stock isolé : c'est le **sur-ensemble** d'un
bucket Supabase Storage déjà en place.

| Mesuré le 18/08 | Valeur |
|---|---|
| Dossier local | **22 403 fichiers, 32,44 Go** (documents 31,93 Go / photos 0,51 Go) |
| Bucket Supabase `hektor-console-documents` | **21 141 objets, 32 Go**, privé |
| Écrits aujourd'hui même (18/08) | **8 186 fichiers, 11,1 Go** — le rapatriement tourne encore |

Le worker applique `shouldKeepCloud()` (`Console/console_job_worker.js:615`) : le serveur
porte **tout**, le cloud ne garde une copie que pour les biens **vivants**
(`archive = 0` et statut dans `CLOUD_STATUSES`). Commentaire du code, 17/08 :

> « le serveur porte TOUTES les photos (tous index confondus), le cloud n'en garde qu'une
> copie pour les biens vivants. »

Trois conséquences :
1. Le risque « je perds les documents » est **déjà partiellement couvert** — mais l'écart
   local/cloud (1 262 fichiers aujourd'hui) va **croître mécaniquement** à chaque archivage.
2. Supabase Storage n'est **pas** une sauvegarde : la documentation Supabase est explicite,
   les objets Storage ne sont **pas** inclus dans les sauvegardes de base de données.
   Personne ne sauvegarde ces 32 Go, ni ici ni là-bas.
3. C'est tout de même **une seconde copie chez un autre hébergeur**, ce qui abaisse
   nettement l'urgence par rapport à ce que laissait craindre le brief.

### 0.2 Le volume cible n'est pas 33 Go, c'est ≈ 155 Go

`console_job_worker.js:3868` : « Rend le rattrapage massif rejouable sans cout : **318 000
photos**. » Aujourd'hui l'index n'en porte que 1 397 (524 Mo, soit **385 Ko en moyenne**).

> 318 000 × 385 Ko ≈ **122 Go de photos** à venir, + 32 Go de documents = **≈ 155 Go**.

Toute décision prise sur la base de « 33 Go » sera périmée avant d'être appliquée. C'est
l'argument décisif contre l'archive monolithique (§1.2).

### 0.3 Le registre de migrations Supabase EXISTE — le brief se trompe sur ce point

Le brief annonce « 143 patchs `.sql`, **aucun registre de migrations** ». Vérifié :

| `supabase_migrations.schema_migrations` | Valeur |
|---|---|
| Migrations enregistrées | **183** |
| Dont le SQL est stocké (`statements`) | **183 / 183** |
| Poids total du SQL | **288 Ko** |
| Période couverte | 2026-05-04 → 2026-08-17 |

Deux réserves qui empêchent de classer le sujet :
- Le projet a été créé le **2026-03-28** : les **cinq premières semaines** de schéma ne sont
  pas dans le registre.
- Le registre **vit dans la base qu'il faudrait restaurer**. Non exporté, il ne sert à rien
  le jour où on en a besoin.

Cela ne supprime pas la question 8, cela la rend **beaucoup moins chère** à traiter (§1.8).

### 0.4 `app_internal_status` : la question est tranchée, et par les chiffres

Le brief pose l'incompatibilité entre « saisie non rejouable » et « réécrite chaque nuit ».
Comptage sur la base vivante :

| `updated_by` | Lignes |
|---|---|
| `bootstrap_phase2` | **22 198** |
| `push_single_annonce_to_supabase` | 20 |
| **Saisie humaine** | **0** |

`bootstrap_phase2.py:234-241` fait un `ON CONFLICT DO UPDATE` inconditionnel sur
`internal_status`, `priority`, `next_action`, `updated_by`. **La table est intégralement
dérivée.** Elle n'a rien d'irremplaçable aujourd'hui (§1.5).

### 0.5 La sauvegarde du 18/08 07:00 est valide — vérifié, pas supposé

Le brief dit, à raison, « on ne sait pas qu'elle fonctionne ». J'ai levé le doute sur le
niveau 1, **sans rien écrire sur le disque** (décompression et ouverture en mémoire) :

```
critical_20260818_070002.sqlite.gz  ->  89,0 Mo décompressés
en-tête SQLite ................... OK
PRAGMA integrity_check ........... ok
_backup_manifest ................. 13 tables présentes
app_dossier ...................... 56 871 lignes  (base vivante : 56 871)
id min / max ..................... 118 / 5 132 231
id NULL .......................... 0
hektor_annonce_id en double ...... 0
hektor_price_change_event ........ 163  (base vivante : 163)
```

**Le niveau 1 produit une archive saine, complète et fraîche.** Ce qui reste non démontré,
c'est la *procédure* de restauration — pas le contenu de l'archive. C'est exactement ce que
règle le §3.

*Point mineur, pour l'exactitude du brief :* les objets dépendant de `app_dossier_id` se
comptent, côté Supabase, en **32 tables + 10 vues**, et **0 contrainte de clé étrangère**
(recompté indépendamment). Le lien reste purement conventionnel : le diagnostic du brief est
confirmé, seule son arithmétique (« 43 ») mélange deux totaux.

### 0.6 Contexte matériel — établi ce matin

| Fait | Valeur |
|---|---|
| Machine | Serveur **dédié bare-metal OVHcloud**, `ns31851120`, IP 51.210.206.154, AsrockRack B650D4U3, 32 Go RAM |
| Disques | **2 × NVMe Samsung 894,3 Go**, tous deux `Healthy`, **un seul volume C: de 893,8 Go**. **RAID1 CONFIRMÉ** le 18/08 par l'inventaire de l'agent Veeam : volume `VDS_VT_MIRROR` réparti sur les disques 0 et 1, partitions `LDM data` → il s'agit d'un **miroir logiciel Windows** (disques dynamiques), pas d'un RAID matériel |
| Espace libre | 771,6 Go |
| OS | Windows Server 2025, installé le 19/05/2026 |
| Outils présents | `robocopy` (natif), `tar`, `gzip`, `curl`, Node 24.15, Python 3.14.5 |
| Outils **absents** | `rclone`, `7-Zip`, `restic`, `borg`, `pg_dump`, `psql`, CLI Supabase, Docker, agent de sauvegarde |
| Windows Server Backup | Fonctionnalité **disponible mais non installée** |
| Tailscale | Installé mais **arrêté** |
| Code source | Poussé sur `github.com/GTIImmo/Groupe-GTI` — **mais 2 commits locaux non poussés** |

Le miroir RAID1 nuance P1 : la panne d'**un** disque est probablement survivable. Il ne
change **rien** au reste — un miroir réplique instantanément une suppression, un
chiffrement par rançongiciel et une corruption logique. Le risque dominant reste entier.

### 0.7 Un service de sauvegarde hors site est DÉJÀ souscrit — et il ne sauvegarde rien

*(Ajouté après coup, sur signalement de Frédéric : capture de l'espace client OVH.)*

**C'est la découverte la plus importante du dossier, et elle réécrit les §1.1 et §1.2.**

L'espace client OVH montre un service **Backup Agent** actif :

| Champ | Valeur |
|---|---|
| Tenant | `vspc-tenant-734935` |
| Statut | **Actif** |
| Localisation du vault | Europe (France - **Roubaix**), `eu-west-rbx` |
| Serveurs liés / Vaults liés | 1 / 1 |
| Date de création | **19 mai 2026** — le jour même de l'installation de l'OS |
| Offre | Sans engagement, **renouvellement automatique**, prochaine échéance 1er septembre 2026 |

**Ce que c'est.** Le service managé de sauvegarde d'OVHcloud pour serveurs dédiés, bâti sur
**Veeam**. « VSPC » = *Veeam Service Provider Console*, l'interface web de pilotage. Le
principe : on installe un **agent Veeam** sur le serveur, il s'enregistre auprès du tenant,
et il pousse une **sauvegarde image complète de la machine** vers un **vault** — un dépôt
Veeam Cloud Connect hébergé par OVH.

**Ce que le service apporte, et que rien de ce que je proposais n'apportait :**

| Caractéristique | Détail |
|---|---|
| Périmètre | **Image complète du serveur** — OS, code, bases, documents, secrets, tout. Restauration bare-metal possible. |
| Anti-affinité géographique | **VÉRIFIÉ le 18/08** : le serveur est à **Gravelines**, le vault à **Roubaix**. Deux datacenters distincts, ≈ 60 km d'écart. **La corrélation géographique est réglée, et c'est constaté, pas promis.** |
| Immuabilité | **14 jours d'immuabilité** sur le stockage — protection réelle contre le rançongiciel et la suppression malveillante. |
| Cohérence des bases | L'agent Veeam Windows passe par **VSS** : les fichiers `.sqlite`, `-wal` et `-shm` sont capturés au même instant. La contrainte WAL du §1 du brief **ne s'applique pas** à cette couche. |
| Chiffrement au repos | Géré par OVH. |
| Licence | **Incluse gratuitement** avec les serveurs dédiés. |
| Coût | **0,007 € HT/Go/mois**, à la consommation. **Aucun frais de sortie** — restaurer ne coûte rien. |

**Et voici le problème.** Vérifié sur la machine, trois fois plutôt qu'une :

```
Services Veeam ..................... AUCUN
C:\Program Files\Veeam ............. ABSENT
C:\ProgramData\Veeam ............... ABSENT
Programmes installés ............... aucune entrée Veeam / Backup / Agent
Services non-Microsoft actifs ...... les 4 workers Hektor, Tailscale, Defender. Rien d'autre.
```

> **L'agent n'a jamais été installé. Le service est souscrit depuis 3 mois et n'a jamais
> sauvegardé un seul octet.**

« 1 serveur lié » signifie que l'abonnement est rattaché au serveur dans le compte OVH —
pas qu'un agent est enregistré et travaille. Le vault existe ; il est vide.

La facturation étant **à la consommation**, un vault vide se facture ≈ 0 €. Ce n'est donc
pas de l'argent gaspillé : **c'est une protection payée d'avance, disponible, et jamais
activée.** À vérifier d'un clic dans l'onglet « Facturation » de cette même page.

**Ce que cela change.** Le geste le plus rentable de tout ce dossier n'est plus « ouvrir une
destination hors site » : c'est **installer un agent qui attend depuis le 19 mai**. Les §1.1
et §1.2 ci-dessous sont réécrits en conséquence.

**Restrictions à connaître** (documentation OVH) : la politique de sauvegarde est
**non modifiable** — pas de sélection de fichiers ou de dossiers, pas de réglage de l'heure
de déclenchement ; l'accès VSPC est en **lecture seule** ; la rétention est de **14 jours**
(extensible à 30) ; le produit ne fonctionne qu'avec l'**IP publique OVH** du serveur (ni
IP Additional, ni vRack) — ce qui est bien le cas ici (51.210.206.154).

Ces restrictions ne sont pas des défauts, ce sont des **frontières** : elles disent
précisément ce que cette couche ne fera pas, et donc ce qu'il faut garder à côté (§1.1).

### 0.8 L'agent a été installé le 18/08 à 17:08 — état vérifié

Installation faite le jour même, sur décision de Frédéric. Installeur récupéré depuis
l'espace client OVH, **signature Authenticode valide** (certificat EV *Veeam Software Group
GmbH*, émis par Entrust), installé en mode silencieux documenté.

| Contrôle | Résultat |
|---|---|
| `VeeamManagementAgentSvc` | **Running**, démarrage Automatique |
| `VeeamEndpointBackupSvc` — *Veeam Agent for Microsoft Windows* | **Running**, démarrage Automatique |
| Versions | Management Agent **9.1.0.30345** · Agent for Windows **13.0.2.1102** |
| Connexion sortante | **145.239.193.230:6180** établie — plage OVH, canal VSPC ouvert |
| Licence | « edition has been changed from **Free to Server** » · `Source: Rmm, Mode: Server, Servers: 1`, expiration 17/09/2026 |
| Mode | « Veeam Agent has been switched to **managed mode** » — piloté par OVH |
| Prérequis posés | .NET 8.0.21 (Runtime, Host, ASP.NET Core, Desktop) |
| Redémarrage | **Non requis par Veeam.** Le code de sortie 1000 signalait un `PendingFileRename` **préexistant**, portant sur des fichiers temporaires **Chrome** et le spouleur d'impression — sans rapport. |

**Suite, à 17:11 :** OVH a poussé sa politique. Le travail **`ns31851120` a été créé**, et
ses paramètres ont été **validés par la passerelle OVH**
(`vspc-cgw31.prod01.eu-west-rbx.backup.ovhcloud.com:6180` → `IsValid="True"`). Le canal vers
le vault fonctionne. **Aucune sauvegarde n'a encore tourné** : l'agent attend l'heure imposée
par la politique. La première passe devra transférer ≈ 124 Go.

**Enregistrement côté OVH, constaté dans l'onglet `Agents` :**

| Champ | Valeur |
|---|---|
| Nom de l'agent | `agent-ns31851120.ip-51-210-206.eu` |
| Statut | **enabled** |
| Adresse IP | `51.210.206.154/32` — l'IP publique OVH, conforme à la restriction du produit |
| Politique | **`14d_retention`** — la rétention 14 jours est confirmée, c'est la seule proposée |
| Localisation du **serveur** | **Europe (France - Gravelines)** |
| Localisation du **vault** | **Europe (France - Roubaix)** — cf. §0.7 |

> **C'est le point le plus important de tout le dossier, et il est désormais constaté :**
> les données du serveur de Gravelines partent vers un coffre de Roubaix. Le risque P1 du
> brief — « une panne, un incendie ou un rançongiciel emporte la source **et** sa
> sauvegarde » — cesse d'exister dès la première sauvegarde réussie.

### ⚠️ 0.9 Point de vigilance : édition de licence *Workstation* sur un OS *Server*

Chronologie relevée dans `Svc.VeeamEndpointBackup.log` :

```
17:07:59   Mode: Server        (« edition changed from Free to Server »)
17:09:47   Mode: Server
17:11:39   Mode: Workstation   (« edition changed from Server to Workstation »)
17:11:46   Foreign license: Mode: Workstation
```

Au moment exact où OVH a créé le travail de sauvegarde, l'agent est **repassé de l'édition
Server à l'édition Workstation**. Or la machine tourne sous **Windows Server 2025**, et le
tenant dispose des deux droits (`Workstations: 1, Servers: 1`).

Ce que cela peut signifier — **à vérifier, je ne tranche pas** : soit c'est le fonctionnement
normal de l'offre OVH, soit le serveur a été **déclaré comme poste de travail** dans la
console. L'édition Workstation est prévue pour les postes clients ; elle sauvegarde bien
l'image du volume, mais elle n'offre pas le traitement applicatif de l'édition Server.

**Vérification faite dans l'onglet `Agents` :** la console **n'expose aucun champ d'édition**
— pas de distinction poste/serveur, un seul bouton « Ajouter un **serveur** », une seule
politique (`14d_retention`), et l'agent est `enabled`. Tout indique donc une **modalité
interne d'attribution de licence par OVH**, et non une mauvaise déclaration de la machine.

**Impact pratique attendu : nul.** Les bases sont en SQLite — ni SQL Server, ni Exchange —
et la cohérence vient du **snapshot VSS du volume**, qui fonctionne dans les deux éditions.

**Statut : point de vigilance, pas anomalie.** Il se referme tout seul le jour où la première
sauvegarde se termine correctement. S'il devait au contraire y avoir un échec évoquant la
licence ou le type de système, c'est la **première piste** à donner au support OVH.

### ✅ 0.10 La première sauvegarde a réussi — 18/08 22:00, vérifiée le 19/08 à 09:00

```
18/08 22:00:01   Veeam Agent 'vspc-tenant-cc1-734935-ns31851120-14d_retention' has been started
18/08 22:31:55   'ns31851120' restore point has been created
18/08 22:32:05   finished with Success
                 Session result: "Success", job type: "EndpointBackup"  /  IsSuccess: 'True'
```

| Mesure | Valeur |
|---|---|
| Durée | **32 minutes** |
| Trafic sortant | 66,79 Go (18/08 18:15) → **170,39 Go** (19/08 09:00) = **+103,6 Go transférés** |
| Contrôles horaires depuis | tous à `Result: [Success], State: [Stopped]` |
| Sauvegarde locale du 19/08 07:00 | `critical_20260819_070002.sqlite.gz`, 7,7 Mo, tâche en résultat 0 |

> **Le risque P1 du brief est fermé.** « Une panne disque, un ransomware ou la perte du
> serveur emporte la source **et** sa sauvegarde ensemble » : ce n'est plus vrai depuis le
> 18/08 à 22:32. 103,6 Go de données de Gravelines dorment à Roubaix, immuables 14 jours.
>
> **Ce qui reste non prouvé, et c'est maintenant LE sujet :** personne n'a jamais restauré.
> Le §3 devient le seul chantier critique du dossier.

### 0.11 Le volume grossit vite — la décision du §1.2 était plus urgente que prévu

Mesuré le 19/08 à 09:00, soit **15 heures** après la mesure de référence :

| | 18/08 18:00 | 19/08 09:00 | Écart |
|---|---|---|---|
| `HektorConsoleDocuments` | 22 515 fichiers, **32,5 Go** | 42 033 fichiers, **56,37 Go** | **+19 518 fichiers, +23,87 Go** |

Le rattrapage des photos tourne à plein. En une nuit, le dossier a pris **73 %**. La
projection de ≈ 155 Go du §0.2 n'était pas pessimiste : un tiers du chemin a été parcouru
en quinze heures.

> Conséquence directe : si le niveau 3 n'avait pas été désactivé, le zip de dimanche 23/08
> ne portait plus sur 32,5 Go mais vraisemblablement sur **plus de 100 Go** — soit une passe
> de plus d'une heure et ≈ 400 Go en rétention. La décision du §1.2 s'est révélée plus
> urgente que ce que ses propres chiffres annonçaient.

### ✅✅ 0.11bis LA PREUVE — restauration réelle depuis le coffre OVH, 19/08 à 11h

**C'est le seul test qui manquait depuis le début du chantier. Il est fait, et il passe.**

Un fichier a été **rapatrié depuis le vault de Roubaix** via l'assistant *File Level Restore*
de l'agent Veeam (chemin `Copy To…`, jamais `Restore` — rien n'a été écrasé).

Fichier témoin choisi pour être petit, daté d'avant le point de restauration, et
**auto-vérifiable** : `C:\Hektor\Backups\critical\critical_20260818_070002.sqlite.gz`
(7,7 Mo, écrit le 18/08 à 07:00, donc présent dans le point de 22:32).

**Étape 1 — le fichier revient intact, octet pour octet :**

| | Référence (fichier vivant) | Restauré depuis Roubaix |
|---|---|---|
| Taille | 8 110 232 o | **8 110 232 o** |
| SHA256 | `5FF82B27CDA1364F2D1AE6763DB8D741410B91B57462B15A314AA48290FF4F9F` | **identique** |

**Étape 2 — et la donnée est lisible et complète :**

```
decompresse      89,0 Mo
entete SQLite    True
integrity_check  ok
tables manifeste 13
app_dossier      56 871 lignes
id min / max     118 / 5 132 231
id NULL          0        doublons hektor  0

controle croise  annonce 11701 -> (1337944, 'EM66580')
                 base vivante  -> (1337944, 'EM66580')   <- concordant
```

> **La chaîne complète est prouvée :** coffre OVH de Roubaix → fichier rapatrié →
> empreinte identique → archive décompressée → base SQLite saine → 56 871 dossiers →
> un dossier précis vérifié contre la production.
>
> Le dispositif n'est plus une hypothèse. **On sait sauvegarder, et on sait restaurer.**

Ce que ce test ne couvre pas encore : la restauration **complète du serveur** (T3, chemin 1),
et surtout la restauration **depuis la console OVH sans le serveur** — le vrai scénario de
sinistre. Mais le doute principal est levé : les données du coffre sont intègres et
exploitables.

Écran de l'assistant, relevé au passage :

```
Computer name    ns31851120
Disks included   Disk 1, Disk 0
Volumes included C
OS               Windows Server 2025 Standard
Restore points   1 — « less than a day ago », type Full
```

### ✅ 0.12 Tests T1 et T2 exécutés le 19/08 — et ce qu'ils ont trouvé

**T1 — archive quotidienne, ouverte en mémoire, aucune écriture. Les 7 critères sont verts.**

```
archive          critical_20260819_083236.sqlite.gz   (age 0,8 h)
entete SQLite    True          integrity_check   ok
tables manifeste 13           app_dossier       56 880
id min / max     118 / 5 189 129
id NULL          0            doublons hektor   0
```

**T2 — restauration réelle de `phase2.sqlite` depuis l'instantané du 17/08.**

```
1 859,5 Mo decompresses en 2,3 s   ->   integrity_check : ok
24 tables | app_dossier 56 867 | app_affaire_ledger 28 978 | id 118 .. 4 961 608
```

Puis le test de mapping, sur 300 paires réparties de l'id 613 à 4 791 021, **empreinte md5
vérifiée identique à celle de Supabase** (`eed4c66e…`, 3 438 caractères) :

| Résultat | Valeur |
|---|---|
| **DIVERGENTS** | **0** ← le critère décisif |
| INTROUVABLES par l'une ou l'autre clé | **0 sur 300** |
| résolus par `app_dossier.id` | 27 |
| résolus par `hektor_annonce_id` | **273** |

> **Verdict : la sauvegarde est fidèle.** Vérification croisée faite sur la base **vivante** :
> elle donne **exactement les mêmes résultats** que la base restaurée, ligne pour ligne. Le
> fichier restauré est une copie exacte. C'était la question posée ; elle est tranchée.

### ⚠️ 0.13 Ce que le test a trouvé au passage — un sujet distinct, et sérieux

Le test devait valider une sauvegarde. Il a validé la sauvegarde **et** mis au jour autre
chose : **`app_dossier_current.app_dossier_id`, côté Supabase, ne correspond plus à
`phase2.app_dossier.id` pour ~91 % des dossiers courants.**

Exemples relevés :

| Annonce Hektor | `app_dossier_id` chez Supabase | `app_dossier.id` en local |
|---|---|---|
| 11701 | 613 | **1 337 944** |
| 11795 | 675 | **1 338 047** |
| 11863 | 735 | **1 338 123** |
| 62881 | 4 791 021 | 4 791 021 *(concordant)* |

Trois précisions qui cadrent le constat :

1. **Supabase est cohérent avec lui-même.** Pour l'annonce 11701, `app_dossier_current`,
   `app_dossier_detail_current` et les autres tables s'accordent toutes sur `613`. Rien
   n'est cassé *à l'intérieur* de Supabase.
2. **Aucune donnée n'est perdue.** Les 300 paires se retrouvent, 300 sur 300 — mais 273
   d'entre elles ne se retrouvent que par `hektor_annonce_id`.
3. **La clé de jointure qui fonctionne réellement entre les deux systèmes est donc
   `hektor_annonce_id` — c'est-à-dire l'identifiant de Hektor, pas le nôtre.**

**Pourquoi cela compte.** Le brief présente `app_dossier` comme « le point de défaillance
unique du modèle de données », au motif que ses ids AUTOINCREMENT ne sont pas
reconstructibles. Le constat ci-dessus ne contredit pas l'importance du fichier, mais il
déplace le problème : **la divergence a déjà eu lieu**, et le lien entre l'application et
ses propres données Supabase repose aujourd'hui, en pratique, sur un identifiant qui
appartient à Hektor. Pour un projet dont l'objet est précisément de s'affranchir de Hektor,
c'est un point à instruire.

**Ce que je ne sais pas** — et que ce test ne permet pas de trancher : dans quel sens la
divergence s'est produite (ids locaux réémis lors d'une reconstruction de `phase2.sqlite`,
ou valeurs Supabase figées à un état ancien), depuis quand, et si les 43 objets dépendants
sont tous logés à la même enseigne. Le constat porte sur **un échantillon de 300 lignes
d'une seule table**.

**Recommandation : un audit dédié, distinct de ce chantier.** Mesurer le recouvrement
complet sur les 13 220 lignes de `app_dossier_current`, puis sur les 32 tables et 10 vues
concernées. Ne rien corriger avant d'avoir compris le sens de la divergence — une
« correction » à l'aveugle sur une clé sans contrainte d'intégrité ferait plus de dégâts que
le problème lui-même.

> **La leçon du jour.** Le premier test de restauration jamais exécuté sur ce projet a
> confirmé la sauvegarde en quelques minutes — et a révélé un problème qu'aucune lecture de
> code n'avait vu, ni dans l'audit du 18/08, ni dans le brief. C'est très exactement ce à
> quoi sert un test de restauration.

---

## 1. Recommandation, question par question

### 1.1 — Destination hors site *(brief §5.1, urgence haute)*

**Ce que je propose : activer ce qui est déjà payé, puis ajouter une seule chose.**

#### Couche A — installer l'agent Veeam du Backup Agent OVH *(le geste n°1 du dossier)*

Le service est souscrit depuis le 19 mai et **n'a jamais tourné** (§0.7). L'installer, c'est
obtenir en une opération :

- une **image complète du serveur** hors site — OS, code, bases SQLite, 32 Go de documents,
  secrets, tâches planifiées, services : **tout**, y compris ce que j'aurais oublié ;
- dans un **datacenter différent** de celui du serveur, par construction ;
- avec **14 jours d'immuabilité** contre le rançongiciel ;
- avec une **cohérence VSS** des bases en WAL, sans arrêt d'écriture ;
- **restauration bare-metal**, et **sans frais de sortie**.

**Coût : la licence est incluse, seul le stockage est facturé, à 0,007 € HT/Go/mois.**
Le volume C: occupe aujourd'hui **122,2 Go**. Après compression Veeam, l'empreinte stockée
se situera vraisemblablement entre **80 et 130 Go**, soit **0,55 à 0,90 € HT/mois**. À la
cible de 155 Go de documents (§0.2), compter **1,50 à 2,50 € HT/mois**. Même 1 To ne coûte
que **7 € HT/mois**.

> C'est moins cher que tout ce que j'avais proposé, cela couvre infiniment plus, et
> **c'est déjà payé.** Il n'y a aucun arbitrage à faire ici : c'est un oubli à réparer.

**Ce que cette couche ne fera PAS** — et c'est pourquoi elle ne remplace pas tout :

| Limite | Conséquence |
|---|---|
| **Rétention 14 jours** (30 en option) | Une erreur logique découverte au bout de 3 semaines n'est plus rattrapable. |
| **Image complète uniquement** — pas de sélection de fichiers | Récupérer *une* table ou *un* dossier impose de monter une image de ~120 Go. Lourd, lent, mal adapté au cas courant. |
| **Politique non modifiable**, heure de déclenchement imposée, VSPC en lecture seule | On ne maîtrise ni la fenêtre, ni la fréquence. À vérifier : le déclenchement ne doit pas tomber pendant le pipeline de 05:30. |
| **Même fournisseur, même compte** | Couvre l'incendie et le rançongiciel. Ne couvre **pas** la perte du compte OVH : suspension, litige de facturation, résiliation par erreur. |

#### Couche B — le petit jeu, chez un second fournisseur

C'est la seule chose que j'ajoute, et elle répond exactement aux 4 limites ci-dessus.
**Hetzner Storage Box BX11, 1 To, 3,20 € HT/mois** (SFTP, snapshots inclus, trafic
illimité, sans engagement). Elle ne reçoit **que le petit jeu, moins de 1 Go** :

| Contenu | Poids | Rétention |
|---|---|---|
| Jeu critique quotidien (13 tables + ledger) | ≈ 9,2 Mo/nuit | **90 jours** |
| Instantané `phase2` hebdomadaire | 220 Mo | 28 jours |
| Dump Supabase hebdomadaire (§1.7) | 300–500 Mo | 28 jours |
| Coffre de secrets chiffré (§1.6) | ≈ 7 Ko | — |
| Instantané mensuel `hektor.sqlite` (§4) | 400–600 Mo | 2 copies |

Elle apporte trois choses que la couche A ne donne pas : **90 jours d'historique** au lieu
de 14, une **restauration granulaire immédiate** (un `.gz` de 9 Mo qu'on ouvre en 10
secondes — c'est ce que fait le test T1), et la **décorrélation du fournisseur**.

**Outil : `rclone`**, un exécutable autonome, sans installeur ni service, avec `crypt`
pour le chiffrement côté client. Passe-phrase **uniquement** dans le gestionnaire de mots de
passe, jamais sur le serveur.

**Règle non négociable : la cible n'est jamais montée en lecture-écriture permanente.**
Pas de lettre de lecteur, pas de CIFS persistant. Les identifiants ne servent qu'à l'instant
du `rclone copy`. Une cible montée en permanence est chiffrée en même temps que la source —
c'est le mode d'échec le plus fréquent des sauvegardes qui « existaient ».

*(L'offre « OVH Backup Storage 500 Go incluse » que j'évoquais dans la version initiale de
cette note n'est plus nécessaire : le Backup Agent la rend redondante pour le gros volume,
et la couche B la rend redondante pour le petit. Ne rien ouvrir de ce côté.)*

| | |
|---|---|
| **Coût** | Couche A : **0,55 à 0,90 € HT/mois** aujourd'hui (licence incluse, stockage à la consommation), déjà souscrite. Couche B : **3,20 € HT/mois**. **Total ≈ 4 € HT/mois.** |
| **Temps** | **1 h** (installer et vérifier l'agent Veeam) + 2 h (couche B + rclone + crypt) |
| **En cas de sinistre** | Aujourd'hui : perte du serveur = perte totale, sans recours. Après : le serveur **entier** se reconstruit depuis une image dans un autre datacenter, immuable 14 jours ; et les données irremplaçables ont en plus 90 jours d'historique granulaire chez un **second fournisseur**. |

---

### 1.2 — Les 33 Go de documents *(brief §5.2, urgence haute, échéance dimanche 23/08)*

**Ce que je propose : arrêter le niveau 3 (l'archive zip), sans rien mettre à la place.**

*(Révisé après §0.7. La version initiale de cette note proposait un miroir `rclone` des
32 Go. Le Backup Agent le rend **inutile** : il embarque déjà ces fichiers dans l'image
complète, hors site, dans un autre datacenter, immuable 14 jours. Construire un miroir en
plus serait une troisième copie payée deux fois. **On supprime, on ne remplace pas.**)*

**Pourquoi l'archive monolithique ne tient pas — mesuré, pas estimé.**

| Mesure faite le 18/08 | Résultat |
|---|---|
| Compressibilité réelle des PDF (échantillon de 60, 155 Mo) | **6,3 % de gain** — un zip de 32,4 Go produit ≈ 30 Go |
| Débit lecture + deflate observé | **28 Mo/s** → **≈ 20 minutes** de passe synchrone |
| Rétention en vigueur | 28 jours = **4 archives** ≈ **121 Go** de copies quasi identiques |
| À la cible de 155 Go (§0.2) | 4 × ≈ 145 Go = **≈ 580 Go** sur un volume de 894 Go → **saturation** |

Ce n'est pas un problème dimanche prochain (771 Go libres) : c'est un problème **certain**
avant la fin du rapatriement des photos. Et une archive de 30 Go est, en pratique, la pire
chose à manipuler le jour d'une restauration sous stress.

**Un argument de plus, apporté par le §0.7 : ces zips seraient sauvegardés, et facturés.**
Le Backup Agent prend une image du volume C:. Les 121 Go d'archives quasi identiques que le
niveau 3 accumulerait s'y retrouveraient intégralement, à **0,007 € HT/Go/mois** —
soit ≈ **0,85 € HT/mois de facture pour sauvegarder des copies de fichiers déjà
sauvegardés**, et ≈ 4 € HT/mois à la cible de 155 Go. Le niveau 3 n'est plus seulement
inutile : il devient un poste de coût qui grossit tout seul.

**Ce qu'il faut décider avant dimanche.**
Le niveau 3 se déclenche par `(Get-Date).DayOfWeek -eq 'Sunday'` dans `run_backup.ps1:23`.
Il n'existe **aucun interrupteur** pour le neutraliser sans toucher au code.

- **Option recommandée — une modification minimale et réversible (≈ 30 min) :** un drapeau
  `--no-documents` sur `backup_critical.py`, plus un garde-fou de taille qui saute le
  niveau 3 au-delà d'un seuil (par exemple 2 Go) en le journalisant explicitement. Additif,
  derrière un interrupteur, conforme aux règles du projet. **C'est le seul développement
  que je demande avant dimanche.**
- **Repli sans une ligne de code (2 min) :** faire passer le déclencheur de la tâche
  `GTI Sauvegarde` de « tous les jours » à « du lundi au samedi ». **Je le déconseille** :
  cela supprime aussi le niveau 1 du dimanche *et* l'instantané `phase2` hebdomadaire —
  on éteindrait la sauvegarde pour éviter qu'elle grossisse.

| | |
|---|---|
| **Coût** | **0 €**, et ≈ 0,85 € HT/mois **évités** sur la facture du vault (≈ 4 € à la cible) |
| **Temps** | **30 min**, avant dimanche. Plus de miroir à construire. |
| **En cas de sinistre** | Aujourd'hui : 99,8 % des documents locaux ne sont dans aucune sauvegarde, et le cloud n'en tient qu'une copie élaguée. Après l'installation de l'agent (§1.1) : les 22 403 fichiers sont dans l'image hors site, dans un autre datacenter, immuables 14 jours. |

---

### 1.3 — Protocole de test de restauration *(brief §5.3, urgence haute)*

**Ce que je propose : trois niveaux de test, de 10 minutes à une demi-journée.**
C'est le cœur de cette note : le §3 en donne le détail complet, les commandes et les
critères. Résumé :

| | Fréquence | Durée | Ce qui est prouvé |
|---|---|---|---|
| **T1** | mensuel, automatisable | 10 min | L'archive de la nuit est saine, complète, fraîche |
| **T2** | trimestriel | 1 h | `phase2.sqlite` se restaure et le mapping d'identité **résout réellement** contre Supabase |
| **T3** | semestriel | ½ journée | « Le serveur a disparu » — on repart de zéro sur une autre machine |

**Pourquoi c'est le point le plus important.** Une sauvegarde jamais restaurée n'est pas une
sauvegarde, c'est une hypothèse coûteuse. Le brief le dit ; les **deux fichiers de 0 octet**
de `Backups\critical\` (17/08 11:50) le prouvent : un run peut produire un fichier
inexploitable sans que rien ne le signale, et la purge ne l'effacera qu'au bout de 90 jours.

| | |
|---|---|
| **Coût** | 0 € |
| **Temps** | 1 h 30 pour outiller T1 + T2 ; T3 = ½ journée à caler dans le trimestre |
| **En cas de sinistre** | La différence entre « je crois qu'on a une sauvegarde » et « je sais restaurer en N heures, je l'ai fait le mois dernier ». |

---

### 1.4 — Surveillance *(brief §5.4, urgence moyenne)*

**Ce que je propose : les quatre correctifs du brief, plus deux.** Ils sont petits,
indépendants, et sans eux tout le reste peut mourir en silence.

1. **Remonter le code de sortie.** `run_backup.ps1:32-34` attrape l'exception et **ne
   relance rien** : `LastTaskResult` vaut 0 quoi qu'il arrive. Confirmé à l'instant : les
   5 tâches GTI affichent `Resultat = 0`. Correctif : `exit 1` dans le `catch`.
2. **Ajouter `GTI Sauvegarde` aux tâches surveillées** (`check_gti_health.py:1497`, défaut
   à 4 tâches, celle-ci absente).
3. **Aligner la tâche sur S4U.** Vérifié : les 4 autres tâches GTI sont en `S4U`,
   `GTI Sauvegarde` est **la seule en `Interactive`**. Elle dépend d'une session `admin`
   ouverte — sur précisément la tâche la moins surveillée.
4. **Sonde d'âge et de taille** sur `C:\Hektor\Backups` : alerte si la dernière archive
   `critical` a plus de 30 h **ou** pèse moins de 5 Mo (elle en pèse 8,1). Une sonde de
   *présence* ne détecterait pas les fichiers de 0 octet — c'est le **plancher de taille**
   qui les attrape.
5. **En plus : une empreinte `.sha256` à côté de chaque archive**, écrite après le gzip.
   Elle rend T1 instantané et détecte la corruption silencieuse.
6. **En plus : un horodatage « dernier envoi hors site réussi »**, remonté par la même
   sonde. Sans lui, on surveillerait la production d'archives sans savoir si elles quittent
   le serveur — c'est-à-dire le seul point qui compte.
7. **En plus, depuis le §0.7 : surveiller l'agent Veeam.** Le service dort depuis trois mois
   **sans qu'aucun signal ne l'ait dit** — c'est exactement le défaut P3, mais sur la couche
   la plus importante. Deux sondes locales, indépendantes de la console OVH : le **service
   Veeam est-il en cours d'exécution**, et le **journal du dernier travail réussi a-t-il
   moins de 48 h** ? Une alerte purement locale, qui ne dépend pas d'aller regarder un
   tableau de bord.

Les alertes partent vers `frederic.gerphagnon@gti-immobilier.fr` (canal existant, jamais
`accueil@`).

| | |
|---|---|
| **Coût** | 0 € |
| **Temps** | ≈ 3 h |
| **En cas de sinistre** | Aujourd'hui la sauvegarde peut échouer chaque nuit sans que personne ne l'apprenne. Après, un échec est connu **le lendemain**. |

---

### 1.5 — Périmètre *(brief §5.5, urgence moyenne)*

**`app_affaire_ledger` : OUI, quotidiennement, mais sans `payload_json`.**

Mesuré : 28 979 lignes locales, 28 979 côté Supabase, **0 ligne** avec
`present_in_hektor = false` à ce jour. Aujourd'hui c'est un doublon parfait de Supabase.
Mais sa raison d'être est précisément d'**accumuler ce que Hektor finira par retirer** : sa
valeur irremplaçable est **future et croissante**. On ne l'ajoute pas parce qu'elle est
critique aujourd'hui, on l'ajoute parce qu'elle le deviendra sans qu'aucun signal ne le dise.

| Variante | Poids gzip mesuré | Effet sur le niveau 1 |
|---|---|---|
| Table complète | **≈ 19 Mo** (`payload_json` = 106 Mo bruts) | 7,7 → ≈ 27 Mo/nuit, soit 2,4 Go sur 90 j |
| **Sans `payload_json`** | **1,45 Mo** | 7,7 → **≈ 9,2 Mo/nuit** |

`payload_json` est la copie brute de ceinture-et-bretelles ; toutes les colonnes que
l'application lit (`kind`, `state`, `montant`, `date`, `date_acte`, `sequestre`,
`acquereur_json`, `first_seen_at`, `present_in_hektor`…) sont structurées à côté. Et
`payload_json` **voyage déjà** dans l'instantané `phase2` hebdomadaire. On obtient donc la
granularité quotidienne sur ce qui compte, pour **+1,45 Mo**, sans rien perdre.

**`app_internal_status` : la garder, corriger le commentaire.**
Chiffres du §0.4 : **0 ligne de saisie humaine**. Elle n'a pas sa place dans une liste dite
« non rejouable » — mais elle ne coûte rien et pourrait redevenir critique le jour où
l'application y écrira du statut saisi. Décision : **on la garde, on corrige le commentaire
mensonger de `backup_critical.py:69`**, et on rouvre la question ce jour-là.

**Sessions Playwright : NON.**
Les 4 fichiers actifs (`storage_state_actions/admin/documents/sync_light`, ≈ 17 Ko chacun,
rafraîchis ce matin) sont **régénérables** : le worker sait se reconnecter seul, TOTP
compris (`HEKTOR_TOTP_SECRET`, commit `e63858b`). Ce qu'il faut mettre à l'abri, ce sont
**les identifiants**, pas les cookies (§1.6). Les sauvegarder reviendrait à stocker des
jetons de session vivants dans une archive — un risque ajouté sans bénéfice.

**Configuration de déploiement : OUI, mais en la matérialisant.**
Aucun `vercel.json`, `render.yaml` ni `Dockerfile` : tout vit dans des tableaux de bord SaaS
et **rien n'est reproductible**. Deux gestes peu coûteux, à traiter comme un lot distinct :
- exporter en XML les **5 tâches planifiées GTI** et les définitions des **4 services
  worker** (quelques Ko, à embarquer dans le niveau 1) ;
- écrire un `notice/RESTAURATION_INFRA.md` listant les variables d'environnement Vercel et
  Render **par leur nom** (jamais leur valeur — les valeurs vont au coffre).

C'est ce qui transforme une remise en route de 3 jours en une remise en route de 3 heures.

**Données propres à Supabase : couvertes, et minuscules.**
Recensement des tables qui naissent dans Supabase et n'existent nulle part ailleurs :
`app_agent_prompt` (3 lignes, prompts réglés à la main), `app_dossier_estimation` (31),
`app_dossier_cadastre` (21), `app_email_envoi` (82), `app_email_event` (79),
`app_google_calendar_event_link` (7), `app_relance_rapprochement` (10),
`app_espace_message` (1), `app_espace_visite_request` (3). **Moins de 2 Mo au total.**
Le dump hebdomadaire du §1.7 les couvre intégralement. Rien de spécifique à prévoir.

| | |
|---|---|
| **Coût** | 0 € |
| **Temps** | 1 h (ledger + commentaire) + 2 h (lot « configuration de déploiement ») |
| **En cas de sinistre** | Le registre d'affaires — conçu pour survivre à Hektor — survit aussi au serveur ; et on sait **comment** rebâtir l'infrastructure au lieu de la redécouvrir. |

---

### 1.6 — Les secrets *(brief §5.6, urgence moyenne)*

**Ce que je propose : un coffre, et une copie chiffrée hors site. Jamais en clair dans une
archive.**

Inventaire vérifié — **6 fichiers, ≈ 6,8 Ko au total** :

| Fichier | Taille |
|---|---|
| `secrets/google-workspace-service-account.json` | 2 385 o |
| `Console/.env` | 2 280 o |
| `.env` (racine) | 1 576 o |
| `apps/hektor-v1/.env` | 415 o |
| `matterport/.env` | 96 o |
| `Ecrans Android/github_token.txt` | 40 o |

1. **Dépôt de référence : le gestionnaire de mots de passe**, pas le serveur. C'est le seul
   endroit qui survit à la perte de la machine *et* qui gère le partage.
2. **Une copie chiffrée hors site** (`rclone crypt` ou une archive AES-256), sur la couche B
   uniquement, **passe-phrase absente du serveur** — sinon on chiffre avec la clé posée à
   côté de la serrure.
3. **Séparer le TOTP du mot de passe.** `HEKTOR_TOTP_SECRET` et `HEKTOR_PASSWORD` cohabitent
   dans `Console/.env` : le second facteur n'apporte aujourd'hui **rien**. Le serveur a
   besoin des deux pour se connecter seul — c'est un compromis assumé au niveau du fichier
   d'exploitation, mais **dans le coffre, ils doivent être dans deux entrées distinctes**,
   pour qu'une fuite de l'une ne donne pas les deux.
4. **Supprimer deux fichiers morts**, confirmés présents : `Console/.env.txt` (2 104 o,
   doublon périmé du 19/05, lu par aucun code) et `Console/token_dump.json` (12 406 o).
   Ce sont deux copies de secrets de plus à protéger, pour zéro usage.

| | |
|---|---|
| **Coût** | 0 € si un gestionnaire est déjà en service ; sinon 10 à 40 €/an |
| **Temps** | 1 h |
| **En cas de sinistre** | Aujourd'hui, perdre le disque impose de régénérer chaque credential auprès de Hektor, Google, Supabase, Matterport et GitHub — plusieurs jours, avec arrêt du pipeline. Après : quelques minutes de restauration. |

---

### 1.7 — Supabase *(brief §5.7, « à établir »)*

**Établi. Voici la réponse complète.**

| Point | Constat vérifié |
|---|---|
| Organisation / plan | « Grou GTI », plan **Pro** |
| Projet | `dwaqxfrinihnychuoptk`, région **eu-west-2**, `ACTIVE_HEALTHY` |
| Postgres | **17.6.1.084** |
| Taille | **1 768 Mo**, 107 tables `public` |
| Sauvegardes fournies | **quotidiennes, rétention 7 jours** — c'est tout ce que le plan Pro donne |
| Type | Postgres ≥ 15.8.1.079 ⇒ **sauvegardes physiques**, donc **NON téléchargeables** |
| Storage | **Les objets Storage ne sont PAS couverts** par les sauvegardes de base |
| Suppression du projet | Supprime **définitivement les sauvegardes** avec |
| PITR | Option payante : **≈ 100 $/mois** pour 7 jours |

Trois conclusions qui ne sautent pas aux yeux :
- **Il n'existe aucun fichier à récupérer chez Supabase.** Le passage aux sauvegardes
  physiques signifie qu'on restaure *sur place* ou vers un clone ; on ne sort rien. La seule
  copie hors-Supabase possible est **celle qu'on fabrique soi-même**.
- **Les 32 Go du bucket `hektor-console-documents` n'ont aucune sauvegarde, nulle part.**
  Ni chez Supabase (exclu du périmètre), ni ici (§0.1). Le miroir du §1.2 est ce qui les
  protège — par le local, qui en est le sur-ensemble.
- **7 jours de rétention est court** pour une erreur logique découverte tardivement.

**Ce que je propose : ne rien acheter, et prendre un dump logique hebdomadaire.**

**Ne pas prendre PITR (≈ 100 $/mois, soit ≈ 1 100 €/an).** Le RPO de 2 minutes qu'il achète
porte sur des données dont la quasi-totalité est **re-poussable depuis les sources locales**
(le pipeline fait exactement cela chaque nuit). L'irremplaçable côté Supabase, c'est le
**schéma** et **moins de 2 Mo** de lignes (§1.5). Payer 1 100 €/an pour 2 minutes de RPO sur
des données reconstructibles, alors que 0 € de copie hors site manque encore, serait acheter
le mauvais bout du problème.

**À la place : `pg_dump` hebdomadaire vers la couche B.** Un dump logique complet
(schéma + données + fonctions + RLS + triggers + jobs `pg_cron`), estimé à 300–500 Mo
compressés. Prérequis : `pg_dump` est **absent** de la machine, tout comme `psql`, la CLI
Supabase et Docker. Installer les **outils clients PostgreSQL 17** (gratuits, sans serveur,
≈ 5 min) est le chemin le plus court et le plus fidèle. Il faudra le **mot de passe de la
base** (tableau de bord Supabase) — ce n'est **pas** la `SERVICE_ROLE_KEY`.

| | |
|---|---|
| **Coût** | **0 €** — et **≈ 1 100 €/an économisés** en refusant PITR |
| **Temps** | 3 h (outils clients + script + premier dump vérifié) |
| **En cas de sinistre** | Aujourd'hui : la disparition du compte Supabase emporte la base **et** ses sauvegardes, sans recours. Après : un dump complet hors site, restaurable dans un projet neuf. |

---

### 1.8 — Le schéma SQL *(brief §5.8, « basse, mais bloquant »)*

**Ce que je propose : traiter la question ici, en une ligne de plus, pas dans un chantier
séparé.**

Le §0.3 change la donne : le registre existe (183 migrations, SQL inclus, 288 Ko). Mais
surtout — **avec un `pg_dump` complet, on ne rejoue pas les patchs.** On restaure le
schéma en une commande. La question « quels patchs rejouer, dans quel ordre » **disparaît**
au lieu d'être résolue.

Le dump du §1.7 étant déjà proposé, le complément se réduit à **une commande de plus dans
le même script** : exporter `supabase_migrations.schema_migrations` en `.sql` lisible, pour
garder l'**historique** (le dump donne l'état final ; le registre donne le chemin). 288 Ko.

Reste un trou assumé : les cinq semaines du 28/03 au 04/05 ne sont dans aucun registre.
Le `pg_dump` les couvre **en résultat** (le schéma actuel les contient), pas en historique.
C'est suffisant pour restaurer ; insuffisant pour comprendre. Je propose de **l'accepter et
de l'écrire**, plutôt que d'ouvrir une archéologie sans valeur opérationnelle.

| | |
|---|---|
| **Coût** | 0 € |
| **Temps** | 15 min (inclus dans le lot §1.7) |
| **En cas de sinistre** | Aujourd'hui, restaurer Supabase supposerait de deviner l'ordre de 143 patchs. Après : une commande. |

---

## 2. Ordre d'exécution

### Avant dimanche 23/08 — 5 jours, ce qui est réellement obligatoire

| # | Action | Durée | Dépend de | Pourquoi cette date |
|---|---|---|---|---|
| **D0** | `git push` des **2 commits locaux** | 5 min | — | Le geste hors site le moins cher du dossier. Le code est déjà sur GitHub **sauf** ces deux commits. À faire aujourd'hui. |
| **D0bis** | Restaurer les **12 notes supprimées** de `notice/` | 5 min | — | **Elles ne sont plus sur le disque** : vérifié, `PLAN_DEV_APRES_AUDIT_COMPLET_2026-08-18.md`, `NOTE_AUDIT_MAITRE_2026-08-17.md` et 10 autres sont absentes et leur suppression est *stagée*. Elles ne survivent que dans `HEAD`. Un `git commit -a` les effacerait définitivement. |
| **D1** | **Installer l'agent Veeam du Backup Agent** et lancer la première sauvegarde | **1 h** | — | **Le geste le plus rentable du dossier.** Le service est payé depuis le 19 mai et n'a jamais tourné. Tant qu'il dort, **il n'existe aucune copie hors site**, et c'est le risque dominant. Une image complète, hors site, immuable, arrive en une opération. |
| **D2** | Décider le §1.2 et poser le garde-fou du niveau 3 | 30 min | feu vert | **Sans cela, dimanche 07:00 déclenche une passe de 20 min sur 32,4 Go**, pour ≈ 30 Go d'archive, répétée 4 fois en rétention — désormais sauvegardés **et facturés** dans le vault. |

> Si le temps manque cette semaine, **les quatre sont incompressibles** — et D1 est le seul
> qui, à lui seul, fait passer le projet de « aucune copie hors site » à « le serveur entier
> est restaurable ailleurs ». D0bis est urgent parce que la perte est **déjà en cours** ;
> D2 parce que l'échéance est datée.

### Après — dans l'ordre des dépendances

| # | Action | Durée | Dépend de |
|---|---|---|---|
| **S1** | Vérifier le **premier point de restauration** dans la VSPC : date, taille, serveur, et **l'heure de déclenchement** (ne doit pas tomber sur le pipeline de 05:30) | 30 min | D1 |
| **S2** | Surveillance : les 7 points du §1.4, dont les 2 sondes Veeam | 3 h | D1 |
| **S3** | Secrets au coffre + suppression des 2 fichiers morts | 1 h | — *(indépendant, faisable en parallèle)* |
| **S4** | Couche B (Storage Box + rclone crypt) + `pg_dump` Supabase hebdomadaire + export du registre | 3 h | S3 |
| **S5** | **Test T1** puis **test T2** | 1 h 30 | S4 |
| **S6** | `app_affaire_ledger` sans `payload_json` + correction du commentaire `app_internal_status` | 1 h | — |
| **S7** | Lot « configuration de déploiement » (XML des tâches, services, `RESTAURATION_INFRA.md`) | 2 h | — |
| **S8** | **Test T3** — l'exercice « le serveur a disparu », **restauration depuis le vault Veeam** | ½ journée | S1 → S7 |

**Total : ≈ 12 h de mise en œuvre + ½ journée d'exercice, pour ≈ 4 € HT par mois**
(dont 3,20 € de couche B ; la couche A est déjà souscrite et facturée à la consommation).

Chemin critique : **D1 → S1/S2 → S4 → S5 → S8.** D2 est indépendant mais daté. S3, S6 et S7
sont détachables et peuvent attendre sans que rien ne se dégrade.

---

## 3. Protocole de test de restauration

**C'est le livrable central de cette note.** Sans ces trois tests, tout ce qui précède reste
une intention. Chaque test dit : **quoi**, **où**, **avec quelles commandes**, **quel critère
prouve que ça a marché**, et **quoi faire s'il échoue**.

Convention : tout se fait dans `C:\Hektor\_restore_test\`, **jamais** dans `C:\Hektor\Projet`
ni dans `C:\Hektor\Backups`. Ce répertoire est jetable et se supprime à la fin.

---

### T1 — Vérification de l'archive de la nuit

**Quoi.** La dernière archive `critical_*.sqlite.gz`.
**Où.** Nulle part : décompression et ouverture **en mémoire**, zéro écriture disque.
**Fréquence.** Mensuel à la main ; à automatiser dans `check_gti_health.py` (§1.4) pour un
passage quotidien.
**Durée.** ≈ 10 secondes.

```bash
python -c "
import gzip, sqlite3, glob, os, datetime
p = max(glob.glob(r'C:\Hektor\Backups\critical\critical_*.sqlite.gz'), key=os.path.getmtime)
age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(p))).total_seconds()/3600
blob = gzip.decompress(open(p,'rb').read())
con = sqlite3.connect(':memory:'); con.deserialize(blob)
print('archive        :', os.path.basename(p))
print('age            : %.1f h' % age)
print('entete SQLite  :', blob[:16] == b'SQLite format 3\x00')
print('integrity      :', con.execute('pragma integrity_check').fetchone()[0])
print('tables         :', con.execute('select count(*) from _backup_manifest').fetchone()[0])
print('app_dossier    :', con.execute('select count(*) from app_dossier').fetchone()[0])
print('id min/max     :', con.execute('select min(id), max(id) from app_dossier').fetchone())
print('id NULL        :', con.execute('select count(*) from app_dossier where id is null').fetchone()[0])
print('doublons hai   :', con.execute('select count(*) from (select hektor_annonce_id from app_dossier group by 1 having count(*)>1)').fetchone()[0])
con.close()
"
```

**Critères de succès — les 7 doivent être vrais :**

| # | Critère | Référence du 18/08 |
|---|---|---|
| 1 | `age` < 30 h | 4,8 h |
| 2 | `entete SQLite` = `True` | True |
| 3 | `integrity` = `ok` | ok |
| 4 | `tables` = **13** (14 après ajout du ledger) | 13 |
| 5 | `app_dossier` ≥ **56 000** et à ±2 % de la base vivante | 56 871 = 56 871 |
| 6 | `id NULL` = **0** | 0 |
| 7 | `doublons hai` = **0** | 0 |

**Si ça échoue.** Ne pas purger l'archive fautive. Relancer
`python phase2\sync\backup_critical.py` à la main, relire
`logs\scheduled\backup_*.log`, comparer avec l'archive de la veille. Un critère 5 en baisse
brutale signale une troncature côté source, pas côté sauvegarde — c'est **plus grave** qu'un
échec de sauvegarde.

---

### T2 — Restauration réelle de `phase2.sqlite` et preuve du mapping d'identité

**Quoi.** Le dernier instantané hebdomadaire `phase2_*.sqlite.gz` (≈ 220 Mo).
**Où.** `C:\Hektor\_restore_test\phase2.sqlite`.
**Fréquence.** Trimestriel, et **obligatoirement après toute modification** de
`backup_critical.py`.
**Durée.** ≈ 1 h dont ≈ 10 min de machine.

**Étape 1 — décompresser dans le bac à sable**

```bash
python -c "
import gzip, glob, os, shutil, pathlib
src = max(glob.glob(r'C:\Hektor\Backups\phase2\phase2_*.sqlite.gz'), key=os.path.getmtime)
dst = pathlib.Path(r'C:\Hektor\_restore_test\phase2.sqlite')
dst.parent.mkdir(parents=True, exist_ok=True)
with gzip.open(src,'rb') as f, open(dst,'wb') as o: shutil.copyfileobj(f, o, 1024*1024)
print('restaure :', dst, round(dst.stat().st_size/1024/1024,1), 'Mo  <-', os.path.basename(src))
"
```

**Étape 2 — intégrité et volumétrie du fichier restauré**

```bash
python -c "
import sqlite3
con = sqlite3.connect(r'file:C:\Hektor\_restore_test\phase2.sqlite?mode=ro', uri=True)
print('integrity     :', con.execute('pragma integrity_check').fetchone()[0])
print('tables        :', con.execute(\"select count(*) from sqlite_master where type='table'\").fetchone()[0])
print('app_dossier   :', con.execute('select count(*) from app_dossier').fetchone()[0])
print('ledger        :', con.execute('select count(*) from app_affaire_ledger').fetchone()[0])
print('id min/max    :', con.execute('select min(id), max(id) from app_dossier').fetchone())
con.close()
"
```

**Étape 3 — LE test qui compte : le mapping résout-il contre Supabase ?**

> **Protocole corrigé le 19/08 après la première exécution réelle.** La version initiale
> joignait sur `app_dossier_id`, en supposant que la valeur portée par Supabase égale
> `phase2.app_dossier.id`. **Cette hypothèse est fausse pour ~91 % des dossiers courants**
> (§0.12). Le test échouait donc pour une raison qui n'avait rien à voir avec la sauvegarde.
> On joint désormais sur les **deux** clés, et on distingue les deux cas.

Échantillon côté Supabase (lecture seule). Prendre 300 paires réparties sur toute la plage,
**et leur empreinte md5** — sans quoi une erreur de recopie serait prise pour une divergence :

```sql
with s as (
  select app_dossier_id, hektor_annonce_id,
         row_number() over (order by app_dossier_id) rn
  from public.app_dossier_current
  where app_dossier_id <= <id_max_de_l_instantane>
)
select count(*),
       string_agg(app_dossier_id || ':' || hektor_annonce_id, ' ' order by app_dossier_id),
       md5(string_agg(app_dossier_id || ':' || hektor_annonce_id, ' ' order by app_dossier_id))
from s where rn % 44 = 0;
```

Confronter à la base restaurée — **vérifier d'abord l'empreinte**, puis les deux clés :

```bash
python -c "
import sqlite3, hashlib, pathlib
ech = pathlib.Path(r'C:\Hektor\_restore_test\echantillon.txt').read_text().strip()
assert hashlib.md5(ech.encode()).hexdigest() == '<md5_annonce_par_supabase>', 'recopie inexacte'
con = sqlite3.connect(r'file:C:\Hektor\_restore_test\phase2.sqlite?mode=ro', uri=True)
par_id = par_hektor = introuvables = divergents = 0
for paire in ech.split():
    aid, hai = paire.split(':')
    r_id  = con.execute('select hektor_annonce_id from app_dossier where id = ?', (int(aid),)).fetchone()
    r_hai = con.execute('select id from app_dossier where hektor_annonce_id = ?', (hai,)).fetchone()
    if r_id and str(r_id[0]) == hai: par_id += 1
    elif r_id and str(r_id[0]) != hai: divergents += 1
    elif r_hai: par_hektor += 1
    else: introuvables += 1
print('par app_dossier.id :', par_id)
print('par hektor_annonce_id :', par_hektor)
print('DIVERGENTS :', divergents)
print('INTROUVABLES :', introuvables)
con.close()
"
```

**Critères de succès :**

| # | Critère | Pourquoi |
|---|---|---|
| 1 | `integrity` = `ok` | le fichier restauré est sain |
| 2 | `app_dossier` ≥ 56 000 | rien n'a été tronqué |
| 3 | `id min/max` cohérent avec la base vivante | les identifiants historiques sont préservés |
| 4 | **`INTROUVABLES` = 0** | tout dossier vu par Supabase se retrouve dans la base restaurée, **par l'une ou l'autre clé** |
| 5 | **`DIVERGENTS` = 0** | **le critère décisif** — quand l'id résout, il pointe le *même* bien Hektor. Une seule divergence signifierait que le mapping a été réémis. |
| 6 | `par_id` + `par_hektor` = total | contrôle de cohérence de l'addition |

**Si `DIVERGENTS` > 0 ou `INTROUVABLES` > 0 : arrêt immédiat et escalade.** Ce n'est alors
pas un problème de sauvegarde mais une atteinte à l'intégrité du modèle de données. Avant de
conclure, **toujours rejouer la même requête sur la base VIVANTE** : si elle donne le même
résultat, la sauvegarde est fidèle et le problème est ailleurs. C'est exactement ce qui s'est
passé le 19/08.

**Ménage.** `Remove-Item -Recurse -Force C:\Hektor\_restore_test`, et consigner le résultat
en une ligne dans une note de suivi.

---

### T3 — L'exercice « le serveur a disparu »

**Quoi.** Tout. **Où.** Une machine neuve — VM jetable, poste de secours, serveur de test.
**Fréquence.** Semestrielle, et une fois **avant** de considérer le chantier clos.
**Durée.** ½ journée. **Ce qui est mesuré : le temps réel de remise en route.**

Règle du jeu : on n'a le droit de toucher **ni** à `C:\Hektor`, **ni** au serveur d'origine.
Uniquement le hors site et le gestionnaire de mots de passe.

**Deux chemins à éprouver, pas un.** Le §0.7 en ajoute un — et c'est désormais le chemin
principal. Il faut vérifier **les deux**, parce qu'ils échouent pour des raisons différentes.

**Chemin 1 — la restauration d'image (le chemin nominal, depuis le vault Veeam)**

| # | Étape | Critère de succès |
|---|---|---|
| 1 | Restaurer l'image complète depuis la VSPC vers une machine de test | La restauration aboutit ; le volume monte |
| 2 | Contrôler les données | `phase2.sqlite` s'ouvre, `integrity_check = ok`, ≥ 56 000 `app_dossier` — **c'est le test qui valide la cohérence VSS sur une base en WAL** |
| 3 | Contrôler les documents | Décompte de fichiers à ±1 % de la source ; **10 PDF tirés au hasard s'ouvrent** |
| 4 | Mesurer | **Combien de temps a pris la restauration de 120 Go ?** C'est le RTO réel. |

**Chemin 2 — la reconstruction pièce par pièce (le chemin de secours, si le vault est
inaccessible : compte OVH perdu, sauvegarde trop ancienne, image corrompue)**

| # | Étape | Source | Critère de succès |
|---|---|---|---|
| 1 | Cloner le dépôt | `github.com/GTIImmo/Groupe-GTI` | Le dépôt se clone et `main` contient les 2 commits de D0 |
| 2 | Restaurer les secrets | coffre + copie chiffrée couche B | Les 6 fichiers sont reconstitués ; **la passe-phrase a été retrouvée sans passer par le serveur** |
| 3 | Restaurer `phase2.sqlite` | couche B | T2 étapes 1-2 au vert |
| 4 | Restaurer `hektor.sqlite` | instantané mensuel (§4) | `integrity_check = ok` |
| 5 | Restaurer Supabase | `pg_dump` hebdomadaire → projet neuf ou branche | `\dt` liste ≥ 100 tables ; les fonctions RPC existent ; `app_agent_prompt` a ses 3 lignes |
| 6 | Les documents | — | **Constat assumé : par ce chemin, ils sont perdus.** Les 32 Go ne sont dans aucune couche B. Reste la copie partielle du bucket Supabase (§0.1), élaguée des biens archivés. **Ce trou est le prix de la simplicité ; il doit être écrit, pas découvert.** |
| 7 | Reconstruire l'infra | `RESTAURATION_INFRA.md` + XML des tâches | Les 5 tâches et les 4 services sont recréés à l'identique |
| 8 | **Preuve de bout en bout** | — | **On choisit un bien à l'avance** (par exemple `VA6482`) : l'application démarre, la fiche s'affiche, avec **son mandat, ses documents, son estimation et son historique d'affaires**. |

**Le critère 8 est le seul qui compte vraiment.** Les sept autres vérifient des fichiers ;
celui-là vérifie que le **système** fonctionne. On note le temps écoulé : c'est le RTO réel,
et c'est ce chiffre — pas le plan — qu'il faudra présenter le jour où quelqu'un demandera
combien de temps prend une remise en route.

**Livrable de T3 :** une note de trois lignes — date, temps réel constaté, ce qui a bloqué.
Ce qui a bloqué devient le lot de travail suivant.

---

## 4. Ce que je propose de NE PAS faire

Un plan de sauvegarde trop ambitieux ne tient pas six mois. Voici ce que j'écarte
délibérément, et pourquoi.

**1. Ne pas prendre l'option PITR de Supabase (≈ 100 $/mois).**
Elle achète un RPO de 2 minutes sur des données majoritairement re-poussables depuis les
sources locales. Tant qu'il manque une copie hors site à 0 €, dépenser 1 100 €/an sur ce
poste est une inversion de priorité. À rouvrir **le jour où Supabase deviendra la source de
vérité** — c'est-à-dire quand le chantier de découplage app-first aboutira, pas avant.

**2. Ne pas sauvegarder `hektor.sqlite` chaque nuit.**
3,63 Go, et c'est un **miroir de Hektor** : tant que Hektor vit, il se re-tire. Le niveau 4
n'a jamais été planifié — c'était le bon choix. Nuance importante : le projet existe
précisément pour survivre à la disparition de Hektor, donc ce fichier a une valeur de
police d'assurance. Je propose **un instantané mensuel** poussé hors site (≈ 400 à 600 Mo
compressés estimés, rétention 2 copies) — pas un quotidien. Les tables de ce fichier qui
sont réellement irremplaçables (`sync_meta`, `hektor_price_change_event`, les 3 caches de
scrape) sont **déjà** dans le niveau 1, chaque nuit.

**3. Ne pas sauvegarder les sessions Playwright.** Régénérables par la connexion automatisée,
TOTP compris. Les archiver revient à stocker des jetons de session vivants — un risque de
plus, un bénéfice nul.

**4. Ne pas monter la cible hors site en lecteur réseau permanent.**
Ni lettre de lecteur, ni CIFS, ni NFS monté à demeure. Une cible montée en permanence est
chiffrée en même temps que la source. Les identifiants ne servent qu'à l'instant du push.
C'est aussi la raison pour laquelle je préfère `rclone` à `robocopy`, malgré la présence de
`robocopy` sur la machine.

**5. Ne PAS construire un miroir des 32 Go de documents.** *(Révisé après §0.7 — c'était ma
recommandation initiale.)* Le Backup Agent les embarque déjà dans l'image complète, hors
site, dans un autre datacenter, immuable 14 jours. Un miroir `rclone` en plus serait une
troisième copie, à construire, à surveiller et à payer — pour couvrir un risque déjà
couvert. **On supprime le zip, et on ne met rien à la place.** Si un jour un miroir devient
utile malgré tout, la règle reste `rclone copy` additif, **jamais** `sync` ni
`robocopy /MIR` : ceux-là propagent les suppressions et transforment le miroir en
amplificateur de sinistre.

**6. Ne pas déployer un moteur de sauvegarde dédupliqué (Borg, Restic, Duplicati) sur les
155 Go.** Séduisant sur le papier, doublement inutile ici : Veeam fait déjà de l'incrémental
dédupliqué, et l'arborescence est un stock **immuable, en écriture unique** — il n'y a
presque rien à dédupliquer. On paierait la complexité au pire moment, celui de la
restauration sous stress.

**7. Ne pas acheter de NAS ni de disque externe sur site.** Il n'y a pas de second volume,
c'est un serveur dédié distant — brancher un disque suppose une intervention physique en
datacenter. Et un disque sur site ne couvre ni l'incendie, ni le vol, ni la perte du
fournisseur. Le Backup Agent fait mieux, il est déjà payé.

**8. Ne pas ouvrir l'offre « OVH Backup Storage 500 Go » ni installer *Windows Server
Backup*.** *(Révisé après §0.7.)* Le Backup Agent rend la première redondante pour le gros
volume, la couche B la rend redondante pour le petit, et la seconde n'apporte rien qu'un
agent Veeam ne fasse déjà mieux. Deux dispositifs de sauvegarde concurrents sur la même
machine, c'est deux fois plus à surveiller et deux fois plus d'occasions de croire qu'on est
protégé par l'autre.

**9. Ne pas attendre la fin du chantier de découplage app-first.** Ce chantier durera des
mois. Le risque, lui, est ouvert cette nuit.

**10. Ne pas chercher à reconstituer l'historique des cinq semaines de schéma manquantes**
(28/03 → 04/05). Le `pg_dump` couvre l'état final, ce qui suffit à restaurer. Reconstituer
l'historique est de l'archéologie sans valeur opérationnelle.

---

## 5. Ce que je ne peux pas trancher — décisions qui t'appartiennent

**1. La couche B est-elle justifiée, maintenant que la couche A existe ?**
*(Question reformulée après §0.7.)* Le Backup Agent, une fois installé, couvre la perte du
serveur, l'incendie et le rançongiciel — pour ≈ 0,55 à 0,90 € HT/mois déjà souscrits. Les
3,20 € de la couche B achètent trois choses qu'il ne donne pas : **90 jours d'historique**
au lieu de 14, une **restauration granulaire en 10 secondes** au lieu du montage d'une image
de 120 Go, et la **décorrélation du compte OVH**. **Ma recommandation : oui, les 3,20 €.**
Mais c'est un arbitrage de risque, pas un fait technique — et il est moins évident
qu'avant la découverte du §0.7.

**1bis. Rétention Veeam : 14 jours (standard) ou 30 (étendue) ?**
14 jours est court pour une erreur logique découverte tardivement. La rétention étendue se
paie en stockage supplémentaire (0,007 € HT/Go/mois). Si la couche B est retenue avec ses
90 jours sur le petit jeu, **14 jours suffisent** sur l'image complète — les deux se
complètent. Si la couche B est écartée, **il faut passer à 30**. Les deux décisions sont
liées ; à trancher ensemble.

**1ter. À vérifier d'un clic : l'onglet « Facturation » de cette page.**
Le modèle est à la consommation ; un vault vide se facture ≈ 0 €. Confirme-le, et
regarde ce que devient la ligne après la première sauvegarde complète — c'est le seul
chiffre réel, mes 0,55 à 0,90 € sont une estimation à partir des 122,2 Go occupés.

**2. Quelle perte est acceptable, en heures ?**
Le dispositif actuel implique **24 h** (sauvegarde à 07:00). Le jeu critique pèse 9,2 Mo :
le pousser **toutes les heures** ne coûte rien de plus, ni en argent, ni en charge machine.
Question directe : **perdre jusqu'à 24 h de saisie est-il acceptable, ou vise-t-on l'heure ?**
Ma recommandation : l'heure pour les 9,2 Mo, 24 h pour le reste. Mais c'est ta tolérance,
pas la mienne.

**3. Qui d'autre détient la passe-phrase du coffre ?**
Si tu es seul à la connaître, le dispositif a un facteur d'autobus de 1 : la restauration
devient impossible en ton absence. Ce n'est pas une question technique — c'est une décision
d'organisation, et elle est plus importante que le choix de la destination.

**4. Le rattrapage des 318 000 photos est-il confirmé, et à quelle échéance ?**
Toute la volumétrie en dépend : **32 Go aujourd'hui, ≈ 155 Go à l'arrivée.** Ce n'est plus
un problème de dimensionnement — le vault n'a pas de plafond — mais un problème de
**facture** : le poste passerait de ≈ 0,80 € à ≈ 2 € HT/mois. Reste sous le seuil de
l'anecdote, mais autant le savoir avant de le voir apparaître.

**~~4bis. À quelle heure l'agent Veeam déclenche-t-il sa sauvegarde ?~~ — RÉGLÉ le 18/08.**
Relevé dans `Svc.VeeamEndpointBackup.log` à 18:08 :

```
Schedule options (enabled): Next run time: [18/08/2026 22:00:00]
Daily options: [Enabled: True, Time: 22:00:00, Days: Sunday..Saturday]
Retry times on failure: [3], Retry timeout: [10 min]
```

**Sauvegarde quotidienne à 22:00, tous les jours, avec 3 tentatives espacées de 10 minutes
en cas d'échec.** La fenêtre est **bonne** : aucun conflit avec le pipeline de 05:30 ni avec
la sauvegarde locale de 07:00. Rien à décaler. Rythme de la journée :

| Heure | Quoi |
|---|---|
| 05:30 | Pipeline GTI |
| 07:00 | Sauvegarde locale (7,7 Mo ; + 220 Mo le dimanche) |
| **22:00** | **Sauvegarde Veeam → vault de Roubaix** |

**5. Le feu vert pour la modification d'avant dimanche.**
Le garde-fou du niveau 3 (§1.2) est le **seul** développement que je demande avant le 23/08.
30 minutes, additif, derrière un interrupteur, réversible. Sans lui, dimanche 07:00 produit
≈ 30 Go d'archive pour rien. **Sans ton accord explicite, je n'y touche pas** — et il faudra
alors choisir le repli (déclencheur lundi-samedi), qui a le défaut de supprimer aussi le
niveau 1 du dimanche.

**6. Le fournisseur de la couche B.**
J'ai retenu Hetzner Storage Box pour le prix, les snapshots inclus et le trafic illimité.
Si tu préfères un fournisseur français ou déjà contractualisé (Scaleway, Infomaniak, OVH
Object Storage sur un **autre** compte), le plan ne change pas d'un iota — seule la commande
`rclone` change. C'est ton choix, pas une contrainte technique.

---

## 6. Annexe — mesures du 18/08/2026, méthode

Toutes les valeurs de cette note ont été mesurées le 18/08/2026 entre 11:30 et 12:00,
**en lecture seule**. Aucune écriture sur le disque projet, aucune écriture sur Supabase
(uniquement `get_project`, `get_organization`, `list_migrations`, `execute_sql` en `select`).
Les bases SQLite ont été ouvertes en `mode=ro`. L'archive de sauvegarde a été vérifiée
**en mémoire**, sans être écrite sur le disque.

| Objet | Mesure |
|---|---|
| `C:\Hektor\Backups` | 9 fichiers, 310 Mo — `critical` 7 fichiers (dont **2 de 0 octet**, 17/08 11:50), `documents` 1 (51,3 Mo), `phase2` 1 (220 Mo) |
| Dernière archive critique | `critical_20260818_070002.sqlite.gz`, 8,11 Mo, **integrity ok**, 13 tables, 56 871 `app_dossier` |
| `phase2.sqlite` | 1,83 Go (WAL) |
| `data\hektor.sqlite` | 3,63 Go (WAL) |
| `HektorConsoleDocuments` | 22 403 fichiers, 32,44 Go — 17 635 PDF (27,88 Go), 3 575 JPG (3,54 Go) |
| Écrits le 18/08 | 8 186 fichiers, 11,1 Go |
| Compressibilité PDF | **6,3 %** (échantillon 60 fichiers, 155 Mo) |
| Débit lecture + deflate | **28 Mo/s** → 32,4 Go en ≈ 20 min |
| `app_affaire_ledger` | 28 979 lignes ; `payload_json` 106,2 Mo bruts ; **sans `payload_json` : 1,45 Mo gzip** |
| `app_internal_status` | 22 218 lignes — 22 198 `bootstrap_phase2`, 20 `push_single_annonce_to_supabase`, **0 humain** |
| Supabase | plan **Pro**, `eu-west-2`, PG 17.6.1.084, **1 768 Mo**, 107 tables, **rétention 7 j**, sauvegardes **physiques non téléchargeables** |
| Supabase Storage | `hektor-console-documents` : **21 141 objets, 32 Go**, **hors périmètre des sauvegardes** |
| Registre de migrations | `supabase_migrations.schema_migrations` : **183 migrations**, SQL inclus, 288 Ko, 04/05 → 17/08 |
| Dépendances `app_dossier_id` | **32 tables + 10 vues** dans `public`, **0 clé étrangère** |
| Tâches planifiées | 5 tâches GTI, toutes `LastTaskResult = 0` ; **`GTI Sauvegarde` seule en `Interactive`**, les 4 autres en `S4U` |
| Secrets | 6 fichiers, **6 792 octets** au total ; + `Console\.env.txt` (2 104 o) et `Console\token_dump.json` (12 406 o) à supprimer |
| Sessions Playwright | 7 fichiers, dont 4 actifs rafraîchis ce matin (≈ 17 Ko chacun) |
| Git | `main` @ `0a06fdd`, **2 commits non poussés**, 12 suppressions stagées (fichiers **absents du disque**), 90 fichiers non suivis, `.git` = 4,4 Go |
| Matériel | OVH `ns31851120`, 2 × NVMe 894,3 Go `Healthy`, **1 seul volume C:** 893,8 Go / 771,6 Go libres |
| Volume C: occupé | **122,2 Go** — base de l'estimation du coût du vault Veeam |
| **OVH Backup Agent** | Tenant `vspc-tenant-734935`, **Actif**, vault `eu-west-rbx` (Roubaix), créé le **19/05/2026**, renouvellement auto au 01/09/2026 |
| **Agent Veeam sur la machine** | **ABSENT** — aucun service, aucun répertoire `Veeam`, aucune entrée dans les programmes installés, aucun processus. **Rien n'a jamais été sauvegardé.** |

**Sources externes consultées :**
- [Supabase — Database Backups](https://supabase.com/docs/guides/platform/backups)
- [Supabase — Manage PITR usage](https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery)
- [OVHcloud — Backup Agent, présentation du produit](https://docs.ovhcloud.com/en/guides/storage-and-backup/backup-agent/product-presentation)
- [OVHcloud — Backup Agent, restrictions connues](https://docs.ovhcloud.com/fr/guides/storage-and-backup/backup-agent/restrictions)
- [OVHcloud — Backup Agent, première configuration](https://docs.ovhcloud.com/en/guides/storage-and-backup/backup-agent/first-configuration)
- [IT-Connect — OVHcloud Backup Agent, solution basée sur Veeam](https://www.it-connect.fr/ovhcloud-lance-backup-agent-une-solution-basee-sur-veeam-pour-la-sauvegarde-des-serveurs-dedies/) *(source du tarif 0,007 € HT/Go et de la licence incluse — à confirmer sur la facture)*
- [Hetzner — Storage Box](https://www.hetzner.com/storage/storage-box/) · [BX11](https://www.hetzner.com/storage/storage-box/bx11/) · [BX21](https://www.hetzner.com/storage/storage-box/bx21/)

---

## 7. En une phrase

Le dispositif du 17/08 est bien conçu et **il fonctionne** — je l'ai vérifié ; et la sortie
du serveur qui lui manquait **est déjà payée depuis le 19 mai, elle n'a simplement jamais
été branchée**. Il reste donc trois choses : **installer l'agent Veeam** (1 h), **poser le
garde-fou avant dimanche** (30 min), et **restaurer pour de vrai au moins une fois**. Cela
représente 12 heures de travail, ≈ 4 € HT par mois, et une demi-journée d'exercice.

**Rien ne sera codé sans ton feu vert, question par question.**
