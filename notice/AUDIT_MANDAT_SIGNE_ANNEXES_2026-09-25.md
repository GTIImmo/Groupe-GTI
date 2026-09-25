# Le mandat signé, les annexes — et où en est l'extraction des documents

*25/09/2026. Frédéric se souvenait de deux choses : le run des documents est « bloqué », et
« sur l'app, à la place du mandat signé, il n'y a que les annexes ». **Les deux sont exactes.**
Vérifié dans le code, dans la base, et **à l'écran dans l'app connectée** — PDF ouverts.*

## 1. Le run des documents ne tourne pas — et ce n'est pas une panne

L'étape existe dans `run_full_pipeline.ps1` (l. 1020), mais **derrière un interrupteur** :

```powershell
if ($EnqueueConsoleDocuments -or $EnqueueAllConsoleDocumentsLocal) { ... }
```

Et la tâche planifiée « GTI Quotidien » appelle `scheduled\run_quotidien.ps1`, qui lance :

```
run_full_pipeline.ps1 -PushContactsToSupabase -ContactsEligibleOnly
                      -AllowStaleSupabaseDeletes -IncludeArchivedContactSearches
```

➡ **Le drapeau n'est jamais passé. L'étape ne s'exécute donc jamais.** Ce n'est pas cassé :
c'est un interrupteur laissé retombé après le bannissement d'IP du 20/08. Dernier passage réel
le **23/08 à 16 h 09**, 0 travail en erreur.

## 2. Le mandat signé : les données sont là, c'est le CONTENU qui pose problème

**Contrairement à ce que disait ma mémoire, les blocs ImmoSign SONT indexés :**

| source | lignes | dont « mandat » | rapatriées |
|---|---|---|---|
| procédures ImmoSign | 448 | 434 | 440 |
| **mandats signés** | **36** | 34 | **36 — toutes** |

Et pour chaque mandat, **trois fichiers** sont descendus : le PDF signé, `preuves-NNN.zip`,
`procedure-NNN.zip`. Tout est sur le serveur **et** dans Supabase.

**L'écran les affiche correctement** : onglet « Documents », filtre « Signés », nom, taille,
date de signature, bouton « Ouvrir le signé ». Vérifié sur l'annonce **32675** *(EM69816,
« Ancienne ferme rénovée »)*, qui en porte deux.

### ⛔ MAIS : sous le même nom, deux documents très différents

Les deux lignes de l'annonce 32675 s'appellent **exactement pareil** —
*« Mandat (Avec saisie du numéro) (Vente) »* — et j'ai ouvert les deux PDF :

| document | taille | pages | ce que c'est VRAIMENT |
|---|---|---|---|
| Document 419 | 876 Ko | **11** | ⭐ **le vrai mandat** — couverture GTI, puis le contrat |
| Document 439 | 193 Ko | **6** | ⛔ **les ANNEXES SEULES** — commence par « ANNEXE 1 — INFORMATIONS CONTRACTUELLES DU CONSOMMATEUR » |

➡ **C'est exactement ce que Frédéric décrivait.** Quand une annonce n'a que le petit document,
**le négociateur ne voit que les annexes** — et l'app lui affiche « Mandat », ce qui est
trompeur.

### L'ampleur, mesurée sur les 36

| | documents | annonces |
|---|---|---|
| **gros** *(329 Ko à 1,38 Mo)* — le vrai mandat | **28** | 25 |
| **petits** *(163 à 218 Ko)* — vraisemblablement des annexes seules | **8** | **8** |

⚠ **8 annonces sont donc concernées** — sous réserve : seuls **deux** PDF ont été ouverts.
Le seuil de 260 Ko est une **hypothèse tirée de ces deux cas**, pas une règle vérifiée.
**Il faut ouvrir les 8 pour conclure.**

## 2bis. L'INVENTAIRE COMPLET — ce qu'on a déjà récupéré *(mesuré le 25/09)*

### Vue d'ensemble

| | |
|---|---|
| **documents indexés** | **44 516** |
| **poids total** | **60 Go** |
| **annonces couvertes** | **8 549** *(sur 13 437 dans l'app)* |
| dans Supabase *(donc visibles dans l'app)* | **22 023** |
| sur le serveur seulement *(invisibles)* | **22 493** |
| période couverte | 29/06 → **26/08/2026** |

### Par source — d'où ils viennent chez Hektor

| source | documents | annonces | poids | dans Supabase | serveur seul |
|---|---|---|---|---|---|
| **documents privés** *(console)* | **42 181** | 8 459 | 58 Go | 19 768 | **22 413** |
| documents partagés | 1 184 | 158 | 1,4 Go | 1 150 | 34 |
| modèles | 667 | 238 | 171 Mo | 629 | 38 |
| **bloc ImmoSign** | **448** | 313 | 299 Mo | 440 | 8 |
| **mandats signés** *(lignes synthétiques)* | **36** | 32 | 25 Mo | 36 | 0 |

⚠ Les **36** ne sont pas « les seuls mandats signés » : ce sont les cas où le document
**a perdu son `force_transfert`** en étant signé, et qu'une ligne de rattrapage a dû
reconstruire *(le correctif `808dfe5` du 29/06)*.

### Par famille — de quoi il s'agit *(classé sur le nom du fichier)*

| famille | documents | annonces | poids |
|---|---|---|---|
| **cadastre / plan** | 5 492 | 3 942 | 2,8 Go |
| **images** | 4 590 | 1 561 | 7,5 Go |
| **mandats** | **4 303** | **2 951** | 3,2 Go |
| **avis de valeur** | 3 956 | 2 927 | 12 Go |
| **diagnostics** | 3 316 | 1 824 | 8,1 Go |
| copropriété | 2 694 | 1 663 | 3,7 Go |
| pièces d'identité | 1 947 | 799 | 1,8 Go |
| offres | 968 | 555 | 865 Mo |
| avenants | 882 | 608 | 351 Mo |
| taxes | 862 | 752 | 750 Mo |
| compromis / promesses | 446 | 360 | 1,5 Go |
| **autre / non classé** | **15 060** | 5 110 | 18 Go |

⚠ **Ce classement est une DÉDUCTION sur le nom du fichier**, pas une donnée de Hektor : la
colonne `document_type` vaut « document » pour **tous**. D'où les **15 060 non classés (34 %)**.
**Hektor ne nous dit pas ce qu'est un document.**

### La signature — et c'est une bonne surprise

| | documents | annonces |
|---|---|---|
| **signés** | **281** | ~240 |
| en procédure, pas encore signés *(`pending`)* | 48 | 45 |
| « signable » mais jamais envoyé *(`to_send`)* | 7 258 | ~2 140 |

Et surtout : **les 244 ImmoSign marqués « signés » ont TOUS leur PDF signé rapatrié**
*(244 sur 244)*, **et** leur `procedure-NNN.zip`. **Aucun trou de ce côté.**

➡ **Le mécanisme de récupération des signés fonctionne.** Le défaut est ailleurs : dans
**ce que contient** le PDF rapatrié pour 8 d'entre eux *(§2)*, et dans le **nom affiché**,
qui ne distingue pas le mandat de ses annexes.

## 3. Ce qu'il reste à comprendre — non mesuré

- **Pourquoi certaines procédures ne rendent que l'annexe.** Hypothèses non vérifiées :
  le mandat et ses annexes sont **deux procédures ImmoSign distinctes** chez Hektor, ou bien
  seule la dernière pièce signée est rapatriée.
- **Le `procedure-NNN.zip` contient-il le mandat complet ?** Il pèse ~925 Ko dans les deux cas,
  y compris celui dont le PDF signé ne fait que 193 Ko. **Si oui, la pièce manquante est déjà
  sur le serveur** — il suffirait de l'extraire, sans rien redemander à Hektor.
- Le nom affiché vient de Hektor (`archive_filename`) : **rien ne distingue le mandat de ses
  annexes**. À corriger dans l'affichage, quelle que soit la cause.

## 4. Ce que ça donne pour `D.0`

L'ordre à suivre, du moins cher au plus cher :

1. **Ouvrir les 8 petits PDF** pour confirmer que ce sont bien des annexes. *(lecture, ~30 min)*
2. **Regarder le contenu d'un `procedure-NNN.zip`** déjà sur le serveur : s'il contient le
   mandat complet, le problème se règle **sans toucher à Hektor**. *(lecture, ~15 min)*
3. **Distinguer le mandat des annexes à l'écran**, quoi qu'il arrive. *(petit)*
4. **Puis seulement**, rallumer l'extraction — avec le frein anti-bannissement, sans jamais
   rejouer les annonces déjà en échec.

⚠ **L'ordre compte** : rallumer l'extraction avant d'avoir compris ce qu'on rapatrie ferait
redescendre 44 516 documents avec le même défaut.
