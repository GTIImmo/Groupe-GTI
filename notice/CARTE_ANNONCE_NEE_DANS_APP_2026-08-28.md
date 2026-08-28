# Carte — une annonce née dans l'app, colonne par colonne (26bis-③)

*28/08/2026 — tout est **mesuré**, rien n'est estimé. Essai en **lecture seule**, aucune écriture.*

---

## Ce que cette carte tranche

Le plan disait : *« poser ces lignes dans `app_view_generale` changerait ce que le push envoie,
avec **84 colonnes vides sur 130** : c'est l'étape ③, elle se décide champ par champ. »*

Deux choses ont changé depuis :

1. **Le chiffre était périmé.** C.15 a ajouté 33 colonnes commerce à la vue le 27/08 **sans les
   ajouter côté Supabase**. La vue fait aujourd'hui **163 colonnes**. L'écart se creuse tout seul
   à chaque chantier — argument pour trancher maintenant.
2. **La méthode était la mauvaise.** Voir ci-dessous.

---

## ① LA DÉCOUVERTE STRUCTURELLE — la vue n'est pas pilotée par le miroir

```sql
CREATE TABLE app_view_generale AS
...
FROM app_dossier d                                    <-- table LOCALE, jamais reconstruite
LEFT JOIN hektor.hektor_annonce ann ON ...            <-- le miroir n'est QU'UN LEFT JOIN
LEFT JOIN hektor.hektor_annonce_detail det ON ...
LEFT JOIN app_internal_status ist ON ...
```

**Il n'y a aucun `WHERE`.** Chaque ligne de `app_dossier` produit une ligne de la vue, sans
condition. D'où l'égalité exacte, vérifiée :

```
   app_dossier         61 094 lignes
   app_view_generale   61 094 lignes
```

> **Conséquence** : pour qu'une annonce née dans l'app existe côté serveur, il ne faut **pas**
> l'injecter dans la vue. Il faut lui donner **une ligne dans `app_dossier`** — 10 colonnes
> d'identité — et la vue se reconstruit autour d'elle, toute seule, chaque nuit.

### Pourquoi ça change tout

| | `--injecter` dans la vue *(conçu le 26/08)* | une ligne dans `app_dossier` |
|---|---|---|
| Colonnes à écrire | **163** | **10** |
| Fréquence | **chaque nuit**, après le `DROP` de 05:30 | **une fois** |
| Si le script échoue une nuit | **l'annonce disparaît du serveur ce jour-là** | rien, la vue la reprend |
| Sauvegarde | à ajouter | **déjà sous sauvegarde critique** |
| Patron | neuf | **`app_dossier`, éprouvé depuis l'origine** |

`--injecter` n'est pas faux — il est **réparateur par construction**. Il répare chaque nuit un
trou qu'on peut ne pas creuser.

---

## ② LA PREUVE — essai en lecture seule

Une CTE du même nom masque `app_dossier` par **une seule ligne fabriquée sans numéro Hektor**,
puis on rejoue la requête de la vue. Rien n'est écrit.

**Résultat : 1 ligne produite, aucun rejet, aucune erreur.** Et **13 colonnes se remplissent
seules**, avec des valeurs saines :

```
   titre_bien                   [Sans titre]
   responsable_type             non_attribue
   validation_diffusion_state   a_controler
   etat_visibilite              non_diffusable
   etat_transaction             sans_transaction
   internal_status              a_qualifier
   priority                     normal
   nb_portails_actifs  0   has_diffusion_error  0
   has_open_blocker    0   is_blocked           0   is_followup_needed  0
```

> Une annonce app-seule n'arrive donc pas « cassée » dans la vue : elle arrive **neuve**,
> à qualifier. C'est exactement ce qu'elle est.

---

## ③ LA CARTE DES 163 COLONNES

| Lot | Combien | Qui les remplit |
|---|---|---|
| **A — la vue les remplit seule** | **13** | valeurs par défaut, déjà justes |
| **B — Supabase les détient** | **50** | `app_dossier_current` · C.7 sait déjà les poser |
| **C — vide = NORMAL pour une annonce neuve** | **54** | offre, compromis, vente, mandat, commerce : *elle n'en a pas encore* |
| **D — À TRANCHER** | **46** | ni la vue, ni Supabase |

### Le lot D se décompose en deux, et c'est ce qui le rend petit

**37 colonnes viennent du PAQUET DE DÉTAIL Hektor** — `*_json`, `*_detail`, `nb_*`,
`texte_principal_*`, `proprietaires_*`, `note_hektor_principale`, `honoraires_resume`…

Or ce paquet a un équivalent côté app : `app_dossier_detail_current.detail_payload_json`
*(13 371 lignes, **un seul blob** d'environ 134 clés)*. **La question n'est donc pas « 37 champs »
mais « une seule structure ».** Et l'app en écrit déjà **7 clés**.

**9 colonnes viennent de la LIGNE DE LISTING** Hektor :

```
   surface · date_maj · partage · valide · responsable_affichage
   annonce_list_raw_json · corps_listing_html
   ville_publique_listing · code_postal_public_listing
```

⚠ **`surface` est le cas à regarder en premier** : remplie à **100 %** du parc, **lue par le
front**, et **absente des 71 colonnes de Supabase**. Ce n'est pas un oubli de l'app — c'est que
la liste de l'app n'affiche pas la surface. Il faut décider si une annonce app doit la porter.

---

## ④ CE QUI RESTE À DÉCIDER — et ce n'est plus « 105 champs »

1. **`app_dossier` plutôt que la vue** — écrire l'identité une fois, laisser la vue faire.
   *(Et garder `--injecter` comme filet, pas comme mécanisme principal.)*
2. **Le blob de détail** — quelles clés l'app pose-t-elle pour une annonce qu'elle a créée ?
   *Elle en pose déjà 7.*
3. **Les 9 champs de listing** — `surface` d'abord.
4. **Puis, et seulement puis** : allumer `CHAMPS_APP_ANNONCE`, l'interrupteur du contrat
   d'autorité, qui reste **vide à ce jour**.

---

## ⑤ CE QUE L'AUDIT PRÉALABLE A VÉRIFIÉ, ET QUI ÉTAIT DÉJÀ FAIT

La note du 21/08 donnait à 26bis **trois** composants. Les deux que je croyais ouverts
étaient fermés :

| | |
|---|---|
| **Trou A** — les 2 tables clés hors sauvegarde de nuit | ✅ `app_search_registry` et `app_affaire_ledger` sont dans `backup_critical.py` |
| **Trou B** — *« aucun tuyau ne redescend »* | ✅ tâche **GTI Descente**, 07:30, a tourné ce matin · 122 tables, 90 remplies, **1 530 644 lignes** · les **3 freins** exigés après l'incident du 21/08 sont posés |
| **Trou C** — le miroir sur le chemin de **lecture** | ⚠ ouvert, **non bloquant** : 37 728 annonces archivées lisent le miroir, mais le miroir **gèle sans disparaître** et une archive ne change plus |
| **§7-②** — *« persister les 36 champs calculés à l'export »* | ✅ **C.6, 25/08** — `app_annonce_champ_app`. *(« 36 » était faux : **13**.)* |

**Contradiction levée** : le plan dit *« la création optimiste est derrière un drapeau éteint »*,
le code dit `PROVISIONAL_CREATION_ENABLED = true`. Les deux sont justes — le drapeau `true` pose
une **ligne provisoire d'affichage** puis passe **quand même par Hektor** ; le « drapeau éteint »
désigne le patron *naître sans numéro Hektor*, **jamais exercé** *(0 ligne sur 61 094, remesuré)*.

---

*Sources : `phase2/pipeline/view_generale.py:34-515` · `phase2/identite/annonces_app_seule.py` ·
`phase2/identite/magasin_annonce_app.py` · `backup_critical.py:100-126` ·
`scheduled/run_descente.ps1` · essais `.tmp/carte_105.py`, `.tmp/essai_annonce_app.py`,
`.tmp/carte_finale.py` (lecture seule).*
