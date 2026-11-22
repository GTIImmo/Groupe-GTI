#!/usr/bin/env python
"""LA REPETITION DE LA MISE DE COTE DES 3 CICATRICES, SUR UNE COPIE -- chantier classeur, 22/11/2026 soir.

Le patch n'est pas une fonction de nuit, mais il ECRIT en production : on le joue d'abord sur une copie, tel qu'il sera
colle (son mot : « je refuse que la NUIT soit son premier essai » -- le patron est le meme).

  1. EXTRAIRE, en LECTURE SEULE chez Supabase : les colonnes exactes du registre et des notes (leurs types), les 190
     copies, les 3 jumelles, les notes des copies ; la fonction de la vraie date et sa table des dates convenues
     (la copie du rejeu du journal, deja relue identique a Supabase) ;
  2. sur le Postgres LOCAL (localhost:54329, arrete a la fin) :
       A le PATCH tel quel -> il doit passer ; sa REPETITION -> 7 OUI ;
       B l'INVERSE tel quel -> le registre et les notes doivent revenir A L'EMPREINTE D'AVANT ;
       C le TEMOIN INVERSE : une copie modifiee (son numero) -> le patch doit REFUSER, rien d'ecrit ;
       D le patch rejoue apres l'inverse -> il doit REFUSER (« ne se rejoue pas »).
⚠ Le declencheur des parties (app_affaire_partie_suivre) n'existe pas sur la copie : les copies n'ont ni acquereurs ni
  mandants, il n'aurait rien a faire -- c'est dit, pas cache.
USAGE : python -u phase2/checks/repeter_mise_de_cote_cicatrices_sur_copie.py --pg <dossier des binaires>
CODES : 0 vert . 1 un rouge . 2 pas pu
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rejeu_patch_journal_sur_copie as R  # noqa: E402

PATCH = RACINE / "supabase" / "patch_mise_de_cote_cicatrices_famille1_2026-11-22.sql"
INVERSE = RACINE / "supabase" / "patch_mise_de_cote_cicatrices_famille1_2026-11-22_INVERSE.sql"
REPETITION = RACINE / "supabase" / "patch_mise_de_cote_cicatrices_famille1_2026-11-22_REPETITION.sql"
TABLES = ("app_affaire_ledger", "app_affaire_note")
COPIE_DU_REJEU = R.CACHE / "2026-11-22_201242"


def dire(s: str = "") -> None:
    print(s, flush=True)


def extraire() -> dict:
    import sauvegarde_datee_classeur as S
    cn, cu = S.connexion()
    out = {"ddl": {}, "csv": {}}
    try:
        for t in TABLES:
            cu.execute("select a.attname, format_type(a.atttypid, a.atttypmod) from pg_attribute a "
                       "where a.attrelid = ('public.' || %s)::regclass and a.attnum > 0 and not a.attisdropped "
                       "order by a.attnum", (t,))
            out["ddl"][t] = cu.fetchall()
        sel = {"app_affaire_ledger": "select * from public.app_affaire_ledger where transaction_origine = 'classeur' "
                                     "or app_affaire_id in (5055, 1876, 11958)",
               "app_affaire_note": "select * from public.app_affaire_note where app_affaire_id in (select app_affaire_id "
                                   "from public.app_affaire_ledger where transaction_origine = 'classeur' or "
                                   "app_affaire_id in (5055, 1876, 11958))"}
        for t in TABLES:
            buf = io.StringIO()
            cu.copy_expert("copy (%s) to stdout with (format csv)" % sel[t], buf)
            out["csv"][t] = buf.getvalue()
        cn.rollback()
    finally:
        cn.close()
    return out


def empreinte(cu, t: str) -> tuple:
    cu.execute("select count(*), md5(coalesce(string_agg(x, E'\\n' order by x collate \"C\"), '')) from "
               "(select t::text as x from public.%s t) s" % t)
    return tuple(cu.fetchone())


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pg", required=True)
    a = ap.parse_args()
    try:
        ex = extraire()
    except Exception as e:  # noqa: BLE001
        dire("⛔ Supabase n'a pas pu etre lu (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    dire("EXTRAIT (lecture seule) : registre %d colonnes, %d lignes ; notes %d colonnes, %d lignes" % (
        len(ex["ddl"]["app_affaire_ledger"]), ex["csv"]["app_affaire_ledger"].count("\n"),
        len(ex["ddl"]["app_affaire_note"]), ex["csv"]["app_affaire_note"].count("\n")))
    L = R.Local(Path(a.pg))
    rouges = []
    L.demarrer()
    try:
        cn = L.cnx()
        cu = cn.cursor()
        for b in ("cicatrices_modele", "cicatrices", "cicatrices_temoin"):
            cu.execute("drop database if exists %s" % b)
        cu.execute("create database cicatrices_modele")
        for role in ("anon", "authenticated"):
            cu.execute("select 1 from pg_roles where rolname = %s", (role,))
            if not cu.fetchone():
                cu.execute("create role %s" % role)
        cn.close()
        cn = L.cnx("cicatrices_modele", autocommit=False)
        cu = cn.cursor()
        for t in TABLES:
            cu.execute("create table public.%s (%s)" % (t, ", ".join('"%s" %s' % c for c in ex["ddl"][t])))
            cu.copy_expert("copy public.%s from stdin with (format csv)" % t, io.StringIO(ex["csv"][t]))
        cu.execute("create table public.app_affaire_date_convenue (app_affaire_id bigint primary key, jour text not null)")
        with (COPIE_DU_REJEU / "convenue.csv").open(encoding="utf-8", newline="") as f:
            cu.copy_expert("copy public.app_affaire_date_convenue (app_affaire_id, jour) from stdin with (format csv)", f)
        cu.execute((COPIE_DU_REJEU / "fonction_app_dossier_jour_date_transaction.sql").read_text(encoding="utf-8"))
        cn.commit()
        cn.close()
        # A -- le patch tel quel, puis sa repetition
        R.base_depuis("cicatrices_modele", "cicatrices")
        cn = L.cnx("cicatrices")
        cu = cn.cursor()
        avant = {t: empreinte(cu, t) for t in TABLES}
        cn.close()
        try:
            R.jouer_fichier("cicatrices", PATCH)
            dire("A. LE PATCH, joue tel quel : PASSE")
        except Exception as e:  # noqa: BLE001
            dire("A. ⛔ LE PATCH A ECHOUE : %s" % str(e).splitlines()[0][:200])
            rouges.append("patch")
        cn = L.cnx("cicatrices")
        cu = cn.cursor()
        cu.execute(REPETITION.read_text(encoding="utf-8"))
        rep = cu.fetchall()
        apres = {t: empreinte(cu, t) for t in TABLES}
        cn.close()
        non = [r for r in rep if r[1] != "OUI"]
        dire("   REPETITION : %d controle(s) sur %d disent OUI" % (len(rep) - len(non), len(rep)))
        for r in rep:
            dire("     %-3s %s (%s)" % (r[1], r[0], r[2]))
        if non:
            rouges.append("repetition")
        dire("   registre %s lignes -> %s ; notes %s -> %s" % (avant["app_affaire_ledger"][0], apres["app_affaire_ledger"][0],
                                                              avant["app_affaire_note"][0], apres["app_affaire_note"][0]))
        # B -- l'inverse : retour a l'empreinte d'avant
        try:
            R.jouer_fichier("cicatrices", INVERSE)
        except Exception as e:  # noqa: BLE001
            dire("B. ⛔ L'INVERSE A ECHOUE : %s" % str(e).splitlines()[0][:200])
            rouges.append("inverse")
        cn = L.cnx("cicatrices")
        cu = cn.cursor()
        retour = {t: empreinte(cu, t) for t in TABLES}
        cn.close()
        ok_b = retour == avant
        dire("B. L'INVERSE : registre %s, notes %s -- %s" % (retour["app_affaire_ledger"], retour["app_affaire_note"],
                                                           "RETOUR EXACT (empreintes d'avant)" if ok_b else
                                                           "⛔ PAS DE RETOUR EXACT (avant %s)" % avant))
        if not ok_b:
            rouges.append("retour")
        # D -- le patch rejoue apres l'inverse : il doit refuser
        try:
            R.jouer_fichier("cicatrices", PATCH)
            dire("D. ⛔ LE PATCH S'EST REJOUE apres l'inverse")
            rouges.append("rejoue")
        except Exception as e:  # noqa: BLE001
            dire("D. le patch rejoue apres l'inverse REFUSE : %s" % str(e).splitlines()[0][:160])
        # C -- le temoin inverse : une copie qui n'est plus telle que mesuree
        R.base_depuis("cicatrices_modele", "cicatrices_temoin")
        cn = L.cnx("cicatrices_temoin")
        cu = cn.cursor()
        cu.execute("update public.app_affaire_ledger set app_dossier_numero = 'D2024-9999' where app_affaire_id = 1001563")
        av_t = {t: empreinte(cu, t) for t in TABLES}
        cn.close()
        try:
            R.jouer_fichier("cicatrices_temoin", PATCH)
            dire("C. ⛔ TEMOIN INVERSE : le patch a ECRIT sur une copie modifiee")
            rouges.append("temoin")
        except Exception as e:  # noqa: BLE001
            cn = L.cnx("cicatrices_temoin")
            cu = cn.cursor()
            ap_t = {t: empreinte(cu, t) for t in TABLES}
            cn.close()
            dire("C. TEMOIN INVERSE (numero de 1001563 change) : le patch REFUSE (%s) ; rien d'ecrit : %s" % (
                str(e).splitlines()[0][:110], "OUI" if ap_t == av_t else "⛔ NON"))
            if ap_t != av_t:
                rouges.append("temoin ecrit")
    finally:
        L.arreter()
    dire("⭐ VERT : le patch passe, sa repetition dit 7 OUI, l'inverse repose a l'identique, et il refuse ce qu'il doit"
         if not rouges else "⛔ ROUGE : %s" % rouges)
    return 1 if rouges else 0


if __name__ == "__main__":
    sys.exit(main())
