# Note limite push upgrade Annonces

Date: 2026-03-27

## Objet

Documenter le comportement reel du script :

- `phase2/sync/push_upgrade_to_supabase.py`

et la limite constatee lors des premiers essais.

## Constat reel

Le script fonctionne techniquement :

- il alimente les tables `current`
- il journalise dans `app_delta_run`
- l'app peut ensuite lire les vues `current`

Mais le comportement observe n'est pas encore celui d'un vrai `upgrade rapide`.

## Pourquoi

Le script actuel fait :

1. reconstruction du payload local complet phase 2
2. lecture du stock distant `current`
3. comparaison de hashes sur l'ensemble du stock
4. ecriture seulement des lignes detectees comme differentes

Donc aujourd'hui, le mecanisme est :

- `full compare + selective write`

et non encore :

- `delta detect + selective rebuild + selective write`

## Consequence

Meme quand il n'y a presque rien de nouveau :

- le run reste long
- car il relit et recompare une grande partie du stock
- surtout sur :
  - `app_dossier_current`
  - `app_dossier_detail_current`

Le premier run apres nettoyage du `current` se comporte logiquement comme une reconstruction complete du stock courant.

Mais meme les runs suivants restent encore trop lourds si l'objectif est un vrai mode upgrade quotidien rapide.

## Ce que le script fait deja bien

- evite la creation d'un nouveau `sync_run` snapshot pour chaque mise a jour
- garde la couche `current` separee du snapshot historique
- permet de basculer l'app vers `current`
- permet un premier niveau de selective write par hash

## Ce qu'il ne fait pas encore

Il ne sait pas encore :

- detecter uniquement les dossiers impactes depuis la phase 1
- reconstruire localement seulement ces dossiers
- ne charger dans Supabase que ce sous-ensemble

## Ce qu'il faut faire pour la version 2

Le vrai mode `upgrade rapide` doit faire :

1. detecter les changements phase 1
   - annonces nouvelles
   - annonces modifiees
   - mandats modifies
   - offres modifiees
   - compromis modifies
   - ventes modifiees
   - diffusions / passerelles modifiees

2. en deduire la liste des `app_dossier_id` impactes

3. reconstruire localement uniquement :
   - les dossiers concernes
   - leurs details
   - leurs work items
   - le catalogue courant

4. pousser seulement ce sous-ensemble dans Supabase

## Conclusion

Le script actuel est une etape utile :

- il met en place la couche `current`
- il remplace le snapshot comme source exclusive de lecture

Mais il ne faut pas encore le considerer comme la version finale du vrai `upgrade rapide`.

Le prochain chantier est :

- un `push_upgrade_to_supabase.py` version 2
- pilote par un vrai delta issu de la phase 1
