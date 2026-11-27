#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""LE TEMOIN DU RATTACHEMENT 3648 -> 3647 -- MESURE DANS LE REGISTRE, JAMAIS LU DANS LE COMPTE RENDU. LECTURE SEULE.

    python -X utf8 -u phase2\checks\temoin_du_rattachement_de_3648_2026-11-27.py

SON MOT (26/11) : « demain matin, ne me donne pas le compte rendu de la nuit : donne-moi le temoin. Ton propre module porte
cette note, ecrite apres un echec : indexes par un entier au lieu d'un texte, les rattachements etaient ignores en silence
[...] le compte rendu disait « 6 lignes » et rien n'etait fait [...] Alors demain : 3648 est-elle reellement dans la chaine
3647, et D2024-0306 a-t-il bien fusionne ? Mesure, pas rapporte. »

⏰ A LANCER APRES 07:30 (son mot : ni le run ni la descente ne doivent tourner). Lancé AVANT la nuit qui pose la ligne, il
DOIT repondre « PAS REUNIE » -- c'est son temoin inverse, pris le 26/11.

CE QU'IL MESURE, aux deux endroits ou vit le dossier :
  ① phase2.sqlite (mode=ro), le registre MAITRE : la chaine de 3646, 3647, 3648, 3649, 3650 ;
  ② Supabase : la meme chose + l'etiquette (uuid, numero) de chaque piece ; qui porte encore D2024-0306 ; le journal des
     etiquettes (une fusion de 445c3170 dans 42dd4d66, nommant 3648) ; le compteur ;
  ③ le temoin POSITIF du mecanisme : les 16 autres rattachements du fichier sont-ils reunis, eux aussi ?
  ④ LE JOURNAL DE LA NUIT (ajoute le 26/11 sur son mot) -- « Reunie « oui » ne dit pas par quoi : si une regle l'avait
     rapprochee d'elle-meme, ou si notre ligne n'avait pas ete appliquee du tout, le temoin dirait oui dans les deux cas. »
     Le mecanisme ecrit CINQ messages (affaire_ledger.py, boucle « LES RATTACHEMENTS DECIDES A LA MAIN ») :
         « [M] rattachement decide a la main »                          <- le SEUL attendu
         « [M] rattachement manuel : le bien ne correspond pas »        \
         « [M] rattachement manuel : transaction introuvable »           |  chacun doit etre ABSENT
         « [M] rattachement manuel deja obtenu par une regle »           |  (et tout autre message « [M] »)
         « [M] ⚠ rattachement manuel : DEUX VENTES dans le dossier »    /
     ⚠ LE JOURNAL NE NOMME PAS LE BIEN : signale() compte par LIBELLE (anomalies[quoi] += 1). La preuve se lit donc ainsi :
       chaque ligne du fichier, sur son bien, produit EXACTEMENT UN des quatre premiers messages (la boucle fait `continue`
       apres chaque refus) -> « lignes lues » = « decide a la main » = le nombre de lignes du fichier, ET aucun autre
       message « [M] », veut dire que CHAQUE ligne, la notre comprise, a ete appliquee A LA MAIN -- ni refusee, ni deja
       obtenue par une regle. Plus : l'etape est DONE, le journal est posterieur a la derniere ecriture du fichier, et la
       ligne « etiquettes : ... fusion N » porte N >= 1.
     Le LECTEUR a son temoin inverse a chaque lancement : un journal truque EN MEMOIRE (un refus ajoute, un compte change)
     doit le faire crier -- sinon un journal sans refus ne prouverait rien.
  ⑤ LE BIEN NOMME : la vraie recalculer_les_chaines rejouee sur une copie EN MEMOIRE du registre du matin, avec un fichier
     temporaire qui ne porte QUE la ligne 3648 (aucune autre decision n'est sur le bien 8395, verifie le 26/11) : ses
     messages « [M] » sont donc ceux du bien 8395 et de lui seul -> exactement { « decide a la main » : 1 }.
     ⚠ C'est un REJEU sur les donnees du matin, pas l'enregistrement de la nuit (qui est ④).
Sortie : 0 reunie et fusionnee . 1 pas (encore) reunie . 2 pas pu mesurer.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402
import phase2.sync.affaire_ledger as al  # noqa: E402

PIECES = (3646, 3647, 3648, 3649, 3650)
U_0511, U_0306 = "42dd4d66-eb07-47b6-85d6-8db1e7000090", "445c3170"
JOURNAUX = RACINE / "logs" / "scheduled"
ATTENDU = "[M] rattachement decide a la main"
LES_AUTRES = ("[M] rattachement manuel : le bien ne correspond pas", "[M] rattachement manuel : transaction introuvable",
              "[M] rattachement manuel deja obtenu par une regle", "[M] ⚠ rattachement manuel : DEUX VENTES dans le dossier")
ETAPE = "phase2 affaire ledger refresh+push"


def lire_le_journal(texte: str) -> dict:
    """Le bloc du chainage dans le journal de la nuit -> ce qu'il dit, sans rien supposer. Un bloc absent ou en double
    rend « illisible » (le temoin dit alors « pas pu mesurer », jamais « oui »)."""
    lus = re.findall(r'"chainage_rattachements_manuels":\s*(\d+)', texte)
    if len(lus) != 1:
        return {"illisible": "%d bloc(s) « chainage_rattachements_manuels » (attendu 1)" % len(lus)}
    m_ = dict()
    for cle, n in re.findall(r'"(\[M\][^"]*)":\s*(\d+)', texte):
        m_[cle] = m_.get(cle, 0) + int(n)
    et = re.findall(r"etiquettes : pose (\d+) \. propagation (\d+) \. fusion (\d+) \. scission (\d+)", texte)
    return {"lus": int(lus[0]), "decide": m_.get(ATTENDU, 0), "autres": {k: v for k, v in m_.items() if k != ATTENDU},
            "fusion": int(et[-1][2]) if len(et) == 1 else None, "lignes_etiquettes": len(et),
            "fait": ("DONE  " + ETAPE) in texte, "echec": bool(re.search(r"FAIL\w*\s+" + re.escape(ETAPE), texte))}


def juger_le_journal(j: dict, n_fichier: int) -> list[str]:
    """[] = le journal dit que CHAQUE ligne du fichier a ete appliquee a la main ; sinon la liste nommee des ecarts."""
    if "illisible" in j:
        return [j["illisible"]]
    pas = []
    if not j["fait"] or j["echec"]:
        pas.append("l'etape « %s » n'est pas DONE" % ETAPE)
    if not (j["lus"] == j["decide"] == n_fichier):
        pas.append("lignes lues %d, « decide a la main » %d, lignes du fichier %d (attendu : les trois egaux)"
                   % (j["lus"], j["decide"], n_fichier))
    if j["autres"]:
        pas.append("message(s) « [M] » qui ne devraient pas etre la : %s" % j["autres"])
    if j["fusion"] is None:
        pas.append("%d ligne(s) « etiquettes : ... » (attendu 1)" % j["lignes_etiquettes"])
    elif j["fusion"] < 1:
        pas.append("etiquettes : fusion %d (attendu >= 1 : D2024-0306 dans D2024-0511)" % j["fusion"])
    return pas


def rejeu_du_seul_bien_8395(ligne: str | None) -> dict:
    """⑤ La vraie fonction de nuit sur une copie en memoire du registre du matin, avec SEULEMENT la ligne 3648."""
    spec = importlib.util.spec_from_file_location("rejeu3648", ICI / "rejouer_le_rattachement_de_3648_2026-11-26.py")
    R = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R)
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "seule_3648.csv"
        f.write_text((ligne + "\n") if ligne else "", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            chaines, compte = R.rejouer(f)
    return {"chaine_3648": chaines.get(3648), "M": {k: v for k, v in compte.items() if k.startswith("[M]")}}


def main() -> int:
    ok = True
    print("① LE REGISTRE LOCAL (maitre), phase2.sqlite en lecture seule")
    lo = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(), uri=True)
    L = {int(a): int(c) for a, c in lo.execute("select app_affaire_id, app_chaine_id from app_affaire_ledger where "
                                               "app_affaire_id in (%s)" % ",".join(map(str, PIECES)))}
    print("   chaines : %s" % L)
    reunie_local = L.get(3648) == L.get(3647) == L.get(3650) == 3647 and L.get(3646) == L.get(3649) == 3646
    print("   3648 dans la chaine 3647 (et 427UDDSF sur 3646) : %s" % ("OUI" if reunie_local else "⛔ NON"))
    ok &= reunie_local
    try:
        cn, cu = P.pooler()
    except Exception as e:  # noqa: BLE001
        print("⛔ Supabase illisible (%s) -- pas de verdict (code 2)" % str(e)[:120])
        return 2
    print("\n② SUPABASE")
    cu.execute("select app_affaire_id, kind, state, app_chaine_id, app_dossier_uuid::text, app_dossier_numero "
               "from public.app_affaire_ledger where app_affaire_id = any(%s) order by 1", (list(PIECES),))
    S = {r[0]: r[1:] for r in cu.fetchall()}
    for a, r in S.items():
        print("   %s %-9s %-9s chaine %s  %s %s" % (a, r[0], r[1], r[2], r[3][:8], r[4]))
    reunie_sb = (S[3648][2] == S[3647][2] == 3647 and S[3648][3] == S[3647][3] == S[3650][3] == U_0511
                 and S[3646][3] == S[3649][3] and S[3646][3] != U_0511)
    print("   3648 en chaine 3647 ET sur D2024-0511 (42dd4d66) ; 427UDDSF a part : %s" % ("OUI" if reunie_sb else "⛔ NON"))
    ok &= reunie_sb
    cu.execute("select count(*), array_agg(app_affaire_id) from public.app_affaire_ledger where app_dossier_numero = 'D2024-0306'")
    n0306, qui = cu.fetchone()
    print("   pieces qui portent encore D2024-0306 : %d %s" % (n0306, qui or []))
    ok &= n0306 == 0
    cu.execute("select quand, evenement, dossier_numero, ancien_numero, transactions, pourquoi from "
               "public.app_dossier_etiquette_journal where (autre_uuid::text like %s or 3648 = any(transactions)) "
               "and quand > '2026-11-26' order by quand", (U_0306 + "%",))
    J = cu.fetchall()
    for r in J:
        print("   journal : %s %s %s <- %s %s (%s)" % (str(r[0])[:19], r[1], r[2], r[3], r[4], (r[5] or "")[:60]))
    fus = [r for r in J if r[1] == "fusion" and r[2] == "D2024-0511" and r[3] == "D2024-0306"]
    print("   une FUSION de D2024-0306 dans D2024-0511 au journal depuis le 26/11 : %s" % ("OUI" if fus else "⛔ NON"))
    ok &= bool(fus)
    print("\n③ LE TEMOIN POSITIF DU MECANISME : les autres rattachements du fichier, reunis dans Supabase ?")
    dec = [d for d in al.lire_rattachements_manuels() if d[0] != 3648]
    ids = sorted({x for s, c, _b, _p in dec for x in (s, c)})
    cu.execute("select app_affaire_id, app_chaine_id from public.app_affaire_ledger where app_affaire_id = any(%s)", (ids,))
    ch = dict(cu.fetchall())
    pas = [(s, c) for s, c, _b, _p in dec if ch.get(s) is None or ch.get(s) != ch.get(c)]
    print("   %d decision(s) hors 3648 : %d reunies, %d pas %s" % (len(dec), len(dec) - len(pas), len(pas), pas))
    cn.rollback()
    cn.close()

    print("\n④ LE JOURNAL DE LA NUIT -- par QUOI elle est reunie (le bon libelle, et l'absence des quatre autres)")
    fichier = al.lire_rattachements_manuels()
    ligne_3648 = [d for d in fichier if d[0] == 3648]
    print("   le fichier : %d ligne(s) lue(s) ; la ligne 3648 : %s" % (
        len(fichier), "OUI, %s, commentaire %r" % (ligne_3648[0][:3], ligne_3648[0][3][:40] + "...") if ligne_3648
        else "⛔ ABSENTE"))
    ok &= bool(ligne_3648) and ligne_3648[0][:3] == (3648, 3647, 8395)
    arg = [a for a in sys.argv[1:] if a.startswith("--journal=")]
    journal = Path(arg[0].split("=", 1)[1]) if arg else max(JOURNAUX.glob("quotidien_*.log"), key=lambda p: p.name)
    texte = journal.read_bytes().decode("utf-8-sig", errors="replace")
    ecrit = datetime.fromtimestamp(al.FICHIER_RATTACHEMENTS.stat().st_mtime)
    nuit = datetime.strptime(journal.stem.replace("quotidien_", ""), "%Y-%m-%d_%H-%M-%S")
    print("   le journal : %s (nuit du %s) ; le fichier ecrit le %s -> journal POSTERIEUR : %s" % (
        journal.name, nuit.strftime("%d/%m %H:%M"), ecrit.strftime("%d/%m %H:%M"), "OUI" if nuit > ecrit else "⛔ NON"))
    ok &= nuit > ecrit
    # le temoin inverse DU LECTEUR, a chaque lancement : il doit crier sur un journal truque en memoire
    j = lire_le_journal(texte)
    if "illisible" in j:
        print("   ⛔ journal illisible : %s -- pas de verdict (code 2)" % j["illisible"])
        return 2
    n = j["lus"]
    truques = {
        "un refus ajoute": texte.replace('"%s": %d' % (ATTENDU, j["decide"]),
                                         '"%s": %d,\n      "%s": 1' % (ATTENDU, j["decide"], LES_AUTRES[2]), 1),
        "DEUX VENTES ajoute": texte.replace('"%s": %d' % (ATTENDU, j["decide"]),
                                            '"%s": %d,\n      "%s": 1' % (ATTENDU, j["decide"], LES_AUTRES[3]), 1),
        "une ligne non appliquee": texte.replace('"%s": %d' % (ATTENDU, j["decide"]), '"%s": %d' % (ATTENDU, j["decide"] - 1), 1),
        "la ligne absente du journal": texte.replace('"%s": %d' % (ATTENDU, j["decide"]), '"x": 0', 1)}
    # ⚠ la fusion est FORCEE a 1 dans ces essais : sans ca, la fusion 0 d'un journal d'avant la ligne ferait crier les
    #   quatre a elle seule, et le temoin inverse ne prouverait rien sur les messages « [M] ».
    def sans_la_fusion(d: dict) -> dict:
        return d if "illisible" in d else dict(d, fusion=max(1, d["fusion"] or 0))
    assert all(t != texte for t in truques.values()), "un truquage n'a rien change au texte"
    muets = [nom for nom, t in truques.items() if not juger_le_journal(sans_la_fusion(lire_le_journal(t)), n)]
    sain = juger_le_journal(sans_la_fusion(j), n)
    print("   temoin inverse du LECTEUR : il crie sur %d / %d journaux truques en memoire%s ; sur le vrai, compte pour compte : %s"
          % (len(truques) - len(muets), len(truques), (" ⛔ MUET sur %s" % muets) if muets else "",
             "il se tait" if not sain else "⛔ %s" % sain))
    if muets:
        print("   ⛔ LE LECTEUR NE SAIT PAS CRIER -- pas de verdict (code 2)")
        return 2
    print("   ce que dit la nuit : lignes lues %d . « decide a la main » %d . autres « [M] » %s . etiquettes : fusion %s . "
          "etape %s" % (j["lus"], j["decide"], j["autres"] or "AUCUN", j["fusion"],
                        "DONE" if j["fait"] and not j["echec"] else "⛔ PAS DONE"))
    pas_j = juger_le_journal(j, len(fichier))
    for p in pas_j:
        print("   ⛔ %s" % p)
    a_la_main = [p for p in pas_j if not p.startswith("etiquettes")]
    print("   la nuit a applique A LA MAIN chacune des %d lignes du fichier, sans refus ni cri : %s ; et une fusion "
          "d'etiquette : %s" % (len(fichier), "OUI" if not a_la_main else "⛔ NON",
                                "OUI" if len(a_la_main) == len(pas_j) else "⛔ NON"))
    ok &= not pas_j

    print("\n⑤ LE BIEN 8395 NOMME -- la vraie fonction de nuit, rejouee sur le registre du matin avec SEULE la ligne 3648")
    brut = [b for b in al.FICHIER_RATTACHEMENTS.read_text(encoding="utf-8-sig").splitlines()
            if b.strip().startswith("3648;")]
    r5 = rejeu_du_seul_bien_8395(brut[0].strip() if len(brut) == 1 else None)
    print("   ligne rejouee : %s ; 3648 -> chaine %s ; messages « [M] » du seul bien 8395 : %s" % (
        "la ligne du fichier" if len(brut) == 1 else "⛔ AUCUNE (%d ligne(s) 3648 dans le fichier)" % len(brut),
        r5["chaine_3648"], r5["M"] or "AUCUN"))
    bon5 = r5["M"] == {ATTENDU: 1} and r5["chaine_3648"] == 3647
    print("   le bien 8395 dit exactement « %s » une fois, et rien d'autre : %s" % (ATTENDU, "OUI" if bon5 else "⛔ NON"))
    ok &= bon5
    print("\n⇒ %s" % ("✅ 3648 EST REUNIE A 3647, ET D2024-0306 A FUSIONNE DANS D2024-0511 -- mesure" if ok
                      else "⛔ PAS (ENCORE) REUNIE / FUSIONNEE -- voir ci-dessus"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
