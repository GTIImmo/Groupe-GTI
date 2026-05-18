# Note projet - Generation automatique du numero de mandat Hektor

Date : 2026-05-18

## Objectif

Ajouter dans l'app une action controlee permettant de generer le numero de mandat depuis Hektor, sans passer manuellement par la console.

Cette action est volontairement separee de la creation d'annonce et de l'ajout de mandant, car Hektor consomme un vrai numero au moment de la validation.

## Flux installe

App en ligne -> Supabase job `create_hektor_mandat_auto_number` -> worker actions PC local -> Hektor Console -> job `refresh_console_data` -> app mise a jour.

L'action est disponible dans la fiche annonce, onglet `Mandat et contacts`, et dans la fenetre de modification Hektor.

## Preconditions

- L'annonce doit exister dans Hektor.
- Un mandant doit deja etre rattache a l'annonce.
- Le worker doit se placer dans le contexte Hektor du negociateur de l'annonce ou du commercial demandeur.
- Si aucun mandant n'est detecte, le job passe en erreur sans consommer de numero.

## Commandes Hektor identifiees

Chargement de l'onglet mandat/prix :

```text
GET /admin/xmlrpc.php?mode=chargeannonce_MandatPrix&id={hektor_annonce_id}&lang=fr
```

Ouverture du wizard mandat :

```text
GET /admin/xmlrpc.php?mode=protexa-mandat&mandat=0&idann={hektor_annonce_id}
POST /admin/xmlrpc.php?mode=protexa-listeTypeMandat
```

Generation automatique du numero :

```text
GET /admin/xmlrpc.php?mode=protexa-valideStep1&id={hektor_annonce_id}&numMandat=0
```

La reponse contient le numero dans `mandat.numero`.

Validation du mandat :

```text
GET /admin/xmlrpc.php?mode=protexa-valideStep2&id={hektor_annonce_id}&numMandat={numero}&typeMandat={type}&subType={subtype}
GET /admin/xmlrpc.php?mode=protexa-valideStep3&id={hektor_annonce_id}&numMandat={numero}&date_debut={jj-mm-aaaa}&duree={mois}&TR={0|1}
GET /admin/xmlrpc.php?mode=protexa-valideStep4&id={hektor_annonce_id}&numMandat={numero}&idMandants={contactId|}
GET /admin/xmlrpc.php?mode=protexa-valideStep5&id={hektor_annonce_id}&numMandat={numero}
```

## Fichiers modifies

- `Console/console_job_worker.js` : handler worker Hektor.
- `supabase/patch_console_create_mandat_auto_number_2026-05-18.sql` : RPC et routage worker.
- `apps/hektor-v1/src/lib/api.ts` : appel RPC depuis l'app.
- `apps/hektor-v1/src/types.ts` : type de job.
- `apps/hektor-v1/src/App.tsx` : formulaire/bouton dans Mandat et contacts.
- `apps/hektor-v1/src/styles.css` : rendu desktop/mobile.

## Securite fonctionnelle

Le bouton ne genere pas un numero localement. Il cree seulement un job Supabase.

Le numero est cree uniquement par Hektor, cote PC serveur, avec la session console et le contexte negociateur. Le front ne contient aucun cookie Hektor ni secret.
