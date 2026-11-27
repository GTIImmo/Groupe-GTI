"""LA MEMOIRE DES DECISIONS DU PROTOCOLE, EN BASE (27/11).

Son mot du 27/11 : « ce qui m'inquiete le plus : ton socle.sqlite, 159 Mo, est dans un dossier de cache sans aucune
sauvegarde ailleurs -- les 17 copies sont toutes dans le meme dossier. Mets la memoire des decisions en base. »

CE QUI PART EN BASE (chez Supabase, schema public, RLS allumee, illisible par anon et authenticated) :
  - les 4 tables du socle, A L'IDENTIQUE (memes colonnes, memes textes, octet pour octet) :
      app_classeur_protocole_passage  <- passage   (un passage du juge : image, code, version, comptes, note)
      app_classeur_protocole_verdict  <- verdict   (le verdict de chaque ligne a chaque passage, ses pieces, ses preuves)
      app_classeur_protocole_temoin   <- temoin    (les ecarts des temoins ; « rang » = l'ordre d'ecriture du socle)
      app_classeur_protocole_motif    <- motif     (le catalogue des motifs)
  - app_classeur_protocole_fichier : les ENTREES VIVANTES du juge (son verdict en depend : l'empreinte du 82 les nomme)
    et la PHOTO DU SHEET de l'image du passage officiel (sheet.json, gel.json, manifeste.json, t6_photo.json), en octets,
    avec leur md5. ⛔ PAS le registre.sqlite de l'image (96 Mo) : c'est une photo de NOTRE base, a sa decision.

LA PREUVE : chaque table est relue DEPUIS LA BASE et son empreinte (md5 des lignes dans l'ordre de la cle, chaque ligne
ecrite en JSON) doit etre EGALE a celle du socle. Un seul octet different fait echouer le geste (temoin inverse joue a blanc).

LES MODES :
  --a-blanc     tables TEMPORAIRES (create temp table : elles meurent avec la connexion) -> copie, relecture, empreintes ;
                RIEN ne reste en base. Et le temoin inverse : une ligne alteree DOIT faire differer l'empreinte.
  --ecrire      ⛔ A SON ACCORD : les tables doivent exister (le patch supabase/patch_socle_du_protocole_en_base_2026-11-27.sql) ;
                copie les passages ABSENTS de la base (increment) et les fichiers ; relit et compare AVANT le commit.
  --verifier    lecture seule : la base contre le socle, table par table.

USAGE : python -u -X utf8 phase2/checks/socle_du_protocole_en_base_2026-11-27.py --a-blanc
"""
import argparse
import hashlib
import io
import json
import os
import sqlite3
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

#: table du socle -> (table en base, colonnes dans l'ordre, colonnes entieres, cle)
TABLES = {
    "passage": ("app_classeur_protocole_passage",
                ["id", "image", "image_code", "code", "version", "debut", "fin", "lignes", "tranchees", "en_attente",
                 "boucle", "note"], {"id", "lignes", "tranchees", "en_attente", "boucle"}, ["id"]),
    "verdict": ("app_classeur_protocole_verdict",
                ["passage", "id_unique", "num", "biens", "verdict", "etiquette", "pieces", "preuves", "motif",
                 "motif_texte", "epreuve"], {"passage", "num"}, ["passage", "id_unique"]),
    "temoin": ("app_classeur_protocole_temoin",
               ["passage", "rang", "temoin", "id_unique", "attendu", "obtenu", "ecart"], {"passage", "rang", "ecart"},
               ["passage", "rang"]),
    "motif": ("app_classeur_protocole_motif", ["code", "epreuve", "libelle"], set(), ["code"]),
}
DDL = {
    "passage": "id integer primary key, image text not null, image_code text not null, code text not null, "
               "version text not null, debut text not null, fin text, lignes integer, tranchees integer, "
               "en_attente integer, boucle integer, note text",
    "verdict": "passage integer not null, id_unique text not null, num integer, biens text not null, "
               "verdict text not null, etiquette text, pieces text, preuves text, motif text, motif_texte text, "
               "epreuve text not null, primary key (passage, id_unique)",
    "temoin": "passage integer not null, rang integer not null, temoin text not null, id_unique text, attendu text, "
              "obtenu text, ecart integer not null, primary key (passage, rang)",
    "motif": "code text primary key, epreuve text not null, libelle text not null",
}
DDL_FICHIER = ("nom text primary key, origine text not null, octets bigint not null, md5 text not null, "
               "contenu bytea not null")
IMAGE_OFFICIELLE = "2026-11-26_094931"   # l'image du passage officiel 82
# 27/11 au soir : les entrees de CHAQUE passage officiel a partir du 81 (83 rouge, garde comme trace ; 84 vert) -- meme image
FICHIERS = (sorted((f for f in P.DOSSIER.glob("entrees_passage_*.json") if int(f.stem.rsplit("_", 1)[1]) >= 81),
                   key=lambda f: int(f.stem.rsplit("_", 1)[1]))
            + [P.DOSSIER / "mandants_des_biens_2026-11-23.json", P.DOSSIER.parent / "v3_calcul.json"]
            + [P.IMAGES / IMAGE_OFFICIELLE / f for f in ("manifeste.json", "sheet.json", "gel.json", "t6_photo.json")])


def dire(s=""):
    print(s, flush=True)


def connexion_ecriture():
    """La meme connexion que P.pooler(), SANS « set transaction read only ». Les secrets restent dans l'environnement."""
    import psycopg2
    from phase2.sync import push_upgrade_to_supabase as PU
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    return psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                            user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                            connect_timeout=15, sslmode="require")


def lignes_du_socle(so, t, passages=None):
    _nom, cols, _ent, cle = TABLES[t]
    src = [c if c != "rang" else "rowid as rang" for c in cols]
    q = "select %s from %s" % (", ".join(src), t)
    if passages is not None and t != "motif":
        q += " where %s in (%s)" % ("id" if t == "passage" else "passage", ",".join(str(int(p)) for p in passages))
    q += " order by " + ", ".join("rowid" if c == "rang" else c for c in cle)
    return so.execute(q)


def empreinte(rangees):
    h = hashlib.md5()
    n = 0
    for r in rangees:
        h.update((json.dumps(list(r), ensure_ascii=False) + "\n").encode("utf-8"))
        n += 1
    return n, h.hexdigest()


def texte_copy(v):
    if v is None:
        return "\\N"
    s = str(v)
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def copier(cu, so, t, cible, passages=None):
    _nom, cols, _ent, _cle = TABLES[t]
    buf = io.StringIO()
    n = 0
    for r in lignes_du_socle(so, t, passages):
        buf.write("\t".join(texte_copy(v) for v in r) + "\n")
        n += 1
    buf.seek(0)
    cu.copy_expert("copy %s (%s) from stdin with (format text)" % (cible, ", ".join(cols)), buf)
    return n


def relire(cn, t, cible, passages=None):
    _nom, cols, ent, cle = TABLES[t]
    q = "select %s from %s" % (", ".join(cols), cible)
    if passages is not None and t != "motif":
        q += " where %s = any(%%s)" % ("id" if t == "passage" else "passage")
    q += " order by " + ", ".join(c + (" collate \"C\"" if c not in ent else "") for c in cle)
    cur = cn.cursor(name="relire_%s" % t)
    cur.itersize = 20000
    cur.execute(q, (list(passages),) if passages is not None and t != "motif" else None)
    for r in cur:
        yield tuple(r)
    cur.close()


def ordre_socle(so, t, passages=None):
    """Les lignes du socle dans l'ORDRE BINAIRE de la cle (celui de la relecture collate "C")."""
    _nom, cols, ent, cle = TABLES[t]
    rs = list(lignes_du_socle(so, t, passages))
    idx = [cols.index(c) for c in cle]
    rs.sort(key=lambda r: tuple(r[k] if cols[k] in ent else str(r[k]).encode("utf-8") for k in idx))
    return rs


def fichiers():
    out = []
    for f in FICHIERS:
        b = f.read_bytes()
        nom = ("image_%s/%s" % (IMAGE_OFFICIELLE, f.name)) if f.parent.name == IMAGE_OFFICIELLE else f.name
        out.append((nom, str(f), len(b), hashlib.md5(b).hexdigest(), b))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--a-blanc", action="store_true")
    g.add_argument("--ecrire", action="store_true")
    g.add_argument("--verifier", action="store_true")
    a = ap.parse_args()
    so = sqlite3.connect("file:%s?mode=ro" % P.SOCLE.as_posix(), uri=True)
    dire("LE SOCLE %s (%d octets, md5 du fichier %s)" % (P.SOCLE, P.SOCLE.stat().st_size,
                                                       hashlib.md5(P.SOCLE.read_bytes()).hexdigest()[:8]))
    tous = [r[0] for r in so.execute("select id from passage order by id")]
    dire("   passages %d a %d (%d)" % (tous[0], tous[-1], len(tous)))
    attendu = {}
    for t in TABLES:
        attendu[t] = empreinte(ordre_socle(so, t))
        dire("   %-8s %7d lignes, empreinte %s" % (t, *attendu[t]))
    fs = fichiers()
    for nom, _o, n, m, _b in fs:
        dire("   fichier %-40s %9d octets md5 %s" % (nom, n, m[:8]))

    if a.verifier:
        import psycopg2  # noqa: F401
        cn, _cu = P.pooler()
        ok = True
        for t, (cible, *_r) in TABLES.items():
            vu = empreinte(relire(cn, t, "public." + cible))
            dire("   BASE %-8s %7d lignes, empreinte %s -> %s" % (t, *vu, "EGALE" if vu == attendu[t] else "⛔ DIFFERE"))
            ok &= vu == attendu[t]
        cu2 = cn.cursor()
        cu2.execute("select nom, octets, md5 from public.app_classeur_protocole_fichier")
        base = {n: (o, m) for n, o, m in cu2.fetchall()}
        for nom, _o, n, m, _b in fs:
            dire("   BASE fichier %-40s %s" % (nom, "EGAL" if base.get(nom) == (n, m) else "⛔ %s" % (base.get(nom),)))
            ok &= base.get(nom) == (n, m)
        cn.close()
        dire("VERDICT : %s" % ("la base porte le socle A L'IDENTIQUE" if ok else "⛔ ECART"))
        return 0 if ok else 1

    cn = connexion_ecriture()
    cu = cn.cursor()
    if a.a_blanc:
        dire("A BLANC : tables TEMPORAIRES (elles meurent avec la connexion ; rien ne reste en base)")
        for t, (cible, *_r) in TABLES.items():
            cu.execute("create temp table %s (%s) on commit drop" % (cible, DDL[t]))
        cu.execute("create temp table app_classeur_protocole_fichier (%s) on commit drop" % DDL_FICHIER)
        cibles = {t: v[0] for t, v in TABLES.items()}
        passages = None
    else:
        cu.execute("select count(*) from information_schema.tables where table_schema = 'public' and table_name like "
                   "'app_classeur_protocole_%%'")
        if cu.fetchone()[0] != 5:
            raise SystemExit("⛔ les 5 tables n'existent pas : le patch supabase/patch_socle_du_protocole_en_base_2026-11-27.sql "
                             "n'est pas joue -- RIEN n'est ecrit")
        cu.execute("select id from public.app_classeur_protocole_passage")
        deja = {r[0] for r in cu.fetchall()}
        passages = [p for p in tous if p not in deja]
        dire("ECRIRE : %d passages deja en base, %d a copier (%s)" % (len(deja), len(passages),
                                                                    (passages[:3], passages[-3:]) if passages else "-"))
        cibles = {t: "public." + v[0] for t, v in TABLES.items()}
        cu.execute("delete from public.app_classeur_protocole_motif")   # le catalogue : remplace en entier (18 lignes)
    for t in TABLES:
        n = copier(cu, so, t, cibles[t], None if t == "motif" else passages)
        dire("   copie %-8s %7d lignes" % (t, n))
    cible_f = "app_classeur_protocole_fichier" if a.a_blanc else "public.app_classeur_protocole_fichier"
    for nom, o, n, m, b in fs:
        cu.execute("insert into %s (nom, origine, octets, md5, contenu) values (%%s, %%s, %%s, %%s, %%s) "
                   "on conflict (nom) do update set origine = excluded.origine, octets = excluded.octets, "
                   "md5 = excluded.md5, contenu = excluded.contenu" % cible_f, (nom, o, n, m, b))
    # LA PREUVE, dans la meme transaction, AVANT le commit
    ok = True
    for t in TABLES:
        vu = empreinte(relire(cn, t, cibles[t]))
        dire("   relu  %-8s %7d lignes, empreinte %s -> %s" % (t, *vu, "EGALE" if vu == attendu[t] else "⛔ DIFFERE"))
        ok &= vu == attendu[t]
    cu.execute("select nom, octets, md5, md5(contenu) from %s" % cible_f)
    for nom, n, m, m2 in cu.fetchall():
        bon = (m == m2) and any(x[0] == nom and x[2] == n and x[3] == m for x in fs)
        dire("   relu  fichier %-40s %s" % (nom, "EGAL" if bon else "⛔ DIFFERE"))
        ok &= bon
    if a.a_blanc:
        tot = 0
        for c in list(cibles.values()) + [cible_f]:
            cu.execute("select pg_total_relation_size(%s::regclass)", (c,))
            n = cu.fetchone()[0]
            tot += n
            dire("   place %-36s %8.1f Mo" % (c, n / 1e6))
        dire("   PLACE EN BASE, MESUREE : %.1f Mo" % (tot / 1e6))
        # LE TEMOIN INVERSE : une seule lettre changee dans un seul verdict doit faire differer l'empreinte
        cu.execute("update %s set epreuve = epreuve || '.' where (passage, id_unique) = (select passage, id_unique "
                   "from %s order by passage, id_unique limit 1)" % (cibles["verdict"], cibles["verdict"]))
        vu = empreinte(relire(cn, "verdict", cibles["verdict"]))
        mord = vu != attendu["verdict"]
        dire("   TEMOIN INVERSE (une lettre ajoutee a un verdict) : empreinte %s -> %s" % (
            vu[1][:8], "elle DIFFERE, le controle mord" if mord else "⛔ ELLE NE BOUGE PAS"))
        ok &= mord
        cn.rollback()
        cn.close()
        dire("A BLANC %s ; rollback fait, connexion fermee : rien ne reste" % ("VERT" if ok else "⛔ ROUGE"))
        return 0 if ok else 1
    if not ok:
        cn.rollback()
        cn.close()
        dire("⛔ ECART : rollback, RIEN n'est ecrit")
        return 1
    cn.commit()
    cn.close()
    dire("ECRIT : la base porte le socle a l'identique (relu avant le commit)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
