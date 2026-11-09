# SPÉCIFICATION — ANNULER UNE AFFAIRE, DANS LES MOTS DE FRÉDÉRIC

**09/11/2026.** ⛔ **CE DOCUMENT DÉCRIT LA CIBLE, PAS LE PRÉSENT.** Frédéric,
09/11 : *« non c'est pour mon idée, pas actuellement »*. Ce que le code fait
aujourd'hui est mesuré dans `notice/AUDIT_DATE_ANNULATION_TROIS_VOIES_2026-11-09.md`
et rappelé ici **seulement** là où il faudra le changer.

⛔ **Rien n'est codé. Aucun « vas-y » n'a été donné.**

---

# 1. ⭐⭐⭐ LA RÈGLE, EN UNE PHRASE

> **Chez Hektor on supprime. Chez nous on annule — on ne supprime jamais, sauf si
> on choisit expressément le geste « supprimer ».**

*(Frédéric, 09/11 : « on peut pas annuler une vente sur Hektor, il faudra les
supprimer chez eux et supprimer aussi le compromis sinon ils ont un bug lorsqu'on
ajoute un nouveau compromis. Mais chez nous on met juste annulé, on ne supprime pas
sauf si on choisit le geste supprimer. »)*

⭐ **Cette règle est PLUS CONFORME à la doctrine du projet que le geste actuel.**
`phase2/sync/affaire_ledger.py:2442` dit déjà : *« DELETE-NEVER reste la règle par
défaut. Ce que Hektor efface dans son coin garde sa ligne, marquée
`present_in_hektor = false`. »*

---

# 2. LA CASCADE — *un geste sur une étape agit sur toute la chaîne*

*(Frédéric, 09/11 : « si on annule une transaction, exemple le compromis, l'app doit
passer l'offre liée en refusé ; si on met annulé sur une vente avec compromis et
offre d'achat, les 3 doivent être annulés et refusés, et une date d'annulation est
demandée pour mettre annulé sur le registre. »)*

```
LE GESTE                 CHEZ HEKTOR                      CHEZ NOUS
annuler le COMPROMIS     compromis  SUPPRIME              compromis  annule + date
                         offre      REFUSEE               offre      annulee + date
annuler la VENTE         vente      SUPPRIMEE             vente      annulee + date
                         compromis  SUPPRIME              compromis  annule + date
                         offre      REFUSEE               offre      annulee + date
annuler l'OFFRE seule    offre      REFUSEE               offre      annulee + date
```

⭐ **La date d'annulation est demandée UNE SEULE FOIS**, avec un motif, et elle est
posée sur **toutes** les transactions de la chaîne, dans la même écriture.

⭐ **ET C'EST LA DATE QUI FAIT L'ÉTAT** *(sa règle du 09/11)* : il n'y a pas de champ
« annulé » séparé. Une date présente dit que l'affaire est tombée. Un seul champ ne
peut pas se contredire ; deux champs, si.

## ⭐ POURQUOI SUPPRIMER CHEZ HEKTOR ET PAS ANNULER

```
① LA VENTE N'A PAS LE CHOIX. Le code le dit (console_job_worker.js, en-tete de
   handleDeleteHektorVente) : « une vente n'a AUCUN etat chez Hektor -- elle n'est
   pas annulee, elle DISPARAIT ». Mesure : 9 277 ventes sur 9 277 ont un etat VIDE.
② LE COMPROMIS, LUI, POURRAIT ETRE ANNULE (status 2) -- mais il faut le SUPPRIMER,
   parce qu'un compromis annule qui reste provoque un BUG chez Hektor a la creation
   du compromis SUIVANT.
   ⛔ CETTE REGLE NE SE DEDUIT D'AUCUNE MESURE : elle vient de l'experience de
   Frederic avec Hektor, declaree le 09/11/2026. Elle n'etait ecrite NULLE PART
   dans le projet. ⬜ Non eprouvee de notre cote -- a verifier le jour ou on
   touchera a ce geste, sur un bien d'essai.
③ L'OFFRE EST REFUSEE, PAS SUPPRIMEE, et ca marche : 15 travaux
   `change_hektor_offre_status` avec le geste « refus », TOUS `done`, du 29/08 au
   03/11/2026, zero echec.
   ⚠ ET J'AVAIS CONCLU L'INVERSE A TORT le 09/11, en confondant deux gestes : la
   mesure du 13/10 (« HTTP 200, 0 octet, 9 sur 9 ») portait sur l'OUVERTURE DU
   FORMULAIRE DE MODIFICATION d'une offre acceptee, pas sur son CHANGEMENT D'ETAT.
   Modifier une offre acceptee : impossible. La refuser : ca marche.
```

---

# 3. ⭐⭐ CE QUI FONDE LA CASCADE — *mesuré le 09/11*

```
« SI UN DES TROIS PASSE EN ANNULE, LE DOSSIER EST ANNULE » -> VRAI A 100 %.
   Sur 1 133 dossiers testes, zero contre-exemple. Les 6 que j'avais annonces
   comme des exceptions n'en sont pas : 5 ont une VENTE (le dossier a abouti),
   et la 6e a un compromis annule (le dossier est ferme).
   ⛔ Mon « 10 exceptions » additionnait deux categories qui SE CHEVAUCHENT, et je
   n'avais pas regarde les cas un par un. « Un controle qui agrege perd ce qui
   sert a agir. »

L'OFFRE ET LE COMPROMIS VONT ENSEMBLE, ILS NE SONT PAS CONCURRENTS.
   106 dossiers sur 108 « a plusieurs pistes vivantes » sont en fait UNE OFFRE
   ACCEPTEE + SON COMPROMIS ACTIF -- le cas normal d'un dossier en cours.
   ⭐ La VRAIE concurrence (deux offres vivantes) n'existe que sur 2 DOSSIERS.
   ➡ Donc un message « une autre piste reste ouverte » se tromperait 106 fois sur
     108. La cascade est la bonne reponse ; le message est l'exception.

L'ORDRE COMPTE, ET LA MESURE LE MONTRE.
   compromis ACTIF  -> offre refusee  0 sur 109 dossiers   (0,0 %)
   compromis ANNULE -> offre refusee  391 sur 1 047        (37,3 %)
   ➡ On annule le compromis d'abord, l'offre devient refusable ensuite.

ET LA CASCADE REPARERAIT UN DEFAUT REEL :
   656 OFFRES sont restees « acceptees » alors que leur compromis est annule --
   63 % des cas. C'est fait a la main une fois sur trois, quand quelqu'un y pense.
   ⭐ Ca recoupe les 595 dossiers fantomes (une offre acceptee et plus rien, dont
   545 sans mouvement depuis plus de 18 mois, la plus ancienne de 2006).
```

---

# 4. ⬜ CE QU'IL FAUT CHANGER DANS L'EXISTANT

```
① LE GESTE DE SUPPRESSION NE DOIT PLUS EFFACER NOTRE LIGNE.
   Aujourd'hui (affaire_ledger.py, appliquer_les_suppressions) : quand l'APP ordonne
   une suppression, le worker efface la ligne chez Supabase, l'inscrit au journal
   `app_affaire_supprimee`, et le serveur local retire la sienne.
   ➡ CIBLE : marquer `present_in_hektor = false` et poser la date d'annulation,
     exactement comme le projet le fait DEJA quand la disparition vient de Hektor.
   ⭐ Aucun risque de recreer la transaction chez Hektor : le mecanisme de recreation
     que le commentaire redoute concerne la copie SUPABASE, pas Hektor.
   ⚠ MODIFICATION DE CODE EXISTANT -> « vas-y » obligatoire.

② UNE COLONNE `date_annulation` DANS app_affaire_ledger, PROTEGEE PAR OMISSION.
   Le patron est etabli et nomme dans le code : « ce que le run ne reecrit pas, il
   le preserve. C'est la protection par omission. » Six colonnes en vivent deja
   (app_chaine_id, les notaires, jours_validite, les champs de contact).
   ⛔ NE PAS ecrire dans `state` : il EST dans le ON CONFLICT (ligne 909), donc
     recopie de Hektor chaque nuit.

③ LA CASCADE, DANS UNE SEULE FONCTION, APPELEE PAR LES DEUX PORTES.
   La porte du jour (le geste du negociateur) et la porte du rattrapage (une affaire
   historique, sans transaction a changer) doivent ecrire PAR LA MEME FONCTION.
   ⚠ C'est ce qui evite le defaut des « deux portes » du mandat, ou deux chemins
     faisaient la meme chose de deux facons et l'un contournait l'autre.

④ LE GESTE INVERSE. Vider la date doit REOUVRIR l'affaire. C'est ce qui rend
   l'ensemble sans risque. Le patron existe : la date de cloture du mandat
   (App.tsx:23875) -- « vider le champ EFFACE notre date et fait reapparaitre celle
   de Hektor s'il en a une ».
   ⬜ Non eprouve : qu'une chaine reouverte retrouve exactement sa forme d'avant.
     La deduction devrait le garantir (elle ne garde aucun etat), mais il faudra
     le voir une fois en vrai.

⑤ LA FERMETURE DE LA CHAINE PAR LA DATE. Un QUATRIEME critere de fermeture, a cote
   des trois existants (la vente, le compromis annule, l'offre refusee seule).
   ⛔ DERRIERE UN INTERRUPTEUR, et en DEUX endroits qui doivent dire la meme chose :
     recalculer_les_chaines()  phase2/sync/affaire_ledger.py  (le run, 05:00)
     app_chaine_pour()         Supabase                       (entre deux runs)
   ⚠ « Deux copies d'une formule divergent tot ou tard. » (patch du 05/09)
   ⭐ Effet mesure : 100 dossiers fermes, 138 laisses OUVERTS a juste titre (67
     ventes prevues, 26 ventes fixees, 20 compromis en attente, 17 offres).
```

---

# 5. ⬜ CE QUI RESTE À TRANCHER PAR LUI

```
. OU METTRE LE CHAMP A L'ECRAN : dans la modale de statut qui existe (rapide, mais
  elle envoie le statut a Hektor alors que l'annulation reste chez nous), ou comme
  un GESTE A PART sur la fiche de l'affaire (plus propre). Je recommande le geste
  a part.
. LE MESSAGE D'AVERTISSEMENT : son idee du 09/11 (« un message pour prevenir que le
  dossier va etre annule, on demande la raison et la date »). ⭐ Mesure : il dirait
  vrai dans 1 294 cas et se tromperait dans 2. Donc il s'affiche TOUJOURS, sauf
  sur les 2 dossiers en vraie concurrence.
. LES 3 LIGNES du classeur ou une VENTE existe alors que le classeur dit « annulee
  avec une date », et les 4 symetriques (compromis annule, classeur « vente reglee »).
```

---

# 6. ⚠ CE QUI N'EST PAS MESURÉ

```
. LE BUG DE HEKTOR a la creation d'un nouveau compromis quand l'ancien est seulement
  annule. Declare par Frederic le 09/11, jamais eprouve de notre cote.
. SI LE REFUS D'UNE OFFRE MARCHE AUSSI sans compromis du tout. Les 15 reussites ne
  disent pas dans quelle situation elles etaient.
. CE QUE DEVIENT LE STATUT DE L'ANNONCE dans la cascade. Mesure partielle : annuler
  un compromis ne touche PAS le statut de l'annonce (seule une resynchro est posee),
  mais SUPPRIMER un compromis « fait redescendre le statut, par un second appel »
  (console_job_worker.js, en-tete de handleDeleteHektorCompromis).
  ⛔ Donc la cascade, qui SUPPRIME, fera redescendre le statut. A verifier avant.
```
