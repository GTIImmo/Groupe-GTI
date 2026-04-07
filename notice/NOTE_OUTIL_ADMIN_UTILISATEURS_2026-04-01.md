## Outil admin utilisateurs

### Objectif

Ajouter un petit outil dans l'app pour creer un utilisateur sans passer manuellement par plusieurs ecrans.

### Ce que fait l'outil

Depuis l'app, un administrateur peut maintenant :

- saisir prenom
- saisir nom
- saisir email
- definir un mot de passe temporaire
- choisir un role
- definir si le compte est actif
- lister les utilisateurs existants
- modifier role / nom / email
- archiver ou reactiver un utilisateur via `is_active`
- envoyer un lien de reinitialisation de mot de passe

### Ce que fait techniquement le backend local

Le serveur Vite local :

1. cree le compte dans `auth.users`
2. confirme l'email localement
3. alimente `public.app_user_profile`

### Variables requises

Il faut configurer :

- `SUPABASE_SERVICE_ROLE_KEY`
- `APP_BASE_URL`

Cette cle ne doit pas etre exposee dans le front.
Elle est lue seulement cote serveur local dans `vite.config.ts`.

### Point d'entree

Dans l'app :

- bouton `Utilisateurs` visible pour les admins

### Limite actuelle

L'outil est pour l'instant un outil de creation + gestion simple.

Il ne gere pas encore :

- suppression / archivage
- suppression physique
- invitation email
