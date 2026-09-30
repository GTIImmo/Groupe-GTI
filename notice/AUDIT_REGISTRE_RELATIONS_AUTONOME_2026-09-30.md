# Audit — le registre des relations contact ↔ bien, vers l'autonomie

*30/09/2026. Lecture seule : aucun code, aucune écriture en base. Déclenché par un bug vu à
l'écran (fiche contact de Julien SAURA : « Aucune annonce liée » alors que la fiche annonce le
montre mandant), puis élargi à la demande de Frédéric : « il me faut un registre des relations
autonome, qui se met à jour selon un contrat d'autorité entre le run de nuit Hektor et les
workers de l'app ».*

**Périmètre** : l'objet RELATION (mandant, propriétaire, acquéreur offre / compromis / vente).
Les autres objets ne sont mesurés que là où ils touchent la relation.
**Méthode** : code actuel (front, worker, build, push, fonctions SQL en base), les deux bases
(`phase2/phase2.sqlite` et Supabase), l'historique git et les notes.

---

## 0. En une page

```
LE LIEN A SON IDENTITE CHEZ NOUS        oui   carnet app_relation_registry (C.9-d, C.9-f)
LE LIEN A SON EXISTENCE CHEZ NOUS       NON   la table est refaite CHAQUE NUIT depuis 6 sources
                                              Hektor (DELETE + INSERT de la table entiere)
L'APP ECRIT UN LIEN DURABLE             NON   seulement une ligne PROVISOIRE, purgee sous 24 h
LE WORKER ECRIT UN LIEN DURABLE         NON   il ne sait qu'EFFACER (suppression contact/annonce)
CONTRAT D'AUTORITE POUR LE LIEN         AUCUN pas de pending, pas de dirty, pas d'adoption
SENTINELLE                              AUCUNE
LA FICHE ANNONCE LIT LE REGISTRE        NON   elle lit proprietaires_json (copie Hektor, n° Hektor)
LA FICHE CONTACT LIT LE REGISTRE        oui   mais recoit un n° Hektor depuis l'annonce -> vide
```

**La relation est le seul des objets principaux qui n'a qu'UN robinet.** L'annonce, le contact
et la transaction en ont deux (le run ET l'app). Le mandat en aura deux (étape D).

---

## 0-bis. SECONDE PASSE, demandée par Frédéric le 30/09 après-midi

> *« Les liens sont toujours créés dans Hektor jusqu'à la coupure. Tu dois voir ce registre
> dans la globalité du projet, car le lien actuel du front pointe tout sur l'id Hektor et
> non sur un registre serveur et apps avec id apps. »*

**SA PRÉMISSE EST JUSTE POUR LE FRONT, ET FAUSSE POUR LES DONNÉES — et c'est une
bonne nouvelle.** Mesuré en production le 30/09 :

```
app_contact_relation_current                                          81 379 lignes
   colonne « hektor_contact_id » -- valeurs DANS LA PLAGE APP         81 379   100 %
                                 -- valeurs de style Hektor                0
   etendue des valeurs                              10 000 023 .. 10 650 449
   colonne app_contact_id, presente et remplie                        81 366
   colonne app_dossier_id, remplie                                    81 379   100 %

app_contact_current  -- meme constat sur la fiche contact
   « hektor_contact_id » dans la plage app          62 059 sur 62 059   100 %
```

### ⚠ LE NOM DE LA COLONNE MENT, ET C'EST POUR ÇA QUE PERSONNE NE L'A VU

`build_contacts_layer.py:1093` fait `contact_id = identite_app(contact_id)` **AVANT** de
remplir la ligne, puis écrit `"hektor_contact_id": contact_id`. Depuis la bascule du 23/09,
cette colonne ne contient **plus jamais** un numéro Hektor. Le nom est un vestige.

➡ **La couche de données est DÉJÀ sur nos numéros.** Ce n'est pas le chantier qu'on croyait.

### CE QUI MANQUE VRAIMENT, ET C'EST AILLEURS

```
① LA VUE QUE LIT LE FRONT N'EXPOSE PAS app_contact_id
   app_contact_relations_current recopie 18 colonnes sur 19 : elle OUBLIE la
   derniere, app_contact_id. La donnee est la, le front ne peut pas la voir.
   -> une ligne dans un CREATE VIEW.

② LE FRONT PASSE UN NUMERO HEKTOR sur le chemin annonce -> contact
   La fiche annonce derive ses mandants de `proprietaires_json` (la copie Hektor,
   donc les numeros Hektor) et passe cet id a loadContactRelations, qui filtre
   `.eq('hektor_contact_id', ...)` -- une colonne qui ne contient QUE des
   numeros d'app. Rien ne correspond -> « Aucune annonce liee ». C'est le bug ①.
   -> la fiche annonce doit lire le REGISTRE, pas proprietaires_json.

③ relation_key EST DEJA AUTONOME -- et personne ne l'avait dit
   recette = {contact_id (identite APP), annonce_id (app_dossier_id, C.9-f),
              role, source, transaction_type, transaction_id}
   Les DEUX numeros de la cle sont les notres. La cle survivra a la coupure.

④ LE CARNET N'EXISTE PAS DANS LE CLOUD
   app_relation_registry : 167 583 cles, PUREMENT LOCALES. Le cloud n'en a
   aucune trace -- donc aucune adoption possible depuis Supabase.

⑤ LE CLOUD NE PORTE QUE LES BIENS ACTIFS
   81 379 contre 167 547 cote serveur. Les 6 sources sont toutes Hektor :
   api_annonce_detail_proprietaires · api_contact_detail_annonces ·
   api_list_compromis · api_list_offres · api_list_ventes ·
   sync_annonce_contact_link

⑥ L'EXISTENCE RESTE ENTIEREMENT AU MIROIR -- inchange depuis la 1re passe :
   DELETE + INSERT chaque nuit · aucune ecriture durable par l'app ou le worker ·
   aucun contrat d'autorite · aucune sentinelle.
```

### CE QUE ÇA CHANGE POUR LE CHANTIER

Le chantier n'est **pas** « mettre les liens sur nos numéros » — **c'est déjà fait**. Il est :

```
A  RENDRE NOTRE NUMERO VISIBLE     ajouter app_contact_id a la vue        1 ligne
B  FAIRE LIRE LE REGISTRE          la fiche annonce quitte proprietaires_json
C  DONNER SON EXISTENCE AU LIEN    table durable, 2 robinets, adoption,
                                   delete-never, sentinelles -- le patron
                                   applique 4 fois (annonce, contact,
                                   transaction, et le mandat le 30/09)
D  RENOMMER LA COLONNE             cosmetique mais dangereux : le nom ment,
                                   et c'est ce mensonge qui a cache le bug
```

**A et B sont petits et rendent l'écran juste tout de suite. C est le vrai chantier.**

---

## 1. Ce que contient le registre aujourd'hui (mesuré le 30/09)

### 1.1 Volumes

```
serveur   app_contact_relation_current   167 547 liens · 109 605 contacts · 58 622 biens
          app_relation_registry (carnet) 167 583 cles  · 36 marquees absentes, jamais effacees
          app_relation_app_seule              45 recensees, JAMAIS reinjectees
Supabase  app_contact_relation_current    81 379 = les liens des annonces ACTIVES seulement
                                                   (push : WHERE is_active_annonce = 1)
          app_relation_provisional             0 (purgee)
          contacts nes dans l'app (>= 20 M)    0 — le compteur est encore a 20 000 000
```

Tous les contacts des liens portent déjà l'identité de l'app (10 M–20 M). Aucun lien ne porte
un contact né dans l'app : le chemin n'a encore jamais servi en réel.

### 1.2 Rôles × sources

| rôle | source Hektor (miroir) | liens |
|---|---|---|
| mandant | `api_annonce_detail_proprietaires` (`hektor_annonce_detail.proprietaires_json`) | 45 134 |
| mandant | `sync_annonce_contact_link` | 24 617 |
| mandant | `api_contact_detail_annonces` (`raw_api_response`, fiche contact) | 4 415 |
| propriétaire | `api_annonce_detail_proprietaires` | 30 409 |
| propriétaire | `sync_annonce_contact_link` | 25 977 |
| propriétaire | `api_contact_detail_annonces` | 2 070 |
| acquéreur compromis | `api_list_compromis` (`hektor_compromis.acquereurs_json`) | 13 269 |
| acquéreur offre | `api_list_offres` (`hektor_offre`) | 11 145 |
| acquéreur vente | `api_list_ventes` (`hektor_vente.acquereurs_json`) | 10 511 |

États des transactions portées : compromis actifs 11 632 / annulés 1 637 · offres acceptées
9 949 / refusées 1 112 / proposées 30 / sans état 54 · ventes 10 511.

### 1.3 Trois faits qui changent la conception

**① « Mandant » et « propriétaire » ne sont PAS deux faits Hektor. C'est UN fait, étiqueté
après coup.** Hektor dit « cette personne est propriétaire du bien ». Le build réécrit ensuite
le rôle : `mandant` si l'annonce porte un numéro de mandat, sinon `propriétaire`
(`build_contacts_layer.py:1337`), et **APRÈS** le calcul de la clé. D'où les 57 % de clés
seulement recalculables depuis la table (mesure du 24/09), et d'où le carnet C.9-d qui note la
recette **avant** la réécriture. Conséquence : un registre autonome doit stocker le fait brut
(« lié au bien comme propriétaire ») et **dériver** le libellé mandant / propriétaire, sinon
chaque signature de mandat changerait l'identité du lien.

**② Le même lien arrive par trois sources.** Les trois sources hors transaction
(`proprietaires_json`, `sync_annonce_contact_link`, fiche contact) produisent la même clé
(`source = non_transaction`) : la dernière lue gagne. Le lien n'a donc qu'un seul vrai contenu,
vu par trois fenêtres de Hektor.

**③ Les acquéreurs sont DÉJÀ tenus ailleurs, et durablement.** `app_affaire_ledger` porte
l'acquéreur de chaque offre / compromis / vente (30 364 lignes sur 31 017), avec
`hektor_acquereur_id`, `app_contact_id`, `acquereur_json`, `acquereurs_json` et deux robinets
(run + worker). Les 34 925 liens « acquéreur » de la table des relations sont une **seconde
copie** du même fait, refaite depuis le miroir. Ils ne sont pas une source : ils doublonnent le
ledger.

Autres mesures : 11 504 paires (contact, bien) portent plusieurs rôles (vraisemblablement le
même acquéreur à l'offre puis au compromis — non vérifié ligne à ligne) ; 523 triplets
(contact, bien, rôle) ont plusieurs lignes (plusieurs transactions) ; 9 liens sans bien connu
chez nous.

---

## 2. Objets × gestes — la relation

| geste | où | fonction / RPC | job worker | ce qui reste DANS L'APP |
|---|---|---|---|---|
| **rattacher** un mandant existant | fiche annonce, « Mandants » | `app_link_mandant_optimistic` | `link_hektor_mandant` | provisoire seulement ; aucun rafraîchissement du contact → le lien durable n'arrive qu'au run de nuit |
| **créer** un contact comme mandant | fiche annonce, « Mandants » | `app_create_mandant_contact_optimistic` | `create_hektor_mandant_contact` | provisoire seulement : **ni contact ni lien** avant Hektor (contrairement à la création par l'annuaire) |
| **modifier** un mandant | carte mandant, « Modifier » | `app_update_mandant_contact_optimistic` | `update_hektor_mandant_contact` | le contact, oui ; le lien ne change pas |
| **retirer** un mandant | — | — | — | **LE GESTE N'EXISTE PAS** (déjà noté le 25/09, `AUDIT_OBJETS_ET_GESTES`) |
| mandant à la **création d'annonce** | assistant, étape mandat | `app_create_annonce_job_optimistic` | `create_hektor_draft_annonce` | rien, pas même un provisoire : le mandant n'est que dans la charge du job |
| propriétaire à la **création d'un contact** | annuaire, « Relier à une annonce » | `app_create_contact_optimistic` | `create_hektor_contact` → `applyHektorOwnerNextStep` | le contact oui, le lien non |
| **acquéreurs** d'une offre / compromis / vente | modale transaction | `app_change_annonce_status_optimistic` | `change_hektor_annonce_status` | création : **durable dans `app_affaire_ledger`** · modification : les acquéreurs ne vont que dans le job ; le ledger ne reprend que ce que Hektor relit |
| **mandants d'une affaire** | modale transaction, `SelecteurMandants` | idem | idem (`tx.mandantsVoulus`) | **rien de durable** : ni colonne ni carnet, seulement `personnes_posees` pour l'alerte d'écart |
| notaire vendeur / acquéreur | modale transaction | idem | idem | seul le notaire de l'acquéreur va au carnet |
| choisir les mandants d'un **numéro de mandat** | formulaire mandat | `app_console_create_mandat_auto_number_job` | `create_hektor_mandat_auto_number` | rien (choix parmi les liés, pas d'ajout) |
| **supprimer** un contact / une annonce | fiches | — | `delete_hektor_contact` / `delete_hektor_annonce` | le worker **EFFACE** ses liens dans Supabase (`cleanupSupabaseContactRows`, `cleanupSupabaseAnnonceRows`) — le seul endroit où il écrit la table |
| **lire**, fiche contact | | `loadContactRelations` | | registre, n° app ✅ (mais voir §4, bug 1) |
| **lire**, fiche annonce | | `buildDetailContactsFromProprietaires` | | `proprietaires_json`, n° Hektor ❌ |
| **lire**, liens en attente | | `loadRelationProvisionals` → `MandantsEnCreation` | | visible dans UN seul écran (voir §4, bug 3) |
| co-mandant / conjoint | | — | | aucun geste ; le conjoint n'est que des champs `spouse*` |

⚠ **Les définitions SQL de `app_link_mandant_optimistic`, `app_create_mandant_contact_optimistic`
et `app_update_mandant_contact_optimistic` ne sont versionnées nulle part** dans `supabase/`.
Elles n'existent que dans la base de production.

---

## 3. Le contrat d'autorité : ce que les autres registres ont, et que la relation n'a pas

| | annonce `app_dossier` | contact `app_contact` | transaction `app_affaire_ledger` | mandat `app_mandat` | recherche | **relation** |
|---|---|---|---|---|---|---|
| numéro frappé par une séquence | ✅ | ✅ `app_contact_identite_seq` | ✅ plage ≥ 1 000 000 | ✅ | nom figé (registre) | ❌ clé = empreinte calculée en Python |
| l'app écrit la ligne durable au geste | ✅ (e3) | ✅ par l'annuaire / ❌ comme mandant | ✅ à la création | 🟡 étape D | ❌ provisoire (à confirmer, le plan dit ✅) | ❌ |
| le run **adopte** ce que l'app a créé | ✅ | ✅ | ✅ triplet (annonce, type, acquéreur) | ✅ | — | ❌ |
| le run **conserve** (jamais de suppression) | ✅ | ✅ `absent_depuis` | ✅ UPSERT, « le silence ne gagne pas » | ✅ `present_in_hektor` | ✅ | ❌ DELETE + INSERT de la table entière |
| saisie en attente protégée au push | ✅ pending | ✅ `app_contact_pending` | ✅ carnet `app_affaire_champ_app` | ✅ par omission | ✅ dirty | ❌ |
| suppression ordonnée par l'app, journalisée | — | — | ✅ `app_affaire_supprimee` | — | — | ❌ |
| sentinelles | 4 | 4+ | ✅ | ✅ `mandat_disparu` | 5 | **0** |

**La règle générale est déjà écrite** (journal des décisions du plan, 21/09, « PAS D'INTERRUPTEUR ») : *pas d'interrupteur,
la règle est permanente et symétrique ; l'arbitre est la RÉCENCE ; Hektor confirme, il
n'écrase pas.* Elle est codée pour l'annonce (`app_annonce_reappliquer_saisies`), le contact
(`push_contacts_to_supabase.py:451-504`), la transaction (`affaire_ledger.py:763-903`). **Elle
n'a jamais été appliquée à la relation**, faute de ligne durable à protéger.

---

## 4. Défauts trouvés en chemin (à corriger, hors du chantier principal)

1. **Fiche contact vide quand on l'ouvre depuis une annonce.** L'annonce passe le n° Hektor
   (`110090`) ; `loadContactById` cherche sous les deux numéros, mais `loadContactRelations` et
   `loadContactSearches` seulement sous l'identité (`App.tsx:13060`, `api.ts:3209` et `3379`).
   Décision G-6 du 23/09 (« cohérentes par construction ») jamais vérifiée sur ce chemin, et
   **figée par un test** (`test_genants_front.cjs:83`).
2. **`update_hektor_mandant_contact` rafraîchit le contact avec la CIBLE** (worker :17439),
   alors que le pipeline attend l'identité — exactement le défaut décrit par C-12 (:4138).
3. **Un lien en attente est invisible** hors de `DossierDetailLayoutBase` : ni dans le cockpit
   (:28515), ni sur mobile (:33833), ni quand le bien n'a encore aucun mandant (:29862).
4. **`constaterLesPersonnes`** range un n° Hektor dans `app_affaire_personne_ecart.contact_id`,
   puis cherche le nom par identité : après la bascule, le bandeau peut afficher un numéro au lieu
   d'un nom.
5. `link_hektor_mandant` et les mandants de création d'annonce ne déclenchent **aucun
   rafraîchissement du contact** : même quand Hektor a confirmé, le lien n'arrive qu'au run de
   nuit.

---

## 5. Pourquoi le plan ne l'a pas vu venir

- **31/08** : ligne provisoire choisie *parce que* la clé était un haché calculé en Python
  (« deux copies d'une formule divergent »). Choix juste à l'époque.
- **03/09** : le plan écrit la conséquence (révision du 03/09, bloc « 26bis-relations n'avait jamais été décrit ») — *« ce patron meurt à la coupure »* — et le
  même jour les transactions reçoivent la solution (un numéro frappé, jamais calculé), en citant
  la relation comme leçon (LISTE, registre des transactions, tâche 1.1). **La relation ne la reçoit pas.**
- **21/09** : L2 est marqué ✅ « relations » ; ce qui a été livré (`bc359b6`) est un
  **observateur** (« on observe »). La case `26bis-RELATIONS` de la liste reste, elle, `[ ]`.
- **24-25/09** : C.9-d / C.9-f règlent l'**identité** du lien. L'**existence** reste au miroir,
  et la clé reste un haché fabriqué par le build : l'obstacle du 31/08 est intact pour l'app.
- **28/09** : l'audit final nomme la relation « seule vraie faiblesse » — notée, pas enchaînée.
- Le tableau comparatif du plan (section « FINIR L'ANNONCE ») note « naît dans l'app ✅ » pour la recherche, et
  « 13 sur 16 » gestes écrivent d'abord dans l'app en comptant « créer un mandant » : **les deux
  sont faux pour la relation.**

---

## 6. Ce qu'il faudrait — piste à valider, PAS une décision

Le patron existe déjà trois fois ; il suffit de l'appliquer au lien.

1. **Un numéro de lien frappé** (séquence, comme `app_affaire_id`), jamais calculé. La clé
   métier sert à l'**adoption** : (identité du contact, `app_dossier_id`, famille de rôle).
   Le haché actuel reste en doublure le temps de la transition (le carnet C.9-d le permet).
2. **Deux robinets, une table.**
   - l'app : la RPC du geste écrit la ligne durable **tout de suite**, avec son numéro, comme
     `app_create_contact_optimistic` pour le contact ;
   - le run : il **adopte** par la clé métier, ne crée que l'inconnu, **ne supprime jamais**
     (`absent_depuis` / `present_in_hektor`), et laisse gagner une saisie app en attente.
3. **Le fait brut, pas le libellé** : « propriétaire du bien » est stocké ; « mandant » se
   dérive du mandat à la lecture.
4. **Les acquéreurs ne se dupliquent pas** : ils vivent dans `app_affaire_ledger`, et le
   registre des relations les **projette** au lieu de les recopier depuis le miroir.
5. **Retirer devient un geste**, journalisé comme `app_affaire_supprimee`.
6. **Les deux fiches lisent la même table** : la fiche annonce quitte `proprietaires_json` (qui
   reste en secours derrière un interrupteur).
7. **Les sentinelles** : lien app non adopté au-delà de N jours, lien disparu, œil
   serveur ↔ Supabase.
8. **Versionner** les fonctions SQL des gestes mandant dans `supabase/`.

## 7. Questions pour Frédéric avant tout code

1. Le registre doit-il porter **tous** les liens (167 547, archives comprises) dans Supabase,
   ou seulement ceux des biens actifs, comme aujourd'hui (81 379) ?
2. Les acquéreurs : **projection** depuis `app_affaire_ledger` (recommandé) ou copie ?
3. « Retirer un mandant » : le geste doit-il partir chez Hektor tant qu'il vit, ou rester propre
   à l'app ?
4. Les mandants choisis dans une affaire (`mandantsVoulus`) : sont-ils des liens au bien, ou
   seulement des parties de la transaction ?
5. Ordre : corriger d'abord les défauts du §4 (petits, sans risque), puis le registre ?

*Non mesuré : le détail de `delete_hektor_compromis`, la partie Protexa de
`create_hektor_mandat_auto_number`, et le chemin « passage en acquéreur » de la recherche
(`d7a3586`).*
