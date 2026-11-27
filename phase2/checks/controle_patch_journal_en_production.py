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
  essais         HORS LIGNE : le juge de l'empreinte et le temoin de l'appel sur des cas fabriques (dont les temoins
                 inverses), puis le temoin de l'appel sur les VRAIS journaux du run des 20, 21, 22 et 23/11.

CORRIGE LE 23/11 AU MATIN (son mot du 23/11 (6), points 1 et 2) :
  1. L'EMPREINTE SE JUGE SANS SES RETOURS CHARIOT. Un CREATE OR REPLACE colle depuis Windows les garde : la fonction
     posee le 23/11 en porte 214, et son empreinte brute (b9fa8dea) n'est pas celle du fichier (e695bf7e). Le juge
     compare md5(replace(pg_get_functiondef(...), chr(13), '')) a e695bf7e ; l'empreinte BRUTE est AFFICHEE, avec son
     nombre de retours chariot, contre la valeur du collage. ⛔ LES DEUX ATTENDUS SONT EN DUR, et AUCUN n'est recopie de
     la production : e695bf7e vient du rejeu du 22/11 (fichier en LF), b9fa8dea du rejeu du 23/11 ou chaque fichier
     colle passe en CRLF (rejeu_sortie_23_11_tel_que_colle_CRLF.txt, ligne 14). Memoire du projet, depuis le 08/10 :
     empreinte-md5-faussee-par-fins-de-ligne-windows.
  2. LE TEMOIN DE L'APPEL. Un zero au journal est muet : il ne distingue pas « rien a poser » de « la fonction n'a pas
     ete appelee ». Le mode matin lit donc, dans CHAQUE journal du run depuis la photo, le compte rendu "etiquettes"
     ecrit par affaire_ledger.poser_les_etiquettes_de_dossier, et EXIGE « actif: true » avec ses HUIT compteurs (pose,
     propagation, fusion, scission, chacun en dossiers et en _lignes). Les trois autres formes que la fonction sait
     ecrire sont des rouges nommes : {"actif": false} seul (interrupteur eteint), "echec" (l'appel a echoue),
     "compte_rendu_illisible".
CODES : 0 vert . 1 un rouge (nomme) . 2 pas pu lire
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
CACHE = Path(r"C:\Hektor\chantier_classeur_q6_cache\rejeu_patch_journal")
LOGS = RACINE / "logs" / "scheduled"
REPETITION = RACINE / "supabase" / "patch_journal_ancien_numero_2026-11-22_REPETITION.sql"
# LA FONCTION D'AVANT : lue en production le 22/11, sans aucun retour chariot (la garde du patch, sa ligne 32, la
#   comparait BRUTE et elle est passee le 23/11) -- brute et sans retour chariot, c'est la meme.
AVANT = "815e956f716cceb6477876b774b9f885"
# LA FONCTION DU PATCH, SANS SES RETOURS CHARIOT : prouvee sur la copie par le rejeu du 22/11 (le fichier, en LF).
#   ⛔ C'EST ELLE QUI JUGE.
APRES_SANS_CR = "e695bf7ed0ed6fcd4ec9126892305e23"
# LA FONCTION DU PATCH TELLE QUE COLLEE : REPRODUITE sur la copie le 23/11 (le meme rejeu, chaque fichier colle passe
#   en CRLF), jamais recopiee de la production. Elle s'AFFICHE, elle ne juge pas.
APRES_COLLE_BRUT = "b9fa8deae9d73caa7b059918488e7f94"
CR_DU_COLLAGE = 214                     # un par ligne du corps (prosrc 10 455 = 10 241 + 214)
COMPTEURS = ("pose", "pose_lignes", "propagation", "propagation_lignes", "fusion", "fusion_lignes", "scission",
             "scission_lignes")
DERNIER_ID_AVANT_PATCH = 34545          # le journal au 22/11 20:12 (11 657 lignes) -- la copie du rejeu
LIGNES_A_REMPLIR = 190                  # ses fusions et scissions a cette heure-la


def dire(s: str = "") -> None:
    print(s, flush=True)


def connexion():
    import sauvegarde_datee_classeur as S
    return S.connexion()


def empreinte(cu) -> dict:
    """L'empreinte BRUTE, l'empreinte SANS RETOURS CHARIOT (celle qui juge), et le nombre de retours chariot."""
    cu.execute("select md5(d), md5(replace(d, chr(13), '')), length(d) - length(replace(d, chr(13), '')) "
               "from (select pg_get_functiondef('public.app_poser_etiquettes_dossier'::regproc) as d) x")
    brut, sans_cr, cr = cu.fetchone()
    return {"brut": brut, "sans_cr": sans_cr, "cr": int(cr)}


def juger_empreinte(e: dict) -> tuple[bool, str]:
    """Le juge : l'empreinte SANS retours chariot doit etre celle du patch prouve (e695bf7e). La brute est dite a cote,
    contre celle du collage reproduit sur la copie ; un autre brut au meme corps est un ⚠ nomme, pas un rouge (le corps
    est le meme : quelqu'un l'a recolle avec d'autres fins de ligne)."""
    if e["sans_cr"] == AVANT:
        return False, ("⛔ sans retours chariot %s = la fonction D'AVANT le patch (l'inverse est passe, ou le patch n'a pas "
                       "pris)" % e["sans_cr"])
    if e["sans_cr"] != APRES_SANS_CR:
        return False, ("⛔ sans retours chariot %s : ni celle d'avant (%s), ni celle du patch prouvee sur la copie (%s) -- "
                       "quelqu'un a change la fonction" % (e["sans_cr"], AVANT, APRES_SANS_CR))
    if e["brut"] == APRES_COLLE_BRUT and e["cr"] == CR_DU_COLLAGE:
        brut = "brute %s avec %d retours chariot = le collage du 23/11, reproduit sur la copie" % (e["brut"], e["cr"])
    elif e["cr"] == 0:
        brut = "brute %s, 0 retour chariot (collee sans retours chariot)" % e["brut"]
    else:
        brut = ("⚠ brute %s avec %d retours chariot : le MEME corps, mais d'autres fins de ligne que le collage du 23/11 "
                "(%s, %d) -- recollee ?" % (e["brut"], e["cr"], APRES_COLLE_BRUT, CR_DU_COLLAGE))
    return True, "sans retours chariot %s = celle du patch prouvee sur la copie ; %s" % (e["sans_cr"], brut)


def temoin_de_l_appel(texte: str) -> dict:
    """LE TEMOIN DE L'APPEL, lu dans UN journal du run (son mot du 23/11 (6), point 2).

    affaire_ledger.poser_les_etiquettes_de_dossier ecrit dans le compte rendu du run un bloc "etiquettes" et n'en
    connait que quatre formes : {"actif": false} seul (l'interrupteur est eteint, la RPC n'est pas appelee) ;
    {"actif": true, "echec": ...} (l'appel a echoue) ; {"actif": true, "compte_rendu_illisible": true} ; et le compte
    rendu complet -- les HUIT compteurs et « actif: true ». ⛔ Seule la derniere prouve l'appel."""
    plat = texte.replace("\r", "").replace("\n", "")      # la transcription coupe les longues lignes
    fin = re.search(r"=== Run quotidien termine (\S+ \S+) \(exit (\d+)\) ===", texte)
    blocs = re.findall(r'"etiquettes":\s*\{(.*?)\}', plat)
    r = {"blocs": len(blocs), "fini": bool(fin), "fin": fin.group(1) if fin else None,
         "code": int(fin.group(2)) if fin else None, "compteurs": {}, "rouge": None}
    if "la pose a echoue" in plat:
        r["rouge"] = "L'APPEL A ECHOUE (« la pose a echoue » dans le journal)"
    if len(blocs) != 1:
        r["rouge"] = r["rouge"] or ("AUCUN compte rendu \"etiquettes\" : rien ne prouve l'appel" if not blocs else
                                    "%d comptes rendus \"etiquettes\" dans un seul journal : temoin ambigu" % len(blocs))
        return r
    champs = dict(re.findall(r'"(\w+)":\s*(true|false|-?\d+)', blocs[0]))
    r["compteurs"] = {k: int(champs[k]) for k in COMPTEURS if k in champs and champs[k] not in ("true", "false")}
    manquent = [k for k in COMPTEURS if k not in r["compteurs"]]
    if r["rouge"]:
        pass
    elif '"echec"' in blocs[0]:
        r["rouge"] = "L'APPEL A ECHOUE (\"echec\" dans le compte rendu)"
    elif '"compte_rendu_illisible"' in blocs[0]:
        r["rouge"] = "COMPTE RENDU ILLISIBLE"
    elif champs.get("actif") != "true":
        r["rouge"] = "L'INTERRUPTEUR EST ETEINT (actif %s) : la fonction n'a pas ete appelee" % champs.get("actif", "absent")
    elif manquent:
        r["rouge"] = "« actif: true » SANS ses huit compteurs (manquent : %s)" % ", ".join(manquent)
    elif any(v < 0 for v in r["compteurs"].values()):
        r["rouge"] = "un compteur negatif : %s" % r["compteurs"]
    return r


def journaux_depuis(quand: str) -> list:
    """Les journaux du run (quotidien_AAAA-MM-JJ_HH-MM-SS.log) commences APRES la photo (« AAAA-MM-JJ_HHMMSS »)."""
    depuis = datetime.strptime(quand, "%Y-%m-%d_%H%M%S")
    out = []
    for f in LOGS.glob("quotidien_*.log"):
        m = re.match(r"quotidien_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.log$", f.name)
        if m and datetime.strptime(m.group(1), "%Y-%m-%d_%H-%M-%S") > depuis:
            out.append(f)
    return sorted(out)


def dire_compteurs(c: dict) -> str:
    return " . ".join("%s %s (%s lignes)" % (g, c.get(g), c.get(g + "_lignes")) for g in ("pose", "propagation", "fusion",
                                                                                       "scission"))


# ─── LE RECOUPEMENT COMPTE RENDU / JOURNAL, JUGE (son mot du 23/11 (8), § 1 -- repris a son compte par Frederic) ───
#
# LA REGLE EST ASYMETRIQUE, geste par geste -- mesuree sur les quatre nuits qui ont bouge (18-21/11), 0 ecart :
#     pose        == lignes « pose » du journal
#     propagation == lignes « propagation »
#     scission    == lignes « scission »          18/11 : 138 comptees = 138 lignes (136 dossiers coupes seulement)
#     fusion      == dossiers GARDES distincts, ET lignes >= fusion     21/11 : 30 comptees = 30 gardes (31 lignes)
#   Une FUSION reunit N etiquettes en UN geste (1 garde, N lignes) ; une SCISSION fabrique N etiquettes NEUVES (1 ligne
#   chacune). ⛔ Les « _lignes » du compte rendu sont des TRANSACTIONS, pas des lignes du journal : affichees, jamais
#   recoupees (21/11 fusion 30 / fusion_lignes 56 ; 18/11 scission 138 / 142).
# LES DEUX SENS :
#     sens 1   un geste compte qui ne trouve pas ses lignes au journal -> ROUGE, une trace perdue
#     sens 2   des lignes au journal qu'aucun geste compte ne reclame  -> ⛔⛔ ROUGE FRANC, un ECRIVAIN INCONNU (un geste
#              a la main, un patch qui se rejoue, un deuxieme run) : la question « qui a ecrit ca ? » du geste du 11/11
#   Une ligne ecrite HORS de la fenetre d'un run (entre son debut et sa fin) est du sens 2. Un evenement inconnu aussi.
# ⛔ JUGE PAR NUIT -- la fenetre du journal du run --, jamais sur tout le journal.
# ⛔ UNE LIGNE « restauration » (l'evenement du patch, pour la mise de cote) n'a jamais de geste au compte rendu : elle
#   est NOMMEE et EXCLUE, et le controle le DIT.
# ⚠ LA PREMIERE FOIS QU'UN ROUGE SORT : ON SOUPCONNE LA REGLE AVANT LE CODE. Les nuits mesurees ne portent qu'UNE fusion
#   triple (21/11) et UNE scission qui coupe un dossier en trois (18/11).
GESTES = ("pose", "propagation", "fusion", "scission")
EXCLUS_DU_RECOUPEMENT = ("restauration",)


def fenetre(f: Path, t: dict) -> tuple:
    """La fenetre d'un run : de l'heure de son journal (le nom du fichier) a sa ligne de fin ; pas fini -> None."""
    m = re.match(r"quotidien_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.log$", f.name)
    debut = datetime.strptime(m.group(1), "%Y-%m-%d_%H-%M-%S")
    return debut, (datetime.strptime(t["fin"], "%Y-%m-%d %H:%M:%S") if t["fin"] else None)


def recouper(nuits: list, lignes: list, maintenant: datetime) -> dict:
    """LE JUGE DU RECOUPEMENT, pur (sans base ni fichier).
    nuits  : [{"nom", "debut", "fin" (None = run pas fini : jusqu'a maintenant), "compteurs" (les huit, ou incomplets
             si son temoin de l'appel est rouge)}]
    lignes : [(id, quand -- heure de Paris, sans fuseau --, evenement, dossier_uuid)] : TOUTES les lignes du journal de
             la periode jugee (depuis la photo, ou depuis le debut du premier run).
    Rend {"nuits": [{"nom", "texte", "rouges"}], "hors_fenetre": [...], "exclues": [...], "rouges": [...]}."""
    par_nuit = defaultdict(list)
    hors, exclues = [], []
    for ligne in lignes:
        _id, quand, ev, _du = ligne
        if ev in EXCLUS_DU_RECOUPEMENT:
            exclues.append(ligne)
            continue
        n = next((x["nom"] for x in nuits if x["debut"] <= quand <= (x["fin"] or maintenant)), None)
        if n is None:
            hors.append(ligne)
        else:
            par_nuit[n].append(ligne)
    out = {"nuits": [], "hors_fenetre": hors, "exclues": exclues, "rouges": []}
    for x in nuits:
        c, ls, rg = x["compteurs"], par_nuit.get(x["nom"], []), []
        cpt = Counter(l[2] for l in ls)
        gardes = len({l[3] for l in ls if l[2] == "fusion"})
        if any(g not in c for g in GESTES):
            rg.append("PAS JUGEABLE : son temoin de l'appel est rouge, le compte rendu n'a pas ses compteurs (%d ligne(s) "
                      "au journal dans sa fenetre)" % len(ls))
        else:
            for g in ("pose", "propagation", "scission"):
                if cpt[g] < c[g]:
                    rg.append("sens 1 -- %s : le run en compte %d, le journal n'en garde que %d ligne(s) : TRACE PERDUE"
                              % (g, c[g], cpt[g]))
                elif cpt[g] > c[g]:
                    rg.append("⛔⛔ sens 2 -- %s : le journal porte %d ligne(s), le run n'en reclame que %d : un ECRIVAIN "
                              "INCONNU" % (g, cpt[g], c[g]))
            if gardes < c["fusion"]:
                rg.append("sens 1 -- fusion : le run en compte %d, le journal n'en garde que %d dossier(s) garde(s) : "
                          "TRACE PERDUE" % (c["fusion"], gardes))
            elif gardes > c["fusion"]:
                rg.append("⛔⛔ sens 2 -- fusion : le journal porte %d dossier(s) garde(s), le run n'en reclame que %d : un "
                          "ECRIVAIN INCONNU" % (gardes, c["fusion"]))
            if cpt["fusion"] < c["fusion"]:
                rg.append("sens 1 -- fusion : %d ligne(s) pour %d fusion(s) comptee(s) (attendu lignes >= fusion)"
                          % (cpt["fusion"], c["fusion"]))
            inconnus = sorted(set(cpt) - set(GESTES))
            if inconnus:
                rg.append("⛔⛔ sens 2 -- evenement(s) INCONNU(S) au journal : %s" % ", ".join(
                    "%s %d" % (e, cpt[e]) for e in inconnus))
        texte = ("run %s : pose %s/%d . propagation %s/%d . fusion %s/%d garde(s) (%d ligne(s)) . scission %s/%d   "
                 "[compte rendu / journal ; les _lignes, transactions, affichees non jugees : %s]" % (
                     x["nom"], c.get("pose"), cpt["pose"], c.get("propagation"), cpt["propagation"], c.get("fusion"),
                     gardes, cpt["fusion"], c.get("scission"), cpt["scission"],
                     " . ".join("%s %s" % (g + "_lignes", c.get(g + "_lignes")) for g in GESTES)))
        out["nuits"].append({"nom": x["nom"], "texte": texte, "rouges": rg})
        out["rouges"] += ["%s : %s" % (x["nom"], r) for r in rg]
    if hors:
        out["rouges"].append("⛔⛔ sens 2 -- %d ligne(s) du journal ecrite(s) HORS de toute fenetre de run : un ECRIVAIN "
                             "INCONNU (ids %s)" % (len(hors), [l[0] for l in hors[:10]]))
    return out


def dire_recoupement(r: dict) -> None:
    for x in r["nuits"]:
        dire("   %s -- %s" % (x["texte"], "VERT" if not x["rouges"] else "⛔ ROUGE"))
        for t in x["rouges"]:
            dire("      ⛔ " + t)
    for l in r["hors_fenetre"][:10]:
        dire("      ⛔⛔ HORS FENETRE : ligne %s du %s, %s, dossier %s" % (l[0], l[1], l[2], l[3]))
    dire("   lignes « restauration » nommees et EXCLUES du recoupement (l'evenement du patch, aucun geste ne la compte) : "
         "%d%s" % (len(r["exclues"]), (" -- ids %s" % [l[0] for l in r["exclues"][:20]]) if r["exclues"] else ""))


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
         "journal %d lignes (dernier id %d) ; fonction sans retours chariot %s (brute %s, %d retours chariot) ; colonne "
         "ancien_numero %s -> %s" % (len(d), sum(len(x["pieces"]) for x in d.values()), deux, jn, jmax, f_md5["sans_cr"],
                                     f_md5["brut"], f_md5["cr"], "PRESENTE" if col else "ABSENTE", f))
    return 0


def etape_apres_collage() -> int:
    rouges = []
    cn, cu = connexion()
    try:
        f_md5, col = empreinte(cu), colonne(cu)
        if not col:
            dire("⛔ la colonne ancien_numero est ABSENTE : le patch n'est pas colle (fonction sans retours chariot %s) "
                 "-- code 1" % f_md5["sans_cr"])
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
        # 3. L'EMPREINTE -- jugee SANS ses retours chariot (corrige le 23/11, voir l'en-tete)
        ok3, texte3 = juger_empreinte(f_md5)
        dire("3. L'EMPREINTE DE LA FONCTION APRES LE PATCH (avant : %s) : %s -- %s" % (
            AVANT, texte3, "VERT" if ok3 else "ROUGE"))
        if not ok3:
            rouges.append("empreinte")
        cn.rollback()
    finally:
        cn.close()
    dire("%s" % ("⭐ VERT : le patch est pose, sa repetition 9/9, les 190 lignes remplies, l'empreinte (sans retours "
                 "chariot) est celle du patch prouve" if not rouges else "⛔ ROUGE : %s" % rouges))
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
        cu.execute("select id, quand at time zone 'Europe/Paris', evenement, dossier_uuid::text "
                   "from public.app_dossier_etiquette_journal where id > %s order by id", (ph["journal_max_id"],))
        lignes_heure = cu.fetchall()
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
    # a bis) LA FONCTION EST TOUJOURS CELLE DU PATCH -- jugee SANS ses retours chariot (corrige le 23/11)
    ok_f, texte_f = juger_empreinte(f_md5)
    dire("a bis) LA FONCTION : %s -- %s" % (texte_f, "VERT" if ok_f else "ROUGE"))
    if not ok_f:
        rouges.append("fonction")
    # b) LE JOURNAL DE LA NUIT
    cpt = Counter(r[2] for r in jn)
    fs = [r for r in jn if r[2] in ("fusion", "scission")]
    vides = [r for r in fs if not r[6]]
    faux = [r for r in fs if r[6] and r[6] != naissance.get(r[3] if r[2] == "scission" else r[5])]
    pp = [r for r in jn if r[2] in ("pose", "propagation") and r[6]]
    dire("b) LE JOURNAL DE LA NUIT : %d ligne(s) neuve(s) (%s) ; fusions et scissions : %d, dont %d SANS ancien numero et "
         "%d FAUX ; poses / propagations avec un ancien numero : %d -- %s" % (
             len(jn), " . ".join("%s %d" % kv for kv in cpt.most_common()) or "aucune", len(fs), len(vides), len(faux),
             len(pp), "VERT" if not (vides or faux or pp) else "⛔ ROUGE"))
    for r in (vides + faux)[:10]:
        dire("   ⛔ ligne %s %s %s : numero %s, ancien %s" % (r[0], r[1], r[2], r[4], r[6]))
    if vides or faux or pp:
        rouges.append("b")
    # b bis) LE TEMOIN DE L'APPEL (son mot du 23/11 (6), point 2) : sans lui, un zero au journal est muet
    nuits = journaux_depuis(ph["quand"])
    if not nuits:
        dire("b bis) LE TEMOIN DE L'APPEL : AUCUN journal du run commence apres la photo (%s) dans %s -- ⛔ ROUGE : rien "
             "ne prouve que la fonction a ete appelee, un zero au journal ne se croit pas" % (ph["quand"], LOGS))
        rouges.append("temoin")
    fenetres = []
    for f in nuits:
        t = temoin_de_l_appel(f.read_text(encoding="utf-8", errors="replace"))
        debut, fin_run = fenetre(f, t)
        fenetres.append({"nom": f.name, "debut": debut, "fin": fin_run, "compteurs": t["compteurs"]})
        dire("b bis) LE TEMOIN DE L'APPEL, %s : run %s (code %s, %s) ; %s" % (
            f.name, "fini" if t["fini"] else "⚠ PAS FINI", t["code"], t["fin"],
            ("« actif: true » et ses huit compteurs : %s -- VERT, la fonction a ete appelee" % dire_compteurs(t["compteurs"]))
            if not t["rouge"] else "⛔ ROUGE : " + t["rouge"]))
        if t["rouge"]:
            rouges.append("temoin")
    if nuits and "temoin" not in rouges and not jn:
        dire("   ⭐ le zero du journal veut donc dire « rien a poser », pas « pas appelee »")
    # b ter) LE RECOUPEMENT, JUGE PAR NUIT, DANS LES DEUX SENS (son mot du 23/11 (8), § 1)
    rec = recouper(fenetres, lignes_heure, datetime.now())
    dire("b ter) LE RECOUPEMENT compte rendu / journal, par nuit, dans les deux sens : %s" % (
        "VERT" if not rec["rouges"] else "⛔ ROUGE (%d) -- ⚠ ON SOUPCONNE LA REGLE AVANT LE CODE" % len(rec["rouges"])))
    dire_recoupement(rec)
    if rec["rouges"]:
        rouges.append("recoupement")
    dire("c) ENSUITE SEULEMENT : la mesure du matin (ce que la nuit a deplace), puis le passage.")
    return 1 if rouges else 0


def etape_essais() -> int:
    """HORS LIGNE : les deux juges sur des cas fabriques (temoins inverses compris), puis sur les vrais journaux."""
    echecs = []

    def exige(nom: str, ok: bool, detail: str = "") -> None:
        dire("   %s %s%s" % ("OUI" if ok else "NON", nom, (" (%s)" % detail) if detail else ""))
        if not ok:
            echecs.append(nom)

    dire("1. LE JUGE DE L'EMPREINTE")
    ok, t = juger_empreinte({"brut": APRES_COLLE_BRUT, "sans_cr": APRES_SANS_CR, "cr": CR_DU_COLLAGE})
    exige("le collage du 23/11 (b9fa8dea brute, e695bf7e sans CR, 214 CR) est VERT", ok and "⚠" not in t, t)
    ok, t = juger_empreinte({"brut": APRES_SANS_CR, "sans_cr": APRES_SANS_CR, "cr": 0})
    exige("le fichier colle sans CR (e695bf7e des deux cotes) est VERT", ok and "⚠" not in t, t)
    ok, t = juger_empreinte({"brut": "0" * 32, "sans_cr": APRES_SANS_CR, "cr": 7})
    exige("le meme corps recolle avec d'autres fins de ligne : VERT, avec son ⚠ nomme", ok and "⚠" in t, t)
    ok, t = juger_empreinte({"brut": AVANT, "sans_cr": AVANT, "cr": 0})
    exige("TEMOIN INVERSE : la fonction d'avant (815e956f) est ROUGE", not ok, t)
    ok, t = juger_empreinte({"brut": "9581f8d2a287da5a1ed8890238566858", "sans_cr": AVANT, "cr": 214})
    exige("TEMOIN INVERSE : l'inverse colle (9581f8d2 brute, 815e956f sans CR) est ROUGE", not ok, t)
    ok, t = juger_empreinte({"brut": APRES_COLLE_BRUT, "sans_cr": "1" * 32, "cr": CR_DU_COLLAGE})
    exige("TEMOIN INVERSE : la brute du collage avec un AUTRE corps est ROUGE (la brute ne juge pas)", not ok, t)

    dire("2. LE TEMOIN DE L'APPEL, cas fabriques")
    plein = ('"etiquettes": {"pose": 0, "pose_lignes": 0, "propagation": 0, "propagation_lignes": 0, "fusion": 0, '
             '"fusion_lignes": 0, "scission": 0, "scission_lignes": 0, "actif": true}')
    fin = "\n=== Run quotidien termine 2026-11-23 06:33:25 (exit 0) ===\n"
    r = temoin_de_l_appel(plein + fin)
    exige("le compte rendu complet a zero est VERT", r["rouge"] is None and len(r["compteurs"]) == 8, str(r))
    coupe = plein.replace('"fusion_lignes": 0, ', '"fusion_li\r\ngnes": 0, ')
    r = temoin_de_l_appel(coupe.replace('"pose": 0, ', '"pose":\n 0, ') + fin)
    exige("une ligne coupee par la transcription se recolle (VERT)", r["rouge"] is None, str(r))
    for nom, texte in (("{\"actif\": false} seul (interrupteur eteint)", '"etiquettes": {"actif": false}'),
                       ("\"echec\" (l'appel a echoue)", '"etiquettes": {"actif": true, "echec": "HTTP 500"}'),
                       ("« la pose a echoue » au journal", plein + "\n[affaire_ledger] ETIQUETTES : la pose a echoue"),
                       ("compte rendu illisible", '"etiquettes": {"actif": true, "compte_rendu_illisible": true}'),
                       ("« actif: true » a SEPT compteurs", plein.replace('"scission_lignes": 0, ', '')),
                       ("aucun compte rendu", "le run a tourne sans rien dire"),
                       ("deux comptes rendus", plein + "\n" + plein)):
        r = temoin_de_l_appel(texte + fin)
        exige("TEMOIN INVERSE : %s est ROUGE" % nom, r["rouge"] is not None, r["rouge"] or "")

    dire("3. LE TEMOIN DE L'APPEL, sur les VRAIS journaux du run")
    # les compteurs NON NULS de chaque nuit, tels que les journaux les portent (lus le 23/11) -- un temoin POSITIF : la
    #   fonction sait dire qu'elle a bouge, et le juge le lit
    attendus = {"2026-11-20": {"propagation": 4, "propagation_lignes": 4, "fusion": 10, "fusion_lignes": 10},
                "2026-11-21": {"pose": 2, "pose_lignes": 2, "propagation": 3, "propagation_lignes": 3, "fusion": 30,
                               "fusion_lignes": 56},
                "2026-11-22": {}, "2026-11-23": {}}
    for jour, attendu in attendus.items():
        fs = sorted(LOGS.glob("quotidien_%s_*.log" % jour))
        if not fs:
            exige("le journal du run du %s existe" % jour, False)
            continue
        r = temoin_de_l_appel(fs[-1].read_text(encoding="utf-8", errors="replace"))
        non_nuls = {k: v for k, v in r["compteurs"].items() if v}
        exige("%s : VERT, run fini en code 0, et ses compteurs non nuls sont %s" % (jour, attendu or "aucun"),
              r["rouge"] is None and r["fini"] and r["code"] == 0 and non_nuls == attendu,
              "%s . %s" % (r["rouge"] or "appelee", dire_compteurs(r["compteurs"])))
    dire("4. LE RECOUPEMENT, cas fabriques sur la forme des deux nuits qui decident la regle")
    d21, f21 = datetime(2026, 11, 21, 4, 0, 2), datetime(2026, 11, 21, 6, 44, 19)
    q21 = datetime(2026, 11, 21, 6, 20, 4)
    c21 = {"pose": 2, "pose_lignes": 2, "propagation": 3, "propagation_lignes": 3, "fusion": 30, "fusion_lignes": 56,
           "scission": 0, "scission_lignes": 0}
    # 21/11 : 2 poses, 3 propagations, 31 lignes de fusion sur 30 dossiers gardes (le garde g0 absorbe deux etiquettes)
    l21 = ([(i, q21, "pose", "p%d" % i) for i in range(2)] + [(10 + i, q21, "propagation", "q%d" % i) for i in range(3)]
           + [(100 + i, q21, "fusion", "g%d" % i) for i in range(30)] + [(130, q21, "fusion", "g0")])
    d18, f18 = datetime(2026, 11, 18, 4, 0, 1), datetime(2026, 11, 18, 6, 40, 0)
    q18 = datetime(2026, 11, 18, 6, 15, 0)
    c18 = {"pose": 0, "pose_lignes": 0, "propagation": 0, "propagation_lignes": 0, "fusion": 0, "fusion_lignes": 0,
           "scission": 138, "scission_lignes": 142}
    # 18/11 : 138 lignes de scission sur 136 dossiers coupes (deux dossiers coupes en trois)
    l18 = [(200 + i, q18, "scission", "s%d" % (i if i < 136 else i - 136)) for i in range(138)]

    def nuit(nom, d, f, c):
        return {"nom": nom, "debut": d, "fin": f, "compteurs": dict(c)}

    maintenant = datetime(2026, 11, 23, 9, 0)
    r = recouper([nuit("21/11", d21, f21, c21), nuit("18/11", d18, f18, c18)], l21 + l18, maintenant)
    exige("les deux nuits telles quelles sont VERTES (fusion = 30 gardes sur 31 lignes ; scission = 138 lignes sur 136 "
          "dossiers)", not r["rouges"], str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, dict(c21, fusion=31))], l21, maintenant)
    exige("TEMOIN INVERSE de la FUSION : le compte rendu dit 31 au lieu de 30 -> ROUGE (sens 1 : 30 gardes, compter les "
          "lignes serait faux)", any("sens 1 -- fusion" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("18/11", d18, f18, dict(c18, scission=136))], l18, maintenant)
    exige("TEMOIN INVERSE de la SCISSION : le compte rendu dit 136 au lieu de 138 -> ROUGE (sens 2 : 138 lignes, compter "
          "les dossiers serait faux)", any("sens 2 -- scission" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, dict(c21, pose=3))], l21, maintenant)
    exige("TEMOIN INVERSE de la POSE : 3 comptees pour 2 lignes -> ROUGE (sens 1)",
          any("sens 1 -- pose" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, dict(c21, propagation=2))], l21, maintenant)
    exige("TEMOIN INVERSE de la PROPAGATION : 2 comptees pour 3 lignes -> ROUGE (sens 2)",
          any("sens 2 -- propagation" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, c21)], l21 + [(999, datetime(2026, 11, 21, 14, 0), "fusion", "g5")], maintenant)
    exige("TEMOIN INVERSE du sens 2 : une ligne ecrite a 14:00, HORS du run -> ROUGE (ecrivain inconnu)",
          any("HORS de toute fenetre" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, c21)], l21 + [(998, q21, "fusion", "g31")], maintenant)
    exige("TEMOIN INVERSE du sens 2 : une fusion de plus DANS la fenetre (31 gardes pour 30) -> ROUGE",
          any("sens 2 -- fusion" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, c21)], l21 + [(997, q21, "renumerotation", "x")], maintenant)
    exige("TEMOIN INVERSE : un evenement INCONNU au journal -> ROUGE (sens 2)",
          any("INCONNU" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, c21)], l21 + [(996, datetime(2026, 11, 21, 15, 0), "restauration", "m1")],
                 maintenant)
    exige("une ligne « restauration » est NOMMEE et EXCLUE, meme hors fenetre (VERT, 1 exclue)",
          not r["rouges"] and len(r["exclues"]) == 1, str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, dict(c21, fusion_lignes=999, scission_lignes=7))], l21, maintenant)
    exige("les « _lignes » ne sont PAS jugees (fusion_lignes 999 : VERT)", not r["rouges"], str(r["rouges"]))
    r = recouper([nuit("21/11", d21, f21, {})], l21, maintenant)
    exige("une nuit dont le temoin de l'appel est rouge -> PAS JUGEABLE, ROUGE",
          any("PAS JUGEABLE" in x for x in r["rouges"]), str(r["rouges"]))
    r = recouper([nuit("23/11", datetime(2026, 11, 23, 4, 0, 2), None, dict(c21, pose=0, propagation=0, fusion=0,
                                                                           fusion_lignes=0))],
                 [(995, datetime(2026, 11, 23, 8, 0), "pose", "z")], maintenant)
    exige("TEMOIN INVERSE : un run PAS FINI juge jusqu'a maintenant -- une pose au journal sans geste compte -> ROUGE",
          any("sens 2 -- pose" in x for x in r["rouges"]), str(r["rouges"]))
    dire("%s" % ("⭐ ESSAIS : tout est vert" if not echecs else "⛔ ESSAIS : %d NON -- %s" % (len(echecs), echecs)))
    return 1 if echecs else 0


def etape_nuits() -> int:
    """LE RECOUPEMENT REJOUE SUR LES VRAIES NUITS (lecture seule) : chaque journal du run qui porte un compte rendu
    "etiquettes" (le premier est celui du 13/11), contre TOUTES les lignes du journal ecrites depuis le debut du premier
    -- celles d'entre les runs comprises (le sens 2)."""
    nuits = []
    for f in sorted(LOGS.glob("quotidien_*.log")):
        if not re.match(r"quotidien_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.log$", f.name):
            continue
        texte = f.read_text(encoding="utf-8", errors="replace")
        if '"etiquettes"' not in texte.replace("\r", "").replace("\n", ""):
            if nuits:          # apres le premier, une nuit SANS compte rendu est un trou : on la garde, elle criera
                t = temoin_de_l_appel(texte)
                d, fi = fenetre(f, t)
                nuits.append({"nom": f.name, "debut": d, "fin": fi, "compteurs": {}})
            continue
        t = temoin_de_l_appel(texte)
        d, fi = fenetre(f, t)
        nuits.append({"nom": f.name, "debut": d, "fin": fi, "compteurs": t["compteurs"] if not t["rouge"] else {}})
    if not nuits:
        dire("⛔ aucun journal du run avec un compte rendu \"etiquettes\" dans %s -- code 2" % LOGS)
        return 2
    cn, cu = connexion()
    try:
        cu.execute("select id, quand at time zone 'Europe/Paris', evenement, dossier_uuid::text "
                   "from public.app_dossier_etiquette_journal where quand at time zone 'Europe/Paris' >= %s order by id",
                   (nuits[0]["debut"],))
        lignes = cu.fetchall()
        cu.execute("select count(*), min(quand at time zone 'Europe/Paris') from public.app_dossier_etiquette_journal "
                   "where quand at time zone 'Europe/Paris' < %s", (nuits[0]["debut"],))
        avant, plus_ancienne = cu.fetchone()
        cn.rollback()
    finally:
        cn.close()
    dire("LE RECOUPEMENT SUR LES VRAIES NUITS (lecture seule) : %d run(s), du %s au %s ; %d ligne(s) du journal depuis le "
         "debut du premier (%d avant, non jugees : la pose initiale et ce qui l'a precedee, depuis le %s)" % (
             len(nuits), nuits[0]["nom"], nuits[-1]["nom"], len(lignes), avant, plus_ancienne))
    rec = recouper(nuits, lignes, datetime.now())
    dire_recoupement(rec)
    dire("%s" % ("⭐ VERT : chaque nuit, chaque geste compte a ses lignes, et chaque ligne a son geste" if not rec["rouges"]
                 else "⛔ ROUGE (%d) -- ⚠ ON SOUPCONNE LA REGLE AVANT LE CODE :\n   %s" % (
                     len(rec["rouges"]), "\n   ".join(rec["rouges"][:20]))))
    return 1 if rec["rouges"] else 0


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
        if etape == "essais":
            return etape_essais()
        if etape == "nuits":
            return etape_nuits()
    except Exception as e:  # noqa: BLE001
        dire("⛔ la base n'a pas pu etre lue (%s) -- code 2" % str(e).splitlines()[0][:200])
        return 2
    dire("usage : photo | apres-collage | matin | essais | nuits")
    return 2


if __name__ == "__main__":
    sys.exit(main())
