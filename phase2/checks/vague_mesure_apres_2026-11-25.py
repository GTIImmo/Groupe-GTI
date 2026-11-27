"""LA VAGUE DU 25/11 (09:02 -> 09:07:54) : CE QU'ELLE A FAIT, MESURE APRES -- LECTURE SEULE (pooler en read only).

SON MOT : « tu me rends : les empreintes d'apres, le journal des 797 pieces, le compte des orphelines (il doit tomber a 0),
les 231 fusions attendues, et ce que les gardes ont refuse s'il y a lieu. »

CONTRE QUOI : les sauvegardes datees de l'etape 1 (suffixe 20261125_090205) -- le registre (chaines et etiquettes), le
journal des etiquettes, la repartition -- et la prevision du protocole (le rejeu E de la vague entiere, passage 82 a blanc).
SORTIE : sa console, et notice/LA_VAGUE_DU_25_11_LES_PIECES_QUI_ONT_BOUGE.csv (chaque piece : sa chaine et son etiquette
avant -> apres, la prevision, le verdict).
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import coupe_preuve_interne as K  # noqa: E402
import protocole_classeur as P  # noqa: E402
import protocole_portes as PO  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
SUF = "20261125_090205"
EXPR = ("md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, "
        "origine, ecrit_par), ';' order by app_chaine_id, cote, rang), ''))")


def dire(s=""):
    print(s, flush=True)


# la prevision du protocole (le meme calcul que l'essai a blanc des etiquettes)
_AB = P.DOSSIER.parent / "protocole_a_blanc_retrait_e"
P.SOCLE, P.DOSSIER, PO.MODULE = _AB / "socle.sqlite", _AB, _AB / "affaire_ledger_sans_4126_21520.py"
image = "2026-11-25_072625"
I = P.Image(P.IMAGES / image)
lab_img = {a: I.pieces[a]["app_dossier_uuid"] for a in I.pieces}
chE, _ = PO.rejeu_en_cache("E", image, _AB / "brouillon_detachements_protocole_passage_82.csv",
                           {"APP_CHAINAGE_GARDE_G2": "0", "APP_CHAINAGE_DETACHEMENTS": "1"}, False)
labE = K.pose_de_nuit(lab_img, chE)

cn, cu = P.pooler()
q = lambda s: (cu.execute(s), cu.fetchall())[1]
dire("LA VAGUE DU 25/11 -- MESURE APRES (lecture seule) -- relu le %s" % q("select now()::text")[0][0])

# ① les chaines et les etiquettes : avant (la sauvegarde) -> apres (le registre), contre la prevision
av = {int(a): (c, str(u) if u else None, n) for a, c, u, n in q(
    "select app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero from public.app_affaire_ledger_chaines_avant_vague_%s" % SUF)}
ap = {int(a): (c, str(u) if u else None, n) for a, c, u, n in q(
    "select app_affaire_id, app_chaine_id, app_dossier_uuid, app_dossier_numero from public.app_affaire_ledger")}
ch_bouge = sorted(a for a in ap if av.get(a, (None,))[0] != ap[a][0])
lab_bouge = sorted(a for a in ap if av.get(a, (None, None))[1] != ap[a][1])
uuids_avant = {v[1] for v in av.values() if v[1]}
prevu_lab = {a: l_ for a, l_ in labE.items() if l_ != lab_img.get(a)}
ch_ecart = sorted(a for a in ap if ap[a][0] != chE.get(a))
verdict, groupes = {}, defaultdict(set)
for a in sorted(set(lab_bouge) | set(prevu_lab)):
    p_ = prevu_lab.get(a)
    u = ap.get(a, (None, None))[1]
    if p_ is None:
        verdict[a] = "⛔ CHANGEE SANS ETRE PREVUE"
    elif str(p_).startswith("NEUVE"):
        groupes[p_].add(u)
        verdict[a] = "NEUVE, comme prevu" if u and u not in uuids_avant else "⛔ PREVUE NEUVE, PAS NEUVE"
    else:
        verdict[a] = "existante, comme prevu" if u == p_ else "⛔ AUTRE ETIQUETTE QUE PREVUE"
eclates = [g for g, us in groupes.items() if len(us) != 1]
cv = Counter(verdict.values())
dire()
dire("① LES PIECES QUI ONT BOUGE (le registre contre sa sauvegarde de 09:02)")
dire("   chaines : %d pieces changent de chaine ; contre le rejeu du matin : %d ecart(s) %s" % (
    len(ch_bouge), len(ch_ecart), ch_ecart[:10]))
dire("   etiquettes : %d pieces changent d'etiquette (prevues : %d) -> %s ; %d groupes neufs prevus -> %d etiquettes neuves, %d "
     "groupe(s) eclate(s)" % (len(lab_bouge), len(prevu_lab), dict(cv), len(groupes),
                              len({next(iter(us)) for us in groupes.values() if len(us) == 1}), len(eclates)))
f = Path(r"C:\Hektor\Projet\notice\LA_VAGUE_DU_25_11_LES_PIECES_QUI_ONT_BOUGE.csv")
with f.open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["app_affaire_id", "chaine_avant", "chaine_apres", "chaine_prevue", "etiquette_avant", "etiquette_apres",
                "etiquette_prevue", "verdict_etiquette"])
    for a in sorted(set(ch_bouge) | set(lab_bouge)):
        b_, c_ = av.get(a, (None, None, None)), ap[a]
        p_ = prevu_lab.get(a)
        w.writerow([a, b_[0], c_[0], chE.get(a), b_[2] or "-", c_[2] or "-",
                    ("NEUVE" if str(p_).startswith("NEUVE") else (I.pieces.get(a, {}) and p_ and next(
                        (v[2] for v in av.values() if v[1] == p_), p_))) if p_ else "inchangee",
                    verdict.get(a, "inchangee")])
dire("   -> %s (%d pieces)" % (f, len(set(ch_bouge) | set(lab_bouge))))

# ② le journal des etiquettes : ce que la pose de ce matin y a ecrit
n_av = q("select count(*) from public.app_dossier_etiquette_journal_avant_vague_%s" % SUF)[0][0]
n_ap = q("select count(*) from public.app_dossier_etiquette_journal")[0][0]
cols = [r[0] for r in q("select column_name from information_schema.columns where table_schema='public' and "
                         "table_name='app_dossier_etiquette_journal' order by ordinal_position")]
col_geste = next((c for c in ("geste", "nature", "type", "evenement") if c in cols), None)
dire()
dire("② LE JOURNAL DES ETIQUETTES : %d lignes avant, %d apres -> %d ecrites par la pose de ce matin%s" % (
    n_av, n_ap, n_ap - n_av, (" : %s" % dict(q(
        "select %s, count(*) from public.app_dossier_etiquette_journal j where not exists (select 1 from "
        "public.app_dossier_etiquette_journal_avant_vague_%s s where s = j) group by 1" % (col_geste, SUF)))) if col_geste else ""))

# ③ la repartition : apres A2 (empreinte de la repetition), apres l'etape 8, et les dossiers que l'etape 8 a ecrits
n_rep, e_rep = q("select count(*), %s from public.app_affaire_repartition" % EXPR)[0]
dire()
dire("③ LA REPARTITION : %d parts, empreinte %s (apres A2, la repetition rendait f4e1feb6 ; l'etape 8 a ecrit ensuite)" % (n_rep, e_rep))
ecrits = q("select distinct app_chaine_id from public.app_affaire_repartition where ecrit_par = 'conversion' "
           "and ecrit_le > '2026-11-25 07:30:00+00'")
for (c,) in ecrits:
    avant_c = q("select cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par from "
                "public.app_affaire_repartition_avant_vague_%s where app_chaine_id = %d order by cote, rang" % (SUF, c))
    apres_c = q("select cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par from "
                "public.app_affaire_repartition where app_chaine_id = %d order by cote, rang" % c)
    membres = sorted(int(a) for a, v in ap.items() if v[0] == c)
    membres_av = sorted(int(a) for a, v in av.items() if v[0] == c)
    dire("   ⚠ ECRIT PAR L'ETAPE 8 : chaine %d -- membres avant %s, apres %s" % (c, membres_av, membres))
    dire("        avant (sauvegarde 09:02) : %s" % [tuple(r) for r in avant_c])
    dire("        apres                    : %s" % [tuple(r) for r in apres_c])

# ④ les orphelines, les ventes reglees sans part, les reflets
orph = q("select count(*), count(distinct app_chaine_id) from public.app_affaire_repartition r where not exists "
         "(select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)")[0]
vr = q("select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
       "coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from "
       "public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)")[0][0]
nf = q("select count(*) from public.app_affaire_note n join public.app_affaire_ledger l on l.app_affaire_id = n.app_affaire_id "
       "where n.app_chaine_id is distinct from l.app_chaine_id")[0][0]
cf = q("select count(*) from public.app_affaire_condition c join public.app_affaire_ledger l on l.app_affaire_id = c.app_affaire_id "
       "where c.app_chaine_id is distinct from l.app_chaine_id")[0][0]
dire()
dire("④ LES PARTS ORPHELINES : %d parts sur %d chaines (26 parts sur 13 chaines ce matin) ; ventes reglees sans part : %d ; "
     "notes au reflet faux : %d ; conditions : %d" % (orph[0], orph[1], vr, nf, cf))

# ⑤ les journaux et la mise de cote
dire()
dire("⑤ LE JOURNAL DU REALIGNEMENT : %s ; LA MISE DE COTE : %s" % (
    dict(q("select lot, count(*) from public.app_classeur_realignement_journal group by lot order by lot")),
    dict(q("select mise_de_cote_par, count(*) from public.app_affaire_repartition_mise_de_cote group by 1 order by 1"))))
dire("   les sauvegardes datees : %s" % [r[0] for r in q(
    "select c.relname from pg_class c where c.relnamespace = 'public'::regnamespace and (c.relname like '%%avant_vague_2026112%%'"
    " or c.relname like '%%avant_a2vague%%' or c.relname like '%%avant_a1vague%%' or c.relname like '%%avant_a3vague%%') order by 1")])
cn.rollback()
cn.close()
