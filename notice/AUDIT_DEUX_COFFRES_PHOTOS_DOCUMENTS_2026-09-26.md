# Audit avant construction — les deux coffres, et le trou du run photo

*26/09/2026. Demandé par Frédéric : « avant il faut bien auditer mon projet pour que tout
soit bien prévu ». Décisions déjà prises : le coffre s'appellera **`gti-photo`** ; **pas
d'accès au DNS pour l'instant**, donc on servira sous le domaine Supabase.*

---

## 1. Ce que tu as aujourd'hui — mesuré

| | |
|---|---|
| **coffres Supabase** | **UN seul** : `hektor-console-documents`, **privé**, créé le 14/05 |
| son contenu | 22 925 fichiers · **33 Go** · que des documents |
| ses règles | lecture vérifiée ligne par ligne · dépôt autorisé sur le temporaire |
| **ton serveur** | 481 527 fichiers · **229,4 Go** *(documents 60 + photos 169)* · 518 Go libres |
| **coffre public** | **aucun** |
| **le logo** | `https://www.gti-immobilier.fr/images/logoSite.png` → **hébergé par Hektor** |

**Conséquence directe** : une photo n'a aujourd'hui **aucune adresse qui t'appartienne**, et
tes PDF générés (mandat, avis de valeur) chargent un logo qui meurt à la coupure.

---

## 2. ⛔ LE TROU QUE FRÉDÉRIC A TROUVÉ — il n'y a pas de run photo

*« On a récupéré toutes les photos, mais comment récupérer les nouvelles photos venant de
Hektor ? On n'a pas de run quotidien comme pour les documents. »* **Exact, et mesuré :**

| | |
|---|---|
| travaux `sync_hektor_photos` | **313 en tout**, le dernier le **17/08** |
| dans `run_full_pipeline.ps1` | **jamais** — aucune occurrence |
| dans les tâches planifiées | **jamais** |

**Donc : une photo ajoutée dans Hektor depuis hier soir n'arrivera jamais chez nous.** Le
rapatriement était un geste unique ; rien ne l'entretient.

### Ce qui sauve la situation

**Le miroir EST rafraîchi chaque nuit.** Mesuré ce matin : fichier modifié à **06 h 47**,
**57 973 annonces** contre 57 967 hier — six de plus. Le run relit le détail de toutes les
annonces, donc `images_json` connaît les photos nouvelles **dès le lendemain matin**.

➡ **Il n'y a rien à demander de plus à Hektor.** Il suffit de faire tourner le rapatriement
chaque nuit : il est incrémental par construction *(un fichier déjà là, de la bonne taille,
est sauté)*. Une nuit ordinaire = quelques photos.

### ⚠ Mais `synced_at` ne sert à rien pour cibler

Mesuré : **57 953 annonces sur 57 973 portent la date du jour**. Le run rafraîchit tout, donc
la date de synchro ne distingue pas ce qui a changé. **Il faut comparer les listes de photos**,
pas les dates.

**Optimisation à prévoir** : le script relit aujourd'hui les **436 523 lignes** d'index
(437 pages, ~10 min). En les demandant **regroupées par annonce**
*(`hektor_annonce_id` + la liste de ses photos)*, on descend à **48 464 lignes** — neuf fois
moins. Comparer deux listes par annonce détecte aussi bien un **ajout** qu'un **remplacement**,
ce qu'un simple comptage manquerait.

---

## 3. Qui consomme les photos — 48 points, pas 30

C'est la vraie portée du rebranchement. Mesuré :

| fichier | points | qui c'est |
|---|---:|---|
| `apps/hektor-v1/src/App.tsx` | **31** | l'app du négociateur |
| `Ecrans Android/export_project_vitrine.py` | **8** | la **vitrine publique** GitHub |
| `backend/app/services/espace_client.py` | **4** | l'**espace client** |
| `backend/app/services/appointment_service.py` | **3** | les RDV / la fiche visite |
| `backend/app/services/rapprochement_email.py` | **2** | les **emails** de rapprochement |

**Cinq consommateurs, pas un.** Et trois d'entre eux sont **publics ou envoyés à l'extérieur**
— la vitrine, l'espace client, les emails. C'est ce qui interdit de se contenter d'une adresse
privée à lien expirant.

⚠ **Les portails s'ajoutent à cette liste, et ils ne sont pas encore branchés.** `A.1` du plan
dit : *« sortie en nom propre, le flux de diffusion se construit en parallèle »*. Aujourd'hui
c'est Hektor qui donne les photos aux portails ; demain c'est toi, **avec tes adresses**.

---

## 4. Les pièges à prévoir — la raison de cet audit

### ⚠ P-1 · Une adresse publiée ne change JAMAIS
Un portail l'a mise en cache, un email l'a intégrée, un client l'a en favori. **On ne renomme
pas, on ne déplace pas.** D'où le choix du chemin, qui est le seul point vraiment irréversible :

```
gti-photo/{app_dossier_id}/{app_photo_id}/w400.jpg
gti-photo/{app_dossier_id}/{app_photo_id}/w1600.jpg
```

**Aucun numéro Hektor dedans.** C'est le travail d'identité des 24-26/09 qui le rend possible :
il y a trois jours, ces photos n'avaient *que* le numéro Hektor.

### ⚠ P-2 · Une photo retirée chez Hektor ne doit PAS être supprimée chez nous
Elle disparaît de `images_json`. Mais un portail ou un email peut encore la réclamer.
➡ **`delete-never`**, comme le registre d'affaires : on marque « plus dans Hektor », on garde
le fichier et l'adresse. *(Décision à confirmer par Frédéric.)*

### ⚠ P-3 · Une photo remplacée est une photo NEUVE
Même position dans la galerie, autre identifiant → nouveaux dérivés, nouvelle adresse.
L'ancienne reste. Sinon un portail servirait l'ancienne image sous la nouvelle adresse.

### ⚠ P-4 · Que faire des dérivés quand une annonce s'archive ?
Les documents descendent du cloud *(règle `shouldKeepCloud`)*. **Pour les photos, ce serait une
erreur de faire pareil** : un email envoyé le mois dernier pointerait dans le vide.
➡ **Proposition : on garde les dérivés**. 25 Go ne justifient pas de casser des adresses
diffusées. *(À trancher.)*

### ⚠ P-5 · L'egress — vérifié, et ça passe
Le plan Pro inclut **250 Go/mois non mis en cache + 250 Go en cache**. Les photos publiques
passent par le CDN, donc en **cache** *(0,03 $/Go au-delà)*. Un rafraîchissement complet des
portails ≈ 22 Go. **Confortable**, mais à surveiller si la vitrine prend du trafic.

### ⚠ P-6 · Le redimensionnement à la volée est facturé
5 $ par **1 000 images distinctes** transformées, quota Pro = **100**. Sur 74 585 photos ≈
**375 $ le premier mois**, et le compteur repart chaque cycle.
➡ **On pré-génère.** C'est ce que la documentation Supabase recommande elle-même.

### ⚠ P-7 · Le coffre public n'est pas un coffre sans règles
Seule la **lecture** devient libre. Le **dépôt** reste réservé au worker (clé de service).
Et on limite les types à `image/jpeg`, `image/png`, `image/webp` : **un PDF ne peut pas y
entrer par erreur**. C'est la protection par construction — pas par configuration.

### ⚠ P-8 · Le logo doit y aller aussi
Sinon les mandats et avis de valeur sortiront sans logo le jour de la coupure.
Deux endroits dans le worker : `console_job_worker.js:6451` et `:7248`.

### ⚠ P-9 · Le repli pendant la transition
Tant que Hektor vit, les deux adresses fonctionnent. **Prévoir : si le dérivé n'existe pas
encore, on affiche l'adresse Hektor.** Ça permet de basculer les 48 points progressivement, sans
jamais d'écran vide. C'est le même principe que le recouvrement des liens publics de RDV.

### ▫ P-10 · Les restes connus
- **8 013 photos / 583 annonces « Mandat clos »** : dans le miroir, **dans aucun index de
  l'app** → écartées. À trancher : ces annonces doivent-elles exister dans l'app ?
- **2 photos sans fichier** : lignes de l'ancienne couche Console, adresses `/wa/images/`
  au lieu de `/original/images/`, absentes du miroir.

---

## 5. Le chiffrage

```
MASTER      ton serveur, 169 Go, tout le parc, jamais servi          ✅ fait
DÉRIVÉS     coffre public gti-photo, annonces en vente seulement
              w400    ~40 ko  x 74 585  =   3 Go    listes, app
              w1600  ~300 ko  x 74 585  =  22 Go    fiche, vitrine, PORTAILS, emails
                                          ------
                                            25 Go
```

| | |
|---|---:|
| Supabase aujourd'hui | 33 Go |
| − le ménage *(archivés + orphelins)* | −3 Go |
| + les dérivés photo | +25 Go |
| **total** | **55 Go sur 100 inclus** |
| **marge** | **45 Go** |

⚠ **Les documents continuent de grossir d'environ 1 Go/mois** — la marge n'est pas éternelle.

---

## 6. L'ordre des lots

| | | pourquoi ici |
|---|---|---|
| **1** | **le run photo quotidien** — faire tourner le rapatriement chaque nuit | **le trou de Frédéric.** Sans lui, tout ce qui suit travaille sur un stock qui vieillit |
| **2** | créer `gti-photo` + le générateur de tailles dans le worker | rien n'est visible, tout est vérifiable |
| **3** | générer les dérivés des annonces en vente | 25 Go, une nuit |
| **4** | brancher **le logo** | petit, et visible tout de suite dans les PDF |
| **5** | rebrancher les **48 points**, avec repli sur Hektor | par consommateur : app, vitrine, espace client, emails, RDV |
| **6** | le ménage des 3 Go + `D4` *(l'état suit)* | libère la marge |
| **7** | le flux portails *(`A.1`)* | dépend du contrat, pas de nous |

**Le lot 1 d'abord, et c'est contre-intuitif** : on vient de finir un rapatriement de 169 Go,
et la première chose à faire est de s'assurer qu'il ne se périme pas. Une photo ajoutée ce
matin dans Hektor n'est chez nous **par aucun moyen**.

---

## 7. Ce qui n'a pas été mesuré

- La **taille réelle** d'un dérivé w400/w1600 sur tes photos — les 40 et 300 ko sont des
  ordres de grandeur, pas des mesures. **À calibrer sur 200 photos avant de lancer.**
- Quelle **bibliothèque d'images** côté worker *(sharp est le standard Node)* et son coût
  d'installation sur le serveur.
- Ce que les **portails** exigent exactement comme résolution minimale.
- Le trafic attendu de la **vitrine**, pour l'egress.
