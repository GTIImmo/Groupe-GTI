# AUDIT — OÙ NOUS EN SOMMES, LE 09/11/2026 AU SOIR

**Demandé par Frédéric** : *« Fais de nouveau un audit et explique moi où nous en sommes. »*

**LECTURE SEULE.** Rien n'a été écrit en base, ni dans le classeur, ni chez Hektor.
Deux patchs ont été écrits dans `supabase/` aujourd'hui, **aucun n'est collé**.

⚠ Cet audit ne refait pas A15 (ce matin, 09:53). Il **mesure ce qui a changé depuis**,
et il croise pour la première fois les 38 décisions avec le rapport de gel.

---

# 0. LES QUATRE RÉPONSES, EN HAUT DE PAGE

```
① LE VERROU QUI BLOQUAIT P1.4 DEPUIS LE 02/11 EST LEVE -- et c'est AUJOURD'HUI
   qu'il l'a ete. A15 § 4 disait : « 8 909 cases remplies des deux cotes et
   DIFFERENTES, CAS 4 NON TRANCHE, et c'est le seul verrou de P1.4 ».
   ⭐ Les 38 decisions prises aujourd'hui SONT cette reponse : « tout » = le
   classeur ecrase, « les vides » = nous gardons. Le CAS 4 est tranche, colonne
   par colonne. Je ne l'avais pas dit.

② P1.4 ECRIRAIT 10 240 CASES -- mesure neuve, en croisant le rapport de gel avec
   les 38 decisions. Et 6 806 cases d'ecart sont ECARTEES PAR DECISION, dont les
   1 727 du notaire et les 1 693 de la ville : ce ne sont plus des « ecarts a
   traiter », ce sont des choix faits.

③ MAIS SEULES 3 705 DE CES CASES SONT EXECUTABLES AUJOURD'HUI. Les 6 535 autres
   attendent une CASE OU ECRIRE -- les neuf champs du § 4 bis. ⭐ Et c'est
   exactement ce que le travail du jour attaque : l'etiquette de dossier debloque
   sept d'entre eux, la date d'annulation le huitieme.

④ LE DEFAUT DU RAPPORT EST TOUJOURS LA. Il reclame 731 cases de charge deja
   posees le 04/11 (23 474 au registre des mandats contre 7 la ou il regarde).
   Une ligne a corriger, et j'attends l'accord depuis ce matin.
```

---

# 1. ⭐⭐⭐ LE VERROU DU 02/11 EST LEVÉ

## Ce que disait A15 ce matin

> *« 8 909 cases **remplies des deux côtés, différentes** — LE CAS 4, NON TRANCHÉ.
> Et c'est le seul verrou de P1.4 : on ne peut pas écrire un patch de mise en
> conformité sans savoir, pour chaque champ, qui gagne en cas de conflit. »*

## Ce que les 38 décisions disent, dans ses mots du 09/11

```
TOUT            16 colonnes   le classeur ECRASE, ou remplit un champ NEUF
LES VIDES        7 colonnes   on ne remplit que NOS TROUS, on ne corrige rien
COMPARER JUSTE   1 colonne    on mesure et on affiche, on n'ecrit pas
RIEN            14 colonnes   on n'y touche pas
```

➡ **« Qui gagne en cas de conflit » est EXACTEMENT la question à laquelle
« tout » / « les vides » répond.** Le CAS 4 n'est pas une question qui reste : c'est
la question que les 38 décisions ont tranchée, colonne par colonne, aujourd'hui.

⚠ **Et une conséquence qu'il faut dire** : sur les 7 colonnes en « les vides », *« si
mon app a des erreurs on ne corrige rien »* — ses mots. Une valeur fausse chez nous
reste fausse. Ce n'est pas un oubli, c'est la décision.

---

# 2. CE QUE P1.4 ÉCRIRAIT — mesuré, colonne par colonne

Croisement du rapport de gel du jour (`A4_RAPPORT_GEL_ECARTS_SEULS_2026-11-09.csv`,
3 985 lignes) avec les décisions du 02/11. Les 21 champs du rapport ont tous une
décision ; aucun n'en manque.

```
champ              decision     ECART  cl. seul   A ECRIRE
----------------------------------------------------------
Vente Prevue       TOUT          1768        39      1807
Vente Reglee       TOUT             0      3265      3265   <- champ NEUF
Numero de facture  TOUT             0      3242      3242   <- champ NEUF
Negociateur 1      TOUT           430       162       592
Negociateur 2      TOUT           375        47       422
Negociateur 3      TOUT             9         2        11
Charge Commission  TOUT             0       731         0   <- DEJA FAIT le 04/11
Commission TTC     LES VIDES       83       299       299
Vendeur            LES VIDES       68       297       297
Offre Achat        LES VIDES      211       133       133
Compromis          LES VIDES       44        85        85
Vente Fixee        LES VIDES       61        39        39
Mandat             LES VIDES      134        28        28
Acquereur          LES VIDES      119        20        20
Prix               COMPARER       207         1         0
Nature             RIEN          1650        30         0
Ville              RIEN          1644        49         0
Notaire            RIEN          1370       357         0
Agence             RIEN           498        30         0
Etat Actuel        RIEN           172         0         0
product_ref        RIEN            69         9         0
----------------------------------------------------------
      par « tout »        9 339 cases
      par « les vides »     901 cases
                  TOTAL  10 240 cases   <-- c'est P1.4
      ecartees par decision  6 806 cases
      reclamees A TORT         731 cases (la charge)
```

## ⭐ Ce que ce tableau apprend, et qui n'était pas su

**Les deux plus gros postes ne sont pas des conflits.** `Vente Réglée` (3 265) et
`N° de facture` (3 242) affichent **zéro écart** : ce sont des colonnes dont nous
n'avons aucune case. Ensemble : **6 507 des 10 240 cases, soit 64 %**.

➡ **P1.4 est donc beaucoup moins une « mise en conformité » qu'un remplissage de
champs neufs.** Et un remplissage ne détruit rien — ce qui change la nature du risque.

**Le plus gros conflit réel est `Vente Prévue`** : 1 768 cases où les deux côtés
portent une date différente, et le classeur gagne. C'est le seul endroit où P1.4
écrase vraiment des valeurs à nous en nombre.

**Et 6 806 cases d'écart ne sont plus un problème.** Le notaire (1 727), la ville
(1 693), la nature (1 680), l'agence (528) : ces chiffres faisaient le gros des
« écarts à traiter » dans tous les rapports précédents. Ils sont **écartés par
décision**. Il ne faut plus les compter comme de la dette.

---

# 3. ⛔ CE QUI BLOQUE ENCORE — et le travail du jour tape dessus

Le § 4 bis du registre de décisions le dit depuis le 02/11 : **neuf champs ne sont pas
exécutables faute de case où écrire.** Mesuré en base ce soir :

```
LES 7 CHAMPS DE SUIVI       Y Vente Reglee . AA N° facture . F En attente de
                            G COMMENTAIRES . AH Avis a envoyer
                            AI Commentaire Avis . AJ Avis envoye
  ou ils doivent aller       app_registre_champ_app -- TABLE GENERIQUE, 1 ligne
  ce qui manquait            une ADRESSE stable par dossier
  ⭐ POSE AUJOURD'HUI        l'etiquette de dossier, patch DORMANT (commit aab95b8)
  cases concernees           6 507 au rapport (Y + AA) ; les 5 autres ne sont pas
                             mesurees par le rapport, ce sont des champs neufs

Z  ANNULEE                  896 dates, 100 % lisibles
  ou elle doit aller         une colonne par transaction + la cascade
  mesure en base ce soir     AUCUNE colonne d'annulation n'existe (0)
  ⭐ SPECIFIE AUJOURD'HUI    SPEC_ANNULATION_AFFAIRE + AUDIT_DATE_ANNULATION_TROIS_VOIES
  ⛔ rien n'est code

C  MANDAT                    28 cases
  ce qui manque              numero_mandat_app -- mesure en base : N'EXISTE PAS (0)
  pourquoi                   sans elle, la colonne est de CLASSE C et LA NUIT L'EFFACE
  ⬜ rien n'a avance aujourd'hui
```

➡ **Donc, aujourd'hui : 3 705 cases exécutables** *(V I K M P S T W AB AD)*, **6 507
bloquées par les champs de suivi**, **28 bloquées par le mandat**, et Z en plus.

---

# 4. L'ÉTAT MESURÉ DES PIÈCES, CE SOIR

```
PHASE A -- LE RATTRAPAGE (un seul sens, une seule fois)
  T0.1  apparier_classeur.py sous git           ⛔ TOUJOURS HORS GIT
  T0.2  push_suivi_appsheet.py sous git         ⛔ TOUJOURS HORS GIT
        100 notes de notice/ non suivies        ⚠ un chantier entier sans filet
  P1.1  la cascade en lecture seule             ✅ FAIT
  P1.2  le gel du lien                          ✅ FAIT -- app_classeur_lien 12 422
        regel du jour                           ✅ +9 liens (sauvegarde datee gardee)
        liens reellement casses                 ✅ ZERO -- les 5 de la vue portent
                                                   « Hektor ne l'a plus, NOUS la
                                                   gardons : le lien tient »
  P1.3  le rapport des ecarts                   ✅ RELANCE aujourd'hui, 3 985 lignes
        ⛔ son defaut sur la charge              TOUJOURS LA (voir § 5)
  P1.4  LE PATCH DE MISE EN CONFORMITE          ⬜ verrou LEVE, 3 705 cases pretes
  P2    la porte sans ecran                     ⬜
  P3a/b les vagues                              ⬜
  P4    le routeur + destination classeur       ⛔ bloque par le verrou Apps Script (V1)

L'ETIQUETTE DE DOSSIER (plan B0->B5 du 29/10)
  B0  decider le format                         ✅ FAIT CE SOIR -- D2026-0431 + UUID
  B1  compter fusions et scissions              ✅ sans objet : APP_CHAINAGE_V2=1 est
                                                   deja allume (.env:58, 20/10), les
                                                   426 deplacements ont deja eu lieu
  B2  le patch Supabase DORMANT                 ✅ ECRIT, commit aab95b8
      -- colle en base ?                        ⛔ NON (mesure : 0 colonne)
      -- la condition C1 cote local             ✅ FAITE, dans les DEUX listes
  B3  le premier remplissage                    ⬜ attend son « vas-y »
  B4  l'appel dans le run + la sentinelle       ⬜
  B5  re-cler app_classeur_lien sur l'etiquette ⬜

L'ANNULATION
  la logique reunie                             ✅ ecrite (cascade fondee a 100 %
                                                   sur 1 133 dossiers)
  la date d'annulation, ou elle vit             ✅ tranchee (voie C)
  le 6e geste + la cascade dans l'app           ⬜ rien code
  le champ « vente annulee » dans la modale     ⬜ rien code
```

---

# 5. ⛔ LE DÉFAUT DU RAPPORT, TOUJOURS LÀ

Mesure en base ce soir, inchangée depuis ce matin :

```
la charge POSEE, au registre des MANDATS              23 474 valeurs
ce que le rapport regarde (registre des AFFAIRES)          7 valeurs
ce qu'il en conclut                     « 731 cases a prendre au classeur »
```

➡ **Le rapport réclame un travail accompli le 04/11.** Une ligne à corriger : lui
faire lire `mandat_charge_honoraires_app` via `hektor_annonce_id`.

✅ **La réserve que A15 ouvrait à côté est, elle, LEVÉE** : *« la même question se pose
pour les 20 autres champs — ce n'est pas mesuré »*. Elle a été mesurée cet après-midi :
**une seule faute de case, la charge ; les 20 autres champs lisent la bonne.**

⛔ Toujours pas corrigé, parce que ça change un chiffre de référence du chantier.

---

# 6. CE QU'IL RESTE À DÉCIDER — et rien d'autre ne bloque

```
① LE FORMAT DE L'ETIQUETTE           D2026-0431 (ecrit) ou D26-0431 ?
                                      une ligne a changer, elle est marquee
② COLLER LE PATCH DORMANT (B2)        ecriture en base de production
③ LES NEUF CHAMPS DU § 4 bis          creation de cases = decision de perimetre
                                      -> debloque 6 535 des 10 240 cases
④ CORRIGER LE RAPPORT SUR LA CHARGE   une ligne ; change un chiffre de reference
⑤ LE STATUT DE L'ANNONCE              la cascade supprime le compromis, et
                                      supprimer FAIT REDESCENDRE le statut.
                                      Voulu, ou a brider ?
⑥ T0.1 / T0.2                         mettre le chantier sous git -- 2 minutes,
                                      en attente depuis le 28/10
```

---

# 7. ⭐ LA PHRASE QUI RÉSUME

**Les décisions sont prises. Le verrou de P1.4 est tombé aujourd'hui. Ce qui reste
n'est plus de l'analyse : ce sont des cases à créer et des patchs à coller.**

Et sur les 10 240 cases que le rattrapage écrira, **64 % sont des colonnes vides chez
nous** — pas des conflits. Le gros du travail ne détruit rien.
