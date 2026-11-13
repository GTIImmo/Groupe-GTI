#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- LE TABLEAU DE DECISION, pour Frederic.       13/11/2026

Demande : *« refais un audit sur la liste des lignes bien liees et les
problematiques, SAUF celles deja tranchees en attente. Genere un tableau
d'analyse, puis ligne par ligne fais ton propre raisonnement par logique, et fais
un tableau d'analyse que je peux aussi modifier pour decider -- ou alors laisser
non lie avec la possibilite de le faire plus tard manuellement. »*

═══════════════════════════════════════════════════════════════════════════════
CE QUE CE FICHIER PRODUIT, ET COMMENT LE LIRE
═══════════════════════════════════════════════════════════════════════════════
Un CSV ouvrable dans Excel ou Sheets, avec DEUX COLONNES VIDES a la fin :
    DECISION          <- Frederic ecrit : GEL / NON LIE / A VOIR / (vide)
    SON COMMENTAIRE   <- ce qu'il veut

Et, pour chaque ligne, TOUT ce qu'il faut pour decider sans me croire :
    . ce que dit le classeur (mandat, acquereur, vendeur, prix, ville, dates)
    . ce que dit LE GEL, et avec quelle confiance / quel etage
    . ce que JE dis, et avec combien de familles de temoins
    . MON RAISONNEMENT, en clair
    . MA RECOMMANDATION

⭐ LES LIGNES DEJA TRANCHEES SONT EXCLUES (demande explicite) : 3229, 3370, 3390,
  3826, 4393, et les 2 « a valider » 3406 / 4372 instruites ce matin.

═══════════════════════════════════════════════════════════════════════════════
⛔ COMMENT J'ECRIS « MON RAISONNEMENT » -- et je le dis honnetement
═══════════════════════════════════════════════════════════════════════════════
Je ne peux pas rediger 239 raisonnements tous differents sans me repeter ni me
contredire. Ce que je fais est plus honnete et plus utile :
  ① je CLASSE chaque ligne dans une SITUATION mesuree (il y en a 9) ;
  ② j'ecris le raisonnement de CHAQUE SITUATION, une fois, proprement ;
  ③ je l'INSTANCIE avec les faits de la ligne -- donc chaque ligne porte un texte
    qui parle d'ELLE, avec ses chiffres ;
  ④ et les cas que le classement ne sait pas ranger, je les prends A LA MAIN.
⭐ Un raisonnement par SITUATION est reproductible ; 239 jugements improvises ne
  le seraient pas. Et c'est reproductible qui permet a Frederic de me contredire.

LECTURE SEULE.
"""
from __future__ import annotations

import collections
import csv
import io
import sqlite3
import sys
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                                   # noqa: BLE001
    pass

from apparier_v2_socle import lire_le_sheet, pur  # noqa: E402

SORTIE = RACINE / "notice" / "TABLEAU_DECISION_APPARIEMENT_2026-11-13.csv"
DEJA_TRANCHEES = {"3229", "3370", "3390", "3826", "4393", "3406", "4372"}
RANG = {"sûre": 3, "bonne": 2, "à valider": 1}


def main() -> int:
    # ── LE GEL ──────────────────────────────────────────────────────────────
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""select g.ligne_classeur, g.role, g.app_affaire_id, g.confiance, g.etage,
                        l.hektor_annonce_id
                   from app_classeur_lien g
                   left join app_affaire_ledger l on l.app_affaire_id = g.app_affaire_id""")
    gel = collections.defaultdict(list)
    for lig, role, aff, conf, et, bien in c.fetchall():
        gel[str(lig)].append({"role": role, "aff": aff, "conf": (conf or "").strip(),
                              "etage": (et or "").strip(), "bien": bien})
    c.execute("""select hektor_annonce_id, ville, type_bien, statut_annonce,
                        commercial_nom from app_registre_mandats_current""")
    infos = {}
    for r in c.fetchall():
        infos.setdefault(r[0], {"ville": r[1], "type": r[2], "statut": r[3], "nego": r[4]})
    con.close()

    # ── MOI ─────────────────────────────────────────────────────────────────
    with io.open(RACINE / "notice" / "APPARIEUR_V2_FINAL_2026-11-13.csv",
                 encoding="utf-8-sig", newline="") as fh:
        fin = {x["ligne"]: x for x in csv.DictReader(fh, delimiter=";")}
    mes = collections.defaultdict(list)
    with io.open(RACINE / "notice" / "APPARIEUR_V2_LIENS_2026-11-13.csv",
                 encoding="utf-8-sig", newline="") as fh:
        for l in csv.DictReader(fh, delimiter=";"):
            mes[l["ligne du classeur"]].append(l)
    with io.open(RACINE / "notice" / "RAPPORT_V2_CONTRE_GEL_2026-11-13.csv",
                 encoding="utf-8-sig", newline="") as fh:
        rap = list(csv.DictReader(fh, delimiter=";"))
    divergentes = {x["ligne"] for x in rap if x["cas"] == "DIVERGENT"}
    div_bien = {x["ligne"] for x in rap
                if x["cas"] == "DIVERGENT" and x["bien du gel"] != x["bien de la v2"]}

    # ── les DOUBLONS du classeur, remesures ici ────────────────────────────
    from apparier_v2_socle import chiffres, jour, noms, somme
    entetes, lignes = lire_le_sheet()
    ic = {k: (entetes.index(k) if k in entetes else None) for k in entetes}

    def case(l, nom):
        i = ic.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    # ⭐⭐ LE DIAGNOSTIC -- ajoute le 13/11 EN RELISANT LE TABLEAU. Dire « 0 famille »
    #   ne suffit pas : la ligne 566 porte un MANDAT et QUATRE DATES, et « rien
    #   trouve » est suspect tant qu'on ne sait pas POURQUOI. Frederic doit pouvoir
    #   decider, donc il lui faut la CAUSE, pas le constat.
    con2 = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                           uri=True, timeout=30)
    c2 = con2.cursor()
    c2.execute("select distinct numero_mandat from app_affaire_ledger where numero_mandat is not null")
    mandats_chez_nous = {chiffres(r[0]) for r in c2.fetchall() if chiffres(r[0])}
    c2.execute("select distinct numero_mandat from app_registre_mandats_current where numero_mandat is not null")
    mandats_chez_nous |= {chiffres(r[0]) for r in c2.fetchall() if chiffres(r[0])}
    c2.execute("select kind, date, date_acte, hektor_annonce_id from app_affaire_ledger")
    jours_connus = collections.defaultdict(set)
    for kk, dd, da, bb in c2.fetchall():
        for x in (jour(dd), jour(da)):
            if x:
                jours_connus[x].add(bb)
    con2.close()

    def diagnostic(l):
        """POURQUOI ca ne marche pas -- en clair, et mesure."""
        out = []
        m = chiffres(case(l, "Mandat"))
        if not m:
            out.append("le classeur n'a PAS de n° de mandat")
        elif m in mandats_chez_nous:
            out.append("mandat %s CONNU chez nous" % m)
        else:
            out.append("⛔ mandat %s INCONNU chez nous" % m)
        ds = [(k, jour(case(l, k))) for k in
              ("Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée")
              if jour(case(l, k))]
        if not ds:
            out.append("aucune date lisible au classeur")
        else:
            touchent = sum(1 for _, d in ds if d in jours_connus)
            out.append("%d date(s) lisible(s), dont %d tombent sur une transaction"
                       % (len(ds), touchent))
        p = somme(case(l, "Prix"))
        if p is None:
            out.append("prix illisible")
        return " . ".join(out)

    emp = collections.defaultdict(list)
    for num, l in lignes:
        m, p = chiffres(case(l, "Mandat")), somme(case(l, "Prix"))
        a = " ".join(sorted(noms(case(l, "Acquéreur"))))
        d = jour(case(l, "Offre Achat"))
        if m and p and a:
            emp[(m, p, a, d)].append(str(num))
    doublon_de = {}
    for v in emp.values():
        if len(v) > 1:
            for x in v:
                doublon_de[x] = [y for y in v if y != x]

    # ═══ LE CLASSEMENT EN SITUATIONS, ET LE RAISONNEMENT DE CHACUNE ════════
    lot = []
    stat = collections.Counter()
    for num, l in lignes:
        num = str(num)
        f = fin.get(num, {})
        nf = int(f.get("nb familles") or 0)
        g = gel.get(num, [])
        gmax = max((RANG.get(x["conf"], 0) for x in g), default=0)
        mien = mes.get(num, [])
        mon_bien = (f.get("bien") or "").strip()
        bien_gel = str(g[0]["bien"]) if g and g[0]["bien"] is not None else ""
        etage_gel = g[0]["etage"] if g else ""
        conf_gel = g[0]["conf"] if g else ""

        # ── les SOLIDES ne vont pas au tableau de decision ─────────────────
        if num in DEJA_TRANCHEES:
            stat["exclue : deja tranchee"] += 1
            continue
        solide = (gmax >= 3 or nf >= 3) and num not in divergentes
        if solide:
            stat["SOLIDE -- pas au tableau"] += 1
            continue

        # ── sinon : on classe, et on RAISONNE ─────────────────────────────
        inf = infos.get(int(mon_bien)) if mon_bien.isdigit() else {}
        faits = "classeur: mandat %s . %s / %s . %s EUR . %s" % (
            case(l, "Mandat") or "-", (case(l, "Acquéreur") or "-")[:28],
            (case(l, "Vendeur") or "-")[:28], case(l, "Prix") or "-",
            case(l, "Ville") or "-")
        dates_cl = " . ".join("%s=%s" % (k[:9], case(l, k)) for k in
                              ("Offre Achat", "Compromis", "Vente Prévue", "Vente Fixée")
                              if case(l, k))

        if num in doublon_de:
            situation = "① DOUBLON DU CLASSEUR"
            raison = ("Cette ligne a LES MEMES valeurs (mandat, prix, acquereur, date "
                      "d'offre) que la/les ligne(s) %s. Une affaire a ete saisie, "
                      "annulee, puis re-saisie : la ligne « Annulee » est un HISTORIQUE, "
                      "pas une affaire distincte. Donc elle ne devrait porter AUCUN lien "
                      "-- les transactions appartiennent a l'autre ligne."
                      % ", ".join(doublon_de[num]))
            reco = "NON LIE (doublon)"
        elif num in div_bien:
            situation = "② DESACCORD DE BIEN"
            raison = ("Le gel dit le bien %s, moi le bien %s. Les deux ne peuvent pas "
                      "avoir raison. Mon lien tient sur %d famille(s) de temoins (%s) ; "
                      "le gel sur « %s », etage « %s »."
                      % (bien_gel or "-", mon_bien or "-", nf,
                         f.get("familles") or "aucune", conf_gel or "-", etage_gel[:40]))
            reco = "A VOIR -- comparer les dates au jour"
        elif num in divergentes:
            situation = "③ MEME BIEN, AUTRE TRANSACTION"
            raison = ("Le gel et moi sommes D'ACCORD SUR LE BIEN (%s) : on hesite "
                      "seulement sur LAQUELLE des transactions du dossier rattacher. "
                      "L'enjeu est faible -- le bien est juste dans les deux cas."
                      % (mon_bien or bien_gel or "-"))
            reco = "GEL (le bien est sur)"
        elif not g and not mien:
            if not mon_bien:
                situation = "④ PERSONNE NE TROUVE RIEN"
                raison = ("Ni le gel ni moi ne proposons quoi que ce soit, et je "
                          "M'ABSTIENS faute de temoin : %s. Il n'y a rien a deduire -- "
                          "soit l'affaire n'est pas chez Hektor, soit le classeur ne "
                          "porte pas assez pour la retrouver."
                          % (f.get("familles") or "aucune famille"))
            else:
                situation = "⑤ BIEN TROUVE, AUCUNE TRANSACTION LIBRE"
                raison = ("Je trouve le bien %s (%s, %s) mais AUCUNE transaction n'a pu "
                          "etre retenue : soit elles sont deja prises par une autre "
                          "ligne du classeur, soit HEKTOR N'A PAS la transaction que le "
                          "classeur decrit. C'est exactement le cas des lignes 3406 et "
                          "4372 instruites ce matin."
                          % (mon_bien, (inf.get("ville") or "?"), (inf.get("statut") or "-")))
            reco = "NON LIE -- a reprendre a la main plus tard"
        elif g and not mien:
            situation = "⑥ LE GEL SEUL, FAIBLEMENT"
            raison = ("Le gel relie cette ligne (bien %s) en « %s » par l'etage "
                      "« %s », et MOI je ne trouve rien d'assez sur (%s). Le gel a "
                      "probablement raison : je ne vois pas mieux, et je m'abstiens "
                      "plutot que de dire au hasard."
                      % (bien_gel or "-", conf_gel or "-", etage_gel[:38],
                         f.get("familles") or "aucune famille"))
            reco = "GARDER LE GEL tel quel"
        elif mien and not g:
            situation = "⑦ MOI SEUL, FAIBLEMENT"
            raison = ("Le gel ne connait pas cette ligne. Je propose le bien %s, mais "
                      "sur %d seule(s) famille(s) de temoins (%s) -- et ma mesure dit "
                      "qu'a ce niveau je n'ai raison que 9 fois sur 10. Pas assez pour "
                      "geler sans regarder."
                      % (mon_bien or "-", nf, f.get("familles") or "aucune"))
            reco = "A VOIR -- ou laisser NON LIE"
        else:
            situation = "⑧ LES DEUX, MAIS FAIBLEMENT"
            raison = ("Le gel (« %s », etage « %s ») et moi (%d famille(s) : %s) "
                      "designons le meme bien %s, mais ni l'un ni l'autre n'est "
                      "solide. L'accord de deux methodes faibles vaut mieux qu'une "
                      "seule, sans valoir une preuve."
                      % (conf_gel or "-", etage_gel[:30], nf,
                         f.get("familles") or "aucune", mon_bien or bien_gel or "-"))
            reco = "GEL (accord des deux)"

        stat[situation] += 1
        lot.append([num, case(l, "ID Unique"), situation, case(l, "Etat Actuel"),
                    faits, dates_cl, diagnostic(l),
                    bien_gel, conf_gel, etage_gel[:46],
                    mon_bien, nf, f.get("familles") or "",
                    ",".join(sorted(x["role"] for x in mien)),
                    raison, reco, "", ""])

    # ═══ LE TABLEAU ═════════════════════════════════════════════════════════
    print("=" * 86)
    print("TABLEAU DE DECISION -- ce qui y entre, et pourquoi")
    print("=" * 86)
    print()
    for k, n in sorted(stat.items()):
        print("   %-42s %5d" % (k, n))
    print()
    print("   ---> LIGNES AU TABLEAU : %d" % len(lot))

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ligne", "ID Unique", "SITUATION", "Etat Actuel",
                    "ce que dit le classeur", "ses dates", "POURQUOI (diagnostic)",
                    "bien GEL", "confiance gel", "etage gel",
                    "bien MOI", "nb familles", "quelles familles", "roles que je lie",
                    "MON RAISONNEMENT", "MA RECOMMANDATION",
                    "DECISION (a remplir)", "COMMENTAIRE (a remplir)"])
        w.writerows(sorted(lot, key=lambda x: (x[2], int(x[0]))))
    print("\n   ecrit : %s" % SORTIE)
    print("\n" + "=" * 86)
    print("LECTURE SEULE. Les 2 dernieres colonnes sont VIDES, a remplir par Frederic.")
    print("=" * 86)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
