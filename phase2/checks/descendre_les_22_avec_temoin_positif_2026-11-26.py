#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LA DESCENTE DE CONTROLE DES 22 -- LE TEMOIN (c) DU GESTE DE 13:39, AVEC SON TEMOIN POSITIF.

    python -X utf8 -u phase2\checks\descendre_les_22_avec_temoin_positif_2026-11-26.py gardes   (LECTURE SEULE)
    python -X utf8 -u phase2\checks\descendre_les_22_avec_temoin_positif_2026-11-26.py geste    (⛔ A SON MOT : ecrit phase2.sqlite)

SON MOT (26/11) : « Vas-y pour la descente des 22. Un seul ajout : ta garde compare les lignes lues aux lignes attendues,
mais les deux viennent de la MEME source. Si elle rendait zero, 0 = 0 et les 22 copies locales seraient remplacees par du
vide sans un mot. Exige donc le temoin positif : attendu different de zero, table par table, avant la bascule. »

CE QUE FAIT LA DESCENTE (pull_from_supabase.copy_table, lu dans le code) : elle remplit <table>__tmp par l'API (cle de
service), compte la table chez Supabase par la MEME API (Content-Range), et ne bascule que si lues == attendues. DEUX TROUS :
  . attendu 0 et lues 0 -> 0 == 0 -> la copie locale est remplacee par une table VIDE, sans un mot ;
  . attendu None (le comptage a echoue) -> la garde est SAUTEE (`if attendu is not None and ...`) -> la bascule a lieu
    sans aucune verification.
CE SCRIPT LES FERME POUR CES 22, SANS TOUCHER AU CODE DE NUIT :
  T0   L'ATTENDU INDEPENDANT : le compte de chaque table lu par une AUTRE porte (P.pooler : role postgres, lecture seule,
       pas l'API), exige DIFFERENT DE ZERO table par table, et un total egal aux 125 387 lignes mesurees au geste de 13:39
       (en dur, sortie prepa_25_11/103) -- sinon rien n'est descendu (code 3).
  T1   LE TEMOIN POSITIF DANS LA BASCULE : SupabaseReader.count est enveloppe. Pour chacune des 22, il LEVE si l'attendu de
       l'API est None, 0, ou different du compte independant. Il est appele dans copy_table AVANT la bascule : la table
       part en echec, marquer_echec ne supprime que <table>__tmp, L'ANCIENNE COPIE RESTE.
  T1i  L'ENVELOPPE EST EPROUVEE D'ABORD, hors ligne : un faux comptage qui rend 0, None, puis le compte - 1 -> elle DOIT
       lever ; le bon compte -> elle DOIT laisser passer. Et T0 doit refuser une liste qui contient un zero.
  T2   APRES : chaque copie locale a EXACTEMENT le compte independant ; 0 echec ; aucune <table>__tmp ne reste ; le compte en
       postgres relu, inchange. L'etat local d'avant est affiche a cote (ce que la descente a remplace).
CODES : 0 vert . 1 un rouge nomme . 3 une garde refuse (rien n'est descendu).
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
from phase2.sync import pull_from_supabase as PF  # noqa: E402

_spec = importlib.util.spec_from_file_location("refermer_22", ICI / "refermer_les_22_sauvegardes_ouvertes_2026-11-26.py")
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
LES_22: list[str] = list(R.LES_22)
#: le total mesure au geste de 13:39 (prepa_25_11/103), en postgres -- EN DUR, pas relu de la source qu'il juge
TOTAL_DU_GESTE = 125_387

VUS: dict[str, object] = {}


def comptes_independants() -> dict[str, int]:
    cn, cu = P.pooler()
    n = {}
    for t in LES_22:
        cu.execute('select count(*) from public."%s"' % t)
        n[t] = cu.fetchone()[0]
    cn.rollback()
    cn.close()
    return n


def juger_t0(attendus: dict[str, int]) -> list[str]:
    """Les refus de T0 : une table absente, un zero, un total different de celui du geste."""
    refus = ["%s : %r" % (t, attendus.get(t)) for t in LES_22 if not attendus.get(t)]
    if sum(attendus.get(t) or 0 for t in LES_22) != TOTAL_DU_GESTE:
        refus.append("total %d au lieu de %d" % (sum(attendus.get(t) or 0 for t in LES_22), TOTAL_DU_GESTE))
    return refus


def enveloppe(attendus: dict[str, int], original):
    def count(self, table):
        n = original(self, table)
        if table in attendus:
            VUS[table] = n
            if n is None or n == 0 or n != attendus[table]:
                raise RuntimeError("TEMOIN POSITIF : l'API rend %r pour %s, le compte independant est %d -- bascule "
                                   "REFUSEE, l'ancienne copie reste" % (n, table, attendus[table]))
        return n
    return count


def eprouver_l_enveloppe(attendus: dict[str, int]) -> list[str]:
    t = LES_22[0]
    a = attendus[t]
    faux = []
    for rendu, doit_lever in ((0, True), (None, True), (a - 1, True), (a, False)):
        f = enveloppe({t: a}, lambda self, table, v=rendu: v)
        try:
            f(None, t)
            leve = False
        except RuntimeError:
            leve = True
        print("   T1i : faux comptage %-6r -> %s (attendu : %s)" % (rendu, "LEVE" if leve else "passe",
                                                                     "LEVE" if doit_lever else "passe"))
        if leve != doit_lever:
            faux.append(repr(rendu))
    VUS.clear()
    zero = dict(attendus)
    zero[t] = 0
    r0 = juger_t0(zero)
    print("   T1i : T0 sur une liste ou %s vaut 0 -> %s" % (t, "REFUSE" if r0 else "⛔ accepte"))
    if not r0:
        faux.append("T0 muet sur un zero")
    return faux


def comptes_locaux() -> dict[str, int | None]:
    con = sqlite3.connect("file:%s?mode=ro" % PF.PHASE2_DB.as_posix(), uri=True)
    existe = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    n = {t: (con.execute('select count(*) from "%s"' % t).fetchone()[0] if t in existe else None) for t in LES_22}
    tmp = sorted(x for x in existe if x.endswith("__tmp") and x[:-5] in LES_22)
    con.close()
    return n, tmp


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("gardes", "geste"):
        print(__doc__)
        return 2
    assert len(LES_22) == 22 and len(set(LES_22)) == 22
    attendus = comptes_independants()
    refus = juger_t0(attendus)
    print("T0  attendu INDEPENDANT (pooler, role postgres) : %d tables, total %d (geste de 13:39 : %d), zero nulle part : %s"
          % (len(attendus), sum(attendus.values()), TOTAL_DU_GESTE, "OUI" if not refus else "⛔ NON %s" % refus))
    faux = eprouver_l_enveloppe(attendus)
    print("T1i l'enveloppe du comptage leve sur 0, None et compte-1, laisse passer le bon : %s"
          % ("OUI" if not faux else "⛔ NON %s" % faux))
    avant, tmp_avant = comptes_locaux()
    print("    copies locales AVANT : %d presentes, total %d ; tables __tmp qui trainent : %s" % (
        sum(v is not None for v in avant.values()), sum(v or 0 for v in avant.values()), tmp_avant or "aucune"))
    if refus or faux:
        print("\n⛔ UNE GARDE REFUSE -- rien n'est descendu (code 3)")
        return 3
    if mode == "gardes":
        print("\nGARDES VERTES -- LECTURE SEULE : rien n'est descendu")
        return 0

    PF.SupabaseReader.count = enveloppe(attendus, PF.SupabaseReader.count)
    sys.argv = ["pull_from_supabase.py"] + [x for t in LES_22 for x in ("--table", t)]
    print("\n--- LA DESCENTE (pull_from_supabase.main, --table x 22, avec le temoin positif) ---")
    code = PF.main()
    print("--- fin de la descente : code %s ---\n" % code)

    apres, tmp_apres = comptes_locaux()
    pg = comptes_independants()
    rouges = []
    for t in LES_22:
        ok = apres[t] == attendus[t] and VUS.get(t) == attendus[t]
        print("   %-58s postgres %6d | API %6s | local %6s -> %6s %s" % (
            t, attendus[t], VUS.get(t), avant[t], apres[t], "" if ok else "⛔"))
        if not ok:
            rouges.append(t)
    print("\nT2  chaque copie locale = le compte independant, l'API a compte pour chacune : %s"
          % ("OUI, 22 / 22" if not rouges else "⛔ NON %s" % rouges))
    print("    total local %d (attendu %d) ; code de la descente %s (0 = aucun echec) ; __tmp restantes : %s"
          % (sum(v or 0 for v in apres.values()), TOTAL_DU_GESTE, code, tmp_apres or "aucune"))
    print("    postgres relu apres : %s" % ("INCHANGE" if pg == attendus else "⛔ CHANGE %s" % {
        t: (attendus[t], pg[t]) for t in LES_22 if pg[t] != attendus[t]}))
    vert = not rouges and code == 0 and not tmp_apres and pg == attendus and \
        sum(v or 0 for v in apres.values()) == TOTAL_DU_GESTE
    print("\n%s" % ("✅ TEMOIN (c) VERT : les 22 descendues, aucune ligne perdue" if vert else "⛔ TEMOIN (c) EN ECHEC"))
    return 0 if vert else 1


if __name__ == "__main__":
    sys.exit(main())
