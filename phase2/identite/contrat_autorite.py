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


def contrat_vide() -> bool:
    """Vrai tant qu'aucun champ d'annonce n'appartient a l'app.

    Sert aux etapes du pipeline a dire clairement « je n'ai rien fait, et c'est
    normal » plutot qu'a passer en silence.
    """
    return not CHAMPS_APP_ANNONCE
