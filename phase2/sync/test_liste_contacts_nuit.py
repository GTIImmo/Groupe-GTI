"""Essai hors ligne de liste_contacts_nuit.py (couples §45, 03/11/2026).

Un FAUX Hektor sert une liste triee par numero, 20 par page, comme ListContacts.
On rejoue : un tour complet ; un arret au plafond puis une reprise apres des
DEPARTS sous la position (le cas qui fait sauter des contacts quand on reprend « a
la page N ») ; un refus 403 (arret net, reprise gardee) ; le rapport ; et surtout
le TEMOIN que rien n'est ecrit dans le carnet du run ni dans les pages relues par
la normalisation. Une derniere passe rejoue de VRAIES pages du 23/06 (lecture seule).

    python -I phase2/sync/test_liste_contacts_nuit.py
    sortie 0 = tout vert · 1 = un controle en echec
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "phase2" / "sync"))

from hektor_pipeline.common import HektorNonRetryableError, connect_db, init_db  # noqa: E402
import liste_contacts_nuit as m  # noqa: E402

ECHECS: list[str] = []


def verifier(nom: str, condition: bool, detail: str = "") -> None:
    print(("  ok  " if condition else "  KO  ") + nom + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        ECHECS.append(nom)


class FauxHektor:
    def __init__(self, contacts: list[dict], refus_page: int | None = None):
        self.contacts = contacts
        self.refus_page = refus_page
        self.pages_servies: list[int] = []

    def get_json(self, path, params=None):
        page = int(params["page"])
        self.pages_servies.append(page)
        if self.refus_page == page:
            raise HektorNonRetryableError("403 Client Error: Forbidden")
        tries = sorted(self.contacts, key=lambda c: int(c["id"]))
        data = tries[(page - 1) * 20: page * 20]
        nb_pages = (len(tries) + 19) // 20
        return {"data": data, "metadata": {"total": len(tries), "perPage": 20, "currentPage": page,
                                           "nextPage": page + 1 if page < nb_pages else None}}


def contact(i: int, datemaj="2026-11-02 10:00:00", nego="5", couple=None) -> dict:
    return {"id": str(i), "datemaj": datemaj, "refCouple": couple, "id_negociateur": nego, "archive": "0"}


def base_neuve() -> sqlite3.Connection:
    dossier = Path(tempfile.mkdtemp(prefix="liste_nuit_"))
    conn = connect_db(dossier / "essai.sqlite")
    init_db(conn)  # raw_api_response, sync_meta, sync_contact_state… (schema du projet)
    m.creer_tables(conn)
    for t, cols in (("hektor_contact", "hektor_contact_id TEXT PRIMARY KEY, hektor_negociateur_id TEXT,"
                                       " hektor_couple_contact_id TEXT, archive TEXT"),
                    ("sync_annonce_contact_link", "hektor_annonce_id TEXT, hektor_contact_id TEXT")):
        conn.execute(f"CREATE TABLE IF NOT EXISTS {t} ({cols})")
    conn.commit()
    return conn


def temoins(conn) -> tuple:
    return (
        conn.execute("SELECT COUNT(*), COALESCE(MAX(last_seen_at), '') FROM sync_contact_state").fetchone()[:],
        conn.execute("SELECT COUNT(*) FROM sync_meta WHERE key LIKE 'contact_cursor%'").fetchone()[0],
        conn.execute("SELECT COUNT(*) FROM raw_api_response WHERE endpoint_name LIKE 'list_contacts%'").fetchone()[0],
    )


def lire(conn, faux, **kw):
    lecteur = m.Lecteur(faux, "active", "v2")
    opts = dict(scope="active", nouveau_tour=False, heure_limite=None, max_pages=0,
                pause_toutes=0, pause_secondes=0, dormir=lambda s: None)
    opts.update(kw)
    return m.lire_la_liste(conn, lecteur, **opts), lecteur


print("1. un tour complet (95 contacts, 5 pages)")
conn = base_neuve()
conn.execute("INSERT INTO sync_contact_state(hektor_contact_id, listing_variant, date_maj, last_seen_at)"
             " VALUES ('7', 'active', '2026-01-01 00:00:00', '2026-05-26T00:00:00Z')")
conn.execute("INSERT INTO sync_meta(key, value, updated_at) VALUES ('contact_cursor_active', 'x', 'y')")
conn.commit()
avant = temoins(conn)
bilan, lecteur = lire(conn, FauxHektor([contact(i) for i in range(1, 96)]))
verifier("fin = tour_termine", bilan["fin"] == "tour_termine", bilan["fin"])
verifier("5 pages, 95 contacts", (bilan["pages"], bilan["contacts"]) == (5, 95), str(bilan))
verifier("5 requetes", lecteur.requetes == 5, str(lecteur.requetes))
verifier("95 contacts au carnet de la nuit",
         conn.execute("SELECT COUNT(*) FROM liste_nuit_contact").fetchone()[0] == 95)
verifier("pages rangees a part (nuit_liste_contacts_active)",
         conn.execute("SELECT COUNT(*) FROM raw_api_response WHERE endpoint_name='nuit_liste_contacts_active'").fetchone()[0] == 5)
verifier("TEMOIN : carnet du run, curseur et pages list_contacts INTACTS", temoins(conn) == avant,
         f"{avant} -> {temoins(conn)}")
verifier("le tour est marque termine", bool(m.lire_tour(conn, "active")["termine_le"]))

print("2. plafond puis reprise apres des DEPARTS sous la position")
conn = base_neuve()
liste = [contact(i) for i in range(1, 121)]
bilan, _ = lire(conn, FauxHektor(liste), max_pages=2)
tour = m.lire_tour(conn, "active")
verifier("arret au plafond, page 2, dernier numero 40",
         (bilan["fin"], tour["derniere_page"], tour["dernier_id"]) == ("max_pages", 2, 40), str(dict(tour)))
# 25 contacts de numero < 40 quittent la liste active : tout recule de plus d'une page.
liste_apres = [c for c in liste if not (5 <= int(c["id"]) < 30)]
faux = FauxHektor(liste_apres)
bilan, _ = lire(conn, faux)
verifier("recul d'une page pour retrouver le numero 40", bilan["recul"] == 1, str(bilan))
attendus = {c["id"] for c in liste_apres if int(c["id"]) > 40}
vus = {r[0] for r in conn.execute("SELECT hektor_contact_id FROM liste_nuit_contact")}
verifier("AUCUN contact saute apres la reprise", attendus <= vus, f"manquent {sorted(attendus - vus)[:5]}")
verifier("tour termine apres la reprise", bilan["fin"] == "tour_termine", bilan["fin"])
# Une creation (numero plus grand) ne decale rien : un nouveau tour la voit en fin.
bilan, _ = lire(conn, FauxHektor(liste_apres + [contact(500)]))
verifier("nouveau tour apres un tour termine, la creation est vue",
         conn.execute("SELECT COUNT(*) FROM liste_nuit_contact WHERE hektor_contact_id='500'").fetchone()[0] == 1)

print("3. refus 403 : arret net, reprise gardee")
conn = base_neuve()
faux = FauxHektor([contact(i) for i in range(1, 101)], refus_page=3)
try:
    lire(conn, faux)
    verifier("le refus remonte", False)
except HektorNonRetryableError:
    verifier("le refus remonte", True)
tour = m.lire_tour(conn, "active")
verifier("reprise gardee a la page 2 (numero 40)", (tour["derniere_page"], tour["dernier_id"]) == (2, 40), str(dict(tour)))
verifier("aucune page demandee apres le refus", faux.pages_servies == [1, 2, 3], str(faux.pages_servies))

print("4. heure limite")
verifier("00:20 avant 01:55 -> pas depassee", not m.heure_depassee("01:55", datetime(2026, 11, 4, 0, 20)))
verifier("01:56 -> depassee", m.heure_depassee("01:55", datetime(2026, 11, 4, 1, 56)))
verifier("23:10 la veille -> pas depassee", not m.heure_depassee("01:55", datetime(2026, 11, 3, 23, 10)))
verifier("refus sous 300 ms", m.main(["--intervalle-ms", "200", "--rapport-seul"]) == 2)

print("5. le rapport (aucun appel, aucune ecriture)")
conn = base_neuve()
contacts = [
    contact(1, datemaj="2026-11-02 23:47:29", nego="2", couple="1"),   # modifie apres sa relecture
    contact(2, datemaj="2026-05-01 10:00:00", nego="5"),               # rien a relire
    contact(3, datemaj="0000-00-00 00:00:00"),                         # date inconnue
    contact(4),                                                        # jamais relu
    contact(5),                                                        # absent du miroir
]
for cid, relu in (("1", "2026-05-26T18:07:04Z"), ("2", "2026-05-26T18:07:04Z"), ("3", "2026-05-26T18:07:04Z")):
    conn.execute("INSERT INTO sync_contact_state(hektor_contact_id, listing_variant, last_detail_sync_at, last_seen_at)"
                 " VALUES (?, 'active', ?, 'x')", (cid, relu))
for cid, nego, couple in (("1", None, None), ("2", "5", None), ("3", "5", None), ("4", "5", None)):
    conn.execute("INSERT INTO hektor_contact(hektor_contact_id, hektor_negociateur_id, hektor_couple_contact_id, archive,"
                 " raw_json, synced_at) VALUES (?, ?, ?, '0', '{}', 'x')", (cid, nego, couple))
conn.execute("INSERT INTO sync_annonce_contact_link(hektor_annonce_id, hektor_contact_id, role_contact, last_seen_at)"
             " VALUES ('59545', '1', 'proprietaire', 'x')")
conn.commit()
lire(conn, FauxHektor(contacts))
r = m.rapport(conn, "active")
verifier("3 fiches a relire (la modifiee + 2 jamais relues, dont l'absente du miroir)",
         r["fiches_a_relire"] == 3 and r["dont_jamais_lues"] == 2, str((r["fiches_a_relire"], r["dont_jamais_lues"])))
verifier("1 date 0000", r["date_inconnue_0000"] == 1)
verifier("1 annonce liee", r["annonces_liees_aux_fiches_a_relire_au_plus"] == 1)
verifier("1 absent du miroir", r["absents_du_miroir"] == 1)
verifier("negociateur : vide -> 2 sur 1 contact",
         r["negociateur_change_principaux"] == [{"miroir": "(vide)", "liste": "2", "contacts": 1}],
         json.dumps(r["negociateur_change_principaux"]))
verifier("lien de couple different sur 1 contact", r["lien_de_couple_different"] == 1)

print("6. de VRAIES pages du 23/06 (lecture seule de data/hektor.sqlite)")
vraie = sqlite3.connect(f"file:{ROOT / 'data' / 'hektor.sqlite'}?mode=ro", uri=True)
pages = {p: json.loads(pl) for p, pl in vraie.execute(
    "SELECT page, payload_json FROM raw_api_response WHERE endpoint_name='list_contacts_active'"
    " AND fetched_at LIKE '2026-06-23%' AND page <= 3")}
vraie.close()


class VraiesPages:
    def get_json(self, path, params=None):
        p = dict(pages[int(params["page"])])
        meta = dict(p.get("metadata") or {})
        meta["nextPage"] = int(params["page"]) + 1 if int(params["page"]) < 3 else None
        p["metadata"] = meta
        return p


conn = base_neuve()
bilan, _ = lire(conn, VraiesPages())
verifier("3 vraies pages, 60 contacts, ordre respecte",
         (bilan["pages"], bilan["contacts"], bilan["inversions"]) == (3, 60, 0), str(bilan))
ligne = conn.execute("SELECT datemaj, archive FROM liste_nuit_contact LIMIT 1").fetchone()
verifier("datemaj et archive lus sur une vraie ligne", bool(ligne[0]) and ligne[1] == "0", str(tuple(ligne)))

print()
print("TOUT VERT" if not ECHECS else f"{len(ECHECS)} ECHEC(S) : {ECHECS}")
raise SystemExit(1 if ECHECS else 0)
