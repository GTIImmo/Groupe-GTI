# 🗺 LA CARTE DES CHAMPS D'UNE ANNONCE

**21/09/2026.** Tâche **26bis-3**, préalable de la **protection par champ** *(lot L3)*.
Mesuré dans la base et le code. **Aucune donnée modifiée.**

> **La question à laquelle cette carte répond :** *« si un négociateur saisit un champ dans
> l'app, où cette valeur est-elle rangée — et peut-on la protéger sans geler tout le bien ? »*

---

## 1. Combien de champs, vraiment

| | Nombre |
|---|---|
| Colonnes de l'annonce dans l'app *(`app_dossier_current`)* | **71** |
| Clés du **grand bloc** *(`detail_payload_json`)* | **134** |
| **Total, côté app** | **~205** |
| Colonnes sur le serveur *(`app_view_generale`)* | **163** |
| Colonnes **communes** app / serveur — donc arbitrables par la machinerie actuelle | **58** |
| Champs que le worker sait **envoyer à Hektor** | **53** |

**« 46 colonnes dont 37 dans un blob »**, comme disait la tâche, était un ordre de grandeur pris
sur un périmètre plus étroit. Le compte réel est **205 champs, dont 134 dans un seul paquet**.

---

## 2. Les quatre endroits où une valeur peut vivre

| | Où | Ce que c'est | Survit à la nuit ? |
|---|---|---|---|
| **①** | **Colonne de l'app** — 71 | prix, ville, code postal, numéro de mandat, statut… | Réécrite depuis le serveur, **sauf** si une saisie est en attente sur ce bien |
| **②** | **Grand bloc** — 134 clés | surface, pièces, DPE, copropriété, chauffage, portails… Beaucoup sont eux-mêmes des paquets *(`mandats_json`, `honoraires_json`, `detail_raw_json`…)* | Idem |
| **③** | **Le calque** *(`app_optimistic_overlay`, dans le bloc)* | **Ce que l'app vient de saisir**, champ par champ, avant confirmation | **Il n'existe que le temps de l'attente** — 0 dossier aujourd'hui |
| **④** | **La ligne d'attente** *(`app_annonce_pending.push_fields`)* | Les champs saisis **et pas encore confirmés par Hektor** | Oui, tant qu'elle vit |

**Le fait qui décide de tout** : ③ et ④ portent déjà **exactement** la liste des champs saisis par
l'app, un par un. **La protection par champ n'a donc rien à inventer** — elle a seulement à
appliquer cette liste au lieu de geler le bien entier.

---

## 3. Les 53 champs que l'app sait envoyer, et où ils vivent

| Où vit la valeur | Champs |
|---|---|
| **Colonne de l'app** *(5)* | `price` → prix · `city` → ville · `postal_code` → code postal · `mandate_number` → numéro de mandat · `title` → titre |
| **Grand bloc, clé nommée** *(7)* | `surface` · `room_count` → nb_pieces · `bedroom_count` → nb_chambres · `land_surface` · `latitude` · `longitude` · `garage_count` |
| **Calque seulement** *(41)* | adresse et complément, ville et code postal privés, immeuble, transports, proximité, environnement, cuisine, exposition, vue, jardin, piscine, terrasse, état intérieur et extérieur, DPE, GES, commentaire de risques, type et dates de mandat, surface Carrez, étage, niveaux, salles de bain, salles d'eau, WC, surface du jardin, terrasses, surface de garage, parkings intérieurs et extérieurs, année de construction, lots et charges de copropriété, quote-part, fonds de travaux, honoraires, prix net vendeur, description |

⚠️ **Les 41 du bas sont le vrai sujet** : la saisie s'affiche *(par le calque)* et part chez Hektor,
mais **aucune colonne ne la range**. Tant que Hektor ne l'a pas confirmée, elle ne vit que dans le
calque et la ligne d'attente — qui disparaissent quand la saisie est soldée.

---

## 4. Ce que la carte permet de décider

1. **La protection par champ est possible sans rien restructurer** : la liste des champs à protéger
   est déjà écrite dans la ligne d'attente, à chaque saisie.
2. **Elle ne demande pas de créer 41 colonnes.** Le calque fait déjà le travail d'affichage ; ce qui
   manque, c'est que la reconstruction nocturne **le respecte champ par champ** au lieu de sauter
   le bien.
3. **Le grand bloc n'est un obstacle que pour un objet né dans l'app** — un bien que le miroir
   ignore n'a aucun bloc à recomposer. C'est 26bis-3 au sens strict, et ça appartient à **L4**,
   collé à la création.

---

## 5. Ce que la carte ne dit pas encore

- **Quels champs sont exclusifs à l'app.** Aujourd'hui : aucun côté annonce. Le jour où il y en
  aura un *(une note interne, un état de cycle)*, il ira au contrat d'autorité.
- **Les 9 champs à vérifier un par un** : surface, pièces, chambres, terrain, latitude, longitude,
  année de construction, prix net vendeur, honoraires — ils ont une colonne **sur le serveur** mais
  pas dans l'app. À regarder au moment de la protection par champ.
