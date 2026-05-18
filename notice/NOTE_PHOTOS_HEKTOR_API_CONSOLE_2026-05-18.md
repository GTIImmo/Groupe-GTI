# Photos Hektor - API + Console

## Decision

Le projet conserve le flux photos API existant.

Les photos visibles issues de l'API Hektor restent stockees sous forme d'URLs dans les donnees annonce :

- `images_json`
- `images_preview_json`
- `photo_url_listing`
- `nb_images`

Les fichiers images restent heberges chez Hektor / staticlbi. Supabase ne stocke pas les fichiers photos API dans Storage.

## Ajout Bloc 2

Une couche Console separee a ete ajoutee pour indexer les photos gerees dans la console Hektor.

Nouvelle table :

- `public.app_console_photo`

Elle stocke uniquement l'index :

- annonce / dossier
- identifiant photo Hektor
- URL vignette
- URL HD
- visible / masquee
- legende
- ordre
- donnees source Console

## Job ajoute

Types de jobs :

- `sync_hektor_photos`
- `upload_hektor_photo`

Le worker `documents` lit :

- `/admin/xmlrpc.php?mode=vignettes&id={id}&sortBy=byOrder`
- `/admin/xmlrpc.php?mode=vignettes_hidden&id={id}&sortBy=byOrder`

Puis met a jour `app_console_photo`.

Pour l'ajout d'une photo :

1. l'app cree un job `upload_hektor_photo` ;
2. l'app depose la photo en temporaire prive dans Supabase Storage :
   `temp/photos/{job_id}/{filename}` ;
3. le worker `documents` telecharge le fichier temporaire ;
4. le worker se place dans le bon contexte Hektor negociateur ;
5. le worker ouvre la page Console Photos Hektor avec Playwright et envoie le fichier via l'input Hektor natif ;
6. le worker relit `vignettes` / `vignettes_hidden` et met a jour `app_console_photo` ;
7. le fichier temporaire Supabase est supprime.

## Front

Dans l'onglet `Contenu de l'annonce`, la rubrique Photos affiche :

- les photos API existantes si l'index Console n'est pas encore disponible ;
- les photos Console quand elles ont ete synchronisees ;
- les badges `API`, `Visible`, `Masquee` ;
- un formulaire `Ajouter une photo` visible / masquee ;
- un bouton secondaire de synchronisation Console.

## Important

Cette etape ne modifie pas le pipeline API quotidien et ne copie pas les fichiers photos dans Supabase Storage.

La commande directe HTTP d'upload photo Hektor n'est pas encore consideree comme stabilisee. L'upload photo utilise donc Playwright cote PC serveur pour reproduire l'action officielle de la page Hektor Photos.

Les futures actions photos restent a faire apres capture fiable des commandes Hektor :

- modifier une legende ;
- masquer / afficher ;
- supprimer ;
- reordonner.
