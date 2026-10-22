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
