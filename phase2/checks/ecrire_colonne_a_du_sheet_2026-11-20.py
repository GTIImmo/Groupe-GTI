#!/usr/bin/env python
"""L'ECRIVAIN NEUF DE LA COLONNE A DU SHEET (affair_uuid) -- chantier classeur, ⑬, 20/11/2026.

⛔⛔ DORMANT. A BLANC PAR DEFAUT. Il n'ecrit dans le Sheet QUE si ses TROIS verrous sont ouverts
   ENSEMBLE (methode du § 8.3, validee) :
     1. l'interrupteur APP_SHEET_ECRIRE_AFFAIR_UUID=1, donne A LA COMMANDE -- jamais lu dans .env
        (s'il y est, l'outil REFUSE : un interrupteur d'ecriture ne doit pas rester arme) ;
     2. un FICHIER DE VAGUE, et son empreinte SHA-256 recopiee a la commande (le fichier ecrit est
        celui qui a ete lu et accorde, a l'octet) ;
     3. l'EMPREINTE D'AVANT de la colonne A (donnee par l'a blanc), qui doit CONCORDER au moment
        d'ecrire : si quoi que ce soit a bouge dans la colonne A depuis l'a blanc, il refuse.
   Plus deux gardes : la table app_sheet_ecrit doit exister chez Supabase (la memoire de ce que
   nous ecrivons) ; et l'heure doit etre hors de la nuit (03:30-09:30 : run, pose, descente).

CE QU'IL FAIT, ET RIEN D'AUTRE (§ 8.3) :
  . UNE SEULE COLONNE : A (« affair_uuid »). En RAW, jamais une formule.
  . L'ADRESSE PAR L'ID UNIQUE (colonne AL), relu juste avant CHAQUE paquet de 100 -- jamais par le
    numero de ligne. AL absent, en double, ou A deja remplie -> la ligne est SAUTEE et NOMMEE.
  . L'ETIQUETTE LUE CHEZ SUPABASE AU MOMENT D'ECRIRE (pas dans le CSV de la mesure), exigee
    IDENTIQUE sur toutes les transactions de la ligne (regle C5 decidee le 19/11 : une creation du
    Sheet ne decide jamais -- on prend celles de Hektor), et egale a celle du fichier de vague.
  . Rejoue, a l'instant, ce qui peut avoir bouge depuis la mesure : les liens du gel, leur confiance,
    le dossier qui ne porte AUCUNE autre ligne, l'UUID absent du reste de la colonne A, la liste de
    la decision B (20/11 : 9 lignes en vague 2, apres G2), la memoire app_sheet_ecrit.
  . Apres chaque paquet : RELIT A et AL, et exige chaque UUID sur la ligne de SON ID Unique. Une
    seule case mal posee -> ARRET IMMEDIAT (code 4), le retour arriere sait la retrouver.
  . SAUVEGARDE DATEE avant d'ecrire, dans C:\\Hektor\\Backups\\classeur_colonne_a\\ : tout le Sheet
    (A1:AL), A et AL par ligne, l'empreinte B..AL par ID Unique, la vague.
  . LE RETOUR ARRIERE ne juge que SA part (lecon 31) : il ne vide une case que si elle porte encore
    NOTRE valeur ; une autre valeur est nommee et laissee. Il retrouve aussi une case mal posee
    (notre valeur sur une ligne dont la sauvegarde prouve que A etait vide).

USAGE -- une etape par appel, `python -u` :
  preparer --nom vague0 --ids ID1,ID2,ID3      fabrique notice/CLASSEUR_VAGUE_<nom>_<date>.csv (lecture seule)
  preparer --nom vague1a --premieres 50        (ou --toutes) dans la case VAGUE_1 du fichier de classement
  a_blanc  --vague <fichier>                   le bon d'ecriture : ce qui serait ecrit, saute, et pourquoi,
                                               + les deux empreintes a recopier (lecture seule)
  ecrire   --vague <fichier> --empreinte-vague X --empreinte-colonne-a Y
           avec  APP_SHEET_ECRIRE_AFFAIR_UUID=1  dans l'environnement DE LA COMMANDE
  defaire  --nom vague0                         a blanc sans l'interrupteur ; avec lui ET
           --empreinte-colonne-a Y              vide nos cases (celles qui portent encore notre valeur)
  simuler                                      l'epreuve complete sur une COPIE EN MEMOIRE du Sheet,
                                               temoins inverses semes -- aucun POST, aucune ecriture

CODES : 0 vert . 1 un rouge . 2 pas pu lire (jamais un vert) . 3 un verrou refuse . 4 arret en cours d'ecriture
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

INTERRUPTEUR = "APP_SHEET_ECRIRE_AFFAIR_UUID"
#: ⛔ lu AVANT le chargement de .env : l'interrupteur se donne a la commande, une fois.
INTERRUPTEUR_A_LA_COMMANDE = os.environ.get(INTERRUPTEUR)

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
from check_google_scopes import load_env_file  # noqa: E402

SHEET_ID = "1wFd3pQYItvOrbk10W0r--bmhOaV1R4tWgZ3dq1XCipk"
ONGLET = "Sheet1"
COLONNE = "affair_uuid"            # le libelle de la colonne A en ligne 1
A, AL, LARGEUR = 0, 37, 38
ENTETE_AL = "ID Unique"
PAQUET = 100
PAGE = 1000                         # le plafond de lecture de Supabase, verifie par un temoin au demarrage
TRANCHE = 50                        # une liste in.(...) ne depasse jamais 50 valeurs
ORIGINE = "ecrire_colonne_a_du_sheet_2026-11-20.py"
FENETRE_INTERDITE = ((3, 30), (9, 30))   # le run (04:00), la pose des etiquettes, la descente (07:45)
DECISION_B = RACINE / "notice" / "TEMPS6_DECISION_B_LIGNES_REPORTEES_EN_VAGUE_2_PAR_G2_2026-11-20.csv"
#: decision du 20/11 (« LES 19 : OUI, sors-les, comme les 9 de B ») -- mesure du § 13.8 (temps7)
DECISION_19 = RACINE / "notice" / "TEMPS7_DECISION_DU_20_11_LES_19_HORS_DE_LA_VAGUE_1_2026-11-20.csv"
CLASSEMENT = RACINE / "notice" / "TEMPS5_Q8_LES_LIGNES_DU_SHEET_ET_LEUR_VAGUE_2026-11-19.csv"
SORTIES = Path(r"C:\Hektor\Backups\classeur_colonne_a")
SORTIES_SIMULATION = Path(r"C:\Hektor\chantier_classeur_q6_cache\ecrivain_colonne_a_simulation")


class LectureRatee(Exception):
    """Une lecture qui echoue n'est JAMAIS un vert : code 2."""


class VerrouRefuse(Exception):
    """Un verrou ferme : code 3."""


# ═══════════════════════════════════════════ petits outils ═══════════════════════════════════════════
def maintenant_local() -> datetime:
    return datetime.now()


def horodatage(t: datetime | None = None) -> str:
    return (t or maintenant_local()).strftime("%Y-%m-%d_%H%M%S")


def sha256_fichier(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tranches(seq, n=TRANCHE):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def propre(x) -> str:
    return str(x if x is not None else "").strip()


def ligne_pleine(l) -> list[str]:
    l = [str(x) if x is not None else "" for x in list(l)]
    return (l + [""] * LARGEUR)[:LARGEUR]


def empreinte_colonne_a(valeurs: list[list[str]]) -> str:
    """L'empreinte de la colonne A, PAR ID UNIQUE (un tri humain ne la change pas) : la liste triee
    des couples (AL, A) de toutes les lignes ou l'un des deux est rempli."""
    couples = sorted([propre(r[AL]), propre(r[A])] for r in valeurs[1:] if propre(r[AL]) or propre(r[A]))
    return hashlib.sha256(json.dumps(couples, ensure_ascii=True).encode("ascii")).hexdigest()


def empreintes_b_al(valeurs: list[list[str]]) -> dict[str, str]:
    """B..AL, ligne par ligne, rangees par ID Unique -- le critere ③ (0 case hors de A modifiee par nous)."""
    out: dict[str, list[str]] = defaultdict(list)
    for r in valeurs[1:]:
        i = propre(r[AL])
        if i:
            out[i].append(hashlib.sha1(json.dumps([propre(x) for x in r[1:LARGEUR]],
                                                  ensure_ascii=True).encode("ascii")).hexdigest())
    return {i: "+".join(sorted(v)) for i, v in out.items()}


def positions(colonne_al: list[str]) -> dict[str, list[int]]:
    """ID Unique -> numeros de ligne (1 = l'en-tete)."""
    pos: dict[str, list[int]] = defaultdict(list)
    for k, x in enumerate(colonne_al):
        if k and propre(x):
            pos[propre(x)].append(k + 1)
    return pos


def a_par_id(valeurs) -> dict[str, str]:
    out = {}
    for r in valeurs[1:]:
        i = propre(r[AL])
        if i:
            out[i] = propre(r[A]) if i not in out else out[i] + " | " + propre(r[A])
    return out


def dans_la_fenetre_interdite(t: datetime) -> bool:
    (h1, m1), (h2, m2) = FENETRE_INTERDITE
    return (h1, m1) <= (t.hour, t.minute) < (h2, m2)


# ═══════════════════════════════════════════ le Sheet ═══════════════════════════════════════════
class SheetReel:
    """Le vrai Sheet. Les lectures sont des GET. ⛔ ecrire() et vider() refusent tant que `arme` est faux,
    et `arme` n'est mis a vrai QUE par le chemin qui a ouvert les trois verrous."""

    def __init__(self) -> None:
        self.arme = False
        self._creds = None
        self.appels = Counter()

    def _jeton(self) -> str:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        if self._creds is None:
            self._creds = service_account.Credentials.from_service_account_file(
                os.environ["GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE"],
                # la meme portee que les lecteurs du chantier (apparier_classeur.py l. 283) : la delegation
                # du domaine n'a pas ete mesuree pour « readonly » (§ ⑨ point 5)
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            ).with_subject(os.environ["GOOGLE_WORKSPACE_SUBJECT_EMAIL"])
        if not self._creds.valid:
            self._creds.refresh(Request())
        return self._creds.token

    def _http(self, methode: str, url: str, **kw):
        import requests
        time.sleep(1.1)                                   # le quota de Google : 60 appels / min / utilisateur
        self.appels[methode] += 1
        rep = requests.request(methode, url, headers={"Authorization": f"Bearer {self._jeton()}"},
                               timeout=180, **kw)
        if rep.status_code >= 400:
            raise LectureRatee(f"Google {rep.status_code} sur {methode} : {rep.text[:300]}")
        return rep.json()

    def lire_tout(self) -> list[list[str]]:
        rng = urllib.parse.quote(f"{ONGLET}!A1:AL")
        v = self._http("GET", f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{rng}").get("values", [])
        if not v:
            raise LectureRatee("le Sheet est vide")
        return [ligne_pleine(l) for l in v]

    def lire_a_al(self) -> tuple[list[str], list[str]]:
        q = urllib.parse.urlencode([("ranges", f"{ONGLET}!A1:A"), ("ranges", f"{ONGLET}!AL1:AL"),
                                    ("majorDimension", "COLUMNS")])
        r = self._http("GET", f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchGet?{q}")
        vr = r.get("valueRanges", [])
        if len(vr) != 2:
            raise LectureRatee("batchGet : %d plages au lieu de 2" % len(vr))
        col_a = [str(x) for x in (vr[0].get("values") or [[]])[0]]
        col_al = [str(x) for x in (vr[1].get("values") or [[]])[0]]
        n = max(len(col_a), len(col_al))
        return col_a + [""] * (n - len(col_a)), col_al + [""] * (n - len(col_al))

    def ecrire(self, cases: list[tuple[int, str]]) -> None:
        if not self.arme:
            raise VerrouRefuse("SheetReel.ecrire appele sans les verrous ouverts")
        corps = {"valueInputOption": "RAW",
                 "data": [{"range": f"{ONGLET}!A{row}", "values": [[val]]} for row, val in cases]}
        self._http("POST", f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchUpdate", json=corps)

    def vider(self, lignes: list[int]) -> None:
        if not self.arme:
            raise VerrouRefuse("SheetReel.vider appele sans les verrous ouverts")
        corps = {"ranges": [f"{ONGLET}!A{row}" for row in lignes]}
        self._http("POST", f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values:batchClear", json=corps)


class SheetMemoire:
    """Une COPIE du Sheet en memoire, pour l'epreuve. `crochet` simule un humain entre la relecture et
    l'ecriture d'un paquet (un tri, une ligne inseree)."""

    def __init__(self, valeurs: list[list[str]]) -> None:
        self.v = [ligne_pleine(l) for l in copy.deepcopy(valeurs)]
        self.crochet = None
        self.arme = True
        self.appels = Counter()

    def lire_tout(self):
        self.appels["GET"] += 1
        return copy.deepcopy(self.v)

    def lire_a_al(self):
        self.appels["GET"] += 1
        return [r[A] for r in self.v], [r[AL] for r in self.v]

    def ecrire(self, cases):
        self.appels["POST"] += 1
        if self.crochet:
            self.crochet(self)
        for row, val in cases:
            self.v[row - 1][A] = val

    def vider(self, lignes):
        self.appels["POST"] += 1
        for row in lignes:
            self.v[row - 1][A] = ""


# ═══════════════════════════════════════════ Supabase ═══════════════════════════════════════════
def client_supabase():
    from push_upgrade_to_supabase import SupabaseRestClient
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and key):
        raise LectureRatee("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY absents")
    return SupabaseRestClient(base_url=url, service_role_key=key)


def liste_in(valeurs, texte: bool) -> str:
    if texte:
        return "in.(%s)" % ",".join('"%s"' % str(v).replace('"', "") for v in valeurs)
    return "in.(%s)" % ",".join(str(int(v)) for v in valeurs)


class Registre:
    """LECTURE SEULE chez Supabase : le registre des transactions et le gel des liens."""

    def __init__(self, client) -> None:
        self.c = client
        self.appels = 0

    def _get(self, table: str, select: str, filtres: dict, ordre: str) -> list[dict]:
        out, offset = [], 0
        while True:
            self.appels += 1
            r = self.c._request(method="GET", path=table, query={  # noqa: SLF001
                "select": select, **filtres, "order": ordre, "limit": str(PAGE), "offset": str(offset)})
            if not isinstance(r, list):
                raise LectureRatee(f"{table} : reponse illisible")
            out += r
            if len(r) < PAGE:
                return out
            offset += PAGE

    def verifier_plafond(self) -> None:
        """TEMOIN POSITIF de la pagination : une page pleine doit revenir PLEINE. Si le serveur coupait
        plus bas que PAGE, une page courte serait prise pour la derniere et on croirait avoir tout lu."""
        r = self.c._request(method="GET", path="app_affaire_ledger", query={  # noqa: SLF001
            "select": "app_affaire_id", "order": "app_affaire_id.asc", "limit": str(PAGE)})
        if not isinstance(r, list) or len(r) != PAGE:
            raise LectureRatee("le plafond de lecture de Supabase n'est pas %d (recu %s)"
                               % (PAGE, len(r) if isinstance(r, list) else r))

    def liens_des_lignes(self, ids) -> dict[str, list[tuple[int, str]]]:
        out: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for t in tranches(sorted(set(ids))):
            for x in self._get("app_classeur_lien", "id_unique,app_affaire_id,confiance",
                               {"id_unique": liste_in(t, True)}, "id_unique.asc,app_affaire_id.asc"):
                out[x["id_unique"]].append((int(x["app_affaire_id"]), x["confiance"]))
        return out

    def liens_des_transactions(self, txs) -> dict[int, set[str]]:
        out: dict[int, set[str]] = defaultdict(set)
        for t in tranches(sorted(set(txs))):
            for x in self._get("app_classeur_lien", "id_unique,app_affaire_id",
                               {"app_affaire_id": liste_in(t, False)}, "app_affaire_id.asc,id_unique.asc"):
                out[int(x["app_affaire_id"])].add(x["id_unique"])
        return out

    def transactions(self, txs) -> dict[int, dict]:
        out = {}
        for t in tranches(sorted(set(txs))):
            for x in self._get("app_affaire_ledger",
                               "app_affaire_id,app_dossier_uuid,transaction_origine,kind,state,hektor_annonce_id",
                               {"app_affaire_id": liste_in(t, False)}, "app_affaire_id.asc"):
                out[int(x["app_affaire_id"])] = {"uuid": x["app_dossier_uuid"], "origine": x["transaction_origine"],
                                                 "genre": x["kind"], "etat": x["state"],
                                                 "bien": x["hektor_annonce_id"]}
        return out

    def transactions_des_dossiers(self, uuids) -> dict[int, dict]:
        out = {}
        for t in tranches(sorted(set(u for u in uuids if u))):
            for x in self._get("app_affaire_ledger", "app_affaire_id,app_dossier_uuid,transaction_origine",
                               {"app_dossier_uuid": liste_in(t, True)}, "app_affaire_id.asc"):
                out[int(x["app_affaire_id"])] = {"uuid": x["app_dossier_uuid"], "origine": x["transaction_origine"]}
        return out


class RegistreSimule:
    """Pour l'epreuve SEULEMENT : le vrai registre, avec des transactions dont on force l'origine (pour
    semer le temoin « C5 seule » sans toucher la base)."""

    def __init__(self, vrai: Registre, origine_forcee: dict[int, str]) -> None:
        self.vrai, self.forcee = vrai, origine_forcee

    def __getattr__(self, nom):
        return getattr(self.vrai, nom)

    def transactions(self, txs):
        out = self.vrai.transactions(txs)
        for a, o in self.forcee.items():
            if a in out:
                out[a] = dict(out[a], origine=o)
        return out

    def transactions_des_dossiers(self, uuids):
        out = self.vrai.transactions_des_dossiers(uuids)
        for a, o in self.forcee.items():
            if a in out:
                out[a] = dict(out[a], origine=o)
        return out


def effectives(txs, info: dict[int, dict]) -> list[int]:
    """La regle C5 « a l'export » (decidee le 19/11) : une creation du Sheet ne decide JAMAIS de
    l'etiquette d'une ligne -- on prend les transactions de Hektor ; s'il n'y en a aucune, toutes."""
    connues = [a for a in txs if a in info]
    hk = [a for a in connues if info[a]["origine"] != "classeur"]
    return hk if hk else connues


# ═══════════════════════════════════════════ la memoire app_sheet_ecrit ═══════════════════════════════════════════
class MemoireSupabase:
    TABLE = "app_sheet_ecrit"

    def __init__(self, client) -> None:
        self.c = client
        self.arme = False

    def existe(self) -> bool:
        try:
            r = self.c._request(method="GET", path=self.TABLE, query={"select": "id_unique", "limit": "1"})  # noqa: SLF001
            return isinstance(r, list)
        except RuntimeError as e:
            if "42P01" in str(e) or "PGRST205" in str(e) or " 404 " in str(e) or "does not exist" in str(e):
                return False
            raise LectureRatee(f"memoire illisible : {e}") from e

    def lire(self, ids=None, vague=None) -> dict[str, dict]:
        filtres = {"colonne": f"eq.{COLONNE}"}
        if vague:
            filtres["vague"] = f"eq.{vague}"
        out = {}
        lots = [None] if ids is None else list(tranches(sorted(set(ids))))
        for t in lots:
            f = dict(filtres)
            if t is not None:
                if not t:
                    continue
                f["id_unique"] = liste_in(t, True)
            off = 0
            while True:
                try:
                    r = self.c._request(method="GET", path=self.TABLE, query={  # noqa: SLF001
                        "select": "*", **f, "order": "id_unique.asc", "limit": str(PAGE), "offset": str(off)})
                except RuntimeError as e:
                    raise LectureRatee(f"memoire illisible : {e}") from e
                if not isinstance(r, list):
                    raise LectureRatee("memoire : reponse illisible")
                for x in r:
                    out[x["id_unique"]] = x
                if len(r) < PAGE:
                    break
                off += PAGE
        return out

    def poser_prevu(self, lignes: list[dict]) -> None:
        if not self.arme:
            raise VerrouRefuse("memoire.poser_prevu sans les verrous ouverts")
        if lignes:
            self.c._request(method="POST", path=self.TABLE, payload=lignes,  # noqa: SLF001
                            prefer="resolution=merge-duplicates,return=minimal",
                            query={"on_conflict": "id_unique,colonne"})

    def marquer(self, ids, etat: str) -> None:
        if not self.arme:
            raise VerrouRefuse("memoire.marquer sans les verrous ouverts")
        corps = {"etat": etat, "defait_le": datetime.now(timezone.utc).isoformat() if etat == "defait" else None}
        for t in tranches(sorted(set(ids))):
            self.c._request(method="PATCH", path=self.TABLE, payload=corps, prefer="return=minimal",  # noqa: SLF001
                            query={"colonne": f"eq.{COLONNE}", "id_unique": liste_in(t, True)})


class MemoireLocale:
    """La meme memoire, dans un dictionnaire : pour l'epreuve."""

    def __init__(self) -> None:
        self.t: dict[str, dict] = {}
        self.arme = True

    def existe(self):
        return True

    def lire(self, ids=None, vague=None):
        return {i: dict(x) for i, x in self.t.items()
                if (ids is None or i in set(ids)) and (vague is None or x["vague"] == vague)}

    def poser_prevu(self, lignes):
        for x in lignes:
            self.t[x["id_unique"]] = dict(x)

    def marquer(self, ids, etat):
        for i in ids:
            self.t[i]["etat"] = etat
            self.t[i]["defait_le"] = datetime.now(timezone.utc).isoformat() if etat == "defait" else None


# ═══════════════════════════════════════════ la vague ═══════════════════════════════════════════
COLONNES_VAGUE = ["id_unique", "nom_vague", "ligne_vue", "etiquette_prevue", "transactions", "admis", "case_source"]


def lire_vague(p: Path) -> tuple[str, list[dict], str]:
    entrees = []
    with p.open(encoding="utf-8-sig", newline="") as f:
        lecteur = csv.DictReader(f, delimiter=";")
        manque = [c for c in COLONNES_VAGUE if c not in (lecteur.fieldnames or [])]
        if manque:
            raise VerrouRefuse(f"fichier de vague illisible : colonnes absentes {manque}")
        for r in lecteur:
            entrees.append({"id_unique": propre(r["id_unique"]), "nom_vague": propre(r["nom_vague"]),
                            "ligne_vue": propre(r["ligne_vue"]), "etiquette_prevue": propre(r["etiquette_prevue"]),
                            "transactions": sorted(int(x) for x in propre(r["transactions"]).split()),
                            "admis": propre(r["admis"]).split(), "case_source": propre(r["case_source"])})
    noms = {e["nom_vague"] for e in entrees}
    if len(noms) != 1 or not next(iter(noms)):
        raise VerrouRefuse(f"fichier de vague : un seul nom de vague attendu, trouve {sorted(noms)}")
    ids = Counter(e["id_unique"] for e in entrees)
    if any(n > 1 for n in ids.values()) or "" in ids:
        raise VerrouRefuse("fichier de vague : un ID Unique vide ou en double")
    return next(iter(noms)), entrees, sha256_fichier(p)


def lire_decision_b() -> set[str]:
    with DECISION_B.open(encoding="utf-8-sig", newline="") as f:
        ids = {propre(r["id_unique"]) for r in csv.DictReader(f, delimiter=";")}
    if len(ids) != 9:
        raise LectureRatee(f"decision B : {len(ids)} lignes lues, 9 attendues (decision du 20/11)")
    return ids


def lire_hors_vague() -> dict[str, tuple[str, str]]:
    """Les lignes que Frederic a SORTIES de la vague 1, et pourquoi : {ID Unique: (raison, detail)}.
    Les 9 de B (vague 2, apres G2) et les 19 du 20/11 (une reparation que le Sheet designe les attend)."""
    hors = {i: ("DECISION_B", "decision du 20/11 : vague 2, apres G2") for i in lire_decision_b()}
    with DECISION_19.open(encoding="utf-8-sig", newline="") as f:
        lus = {propre(r["id_unique"]): propre(r["nature"]) for r in csv.DictReader(f, delimiter=";")}
    if len(lus) != 19:
        raise LectureRatee(f"decision des 19 : {len(lus)} lignes lues, 19 attendues (decision du 20/11)")
    if set(lus) & set(hors):
        raise LectureRatee(f"une ligne est dans B ET dans les 19 : {sorted(set(lus) & set(hors))}")
    for i, nature in lus.items():
        hors[i] = ("DECISION_19", "decision du 20/11 : hors de la vague 1, une reparation l'attend (%s)" % nature)
    return hors


# ═══════════════════════════════════════════ LE JUGE D'UN PAQUET ═══════════════════════════════════════════
def juger_paquet(entrees, col_a, col_al, reg, memo: dict, exclus_b: dict, doubles_vague: set) -> list[dict]:
    """Pour chaque ligne du paquet : A_ECRIRE (avec sa ligne et son etiquette) ou SAUTEE (avec sa raison).
    Tout est relu A L'INSTANT : le Sheet (col_a, col_al), le gel et le registre (Supabase), la memoire."""
    pos = positions(col_al)
    deja: dict[str, list[int]] = defaultdict(list)
    for k, x in enumerate(col_a):
        if k and propre(x):
            deja[propre(x)].append(k + 1)
    ids = [e["id_unique"] for e in entrees]
    liens = reg.liens_des_lignes(ids)
    info = reg.transactions({a for l in liens.values() for a, _ in l})

    decisions, candidats = [], {}
    for e in entrees:
        i = e["id_unique"]
        d = {"id_unique": i, "ligne": None, "etiquette": None, "verdict": "SAUTEE", "raison": "", "detail": ""}
        decisions.append(d)

        def sauter(raison, detail=""):
            d["raison"], d["detail"] = raison, detail
            return d

        if i in exclus_b:
            sauter(*exclus_b[i])
            continue
        if i in doubles_vague:
            sauter("UUID_EN_DOUBLE_DANS_LA_VAGUE", "la meme etiquette prevue sur deux lignes du fichier")
            continue
        rows = pos.get(i, [])
        if not rows:
            sauter("ID_UNIQUE_ABSENT", "AL ne porte plus cet ID Unique")
            continue
        if len(rows) > 1:
            sauter("ID_UNIQUE_EN_DOUBLE", "lignes %s" % rows)
            continue
        row = rows[0]
        d["ligne"] = row
        if propre(col_a[row - 1]):
            sauter("A_DEJA_REMPLIE", "A porte %r -- on n'ecrase jamais" % propre(col_a[row - 1])[:60])
            continue
        l = liens.get(i, [])
        if not l:
            sauter("SANS_LIEN", "le gel ne relie plus cette ligne a aucune transaction")
            continue
        txs = sorted({a for a, _ in l})
        if txs != e["transactions"]:
            sauter("GEL_A_CHANGE", "fichier %s / maintenant %s" % (e["transactions"], txs))
            continue
        pas_sures = sorted({c for _, c in l} - {"sûre"})
        if pas_sures and "lien_non_sur" not in e["admis"]:
            sauter("LIEN_NON_SUR", "confiance %s" % pas_sures)
            continue
        absentes = [a for a in txs if a not in info]
        if absentes:
            sauter("TRANSACTION_ABSENTE_DU_REGISTRE", "%s" % absentes)
            continue
        if all(info[a]["origine"] == "classeur" for a in txs):
            sauter("C5_SEULE", "que des creations du Sheet : aucune ne decide de l'etiquette")
            continue
        eff = effectives(txs, info)
        uuids = sorted({info[a]["uuid"] for a in eff})
        if len(uuids) != 1 or not uuids[0]:
            sauter("PLUSIEURS_DOSSIERS", "etiquettes %s" % uuids)
            continue
        u = uuids[0]
        d["etiquette"] = u
        if u != e["etiquette_prevue"]:
            sauter("ETIQUETTE_A_CHANGE", "prevue %s / maintenant %s" % (e["etiquette_prevue"], u))
            continue
        if deja.get(u):
            sauter("UUID_DEJA_DANS_LE_SHEET", "deja en A, ligne(s) %s" % deja[u])
            continue
        m = memo.get(i)
        if m and m.get("etat") in ("prevu", "ecrit"):
            sauter("MEMOIRE_DIT_%s_MAIS_A_VIDE" % m["etat"].upper(),
                   "notre memoire dit %s (%s, vague %s) et la case est vide : un humain l'a videe, "
                   "ou une ecriture s'est arretee -- a regarder" % (m["etat"], m.get("valeur"), m.get("vague")))
            continue
        candidats[i] = u

    # ── LE DOSSIER NE PORTE AUCUNE AUTRE LIGNE (regle C5 appliquee aux autres lignes aussi) ──
    if candidats:
        dossiers = reg.transactions_des_dossiers(set(candidats.values()))
        liens_tx = reg.liens_des_transactions(dossiers.keys())
        autres = {j for js in liens_tx.values() for j in js}
        liens_autres = reg.liens_des_lignes(autres)
        info_autres = reg.transactions({a for l in liens_autres.values() for a, _ in l})
        lignes_du_dossier: dict[str, set[str]] = defaultdict(set)
        for j, l in liens_autres.items():
            for a in effectives(sorted({a for a, _ in l}), info_autres):
                lignes_du_dossier[info_autres[a]["uuid"]].add(j)
        par_id = {e["id_unique"]: e for e in entrees}
        for d in decisions:
            i = d["id_unique"]
            if i not in candidats:
                continue
            u = candidats[i]
            admises = {t.split(":", 1)[1] for t in par_id[i]["admis"] if t.startswith("autre_ligne:")}
            en_trop = sorted(lignes_du_dossier[u] - {i} - admises)
            if i not in lignes_du_dossier[u]:
                d["raison"], d["detail"] = "LIGNE_HORS_DE_SON_DOSSIER", "le gel ne la relie pas au dossier %s" % u
            elif en_trop:
                d["raison"], d["detail"] = "ETIQUETTE_PARTAGEE", "le dossier porte aussi %s" % en_trop
            else:
                d["verdict"] = "A_ECRIRE"
                if admises:
                    d["detail"] = "autres lignes ADMISES par le fichier de vague : %s" % sorted(admises)
    return decisions


def doubles_dans_la_vague(entrees) -> set[str]:
    c = Counter(e["etiquette_prevue"] for e in entrees if e["etiquette_prevue"])
    return {e["id_unique"] for e in entrees if c[e["etiquette_prevue"]] > 1}


# ═══════════════════════════════════════════ ECRIRE (et l'a blanc) ═══════════════════════════════════════════
def verifier_verrous(*, interrupteur, env_le_definit, sha_vague, sha_donne, emp_a, emp_donnee, quand, memoire) -> None:
    if env_le_definit:
        raise VerrouRefuse(f"{INTERRUPTEUR} est ecrit dans .env : un interrupteur d'ecriture ne reste pas arme. "
                           "Le retirer de .env et le donner a la commande.")
    if interrupteur != "1":
        raise VerrouRefuse(f"verrou 1 : {INTERRUPTEUR}=1 absent de l'environnement de la commande")
    if not sha_donne or len(sha_donne) < 12 or not sha_vague.startswith(sha_donne.lower()):
        raise VerrouRefuse(f"verrou 2 : l'empreinte du fichier de vague ne concorde pas "
                           f"(donnee {sha_donne!r}, fichier {sha_vague[:16]}...)")
    if not emp_donnee or len(emp_donnee) < 12 or not emp_a.startswith(emp_donnee.lower()):
        raise VerrouRefuse(f"verrou 3 : la colonne A a change depuis l'a blanc, ou l'empreinte donnee est fausse "
                           f"(donnee {emp_donnee!r}, maintenant {emp_a[:16]}...)")
    if dans_la_fenetre_interdite(quand):
        raise VerrouRefuse("garde : %s est dans la fenetre de la nuit %02d:%02d-%02d:%02d (run, pose, descente)"
                           % (quand.strftime("%H:%M"), *FENETRE_INTERDITE[0], *FENETRE_INTERDITE[1]))
    if not memoire.existe():
        raise VerrouRefuse("garde : la table app_sheet_ecrit n'existe pas chez Supabase "
                           "(supabase/patch_sheet_ecrit_memoire_colonne_a_2026-11-20.sql, a coller par Frederic)")


def sauvegarder(dossier: Path, valeurs, entrees, meta: dict) -> None:
    dossier.mkdir(parents=True, exist_ok=False)
    (dossier / "sheet_A1_AL_avant.json").write_text(json.dumps(valeurs, ensure_ascii=False), encoding="utf-8")
    with (dossier / "colonne_a_al_avant.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ligne", "id_unique", "A"])
        for k, r in enumerate(valeurs[1:], start=2):
            w.writerow([k, propre(r[AL]), propre(r[A])])
    with (dossier / "empreintes_b_al_avant.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_unique", "empreinte_b_al"])
        for i, h in sorted(empreintes_b_al(valeurs).items()):
            w.writerow([i, h])
    with (dossier / "vague.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(COLONNES_VAGUE)
        for e in entrees:
            w.writerow([e["id_unique"], e["nom_vague"], e["ligne_vue"], e["etiquette_prevue"],
                        " ".join(map(str, e["transactions"])), " ".join(e["admis"]), e["case_source"]])
    (dossier / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def derouler_ecriture(*, mode: str, nom: str, entrees, sha_vague: str, sheet, memoire, reg, sortie: Path,
                      quand: datetime, interrupteur=None, env_le_definit=False, sha_donne=None, emp_donnee=None,
                      journal=print) -> tuple[int, dict]:
    """mode = 'a_blanc' (lecture seule) ou 'ecrire'. Renvoie (code, rapport)."""
    assert mode in ("a_blanc", "ecrire")
    exclus_b = lire_hors_vague()
    valeurs = sheet.lire_tout()
    if propre(valeurs[0][A]) != COLONNE or propre(valeurs[0][AL]) != ENTETE_AL:
        raise LectureRatee("l'en-tete du Sheet a bouge : A=%r AL=%r" % (valeurs[0][A], valeurs[0][AL]))
    emp_a = empreinte_colonne_a(valeurs)
    b_al_avant = empreintes_b_al(valeurs)
    a_avant = a_par_id(valeurs)
    memoire_existe = memoire.existe()
    rapport = {"mode": mode, "vague": nom, "lignes_du_fichier": len(entrees), "sha_vague": sha_vague,
               "empreinte_colonne_a_avant": emp_a, "heure": quand.isoformat(timespec="seconds"),
               "memoire_existe": memoire_existe, "decisions": [], "paquets": [], "arret": None, "criteres": {}}
    journal("vague %s : %d lignes ; fichier %s ; colonne A %s" % (nom, len(entrees), sha_vague[:16], emp_a[:16]))

    if mode == "ecrire":
        verifier_verrous(interrupteur=interrupteur, env_le_definit=env_le_definit, sha_vague=sha_vague,
                         sha_donne=sha_donne, emp_a=emp_a, emp_donnee=emp_donnee, quand=quand, memoire=memoire)
        sheet.arme = True
        memoire.arme = True
        sauvegarder(sortie / "sauvegarde", valeurs, entrees,
                    {"vague": nom, "sha_vague": sha_vague, "empreinte_colonne_a": emp_a,
                     "heure": quand.isoformat(timespec="seconds"), "origine": ORIGINE})
        journal("SAUVEGARDE : %s" % (sortie / "sauvegarde"))

    doubles = doubles_dans_la_vague(entrees)
    ecrites: dict[str, tuple[int, str]] = {}
    for k, paquet in enumerate(tranches(entrees, PAQUET), start=1):
        col_a, col_al = sheet.lire_a_al()
        memo = memoire.lire(ids=[e["id_unique"] for e in paquet]) if memoire_existe else {}
        dec = juger_paquet(paquet, col_a, col_al, reg, memo, exclus_b, doubles)
        rapport["decisions"] += dec
        a_ecrire = [d for d in dec if d["verdict"] == "A_ECRIRE"]
        info_p = {"paquet": k, "lignes": len(paquet), "a_ecrire": len(a_ecrire),
                  "sautees": len(paquet) - len(a_ecrire)}
        rapport["paquets"].append(info_p)
        journal("paquet %d : %d lignes, %d a ecrire, %d sautees" % (k, len(paquet), len(a_ecrire),
                                                                     len(paquet) - len(a_ecrire)))
        if mode == "a_blanc" or not a_ecrire:
            continue
        now = datetime.now(timezone.utc).isoformat()
        memoire.poser_prevu([{"id_unique": d["id_unique"], "colonne": COLONNE, "valeur": d["etiquette"], "avant": "",
                              "etat": "prevu", "vague": nom, "ligne_vue": d["ligne"], "ecrit_le": now,
                              "defait_le": None, "origine": ORIGINE} for d in a_ecrire])
        sheet.ecrire([(d["ligne"], d["etiquette"]) for d in a_ecrire])
        col_a2, col_al2 = sheet.lire_a_al()
        pos2 = positions(col_al2)
        ok, mal = [], []
        for d in a_ecrire:
            i, u = d["id_unique"], d["etiquette"]
            ou = [k2 + 1 for k2, x in enumerate(col_a2) if k2 and propre(x) == u]
            bonnes = [r for r in ou if propre(col_al2[r - 1]) == i]
            if len(ou) == 1 and bonnes and pos2.get(i) == bonnes:
                ok.append(i)
                ecrites[i] = (bonnes[0], u)
            else:
                mal.append({"id_unique": i, "etiquette": u, "trouvee_sur": [(r, propre(col_al2[r - 1])) for r in ou]})
        if ok:
            memoire.marquer(ok, "ecrit")
        info_p["ecrites_verifiees"] = len(ok)
        if mal:
            rapport["arret"] = {"paquet": k, "mal_posees": mal}
            journal("⛔ ARRET : %d case(s) MAL POSEE(S) ou non retrouvee(s) au paquet %d : %s"
                    % (len(mal), k, mal[:5]))
            break

    # ── LES CRITERES DU § 8.5 ──
    sautees = [d for d in rapport["decisions"] if d["verdict"] == "SAUTEE"]
    rapport["compte_raisons"] = dict(Counter(d["raison"] for d in sautees))
    prevues = [d for d in rapport["decisions"] if d["verdict"] == "A_ECRIRE"]
    rapport["a_ecrire"] = len(prevues)
    if mode == "a_blanc":
        rapport["code"] = 0
        return 0, rapport
    apres = sheet.lire_tout()
    a_apres = a_par_id(apres)
    pos_apres = positions([r[AL] for r in apres])
    c1 = [i for i, (_, u) in ecrites.items() if a_apres.get(i) != u or len(pos_apres.get(i, [])) != 1]
    c2 = sorted(i for i in set(a_avant) | set(a_apres) if i not in ecrites and a_avant.get(i, "") != a_apres.get(i, ""))
    b_al_apres = empreintes_b_al(apres)
    c3 = sorted(i for i in set(b_al_avant) | set(b_al_apres) if b_al_avant.get(i) != b_al_apres.get(i))
    c3_nous = [i for i in c3 if i in ecrites]
    # ④ : l'etiquette ecrite = celle que portent, A CET INSTANT, toutes les transactions de la ligne
    c4 = []
    if ecrites:
        liens = reg.liens_des_lignes(ecrites)
        info = reg.transactions({a for l in liens.values() for a, _ in l})
        for i, (_, u) in ecrites.items():
            eff = effectives(sorted({a for a, _ in liens.get(i, [])}), info)
            if {info[a]["uuid"] for a in eff} != {u}:
                c4.append(i)
    valeurs_a = Counter(propre(r[A]) for r in apres[1:] if propre(r[A]))
    c5 = sorted(v for v, n in valeurs_a.items() if n > 1)
    rapport["criteres"] = {
        "1_ecrites_relues_sur_leur_ID_Unique": {"attendu": len(ecrites), "fausses": c1},
        "2_aucune_autre_case_A_modifiee": {"fausses": c2},
        "3_rien_hors_de_A_par_nous": {"lignes_touchees_par_un_humain": c3, "dont_parmi_les_notres": c3_nous},
        "4_etiquette_ecrite_egale_a_celle_des_transactions": {"fausses": c4},
        "5_aucun_uuid_sur_deux_lignes": {"fausses": c5},
        "a_blanc_prevoyait": len(prevues), "ecrites_verifiees": len(ecrites),
    }
    rapport["ecrites"] = {i: {"ligne": r, "etiquette": u} for i, (r, u) in ecrites.items()}
    rouge = bool(c1 or c2 or c3_nous or c4 or c5)
    code = 4 if rapport["arret"] else (1 if rouge else 0)
    rapport["code"] = code
    return code, rapport


# ═══════════════════════════════════════════ DEFAIRE ═══════════════════════════════════════════
def derouler_defaire(*, mode: str, nom: str, sheet, memoire, a_avant_de_la_vague: dict[str, str] | None,
                     sortie: Path, quand: datetime, interrupteur=None, env_le_definit=False, emp_donnee=None,
                     journal=print) -> tuple[int, dict]:
    """Vide les cases que NOUS avons ecrites pour la vague `nom` -- SEULEMENT si elles portent encore notre
    valeur. `a_avant_de_la_vague` (la sauvegarde de l'ecriture : ID Unique -> A avant) permet de reconnaitre
    une case MAL POSEE : notre valeur sur une ligne dont A etait vide avant la vague."""
    assert mode in ("a_blanc", "defaire")
    if not memoire.existe():
        raise VerrouRefuse("la table app_sheet_ecrit n'existe pas chez Supabase : il n'y a rien a defaire "
                           "(aucune ecriture n'a pu avoir lieu sans elle)")
    memo = {i: m for i, m in memoire.lire(vague=nom).items() if m.get("etat") in ("prevu", "ecrit")}
    valeurs = sheet.lire_tout()
    emp_a = empreinte_colonne_a(valeurs)
    rapport = {"mode": mode, "vague": nom, "memoire_a_defaire": len(memo), "empreinte_colonne_a_avant": emp_a,
               "heure": quand.isoformat(timespec="seconds"), "plan": [], "code": None}
    journal("defaire %s : %d case(s) en memoire (prevu ou ecrit) ; colonne A %s" % (nom, len(memo), emp_a[:16]))

    def planifier(col_a, col_al):
        """D'abord les CASES : toute case de A qui porte une de NOS valeurs (celles de la memoire de cette
        vague). Ensuite les LIGNES de la memoire dont la valeur n'est plus nulle part."""
        pos = positions(col_al)
        plan, trouvees = [], set()
        notres = {m["valeur"]: i for i, m in memo.items()}
        for k, x in enumerate(col_a):
            v = propre(x)
            if not k or v not in notres:
                continue
            r, j, proprio = k + 1, propre(col_al[k]), notres[v]
            trouvees.add(v)
            if j == proprio:
                plan.append({"id_unique": proprio, "geste": "VIDER", "raison": "NOTRE_VALEUR_SUR_SA_LIGNE",
                             "ligne": r, "id_de_la_ligne": j})
            elif a_avant_de_la_vague is not None and j and a_avant_de_la_vague.get(j, None) == "":
                plan.append({"id_unique": proprio, "geste": "VIDER", "raison": "MAL_POSEE_SUR_%s" % j, "ligne": r,
                             "id_de_la_ligne": j})
            else:
                plan.append({"id_unique": proprio, "geste": "LAISSEE",
                             "raison": "NOTRE_VALEUR_SUR_UNE_AUTRE_LIGNE_SANS_PREUVE_QUE_A_ETAIT_VIDE",
                             "ligne": r, "id_de_la_ligne": j})
        for i, m in sorted(memo.items()):
            if m["valeur"] in trouvees:
                continue
            rows = pos.get(i, [])
            if len(rows) != 1:
                plan.append({"id_unique": i, "geste": "LAISSEE", "ligne": None,
                             "raison": "ID_UNIQUE_%s_ET_NOTRE_VALEUR_NULLE_PART" % ("ABSENT" if not rows else "EN_DOUBLE")})
            elif propre(col_a[rows[0] - 1]):
                plan.append({"id_unique": i, "geste": "LAISSEE", "raison": "AUTRE_VALEUR", "ligne": rows[0],
                             "valeur_trouvee": propre(col_a[rows[0] - 1])[:80]})
            else:
                plan.append({"id_unique": i, "geste": "MARQUER", "raison": "DEJA_VIDE", "ligne": rows[0]})
        return plan

    col_a, col_al = [r[A] for r in valeurs], [r[AL] for r in valeurs]
    plan = planifier(col_a, col_al)
    rapport["plan"] = plan
    rapport["compte"] = {"%s %s" % k: n for k, n in
                         Counter((p["geste"], p["raison"].split("_SUR_")[0]) for p in plan).items()}
    journal("plan : %s" % rapport["compte"])
    if mode == "a_blanc":
        rapport["code"] = 0
        return 0, rapport

    if env_le_definit:
        raise VerrouRefuse(f"{INTERRUPTEUR} est ecrit dans .env")
    if interrupteur != "1":
        raise VerrouRefuse(f"verrou 1 : {INTERRUPTEUR}=1 absent de l'environnement de la commande")
    if not emp_donnee or len(emp_donnee) < 12 or not emp_a.startswith(emp_donnee.lower()):
        raise VerrouRefuse("verrou 3 : la colonne A a change depuis l'a blanc du retour arriere")
    if dans_la_fenetre_interdite(quand):
        raise VerrouRefuse("garde : heure de la nuit")
    sheet.arme = True
    memoire.arme = True
    dos = sortie / "sauvegarde"
    dos.mkdir(parents=True, exist_ok=False)
    (dos / "sheet_A1_AL_avant_defaire.json").write_text(json.dumps(valeurs, ensure_ascii=False), encoding="utf-8")
    journal("SAUVEGARDE : %s" % dos)

    videes, marquees = [], []
    a_vider = [p for p in plan if p["geste"] == "VIDER"]
    for paquet in tranches(a_vider, PAQUET):
        col_a, col_al = sheet.lire_a_al()                     # relu juste avant : la ligne n'a pas bouge ?
        sures = [p for p in paquet
                 if p["ligne"] <= len(col_a)
                 and propre(col_a[p["ligne"] - 1]) == memo[p["id_unique"]]["valeur"]
                 and propre(col_al[p["ligne"] - 1]) == p["id_de_la_ligne"]]
        for p in paquet:
            if p not in sures:
                p["geste"], p["raison"] = "LAISSEE", "A_BOUGE_ENTRE_LE_PLAN_ET_LE_GESTE"
        if sures:
            sheet.vider([p["ligne"] for p in sures])
            col_a2, _ = sheet.lire_a_al()
            for p in sures:
                if not propre(col_a2[p["ligne"] - 1]):
                    videes.append(p)
                else:
                    p["geste"], p["raison"] = "LAISSEE", "PAS_VIDEE_APRES_LE_GESTE"
    for p in plan:
        if p["geste"] == "MARQUER":
            marquees.append(p["id_unique"])
    ids_finis = sorted({p["id_unique"] for p in videes} | set(marquees))
    # une ligne n'est « defaite » que si AUCUNE de ses cases n'est laissee (sa ligne ET une eventuelle mal posee)
    laissees_ids = {p["id_unique"] for p in plan if p["geste"] == "LAISSEE"}
    ids_finis = [i for i in ids_finis if i not in laissees_ids]
    if ids_finis:
        memoire.marquer(ids_finis, "defait")
    apres = sheet.lire_tout()
    a_apres = a_par_id(apres)
    restes = []
    if a_avant_de_la_vague is not None:
        restes = sorted(i for i in set(a_avant_de_la_vague) | set(a_apres)
                        if a_avant_de_la_vague.get(i, "") != a_apres.get(i, "") and i not in laissees_ids)
    rapport.update({"videes": len(videes), "marquees_deja_vides": len(marquees),
                    "laissees": sorted(laissees_ids), "differences_avec_l_avant_de_la_vague": restes,
                    "empreinte_colonne_a_apres": empreinte_colonne_a(apres)})
    code = 1 if restes else 0
    rapport["code"] = code
    return code, rapport


# ═══════════════════════════════════════════ PREPARER ═══════════════════════════════════════════
def preparer(args, reg, journal=print) -> int:
    exclus_b = lire_hors_vague()
    with Path(args.source).open(encoding="utf-8-sig", newline="") as f:
        tete = f.readline()
        f.seek(0)
        sep = ";" if tete.count(";") > tete.count(",") else ","
        source = {propre(r["id_unique"]): r for r in csv.DictReader(f, delimiter=sep)}
    dans_la_case = [i for i, r in source.items() if propre(r.get(args.colonne_case)) == args.case]
    if args.ids:
        voulues = [x.strip() for x in args.ids.split(",") if x.strip()]
    elif args.premieres:
        voulues = sorted(dans_la_case, key=lambda i: int(source[i].get("ligne_au_19_11") or 0))[:args.premieres]
    elif args.toutes:
        voulues = sorted(dans_la_case, key=lambda i: int(source[i].get("ligne_au_19_11") or 0))
    else:
        journal("preparer : --ids, --premieres N ou --toutes")
        return 3
    refus = []
    gardees = []
    for i in voulues:
        if i not in source:
            refus.append((i, "absente du fichier de classement %s" % Path(args.source).name))
        elif propre(source[i].get(args.colonne_case)) != args.case:
            refus.append((i, "case %s, pas %s" % (source[i].get(args.colonne_case), args.case)))
        elif i in exclus_b:
            refus.append((i, "%s : %s" % exclus_b[i]))
        else:
            gardees.append(i)
    liens = reg.liens_des_lignes(gardees)
    info = reg.transactions({a for l in liens.values() for a, _ in l})
    lignes = []
    for i in gardees:
        txs = sorted({a for a, _ in liens.get(i, [])})
        eff = effectives(txs, info)
        uuids = sorted({info[a]["uuid"] for a in eff})
        if not txs:
            refus.append((i, "le gel ne la relie a rien"))
        elif len(uuids) != 1:
            refus.append((i, "plusieurs etiquettes maintenant %s" % uuids))
        else:
            lignes.append([i, args.nom, propre(source[i].get("ligne_au_19_11")), uuids[0], " ".join(map(str, txs)),
                           "", "%s=%s (%s)" % (args.colonne_case, args.case, Path(args.source).name)])
    sortie = Path(args.dossier or (RACINE / "notice")) / ("CLASSEUR_VAGUE_%s_%s.csv"
                                                          % (args.nom, maintenant_local().strftime("%Y-%m-%d")))
    if sortie.exists():
        journal("REFUS : %s existe deja -- on n'ecrase pas un fichier de vague (le renommer ou changer --nom)" % sortie)
        return 3
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(COLONNES_VAGUE)
        w.writerows(lignes)
    journal("FICHIER DE VAGUE : %s -- %d ligne(s)" % (sortie, len(lignes)))
    journal("EMPREINTE (a recopier a la commande d'ecriture) : %s" % sha256_fichier(sortie))
    for i, r in refus:
        journal("   NON MISE dans la vague : %s -- %s" % (i, r))
    return 0


# ═══════════════════════════════════════════ rapports ═══════════════════════════════════════════
def ecrire_rapport(dossier: Path, rapport: dict, titre: str) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "rapport.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=1, default=str),
                                          encoding="utf-8")
    l = ["# %s" % titre, "", "```"]
    for k in ("mode", "vague", "heure", "lignes_du_fichier", "sha_vague", "empreinte_colonne_a_avant",
              "a_ecrire", "compte_raisons", "memoire_a_defaire", "compte", "videes", "marquees_deja_vides",
              "laissees", "differences_avec_l_avant_de_la_vague", "arret", "code"):
        if k in rapport:
            l.append("%-36s %s" % (k, rapport[k]))
    for k, v in (rapport.get("criteres") or {}).items():
        l.append("%-36s %s" % (k, v))
    l.append("```")
    if rapport.get("decisions"):
        l += ["", "## Ligne par ligne", "", "```"]
        for d in rapport["decisions"]:
            l.append("%-10s %-9s ligne %-5s %-38s %s %s" % (d["id_unique"], d["verdict"], d["ligne"],
                                                            d["etiquette"] or "", d["raison"], d["detail"]))
        l.append("```")
    if rapport.get("plan"):
        l += ["", "## Le plan du retour arriere", "", "```"]
        for p in rapport["plan"]:
            l.append("%-10s %-8s ligne %-5s %s" % (p["id_unique"], p["geste"], p["ligne"], p["raison"]))
        l.append("```")
    (dossier / "rapport.md").write_text("\n".join(l) + "\n", encoding="utf-8")


# ═══════════════════════════════════════════ SIMULER : l'epreuve ═══════════════════════════════════════════
def simuler(reg: Registre, journal=print) -> int:
    """L'epreuve complete sur une COPIE EN MEMOIRE du Sheet (lu une fois, en GET), la memoire dans un
    dictionnaire, le registre et le gel VRAIS (lus chez Supabase). Aucun POST ne peut partir : la classe du
    vrai Sheet n'est meme pas construite, et requests.post est remplace par une erreur."""
    import requests
    _requete = requests.request

    def _seulement_get(methode, url, **kw):                      # ceinture : seul un GET part vers Google
        if str(methode).upper() != "GET":
            raise VerrouRefuse("appel %s INTERDIT pendant la simulation" % methode)
        return _requete(methode, url, **kw)
    requests.request = _seulement_get
    requests.post = requests.put = requests.patch = requests.delete = _interdit
    sortie = SORTIES_SIMULATION / horodatage()
    sortie.mkdir(parents=True, exist_ok=True)
    verdicts: list[tuple[bool, str]] = []

    def attendu(cond: bool, texte: str):
        verdicts.append((bool(cond), texte))
        journal("   %s  %s" % ("VERT " if cond else "ROUGE", texte))

    reel = SheetReel()
    valeurs = reel.lire_tout()
    journal("Sheet lu une fois (GET) : %d lignes ; colonne A remplie sur %d"
            % (len(valeurs) - 1, sum(1 for r in valeurs[1:] if propre(r[A]))))
    exclus_b = lire_hors_vague()
    cl = {}
    with CLASSEMENT.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cl[r["id_unique"]] = r
    pos0 = positions([r[AL] for r in valeurs])

    def entree_vivante(i, nom, reg_=reg):
        l = reg_.liens_des_lignes([i]).get(i, [])
        txs = sorted({a for a, _ in l})
        info = reg_.transactions(txs)
        eff = effectives(txs, info)
        u = sorted({info[a]["uuid"] for a in eff})
        return {"id_unique": i, "nom_vague": nom, "ligne_vue": str(pos0.get(i, [""])[0]),
                "etiquette_prevue": u[0] if len(u) == 1 else (u[0] if u else ""), "transactions": txs, "admis": [],
                "case_source": cl.get(i, {}).get("case_aujourd_hui", "")}, info, l

    # ── les lignes nominales : la case VAGUE_1, dans l'ordre du Sheet, hors decision B ──
    v1 = sorted((i for i, r in cl.items() if r["case_aujourd_hui"] == "VAGUE_1" and i not in exclus_b and i in pos0),
                key=lambda i: pos0[i][0])
    nominales = [entree_vivante(i, "SIMULATION")[0] for i in v1[:240]]
    journal("%d lignes nominales tirees de la vague 1 du 19/11 (3 paquets)" % len(nominales))

    # ════ SCENARIO A : nominal + temoins inverses semes ════
    journal("SCENARIO A -- nominal, et 12 temoins inverses qui DOIVENT etre sautes et nommes")
    sheet = SheetMemoire(valeurs)
    memo = MemoireLocale()
    ent = [dict(e) for e in nominales]
    par_id = {e["id_unique"]: e for e in ent}
    attendus: dict[str, str] = {}
    graines = [e["id_unique"] for e in ent[:11]]
    x = iter(graines)
    s = next(x); sheet.v[pos0[s][0] - 1][A] = "E"; attendus[s] = "A_DEJA_REMPLIE"
    s = next(x); sheet.v[pos0[s][0] - 1][AL] = "ZZDISPARU"; attendus[s] = "ID_UNIQUE_ABSENT"
    s = next(x); sheet.v.append(ligne_pleine([""] * AL + [s])); attendus[s] = "ID_UNIQUE_EN_DOUBLE"
    s = next(x); par_id[s]["etiquette_prevue"] = "00000000-0000-0000-0000-000000000000"; attendus[s] = "ETIQUETTE_A_CHANGE"
    s = next(x); par_id[s]["transactions"] = sorted(par_id[s]["transactions"] + [99999999]); attendus[s] = "GEL_A_CHANGE"
    s = next(x)
    libre = next(k for k, r in enumerate(sheet.v) if k > 1 and not propre(r[A]) and propre(r[AL]) not in par_id)
    sheet.v[libre][A] = par_id[s]["etiquette_prevue"]; attendus[s] = "UUID_DEJA_DANS_LE_SHEET"
    s = next(x)
    memo.t[s] = {"id_unique": s, "colonne": COLONNE, "valeur": par_id[s]["etiquette_prevue"], "avant": "",
                 "etat": "ecrit", "vague": "UNE_AUTRE", "ligne_vue": 0, "ecrit_le": "", "defait_le": None,
                 "origine": "graine"}
    attendus[s] = "MEMOIRE_DIT_ECRIT_MAIS_A_VIDE"
    s1, s2 = next(x), next(x)
    par_id[s2]["etiquette_prevue"] = par_id[s1]["etiquette_prevue"]
    attendus[s1] = attendus[s2] = "UUID_EN_DOUBLE_DANS_LA_VAGUE"
    # une ligne de la decision B, glissee dans la vague
    b = sorted(i for i, (r, _) in exclus_b.items() if r == "DECISION_B")[0]
    eb = entree_vivante(b, "SIMULATION")[0]
    ent.append(eb); attendus[b] = "DECISION_B"
    # une ligne des 19 du 20/11, glissee dans la vague
    b19 = sorted(i for i, (r, _) in exclus_b.items() if r == "DECISION_19")[0]
    ent.append(entree_vivante(b19, "SIMULATION")[0]); attendus[b19] = "DECISION_19"
    # des lignes REELLES dans les cases bloquees du 19/11 : la premiere qui, a l'instant, montre le defaut
    for case, raison in (("ETIQUETTE_PARTAGEE", "ETIQUETTE_PARTAGEE"), ("PLUSIEURS_DOSSIERS", "PLUSIEURS_DOSSIERS"),
                         ("LIEN_A_VALIDER", "LIEN_NON_SUR")):
        trouve = None
        for i in sorted((i for i, r in cl.items() if r["case_aujourd_hui"] == case and i in pos0 and i not in exclus_b),
                        key=lambda i: pos0[i][0])[:15]:
            e, info, l = entree_vivante(i, "SIMULATION")
            if not e["transactions"] or propre(sheet.v[pos0[i][0] - 1][A]):
                continue
            d = juger_paquet([e], [r[A] for r in sheet.v], [r[AL] for r in sheet.v], reg, {}, exclus_b, set())[0]
            if d["raison"] == raison:
                trouve = e
                break
        if trouve:
            ent.append(trouve); attendus[trouve["id_unique"]] = raison
        else:
            attendu(False, "temoin %s : aucune ligne reelle ne montre le defaut a l'instant -- NON EPROUVE" % raison)
    # C5 seule : on force l'origine « classeur » sur TOUTES les transactions d'une ligne nominale
    s = next(x)
    forcee = {a: "classeur" for a in par_id[s]["transactions"]}
    attendus[s] = "C5_SEULE"
    reg_sim = RegistreSimule(reg, forcee)
    # temoin POSITIF de la regle C5 : une ligne qui a une creation du Sheet dans un AUTRE dossier, et qui s'ecrit
    c5_pos = None
    for i in sorted((i for i, r in cl.items() if r["case_aujourd_hui"] == "PLUSIEURS_DOSSIERS" and i in pos0
                     and i not in exclus_b), key=lambda i: pos0[i][0])[:80]:
        e, info, l = entree_vivante(i, "SIMULATION")
        c5_ = [a for a in e["transactions"] if info.get(a, {}).get("origine") == "classeur"]
        hk = [a for a in e["transactions"] if a in info and info[a]["origine"] != "classeur"]
        if not c5_ or not hk or {info[a]["uuid"] for a in c5_} <= {info[a]["uuid"] for a in hk}:
            continue
        d = juger_paquet([e], [r[A] for r in sheet.v], [r[AL] for r in sheet.v], reg, {}, exclus_b, set())[0]
        if d["verdict"] == "A_ECRIRE":
            c5_pos = e
            break
    if c5_pos:
        ent.append(c5_pos); attendus[c5_pos["id_unique"]] = "A_ECRIRE"
        journal("   temoin positif C5 : %s (une creation du Sheet dans un autre dossier ; elle doit s'ecrire)"
                % c5_pos["id_unique"])
    else:
        attendu(False, "temoin positif C5 : aucune ligne trouvee -- NON EPROUVE")

    valeurs_a = sheet.lire_tout()
    a_avant = a_par_id(valeurs_a)
    emp = empreinte_colonne_a(valeurs_a)
    quand = maintenant_local().replace(hour=20, minute=0)
    code, rap = derouler_ecriture(mode="ecrire", nom="SIMULATION", entrees=ent, sha_vague="f" * 64, sheet=sheet,
                                  memoire=memo, reg=reg_sim, sortie=sortie / "A_ecrire", quand=quand,
                                  interrupteur="1", sha_donne="f" * 16, emp_donnee=emp[:16],
                                  journal=lambda t: journal("      " + t))
    ecrire_rapport(sortie / "A_ecrire", rap, "Simulation, scenario A -- ecrire")
    dec = {d["id_unique"]: d for d in rap["decisions"]}
    for i, r in sorted(attendus.items()):
        got = dec[i]["verdict"] if r == "A_ECRIRE" else dec[i]["raison"]
        attendu(got == r, "temoin %-10s attendu %-30s obtenu %s %s" % (i, r, got, dec[i]["detail"][:70]))
    normales = [e["id_unique"] for e in ent if e["id_unique"] not in attendus]
    ecrites = rap.get("ecrites", {})
    sautees_normales = [(i, dec[i]["raison"], dec[i]["detail"][:60]) for i in normales if dec[i]["verdict"] != "A_ECRIRE"]
    attendu(len(ecrites) > 150, "TEMOIN POSITIF : %d lignes ECRITES -- %d nominales sur %d, + le temoin positif C5 "
            "(un zero ne se croit pas)" % (len(ecrites), sum(1 for i in normales if i in ecrites), len(normales)))
    if sautees_normales:
        journal("      (nominales sautees a l'instant, nommees -- la base a bouge depuis le 19/11 : %d) %s"
                % (len(sautees_normales), sautees_normales[:8]))
    attendu(code == 0, "code de l'ecriture = %s (attendu 0) ; criteres %s" % (code, {k: (v if not isinstance(v, dict) else
            {kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}) for k, v in rap["criteres"].items()}))
    attendu(all(memo.t[i]["etat"] == "ecrit" for i in ecrites), "la memoire dit « ecrit » pour les %d" % len(ecrites))
    attendu(all(sheet.v[pos0[i][0] - 1][A] == u["etiquette"] for i, u in ecrites.items() if i in pos0),
            "chaque etiquette est sur la ligne de SON ID Unique (relu dans la copie)")

    # ── le retour arriere, avec deux humains passes entre-temps ──
    ids_e = sorted(ecrites)
    h1 = ids_e[0]
    sheet.v[pos0[h1][0] - 1][A] = "corrige par un humain"
    k1, k2 = pos0[ids_e[1]][0] - 1, pos0[ids_e[2]][0] - 1
    sheet.v[k1], sheet.v[k2] = sheet.v[k2], sheet.v[k1]          # un tri humain : deux lignes echangees
    emp_d = empreinte_colonne_a(sheet.lire_tout())
    code_d, rap_d = derouler_defaire(mode="defaire", nom="SIMULATION", sheet=sheet, memoire=memo,
                                     a_avant_de_la_vague=a_avant, sortie=sortie / "A_defaire", quand=quand,
                                     interrupteur="1", emp_donnee=emp_d[:16], journal=lambda t: journal("      " + t))
    ecrire_rapport(sortie / "A_defaire", rap_d, "Simulation, scenario A -- defaire")
    attendu(rap_d["videes"] == len(ecrites) - 1, "retour arriere : %d cases videes (attendu %d)"
            % (rap_d["videes"], len(ecrites) - 1))
    attendu(rap_d["laissees"] == [h1], "la case corrigee par un humain est NOMMEE et LAISSEE : %s" % rap_d["laissees"])
    a_fin = a_par_id(sheet.lire_tout())
    diff = sorted(i for i in set(a_avant) | set(a_fin) if a_avant.get(i, "") != a_fin.get(i, ""))
    attendu(diff == [h1], "apres le retour arriere, la colonne A est celle d'AVANT, sauf la case humaine : %s" % diff)
    attendu(memo.t[h1]["etat"] == "ecrit" and all(memo.t[i]["etat"] == "defait" for i in ids_e if i != h1),
            "la memoire : %d « defait », la case humaine reste « ecrit »" % (len(ids_e) - 1))

    # ════ SCENARIO B : un humain insere une ligne ENTRE la relecture et l'ecriture ════
    journal("SCENARIO B -- une ligne inseree en haut du Sheet pendant le paquet : ARRET, puis retour arriere")
    sheet = SheetMemoire(valeurs)
    memo = MemoireLocale()
    ent_b = [dict(e) for e in nominales[40:45]]
    a_avant_b = a_par_id(sheet.lire_tout())
    emp_b = empreinte_colonne_a(sheet.lire_tout())

    def inserer(sh):
        sh.v.insert(1, ligne_pleine([]))
        sh.crochet = None
    sheet.crochet = inserer
    code_b, rap_b = derouler_ecriture(mode="ecrire", nom="SIM_B", entrees=ent_b, sha_vague="e" * 64, sheet=sheet,
                                      memoire=memo, reg=reg, sortie=sortie / "B_ecrire", quand=quand, interrupteur="1",
                                      sha_donne="e" * 16, emp_donnee=emp_b[:16], journal=lambda t: journal("      " + t))
    ecrire_rapport(sortie / "B_ecrire", rap_b, "Simulation, scenario B -- ecrire (course)")
    attendu(code_b == 4 and rap_b["arret"] and len(rap_b["arret"]["mal_posees"]) == len(ent_b),
            "ARRET IMMEDIAT, code %s, %d case(s) mal posee(s) nommee(s) (attendu 4 et %d)"
            % (code_b, len((rap_b["arret"] or {}).get("mal_posees", [])), len(ent_b)))
    emp_bd = empreinte_colonne_a(sheet.lire_tout())
    code_bd, rap_bd = derouler_defaire(mode="defaire", nom="SIM_B", sheet=sheet, memoire=memo,
                                       a_avant_de_la_vague=a_avant_b, sortie=sortie / "B_defaire", quand=quand,
                                       interrupteur="1", emp_donnee=emp_bd[:16], journal=lambda t: journal("      " + t))
    ecrire_rapport(sortie / "B_defaire", rap_bd, "Simulation, scenario B -- defaire (course)")
    a_fin_b = a_par_id(sheet.lire_tout())
    diff_b = sorted(i for i in set(a_avant_b) | set(a_fin_b) if a_avant_b.get(i, "") != a_fin_b.get(i, ""))
    attendu(code_bd == 0 and not diff_b, "le retour arriere retrouve les cases MAL POSEES et rend la colonne A "
            "d'avant (code %s, differences %s)" % (code_bd, diff_b))

    # ════ SCENARIO C : les verrous ════
    journal("SCENARIO C -- chaque verrou ferme doit REFUSER (code 3)")
    sheet = SheetMemoire(valeurs)
    emp_c = empreinte_colonne_a(sheet.lire_tout())
    cas = [("sans l'interrupteur", dict(interrupteur=None)),
           ("interrupteur ecrit dans .env", dict(env_le_definit=True)),
           ("mauvaise empreinte du fichier", dict(sha_donne="0" * 16)),
           ("empreinte du fichier trop courte", dict(sha_donne="d" * 6)),
           ("colonne A changee depuis l'a blanc", dict(emp_donnee="0" * 16)),
           ("en pleine nuit (05:12)", dict(quand=quand.replace(hour=5, minute=12)))]
    for texte, change in cas:
        kw = dict(interrupteur="1", env_le_definit=False, sha_donne="d" * 16, emp_donnee=emp_c[:16], quand=quand)
        kw.update(change)
        mem_c = MemoireLocale()
        try:
            derouler_ecriture(mode="ecrire", nom="SIM_C", entrees=nominales[:3], sha_vague="d" * 64, sheet=sheet,
                              memoire=mem_c, reg=reg, sortie=sortie / "C", journal=lambda t: None, **kw)
            attendu(False, "verrou « %s » : il a LAISSE PASSER" % texte)
        except VerrouRefuse as e:
            attendu(sheet.appels["POST"] == 0 and not mem_c.t, "verrou « %s » : refuse, rien ecrit (%s)"
                    % (texte, str(e)[:70]))
    reel_tente = SheetReel()
    try:
        reel_tente.ecrire([(2, "x")])
        attendu(False, "le vrai Sheet desarme a ACCEPTE d'ecrire")
    except VerrouRefuse:
        attendu(True, "le vrai Sheet, desarme, refuse d'ecrire (sans aucun appel reseau)")
    attendu(reel.appels.get("POST", 0) == 0 and reel_tente.appels.get("POST", 0) == 0,
            "AUCUN appel POST vers Google pendant toute l'epreuve (GET : %d)" % reel.appels.get("GET", 0))

    rouges = [t for ok, t in verdicts if not ok]
    (sortie / "VERDICT.txt").write_text("\n".join(("VERT  " if ok else "ROUGE ") + t for ok, t in verdicts) + "\n",
                                        encoding="utf-8")
    journal("")
    journal("EPREUVE : %d verdicts, %d rouge(s) -- %s" % (len(verdicts), len(rouges), sortie))
    return 1 if rouges else 0


def _interdit(*a, **k):
    raise VerrouRefuse("appel reseau en ecriture INTERDIT pendant la simulation")


# ═══════════════════════════════════════════ la commande ═══════════════════════════════════════════
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = p.add_subparsers(dest="etape", required=True)
    pr = sp.add_parser("preparer")
    pr.add_argument("--nom", required=True)
    pr.add_argument("--source", default=str(CLASSEMENT))
    pr.add_argument("--colonne-case", default="case_aujourd_hui")
    pr.add_argument("--case", default="VAGUE_1")
    pr.add_argument("--dossier", help="ou ecrire le fichier de vague (defaut : notice/)")
    g = pr.add_mutually_exclusive_group()
    g.add_argument("--ids")
    g.add_argument("--premieres", type=int)
    g.add_argument("--toutes", action="store_true")
    ab = sp.add_parser("a_blanc")
    ab.add_argument("--vague", required=True)
    ec = sp.add_parser("ecrire")
    ec.add_argument("--vague", required=True)
    ec.add_argument("--empreinte-vague", required=True)
    ec.add_argument("--empreinte-colonne-a", required=True)
    de = sp.add_parser("defaire")
    de.add_argument("--nom", required=True)
    de.add_argument("--sauvegarde", help="le dossier de sauvegarde de l'ecriture (sinon : le plus recent pour ce nom)")
    de.add_argument("--empreinte-colonne-a")
    sp.add_parser("simuler")
    args = p.parse_args()

    env_le_definit = False
    # les deux fichiers que lit le registre (push_upgrade_to_supabase.DEFAULT_ENV_FILES) : la racine, puis l'app
    for envf in (RACINE / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
        if envf.exists():
            for raw in envf.read_text(encoding="utf-8", errors="ignore").splitlines():
                if raw.strip().startswith(INTERRUPTEUR + "=") or raw.strip().startswith(INTERRUPTEUR + " ="):
                    env_le_definit = True
        load_env_file(envf)
    if INTERRUPTEUR_A_LA_COMMANDE is None:
        os.environ.pop(INTERRUPTEUR, None)       # .env ne l'arme jamais

    try:
        reg = Registre(client_supabase())
        reg.verifier_plafond()
        if args.etape == "preparer":
            return preparer(args, reg)
        if args.etape == "simuler":
            return simuler(reg)
        memoire = MemoireSupabase(client_supabase())
        sheet = SheetReel()
        quand = maintenant_local()
        if args.etape in ("a_blanc", "ecrire"):
            nom, entrees, sha = lire_vague(Path(args.vague))
            mode = "a_blanc" if args.etape == "a_blanc" else "ecrire"
            sortie = SORTIES / ("%s_%s_%s" % (horodatage(quand), nom, mode.upper()))
            code, rap = derouler_ecriture(mode=mode, nom=nom, entrees=entrees, sha_vague=sha, sheet=sheet,
                                          memoire=memoire, reg=reg, sortie=sortie, quand=quand,
                                          interrupteur=INTERRUPTEUR_A_LA_COMMANDE, env_le_definit=env_le_definit,
                                          sha_donne=getattr(args, "empreinte_vague", None),
                                          emp_donnee=getattr(args, "empreinte_colonne_a", None))
            ecrire_rapport(sortie, rap, "Colonne A, vague %s -- %s" % (nom, mode))
            print("LIGNES A ECRIRE : %d ; SAUTEES : %s" % (rap["a_ecrire"], rap["compte_raisons"]))
            if mode == "a_blanc":
                print("POUR ECRIRE (avec %s=1 a la commande) :" % INTERRUPTEUR)
                print("   --empreinte-vague %s --empreinte-colonne-a %s" % (sha[:16], rap["empreinte_colonne_a_avant"][:16]))
                if not rap["memoire_existe"]:
                    print("   ⛔ la table app_sheet_ecrit n'existe pas encore : l'ecriture serait REFUSEE")
            print("RAPPORT : %s (code %s)" % (sortie, code))
            return code
        if args.etape == "defaire":
            if args.sauvegarde:
                sauv = Path(args.sauvegarde)
            else:
                cands = sorted(SORTIES.glob("*_%s_ECRIRE" % args.nom))
                sauv = cands[-1] / "sauvegarde" if cands else None
            a_avant = None
            if sauv and (sauv / "colonne_a_al_avant.csv").exists():
                with (sauv / "colonne_a_al_avant.csv").open(encoding="utf-8") as f:
                    a_avant = {r["id_unique"]: r["A"] for r in csv.DictReader(f, delimiter=";") if r["id_unique"]}
            print("sauvegarde de l'ecriture : %s" % (sauv if a_avant is not None else
                                                    "INTROUVABLE -- une case mal posee ne sera pas reconnue"))
            mode = "defaire" if (INTERRUPTEUR_A_LA_COMMANDE == "1" and args.empreinte_colonne_a) else "a_blanc"
            sortie = SORTIES / ("%s_%s_DEFAIRE_%s" % (horodatage(quand), args.nom, mode.upper()))
            code, rap = derouler_defaire(mode=mode, nom=args.nom, sheet=sheet, memoire=memoire,
                                         a_avant_de_la_vague=a_avant, sortie=sortie, quand=quand,
                                         interrupteur=INTERRUPTEUR_A_LA_COMMANDE, env_le_definit=env_le_definit,
                                         emp_donnee=args.empreinte_colonne_a)
            ecrire_rapport(sortie, rap, "Colonne A, vague %s -- retour arriere (%s)" % (args.nom, mode))
            if mode == "a_blanc":
                print("POUR DEFAIRE (avec %s=1 a la commande) : --empreinte-colonne-a %s"
                      % (INTERRUPTEUR, rap["empreinte_colonne_a_avant"][:16]))
            print("RAPPORT : %s (code %s)" % (sortie, code))
            return code
    except VerrouRefuse as e:
        print("⛔ REFUS : %s" % e)
        return 3
    except LectureRatee as e:
        print("⛔ LECTURE RATEE (jamais un vert) : %s" % e)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
