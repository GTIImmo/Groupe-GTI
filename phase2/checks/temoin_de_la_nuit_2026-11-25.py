"""LE TEMOIN DE LA NUIT DU 25 AU 26/11 -- LA PREMIERE NUIT DE LA VAGUE (son mot du 25/11) -- LECTURE SEULE.

SON MOT : « Et demain matin, le temoin de la nuit : la vague a-t-elle tenu, et les orphelines sont-elles restees a 0 ? »

LES DEUX FACES, comme les 24-25/11 :
  ① CE QUI A TENU -- le run de 04:00 rejoue le chainage avec le fichier pose (c'est deterministe) : les chaines et les etiquettes
     de chaque piece de la photo sont-elles les memes ? les avis, notes et conditions (leurs reflets) ? le journal du
     realignement et la mise de cote ? les orphelines (0) ? les ventes reglees sans part (0) ? et les 4 gestes du 24/11 ?
  ② CE QUI A BOUGE AILLEURS -- dans TOUT le registre des parts : chaque chaine changee, apparue, disparue ou reecrite a
     l'identique, rangee par origine ; les pieces neuves ; les pieces dont la chaine ou l'etiquette a change.
  ③ L'EMPREINTE GLOBALE, le temoin de la methode (meme empreinte en Python et en SQL) et le temoin du comparateur (une part
     retouchee expres est vue).

USAGE : python -X utf8 phase2/checks/temoin_de_la_nuit_2026-11-25.py photo     (le 25/11, apres le dernier geste du jour)
        python -X utf8 phase2/checks/temoin_de_la_nuit_2026-11-25.py comparer  (le 26/11 au matin)
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
_spec = importlib.util.spec_from_file_location("t24", Path(__file__).resolve().parent / "temoin_de_la_nuit_2026-11-24.py")
T24 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T24)          # ses 4 empreintes du 24/11 et son empreinte_py
PHOTO = P.DOSSIER / "temoin_nuit_photo_25_11.json"
REFLETS = {
    "avis": "select md5(coalesce(string_agg(concat_ws('|', id_unique, app_dossier_uuid, app_dossier_numero), ';' order by "
            "id_unique), '')) from public.app_classeur_avis",
    "notes": "select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, app_chaine_id), ';' order by app_affaire_id), '')) "
             "from public.app_affaire_note",
    "conditions": "select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, rang, app_chaine_id), ';' order by "
                  "app_affaire_id, rang), '')) from public.app_affaire_condition"}
COMPTES = {
    "orphelines": "select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l "
                  "where l.app_chaine_id = r.app_chaine_id)",
    "ventes reglees sans part": "select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
                                "coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 "
                                "from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)",
    "journal du realignement": "select count(*) from public.app_classeur_realignement_journal",
    "mise de cote": "select count(*) from public.app_affaire_repartition_mise_de_cote",
    "etiquettes distinctes": "select count(distinct app_dossier_uuid) from public.app_affaire_ledger"}


def lire(cu) -> dict:
    out = {"parts": T24.lire(cu)}
    cu.execute("select app_affaire_id, app_chaine_id, app_dossier_uuid::text, app_dossier_numero from public.app_affaire_ledger")
    out["registre"] = {str(a): [c, u, n] for a, c, u, n in cu.fetchall()}
    out["reflets"] = {}
    for k, q in REFLETS.items():
        cu.execute(q)
        out["reflets"][k] = cu.fetchone()[0]
    out["comptes"] = {}
    for k, q in COMPTES.items():
        cu.execute(q)
        out["comptes"][k] = cu.fetchone()[0]
    out["gestes_24_11"] = T24.empreintes(cu)
    cu.execute("select now()::text")
    out["quand"] = cu.fetchone()[0]
    return out


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    cn, cu = P.pooler()
    m = lire(cu)
    cn.rollback()
    cn.close()
    if mode == "photo":
        PHOTO.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        print("PHOTO %s : %d parts (%s), %d pieces, comptes %s, reflets %s -> %s" % (
            m["quand"], len(m["parts"]), T24.empreinte_py(m["parts"])[:8], len(m["registre"]), m["comptes"],
            {k: v[:8] for k, v in m["reflets"].items()}, PHOTO))
        return 0
    if mode != "comparer":
        print(__doc__)
        return 2
    av = json.loads(PHOTO.read_text(encoding="utf-8"))
    print("LE TEMOIN DE LA PREMIERE NUIT DE LA VAGUE -- photo du %s, relu le %s" % (av["quand"], m["quand"]))
    print()
    print("① CE QUI A TENU")
    ra, rb = av["registre"], m["registre"]
    ch = sorted(a for a in ra if a in rb and ra[a][0] != rb[a][0])
    lb = sorted(a for a in ra if a in rb and ra[a][1] != rb[a][1])
    neuves, parties = sorted(set(rb) - set(ra)), sorted(set(ra) - set(rb))
    print("   le chainage de la vague : %d pieces de la photo ont change de CHAINE %s ; %d d'ETIQUETTE %s -> %s" % (
        len(ch), ch[:10], len(lb), lb[:10], "TENU" if not ch and not lb else "⛔ A LIRE"))
    print("   pieces neuves cette nuit : %d %s ; pieces disparues : %d %s" % (len(neuves), neuves[:10], len(parties), parties[:10]))
    # ⭐ SON MOT DU 25/11 : « et 8016 est-il protege du run ? » -- ses parts, avant et apres la nuit, et le verrou (une part
    #   hors hektor% : l'absorbeur n'y touche pas)
    p8a = sorted((r[1], r[4], r[5], r[6]) for r in av["parts"] if r[0] == 8016)
    p8b = sorted((r[1], r[4], r[5], r[6]) for r in m["parts"] if r[0] == 8016)
    prot = any(not str(r[3]).startswith("hektor") for r in p8b)
    print("   8016 (SXJDHXKF, vente reglee ROMERA 100) : %s -> %s ; protegee %s -> %s" % (
        p8a, p8b, prot, "TENU" if p8a == p8b and prot else "⛔ A LIRE"))
    for k in REFLETS:
        print("   reflets des %-12s %s -> %s %s" % (k, av["reflets"][k][:8], m["reflets"][k][:8],
                                                  "TENU" if av["reflets"][k] == m["reflets"][k] else "⛔ CHANGE"))
    for k in COMPTES:
        bon = av["comptes"][k] == m["comptes"][k]
        cible0 = k in ("orphelines", "ventes reglees sans part")
        print("   %-28s %s -> %s %s" % (k, av["comptes"][k], m["comptes"][k],
                                       ("TENU" if bon else "⛔ CHANGE") + (" (attendu 0)" if cible0 else "")))
    # la photo contre maintenant (la nuit a-t-elle touche ces gestes ?) ; l'ecart a l'empreinte du 24/11 est DIT a part :
    #   le 25/11, des gestes accordes ont touche des pieces des 42 (A3 : des reflets de notes ; les dates sur 27195 et 27134)
    for k, (att, _q) in T24.EMPREINTES.items():
        print("   geste du 24/11 %-52s %s%s" % (k[:52], "TENU" if m["gestes_24_11"][k] == av["gestes_24_11"][k] else "⛔ CHANGE",
                                              "" if av["gestes_24_11"][k] == att else
                                              " (≠ du 24/11 depuis les gestes accordes du 25/11 : A3, les dates)"))
    print()
    print("② CE QUI A BOUGE AILLEURS -- tout le registre des parts")

    def par_chaine(rs):
        d = defaultdict(dict)
        for r in rs:
            d[r[0]][(r[1], r[2])] = r
        return d
    A, B = par_chaine(av["parts"]), par_chaine(m["parts"])
    val = lambda r: (r[3], r[5], r[6])
    c_ = defaultdict(Counter)
    ex = defaultdict(list)
    for c in set(A) | set(B):
        a, b = A.get(c, {}), B.get(c, {})
        cle = "+".join(sorted({str(r[6]) for r in list(a.values()) + list(b.values())}))
        if not a:
            quoi = "APPARUE"
        elif not b:
            quoi = "DISPARUE"
        elif {k: val(r) for k, r in a.items()} != {k: val(r) for k, r in b.items()}:
            quoi = "CHANGEE"
        elif {k: r[8] for k, r in a.items()} != {k: r[8] for k, r in b.items()}:
            quoi = "REECRITE A L'IDENTIQUE"
        else:
            continue
        c_[quoi][cle] += 1
        ex[quoi + " " + cle].append(c)
    for quoi in ("CHANGEE", "APPARUE", "DISPARUE", "REECRITE A L'IDENTIQUE"):
        print("   chaines %-24s %4d  %s" % (quoi, sum(c_[quoi].values()), dict(c_[quoi])))
    for k, v in sorted(ex.items()):
        print("      %s : %s" % (k, sorted(v)[:15]))
    print()
    e_av, e_ap = T24.empreinte_py(av["parts"]), T24.empreinte_py(m["parts"])
    print("③ L'EMPREINTE GLOBALE DES PARTS : photo %s (%d) -> maintenant %s (%d) -> %s" % (
        e_av, len(av["parts"]), e_ap, len(m["parts"]), "INCHANGE" if e_av == e_ap else "CHANGE"))
    faux = copy.deepcopy(av["parts"])
    faux[0][5] = str(float(faux[0][5]) + 1)
    vu = T24.empreinte_py(faux) != e_av
    print("   temoin du comparateur : une part de la photo retouchee expres change l'empreinte -> %s" % ("il voit" if vu else "⛔"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
