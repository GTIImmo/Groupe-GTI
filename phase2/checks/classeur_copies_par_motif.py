#!/usr/bin/env python
"""LES 190 COPIES DU LOT DU CLASSEUR, PAR MOTIF -- chantier classeur, 22/11/2026 soir (son mot « le patch est accorde », § 4).

SON MOT : « NE METS PAS LES 5 DANS LE MEME GESTE. [...] L'ACQUEREUR NE CORRESPOND PAS [...] FAMILLE 2, non expliquee :
  1001561, 1001593. NE LES TOUCHE PAS. Mesure-les et dis-moi, pour chacune, si mon classeur a raison -- une offre acceptee
  a-t-elle existe pour CET acheteur, et ou est-elle passee ? [...] y en a-t-il D'AUTRES de la famille 2 ? [...] Cherche,
  et donne-moi le compte par MOTIF. »

LECTURE SEULE. Pour chaque copie (transaction_origine = 'classeur') :
  L'ACHETEUR DU CLASSEUR   la note posee avec la copie (« Acquereur au classeur : ... ») -- les noms de famille par
                           apparier_classeur.mots_propres, la meme lecture que le gel (aucune regle recopiee)
  LES PIECES DE HEKTOR     du meme bien et du meme genre, avec leur VRAIE date (app_dossier_jour_date_transaction, par la
                           base) et leurs acquereurs (meme lecture des noms)
  LES MOTIFS (un seul par copie, dans cet ordre) :
    M1 JUMELLE, MEME ACHETEUR          une piece du meme genre a la meme vraie date, au nom de l'acheteur : la meme
                                       transaction posee deux fois (cicatrice si sa date brute a ete deplacee par nos gestes)
    M2 JUMELLE PAR LA DATE, AUTRE NOM  une piece du meme genre a la meme vraie date, mais AUCUN nom en commun -- SA FAMILLE 2
    M3 L'ACHETEUR A UNE PIECE DE CE GENRE, A UNE AUTRE DATE
    M4 L'ACHETEUR N'A AUCUNE PIECE DE CE GENRE CHEZ HEKTOR (le cas que le lot devait remplir)
    M5 PAS DE NOM LISIBLE au classeur
  ⭐ LE M2 SE SOUS-CLASSE PAR DES FAITS, JAMAIS PAR LE NOM SEUL -- la regle du projet (audit V2 du 19/11, memoire
    hektor-reutilise-le-contact-de-l-acheteur-precedent) : chez Hektor le contact d'une transaction ment souvent, « une
    date au jour exact bat un nom seul », « un nom different sans date DOUTE, il ne PROUVE pas » :
    M2a LE MEME ACHETEUR, ECRIT AUTREMENT   le nom de la jumelle est dans la colonne VENDEUR de la ligne (colonnes
                                            inversees au classeur), ou le meme nom colle / decolle (VAN ROSSUM /
                                            VANROSSUM)
    M2e UNE NOTE DE SON CLASSEUR NOMME LES DEUX  (colonnes F / G posees par C4 -- PAS une note de Hektor) : elle se
                                            LIT, elle ne prouve pas l'identite (« BELLAN/MARTINEZ GAY » = le meme menage ;
                                            sur 28422 la note dit une PREEMPTION par la locataire)
    M2b LA JUMELLE EST TENUE PAR UNE LIGNE SOEUR  le gel la relie a une autre ligne du bien : la date de la copie est
                                            peut-etre celle de la soeur (les acheteurs successifs croises de l'audit)
    M2c L'ACHETEUR NAIT APRES                son contact chez Hektor est ne APRES la date que le classeur donne a sa
                                            piece : Hektor ne pouvait pas la porter a son nom
    M2d LE RESTE : la date au jour exact, un autre contact, rien d'autre (le cas du contact reutilise)
  ET DEUX FAITS EN PLUS, pour juger un M2 sans deviner :
    . l'acheteur du classeur est-il CONNU de Hektor sur le bien (son nom sur un compromis ou une vente) ? et depuis quand
      (dateenr de son contact) -- un contact ne avant / APRES la date de l'offre du classeur ;
    . la piece jumelle a-t-elle ete touchee par NOS GESTES (refus du 11/11, reacceptation du 12/11...) ?
SORTIE : notice/CLASSEUR_COPIES_PAR_MOTIF_<date>.csv . CODES : 0 mesure faite . 2 pas pu lire
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
SORTIE = RACINE / "notice" / ("CLASSEUR_COPIES_PAR_MOTIF_%s.csv" % date.today().isoformat())
MOTIFS = ("M1 jumelle, meme acheteur", "M2 jumelle par la date, AUTRE nom", "M3 l'acheteur a une piece de ce genre, a une "
          "autre date", "M4 l'acheteur n'a aucune piece de ce genre chez Hektor", "M5 pas de nom lisible au classeur")


def dire(s: str = "") -> None:
    print(s, flush=True)


def gens(blob) -> list[dict]:
    if isinstance(blob, str):
        try:
            blob = json.loads(blob)
        except ValueError:
            return []
    return [g for g in (blob if isinstance(blob, list) else [blob] if isinstance(blob, dict) else []) if isinstance(g, dict)]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    import apparier_classeur as ac
    import classeur_detecteur_cicatrices as DC
    ac.MORCEAUX_DE_NOM = True
    try:
        cn, cu = DC.connexion()
    except Exception as e:  # noqa: BLE001
        dire("⛔ la base n'a pas pu etre lue (%s) -- code 2" % str(e).splitlines()[0][:160])
        return 2
    try:
        cu.execute("select l.app_affaire_id, l.kind, coalesce(l.state, ''), left(coalesce(l.date, ''), 10), "
                   "l.hektor_annonce_id, l.app_chaine_id, l.payload_json->>'classeur_id_unique', "
                   "l.payload_json->>'classeur_lot', (select string_agg(n.texte, ' | ') from public.app_affaire_note n "
                   "where n.app_affaire_id = l.app_affaire_id and n.origine = 'classeur') "
                   "from public.app_affaire_ledger l where l.transaction_origine = 'classeur' order by 1")
        copies = cu.fetchall()
        biens = sorted({int(c[4]) for c in copies})
        cu.execute("select l.app_affaire_id, l.kind, coalesce(l.state, ''), left(coalesce(l.date, ''), 10), "
                   "public.app_dossier_jour_date_transaction(l.kind, l.date, l.propositions_json, l.app_affaire_id), "
                   "l.hektor_annonce_id, l.app_chaine_id, l.acquereurs_json, l.acquereur_json "
                   "from public.app_affaire_ledger l where coalesce(l.transaction_origine, '') <> 'classeur' "
                   "and l.hektor_annonce_id = any(%s)", (biens,))
        vraies = defaultdict(list)
        for a, k, s, brute, vraie, b, ch, acqs, acq1 in cu.fetchall():
            g = gens(acqs) or gens(acq1)
            vraies[int(b)].append({"id": int(a), "kind": k, "state": s, "brute": brute, "vraie": vraie or "", "chaine": ch,
                                   "noms": ac.mots_propres(" ".join(str(x.get("nom") or "").upper() for x in g)),
                                   "noms_bruts": [str(x.get("nom") or "") for x in g if x.get("nom")],
                                   "qui": " / ".join(("%s %s" % (x.get("nom") or "", x.get("prenom") or "")).strip()
                                                     for x in g),
                                   "nes": sorted({str(x.get("dateenr") or "")[:10] for x in g if x.get("dateenr")})})
        ctx = DC.lire_contexte(cu, set(biens))
        # ⚠ ces notes viennent de SON CLASSEUR (origine classeur:F / classeur:G / classeur:F+G -- ses colonnes F et G
        #   posees par C4), ou d'une saisie dans l'app : PAS de Hektor. Les copies (origine « classeur ») sont exclues.
        cu.execute("select l.hektor_annonce_id, n.app_affaire_id, coalesce(n.origine, ''), n.texte "
                   "from public.app_affaire_note n join public.app_affaire_ledger l "
                   "on l.app_affaire_id = n.app_affaire_id where coalesce(n.origine, '') <> 'classeur' "
                   "and l.hektor_annonce_id = any(%s)", (biens,))
        notes_du_bien = defaultdict(list)
        for b, na, no, t in cu.fetchall():
            notes_du_bien[int(b)].append((int(na), no, t or ""))
        cn.rollback()
    finally:
        cn.close()
    # le Sheet et le gel : la derniere image du protocole (lecture seule)
    import protocole_classeur as P
    con = P.socle()
    image = con.execute("select image from passage where image is not null order by id desc limit 1").fetchone()[0]
    con.close()
    I = P.Image(P.IMAGES / image)
    ent = I.sheet["entete"]
    k_ac, k_ve = ent.index("Acquéreur"), ent.index("Vendeur")

    def ligne(i):
        v = I.sheet["par_id"].get(i)
        return v[0]["row"] if v else None

    def espaces(t: str) -> str:
        import unicodedata
        t = unicodedata.normalize("NFD", str(t or "").upper())
        return "".join(c if "A" <= c <= "Z" else " " for c in t if unicodedata.category(c) != "Mn")

    def lettres(t: str) -> str:
        import unicodedata
        t = unicodedata.normalize("NFD", str(t or "").upper())
        return "".join(c for c in t if "A" <= c <= "Z")
    lignes, cpt, cpt_lot = [], Counter(), defaultdict(Counter)
    for a, k, s, d, b, ch, iu, lot, note in copies:
        m = re.search(r"Acquereur au classeur : (.*?)\. Reprise", note or "")
        texte = m.group(1) if m else ""
        noms = ac.mots_propres(texte)
        vr = vraies.get(int(b), [])
        meme_genre = [v for v in vr if v["kind"] == k]
        jum = [v for v in meme_genre if v["vraie"] and v["vraie"] == d]
        jum_meme = [v for v in jum if v["noms"] & noms]
        a_lui = [v for v in meme_genre if v["noms"] & noms]
        connu = [v for v in vr if v["kind"] in ("compromis", "vente") and v["noms"] & noms]
        if not noms:
            motif = MOTIFS[4]
        elif jum_meme:
            motif = MOTIFS[0]
        elif jum:
            motif = MOTIFS[1]
        elif a_lui:
            motif = MOTIFS[2]
        else:
            motif = MOTIFS[3]
        touche = [v for v in jum if ctx["gestes"].get(v["id"])]
        ne_apres = sorted({n for v in connu for n in v["nes"] if n and d and n > d})
        indices = []
        if motif == MOTIFS[1]:
            row = ligne(iu) or []
            vend = ac.mots_propres(row[k_ve]) if row else set()
            for v in jum:
                if v["noms"] & vend:
                    indices.append("M2a colonnes inversees : %s est dans la colonne VENDEUR de la ligne" % "/".join(
                        sorted(v["noms"] & vend)))
                # le meme nom colle ou decolle : les LETTRES seules du nom de Hektor dans les lettres du classeur
                if any(lettres(n) and lettres(n) in lettres(texte) for n in v["noms"]):
                    indices.append("M2a meme nom ecrit autrement (%s / %s)" % (texte, v["qui"]))
                # ⚠ la note se lit MOT ENTIER contre MOT ENTIER (les lettres seules) : mots_propres ecarte les noms de
                #   moins de 4 lettres, et « BELLAN/MARTINEZ GAY » (la vente de 47557) perdait GAY
                for na, no, tx in notes_du_bien.get(int(b), []):
                    mots_note = set(re.findall(r"[A-Z]{2,}", espaces(tx)))     # UNE note a la fois
                    cl_ = {lettres(n) for n in noms} & mots_note
                    hk_ = {lettres(str(g)) for g in v["noms_bruts"]} & mots_note
                    if cl_ and hk_:
                        indices.append("M2e la note %s (%s, piece %d) nomme les deux : %s + %s -- %r" % (
                            "de TON CLASSEUR" if no.startswith("classeur") else "saisie", no, na, "/".join(sorted(cl_)),
                            "/".join(sorted(hk_)), tx.split("--", 1)[-1].strip()[:80]))
                soeurs = [j for j in I.gel_par_piece.get(v["id"], []) if j != iu]
                for j in soeurs:
                    rj = ligne(j)
                    indices.append("M2b tenue par la ligne soeur %s (acheteur au classeur %r)" % (
                        j, rj[k_ac] if rj else "?"))
            if ne_apres:
                indices.append("M2c le contact de l'acheteur est ne le %s, APRES la date du classeur" % ",".join(ne_apres))
            sous = next((s_ for s_ in ("M2a", "M2e", "M2b", "M2c") if any(x.startswith(s_) for x in indices)), "M2d")
            cpt["  " + sous] += 1
        else:
            sous = ""
        cpt[motif] += 1
        cpt_lot[lot][motif] += 1
        lignes.append({"copie": a, "id_unique": iu, "lot": lot, "genre": k, "etat": s, "date": d, "bien": b,
                       "chaine": ch, "acheteur_au_classeur": texte, "motif": motif,
                       "jumelles": " | ".join("%d %s %s vraie %s brute %s chaine %s acheteur %s%s" % (
                           v["id"], v["kind"], v["state"], v["vraie"], v["brute"], v["chaine"], v["qui"] or "-",
                           (" -- NOS GESTES : %s" % " + ".join(ctx["gestes"][v["id"]])) if ctx["gestes"].get(v["id"])
                           else "") for v in jum),
                       "pieces_de_l_acheteur_de_ce_genre": " | ".join("%d %s vraie %s" % (v["id"], v["state"], v["vraie"])
                                                                      for v in a_lui),
                       "acheteur_connu_de_hektor_sur_le_bien": " | ".join("%d %s du %s (contact ne le %s)" % (
                           v["id"], v["kind"], v["vraie"], ",".join(v["nes"]) or "?") for v in connu),
                       "contact_ne_apres_la_date_du_classeur": ",".join(ne_apres),
                       "jumelle_touchee_par_nos_gestes": "oui" if touche else "",
                       "sous_motif": sous, "indices": " | ".join(indices)})
    dire("LES %d COPIES DU LOT, PAR MOTIF (l'acheteur du classeur contre les pieces de Hektor du meme bien) :" % len(copies))
    for mo in MOTIFS:
        dire("   %-58s %4d   %s" % (mo, cpt[mo], " . ".join("%s %d" % (str(l).replace("C5 lot B -- ", ""), c[mo])
                                                          for l, c in sorted(cpt_lot.items()) if c[mo])))
    for mo in MOTIFS[:2]:
        dire("=== %s ===" % mo)
        for x in lignes:
            if x["motif"] == mo:
                dire("   copie %s %-10s %s/%s du %s, bien %s ; acheteur au classeur %r%s%s" % (
                    x["copie"], x["id_unique"], x["genre"], x["etat"], x["date"], x["bien"], x["acheteur_au_classeur"],
                    " ; ⚠ son contact est ne APRES (%s)" % x["contact_ne_apres_la_date_du_classeur"]
                    if x["contact_ne_apres_la_date_du_classeur"] else "",
                    " ; jumelle touchee par NOS GESTES" if x["jumelle_touchee_par_nos_gestes"] else ""))
                dire("        jumelle(s) : %s" % x["jumelles"])
                if mo == MOTIFS[1]:
                    dire("        l'acheteur chez Hektor sur ce bien : %s" % (x["acheteur_connu_de_hektor_sur_le_bien"]
                                                                          or "AUCUNE piece a son nom"))
                    dire("        %s : %s" % (x["sous_motif"], x["indices"] or "la date au jour exact, un autre contact, "
                                                                            "rien d'autre"))
    dire("LE M2 SOUS-CLASSE (par des faits) : " + " . ".join("%s %d" % (k.strip(), cpt[k]) for k in
                                                           ("  M2a", "  M2e", "  M2b", "  M2c", "  M2d")))
    with SORTIE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]), delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    dire("-> %s" % SORTIE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
