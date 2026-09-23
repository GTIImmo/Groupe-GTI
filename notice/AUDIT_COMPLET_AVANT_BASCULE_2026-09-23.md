# Audit complet avant la bascule — les zones oubliées

*23/09/2026. Quatre balayages : la donnée (moi), le front, le serveur, le worker + l'API.
Une seule question posée à chacun : **qu'est-ce qui casse le jour où la VALEUR de
`hektor_contact_id` change ?***

---

## 0. Pourquoi je l'avais raté

Mes audits précédents ont **lu du code** et **jamais compté la donnée**. J'ai cherché
`hektor_contact_id` avec des `grep` : cela trouve les colonnes qui portent ce nom, et rate
celles qui portent le même contenu sous un autre nom — `contact_id`,
`primary_candidate_hektor_contact_id`, `related_entity_id`, `attendee_contacts[]`.

Et j'ai mesuré **une** famille à la fois. La bascule ne casse pas une famille : elle casse
**la couture entre deux familles**. Une table reconstruite chaque nuit bascule seule ; une
table jamais reconstruite reste en arrière ; **c'est la jointure entre les deux qui meurt**,
et elle ne meurt jamais avec une erreur — elle rend zéro ligne.

---

## 1. La surface réelle, mesurée

```
Supabase   28 tables portent une identite de contact         (j'avais dit 18)
           35 fonctions et vues cousent reconstruit <-> fige (j'avais dit 11 RPC)
Local      52 tables, 33 non vides, 8 maitrisees ici
API        11 lectures + 5 ecritures a cheval sur les deux familles
Worker      9 sites sortants + la PORTE elle-meme
Front      ~10 chemins, 12 garde-fous /^\d+$/ qui ne gardent rien
```

**Le point qui change tout** *(mesuré ce jour)* :

```
app_search_registry            77 088 lignes
   dont app_contact_id rempli  77 083      <- 99,99 %
   dont vide                        5
```

Le **nom figé** des recherches est ancré sur `(contact, rang)` et retrouvable **par les deux
numéros**. Puisque la doublure est déjà posée sur 77 083 lignes, **les 456 000 lignes qui
pendent sous `contact_search_key` ne bougeront pas**. C'est la plus grosse dépendance du
projet, et elle est **déjà protégée**. Il reste 5 lignes à combler.

En revanche `relation_key` n'a **pas** de registre : les **167 465** empreintes de relations
changent toutes la même nuit.

---

## 2. LE LISTING DES CORRECTIONS

### Bloquants — sans eux la bascule casse le jour même

---

**C-1 · La porte du worker se ferme sur tout le monde**
`Console/console_job_worker.js:1886-1892`

```js
const PLAGE_NUMEROS_APP = 10000000
if (Number(brut) >= PLAGE_NUMEROS_APP) throw   // <- AVANT de lire la cible
```

Après la bascule **tous** les contacts sont >= 10 M. La levée se produit **avant** la lecture
de `hektor_target_id` (`:1900-1906`). => **plus aucun travail ne part vers Hektor** :
`:4041`, `:14040`, `:15587`, `:15796`, `:16664`, `:16968`, `:11055`, `:11722`, `:14331`,
`:18576`. Et `ciblesHektorContacts` (`:1932-1957`) refuse **le lot entier** => aucun
compromis, aucune vente, aucun mandat.

> **Correctif** : lire `hektor_target_id` **d'abord** ; ne lever que si la cible est absente.
> Le message devient « pas encore créé chez Hektor », ce qu'il voulait dire depuis le début.

---

**C-2 · La sonde d'attente était aveugle au seul cas qui demande un humain**
`supabase/patch_5b_barriere_attente_2026-09-21.sql:62-66`, `:147-151`, `:190-198`

> ⚠ **CORRIGÉ LE 23/09, ET J'AVAIS ÉCRIT TROP GRAVE CE MATIN.** J'avais annoncé
> « plus aucune édition ne repart à la bascule ». **C'est faux** : la bannette est
> remplie **par le front en direct**, avec l'identité — la même que porte
> `app_contact_current`. Après la bascule, les deux côtés parlent la même langue.
> Le risque réel se réduit à **une ligne qui enjambe la bascule** : **0** aujourd'hui,
> et on bascule services arrêtés.
>
> **Mais l'audit a trouvé un défaut d'AUJOURD'HUI**, ci-dessous. Voir aussi le
> patch `supabase/patch_c2_sonde_attente_voit_tout_2026-09-23.sql`.

```sql
select * into ec from app_contact_current where hektor_contact_id = r.hektor_contact_id;
if ec.hektor_contact_id is null then continue;   -- silencieux
```

`r` vient de `app_contact_pending`. Quand la jointure ne rend rien, `continue` : **la saisie
reste dans la bannette pour toujours**, sans erreur, sans travail, sans trace. Et la **sonde**
censée voir l'attente (`app_v_envois_en_attente_hektor`) joignait de la même façon : **elle
était aveugle exactement au cas qu'elle devait voir**.

*(Ce que j'avais mal lu ce matin : la jointure ne casse pas à la bascule, puisque les deux
côtés portent l'identité. Elle casse quand le contact n'est **pas là** — et ça, ça arrive
déjà.)*

**Le défaut d'aujourd'hui.** `app_contact_current` ne porte que le **périmètre éligible**
— **61 984** contacts au 23/09, pas les 356 000 de l'app — et ce périmètre **rétrécit
chaque nuit** (`elargir_perimetre_console.py`). Un contact qui en sort pendant que sa saisie
attend voit **cette saisie abandonnée en silence**. C'est le contraire de la règle C.1' :
*une saisie ne se perd jamais*.

> **FAIT le 23/09** : la sonde passe en `LEFT JOIN LATERAL`, accepte **les deux numéros**, et
> **nomme la cause** — `en_attente_du_numero` *(normal, se résout seul)* contre
> `contact_absent_de_l_index` *(anormal, il faut un humain)*.
> **Preuve** : sur une saisie dont le contact est absent, l'ancienne forme voyait
> **0 ligne**, la nouvelle en voit **1**. Droits conservés *(`CREATE OR REPLACE`, colonne
> ajoutée en fin)*. **0 ligne aujourd'hui** — pas de fausse alerte.

---

**C-3 · La table de traduction se refuse elle-même**
`phase2/identite/descendre_correspondance_contacts.py:67`, `:88`, `:112-115`

La vue `app_v_correspondance_identite_cible` ne rend aujourd'hui **aucune ligne**
*(les contacts d'essai ont été supprimés)*. Après la bascule elle en rend **61 984** — tout
le périmètre éligible. Or :

```python
adresse = f"...&limit=10000"     # tronque silencieusement
PLAFOND = 5000                   # -> "REFUS", return 3
```

Et l'étape est **non bloquante** dans le run (`run_full_pipeline.ps1:438`) : le build tourne
quand même avec la correspondance de la veille => **la couche entière repart en numéros
Hektor**, en **recalculant les empreintes** au passage.

> **FAIT le 23/09.** Trois gestes, parce qu'il y avait trois défauts :
>
> **① Pagination.** PostgREST plafonne ses réponses : `limit=10000` rendait **une page**
> et se taisait. On lit page par page, **avec un tri stable** — une pagination sans ordre
> n'en est pas une.
>
> **② Le plafond devient un contrôle de FORME.** On ne répare pas un plafond en
> l'augmentant : **si un parc entier devient normal, un dérapage aussi**. Le nouveau
> contrôle refuse ce qui est *incohérent* — une identité hors plage, un numéro Hektor dans
> la nôtre, **deux identités qui visent le même numéro** *(le défaut du 21/09 vu de
> l'autre bout)*, une identité qui en vise deux. Ça tient à n'importe quel volume.
>
> **③ L'arrêt est placé dans le BUILD, pas dans le run.** Rendre l'étape bloquante tuerait
> le run pour un hoquet Supabase un soir ordinaire. La règle s'arme toute seule :
> **si la couche porte déjà des identités à nous et que la correspondance est vide,
> le build s'arrête.** Aujourd'hui : 0 identité dans la plage ⇒ **dormante**.
>
> **16 contrôles** dans `phase2/checks/test_c3_correspondance.py`, hors ligne.
> *(Au passage : le chemin inverse parcourait toute la correspondance à chaque appel —
> 61 984 parcours de 61 984 entrées le jour J. C'est une table maintenant.)*

---

**C-4 · Le run demanderait la suppression de tout le parc**
`phase2/sync/push_contacts_to_supabase.py:229-244`, `:753-758`

`app_contact_supabase_push_state` (**154 683 lignes**, jamais vidée) garde les `row_key` de
la veille. La nuit de la bascule, **aucune** ne se retrouve => le run demande à Supabase la
suppression de la totalité des contacts et des relations, puis les ré-insère.
~520 000 suppressions + 520 000 insertions — **exactement le scénario qui a saturé Supabase
le 22/08**.

**Ce qui n'arrivera PAS**, vérifié : **aucune clé étrangère** ne pointe vers ces tables,
donc **pas de cascade**. Et les cibles Hektor survivent — le déclencheur
`app_contact_remplir_cible` n'écrit **que si la case est vide**, il n'écrase jamais, et la
cible voyage dans l'envoi depuis L4-c ④.

**Le compte exact** *(les recherches sont épargnées par le nom figé)* :

```
app_contact_relation_current   81 315   la cle est un calcul SUR le numero -> change
app_contact_current            61 984   la cle EST le numero              -> change
app_contact_search_current     11 384   nom fige                          -> NE CHANGE PAS
                              ────────
                              143 299 cles declarees disparues d'un coup
```

Et **la suppression passe avant la repose** *(ligne 757 puis 765)* : il y a un moment où les
contacts et les relations **ne sont plus dans Supabase**.

> **Le geste de la fenêtre** : `--reset-push-state` avant le premier push post-bascule. Plus
> aucune clé ancienne, donc **rien ne paraît disparu**, donc **aucune suppression**.

**Et le garde-fou mort — FAIT le 23/09.** `delete_contacts_except_dirty` existait depuis le
21/09, testé par `test_dirty_guards.py`, **vert à chaque fois, et appelé nulle part**.

> ⚠ **Le trou n'était pas où je l'avais dit.** Dans le run de nuit, un contact né dans
> l'app **ne peut pas** être supprimé : il n'a jamais été envoyé par le serveur, donc il
> n'est pas dans la mémoire d'envoi, donc rien ne le déclare disparu.
>
> **Le trou est dans le rafraîchissement CIBLÉ** — celui que le worker appelle pour un seul
> contact. Un contact né dans l'app et rafraîchi **avant** que Hektor le connaisse n'est ni
> dans la repose ni « dirty » : il tombait dans `to_delete`, **et Supabase est son seul
> exemplaire**. Ses **relations et ses recherches** aussi — épargner la fiche et effacer ses
> relations ne vaut rien.
>
> Le garde-fou est **branché là**, plus un second verrou local, gratuit, sur le run de nuit.
> Et l'**ordre** des trois lignes qui calculent les disparues est désormais **écrit comme une
> protection** : si le calcul passait après le filtre des changements, le mode `update`
> déclarerait disparu **tout ce qui n'a pas changé**, c'est-à-dire le parc.
>
> **11 contrôles** (`phase2/checks/test_c4_suppressions.py`), dont **deux éprouvés en échec
> sur la version d'avant**. Vérifier qu'une fonction marche ne dit rien de savoir si
> quelqu'un l'appelle : c'est un contrôle de **branchement** qu'il fallait.
> Dry-run avec les options réelles du run de nuit : **`to_delete: 0` partout**.

---

**C-5 · Le registre d'identité se dédoublerait**
`phase2/identite/registre_contacts.py:43-52`

`app_contact` (**356 156 lignes**) accumule, avec `UNIQUE(hektor_contact_id)`. Elle se
nourrit de `app_contact_current`. Après la bascule, chaque contact arrive sous un numéro que
la table ne connaît pas => **une seconde ligne, donc un second `app_contact_id`, pour chaque
personne**. La série d'identité double.

> **Correctif** : traduire `app_contact.hektor_contact_id` **dans la même fenêtre** que la
> bascule — les 356 156 lignes, `app_contact_id` étant déjà rempli à 100 %.

---

**C-6 · Le miroir se ferait polluer par nos propres numéros**
`phase2/sync/sync_active_searches.py:45-62`, `:234-247` · `normalize_source.py:1068-1084`

La liste des recherches actives est tirée de **notre** couche, puis envoyée telle quelle à
Hektor (`ContactById`) **et** à `normalize_source --contact-id`. Or :

```python
for contact_id in requested_ids:
    item = listing_items.get(contact_id, {"id": contact_id})
    upsert_contact_from_sources(...)   # INSERT INTO hektor_contact
```

**Un numéro d'app inconnu de Hektor est INSÉRÉ dans le miroir comme s'il était un contact
Hektor**, champs vides. Le miroir — « une copie de Hektor, pour toujours » — se met à
contenir nos numéros, et le run suivant les relit comme des contacts réels. Hektor répond
404, et ces numéros entrent en **liste noire** (`sync_contact_detail_skip`), lue par
`marquer_contacts_disparus`.
Même trou dans `refresh_contact_inproc.py:33-53` et `scheduled/run_recherches_actives.ps1`.

> **FAIT le 23/09.** Deux gestes, à deux hauteurs différentes :
>
> **① Un verrou à la PORTE du miroir** (`upsert_contact_from_sources`). C'est la seule
> entrée de `hektor_contact`, donc le seul endroit qui tienne **quel que soit le chemin**.
> Il refuse, il le dit, et il ne lève pas.
>
> **② Les listes cessent de mélanger deux langues.** C'était le défaut de fond :
> `sync_active_searches` donnait **une seule liste** à trois étapes dont deux parlent la
> langue de Hektor *(l'API, le miroir)* et une la nôtre *(le push)*. Idem dans
> `refresh_contact_inproc`, où **un seul numéro** servait à quatre étapes — et c'est celui
> que le worker appelle **chaque fois qu'on ouvre une fiche contact**.
>
> **Non-régression mesurée sur la vraie base** : ancienne liste **3 970**, nouvelle
> **3 970**, *identiques*. **13 contrôles** (`phase2/checks/test_c6_miroir_propre.py`),
> dont **trois éprouvés en échec sur la version d'avant**.

---

**C-7 · L'espace client se viderait, et ré-enverrait ce qui a été refusé**
`backend/app/services/espace_client.py:226-231`, `:289-300`, `:537-653`, `:665-695`
`backend/app/services/rapprochement_sender.py:81-102`

Une **seule** valeur sert à interroger `app_email_envoi`, `app_bien_acquereur_statut`,
`app_espace_visite_request` (figées) **et** `app_contacts_current`,
`app_contact_search_current` (reconstruites). Quelle que soit la valeur choisie, **une moitié
rend zéro ligne**.

Le plus grave n'est pas l'écran vide : `_fresh_filter` ne trouvant plus aucun statut
bloquant, **tous les biens repassent pour « frais »** => **ré-envoi par email de biens déjà
proposés, écartés ou refusés**. Chez le client.

> **Correctif** : C-13 (traduction des tables figées) règle tout ce bloc d'un coup. En
> attendant, **couper l'envoi automatique** pendant la fenêtre de bascule.

---

**C-8 · Les jetons déjà partis — 60 jours de portée**
`backend/app/services/email_tokens.py:136-145` · `rapprochement_email.py:611-628`

Le numéro de contact est **signé dans un jeton HMAC** et **encodé dans l'URL** de chaque bien
de chaque email. Durée : **60 jours**. Ces URL sont déjà chez les clients, non rattrapables.
`identite_depuis_jeton` les traduit bien — mais la valeur traduite sert ensuite à interroger
`app_email_envoi`, qui n'a pas basculé (C-7).

> **Correctif** : C-13 rend la traduction cohérente. **Aucune action n'est possible sur les
> URL déjà parties** — c'est la raison pour laquelle C-13 doit être fait, et pas contourné.

---

**C-9 · Des numéros à nous partiraient chez Hektor**
`console_job_worker.js:11375`, `:11742` (mandants) · `:11366-11367`, `:11733`, `:11736`
(notaires)

`tx.mandantsVoulus` et `tx.notary` partent **bruts** dans la requête HTTP. Le front fournit
l'identité (`App.tsx:16055`, `:18814`, `:18835`). Au mieux Hektor ignore ; **au pire il
désignera la fiche d'un tiers le jour où ses numéros atteindront cette plage**.

Effet immédiat : `constaterLesPersonnes` (`:13073-13085`) compare des mandants **non
traduits** à ce que Hektor relit => **tous les mandants comptés comme refusés**, bandeau
d'écart faux sur chaque transaction.

> **FAIT le 23/09.** Pas six rustines — **une traduction du `tx` entier, en place**, juste
> après sa construction, aux **deux** endroits qui en bâtissent un.
>
> C'est le seul point où les trois valeurs se rencontrent. Corriger les six endroits
> d'envoi aurait laissé `personnes_posees` faux — donc **le bandeau d'écart faux** — et
> le prochain envoi ajouté serait revenu à en oublier un.
>
> **4 contrôles ajoutés** à `Console/test_porte_contacts.js` *(21 au total)*, dont un sur
> **l'ordre** : la traduction doit venir **avant** les envois. *C'est exactement la forme du
> défaut C-1 — le bon geste, au mauvais moment.* **Les 4 échouent sur la version d'avant.**
>
> ⚠ **Ce que ces contrôles ne font pas** : ils lisent le texte du code, ils n'exécutent pas
> le worker *(19 000 lignes, non importable isolément)*. La forme est prouvée, le
> comportement ne l'est pas.

---

**C-10 · Le ménage d'un contact supprimé ne supprimerait plus rien**
`console_job_worker.js:16837-16868`, `:16841-16854`

La même valeur purge des tables figées **et** reconstruites : la moitié du ménage échoue. Et
les tables purgées **par `contact_search_key`** (`app_rapprochement`,
`app_rapprochement_score_history`, `app_rapprochement_search_state`,
`app_relance_rapprochement`, `app_notification`) reçoivent la clé lue dans la couche
reconstruite => **zéro ligne supprimée**, le correctif C.4 du 20/09 annulé.

> **Correctif** : C-13. *(La protection du nom figé, §1, limite la casse — mais seulement si
> les 5 lignes manquantes sont comblées.)*

---

**C-11 · Deux écrans écriraient deux numéros pour la même personne**
`backend/app/services/email_tracking.py:111-121`

`RapprochementMandat.tsx:177` fournit un numéro lu dans `app_rapprochement` (figée) ;
`RechercheAcquereur.tsx:676` fournit un numéro lu dans `app_contacts_current` (reconstruite).
**Même table, même personne, deux numéros.**

> **Correctif** : que les deux écrans lisent la même source. C-13 la rend unique.

---

**C-12 · La photo « fraîche » se lit au mauvais endroit**
`console_job_worker.js:15939-15949`, appelée en `:16250`

Le commentaire dit « la photo FRAÎCHE se lit chez Hektor, donc avec la cible » — mais la
fonction lit **notre** table `app_contact_search_current`, avec la cible. Après la bascule :
`fresh = null` => `recherche_introuvable_cote_hektor` => **toute édition de recherche bloquée
en conflit**.

> **FAIT le 23/09.** Les deux photos se lisent avec l'identité. Et le **paramètre s'appelait
> `contactId`** — un nom qui mentait, puisque la fonction lit *notre* table : renommé.
> *Un nom ambigu a suffi à ce qu'on lui passe la cible pendant un jour.*
>
> **⚠ ET C-12 EN CACHAIT UN SECOND, que j'avais créé moi-même une heure plus tôt.** C-6 a
> donné à `refresh_contact_inproc.py` de quoi traduire seul : **son contrat a changé**, il
> prend désormais l'identité. Or **ses deux appelants du worker lui passaient encore la
> cible**. Invisible aujourd'hui, faux le jour J. *Un contrat qui change sans que ses
> appelants bougent, c'est une panne qui attend son jour.*
>
> **23 contrôles** au total, les 2 nouveaux **éprouvés en échec** sur la version d'avant.

---

**C-13 · LA correction qui en règle dix : traduire les tables figées**

**28 tables** Supabase et **35 fonctions et vues** cousent le reconstruit au figé. La
traduction est mécanique — `hektor_contact_id := app_contact_id` — puisque la doublure est
déjà posée.

```
traduisibles        59 971 lignes
NE PAS traduire     app_console_deleted_contact_log  (12)  <- c'est un JOURNAL
                    app_contact_consent                    <- trace RGPD datee
non traduisibles    ~77 lignes  (contacts absents de l'app, poids mort deja)
```

Deux colonnes que mes `grep` ne pouvaient pas trouver, et qui portent pourtant une identité
de contact : **`app_affaire_personne_ecart.contact_id`** et
**`app_contact_duplicate_group_current.primary_candidate_hektor_contact_id`**.

> **Correctif** : un seul patch SQL, dans la fenêtre de bascule, avant le premier build.

---

### Gênants — l'app marche, mais ment

| # | où | ce qui casse |
|---|---|---|
| G-1 | `App.tsx:32505-32535` | **la même personne deux fois** dans les invités d'un RDV, une fois avec email, une fois sans |
| G-2 | `App.tsx:20946` + `api.ts:2429-2431` | **taper le numéro lu dans Hektor ne trouve plus rien** ; le placeholder promet pourtant « ou un ID contact » |
| G-3 | `api.ts:5600-5617` + `App.tsx:15734` | la **répartition de commission** n'est plus posée — échec avalé par `.catch(() => null)` |
| G-4 | `App.tsx:15067-15085` | le **même acquéreur ajouté deux fois**, le retrait n'en enlève qu'un |
| G-5 | `api.ts:8476-8516` | les invités perdent **email et téléphone**, remplacés par « Contact 10605453 » |
| G-6 | `App.tsx:6839-6841` | `detailContactDirectoryId` retient le **premier candidat numérique** — il ne sait pas de quelle série il parle |
| G-7 | `api.ts:8368-8386` | `MandantContactSearchOption` **n'expose pas `hektor_target_id`** alors que la requête le ramène |
| G-8 | 12 sites du front | les garde-fous `/^\d+$/` « ID Hektor numérique requis » **ne distinguent pas les deux séries** — ils ne protègent de rien |
| G-9 | `marquer_contacts_disparus.py:48-78` | lit le miroir, écrit dans l'app => **0 ligne marquée**, et affiche « 0 nouvellement marquée » |
| G-10 | `affaire_ledger.py:685-693`, `:786` | le **lien vente <-> acheteur cesse d'être créé** — celui-là même qu'on avait doublé pour la coupure |
| G-11 | `elargir_perimetre_console.py:96-204` | **0 contact marqué éligible** => les 1 738 personnes citées par Hektor **ressortent de l'annuaire la nuit même** |
| G-12 | `contacts_app_seuls.py:71-73` | **tout Supabase paraît « né dans l'app »** si les deux côtés ne basculent pas ensemble |
| G-13 | `build_contacts_layer.py:645-684` | `resoudre_menages` traduit **dans le mauvais sens** => nom de la porteuse vide |
| G-14 | `build_contacts_layer.py:738 + 787` | filtre posé en numéros miroir, comparé à l'identité => **le rafraîchissement ciblé jette tout** |
| G-15 | `comparer_doublures.py:79-85`, `:163-165` · `check_gti_health.py:1945` | les **sondes de doublure** comptent 100 % d'écart : fausse alarme, puis alarme aveugle |
| G-16 | `test_substitution_identite.py:61-66` | le témoin ne se trouve plus => **l'assertion est sautée en silence**, le test passe au vert sans rien tester |
| G-17 | `google_calendar_event_link_service.py:105-110` | les **9 liens d'agenda** ne remontent plus, ni par colonne ni par JSON |
| G-18 | `email_tracking.py:299-314` | réconciliation des relances muette => **doublons de relance** |
| G-19 | `App.tsx:36936`, `:36961`, `:37002`, `:31669` | `'invite'`, `'agenda_global'` ou **une adresse email** posées dans un champ de numéro de contact |

---

## 3. Ce qui est protégé — vérifié, pas supposé

- **456 000 lignes sous `contact_search_key`** : le nom figé les tient, `app_contact_id` est
  rempli sur **77 083 / 77 088** lignes du registre. *(5 à combler.)*
- **`app_affaire_ledger`** (30 995 transactions) : relie **par la doublure** => bascule seul.
- **Aucun numéro de contact** dans le `localStorage`, une URL d'écran, un QR code, un
  `mailto`, un document imprimé. Ni le bon de visite, ni le mandat n'en portent.
- **Rien en file** : `app_console_job` **0 en attente**, `app_contact_pending` **0**,
  `app_search_pending` **0**, `app_contact_override` **0 ligne**.
  => **tout le chapitre « travaux créés avant, consommés après » disparaît si l'on bascule
  file vide.** C'est une règle de procédure, pas un développement.
- `App.tsx:7920-7947` (`cibleHektorDuContact`) : la seule fonction du front qui connaît les
  deux séries, et elle est correcte.
- `enqueue_delete_contacts.py:125-136` : le seul script de `phase2/` qui lit déjà
  `hektor_target_id`. Ce chemin est prêt.

---

## 4. Les huit points non mesurés — TRANCHÉS le 23/09

| # | question | réponse mesurée |
|---|---|---|
| **1** | la description des événements **Google Agenda** porte `Contact Hektor : <n>` | **CORRIGÉ.** Le front écrivait **l'identité** sous une étiquette qui dit « Hektor ». Il écrit désormais la **cible**, et n'écrit **rien** plutôt qu'un numéro faux. Les **9** déjà chez Google sont justes *(cible = identité aujourd'hui)* et intouchables |
| **2** | `app_affaire_ledger.hektor_acquereur_id` : Hektor ou identité ? | **reste Hektor** — c'est la trace brute de ce que Hektor a dit. Le doublage s'est fait en **ajoutant** `app_contact_id` à côté. ⚠ **Et cette question a fait tomber C-5** : voir ci-dessous |
| **3** | les tables `*_provisional` | **2** lignes contact, **2** recherche, **0** ailleurs. Le lien du contact porte désormais **l'identité** *(c'est l'écran qui le relit, et l'écran ne connaît que nos numéros)*. Le chemin voisin « créer un mandant » **ne porte aucune identité d'app** : ce n'est pas une incohérence, c'est un manque à combler dans **C.9** |
| **4** | `app_contact_id_propager`, la fonction Postgres non lue | **elle survit.** Elle ne remplit que les **cases vides**, par auto-jointure : après la bascule les lignes neuves portent l'identité des deux côtés. Résidu à rattraper : **37** rapprochements + **40** compteurs *(contacts absents de l'app, poids mort)* + **1** lien d'agenda. La lancer **dans la fenêtre** suffit — c'était déjà l'étape (1) |
| **5** | 5 scripts jamais ouverts | **4 n'ont AUCUNE** occurrence de contact *(`reappliquer_saisies_app`, `magasin_affaire_app`, `magasin_mandat_app`, `quality_checks`)*. Le 5ᵉ, `backfill_couple_contact`, travaille **entièrement dans le miroir** — numéro Hektor des deux côtés — et **ne figure pas au run quotidien** |
| **6** | la seconde fonction de hachage, `build_contacts_layer.py:237` | `short_hash` porte sur **l'email, le téléphone et une clé normalisée**. **Jamais un numéro de contact** |
| **7** | `app_contact_audit_run` | **des comptes et des dates**, rien d'autre |
| **8** | **RDV et visites** comme objet propre | **9 tables** balayées. **Deux seulement** portent un contact — `app_espace_visite_request` *(3)* et `app_google_calendar_event_link` *(11)* — et **les deux étaient déjà comptées**. Les sept autres, dont `app_appointment_public_link` *(2 222 lignes)*, n'en portent **aucun**. Les RDV n'apportent rien de neuf à la bascule |

### ⚠ Ce que la question 2 a fait tomber : **C-5 était faux**

Le plan disait « traduire `app_contact.hektor_contact_id` en identité ». Mesure du jour :

```
app_contact (le registre)   app_contact_id . hektor_contact_id
                            created_at . updated_at . absent_depuis
```

**Aucune colonne pour la cible.** Traduire en place **effacerait le numéro de Hektor du
registre** — et avec lui la seule correspondance locale dont `affaire_ledger` se sert pour
relier une **vente à son acheteur**. C'est-à-dire le lien que tu avais fait doubler le 01/09
*précisément* parce qu'il était le seul non doublé du projet.

> **FAIT** : `hektor_target_id` posé sur `app_contact`, **356 156 / 356 156** remplis.
> Même geste que L4-c ④ côté couche — la couche l'avait, le registre ne l'a jamais eu.

### Et les 5 lignes à combler : **il n'y en a pas**

Les **5** lignes de `app_search_registry` sans doublure appartiennent à des contacts qui
**n'existent plus** — `605093/94/95` *(31/08)* et les deux témoins du 21/09. Leurs clés figées
sont référencées **nulle part** *(0 dans les six tables qui pendent dessus)*.
➡ **L'étape (1) de la procédure est annulée.**

---

## 5. L'ordre, puisque c'est lui qui décide de tout

```
(1)  lancer app_contact_id_propager  -> rattrape 37 + 40 + 1
(2)  vider la file (deja vide) + ARRETER les 4 services
(3)  SAUVEGARDE locale (VACUUM INTO) + compte de chaque table
(4)  C-1 C-2 C-3 C-6 C-9 C-12 : le code, DORMANT, deploye avant
(5)  patch SQL : bascule app_contact_current + C-13 les 28 tables
(6)  traduire app_contact local (356 156)                          [C-5]
(7)  descendre la correspondance  -> 61 984 paires                 [C-3]
(8)  push_contacts --reset-push-state --include-archived-searches  [C-4]
(9)  build_contacts_layer
(10) redemarrer les services, verifier : rapprochements visibles,
     sondes a zero, cibles a 100 %, un envoi d'espace client reel
```

**(5) à (9) dans la même fenêtre.** Entre (5) et (9) la base est incohérente.

**Écrire chaque commande en entier et la MONTRER avant de l'exécuter** *(règle posée le
22/09 après la suppression accidentelle de 7 201 recherches, causée par un drapeau oublié)*.

**RETOUR ARRIÈRE** : la sauvegarde (3), plus la traduction inverse — `app_contact_id` ->
l'ancien numéro, lisible dans `hektor_target_id`.
