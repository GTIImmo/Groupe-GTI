# OÙ ON EN EST VRAIMENT — L'ANNULATION, LE DOSSIER, ET CE QUI BLOQUE

**09/11/2026, fin de journée.** Frédéric : *« réunis la logique sur l'annulation et les
points abordés, ensuite refais un audit enfin sur les bons codes, et cette fois fais-moi
un vrai résumé de la situation. »*

⛔ **Lecture seule. Rien n'est codé aujourd'hui en dehors des documents.**

---

# 1. ⛔ D'ABORD : CE QUI EXISTAIT DÉJÀ ET QUE J'AI CHERCHÉ À TORT

**J'ai re-audité pendant deux heures des choses déjà faites.** La cause est un seul mot :

> **Le projet dit « DOSSIER ». Une « affaire », chez nous, est UNE TRANSACTION.**
> J'ai cherché « id affaire », « identifiant d'affaire », « numéro d'affaire » — et je n'ai
> rien trouvé, parce que ce n'est pas le vocabulaire du projet.

```
CE QUI EXISTE                                          DEPUIS      OU
le REGISTRE DES TRANSACTIONS, 1 ligne par DOSSIER      31/10/2026  fonction
   app_registre_dossiers(p_annee) -> 25 colonnes,                  Supabase
   cle app_chaine_id, etape, 4 dates, honoraires,                  + api.ts:9296
   acquereur, nb_transactions, je_suis_nomme
   ⚠ C'EST UNE FONCTION DE LECTURE : elle CALCULE le registre
     a la demande. ON NE PEUT RIEN Y ECRIRE.
l'AUDIT DE L'ID DE DOSSIER, verdict + 4 conditions     29/10/2026  notice/AUDIT_EXPERT_
                                                                   ID_DOSSIER_2026-10-29.md
la MAQUETTE du registre (4 ecrans, vraies donnees)     29/10/2026  artifact 3FA3yDqW...
les 5 GESTES d'etat, par UNE SEULE fonction            deja la     App.tsx:19832
   handleGesteHektor('refus'|'accepte'|'annuler_                   handleGesteHektor
   compromis'|'supprimer_compromis'|'supprimer_vente')
la DATE RETROACTIVE + le MOTIF dans la modale          13/10/2026  App.tsx:14882, 23875
le CHOIX DE L'AFFAIRE dans la modale                   06/11/2026  statusChangeAffaireChoisie
```

⚠ **Et le registre des MANDATS n'est pas celui-là** : `app_registre_mandats_current`, une
ligne par (annonce, mandat), 24 579 lignes dont **16 647 sans aucune affaire**. Il ne montre
qu'**une** affaire par mandat (853 lignes en cachent 2 à 7) et **3 039 dossiers n'y
apparaissent pas** (aucun numéro de mandat). **Je l'ai mesuré en croyant mesurer le registre
des transactions.**

---

# 2. ⭐⭐ LA LOGIQUE DE L'ANNULATION, RÉUNIE — *sa conception, en un bloc*

## SA RÈGLE

> **Chez Hektor on supprime. Chez nous on annule — on ne supprime jamais, sauf si on
> choisit expressément le geste « supprimer ».**

## LA CASCADE, ET SON DÉCLENCHEUR

Les trois gestes d'état sont **liés au sein d'un même dossier**. Sélectionner l'un des trois
— offre refusée, compromis annulé, **vente annulée** — annule **le dossier et sa chaîne**.

```
LE GESTE              CHEZ HEKTOR                CHEZ NOUS
compromis annule      compromis SUPPRIME         compromis annule + date
                      offre     REFUSEE          offre     annulee + date
vente annulee         vente     SUPPRIMEE        vente     annulee + date
   (le champ NEUF)    compromis SUPPRIME         compromis annule + date
                      offre     REFUSEE          offre     annulee + date
offre refusee seule   offre     REFUSEE          offre     annulee + date
```

⭐ **Une seule chose à ajouter à l'écran** : un champ **« vente annulée »** dans l'onglet
**vendu** de la modale « changer statut ». Donc un **sixième geste** `annuler_vente`, à côté
de `supprimer_vente` qui existe déjà — les deux ne font pas la même chose.

⭐ **La date est demandée UNE FOIS**, avec un motif, et posée sur **toutes** les transactions
de la chaîne. **Et c'est la date qui fait l'état** : pas de champ « annulé » séparé.

## CE QUI LA FONDE — *tout est mesuré le 09/11*

```
« un des trois annule = le dossier annule »   VRAI A 100 % sur 1 133 dossiers.
   Mes 6 « exceptions » n'en etaient pas : 5 ont une VENTE (le dossier a abouti),
   la 6e un compromis annule (il est ferme). J'additionnais deux categories qui se
   CHEVAUCHENT, sans regarder les cas un par un.

l'offre et le compromis NE SONT PAS CONCURRENTS
   106 des 108 dossiers « a plusieurs pistes vivantes » = une offre acceptee + son
   compromis actif, le cas NORMAL. La vraie concurrence : 2 DOSSIERS.
   ➡ Un message « une autre piste reste ouverte » se tromperait 106 fois sur 108.

l'ordre compte                 compromis ACTIF  -> 0 offre refusee / 109 dossiers
                               compromis ANNULE -> 391 / 1 047  (37,3 %)

la cascade reparerait un defaut REEL
   656 OFFRES sont restees « acceptees » alors que leur compromis est annule (63 %).
   Fait a la main une fois sur trois, quand quelqu'un y pense.
   ⭐ Recoupe les 595 dossiers fantomes (une offre acceptee et plus rien, dont 545
     sans mouvement depuis plus de 18 mois, la plus ancienne de 2006).

l'effet sur le classeur        100 dossiers fermes par la date d'annulation
                               138 laisses OUVERTS a juste titre (67 ventes prevues,
                               26 ventes fixees, 20 compromis en attente, 17 offres)
```

## CE QUE LES GESTES SAVENT DÉJÀ FAIRE — *lu dans le code, pas déduit*

```
REFUSER une offre        ✅ 15 travaux, TOUS done, du 29/08 au 03/11. Zero echec.
   ⛔ J'avais conclu l'inverse en confondant deux gestes : MODIFIER une offre
     acceptee est impossible (200 + 0 octet, 9 sur 9 le 13/10), la REFUSER marche.
     Verbes differents : createOffre&init=1 contre updateOffre type=refus.
ANNULER un compromis     ✅ GET mode=annonce-SuiviVente-cloture, status verifie = 2.
   Si Hektor refuse -> restaurerEtatAffaire() remet l'etat d'avant chez nous.
   Puis un travail de RESYNCHRO de l'annonce est pose. Le statut de l'annonce
   N'EST PAS touche.
SUPPRIMER un compromis   ✅ GET mode=annonce-SuiviVente-deleteCompromis + idAnn.
   ⚠ « Le statut redescend -- par un second appel. » DONC LA CASCADE, QUI SUPPRIME,
     FERA REDESCENDRE LE STATUT DE L'ANNONCE. A vouloir explicitement.
SUPPRIMER une vente      ✅ GET mode=ventes-deleteVente&id=. Exige confirmer=true.
   « DEFINITIF : une vente n'a AUCUN etat chez Hektor, elle DISPARAIT. »
   Mesure : 9 277 ventes sur 9 277 ont un etat VIDE.
```

## ⛔ ET LE POINT QU'IL FAUT CHANGER DANS L'EXISTANT

Aujourd'hui, quand **l'app** ordonne une suppression, le worker **efface notre ligne** chez
Supabase, l'inscrit au journal `app_affaire_supprimee`, et le serveur local retire la sienne.
➡ **Donc supprimer chez Hektor supprime aussi chez nous, et la date d'annulation partirait
avec la ligne.**

⭐ **Le remède est déjà écrit — pour l'autre cas.** Quand c'est **Hektor** qui efface de son
côté, la doctrine est inverse : *« DELETE-NEVER reste la règle par défaut. Ce que Hektor
efface dans son coin garde sa ligne, marquée `present_in_hektor = false`. »*
➡ **Il suffit que le geste fasse pareil : marquer, pas effacer.** Sa règle est donc **plus
conforme au projet** que le geste actuel.

---

# 3. ⭐⭐⭐ OÙ RANGER UNE DONNÉE « PAR DOSSIER » — *la question qui bloque tout*

**Il n'existe aujourd'hui AUCUNE adresse fiable pour un dossier.** Les quatre candidats, et
pourquoi chacun échoue :

```
app_chaine_id            ⛔ IL BOUGE. C'est le plus petit app_affaire_id du groupe, donc
                           il change si une transaction plus ancienne ARRIVE (35 dossiers
                           mesures) ou si la tete disparait. Et la regle du 28/10 l'interdit
                           explicitement : « un numero de chaine ne doit JAMAIS servir de
                           point d'accrochage a quoi que ce soit d'exterieur ».
(annonce, numero_mandat) ⛔ IL ECRASE. 853 lignes du registre des mandats portent 2 a 7
                           dossiers, et 3 039 dossiers n'ont aucun numero de mandat.
                           66 % de fiabilite.
app_registre_dossiers    ⛔ C'EST UNE FONCTION DE LECTURE. Elle calcule a la demande,
                           on n'y ecrit pas.
« ID Unique » du classeur ⚠ CA MARCHE, mais c'est une BEQUILLE : une affaire nee dans
                           l'app n'a pas de ligne au classeur, donc pas de place.
```

## ⭐ ET L'ÉTIQUETTE EST DÉJÀ AUDITÉE ET APPROUVÉE — *29/10, verdict OUI*

**C'est un AJOUT, pas un remplacement** : la règle de regroupement n'est pas touchée
(0 ligne modifiée), `app_chaine_id` reste et continue comme avant, le worker n'est pas
concerné (0 occurrence, mesuré), aucune vue Supabase ne l'est, **et le retour arrière est
gratuit** — on cesse d'appeler la fonction, la colonne dort.

```
C1  la colonne entre dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS  AVANT tout remplissage
C2  l'etiquette se pose APRES le calcul des groupes, JAMAIS pendant
      (lecon du 05/09 : 9 000 dossiers coupes en deux)
C3  un SEUL emetteur, et c'est Supabase (lecon du 03/09, l'effacement silencieux)
C4  un JOURNAL des fusions et des scissions, lu par le moniteur
```

⭐ **C2 répond exactement à ma mesure du jour** : les 35 dossiers dont la tête est arrivée
après les autres sont précisément ce que cette condition évite.
⭐ **C4 comble la lacune nommée le 28/10** : *« aucun journal ne dit combien de dossiers ont
changé de numéro cette nuit ».*

## ⚠ ET C1 VAUT AUSSI POUR LA DATE D'ANNULATION — *même mécanisme, même piège*

La liste existe : `COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS` *(affaire_ledger.py:2300)* contient
`taux_honoraires`, `notaire_id`, `honoraires_entree_app`, `honoraires_sortie_app`,
`charge_commission_app`.

⛔ **La leçon du 07/09 dit pourquoi, et elle porte exactement sur une annulation** :

```
06:38  un compromis est ANNULE depuis l'app   -> `cancelled` chez Supabase en secondes
07:52  `--push` lance a la main               -> il pousse l'etat du MIROIR LOCAL, qui
                                                 date du run de 04:18 (encore `active`)
       ➡ L'ANNULATION EST EFFACEE CHEZ SUPABASE
08:05  le read-through ne repare rien
```

➡ **Toute colonne d'annulation doit entrer dans cette liste AVANT d'être remplie.**

---

# 4. ⭐ CE QUE TOUT ÇA DONNE, AU COMPLET

```
① L'ETIQUETTE DE DOSSIER      une colonne de app_affaire_ledger, type `_app`, posee par
                              Supabase APRES le calcul des groupes, dans la liste C1,
                              + le journal C4.      ⬜ IL NE MANQUE QUE LE FORMAT.
② LA DATE D'ANNULATION        une colonne de app_affaire_ledger, meme patron, dans la
                              liste C1. PAR TRANSACTION, ce que la cascade demande.
③ LES 7 COLONNES DU CLASSEUR  dans app_registre_champ_app (objet / objet_id / champ /
                              valeur), avec objet = 'dossier' et objet_id = L'ETIQUETTE.
                              ⭐ AUCUNE TABLE A CREER -- elle existe, et ne porte qu'UNE
                                ligne aujourd'hui.
④ LE GESTE                    un champ « vente annulee » dans l'onglet vendu, un sixieme
                              geste annuler_vente, et LA CASCADE dans handleGesteHektor.
⑤ LE GESTE INVERSE            vider la date REOUVRE le dossier. Patron existant : la date
                              de cloture du mandat.
⑥ LA FERMETURE DE LA CHAINE   un QUATRIEME critere, derriere un interrupteur, en DEUX
                              endroits qui doivent dire la meme chose (le run + Supabase).
```

⭐⭐ **ET LE PATCH `app_affaire_suivi` QUE J'AVAIS ÉCRIT DEVIENT INUTILE.** Il créait une
table clé par « ID Unique » parce que je ne savais pas où ranger une donnée de dossier. Avec
l'étiquette, `app_registre_champ_app` suffit. ➡ **Ne pas l'appliquer.**

---

# 5. ⬜ CE QUI ATTEND SA DÉCISION — **un seul point**

> **LE FORMAT DE L'ÉTIQUETTE.** Proposé le 30/10, jamais validé : **les deux** — un UUID
> caché + un numéro court lisible `D26-0431` *(année d'ouverture + rang ; max ~800
> dossiers/an)*.
> ⚠ **Réserve notée à l'époque : 108 dossiers n'ont aucune date**, donc pas d'année
> d'ouverture. Il faut une règle pour eux.

Tout le reste est spécifié depuis le 29/10. **Il manque le format, puis le « vas-y ».**

---

# 6. ⛔ MES FAUTES DE LA JOURNÉE, NOMMÉES — *pour ne pas les refaire*

```
① J'AI CHERCHE LE MAUVAIS MOT. « affaire » au lieu de « dossier ». Cout : un audit
   entier refait, et deux heures.  -> memoire posee.
② J'AI MESURE LE MAUVAIS REGISTRE. Celui des mandats, en croyant mesurer celui des
   transactions. Je n'avais pas lu ce que l'ecran interroge.
③ J'AI CONCLU « on ne peut pas refuser une offre chez Hektor » EN CITANT MA PROPRE
   MEMOIRE, dont la derniere ligne disait le contraire. Je m'etais arrete au tableau
   du haut -- comme le 28/10 sur le min() du chainage.  -> memoire corrigee.
④ J'AI ANNONCE « 10 exceptions » en additionnant deux categories qui se chevauchent,
   sans regarder les 6 cas un par un. Il n'y en avait AUCUNE.
⑤ J'AI ACCROCHE UNE TABLE A app_chaine_id, ce qu'une regle que J'AVAIS ECRITE le
   28/10 interdit explicitement.
⑥ J'AI PROPOSE UN MESSAGE CONDITIONNEL qui se serait trompe 106 fois sur 108.
```

⭐ **Le fil commun : j'ai déduit au lieu de lire, et j'ai agrégé au lieu de regarder les
cas.** Les deux leçons sont déjà écrites dans le projet. C'est lui qui a dû me les rappeler,
quatre fois.
