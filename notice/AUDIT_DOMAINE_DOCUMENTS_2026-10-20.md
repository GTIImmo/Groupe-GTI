# Le domaine des documents — audit, mesures, et les deux correctifs

*20/10/2026. Frédéric a demandé de reprendre la main sur le chantier ouvert par
`PROMPT_CHANTIER_DOMAINE_DOCUMENTS_2026-10-20.md`, d'auditer le code **et surtout les notes
de l'époque, « sans s'arrêter à la première »**, puis d'expliquer la solution.*

---

## ⚠⚠ 1. CE QUE LES NOTES DE L'ÉPOQUE DISENT — et c'est le vrai choc

**`AUDIT_RATTRAPAGE_DOCUMENTS_2026-09-25.md`, §5 « Les réserves, à traiter AVANT de relancer »,
réserve 2 :**

> *« La clé d'unicité d'un document est `(hektor_annonce_id, source, hektor_document_id)` — pas
> la nôtre. **Un changement de numéro Hektor recrée les documents en double au lieu de les
> reconnaître.** »*

➡ **Le défaut était écrit le 25/09. La première vague est du 26/09 — le lendemain.**
Vérifié : **cette réserve n'a jamais été traitée ni même re-citée** en 25 jours. La réserve 1 du
même paragraphe, elle, a été corrigée **le jour même**.

⚠ **La réserve 3 non plus n'a pas été traitée** : *« la détection n'a ni cadence ni arrêt sur 403
[…] le jour où le retard est résorbé, le balayage quotidien lit 13 068 pages à pleine vitesse »*.
**C'est la même famille de risque que le coût Hektor mesuré ci-dessous.**

## 2. La cause, confirmée dans le code

```js
Console/console_job_worker.js:1075     hektor_document_id: sha1(url)
```

Le numéro d'un document est le **sha1 de son adresse complète**, domaine compris. Le portail a
déménagé le 11/09 *(mémoire `hektor-bascule-domaine-gti-immobilier`)*. **Même fichier, autre
numéro.** Le worker crée un double, et `pruneDeletedDocuments` supprime l'ancienne fiche — son
**seul** garde-fou de masse étant *« liste vide »*.

## ⭐⭐ 3. La preuve décisive : le même fichier sous les deux domaines

```
17 paires  meme annonce + meme chemin, sous les DEUX domaines
17 sur 17  LE NUMERO A CHANGE
17 anciennes portent le fichier · 1 seule neuve en porte un
```

⭐ Une seule annonce le montre *(59578)* — **parce que c'est la seule dont la suppression est
tombée en panne.** Partout ailleurs l'ancienne fiche a déjà disparu.

## 4. L'ampleur, et le coût que le prompt ne chiffrait pas

| | |
|---|---|
| depuis le 11/09 | **2 330 travaux · 15 403 fiches supprimées · 17 120 recréées** |
| **avant** la bascule *(2 mois)* | **18 travaux · 20 fiches** — le rythme normal |
| ces dernières 48 h | **33 annonces · 625 fiches** |
| reste à risque | **28 363 fiches · 6 199 annonces** |
| ⚠⚠ **fichiers RETÉLÉCHARGÉS chez Hektor** | **17 118** *(dont 5 734 remontés au cloud)* · **781 ces 48 h** |

⭐⭐ **Le coût Hektor est le point le plus grave, et il n'était pas chiffré.** Le mur de Hektor est
un **quota de VOLUME** *(13 000–17 000 par période)* et notre IP a été **bannie les 19-20/08**.
Ce défaut a donc déjà consommé l'équivalent d'une période entière, en silence.

## ⭐ 5. Ce qui est VRAIMENT perdu — mesuré, pour répondre à l'inquiétude

```
2 330 annonces erodees · 17 150 documents aujourd'hui
17 148 sur 17 150 portent leur FICHIER        99,99 %
     0 annonce n'a perdu tous ses documents
   207 fiches SIGNEES toujours presentes
     2 fiches sans fichier -- les seules
```

➡ ⭐⭐ **Aucun document n'est perdu.** Les fiches ont été **remplacées**, pas effacées.
**Ce qui se perd** : l'**identifiant de l'app** *(règle « un numéro ne se perd jamais »)* et
**7,4 Go de DOUBLONS** dans le coffre — **du ménage, pas une récupération.**

⚠ **Non mesurable sans un « avant »** : combien de dates `sent_at` / `signed_at` ont disparu.
Elles sont rares partout *(487 sur 192 629 fiches)* et **245 survivent** sur les annonces touchées.
**Je ne donne pas de chiffre que je n'ai pas.**

## ⭐⭐⭐ 6. La mesure qui décide de la solution

```
ancien domaine   28 363 fiches ->  28 363 cles distinctes -> 0 collision
nouveau domaine 164 229 fiches -> 164 229 cles distinctes -> 0 collision
                ------                                      ----------
TOTAL           192 592 fiches                              0 COLLISION
```

**Le chemin sans l'hôte est une clé parfaite sur les 192 592 fiches, des deux côtés.**
*(mesuré sur la clé entière : annonce + source + chemin, interrogation comprise)*

---

## 7. Les deux correctifs — et pourquoi j'ai inversé l'ordre proposé

Le prompt proposait : **migrer les 28 000 fiches d'abord**, le garde-fou ensuite, la
reconnaissance par chemin en dernier.

⭐ **Le point qui change tout : les fiches ne s'abîment pas en dormant. Elles s'abîment au moment
où l'annonce est resynchronisée.** Donc réparer la synchro répare tout — **chaque annonce se
remet d'aplomb à son prochain passage, sans migration de masse.**

### ⭐ A — la reconnaissance par chemin *(le vrai correctif)*

`reconcilierParChemin()`, appelée **avant** l'upsert : si une fiche existante porte **le même
chemin** qu'une entrée lue, sous un autre numéro, c'est **le même document** → on la **re-clé par
un PATCH** *(numéro + adresse)*, et l'upsert la retrouve ensuite normalement.

⚠ **Pourquoi un PATCH et pas une simple adoption** : la base cherche le conflit sur
*(annonce, source, numéro)*. Laisser l'upsert écrire le nouveau numéro en reprenant l'`id`
donnerait un **409 `app_console_document_pkey`** — exactement le bug corrigé le 19/10.

⭐ **Elle se branche comme une troisième sœur** de `adoptExistingImmoSignRows` et
`adoptExistingAppRows`, au même endroit. Et `loadExistingDocuments` charge déjà toutes les
fiches : **la reconnaissance ne coûte aucun appel de plus.**

### B — le garde-fou du prune, **à deux niveaux**

**⭐ Niveau 1, EXACT** : ne jamais supprimer une fiche dont **le chemin est présent** dans la liste
qu'on vient de lire. C'est la signature même du changement de domaine — **une identité, pas une
statistique.**

**⚠ Niveau 2, chiffré** — le filet pour l'inconnu. **Et son seuil a dû être recalibré :**

| seuil | attrape du bug | faux positifs |
|---|---|---|
| ≥3 et **>** moitié *(proposé)* | **1,2 %** | 0 |
| ≥3 et **≥** moitié | 45,5 % | 0 |
| ⭐ **≥2 et ≥ moitié** *(retenu)* | **58,7 %** | **0** |
| ≥2 et ≥ 40 % | 69,1 % | **1** |

⭐⭐ **Le seuil proposé n'aurait attrapé que 1,2 % des cas**, pour une raison arithmétique : dans
un remplacement on supprime N et on recrée N, donc la part est **exactement la moitié**, jamais
*« plus de la moitié »*. **Il ratait d'un cheveu.**

⚠ **Un seuil chiffré n'attrapera jamais tout : c'est un filet, pas le correctif.**

### C — la migration en masse : **devenue optionnelle**

Avec A, chaque annonce se répare à son passage. La migration ne sert qu'à **ne pas attendre** —
et elle ne protégerait de rien pour l'avenir.

## 8. L'épreuve — `Console/test_domaine_documents.js`

**13 contrôles verts**, sur **le code réel** *(fonctions découpées dans le worker et montées avec
un faux Supabase qui applique la vraie contrainte d'unicité — même technique que
`test_adoption_ligne_app.js`)* :

```
(1)  LA PREUVE D'ABORD : les trois pieces sont dans le worker  (sinon sortie 2)
(2)  le chemin est le MEME sous les deux domaines
(3)  et il n'invente rien : vide, nul, texte -> null
(4)  ⭐ LA FICHE EST RE-CLEE   (5) ⭐⭐ ET ELLE GARDE SON id ET SON FICHIER
(6)  le journal le DIT          (7) elle NE re-cle PAS vers un numero deja pris
(8)  une fiche sans adresse lisible n'est jamais touchee
(9)  les sources qui ne sont pas hektor_console sont epargnees
(10) ⭐⭐ NIVEAU 1 : ce qui est toujours la n'est PAS supprime
(11) ⭐ NIVEAU 2 : une suppression EN BLOC est refusee   (12) et c'est ECRIT
(13) ⚠⚠ TEMOIN INVERSE : une VRAIE suppression isolee passe TOUJOURS
```

⭐ Le **(13)** est le plus important : *un garde-fou qui bloque tout protège de tout, y compris de
ce qu'on veut.*

**Les 8 essais documents existants restent verts**, dont `test_adoption_ligne_app.js` — ⚠ **mon
changement avait cassé son harnais** *(il montait `upsertConsoleDocuments` sans ma fonction)* :
2 tranches ajoutées, **9 lignes, aucune restructuration**.

## ⭐⭐ 8 bis. CE QUE LA POSE A APPRIS, LE SOIR MÊME

### ⭐⭐⭐ La réserve 3 du 25/09 est RÉPONDUE : c'est un SCRIPT, et il part du 25/09

*« Ce qui déclenche la resynchro d'une annonce » était la dernière inconnue. La base le dit :

```
41 231 travaux sync_console_documents depuis le 11/09
         TOUS poses par un SCRIPT (requested_by vide) -- un seul par un humain
   666 ces dernieres 48 h, soit ~330 par nuit
le premier : 2026-09-25 a 12:57:07
```

⚠⚠ **Le premier travail est du 25/09 à 12:57 — le jour même où la réserve 2 était écrite.**
Le rattrapage a été lancé quelques heures après qu'on ait écrit *« à traiter **avant** de
relancer »*. Ce n'est pas un balayage oublié : **c'est le rattrapage lui-même qui a usé le parc.**

⭐ **Et c'est une bonne nouvelle pour l'épreuve** : le script repasse **chaque nuit**. Le
correctif sera donc exercé sur ~330 annonces sans qu'on ait rien à provoquer — **aucun risque
à prendre pour le prouver.**

### ⚠ Un geste d'écran que le commentaire promet et que personne n'appelle

`apps/hektor-v1/src/lib/api.ts:8624` déclare `createSyncConsoleDocumentsJob`, avec ce
commentaire : *« Synchro documents à la demande (read-through) […] **Déclenché en silence à
l'ouverture de l'annonce.** »* — **elle n'a AUCUN appelant dans tout le front.** Le geste promis
n'existe pas. *« Un commentaire de code n'est pas une mesure »*, une fois de plus.
⚠ **Noté, non traité** : ce n'est pas le périmètre de ce correctif, et ça ne se décide pas seul.

### ⭐⭐ LE TÉMOIN DE LA RÉPARATION, et il était déjà dans la base

**Une fiche re-clée garde sa date de naissance ; une fiche supprimée puis recréée en porte une
neuve.** Donc il suffit de regarder `created_at` :

| côté | fiches | nées **avant** le 11/09 | nées **après** |
|---|---|---|---|
| encore à l'ancien domaine *(intactes)* | **28 363** | **28 363** | **0** |
| passées au nouveau *(resynchronisées)* | 164 229 | **716** | **163 513** |

⭐⭐⭐ **163 513 fiches sur 164 229 ont été RECRÉÉES, pas reconnues** — seules **716** (0,4 %)
avaient survécu. C'est la mesure la plus directe du dégât, **et c'est le contrôle de demain** :
ce 716 doit monter, et il ne peut que monter.

### La pose, et le contrôle qui la juge

⏰ **20/10 à 20:30:46-47 : les QUATRE services ont redémarré** *(prouvé deux fois — la ligne
« service stopping / service starting / worker started pid=16352 kind=documents » dans
`Console/logs/console_worker_service_documents.log`, et la date de création des 4 processus,
toutes postérieures à l'écriture du code à 19:49:37)*. ⭐ Ce redémarrage général solde au
passage la note « 3 services sur 4 tournent sur du code ancien ».

⚠ **Le premier redémarrage est allé sur `Admin`, pas sur `Documents`** — et seule la mesure l'a
vu : le journal d'`admin` portait la coupure à 20:16:41, celui de `documents` n'en avait aucune.
*On exige la preuve du succès, jamais l'absence d'erreur.*

```bash
python phase2/checks/controle_domaine_documents.py
```

**7 points, sortie 0 / 1 / 2**, dont le témoin ci-dessus, les deux garde-fous lus au journal, le
coût Hektor, et — le plus important — **le témoin inverse : les suppressions légitimes
passent-elles toujours ?** ⚠ Il a été lancé le soir de la pose : il rend les mêmes nombres que
les requêtes SQL de cet audit *(164 229 / 716 / 28 363)*, **donc il mesure bien la bonne chose.**

## ⛔ 9. Ce qu'il reste à faire, et ce que je n'ai pas mesuré

**À faire :** pousser · ⏰ **redémarrer `HektorConsoleWorkerDocuments`, file vide** *(0 pending ET
0 running)* · puis regarder la nuit suivante : **`pruned` doit tomber à presque rien**, et le
journal doit montrer *« reconnus par leur CHEMIN et re-clés »*.

**Non mesuré, et je ne le suppose pas :**
1. le nombre de dates de signature réellement perdues ;
2. **les photos** : même défaut ou non *(leur identifiant vient du CDN, pas de la page)* ;
3. ✅ **répondu ci-dessus** : un script, ~330 annonces par nuit, depuis le 25/09 à 12:57.
   ⚠ Reste ouverte, elle, l'autre moitié de la réserve 3 : **ce balayage n'a ni cadence ni
   arrêt sur 403** ;
4. les **7,4 Go de doublons** du coffre : du ménage, à faire **après** avoir vu A tenir une nuit.

⚠ **Coordination** : une conversation a été ouverte sur ce chantier avec le prompt du 20/10.
**Ces correctifs sont A et C de son plan, dans l'ordre inverse** — et sa migration *(A chez lui)*
devient optionnelle. **À lui dire avant qu'il ne pose la migration.**
