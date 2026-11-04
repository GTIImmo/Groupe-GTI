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

## 9. LES DOUBLONS — CE QUI EXISTE, CE QUI EST FAIT, CE QUI RESTE *(04/11, « on reprend l'audit des contacts, les doublons et les 176 000 »)*

- **Le cahier des charges existe** (`CAHIER_CHARGES_DOUBLONS_CONTACTS_2026-06-29.md`, « version de cadrage, à valider avant développement ») :
  - un workflow de qualité des données, « pas un script de suppression » ;
  - 4 règles de détection, 5 priorités (recherches actives d'abord), 7 lots ;
  - l'archivage automatique y est interdit.
- **Ce qui est fait : le lot 0 seulement.**
  - Le détecteur tourne chaque nuit (`build_contacts_layer.py`, `duplicate_key_groups`) et pose sur chaque fiche `duplicate_group_count`,
    `duplicate_max_severity` et `duplicate_primary_candidate_id`.
  - L'app ne s'en sert que pour une pastille de risque (`contactHasDuplicateRisk`, `App.tsx` 40539), le tri de l'annuaire (les fiches à
    doublons d'abord) et un compteur.
  - Les tables de groupes ne partent pas dans le cloud : `--include-duplicates` n'est pas passé la nuit.
- **Ce qui n'est pas fait** : les lots 1 à 6 (affinage des règles, couche de décisions, écran de revue, traitement). Le geste « fusionner deux
  fiches » n'existe pas (L5 / E.0-bis reporté, CH39 proposé le 07/10, rien de décidé).
- **La mesure la plus récente** (audit des couples anciens §8, 01/11) : 37 715 groupes, 48 333 fiches.
  - 27 500 groupes sont la même personne : 12 950 personnes en 27 810 fiches, soit **14 860 fiches en trop**. Dans l'app : 2 868 personnes
    touchées, et **444 ont deux fiches vivantes ou plus**.
  - 4 132 groupes ont le même nom avec des prénoms différents (des conjoints ou une famille, pas des doublons).
  - 3 888 groupes partagent un e-mail sous des noms différents ; 2 195 ont le même prénom et des noms différents.
  - Les doublons ont fabriqué 9 232 foyers automatiques en trop.
- **Le lien avec l'index** :
  - un index de tous les contacts mettrait sous les yeux des agents les 14 860 fiches en trop, aujourd'hui invisibles parce qu'elles sont
    hors de l'app (11 956 actives et 25 099 archivées hors de l'app sont dans un groupe) ;
  - ⇒ l'index et les doublons se décident ENSEMBLE : soit l'index montre la pastille de doublon et propose la fiche principale
    (`duplicate_primary_candidate_id`), soit il n'expose que la fiche principale de chaque groupe « même personne ».

## 10. LES 176 417 PERSONNES HORS DE L'APP — QUI ELLES SONT

- **64 039 actives** :
  - 50 694 joignables (36 081 par e-mail, 44 120 par téléphone) ;
  - par type : mandant 22 410, acquéreur 21 816, **partenaire 16 098**, mandant + partenaire 1 976, acquéreur + mandant 1 673 ;
  - 23 242 ont un lien avec un bien (désormais archivé) ; 51 seulement ont une recherche, inactive ;
  - 11 956 sont dans un groupe de doublons ; 605 sont marquées supprimées chez Hektor ;
  - dernière modification : mars 2025 pour 25 302, novembre 2024 pour 14 215 (les mises à jour de masse, §63) ;
  - créées surtout entre 2019 et 2026 (de 2 000 à 5 000 par an).
- **112 378 archivées** :
  - 108 784 joignables ;
  - 25 099 dans un groupe de doublons ;
  - 10 334 avec un lien à un bien ; **57 263 avec une recherche, inactive** (d'anciens acquéreurs) ;
  - dernière modification : surtout les trois purges (mars 2025 44 420, septembre 2023 34 670, octobre 2021 13 120).
- **Ce qui les cite déjà dans l'app** : le REGISTRE des relations. Chez Supabase, **50 920 contacts du registre (63 182 liens) sont absents de
  l'app**, sur 96 313 contacts cités.
  ⇒ L'historique d'un bien sorti du parc nomme des personnes dont l'app n'a pas la fiche. C'est le trou qu'un index fermerait le plus
  utilement : une fiche à la demande depuis le registre.
- **Ce qui reste non mesuré** : ce que l'écran montre aujourd'hui quand il rencontre ces 50 920 (un nom, un numéro, rien ?) ; la part des
  partenaires qui seraient utiles dans l'annuaire.

## 11. CE QUI SE DÉCIDE, DANS L'ORDRE PROPOSÉ

1. **Les contacts figés** : le remède en une clause est prêt et éteint (synthèse couples §64). Il est indépendant de tout le reste.
2. **L'index** : qui y entre. Les mesures suggèrent de commencer par **les contacts cités par le registre** (50 920). Ce sont eux qui manquent à
   l'écran, plutôt que les 176 417 d'un coup.
3. **Les doublons** : valider (ou revoir) le cahier des charges du 29/06 avant d'exposer plus de fiches, et décider si l'index montre les
   doublons ou seulement la fiche principale.
4. **Les données personnelles** : téléphone et e-mail dans l'index, oui ou non.

## 12. LES 50 920 VÉRIFIÉS : 50 911, TOUS PROPRIÉTAIRES DE BIENS SORTIS DU PARC *(04/11, « vérifier et mesurer les 50 920 et revoir la règle »)*

- ⛔ **Correction de ma mesure** : la jointure passait par `app_contact_current.app_contact_id`, qui est VIDE sur 22 fiches de l'app. Ce sont
  des contacts nés chez Hektor cette nuit, propriétaires de 9 biens vivants, que j'avais crus absents. Joint sur le bon numéro
  (`hektor_contact_id` = l'identité) : **50 911 contacts, 63 172 liens**.
  ⚠ 22 fiches sans `app_contact_id` chez Supabase : à suivre, sans effet mesuré.
- **Ce qu'ils sont** : 100 % « propriétaire du bien » (mandant ou propriétaire), aucun acquéreur. Sur les biens :
  - **index des archives : 49 214 contacts, 28 385 biens** ;
  - aucun index : 2 468 contacts sur 1 930 biens, dont 1 926 dans la plage 55 120 – 58 871, c'est-à-dire **des LOCATIONS** (`offre_type` 2 et 11,
    « Mandat clos »). Les locations restent au serveur par décision du 26/08 ;
  - parc vivant et index des vendus : **0**.
- **Ce que l'écran montre** :
  - pour un bien VIVANT, la rubrique Contact lit le registre (`loadAnnonceMandants`, `api.ts` 10794). Un lien sans fiche « n'est pas jeté » :
    la ligne revient avec un nom vide, et l'appelant la reconnaît ;
  - pour un bien ARCHIVÉ, la fiche vient du cache préparé depuis le serveur (`mandants_texte`, `proprietaires_json`), donc avec des noms.
  - ⚠ **Non vérifié à l'écran** : ce qui se passe quand on clique sur un de ces noms. Il n'existe aucune fiche à ouvrir dans l'app.

## 13. LA RÈGLE D'ENVOI — CE QU'ELLE DIT, ET CE QU'ON POURRAIT CHANGER (rien n'est décidé)

- **Elle dit** (`build_contacts_layer.py` l. 1750, plus `elargir_perimetre_console.py`) : un contact monte s'il a
  (1) un lien à une annonce NON ARCHIVÉE (vendus et estimations compris), ou (2) une recherche active, ou (3) un rôle dans une transaction
  lue par la console. Elle ne regarde ni l'archivage du contact, ni notre registre.
- **Ce qui en découle** : les propriétaires d'un bien VENDU non archivé sont dans l'app, ceux d'un bien ARCHIVÉ n'y sont pas, alors que
  notre registre les nomme dans les deux cas (49 214 dans le second).
- **Les formes possibles** :
  - **R1 — ne rien changer.** Les 49 214 restent nommés dans l'historique du bien, sans fiche.
  - **R2 — ajouter une 4e raison : « nommé par notre registre des relations »** (hors locations). +49 214 fiches complètes dans l'app,
    ~5 Ko chacune avec les index, soit **~250 Mo**, plus une fois et demie la table d'aujourd'hui (317 Mo).
    Un seul ajout à la règle, sur le modèle exact de la 3e raison du 11/09.
  - **R3 — la même chose, mais en INDEX LÉGER** (§1-8) : ~336 octets par ligne, soit ~17 Mo plus les index, avec la fiche à la demande.
    Plus léger, mais c'est le chantier de l'index.
  - **R4 — resserrer** (« lié à un bien encore en vente ») : retirerait ~45 000 contacts d'affaires passées. ⛔ Contraire aux décisions du
    11/09 et du 30/09 (vendeurs et acquéreurs d'un bien vendu gardés) et à 8b.
- ⭐ **R2 est la plus simple** : elle suit la règle du 11/09 (« si Hektor nomme quelqu'un dans une transaction, l'app doit pouvoir le nommer ») ;
  ici, « si NOTRE registre nomme quelqu'un, l'app doit pouvoir l'ouvrir ». Son coût est le poids, à mesurer à blanc avant d'en décider.

## 14. LES PARTENAIRES ET LES CLASSEURS DE L'ANCIEN LOGICIEL *(04/11, « travailler les 16 098 pour voir si on peut en sortir un annuaire de partenaires, consulte aussi nos classeurs contacts Excel »)*

- **Chez Hektor**, la typologie ne dit que « partenaire », sans métier ni catégorie : 31 086 fiches actives hors de l'app portent le type
  `["partenaire"]` seul, dont **16 098 personnes** (les cases vides exclues).
  - Les champs utiles sont presque vides : SIRET 79, commentaire 3 598.
  - Coordonnées : 9 230 avec e-mail et téléphone, 3 929 avec e-mail seul, 2 432 avec téléphone seul, 15 495 sans rien (surtout les cases vides).
- **Le classeur de l'ancien logiciel** (`contacts_extraits.xlsx`, 202 218 fiches, lu en comptes seulement) porte un code `contact_type`
  (une liste), une `company_name` (2 946 remplies) et une `origin`.
- **Le croisement** (nom, prénom, jour de création ; même méthode que les appariements c3 du 01/11) : **11 531 des 16 098 partenaires
  retrouvés** (11 349 sans ambiguïté). Leur type dans l'ancien logiciel :
  - **AUCUN type : 7 543 (65 %)** ;
  - code 7 : 2 622 ; code 82 : 673 ; code 85 : 332 ; code 13 : 78 ; code 80 : 73 ; une poignée d'autres ;
  - 21 seulement ont une société.
  - Témoins : les acquéreurs de Hektor sont « 17 » dans l'ancien logiciel (11 358) ; les mandants y sont « 24 » ou « 2, 24 » (11 498).
  ⇒ ⭐ **« Partenaire » chez Hektor est surtout la case par défaut de l'import : les fiches SANS TYPE de l'ancien logiciel.** Un annuaire de
  partenaires tiré de cette typologie serait surtout du bruit.
- **Les vrais partenaires** sont sans doute les codes 7, 13 et 80 à 86 de l'ancien logiciel (le 13 porte beaucoup de sociétés : 409 sur 1 257).
  ⚠ **La signification des codes n'est écrite nulle part** dans le projet (270 combinaisons, `AUDIT_MIGRATION_C3` l. 233). Il faut que
  Frédéric (ou l'ancien logiciel) dise ce que sont 7, 13, 80, 81, 82, 83, 84, 85 et 86.
- **Ce qui serait possible ensuite** : un annuaire de partenaires construit sur les codes confirmés + la société + les coordonnées, avec
  la fiche Hektor en lien (11 349 appariés sans ambiguïté). Rien n'est proposé avant la signification des codes.

## 15. ⛔ CORRECTION DU §63 (synthèse couples) : LES « TROIS PURGES » NE SONT PAS PROUVÉES

- Dans l'ancien logiciel, **201 fiches seulement étaient archivées** sur 202 218. Les journées du 26/03/2025 (72 028 fiches) et du 20/12/2024
  (65 845) y sont des journées de **MODIFICATION en masse** (`time_modified`), et Hektor a recopié ces dates dans `date_maj`.
- ⇒ L'archivage de ~184 000 contacts a très probablement été posé **à la migration de mars 2026** (une règle d'import), et les dates du §63
  sont des dates de modification héritées, pas des dates d'archivage. La journée du 07/09/2023 (72 658, Saint-Étienne) n'apparaît pas dans
  l'ancien logiciel : son origine est **non établie**.

## 16. LES CODES DE L'ANCIEN LOGICIEL — TROUVÉS DANS « NOTICE MODELO » *(04/11, « tu arrives à lire la notice dossier notice modelo dans téléchargements »)*

- **La source** : `C:\Users\admin\Downloads\notice modelo.txt`. C'est la documentation OpenAPI de l'API **Netty** (« Groupe GTI Immobilier »,
  production), l'ancien logiciel, avec 17 chemins (`/contacts`, `/affairs`, `/mandates`, `/types`…). Hors du dépôt ; lue en lecture seule.
- **`contact_type`** :
  1 Locataire · 2 Vendeur · 3 Maintenance · 4 Administration · 5 Technicien · 6 Bailleur · 7 **Autre** · 8 Marchand de biens ·
  9 Apporteur d'affaires · 10 Fournisseur · 11 Huissier · 12 Avocat · 13 **Notaire** · 14 Banque · 15 Partenaire · 16 Agent immobilier ·
  17 **Acquéreur** · 22 Mandataire · 23 Collaborateur · 24 **Propriétaire** · 25 Investisseur · 26 Gestionnaire · 27 Promoteur ·
  29 **Prospect** · 34 Diagnostiqueur · 35 Newsletter · 36 Société · 37 Lotisseur · 80 **WebContact** · 81 WebContact – Envoi à un ami ·
  82 **WebContact – Demande d'estimation** · 83 WebContact – Alerte e-mail · 84 Courtier · 85 **Candidat** · 86 Parrain ·
  87 WebContact – Compte.
- **`origin`** :
  1 Passage à l'agence · 2 Site web de l'agence · 3 Portail · 4 Relationnel · 5 Annonce presse · … · 90 Leboncoin – Formulaire ·
  93 **Site web – Visite virtuelle** · 94-99 Site web (acquéreur, estimation, recrutement, alerte, divers) · 100 Maline.
  (La liste complète est dans la notice.)
- **`gender`** : 1 M. · 2 Mme. · 3 Mlle. Les valeurs 4, 5 et 6 vues dans le classeur (les couples) ne sont PAS documentées dans la notice.

**Ce que ça dit des 16 098 « partenaires » de Hektor** (§14, 11 349 appariés sans ambiguïté) : ce ne sont pas des partenaires.
- Sans type : 7 543 ; Autre : 2 622 ;
- **demandes d'estimation du site : 673** (des leads vendeurs) ;
- **candidats : 332** (du recrutement) ;
- notaires 78, webcontacts 73…

**Les vrais professionnels de l'ancien logiciel** (classeur, par métier ; une fiche peut en avoir plusieurs) : **1 469** en tout.
- **Notaires : 1 257**. 845 sont retrouvés chez Hektor (748 typés « partenaire »), **657 sont déjà dans l'app**. Ils sont couverts par le chantier du
  type Notaire (28/10 : la fiche et l'écran des notaires) et par le registre des ventes (1 280 notaires).
- **Les autres métiers : ~212 fiches** :
  - courtiers 43, apporteurs d'affaires 43, banques 39, diagnostiqueurs 30, parrains 17, sociétés 12, administration 11 ;
  - plus une poignée de mandataires, agents immobiliers, investisseurs et marchands de biens.
  - 113 sont retrouvés chez Hektor, et 31 sont dans l'app.
  - Presque tous sont joignables.

⇒ **Un annuaire de partenaires est faisable et PETIT** : les notaires (déjà traités) plus ~200 professionnels, que le classeur de Netty
classe par métier, alors que Hektor ne le fait pas.
⇒ **Deux gisements trouvés en passant**, à rattacher à d'autres chantiers :
- les **demandes d'estimation du site** (673 rangées « partenaire », 1 052 dans l'ancien logiciel) → les leads (A.5) ;
- les **candidats** (332 rangés « partenaire », 429 dans l'ancien logiciel) → le site de recrutement.
