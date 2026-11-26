#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""REFERMER LES 22 SAUVEGARDES DATEES OUVERTES A `authenticated` : RLS ACTIVEE, SANS POLITIQUE, AUCUN CONTENU TOUCHE.

    python -X utf8 -u phase2\checks\refermer_les_22_sauvegardes_ouvertes_2026-11-26.py gardes      (LECTURE SEULE)
    python -X utf8 -u phase2\checks\refermer_les_22_sauvegardes_ouvertes_2026-11-26.py a_blanc     (⛔ A SON MOT : ecriture ANNULEE)
    python -X utf8 -u phase2\checks\refermer_les_22_sauvegardes_ouvertes_2026-11-26.py geste       (⛔ A SON MOT, CE SOIR)
    python -X utf8 -u phase2\checks\refermer_les_22_sauvegardes_ouvertes_2026-11-26.py inverse     (⛔ A SON MOT)

SON MOT (26/11) : « Les 22 copies ouvertes : accord pour les refermer [...] les 22 donnent aussi INSERT, UPDATE, DELETE et
TRUNCATE a tout compte connecte. Un compte de l'agence, ou un bug de l'app, peut vider une de ces photos -- et ce serait le
retour arriere d'un geste de masse qui disparaitrait, sans trace [...] RLS activee sans politique, aucun contenu touche, mais
avec temoin, pas avec promesse : (a) les 22 rendent zero ligne pour authenticated, (b) le protocole rejoue un passage et
retrouve le meme md5 de socle, (c) la descente du soir passe les 22 sans rien perdre. » ; « Ce soir, dans cet ordre : la
RLS des 22 seule, puis la descente de controle avec ses trois temoins, puis -- et seulement apres -- la regle des dates. »

CE SCRIPT PORTE LE TEMOIN (a) ; (b) est le rejeu du 82 sur copie, (c) la descente `--table` des 22 (commandes au carnet).
LES GARDES, avant tout geste :
  G1  la liste mesuree A L'INSTANT (nom date en fin, pas de RLS, authenticated a SELECT) = la liste FIGEE ci-dessous, a
      l'identique : ni une de plus, ni une de moins ;
  G2  chacune : pas de RLS, aucune politique, proprietaire postgres.
LE TEMOIN (a), DANS LA MEME TRANSACTION :
  POSITIF  AVANT : en role authenticated, chaque table rend ses lignes (le meme compte qu'en postgres) -- sinon le zero
           d'apres ne prouverait rien ;
  (a)      APRES : en role authenticated, chaque table rend 0 ligne ; en postgres, le MEME compte qu'avant (rien n'est perdu).
INVERSE : `disable row level security` sur ces 22-la seulement, avec le meme temoin retourne.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(ICI.parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402


def connexion(ecriture: bool):
    """La meme connexion que le juge (P.pooler, qui ouvre en LECTURE SEULE) -- en ecriture seulement pour a_blanc / geste /
    inverse, sur son mot. ⚠ 26/11 : le premier essai a blanc est passe par P.pooler et la base a REFUSE l'ALTER (« read-only
    transaction ») : rien n'a ete touche, et c'est ce verrou qui l'a dit."""
    if not ecriture:
        return P.pooler()
    import os
    import urllib.parse
    import psycopg2
    from phase2.sync import push_upgrade_to_supabase as PU
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    cn = psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                          user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                          connect_timeout=15, sslmode="require")
    return cn, cn.cursor()

#: LES 22, FIGEES le 26/11 au matin (mesurer_les_sauvegardes_dans_la_descente_2026-11-26.py, sortie 77)
LES_22 = [
    "app_affaire_avant_c3_dates_20261116", "app_affaire_ledger_avant_doublons_classeur_20261118",
    "app_affaire_ledger_avant_offre_sans_date_20261102", "app_affaire_note_avant_doublons_classeur_20261118",
    "app_affaire_repartition_avant_classeur_20261113", "app_affaire_repartition_avant_classeur_20261114",
    "app_affaire_repartition_avant_essai_24933_20261029", "app_chainage_photo_20261110",
    "app_classeur_lien_avant_doublons_classeur_20261118", "app_classeur_lien_avant_rattachement_43091_20261118",
    "app_console_document_avant_dedoublonnage_59578_20261021", "app_console_job_erreurs_avant_purge_2026_10_15",
    "app_contact_relation_avant_offre_sans_date_20261102", "app_etiquette_avant_repose2_20261112",
    "app_etiquette_avant_repose_20261112", "app_etiquette_compteur_avant_20261112",
    "app_etiquette_compteur_avant_repose2_20261112", "app_etiquette_journal_avant_20261112",
    "app_etiquette_journal_avant_repose2_20261112", "app_sauvegarde_charge_avant_20261104",
    "app_sauvegarde_charge_avant_hektor_20261104", "app_sauvegarde_fonction_20261104"]
DATE_EN_FIN = r"(_20\d{6}(_\d{6})?$|_20\d{2}_\d{2}_\d{2}$)"


def compter(cu, t: str, role: str | None) -> int:
    if role:
        cu.execute("set local role %s" % role)
    cu.execute('select count(*) from public."%s"' % t)
    n = cu.fetchone()[0]
    if role:
        cu.execute("reset role")
    return n


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("gardes", "a_blanc", "geste", "inverse"):
        print(__doc__)
        return 2
    assert len(LES_22) == 22 and len(set(LES_22)) == 22 and all(re.search(DATE_EN_FIN, t) for t in LES_22)
    cn, cu = connexion(mode != "gardes")
    echecs = []
    cu.execute("""select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
                  where n.nspname = 'public' and c.relkind = 'r' and c.relname ~ %s and not c.relrowsecurity
                    and has_table_privilege('authenticated', c.oid, 'SELECT') order by 1""", (DATE_EN_FIN,))
    ouvertes = [r[0] for r in cu.fetchall()]
    cu.execute("""select c.relname, c.relrowsecurity, pg_get_userbyid(c.relowner),
                         (select count(*) from pg_policy p where p.polrelid = c.oid)
                  from pg_class c join pg_namespace n on n.oid = c.relnamespace
                  where n.nspname = 'public' and c.relname = any(%s) order by 1""", (LES_22,))
    etat = {r[0]: r[1:] for r in cu.fetchall()}
    attendu_rls = mode == "inverse"
    if mode == "inverse":
        g1 = all(etat.get(t, (None,))[0] is True for t in LES_22)
        print("G1 (inverse) : les 22 ont la RLS active : %s" % g1)
    else:
        g1 = sorted(ouvertes) == sorted(LES_22)
        print("G1 : ouvertes a l'instant = la liste figee : %s (%d mesurees, %d figees%s)" % (
            g1, len(ouvertes), len(LES_22), "" if g1 else " ; en plus %s ; en moins %s" % (
                sorted(set(ouvertes) - set(LES_22)), sorted(set(LES_22) - set(ouvertes)))))
    g2 = all(t in etat and etat[t][0] is attendu_rls and etat[t][1] == "postgres" and etat[t][2] == 0 for t in LES_22)
    print("G2 : chacune RLS %s, proprietaire postgres, aucune politique : %s" % ("active" if attendu_rls else "absente", g2))
    if not (g1 and g2):
        print("⛔ UNE GARDE REFUSE -- rien n'est fait (code 3)")
        cn.rollback()
        cn.close()
        return 3
    avant = {}
    for t in LES_22:
        avant[t] = (compter(cu, t, None), compter(cu, t, "authenticated"))
    pos = [t for t, (p, a) in avant.items() if (a == p) != (mode != "inverse") or (mode != "inverse" and p == 0)]
    print("TEMOIN POSITIF (avant) : en authenticated, %s : %s" % (
        "chaque table rend ses lignes" if mode != "inverse" else "chaque table rend 0 ligne",
        "OUI" if not pos else "⛔ NON %s" % pos))
    if mode != "inverse" and pos:
        echecs.append("temoin positif")
    if mode == "gardes":
        cn.rollback()
        cn.close()
        print("\n%s -- LECTURE SEULE : rien n'est change" % ("GARDES VERTES" if not echecs else "⛔ %s" % echecs))
        return 1 if echecs else 0
    verbe = "disable" if mode == "inverse" else "enable"
    for t in LES_22:
        cu.execute('alter table public."%s" %s row level security' % (t, verbe))
    apres = {t: (compter(cu, t, None), compter(cu, t, "authenticated")) for t in LES_22}
    perdu = [t for t in LES_22 if apres[t][0] != avant[t][0]]
    if mode == "inverse":
        faux = [t for t in LES_22 if apres[t][1] != apres[t][0]]
        print("TEMOIN (inverse) : en authenticated, chaque table rend de nouveau ses lignes : %s" % ("OUI" if not faux else faux))
    else:
        faux = [t for t in LES_22 if apres[t][1] != 0]
        print("TEMOIN (a) : en authenticated, chaque table rend 0 ligne : %s" % ("OUI, 22 / 22" if not faux else "⛔ %s" % faux))
    print("            en postgres, le meme compte qu'avant (rien n'est perdu) : %s ; total %d lignes"
          % ("OUI" if not perdu else "⛔ %s" % perdu, sum(p for p, _a in apres.values())))
    for t in LES_22:
        print("   %-58s postgres %6d -> %6d | authenticated %6d -> %6d" % (t, avant[t][0], apres[t][0], avant[t][1], apres[t][1]))
    if faux or perdu:
        echecs.append("temoin (a)")
    if mode == "a_blanc" or echecs:
        cn.rollback()
        print("\n%s -- TRANSACTION ANNULEE : rien n'est change" % ("⛔ TEMOIN EN ECHEC : %s" % echecs if echecs else "A BLANC VERT"))
        cn.close()
        return 1 if echecs else 0
    cn.commit()
    cu.execute("""select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace
                  where n.nspname = 'public' and c.relname = any(%s) and c.relrowsecurity""", (LES_22,))
    print("\n✅ %s ET COMMITE -- relu apres le commit : %d / 22 avec la RLS active" % (
        "GESTE FAIT" if mode == "geste" else "INVERSE FAIT", cu.fetchone()[0]))
    cn.rollback()
    cn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
