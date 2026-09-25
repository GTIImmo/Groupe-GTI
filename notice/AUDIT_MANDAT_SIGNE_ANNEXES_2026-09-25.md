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
