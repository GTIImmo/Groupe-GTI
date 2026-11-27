#!/usr/bin/env python3
"""LA SAUVEGARDE DATEE QUI SE RELIT -- chantier classeur, ㉑bis, 22/11/2026 (soir).

Son mot (reponses au rapport 21 bis, § 2) : « LA SAUVEGARDE DATEE QUI SE RELIT. Avant la premiere ecriture, pas apres.
  Et je ne veux pas qu'on verifie qu'elle EXISTE : je veux qu'on la RELISE POUR DE VRAI et qu'on prouve qu'elle redonne
  les 216 etiquettes. Une sauvegarde qu'on n'a jamais relue n'est pas une sauvegarde, c'est un espoir. »

⛔ LECTURE SEULE de la base : Supabase par le pooler, dans UNE transaction « repeatable read, read only » (une photo
   coherente) ; le registre local en mode=ro ; le Sheet par un GET. Elle n'ECRIT que dans son propre dossier, HORS du
   depot : C:\\Hektor\\Backups\\classeur\\<date>\\ (la convention du projet, hors git).

CE QU'ELLE EMPORTE (tout ce que l'ecriture du protocole peut toucher, et ce qui en temoigne) :
  . app_affaire_ledger : la piece, sa chaine, son etiquette, son numero (31 368 lignes) ;
  . app_classeur_lien (le gel) EN ENTIER -- ⚠ c'est l'une des deux tables du cloud SANS AUCUNE copie locale (audit 8d) ;
  . app_dossier_numero_compteur, app_dossier_etiquette_journal (temoins : un numero donne ne se redonne jamais) ;
  . app_classeur_avis, SANS ecrit_par (une identite ne s'ecrit pas sur un document) ;
  . le registre LOCAL (phase2.sqlite, les memes 4 colonnes) ; le Sheet entier (dont la colonne A) ; les deux fichiers
    de decisions (detachements_manuels.csv, rattachements_manuels.csv), copies a l'octet.

LES TROIS PREUVES, chacune dans un processus a part (jamais la memoire de celui qui a ecrit) :
  prendre                 la photo ; pour chaque table, l'EMPREINTE CALCULEE PAR POSTGRES dans la meme transaction
  relire  <dossier>       relit les fichiers DEPUIS LE DISQUE : l'empreinte de chaque fichier, puis l'empreinte du
                          CONTENU recalculee ligne par ligne -- elle doit etre celle que Postgres a donnee. Puis elle dit
                          ce qui a bouge dans la base depuis.
  epreuve <dossier>       ⭐ LA PREUVE DES 216 : sur une COPIE (sqlite en memoire), l'etat d'arrivee du protocole (rejeu E +
                          pose de nuit), puis le fichier retire (rejeu A + pose de nuit) -> les etiquettes qui ne
                          reviennent pas ; puis la RESTAURATION fabriquee DEPUIS LE FICHIER relu -> la copie doit redonner
                          l'empreinte de Postgres au moment de la sauvegarde, et chacune des 216.
  restauration <dossier>  fabrique (sans le jouer) le patch qui remettrait les etiquettes de la sauvegarde dans la base
                          (chaque dossier restaure laisse sa ligne au journal : l ancien et le neuf)
                          d'AUJOURD'HUI -- seulement les lignes qui different, chacune gardee par sa valeur du moment.
⚠ LE COMPTEUR NE SE REMET JAMAIS EN ARRIERE : un numero donne une fois ne se redonne pas (sinon deux dossiers
  porteraient le meme numero a deux dates). La sauvegarde le garde en TEMOIN, la restauration n'y touche pas.
USAGE : python -u phase2/checks/sauvegarde_datee_classeur.py prendre [--note TEXTE]
        python -u phase2/checks/sauvegarde_datee_classeur.py relire|epreuve|restauration [<dossier>] [--passage P]
CODES : 0 vert . 1 un rouge (nomme) . 2 pas pu lire
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import protocole_classeur as P  # noqa: E402

SAUVEGARDES = Path(r"C:\Hektor\Backups\classeur")
SEP, NUL = chr(31), "∅"
TABLES = {  # nom du fichier -> (table, colonnes ECARTEES, cle d'identite d'une ligne)
    "registre": ("public.app_affaire_ledger", None, ["app_affaire_id"]),
    "gel": ("public.app_classeur_lien", set(), None),
    "compteur": ("public.app_dossier_numero_compteur", set(), ["annee"]),
    "journal": ("public.app_dossier_etiquette_journal", set(), ["id"]),
    "avis": ("public.app_classeur_avis", {"ecrit_par"}, ["id_unique"]),
}
COLONNES_REGISTRE = ["app_affaire_id", "app_chaine_id", "app_dossier_uuid", "app_dossier_numero"]
FICHIERS_DECISIONS = [P.RACINE / "phase2" / "sync" / "detachements_manuels.csv",
                      P.RACINE / "phase2" / "sync" / "rattachements_manuels.csv"]


def dire(s: str = "") -> None:
    print(s, flush=True)


def md5_octets(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def empreinte(lignes: list) -> str:
    """LA MEME FORMULE QUE POSTGRES : chaque champ en texte (NULL = ∅), joints par chr(31), lignes triees (ordre « C »
    = ordre des points de code), jointes par un saut de ligne, md5."""
    rs = sorted(SEP.join(NUL if f is None else f for f in r) for r in lignes)
    return md5_octets("\n".join(rs).encode("utf-8"))


def connexion():
    import os
    import urllib.parse
    import psycopg2 as pg
    from phase2.sync import push_upgrade_to_supabase as PU
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    cn = pg.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                    user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                    connect_timeout=15, sslmode="require")
    cn.set_session(isolation_level="REPEATABLE READ", readonly=True)
    return cn, cn.cursor()


def expressions(cu, table: str, ecartees: set | None) -> tuple[list, list]:
    schema, nom = table.split(".")
    cu.execute("select column_name, data_type from information_schema.columns where table_schema=%s and table_name=%s "
               "order by ordinal_position", (schema, nom))
    cols = cu.fetchall()
    if ecartees is None:                                   # le registre : les 4 colonnes de l'etiquette, et rien d'autre
        cols = [c for c in cols if c[0] in COLONNES_REGISTRE]
        cols.sort(key=lambda c: COLONNES_REGISTRE.index(c[0]))
    else:
        cols = [c for c in cols if c[0] not in ecartees]
    ex = []
    for c, t in cols:
        if t.startswith("timestamp"):
            ex.append("to_char(%s at time zone 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US')" % c)
        else:
            ex.append("%s::text" % c)
    return [c for c, _t in cols], ex


def lire_table(cu, table: str, ecartees: set | None) -> dict:
    noms, ex = expressions(cu, table, ecartees)
    cu.execute("select %s from %s" % (", ".join(ex), table))
    lignes = [list(r) for r in cu.fetchall()]
    rangee = " || chr(31) || ".join("coalesce(%s, '%s')" % (e, NUL) for e in ex)
    cu.execute("select count(*), md5(coalesce(string_agg(r, E'\\n' order by r collate \"C\"), '')) from (select %s as r "
               "from %s) x" % (rangee, table))
    n, emp = cu.fetchone()
    return {"table": table, "colonnes": noms, "n": n, "empreinte_postgres": emp, "lignes": lignes}


def lire_registre_local() -> list:
    con = sqlite3.connect("file:%s?mode=ro" % P.BASE.as_posix(), uri=True)
    rows = [[None if v is None else str(v) for v in r] for r in con.execute(
        "select %s from app_affaire_ledger" % ", ".join(COLONNES_REGISTRE))]
    con.close()
    return rows


def ecrire_json(d: Path, nom: str, obj) -> str:
    b = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (d / nom).write_bytes(b)
    return md5_octets(b)


# ═══════════════════════════════════════ PRENDRE ═══════════════════════════════════════════════════════════════════
def prendre(note: str) -> int:
    t0 = datetime.now()
    d = SAUVEGARDES / t0.strftime("%Y-%m-%d_%H%M%S")
    d.mkdir(parents=True, exist_ok=False)
    dire("SAUVEGARDE DATEE -- %s (%s)" % (d, note or "sans note"))
    man = {"fait_le": t0.isoformat(timespec="seconds"), "note": note, "outil_md5": md5_octets(
        Path(__file__).read_bytes().replace(b"\r\n", b"\n")), "base": {}, "fichiers": {}}
    try:
        cn, cu = connexion()
        for f, (table, ecartees, _cle) in TABLES.items():
            t = lire_table(cu, table, ecartees)
            if len(t["lignes"]) != t["n"]:
                dire("⛔ %s : %d lignes lues, %d comptees par Postgres -- code 2" % (table, len(t["lignes"]), t["n"]))
                return 2
            man["base"][f] = {k: t[k] for k in ("table", "colonnes", "n", "empreinte_postgres")}
            man["fichiers"]["supabase_%s.json" % f] = ecrire_json(d, "supabase_%s.json" % f, t)
            dire("   %-9s %-36s %7d lignes . empreinte Postgres %s" % (f, table, t["n"], t["empreinte_postgres"]))
        cu.execute("select now()::text")
        man["photo_postgres_a"] = cu.fetchone()[0]
        cn.rollback()
        cn.close()
    except Exception as e:  # noqa: BLE001
        dire("⛔ Supabase n'a pas pu etre lue (%s) -- code 2" % str(e).splitlines()[0][:200])
        return 2
    loc = lire_registre_local()
    man["local_registre"] = {"n": len(loc), "empreinte": empreinte(loc)}
    man["fichiers"]["local_registre.json"] = ecrire_json(d, "local_registre.json",
                                                         {"colonnes": COLONNES_REGISTRE, "lignes": loc})
    dire("   registre LOCAL (phase2.sqlite, mode=ro) : %d lignes . empreinte %s" % (len(loc), man["local_registre"][
        "empreinte"]))
    import apparier_classeur as ac
    ac.MORCEAUX_DE_NOM = True
    ac.load_env_file(P.RACINE / ".env")
    try:
        entete, lignes = ac.lire_classeur()
    except Exception as e:  # noqa: BLE001
        dire("⛔ le Sheet n'a pas pu etre lu (%s) -- code 2" % str(e).splitlines()[0][:200])
        return 2
    sh = {"entete": entete, "lignes": [[num, [("" if x is None else str(x)) for x in l]] for num, l in lignes]}
    col_a = [[num, r[0] if r else ""] for num, r in sh["lignes"]]
    man["sheet"] = {"lignes": len(sh["lignes"]), "colonne_a": entete[0], "colonne_a_remplie": sum(1 for _n, v in col_a
                                                                                                    if v.strip()),
                    "empreinte_colonne_a": empreinte([[str(n), v] for n, v in col_a]),
                    "empreinte": md5_octets(json.dumps(sh["lignes"], ensure_ascii=False).encode("utf-8"))}
    man["fichiers"]["sheet.json"] = ecrire_json(d, "sheet.json", sh)
    dire("   Sheet : %d lignes ; colonne A « %s » remplie sur %d" % (len(sh["lignes"]), entete[0],
                                                                   man["sheet"]["colonne_a_remplie"]))
    (d / "fichiers").mkdir()
    for f in FICHIERS_DECISIONS:
        b = f.read_bytes()
        (d / "fichiers" / f.name).write_bytes(b)
        man["fichiers"]["fichiers/%s" % f.name] = md5_octets(b)
        dire("   fichier %s : %d octets . md5 %s" % (f.name, len(b), md5_octets(b)))
    (d / "manifeste.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    dire("SAUVEGARDE PRISE en %.0f s. ⚠ Elle n'est pas encore une sauvegarde : il faut la RELIRE --" % (
        (datetime.now() - t0).total_seconds()))
    dire("   python -u phase2/checks/sauvegarde_datee_classeur.py relire %s" % d.name)
    return 0


def dossier_choisi(nom: str | None) -> Path:
    if nom:
        p = Path(nom)
        return p if p.is_absolute() else SAUVEGARDES / nom
    ds = sorted(p for p in SAUVEGARDES.iterdir() if (p / "manifeste.json").exists()) if SAUVEGARDES.exists() else []
    if not ds:
        raise SystemExit("⛔ aucune sauvegarde -- lancer d'abord : prendre")
    return ds[-1]


def charger(d: Path) -> tuple[dict, dict]:
    """Relit le dossier DEPUIS LE DISQUE et verifie l'empreinte de chaque fichier. Rend (manifeste, ecarts)."""
    man = json.loads((d / "manifeste.json").read_text(encoding="utf-8"))
    ecarts = {f: "absent" for f in man["fichiers"] if not (d / f).exists()}
    for f, e in man["fichiers"].items():
        if f not in ecarts and md5_octets((d / f).read_bytes()) != e:
            ecarts[f] = "empreinte changee"
    return man, ecarts


# ═══════════════════════════════════════ RELIRE ════════════════════════════════════════════════════════════════════
def relire(d: Path) -> int:
    dire("RELIRE LA SAUVEGARDE %s -- depuis le disque, dans un processus neuf" % d)
    man, ecarts = charger(d)
    dire("   1. les %d fichiers : %s" % (len(man["fichiers"]), "tous a leur empreinte" if not ecarts else
                                         "⛔ %s" % ecarts))
    rouges = ["fichier %s %s" % kv for kv in ecarts.items()]
    for f, m in man["base"].items():
        t = json.loads((d / ("supabase_%s.json" % f)).read_text(encoding="utf-8"))
        e = empreinte(t["lignes"])
        ok = e == m["empreinte_postgres"] and len(t["lignes"]) == m["n"]
        dire("   2. %-9s %7d lignes relues . empreinte recalculee %s %s celle de Postgres" % (
            f, len(t["lignes"]), e, "=" if ok else "⛔ DIFFERENTE DE"))
        if not ok:
            rouges.append("contenu %s" % f)
    loc = json.loads((d / "local_registre.json").read_text(encoding="utf-8"))
    ok = empreinte(loc["lignes"]) == man["local_registre"]["empreinte"]
    reg = json.loads((d / "supabase_registre.json").read_text(encoding="utf-8"))
    pareil = len({tuple(r) for r in loc["lignes"]} & {tuple(r) for r in reg["lignes"]})
    dire("   3. registre LOCAL : %d lignes, empreinte %s ; identiques a Supabase, ligne pour ligne : %d sur %d" % (
        len(loc["lignes"]), "retrouvee" if ok else "⛔ DIFFERENTE", pareil, len(reg["lignes"])))
    if not ok:
        rouges.append("registre local")
    sh = json.loads((d / "sheet.json").read_text(encoding="utf-8"))
    ok = empreinte([[str(n), (r[0] if r else "")] for n, r in sh["lignes"]]) == man["sheet"]["empreinte_colonne_a"]
    dire("   4. Sheet : %d lignes, colonne A %s (remplie sur %d)" % (len(sh["lignes"]), "retrouvee" if ok else
                                                                     "⛔ DIFFERENTE", man["sheet"]["colonne_a_remplie"]))
    if not ok:
        rouges.append("Sheet")
    # 5. la base d'aujourd'hui contre la sauvegarde
    try:
        cn, cu = connexion()
        bouge = {}
        for f, (table, ecartees, cle) in TABLES.items():
            t = lire_table(cu, table, ecartees)
            if t["empreinte_postgres"] != man["base"][f]["empreinte_postgres"]:
                avant = {SEP.join(NUL if x is None else x for x in r) for r in json.loads(
                    (d / ("supabase_%s.json" % f)).read_text(encoding="utf-8"))["lignes"]}
                apres = {SEP.join(NUL if x is None else x for x in r) for r in t["lignes"]}
                bouge[f] = "%d ligne(s) disparue(s) ou changee(s), %d nouvelle(s) ou changee(s)" % (
                    len(avant - apres), len(apres - avant))
        cn.rollback()
        cn.close()
        dire("   5. la base AUJOURD'HUI contre la sauvegarde : %s" % (
            "RIEN n'a bouge" if not bouge else " ; ".join("%s : %s" % kv for kv in bouge.items())))
    except Exception as e:  # noqa: BLE001
        dire("   5. ⚠ la base d'aujourd'hui n'a pas pu etre lue (%s)" % str(e).splitlines()[0][:160])
    dire("VERDICT : %s" % ("LA SAUVEGARDE SE RELIT -- chaque fichier et chaque contenu redonnent l'empreinte du moment"
                           if not rouges else "⛔ %d ROUGE(S) : %s" % (len(rouges), " | ".join(rouges))))
    return 0 if not rouges else 1


# ═══════════════════════════════════════ LA RESTAURATION ═══════════════════════════════════════════════════════════
def instructions(sauvee: dict, maintenant: dict) -> list[tuple]:
    """Les lignes a remettre : (id, uuid et numero d'AUJOURD'HUI, uuid et numero SAUVES). La chaine ne se restaure pas
    (le chainage la recalcule chaque nuit) ; elle se verifie."""
    out = []
    for a, (_c, u, n) in sauvee.items():
        _c2, u2, n2 = maintenant.get(a, (None, None, None))
        if (u2, n2) != (u, n):
            out.append((a, u2, n2, u, n))
    return out


def sql_portable(x: tuple) -> str:
    """UNE instruction, la meme pour Postgres et pour l'epreuve sur sqlite : elle ne touche la ligne QUE si elle porte
    encore la valeur du moment (sinon quelqu'un est passe entre deux, et on ne l'ecrase pas a l'aveugle)."""
    a, u_now, n_now, u, n = x

    def lit(v):
        return "null" if v is None else "'%s'" % str(v).replace("'", "''")
    return ("update app_affaire_ledger set app_dossier_uuid = %s, app_dossier_numero = %s where app_affaire_id = %d and "
            "coalesce(cast(app_dossier_uuid as text), '') = '%s' and coalesce(app_dossier_numero, '') = '%s';"
            % (lit(u), lit(n), a, u_now or "", n_now or ""))


def sql_journal(ins: list, nom: str) -> list[str]:
    """LA LIGNE AU JOURNAL (son mot : « chaque changement doit y laisser sa ligne, avec l'ancien et le neuf ») : une
    par dossier restaure et par numero quitte. ⚠ Elle demande le patch du journal (colonne ancien_numero, evenement
    « restauration ») : supabase/patch_journal_ancien_numero_2026-11-22.sql."""
    from collections import defaultdict
    g = defaultdict(list)
    for a, _u_now, n_now, u, n in ins:
        if u is not None:
            g[(u, n, n_now)].append(a)

    def lit(v):
        return "null" if v is None else "'%s'" % str(v).replace("'", "''")
    return ["insert into app_dossier_etiquette_journal (evenement, dossier_uuid, dossier_numero, ancien_numero, "
            "transactions, combien, pourquoi) values ('restauration', %s, %s, %s, '{%s}', %d, %s);"
            % (lit(u), lit(n), lit(n_now), ",".join(map(str, sorted(ids))), len(ids),
               lit("etiquette restauree depuis la sauvegarde datee %s" % nom))
            for (u, n, n_now), ids in sorted(g.items(), key=lambda kv: min(kv[1]))]


def registre_de(t: dict) -> dict:
    return {int(r[0]): (None if r[1] is None else int(r[1]), r[2], r[3]) for r in t["lignes"]}


def epreuve(d: Path, pid: int) -> int:
    import coupe_preuve_interne as K
    import protocole_portes as PO
    dire("L'EPREUVE DES 216 -- sauvegarde %s, protocole passage %d -- TOUT SUR UNE COPIE" % (d.name, pid))
    man, ecarts = charger(d)
    if ecarts:
        dire("⛔ la sauvegarde ne se relit pas (%s) -- code 1" % ecarts)
        return 1
    t = json.loads((d / "supabase_registre.json").read_text(encoding="utf-8"))
    if empreinte(t["lignes"]) != man["base"]["registre"]["empreinte_postgres"]:
        dire("⛔ le registre sauve ne redonne pas l'empreinte de Postgres -- code 1")
        return 1
    avant = registre_de(t)
    con = P.socle()
    image = con.execute("select image from passage where id=?", (pid,)).fetchone()[0]
    con.close()
    I = P.Image(P.IMAGES / image)
    meme = sum(1 for a, x in avant.items() if a in I.pieces and (I.pieces[a]["app_chaine_id"], I.pieces[a][
        "app_dossier_uuid"], I.pieces[a]["app_dossier_numero"]) == x)
    dire("   0. la sauvegarde (relue du disque) contre l'image %s du protocole : %d pieces identiques sur %d" % (
        image, meme, len(avant)))
    lab0 = {a: x[1] for a, x in avant.items()}
    num_de = {x[1]: x[2] for x in avant.values() if x[1]}
    NN = json.loads((P.DOSSIER / ("numeros_neufs_passage_%d.json" % pid)).read_text(encoding="utf-8"))["numero_neuf"]
    chA, _ = PO.rejeu_en_cache("A", image, PO.FICHIER_DET_PROD, PO.ETEINTS, False)
    chE, _ = PO.rejeu_en_cache("E", image, P.DOSSIER / ("brouillon_detachements_protocole_passage_%d.csv" % pid),
                               {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)

    def numero(l_):
        return num_de.get(l_) or NN.get(l_) or ("NEUF(%s)" % l_ if l_ else None)
    labE = K.pose_de_nuit(lab0, chE)
    apres = {a: (chE[a], ("u-" + labE[a]) if str(labE[a]).startswith("NEUVE") else labE[a], numero(labE[a]))
             for a in avant}
    labU = K.pose_de_nuit(labE, chA)
    defait = {a: (chA[a], ("u-" + labU[a]) if str(labU[a]).startswith("NEUVE") else labU[a], numero(labU[a]))
              for a in avant}
    change_E = sum(1 for a in avant if apres[a][1:] != avant[a][1:])
    ne_revient_pas = sorted(a for a in avant if defait[a][1:] != avant[a][1:])
    ch_ok = sum(1 for a in avant if defait[a][0] == avant[a][0])
    dire("   1. l'ARRIVEE du protocole (rejeu E + pose de nuit) : %d etiquettes changent" % change_E)
    dire("   2. DEFAIRE sans sauvegarde (le fichier retire : rejeu A + pose de nuit) : les dossiers reviennent pour %d "
         "pieces sur %d ; ⛔ %d etiquettes NE REVIENNENT PAS, sur %d dossiers" % (
             ch_ok, len(avant), len(ne_revient_pas), len({avant[a][1] for a in ne_revient_pas})))
    # 3. la copie, dans l'etat defait ; la restauration fabriquee DEPUIS LE FICHIER relu ; jouee sur la copie
    m = sqlite3.connect(":memory:")
    m.execute("create table app_affaire_ledger (app_affaire_id integer primary key, app_chaine_id integer, "
              "app_dossier_uuid text, app_dossier_numero text)")
    m.executemany("insert into app_affaire_ledger values (?, ?, ?, ?)", [(a,) + defait[a] for a in sorted(defait)])
    m.execute("create table app_dossier_etiquette_journal (id integer primary key, evenement text not null check "
              "(evenement in ('pose', 'propagation', 'fusion', 'scission', 'restauration')), dossier_uuid text not null, "
              "dossier_numero text, ancien_numero text, transactions text, combien integer, pourquoi text)")
    ins = instructions(avant, defait)
    touchees = 0
    for x in ins:
        touchees += m.execute(sql_portable(x)).rowcount
    jl = sql_journal(ins, d.name)
    for q_ in jl:
        m.execute(q_)
    m.commit()
    j_n, j_comb, j_egal = m.execute("select count(*), coalesce(sum(combien), 0), coalesce(sum(ancien_numero = "
                                    "dossier_numero), 0) from app_dossier_etiquette_journal").fetchone()
    rest = [[str(a), None if c is None else str(c), u, n] for a, c, u, n in m.execute("select * from app_affaire_ledger")]
    e_rest = empreinte(rest)
    rest_d = {int(r[0]): (r[2], r[3]) for r in rest}
    revenues = sum(1 for a in ne_revient_pas if rest_d[a] == avant[a][1:])
    ok = (e_rest == man["base"]["registre"]["empreinte_postgres"] and revenues == len(ne_revient_pas)
          and j_comb == len(ins) and not j_egal)
    dire("   3. LA RESTAURATION, fabriquee depuis le fichier relu : %d instruction(s), %d ligne(s) touchee(s) sur la "
         "copie ; AU JOURNAL : %d ligne(s) « restauration » pour %d piece(s), ancien = neuf %d fois" % (
             len(ins), touchees, j_n, j_comb, j_egal))
    dire("   4. ⭐ LA COPIE RESTAUREE : empreinte %s %s celle de Postgres au moment de la sauvegarde ; les %d qui ne "
         "revenaient pas : %d revenues" % (e_rest, "=" if e_rest == man["base"]["registre"]["empreinte_postgres"] else
                                            "⛔ DIFFERENTE DE", len(ne_revient_pas), revenues))
    sortie = P.NOTICE / ("SAUVEGARDE_EPREUVE_LES_%d_ETIQUETTES_%s.csv" % (len(ne_revient_pas), d.name))
    import csv
    with sortie.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["piece", "numero_dans_la_sauvegarde", "numero_a_l_arrivee_du_protocole", "numero_si_on_defait_SANS",
                    "numero_apres_restauration", "revenu"])
        for a in ne_revient_pas:
            w.writerow([a, avant[a][2], apres[a][2], defait[a][2], rest_d[a][1], "OUI" if rest_d[a] == avant[a][1:]
                        else "NON"])
    dire("-> %s" % sortie)
    for a in ne_revient_pas[:4]:
        dire("   ex. piece %d : %s -> a l'arrivee %s -> defait sans sauvegarde %s -> restaure %s" % (
            a, avant[a][2], apres[a][2], defait[a][2], avant[a][2]))
    dire("VERDICT : %s" % ("LA SAUVEGARDE REDONNE LES %d ETIQUETTES, et la copie entiere retrouve l'empreinte du moment"
                           % len(ne_revient_pas) if ok else "⛔ ELLE NE LES REDONNE PAS"))
    return 0 if ok else 1


def restauration(d: Path) -> int:
    dire("LA RESTAURATION -- sauvegarde %s contre la base d'AUJOURD'HUI (lecture seule) ; rien n'est joue" % d.name)
    man, ecarts = charger(d)
    if ecarts:
        dire("⛔ la sauvegarde ne se relit pas (%s) -- code 1" % ecarts)
        return 1
    avant = registre_de(json.loads((d / "supabase_registre.json").read_text(encoding="utf-8")))
    cn, cu = connexion()
    maintenant = registre_de(lire_table(cu, "public.app_affaire_ledger", None))
    cn.rollback()
    cn.close()
    ins = instructions(avant, maintenant)
    nouvelles = sorted(set(maintenant) - set(avant))
    dire("   %d piece(s) dont l'etiquette differe de la sauvegarde ; %d piece(s) nees depuis (non touchees)" % (
        len(ins), len(nouvelles)))
    if not ins:
        dire("VERDICT : RIEN A RESTAURER aujourd'hui -- aucun patch fabrique")
        return 0
    f = P.RACINE / "supabase" / ("restaurer_etiquettes_depuis_sauvegarde_%s.sql" % d.name)
    corps = "\n".join([sql_portable(x) for x in ins] + sql_journal(ins, d.name))
    garde = ("do $garde$ begin if not exists (select 1 from information_schema.columns where table_schema = 'public' "
             "and table_name = 'app_dossier_etiquette_journal' and column_name = 'ancien_numero') then raise exception "
             "'le patch du journal (ancien_numero, restauration) n''est pas pose -- restauration ARRETEE'; end if; end "
             "$garde$;")
    f.write_bytes(("-- RESTAURER LES ETIQUETTES DE LA SAUVEGARDE %s -- fabrique par sauvegarde_datee_classeur.py\n"
                   "-- %d ligne(s). Chaque instruction ne touche sa ligne QUE si elle porte encore la valeur lue le %s,\n"
                   "-- et chaque dossier restaure laisse sa ligne au journal (l'ancien et le neuf).\n"
                   "-- ⛔ AVANT : retirer du fichier les lignes du protocole (sinon la nuit recoupe). Le compteur ne se\n"
                   "--   remet PAS en arriere.\nbegin;\n%s\n%s\ncommit;\n"
                   % (d.name, len(ins), datetime.now().isoformat(timespec="seconds"), garde, corps)).encode("utf-8"))
    dire("-> %s (NON JOUE)" % f)
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("etape", choices=["prendre", "relire", "epreuve", "restauration"])
    ap.add_argument("dossier", nargs="?")
    ap.add_argument("--note", default="")
    ap.add_argument("--passage", type=int, default=20)
    a = ap.parse_args()
    if a.etape == "prendre":
        return prendre(a.note)
    d = dossier_choisi(a.dossier)
    return {"relire": lambda: relire(d), "epreuve": lambda: epreuve(d, a.passage),
            "restauration": lambda: restauration(d)}[a.etape]()


if __name__ == "__main__":
    sys.exit(main())
