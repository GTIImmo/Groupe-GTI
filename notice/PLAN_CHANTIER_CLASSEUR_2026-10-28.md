# LE CHANTIER CLASSEUR — où on en est, le but, le plan, les tâches

---

# 0. ⭐⭐ LE PLAN D'ACTION ACTIF — **réécrit le 12/11/2026, tout est mesuré**

> ⛔ **CETTE SECTION EST LE PLAN D'ACTION EN COURS.** Le reste du document garde
> **le but** (§ 2), **les tâches d'origine** (§ 4) et **les interdits** (§ 6) : ils ne
> changent pas. On ne duplique pas ce fichier, on met CETTE section à jour.
>
> ⚠ **Ce qui a dû être corrigé pour arriver à cette version, à ne pas refaire :**
> j'ai donné « le plan » quatre fois en lisant mes propres audits (A15, A17, A18) au
> lieu d'ouvrir ce fichier. Deux conséquences : j'ai proposé **de créer une table
> `app_affaire_suivi` et des colonnes**, ce que le § 6 interdit, et j'ai annoncé « puis
> le classeur ferme », alors que le § 2 dit l'inverse — **il change d'écrivain**.

## Le but, en deux lignes *(§ 2, inchangé)*

```
① le classeur FAIT FOI  -> on met notre data en conformite avec lui
                           il REMPLIT les vides ET CORRIGE les divergences
② puis LA BASCULE       -> on saisit dans l'app, plus dans le classeur
                           ⚠ le classeur NE FERME PAS : il change d'ecrivain
```

## ⭐ La correspondance : comment une ligne du Sheet trouve son dossier

```
id_unique du Sheet
      |  LE GEL  (app_classeur_lien, 29/10 -- 12 422 liens)
numero de transaction        <- il ne change JAMAIS
      |  le chainage, chaque nuit
le dossier
      |  l'etiquette
D2026-0431  +  un UUID
```

⭐ **Le gel s'accroche à la TRANSACTION, pas à la chaîne** — règle du 28/10 : *« un
numéro de chaîne ne doit jamais servir de point d'accrochage, il bouge »*. C'est pour
ça que le chaînage a pu être refait sans casser un seul lien.

⭐⭐ **ET LE GEL EST UN ÉCHAFAUDAGE, PAS LE MUR.** Il sert **une seule fois de plus** :
à écrire notre UUID dans la colonne `affair_uuid` du Sheet (étape 5). Après ça, chaque
ligne porte elle-même l'identifiant de notre dossier, la correspondance est écrite des
deux côtés, et **le gel devient une archive**.

**Mesure du 12/11, avec le chaînage corrigé :**

```
lignes du Sheet qui tombent dans UN SEUL dossier   4 655   (99,3 %)
lignes a cheval sur DEUX dossiers                     33
dossiers portant UNE SEULE ligne du Sheet          4 715
dossiers portant DEUX lignes                           3
```

➡ **Aucune règle nouvelle à inventer.** Restent 36 cas à trancher à la main — et la
décision du 04/09 interdit de les régler par une règle.

## ⚠⚠ LE DÉFAUT TROUVÉ LE 12/11 — **la date d'une offre refusée**

```
offres portant la date du 11/11/2026              1 185   = nos refus de la veille
   heures : 07:52:36 -> 19:37:07
```

**Pour une OFFRE, Hektor met dans `date` son DERNIER mouvement, pas la proposition.**
Nos 1 185 refus ont donc déplacé la date de 1 185 offres au 11/11/2026. Relevé sur
l'offre 14112 : proposition le 25/03/2021, acceptation le 25/03/2021, refus le
11/11/2026 — et `date` porte le refus.

⭐ **Rien n'est perdu** : la vraie date vit dans `propositions_json`.
⭐ **Le chaînage n'est pas touché** : il ordonne une offre sur sa première proposition.
⛔ **ON NE CORRIGE PAS LA COLONNE** — classe C, le run la relit chaque nuit (ce serait
le gel du 03/09) ; et la corriger chez Hektor demanderait de réenregistrer les offres,
c'est-à-dire de redéplacer la date. **On corrige les LECTEURS.**

```
l'apparieur                        ✅ REPARE le 12/11 -- reparation « propositions »
le chainage                        ✅ deja bon
l'historique de l'offre a l'ecran  ✅ bon (il lit propositions_json)
rapport_gel_tous_les_champs.py     ✅ REPARE le 12/11 -- 536 faux ecarts evites
la date affichee sur la ligne      ✅ REPARE le 12/11 (commit 541f1be)
« derniere date » de l'avancement  ✅ REPARE le 12/11 -- meme commit
```

⭐⭐ **LES QUATRE LECTEURS SONT ALIGNES depuis le 12/11** — commit `541f1be`, non pousse
a l'heure ou ceci est ecrit :

```
le chainage de nuit   _date_de_tri              affaire_ledger.py l. 1517 . deja juste
l'apparieur           dates_des_propositions    apparier_classeur.py . 12/11
le rapport du gel     premiere_proposition      rapport_gel_*.py . 12/11
l'ECRAN               dateOffreFaite            api.ts . 12/11
MESURE : 1 435 offres retrouvent leur vraie date, dans 1 430 dossiers
         dont 1 180 par nos refus . 255 l'avaient DEJA avant nous
         la plus ancienne retrouvee : 18/09/2006
```

⭐ **UNE SEULE DEFINITION** : `dateOffreFaite` existait dans `App.tsx` depuis le
**05/11** mais ne servait qu'a la REGULARISATION d'une offre oubliee. Elle a demenage
dans `api.ts`, a cote du type et des requetes. *(Lecon n° 15 : chercher si le projet a
deja tranche -- j'allais ecrire une fonction qui existait.)*

⛔ **ET LA COLONNE NE SE CORRIGE PAS, c'est prouve par le code** : le run la relit chez
Hektor a chaque nuit (`R2_CHAMP_VERS_COLONNE`, `affaire_ledger.py` l. 1661) et la
protection est **nommement refusee** pour ce couple (`R2_JUGES_SUR_LE_REGISTRE`, l. 1671),
parce que R3 doit pouvoir comparer notre valeur a celle de Hektor.

⚠ **Et le phénomène n'est pas né hier** : 263 offres l'avaient déjà. En revanche
**1 061 offres refusées ont leur date intacte** — il y a donc une différence entre un
refus fait à la main chez Hektor et le nôtre. **NON MESURÉ, c'est une hypothèse.**

## 📋 LES ÉTAPES

### ÉTAPE 1 — fermer l'appariement *(P1)*

```
1.1 ✅ FAIT 12/11   l'apparieur repare : 4 691 / 4 786 reconnues (98,0 %)
                    sure 4 569 . bonne 11 . a valider 111 . aucune 95
                    temoins : 0 ligne perdue . 17 des 20 regressions revenues
                    ⭐ et 3 des 5 cibles changees S'ALIGNENT SUR LE GEL
1.2 ✅ FAIT 12/11   rapport_gel_tous_les_champs.py repare (premiere_proposition)
                    AMPLEUR MESUREE : 536 offres gelees avaient leur date deplacee
                    (306 par nos refus) -> le rapport annoncait 536 FAUX ecarts
                    sur « Offre Achat ». C'ETAIT UN PREREQUIS DE 3.1.
                    temoins : cas reel 14112 -> 2021-03-25 . refus seul -> None
                              8 formes degradees, aucune exception
1.3 ✅ FAIT 12/11   LA « SEULE DIVERGENCE » N'EXISTE PAS : pour 2dfa6ef3,
                    l'apparieur dit la chaine 30656 et le gel la transaction
                    30692 -- QUI EST DANS LA CHAINE 30656. Je comparais un
                    dossier a une transaction. La reserve tombe.
                    8Q3LHGZ4  2 pistes = SERRA et CHEVALIER, deux acheteurs du
                              bien 16831 -> le CLASSEUR melange deux affaires
                    I847SPN3  3 chaines ; le gel pointe le dossier 3699 (celui
                              laisse parmi les 38 impossibles)
                    UTLG66LE  3 chaines ; cause mesuree : sa date est 0000-00-00
1.4 ✅ MESURE 13/11  LES 2 « a valider » SONT INSTRUITES, et la reponse est LA MEME
                    pour les deux : LE BIEN EST JUSTE, MAIS LA TRANSACTION QUE LE
                    CLASSEUR DECRIT N'EXISTE PAS CHEZ HEKTOR.
                      ME6S0TR9 (ligne 3406) -> bien 42976, mandat 17260, Yssingeaux
                        classeur : TROY Pierre, 240 000, offre 06/11/2024,
                        compromis 06/01/2025, annulee 25/04/2025
                        Hektor : les transactions du bien sont a GIBERT puis PEPIER
                        ⚠ l'apparieur la rattachait a la chaine 24256 PAR LE NOM
                          « TROY » (rachel TROY, bien 47955, mandat 14338, 152 000) :
                          deux personnes, rien d'autre ne concorde. Il se trompe,
                          et sa confiance « a valider » etait juste.
                      6a259cce (ligne 4372) -> bien 11729, mandat 18040, Ambert
                        classeur : RIVOLLIER Remi, 160 350, offre 28/10/2025,
                        ANNULEE 30/10/2025 (« pas le financement »)
                        Hektor : le MEME JOUR, offre de VALENTIN CHANTELOUP au MEME
                        PRIX (160 350), qui aboutit a la vente du 03/04/2026
                        ⭐ le prix est EXACTEMENT egal et les vendeurs concordent :
                          le bien est certain, mais l'offre Rivollier n'a jamais ete
                          enregistree chez Hektor.
                    ⬜ LA DECISION RESTE A FREDERIC : on ne gele RIEN (le gel accroche
                      des TRANSACTIONS, pas des biens), ou on cree les transactions
                      manquantes chez Hektor.
1.5 ⬜ ACCORD       le RE-GEL ADDITIF des gains -- LISTE CONFIRMEE A JOUR le 13/11,
                    apres relance de l'apparieur ET avec le chainage de la regle D :
                      « sure »      3990 Z3DYDC4X -> 14111 . 4790 d7cbb8fa -> 30806
                                    4791 b7439331 -> 30809 . 4792 c67ccc6a -> 30808
                      « a valider » 3406 ME6S0TR9 . 4372 6a259cce  (voir 1.4)
                    ⛔ ADDITIF : on ne retouche aucun des 12 422 liens
⭐⭐ 1.5bis ✅ MESURE 13/11 -- LE CHAINAGE N'A RIEN CASSE DANS LE GEL, et c'est
                    desormais MESURE SUR SUPABASE (chainage a jour, regle D incluse),
                    pas seulement affirme :
                      liens du gel                              12 422
                      dont la TRANSACTION a disparu                  0
                      dont la transaction est HORS CHAINE            0
                      lignes dont les liens pointent 2 BIENS         0   ⭐
                      lignes eclatees sur 2 CHAINES                 32
                    ⭐ Les 32 sont sur LE MEME BIEN, deux chaines : c'est le chainage
                      qui coupe le dossier, pas le gel qui se trompe. C'est la famille
                      des « lignes a cheval » (33 le 12/11), deja expliquee.
                    ⭐ Et la sentinelle app_v_classeur_lien_casse n'en compte que 5,
                      tous « ABSENTE_CHEZ_HEKTOR » -- donc VOULUS (le carnet est a
                      nous), et vus pour la derniere fois en septembre/octobre.
                    ➡ IL N'Y A DONC PAS A REFAIRE TOURNER LE GEL. Ce qui etait prevu,
                      c'est le RE-GEL ADDITIF de 1.5, et sa liste est inchangee.
1.6 ⬜              git : apparier_classeur.py n'est PAS suivi, ni les notes
```

### ÉTAPE 2 — l'étiquette de dossier *(B2/B3 du plan du 29/10)*

```
2.1 ✅ FAIT 12/11   la REPETITION ecrite AVANT le collage -- 12 controles, 3 temoins
                    inverses (..._REPETITION.sql, commit cc537ce)
2.2 ✅ FAIT 12/11   la pose A BLANC : 11 441 dossiers, 0 ligne ecrite
2.3 ✅ POSE 12/11   deux migrations : etiquette_dossier_objets_2026_11_12 et
                    etiquette_dossier_pose_et_droits_2026_11_12
                    les 12 controles joues apres le collage : TOUS VERTS
2.4 ✅ B3 FAIT 12/11  le remplissage, en 4 lots (50 d'essai, puis 3 000, 4 000, le reste)
                    31 151 / 31 151 transactions etiquetees -- 0 sans etiquette
                    11 441 dossiers = 11 441 uuid = 11 441 numeros (bijection)
                    invariants 0/0 . journal 11 441 poses, somme 31 151
                    compteur : 25 annees, somme des rangs 11 441
                    ⭐ les 6 dossiers muets (D0000-xxxx) sont TOUS MORTS -- les
                      fermetures du matin ont solde les 2 qui comptaient encore
2.5 ✅ FAIT 12/11   B4 : LA POSE EST BRANCHEE DANS LE RUN DE NUIT **ET ALLUMEE**
                    (`APP_ETIQUETTE_DOSSIER=1` dans `.env`, hors git ; sauvegarde
                    `env_avant_etiquette_2026-11-12.bak`). L'appel est a
                    `affaire_ledger.py` l. 2772, ENTRE `rpc/app_attribuer_chaines_affaire`
                    (l. 2761) et la redescente (l. 2777) -- donc APRES le calcul des
                    groupes, comme C2 du 29/10 l'exige.
                    ⭐ AVEC UN FILET : si la pose echoue, LE RUN CONTINUE. Une
                      etiquette manquante se rattrape la nuit suivante ; un run
                      interrompu coute la nuit entiere.
                    ⭐ ET UNE ALERTE : SEUIL_FUSIONS_QUI_INQUIETE = 10 -- une fusion
                      est DEFINITIVE pour l'etiquette absorbee, qui ne vit plus que
                      dans le journal.
                    essai hors ligne : phase2/checks/test_etiquette_dans_le_run.py
                    32 controles verts, client FAUX, aucune connexion
⏰ 2.5bis A CONTROLER DEMAIN MATIN (13/11) -- premiere nuit de B4. Chercher dans le
                    compte rendu du run :
                      [affaire_ledger] etiquettes : pose N . propagation N .
                                                    fusion N . scission N
                    ⛔ Si la ligne MANQUE, l'interrupteur n'a pas ete lu.
                    ⛔ Si les FUSIONS depassent 10, le run le crie -- regarder.
⭐ le format est valide (« Oui » aux deux, 09/11) : D2026-0431 + un UUID
⭐ le code local etait PRET avant la pose : les 2 colonnes sont dans
  COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (affaire_ledger.py l. 2561) -- condition C1
```

### ⛔⛔ LE DÉFAUT QUE FRÉDÉRIC A TROUVÉ LE 12/11 AU SOIR — *ma correction était incomplète*

> *« pourquoi les offres du 11/11 sont toujours visibles dans le registre des
> transactions ? et le pilotage forcément »*

Il avait raison. J'avais corrigé les **deux écrans de détail** et conclu trop vite. Le
registre passe par une fonction **EN BASE**, `app_registre_dossiers`, que je n'avais pas
vue — et **le filtre par année s'appuyait sur la date faussée**.

```
MESURE AVANT, sur les 11 424 dossiers du registre
  « date du dernier evenement » fausse        1 277
  CLASSES EN 2026 A TORT                     1 190   <- la plus ancienne : 2006
  date d'offre fausse                        1 412
APRES (3 migrations collees le 12/11)
  dossiers en 2026       1 684  ->  494      1 190 retrouvent leur annee
  dossiers au 11/11/2026 1 185  ->    5      les 5 sans aucun recours
  offres sans date         786  ->   85      701 retrouvent une date
```

⭐ **Et la cascade qu'il a dictée est en service** : journal → compromis → vente.
**56 offres sur 68** retrouvent une date. ⛔ Les crans 4 (le classeur) et 5 (le mandat)
ne sont **pas** dans la fonction : le mandat ne donne qu'une **année**, et on n'invente
jamais un jour. Sans réponse, l'écran affiche « — ».

#### ⛔ ET LE POINT LE PLUS GRAVE, QUE J'AVAIS ÉCARTÉ LE MATIN

Le préremplissage de la modale (`App.tsx:19260`) lisait `affaire.date` brut. Or ce champ
**part chez Hektor** (`console_job_worker.js:15769`, `body.set("dateOffre", tx.date)`).

➡ **Ouvrir puis enregistrer une de ces offres écrivait le 11/11/2026 chez Hektor.**
J'avais écarté ce point « par prudence » : c'était l'inverse, ne pas le toucher laissait
la contamination se propager. **Corrigé le 12/11.**

#### LES QUATRE COUCHES AUDITÉES, ET CE QUI RESTE

```
EN BASE    ✅ app_registre_dossiers . la pose . l'annee d'ouverture
           ✅ app_pilotage_acquereurs    1 408 acquereurs, dont 524 au 11/11
           ✅ app_pilotage_affaires_plus 1 869 -> 702 offres sur 2025-2026, et le
              delai moyen mandat->offre passe de 2 148 jours (5,9 ANS) a 181 jours
           ⭐⭐ LE CHAINAGE EST SAIN, MESURE : app_attribuer_chaines_affaire trie
              par app_affaire_id, et app_chaine_pour (les 2 signatures) groupe sur
              l'annonce, l'acquereur et l'ETAT. AUCUNE date nulle part.
              ⛔ Mon audit l'avait signale A TORT -- ma requete cherchait
                « order by … date » et a crie sur « order by app_affaire_id ».
                Un detecteur qui crie n'est pas une preuve : il faut lire le corps.
           ✅ app_notaire_fiche -- migration notaire_fiche_date_offre_reelle_2026_11_12
AU FRONT   ✅ les 2 tris . la ligne Date . la tuile . le PREREMPLISSAGE
           ✅ le cockpit, le resume et le tri des dossiers d'un bien (App.tsx 32321 .
              32634 . 32753) -- ils passent tous par `dateDeRangement`
PYTHON     ✅ le chainage . l'apparieur . le rapport du gel
           ⚠ export_app_payload.py et transactions_annonce_from_api.py : non mesures
WORKERS    ✅ ils n'ont PAS de lecteur -- ils envoient ce que la modale leur donne
```

### ✅ PROUVÉ À L'ÉCRAN, ET B EST FAIT — *12/11 au soir*

**Le registre des transactions, ouvert dans le navigateur :**

```
« 494 dossiers · 2026 »        <- exactement les 494 mesurés en base (contre 1 684)
291 vendus + 88 compromis + 41 acceptees + 6 proposees + 10 annules + 58 refusees
                              = 494, les compteurs s'additionnent
```

⚠ **Et les 5 offres en tête de liste sont exactement les 5 sans recours**
(24256, 20169, 16330, 16255, 9557) — celles dont Hektor dit `0000-00-00`. Elles sont
les **seules** à rester au 11/11, comme la mesure l'annonçait. ➜ Elles font partie des
**12 à trancher par Frédéric**.

#### ✅ B — L'ÉTIQUETTE POSÉE AU CLIC

```
app_poser_etiquette_du_dossier(p_chaine)   pose + propagation, UN SEUL dossier
la modale l'appelle apres son INSERT       avec un FILET : si la pose echoue,
                                           LE GESTE DE L'UTILISATEUR PASSE QUAND MEME
```

⛔⛔ **Elle ne FUSIONNE ni ne SCINDE jamais** : un clic ne doit pas pouvoir réunir deux
dossiers, une fusion étant irréversible pour l'étiquette absorbée. Fusion et scission
sont des conséquences d'un **recalcul**, et le recalcul n'a lieu que la nuit.

⭐ **Aucune règle dupliquée** : l'année vient du lecteur unique, le rang du **même
compteur que la nuit** — donc aucune série parallèle.

```
EPREUVE, en transactions ANNULEES sur le dossier 3676
  propagation  on retire l'etiquette de la vente -> les 4 la retrouvent (D2025-0254)
  pose         on denude tout le groupe -> un numero neuf D2025-0438, 0 nue,
               1 ligne au journal « AU CLIC », compteur 2025 : 437 -> 438
  apres rollback : tout intact, compteur revenu a 437, 0 ligne « AU CLIC »
```

⚠ **CE QUI N'EST PAS ENCORE PROUVÉ** : personne n'a fait le geste **depuis l'écran**.
L'épreuve appelle la fonction directement. Au premier changement de statut réel, vérifier
que la ligne neuve porte son étiquette à la seconde, et que le journal dit « AU CLIC ».

### ✅ LES 4 ESSAIS DU CHAÎNAGE SONT VERTS — *12/11 au soir*

Ils criaient ROUGE à chaque passage depuis des semaines, et **aucun ne parlait du code**.

```
① l'invariant « bloc date APRES la vente »   11 cas LEGITIMES (offres saisies apres
   coup) presentes comme « ce qui ne doit JAMAIS arriver » -> socle tolere, cri des
   qu'il BOUGE, dans les deux sens . le nombre reste AFFICHE
② les references de compte du 20/10          12 702 / 12 278 / 12 159 / 12 149 avec
   une tolerance de 30, alors que 4 regles ont REUNI 727 dossiers depuis
   -> reetalonnees AVEC la liste des regles sous lesquelles elles valent
   ⭐⭐ + LES RELATIONS, le seul juge qui ne se demode pas : une regle qui REUNIT ne
      peut pas AUGMENTER le nombre de dossiers
      V2 eteinte 11 485 -> V2 11 438 -> cran 1 11 438 -> cran 2 11 428
③ le cran des sans-date IMPOSE a 1           la production est au cran 2
   -> on lit `.env` . ⚠ un setdefault NE SUFFIT PAS (la variable y est chargee PLUS TARD)
```

⛔⛔ **ET DEUX PIÈGES DE MESURE QUI VALENT POUR TOUT LE PROJET :**

```
la base LOCALE porte les chaines du DERNIER RUN -- tout ce qui est pose dans la
   journee n'y est PAS encore. Releve : le dossier 3676 etait encore COUPE EN DEUX
   en local alors que la regle D l'avait reuni chez Supabase, et les 19 offres
   reacceptees y etaient encore « refused ». Un ecart local/Supabase est un RETARD.
⭐⭐ CE QUI COMPTE N'EST PAS LE NUMERO MAIS LE GROUPE : 1 187 numeros differents
   mais 2 854 GROUPES differents. Pour juger un chainage on compare les PARTITIONS
   (qui est avec qui), JAMAIS les numeros.
```

**État : six essais, six verts** — `offre_regularisee` · `vente_ferme` · `v2` (4 sens
+ 3 relations) · `offre_proposee` · `dirty_guards` · `etiquette_dans_le_run`.

### ⚠⚠ LES TROIS TROUVAILLES DE L'APRÈS-MIDI DU 12/11 — *mesurées, pas supposées*

#### ① L'ANNÉE DES ÉTIQUETTES EST FAUSSE POUR 708 DOSSIERS *(le même défaut)*

La pose de 11:00 a daté chaque dossier sur `min(date)`. Donc la date d'une offre
refusée a daté son dossier.

```
dossiers dates                                11 347
dont l'annee est FAUSSE                          708   (6,2 %)
dont etiquetes « 2026 » a tort                   653
part des dossiers « 2026 » qui sont faux   653/1 019   (64 %)
l'annee vraie s'etale de 2006 a 2025
```

⛔ **DEUX lecteurs d'année existaient, aucun n'avait été réparé** — `app_dossier_annee_ouverture`
**et** la CTE « groupes » DANS la fonction de pose. *C'est elle qui a posé les 653.*
*(« Élargir un seuil : chercher ses jumeaux ».)*

⭐⭐ **ET LA FENÊTRE SE FERME** : rien ne lit l'étiquette — `grep` sur `apps/ backend/
Console/ scheduled/` rend **zéro**, 0 clé étrangère, 0 vue, 0 autre fonction. Reposer est
donc gratuit **tant que les UUID ne sont pas partis dans le classeur (5.2)**. Après, le
numéro est public et « un numéro ne se perd jamais » l'interdit.

⚠ **Un piège trouvé à blanc** : 14 offres portent une proposition datée `0000-00-00` ;
sans filtre, leur dossier tombait en `D0000`. **14 régressions évitées.**

```
2.6 ✅ COLLE 12/11  les LECTEURS, en trois migrations :
                    etiquette_annee_lecteur_unique_2026_11_12
                    etiquette_annee_lecteur_durci_2026_11_12
                    etiquette_pose_passe_par_le_lecteur_2026_11_12
2.7 ✅ COLLE 12/11  la REPOSE : etiquette_annee_repose_2026_11_12
                    697 numeros mentaient -> 0 . dont 648 « 2026 » -> 0
                    31 151 etiquettes . invariants 0/0/0 . bijection 11 441
                    compteur 11 441 . journal somme 31 151 . format 0 mal forme
                    de D0000-0001 a D2026-0371 (etait D2026-0550)
                    ⭐ CHRONOLOGIE 100,00 % : 0 desordre sur 11 323 comparaisons
                    sauvegarde : app_etiquette_avant_repose_20261112 (31 151 l.)
2.8 ✅ POSE 12/11   LA DATE DECIDEE pour les 5 offres sans date NULLE PART, en
                    quatre migrations : date_convenue_des_transactions .
                    les_appelants_passent_l_id_v2 .
                    date_convenue_prime_sur_la_colonne . date_convenue_reliee_au_registre
                    + 5 greffes dans api.ts (le front recalculait la regle en TS, et
                      le PREREMPLISSAGE de la modale part CHEZ HEKTOR)
                    9557 -> 11/12/2017 . 16255 -> 11/07/2022 . 16330 -> 08/04/2021
                    20169 -> 01/03/2024 . 24256 -> 25/02/2022
                    ⭐ SOURCE MESUREE, pas devinee : contact 0,95 (mediane 11 j) ;
                      identifiants 0,19 / 0,14 / 0,01 ECARTES -- Hektor recycle ses
                      numeros (prouve sur le mandat 16705, porte par DEUX biens)
                    ⛔ MON ERREUR, trouvee par la mesure en une minute : la date
                      decidee etait APRES la colonne `date` dans le coalesce. Or
                      `date` n'est pas vide : elle porte le 11/11 faux. Le repli ne
                      jouait JAMAIS. Ordre juste : journal -> DECIDEE -> `date`.
                    temoin inverse : compromis 10 653 -> 0 bouge . offre 11 218 -> 5
                      bougent . vente 9 280 -> 0 bouge
                    trace : supabase/patch_date_convenue_2026-11-12.sql
2.9 ✅ POSE 12/11   LA REPOSE N°2 -- les 5 dossiers ayant change d'annee, leur
                    etiquette D2026-0367..0371 etait devenue fausse et l'invariant
                    valait 5 : le controle aurait CRIE chaque jour.
                    migration etiquette_repose2_apres_dates_decidees_2026_11_12
                    l'annee qui ment 5 -> 0 . 1 486 dossiers renumerotes (4 010
                    transactions) . bijection 11 441 = 11 441 . 0 desordre chrono
                    plage D2026-0371 -> D2026-0366
                    ⭐⭐ LES 5 PORTENT EXACTEMENT LES NUMEROS QUE LA SIMULATION EN
                      LECTURE SEULE AVAIT ANNONCES : D2017-0564 . D2022-0335 .
                      D2021-0217 . D2024-0072 . D2022-0098 -- des rangs au MILIEU
                      de leur annee, donc chronologiquement justes
                    ⚠⚠ PIEGE EVITE DE JUSTESSE : le patch de 2.7 cree ses copies en
                      `create table if not exists`. Le relancer n'aurait RIEN
                      sauvegarde et j'aurais detruit en croyant etre couvert. D'ou
                      des tables PROPRES : app_etiquette_avant_repose2_20261112
                      ⭐ LECON : un patch idempotent n'est pas rejouable.
                    trace : supabase/patch_etiquette_repose2_2026-11-12.sql
```

⛔⛔ **ET LE TÉMOIN INVERSE DE MA PROPRE RÉPÉTITION A TROUVÉ UN DÉFAUT DANS MA PREMIÈRE
VERSION DU LECTEUR.** Écrit en SQL pur, il **levait** sur un `propositions_json` qui n'est
pas du JSON (*« invalid input syntax for type json »*) au lieu de retomber sur `date` :
**une seule valeur abîmée aurait fait tomber la pose entière.**

```
le risque est THEORIQUE -- la colonne est de type JSONB, la base ne peut pas
   contenir du non-JSON. MAIS la fonction prend du `text`.
corrige quand meme : plpgsql + bloc exception, 5 lignes
eprouve sur : JSON illisible . tableau de texte . JSON tronque -> repli sur `date`
les 10 temoins sont verts, dont les TROIS qui faisaient lever
```

⭐ **C'est exactement à quoi sert une répétition écrite avant le collage.** Sans elle,
le défaut dormait jusqu'au jour où une ligne aurait été abîmée.

#### ② LES 33 LIGNES À CHEVAL : L'ÉNIGME EST RÉSOLUE

Elles ont **toutes la même forme** — *offre refusée + compromis annulé, même bien* :

```
23 lignes   deux ACHETEURS DIFFERENTS -> LE CLASSEUR melange deux affaires sur
            une ligne. LE CHAINAGE A RAISON, il n'y a rien a corriger chez nous.
 5 lignes   MEME acheteur -> le chainage a rate : reunissables
            8SZDU4F5 . BHMANOK7 . H3SQXY47 . U258U4CX . WUQ5445T
 5 lignes   un nom manque -> a mesurer
            26283bf9 . 566d1a48 . 600f4e1c . 7PBRZJD8 . CA2XNF38
```

⛔ **ET PAS DE RÈGLE AUTOMATIQUE.** Portée mesurée sur tout le registre : **472 paires,
dont 417 avec deux acheteurs DIFFÉRENTS.** Une règle sans la garde du nom aurait fusionné
417 affaires d'acheteurs concurrents. *La décision du 04/09 était juste.*

⚠ **Et ma première mesure disait « 472 sans acquéreur »** : `acquereurs_json` est
**parfois un OBJET, parfois un TABLEAU**. Une lecture ratée n'est jamais un vert.

#### ③ 20 OFFRES REFUSÉES À TORT PAR MON LOT DU 11/11

⛔⛔ **ET MA PREMIÈRE QUALIFICATION ÉTAIT FAUSSE — corrigée le 12/11 après mesure.**
J'avais écrit *« 517 offres refusées à tort, dont 496 l'histoire de Hektor depuis 2007 »*.
**C'est faux, et c'eût été grave de le laisser écrit** : quelqu'un serait allé « réparer »
500 lignes justes dans six mois.

```
offres refusees dont l'acheteur a FINALEMENT achete        220
  leur refus est AVANT ou LE JOUR de la vente              218   ⭐ l'ordre d'une NEGOCIATION
  apres la vente                                             1
  sans refus a leur journal                                  1
  ACCEPTEES puis refusees -- la seule vraie anomalie          2
```

⭐ **« Même acheteur » ne veut pas dire « erreur ».** Une offre refusée n'empêche pas le
même acheteur d'acheter ensuite : il offre 180 000, c'est refusé, on négocie, il revient à
195 000 et la vente se fait. **L'offre à 180 000 reste refusée, et c'est juste.** Les 218
refus antérieurs à la vente le prouvent.

⭐ **La vraie anomalie est « ACCEPTÉE puis refusée alors que l'affaire a abouti »**, et il
n'y en a que **2** :

```
offre 11147  HUGON, bien 23353 . acceptee 19/01/2026, refusee 11/03/2026, vendue 27/03/2026
             ⭐ le refus N'EST PAS DE NOUS (11 mars) : geste humain 16 jours avant la
               vente, l'affaire a ete refaite. RIEN A CORRIGER.
offre 14420  BELLAVIA . refusee le 11/11/2026 PAR MOI -> le seul cas restant, et il
             est a nous (c'est celle qui est LAISSEE de cote plus bas)
```

➡ **Il n'y a pas 500 anomalies chez Hektor. Il y en avait 20, toutes de mon fait, dont
19 sont réparées.** ⚠ Ce qui ne change rien à l'erreur de méthode : j'ai agi en masse sur
un chaînage que je savais incomplet.

⭐ **Le script avait la BONNE garde** (`cpAnnule && !cpVivant && !vente && offreAcceptee`).
⛔ **L'erreur est une erreur d'ORDRE, et elle est à moi** : j'ai refusé sur un chaînage
incomplet, puis j'ai corrigé le chaînage **le lendemain**. Hier soir l'offre 3678 était
seule ; la règle D l'a réunie ce matin aux trois autres transactions de DEFOUR, révélant
que le refus était faux.

➡ **LEÇON : ne jamais poser un geste de masse chez Hektor sur un chaînage qu'on sait
incomplet. Le chaînage d'abord, le geste ensuite.**

```
1.7 ✅ FAIT 12/11   19 offres remises « acceptee » CHEZ HEKTOR ET CHEZ NOUS
                    Console/enqueue_reaccepter_offres_refusees_a_tort.js
                    18 travaux done, 0 erreur . 19/19 « accepted », 0 « refused »
                    ⛔ 1 LAISSEE, DECLAREE : l'offre 14420, dont l'offre est datee
                      APRES sa vente (20/11/2009 contre 25/07/2008) -- deux defauts
                      se superposent, on ne repare pas deux choses d'un geste.
                      TEMOIN INVERSE : elle est bien restee « refused ».
                    ⛔ ET LES 219 AUTRES N'ONT PAS BOUGE -- et c'est JUSTE : ce sont des
                      NEGOCIATIONS NORMALES (refus AVANT la vente), pas des defauts.
                      Voir la correction de ma qualification au § ③ ci-dessus.

⭐⭐ **L'ESSAI SUR UNE SEULE A TROUVE UN TROU, ET C'EST POUR CA QU'ON LE FAIT.**
Le travail finissait `done`, avec `verbe: GET` et `reponse_hektor: 1`, la relecture de
la fiche tournait -- **et notre registre disait toujours « refused », le journal de
l'offre n'avait aucun 4e evenement.** A ce stade je ne POUVAIS PAS dire si Hektor avait
bascule.

```
la cause   le refresh_console_data relit L'ANNONCE, pas les TRANSACTIONS
           (elles ont leur propre listing, list_offres, relu LA NUIT)
le remede  phase2/sync/transaction_etat_from_api.py -- porte 2, ecrite le 16/09
           pour cette raison exacte : « une verification qui ne depend pas de
           l'ordre des choses ». Sur 9886 : « etat: accepte ».
```

⛔ **La seconde passe lit maintenant l'etat CHEZ HEKTOR, offre par offre, et n'ecrit
chez nous que si Hektor dit « accepte ».** Une lecture ratee n'ecrit rien et compte
comme un echec. *Sans l'essai sur une seule, j'aurais pose 19 etats sans preuve.*

⚠ **A VOIR DEMAIN MATIN** : la colonne `date` de ces 19 offres passera au 12/11 (le run
relira leur journal, qui porte maintenant l'acceptation). **Sans effet a l'ecran** depuis
le commit 541f1be -- c'est exactement ce qu'il devait proteger.

⚠ **ET UN SUJET A PART, TROUVE EN PASSANT** : 7 de ces dossiers portent **a la fois une
vente et un compromis encore « actif »**. Un compromis ne devrait pas rester actif apres
la vente. Non traite, pas mesure en ampleur.
```

### ÉTAPE 3 — le rapatriement *(P1.4)*

```
3.1 ⬜              refaire le rapport des ecarts avec l'apparieur repare
3.2 ⬜              fermer les 2 reserves : 413 ecarts contre 211 du rapport (lot 3)
                    et charge_commission, 23 480 valeurs
3.3 ⬜ ACCORD       les 7 colonnes qui ONT une case : P S T W AB AD (+ AF comparer)
3.4 ⬜ ACCORD       Y le reglement et AA la facture -> app_affaire_champ_app,
                    sur la transaction de role 'vente'
                    ⚠ MESURER D'ABORD les 1 062 lignes sans role 'vente'
3.5 ⬜ FREDERIC     le carnet des 5 colonnes de dossier (F G AH AI AJ), cle id_unique
                    + la case du numero de mandat (C, « les vides », ~9 utiles)
```

⛔⛔ **CE QU'IL NE FAUT PAS FAIRE, ET J'ALLAIS LE FAIRE** : créer la table
`app_affaire_suivi`. Mon propre audit du 09/11 l'avait déjà déclarée **inutile**
(*« ne pas l'appliquer »*), et `app_registre_champ_app` **ne convient pas** — mesuré le
12/11 : son `CHECK` n'accepte que `societe / agence / personne`, son `objet_id` est un
`bigint`, et son seul lecteur est `registreUtilisateurs.ts`. **C'est la table du
registre des agences, le chantier de l'autre session.**

### ÉTAPE 4 — la porte et les vagues *(P2/P3)*

```
4.1 ⬜ ACCORD       P2 la porte sans ecran : une RPC qui APPELLE
                    app_modifier_affaire_optimistic, jamais une copie
4.2 ⬜ ACCORD       P3a une affaire qu'il choisit
4.3 ⬜ ACCORD       P3b la reprise complete, LA NUIT (~2 a 3 h, arret sur conflit)
```

### ÉTAPE 5 — la bascule *(V1/P4)*

```
5.1 ⬜ FREDERIC     V1 lire les Apps Script du classeur (10 min) -- BLOQUE P4
5.2 ⬜ ACCORD       ecrire nos UUID dans la colonne affair_uuid du Sheet
                    ⭐ LE GEL SERT ICI, UNE FOIS -- puis il dort
5.3 ⬜ ACCORD       P4 le routeur : l'app ecrit dans le classeur, par l'uuid
```

### EN PARALLÈLE, indépendant du chantier

```
R-A ⬜              le frein Hektor PARTAGE (par processus : 4 workers = 4 req/s)
                    ⚠ il a mordu les 27-28/10
R-B ⬜              le balayage qui relance une commande morte depuis le carnet
```

---

**28/10/2026.** Écrit à la demande de Frédéric, **sans aucune mesure** : le run quotidien
tourne *(relancé après un échec, fin vers 9 h 30)* et ni `phase2.sqlite` ni Supabase ne
doivent être sollicités.

> ⚠ **Tous les chiffres de ce document ont été mesurés le 26/10 et doivent être rejoués.**
> Le parc bouge tous les jours.

---

# 1. OÙ ON EN EST

## Le projet, en deux étapes *(définies par Frédéric le 08/10)*

```
ETAPE 2   l'app fait tout le travail quotidien ; Hektor vit, il FOURNIT LES NUMEROS,
          les workers lui ENVOIENT les mises a jour              <- ON EST ICI
ETAPE 3   notre registre electronique des mandats -> la signature -> la pub,
          plus le site, le DNS, l'e-mail
```

## Les deux chantiers qui tournent en parallèle

```
⑧ GARDE CHEZ NOUS      une AUTRE conversation          🔧 EN COURS
   tous les champs saisis chez nous des le clic, et le controle au retour
   pieces 1-4 + R3 en production (25/10) · restent la piece 5, R2, R4, R5

LE CLASSEUR            cette conversation              ⏸ EN PAUSE, par sa decision
   relier le classeur Google au registre, puis inverser le sens des ecritures
```

## ⭐ Ce que ⑧ nous a déjà débloqué

Le 23/10 je disais : *« la reprise du classeur a besoin de R3, et R3 n'est pas posé —
sinon on tire 200 corrections dans le noir. »*

```
MESURE DU 26/10        le carnet      10 -> 56 lignes
                       avec VERDICT    5 -> 33
                       dont « arrivee », origine creation_app, 11 lignes avec la
                       valeur relue chez Hektor
```

✅ **R3 rend des verdicts. Le verrou est levé.**

## ⚠ Et ce que ⑧ n'a PAS changé

```
ancienne methode / donnees du 23/10   94,9 %
ancienne methode / donnees du 26/10   94,9 %    <- a methode constante, RIEN n'a bouge
nouvelle methode / donnees du 26/10   96,8 %    <- le gain vient de LA METHODE
```

C'est normal : **l'appariement dépend du classeur et des mandats**, que ⑧ ne touche pas.

---

# 2. LE BUT DU CHANTIER — ⚠ RÉÉCRIT LE 28/10, DANS LES MOTS DE FRÉDÉRIC

> *« Le classeur Sheet est notre **data officielle de vente** depuis quelques années, et
> actuellement. Le but est donc de **mettre à jour ma data pour correspondre à mon Sheet**.
> Puis **pouvoir ajouter et modifier les lignes à partir de l'app**. »*

```
① LE CLASSEUR FAIT FOI
     c'est la data OFFICIELLE des ventes depuis des annees, et encore aujourd'hui
     -> on met NOTRE data en conformite avec LUI

② ENSUITE on ajoute et on modifie les lignes DEPUIS L'APP
     et on ne saisit plus dans le classeur
```

⛔ **Ma formulation précédente — « trois sources, personne ne détient l'affaire entière » —
était une DESCRIPTION, pas un but.** Le but, c'est **la conformité, puis la bascule**.

## ⛔⛔ CE QUE ÇA CORRIGE DANS CE PLAN

J'avais écrit *« P1.4 : le patch d'alignement, **famille ① seulement** — là où le classeur
remplit un VIDE chez nous. RIEN D'AUTRE, les conflits se LISTENT. »*

**C'est contraire à sa demande du 22/10 :**

> *« les données **manquantes ET AUSSI DIVERGENTES** — c'est le classeur qui a raison si on
> est sûr de la correspondance »*

⛔ **J'avais rétréci son périmètre sans le dire.** Corrigé : **le patch corrige aussi les
divergences**, le classeur faisant foi.

```
AVANT (faux)   le classeur remplit un VIDE          -> les conflits se LISTENT
APRES (juste)  le classeur FAIT FOI                 -> il remplit ET il corrige
```

## Les deux seules réserves, et elles ne portent pas sur « qui a raison »

```
① ON NE CORRIGE QUE CE QU'ON A SUREMENT APPARIE
   ce n'est pas un doute sur le classeur : c'est que poser la BONNE valeur sur la
   MAUVAISE affaire est pire que ne rien faire (43 lignes se telescopaient --
   le cas GENILLON).  -> c'est tout l'objet de P1.

② CERTAINS CHAMPS NE PEUVENT PAS SE CORRIGER MECANIQUEMENT
   « Vente reglee » du classeur est une date de REGLEMENT, pas notre date d'acte
   (+3 jours de mediane, mesure du 19/10). Elle ne remplace donc pas la notre :
   ELLE A SA PROPRE PLACE.  Ce n'est pas « le classeur a tort », c'est
   « ce n'est pas le meme champ ».
```

## Ce qu'on produira

```
AVANT   le negociateur saisit dans l'app PUIS quelqu'un retape dans le classeur
APRES   il saisit UNE FOIS, dans l'app
          -> l'app envoie a HEKTOR ce qui le concerne
          -> l'app ecrit dans le CLASSEUR ce qui concerne la vente et la paie
          -> plus personne ne tape dans le classeur
```

⚠ **Le classeur ne disparaît pas** — il reste la référence officielle, et la paie s'en sert.
**Il change d'écrivain.**

⭐ **Le gain** : la data officielle sera enfin **dans l'app aussi** — donc retrouvable,
contrôlable, explicable. Une commission tapée dans une case Google n'a ni auteur, ni date,
ni trace.

---

# 3. LE PLAN, EN DEUX PHASES *(décidé par Frédéric le 22/10)*

```
PHASE A   UNE SEULE FOIS       le Sheet  ──>  le serveur + l'app
                               on rattrape TOUT ce qui est possible

PHASE B   ENSUITE, DEFINITIF   l'app  ──>  le Sheet
                               plus personne ne saisit dans le classeur
```

⭐ **Ce n'est PAS une synchronisation permanente à double sens.** Cette précision a retiré
**deux mécanismes délicats** du chemin critique : l'arbitre *(« qui gagne ? »)* et le journal
Apps Script.

## Et le mécanisme : la correction du classeur est **un geste de l'app comme un autre**

```
1  LE CARNET      on note : « affaire X, champ Y, valeur Z, origine = classeur »
2  LA COMMANDE    un travail est pose -- LES DEUX DANS LA MEME TRANSACTION
3  LE FACTEUR     le worker porte chez Hektor ce qui a une case chez lui
4  IL RELIT       et ecrit chez nous CE QUE HEKTOR A RETENU, jamais notre intention
5  LE VERDICT     arrivee / en_attente / conflit
6  CE QUI RESTE   commission · charge · notaire · facture · reglement
                  -> restent au carnet, c'est LEUR place : Hektor n'a pas de case
```

⭐ **Rien de neuf à inventer** : cette route existe, elle s'appelle **la classe B**, et elle
est en production.

---

# 4. 📋 LA LISTE DES TÂCHES

## T0 — DEUX GESTES RAPIDES, ET ILS SONT À TOI

| | tâche | taille |
|---|---|---|
| **T0.1** | mettre `scheduled/push_suivi_appsheet.py` **sous git** — il porte mon correctif du 22/10 et n'a **aucune histoire** | 2 min |
| **T0.2** | commiter les documents de `notice/` produits depuis le 22/10 | 2 min |

## P1 — RELIER ⏱ 3 j · **le préalable à tout**

| | marche | taille | risque |
|---|---|---|---|
| **P1.1** | la cascade **en lecture seule** — `phase2/checks/apparier_classeur.py` | 1 j | ✅ aucun |
| **P1.2** | geler le lien — table `app_classeur_lien` | 0,5 j | ⛔ ton accord |
| **P1.3** | le rapport des écarts, champ par champ | 0,5 j | ✅ lecture seule |
| **P1.4** | le patch de **mise en conformité** — le classeur **remplit** les vides **ET corrige** les divergences *(il fait foi)*. ⚠ Famille par famille, avec la liste sous les yeux avant d'écrire | 1 j | ⛔ ton accord |

**La règle appliquée** *(mise au point ensemble les 20 et 23/10)* :

```
0.  le mandat est-il un MANDAT DE RECHERCHE ? -> pas de bien, c'est NORMAL
1.  LE MANDAT                                     65 %
2.  + LA DATE                                     92 %    <- ton idee du 23/10
3.  + LA DATE LA PLUS PROCHE                      94 %
4.  + LE VENDEUR                                  95 %
5.  + LA VILLE                                    96 %
6.  + LE RATTRAPAGE par l'acquereur + le montant  96,8 %
    sinon -> ABSTENTION, et elle est NOMMEE
```

⚠ **Ces 96,8 % répondent à « quel BIEN ».** Il manque **« quelle AFFAIRE dans ce bien »**
— l'étage 2. **Ce taux-là, personne ne le connaît.** C'est P1 qui le dira.

**Les 4 contrôles, et le dernier est le plus important :**

```
le TEMOIN INVERSE    l'ancienne cascade doit rendre EXACTEMENT 4 527 (26/10, a rejouer)
l'EXCLUSIVITE        0 affaire ne recoit deux lignes
le cas GENILLON      bien 15220 : L40 -> 7500 et L3405 -> 7499, chacune la sienne
⛔ AUCUNE REGRESSION  toute ligne appariee par l'ANCIENNE et PERDUE par la nouvelle
                     est NOMMEE, une par une
```

## P2 à P4 — LA REPRISE, PUIS LE SENS INVERSE

| | tâche | taille | dépend de |
|---|---|---|---|
| **P2** | **la porte sans écran** — une RPC qui *appelle* `app_modifier_affaire_optimistic`, jamais une copie | 1 j | ⛔ ton accord |
| **P3a** | **la première vague : UNE affaire que tu choisis** — *Hektor accepte-t-il de corriger une affaire close ?* | 0,5 j | ✅ R3 est posé |
| **P3b** | **la reprise complète** — par vagues, **la nuit**, avec arrêt automatique sur conflit | 1 j | P3a concluant |
| **P4** | **le routeur + la destination classeur** | 2 j | ⛔ **V1** |

⚠ **Le débit de P3b** : ~200 corrections × 30-50 s = **2 à 3 heures**. ⛔ **La nuit
uniquement** — en journée, ça bloquerait les gestes de tes collaborateurs, même file.

## V — LES DEUX VERROUS, ET ILS SONT À TOI

```
V1  LIRE LES APPS SCRIPT DU CLASSEUR            10 min   ⛔ BLOQUE P4
      Sheet1 nourrit LA PAIE. Les onglets CA Mensuel, Reporting, 12 mois lissants
      et Agence n'ont AUCUNE formule -- un script les remplit, jamais ouvert.
V2  COLLER app_sheet_ecrit (le patch du 16/10)  15 min
      sans lui, on relit nos propres ecritures comme des saisies humaines
```

## R — LES RISQUES ACTIFS, INDÉPENDANTS DU CHANTIER

| | tâche | taille | urgence |
|---|---|---|---|
| **R-A** | **le frein Hektor PARTAGÉ** — il est par processus : 4 workers = 4 req/s, au-dessus du seuil qui a banni | 0,5 j | ⚠⚠ **et il a encore mordu les 27-28/10** |
| **R-B** | **le balayage qui relance une commande morte** depuis le carnet | 0,5 j | ⚠ sinon la reprise n'a aucun filet |
| **R-C** | **le geste écrit chez nous d'abord** — le mur est vers **16 utilisateurs**, pas 30 | ? | le gros morceau |

## F — LES FILS OUVERTS, À REGARDER QUAND TU VOUDRAS

```
11 VENTES portent le nom du MAUVAIS acquereur (celui du compromis ANNULE)       1 j
   biens 9340 · 11786 · 15220 · 17534 · 17536 · 23238 · 36344 · 41672 · 46585
         48311 · 54867

1 BIEN VIVANT affiche une offre morte : 62106 Bessamorel                        30 s
   -> un refus d'offre DANS Hektor suffit, aucun code

LES 56 ABSTENTIONS ont un air de famille : mandats ~4000-4300, TOUS en 2021,
   deux biens aux periodes QUI SE CHEVAUCHENT -- un lot reattribue en bloc ?

LES ~78 MANDATS INTROUVABLES, dont 17 hors de nos plages (27 000 a 91 000)
   -> une autre numerotation. PROTEXA ? un autre logiciel ? NON MESURE.
```

---

# 5. L'ORDRE, ET CE QUI DÉPEND DE QUOI

```
T0      git                        2 min   TOI
P1      RELIER                     3 j     ✅ ne depend de RIEN
P2      la porte                   1 j
P3a     une affaire                0,5 j   ✅ R3 est pose, le verrou est leve
P3b     la reprise, la nuit        1 j
──      LA BASCULE : la saisie passe par l'app  ──
V1      tu lis les Apps Script     10 min  ⛔ BLOQUE P4
P4      le routeur + le classeur   2 j

R-A     le frein Hektor partage    0,5 j   ⚠ EN PARALLELE, et c'est urgent
```

**Taille du chantier, hors R-C : ~8 jours.**

---

# 6. ⛔ CE QUI NE SE FAIT PAS

```
- ecrire dans le classeur avant que V1 soit fait
- rallumer CHAMPS_APP_AFFAIRE : vide EXPRES depuis le 16/09 (« le gel »)
- creer des colonnes au registre pour les champs financiers -> ils vont AU CARNET
- corriger l'acquereur : « changer qui achete n'est pas une correction,
  c'est une AUTRE affaire. Elle se cree, elle ne se rectifie pas. »
- deviner : une ligne non appariee reste SANS LIEN, et NOMMEE
- lancer P1 pendant le run de nuit ou la descente
```
