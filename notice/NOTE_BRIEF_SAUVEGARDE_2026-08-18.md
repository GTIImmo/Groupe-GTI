# Brief — chantier Sauvegarde du serveur et du projet

Date : 2026-08-18
Statut : **brief d'entrée de chantier. Rien n'est décidé, rien ne doit être codé.**
Origine : audit complet du projet (6 analyses en lecture seule, 18/08/2026).

Ce document existe pour qu'une session dédiée à la sauvegarde n'ait pas à refaire
l'exploration. Tous les chiffres ci-dessous ont été **vérifiés** le 18/08/2026.

---

## 1. Ce qui existe déjà

Dispositif en place depuis le **17/08/2026** (moins de 48 h de vie au moment de ce brief).

| Élément | Valeur |
|---|---|
| Script | `phase2/sync/backup_critical.py` |
| Lanceur | `scheduled/run_backup.ps1` |
| Tâche planifiée Windows | `GTI Sauvegarde`, **07:00**, compte `admin` |
| Destination | `C:\Hektor\Backups` (hors arbre projet, volontaire) |
| Commit | `70b2b09` — « feat(backup): sauvegarde des donnees locales irremplacables (Phase 0.1) » |

### Les 4 niveaux

| Niveau | Fréquence | Contenu | Poids | Rétention |
|---|---|---|---|---|
| 1 | quotidien | 13 tables critiques exportées en JSON gzip | **7,7 Mo, 3 secondes** | 90 j |
| 2 | dimanche | `VACUUM INTO` de `phase2.sqlite` | ~220 Mo | 28 j |
| 3 | dimanche | zip de `C:\Hektor\HektorConsoleDocuments` | voir §3 | 28 j |
| 4 | `--full` uniquement | `VACUUM INTO` de `hektor.sqlite` (3,89 Go) | — | 60 j |

Le niveau 4 **n'est jamais planifié et n'a jamais été exécuté**.

### Trois choix de conception à conserver

1. **`VACUUM INTO` obligatoire.** Les deux bases sont en mode WAL. Une copie de fichier
   simple produirait une base incohérente. `VACUUM INTO` est le seul moyen d'obtenir un
   instantané cohérent sans arrêter les écritures.
2. **Tâche séparée à 07:00, hors pipeline.** Justification écrite dans `run_backup.ps1` :
   « le run quotidien se termine vers 06:25 ; on sauvegarde APRÈS (données fraîches) mais
   dans une tâche SÉPARÉE, pour que la sauvegarde ait lieu même les jours où le pipeline
   échoue — précisément les jours où l'on peut en avoir besoin. »
3. Toutes les lectures se font en `mode=ro` : le script ne peut pas altérer les sources.

---

## 2. Ce qui est irremplaçable, et pourquoi

### Le fichier le plus critique du projet : `phase2/phase2.sqlite`, table `app_dossier`

- 56 871 lignes. Clé `id INTEGER PRIMARY KEY AUTOINCREMENT`, `UNIQUE(hektor_annonce_id)`.
- Les identifiants réels vont de **118 à 5 132 231** : non séquentiels, marqués par l'histoire
  du projet. Une régénération réattribuerait d'autres identifiants.
- **43 objets dépendent de cet identifiant** : 32 tables Supabase + 10 vues + 11 objets locaux.
- **`fk_vers_app_dossier_current = 0`** — vérifié : *aucune* contrainte de clé étrangère ne
  protège ce lien dans Postgres. Il est purement conventionnel.

> Conséquence : la perte de ce fichier orpheline silencieusement 32 tables Supabase,
> **sans qu'aucune erreur ne remonte nulle part**. C'est le point de défaillance unique
> du modèle de données.

### Les 13 tables du niveau 1 (déjà couvertes)

Depuis `phase2.sqlite` : `app_dossier`, `app_internal_status` (22 218), `app_diffusion_target` (42),
`app_diffusion_agency_target` (34), `app_diffusion_refusal_reason` (9), `app_contact_audit_run` (93).

Depuis `hektor.sqlite` : `sync_meta` (4 curseurs de delta — sans eux, re-pull complet),
`hektor_price_change_event` (163 — dérivé de diffs entre snapshots, **non re-dérivable**),
`hektor_contact_missing_detail` (43 999), `hektor_annonce_chauffage_detail` (56 798),
`hektor_annonce_console_detail` (155), `hektor_annonce_draft_state` (435), `hektor_draft_sweep_meta`.

Les trois caches de scrape sont des données **absentes de l'API Hektor**, obtenues par
navigateur automatisé. Leur perte impose plusieurs jours de re-scrape.

### Ce qui N'EST PAS couvert et devrait peut-être l'être — à trancher

| Élément | Volume | Enjeu |
|---|---|---|
| **`app_affaire_ledger`** | 28 979 lignes | Registre d'affaires app-owned, conçu pour survivre à Hektor. Non listé dans les 13 tables. Existe aussi côté Supabase, donc partiellement redondant — à qualifier. |
| **Les secrets** | 6 fichiers | Voir §4. Hors git **et** hors sauvegarde. |
| **`Console/sessions/storage_state_*.json`** | 4 fichiers | Sessions Playwright. Leur perte est classée `critical` par le moniteur. Non sauvegardés. |
| **Configuration de déploiement** | — | Aucun `vercel.json`, `render.yaml`, `Dockerfile`. Tout vit dans les dashboards SaaS. Non reproductible, non sauvegardé. |
| **Le schéma Supabase** | 143 patchs `.sql` | Aucun registre de migrations. En cas de restauration, **on ne saurait pas quels patchs rejouer**. |
| **Supabase lui-même** | 85 tables | Quelle sauvegarde native le plan offre-t-il ? **Non vérifié.** À établir. |

### Point à trancher au passage

`app_internal_status` (22 218 lignes) figure dans les tables « saisies non rejouables »
(`backup_critical.py:69`), **mais** `bootstrap_phase2.py:210-242` la réécrit chaque nuit
(`updated_by='bootstrap_phase2'`). Les deux affirmations sont incompatibles : soit elle porte
de la saisie humaine et elle est écrasée chaque nuit, soit elle est dérivée et n'a pas à
figurer dans la sauvegarde critique. **À trancher.**

---

## 3. Les cinq problèmes constatés le 18/08

### P1 — Il n'existe aucune copie hors site. C'est le risque dominant.

`Get-Volume` ne retourne **qu'un seul volume : `C:`** (893,8 Go, 771,7 libres).
Aucun second disque, aucun lecteur réseau, aucun montage cloud.

Sur ce même volume cohabitent : le code, les bases SQLite sources, **les sauvegardes**,
les secrets, et les 33 Go de documents rapatriés.

> Une panne disque, un ransomware ou la perte du serveur emporte **la source et sa
> sauvegarde ensemble**. Le dispositif actuel protège contre l'erreur logique
> (suppression accidentelle, bug de pipeline), pas contre la perte du support.

Ordre de grandeur : le niveau 1 fait **7,7 Mo par nuit**. N'importe quelle destination
distante rend ce risque nul pour un coût dérisoire.

### P2 — La sauvegarde n'a jamais été restaurée

Elle tourne depuis le 17/08. Tant qu'un essai de restauration n'a pas été fait,
**on ne sait pas qu'elle fonctionne** — on sait seulement qu'elle produit des fichiers.

Aggravant : `C:\Hektor\Backups\critical\` contient déjà **2 fichiers de 0 octet**
(runs plantés du 17/08). Preuve qu'un run peut « produire » un fichier inexploitable
sans que rien ne le signale. `purge_old` ne les supprimera qu'au bout de 90 jours.
Aucune vérification d'intégrité n'existe.

### P3 — Un échec de sauvegarde est structurellement silencieux

Trois verrous cumulés :

1. `run_backup.ps1` avale l'exception dans son `catch` et **sort en code 0** →
   `LastTaskResult` de la tâche Windows est toujours 0, quoi qu'il arrive.
2. `GTI Sauvegarde` **n'est pas dans la liste des tâches surveillées** par
   `monitoring/check_gti_health.py` (défaut : `GTI Quotidien, GTI Recherches Actives,
   GTI Health Monitor, GTI Relances Email`).
3. Aucune sonde ne regarde l'âge ni la taille des archives dans `C:\Hektor\Backups`.

> La sauvegarde peut échouer chaque nuit sans que personne ne l'apprenne.

### P4 — Les documents ne sont plus sauvegardés, d'un facteur 570

| Mesure | Valeur |
|---|---|
| `C:\Hektor\HektorConsoleDocuments` | **22 367 fichiers, 33,2 Go** |
| Unique archive documents existante | **51,3 Mo**, datée du 17/08 12:00 |
| Fichiers antérieurs à l'archive (capturés) | 41 fichiers / 57 Mo |
| Fichiers postérieurs (**non capturés**) | **22 335 fichiers / 33 Go** |

→ **99,8 % des documents locaux ne sont aujourd'hui dans aucune sauvegarde.**
Le rapatriement massif des 17-18/08 a eu lieu *après* la seule archive produite.
Les commentaires du code (« ~58 Mo », « empreinte stable ~1,8 Go ») sont périmés.

**Échéance immédiate : dimanche 23/08**, `shutil.make_archive` va tenter de zipper 33 Go
de PDF déjà compressés en un passage synchrone. Avec 28 jours de rétention, cela produirait
≈ 130 Go d'archives quasi identiques.

### P5 — Asymétrie de configuration de la tâche

Les quatre autres tâches GTI sont en `LogonType = S4U` (s'exécutent sans session ouverte).
**`GTI Sauvegarde` est la seule en `Interactive`** — son comportement dépend de la présence
d'une session `admin`. Elle a fonctionné les 17 et 18/08, mais c'est une asymétrie non
intentionnelle sur précisément la tâche la moins surveillée.

---

## 4. Les secrets — hors git ET hors sauvegarde

L'hygiène git est **excellente** : `.gitignore` défensif, `git log --all` sur les fichiers
sensibles ne retourne rien. **Aucune fuite historique sur aucune branche.** Rien à corriger
de ce côté.

Le risque est ailleurs : ces fichiers n'existent qu'à un seul endroit, en clair, sur le
disque unique du P1. Leur perte impose de régénérer chaque credential auprès de Hektor,
Google, Supabase, Matterport et GitHub.

| Fichier | Contenu |
|---|---|
| `secrets/google-workspace-service-account.json` | clé privée RSA avec **délégation domaine-wide** |
| `apps/hektor-v1/.env` | `SUPABASE_SERVICE_ROLE_KEY` (contourne toute la RLS) + mot de passe SMTP |
| `Console/.env` | `HEKTOR_LOGIN`, `HEKTOR_PASSWORD`, **`HEKTOR_TOTP_SECRET`** |
| `.env` (racine) | `OPENAI_API_KEY`, `HEKTOR_CLIENT_SECRET` |
| `matterport/.env` | identifiants Matterport |
| `Ecrans Android/github_token.txt` | jeton GitHub |

Remarque de sécurité à traiter séparément : le secret TOTP stocké **à côté** du mot de passe
annule la valeur du second facteur. Deux fichiers inutiles à supprimer au passage :
`Console/.env.txt` (doublon périmé du 19/05, lu par aucun code) et `Console/token_dump.json`.

---

## 5. Ce qu'il reste à décider — les questions du chantier

Aucune n'a de réponse aujourd'hui. Classées par urgence.

1. **Destination hors site.** Quelle cible (disque externe, NAS, stockage objet, rclone vers
   un fournisseur) ? Quel coût mensuel acceptable ? Le chiffrement au repos est-il exigé,
   sachant que les secrets pourraient y figurer ? — *urgence : haute*
2. **Les 33 Go de documents.** Archive monolithique hebdomadaire (intenable) ou miroir
   incrémental (robocopy / rclone) ? Décision à prendre **avant le dimanche 23/08**.
   — *urgence : haute, avec échéance*
3. **Protocole de test de restauration.** Quoi restaurer, où, avec quel critère de succès,
   à quelle fréquence ? Sans ce test, tout le reste est une hypothèse. — *urgence : haute*
4. **Surveillance.** Faire remonter le code de sortie de `run_backup.ps1`, ajouter
   `GTI Sauvegarde` aux tâches surveillées, ajouter une sonde d'âge/taille sur
   `C:\Hektor\Backups`, aligner la tâche sur S4U. — *urgence : moyenne*
5. **Périmètre.** Ajouter `app_affaire_ledger` ? Les sessions Playwright ? La configuration
   de déploiement (en la matérialisant enfin en fichiers versionnés) ? — *urgence : moyenne*
6. **Les secrets.** Où et comment ? Un coffre séparé, ou dans la sauvegarde chiffrée ?
   — *urgence : moyenne*
7. **Supabase.** Quelle sauvegarde le plan actuel fournit-il, et sur quelle profondeur ?
   Faut-il un export propre en complément ? — *urgence : à établir, non vérifié*
8. **Le schéma SQL.** Les 143 patchs sans registre rendent une restauration Supabase
   non reproductible. Traiter ce point ici ou dans un chantier séparé ?
   — *urgence : basse, mais bloquant en cas de sinistre réel*

---

## 6. Règles de conduite du projet — à respecter

Extraites du plan de développement en vigueur (`PLAN_DEV_APRES_AUDIT_COMPLET_2026-08-18.md`) :

> « On ajoute, on ne remplace jamais. »
> « Tout passe derrière un interrupteur. »
> « **Rien n'est codé sans un feu vert explicite.** Une étude, une proposition, ton accord,
>   puis le code — jamais l'inverse. »
> « Rien n'est déployé sans être vérifié sur un bien de test. »

Deux règles d'exploitation supplémentaires, issues de l'historique du projet :

- **Stager les fichiers un par un.** Jamais `git add .`.
- ⚠️ **Ne jamais faire `git commit -a` en l'état.** L'index contient actuellement
  **12 suppressions stagées** portant sur les notes du chantier d'indépendance
  (`notice/*_2026-08-08.md` et `notice/*_2026-08-17.md`). Elles sont encore récupérables par
  `git show HEAD:notice/<fichier>` ; un commit qui valide l'index les effacerait du HEAD.

---

## 7. État de référence, mesuré le 18/08/2026

```
C:\Hektor\Backups                      9 fichiers, 309,6 Mo, le plus ancien du 17/08 11:50
  critical\                            dont 2 fichiers de 0 octet (runs plantés du 17/08)
  documents\                           1 archive de 51,3 Mo (17/08 12:00)

C:\Hektor\HektorConsoleDocuments       22 367 fichiers, 33,2 Go
C:\Hektor\Projet\data\hektor.sqlite    3,89 Go (WAL)
C:\Hektor\Projet\phase2\phase2.sqlite  1,97 Go (WAL) — archive VACUUM INTO ~220 Mo
Volume C:                              893,8 Go total, 771,7 Go libres — SEUL VOLUME

Depot git                              C:\Hektor\Projet (et non C:\Hektor)
Dernier commit                         0a06fdd
origin/main                            4cc7936 — 2 commits locaux NON POUSSES
git status                             12 suppressions stagees, 89 fichiers non suivis
```
