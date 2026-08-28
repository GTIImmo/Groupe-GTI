# -*- coding: utf-8 -*-
"""LE CONTRAT D'AUTORITE -- qui possede quel champ, et donc qui gagne.

UNE SEULE CONSTANTE, LUE PARTOUT. C'est l'exigence de la carte A1 du 19/08 :

    « Il devient une constante unique dans le code, lue par les trois portes
      d'entree : le rafraichissement de fiche, l'import de nuit annonces,
      l'import de nuit contacts. SURTOUT PAS TROIS COPIES. »

Trois copies, c'est la garantie qu'un jour l'une d'elles divergera -- et que
personne ne saura laquelle fait foi.

-------------------------------------------------------------------------------
COMMENT CA MARCHE, ET POURQUOI C'EST UNE SOUSTRACTION

Aujourd'hui, tout ce que l'app ecrit doit faire l'aller-retour par Hektor pour
survivre :

    l'app ecrit -> worker -> HEKTOR -> import de nuit -> retour dans l'app

Si un maillon casse, l'import ramene la valeur de Hektor et LA SAISIE EST
REMPLACEE. Un champ inscrit ici est retire de ce cycle : l'import ne le reecrit
plus, et la valeur de l'app survit sans l'aller-retour.

-------------------------------------------------------------------------------
POURQUOI LES DEUX LISTES N'ONT PAS LE MEME STATUT

CONTACTS -- les trois champs qui y figurent marchent depuis longtemps, et c'est
FACILE : Hektor ne les connait pas du tout. Il n'y a rien a arbitrer, personne a
contredire.

ANNONCES -- la liste est VIDE, et ce n'est pas un oubli. C'EST L'INTERRUPTEUR DU
CHANTIER. Vide = « Hektor gagne partout » = exactement le comportement
d'aujourd'hui. La machinerie existe et ne fait rien. On y inscrira des champs
UN PAR UN, quand les negociateurs seront passes sur l'app -- pas avant : tant
qu'ils saisissent dans Hektor, inscrire un champ ici le FIGERAIT sur une valeur
perimee dans l'app.

-------------------------------------------------------------------------------
LES TROIS ARBITRAGES EN ATTENTE (carte A1, section ORANGE)

Ce sont les seuls champs ou les deux cotes ont une raison legitime d'ecrire :

    statut_annonce / archive     le negociateur change le statut dans l'app,
                                 MAIS Hektor peut archiver de son cote
    negociateur_email            l'affectation se fait dans l'app, MAIS le worker
    commercial_id / _nom         s'impersonne avec cet identifiant pour ecrire
                                 dans Hektor -> la carte A1 recommande elle-meme
                                 « bleu jusqu'a la derniere phase »
    mandat_type / dates / montant  saisis dans l'editeur de mandat, MAIS ils
                                 cohabitent avec numero_mandat qui reste a Hektor

ET CE NE SONT PAS DES DECISIONS DE FOND SUR LE METIER. Le jour de la coupure,
Hektor n'existe plus : il n'y a plus rien a arbitrer, l'app gagne tout. Ce sont
donc TROIS REGLAGES DE TRANSITION, reversibles, qui ne valent que pendant la
cohabitation. On peut les laisser a « Hektor gagne » aussi longtemps qu'on veut.
"""
from __future__ import annotations

# ---------------------------------------------------------------- CONTACTS
# Hektor ne renvoie JAMAIS ces trois-la : seule l'app les ecrit. Aucun arbitrage
# possible, donc aucun risque. Ils fonctionnent depuis longtemps.
CHAMPS_APP_CONTACT: tuple[str, ...] = ("birth_date", "birth_place", "marital_status")

# ---------------------------------------------------------------- ANNONCES
# VIDE, ET C'EST VOULU -- voir l'en-tete. C'est l'interrupteur du chantier :
# le remplir change le comportement, le laisser vide ne change rien.
CHAMPS_APP_ANNONCE: tuple[str, ...] = ()


# ---------------------------------------------------------------- MANDATS
# C.13-b (28/08/2026) -- LE PREMIER CHAMP JAMAIS INSCRIT A CE CONTRAT.
#
# POURQUOI CELUI-LA, ET PAS UN AUTRE. Mesure du 28/08 sur les 24 939 mandats :
#
#     date de cloture      94 valeurs chez Hektor    0,4 %   <-- ce champ
#     date de fin      24 937                      100,0 %
#     date de debut    24 937                      100,0 %
#     montant          24 718                       99,1 %
#     mandants         24 648                       98,8 %
#     type             23 743                       95,2 %
#
# La reserve inscrite en tete de ce fichier -- « inscrire un champ ici le FIGERAIT
# sur une valeur perimee » -- ne s'applique pas a la date de cloture : il n'y a
# quasiment rien a figer, et le rythme s'effondre (24 clotures en juin, 7 en aout).
# C'est un champ que l'app CREE, pas un champ que Hektor entretient.
#
# Les cinq autres suivront quand l'editeur de mandat de l'app sera le seul lieu de
# saisie. La creation a deja migre -- depuis juin, 181 mandats neufs viennent de
# l'app contre 1 de Hektor -- mais la MODIFICATION d'un mandat ancien (un avenant)
# peut encore se faire chez lui, et nous n'avons pas d'historique pour la mesurer.
CHAMPS_APP_MANDAT: tuple[str, ...] = ("mandat_date_cloture",)

# ---------------------------------------------------------------- LA REGLE
# « L'APP GAGNE QUAND ELLE A QUELQUE CHOSE A DIRE » -- arbitrage de Frederic, 28/08.
#
# Le contrat des CONTACTS applique « l'app gagne » sans condition, et c'est sans
# danger : Hektor ne connait pas ces trois champs, il n'y a jamais rien a ecraser.
#
# Pour le mandat c'est FAUX, et ca s'est vu des le premier essai : le magasin a
# trouve TROIS mandats que Hektor dit clos et que Supabase ignore encore
# (30673/12264, 61513/74415, 61521/74417). Un « l'app gagne » aveugle aurait
# efface ces trois vraies clotures des la premiere nuit -- en silence, puisque
# c'est exactement ce que le contrat est cense faire.
#
#     l'app a une valeur   ->  elle gagne          (le but du chantier)
#     l'app n'a rien       ->  on ne touche a rien (on ne detruit pas)
#
# Moins pur, et assume : c'est un reglage de TRANSITION. Le jour de la coupure,
# Hektor n'aura plus rien a dire et l'app gagnera de fait.
VIDE_NE_GAGNE_PAS: bool = True


def contrat_vide() -> bool:
    """Vrai tant qu'aucun champ d'annonce n'appartient a l'app.

    Sert aux etapes du pipeline a dire clairement « je n'ai rien fait, et c'est
    normal » plutot qu'a passer en silence.
    """
    return not CHAMPS_APP_ANNONCE


def contrat_mandat_vide() -> bool:
    """Le pendant, pour les mandats. Voir CHAMPS_APP_MANDAT."""
    return not CHAMPS_APP_MANDAT
