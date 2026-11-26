# Audit de la garde de la descente — 26/11/2026

> **Chantier annexe, ouvert le 26/11.** Audit LIMITÉ au mécanisme de bascule de
> `phase2/sync/pull_from_supabase.py` (la recopie nocturne Supabase → `phase2.sqlite`).
> Il ne porte sur aucun des huit objets métier ni sur aucun geste chez Hektor.
> **Rien n'a été écrit** : ni en base, ni chez Hektor, ni dans le Sheet, ni dans le code.
> `phase2.sqlite` lu en `mode=ro`, Supabase lu par l'outil MCP (lecture seule), mesures
> faites entre 17:00 et 17:15, hors de la fenêtre 04:00-07:30.
> Code lu à l'état de `092eb03` (17:04) : les deux commits de la règle des dates
> (`c75ccf5`, `092eb03`) sont dedans ; ils ne touchent que `main()`, au-delà de la l. 1139.

---

## 1. Le mécanisme, tel que le code le fait

- **Le compte** : `SupabaseReader.count()` (l. 369-381) lit le total dans l'en-tête
  `Content-Range` d'une requête `?select=*&limit=1` avec `Prefer: count=exact`, et rend
  `None` sur toute exception, ou si l'en-tête ne porte pas de total chiffré.
- **Ce que « toute exception » veut dire** : `count()` passe par `get()` (l. 267-339), qui
  fait **4 essais**. Pour une coupure réseau, les pauses font ≈ 9 s en tout ; pour une
  passerelle 520-524, jusqu'à ≈ 36 s. Un **refus 4xx n'est jamais réessayé**.
- **La vérification** : `attendu = reader.count(distant)` (l. 737), puis la relecture par
  rang (l. 760) et le refus (l. 778), **tous deux conditionnés par `attendu is not None`**.
- **La bascule** : `DROP` de l'ancienne puis `RENAME` de la `__tmp` (l. 788-789).
- **L'échec** : `marquer_echec()` (l. 914) ne supprime que la `__tmp` ; l'ancienne copie
  reste. Le message dit toujours « l'ancienne copie est conservée » (l. 783-785), qu'elle
  existe ou non.
- **La découverte** : la liste des cibles vient de la spécification de l'API (`schema()`,
  l. 341). Un objet absent de l'API n'est **pas une cible** : rien ne se passe pour lui.
- **Le delta** (l. 868-872) traite déjà un compte `None` comme un doute : il retombe sur la
  copie complète. Seule `copy_table` saute la vérification.

## 2. L'inventaire, ventilé

**284 objets suivis** dans `sb_pull_state`, **3 613 945 lignes** au dernier état.
- **279 existent au serveur** : 226 tables et 53 vues.
- **5 n'existent plus au serveur** (voir faille D).

Leur dernière descente :
- **238 le 26/11** : les cibles de ce matin, dont 3 en échec.
- **41 le 12/10** : les vues de `VUES_NON_DESCENDUES`, figées depuis.
- **5 plus anciennes** : 24/08, 31/10, 01/11, 06/11, 10/11. Ce sont les 5 disparus.

Total : 238 + 41 + 5 = 284.

- **72 objets à nom daté**, pour 281 017 lignes (8 %) : 69 existent au serveur, et 3 ont
  disparu.
- À partir de ce soir, **169 cibles** : 238 moins les 69 sauvegardes datées.
- **0 table `__tmp`** ne traîne en local.

**Les journaux** : 34 descentes de `logs/scheduled/descente_*.log`, du 28/10 au 26/11.
Ce sont 30 descentes de nuit et 4 lancées à la main (29/10 10:16, 31/10 08:00, 01/11 11:25,
10/11 12:23). S'y ajoutent **88 descentes ciblées** du run de nuit, relevées dans
30 des 33 journaux `quotidien_*.log` (`--table` app_affaire_ledger, app_relation, app_mandat,
app_affaire_console). Il n'existe aucun journal plus ancien que le 28/10.

---

## 3. Faille A — la vérification peut être sautée

**A-t-elle déjà mordu ? Jamais, mesuré, dans la limite des journaux.**
- **88 fois, la lecture a été courte**, et à chaque fois le compte a répondu : 77 relectures
  par rang et 11 refus « copie incomplète ». Tous concernaient des sauvegardes datées.
  - Si une seule de ces 88 fois avait rendu `None`, la copie courte aurait basculé sans un
    mot.
  - Exemple concret : `app_securite_droits_avant_20261008` aurait été remplacée par
    **1 000 lignes au lieu de 2 546**, les 34 nuits. Sa lecture par valeur s'arrête à la
    première page **chaque nuit**, et c'est le compte seul qui la sauve.
- **0 échec réseau ou HTTP** sur les 34 descentes et les 88 descentes ciblées. Aucune
  requête n'a épuisé ses 4 essais ; les 11 échecs sont tous « copie incomplète ».
- **Deux « chutes puis remontées »** pouvaient faire penser à A. Elles ont été contrôlées
  au serveur, et elles sont cohérentes avec de vraies suppressions :
  - `app_notification`, le 29/10 à 10:16 : 1 848 lignes posées, et 1 832 lignes encore
    présentes aujourd'hui étaient nées avant cette heure ;
  - `app_rapprochement`, le 11/11 : 56 643 posées, et 53 517 vues avant cette heure sont
    encore là.
- **Limite** : un compte `None` ne laisse **aucune trace** dans le journal. On ne peut donc
  rien affirmer pour les nuits où la lecture était complète, mais ces nuits-là, la faille
  ne coûte rien. Avant le 28/10, il n'y a aucun journal. Or les matins du 15/09 (503
  pendant 1 h 45) et du 01/10 (réponses coupées) ont épuisé les essais : le compte a pu y
  rendre `None`. Ce n'est pas mesurable.

**Ce qu'elle pourrait coûter.** Une copie juste remplacée **en silence** par une copie
tronquée, chaque fois qu'un compte raté tombe la même nuit qu'une lecture courte.
- Depuis la règle des dates, les tables vivantes se lisent en entier (clé primaire). A ne
  mord donc qu'avec une troncature, par exemple :
  - une réponse coupée qui ressemble à une fin de table ;
  - une colonne de parcours nulle dans une vue (l. 718-722) ;
  - surtout, **un plafond de lignes abaissé côté serveur** (« Max rows » < 1 000). Dans ce
    cas, toute table au-delà serait lue en une page et s'arrêterait. Le compte est alors le
    seul juge pour **toutes les tables à la fois**.
- **Qui en pâtit** :
  - le run de la nuit suivante, qui lit ces copies ;
  - la sauvegarde de 08:00, qui passe **après** la descente et garde la copie tronquée.
    La bonne ne reste que dans les sauvegardes des jours d'avant (90 jours pour les tables
    critiques, 28 jours pour l'instantané hebdomadaire).
- Une nuit où le compte répond la répare.

**Le correctif proposé — règle « pas de compte, pas de bascule ».**
- **Le geste** : juste après la l. 737, si `attendu is None`, la table part en échec
  (« comptage impossible chez Supabase — bascule refusée »). L'ancienne copie reste et
  `marquer_echec` fait le reste, comme pour une copie incomplète.
- **L'interrupteur** : une constante `EXIGER_LE_COMPTE = True` en tête du fichier. Avec
  `False`, on retrouve le comportement d'avant.
- **Son risque** : une table dont le compte rate n'est pas rafraîchie cette nuit-là, avec
  un code 1 nommé. La fréquence attendue, mesurée sur 34 nuits, est ≈ 0. Une table qui n'a
  encore aucune copie locale attend la nuit suivante.

**Ce que ça pourrait casser ailleurs, vérifié :**
- le delta : inchangé, il traite déjà `None` comme un doute ;
- le patron du 26/11 (`descendre_les_22_avec_temoin_positif_2026-11-26.py`) : son
  enveloppe lève elle-même sur `None`, **avant**, donc il reste compatible ;
- les 4 descentes ciblées du run : ce sont toutes des `Invoke-OptionalStepWithRetry`, non
  bloquantes, mais à **un seul essai** (correction du soir) : `MaxAttempts` vaut 1 par
  défaut (`run_full_pipeline.ps1:304`), et aucune des 4 ne le change. Un compte raté fait
  sauter l'étape, et le run continue sur la copie de la veille, exactement comme
  aujourd'hui quand une page échoue. ⚠ Voir la règle 0 (§ 10) : ses lecteurs doivent alors
  savoir que la copie est celle de la veille ;
- le banc `test_descente_sans_cle_primaire.py` : son faux `count` rend toujours un nombre,
  il est donc inchangé ;
- le texte « incomplete », qu'il vérifie, n'est pas touché ;
- aucun autre fichier du dépôt ne lit ces messages (cherché dans `*.py`, `*.ps1`, `*.js`,
  `*.ts`, `*.tsx` et `*.sql`).

**Le témoin inverse :**
- un faux lecteur dont `count` rend `None` : `copy_table` DOIT lever, l'ancienne table DOIT
  garder ses lignes et son empreinte, aucune `__tmp` ne doit rester, et `sb_pull_state`
  DOIT être marqué ;
- le même lecteur avec le bon compte DOIT basculer ;
- avec l'interrupteur à `False`, il DOIT basculer comme avant. C'est la preuve que
  l'interrupteur coupe.

**Le retour arrière** : l'interrupteur à `False`, ou `git revert` du commit.

---

## 4. Faille B — zéro se compare à zéro

**A-t-elle déjà mordu ? Jamais, mesuré.**
- **Les 46 copies locales à zéro**, toutes comparées au serveur :
  - **28 descendues ce matin** (23 tables, 5 vues) : **toutes à 0 au serveur**. Parmi
    elles, les huit suspectes nommées dans le brief : `app_sync_run`,
    `app_summary_snapshot`, `app_affaire_carnet_decision`, `app_dossier_v1`,
    `app_dossier_detail_v1`, `app_work_item_v1` et `app_filter_catalog_v1` sont des
    **tables**, vides. `app_latest_sync_run` est une vue figée, vide aussi.
  - **17 vues figées depuis le 12/10** (`VUES_NON_DESCENDUES`, plus jamais recopiées).
    15 sont à 0. **Deux ont des lignes aujourd'hui**, mais elles ne descendent plus par
    décision. Ce n'est donc pas une morsure de B :
    - `app_console_action_abandonnees` : 1 050 lignes aujourd'hui. Reconstitué au 12/10 :
      **aucun travail connu ne l'aurait remplie** ce matin-là. Le plus ancien travail en
      erreur encore présent date du 13/10, et la purge du 15/10 n'a archivé que des
      travaux nés après le 11/10. C'est une reconstitution forte, pas une preuve : un
      travail relancé à la main depuis a pu changer de statut.
    - `app_contacts_sans_numero` : 4 lignes aujourd'hui. **Non reconstituable** : c'est une
      vue de calcul sur 19 tables.
  - **1 disparue du serveur** : `app_notaire_interlocuteur`, renommée le 06/11. Celle qui
    lui succède est vide elle aussi.
  - Total : 28 + 17 + 1 = 46.
- **L'historique** : en 34 descentes, il y a **6 passages de N > 0 à 0, sur 4 objets**,
  tous légitimes :
  - des files d'attente qui se vident : `app_search_provisional` (1 → 0, trois fois) et
    `app_relation_provisional` (1 → 0) ;
  - des vues d'écarts corrigées : `app_v_negociateur_signaux` (13 → 0, le 18/11) et
    `app_v_repartition_orpheline` (26 → 0 ce matin : la vague du 25/11, « orphelines 0 »).
  - Les 4 sont à 0 au serveur aujourd'hui.

**La vraie nature de B, à corriger dans le brief.** La descente lit avec `service_role`,
qui a `rolbypassrls = true` (mesuré). La RLS, en mode simple **comme en FORCE**, ne peut
donc pas lui faire lire un faux zéro.
- **Si l'API rend 0, la source est vraiment vide**, sauf si la clé changeait un jour pour
  une clé `anon` ou `authenticated` : là, toutes les tables protégées liraient 0 = 0.
- **Le vrai risque de B est donc une perte RÉELLE en amont** : un `TRUNCATE` ou un
  `DELETE` de trop, un patch, une migration. La descente recopie fidèlement la perte le
  lendemain matin.
- La copie locale, qui est la seule copie hors de Supabase de ce que l'app invente, est
  alors remplacée. La sauvegarde de 08:00 garde la copie vide.
- Une chute massive qui ne va pas jusqu'à zéro a le même effet : **zéro n'est que le cas
  extrême d'une chute**.

**Ce qu'elle pourrait coûter.** Une perte en amont recopiée en silence. On ne la rattrape
que par les sauvegardes des jours précédents, et seulement si quelqu'un la voit à temps.

**Le correctif proposé — règle « une chute ne se croit pas sans témoin ».** Le témoin
positif, c'est **la copie d'avant**.
- **La règle** : si l'ancienne copie locale avait **au moins 100 lignes** et que la neuve
  en a **moins de la moitié** (zéro compris), la bascule est refusée. L'ancienne reste, et
  l'échec est nommé avec un code 1.
- **Quand la chute est vraie**, on l'accepte par un geste humain nommé :
  `--accepter-chute <table>`, répétable.
- **L'interrupteur** : `SEUIL_CHUTE = (100, 0.5)` ; avec `None`, la règle est éteinte.
- **La mesure des seuils** sur les 34 descentes : **0 fausse alerte**.
  - Au-dessus de 100 lignes, les chutes légitimes font au plus 2,6 %
    (`app_mandat_broadcast_current`, 1 407 → 1 370) ; `app_rapprochement` a chuté de
    0,6 %.
  - Les chutes légitimes à zéro portaient toutes sur 26 lignes au plus.
- **Son risque** :
  - une purge massive et voulue en amont laisse la table sur sa copie d'avant, avec un
    code 1, jusqu'au geste humain. C'est du bruit, jamais une perte ;
  - sous 100 lignes, aucune protection. C'est un choix : les 6 chutes légitimes sont là.
- **L'autre voie, que je ne recommande pas maintenant** : un compte indépendant par le
  pooler pour chaque table, comme le T0 du patron. Il protège d'un mensonge de l'API, pas
  d'une vraie perte en amont, et il ouvre une seconde connexion chaque nuit.

**Ce que ça pourrait casser ailleurs :**
- le delta : il ne rétrécit jamais (`INSERT OR REPLACE`). Son filet n° 1 retombe sur
  `copy_table`, où la garde s'applique, et c'est voulu ;
- les descentes ciblées : non bloquantes ;
- les sauvegardes datées : elles ne descendent plus, donc aucun effet.

**Le témoin inverse :**
- une ancienne copie de 500 lignes et une lecture de 0 avec un compte de 0 : DOIT lever et
  garder les 500 ;
- 300 lignes sur 500 : DOIT passer ;
- 99 → 0 : DOIT passer (sous le seuil) ;
- avec `--accepter-chute` : DOIT passer ;
- avec l'interrupteur éteint : DOIT passer.

---

## 5. Faille C — la pagination sans unicité

**A-t-elle déjà mordu ?**
- **Sur les sauvegardes, oui, mais jamais en silence** : 77 relectures par rang et 11 refus
  depuis le 28/10, tous sur des tables à nom daté. Le compte était là à chaque fois.
- **Sur les données vivantes, jamais : mesuré.**
  - Sur 157 tables vivantes, **155 ont une clé primaire**.
  - Les 2 sans clé tiennent dans une seule page de 1 000 : `app_console_job_error_archive`
    (233 lignes, figée depuis le 15/10) et `app_affaire_partie_ecart_releve` (0 ligne).
    Le parcours par valeur ne peut rien y sauter.
  - **12 vues descendent encore chaque nuit** (les 53 vues, moins les 41 de la liste).
    11 font moins de 1 000 lignes, donc une seule page.
  - La 12e, `app_v_mandat_statut`, fait 25 175 lignes, et sa première colonne
    `register_row_id` est **unique** : 25 175 valeurs distinctes, aucune nulle.

**Ce qu'elle pourrait coûter.** Seule, C n'est **jamais silencieuse** tant que le compte
répond. L'écart est soit réparé par la relecture (jusqu'à 15 000 lignes), soit refusé
bruyamment. **C ne devient silencieuse qu'avec A.** Fermer A ferme donc la part
silencieuse de C.

**Le correctif proposé : rien à coder maintenant.**
- La règle des dates (`c75ccf5`) sort de la nuit, dès ce soir, les 67 sauvegardes sans
  unicité.
- **Risque dormant** : une vue dont la première colonne se répète et qui passerait
  1 000 lignes, ou une archive sans clé qui se remplirait.
- Le remède, ce jour-là, est déjà écrit dans le code (l. 208-209) : une clé primaire à la
  création.
- Mettre les 12 vues dans `VUES_NON_DESCENDUES` n'est pas proposé ici. La santé les lit
  au serveur, mais je n'ai pas prouvé qu'aucun script local ne lit leur copie.

---

## 6. Faille D — les objets suivis qui ont disparu du serveur

**5 des 284 objets suivis n'existent plus au serveur**, tous retirés par un geste délibéré :
- `tmp_etape12_avant` : supprimée le 24/08 par
  `supabase/patch_fermer_acces_public_2026-08-24.sql`. Sa copie locale de 39 lignes est
  gardée.
- `app_notaire_interlocuteur` : renommée le 06/11 en `app_partenaire_interlocuteur`
  (`patch_partenaire_interlocuteur_2026-11-06.sql`). Sa copie locale fait 0 ligne et est
  figée depuis le 06/11.
- `app_classeur_lien_avant_regel_20261029`, `..._20261031` et `..._20261109` : sauvegardes
  du gel du classeur.
  - `20261031` a été exportée dans `supabase/rollback/` puis supprimée, sur sa décision du
    01/11.
  - Pour `20261029` et `20261109`, **je n'ai pas retrouvé d'export** : non mesuré, à
    vérifier côté classeur.
  - Aucune des trois n'a jamais eu de copie locale : toutes leurs descentes ont échoué
    (les 30 et 31/10, le 01/11, le 10/11).

**Ce que la descente en fait.** Rien, et en silence. Un objet absent de l'API n'est pas une
cible :
- pas une ligne au journal ;
- aucune suppression : la copie locale reste, figée, et c'est le bon comportement ;
- `sb_pull_state` garde son dernier état pour toujours.

**A-t-elle déjà mordu ?** Aucune donnée perdue : les 5 cas sont des gestes voulus. **Mais
l'information est fausse à 6 endroits** : 6 lignes de `sb_pull_state` disent
« l'ancienne copie est conservée » alors qu'**aucune copie locale n'a jamais existé**.
- 3 sont ces gels du classeur, que **plus aucun passage ne nomme** : elles ne sont ni dans
  l'API ni dans la liste des sauvegardes écartées.
- 3 sont les sauvegardes du 25/11. Depuis `092eb03` (17:04), elles sont nommées
  « AUCUNE COPIE LOCALE » à chaque passage.

**Ce qu'elle pourrait coûter.** Le jour où une table disparaît en amont **par erreur**, sa
copie locale devient la dernière, et personne n'est prévenu.

**Le correctif proposé.** Deux petites choses, additives, sans changer le comportement :
- **D1** : à chaque passage, la descente déclare les objets suivis absents de l'API, avec
  l'état de leur copie locale (« N lignes gardées » ou « aucune copie »). Comme les
  sauvegardes écartées, cela n'entraîne pas de code 1 : une suppression voulue est normale.
- **D2** : le message de la garde dit vrai. Il ne promet « l'ancienne copie est
  conservée » que si la table locale existe ; sinon il dit « aucune copie locale n'existe ».
  Le mot « incomplete », que le banc vérifie, est gardé.
- **Le risque** : nul. Ce n'est que de l'affichage et un message ; seul le banc lit ce
  texte.

---

## 7. Trouvé en passant, non traité

- **Les 3 sauvegardes de la vague du 25/11** n'existent **qu'au serveur** :
  - `app_affaire_repartition_avant_a2vague_20261125`, `..._avant_vague_20261125_080931` et
    `..._090205`, de 17 907 lignes chacune ;
  - leur seule descente, le 26/11, a été refusée, et la règle des dates ne les descendra
    plus ;
  - le précédent du 01/11 est l'export dans `supabase/rollback/`. C'est au chantier du
    classeur de décider.
- **Les codes de sortie de la descente** : un code 1 sur **7 des 34 descentes** (30/10,
  31/10, 01/11, 10/11, 14/11, 15/11, 26/11).
  - C'étaient toujours des sauvegardes neuves, sur leur ou leurs premières nuits ; le 25/11
    était en code 0.
  - « Le code 1 chaque nuit » (brief) et « 3 tables qui échouaient chaque nuit depuis le
    25/11 » (`c75ccf5`) sont donc inexacts : ces 3 tables ont échoué **une seule nuit**.
  - Ce soir, le code 0 est attendu.
- **La sauvegarde de 08:00 passe après la descente** : elle garde la copie du matin, bonne
  ou mauvaise.
- **L'étape 4 du lanceur** (« rattrapage du carnet ») est sortie 2 fois sur 34 en
  `-1073740791` (0xC0000409, arrêt brutal), dont ce matin. Elle est non bloquante, et je ne
  l'ai pas creusée.
- **Les horaires** : la descente part à **06:45** (et non 07:45), puis attend la fin du
  run. Ce matin, elle a vraiment démarré à 06:59.

## 8. Corrections apportées au brief

- **Sur `count()`** : il ne rend pas `None` sur une coupure d'une seconde ; ses 4 essais
  absorbent une panne de ≈ 9 s, et jusqu'à ≈ 36 s pour une passerelle. Il rend `None`
  dans trois cas :
  - une panne plus longue que ses essais ;
  - **tout refus 4xx** ;
  - un `Content-Range` sans total chiffré.
- **Sur les numéros de ligne** : la vérification est aux l. 760 et 778 (et non 746), la
  bascule aux l. 788-789, `marquer_echec` à la l. 914, `count` aux l. 369-381.
- **Sur les « 6 en échec permanent »** : 3 sont des lignes fantômes (objets supprimés au
  serveur, plus tentés depuis le 31/10, le 01/11 et le 10/11). Les 3 autres ont échoué
  **une** nuit, et sortent de la descente ce soir.
- **Sur la RLS** : simple ou FORCE, elle ne touche pas la descente, puisque `service_role`
  passe outre (`rolbypassrls = true`).

---

## 9. Ce qui reste à décider — des règles, une à la fois

Ordre proposé :
1. **A** : la plus grave, la plus petite, et elle ferme la part silencieuse de C.
2. **D** : D2, puis D1.
3. **B**.

**C** n'a rien à coder.

Chaque règle sera écrite **sur son « vas-y »**, en additif, derrière son interrupteur. Elle
sera éprouvée par son témoin inverse **avant** toute nuit, puis commitée localement dans la
branche normale, fichier par fichier, **sans pousser**. Avant chaque écriture dans
`pull_from_supabase.py`, je relis `git log`. Au 26/11 à 17:12, son dernier commit est
`092eb03` (l'autre session : « les trois failles … sont traitées par une autre
session : rien d'autre n'est touché »).

- **Règle A** : « pas de compte, pas de bascule ».
- **Règle D** : « un objet suivi qui disparaît du serveur se déclare, et un message ne
  promet pas une copie qui n'existe pas ».
- **Règle B** : « la chute d'une copie d'au moins 100 lignes à moins de la moitié ne se
  croit pas sans geste humain ».

Aucune ne demande d'écrire en base, de lancer un run, ni de redémarrer quoi que ce soit.
Chacune prendra effet **à la descente suivante**, ce qui ne demande aucun geste de plus.

---

## 10. L'audit en profondeur, le 26/11 au soir

Il a été demandé pour « ne pas faire d'erreur » avant d'écrire les règles. Comme le reste,
il est en lecture seule.

### 10.1 ⛔ Un défaut qui existe déjà, et qui passe AVANT les règles : la règle 0

**Le défaut.** Avant de copier, `copy_table` écrit dans `sb_pull_state`
`derniere_descente = <heure du passage>` et `dernier_echec = 'copie en cours'` (l. 581-588).
Si la copie est ensuite refusée, `marquer_echec` laisse cette date en place. Après un
refus, la date dit donc « aujourd'hui » alors que la copie en place est **celle de la
veille**.

**Les quatre lecteurs qui jugent la fraîcheur sur cette date :**
- `phase2/sync/relation_ledger.py:552-587` : il tourne dans le run de nuit et lève les
  retraits de liens **seulement si la doublure est du jour**. Ce garde-fou existe pour ne
  jamais faire réapparaître un lien retiré la veille. Après un refus, il serait trompé, et
  ferait exactement l'erreur qu'il interdit.
- `phase2/checks/relation_disparue.py:312-316` : la sentinelle juge la doublure
  « périmée ou non » sur la même date.
- `phase2/checks/mandat_un_numero.py:176-186` : elle n'écarte que le cas « copie en
  cours », pas un refus.
- `monitoring/check_gti_health.py:2808-2824` : elle lit la même date, et le maximum de
  toutes les dates comme « heure du dernier passage ».

**A-t-il déjà mordu ? Jamais, mesuré.** En 34 descentes et 88 descentes ciblées, aucune des
trois copies concernées (`app_relation__sb`, `app_mandat__sb`,
`app_contact_search_current__sb`) n'a échoué. Mais **les règles 1 et 4 fabriqueront des
refus** : sans la règle 0, elles armeraient ce piège.

**La règle 0, « la date d'une copie est celle de la copie en place ».**
- **Le geste** : à l'enregistrement « copie en cours », ne plus toucher `derniere_descente`
  d'une ligne qui existe déjà (elle n'avance qu'à une bascule réussie). Une table neuve
  part avec une date vide.
- **Ce que ça change** : un refus laisse la date de la veille, et les quatre lecteurs le
  voient. `relation_ledger` s'abstient et le dit, comme il est écrit.
- **Le risque, mesuré dans le code** : si **toutes** les tables échouaient la même nuit, le
  maximum lu par la santé ne bougerait pas. Elle croirait alors que la descente n'a pas
  tourné. La tâche « GTI Descente », en critique, le dit déjà.
- **Le témoin inverse** :
  - une ligne d'état datée de la veille, puis une copie refusée : la date DOIT rester celle
    de la veille, et `relation_ledger` DOIT s'abstenir ;
  - une copie réussie : la date DOIT avancer.

### 10.2 Les mesures qui confirment les règles 1 et 4

- **Le compte répond, même sur les plus grosses tables.** Un delta n'est validé que si le
  compte a répondu et égale le local (l. 868-872). Or il y a eu **149 deltas réussis en
  34 descentes** sur les cinq tables les plus lourdes : app_console_job_log 30,
  app_rapprochement_score_history 30, app_console_photo 30, app_affaire_console 33,
  app_affaire_repartition 26.
- **Le temps d'un comptage** : de 0,02 à 1,8 s, mesuré au serveur (591 420 lignes pour la
  plus grosse). Les six comptages, faits ensemble à froid, ont pris 19 s.
- **La limite du serveur** : la descente passe par le rôle `authenticator`, qui a
  `statement_timeout = 8s` ; `service_role` n'en a pas.
- **La marge est réelle mais pas énorme à froid.** Avec la règle 1, un comptage hors délai
  donnerait un refus nommé au lieu d'une bascule aveugle.
- **Les purges programmées dans Supabase** (15 tâches pg_cron, relevées) ne touchent que
  de petites files d'attente : les provisoires, les orphelins de recherche, les parcours
  de l'assistant. Aucune ne fait chuter une grosse table : la règle 4 ne criera pas pour
  elles.
- **Une conséquence d'un refus à connaître** : `marquer_echec` met `lignes` à vide. Le
  delta est alors refusé la nuit suivante (`delta_possible`), qui fait une copie complète.
  Pour `app_console_photo`, cela représente environ 964 Mo, d'après le commentaire du 01/10
  (l. 484). C'est déjà le cas aujourd'hui après tout échec.
- **Le banc** `test_descente_sans_cle_primaire.py` part d'une base vide, sans copie
  d'avant : la règle 4 ne change aucun de ses cas.

### 10.3 La sentinelle « GTI Descente » du 26/11 (10:49, 14:52, 16:49)

- **Sa cause** : le code 1 de la descente de 06:45, dû aux trois sauvegardes de la vague
  du 25/11. La règle des dates les écarte dès ce soir. J'ai vérifié que les trois noms
  sont bien pris par l'expression, et ce sont les seuls échecs du matin.
- **Elle a sonné deux fois pour une seule cause**, à cause d'un défaut de la sonde,
  `monitoring/check_gti_health.py` :
  - à 08:49 et à 14:49, la lecture des tâches planifiées par PowerShell a échoué
    (« Impossible de lire les taches planifiees ») ;
  - la sonde n'a donc pas réémis la clé `scheduledtasks:gti_descente`, et la boucle des
    familles (l. 3852-3884) en a conclu « Retour a la normale ». Un e-mail de
    rétablissement est parti à 14:52 (l. 3785-3786) ;
  - la passe de 16:49 a relu le même code 1 et l'a annoncé comme neuf (l. 3779-3784).
  - Conséquence : la première alerte du matin a pris deux heures de retard (10:49 au lieu
    de 08:49), et il y a eu un faux rétablissement.
- **Ce n'est pas la descente du chantier de l'après-midi** : celle-là a été lancée par un
  script, pas par la tâche, et elle a fini en code 0. Le dernier résultat de la tâche est
  resté celui de 06:45 (vérifié : `LastRunTime` 26/11 06:45:01, prochaine 27/11 06:45).
- **Elle s'éteint seule** à la première passe qui suit la descente de demain, si celle-ci
  sort en code 0.
- **Le remède proposé à la sonde**, à part et sur son « vas-y » : « ne pas voir n'est pas
  guérir ». Quand la lecture des tâches échoue, la sonde garde l'état précédent de chaque
  tâche au lieu d'annoncer un retour à la normale.

### 10.4 La même famille, AILLEURS que dans la descente

Un agent a balayé le dépôt à la recherche des autres mécanismes qui remplacent ou élaguent
une copie. Ses conclusions ne sont **pas** la descente ; elles relèvent d'un ou plusieurs
chantiers à part. J'ai **vérifié moi-même** les quatre plus graves ; le reste est
**rapporté, non vérifié**.

**Vérifié dans le code (26/11, au soir) : une chaîne sans seuil, de Hektor jusqu'à l'app.**
1. **Le listing des annonces** (`sync_raw.py:1185-1259`) s'arrête à la première page vide.
   Or `get_json` (`hektor_pipeline/common.py:294-308`) rend n'importe quel JSON, y compris
   une réponse d'erreur en HTTP 200 sans `data`. Les pages au-delà sont ensuite supprimées
   (`prune_raw_listing_pages`, l. 667-676, appelée l. 1791).
2. **Le miroir** : `normalize_source.py:2084` calcule le périmètre à partir de ces pages,
   et `prune_annonce_scope` (l. 755-823) **supprime sans aucun seuil** tout ce qui n'y est
   pas, dans neuf tables. Cela comprend les annonces et leur détail, les offres, les
   compromis et les ventes.
   - Un périmètre vide déclenche un `DELETE` intégral (l. 756-773).
   - C'est contraire à la règle du projet : « le miroir se met à jour, il ne se remplace
     pas ».
3. **Supabase** : la nuit pousse « distant moins local » en suppressions, sans plafond,
   pour les index des archives, des historiques et des brouillons
   (`phase2/sync/push_upgrade_to_supabase.py:1689-1703`). L'option
   `-AllowStaleSupabaseDeletes` est passée chaque nuit (`scheduled/run_quotidien.ps1:53`).
   Seuls les dossiers « stale » ont un plafond, de 500.
4. **L'annuaire des utilisateurs et des agences** : il est purgé chaque nuit de tout ce que
   la lecture Hektor n'a pas rendu, sans plancher
   (`phase2/sync/push_hektor_directory_to_supabase.py:133-140` et 414-430). Une réponse
   vide de Hektor viderait `app_user_directory`. Le rôle exact de cette table dans l'app
   n'est pas mesuré.

**A-t-elle déjà mordu ? Non mesuré.** Ni les volumes du miroir nuit par nuit, ni l'annuaire
ne sont relevés ici. Selon l'agent, le brut du détail est gardé (`sync_raw.py:795-808`,
non vérifié par moi) : une nuit normale suivante reconstruirait alors en grande partie.

**Rapporté par l'agent, NON vérifié par moi** (à vérifier avant toute décision) :
- le balayage complet des brouillons interrompu déclasse quand même
  (`sync_hektor_drafts.py:322-340`) ;
- le catalogue public de la vitrine peut se publier vide (`export_project_vitrine.py`) ;
- `magasin_affaire_app.py` peut effacer son carnet local sur une lecture vide, et pagine
  par OFFSET sur une clé non unique ;
- `descendre_correspondance_contacts.py` : 0 ligne lue vide la table ;
- `affaire_ledger.py:1083-1089` marque absentes, sans plafond, les affaires non revues ;
- `app_repartition_purger_orphelines` supprime sans plancher des parts dérivées.

Protégés selon lui, et cohérents avec ce que je connais :
- `aligner_miroir_sur_hektor` ;
- les registres des liens et des mandats (`garde_retrait_de_masse`) ;
- le push des contacts (plafonds) ;
- la suppression des documents (niveaux 1 et 2) ;
- les planchers de 5 000 des deux fonctions SQL de ménage.

⛔ **Rien de cela n'est à corriger dans le chantier de la descente.** Ce sont des sujets à
part, à ouvrir sur décision de Frédéric.

### 10.5 Qui dépend des copies descendues

Un second agent a cherché les 284 noms dans 1 164 fichiers, puis a lu chaque lecteur.
Ce que j'ai **vérifié moi-même** est marqué ✔ ; le reste est rapporté.

- **36 des 284 tables sont lues ou écrites en SQLite local.** Le texte d'en-tête de la
  descente (« personne ne lit ces tables », l. 39-42) est donc faux aujourd'hui.
- **248 tables n'ont aucun lecteur local trouvé** : 72 sauvegardes datées, 40 vues figées
  et 136 tables vivantes, comme `app_setting`, `app_rapprochement`,
  `app_console_document` ou `app_user_profile`. L'app elle-même (`apps/hektor-v1`) et
  `backend/` lisent Supabase, jamais ces copies.
- **Les lecteurs de nuit qui comptent pour les règles :**
  - ✔ `phase2/sync/affaire_ledger.py`, étape **BLOQUANTE** (`run_full_pipeline.ps1:988`).
    Il lit `app_affaire_ledger__sb` (l. 779, 793, 3553) sans regarder sa fraîcheur.
    - Cette doublure est rafraîchie juste avant par une descente ciblée non bloquante
      (l. 979), dont le commentaire dit : « si la descente échoue, le run continue avec
      l'ancienne doublure ».
    - Selon l'agent, une doublure trop vieille donne un second numéro à une offre née
      depuis : l'envoi heurte l'index unique et le run s'arrête (l'incident du 02/09). Je ne
      l'ai pas vérifié.
    - **Ce que les règles y changent** : un refus laisse la copie de la veille, comme
      aujourd'hui quand cette étape échoue. Sans la règle 1, un compte raté poserait une
      copie **amputée**, qui manquerait des numéros : c'est pire.
  - ✔ `phase2/sync/relation_ledger.py` : il a la seule vraie garde de fraîcheur, et c'est
    elle que la règle 0 répare (§ 10.1). Selon l'agent, la reprise des numéros et la pose
    des retraits se font sans cette garde.
  - `mandat_ledger.py`, `repartition_commission.py`, `registre_depuis_console.py`,
    `registre_partenaires_reprise.py` et `sync_hektor_contacts_diagnostics.py` : non
    bloquants et sans garde de fraîcheur. Une copie de la veille les fait travailler sur
    la veille.
  - `pousser_numeros_contact.py:78` et `quality_checks.py:155` : étapes bloquantes qui
    plantent si la table est **absente**. Aucune règle proposée ne supprime une copie : elles
    ne sont pas concernées.
  - ✔ `phase2/sync/backup_critical.py` (sauvegarde de 08:00) : il sauvegarde la copie en
    place sans dire de quand elle date.
  - `comparer_doublures.py` : une doublure de la veille donnerait de faux écarts dans son
    journal.
  - les sentinelles `mandat_un_numero`, `relation_disparue` et `mandat_disparu`, et la
    sonde : voir la règle 0.
- **Le piège « on n'écrit jamais dans une copie »** : ✔ `phase2/sync/delete_local_annonce.py`
  (l. 124-159), appelé par le worker après la suppression d'une annonce, efface des lignes
  dans cinq tables descendues. C'est sans danger : la ligne a déjà disparu de Supabase, et
  une copie refusée garde la suppression. Je le note pour mémoire, sans rien proposer.
- **Les petites tables lues en local, que la règle 4 à 100 lignes ne couvre pas**
  (comptes ✔, au dernier état) :
  - `app_affaire_champ_app__sb` (48), `app_contact_saisie_modif` (46),
    `app_affaire_supprimee` (28), `app_annonce_champ_app__sb` (21) ;
  - `app_annonce_saisie_modif` (14), `app_annonce_saisie_naissance` (13),
    `app_diffusion_request__sb` (9), `app_negociateur_journal` (60).
  - Ce sont surtout des **saisies de l'app**, c'est-à-dire exactement ce que la descente
    protège.

### 10.6 Les règles, revues après l'audit en profondeur

Dans l'ordre où je propose de les écrire, une à la fois, chacune sur son « vas-y » :

0. **La date d'une copie est celle de la copie en place** (§ 10.1). Elle est **NOUVELLE**
   et passe avant les autres : sans elle, les règles 1 et 4 tromperaient quatre gardes.
1. **Pas de compte, pas de bascule** (§ 3). Elle est inchangée ; les mesures du § 10.2 la
   confirment.
2. **Un message ne promet pas une copie qui n'existe pas** (D2, § 6).
3. **Un objet suivi qui disparaît du serveur se déclare** (D1, § 6).
4. **Une chute ne se croit pas sans geste humain** (§ 4), **précisée** :
   - (a) toute table ou vue d'au moins 100 lignes qui perd plus de la moitié ;
   - (b) **NOUVEAU** : toute table **à clé primaire** qui perd plus de la moitié **dès
     2 lignes**, zéro compris. C'est pour couvrir les petites saisies de l'app.
   - **Mesure sur 34 descentes**, recomptée sans filtre (toute chute de plus de moitié
     dès 2 lignes) :
     - (a) aurait donné **0 fausse alerte** ;
     - (b) aurait donné **1 fausse alerte** : `app_relation_provisional`, de 3 à 1 ligne,
       le 20/11. C'est une file d'attente qui se vide normalement.
     - Les deux autres chutes du relevé sont des vues, sans clé, donc hors de (b) :
       `app_v_negociateur_signaux` (13 → 0) et `app_v_repartition_orpheline` (26 → 0).
     - ⛔ J'avais écrit « 0 fausse alerte pour (b) » avant de recompter : c'était faux.
   - ⚠ **Le risque de (b)** : les files d'attente à clé (`_pending`, `_provisional`,
     `_dirty`) se vident normalement, et elles feraient crier.
   - **À trancher par lui** : (b) pour toutes les tables à clé (1 fausse alerte en
     34 nuits), ou (b) sauf les noms de file d'attente (0 en 34 nuits, mais c'est une
     règle par le nom).
5. **La sonde : ne pas voir n'est pas guérir** (§ 10.3). C'est dans
   `monitoring/check_gti_health.py`, un autre fichier, à part.

Pour la même famille hors de la descente (§ 10.4), je propose un chantier à part.

---

## 11. Ce qui est écrit

Son mot, le 26/11 au soir : « c'est de la sécurité donc il ne devrait pas y avoir de
problème ». Les règles sont donc écrites ce soir, une par une. Chacune a son interrupteur
et son témoin inverse, et chacune fait l'objet d'un commit local à part, dans la branche
normale, sans poussée. Le banc : `phase2/sync/test_garde_de_la_descente.py`.

### Règle 0 — la date d'une copie est celle de la copie en place (26/11, 19:56, `ef36b19`)

- **Le code** : `pull_from_supabase.py`, constante `DATE_DE_LA_COPIE_EN_PLACE = True`, et
  l'enregistrement « copie en cours » de `copy_table`.
  - Interrupteur allumé : la date d'une ligne existante n'est plus touchée, et une table
    neuve part sans date.
  - Interrupteur éteint : l'ancien code, conservé à l'identique dans la branche `else`.
- **L'épreuve : 12 sur 12.**
  - Une copie refusée garde la date de la veille, et sa copie d'avant intacte (500 lignes,
    aucune `__tmp`). La garde de `relation_ledger` ne la croit plus du jour.
  - Une copie réussie fait avancer la date.
  - Une table neuve refusée n'a aucune date.
- **Le témoin inverse**, interrupteur éteint : le piège réapparaît. La date dit « ce
  matin », `relation_ledger` serait trompé, et la table neuve porte la date du jour
  (essais 0f, 0g et 0k).
- **L'ancien banc** `test_descente_sans_cle_primaire.py` : 19 sur 19, avant comme après.
- **Ce qui change dehors**, voulu : un jour de refus, la sonde verra la copie comme « en
  retard » sur la table native. C'est vrai, et elle ne le voyait pas avant.
- **Le retour arrière** : `DATE_DE_LA_COPIE_EN_PLACE = False`, ou `git revert` du commit.
- **Prend effet** à la prochaine exécution, sans aucun geste : la descente ciblée du run de
  04:00, puis la descente de 06:45.

### Règle 1 — pas de compte, pas de bascule (26/11)

- **Le code** : constante `EXIGER_LE_COMPTE = True`, et un refus juste après
  `attendu = reader.count(distant)` dans `copy_table`. Le message est « comptage impossible
  chez Supabase (le compte n'a pas répondu) — bascule refusée ». Le reste de la fonction
  est inchangé.
- **L'épreuve : 22 sur 22** avec la règle 0. Côté règle 1 :
  - compte absent : la copie est refusée, et l'ancienne reste avec sa date ;
  - **lecture coupée à 300 lignes sur 500 et compte absent : refusée, les 500 restent** ;
  - compte juste : la copie passe ;
  - lecture coupée avec un compte : réparée par la relecture par rang, comme avant.
- **Le témoin inverse**, interrupteur éteint : la lecture coupée remplace la copie **sans
  un mot**, et l'état la dit complète et du jour (essais 1e et 1f). C'est exactement la
  faille A.
- **La limite, écrite exprès** (essai 1i) : une source vide remplace encore 500 lignes par
  0. C'est la faille B, que traitera la règle 4. L'essai changera de sens ce jour-là.
- **L'ancien banc** : 19 sur 19.
- **Le retour arrière** : `EXIGER_LE_COMPTE = False`.
- **Commit** : `2cb4cab`.

### Règles 2 et 3 — ce que la descente dit doit être vrai (26/11)

- **Le code** :
  - `UN_MESSAGE_DIT_VRAI = True` et la fonction `suite_du_refus()` : les deux messages de
    refus disent « l'ancienne copie est conservée » **seulement si elle existe**, et sinon
    « AUCUNE copie locale n'existe encore : rien n'est remplacé, rien n'est gardé » ;
  - `DECLARER_LES_DISPARUS = True` et la fonction `objets_disparus()` : à chaque passage
    complet, la descente nomme les objets suivis que l'API n'expose plus, avec ce qui en
    reste en local. Elle ne supprime rien et ne sort pas en code 1.
- **Le banc : 32 sur 32** pour les règles 0 à 3.
  - Règle 2 : sans copie locale, le refus le dit ; avec une copie, le texte reste
    « conservée » ; le refus de la règle 1 dit vrai lui aussi.
  - **Témoin inverse** de la règle 2 : interrupteur éteint, le texte d'avant revient **à
    l'octet près**, avec la promesse d'une copie absente.
  - Règle 3 : trois disparus fabriqués sont nommés avec leur reste local. Une doublure
    `__sb` dont l'original existe n'est pas prise pour disparue, et rien n'est supprimé.
- **Sur l'état réel**, avec la vraie fonction `main()` en `--dry-run` :
  - les conditions : la base locale ouverte en **lecture seule**, **aucun appel réseau**
    (toute requête aurait levé), **aucun `.env` lu**, et pour liste du serveur les 279
    objets mesurés au serveur le 26/11 ;
  - **interrupteur allumé** : exactement les 5 disparus mesurés.
    - `app_classeur_lien_avant_regel_20261029`, `_20261031` et `_20261109` : « AUCUNE
      COPIE LOCALE » ;
    - `app_notaire_interlocuteur` : 0 ligne gardée ;
    - `tmp_etape12_avant` : 39 lignes gardées.
  - **interrupteur éteint** : aucune ligne, comme avant ;
  - dans les deux cas, 169 tables à descendre (le chiffre du `--dry-run` de `092eb03`) ;
  - `phase2.sqlite` est inchangé : même taille (7 089 815 552 octets), même heure (16:37:51).
- **Le retour arrière** : les deux interrupteurs à `False`.
- **Commit** : `28ef02e`.
- ⚠ **Poussée** : les commits `ef36b19`, `2cb4cab` et `28ef02e` ont été **poussés sur
  GitHub vers 20:10**, avec d'autres commits du jour. Ce n'est pas par cette session : à
  20:48, `origin/main` était sur `28ef02e`.

### Règle 4 — une chute ne se croit pas sans geste humain (26/11, au soir)

- **Sa décision** (26/11) : « oui vas-y », sur le conseil d'écarter les files d'attente du
  seuil de 2 lignes.
- **Le code** :
  - les constantes `REFUSER_LES_CHUTES = True`, `CHUTE_FRACTION = 0.5`,
    `CHUTE_SEUIL_GENERAL = 100`, `CHUTE_SEUIL_TABLE_A_CLE = 2` et
    `FILE_D_ATTENTE = _(pending|provisional|dirty)$`, qui porte sur la **fin** du nom ;
  - la fonction pure `decision_de_chute()`, et la garde dans `copy_table` juste avant la
    bascule ;
  - l'option `--accepter-chute <table>` (le geste humain, écrit au journal) ;
  - la déclaration, à chaque passage, des files d'attente écartées.
- **La règle** : une copie qui a moins de la moitié de la copie en place est refusée si
  celle-ci avait :
  - au moins 100 lignes (toute table, toute vue) ;
  - ou au moins 2 lignes, pour une table à clé qui n'est pas une file d'attente.
- **Le banc : 48 sur 48** pour les règles 0 à 4.
  - La source vidée (500 → 0) est refusée, le message dit comment l'accepter, et la copie
    d'hier reste avec sa date.
  - Les seuils sont respectés : 48 % refusé, 60 % accepté ; une table à clé de 48 → 20
    refusée, de 48 → 30 acceptée, de 1 → 0 acceptée.
  - La file d'attente du 20/11 (3 → 1) passe, mais une file de 300 → 0 est refusée ;
    `app_pending_resolution` n'est pas prise pour une file.
  - Une vue de 26 → 0 passe, une de 25 175 → 0 est refusée ; une table neuve passe.
  - `--accepter-chute` laisse passer la chute voulue.
  - **Le témoin inverse**, interrupteur éteint : 500 lignes remplacées par 0, sans un mot.
  - L'essai 1i (« 0 = 0 passe ») est désormais joué règle 4 éteinte : il prouve que la
    règle 1 seule ne fermait pas ce trou.
- **Le rejeu de l'histoire avec la vraie fonction** : 67 journaux (34 descentes et 33 runs
  de nuit), 5 703 copies complètes comparées chacune à la précédente, **0 refus**.
  - **Le témoin positif du rejeu** : sans l'exclusion des files, il retrouve exactement le
    cas connu (`app_relation_provisional` 3 → 1, le 20/11) ; avec un seuil volontairement
    trop strict (0,5 %), il voit 23 baisses. Le zéro est donc réel.
- **Le `--dry-run` réel** (lecture seule, sans réseau, sans `.env`) déclare les **8** files
  écartées : `app_annonce_pending`, `app_annonce_provisional`, `app_contact_pending`,
  `app_contact_provisional`, `app_rapprochement_dirty`, `app_relation_provisional`,
  `app_search_pending` et `app_search_provisional`. Il trouve toujours 169 tables à
  descendre, et `phase2.sqlite` est inchangé.
- **L'ancien banc** : 19 sur 19.
- **Le retour arrière** : `REFUSER_LES_CHUTES = False`.
- **Ce qui reste** : la règle 5, la sonde (`monitoring/check_gti_health.py`).
