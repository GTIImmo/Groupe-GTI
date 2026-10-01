# -*- coding: utf-8 -*-
"""CONTROLE DE LA DESCENTE DU 02/10 -- le delta des photos a-t-il tenu ?   01/10/2026

LECTURE SEULE. Aucune ecriture, ni locale ni en ligne. Se lance a tout moment.

    .venv\\Scripts\\python.exe phase2\\checks\\apres_descente_2026-10-02.py

POURQUOI CE CONTROLE EXISTE
---------------------------
La nuit du 01/10, la descente a sature Supabase : le front en « canceling statement
due to statement timeout », ~50 executions d'automates perdues sur ~27 minutes, et
app_console_photo morte sur une reponse coupee a 1 Mio.

Trois correctifs ont ete poses le 01/10 au soir (commit de29e4d) :
  · un DECLENCHEUR garantit updated_at sur app_console_photo
  · la table entre dans DELTA_HORODATAGE -> elle ne descend plus que ses modifications
  · une reponse TRONQUEE est desormais reessayee comme une coupure de passerelle
Puis une descente CIBLEE (--page-size 300) a pose la copie complete qui autorise
le delta : 437 044 lignes en 18 min, ZERO echec d'automate.

CE CONTROLE VERIFIE QUE CA A TENU EN CONDITIONS REELLES. Il ne dit pas « ca marche » :
il affiche des chiffres, et dit ATTENDU quand un chiffre non nul est normal.

⚠ CE QU'IL NE PEUT PAS VOIR : si la descente n'a pas encore tourne, tout sera
  « inchange depuis hier » -- ce n'est pas un echec, c'est trop tot.
"""
from __future__ import annotations

import datetime
import os
import pathlib
import sqlite3
import sys
import urllib.error
import urllib.request
import json

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VERT, ROUGE, INFO, ATTENDU = "  OK ", " !!! ", "  .. ", "  ~~ "
PHASE2 = ROOT / "phase2" / "phase2.sqlite"
JOURNAUX = ROOT / "logs" / "scheduled"


def dire(marque: str, titre: str, detail: str = "") -> None:
    print("%s %-46s %s" % (marque, titre[:46], detail))


def un(conn, sql, args=()):
    try:
        r = conn.execute(sql, args).fetchone()
        return r[0] if r else None
    except sqlite3.Error as exc:
        return "illisible (%s)" % exc


def charger_env() -> tuple[str | None, str | None]:
    for nom in (".env", "Console/.env", "apps/hektor-v1/.env"):
        chemin = ROOT / nom
        if not chemin.exists():
            continue
        for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" not in ligne or ligne.lstrip().startswith("#"):
                continue
            cle, _, val = ligne.partition("=")
            os.environ.setdefault(cle.strip(), val.strip().strip('"').strip("'"))
    return (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL"),
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))


def compter_cloud(table: str) -> int | None:
    """Le COMPTE seul, par l'en-tete Content-Range : une requete, aucune donnee.

    ⚠ `count=exact` fait compter TOUTES les lignes : sur app_console_photo
      (437 044) la premiere version expirait a 30 s et le controle affichait
      « cloud illisible (hors ligne ?) » -- un message FAUX, qui accusait le
      reseau pour un simple delai. Un controle qui se trompe de cause est pire
      qu'un controle muet. D'ou : 90 s, et un second essai.
    """
    url, cle = charger_env()
    if not (url and cle):
        return None
    req = urllib.request.Request(
        "%s/rest/v1/%s?select=*&limit=1" % (url.rstrip("/"), table),
        headers={"apikey": cle, "Authorization": "Bearer %s" % cle,
                 "Prefer": "count=exact"})
    for essai in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=90) as rep:
                portee = rep.headers.get("Content-Range") or ""
            return int(portee.split("/")[-1]) if "/" in portee else None
        except (urllib.error.URLError, OSError, ValueError):
            if essai == 2:
                return None
    return None


def journal_du_jour() -> pathlib.Path | None:
    jour = datetime.date.today().isoformat()
    candidats = sorted(JOURNAUX.glob("descente_%s_*.log" % jour))
    return candidats[-1] if candidats else None


def main() -> int:
    print("=" * 78)
    print("  LA DESCENTE APRES LES CORRECTIFS DU 01/10        %s"
          % datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
    print("=" * 78)

    if not PHASE2.exists():
        dire(ROUGE, "phase2.sqlite", "introuvable")
        return 1
    conn = sqlite3.connect("file:%s?mode=ro" % PHASE2.resolve().as_posix(),
                           uri=True, timeout=30)

    # ─── 1. LE JOURNAL : LE DELTA A-T-IL ETE EMPLOYE ? ────────────────────────
    print("\n--- 1. ce que le journal de la descente raconte ---")
    log = journal_du_jour()
    if log is None:
        dire(INFO, "1. journal du jour", "aucun -- la descente n'a pas encore tourne")
    else:
        texte = log.read_text(encoding="utf-8", errors="replace")
        dire(INFO, "1. journal lu", log.name)
        total = 0
        for ligne in texte.splitlines():
            if "app_console_photo" in ligne:
                marque = VERT if "(delta)" in ligne else ROUGE
                detail = ligne.strip()[:60]
                dire(marque, "1a. app_console_photo",
                     detail + ("" if "(delta)" in ligne else "   <- PAS en delta !"))
            if "ECHEC" in ligne and "[" in ligne:
                dire(ROUGE, "1b. table en echec", ligne.strip()[:60])
                total += 1
        if total == 0:
            dire(VERT, "1b. tables en echec", "aucune")
        # LE POIDS TOTAL. ⚠ On ne somme QUE les lignes d'inventaire de la forme
        #   « [ 42/150] app_truc    1234 lignes »
        # Un `\s(\d+) lignes` nu ramassait aussi les chiffres des messages et des
        # commentaires du journal : il rendait 3 053 362 pour une descente de
        # 1 959 855 (premier essai, 01/10) -- un total faux ne se remarque pas,
        # il se lit comme une mesure.
        import re
        poids = sum(int(m) for m in re.findall(
            r"^\s*\[\s*\d+/\s*\d+\]\s+\S+\s+(\d+) lignes", texte, re.MULTILINE))
        repere = "attendu ~1 292 000 (contre 1 959 855 le 01/10)"
        dire(VERT if poids and poids < 1_600_000 else INFO,
             "1c. lignes rapatriees", "%s   %s" % (f"{poids:,}".replace(",", " "), repere))

    # ─── 2. L'ETAT DE LA TABLE DES PHOTOS ─────────────────────────────────────
    print("\n--- 2. app_console_photo, serveur contre cloud ---")
    etat = conn.execute(
        "SELECT lignes, derniere_descente, derniere_complete, dernier_echec "
        "FROM sb_pull_state WHERE table_name = 'app_console_photo'").fetchone()
    if not etat:
        dire(ROUGE, "2. etat en base", "la table n'est pas suivie")
    else:
        dire(VERT if etat[0] else ROUGE, "2a. copie complete derriere elle",
             "lignes=%s" % etat[0])
        dire(VERT if not etat[3] else ROUGE, "2b. dernier echec",
             etat[3] or "aucun")
        dire(INFO, "2c. derniere complete", str(etat[2]))
    local = un(conn, "SELECT COUNT(*) FROM app_console_photo")
    cloud = compter_cloud("app_console_photo")
    if cloud is None:
        dire(INFO, "2d. serveur vs cloud", "cloud illisible (hors ligne ?) -- local %s" % local)
    else:
        dire(VERT if local == cloud else ROUGE, "2d. serveur vs cloud",
             "%s / %s" % (local, cloud))

    # ─── 3. LE DECLENCHEUR TIENT-IL SA PROMESSE ? ─────────────────────────────
    # Sans lui, le delta se fierait a une date non garantie. On ne peut pas lire
    # pg_trigger par PostgREST : on verifie donc son EFFET -- quand la tache de
    # 08:30 pose hors_vitrine_depuis, updated_at doit suivre.
    #
    # ⚠⚠ ON NE COMPARE QUE CE QUI EST POSTERIEUR AU DECLENCHEUR. Avant lui,
    #    l'ecart est NORMAL -- c'est meme ce qui a justifie de le poser. Un
    #    controle qui crie sur des donnees historiques ne sert a rien, et pire :
    #    on finit par ne plus le lire.
    #
    # ⭐ LA MESURE QUI A MOTIVE TOUT CECI, le 01/10 a 22:15, AVANT le declencheur :
    #      36 sorties de vitrine posees a 10:30 par la tache pg_cron
    #        13 avaient updated_at = 07:40        -> la date n'a PAS suivi
    #         6 avaient updated_at = 26/09        -> CINQ JOURS de retard
    #        17 avaient updated_at = 14:41        -> suivie PAR HASARD : le worker
    #                                               les avait touchees pour autre chose
    #    Soit 19 sorties sur 36 qu'un delta aurait ratees EN SILENCE.
    print("\n--- 3. le declencheur updated_at (verifie par son EFFET) ---")
    POSE_LE = "2026-10-01T19:30:00"      # heure d'application du patch declencheur
    posees = un(conn,
                "SELECT COUNT(*) FROM app_console_photo "
                "WHERE hors_vitrine_depuis > ?", (POSE_LE,))
    suivies = un(conn,
                 "SELECT COUNT(*) FROM app_console_photo "
                 "WHERE hors_vitrine_depuis > ? AND updated_at >= hors_vitrine_depuis",
                 (POSE_LE,))
    if not posees:
        dire(INFO, "3. sorties posees DEPUIS le declencheur",
             "aucune encore -- la tache de 10:30 n'a pas retourne depuis")
    elif suivies == posees:
        dire(VERT, "3. sorties posees DEPUIS le declencheur",
             "%s posees, %s avec la date suivie -> le declencheur tient" % (posees, suivies))
    else:
        dire(ROUGE, "3. sorties posees DEPUIS le declencheur",
             "%s posees mais %s seulement avec la date suivie "
             "-> LE DELTA EN RATERAIT" % (posees, suivies))
    # l'historique, pour memoire -- JAMAIS une alerte
    avant = un(conn,
               "SELECT COUNT(*) FROM app_console_photo "
               "WHERE hors_vitrine_depuis IS NOT NULL AND hors_vitrine_depuis <= ? "
               "  AND updated_at < hors_vitrine_depuis", (POSE_LE,))
    dire(ATTENDU, "3b. ecarts ANTERIEURS au declencheur",
         "%s -- normal, c'est ce qui a justifie de le poser" % avant)

    # ─── 4. LES REGISTRES, SERVEUR CONTRE CLOUD ───────────────────────────────
    print("\n--- 4. les registres (ils n'ont PAS ete modifies le 01/10) ---")
    for natif, distant in (("app_relation", "app_relation"),
                           ("app_mandat", "app_mandat"),
                           ("app_affaire_ledger", "app_affaire_ledger")):
        n = un(conn, 'SELECT COUNT(*) FROM "%s"' % natif)
        d = compter_cloud(distant)
        if d is None:
            dire(INFO, "4. %s" % natif, "cloud illisible -- serveur %s" % n)
        else:
            dire(VERT if n == d else ROUGE, "4. %s" % natif, "%s / %s" % (n, d))

    # ─── 5. CE QUE LA SATURATION AURAIT CASSE ─────────────────────────────────
    # Les 8 automates pg_cron tournent a la minute, jour et nuit. C'est EUX qui
    # ont echoue le 01/10 (~50 executions perdues) -- pas des utilisateurs.
    print("\n--- 5. les automates ont-ils souffert ? (a lire en ligne) ---")
    dire(INFO, "5. a verifier a la main",
         "cron.job_run_details, fenetre de la descente")
    print("       SELECT to_char(start_time AT TIME ZONE 'Europe/Paris','HH24:MI'),")
    print("              count(*) FILTER (WHERE status <> 'succeeded')")
    print("         FROM cron.job_run_details")
    print("        WHERE start_time > now() - interval '3 hours'")
    print("        GROUP BY 1 HAVING count(*) FILTER (WHERE status <> 'succeeded') > 0;")
    print("       -> AUCUNE LIGNE = la descente n'a gene personne")

    # ─── 6. LE PIEGE QUI RESTE OUVERT ─────────────────────────────────────────
    print("\n--- 6. ce qui n'est PAS corrige (rappel) ---")
    dire(ATTENDU, "6a. 13 autres tables > 1 Mio par page",
         "POIDS_PAGE_MAX=4 Mo > point de rupture 1 Mio")
    dire(ATTENDU, "6b. retire_le n'est jamais adopte",
         "le geste L5 « retirer un mandant » serait efface en une nuit")
    dire(ATTENDU, "6c. etiquette « retard du cloud » perimee",
         "dans relation_disparue.py -- c'est un GAIN, pas un retard")

    print("\n" + "=" * 78)
    print("  OK = conforme   ~~ = connu, non corrige   !!! = a regarder   .. = information")
    print("=" * 78)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
