"""Essais de la nature des fiches (couples, phase 1, 01/11/2026).

    .venv/Scripts/python.exe -m unittest phase2.contacts.test_nature_des_fiches
"""
from __future__ import annotations

import sqlite3
import unittest

from phase2.contacts import charger_ancien_logiciel as ch
from phase2.contacts import nature_des_fiches as m


def fiche(numero, lien=None, nom="", prenom="", civilite="", archive=0, agence="12", cible=None):
    return {"hektor_contact_id": str(numero), "hektor_couple_contact_id": str(lien) if lien else None,
            "nom": nom, "prenom": prenom, "civilite": civilite, "archive": archive,
            "hektor_agence_id": agence, "hektor_target_id": str(cible or numero), "supabase_sync_eligible": 0}


def calculer(*fiches, madames=None):
    index = {f["hektor_contact_id"]: f for f in fiches}
    return {l["hektor_contact_id"]: l for l in m.calculer(index, madames)}


class Natures(unittest.TestCase):
    def test_personne_seule(self):
        self.assertEqual(calculer(fiche(1, nom="DUPONT", prenom="Paul"))["1"]["nature_fiche"], "personne_seule")

    def test_personne_seule_mise_en_foyer_par_l_import_reste_seule(self):
        r = calculer(fiche(1, lien=1, nom="DUPONT", prenom="Paul", civilite="M."), fiche(2, lien=1))
        self.assertEqual(r["1"]["nature_fiche"], "personne_seule")
        self.assertIsNone(r["1"]["couple_deuxieme"])
        self.assertEqual(r["2"]["nature_fiche"], "case_conjoint_vide")

    def test_les_signes_d_un_couple(self):
        for f in (fiche(1, civilite="Mr./Mme", nom="DUPONT"), fiche(1, civilite="M_Mme", nom="DUPONT"),
                  fiche(1, nom="DUPONT", prenom="Paul et Anne"), fiche(1, nom="DUPONT & MARTIN", prenom="Paul"),
                  fiche(1, nom="DUPONT", prenom="Paul / Anne")):
            self.assertEqual(calculer(f)["1"]["nature_fiche"], "couple", f)

    def test_couple_par_le_prenom_de_la_deuxieme_fiche(self):
        r = calculer(fiche(1, lien=1, nom="DUPONT", prenom="Paul", civilite="M."),
                     fiche(2, lien=1, nom="DUPONT", prenom="Anne"))
        self.assertEqual(r["1"]["nature_fiche"], "couple")
        self.assertEqual(r["1"]["couple_deuxieme"], "conjoint_avec_prenom")
        self.assertEqual(r["2"]["nature_fiche"], "conjoint")

    def test_les_deuxiemes_fiches(self):
        r = calculer(fiche(1, lien=1, nom="DUPONT", civilite="Mr./Mme"), fiche(2, lien=1, nom="DUPONT"),
                     fiche(3, lien=99))
        self.assertEqual(r["1"]["couple_deuxieme"], "nom_recopie")
        self.assertEqual(r["2"]["nature_fiche"], "conjoint_sans_prenom")
        self.assertEqual(r["3"]["nature_fiche"], "case_vide_orpheline")   # sa principale n'existe pas

    def test_cas_c_d_e(self):
        r = calculer(fiche(1, lien=1, nom="A", civilite="Mr./Mme"), fiche(2, lien=1),
                     fiche(3, lien=3, nom="B", civilite="Mr./Mme"),
                     fiche(4, nom="C", civilite="Mr./Mme"))
        self.assertEqual(r["1"]["couple_deuxieme"], "case_vide")
        self.assertEqual(r["3"]["couple_deuxieme"], "aucune_deuxieme_fiche")
        self.assertEqual(r["4"]["couple_deuxieme"], "aucun_lien")

    def test_fiche_vide_sans_lien_est_orpheline(self):
        self.assertEqual(calculer(fiche(1, civilite="Mr./Mme"))["1"]["nature_fiche"], "case_vide_orpheline")


class Tris(unittest.TestCase):
    def test_t3_case_active_principale_archivee(self):
        r = calculer(fiche(1, lien=1, nom="A", archive=1), fiche(2, lien=1, archive=0), fiche(3, lien=1, archive=1))
        self.assertEqual(r["2"]["suit_principale_archivee"], 1)
        self.assertEqual(r["3"]["suit_principale_archivee"], 0)     # deja archivee
        self.assertEqual(r["1"]["suit_principale_archivee"], 0)

    def test_t3_temoin_inverse_principale_active(self):
        r = calculer(fiche(1, lien=1, nom="A", archive=0), fiche(2, lien=1, archive=0))
        self.assertEqual(r["2"]["suit_principale_archivee"], 0)

    def test_t4_sans_agence(self):
        r = calculer(fiche(1, nom="A", agence=""), fiche(2, nom="B"))
        self.assertEqual((r["1"]["supprimee_chez_hektor"], r["2"]["supprimee_chez_hektor"]), (1, 0))


class Civilite(unittest.TestCase):
    def test_madame_rendue_seulement_si_hektor_n_a_rien(self):
        r = calculer(fiche(10000001, nom="A", cible=1), fiche(10000002, nom="B", civilite="M.", cible=2),
                     madames={"1", "2"})
        self.assertEqual(r["10000001"]["civilite_app"], "Mme.")          # jointure par le numero HEKTOR
        self.assertEqual(r["10000001"]["civilite_source"], "ancien_logiciel")
        self.assertIsNone(r["10000002"]["civilite_app"])                 # Hektor a une civilite : elle gagne

    def test_pas_de_madame_sur_une_case_vide_ni_sans_table(self):
        self.assertIsNone(calculer(fiche(1), madames={"1"})["1"]["civilite_app"])
        self.assertIsNone(calculer(fiche(1, nom="A"), madames=None)["1"]["civilite_app"])

    def test_contradiction_dans_l_ancien_logiciel(self):
        conn = sqlite3.connect(":memory:")
        conn.execute(f"CREATE TABLE {m.TABLE_ANCIEN} (ancien_contact_id, gender, hektor_contact_id, methode, charge_le)")
        conn.executemany(f"INSERT INTO {m.TABLE_ANCIEN} VALUES (?, ?, ?, 'nd', 'x')",
                         [(1, 2, "7"), (2, 2, "8"), (3, 1, "8"), (4, 2, None)])
        self.assertEqual(m.madames_de_l_ancien_logiciel(conn), {"7"})
        self.assertIsNone(m.madames_de_l_ancien_logiciel(sqlite3.connect(":memory:")))


class Rattachement(unittest.TestCase):
    def index(self, *fiches):
        return {f["hektor_contact_id"]: f for f in fiches}

    def test_case_rattachee_a_la_seule_personne_nee_le_meme_jour(self):
        F = self.index(fiche(1, lien=99, civilite="Mr./Mme"), fiche(2, nom="DUPONT", prenom="Paul"),
                       fiche(3, nom="ACHETEUR"))
        for k, d in (("1", "2015-03-04"), ("2", "2015-03-04 10:00"), ("3", "2019-01-01")):
            F[k]["date_enregistrement"] = d
        faits, cote = m.rattachements(F, {"1": {"A"}, "2": {"A"}, "3": {"A"}}, {"A": {"1", "2", "3"}})
        self.assertEqual((faits, cote), ({"1": "2"}, {}))
        r = {l["hektor_contact_id"]: l for l in m.calculer(F, None, faits, cote)}
        self.assertEqual(r["1"]["nature_fiche"], "case_conjoint_vide")
        self.assertEqual(r["1"]["rattachee_a"], "2")
        # 02/11 (decision de Frederic) : la personne reste ce que dit Hektor -- PERSONNE SEULE --, sa case est masquee
        self.assertEqual((r["2"]["nature_fiche"], r["2"]["couple_deuxieme"]), ("personne_seule", None))
        self.assertEqual(r["2"]["rattachement"], "meme_bien_meme_jour")
        self.assertEqual(r["3"]["nature_fiche"], "personne_seule")      # temoin : l'autre personne du bien
        self.assertEqual(F["1"]["hektor_couple_contact_id"], "99")      # la couche n'est pas touchee

    def test_mises_de_cote(self):
        F = self.index(fiche(1), fiche(2, nom="A"), fiche(3, nom="B"), fiche(4), fiche(5, nom="C"))
        for k in "1234":
            F[k]["date_enregistrement"] = "2015-03-04"
        F["5"]["date_enregistrement"] = "2016-01-01"
        biens = {"1": {"A"}, "2": {"A"}, "3": {"A"}, "4": {"B"}, "5": {"B"}}
        faits, cote = m.rattachements(F, biens, {"A": {"1", "2", "3"}, "B": {"4", "5"}})
        self.assertEqual(faits, {})
        self.assertEqual(cote, {"1": "plusieurs_personnes_le_meme_jour", "4": "personne_nee_un_autre_jour"})

    def test_jamais_vers_une_seconde_fiche_ni_sans_bien(self):
        F = self.index(fiche(1), fiche(2, nom="A", lien=7), fiche(7, nom="P", lien=7), fiche(8))
        for f in F.values():
            f["date_enregistrement"] = "2015-03-04"
        faits, cote = m.rattachements(F, {"1": {"A"}, "2": {"A"}}, {"A": {"1", "2"}})
        self.assertEqual((faits, cote), ({}, {"1": "aucune_personne_sur_le_bien"}))   # 8 : aucun bien, ignoree


class Ecriture(unittest.TestCase):
    def test_idempotente(self):
        conn = sqlite3.connect(":memory:")
        lignes = m.calculer({"1": fiche(1, nom="A")}, None)
        m.ecrire(conn, lignes)
        m.ecrire(conn, lignes)
        self.assertEqual(conn.execute(f"SELECT count(*), nature_fiche FROM {m.TABLE}").fetchone(), (1, "personne_seule"))


class Appariement(unittest.TestCase):
    def setUp(self):
        self.H, self.idx = ch.indexer_hektor([
            {"hektor_contact_id": 5, "nom": "Dupont", "prenom": "Anne", "date_enregistrement": "2010-01-02 10:00:00",
             "hektor_couple_contact_id": 5, "email": "", "portable": "", "fixe": ""},
            {"hektor_contact_id": 6, "nom": "Dupont", "prenom": "", "date_enregistrement": "2010-01-02 10:00:00",
             "hektor_couple_contact_id": 5, "email": "", "portable": "", "fixe": ""},
            {"hektor_contact_id": 7, "nom": "Martin", "prenom": "", "date_enregistrement": "2011-01-01",
             "hektor_couple_contact_id": None, "email": "x@y.fr", "portable": "06 01 02 03 04", "fixe": ""},
        ])

    def test_nom_et_date_prefere_la_principale(self):
        a = {"last_name": "DUPONT", "first_name": "Anne", "time_created": "2010-01-02 10:00:00"}
        self.assertEqual(ch.apparier(a, self.H, self.idx), ("5", "nd"))

    def test_repli_e_mail_puis_telephone(self):
        self.assertEqual(ch.apparier({"last_name": "Autre", "email": "X@y.fr"}, self.H, self.idx), ("7", "em"))
        self.assertEqual(ch.apparier({"last_name": "Autre", "phone_mobile": "+33 6 01 02 03 04"}, self.H, self.idx),
                         ("7", "tel"))

    def test_non_trouvee(self):
        self.assertEqual(ch.apparier({"last_name": "Inconnu"}, self.H, self.idx), (None, "non_trouvee"))


if __name__ == "__main__":
    unittest.main()


class Notaires(unittest.TestCase):
    """⛔ 02/11 (règle de Frédéric) : une fiche NOTAIRE n'est jamais un couple -- historique et ajouts."""

    def calc(self, *fiches, notaires=None, rattache=None):
        index = {f["hektor_contact_id"]: f for f in fiches}
        return {l["hektor_contact_id"]: l for l in m.calculer(index, None, rattache, None, notaires)}

    def test_un_notaire_en_menage_n_est_pas_un_couple(self):
        r = self.calc(fiche(1, lien=1, nom="SCP DURAND et MARTIN", civilite="Mr./Mme"), fiche(2, lien=1),
                      notaires={"1"})
        self.assertEqual(r["1"]["nature_fiche"], "notaire")
        self.assertIsNone(r["1"]["couple_deuxieme"])
        self.assertEqual(r["2"]["nature_fiche"], "case_conjoint_vide", "sa case vide reste vide, masquee comme avant")

    def test_temoin_inverse_le_meme_menage_sans_registre_reste_couple(self):
        r = self.calc(fiche(1, lien=1, nom="SCP DURAND et MARTIN", civilite="Mr./Mme"), fiche(2, lien=1))
        self.assertEqual(r["1"]["nature_fiche"], "couple")

    def test_un_notaire_seul_devient_notaire(self):
        self.assertEqual(self.calc(fiche(1, nom="MAITRE", prenom="Anne"), notaires={"1"})["1"]["nature_fiche"], "notaire")

    def test_la_seconde_nommee_d_un_notaire_n_est_pas_son_conjoint(self):
        r = self.calc(fiche(1, lien=1, nom="SCP A"), fiche(2, lien=1, nom="B", prenom="Luc"), notaires={"1"})
        self.assertEqual(r["2"]["nature_fiche"], "personne_seule")

    def test_le_notaire_est_reconnu_par_son_numero_hektor(self):
        r = self.calc(fiche(10000001, lien=10000001, nom="SCP A", civilite="Mr./Mme", cible=4242), notaires={"4242"})
        self.assertEqual(r["10000001"]["nature_fiche"], "notaire")

    def test_un_notaire_ne_recoit_jamais_une_case(self):
        F = {"1": fiche(1, civilite="Mr./Mme"), "2": fiche(2, nom="SCP NOTAIRE")}
        F["1"]["nom"] = ""
        for f in F.values():
            f["date_enregistrement"] = "2020-01-01"
        faits, cote = m.rattachements(F, {"1": {"A"}, "2": {"A"}}, {"A": {"1", "2"}}, notaires={"2"})
        self.assertEqual((faits, cote), ({}, {"1": "seule_personne_est_un_notaire"}))
        faits, _ = m.rattachements(F, {"1": {"A"}, "2": {"A"}}, {"A": {"1", "2"}})
        self.assertEqual(faits, {"1": "2"}, "temoin inverse : sans le registre, il la recevait")

    def test_registre_lu_entree_et_sortie_liste_ou_objet(self):
        from phase2.contacts import notaires_registre as nr
        self.assertEqual(nr.notaires_du_json('{"entree": {"id": "7"}, "sortie": [{"id": "8"}, {"id": ""}]}'), {"7", "8"})
        self.assertEqual(nr.notaires_du_json('{"entree": null, "sortie": null}'), set())
        self.assertEqual(nr.notaires_du_json("pas du json"), set())
        c = sqlite3.connect(":memory:")
        self.assertEqual(nr.notaires_hektor(c), set(), "table absente : ensemble vide, la nuit continue")
        c.execute("CREATE TABLE app_affaire_ledger (notaires_json TEXT)")
        c.executemany("INSERT INTO app_affaire_ledger VALUES (?)", [('{"entree": {"id": "7"}}',), (None,), ("",)])
        self.assertEqual(nr.notaires_hektor(c), {"7"})


class RattachementNeFaitPasUnCouple(unittest.TestCase):
    """02/11 (decision de Frederic) : le rattachement masque la coquille, il ne fabrique pas de couple."""

    def test_la_personne_reste_seule_mais_un_signe_de_couple_compte_toujours(self):
        F = {"1": fiche(1, lien=99, civilite="Mr./Mme"), "2": fiche(2, nom="DIAZ", prenom="Paul"),
             "3": fiche(3, lien=98), "4": fiche(4, nom="DUPONT", prenom="Paul et Anne")}
        for k in F:
            F[k]["date_enregistrement"] = "2025-12-22"
        r = {l["hektor_contact_id"]: l for l in m.calculer(F, None, {"1": "2", "3": "4"}, None)}
        self.assertEqual(r["2"]["nature_fiche"], "personne_seule")
        self.assertEqual(r["1"]["nature_fiche"], "case_conjoint_vide", "la coquille reste masquee")
        self.assertEqual(r["4"]["nature_fiche"], "couple", "temoin : un couple ECRIT dans le nom reste couple (les 123)")

