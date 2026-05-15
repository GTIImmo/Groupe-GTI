# Correctif mandant Hektor - 2026-05-15

## Objectif

Remplacer l'ancien fonctionnement "associer un mandant par ID contact Hektor" par un vrai formulaire dans l'app.

Avant, l'utilisateur devait connaitre un ID contact Hektor, ce qui n'est pas exploitable dans l'app. Maintenant, l'utilisateur saisit directement les informations du nouveau mandant. Le PC serveur cree le contact dans Hektor et l'associe automatiquement comme mandant/proprietaire de l'annonce.

## Fonctionnement installe

1. Dans l'app, l'utilisateur ouvre une fiche annonce.
2. Dans la rubrique mandat/contacts, il remplit le formulaire "Creer un mandant Hektor".
3. L'app cree une job Supabase de type `create_hektor_mandant_contact`.
4. Le worker local prend la job, se place dans le bon contexte Hektor negociateur, puis appelle la console Hektor.
5. Le worker charge le formulaire Hektor natif de creation contact mandant.
6. Le worker envoie le contact avec `saveOrUpdate=mandantOnAnnonce`.
7. Hektor cree le contact et l'attache a l'annonce.
8. Le worker verifie que le contact apparait bien dans la liste des mandants.
9. Le worker relance une synchronisation immediate de l'annonce pour que l'app se mette a jour sans attendre la synchro quotidienne.

## Endpoint Hektor utilise

Chargement du formulaire natif :

```text
POST /admin/xmlrpc.php
mode=contacts-actions-addManuelContactFromOtherObject
statut=contact_seule
qualification=3
```

Creation + association du mandant :

```text
POST /admin/xmlrpc.php
mode=contacts-actions-insertManuelContactFromOtherObject
saveOrUpdate=mandantOnAnnonce
saveOrUpdateValue={hektor_annonce_id}
statut=1
qualification=3
```

Verification :

```text
GET /admin/xmlrpc.php?mode=div_display_prospects_liste&json=1&id={hektor_annonce_id}
```

Fallback si l'association automatique n'est pas confirmee :

```text
GET /admin/xmlrpc.php?mode=selectnouveauproprio_sup&id={hektor_contact_id}&idann={hektor_annonce_id}
```

## Supabase

Migration ajoutee :

```text
supabase/patch_console_create_mandant_contact_2026-05-15.sql
```

Elle ajoute :

- le type de job `create_hektor_mandant_contact`
- la RPC `app_console_create_mandant_contact_job(...)`
- les droits metier dans `app_console_can_request_job(...)`

Regles :

- admin : autorise
- manager : autorise
- commercial : autorise uniquement sur son perimetre accessible

## Fichiers modifies

- `Console/console_job_worker.js`
- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/types.ts`
- `apps/hektor-v1/src/styles.css`
- `supabase/patch_console_create_mandant_contact_2026-05-15.sql`

## Important

Ce correctif ne supprime pas l'ancien handler worker `link_hektor_mandant`. Il reste disponible pour compatibilite technique, mais l'interface utilisateur ne demande plus d'ID contact Hektor.

Le worker garde la logique de session Hektor existante : si la session expire, il relance le login Playwright puis retente la commande une fois.

## Correctif apres test second mandant

Test reel effectue sur l'annonce Hektor `62243` :

- premier mandant test cree et associe : contact Hektor `603484`
- deuxieme mandant test cree et associe : contact Hektor `603485`

Le test a confirme que Hektor accepte plusieurs mandants sur la meme annonce.

Un garde-fou a aussi ete ajoute au worker : chaque script Python de synchro immediate a maintenant un timeout. Si la derniere etape de push Supabase se fige, le worker ne reste plus bloque indefiniment et peut continuer a traiter les prochaines jobs.
