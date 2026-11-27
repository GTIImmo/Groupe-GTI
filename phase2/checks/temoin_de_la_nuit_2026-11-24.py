"""LE TEMOIN COMPLET DE LA NUIT DU 24 AU 25/11 (son 8e mot du 24/11) -- LECTURE SEULE, chez Supabase (le pooler en `read only`).

SON MOT : « ⏰ ET DEMAIN MATIN, LE TEMOIN COMPLET DE LA NUIT : les 12 parts, les 2 corrections, les 18 Charges et les 42 ecritures
ont-elles tenu le run de 05:00 ? Plus le temoin inverse : combien de parts « hektor% » le run a-t-il reecrites dans tout le
registre cette nuit -- c'est ce que nous perdons sans le savoir. »

DEUX TEMPS :
  photo     (le 24/11 au soir, AVANT le run) : toutes les parts de app_affaire_repartition (cle, valeur, origine, ecrit_par,
            ecrit_le) et les quatre empreintes des gestes du 24/11 -> P.DOSSIER / temoin_nuit_photo_24_11.json
  comparer  (le 25/11 au matin, APRES le run de 05:00) : les quatre empreintes contre celles rendues le 24/11 ; et, sur TOUT le
            registre des parts : chaque chaine dont la repartition a change pendant la nuit, rangee par origine (hektor% =
            reecrite par la nuit ; une autre origine = une saisie de l'app, ou ⛔ un ecrasement) ; les lignes reecrites a
            l'identique (ecrit_le neuf, meme valeur) comptees a part.

USAGE : python -X utf8 phase2/checks/temoin_de_la_nuit_2026-11-24.py photo | comparer
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, r"C:\Hektor\Projet\phase2\checks")
sys.path.insert(0, r"C:\Hektor\Projet")
import protocole_classeur as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
PHOTO = P.DOSSIER / "temoin_nuit_photo_24_11.json"

EMPREINTES = {
    "① les 18 Charges (patch_charge)": ("b58ba6cb9a5cd6c6e20dc01f99bcc266", """
select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), coalesce(k.origine, '-'),
       coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' order by m.annonce, m.numero), ''))
  from (values ('47542', '17840'), ('23297', '17564'), ('17548', '17481'), ('46338', '17322'), ('47174', '17639'),
               ('63490', '18999'), ('59164', '18127'), ('59339', '18143'), ('54734', '18053'), ('17597', '18973'),
               ('62336', '18648'), ('62766', '18773'), ('11695', '17296'), ('59637', '18286'), ('62934', '18950'),
               ('63299', '18942'), ('39684', '17987'), ('61893', '18996')) m(annonce, numero)
  left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero
   and k.champ = 'charge_commission'
  left join public.app_mandat_register_current r on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero"""),
    "④ les 12 parts des 6 suppositions (patch_suppositions)": ("91a61e04b6d5507cd49c95b4af7d5f89", """
select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
       ecrit_par), ';' order by app_chaine_id, cote, rang), ''))
  from public.app_affaire_repartition where app_chaine_id in (1027, 1875, 4234, 6391, 9370, 27984)"""),
    "⑤ les 2 corrections (patch_corrections)": ("adb3c8f86656a03da199a56ca9af6d15", """
select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
       ecrit_par), ';' order by app_chaine_id, cote, rang), ''))
  from public.app_affaire_repartition where app_chaine_id in (27195, 27196)"""),
    "les 42 ecritures (patch_realignement_42, les 65 pieces)": ("072b3cb3afbf685ca10dfb3c0e590a07", None),
}
IDS_42 = ("177, 178, 1059, 1061, 1101, 1104, 3646, 3650, 3699, 3701, 4196, 4197, 4385, 4387, 4480, 4483, 4496, 6171, 6172, "
          "6554, 6555, 11138, 11139, 14111, 14115, 14813, 14816, 15004, 15005, 16342, 16343, 16377, 16378, 16382, 16383, "
          "17131, 17136, 17387, 17427, 17431, 19130, 19132, 19133, 20264, 20268, 21551, 23050, 23054, 23801, 24450, 24454, "
          "26013, 26016, 27134, 27140, 27141, 27195, 27196, 27445, 27449, 27512, 27513, 28568, 28569, 30813")
EMPREINTES["les 42 ecritures (patch_realignement_42, les 65 pieces)"] = ("072b3cb3afbf685ca10dfb3c0e590a07", """
select md5(coalesce((select string_agg(concat_ws('|', l.app_affaire_id, l.vente_reglee_app, l.numero_facture_app,
         l.date_annulation_app, l.motif_annulation_app, l.honoraires_entree_app), ';' order by l.app_affaire_id)
    from public.app_affaire_ledger l where l.app_affaire_id in (%s)), '') || '#' ||
  coalesce((select string_agg(concat_ws('|', n.app_affaire_id, n.origine, md5(n.texte), n.app_dossier_id, n.app_chaine_id,
         n.ecrit_par), ';' order by n.app_affaire_id)
    from public.app_affaire_note n where abs(n.app_affaire_id) in (%s)), ''))""" % (IDS_42, IDS_42))


def empreinte_py(rows) -> str:
    """md5 de string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine,
    ecrit_par), ';' order by app_chaine_id, cote, rang) -- calculee sur les lignes lues (photo ou maintenant)."""
    import hashlib
    rs = sorted(rows, key=lambda r: (int(r[0]), r[1], int(r[2])))
    txt = ";".join("|".join(str(x) for x in r[:8] if x is not None) for r in rs)
    return hashlib.md5(txt.encode("utf-8")).hexdigest()


def lire(cu):
    cu.execute("select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage::text, origine, ecrit_par, "
               "ecrit_le::text from public.app_affaire_repartition")
    return [list(r) for r in cu.fetchall()]


def empreintes(cu):
    out = {}
    for nom, (_attendue, sql) in EMPREINTES.items():
        cu.execute(sql)
        out[nom] = cu.fetchone()[0]
    return out


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    cn, cu = P.pooler()
    if mode == "photo":
        rows = lire(cu)
        emp = empreintes(cu)
        cu.execute("select now()::text")
        quand = cu.fetchone()[0]
        PHOTO.write_text(json.dumps({"quand": quand, "parts": rows, "empreintes": emp}, ensure_ascii=False), encoding="utf-8")
        print("PHOTO %s : %d parts (%s) ; empreintes :" % (quand, len(rows), dict(Counter(r[6] for r in rows))))
        for nom, (attendue, _s) in EMPREINTES.items():
            print("   %-60s %s %s" % (nom, emp[nom][:8], "= attendue" if emp[nom] == attendue else "⛔ attendue %s" % attendue[:8]))
        print("-> %s" % PHOTO)
        return 0
    if mode != "comparer":
        print(__doc__)
        return 2
    av = json.loads(PHOTO.read_text(encoding="utf-8"))
    rows = lire(cu)
    emp = empreintes(cu)
    cu.execute("select now()::text")
    print("LE TEMOIN DE LA NUIT -- photo du %s, relu le %s" % (av["quand"], cu.fetchone()[0]))
    print()
    print("① LES GESTES DU 24/11 ONT-ILS TENU LE RUN ?")
    ok = 0
    for nom, (attendue, _s) in EMPREINTES.items():
        bon = emp[nom] == attendue
        ok += bon
        print("   %-60s %s -> %s" % (nom, emp[nom][:8], "TENU" if bon else "⛔ CHANGE (attendu %s)" % attendue[:8]))
    print("   -> %d / %d" % (ok, len(EMPREINTES)))
    print()
    print("② LE TEMOIN INVERSE : ce que la nuit a reecrit dans TOUT le registre des parts")
    def par_chaine(rs):
        d = defaultdict(dict)
        for r in rs:
            d[r[0]][(r[1], r[2])] = r
        return d
    A, B = par_chaine(av["parts"]), par_chaine(rows)
    val = lambda r: (r[3], r[5], r[6])
    changees, apparues, disparues, identiques_reecrites = Counter(), Counter(), Counter(), Counter()
    exemples = defaultdict(list)
    for ch in set(A) | set(B):
        a, b = A.get(ch, {}), B.get(ch, {})
        orig = sorted({r[6] for r in list(a.values()) + list(b.values())})
        cle = "+".join(orig)
        if not a:
            apparues[cle] += 1
            exemples["apparue " + cle].append(ch)
        elif not b:
            disparues[cle] += 1
            exemples["disparue " + cle].append(ch)
        elif {k: val(r) for k, r in a.items()} != {k: val(r) for k, r in b.items()}:
            changees[cle] += 1
            exemples["changee " + cle].append(ch)
        elif {k: r[8] for k, r in a.items()} != {k: r[8] for k, r in b.items()}:
            identiques_reecrites[cle] += 1
    for titre, c in (("chaines dont la repartition a CHANGE", changees), ("chaines APPARUES", apparues),
                     ("chaines DISPARUES", disparues), ("chaines reecrites A L'IDENTIQUE (ecrit_le neuf)", identiques_reecrites)):
        print("   %-50s %5d  %s" % (titre, sum(c.values()), dict(c)))
    for k, v in sorted(exemples.items()):
        print("      %s : %s" % (k, sorted(v)[:15]))
    nh = [ch for ch, v in B.items() if any(not str(r[6]).startswith("hektor") for r in v.values())
          and any(str(r[6]).startswith("hektor") for r in v.values())]
    print("   ⚠ chaines MIXTES (une part hektor%% a cote d'une part protegee) : %d %s" % (len(nh), sorted(nh)[:15]))

    # ③ SON MOT DU 25/11 : « LES DEUX FACES [...] AVEC TON EMPREINTE GLOBALE »
    print()
    print("③ L'EMPREINTE GLOBALE DU REGISTRE DES PARTS (la meme expression que les patchs : concat_ws, ordre chaine/cote/rang)")
    cu.execute("select count(*), md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, "
               "nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) "
               "from public.app_affaire_repartition")
    n_sql, e_sql = cu.fetchone()
    e_photo, e_py_maintenant = empreinte_py(av["parts"]), empreinte_py(rows)
    print("   la photo (%s) : %d parts, empreinte %s (recalculee ici sur ses lignes)" % (av["quand"][:16], len(av["parts"]), e_photo))
    print("   maintenant      : %d parts, empreinte %s (chez Supabase, en SQL)" % (n_sql, e_sql))
    print("   ⭐ temoin de la methode : la meme empreinte recalculee ici sur les lignes de maintenant = %s -> %s" % (
        e_py_maintenant, "IDENTIQUE au SQL" if e_py_maintenant == e_sql else "⛔ DIFFERENTE : la methode ne vaut rien"))
    print("   -> %s" % ("LE REGISTRE DES PARTS EST INCHANGE DEPUIS LA PHOTO" if e_photo == e_sql else
                       "⛔ LE REGISTRE A CHANGE DEPUIS LA PHOTO"))
    # le temoin positif du comparateur : une copie de la photo dont UNE part est retouchee doit etre vue
    import copy
    faux = copy.deepcopy(av["parts"])
    faux[0][5] = str(float(faux[0][5]) + 1)
    A2_, B2_ = par_chaine(av["parts"]), par_chaine(faux)
    vus = [ch for ch in set(A2_) | set(B2_) if {k: val(r) for k, r in A2_.get(ch, {}).items()} !=
           {k: val(r) for k, r in B2_.get(ch, {}).items()}]
    print("   ⭐ temoin positif du comparateur : une part de la photo retouchee (chaine %s) -> %d chaine(s) vue(s) changee(s) %s" % (
        faux[0][0], len(vus), "(il voit)" if vus == [faux[0][0]] else "⛔ (il ne voit pas)"))

    # ④ LES TABLES VOISINES DES GESTES DU 24/11 (ce qui pourrait avoir bouge ailleurs)
    print()
    print("④ LES TABLES VOISINES")
    for titre, q in (
            ("journal du realignement (par lot)", "select coalesce(string_agg(lot || ' ' || n, ', ' order by lot), '') from "
             "(select lot, count(*) n from public.app_classeur_realignement_journal group by lot) x"),
            ("journal : derniere ecriture", "select max(ecrit_le)::text from public.app_classeur_realignement_journal"),
            ("mise de cote (par auteur)", "select coalesce(string_agg(mise_de_cote_par || ' ' || n, ', ' order by mise_de_cote_par), '') "
             "from (select mise_de_cote_par, count(*) n from public.app_affaire_repartition_mise_de_cote group by 1) x"),
            ("notes (app_affaire_note), par origine", "select string_agg(coalesce(origine, '-') || ' ' || n, ', ' order by origine) "
             "from (select origine, count(*) n from public.app_affaire_note group by 1) x"),
            ("notes ecrites depuis la photo", "select count(*) from public.app_affaire_note where ecrit_le > '%s'" % av["quand"]),
            ("carnet des mandats : Charges du classeur", "select count(*) from public.app_mandat_champ_app where champ = "
             "'charge_commission' and origine = 'classeur'"),
            ("carnet : ecrit depuis la photo (tous champs)", "select coalesce(string_agg(champ || '/' || coalesce(origine, '-') || ' ' "
             "|| n, ', '), '0') from (select champ, origine, count(*) n from public.app_mandat_champ_app where ecrit_le > '%s' "
             "group by 1, 2) x" % av["quand"]),
            ("parts ecrites depuis la photo", "select count(*) from public.app_affaire_repartition where ecrit_le > '%s'" % av["quand"])):
        try:
            cu.execute(q)
            print("   %-48s %s" % (titre, cu.fetchone()[0]))
        except Exception as e:  # noqa: BLE001
            cn.rollback()
            cu.execute("set transaction read only")      # la lecture reste en lecture seule apres une erreur
            print("   %-48s (illisible : %s)" % (titre, str(e).strip().splitlines()[0][:120]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
