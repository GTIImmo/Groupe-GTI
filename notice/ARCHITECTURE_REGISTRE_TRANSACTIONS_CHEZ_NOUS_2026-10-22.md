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
