# Audit `L5` — les photos : système, poids, choix déjà faits, ce qui manque

*25/09/2026. Lecture seule : les notes (dont celles supprimées du git), la mémoire, le worker,
le front, Supabase. Rien n'a été modifié.*

**Audit limité aux PHOTOS d'annonce.** Les documents (`D.0`, `D.1`) ne sont pas mesurés ici,
sauf là où ils partagent le même stockage.

## 1. Le choix d'origine, et il tient toujours

➡ `notice/NOTE_PHOTOS_HEKTOR_API_CONSOLE_2026-05-18.md`

> **Le projet conserve le flux photos API existant.** Les photos restent hébergées chez
> Hektor / staticlbi, sous forme d'URLs dans `images_json`, `images_preview_json`,
> `photo_url_listing`, `nb_images`. **Supabase ne stocke pas les fichiers photos.**

Une **seconde couche** a été ajoutée ensuite, la couche Console : la table
`app_console_photo`, qui **indexe** les photos de la console Hektor sans les héberger.
Deux travaux la servent : `sync_hektor_photos` *(lecture)* et `upload_hektor_photo` *(ajout)*.

⚠ **L'ajout passe par Playwright, pas par HTTP** — décision explicite de la note :
*« la commande directe HTTP d'upload photo Hektor n'est pas encore considérée comme
stabilisée »*. Le worker ouvre la page Console de Hektor et se sert de son champ de fichier.

## 2. Ce que le système sait faire aujourd'hui — le tableau des gestes

| | créer | modifier | supprimer / masquer | lire |
|---|---|---|---|---|
| **photo (couche API)** | — *(Hektor seul)* | — | — | ✅ URLs dans l'annonce |
| **photo (couche Console)** | ✅ `upload_hektor_photo` *(Playwright)* | ⛔ **rien** | ⛔ **rien** | ✅ `sync_hektor_photos` |

**Deux modes Hektor seulement sont connus du worker** : `vignettes` et `vignettes_hidden`,
tous deux en **lecture**. **Aucun mode de suppression, de réordonnancement ou de choix de la
photo principale n'a jamais été relevé.** *(Par comparaison, le worker connaît bien
`UploadedDocument_delete` pour les documents et `supprimeannonce` pour les annonces.)*

**Côté front, même constat** : l'écran ne propose que l'ajout et la synchronisation. La seule
occurrence de « photo principale » est un **compteur d'accueil** *(« Annonces sans photo
principale »)*, pas un geste.

➡ **Le manque annoncé par `E.0-bis` est confirmé et complet** : supprimer, réordonner et
choisir la principale n'existent ni côté worker, ni côté front, **et les commandes Hektor
correspondantes ne sont pas connues**. C'est le vrai travail : **les trouver d'abord.**

## 3. Le poids — mesuré ce jour

| | |
|---|---|
| photos indexées (`app_console_photo`) | **1 397** — c'est exactement le « 1 397 » de `D.2` |
| annonces concernées | **229** seulement, sur 13 437 : **l'index Console est très partiel** |
| **poids total** | **524 Mo** |
| poids moyen / la plus lourde | **396 ko** / **4,8 Mo** |
| photos visibles | 1 252 |
| **dans Supabase Storage** | ⛔ **0** — `storage_path` est vide sur **toutes** |
| état | 1 355 `local_only` · 42 `pending` *(6 annonces, jamais traitées)* |

Le seul bucket, `hektor-console-documents`, contient **22 925 fichiers** — **des documents,
pas des photos**. Le choix de mai *(« Supabase ne stocke pas les fichiers photos »)* n'a
jamais été enfreint.

⚠ **Mais la table est déjà équipée pour le rapatriement** : elle porte `storage_bucket`,
`storage_path`, `storage_status`, `file_size`, `sha256`. **Le schéma de `D.2` est posé, le
transfert n'a jamais été lancé.**

## 4. Ce que ça veut dire pour `L5`

**Le geste « photos » de `L5` n'est pas un travail d'interface, c'est d'abord une
reconnaissance.** Avant d'écrire quoi que ce soit, il faut **relever les commandes de la page
Photos de Hektor** — supprimer, réordonner, définir la principale — comme cela a été fait pour
les autres écrans *(`Console/releve_assistant_etapes.js` est le patron : il n'écrit jamais)*.

**Trois étapes, dans cet ordre :**

1. **Relever** les commandes de la page Photos, en lecture seule, sur une annonce d'essai.
   *(~0,5 j — ⚠ touche Hektor en lecture : cadence 0,5 s, et **un 403 = arrêt**.)*
2. **Coder** les trois gestes sur le patron de `upload_hektor_photo` *(Playwright, travail,
   index relu ensuite)*. *(~1,5-2 j)*
3. **Éprouver** sur une annonce d'essai, **avec ton accord** : ce sont des écritures chez
   Hektor, et **supprimer une photo est irréversible**.

⚠ **Deux points à trancher, qui ne sont pas techniques :**
- **sur quelle annonce faire l'essai ?** Supprimer une photo est définitif chez Hektor.
- **faut-il en profiter pour lancer `D.2`** *(rapatrier les 524 Mo)* ? Le schéma est prêt, et
  tant que les fichiers vivent chez Hektor, **une photo disparaît de l'app le jour de la
  coupure**. Ce n'est pas dans `L5` mais dans `L7` — à ne pas mélanger, seulement à savoir.

## 5. Ce qui n'a pas été mesuré

- **Pourquoi 229 annonces seulement** sont dans l'index Console, sur 13 437.
- **Les 42 photos `pending`** de 6 annonces, jamais traitées — depuis quand, et pourquoi.
- Le comportement de l'upload quand Hektor renvoie une erreur de taille ou de format.
