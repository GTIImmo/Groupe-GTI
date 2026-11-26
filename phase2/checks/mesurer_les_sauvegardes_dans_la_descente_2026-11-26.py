#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LES SAUVEGARDES DATEES DANS LA DESCENTE -- LECTURE SEULE, ⛔ RIEN N'EST ECRIT (ni Supabase, ni phase2.sqlite).

    python -X utf8 -u phase2\checks\mesurer_les_sauvegardes_dans_la_descente_2026-11-26.py

SON MOT (26/11 au matin) : « La descente sort en code 1 chaque nuit, et je voudrais que tu regardes la cause plutot que le
symptome [...] la descente recopie chaque nuit 1 665 000 lignes sur 235 tables, dont environ 250 000 lignes sur 61 tables
de sauvegarde [...] est-ce que ces 61 tables ont la moindre raison de descendre, et quelle regle poses-tu pour que les
sauvegardes futures n'y entrent pas d'elles-memes ? Une regle par motif de nom, pas une liste de 61 exclusions a la main. »

CE QU'IL LIT
  ① les journaux de la descente (logs/scheduled/descente_*.log) : chaque table, ses lignes, delta ou ECHEC, nuit par nuit ;
  ② Supabase (pg_class, en lecture) : vue ou table, cle primaire, RLS, droit SELECT de anon / authenticated ;
  ③ phase2.sqlite, OUVERT EN LECTURE SEULE (mode=ro) : la copie locale existe-t-elle, sb_pull_state ;
  ④ le code (git grep, hors .sql/.md/.csv/.txt) : qui nomme ces tables ;
  ⑤ la REGLE CANDIDATE, simulee : ce qu'elle ecarterait, ce qu'elle laisserait, et ses voisines qui n'y tombent pas.
"""
from __future__ import annotations

import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

JOURNAUX = RACINE / "logs" / "scheduled"
PHASE2 = RACINE / "phase2" / "phase2.sqlite"

# ⭐ LA REGLE CANDIDATE : UN NOM QUI FINIT PAR UNE DATE EST UNE PHOTO FIGEE.
#   _AAAAMMJJ, eventuellement suivi de _HHMMSS ; ou _AAAA_MM_JJ (la forme de la purge du 15/10).
MOTIF_DATE = re.compile(r"_20\d{2}(0[1-9]|1[0-2])([0-2]\d|3[01])(_\d{6})?$|_20\d{2}_(0[1-9]|1[0-2])_([0-2]\d|3[01])$")
# Le second motif, regarde A COTE pour voir s'il apporterait quelque chose : « _avant_ » n'importe ou.
MOTIF_AVANT = re.compile(r"_avant(_|$)")
LIGNE = re.compile(r"^\s+\[\s*(\d+)/(\d+)\]\s+(\S+)\s+(?:(\d+) lignes(\s+\(delta\))?|ECHEC : (.*))$")


def masque(nom: str) -> str:
    """Un nom de table peut porter un nom de personne (app_user_supprime_<prenomnom>_<date>) : on ne l'imprime pas."""
    return re.sub(r"^(app_user_supprime_)[a-z]+(_20\d{6})$", r"\1<nom>\2", nom)


def lire_journal(chemin: Path) -> dict[str, tuple[str, int | None]]:
    out: dict[str, tuple[str, int | None]] = {}
    for brut in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LIGNE.match(brut)
        if not m:
            continue
        nom = m.group(3)
        if m.group(6) is not None:
            out[nom] = ("ECHEC", None)
        else:
            out[nom] = ("delta" if m.group(5) else "complete", int(m.group(4)))
    return out


def main() -> int:
    journaux = sorted(JOURNAUX.glob("descente_2026-11-*.log"))
    nuits = {j.name[9:19]: lire_journal(j) for j in journaux}
    nuits = {k: v for k, v in nuits.items() if v}
    cette_nuit = max(nuits)
    T = nuits[cette_nuit]
    print("① LA DESCENTE DE CETTE NUIT (%s) : %d tables, %d lignes, %d en ECHEC"
          % (cette_nuit, len(T), sum(n or 0 for _, n in T.values()), sum(1 for e, _ in T.values() if e == "ECHEC")))

    datees = sorted(n for n in T if MOTIF_DATE.search(n))
    avant_sans_date = sorted(n for n in T if MOTIF_AVANT.search(n) and not MOTIF_DATE.search(n))
    lignes_datees = sum(T[n][1] or 0 for n in datees)
    print("\n⑤a LA REGLE « le nom finit par une date » prend %d tables, %d lignes cette nuit (dont %d en ECHEC)"
          % (len(datees), lignes_datees, sum(1 for n in datees if T[n][0] == "ECHEC")))
    print("    « _avant_ » SANS date en fin de nom : %d table(s) %s" % (len(avant_sans_date), avant_sans_date))

    cn, cu = P.pooler()

    def q(s, a=()):
        cu.execute(s, a)
        return cu.fetchall()
    meta = {}
    for nom, kind, pk, rls, anon, auth, npol in q(
            "select c.relname, c.relkind, exists(select 1 from pg_constraint k where k.conrelid = c.oid and k.contype = 'p'), "
            "c.relrowsecurity, has_table_privilege('anon', c.oid, 'SELECT'), has_table_privilege('authenticated', c.oid, 'SELECT'), "
            "(select count(*) from pg_policy p where p.polrelid = c.oid) "
            "from pg_class c join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'public' and c.relkind in ('r','v','m','p')"):
        meta[nom] = (kind, pk, rls, anon, auth, npol)
    cn.rollback()
    cn.close()
    toutes_datees_sb = sorted(n for n in meta if MOTIF_DATE.search(n))
    print("    cote Supabase, %d relations du schema public finissent par une date (la descente en a vu %d)"
          % (len(toutes_datees_sb), len(datees)))
    for n in toutes_datees_sb:
        if n not in T:
            print("      - pas dans la descente de cette nuit :", masque(n))

    print("\n② CE QU'ELLES SONT COTE SUPABASE")
    sans_pk = [n for n in datees if n in meta and not meta[n][1]]
    vues = [n for n in datees if n in meta and meta[n][0] != "r"]
    anon_lit = [n for n in datees if n in meta and meta[n][3] and not meta[n][2]]
    auth_lit = [n for n in datees if n in meta and meta[n][4] and not meta[n][2]]
    rls_sans_pol = [n for n in datees if n in meta and meta[n][2] and meta[n][5] == 0]
    print("    sans cle primaire : %d sur %d ; vues : %d" % (len(sans_pk), len(datees), len(vues)))
    print("    RLS active : %d (dont %d sans aucune politique = fermees a anon/authenticated)"
          % (sum(1 for n in datees if n in meta and meta[n][2]), len(rls_sans_pol)))
    print("    ⚠ SANS RLS ET LISIBLES par anon : %d ; par authenticated : %d" % (len(anon_lit), len(auth_lit)))
    for n in anon_lit:
        print("       anon lit :", masque(n), T[n][1])
    for n in [x for x in auth_lit if x not in anon_lit]:
        print("       authenticated seul lit :", masque(n), T[n][1])

    print("\n③ LEUR STABILITE, NUIT PAR NUIT (une photo figee ne change pas de taille)")
    bougent = []
    for n in datees:
        serie = [(d, nuits[d][n][1]) for d in sorted(nuits) if n in nuits[d] and nuits[d][n][1] is not None]
        tailles = {t for _, t in serie}
        if len(tailles) > 1:
            bougent.append((n, serie))
    print("    sur %d nuits (%s -> %s) : %d table(s) datee(s) ont change de taille"
          % (len(nuits), min(nuits), max(nuits), len(bougent)))
    for n, serie in bougent:
        print("      -", masque(n), serie)

    print("\n③b LA COPIE LOCALE (phase2.sqlite, lecture seule)")
    ro = sqlite3.connect("file:%s?mode=ro" % PHASE2.as_posix(), uri=True)
    locales = {r[0] for r in ro.execute("select name from sqlite_master where type = 'table'")}
    etat = {r[0]: r[1:] for r in ro.execute("select table_name, lignes, derniere_descente, dernier_echec from sb_pull_state")}
    jamais = [n for n in datees if n not in locales]
    print("    presentes en local : %d ; JAMAIS ECRITES en local : %d %s" % (len(datees) - len(jamais), len(jamais),
                                                                          [masque(x) for x in jamais]))
    echecs_etat = [n for n in datees if n in etat and etat[n][2]]
    print("    sb_pull_state porte un dernier echec pour : %s" % [masque(x) for x in echecs_etat])
    ro.close()

    print("\n④ QUI LES NOMME DANS LE CODE (git grep, hors .sql / .md / .csv / .txt / journaux)")
    args_e = [x for n in datees for x in ("-e", n)]
    r = subprocess.run(["git", "-C", str(RACINE), "grep", "-o", "-F", *args_e, "--",
                        "*.py", "*.js", "*.mjs", "*.cjs", "*.ts", "*.tsx", "*.ps1"],
                       capture_output=True, text=True, encoding="utf-8")
    par_table: dict[str, set[str]] = {}
    for ligne in r.stdout.splitlines():
        fichier, _, nom = ligne.partition(":")
        if fichier.endswith("mesurer_les_sauvegardes_dans_la_descente_2026-11-26.py"):
            continue
        par_table.setdefault(nom, set()).add(fichier)
    print("    %d table(s) datee(s) nommee(s) dans du code" % len(par_table))
    for n in sorted(par_table):
        print("      -", masque(n), "->", sorted(par_table[n]))

    print("\n⑤b LES VOISINES QUI N'Y TOMBENT PAS (un nom d'archive, de journal ou de photo, sans date)")
    for n in sorted(T):
        if not MOTIF_DATE.search(n) and re.search(r"archive|sauvegarde|snapshot|photo|gel|backup|_log$|_v1$", n):
            print("      -", n, T[n])

    print("\n⑤c LA MEME DESCENTE, AUTRE FAMILLE : les VUES qui descendent encore (absentes de VUES_NON_DESCENDUES)")
    vues_desc = sorted(n for n in T if n in meta and meta[n][0] == "v")
    print("    %d vue(s), %d lignes : %s" % (len(vues_desc), sum(T[n][1] or 0 for n in vues_desc), vues_desc))

    reste = {n: v for n, v in T.items() if n not in datees}
    print("\n⑥ SI LA REGLE JOUAIT CETTE NUIT : %d tables, %d lignes descendues ; %d en ECHEC"
          % (len(reste), sum(v[1] or 0 for v in reste.values()), sum(1 for v in reste.values() if v[0] == "ECHEC")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
