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

Nouveau type de job :

- `sync_hektor_photos`

Le worker `documents` lit :

- `/admin/xmlrpc.php?mode=vignettes&id={id}&sortBy=byOrder`
- `/admin/xmlrpc.php?mode=vignettes_hidden&id={id}&sortBy=byOrder`

Puis met a jour `app_console_photo`.

## Front

Dans l'onglet `Contenu de l'annonce`, la rubrique Photos affiche :

- les photos API existantes si l'index Console n'est pas encore disponible ;
- les photos Console quand elles ont ete synchronisees ;
- les badges `API`, `Visible`, `Masquee` ;
- un bouton de synchronisation Console.

## Important

Cette etape ne modifie pas le pipeline API quotidien et ne copie pas les fichiers photos dans Supabase Storage.

Les futures actions photos restent a faire apres capture fiable des commandes Hektor :

- ajouter une photo ;
- modifier une legende ;
- masquer / afficher ;
- supprimer ;
- reordonner.
