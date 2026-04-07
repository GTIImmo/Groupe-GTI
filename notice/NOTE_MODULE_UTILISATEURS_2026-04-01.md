## Module utilisateurs

### Perimetre couvert

Le socle utilisateurs de l'app `hektor-v1` est maintenant en place.

Il couvre :

- creation de compte
- edition de profil
- activation / archivage
- gestion des roles
- reset mot de passe
- mot de passe oublie
- affichage du nom utilisateur dans les mails
- cloisonnement du role `commercial`
- verrouillage RLS cote Supabase pour le portefeuille commercial

---

## 1. Gestion des comptes

### Creation utilisateur

Un outil admin est disponible dans l'app via le bouton :

- `Utilisateurs`

Visible pour :

- `admin`

Depuis cet outil, un admin peut :

- creer un utilisateur
- saisir `first_name`
- saisir `last_name`
- saisir `display_name`
- saisir `email`
- definir un mot de passe temporaire
- choisir un role
- definir `is_active`

### Backend local

La creation passe par le serveur local Vite.

Flux :

1. creation du compte dans `auth.users`
2. confirmation email cote serveur
3. insertion / mise a jour dans `public.app_user_profile`

### Variables serveur requises

- `SUPABASE_SERVICE_ROLE_KEY`
- `APP_BASE_URL`

La cle serveur reste cote backend local.

Elle ne doit pas etre exposee via `VITE_...`.

---

## 2. Profil public utilisateur

### Table cible

- `public.app_user_profile`

### Colonnes utilisees

- `id`
- `email`
- `role`
- `is_active`
- `display_name`
- `first_name`
- `last_name`

### Patch applique / a garder

Fichier :

- `supabase/patch_app_user_profile_names_2026-04-01.sql`

Ajout :

```sql
alter table public.app_user_profile
add column if not exists first_name text,
add column if not exists last_name text;
```

---

## 3. Roles actuellement utilises

### Roles disponibles

- `admin`
- `manager`
- `commercial`
- `lecture`

### Intention actuelle

- `admin`
  - vue globale
  - acces `Suivi`
  - acces `Utilisateurs`
  - gestion des demandes
  - gestion diffusion

- `manager`
  - vue globale
  - pas encore specialise plus finement

- `commercial`
  - portefeuille limite a ses annonces
  - usage negociateur

- `lecture`
  - vue globale pour l'instant
  - pas de specialisation supplementaire faite a ce stade

### Libelles UI actuels

- `admin` -> `Administrateur`
- `manager` -> `Manager`
- `commercial` -> `Negociateur`
- `lecture` -> `Lecture`

---

## 4. Activation / archivage

Le module gere :

- activation via `is_active = true`
- archivage via `is_active = false`

Point important constate pendant les tests :

- un utilisateur `commercial` en `is_active = false` ne voit aucune donnee
- ce comportement est normal avec les policies RLS existantes

Donc :

- si un nouveau compte ne voit rien, verifier d'abord `is_active`

Exemple SQL :

```sql
update public.app_user_profile
set is_active = true
where email = 'utilisateur@example.com';
```

---

## 5. Mot de passe oublie / reset

### Depuis l'admin

Dans `Utilisateurs`, un admin peut envoyer :

- `Mot de passe perdu`

Ce bouton appelle un endpoint serveur local qui utilise :

- `supabase.auth.admin`
- puis `resetPasswordForEmail(...)`

### Depuis l'ecran de connexion

L'ecran de login contient maintenant :

- `Mot de passe oublie ?`

L'utilisateur saisit son email.

L'app envoie ensuite le lien de reinitialisation.

### Flux de retour

Quand l'utilisateur clique sur le lien Supabase :

- l'app detecte le mode `recovery`
- elle affiche un ecran dedie
- l'utilisateur peut definir un nouveau mot de passe
- le mot de passe est mis a jour
- la session est nettoyee proprement

### Point de configuration important

Il faut aligner :

- `APP_BASE_URL`
- `Authentication > URL Configuration` dans Supabase

Exemple local :

- `http://localhost:5173`

---

## 6. SMTP et notifications email

### Ce qui est en place

Apres acceptation ou refus d'une demande de diffusion :

- la decision est enregistree
- un email SMTP est envoye au negociateur

### Infrastructure

Le projet utilise :

- `nodemailer`
- endpoint local Vite
- SMTP Google configure

### Variables SMTP utilisees

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_SECURE`
- `SMTP_FROM`
- `SMTP_ALLOW_USER_FROM`

### Mode expediteur retenu

Mode recommande :

- expediteur technique stable
- `reply-to` = utilisateur connecte

### Rendu mail

Le mail contient :

- statut decision
- dossier
- mandat
- titre du bien
- ville
- message principal
- photo du bien si disponible

### Nom expediteur

Ordre de priorite :

1. `first_name + last_name`
2. `display_name`
3. `email`

---

## 7. Cloisonnement negociateur dans l'app

### Regle appliquee

Un utilisateur avec :

- `role = commercial`

est maintenant automatiquement scope par :

- `session.user.email`
- compare a `negociateur_email`

### Ce qui est scope

- dossiers
- mandats
- work items
- stats
- catalogues de filtres

### Effet attendu

- si l'email existe dans les donnees Hektor, le commercial ne voit que son portefeuille
- si l'email n'est rattache a aucune annonce, la vue est vide

---

## 8. Verrouillage RLS Supabase

### Objectif

Ne pas dependre uniquement du filtrage front.

Le cloisonnement doit etre impose aussi cote base.

### Patch prepare et applique

Fichier :

- `supabase/patch_rls_commercial_scope_2026-04-01.sql`

Ce patch :

- laisse `admin`, `manager`, `lecture` en vue globale
- limite `commercial` aux lignes ou `negociateur_email = son email`

### Objets cibles

Quand ils existent :

- `app_dossier_current`
- `app_dossier_detail_current`
- `app_work_item_current`
- `app_mandat_current`
- `app_mandat_broadcast_current`
- `app_diffusion_request`
- ainsi que les tables `v1` equivalentes

### Particularite

Le patch a ete rendu tolerant :

- il ne plante pas si certaines tables n'existent pas encore sur l'instance

---

## 9. UI session utilisateur

### Carte session

Le header utilisateur a ete ajuste.

Pour le compte admin :

- bouton `Utilisateurs`
- bouton `Se deconnecter`

sont maintenant correctement regroupes dans un bloc d'actions.

---

## 10. Fichiers principaux modifies

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/lib/supabase.ts`
- `apps/hektor-v1/src/types.ts`
- `apps/hektor-v1/src/styles.css`
- `apps/hektor-v1/vite.config.ts`
- `apps/hektor-v1/.env.smtp.example`
- `supabase/patch_app_user_profile_names_2026-04-01.sql`
- `supabase/patch_rls_commercial_scope_2026-04-01.sql`

---

## 11. Etat actuel

Le module utilisateurs est considere comme fonctionnel pour le socle.

### Fait

- creation
- edition
- activation / archivage
- reset mot de passe
- mot de passe oublie
- mails SMTP de decision
- personnalisation nom utilisateur
- cloisonnement commercial
- RLS commercial

### Reste eventuel plus tard

- specialiser `manager`
- durcir davantage `lecture`
- invitation email utilisateur
- tableau de bord utilisateurs plus riche

---

## 12. Priorites suivantes

La suite logique n'est plus le socle utilisateurs.

Les prochains chantiers sont :

1. optimisation du design et du ton des mails
2. ajout de liens vers l'app et Hektor
3. mise en place des relances
4. eventualisation d'un workflow de relance automatique ou semi-assistee
