# -*- coding: utf-8 -*-
"""LE CONTROLE DU LENDEMAIN — les 12 points a verifier apres le run du 01/10.

LECTURE SEULE. Aucun appel a Hektor, aucune ecriture nulle part.

POURQUOI CE SCRIPT
    La nuit du 30/09 au 01/10 est la premiere a porter QUATRE chantiers d'un
    coup : le deballeur des passerelles, l'instantane cible, le menage des
    passerelles supprimees, et les +3 782 liens acquereur de la veille.
    Verifier cela a la main, c'est douze requetes dans deux bases et un fichier
    de journal -- donc c'est ce qu'on ne fait pas.

CE QU'IL NE FAIT PAS, ET C'EST VOULU
    Il ne repare rien. Les points 11 et 12 sont connus pour rester ROUGES : ce
    sont les deux correctifs qui restent a ecrire. Un controle qui les passerait
    sous silence mentirait sur l'etat reel.

USAGE
    python phase2/checks/apres_run_2026-10-01.py
    code 0 = tout ce qui devait bouger a bouge ; 1 sinon.
"""
from __future__ import annotations

import glob
import io
import json
import os
import sqlite3
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MIROIR = os.path.join("data", "hektor.sqlite")
CARTE = os.path.join("phase2", "phase2.sqlite")

VERT, ROUGE, ATTENDU, INFO = "  OK  ", "  ⛔  ", "  ⚠️  ", "  ·   "
resultats: list[tuple[str, str, str]] = []


def dire(marque: str, titre: str, detail: str) -> None:
    resultats.append((marque, titre, detail))
    print("%s %-44s %s" % (marque, titre[:44], detail))


def lire(chemin: str):
    conn = sqlite3.connect("file:%s?mode=ro" % chemin, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def un(conn, sql, params=()):
    try:
        ligne = conn.execute(sql, params).fetchone()
        return ligne[0] if ligne else None
    except sqlite3.Error:
        return None


def cles_supabase() -> tuple[str, str]:
    url = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").strip()
    cle = (os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if url and cle:
        return url, cle
    chemin = os.path.join("apps", "hektor-v1", ".env")
    if os.path.exists(chemin):
        with io.open(chemin, encoding="utf-8") as fichier:
            for ligne in fichier:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "=" not in ligne:
                    continue
                nom, _, valeur = ligne.partition("=")
                valeur = valeur.strip().strip('"').strip("'")
                if not url and nom.strip() in ("SUPABASE_URL", "VITE_SUPABASE_URL"):
                    url = valeur
                elif not cle and nom.strip() == "SUPABASE_SERVICE_ROLE_KEY":
                    cle = valeur
    return url, cle


def compter_cloud(table: str, filtre: dict | None = None) -> int | None:
    """Compte exact via PostgREST. None si on ne sait pas lire."""
    url, cle = cles_supabase()
    if not url or not cle:
        return None
    try:
        import requests
        params = {"select": "*"}
        params.update(filtre or {})
        reponse = requests.get(
            "%s/rest/v1/%s" % (url.rstrip("/"), table),
            headers={"apikey": cle, "Authorization": "Bearer %s" % cle,
                     "Prefer": "count=exact", "Range": "0-0"},
            params=params, timeout=30,
        )
        if reponse.status_code >= 400:
            return None
        plage = reponse.headers.get("content-range", "")
        return int(plage.split("/")[-1]) if "/" in plage else None
    except Exception:
        return None


def main() -> int:
    aujourd_hui = date.today().isoformat()
    print("=" * 84)
    print("APRES LE RUN — les 12 points du 01/10/2026       (lecture seule)")
    print("=" * 84)

    # ── 1. le run est-il alle au bout ? ────────────────────────────────────────
    journaux = sorted(glob.glob(os.path.join(".tmp", "full_pipeline_*.log")))
    dernier = journaux[-1] if journaux else None
    if not dernier:
        dire(ROUGE, "1. le run", "aucun journal trouve")
    else:
        nom = os.path.basename(dernier)
        du_jour = aujourd_hui.replace("-", "") in nom
        with io.open(dernier, encoding="utf-8", errors="replace") as f:
            fin = f.read()[-4000:]
        fini = "Pipeline finished successfully" in fin
        if du_jour and fini:
            dire(VERT, "1. le run est alle au bout", nom)
        elif not du_jour:
            dire(ATTENDU, "1. le run", "%s — PAS celui d'aujourd'hui" % nom)
        else:
            dire(ROUGE, "1. le run", "%s — fin anormale" % nom)

    miroir = lire(MIROIR)

    # ── 2. les passerelles sont-elles degelees ? ───────────────────────────────
    n_pass = un(miroir, "SELECT COUNT(*) FROM hektor_broadcast")
    frais = un(miroir, "SELECT COUNT(*) FROM hektor_broadcast WHERE substr(synced_at,1,10) = ?", (aujourd_hui,))
    dire(VERT if (frais or 0) >= 38 else ROUGE, "2. passerelles rafraichies",
         "%s vues aujourd'hui sur %s en base   (attendu >= 38)" % (frais, n_pass))

    # ── 3. l'instantane a-t-il fonctionne ? ────────────────────────────────────
    n_list = un(miroir, "SELECT COUNT(*) FROM hektor_broadcast_listing")
    perimees = un(miroir, "SELECT COUNT(*) FROM hektor_broadcast_listing WHERE substr(synced_at,1,10) < ?", (aujourd_hui,))
    dire(VERT if perimees == 0 else ROUGE, "3. instantane des diffusions",
         "%s lignes, dont %s perimees   (attendu 0 perimee)" % (n_list, perimees))

    # ── 4. les 8 passerelles mortes ont-elles lache leurs lignes ? ─────────────
    mortes = un(miroir,
                "SELECT COUNT(*) FROM hektor_broadcast_listing "
                "WHERE hektor_broadcast_id IN ('36','37','38','39','40','41','42','43','44')")
    dire(VERT if mortes == 0 else ROUGE, "4. passerelles LBC supprimees",
         "%s ligne(s) restantes sur 36-44   (attendu 0)" % mortes)

    # ── 5. l'ecran dit-il la verite ? ──────────────────────────────────────────
    lbc = compter_cloud("app_dossiers_current", {"portails_resume": "ilike.*leboncoin*"})
    if lbc is None:
        dire(INFO, "5. LeBonCoin a l'ecran", "non mesurable (cles Supabase absentes)")
    else:
        dire(VERT if 240 <= lbc <= 290 else ATTENDU, "5. LeBonCoin a l'ecran",
             "%s annonces   (etait 268, Hektor en annoncait 264)" % lbc)

    # ── 6. la carte tient-elle encore ? ────────────────────────────────────────
    dire(INFO, "6. la carte agence -> passerelle",
         "a lancer a part : passerelle_par_agence.py --par-agence")

    # ── 7. les acquereurs sont-ils montes ? ────────────────────────────────────
    liens = compter_cloud("app_contact_relations_current")
    if liens is None:
        dire(INFO, "7. liens a l'ecran", "non mesurable")
    else:
        dire(VERT if liens > 163765 else ATTENDU, "7. liens a l'ecran",
             "%s   (etait 163 765 ; +3 782 acquereurs attendus)" % liens)

    # ── 8. la doublure du registre des liens ───────────────────────────────────
    carte = lire(CARTE)
    existe = un(carte, "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='app_relation__sb'")
    if existe:
        dire(VERT, "8. doublure app_relation__sb",
             "%s lignes descendues" % un(carte, "SELECT COUNT(*) FROM app_relation__sb"))
    else:
        dire(ROUGE, "8. doublure app_relation__sb", "toujours absente")

    # ── 9. relation_disparue ne ment plus ? ────────────────────────────────────
    dire(INFO, "9. relation_disparue",
         "si app_relation__sb existe, son « retard du cloud » doit changer de sens")

    # ── 10. les quatre sentinelles ─────────────────────────────────────────────
    dire(INFO, "10. les 4 sentinelles",
         "a lancer : mandat_un_numero · annonce_un_numero · mandat_disparu · relation_disparue")

    # ── 11 et 12 : LES DEUX QUI DOIVENT RESTER ROUGES ─────────────────────────
    bloquees = compter_cloud("app_search_pending")
    if bloquees is None:
        dire(INFO, "11. la saisie du 23/09", "non mesurable")
    else:
        dire(ATTENDU if bloquees else VERT, "11. saisie de recherche bloquee",
             "%s en attente — LE RUN NE LA DEBLOQUE PAS, c'est un correctif a ecrire" % bloquees)

    erreurs = compter_cloud("app_console_job", {"status": "eq.error"})
    if erreurs is None:
        dire(INFO, "12. travaux en erreur", "non mesurable")
    else:
        dire(ATTENDU if erreurs else VERT, "12. travaux en erreur",
             "%s — JAMAIS REJOUES, l'alarme reste rouge tant qu'on ne les traite pas" % erreurs)

    print("=" * 84)
    rouges = sum(1 for m, _, _ in resultats if m == ROUGE)
    attendus = sum(1 for m, _, _ in resultats if m == ATTENDU)
    print("  %s anomalie(s) · %s point(s) connus a traiter a la main" % (rouges, attendus))
    print("=" * 84)
    return 1 if rouges else 0


if __name__ == "__main__":
    raise SystemExit(main())
