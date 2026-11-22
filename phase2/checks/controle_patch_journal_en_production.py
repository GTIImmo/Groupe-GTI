#!/usr/bin/env python
"""LE CONTROLE DU PATCH DU JOURNAL EN PRODUCTION -- chantier classeur, 22/11/2026 soir (son mot « le patch est accorde »).

LECTURE SEULE (REPEATABLE READ, READ ONLY) -- il n'ecrit rien en base. Trois appels, un par moment :

  photo          AVANT LA NUIT : les dossiers (uuid -> numero, pieces), le journal (dernier id), le compteur, l'empreinte
                 de la fonction -> C:\\Hektor\\chantier_classeur_q6_cache\\rejeu_patch_journal\\photo_avant_nuit_*.json
  apres-collage  SES TROIS POINTS, juste apres le collage :
                   1. la REPETITION (le fichier, lu tel quel -- un SELECT), controle par controle : 9 sur 9, ou lesquels
                   2. LA COLONNE EST LA ET REMPLIE : les lignes de fusion et de scission d'avant le patch (190 le 22/11 a
                      20:12) portent toutes leur ancien numero, AUCUNE vide
                   3. L'EMPREINTE DE LA FONCTION APRES LE PATCH, en clair : elle DOIT avoir quitte 815e956f... et doit etre
                      celle que la copie a donnee (e695bf7e...)
  matin          SON ORDRE DE DEMAIN, AVANT TOUT LE RESTE (a et b ; c est la mesure du matin, ensuite seulement) :
                   a) ses 11 551 dossiers sont-ils toujours la, avec les MEMES numeros ? -- contre la photo ; chaque
                      dossier disparu ou renumerote doit etre explique par une ligne de la nuit dans le journal, sinon ⛔
                   b) le journal a-t-il ses lignes neuves, et chaque fusion / scission porte-t-elle son ancien numero
                      (juste : la naissance de l'uuid coupe ou absorbe) ?
                 ⛔ SON MOT : « Si (a) crie, on joue l'inverse tout de suite et on ne touche a rien d'autre. »
CODES : 0 vert . 1 un rouge (nomme) . 2 pas pu lire
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache\rejeu_patch_journal")
REPETITION = RACINE / "supabase" / "patch_journal_ancien_numero_2026-11-22_REPETITION.sql"
AVANT = "815e956f716cceb6477876b774b9f885"
APRES_SUR_LA_COPIE = "e695bf7ed0ed6fcd4ec9126892305e23"
DERNIER_ID_AVANT_PATCH = 34545          # le journal au 22/11 20:12 (11 657 lignes) -- la copie du rejeu
LIGNES_A_REMPLIR = 190                  # ses fusions et scissions a cette heure-la


def dire(s: str = "") -> None:
    print(s, flush=True)


def connexion():
    import sauvegarde_datee_classeur as S
    return S.connexion()


def empreinte(cu) -> str:
    cu.execute("select md5(pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc))")
    return cu.fetchone()[0]


def colonne(cu) -> bool:
    cu.execute("select exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = "
               "'app_dossier_etiquette_journal' and column_name = 'ancien_numero')")
    return bool(cu.fetchone()[0])


def dossiers(cu) -> dict:
    cu.execute("select app_dossier_uuid::text, min(app_dossier_numero), max(app_dossier_numero), count(*), "
               "array_agg(app_affaire_id order by app_affaire_id) from public.app_affaire_ledger "
               "where app_dossier_uuid is not null group by 1")
    return {u: {"numero": n1, "numeros": 1 if n1 == n2 else 2, "pieces": list(p)} for u, n1, n2, _c, p in cu.fetchall()}


def etape_photo() -> int:
    cn, cu = connexion()
    try:
        d = dossiers(cu)
        cu.execute("select coalesce(max(id), 0), count(*) from public.app_dossier_etiquette_journal")
        jmax, jn = cu.fetchone()
        cu.execute("select annee, dernier from public.app_dossier_numero_compteur order by 1")
        cpt = {str(a): int(b) for a, b in cu.fetchall()}
        f_md5, col = empreinte(cu), colonne(cu)
        cn.rollback()
    finally:
        cn.close()
    quand = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    f = CACHE / ("photo_avant_nuit_%s.json" % quand)
    f.write_text(json.dumps({"quand": quand, "dossiers": d, "journal_max_id": jmax, "journal_lignes": jn,
                             "compteur": cpt, "fonction": f_md5, "colonne_ancien_numero": col},
                            ensure_ascii=False), encoding="utf-8")
    deux = sum(1 for x in d.values() if x["numeros"] > 1)
    dire("PHOTO D'AVANT LA NUIT (lecture seule) : %d dossiers, %d pieces etiquetees, %d dossier(s) a deux numeros ; "
         "journal %d lignes (dernier id %d) ; fonction %s ; colonne ancien_numero %s -> %s" % (
             len(d), sum(len(x["pieces"]) for x in d.values()), deux, jn, jmax, f_md5,
             "PRESENTE" if col else "ABSENTE", f))
    return 0


def etape_apres_collage() -> int:
    rouges = []
    cn, cu = connexion()
    try:
        f_md5, col = empreinte(cu), colonne(cu)
        if not col:
            dire("⛔ la colonne ancien_numero est ABSENTE : le patch n'est pas colle (fonction %s) -- code 1" % f_md5)
            cn.rollback()
            return 1
        # 1. LA REPETITION, telle quelle (un SELECT)
        cu.execute(REPETITION.read_text(encoding="utf-8"))
        rep = cu.fetchall()
        non = [r for r in rep if r[1] != "OUI"]
        dire("1. LA REPETITION : %d controle(s) sur %d disent OUI%s" % (len(rep) - len(non), len(rep),
                                                                        "" if not non else " -- ⛔ MANQUENT :"))
        for r in rep:
            dire("   %-3s %s%s" % (r[1], r[0], (" (%s)" % r[2]) if r[2] else ""))
        if non or len(rep) != 9:
            rouges.append("repetition")
        # 2. LA COLONNE EST LA ET REMPLIE : les lignes d'avant le patch
        cu.execute("select count(*), count(*) filter (where ancien_numero is not null and btrim(ancien_numero) <> ''), "
                   "count(*) filter (where ancien_numero is null or btrim(ancien_numero) = ''), "
                   "count(*) filter (where evenement = 'fusion'), count(*) filter (where evenement = 'scission') "
                   "from public.app_dossier_etiquette_journal where evenement in ('fusion', 'scission') and id <= %s",
                   (DERNIER_ID_AVANT_PATCH,))
        n, pleines, vides, nf, ns = cu.fetchone()
        ok2 = n == LIGNES_A_REMPLIR and pleines == n and vides == 0
        dire("2. LA COLONNE : %d lignes de fusion (%d) et de scission (%d) d'avant le patch ; %d portent leur ancien numero, "
             "%d VIDE(S) -- %s" % (n, nf, ns, pleines, vides, "VERT (190 / 190, aucune vide)" if ok2 else
                                   "⛔ attendu %d remplies, 0 vide" % LIGNES_A_REMPLIR))
        cu.execute("select id, evenement, dossier_numero, ancien_numero from public.app_dossier_etiquette_journal "
                   "where evenement in ('fusion', 'scission') and id <= %s order by id limit 3", (DERNIER_ID_AVANT_PATCH,))
        for r in cu.fetchall():
            dire("   ex. ligne %s %-9s numero %s <- ancien %s" % r)
        if not ok2:
            rouges.append("colonne")
        # 3. L'EMPREINTE
        ok3 = f_md5 != AVANT and f_md5 == APRES_SUR_LA_COPIE
        dire("3. L'EMPREINTE DE LA FONCTION APRES LE PATCH : %s (avant : %s) -- %s" % (
            f_md5, AVANT, "ELLE A CHANGE, et c'est celle de la copie" if ok3 else
            ("⛔ ELLE N'A PAS CHANGE : le patch n'a pas pris" if f_md5 == AVANT else
             "⛔ elle a change, mais ce n'est PAS celle de la copie (%s)" % APRES_SUR_LA_COPIE)))
        if not ok3:
            rouges.append("empreinte")
        cn.rollback()
    finally:
        cn.close()
    dire("%s" % ("⭐ VERT : le patch est pose, sa repetition 9/9, les 190 lignes remplies, l'empreinte a change"
                 if not rouges else "⛔ ROUGE : %s" % rouges))
    return 1 if rouges else 0


def etape_matin() -> int:
    photos = sorted(CACHE.glob("photo_avant_nuit_*.json"))
    if not photos:
        dire("⛔ pas de photo d'avant la nuit -- code 2")
        return 2
    ph = json.loads(photos[-1].read_text(encoding="utf-8"))
    cn, cu = connexion()
    try:
        d = dossiers(cu)
        cu.execute("select id, to_char(quand at time zone 'Europe/Paris', 'DD/MM HH24:MI'), evenement, dossier_uuid::text, "
                   "dossier_numero, autre_uuid::text, ancien_numero from public.app_dossier_etiquette_journal "
                   "where id > %s order by id", (ph["journal_max_id"],))
        jn = cu.fetchall()
        cu.execute("select dossier_uuid::text, dossier_numero from public.app_dossier_etiquette_journal "
                   "where evenement = 'pose' union all select autre_uuid::text, dossier_numero from "
                   "public.app_dossier_etiquette_journal where evenement = 'scission'")
        naissance = {u: n for u, n in cu.fetchall()}
        f_md5 = empreinte(cu)
        cn.rollback()
    finally:
        cn.close()
    rouges = []
    av = ph["dossiers"]
    # a) LES DOSSIERS, CONTRE LA PHOTO
    expliques = defaultdict(list)
    for _id, _q, ev, du, _dn, au, _an in jn:
        for u in (du, au):
            if u:
                expliques[u].append(ev)
    disparus = [u for u in av if u not in d]
    renum = [u for u in av if u in d and d[u]["numero"] != av[u]["numero"]]
    nes = [u for u in d if u not in av]
    sans_raison = [u for u in disparus + renum if not expliques.get(u)]
    dire("a) LES DOSSIERS : %d hier soir (photo %s) -> %d ce matin ; %d disparu(s), %d renumerote(s), %d ne(s) ; SANS ligne "
         "de la nuit au journal : %d -- %s" % (len(av), ph["quand"], len(d), len(disparus), len(renum), len(nes),
                                              len(sans_raison), "VERT" if not sans_raison else
                                              "⛔ ROUGE -- on joue l'INVERSE tout de suite"))
    for u in sans_raison[:10]:
        dire("   ⛔ %s %s -> %s" % (u, av[u]["numero"], d.get(u, {}).get("numero", "DISPARU")))
    if sans_raison:
        rouges.append("a")
    # b) LE JOURNAL DE LA NUIT
    cpt = Counter(r[2] for r in jn)
    fs = [r for r in jn if r[2] in ("fusion", "scission")]
    vides = [r for r in fs if not r[6]]
    faux = [r for r in fs if r[6] and r[6] != naissance.get(r[3] if r[2] == "scission" else r[5])]
    pp = [r for r in jn if r[2] in ("pose", "propagation") and r[6]]
    dire("b) LE JOURNAL DE LA NUIT : %d ligne(s) neuve(s) (%s) ; fusions et scissions : %d, dont %d SANS ancien numero et "
         "%d FAUX ; poses / propagations avec un ancien numero : %d -- %s ; fonction %s" % (
             len(jn), " . ".join("%s %d" % kv for kv in cpt.most_common()) or "aucune", len(fs), len(vides), len(faux),
             len(pp), "VERT" if not (vides or faux or pp) else "⛔ ROUGE", f_md5))
    for r in (vides + faux)[:10]:
        dire("   ⛔ ligne %s %s %s : numero %s, ancien %s" % (r[0], r[1], r[2], r[4], r[6]))
    if vides or faux or pp:
        rouges.append("b")
    dire("c) ENSUITE SEULEMENT : la mesure du matin (ce que la nuit a deplace), puis le passage.")
    return 1 if rouges else 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    etape = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if etape == "photo":
            return etape_photo()
        if etape == "apres-collage":
            return etape_apres_collage()
        if etape == "matin":
            return etape_matin()
    except Exception as e:  # noqa: BLE001
        dire("⛔ la base n'a pas pu etre lue (%s) -- code 2" % str(e).splitlines()[0][:200])
        return 2
    dire("usage : photo | apres-collage | matin")
    return 2


if __name__ == "__main__":
    sys.exit(main())
