#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CONTROLE DU BALAYAGE DES PHOTOS MASQUEES (00:00)                19/10/2026

Ecrit LA VEILLE de la premiere nuit, pour que le controle du lendemain ne depende
d'aucune conversation : il se joue en une commande et il rend un verdict.

    python phase2/checks/controle_balayage_photos_masquees.py

IL NE FAIT QUE LIRE. Aucun appel a Hektor, aucune ecriture, nulle part.
Sortie 0 = tout est vert · 1 = au moins un point rouge · 2 = il n'a pas pu mesurer.

LES HUIT POINTS
---------------
 1. LA TACHE a tourne : resultat Windows 0, son marqueur au journal, « la ligne
    est passee ». ⚠ Un refus (code 3 « file non vide », code 4 « trop d'erreurs »)
    sort en 1 EXPRES -- il est donc ROUGE ici, et c'est voulu : il faut le voir.
 2. LE LOT A ETE POSE : ~1 000 travaux `sync_hektor_photos` crees cette nuit.
 3. IL A ETE DIGERE : combien `done`, combien encore en file, combien en erreur.
 4. ⭐ LE RYTHME REEL. C'EST LE CHIFFRE QUI DECIDE DE LA SUITE : la duree medianne
    d'un travail de cette nuit. La reference historique est 10 s, mais TOUS les
    travaux historiques telechargeaient (4,4 photos en moyenne). Nos annonces ont
    deja leurs visibles, donc 98,5 % ne telechargent RIEN -> on s'attend a PLUS
    RAPIDE. Si c'est le cas, on peut monter le plafond au-dessus de 1 000.
 5. ⭐ LA RECOLTE : combien de photos masquees trouvees, sur combien d'annonces.
    Projection du 19/10 : 1,5 % des annonces, ~2,3 masquees chacune -> on attend
    ~15 annonces et ~35 photos pour un lot de 1 000.
 6. ⚠ AUCUN REFUS DE HEKTOR. C'est le point de securite : un seul 403/429 doit
    arreter le balayage, et il doit se VOIR.
 7. ⭐⭐ LE VERROU TIENT : ZERO photo masquee dans une boite publique. C'est LE
    controle qui compte -- sans lui, les masquees fraichement ramenees partiraient
    sur la vitrine Android, l'espace client et le portail de rapprochement.
 8. LE CURSEUR AVANCE : combien reste-t-il, et combien de nuits a ce rythme.

⚠ « UN CONTROLE QUI AGREGE PERD CE QUI SERT A AGIR » : on n'ecrit jamais « N sur
  M », on ecrit chaque mesure avec sa valeur et sa reference.
"""

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ⚠ LA CONSOLE WINDOWS EST EN cp1252 : sans cette ligne, le PREMIER caractere
#   d'ornement (⚠, ✅, ⛔) fait tomber le script en UnicodeEncodeError -- et comme
#   chaque bloc est sous un `except`, ca s'afficherait en « impossible a lire »,
#   c'est-a-dire un FAUX ROUGE. Defaut vecu le 15/10 sur le controle des documents.
for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = Path(__file__).resolve().parents[2]
JOURNAUX = RACINE / "logs" / "scheduled"
TACHE = "GTI Balayage Photos Masquees"
BASE_COFFRE = "https://dwaqxfrinihnychuoptk.supabase.co/storage/v1/object/public/gti-photo/"

# ── LA REFERENCE FIGEE DU 19/10, AVANT LA PREMIERE NUIT ───────────────────────
# Elle ne se recalcule pas : c'est tout son interet. Si une de ces valeurs bouge
# autrement que prevu, c'est qu'autre chose s'est passe.
REF = {
    "lot_attendu": 1000,
    "travaux_done_avant": 315,
    "annonces_a_faire_avant": 13490,     # 3 a mettre a jour + 13 487 jamais vues
    "masquees_avant": 106,
    "annonces_masquees_avant": 15,
    "masquees_avec_derive_avant": 3,
    "masquees_dans_une_boite_avant": 0,  # ⭐ LE TEMOIN QUI COMPTE
    "duree_medianne_historique_s": 10,
    "taux_masquees_attendu_pct": 1.5,
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


def lire(chemin: str):
    requete = urllib.request.Request(
        f"{URL}/rest/v1/{chemin}",
        headers={"apikey": CLE, "Authorization": f"Bearer {CLE}"},
    )
    with urllib.request.urlopen(requete, timeout=90) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def compter(chemin: str) -> int:
    """Compte EXACT par l'en-tete Content-Range (jamais une page tronquee)."""
    requete = urllib.request.Request(
        f"{URL}/rest/v1/{chemin}",
        headers={"apikey": CLE, "Authorization": f"Bearer {CLE}",
                 "Prefer": "count=exact", "Range": "0-0"},
    )
    with urllib.request.urlopen(requete, timeout=90) as reponse:
        portee = reponse.headers.get("content-range") or ""
    if "/" not in portee:
        raise RuntimeError(f"pas de content-range pour {chemin}")
    total = portee.rsplit("/", 1)[1]
    if total in ("*", ""):
        raise RuntimeError(f"compte inconnu pour {chemin}")
    return int(total)


def titre(texte: str) -> None:
    print(f"\n{texte}\n" + "-" * len(texte))


def ligne(nom: str, valeur, reference=None, verdict: str = "") -> None:
    ref = f"   (reference : {reference})" if reference is not None else ""
    print(f"  {nom:<44} {valeur}{ref}  {verdict}")


# ═══════════════════════════════════════════════════════════════════════════════
print(f"CONTROLE DU BALAYAGE DES PHOTOS MASQUEES -- {datetime.now():%Y-%m-%d %H:%M}")
print(f"reference figee le 19/10/2026, avant la premiere nuit")

# ── ① LA TACHE WINDOWS ────────────────────────────────────────────────────────
titre("① LA TACHE A-T-ELLE TOURNE ?")
try:
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"$t=Get-ScheduledTask -TaskName '{TACHE}';"
        "if($t){$i=$t|Get-ScheduledTaskInfo;"
        "[pscustomobject]@{State=[string]$t.State;Result=$i.LastTaskResult;"
        "Last=[string]$i.LastRunTime;Next=[string]$i.NextRunTime}|ConvertTo-Json -Compress}"
        "else{'{}'}"
    )
    proc = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                          capture_output=True, text=True, timeout=60)
    info = json.loads((proc.stdout or "{}").strip() or "{}")
    if not info:
        rouges.append("la tache est introuvable dans Windows")
        ligne("etat", "INTROUVABLE", "Ready", "⛔ ROUGE")
    else:
        ligne("etat", info.get("State"), "Ready")
        ligne("derniere passe", info.get("Last") or "(jamais)")
        res = info.get("Result")
        # 0 = succes · 267009 = en cours · 267011 = jamais lancee
        if res == 0:
            ligne("dernier resultat", res, 0, "✅")
        elif res in (267009, 267011):
            oranges.append(f"la tache n'a pas encore tourne (resultat {res})")
            ligne("dernier resultat", res, 0, "🟠 pas encore tournee")
        else:
            # ⚠ 1 = ECHEC *OU* REFUS VOLONTAIRE (code 3 file non vide, code 4 erreurs).
            #   Le journal dira lequel -- c'est pour ca qu'on le lit juste apres.
            rouges.append(f"la tache est sortie en {res}")
            ligne("dernier resultat", res, 0, "⛔ ROUGE -- lire le journal ci-dessous")
except Exception as exc:  # noqa: BLE001
    oranges.append(f"etat de la tache non mesurable : {exc}")
    ligne("etat de la tache", f"non mesurable ({exc})", None, "🟠")

# ── ② LE JOURNAL DE LA NUIT ───────────────────────────────────────────────────
titre("② LE JOURNAL PORTE-T-IL SES MARQUEURS ?")
try:
    fichiers = sorted(JOURNAUX.glob("balayage_photos_masquees_*.log"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    if not fichiers:
        rouges.append("aucun journal de balayage")
        ligne("journal", "AUCUN", "un par nuit", "⛔ ROUGE")
    else:
        dernier = fichiers[0]
        texte = dernier.read_text(encoding="utf-8", errors="replace")
        ligne("journal", dernier.name)
        ligne("taille", f"{len(texte)} caracteres")
        for attendu, nom in (("--- 1/1 l'EMPILEUR", "le marqueur de ligne"),
                             ("la ligne est passee", "la phrase de fin")):
            if attendu in texte:
                ligne(nom, "present", None, "✅")
            else:
                rouges.append(f"{nom} absent du journal")
                ligne(nom, "ABSENT", attendu, "⛔ ROUGE")
        # ⚠ LES DEUX REFUS SE LISENT ICI, nommement -- sinon « sortie 1 » ne dit
        #   pas SI c'est une panne ou la garde qui a fait son travail.
        for marque, quoi in (("REFUS 3", "la file n'etait pas vide -> baisser -Limite"),
                             ("REFUS 4", "trop d'erreurs en 24 h -> Hektor nous rejette")):
            if marque in texte:
                rouges.append(f"{marque} : {quoi}")
                ligne(marque, "PRESENT", None, f"⛔ {quoi}")
except Exception as exc:  # noqa: BLE001
    oranges.append(f"journal non lisible : {exc}")
    ligne("journal", f"non lisible ({exc})", None, "🟠")

# ── ③ LE LOT A-T-IL ETE POSE, ET DIGERE ? ─────────────────────────────────────
titre("③ LE LOT : POSE, DIGERE ?")
depuis = (datetime.now(timezone.utc) - timedelta(hours=18)).isoformat()
q = urllib.parse.quote(depuis, safe="")
try:
    poses = compter(f"app_console_job?select=id&job_type=eq.sync_hektor_photos&requested_at=gte.{q}")
    faits = compter(f"app_console_job?select=id&job_type=eq.sync_hektor_photos&status=eq.done&requested_at=gte.{q}")
    enfile = compter("app_console_job?select=id&job_type=eq.sync_hektor_photos&status=in.(pending,running)")
    erreurs = compter(f"app_console_job?select=id&job_type=eq.sync_hektor_photos&status=eq.error&requested_at=gte.{q}")

    ligne("travaux poses cette nuit", poses, REF["lot_attendu"],
          "✅" if poses >= REF["lot_attendu"] * 0.9 else "🟠 moins que le lot")
    if poses < REF["lot_attendu"] * 0.9:
        oranges.append(f"{poses} travaux poses au lieu de ~{REF['lot_attendu']}")
    ligne("dont TERMINES", faits, poses, "✅" if faits == poses else "🟠 reste a digerer")
    ligne("encore en file (tous lots)", enfile, 0,
          "✅" if enfile == 0 else "🟠 le lot de ce soir sera REFUSE si ca reste")
    if enfile > 0:
        oranges.append(f"{enfile} travaux encore en file -> le lot de ce soir sera refuse (code 3)")
    ligne("EN ERREUR", erreurs, 0, "✅" if erreurs == 0 else "⛔ ROUGE")
    if erreurs > 0:
        rouges.append(f"{erreurs} travaux en erreur -- NE JAMAIS LES REJOUER, les regarder")
except Exception as exc:  # noqa: BLE001
    oranges.append(f"file non mesurable : {exc}")
    ligne("la file", f"non mesurable ({exc})", None, "🟠")

# ── ④ LE RYTHME REEL -- LE CHIFFRE QUI DECIDE DE LA SUITE ─────────────────────
titre("④ ⭐ LE RYTHME REEL (c'est lui qui dit si on peut monter le plafond)")
try:
    lignes = lire(f"app_console_job?select=started_at,finished_at,result_json"
                  f"&job_type=eq.sync_hektor_photos&status=eq.done"
                  f"&requested_at=gte.{q}&limit=2000")
    durees = []
    for r in lignes:
        a, b = r.get("started_at"), r.get("finished_at")
        if not a or not b:
            continue
        try:
            durees.append((datetime.fromisoformat(b.replace("Z", "+00:00"))
                           - datetime.fromisoformat(a.replace("Z", "+00:00"))).total_seconds())
        except Exception:
            continue
    # ⚠⚠ UN VERDICT SUR UN ECHANTILLON DE 1 N'EST PAS UN VERDICT. Joue le 19/10 au
    #   soir, ce bloc a conseille « baisser le plafond a 114 » -- sur UN SEUL travail,
    #   celui de l'essai du matin, qui etait LE PLUS LENT DES 315 (78,9 s : il
    #   telechargeait 3 photos et fabriquait leurs derives). On exige donc un
    #   minimum avant de conseiller quoi que ce soit.
    #   (Meme famille que « une mesure approximative vaut une mesure fausse ».)
    MINI_ECHANTILLON = 20
    if not durees:
        oranges.append("aucune duree mesurable (aucun travail termine)")
        ligne("duree medianne", "non mesurable", REF["duree_medianne_historique_s"], "🟠")
    elif len(durees) < MINI_ECHANTILLON:
        durees.sort()
        ligne("travaux mesures", len(durees), f">= {MINI_ECHANTILLON} pour conclure", "🟠 trop peu")
        ligne("duree medianne (s)", round(durees[len(durees) // 2], 1),
              REF["duree_medianne_historique_s"], "-- INDICATIF, pas un verdict")
        oranges.append(f"rythme NON CONCLUANT : {len(durees)} travail(aux) mesure(s),"
                       f" il en faut {MINI_ECHANTILLON}. Aucun conseil de plafond.")
    else:
        durees.sort()
        med = durees[len(durees) // 2]
        ligne("travaux mesures", len(durees))
        ligne("duree MEDIANNE (s)", round(med, 1), REF["duree_medianne_historique_s"])
        ligne("la plus lente (s)", round(durees[-1], 1))
        # ⭐ LA CONCLUSION CHIFFREE : combien tiennent dans les 2 h 30 de la fenetre.
        tiennent = int(9000 / med) if med > 0 else 0
        ligne("tiennent dans 2 h 30", f"{tiennent} annonces", REF["lot_attendu"])
        if tiennent >= REF["lot_attendu"] * 1.5:
            print(f"\n  ⭐ ON PEUT MONTER LE PLAFOND : a {round(med,1)} s par annonce, "
                  f"{tiennent} tiennent dans la fenetre.")
            print(f"     ⚠ MAIS LE QUOTA HEKTOR BORNE AUSSI : chaque annonce coute 2 requetes, "
                  f"et la nuit en consomme deja ~4 500.")
            print(f"     Rester sous ~2 250 annonces (4 500 requetes) pour tenir la cible du 20/08.")
        elif tiennent < REF["lot_attendu"]:
            oranges.append(f"a {round(med,1)} s/annonce, seules {tiennent} tiennent dans la fenetre"
                           f" -> baisser -Limite a {tiennent}")
            ligne("verdict", f"BAISSER le plafond a ~{tiennent}", None, "🟠")
except Exception as exc:  # noqa: BLE001
    oranges.append(f"rythme non mesurable : {exc}")
    ligne("le rythme", f"non mesurable ({exc})", None, "🟠")

# ── ⑤ LA RECOLTE ──────────────────────────────────────────────────────────────
titre("⑤ ⭐ LA RECOLTE : combien de masquees ramenees ?")
try:
    masquees = compter("app_console_photo?select=id&visible=is.false")
    annonces = len({r["app_dossier_id"] for r in
                    lire("app_console_photo?select=app_dossier_id&visible=is.false&limit=5000")})
    ligne("photos masquees chez nous", masquees, REF["masquees_avant"],
          "✅ en hausse" if masquees > REF["masquees_avant"] else "🟠 inchange")
    if masquees <= REF["masquees_avant"]:
        oranges.append("aucune masquee ramenee cette nuit -- normal si le lot est tombe sur des"
                       " annonces sans masquee (taux attendu 1,5 %), suspect deux nuits de suite")
    ligne("annonces qui en portent", annonces, REF["annonces_masquees_avant"])
    ligne("gagnees cette nuit", masquees - REF["masquees_avant"],
          f"~35 attendues pour 1 000 annonces")
except Exception as exc:  # noqa: BLE001
    oranges.append(f"recolte non mesurable : {exc}")
    ligne("la recolte", f"non mesurable ({exc})", None, "🟠")

# ── ⑥ AUCUN REFUS DE HEKTOR ───────────────────────────────────────────────────
titre("⑥ ⚠ HEKTOR NOUS A-T-IL REFUSE QUELQUE CHOSE ?")
try:
    msgs = lire(f"app_console_job?select=hektor_annonce_id,error_message"
                f"&job_type=eq.sync_hektor_photos&status=eq.error&requested_at=gte.{q}&limit=50")
    refus = [m for m in msgs if any(c in str(m.get("error_message") or "")
                                    for c in ("403", "429", "503", "401"))]
    ligne("travaux en erreur", len(msgs), 0, "✅" if not msgs else "⛔ ROUGE")
    ligne("dont un REFUS de Hektor", len(refus), 0, "✅" if not refus else "⛔⛔ ARRETER LE BALAYAGE")
    if refus:
        rouges.append(f"{len(refus)} REFUS DE HEKTOR -- desactiver la tache et ne RIEN rejouer")
        for m in refus[:5]:
            ligne(f"  annonce {m.get('hektor_annonce_id')}", str(m.get("error_message"))[:70])
except Exception as exc:  # noqa: BLE001
    oranges.append(f"refus non mesurables : {exc}")
    ligne("les refus", f"non mesurables ({exc})", None, "🟠")

# ── ⑦ LE VERROU TIENT-IL ? -- LE CONTROLE QUI COMPTE ──────────────────────────
titre("⑦ ⭐⭐ LE VERROU : une masquee est-elle sortie dans une BOITE PUBLIQUE ?")
try:
    avec_derive = compter("app_console_photo?select=id&visible=is.false"
                          "&present_in_hektor=is.true&derives_json=not.is.null")
    ligne("masquees avec un derive (la vanne)", avec_derive, REF["masquees_avec_derive_avant"])
    # ⚠ On reproduit EXACTEMENT ce que la fonction produirait, cote lecture : une
    #   masquee ne doit JAMAIS figurer dans images_preview_json_app.
    chemins = {BASE_COFFRE + (r["derives_json"] or {}).get("w400", {}).get("chemin", "")
               for r in lire("app_console_photo?select=derives_json&visible=is.false"
                             "&present_in_hektor=is.true&derives_json=not.is.null&limit=2000")
               if (r.get("derives_json") or {}).get("w400")}
    fuites = 0
    exemples = []
    for d in lire("app_dossier_current?select=app_dossier_id,images_preview_json_app"
                  "&images_preview_json_app=not.is.null&limit=20000"):
        for e in (d.get("images_preview_json_app") or []):
            if isinstance(e, dict) and e.get("url") in chemins:
                fuites += 1
                if len(exemples) < 5:
                    exemples.append(d.get("app_dossier_id"))
    ligne("masquees dans une boite PUBLIQUE", fuites, REF["masquees_dans_une_boite_avant"],
          "✅ LE VERROU TIENT" if fuites == 0 else "⛔⛔ FUITE")
    if fuites:
        rouges.append(f"⛔⛔ {fuites} masquee(s) dans une boite publique -- annonces {exemples}."
                      " Verifier que le patch des deux boites est toujours en place.")
except Exception as exc:  # noqa: BLE001
    # ⚠ ON NE CONCLUT PAS AU VERT SI ON N'A PAS PU MESURER : c'est le controle
    #   le plus important du fichier.
    rouges.append(f"LE VERROU N'A PAS PU ETRE MESURE : {exc} -- ne pas conclure au vert")
    ligne("le verrou", f"NON MESURE ({exc})", None, "⛔ ROUGE par prudence")

# ── ⑧ LE CURSEUR AVANCE-T-IL ? ────────────────────────────────────────────────
titre("⑧ COMBIEN RESTE-T-IL ?")
try:
    noeud = RACINE / "Console" / "enqueue_photos_masquees_lot.js"
    exe = os.environ.get("CONSOLE_NODE_EXE") or r"C:\Program Files\nodejs\node.exe"
    proc = subprocess.run([exe, str(noeud), "--dry-run"],
                          capture_output=True, text=True, timeout=600, cwd=str(RACINE))
    bilan = json.loads(proc.stdout[proc.stdout.index("{"):proc.stdout.rindex("}") + 1])
    reste = bilan.get("part_mise_a_jour_disponible", 0) + bilan.get("part_balayage_disponible", 0)
    ligne("deja visitees", bilan.get("deja_visitees"), REF["travaux_done_avant"])
    ligne("RESTE A FAIRE", reste, REF["annonces_a_faire_avant"],
          "✅ ca avance" if reste < REF["annonces_a_faire_avant"] else "🟠 rien n'a avance")
    if reste >= REF["annonces_a_faire_avant"]:
        oranges.append("le curseur n'a pas avance")
    ligne("nuits restantes", bilan.get("nuits_restantes_a_ce_rythme"))
    ligne("ecartees pour erreur", bilan.get("ecartees_pour_erreur"), 0)
    if bilan.get("ecartees_pour_erreur"):
        oranges.append(f"{bilan['ecartees_pour_erreur']} annonces ecartees pour erreur"
                       f" -- exclues des passages AUTOMATIQUES, a rejouer exprès si besoin :"
                       f" {bilan.get('exemples_ecartees')}")
except Exception as exc:  # noqa: BLE001
    oranges.append(f"curseur non mesurable : {exc}")
    ligne("le curseur", f"non mesurable ({exc})", None, "🟠")

# ═══════════════════════════════════════════════════════════════════════════════
titre("LE VERDICT")
if rouges:
    print(f"  ⛔ {len(rouges)} ROUGE(S) :")
    for r in rouges:
        print(f"     - {r}")
if oranges:
    print(f"  🟠 {len(oranges)} point(s) a regarder :")
    for o in oranges:
        print(f"     - {o}")
if not rouges and not oranges:
    print("  ✅ TOUT VERT.")
print()
sys.exit(1 if rouges else 0)
