# A1 — Qui possède quel champ, entre l'app et Hektor

Date : 2026-08-19. **Document de décision. Aucun code.**
À valider par Frédéric ligne par ligne avant A2.

---

## 1. La règle qui produit ce tableau

> **Si l'app sait écrire un champ dans Hektor, c'est que le négociateur en est l'auteur.
> Donc l'import n'a pas le droit de le réécrire.**

La liste n'est pas inventée : elle est **dérivée du worker**, qui sait déjà quoi pousser vers
Hektor. Trois listes, lues dans `Console/console_job_worker.js` :

| Source | Champs |
|---|---|
| `HEKTOR_CLEANFIELD_TEXT_KEYS` | **27** |
| `HEKTOR_CLEANFIELD_NUMBER_KEYS` | **26** |
| `HEKTOR_WIZARD_FIELDS_BY_PROFILE` (union des 6 profils) | **136** |
| **Total** | **189** |

Tout est donc **vert par défaut**. Le travail consiste uniquement à repérer les exceptions.

---

## 2. VERT — l'app possède *(189 champs)*

### 2.1 Texte — 27 champs

`title` `description` `address` `address_complement` `postal_code` `city`
`private_city` `private_postal` `building` `transport` `proximity` `environment`
`kitchen` `exposure` `view` `garden` `pool` `terrace` `interior_state`
`exterior_state` `dpe_value` `ges_value` `diagnostic_risk_comment`
`mandate_type` `mandate_start_date` `mandate_end_date`
~~`mandate_number`~~ **-> voir exception §3**

### 2.2 Nombres — 26 champs

`price` `net_seller_price` `surface` `carrez_surface` `room_count` `bedroom_count`
`floor` `level_count` `bathroom_count` `shower_room_count` `wc_count` `land_surface`
`garden_surface` `terrace_count` `garage_count` `garage_surface`
`parking_inside_count` `parking_outside_count` `construction_year`
`copro_lots` `copro_charges` `copro_quote_part` `copro_works_fund` `fees`
`latitude` `longitude`

> `latitude` / `longitude` : produits par le **géocodage de l'app** au moment de
> l'édition d'adresse. Donc verts, malgré les apparences.

### 2.3 Équipements — 136 champs

Toute l'union des profils appartement / maison / terrain / garage / immeuble / autre :
`NB_CHAMBRES` `SURF_CARREZ` `ASCENSEUR` `CAVE` `PISCINE*` `TERRASSE` `CUISINE`
`ASSAINISSEMENT` `CHAUFFAGE` `EXPOSITION` … (liste complète : scratchpad `champs_worker.json`)

Ils vivent dans `app_dossier_detail_current.detail_payload_json`, pas en colonne.
**Conséquence : le blob ne peut pas être réécrit en entier par l'import** — il faut
préserver ces clés. C'est le point technique le plus délicat de A2/A3.

---

## 3. BLEU — Hektor produit, l'app ne sait pas fabriquer

| Champ | Pourquoi |
|---|---|
| **`numero_mandat`** | **La seule exception dans la liste des 189.** L'app sait l'écrire, mais c'est le moteur de numérotation Hektor qui le fabrique. Reste bleu jusqu'au registre en propre |
| `diffusable`, `nb_portails_actifs`, `has_diffusion_error`, `portails_resume` | retour de diffusion portails |
| `offre_id/state`, `compromis_id/state`, `vente_id` | cycle transaction tenu par Hektor |
| `images_preview_json`, `photo_url_listing` | photos hébergées chez Hektor (bascule en vert après rapatriement) |
| `agence_nom` | annuaire Hektor |
| `source_updated_at`, `source_hash`, `refreshed_at`, `search_text` | technique, calculé |

---

## 4. ORANGE — à trancher, et personne ne peut le faire à ta place

| Champ | La question |
|---|---|
| `statut_annonce`, `archive` | Le négociateur change le statut dans l'app, **mais Hektor peut archiver de son côté**. Vert (geste métier de l'app) ou bleu (Hektor fait foi) ? |
| `negociateur_email`, `commercial_id`, `commercial_nom` | L'affectation se fait dans l'app, **mais le worker s'impersonne avec cet identifiant pour écrire dans Hektor**. Le passer en vert avant la coupure risque de désaligner l'impersonation -> **prudence : bleu jusqu'à la dernière phase** |
| `mandat_type`, `mandat_date_debut`, `mandat_date_fin`, `mandat_montant` | Saisis dans l'éditeur de mandat de l'app. Vert probable — mais ils cohabitent avec `numero_mandat` qui reste bleu |

---

## 5. Ce que ce tableau déclenche

1. Il devient **une constante unique** dans le code, lue par les trois portes d'entrée :
   le rafraîchissement de fiche, l'import de nuit annonces, l'import de nuit contacts.
   **Surtout pas trois copies.**
2. Concrètement : les champs verts sont **retirés du paquet** envoyé. L'écriture se fait
   en « fusion » -> ce qui n'est pas envoyé n'est pas modifié. **C'est une soustraction.**
3. Règle du premier remplissage : un champ vert est écrit **si la ligne est nouvelle**,
   jamais ensuite.
4. Retour arrière : remettre le champ dans le paquet. Réversible ligne par ligne.

---

## 6. Ce que je n'ai pas vérifié

- La correspondance exacte entre chaque champ du worker et sa colonne ou sa clé de blob.
  Les noms diffèrent (`title` -> `titre_bien` + `texte_principal_titre`). **À faire avant A2**,
  sinon on retire du paquet une colonne qui ne correspond à rien.
- Les 136 champs d'équipement n'ont pas été croisés un par un avec les 134 clés du blob.
- Les contacts et les recherches acquéreur : hors périmètre de ce tableau, à traiter à part.
