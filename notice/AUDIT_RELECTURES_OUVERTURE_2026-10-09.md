# Audit — les relectures Hektor à l'ouverture d'une fiche (« read-through »)

*09/10/2026, lecture seule. Question de Frédéric : « nos écritures sont maintenant chez nous,
pourquoi aller appeler Hektor à l'ouverture ? Peut-on supprimer ces refresh ? »
Origine : la modale « Préparer le mandat » se fermait seule (voir § 4).*

Audit limité aux relectures déclenchées par l'écran (annonce, contact) et au rechargement de
l'écran qui les suit. Les relectures du run de nuit et celles qui suivent un geste ne sont pas
remises en cause.

---

## 1. Ce qui existe

| déclencheur | travail créé | ce qu'il fait chez Hektor | où |
|---|---|---|---|
| ouverture d'une **fiche annonce** | `refresh_console_data` (motif `read_through_open`, mode léger) | détail de l'annonce, passerelles, mandats, propriétaires, photos, DPE, **puis l'état de signature des documents et le PDF signé** (`reconcileSignatureStates`, connexion web) | front `App.tsx` (effet `requestAnnonceRefresh`) · RPC `app_console_request_annonce_refresh` (TTL 30 min) · worker `handleRefreshConsoleData` |
| ouverture d'une **fiche contact** | `refresh_console_contact_data` (`read_through_open`) | fiche contact, recherches, liens | front (effet `requestContactRefresh`) · TTL 30 min |
| **après un geste** (rattacher un mandant, statut, etc.) | `refresh_console_data` avec le motif du geste | relit ce que Hektor a confirmé | worker, à la suite du geste |
| **toute fin de travail** suivi par l'écran | aucun : **rechargement de l'écran** (`dataReloadKey`) | — | `App.tsx`, polling toutes les 5 s |

## 2. Mesure sur 14 jours (Supabase, `app_console_job`)

```
relectures a l'ouverture   annonces 250 (236 faites, 14 en erreur) · contacts 24
                           ~20 par jour, 18,7 s en moyenne chacune
relectures apres un geste  16 en 14 jours
annonce la plus relue      63158 : 51 fois en 14 jours
```

**Ce qu'elles ont rapporté** (annonces, 235 classées contre la date de modification Hektor) :

```
176  (75 %)  RIEN de neuf chez Hektor depuis le run de nuit
 43  (18 %)  modifiee APRES la relecture -> indetermine
 16  ( 7 %)  modifiee chez Hektor dans la journee, AVANT la relecture
             dont 2 par un geste de l'app (deja ramene par la relecture d'apres-geste)
             -> 7 annonces reellement modifiees DANS HEKTOR sans l'app
                (18540, 42976, 63156, 63158, 63176, 63204, 63251)
signatures   1 PDF signe recupere en 236 relectures
```

## 3. Ce que ça coûte

- **Une dépendance à Hektor à chaque ouverture** : API et connexion web pour la signature
  (risque de freins et de bannissement déjà vécu), environ 20 fois par jour.
- **Le worker occupé** environ 19 s par ouverture.
- **Le rechargement de l'écran à la fin du travail** : c'est lui qui ferme les modales (§ 4).

## 4. La modale qui se ferme seule

1. Le polling (toutes les 5 s) recharge l'écran **dès qu'un travail se termine** : le sien (la
   relecture de la fiche, environ 20 à 30 s après l'ouverture), mais aussi **celui de
   n'importe quel utilisateur** parmi les types suivis (`hektorActionJobTypes`).
2. Le rechargement produit de nouveaux objets `detail` / `contacts`.
3. `MandatDocumentEditor` recalcule son brouillon sur l'identité de ces objets, et son effet
   fait `setOpen(false)`, remet le premier onglet et **écrase la saisie**
   (`App.tsx`, `useEffect([initialDraft])`).
   Reproduit le 09/10 sur 18402 : fermeture entre 8 et 16 s, au moment où un travail d'un
   autre utilisateur (contact Mickael MARTIN) se terminait.

## 5. Peut-on supprimer les relectures à l'ouverture ?

**Pas sans remplaçant, tant que Hektor vit (étape 2).** Elles ramènent encore :
- les **saisies faites directement dans Hektor** (7 annonces en 14 jours) ;
- les **numéros de mandat pris chez Hektor** (V430063244, n° 18928, le 08/10) ;
- l'**état de signature** des mandats en cours (1 en 14 jours).

**Mais elles sont mal placées** : elles ne voient un changement que si quelqu'un ouvre la
fiche, et paient Hektor 3 fois sur 4 pour rien.

### Proposition

| | geste | effet |
|---|---|---|
| **A** | un **delta de journée** : toutes les 15 à 30 min, UNE liste des annonces modifiées chez Hektor (triée par date de modification), puis la relecture des seules annonces changées | capte les saisies Hektor pour TOUT le monde, même si personne n'ouvre la fiche ; ~1 appel au lieu de ~20 |
| **B** | la **signature** suivie seulement pour les mandats « à envoyer » ou « en signature » (la règle « procédure en cours » existe déjà dans la conception documents) | plus de connexion web à chaque ouverture |
| **C** | **supprimer** les relectures à l'ouverture (annonce et contact) une fois A et B en place | plus aucune dépendance Hektor à l'ouverture |
| **D** | le **rechargement de l'écran** ne se déclenche que pour un travail qui concerne la fiche affichée | plus de rechargement pour le travail d'un collègue — **codé le 11/10** (`jobConcernsThisScreen`, App.tsx), en attente de déploiement |
| **E** | `MandatDocumentEditor` ne se ferme plus sur un simple rechargement (correctif mis de côté) | à faire de toute façon : un autre rechargement le déclencherait encore |

**Garder** : les relectures après un geste (elles ramènent la confirmation et les numéros de
Hektor), et le run de nuit.

**Ordre conseillé** : E et D d'abord (ils corrigent le symptôme sans toucher à Hektor), puis A
et B, puis C. Supprimer C seul ferait passer les saisies faites dans Hektor au lendemain
matin : acceptable seulement si les négociateurs n'y saisissent plus rien.

*Non mesuré : la part de saisies directes dans Hektor sur les contacts ; le coût exact d'une
relecture en appels Hektor ; si les 43 « indéterminées » ont ramené quelque chose.*

---

## 6. Faisabilité de Supabase Realtime *(audit du 10/10, lecture seule)*

**Ce qui est là** : abonnement Supabase **Pro** · `@supabase/supabase-js` **2.57** dans le front
(Realtime inclus) · la publication `supabase_realtime` existe mais **ne contient aucune table** ·
**aucun** usage de Realtime dans le front aujourd'hui · 6 comptes actifs, 3 connectés sur 7 jours.

**Les contraintes trouvées**
- **L'écran lit des VUES** (`app_dossiers_current`, `app_contacts_current`, `app_contact_relations_current`) ;
  Realtime ne suit que des **tables** : il faut écouter les tables sous-jacentes.
- **Le run de nuit réécrit des tables entières** : depuis la dernière remise à zéro des
  statistiques, `app_affaire_ledger` cumule 678 086 mises à jour pour 31 058 lignes,
  `app_contact_relation_current` 810 219 pour 85 260, `app_dossier_detail_current` 273 059
  pour 13 475. Écouter ces tables telles quelles enverrait des **dizaines de milliers
  d'événements par nuit**, la plupart pour des lignes inchangées.
- **« Postgres Changes » vérifie les droits (RLS) pour chaque événement et chaque abonné**, sur un
  seul fil d'exécution (documentation Supabase) : la doc conseille, à l'échelle, de passer par
  **Broadcast** (émis par un déclencheur en base) plutôt que d'écouter les tables.
- `DELETE` : la RLS ne s'applique pas, seul l'identifiant est transmis.

**La forme qui tient** : des **signaux légers**, pas les données.
1. **Un signal « ton travail est fini »** : déclencheur sur `app_console_job` quand `status`
   passe à `done` / `error`, envoyé sur un canal privé de l'utilisateur (`requested_by`).
   Remplace le sondage toutes les 5 s.
2. **Un signal « la fiche X a changé »** : déclencheur sur les tables de fiche, **seulement si
   la ligne a réellement changé** (`OLD IS DISTINCT FROM NEW`), envoyé sur le canal de la fiche ;
   l'écran abonné à CETTE fiche relit ce morceau.
3. **Rien pendant le run de nuit** côté écran : peu d'utilisateurs connectés, et le signal ne part
   que si la ligne change vraiment.

**Faisable** : oui. **Coût** : patch SQL (déclencheurs + politiques des canaux privés
`realtime.messages`, appliqué par Frédéric) + reprise des 4 rechargements du front.
**Prérequis conseillé** : la méthode C (rechargement ciblé) d'abord — Realtime en devient le
remplaçant naturel, sans tout refaire.

*Lu dans la documentation Supabase : les passages sur les limites de Postgres Changes, la RLS et
Broadcast depuis la base (extraits par mot-clé, pas la page entière).*

### 6 bis. Relecture complète de la doc Realtime (10/10)

Pages lues en entier : Concepts, Postgres Changes, Subscribing to Database Changes, Broadcast,
Authorization, Limits, Pricing, Manage Realtime Messages usage, Benchmarks ; Tables and data +
Views (base de données). Non lues : Presence, Protocol, Settings, Reports (tableaux de bord).

- La doc recommande **Broadcast** (« recommended method for scalability and security ») et présente
  Postgres Changes comme plus simple mais moins tenable à l'échelle.
- Pro : 500 connexions simultanées, 500 messages/s, **5 millions de messages/mois inclus**. Un
  événement compte 1 message par écran abonné. Avec 6 comptes, des signaux légers restent très
  loin du quota.
- Droits Broadcast : vérifiés **à l'entrée dans le canal** puis gardés en cache le temps de la
  connexion, sans relecture de la base à chaque message.
- Messages émis depuis la base : stockés dans `realtime.messages`, effacés après 3 jours ; un
  écran qui se reconnecte peut rattraper les 25 derniers (« replay », supabase-js ≥ 2.74 ; nous
  sommes en 2.57).

**Verdict** : Realtime n'est **pas nécessaire** au bon fonctionnement de l'app (peu d'utilisateurs,
peu d'édition simultanée d'une même fiche, aucune donnée à voir à la seconde près). Le vrai défaut
est le rechargement global (§ 5, D). Realtime devient utile ensuite, comme sonnette
(« ton travail est fini », « la fiche X a changé »), pas comme tuyau de données.

### 6 ter. Pourquoi l'écran lit des vues (10/10)

Vues lues par le front et ce qu'elles ajoutent à la table :

| vue | table | ce que la vue ajoute |
|---|---|---|
| `app_dossiers_current` | `app_dossier_current` | photo/vignette : **notre valeur d'abord**, sinon celle de Hektor |
| `app_registre_mandats_current` | `app_mandat_register_current` | même règle photo |
| `app_contacts_current` | `app_contact_current` | sélection de colonnes (contrat stable pour le front) |
| `app_contact_relations_current` | `app_relation` (+ annonces actives/historique/archives) | rôle calculé (mandant si n° de mandat, sinon propriétaire) + infos du bien |
| `app_dossier_details_current`, `app_work_items_current`, `app_filter_catalog_current` | table `_current` OU dernier instantané complet `_v1` | choisit la bonne version selon que le delta a tourné |

⚠ **Trouvé en passant (droits, non corrigé)** : 4 vues sont passées en « droits du
propriétaire » (`security_invoker` absent) : `app_dossiers_current`, `app_contacts_current`,
`app_contact_relations_current`, `app_registre_mandats_current`. Les tables `app_dossier_current`
et `app_contact_current` ont pourtant une RLS **par négociateur** (`is_app_global_reader() OR
can_access_negotiat…`) : à travers la vue, elle ne s'applique pas. Les patchs d'avril/mai posaient
`security_invoker` ; des `CREATE OR REPLACE VIEW` ultérieurs sans la clause `WITH` l'ont retiré
(ex. 21/05 annonces, 11/09 et 22/09 contacts). À traiter avec le chantier ② « droits ».
