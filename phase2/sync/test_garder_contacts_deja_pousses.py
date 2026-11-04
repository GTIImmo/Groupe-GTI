"""Essais : un contact deja envoye reste a jour (04/11/2026, synthese couples §61-64).

    PYTHONPATH=. .venv/Scripts/python.exe -m unittest phase2.sync.test_garder_contacts_deja_pousses
"""
from __future__ import annotations

import sqlite3
import unittest

from phase2.sync import push_contacts_to_supabase as push


def base() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE app_contact_current (hektor_contact_id TEXT PRIMARY KEY, supabase_sync_eligible INTEGER, archive INTEGER)")
    c.executemany("INSERT INTO app_contact_current VALUES (?,?,?)", [
        ("10000001", 1, 0),   # eligible
        ("10000002", 0, 1),   # deja envoye, plus eligible, archive chez Hektor : le cas des 216
        ("10000003", 0, 0),   # jamais envoye, pas eligible : reste dehors
    ])
    push.ensure_push_state(c)
    c.executemany(f"INSERT INTO {push.PUSH_STATE_TABLE}(table_name, row_key, payload_hash, pushed_at) VALUES (?,?,?,?)", [
        ("app_contact_current", "10000001", "h1", "2026-10-01"),
        ("app_contact_current", "10000002", "h2", "2026-10-03"),
        ("app_contact_relation_current", "10000003", "h3", "2026-10-03"),  # une autre table ne compte pas
    ])
    return c


def charges(c: sqlite3.Connection, where: str) -> set[str]:
    return {r[0] for r in c.execute(f"SELECT hektor_contact_id FROM app_contact_current {where}")}


class GarderContactsDejaPousses(unittest.TestCase):
    def test_le_perimetre_s_elargit_aux_seuls_contacts_deja_envoyes(self):
        c = base()
        self.assertEqual(charges(c, "WHERE supabase_sync_eligible = 1"), {"10000001"}, "temoin : le perimetre d'avant")
        self.assertEqual(charges(c, push.elargir_aux_contacts_deja_pousses("WHERE supabase_sync_eligible = 1")),
                         {"10000001", "10000002"})

    def test_les_autres_perimetres(self):
        c = base()
        self.assertEqual(charges(c, push.elargir_aux_contacts_deja_pousses("WHERE archive = 0 OR supabase_sync_eligible = 1")),
                         {"10000001", "10000002", "10000003"})
        self.assertEqual(push.elargir_aux_contacts_deja_pousses(""), "", "« all » est deja tout")

    def test_plus_aucune_disparue_pour_un_contact_deja_envoye(self):
        c = base()
        lignes = [{"hektor_contact_id": k} for k in charges(c, push.elargir_aux_contacts_deja_pousses("WHERE supabase_sync_eligible = 1"))]
        etat = {r[0] for r in c.execute(f"SELECT row_key FROM {push.PUSH_STATE_TABLE} WHERE table_name = 'app_contact_current'")}
        self.assertEqual(etat - {l["hektor_contact_id"] for l in lignes}, set())

    def test_interrupteur_eteint_par_defaut(self):
        import os
        ancien = os.environ.pop("APP_GARDER_CONTACTS_DEJA_POUSSES", None)
        push._GARDER_CONTACTS_ALLUME = None
        try:
            self.assertFalse(push.garder_contacts_deja_pousses_allume() and not ancien)
        finally:
            push._GARDER_CONTACTS_ALLUME = None
            if ancien is not None:
                os.environ["APP_GARDER_CONTACTS_DEJA_POUSSES"] = ancien


if __name__ == "__main__":
    unittest.main()
