from __future__ import annotations

import unittest

from phase2.sync.push_contacts_to_supabase import delete_contacts_except_dirty
from phase2.sync.push_single_annonce_to_supabase import is_annonce_pending


class ContactDirtyDeleteGuardTest(unittest.TestCase):
    def test_delete_contacts_except_dirty_skips_pending_contacts(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str, list[str], int]] = []

            def delete_rows_by_filter(self, table: str, column: str, values: list[str], batch_size: int) -> int:
                self.calls.append((table, column, values, batch_size))
                return len(values)

        client = FakeClient()

        deleted = delete_contacts_except_dirty(
            client,
            contact_ids=["101", "102", "103"],
            dirty_contact_ids={"102"},
            batch_size=50,
        )

        self.assertEqual(deleted, 2)
        self.assertEqual(client.calls, [("app_contact_current", "hektor_contact_id", ["101", "103"], 50)])

    def test_delete_contacts_except_dirty_does_nothing_when_all_are_pending(self) -> None:
        class FakeClient:
            def delete_rows_by_filter(self, table: str, column: str, values: list[str], batch_size: int) -> int:
                raise AssertionError("dirty contacts must not be deleted")

        deleted = delete_contacts_except_dirty(
            FakeClient(),
            contact_ids=["101", "102"],
            dirty_contact_ids={"101", "102"},
            batch_size=50,
        )

        self.assertEqual(deleted, 0)


class AnnonceDirtyGuardTest(unittest.TestCase):
    def test_is_annonce_pending_reads_app_annonce_pending(self) -> None:
        class FakeClient:
            def _request(self, *, method: str, path: str, query: dict[str, str]):
                self.method = method
                self.path = path
                self.query = query
                return [{"app_dossier_id": 42}]

        client = FakeClient()

        self.assertTrue(is_annonce_pending(client, 42))
        self.assertEqual(client.method, "GET")
        self.assertEqual(client.path, "app_annonce_pending")
        self.assertEqual(client.query["app_dossier_id"], "eq.42")

    def test_is_annonce_pending_is_false_without_row(self) -> None:
        class FakeClient:
            def _request(self, *, method: str, path: str, query: dict[str, str]):
                return []

        self.assertFalse(is_annonce_pending(FakeClient(), 42))


if __name__ == "__main__":
    unittest.main()
