#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CONTROLE DE LA TACHE « GTI ENTRETIEN DOCUMENTS » (22:00)        15/10/2026

Ecrit la VEILLE de la premiere nuit, pour que le controle du lendemain ne depende
d'aucune conversation : il se joue en une commande et il rend un verdict.

    python phase2/checks/controle_entretien_documents.py

IL NE FAIT QUE LIRE. Aucun appel a Hektor, aucune ecriture, nulle part.
Sortie 0 = tout est vert · 1 = au moins un point rouge · 2 = il n'a pas pu mesurer.

LES CINQ POINTS (les memes que CLAUDE.md §2, item ⑪)
-----------------------------------------------------
 1. LA TACHE a tourne : resultat Windows 0, et ses TROIS lignes sont passees.
    (Elle en avait QUATRE jusqu'au 19/10 : la 4e, les photos, a sa propre tache.)
 2. LES 33 ANNONCES LIBEREES par la purge du 15/10 ont recu leur empreinte.
    ⭐ 32 d'entre elles n'en avaient PAS, donc la detection les sert EN PREMIER.
 3. LE CORRECTIF DU COFFRE a travaille EN REEL : au moins une ligne porte
    `metadata_json.cloud_refuse`. C'est LE temoin -- il valait 0 le 15/10 a 15:40.
    ⚠ Sans lui, un travail serait retombe en erreur : les deux se lisent ensemble.
 4. LES PHOTOS : l'ecart avec le miroir doit avoir fondu (440 a marquer et 1 662 a
    reordonner la veille). Se mesure a part, avec l'outil lui-meme en lecture seule :
        node Console/accorder_photos_miroir.js
    (le script le rappelle, il ne le lance pas : c'est une mesure d'une minute)
 5. LA FILE est vide et AUCUN travail documents n'est en erreur.
    ⚠ L'alerte `data.travaux_en_erreur` compte TOUS les types : il restait 2 travaux
      `change_hektor_annonce_status` de l'AUTRE SESSION le 15/10 a 15:40. Un rouge
      pour ceux-la est ATTENDU et n'est pas une rechute -- le script les compte a part.

LA REFERENCE, FIGEE LE 15/10 A 15:40 (avant la premiere nuit)
--------------------------------------------------------------
    biens en vente     729 dont 726 avec empreinte,     3 sans
    estimations     12 758 dont 12 728 avec empreinte,  30 sans
    vendus/clos      8 943 dont  7 545 avec empreinte, 1 398 sans
    travaux documents en erreur : 0      file : 0
    lignes marquees cloud_refuse : 0     (LE TEMOIN)
    photos : a_marquer 440 (67 annonces) · a_reordonner 1 662 · visible_divergent 0

CE QU'ON ATTEND DE LA PREMIERE NUIT (budgets de la tache, sans parametre)
-------------------------------------------------------------------------
    ligne 1  biens en vente     800 lectures, cap 300  -> les 729 relus
    ligne 2  estimations      2 000 lectures, cap 100  -> les 30 sans empreinte
             sont servies EN PREMIER (empilees SANS lecture), puis ~2 000 relues
    ligne 3  vendus/clos      2 000 lectures, cap 300  -> ~300 des 1 398 traites
    (la ligne photos est partie le 19/10 -> « GTI Entretien Photos », 21:00)
    ⚠ LE CAP EST UN PLAFOND, PAS UN ECHEC : s'il mord, c'est normal le premier soir --
      la tache repasse chaque nuit. Ce qui serait grave : 0 progres, ou un travail en erreur.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ⚠ LA CONSOLE WINDOWS EST EN cp1252 : sans cette ligne, le PREMIER caractere accentue
#   d'ornement (⚠, ✅, ⛔) fait tomber le script en UnicodeEncodeError -- et comme chaque
#   bloc est sous un `except`, l'erreur s'affichait en « impossible a lire », c'est-a-dire
#   un FAUX ROUGE. Trouve par l'essai a blanc du 15/10.
for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = Path(__file__).resolve().parents[2]
JOURNAUX = RACINE / "logs" / "scheduled"
TACHE = "GTI Entretien Documents"

# ── LA REFERENCE DU 15/10 15:40 — elle ne se recalcule pas, c'est son interet ──────
REF = {
    "vente": {"total": 729, "avec": 726, "sans": 3},
    "estimation": {"total": 12758, "avec": 12728, "sans": 30},
    "vendus_clos": {"total": 8943, "avec": 7545, "sans": 1398},
    "doc_en_erreur": 0,
    "autres_en_erreur": 2,
    "cloud_refuse": 0,
    "photos_a_marquer": 440,
    "photos_a_reordonner": 1662,
}

rouges: list[str] = []
oranges: list[str] = []


def load_env_file(path: Path) -> None:
    """Meme patron que monitoring/check_gti_health.py : l'environnement deja pose gagne."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = value.strip().strip('"').strip("'")


for fichier in (RACINE / ".env", RACINE / "Console" / ".env", RACINE / "apps" / "hektor-v1" / ".env"):
    load_env_file(fichier)

URL = (os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL") or "").rstrip("/")
CLE = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
if not URL or not CLE:
    print("ARRET : SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY introuvable.")
    sys.exit(2)


def compter(chemin: str) -> int:
    """Compte EXACT par l'en-tete Content-Range (jamais une page tronquee)."""
    requete = urllib.request.Request(
        f"{URL}/rest/v1/{chemin}",
        headers={"apikey": CLE, "Authorization": f"Bearer {CLE}",
                 "Prefer": "count=exact", "Range": "0-0"},
    )
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        portee = reponse.headers.get("content-range") or ""
    if "/" not in portee:
        raise RuntimeError(f"pas de content-range pour {chemin}")
    total = portee.rsplit("/", 1)[1]
    if total in ("*", ""):
        raise RuntimeError(f"compte inconnu pour {chemin}")
    return int(total)


def lire(chemin: str):
    requete = urllib.request.Request(
        f"{URL}/rest/v1/{chemin}",
        headers={"apikey": CLE, "Authorization": f"Bearer {CLE}"},
    )
    with urllib.request.urlopen(requete, timeout=120) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def titre(texte: str) -> None:
    print()
    print(texte)
    print("-" * len(texte))


def verdict(nom: str, ok: bool, detail: str, grave: bool = True) -> None:
    print(f"  {'OK ' if ok else 'KO '} {nom} -- {detail}")
    if not ok:
        (rouges if grave else oranges).append(f"{nom} : {detail}")


# ══ 1. LA TACHE A-T-ELLE TOURNE, ET SES QUATRE LIGNES SONT-ELLES PASSEES ? ════════
titre("1. LA TACHE DE 22:00")
try:
    brut = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         # ⚠ DEUX PIEGES, les deux vecus le 15/10 a l'essai a blanc :
         #   1. ConvertTo-Json rend un DateTime sous la forme « /Date(943916400000)/ »,
         #      illisible -> on formate EN TEXTE ici ;
         #   2. PowerShell 5.1 n'accepte pas un `if` comme SOUS-EXPRESSION dans un
         #      @{...} : la commande echouait, `info` revenait vide, et le script
         #      sautait les deux verdicts SANS RIEN DIRE. On passe donc par des
         #      instructions separees, et l'absence de reponse est desormais un ROUGE.
         "$i = Get-ScheduledTaskInfo -TaskName '%s'; "
         "$d = ''; if ($i.LastRunTime) { $d = $i.LastRunTime.ToString('yyyy-MM-dd HH:mm:ss') }; "
         "$n = ''; if ($i.NextRunTime) { $n = $i.NextRunTime.ToString('yyyy-MM-dd HH:mm:ss') }; "
         "[pscustomobject]@{ derniere = $d; resultat = $i.LastTaskResult; prochaine = $n } "
         "| ConvertTo-Json -Compress" % TACHE],
        capture_output=True, text=True, timeout=120,
    )
    info = json.loads(brut.stdout.strip() or "{}")
except Exception as erreur:  # pragma: no cover
    info = {}
    verdict("l'etat de la tache se lit", False, f"impossible : {erreur}")

if not info:
    # ⚠ PAS DE SILENCE : une mesure qu'on n'a pas pu faire se DIT. Sans ce rouge, le
    #   script aurait rendu « tout est vert » en n'ayant jamais regarde la tache.
    verdict("l'etat de la tache se lit", False,
            "la commande Windows n'a rien rendu : "
            + (brut.stderr or brut.stdout or "aucune sortie").strip()[:160])
else:
    resultat = info.get("resultat")
    verdict("resultat Windows", resultat == 0,
            f"derniere execution {info.get('derniere')} -> resultat {resultat}"
            + ("" if resultat == 0 else "  (267011 = n'a jamais tourne ; 1 = une ligne a echoue)"))
    verdict("prochaine execution prevue", bool(info.get("prochaine")), str(info.get("prochaine")))

journaux = sorted(JOURNAUX.glob("entretien_documents_*.log"), key=lambda p: p.stat().st_mtime)
if not journaux:
    verdict("le journal de la tache existe", False, f"aucun fichier dans {JOURNAUX}")
else:
    dernier = journaux[-1]
    texte = dernier.read_text(encoding="utf-8", errors="ignore")
    print(f"  (journal : {dernier.name}, {len(texte)} caracteres)")
    # 19/10 : la tache est passee a TROIS lignes -- la 4e (les photos) a sa propre
    #   tache, « GTI Entretien Photos » (21:00). Sans cette correction, ce controle
    #   aurait crie « ligne 4/4 absente » chaque matin sur une tache saine.
    for ligne in ("1/3", "2/3", "3/3"):
        verdict(f"ligne {ligne} presente", f"--- {ligne}" in texte, "dans le journal")
    verdict("aucune ligne en echec", "ECHEC" not in texte.upper(),
            "le journal ne porte pas le mot ECHEC")
    marques = [m for m in ("refuse par le coffre", "budget_atteint", "arret") if m in texte]
    if marques:
        print("  (mots remarques dans le journal : " + ", ".join(marques) + ")")

# ══ 2. LES 33 ANNONCES LIBEREES ONT-ELLES RECU LEUR EMPREINTE ? ═══════════════════
titre("2. LES 33 ANNONCES LIBEREES PAR LA PURGE DU 15/10")
try:
    sauvegarde = lire("app_console_job_erreurs_avant_purge_2026_10_15?select=hektor_annonce_id")
    numeros = sorted({str(r["hektor_annonce_id"]) for r in sauvegarde if r.get("hektor_annonce_id")})
    print(f"  (la sauvegarde datee en porte {len(numeros)})")
    vues = set()
    for debut in range(0, len(numeros), 50):
        lot = numeros[debut:debut + 50]
        filtre = "in.(" + ",".join(urllib.parse.quote(n) for n in lot) + ")"
        for ligne in lire(f"app_console_document_fingerprint?select=hektor_annonce_id,checked_at"
                          f"&hektor_annonce_id={filtre}"):
            vues.add(str(ligne["hektor_annonce_id"]))
    manquantes = [n for n in numeros if n not in vues]
    verdict("toutes portent une empreinte", not manquantes,
            f"{len(vues)}/{len(numeros)}" + ("" if not manquantes else f" -- sans empreinte : {manquantes[:10]}"),
            grave=False)
    if manquantes:
        print("     ⚠ un cap peut les avoir coupees : c'est normal le premier soir,"
              " elles repassent la nuit suivante. Ce qui serait grave, c'est 0 progres.")
except Exception as erreur:
    verdict("les 33 se lisent", False, f"impossible : {erreur}")

# ══ 3. LE TEMOIN DU CORRECTIF : AU MOINS UNE LIGNE MARQUEE `cloud_refuse` ═════════
titre("3. LE CORRECTIF DU COFFRE A-T-IL TRAVAILLE EN REEL ?")
try:
    marquees = compter("app_console_document?select=id&metadata_json=not.is.null"
                       "&metadata_json->cloud_refuse=not.is.null")
    verdict("des documents refuses sont marques et gardes", marquees > REF["cloud_refuse"],
            f"{marquees} ligne(s) portent cloud_refuse (reference de la veille : {REF['cloud_refuse']})",
            grave=False)
    if marquees == 0:
        print("     ⚠ 0 n'est pas forcement un echec : il faut qu'une annonce A TYPE REFUSE soit"
              " repassee cette nuit. A croiser avec le point 5 : si 0 marque ET 0 en erreur,"
              " le sujet n'a simplement pas ete touche.")
except Exception as erreur:
    verdict("le temoin se lit", False, f"impossible : {erreur}")

# ══ 4. LES EMPREINTES PAR INDEX, CONTRE LA REFERENCE DE LA VEILLE ════════════════
titre("4. L'AVANCEE PAR INDEX (reference du 15/10 15:40)")
FAMILLES = {
    "vente": "app_dossier_current?select=hektor_annonce_id&statut_annonce=in.(%22Actif%22,%22Sous%20offre%22,%22Sous%20compromis%22)",
    "estimation": "app_dossier_current?select=hektor_annonce_id&statut_annonce=eq.Estimation",
    "vendus_clos": "app_historical_annonce_index_current?select=hektor_annonce_id",
}
try:
    relues = compter("app_console_document_fingerprint?select=hektor_annonce_id"
                     f"&checked_at=gte.{datetime.now(timezone.utc).date().isoformat()}T00:00:00Z")
    print(f"  empreintes verifiees depuis minuit (UTC) : {relues}")
    verdict("la nuit a relu des annonces", relues > 0, f"{relues} empreintes verifiees")
    for nom, chemin in FAMILLES.items():
        total = compter(chemin)
        print(f"  {nom:<12} total {total} (reference {REF[nom]['total']})")
except Exception as erreur:
    verdict("les index se lisent", False, f"impossible : {erreur}")

# ══ 5. LA FILE ET LES ERREURS ═════════════════════════════════════════════════════
titre("5. LA FILE ET LES TRAVAUX EN ERREUR")
try:
    attente = compter("app_console_job?select=id&status=in.(pending,running)")
    doc_erreur = compter("app_console_job?select=id&job_type=eq.sync_console_documents&status=eq.error")
    tous_erreur = compter("app_console_job?select=id&status=eq.error")
    verdict("la file est vide", attente == 0, f"{attente} travaux en attente ou en cours")
    verdict("aucun travail DOCUMENTS en erreur", doc_erreur == 0,
            f"{doc_erreur} (reference de la veille : {REF['doc_en_erreur']})")
    autres = tous_erreur - doc_erreur
    verdict("les autres types n'ont pas empire", autres <= REF["autres_en_erreur"],
            f"{autres} travaux d'un AUTRE type en erreur (reference : {REF['autres_en_erreur']} --"
            " ce sont ceux de l'autre session, PAS une rechute)", grave=False)
except Exception as erreur:
    verdict("la file se lit", False, f"impossible : {erreur}")

# ══ LE RAPPEL DE LA MESURE QUI SE FAIT A PART ════════════════════════════════════
titre("6. LES PHOTOS -- une mesure a lancer a la main (lecture seule, ~1 min)")
print("  node Console/accorder_photos_miroir.js")
print(f"  ATTENDU : a_marquer et a_reordonner ont FONDU (la veille : {REF['photos_a_marquer']}"
      f" et {REF['photos_a_reordonner']}), visible_divergent reste 0.")
print("  ⚠ L'outil est en lecture seule par defaut : le lancer ne change rien.")

# ══ LE VERDICT ════════════════════════════════════════════════════════════════════
print()
print("=" * 72)
if rouges:
    print(f"⛔ {len(rouges)} POINT(S) ROUGE(S) :")
    for ligne in rouges:
        print(f"   - {ligne}")
if oranges:
    print(f"🟠 {len(oranges)} point(s) a regarder (pas forcement un echec) :")
    for ligne in oranges:
        print(f"   - {ligne}")
if not rouges and not oranges:
    print("✅ TOUT EST VERT.")
print("=" * 72)
sys.exit(1 if rouges else 0)
