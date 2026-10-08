# CHANTIER ⑤ — LES GESTES CASSÉS (5a → 5i)

> Ouvert le 08/10/2026. Source : `notice/AUDIT_OBJETS_ETAPE2_2026-10-08.md` §2 ⑤ et §3.
> Méthode (Frédéric, 08/10) : **audit du sujet → explication des correctifs → « vas-y » →
> code → contrôle du résultat → documents**. Un point à la fois, dans l'ordre 5a → 5i.
> Toute explication de correctif porte la rubrique **« ce que ça pourrait casser ailleurs »**.

## Les points et leur état

| # | Le geste cassé | Objet | État |
|---|---|---|---|
| 5a | Désarchiver une annonce | Annonce | 🔎 audit refait le 08/10 — **confirmé** |
| 5b | Modifier un mandant depuis sa carte | Mandant | ⬜ |
| 5c | Premier n° de mandat demandé depuis l'app (dormant) | Mandat | ⬜ |
| 5d | Filet du rattachement sur la mauvaise clé | Mandant | ⬜ |
| 5e | Retirer puis rattacher le même mandant | Mandant | ⬜ |
| 5f | Retour d'état après un échec passager (offre / compromis) | Transaction | ⬜ |
| 5g | Supprimer un contact : le nettoyage local rate sa cible | Contact | ⬜ |
| 5h | Mandant créé en échec : rien n'est défait | Mandant | ⬜ |
| 5i | Conflit causé par l'app elle-même | Annonce | ⬜ |

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
