# CHANTIER ② — LES DROITS DU NÉGOCIATEUR

> **Ouvert le 09/10/2026.** Audit par objet du 08/10, §2 ② et §3 (critère C8) ·
> plan : section « 🧭 LES CHANTIERS DE L'ÉTAPE 2 », ligne ② · CLAUDE.md §2.
> **Ce chantier attend une décision de Frédéric avant tout code** : *que fait un
> négociateur seul, que demande-t-il ?*

## LES POINTS DU CHANTIER — *proposition de découpage, à valider*

| # | point | état |
|---|---|---|
| **2a** | **L'état des lieux et LA DÉCISION** : qui peut quoi aujourd'hui, par quelle porte | 🔎 audit fait le 09/10 → 💬 **attend la décision** |
| 2b | **Annonce** : modifier les champs, changer le statut, archiver / désarchiver, changer de négociateur, supprimer | ⬜ |
| 2c | **Mandant** : rattacher, retirer, créer, modifier | ⬜ |
| 2d | **Transaction** : offre, compromis, vente (+ faut-il un circuit de demande ?) | ⬜ |
| 2e | **Documents et photos** : générer (avis de valeur, mandat, cadastre), supprimer, ajouter une photo, resynchroniser | ⬜ |
| 2f | **Numéro de mandat** : demander un numéro | ⬜ |
| 2g | **Les comptes** : 43 adresses de négociateur portent le parc, 2 comptes commerciaux actifs, 0 manager | ⬜ |
| 2h | **L'écran** : les boutons que le front cache à tout le monde sauf l'admin | ⬜ |

---

## 2a · L'ÉTAT DES LIEUX — *mesuré le 09/10/2026 vers 14 h, en lecture seule*

### Verdict : CONFIRMÉ, et plus simple qu'annoncé — **il n'y a que CINQ portes**

L'audit du 08/10 disait vrai sur tous les gestes refusés. Mais il ne disait pas
l'essentiel : **une seule fonction commande presque tout**.

| porte | ce qu'elle commande | qui passe |
|---|---|---|
| **1. `app_console_can_request_job`** | **16 fonctions RPC** *(annonce, mandant, photos, n° de mandat, matterport…)* **ET la règle RLS d'écriture de `app_console_job`** (`app_console_job_insert_scope`) — donc aussi les travaux que le front insère en direct, sans passer par une fonction : avis de valeur, PDF de mandat, plan cadastral, photo, suppression d'un document | admin : tout · manager : tout **sauf** statut et archiver · commercial : **7 types de documents** sur **ses** biens |
| **2. `app_console_can_request_contact_job`** | contacts et recherches acquéreur (12 fonctions) | admin, manager : tout · **commercial : OUI, sur ses contacts** *(déjà ouvert)* |
| **3. `is_app_admin()`** | **6 fonctions « affaire »** : offre, compromis, vente, note, conditions, écart de personne | **admin seul** |
| **4. contrôle écrit en dur** | créer un brouillon d'annonce *(commercial accepté, dans une agence où il porte déjà un bien)* · supprimer une annonce *(admin seul + mot de confirmation `SUPPRIMER <n°>`)* | — |
| **5. le front** | `isAdmin = profile?.role === 'admin'` — **49 endroits** dans `App.tsx` | un **manager** ne voit à l'écran rien de plus qu'un commercial |

➡ **Conséquence pour le correctif** : ouvrir les gestes au négociateur se joue d'abord
dans **UNE fonction** (porte 1), qui sert à la fois les RPC et la règle RLS. C'est la
raison pour laquelle ce chantier est beaucoup moins lourd qu'il en avait l'air — mais
**le front doit bouger en même temps**, sinon les boutons restent cachés.

### Ce qu'un négociateur (rôle `commercial`) peut faire, geste par geste

*Mesuré sur la définition réelle des fonctions (`pg_get_functiondef`) et sur
`pg_policies`, pas sur les notes.*

| geste | travail envoyé à Hektor | admin | manager | commercial |
|---|---|---|---|---|
| modifier les champs d'une annonce | `update_hektor_annonce_fields` | oui | oui | **NON** |
| changer le statut | `change_hektor_annonce_status` | oui | **NON** | **NON** |
| archiver | `archive_hektor_annonce` | oui | **NON** | **NON** |
| désarchiver | `restore_hektor_annonce` | oui | oui | **NON** |
| changer de négociateur | `assign_hektor_annonce_negotiator` | oui | oui | **NON** |
| supprimer une annonce | `delete_hektor_annonce` | oui | **NON** | **NON** |
| créer un brouillon d'annonce | `create_hektor_draft_annonce` | oui | oui | **oui** *(son agence)* |
| rattacher / retirer un mandant | `link_` / `unlink_hektor_mandant` | oui | oui | **NON** |
| créer / modifier un mandant | `create_` / `update_hektor_mandant_contact` | oui | oui | **NON** |
| offre, compromis, vente | 4 types | oui | **NON** | **NON** |
| répartition de commission | *(aucun travail Hektor)* | oui | **NON** | **NON** |
| contact : créer, modifier, supprimer | `*_hektor_contact` | oui | oui | **oui** *(ses contacts)* |
| recherche acquéreur | `*_hektor_contact_search` | oui | oui | **oui** *(ses contacts)* |
| documents : préparer, envoyer, resynchroniser, relancer ou annuler une signature | 7 types | oui | oui | **oui** *(ses biens)* |
| générer un avis de valeur, un PDF de mandat, un plan cadastral | `generate_*` | oui | oui | **NON** |
| supprimer un document chez Hektor | `delete_document_from_hektor` | oui | oui | **NON** |
| ajouter une photo · resynchroniser les photos | `upload_hektor_photo` · `sync_hektor_photos` | oui | oui | **NON** |
| demander un numéro de mandat | `create_hektor_mandat_auto_number` | oui | oui | **NON** |

**La LECTURE, elle, est déjà faite.** `app_dossier_current` et `app_contact_current`
portent une règle RLS qui limite un commercial à **ses** biens et **ses** contacts
(`can_access_negotiator_email`, `can_access_current_dossier`) ; un admin, un manager et
un rôle `lecture` voient tout. **Le trou est donc uniquement du côté de l'écriture.**

### Les mesures

```
COMPTES (app_user_profile)   4 admins actifs · 2 commerciaux actifs · 0 manager
                             0 compte « lecture » · 1 admin et 1 commercial desactives
                             (le role connait 4 valeurs : admin, manager, commercial, lecture)
LE PARC                      43 adresses de negociateur portent 21 149 lignes d'annonce ;
                             SEULES 4 ont un compte actif
LES 2 COMMERCIAUX ACTIFS     portent 125 et 916 lignes : ce sont de vrais negociateurs
USAGE REEL                   0 travail demande par un commercial, depuis toujours
                             (86 217 par les services, 3 351 par des admins)
LE CIRCUIT DE DEMANDE EXISTE app_diffusion_request, 3 types (diffusion, baisse de prix,
                             annulation de mandat) : 9 demandes EN TOUT, toutes posees par
                             un ADMIN, la derniere le 02/06/2026 -> il dort
FONCTIONS JOIGNABLES         les 11 RPC de gestes sont executables par « authenticated » et
                             fermees a « anon » : le chantier ① tient, c'est bien le controle
                             de role INTERNE qui refuse, pas un droit d'execution
NON MESURE                   la derniere connexion de chaque compte : le schema « auth »
                             refuse mes lectures (3 essais, connexion coupee)
```

### L'HISTORIQUE — *pourquoi c'est comme ça*

- **20/05/2026** — la liste du commercial naît avec **3** types de documents
  (`patch_archive_annonce_detail_request_2026-05-20.sql`), elle grandit jusqu'à **7**.
- **21/05/2026** — statut et archivage sont **réservés à l'admin**
  (`patch_console_change_annonce_status_2026-05-21.sql`, l. 48) : **aucune raison écrite**,
  ni dans le patch, ni au journal des décisions.
- **24/08/2026** *(journal des décisions)* — « **À l'étape 2, les négociateurs n'ouvrent
  plus Hektor** » : la décision de les faire travailler dans l'app est prise depuis
  six semaines ; les droits n'ont jamais suivi.
- **25/08/2026 (E.0)** — la décision suppose un **circuit de demande de validation** pour
  les transactions : **il n'en existe aucun** (seulement diffusion, baisse de prix,
  annulation de mandat).
- **30/08/2026** — `patch_c4_droits_jamais_null` garde le cas particulier mais le rend
  sûr : un rôle inconnu rendait `NULL`, et `not NULL` vaut `NULL`, donc le garde-fou ne
  se déclenchait pas. **C'était un correctif de sécurité, pas une décision métier** : il
  ne dit rien sur ce qu'un négociateur doit pouvoir faire.
- Le plan prévoit déjà un **pilote** avant l'ouverture à tous (liste des étapes, nº 10 :
  « LE PILOTE S'OUVRE : quelques négociateurs », puis nº 14 « puis tous les négociateurs »).

### CE QUI ATTEND FRÉDÉRIC — *la décision, en trois questions*

1. **Que fait un négociateur seul sur SES biens ?** *(option A, B ou C — détail dans le
   message du 09/10 : tout sauf supprimer · le quotidien et une demande pour les gestes
   graves · rien de plus qu'aujourd'hui)*
2. **Le rôle `manager`** : on le garde et on lui donne statut + archivage, ou on le laisse
   de côté (0 compte aujourd'hui) ?
3. **Les comptes** : un pilote de 2-3 négociateurs d'abord, ou les 39 comptes manquants
   tout de suite ?

*Rien n'est codé avant ces réponses.*
