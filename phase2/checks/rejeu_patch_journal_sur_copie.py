#!/usr/bin/env python
"""LE REJEU DU PATCH DU JOURNAL SUR UNE COPIE -- chantier classeur, 22/11 soir.

SON MOT (reponses 21 ter, question 1) : « AUCUN [de tes controles] NE VERIFIE QUE LA FONCTION MODIFIEE POSE LES MEMES
  NUMEROS QU'AUJOURD'HUI. [...] REJOUE LA FONCTION MODIFIEE SUR UNE COPIE et prouve qu'elle redonne EXACTEMENT les
  etiquettes et les numeros d'aujourd'hui. [...] Je ne doute pas de ton patch. Je refuse que la NUIT soit son premier
  essai. »

⚠ CE QUE L'OUTIL DU MATIN NE POUVAIT PAS FAIRE : le rejeu « zero ecart sur 31 368 » rejoue une COPIE EN PYTHON des
  regles de la pose (coupe_preuve_interne.pose_de_nuit), pas la fonction SQL. Il ne voit donc pas le patch. Ici, c'est
  LA VRAIE FONCTION qui tourne -- le texte lu chez Supabase, et le FICHIER DU PATCH tel qu'il sera colle -- sur un
  Postgres LOCAL (meme version que Supabase : 17.6), jamais sur la production.

ETAPES (une par appel, python -u) :
  extraire                LECTURE SEULE chez Supabase (REPEATABLE READ, READ ONLY) : ce que la pose lit et ecrit --
                          les 5 fonctions (texte + empreinte), le registre (les 8 colonnes que la pose lit), les annees
                          de mandat, les dates convenues, le compteur, le journal -> CACHE/<horodatage>/
  rejouer --pg <bin>      sur un Postgres LOCAL (localhost seulement, port 54329, arrete a la fin) :
                          . la COPIE : chargee, puis ses empreintes comparees a celles de Supabase (registre, compteur,
                            journal) et les 5 fonctions a la leur (md5 de pg_get_functiondef) ;
                          . AVANT = la fonction d'aujourd'hui ; APRES = la copie + LE FICHIER DU PATCH, joue tel quel
                            (sa garde, sa colonne, sa fonction, ses 190 lignes, son controle) ;
                          . CINQ ETATS, chacun rejoue des deux cotes a partir du MEME depart :
                              S0 aujourd'hui (la nuit telle qu'elle est : rien a faire)
                              S1 l'arrivee du protocole (le chainage du rejeu E : fusions et scissions, les numeros
                                 neufs) -- et contre la PREDICTION des numeros neufs (protocole_les_numeros_neufs.py)
                              S2 defait (des groupes sans etiquette -> POSE, des pieces nues -> PROPAGATION) + S1
                              S3 S1 a blanc (p_a_blanc) : rien ne doit changer, des deux cotes
                              S4 S2 avec p_limite = 25
                            on compare : chaque piece (chaine, etiquette, numero), le compteur, les lignes neuves du
                            journal (sans la colonne neuve), ce que la fonction rend. Une etiquette NEE pendant le rejeu
                            est tiree au hasard (gen_random_uuid) : elle est nommee par sa plus petite piece, des deux
                            cotes ;
                          . l'ANCIEN NUMERO ecrit par APRES : chaque scission = le numero du dossier coupe, chaque fusion
                            = le numero absorbe, rien pour une pose ou une propagation ;
                          . le TEMOIN INVERSE : APRES fausse expres (le rang d'une scission + 1) -> la comparaison DOIT
                            crier, sinon elle est aveugle ;
                          . la REPETITION du patch (ses 9 controles) sur APRES, et son INVERSE sur une copie : la
                            fonction revient a l'empreinte 815e956f.
CODES : 0 vert . 1 un rouge . 2 pas pu lire / lancer
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache\rejeu_patch_journal")
PATCH = RACINE / "supabase" / "patch_journal_ancien_numero_2026-11-22.sql"
REPETITION = RACINE / "supabase" / "patch_journal_ancien_numero_2026-11-22_REPETITION.sql"
INVERSE = RACINE / "supabase" / "patch_journal_ancien_numero_2026-11-22_INVERSE.sql"
EMPREINTE_FONCTION = "815e956f716cceb6477876b774b9f885"
FONCTIONS = ("app_dossier_numero_format", "app_dossier_annee_date_transaction", "app_dossier_jour_date_transaction",
             "app_dossier_annee_ouverture", "app_poser_etiquettes_dossier")
PORT = 54329
#: ce que la pose lit et ecrit, et rien d'autre (lu dans le texte des 5 fonctions le 22/11)
TABLES = {
    "ledger": ("public.app_affaire_ledger",
               "app_affaire_id, kind, date, propositions_json, hektor_annonce_id, app_chaine_id, app_dossier_uuid, "
               "app_dossier_numero", "app_affaire_id"),
    "mandat": ("public.app_mandat", "hektor_annonce_id, date_debut", "hektor_annonce_id, date_debut"),
    "convenue": ("public.app_affaire_date_convenue", "app_affaire_id, jour", "app_affaire_id"),
    "compteur": ("public.app_dossier_numero_compteur", "annee, dernier", "annee"),
    "journal": ("public.app_dossier_etiquette_journal",
                "id, quand, evenement, dossier_uuid, dossier_numero, autre_uuid, app_chaine_id, transactions, combien, "
                "pourquoi", "id"),
}
DDL = """
create table public.app_affaire_ledger (app_affaire_id bigint primary key, kind text, date text, propositions_json jsonb,
  hektor_annonce_id bigint, app_chaine_id bigint, app_dossier_uuid uuid, app_dossier_numero text);
create table public.app_mandat (hektor_annonce_id text, date_debut text);
create table public.app_affaire_date_convenue (app_affaire_id bigint primary key, jour text not null);
create table public.app_dossier_numero_compteur (annee integer primary key, dernier integer not null default 0,
  constraint app_dossier_numero_compteur_dernier_check check (dernier >= 0));
create table public.app_dossier_etiquette_journal (id bigserial primary key, quand timestamptz not null default now(),
  evenement text not null, dossier_uuid uuid not null, dossier_numero text, autre_uuid uuid, app_chaine_id bigint,
  transactions bigint[] not null default '{}'::bigint[], combien integer not null default 0, pourquoi text,
  constraint app_dossier_etiquette_journal_evenement_check
    check (evenement = any (array['pose'::text, 'propagation'::text, 'fusion'::text, 'scission'::text])));
"""
#: l'empreinte d'une table : chaque champ en texte (NULL = ∅), joints par chr(31), lignes triees (collate "C"), md5
EMPREINTE_SQL = ("select count(*), md5(coalesce(string_agg(x, E'\\n' order by x collate \"C\"), '')) from (select "
                 "concat_ws(chr(31), %s) as x from %s) t")
FAUSSE = ("(c.dernier + row_number() over (partition by s.annee", "(c.dernier + 1 + row_number() over (partition by s.annee")


def dire(s: str = "") -> None:
    print(s, flush=True)


def empreinte(cu, table: str, cols: str) -> tuple[int, str]:
    champs = ", ".join("coalesce(%s::text, '∅')" % c.strip() for c in cols.split(","))
    cu.execute(EMPREINTE_SQL % (champs, table))
    n, m = cu.fetchone()
    return int(n), m


# ═══════════════════════════════════════════ EXTRAIRE (lecture seule) ═══════════════════════════════════════════
def etape_extraire() -> int:
    import sauvegarde_datee_classeur as S
    d = CACHE / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    d.mkdir(parents=True, exist_ok=False)
    try:
        cn, cu = S.connexion()
    except Exception as e:  # noqa: BLE001
        dire("⛔ Supabase n'a pas pu etre lu (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    try:
        man = {"quand": datetime.now().isoformat(timespec="seconds"), "fonctions": {}, "tables": {}}
        # ⚠ la date du journal s'ecrit selon le fuseau de la SESSION : les deux cotes en UTC, sinon l'empreinte ment
        cu.execute("set time zone 'UTC'")
        cu.execute("select version(), datcollate, datctype from pg_database where datname = current_database()")
        man["version"], man["collation"], man["ctype"] = cu.fetchone()
        for f in FONCTIONS:
            cu.execute("select p.oid::regprocedure::text, pg_get_functiondef(p.oid), md5(pg_get_functiondef(p.oid)) "
                       "from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
                       "where n.nspname = 'public' and p.proname = %s", (f,))
            rows = cu.fetchall()
            if len(rows) != 1:
                raise SystemExit("⛔ %s : %d definitions (1 attendue)" % (f, len(rows)))
            sig, texte, m = rows[0]
            if "\r" in texte:
                raise SystemExit("⛔ %s : le texte porte un retour chariot" % f)
            (d / ("fonction_%s.sql" % f)).write_text(texte, encoding="utf-8", newline="\n")
            man["fonctions"][f] = {"signature": sig, "md5": m}
        if man["fonctions"]["app_poser_etiquettes_dossier"]["md5"] != EMPREINTE_FONCTION:
            dire("⛔ la fonction de pose n'est plus celle du patch (%s) -- le patch s'arreterait de lui-meme : code 1"
                 % man["fonctions"]["app_poser_etiquettes_dossier"]["md5"])
            return 1
        for k, (table, cols, ordre) in TABLES.items():
            buf = io.StringIO()
            cu.copy_expert("copy (select %s from %s order by %s) to stdout with (format csv)" % (cols, table, ordre),
                           buf)
            (d / ("%s.csv" % k)).write_text(buf.getvalue(), encoding="utf-8", newline="")
            n, m = empreinte(cu, table, cols)
            man["tables"][k] = {"table": table, "colonnes": cols, "lignes": n, "empreinte": m}
            dire("   %-9s %-40s %7d lignes  empreinte %s" % (k, table, n, m))
        cu.execute("select last_value, is_called from public.app_dossier_etiquette_journal_id_seq")
        man["sequence_journal"] = list(cu.fetchone())
        cn.rollback()
    finally:
        cn.close()
    (d / "manifeste.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    dire("EXTRAIT, en lecture seule -> %s (Supabase %s ; fonction de pose %s)" % (
        d, man["version"].split(" on ")[0], man["fonctions"]["app_poser_etiquettes_dossier"]["md5"]))
    return 0


# ═══════════════════════════════════════════ LE POSTGRES LOCAL ═══════════════════════════════════════════
class Local:
    """Un Postgres LOCAL, dans le cache, a l'ecoute de localhost seulement -- demarre pour le rejeu, arrete apres."""

    def __init__(self, binaires: Path):
        self.bin = binaires
        self.data = CACHE / "pgdata"
        self.journal = CACHE / "pg_local.log"

    def _exe(self, nom: str) -> str:
        p = self.bin / (nom + ".exe")
        if not p.exists():
            raise SystemExit("⛔ %s introuvable dans %s" % (p.name, self.bin))
        return str(p)

    def demarrer(self) -> None:
        if not (self.data / "PG_VERSION").exists():
            subprocess.run([self._exe("initdb"), "-D", str(self.data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                            "--locale=C"], check=True, capture_output=True)
        # ⚠ PAS de capture_output ici (22/11, 21:40) : sous Windows le serveur lance par pg_ctl HERITE des tuyaux, et
        #   subprocess.run attend leur fin -- qui ne vient jamais. Le serveur ecrit deja dans son journal (-l).
        subprocess.run([self._exe("pg_ctl"), "-D", str(self.data), "-l", str(self.journal), "-w", "-o",
                        "-p %d -c listen_addresses=localhost" % PORT, "start"], check=True,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def arreter(self) -> None:
        subprocess.run([self._exe("pg_ctl"), "-D", str(self.data), "-m", "fast", "-w", "stop"],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def cnx(base: str = "postgres", autocommit: bool = True):
        import psycopg2
        cn = psycopg2.connect(host="localhost", port=PORT, user="postgres", dbname=base, connect_timeout=10,
                              options="-c TimeZone=UTC")
        cn.autocommit = autocommit
        return cn


def charger_modele(L: Local, d: Path, man: dict) -> list[str]:
    """La base « modele » : les 5 tables chargees, les 5 fonctions d'aujourd'hui. Rend la liste des rouges."""
    rouges = []
    cn = L.cnx()
    cu = cn.cursor()
    for b in ("modele", "modele_apres", "avant", "apres", "avant2", "faux", "inverse"):
        cu.execute("drop database if exists %s" % b)
    cu.execute("create database modele")
    cn.close()
    cn = L.cnx("modele", autocommit=False)
    cu = cn.cursor()
    cu.execute(DDL)
    for k, (table, cols, _o) in TABLES.items():
        with (d / ("%s.csv" % k)).open(encoding="utf-8", newline="") as f:
            cu.copy_expert("copy %s (%s) from stdin with (format csv)" % (table, cols), f)
    lv, ic = man["sequence_journal"]
    cu.execute("select setval('public.app_dossier_etiquette_journal_id_seq', %s, %s)", (lv, ic))
    for f in FONCTIONS:
        cu.execute((d / ("fonction_%s.sql" % f)).read_text(encoding="utf-8"))
    cn.commit()
    for k, (table, cols, _o) in TABLES.items():
        n, m = empreinte(cu, table, cols)
        ok = (n, m) == (man["tables"][k]["lignes"], man["tables"][k]["empreinte"])
        dire("   copie %-9s %7d lignes, empreinte %s -- %s" % (k, n, m, "IDENTIQUE a Supabase" if ok else
                                                                "⛔ DIFFERENTE de Supabase"))
        if not ok:
            rouges.append("copie %s differente" % k)
    for f in FONCTIONS:
        cu.execute("select md5(pg_get_functiondef(p.oid)) from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
                   "where n.nspname = 'public' and p.proname = %s", (f,))
        m = cu.fetchone()[0]
        ok = m == man["fonctions"][f]["md5"]
        dire("   fonction %-36s %s -- %s" % (f, m, "IDENTIQUE a Supabase" if ok else "⛔ DIFFERENTE"))
        if not ok:
            rouges.append("fonction %s differente" % f)
    cn.rollback()
    cn.close()
    return rouges


def base_depuis(modele: str, nom: str) -> None:
    cn = Local.cnx()
    cu = cn.cursor()
    cu.execute("drop database if exists %s" % nom)
    cu.execute("create database %s template %s" % (nom, modele))
    cn.close()


def jouer_fichier(base: str, f: Path, remplacer: tuple | None = None) -> None:
    """Un fichier SQL joue TEL QUEL (ses propres begin / commit), comme il sera colle."""
    texte = f.read_text(encoding="utf-8")
    if remplacer:
        if texte.count(remplacer[0]) != 1:
            raise SystemExit("⛔ l'ancre du temoin inverse est trouvee %d fois" % texte.count(remplacer[0]))
        texte = texte.replace(*remplacer)
    cn = Local.cnx(base)
    try:
        cn.cursor().execute(texte)
    finally:
        cn.close()


# ═══════════════════════════════════════════ LES ETATS, ET LA COMPARAISON ═══════════════════════════════════════════
def preparer(base: str, etat: str, chE: dict | None) -> None:
    """Le MEME depart des deux cotes : des requetes deterministes, sans hasard."""
    cn = Local.cnx(base, autocommit=False)
    cu = cn.cursor()
    if etat in ("S1", "S2", "S3", "S4") and chE:
        cu.execute("create temporary table _ch (a bigint primary key, c bigint)")
        buf = io.StringIO("".join("%d,%s\n" % (a, "" if c is None else c) for a, c in chE.items()))
        cu.copy_expert("copy _ch from stdin with (format csv)", buf)
        cu.execute("update public.app_affaire_ledger l set app_chaine_id = _ch.c from _ch "
                   "where l.app_affaire_id = _ch.a and l.app_chaine_id is distinct from _ch.c")
    if etat in ("S2", "S4"):
        # des GROUPES entiers sans etiquette -> la pose ; des pieces nues dans un groupe etiquete -> la propagation
        cu.execute("update public.app_affaire_ledger set app_dossier_uuid = null, app_dossier_numero = null "
                   "where app_chaine_id % 17 = 3")
        cu.execute("update public.app_affaire_ledger l set app_dossier_uuid = null, app_dossier_numero = null "
                   "where l.app_affaire_id % 23 = 5 and l.app_chaine_id % 17 <> 3 and l.app_affaire_id <> "
                   "(select min(app_affaire_id) from public.app_affaire_ledger x where x.app_chaine_id = l.app_chaine_id)")
    cn.commit()
    cn.close()


def photo(base: str, apres: bool) -> dict:
    cn = Local.cnx(base, autocommit=False)
    cu = cn.cursor()
    cu.execute("select app_affaire_id, app_chaine_id, app_dossier_uuid::text, app_dossier_numero "
               "from public.app_affaire_ledger")
    led = {a: (c, u, n) for a, c, u, n in cu.fetchall()}
    cu.execute("select annee, dernier from public.app_dossier_numero_compteur")
    cpt = dict(cu.fetchall())
    cu.execute("select coalesce(max(id), 0) from public.app_dossier_etiquette_journal")
    jmax = cu.fetchone()[0]
    cn.rollback()
    cn.close()
    return {"ledger": led, "compteur": cpt, "jmax": jmax}


def jouer_pose(base: str, args: str) -> list:
    cn = Local.cnx(base, autocommit=False)
    cu = cn.cursor()
    cu.execute("select * from public.app_poser_etiquettes_dossier(%s)" % args)
    rend = [tuple(r) for r in cu.fetchall()]
    cn.commit()
    cn.close()
    return rend


def journal_neuf(base: str, depuis: int, apres: bool) -> list:
    cn = Local.cnx(base, autocommit=False)
    cu = cn.cursor()
    cu.execute("select evenement, dossier_uuid::text, dossier_numero, autre_uuid::text, app_chaine_id, transactions, "
               "combien, pourquoi%s from public.app_dossier_etiquette_journal where id > %%s order by id" % (
                   ", ancien_numero" if apres else ""), (depuis,))
    rows = [tuple(tuple(x) if isinstance(x, list) else x for x in r) for r in cu.fetchall()]
    cn.rollback()
    cn.close()
    return rows


def normaliser(depart: dict, fin: dict, journal: list) -> tuple[dict, list]:
    """Les etiquettes NEES pendant le rejeu (tirees au hasard) prennent le nom de leur plus petite piece."""
    connues = {u for _c, u, _n in depart["ledger"].values() if u}
    nom = {}
    for a in sorted(fin["ledger"]):
        u = fin["ledger"][a][1]
        if u and u not in connues and u not in nom:
            nom[u] = "NEE:%d" % a
    led = {a: (c, nom.get(u, u), n) for a, (c, u, n) in fin["ledger"].items()}
    jr = []
    for r in journal:
        r = list(r)
        for k in (1, 3):
            if r[k] and r[k] not in connues:
                r[k] = nom.get(r[k], "NEE-HORS-REGISTRE")
        jr.append(tuple(r))
    return led, jr


def comparer(nom: str, dep_a: dict, fin_a: dict, j_a: list, r_a: list, dep_b: dict, fin_b: dict, j_b: list,
             r_b: list) -> dict:
    led_a, ja = normaliser(dep_a, fin_a, j_a)
    led_b, jb = normaliser(dep_b, fin_b, [r[:8] for r in j_b])
    ec_led = sorted(a for a in set(led_a) | set(led_b) if led_a.get(a) != led_b.get(a))
    ec_cpt = sorted(an for an in set(fin_a["compteur"]) | set(fin_b["compteur"])
                    if fin_a["compteur"].get(an) != fin_b["compteur"].get(an))
    # ⚠ 22/11, 21:55 -- LE JOURNAL SE COMPARE EN ENSEMBLE, PAS LIGNE A LIGNE. La pose ecrit ses lignes dans l'ordre de
    #   l'uuid du dossier, et cet uuid est TIRE AU HASARD (gen_random_uuid) : deux passages de LA MEME fonction ecrivent
    #   les memes lignes dans un autre ordre (prouve par le temoin « avant contre avant » de S1). La 1re version comparait
    #   par position et criait 42 / 718 / 50 ecarts -- c'etait l'ordre, pas le patch. On compare donc le MULTI-ENSEMBLE
    #   des lignes, les uuid nes pendant le rejeu nommes par leur plus petite piece ; l'ecart par position reste dit.
    ca, cb = Counter(ja), Counter(jb)
    ec_j = sum((ca - cb).values()) + sum((cb - ca).values())
    ec_j_ordre = sum(1 for x, y in zip(ja, jb) if x != y) + abs(len(ja) - len(jb))
    bouge = sum(1 for a in fin_a["ledger"] if fin_a["ledger"][a] != dep_a["ledger"].get(a))
    return {"etat": nom, "pieces": len(led_a), "pieces_qui_bougent_avant": bouge, "ecarts_pieces": len(ec_led),
            "ex_ecarts": ec_led[:10], "ecarts_compteur": ec_cpt, "journal_avant": len(ja), "journal_apres": len(jb),
            "ecarts_journal": ec_j, "ecarts_journal_par_position": ec_j_ordre,
            "ex_journal": [list(map(str, x)) for x in list((ca - cb).elements())[:3] + list((cb - ca).elements())[:3]],
            "rend_avant": r_a, "rend_apres": r_b, "rend_egal": r_a == r_b}


def verifier_ancien(dep: dict, j_b: list) -> tuple[int, list]:
    """L'ancien numero ecrit par APRES : scission = le numero du dossier coupe, fusion = le numero absorbe."""
    num = {}
    for _a, (_c, u, n) in dep["ledger"].items():
        if u:
            num.setdefault(u, set()).add(n)
    faux = []
    for r in j_b:
        ev, du, _dn, au, _c, _t, _k, _p, anc = r
        attendu = None
        if ev == "scission":
            attendu = min(num.get(du, {None}) - {None}, default=None)
        elif ev == "fusion":
            attendu = min(num.get(au, {None}) - {None}, default=None)
        if anc != attendu:
            faux.append((ev, du, au, anc, attendu))
    return len(j_b), faux


def etape_rejouer(binaires: Path, copie: str | None) -> int:
    import coupe_preuve_interne as K  # noqa: F401
    import protocole_classeur as P
    import protocole_portes as PO
    d = Path(copie) if copie and Path(copie).is_absolute() else (
        CACHE / copie if copie else max((x for x in CACHE.iterdir() if (x / "manifeste.json").exists()),
                                        key=lambda x: x.name))
    man = json.loads((d / "manifeste.json").read_text(encoding="utf-8"))
    dire("LE REJEU DU PATCH SUR UNE COPIE -- copie %s (lue chez Supabase le %s), Postgres local %s" % (
        d.name, man["quand"], binaires))
    # le chainage d'arrivee du protocole (S1) : le rejeu E du dernier passage
    con = P.socle()
    pid = con.execute("select max(id) from passage where image is not null").fetchone()[0]
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    con.close()
    chE, _ = PO.rejeu_en_cache("E", image, P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % pid),
                               {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
    f_nn = P.DOSSIER / "numeros_neufs_passage_20.json"
    prediction = json.loads(f_nn.read_text(encoding="utf-8"))["numero_neuf"] if f_nn.exists() else {}
    I = P.Image(P.IMAGES / image)
    meme_que_l_image = all(I.pieces.get(int(r[0]), {}).get("app_dossier_uuid") == (r[6] or None)
                           for r in csv.reader((d / "ledger.csv").open(encoding="utf-8", newline="")))
    L = Local(binaires)
    rouges, res = [], {"copie": d.name, "etats": []}
    t0 = time.time()
    L.demarrer()
    try:
        cn = L.cnx()
        cu = cn.cursor()
        cu.execute("select version()")
        v_local = cu.fetchone()[0]
        cn.close()
        dire("   Postgres local : %s ; Supabase : %s (collation %s) -- les rangs se trient sur des dates AAAA-MM-JJ et "
             "des numeros : meme ordre en C" % (v_local.split(" on ")[0], man["version"].split(" on ")[0],
                                                man.get("collation")))
        rouges += charger_modele(L, d, man)
        # APRES : la copie + LE FICHIER DU PATCH, tel quel
        base_depuis("modele", "modele_apres")
        jouer_fichier("modele_apres", PATCH)
        cn = L.cnx("modele_apres")
        cu = cn.cursor()
        cu.execute("select md5(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc)), "
                   "(select count(*) from public.app_dossier_etiquette_journal where ancien_numero is not null)")
        m_apres, n_rempl = cu.fetchone()
        cu.execute(REPETITION.read_text(encoding="utf-8"))
        rep = cu.fetchall()
        cn.close()
        non = [r for r in rep if "NON" in " ".join(map(str, r))]
        dire("   LE PATCH, joue tel quel sur la copie : fonction %s ; %d lignes du journal recoivent leur ancien numero ; "
             "REPETITION : %d controles, %d NON" % (m_apres, n_rempl, len(rep), len(non)))
        if non:
            rouges.append("repetition : %s" % non)
        res["patch"] = {"fonction_apres": m_apres, "lignes_remplies": n_rempl, "repetition": [list(map(str, r)) for r in rep]}
        # l'INVERSE, sur une copie de APRES : la fonction revient a 815e956f
        base_depuis("modele_apres", "inverse")
        jouer_fichier("inverse", INVERSE)
        cn = L.cnx("inverse")
        cu = cn.cursor()
        cu.execute("select md5(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc)), exists (select 1 "
                   "from information_schema.columns where table_name = 'app_dossier_etiquette_journal' and column_name "
                   "= 'ancien_numero')")
        m_inv, col = cu.fetchone()
        cn.close()
        ok_inv = m_inv == EMPREINTE_FONCTION and not col
        dire("   L'INVERSE, joue sur une copie du patch : fonction %s, colonne %s -- %s" % (
            m_inv, "encore la" if col else "retiree", "RETOUR EXACT" if ok_inv else "⛔ PAS DE RETOUR EXACT"))
        if not ok_inv:
            rouges.append("inverse")
        res["inverse"] = {"fonction": m_inv, "colonne": col}

        for etat, args in (("S0", "null, false"), ("S1", "null, false"), ("S2", "null, false"),
                           ("S3", "null, true"), ("S4", "25, false")):
            dep, fin, jn, rend = {}, {}, {}, {}
            for cote, modele in (("avant", "modele"), ("apres", "modele_apres")):
                base_depuis(modele, cote)
                preparer(cote, etat, chE)
                dep[cote] = photo(cote, cote == "apres")
                rend[cote] = jouer_pose(cote, args)
                fin[cote] = photo(cote, cote == "apres")
                jn[cote] = journal_neuf(cote, dep[cote]["jmax"], cote == "apres")
            c = comparer(etat, dep["avant"], fin["avant"], jn["avant"], rend["avant"], dep["apres"], fin["apres"],
                         jn["apres"], rend["apres"])
            n_j, faux_anc = verifier_ancien(dep["apres"], jn["apres"])
            c["ancien_numero"] = {"lignes": n_j, "faux": faux_anc[:10], "n_faux": len(faux_anc)}
            if etat == "S0":
                led0 = {int(r[0]): (int(r[5]) if r[5] else None, r[6] or None, r[7] or None)
                        for r in csv.reader((d / "ledger.csv").open(encoding="utf-8", newline=""))}
                c["contre_aujourdhui"] = sum(1 for a, x in fin["apres"]["ledger"].items() if led0.get(a) != x)
            if etat == "S1" and prediction and meme_que_l_image:
                nees = {}
                for a, (_c, u, n) in fin["avant"]["ledger"].items():
                    if u and u not in {x[1] for x in dep["avant"]["ledger"].values()}:
                        nees.setdefault(u, []).append(a)
                comp = [(min(v), fin["avant"]["ledger"][min(v)][2], prediction.get("NEUVE:%d" % min(v)))
                        for v in nees.values()]
                c["contre_la_prediction"] = {"nees": len(comp), "egales": sum(1 for _a, n, p in comp if n == p),
                                             "ex_differentes": [x for x in comp if x[1] != x[2]][:10],
                                             "predites": len(prediction)}
            vert = (c["ecarts_pieces"] == 0 and not c["ecarts_compteur"] and c["ecarts_journal"] == 0 and c["rend_egal"]
                    and c["ancien_numero"]["n_faux"] == 0 and c.get("contre_aujourdhui", 0) == 0)
            if etat == "S3" and c["pieces_qui_bougent_avant"]:
                vert = False
            if "contre_la_prediction" in c and c["contre_la_prediction"]["egales"] != c["contre_la_prediction"]["nees"]:
                vert = False
            if not vert:
                rouges.append(etat)
            res["etats"].append(c)
            dire("   %s (%s) : %d pieces, %d bougent ; AVANT / APRES : %d ecart(s) de piece, %d au compteur, %d au journal "
                 "(%d / %d lignes neuves), rendu %s ; ancien numero %d ligne(s), %d faux%s%s -- %s" % (
                     etat, args, c["pieces"], c["pieces_qui_bougent_avant"], c["ecarts_pieces"],
                     len(c["ecarts_compteur"]), c["ecarts_journal"], c["journal_avant"], c["journal_apres"],
                     "IDENTIQUE" if c["rend_egal"] else "DIFFERENT %s / %s" % (c["rend_avant"], c["rend_apres"]),
                     c["ancien_numero"]["lignes"], c["ancien_numero"]["n_faux"],
                     (" ; contre aujourd'hui : %d ecart(s) sur %d" % (c["contre_aujourdhui"], c["pieces"]))
                     if "contre_aujourdhui" in c else "",
                     (" ; contre la prediction : %d / %d numeros neufs egaux" % (
                         c["contre_la_prediction"]["egales"], c["contre_la_prediction"]["nees"]))
                     if "contre_la_prediction" in c else "", "VERT" if vert else "⛔ ROUGE"))
            dire("      journal : %d ligne(s) differente(s) en ENSEMBLE ; %d par POSITION (l'ordre suit l'uuid tire au hasard)"
                 % (c["ecarts_journal"], c["ecarts_journal_par_position"]))
            if etat == "S1":
                # LE TEMOIN DU HASARD : la fonction d'AUJOURD'HUI contre elle-meme -- l'ordre du journal doit differer
                #   (sinon le choix de comparer en ensemble ne serait pas justifie), et l'ensemble doit etre egal
                base_depuis("modele", "avant2")
                preparer("avant2", etat, chE)
                dep_2 = photo("avant2", False)
                rend_2 = jouer_pose("avant2", args)
                fin_2 = photo("avant2", False)
                jn_2 = journal_neuf("avant2", dep_2["jmax"], False)
                c2 = comparer("S1-avant-contre-avant", dep["avant"], fin["avant"], jn["avant"], rend["avant"], dep_2,
                              fin_2, jn_2 + [], rend_2)
                hasard = c2["ecarts_journal_par_position"] > 0 and c2["ecarts_journal"] == 0 and c2["ecarts_pieces"] == 0
                dire("   TEMOIN DU HASARD (la fonction d'aujourd'hui contre elle-meme) : %d ecart(s) de piece ; journal %d "
                     "en ensemble, %d par position -- %s" % (
                         c2["ecarts_pieces"], c2["ecarts_journal"], c2["ecarts_journal_par_position"],
                         "l'ORDRE du journal est du hasard, l'ENSEMBLE est stable" if hasard else
                         "⛔ le temoin ne dit pas ce qu'on croit"))
                if not hasard:
                    rouges.append("temoin du hasard")
                res["temoin_du_hasard"] = {k: c2[k] for k in ("ecarts_pieces", "ecarts_journal",
                                                              "ecarts_journal_par_position")}
                # LE TEMOIN INVERSE : le patch fausse expres (le rang d'une scission + 1) -- la comparaison doit crier
                base_depuis("modele", "faux")
                jouer_fichier("faux", PATCH, remplacer=FAUSSE)
                preparer("faux", etat, chE)
                dep_f = photo("faux", True)
                rend_f = jouer_pose("faux", args)
                fin_f = photo("faux", True)
                jn_f = journal_neuf("faux", dep_f["jmax"], True)
                cf = comparer("S1-faux", dep["avant"], fin["avant"], jn["avant"], rend["avant"], dep_f, fin_f, jn_f,
                              rend_f)
                crie = cf["ecarts_pieces"] > 0
                dire("   TEMOIN INVERSE (la scission fausse expres : rang + 1) : %d ecart(s) de piece, %d au compteur -- %s"
                     % (cf["ecarts_pieces"], len(cf["ecarts_compteur"]), "LA COMPARAISON CRIE" if crie else
                        "⛔ LA COMPARAISON EST AVEUGLE"))
                if not crie:
                    rouges.append("temoin inverse muet")
                res["temoin_inverse"] = {"ecarts_pieces": cf["ecarts_pieces"], "ecarts_compteur": cf["ecarts_compteur"]}
    finally:
        L.arreter()
    res["rouges"] = rouges
    res["duree_s"] = round(time.time() - t0)
    (d / "rejeu.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    dire("%s -- %d s -> %s" % ("⭐ VERT : la fonction modifiee pose EXACTEMENT ce que pose celle d'aujourd'hui"
                               if not rouges else "⛔ ROUGE : %s" % rouges, res["duree_s"], d / "rejeu.json"))
    return 1 if rouges else 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("etape", choices=("extraire", "rejouer"))
    ap.add_argument("--pg", help="le dossier des binaires du Postgres local (initdb.exe, pg_ctl.exe)")
    ap.add_argument("--copie", help="la copie a rejouer (par defaut : la derniere extraite)")
    a = ap.parse_args()
    if a.etape == "extraire":
        return etape_extraire()
    if not a.pg:
        dire("⛔ rejouer demande --pg <dossier des binaires du Postgres local> -- code 2")
        return 2
    return etape_rejouer(Path(a.pg), a.copie)


if __name__ == "__main__":
    sys.exit(main())
