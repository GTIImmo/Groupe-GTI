# Rapport Contacts Hektor - 2026-05-25

## Objectif

Mettre en place une couche contacts comparable a la couche Annonces :

- copie globale locale depuis Hektor dans le serveur ;
- exposition limitee dans Supabase pour l'app ;
- consultation ergonomique dans l'interface ;
- preparation de l'ajout/modification Hektor via le modele Console ;
- audit fort des doublons sans aucune suppression.

## Ce qui a ete ajoute

### Couche locale serveur

- `phase2/contacts/build_contacts_layer.py`
  - construit les tables derivees dans `phase2/phase2.sqlite` ;
  - conserve la source Hektor intacte dans `data/hektor.sqlite` ;
  - classe les doublons par regle et severite ;
  - produit des rapports CSV/JSON dans `exports_contacts_audit`.

- `phase2/contacts/test_contacts_layer.py`
  - verifie que les doublons sont classes ;
  - verifie que la table source Hektor n'est pas supprimee.

- `phase2/sync/sync_contact_details.py`
  - prepare l'export detail `ContactById` pour les 340k+ fiches ;
  - supporte reprise par `--missing-only`, `--changed-only`, `--start-after-id`, `--limit` ;
  - le `--dry-run` est maintenant local et ne demande plus les secrets Hektor.

### Supabase limite

- `supabase/patch_contacts_module_2026-05-25.sql`
  - tables limitees : contacts, relations annonces, groupes doublons, membres doublons ;
  - vues `security_invoker = true` ;
  - RLS activee ;
  - lecture contact limitee au portefeuille utilisateur, aux dossiers accessibles ou aux roles manager/admin ;
  - audit doublons reserve manager/admin.

- `phase2/sync/push_contacts_to_supabase.py`
  - pousse les tables limitees vers Supabase ;
  - `--dry-run` disponible et verifie localement les volumes ;
  - aucune application distante n'a ete faite sans accord.

### Interface app

- `apps/hektor-v1/src/App.tsx`
  - nouvel ecran `Contacts Hektor` ;
  - recherche nom/email/telephone/ville/ID ;
  - filtres negociateur, agence, archive, role contact ;
  - tableau desktop avec fiche laterale ;
  - badges doublons ;
  - liens vers annonces/mandats rattaches.

- `apps/hektor-v1/src/lib/api.ts`
  - chargement pagine des contacts ;
  - stats contacts ;
  - chargement des relations contact-annonce.

- `apps/hektor-v1/src/types.ts`
  - types `AppContact`, `AppContactRelation`, `ContactStats`.

- `apps/hektor-v1/src/styles.css` et `apps/hektor-v1/src/mobile.css`
  - integration visuelle desktop/mobile ;
  - icone Contacts ;
  - table dense et cartes mobiles.

## Resultat audit local

Audit complet relance le 2026-05-25 :

- contacts analyses : 354 293 ;
- actifs : 215 980 ;
- archives : 138 313 ;
- relations contacts-annonces : 123 412 ;
- contacts avec relation annonce : 91 991 ;
- relations ignorees car contact absent de `hektor_contact` : 2 ;
- groupes doublons detectes : 36 427 ;
- contacts uniques membres d'un doublon : 46 909 ;
- groupes high/critical : 24 775 ;
- groupes suspectant une erreur de transfert en archive : 13 739.

Regles de detection :

- email exact : 14 752 groupes ;
- identite complete exacte : 5 024 groupes ;
- telephone + nom : 10 335 groupes ;
- meme nom + meme lieu : 6 316 groupes.

Patterns archive :

- actif + archive : 16 917 groupes ;
- tous actifs : 12 969 groupes ;
- tous archives : 6 541 groupes.

Important : aucune suppression n'a ete faite. Les scripts classent et proposent des candidats principaux pour revue ulterieure.

## Controles executes

- build front : `npm --prefix C:\Hektor\Projet\apps\hektor-v1 run build` OK ;
- tests audit : `python -m unittest phase2.contacts.test_contacts_layer` OK ;
- audit complet local : OK, rapports regenes ;
- dry-run Supabase : 354 293 contacts, 123 412 relations, 36 427 groupes, 79 295 lignes membres ;
- dry-run export details : selection locale OK sur 5 contacts, sans appel Hektor.

## Points a valider avant ecriture Hektor

La consultation globale est integree. Pour l'ajout/modification globale de contacts, il reste a valider le contrat Console exact avec Hektor :

- payload officiel create/update contact ;
- champs obligatoires par typologie ;
- gestion des couples/personnes morales ;
- regle de rattachement negociateur/agence ;
- strategie de merge : jamais de suppression automatique, uniquement une file de revue.

Recommandation : ajouter ensuite des jobs `create_hektor_contact`, `update_hektor_contact` et `review_hektor_contact_duplicate_group` dans `app_console_job`, sur le meme modele que les annonces.
