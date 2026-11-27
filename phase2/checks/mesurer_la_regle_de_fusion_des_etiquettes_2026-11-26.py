"""SUR QUOI LA FUSION DEPARTAGE VRAIMENT (26/11) -- LECTURE SEULE.
Le code (app_poser_etiquettes_dossier, etape 3) : la gagnante = l'etiquette de la ligne au PLUS PETIT app_affaire_id.
Le commentaire (SQL et docstring Python) : « on garde la plus ANCIENNE ».
On mesure : notre cas (3647 / 3648), puis toutes les fusions du journal, sous deux sens de « plus ancienne » :
  N  le numero le plus ancien (annee, rang) -- le rang suit la date de la premiere transaction ;
  P  l'etiquette POSEE la premiere (journal, evenement 'pose' ou 'scission' qui l'a creee).
Resultat du 26/11 : 296 fusions ; N contredit le code 107 fois ; P jamais, mais 170 ex aequo (posees dans la meme seconde,
departagees par l'app_affaire_id). Notre cas : 445c3170 / D2024-0306 posee le 12/11, 42dd4d66 / D2024-0511 nee d'une
scission le 25/11 -- les DEUX sens gardent D2024-0306, le code garde D2024-0511 (3647 < 3648) : ce sera la premiere fusion
qui absorbe une etiquette posee AVANT la gardee. Texte de la RPC : prepa_25_11/105 (md5 b9fa8dea)."""
import re
import sys
from pathlib import Path

C = Path(__file__).resolve().parent
sys.path.insert(0, str(C))
sys.path.insert(0, str(C.parents[1]))
import protocole_classeur as P  # noqa: E402


def cle(num):
    m = re.match(r"D(\d{4})-(\d+)$", num or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


cn, cu = P.pooler()
print("① NOTRE CAS")
cu.execute("""select app_affaire_id, kind, state, date, app_dossier_numero, app_dossier_uuid::text,
                     public.app_dossier_jour_date_transaction(kind, date, propositions_json, app_affaire_id)
              from public.app_affaire_ledger where app_affaire_id in (3647, 3648, 3650) order by 1""")
for r in cu.fetchall():
    print("   %s %-9s %-9s date %s  jour de rang %s  %s %s" % (r[0], r[1], r[2], str(r[3])[:10], r[6], r[4], r[5][:8]))
for u in ("42dd4d66", "445c3170"):
    cu.execute("""select quand, evenement, dossier_numero, transactions from public.app_dossier_etiquette_journal
                  where dossier_uuid::text like %s and evenement in ('pose', 'scission') order by quand limit 3""", (u + "%",))
    print("   naissance de %s : %s" % (u, [(str(q)[:19], e, n, t) for q, e, n, t in cu.fetchall()]))
cu.execute("""select quand, evenement, dossier_numero, transactions from public.app_dossier_etiquette_journal
              where autre_uuid::text like '445c3170%%' and evenement = 'scission' order by quand""")
print("   445c3170 nee d'une scission (autre_uuid) : %s" % [(str(q)[:19], e, n, t) for q, e, n, t in cu.fetchall()])

print("\n② TOUTES LES FUSIONS DU JOURNAL")
cu.execute("""select f.quand, f.dossier_numero, f.ancien_numero, f.dossier_uuid::text, f.autre_uuid::text, f.transactions
              from public.app_dossier_etiquette_journal f where f.evenement = 'fusion' order by f.quand""")
F = cu.fetchall()
cu.execute("""select dossier_uuid::text, min(quand) from public.app_dossier_etiquette_journal where evenement = 'pose'
              group by 1""")
pose = dict(cu.fetchall())
cu.execute("""select autre_uuid::text, min(quand) from public.app_dossier_etiquette_journal where evenement = 'scission'
              group by 1""")
for u, q in cu.fetchall():
    pose[u] = min(q, pose.get(u, q))
cn.rollback()
cn.close()
n_contre = p_contre = p_egal = p_inconnu = 0
exemples = []
for q, garde, absorbee, ug, ua, tx in F:
    kg, ka = cle(garde), cle(absorbee)
    if kg and ka and ka < kg:
        n_contre += 1
        exemples.append((str(q)[:10], garde, absorbee))
    pg, pa = pose.get(ug), pose.get(ua)
    if pg is None or pa is None:
        p_inconnu += 1
    elif pa < pg:
        p_contre += 1
    elif pa == pg:
        p_egal += 1
print("   %d fusion(s) au journal" % len(F))
print("   N : l'absorbee avait le numero PLUS ANCIEN que la gardee : %d fusion(s) ; exemples %s" % (n_contre, exemples[:8]))
print("   P : l'absorbee avait ete POSEE AVANT la gardee : %d ; posees dans la meme seconde : %d ; naissance inconnue : %d"
      % (p_contre, p_egal, p_inconnu))
