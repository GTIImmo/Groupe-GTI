# CHANTIER ⑤ — LES GESTES CASSÉS (5a → 5i)

> Ouvert le 08/10/2026. Source : `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md` §2 ⑤ et §3.
> Méthode (Frédéric, 08/10) : **audit du sujet → explication des correctifs → « vas-y » →
> code → contrôle du résultat → documents**. Un point à la fois, dans l'ordre 5a → 5i.
> Toute explication de correctif porte la rubrique **« ce que ça pourrait casser ailleurs »**.

## Les points et leur état

**État au 08/10 au soir : les 9 points sont traités. Le chantier est FINI.**

| # | Le geste cassé | Objet | État |
|---|---|---|---|
| 5a | Désarchiver une annonce | Annonce | ✅ **prouvé en réel** (VA2380, done en 43 s) — + **5a bis** le bouton, déployé · + **5a ter** ouvrir une archive sans Hektor (2 s) |
| 5b | Modifier un mandant depuis sa carte | Mandant | ✅ **prouvé en réel** (bien 62774, Hektor modifié en 26 s) |
| 5c | Premier n° de mandat demandé depuis l'app | Mandat | 🧪 la date était un **FAUX** de l'audit ; vrai défaut = décalage d'horaire, étape de descente ajoutée (28 s) — **attend le run du 09/10** |
| 5d | Filet du rattachement sur la mauvaise clé | Mandant | ✅ **prouvé en réel** (`relation_etablie: done` en 28 s) ; le filet du REFUS reste non éprouvé |
| 5e | Retirer puis rattacher le même mandant | Mandant | ✅ morceau A **prouvé en réel** (`retire_le` → NULL sans renuméroter) · 🧪 morceau B (le run ne doit pas reposer le retrait) **attend le run du 09/10** |
| 5f | Retour d'état après un échec passager (offre / compromis) | Transaction | ✅ actif, **éprouvé hors ligne 6/6** — c'était la seconde moitié de C.4-bis (29/08). Reste : l'abandon RÉEL (5 tentatives ou « abandon » humain) → chantier ④ |
| 5g | Supprimer un contact : le nettoyage local rate sa cible | Contact | ✅ **prouvé en réel** (contact 10355757, liens physiquement effacés des deux côtés) |
| 5h | Mandant créé en échec : rien n'est défait | Mandant | ✅ sentinelle `contact_sans_numero_hektor` posée, lue par le moniteur, **verte** · options B/C (marqueur à l'écran, bouton « réessayer ») non faites |
| 5i | Conflit causé par l'app elle-même | Annonce | 🔧 codé, `node --check` ✔ — **DORMANT** jusqu'au redémarrage des 4 workers, **non éprouvé en réel** (mode opératoire en fin de note) |

---

## 5a — DÉSARCHIVER EST IMPOSSIBLE

### Étape 1 — Audit du 08/10/2026 (lecture seule) · verdict : **CONFIRMÉ**

**Le geste.** Trois boutons « Désarchiver » dans l'app, tous branchés sur le même chemin :
`App.tsx:27744` (menu de la fiche complète), `App.tsx:29702` (bandeau « fiche consultée depuis
l'index léger »), `App.tsx:34064` (mobile) → `handleRestoreHektorAnnonce` (`App.tsx:13857`) →
`createRestoreHektorAnnonceJob` (`lib/api.ts:9552`) → RPC `app_restore_annonce_optimistic`.

**Ce que fait la fonction aujourd'hui** (`pg_get_functiondef`, mesuré le 08/10 09:20) :
sa toute première ligne est
`select * into d from app_dossier_current where app_dossier_id = target_dossier_id;`
puis `if not found then raise exception 'dossier_not_found'`.

**Pourquoi c'est impossible.** Les archives ne sont PAS dans `app_dossier_current` :

| mesure (08/10, Supabase) | résultat |
|---|---|
| `app_archive_annonce_index_current` | **35 317** lignes, toutes `archive='1'` |
| ces archives dont le n° Hektor existe dans `app_dossier_current` | **0** |
| `app_dossier_current` | 13 467 lignes, dont `archive='1'` : **0** |

`app_dossier_current` est une **table** (`relkind='r'`), pas une vue : rien n'y rend les
archives visibles. Et l'index des archives **n'a pas de colonne `app_dossier_id`** (sa clé
primaire est `hektor_annonce_id`, son identifiant interne est `app_archive_id`).

**Ce que l'écran envoie donc.** `lightweightIndexRowToDossier` (`api.ts:2618`) fabrique
`app_dossier_id = Number(row.app_archive_id ?? …)`. Le numéro envoyé à la RPC est donc un
**`app_archive_id`**, qui n'est jamais un `app_dossier_id` : mesuré, **0** des 35 317
`app_archive_id` existe comme `app_dossier_id` (les plages se chevauchent pourtant :
15 633 → 7 344 118 contre 118 → 10 000 000 ; aucune collision aujourd'hui, mais rien ne
l'interdit).
→ L'utilisateur voit le message brut **« dossier_not_found »** (`App.tsx:13869`,
`setErrorMessage(error.message)`). Ce n'est pas un échec silencieux : c'est un geste
impossible, avec un message incompréhensible.

**Depuis quand.** Commit `e7b9df7` du **30/08/2026 à 09:43:39 +0200** (« C.4 : archiver et
desarchiver ecrivent chez nous d-abord »). Avant, le front **insérait le travail directement**
dans `app_console_job` avec `hektor_annonce_id` (diff de `api.ts` dans ce commit) : le
`app_dossier_id` n'était qu'une colonne, jamais une condition. Le passage par la RPC a ajouté
la condition — et l'a cassé.

**Preuve par les travaux.** `app_console_job`, `job_type='restore_hektor_annonce'` :
**15 travaux, tous `done`**, du 21/05/2026 15:53 UTC au **30/08/2026 07:42:21 UTC**
(= 09:42 Paris). Le dernier désarchivage réussi est **une minute avant le commit** qui a
posé la RPC. Aucun travail depuis : zéro tentative enregistrée, parce que la RPC échoue
avant d'écrire quoi que ce soit.

**Ce qui marche encore, et qu'il ne faut pas refaire.**
- Le worker : `handleRestoreHektorAnnonce` (`Console/console_job_worker.js:18406`) n'a besoin
  que de `hektor_annonce_id` ; `app_dossier_id` y est toléré `null` (l. 18409, 18453). Il
  appelle Hektor (`upval…champ=archive&val=0`), **relit l'état par l'API** et refuse de
  conclure au succès sans confirmation (l. 18427-18436), puis enfile un
  `refresh_console_data` (l. 18444) qui fait redescendre l'annonce.
- Les droits : `app_console_can_request_job('restore_hektor_annonce', …)` rend vrai pour
  `admin` et `manager`, **sans se servir du numéro de dossier** (mesuré le 08/10).
- Aucune contrainte de clé étrangère sur `app_dossier_id`, ni dans `app_console_job`, ni dans
  `app_annonce_champ_app` (clé primaire `(app_dossier_id, champ)`).

**Non mesuré / non éprouvé.** Le geste n'a pas été cliqué dans l'app connectée (il écrirait
chez Hektor) : le verdict repose sur le code et la base. Je n'ai pas mesuré si un
`app_archive_id` pourrait un jour percuter un `app_dossier_id` réel (la place est libre).

### Étape 2 — Le correctif proposé (08/10, **attend le « vas-y »**)

**La cause, en une phrase.** Le 30/08, le geste est passé par une RPC qui exige que le bien
soit dans `app_dossier_current` — or un bien archivé n'y est jamais.

**Option A (recommandée) — une seule fonction SQL, rien d'autre.**
`CREATE OR REPLACE FUNCTION public.app_restore_annonce_optimistic` (même signature) :
le chemin actuel est conservé mot pour mot ; on ajoute un **second chemin** quand le dossier
n'est pas trouvé → chercher dans `app_archive_annonce_index_current` par
`app_archive_id = target_dossier_id` (c'est exactement le numéro que l'écran envoie,
`api.ts:2618`) et, si on le trouve, créer le travail avec `hektor_annonce_id` de l'index et
`app_dossier_id = null` (colonne nullable, mesuré). Le carnet `app_annonce_champ_app` n'est
écrit que si le dossier existe vraiment chez nous : y écrire sous un numéro d'archive serait
poser un faux identifiant, et **rien ne lit ce carnet pour l'annonce** (`magasin_annonce_app.py`
l. 19-21 « il n'applique rien… pour l'annonce cette liste est VIDE » ; preuve en base : le bien
62774 porte `archive='1'` au carnet depuis le 30/08 et s'affiche `archive='0'`).
Toujours `dossier_not_found` si le numéro n'est **ni** un dossier **ni** une archive.
→ **Aucune ligne de front, aucun déploiement.** 1 fonction, ~15 lignes ajoutées.

**Option B — une fonction neuve `…_depuis_archive(hektor_annonce_id)` + l'écran la choisit.**
Plus propre sur le papier (on parle en n° Hektor, la vraie clé), mais : code front modifié,
`npm run build`, **déploiement Vercel**, et deux fonctions à maintenir. Même résultat.

**CE QUE ÇA POURRAIT CASSER AILLEURS** *(chaque point vérifié)*

| Ce que j'ai vérifié | Preuve | Verdict |
|---|---|---|
| Tous les appelants de la RPC | `grep` sur tout le dépôt (hors `dist/`, `.tmp/`, worktrees) : **un seul**, `lib/api.ts:9560` | aucun autre écran |
| Front, chemin du dossier vivant | le premier `select` et tout son corps sont inchangés ; `app_dossier_current` d'abord | inchangé |
| Worker (4 services) | `console_job_worker.js:18406-18453` n'utilise que `hektor_annonce_id`, `app_dossier_id` toléré `null` (l. 18409) | pas de redémarrage nécessaire |
| Droits | `app_console_can_request_job('restore_hektor_annonce', …)` : admin ou manager, **sans se servir du n° de dossier** | garde-fou intact |
| Chantier ① (sécurité) | ACL actuelle : `authenticated=X, service_role=X`, **anon=non**. `CREATE OR REPLACE` **conserve** l'ACL — le patch ne fait **jamais** `DROP FUNCTION` | pas de réouverture à `anon` (revérifié après) |
| RLS de `app_console_job` | `select` : `requested_by = auth.uid()` OR `can_request_job(...)` → la relecture du travail par l'écran marche avec `app_dossier_id null` | OK |
| Contraintes | `app_dossier_id` **nullable**, aucune clé étrangère ; l'index « admin annonce » n'est **pas** unique | insertion possible |
| Carnet / run de nuit / phase2 / crons | aucun script n'appelle la RPC ; le carnet annonce n'est appliqué par personne (ci-dessus) | rien ne bouge la nuit |
| Pages publiques (vitrine, photos, RDV, espace client) | la RPC n'y est pas appelée et `anon` ne peut pas l'exécuter | aucun effet |
| Décision écrite C.4 du 30/08 (« écrire chez nous d'abord ») | respectée pour un dossier vivant ; pour une archive, nous n'avons **aucune** ligne à écrire chez nous — l'intention est tenue par le travail, créé dans la même transaction | tenue |

**Limite connue, dite franchement.** Avec `app_dossier_id null`, le bandeau « geste abandonné »
(`App.tsx:32603`, qui cherche par `app_dossier_id`) ne montrera pas un désarchivage resté en
plan sur un bien archivé. Mettre le numéro d'archive dans cette colonne le ferait apparaître —
mais ce serait écrire un faux identifiant, la faute même de 5d et 5g. À traiter proprement au
chantier ④ si Frédéric le veut.

**Par-dessus le marché** (hors 5a, à ne pas corriger ici) : `api.ts:9545` guette une erreur
`app_console_job_active_admin_annonce_idx`, index **qui n'existe plus** (il est devenu
`app_console_job_admin_annonce_queue_idx`, **non unique**) : deux travaux admin simultanés sur
la même annonce ne sont plus arrêtés par la base, seulement par l'écran.

**Retour arrière.** Un script inverse qui repose la définition d'aujourd'hui **mot pour mot**
(`pg_get_functiondef` du 08/10, copié dans `supabase/`), toujours en `CREATE OR REPLACE`.

**Le contrôle prévu.** ① une **répétition** dans l'éditeur SQL : patch + inverse + une erreur
volontaire finale qui annule tout, avec le détail de deux appels joués sous l'identité d'un
admin (`set_config('request.jwt.claims', …)`) — une archive réelle (travail créé, bon
`hektor_annonce_id`, `app_dossier_id` nul) et un numéro inventé (`dossier_not_found`) ;
② après application : `anon` toujours sans droit d'exécution ; ③ essai réel à l'écran sur
**un bien archivé choisi par Frédéric** (le geste écrit chez Hektor : son accord est
obligatoire), puis relecture du travail et de l'état Hektor.

### Étape 4 — La répétition, jouée par Frédéric le 08/10 (~09:50) : **13 lignes sur 14 exactes**

Collée dans l'éditeur SQL, elle a rendu l'erreur attendue `ESSAI ANNULE`. Tout est conforme :

| ce qui était annoncé | ce qui est sorti |
|---|---|
| le bug reproduit sur l'archive 15633 | `22023/dossier_not_found` ✔ |
| après le patch, le même geste marche | `dossier=NULL hektor=49544 statut=pending priorite=8 numero=VM69168 source=index_archives demandeur=pose` ✔ |
| le chemin du bien vivant inchangé | `dossier=3828957 hektor=62774 source=dossier_vivant carnet=0/geste_desarchiver` ✔ |
| un numéro inventé refusé | `22023/dossier_not_found` ✔ |
| sans connexion, refusé | `42501/forbidden_restore` ✔ |
| rien laissé derrière | `travaux=15` et `carnet=3`, comme au départ ✔ |
| droits | `anon=non authenticated=oui service_role=oui` ✔ |

**La 14e ligne, et ce qu'elle apprend.** `apres_inverse_empreinte` a rendu
`d0b925a2ceb970acf69efe3140d31581` au lieu de `d4f311d782c7525494107cc0596fdedc`.
Cause trouvée et **prouvée hors ligne**, sans rien demander de plus : un copier-coller depuis
Windows remplace les fins de ligne du corps de la fonction (`\n` → `\r\n`). En reconstruisant
la définition à partir du fichier :

```
même texte, fins de ligne LF    -> d4f311d782c7525494107cc0596fdedc  (= l'avant mesuré)
même texte, fins de ligne CRLF  -> d0b925a2ceb970acf69efe3140d31581  (= l'après-inverse mesuré)
```

Les deux empreintes sont reproduites **au bit près** : pas une lettre de code ne diffère. Pour
PL/pgSQL un `\r` est un espace ; précédent connu en production, `app_console_current_role`
vit avec un corps en CRLF. **Ce n'était pas un échec du patch, mais un défaut de ma mesure.**

**Corrigé dans les deux fichiers** : la comparaison d'empreinte retire maintenant les `chr(13)`
avant de comparer (`supabase/patch_5a_…_INVERSE.sql` l. 74-78). C'était important : telle quelle,
ma garde aurait **refusé de faire le retour arrière** le jour où on en aurait eu besoin.
Le patch affiche en plus l'empreinte attendue après application :
`709571469083a76b1be384e879ca523b` (calculée depuis le fichier, retours Windows retirés).

**État de la base, revérifié après la répétition** (lecture seule, 08/10) : fonction toujours
celle d'avant (`d4f311d7…`, corps sans `\r`), **15** travaux de désarchivage, **3** lignes de
carnet, carnet `archive` toujours `1/geste_archiver/2026-08-30`. **La répétition n'a rien laissé.**

### Étape 5 — Contrôle après application (08/10, ~09:55) · patch **EN PRODUCTION**

Frédéric a collé le patch : « Success. No rows returned ». Relecture en base, lecture seule :

| ce qu'on contrôle | mesure |
|---|---|
| empreinte de la fonction (retours Windows retirés) | **`709571469083a76b1be384e879ca523b`** = exactement la valeur annoncée avant d'appliquer |
| le chemin des archives est bien dans le code | `prosrc` contient `app_archive_annonce_index_current` ✔ |
| la nature de la fonction | `SECURITY DEFINER` ✔, `search_path=public` ✔, même signature ✔ |
| les droits (chantier ①) | `anon=non` · `authenticated=oui` · `service_role=oui` ✔ |
| rien n'a été écrit au passage | **15** travaux de désarchivage (inchangé), **3** lignes de carnet (inchangé), carnet `archive` toujours `1/geste_archiver/2026-08-30` ✔ |
| fins de ligne du corps | CRLF (3 365 octets contre 3 293 en LF) — attendu, sans effet : un `\r` est un espace pour PL/pgSQL |

**Ce qui est prouvé** : la fonction accepte désormais une archive et crée le bon travail
(répétition : `hektor=49544`, `numero=VM69168`, `source=index_archives`), le chemin du bien
vivant est intact, les refus tiennent (numéro inconnu, sans connexion), les droits n'ont pas bougé.

**Ce qui n'est PAS encore prouvé, et il faut le dire** : le geste n'a pas été **cliqué dans
l'app**. Le chaînon « bouton → numéro envoyé » est vérifié dans le code (`api.ts:2618`,
`App.tsx:13857`) mais pas en réel. Un vrai clic crée un travail que le worker envoie à Hektor :
cela demande l'accord de Frédéric **et une annonce archivée choisie par lui**.

### 5a bis — LE BOUTON N'EXISTAIT POUR AUCUNE ARCHIVE (trouvé le 08/10 pendant l'essai réel)

**Ce qui s'est passé.** Essai sur VA2380 (bien Hektor 78, `app_archive_id` 1107157) dans l'app
connectée. La fiche s'ouvre — et **aucun bouton « Désarchiver »**, ni dans la page, ni dans le
menu « ••• » (relevé de tous les boutons de la page, pas une impression d'écran).

**Pourquoi.** Dans le cockpit (`CockpitDetail`), deux conditions se fermaient l'une l'autre :

```
if (props.onRestoreAnnonce && !isLightweightDetail && estArchive)      <- App.tsx:27744
      estArchive          = /archiv/i.test(statut_annonce)
      isLightweightDetail = vrai des que archive === '1'
```

- `estArchive` lit le **statut**. Or une archive porte « Clos » (33 878), « (vide) » (785),
  « Vendu » (423), « Actif » (199), « Estimation » (30), « Sous offre » (2) — **jamais
  « Archivé » : 0 sur 35 317** (mesure en base du 08/10).
- `isLightweightDetail` est **toujours vrai** pour une archive (il rend vrai dès `archive='1'`).

Le bouton du bandeau de lecture seule (`:27968`) était bloqué pareil : il exigeait
`ckStage === 'archive'`, or le statut prime dans le calcul du cran — une archive « Clos »
tombe sur le cran « clos ».

**Correctif (« vas-y » de Frédéric, 08/10)** — deux conditions, dans `CockpitDetail` :
le menu et le bouton visible regardent désormais **le champ `archive`**
(`isArchivedAnnonceRecord`) en plus du statut, et ne se ferment plus sur
`!isLightweightDetail` : désarchiver est justement l'action qu'une fiche en lecture seule doit
offrir. `npm run build` ✔ (6,09 s). Le mobile (`:34063`) regardait déjà le bon champ.
**Attend un déploiement** (pousser = déployer).

### 5a ter — la préparation du détail d'archive appelle Hektor (audit du 08/10)

Frédéric : *« on n'a pas besoin de faire appel à Hektor, normalement le serveur a déjà tout »*.
Mesuré, il a raison pour la fiche, pas pour le bloc console :

| mesure (base locale `data/hektor.sqlite`, lecture seule) | |
|---|---|
| annonces archivées | 37 773 |
| **avec le détail complet en local** | **34 532 (91 %)** |
| avec le bloc **console** en local | **35** |
| bloc console en local, toutes annonces confondues | 164 |

Le travail `prepare_archived_annonce_detail` fait donc deux choses : il **appelle Hektor**
(`sync_console_missing_fields.py`, 20,4 s sur le bien 78) pour ramener le bloc console
(secteur, chauffage, diagnostics, honoraires détail, pièces, images DPE/GES), **puis** il
reconstruit la fiche **depuis la base locale** (60 119 octets).

**Et il rappelle Hektor même quand la donnée est déjà là** : dans
`phase2/sync/sync_console_missing_fields.py` l. 214-217, un identifiant passé explicitement
vaut `reason = "explicit"` — le cache local n'est même pas regardé. Rouvrir deux fois la même
archive, c'est deux extractions.

### Étape 5 (suite) — L'ESSAI RÉEL A RÉUSSI (08/10, 10:45) · **5a est fini**

Déploiement Vercel du commit `78e6574` : **READY** en production (vérifié par l'API Vercel).
Fiche VA2380 rouverte dans l'app connectée : **les deux boutons « Désarchiver » sont là**
(le visible, dans le bandeau de lecture seule, et l'entrée du menu « ••• »). Clic.

```
08:45:44 UTC  travail cree   app_dossier_id = NULL   hektor_annonce_id = 78
                             cible_source = index_archives   numero = VA2380   priorite = 8
08:45:48      pris par le worker
08:46:31      done en 43 s -- Hektor a confirme archive=0 (le worker refuse de conclure sans
                             relecture par l'API : console_job_worker.js:18427-18436)
08:46:31      refresh_console_data enfile tout seul -> done a 08:46:56
```

**Le premier désarchivage depuis 39 jours** : le précédent datait du 30/08 à 07:42 UTC, celui-là
même qui précédait d'une minute le commit qui a cassé le geste. Travaux de désarchivage :
15 → **16**. Carnet : 3 lignes, inchangé (normal, une archive n'a pas de numéro de dossier
chez nous). Le bien est sorti de l'index des archives : 35 317 → **35 316**.

**CE QUI RESTE À SURVEILLER, dit franchement.** Le bien 78 n'est, à cette minute,
**ni dans les archives, ni dans le parc vivant** (0 et 0 ; parc toujours 13 467). Hektor est à
jour, mais chez nous l'index actif n'est reconstruit que par la descente : **le bien est
invisible dans l'app jusqu'au run de cette nuit**. À vérifier demain matin ; si ça se confirme
comme un trou de quelques heures après chaque désarchivage, c'est un point à ouvrir.

### 5a ter (suite) — POURQUOI SEULEMENT 35 ARCHIVES ONT LE BLOC CONSOLE

Question de Frédéric : *« c'est sûrement lié au run chauffage/DPE quotidien... mais alors
pourquoi seulement 35 ? »* Mesuré :

**1. L'extraction console ne tourne JAMAIS la nuit.** Dans `run_full_pipeline.ps1` l. 716 elle
est derrière un interrupteur `-RunConsoleMissingFields` (interrupteur éteint par défaut,
l. 86) — et le run de nuit ne le passe pas : `scheduled/run_quotidien.ps1` l. 39 n'envoie que
`-PushContactsToSupabase -ContactsEligibleOnly -AllowStaleSupabaseDeletes
-IncludeArchivedContactSearches`. Sa limite par défaut serait de toute façon **25 par passage**.

**2. D'où viennent les 164 lignes** (dates d'extraction) : **135 en juin** (une campagne à la
main), puis 15 en juillet, 6 en août, 4 en septembre, **4 en octobre** — c'est-à-dire une par
une, posées par ce geste-ci et ses voisins. D'où les **35 archives seulement**.

**3. Ce qui tourne vraiment la nuit, c'est le CHAUFFAGE — une AUTRE extraction, une autre
table.** `-SkipHektorChauffage` n'est pas passé, scope `current`, **50 par nuit maximum**
(`run_full_pipeline.ps1` l. 70-81 et 351). Et elle, elle est bien remplie :

| `hektor_annonce_chauffage_detail` | |
|---|---|
| lignes | **57 092** |
| sur annonces vivantes | 22 560 |
| **sur archives** | **34 532** |

Donc l'intuition de Frédéric est juste sur le principe — il y a bien un rattrapage de champs
manquants chaque nuit — mais c'est le **chauffage**, pas le bloc console. Et
`prepare_archived_annonce_detail.py` lit le chauffage dans **sa propre table locale**
(l. 170-177) : le chauffage est déjà servi sans appeler Hektor.

**Ce que l'appel à Hektor apporte donc vraiment, pour une archive** : secteur, contacts des
diagnostics, détail des honoraires, rendement locatif, détail des pièces, images DPE/GES.
Rien d'autre.

**Le gaspillage, prouvé en direct aujourd'hui** : deux extractions pour le bien 78, à 08:22
puis **08:44** UTC — 22 minutes d'écart, alors que la donnée était en cache depuis la première.

### 5a ter (fin) — LA MÉTHODE EXISTE : trois étages, et le vrai trou fait ~25 champs, pas 157

Question de Frédéric : *« mon projet doit avoir une méthode, sinon tous ces champs seraient
vides sur les annonces puisque seulement 35 ? »* — il a raison, et ma présentation précédente
était trompeuse. Mesuré :

**Étage 1 — l'API Hektor fait l'essentiel, et elle ne rend QUE LE RENSEIGNÉ.**
Le blob `detail_raw_json` porte les mêmes groupes que les écrans de la console
(`ag_interieur`, `ag_exterieur`, `terrain`, `equipements`, `diagnostiques`, `copropriete`,
`mandat_infofi`, `mandat_mandatdispo`) plus `honoraires`, `textes`, `images`, `mandats`,
`proprietaires`, `localite`, `zones`. **Elle n'envoie pas les cases vides** — preuve sur
400 annonces vivantes :

| groupe | noms de champs vus | toujours présents |
|---|---|---|
| `ag_interieur` | 12 | 3 |
| `ag_exterieur` | 18 | 4 |
| `diagnostiques` | 16 | 1 |
| `mandat_infofi` | 12 | 4 |
| `copropriete` | 4 | 1 |
| **`equipements`** | **1** | **1 (`ASCENSEUR`)** |

Un champ « absent » du blob veut donc dire **vide chez Hektor**, pas « perdu ». C'est pour ça
que les fiches ne sont pas vides, et c'est ce que mon comparatif du bien 78 (« 103 champs en
plus côté console ») laissait croire à tort : ce bien est une vieille archive presque vide.

**Étage 2 — le run chauffage, chaque nuit, parce que l'API ne rend pas les équipements.**
Une seule exception au tableau ci-dessus, et elle est structurelle : `equipements` ne rend
**jamais** autre chose qu'`ASCENSEUR`. Le chauffage a donc sa tâche dédiée — et une autre
raison d'exister : l'API ne donnerait qu'une valeur, alors qu'un bien peut avoir **plusieurs
chauffages** (le relevé rend la liste : format / type / énergie par ligne). 57 092 lignes.

**Étage 3 — le run console, éteint : le reste du bloc équipements, et quelques détails.**
En retirant ce que l'API donne déjà et ce que le chauffage couvre, ce qui ne redescend
**jamais** chez nous se réduit à ceci :

- **le bloc équipements moins ascenseur et chauffage (~20 champs)** : EAU, ASSAINISSEMENT,
  DISTRIBUTION_EAU, ENERGIE_EAU, cheminee, climatisation (+ spec), double_vitrage,
  triple_vitrage, volets_elctriques, porte_blindee, interphone, visiophone, alarme, digicode,
  detecteur_fumee, gardien, cable, ACCES_HANDI ;
- **organiser la visite (2)** : `CLES`, `moyens_visite` ;
- **secteur (texte)** : `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT`, `immeuble`, `irisAnnonce` ;
- **les images DPE et GES** (`dpe_image_url`, `ges_image_url`) ;
- **le détail des grilles d'honoraires** (`_detailHonoraire2/3`, `_idGrille2/3`…) — l'API rend
  déjà la liste `honoraires` (taux, à charge de) ;
- **la composition détaillée des pièces** (`pieces` existe dans le blob mais souvent `null`).

**L'asymétrie à retenir** : l'app sait **écrire** plusieurs de ces champs chez Hektor — ils sont
dans l'assistant de création (`App.tsx:1536-1550` : Assainissement, Double vitrage, Porte
blindée, Détecteur fumée…) et dans la lecture OCR d'une fiche scannée — mais elle ne sait pas
les **relire**. Un aller sans retour. C'est un sujet de **chantier ⑥** (« ce qui ne redescend
pas »), pas du point 5a.

**Correction de ce que j'ai dit plus tôt** : le trou n'est pas de 157 champs, mais d'environ
**25**, et il concerne **tout le parc**, pas seulement les archives.

### 5a ter (correction) — NON, CES CHAMPS NE SONT PAS VIDES. Deux erreurs de mesure.

Frédéric : *« vérifie que tous ces champs sont vides dans ma data actuelle »*. Vérifié :
**ils ne le sont pas**, et mes deux conclusions précédentes venaient de deux pièges de mesure.

**Piège 1 — `LIKE` en SQLite.** Il **ignore la casse** et **`_` y est un joker**.
`LIKE '%ASSAINISSEMENT%'` rendait **53 546** blobs : il attrapait le mot « assainissement »
dans le TEXTE des annonces. La bonne mesure, `instr(detail_raw_json, '"ASSAINISSEMENT"')>0` :
**589**.

**Piège 2 — `limit 400` sans `ORDER BY`.** SQLite rend alors les lignes les plus ANCIENNES.
Mon échantillon n'était fait que de vieux biens vides, d'où ma conclusion fausse « l'API ne
rend jamais le bloc équipements ». Elle le rend très bien.

**Mesure exacte, sur les 58 058 blobs (`instr`, sensible à la casse) :**

| | total | parc vivant |
|---|---|---|
| au moins un champ d'équipement | — | **710 (3,0 %)** |
| **sur les annonces récentes (n° > 60 000)** | — | **597 sur 1 544 — 38,7 %** |
| `ASCENSEUR` | 14 004 | 4 974 (21,1 %) |
| `ASSAINISSEMENT` | 589 | 532 |
| `double_vitrage` | 655 | — |
| `CLES` | 4 475 | 1 826 |
| `moyens_visite` | 12 898 | 3 962 |
| `terrain_ref_cadastr` | 1 549 | 516 |

Exemple complet (bien 63237) : l'API rend `ACCES_HANDI`, `climatisation`, `EAU`,
`ASSAINISSEMENT`, `DISTRIBUTION_EAU`, `ENERGIE_EAU`, `cheminee`, `ARROSAGE`, `BARBECUE`…
**L'API rend tout ce qui est rempli.** Si un champ manque, c'est qu'il est vide CHEZ HEKTOR —
et le parc ancien est vide parce que personne ne l'a saisi, pas parce qu'on l'a perdu.

**CE QUI N'EST VRAIMENT JAMAIS RENDU — 0 sur 58 058 :**

| | pourquoi ça compte |
|---|---|
| `formatChauff`, `typeChauff`, `energieChauff` | **c'est la raison d'être du run chauffage de la nuit** — et lui rend la LISTE (un bien peut en avoir plusieurs) |
| `TRANSPORT`, `PROXIMITE`, `ENVIRONNEMENT`, `immeuble`, `irisAnnonce` | les textes de secteur — affichés par la fiche (`App.tsx:29416`) |
| `dpe_image_url`, `ges_image_url` | les images DPE/GES — affichées (`App.tsx:6206-6209`, `:9840`) |
| `_detailHonoraire2/3`, `_idGrille2/3` | le détail des grilles ; l'API rend déjà la liste `honoraires` (taux, à charge de) |

**Donc le trou réel, ce n'est ni 157 champs ni 25 : c'est le chauffage (déjà couvert par sa
propre tâche de nuit) + 5 textes de secteur + 2 images + le détail des grilles d'honoraires.**
Tout le reste de la fiche vient de l'API et est déjà chez nous.

**Conséquence pour la décision 5a ter** : l'appel à Hektor au moment d'ouvrir une archive ne
rapporte, en pratique, que ces quatre choses-là. L'option A (couper l'appel) coûte donc bien
moins cher que ce que j'avais annoncé. Décision à Frédéric.

### 5a ter — CODÉ (option A, choisie par Frédéric le 08/10)

`Console/console_job_worker.js` :
- l. 51-62 : un interrupteur **`CONSOLE_ARCHIVE_DETAIL_EXTRACTION`**, éteint par défaut, avec
  la mesure qui justifie la décision écrite juste au-dessus ;
- l. 4252-4263 : `handlePrepareArchivedAnnonceDetail` n'appelle plus Hektor ; il écrit à la
  place une ligne de journal « extraction console NON faite ». Le reste du travail est
  inchangé : la fiche se reconstruit depuis la base locale.

`node --check` ✔. **Le code ne prend effet qu'après redémarrage des QUATRE services worker**
(ils partagent ce fichier) — accord de Frédéric nécessaire, file documents vide.

**Ce que ça pourrait casser ailleurs** — les trois autres appelants de
`runTargetedConsoleMissingFields` ne sont **pas touchés** : `refresh_console_data` (l. 3977,
il veut justement du frais après un changement), le rafraîchissement des caches légers
(l. 4036) et le **jumeau `prepare_historical_annonce_detail`** (l. 4272, pour les Vendu/Clos
non archivés). ⚠ **Question ouverte à Frédéric** : faut-il appliquer la même chose au jumeau ?
Je ne l'ai pas décidé seul.

**Retour arrière** : poser `CONSOLE_ARCHIVE_DETAIL_EXTRACTION=1` dans l'environnement des
services et redémarrer — aucun code à modifier.

**Contrôle prévu** : après redémarrage, ouvrir une archive jamais extraite et vérifier dans
`app_console_job_log` qu'il n'y a plus d'étape `console_missing_fields` en `running`, que le
travail finit en quelques secondes au lieu de ~22 s, et que la fiche s'affiche.

---

## 5b — MODIFIER UN MANDANT DEPUIS SA CARTE

### Étape 1 — Audit du 08/10 · verdict : **CONFIRMÉ, 100 % des cas depuis le 23/09**

Le crayon « Modifier » (`HektorMandantContactEditForm`) existe à **5 endroits**, tous sur une
annonce existante : cockpit onglet « Contact » (`App.tsx:28963`), ancienne fiche (`:30216`,
`:30275`), popup d'édition (`:30778`), mobile (`:34287`). **Pas dans la création d'annonce** :
elle passe par `createLinkHektorMandantJobOptimistic` et `createHektorMandantContactJob`.

La RPC `app_update_mandant_contact_optimistic` fait trois choses : ① le travail pour Hektor
(marche), ② l'écriture chez nous, ③ la désignation du travail au balayage. ② et ③ sont dans un
même bloc terminé par `exception when others then null`.

**② échoue toujours.** L'écran envoie `hektor_target_id` = **le numéro de Hektor**
(`App.tsx:7272`, et c'est le bon pour détacher un mandant). `app_edit_contact_optimistic`
cherche par `hektor_contact_id`, qui porte **notre** numéro depuis la bascule du 23/09 :

| mesure du 08/10 sur `app_contact_current` | |
|---|---|
| contacts | 62 162 |
| où cible = identité | **0** |
| où les deux diffèrent | **62 162** |
| où `hektor_contact_id` vaut bien notre `app_contact_id` | 62 154 |

Donc `contact_not_found` à tous les coups, avalé. **③ non plus n'est jamais atteinte** : elle
protège du double envoi et fait réessayer au bout de 30 min (5 fois) — ce filet n'existe pas
pour un mandant. 9 travaux `update_hektor_mandant_contact`, tous réussis, le dernier le 31/08
— avant la bascule. La fiche contact, elle, marche : elle passe l'identité (`api.ts:9146`).

**Ce que l'audit du 08/10 disait de trop** : la modification **arrive bien chez Hektor**. Ce
qui est perdu, c'est le « chez nous d'abord ».

### Les registres — vérifié avant de coder *(question de Frédéric)*

- `app_relation` ne porte **aucune** copie de l'identité → rien à mettre à jour ; l'écran lit
  le registre pour les identifiants puis joint les contacts en direct (`api.ts:8770-8800`).
- Le registre des mandats est **refait à chaque push** depuis les liens vivants
  (`charger_mandants_du_registre_des_liens`) : la copie du nom suit toute seule.
- Le **rôle du lien dit si le bien a un mandat numéroté** : mandant → 26 763 biens dont
  **24 424 au registre** ; propriétaire → 31 872 biens dont **0**. Jamais les deux rôles sur un
  même bien. Un mandant sur une annonce sans numéro ne touche donc que le registre des liens.
- Le **contrat d'autorité existe** pour les relations depuis les 02-03/10 (deux distributeurs
  et deux plages — run à 132 714, app à 1 000 009 ; jamais de renumérotation ; DELETE-NEVER ;
  une ligne née dans l'app porte `present_in_hektor = false` et le run ne la marque pas sortie).
  `app_link_mandant_optimistic` le respecte. **5b n'y touche pas.** Encadré daté ajouté au plan.

### Étape 2 et 3 — Correctif codé (option A, « vas-y » du 08/10)

Traduire la cible en identité, une fois, juste avant l'écriture ; le travail pour Hektor garde
la cible. Trois fichiers, `supabase/patch_5b_mandant_identite_2026-10-08*` :

- le patch (garde-fou d'entrée : les 2 colonnes de numéro, la signature, **et l'empreinte
  `b8a89ff72095acb00dccbf3c857e90ab`** — si la fonction a bougé depuis la mesure, il refuse) ;
- l'inverse : corps **vérifié hors ligne contre `pg_proc.prosrc`**, md5
  `0d6d48371f09ca3626c2fad404a27d5b`, identique au bit près ;
- la répétition : le bug reproduit, le geste réparé, le repli, puis l'inverse, puis l'erreur
  volontaire. Cas d'essai réel : annonce 63244, mandant identité 10025872 / cible 48422.

Empreinte attendue après le patch : **`c0fe0f30a3dc1b2d4cdceea156800092`**.
Les **noms de paramètres sont inchangés** (Postgres refuse un renommage par
`create or replace`). Aucune ligne de front, aucun déploiement, aucun redémarrage.

### Étape 4 — Répétition v1 : ARRÊTÉE par un garde-fou d'origine (08/10, ~11:20)

Collée par Frédéric. Les trois essais ont rendu **`ERREUR 22023/missing_contact_email`** :
ma charge d'essai n'avait pas d'e-mail, et `app_console_create_update_mandant_contact_job`
en exige un (comme il exige un nom, un numéro d'annonce, un identifiant numérique et le droit).
**Le garde-fou a fait son travail** ; le défaut était dans mon essai, pas dans le patch.

Tout le reste de la répétition est conforme : empreinte d'avant
`b8a89ff72095acb00dccbf3c857e90ab`, 9 travaux, 0 ligne d'attente, ville inchangée, droits
`anon=non`, et **empreinte après inverse identique à l'avant** — la base n'a pas bougé.

**Répétition v2** : la charge est construite **depuis la base** (nom et e-mail réels lus au
moment de l'essai), donc aucune donnée de client n'est écrite dans le fichier.

### Étape 4 (v2) et 5 — répétition EXACTE, patch **APPLIQUÉ** (08/10, ~11:35)

La répétition v2 a rendu **13 lignes sur 13 conformes** :

```
AVANT_PATCH = travail cree=oui | ville apres=Saint-André-le-Puy | attente=0   <- le bug
APRES_PATCH = travail cree=oui | ville apres=ESSAI 5B | attente=1 | travail designe=oui
APRES_PATCH_identite_directe = ville apres=ESSAI 5B BIS                       <- le repli
apres_travaux_mandant=9  apres_lignes_attente=0  apres_ville=Saint-André-le-Puy
apres_droits=anon=non authenticated=oui service_role=oui
apres_inverse_empreinte=b8a89ff72095acb00dccbf3c857e90ab                      <- = l'avant
```

**Patch appliqué par Frédéric.** Contrôle en base, lecture seule :

| contrôle | mesure |
|---|---|
| empreinte normalisée | **`c0fe0f30a3dc1b2d4cdceea156800092`** = la valeur annoncée avant d'appliquer |
| la traduction est dans le code | `hektor_target_id = target_contact_id` ✔ et la variable `v_identite` ✔ |
| nature | `SECURITY DEFINER`, `search_path=public`, même signature ✔ |
| droits (chantier ①) | `anon=non` · `authenticated=oui` · `service_role=oui` ✔ |
| rien écrit au passage | 9 travaux mandant, 0 ligne d'attente, ville témoin inchangée ✔ |

**Pas encore prouvé** : le geste n'a pas été fait depuis l'écran. Le chaînon « crayon → numéro
envoyé » est vérifié dans le code, pas en réel — il faut un mandant choisi par Frédéric
(le geste écrit chez Hektor).

### Étape 5 (suite) — ESSAI RÉEL RÉUSSI, cycle complet (08/10, 13:06) · **5b est fini**

Choix de Frédéric : une vraie correction sur une annonce d'essai. Bien **62774
« TEST C4 du 25-08 Villa Bellecour »**, mandant **« Sophie TEST MANDANT 25-08 »**
(identité 10355712, cible Hektor 605030), dont la **ville était vide**. Saisie :
`Saint-Étienne`.

```
13:06:04  clic  -> ville chez nous = Saint-Étienne  IMMEDIATEMENT
                   app_contact_pending : 1 ligne, push_job_id POSE (le verrou),
                   app_contact_id = 10355712 (notre numero voyage avec la saisie),
                   push_fields = city, email, phone, address, last_name, first_name
13:06:06  le worker « actions » prend le travail
          session Hektor : admin -> contexte AGENCE (le negociateur du bien est inactif)
          hektor_mandant_update sur le contact 605030  -> « status: updated »
13:06:32  done en 26 s, et DEUX rafraichissements enfiles tout seuls
          (refresh_console_data 62774 + refresh_console_contact_data 605030)
13:0x     les deux done -> la ville revient de Hektor : toujours Saint-Étienne
          app_contact_pending : 0 ligne -- le balayage l'a retiree, le travail etant fait
```

**Tout ce que la répétition annonçait s'est produit en vrai** : la valeur chez nous tout de
suite, le travail désigné (pas de double envoi), Hektor modifié, la redescente qui confirme,
la file qui se vide. Travaux mandant : 9 → **10**, le premier depuis le 31/08. Les 3 liens du
bien sont intacts, le registre n'a pas bougé.

**Note utile pour la suite** : le worker a basculé en **contexte AGENCE** parce que le
négociateur propriétaire du bien est inactif — repli prévu, journalisé, qui a fonctionné.

### Ce qui reste ouvert sur 5b *(pas de ce point)*

- le `exception when others then null` efface toujours la trace d'un échec → **chantier ④** ;
- l'écran, lui, affiche bien l'erreur si la RPC échoue (`App.tsx:13869`), ce n'est donc pas
  un silence complet côté utilisateur.

### 5a ter (suite) — LE JUMEAU « VENDU / CLOS » reçoit le même traitement (08/10)

Frédéric : *« même traitement si les problèmes sont similaires »*. Mesuré, ils le sont — et le
cas est encore plus net que pour les archives :

| périmètre « historique » (Vendu / Clos, non archivé) | |
|---|---|
| annonces | 9 687 |
| **avec le détail complet en local** | **9 616 — 99,3 %** |
| avec le bloc console en local | **21** |
| avec le chauffage en local | 8 868 (91,5 %) |

`prepare_historical_annonce_detail.py` lit la même base locale (`data/hektor.sqlite`) et la
même table `hektor_annonce_console_detail` que son jumeau. Le handler du worker appelait
`runTargetedConsoleMissingFields` exactement pareil.

**Codé** : un **seul interrupteur pour les deux**, renommé
`CONSOLE_DETAIL_LEGER_EXTRACTION` (l'ancien nom disait « ARCHIVE » et aurait trompé le lecteur
sur le chemin Vendu/Clos ; rien n'était encore actif, le renommage ne coûte rien). Éteint par
défaut. `node --check` ✔.

⚠ **Toujours DORMANT** : actif seulement après redémarrage des **quatre** services worker.
**Retour arrière** : `CONSOLE_DETAIL_LEGER_EXTRACTION=1` + redémarrage, aucun code à toucher.

---

## 5c — LE PREMIER NUMÉRO DE MANDAT DEMANDÉ DEPUIS L'APP

### Étape 1 — Audit du 08/10 · **confirmé, moins grave qu'annoncé, et un point FAUX**

**Le geste marche.** 3 numéros demandés depuis l'app (28/07, 25/08, 28/08), **3 réussis**, les
cinq étapes Hektor jusqu'au bout.

**FAUX — la date.** L'audit du 08/10 soupçonnait le format `JJ-MM-AAAA` (`inputDateToFrench`).
Mesuré sur les trois usages réels : date envoyée `28-08-2026`, étape des dates `done`, et les
dates **enregistrées sont exactes** (2026-08-25, 2026-08-28, 2026-07-28). **Pas un défaut.**

**CONFIRMÉ — l'enchaînement.** Depuis l'étape D, le worker écrit notre ligne dans Supabase
`app_mandat` dès qu'il a le numéro (`enregistrerMandatAuRegistreApp`), avec un id de la **plage
réservée à l'app** (`app_mandat_id_app_seq` = 1 000 001). Le `refresh` du run sait **adopter**
cet id (mandat_ledger l. 394-405) en lisant `app_mandat__sb`.

**⚠ CORRECTION DE MA PREMIÈRE ANALYSE.** J'avais écrit « la doublure n'est jamais descendue »,
en me fiant à un commentaire du code. **C'est faux, mesuré** : `app_mandat__sb` existe en
local avec ses **26 847 lignes** (= le compte Supabase). Il y a **15 doublures `__sb`**,
rafraîchies chaque jour par **GTI Descente**. Le vrai décalage est horaire :

| tâche Windows | heure réelle |
|---|---|
| **GTI Quotidien** (le run qui reconstruit et pousse) | **05:00** |
| **GTI Descente** (qui rafraîchit les 15 doublures) | **08:15** |

Le run lit donc une doublure vieille de ~21 h :

```
jour D   10:00  demande d'un numero -> id 1 000 001 en ligne
jour D+1 05:00  le run ne le voit pas -> SECOND id -> le push INSERE et heurte
                UNIQUE (hektor_annonce_id, numero_mandat) -> LE LOT CASSE
jour D+1 08:15  la descente le rapporte
jour D+2 05:00  le run l'adopte -> tout rentre dans l'ordre
```

**UNE nuit de registre perdue, pas « chaque nuit »** — et en silence (étape non bloquante).
Mesure : **0 ligne `origine='app'`** aujourd'hui, les 3 demandes datent d'avant l'étape D
(leurs journaux n'ont pas l'étape « registre app »). **Le piège est armé pour le prochain numéro.**

**Et c'était prévu.** Le run fait déjà exactement ce geste **trois fois** —
`app_affaire_ledger` (l. 786), `app_relation` (l. 923), `app_affaire_console` (l. 1073) — avec
la raison écrite : *« la doublure passe à 07h30, or ce run passe à 05h30 »*. Le registre des
mandats avait été laissé de côté **exprès**, raison écrite elle aussi : *« rien n'écrit encore
dans app_mandat… elle viendra AVEC l'écriture du worker (étape D), pas avant »*.
L'étape D est arrivée, la descente n'a pas suivi. **Un oubli d'enchaînement, pas un trou de
conception.**

**Non mesuré** : « un numéro est brûlé si les étapes 2 à 5 échouent » — vrai par construction,
jamais observé (3 sur 3 réussis).

### Étapes 2 et 3 — Correctif (option A, « vas-y » du 08/10)

Une seule étape ajoutée dans `run_full_pipeline.ps1`, **juste avant** celle du registre, copiée
sur les trois autres : `pull_from_supabase.py --table app_mandat`, en
`Invoke-OptionalStepWithRetry` (**non bloquante**), clé `phase2.doublure_mandat`. Ça ne crée
pas une doublure : ça rafraîchit celle qui existe, au bon moment.

Encodage vérifié (CRLF + BOM conservés) et **syntaxe PowerShell validée par le parseur**.

**Ce que ça pourrait casser ailleurs** : `pull_from_supabase` écrit **à côté**, sous `__sb` —
la table locale `app_mandat` n'est pas touchée ; aucune écriture dans Supabase (c'est une
lecture) ; trois fichiers seulement lisent `app_mandat__sb` et tous l'attendent
(`mandat_ledger.py`, `phase2/checks/mandat_un_numero.py`, `monitoring/check_gti_health.py`) ;
l'étape est non bloquante, donc un échec laisse le run exactement comme aujourd'hui.
**Coût non mesuré** : 26 847 lignes (comparaison : 18 442 lignes en 12 s pour la console,
2-3 min pour les 132 664 du registre des liens) — à chronométrer au premier run.

**Retour arrière** : retirer les deux lignes de l'étape. Rien d'autre.

### Étape 5 — CONTRÔLES DU 08/10 APRÈS-MIDI (workers redémarrés par Frédéric)

**Les 4 services** : `Running` tous les quatre.

**5a ter est ACTIF, et mesuré en production.** Préparation du détail de l'archive VA2362
(bien 70), déclenchée depuis l'app :

| | avant (bien 78, ce matin) | après (bien 70, 13:52) |
|---|---|---|
| étape `console_missing_fields` | « Extraction console ciblée » → **appel à Hektor** | **« Extraction console NON faite : la fiche se reconstruit depuis la base locale (5a ter, 08/10) »** |
| durée du travail | 22 s puis 13 s | **2 s** |

Et la fiche reconstruite tient debout : **22 573 octets**, avec le bloc intérieur, les
diagnostics et le chauffage. Il lui manque les **images DPE/GES** — exactement le coût connu
et accepté de l'option A, rien de plus.

**5c — la descente ciblée, chronométrée** (option ①, accord de Frédéric) :

```
.venv\Scripts\python.exe phase2\sync\pull_from_supabase.py --table app_mandat
  -> app_mandat (le nom local est pris) -> app_mandat__sb
  -> 26 847 lignes en 28 s, 27 appels API
```

Relecture locale : `app_mandat__sb` = **26 847 lignes**, dont **0** dans la plage de l'app
(≥ 1 000 000) — normal, aucun numéro n'a encore été demandé depuis l'app. Le coût se place
bien entre la console (12 s) et le registre des liens (2-3 min), comme annoncé.
**Reste à voir au run de 05:00 demain** : l'étape apparaît dans le journal et le registre
part sans erreur.

**Observé au passage, à ne pas perdre** : pendant la recherche étendue, l'app a affiché un
bandeau **« canceling statement due to statement timeout »** — une requête Supabase expirée,
remontée à l'écran. À verser au **chantier ④**.

---

## 5d — LE FILET DU RATTACHEMENT VISAIT LA MAUVAISE CLÉ

### Étape 1 — Audit du 08/10 · **CONFIRMÉ, et c'est DEUX endroits**

**La racine : une colonne du même nom, au contenu inverse selon la table.** Vérifié par la
**plage des numéros** — qui ne dépend d'aucun nom — et recoupé avec le **miroir Hektor**, qui
ne connaît par construction que les numéros de Hektor (1 … 605 744) :

| table · colonne | plage réelle | contient |
|---|---|---|
| contacts · `hektor_contact_id` | 10 000 003 … 10 650 596 | **NOTRE numéro** *(le nom ment)* |
| contacts · `hektor_target_id` | 3 … 605 743 | Hektor |
| registre des liens · `app_contact_id` | 10 000 026 … 10 650 596 | **nous**, 132 713 / 132 713 |
| registre des liens · `hektor_contact_id` | **47 … 605 743** | **Hektor**, 132 713 / 132 713 |

*(Frédéric l'avait en mémoire et a demandé deux fois de revérifier : « un id app portait encore
hektor id comme libellé ». Il avait raison.)*

**Le worker y cherchait NOTRE numéro, à deux endroits :**

1. **le filet d'échec** (l. 14919) : `annulerRattachementOptimiste(job, annonceId, identite, …)`
   — la fonction filtre sur `hektor_contact_id`. Zéro ligne → **un rattachement refusé par
   Hektor restait affiché, pour toujours** ;
2. **le marquage de réussite** (l. 14954) : `hektor_contact_id=eq.<identite>` → zéro ligne → le
   lien restait `present_in_hektor = false`, donc **non retirable jusqu'au run du lendemain** —
   exactement ce que ce bloc du 03/10 voulait supprimer. Son propre journal le soupçonnait :
   *« Aucune ligne à marquer (déjà établie, **ou posée sous une autre clé**) »*.

**Ce que `cef0ed2` (03/10) avait vraiment fait** : élargir la **portée** du filet aux étapes
précédentes. Il n'a pas touché à la clé.

**Jamais déclenché à ce jour** : 3 rattachements, tous **acceptés** (dernier le 03/10), donc le
filet d'échec n'a jamais servi ; et le marquage **n'a jamais tourné** (ces travaux n'ont pas
l'étape `relation_etablie`, le code étant postérieur — les workers n'ont redémarré
qu'aujourd'hui). Trace : les 2 lignes `source='app'` sont encore `present_in_hektor = false`.

### Étapes 2 et 3 — Correctif (option A, « vas-y » du 08/10)

Utiliser la **cible Hektor que le worker calcule déjà** trois lignes plus haut
(`contactId = await cibleHektorContact(identite)`), aux deux endroits. Et **ne jamais deviner** :
si la traduction elle-même a échoué (`contactId` nul), on ne filtre pas au hasard — on **crie**
dans le journal « à reprendre à la main », comme le fait le geste jumeau. Les journaux nomment
désormais **les deux numéros** (`hektor_contact_id` et `identite_app`), pour que le prochain
lecteur n'ait pas à deviner.

**Vérifié avant de coder, comme annoncé** : les trois filtres du worker sur `app_relation` —
le troisième, `annulerRetraitOptimiste`, filtre sur `app_contact_id` (notre numéro, fourni par
le front dans `payload.app_contact_id`) : **il est juste, je n'y touche pas** ; le garde-fou
`source=eq.app` (on ne touche qu'aux liens nés dans l'app) : **conservé** ; `retire_le=is.null`
(on ne réveille jamais un lien retiré) : **conservé**.

*(Option B — tout aligner sur `app_contact_id` — écartée : le payload du rattachement ne porte
pas `app_contact_id`, contrairement à celui du retrait, et `identite` n'est pas garanti d'être
notre numéro : la RPC accepte les deux.)*

`node --check` ✔. ⚠ **DORMANT** : actif après redémarrage des 4 services worker.
**Retour arrière** : remettre `identite` aux deux endroits.

### Étape 5 — ESSAI RÉEL, 5d est **PROUVÉ** (08/10, ~15:25, workers redémarrés)

Rattachement du mandant d'essai **« M. Test CLOTURE »** (identité 10355757, cible Hektor
605075) à l'annonce d'essai **62774**. *(Il a fallu un contact du MÊME négociateur que le
bien : la recherche de l'écran est filtrée par négociateur — « Aucun contact trouvé pour ce
négociateur » sinon. Recherche par l'identifiant Hektor `605075`, le champ l'accepte.)*

**La ligne posée par la RPC, au clic** — et elle confirme toute l'analyse de la clé :

```
app_relation_id    1000010      <- la plage reservee a l'app
app_contact_id     10355757     <- NOTRE numero
hektor_contact_id  605075       <- celui de HEKTOR  (c'est bien ca, la colonne)
source             app          role_hektor  null    present_in_hektor  false
```

**Puis le worker, 28 secondes plus tard :**

```
relation_etablie : done
   « Le registre porte le lien comme ETABLI : il est visible, et retirable, tout de suite »
present_in_hektor -> TRUE
```

**C'est la première fois que cette étape tourne**, et elle trouve sa ligne. Avant le
correctif elle aurait dit « Aucune ligne à marquer ». Le mandant est donc **retirable tout de
suite**, et non le lendemain.

**Bonus constaté à l'écran** : la carte de Sophie TEST MANDANT 25-08 affiche
« 3 rue de la Chaine, **Saint-Étienne** » — la correction de 5b, redescendue et visible.

**À savoir, et je le dis** : ce 4e mandant **restera attaché** au bien d'essai. Le bouton
« Retirer ce mandant » est grisé dès qu'un numéro de mandat existe (règle de Frédéric), et
62774 porte le mandat n° 18836. Sans conséquence sur une annonce d'essai.

**Non éprouvé** : le filet du **refus** (Hektor qui refuse le rattachement). Je ne sais pas le
provoquer proprement ; le correctif est le même et porte sur la même clé, mais il reste
non éprouvé en réel.

---

## 5e — RETIRER PUIS RATTACHER LE MÊME MANDANT

### Étape 1 — Audit du 08/10, **refait à la demande de Frédéric** · 5 vérifications

| affirmation | vérifiée où | verdict |
|---|---|---|
| la RPC finit par `ON CONFLICT … DO NOTHING` | définition relue **dans la base** | ✔ |
| la vue exige `retire_le IS NULL` | `WHERE (present_in_hektor OR source='app' AND absent_depuis IS NULL) AND retire_le IS NULL` | ✔ |
| **l'écran propose un contact retiré** | la recherche de rattachement interroge la table des **contacts**, jamais les liens (`api.ts:8967`) | ✔ **atteignable sans avertissement** |
| le run de nuit n'efface jamais un retrait | `UPDATE … WHERE app_relation.retire_le IS NULL` — il ne sait que **poser** | ✔ |
| et il **pousse** `retire_le` | `COLONNES_POUSSEES` le contient | ✔ |

**Ce que verrait le négociateur** (plus grave que ce que l'audit du 08/10 décrivait) :

```
au clic        un bandeau « mandant en creation » s'affiche
~30 s apres    le worker recree le lien CHEZ HEKTOR, pour de vrai
puis           le mandant ne rejoint JAMAIS la liste reelle
24 h apres     la ligne provisoire est purgee (status 'linked' > 24 h)
               -> le mandant DISPARAIT, alors qu'il est lie chez Hektor
```

**Cas réel en base** : contact 10355712 sur 62963 et 62964, `retire_le` au 03/10. Hektor n'a
plus ces liens non plus aujourd'hui : **rien ne ment en ce moment**, le piège se referme au
prochain rattachement.

**Et le code avait écrit la condition** (`relation_ledger.py`, 03/10) : *« Tant que le
rattachement n'existe pas dans le front […]. Le complément se posera ICI. »* Le rattachement
existe depuis le 03/10 — **joué en réel aujourd'hui pour 5d**. La condition est levée.

**La règle qui autorise le correctif**, déjà écrite et surveillée (`relation_disparue.py` l. 77) :
*« `retire_le` / `retire_par` APPARTIENNENT À L'APP. Le miroir Hektor ne peut pas les
produire. »* Le cloud fait autorité — dans les deux sens.

### Étapes 2 et 3 — Correctif en DEUX morceaux indissociables

**A · la RPC** (`supabase/patch_5e_rattacher_apres_retrait_2026-10-08*`) : `do nothing` devient
`do update set retire_le = null, retire_par = null, absent_depuis = null`. `app_relation_id`
reste **hors du SET** (on ne renumérote jamais), `present_in_hektor` et `source` ne sont pas
touchés. Empreinte attendue après patch : **`f39e01658e438ab085710a6ecae1a6f2`**.

> Le corps de l'inverse a été **récupéré encodé en base64 depuis la base**, puis décodé :
> md5 `a7213743cbede951bd13ce9e47f3cd14`, 4 569 caractères — **pas une lettre retapée à la
> main** (le corps est en CRLF, le recopier était trop risqué).

**B · le registre de nuit** (`phase2/sync/relation_ledger.py`) : il sait maintenant **lever**
un retrait que la doublure fraîche ne porte plus. Trois gardes :
**fraîcheur** (si la doublure n'est pas du jour on ne lève RIEN, et on le dit — même règle que
la sentinelle ⑥) · **on pilote depuis la petite table** (3 retraits locaux, jamais les 132 713
liens : la leçon des 79 minutes du 03/10) · **on n'efface que ce que la doublure contredit
explicitement** (le couple doit y être ET y porter `retire_le IS NULL`). Le compte
`retraits_leves` entre au bilan du run.

⚠ **A sans B ne tient qu'une journée** : le serveur garderait l'ancien retrait et le
repousserait. Les deux vont ensemble.

`ast.parse` ✔, CRLF et BOM conservés. ⚠ B n'agit qu'au **prochain run de nuit** ; A attend la
répétition puis ton application.

### Étape 5 — répétition exacte (7/7) et patch **APPLIQUÉ** (08/10, ~17:10)

```
AVANT_PATCH = travail cree=oui | retire_le APRES=TOUJOURS POSE   <- le bug
APRES_PATCH = travail cree=oui | retire_le APRES=EFFACE          <- repare
apres_retrait = pose le 2026-10-03 (inchange)  ·  apres_inverse_empreinte = l'avant
```

Patch collé par Frédéric. Contrôle en base, lecture seule :

| contrôle | mesure |
|---|---|
| empreinte normalisée | **`f39e01658e438ab085710a6ecae1a6f2`** = la valeur annoncée avant d'appliquer |
| la clause a bien changé | `on conflict … do update` **posée** ; plus **aucune** clause `do nothing` (l'unique occurrence du texte est dans un commentaire) |
| `app_relation_id` hors du SET | ✔ on ne renumérote jamais |
| nature et droits | `SECURITY DEFINER`, `anon=non`, `authenticated=oui` ✔ |
| rien écrit au passage | 3 retraits toujours en place, 4 travaux de rattachement (les 3 d'avant + l'essai de 5d) ✔ |

**Reste à éprouver en réel**, et ça demande deux temps :
1. retirer puis rattacher un mandant sur un bien d'essai **sans numéro de mandat** (62963 ou
   62964 — sur 62774 le retrait est grisé) et vérifier qu'il **réapparaît au clic** ;
2. vérifier le **lendemain matin** qu'il est **toujours là** — c'est ce qui prouve le morceau B.

### Étape 5 (suite) — ESSAI RÉEL : **le geste marche au clic** (08/10, ~17:40)

Bien d'essai **62963** (« TEST C15 entrepot », **sans numéro de mandat**), mandant
**Sophie TEST MANDANT 25-08** (cible Hektor 605030), **retiré le 03/10 à 18:22**.

**Preuve d'atteignabilité, au passage** : la fiche affichait « Source Registre des liens ·
**0 mandant** » et « Aucun contact lié », et la recherche de rattachement a pourtant **proposé
ce contact retiré, sans le moindre avertissement**. Le scénario n'est pas théorique.

```
au clic   app_relation_id 1000008  (LE MEME -- la ligne n'est pas renumerotee)
          retire_le    2026-10-03  ->  NULL
          retire_par                  ->  NULL
          source       app  (inchange)
          liens visibles du bien :  0  ->  1
+35 s     le worker : done, et l'etape de 5d dit
          « Le registre porte le lien comme ETABLI : il est visible, et retirable,
            tout de suite »
          present_in_hektor  ->  TRUE
```

**Les deux correctifs de la journée s'enchaînent** : 5e efface le retrait, ce qui rend la ligne
éligible au marquage réparé en 5d, qui la bascule 35 secondes plus tard. Avant ce matin, aucun
des deux n'aurait joué.

**Reste à voir demain matin** : que le run de 05:00 **ne repose pas** le retrait — c'est le
morceau B (`relation_ledger.py`), et c'est le seul contrôle qui manque à 5e.

---

## ⏰ À VÉRIFIER APRÈS LE RUN DU 09/10 (05:00) — la liste, dans l'ordre

Trois choses sont en attente de ce run. Le journal du run est dans `logs/` ; le bilan du
registre des liens s'affiche dans la sortie de l'étape « registre des liens (app_relation) ».

**① 5c — la doublure du registre des mandats** *(étape neuve dans `run_full_pipeline.ps1`)*
- l'étape **« phase2 doublure du registre des mandats »** apparaît dans le journal,
  **avant** « phase2 registre des mandats (app_mandat) » ;
- sa durée est de l'ordre de **28 s** (mesure du 08/10 : 26 847 lignes, 27 appels) ;
- l'étape du registre qui suit finit **sans erreur** ;
- en base locale : `app_mandat__sb` porte le nombre de lignes de `app_mandat` en ligne.
- ⚠ Si l'étape **allonge trop le run** (il doit finir avant 08:15, sinon il tombe dans la
  descente — incident du 03/10), le dire : on la déplacera.

**② 5e-B — le registre de nuit lève-t-il le retrait ?** *(le contrôle qui manque à 5e)*
- dans le bilan du registre des liens, le compte **`retraits_leves`** doit valoir **1**
  *(le lien 1000008, Sophie TEST MANDANT 25-08 sur le bien 62963, rattaché le 08/10 à 17:40)* ;
- et en base : `select retire_le, present_in_hektor from app_relation where app_relation_id=1000008`
  → **`retire_le` NULL** et **`present_in_hektor` vrai**.
- ⛔ **Si `retire_le` est de nouveau posé**, le morceau B n'a pas joué : regarder d'abord
  `doublure_du` dans le bilan (la garde de fraîcheur refuse de lever si la doublure n'est pas
  **du jour**), et le message « retraits NON leves : la doublure est du … ».

**③ Rien d'autre n'a bougé**
- durée totale du run comparable aux nuits précédentes ;
- aucune étape en erreur qui ne l'était pas avant ;
- la sentinelle `relation_disparue.py` : `retraits_perdus` = 0 et `doublure_perimee` = 0.

**④ 5a — le bien désarchivé du 08/10** *(point resté ouvert)*
- le bien **78 (VA2380)** doit être revenu dans le parc vivant après la descente : il était
  sorti des archives sans y entrer (`ni archives ni parc vivant` le 08/10 à 10:47).
  `select count(*) from app_dossier_current where hektor_annonce_id=78` → **1 attendu**.

---

## 5f — L'ÉCHEC PASSAGER SUR UNE TRANSACTION

### Étape 1 — Audit · **ce n'est pas un défaut à corriger : c'est une décision à moitié appliquée**

Frédéric : *« cherche s'il y a une explication dans les notes avant de changer, le worker a été
testé de nombreuses fois et normalement tout avait été prévu »*. **Il avait raison.**

**① Pourquoi le worker restaure** — commit `c484c28` du 29/08 :
> *« Sans l'état précédent dans le payload, le worker ne saurait pas quoi restaurer si Hektor
> refuse — et l'app afficherait "offre refusée" alors qu'elle ne l'est pas, **indéfiniment**.
> C'est exactement le mensonge silencieux que ce projet chasse. »*

Décision délibérée : à l'époque, **il n'y avait pas de filet de rejeu**, restaurer était la
seule façon de ne pas mentir.

**② Et la suite était décidée le même jour** — plan, tâche C.4-bis :
> ⚠ *UN CHOIX DE CONCEPTION, TRANCHÉ PAR FRÉDÉRIC LE 29/08 : aujourd'hui, quand Hektor refuse,
> le worker remet l'état d'avant. **Avec un rejeu, ce sera l'inverse — on garde l'état affiché
> et on réessaie en arrière-plan**, comme une édition qui attend. Contrepartie assumée :
> pendant **jusqu'à 25 minutes**, l'app peut montrer un état que Hektor n'a pas encore.*

**③ Ce qui s'est passé** : le filet a été construit les 29-30/08 (cron `app-action-retry-due`,
chaque minute, **actif**, et il couvre bien les quatre gestes) — **la bascule du comportement
ne l'a jamais suivi**. Le `catch` attrape TOUT (réseau, session expirée, délai de 60 s) et
traitait un incident passager comme un refus, en écrivant « Hektor a refusé », ce qu'on ne sait
pas. Puis le filet rejouait, le rejeu réussissait, et rien ne reposait l'état chez nous.

**Jamais arrivé** : 47 travaux de transaction, **0 en erreur**, le dernier le 18/09. Mais le
filet, lui, a déjà servi : 3 travaux menés à bien à la 2ᵉ tentative, 2 à la 4ᵉ.

### Le périmètre, vérifié à la demande de Frédéric (« il ne faut rien casser »)

| ce que fait l'écran | crée un travail Hektor ? | concerné par ce chemin ? |
|---|---|---|
| `app_edit_affaire_optimistic` — prix, dates, séquestre | **non** | **non** |
| `app_repartition_commission_set` — répartition de commission | **non** | **non** |
| `app_geste_affaire_optimistic` — les 4 gestes d'état | **oui**, avec l'état précédent | **oui** |

Les huit appels à la restauration appartiennent à **quatre handlers seulement** : offre,
annulation de compromis, suppression de compromis, suppression de vente. Le **changement de
statut d'annonce** n'appelle pas `restaurerEtatAffaire` : il n'est pas touché.
**Une répartition de commission ne peut pas passer par ici** — elle ne crée aucun travail.

### Étapes 2 et 3 — Codé : appliquer la décision du 29/08

Un garde-fou `leFiletVaRejouer(job)` **dont les seuils sont copiés du filet, pas inventés**
(types rejouables, tentatives 1 à 4, 24 h). Si le filet va rejouer, on **conserve l'état
affiché** et le journal dit « envoi échoué — l'état affiché est CONSERVÉ, le filet rejouera ».
Sinon, on restaure comme avant.

**Éprouvé hors ligne, 6 cas sur 6** (banc monté sur le code réel extrait du worker) :

```
  CONSERVE   geste d'etat, 1re tentative, recent
  CONSERVE   geste d'etat, 4e tentative, recent
  RESTAURE   geste d'etat, 5e tentative -- le filet s'arrete
  RESTAURE   geste d'etat vieux de 30 h -- hors fraicheur
  RESTAURE   geste NON rejouable (creation)
  RESTAURE   payload abime : pas de date
```

`node --check` ✔, CRLF conservés. ⚠ **DORMANT** : actif après redémarrage des 4 services.
**Retour arrière** : retirer le `if` en tête de `restaurerEtatAffaire`.

**Pas fait, et c'est volontaire** : remettre l'état quand le geste est **vraiment abandonné**
(5 tentatives, ou « abandon » choisi dans le bandeau — `app_action_resolve` ne restaure rien
aujourd'hui). C'est la suite logique, elle touche deux fonctions SQL : **à décider séparément**.

---

## 5g — SUPPRIMER UN CONTACT

### Étape 1 — Audit du 08/10 · **CONFIRMÉ, troisième fois la même racine**

Supprimer un contact nettoie **trois endroits** : Supabase, notre couche locale, et le miroir
Hektor. Les deux derniers sont nettoyés par un seul script, qui ne recevait **qu'un numéro**.

| base locale | plage de `hektor_contact_id` | c'est donc |
|---|---|---|
| miroir `data/hektor.sqlite` | **1 … 605 744** | le numéro **de Hektor** |
| notre couche `phase2.sqlite` | **10 000 001 … 10 650 597** | **notre** numéro |

Le worker envoyait **notre** numéro aux deux. Donc :
Supabase nettoyé ✔ · notre couche nettoyée ✔ · **le miroir : rien**.

**Et c'est le miroir qui recompose notre couche** : 356 416 contacts dans le miroir,
**356 416** dans notre couche — une projection ligne à ligne. **Le build suivant remettait le
contact.** Muet, en plus : le journal écrivait « caches locaux nettoyés » sans avoir rien
nettoyé.

**Dormant, et daté** : 12 suppressions en tout, la dernière le **21/09** — avant la bascule du
23/09, quand les deux numéros étaient encore égaux. **Le défaut est né le 23/09 et n'a jamais
servi.**

**⚠ Une mesure que je me suis interdit d'utiliser** : 63 234 liens vivants pointent un contact
absent de `app_contact_current`. **Ce n'est pas un symptôme de ce défaut** — c'est le périmètre
cloud connu (62 162 contacts sur 356 416).

### Étapes 2 et 3 — Codé (décision de Frédéric du 08/10)

**① Les deux numéros au script.** `delete_local_contact.py` prend un `--cible-hektor`
optionnel : notre numéro pour `phase2.sqlite`, celui de Hektor pour le miroir. **Rétrocompatible**
— sans l'argument, comportement d'avant. Le worker, qui connaît déjà les deux, les passe.

**② Le registre des liens suit la suppression — lignes PHYSIQUEMENT EFFACÉES.**
*Décision de Frédéric, 08/10 : « si on supprime un contact il faut aussi mettre à jour le
registre des relations pour effacer ce contact », puis « je veux que les lignes soient
physiquement effacées, en plus normalement Hektor fera tout seul de même ».*

> **C'est une exception assumée au DELETE-NEVER du registre.** Cette règle existe pour qu'un
> **silence de Hektor** n'efface rien ; elle ne vise pas une suppression **voulue** par un
> humain dans notre app. La trace reste au journal du travail et dans
> `app_deleted_contact_log` — pas dans le registre.

**Et il faut les DEUX côtés, c'est la leçon du point 5e** : effacer en ligne sans effacer en
local ne tiendrait pas une nuit — `relation_ledger` pousse la table **locale** en upsert, le run
remettrait les lignes. Le worker efface en ligne, `delete_local_contact.py` efface en local,
dans la même suppression.

**L'ordre compte pour la sentinelle** : `relation_disparue` exige que tout lien de
`app_contact_relation_current` soit dans `app_relation` (`source_absents`, **zéro exigé**). Le
script efface les deux tables dans la même transaction : la garde reste à zéro.

La clé utilisée est **`app_contact_id`**, notre numéro : dans `app_relation`, la colonne
`hektor_contact_id` porte celui de Hektor (132 713 sur 132 713). **C'est la même confusion qui
a cassé 5b, 5d et 5g** — trois points sur six, la même racine.

`node --check` ✔, `ast.parse` ✔, CRLF conservés. ⚠ **DORMANT** : actif après redémarrage des
4 services. **Retour arrière** : retirer l'argument et le bloc du registre.

---

## 5h — CRÉER UN MANDANT QUI ÉCHOUE

### Étape 1 — Audit du 08/10 · **confirmé, mais la moitié du geste va déjà bien**

Le clic « créer un mandant » (`app_create_mandant_contact_optimistic`) écrit **le contact
durablement** dans `app_contact_current` — avec notre numéro et **sans numéro Hektor** — et
**le lien en provisoire**, avec un jeton.

**Si le worker échoue** : la ligne provisoire du **lien** est marquée en erreur, le bandeau
l'affiche en rouge, elle est purgée à 24 h. **Cette moitié fonctionne.**

**Ce qui reste : le contact.** Il demeure dans l'annuaire, indiscernable d'un vrai. Et **rien
ne le rattrape** — vérifié, pas supposé :

| | |
|---|---|
| le **filet de rejeu** | **exclut les créations** — décision du 29/08, « rejouer une création la DOUBLE » |
| le **push de nuit** | ne supprime que ce qu'il a **lui-même envoyé** (il compare à son propre état d'envoi). Un contact né seulement dans Supabase n'y figure pas : jamais déclaré disparu, jamais effacé |
| le **build** | travaille depuis le miroir : il ne le voit pas, et ne lui donnera jamais de numéro |

**Dormant** : **0** contact sans numéro Hektor aujourd'hui ; 17 créations de mandant, **0 en
erreur**, la dernière le 25/08. Le défaut est armé depuis la bascule du 23/09.

**⚠ Et garder le contact est VOULU** : c'est C.1', *« une saisie ne se perd jamais »*. Jeter le
nom, l'adresse et le téléphone qu'un négociateur vient de taper parce que Hektor a eu un hoquet
serait pire. **Le défaut n'est pas qu'il reste : c'est qu'on ne le dit pas.**

### Étapes 2 et 3 — Option A : une sentinelle *(choix de Frédéric)*

**D'abord vérifié qu'il n'y en avait pas déjà une** *(à sa demande)* : les 8 contrôles de
`quality_checks.py` sont `registre_couche_desaccord`, `registre_identite_mal_rangee`,
`vue_generale_total`, `demandes_total`, `missing_titles`, `view_generale_without_dossier`,
`demandes_without_view_generale`, `mandat_numero_id_collision`. **Aucun ne couvre ce cas.**

**Ajoutée** : `contact_sans_numero_hektor`, **zéro attendu**. Pas de nouvelle colonne, pas de
migration : l'absence de `hektor_target_id` **est** la signature.

> ⚠ **Elle lit la DOUBLURE `app_contact_current__sb`, pas notre couche locale** — et c'est tout
> le sujet : le contact orphelin n'existe **que** dans Supabase ; notre couche est une
> projection du miroir Hektor et ne le verra jamais. **Une sentinelle posée sur la couche
> locale aurait rendu 0 en mentant.**

**Et elle est LUE** — sinon ce n'est pas une garde. Ajoutée au moniteur de santé
(`check_gti_health.py`, sonde `data.contacts_sans_hektor`, seuil 0, **critique** au-dessus),
sur le patron exact des deux contrôles d'identité : **la formule reste dans `quality_checks.py`
et le moniteur la lit par sa clé** — une seule copie de la règle.

**Éprouvé** : `run_quality_checks.py` passe et le rapport porte
`contact_sans_numero_hektor : 0 | attente : 0`.

### 5g — ESSAI RÉEL : **tout est parti, des deux côtés** (08/10, ~19:00)

Contact d'essai **« M. Test CLOTURE »** (identité 10355757, cible Hektor 605075), supprimé
depuis l'annuaire de l'app. *(Il portait 2 liens : celui que j'avais rattaché au bien 62774
pour éprouver 5d, et un lien venu de Hektor sur le bien 62966 — l'essai défait donc aussi ma
manipulation de l'après-midi.)*

La phrase de confirmation demandée est **« SUPPRIMER CONTACT 10355757 »** — l'**identité**,
pas la cible : le correctif du 21/09 tient.

**Travail : `done` en 14 s**, et son journal porte la nouvelle étape :
`claim | hektor_context | hektor_contact_delete | sync_queue ×3 | local_cleanup |
`**`registre_des_liens`**` | finish`.

| | avant | après |
|---|---|---|
| **miroir** `hektor_contact` (clé Hektor 605075) | 1 | **0** ✔ *(c'était le trou : il ne partait pas)* |
| **miroir** `sync_contact_state` | 1 | **0** ✔ |
| **miroir** `sync_annonce_contact_link` | 2 | **0** ✔ |
| **couche** `app_contact_current` (clé identité) | 1 | **0** ✔ |
| **couche** `app_relation` | 1 | **0** ✔ |
| **couche** `app_contact_relation_current` | 4 | **0** ✔ |
| **en ligne** contact · registre · couche | 1 · 2 · 4 | **0 · 0 · 0** ✔ |

**Les deux moitiés du correctif sont prouvées** : le miroir reçoit enfin le bon numéro (sans
quoi le build aurait remis le contact), et le registre des liens est **physiquement effacé**
des deux côtés — donc le push de nuit ne les remettra pas.

**5g est fini.**

---

## 5i — LE CONFLIT CAUSÉ PAR L'APP ELLE-MÊME

### Étape 1 — Audit du 08/10

Quand un négociateur corrige un champ, la saisie attend **10 minutes** (le temps qu'il finisse
de taper), avec une **photo de l'heure de dernière modification chez Hektor** prise au clic.
Dix minutes plus tard, avant d'écrire, le worker vérifie que Hektor n'a pas bougé. S'il a
bougé : **il gagne**, et la saisie était **soldée** — jetée, archivée au journal des
résolutions, **et aucun bandeau**.

**Le défaut : le garde-fou regarde une HEURE, pas une signature.** Or l'app écrit aussi chez
Hektor :

```
14:00  le negociateur corrige le prix       -> en attente, photo de l'heure Hektor
14:03  LE MEME negociateur change le statut -> ce geste part TOUT DE SUITE chez Hektor
14:10  le worker : « Hektor a bouge »       -> la correction du prix est JETEE
```

Personne n'a rien tranché, et le bandeau « saisie en conflit » — qui existe pourtant, avec ses
deux boutons — **ne s'affiche pas**, puisque la ligne est supprimée et non gardée.

**Jamais arrivé** : **0** résolution pour cause `hektor_plus_recent` (le journal n'en porte que
2, et ce sont des gestes de transaction) ; 0 saisie en attente aujourd'hui.

### ⭐ La remarque de Frédéric qui donne la règle

> *« Ce ne sont pas vraiment les mêmes demandes, sinon elles seraient réunies pendant les
> 10 minutes, non ? »*

**Exact, et vérifié** — ce sont **deux circuits** :

| | circuit **débouncé** | circuit **immédiat** |
|---|---|---|
| porte | les **champs** (prix, surfaces, textes) | les **gestes d'état** (statut, archiver, négociateur, transactions) |
| part | après 10 min, et **fusionne** : une ligne par bien | **tout de suite**, un travail par geste |

Et `app_edit_annonce_optimistic` ne touche **ni le statut, ni l'archivage, ni le négociateur**
(relu dans son code). **Deux tiroirs séparés : aucun champ commun possible.** Mesure :
68 travaux d'édition de champs, dont **43 débouncés** et **25 directs**.

### Étapes 2 et 3 — Codé

```
Hektor a bouge depuis la photo. QUI ?
  un de NOS gestes d'etat    -> aucun champ commun -> ON POUSSE la saisie
  tout le reste (autre edition de champs, un humain dans Hektor, ou on ne sait pas)
                             -> ON NE JETTE RIEN : la saisie reste EN CONFLIT,
                                le bandeau s'affiche, le negociateur tranche
```

**Plus jamais de saisie jetée en silence**, dans aucune des deux branches.

**Vérifié avant de coder, comme promis** : marquer la saisie en conflit **fait bien apparaître
un bandeau** — `app_annonce_edit_status` rend `conflict`, et `AnnonceEditStatusBanner` l'affiche
avec ses deux boutons (« j'ai refait » / « j'abandonne »).

> ⚠ **Ceci modifie la décision du 20/09** (« Hektor plus récent → il gagne, on solde »). Elle
> valait quand l'autre écrivain était un humain dans Hektor : il avait vraiment tranché. Elle
> ne vaut pas quand l'autre écrivain, c'est nous. `app_annonce_pending_solder_hektor` n'est
> **plus appelée ici** — elle reste en place, elle n'est pas supprimée.

> ⚠ **On ne compare jamais l'heure de Hektor à la nôtre** : l'une est locale, l'autre en UTC,
> deux heures d'écart suffiraient à tout fausser. On compare **nos deux dates entre elles** —
> `dirty_at` (l'heure de la saisie) et `finished_at` (la fin du travail), toutes deux écrites
> par nous.

> ⚠ **Si la question ne peut pas être posée** (lecture impossible), on répond « je ne sais
> pas » et on retombe sur le cas prudent : conflit et bandeau.

`node --check` ✔, CRLF conservés. ⚠ **DORMANT** : actif après redémarrage des 4 services.
**Non éprouvé en réel** : il faudrait provoquer la séquence « corriger un champ puis changer le
statut dans les 10 minutes » sur un bien d'essai — faisable, à faire si Frédéric le veut.

---

## ✅ LE CHANTIER EST FINI — bilan du 08/10, et ce qui reste

### Ce qui a été réparé, et comment on le sait

9 points, **6 prouvés par un geste réel en production** (5a, 5a ter, 5b, 5d, 5e-A, 5g),
1 sentinelle posée et lue (5h), 1 éprouvé hors ligne et actif (5f), 1 codé et dormant (5i).
**4 patchs SQL** appliqués par Frédéric après répétition (5a, 5b, 5e, et le correctif de la
garde de retour arrière), **1 déploiement front** (le bouton de désarchivage, `78e6574`),
**3 fichiers serveur** touchés (`console_job_worker.js`, `relation_ledger.py`,
`delete_local_contact.py`), **1 étape ajoutée au run**, **1 sentinelle** de plus.

### La racine commune, qu'il faut retenir

**Trois des neuf bugs (5b, 5d, 5g) venaient de la même chose** : une colonne nommée
`hektor_contact_id` qui ne contient pas la même chose selon la table. Le nom ment, la
**plage** dit la vérité. Tant que les deux numéros coexistent (jusqu'à `L4-c`), **tout code
qui mêle les deux mondes est suspect** : il faut mesurer min/max des deux côtés avant
d'écrire une jointure ou un filtre.

**Deux autres (5f, 5i) n'étaient pas des négligences mais des décisions à moitié
appliquées** : 5f était la seconde moitié de C.4-bis (29/08), 5i amende la règle du 20/09.
On ne l'a su que parce que Frédéric a exigé de chercher le *pourquoi* avant de changer.

**Un sur neuf (5c) était un faux** de l'audit par objet : j'avais conclu d'un commentaire de
code au lieu de mesurer la base. La hiérarchie est **la base > le code > les notes**.

### ⏰ Ce qui reste à faire, dans l'ordre

1. **Le run du 09/10** — la liste détaillée est dans la section
   « ⏰ À VÉRIFIER APRÈS LE RUN DU 09/10 » ci-dessus (5c et 5e-B).
2. **Allumer 5i** : redémarrer les 4 services worker (accord de Frédéric, en journée, file
   des documents vide), puis l'essai réel ci-dessous.
3. **Le marqueur à l'écran et le bouton « réessayer » de 5h** (options B et C) — pas faits,
   ils relèvent du chantier ④ « aucun échec silencieux ».
4. **L'abandon réel de 5f** (rendre l'état quand le filet a vraiment renoncé : 5 tentatives
   ou « abandon » humain) — touche 2 fonctions SQL, chantier ④.
5. **Les ~25 champs que l'API de Hektor ne rend jamais** (chauffage mis à part : il a sa
   source `chauffage_console_json`) : 5 textes de secteur, 2 images DPE/GES, le détail de la
   grille d'honoraires — **chantier ⑥**, pas celui-ci.

### Le mode opératoire de l'essai réel de 5i (à faire après le redémarrage)

Ce que 5i change ne se voit **que** si l'app elle-même fait bouger Hektor pendant les
10 minutes d'attente d'une saisie. La séquence :

```
1. REDEMARRER les 4 workers  (admin, file documents vide, accord de Frederic)
       Get-Service HektorConsoleWorker* | Restart-Service -Force
2. Sur un bien d'essai SANS numero de mandat (62963 ou 62965) :
       a. corriger un champ de texte  ->  cree la ligne app_annonce_pending (10 min)
       b. DANS LA MEME MINUTE, changer le statut  ->  part tout de suite en travail
3. Attendre que les 10 minutes s'ecoulent, puis lire :
       - app_annonce_pending : la ligne doit etre PARTIE (push_job_id renseigne, pas de
         conflit « hektor_plus_recent »)
       - le journal du worker : « annonce_overwrite_guard » doit dire que le mouvement de
         Hektor vient de NOUS (le geste d'etat), et laisser passer la saisie
       - chez Hektor : le champ corrige DOIT porter la nouvelle valeur
4. AVANT le correctif, la saisie aurait ete SOLDEE au journal des resolutions (perdue pour
   Hektor) : c'est exactement ce qu'on veut ne plus voir.
```

⚠ **À ne pas faire sur une vraie annonce** : l'essai écrit chez Hektor.
