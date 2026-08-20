# Analyse — le renommage (5a) et la nouvelle clé de recherche

Date : 2026-08-20. **Lecture seule.** Demandée par Frédéric : *« je veux être sûr que le
renommage et ensuite la nouvelle clé ne vont pas empêcher mon app de fonctionner pour les
mises à jour de Hektor dans les deux sens, les rapprochements, les espaces clients, les
notifications… fais des tests. »*

Tout ce qui suit est **mesuré ou testé**, pas déduit.

---

# PARTIE 1 — Le renommage. **J'avais tort de le dire « sans risque ».**

J'avais annoncé : *« effet nul, vérifié par la compilation »*. **Les deux moitiés de cette
phrase sont fausses.** Trois tests le montrent.

### Test 1 — PostgreSQL refuse de renommer un paramètre

```sql
create or replace function zz_test(target_contact_id text) ...
create or replace function zz_test(hektor_contact_id text) ...
```
> `ERROR: cannot change name of input parameter "target_contact_id"`

**Il faut donc SUPPRIMER puis RECRÉER** chacune des 11 fonctions.

### Test 2 — l'appel se fait PAR LE NOM du paramètre

```sql
select zz_test(hektor_contact_id := 'abc')   -- avant renommage
```
> `ERROR: function zz_test(hektor_contact_id => unknown) does not exist`

C'est **exactement** l'erreur que renverrait l'app : PostgREST construit l'appel avec les noms
envoyés par le front. Un nom qui ne correspond plus = **la fonction n'existe pas**.

### Test 3 — la compilation ne vérifie RIEN

`apps/hektor-v1/src/lib/supabase.ts:19` :
```ts
createClient(url, anonKey, { … })     // <- sans le type généré de la base
```
Aucun schéma TypeScript généré n'existe dans le projet. `supabase.rpc('nom', { … })` accepte
donc **n'importe quel nom de paramètre**. **La vérification que je proposais ne vérifie rien.**

### Ce que la suppression détruit au passage

Les 11 fonctions sont **toutes `SECURITY DEFINER`** avec des droits explicites — et **deux
n'ont pas les mêmes** :

| Fonctions | Droits |
|---|---|
| Les 9 appelées par le front | `anon`, `authenticated`, `service_role` |
| `app_espace_edit_search_optimistic`, `app_espace_create_search_update_job` | **`service_role` seulement** |

`DROP` efface ces droits. Les redonner de travers, c'est soit casser l'espace client, soit
ouvrir à `anon` une fonction qui ne doit pas l'être.

### Les appelants réels

| Fonction | Appelée depuis |
|---|---|
| 9 fonctions | `apps/hektor-v1/src/lib/api.ts` uniquement |
| `app_espace_edit_search_optimistic` | `backend/app/services/espace_client.py:707` *(Render)* |
| `app_espace_create_search_update_job` | **aucun appelant — morte** |

### Conclusion de la partie 1

Le renommage n'est pas un geste interne : c'est un **changement de contrat** entre trois
machines déployées séparément — la base, le front (Vercel), le backend (Render). Entre la
suppression des fonctions et la mise en ligne du nouveau front, **toute édition de contact,
toute édition de recherche, toute suppression, toute création de mandant et tout
rafraîchissement échouent** — et échouent **silencieusement**, puisque rien ne les type.

**Deux chemins possibles :**

| | Comment | Fenêtre de casse |
|---|---|---|
| **Direct** | supprimer/recréer, redéployer front + backend dans la foulée | **quelques minutes** |
| **Par recouvrement** | créer les nouvelles fonctions **à côté**, migrer les appelants, supprimer les anciennes ensuite | **aucune** |

**Recommandé : par recouvrement**, ou bien **ne pas renommer seul du tout** et le faire au
moment de la bascule d'identité, quand le front doit changer de toute façon. Renommer seul
coûte un déploiement coordonné et ne rapporte que de la lisibilité.

---

# PARTIE 2 — La nouvelle clé de recherche, flux par flux

## 2.1 Sens montant : app → Hektor — **aucun risque, prouvé**

**La clé de recherche ne part JAMAIS chez Hektor.** Zéro occurrence de `contact_search_key`
ou `search_key` dans `Console/console_job_worker.js` (87 occurrences de `hektor_contact_id`,
mais aucune de la clé).

Le worker cible une recherche chez Hektor par **`idCritere`** (l'identifiant de Hektor) ou,
à défaut, par **`search_index`** — `console_job_worker.js:11443-11449`.

> **La clé est purement interne à l'app.** La changer ne peut rien casser côté Hektor.

## 2.2 Sens descendant : Hektor → app — **le seul vrai point dur**

**Un seul endroit au monde fabrique la clé** : `build_contacts_layer.py:827`.

```python
for index, search in enumerate(recherches):        # <- l'index est la POSITION dans la liste
    key_payload = {"contact_id": contact_id, "index": index, "search": search}
    search_key = stable_hash(key_payload)[:24]
```

Si la recherche reçoit un numéro à elle, l'import de nuit doit **reconnaître** une recherche
déjà connue au lieu de recalculer une empreinte. Avec quoi ?

**L'app ne stocke pas l'`idCritere` de Hektor** — vérifié : la table `app_contact_search_current`
ne porte aucune colonne d'identifiant Hektor de recherche. La seule poignée disponible est
donc **`(contact, index)`**.

### Le risque, mesuré

`(contact, index)` est **unique aujourd'hui** — 0 doublon sur 3 961. Mais l'index est une
**position** : si Hektor supprime la première recherche d'un contact, les suivantes glissent.

| Contacts | Recherches | Risque de glissement |
|---|---|---|
| **3 584** | 1 seule | **aucun** |
| 175 | 2 | réel |
| 9 | 3 | réel |

> **95 % du parc est hors risque.** Le point dur porte sur **184 contacts**.
> Et c'est réparable : capturer l'`idCritere` de Hektor — la console l'expose déjà
> (`console_job_worker.js:11405`) — supprimerait le glissement pour de bon.

## 2.3 Espace client — **il est déjà prêt**

`backend/app/services/espace_client.py:626-655` résout la recherche en trois niveaux, et son
propre commentaire dit pourquoi :

> ① `(contact + search_index)` — ② la recherche **active** du contact — ③ **la clé, en tout
> dernier recours**, *« on ne s'y fie donc qu'en tout dernier recours »*.

**L'espace client ne dépend pas de la clé.** Il continuerait de fonctionner pendant et après
le changement, et **se simplifierait** une fois la clé devenue stable.

## 2.4 Rapprochements — le vrai volume de travail

| Table | Lignes portant la clé |
|---|---|
| `app_rapprochement_score_history` | **438 080** |
| `app_rapprochement` | 46 174 |
| `app_rapprochement_search_state` | 4 076 |
| `app_contact_search_current` | 3 961 |
| notifications · envois · propositions · relances · statuts · visites | ≈ 760 |
| **Total** | **≈ 493 000** |

Le moteur : un déclencheur `trg_search_dirty` sur `app_contact_search_current`, et trois
fonctions qui prennent la clé en paramètre — `app_upsert_one_rapprochement`,
`app_refresh_rapprochements_for_search`, `app_process_rapprochement_dirty`.

⚠️ **Ces trois-là retombent sous le problème de la partie 1** : changer leur paramètre, c'est
le même DROP/CREATE, la même fenêtre, les mêmes droits à redonner.

## 2.5 Notifications — suivent, ne décident pas

708 notifications portent la clé, écrites par `app_generate_rapprochement_alerts`. Elles la
subissent, elles ne la fabriquent pas : elles suivent les rapprochements.

*(Rappel : les notifications déjà orphelines ont été abandonnées par décision de Frédéric —
« c'est pas grave de perdre les notifications ».)*

---

# Ce que je retiens

| | Verdict |
|---|---|
| **Hektor, sens montant** | **aucun risque** — la clé n'y va jamais |
| **Hektor, sens descendant** | **le point dur** — 184 contacts exposés au glissement d'index, 3 584 hors risque |
| **Espace client** | **déjà protégé**, se simplifierait |
| **Rapprochements** | ≈ 493 000 lignes + 3 fonctions à changer *(→ problème de la partie 1)* |
| **Notifications** | suivent |
| **Le renommage seul (5a)** | **PAS sans risque** — trois tests le prouvent |

**Préalable qui n'était dans aucun plan** : capturer l'`idCritere` de Hektor. Sans lui, la
réconciliation descendante repose sur une position, et 184 contacts peuvent voir leur
historique se rattacher à la mauvaise recherche.

Voir `AUDIT_IDENTITE_CONTACTS_2026-08-20.md`, `PLAN_DEV_ACTUALISE_2026-08-20.md`,
`RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md`.
