# Comment c'est arrivé, et ce qui est vraiment perdu

*20/10/2026, le soir de la pose du correctif. Frédéric a demandé un audit neuf, sur deux
questions : **comment cela est arrivé**, et **ai-je perdu des informations de signature**.*

**Lecture seule.** Aucune écriture, aucun appel à Hektor.
Le correctif lui-même et ses mesures sont dans `AUDIT_DOMAINE_DOCUMENTS_2026-10-20.md`.

---

# PARTIE 1 — LES SIGNATURES : **le dossier est intact, MAIS ~29 DOSSIERS DE PREUVES SONT PERDUS**

## ⛔⛔ JE M'ÉTAIS TROMPÉ, ET C'EST FRÉDÉRIC QUI M'A FAIT CREUSER

J'avais écrit *« non, rien n'est perdu en signatures »*. **C'est faux, et voici la mesure qui le
dit.** Un document signé a deux choses : **son dossier** *(statut, date, n° de procédure, PDF
signé)* et **son dossier de preuves** *(`preuves-N.zip`, la piste d'audit de la signature
électronique)*. Le premier est intact partout. **Le second manque six fois plus souvent sur les
fiches que le bug a remplacées :**

| fiches signées | signés | sans leur ZIP de preuves | **taux** |
|---|---|---|---|
| **A. jamais touchées** *(témoin)* | 99 | 4 | **4,0 %** |
| ⛔ **B. recréées par le bug** | 142 | **35** | ⛔ **24,6 %** |
| C. d'origine, nouveau domaine | 188 | 2 | **1,1 %** |

⭐ **C'est la comparaison des TAUX qui tranche**, pas le nombre brut : au taux des fiches
intactes, il en manquerait **~6** sur 142. **Il en manque 35.**
➡ **Environ 29 dossiers de preuves ont été détruits par le bug.**

**Pourquoi** : le `preuves-N.zip` est rangé **dans le dossier de la fiche**. Fiche remplacée =
nouveau dossier = le zip reste derrière, et **rien ne va le rechercher** *(le worker ne
retélécharge que le document, pas ses compagnons)*.

⭐⭐ **ET C'EST PROBABLEMENT RÉCUPÉRABLE** : les **35 numéros de procédure sont connus**, et
ImmoSign appartient à Hektor. Si la procédure existe encore chez eux, le dossier de preuves se
retélécharge. **35 procédures = 35 appels**, à faire avec l'accord de Frédéric et le frein habituel.

⚠ **Les 4 fiches intactes sans zip prouvent qu'une partie de l'absence préexiste au bug** — tout
n'est pas imputable, et je ne l'impute pas.

## ⭐⭐⭐ Ce qui EST intact, et la preuve par les identifiants

Chaque signature porte un **numéro de procédure** ImmoSign. Ce numéro apparaît **deux fois** :
dans la fiche *(`metadata_json->'signature'->>'procedure_id'`)* et **dans le nom des fichiers du
coffre** *(`procedure-905.zip`, `preuves-905.zip`)*. Les deux listes sont donc comparables.

```
388 numeros de procedure trouves dans le COFFRE
388 sur 388 sont ENCORE portes par une fiche en base
  0 numero au coffre sans fiche  ->  AUCUNE SIGNATURE PERDUE
```

⭐ C'est la règle du projet *« on croise sur des IDENTIFIANTS, jamais sur des nombres »*. Un
comptage aurait pu coïncider par hasard ; **388 numéros qui se retrouvent un par un, non.**

⚠⚠ **MAIS CE CROISEMENT NE PROUVAIT QUE LA MOITIÉ, et c'est l'erreur que j'ai faite** : il
compare ce qui est **au coffre** à ce qui est **en base**. Il ne pouvait donc PAS voir ce qui
n'est **ni** au coffre **ni** en base — c'est-à-dire exactement les 29 dossiers de preuves
détruits. **Un croisement ne voit jamais ce qui a disparu des deux côtés à la fois.** Il a fallu
comparer des **taux entre populations** pour le découvrir *(section ci-dessus)*.

## L'état des signatures aujourd'hui, une ligne par état

| état | fiches | date de signature | n° de procédure | PDF signé |
|---|---|---|---|---|
| `to_send` *(jamais envoyé)* | 9 849 | 0 | 0 | 0 |
| ⭐ **`signed`** | **429** | **429** | **429** | **429** |
| `pending` *(en cours)* | 54 | 0 | 54 | 0 |

⭐⭐ **Les 429 signées sont COMPLÈTES** : chacune a sa date, son numéro de procédure **et** son
PDF signé. **Aucune n'est à moitié.** La plus ancienne est du 01/04/2026, la plus récente du
**31/08/2026** — *donc aucune signature n'a eu lieu après le déménagement du 11/09.*

## ⭐⭐⭐ POURQUOI elles ont survécu — et ce n'est pas de la chance

`pruneDeletedDocuments` saute explicitement les lignes signées, **depuis le 30 juin** :

```js
if (src === "hektor_immosign_signed") continue;                  // ligne synthetique signee
if (r.metadata_json && r.metadata_json.signed_document) continue; // archive signee conservee
```

Le commit qui a écrit cette purge, **`7e41fbd` du 30/06/2026 à 00:32**, s'appelle *« garde-fous
stricts »*, et son message dit :

> *« Ne touche jamais les lignes synthétiques signées ni les archives signées (`signed_document`) ;
> **ne purge rien si lecture vide (anti-suppression massive)**. »*

➡ **L'auteur avait prévu trois risques et protégé contre les trois.** Les signatures sont intactes
**grâce à une garde écrite quatre mois avant le bug.** C'est la meilleure nouvelle de cet audit.

## ⚠ Et le « etc. » : ce qu'une fiche remplacée perd VRAIMENT

Les fiches encore à l'ancienne adresse n'ont jamais été touchées : **elles sont le témoin
« avant »**. Comparaison :

| | fiches | un nom | fichier au coffre | archive locale | visibilité |
|---|---|---|---|---|---|
| **A. intactes** *(témoin avant)* | 28 343 | 100 % | 57,2 % | 100 % | 100 % |
| **B. recréées par le bug** | 163 556 | 100 % | **4,4 %** | 100 % | 100 % |
| C. nouveau domaine, nées avant | 736 | 100 % | 98,6 % | 100 % | 100 % |

**Ce qui est perdu, et c'est tout** :
1. ⛔ **l'identifiant interne de l'app** — 163 556 fiches ont un numéro neuf. **Irrécupérable** :
   l'ancien n'est écrit nulle part. Un lien posé vers l'ancien numéro ne retombe plus dessus.
2. ⛔ **la date de naissance de la fiche** — elle porte celle du remplacement, pas celle du
   document. C'est aussi ce qui en fait **le témoin du correctif**.

**Ce qui N'EST PAS perdu** : le nom, la visibilité, l'archive locale *(100 % des trois groupes)*,
et **les signatures**. Il n'existe **aucune table ni aucune colonne de signature** dans la base —
tout vit dans le blob de la fiche — ce qui rendait la perte possible en principe : **la garde du
30/06 est la seule raison qu'elle n'ait pas eu lieu.**

⚠ **Ce que je ne peux pas mesurer** : si une fiche avait, *avant* son remplacement, une
information que la nouvelle n'a pas reprise **et** que Hektor ne renvoie plus. Il n'existe aucun
instantané d'avant. Les deux pertes ci-dessus sont les seules **démontrables**.

---

# PARTIE 2 — COMMENT C'EST ARRIVÉ : sept maillons, et aucun n'est une négligence

### ⛔⛔⛔ 1. Le choix d'origine — **et le vrai numéro était À SIX LIGNES DE LÀ**

C'est le maillon le plus dur à regarder, et c'est Frédéric qui a demandé de le creuser. Le code
qui fabrique une entrée de document, `extractDocumentEntries` :

```js
entries.push({
  hektor_document_id: sha1(url),                                    // <- LA CLE : un hache de l'adresse
  document_name: safeFilename(crmLabel, technicalName),
  document_type: "document",
  visibility,
  source,
  console_url: url,
  technical_name: technicalName,
  transfer_name: transferName,
  hektor_uploaded_document_id: deleteMatch ? deleteMatch[1] : null, // <- LE VRAI NUMERO DE HEKTOR
  signature,
});
```

Le vrai numéro est lu **trois lignes plus haut**, dans la même ligne HTML, dans la même tour de
boucle :

```js
const deleteMatch = rowHtml.match(/deleteUploadedDocument\(\s*['"]([^'"]+)['"]/i);
```

➡ **Il était disponible au moment exact du calcul de la clé. Il est rangé dans la fiche. Et la
clé est un haché de l'adresse.** Aucune excuse de séquence : rien n'arrivait « plus tard ».

**Et il aurait marché**, mesuré sur toute la base :

```
avec un numero Hektor   190 840 fiches -> 190 840 cles distinctes -> 0 COLLISION
sans numero Hektor        1 795 fiches  (0,9 % -- la ligne n'a pas de bouton supprimer)
```

⭐⭐⭐ **LA MESURE DECISIVE**, sur les 17 paires survivantes de l'annonce 59578 — le même document
vu sous les deux domaines :

```
17 paires
17  NOTRE numero a change
17  le numero de HEKTOR est RESTE IDENTIQUE
 0  change        0  manquant
```

**Hektor nous donnait un numéro stable. Nous l'enregistrions. Nous avons choisi de hacher
l'adresse à la place.** Avec sa clé, l'incident entier était impossible.

⚠ **La seule défense possible**, et elle est faible : le numéro de Hektor est absent dans **0,9 %**
des cas. Une clé nulle 0,9 % du temps ne peut pas être LA clé seule — **mais elle pouvait l'être
avec un repli**, ce que n'importe quelle conception prudente aurait fait. Le haché de l'adresse
aurait été le repli, pas la règle.

⭐ **Pourquoi personne ne l'a vu** : un haché d'adresse *est* un identifiant stable, et il l'a été
**pendant des mois**. Il ne devient faux qu'au moment où l'adresse change. La question *« quelle
part de cette entrée peut changer sans que le document change ? »* n'a jamais été posée, **parce
que ça marchait.**

### 2. La garde du 30 juin *(commit `7e41fbd`)* — elle protégeait du MAUVAIS accident

Trois protections : lignes signées, archives signées, **et « ne rien purger si lecture vide »**.

⭐⭐⭐ **C'est LE maillon à comprendre.** La garde protège contre *« Hektor n'a rien répondu »*.
Elle ne peut pas protéger contre *« Hektor a parfaitement répondu, mais nous ne reconnaissons
plus ce qu'il dit »*. **La liste était pleine, complète, correcte — et entièrement
méconnaissable.** Le garde-fou a regardé la liste, l'a trouvée pleine, et a laissé faire.

➡ **Une garde contre un silence ne protège pas d'un malentendu.**

### 3. Le déménagement du 11/09 — un événement extérieur et légitime

`groupe-gti-immobilier.la-boite-immo.com` → `www.gti-immobilier.fr`. Rien d'anormal : c'est
Hektor chez lui. **Même fichier, même chemin, autre adresse, donc autre numéro.**

### 4. La réserve du 25/09 — **le défaut était écrit noir sur blanc**

`AUDIT_RATTRAPAGE_DOCUMENTS_2026-09-25.md`, §5 *« Les réserves, à traiter **AVANT** de relancer »*,
réserve 2 :

> *« La clé d'unicité d'un document est `(hektor_annonce_id, source, hektor_document_id)` — pas la
> nôtre. **Un changement de numéro Hektor recrée les documents en double au lieu de les
> reconnaître.** »*

⚠ **La réserve 1 du même paragraphe a été corrigée le jour même. La réserve 2 ne l'a jamais été.**
On traite ce qui bloque le lancement, et on abandonne le reste.

### 5. Le rattrapage lancé le 25/09 **à 12:57:07** — quelques heures après

```
41 231 travaux sync_console_documents depuis le 11/09
         TOUS poses par un SCRIPT (un seul par un humain)
   666 ces dernieres 48 h, soit ~330 par nuit
le premier : 2026-09-25 a 12:57:07
```

➡ **Ce n'est pas un balayage oublié dans un coin : c'est le rattrapage lui-même**, lancé le jour
où la réserve disait *« à traiter avant de relancer »*, **qui a usé le parc pendant 25 jours.**

### ⛔⛔ 5 bis. LE 07/10 — quelqu'un a VU l'ancien domaine chez nous, et a regardé au mauvais endroit

C'est la quatrième occasion manquée, et la plus troublante. `AUDIT_AUTONOMIE_COMPLET_2026-10-07.md`,
**ligne 278**, en pleine saignée *(le bug tournait depuis 11 jours)* :

> *« le bouton « Signature » vise probablement une adresse morte AUJOURD'HUI. Le paquet en ligne
> contient **6 fois l'ancien domaine** `groupe-gti-immobilier.la-boite-immo.com` (la variable
> `VITE_HEKTOR_BASE_URL` n'est pas posée sur Vercel). Selon la mémoire du projet, ce domaine
> **n'authentifie plus depuis le 11/09**. »*

➡ **L'observation est juste, datée, chiffrée.** Mais la question posée était *« est-ce qu'un
bouton pointe vers une adresse morte ? »*, et le regard est allé dans **le paquet du site**.

⚠ **La question voisine — « qu'avons-nous STOCKÉ qui contient cette adresse morte ? » — n'a pas
été posée.** Sa réponse, ce jour-là, était **28 363 lignes**, en train d'être détruites, et une
seule requête SQL l'aurait donnée.

### 6. ⚠⚠ Pourquoi RIEN ne l'a vu — *parce que rien n'a échoué*

Le compte rendu de chaque travail porte un champ **`pruned`** : le nombre de fiches supprimées.

**Mesure : `pruned` n'était lu par AUCUN contrôle, aucune alerte, aucun seuil.** Les seules
occurrences dans tout le projet sont dans le contrôle écrit aujourd'hui.

⭐⭐ Et surtout : **il n'y avait rien à alerter.** La lecture réussissait, les documents étaient
trouvés, les fichiers étaient rangés, le travail finissait en `done`. **Le chantier ④ « aucun
échec silencieux » est fini depuis le 11/10 et n'aurait rien attrapé ici : ce n'était pas un
échec.** C'était un succès qui faisait la mauvaise chose.

➡ **Un système qui ne surveille que ses échecs est aveugle à ses succès nuisibles.**

### 7. Pourquoi on ne l'a vu que sur **une** annonce

Le bug ne laissait pas de double : il **remplaçait**. Mesure : **17 doublons en base, tous sur
l'annonce 59578** — la seule dont la suppression est tombée en panne. **Partout ailleurs, la
preuve s'effaçait elle-même.** C'est pour ça que ça a tenu 25 jours sans être vu à l'œil.

⚠ **Et mon correctif les rend permanents** : mon verrou n° 1 refuse de supprimer une fiche dont le
chemin est dans la liste lue — c'est le cas des 17. **Elles ne partiront plus sans un geste
exprès.** L'annonce 59578 montre aujourd'hui **35 lignes pour 18 documents**.

---

# PARTIE 3 — ⚠⚠ CE QUE CET AUDIT A TROUVÉ EN PASSANT, et qui change une décision

## Le ménage du coffre, tel que je l'avais décrit, **aurait détruit des preuves de signature**

J'avais dit : *« supprimer tout ce qu'aucune fiche ne réclame, 7,8 Go »*. **C'était faux**, et la
raison est structurelle : les fichiers **compagnons** *(zip de preuves, procédure, PDF signé)* sont
rangés **dans le dossier de la fiche** mais ne sont **pas** la valeur de `storage_path`. Ils
paraissent donc orphelins **alors qu'ils appartiennent à une fiche bien vivante.**

Le bon critère n'est pas *« une fiche pointe-t-elle ce fichier ? »* mais **« le dossier qui le
contient est-il encore une fiche vivante ? »** — car le chemin porte l'identifiant de la fiche :

| verdict | fichiers | poids |
|---|---|---|
| ⛔ **compagnons d'une fiche VIVANTE — À GARDER** | **1 129** | **774 Mo** |
| ✅ déchet, documents *(la fiche n'existe plus)* | 5 074 | 7 086 Mo |
| ✅ déchet, photos | 132 | 98 Mo |

➡ **Le ménage rend 7,2 Go, pas 7,8** — et **il doit se faire sur l'identifiant du dossier, jamais
sur `storage_path`.** C'était exactement la vérification que j'avais annoncée comme *« non
faite »* : **elle était nécessaire, et elle a mordu.**

## La croissance du coffre, mois par mois

| mois | fichiers déposés | poids | cumul |
|---|---|---|---|
| mai → juillet | 68 | 110 Mo | 110 Mo |
| août *(la reprise voulue)* | 22 749 | 33 Go | 33 Go |
| septembre | 3 | 1,5 Mo | 33 Go |
| ⚠ **octobre** | **7 652** | **9,6 Go** | **42 Go** |

Dans les 9,6 Go d'octobre : **5,5 Go de recopies démontrées** *(même nom, même annonce, autre
dossier, jumeau antérieur)*, **3,0 Go de vrai travail** *(annonces jamais touchées)*, et **1,1 Go
que je ne sais pas attribuer — et que je n'attribue donc pas.**

---

# PARTIE 4 — Ce qui reste à faire, et ce que je n'ai pas mesuré

| | |
|---|---|
| ⏰ **demain matin** | `python phase2/checks/controle_domaine_documents.py` — il dit si le correctif mord |
| **A** — dédoublonner l'annonce 59578 *(17 lignes)* | petit, visible, et **nécessaire** puisque mon verrou les protège désormais |
| **B** — ménage du coffre *(7,2 Go)* | ⚠ **sur l'identifiant du dossier**, après une nuit de correctif |

**⛔ Non mesuré, et je ne le suppose pas :**
1. si une information autre que l'identifiant et la date de naissance a été perdue à un
   remplacement *(il n'existe aucun instantané d'avant)* ;
2. l'autre moitié de la **réserve 3 du 25/09** : ce balayage **n'a ni cadence ni arrêt sur un
   refus 403**, et il tourne chaque nuit. **Toujours pas corrigé** — et notre IP a déjà été
   bannie les 19-20/08 ;
3. ✅ **l'archive locale du serveur : mesurée, et moins grave que je ne le craignais.**

## L'archive locale du serveur — **~21 Go de dossiers abandonnés, pas 190**

Le chemin local *(`C:\Hektor\HektorConsoleDocuments\annonces\<n°>\documents\<ID-FICHE>\…`)* porte
lui aussi l'identifiant de la fiche. **Je craignais donc un dossier abandonné par remplacement,
soit ~163 000.** La mesure dit autre chose :

```
SUR LE DISQUE   650 659 fichiers   461,5 Go   (C: 290,5 Go libres sur 893,8)
  documents     207 817 dossiers   290,5 Go
  photos        441 626 dossiers   171,0 Go
EN BASE         192 626 fiches     ~269 Go annonces
```

| | |
|---|---|
| dossiers de documents sur le disque | **207 817** |
| fiches de documents en base | **192 626** |
| ➡ **dossiers abandonnés** | **≈ 15 191, soit ~21 Go** |

⭐ **Donc la grande majorité des remplacements n'a PAS recréé de dossier local** — cohérent avec
le fait que seules **4,4 %** des fiches recréées ont un fichier au coffre : le worker n'a
retéléchargé qu'une petite partie. **Le serveur a bien grossi, mais de ~21 Go, pas de 190.**

⭐⭐ **Et un recoupement rassurant** : les **441 626** dossiers de photos sur le disque collent aux
**441 627** photos comptées par l'audit des photos du même jour. **Aucun dossier de photo
abandonné** — ce qui confirme, par un autre chemin, que les photos n'ont pas le défaut.

## ⭐⭐⭐ LA LEÇON, et c'est la vraie réponse à « comment on a pu faire ça »

**Quatre personnes prudentes, quatre axes, et le défaut vivait entre les axes :**

| quand | qui regardait | ce qui a été vu | la question voisine, jamais posée |
|---|---|---|---|
| juin | **la clé** | un haché d'URL, déterministe | *quelle part de cette entrée peut changer ?* |
| 30/06 | **la purge** | 3 garde-fous écrits exprès | *et si la liste est pleine mais méconnaissable ?* |
| 11/09 | **la connexion** | 2 portes d'auth qui divergent, 4 workers tombés | *qu'avons-nous STOCKÉ qui contient ce domaine ?* |
| 07/10 | **le paquet du site** | 6 fois l'ancien domaine, « adresse morte » | *et en BASE, combien de fois ?* |

⚠ **Aucun de ces quatre regards n'est négligent** — le même fichier porte un commentaire de
12 lignes sur un lien orphelin, le risque de 403 et le bannissement d'IP. **La rigueur était
réelle ; elle était simplement pointée ailleurs.**

➡ **Une grosse erreur n'a pas besoin d'une personne distraite. Elle a besoin de plusieurs
personnes attentives, chacune sur son axe, et d'un défaut logé dans l'angle mort commun.**

⭐ Et la réserve du 25/09 est la cinquième occasion : **quelqu'un avait écrit le mécanisme exact,
dans les bons termes.** Elle n'a pas manqué d'être vue — elle a manqué d'être **une tâche**.

---

# PARTIE 5 — « PEUT-ON RÉCUPÉRER LES 29 PREUVES ? » — audit du 21/10, lecture seule

*Frédéric : « vas-y ». Aucun appel à Hektor, aucune écriture. Verdict : **OUI, mais
ça n'arrivera pas tout seul.**

## ⭐⭐⭐ D'abord : la destruction est CONFIRMÉE, et par une meilleure mesure

Ma première preuve *(24,6 % contre 4,0 %)* était **confondue par l'âge** : le zip manque
beaucoup plus sur les vieilles procédures, quel que soit l'état de la fiche *(20,9 % en
mars-avril contre 4,1 % en juillet+)*. Il fallait donc comparer des fiches **du même âge** :

| ancienneté | état de la fiche | signés | sans zip | taux |
|---|---|---|---|---|
| **anciennes** *(proc < 400)* | ⛔ **recréée par le bug** | 32 | **29** | ⛔ **90,6 %** |
| **anciennes** | **jamais touchée** | 46 | **0** | ✅ **0,0 %** |
| anciennes | origine, nouv. domaine | 84 | 1 | 1,2 % |
| récentes *(≥ 400)* | recréée par le bug | 110 | 6 | 5,5 % |
| récentes | jamais touchée | 53 | 4 | 7,5 % |

⭐⭐ **29 sur 32 contre 0 sur 46, à âge égal.** Ce n'est pas l'ancienneté : c'est le bug. Et il
n'a touché **que** les procédures de **mars à mai** — sur les récentes, aucune différence.
⚠ **Le chiffre de 29 est donc exact, mais ma première démonstration ne valait rien.**

## ⭐ Ce qui rend la récupération possible

```
Console/console_job_worker.js:5306
  { key: "proofs_zip", filename: `preuves-${procId}.zip`,
    url: `${XMLRPC_URL}?mode=ImmoSign-downloadProofsByProcedure&procedureId=${procId}` }
```

**Un dossier de preuves se demande avec le seul numéro de procédure.** Et le commentaire du
code écrit : *« Ils sont **IMMUABLES** une fois la procédure créée »*.

Les 29 fiches ont tout ce qu'il faut :

```
les 29                            29
avec un modelo immosign           29   <- la fonction s'executera (sinon elle sort aussitot)
le modelo porte la procedure       29
se souviennent du chemin local     29   <- mais le fichier n'y est plus -> elle RETELECHARGERA
se souviennent du chemin coffre     0   <- ils n'y ont jamais ete remontes
```

⭐⭐ **Et le garde-fou de la fonction joue en notre faveur** : elle ne saute le
téléchargement que *si la copie locale est lisible*. **Mesure : 0 zip de preuves sur tout le
serveur** *(recherche de `preuves-*.zip` et `procedure-*.zip` dans tout
`C:\Hektor\HektorConsoleDocuments` : zéro)*. Donc la condition de saut est fausse, et elle
retentera. ⚠ **Et un échec est propre** : si Hektor renvoie une page HTML au lieu d'un ZIP,
le code refuse de stocker un faux ZIP.

## ⚠⚠ CE QUI L'EMPÊCHE D'ARRIVER TOUT SEUL — et c'est le vrai résultat de cet audit

`persistImmoSignCompanionFiles` n'a **qu'un seul appelant** : la synchro des documents
*(l. 6166)*. Or :

```
les 26 annonces concernees : TOUTES ABSENTES de app_dossier_current
  11682 23373 36452 39707 48017 54773 54806 58908 59625 61578 61621 61650 61654
  61667 61779 61802 61961 62024 62044 62055 62104 62153 62163 62174 62268 8377
```

⚠⚠ **Absentes de l'index vivant = vendues, closes ou archivées** *(voir
[[bien-vendu-clos-nest-plus-dans-dossier-current]])*. **Le balayage nocturne ne les touchera
jamais.** Les preuves ne reviendront donc **pas** d'elles-mêmes : il faut une **action
délibérée sur 26 annonces nommées.**

⭐ **Et c'est précisément là que ça compte** : ce sont des **mandats signés de biens vendus**
— la piste d'audit d'une signature électronique sur une vente aboutie.

## Ce que coûterait la récupération

| | |
|---|---|
| annonces à resynchroniser | **26** |
| appels à Hektor | ~26 pages + jusqu'à 58 ZIP = **~85**, contre un quota de 13 000–17 000 |
| où atterrira le zip | **sur le serveur**, pas au coffre — `shouldKeepCloud` est faux pour un bien vendu, et c'est **approprié** |
| écriture en base | le `metadata_json.immosign_files` des 29 fiches |

⛔ **Rien de tout cela n'est fait : l'accord de Frédéric est obligatoire** *(appels Hektor +
écriture en production)*, et le chemin exact *(un type de travail dédié, ou un rejeu de la
synchro documents sur ces 26)* **reste à trancher avec lui** — un périmètre ne se décide pas seul.

⚠ **Non mesuré** : qu'ImmoSign serve encore ces 29 procédures. Le code dit « immuables » et
388 autres répondent, mais **je ne l'ai pas vérifié sur ces 29** — ça demanderait un appel à
Hektor, donc son accord. **C'est le seul vrai inconnu, et il se lève avec UN SEUL essai.**
