# Où placer l'étape photos dans le run de nuit — audit

*26/09/2026. Après la mesure décisive : **Hektor DATE les photos** (date_maj passée de
`2026-09-24 12:10:17` à `2026-09-26 09:32:51` à l'instant de l'ajout). Donc pas de balayage
à construire — juste une étape au bon endroit.*

---

## 1. Les trois contraintes d'ordre

L'étape lit le miroir local et Supabase, et télécharge sur le CDN. **Elle ne parle jamais à
Hektor.** Mais elle dépend de deux étapes qui, elles, en dépendent :

| contrainte | pourquoi | position minimale |
|---|---|---|
| **① après `normalize_source`** *(l. 285)* | c'est lui qui réécrit `hektor_annonce_detail.images_json`. Avant, le miroir porte les photos de la veille. | l. 285 |
| **② après `push upgrade to supabase`** *(l. 925)* | ⚠ **le point que Frédéric soulève.** L'étape doit résoudre `app_dossier_id` depuis les **quatre index Supabase**. Une annonce apparue cette nuit n'y est qu'après cette étape — sinon ses photos seraient **écartées faute de numéro d'app**. | **l. 925** |
| **③ avant l'export vitrine** *(l. 1085)* | pour que le site publie des adresses à jour. Pas critique aujourd'hui *(la vitrine lit encore Hektor)*, indispensable après `P2`. | l. 1085 |

➡ **Fenêtre : entre la ligne 925 et la ligne 1085.**

## 2. La place retenue : juste après l'étape documents

```
l. 1038   enqueue console documents   (derrière son drapeau)
l. ~1045  >>> ENFILAGE DES PHOTOS <<<
l. 1052   Matterport
l. 1062   liens publics de RDV
l. 1085   export vitrine
```

**Pourquoi là plutôt qu'ailleurs :** les deux chantiers de fichiers se lisent ensemble dans
le journal, et l'ordre documents → photos → Matterport → vitrine suit la logique
« on remplit, puis on publie ».

## 3. Pourquoi DANS le run, et pas une tâche séparée

Le rattrapage **documents** a sa propre tâche à 23 h, pour une raison précise : il consomme
le **quota Hektor**, et il doit être espacé du run.

**Les photos n'ont pas ce problème** — CDN public, hors quota, mesuré à 0 refus sur
435 000 téléchargements. Donc rien ne justifie de la sortir du run, et l'y mettre garantit
qu'elle suit toujours le miroir qu'elle exploite.

## 4. Les deux numéros — le point de Frédéric

*« Pense à notre plan dev, à l'id de l'app mais toujours id hektor aussi pour les workers. »*
Les deux sont nécessaires, **et pour des raisons différentes** :

| | à quoi il sert ici |
|---|---|
| **`app_dossier_id`** | rattacher la photo au bien **dans l'app**, et survivre à la coupure. C'est lui qui impose la contrainte ② : il vient des index Supabase. |
| **`hektor_annonce_id`** | ⚠ **l'adresse du fichier sur le CDN en dépend** *(le chemin `.../biens/…`)*, et le worker s'en sert pour désigner la fiche. Sans lui, on ne sait pas quoi télécharger. |
| **`hektor_photo_id`** | la clé d'unicité `(annonce, photo)` — c'est elle qui reconnaît une photo déjà rapatriée. |

**Le script écrit les trois**, et refuse un paquet entier si une seule ligne part sans le
numéro d'app *(garde-fou posé le 25/09, contrôles u→z)*.

## 5. Deux réglages à poser

| | |
|---|---|
| **non bloquante** | `Invoke-OptionalStepWithRetry`, comme Matterport. Un hoquet du CDN ne doit pas tuer la fin du run — l'export vitrine et les liens de RDV viennent après. |
| **plafonnée** | `--limite 2000`. Une nuit ordinaire = quelques photos ; mais après une interruption, le retard pourrait faire durer le run. À 17 photos/s, 2 000 = **2 minutes**. |
| **sonde** | `-WorkerKey "phase2.rattrapage_photos"` — sinon l'étape peut échouer en silence, le défaut le plus dangereux de ce projet. |

## 6. Ce qui reste à vérifier demain — gratuit

J'ai lu la `date_maj` par l'API `AnnonceById`. **Le run, lui, lit le listing.** Très
probablement le même champ, mais ce n'est pas prouvé.

➡ **Demain matin** : `sync_annonce_state.date_maj` pour 63146 doit avoir bougé, et
`images_json` doit contenir la photo d'essai. Si oui, la chaîne est prouvée de bout en bout,
sans une requête de plus.

⚠ **Si le listing ne portait PAS la date**, le run ne relirait pas l'annonce et il faudrait
revenir au balayage plafonné. **Ne pas coder l'étape comme si c'était acquis** — c'est pour
ça que la vérification est au plan.
