## Mail HTML diffusion

### Objectif

Ameliorer les emails automatiques envoyes au negociateur apres acceptation ou refus :

- nom expediteur propre
- mise en page HTML
- photo du bien si disponible

### Ce qui a ete fait

- ajout d'un template HTML dans `apps/hektor-v1/src/App.tsx`
- envoi `text + html` dans `apps/hektor-v1/vite.config.ts`
- priorite au nom complet utilisateur pour la signature expediteur
- ajout d'une version notification compacte et orientee action
- simplification du mail autour d'un seul CTA utile
- lien profond app qui ouvre directement le popup de demande
- refonte visuelle du rendu HTML avec carte premium, meilleure hierarchie et blocs d'action

### Donnees affichees

- statut de la decision
- numero de dossier
- numero de mandat
- titre du bien
- ville
- motif ou statut principal
- commentaire si present
- action attendue
- bouton `Ouvrir dans l'application`

### Lien profond application

Le bouton application embarque maintenant une URL du type :

```text
/?screen=mandats&app_dossier_id=123&open=request&role=nego
```

Au chargement de l'app :

- l'ecran `mandats` est ouvert
- le dossier cible est selectionne
- le popup de demande est ouvert directement
- l'URL est nettoyee ensuite dans l'historique du navigateur

### Nom utilisateur

Le projet peut maintenant utiliser :

- `first_name`
- `last_name`
- sinon `display_name`
- sinon l'email

### Patch SQL a appliquer

Fichier :

- `supabase/patch_app_user_profile_names_2026-04-01.sql`

Contenu :

```sql
alter table public.app_user_profile
add column if not exists first_name text,
add column if not exists last_name text;
```

### Exemple de mise a jour utilisateur

```sql
update public.app_user_profile
set first_name = 'Frederic',
    last_name = 'Gerphagnon',
    display_name = 'Frederic Gerphagnon'
where email = 'frederic.gerphagnon@gti-immobilier.fr';
```
