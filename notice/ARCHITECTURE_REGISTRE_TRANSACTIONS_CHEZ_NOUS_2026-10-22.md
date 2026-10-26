# LE REGISTRE DES TRANSACTIONS : tout chez nous au clic — audit et architecture proposée

**22/10/2026 · chantier ⑧ · LECTURE SEULE, RIEN N'EST CODÉ.**
Demande de Frédéric : *« fais un audit ultra pointu sur le registre des transactions, chaînage, doublure, run etc.
pour bien comprendre et ensuite propose-moi une architecture pour que tous les champs soient chez nous
immédiatement, sauf cas particuliers (ID Hektor etc.), sans avoir besoin d'attendre le retour d'Hektor »*.

> Audit limité à l'objet **transaction** (offre, compromis, vente). Sources lues : les 7 RPC d'affaire en entier,
> `affaire_ledger.py` (refresh, adoption, « le silence ne gagne pas », chaînes, push), `run_full_pipeline.ps1`
> (l. 880-1335), `registre_depuis_console.py`, `magasin_affaire_app.py`, le worker (création, preuve, verdict,
> report, retour arrière), le front (`api.ts`). Décisions relues : `contrat_autorite.py` (3.3, « le gel »),
> `AUDIT_CONTRAT_AUTORITE_AFFAIRE_2026-10-22.md`, ⑦-6.

---

## 1. CE QUI EXISTE — le chemin d'une transaction

```
AU CLIC (l'app)                         RPC app_change_annonce_status_optimistic
   ligne au registre app_affaire_ledger, numero de l'app >= 1 000 000
   colonnes posees : acquereur(s), numero de mandat, etat 'en_cours', montant, date,
                     la chaine (app_chaine_pour), la charge entiere dans payload_json
   carnet app_affaire_champ_app : 13 champs, origine creation_app
   travail change_hektor_annonce_status

LE WORKER (secondes)                    console_job_worker.js
   cree chez Hektor, PROUVE qu'une transaction NOUVELLE est apparue (prouverTransactionCreee)
   pose tout de suite le numero Hektor sur la ligne (poserIdTransactionSurAffaire)
   ⚠ ne compare PAS les valeurs a la creation -- seulement a la modification
     (prouverTransactionModifiee -> reporterAuRegistre -> marquerLeCarnetRestant)

LA NUIT (05:00)
   l. 902   la DOUBLURE : app_affaire_ledger descend de Supabase (__sb) juste avant,
            pour adopter les lignes nees dans l'app (par le triplet annonce/genre/n° Hektor)
   l. 912   affaire_ledger.py
              1. relit le miroir Hektor (offres, compromis, ventes)
              2. UPSERT : 20 colonnes REECRITES par la valeur de Hektor
              3. « le silence ne gagne pas » : marque absentes celles que Hektor ne rend plus,
                 SAUF les lignes de l'app, celles qui ont un carnet ou un travail en cours
              4. RECALCULE TOUTES LES CHAINES (0,09 s)
              5. pousse le registre local vers Supabase (SELECT *, sauf 5 colonnes de classe A)
   l. 1253  registre_depuis_console.py : notaires, taux vendeur, unites, depuis la console
            (une saisie humaine, notaires_origine = 'saisie', n'est jamais ecrasee)
   l. 1318  magasin_affaire_app.py : descend le carnet en local
   l. 1321  appliquer_contrat_affaire.py : DORMANT (CHAMPS_APP_AFFAIRE vide depuis le 16/09)
```

### Les colonnes du registre, rangées par qui en décide *(44 colonnes en base)*

| famille | colonnes | qui écrit | la nuit |
|---|---|---|---|
| **identité, à nous** | `app_affaire_id`, `app_dossier_id`, `app_contact_id`, `app_chaine_id` | l'app / le run | protégées (absentes du `DO UPDATE`, ou `COALESCE`) |
| **identifiants Hektor** | `hektor_affaire_id`, `hektor_annonce_id`, `hektor_mandat_id`, `hektor_acquereur_id`, `present_in_hektor` | Hektor (le worker pose le n° tout de suite) | réécrites — **c'est le cas particulier, normal** |
| **classe A, à nous seuls** | `taux_honoraires`, `notaire_id`, `honoraires_entree_app`, `honoraires_sortie_app`, `charge_commission_app` | l'app | **protégées** (jamais poussées, jamais réécrites) |
| **partagées : saisies dans l'app ET connues de Hektor** | `state`, `montant`, `date`, `date_acte`, `sequestre`, `date_fin_retractation`, `jours_validite`, `prix_net_vendeur`, `honoraires_entree`, `honoraires_sortie`, `numero_mandat`, `acquereur_json`, `acquereurs_json`, `mandants_json`, `notaires_json`, `notaire_acquereur_id`, `notaire_mandant_id` | l'app au clic (en partie), puis Hektor | ⛔ **RÉÉCRITES chaque nuit par Hektor** |
| **Hektor seul** | `propositions_json`, `commission_agence`, `payload_json`, `mandat_origine`, `unites_*`, `taux_honoraire_entree` | Hektor / la console | réécrites — normal |

⭐ **Le problème tient dans la 4ᵉ ligne.** Pour ces champs, la nuit **remplace** la colonne par la valeur de Hektor
**même si Hektor n'a pas encore reçu la nôtre**. C'est pour ça que le projet a dû ranger notre saisie **à côté**,
dans le carnet : sinon elle disparaissait au premier run (mesuré le 01/09).

### Ce que la création écrit au clic, champ par champ

| saisi dans la modale | colonne du registre au clic | carnet |
|---|---|---|
| montant / prix | ✅ `montant` | ✅ |
| date | ✅ `date` | ✅ |
| acquéreur principal + co-acquéreurs | ✅ `acquereur_json`, `acquereurs_json` | ❌ |
| n° de mandat | ✅ `numero_mandat` | ✅ |
| date d'acte, séquestre, net vendeur, honoraires acquéreur / vendeur, jours de validité | ❌ **rien** | ✅ |
| jours de rétractation | ❌ (`date_fin_retractation` vide) | ✅ |
| taux d'honoraires, notaire de l'acquéreur | ❌ (`taux_honoraires`, `notaire_id` restent vides) | ✅ |
| **notaire du vendeur** | ❌ | ❌ **nulle part** |
| **mandants** | ❌ | ❌ **nulle part** |

➡ **Au clic, 4 champs sur 15 sont dans le registre.** Les autres attendent la nuit (si Hektor les a pris), ou
vivent au carnet seulement, ou sont perdus.

---

## 2. LES DÉFAUTS TROUVÉS

| | défaut | preuve |
|---|---|---|
| **D1** | la nuit réécrit les champs partagés **sans savoir** si Hektor a reçu notre valeur | `affaire_ledger.py`, `DO UPDATE SET` : 20 colonnes, aucune condition |
| **D2** | la création ne pose que 4 champs au registre | RPC, `INSERT` : `montant`, `date`, acquéreurs, mandat |
| **D3** | la création n'a **aucun contrôle au retour** | `marquerLeCarnetRestant` n'a qu'un appelant, la modification. Carnet : 17 lignes, **0 verdict** |
| **D4** | notaire du vendeur et mandants saisis, **gardés nulle part** | charge du travail seulement (`api.ts:10676`) |
| **D5** | ⚠ le contrat dormant est **placé trop tard** : l. 1321, APRÈS le push du registre (l. 912) et APRÈS le calcul des chaînes. Allumé, il écrirait en local une valeur qui ne monterait qu'à la nuit suivante, sur des chaînes déjà calculées | c'est **exactement le gel mesuré le 16/09** (« le contrat reposait sa date TROIS MINUTES après le calcul des chaînes »). ⚠ Le commentaire du run dit « AVANT le push » : je n'ai pas trouvé de second envoi du registre après l. 1321 |
| **D6** | l'état (refus, annulation, suppression) n'est jamais au carnet : défait par le worker si Hektor échoue, réécrit la nuit | audit « l'écriture meurt », plus haut dans la note ⑧ |
| **D7** | modifier une transaction **sans numéro Hektor** est refusé | `modification_sans_numero_hektor` |
| **D8** | deux copies de la règle de chaîne : SQL au clic (`app_chaine_pour`) et Python la nuit (`recalculer_les_chaines`). La nuit gagne | « elle doit rester identique » (commentaire de la RPC) ; ⚠ `APP_CHAINAGE_V2` n'existe que côté Python |
| **D9** | le cycle d'affaires du **registre des mandats** (`affaires_detail_json`) n'est refait que la nuit | `app_mandat_register_current`, refait à chaque push. ⚠ Non vérifié à l'écran |

**La mesure qui décide de tout** — qui crée les transactions aujourd'hui :

```
            nees dans l'app   nees chez Hektor
aout             315                39        <- les essais du chantier (24933, 62774)
septembre         15             1 706
octobre            1                70
```

⭐ **Les négociateurs saisissent encore leurs transactions DANS HEKTOR.** C'est la raison du « gel » :
une valeur de l'app qui gagnerait **toujours** masquerait ce qu'ils corrigent ensuite chez Hektor.

---

## 3. L'ARCHITECTURE PROPOSÉE — « le registre porte tout au clic, Hektor confirme »

### La règle, en une phrase

> **Au clic, tout entre dans le registre. La nuit ne remplace un champ que lorsque Hektor a CONFIRMÉ notre
> valeur — ou lorsque personne dans l'app n'attend rien sur ce champ.**

C'est **la règle du contact et de l'annonce** (8a) : on écrit chez nous, on garde la saisie **tant que Hektor
ne l'a pas prouvée**, et on contrôle au retour.

### ⭐ Pourquoi ce n'est PAS le gel

```
LE GEL (avant le 16/09)          l'app gagne TOUJOURS, pour toujours
                                 -> une correction faite ensuite dans Hektor est MASQUEE
                                 -> et le contrat reposait la valeur APRES les chaines

CE QUI EST PROPOSE               l'app gagne SEULEMENT TANT QUE Hektor n'a pas confirme
                                 -> des que le worker a PROUVE l'arrivee, la protection tombe :
                                    la nuit reprend la valeur de Hektor, qui est la notre
                                 -> une correction faite ensuite dans Hektor est reprise
                                 -> un desaccord (« conflit ») n'est pas masque : il SONNE
                                 -> et la protection joue AVANT les chaines
```

Les **70 transactions d'octobre créées dans Hektor** n'ont aucune saisie en attente : **rien ne change pour
elles**, la nuit fait exactement ce qu'elle fait aujourd'hui.

### Et le carnet, alors ?

**L'écran et le registre portent tout.** Le carnet ne sert plus à *montrer* notre valeur. Il devient ce que sont
`app_contact_saisie_modif` pour le contact et `app_annonce_saisie_naissance` pour l'annonce : **la liste
d'attente**, en coulisse — *« ces champs, Hektor ne les a pas encore confirmés : nuit, n'y touche pas »*.
Une ligne y entre au clic ; elle en sort quand le worker a prouvé l'arrivée. Les champs de classe A, eux,
n'y passent même pas : ils ont déjà leur colonne protégée.

### Les cinq pièces

| | pièce | où | ce qu'elle fait |
|---|---|---|---|
| **R1** | **naître complet** | RPC de création (+ modification) | écrit **les 15 champs** dans leurs colonnes au clic (date d'acte, séquestre, net vendeur, honoraires, validité, fin de rétractation = date + jours, taux, notaires des deux côtés avec `notaires_origine = 'saisie'`, mandants) ; met **tous les champs partagés** en attente au carnet, y compris notaire du vendeur, mandants, acquéreurs. Derrière un interrupteur `app_setting` (`affaire_nait_complete`), éteint au départ |
| **R2** | **la nuit respecte l'attente** | `affaire_ledger.py`, **entre l'UPSERT et le calcul des chaînes** | descend le carnet juste avant (comme la doublure, l. 902), puis repose sur le registre local **les seuls champs encore en attente**. Les chaînes et le push partent donc avec notre valeur. Derrière un interrupteur du run (éteint au départ). Remplace le contrat dormant de la l. 1321, mal placé (D5) |
| **R3** | **le contrôle au retour de la création** | worker | après la création, relire chez Hektor, reporter au registre ce qu'il a retenu, poser le verdict champ par champ (le code de la modification existe : on le rebranche). « arrivée » → la ligne sort de l'attente. « conflit » → elle reste, et elle sonne |
| **R4** | **la sentinelle et l'écran** | `check_gti_health.py` + fiche | `data.affaire_ecart` (comme `data.contact_modif_ecart`) ; à l'écran, un champ en attente ou en conflit se signale |
| **R5** | **l'état aussi** | RPC du geste + worker + R2 | l'état (refus, annulation, suppression) entre en attente comme les autres champs ; la nuit le respecte tant que Hektor n'a pas confirmé |

**Restent à part, pour la coupure** (déjà notés, décision de Frédéric) : T1 (le worker défait l'état quand Hektor
ne répond pas, décision du 29/08) et T3 / D7 (modifier sans numéro Hektor).

### Ce que ça pourrait casser ailleurs

| | risque | parade |
|---|---|---|
| **le chaînage** | R2 change la valeur sur laquelle la nuit calcule les chaînes, pour les seules transactions en attente | c'est voulu : la chaîne est calculée sur ce que l'écran montre. Mesurer avant/après par le rejeu existant (fidèle à 100,00 %) |
| **deux règles de chaîne** (D8) | si `APP_CHAINAGE_V2` est allumé, `app_chaine_pour` (SQL) n'a pas la v2 | à trancher avant d'allumer la v2 — indépendant de R1-R5 |
| **une attente qui ne finit jamais** | une ligne qu'aucun travail n'enverra (`origine = 'classeur'`, saisie sans envoi) resterait protégée à vie → **c'est le gel** | R2 ne protège QUE les lignes nées d'un geste qui a un travail (`creation_app`, `modification_app`, geste d'état), et seulement sans verdict « arrivée ». ⚠ **À trancher par Frédéric** : une durée maximale ? |
| **le classeur** (chantier en attente de ⑧) | ses corrections vont au carnet `origine = 'classeur'` | compatible, à condition de les exclure de R2 (ligne précédente) |
| **« le silence ne gagne pas »** | une ligne au carnet empêche de marquer la transaction absente | déjà le cas aujourd'hui ; R1 en ajoute quelques-unes par jour |
| **l'adoption par la doublure** | inchangée : elle se fait par le n° Hektor, que le worker pose tout de suite | rien |
| **le push du registre** | il enverra notre valeur pour les champs en attente | c'est le but ; le conflit d'index (`retirer_les_lignes_en_conflit`) est inchangé |
| **les notaires de la console** (l. 1253) | ils écrasent les notaires… sauf `notaires_origine = 'saisie'` | ⚠ **corrigé au §4 B** : `'saisie'` fige pour toujours, c'est le gel. Le notaire passe par l'attente (R2) |
| **les 4 services worker** | R3 touche le worker | redémarrage par Frédéric, file vide (0 pending, 0 running) |

### L'ordre proposé *(à décider par Frédéric)*

```
R1  naitre complet          la base seule ; additif ; interrupteur eteint  -> essai reel sur 62774
R3  controle au retour      le worker                                     -> preuve : un verdict pose
R2  la nuit respecte        le run ; interrupteur eteint                  -> rejeu des chaines avant/apres
R4  sentinelle + ecran
R5  l'etat
```

**Comment on reviendra en arrière** : chaque pièce a son interrupteur ou son patch inverse, comme 8a.
**Comment on vérifiera** : une transaction d'essai sur 62774, ses 15 champs au registre **à la seconde**,
puis le lendemain matin **intacts**, chaînes comprises, et le verdict « arrivée » sur chacun.

---

## 4. ⚠ RELECTURE AVANT R1 — les particularités des champs *(22/10, Frédéric : « reprends les notes et mon historique […] vérifie si l'absence du mandant n'est pas normale »)*

Sources relues : liste des tâches **1.8**, **2.6**, **2.7**, **3.2d** (lots 1 à 4), **3.2e** ; `normalizeStatusTransactionPayload`
(worker, l. 12900) ; `patch_registre_console_2026-09-16.sql` ; `registre_depuis_console.py` ; `LEDGER_SQL`
(`affaire_ledger.py`). Mesures en base sur les 31 088 transactions.

### ⭐ A. Les mandants — leur absence est NORMALE. Frédéric avait raison.

- **Hektor les déduit du mandat, tout seul.** Mesure du 16/09 : le compromis 50084, créé par l'app **sans
  envoyer un seul mandant**, est revenu avec **trois** (141053, 485955, 605030).
- **La règle est écrite dans le worker** (3.2d lot 3, 16/09) : *« null et tableau vide ne disent pas la même chose »*.
  `null` = l'app n'y a pas touché → on n'envoie rien, Hektor garde les siens. Un tableau = l'app **affirme** cette
  liste. *« Poser systématiquement notre liste remplacerait la sienne — et une liste incomplète ferait pire que
  mieux. »*
- Mesure : **une offre n'a JAMAIS de mandants** (0 sur 11 190 — l'offre de Hektor n'en porte pas). Compromis et
  ventes les ont à **99,8 %** (19 877 sur 19 898), tous venus de Hektor. Dans les 100 travaux de création, la liste
  n'a **jamais** été affirmée.

➡ **Correction de ma note** : « mandants : nulle part » était faux en tant que défaut. Les mandants **ne se
saisissent pas, ils découlent du mandat**. R1 ne doit **rien inventer** : il écrit les mandants **seulement s'ils
sont affirmés**. *(Piste, non décidée : les déduire au clic de NOTRE registre des mandats et des liens — mais ce
serait une seconde copie de la règle de Hektor, et le registre des mandats porte 457 « corps empruntés »
connus. À trancher.)*

### ⭐ B. Les notaires — la colonne « classe A » est MORTE, et le « gel » est déjà là

- **`notaire_id` (classe A, « Hektor l'ignore ») : 0 ligne remplie sur 31 088.** L'étiquette n'est vraie que pour
  l'**offre**, qui n'a pas de notaire chez Hektor (0 sur 11 190). Pour le **compromis** et la **vente**, Hektor
  **garde les deux notaires** (3.2d lot 2, 15/09 ; vente 23316 « 2 notaires, tout gardé »).
- **Leur vraie place existe** : `notaire_acquereur_id/_nom` et `notaire_mandant_id/_nom`, remplies la nuit par
  `registre_depuis_console.py` — **8 501 compromis** (console) et **8 612 ventes** (API).
- Le notaire du **vendeur** est le cas **majoritaire** : 89 % des compromis, 70 % des ventes (mesure du 15/09).
- ⚠⚠ **`notaires_origine = 'saisie'` FIGE la ligne pour toujours** (commentaire de la colonne : *« l'étape locale
  ne la touche plus »*). Si R1 posait `'saisie'`, un notaire changé ensuite dans Hektor ne remonterait **jamais**.
  **C'est le gel.** Mesure : 0 ligne `'saisie'` aujourd'hui.
- Même règle « affirmé » : `notaires_affirmes` — en modification, un champ prérempli n'est pas une intention.

➡ **Deux corrections de ma note** : (1) R1 écrit les notaires dans `notaire_acquereur_*` / `notaire_mandant_*`,
**pas** dans `notaire_id` ; (2) ma parade « R1 pose `'saisie'`, la garde existe déjà » était **fausse** : il faut
l'attente (R2), qui tombe une fois Hektor confirmé, pas `'saisie'`, qui ne tombe jamais.

### C. Les acquéreurs multiples — ça marche, sauf sur l'offre (par construction)

- **Prouvé le 16/09 et le 18/09** (vente 23317 : « 2 acquéreurs gardés »). Les essais d'avant ne prouvaient rien :
  ils utilisaient toujours le même couple de contacts de test, dont un que Hektor refusait (2.6, 10/09).
- Mesure : **2 451 transactions** ont plusieurs acquéreurs — **0 offre** (l'offre de Hektor n'en a qu'un).
- La RPC les écrit déjà au clic (`acquereurs_json`, 2.6) ; la nuit les remplace par la liste de Hektor.
- Règle « affirmé » : en reprise, la liste ne part que si l'écran l'a touchée (`acquereurs_affirmes`).
- Décision écrite : *« changer qui achète n'est pas une correction, c'est une autre affaire »*.

### ⭐ D. Les champs ne sont PAS les mêmes selon le genre — R1 doit écrire PAR GENRE

| champ | offre | compromis | vente |
|---|---|---|---|
| montant / prix | ✅ (dans les **propositions**) | ✅ prix public | ✅ prix |
| date | ✅ | ✅ | ✅ |
| jours de validité | ✅ (propositions) | — | — |
| date d'acte, séquestre | — | ✅ | **— (absents de l'assistant de vente, relevé du 08/09)** |
| rétractation | — | ✅ (Hektor garde la **date de fin**) | — |
| net vendeur | — (0 sur 11 182) | ✅ | ✅ |
| honoraires vendeur | **— Hektor ne les a pas** → `honoraires_entree_app` (lot 1a) | ✅ | ✅ |
| honoraires acquéreur | ✅ | ✅ | ✅ |
| notaires | **— aucun** | ✅ les deux | ✅ les deux |
| mandants | **— aucun** | déduits du mandat | déduits du mandat |
| acquéreurs | **un seul** | un ou plusieurs | un ou plusieurs |

Le `LEDGER_SQL` de la nuit encode exactement ce tableau (des `NULL AS …` par genre). Un champ vide dans une case
« — » n'est **pas** un défaut.

### ⭐ E. Une correction que je n'avais pas vue : la modification remplit le carnet avec du PRÉREMPLI

`app_modifier_affaire_optimistic` met au carnet **tout champ non vide de la charge**, qu'il ait été tapé ou
seulement prérempli. La leçon du 08/09 est écrite dans le worker : *« `sale_price` portait LE PRIX DE L'ANNONCE
(180 000) que personne n'avait tapé »*. Exemple possible : la modification de 30712 (13/10) a mis 6 champs au
carnet, dont `prix_publique = 180000`. ✅ **Vérifié dans le code de l'API** (`api.ts:10734`) : création et modification partagent **une seule charge**
(« on garde une seule construction de charge »), avec tous les champs de la modale. ⚠ Pas vérifié à l'écran :
si la modale vide d'elle-même les champs non touchés.
➡ **Avant R2**, le carnet ne doit recevoir que ce que l'utilisateur a **touché**. Sinon R2 protégerait du
prérempli — un gel fabriqué par nous.

### F. Le numéro de mandat est RECALCULÉ la nuit

`numero_mandat` ne vient pas tel quel de Hektor : la nuit le déduit par une cascade (2.7, colonne
`mandat_origine`). R1 écrit celui choisi dans la modale ; si la cascade en trouve un autre, c'est un **conflit
à montrer**, pas à écraser.

### Ce que ça change au plan R1-R5

```
R1   ecrire PAR GENRE (tableau D) · notaires dans notaire_acquereur_* / notaire_mandant_*,
     PAS notaire_id, et JAMAIS notaires_origine = 'saisie' · mandants SEULEMENT s'ils sont
     affirmes · en modification, seulement les champs TOUCHES (E)
R2   ne proteger que ce qui est en attente ET a ete touche ; le notaire passe par l'attente
R3   le verdict par genre (les champs « — » ne se jugent pas)
NEUF  decider du sort de `notaire_id` (colonne de classe A morte : 0 / 31 088)
NEUF  decider si les mandants se deduisent chez nous (piste A) ou restent a Hektor
```

### Décisions de Frédéric (22/10)

1. **Les mandants : Hektor les déduit du mandat.** R1 ne les écrit que s'ils sont affirmés dans la modale.
   La piste « les déduire chez nous » est écartée.
2. **Le notaire : rien n'est cassé.** Le circuit marche de bout en bout (prouvé les 15-18/09 chez Hektor :
   « 2 notaires, tout gardé »). L'écran lit la ligne de carnet `notaire_id` puis les colonnes
   `notaire_acquereur_*` / `notaire_mandant_*`. La **colonne** `app_affaire_ledger.notaire_id` n'est ni écrite
   ni lue : c'est un doublon inerte. **On la laisse, on n'y écrit pas.** R1 pose le notaire au clic dans
   `notaire_acquereur_*` / `notaire_mandant_*`, sans `notaires_origine = 'saisie'`.

### Pourquoi la colonne `notaire_id` existe — l'histoire *(Frédéric : « elle doit bien avoir un rôle et une raison »)*

| date | ce qui s'est passé | source |
|---|---|---|
| **03/09** | née en **classe A** (tâche 1.2) : *« NOTE DE L'APP, qui ne repart jamais chez Hektor (arbitrage Frédéric) »*. À l'époque, la modale avait un champ libre « ID notaire » et **rien n'était envoyé à Hektor** | commit `6b43e51`, liste l. 2142 |
| **15/09** | **3.2d lot 2** : le notaire part chez Hektor, **des deux côtés** (acquéreur et vendeur). Le commentaire de l'écran le dit : *« notaire_id — ce lot vient de l'ouvrir, des DEUX côtés »*. ➡ **la raison d'être de la colonne tombe** | `App.tsx:17368` |
| **16/09** | les notaires de Hektor reçoivent **leurs colonnes** (`notaire_acquereur_*`, `notaire_mandant_*`), remplies chaque nuit par la console et l'API | `patch_registre_console_2026-09-16.sql` |

**Qui l'écrit ?** Personne. Les RPC écrivent la **ligne de carnet** nommée `notaire_id`, pas la colonne. La colonne est
seulement portée par la liste de protection (`COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS`) et redescendue chaque nuit pour la
sauvegarde. **0 sur 31 088.**
**Qui la lit ?** Personne : ni l'écran, ni le run, ni le worker.

➡ **Elle a eu un rôle (garder un notaire que Hektor ne recevait pas), et ce rôle a disparu le 15/09** quand le notaire
s'est mis à partir chez Hektor. Elle n'est **pas utile aujourd'hui**. La retirer demanderait de toucher trois endroits
(Supabase, la table locale, la liste de protection) pour aucun gain : **on la laisse, inerte**.

⭐ **Et en la cherchant, un petit défaut d'affichage trouvé** : dans la liste des transactions de la modale de statut,
la ligne « Notaire » (`App.tsx:21154`) lit **seulement le carnet**, sans repli sur le registre. Pour une transaction
créée dans Hektor, elle est donc **vide**, alors que le nom est dans `notaire_acquereur_nom` (8 501 compromis,
8 612 ventes). Et il n'y a **pas de ligne pour le notaire du vendeur**, le cas majoritaire. À corriger avec R1
(l'écran), sur décision.

---

## 5. R1 — PRÉPARÉ LE 22/10, NON POSÉ *(Frédéric : « oui, profites-en pour corriger les points »)*

**Base** — `supabase/patch_r1_affaire_nait_complete_2026-10-22.sql` (+ `_INVERSE`, `_REPETITION`), générés par
`phase2/checks/gen_patch_r1_affaire_nait_complete.py`. Interrupteur `affaire_nait_complete`, **éteint**.
Deux ancres d'une ligne ; empreinte `3eec3f85` → `caab6b6c` (calculée d'avance dans la base, en lecture seule).
Allumé, la création écrit chaque champ dans sa colonne **par genre** (§ 4 D), les notaires dans
`notaire_acquereur_*` / `notaire_mandant_*` **sans** `'saisie'`, les mandants **seulement s'ils sont affirmés**.
Une erreur dans ce bloc ne fait **jamais** échouer le geste (WARNING).

**Répétition sur la vraie base, annulée : 13 sur 13** — éteint = rien de neuf (témoin inverse) · offre = validité,
honoraires acquéreur, taux, et rien d'un compromis · compromis = acte, séquestre, net, honoraires, taux, fin de
rétractation = date + 10, les deux notaires avec leur nom, pas de mandants non affirmés · mandants affirmés = les
deux, dans l'ordre · vente = net, honoraires, notaires, ni acte ni séquestre ni fin · le carnet reçoit autant de
lignes éteint et allumé · une date impossible ne casse pas le geste · l'inverse rend `3eec3f85`. Vérifié après :
empreinte, interrupteur, lignes et travaux d'essai, **rien n'est resté**. *(La séquence des numéros d'affaire a
avancé de 6 : une séquence ne recule jamais.)*

**Écran** (`npm run build` vert, **non déployé, non vu**) — la charge porte `buyer_notary_nom` /
`seller_notary_nom` (la RPC ne peut pas retrouver le nom : les notaires ne sont pas dans `app_contact_current`) ;
la liste des transactions de la modale montre **« Notaire acquéreur »** (carnet, puis registre en repli) et
**« Notaire vendeur »** (registre).

**Ce que R1 ne fait pas, et ce qui a été trouvé en le préparant**
- ⚠ **Le notaire posé au clic est remis à vide la première nuit**, entre le push du registre (l. 912, qui envoie
  les colonnes locales, encore vides) et celui de la console (l. 1253). La console le remet dès qu'elle a lu la
  transaction — le worker range cette lecture **au moment de la création**. Fenêtre de quelques minutes ; c'est R2
  qui la fermera.
- La **modification** n'est pas touchée (point E : la charge porte du prérempli) — pièce suivante, avec une
  décision : comment reconnaître un champ « touché ».
- Les autres colonnes posées au clic sont **réécrites la nuit** par la valeur de Hektor (identique si Hektor l'a
  prise). C'est R2.

**Pour le poser** (accord de Frédéric) : coller le patch, vérifier les 3 OK, allumer l'interrupteur ; pousser le
front ; essai réel par l'écran sur l'annonce d'essai 63331.

✅ **PATCH POSÉ EN PRODUCTION le 22/10 à 18:19:29**, par moi avec l'accord de Frédéric (« j'autorise : colle
toi-même le patch R1 »). Les 3 contrôles : **OK · OK · OK** (empreinte `caab6b6c`, interrupteur présent et
**éteint**, droits inchangés). Tant que l'interrupteur est éteint, la création se comporte comme avant.
⬜ Reste : le push du front (Frédéric), l'allumage, l'essai réel sur 63331.

### ✅ R1 EN PRODUCTION — essai réel du 22/10 par l'écran, sur VA6482 (annonce 24113)

Interrupteur `affaire_nait_complete` **allumé à 18:34:20** (accord de Frédéric). Front servi par Vercel
(`index-UiODBhSX.js`). Compromis saisi dans la modale : 130 000 €, date 22/10/2026, acte 15/01/2027, rétractation
10 j, séquestre 5 000, honoraires vendeur 8 000, acquéreur ESSAI 8A B2, les deux notaires ; mandants non touchés.

**⭐ LA PREUVE DE R1 — tout est chez nous à la MÊME milliseconde que le travail (18:40:16.526)**, transaction 1001368 :
`montant 130000` · `date 2026-10-22` · `date_acte 2027-01-15` · `sequestre 5000` · `date_fin_retractation 2026-11-01`
(date + 10) · `prix_net_vendeur 122000` · `honoraires_entree 8000` · `notaire_acquereur` 10064499 + son nom ·
`notaire_mandant` 10165291 + « Philippe notaires St Etienne » · `notaires_origine` vide · `notaire_id` vide ·
`mandants_json` vide (non affirmés) · carnet 11 lignes, inchangé. *(`honoraires_sortie` vide : la modale envoie
`null` pour 0.)* À l'écran, la liste des transactions montre la ligne, et « Notaire vendeur » affiche le nom.

**⚠⚠ MAIS HEKTOR N'A PAS CRÉÉ LE COMPROMIS — et ce n'est pas R1.** Journal du travail :
`findProspect rend 0 identifiant(s)` pour l'acquéreur 605946 → l'assistant est parti **sans acquéreur** →
« **AUCUN compromis NOUVEAU sur la fiche après l'envoi — la création n'a rien produit** » (18:41:08). Puis le
travail a **quand même** posé le statut « Sous compromis » chez Hektor et s'est terminé **`done`** ; l'écran a
affiché « Statut accepté ».
- État laissé : annonce 24113 **« Sous compromis » chez Hektor et chez nous, sans aucun compromis** ; notre ligne
  1001368 **sans numéro Hektor** ; une recherche de qualification créée puis archivée pour le contact d'essai.
- Deux défauts **trouvés par l'essai, hors R1, notés, non corrigés** :
  1. **un échec qui finit `done`** : la preuve dit « rien produit » mais le statut part quand même, et l'écran
     dit « accepté » (famille du chantier ④, « aucun échec silencieux ») ;
  2. **le contact d'essai n'est pas accepté comme acquéreur par Hektor** (`findProspect` vide) — la piste
     « portefeuille / typologie » de 2.6, jamais tranchée.
- **Petit défaut d'écran de R1** : la ligne « Notaire acquéreur » affiche le **numéro** (10064499) au lieu du nom,
  parce que le carnet porte l'identifiant sous la clé `notaire_id` et passe avant le registre. À corriger.

### ⛔ MON ERREUR DANS L'ESSAI, ET SON AUDIT *(Frédéric : « rattrapage de ton erreur, audit et explication »)*

**L'erreur** : j'ai choisi un acquéreur (ESSAI 8A B2, Hektor 605946) **sans aucune offre vivante sur le bien**.
C'est **le cas connu et jamais résolu** de la tâche 2.6, écrit noir sur blanc dans la liste
(`LISTE_TACHES_A_COCHER_2026-08-29.md`, l. ~5925) :

```
50067  worker    · 605075 (offres toutes refusees)   -> VIDE
50069  worker    · 605030 (offre acceptee)           -> attache
50068  ASSISTANT · 86793  (AUCUNE offre sur le bien) -> attache   (l'interface de Hektor, pas nous)
```
*« LEUR interface y arrive, la nôtre non. L'écart est dans NOTRE façon d'envoyer — reste à trouver laquelle. »*
Je ne l'ai pas relu avant de choisir l'acquéreur.

**Ce que dit l'historique, mesuré dans les journaux** (tous les compromis/ventes créés par l'app depuis le 30/08) :
- **Toutes** les créations réussies sur 24933 avaient un acquéreur **déjà présent dans l'assistant** de Hektor —
  parce qu'il avait une offre vivante sur le bien (605030, 605075). Le journal en garde la preuve :
  « Assistant relu : 3 acquéreur(s) », même quand `findProspect` rendait 0.
- **`findProspect` n'ajoute pas** un acquéreur que l'assistant ne propose pas déjà : 0 identifiant le 22/10, comme
  les 16-18/09. Quand l'assistant ne le propose pas, le compromis part **sans acquéreur**, et Hektor ne crée rien.
- ⚠ **La qualification (le grand chantier du 18/09, `8d70f1e`) a bien joué** : recherche créée (critère 471880),
  puis archivée. **Elle n'est pas la cause.** Et sa preuve « sur compromis (605414) » était une **modification**
  du compromis 50088 dont les acquéreurs étaient déjà attachés — **jamais une création**.
- ➡ **L'app n'a JAMAIS créé un compromis dont l'acquéreur n'avait pas déjà une offre vivante sur le bien.** Le vrai
  parcours, celui qui marche, est la chaîne : **offre → acceptée → compromis**.

**Deux défauts du worker que l'essai a montrés** (hors R1, notés, non corrigés) :
1. **le statut part AVANT la preuve** : « Statut Hektor Sous compromis envoyé » à 18:40:53, la preuve « rien
   produit » à 18:41:08. Le bien est donc « Sous compromis » sans compromis, et le travail finit `done` ;
2. l'écran dit « Statut accepté » sur un échec (famille du chantier ④).

**Le rattrapage proposé — À DÉCIDER PAR FRÉDÉRIC**
- ⛔ « Supprimer le compromis » est **impossible** : il n'existe pas chez Hektor (aucun numéro), le geste de
  suppression exige ce numéro.
- ⛔ Repasser « Actif » **par l'app** est **dangereux** : la configuration du worker pose `diffusable = 1` avec
  « Actif » (`HEKTOR_STATUS_CONFIG`), alors que VA6482 était **non diffusable** avant l'essai.
- ✅ **1.** remettre le statut « Actif » **chez Hektor, à la main**, sans toucher à la diffusion ; la relecture
  ramènera le statut chez nous ;
- ✅ **2.** retirer chez nous la ligne d'essai 1001368, ses 11 lignes de carnet et sa lecture console, **après une
  sauvegarde datée** (elle n'a pas de jumelle chez Hektor, la nuit ne la recréera pas) ;
- ✅ **3.** refaire la preuve complète plus tard, **par la chaîne** (offre → acceptée → compromis), avec R3.

### ⛔⛔ CORRECTION DE L'AUDIT CI-DESSUS — Frédéric avait raison *(« re-audite, ajouter un compromis a fonctionné avec des contacts non présents en offre, vérifie »)*

**Ce que j'ai écrit est FAUX** : « l'app n'a jamais créé un compromis dont l'acquéreur n'avait pas d'offre vivante ».
Mesure dans les journaux et les lectures console de 24933 :

| compromis | acquéreur(s) attaché(s) | offre de cet acquéreur sur 24933 ? |
|---|---|---|
| **50085** (16/09) | 605008 TESTA Gabrielle, **605029** TEST CHAINE | **aucune** pour l'un comme pour l'autre |
| **50088** (17/09) | **413764** TEST SEPTEO, 605030 | **aucune** pour 413764 — relu attaché à 20:11 |
| vente 23317 (18/09) | **605429** (créé « Propriétaire », qualifié) | **aucune** |

J'avais tiré ma conclusion de l'acquéreur **principal** et des notes du 04/09, sans regarder les co-acquéreurs, et
sans comparer les réponses de Hektor.

**Ce que la mesure dit vraiment de l'essai du 22/10 :**
- `findProspect` a rendu pour 605946 **un bloc de la même forme** que pour 413764 le 17/09 (« Suivi par … ESSAI 8A B2
  Creation · Créé le 22-10-2026 », 1 843 car.). Le « 0 identifiant » est **normal** : il s'affiche aussi pour tous
  les compromis réussis de septembre (le lecteur ne reconnaît pas ce format de bloc).
- « Assistant relu : 0 acquéreur » au moment de la création est **normal** aussi : même lecture dans les cas réussis.
- **La réponse finale de Hektor est identique, octet pour octet sur l'aperçu, à celle des 15 compromis réussis** de
  septembre (`success:true`, `currentStepIndex 3`).
- ➡ **Le seul signe d'échec est la preuve du worker**, qui relit la fiche **15 secondes** après l'envoi. Et cette preuve
  a déjà été **fausse** : le 31/08, trois « AUCUN compromis NOUVEAU » (00:26, 00:28, 01:12) ont été suivis à 07:53 de
  « **PLUSIEURS** compromis nouveaux » — ils avaient donc bien été créés, plus tard visibles.
- ➡ **On ne sait PAS si le compromis existe chez Hektor.** Notre miroir local ne tranche pas (les transactions de 24113
  y datent de 04:24 ce matin). Je n'ai pas pu regarder la fiche Hektor : la session n'est pas ouverte dans Chrome, et je
  ne saisis pas de mot de passe.

**Ce qu'il faut savoir avant de corriger**
- S'il existe : ⚠ notre ligne 1001368 porte l'acquéreur sous **notre** numéro (`20000008`), le miroir le portera sous
  celui de Hektor (`605946`). L'adoption de nuit par l'acquéreur risque de **ne pas** les rapprocher → **une seconde
  ligne** pour le même compromis. Non mesuré, à surveiller.
- S'il n'existe pas : la piste reste ouverte (bien, mandants incomplets — 6 mandants dont un « Mr./Mme » sans nom —,
  ou autre). **Je n'affirme plus de cause.**

**Le rattrapage, révisé — à décider par Frédéric**
1. **Regarder la fiche VA6482 chez Hektor** (Suivi de vente) : y a-t-il un compromis à 130 000 € avec ESSAI 8A B2 ?
   *(Frédéric, connecté ; ou attendre le miroir de cette nuit.)*
2. **S'il existe** : le supprimer — chez Hektor à la main, ou par l'app après avoir posé son numéro sur notre ligne
   (le geste « supprimer » l'exige) — puis vérifier que le statut redescend.
3. **S'il n'existe pas** : remettre « Actif » chez Hektor à la main (pas par l'app, qui rendrait le bien diffusable),
   puis retirer chez nous la ligne 1001368 après une sauvegarde datée.

### ✅ VÉRIFIÉ CHEZ HEKTOR (22/10, fiche VA6482 lue dans Chrome) — LE COMPROMIS EXISTE, COMPLET

**Compromis 50128**, « Compromis de vente signé » :
acquéreur **Mme ESSAI 8A B2 Creation** · **6 mandants déduits du mandat** par Hektor (PHILIBERT ×2, MANOA, « Mr./Mme »,
SAMUEL-PHILIBERT, TESTCLAUDE) · date 22/10/2026 · **fin de rétractation 01/11/2026** (la même que celle que R1 a
calculée) · acte prévu 15/01/2027 · séquestre 5 000 € · prix 130 000 € · honoraires agence 6 666,67 € HT
(8 000 TTC) · **notaire acquéreur CORNU**, **notaire mandant FAURE**. Statut du bien : Sous compromis.

➡ **L'essai a donc RÉUSSI de bout en bout.** R1 et Hektor disent la même chose, champ par champ. Ce qui a échoué,
c'est **le contrôle du worker**, qui a relu la fiche 15 s après l'envoi et n'a pas vu le compromis
(**faux négatif**, déjà vu le 31/08). Conséquence : le numéro 50128 n'a **pas** été posé sur notre ligne 1001368.

⚠⚠ **ET UN DÉFAUT RÉEL, TROUVÉ PAR CET ESSAI** : sans ce numéro, la nuit cherche à rapprocher notre ligne **par
l'acquéreur** (`adoptables`, `affaire_ledger.py` l. ~701). Or notre ligne porte l'acquéreur sous **notre** numéro
(`hektor_acquereur_id = 20000008`, l'écran envoie l'identité depuis le 23/09) et le miroir le portera sous celui de
Hektor (`605946`). **Le rapprochement échouera, et la nuit créera une seconde ligne pour le compromis 50128.**
Ce trou existe depuis le 23/09 pour toute transaction dont la preuve rate ; il ne mord que dans ce cas, parce que,
sinon, le worker pose le numéro tout de suite et le rapprochement se fait par le numéro.

**Le rattrapage, maintenant que les faits sont sûrs — à décider par Frédéric**
1. **Poser le numéro 50128 sur notre ligne 1001368** (+ `present_in_hektor = true`) — exactement ce que le worker
   aurait fait. La nuit la rapprochera alors par le numéro : pas de doublon.
2. **Supprimer le compromis PAR L'APP** (modale de statut → la transaction → « Supprimer le compromis ») : le geste
   prévu, éprouvé les 07/09 et 18/09 — il exige le numéro, supprime chez Hektor avec preuve, inscrit au journal des
   suppressions, retire notre ligne, et Hektor redescend le statut tout seul.
3. Vérifier chez Hektor et chez nous : plus de compromis, statut revenu, notre ligne partie.

### ✅ RATTRAPAGE FAIT (22/10, accord de Frédéric : « fais les 2 »)

1. **Sauvegarde datée** : `app_affaire_ledger_avant_numero_50128_20261022` (la ligne 1001368 telle qu'elle était).
   **Numéro posé** sur la ligne 1001368 : `hektor_affaire_id = 50128`, `present_in_hektor = true`.
2. **Suppression par l'app**, modale de statut → « Supprimer le compromis » (la modale affichait bien
   « Compromis n° 50128 »). La confirmation du navigateur a été acceptée par script, son texte gardé :
   *« Supprimer DÉFINITIVEMENT ce compromis chez Hektor ? … VA6482 — compromis n° 50128 »*.
   Travail `delete_hektor_compromis` **done** à 22:12:18 : « Suppression DÉFINITIVE du compromis 50128 » ·
   « Statut Hektor redescendu à Actif » · « Affaire 1001368 (compromis 50128) : journal écrit, ligne en ligne
   effacée, 11 saisie(s) retirée(s) du carnet ».
3. **Vérifié des deux côtés** :
   - **chez nous** : ligne 1001368 **absente**, carnet **vide**, journal des suppressions **1 ligne**
     (`geste_app`, compromis 50128), fiche **Actif**, `diffusable` **0** (inchangé), 0 portail ;
   - **chez Hektor** (fiche lue dans Chrome) : étiquette **ACTIF**, « Bien actif » coché, **plus aucun compromis**,
     plus d'événement « Compromis » dans la synthèse.
- Reste, sans effet : la lecture console de 1001368 (`app_affaire_console`, une ligne — plus aucune affaire ne la
  lit) ; la recherche de qualification du contact d'essai, créée puis archivée chez Hektor (prévu).

---

## 6. POINT 1 — LE CONTRÔLE TROP PRESSÉ ET LE DOUBLON DE NUIT — audit du 22/10 *(Frédéric : « 1 »)* — lecture seule

### A. Pourquoi le worker a cru à un échec

`prouverTransactionCreee` (`console_job_worker.js:15617`) relit **3 fois, espacées de 4 s** (≈ 15 s en tout) la liste
des compromis **par l'API** (`phase2/sync/transactions_annonce_from_api.py` : `/Api/Vente/ListCompromis/`, **page 0**,
tri `dateStart` décroissant, puis filtre sur l'annonce). Le 22/10, l'API a répondu trois fois, **sans le compromis 50128**.
- Ce n'est **pas** le tri : notre registre ne porte aucun compromis daté du 22/10 ou après (mesure) — 50128 aurait dû
  être en tête de la page.
- La fiche (le repli) n'a pas été lue : elle ne sert que si l'API est muette.
- ➡ **Cause la plus probable : un délai de l'API de Hektor** au-delà de 15 s. *(Non mesurable a posteriori : 50128 est
  supprimé. Il faudrait une création pour mesurer le délai.)* Le commentaire du 31/08 décrivait déjà « la fiche
  retarde » ; l'API retarde aussi, parfois.
- Le statut « Sous compromis » part **avant** la preuve : ce jour-là c'était juste, puisque le compromis existait.

### B. Pourquoi la nuit aurait fait un doublon

Sans numéro Hektor, la nuit rapproche la ligne de l'app **par l'acquéreur** (`affaire_ledger.py` l. ~701 : clé
`(annonce, genre, hektor_acquereur_id)`). Or la RPC de création range dans `hektor_acquereur_id` **le numéro envoyé par
l'écran**, c'est-à-dire **notre identité** (`buyer_contact_id`). Pour un contact venu de Hektor, identité = numéro
Hektor (< 10 M) : aucun souci (ex. 605717, le 13/10). Pour un contact **né dans l'app** (≥ 20 M, `contact_nait_complet`
allumé le 21/10), les deux diffèrent (20000008 / 605946) : **le rapprochement échoue**.
- La même identité part aussi dans `app_chaine_pour(annonce, acquéreur, …)` au clic : la chaîne posée au clic peut donc
  différer de celle de la nuit (qui la recalcule de toute façon).
- **Ampleur aujourd'hui** : 0 ligne touchée (la seule, 1001368, est rattrapée et supprimée) ; 2 créations par l'app
  depuis le 23/09. **Mais chaque nouveau contact créé dans l'app est désormais concerné.**
- Le filet existe : la sentinelle `data.affaire_sans_numero_hektor` (seuil 0) **aurait sonné** — mais au moniteur de
  05:48, **après** le run de 05:00 qui aurait déjà créé le doublon.

### C. Les corrections proposées — À DÉCIDER

| | quoi | où | ce que ça pourrait casser ailleurs |
|---|---|---|---|
| **1a** | **la preuve patiente** : si rien n'est vu en 15 s, ne pas conclure « rien produit » mais **reprendre plus tard** (ex. relectures à +30 s, +2 min, +10 min), et poser le numéro dès qu'il apparaît — en exigeant que la transaction vue porte **notre acquéreur et notre montant** (pas seulement « un numéro nouveau ») | worker | quelques lectures API de plus (une par relecture, loin du quota) ; un travail plus long bloque la file du worker — d'où une **reprise différée** plutôt qu'une attente sur place ; les 4 services à redémarrer |
| **1b** | **le bon numéro à la bonne place** : la RPC range dans `hektor_acquereur_id` le **numéro Hektor** de l'acquéreur (`hektor_target_id`), notre identité restant dans `app_contact_id` (déjà fait) ; la chaîne du clic utilise le même numéro que la nuit | base (RPC de création, ancre + interrupteur) | la recherche de chaîne au clic change pour les contacts nés dans l'app — c'est le but ; aucun effet pour les contacts venus de Hektor (même numéro) |
| **1c** | **filet de nuit** : le rapprochement par acquéreur essaie aussi le numéro traduit (identité → Hektor, table locale `app_contact`) | `affaire_ledger.py` | touche le run de nuit ; utile seulement pour des lignes déjà écrites avec l'identité — **0 aujourd'hui** |

**Ma recommandation** : **1b d'abord** (petit, ferme le doublon à la racine), puis **1a** (le faux échec).
**1c** n'est pas nécessaire tant qu'aucune ligne n'est touchée.

### 1b ne touche pas le worker — vérifié *(Frédéric : « confirme que le worker fonctionnera comme avant pour l'acquéreur »)*

- **Le worker ne lit jamais `hektor_acquereur_id` du registre** (une seule mention, `console_job_worker.js:15233`, pour
  dire qu'il ne la touche pas). Il prend l'acquéreur dans **la charge du travail** (`buyer_contact_id`) et le **traduit
  lui-même** vers le numéro Hektor (`ciblesHektorContacts`, depuis le 22/09).
- **Preuve du 22/10** : la charge portait `20000008`, le worker a visé `605946`, et Hektor a attaché **Mme ESSAI 8A B2**
  au compromis 50128. Avant (septembre, 13/10), la charge portait des numéros Hektor et le worker les visait tels quels.
- 1b ne change **ni la charge, ni le worker** : seulement ce que la RPC range dans la colonne du registre.
- Les autres lecteurs de la colonne : `app_chaine_pour` et `app_attribuer_chaines_affaire` (ils la comparent aux lignes
  venues de Hektor — 1b les aligne), l'écran (« même acquéreur sur deux compromis ? » — aligné aussi), et le run de nuit
  (il lit la table **locale**, remplie par le miroir : numéros Hektor, inchangé).

### ⚠ CORRECTION DE L'AUDIT DU POINT 1 — l'ampleur était sous-estimée

J'ai écrit « seuls les contacts nés dans l'app ont deux numéros ». **Faux** : les **62 288** contacts de
`app_contact_current` ont **tous** une identité (≥ 10 M) différente de leur numéro Hektor. Et l'écran envoie **tantôt
l'identité** (la recherche de contacts : 20000008 le 22/10), **tantôt le numéro Hektor** (605717 pour KURCEBA le 13/10,
identité 10650570). Les deux cas cassent quelque chose :
- identité → la nuit ne rapproche pas (doublon) ;
- numéro Hektor → la RPC ne retrouve pas notre contact (`app_contact_id` vide au clic ; la nuit l'a refait le 13/10).

### 1b — PRÉPARÉ, RÉPÉTÉ, NON POSÉ

`supabase/patch_1b_affaire_acquereur_numero_hektor_2026-10-22.sql` (+ `_INVERSE`, `_REPETITION`), généré par
`phase2/checks/gen_patch_1b_affaire_acquereur_numero_hektor.py`. Interrupteur `affaire_acquereur_numero_hektor`, éteint.
Cinq ancres d'une ligne, empreinte `caab6b6c` (R1) → `f9d02447`. Allumé : la RPC reconnaît le contact **par l'un ou
l'autre numéro**, range le **numéro Hektor** dans `hektor_acquereur_id`, le passe à `app_chaine_pour`, et notre identité
dans `app_contact_id`. Inconnu : rangé tel quel, rien d'inventé. **Le worker n'est pas touché.**

**Répétition sur la vraie base, annulée : 7 sur 7** — éteint, identité : rangée telle quelle · éteint, numéro Hektor :
lien vide (les deux témoins inverses) · allumé, 20000008 → 605946 · 10650570 → 605717 · 605717 → contact 10650570
retrouvé · inconnu → tel quel · l'inverse rend `caab6b6c`. Vérifié après : empreinte, interrupteurs, lignes, travaux
d'essai — **rien n'est resté**.
⚠ **Ordre des retours arrière** : l'inverse de 1b **avant** celui de R1.

✅ **1b POSÉ EN PRODUCTION le 22/10** (accord de Frédéric : « pose et allume ») — contrôles **OK ×4** (empreinte
`f9d02447`, interrupteur présent, droits inchangés, interrupteur de R1 toujours là) — **interrupteur
`affaire_acquereur_numero_hektor` ALLUMÉ à 22:56:52**. Aucun service à redémarrer (base seule).
⬜ Pas encore éprouvé par l'écran : la prochaine transaction créée dans l'app doit porter le numéro Hektor de son
acquéreur dans `hektor_acquereur_id`, et notre contact dans `app_contact_id`.

### 1a — LE CONTRÔLE QUI PATIENTE : audit du 22/10 *(Frédéric : « continue »)* — lecture seule

**Ce que dit l'historique** (toutes les créations par l'app depuis le 30/08, ~60) : la preuve a échoué **19 fois**, et
**à chaque fois le numéro Hektor n'a pas été posé** :

| échec | nombre | ce qui s'est passé |
|---|---|---|
| « AUCUN nouveau » | 10 | 7 les 30-31/08 (avant le passage à l'API, le soir du 31/08) · 10/09 une vente partie **vraiment** sans acquéreur · **22/10, un faux négatif** (50128 existait) |
| « PLUSIEURS nouveaux » | 6 | toutes sur 24933 : des compromis d'essai **supprimés de notre registre mais vivants chez Hektor** passaient pour « nouveaux » — la preuve refuse de choisir, à raison |
| « NON vérifié » | 4 | l'API muette (3 fois de suite), la fiche illisible |

**Ce que 1b change déjà** : sans numéro, la nuit rapproche maintenant par l'acquéreur **avec le bon numéro** — le
doublon est fermé. Ce qui reste : **un jour sans numéro**, pendant lequel « Modifier » est refusé
(`modification_sans_numero_hektor`) et « Supprimer » impossible (le geste exige le numéro) ; et un journal qui dit
« rien produit » quand on ne sait pas.

**La proposition 1a — à décider**
- **Une seconde preuve, sans nouveau type de travail.** Le travail de relecture (`refresh_console_data`) part déjà
  ~30 s après chaque changement de statut. On lui ajoute une étape *« poser les numéros manquants »* : pour l'annonce
  relue, s'il existe une transaction née dans l'app **sans numéro**, il relit la liste de l'API et pose le numéro
  **seulement si un seul candidat** porte **le même genre et le même acquéreur** et n'est pas déjà connu du registre.
  Sinon il ne choisit pas, et le dit. ⭐ Le critère « même acquéreur » tranche aussi les cas « PLUSIEURS ».
- **Le journal dit vrai** : « pas encore vu — seconde preuve à la relecture » au lieu de « la création n'a rien
  produit ».

**Ce que ça pourrait casser ailleurs**
- La relecture est un travail **central** (elle tourne très souvent) : la nouvelle étape doit être **sans risque**
  (une erreur = une ligne de journal, jamais un échec de la relecture) et **muette** quand il n'y a rien à faire —
  elle ne lit l'API que s'il existe une ligne sans numéro (rare).
- Poser un numéro faux serait grave : d'où **unicité + même acquéreur + inconnu du registre**, sinon on s'abstient.
- Touche le worker : **les 4 services à redémarrer**, file vide.
- Ne change ni la nuit ni la preuve immédiate (elle garde ses 3 lectures).

### 1a — CODÉ, ESSAYÉ HORS LIGNE, NON ACTIF *(Frédéric : « vas-y 1a »)*

`Console/console_job_worker.js` :
- **`poserNumerosManquants(job, annonce)`** (+ `acquereursDuDetail`), juste après `poserIdTransactionSurAffaire` ;
  interrupteur de code `SECONDE_PREUVE_RELECTURE = true` (retour arrière : `false`) ;
- appelée dans **`handleRefreshConsoleData`**, après le nettoyage des lignes provisoires, son bilan rangé sous
  `numeros_manquants` dans le résultat de la relecture ;
- le journal de la preuve dit désormais « AUCUN … NOUVEAU **vu** après l'envoi (3 lectures, ~15 s) — pas encore
  publié, ou pas créé. Seconde preuve à la relecture » au lieu de « la création n'a rien produit ».

**Règle** : pour chaque transaction de l'annonce relue, **née dans l'app, sans numéro**, on relit la liste de l'API
et on pose le numéro **seulement** si **un seul** candidat porte **le même genre et le même acquéreur** (numéro Hektor,
cf. 1b) et n'est pas déjà au registre. Sinon : abstention, écrite au journal (`hektor_transaction_seconde_preuve`).
Sans ligne orpheline : **aucune lecture chez Hektor**. Une erreur : une ligne de journal, **jamais** un échec.

**Essai hors ligne sur le vrai code : `node Console/test_seconde_preuve.js` → 13 sur 13**, dont le cas du 22/10
(50128 posé sur 1001368), les cinq abstentions (autre acquéreur, deux candidats, registre illisible, API muette,
identité d'avant 1b, deux lignes orphelines), l'offre, l'erreur Supabase sans échec, et le **témoin inverse**
(interrupteur à `false` : rien lu, rien posé). `node --check` vert, fins de ligne CRLF intactes.

⚠ **Non vérifié en réel** : la forme exacte de l'acquéreur dans la liste des **offres** de l'API (`id_acquereur` à
plat, lu dans le brut des offres de la nuit) ; celle des compromis (liste `acquereurs`) est déjà lue par le worker
depuis le 16/09.
⬜ **Pour l'activer** : redémarrer **les 4 services**, file vide (0 pending, 0 running) — Frédéric ; puis pousser.

✅ **1a ACTIF (22/10, 23:35)** — mesuré, pas supposé : `origin/main` = `678b731` (le commit de 1a), fichier du worker
écrit à 23:33:10, **les 4 services redémarrés à 23:35:49-50** (heure des processus `node.exe`, enfants de chaque
service). File vide, 0 erreur dans l'heure, **0 transaction de l'app sans numéro**.
⬜ **Pas encore vu tourner** : aucune relecture (`refresh_console_data`) n'est passée depuis le redémarrage. La
première portera `numeros_manquants: {"status": "rien_a_faire"}` dans son résultat.
✅ **1a VU TOURNER (22/10, 23:40:29)** — accord de Frédéric (« relance pour vérifier ») : relecture
`refresh_console_data` posée sur l'annonce d'essai 63331 (travail `9ddabe3b`), prise par le service **SyncLight**,
**`done`**, résultat **`numeros_manquants: {"status": "rien_a_faire"}`** — l'étape tourne, ne lit rien chez Hektor
quand il n'y a rien à faire, et ne gêne pas la relecture. *(Le cas « numéro posé » n'a pas encore eu lieu en réel :
il faudra une création dont la preuve rate.)*

### SECOND ESSAI RÉEL (22/10, 23:47, VA6482) — 1b prouvé, et LA VRAIE CAUSE du faux échec trouvée

Compromis saisi dans la modale : 135 000 €, acte 15/02/2027, rétractation 10 j, séquestre 6 000, honoraires vendeur
9 000, acquéreur ESSAI 8A B2, les deux notaires.

- ✅ **R1 + 1b au clic (23:47:07)**, ligne **1001375** : tous les champs, **`hektor_acquereur_id = 605946`** (le numéro
  Hektor) et **`app_contact_id = 20000008`** (notre contact). **1b est prouvé en réel.**
- ✅ **Chez Hektor** (fiche lue dans Chrome) : **compromis 50129**, complet, identique à la saisie (rétractation au
  01/11/2026, acte 15/02/2027, séquestre 6 000, 135 000 €, notaires CORNU et FAURE, 6 mandants déduits).
- ⚠ **Premier contrôle** (23:47:54) : « AUCUN compromis NOUVEAU vu … pas encore publié, ou pas créé » — le nouveau
  message, juste cette fois.
- ⚠ **Seconde preuve** (relecture de 23:49:09) : **abstention, 0 candidat**. Elle a fait ce qu'il fallait : ne pas
  deviner.

**⭐ LA CAUSE, MESURÉE (lecture seule de l'API, 23:5x)** : la première page de `/Api/Vente/ListCompromis/` est triée
**par numéro d'ANNONCE décroissant** (63037, 62967, 62922 … 62405), **pas par date** comme le croit le code (`sort=dateStart`,
`way=desc` sont sans effet). Un compromis posé sur une annonce **ancienne** (24113) **n'y figure jamais**, même des
minutes après : l'API répondait encore `ids: []` à 23:5x. Ce n'est **pas un délai** — mon audit du point 1 se trompait
sur ce point.
- Les essais de septembre passaient parce que… *non expliqué* : l'ordre de cette route a pu changer depuis, ou 24933
  y figurait encore. **Non mesuré.**
- La **fiche**, elle, porte le bon marqueur : `clore_compromis_vente(50129)`.
- ~~Même route utilisée par la **preuve d'une modification**~~ — ⛔ **FAUX, corrigé le 23/10** : depuis `d79f88f` (18/09) la
  modification d'un compromis se relit **par son numéro** (`CompromisById`), elle n'est **pas** touchée. Voir plus bas.

**Ce que ça veut dire pour 1a** : la seconde preuve est juste et prudente, mais elle lit **la même liste aveugle** —
elle ne pourra rien poser pour une annonce ancienne. **Correctif à proposer (non codé)** : quand la liste ne voit rien,
lire la **fiche** (le marqueur), puis **confirmer chaque candidat par l'API « par numéro »** (`CompromisById` /
`VenteById`, déjà utilisées : la porte 2) en vérifiant l'annonce et l'acquéreur.

**Le compromis 50129 est GARDÉ pour l'instant, exprès** : sans numéro sur 1001375, **la nuit doit le rapprocher par
l'acquéreur** — maintenant que 1b y range 605946. C'est **la preuve du chemin de nuit de 1b**, à vérifier demain
matin ; on le supprimera ensuite.

### Le problème était-il là avant ? *(Frédéric, 22/10)* — mesuré

- **Non, pas en septembre.** Du 16 au 18/09, la même lecture (page 0 de `ListCompromis`) **trouvait** les compromis de
  24933 — une annonce **ancienne** : « compromis 50084 / 50085 / 50086 créé et confirmé par les DEUX portes ». La page 0
  était donc alors rangée par **date** (les compromis d'essai étaient les plus récents).
- **Notre lecture n'a pas changé depuis** : `transactions_annonce_from_api.py`, dernier commit le 16/09 ; le client
  commun a seulement gagné de la patience le 22/09.
- **Aujourd'hui, la page 0 est rangée par numéro d'annonce décroissant** (mesure de 23:5x). ➡ **Le changement vient de
  Hektor, entre le 18/09 et le 22/10.** Date exacte **non mesurable** : aucune création par l'app sur une annonce
  ancienne entre les deux.
- **Ce qui est touché** : seulement la **preuve immédiate** du worker pour les **compromis** (création, et preuve d'une
  modification), sur les annonces **anciennes**. Ventes : leur liste est filtrée par une fenêtre de dates, non touchée a
  priori. Offres : **mesuré le 23/10, pas touchées** (voir plus bas). ⚠ *La « preuve d'une modification » est hors de cause : elle
  lit par numéro depuis le 18/09.*
- **Ce qui n'est PAS touché** : la **nuit**. Elle lit la liste **entière** (`DailyRawMaxPages = 0`) : 11 compromis
  d'octobre sur des annonces anciennes (< 60 000) sont bien arrivés au registre.
- **Conséquence réelle** : jusqu'à la nuit, une transaction créée dans l'app sur une annonce ancienne reste sans numéro
  (« Modifier » refusé, « Supprimer » impossible). Grâce à **1b**, la nuit la rapproche sans doublon.

### Comment faisait le worker avant, et la solution déjà trouvée *(Frédéric, 23/10 : « vérifie les tests, je crois que nous avions trouvé une solution »)* — mesuré

**Les trois époques de la preuve d'un compromis :**

| période | le worker prouvait par | résultat mesuré (journal `hektor_transaction_preuve`) |
|---|---|---|
| jusqu'au 31/08 | la **fiche** de l'annonce (marqueur `clore_compromis_vente(ID)`) | semaine du 24/08 : **2 réussies, 4 ratées** — la fiche ne montre qu'un compromis, pas toujours le dernier (`8ef38c1`) |
| 31/08 → 03/09 | la **liste** API, page 0 | semaine du 31/08 : **9 réussies, 5 ratées** — il manquait `withCompromisStatus=false` (corrigé le 03/09) |
| 03/09 → 18/09 | la liste API **réglée** + relecture par numéro pour une **modification** (`d79f88f`, `daa4b39`) | semaines du 07 et du 14/09 : **51 preuves réussies** *(créations et modifications)*, **0 « aucun nouveau »** ⭐ |
| 22/10 | la même liste, **code inchangé** | **0 réussie, 2 ratées** (50128 et 50129, tous deux bien créés) |

- ⭐ **Oui, la solution avait été trouvée, et elle marchait** : 51 preuves réussies et aucune création manquée en septembre (sur 24933, une annonce ancienne).
- ⭐ **Le 18/09, la solution « par numéro » a été posée pour la MODIFICATION** (commit `d79f88f` : « ListCompromis ne rend que
  les 20 compromis les plus récents de l'agence (**tri par date**) »). Le message le dit : **le 18/09 la liste était rangée par
  date**. Pour la **création**, la liste a été gardée exprès : on ne connaît pas encore le numéro, donc on ne peut pas le lire
  par numéro, et « une transaction créée à l'instant est forcément parmi les 20 plus récentes ».
- ⛔ **C'est cette dernière phrase que Hektor a cassée** entre le 18/09 et le 22/10 : `sort=dateStart` est désormais
  **ignoré**, la page 0 est rangée par **numéro d'annonce**. Aucune création de compromis par l'app entre ces deux dates
  (journal vide du 19/09 au 21/10) : la date exacte du changement ne se mesure pas.

**Les tris mesurés le 23/10 (lecture seule, avec LES PARAMÈTRES DU WORKER, `withCompromisStatus=false` compris) :**

| essai sur `ListCompromis` page 0 | 50129 (créé la veille) |
|---|---|
| `sort=dateStart way=desc` *(le code actuel)* | **absent** — annonces 63037, 62967… |
| idem + `agence=12` | absent |
| idem + `version` | absent |
| **`sort=id way=desc`** | ⭐ **en TÊTE** — 50129, 50127, 50126, 50125, 50124 |

`ListOffres` page 1 : **déjà rangée par numéro décroissant** (33108, 33107, 33106…) → les offres ne sont pas touchées.

**Qui lit cette liste de compromis (le correctif les couvre tous) :** la preuve de création · la lecture « avant » qui sert à
reconnaître ce qui est apparu · le filet anti-doublon d'une modification (`apres_modification_liste`) · la seconde preuve 1a.
**Ne la lit PAS** : la preuve d'une modification (par numéro) · la suppression (par numéro) · **la nuit** — `sync_raw.py`
porte aussi `sort=dateStart`, mais le run passe `--compromis-recent-limit 999999` (`run_full_pipeline.ps1:43`) : il lit
**toutes** les pages, l'ordre ne change rien.

**Le correctif — ✅ CODÉ ET ACTIF le 23/10 à 00:1x** *(Frédéric : « oui »)*, commit `2704dee` : dans
`phase2/sync/transactions_annonce_from_api.py`, branche compromis, `"sort": "dateStart"` → `"sort": "id"` (on garde
`way=desc` et `withCompromisStatus=false`), commentaires corrigés.
- **Essai réel en lecture seule** (le script lui-même, comme l'appelle le worker) sur 24113 : `{"trouve": true, "ids":
  ["50129"]…}`. **Témoin inverse** : le même appel avec l'ancien tri ne le trouvait pas (mesure du 22/10, 23:5x).
- **Actif sans redémarrage** : le worker lance un **nouveau** Python à chaque lecture (`runProjectPythonScript` → `spawn`).
- ⏰ **Reste à le voir en vrai** : la prochaine création de compromis par l'app doit être prouvée **tout de suite**.

**Les essais du correctif (23/10, ~00:30, lecture seule, Frédéric : « as-tu testé ? »)** — l'ANCIEN script (tiré de
`7724da6`) et le NOUVEAU, côte à côte, sur les mêmes annonces :

| annonce | compromis récent | ancien tri | nouveau tri |
|---|---|---|---|
| 24113 | 50129 (22/10) | **rien** | ✅ 50129 |
| 62334 | 50127 (19/10) | **rien** | ✅ 50127 |
| 8489 | 50126 (16/10) | **rien** | ✅ 50126 |
| 63037 | 50121 (14/10) | 50121 | ✅ 50121 |

⚠ **Pire que je ne le disais** : l'ancien tri ne ratait pas que les annonces « anciennes » — il rate aussi 62334, une annonce
récente. Seules les annonces aux plus grands numéros (≥ ~63 000) restaient visibles.
- **Offres et ventes inchangées** (le diff ne touche que la ligne des compromis), et vérifiées par le script : offres 33108
  (63255) et 33107 (63156) trouvées ; ventes 23350 (43783) et 23349 (9403) trouvées.
- **Essai hors ligne de la seconde preuve** (`node Console/test_seconde_preuve.js`) : **13/13 vert**.
- ⛔ **NON ESSAYÉ** : le chemin complet du worker sur une vraie création (il faut écrire chez Hektor), et la seconde preuve
  en réel (elle poserait 50129 sur 1001375 — écriture en base).

**Les compromis d'essai encore vivants (inventaire du 23/10, 00:2x) :**
- **chez Hektor**, les 40 plus récents (`sort=id`, pages 0 et 1) : **un seul essai, 50129** (ESSAI 8A B2, annonce 24113).
  50128 est supprimé ; les essais de septembre sur 24933 (50084 → 50092) ne sont plus là.
- **au registre**, lignes nées dans l'app (≥ 1 000 000) : **une seule d'essai vivante, 1001375** (= 50129, sans numéro).
  *(50048 sur le bac à sable 62774 est un essai du 29/08, déjà ANNULÉ — pas de moi, laissé tel quel.)*
- ⏰ **La nuit n'a pas encore tourné** au moment de l'inventaire (00:16 ; run à 05:00) : la ligne 1001375 n'a donc encore
  été ni rapprochée ni doublée (`last_seen_at` = 22/10 21:47, aucune ligne 50129).

## 7. POINT E — LA MODIFICATION MET DU PRÉREMPLI AU CARNET — audit du 23/10 *(Frédéric : « E »)* — lecture seule

### Ce que fait le code aujourd'hui (lu, pas supposé)
1. **L'écran** ouvre la modale de modification **déjà remplie** : carnet d'abord, registre ensuite (`App.tsx` ~16916),
   plus des valeurs d'office (prix de l'annonce dans « prix », 10 jours de rétractation…).
2. **La charge** est la même que pour une création (`api.ts:10646`) : **tous** les champs non vides partent.
3. **La RPC** `app_modifier_affaire_optimistic` (empreinte `a5297281`) met au carnet **tout champ non vide** de la charge
   (origine `modification_app`), et réécrit `montant` / `date` au registre.
4. **Le carnet PRIME** à l'écran et au préremplissage suivant. Le run ne le touche jamais.
5. **Le worker** juge au retour (`marquerLeCarnetRestant`, `retirerDuCarnetCeQuiEstArrive`) : ce qui est arrivé chez Hektor
   **sort** du carnet. ⚠ Seulement pour 8 champs (`CARNET_VERS_REGISTRE`) et **seulement si le travail réussit**.

### La mesure (carnet entier, 23/10)
- Le carnet est presque vide : **1 seule modification** y a laissé des lignes — **l'offre 33094 (KURCEBA, V720061672, 61672,
  négociateur arnaud.valla)**, modifiée par Frédéric le **13/10 à 09:37**. **6 lignes**, dont **au moins 4 sont du
  prérempli** : `date` (même jour), `jours_validite` = 10 (= la photo), `numero_mandat` = 18426 (= la photo),
  `jours_retractation` = 10 *(une offre n'a pas de rétractation)*, `prix_publique` = 180 000 *(le prix de l'annonce — le
  piège du 08/09)*. Seul `montant` = **160 000** ressemble à une saisie (photo : **16 000**).
- ⚠⚠ **ET LE TRAVAIL A ÉCHOUÉ** : 5 tentatives, `Reponse Hektor JSON invalide init Sous offre` (offre **acceptée** : Hektor
  refuse, voir mémoire « offre acceptée, Hektor refuse en silence »). Aucun verdict n'a été posé (`etat` vide).
  ➡ **Depuis 10 jours, l'app affiche 160 000 pour cette offre ; Hektor dit 16 000.** Lequel est vrai : **à Frédéric**.

### Pourquoi on ne peut PAS simplement « ne plus envoyer » les champs non touchés
Le worker de l'**offre** construit un formulaire **neuf** à partir de la charge (`montantOffre = tx.amount`…, l. ~14081 :
*« omettre serait un pari, pas une protection »*). Une charge allégée ferait partir une offre **sans montant**.
➡ **Ce qui part chez Hektor ne doit pas changer.** Seul ce qui entre **au carnet** doit changer.

### Le notaire acquéreur qui s'affiche en numéro (défaut R1)
La grille lit le carnet d'abord : `notaire_id` y vaut le **numéro** (10064499), posé à la création. Le nom est au registre
(`notaire_acquereur_nom`) mais passe après. Écran seulement.

### Proposition — NON CODÉE, en attente du « vas-y »
- **E1 (écran)** : à la modification, l'écran retient ce qu'il a **affiché à l'ouverture** et ajoute à la charge une liste
  `champs_touches` (les seuls champs dont la valeur a changé). Le reste de la charge **ne bouge pas**. Le worker ignore cette
  clé (0 occurrence dans `console_job_worker.js`).
- **E2 (base)** : `app_modifier_affaire_optimistic`, derrière un interrupteur `affaire_modif_champs_touches` : si la liste est
  là, **seuls ces champs** vont au carnet et au registre (`montant` / `date`). Liste absente (vieil écran en cache) ou
  interrupteur éteint → comportement d'aujourd'hui. Patch avec empreinte, inverse, répétition.
- **Notaire (écran)** : quand le carnet porte le même numéro que le registre, afficher le **nom** du registre.
- **Hors E, à décider** : (a) l'offre 33094 — 160 000 ou 16 000 ? ses 6 lignes de carnet ; (b) un travail **échoué** laisse
  ses valeurs au carnet sans verdict → c'est R3/R4.

### E1, E2 et le notaire — ✅ CODÉS, RÉPÉTÉS, NON POSÉS *(Frédéric, 23/10 : « vas-y E1 E2 et notaire »)*

**E1 — l'écran** (`App.tsx`, `api.ts`) : un état `statusChangeTouches` (remis à vide à l'ouverture de la modale) reçoit la
**clé de la charge** de chaque champ qu'une saisie change (`onChange`) : `amount`, `sale_price`, `transaction_date`,
`validity_days`, `signature_date`, `retraction_days`, `selected_mandat`, `buyer_notary_id`, `buyer_fees`, `buyer_fees_rate`,
`seller_fees`, `net_seller_price`, `sequestration` — plus `net_seller_price` quand le net est **déduit** d'une saisie. Envoyé
en `champs_touches`, **en modification seulement**. ⚠ **Le reste de la charge ne change pas d'un octet.**

**E2 — la base** : `supabase/patch_e_modif_champs_touches_2026-10-23.sql` (+ `_INVERSE`, `_REPETITION`), générateur
`phase2/checks/gen_patch_e_modif_champs_touches.py`. Empreinte **`a5297281` → `049643b8`**, 7 ancres d'une ligne,
interrupteur **`affaire_modif_champs_touches`** posé **éteint**. Allumé avec une liste : seuls ces champs vont au carnet ; le
registre (`montant`, `date`) ne bouge que si son champ est touché. ⚠ **Le montant se juge sur la PAIRE `amount` /
`sale_price`** : l'une touchée, on garde le calcul d'avant (sinon un prix de vente touché seul deviendrait le montant d'un
compromis). Le retour de la RPC porte `champs_touches` (pour la preuve).

**La répétition (annulée d'elle-même), sur l'offre d'essai 33026 (1000001, bac à sable 62774), charge PRÉREMPLIE : 8 sur 8.**
T1 éteint → les 6 champs (**le témoin inverse : le défaut**) · T2 allumé, montant seul → `montant` seul, date intacte · T3
liste vide → rien · T4 sans liste (vieil écran) → les 6, comme avant · T5 date + validité → ces deux-là · T6 prix de vente
seul → `montant` + `prix_publique` (la paire) · T7 le retour porte la liste · T8 l'inverse rend `a5297281`. **Contrôle
d'après** : empreinte `a5297281`, aucun interrupteur, carnet et registre de 1000001 intacts, **0 travail créé**.

**Le notaire** (`App.tsx`, grille des transactions) : quand le carnet porte le **même numéro** que le registre, la ligne
montre le **nom** du registre (toujours marquée « app »). Un numéro différent reste affiché tel quel.

**Contrôle du front** : `npm run build` ✅. ⛔ **Non vu à l'écran** (il faut une session) — à voir après le déploiement :
la ligne « Notaire acquéreur » de 1001375 doit montrer « Tiffany SELARL… » au lieu de 10064499.

**Ordre des gestes (accord de Frédéric à chaque étape) :**
1. **coller** `supabase/patch_e_modif_champs_touches_2026-10-23.sql` → 4 contrôles OK ;
2. **pousser** (le front part avec `champs_touches` ; interrupteur éteint = aucun effet tant qu'on n'allume pas) ;
3. **allumer** l'interrupteur ;
4. **essai réel** : une modification par l'écran sur une transaction d'essai, en touchant UN champ → au carnet, ce champ seul.
Pas de redémarrage de service : le worker n'est pas touché.

## 8. LA NUIT DU 23/10 — LE CHEMIN DE NUIT DE 1b, VÉRIFIÉ *(Frédéric : « le run est passé, fais la vérification »)*

Run `GTI Quotidien` du 23/10 à 05:00, **code 0**. Mesures à 07:27 (lecture seule) :

- ✅ **ADOPTÉE PAR L'ACQUÉREUR, SANS DOUBLON** : la ligne **1001375** porte maintenant **50129**, `present_in_hektor = true`,
  état `active`, adoptée à 04:46:27. **Une seule ligne** pour 50129 au registre. ➡ **Le chemin de nuit de 1b est prouvé** :
  sans 1b, la ligne portait notre identité 20000008 et la nuit aurait créé un doublon.
- ✅ **Hektor a CONFIRMÉ la saisie du clic** : montant 135 000, date d'acte 15/02/2027, séquestre 6 000, net vendeur 126 000,
  honoraires vendeur 9 000 — les mêmes. Les **mandants** sont arrivés (déduits du mandat par Hektor, comme prévu). Les deux
  **notaires** sont les mêmes personnes, sous **leur numéro Hektor** : 122190 (= notre 10064499) et 300465 (= notre 10165291).
- ⚠ **NOTÉ, PAS NOUVEAU** : `first_seen_at` passe à la date de la nuit d'adoption (22/10 21:47 → 23/10 04:46). Mesuré sur
  les 6 dernières adoptions (depuis le 03/09) : **toujours ainsi**. Ce n'est pas 1b.
- ⚠ **LE CARNET garde ses 11 lignes de création, sans verdict** — attendu : le contrôle au retour de la création, c'est R3.

### ⚠⚠ TROUVAILLE : LA NUIT PERD LE LIEN VERS UN CONTACT CRÉÉ DANS L'APP
- `app_contact_id` de 1001375 valait **20000008** (posé au clic par 1b) ; après la nuit il est **VIDE**.
- Sur **tout** le registre : **28 644** lignes dont l'acquéreur est un contact de Hektor ont leur lien, **0 perdu**. La **seule**
  ligne dont l'acquéreur est né dans l'app (≥ 20 000 000) l'a perdu : **1 sur 1**.
- **La cause, mesurée** : la nuit cherche le lien dans la doublure **locale** `app_contact` (`affaire_ledger.py` ~l. 756).
  Supabase connaît la paire (`20000008 → 605946`), la doublure locale **non** : elle porte `20000008` comme si c'était un
  numéro de Hektor, **sans cible**, avec une identité **inventée 10650807**. ⚠ Elle ne contient **aucune** identité
  ≥ 20 000 000.
- **Ampleur aujourd'hui** : 3 contacts nés dans l'app (20000007, 20000008, 20000009, tous des essais). **Demain** : chaque
  contact créé dans l'app (8a pièce 1, allumée le 21/10) qui deviendra acquéreur perdra son lien la nuit de l'adoption.
- ⚠ **Non mesuré** : les autres lecteurs de la doublure locale (relations, recherches, push des contacts) — ils pourraient
  avoir le même trou. **C'est un sujet d'IDENTITÉ, hors du point E** : à auditer, à décider par Frédéric.

### ⚠ Et mon correctif du NOTAIRE ne couvre que la journée du clic
Il compare le numéro du carnet (**notre** 10064499) à celui du registre : vrai **jusqu'à la nuit**. Après, le registre porte
**celui de Hektor** (122190) : les numéros diffèrent, la ligne remontrerait 10064499. Pour couvrir aussi l'après-nuit, il faut
comparer **la personne** (identité ↔ numéro Hektor, `app_contact_current`) — ou que R3 retire du carnet ce que Hektor a
confirmé. **Non codé.**

✅ **50129 SUPPRIMÉ PAR L'APP le 23/10 à 07:37** *(Frédéric : « supprime »)* — travail `delete_hektor_compromis` `done` en
11 s : supprimé chez Hektor, statut redescendu à « Actif », ligne 1001375 effacée du registre (journal écrit), **11 lignes
retirées du carnet**. Vérifié par moi : `CompromisById 50129` → `trouve: false` ; liste de 24113 → aucun compromis ;
registre et carnet → 0 ligne ; bien « Actif ».

### BILAN DES ESSAIS RÉELS DU 22-23/10 (VA6482) — ce qu'ils ont révélé
| # | défaut | état |
|---|---|---|
| 1 | **le doublon de nuit** : l'acquéreur rangé sous notre identité | ✅ corrigé (1b), **prouvé la nuit du 23/10** |
| 2 | **la preuve immédiate ratait** les compromis créés (Hektor ignore `sort=dateStart` depuis fin sept.) | ✅ corrigé (tri par numéro), prouvé en lecture ; vraie création non revue |
| 3 | rien ne rattrapait un numéro manqué avant la nuit | ✅ seconde preuve (1a), active |
| 4 | **le nom du notaire** s'affichait en numéro | 🟡 corrigé pour la journée du clic seulement ; l'après-nuit reste |
| 5 | **la modification met du prérempli au carnet** (point E) | 🟡 codé et répété (8/8), **non posé** |
| 6 | **la nuit perd le lien vers un contact créé dans l'app** | 🔴 trouvé le 23/10, **non corrigé** — sujet d'identité |
| 7 | une modification **échouée** laisse ses valeurs au carnet sans verdict (offre 33094 : app 160 000, Hektor 16 000) | 🔴 non corrigé — R3/R4, et 33094 à trancher |

## 9. DÉFAUT 6 — POURQUOI ON NE L'AVAIT PAS AVANT — audit du 23/10 *(Frédéric : « pourquoi ce problème 6, on n'avait pas cela avant, nous avions résolu ce problème d'acquéreur »)* — lecture seule

### Ce que 1b avait résolu, et ce qui est différent
- **1b** règle la **clé du rapprochement** (`hektor_acquereur_id` = le numéro Hektor) : **prouvé cette nuit**, aucun doublon.
- Le défaut 6 porte sur **une autre colonne** : `app_contact_id`, le **lien vers notre fiche contact**. La nuit le recalcule à
  partir du **registre local d'identité** (`app_contact`, dans `phase2.sqlite`), pas à partir de Supabase.

### Pourquoi « avant » ça marchait
- Avant le 21/10, un contact créé dans l'app partait **d'abord chez Hektor** ; son identité lui était donnée **ensuite, la
  nuit, par le registre local**, sous la forme « identité 1065xxxx ↔ numéro Hektor ». Exemple mesuré : **10650570 ↔ 605717**
  (créé le 07/10) — la nuit le connaît, l'offre 1001361 garde son lien.
- **Depuis le 21/10 (8a pièce 1, « naître complet »)**, le contact reçoit **tout de suite** son identité **chez Supabase**,
  dans la plage **≥ 20 000 000** (20000007, 20000008, 20000009). **C'est la première fois** que le registre local voit
  arriver des contacts qui ont **déjà** leur identité : il n'en avait **jamais** vu (mesuré : ces 3-là seulement).

### Ce que fait alors le registre local — LA CAUSE
`phase2/identite/registre_contacts.py` (règle « L4-c-bis » du 24/09) : pour une clé ≥ 10 M, il **garde la clé** dans
`hektor_contact_id`… **mais lui attribue quand même un NOUVEAU numéro** et **laisse le numéro Hektor vide** :

| contact (Supabase) | ligne fabriquée dans le registre local |
|---|---|
| 20000007 ↔ 605925 | `app_contact_id` **10650777**, `hektor_contact_id` 20000007, cible **vide** (22/10 04:39) |
| 20000008 ↔ 605946 | **10650807**, 20000008, cible **vide** (23/10 04:38) |
| 20000009 ↔ 605947 | **10650808**, 20000009, cible **vide** (23/10 04:38) |

La bonne paire existe pourtant en local, mais dans la table **complémentaire** (`app_contact_identite_app`, descendue de
Supabase). ➡ **Le défaut dormait depuis le 24/09** : la règle n'avait jamais rencontré un vrai contact né dans l'app.

### Qui en souffre
1. **Le registre des transactions** (`affaire_ledger.py`) : ne lit **que** `app_contact` → ne trouve pas 605946 → lien
   **vide** (1001375, cette nuit).
2. ⚠⚠ **`pousser_numeros_contact.py`** (dans le run, `run_full_pipeline.ps1:1436`) renvoie chaque nuit à Supabase le numéro
   du registre local → **le contact 20000007 porte DÉJÀ `app_contact_id = 10650777` chez Supabase** (au lieu de 20000007).
   20000008 et 20000009 sont encore justes, **mais suivront probablement la nuit prochaine**.
3. **12 fonctions Supabase lisent `app_contact_current.app_contact_id`** — dont `app_change_annonce_status_optimistic` (1b :
   le lien posé au clic), `app_contact_id_propager`, `app_edit_contact_optimistic`, `app_edit_search_optimistic`… Pour
   20000007, elles liraient désormais **10650777**, un numéro qui n'est **la fiche de personne**.
- **Pas encore répandu** (mesuré) : 0 relation, 0 transaction, 0 recherche, 0 fiche ne porte 10650777 / 10650807 / 10650808.
- **Ampleur** : 3 contacts, tous des **essais**. **Mais chaque contact créé dans l'app depuis le 21/10 y passera.**
- *(Lecteurs vérifiés et sains : le build des contacts lit les deux tables, la table complémentaire en second.)*

### Pistes — NON CODÉES, À DÉCIDER PAR FRÉDÉRIC
- **A** `registre_contacts.py` : une clé ≥ 20 M **est** l'identité → ne pas en fabriquer une autre, et prendre le numéro
  Hektor dans la table complémentaire. Réparer les 3 lignes locales.
- **B** `affaire_ledger.py` : lire **aussi** la table complémentaire (comme le build).
- **C** **arrêter la propagation** : `pousser_numeros_contact.py` ne doit jamais envoyer un numéro < 20 M pour une identité
  ≥ 20 M — et **remettre 20000007** chez Supabase (écriture en production).
- ⏰ **Urgence** : sans rien faire, la nuit prochaine écrit probablement 10650807 / 10650808 sur 20000008 / 20000009.

### ⛔ CORRECTION DE L'AUDIT CI-DESSUS — Frédéric avait raison *(« le worker crée le contact tout de suite, puis récupère l'id Hektor, il a 2 numéros comme avant, non ? qu'est-ce qui a changé ? »)*
- **Rien n'a changé dans la création.** Depuis le **21/09** (L4-b, `28b2fbd`), `app_create_contact_optimistic` donne **toujours**
  l'identité à la naissance (`app_contact_identite_seq`), interrupteur ou pas ; le worker crée chez Hektor et rapporte le
  numéro → **deux numéros**, comme avant. **8a pièce 1 n'a ajouté que les autres champs.** Mon « depuis le 21/10 » était FAUX.
- **Mon exemple « d'avant » était faux aussi** : 10650570 (605717, KURCEBA) est un contact **créé dans Hektor**, pas dans l'app.
- **Ce qui est vrai, mesuré** : le distributeur a été placé à **20 000 000 le 22/09** et n'a donné que **9 numéros** en un mois.
  Créations de contact **par l'app** : 2 le 18/09, 2 le 21/09 (10000001/2, des essais, supprimés), puis **AUCUNE du 22/09 au
  20/10**, puis nos essais du 21-22/10 (20000006 à 20000009). Les négociateurs créent leurs contacts **dans Hektor**.
- ➡ **La nuit n'avait JAMAIS vu un contact né dans l'app avec une identité ≥ 20 000 000** avant celle du 22/10 (20000007).
  Le défaut du registre local est **ancien** (règle du 24/09) ; **nos essais l'ont simplement déclenché pour la première fois.**
  Le reste de l'audit (la cause, la propagation sur 20000007, les pistes A/B/C) est inchangé.

## 10. DÉFAUT 6 — L'HISTOIRE : POURQUOI LE PROJET EST FAIT AINSI, ET COMMENT LE RÉSOUDRE *(Frédéric : « audite mon projet, comment et pourquoi avons-nous fait cela, il y a bien une raison, et surtout comment résoudre »)* — lecture seule

### Les décisions, dans l'ordre (commits et plan)
| date | décision | pourquoi |
|---|---|---|
| 19/08 | **le serveur local numérote les contacts** (registre `app_contact`) — « Supabase reçoit la série, il ne la fabrique jamais » | une seule source de numéros ; le serveur reconstruit tout chaque nuit depuis le miroir de Hektor |
| 21/09 L4-a/L4-b (`627552f`, `28b2fbd`) | **un objet NAÎT dans l'app avec son numéro** : distributeur Supabase pour le contact, l'annonce, la recherche (option B : identité / cible) | ne plus attendre Hektor (« naître dans l'app ») ; préparer la coupure |
| 21/09 | ⭐ **« le serveur remplit LES DEUX CASES : l'objet arrive avec un numéro d'app → ON L'ADOPTE »** — `adopter_numeros_app.py` | sans adoption, le serveur fabriquerait un **second numéro** à l'objet né dans l'app |
| 22/09 L4-c (`b57d78d`) | **trois étages** : < 10 M Hektor · 10 M – 20 M la doublure (contacts venus de Hektor) · **≥ 20 M nés dans l'app** ; distributeur placé à 20 M | sans cela, le registre local et le distributeur auraient donné **le même numéro** à deux personnes |
| 23/09 | **bascule** : `hektor_contact_id` porte l'identité, `hektor_target_id` le numéro Hektor | « une personne, un numéro » |
| 24/09 L4-c-bis (`e414fe0`) | le registre range un contact NEUF **venu de Hektor** dans la bonne colonne | 23 contacts créés chez Hektor restaient sous leur numéro Hektor |
| 24/09 C.9-a | ⭐ **pour l'ANNONCE, le même défaut est FERMÉ** : `descendre_correspondance_annonces.py` apprend le numéro de l'app **avant** le bootstrap, et un déclencheur interdit qu'un numéro de la plage app entre **sans adoption** | la liste le dit : « **jumeau du défaut contact du 21/09** » ; `adopter_numeros_app` = « 0 appelant, 3 défauts » |

### Ce qui manque — LA VRAIE CAUSE
- **Pour l'annonce**, l'adoption a été **branchée** (C.9-a, dans le run, éprouvée).
- **Pour le contact**, la moitié a été faite : `descendre_correspondance_contacts.py` apprend la paire (20000008 ↔ 605946)
  et **le build** s'en sert — c'est pour ça que la fiche est juste chez Supabase. **Mais le registre `app_contact` n'adopte
  pas** : `adopter_numeros_app.py` n'a **jamais été mis dans le run** (« inerte, posé avant d'en avoir besoin »), et il est
  resté écrit pour **avant** la bascule du 23/09 (il range l'identité avec `hektor_contact_id` vide). L4-c-bis (24/09) n'a
  pensé qu'aux contacts **venus de Hektor** : pour une clé ≥ 10 M il garde la clé mais **tire un numéro neuf** et **jette la
  cible** — alors que la source locale la porte (`app_contact_current` : 20000008 / cible 605946, vérifié).
- **Pourquoi personne ne l'a vu en un mois** : **aucun contact n'a été créé par l'app du 22/09 au 20/10** (les négociateurs
  créent dans Hektor). Le défaut attendait le premier — nos essais du 21-22/10.

### LA SOLUTION — le jumeau de C.9-a, pour le contact (NON CODÉE)
1. **`registre_contacts.py` ADOPTE** : une clé neuve **≥ 20 000 000** est une identité née dans l'app → `app_contact_id` =
   **cette clé**, `hektor_contact_id` = cette clé, `hektor_target_id` = **la cible que la source porte déjà**. Aucun numéro
   tiré. *(Une clé < 10 M garde la règle d'aujourd'hui : numéro tiré par le registre.)*
2. **Le garde-fou, comme pour l'annonce** : un numéro ≥ 20 M n'entre dans `app_contact` **que s'il est égal à l'identité**
   (déclencheur, ou contrôle dans le script) — sinon **arrêt bruyant** plutôt qu'un second numéro muet.
3. **Réparer les 3 essais** : local `app_contact` (10650777 / 10650807 / 10650808 → 20000007 / 20000008 / 20000009, cibles
   605925 / 605946 / 605947), local `app_search_registry` (77235 : 10650807 → 20000008), **Supabase** `app_contact_current`
   de 20000007 (`app_contact_id` 10650777 → 20000007). Sauvegarde datée avant. *(Mesuré : 10650777/807/808 ne sont utilisés
   nulle part ailleurs, ni en local ni chez Supabase.)*
4. **Alors, rien d'autre à changer** : la nuit des transactions trouvera 605946 → 20000008 (le lien tient), et
   `pousser_numeros_contact.py` renverra 20000008 → 20000008 (juste). Les pistes B et C d'avant deviennent **inutiles**.
- ⏰ **Avant la nuit prochaine**, sinon 20000008 / 20000009 reçoivent probablement leur faux numéro chez Supabase.
- **Ce que ça pourrait casser** : rien pour les 356 000 contacts venus de Hektor (clé < 10 M, chemin inchangé) ; à éprouver
  sur **copie** de la base avec le **vrai** script, comme L4-c-bis (17/17) — y compris le témoin inverse (l'ancien script
  refabrique 10650807).

### DÉFAUT 6 — L'ADOPTION, CODÉE ET ÉPROUVÉE *(Frédéric, 23/10 : « oui vas-y »)*

**Le code** — `phase2/identite/registre_contacts.py` :
- `adopter_les_nes_dans_l_app()` passe **avant** la numérotation : une clé neuve **≥ 20 000 000** est inscrite **sous son
  propre numéro**, avec la cible que la couche porte (numéro de Hektor < 10 M, et seulement si aucune autre ligne ne la porte).
  Une cible qui arrive plus tard se pose une nuit suivante. Les clés < 20 M : **chemin inchangé**.
- **Garde-fou** (jumeau du déclencheur de C.9-a) : si le passage a fait **monter** le nombre de contacts nés dans l'app à deux
  numéros, il **annule tout** et sort en **5**. Les 3 lignes d'avant le 23/10 sont **signalées** (« ATTENTION … DEUX
  numeros 3 »), sans arrêter la nuit.
- ⚠ **Ce fichier est lu par le run de cette nuit** (pas de redémarrage, pas de déploiement) : il est **actif dès 05:00**.

**Les essais** :
- `phase2/checks/test_adoption_contact_ne_dans_app.py` — **22/22**, le VRAI script sur bases jetables, lu comme la nuit le lit
  (table de `affaire_ledger.py`, vraie fonction du build). **Témoin inverse** : l'ancien script (`c92003f`) refabrique bien
  un second numéro sans cible. **Mutant** : sans l'adoption, le garde-fou arrête le passage (code 5) et n'écrit rien.
  ⭐ **L'essai a attrapé DEUX défauts de mon premier jet** : (a) le garde-fou jugeait « posé par ce passage » à la seconde près
  → faux arrêt ; remplacé par un compte avant / après ; (b) le symbole ⚠ dans un message **faisait planter le script** sur
  une console non UTF-8 → message en ASCII.
- Non-régression : `test_l4c_bis_contacts_neufs.py` **vert** (après avoir rendu l'adoption tolérante à une couche sans
  colonne cible) · `test_seconde_passe_contacts_neufs.py` **7/7**. `test_registre_ne_double_pas.py` échoue sur la **vraie
  base** : « 3 sans case cible » = **nos 3 lignes parasites** — il les voyait déjà ; il repassera au vert après la réparation.
- **Répétition sur copie** des 4 tables réelles (356 629 lignes) : code 0, **0 ligne neuve**, les 3 signalées. **Ancien script
  sur la même copie : sortie identique** (hors la ligne d'alerte).

**La réparation des 3 essais — PRÊTE, NON JOUÉE** — `phase2/identite/reparer_contacts_nes_dans_app_2026-10-23.py`
(mesure seule par défaut, `--ecrire`, `--inverse`, `--base`). 10650777 / 10650807 / 10650808 → 20000007 / 20000008 / 20000009,
cibles 605925 / 605946 / 605947, recherche 77235 → 20000008 ; vérifie chaque ligne avant d'écrire, **sauvegarde datée**
(`app_contact_avant_reparation_20261023`, `app_search_registry_avant_reparation_20261023`), contrôle final avant d'enregistrer.
**Répétée sur la copie : 11/11** (mesure, réparation, rejouer = rien, nuit simulée = plus d'alerte, **605946 → 20000008**,
retour arrière exact). ⭐ **Chez Supabase, rien à écrire à la main** : la nuit suivant la réparation, `pousser_numeros_contact`
renverra 20000007 → 20000007 (vérifié sur la copie).
- ⏰ **À jouer AVANT le run de 05:00** (écriture dans la base du serveur : **accord de Frédéric**), sinon la nuit recopie
  probablement 10650807 / 10650808 sur 20000008 / 20000009 chez Supabase.

**Noté en passant, PAS de moi, non traité** : chaque passage du registre « relève » **7 658** contacts marqués absents
(vraie base : 7 661 absents) — l'ancien script fait **exactement** pareil sur la même copie. Probable va-et-vient avec
`marquer_contacts_disparus.py`. À regarder à part.

### ✅ RÉPARATION JOUÉE SUR LA VRAIE BASE — 23/10 à 08:24 *(Frédéric : « vas-y »)*
Rien ne tournait. Mesure seule identique à la copie, puis `--ecrire` → code 0. **Vérifié en lecture seule** :
- 20000007 / 20000008 / 20000009 portent **leur numéro** et leur cible (605925 / 605946 / 605947) ; **0** contact à deux
  numéros ; **0** numéro parasite restant ; recherche 77235 → 20000008 ; registre 356 629 lignes, 356 629 numéros distincts.
- **La nuit des transactions** relie 605925 / 605946 / 605947 → 20000007 / 20000008 / 20000009.
- Sauvegarde : `app_contact_avant_reparation_20261023` (3 lignes) et `app_search_registry_avant_reparation_20261023` (1).
- `test_registre_ne_double_pas.py` sur la vraie base : **5/5 vert** — après avoir corrigé son contrôle (4), qui exigeait un
  plus haut numéro < 20 M : faux par construction depuis l'adoption ; il ne mesure plus que les numéros **tirés** par le
  registre (plus haut : 10 650 806). `test_adoption_contact_ne_dans_app.py` toujours **22/22**.
- ⏰ **À vérifier demain matin** : chez Supabase, `app_contact_current.app_contact_id` de **20000007** doit être revenu à
  **20000007** (renvoyé par `pousser_numeros_contact`), et 20000008 / 20000009 doivent être restés justes.

### PEUT-ON ÉPROUVER L'ADOPTION AUJOURD'HUI, SANS ATTENDRE LA NUIT ? — audit du 23/10 *(Frédéric)* — lecture seule
**Oui, pour la pièce corrigée.** Ce qui se passe le jour d'une création (lu dans le code) :
1. l'écran crée le contact chez nous (identité ≥ 20 M) → le worker le crée chez Hektor (`create_hektor_contact`) ;
2. il enchaîne la **relecture** (`refresh_console_contact_data` → `refresh_contact_inproc.py`) : elle apprend la paire
   (`app_contact_identite_app`, remède 8a du 21/10) puis **reconstruit la couche locale pour ce contact** (`build --contact-id`)
   → `app_contact_current` local porte l'identité **et** le numéro Hektor ;
3. le **registre** (`registre_contacts.py`), lui, ne tourne **que la nuit** — c'est la seule pièce qui attend.
➡ Après la relecture, le registre a tout ce qu'il lit. On peut le faire tourner tout de suite :
- **A — sur une COPIE des 4 tables réelles** (comme la répétition de ce matin) : **aucune écriture** dans la base du serveur ;
  prouve l'adoption sur le **vrai** contact fraîchement créé. La vraie inscription se fait la nuit. ⭐ recommandé
- **B — sur la VRAIE base** : inscrit le contact dès maintenant. Effets de bord mesurés : il relève aussi les **7 658** marques
  « absent » (comme chaque nuit ; le run les remet ensuite par `marquer_contacts_disparus.py`, aucun autre lecteur trouvé),
  verrou d'écriture de quelques secondes (les relectures attendent 30 s). N'apporte rien de plus que A pour la preuve.
**Ce qui ne peut PAS s'éprouver de jour** : le lien des transactions (`affaire_ledger.py`) et le renvoi des numéros à Supabase
(`pousser_numeros_contact.py`) sont des étapes du run ; elles se vérifient demain matin (avec le retour de 20000007).
**Gestes chez Hektor** : créer le contact d'essai (puis le supprimer après la vérification de demain) — **accord** à chaque fois.

### ✅ ESSAI A RÉEL — 23/10 à 08:38 *(Frédéric : « ok option A »)*
- **Création par l'écran** (compte de formation FRANCK GERPHAGNON, propriétaire, **sans annonce reliée** — l'étape 2 « Terminer »
  le permet, comme pour l'essai B2) : **ESSAI 8A D1 / Adoption**, Firminy 42700. `create_hektor_contact` **done en 11 s** →
  identité **20000010**, numéro Hektor **605957**. Relecture **done** à 08:39 : « paire apprise : identite 20000010 <-> numero
  Hektor 605957 ».
- Mesuré : Supabase (20000010 / 605957 / `app_contact_id` 20000010) ✅ · couche locale (20000010 / 605957) ✅ · correspondance
  ✅ · registre local : **rien encore** (étape de nuit) — exactement ce que l'audit disait.
- **Registre sur COPIE des 4 tables réelles : 9/9.** NOUVEAU : « 1 adopté », ligne **(20000010, '20000010', '605957')**, la nuit
  des transactions relierait **605957 → 20000010**, aucun contact à deux numéros. **ANCIEN (témoin inverse)** : second numéro
  sans cible, 605957 non relié. **Vraie base inchangée.**
- ⏰ **Demain matin** : registre réel → 20000010 adopté vers 06:40 ; Supabase → 20000007 revenu à 20000007. Puis **supprimer
  les contacts d'essai** 20000007 / 20000008 / 20000009 / 20000010 (accord de Frédéric).

## 11. LES NUMÉROS DE TRANSACTION ONT-ILS LE MÊME PROBLÈME ? — audit du 23/10 *(Frédéric)* — lecture seule
**Non.** La transaction a été le **premier** objet « né dans l'app » (20/08) : son adoption a été construite **dès le départ**,
et elle a déjà payé, et corrigé, le même genre de défaut.
- **Deux séries qui ne se croisent pas** : la nuit (`affaire_ledger.py`) numérote **sous 1 000 000** (`PLAGE_RESERVEE_APP`,
  plus haut aujourd'hui : **30 762**) ; l'app prend **la séquence Supabase** `app_affaire_id_app_seq` (≥ 1 000 000, dernière
  valeur : **1 001 375**).
- ⚠ **Le défaut a existé, du 27/08 au 01/09** : le run comptait « le plus grand + 1 » sur toute la table, a pris 1 000 008 →
  1 000 312 pour 305 vieilles affaires Hektor, et la séquence de l'app est tombée sur des numéros pris (« duplicate key ») →
  **aucune transaction créable depuis l'app pendant 5 jours**. **Corrigé le 01/09** (le run ne regarde plus que sous
  1 000 000). Les **323** lignes d'août restées dans la plage de l'app sont **gardées par décision** (« un dossier ne perd jamais
  son numéro »).
- **L'adoption existe depuis le 25/08 (C.4)** : une transaction née dans l'app est **reprise** la nuit, par son **triplet**
  (annonce, type, numéro Hektor — depuis le 02/09) ou, faute de numéro, par son **acquéreur** (une seule candidate). ✅
  **Prouvée cette nuit** : 1001375 a gardé son numéro sous 50129.
- **Mesuré le 23/10** : 0 ligne au-delà de la séquence (pas de collision possible) · 0 triplet en double · 8 transactions
  nées dans l'app vivantes, **toutes** avec leur numéro Hektor, **0** sans numéro, **0** jumelle de nuit. Un seul cas à
  regarder (61672) : **deux offres distinctes** du même acquéreur (33094 née chez Hektor le 06/10, 33098 née dans l'app le
  13/10) — une ligne chacune, **pas un doublon**.
- **Ce qui reste fragile, déjà connu** : l'adoption par l'acquéreur exige le **même numéro d'acquéreur** des deux côtés —
  c'était le défaut 1 (corrigé par 1b, prouvé) ; et le **lien vers notre fiche contact** — le défaut 6 (corrigé aujourd'hui).

### ✅ E2 POSÉ EN PRODUCTION — 23/10 *(Frédéric : « j'autorise : colle le patch E2, interrupteur éteint »)*
Empreinte vérifiée avant : `a5297281`. Patch passé sans erreur. **Les 4 contrôles : OK** — empreinte **`049643b8`** ·
interrupteur `affaire_modif_champs_touches` **éteint** · `authenticated` peut toujours appeler · `SECURITY DEFINER` gardé.
➡ **Aucun effet tant que l'interrupteur est éteint.** Reste : **pousser** (le front E1 + le nom du notaire partent avec), puis
**allumer**, puis **essai réel** (une modification par l'écran en touchant UN champ → au carnet, ce champ seul).
Retour arrière : `supabase/patch_e_modif_champs_touches_2026-10-23_INVERSE.sql`.

## 12. R2 — « LA NUIT RESPECTE L'ATTENTE » : audit du 23/10 *(Frédéric : « ensuite on attaque R2 »)* — lecture seule

### Ce que R2 doit faire (§3) et la règle qu'il ne doit pas casser
R2 repose sur le registre, **pendant la nuit et avant les chaînes**, les seuls champs du carnet **encore en attente**. Il ne
doit **pas** redevenir **le gel** du 16/09 (mémoire « le registre est à Hektor, le carnet est à nous ») : une valeur de l'app qui
gagne **pour toujours** masque ce que les négociateurs corrigent ensuite dans Hektor. La différence tient en un mot : **la
protection doit TOMBER** dès que Hektor a confirmé — et ce sont **les verdicts** qui la font tomber.

### ⚠ L'ordre convenu était R1 → R3 → R2, et il n'est pas décoratif
C'est **R3** (le contrôle au retour de la **création**) qui pose le verdict « arrivée » et sort la ligne de l'attente. Sans R3,
une ligne de création n'a **jamais** de verdict (D3) → R2 la protégerait **à vie** → **le gel**.

### La mesure : ce que R2 protégerait s'il était allumé AUJOURD'HUI
Le carnet compte **17 lignes, 3 transactions, 0 verdict** :
| transaction | origine | ce que R2 ferait |
|---|---|---|
| **30712** — offre 33094 KURCEBA (**vraie**) | modification **échouée** le 13/10 | ⛔ **imposerait 160 000** au registre, alors que Hektor dit 16 000 — et pour toujours |
| 1001339 — offre 33050 (essai, 24933) | création du 04/09 | protégée depuis 7 semaines, sans fin |
| 1001361 — offre 33098 KURCEBA | création du 13/10 | idem |
Et sur les **trois**, la **date** du carnet est un jour (`2026-10-06`) quand le registre porte l'heure (`2026-10-06 16:12:54`) :
R2 **effacerait l'heure**, et l'offre se chaîne sur cette date. Tous les autres champs sont **égaux** à ceux de Hektor — ils
sont donc *de fait* arrivés, mais **personne ne l'a constaté**.

### Les conditions pour poser R2 sans recréer le gel
1. **R3 d'abord** : un verdict au retour de chaque **création** (le code de la modification existe, on le rebranche).
2. **Un travail ÉCHOUÉ ne laisse pas une attente** : aujourd'hui ses valeurs restent au carnet sans verdict (30712). Il faut un
   verdict « échec » (ou les retirer), et le montrer. *(C'est le défaut 7.)*
3. **E allumé** (pas de prérempli au carnet) — posé ce jour, interrupteur éteint.
4. **Comparer une date sans l'heure à une date avec l'heure** comme égales (sinon faux « en attente », et R2 rogne l'heure).
5. **Une durée maximale ?** (question ouverte du §3) — à trancher par Frédéric.
6. **Les 3 transactions d'aujourd'hui** : leur poser un verdict (ou les nettoyer) **avant** d'allumer R2 ; et **30712 : 160 000
   ou 16 000** (décision de Frédéric).

## 13. R3 — LE CONTRÔLE AU RETOUR DE LA CRÉATION : audit du 23/10 *(Frédéric : « R3 d'abord, commence par l'audit »)* — lecture seule

### Le modèle existe : la MODIFICATION (worker, ~l. 15060-15495)
Après une modification prouvée : relecture **par numéro** → `retirerDuCarnetCeQuiEstArrive` → `reporterAuRegistre` (ce que
Hektor a **retenu** va au registre : prix, net, honoraires, séquestre, dates, validité, **acquéreurs, mandants**) →
`marquerLeCarnetRestant` (verdict par ligne : **arrivée** → retirée · **en_attente** · **conflit** · **inconnu**). Le verdict
compare 3 valeurs : la **photo** (Hektor avant), la **saisie**, la **relue**.

### La création s'arrête avant (D3, confirmé dans le code)
`prouverTransactionCreee` (~l. 15625) : preuve en 3 lectures → confirmation → `poserIdTransactionSurAffaire` → **fin**. Aucun
report, aucun verdict. Les lignes `creation_app` restent au carnet **sans verdict, pour toujours** (1001339 depuis le 04/09).

### Les 6 trous que R3 doit fermer
1. **Pas de photo à la création** : rien n'existait chez Hektor avant → la règle actuelle rend « **inconnu** » pour TOUT.
   Il faut une règle de création : relue = saisie → **arrivée** (retirée) · relue vide → **en_attente** · sinon → **conflit**.
2. **Les données relues selon le genre** (mesuré ce jour, lecture seule) :
   - **compromis** : la liste les a déjà en main (prixPublique, prixNetVendeur, sequestre, dateStart, dateSignatureActe,
     dateEnd = fin de rétractation, honorairesEntree/Sortie, acquereurs, mandants) → **0 requête de plus** ;
   - **vente** : la liste aussi (prix, date, honoraires, honorairesEntree/Sortie, acquereurs, mandants) → **0 de plus** ;
   - **offre** : la liste ne rend **ni montant, ni validité, ni date** → il faut **1 lecture par numéro** (OffreById :
     montant, validite, dateProposition). ⚠ Le quota de Hektor : +1 requête par offre créée.
3. **Une date sans heure ≠ la même date avec heure** pour `memeValeurHektor` (« 2026-10-06 » contre « 2026-10-06 16:12:54 »).
   ⚠ **Défaut latent AUSSI en modification** : une date d'offre inchangée y serait jugée « en_attente » à tort.
4. **Les champs sans colonne au registre** — `prix_publique`, `honoraires`, `jours_retractation`, `notaire_id`, `taux_honoraires` :
   jugés « inconnu » aujourd'hui. Certains se jugent par une autre clé (prix_publique ↔ prixPublique/prix ; honoraires ↔
   honorairesSortie ; rétractation ↔ dateEnd − dateStart). Le notaire n'est **pas** dans la relecture (et se compare entre
   deux numérotations). ➡ **À trancher** : ce qui ne se juge pas reste « inconnu » (et R2 l'ignore), ou sort à la confirmation ?
5. **Deux autres chemins donnent un numéro sans verdict** : la **seconde preuve** (1a) et **l'adoption de nuit**. Proposé : un
   **verdict de rattrapage** à la relecture d'une annonce, pour les lignes sans verdict d'une transaction qui a son numéro —
   il couvre aussi les 3 transactions d'aujourd'hui (1001339, 1001361, 30712).
6. **Un travail ÉCHOUÉ laisse ses valeurs** (30712, modification refusée le 13/10). Proposé : verdict **« echec »** (montré en
   rouge, **ignoré par R2**) quand le travail finit en erreur.

### Ce que ça pourrait casser ailleurs
- **Le worker** : code neuf **après** la pose du numéro, entouré d'un `try` (comme le report de la modification : « on
  n'échoue jamais le travail pour ça »). Derrière un interrupteur. **Redémarrage des 4 services** (Frédéric, file vide).
- **L'écran** : il lit le carnet d'abord — une ligne retirée « arrivée » montre la valeur du registre, qui **est** la même.
- **La comparaison des dates** : `memeValeurHektor` sert aussi aux preuves de modification ; la rendre tolérante à l'heure ne
  peut que faire passer « conforme » un jour égal — à éprouver hors ligne sur les deux chemins.
- **Les chaînes** : `reporterAuRegistre` écrit `date` ; une date relue identique ne change rien.
- **Le quota de Hektor** : +1 lecture par offre créée.
- **Essais** : hors ligne (comme `test_seconde_preuve.js`), puis réel : un compromis sur VA6482 et une offre sur le bac à
  sable 62774 → lignes « arrivée » retirées, registre complété.

### R3 et la coupure *(Frédéric, 23/10 : « R3 crée une dépendance à Hektor ? mon système survivra-t-il à la coupure ? »)*
- **R3 n'ajoute pas de dépendance** : il ne s'exécute **qu'après** un travail réussi chez Hektor, pour **constater**. Il ne
  bloque rien et n'est jamais attendu : depuis **R1**, toute la saisie est au registre **dès le clic**. Sans réponse de Hektor,
  R3 ne tourne simplement pas.
- **La règle à tenir en le codant** : « pas de réponse de Hektor » ne doit **jamais** devenir un conflit, une alarme ou une
  attente qui bloque. R2 / R3 / R4 sont un mécanisme **de la période de transition** (deux systèmes vivants) : à la coupure, **un
  interrupteur** les endort (plus de travail vers Hektor, plus d'import de nuit, le carnet n'a plus rien à attendre).
- **Ce qui casserait à la coupure AUJOURD'HUI, indépendamment de R3** (déjà notés, « à part, pour la coupure ») :
  **T1** — le worker défait l'état quand Hektor ne répond pas (décision du 29/08) ; **T3 / D7** — modifier une transaction
  **sans numéro Hektor** est refusé (`modification_sans_numero_hektor`) ; et le **travail de création** resterait « en cours »
  sans worker. Plus, hors transactions : la diffusion portails et la signature (note de stratégie du 01/07).

### R3 — CODÉ ET ÉPROUVÉ HORS LIGNE, NON ACTIF *(Frédéric, 23/10 : « ok donc reprends R3 »)*
**Le code** — `Console/console_job_worker.js`, bloc « R3 » placé à côté de 1a :
- `controlerLeCarnet(job, annonce, {appAffaireId, chez, force})` : **une seule fonction**, deux appelants —
  `prouverTransactionCreee` (juste après la pose du numéro : `reporterAuRegistre` puis verdict, `force`) et
  `handleRefreshConsoleData` (le **rattrapage**, après la seconde preuve). Interrupteur `R3_CONTROLE_CARNET`.
- **Règle de création** (sans photo) : relue = saisie → **arrivée** (retirée) · pas encore lisible → **en_attente** · autre
  valeur → **conflit** · champ que ce genre n'a pas → **sans_objet** · travail échoué → **echec**. Une ligne de modification
  garde la règle d'avant (photo).
- **Les 5 champs** : honoraires (`honorairesSortie`, `honoraire_acquereur` pour l'offre) · rétractation (`dateEnd − dateStart`) ·
  prix public (`prixPublique` / `prix`) · **notaire et n° de mandat : le lendemain**, au registre relu par la nuit
  (`last_seen_at` postérieur à la saisie), le notaire comparé **par la personne** (`app_contact_current`) · taux **recalculé**
  (jamais « conflit »).
- **Offre** : 1 lecture par numéro (montant, validité, dateProposition) — à la création et au rattrapage.
- **Travail en cours** → on ne juge pas. **Travail échoué** → « echec » (reconnu par `ecrit_le = created_at`, même transaction).
- ⛔ **Règle de la coupure** : API muette ou transaction introuvable → **rien n'est jugé, aucune alarme**.
- Rattrapage : seulement les lignes sans verdict / en attente, **pas plus d'une relecture chez Hektor toutes les 6 h** par ligne.
- `memeValeurHektor` : « 2026-10-06 » = « 2026-10-06 16:12:54 » (sert aussi aux preuves de **modification**).
- Écran (`App.tsx`) : « échec, non envoyé » et « sans objet » s'affichent.

**Les essais** : `Console/test_controle_carnet_r3.js` — **22/22**, sur le vrai code et les valeurs réelles des 22-23/10.
**Témoin inverse** : l'ancien verdict rend « inconnu » pour les 11 lignes d'une création (D3). **4 mutants, 4 attrapés** (sans la
règle des dates · registre jugé avant la nuit · échec pris pour une attente · API muette jugée quand même). Non-régression :
`test_seconde_preuve.js` et `test_garde_copropriete.js` verts ; `npm run build` vert.
⚠ **Trouvé par un mutant** : mon insertion avait **doublé 238 fins de ligne** (`

`) dans le worker — invisibles au
compte des CRLF, et Node les accepte. Corrigé (0), syntaxe vérifiée.

**Pour l'activer (gestes de Frédéric)** : pousser (le libellé de l'écran) · **redémarrer les 4 services, file vide**. ⚠ **Dès
l'activation**, la prochaine relecture de 24933 et de 61672 jugera les 3 transactions déjà au carnet : 1001339 et 1001361 →
leurs champs arrivés **sortent du carnet** ; **30712 → le 160 000 passe en « échec »** (le reste, arrivé, sort). Puis **essai réel** :
un compromis sur VA6482 et une offre sur le bac à sable 62774.

### R3 ACTIF — PREMIER PASSAGE RÉEL, 23/10 à 09:34 *(Frédéric : « c'est fait » : poussé `a91c6bf`, 4 services redémarrés à 09:32:33-34)*
Vérifié : `origin/main` = `a91c6bf` ; processus démarrés **après** le fichier (09:25:43) ; file vide. Relecture de 61672 déclenchée
en ouvrant la fiche V720061672 (lecture seule chez Hektor). **R3 a jugé 12 lignes, retiré 6 arrivées** :
- **1001361** (offre 33098, création du 13/10) : montant, date, n° de mandat, validité → **arrivée, retirées** ; prix public et
  rétractation → **sans_objet**. ✅
- **30712** (offre 33094, modification échouée du 13/10) : **montant 160 000 → « echec »** ✅ (Hektor : 16 000) ; n° de mandat et
  validité → arrivée, retirés ✅.
- ⚠ **DEUX ERREURS DE MA RÈGLE, trouvées par ce passage** : (a) la **date** de 33094 jugée « echec » — Hektor rend la date de la
  **dernière proposition** (30/09), alors que l'offre date du 06/10 ; (b) le prix public et la rétractation (champs qu'une offre
  n'a pas) marqués « echec » au lieu de « sans_objet ». **Corrigé** (offre : date de l'offre relue la nuit d'abord ;
  « sans_objet » avant « echec »), essai **23/23**, **4 mutants attrapés**, et **la version en service reproduit exactement les deux
  verdicts faux** (témoin inverse). **Non actif** tant que les services ne sont pas redémarrés.
- ⚠ Les 3 lignes de 30712 déjà marquées « echec » à tort (date, prix public, rétractation) **ne seront pas rejugées** (R3 ne revient
  pas sur un verdict tranché) : **les remettre à blanc** (écriture en production, accord de Frédéric) après le redémarrage.
- 1001339 (annonce 24933, plus parmi les biens actifs) : sera jugée à sa prochaine relecture.

### ✅ CORRECTIF R3 ACTIF ET VÉRIFIÉ — 23/10 à 09:40 *(Frédéric : « poussé, 4 services redémarrés ; remets à blanc les 3 lignes, j'autorise »)*
Vérifié : `origin/main` = `6731460` ; processus démarrés à 09:38:24-26, après le fichier (09:35:56).
- **Remise à blanc** des 3 lignes de 30712 jugées « echec » à tort (date, prix public, rétractation) : `etat`, `valeur_hektor_relue`,
  `constate_le` à vide, **valeurs saisies intactes**, et seulement si elles étaient encore à « echec » (3 lignes).
- La fiche ne relançait pas de relecture (la précédente datait de 09:34) → **un travail de relecture recopié de celui de 09:34**
  (`reason = verif_r3_23_10`, lecture seule chez Hektor), terminé à 09:40:49.
- **Le nouveau verdict** : **date → arrivée, retirée** (date de l'offre relue la nuit) · prix public et rétractation → **sans_objet** ·
  le montant 160 000 reste **« echec »** (non rejugé, comme voulu). Carnet de 30712 : 3 lignes, toutes tranchées.

### 33094 REMISE À 16 000 CHEZ NOUS — 23/10 à 09:4x *(Frédéric : « passe à 16 000 chez nous sans envoyer à Hektor, qui est déjà à 16 000 »)*
Le registre portait déjà 16 000 ; c'est la ligne de carnet `montant = 160 000` (« echec ») qui passait devant à l'écran. **Retirée**
après **sauvegarde datée** `app_affaire_champ_app_avant_33094_16000_20261023` (1 ligne, RLS activée). **Aucun travail créé, rien
envoyé à Hektor.** *(Le reste de son carnet — prix public, rétractation — est « sans_objet » ; il s'affiche encore à l'écran.)*
⚠ Frédéric : modifier une offre **acceptée** bloque chez Hektor et créerait une nouvelle offre — **« c'est un autre problème »**.

### ✅ ESSAI RÉEL DE R3 SUR UNE CRÉATION — compromis 50130, VA6482, 23/10 à 09:48 *(accord de Frédéric)*
- Bac à sable **62774 indisponible** (mandat clos lors de l'essai du 21/10, plus dans le parc vivant) → **l'offre n'est pas faite**.
- Compromis par l'écran : 135 000, acte 15/02/2027, rétractation 10, séquestre 6 000, acquéreur ESSAI 8A B2 (net et commission
  laissés « auto »). ⭐ **La preuve immédiate a marché du premier coup** (« créé et confirmé par les DEUX portes ») : **première
  vraie création depuis le correctif du tri** (`2704dee`). Numéro posé, registre mis à jour avec ce que Hektor a retenu.
- ⚠ **R3 au moment de la création : 0 ligne jugée** — le travail appelant était lui-même « running », et ma règle « travail en
  cours → on ne juge pas » le reconnaissait. **Le rattrapage, une minute plus tard, a tout jugé juste** : montant, date, date
  d'acte, séquestre, prix public, rétractation → **arrivée, retirés** · n° de mandat → **en_attente** (la nuit) · validité →
  **sans_objet**. **Corrigé** (`834da97` : le travail appelant ne se compte pas), essai **24/24**, la version en service reproduit
  le raté, 4 mutants attrapés. **Non actif** tant que les services ne sont pas redémarrés.
- **Supprimé ensuite par l'écran** : `delete_hektor_compromis` done, statut « Actif », registre et carnet **vides**, et Hektor ne
  le rend plus (`CompromisById 50130` → `trouve: false`).
- **Noté à l'écran, non traité** : la fiche VA6482 annonce « Mandat clos le 30/07/2026 — échéance initiale le 27/08/2027 » : elle
  mélange la **clôture de l'ancien mandat n° 1** avec l'échéance du mandat **en cours** n° 18787.

### ✅ CORRECTIF `834da97` ACTIF — 23/10 à 09:56 *(Frédéric : « poussé, 4 services redémarrés, file vide »)*
`origin/main` = `e93180b` ; processus démarrés à 09:56:33-35, **après** le fichier (09:51:11) ; la ligne du correctif est dans le
fichier en service ; file vide, 0 erreur sur 20 min. ⚠ **Non revu en réel** : il faudrait une nouvelle création (écriture chez
Hektor) — il se verra à la prochaine vraie création (« R3 : N ligne(s) jugée(s) » dès le travail de création).

### ✅ E ALLUMÉ, ET ESSAI RÉEL D'UNE OFFRE (création + modification d'un seul champ) — 23/10, 10:03-10:15 *(Frédéric : « allume E » ; bien choisi : VA6482)*
- **E allumé** à 10:03:17 (`affaire_modif_champs_touches = on`). Vérifié avant : la version EN LIGNE du front porte E1
  (`index-9tny6SWH.js` contient `champs_touches`) ; un onglet resté ouvert sur l'ancienne version n'envoie pas la liste → comportement
  d'avant, sans danger. *(L'onglet de Chrome était « caché » : captures et clics à l'écran figés ; essai mené par script.)*
- **Création** de l'offre **33109** (120 000, validité 10, ESSAI 8A B2) : prouvée par les deux portes, numéro posé, registre mis à jour
  par la **lecture par numéro** (montant 120 000, validité 10). ⭐ **R3 a jugé DÈS LA CRÉATION** (6 lignes, 3 arrivées retirées : montant,
  date, validité) — le correctif `834da97` est prouvé. Restaient : n° de mandat **en_attente**, prix public et rétractation **sans_objet**.
- **Modification d'un seul champ** (validité 10 → 12, « Modifier la transaction ») : ⭐ **E prouvé** — charge `champs_touches =
  ["validity_days"]`, **charge entière** envoyée (montant 120 000 compris), **une seule ligne au carnet** (`jours_validite = 12`). Hektor
  a relu **validité = 12**, ligne retirée, registre à 12.
- ⚠ **DÉFAUT TROUVÉ** : après la modification, l'**ancien** verdict (`marquerLeCarnetRestant`) a repassé sur les lignes de la
  **création** et remplacé « sans_objet » / « en_attente » par « **inconnu** ». **Corrigé** (il saute désormais les lignes
  `creation_app`, laissées à R3), essai **26/26**, la version en service reproduit le défaut, 4 mutants attrapés. **Non actif** sans
  redémarrage. Les 3 lignes de 1001377 resteront « inconnu » jusqu'à leur prochain rattrapage (≥ 6 h).
- **Nettoyage** : offre 33109 **refusée** chez Hektor (`change_hektor_offre_status` done ; registre « refused ») — une offre ne se supprime
  pas, la trace « offre refusée » reste. Bien remis à **« Actif »** (`change_hektor_annonce_status` done).
- ⚠⚠ **EFFET DE BORD — VA6482 EST PASSÉ « diffusable = 1 »** (il était à 0). Le geste « Actif » envoie **toujours** `diffusable = 1`
  (`HEKTOR_STATUS_CONFIG.active`, l. 12436). L'app n'a **aucun geste** pour retirer la seule diffusion. Le bien n'a **aucun portail
  actif** et sa validation est « à contrôler » ; **non vérifié** : s'il apparaît sur le site de l'agence. **À remettre à 0 par Frédéric**
  (fiche Hektor). Leçon : nettoyer un essai par le geste « Actif » n'est pas neutre.
- **Noté** : la fiche du bien (`app_dossier_current`) porte encore `compromis_id = 50129` (supprimé) et pas `offre_id = 33109` — ces
  pointeurs ne sont remplis que la nuit (déjà dit dans le code, 02/09) ; la modale s'en sort par son repli.

### ✅ VA6482 REMIS « NON DIFFUSABLE » — 23/10 à 10:2x *(Frédéric : « si on peut, dans pilotage, mettre diffusable sur non »)*
Fiche du bien → menu **« Pilotage »** de l'en-tête → **« Pilotage diffusion » : Désactiver** (`setDossierDiffusableOnHektor`, par le
backend Render, écrit chez Hektor puis met à jour notre fiche). ⚠ Avant rechargement, l'écran montrait déjà « Désactiver » choisi
(état périmé) — il a fallu recharger pour voir « Activer » et pouvoir cliquer. **Vérifié des deux côtés** : notre fiche `diffusable = 0`
et **Hektor `keyData.diffusable = 0`** (lecture `AnnonceById`).

## 14. AUDIT GLOBAL DU CARNET — avant d'activer `fd8e3c8` — 23/10 *(Frédéric : « tu as mal audité mon architecture globale, fais-le maintenant : ton correctif ne doit pas générer de bug en cascade »)* — lecture seule

> **Périmètre** : objet **transaction** (offre, compromis, vente), et tout ce qui écrit ou lit le carnet `app_affaire_champ_app`,
> son `etat`, et les colonnes du registre que R3 écrit. **Les autres objets ne sont pas mesurés ici.**

### Qui ÉCRIT le carnet — tous trouvés
| écrivain | quand | ce qu'il fait |
|---|---|---|
| RPC `app_change_annonce_status_optimistic` | clic « créer » | lignes `creation_app`, sans photo |
| RPC `app_modifier_affaire_optimistic` | clic « modifier » | upsert `modification_app`, **la 1re photo gagne** ; ⚠ **ne remet PAS `etat` à blanc** |
| RPC `app_edit_affaire_optimistic` | **dormante** (appel retiré de l'écran le 15/09) | `saisie_app`, jamais envoyée à Hektor |
| worker `retirerDuCarnetCeQuiEstArrive` | modification prouvée | **efface par champ**, quelle que soit l'origine (une ligne de création comprise) |
| worker `marquerLeCarnetRestant` (ancien verdict) | modification prouvée, seulement sur le chemin du succès | juge **toutes** les lignes sauf `creation_app` (`fd8e3c8`) ; efface les « arrivée » qui ont une colonne |
| worker `controlerLeCarnet` (R3) | création + chaque relecture (1 fois / 6 h / ligne) | juge les lignes à `etat` vide / en_attente / inconnu ; efface les « arrivée » |
| worker, suppression d'une transaction | geste « supprimer » | purge le carnet (borné à `requested_at`) |
| `nettoyer_carnet_affaire.py` | **à la main seulement — PAS dans le run** (vérifié) | — |
| `magasin_affaire_app.py` / `appliquer_contrat_affaire.py` | nuit | copie locale / **ne fait rien** (contrat vide, « le gel ») — ne lisent pas `etat` |

### Qui LIT le carnet
- **La modale « Modifier »** (App.tsx ~16933-17060) : le carnet **d'abord**, puis le registre — **sauf** pour 4 champs qui ne lisent
  **QUE le carnet** : **validité**, **rétractation**, taux d'honoraires, prix public.
- **La grille de détail** (App.tsx ~21142) : prix public, prix net vendeur, honoraires, taux — **carnet seul**, aucun repli sur le
  registre (qui porte pourtant `prix_net_vendeur` et `honoraires_sortie`).
- **Les étiquettes d'état** (`loadAffaireCarnetEtats`).
- **La nuit** (`affaire_ledger.py`) : une ligne au carnet **protège** l'affaire du marquage « absente ». Les affaires nées dans l'app
  (≥ 1 M) sont protégées de toute façon par leur plage.

### La mesure (23/10)
Le carnet entier compte **18 lignes**. Les 3 « inconnu » de 1001377 sont celles que `fd8e3c8` empêchera à l'avenir.
Le registre : **47 compromis actifs sur 323** dont la rétractation est connue ont une rétractation **≠ 10 jours** ; **8 offres**
ont une validité **≠ 10**.

### ⛔ LE RISQUE EN CASCADE TROUVÉ — R-A (réel)
Quand une ligne « arrivée » sort du carnet, la modale **ne relit pas le registre** pour la validité ni la rétractation : elle remet
**« 10 » par défaut** (App.tsx:16603-16604). Comme la charge part **entière** (E ne filtre que le carnet), la **modification
suivante, même d'un autre champ, envoie 10 à Hektor** — en silence (la rétractation n'est pas un champ prouvé).
- **Exemple vivant** : l'offre 33109 porte **12** au registre et chez Hektor ; sa ligne est sortie à 10:15 ; la modale montrerait
  **10**.
- ⚠ **Ce n'était pas créé par R3**, ça existait : la modification efface déjà la validité arrivée (11/09 / 18/09), et **tout compromis
  né chez Hektor** n'a aucune ligne (les 47). **Mais R3 l'étend à toutes les créations de l'app**, dès le retour de Hektor.
- **Parade A1 (écran, la vraie cause)** : la validité se replie sur `jours_validite` du registre ; la rétractation sur
  `date_fin_retractation − date` ; la grille se replie sur `prix_net_vendeur` et `honoraires_sortie`. Ça couvre aussi l'existant.
  ⚠ Pour un compromis sans `date_fin_retractation` (la plupart des anciens), on ne sait pas : « 10 » reste — comme avant.

### Les risques plus petits
- **R-B, étiquette périmée** : la RPC de modification ne remet pas `etat` à blanc, et R3 saute une ligne « déjà tranchée ». Une ligne
  « conflit » ou « échec » réécrite garde son ancienne étiquette si le nouvel envoi échoue. **Parade B (worker, 1 ligne)** : R3 rejuge
  une ligne écrite APRÈS son dernier verdict (`ecrit_le > constate_le`).
- **R-C, va-et-vient** : l'ancien verdict réécrit en « inconnu » les verdicts de R3 sur les lignes de modification qu'il ne sait pas
  juger (notaire, taux, rétractation), et repousse R3 de 6 h. Seulement visuel. **Parade C (worker)** : quand R3 est allumé, l'ancien
  verdict laisse ces lignes-là à R3.
- **R-D, lectures sans fin** : une ligne qui ne peut jamais conclure (taux recalculé faux, offre sans mandat, notaire jamais posé)
  relit Hektor toutes les 6 h à chaque relecture, **pour toujours**. Aujourd'hui négligeable (18 lignes). **Parade D** : arrêter après
  N jours. **La durée est à Frédéric.**
- **R-E, dormant** : R3 jugerait aussi une ligne `saisie_app` ou `classeur` (jamais envoyée par construction) → faux « conflit ».
  0 ligne aujourd'hui. **Parade E (worker, 1 ligne)** : R3 ne juge que `creation_app` et `modification_app`.

### Vérifié, sans risque
- `fd8e3c8` lui-même : **aucun risque nouveau trouvé**. Une ligne de création réécrite par une modification devient
  `modification_app`, donc l'ancien verdict la juge. R3 éteint → retour exact au comportement d'avant.
- Un travail **en cours** sur la même affaire : R3 ne juge pas ses lignes (garde par `ecrit_le = created_at`).
- Le **filet de rejeu** : R3 est idempotent (une ligne effacée ne revient pas, une ligne tranchée n'est pas rejugée).
- La **suppression** d'une transaction purge le carnet ; R3 ne ressuscite rien.
- La **protection de nuit** : identique à avant R3 (l'ancien verdict effaçait déjà les « arrivée »).
- `reporterAuRegistre` à la création : n'écrit que ce que Hektor a relu (« vide ne gagne pas ») ; ne touche pas `hektor_acquereur_id`
  (la clé du chaînage).
- ⚠ **Hors R3, déjà connu = R2** : le `--push` de nuit fait `SELECT *` + upsert et remplace la ligne du registre entière.

## 15. L'AUDIT CHAMP PAR CHAMP — 23/10 *(Frédéric : « certains champs ne sont pas tous retournés par Hektor, acceptés, ou envoyés à la création mais pas à la modification — as-tu vraiment audité ? »)* — lecture seule

⛔ **Non : le §14 traitait les champs en bloc, et sa parade A1 était FAUSSE pour deux champs.** Chaque champ a son propre
circuit. Mesuré dans le code (RPC en base, worker, `affaire_ledger.py`, `registre_depuis_console.py`, écran) :

| champ | au clic, création (R1) | au clic, modification | Hektor le rend ? | le retour l'écrit au registre ? | la nuit | la modale se replie sur le registre ? | si R3 retire la ligne |
|---|---|---|---|---|---|---|---|
| montant, date | ✅ | ✅ | ✅ | ✅ | réécrit | ✅ | sans risque |
| date d'acte, séquestre | ✅ | ❌ | ✅ | ✅ | réécrit | ✅ | sans risque |
| net vendeur, honoraires vendeur | ✅ | ❌ | ✅ | ✅ | réécrit | ✅ | la grille ne l'affiche plus |
| honoraires acquéreur | ✅ | ❌ | compromis/vente ✅ · offre : liste seulement | compromis/vente ✅ | réécrit | ✅ (si > 0) | la grille ne l'affiche plus |
| **validité** (offre) | ✅ | ❌ | ✅ par numéro | ✅ | réécrit | ❌ → **10** | ⛔ **10 renvoyé** — A1 corrige, **juste** |
| **rétractation** (compromis) | ✅ (fin = date + jours) | ❌ | ✅ (`dateEnd`) | ⛔ **NON** (`dateEnd` absent de `REGISTRE_PAR_HEKTOR`) | réécrit | ❌ → **10** | ⛔ **A1 seul serait FAUX** : jusqu'à la nuit le registre porte l'ANCIENNE fin |
| rétractation (offre) | carnet seulement : **le 10 prérempli** | — (E l'écarte) | n'existe pas | — | — | — | jamais retirée (« sans objet ») ; s'affiche « 10 jours » sur une offre — **déjà avant R3** |
| **taux d'honoraires** | ✅ (colonne classe A) | ⛔ **NON** | ⛔ **NON** (R3 le recalcule) | — | **jamais** (classe A) | ❌ | ⛔ **A1 serait FAUX** : après une modification, le registre garde le taux de la CRÉATION, pour toujours |
| notaire acquéreur | ✅ (`notaires_origine = 'saisie'`) | ❌ | ❌ (la nuit, console) | — | ⚠ **jamais**, une saisie est protégée | ✅ | après une modification : **faux « conflit » à vie** (le registre garde le notaire de la création) |
| n° de mandat | ✅ | ❌ | la nuit | — | réécrit | ❌ (vide = Hektor garde le sien) | sans risque pour Hektor |
| prix public | pas de colonne | — | compromis ✅ | — | — | ❌ | la grille ne l'affiche plus |
| commission `_app`, charge, **répartition** | hors carnet (`ecrireAffaireCommission`, `saveRepartition`, après le geste, création ET modification) | | rien ne part chez Hektor | | jamais | | **non touchées par R3 ni par `fd8e3c8`** |

### Ce que ça change aux parades
- **Validité** : A1 (repli sur `jours_validite`) est juste — le retour l'écrit au registre.
- **Rétractation** : il faut **d'abord** que le retour écrive `date_fin_retractation` depuis `dateEnd` (une ligne dans
  `REGISTRE_PAR_HEKTOR`), **puis** A1. Sinon la modale montrerait l'ancienne valeur et la renverrait.
- **Taux** : Hektor ne le rend pas et rien ne met sa colonne à jour après une modification → **R3 ne doit JAMAIS retirer
  une ligne de taux** : c'est la seule copie à jour. (Ou la modification doit écrire la colonne : patch de RPC.)
- **Notaire** : la RPC de modification n'écrit pas le registre, et la nuit protège la saisie de la création → R3 dira « conflit »
  à tort après un changement de notaire. **Rien ne part chez Hektor de travers** (le carnet prime) — c'est une fausse alarme.
- **Rétractation et prix public d'une OFFRE** : du prérempli rangé au carnet à la création (E ne corrige que la modification).
  Inoffensif pour Hektor, trompeur à l'écran. Déjà là avant R3.
- **Répartition et commission** : hors du carnet, R3 n'y touche pas.
- ⛔ **Constat de fond** : R1 avait promis d'écrire au registre « au clic, création **+ modification** ». La modification n'écrit
  que `montant` et `date`. C'est ce trou qui rend le carnet indispensable pour 5 champs — et dangereux à vider.

## 16. LA LOGIQUE D'AVANT ⑧, ET L'ERREUR DE R3 — 23/10 *(Frédéric : « fais une analyse de mon projet AVANT ce chantier, explique la situation et comment tout corriger »)* — lecture seule

### La logique du carnet, telle qu'elle a été construite (commits et décisions)
| date | décision | source |
|---|---|---|
| 01/09 | la saisie se range au carnet, **que la nuit ne touche jamais** ; l'écran le lit **d'abord** ; 4 champs y entrent **parce qu'ils n'ont aucune colonne de la bonne nature** (validité, rétractation, notaire, taux) : *« ils se conservent dans le carnet, qui est fait pour ça : il attend sa colonne »* | `6e49230` |
| 12/09 | **une saisie disparaît une fois arrivée** — mais seulement après une **preuve sans écart**, sur les champs **prouvables** | `8466ec3` |
| 16/09 | le contrat d'autorité est **vidé** (« le gel ») ; le verdict retire une ligne **quand le REGISTRE porte exactement la saisie** — l'écran, qui se replie sur le registre, ne perd donc rien. Un champ **sans colonne** n'a pas de photo → « inconnu » → **il reste** | `3562bce`, `e079218` |
| 18/09 | la validité devient prouvable (relue par numéro) ; la grille se replie sur le registre pour la validité (D4) — **pas la modale** | worker l. 15037, App.tsx |

⭐ **LA RÈGLE, en une phrase : une ligne ne quitte le carnet que si LE REGISTRE porte désormais la même valeur.**
Les 5 champs qui n'ont pas de place sûre au registre — **prix public, honoraires (nom du carnet), rétractation, notaire,
taux** — **restaient exprès** : le carnet est leur seule mémoire.

### Ce que R1 (22/10) a changé
Au clic de **création**, R1 écrit aussi au registre la fin de rétractation, le taux, les honoraires, les notaires. **Mais pas
à la modification** (seuls montant et date), la nuit réécrit les colonnes partagées depuis Hektor, et le taux (classe A) n'est
jamais réécrit. ➡ **Ces champs n'ont toujours pas de place sûre au registre : la règle du 16/09 reste vraie.**

### ⛔ L'erreur de R3 (23/10, la mienne)
R3 compare la saisie à **Hektor en direct** (`R3_SOURCES`), pas **au registre**, et retire la ligne dès que Hektor porte la
même valeur — **même pour les 5 champs sans place au registre**. Il casse donc la règle du 16/09.
⚠ Le §13 point 4 l'avait écrit **« À trancher »** (« ce qui ne se juge pas reste "inconnu", ou sort à la confirmation ? ») —
**je l'ai tranché seul en codant**, et le §13 affirmait à tort « une ligne retirée montre la valeur du registre, qui EST la même ».

### Ce qui est abîmé aujourd'hui en production — mesuré
- **Aucun des 5 champs n'a été retiré sur une transaction vivante** : les seules lignes « prix public » et « rétractation »
  retirées étaient celles du compromis d'essai 50130 (1001376), supprimé depuis.
- Les **validités** retirées (1001361, 30712, 1001377) : le registre porte 10, 10 et 12 ; seule 33109 (12, **refusée**) ferait
  afficher 10 dans la modale.

### La correction, qui RÉTABLIT la règle au lieu d'en inventer une
1. **R3 (worker)** : il continue de **juger et d'étiqueter** tout, mais il ne retire une ligne que selon la règle du 16/09 —
   champ ayant une colonne (`CARNET_VERS_REGISTRE`) **et** registre égal à la saisie après le report. Les 5 autres restent,
   avec leur étiquette « arrivée ». ➡ Même règle dans les deux verdicts (« deux copies d'une règle divergent »).
2. **Modale (écran)** : la validité se replie sur le registre, comme la grille le fait depuis le 18/09. Le registre la porte
   (le retour l'écrit, la nuit la relit). Ça corrige aussi le défaut d'avant (validité retirée après une modification).
3. **B, C, E** (§14) : inchangés.
4. **D** (durée avant d'arrêter de relire) : **à Frédéric**.
5. **Noté, non traité** : R1 incomplet à la modification ; rétractation et prix public préremplis rangés sur une OFFRE à la
   création ; le « 10 » par défaut sur les 47 compromis nés chez Hektor ; faux « conflit » de notaire après modification.

### Le jugement, champ par champ — comment faisait l'ancien, et ce que fait R3 *(Frédéric : « c'est champ par champ, certains ne sont pas envoyés ou pas retournés — tu as vu comment on faisait ? »)*
**L'ancien (modification, depuis le 12/09)** juge avec trois filtres : ① seulement ce qui a **vraiment été envoyé** (`aVerifier` :
clé de la charge non vide) ; ② moins ce qui a été **laissé à Hektor** (`champs_non_verifiables`, ex. le net vendeur quand les
honoraires sont illisibles), plus ce qui a été **calculé** (`champs_calcules`, le net déduit) ; ③ le verdict compare **au registre**,
avec la **photo** — pas de photo ou pas de colonne → **« inconnu », on ne devine pas**.

**R3 (création)** juge par la table `R3_SOURCES`, **par champ ET par genre**, mesurée le 23/10. Il ne lit pas la liste « envoyé » :
à la création c'est sans conséquence, **chaque ligne du carnet part chez Hektor** (vérifié : compromis l. 13586-13616, offre
l. 14090-14120), sauf le prix public et la rétractation d'une **offre** (préremplis, pas des champs de l'offre → « sans objet »).

| champ | envoyé à la création | Hektor le rend | R3 juge | retiré après correction |
|---|---|---|---|---|
| montant, date | ✅ | ✅ (date d'offre : la nuit) | arrivée / conflit | ✅ le registre l'a |
| date d'acte, séquestre (compromis) | ✅ | ✅ | arrivée / conflit | ✅ |
| net vendeur, honoraires vendeur (si saisis) | ✅ | ✅ | arrivée / conflit | ✅ |
| validité (offre) | ✅ | ✅ par numéro | arrivée / conflit | ✅ + repli de la modale |
| n° de mandat | ✅ | la nuit seulement | en attente → arrivée | ✅ |
| honoraires acquéreur | ✅ | compromis/vente ✅ · offre : `honoraire_acquereur` ⚠ **jamais éprouvé** | arrivée / conflit | ❌ **gardé** |
| prix public | compromis ✅ · offre : prérempli | compromis ✅ | arrivée · offre : sans objet | ❌ **gardé** |
| rétractation | compromis ✅ (10 si non touché) · offre : prérempli | en date de fin → calculée | arrivée · offre : sans objet | ❌ **gardé** |
| taux | ✅ | ⛔ jamais | recalculé, **jamais** « conflit » | ❌ **gardé** |
| notaire acquéreur | ✅ | pas à la relecture → le lendemain | en attente → arrivée (par la personne) | ❌ **gardé** |

## 17. LE PLAN DE CORRECTION, ET LES CONTACTS / ANNONCES VÉRIFIÉS — 23/10 *(Frédéric : « redonne-moi les étapes, et vérifie si tes améliorations du registre des contacts n'ont pas fait la même chose »)*

### Les contacts et les annonces (8a, 22/10) n'ont PAS fait la même erreur — vérifié dans les patchs et en base
| pièce | où vit la saisie | efface-t-elle ? | ce que voit l'écran |
|---|---|---|---|
| 8a-B / B2 contact, modification et création (`8a5`, `8a6`) | table à part `app_contact_saisie_modif` | **non** (4 lignes, toutes gardées, « jugé ») | la valeur de Hektor + l'écart signalé (règle 2, voulu) ; naissance / lieu / situation **réinjectés**, prouvé en réel (20000006, 605925) |
| 8a-A commentaire au clic (`8a4`) | la colonne, au clic | non | Hektor rend le commentaire ; il est jugé par 8a-B |
| pièce 3 annonce née dans l'app (`8a3`) | table à part `app_annonce_saisie_naissance` | **non** | les champs « console seule » **reposés** sur la fiche (notre valeur si Hektor ne la rend pas) |
| 8a-C annonce, modification (`8a7`) | table à part `app_annonce_saisie_modif` | **non** | la valeur de Hektor + l'écart signalé |
⭐ **Leur dessin est le bon** : la saisie vit dans une table que **rien n'efface**, le contrôle **constate**, l'écran ne perd rien
de ce que Hektor ne rend pas. **R3 est le seul à avoir retiré des lignes** — parce que le carnet des transactions, lui, est À
LA FOIS la liste d'attente et la seule mémoire de 5 champs (règle du 16/09).

### Les étapes de la correction
1. **R3 — la règle de retrait** (`controlerLeCarnet`) : retirer une ligne **seulement si** verdict « arrivée » **ET** champ ayant
   une colonne (`CARNET_VERS_REGISTRE` : montant, date, date d'acte, séquestre, net vendeur, honoraires vendeur, n° de mandat,
   validité) **ET** registre égal à la saisie après le report. Sinon la ligne **reste**, étiquetée « arrivée ».
2. **B** : R3 rejuge une ligne réécrite après son verdict (`ecrit_le > constate_le`) — devenu **indispensable** : une ligne de taux
   gardée « arrivée » puis modifiée garderait sinon l'étiquette « arrivée » sur la nouvelle valeur.
3. **C** : quand R3 est allumé, l'ancien verdict laisse à R3 les champs qu'il ne sait pas juger (sans colonne).
4. **E** : R3 ne juge que `creation_app` et `modification_app`.
5. **Écran** : la modale relit `jours_validite` au registre quand le carnet n'a plus la ligne (comme la grille depuis le 18/09).
6. **Essais hors ligne** : les 5 champs « arrivée » restent · montant « arrivée » + registre égal → retiré · « arrivée » mais registre
   différent → reste · ligne réécrite → rejugée · `saisie_app` ignorée · **témoin inverse** contre la version en service ·
   mutants · `npm run build` · fins de ligne (`\r\r\n` = 0).
7. **Commit local**, fichier par fichier.
8. **Frédéric** : pousser (worker + écran), redémarrer les 4 services **file vide**.
9. **Essai réel** (accord de Frédéric, sur VA6482) : un compromis avec taux et rétractation ≠ 10 → le carnet **garde** taux,
   rétractation, prix public ; montant / date / date d'acte / séquestre **retirés** ; la modale montre les bonnes valeurs.
   Puis nettoyage (⚠ la diffusion : vérifier `diffusable` avant / après).
10. **La note et le plan** à jour.
- **D** : sans limite pour l'instant (décision à Frédéric).
- **Hors de cette correction, notés** : la modification n'écrit pas au registre (R1 incomplet) ; rétractation / prix public
  préremplis rangés sur une offre ; le « 10 » des 47 compromis nés chez Hektor ; le faux « conflit » de notaire.

### ✅ ÉTAPES 1 À 7 CODÉES ET ÉPROUVÉES HORS LIGNE — 23/10 *(Frédéric : « vas-y »)* — commit `941cb70`, **non actif**
- **Worker** (`controlerLeCarnet`, `marquerLeCarnetRestant`) : la règle de sortie (registre égal, table `CARNET_VERS_REGISTRE`,
  la même que l'ancien verdict) ; **B** (ligne réécrite après son verdict → rejugée, même « arrivée ») ; **C** (l'ancien verdict
  laisse à R3 les champs sans colonne) ; **E** (`R3_ORIGINES_JUGEES` : création et modification seulement). Le journal dit
  « N retirées, M gardées ».
- **Écran** (App.tsx ~16998) : la validité se replie sur `jours_validite` du registre.
- **Essais** : `Console/test_controle_carnet_r3.js` **36/36** (dont 11 neufs : les 5 champs gardés, registre différent → gardée,
  B, E, C avec son témoin éteint). **Témoins inverses** : la version en service (`origin/main`) échoue **12** contrôles, celle
  d'avant ce commit **11**. **Mutants** : retrait sans regarder le registre, sans colonne → on se fie à Hektor, B absent, E absent,
  C absent → **5 attrapés** (un 6ᵉ était équivalent : écarté). `npm run build` vert. Fins de ligne : `\r\r\n` = 0 partout.
- ⚠ **Non éprouvé** : le chemin réel (un compromis créé par l'écran) — c'est l'étape 9. ⚠ Remarqué en codant, **noté** : le
  notaire saisi à la création garde `notaires_origine = 'saisie'`, que la nuit ne réécrit pas ; R3 risque donc de comparer le
  notaire **à lui-même** (« arrivée » sans preuve). Sans conséquence sur le carnet désormais (le notaire reste), à mesurer
  demain matin avec la preuve de nuit.
- ➡ **Pour l'activer** : pousser, puis redémarrer les 4 services, file vide (Frédéric). L'écran part avec le push (Vercel).

## 18. L'ESSAI COMPLET — contact → offre → acceptée → compromis → vente, sur VA6482 *(Frédéric, 23/10 : « prouver tout le registre et aussi le chaînage »)* — PROTOCOLE, rien n'est lancé

⚠ **Il se joue APRÈS le push et le redémarrage** : avant, c'est l'ancien R3 qui tournerait (il retire les 5 champs), et l'essai ne
prouverait pas la correction `941cb70`.

**État de départ, mesuré le 23/10** : VA6482 (annonce 24113, dossier 1068399) **Actif**, `diffusable 0`, mandat **18787 ouvert**
(échéance 27/08/2027, aucune clôture chez nous) ; offres 33109 et 32849 **refusées** ; carnet : les 3 lignes de 1001377 seulement.

**Ce que le code dit de chaque geste (lu le 23/10)**
- **Contact sans recherche** : l'OFFRE n'a pas ce filtre (`qualifierAcquereursAvantTransaction` : « l'offre n'a pas ce filtre ») ;
  au **compromis et à la vente**, le worker crée une recherche, attache la transaction, puis **archive** la recherche — dans le même
  travail (décision du 18/09). Journal : `hektor_qualification_acquereur`.
- **Vente** : statut **Vendu** chez Hektor ; le mandat **18787 est clos CHEZ NOUS** (`cloturerMandatLocalement`) ; **pas chez
  Hektor** (`CONSOLE_HEKTOR_CLOTURE_MANDAT` absent = faux) ; « après la vente » = **actif** (constante de l'écran) → pas d'archivage.

| étape | geste (par l'écran) | valeurs d'essai | ce qu'on vérifie |
|---|---|---|---|
| 1 | créer le contact « ESSAI 8 R3 » | sans recherche | numéro ≥ 20 M, paire Hektor apprise, 0 doublon |
| 2 | offre à son nom | 120 000 · validité **15** · honoraires acquéreur + taux | carnet : montant, date, validité **retirés** (registre égal) ; honoraires, taux **gardés** ; prix public, rétractation **sans objet** ; registre validité 15 ; la modale « Modifier » montre **15** (sans envoyer). ⭐ 1ʳᵉ preuve des honoraires d'une offre |
| 3 | accepter l'offre | — | registre `accepted` |
| 4 | compromis depuis l'offre | rétractation **14** · acte · séquestre · notaire · taux | recherche **créée puis archivée** ; **même chaîne** que l'offre ; carnet : 6 retirés, rétractation / prix public / taux / honoraires / notaire **gardés** ; la modale montre **14** |
| 5 | vente depuis le compromis | prix · date | **même chaîne** ; Vendu chez Hektor ; mandat clos chez nous seulement ; non archivé ; `diffusable` inchangé |
| 6 | **le lendemain** | — | la nuit adopte sans doubler, **recalcule les chaînes et garde la même** (D8 : la nuit gagne), notaire et mandat jugés |

**Le nettoyage — chaque geste avec l'accord de Frédéric** : supprimer la vente puis le compromis (gestes de l'app) ; l'offre acceptée
**reste** (Hektor la fige) ; retirer la clôture locale du mandat 18787 (écriture en base, sauvegarde datée) ; le contact d'essai
(archiver ou garder) ; vérifier `diffusable = 0` à la fin. ⚠ Nettoyer **avant** la nuit empêche l'étape 6.

### ✅ L'ESSAI COMPLET JOUÉ EN RÉEL — 23/10, 09:32-09:46, après le push et le redémarrage (processus nés à 11:26, front `index-BvDwv-Gq.js`)
| étape | résultat |
|---|---|
| 1 contact | **20000011 ↔ 605963**, tous les champs saisis (2 téléphones, adresse, naissance, lieu, situation, source, note), **0 recherche**, e-mail RGPD coupé ; contrôle au retour **10/10 identiques** ; 1 seule fiche. ⚠ « doublon possible » : j'avais repris le téléphone du contact d'essai 20000010 — la garde a joué, aucune fusion |
| 2 offre **33110** (1001378) | au clic le registre porte tout ; R3 : montant, date, validité **retirés** (registre égal) ; **honoraires 5 000 et taux 4,17 gardés « arrivée »** (⭐ 1ʳᵉ preuve des honoraires d'une offre) ; la modale « Modifier » montre **validité 15** |
| 3 acceptée | `change_hektor_offre_status` done, registre `accepted` |
| 4 compromis **50131** (1001379) | **même chaîne 1001378 dès le clic** ; fin de rétractation 06/11 (date + 14) au clic ; R3 : 6 retirés, **rétractation 14, honoraires, taux gardés** ; la modale montre **14** ; Hektor : « toutes les personnes envoyées gardées » |
| 5 vente **23354** (1001380) | **même chaîne 1001378** ; Vendu chez Hektor ; mandat 18787 **clos chez nous** (`mandat_date_cloture_app = 2026-10-23`), pas chez Hektor ; `diffusable 0` ; R3 : 3 retirés, 3 gardés |
| 6 nuit | ⏰ demain matin : adoption sans doublon, **chaîne gardée par le recalcul de nuit**, notaire et mandat jugés |

### ⚠ Ce que l'essai a trouvé
- **F1 — un défaut de R3, le mien** : le carnet range le **prix de vente** sous le nom `prix_publique` ; R3 le compare au **prix public** de Hektor
  → faux « conflit » sur 50131 (115 000 contre 120 000), dès que des honoraires acquéreur séparent les deux prix. ⛔ **L'ancien worker
  l'avait déjà réglé** : la preuve de modification ne juge qu'UNE fois `amount`/`sale_price` (même champ Hektor) et le « jumeau » ne
  retire `prix_publique` que s'il vaut le montant. R3 a récrit sa propre table (`R3_SOURCES`) au lieu de reprendre `CHAMPS_PROUVABLES`
  et la règle du jumeau — « deux copies d'une règle divergent ». Correction proposée : reprendre la règle existante.
- **F2** — à la vente, l'acquéreur part sous le numéro de **Hektor** (605963, écrit au registre par le report) et la qualification
  ne cherche que **notre** numéro → « contact inconnu de notre base » (sans effet ici : il était déjà acquéreur). La recherche par
  `hektor_target_id` manque (préexistant, 18/09) ; le report à la création le rend immédiat.
- **F3** — le mécanisme « contact sans recherche » **n'a pas été exercé** : créé « Acquéreur », le contact l'est déjà chez Hektor.
  Pour l'éprouver : un contact créé « Propriétaire ».
- **F4** — du compromis à partir de l'offre, le **mandant** et le **notaire du vendeur** ne sont pas repris (R1 n'écrit pas les
  notaires d'une offre) ; le **prix de vente** est prérempli avec le prix du mandat.
- **F5** — en modification d'offre, la modale ne montre pas la commission `_app` (8 000) ni la charge (« acquéreur ») ; rien n'est perdu.
- **F6** — R1 laisse `notaires_origine` vide sur le compromis et la vente ; à mesurer cette nuit (`registre_depuis_console`).
- **F7** — sur une offre, le notaire est envoyé mais R3 le dit « sans objet ».
- ⏰ **Le nettoyage attend la preuve de nuit** (étape 6) : vente, compromis, clôture locale du mandat 18787, contacts 20000007/8/9/10/11.

### ⛔ CORRECTION — F6 était FAUX, et la remarque du §17 sur le notaire aussi *(vérifié dans la RPC, 23/10)*
R1 laisse `notaires_origine` vide **exprès** (RPC de création, l. 233) : *« SANS notaires_origine = 'saisie', qui figerait la ligne
pour toujours : la console doit pouvoir la confirmer ou la corriger. »* Ce n'est donc pas un défaut. Et R3 ne compare **pas** le
notaire à lui-même : la nuit, `registre_depuis_console.py` réécrit le notaire depuis la console de Hektor, et R3 juge ensuite cette
valeur-là. J'avais supposé l'inverse sans lire la RPC.

### Les constats, ancien ou nouveau *(question de Frédéric)*
| | constat | depuis quand |
|---|---|---|
| F1 | faux « conflit » prix public / prix de vente | **NOUVEAU, R3 (23/10, moi)** — l'ancien worker l'avait réglé (12/09) |
| F2 | qualification à la vente : numéro Hektor non reconnu | **ANCIEN** (recherche par notre numéro seulement, 18/09 ; tous les contacts sont sur nos numéros depuis fin septembre) ; R3 le rend immédiat (le registre passe aux numéros Hektor dès le retour, au lieu de la nuit) |
| F3 | mécanisme « sans recherche » non exercé | **ni l'un ni l'autre** : mon choix de type « Acquéreur » pour l'essai |
| F4 | offre → compromis : mandant et notaire du vendeur non repris ; prix de vente = prix du mandat | **ANCIEN** — l'offre n'a jamais gardé ses notaires au registre (D4, 22/10) ; écran non touché |
| F5 | modale de modification sans la commission `_app` ni la charge | **ANCIEN** (lot 1c, 16/10) ; écran non touché |
| F6 | `notaires_origine` vide | **PAS UN DÉFAUT** — voulu par R1 (voir ci-dessus) |
| F7 | notaire d'une offre « sans objet » | **NOUVEAU, R3 (23/10, moi)** — la table de R3 ne donne pas de source au notaire d'une offre ; la ligne reste au carnet, l'étiquette est fausse |

## 19. LES CHAMPS DE L'OFFRE QUI RESTENT CHEZ NOUS — audit du 23/10 *(Frédéric : « on a ajouté des champs à la modale de l'offre qui ne doivent pas être envoyés à Hektor, seulement conservés : donc pas contrôlés en relecture »)* — lecture seule

| champ de la modale d'offre | ajouté le | décision | envoyé chez Hektor | au carnet | R3 le contrôle |
|---|---|---|---|---|---|
| charge de la commission | 16/10 (lot 1c) | « reste à nous PARTOUT » (14/10) | non | non (`charge_commission_app`) | **non** ✅ |
| honoraires vendeur | 16/10 (lot 1c) | à l'offre « Hektor n'a aucune destination » → chez nous | non (« jamais l'offre ») | non (`honoraires_entree_app`) | **non** ✅ |
| répartition | 14/09 | « UNIQUEMENT les répartitions ne sont pas envoyées » (Frédéric, 16/10) | non | non (`app_affaire_repartition`) | **non** ✅ |
| note libre | 17/09 | « elle reste chez nous » | non | non | **non** ✅ |
| **honoraires acquéreur** | modale d'origine ; chez nous à l'offre le 16/10 (`honoraires_sortie_app`) | à l'offre → **chez nous** (16/10) | ⚠ **oui** : le corps de l'offre pose encore `montantHonoraireSortie` (code d'avant le 16/10) | ⚠ oui (`honoraires`) | ⚠ **OUI — à tort** |
| **taux d'honoraires** | 01/09 (B2) | **classe A** : « Hektor n'a aucune destination » (03/09) | ⚠ oui (`tauxHonoraireSortie`) | ⚠ oui | ⚠ **OUI — à tort** (recalculé) |
| notaires (2) | 15/09 | **envoyés** exprès (« les deux notaires se désignent ») | oui | oui (`notaire_id`) | non (« sans objet ») — conservé par hasard |

➡ **Frédéric a raison pour 2 champs** : à l'offre, les honoraires acquéreur et le taux sont des valeurs **gardées chez nous** ; R3 ne
doit pas les contrôler. Les 4 champs ajoutés le 16/10 (charge, honoraires vendeur) et avant (répartition, note) ne sont déjà **ni
envoyés ni contrôlés**.
⚠ **Une contradiction à trancher, pas à supposer** : le 16/10 disait « Hektor ne garde RIEN à l'offre » (0 % sur 11 187 — mesure faite
sur **notre registre**) ; aujourd'hui la **liste de Hektor** a rendu `honoraire_acquereur = 5 000` pour l'offre 33110. Hektor garde donc
peut-être quelque chose, que notre nuit ne lit pas. Et le worker **envoie toujours** honoraires et taux à l'offre : arrêter de les envoyer
est une **décision de Frédéric**, pas une correction.

### F2 expliqué — l'acquéreur « inconnu » à la vente
Le contact a deux numéros : **20000011** (le nôtre) et **605963** (celui de Hektor). La qualification (18/09) cherche l'acquéreur dans
`app_contact_current` **par notre numéro seulement** (`hektor_contact_id=in.(…)`). Au compromis, la charge portait **20000011** (le
registre de l'offre) → trouvé. Le retour du compromis a ensuite écrit au registre l'acquéreur **sous le numéro de Hektor** (605963, la
norme). La vente, qui hérite du registre du compromis, est partie avec **605963** → pas trouvé → « inconnu de notre base », **pas de
qualification**. L'ENVOI, lui, a marché (la porte `ciblesHektorContacts` reconnaît les deux numéros) et Hektor a gardé l'acquéreur.
**Le risque** : un acquéreur qui n'est pas encore « acquéreur » chez Hektor serait **écarté en silence** de la vente (le défaut 1.4).
**Ancien** : toute vente ou compromis créé APRÈS une nuit hérite de numéros Hektor. **Parade** : chercher aussi par `hektor_target_id`
(le patron de 8a-B2).

### ✅ CORRECTIONS DE R3 ET DE LA QUALIFICATION, CODÉES ET ÉPROUVÉES HORS LIGNE — 23/10 *(Frédéric : « oui bien sûr »)* — commit `7fce928`, **non actif**
- **F1** : `prix_publique` d'un compromis (= le prix de vente) se compare à **prix public − honoraires de sortie** (`@prixDeVente`),
  l'invariant de Hektor et la formule que le worker pose déjà en modification. Sans honoraires relus : « en attente », jamais un faux conflit.
- **Offre** (`R3_NON_CONTROLES`, déclaré avec ses décisions) : honoraires (16/10), taux (classe A, 03/09), notaire (« personne ne le
  relit », 16/09) **ne sont plus contrôlés**. Au compromis et à la vente, ils le restent. ⚠ L'envoi chez Hektor n'est pas touché.
- **F7** est couvert par la même table (le notaire d'une offre n'est plus étiqueté « sans objet » : il n'est plus jugé).
- **Qualification** : l'acquéreur se cherche par **notre** numéro **et** celui de **Hektor** (patron de 8a-B2).
- **Essais** : `test_controle_carnet_r3.js` **41/41** ; `test_qualification_numero_hektor.js` **4/4**. Témoins inverses sur la version
  **en service** : 3 et 2 échecs (dont le vrai « 605963 inconnu »). Mutants : prix de vente comparé au prix public, offre tout contrôlée,
  déduction sans honoraires relus, retrait sans regarder le registre → **4 attrapés**. `\r\r\n` = 0.
- ⚠ **Les lignes déjà jugées restent telles quelles** (1001379 `prix_publique` « conflit », 1001378 honoraires / taux « arrivée »,
  notaire « sans objet ») : R3 ne rejuge pas une ligne tranchée. Les remettre à blanc = une écriture en base, **à l'accord de Frédéric**.
- ➡ **Pour l'activer** : pousser, redémarrer les 4 services file vide.
- ✅ **ACTIF le 23/10 à 12:11** *(Frédéric : « poussé et 4 services redémarrés, file vide »)* : `7fce928` est sur `origin/main`
  (commit de 12:08:54) ; les **4 processus** du worker sont nés à **12:11:07-09**, après le commit ; file vide (0 en attente, 0 en
  cours), aucun travail ni erreur depuis. ⏰ Première preuve réelle : la prochaine relecture ou création de transaction, puis la nuit.

## 20. A1 ET A5 — audit du 23/10 *(Frédéric a choisi : A1 la rétractation, A5 la modification écrit au registre ; l'envoi des honoraires / taux d'une offre est GARDÉ)* — lecture seule

### A1 — la rétractation ne retombe plus à « 10 »
- **Worker** : `REGISTRE_PAR_HEKTOR` gagne `dateEnd → date_fin_retractation`. Le retour (création ET modification) écrit donc la fin
  de rétractation **relue chez Hektor**, comme la nuit le fait déjà (`affaire_ledger.py` l. 837). Seul le compromis rend `dateEnd`.
  La colonne existe (R1 l'écrit) : le PATCH ne peut pas être refusé pour une colonne inconnue.
- **Écran** : la modale se replie sur `date_fin_retractation − date` (en jours) quand le carnet n'a pas la ligne, comme la grille
  (« jusqu'au … »). Garde : un nombre entre 1 et 365, sinon « 10 » comme avant.
- **Ce que ça pourrait casser** : la règle de sortie ne change pas (`jours_retractation` n'a pas de colonne : il reste au carnet) ;
  aucun verdict ne lit `date_fin_retractation` ; lecteurs : la grille, la modale, la nuit (qui la réécrit de toute façon). Un compromis
  sans date de fin chez Hektor (la plupart des anciens) garde « 10 » — comme aujourd'hui.

### A5 — la modification écrit au registre ce qu'elle ENVOIE
Aujourd'hui `app_modifier_affaire_optimistic` n'écrit au registre que `montant` et `date`. R1 l'avait promis « création + modification ».
**Le piège trouvé à l'audit** : l'ancien verdict (`marquerLeCarnetRestant`) compare la saisie **au registre** après le retour. Si la
modification écrit NOTRE valeur au registre et que Hektor ne la rend pas à la relecture, le verdict se comparerait **à lui-même** —
« arrivée » sans preuve, ligne retirée. Mesuré : c'est le cas du **net vendeur d'une VENTE** (« la vente n'a pas de prixNetVendeur »).
**D'où le dessin, colonne par colonne — n'écrire que ce que Hektor RELIT, ou ce qu'aucun verdict ne juge sur le registre** :
| genre | colonnes écrites au clic de la modification |
|---|---|
| offre | validité (relue par numéro) · honoraires acquéreur, taux (non jugés) |
| compromis | date d'acte, séquestre, net vendeur, honoraires vendeur et acquéreur (tous relus) · taux · fin de rétractation (non jugés au registre ; A1 la réécrit au retour) · notaires · mandants |
| vente | honoraires vendeur et acquéreur (relus) · taux · notaires · mandants — **PAS le net vendeur** |
- **Seulement ce qui a été TOUCHÉ** (la liste `champs_touches` de E) ; les notaires seulement s'ils sont **affirmés** (`notaires_affirmes`),
  les mandants seulement s'ils sont **désignés** — exactement ce que le worker envoie comme intention. **E éteint ou liste absente : rien
  ne change.** « Vide ne gagne pas » : une case vidée n'efface pas le registre.
- La **photo** du carnet reste prise dans la ligne lue AVANT l'écriture (déjà le cas).
- **Ce que ça pourrait casser** : la nuit réécrit encore les colonnes partagées depuis Hektor (c'est R2, pas fait) — notre saisie reste au
  carnet et l'écran la montre d'abord, comme pour la création. Les chaînes ne lisent que `date` (déjà écrite). Le classeur et l'export lisent
  le registre : ils verront la valeur saisie dès le clic au lieu du lendemain.
- **La forme** : un patch SQL de la RPC, généré avec ses gardes d'empreinte (`049643b8` → empreinte calculée d'avance), son **inverse** et
  sa **répétition** ; **collé par Frédéric**. Plus les essais du worker (A1) et la compilation de l'écran.

### ✅ A1 ET A5 CODÉS — 23/10 *(Frédéric : « vas-y : code A1 et A5 comme décrit »)* — commit `5b0e2fb`, **non actif**
- **A1** : worker (`REGISTRE_PAR_HEKTOR` : `dateEnd → date_fin_retractation`) + modale (repli sur fin − date, 1 à 365 jours).
  `Console/test_report_retractation.js` **4/4** ; la version **en service** échoue le contrôle (1) — témoin inverse. `npm run build` vert.
- **A5** : `supabase/patch_a5_modif_au_registre_2026-10-23.sql` (+ `_INVERSE`, + `_REPETITION`), générés d'un seul texte
  (`phase2/checks/gen_patch_a5_modif_au_registre.py`). Empreinte **049643b8 → 0dac8c86**, calculée DANS la base en lecture seule ;
  l'ancre est trouvée **1** fois (mesuré). Interrupteur **`affaire_modif_au_registre`, posé ÉTEINT**. La répétition (11 cas, dont le
  témoin éteint, la vente sans net vendeur, la photo d'avant, l'inverse) **s'annule seule**.
- ⛔ **À faire par Frédéric, dans l'ordre** : coller la RÉPÉTITION (elle doit finir sur « ESSAI ANNULE -- 11 sur 11 ») → coller le PATCH
  (5 contrôles OK) → **allumer** l'interrupteur → pousser (A1 : worker + écran) → redémarrer les 4 services file vide.
- ⚠ **Retour arrière** : éteindre l'interrupteur suffit à suspendre A5 ; l'inverse rend 049643b8.
- ✅ **A5 POSÉ ET ALLUMÉ EN PRODUCTION — 23/10, 13:14** *(Frédéric : « fais-le toi-même, tu as mon accord »)*, par `execute_sql` :
  - **répétition** jouée **telle que le fichier** : « ESSAI ANNULE -- **11 sur 11** », retour arrière compris. ⚠ Un premier passage avait
    un dernier cas réécrit à la main (le contrôle de l'inverse remplacé par celui de l'empreinte posée) : il ne valait pas preuve de
    l'inverse, je l'ai rejoué À L'IDENTIQUE. Vérifié ensuite : rien n'est resté (empreinte 049643b8, pas d'interrupteur, registre intact,
    0 travail) ;
  - **patch** collé : **5 contrôles OK** (empreinte **0dac8c86**, interrupteur créé éteint, droits et SECURITY DEFINER inchangés, E allumé) ;
  - **interrupteur `affaire_modif_au_registre` allumé** à 11:14:13 UTC.
  - ⏰ Reste : pousser A1 (worker + écran) et redémarrer les 4 services — puis le second essai complet.

## 21. LE SECOND ESSAI COMPLET — 23/10, 13:30-14:00, avec 7fce928 + A1 + A5 actifs *(Frédéric : « lance le second essai complet », VA6482 nettoyé d'abord)*

**Nettoyage de la première chaîne (accord de Frédéric)** : vente 23354 supprimée · compromis 50131 supprimé · **offre 33110 refusée,
vérifiée « refus » par l'API de Hektor** · clôture locale du mandat 18787 retirée (sauvegarde
`app_mandat_champ_app_avant_essai_va6482_20261023`). ⚠ **La suppression de la vente a remis `diffusable = 1` chez Hektor** → remis à 0
par Pilotage, vérifié par `AnnonceById`.

| étape | résultat |
|---|---|
| contact « Propriétaire » | **20000012 ↔ 605967**, typologie « mandant », 0 recherche, contrôle 0 écart |
| offre **33112** (1001381) | ⭐ honoraires, taux, notaire **non contrôlés** (étiquette vide, gardés) ; montant, date, validité retirés |
| acceptée | done, `accepted` |
| compromis **50132** (1001382) | **même chaîne 1001381** ; ⭐ **F1 : prix de vente 112 000 = 118 000 − 6 000 « arrivée », 0 conflit** ; ⭐ la recherche de qualification **créée** et l'acheteur **gardé** par Hektor (« acquéreur, mandant ») |
| modification (rétractation 21 → 28, séquestre 5 500 → 6 500) | ⭐ **A5 au clic** : registre 6 500 et fin 20/11 pendant que le travail tournait ; `champs_touches` = les 2 ; photo = 5 500 ; ⭐ **A1** : le retour écrit la fin relue (20/11) ; ⭐ **B** : seule la ligne réécrite est rejugée (28 « arrivée ») ; la modale montre **28** |
| vente **23355** (1001383) | **même chaîne 1001381** ; personnes gardées ; mandat clos chez nous ; R3 : 3 retirés, 3 gardés |

### ⚠ Ce que ce second essai a trouvé
- **F8 — la cascade de ma correction 7fce928** : reconnu sous le numéro de Hektor, l'acquéreur partait à la suite de la qualification avec
  ce numéro → « Contact introuvable dans l'index Supabase: 605967 ». Sans effet ici (Hektor l'avait déjà comme acquéreur). **Corrigé,
  commit local** (la suite reçoit NOTRE numéro ; une relance retrouve ses traces) — essai 6/6, témoin inverse ✅. **Non actif.**
- **F9 — la recherche de qualification n'est PAS archivée** (« identifiant non retrouvé, elle ne sera pas archivée ») : une recherche
  active reste sur le contact d'essai chez Hektor. À auditer (`listerCriteresBestEffort` avant / après). **Non traité.**
- **F10 — `diffusable` repasse à 1 chez Hektor** après la suppression d'une vente ET après la création de la vente (Vendu). La fiche d'un
  bien Vendu n'a pas « Pilotage » : **l'app ne peut pas le remettre à 0**. VA6482 est à **1** en ce moment (aucun portail actif).
- **F11** — du compromis depuis l'offre, la **commission vendeur et la charge** ne sont pas reprises de l'offre (le lot 1c du 16/10 le
  promettait). Préexistant, non traité.
- La typologie de notre fiche reste « mandant » jusqu'à la relecture du contact (Hektor dit « acquéreur, mandant ») — d'où F8.
- ⏰ **Demain matin, la preuve de nuit porte sur la SECONDE chaîne** (1001381 : offre 33112, compromis 50132, vente 23355).

### L'acquéreur est-il relu et validé ? *(Frédéric, 23/10)* — mesuré dans les journaux
- **Compromis 50132** : relu chez Hektor, et le contrôle des personnes dit **demandés [605967] = gardés [605967]** ; mandants demandés
  [603953] = gardés. ✅
- **Vente 23355** : acquéreur demandé [605967] = gardé. ✅
- **Offre 33112** : ⚠ **pas de relecture des personnes** — une offre n'a pas d'assistant chez Hektor (« Assistant relu : 0 acquéreur ») et
  son API ne rend pas l'acquéreur. L'offre est prouvée créée (fiche + API), mais **pas son acquéreur** ; le registre garde NOTRE numéro
  (20000012) jusqu'à la nuit. Préexistant.
- ✅ **Correction du point 6 de la liste** : le **notaire du vendeur EST gardé** au compromis — la relecture de la modification (11:55)
  rend « 1 notaire mandant ». Le « 0 » de la création était lu AVANT que Hektor l'enregistre.
- ⚠ **Trouvé en passant** : Hektor **ajoute l'acquéreur d'une vente aux mandants du bien**. VA6482 porte désormais **7 mandants**,
  dont **605963** (l'acquéreur de la 1ʳᵉ vente, supprimée depuis). La suppression de la vente ne le retire pas. À nettoyer.

### Pourquoi l'écran ne montre pas l'acquéreur du compromis et de la vente *(Frédéric, 23/10, vu dans Chrome)*
- **La donnée est juste** : le registre porte 605967 sur le compromis 50132 et la vente 23355, et Hektor l'a gardé.
- **Les cartes « Compromis » et « Vente »** (App.tsx ~27013-27040) n'ont **aucune ligne « Acquéreur » dans le code** — seule l'offre en a
  une. L'acquéreur est censé apparaître dans le bloc **« Parties à l'affaire »**.
- **« Parties à l'affaire »** (`ckAffPartyCards`, App.tsx ~28527) lit l'acquéreur dans le **résumé d'affaires du registre des mandats**
  (`app_registre_mandats_current.affaires_detail_json`) — refait **la nuit seulement** (D9, noté le 22/10, « non vérifié à l'écran » :
  c'est vérifié maintenant). Mesuré : **aucune ligne** pour VA6482 en ce moment → le bloc n'affiche que le propriétaire (repli).
- Sur la carte de l'offre, le nom apparaît **deux fois** (« X et X » : le principal et la liste).
- **Ancien** : D9 existait avant R1 ; R1 a rendu le registre des transactions complet au clic, mais l'écran lit encore un résumé de nuit.
- **Correction proposée (écran)** : les cartes et « Parties à l'affaire » se replient sur le **registre des transactions** quand le résumé de
  nuit n'a pas encore l'affaire ; le nom n'est plus doublé. ⏰ Et vérifier demain si la nuit ramène la ligne d'un bien VENDU.

### Les cartes à moitié vides — lu dans le code (`ckAffaireDepuisChaine`, App.tsx ~27951) *(Frédéric, 23/10)*
1. **Par construction** : la carte Compromis porte prix, net, dates, rétractation, séquestre ; la carte Vente prix, date, honoraires,
   commission, notaires ; **aucune des deux n'a de ligne Acquéreur** (seule l'offre). La carte Compromis est **repliée** dès qu'une vente
   existe (`open = compromis pas terminé`) : on n'en voit que l'en-tête. Le « net vendeur » de l'offre est vide **en dur** (`net: ''`).
2. **Ce qui n'arrive que la nuit** : la commission agence HT et les notaires de la vente (l'API, relue la nuit), et le bloc « Parties à
   l'affaire » (résumé du registre des mandats, D9).
3. **La lecture console (notaires, honoraires vendeur, conditions) n'est prise que pour l'étape LA PLUS AVANCÉE** (`courante` = la vente) :
   dès qu'une vente existe, la carte du compromis perd les notaires et les conditions du compromis.
4. **Le nom doublé** : l'offre porte l'acquéreur sous NOTRE numéro (20000012), le compromis et la vente sous celui de HEKTOR (605967) ;
   `affaireAcquereursDeChaine` les compte comme deux personnes → « X et X ».
➡ Tout est **ancien** (l'écran n'a pas été touché par ⑧, sauf le repli validité / rétractation de la modale).

### Pourquoi la rubrique Affaires ne montre pas ce que le registre porte, et pourquoi la répartition ne se voit pas *(Frédéric, 23/10 : « STOP »)* — lu dans le code
**La rubrique Affaires** (cartes `ckAffaireDepuisChaine` + « Parties à l'affaire ») a été dessinée le **17/07 pour montrer ce que Hektor
rend**, et branchée sur le registre le 03/09 (2.1). **R1 (22/10) a ensuite rempli le registre au clic — mais la rubrique n'a jamais appris
à lire ces colonnes** : notaires (`notaire_acquereur_*`, `notaire_mandant_*`), taux, mandants, acquéreurs du compromis et de la vente,
commission `_app` et charge. Elle lit à la place : un champ fixe par carte · la lecture console (étape la plus avancée seulement) · l'API
de nuit (notaires de la vente) · le résumé de nuit du registre des mandats (« Parties à l'affaire », D9).

**La répartition** :
- **elle n'est affichée nulle part dans la rubrique Affaires** — un seul lecteur dans tout l'écran : la modale de statut
  (`loadRepartition`, App.tsx ~17213) ;
- **dans la modale, elle se retrouve par « le dossier ouvert du bien »** (`repartitionChaineId` → `dossiersOuvertsDuBien` : une chaîne
  qui porte une vente n'est plus « ouverte »). Dès la vente, la modale **ne trouve plus la chaîne** → elle montre la **répartition par
  défaut** (sortie 1 = FRANCK GERPHAGNON 50 %) au lieu de celle enregistrée (4 × 25 %) ;
- ⛔ **et un enregistrement à ce moment-là partirait sous le numéro de la VENTE (1001383) au lieu de la chaîne (1001381)** — c'est pour ça
  que l'essai a été arrêté : rien n'a été envoyé.
- Ancien (modale du 14/09) ; l'essai complet l'a révélé.

## 22. AUDIT EN PROFONDEUR — chaque champ saisi : où il dort, qui le montre, et s'il survit à la vente — 23/10 *(Frédéric : « dans la rubrique Affaires on doit faire apparaître tous les renseignements saisis sur l'offre, le compromis, etc., et dans la modale aussi, et que ce soit mémorisé après la vente »)* — lecture seule

> **Audit limité à l'objet TRANSACTION** (offre, compromis, vente) × les gestes **créer / modifier / lire**. Supprimer n'est pas
> mesuré ici. Mesuré sur le code (App.tsx, api.ts, worker) **et** en base sur les chaînes d'essai 1001378 et 1001381 (VA6482).

### 22.1 Où chaque champ dort

| table | clé | ce qu'elle porte |
|---|---|---|
| `app_affaire_ledger` (le registre) | l'affaire | montant, date, validité, date d'acte, séquestre, net vendeur, fin de rétractation, n° mandat, acquéreurs, mandants, honoraires entrée/sortie (Hektor), **`honoraires_entree_app` / `honoraires_sortie_app` / `charge_commission_app` (à nous)**, taux, les 2 notaires (id + nom) |
| `app_affaire_champ_app` (le carnet) | l'affaire | ce qui n'a **pas de colonne** : prix public, honoraires, taux, rétractation (jours), notaire de l'offre — et le reste tant qu'il n'est pas arrivé |
| `app_affaire_repartition` | **la chaîne** | la répartition (entrée 1/2, sortie 1/2, %) |
| `app_affaire_condition` | l'affaire | les conditions suspensives |
| `app_affaire_note` | l'affaire | la note libre |
| `app_affaire_console` | l'affaire | ce que le worker a **lu** dans l'assistant de Hektor (notaires, conditions de Hektor, partage) |

⭐ **Rien n'est effacé par la vente** : toutes ces lignes restent (mesuré : la chaîne 1001381 garde ses 3 affaires, 4 lignes de répartition,
son carnet). **Le problème n'est pas la mémoire, c'est la LECTURE** : qui va chercher quoi.

⚠ **Non mesuré : la nuit.** Le run peut-il effacer une colonne posée au clic (les notaires du compromis surtout, que l'API ne rend jamais) ?
C'est la preuve de nuit prévue demain matin sur 1001381.

### 22.2 Le tableau — champ par champ

✅ = montré · ❌ = absent · ⚠ = montré, mais d'une autre source que la saisie

| champ saisi | genre | dort dans | **carte de la rubrique** | **modale (modifier)** | **après la vente** |
|---|---|---|---|---|---|
| montant / prix | 3 | registre | ✅ | ✅ | ✅ |
| date | 3 | registre | ✅ | ✅ | ✅ |
| validité | offre | registre | ✅ | ✅ (941cb70) | ✅ |
| date d'acte, séquestre | compromis | registre | ✅ | ✅ | ✅ |
| rétractation | compromis | registre (date de fin) | ✅ « jusqu'au » | ✅ (A1) | ✅ |
| rétractation | offre | carnet | ❌ | ✅ | ✅ |
| net vendeur | compromis | registre | ✅ | ✅ | ✅ |
| net vendeur | vente | registre | ❌ | ✅ | — |
| acquéreur(s) | offre | registre | ✅ | ✅ | ✅ |
| acquéreur(s) | compromis, vente | registre | ❌ (pas de ligne) | ✅ | ⚠ bloc « Parties » = résumé de **nuit** |
| mandants | compromis, vente | registre | ❌ | ✅ | ⚠ résumé de nuit |
| notaire de l'acquéreur | offre | carnet | ❌ | ✅ | ✅ (carnet) |
| notaires (acq. + vendeur) | compromis | registre (R1/A5) | ⚠ lus dans la **console de l'étape la plus avancée** — après la vente, celle de la VENTE | ✅ | ⚠ |
| notaires | vente | registre (R1) | ⚠ lus dans `notaires_json` (API de nuit) → **« — » au clic** alors que le registre les a | ✅ | ⚠ |
| honoraires acquéreur | offre | registre `_app` + Hektor | ❌ | ✅ | ✅ |
| honoraires vendeur | offre | registre `honoraires_entree_app` | ❌ | ❌ **(F5 : la modale lit `honoraires_entree`, vide sur une offre)** | ✅ repris au compromis |
| honoraires vendeur | compromis | registre (Hektor) | ⚠ console seulement | ✅ | ✅ |
| honoraires (entrée + sortie) | vente | registre | ✅ | ✅ | ✅ |
| taux | 3 | registre + carnet | ❌ | ✅ (carnet) | ✅ |
| charge de la commission | 3 | registre `charge_commission_app` | ❌ | ❌ en modification (seulement **reprise de l'offre** à la création du compromis/vente) | — |
| prix public | offre, compromis | carnet | ❌ | ✅ | ✅ |
| n° de mandat | 3 | registre + carnet | ❌ | ⚠ **carnet seulement** — quand la ligne sort du carnet (même valeur au registre), la case se vide | — |
| **répartition** | la chaîne | `app_affaire_repartition` | ❌ **nulle part** | ✅ avant la vente | ⛔ **la modale ne la trouve plus** → défauts 50 %, et **enregistrer l'écrirait sous le n° de la VENTE** |
| **conditions suspensives** | l'affaire | `app_affaire_condition` | ⚠ la carte lit les conditions **de Hektor** (console), **jamais les nôtres** | ✅ | ✅ (par affaire) |
| **note libre** | l'affaire | `app_affaire_note` | ❌ nulle part | ✅ | ✅ |
| bloc « Honoraires & rendement » | — | — | ❌ jamais rempli par la chaîne (le constructeur ne pose pas `honoraires`) | — | — |

⚠ **Pas éprouvé dans les essais** : les conditions suspensives et la note — **0 ligne** dans les deux tables pour les 4 affaires d'essai.

### 22.3 Les causes — 4, toutes anciennes

1. **La rubrique a été dessinée le 17/07 pour montrer ce que Hektor RENDAIT** : une liste fixe de lignes par carte. R1 (22/10) a rempli le
   registre au clic, **la rubrique n'a jamais appris à lire ces colonnes**.
2. **Ce qui est à nous** (répartition, conditions, note, commission `_app`, charge) **n'a qu'un lecteur : la modale.** La rubrique montre
   ce que Hektor dit (console, API), pas ce que nous avons saisi.
3. **« Parties à l'affaire » vient du résumé de nuit** (`app_registre_mandats_current.affaires_detail_json`) — **24113 n'a aucune ligne**
   dans cette table aujourd'hui (mesuré) : bloc vide jusqu'à la nuit, peut-être plus longtemps pour un bien vendu (à mesurer demain).
4. **La modale retrouve la répartition par « le dossier OUVERT du bien »** (`repartitionChaineId` → `dossiersOuvertsDuBien`) ; une
   chaîne qui porte une vente n'est plus ouverte. Les conditions et la note, elles, sont rangées **par affaire** : elles survivent.

### 22.4 Le plan de correction — 7 pièces, **à trancher par Frédéric** (périmètre et ordre)

| # | quoi | où | risque / ce que ça pourrait casser ailleurs |
|---|---|---|---|
| **P1** | les **cartes lisent le registre** : offre + honoraires (acq./vendeur), taux, charge, n° mandat, notaire, prix public, rétractation ; compromis + acquéreur(s), mandants, honoraires, taux, charge, notaires **du registre d'abord**, console en repli ; vente + net vendeur, acquéreur(s), mandants, charge, notaires **du registre d'abord** | front (`ckAffaireDepuisChaine`, cartes) + lecture du carnet dans la rubrique | **lecture seule, rien chez Hektor.** Règle gardée : **pas de « — » pour « pas lu »** (une ligne n'apparaît que si elle a une valeur). ⚠ Mandants de la vente : Hektor y **ajoute l'acquéreur** (VA6482 en porte 7, dont 605963, l'acquéreur d'une vente supprimée) — la carte montrerait ces 7 tels quels |
| **P2** | la **répartition affichée** dans la rubrique (bloc par chaîne, nom + %) | front + `loadRepartition` (déjà écrit) | lecture seule. ⚠ La table est en lecture pour qui ? À vérifier pour le négociateur (droits du chantier ②) |
| **P3** | la **modale retrouve la répartition de la chaîne VISÉE**, même vendue : d'abord la chaîne de l'affaire courante, ensuite seulement l'ancienne règle ; et **ne jamais enregistrer sous un n° d'affaire quand une chaîne existe** | front (`repartitionChaineId`, enregistrement ~17630) | ⚠ **touche à de l'argent.** À la création (pas d'affaire courante), le chemin d'aujourd'hui reste identique. Essai : modifier la vente → les 4 × 25 % reviennent, l'enregistrement garde 1001381 |
| **P4** | **nos conditions et notre note** sur la carte du compromis (et de l'offre), celles de Hektor en repli | front + `loadAffairesConditions` / `loadAffairesNotes` (déjà écrits) | lecture seule. ⚠ « aucune » et « pas encore lu » ne se disent pas pareil (règle déjà écrite pour la console) |
| **P5** | la **modale d'une offre** reprend honoraires vendeur et charge (`honoraires_entree_app`, `charge_commission_app`) — F5 | front (préremplissage) | le préremplissage **ne lève pas le drapeau** « touché » : rien ne part tant qu'on ne tape pas (même discipline que les acquéreurs) |
| **P6** | la **modale reprend le n° de mandat du registre** quand le carnet n'en a plus | front, 1 ligne | rien ne part tant qu'on ne touche pas |
| **P7** | **« Parties à l'affaire » prend la chaîne** quand le résumé de nuit manque ; et **un même contact sous deux numéros** (20000012 / 605967) ne s'affiche qu'une fois | front | lecture seule. ⚠ Le dédoublonnage s'appuie sur la paire `hektor_contact_id` / `hektor_target_id` (règle « reconnaître par la plage ») — jamais sur le nom |

**Hors de ce plan, déjà notés** (à part si Frédéric les veut dedans) : F9 la recherche de qualification jamais archivée · F10 la diffusion
remise à 1 par Hektor · F4 le prix de vente = prix du mandat · l'acquéreur de l'offre jamais relu · les mandants ajoutés par Hektor à la vente.

**Ensuite, dans l'ordre demandé** : nettoyer VA6482 (supprimer la vente 23355, le compromis 50132, refuser l'offre 33112, la clôture locale
avec sauvegarde datée, la diffusion), puis le **troisième essai complet**, **en saisissant cette fois conditions, note et répartition à 100 %**.

## 23. LE PLAN RAMENÉ À « COMME AVANT, MAIS TOUT DE SUITE » — 23/10 *(Frédéric : « je ne demande pas mieux que avant ce chantier au niveau affichage, juste que tout fonctionne correctement et soit visible comme avant » ; « la modale est liée à l'affaire en cours… il faut pouvoir modifier la répartition sur le compromis ; une vente peut juste être choisie et supprimée »)* — lecture seule

⚠ **Le §22.4 (P1-P7) allait trop loin** : il ajoutait des lignes que l'écran n'a jamais eues. **Le modèle à reproduire est VM71227**
(bien vendu le 19/10, passé par la nuit), où tous les blocs sont pleins.

### 23.1 Ce que la relecture du code d'avant a établi
- **Le résumé de nuit est fabriqué MÉCANIQUEMENT à partir des mêmes champs que notre registre des transactions**
  (`export_app_payload.py`, `build_affaire_detail_for_cycle`, ~l. 996) : acquéreur = 1er de `acquereurs_json`, mandant = 1er de
  `mandants_json`, notaire de la vente = 1er de `notaires_json`, plus prix, dates, séquestre, net. **Notre registre porte tout cela dès le
  retour de Hektor** (mesuré sur 1001382 / 1001383). Refaire la même recette à l'écran, sur le registre, donne **le même bloc**, sans attendre.
- ⛔ **Attendre la nuit ne suffirait pas pour VA6482** : son mandat 18787 n'a **aucune ligne** dans `app_mandat_register_current`
  (mesuré : 0, alors que VM71227 en a une et qu'il y en a 6 775 avec une vente). Le bloc « Parties à l'affaire » ne s'y remplirait **jamais**.
- **La répartition vit dans la modale, et seulement là — c'est le dessin du 14/09.** On ne l'ajoute pas à la rubrique.
- **Après la vente, le compromis reste « vivant »** (`en_cours`) : l'onglet Compromis de la modale le vise toujours, « Modifier chez Hektor »
  y est offert. C'est là que la répartition doit se modifier — et c'est là qu'elle est perdue (`repartitionChaineId` → `dossiersOuvertsDuBien`
  écarte une chaîne qui a sa vente).
- **L'onglet Vente** offre aujourd'hui « Modifier chez Hektor » ET « Supprimer la vente » (App.tsx ~21403, ~21436). Le projet avait mesuré
  que le worker *peut* modifier une vente (LISTE l. 4760 ; PLAN l. 2237 : sans danger sur une annonce active, **danger sur une annonce
  archivée**). ⚠ Frédéric dit « une vente peut juste être choisie et supprimée » : **retirer « Modifier » de la vente est à trancher par lui.**

### 23.2 Les 6 corrections — écran seulement, rien chez Hektor, rien en base
| # | quoi | résultat attendu |
|---|---|---|
| **C1** | « Parties à l'affaire » : **quand le résumé de nuit n'a pas la transaction la plus récente** (ou pas de ligne du tout), le bloc est fabriqué **avec la recette de la nuit**, appliquée au registre des transactions | acquéreur + coordonnées, mandant, comme VM71227, **dès le retour de Hektor** |
| **C2** | carte Vente : notaires de `notaires_json` **d'abord** (comme avant), sinon ceux que le registre porte depuis le clic (`notaire_mandant_*`, `notaire_acquereur_*`) | plus de « — » le jour de la vente |
| **C3** | chaque carte lit la lecture de l'assistant de **SA** transaction (aujourd'hui : celle de l'étape la plus avancée seulement) | la carte du compromis garde ses notaires, ses honoraires vendeur et ses conditions après la vente |
| **C4** | une même personne sous ses deux numéros (notre ≥ 10 M / celui de Hektor) **comptée une fois** — par la paire `hektor_contact_id` / `hektor_target_id`, jamais par le nom | plus de « X et X » |
| **C5** | modale : la répartition est cherchée **d'abord dans la chaîne de la transaction visée** (le compromis, même après la vente), l'ancienne règle ensuite ; et **jamais enregistrée sous un n° de transaction quand la chaîne existe** | on rouvre le compromis vendu : les vraies parts reviennent, on les modifie, elles restent sur la chaîne |
| **C6** | modale d'une offre : reprendre honoraires vendeur et charge saisis (`honoraires_entree_app`, `charge_commission_app`) et le n° de mandat du registre, **sans lever le drapeau « touché »** | ce qui a été saisi se revoit ; rien ne part tant qu'on ne tape pas |

**Ce que ça pourrait casser ailleurs** :
- C1 : le bloc « Dossiers abandonnés » lit aussi le résumé de nuit (`dossiers[]`) — **il n'est pas touché** ; un cycle **passé** garde son
  résumé (le repli ne joue que pour le cycle courant). Si le résumé est plus récent que le registre, **c'est lui qui gagne** (comme avant).
- C1 : le mandant pris est le **1er** de la liste, comme la nuit — y compris quand Hektor a ajouté l'acquéreur aux mandants à la vente.
  On reproduit la nuit, on ne la corrige pas.
- C2 : le nom du notaire de l'acquéreur n'est pas toujours au registre (`notaire_acquereur_nom` vide sur 1001382/83) : il faudra le lire
  dans la fiche contact, sinon n'afficher que celui qu'on a.
- C5 : **de l'argent.** À la création (pas de transaction visée), le chemin d'aujourd'hui est inchangé. Essai obligatoire : rouvrir le
  compromis après la vente → 4 lignes reviennent → modifier → la chaîne garde ses lignes, aucune ligne sous 1001383.
- C6 : le prérenseignement ne lève aucun drapeau → la charge envoyée à Hektor ne change pas.

**Pas dans ce plan** (déjà notés, à part) : F9 recherche de qualification non archivée · F10 diffusion remise à 1 · F4 prix de vente =
prix du mandat · acquéreur de l'offre jamais relu · mandants ajoutés par Hektor à la vente · nos conditions et notre note dans la rubrique.

**Ensuite** : `npm run build`, essais hors ligne des fonctions touchées, commit local, Frédéric pousse ; puis nettoyage de VA6482 (geste par
geste, avec accord) et le **troisième essai complet** — conditions, note et répartition à 100 % saisies cette fois, et **la répartition
modifiée sur le compromis après la vente**.

## 24. QUI ÉCRIT LE REGISTRE, QUI LE LIT — l'histoire datée *(Frédéric, 23/10 : « pourquoi avant le registre était déjà indépendant et la vue ne regardait pas le miroir ? » ; « tous les champs, c'est compris ? la répartition dans les blocs ? »)* — lecture seule

### 24.1 Trois étages
1. **Le miroir de Hektor** : la base locale du serveur (`phase2`), refaite **la nuit** depuis l'API et l'assistant de Hektor.
2. **Notre registre des transactions** (`app_affaire_ledger`) : **ses propres numéros** (`app_affaire_id`, `app_chaine_id`), lignes jamais
   effacées — c'est son **indépendance**. Ses colonnes sont remplies par trois écrivains :
   - **la nuit**, depuis le miroir (`affaire_ledger.py` puis l'envoi « SELECT * … puis upsert ») — le registre est maître, le miroir le nourrit ;
   - **le worker, au retour de Hektor** : le numéro Hektor tout de suite (`poserIdTransactionSurAffaire`), la lecture de l'assistant
     (`app_affaire_console`, 10/09) ;
   - **depuis le 22/10 (R1), la création au clic**, et depuis le 23/10 (A5) la modification au clic.
3. **Ce qui n'est qu'à nous** : le carnet, la répartition, les conditions, la note, la commission `_app` et sa charge.

### 24.2 Ce que lit l'écran, et depuis quand (git)
| bloc | lit | depuis | attend la nuit ? |
|---|---|---|---|
| « Parties à l'affaire » | le **résumé du registre des mandats** (`app_mandat_register_current.affaires_detail_json`), fabriqué **la nuit depuis le miroir** | **31/07** (`5e7f743`, `0a352b1`) | **oui** |
| les cartes Offre / Compromis / Vente | **notre registre** (la chaîne) | **03/09** (`e0406f6`, « 2.1 la rubrique Affaires lit le registre ») | non, sauf les colonnes que seule la nuit remplit |
| notaires, honoraires vendeur, taux, partage, conditions (carte Compromis) | la lecture de l'assistant faite **par le worker à l'écriture** | **10/09** (`3a04ada`) | non — mais lue pour l'étape la plus avancée seulement |
| notaires de la carte Vente | `notaires_json`, colonne du registre **remplie par la nuit seulement** (l'API) | 03/09 | **oui** |

➡ **Frédéric a raison pour les cartes** : depuis le 03/09 elles lisent notre registre, pas le miroir. **Mais 2.1 a choisi « lire à côté »
sans toucher au bloc « Parties à l'affaire »** (son message : « CkAffaires PAS TOUCHÉ ») : ce bloc, plus ancien d'un mois, lit encore un
résumé de nuit. C'est **le seul morceau** de la rubrique qui attend la nuit, avec les notaires de la vente.
➡ **VM71227 est complet** parce qu'il est né chez Hektor et que la nuit est passée. **VA6482** est né dans l'app aujourd'hui, et son mandat
n'a aucune ligne au registre des mandats : la nuit ne le remplirait pas.

### 24.3 « Tous les champs » : ce qui n'a JAMAIS été affiché, avant ⑧ non plus
Les cartes portent **une liste fixe de lignes** depuis la maquette du 17/07. Jamais affichés : honoraires, taux, charge et n° de mandat sur
l'offre ; acquéreur(s) et mandants sur les cartes Compromis et Vente ; net vendeur, taux et charge sur la vente ; **la répartition** ; **nos**
conditions et **notre** note. Les montrer, c'est **ajouter** des lignes (le P1, P2, P4 du §22.4), pas réparer.
⚠ **Décision de Frédéric attendue** : C1-C6 seuls (« comme avant, tout de suite »), ou C1-C6 **plus** ces lignes et un bloc « Répartition ».

## 25. C1-C6 + TOUS LES CHAMPS + LE BLOC RÉPARTITION — CODÉ le 23/10 *(Frédéric : « Vas-y : C1 à C6, plus tous les champs saisis sur les cartes et un bloc Répartition dans la rubrique »)* — écran seulement, **pas poussé**

**Fichiers** : `apps/hektor-v1/src/App.tsx`, `apps/hektor-v1/src/lib/api.ts`, essai `apps/hektor-v1/test_rubrique_affaires_complete.cjs`.
Rien chez Hektor, rien en base : uniquement des LECTURES en plus.

| | ce qui change à l'écran |
|---|---|
| **C1** | « Parties à l'affaire » : si le résumé de nuit n'a pas vu la transaction la plus avancée (comparaison par **numéro Hektor**), ou n'existe pas, le bloc est fabriqué avec **la recette de la nuit** appliquée au registre (`ckDetailDepuisRegistre`). Sinon, la nuit, comme avant. Les « dossiers abandonnés » restent ceux de la nuit. Un cycle passé n'est pas touché |
| **C2** | carte Vente : notaires de l'API d'abord, sinon ceux du registre (« … (vendeur) — … (acquéreur) ») |
| **C3** | la carte Compromis lit la lecture de l'assistant **du compromis** (avant : celle de la vente dès qu'elle existait) ; notaires et honoraires vendeur du **registre d'abord**, la lecture en repli |
| **C4** | une personne sous ses deux numéros comptée une fois : paire `app_contact_id` / `hektor_acquereur_id` de chaque ligne |
| **C5** | modale : la répartition est cherchée dans **la chaîne de la transaction visée** d'abord (le compromis après la vente) ; à la création, l'ancienne règle, inchangée |
| **C6** | modale d'une offre : honoraires vendeur et charge repris (`honoraires_entree_app`, `charge_commission_app`), **sans drapeau « touché »** |
| **tous les champs** | offre : honoraires acquéreur, taux, honoraires vendeur, charge, n° mandat, notaire, nos conditions, note · compromis : acquéreur(s), mandant(s), prix public, honoraires acquéreur, taux, charge, n° mandat, nos conditions (avant celles de Hektor), note · vente : acquéreur(s), mandant(s), net vendeur, taux, charge, n° mandat, note. **Une ligne par valeur présente**, jamais de tiret |
| **Répartition** | bloc par dossier sous les cartes (nom · %), et **un côté qui ne fait pas 100 % se dit** (« Total entrée : 50 % attribués sur 100 % ») |

**Choix faits en codant, à relire par Frédéric** :
- sur l'**offre**, le prix public et la rétractation du carnet **ne s'affichent pas** : ce sont les valeurs **pré-remplies** par la modale (constat 7), pas des saisies ;
- le **n° de mandat n'est pas repris du registre dans la modale** (C6 réduit) : `selectedMandat` part **toujours** dans la charge du geste (App.tsx ~17541) — le reprendre changerait ce qui part chez Hektor ;
- une fiche mandant **sans nom ni prénom** (« Mr./Mme » seul, VA6482 en a une) n'est pas listée.

**Contrôles** : `npm run build` vert · `node apps/hektor-v1/test_rubrique_affaires_complete.cjs` **18/18**, sur les lignes mesurées de VA6482,
en exécutant le code découpé dans App.tsx · **témoin inverse** : 16 sur 18 échouent sur la version d'avant (les 2 autres disent « rien ne
change » : le pré-rempli caché, l'ancienne règle à la création).
⚠ **Pas éprouvé hors ligne** : C6 (le préremplissage vit dans un effet du composant) — vérifié à la lecture seulement ; et **rien n'est vu à
l'écran** : ce sera le troisième essai, après le push.

**Décisions de Frédéric sur les choix du §25 (23/10)** :
- **offre : le « Prix de vente » ne s'affiche pas** sur la carte — *« si il y a le montant de l'offre c'est suffisant »*. (La case est
  pourtant une vraie saisie : visible et modifiable sur l'onglet Offre, pré-remplie du prix du bien.) La rétractation reste cachée
  (aucune case sur l'onglet Offre : le « 10 » est le défaut de la modale).
- **n° de mandat** : pas repris du registre dans la modale (vide = le worker prend la valeur de Hektor, « id-FAMILLE »). ⚠ Nos essais
  du 23/10 ont TAPÉ 18787 : 7 gestes l'ont envoyé ; que Hektor ait gardé le mandat n'est **pas vérifié** (carnet « en_attente ») —
  à juger avec la preuve de nuit.

## 26. LE TROISIÈME ESSAI — 23/10, 16:30-16:50 — ARRÊTÉ APRÈS L'OFFRE : deux défauts trouvés

**Actif** : front déployé (le paquet en ligne porte « Taux honoraires acquéreur », « Total entrée ») ; 4 workers démarrés à 16:30:40-41
(après cd46764) ; file vide. **Vu à l'écran, sur les données de l'essai 2, AVANT nettoyage** : cartes complètes, nom non doublé,
« Parties à l'affaire » rempli sans la nuit (acquéreur + coordonnées, mandant 189298, notaire PAILHES), bloc Répartition, et **la modale
du compromis après la vente retrouve les 4 × 25 %** (avant : défauts).

**Nettoyage VA6482** (accord de Frédéric) : vente 23355 supprimée · compromis 50132 supprimé · offre 33112 refusée (Hektor : `refus`) ·
clôture locale retirée (sauvegarde `app_mandat_champ_app_avant_essai3_va6482_20261023`) · Hektor : `diffusable 0`, statut « Sous offre ».

**Essai 3** : contact **20000013** (Hektor **605973**, « mandant » seul) · offre **33114** / chaîne **1001384** : montant 115 000, validité 15,
honoraires acq. 5 000, taux 4,35, honoraires vendeur 6 500, charge acquéreur, acquéreur, mandant TESTCLAUDE, notaires PAILHES / Tiffany
SELARL, note libre, répartition 30 / 20 / 25 / 25. N° de mandat laissé VIDE exprès (le registre porte quand même 18787).

⛔ **DÉFAUT 1 — la note et les conditions saisies À LA CRÉATION ne sont JAMAIS enregistrées.** Le code (App.tsx, après le geste) vise
`affaireCourantePourStatut()`, qui est **vide à la création** ; la répartition et la commission, elles, se replient sur le numéro neuf
rendu par le travail (`payload_json.app_affaire_id`). Depuis le 16/09 (conditions, cb864a5) et le 17/09 (note, 0329f36).
**Mesuré : `app_affaire_note` = 0 ligne et `app_affaire_condition` = 0 ligne dans TOUTE la base.** ⚠ Mon compte rendu de l'essai 2
(« conditions suspensives : gardées chez nous ») était **faux** : je ne l'avais pas mesuré.

⚠ **DÉFAUT 2 (déjà noté F11)** — sur une **offre**, le mandant et le notaire du vendeur désignés ne sont gardés **nulle part** (registre :
`mandants_json` et `notaire_mandant_*` vides ; carnet : seulement `notaire_id` = notaire de l'acquéreur).

⚠ **MON ERREUR SUR LA RÉPARTITION** : les 4 parts se comptent **ensemble** sur 100 % (la modale : « Les parts font 200 % … refusé »).
4 × 25 était donc **juste**, et je l'avais dit faux. Le bloc de la rubrique est corrigé (commit d210d1c : « Total — N % attribués à
personne » seulement si la somme des 4 n'est pas 100) ; essai 19/19.

## 27. LE NOTAIRE DU VENDEUR DE L'OFFRE — décision A (le garder chez nous) ; la note et les conditions corrigées — 23/10

**Pourquoi il se perdait** : (1) une offre Hektor n'a ni notaire ni mandant (0 sur 11 190, §4) ; le worker envoie quand même
`notairesMandant[]` avec l'offre (`submitHektorTransactionStatus`), sans relecture possible ; (2) R1 n'écrit les notaires que « pour le
genre où Hektor les porte » (compromis, vente) ; (3) le carnet n'a qu'un champ notaire, `notaire_id` = celui de l'acquéreur (d'avant le
15/09). La case « Notaire du vendeur » est affichée sur l'onglet Offre, rien ne la range.

**Le mandant — Frédéric : « on l'a déjà normalement »** : oui. Les mandants sont ceux **du bien** (registre des liens : rubrique Contact,
« 7 mandants » sur VA6482 ; repli « Propriétaire du bien » du bloc Parties) et Hektor les **déduit du mandat** au compromis (mesure du
16/09 : 50084 revenu avec 3 mandants sans qu'on en envoie). Rien à ranger pour l'offre. *(La case « Mandant » de l'onglet Offre ne sert
donc à rien : la masquer reste à décider.)*

**Corrigé (commit 53bebff, front seul)** : à la **création**, la note, les conditions et la commission visent la **transaction neuve**
(numéro rendu dans la charge du travail) ; en modification, l'affaire visée. Build vert, essai hors ligne 19/19 (non touché).
⚠ Effet de bord connu : créer une 2ᵉ offre alors qu'une offre vit encore — la modale pré-remplit la note de l'ancienne ; si on envoie
sans l'effacer, la nouvelle en reçoit une copie (visible à l'écran avant l'envoi).

**Plan pour le notaire du vendeur de l'offre (A) — ⚠ ÉCRITURE EN BASE, accord requis** :
1. **base** : dans `app_change_annonce_status_optimistic` (empreinte f9d02447) et `app_modifier_affaire_optimistic` (0dac8c86), deux
   lignes de carnet **pour l'offre seulement** : `notaire_mandant_id` ← `seller_notary_id`, `notaire_mandant_nom` ← `seller_notary_nom`
   (en modification : seulement si les notaires sont **affirmés**). Patch gardé par empreinte, inverse et répétition, comme A5 ;
2. **worker** : `R3_NON_CONTROLES.offre` + ces deux champs (gardés chez nous, pas contrôlés — Hektor ne les porte pas) ;
3. **écran** : la modale d'une offre les reprend en modification ; **le compromis créé sur la même chaîne les reprend** (comme la
   commission — corrige F11 pour le notaire) ; la carte de l'offre affiche « Notaire vendeur ».
Ce que ça pourrait casser : rien chez Hektor (le worker envoie déjà ce champ avec l'offre) ; le compromis et la vente ne changent pas ;
le carnet garde ces lignes pour toujours (pas de colonne : règle de sortie du 16/09), ce qui est voulu.

## 28. PATCH N CODÉ (notaire du vendeur de l'offre) — 23/10, commit 103a0b4 — ⛔ PAS POSÉ

- **Base** : `supabase/patch_n_offre_notaire_vendeur_2026-10-23.sql` (+ `_INVERSE`, `_REPETITION`), générateur
  `phase2/checks/gen_patch_n_offre_notaire_vendeur.py`. Empreintes : création f9d02447 → **44697dd5**, modification 0dac8c86 →
  **43247de7**. Interrupteur `offre_notaire_vendeur`, posé **éteint**. **Répétition jouée : 7/7** (éteint → rien, le défaut ; allumé →
  id + nom au carnet ; sans notaire → rien ; les autres lignes du carnet identiques ; modification affirmée → les deux lignes ; non
  affirmée → rien ; l'inverse rend les deux empreintes). Vérifié après : empreintes d'origine, pas d'interrupteur, aucune affaire ni
  ligne de carnet restée, file vide.
- **Worker** : `R3_NON_CONTROLES.offre` + `notaire_mandant_id`, `notaire_mandant_nom` (essai R3 vert).
- **Écran** : clé `seller_notary_id` dans la liste du point E · la modale d'une offre relit le carnet · **le compromis créé sur la
  chaîne reprend le notaire du vendeur de l'offre** · la carte de l'offre montre « Notaire vendeur ».
- ⚠ **Trouvé en codant — la reprise de la commission de l'offre (lot 1c, 16/10) ne jouait JAMAIS à la création** : elle cherchait
  « l'affaire courante », qui n'existe pas encore quand on crée le compromis (c'est F11). Elle prend maintenant le dossier ouvert du
  bien (même règle que la répartition). ⚠ **Conséquence voulue par la décision du 16/10** : à la création du compromis, la commission
  vendeur saisie sur l'offre est pré-remplie, son drapeau levé, donc **elle part chez Hektor** avec le compromis.
- Essais : rubrique 21/21 (témoin inverse : la ligne « Notaire vendeur » échoue sur la version d'avant), build vert.
- **Pour activer** (accord de Frédéric) : poser le patch, allumer l'interrupteur, pousser, redémarrer les 4 services (file vide).
- ✅ **POSÉ EN PRODUCTION le 23/10 à 15:12 UTC, avec l'accord de Frédéric (« Oui »)** : 5 contrôles OK (empreintes 44697dd5 /
  43247de7, droits d'appel et SECURITY DEFINER inchangés, interrupteur créé éteint), puis **interrupteur `offre_notaire_vendeur`
  allumé à 15:12:25 UTC**. Retour arrière : `supabase/patch_n_offre_notaire_vendeur_2026-10-23_INVERSE.sql` ; suspendre : l'éteindre.
- ⏳ **Pas encore actif côté écran et worker** : il faut pousser et redémarrer les 4 services. D'ici là, la création d'une offre
  range déjà le notaire du vendeur (le front actuel l'envoie), la modification non (la clé `seller_notary_id` n'est pas encore
  envoyée), et R3 jugera ces lignes jusqu'au redémarrage (sans effet chez Hektor).

## 29. ESSAI 3, SUITE — 23/10, 17:15-17:35 (heure de Paris), avec 103a0b4 + patch N actifs

**Actif vérifié** : le paquet en ligne porte « Notaire vendeur », « attribués à personne », `seller_notary_id` ; 4 workers démarrés à
17:13:43-44 ; patch N posé et allumé.

**✅ Prouvé en réel**
- **Modification de l'offre 33114** : la modale se remplit — commission vendeur 6 500 (C6), charge acquéreur, répartition 30/20/25/25 ;
  notaire du vendeur désigné → **carnet `notaire_mandant_id` 10355906 / `notaire_mandant_nom` « Me. Eric PAILHES »** (origine
  modification_app, non jugé par R3) ; **la note est enregistrée — la PREMIÈRE note de toute la base**.
- **Offre acceptée** (`change_hektor_offre_status` done).
- **Compromis 50135 (1001388), même chaîne 1001384** : la modale reprend **le notaire du vendeur PAILHES** de l'offre (patch N),
  la commission 6 500, la charge, la répartition ; registre au clic : acte 01/03/2027, séquestre 5 000, net 103 500, rétractation
  14 j → fin 06/11/2026, notaire du vendeur 10355906, notaire acquéreur 10064499, 1 mandant ; **2 conditions enregistrées**
  (préemption 60 j, crédit 45 j) ; **note enregistrée** ; qualification : recherche 471886 créée ; « Hektor a gardé toutes les
  personnes envoyées ».

**⛔ Défauts trouvés**
1. **La commission vendeur n'est pas partie au compromis** (`seller_fees` absent de la charge → Hektor : 0,00) et **la charge n'a
   pas été écrite**. Cause : MON code du jour — la modale s'ouvre sur l'onglet Offre, qui affiche 6 500 ; sur Compromis, la case reste
   remplie SANS drapeau et la reprise s'arrête. **Corrigé, commit f00691e (écran seul, pas poussé)** : à la création seule une saisie
   bloque la reprise. Le même reste a montré « 0,00 » sur l'onglet Vente (tapé à la main pour l'essai).
2. **L'échéance des conditions s'affiche un jour trop tôt** (23/10 + 60 j → « 21/12 » au lieu du 22/12) : `echeanceCondition`
   passe par `toISOString()` (UTC) sur une date locale. Ancien (16/09). Non corrigé.
3. **Le prix de vente du compromis reste au prix du mandat** (128 787) à la création — F4, déjà noté ; corrigé à la main.
4. **Le worker sync_light s'est arrêté net à 17:24:40** (relancé par le service) et a laissé `refresh_console_contact_data` « running »
   sur 24113 : la vente (créée 17:26:50) attend la libération (~30 min). Défaut connu (0xC0000409, §2 de CLAUDE.md).

**⚠ MES DONNÉES D'ESSAI ÉTAIENT FAUSSES SUR LES HONORAIRES** (Frédéric : « une transaction a soit des honoraires à charge vendeur,
soit à charge acquéreur, jamais les deux ») : j'ai saisi 5 000 acquéreur **et** 6 500 vendeur, charge acquéreur. Le « conflit »
R3 sur le prix public du compromis (115 000 contre 110 000 = 115 000 − 5 000) en découle ; les résultats de commission de cet
essai ne comptent pas. ⚠ La modale accepte les deux à la fois : rien ne prévient — **à trancher par Frédéric**.

## 30. ESSAI 4 (PROPRE) — 23/10, 18:04-18:25 (Paris) — honoraires d'UN seul côté (charge acquéreur : 5 000 acquéreur, 0 vendeur)

Nettoyage d'abord (vente 23356, compromis 50135 supprimés ; offre 33114 refusée ; clôture locale retirée, sauvegarde
`app_mandat_champ_app_avant_essai4_va6482_20261023` ; diffusion remise à 0 par Pilotage, vérifiée chez Hektor). ⚠ f00691e **pas
encore poussé** pendant l'essai (sans effet ici : aucune commission vendeur à reprendre).

**✅ Prouvé en réel** — contact **20000014** (Hektor 605975, « mandant » seul) · offre **33115** / chaîne **1001390** : la **note
enregistrée À LA CRÉATION** (correctif 53bebff), le notaire du vendeur au carnet (patch N), charge, répartition 30/20/25/25 · offre
acceptée · compromis **50136** : notaire du vendeur **repris de l'offre**, **R3 : 0 conflit** (prix public 110 000 arrivé, rétractation 14
arrivée), net 110 000, acte, séquestre, mandant, 2 conditions, note, recherche de qualification 471887, « Hektor a gardé toutes les
personnes » · vente **23357** : notaires, net, charge, note · **répartition modifiée sur le compromis APRÈS la vente → rangée sous la
chaîne 1001390 (40/10/25/25), rien sous la vente** (C5) · **rubrique** : les trois cartes complètes (offre avec « Notaire vendeur »,
compromis avec acquéreur, mandant, conditions, note ; vente avec notaires dès le clic), « Parties à l'affaire » rempli sans la nuit
(acquéreur + coordonnées, mandant, notaire), bloc Répartition à jour après rechargement.

**⛔ Défauts trouvés**
1. ⛔⛔ **Modifier le compromis APRÈS la vente remet le bien « Sous compromis » chez Hektor** (statut 4) alors que la vente 23357 existe
   toujours, et la diffusion repasse à 1. « Modifier la transaction » renvoie le statut du genre visé. Avant aujourd'hui, personne ne
   modifiait un compromis après la vente ; c'est le geste demandé pour la répartition qui l'a révélé. **VA6482 est dans cet état.**
2. **La charge ne passe pas au compromis quand il n'y a pas de commission vendeur** : la reprise (lot 1c) s'arrête si l'offre n'a pas
   de `honoraires_entree_app`. Compromis : charge vide ; onglet Vente : « vendeur » par défaut (corrigé à la main).
3. **Le nom du notaire de l'acquéreur se perd** : l'offre ne garde que son numéro (`notaire_id`), le compromis le reprend sans nom →
   « Contact 10064499 » partout (c'est « Tiffany SELARL »).
4. **Les mandants de la vente cumulent les acquéreurs des essais** (9 noms) : Hektor ajoute l'acquéreur aux mandants à chaque vente,
   la suppression ne les retire pas (constat du 23/10, à nettoyer).
5. Rappel : l'échéance des conditions affichée un jour trop tôt.

## 31. DEUX AUDITS — les acquéreurs « mandants », et la piste A (le compromis après la vente) — 23/10, lecture seule

**Les acquéreurs qui s'accumulent en propriétaires — C'EST HEKTOR, et c'est voulu chez lui.**
- Mesure chez Hektor (`AnnonceById` → `proprietaires`) : VA6482 porte **10 propriétaires**, dont les **4 acquéreurs des essais**
  (605963, 605967, 605973, 605975), typologie « acquéreur, mandant ».
- **Contre-épreuve sur un vrai bien** : VM71227 (61483), vendu le 19/10 **directement dans Hektor** (aucun travail de l'app sur ce bien) :
  son acquéreur 604016 (HUGUES) est **aussi** devenu propriétaire. ⇒ **À la vente, Hektor inscrit l'acquéreur comme propriétaire du
  bien** (le nouveau propriétaire) ; supprimer la vente ne le retire pas.
- Aucun `link_hektor_mandant` de l'app sur 24113. ⇒ Pas un défaut de l'app : **un effet de nos 4 ventes d'essai sur le même bien**.
  Ma phrase « Hektor ajoute l'acquéreur aux mandants » était juste sur le fait, mais je l'avais présentée comme une anomalie.
- À nettoyer sur VA6482 : délier les 4 acquéreurs d'essai (geste chez Hektor → accord).

**La piste A (décidée par Frédéric) — ce que l'audit établit**
- Le worker pose le statut du genre visé à CHAQUE `change_hektor_annonce_status`, reprise comprise (`HEKTOR_STATUS_CONFIG.compromise`
  = statut 4 « Sous compromis », l. ~12438). Modifier le compromis d'une chaîne vendue remet donc le bien « Sous compromis ».
- Ce qu'on garde chez nous et qui doit rester modifiable après la vente : **répartition** (par chaîne), **conditions** et **note** (par
  transaction), **charge** (`charge_commission_app`). Les quatre ont déjà leur RPC (`app_repartition_commission_set` via
  `saveRepartition`, `app_conditions_affaire_ecrire`, `app_affaire_note_ecrire`, `app_affaire_commission_ecrire`) : **aucun travail
  Hektor n'est nécessaire**.
- **Plan A** : sur l'onglet Compromis, quand la chaîne visée porte une **vente vivante**, « Modifier la transaction » est remplacé par
  **« Enregistrer dans l'app »** (ces quatre écritures, aucun travail) avec un bandeau qui le dit. Écran seul.
- À trancher en même temps : « Annuler le compromis » / « Supprimer le compromis » après la vente (mêmes risques sur le statut) ; et
  « Modifier chez Hektor » sur l'onglet Vente (« une vente se choisit et se supprime »).

## 32. LA CHARGE ET LE NOM DU NOTAIRE DE L'ACQUÉREUR — audit du 23/10, lecture seule

**La charge** (`statusChangeChargeCommission`, App.tsx) : à l'ouverture de la modale, « vendeur », drapeau baissé (l. ~16640). Elle n'est
**enregistrée que si le drapeau est levé** (`statusChangeCommissionTouchee`) : par un choix dans la liste (l. ~20691), ou par la reprise
de l'offre (lot 1c, l. ~16459) — **mais cette reprise s'arrête si l'offre n'a pas de commission vendeur** (`if (!repris) return` AVANT la
charge). Conséquences mesurées à l'essai 4 : compromis 1001391 charge **vide** (la case montrait « acquéreur », reste de l'onglet Offre,
non enregistré) ; vente : « vendeur » par défaut, **et une fois « acquéreur » choisi, elle est bien enregistrée** (vente 1001392 :
`acquereur`). ⇒ Le choix marche ; c'est la REPRISE qui est liée à tort à la commission vendeur, et l'écran montre une valeur non gardée.

**Le nom du notaire de l'acquéreur** : la lecture de l'assistant de Hektor **a le nom** (compromis 1001391 et vente 1001392 :
« CORNU,. SELARL « Corine ROSTAING-MUSSIO, Tiffany CORNU… » ») **sous le numéro de HEKTOR 122190** ; notre registre et le carnet portent
**NOTRE numéro 10064499** (`app_contact_current` : 10064499 ↔ 122190). La carte cherche le nom par égalité de numéro → aucun → « Contact
10064499 ». En amont : l'offre ne garde que le numéro (carnet `notaire_id`), le compromis le reprend sans nom (reste de l'onglet Offre),
`buyer_notary_nom` part vide, R1 écrit un nom vide. C'est le même « une personne, deux numéros » que C4 pour les acquéreurs.

**Correctifs proposés (écran seul)** :
- 2 — la reprise de l'offre prend **la charge même sans commission vendeur** (création du compromis et de la vente, jamais par-dessus un choix).
- 3 — le nom d'un notaire connu par son numéro se lit **dans sa fiche contact** (par nos deux numéros) : dans la carte, et dans la modale
  quand le numéro arrive sans nom — il part alors avec le compromis et le registre le garde.

## 33. LES SÉCURITÉS QUI EXISTENT DÉJÀ — vérifiées dans le code le 23/10 *(Frédéric : « normalement il y a une sécurité… vérifie »)*

| sécurité | en place ? | où |
|---|---|---|
| **pas de 2ᵉ compromis tant qu'un compromis est en cours** (ni 2ᵉ vente) | ✅ **oui, deux fois** | écran : `avisGardeFouSaisie` (2.2c, 05/09 — « Il faut l'annuler avant d'en créer un autre ») ; worker : garde-fou du 31/08 (C1/C2/C3, interroge Hektor en direct) |
| **l'OFFRE ne se touche plus dès que son dossier porte un compromis vivant ou une vente** | ✅ **oui** | écran : `offreVerrouilleeParSonDossier` (16/09) cache Refuser/Accepter et dit « Pour y revenir, il faut d'abord supprimer la vente / annuler le compromis » ; **base** : la RPC `app_geste_affaire_optimistic` refuse (patch_offre_verrouillee_2026-09-16) — « l'écran n'est pas la serrure » |
| une offre acceptée ne se modifie plus | ✅ oui | `offreAccepteeFigeeChezHektor` (13/10) éteint « Modifier » |
| **le COMPROMIS ne se touche plus dès que son dossier porte une vente** | ⛔ **NON — ni à l'écran, ni en base** | « Modifier la transaction », « Annuler le compromis », « Supprimer le compromis » restent offerts. C'est le trou que l'essai 4 a révélé |

⇒ **La solution de Frédéric** : étendre au compromis le verrou de l'offre, avec la même phrase — *« On ne revient plus sur ce compromis :
son dossier porte une vente (n° …). Pour y revenir, il faut d'abord supprimer la vente. »* — à l'écran (cacher les trois boutons), et
dans la base comme pour l'offre (refus dans `app_modifier_affaire_optimistic` et `app_geste_affaire_optimistic` pour un compromis dont la
chaîne porte une vente vivante : patch, accord requis). Elle remplace la piste A pour les gestes Hektor.
⚠ **Reste à trancher** : après la vente, la répartition / les conditions / la note / la charge (à nous seuls) restent-elles modifiables
« dans l'app » sans toucher Hektor, ou faut-il, là aussi, supprimer la vente d'abord ?

## 34. V CODÉ (le compromis verrouillé par sa vente) + la charge + le nom du notaire — 23/10, commit local — ⛔ V PAS POSÉ

Décision de Frédéric : *« Non : après la vente tout est verrouillé ; pour modifier quoi que ce soit sur le compromis, il faut d'abord
supprimer la vente. »* (la piste A « Enregistrer dans l'app » est abandonnée).
- **Base** : `supabase/patch_v_compromis_verrouille_2026-10-23.sql` (+ `_INVERSE`, `_REPETITION`), générateur
  `phase2/checks/gen_patch_v_compromis_verrouille.py`. Gestes 20eeca7c → **a6569229**, modification 43247de7 → **910e7947**.
  Interrupteur `compromis_verrouille_par_vente`, posé éteint. **Répétition : 8/8** (éteint → accepté = le défaut ; allumé : modifier,
  annuler, supprimer le compromis → refusés « compromis_verrouille … supprimer la vente » ; modifier la vente → accepté ; le verrou de
  l'offre répond toujours ; une vente effacée chez Hektor ne verrouille plus ; l'inverse rend les deux empreintes). Vérifié après :
  rien n'est resté.
- **Écran** : `compromisVerrouilleParSaVente` ; bandeau « On ne revient plus sur ce compromis… Pour y revenir, il faut d'abord supprimer
  la vente » ; « Modifier la transaction », « Annuler / Supprimer le compromis » retirés tant que la vente existe.
- **Charge** : la reprise de l'offre pose la charge **même sans commission vendeur** (création du compromis et de la vente, jamais
  par-dessus un choix).
- **Nom du notaire** : `loadNomsContacts` (par nos DEUX numéros) — la carte (repli après le registre et la lecture de l'assistant) et
  la modale (quand le numéro arrive sans nom ; il part alors avec le compromis, R1 le garde).
- Essai rubrique **25/25** (témoin inverse : les 3 nouveaux échouent sur la version d'avant), build vert.
- ⚠ Non éprouvé hors ligne : la reprise de la charge et le nom dans la modale (effets du composant) — au prochain essai réel.
- **Pour activer** : poser V (accord), allumer l'interrupteur, pousser (écran seul : pas de redémarrage).
- ✅ **V POSÉ EN PRODUCTION le 23/10 à 16:54 UTC, avec l'accord de Frédéric** : 5 contrôles OK (empreintes a6569229 / 910e7947, droits et
  SECURITY DEFINER inchangés, interrupteur créé éteint), puis **interrupteur `compromis_verrouille_par_vente` allumé à 16:54:24 UTC**.
  Retour arrière : `supabase/patch_v_compromis_verrouille_2026-10-23_INVERSE.sql` ; suspendre : l'éteindre.
  ⚠ Le verrou en base est actif tout de suite ; l'écran (bandeau, boutons retirés) le sera après le push. D'ici là, un clic sur
  « Modifier / Annuler / Supprimer » un compromis vendu reçoit le refus de la base.

## 35. L'ACQUÉREUR DEVENU PROPRIÉTAIRE APRÈS UNE VENTE SUPPRIMÉE — et notre registre des liens — 23/10, lecture seule

*(Frédéric : « le registre des relations devrait se mettre à jour… sans la mise à jour de Hektor notre registre n'aurait pas bougé ;
il faut que la suppression de la vente annule la relation si c'est elle qui la crée »)*
- **Mesure** : `app_relation` de 24113 ne porte **aucun** des 4 acquéreurs d'essai (seul 603953 TESTCLAUDE, mandant depuis le 30/09,
  source `sync_annonce_contact_link`). Notre registre des liens se nourrit **la nuit**, de la liste des propriétaires de Hektor : il ne
  les a pas encore vus. ⇒ **Cette nuit, il les copierait** comme « propriétaire du bien », et ils y resteraient, puisque Hektor les garde.
- **L'app ne crée aucun lien à la vente** : c'est Hektor qui ajoute l'acquéreur aux propriétaires (contre-épreuve VM71227) ; le geste
  « Supprimer la vente » (`delete_hektor_vente`) ne fait que supprimer la vente.
- **Proposition** (worker, à décider) : après « Supprimer la vente », relire les propriétaires chez Hektor ; tout acquéreur de CETTE vente
  qui y figure **et qui n'était pas déjà lié au bien dans notre registre avant la date de la vente** est délié (même chemin que le geste
  « Délier » : `executerRetraitMandant`), au journal du travail. Un acquéreur déjà propriétaire avant la vente est gardé.
  Non couvert : une vente supprimée depuis l'écran de Hektor (aucun travail chez nous).
- **Tout de suite, au nettoyage** (accord) : délier les 4 acquéreurs d'essai de VA6482 **avant cette nuit**.

## 36. AUDIT DU REGISTRE DES LIENS (`app_relation`) — comment il réagit aux changements — 23/10, lecture seule

**Son autonomie** (relation_ledger.py, 30/09) : sa table, ses numéros (deux plages, celle de l'app ≥ 1 000 000), *delete-never*, le FAIT
« propriétaire du bien » (mandant / propriétaire n'en sont que deux libellés). **Les acquéreurs n'y sont PAS, par décision** : ils vivent
dans le registre des transactions. Mesure : **132 841 liens**, 132 793 présents chez Hektor, **48 sortis du miroir** (gardés), **2 retirés
par l'app**, **3 nés dans l'app** ; dernier passage de nuit 04:48 UTC.

| ce qui change | qui l'écrit | quand |
|---|---|---|
| lier un mandant depuis l'app | `app_link_mandant_optimistic` (patch « lien durable à la saisie ») | **au clic** |
| créer un mandant dans l'app | `app_create_mandant_contact_optimistic` | **au clic** |
| retirer un mandant depuis l'app | `app_unlink_mandant_optimistic` : `retire_le` au clic + travail « délier » chez Hektor | **au clic** |
| un lien apparaît chez Hektor | la nuit (`relation_ledger.py`, depuis les propriétaires de Hektor) : ligne ajoutée | **la nuit** |
| un lien disparaît chez Hektor | la nuit : `present_in_hektor = 0`, `absent_depuis` — **jamais supprimé** | **la nuit** |
| un lien retiré par l'app que Hektor montre encore | la nuit le revoit mais **garde le retrait** (`retire_le` appartient à l'app ; le serveur s'aligne sur le cloud) | — |

**Le cas de la vente** : Hektor inscrit l'acquéreur comme propriétaire → **cette nuit**, notre registre l'ajoutera comme « propriétaire du
bien » ; supprimer la vente ne le retire pas chez Hektor → notre registre le gardera. ⇒ **Sans geste de l'app, notre registre recopie
l'effet de Hektor** (crainte de Frédéric confirmée).

**La correction proposée** (worker, à décider) : à « Supprimer la vente », pour chaque acquéreur de CETTE vente **qui n'était pas déjà lié
au bien chez nous avant la vente**, prendre **le même chemin que « Retirer un mandant »** (`app_unlink_mandant_optimistic` : retrait au clic
chez nous + délier chez Hektor). La nuit respecte alors le retrait, même si Hektor tardait. Un acquéreur déjà propriétaire avant est gardé.
*(Option à trancher : à la CRÉATION de la vente, inscrire tout de suite l'acquéreur comme propriétaire chez nous, comme Hektor le fait —
pour que le registre soit juste avant la nuit.)*

## 37. « L'ACQUÉREUR RESTE ACQUÉREUR, LE PROPRIÉTAIRE RESTE LE MANDANT » — mesure sur tout le parc, 23/10

*(Frédéric : « c'est toi qui te trompes : l'acquéreur reste acquéreur pour toujours, jamais propriétaire ; le propriétaire reste le mandant »)*
- **Mesure (ventes du registre, acquéreur retrouvé dans `app_relation` du même bien)** : juin 2026 **3 sur 39** ; juillet **27/34** ; août
  **10/10** ; septembre **32/32** ; octobre **18/19**. Depuis juillet, **87 des 94 ventes** — **toutes faites directement dans Hektor**, aucune
  par l'app — ont leur acquéreur rangé chez nous comme **« mandant » du bien vendu** (source `sync_annonce_contact_link`, c.-à-d. la liste
  des propriétaires de l'annonce chez Hektor). Au total **133 liens « acquéreur = mandant »**, dont **115 encore actifs**.
- ⇒ **Ce n'est pas l'essai** (nos 4 acquéreurs ne sont que la même chose sur VA6482) : chez Hektor, depuis juillet, l'acquéreur se retrouve
  dans les propriétaires du bien après la vente, et **notre registre des liens le recopie la nuit comme mandant**. Selon la règle de
  Frédéric, **c'est faux chez nous**.
- **Mon erreur** : je l'ai présenté comme « normal, la règle de Hektor ». Le FAIT est mesuré ; l'avoir jugé acceptable pour notre registre
  était faux.
- **Conséquence à mesurer avant de corriger** : tout ce qui lit les mandants dans ce registre (rubrique Contact « Mandants / Propriétaires »,
  registre des mandats, reporting mandant, parties à l'affaire en repli) peut montrer l'acquéreur comme mandant.
- **Piste (à décider)** : à l'import de nuit, un contact qui est **l'acquéreur d'une vente du bien** n'est **jamais** rangé comme
  propriétaire/mandant de ce bien (sauf s'il l'était déjà avant la vente) ; rattrapage des 115 liens actifs, marqués et non supprimés
  (*delete-never*). Chez Hektor : ne rien toucher, ou délier — à décider.

## 38. AUDIT EN PROFONDEUR : depuis quand, et qui — « l'acquéreur rangé en propriétaire » — 23/10, lecture seule

*(Frédéric : « ce n'est pas possible, audite vraiment en profondeur, vérifie aussi Hektor depuis le début ou juste juillet »)*

**1. Chez Hektor, en direct** (`AnnonceById` → `proprietaires`, 40 ventes tirées au hasard, 8 par période) :

| période de la vente | acquéreur présent dans les propriétaires du bien chez Hektor |
|---|---|
| avant 2025 (2012-2023) | **0 / 8** |
| 2025 | **0 / 8** |
| 2026 janvier-mai | **1 / 8** |
| 2026 juin | **0 / 8** |
| 2026 juillet-octobre | **7 / 8** |

Quand il y est, sa typologie chez Hektor est « acquéreur, mandant ».

**2. La date de bascule** (toutes les ventes du 15/06 au 31/07, croisées avec notre registre des liens) : jusqu'au **10/07/2026** l'acquéreur
n'est presque jamais lié (2 exceptions, 30/06 et 02/07) ; **à partir du 17/07/2026, il l'est À CHAQUE VENTE** (25 sur 25 jusqu'au 31/07,
puis août 10/10, septembre 32/32, octobre 18/19).

**3. L'app n'y est pour rien** : aucun travail de l'app (ni vente, ni compromis, ni lien de mandant) sur les biens de l'échantillon
juillet-octobre ; les 87 ventes concernées depuis juillet ont été faites **directement dans Hektor**.

⇒ **C'est un changement côté Hektor, entre le 10 et le 17 juillet 2026** (nouvelle règle chez eux, ou nouvelle façon de saisir les ventes
chez GTI — la donnée ne permet pas de trancher) : depuis, l'acquéreur entre dans les propriétaires du bien vendu. Avant, jamais.
⇒ **Notre registre des liens le recopie chaque nuit** comme « mandant » : **133 liens** (115 actifs). Contraire à la règle de Frédéric
(« l'acquéreur reste acquéreur pour toujours ; le propriétaire reste le mandant »).
⇒ Nos 4 acquéreurs d'essai sur VA6482 : le même mécanisme, déclenché par nos 4 ventes d'essai.

**À faire, à décider par Frédéric** : (a) la règle d'import — l'acquéreur d'une vente n'est jamais rangé propriétaire/mandant de ce bien
(sauf s'il l'était avant la vente) ; (b) le rattrapage des liens déjà copiés (marqués, jamais supprimés) ; (c) chez Hektor : ne rien
toucher, ou délier ; (d) avant tout : mesurer qui lit ces liens (rubrique Contact, registre des mandats, reporting, parties).
- **« Le contact est-il acquéreur ET propriétaire ? »** (Frédéric) — mesure des ventes 2026 : **la typologie ne le dit pas**. Avant le
  17/07, **132 acquéreurs sur 170** portaient déjà « acquéreur, mandant » sur leur fiche **sans** être liés au bien vendu (la typologie est
  celle du CONTACT, tous biens confondus). Depuis le 17/07, sur 86 acquéreurs liés au bien vendu : 38 « acquéreur, mandant », **47
  « acquéreur » seul** dans notre copie des contacts (copie plus ancienne que le lien, ou typologie non mise à jour par Hektor : non
  mesuré). Chez Hektor en direct, les 7 liés de l'échantillon portent « acquéreur, mandant ». ⇒ Le fait qui compte est **le lien au bien**
  (liste des propriétaires), pas la typologie.

## 39. LES TYPES DE CONTACTS ET LES LIENS — Hektor, serveur, app : règles et données (synthèse du 23/10, lecture seule)

**1. Les 4 types de l'APP** (App.tsx ~37346, `contactDirectoryCategories`) — **calculés par nous**, non exclusifs, priorité
Mandant > Acheteur > Propriétaire > Acquéreur :

| type | règle de l'app |
|---|---|
| **Mandant** | lié à un bien **avec** numéro de mandat (rôle `mandant`) |
| **Propriétaire** | lié à un bien **sans** numéro de mandat (rôle `proprietaire`) |
| **Acheteur** | lié à un bien par une **transaction** (rôles `acquereur_offre` / `_compromis` / `_vente`) |
| **Acquéreur** | a une **recherche active** (prospect), indépendamment des biens |

**2. Ce que HEKTOR connaît** — deux choses différentes :
- la **typologie du CONTACT** (globale, tous biens) : « acquéreur », « mandant », « partenaire »… → **récupérée** (`typologies_json`),
  mais **les 4 types de l'app ne l'utilisent pas**. Elle sert seulement : aux badges de la fiche, à la **qualification de l'acquéreur**
  avant un compromis / une vente (worker `estQualifieAcquereur`, avertissement de la modale), à deviner la nature (partenaire, locataire)
  pour modifier une fiche.
- les **LIENS au BIEN** : la liste des **propriétaires de l'annonce** (UN seul fait) et les listes d'offres / compromis / ventes (avec
  l'acquéreur). Hektor n'a pas de lien « mandant » : c'est **notre build** qui rebaptise le propriétaire en « mandant » quand l'annonce
  porte un numéro de mandat (`build_contacts_layer.py` l. ~1395).

**3. Ce que fait le SERVEUR (la nuit)** : `build_contacts_layer.py` refait `app_contact_relation_current` depuis 6 sources —
propriétaires de l'annonce (`sync_annonce_contact_link`) → mandant / propriétaire ; listes d'offres, compromis, ventes → acheteur ;
+ `api_contact_detail_annonces`, `api_annonce_detail_proprietaires` ; puis `relation_roles_json` par contact → **les 4 types de l'app**.
`relation_ledger.py` tient à part le registre durable `app_relation` (le fait « propriétaire du bien » seulement).

**4. Les données** (`app_contact_relation_current`) : propriétaire 25 975 + 76 · mandant 24 201 + 107 · acheteur offre 11 164 ·
compromis 13 267 · vente 10 539.

**5. Le défaut, chiffré** : un acheteur qui a AUSSI un rôle propriétaire/mandant sur **le bien qu'il a acheté** :
**91 pour les ventes depuis le 17/07** (89 « mandant »), **14 en 2026 avant le 17/07**, **13 avant 2026**. Depuis le 17/07, c'est Hektor qui
l'inscrit propriétaire (§38) ; notre build le range « mandant » (le bien a le numéro de mandat du VENDEUR) ; **dans l'app, son type dominant
devient « Mandant »** au lieu d'« Acheteur ». Contraire à la règle de Frédéric.
⚠ Les cas anciens ne sont pas forcément faux : un acheteur qui **revend plus tard le même bien** sous un nouveau mandat EST mandant. La
règle doit donc porter sur le moment (lien apparu après la vente, sur le mandat du vendeur), pas sur « acheteur ⇒ jamais mandant ».

**6. Le push en attente** (rubrique Affaires, verrou V à l'écran, note, conditions, charge, notaire) **ne touche ni les liens ni les types**.

## 40. ESSAI 5 — le chantier en entier, APRÈS le push (N + V + écran) — 23/10, 19:28-19:45 (Paris)

Nettoyage d'abord (§ fin de l'essai 4 : vente 23357 et compromis 50136 supprimés, offre 33115 refusée, clôture locale retirée avec
sauvegarde `app_mandat_champ_app_avant_essai5_va6482_20261023`, diffusion remise à 0). Contact **20000015** (Hektor **605976**).
Données d'essai **justes cette fois** : honoraires d'UN seul côté — **5 000 acquéreur, 0 vendeur, charge acquéreur**.
⭐ **La charge n'a été touchée NI au compromis NI à la vente** : c'est ce que l'essai devait prouver.

| étape | Hektor | ce qui est arrivé chez nous |
|---|---|---|
| offre | **33116** (115 000, honoraire acquéreur 5 000, notaire 122190) | chaîne **1001393** · charge `acquereur` · honoraires 5 000 / 4,35 % · carnet : `notaire_id` 10064499, **`notaire_mandant_id` 10355906 + nom « Me. Eric PAILHES »** (patch N) · répartition **30/20/25/25** (4 lignes sous la chaîne) · **note enregistrée à la création** |
| acceptée | `change_hektor_offre_status` done en 6 s | registre `accepted` |
| compromis | **50137** | **la modale reprend la charge `acquereur` sans geste** (correctif de la charge) · notaire du vendeur **repris de l'offre** · nom du notaire de l'acquéreur **retrouvé** (« Tiffany SELARL… », plus de « Contact 10064499 ») · net 110 000 · acte 15/12/2026 · condition « Préemption mairie » · note · même chaîne |
| vente | **23358** | **charge `acquereur` reprise sans geste** · prix 115 000, net 110 000, honoraires 5 000 · les deux notaires avec leur nom · note · même chaîne, 4 lignes de répartition |

**Contrôles**
- **10 travaux depuis 17:30 UTC, tous `done`, 0 erreur.** Pas d'arrêt du worker cette fois.
- **R3 : 0 conflit** sur la chaîne — chaque ligne du carnet est `arrivee`, `sans_objet`, `en_attente` ou non contrôlée (les 5 champs
  gardés de l'offre).
- **Rubrique Affaires** (après rechargement) : « 7 dossiers », la chaîne 1001393 avec ses **trois transactions**. Carte offre complète
  (notaire acquéreur ET vendeur nommés, charge, note) ; carte compromis complète (prix, net, acte, rétractation, notaires, charge,
  condition, note) ; carte vente (notaires nommés, note) ; **bloc Répartition 30/20/25/25** « gardée dans l'app ».
- **Verrou V à l'écran, sur la vraie vente** : onglet Compromis → bandeau « On ne revient plus sur ce compromis. Son dossier porte une
  vente (n° 23358)… il faut d'abord supprimer la vente. » ; **Modifier / Annuler / Supprimer ont disparu**. Modale fermée sans rien
  envoyer.

**⚠ Ce que l'essai a vu, et qui n'est pas corrigé**
1. **La rubrique ne montre pas une chaîne NÉE pendant la session tant que la page n'est pas rechargée** : ouverte après la vente sans
   recharger, elle disait « 6 dossiers » (les 6 offres refusées) ; après rechargement, « 7 dossiers ». Les gestes sur une chaîne qui
   EXISTAIT (essai 4) s'affichaient, eux, tout de suite. **Constaté, pas diagnostiqué.**
2. **La diffusion est repassée à 1 chez Hektor** (`diffusable = 1`, statut Vendu) alors que le nettoyage l'avait remise à 0. Même famille
   que le défaut déjà noté (« une vente supprimée remet la diffusion à 1 ») : ici la CRÉATION aussi. ⛔ La remettre à 0 = écriture chez
   Hektor → **accord de Frédéric**.
3. **Le 5e acheteur d'essai est inscrit propriétaire chez Hektor** (605976, 11 propriétaires sur VA6482) et apparaît dans
   « MANDANT(S) » des cartes compromis et vente → c'est le problème des types (§37-39), **reporté après ⑧ par Frédéric**.
4. Rappels déjà notés : l'échéance d'une condition affichée **un jour trop tôt** (« échéance 22/10 » pour 0 jour un 23/10) ;
   « Envoyer vers Compromis » encore proposé sur une chaîne vendue (la base refuse un 2e compromis) ; les libellés de la modale du
   compromis prêtent à confusion (« Montant / prix public » → prix de vente 115 000 ; « Prix de vente » → `prix_publique` 110 000 — les
   valeurs sont justes, R3 les dit arrivées).

**Bilan** : les trois défauts de l'essai 4 (charge, nom du notaire, compromis modifiable après la vente) sont **corrigés et prouvés en
réel**, avec le notaire du vendeur gardé sur l'offre (N). ➡ **Le chantier du registre (⑧) est fini côté transactions**, sous réserve de
la preuve de nuit sur la chaîne 1001393. Suite décidée par Frédéric : **le problème des types de contacts** (§37-39).

**Diffusion remise à 0 (23/10, ~19:55, accord de Frédéric : « fais-le »)** — vérifié par l'API Hektor : `diffusable = 0`, statut Vendu.
⚠ **Le bouton de l'app ne marche pas sur un bien VENDU** : Pilotage → Diffusion → « Désactiver » est cliquable, mais **aucune requête
ne part et aucun message ne s'affiche** (`handleSetSelectedDossierDiffusable`, App.tsx ~18758, sort sans rien dire quand
`selectedDossier` est vide — un bien vendu n'est plus dans `app_dossier_current`). Un **échec silencieux** (famille du chantier ④).
Fait donc par la fiche Hektor (icône « Diffuser ou non ce bien »). Notre fiche reprendra la valeur à la nuit.
Au passage, l'en-tête Hektor de VA6482 dit « Propriétaire : M. ESSAI 8 CINQ » : Hektor tient l'acheteur pour LE propriétaire (§37-39).

## 41. UN BIEN VENDU NE PREND PLUS DE NOUVELLE TRANSACTION — 23/10 *(Frédéric : « oui, code avant R2 »)* — écran seulement, **pas poussé**

**Le défaut** (vu à l'essai 5) : sur VA6482 vendu, la modale offrait encore « Envoyer vers Compromis » (et Offre, Vendu). Ce bouton
**crée** une affaire dans un dossier neuf. La garde 2.2c (`avisGardeFouSaisie`) ne compte que les dossiers **ouverts** ; un dossier clos
par sa vente « ne bloque pas » — voulu pour une **revente sous un nouveau mandat**. La base refuse hors du parc vivant
(`app_change_annonce_status_optimistic` : `transaction_hors_parc_vivant`), mais **seulement une fois le bien relu** ; et l'écran
affichait ce code **brut** (aucune traduction dans le front).

**Le correctif** (`bienVenduPourStatut`, à côté de `compromisVerrouilleParSaVente`) — deux preuves, l'une suffit :
- **A** le registre porte une vente **confirmée** par Hektor (numéro, pas effacée) **sous le mandat courant** — couvre la minute d'avant la relecture ;
- **B** le statut du bien dit « Vendu ».
Alors, sur les onglets Offre / Compromis / Vendu : **bandeau** « Ce bien est vendu (vente n° …). … il faut d'abord supprimer la vente »,
le bouton « Envoyer vers » **disparaît**, et le geste lui-même refuse (la touche Entrée soumet aussi le formulaire). « Modifier »,
« Supprimer la vente », « Actif » et « Clos » **ne sont pas touchés**. Le refus de la base est **traduit** (`throwConsoleAdminJobError`, api.ts).

**Ce que ça pourrait casser ailleurs** : la **revente** (nouveau mandat, autre numéro, statut actif) garde ses boutons — contrôlé ;
une vente **sans numéro Hektor** (travail échoué) ou **effacée** ne ferme rien — contrôlé. ⚠ Juste après une **suppression** de vente,
tant que la fiche n'est pas relue, le statut peut encore dire « Vendu » : le bouton reste caché une minute (sans danger, rien ne part).

**Contrôles** : `test_rubrique_affaires_complete.cjs` **31/31** (6 neufs) · témoin inverse : les 6 neufs **échouent** sur la version
d'avant · **3 mutants attrapés** (sans le numéro Hektor, sans le même mandat, effacée comptée) · `npm run build` vert · `\r\r\n` = 0.
✅ **VU À L'ÉCRAN le 24/10** (poussé `812e7af`, bundle `index-6wMBhZVs.js` vérifié servi par Vercel ; accord de Frédéric pour
recharger l'onglet), modale de VA6482 ouverte onglet par onglet, **rien envoyé** (0 travail sur 24113) :

| onglet | bandeau « Ce bien est vendu (vente n° 23358) » | boutons du bas |
|---|---|---|
| Actif | non | Annuler · Envoyer vers Actif *(inchangé)* |
| Offre | oui | Annuler · Modifier la transaction *(grisé : l'offre est verrouillée par sa chaîne, 16/09)* |
| Compromis | oui, **et** le bandeau V | **Annuler seul** |
| Vendu | oui | Annuler · Modifier la transaction · Supprimer la vente |
| Clos | non | Annuler · Envoyer vers Clos *(inchangé)* |

⚠ Vu au passage, non corrigé : sur l'onglet Compromis, l'ancien message 2.2c « Ce bien porte déjà un compromis. **Modifier la
transaction** reprend celle-là… » s'affiche encore, alors que ce bouton est retiré par V — il contredit les deux bandeaux.
⚠ Rappel : la vente garde « Modifier la transaction » ; Frédéric avait dit « une vente peut juste être choisie et supprimée »
(§23.1) — **à trancher par lui**, non touché.

## 42. LES BOUTONS DE LA MODALE, ÉTAT PAR ÉTAT — audit du 24/10 *(Frédéric : « les boutons doivent être visibles ou non en fonction de l'état de la transaction ; fais-moi un récapitulatif »)* — lecture seule

**Source** : le code (`App.tsx` ~21524-21609, `affaireCourantePourStatut`, `offreVerrouilleeParSonDossier`, `offreAccepteeFigeeChezHektor`,
`compromisVerrouilleParSaVente`, `bienVenduPourStatut`, `avisGardeFouSaisie`, `bienEngage`) et les refus de la base
(`app_geste_affaire_optimistic`, `app_modifier_affaire_optimistic`, `app_change_annonce_status_optimistic`). ⚠ **Lu, pas cliqué** :
seul l'état « vendu » a été vu à l'écran (§41).

**Quelle transaction les boutons visent** : celle que l'utilisateur a « Choisie », sinon la seule VIVANTE du genre (une refusée ou une
annulée n'est jamais visée d'office ; s'il y en a deux vivantes, aucune → pas de bouton tant qu'on n'a pas choisi). « Choisir » une offre
refusée n'est possible que si le bien n'est pas engagé (pas de compromis ouvert, pas d'offre acceptée).

### Onglet OFFRE
| état | Refuser | Accepter | Modifier | Envoyer vers Offre (crée) |
|---|---|---|---|---|
| aucune offre vivante | — | — | — | ✅ |
| offre **en cours** | ✅ | ✅ | ✅ | ✅ *(une 2ᵉ offre)* |
| offre **acceptée**, pas de compromis | ✅ | ✅ ⚠ | 🔘 grisé *(figée chez Hektor, 13/10)* | ✅ ⚠ |
| offre **refusée**, choisie (bien libre) | ✅ ⚠ | ✅ *(voulu, 08/09)* | ✅ | ✅ |
| offre dont le dossier a un **compromis** ou une **vente** | — *(verrou 16/09, base aussi)* | — | 🔘 grisé si acceptée | ✅ ⚠ (— si vendu, §41) |

### Onglet COMPROMIS
| état | Modifier | Annuler le compromis | Supprimer le compromis | Envoyer vers Compromis (crée) |
|---|---|---|---|---|
| aucun compromis | — | — | — | ✅ |
| compromis **en cours** | ✅ | ✅ | ✅ (rouge) | 🔘 grisé *(2.2c : « déjà un compromis en cours »)* |
| compromis **annulé** | — | — | — | ✅ *(son dossier est clos)* |
| compromis + **vente** | — *(V, base aussi)* | — | — | — *(§41)* |

### Onglet VENDU
| état | Modifier | Supprimer la vente | Envoyer vers Vendu (crée) |
|---|---|---|---|
| pas de vente | — | — | ✅ |
| vente **enregistrée** | ✅ ⚠ | ✅ (rouge) | — *(§41)* |
| vente **supprimée** chez Hektor | — | — | ✅ |

### Onglets ACTIF et CLOS
Toujours « Envoyer vers Actif » / « Envoyer vers Clos », **quel que soit l'état** — y compris sur un bien vendu (la base l'accepte
exprès hors du parc vivant : `target_status in ('active','closed')`).

### ⚠ Les incohérences trouvées — rien n'est corrigé, **à trancher par Frédéric**
1. **« Accepter » sur une offre déjà acceptée**, **« Refuser » sur une offre déjà refusée** : affichés, et la base ne les refuse pas
   (elle ne regarde que le genre, pas l'état). Un geste qui ne change rien, et qui part chez Hektor.
2. **« Envoyer vers Offre » sur un bien ENGAGÉ** (offre acceptée ou compromis en cours) : affiché et actif. La garde 2.2c ne couvre
   que compromis et vente (`if (genre === 'offre') return null`). Contraire à la règle écrite au 08/09 : « il peut y avoir plusieurs
   offres, mais plus possible quand compromis ouvert ou offre acceptée » — appliquée aujourd'hui au seul « Choisir ».
3. **« Modifier » sur une vente** : affiché ; Frédéric avait dit « une vente peut juste être choisie et supprimée » (§23.1).
4. **« Envoyer vers Actif » / « Clos » sur un bien VENDU** : affichés. « Actif » remettrait le bien en vente chez Hektor (et la
   diffusion à 1 — mémoire « le geste Actif remet diffusable = 1 »).
5. **Le vieux message 2.2c** de l'onglet Compromis (« Modifier la transaction reprend celle-là… ») s'affiche encore quand V a retiré
   ce bouton (§41).
6. Rappel : le bouton **Pilotage → Diffusion** est muet sur un bien vendu (§40).

## 43. PEUT-ON MODIFIER UNE OFFRE EN COURS ? UNE VENTE ? — l'histoire, 24/10 *(Frédéric : « je crois qu'on peut dire refused ou accepted, c'est tout ; une vente ne peut pas être modifiée, non ? vérifie »)* — lecture seule

**Ce que le projet a décidé et prouvé**
- **07/09, arbitrage de Frédéric** (LISTE l. ~6422) : *« il faut pouvoir modifier des offres refused dans le cas où l'on veut la passer
  en valide et si possible changer le montant et l'état, idem un compromis peut être débloqué en cas d'erreur »* → `TRANSACTIONS_REPRISES`
  n'exclut **aucun état** (worker l. 12404).
- **08/09, tâche 3.2b, cochée le 10/09** : les **trois genres** se modifient, prouvés en réel sur 24933 — offre **33050** (en cours)
  165 000 → 167 000 ; compromis 50078 ×4 ; **vente 23301** 175 000 → 176 500, une seule vente, puis supprimée.
- **13/10** (`MESURE_MODIFIER_OFFRE_ACCEPTEE_2026-10-13.md`) : Hektor **refuse** d'ouvrir une offre **acceptée** (200 + 0 octet, 9/9) ;
  une offre **en cours** ou **refusée** s'ouvre (3/3). Depuis, « Modifier » est **grisé** sur une offre acceptée.
- **29/08, plan C.19-c** (PLAN l. ~2237) : *« modifier une vente sur une annonce ARCHIVÉE → DANGER : désarchiver la détruit »* ; et
  *« aucun de nos workers ne doit "modifier" une vente par ce chemin tant que ce n'est pas éclairci ; si l'app doit un jour corriger une
  vente, elle le fera chez nous »*. **3.2b l'a ouvert quand même le 08/09**, sur une annonce active. Mesure du 24/10 : les 8 819 biens
  vendus de notre index sont **archive = 0** — le cas dangereux est un vendu archivé ensuite.
- **23/10** : *« une vente peut juste être choisie et supprimée »* (§23.1) ; la répétition de V garde « modifier la vente → accepté ».

**L'usage réel** (`app_console_job`, reprises) : **aucune** modification d'offre en cours ni de vente hors des biens d'essai
(24933, 24113) ; **une seule** tentative sur un vrai bien — l'offre **acceptée** 33094 (61672), échouée le 13/10.

➡ **Ce qui est écrit contredit le souvenir de Frédéric** : l'offre en cours et la vente sont modifiables **par sa décision du 07/09**,
et la vente contre l'avertissement du 29/08. **Rien n'est changé** : retirer « Modifier » de l'offre en cours et/ou de la vente est
une **décision de Frédéric**.

**⛔ DÉCISION DE FRÉDÉRIC (24/10) : « on ne touche pas ».** « Modifier » reste sur l'offre en cours et sur la vente, comme décidé le 07/09. Ne pas relancer.

## 44. LA NUIT DU 24/10 SUR LA CHAÎNE DE L'ESSAI 5 (1001393) — lecture seule

Relue à 04:52 UTC. **Tient** : la même chaîne pour les trois, offre `accepted`, charge `acquereur` sur les trois, honoraires 5 000,
notaires nommés (compromis et vente), notes (3), condition du compromis, répartition 30/20/25/25, `present_in_hektor` partout.
**A bougé** : le compromis passe `en_cours` → `active` (le mot de Hektor) ; ⚠ **la vente perd `prix_net_vendeur`** au registre
(110 000 → vide) — Hektor ne le porte pas sur une vente ; le carnet le garde (verdict `sans_objet`). C'est exactement le terrain de
**R2** (la nuit remplace la ligne du registre). Non corrigé.

## 45. PLUSIEURS AFFAIRES SUR UNE ANNONCE, ET MON CORRECTIF DU 23/10 (§41) — audit du 24/10 *(Frédéric : « une annonce pouvait avoir plusieurs affaires du moment où la chaîne était close… il faudrait plutôt dire : pas de transaction pour les biens en état Vendu, Clos ou Estimation ; si l'état revient à Actif, possibilité de refaire une nouvelle chaîne… audite d'abord mon projet dans sa globalité »)* — lecture seule

### L'histoire, datée
| date | quoi | où |
|---|---|---|
| 30/07 | « Vendu » clôt aussi le mandat courant (`close_mandat_on_sale`) ; réactiver un mandat clos passe par « Actif » | `a206938` |
| 31/07 | le dossier suit le **cycle de mandat courant** : une transaction d'un ancien mandat (autre **numéro**) n'est plus rangée sous le nouveau | `ea8b90a` |
| 02-03/09 | seule la **création** d'une transaction déplace le statut du bien chez Hektor ; la vente le passe à « Vendu » ; le compromis reste `active` après la vente | `901995c` `1108752` `9cf217d` |
| 03/09 | le **dossier d'affaire** (`app_chaine_id`), un numéro par chaîne, frappé par Supabase | `aedd681` |
| 04/09 | **la règle de Frédéric** : « une chaîne c'est trois blocs, ou deux, ou un seul ; un compromis est clos quand il est annulé ou quand la vente est passée » → chaînage par la SÉQUENCE | `1db53f2` |
| 04-05/09 | **2.2c** : on bloque une 2ᵉ vente, un 2ᵉ compromis vivant ; ⚠ **objection de Frédéric** : « gérer le cas d'une chaîne d'un ANCIEN mandat sur la même annonce » → on compte les **dossiers OUVERTS**, pas les transactions. Mesure : **8 biens vendus autrefois revenus en Estimation** | `156489f` `cbea46d` |
| 08/09 | une vente ferme **toujours** sa chaîne | `858a34c` |
| 16/09 | 2.7 : le numéro de mandat d'une transaction se **déduit** la nuit (cascade : Hektor l'a dit → l'annonce n'a qu'un mandat → la période → le mandant) | `affaire_ledger.py:466` |
| 23/10 | §41 : mon `bienVenduPourStatut` | `37c0682` |

### Les trois étages qui décident aujourd'hui
1. **La base** (`app_change_annonce_status_optimistic`) : sur le **parc vivant** (`app_dossier_current` = archive 0 et statut ∈ Actif,
   Sous offre, Sous compromis, **Estimation** — plan l. 1689) → tout est permis ; sur l'**historique** (Vendu, Clos non archivés) →
   seulement Actif / Clos (`transaction_hors_parc_vivant`) ; sur l'**archive** → rien (`annonce_archivee_lecture_seule`).
2. **L'écran, 2.2c** (`avisGardeFouSaisie` + `dossiersOuvertsDuBien`) : un **dossier ouvert** qui porte déjà un compromis (ou une vente)
   éteint « Envoyer vers » ; un dossier **clos** (vente passée, compromis annulé, offres toutes refusées) **ne bloque pas** → c'est ce qui
   permet une **nouvelle chaîne** sur la même annonce.
3. **Mon correctif §41** : **A** une vente confirmée **sous le même numéro de mandat** que le bien, **ou B** le statut « Vendu ».

### Mesure du 24/10
| parc | statuts |
|---|---|
| vivant | Estimation **12 781** · Actif 592 · Sous compromis 90 · Sous offre 44 |
| historique | Vendu 8 819 · Clos 136 |
| archive | Clos 34 788 · Vendu 425 · Actif 91 · Estimation 31 |

⚠ **Ma preuve A bloque 8 biens VIVANTS** — tous en **Estimation**, et ce sont **les 8 de l'objection du 05/09** : vendus entre 2016
et 2021 (EM16784, EM19904, EM29852, EA14544, EM33490, EM41252, EM42200, EM42964), revenus en Estimation **sous le même numéro de
mandat** que leur ancienne vente (numéro donné par Hektor). Aucun bien Actif / Sous offre / Sous compromis n'est touché aujourd'hui.

### Verdict
- **Frédéric a raison : A casse le mécanisme des chaînes successives.** Elle regarde l'HISTOIRE (une vente sous ce numéro) au lieu
  de l'ÉTAT du bien. Si l'un de ces 8 biens redevient **Actif sans nouveau numéro** de mandat, A l'empêcherait de recevoir une offre
  — exactement l'erreur que le 05/09 avait évitée en comptant les dossiers ouverts. Le risque dépend d'un numéro de mandat (donné par Hektor
  pour 48 % des lignes, DÉDUIT la nuit pour ~27 % — mesure du 16/09 ; Hektor recycle ses identifiants de mandat) : une base fragile pour un verrou.
- **B** (statut « Vendu ») est dans la logique de Frédéric ; il manque **Clos** et **Estimation**.
- **⚠ Estimation n'est refusé NULLE PART aujourd'hui** : ni par l'écran, ni par la base (le parc vivant l'inclut). Aucune décision
  écrite trouvée sur une transaction sur une estimation.

### Correctif proposé — NON CODÉ, en attente du « vas-y »
- **Écran** : remplacer A + B par **l'état du bien seul** — « Envoyer vers Offre / Compromis / Vendu » caché si le statut est **Vendu,
  Clos ou Estimation** ; présent sur Actif, Sous offre, Sous compromis. 2.2c (les dossiers ouverts), le verrou de l'offre et V ne bougent
  pas. Modifier / Supprimer / Actif / Clos inchangés.
- **Base** (accord requis) : refuser aussi la création sur un bien en **Estimation** — aujourd'hui elle passe.
- **Ce qu'on perd** : la minute après une vente, la fiche peut encore dire « Sous compromis ». Le travail de vente en cours bloque déjà
  toute autre action sur l'annonce, puis la relecture la sort du parc vivant et la base refuse. Reste une fenêtre courte, non mesurée.

## 46. L'ÉTAT DU BIEN FERME LES TRANSACTIONS — écran codé, patch de base PRÉPARÉ — 24/10 *(Frédéric : « les deux si c'est nécessaire »)* — **pas poussé, pas posé**

**Écran** (`etatFermeAuxTransactions`, remplace `bienVenduPourStatut` du §41) : « Envoyer vers Offre / Compromis / Vendu » est caché,
avec un bandeau, quand le statut du bien est **Vendu, Clos ou Estimation** ; il reste sur Actif, Sous offre, Sous compromis, où la
garde 2.2c (les dossiers ouverts) continue de décider. **L'histoire du bien n'est plus regardée** (fin de la preuve A). Bandeau :
Vendu → « supprimer d'abord la vente » ; Clos / Estimation → « passez d'abord le bien en Actif ». Le geste refuse aussi (touche Entrée),
et le refus de la base `transaction_sur_estimation` est traduit (api.ts). Modifier, Supprimer, Actif, Clos : inchangés.
- Essais : `test_rubrique_affaires_complete.cjs` **29/29** (4 neufs) · témoin : **l'ancienne règle (HEAD) bloquait EM16784 repassé
  Actif sous le même mandat** (« BLOQUE par la vente 2417 »), la nouvelle le laisse libre · **2 mutants attrapés** (sans Estimation,
  sans Clos) · `npm run build` vert · `\r\r\n` = 0.

**Base** — `supabase/patch_transaction_sur_estimation_2026-10-24.sql` (+ `_INVERSE`, `_REPETITION`), générateur
`phase2/checks/gen_patch_transaction_sur_estimation.py`. `app_change_annonce_status_optimistic` **44697dd5 → 93be71b4**, une ancre
(`-- @repli-fin`), interrupteur `transaction_refusee_sur_estimation` posé **éteint**. Allumé : créer une offre, un compromis ou une vente
sur une Estimation → `transaction_sur_estimation` ; « Actif » et « Clos » passent ; Actif / Sous offre / Sous compromis inchangés ;
la modification (autre fonction) n'est pas touchée.
- **Répétition : 7/7** (T1 éteint → accepté = le défaut ; T2-T4 allumé → offre, compromis, vente refusés ; T5 « Actif » accepté ; T6 une
  offre sur un bien Actif acceptée ; T7 l'inverse rend 44697dd5). Vérifié après : empreinte 44697dd5, pas d'interrupteur, 63331 toujours
  en Estimation, 0 ligne au registre, 0 travail.
- ⚠ **La 1ʳᵉ répétition a dit 4/7, et c'était la répétition, pas le patch** : la création est **optimiste** — elle passe aussitôt le
  bien « Sous offre » chez nous (mesuré : Estimation → Sous offre). Après T1, T2-T4 ne visaient plus une estimation. Corrigé en remettant
  le bien en Estimation avant chaque appel. ⭐ C'est aussi la preuve du défaut : une offre sur une estimation **change son statut**.
- ⚠ La répétition jouée est la logique du fichier, avec des messages d'arrêt raccourcis pour l'envoi.

**Ce que ça pourrait casser ailleurs** : un négociateur qui enregistrait une offre sur un bien encore en Estimation (sans l'avoir passé
Actif) devra d'abord le passer Actif — c'est la règle voulue. Les 8 biens vendus revenus en Estimation : fermés tant qu'ils sont en
Estimation, ouverts dès qu'ils repassent Actif, quel que soit leur numéro de mandat.

**Pour activer** : (1) Frédéric pousse (l'écran part avec Vercel) ; (2) poser le patch (accord) ; (3) allumer l'interrupteur (accord).

## 47. CE QUE LA NUIT A EFFACÉ — toutes les transactions nées dans l'app, 24/10 *(Frédéric : « ce champ ne doit pas attendre un retour de Hektor, on le fait pour d'autres ; est-ce le seul disparu ? »)* — lecture seule

**Mesure** : chaque ligne du carnet (valeur saisie) comparée à sa colonne du registre, sur les 339 transactions nées dans l'app.
Une seule chaîne a des trous, 1001393 (essai 5, née la veille) :
| transaction | champ | carnet | registre | compte ? |
|---|---|---|---|---|
| vente 23358 | **prix net vendeur** | 110 000 | **vide** | ⚠ **oui** — Hektor ne le porte jamais sur une vente (0 sur 9 266 ; 10 601 sur 10 616 compromis l'ont) |
| vente 23358 | date d'acte | 15/12/2026 | vide | non — reprise du compromis ; la vente a sa date de vente, et le compromis garde l'acte |
| vente 23358, compromis 50137 | validité | 15 | vide | non — la validité ne concerne que l'offre (reprise de l'onglet Offre) |
Rien d'autre n'est perdu. Ont **changé** sans se perdre : les numéros des notaires (ceux de Hektor, 122190 / 605227, au lieu des nôtres),
leurs noms réécrits par Hektor, la date de l'offre (avec l'heure), l'état du compromis (`en_cours` → `active`) ; et `first_seen_at`
des 3 lignes, posé au clic (17:33), réécrit à la première nuit (04:52) — un horodatage, pas une saisie.

**Ce que le projet fait déjà pour les champs qui n'attendent pas Hektor** : colonnes `_app` que la nuit ne touche pas (la charge,
les honoraires saisis — d'où la charge intacte) ; `R3_NON_CONTROLES` (5 champs de l'offre gardés au carnet) ; la règle de sortie
du carnet (une ligne reste tant que le registre ne porte pas la même valeur) ; nos tables (répartition, conditions, notes).
➡ Le net de la vente **est gardé** (au carnet, `sans_objet`) ; c'est la **carte Vente** de la rubrique qui ne lit que le registre
(`App.tsx` ~28402), quand la modale lit le carnet d'abord (~17001). Non corrigé.

## 48. LA CARTE VENTE LIT LE CARNET ; L'ÉTAT DU COMPROMIS ; LES DEUX NUMÉROS DES NOTAIRES — 24/10

**Carte Vente** (`4f26fe4`, écran seul, pas poussé) : « Prix net vendeur » = carnet d'abord, registre ensuite — comme la modale et le
taux. Essais 30/30, témoin inverse : la version d'avant échoue le contrôle neuf ; build vert.

**L'état du compromis — mesuré, lecture seule.** Au clic, la base écrit `en_cours` (affiché « enregistrée dans l'app ») ; la nuit le
remplace par le mot de Hektor : `active` (« signé ») ou `cancelled` (« annulé »). Hektor n'a QUE ces deux états (status 1 / 2) ; la
conclusion d'un compromis ne s'exprime que par l'existence d'une vente (15/09). Registre : compromis **9 263 active · 1 374 cancelled ·
0 en_cours** (les 96 nés dans l'app sont tous passés `active`). **Tous les lecteurs** (dossiers ouverts 2.2c, verrou de l'offre, chaînage,
`AFFAIRE_ETAT_MORT`) ne distinguent que **annulé / pas annulé** : `en_cours` et `active` valent « vivant ». ➡ Normal, comme avant ; seul
le libellé change. (Même chose pour la vente : `en_cours` au clic, vide après la nuit — Hektor n'a pas d'état de vente — d'où le titre
« Vente · état non renseigné », vrai aussi pour les 9 198 ventes venues de Hektor.)

**Les deux numéros des notaires — mesuré.** La paire existe déjà, dans la fiche contact (`app_contact_current`) :
10355906 ↔ 605227 (Me Eric PAILHES), 10064499 ↔ 122190 (Tiffany SELARL). Le registre n'en garde **qu'un** : le nôtre au clic, celui de
Hektor après la nuit. L'écran nomme les deux (`loadNomsContacts`). ⚠ **Ce que ça casse** : R3 compare 10064499 à 122190, ne les reconnaît
pas, et la ligne `notaire_id` du carnet reste **« en attente » pour toujours** (2 lignes aujourd'hui, compromis et vente de l'essai 5).
Deux voies, **à trancher par Frédéric** : (a) R3 reconnaît le notaire **par la paire** (la règle « deux numéros, reconnaître par la plage »),
rien en base ; (b) une **seconde colonne** au registre pour notre numéro, que la nuit ne touche pas (comme les colonnes `_app`).

## 49. LES NOTAIRES, DEUX NUMÉROS COMME L'ACQUÉREUR — audit du 24/10 *(Frédéric : « l'id Hektor pour communiquer avec Hektor, et mon id app pour le registre, comme les autres fiches de mon app gèrent les deux id »)* — lecture seule, **rien codé**

### Le modèle qui existe déjà : l'acquéreur
- Deux colonnes : `hektor_acquereur_id` (Hektor) et `app_contact_id` (nous).
- Au clic, la création écrit notre numéro. La nuit (`affaire_ledger.py` ~l. 745-832, G-10 du 23/09) lit le numéro de Hektor dans le miroir,
  le **traduit par la paire** (`app_contact` : `hektor_contact_id` / `hektor_target_id`) et pose `app_contact_id` avec un
  `COALESCE` — **elle n'efface jamais** un rattachement établi. Vérifié sur la vente 23358 après la nuit : 20000015 et 605976, intacts.
- Vers Hektor, le worker traduit nos numéros en ceux de Hektor par `cibleHektorContact` (C-1/C-9, 23/09) — **notaires compris**
  (l. ~2226-2270 : « notaires et mandants passent la porte, comme les acquéreurs »). La communication avec Hektor est donc DÉJÀ juste.

### Les notaires aujourd'hui : une seule colonne par rôle
| qui | écrit quoi |
|---|---|
| la création / la modification (R1, A5, N) | **notre** numéro (10064499, 10355906) dans `notaire_acquereur_id` / `notaire_mandant_id` |
| la nuit, `registre_depuis_console.py` | **le numéro de Hektor** (API pour la vente, console pour le compromis) **par-dessus** — sauf `notaires_origine = 'saisie'` (le gel, non employé) |
| le push | recopie la ligne locale chez Supabase |
**Mesure du 24/10** : 23 340 références de notaire au registre (6 772 côté acquéreur, 16 568 côté vendeur, ~880 notaires distincts) —
**100 % portent le numéro de Hektor, 0 le nôtre**, y compris celles nées dans l'app. **96 % se traduisent** par la paire (6 511 et
16 113) ; 261 + 455 n'ont pas de fiche chez nous.

### ⛔ Correction de ce que j'ai dit (§48)
R3 **sait** traduire (`@notaire`, worker ~l. 21478 : il compare la personne via la paire) — mais **seulement si la nuit est passée**, et
R3 ne tourne qu'**à la fin d'un travail**, donc avant la nuit. Résultat identique : la ligne `notaire_id` du carnet reste « en attente »
tant qu'aucun autre travail ne touche l'affaire.

### Le plan proposé — sur le modèle de l'acquéreur, À DÉCIDER
| # | pièce | où | ce que ça pourrait casser |
|---|---|---|---|
| P1 | deux colonnes **`notaire_acquereur_app_id`**, **`notaire_mandant_app_id`** (nous) ; les colonnes actuelles restent celles de **Hektor** | Supabase + la table locale (ajout de colonne au démarrage, comme `app_contact_id`) | additif ; le push envoie une colonne de plus — elle doit exister des deux côtés **avant** le run, sinon le run échoue (même piège que `app_contact_id`, l. 555) |
| P2 | la création / la modification écrivent **notre** numéro dans `_app_id` | les RPC (patch, accord) | trois fonctions déjà patchées aujourd'hui (empreintes à suivre) |
| P3 | la nuit **traduit** le numéro de Hektor en le nôtre (par la paire, `COALESCE`, jamais d'effacement) | `registre_depuis_console.py` | un notaire sans fiche chez nous (3 %) garde `_app_id` vide — on ne fabrique rien |
| P4 | rattrapage des 23 340 références (96 % traduisibles) | une seule écriture, accord | — |
| P5 | les lecteurs prennent **notre** numéro d'abord : l'écran (19 endroits dans App.tsx, 3 dans api.ts), la modale (préremplissage), R3 (compare `_app_id` à la saisie : égalité directe, plus besoin d'attendre la nuit → la ligne du carnet sort tout de suite) | front + worker | le worker continue d'envoyer le numéro de Hektor (inchangé) |
⚠ À regarder avant de coder : le classeur (`push_suivi_appsheet.py`) et les exports ne lisent pas ces colonnes (0 trouvé hors App.tsx,
api.ts, worker, `affaire_ledger.py`, `registre_depuis_console.py`) — à confirmer pièce par pièce.

## 50. « LES NOTAIRES SONT DES CONTACTS : POURQUOI UNE COLONNE DE PLUS ? » — 24/10 *(Frédéric)* — lecture seule, **remplace le plan du §49**

**Mesures.** Les notaires SONT des contacts. Le registre des contacts porte les deux numéros pour **tous** : 62 319 fiches, 62 319 avec
notre identité (≥ 10 M, dans la colonne au nom trompeur `hektor_contact_id`) **et** le numéro de Hektor (`hektor_target_id`). Sur les
1 327 notaires cités par le registre des transactions, **1 107 y sont** avec leurs deux numéros ; 220 n'ont pas de fiche dans la vue des
contacts.

**Pourquoi l'acquéreur a deux colonnes** (`db771db`, 01/09) : Frédéric — *« les ids Hektor étant les axes, il y aura un problème lors de la
coupure »*. `hektor_acquereur_id` était lu partout (le chaînage, les comparaisons avec Hektor, la nuit) : on a **ajouté** notre numéro à côté
plutôt que de tout réécrire. Un doublement de **transition**, pas un modèle obligé.

**Frédéric a raison : une colonne de plus n'est pas nécessaire.** Le registre des contacts EST le dictionnaire ; le registre des transactions
n'a besoin que d'UN numéro par notaire — **le nôtre** (il survit à la coupure). Celui de Hektor se retrouve dans la fiche contact, et le worker
le fait déjà avant chaque envoi (`cibleHektorContact`).

**Le plan, simplifié — À DÉCIDER, rien codé**
- les colonnes ACTUELLES portent **notre** numéro : la création l'écrit déjà au clic ;
- **la nuit** (`registre_depuis_console.py`) **traduit** le numéro de Hektor en le nôtre par la fiche contact **avant** d'écrire, et compare
  ainsi (sinon elle réécrirait chaque nuit) ; un notaire sans fiche (220) garde le numéro de Hektor — reconnaissable à la plage (< 10 M) ;
- **R3** compare la saisie (notre numéro) au registre (notre numéro) : égalité directe, plus d'attente à vie ;
- **l'écran** nomme déjà par les deux numéros : rien à changer ;
- **le worker** envoie déjà le numéro de Hektor : rien à changer ;
- **un rattrapage** des 23 340 références (96 % traduisibles), accord requis.
➡ Aucune colonne, aucune liste de plus ; une traduction au seul endroit qui écrit le numéro de Hektor.

**Complément du 24/10 (Frédéric : « et pour les acquéreurs ? pourquoi 220 non présents ? mon serveur a les deux id »).**
- **Les 220 notaires « sans fiche » sont tous sur le serveur.** Supabase n'a que 62 319 contacts (le périmètre de l'app) ; la doublure
  d'identité du serveur, `app_contact` dans `phase2.sqlite`, en a **356 649**, chacun avec ses deux numéros — et elle porte **les 220**
  (ex. Hektor 7987 ↔ nous 10003967). La nuit tourne SUR le serveur et lit déjà cette table pour l'acquéreur (G-10) : la traduction des
  notaires y sera donc **complète** (rattrapage : les 23 340 références, pas 96 %).
- **Les acquéreurs ont déjà notre numéro au registre** : sur 30 422 lignes qui portent le numéro de Hektor, **30 413** portent aussi le
  nôtre (`app_contact_id`) ; 9 non (7 offres, 1 compromis, 1 vente) ; 653 lignes n'ont aucun acquéreur (300 compromis, 342 ventes, 11 offres
  — pas un problème de numéro). Les deux colonnes restent : celle de Hektor sert au chaînage et aux comparaisons avec Hektor, la nôtre au
  registre ; à la coupure, la première devient morte. ➡ Rien à faire pour l'acquéreur, hormis les 9 lignes (à inclure au rattrapage).
- **Les workers envoient-ils le numéro de Hektor ? OUI, prévu et prouvé** (Frédéric, 24/10). `traduireLesPersonnesDeLaTransaction`
  (C-9, 23/09, worker ~l. 2242) traduit notaire de l'acquéreur, notaire du vendeur et mandants, **une fois, avant tout envoi**, sur les DEUX
  chemins : l'offre (`submitHektorTransactionStatus`, l. ~14046) et l'assistant compromis / vente (`submitHektorAssistantTransaction`,
  l. ~13295) — création ET modification. Preuve, essai 5 : l'écran a envoyé **10064499 / 10355906** (nos numéros) ; Hektor a enregistré
  **idNotaire 122190** sur l'offre 33116, et porte **122190 / 605227** sur le compromis 50137 et la vente 23358 (relus la nuit) ; l'acquéreur
  est parti en **605976** (Hektor) quand l'écran donnait 20000015. Un numéro de Hektor reçu tel quel « se vise lui-même »
  (`cibleHektorContact`) : la modification marche que le registre porte l'un ou l'autre. ➡ **Le plan du §50 ne touche pas au worker.**

---

## 51. BILAN DU REGISTRE DES TRANSACTIONS — 25/10 au soir *(Frédéric : « fais un audit, reprends le code actuel, relis le chat, les notes et l'historique ; il faut être sûr »)*

**Sources croisées** : `git log` du 21 au 25/10 (≈ 140 commits ⑧) ; cette note (§1-50) et l'étude des numéros (§1-20) ; le code
(`console_job_worker.js`, `affaire_ledger.py`, `registre_depuis_console.py`, `contrat_autorite.py`, `App.tsx`) ; la base
(`app_setting`, empreintes des fonctions) ; les messages de Frédéric dans les transcripts.

### ✅ FAIT — et vérifié ce soir dans le code ou la base
| pièce | quoi | preuve d'aujourd'hui |
|---|---|---|
| **R1** naître complet | la création écrit ses champs au registre au clic | `app_setting.affaire_nait_complete = on` |
| **A5** | la modification écrit au registre | `affaire_modif_au_registre = on` |
| **E** | la modification n'inscrit au carnet que ce qui a été tapé | `affaire_modif_champs_touches = on` |
| **A1** | la fin de rétractation au registre (retour + modale) | commit `5b0e2fb` (poussé) |
| **1a** | la seconde preuve des numéros à la relecture ; la liste des compromis lue par numéro | `poserNumerosManquants` (l. 21300) ; 0 transaction sans numéro (mesuré 25/10) |
| **1b** | l'acquéreur envoyé sous son numéro Hektor | `affaire_acquereur_numero_hektor = on` |
| **défaut 6** | le registre local adopte un contact né dans l'app | commits du 23/10 (`b9e58b8`…) |
| **R3** | le contrôle au retour de la création (verdict champ par champ, règle de sortie du 16/09, B, C, E, F1) | `controlerLeCarnet` (l. 21584) ; 54/54 |
| **C1-C6 + répartition** | la rubrique Affaires montre tout ce qui a été saisi, tout de suite | `1c5d70d` |
| **N** | le notaire du vendeur d'une offre gardé chez nous, repris par le compromis | `offre_notaire_vendeur = on` |
| **V** | le compromis verrouillé par sa vente | `compromis_verrouille_par_vente = on` |
| **§41 / §46 (écran)** | Vendu / Clos / Estimation ferment les transactions ; Actif rouvre une chaîne | `etatFermeAuxTransactions` (App.tsx l. 27856), poussé |
| **§48** | la carte Vente lit le net vendeur au carnet | `4f26fe4` |
| **pièces 1-4 des numéros** | chaque personne des listes et chaque notaire sous notre numéro ; écrans | `affaire_personnes_deux_numeros = on`, `app_acquereurs_json` = `69904a53` ; `.env` : 2 lignes ; nuit du 25/10 prouvée |
| **R3 sans relecture** | rattrapage « carnet seul » chaque matin + lecture de Hektor seulement au besoin | `.env` `APP_AFFAIRE_R3_RATTRAPAGE=1` ; 24113 : 10 « arrivée » ; 0 en attente |
| **R4, moitié écran** | chaque saisie montre son verdict dans la rubrique (« arrivé », « pas encore parti », « conflit », « échec », « sans objet ») | depuis le **16/09** (3.1, `e079218`), enrichi par R3 le 23/10 |
| **le gel** | reste éteint, comme décidé le 16/09 | `CHAMPS_APP_AFFAIRE = ()` (`contrat_autorite.py:180`) |

### ⬜ PAS FAIT — vérifié ce soir
| pièce | état réel | ce qui manque |
|---|---|---|
| **R2** la nuit respecte l'attente | **audit seul** (§12, 23/10, `eadad03`) ; **aucune ligne de code** dans `affaire_ledger.py`. Frédéric l'avait demandé le 23/10 (« R2, puis R4 et R5 ») ; R3 est passé devant parce qu'il en était la condition | des 6 conditions du §12 : **1 (R3) faite**, **3 (E) faite**, **4 (date sans heure = même jour) faite** dans `memeValeurHektor` ; **2 (un travail échoué)** faite par R3 (verdict « échec ») ; ⛔ **5 la durée maximale : à trancher par Frédéric** ; **6** les transactions d'essai : 0 ligne en attente aujourd'hui. Symptôme connu : le net vendeur de la vente effacé chaque nuit au registre (contourné à l'écran par §48) |
| **R4** la sentinelle | **absente** : aucune ligne `data.affaire_ecart` dans `check_gti_health.py` | une alerte quand R3 trouve un « conflit » ou un « échec » (aujourd'hui seulement dans le journal du travail) |
| **R5** l'état en attente | **rien** | l'état (refus, annulation, suppression) au carnet, respecté par la nuit tant que Hektor n'a pas confirmé |
| **§46 base** | patch « pas de transaction sur un bien en Estimation » **prêt, non posé** (`transaction_sur_estimation` absent de la fonction en base) | l'accord de Frédéric pour le coller |
| **pièce 5** | mesurée (35 005 / 35 005), audit « ce que ça pourrait casser » à faire | §16 de l'étude |
| **relecture de jour du worker** | réécrit les listes sans notre numéro jusqu'à la nuit | worker + redémarrage |
| **§42** boutons | 5 incohérences non tranchées | décisions de Frédéric |
| **petits défauts** | échéance −1 jour · chaîne neuve invisible sans recharger · prix de vente = prix du mandat (F4) · diffusion remise à 1 par une vente · libellé « Envoyer vers Compromis » | — |
| **restes de données** | 17 lignes hors miroir sans notre numéro, dont 3 compromis « active » fantômes ; la ligne d'essai 24933 jamais jugée | à décider |
| **D7 / T1 / T3** | modifier sans numéro Hektor ; le worker défait l'état si Hektor ne répond pas | « pour la coupure », décisions de Frédéric |
| **D8** | deux règles de chaîne (SQL au clic, Python la nuit ; v2 côté Python seulement) | à trancher avant d'allumer la v2 côté clic |
| **D9** | le cycle d'affaires du registre des mandats refait la nuit seulement | non vérifié à l'écran |

### ⛔ DÉCISION DE FRÉDÉRIC (25/10) — R2 : **A, PAS DE DURÉE MAXIMALE**
La protection d'un champ en attente **tombe seulement au verdict « arrivée »** de R3. Un champ que Hektor ne porte jamais (le net
vendeur d'une vente) reste donc **à notre valeur pour toujours** — c'est voulu. R2 ne concerne que les colonnes que la nuit réécrit
depuis Hektor, et seulement les lignes du carnet nées d'un geste **envoyé** à Hektor (`creation_app`, `modification_app`) ; ce qui
est gardé chez nous seulement (colonnes `*_app`, champs sans colonne, `saisie_app`, `classeur`) n'est pas concerné.

---

## 52. R2 — AUDIT DU CODE, avec la décision A — 25/10 *(Frédéric : « A »)* — lecture seule, **rien codé**

### L'ordre de la nuit, lu dans `run_full_pipeline.ps1` et `affaire_ledger.py`
1. l. 902 — la doublure du registre descend (`pull_from_supabase.py --table app_affaire_ledger`) ;
2. l. 911 — **`affaire_ledger.py --refresh --push`** : `refresh_ledger` → l'UPSERT depuis le miroir (l. 839 : `prix_net_vendeur=excluded…`,
   **sans** « vide ne gagne pas », sauf pour `app_contact_id`) → « le silence ne gagne pas » (l. 905) → **`recalculer_les_chaines`** (l. 988) ;
   puis `main()` : suppressions → **le push de la ligne ENTIÈRE** (`ledger_rows_for_push`, `SELECT *`) → les chaînes redescendues ;
3. l. 1253 — `registre_depuis_console.py` (les notaires, 8 colonnes, son propre envoi) ;
4. l. 1318-1322 — **le magasin du carnet puis le contrat dormant** (`magasin_affaire_app.py`, `appliquer_contrat_affaire.py`) : **APRÈS** le push
   et les chaînes — c'est le défaut **D5**, confirmé. Le contrat est vide (`CHAMPS_APP_AFFAIRE = ()`, le gel éteint).

⭐ **Donc la nuit d'aujourd'hui** recopie Hektor, calcule les chaînes, et **envoie à l'app la ligne entière** : un champ que Hektor ne porte
pas (le net vendeur d'une vente) part **vide** et efface ce que la création avait écrit au clic (R1).
⭐ Le worker, lui, **n'efface jamais** : `reporterAuRegistre` saute une valeur vide (« vide ne gagne pas »).

### Le carnet n'est PAS frais sur le serveur à l'heure de R2
La copie locale (`app_affaire_champ_app`) est remplie par le magasin **après** l'étape du registre ; la doublure `__sb` vient de la descente
de la veille (06:45). Une saisie faite dans la journée n'y est pas. ➡ **R2 doit lire le carnet chez Supabase, au moment même** (une lecture,
~60 lignes aujourd'hui). Si la lecture échoue : R2 ne fait rien, le dit, et la nuit fait exactement ce qu'elle fait aujourd'hui.

### La règle de R2 (avec A)
Après l'UPSERT et **avant les chaînes**, pour chaque ligne du carnet :
1. **origine** `creation_app` ou `modification_app` (un geste envoyé ; `saisie_app` et `classeur` exclus, comme R3) ;
2. **verdict** autre que « arrivée » (A : la protection ne tombe qu'à « arrivée ») — **et autre que « échec »** (§12, condition 2 : un
   travail échoué n'a rien envoyé, sa valeur n'est pas la transaction ; c'était 30712 : 160 000 chez nous, 16 000 chez Hektor) ;
3. **le champ a une colonne** (`CARNET_VERS_REGISTRE` du worker : montant, date, date d'acte, séquestre, net vendeur, honoraires vendeur,
   n° de mandat, validité) **et R1 l'écrit pour ce genre** (la table de R1, `gen_patch_r1_affaire_nait_complete.py` l. 37-74) — offre :
   validité ; compromis : acte, séquestre, net, honoraires vendeur ; vente : net, honoraires vendeur ; montant et date pour les trois.
   ⭐ Sans ce filtre, R2 poserait au registre la **validité préremplie** d'un compromis ou d'une vente (mesuré : 15 jours sur 1001394 et
   1001395) et la **date d'acte** préremplie d'une vente — que R1 refuse justement d'écrire ;
4. ⛔ **PAS les champs que R3 juge SUR LE REGISTRE** : `numero_mandat` (les trois genres) et la `date` d'une offre (`@registre:*`). Si R2 y
   reposait notre valeur, R3 comparerait la saisie **à elle-même** et dirait « arrivée » sans preuve, puis la ligne sortirait du carnet —
   **le même piège que les notaires de la pièce 3**. Ils restent donc à Hektor la nuit, et R3 les juge honnêtement le lendemain ;
5. **si le registre (Hektor) porte déjà la même valeur** (`memeValeurHektor` : une date sans heure = la même date avec l'heure), on ne
   touche à rien — sinon R2 rognerait l'heure d'une date.

Alors la colonne reprend la valeur du carnet, **dans le registre local** : les chaînes et le push partent avec elle.

### Ce que R2 changerait CETTE NUIT (mesuré le 25/10 sur Supabase)
Le carnet compte **0 ligne « en attente »** (R3 et son rattrapage les ont toutes jugées). Les lignes « non arrivées » qui ont une colonne :

| ligne | carnet | registre | R2 |
|---|---|---|---|
| vente 1001395 `prix_net_vendeur` (sans objet : Hektor ne le porte pas) | 110 000 | **vide** | ✅ **reposé** |
| vente 1001395 `date_acte`, `jours_validite` | 2026-12-15, 15 | vide | ❌ R1 ne les écrit pas pour une vente |
| compromis 1001394 `jours_validite` | 15 | vide | ❌ R1 ne l'écrit pas pour un compromis |
| offre 1001339 (essai du 04/09) `date`, `jours_validite`, `numero_mandat` | égaux | égaux | ❌ rien à faire (et `date`, `numero_mandat` exclus, point 4) |

➡ **UNE seule valeur change** : le net vendeur de la vente de l'essai 5. C'est exactement le symptôme du 24/10.

### Ce que ça pourrait casser ailleurs
- **Les chaînes** : R2 joue avant `recalculer_les_chaines` ; seuls le montant ou la date d'un champ en attente pourraient bouger une chaîne.
  Ce soir : aucun. **Essai : le rejeu des chaînes avant / après, identique.**
- **R3** : le piège du point 4, évité par l'exclusion. **Essai : un n° de mandat en attente n'est pas reposé.**
- **« Conflit »** : avec A, une ligne en « conflit » **reste protégée** (notre valeur au registre ; celle de Hektor reste dans `payload_json` et
  dans le verdict). ⚠ C'est exactement ce qui peut masquer une correction faite ensuite **dans Hektor** par un négociateur — d'où **R4** (la
  sentinelle), qui doit sonner sur chaque « conflit ». Aujourd'hui : **0 ligne en conflit**.
- **Le classeur** (chantier en attente de ⑧) : `origine = 'classeur'` exclue.
- **Le contrat dormant (D5)** : inchangé, toujours vide et toujours après le push. R2 le **remplace dans l'intention** ; le retirer est une
  autre décision.
- **Les notaires** (`registre_depuis_console.py`) : R2 ne touche aucune de leurs colonnes.
- **Deux copies d'une règle** : la table « quel champ pour quel genre » vit dans le SQL de R1 et vivra dans R2. Si R1 change sans R2, R2 protège
  **moins** (jamais plus) : panne bénigne. Un essai relira le SQL de R1 en base pour comparer.
- **L'étape du registre est BLOQUANTE dans le run** (`Invoke-Step`) : toute erreur de R2 doit être **attrapée** — R2 sauté, écrit au journal,
  la nuit continue comme aujourd'hui.
- **Alternative écartée** : mettre « vide ne gagne pas » (`COALESCE`) sur ces colonnes dans l'UPSERT. Plus court, mais il figerait **toute**
  valeur qu'un négociateur viderait ensuite dans Hektor, saisie dans l'app ou non : c'est le gel, en plus large.

### Le code proposé (rien n'est écrit)
- `phase2/sync/affaire_ledger.py` : `r2_attente_actif()` (interrupteur **`APP_AFFAIRE_R2_ATTENTE=1`** dans `.env`, lu après chargement) ;
  `lire_le_carnet_supabase()` ; `respecter_l_attente(con, carnet)` appelé dans `refresh_ledger` **juste avant** `recalculer_les_chaines` ;
  le journal dit « R2 : N valeur(s) reposée(s) » avec la liste (une ligne par valeur, jamais un total seul).
- Essais `phase2/checks/test_r2_attente.py` sur une **copie** de `phase2.sqlite` (jamais `--push`) : **témoin inverse** éteint = octet pour
  octet ; allumé = **la seule** `1001395.prix_net_vendeur` change ; les exclusions (échec, arrivée, classeur, n° de mandat, validité d'une vente,
  date égale à l'heure près) ; lecture Supabase en panne → rien ne change, la nuit continue ; chaînes identiques ; mutants.
- **Activation** : pousser (le script est en service dès qu'il est enregistré : sans la ligne du `.env`, il ne fait rien), puis la ligne du
  `.env`, puis le contrôle du lendemain matin (le journal de nuit + le registre de 1001395 à 110 000).

---

## 53. R2 CODÉ — la nuit respecte l'attente : écrit, éprouvé sur copies, **non poussé, ÉTEINT** *(25/10, Frédéric : « vas-y »)*

### Le code — `phase2/sync/affaire_ledger.py`
- `respecter_l_attente(con)` est appelé dans `refresh_ledger` **juste après l'UPSERT et le « silence ne gagne pas », avant
  `recalculer_les_chaines`** : les chaînes et le push partent avec notre valeur.
- Les 5 règles du §52 : origine `creation_app` / `modification_app` · verdict ni « arrivée » ni « échec » · colonne **et** genre écrit par
  R1 (`R2_CHAMPS_PAR_GENRE`) · jamais un champ que R3 juge sur le registre (`R2_JUGES_SUR_LE_REGISTRE` : n° de mandat, date d'une offre) ·
  rien si Hektor porte déjà la même valeur (`_meme_valeur`, copie de `memeValeurHektor`).
- Le carnet est lu **chez Supabase, sur le moment** (`lire_le_carnet_supabase`, plafond 20 000 lignes : atteint = on refuse de conclure).
- **Ne lève jamais** : une panne écrit « R2 NON JOUÉ — la nuit continue comme avant » et la nuit fait ce qu'elle faisait.
- Le journal : « R2 : N valeur(s) reposée(s) sur M ligne(s) lues », puis **une ligne par valeur** (`1001395.prix_net_vendeur : (vide) ->
  110000.00 (sans_objet)`) ; le compte rendu de `refresh_ledger` porte `r2`.
- **Interrupteur `APP_AFFAIRE_R2_ATTENTE=1`** dans `.env`, lu après chargement. Absent = « R2 : ÉTEINT », comportement d'avant à l'octet près.
  ⚠ **Le script est en service dès qu'il est poussé** : sans la ligne du `.env`, il n'écrit qu'une ligne de journal de plus.

### Les essais — `phase2/checks/test_r2_attente.py` : **14/14**
- **La fonction** sur un petit registre : (1) le net vendeur d'une vente reposé ; (2) **exactement** les 4 valeurs attendues, dont un
  « conflit » (A) et une validité d'offre modifiée sans verdict ; (3) **intacts** : date d'acte et validité d'une vente (genre), validité d'un
  compromis, n° de mandat, date d'une offre, « échec », « arrivée », `saisie_app`, `classeur`, même valeur (115 000 = 115000.00) ;
  (4) le journal nomme chaque valeur ; (5) **témoin** : éteint, rien ne bouge ; (6) **lecture en panne** : rien ne bouge, aucune exception ;
  (7) la règle d'égalité ; (7b) **les deux copies de la règle par genre** (R2 et le générateur du patch R1) sont identiques, colonne par colonne.
- **La vraie nuit, sur 3 copies de `phase2.sqlite`** (miroir de Hektor en lecture seule, le vrai carnet lu une fois chez Supabase, jamais
  de push) : (8) la version d'avant ne connaît pas R2 ; (9) **TÉMOIN INVERSE : éteinte, la nuit neuve rend le registre de la nuit d'avant,
  31 103 lignes identiques** ; (10) allumée : **1001395.prix_net_vendeur passe de vide à 110000.00** ; (11) **rien d'autre ne change**, ni
  colonne ni ligne ; (12) **aucune chaîne ne bouge** (12 170 chaînes dans les trois cas) ; (13) le compte rendu porte R2.
- **7 mutants attrapés** : n° de mandat protégé, « échec » protégé, genre ignoré, même valeur ignorée, origine ignorée (→ 2, 3) ; panne non
  attrapée (→ 6) ; une colonne ajoutée à la table d'un genre (→ 2, 3, 7b).
- **Les essais voisins** qui chargent ce script : `test_chainage_v2`, `test_chainage_vente_ferme`, `test_adoption_contact_ne_dans_app` :
  **verts**. ⚠ `test_alignement_suppression` est **rouge, et l'était déjà** : son faux client expose `request`, alors que le script appelle
  `_request` depuis le correctif du 17/09 (`bcb05fe`, « le journal des suppressions n'a jamais été lu »). Sans rapport avec R2
  (`appliquer_les_suppressions` n'est pas touché). **Noté, pas corrigé.**

### Pour l'activer, dans l'ordre (chaque geste avec l'accord de Frédéric)
1. **pousser** (rien à redémarrer : c'est le run de nuit, pas le worker) ;
2. ajouter **`APP_AFFAIRE_R2_ATTENTE=1`** au `.env` du serveur ;
3. **le lendemain matin** : dans `logs/scheduled/quotidien_*.log`, « R2 (la nuit respecte l'attente) : 1 valeur(s) reposée(s) » et la ligne
   `1001395.prix_net_vendeur` ; chez Supabase, **le registre de la vente 23358 porte 110 000** ; et le nombre de chaînes inchangé.
⛔ **Retour arrière** : retirer la ligne du `.env` — la nuit suivante, la colonne redevient ce que dit Hektor.

---

## 54. R2 ALLUMÉ, et R4 — AUDIT de la sentinelle — 26/10 *(Frédéric : « allume R2 et attaque R4 »)* — R4 en lecture seule, **rien codé**

### R2 allumé — 26/10, 06:35
`.env` sauvegardé (`.env.avant_r2_attente_20261026`, ignoré par git), puis **`APP_AFFAIRE_R2_ATTENTE=1`** ajouté (74 lignes, 0 `\r\r\n`) ;
**le script de nuit le lit** (`r2_attente_actif()` → `True`). Premier passage : **le run du 27/10 à 04:00**. ⏰ À contrôler le 27/10 au matin :
« R2 : 1 valeur(s) reposée(s) » et la ligne `1001395.prix_net_vendeur`, la vente 23358 à 110 000 chez Supabase, les chaînes inchangées.

### Ce que R4 doit faire (§3)
« `data.affaire_ecart` (comme `data.contact_modif_ecart`) ; à l'écran, un champ en attente ou en conflit se signale. » Avec la décision A
de R2, c'est devenu **indispensable** : un « conflit » reste à notre valeur au registre — il peut cacher une correction faite ensuite
dans Hektor par un négociateur. **Il faut qu'il sonne.**

### Ce qui existe déjà (code et base, 26/10)
- **L'écran** : chaque saisie de la rubrique Affaires porte son verdict (« arrivé », « pas encore parti », « conflit », « échec, non
  envoyé », « sans objet ») depuis le 16/09 (3.1). ✅ La moitié écran de R4 est faite.
- **Les trois sœurs** du chantier 8a (`data.annonce_naissance_ecart`, `data.contact_modif_ecart`, `data.annonce_modif_ecart`,
  `monitoring/check_gti_health.py` l. 680-740) : une **vue** d'écarts, **une ligne par champ** (jamais « N sur M »), une colonne
  `traite_le` et une fonction admin `*_ecart_traiter` (« vu ») ; la sentinelle compte `traite_le is null`, **warning**, avec un
  échantillon. Domaine `data_quality`, posé par la boucle elle-même (l. 1798) : **pas le piège du domaine refusé du 25/10**.
  ⚠ **Mais aucun écran n'appelle leurs fonctions « vu »** (0 appel dans `apps/hektor-v1/src`) : leurs alertes ne se taisent que par SQL.
- **Un écart des personnes d'une transaction existe déjà** : `app_affaire_personne_ecart` (« personne non gardée par Hektor »), avec
  un bandeau **et un bouton « fermer »** dans la rubrique (`fermerAffairePersonneEcart`). **Aucune sentinelle ne le compte.**
- **Le moniteur n'a aucune ligne sur le carnet des transactions** : un « conflit » ou un « échec » trouvé par R3 n'est que dans le journal
  du travail (`app_carnet_controle`, en `error`).

### La mesure (26/10)
Carnet (saisies envoyées) : **0 « conflit », 0 « échec », 0 « en attente »** ; 11 « arrivée », 22 « sans objet », 23 sans état (les
champs d'offre exclus exprès, et l'essai 24933 d'avant R3). Écarts de personnes ouverts : **0**. ➡ R4 serait **vert aujourd'hui** : la
répétition devra fabriquer son **témoin positif** (des lignes d'essai dans une transaction annulée à la fin).

### Le mécanisme proposé — à arbitrer par Frédéric
1. **Une vue** `app_v_affaire_carnet_ecarts`, une ligne par transaction **et par champ** : saisie envoyée (`creation_app`,
   `modification_app`) dont le verdict est **« conflit »** ou **« échec »**, ou **« en attente » / « inconnu » depuis plus de 48 h**
   (le rattrapage R3 passe chaque matin : au-delà de deux matins, la preuve n'arrivera pas seule — c'est le « non relu » des sœurs). Colonnes :
   annonce, genre, numéros, champ, notre valeur, celle de Hektor, verdict, dates, négociateur.
2. **Le « vu » de l'humain** dans une **table à part** `app_affaire_carnet_ecart_vu` (transaction, champ, l'`ecrit_le` vu, qui, quand) —
   ⭐ **plutôt qu'une colonne dans le carnet** : le carnet est écrit par la création, la modification, R3 et R2 ; une table à part ne touche
   aucun de ces écrivains. Une saisie **réécrite** après le « vu » sonne de nouveau (on compare l'`ecrit_le`). Fonction admin
   `app_affaire_carnet_ecart_traiter(app_affaire_id, champ)`.
3. **La sentinelle** `data.affaire_ecart` dans `DATA_SENTINELS`, **warning** comme ses sœurs (seuls les critical envoient un e-mail), avec
   l'échantillon (annonce, genre, champ, verdict, nos valeurs).
4. **Une deuxième ligne, gratuite** : `data.affaire_personne_ecart` sur `app_affaire_personne_ecart` (`ferme_le is null`) — le bouton
   « fermer » existe déjà à l'écran, donc **cette alerte écoute déjà l'humain**.
5. **L'écran** : un petit bouton **« vu »** (admin) à côté de « conflit » / « échec » dans la rubrique, qui appelle la fonction du point 2 —
   sinon l'alerte ne se tait que par SQL, comme les trois sœurs aujourd'hui.

### Ce que ça pourrait casser ailleurs
- **Le moniteur** : une ligne refusée fait tomber tout le lot (25/10) — la boucle pose `data_quality`, la clé est neuve ; **vérifier une
  vraie écriture** après la pose (`observed_at` qui avance). La vue doit être lisible par la clé de service (`grant select … to service_role`).
- **Le carnet** : rien ne change (table à part). R2 et R3 ne lisent pas la nouvelle table.
- **La descente** : une table neuve chez Supabase n'est descendue que si on la déclare — inutile ici (le serveur ne la lit pas).
- **Le bruit** : 48 h et le « vu » évitent qu'une ligne d'essai sonne pour toujours. Les champs d'offre exclus de R3 n'ont pas d'état : ils
  ne sonnent pas.
- **L'écran (point 5)** : un appel de plus dans la rubrique, réservé à l'admin ; la fonction refuse un non-admin (`admin_requis`).

### Ce qui se pose, dans l'ordre (chaque geste avec l'accord de Frédéric)
patch base (vue + table + fonction) avec inverse et répétition **à témoin positif** → collé par Frédéric → sentinelle dans le moniteur
(poussée, active au prochain passage, toutes les 2 h) → l'écran si Frédéric le veut → **essai réel** : une ligne d'essai mise en
« conflit » doit apparaître sur l'écran Santé, puis se taire après « vu ».

---

## 55. R4 — UNE SAISIE FAITE DANS HEKTOR, ET LA RÉPONSE À UN CONFLIT — audit du 26/10 *(Frédéric : « si l'utilisateur écrit directement dans Hektor, que se passe-t-il ? […] audite encore et propose-moi »)* — lecture seule, **rien codé**

### Une saisie faite directement dans Hektor (code de la nuit, de R2, de R3 et de l'écran)
Il n'y a **pas** de règle « la date la plus récente gagne » : Hektor ne donne pas de date par champ. Ce qui décide, c'est **le verdict de R3**.
| cas | ce qui se passe |
|---|---|
| transaction **née dans Hektor** (pas de carnet) | la nuit recopie Hektor, l'app suit — **comme avant** ; R2 ne la voit pas |
| née dans l'app, **modifiée ensuite dans Hektor**, le champ déjà « arrivé » (il a une colonne) | la ligne est **sortie du carnet** par R3 → la nuit reprend Hektor → l'app suit — **comme avant** |
| idem, mais le champ **attendait encore sa preuve** (quelques minutes après la création, ou jusqu'au matin) | R2 garde notre valeur ; R3 voit autre chose chez Hektor → **« conflit »** → c'est là que R4 doit sonner |
| champ que Hektor **ne porte pas** (net vendeur d'une vente, taux, notaires d'une offre) | personne ne peut le changer dans Hektor : l'app garde notre valeur, voulu |

⚠ **Trouvé en vérifiant — deux champs « arrivés » restent au carnet et l'écran les lit là** : le **prix de vente du compromis** (ligne
« Prix public » de la carte, `k.prix_publique`, App.tsx l. ~28391) et le **taux** (`tauxDe`, carnet d'abord). R3 ne rejuge pas une ligne
« arrivée » : si un négociateur change ensuite le prix dans Hektor, l'en-tête (registre) suit mais **cette ligne garde l'ancienne valeur**.
Le taux, lui, n'existe pas chez Hektor (il se recalcule des honoraires). **Noté, pas corrigé** — à traiter à part (un rejugement périodique
des « arrivées » gardées, par le rattrapage du matin).

### Ce qui arrive VRAIMENT comme conflit — mesuré dans le journal de R3 depuis le 23/10
3 passages en « conflit ou échec », tous le 23/10 : **30712** (l'offre **acceptée** 33094 : la modification du 13/10 a échoué, Hektor refuse
en silence une offre acceptée — 3 « échec ») et deux transactions **d'essai** de 24113 (les faux conflits F1 / notaire, corrigés le jour
même). **0 depuis.** ➡ Un vrai conflit est **rare** ; quand il arrive, c'est le plus souvent **Hektor qui a raison** (il a refusé, ou un
négociateur a corrigé).

### Ce que « garder la nôtre » permet vraiment (§42-43, décisions du 07/09, 13/10, 24/10)
Renvoyer notre valeur à Hektor = le geste **« Modifier »** existant. Il est **grisé** sur une offre acceptée (Hektor la refuse), **retiré**
sur un compromis verrouillé par sa vente (V). Il reste sur l'offre en cours / refusée, le compromis ouvert, la vente (« on ne touche pas »).
➡ « Garder la nôtre » ne peut pas toujours **corriger Hektor** ; il peut toujours **garder l'app** à notre valeur.

### La proposition (à arbitrer par Frédéric)
**Par défaut, sans geste humain** : un « conflit » reste protégé (décision A) et **l'alerte sonne** (warning, écran Santé, toutes les 2 h).
**Les gestes** (admin), au même endroit que le verdict dans la rubrique Affaires :
| verdict | ⓐ « Prendre la valeur de Hektor » | ⓑ « Garder la nôtre » |
|---|---|---|
| **conflit** | notre saisie est **rangée** (table des décisions : notre valeur, celle de Hektor, qui, quand) puis **retirée du carnet** → R2 ne protège plus, l'écran retombe sur le registre, la nuit met la valeur de Hektor. « Une saisie ne se perd jamais » : elle reste dans la table des décisions | la décision est rangée, **l'alerte se tait** pour cette saisie ; R2 continue de protéger ; si Hektor doit être corrigé aussi : **« Modifier »** quand il est disponible (il n'est pas automatique) |
| **échec** (rien n'est parti) | idem ⓐ (le registre porte déjà la valeur de Hektor ; l'écran cesse d'afficher notre valeur pour le taux / le net) | idem ⓑ — et « Modifier » pour la renvoyer |
| **en attente > 48 h** | idem ⓐ | « attendre encore » : l'alerte se tait pour cette saisie |
Une saisie **réécrite** après la décision sonne de nouveau (la décision vaut pour l'`ecrit_le` vu).

**Ce que ça remplace dans le §54** : le simple « vu » devient ces deux gestes ; la table du « vu » devient **la table des décisions**
(`app_affaire_carnet_decision`). Le reste du §54 tient (la vue des écarts, la sentinelle `data.affaire_ecart`, la 2ᵉ sentinelle des
personnes, warning).

### Ce que ça pourrait casser ailleurs
- **ⓐ retire une ligne du carnet** : c'est déjà ce que R3 fait pour une « arrivée » (même `DELETE`, même table) ; R2 et l'écran savent déjà
  vivre sans la ligne (ils retombent sur le registre). ⚠ Pour un champ **sans colonne** (prix de vente du compromis, taux), la ligne de la
  carte **disparaît** ; la valeur de Hektor reste dans l'en-tête.
- **La règle du projet « Hektor confirme, il n'écrase pas »** (CLAUDE.md §4) : respectée — sans geste humain, Hektor n'écrase rien ; c'est
  l'humain qui choisit ⓐ.
- **Les droits** : les deux fonctions refusent un non-admin (`admin_requis`), comme les sœurs.
- **Le moniteur** : inchangé par rapport au §54.

---

## 56. R4 CODÉ — les écarts du carnet et les deux gestes : écrit, **non posé, non poussé** *(26/10, Frédéric : « vas-y »)*

### Les pièces
1. **Base** — `supabase/patch_r4_affaire_ecart_2026-10-26.sql` (+ `_INVERSE`, `_REPETITION`), générés par
   `phase2/checks/gen_patch_r4_affaire_ecart.py` depuis **un seul corps** (`gen_patch_r4_affaire_ecart_corps.sql`, repris à l'identique
   par le patch et la répétition). **Additif**, aucune fonction existante retouchée, **le carnet n'est pas modifié** :
   - `app_affaire_carnet_decision` : la réponse de l'humain ; **notre saisie y est rangée** avant d'être retirée (« prendre Hektor ») ;
     lecture pour les connectés actifs (comme le carnet), écriture par la seule fonction ;
   - `app_v_affaire_carnet_ecarts` (`security_invoker`) : une ligne par champ — saisie envoyée en « conflit », « échec », ou « en attente » /
     « inconnu » depuis plus de 48 h ; `a_traiter` = aucune décision pour **cette** saisie (`ecrit_le`) ;
   - `app_affaire_carnet_ecart_trancher(affaire, champ, 'hektor' | 'app' | 'attendre')` — **admin seulement** ; refuse ce qui n'est pas un
     écart, « attendre » hors d'une attente, « garder » hors d'un conflit ou d'un échec. **Rien n'est envoyé chez Hektor.**
   - Le retour arrière **ne perd aucune décision** (table renommée si elle porte des lignes) et ne remet pas au carnet ce que l'humain a retiré.
   - **La répétition : 14 contrôles**, à témoin positif (5 lignes d'essai sur 1001393 / 1001394 : conflit, échec, attente de 72 h, attente de
     2 h, `saisie_app`) — la vue en montre exactement 3 ; un non-admin est refusé ; « garder » range et fait taire, la ligne reste ; une
     saisie **réécrite** sonne de nouveau ; « prendre Hektor » range puis retire ; « attendre » ; les refus de forme ; ce que compterait la
     sentinelle (1) ; puis le vrai retour arrière. Elle finit par « ESSAI ANNULÉ » : **rien ne reste**. ⚠ **Pas encore jouée** : la session ne
     peut pas écrire en base, c'est Frédéric qui la colle.
2. **Moniteur** — `monitoring/check_gti_health.py`, deux sentinelles **warning** : `data.affaire_ecart` (la vue, `a_traiter`) et
   `data.affaire_personne_ecart` (les personnes que Hektor n'a pas gardées, `ferme_le is null`, dont le bouton « fermer » existe depuis le
   17/09). Domaine `data_quality` posé par la boucle. 40 sentinelles, clés uniques.
   ⚠ **Ce fichier est en service dès qu'il est enregistré** (la tâche le lit sur le serveur) : tant que le patch n'est pas collé,
   `data.affaire_ecart` sera **« illisible »** (inconnu, sans e-mail) au passage du moniteur. **Coller le patch avant 08:48.**
3. **Écran** — `lib/api.ts` : `loadAffaireCarnetEcarts` (jamais d'exception : vue absente = aucun geste) et `trancherAffaireCarnetEcart`
   (lève). `App.tsx` : `gestesEcartCarnet(etat)` ; dans la grille des transactions de la modale, à côté du verdict, **pour l'admin et pour un
   champ en écart seulement** : « Prendre la valeur de Hektor » + « Garder la nôtre » (conflit, échec) ou « Attendre encore » (attente) ;
   une aide au survol dit ce que fait chaque geste ; après le geste, le carnet est relu ; une erreur s'affiche sous la grille.

### Les essais
- `npm run build` : **vert**.
- `apps/hektor-v1/test_rubrique_affaires_complete.cjs` : **36/36** (4 neufs pour R4 : les gestes par verdict, aucun geste sur « arrivé » /
  « sans objet », chaque geste porte son aide) ; **témoin inverse** : la version d'avant échoue les 3 contrôles qui exigent un geste.
- Fins de ligne : `\r\r\n` = 0 partout (App.tsx, api.ts, moniteur en CRLF gardés ; SQL et générateur en LF).

### Pour l'activer, dans l'ordre (chaque geste avec l'accord de Frédéric)
1. **coller la répétition** → « ESSAI ANNULÉ -- 14 sur 14 » ;
2. **coller le patch** → les 4 contrôles « OK » ;
3. **pousser** (l'écran part par Vercel ; le moniteur est déjà en service) ;
4. le moniteur suivant : `data.affaire_ecart` et `data.affaire_personne_ecart` **« ok »** (0) sur l'écran Santé — et une **vraie écriture**
   (`observed_at` qui avance) ;
5. **l'essai réel**, si Frédéric le veut : une ligne d'essai mise en « conflit » sur 24113 → elle sonne au moniteur, les deux boutons
   apparaissent dans la modale, « garder la nôtre » la fait taire.

### ✅ R4 POSÉ EN BASE — 26/10, ~07:20 *(Frédéric : « fais-le toi-même »)*
- **La répétition, jouée par moi** (`execute_sql`) : **« ESSAI ANNULÉ -- 14 sur 14 »**, puis vérifié qu'il ne reste rien (aucun objet R4,
  aucune ligne d'essai, carnet à 56 lignes).
- **Le patch, posé par moi** : les contrôles **5 sur 5 « OK »** — table des décisions vide, lecture seule pour les connectés et fermée à anon ;
  vue lisible par les connectés et la clé de service, fermée à anon ; fonction ouverte aux connectés, fermée à anon ; **0 écart** ; carnet
  intact (56 lignes).
- **Les deux sentinelles se lisent par l'API avec la clé du moniteur** : `app_v_affaire_carnet_ecarts?a_traiter=eq.true` et
  `app_affaire_personne_ecart?ferme_le=is.null` → HTTP 200, **0** chacune.
- ⬜ **Reste** : pousser (l'écran, les deux boutons) ; ⏰ au passage du moniteur de 08:48, vérifier `data.affaire_ecart` et
  `data.affaire_personne_ecart` « ok » dans `app_monitor_status` (une VRAIE écriture, `observed_at` qui avance).

---

## 57. R5 — L'ÉTAT D'UNE TRANSACTION : audit du 26/10 *(Frédéric : « on enchaîne sur le dev »)* — lecture seule, **rien codé**

### Ce que R5 devait faire (§3)
« L'état (refus, annulation, suppression) entre en attente comme les autres champs ; la nuit le respecte tant que Hektor n'a pas confirmé. »
C'est le défaut **D6** (§2), et les pistes **T1 / T2** de l'audit « l'écriture meurt » (note ⑧, 22/10).

### Le code aujourd'hui (lu en entier)
- **Le geste** — `app_geste_affaire_optimistic` (empreinte `a6569229`) : refuser / accepter une offre, annuler / supprimer un compromis,
  supprimer une vente. Il écrit l'état **dans la colonne `state` du registre** (ou `present_in_hektor = false` pour une suppression), **pas au
  carnet**, puis pose le travail (`change_hektor_offre_status`, `cancel_hektor_compromis`, `delete_hektor_compromis`, `delete_hektor_vente`)
  qui **emporte l'état d'avant**. Les verrous (offre par son compromis 16/09, compromis par sa vente V 23/10) sont dans la fonction.
- **Le worker** : il vérifie l'état ABSOLU chez Hektor ; si Hektor échoue, le filet rejoue puis `restaurerEtatAffaire` **remet l'état d'avant**
  — **décision écrite du 29/08** (C.4-bis), rappelée « pour la coupure » (T1).
- **La nuit** : l'UPSERT recopie `state=excluded.state` depuis le miroir (colonne non protégée) — R2 ne la touche pas (elle n'est pas au carnet).

### La mesure (base, 26/10)
| geste | travaux | tous « done » | sur un vrai bien | durée médiane | la plus longue |
|---|---|---|---|---|---|
| refuser / accepter une offre | 25 | ✅ | **0** | 7 s | 29 s |
| annuler un compromis | 13 | ✅ | **0** | 9 s | 2 h 18 (une fois, 07/09) |
| supprimer un compromis | 16 | ✅ | **0** | 14 s | 27 s |
| supprimer une vente | 14 | ✅ | **0** | 11 s | 31 s |
➡ **68 gestes d'état depuis le 29/08, tous sur les biens d'essai, tous confirmés par Hektor.** Les négociateurs changent l'état **dans Hektor**,
et la nuit le recopie : c'est le cas « comme avant » du §55. Le risque que R5 couvre **tant que Hektor vit** :
1. un geste dont le travail **n'a pas encore tourné** quand la nuit passe (04:00) — fenêtre de quelques secondes ; la nuit d'après corrige ;
2. un geste que **Hektor refuse** — le worker le voit (état absolu) et **remet l'état d'avant** : c'est voulu (29/08), l'app ne ment pas.
➡ **Aujourd'hui, R5 ne protégerait rien de réel.** Sa vraie valeur est **à la coupure** : sans Hektor, le worker défait chaque état (T1) et la
nuit n'a plus de miroir — c'est exactement « l'écriture meurt » du 22/10.

### Ce que R5 demanderait (pour mémoire, si on le faisait maintenant)
- le geste range l'état **au carnet** (`champ = 'state'`, origine `geste_app`), en plus de la colonne ;
- R3 le juge au retour (« arrivée » si Hektor porte cet état) ; R2 le repose la nuit tant qu'il n'est pas « arrivé » ; R4 sonne s'il reste
  en conflit ;
- ⚠ et **renverser T1** (le worker ne défait plus l'état) — c'est **revenir sur la décision du 29/08** ;
- ce que ça pourrait casser : **les chaînes** (`recalculer_les_chaines` lit `state` : une offre refusée ferme une chaîne), **les verrous** de la
  fonction du geste (ils lisent `state`), le statut du bien (redescente), et la règle « Hektor confirme ».

### Les choix — À DÉCIDER PAR FRÉDÉRIC (rien n'est choisi)
- **A — coder R5 maintenant**, sans toucher T1 (le worker continue de défaire sur un refus de Hektor) : protège la fenêtre de quelques secondes
  et prépare la coupure. Coût : la fonction du geste, R3, R2, l'écran ; risque sur les chaînes et les verrous.
- **B — le ranger avec la coupure**, avec T1 et T3 (modifier sans numéro Hektor), où il prend son sens : un seul chantier « l'état chez nous ».
  Rien n'est perdu aujourd'hui (mesuré : 0 geste réel, 0 échec).
**Ma recommandation : B.** Et prendre à la place un point qui sert **aujourd'hui** (voir la liste au §51).

### ⛔ DÉCISION DE FRÉDÉRIC (26/10) : **B — R5 est rangé dans l'étape 3** *(« B, donc dans l'étape 3 »)*
Avec T1 (le worker défait l'état si Hektor refuse, décision du 29/08) et T3 (modifier sans numéro Hektor) : un seul chantier de la coupure, « l'état d'une transaction chez nous ». Inscrit au plan (`PLAN_DEV_ACTUALISE_2026-08-20.md`, « Ce qui n'est PAS ici » et le journal du 26/10). **Ne pas relancer en étape 2.**

---

## 58. LES POINTS RESTANTS, UN PAR UN — *(Frédéric, 26/10 : « on va corriger tous ces points un par un, mais fais un audit à chaque fois avant de me proposer »)*
Ordre suivi : celui de sa question (1, 2, 4, 5, 6, 7).

### Point 1 — le blocage en base des transactions sur une Estimation (§46) : audit du 26/10, lecture seule
- **La fonction n'a pas bougé depuis la préparation** : `app_change_annonce_status_optimistic` porte toujours **44697dd5** (l'empreinte
  attendue par le patch). L'interrupteur `transaction_refusee_sur_estimation` n'existe pas encore (patch non posé).
- **C'est la SEULE porte qui crée une transaction** : aucune autre fonction n'insère dans `app_affaire_ledger` (lu dans la base).
- **Dans la vraie vie, personne ne pose de transaction sur une Estimation** : sur les biens aujourd'hui en Estimation, le registre ne porte
  que des transactions **anciennes** (2017-2021 : 8 compromis « active », 12 offres acceptées, 8 ventes — des biens vendus puis réestimés) ;
  **0 depuis le 01/01/2026, 0 née dans l'app**. ➡ Le blocage ne gênera aucun usage réel ; il ferme une porte qu'on ne prend que par erreur
  (une offre posée sur une estimation **change son statut** : Estimation → Sous offre, mesuré au 24/10).
- **Les transactions anciennes ne sont pas touchées** : le patch ne regarde que la **création** ; modifier, supprimer, Actif, Clos passent.
- **Le bien d'essai** de la répétition (10000009 / 63331) est toujours en Estimation, **0 transaction, 0 travail en cours** : la répétition
  joue telle quelle.
- **L'écran** cache déjà les boutons sur une Estimation (poussé le 24/10) et traduit le refus `transaction_sur_estimation` (`api.ts` l. ~10500).

#### ✅ Point 1 — POSÉ ET ALLUMÉ le 26/10 *(Frédéric : « les trois »)*, joué par moi
- **Répétition** : **« ESSAI ANNULÉ -- 7 sur 7 »** (éteint, une offre sur l'Estimation passe : le défaut ; allumé : offre, compromis, vente
  refusés ; « Actif » accepté ; une offre sur un bien Actif acceptée ; l'inverse rend 44697dd5). Vérifié après : empreinte d'avant, pas
  d'interrupteur, 63331 en Estimation, 0 ligne, 0 travail.
- **Patch** : contrôles **3 sur 3 « OK »** — empreinte **93be71b4**, droits et SECURITY DEFINER inchangés, interrupteur éteint.
- **Interrupteur `transaction_refusee_sur_estimation` = on** à 07:50 (heure de Paris).
- **Preuve sur la vraie fonction allumée**, dans une transaction annulée, au nom de Frédéric : offre sur 63331 → **« transaction_sur_estimation :
  ce bien est en Estimation… passez-le d'abord en Actif »** ; offre sur le bien Actif 1337936 → **acceptée**. Vérifié après : les deux biens
  inchangés, 0 ligne neuve, 0 travail.
- **Retour arrière** : `update app_setting set value = 'off' where key = 'transaction_refusee_sur_estimation'`, ou le patch inverse.

### Point 2 — LA PIÈCE 5 (les acquéreurs projetés dans les liens d'un contact) : audit du 26/10, lecture seule

**La vue aujourd'hui** (`app_contact_relations_current`, `security_invoker`, 18 colonnes) : branche 1 = mandants / propriétaires depuis
`app_relation` (notre registre) ; branche 2 = `app_contact_relation_current WHERE role_contact LIKE 'acquereur%'` (la table refaite chaque
nuit depuis Hektor : 13 293 compromis, 11 172 offres, 10 540 ventes = 35 005 liens, tous à notre numéro).

**Qui la lit** (mesuré) :
- **l'écran** : la fiche d'un contact (`loadContactRelations`, `select *` par `hektor_contact_id`), les invités d'un RDV par bien
  (`hektor_contact_id, role_contact, relation_source, last_seen_at` par dossier), les mandants d'un bien (branche 1 seulement) ; les colonnes
  utilisées pour un acquéreur : `role_contact`, `transaction_type / _id / _state / _date / _amount`, `is_active_annonce` (tri et filtre),
  `contact_date_maj` (une date d'activité), `numero_mandat`, `numero_dossier`, `titre_bien`. **`relation_key` n'est lue nulle part** ;
  `relation_source` est transmise, jamais interprétée ;
- **la base** : `app_contact_activite` et `app_unlink_mandant_optimistic` — **branche 1 seulement** (mandants / propriétaires) ;
- **le serveur** : **personne** — la vue est dans `VUES_NON_DESCENDUES` depuis le 12/10 (`pull_from_supabase.py`) ; le script des contacts
  ne la cite qu'en commentaire.

**La projection, comparée colonne par colonne aux 35 005 liens de la nuit** (chaque personne d'une liste par `app_contact_id`, plus le
principal) :
| colonne | écart | explication |
|---|---|---|
| annonce, dossier, date de la transaction | **0** | identiques |
| `is_active_annonce` | règle trouvée | la nuit = « le bien n'est PAS dans l'index des archives » (0 exception sur 35 005) — on recopie la règle |
| état d'une vente | 10 540 | la nuit écrit le mot « vente » ; le registre laisse vide → on recopie « vente » |
| montant d'une offre | 11 117 | la nuit n'en porte **aucun** ; le registre l'a → **en plus**, visible sur la fiche (à trancher : le montrer ou non) |
| numéro de mandat | 20 | la nuit porte le mandat **courant** du bien, le registre celui **de la transaction** (8377 : 18469 / 16931 ; 24113 offre 32849 : 18787 / 1) — le registre est le juste |
| `contact_date_maj` | 1 973 | la date de mise à jour du contact, prise à des heures différentes (la nuit / la fiche) — sans effet |
| liens en plus | 17 → **3** | 14 sont des transactions que Hektor ne liste plus (`present_in_hektor = false`) : **on les écarte**, comme la nuit ; restent 3 offres d'essai nées dans l'app (24933) |
⚠ **Correction** de ce que j'avais écrit au §16 : 47146 et 62097 ne sont pas des offres nées dans l'app, ce sont des transactions retirées chez
Hektor.

**La vitesse — le vrai sujet** (mesuré par `EXPLAIN ANALYZE`) : la fiche d'un contact lit ses liens à chaque ouverture.
- projection naïve (déplier les 31 103 listes) : **0,36 s** ;
- projection en deux parts (le principal par sa colonne ; les co-acquéreurs **seulement dans les 2 451 listes à plusieurs personnes**) :
  **0,12 s** sans index ;
- avec **deux index** sur le registre (le principal par son numéro en texte ; un index partiel sur les listes à plusieurs personnes) :
  quelques millisecondes attendues — **à mesurer après la pose** (la table de nuit répond aujourd'hui par index).

**Le lien avec le point 4** : le worker réécrit la liste d'acquéreurs, en journée, sans notre numéro → un **co-acquéreur** d'une transaction
créée le matin n'apparaîtrait qu'après la nuit (le principal, lui, apparaît tout de suite : sa colonne `app_contact_id` est posée au clic).

### La proposition — à arbitrer par Frédéric
1. **Patch de base** (inverse + répétition) : les deux index (additifs), puis `create or replace view` : **la branche 1 inchangée au caractère
   près**, la branche 2 = la projection (mêmes 18 colonnes, mêmes types) — `relation_key` = `aff_<transaction>_<contact>` (unique, lue par
   personne), `relation_source` = `registre_transactions`, `transaction_state` = « vente » pour une vente, `is_active_annonce` = pas dans les
   archives, les transactions retirées chez Hektor écartées.
2. **La table de nuit n'est pas touchée** : elle continue d'être refaite ; elle ne sert plus à la fiche. Retour arrière = l'ancienne vue.
3. **Essais** : la répétition compare la vue neuve à l'ancienne sur **tous** les contacts (35 005 liens retrouvés, les écarts du tableau
   seulement), mesure le temps d'une fiche, et rejoue l'inverse.
4. **À trancher** : montrer le **montant des offres** sur la fiche (nouveau) ou le masquer comme aujourd'hui ; et faire le **point 4** avant ou
   après (sinon les co-acquéreurs d'une transaction du jour attendent la nuit).

### Point 2 bis — LES LIENS ENTRE LE REGISTRE DES TRANSACTIONS ET LE REGISTRE DES RELATIONS — audit du 26/10 *(Frédéric : « audite les liens possibles entre le registre des transactions et le registre des relations de mon app »)* — lecture seule

**Les deux registres** :
- **des relations** (`app_relation`, `relation_ledger.py`, 30/09) : **personne ↔ bien**, un seul fait « propriétaire du bien » (libellé mandant
  si le bien a un numéro de mandat, propriétaire sinon), quatre numéros (`app_contact_id`, `hektor_contact_id`, `app_dossier_id`,
  `hektor_annonce_id`), *delete-never*, deux plages ; écrit **la nuit** (propriétaires de l'annonce chez Hektor) et **au clic** (lier, créer,
  retirer un mandant) ; ⛔ **pas d'acquéreurs, par décision du 30/09** ;
- **des transactions** (`app_affaire_ledger`) : **personne ↔ affaire** — l'acquéreur principal (`app_contact_id` + `hektor_acquereur_id`), la
  liste des acquéreurs, **la liste des mandants de la transaction** (`mandants_json`), les notaires.

**Les liens, un par un (mesurés le 26/10)** :
| | le lien | état |
|---|---|---|
| L1 | **les mêmes personnes, sous leurs deux numéros** | relations : les quatre numéros ✅ · transactions : principal ✅, liste des acquéreurs ✅ (pièces 1-2), notaires ✅ (pièce 3), ⚠ **liste des MANDANTS : aucun de nos numéros** — **58 550 personnes** (31 307 sur les compromis, 27 243 sur les ventes) ne portent que le numéro de Hektor |
| L2 | **les acquéreurs** | absents du registre des relations par décision ; la fiche d'un contact les lit dans la table de nuit → **la pièce 5 les projette depuis le registre des transactions** (35 005 / 35 005) |
| L3 | **les mandants, deux sources** | le mandant **du bien** (relations) et les mandants **de la transaction** (transactions, relus chez Hektor) — sur 2026 : **ventes 731 / 735, compromis 593 / 606** se retrouvent dans le registre des relations (17 non) ; la liste des mandants d'une transaction ne contient **pas** l'acheteur (1 cas sur 86 compromis, 1 sur 87 ventes depuis le 17/07) |
| L4 | ⚠ **l'acheteur rangé « mandant » du bien qu'il a acheté** | depuis le 17/07, Hektor met l'acheteur dans les propriétaires du bien ; notre registre des relations le recopie la nuit → **151 liens, 127 actifs** (le 23/10 : 133 / 115 — il en vient à chaque vente : mai 6 · juin 3 · juillet 31 · août 10 · septembre 32 · octobre 20). Règle de Frédéric : « l'acquéreur reste acquéreur, le propriétaire reste le mandant » → **le défaut des types de contacts**, à traiter après ⑧ (mémoire « l'acheteur rangé mandant ») |
| L5 | **les gestes** | « Retirer un mandant » ne touche que le registre des relations ; « Supprimer la vente » ne retire pas l'acheteur-propriétaire (§35, proposition non décidée) |
| L6 | **les types de l'annuaire** (Mandant > Acheteur > Propriétaire > Acquéreur) | calculés **la nuit** depuis la table de nuit (`relation_roles_json`, `build_contacts_layer.py`) — **la pièce 5 ne les change pas** ; L4 les fausse (l'acheteur devient « Mandant ») |
| L7 | **l'activité d'un contact** (`app_contact_activite`) | lit les biens dont il est mandant/propriétaire (branche 1) → L4 y fait entrer les biens achetés |

**Ce que la pièce 5 règle et ne règle pas** : elle règle **L2** (les acquéreurs lus dans notre registre des transactions, à l'instant et à
la coupure). Elle ne règle **ni L1-mandants** (une « pièce 2 » pour `mandants_json`), **ni L4 / L6 / L7** (la règle d'import de l'acheteur,
chantier des types).

- ✅ **R4 — le premier passage du moniteur (26/10, 08:49 heure de Paris) a ÉCRIT les deux sentinelles** : `data.affaire_ecart` **ok** (0, seuil 0) et `data.affaire_personne_ecart` **ok** (0), `observed_at` 07:49:10 UTC — une vraie écriture, à la même seconde que les sœurs (`data.contact_modif_ecart` 07:49:09). Ni « illisible », ni lot refusé.

### Point 4 — la relecture de jour du worker : ✅ FAIT par le chantier 2 b des types (26/10)
`GARDER_NOS_NUMEROS_A_LA_RELECTURE` (worker, `poserNosNumerosDansLaListe`), actif depuis le redémarrage du 26/10 à 10:57 : les listes
relues chez Hektor gardent nos numéros, sans attendre la nuit (note des types §11). Le point 2 (pièce 5) est fait par **la table des
parties** (même note §15-18).

### Point 5 — LES BOUTONS DE LA MODALE (§42) : audit REFAIT le 26/10 au soir, sur le code ACTUEL — lecture seule, rien codé
*(Frédéric : « dans l'ordre du chapitre, suis le plan de dev » ; le §42 date du 24/10, les §43 et §46 l'ont suivi le même jour)*

| # | l'incohérence du §42 | état au 26/10 (code et base relus) |
|---|---|---|
| 1 | « Accepter » une offre déjà acceptée, « Refuser » une offre déjà refusée | ⚠ **le §42 se trompait sur le danger** : la base répond `deja_dans_cet_etat` et **n'envoie rien chez Hektor** (« on ne renvoie pas de travail pour rien », depuis le 16/09, `cd0d767`) ; l'écran affiche « Cette transaction est déjà dans cet état — rien n'a été envoyé » (`App.tsx:18095`). Reste : **un bouton inutile** — sans danger |
| 2 | « Envoyer vers Offre » sur un bien **engagé** (offre acceptée ou compromis en cours) | ⬜ **toujours possible**. L'écran ne garde que compromis et vente (`avisGardeFouSaisie`, `genre === 'offre'` → aucune garde) ; **la base n'a aucune garde** non plus (`app_change_annonce_status_optimistic` ne refuse que : archive, hors parc, Estimation, droits). Contraire à la règle du 08/09 (« plusieurs offres, mais plus quand compromis ouvert ou offre acceptée »), appliquée au seul « Choisir » |
| 3 | « Modifier » sur une vente | ✅ **tranché le 24/10 (§43) : « on ne touche pas »** — reste |
| 4 | « Envoyer vers Actif » / « Clos » sur un bien **vendu** | ⬜ **toujours affichés** (§46 ne ferme que Offre / Compromis / Vendu). « Actif » remettrait le bien en vente chez Hektor **et la diffusion à 1** |
| 5 | le vieux message « Modifier chez Hektor reprend celle-là… » | ⬜ **toujours affiché** dès qu'une transaction est choisie (`App.tsx:22094`), y compris quand « Modifier » est caché (compromis d'une chaîne vendue) |
| 6 | Pilotage → Diffusion muet sur un bien vendu (§40) | ⬜ **toujours muet** : `handleSetSelectedDossierDiffusable` (`App.tsx:19328`) sort sans un mot quand `selectedDossier` est vide (un bien vendu n'est plus dans `app_dossier_current`) — échec silencieux, famille ④ |

**Ce qui demande une décision de Frédéric** : 2 (bloquer une nouvelle offre sur un bien engagé — à l'écran seulement, ou aussi en base ?
⚠ dans le métier, une « offre de secours » sur un bien sous compromis existe ; la règle du 08/09 dit non) · 4 (cacher Actif / Clos sur un
vendu, ou les garder avec un avertissement — « Actif » sur un vendu peut être voulu pour une vente annulée, mais le chemin prévu est
« supprimer la vente ») · 1 (cacher le bouton inutile, ou le laisser puisqu'il ne fait rien).
**Ce qui est une simple correction d'affichage** (aucune décision de fond) : 5 (n'afficher le message que si « Modifier » est là) et 6 (dire
pourquoi le bouton ne fait rien, ou le faire marcher par le numéro Hektor du bien vendu).

#### Point 5 — LES DÉCISIONS DE FRÉDÉRIC (26/10 soir) : « oui fais 5 et 6 · pour 2 audit de nouveau […] attention · 1 oui · 4 NON LAISSE »

**✅ n° 1, 5, 6 CODÉS — écran seulement, NON POUSSÉS** (`App.tsx`, +54 −6, CRLF conservés)
- **n° 1** `gesteOffreSansEffet()` : « Accepter » est caché sur une offre `accepted`, « Refuser » sur une offre `refused` — **la même
  comparaison que la base, au mot près**. Restent : « Accepter » une offre refusée (08/09), « Refuser » une offre acceptée (le chemin pour
  corriger son montant, 13/10). États réels mesurés : accepted 9 993 · refused 1 123 · proposed 28 · vide 54.
- **n° 5** `modifierChezHektorPossible()` : une seule règle pour le bouton « Modifier chez Hektor » ET son message.
- **n° 6** les boutons **Diffusion** et — ⭐ **son jumeau trouvé en chemin** — **Validé** du panneau Pilotage disent maintenant pourquoi ils ne
  font rien sur un bien vendu ou clos (au lieu de sortir sans un mot), et où le faire (la fiche Hektor).
- **Essais** : `apps/hektor-v1/test_boutons_modale_point5.cjs` **20/20** (le vrai code découpé dans `App.tsx` ; témoin inverse des deux règles
  d'avant ; 2 mutants attrapés) · `test_rubrique_affaires_complete.cjs` toujours vert · `npm run build` vert.
- **n° 4** : laissé, par décision. **n° 3** : tranché le 24/10.

**🔎 n° 2 — AUDIT REFAIT : une nouvelle offre sur un bien ENGAGÉ** *(Frédéric : « normalement on ne peut plus ajouter une offre sur un dossier
chaîné avec un compromis ou une vente […] mais on a peut-être laissé cela soit par oubli, soit pour une bonne raison, donc attention »)*
- **La règle écrite** : la sienne, le 08/09 — « il peut y avoir plusieurs offres, mais **plus possible quand compromis ouvert ou offre
  acceptée** » (`bienEngage`, `App.tsx`). La vente n'y entre pas (elle FERME son dossier : un bien revendu des années plus tard est libre —
  son objection du 08/09).
- **Pourquoi la création est restée ouverte** : le commit `a9c6d02` (08/09) n'a appliqué la règle qu'au bouton « Choisir » et dit « les
  autres genres gardent leur comportement d'origine ». **Aucune note ne donne de raison** de laisser la création ouverte → **un oubli**, selon
  toute vraisemblance. La base n'a aucune garde non plus (`app_change_annonce_status_optimistic` ne refuse que : archive, hors parc,
  Estimation, droits). ⚠ Le garde-fou du worker (31/08) « ne bloque PAS l'offre » : c'était pour les offres **concurrentes** sur un bien
  libre (normal), pas pour un bien engagé.
- **⚠ CE QUE LA VRAIE VIE MONTRE (registre, 2026)** : **11 offres sur 10 vrais biens** ont été posées **dans Hektor** pendant qu'un compromis
  était ouvert — deux familles :
  - **la régularisation** : l'offre ACCEPTÉE saisie **après** son compromis (59183 : compromis 02/03, offre acceptée 09/03, vente 02/06 ;
    43437, 1970) — la même affaire, saisie dans le désordre ;
  - **l'offre de secours** : une offre « proposée » pendant le compromis d'un autre acquéreur (17640, 28542, 61509), ensuite refusée ou restée.
- **⚠ LE PIÈGE DES VIEUX COMPROMIS** : 22866 a reçu une offre **aujourd'hui** alors qu'il porte un compromis « en cours » **de 2009** jamais
  clos ; parmi les biens en cours, **3** ont un compromis ouvert d'avant 2025, et **3** sont incohérents (2 « Sous offre » et 1 « Actif » avec
  un compromis ouvert). Une garde stricte les bloquerait **à tort**.
- **À TRANCHER PAR FRÉDÉRIC** : bloquer à l'écran (comme 2.2c, avec le bandeau et le geste qui débloque) — ou **avertir sans bloquer**
  (la régularisation et l'offre de secours restent possibles) ; et la base, oui ou non.

#### Point 5 n° 2 — « peut-on toujours refuser les AUTRES offres ? » : audit refait (26/10 soir, Frédéric : « refais un audit, cela me semble bizarre, cherche dans mes notes ou l'historique »)
- ⛔ **CORRECTION DE MON AUDIT PRÉCÉDENT** : « 22866 a reçu une offre aujourd'hui » est **FAUX**. Les offres sans date portent l'heure de
  la nuit (`2026-10-26T04:24:57Z`, ~30 offres 6xxx de 2009-2010 sur les annonces 22xxx) : ce n'est pas une date d'offre. Le « piège des
  vieux compromis » reste vrai pour les 3 biens « Sous compromis » d'avant 2025, pas pour 22866.
- **DEUX DÉCISIONS QUI SE CONTREDISENT À L'ÉCRAN** :
  - **08/09** (`a9c6d02`, liste 2.2) — sur un bien **engagé**, **aucune** offre ne se « Choisit » (« on bloque tout ») : la crainte était
    d'**accepter** une seconde offre et d'engager le bien deux fois. La modale vise alors l'offre retenue, et elle seule.
  - **16/09** (`cd0d767`, liste 3.6) — on verrouille l'offre du dossier qui porte un compromis ; « **les offres écartées des autres
    acquéreurs restent refusables, c'est le geste normal du métier quand une offre est retenue** ». La base l'applique
    (`app_geste_affaire_optimistic` ne lit que le dossier de CETTE offre).
  - ➡ **L'intention du 16/09 n'est vraie que dans la base** : à l'écran, une offre écartée ne peut pas être visée (`Choisir` caché par
    `bienEngage`, `App.tsx` « QUI PEUT-ON DESIGNER »), donc pas refusée. Ce n'est pas une règle voulue : c'est la règle du 08/09 (faite pour
    « accepter ») qui empêche aussi « refuser ».
- **Les cas 8 et 10 du protocole du 01/09** (« deux offres, une acceptée, une refusée » ; « créer une offre alors qu'un compromis existe »)
  n'ont **jamais été joués** — aucun résultat écrit.
- **La vraie vie** (registre, depuis 2024) : parmi les offres posées dans les 6 mois avant une offre acceptée du même bien, **66 refusées**
  (57 biens, 28 en 2026), 3 acceptées, 3 encore en cours. Refuser les concurrentes est **le geste courant** — fait aujourd'hui dans Hektor, ou
  avant l'acceptation. Sur les 140 biens engagés en cours, **0** offre concurrente reste ouverte.
- **Proposition** (n'attend que « vas-y ») : sur un bien engagé, ① masquer « Envoyer vers Offre » (la règle du 08/09 appliquée à la
  création), ② permettre de **choisir une autre offre encore en cours pour la REFUSER seulement** — « Accepter » reste caché sur elle (la
  crainte du 08/09), le verrou du 16/09 reste sur l'offre du dossier engagé. Écran seulement ; la base le permet déjà.

#### ✅ Point 5 n° 2 CODÉ — écran seulement, NON POUSSÉ *(26/10 soir, Frédéric : « vas-y : sur un bien engagé, masque « Envoyer vers Offre » et permets de choisir une offre écartée encore en cours pour la refuser seulement »)*
- `nouvelleOffreFermeeSurBienEngage()` : sur un bien **engagé** (`bienEngage`, la règle du 08/09 — la vente n'y entre pas), « Envoyer vers
  Offre » est **masqué** ; la touche Entrée est gardée elle aussi (même message que le bandeau). Le bandeau « Ce bien est déjà engagé » le dit.
- `offreEcarteeSurBienEngage()` : une offre **encore en cours** (vivante, ni acceptée ni refusée) d'un **autre dossier** que celui qui porte
  un compromis ou une vente → elle **se choisit**, et pour elle **seul « Refuser »** s'affiche (ni « Accepter », ni « Modifier » et son
  message). Le verrou du 16/09 reste maître dans son dossier. La base le permettait déjà.
- **Essais** : `apps/hektor-v1/test_boutons_modale_point5.cjs` **38/38** (n° 1, 2, 5 ; 5 scénarios de biens : libre, engagé par une offre,
  engagé par un compromis, revendu, offre disparue de Hektor ; 4 témoins inverses ; 5 mutants attrapés) · `test_rubrique_affaires_complete.cjs`
  vert · `npm run build` vert · CRLF conservés.
- ⚠ **Effet de bord voulu, vu par l'essai** : sur un bien qui a un compromis ouvert, une offre en cours d'un autre dossier n'a plus de
  « Modifier » (elle se refuse seulement).
- **Portée aujourd'hui** : ~140 biens en cours sont engagés (« Envoyer vers Offre » masqué) ; **0** n'a d'offre écartée en cours.
- ⏰ Après le push : ouvrir la modale d'un bien « Sous compromis » → pas de « Envoyer vers Offre », bandeau à jour.
