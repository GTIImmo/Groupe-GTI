# A.1 — LES PASSERELLES PUB : audit global, et la bascule LeBonCoin

**30/09/2026.** Audit demandé par Frédéric avant le chantier des passerelles.
Tout ce qui suit est **mesuré**, jamais déduit d'une note.

---

## En une page

```
⛔ le deballeur des passerelles rendait ZERO element depuis le 07/07   -> REPARE (02c2c7c)
⛔ la table ACCUMULE : 208 diffusions fantomes                          -> REPARE (02c2c7c)
⛔ la carte agence -> passerelle est fausse pour 17 agences sur 17      -> PATCH PRET (d629257)
⚠  aucune sentinelle ne peut voir tout cela                             -> A FAIRE
⭐ LA BASCULE LEBONCOIN A EU LIEU LE 30/09, PENDANT LA SESSION
```

---

## 1. La chaîne était coupée, et elle mentait sur sa fraîcheur

```
Hektor API  ----------------------->  raw_api_response        ✅ FRAIS (04:21 chaque nuit)
                                            |
                                      iter_listing_items      ⛔ RIEN, en silence
                                            |
                                      hektor_broadcast         ⛔ contenu du 07/07
                                      hektor_broadcast_listing ⛔ contenu du 07/07
                                            |
                        upsert_broadcast_states : DELETE + refait CHAQUE NUIT
                                            |
                              hektor_annonce_broadcast_state  ⛔ contenu 07/07
                                            |
                              app_mandat_broadcast_current    ⛔ 1 388 lignes
                                            |
                                        l'ecran
```

**La cause.** Hektor a changé la forme de `list_broadcasts` : `data` était une
**liste**, c'est devenu un carton `{"platforms": [...]}`. Le déballeur testait
`isinstance(data, list)` et rien d'autre → zéro élément, sans un mot.
`list_broadcasts` est **le seul des 28 listings** dans ce cas.

⚠ **LE PIÈGE QUI A FAIT DURER TROIS MOIS.** La lecture à la volée
(`refresh_single_annonce`) ne redemande pas la diffusion à Hektor : elle
**recopie la table figée** en y tamponnant **la date du jour**.

```
hektor_annonce_broadcast_state.synced_at = 30/09 15:35
                       son CONTENU       = 07/07
```

N'importe quel contrôle de fraîcheur aurait dit **vert**.

**L'écart mesuré le 30/09 :**

```
Hektor dit    1 677 diffusions,  416 annonces
nous disions  2 046 diffusions,  503 annonces
   121 diffusees AUJOURD'HUI et l'ecran ne les montrait pas
   208 plus diffusees et l'ecran les montrait encore
```

---

## 2. Le second défaut, trouvé par l'essai — pas par la lecture

Le déballeur réparé **seul** portait la table à **2 703 lignes pour 1 677
vraies** : l'upsert ajoute et corrige, il **n'enlève jamais**.

La diffusion est un **état**, pas une identité. On efface donc les passerelles
que Hektor vient de **redire**, et elles seules.

⚠ **Pas un `DELETE FROM` global** : le jour où Hektor répond partiellement (une
page, une panne), un effacement total emporterait des diffusions vivantes. Une
passerelle absente de la réponse **garde** ses lignes.

```
[0] fige au 07/07                2 046 lignes  503 annonces  fantomes 208  manquantes 121
[A] deballeur seul               2 703         624           208           0
[B] effacement TOTAL             1 677         416             0           0   <- risque
[C] effacement CIBLE             1 677         416             0           0   <- retenu
```

---

## 3. La carte agence → passerelle : le vrai trou

`app_diffusion_agency_target` (34 lignes, écrite à la main le 01/04) fait le
routage `agence + portail → hektor_broadcast_id`. C'est **elle** qui décide où
part une diffusion.

### 3.1 Une panne qui tournait depuis six mois

La passerelle LeBonCoin **n° 37** (Montbrison + Saint-Just) **n'existait plus
depuis le 03/04**. Elle avait été renumérotée **44**.

**Preuve, pas déduction** : les deux passerelles portent **exactement les mêmes
négociateurs** — 18 JEOFFROY (agence 13 Montbrison) et 54 CROIZIER (agence 3
Saint-Just).

```
1 795 annonces (1 106 Montbrison + 689 Saint-Just) = 13 % du parc
```

### 3.2 Et le 30/09, la série entière s'est produite

```
brut du run de nuit, 04:21   29 passerelles,  2 numeros faux
Hektor EN DIRECT,    16:45   38 passerelles, 15 numeros faux
```

Les **9 passerelles groupées sont remplacées par 17 individuelles (45 à 61)**,
une par agence. Seule la **35** survit, avec 3 annonces résiduelles.

**La 37 n'était pas un cas isolé : c'était le premier de la série, six mois en
avance.**

### 3.3 Le relevé, demandé à Hektor agence par agence

`ListPasserelles?idAnnonce=<témoin>` rend la configuration portails de
**l'agence** du bien : numéro **et** identifiant.

```
agence                              ancien -> nouveau   identifiant LeBonCoin
Ambert                                  35 -> 45        285776
COURPIERE                               35 -> 46        496094
ANNONAY                                 36 -> 47        285501
Firminy                                 39 -> 48        122698
Saint-Etienne                           39 -> 49        496104
Montbrison                              37 -> 50        285958
Saint-Just-Saint-Rambert                37 -> 51        496110
Dunieres                                43 -> 52        496111
Tence                                   43 -> 53        285755
BRIOUDE                                 41 -> 54        285965
Issoire                                 41 -> 55        496066
Craponne-sur-Arzon                      42 -> 56        285991
Saint-Bonnet-le-Chateau                 42 -> 57        496075
Monistrol sur Loire                     40 -> 58        285821
Saint-Didier-en-Velay                   40 -> 59        496092
Le Puy en Velay                         38 -> 60        285699
Yssingeaux                              38 -> 61        496125

17 agences interrogees · 17 repondues · 0 muette
17 numeros DISTINCTS · 17 identifiants DISTINCTS
```

⭐ **Frédéric avait raison** : Firminy et Saint-Étienne partageaient la **39**.
Ils ont désormais **48** et **49**.

**`bienicidirect` n'a pas bougé** : 17 lignes sur 17 justes, vérifiées par le
même appel.

---

## 4. Le tableau des gestes

| geste | qui le porte | état au 30/09 |
|---|---|---|
| **lire** la liste des passerelles | `sync_raw` → `normalize_source` | ⛔ mort 07/07 → ✅ réparé |
| **lire** l'état par bien | export → `app_mandat_broadcast_current` | ⛔ juillet → ✅ après le run |
| **lire** à la volée (1 bien) | `refresh_single_annonce` | ⛔ recopiait **et redatait** |
| **créer** une diffusion | `apply-targets` → `addAnnonceToPasserelle` | ⛔ 17 agences sur 17 |
| **retirer** une diffusion | `removeAnnonceToPasserelle` | ⛔ idem |
| rendre **diffusable** | `set-diffusable` (PATCH Diffuse) | ✅ indépendant |
| **valider** l'annonce | `set-validation` | ✅ indépendant |
| **demander** une diffusion | `app_diffusion_request` (9 lignes) | 🟡 dernière le 02/06 |
| **accepter** la demande | `accept-request` | ⛔ dépend de la carte |
| état **voulu** par bien | `hektor_annonce_broadcast_target` | ⛔ 0 ligne, **code mort** |

**Couverture** : phase2 (`hektor_diffusion_writeback.py`, 11 sous-commandes) ·
backend (6 routes, `hektor_bridge.py`) · front (`api.ts`, lit Supabase, replie
sur le proxy de dev) · **le worker ne porte AUCUN geste de diffusion** ·
**le run de nuit n'a aucune étape passerelle dédiée**.

⚠ **Le chemin d'écriture de production ne lit aucune table figée** : il lit
`app_diffusion_target` puis la carte dans Supabase, appelle Hektor en direct,
relit par `ListPasserelles`. La panne de lecture et la panne de carte sont
**deux pannes distinctes**.

⚠ **Non mesuré, et il faut le dire** : je ne sais pas si Hektor **refuse** un
`idPasserelle` mort (le négociateur voit une erreur) ou s'il **accepte sans rien
faire** (personne ne le sait). Le savoir demande d'écrire chez Hektor.

---

## 5. La sentinelle qui n'en était pas une

Il en existait **une**, `data.diffusion_erreur`, seuil 10. Elle lit
`has_diffusion_error` — **dans la table figée**. Sa valeur ne pouvait pas bouger,
donc elle ne pouvait pas passer au rouge.

> **Une garde dont l'entrée est figée n'est pas une garde.**
> C'est le pendant exact de *« une avarie qui ne change rien ne prouve rien »*.

---

## 6. Ce que ce chantier a coûté en fautes — les miennes

```
① mon compteur d'ecarts ne comptait rien      un carton a la mauvaise cle
                                               retombait sur `or []` et repassait
                                               en silence. LE CORRECTIF AVAIT LE
                                               DEFAUT QU'IL PRETENDAIT REPARER.
② mon `--a-blanc` n'annulait rien             les fonctions font commit() en
                                               interne ; le ROLLBACK n'avait plus
                                               rien a annuler.
③ « UN NUMERO PAR AGENCE, confirme »          affiche sur UNE agence repondue,
                                               puis sur ZERO appel. Un verdict
                                               sur rien.
④ `archive = '0'` est du TEXTE                `COALESCE(archive,0)=0` ecartait
                                               les 61 312 annonces.
⑤ quatre chiffres faux au 1er passage         app_diffusion_target 42 (le LOCAL)
                                               vs 13 (Supabase) -- deux cotes, pas
                                               une erreur ; app_diffusion_request
                                               0 -> 9 ; « le worker porte les
                                               appels API » -> faux.
```

➡ Les trois premières sont **la même faute** : *un garde-fou qui n'a pas été vu
échouer n'est pas un garde-fou.* Les trois ont été éprouvées **contre un cas qui
doit échouer**, et les trois ont d'abord échoué à échouer.

---

## 7. Ce qui est fait, ce qui reste

```
✅ 02c2c7c  le deballeur + le compteur d'ecarts + l'instantane cible
            rafraichir_passerelles.py (cible, --a-blanc)
            0 -> 29 passerelles · 2 046 -> 1 677 lignes · perimees -> 0
            rejeu +0 (idempotent) · verrou 0,12 s · 25 autres listings, 0 ecart
✅ f6c3377  passerelle_par_agence.py -- l'epreuve par deduction
✅ 0ada1ee  --par-agence -- l'epreuve par la REPONSE de Hektor
✅ d629257  le patch de la carte, eprouve en BEGIN/ROLLBACK, 3 garde-fous

⛔ COLLER LE PATCH               supabase/patch_passerelles_leboncoin_par_agence_2026-09-30.sql
⬜ RELANCER LE RUN               il ramassera les 38 passerelles tout seul
⬜ LE CONTROLE REPASSE           --par-agence doit rendre « a corriger : 0 »
⬜ UNE SENTINELLE                qui compare la carte aux passerelles vivantes
                                 -- elle serait ROUGE aujourd'hui : c'est sa preuve
⬜ la copie LOCALE de la carte   phase2/phase2.sqlite, 34 lignes, lue seulement
                                 par le chemin de DEV. A aligner apres le run.
⬜ hektor_annonce_broadcast_target  0 ligne, code mort : a retirer ou a servir
```

---

## 8. Ce que la bascule apprend pour la suite

Hektor peut **changer la forme d'une réponse** ou **renuméroter ses passerelles**
sans prévenir, et **rien chez nous ne le dit**. Les deux se sont produits, à six
mois d'écart, sur le même sujet.

➡ **La leçon n'est pas « réparer la carte », c'est « la carte doit se refaire
toute seule »** — depuis `ListPasserelles`, qui est la seule source qui dise la
vérité agence par agence. Tant qu'elle est écrite à la main, elle repérira.
