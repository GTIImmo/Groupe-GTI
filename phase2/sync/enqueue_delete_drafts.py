"""Suppression en lot des brouillons (isDraft) d'un negociateur + nettoyage complet.

Contexte : le worker de suppression n'est PAS relance a chaque fois ; c'est un
service permanent (`console.worker.admin`) qui consomme la file `app_console_job`.
On enfile donc N jobs `delete_hektor_annonce` en une passe, il les traite un par
un (Hektor xmlrpc mode=supprimeannonce + verif + nettoyage doc/Supabase/local +
journal app_console_deleted_annonce_log).

Le "detail" n'a pas besoin d'etre uploade avant : c'est une contrainte de l'UI
(bouton Supprimer dans la fiche ouverte), pas du backend -- on la court-circuite.

DEUX phases :

  Phase 1 (enqueue)  : enfile les jobs delete.
  Phase 2 (cleanup)  : APRES que le worker a fini (job delete = done), purge ce
                       que le handler ne nettoie PAS :
                         - Supabase : app_brouillon_annonce_index_current
                                      (+ app_brouillon_annonce_detail_cache)
                         - Local    : hektor.sqlite -> hektor_annonce_draft_state
                       Sans ce nettoyage local, le prochain push_upgrade
                       reconstruirait l'index brouillon depuis draft_state
                       (is_draft=1) et les brouillons "reviendraient".

Usage :
  python enqueue_delete_drafts.py                      # DRY-RUN enqueue (liste)
  python enqueue_delete_drafts.py --apply              # enfile les jobs delete
  python enqueue_delete_drafts.py --cleanup            # DRY-RUN cleanup (montre)
  python enqueue_delete_drafts.py --cleanup --apply    # nettoie reellement
  python enqueue_delete_drafts.py --nego-id 23 [...]   # autre negociateur
  python enqueue_delete_drafts.py --ids 62240,62248 [...]  # sous-ensemble

Env (.env racine) : SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../Projet
HEKTOR_DB = PROJECT_ROOT / "data" / "hektor.sqlite"
# Meme chaine de chargement que le worker Console (console_job_worker.js) :
# les creds Supabase vivent dans apps/hektor-v1/.env (VITE_SUPABASE_URL +
# SUPABASE_SERVICE_ROLE_KEY).
CANDIDATE_ENVS = [
    PROJECT_ROOT / "apps" / "hektor-v1" / ".env",
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "Console" / ".env",
    Path(__file__).resolve().parent / ".env",
]

REASON = "Nettoyage brouillons vides"
SAFETY_MAX = 30
JOB_PRIORITY = 5


def load_env() -> None:
    for path in CANDIDATE_ENVS:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


class Supabase:
    def __init__(self, base_url: str, key: str) -> None:
        self.base = base_url.rstrip("/")
        self.key = key

    def _req(self, method: str, path: str, *, query: str | None = None,
             body: object | None = None, prefer: str | None = None) -> object | None:
        url = f"{self.base}/rest/v1/{path}"
        if query:
            url = f"{url}?{query}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, headers=headers, method=method, data=data)
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None

    def get(self, path: str, query: str) -> list:
        out = self._req("GET", path, query=query)
        return out if isinstance(out, list) else []

    def insert(self, path: str, rows: list[dict]) -> list:
        out = self._req("POST", path, body=rows, prefer="return=representation")
        return out if isinstance(out, list) else []

    def delete_in(self, path: str, column: str, ids: list[str]) -> list:
        q = urllib.parse.urlencode({column: f"in.({','.join(ids)})"})
        out = self._req("DELETE", path, query=q, prefer="return=representation")
        return out if isinstance(out, list) else []


def resolve_ids(sb: Supabase, args) -> list[str]:
    if args.ids.strip():
        ids = [x.strip() for x in args.ids.split(",") if x.strip()]
        print(f"Ids fournis explicitement : {len(ids)}")
        return ids
    print(f"Brouillons du negociateur {args.nego_id} :")
    q = urllib.parse.urlencode({
        "select": "hektor_annonce_id,titre_bien,ville,statut_annonce",
        "commercial_id": f"eq.{args.nego_id}",
        "order": "hektor_annonce_id.asc",
    })
    rows = sb.get("app_brouillon_annonce_index_current", q)
    for r in rows:
        print(f"  - {r['hektor_annonce_id']:>8}  {r.get('statut_annonce') or '?':<11} "
              f"{(r.get('titre_bien') or '')[:40]:<40} {r.get('ville') or ''}")
    return [str(r["hektor_annonce_id"]) for r in rows]


def delete_job_status(sb: Supabase, ids: list[str]) -> dict[str, str]:
    q = urllib.parse.urlencode({
        "select": "hektor_annonce_id,status",
        "job_type": "eq.delete_hektor_annonce",
        "hektor_annonce_id": f"in.({','.join(ids)})",
        "order": "requested_at.desc",
    })
    seen: dict[str, str] = {}
    for r in sb.get("app_console_job", q):  # dernier statut connu par id
        seen.setdefault(str(r["hektor_annonce_id"]), r["status"])
    return seen


# ---------------------------------------------------------------- Phase 1 : enqueue
def phase_enqueue(sb: Supabase, ids: list[str], reason: str, apply: bool) -> int:
    if len(ids) > SAFETY_MAX:
        raise SystemExit(f"Garde-fou : {len(ids)} > {SAFETY_MAX}. Verifie le filtre.")
    seen = delete_job_status(sb, ids)
    todo = [a for a in ids if seen.get(a) not in ("pending", "running", "done")]
    skip = [(a, seen[a]) for a in ids if seen.get(a) in ("pending", "running", "done")]

    print(f"\n[ENQUEUE] {len(ids)} brouillons | a enfiler : {len(todo)} | "
          f"ignores (job existant) : {len(skip)}")
    for a, st in skip:
        print(f"  skip {a} (delete deja {st})")
    if not apply:
        print("\n[DRY-RUN] rien ecrit. Ajoute --apply pour enfiler.")
        return 0
    rows = [{
        "job_type": "delete_hektor_annonce",
        "app_dossier_id": None,
        "hektor_annonce_id": a,
        "payload_json": {
            "hektor_annonce_id": a,
            "app_dossier_id": None,
            "reason": reason,
            "confirm_text": f"SUPPRIMER {a}",
            "delete_scope": "hektor_supabase_local",
        },
        "status": "pending",
        "priority": JOB_PRIORITY,
    } for a in todo]
    created = sb.insert("app_console_job", rows) if rows else []
    print(f"\n{len(created)} jobs enfiles (pending, priority={JOB_PRIORITY}). "
          f"Le worker 'admin' les traite un par un.")
    print("Quand tous sont 'done', relance avec --cleanup --apply pour purger l'index brouillon.")
    return 0


# ---------------------------------------------------------------- Phase 2 : cleanup
def phase_cleanup(sb: Supabase, ids: list[str], apply: bool) -> int:
    seen = delete_job_status(sb, ids)
    done = [a for a in ids if seen.get(a) == "done"]
    not_done = [(a, seen.get(a) or "aucun job") for a in ids if seen.get(a) != "done"]

    print(f"\n[CLEANUP] cibles nettoyables (delete=done) : {len(done)} / {len(ids)}")
    for a, st in not_done:
        print(f"  differe {a} (delete={st}) -> pas encore nettoye")
    if not done:
        print("Aucune suppression confirmee. Rien a nettoyer pour l'instant.")
        return 0

    # Etat AVANT (comptes)
    sup_idx = len(sb.get("app_brouillon_annonce_index_current",
                         urllib.parse.urlencode({"select": "hektor_annonce_id",
                                                 "hektor_annonce_id": f"in.({','.join(done)})"})))
    with sqlite3.connect(HEKTOR_DB) as con:
        ph = ",".join("?" * len(done))
        loc = con.execute(
            f"SELECT count(*) FROM hektor_annonce_draft_state "
            f"WHERE CAST(hektor_annonce_id AS TEXT) IN ({ph})", done).fetchone()[0]
    print(f"  Supabase app_brouillon_annonce_index_current : {sup_idx} lignes")
    print(f"  Local  hektor_annonce_draft_state            : {loc} lignes")

    if not apply:
        print("\n[DRY-RUN] rien supprime. Ajoute --apply pour nettoyer.")
        return 0

    d1 = sb.delete_in("app_brouillon_annonce_index_current", "hektor_annonce_id", done)
    d2 = sb.delete_in("app_brouillon_annonce_detail_cache", "hektor_annonce_id", done)
    with sqlite3.connect(HEKTOR_DB) as con:
        ph = ",".join("?" * len(done))
        cur = con.execute(
            f"DELETE FROM hektor_annonce_draft_state "
            f"WHERE CAST(hektor_annonce_id AS TEXT) IN ({ph})", done)
        con.commit()
        local_deleted = cur.rowcount
    print(f"\nNettoye : index Supabase {len(d1)} | detail cache {len(d2)} | "
          f"draft_state local {local_deleted}.")
    print("Les brouillons ne reviendront pas au prochain push.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nego-id", default="23", help="idnego (defaut 23 = V.-L. GONZALEZ Firminy)")
    ap.add_argument("--ids", default="", help="liste explicite d'ids (sinon tous les brouillons du nego)")
    ap.add_argument("--reason", default=REASON)
    ap.add_argument("--cleanup", action="store_true", help="phase 2 (purge index brouillon + draft_state)")
    ap.add_argument("--apply", action="store_true", help="ecrit reellement (sinon dry-run)")
    args = ap.parse_args()

    load_env()
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis (.env)")
    sb = Supabase(url, key)

    ids = resolve_ids(sb, args)
    if not ids:
        print("Aucun id. Rien a faire.")
        return 0

    if args.cleanup:
        return phase_cleanup(sb, ids, args.apply)
    return phase_enqueue(sb, ids, args.reason, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
