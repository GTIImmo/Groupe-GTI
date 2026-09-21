# 🗺 LA CARTE DES CHAMPS — CRÉER *et* MODIFIER, OBJET PAR OBJET

**21/09/2026.** Tâche **26bis-3**, élargie le jour même après une correction de Frédéric.
Mesuré dans la base et le code. **Aucune donnée modifiée.**

> ⚠️ **CE DOCUMENT A ÉTÉ CORRIGÉ DEUX HEURES APRÈS SA PREMIÈRE VERSION, ET LA LEÇON VAUT PLUS
> QUE LA CARTE.** La première version ne mesurait que **le chemin de modification** (53 champs)
> et concluait « la protection par champ n'a rien à inventer ». Frédéric : *« le worker ajout
> annonces permet de remplir entièrement un bien avec des centaines de champs, pourquoi tu ne
> m'en parles pas ? »*
>
> **Il avait raison.** Un audit qui regarde un seul geste sur un seul objet n'est pas un audit.
> D'où la règle de méthode posée le même jour *(`CLAUDE.md` §0)* : **tout audit balaie les
> objets ET les gestes, en tableau, avant de conclure.**

---

## 1. Ce que l'app sait faire, objet par objet, geste par geste

| Objet | **Créer** | **Modifier** | Créables mais **non modifiables** |
|---|---|---|---|
| **Annonce** | **167 champs** *(111 appartement · 109 maison · 35 immeuble · 28 terrain · 18 autre · 10 garage)* | **53 champs** | ⚠️ **102** |
| **Contact** | **46 champs** | **13 champs** | ⚠️ **40** |
| **Recherche acquéreur** | **~100 critères** envoyés à Hektor | ~12 exposés par la modale | ✅ **hors sujet — voir §2 bis** |
| **Transaction** *(offre, compromis, vente)* | complet | complet *(fait en septembre)* | ✅ aucun |
| **Relation** *(mandant)* | oui *(rattacher / créer)* | non | à mesurer |
| **Mandat** | numéro + type + dates | prix, honoraires, surface | ⚠️ dates et durée — c'est **E.0-bis** |

---

## 2. L'asymétrie, en clair

**Le même défaut se répète sur trois objets : on sait remplir, on ne sait pas corriger.**

- **Annonce** : un négociateur crée un appartement avec ses 111 champs. Trois jours plus tard, il
  veut corriger « cave : non » en « cave : oui ». **Il doit ouvrir Hektor.**
  Parmi les 102 : cave, balcon, terrasse et leurs surfaces, séjour, cuisine équipée, ascenseur,
  accès handicapé, chauffage, eau et assainissement, climatisation, cheminée, alarme, interphone,
  digicode, volets électriques, double vitrage, piscine *(type, nature, traitement, dimensions,
  chauffée, couverte)*, résidence, dates de disponibilité, murs mitoyens, certificat de
  conformité, assurance dommages-ouvrage.
- **Contact** : 46 champs à la création, 13 modifiables.
*(La recherche ne fait pas partie de cette liste — voir juste en dessous.)*

---

## 2 bis. La recherche suit une règle À PART, et c'est une décision, pas un trou

**Décision de Frédéric du 20/08, appliquée le 24/08 (C.3) :**

> **Seuls l'ajout et l'archivage d'une recherche partent chez Hektor. Tout le reste est
> autonome dans l'app** — la modification des critères, les rapprochements, les propositions,
> les relances, les retours acquéreur.

Donc « le worker sait envoyer 100 critères, la modale n'en expose que 12 » **n'est pas un geste
manquant** : c'est le partage voulu. Une modification n'a pas à repartir chez Hektor ; l'y
renvoyer l'appauvrirait, puisque la modale n'exprime pas tout.

**Et ce qui aurait pu faire perdre des critères est déjà corrigé** : depuis le 30/08, une
modification **fusionne** au lieu de remplacer. Les critères venus de Hektor que l'app ne sait pas
produire sont **conservés** — 1 045 recherches sur 10 910 en portent au moins un, le plus fréquent
étant la pondération de quartier. Avant ce correctif, la perte aurait été immédiate et définitive.

**Ce qui reste ouvert pour la recherche**, et c'est un autre sujet : enrichir la modale pour que
le négociateur puisse **exprimer** plus de critères — un travail de confort côté app, pas une
dépendance à Hektor.

**La bonne nouvelle** : le worker sait **déjà envoyer** tous ces champs, puisqu'il les pose à la
création. Le chemin existe — il est à ouvrir **dans l'autre sens**.

---

## 3. Où vit la valeur, côté app *(annonce)*

| | Nombre |
|---|---|
| Colonnes de l'annonce *(`app_dossier_current`)* | **71** |
| Clés du **grand bloc** *(`detail_payload_json`)* | **134** |
| **Total côté app** | **~205** |
| Colonnes sur le serveur *(`app_view_generale`)* | 163 |
| Colonnes **communes**, donc arbitrables par la machinerie actuelle | 58 |

Et pour les autres objets : **43** colonnes pour le contact, **23** pour la recherche.

**Les quatre endroits où une valeur peut vivre** : la colonne · le grand bloc · **le calque**
*(ce que l'app vient de saisir, champ par champ)* · **la ligne d'attente** *(les champs pas encore
confirmés par Hektor)*.

**Ce qui reste vrai de la première version** : le calque et la ligne d'attente portent déjà la
liste exacte des champs saisis, un par un. **La protection par champ n'a donc pas besoin de
créer 41 colonnes** — elle applique cette liste au lieu de geler le bien.

**Où vivent les 53 champs modifiables** : 5 en colonne *(prix, ville, code postal, numéro de
mandat, titre)*, 7 dans une clé nommée du bloc *(surface, pièces, chambres, terrain, latitude,
longitude, garages)*, **41 dans le calque seulement**.

---

## 4. Ce que ça ajoute au plan

| Où | Quoi |
|---|---|
| **L3** *(inchangé)* | La protection par champ, sur ce que l'app sait écrire |
| **L5 — les gestes manquants** | **Rendre modifiables les champs qu'on ne sait que créer** : **102 pour l'annonce, 40 pour le contact**. ⚠️ **Pas la recherche** : ajout et archivage seuls passent par Hektor, le reste est autonome *(décision du 20/08)*. À côté de « modifier un mandat existant » et « gérer les photos » — même nature de trou |

**Avant d'ouvrir 102 portes**, il faudra mesurer lesquelles servent vraiment dans le parc : un
champ rempli sur 12 000 biens et jamais corrigé ne mérite pas le même effort que la cave ou le
chauffage.

---

## 5. Comment refaire cette mesure

`phase2/checks/carte_champs_annonce.py` — lecture seule, il rend les comptes de la section 3.
Les comptes de la section 1 se relèvent dans `Console/console_job_worker.js` :
`HEKTOR_WIZARD_FIELDS_BY_PROFILE` *(création)*, `HEKTOR_CLEANFIELD_TEXT_KEYS` et
`HEKTOR_CLEANFIELD_NUMBER_KEYS` *(modification)*.
