"""Relecture INDEPENDANTE apres le geste (26/11) : connexion neuve en LECTURE SEULE. Rien n'est ecrit."""
import importlib.util
import sys
from pathlib import Path

C = Path(__file__).resolve().parent
sys.path.insert(0, str(C))
sys.path.insert(0, str(C.parents[1]))
import protocole_classeur as P  # noqa: E402

s = importlib.util.spec_from_file_location("rls", C / "refermer_les_22_sauvegardes_ouvertes_2026-11-26.py")
R = importlib.util.module_from_spec(s)
s.loader.exec_module(R)
cn, cu = P.pooler()
cu.execute("""select c.relname, c.relrowsecurity, c.relforcerowsecurity,
                     (select count(*) from pg_policy p where p.polrelid = c.oid)
              from pg_class c join pg_namespace n on n.oid = c.relnamespace
              where n.nspname = 'public' and c.relname = any(%s) order by 1""", (R.LES_22,))
etat = {r[0]: r[1:] for r in cu.fetchall()}
print("RLS active : %d / 22 ; politiques : %d" % (sum(1 for v in etat.values() if v[0]), sum(v[2] for v in etat.values())))
tot, mauvais = 0, []
for t in R.LES_22:
    p = R.compter(cu, t, None)
    a = R.compter(cu, t, "authenticated")
    cu.execute("select has_table_privilege('anon', %s, 'SELECT')", ('public."%s"' % t,))
    n = cu.fetchone()[0]
    tot += p
    if a or n:
        mauvais.append((t, a, n))
print("postgres : %d lignes au total ; authenticated 0 partout, anon SANS droit de lecture partout -> %s"
      % (tot, "OUI" if not mauvais else mauvais))
cu.execute("""select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace
              where n.nspname = 'public' and c.relkind = 'r' and c.relname ~ %s and not c.relrowsecurity
                and has_table_privilege('authenticated', c.oid, 'SELECT')""", (R.DATE_EN_FIN,))
print("tables a nom date encore ouvertes a authenticated (le G1 d'avant) : %d" % cu.fetchone()[0])
cn.rollback()
cn.close()
