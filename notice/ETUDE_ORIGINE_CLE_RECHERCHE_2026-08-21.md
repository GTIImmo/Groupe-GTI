# Étude — pourquoi la clé de recherche est un haché de contenu

Date : 2026-08-21. **Lecture seule.**
Demandée par Frédéric avant de figer la clé : *« pourquoi ce code a été créé, pourquoi pas
un id simple ? Il faut relire l'origine dans les notes, le git ou autre avant. »*

---

## 1. L'origine, datée

`git log -S "key_payload" -- phase2/contacts/build_contacts_layer.py`
→ **un seul commit : `915f6cd`, 27 mai 2026**, *« feat: integrate Hektor contacts directory »*.

Ce commit apporte en même temps **onze notes d'analyse** rédigées les 25-27 mai. L'une d'elles,
`RAPPORT_ANALYSE_FICHES_DETAIL_CONTACT_HEKTOR_2026-05-25.md`, décrit exactement ce que l'API de
Hektor renvoie pour une recherche acquéreur :

```json
{
  "offre": "0",
  "archive": "0 ou 1",
  "types": { "id_type_bien": "libellé" },
  "types_commerces": null,
  "activites_commerces": null,
  "villes": [],
  "quartiers": null,
  "particularites": null,
  "criteres": [ { "cle": "…", "valeur": "…", "ponderation": "…" } ]
}
```

> **Il n'y a aucun identifiant.** Hektor renvoie les recherches comme un **tableau anonyme**.

**Vérifié le 21/08 sur la réponse réelle la plus récente** (contact 604020, reçue le matin
même) : les clés sont `activites_commerces, archive, criteres, offre, particularites,
quartiers, types, types_commerces, villes`. **Toujours aucun identifiant.**

## 2. Pourquoi pas un id simple

Le concepteur disposait de **trois choses** : le contact, la position dans le tableau, le
contenu. Il les a hachées toutes les trois :

```python
key_payload = {"contact_id": contact_id, "index": index, "search": search}
search_key  = stable_hash(key_payload)[:24]
```

**Ce n'était pas une négligence : c'était la seule matière disponible.** Un identifiant propre
aurait dû s'accrocher à quelque chose de stable — or la seule prise, `(contact, rang)`, n'était
pas encore éprouvée. *(Ce n'est que le 21/08 qu'on a établi que Hektor n'efface jamais une
recherche — il pose une date d'archivage — donc que le rang ne glisse pas.)*

### L'`idCritere` n'existait pas encore

```
   27 mai    la clé est créée
   12 juin   l'idCritere apparaît -- 16 jours plus tard, et par une AUTRE porte :
             la console scrapée par le worker, pas l'API
             (commits 4cfc581 puis 3bc94eb, « recherche acquéreur : ajouter / modifier /
              supprimer » et « fiabilise recherches depuis fiche contact »)
```

**Au moment du choix, aucun identifiant n'existait nulle part dans le projet.**

## 3. Le modèle sous-jacent — et pourquoi il est devenu inadapté

L'intention était cohérente : **une recherche EST ses critères.** Deux recherches identiques
sont la même chose ; une recherche modifiée est une autre recherche. C'est une identité
**par le contenu**, un modèle légitime.

> Il l'est **tant que rien ne pend sous la recherche**.

Le défaut n'apparaît qu'ensuite, quand l'app ajoute ce qui a besoin de **continuité** :
rapprochements, historique de score, propositions, relances, retours acquéreur, envois d'email,
notifications. À partir de là, « une recherche modifiée est une autre recherche » signifie
« l'historique commercial se détache ».

**Ce n'est pas le code de mai qui est faux. C'est le monde autour de lui qui a changé.**

## 4. Contrôle de sûreté — figer la clé casse-t-il quelque chose ?

Le seul danger serait du code qui **recalcule** une clé depuis un contenu pour retrouver une
ligne : figée, la clé recalculée ne correspondrait plus.

Recherche dans tout le projet (`stable_hash`, `search_key =`, `searchKey =`, hachages SQL) :

```
   qui FABRIQUE une clé de recherche ?
      build_contacts_layer.py:828        <-- UN SEUL ENDROIT
```

Partout ailleurs — front (`RapprochementMandat.tsx`, `RechercheAcquereur.tsx`), patches SQL,
fonctions de base, worker — la clé est seulement **comparée** ou **transportée**. Jamais
refabriquée. Le worker, lui, ne la connaît pas du tout.

> **Aucun code ne recalculera une clé pour chercher une ligne. Le risque n'existe pas.**

## 5. Ce que figer veut dire, exactement

```
   AUJOURD'HUI   chaque nuit : nom = stable_hash(contact, rang, CONTENU)
   APRÈS         première fois : nom = stable_hash(...)   <-- le système reste
                 ensuite       : on relit le nom déjà attribué
```

Le mécanisme qui fabrique le nom **n'est pas modifié**. Il cesse simplement d'être rejoué. Le
nom est rangé dans `app_search_registry` — la table posée le 21/08 pour le numéro, qui survit
aux reconstructions complètes de la couche.

**Ce qui ne change pas** : l'empreinte de contenu (`stable_payload_hash`) continue de changer à
chaque modification. C'est elle qui détecte. Figer le nom est précisément **ce qui lui permet
enfin de travailler** — aujourd'hui elle est calculée, stockée, et jamais lue, parce qu'on la
cherche sous un nom qui vient de changer.

**Périmètre** : un endroit (`build_contacts_layer.py:828`) + une colonne au registre.
Les 15 tables portant la clé, les 27 fonctions qui l'utilisent, le front, le worker :
**inchangés**.

## 6. Ce que ça ne donne pas

L'identité reste un haché (`f66f0f01de9ef0bada94cd12`) et non un numéro. Fonctionnellement
c'est équivalent — un nom figé est un nom — mais ce n'est pas la « case propre » posée pour les
annonces (`app_dossier_id`) et les affaires (`app_affaire_id`).

`app_search_id`, posé le 21/08 sur 76 840 recherches, reste donc :
- **la clé du registre** — c'est lui qui permet d'y ranger le nom figé ;
- **l'identité d'après la coupure**, pour une recherche créée dans l'app, qui n'aura aucun
  contenu Hektor à hacher.

Voir `PLAN_DEV_ACTUALISE_2026-08-20.md`, `ANALYSE_RENOMMAGE_ET_CLE_RECHERCHE_2026-08-20.md`,
`RAPPORT_ANALYSE_SYNC_HEKTOR_SUPABASE_2026-06-19.md`.
