# AUDIT — UN INDEX GLOBAL DES CONTACTS DANS LE CLOUD · 04/11/2026

> Demande de Frédéric : « pourquoi ne pas faire l'index global des archivés et actifs ? » puis « oui » (audit).
> Lecture seule : rien n'est codé, rien n'est écrit chez Supabase ni chez Hektor.
> Origine : synthèse couples §58, §61 et §61 bis (les 216 contacts figés, le verrou C-4 réglé sur 10 M au lieu de 20 M).
> ⚠ Audit limité à l'objet CONTACT (fiche, liens, recherches) et à la façon dont les ANNONCES le font déjà. Les autres objets ne sont pas mesurés.

## 1. Le principe de Frédéric, et où les contacts s'en écartent

Un objet doit pouvoir passer du serveur à l'app et de l'app au serveur. Le cloud reste léger : l'app ne garde la fiche complète que de ce qui sert,
et un simple listing (un index) du reste.

- **Les annonces le font déjà.**
  - Les annonces actives ont leur fiche complète dans `app_dossier_current` (et son détail).
  - Les autres ne sont là qu'en lignes d'index : 35 372 archives, 8 961 vendues ou closes, 562 brouillons.
  - Leur fiche complète est préparée à la demande depuis le serveur, pour 24 h.
- **Les contacts ne le font pas.**
  - Les ~63 000 contacts « qui servent » ont leur fiche complète dans `app_contact_current`.
  - Pour les ~293 000 autres, il n'y a RIEN dans le cloud : aucune table d'index, et pas de fiche à la demande.
  - Un contact qui cesse de servir n'a donc nulle part où aller. Le dessin efface sa fiche, mais depuis le 23/09 le verrou C-4 l'en empêche :
    la fiche reste figée (§61).

## 2. Comment les annonces le font — mesuré dans le code (compte rendu d'un agent, lecture seule)

- **Construction** : trois requêtes SQLite sur `app_view_generale` (`phase2/sync/export_app_payload.py` l. 313-497).
  - Une ligne compte ~28 colonnes : numéros, titre, ville, CP, prix, commercial, `negociateur_email`, agence, statut, mandat, `search_text`,
    `source_hash`.
  - Les colonnes sont normalisées par `build_current_*_index_rows` (`push_upgrade_to_supabase.py` l. 836-984).
- **Envoi de nuit** : en delta, par empreinte. Les lignes distantes absentes du local sont supprimées (l. 1641-1661 et 1750-1781).
  ⚠ Ces suppressions n'ont aucun plafond : le frein `max_stale_deletes` ne protège que `app_dossier_current`.
- **Au geste** : `push_single_annonce_to_supabase.py` lance `reconcile_lightweight_indexes` (l. 617-648).
- **Le passage** entre la table complète et l'index : aucune fonction chez Supabase ne le décide, c'est le périmètre SQL local. Une annonce sort
  de l'un parce qu'elle entre dans l'autre, et l'anti-doublon tient à ces périmètres exclusifs.
- **La fiche à la demande** :
  - le clic écrit une demande dans `app_console_job` (`api.ts` 9847-9931, `ttl_hours: 24`) ;
  - le worker lance `Console/prepare_*_annonce_detail.py`, qui lit le SQLite LOCAL (0 appel à Hektor) et écrit dans
    `app_*_annonce_detail_cache`, avec `expires_at` ;
  - l'écran relit ce cache tant qu'il n'est pas périmé.
  ⚠ Rien ne purge les caches expirés : ils sont seulement ignorés à la lecture.
- **Recherche** : `ilike` sur `search_text`, avec un index trigramme. L'écran fusionne les sources (`api.ts` 5226-5352).
- **Droits** : les MÊMES règles sur la table complète et sur les index (`patch_l4bis_vitesse_2026-10-12.sql` 191-257), par périmètre réseau,
  agence ou négociateur.

## 3. Les contacts aujourd'hui — mesuré

- **Droits** : `app_contact_current_select_scoped`, de la même forme que les index d'annonces (lecteur global / réseau / agence / adresse du
  négociateur). Au 03/11, tous les comptes sont au périmètre réseau (§49).
- **L'annuaire** (`loadContactsPage`, `api.ts` 3531) lit la vue `app_contacts_current` avec un compteur `planned` (approché) et un instantané
  de statistiques. ⭐ Le compteur exact a déjà été abandonné pour la vitesse : la contrainte « compter coûte cher » est déjà résolue ici.
- **Vitesse mesurée** : une recherche « durand » parmi les actifs prend **16 ms** sur 63 168 fiches.
- **Ouvrir un contact** : `loadContactById` (`api.ts` ~3590) ne cherche que dans la table complète. Un numéro absent ne donne rien, sans repli
  sur un index, contrairement aux annonces.

## 4. La population et le poids — mesurés

Couche locale (`phase2.sqlite`), nature de la nuit :
- **Déjà dans l'app** : 47 064 personnes (28 448 actives, 18 616 archivées) et 15 888 cases vides.
- **Hors de l'app** : **176 417 personnes** (64 039 actives, 112 378 archivées) et 117 455 cases vides de conjoint. Parmi elles, 605 personnes
  actives sont marquées supprimées chez Hektor, et 37 066 fiches sont dans un groupe de doublons.
- **Poids d'une ligne légère** (moyenne `pg_column_size` chez Supabase, sur 18 colonnes : numéros, civilité, nom, prénom, nom affiché,
  archive, téléphone, e-mail, ville, CP, négociateur, agence, type, nature, `search_text`, date) : **336 octets**, contre 683 pour une ligne
  complète.
  ⇒ Pour 176 417 personnes : environ 60 Mo de table, plus les index de recherche. **Estimation : 120 à 200 Mo** au total, soit 3 à 5 % de la base
  (4,3 Go). Non mesuré en vrai.

## 5. Ce que l'index réglerait

- Plus de contact figé : un contact qui cesse de servir quitte la table complète et passe dans l'index, à jour chaque nuit. Les 216 du §61 y
  passeraient, et les 104 archivés apparaîtraient archivés.
- L'annuaire trouverait les anciens clients, comme Hektor les trouve.
- Une affaire, une recherche ou l'historique d'un bien qui cite un contact de l'index retrouverait sa fiche, à la demande. C'est ce qui rend
  sûr le retrait de la table complète : l'option A du §61, sans son danger.
- Le verrou C-4 pourrait revenir sur 20 000 000 sans perte.

## 6. Les décisions à prendre — RIEN N'EST CHOISI

1. **Qui entre dans l'index** :
   (a) toutes les personnes hors de l'app (176 417) ;
   (b) les actives seulement (64 039) ;
   (c) seulement celles déjà passées par l'app.
   Dans tous les cas, les cases vides restent dehors (la nature les reconnaît).
2. **Quels champs** : le téléphone et l'e-mail dans l'index, ou seulement le nom et la ville ? Avec eux, le cloud porte les coordonnées de tous
   les clients. C'est une question de données personnelles, à trancher par Frédéric.
3. **La fiche à la demande** :
   (a) une table de cache à part, avec durée de vie, comme les annonces (l'écran de la fiche doit alors savoir la lire) ;
   (b) la fiche est remontée dans `app_contact_current` et y reste tant qu'elle sert.
   Dans les deux cas, elle se construit depuis le serveur, sans appel à Hektor : le détail est dans le miroir pour 348 873 contacts.
4. **Le premier envoi** : ~176 000 lignes, soit ~590 lots de 300, en une fois à un moment calme, ou réparti sur plusieurs nuits.
   Rappel : le 22/08, un envoi massif avait saturé Supabase.
5. **Garde-fous à poser d'emblée** : un plafond sur les suppressions de l'index (il manque pour les annonces) et une purge des caches expirés.

## 7. Ce que ça pourrait casser ailleurs

- Si l'index est une TABLE À PART, les écrans actuels, qui lisent la table complète, ne changent pas. Seuls l'annuaire (la fusion des deux
  sources) et `loadContactById` (le repli) seraient touchés.
- Remettre le verrou sur 20 000 000 fera retirer de la table complète, la nuit, les contacts qui ne servent plus. Il faut donc que l'index et le
  repli soient en place AVANT : cet ordre est obligatoire.
- La nature : l'index doit porter `nature_fiche`, pour écarter les cases vides et pour l'affichage des couples.
- Les compteurs de l'annuaire deviennent la somme de deux comptes approchés.
- La sauvegarde : l'index se reconstruit chaque nuit depuis le serveur, il n'y a rien de plus à sauvegarder.

## 8. Non mesuré

- Le poids réel et la vitesse d'une recherche sur l'index : à mesurer sur une copie, avec accord, car il faut écrire chez Supabase.
- Le chemin d'un négociateur (tous les comptes sont au périmètre réseau aujourd'hui).
- Les 18 tables qui pointent un contact (`marquer_contacts_disparus.py`) : lesquelles supposent aujourd'hui que le contact est dans la table
  complète.
