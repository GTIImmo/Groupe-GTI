# Les mandants manquants du registre des mandats — audit + plan

**04/10/2026.** Signalé par Frédéric : des lignes du registre des mandats n'affichent
aucun mandant, alors que la fiche annonce et le registre des relations les ont.

---

## LE FAIT, MESURÉ

```
24 487 lignes au registre
   638 sans mandant
       ├─ 607  que NOTRE registre des relations connaît   <- le défaut
       └─  31  que personne ne connaît                    <- normal, à laisser vide

le registre des relations couvre 24 451 des 24 487 lignes  (99,9 %)
```

⚠ **Ce ne sont PAS surtout des annonces actives** : 635 des 638 n'ont plus de fiche
dans l'app (vendues, archivées). Par ancienneté : 4 récentes (≥ 62000), 8 entre
55000 et 62000, 137 entre 40000 et 55000, **489 anciennes**.

---

## LA CAUSE — une colonne orpheline, PAS une mauvaise lignée

⭐ **Le registre des mandats EST autonome, et je m'étais trompé en disant l'inverse.**
`app_mandat` est notre table durable : 26 835 mandats, plage d'identifiants propre,
doublure, 2 sentinelles, et le worker y écrit à la naissance d'un mandat. Le registre
en est la projection.

**Le défaut porte sur UNE colonne sur 25** :

```
app_mandat : 25 colonnes
   qui nomment une personne :  1   (mandants_texte, un TEXTE)
   identifiants de contact   :  AUCUN
```

`mandants_texte` est la seule colonne restée un texte recopié de Hektor, sans
identifiant et sans chemin pour se remplir depuis chez nous :

```sql
-- view_generale.py:338
COALESCE( NULLIF(TRIM(m.mandants_texte),'') , NULLIF(TRIM(det.proprietaires_resume),'') )
-- deux sources, toutes deux Hektor.  « app_relation » : 0 occurrence dans ce fichier.
```

Quand Hektor ne fournit plus ce texte (bien vendu, archivé, fiche mandat incomplète),
**rien ne prend le relais** — alors que le registre des relations a justement été créé
pour garder ces liens-là (les 82 386 liens qu'un bien vendu emportait).

---

## ⚠ CE QUE LA MESURE A CHANGÉ AU PLAN

**Le multiple est la règle, pas l'exception :**

```
1 seul mandant   4 600  (19 %)      3 à 4      4 887  (20 %)
2               11 884  (49 %)      5 et plus  3 077  (13 %)
                              -> 81 % ont PLUSIEURS mandants
```

**Et le repli naïf écrirait du bruit** — mesuré sur les 607 :

```
1 241 personnes brutes  ->  974 après dédoublonnage     -22 % (267 doublons)
exemple : « M. SCI JCL | Mr./Mme SCI JCL »  = la même entité deux fois
```

C'est le problème connu des **fiches de couple** : Hektor crée une seconde fiche pour
le ménage, notre registre porte les deux à juste titre, mais on ne les affiche pas
deux fois.

Répartition après nettoyage : 308 à 1 mandant · 266 à 2 · 12 à 3 · 12 à 4 · 5 à 5 ·
3 à 6 · 1 à 7.

---

## LE PLAN

### L'endroit — un seul, et il sert les deux chemins

`build_mandat_register_rows()` dans **`phase2/sync/export_app_payload.py`**.

⭐ Il alimente **le push de nuit** (`push_upgrade_to_supabase.py`, run l. 1159) **ET**
**le push par annonce** (`push_single_annonce_to_supabase.py`, déclenché par le worker
en ~1 min). Une correction, les deux bénéfices.

⛔ **NE PAS corriger dans `mandat_ledger.py` (run l. 839)** : il s'exécute AVANT le
rafraîchissement des relations (l. 922) et lirait **les liens de la veille**. L'ordre
du run est le piège principal de ce chantier.

### Deux colonnes, deux rôles

| colonne | rôle |
|---|---|
| `mandants_json` *(neuve)* | la **liste** — un objet par personne avec **nos deux numéros**. C'est elle qui permettra les fiches cliquables (chantier suivant). |
| `mandants_texte` *(existante)* | rempli **en dernier recours**, dérivé de la liste, pour le listing compact et `search_text`. |

Le patron existe déjà dans ces deux tables : `versions_json`, `avenants_json`,
`register_history_json`, `register_avenants_json`. On ne crée pas une forme nouvelle.

### Les règles à tenir

- ⛔ **jamais d'écrasement** : si Hektor ou le détail ont fourni le texte, on ne touche
  à rien — les 23 849 lignes remplies doivent rester **identiques**.
- **dédoublonnage** sur le nom nu (sans civilité, sans accents, sans casse).
- **les liens retirés sont exclus** (`retire_le IS NULL`) — cohérent avec le geste
  « retirer un mandant » posé le 03/10.
- `search_text` se recalcule : ces 607 mandats deviendront **trouvables par le nom du
  mandant**, ce qu'ils ne sont pas aujourd'hui.

### L'ordre des gestes

1. **patch SQL** : la colonne `mandants_json` (Frédéric le colle).
2. **le code** dans `export_app_payload.py`.
3. **contrôle à blanc** : 607 comblées · **0 des 23 849 modifiée** · échantillon relu.
4. **une garde** dans `phase2/checks/relation_disparue.py` : « lignes du registre sans
   mandant alors que les relations savent » — **607 aujourd'hui, devra valoir 0**.

---

## CE QUE CE CORRECTIF NE FAIT PAS

⛔ Les mandants resteront **affichés**, pas **cliquables** : `mandants_json` portera les
numéros, mais l'écran du registre devra être repris pour en faire des liens. Chantier
séparé.

⛔ Et il ne touche en rien les **gestes** du mandat, qui restent le vrai retard :

```
                         fiche ANNONCE        fiche MANDAT
gestes du worker              9                   2  (PDF · numéro)
RPC optimistes               17 (app)             0
champs possédés par l'app   189 cartographiés     1 champ, 2 lignes
« Modifier le montant »     geste optimiste       ouvre une DEMANDE à un humain
```

Les boutons « Modifier le montant », « Annuler le mandat », « Résilier avant
l'échéance » font un `INSERT` dans `app_diffusion_request` — **aucun ne crée de travail
worker, aucun ne touche Hektor**.

---

## DEUX FAITS ÉTABLIS EN CHEMIN

- ⭐ **Le mandat a bien ses deux identités**, comme les autres objets :
  `app_mandat_id` (26 835/26 835) et `hektor_mandat_id` (24 763). Les 2 072 sans
  numéro Hektor portent quand même le nôtre — c'est l'autonomie qui fonctionne.
- ⛔ **Il n'existe PAS de numéro de mandat provisoire**, et c'est **volontaire** : le
  numéro est une mention légale (série « cotée sans discontinuité »), PROTEXA le
  fabrique, et le front confirme avant car **c'est non annulable**. C'est la seule
  place où l'utilisateur attend vraiment.
- ⚠ **`origine = 'app'` : 0 mandat.** Le mécanisme de naissance dans l'app est en
  service depuis le 30/09 et **n'a jamais servi**. Tout ce qui précède sur ce chemin
  est lu dans le code, **pas observé**.
