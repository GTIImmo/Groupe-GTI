"""Essais : la nuit ne recrée jamais une ligne du registre pour un contact supprimé depuis l'app (05/11/2026, §23).

    .venv/Scripts/python.exe -m unittest phase2.contacts.test_registre_partenaires_supprimes
"""
from __future__ import annotations

import unittest
from unittest import mock

from phase2.contacts import registre_partenaires_reprise as r

METIERS = {("20000044", "syndic"): "transactions", ("10215568", "syndic"): "hektor",
           ("20000044", "notaire"): "transactions", ("10000001", "notaire"): "netty"}
LIENS = {(62774, "syndic"): {"partenaire": "20000044", "dossier": 1}, (63001, "syndic"): {"partenaire": "10215568"}}


class EcarterLesSupprimes(unittest.TestCase):
    def test_un_contact_supprime_n_a_plus_ni_metier_ni_lien(self):
        m, l, n = r.ecarter_les_supprimes(METIERS, LIENS, {"20000044"})
        self.assertEqual(set(m), {("10215568", "syndic"), ("10000001", "notaire")})
        self.assertEqual(set(l), {(63001, "syndic")})
        self.assertEqual(n, 3)

    def test_temoin_sans_suppression_rien_ne_change(self):
        m, l, n = r.ecarter_les_supprimes(METIERS, LIENS, set())
        self.assertEqual((m, l, n), (METIERS, LIENS, 0))

    def test_les_dictionnaires_d_origine_ne_sont_pas_touches(self):
        avant_m, avant_l = dict(METIERS), dict(LIENS)
        r.ecarter_les_supprimes(METIERS, LIENS, {"20000044", "10215568"})
        self.assertEqual((METIERS, LIENS), (avant_m, avant_l))

    def test_un_numero_entier_dans_un_lien_est_compare_en_texte(self):
        _, l, _ = r.ecarter_les_supprimes({}, {(1, "syndic"): {"partenaire": 20000044}}, {"20000044"})
        self.assertEqual(l, {})


class LeJournalDesSuppressions(unittest.TestCase):
    def test_les_deux_formes_du_numero_sont_lues(self):
        lignes = [{"id": "a", "app_contact_id": None, "identite": "20000044"},
                  {"id": "b", "app_contact_id": 10215568, "identite": "10215568"},
                  {"id": "c", "app_contact_id": None, "identite": None}]
        with mock.patch.object(r, "lire_tout", return_value=lignes) as lire:
            self.assertEqual(r.contacts_supprimes(), {"20000044", "10215568"})
        self.assertEqual(lire.call_args[0][0], "app_console_deleted_contact_log")


if __name__ == "__main__":
    unittest.main()
