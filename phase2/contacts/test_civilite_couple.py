"""Couples · P1 (31/10/2026) : les codes de couple de Hektor traduits dans le NOM AFFICHE.

    .venv/Scripts/python.exe -m unittest phase2.contacts.test_civilite_couple
    (le Python du projet : l'import des mandats de recherche a besoin de tzdata)
"""
from __future__ import annotations

import unittest

from phase2.contacts.build_contacts_layer import ContactRow, civilite_affichee
from phase2.sync.importer_mandats_recherche import empreinte


def fiche(civilite, prenom="Jean", nom="DUPONT", couple=None, porteuse=None, numero="600001"):
    return ContactRow(
        hektor_contact_id=numero, hektor_agence_id=None, hektor_negociateur_id=None,
        civilite=civilite, nom=nom, prenom=prenom, archive=0, date_enregistrement=None,
        date_maj=None, email=None, portable=None, fixe=None, ville=None, code_postal=None,
        adresse=None, typologie_json=None, raw_json=None, synced_at=None,
        hektor_couple_contact_id=couple, couple_identite_porteuse=porteuse)


class CiviliteCouple(unittest.TestCase):
    def test_les_quatre_codes(self):
        self.assertEqual(fiche("M_Mme").display_name, "M. et Mme Jean DUPONT")
        self.assertEqual(fiche("Mme_M").display_name, "Mme et M. Jean DUPONT")
        self.assertEqual(fiche("Mme_Mme").display_name, "Mme et Mme Jean DUPONT")
        self.assertEqual(fiche("M_M").display_name, "M. et M. Jean DUPONT")

    def test_temoin_inverse_rien_d_autre_ne_bouge(self):
        # « Mr./Mme » est aussi porte par des personnes SEULES : on n'y touche pas.
        self.assertEqual(fiche("Mr./Mme").display_name, "Mr./Mme Jean DUPONT")
        self.assertEqual(fiche("M.").display_name, "M. Jean DUPONT")
        self.assertEqual(fiche("Mme.").display_name, "Mme. Jean DUPONT")
        self.assertEqual(fiche(None).display_name, "Jean DUPONT")
        self.assertEqual(fiche("M_Mme", prenom=None, nom=None).display_name, "Contact 600001")
        self.assertEqual(civilite_affichee(" M_Mme "), "M. et Mme")
        self.assertEqual(civilite_affichee("m_mme"), "m_mme")

    def test_fiche_de_menage_empruntant_sa_porteuse(self):
        vide = fiche("M_Mme", prenom=None, nom=None, couple="600000", porteuse="Jean DUPONT", numero="600002")
        self.assertEqual(vide.display_name, "M. et Mme Jean DUPONT")
        vide = fiche("Mr./Mme", prenom=None, nom=None, couple="600000", porteuse="Jean DUPONT", numero="600002")
        self.assertEqual(vide.display_name, "Mr./Mme Jean DUPONT")

    def test_l_import_des_mandats_de_recherche_ne_voit_aucune_difference(self):
        for code in ("M_Mme", "Mme_M", "Mme_Mme", "M_M"):
            avant = empreinte(f"{code} Jean DUPONT")
            apres = empreinte(fiche(code).display_name)
            self.assertEqual(avant, apres, code)
            self.assertEqual(apres, frozenset({"JEAN", "DUPONT"}), code)


if __name__ == "__main__":
    unittest.main()
