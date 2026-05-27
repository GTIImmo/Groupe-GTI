# Push contacts Supabase - 2026-05-27

## Decision appliquee

- Local conserve la verite complete Hektor : listing complet, `ContactById`, historique, doublons, recherches archivees.
- Supabase recoit uniquement l'index leger utile a l'app.
- Les fiches brutes `ContactById` ne sont pas poussees dans Supabase.
- Les recherches poussees sont uniquement les recherches actives.

## Migration Supabase

Migration appliquee via connecteur Supabase :

- `supabase/patch_contacts_module_2026-05-25.sql`

Tables/vues creees :

- `app_contact_current` / `app_contacts_current`
- `app_contact_relation_current` / `app_contact_relations_current`
- `app_contact_search_current` / `app_contact_searches_current`
- `app_contact_duplicate_group_current` / `app_contact_duplicate_groups_current`
- `app_contact_duplicate_member_current`

## Premier push effectue

Commande executee :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_contacts_to_supabase.py --push-mode full --contacts-scope eligible --batch-size 500
```

Resultat :

- contacts pousses : `56 649`
- relations poussees : `76 956`
- recherches actives poussees : `3 227`
- fiches detail brutes poussees : `0`

Repartition des relations :

- `proprietaire` : `47 823`
- `acquereur_compromis` : `11 482`
- `acquereur_offre` : `9 216`
- `acquereur_vente` : `8 435`

## Controles

- Build front React : OK (`npm run build`)
- Vues Supabase REST lisibles :
  - `app_contacts_current`
  - `app_contact_relations_current`
  - `app_contact_searches_current`
- Etat local de push enregistre dans `phase2/phase2.sqlite`, table `app_contact_supabase_push_state`.

## Suite

- Le run quotidien peut utiliser `-PushContactsToSupabase` pour pousser les deltas contacts.
- Le backfill Hektor manquant pourra reprendre plus tard sans bloquer l'app.
- Une action "Actualiser Hektor" par contact pourra etre ajoutee plus tard pour recuperer `ContactById` a la demande.

## Complement relations ContactById

Ajout applique ensuite dans `phase2/contacts/build_contacts_layer.py` :

- `ContactById.data.annonces` est exploite comme source relationnelle complementaire.
- La source est ajoutee seulement quand aucune relation contact-annonce n'existe deja via les sources plus fortes.
- Role normalise : `mandant`.
- Source technique : `api_contact_detail_annonces`.
- Aucun payload brut `ContactById` n'est pousse vers Supabase.

Delta pousse vers Supabase :

- contacts mis a jour : `252`
- relations ajoutees/mises a jour : `54`
- recherches ajoutees : `0`

Etat Supabase apres delta :

- contacts : `56 700`
- relations : `77 010`
- recherches actives : `3 227`
- relations issues de `ContactById.data.annonces` : `54`

Controle apres push :

- dry-run update contacts : `0` ligne a envoyer
- build front React : OK (`npm run build`)

## Extension listing contacts actifs

Decision appliquee ensuite :

- etendre `app_contact_current` a tous les contacts actifs Hektor en version legere ;
- conserver aussi les contacts archives deja eligibles parce qu'ils portent une relation ou une recherche utile ;
- ne pas ajouter les archives sans utilite app ;
- ne pas envoyer les payloads bruts `ContactById`.

Commande executee :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_contacts_to_supabase.py --push-mode update --contacts-scope active_or_eligible --batch-size 500
```

Resultat :

- contacts actifs legers ajoutes : `176 624`
- relations ajoutees : `0`
- recherches ajoutees : `0`

Etat Supabase apres extension :

- contacts : `233 324`
- contacts actifs : `216 039`
- contacts archives conserves car utiles : `17 285`
- relations : `77 010`
- recherches actives : `3 227`

Lecture importante :

- un contact peut etre present dans le listing Supabase sans fiche `ContactById` locale ;
- dans le perimetre Supabase actuel, `70 485` contacts ont une fiche detail locale ;
- `162 839` contacts sont donc des lignes de listing leger seulement ;
- parmi les actifs, `66 330` ont une fiche detail locale et `149 709` sont listing leger seulement.

Controle apres push :

- dry-run update contacts `active_or_eligible` : `0` ligne a envoyer.

## Complement etat fiche detail

Decision appliquee ensuite :

- conserver le listing contacts leger ;
- ne toujours pas pousser les payloads bruts `ContactById` ;
- ajouter seulement deux indicateurs au contact leger :
  - `has_contact_detail` : la fiche `ContactById` est deja presente dans le miroir local ;
  - `contact_detail_synced_at` : date locale du dernier chargement detail connu.

Objectif :

- eviter de confondre `0 recherche` avec `fiche detail pas encore chargee` ;
- rendre lisible dans l'app si les recherches affichees sont exhaustives pour ce contact ;
- garder les recherches comme objet relationnel separe dans `app_contact_search_current`.

Migration Supabase appliquee :

- `supabase/patch_contacts_detail_state_2026-05-27.sql`
- rafraichissement de la vue `app_contacts_current` pour exposer les nouvelles colonnes.

Push effectue :

```powershell
.\.venv\Scripts\python.exe phase2\sync\push_contacts_to_supabase.py --push-mode update --contacts-scope active_or_eligible --batch-size 500
```

Resultat :

- contacts mis a jour : `233 324`
- relations mises a jour : `0`
- recherches mises a jour : `0`
- fiche detail brute envoyee : `0`

Etat Supabase apres controle :

- contacts dans le listing : `233 324`
- contacts actifs : `216 039`
- contacts avec detail local connu dans le perimetre Supabase : `70 485`
- contacts listing leger uniquement : `162 839`
- contacts avec recherche active : `3 074`
- contacts avec au moins une recherche connue : `13 243`
- relations : `77 010`
- recherches actives poussees : `3 227`

Controle apres push :

- dry-run update contacts `active_or_eligible` : `0` ligne a envoyer ;
- build front React : OK (`npm run build`).
