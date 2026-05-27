# Proposition contacts Hektor local-first - 2026-05-25

## Objectif

Reprendre l'architecture contacts pour respecter deux contraintes :

- conserver une copie complete Hektor en local, avec mise a jour et historique
  d'audit ;
- ne pas surcharger Supabase avec les 354 293 contacts, les 340 000+ details
  `ContactById`, les JSON bruts et les donnees de doublons massives.

Aucune suppression n'a ete faite. Aucun push Supabase n'a ete fait.

## Constat chiffre

### Stock local actuel

| Element | Volume |
| --- | ---: |
| Base brute `data/hektor.sqlite` | 2 474,90 Mo |
| Base app `phase2/phase2.sqlite` | 1 545,73 Mo |
| Contacts `hektor_contact` | 354 293 |
| Annonces `hektor_annonce` | 56 347 |
| Details annonces `hektor_annonce_detail` | 56 326 |
| Offres | 10 882 |
| Compromis | 10 359 |
| Ventes | 2 967 |
| Reponses API brutes | 101 631 |

Le local est donc deja le bon endroit pour le miroir complet.

### Typologies contacts

| Typologie | Total | Actifs | Archives |
| --- | ---: | ---: | ---: |
| Acquereur | 169 175 | 116 640 | 52 535 |
| Mandant | 103 245 | 74 644 | 28 601 |
| Partenaire | 104 962 | 42 668 | 62 294 |
| Locataire | 2 | 2 | 0 |

Combinaisons principales :

- acquereur seul : 156 983 ;
- partenaire seul : 93 804 ;
- mandant seul : 81 613 ;
- acquereur + mandant : 10 724 ;
- mandant + partenaire : 9 692 ;
- acquereur + mandant + partenaire : 1 216.

### Relations annonce-contact

Relations proprietaires/mandants issues des details annonce :

- 123 414 couples contact-annonce trouves dans `proprietaires_json` ;
- 123 412 deja presents dans `app_contact_relation_current` ;
- 2 manquants seulement, car les deux contacts Hektor references par annonce
  ne sont pas presents dans `hektor_contact`.

Relations acquereurs transactionnels a ajouter :

| Source | Couples contact-annonce uniques |
| --- | ---: |
| Offre acquereur | 10 796 |
| Compromis acquereur | 12 582 |
| Vente acquereur | 3 574 |
| Union totale | 14 766 |

Ces 14 766 couples concernent 14 298 contacts distincts. Ils ne sont quasiment
pas encore dans la table relation actuelle.

### Echantillon reel `ContactById`

J'ai recupere un echantillon controle local de 129 fiches detail contact :

| Forme `data` observee | Nombre |
| --- | ---: |
| `contact` seul | 23 |
| `contact + recherches` | 22 |
| `contact + annonces` | 44 |
| `contact + recherches + annonces` | 40 |

Interpretation :

- `contact` est la fiche annuaire globale ;
- `recherches` correspond aux recherches acquereurs ;
- `annonces` correspond aux annonces rattachees au contact cote mandant ;
- la fiche detail n'est pas une fiche acquereur, elle est une fiche globale.

Deux contacts de l'echantillon ont retourne une erreur 404 sur `ContactById`.
Ils doivent etre marques en anomalie locale, pas supprimes.

## Probleme avec une copie Supabase complete

Le schema prepare precedemment pousse potentiellement :

- 354 293 lignes `app_contact_current` ;
- 123 412 relations proprietaires actuelles ;
- 14 766 relations transactionnelles a ajouter ;
- 36 427 groupes doublons ;
- 79 295 membres de doublons ;
- puis, si on ajoutait les recherches/details, des centaines de milliers de
  lignes supplementaires.

Ce n'est pas le bon usage de Supabase pour ce module. Supabase doit rester une
cache operationnelle pour l'app, pas un entrepot complet Hektor.

## Version adaptee proposee

### 1. Local = source de verite complete

Tout Hektor doit rester local :

- listing complet contacts actifs + archives ;
- details `ContactById` complets, par lots ;
- JSON bruts ;
- recherches acquereurs ;
- annonces rattachees depuis les fiches contact ;
- relations proprietaires, acquereurs offre, acquereurs compromis, acquereurs
  vente ;
- audit doublons complet ;
- anomalies 404, IDs presents dans annonce mais absents du listing, incoherences
  archive/actif.

Tables locales a ajouter ou consolider :

| Table locale | Role |
| --- | --- |
| `local_contact_detail_current` | Dernier `ContactById` complet par contact, JSON brut local uniquement |
| `local_contact_search_current` | Recherches acquereurs normalisees depuis `data.recherches` |
| `local_contact_annonce_current` | Annonces rattachees depuis `data.annonces` |
| `local_contact_relation_current` | Union proprietaire + acquereur_offre + acquereur_compromis + acquereur_vente + contact_detail_annonce |
| `local_contact_duplicate_*` | Audit doublons complet, sans suppression |
| `local_contact_sync_state` | Etat de synchronisation par contact |
| `local_contact_anomaly` | 404, ID absent du listing, payload invalide, conflit archive |

La table `app_contact_current` locale peut rester l'annuaire normalise complet,
mais elle ne doit plus signifier "tout doit etre pousse dans Supabase".

### 2. Moteur de mise a jour local

Le flux recommande :

1. `ListContacts` actifs + archives pour detecter les nouveaux/changes via
   `datemaj`.
2. Creation d'une file locale `contact_detail_queue`.
3. Priorite de refresh :
   - contacts modifies depuis le dernier run ;
   - contacts lies a une annonce ;
   - acquereurs actifs ;
   - contacts membres de doublons high/critical ;
   - le reste en backfill lent.
4. `ContactById` par lots controles :
   - reprise possible ;
   - throttle ;
   - erreurs 404 stockees dans `local_contact_anomaly` ;
   - aucune suppression automatique.
5. Reconstruction locale :
   - annuaire ;
   - recherches acquereurs ;
   - relations ;
   - doublons ;
   - statistiques.

Le backfill des 340 000+ fiches doit etre un travail de fond, pas une condition
pour utiliser l'app.

### 3. Supabase = index leger operationnel

Supabase doit contenir seulement ce qui sert a l'app connectee.

#### Option recommandee V1

Pousser uniquement :

- contacts proprietaires/mandants lies a une annonce ;
- contacts acquereurs presents dans offres/compromis/ventes ;
- contacts membres de doublons high/critical ;
- relations contact-annonce utiles a la navigation ;
- statistiques agregees.

Volume estime :

| Perimetre | Contacts |
| --- | ---: |
| Proprietaires/mandants lies a annonce | 91 991 |
| Acquereurs transactionnels | 14 298 |
| Union proprietaires + acquereurs transactionnels | 104 653 |
| + doublons high/critical | 130 348 |

Cette option evite de pousser les 354 293 contacts tout en couvrant les
contacts operationnels et les risques de doublons.

#### Option V1+

Ajouter les acquereurs actifs :

- volume estime : 223 310 contacts ;
- interet : recherche commerciale plus large ;
- inconvenient : plus lourd et moins utile tant que toutes les recherches
  `ContactById` ne sont pas normalisees.

Je recommande de ne pas commencer par V1+.

### 4. Tables Supabase allegees

Tables a exposer :

| Table Supabase | Contenu |
| --- | --- |
| `app_contact_light_current` | Identite minimale, role, agence, negociateur, archive, dates, score qualite |
| `app_contact_relation_light_current` | Relations annonce-contact avec roles |
| `app_contact_search_light_current` | Recherches acquereurs actives ou recentes seulement |
| `app_contact_duplicate_alert_current` | Groupes doublons high/critical seulement, sans details complets |
| `app_contact_stats_current` | Compteurs agreges par role, agence, anomalie, doublon |

Donnees a ne pas pousser :

- JSON brut Hektor ;
- historique complet `ContactById` ;
- toutes les recherches archivees ;
- tous les groupes doublons low/medium ;
- commentaires longs ;
- payloads annonce rattaches depuis `data.annonces`.

### 5. Ergonomie app proposee

Module "Contacts" en 4 onglets :

1. **Annuaire**
   - recherche rapide ;
   - filtres role, actif/archive, agence, negociateur ;
   - badge "local complet" si le detail existe localement ;
   - badge "a rafraichir" si `datemaj` a change.

2. **Relations annonce**
   - proprietaire ;
   - acquereur offre ;
   - acquereur compromis ;
   - acquereur vente ;
   - acces direct a l'annonce.

3. **Recherches acquereurs**
   - budget min/max ;
   - ville/secteur ;
   - type de bien ;
   - pieces/chambres/surface ;
   - statut recherche active/archivee ;
   - plus tard : annonces compatibles.

4. **Doublons**
   - priorites high/critical ;
   - comparaison cote a cote ;
   - action "classer", "ignorer", "a fusionner plus tard" ;
   - jamais de suppression automatique.

Les details lourds doivent etre charges a la demande depuis le serveur local,
pas depuis Supabase.

### 6. Creation et modification de contacts

Pour ajouter ou modifier un contact Hektor :

- l'app cree une demande/action dans une file locale ou Console ;
- la Console execute l'action dans Hektor ;
- apres succes, le serveur local relance `ContactById` pour le contact ;
- la couche locale est reconstruite ;
- Supabase recoit seulement la ligne legere si le contact appartient au
  perimetre expose.

Il ne faut pas faire une ecriture directe Supabase comme si Supabase etait la
source de verite.

## Decision recommandee avant implementation

Je recommande cette trajectoire :

1. garder la base locale comme miroir complet ;
2. etendre les relations locales avec les roles acquereurs transactionnels ;
3. ajouter les tables locales detail/recherches/annonces/anomalies ;
4. lancer un backfill `ContactById` progressif et reprenable ;
5. remplacer le push Supabase actuel par un push "light V1" limite a environ
   130 000 contacts ;
6. adapter l'app pour charger :
   - index et navigation depuis Supabase ;
   - detail lourd depuis le serveur local quand necessaire.

Cette version est plus robuste, moins couteuse pour Supabase, et plus fidele a
la realite Hektor.
