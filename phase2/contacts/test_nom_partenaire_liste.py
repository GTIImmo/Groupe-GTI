"""Essais : le nom d'un syndic / diagnostiqueur sans nom ni prenom vient de la liste de l'annonce (05/11/2026).

Note : notice/CHANTIER_ANNUAIRE_PARTENAIRES_2026-11-04.md §19.

    .venv/Scripts/python.exe -m unittest phase2.contacts.test_nom_partenaire_liste
"""
from __future__ import annotations

import os
import sqlite3
import unittest
from unittest import mock

from phase2.contacts import build_contacts_layer as b

COLONNES = ("hektor_contact_id, hektor_agence_id, hektor_negociateur_id, civilite, nom, prenom, archive, "
            "date_enregistrement, date_maj, email, portable, fixe, ville, code_postal, adresse, typologie_json, "
            "raw_json, synced_at, hektor_couple_contact_id")


def miroir(contacts, choix=None):
    """contacts : (numero, nom, prenom, refCouple) ; choix : (liste, numero, libelle), ou None = pas de table."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(f"CREATE TABLE hektor_contact ({COLONNES})")
    for numero, nom, prenom, couple in contacts:
        c.execute(f"INSERT INTO hektor_contact ({COLONNES}) VALUES (?,1,NULL,'',?,?,0,NULL,NULL,NULL,NULL,NULL,"
                  "NULL,NULL,NULL,'[\"partenaire\"]','{}',NULL,?)", (numero, nom, prenom, couple))
    if choix is not None:
        c.execute("CREATE TABLE hektor_diag_contacts_choix (liste TEXT, hektor_contact_id TEXT, libelle TEXT, "
                  "premier_vu_le TEXT, dernier_vu_le TEXT)")
        c.executemany("INSERT INTO hektor_diag_contacts_choix VALUES (?,?,?,NULL,NULL)", choix)
    return c


def noms(conn):
    return {c.hektor_contact_id: c.display_name for c in b.load_contacts(conn)}


CHOIX = [("syndic", "414566", "GIBERT IMMOBILIER"), ("diagnostiqueur", "423727", ""),
         ("syndic", "500", "FONCIA LOIRE AUVERGNE")]


class NomParLaListe(unittest.TestCase):
    def setUp(self):
        self.allume = mock.patch.dict(os.environ, {"APP_NOM_PARTENAIRE_PAR_LA_LISTE": "1"})
        self.allume.start()

    def tearDown(self):
        self.allume.stop()

    def test_un_syndic_sans_nom_prend_le_nom_de_la_liste(self):
        self.assertEqual(noms(miroir([("414566", "", "", None)], CHOIX))["414566"], "GIBERT IMMOBILIER")

    def test_un_libelle_vide_garde_le_numero(self):
        self.assertEqual(noms(miroir([("423727", "", "", None)], CHOIX))["423727"], "Contact 423727")

    def test_un_contact_qui_a_un_nom_garde_le_sien(self):
        self.assertEqual(noms(miroir([("500", "FONCIA", "", None)], CHOIX))["500"], "FONCIA")

    def test_hors_de_la_liste_rien_ne_change(self):
        self.assertEqual(noms(miroir([("777", "", "", None)], CHOIX))["777"], "Contact 777")

    def test_une_fiche_de_menage_n_est_pas_touchee(self):
        # Seconde fiche d'un menage dont la porteuse a disparu : la regle des couples reste maitre.
        c = miroir([("414566", "", "", "999")], CHOIX)
        self.assertEqual(noms(c)["414566"], "Contact 414566")

    def test_le_syndic_passe_avant_le_diagnostiqueur(self):
        c = miroir([("414566", "", "", None)], [("diagnostiqueur", "414566", "AUTRE"), *CHOIX])
        self.assertEqual(noms(c)["414566"], "GIBERT IMMOBILIER")

    def test_sans_la_table_de_la_liste_rien_ne_casse(self):
        self.assertEqual(noms(miroir([("414566", "", "", None)]))["414566"], "Contact 414566")

    def test_la_cible_hektor_reste_le_numero_de_hektor(self):
        contact = b.load_contacts(miroir([("414566", "", "", None)], CHOIX))[0]
        self.assertEqual((contact.hektor_target_id, contact.nom), ("414566", None), "on n'invente pas de nom")


class TemoinEteint(unittest.TestCase):
    def test_interrupteur_eteint_le_nom_reste_celui_d_avant(self):
        with mock.patch.dict(os.environ, {"APP_NOM_PARTENAIRE_PAR_LA_LISTE": "0"}):
            self.assertEqual(noms(miroir([("414566", "", "", None)], CHOIX))["414566"], "Contact 414566")


if __name__ == "__main__":
    unittest.main()
