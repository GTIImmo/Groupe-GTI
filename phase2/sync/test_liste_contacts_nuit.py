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

# ════════════════════════════ LE MODE REEL (03/11, §48) ════════════════════════════
import sync_raw  # noqa: E402  (le panier du run vit dans sync_raw)


class FauxHektorComplet(FauxHektor):
    """La liste ET les fiches (ContactById)."""

    def __init__(self, contacts, refus_page=None, refus_fiche=None, introuvables=(), illisibles=()):
        super().__init__(contacts, refus_page)
        self.refus_fiche = refus_fiche
        self.introuvables = set(introuvables)
        self.illisibles = set(illisibles)
        self.fiches_servies: list[str] = []

    def get_json(self, path, params=None):
        if "ContactById" not in path:
            return super().get_json(path, params)
        cid = str(params["id"])
        self.fiches_servies.append(cid)
        if cid == self.refus_fiche:
            raise HektorNonRetryableError("403 Client Error: Forbidden")
        if cid in self.introuvables:
            raise HektorNonRetryableError("404 Client Error: Not Found")
        if cid in self.illisibles:
            return {"data": {}}
        return {"data": {"contact": {"id": cid, "nom": "X"}}}


def carnet_du_run(conn) -> list:
    return conn.execute("SELECT hektor_contact_id, listing_variant, date_maj, last_seen_at"
                        " FROM sync_contact_state ORDER BY 1").fetchall()


print("7. mode reel : les pages vont AU VRAI ENDROIT, le carnet du run reste intact")
conn = base_neuve()
conn.execute("INSERT INTO sync_contact_state(hektor_contact_id, listing_variant, date_maj, last_seen_at)"
             " VALUES ('7', 'active', '2026-01-01 00:00:00', '2026-05-26T00:00:00Z')")
conn.execute("INSERT INTO sync_meta(key, value, updated_at) VALUES ('contact_cursor_active', 'x', 'y')")
conn.execute("INSERT INTO raw_api_response(endpoint_name, object_type, object_id_key, page, page_key, payload_json,"
             " http_status, fetched_at) VALUES ('list_contacts_active_update', 'contact_active', '', 1, 1, '{}', 200,"
             " '2026-11-03T03:51:30Z')")
conn.commit()
carnet_avant = carnet_du_run(conn)
curseur_avant = conn.execute("SELECT value, updated_at FROM sync_meta WHERE key='contact_cursor_active'").fetchone()[:]
bilan, _ = lire(conn, FauxHektorComplet([contact(i) for i in range(1, 46)]), reel=True)
pages = conn.execute("SELECT endpoint_name, object_type, page_key, params_json FROM raw_api_response"
                     " WHERE endpoint_name LIKE '%liste_contacts%' OR endpoint_name='list_contacts_active'"
                     " ORDER BY page_key").fetchall()
verifier("3 pages sous list_contacts_active / contact_active, aucune sous nuit_",
         [(p[0], p[1], p[2]) for p in pages] == [("list_contacts_active", "contact_active", k) for k in (1, 2, 3)],
         str([tuple(p[:3]) for p in pages]))
verifier("parametres identiques a la relecture du 23/06 (sort=id, way=ASC)",
         json.loads(pages[0][3]) == {"archive": 0, "sort": "id", "way": "ASC", "page": 1, "version": "v2"}, pages[0][3])
verifier("tour marque REEL", int(m.lire_tour(conn, "active")["reel"]) == 1)
verifier("TEMOIN : carnet du run inchange (date_maj, variante, last_seen_at)", carnet_du_run(conn) == carnet_avant)
verifier("TEMOIN : curseur inchange",
         conn.execute("SELECT value, updated_at FROM sync_meta WHERE key='contact_cursor_active'").fetchone()[:] == curseur_avant)
verifier("TEMOIN : pages _update du run inchangees",
         conn.execute("SELECT fetched_at FROM raw_api_response WHERE endpoint_name='list_contacts_active_update'"
                      ).fetchone()[0] == "2026-11-03T03:51:30Z")

print("8. changer de mode repart d'un tour neuf (la purge exige un tour 100 % reel)")
conn = base_neuve()
lire(conn, FauxHektorComplet([contact(i) for i in range(1, 61)]), max_pages=1)          # a blanc, page 1
bilan, _ = lire(conn, FauxHektorComplet([contact(i) for i in range(1, 61)]), reel=True)  # passe en reel
tour = m.lire_tour(conn, "active")
verifier("le tour reel repart de la page 1 et lit tout", (bilan["pages"], int(tour["reel"])) == (3, 1), str(bilan))

print("9. les fiches : relues au frein, au panier, sans toucher au carnet du run")
conn = base_neuve()
contacts = [contact(1, datemaj="2026-11-02 23:47:29"), contact(2, datemaj="2026-10-20 10:00:00"),
            contact(3, datemaj="2026-05-01 10:00:00"), contact(4, datemaj="2026-11-01 09:00:00"),
            contact(5, datemaj="2026-10-30 08:00:00")]
for cid in ("1", "2", "3"):
    conn.execute("INSERT INTO sync_contact_state(hektor_contact_id, listing_variant, date_maj, last_detail_sync_at,"
                 " last_seen_at) VALUES (?, 'active', '2025-12-22 10:00:00', '2026-05-26T18:07:04Z', 'x')", (cid,))
conn.commit()
lire(conn, FauxHektorComplet(contacts), reel=True)
ordre = m.fiches_a_relire(conn, "active")
verifier("4 fiches a relire, les plus recemment modifiees d'abord (3 est a jour)",
         ordre == ["1", "4", "5", "2"], str(ordre))
carnet_avant = carnet_du_run(conn)
faux = FauxHektorComplet(contacts)
pauses: list = []
bilan_f = m.relire_les_fiches(conn, faux, "v2", ordre, heure_limite=None, dormir=pauses.append)
verifier("4 fiches relues, 4 requetes, une pause apres chacune",
         (bilan_f["relues"], faux.fiches_servies, len(pauses)) == (4, ordre, 4), str(bilan_f))
verifier("reponse brute sous contact_detail",
         conn.execute("SELECT COUNT(*) FROM raw_api_response WHERE endpoint_name='contact_detail'").fetchone()[0] == 4)
relus = dict(conn.execute("SELECT hektor_contact_id, last_detail_sync_at FROM sync_contact_state"))
verifier("last_detail_sync_at avance pour 1 et 2, pas pour 3 (non relue)",
         relus["1"] > "2026-11" and relus["2"] > "2026-11" and relus["3"] == "2026-05-26T18:07:04Z", str(relus))
verifier("TEMOIN : date_maj, variante et last_seen_at du run INCHANGES", carnet_du_run(conn) == carnet_avant)
verifier("4 et 5 (absentes du carnet du run) n'y sont PAS creees",
         conn.execute("SELECT COUNT(*) FROM sync_contact_state WHERE hektor_contact_id IN ('4','5')").fetchone()[0] == 0)
verifier("les 4 au panier du run (relu_le pose, remis vide)",
         conn.execute("SELECT COUNT(*) FROM liste_nuit_contact WHERE relu_le IS NOT NULL AND remis_au_run_le IS NULL"
                      ).fetchone()[0] == 4)
verifier("la nuit suivante, plus rien a relire (y compris 4 et 5, grace a relu_le)",
         m.fiches_a_relire(conn, "active") == [], str(m.fiches_a_relire(conn, "active")))

print("10. fiches : 404 mise de cote, illisible mise de cote, 403 = arret net, heure limite")
conn = base_neuve()
contacts = [contact(i, datemaj=f"2026-10-0{i} 10:00:00") for i in range(1, 7)]
lire(conn, FauxHektorComplet(contacts), reel=True)
ordre = m.fiches_a_relire(conn, "active")          # 6,5,4,3,2,1
faux = FauxHektorComplet(contacts, introuvables={"6"}, illisibles={"5"}, refus_fiche="3")
bilan_f: dict = {}
try:
    m.relire_les_fiches(conn, faux, "v2", ordre, heure_limite=None, dormir=lambda s: None, bilan=bilan_f)
    verifier("le 403 remonte", False)
except HektorNonRetryableError:
    verifier("le 403 remonte", True)
verifier("aucune fiche demandee apres le refus", faux.fiches_servies == ["6", "5", "4", "3"], str(faux.fiches_servies))
verifier("comptes gardes jusqu'a l'arret (1 relue, 1 404, 1 illisible)",
         (bilan_f["relues"], bilan_f["introuvables_404"], bilan_f["illisibles"]) == (1, 1, 1), str(bilan_f))
reste = m.fiches_a_relire(conn, "active")
verifier("la nuit suivante : 6 et 5 ecartees, 4 relue, il reste 3, 2, 1", reste == ["3", "2", "1"], str(reste))
verifier("le rapport compte les 2 ecartees", m.rapport(conn, "active")["fiches_ecartees_404_ou_illisibles"] == 2)
vraie_heure = m.heure_depassee
appels = {"n": 0}


def limite_au_2e_appel(limite, maintenant=None):
    appels["n"] += 1
    return appels["n"] > 2


m.heure_depassee = limite_au_2e_appel
try:
    faux = FauxHektorComplet(contacts)
    bilan_f = m.relire_les_fiches(conn, faux, "v2", reste, heure_limite="01:58", dormir=lambda s: None)
finally:
    m.heure_depassee = vraie_heure
verifier("heure limite : 2 fiches puis arret propre", (bilan_f["relues"], bilan_f["fin"]) == (2, "heure_limite"),
         str(bilan_f))

print("11. le panier du run (sync_raw) : annonces en plus, plafond, puis « remis »")
conn = base_neuve()
verifier("table absente -> panier vide", sync_raw.load_panier_contacts_nuit(conn, set(), 600) == ([], []))
lire(conn, FauxHektorComplet([contact(i) for i in range(1, 5)]), reel=True)
for a, cid in (("100", "1"), ("101", "1"), ("102", "2"), ("103", "3"), ("104", "3"), ("105", "3"), ("106", "4")):
    conn.execute("INSERT INTO sync_annonce_contact_link(hektor_annonce_id, hektor_contact_id, role_contact, last_seen_at)"
                 " VALUES (?, ?, 'proprietaire', 'x')", (a, cid))
for cid, quand in (("1", "2026-11-04T00:41:00Z"), ("2", "2026-11-04T00:42:00Z"), ("3", "2026-11-04T00:43:00Z"),
                   ("4", "2026-11-04T00:44:00Z")):
    conn.execute("UPDATE liste_nuit_contact SET relu_le = ? WHERE hektor_contact_id = ?", (quand, cid))
conn.commit()
remis, ajoutes = sync_raw.load_panier_contacts_nuit(conn, {"101"}, 3)
verifier("plafond 3 : contacts 1 et 2 remis (100, 102 ; 101 deja prevue), le 3 attend (3 annonces de plus)",
         (remis, ajoutes) == (["1", "2"], ["100", "102"]), str((remis, ajoutes)))
sync_raw.marquer_panier_remis(conn, remis)
remis2, ajoutes2 = sync_raw.load_panier_contacts_nuit(conn, set(), 600)
verifier("nuit suivante : 3 et 4 seulement", (remis2, ajoutes2) == (["3", "4"], ["103", "104", "105", "106"]),
         str((remis2, ajoutes2)))
conn.execute("UPDATE liste_nuit_contact SET relu_le = '2026-11-05T00:41:00Z', remis_au_run_le = NULL"
             " WHERE hektor_contact_id = '1'")
conn.commit()
verifier("une fiche relue de nouveau revient au panier",
         sync_raw.load_panier_contacts_nuit(conn, set(), 600)[0] == ["3", "4", "1"])

print("12. la purge des pages perimees : refusee sans tour reel complet, puis seulement au-dela de N")
conn = base_neuve()
for p in range(1, 8):   # les vieilles pages : 1..5 du 23/06, 6..7 de mars
    conn.execute("INSERT INTO raw_api_response(endpoint_name, object_type, object_id_key, page, page_key, payload_json,"
                 " http_status, fetched_at) VALUES ('list_contacts_active', 'contact_active', '', ?, ?, '{}', 200, ?)",
                 (p, p, "2026-06-23T16:00:00Z" if p <= 5 else "2026-03-30T10:00:00Z"))
conn.commit()
verifier("refus : aucun tour reel", "refus" in m.pages_perimees(conn, "active"))
lire(conn, FauxHektorComplet([contact(i) for i in range(1, 61)]))   # a blanc complet
verifier("refus : tour termine mais A BLANC", "refus" in m.pages_perimees(conn, "active"))
lire(conn, FauxHektorComplet([contact(i) for i in range(1, 61)]), reel=True, max_pages=2)
verifier("refus : tour reel pas termine", "refus" in m.pages_perimees(conn, "active"))
lire(conn, FauxHektorComplet([contact(i) for i in range(1, 61)]), reel=True)
etat = m.pages_perimees(conn, "active")
verifier("accepte : 3 pages fraiches, 4 au-dela (4..7)",
         (etat.get("derniere_page_du_tour"), etat.get("pages_au_dela"), etat.get("de_la_page")) == (3, 4, 4), str(etat))
verifier("a blanc par defaut : rien n'est efface",
         m.purger_pages_perimees(conn, "active", False) == 0
         and conn.execute("SELECT COUNT(*) FROM raw_api_response WHERE endpoint_name='list_contacts_active'"
                          ).fetchone()[0] == 7)
m.purger_pages_perimees(conn, "active", True)
restent = [r[0] for r in conn.execute("SELECT page_key FROM raw_api_response WHERE endpoint_name='list_contacts_active'"
                                      " ORDER BY 1")]
verifier("--confirmer : il reste les pages 1..3 du tour", restent == [1, 2, 3], str(restent))

print("13. la garde « worker vide » et l'horloge des declencheurs")
lus = iter([None, 1, 0])
dodos: list = []
verifier("illisible puis occupee puis vide -> part apres 2 attentes",
         m.attendre_file_vide(None, lire=lambda: next(lus), dormir=dodos.append) is True and len(dodos) == 2)
m.heure_depassee = lambda limite, maintenant=None: True
try:
    verifier("toujours occupee et heure limite passee -> ne part pas",
             m.attendre_file_vide("01:55", lire=lambda: 1, dormir=lambda s: None) is False)
    verifier("illisible n'est JAMAIS « vide »",
             m.attendre_file_vide("01:55", lire=lambda: None, dormir=lambda s: None) is False)
finally:
    m.heure_depassee = vraie_heure
from datetime import datetime as _dt, timezone as _tz  # noqa: E402
ecart = (m.heure_des_declencheurs() - _dt.now(_tz.utc).replace(tzinfo=None)).total_seconds()
verifier("horloge des declencheurs = UTC+1 fixe", abs(ecart - 3600) < 5, str(ecart))

print()
print("TOUT VERT" if not ECHECS else f"{len(ECHECS)} ECHEC(S) : {ECHECS}")
raise SystemExit(1 if ECHECS else 0)
