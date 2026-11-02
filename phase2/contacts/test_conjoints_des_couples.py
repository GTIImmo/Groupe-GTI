"""Couples · P2 (31/10/2026) : la premiere fiche connait son conjoint.

    .venv/Scripts/python.exe -m unittest phase2.contacts.test_conjoints_des_couples
"""
from __future__ import annotations

import json
import sqlite3
import sys
import unittest
from pathlib import Path

from phase2.contacts import conjoints_des_couples as m

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sync"))
import push_contacts_to_supabase as push  # noqa: E402

COLONNES = ["hektor_contact_id", "hektor_target_id", "hektor_couple_contact_id", "civilite", "prenom", "nom",
            "phone_primary", "email", "archive", "supabase_sync_eligible", "eligibility_reasons_json",
            "couple_role", "display_name"]


def fiche(numero, lien, prenom=None, nom=None, eligible=0, archive=0, role=None, raisons="[]"):
    return {"hektor_contact_id": numero, "hektor_target_id": str(int(numero) - 10000000),
            "hektor_couple_contact_id": lien, "civilite": "M.", "prenom": prenom, "nom": nom,
            "phone_primary": "0600000000" if nom else None, "email": f"{numero}@essai.test" if nom else None,
            "archive": archive, "supabase_sync_eligible": eligible, "eligibility_reasons_json": raisons,
            "couple_role": role, "display_name": " ".join(x for x in [prenom, nom] if x) or f"Contact {numero}"}


def base(fiches):
    c = sqlite3.connect(":memory:")
    c.execute(f"CREATE TABLE app_contact_current ({', '.join(COLONNES)})")
    c.executemany(f"INSERT INTO app_contact_current VALUES ({','.join('?' for _ in COLONNES)})",
                  [tuple(f[k] for k in COLONNES) for f in fiches])
    return c


def lire(c, numero):
    c.row_factory = sqlite3.Row
    return dict(c.execute("SELECT * FROM app_contact_current WHERE hektor_contact_id = ?", (numero,)).fetchone())


def resume(c, numero):
    texte = lire(c, numero)["couple_json"]
    return json.loads(texte) if texte else None


PARC = [
    # A : couple nomme, premiere envoyee -> conjoint marque et envoye
    fiche("10000001", "10000001", "Jean", "ESSAI", eligible=1, raisons='["active_annonce_relation"]'),
    fiche("10000002", "10000001", "Marie", "ESSAI"),
    # B : seconde vide
    fiche("10000003", "10000003", "Paul", "VIDE", eligible=1, raisons='["active_search"]'),
    fiche("10000004", "10000003", role="menage_resolu"),
    # C : aucune seconde
    fiche("10000005", "10000005", "Luc", "SEUL", eligible=1, raisons='["active_search"]'),
    # D : deux secondes, une vide (plus petit numero) et une nommee -> la nommee
    fiche("10000006", "10000006", "Anne", "DOUBLE", eligible=1, raisons='["active_search"]'),
    fiche("10000007", "10000006", role="menage_resolu"),
    fiche("10000009", "10000006", "Zoe", "DOUBLE"),
    fiche("10000008", "10000006", "Yann", "DOUBLE"),
    # E : premiere NON envoyee -> conjoint resume, mais pas marque
    fiche("10000010", "10000010", "Eve", "DORT"),
    fiche("10000011", "10000010", "Adam", "DORT"),
    # F : premiere ARCHIVEE -> pas marque
    fiche("10000012", "10000012", "Ida", "ARCH", eligible=1, archive=1, raisons='["active_search"]'),
    fiche("10000013", "10000012", "Ugo", "ARCH"),
    # G : un ancien conjoint dont la premiere ne part plus -> retire
    fiche("10000014", "10000014", "Oto", "PLUS"),
    fiche("10000015", "10000014", "Ola", "PLUS", eligible=1, role="conjoint",
          raisons='["conjoint_d_un_contact_envoye"]'),
    # H : une personne seule, sans lien -> jamais touchee
    fiche("10000016", "", "Max", "LIBRE", eligible=1, raisons='["active_search"]'),
]


class Resumer(unittest.TestCase):
    def test_les_etats(self):
        c = base(PARC)
        self.assertEqual(m.executer(c), 0)
        a = resume(c, "10000001")
        self.assertEqual((a["etat"], a["autres"], a["conjoint"]["id"], a["conjoint"]["hektor_id"],
                          a["conjoint"]["prenom"], a["conjoint"]["envoye"]),
                         ("nomme", 0, "10000002", "2", "Marie", True))
        b = resume(c, "10000003")
        self.assertEqual((b["etat"], b["conjoint"]["id"], b["conjoint"]["prenom"]), ("vide", "10000004", None))
        self.assertEqual(resume(c, "10000005"), {"etat": "aucun", "autres": 0, "conjoint": None})
        d = resume(c, "10000006")
        self.assertEqual((d["etat"], d["autres"], d["conjoint"]["id"]), ("nomme", 2, "10000008"))
        self.assertEqual(resume(c, "10000010")["conjoint"]["envoye"], False)

    def test_le_conjoint_marque_et_envoye(self):
        c = base(PARC)
        m.executer(c)
        marie = lire(c, "10000002")
        self.assertEqual((marie["couple_role"], marie["supabase_sync_eligible"]), ("conjoint", 1))
        self.assertEqual(json.loads(marie["eligibility_reasons_json"]), [m.RAISON])
        self.assertEqual(lire(c, "10000008")["couple_role"], "conjoint")
        self.assertIsNone(lire(c, "10000009")["couple_role"], "la seconde nommee NON montree reste comme avant")

    def test_temoin_inverse_rien_d_autre_ne_bouge(self):
        c = base(PARC)
        m.executer(c)
        self.assertEqual(lire(c, "10000004")["couple_role"], "menage_resolu")
        self.assertEqual(lire(c, "10000007")["couple_role"], "menage_resolu")
        for numero in ("10000011", "10000013"):
            ligne = lire(c, numero)
            self.assertEqual((ligne["couple_role"], ligne["supabase_sync_eligible"]), (None, 0), numero)
        seul = lire(c, "10000016")
        self.assertEqual((seul["couple_json"], seul["couple_role"], seul["supabase_sync_eligible"]), (None, None, 1))
        self.assertIsNone(lire(c, "10000002")["couple_json"], "une seconde fiche ne porte pas de resume")

    def test_un_ancien_conjoint_est_retire(self):
        c = base(PARC)
        m.executer(c)
        ola = lire(c, "10000015")
        self.assertEqual((ola["couple_role"], ola["supabase_sync_eligible"], ola["eligibility_reasons_json"]),
                         (None, 0, "[]"))

    def test_idempotente(self):
        c = base(PARC)
        m.executer(c)
        avant = [tuple(r) for r in c.execute("SELECT * FROM app_contact_current ORDER BY 1")]
        m.executer(c)
        self.assertEqual(avant, [tuple(r) for r in c.execute("SELECT * FROM app_contact_current ORDER BY 1")])

    def test_a_blanc(self):
        c = base(PARC)
        m.executer(c, a_blanc=True)
        self.assertEqual(c.execute("SELECT COUNT(*) FROM app_contact_current WHERE couple_json IS NOT NULL").fetchone()[0], 0)
        self.assertIsNone(lire(c, "10000002")["couple_role"])

    def test_une_seule_fiche_ne_touche_que_son_couple(self):
        c = base(PARC)
        m.executer(c, contact_id="10000002")  # on rouvre la seconde : son couple est recalcule
        self.assertEqual(resume(c, "10000001")["etat"], "nomme")
        self.assertEqual(lire(c, "10000002")["couple_role"], "conjoint")
        self.assertIsNone(lire(c, "10000003")["couple_json"], "les autres couples ne sont pas touches")
        self.assertEqual(m.executer(c, contact_id="10000016"), 0, "une personne seule : rien a faire")


class Push(unittest.TestCase):
    def tearDown(self):
        push._COUPLE_CONJOINT_ALLUME = None

    def ligne(self, c, numero):
        c.row_factory = sqlite3.Row
        return c.execute("SELECT * FROM app_contact_current WHERE hektor_contact_id = ?", (numero,)).fetchone()

    def test_eteint_la_colonne_ne_part_pas(self):
        c = base(PARC)
        m.executer(c)
        push._COUPLE_CONJOINT_ALLUME = False
        charge = push.normalize_contact_row(self.ligne(c, "10000001"))
        self.assertNotIn("couple_json", charge)
        self.assertNotIn("Marie", charge["search_text"])

    def test_allume_le_resume_part_et_la_recherche_trouve_le_conjoint(self):
        c = base(PARC)
        m.executer(c)
        push._COUPLE_CONJOINT_ALLUME = True
        charge = push.normalize_contact_row(self.ligne(c, "10000001"))
        self.assertEqual(charge["couple_json"]["conjoint"]["prenom"], "Marie")
        for morceau in ("Marie", "0600000000", "10000002@essai.test"):
            self.assertIn(morceau, charge["search_text"])
        vide = push.normalize_contact_row(self.ligne(c, "10000003"))
        self.assertEqual(vide["search_text"], "Paul VIDE 10000003@essai.test 0600000000",
                         "seconde vide : rien n'est ajoute")

    def test_une_valeur_vide_ne_change_pas_l_empreinte(self):
        sans = {"hektor_contact_id": "1", "nom": "X", "refreshed_at": "a"}
        avec_vide = dict(sans, couple_json=None)
        self.assertEqual(push.stable_payload_hash(sans), push.stable_payload_hash(avec_vide))
        self.assertNotEqual(push.stable_payload_hash(sans),
                            push.stable_payload_hash(dict(sans, couple_json={"etat": "aucun"})))


if __name__ == "__main__":
    unittest.main()


class Notaires(unittest.TestCase):
    """⛔ 02/11 (règle de Frédéric) : la première fiche d'un notaire n'a ni résumé ni conjoint."""

    def test_premiere_d_un_notaire_ni_resume_ni_conjoint(self):
        c = base(PARC)
        c.execute("CREATE TABLE app_affaire_ledger (notaires_json TEXT)")
        c.execute("INSERT INTO app_affaire_ledger VALUES (?)", ('{"sortie": {"id": "1"}}',))   # cible de 10000001
        m.executer(c)
        self.assertIsNone(resume(c, "10000001"))
        self.assertIsNone(lire(c, "10000002")["couple_role"], "la seconde nommee d'un notaire n'est pas marquee conjoint")
        self.assertIsNotNone(resume(c, "10000003"), "temoin : les autres couples gardent leur resume")

    def test_un_resume_deja_pose_s_efface(self):
        c = base(PARC)
        m.executer(c)
        self.assertIsNotNone(resume(c, "10000001"))
        c.execute("CREATE TABLE app_affaire_ledger (notaires_json TEXT)")
        c.execute("INSERT INTO app_affaire_ledger VALUES (?)", ('{"entree": {"id": "1"}}',))
        m.executer(c)
        self.assertIsNone(resume(c, "10000001"))
        self.assertIsNone(lire(c, "10000002")["couple_role"])
