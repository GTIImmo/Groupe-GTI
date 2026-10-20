# Ménage du coffre des documents — audit du 21/10/2026

**Lecture seule.** Aucune suppression, aucune écriture. Suite du chantier du domaine des
documents *(`AUDIT_DOMAINE_DOCUMENTS_2026-10-20.md`)*, dont les remplacements ont laissé
derrière eux des fichiers que plus aucune fiche ne réclame.

---

## 1. L'INVENTAIRE COMPLET du coffre `hektor-console-documents`

Chaque fichier tombe dans **une** catégorie nommée. **Il n'y a aucun « non classé ».**

| catégorie | fichiers | poids |
|---|---|---|
| A. réclamé par une fiche document *(`storage_path`)* | 24 120 | 34 Go |
| B. réclamé par une **photo** *(`app_console_photo.storage_path`)* | 135 | 100 Mo |
| ⛔ **C. COMPAGNON d'un document VIVANT — À GARDER** | **1 129** | **774 Mo** |
| **F. déchet : la fiche n'existe plus** | **5 091** | **7 120 Mo** |
| E. `temp/` | **0** | — |
| D. compagnon de photo · G. déchet photo · H. non classé | **0** | — |

## ⛔⛔ 2. LA VÉRIFICATION QUI DEVAIT ÊTRE FAITE AVANT TOUT — et elle a mordu

*« Du code lit-il un fichier du coffre par un chemin **calculé** au lieu du `storage_path`
enregistré ? »* **Oui, trois familles.**

| | |
|---|---|
| ✅ **le front** | 2 accès seulement, tous deux par le `storage_path` **enregistré** *(`createSignedUrl`, `api.ts:8711` et `11125`)*. `console_url` ne sert **jamais** à ouvrir : zéro occurrence |
| ⛔ **les compagnons ImmoSign** | `console_job_worker.js:5328` — `annonces/<n>/documents/<ID-FICHE>/immosign/<nom>`, **construit, jamais enregistré** |
| ⛔ **le PDF signé** | `console_job_worker.js:5649` — `.../signed/<nom>`, **idem** |
| ⛔ **les temporaires** | `.../temp/uploads/<travail>/<nom>`, enregistré **dans le travail**, pas dans la fiche |

➡ **Le bon critère n'est donc pas** *« une fiche pointe-t-elle ce fichier ? »* **mais**
*« le dossier qui le contient est-il encore une fiche vivante ? »* — car le chemin porte
l'`id` de la fiche. ⭐ **C'est ce critère qui sauve les 1 129 compagnons (774 Mo), dont les
preuves de signature.**

⭐ **Et `temp/` : le projet a DÉJÀ tranché le 14/10** *(`Console/test_nettoyage_temporaire.js`)* —
109 fichiers / 196 Mo supprimés, **le chemin bouché**, et trois cas gardés *(copie serveur
faite → on retire ; pas faite → on garde **et on le dit** ; Hektor ne confirme pas → on garde)*.
**Mesure du 21/10 : 0 fichier sous `temp/`. Le bouchon tient. ON N'Y TOUCHE PAS.**

## ⚠ 3. Deux de mes mesures de la veille étaient fausses

1. **« 132 photos orphelines »** : je n'avais interrogé que `app_console_document`. Les 135
   fichiers de photos sont **réclamés par `app_console_photo`**. ✅ **Zéro déchet photo.**
2. **« 7,8 Go à récupérer »** : c'était 7,8 Go **moins les 774 Mo de compagnons**.
   Le vrai chiffre est **7 120 Mo**.

## ⭐⭐⭐ 4. LA QUESTION QUE PERSONNE N'AVAIT POSÉE : doublon, ou dernière copie ?

Le prune supprime une fiche pour **deux** raisons très différentes : le bug du domaine
*(le document existe encore → le fichier est un doublon)*, **ou** Hektor a réellement effacé
le document *(le fichier est sa dernière trace)*.

| | fichiers | poids | annonces |
|---|---|---|---|
| ✅ **doublon** : le même nom est encore porté par une fiche vivante de la même annonce | **4 103** | **5 515 Mo** | 291 |
| ⚠ **« dernière copie »** : plus aucune fiche de l'annonce ne porte ce nom | **988** | **1 606 Mo** | 63 |

### Et les 988 ne sont PAS de vraies dernières copies — mesuré sur le disque

Le chemin local a **la même forme** que celui du coffre, **avec le même identifiant de fiche**.
Comparaison **annonce par annonce**, 63 lignes :

```
TOTAL      au coffre 988      sur le serveur 1 038
AUCUNE annonce ou le serveur en ait MOINS
```

➡ **Chaque « dernière copie » du coffre a au moins une jumelle sur le serveur.**
⚠ **La limite de cette mesure, et je la dis** : c'est une comparaison de **comptes par
annonce**, pas une vérification octet par octet de chaque fichier. Elle est forte *(même
identifiant de dossier des deux côtés)* mais **ce n'est pas une preuve individuelle**.

## 5. LE DÉCOUPAGE RETENU — et pourquoi

**Lot 1 = les 4 103 doublons, 5 515 Mo.** Son appartenance se prouve **sans sortir de la
base** : le même nom de fichier est encore porté par une fiche vivante de la même annonce.
Aucune dépendance au disque, aucune mesure à refaire.

**Lot 2 = les 988, 1 606 Mo.** Il ne tient que sur la comparaison de comptes ci-dessus.
**Je ne le propose pas aujourd'hui** : pour 1,6 Go, une preuve par comptes ne vaut pas le
risque. ⛔ **À trancher par Frédéric**, et à n'exécuter qu'après une vérification
individuelle si on y va.

## ⚠⚠ 6. L'INSTRUMENT : ce n'est PAS un patch SQL

Supprimer un objet du coffre passe par **l'API Storage**
*(`DELETE /storage/v1/object/<coffre>/<chemin>`, cf. `storageRequest` l. 1741)*. Un `DELETE`
sur `storage.objects` laisserait les octets orphelins et abîmerait les métadonnées.
**Il faut donc un script, pas un patch à coller.**

⭐ **Et le projet a déjà pensé la purge sœur** *(mémoire `purge-cloud-documents-archives`,
21/08)*, dont la doctrine s'applique :

| règle du 21/08 | ce qu'elle donne ici |
|---|---|
| le serveur porte **tout**, le cloud une copie des biens vivants | ✅ confirmé, et c'est le fondement du ménage |
| garde-fou : fichier local présent **et** `sha256` conforme | ⚠ **impossible ici** : nos fichiers n'ont **plus de fiche**, donc plus de `sha256` de référence |
| **exclure les documents signés** *(incident du 19/08)* | ✅ les `signed/` et `immosign/` sont déjà hors lot par le critère du dossier |
| **garder `storage_path`** pour la réhydratation | ⚠ **sans objet** : il n'y a plus de ligne |
| forme : **un type de travail**, pas un script, *« pour la traçabilité »* | ⛔ **à trancher** — voir ci-dessous |

⚠⚠ **DIFFÉRENCE ESSENTIELLE AVEC LA PURGE DU 21/08, dans les deux sens :**
- **plus sûr** : ses 391 documents avaient encore leur fiche, donc un écran pouvait les
  demander et `createConsoleDocumentSignedUrl` refusait un document non disponible. **Nos
  5 091 n'ont aucune fiche : aucun écran ne peut les demander. Le ménage ne casse aucun écran.**
- **plus grave** : pour la même raison, **`prepare_document_cloud` ne peut PAS les
  réhydrater** *(il part d'une fiche)*. **La suppression est donc IRRÉVERSIBLE côté coffre :
  il ne restera que la copie du serveur.**

## 7. Ce qui reste à trancher — et ce n'est pas à moi de le faire

1. **La forme** : un script autonome *(simple, immédiat)* ou **un type de travail** comme le
   projet l'avait prévu le 21/08 *(traçable dans `app_console_job`, visible dans l'app, mais
   trois verrous en base plus du code worker)*.
2. **Le lot 2** *(988 fichiers, 1,6 Go)* : on s'arrête au lot 1, ou on vérifie
   individuellement puis on y va ?
3. **La taille du premier passage** : je recommande **un essai sur ~100 fichiers** avant les
   4 103, pour voir le geste en vrai.

## ⛔ 8. Ce que je n'ai PAS mesuré

1. la vérification octet par octet des 988 *(seulement les comptes par annonce)* ;
2. si un **export**, un **e-mail** ou la **vitrine** a pu mémoriser une URL signée d'un de ces
   fichiers *(une URL signée expire, mais je ne l'ai pas prouvé sur ce coffre)* ;
3. le coffre **public des photos** : hors sujet ici, et non mesuré.
