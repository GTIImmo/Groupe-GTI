# 🧾 INVENTAIRE — ce que la nuit efface et refait

**21/09/2026.** Tâche **INVENTAIRE** du lot **L2**. Mesuré en lisant le code et la base,
pas les notes.

> **La question à laquelle ce document répond, et que personne ne savait trancher :**
> *« si un objet naît dans l'app, qu'est-ce qui l'efface pendant la nuit, et qu'est-ce qui
> le protège ? »*

---

## 1. Sur le serveur — ce qui est vidé puis réécrit depuis le miroir de Hektor

| Table | Volume | Comment | Ce qui protège un objet né dans l'app |
|---|---|---|---|
| `app_view_generale` — le corps des annonces | 61 237 | **DROP + CREATE AS** *(view_generale.py:35)* | ⚠️ **Rien** aujourd'hui. Le recensement existe *(`app_annonce_app_seule`, 0 ligne)* mais **n'injecte pas** — décision du 26/08, ce geste se décide champ par champ *(L3)* |
| `app_contact_current` — le corps des contacts | 356 111 | **DELETE + INSERT** *(build_contacts_layer.py:1281)* | ⚠️ **Rien** — recensement posé le 21/09 *(`app_contact_app_seul`, 0 ligne)*, il n'injecte pas non plus |
| `app_contact_relation_current` — les liens bien ↔ personne | 167 436 | **DELETE + INSERT**, la table **entière** | ⚠️ **Rien** — recensement posé le 21/09 *(`app_relation_app_seule`, 0 ligne)* |
| `app_contact_search_current` — les recherches | 77 061 | **DELETE + INSERT** | Le **registre des recherches** *(`app_search_registry`, table à part, jamais vidée)* rend son numéro et son nom figé à chaque ligne |
| `app_contact_duplicate_group_current` / `_member_current` | 37 352 / 47 953 | **DELETE + INSERT** | Recalculable. ⚠️ **Une fusion décidée dans l'app serait perdue** *(elle n'existe pas encore : le bouton ouvre Hektor)* |
| `app_work_item` *(workflow mandat/diffusion)* | — | **DELETE ciblé** *(bootstrap_phase2.py:150)* | Recalculable |
| `app_affaire_champ_app` — le carnet des transactions | — | **DROP** au rebâtissage du magasin | Le carnet est reconstruit **depuis l'app**, pas depuis le miroir : sans objet |

**Ce qui n'est PAS dans cette liste, et c'est important** : `data/hektor.sqlite` — le miroir — ne
se vide **jamais**. Règle 5 du projet : *« le miroir se met à jour, il ne se remplace pas »*.

---

## 2. Dans l'app — ce que le push du matin supprime

| Table | Volume | Ce qui est supprimé | Ce qui protège |
|---|---|---|---|
| `app_dossier_current` · `app_dossier_detail_current` | 13 417 | Les annonces **absentes du serveur** *(`stale_ids`)* | Le **saut des éditions en cours** *(`fetch_dirty_annonce_ids`)* — et depuis le 20/09, **plus les lignes en conflit** : elles gardent la saisie sans geler le bien |
| `app_contact_current` | 61 955 | Les contacts absents du serveur ou devenus inéligibles | `delete_contacts_except_dirty` — **uniquement** ceux qui ont une saisie en cours |
| `app_contact_search_current` | 11 369 | Les recherches absentes de la repose | `delete_searches_except_dirty` — par couple *(contact, rang)* |
| `app_contact_relation_current` | 81 288 | Toute clé absente de la nouvelle repose | ⚠️ **Rien** |
| `app_mandat_register_current` | 23 836 | **Toute la table** en reconstruction complète, sinon par annonce | ⚠️ **Rien** — c'est A.3-technique *(lot L9)* |
| `app_work_item_current` · `app_mandat_broadcast_current` | 13 113 · 1 427 | Par annonce, avant réécriture | Recalculable |
| `app_filter_catalog_current_store` | 56 | **Toute la table** | Recalculable |

---

## 3. Les trois faits qui sortent de cet inventaire

1. **Quatre tables sont refaites en entier sans aucun filet** : le corps de l'annonce, le corps
   du contact, les relations, le registre des mandats. Ce sont exactement les tâches **26bis-3**,
   **26bis-CONTACTS**, **26bis-RELATIONS** et **A.3-technique**. L'inventaire ne découvre pas de
   trou nouveau : **il confirme que la liste du plan est complète.**

2. **Les recherches sont le seul objet déjà protégé de bout en bout** — registre à part, nom figé,
   saisie protégée à vie. C'est le modèle à recopier pour les trois autres.

3. **Un écart non expliqué, à regarder un jour** : les groupes de doublons comptent **37 352**
   lignes sur le serveur et **0** dans l'app. Ce n'est pas une perte — la table est recalculable —
   mais l'écran des doublons ne voit donc rien de ce que le serveur calcule.

---

## 4. Ce que ce document engage

- Toute table **ajoutée** à l'une de ces deux listes doit dire, le jour où on l'ajoute, **ce qui
  protège un objet né dans l'app**. Sinon elle rejoint la colonne « rien ».
- Les recensements posés *(annonces le 26/08, contacts et relations le 21/09)* restent
  **en observation** : ils notent, ils n'injectent pas. L'injection se décide **champ par champ**,
  c'est le lot **L3**.
