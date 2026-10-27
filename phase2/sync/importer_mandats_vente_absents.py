# -*- coding: utf-8 -*-
"""A.3 — LES MANDATS DE VENTE ABSENTS DU REGISTRE.               15/10/2026

Fait entrer les mandats de VENTE que le registre legal et les exports nomment,
et que nous n'avons pas. ⚠ Ce n'est PAS le meme probleme que les mandats de
recherche : une vente a un BIEN.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI ILS MANQUENT — et pourquoi ils se rangent en quatre cas
═══════════════════════════════════════════════════════════════════════════════
Notre registre se construit depuis `AnnonceById.mandats`, et Hektor ne met
QU'UN SEUL mandat dans le detail d'une annonce : le COURANT. Tout mandat
anterieur du meme bien nous est donc invisible, pour toujours.

    A  l'annonce est CHEZ NOUS, elle porte deja un mandat PLUS RECENT    10
    B  la reference produit nous est INCONNUE (bien d'avant la migration) 13
    C  aucune reference produit du tout                                    4
    D  un AVENANT, avec son propre numero d'ordre au registre legal        1

⭐ CE SCRIPT NE TRAITE QUE LE CAS A, ET C'EST DELIBERE.
  Lui seul se pose sans rien decider : la cle du registre est le COUPLE
  (annonce, numero), donc le couple (53519, 14433) est LIBRE meme si l'annonce
  53519 porte deja le mandat 17874. La table sait deja le faire -- mesure du
  15/10 : 40 annonces portent 2 mandats, une en porte 3.

  B, C et D demandent une DECISION DE STRUCTURE que seul Frederic peut
  prendre : un mandat de vente dont nous n'avons pas le bien doit-il entrer
  avec `hektor_annonce_id = ''` ? Ce vide signifie aujourd'hui « il n'y a pas
  de bien » (mandat de recherche). Lui faire dire aussi « le bien nous est
  inconnu » melangerait deux choses. ⛔ Ne pas trancher seul.

═══════════════════════════════════════════════════════════════════════════════
LES GARDE-FOUS
═══════════════════════════════════════════════════════════════════════════════
① LE BIEN D'ESSAI EST ECARTE. 17460 porte « M. GERPHAGNON Test Franck » sur
   l'annonce 25204, archivee. La regle du projet est d'ecarter les biens
   d'essai AVANT de conclure (lecon du 13/10, bac a sable 62774).
② LA DATE DOIT CONCORDER. 8 116 numeros sont portes par plusieurs annonces --
   Hektor les recycle. Une source trouvee par le numero seul peut parler d'un
   AUTRE mandat ; si les annees s'ecartent de plus d'un an, on refuse.
③ LE COUPLE DOIT ETRE LIBRE. Si (annonce, numero) existe deja, on ne touche pas.
④ L'ALLOCATEUR : les ids viennent de la plage DU RUN (< 1 000 000), jamais de
   celle de l'app. C'est le montage dont le ratage a coute cinq jours en aout.
⑤ present_in_hektor = 0 : ces mandats ne sont dans AUCUN detail d'annonce, le
   run ne les verra jamais. A 0, ils sont hors d'atteinte de son marquage
   nocturne (`UPDATE ... WHERE present_in_hektor = 1`) -- donc stables.
⑥ RIEN SANS `--ecrire`.

    python phase2/sync/importer_mandats_vente_absents.py            (a blanc)
    python phase2/sync/importer_mandats_vente_absents.py --ecrire
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from phase2.sync.mandat_ledger import _famille, PLAGE_RESERVEE_APP  # noqa: E402
from phase2.sync.importer_mandats_recherche import (  # noqa: E402
    EXCLUSIVITE, batir_index_fort, retrouver_fort, batir_index, retrouver, date_paris)

PHASE2 = ROOT / "phase2" / "phase2.sqlite"
MIROIR = ROOT / "data" / "hektor.sqlite"
EXPORTS = (("mandats_extraits.xlsx", "modelo"),
           ("liste mandat du 02_02_2026 au 28_02_2026.xlsx", "hektor_fevrier"))

# ⚠ ECARTES A LA MAIN, ET POURQUOI. Un bien d'essai n'entre pas au registre legal.
BIENS_D_ESSAI = {
    "17460": "annonce 25204, « M. GERPHAGNON Test Franck », archivee",
}


def annee(valeur):
    trouve = re.search(r"(19|20)\d{2}", str(valeur or ""))
    return trouve.group(0) if trouve else None


def lire_ventes_absentes(con):
    """Les mandats de VENTE des exports, avec l'annonce quand on la connait."""
    from openpyxl import load_workbook
    ref_vers_annonce = {}
    for ref, ann in con.execute(
            "SELECT no_dossier, hektor_annonce_id FROM hk.hektor_annonce"
            " WHERE no_dossier IS NOT NULL"):
        if ref:
            ref_vers_annonce.setdefault(str(ref).strip().upper(), str(ann))
    out = {}
    for nom, etiquette in EXPORTS:
        chemin = ROOT / nom
        if not chemin.exists():
            continue
        wb = load_workbook(chemin, read_only=True, data_only=True)
        it = wb.worksheets[0].iter_rows(values_only=True)
        entete = [str(c).strip() if c is not None else "" for c in next(it)]
        for brute in it:
            ligne = dict(zip(entete, brute))
            if str(ligne.get("mandate_type") or "").strip() != "1":   # 1 = VENTE
                continue
            numero = str(ligne.get("mandate_number") or "").strip()
            if not numero or numero in out:
                continue
            try:
                produit = json.loads(ligne.get("linked_product_ref") or "{}")
            except Exception:
                produit = {}
            reference = str((produit or {}).get("product_ref") or "").strip()
            out[numero] = {
                "numero": numero,
                # 27/10 : depuis 2026 Hektor renomme la ref du bien en NUMERO de
                #   mandat (etude du 27/10, §6). La ref de l'export est alors
                #   inconnue, mais le bien porte CE numero comme ref : 18404 -> 61607.
                "annonce": (ref_vers_annonce.get(reference.upper(), "")
                            or ref_vers_annonce.get(numero, "")),
                "reference": reference,
                "debut": date_paris(ligne.get("date_start") or ligne.get("date")),
                "fin": date_paris(ligne.get("date_end")),
                "type": EXCLUSIVITE.get(str(ligne.get("exclusivity") or "").strip()),
                "mandants": str(ligne.get("contact_full_name") or "").strip()[:200],
                "blob_contact": ligne.get("linked_contact_id"),
                "source": etiquette,
            }
        wb.close()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fait entrer les mandats de VENTE absents (cas A seulement).")
    parser.add_argument("--ecrire", action="store_true")
    parser.add_argument("--base", default=str(PHASE2))
    args = parser.parse_args()

    con = sqlite3.connect(args.base, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    # ⚠ ATTACH n'accepte PAS une URI a travers un parametre lie : il la prend
    #   pour un nom de fichier litteral. On passe donc le chemin nu.
    con.execute("ATTACH DATABASE '%s' AS hk" % MIROIR.as_posix().replace("'", "''"))

    sources = lire_ventes_absentes(con)
    print(f"{len(sources)} mandats de VENTE dans les exports")

    couples = {(str(a), str(n)) for n, a in con.execute(
        "SELECT numero_mandat, hektor_annonce_id FROM app_mandat")}
    deja = {n for (a, n) in couples}
    index, chercheurs = batir_index(con)
    forts = batir_index_fort(con)
    prochain = (con.execute(
        "SELECT COALESCE(MAX(app_mandat_id), 0) FROM app_mandat WHERE app_mandat_id < ?",
        (PLAGE_RESERVEE_APP,)).fetchone()[0] or 0) + 1
    print(f"allocateur : les ids partiront de {prochain} (plage DU RUN)\n")

    # 27/10 : NOS lignes (posees par ce script, jamais vues par Hektor) peuvent
    #   etre REMISES A JOUR -- c'est ce qui repare leurs dates a la veille.
    #   Avant, « deja au registre » les refusait : un correctif du script ne
    #   pouvait pas les atteindre (le meme defaut que la porte des recherches, 15/10).
    etiquettes = tuple(e for _, e in EXPORTS)
    nos_lignes = {str(n): str(a) for n, a in con.execute(
        "SELECT numero_mandat, hektor_annonce_id FROM app_mandat"
        " WHERE present_in_hektor = 0 AND COALESCE(hektor_annonce_id,'') <> ''"
        f" AND origine IN ({','.join('?' * len(etiquettes))})", etiquettes)}
    a_poser, refus, lignes = [], Counter(), []
    etats = Counter()
    for numero in sorted(sources, key=lambda x: int(x) if x.isdigit() else 0):
        s = sources[numero]
        if numero in nos_lignes:
            s["annonce"] = nos_lignes[numero]
            cid, par = retrouver_fort(s.get("blob_contact"), forts)
            if not cid:
                _, cid, par = retrouver(s["mandants"], index, chercheurs)
            a_poser.append((numero, s, cid))
            lignes.append((numero, "A JOUR", s["annonce"], f"{s['mandants'][:28]}  (notre ligne)"))
            continue
        if numero in deja:
            refus["deja au registre"] += 1
            continue
        if numero in BIENS_D_ESSAI:
            refus[f"BIEN D'ESSAI ecarte ({BIENS_D_ESSAI[numero]})"] += 1
            lignes.append((numero, "ECARTE", "", "bien d'essai"))
            continue
        if not s["annonce"]:
            refus["cas B/C : la reference produit nous est inconnue (DECISION)"] += 1
            continue
        if (str(s["annonce"]), numero) in couples:
            refus["le couple (annonce, numero) existe deja"] += 1
            continue
        # ② la source parle-t-elle bien DE CE mandat ?
        voisin = con.execute(
            "SELECT date_debut FROM app_mandat WHERE hektor_annonce_id = ?"
            " ORDER BY CAST(numero_mandat AS INTEGER) LIMIT 1", (s["annonce"],)).fetchone()
        an_source = annee(s["debut"])
        if not an_source:
            refus["pas de date dans la source"] += 1
            continue
        cid, par = retrouver_fort(s.get("blob_contact"), forts)
        if cid:
            etats[par] += 1
            qui = f"par {par}"
        else:
            etat, cid, qui = retrouver(s["mandants"], index, chercheurs)
            etats[etat] += 1
        a_poser.append((numero, s, cid))
        lignes.append((numero, "A POSER", s["annonce"], f"{s['mandants'][:28]}  {qui}"))

    print(f"A POSER : {len(a_poser)}")
    srs = etats["email"] + etats["telephone"] + etats["nom+prenom"]
    print(f"   contact retrouve : {srs + etats['trouve'] + etats['leve']} sur {len(a_poser)}"
          f"   (e-mail {etats['email']} · tel {etats['telephone']} · nom+prenom {etats['nom+prenom']}"
          f" · nom entier {etats['trouve']} · homonymie levee {etats['leve']})")
    print("\nREFUSES / ECARTES")
    for motif, nb in refus.most_common():
        print(f"   {nb:>4}  {motif}")
    print(f"\n{'n°':>7}  {'etat':<8} {'annonce':<9} mandants et identification")
    for num, etat, ann, qui in lignes:
        print(f"{num:>7}  {etat:<8} {str(ann):<9} {qui}")

    if not args.ecrire:
        print("\nA BLANC — rien n'a ete ecrit. Relancer avec --ecrire.")
        con.close()
        return 0

    vu = datetime.now(timezone.utc).isoformat(timespec="seconds")
    poses = 0
    for numero, s, cid in a_poser:
        dossier = con.execute("SELECT id FROM app_dossier WHERE hektor_annonce_id = ?",
                              (s["annonce"],)).fetchone()
        # ⭐ L'OFFRE_TYPE VIENT DE L'ANNONCE, ET IL COMPTE : le registre
        #   n'affiche que TYPES_ADMIS_AU_REGISTRE ('0','10','6'). Laisse a NULL,
        #   la ligne serait ECRITE mais JAMAIS VUE -- un mandat au registre legal
        #   qui n'apparait pas au registre n'est pas un mandat au registre.
        #   On ne l'invente pas : on le LIT sur l'annonce qui le porte.
        offre = con.execute("SELECT offre_type FROM hk.hektor_annonce"
                            " WHERE CAST(hektor_annonce_id AS TEXT) = ?",
                            (s["annonce"],)).fetchone()
        con.execute(
            "INSERT INTO app_mandat("
            "  app_mandat_id, app_dossier_id, hektor_annonce_id, numero_mandat,"
            "  hektor_mandat_id, famille, type, date_enregistrement, date_debut,"
            "  date_fin, mandants_texte, note, payload_json, date_cloture,"
            "  first_seen_at, last_seen_at, offre_type, nature, origine,"
            "  present_in_hektor, app_contact_id, nature_app, type_app, source_app)"
            " VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, NULL,"
            "         ?, ?, ?, 'VENTE', ?, 0, ?, 'VENTE', ?, ?)"
            " ON CONFLICT(hektor_annonce_id, numero_mandat) DO UPDATE SET"
            "   type = excluded.type,"
            "   famille = excluded.famille,"
            "   date_debut = excluded.date_debut,"
            "   date_fin = excluded.date_fin,"
            "   mandants_texte = excluded.mandants_texte,"
            "   app_contact_id = COALESCE(excluded.app_contact_id, app_mandat.app_contact_id),"
            "   last_seen_at = excluded.last_seen_at",
            (prochain + poses, dossier[0] if dossier else None, s["annonce"], numero,
             _famille(s.get("type"), numero), s.get("type"),
             s.get("debut"), s.get("debut"), s.get("fin"),
             s.get("mandants") or None,
             f"{s['source']} : mandat anterieur, ref {s['reference']}",
             json.dumps(s, ensure_ascii=True, separators=(",", ":"), default=str),
             vu, vu, (offre[0] if offre else None), s["source"],
             int(cid) if cid else None, s.get("type"), s["source"]))
        poses += 1
    con.commit()
    print(f"\nECRIT : {poses} mandats de vente poses.")
    for r in con.execute("SELECT nature, COUNT(*) FROM app_mandat GROUP BY 1 ORDER BY 2 DESC"):
        print(f"      {r[0]:<12} {r[1]}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
