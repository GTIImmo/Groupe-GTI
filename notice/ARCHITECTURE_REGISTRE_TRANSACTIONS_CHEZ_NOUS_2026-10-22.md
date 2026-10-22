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
