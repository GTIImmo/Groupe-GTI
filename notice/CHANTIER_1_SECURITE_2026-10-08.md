# CHANTIER ① — SÉCURITÉ : ce que la clé publique peut atteindre — 08/10/2026

*Étape 2 · chantier ① · audit fait · explication faite · « vas-y » de Frédéric le 08/10 (patch : oui ;
`hektor-diffusion` : option (a) ; supprimer les 3 comptes : **non**) · **code écrit, attend la répétition puis
l'application par Frédéric**.
Audit en lecture seule : catalogue Supabase, `git grep` des appelants, conseiller de sécurité
Supabase. Rien n'a été modifié.*

## Rappel : la clé publique

Le front embarque la clé `anon` de Supabase : **elle est lisible par n'importe qui** dans le
navigateur. Avec elle seule, sans se connecter, on parle à la base sous le rôle `anon`. Tout
ce que `anon` peut lancer ou lire est donc **public**. Une fonction `SECURITY DEFINER`
s'exécute avec les pleins droits du propriétaire (postgres), **sans** les règles de
protection (RLS) : si elle ne vérifie pas elle-même qui l'appelle, elle est grande ouverte.

## L'historique — ce qui a déjà été fait (♻)

- **24/08, tâches 0.4, 0.5, 0.7** : `app_dossiers_current` fermée à `anon` ; 5 vues de
  surveillance fermées ; audit de 85 fonctions, **12 fonctions de maintenance fermées**
  (balayages, recalculs, `claim_next_job`). **36 fonctions laissées ouvertes en « DETTE
  ASSUMÉE »** (« surtout des lectures que le front appelle »).
- **29/08, `patch_c19_fermer_anon_2026-08-29.sql`** : le piège est écrit noir sur blanc :
  `REVOKE … FROM PUBLIC` **ne suffit pas**, Supabase accorde EXECUTE à `anon` et
  `authenticated` par **privilège par défaut** sur toute fonction neuve. La règle :
  `REVOKE … FROM PUBLIC; REVOKE … FROM anon; GRANT … TO authenticated, service_role`.
- **Depuis**, la règle n'a pas été appliquée partout : la bascule des contacts (23/09), les
  fonctions photos (G.10→G.17), le soldage d'une saisie (20/09) sont nés ouverts.

## La mesure du 08/10

| | Mesure |
|---|---|
| Fonctions du schéma `public` | 172 ; **136 exécutables par `anon`**, dont **94 à pleins droits** (`SECURITY DEFINER`) ; 36 déjà fermées |
| Privilège par défaut | `anon` reçoit encore EXECUTE sur **toute fonction neuve** (`pg_default_acl`) : la cause de la rechute |
| Fonctions à pleins droits **sans aucune garde** (ni `auth.uid()`, ni rôle) | **53** — dont 20 qui **écrivent** |
| Tables protégées par RLS | ✅ toutes leurs règles exigent un utilisateur actif ou un rôle (vérifié sur `pg_policies`) |
| Tables **sans RLS** lisibles et modifiables par `anon` | **2** : `app_console_job_error_archive`, `app_rapprochement_search_state` |
| Vues qui **contournent** la RLS (propriétaire postgres, pas `security_invoker`) lisibles par `anon` | **15**, dont `app_registre_mandats_current` et `app_contact_relations_current` |
| Comptes de connexion | 8, tous créés par l'admin (aucun inconnu) ; 2 désactivés côté app, 1 sans profil — **ils peuvent encore se connecter** |
| Conseiller de sécurité Supabase | 2 alertes **ERROR** : `security_definer_view`, `rls_disabled_in_public` |
| Fonction Edge `hektor-diffusion` | ACTIVE (v14, avril). Exige une connexion, mais **aucun contrôle de rôle ni de compte actif** ; écrit chez Hektor (rend diffusable). Le front ne l'appelle plus (il passe par l'API Render, `api.ts:5143-5265`) |

### Les plus graves (écrivent, sans garde, ouvertes à `anon`)

`app_bascule_identite_contact_annuler` (ramène tous les contacts au n° Hektor sur 13 tables) ·
`app_bascule_identite_contact` · `app_attribuer_chaines_affaire` ·
`app_annonce_pending_solder_hektor` · `app_annonce_reappliquer_saisies` ·
`app_repartition_absorber` · `app_repartition_purger_orphelines` · les 4 fonctions photos ·
`app_set_bien_statut` · `app_record_proposition` · `app_create_relance_for_contact` ·
`app_relance_set_status` · `app_mark_notification_read` · `app_console_mark_document_signed_manual`
· `app_console_touch_document` · `app_upsert_dossier_estimation_*` ·
`app_update_mandant_contact_optimistic`.

## Qui appelle quoi (`git grep`, + dépendances SQL)

| Appelant | Clé utilisée | Conséquence |
|---|---|---|
| front `apps/hektor-v1` | `anon` **+ jeton de l'utilisateur connecté** → rôle `authenticated` | garder `authenticated` sur ce que le front appelle |
| backend Render | `anon` + jeton utilisateur (`auth.py:21`), ou `service_role` | idem |
| worker, `phase2`, `monitoring` | `service_role` (0 usage de la clé anon) | garder `service_role` |
| crons `pg_cron` | `postgres` | non concernés |
| fonctions appelées **par d'autres fonctions** | toutes appelées depuis des fonctions `SECURITY DEFINER` (vérifié) | s'exécutent en postgres : non concernées |
| `can_access_current_dossier`, `can_access_v1_dossier` | utilisées **dans des règles RLS** | garder `authenticated` |
| `apps/rdv-public`, vitrine | passent par l'API ou sont statiques | n'utilisent pas `anon` directement |

**Personne n'a besoin du rôle `anon` sans être connecté.**

### Ce que les internautes doivent continuer de voir *(question de Frédéric, 08/10)* — vérifié

| Ce que voit l'internaute | Par où ça passe | Touché par le patch ? |
|---|---|---|
| **Photos** (vitrine, e-mails, espace client) | coffre `gti-photo` **public** de Supabase Storage : adresse `…/storage/v1/object/public/gti-photo/…`, lue sans aucun rôle de la base | **non** — le patch ne touche que le schéma `public` (fonctions, 15 vues, 2 tables), pas le stockage |
| **Vitrine** (`vitrine-main`) | page statique hébergée à part ; elle lit **un fichier JSON** (`exports/catalogue_vitrine.json`) fabriqué la nuit par le run avec la clé de service (`script.js:539-546`) ; aucun appel à Supabase depuis le navigateur | **non** |
| **Espace client** (`/espace/{token}`, avis ❤/✕, message, visite, recherche) | pages fabriquées par le **backend Render**, qui lit la base avec la **clé de service** (`espace_client.py:726-730`) ; le navigateur ne parle qu'au backend (`espace_portal.py:492, 527, 651`) | **non** |
| **Prise de RDV et estimation publiques** (`apps/rdv-public`) | appels au backend `/public/appointments/…` (`app.js:668-753`), clé de service côté backend (`appointment_service.py:52`) | **non** |
| **Liens des e-mails** (`/r/feedback/{token}`, `/visite/{token}`) | backend, clé de service (`emails.py`, `visite.py`) | **non** |
| **Documents** (coffre privé) | lecture par un utilisateur **connecté** (règles `storage` en `authenticated`) | **non** (`authenticated` est gardé) |

### Détail technique qui change le patch

Pour **121 des 136** fonctions, `anon` reçoit son droit **deux fois** : en direct **et** via le
droit « tout le monde » (`PUBLIC`). Retirer `anon` seul ne suffirait donc pas : le patch retire
aussi `PUBLIC`. C'est sans risque : `authenticated` et `service_role` ont leur droit **explicite
sur les 136** (mesuré), ils ne dépendent pas de `PUBLIC`.

## Les correctifs proposés (en attente du « vas-y » et de l'accord base de production)

Un patch SQL `supabase/patch_chantier1_fermer_anon_2026-10-08.sql`, versionné, que Frédéric
colle (écriture prod), **en quatre lots** :

- **Lot A — fermer `anon` sur toutes les fonctions du schéma `public`** (136) et **le privilège
  par défaut** (`ALTER DEFAULT PRIVILEGES … REVOKE EXECUTE ON FUNCTIONS FROM anon`), pour que
  la rechute ne se reproduise plus. `authenticated` et `service_role` gardent leurs droits.
- **Lot B — réserver au serveur** les 20 fonctions que seul le serveur appelle (worker,
  `phase2`, ou d'autres fonctions) : retirer aussi `authenticated`, garder `service_role`.
  Dont les deux fonctions de bascule.
- **Lot C — les 15 vues** : retirer `anon` (lecture ET écriture) ; pour les 13 que le front
  n'utilise pas (surveillance, `phase2`), retirer aussi `authenticated`.
- **Lot D — les 2 tables sans RLS** : retirer `anon` et `authenticated`, activer la RLS (le
  worker passe en `service_role`, les fonctions en postgres : non concernés).

**Hors patch, à décider** : la fonction Edge `hektor-diffusion` (voir ci-dessous : **ce n'est
PAS une fonction morte**, c'est un chemin de secours) ; les 3 comptes désactivés ou sans
profil qui peuvent encore se connecter. **Après le patch, il restera** que tout utilisateur
**connecté** peut appeler les 33 fonctions de lecture/écriture du front sans contrôle de rôle :
c'est le chantier ② (droits).

**Retour arrière** : un script inverse (les `GRANT` d'origine) est livré avec le patch.

**Contrôle prévu** : avant/après en base (`has_function_privilege`) ; appel réel avec la clé
publique seule → refus ; l'app connectée (annonce, contact, rapprochements, registre, cockpit)
sans erreur dans la console ; une nuit de run sans échec ; conseiller de sécurité relu.

## La fonction Edge `hektor-diffusion` — ce qu'elle est *(08/10, à la demande de Frédéric)*

**Ce qu'elle fait.** C'est le geste « **mettre une annonce en diffusion** » : rendre l'annonce
diffusable chez Hektor (`ensureDiffusable`), puis poser ses portails (`app_diffusion_target`,
remis aux portails par défaut de l'agence pour l'action `accept`). C'est le même geste que
l'acceptation d'une « Validation » par la direction (mémoire `validation-diffusion-flux`).

**Son histoire.** Créée le **07/04/2026** (`4ca9544`), le jour même où naissait le serveur
Python (`f0fc6a3`). Le serveur Render a repris le même geste dès le **08/04** (`d2fe0d3`,
`backend/app/routers/hektor_diffusion.py`). Dernière modification de la fonction Edge le 21/04.

**⚠ Elle n'est pas morte : c'est un chemin de SECOURS.** Le front (`api.ts:7093-7128` pour
`apply`, `:7204-7238` pour `accept`) choisit **dans cet ordre** :
1. le serveur Render, si son adresse est configurée (`VITE_BACKEND_API_URL`) — cas normal ;
2. **sinon la fonction Edge** ;
3. sinon le serveur local de développement.
Journaux Supabase : **0 appel en 24 h** (fenêtre maximale consultable).

**La différence de sécurité entre les deux chemins :**

| | serveur Render (chemin normal) | fonction Edge (secours) |
|---|---|---|
| exige une connexion | oui | oui |
| exige un compte **actif** et **admin ou manager** | **oui** (`assert_admin`, `supabase_admin.py:216-224`) | **non** : tout compte connecté, même désactivé |

**Correctifs possibles (à décider par Frédéric, PAS dans le patch SQL) :**
- **(a)** lui ajouter le même contrôle que Render (compte actif + admin ou manager) et la
  redéployer : le secours reste, il devient aussi sûr que le chemin normal ;
- **(b)** la retirer : alors il faut aussi retirer le secours dans le front (sinon, si Render
  n'est plus configuré un jour, le bouton échouerait au lieu de basculer) ;
- **(c)** ne rien faire : le risque est limité aux 8 comptes existants, dont 3 désactivés ou sans
  profil qui peuvent encore se connecter.

## Le code écrit (08/10, après le « vas-y »)

### Le patch SQL — 3 fichiers dans `supabase/`

| Fichier | Rôle |
|---|---|
| `patch_chantier1_fermer_anon_2026-10-08.sql` | **le patch**, en une transaction : garde-fou d'entrée → **photo d'avant** (`app_securite_droits_avant_20261008`, 2 546 lignes prévues) → lots A à E → **contrôle de sortie** (une seule erreur = tout est annulé) |
| `patch_chantier1_fermer_anon_2026-10-08_INVERSE.sql` | le retour arrière : relit la photo d'avant et rend chaque droit à l'identique, remet les défauts et la RLS d'avant |
| `patch_chantier1_fermer_anon_2026-10-08_REPETITION.sql` | **la répétition** : joue le VRAI patch puis le VRAI inverse, puis lève une erreur volontaire → **rien ne change**. Résultat attendu : « ESSAI ANNULE » avec, après patch, `anon_fonctions=31` (pg_trgm), `auth_fonctions=135`, `photo=2546` ; après inverse, `anon_fonctions=136`, `auth_fonctions=155` |

**Pourquoi une répétition par Frédéric** : le garde-fou de la session a refusé que je l'exécute
moi-même (même annulée), comme le 24/09. Je ne le contourne pas.

**Éprouvé en lecture (08/10)** : lot A vise 141 fonctions ; lot B en trouve 20/20 ; l'app
connectée en gardera 104 (= le contrôle de sortie) ; 17/17 objets nommés existent ; 0 objet du
schéma n'appartient à un autre rôle que postgres ; PostgreSQL 17.6 (le droit `MAINTAIN` existe) ;
aucune fonction de l'app hors du schéma `public` (le retrait global de PUBLIC sur les fonctions
futures ne touche donc rien d'autre).

### La fonction Edge `hektor-diffusion` — option (a)

- **Ajouté** : `isActiveAdminOrManager` — le même contrôle que le chemin Render
  (`supabase_admin.py:216-224`) : profil trouvé par id puis par e-mail, **actif** et **admin ou
  manager**, sinon réponse 403 « Acces admin refuse ». Additif : 32 lignes, rien d'autre ne bouge.
- **Syntaxe vérifiée** (compilateur TypeScript 5.9.3 du front : 0 erreur). Deno n'est pas
  installé : pas de vérification de types complète.
- ⚠ **Trouvé en vérifiant la version déployée** : la fonction en ligne (v14) date du **07/04** ;
  le dépôt a une ligne de plus, du **21/04** (`881500b`, « validation = 1 ou true vaut acceptée »,
  comme Render). La redéployer apportera **les deux** changements.
- **Pas encore déployée** : un déploiement demande l'accord de Frédéric.

### Ce qui reste pour clore le chantier ①

1. ✅ **Répétition faite par Frédéric le 08/10** : « ESSAI ANNULE -- APRES PATCH: anon_fonctions=31
   auth_fonctions=135 photo=2546 lignes || APRES INVERSE: anon_fonctions=136 auth_fonctions=155
   anon_lit_registre=t auth_modifie_registre=t rls_search_state=f » = **exactement l'attendu**, sur
   les deux sens. Relu ensuite en base : rien n'a bougé (photo absente, 136 fonctions anon, RLS off).
2. Si le message est celui attendu : Frédéric colle **le patch**.
3. Accord pour **déployer** la fonction Edge.
4. **Contrôle du résultat** : droits relus en base ; appel avec la clé publique seule → refus ;
   l'app connectée (annonce, contact, rapprochements, registre, cockpit) sans erreur console ;
   en navigation privée : une photo de vitrine, une page d'espace client, la page de RDV ; la
   nuit suivante, run et crons sans échec ; conseiller de sécurité relu.
