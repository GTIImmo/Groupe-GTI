#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPARIEUR V2 -- PASSE 5 : DU BIEN A LA TRANSACTION, ET L'EXCLUSION.
                                                                  13/11/2026

Mission donnee par Frederic : *« lance 1 et 2 puis continue, tu dois y arriver,
sinon fini une par une. Ensuite fais-moi un rapport comparatif avec mon regel.
Tu es autonome en lecture seule. »*

═══════════════════════════════════════════════════════════════════════════════
LES QUATRE LEVIERS, DANS L'ORDRE OU ILS GAGNENT
═══════════════════════════════════════════════════════════════════════════════
① DESCENDRE DU BIEN A LA TRANSACTION. C'etait la contrainte posee au depart et
  non encore honoree : le gel s'accroche a la TRANSACTION, dont le numero ne
  bouge jamais, alors qu'une chaine est recalculee chaque nuit. Une ligne du
  classeur peut designer JUSQU'A TROIS transactions (son offre, son compromis,
  sa vente) -- comme le gel, qui porte 12 422 liens pour 4 688 lignes.

② L'EXCLUSION, et SEULEMENT SUR LA TRANSACTION.
  ⛔⛔ LA MESURE M'A ARRETE SUR LA PREMIERE VERSION DE CETTE IDEE : je voulais
    exclure au niveau du BIEN. Or 410 biens (9,7 %) portent legitimement
    PLUSIEURS lignes du classeur -- et 37 en portent deux CERTAINES, 3 en portent
    trois. Un bien peut porter deux affaires : une offre refusee a un acheteur,
    puis une vente a un autre. ⭐ En faire un veto aurait casse 410 biens justes.
  ⭐ MAIS UNE TRANSACTION DONNEE N'APPARTIENT QU'A UNE LIGNE. La, c'est une vraie
    bijection, donc un vrai sudoku : chaque certitude posee en resout d'autres.

③ LES TEMOINS QUE JE N'EXPLOITAIS PAS. Je lisais 3 colonnes sur 38. S'ajoutent :
    la VILLE          99,8 % remplie
    le NEGOCIATEUR    100 %
    l'AGENCE          99,7 %
  ⭐ Ils ne servent pas a trancher seuls -- ils font PARLER les familles muettes.

④ LE VETO DE COHERENCE. « Vente reglee » exige une vente ; « Annulee » interdit
  une vente active. Ca n'ajoute pas un vote : ca ELIMINE des candidats, ce qui
  est plus fort.

═══════════════════════════════════════════════════════════════════════════════
⛔ CE QUI RESTE HORS DE PORTEE, ET IL FAUT LE DIRE
═══════════════════════════════════════════════════════════════════════════════
Les lignes ou LE CLASSEUR LUI-MEME melange deux affaires (deux acheteurs
differents sur une ligne). Mesure du 12/11 : 23 des 33 lignes « a cheval » sont
de ce type, et sur tout le registre 417 paires sur 472 ont deux acheteurs
differents. Aucune methode ne les rattachera : elles appartiennent a Frederic.

LECTURE SEULE DE BOUT EN BOUT.
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

from apparier_v2_socle import (chiffres, jour, lire_le_registre,     # noqa: E402
                               lire_le_sheet, noms, noms_du_blob, pur, somme)

SORTIE = RACINE / "notice" / "APPARIEUR_V2_LIENS_2026-11-13.csv"
SORTIE_LIGNES = RACINE / "notice" / "APPARIEUR_V2_FINAL_2026-11-13.csv"

CHAMPS_PERSONNES = ("acquereur_json", "acquereurs_json", "mandants_json")
GENRE_DE_COLONNE = {"Offre Achat": "offre", "Compromis": "compromis",
                    "Vente Prévue": "vente", "Vente Fixée": "vente"}


def etats_attendus(etat: str) -> tuple[set[str], set[str]]:
    """(genres EXIGES, genres INTERDITS) d'apres l'« Etat Actuel » du classeur.
    ⚠ On reste prudent : le classeur dit ce qui est ATTEINT. Un seul interdit,
      et il est sur : « Annulee » exclut une vente ABOUTIE."""
    e = pur(etat)
    if "regl" in e or "fix" in e or ("sign" in e and "annul" not in e):
        return {"vente"}, set()
    if "compromis" in e or "prevu" in e:
        return {"compromis"}, set()
    if "annul" in e:
        return set(), {"vente"}
    if "offre" in e:
        return {"offre"}, set()
    return set(), set()


def main() -> int:
    print("=" * 86)
    print("PASSE 5 -- DU BIEN A LA TRANSACTION, PUIS L'EXCLUSION")
    print("=" * 86)

    tx = lire_le_registre()
    par_bien = collections.defaultdict(list)
    for t in tx:
        par_bien[t["hektor_annonce_id"]].append(t)

    # ── les index ───────────────────────────────────────────────────────────
    # ⛔⛔ CORRIGE LE 13/11 EN JUGEANT LA LIGNE 4758 A LA MAIN. Je fusionnais les
    #   noms d'ACQUEREUR et de MANDANT dans un seul ensemble. Resultat : la ligne
    #   4758 (acquereur BAURE Candice, vendeur DEVIDAL Sylvie) a ete rattachee a
    #   un bien de 2017 vendu par la MEME Sylvie DEVIDAL -- j'avais matche sur le
    #   nom du VENDEUR. Le gel avait raison.
    #   ⭐ UN ACQUEREUR N'EST PAS UN VENDEUR : deux index separes, et le score
    #     exige la concordance DU BON COTE.
    iA, iCg = collections.defaultdict(set), collections.defaultdict(set)
    iB_acq, iB_vend = collections.defaultdict(set), collections.defaultdict(set)
    acq_bien, vend_bien = collections.defaultdict(set), collections.defaultdict(set)
    noms_tx = {}
    for t in tx:
        b = t["hektor_annonce_id"]
        m = chiffres(t.get("numero_mandat"))
        if m:
            iA[m].add(b)
        a_mots: set[str] = set()
        for ch in ("acquereur_json", "acquereurs_json"):
            a_mots |= noms_du_blob(t.get(ch))
        v_mots = noms_du_blob(t.get("mandants_json"))
        noms_tx[t["app_affaire_id"]] = a_mots | v_mots
        acq_bien[b] |= a_mots
        vend_bien[b] |= v_mots
        for mot in a_mots:
            iB_acq[mot].add(b)
        for mot in v_mots:
            iB_vend[mot].add(b)
        for d in (jour(t.get("date")), jour(t.get("date_acte"))):
            if d:
                iCg[(t["kind"], d)].add(b)

    # ── les infos du bien : ville, equipe, notre numero de dossier ──────────
    con = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    c = con.cursor()
    c.execute("""select hektor_annonce_id, ville, code_postal, commercial_nom,
                        agence_nom, mandat_numero_reference
                   from app_registre_mandats_current""")
    infos, ref_bien = {}, collections.defaultdict(set)
    for ann, ville, cp, nego, ag, ref in c.fetchall():
        infos.setdefault(ann, {"ville": pur(ville), "cp": chiffres(cp),
                               "nego": pur(nego), "agence": pur(ag)})
        if ref and str(ref).strip():
            ref_bien[pur(ref)].add(ann)
    con.close()
    print("\nindex : A %d mandats . B %d mots . C %d (genre,jour) . %d biens"
          % (len(iA), len(iB_acq) + len(iB_vend), len(iCg), len(par_bien)))
    print("        + ville/equipe sur %d biens . %d numeros de dossier"
          % (len(infos), len(ref_bien)))

    entetes, lignes = lire_le_sheet()
    ic = {k: (entetes.index(k) if k in entetes else None) for k in entetes}

    def case(l, nom):
        i = ic.get(nom)
        return str(l[i]).strip() if i is not None and i < len(l) else ""

    # ═══ PHASE 1 : LE BIEN, avec TOUS les temoins + le VETO ═════════════════
    print("\n" + "-" * 86)
    print("PHASE 1 -- le BIEN : 5 familles de temoins + le veto de coherence")
    print("-" * 86)
    retenus = {}
    stat1 = collections.Counter()
    for num, l in lignes:
        man = chiffres(case(l, "Mandat"))
        acq = noms(case(l, "Acquéreur"))
        vend = noms(case(l, "Vendeur"))
        mots = acq | vend
        dates = {GENRE_DE_COLONNE[k]: jour(case(l, k))
                 for k in GENRE_DE_COLONNE if jour(case(l, k))}
        ville, cp = pur(case(l, "Ville")), chiffres(case(l, "Ville"))
        nego, agence = pur(case(l, "Négociateur 1")), pur(case(l, "Agence"))
        ref = pur(case(l, "product_ref"))
        exiges, interdits = etats_attendus(case(l, "Etat Actuel"))

        cand: set = set()
        if ref:
            cand |= ref_bien.get(ref, set())
        if man:
            cand |= iA.get(man, set())
        for mot in acq:
            cand |= iB_acq.get(mot, set())
        for mot in vend:
            cand |= iB_vend.get(mot, set())
        for g, d in dates.items():
            cand |= iCg.get((g, d), set())
        if not cand:
            retenus[num] = (None, 0, "aucun candidat", {})
            stat1["aucun candidat"] += 1
            continue
        if len(cand) > 500:
            fort = set(ref_bien.get(ref, set())) | set(iA.get(man, set()))
            for g, d in dates.items():
                fort |= iCg.get((g, d), set())
            if fort:
                cand = (cand & fort) or fort

        notes = []
        for b in cand:
            # ── ④ LE VETO : on ELIMINE avant de noter ────────────────────
            genres = {t["kind"] for t in par_bien[b]}
            if interdits and (interdits & genres):
                # ⚠ « Annulee » et une vente : on n'elimine que si la vente est
                #   ABOUTIE et qu'aucun autre signal fort ne parle.
                if not (man and b in iA.get(man, set())):
                    continue
            # ⛔⛔ RETIRE LE 13/11 : LE VETO N EXIGE PLUS RIEN.
            #   Il exigeait un genre (« Vente prevue » -> un compromis). Or LE
            #   CLASSEUR EST EN AVANCE SUR HEKTOR : l agence note « vente
            #   prevue » des la signature chez le notaire, alors que la
            #   transaction compromis n existe pas encore chez Hektor.
            #   ⭐ C est ca qui a fait echouer la ligne 4758 : le bien 63116,
            #     que le gel designait a juste titre, n a QU UNE OFFRE -- mon
            #     veto l a elimine, et j ai pris un bien au hasard.
            #   ➡ UN VETO NE DOIT QU INTERDIRE, JAMAIS EXIGER.
            fam, score = [], 0
            if ref and b in ref_bien.get(ref, set()):
                fam.append("dossier"); score += 100
            if man and b in iA.get(man, set()):
                fam.append("mandat"); score += 40
            # ⭐ L'IDENTITE SE JUGE PAR COTE. L'acquereur pese PLUS que le
            #   vendeur : un vendeur vend plusieurs fois dans sa vie (c'est
            #   exactement ce qui m'a trompe sur la ligne 4758), un acquereur
            #   d'une affaire donnee est l'acquereur de cette affaire.
            ca = acq & acq_bien.get(b, set())
            cv = vend & vend_bien.get(b, set())
            if len(ca) >= 2:
                fam.append("acquereur"); score += 16 * min(len(ca), 4) + 24
            elif ca:
                score += 12
            if len(cv) >= 2:
                fam.append("vendeur"); score += 10 * min(len(cv), 3) + 10
            elif cv:
                score += 5
            # ⚠ ET LE CROISEMENT INVERSE EST UN INDICE CONTRAIRE : si le
            #   « vendeur » du classeur n'apparait que comme ACQUEREUR du bien,
            #   c'est probablement une autre affaire de la meme personne.
            if not ca and not cv:
                croise = (acq & vend_bien.get(b, set())) | (vend & acq_bien.get(b, set()))
                if croise:
                    score -= 8
            justes = sum(1 for g, d in dates.items() if b in iCg.get((g, d), set()))
            if justes >= 2:
                fam.append("dates"); score += 30 * min(justes, 3)
            elif justes == 1:
                score += 22
            inf = infos.get(b, {})
            if ville and inf.get("ville") and (ville in inf["ville"] or inf["ville"] in ville):
                fam.append("lieu"); score += 8
            elif cp and inf.get("cp") and cp == inf["cp"]:
                fam.append("lieu"); score += 6
            if nego and inf.get("nego") and (nego in inf["nego"] or inf["nego"] in nego):
                fam.append("equipe"); score += 7
            elif agence and inf.get("agence") and (agence in inf["agence"]
                                                   or inf["agence"] in agence):
                score += 3
            notes.append((score, len(fam), b, fam))

        if not notes:
            retenus[num] = (None, 0, "tous les candidats elimines par le veto", {})
            stat1["elimines par le veto"] += 1
            continue
        notes.sort(key=lambda x: (-x[0], -x[1]))
        s, nf, b, fam = notes[0]
        # ⛔ LE SEUIL, pose sur MA PROPRE MESURE : un lien que AUCUNE famille ne
        #   soutient n a raison que 2 fois sur 3 (67,7 % mesure contre le gel).
        #   ⭐ Mieux vaut ne rien dire que dire au hasard : on s abstient, et on
        #     le COMPTE -- c est une ligne a juger a la main, pas un lien.
        if nf == 0:
            retenus[num] = (None, s, "ABSTENTION : aucune famille de temoins",
                            {"candidats": len(notes)})
            stat1["abstention (0 famille)"] += 1
            continue
        ecart = s - (notes[1][0] if len(notes) > 1 else 0)
        retenus[num] = (b, s, "+".join(fam), {"familles": nf, "ecart": ecart,
                                              "candidats": len(notes),
                                              "dates": dates, "mots": mots,
                                              "man": man})
        stat1["%d familles" % nf] += 1
    for k, n in sorted(stat1.items()):
        print("   %-28s %5d  (%5.1f %%)" % (k, n, 100.0 * n / len(lignes)))

    # ═══ PHASE 2 : LA TRANSACTION, par genre ════════════════════════════════
    print("\n" + "-" * 86)
    print("PHASE 2 -- du bien a la TRANSACTION (le numero qui ne bouge jamais)")
    print("-" * 86)
    propositions = []     # (score, num, genre, transaction, pourquoi)
    stat2 = collections.Counter()
    for num, (b, s, fam, ctx) in retenus.items():
        if b is None:
            continue
        for genre in ("offre", "compromis", "vente"):
            cands = [t for t in par_bien[b] if t["kind"] == genre]
            if not cands:
                continue
            d = ctx["dates"].get(genre, "")
            if len(cands) == 1:
                propositions.append((s + 5, num, genre, cands[0]["app_affaire_id"],
                                     "seule du genre"))
                stat2["%s : seule" % genre] += 1
                continue
            # plusieurs : on departage, et on DIT comment
            exact = [t for t in cands if d and jour(t.get("date")) == d]
            if len(exact) == 1:
                propositions.append((s + 20, num, genre, exact[0]["app_affaire_id"],
                                     "date exacte"))
                stat2["%s : par la date" % genre] += 1
                continue
            parnom = [t for t in cands if ctx["mots"] & noms_tx.get(t["app_affaire_id"], set())]
            if len(parnom) == 1:
                propositions.append((s + 10, num, genre, parnom[0]["app_affaire_id"],
                                     "par le nom"))
                stat2["%s : par le nom" % genre] += 1
                continue
            jeu = exact or parnom or cands
            propositions.append((s, num, genre, jeu[0]["app_affaire_id"],
                                 "AMBIGU (%d candidats)" % len(cands)))
            stat2["%s : AMBIGU" % genre] += 1
    for k, n in sorted(stat2.items()):
        print("   %-28s %5d" % (k, n))
    print("   TOTAL liens proposes : %d" % len(propositions))

    # ═══ PHASE 3 : L'EXCLUSION -- une transaction = une ligne ═══════════════
    print("\n" + "-" * 86)
    print("PHASE 3 -- L'EXCLUSION sur les TRANSACTIONS (le sudoku)")
    print("   ⛔ jamais sur le bien : 410 biens portent legitimement 2 lignes.")
    print("-" * 86)
    propositions.sort(key=lambda p: -p[0])
    pris: dict = {}
    liens, refuses = [], []
    for score, num, genre, aff, pourquoi in propositions:
        if aff in pris:
            refuses.append((num, genre, aff, pris[aff], score, pourquoi))
            continue
        pris[aff] = num
        liens.append([num, genre, aff, score, pourquoi])
    print("   liens retenus          : %d" % len(liens))
    print("   refuses par l'exclusion: %d  (la transaction etait deja prise par"
          " une ligne mieux notee)" % len(refuses))

    # ⭐ LA SECONDE CHANCE : une ligne qui perd toutes ses transactions doit
    #   pouvoir en retrouver d'autres. On mesure combien sont dans ce cas.
    par_ligne = collections.defaultdict(list)
    for num, genre, aff, score, pourquoi in liens:
        par_ligne[num].append(genre)
    orphelines = [num for num, _ in lignes if retenus[num][0] is not None
                  and num not in par_ligne]
    print("   lignes qui perdent TOUT: %d" % len(orphelines))

    # ═══ LE RESULTAT PAR LIGNE ══════════════════════════════════════════════
    print("\n" + "-" * 86)
    print("LE RESULTAT : combien de transactions par ligne du classeur")
    print("-" * 86)
    cc = collections.Counter(len(v) for v in par_ligne.values())
    for k in sorted(cc):
        print("   %d transaction(s) : %5d lignes" % (k, cc[k]))
    print("   aucune            : %5d lignes" % (len(lignes) - len(par_ligne)))

    with io.open(SORTIE, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ligne du classeur", "role", "app_affaire_id", "score", "pourquoi"])
        w.writerows(sorted(liens, key=lambda x: (int(x[0]), x[1])))
    with io.open(SORTIE_LIGNES, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ligne", "ID Unique", "bien", "score", "familles", "nb familles",
                    "ecart au 2e", "candidats", "roles trouves"])
        for num, l in lignes:
            b, s, fam, ctx = retenus[num]
            w.writerow([num, case(l, "ID Unique"), b or "", s, fam,
                        ctx.get("familles", 0), ctx.get("ecart", 0),
                        ctx.get("candidats", 0), ",".join(sorted(par_ligne.get(num, [])))])
    print("\n   ecrit : %s" % SORTIE.name)
    print("   ecrit : %s" % SORTIE_LIGNES.name)
    print("\n" + "=" * 86)
    print("LECTURE SEULE : rien en base, rien chez Hektor, rien dans le classeur.")
    print("=" * 86)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
