# Ce qui reste pour que documents et photos soient autonomes

*25/09/2026, au soir. Liste établie après la journée d'audits et de correctifs.
Chaque ligne est mesurée ou vérifiée dans le code — rien n'est supposé.*

> **La question à laquelle chaque ligne répond :** *le jour où Hektor est coupé,
> est-ce que ce geste fonctionne encore ?*

---

## ⛔ LE PLUS GRAVE — l'app affiche les photos DEPUIS HEKTOR

Vérifié : le front lit `photo_url_listing` et `images_preview_json` — des adresses
`staticlbi.com`, donc **l'abonnement Hektor**. 30 occurrences dans `App.tsx`.

**Le jour de la coupure, toutes les photos disparaissent de l'écran en même temps** —
fiches, listes, vitrine publique — **même avec les 110 Go rapatriés sur le serveur.**

Rapatrier remplit le coffre. **Ça n'a jamais suffi à afficher.** La preuve est dans les
documents : les 22 023 poussés dans Supabase sont visibles, les 22 493 restés sur le
serveur ne le sont pas. Vercel et Render ne lisent pas le disque du serveur.

**Il faut donc DEUX gestes, pas un :**

| | |
|---|---|
| **P1** | verser les photos des **annonces vivantes** dans Supabase — **~29 Go** *(33 + 29 = 62 sur 100 inclus)* |
| **P2** | faire lire l'app **depuis ces fichiers**, plus depuis les adresses Hektor |

⚠ **P2 est le vrai travail** : 30 points d'affichage à rebrancher, derrière un
interrupteur, avec repli sur l'adresse Hektor tant qu'elle répond.

---

## Les documents

| | geste | état | ce qu'il faut |
|---|---|---|---|
| **D1** | **ajouter** | ⛔ exige Hektor | Le socle est posé *(lots 1, 2a, 2b — dormants)*. **Manque : le front ne peut pas créer la ligne** — il n'a que `SELECT` sur `app_console_document`. Il faut une **RPC `SECURITY DEFINER`** *(patron de la signature manuscrite)* qui **vérifie l'accès du négociateur à l'annonce** — sinon n'importe qui dépose un document sur n'importe quel bien. |
| **D2** | **supprimer** | ⛔ exige Hektor | `handleDeleteDocumentFromHektor` **lève** si Hektor ne confirme pas. À la coupure, supprimer cesse de marcher. Même inversion à faire que pour l'ajout. |
| **D3** | le repassage | ⚠ orphelin | `Console/reprendre_envois_hektor.js` existe et est testé — **aucun run ne l'appelle**. À brancher *(quotidien, ou plus fréquent)*. |
| **D4** | l'état suit | ⛔ non | Une annonce archivée **garde ses fichiers dans Supabase pour toujours** : mesuré **1 691 documents / 95 annonces / 2,2 Go**, contre 628 Mo le 21/08 — **×4 en cinq semaines**. Et rien ne les **remonte** au retour : après la coupure, une annonce réactivée s'ouvrirait sans ses documents. ~34 annonces changent d'état par mois. |
| **D5** | l'index en local | ⚠ non | La descente ne ramène **pas** `app_console_document`. Les 44 516 lignes n'existent **que dans Supabase** ; les fichiers, eux, sont sur le serveur. |
| **D6** | `--detect` au pipeline | ⛔ non | `run_full_pipeline.ps1:1033` lance `--scope daily-cloud` **sans `--detect`** → le drapeau ajouté tel quel empilerait tout le périmètre chaque nuit. ⚠⚠ **Et un balayage du parc entier coûte 56 867 requêtes = 4× le seuil de bannissement** : la détection quotidienne doit rester **plafonnée**. |
| **D7** | étape non bloquante | ⛔ non | L'étape documents **lève** (`throw`) alors que ses voisines fragiles sont en `Invoke-OptionalStepWithRetry`. Une session Hektor morte tuerait Matterport, les **liens publics de RDV**, **la vitrine** et l'export Android. |
| **D8** | allumer le quotidien | — | `-EnqueueConsoleDocuments` dans `run_quotidien.ps1`. **Geste de Frédéric, après le rattrapage.** |

---

## Les photos

| | geste | état | ce qu'il faut |
|---|---|---|---|
| **P1** | verser dans Supabase | ⛔ rien | **0 fichier photo** chez Supabase. ~29 Go pour les annonces vivantes. |
| **P2** | l'app lit chez nous | ⛔ non | 30 points d'affichage pointent encore sur Hektor. **Sans ça, tout le reste ne sert à rien le jour J.** |
| **P3** | **ajouter** | ⛔ exige Hektor | Même **lot 2c** que `D1` — le socle est posé, le front ne peut pas créer la ligne. ✅ *La fuite est bouchée : le fichier est désormais gardé sur le serveur (`c95cb9b`).* |
| **P4** | **supprimer** | ⛔ n'existe pas | Ni worker, ni front, **et la commande Hektor est inconnue**. Le worker ne connaît que `vignettes` et `vignettes_hidden`, en lecture. **Premier pas : un relevé en lecture seule.** |
| **P5** | **réordonner** | ⛔ n'existe pas | idem `P4`. |
| **P6** | **photo principale** | ⛔ n'existe pas | idem `P4`. La seule occurrence dans l'app est un **compteur d'accueil**, pas un geste. |
| **P7** | l'état suit | ⛔ non | Aujourd'hui **0 photo** concernée — parce qu'il n'y en a aucune dans Supabase. **Dès que `P1` est fait, la fuite commence** : ~67 Mo/mois, et surtout **une annonce réactivée s'ouvrirait sans ses photos.** |
| **P8** | les annonces closes | ▫ écarté | **8 013 photos sur 583 annonces « Mandat clos »** : présentes dans le miroir, **dans aucun des 4 index de l'app**. À trancher — faut-il que ces annonces existent dans l'app ? |

---

## L'ordre que je propose

**Tant que `P2` n'est pas fait, le rapatriement des photos protège les fichiers mais
l'écran restera vide le jour J.** C'est la seule chose qui ne se rattrape pas après coup.

| | | pourquoi ici |
|---|---|---|
| **1** | **`P1` + `P2`** — Supabase pour les vivantes, et l'app lit chez nous | le seul point dont l'échéance est la coupure elle-même |
| **2** | **`D1` + `P3`** — la RPC du lot 2c | le socle dort déjà ; c'est la dernière pièce |
| **3** | **`D4` + `P7`** — l'état suit dans les deux sens | la fuite grossit toute seule, et double dès `P1` |
| **4** | **`D3`** — brancher le repassage | sans lui, une ligne en échec n'est jamais reprise |
| **5** | **`D6` + `D7`** — le pipeline | après le rattrapage, avant `D8` |
| **6** | **`D2`** — la suppression autonome | moins urgent : on peut vivre sans supprimer quelques semaines |
| **7** | **`P4` `P5` `P6`** — les gestes photo manquants | commence par un **relevé**, pas par du code |
| **8** | **`D5`, `P8`** | à trancher, pas bloquants |

⚠ **Ce qui n'est PAS dans cette liste parce que c'est déjà fait aujourd'hui** : le
mandat/annexe, le carnet du rattrapage, le frein de la détection, la tâche de 23 h, les
deux numéros sur les photos et sur Matterport, la fuite à l'ajout d'une photo, et le
socle de l'envoi différé.
