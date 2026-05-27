# Rapport explicatif - Integration Contacts Hektor

Date : 2026-05-25

## 1. Objectif

L'objectif etait d'analyser le projet, comprendre les flux Hektor existants, puis preparer une integration solide des contacts dans l'application.

Les contraintes importantes etaient :

- ne rien supprimer ;
- ne faire aucun push sans accord ;
- garder une copie globale de Hektor sur le serveur local ;
- exposer seulement une partie limitee dans Supabase ;
- permettre la consultation des contacts presents dans Hektor ;
- preparer l'ajout et la modification future des contacts ;
- traiter serieusement le soupcon de doublons massifs et d'archives creees par erreur ;
- integrer visuellement les contacts dans l'app avec une ergonomie professionnelle.

## 2. Ce que j'ai compris du projet

Le projet fonctionne deja autour de plusieurs couches :

- une source Hektor locale dans `data/hektor.sqlite` ;
- une couche metier Phase 2 dans `phase2/phase2.sqlite` ;
- une app React/Vite dans `apps/hektor-v1` ;
- Supabase pour les vues exposees a l'application ;
- une Console locale qui execute les actions Hektor via des jobs.

Pour les annonces, le projet separe deja :

- une vue lourde pour les annonces actives et les workflows metier ;
- des index legers pour les archives et historiques ;
- une logique Console pour charger ou modifier certains elements a la demande.

J'ai repris cette philosophie pour les contacts, mais en l'adaptant au volume et a la sensibilite des donnees personnelles.

## 3. Couche locale Contacts creee

J'ai ajoute un module local :

- `phase2/contacts/build_contacts_layer.py`
- `phase2/contacts/test_contacts_layer.py`

Ce module lit les contacts Hektor depuis :

- `data/hektor.sqlite`
- table source : `hektor_contact`

Puis il construit des tables derivees dans :

- `phase2/phase2.sqlite`

Tables creees :

- `app_contact_current`
- `app_contact_relation_current`
- `app_contact_duplicate_group_current`
- `app_contact_duplicate_member_current`
- `app_contact_audit_run`

Important : la table source Hektor n'est pas modifiee. Les scripts remplacent uniquement les tables derivees Phase 2.

## 4. Correction importante sur les relations contact-annonce

Au debut, j'avais utilise la table `sync_annonce_contact_link`.

Cette table etait partielle :

- seulement 2 865 relations ;
- seulement 2 603 contacts relies ;
- seulement 1 270 annonces couvertes.

Tu as signale que ce chiffre etait impossible, et tu avais raison.

J'ai donc verifie les vrais details annonce dans :

- `hektor_annonce_detail.proprietaires_json`

Constat :

- 56 326 details annonce locaux ;
- 54 005 annonces avec proprietaires ;
- 123 414 references proprietaires trouvees ;
- 91 993 IDs contacts distincts avant controle ;
- 2 references proprietaires pointaient vers des contacts absents de `hektor_contact`.

Correction faite :

- extraction des proprietaires depuis `hektor_annonce_detail.proprietaires_json` ;
- conservation de l'ancienne table `sync_annonce_contact_link` comme source secondaire ;
- dedoublonnage par contact, annonce et role ;
- rejet des relations dont le contact n'existe pas dans `hektor_contact`.

Resultat final corrige :

- 123 412 relations contact-annonce valides ;
- 91 991 contacts relies a au moins une annonce ;
- 2 relations ignorees car contact absent de la table contact.

## 5. Audit doublons

J'ai cree un audit doublons global sur les 354 293 contacts.

Regles utilisees :

- email exact ;
- identite complete exacte ;
- telephone + nom ;
- meme nom + meme lieu.

Chaque groupe est classe avec une severite :

- low ;
- medium ;
- high ;
- critical.

L'audit ne supprime rien. Il classe les groupes, donne un candidat principal et prepare une revue future.

Resultats :

- contacts analyses : 354 293 ;
- actifs : 215 980 ;
- archives : 138 313 ;
- groupes doublons : 36 427 ;
- contacts uniques presents dans au moins un doublon : 46 909 ;
- groupes high/critical : 24 775 ;
- groupes compatibles avec une erreur d'archivage massive : 13 739.

Repartition des regles :

- email exact : 14 752 groupes ;
- identite complete exacte : 5 024 groupes ;
- telephone + nom : 10 335 groupes ;
- meme nom + meme lieu : 6 316 groupes.

Patterns archive :

- actif + archive : 16 917 groupes ;
- tous actifs : 12 969 groupes ;
- tous archives : 6 541 groupes.

Conclusion : le soupcon de doublons et d'archives creees par erreur est credible. Il faut une revue metier avant toute action.

## 6. Export detail ContactById

J'ai ajoute :

- `phase2/sync/sync_contact_details.py`

Ce script prepare l'export detail des fiches contact Hektor.

Il est prevu pour gros volume :

- `--missing-only` pour ne charger que les fiches absentes ;
- `--changed-only` pour ne charger que les fiches modifiees ;
- `--start-after-id` pour reprendre apres un ID ;
- `--limit` pour travailler par lots ;
- `--sleep-seconds` pour eviter de saturer Hektor ;
- `--dry-run` pour tester sans appel Hektor.

Correction faite pendant les tests : le mode `--dry-run` ne demande plus les secrets Hektor. Il lit seulement la base locale.

Je n'ai pas lance l'export reel des 340 000 fiches detail. Il faut le faire par lots, avec surveillance.

## 7. Structure Supabase preparee

J'ai ajoute :

- `supabase/patch_contacts_module_2026-05-25.sql`
- `phase2/sync/push_contacts_to_supabase.py`

Tables Supabase prevues :

- `public.app_contact_current`
- `public.app_contact_relation_current`
- `public.app_contact_duplicate_group_current`
- `public.app_contact_duplicate_member_current`

Vues prevues :

- `public.app_contacts_current`
- `public.app_contact_relations_current`
- `public.app_contact_duplicate_groups_current`

Principes de securite :

- RLS activee ;
- vues avec `security_invoker = true` ;
- pas de `raw_json` Hektor expose ;
- les contacts sont visibles selon le role ou le portefeuille ;
- les doublons sont reserves aux managers/admins ;
- le service role est utilise uniquement cote serveur/script, pas cote front.

Je n'ai pas applique le SQL sur Supabase distant. Je n'ai fait qu'un dry-run.

Dry-run Supabase :

- 354 293 contacts ;
- 123 412 relations ;
- 36 427 groupes doublons ;
- 79 295 lignes membres de groupes doublons.

## 8. Integration visuelle dans l'application

J'ai ajoute un ecran Contacts dans l'app React :

- navigation desktop ;
- navigation mobile ;
- recherche rapide ;
- filtres ;
- table desktop ;
- panneau detail contact ;
- badges doublons ;
- liens vers annonces/mandats rattaches ;
- cartes mobiles.

Fichiers principaux modifies :

- `apps/hektor-v1/src/App.tsx`
- `apps/hektor-v1/src/lib/api.ts`
- `apps/hektor-v1/src/types.ts`
- `apps/hektor-v1/src/layouts/MobileLayout.tsx`
- `apps/hektor-v1/src/styles.css`
- `apps/hektor-v1/src/mobile.css`

Fonctions ajoutees cote API front :

- `loadContactsPage`
- `loadContactStats`
- `loadContactRelations`

Types ajoutes :

- `AppContact`
- `AppContactRelation`
- `ContactStats`

## 9. Difference avec les annonces

Pour les annonces, le projet a deux niveaux :

- index lourd : `app_dossiers_current`, `app_mandats_current`, `app_view_generale` ;
- index leger : `app_archive_annonce_index_current`, `app_historical_annonce_index_current`.

L'index lourd sert aux annonces actives et aux actions metier completes.

L'index leger sert aux archives, vendus, clos et recherches larges. Il contient moins de colonnes et neutralise certains filtres lourds comme les offres, compromis, demandes, passerelles ou erreurs diffusion.

Pour les contacts, j'ai mis en place :

- un miroir complet local sur le serveur ;
- un index limite dans Supabase ;
- pas encore de detail complet Supabase ;
- pas encore de cache detail a la demande.

La raison est simple : un contact est moins riche qu'une annonce, mais beaucoup plus sensible et beaucoup plus volumineux. Le bon choix initial est donc de garder le detail complet localement et d'exposer seulement l'essentiel a l'app.

## 10. Tests et controles faits

Controles executes :

- build front : OK ;
- tests unitaires contacts : OK ;
- audit complet local : OK ;
- dry-run Supabase : OK ;
- dry-run export detail contacts : OK ;
- verification visuelle locale de l'ecran Contacts : OK ;
- aucune suppression ;
- aucun push ;
- aucune application Supabase distante.

Commandes verifiees :

- `npm --prefix C:\Hektor\Projet\apps\hektor-v1 run build`
- `python -m unittest phase2.contacts.test_contacts_layer`
- `python phase2/sync/push_contacts_to_supabase.py --dry-run --include-duplicates`
- `python phase2/sync/sync_contact_details.py --dry-run --missing-only --limit 5`

## 11. Ce qui reste a faire

### 11.1 Valider et appliquer Supabase

Le SQL Supabase est pret, mais il faut ton accord pour l'appliquer.

Etapes :

- relire le SQL ;
- appliquer sur Supabase ;
- verifier les policies RLS ;
- pousser les donnees limitees ;
- tester avec les vrais profils.

### 11.2 Exporter les fiches detail contact

Il reste a lancer `ContactById` pour les 340 000+ contacts.

Recommandation :

- lancer par lots ;
- surveiller les erreurs ;
- conserver la reprise `--missing-only` ;
- ne pas saturer Hektor ;
- stocker les payloads complets uniquement localement.

### 11.3 Completer les relations hors proprietaires

Aujourd'hui, les relations fiables viennent des proprietaires d'annonces.

Il reste a enrichir avec :

- acquereurs ;
- notaires ;
- offres ;
- compromis ;
- ventes ;
- autres roles presents dans les details Hektor.

### 11.4 Construire la revue doublons

Il faut une interface ou une file de travail pour traiter les doublons :

- doublon confirme ;
- faux positif ;
- contact principal retenu ;
- a fusionner plus tard ;
- erreur archive prestataire suspectee.

Aucune suppression automatique ne doit etre faite.

### 11.5 Ajouter creation/modification Hektor

La consultation est preparee. Pour l'ecriture Hektor, il faut encore valider :

- endpoint exact de creation contact ;
- endpoint exact de modification contact ;
- champs obligatoires ;
- gestion couples ;
- gestion personnes morales ;
- rattachement negociateur/agence ;
- comportement archive/desarchive ;
- retour Hektor attendu.

Ensuite, il faudra ajouter des jobs Console :

- `create_hektor_contact`
- `update_hektor_contact`
- `review_hektor_contact_duplicate_group`

## 12. Conclusion

La base Contacts est maintenant construite correctement.

Le point critique corrige est la relation contact-annonce : le premier chiffre etait sous-estime car base sur une table partielle. Le bon chiffre est maintenant de 123 412 relations valides et 91 991 contacts relies.

Le risque doublons est confirme et significatif. Il doit etre traite par classement et revue, pas par suppression automatique.

La suite logique est :

1. valider le patch Supabase ;
2. pousser la donnees limitee ;
3. exporter les details ContactById par lots ;
4. construire la file de revue doublons ;
5. ajouter l'ecriture Hektor via Console.
