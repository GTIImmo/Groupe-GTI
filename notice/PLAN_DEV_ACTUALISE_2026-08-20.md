# Plan de développement actualisé — 20/08/2026

Remplace le plan du 18/08. Établi après quatre audits mesurés :
identifiants (19/08), workers (20/08), diffusion (20/08), contacts et modales (20/08).

---

## CE QUI EST FAIT

| | | Commit |
|---|---|---|
| Un dossier ne perd jamais son numéro | on marque `absent_depuis`, on ne supprime plus | `dc45c62` |
| Le correctif anti-fantôme couvre 21 tables au lieu de 5 | ~600 annonces abîmées depuis juin | `aa8a374` |
| **Les identifiants d'annonce sont alignés** | 13 215 / 13 215, vérifié après un run complet | `99e262f` |
| Pipeline et surveillance fiabilisés | chauffage non bloquant, sauvegarde surveillée, 4 sentinelles en critique | 5 commits |

---

## LE CHANTIER D'IDENTITÉ — trois objets, un seul dessin

**Le dessin, valable pour les trois :**

```
   case 1 : un numero A TOI        <- la cle, remplie des la creation, jamais remplacee
   case 2 : le numero de Hektor    <- simple reference, vide en attendant son retour
```

**Arbitrage Frédéric (20/08) : pas de solution mixte.** Un objet ne peut pas avoir une case pour
les anciens et deux pour les nouveaux. **Tout le parc bascule d'un coup, ou rien.**

**Deuxième arbitrage : on double ET on bascule dans la foulée.** Jamais de numéro « secondaire »
généré mais inutilisé — c'est ce qui a laissé `app_dossier_id` dériver de mars à juin sans que
personne le voie. *Ce qui est utilisé est ce qui est vérifié.*

### L'ordre, établi par l'audit des points d'appel (20/08)

| Ordre | Objet | Volume | Points d'appel ambigus | Risque |
|---|---|---|---|---|
| **1** | **Transactions** | ≈ 29 100 | **0 sur 12** — jamais envoyés au worker | **le plus faible** |
| — | *Annonces* | *341 394* | *3 sur 56, dont 2 `null`* | *fait le 19/08* |
| **2** | **Contacts** | ≈ 186 500 | **3 réels**, ≈ 10 fonctions à relire | **le plus élevé** |
| **3** | **Recherches** *(3 961)* | ≈ 1 300 rapprochements à rebrancher | clé = **hachage du contenu**, elle bouge seule | **cas à part — voir le dossier ci-dessous** |

> **Pourquoi les contacts sont les plus risqués** : ils n'ont qu'une seule colonne, donc **aucune
> couche n'a jamais eu a faire la distinction**. Mesure du 20/08 :
>
> | | Front | Fonctions de la base | Worker |
> |---|---|---|---|
> | Annonces | 53 explicites / 56 | explicites | lit un champ nomme |
> | **Contacts** | **3 ambigus**, ~10 fonctions | **6 fonctions ambigues** | lit un champ nomme |
> | Transactions | 12 / 12 explicites | jamais envoyees | ne les connait pas |
>
> Les six fonctions concernees : `app_console_create_update_contact_job`,
> `..._delete_contact_job`, `..._contact_search_job`, `..._update_contact_search_job`,
> `..._delete_contact_search_job`, `..._update_mandant_contact_job` — toutes ecrivent
> `hektor_contact_id` a partir de `target_contact_id`.

### La méthode, par objet — jamais deux à la fois

```
   0. AUDIT COMPLET DES POINTS D'APPEL, sur les TROIS couches -- prealable absolu.
      Partout ou un identifiant part vers un worker, il doit etre lu dans la
      colonne NOMMEE, jamais dans "la cle".
        a) le front        : modales, api.ts, App.tsx
        b) les fonctions de la base : les 14 app_console_create_*_job
        c) le worker       : il lit deja un champ nomme -> a confirmer, pas a modifier
      Puis renommer ce qui est ambigu : input.contactId -> input.hektorContactId.
      Aucun effet fonctionnel aujourd'hui, verifie par la compilation.
   1. ajouter la case (Supabase + local, parent et tables enfants)
   2. renumeroter le stock  : table de correspondance conservee, essai a blanc
                              qui annule tout, transaction unique, verification chiffree
   3. basculer la cle DANS LA FOULEE : les jointures lisent la nouvelle case,
      ET LA CASE HEKTOR DEVIENT FACULTATIVE -> c'est CE geste qui autorise
      la creation depuis l'app. Il est impossible avant l'etape 3, puisque
      la case Hektor est encore la cle.
   4. poser la sentinelle   : doublons = 0, orphelins = 0, ecart local/Supabase = 0
   5. le worker NE CHANGE PAS : il lit toujours le champ nomme hektor_*_id
```

**Preuve avant la masse** : basculer un seul objet, le modifier depuis l'app, vérifier que le
worker aboutit et que Hektor a bien reçu. Dix annonces avaient servi de test le 19/08 avant les
12 162 — aucun orphelin créé.

**Garde-fou pendant la transition** : la RPC de création de travail **refuse** de créer un travail
Hektor si la case Hektor est vide — elle le met en attente. Un travail ne peut donc pas partir
avec un mauvais numéro : il ne part pas du tout.

---

## LE DOSSIER RECHERCHES — enquête du 20/08, à lire avant d'y toucher

**Trois facettes distinctes**, identifiées par `RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md` :

| | Facette | État |
|---|---|---|
| **A** | **Clé instable** — `contact_search_key` hache le **contenu éditable** | ❌ jamais corrigée |
| **B** | **Écrasement** — l'édition renvoie TOUTE la recherche depuis une copie peut-être périmée | ❌ jamais corrigée |
| **C** | **Angle mort `date_maj`** — éditer une recherche dans Hektor ne bump pas la date du contact | ✅ **corrigée le 20/06** |

**C a été corrigée par un run dédié** : `scheduled/run_recherches_actives.ps1` ->
`sync_active_searches.py`, **03:00 chaque nuit**, ~3 590 contacts, sans filtre `date_maj`.

> **Le noeud : la correction de C amplifie A.**
> Avant le 20/06, une édition faite dans Hektor était invisible -> la clé ne bougeait pas.
> Depuis, elle est détectée -> **la clé bouge** -> l'historique se détache.
> **Orphelins : 327 le 19/06 -> 1 332 le 20/08. Multiplié par quatre en deux mois.**

**Ce n'est PAS voulu — vérifié le 20/08 :**

- **6 clés du projet sur 7 hachent une identité** (relation, registre, contact, dossier, doublons).
  La recherche est **la seule** à hacher du contenu.
- **Deux consommateurs s'en protègent déjà en production** : `app_email_envoi.search_index`
  (migration du 17/06 : *« la contact_search_key change à l'édition »*) et
  `espace_client._load_search_for_envoi` (3 niveaux, *« on ne s'y fie qu'en tout dernier recours »*).
  **Le contrat de fait est déjà : ne pas se fier à cette clé.**
- **Personne ne dépend de son instabilité.** Le rapprochement est le seul à ne pas se protéger.

**Pourquoi ça n'a jamais été corrigé** : le correctif proposé en juin était `hash(contact_id, index)`.
Il est **mauvais** — l'`index` est la **position**, qui bouge à chaque suppression et n'est pas
alignée entre l'API et le grattage Console. **La bonne réponse est un identifiant propre à l'app.**

**Gravité** : le moteur de rapprochement est **app-only par décision métier**
(`NOTE_MOTEUR_RAPPROCHEMENT_ACQUEREUR_2026-06-14.md`). Ce qui se détache — propositions, retours
acquéreur, relances, emails — **n'existe nulle part ailleurs**. Hektor ne peut rien reconstruire.

**Vérifié en direct le 20/08**, contact 604020 : édition à 14:36 -> clé inchangée, 41
rapprochements recalculés ; retour de Hektor à 14:48:07 -> **nouvelle clé**, les 41 deviennent
orphelins. Et **aucune des 4 fonctions** qui suppriment des rapprochements ne nettoie par absence.

**Ordre recommandé** : le ménage des orphelins d'abord (une requête + un cron, règle le symptôme),
la clé propre ensuite (avec le chantier d'identité), l'écrasement (B) quand on touchera au chemin
d'écriture. **Ne pas ajouter de garde-fou sur la suppression** — décision Frédéric du 18/08 : il
ferait échouer les cas où le repli `list[0]` tombe juste.

---

## LES TROIS DÉPENDANCES RÉELLES À HEKTOR

| | Ce que Hektor fournit | Comment s'en passer | Délai |
|---|---|---|---|
| **1** | Le numéro de mandat | registre en propre | du code |
| **2** | La signature (ImmoSign) | Yousign | un contrat |
| **3** | **La diffusion portails** | contrats directs ou diffuseur | **contrat + migration commerciale** |

> **Arbitrage Frédéric (20/08) : les contrats démarrent à la fin** (chantier 5), pour préparer la
> coupure. Conséquence assumée : la date sera fixée par leur délai, qui ne commencera à courir
> qu'après le développement. La reprise des 350 annonces en ligne est le seul délai non maîtrisé.

---

## CHANTIER 1 — Maintenant, sans dépendance

| | Quoi | Pourquoi maintenant |
|---|---|---|
| **1.1** | **Un échec de worker prévient l'utilisateur et le monitoring** | **indispensable** : un envoi raté laisse une annonce en ligne au mauvais prix |
| **1.2** | **Les recherches acquéreur sont enregistrées** dans l'app | seul endroit où une saisie se perd |
| **1.3** | Le numéro Hektor d'**annonce** a le droit d'être vide | ouvre la création app-first d'annonce |
| **1.4** | **Identité des transactions** — ajouter la case, renuméroter ≈ 29 100 lignes, **puis la case Hektor a le droit d'être vide** | **le plus sûr des trois** : 0 point d'appel ambigu. Débloque la modale de statut, qui crée offres, compromis et ventes |
| **1.5** | **Identité des contacts** — renommage préalable, ajouter la case, renuméroter ≈ 186 500 lignes, **puis la case Hektor a le droit d'être vide** | débloque la modale d'ajout : contact + recherche + mandant écrits d'un coup. **Demande une demi-journée de relecture avant** |
| **1.6** | ~~Reprendre `numero_dossier`~~ **-> reporte au jour J** : comprendre la règle de numérotation Hektor et la continuer | référence métier lisible dans 11 tables — **personne ne la fabrique après la coupure** |
| **1.7** | ~~Annuaire négociateurs~~ **-> reporte au jour J** : le worker a besoin de l'`idUser` Hektor pour s'impersonner — 40 + 19, présents dans 14 tables | l'affectation doit survivre sans Hektor |

---

## CHANTIER 2 — Le cœur : Hektor confirme, il n'écrase plus

| | Quoi |
|---|---|
| **2.1** | Écrire la règle : les trois cas d'écart *(envoi pas parti / envoi raté / modifié dans Hektor)* |
| **2.2** | La tolérance de comparaison — la traduction des valeurs existe déjà (`resolveHektorSelectValue`) |
| **2.3** | Brancher au retour du worker *(`push_single_annonce_to_supabase.py:573`)* |
| **2.4** | Même règle sur l'import de nuit |

> **Le garde-fou existe déjà**, côté annonce et côté contact (`base_snapshot` + comparaison
> `date_maj`). Aujourd'hui, en cas d'écart, **Hektor gagne**. La règle 2 **inverse le verdict** :
> l'app garde sa valeur et signale. C'est une modification, pas une construction.

**Puis, dans la foulée :**

| | |
|---|---|
| **2.5** | **Le calque d'annonce disparaît** — il n'existe qu'à un seul endroit : l'édition de champs |
| **2.6** | La barrière : un travail sans numéro Hektor **attend** au lieu d'échouer |

---

## CHANTIER 3 — Appliquer le principe aux 16 workers

**Écrire chez soi d'abord, envoyer ensuite, confirmer au retour.**

| Ordre | Workers |
|---|---|
| **3.1** | Les 3 recherches *(ajouter / modifier / supprimer)* |
| **3.2** | **Statut + affaire** *(offre, compromis, vente)* — le geste le plus riche |
| **3.3** | Archiver / désarchiver / supprimer |
| **3.4** | **Créer un contact, créer un mandant, rattacher** *(après 1.3)* |
| **3.5** | **Affectation du négociateur — en DERNIER** (impersonation du worker) |

**Correctifs à glisser dedans :**

- **3.6** — **Clé propre au registre des affaires** *(28 980 lignes, clé 100 % Hektor)*
- **3.7** — **Fiabiliser le mandat des transactions** : l'app doit toujours le fournir ; aujourd'hui
  le worker le devine dans le HTML de Hektor si elle ne le fait pas
- **3.8** — **La clé de recherche** : aujourd'hui un hachage du contenu, elle change à chaque
  édition — **1 270 rapprochements déjà orphelins**. C'est la seule clé structurellement fausse.
- **3.9** — **Ménage** : `app_contact_override` (vide, non écrite), `app_console_create_update_contact_job`
  (remplacée par l'optimiste), tables `_v1` vides

---

## CHANTIER 4 — La création part de l'app

| | Quoi | Dépend de |
|---|---|---|
| **4.1** | **L'annonce** : la création écrit la vraie fiche | 1.4 · 2.3 · 2.6 |
| **4.2** | **Le contact et le mandant** : idem | 1.3 · 2.3 |
| **4.3** | **La modale d'ajout de contact** écrit ses trois objets d'un coup : contact + recherche + relation mandant | 4.2 |
| **4.4** | Les workers deviennent invisibles | **quand l'avertissement d'échec aura fait ses preuves** |

---

## CHANTIER 4bis — Rapatrier les binaires *(à terminer AVANT la coupure)*

| | Quoi | Volume |
|---|---|---|
| **4bis.1** | **Les documents** — `hektor_document_id` pointe vers le stockage de Hektor | **40 493** |
| **4bis.2** | **Les photos** — `hektor_photo_id`, idem | **1 397** |

> Ce ne sont pas des identifiants métier, ce sont **des adresses**. Tant qu'ils pointent vers
> Hektor, ils pointent vers un serveur qui va s'éteindre. **Irréversible : ce qui n'est pas
> descendu avant est perdu.**

---

## CHANTIER 5 — Préparer la coupure : les trois contrats

| | Quoi | Nature |
|---|---|---|
| **5.1** | **Sortie des portails** : combien, chez qui, à quel prix, et **comment reprendre les 350 annonces en ligne sans trou de visibilité** | contrat + migration |
| **5.2** | **Yousign** — l'app ne sait pas *lancer* une signature | contrat + code court |
| **5.3** | **Registre de mandats en propre** — obligation légale, libère `numero_mandat` | code |

---

## CHANTIER 6 — Le jour J, une journée

| | |
|---|---|
| **6.1** | Le distributeur démarre à **100 000**, dans le couloir vide 25 000 → 1 000 000 |
| **6.2** | Le serveur remplit **les deux cases** : les 24 tables qui portent le numéro Hektor continuent sans le savoir |
| **6.3** | Le numéro est **imposé**, pas laissé au compteur local (à 5,25 millions) |
| **6.4** | On éteint l'aspirateur : pipeline, workers, Playwright, file de travaux |
| **6.5** | Les 3 PDF et les 4 workers internes **continuent tels quels** |

---

## LA RÈGLE DES IDENTIFIANTS

> **Pour chaque identifiant que Hektor fabrique, trois questions avant la coupure :**
> **1.** Qui le fabriquera après ? · **2.** Que deviennent les valeurs déjà émises ? · **3.** Qu'est-ce
> qui casse s'il est vide ?
>
> Annonces : répondu. Contacts et affaires : chantier 1. **`numero_dossier`, annuaire, binaires :
> nouvellement identifiés.** Détail : `AUDIT_TOUS_LES_IDENTIFIANTS_2026-08-20.md`.

---

## LES QUATRE RÈGLES

1. **Un numéro ne se perd jamais.** *(fait)*
2. **Hektor confirme, il n'écrase pas.**
3. **Une action a toujours une fin visible** — surtout quand elle rate.
4. **Tant que la diffusion passe par Hektor, Hektor doit rester à jour.**

---

## CE QUI RESTE NON MESURÉ

- **La lenteur du front** — la mesure F12 n'a jamais été faite.
- **Les 176 champs du grand bloc** — affichables et modifiables, non filtrables dans les listes.
- **La clé de recherche** — hachage du contenu, elle change à chaque édition : **1 270 rapprochements
  déjà orphelins**.
- **Le coût réel de l'identifiant contact** — quelles tables parmi les 21 qui portent le numéro Hektor.
