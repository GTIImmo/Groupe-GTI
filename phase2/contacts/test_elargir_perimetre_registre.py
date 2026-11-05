"""Essais du perimetre « registre + partenaires » (04/11/2026, synthese couples §70-71).

    .venv/Scripts/python.exe -m unittest phase2.contacts.test_elargir_perimetre_registre
"""
from __future__ import annotations

import json
import os
import sqlite3
import unittest
from unittest import mock

from phase2.contacts import elargir_perimetre_registre as m
from phase2.contacts import metier_netty as netty


def base(contacts, relations, metiers=None):
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT PRIMARY KEY, nom TEXT, prenom TEXT, "
              "supabase_sync_eligible INTEGER, eligibility_reasons_json TEXT, date_enregistrement TEXT)")
    c.executemany("INSERT INTO app_contact_current VALUES (?,?,?,?,?,?)", contacts)
    c.execute("CREATE TABLE app_relation (app_contact_id INTEGER, hektor_annonce_id TEXT, source TEXT, "
              "present_in_hektor INTEGER, absent_depuis TEXT, retire_le TEXT)")
    c.executemany("INSERT INTO app_relation VALUES (?,?,?,?,?,?)", relations)
    if metiers is not None:
        netty.ecrire(c, metiers)
    return c


def eligibles(c):
    return {r[0]: json.loads(r[1] or "[]") for r in c.execute(
        "SELECT hektor_contact_id, eligibility_reasons_json FROM app_contact_current WHERE supabase_sync_eligible = 1")}


class PerimetreRegistre(unittest.TestCase):
    OFFRE = {"100": "0", "200": "2", "300": "0"}   # 100 vente, 200 LOCATION, 300 vente

    def test_le_proprietaire_d_un_bien_archive_entre(self):
        c = base([("10000001", "DUPONT", "Paul", 0, "[]", "2020-01-01")], [(10000001, "100", "hektor", 1, None, None)])
        self.assertEqual(m.executer(c, self.OFFRE, False), 0)
        self.assertEqual(eligibles(c), {"10000001": ["registre_relation"]})

    def test_locations_case_vide_lien_retire_ou_absent_restent_dehors(self):
        c = base([("10000002", "LOC", "Ana", 0, "[]", ""), ("10000003", "", "", 0, "[]", ""),
                  ("10000004", "RETIRE", "Luc", 0, "[]", ""), ("10000005", "ABSENT", "Eve", 0, "[]", "")],
                 [(10000002, "200", "hektor", 1, None, None), (10000003, "100", "hektor", 1, None, None),
                  (10000004, "100", "hektor", 1, None, "2026-10-01"), (10000005, "100", "hektor", 0, "2026-10-01", None)])
        m.executer(c, self.OFFRE, False)
        self.assertEqual(eligibles(c), {}, "location seule, case vide, lien retire, lien absent chez Hektor : personne n'entre")

    def test_location_plus_vente_entre(self):
        c = base([("10000006", "MIX", "Jo", 0, "[]", "")], [(10000006, "200", "hektor", 1, None, None), (10000006, "300", "hektor", 1, None, None)])
        m.executer(c, self.OFFRE, False)
        self.assertIn("10000006", eligibles(c))

    def test_un_lien_pose_par_l_app_compte(self):
        c = base([("20000001", "APP", "Zoe", 0, "[]", "")], [(20000001, "100", "app", 0, None, None)])
        m.executer(c, self.OFFRE, False)
        self.assertEqual(eligibles(c), {"20000001": ["registre_relation"]})

    def test_un_eligible_garde_ses_raisons_et_n_est_pas_touche(self):
        c = base([("10000007", "DEJA", "Max", 1, '["active_search"]', "")], [(10000007, "100", "hektor", 1, None, None)])
        m.executer(c, self.OFFRE, False)
        self.assertEqual(eligibles(c), {"10000007": ["active_search"]})

    def test_partenaire_netty_et_cumul_des_raisons(self):
        c = base([("10000008", "ETUDE", "Me", 0, "[]", ""), ("10000009", "BANQUE", "X", 0, "[]", "")],
                 [(10000008, "100", "hektor", 1, None, None)],
                 metiers={"10000008": [13], "10000009": [14]})
        m.executer(c, self.OFFRE, False)
        self.assertEqual(eligibles(c), {"10000008": ["registre_relation", "partenaire_netty"], "10000009": ["partenaire_netty"]})

    def test_a_blanc_n_ecrit_rien_et_idempotent(self):
        c = base([("10000001", "DUPONT", "Paul", 0, "[]", "")], [(10000001, "100", "hektor", 1, None, None)])
        m.executer(c, self.OFFRE, True)
        self.assertEqual(eligibles(c), {}, "a blanc")
        m.executer(c, self.OFFRE, False)
        self.assertEqual(m.executer(c, self.OFFRE, False), 0, "rejouer : rien de plus, verification verte")
        self.assertEqual(eligibles(c), {"10000001": ["registre_relation"]})

    def test_sans_registre_local_refus(self):
        c = sqlite3.connect(":memory:")
        c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT, nom TEXT, prenom TEXT, supabase_sync_eligible INTEGER, eligibility_reasons_json TEXT)")
        self.assertEqual(m.executer(c, {}, False), 2)

    def test_type_d_offre_inconnu_compte(self):
        c = base([("10000010", "INCONNU", "Al", 0, "[]", "")], [(10000010, "999", "hektor", 1, None, None)])
        m.executer(c, self.OFFRE, False)
        self.assertIn("10000010", eligibles(c), "bien absent du miroir : pas une location prouvee")


def base_hektor(contacts, relations=()):
    """Comme base(), avec la raison sociale (display_name) et le numero Hektor (hektor_target_id)."""
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT PRIMARY KEY, nom TEXT, prenom TEXT, display_name TEXT, "
              "hektor_target_id TEXT, supabase_sync_eligible INTEGER, eligibility_reasons_json TEXT)")
    c.executemany("INSERT INTO app_contact_current VALUES (?,?,?,?,?,?,?)", contacts)
    c.execute("CREATE TABLE app_relation (app_contact_id INTEGER, hektor_annonce_id TEXT, source TEXT, "
              "present_in_hektor INTEGER, absent_depuis TEXT, retire_le TEXT)")
    c.executemany("INSERT INTO app_relation VALUES (?,?,?,?,?,?)", list(relations))
    return c


class PartenairesHektor(unittest.TestCase):
    """La raison partenaire_hektor (04/11 soir, chantier partenaires §16)."""
    OFFRE = {"100": "0"}

    def test_un_syndic_de_hektor_entre(self):
        c = base_hektor([("10000020", "SYNDIC DES MONTS", "", "SYNDIC DES MONTS", "602487", 0, "[]")])
        self.assertEqual(m.executer(c, self.OFFRE, False, {"602487"}), 0)
        self.assertEqual(eligibles(c), {"10000020": ["partenaire_hektor"]})

    def test_une_societe_sans_nom_ni_prenom_entre_par_sa_raison_sociale(self):
        c = base_hektor([("10000021", "", "", "CABINET COPRO", "602010", 0, "[]"),
                         ("10000022", "", "", "", "602011", 0, "[]")])
        m.executer(c, self.OFFRE, False, {"602010", "602011"})
        self.assertEqual(eligibles(c), {"10000021": ["partenaire_hektor"]}, "sans raison sociale non plus : dehors")

    def test_la_raison_sociale_ne_fait_pas_entrer_une_case_vide_du_registre(self):
        c = base_hektor([("10000023", "", "", "M. et Mme X", "999", 0, "[]")], [(10000023, "100", "hektor", 1, None, None)])
        m.executer(c, self.OFFRE, False, {"602487"})
        self.assertEqual(eligibles(c), {}, "la garde de la case vide reste entiere pour le registre")

    def test_un_nom_fabrique_reste_dehors_interrupteur_allume(self):
        """05/11 : « Contact <numero> » est fabrique par la couche, ce n'est pas une raison sociale."""
        c = base_hektor([("10000024", "", "", "Contact 10000024", "423727", 0, "[]"),
                         ("10000025", "", "", "GIBERT IMMOBILIER", "414566", 0, "[]")])
        with mock.patch.dict(os.environ, {"APP_NOM_PARTENAIRE_PAR_LA_LISTE": "1"}):
            m.executer(c, self.OFFRE, False, {"423727", "414566"})
        self.assertEqual(eligibles(c), {"10000025": ["partenaire_hektor"]})

    def test_temoin_interrupteur_eteint_le_nom_fabrique_entre_comme_avant(self):
        c = base_hektor([("10000024", "", "", "Contact 10000024", "423727", 0, "[]")])
        with mock.patch.dict(os.environ, {"APP_NOM_PARTENAIRE_PAR_LA_LISTE": ""}):
            m.executer(c, self.OFFRE, False, {"423727"})
        self.assertEqual(eligibles(c), {"10000024": ["partenaire_hektor"]}, "eteint = la regle du 04/11, a l'identique")

    def test_temoin_sans_liste_de_hektor_rien_ne_change(self):
        c = base_hektor([("10000020", "SYNDIC", "", "SYNDIC", "602487", 0, "[]")])
        m.executer(c, self.OFFRE, False)
        self.assertEqual(eligibles(c), {})


class MetierNetty(unittest.TestCase):
    def test_appariement_sans_ambiguite(self):
        c = base([("1", "Dupont", "Paul", 0, "[]", "2020-01-01 10:00"), ("2", "MARTIN", "Ana", 0, "[]", "2021-02-02"),
                  ("3", "MARTIN", "Ana", 0, "[]", "2021-02-02")], [])
        fiches = [(("DUPONT", "PAUL", "2020-01-01"), [13]), (("MARTIN", "ANA", "2021-02-02"), [14]), (("ABSENT", "X", "2020-01-01"), [9])]
        trouves, bilan = netty.apparier(c, fiches)
        self.assertEqual(trouves, {"1": [13]})
        self.assertEqual((bilan["ambigues"], bilan["non appariees"]), (1, 1))

    def test_les_codes_clients_et_web_ne_sont_pas_des_pros(self):
        for code in (1, 2, 6, 7, 17, 23, 24, 29, 35, 80, 81, 82, 83, 85, 87):
            self.assertNotIn(code, netty.METIERS_PROS, code)
        for code in (13, 14, 34, 84, 9, 86):
            self.assertIn(code, netty.METIERS_PROS, code)


if __name__ == "__main__":
    unittest.main()
