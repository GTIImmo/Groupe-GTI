#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CONTROLE DU CORRECTIF « DOMAINE DES DOCUMENTS »                  20/10/2026

Ecrit LE SOIR DE LA POSE, pour que le controle du lendemain ne depende d'aucune
conversation : il se joue en une commande et il rend un verdict.

    python phase2/checks/controle_domaine_documents.py

IL NE FAIT QUE LIRE. Aucun appel a Hektor, aucune ecriture, nulle part.
Sortie 0 = tout est vert · 1 = au moins un point rouge · 2 = il n'a pas pu mesurer.

CE QU'ON CORRIGE
---------------
`hektor_document_id` etait le sha1 de l'ADRESSE COMPLETE du fichier, domaine
compris. Le 11/09/2026 le portail Hektor a demenage :
    groupe-gti-immobilier.la-boite-immo.com  ->  www.gti-immobilier.fr
Meme fichier, AUTRE NUMERO : le worker ne reconnaissait plus la fiche, en creait
une neuve, et `pruneDeletedDocuments` supprimait l'ancienne.
Depuis le 20/10 a 20:30, `reconcilierParChemin()` RE-CLE la fiche existante par un
PATCH avant l'upsert, et le prune a deux garde-fous.
Tout est ecrit dans notice/AUDIT_DOMAINE_DOCUMENTS_2026-10-20.md.

⭐⭐ LE TEMOIN, ET IL EST DEJA DANS LA BASE
   Une fiche RE-CLEE garde sa date de naissance. Une fiche SUPPRIMEE PUIS RECREEE
   en porte une neuve. Donc : parmi les fiches passees au NOUVEAU domaine, celles
   qui sont nees AVANT le 11/09 sont celles qu'on a su reconnaitre.
   Mesure du 20/10, AVANT la pose : 716 sur 164 229, soit 0,4 %. C'est la
   reference. Elle doit MONTER, et elle ne peut que monter.

⚠ « UN CONTROLE QUI AGREGE PERD CE QUI SERT A AGIR » : jamais un « N sur M » seul.
  Chaque mesure sort avec sa valeur, sa reference, et les annonces NOMMEES.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# ⚠ LA CONSOLE WINDOWS EST EN cp1252 : sans cette ligne, le premier ornement
#   (⚠, ✅, ⛔) tombe en UnicodeEncodeError -- donc un FAUX ROUGE.
for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = Path(__file__).resolve().parents[2]

ANCIEN = "la-boite-immo.com"
BASCULE = "2026-09-11"
# ⏰ L'INSTANT DE LA POSE : les 4 services ont redemarre a 20:30:46-47 le 20/10.
POSE = "2026-10-20T20:30:47+02:00"

# ── LA REFERENCE FIGEE DU 20/10, AVANT LA POSE ────────────────────────────────
# Elle ne se recalcule pas : c'est tout son interet.
REF = {
    "a_l_ancien_domaine": 28363,        # doit BAISSER
    "au_nouveau_domaine": 164229,
    "reclees_avant_la_pose": 716,       # ⭐⭐ LE TEMOIN -- doit MONTER
    "travaux_du_bug": 2330,
    "fiches_remplacees": 15403,
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


for fichier in (RACINE / ".env", RACINE / "Console" / ".env",
                RACINE / "apps" / "hektor-v1" / ".env"):
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
    with urllib.request.urlopen(requete, timeout=120) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def compter(chemin: str) -> int:
    """Compte EXACT par l'en-tete Content-Range (jamais une page tronquee)."""
    separateur = "&" if "?" in chemin else "?"
    requete = urllib.request.Request(
        f"{URL}/rest/v1/{chemin}{separateur}select=id&limit=1",
        headers={"apikey": CLE, "Authorization": f"Bearer {CLE}",
                 "Prefer": "count=exact", "Range": "0-0"},
    )
    with urllib.request.urlopen(requete, timeout=120) as reponse:
        plage = reponse.headers.get("Content-Range") or ""
    if "/" not in plage:
        raise RuntimeError(f"pas de Content-Range sur {chemin}")
    return int(plage.rsplit("/", 1)[1])


def q(valeur: str) -> str:
    return urllib.parse.quote(valeur, safe="")


print("=" * 78)
print("CONTROLE DU CORRECTIF « DOMAINE DES DOCUMENTS »")
print("  pose le 20/10/2026 a 20:30:47 (les 4 services)   commit c82d973")
print("=" * 78)

# ─────────────────────────────────────────────────────────────────────────────
# 1. ⭐⭐ LE TEMOIN QUI COMPTE : les fiches RECONNUES par leur chemin
# ─────────────────────────────────────────────────────────────────────────────
print("\n1. ⭐⭐ LE TEMOIN : les fiches RECONNUES (elles gardent leur date de naissance)")
try:
    base = ("app_console_document?source=like.hektor_console*"
            f"&metadata_json->>console_url=not.like.*{q(ANCIEN)}*")
    au_nouveau = compter(base + "&metadata_json->>console_url=not.is.null")
    reclees = compter(base + f"&metadata_json->>console_url=not.is.null&created_at=lt.{BASCULE}")
    gagne = reclees - REF["reclees_avant_la_pose"]
    print(f"   au NOUVEAU domaine        : {au_nouveau:>7}   (reference {REF['au_nouveau_domaine']})")
    print(f"   dont nees AVANT la bascule: {reclees:>7}   (reference {REF['reclees_avant_la_pose']})")
    print(f"   ⭐ RECONNUES DEPUIS LA POSE : {gagne:>7}")
    if gagne > 0:
        print("   ✅ LE CORRECTIF MORD : des fiches ont ete re-clees au lieu d'etre remplacees.")
    else:
        oranges.append("aucune fiche re-clee encore -- le balayage n'a peut-etre pas "
                       "touche d'annonce a l'ancien domaine depuis la pose")
        print("   ⚠ aucune encore. Ce n'est un ROUGE que si des annonces a l'ancien")
        print("     domaine ont ete synchronisees depuis la pose (voir le point 3).")
except Exception as exc:
    rouges.append(f"temoin des re-clages impossible a mesurer : {exc}")
    print(f"   ⛔ impossible a mesurer : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. LE CURSEUR : combien reste-t-il a l'ancien domaine
# ─────────────────────────────────────────────────────────────────────────────
print("\n2. LE CURSEUR : ce qui reste a l'ancien domaine")
try:
    reste = compter("app_console_document?source=like.hektor_console*"
                    f"&metadata_json->>console_url=like.*{q(ANCIEN)}*")
    print(f"   fiches a l'ancien domaine : {reste:>7}   (reference {REF['a_l_ancien_domaine']})")
    if reste < REF["a_l_ancien_domaine"]:
        print(f"   ✅ il BAISSE : {REF['a_l_ancien_domaine'] - reste} fiches sont passees.")
    elif reste == REF["a_l_ancien_domaine"]:
        print("   ⚠ inchange : aucune annonce de ce lot n'a ete synchronisee depuis.")
    else:
        rouges.append(f"le reste a l'ancien domaine a AUGMENTE ({reste} > "
                      f"{REF['a_l_ancien_domaine']}) -- ca ne doit pas arriver")
        print("   ⛔ il AUGMENTE. Ca ne doit pas arriver : quelque chose recree de l'ancien.")
except Exception as exc:
    rouges.append(f"curseur impossible a mesurer : {exc}")
    print(f"   ⛔ impossible a mesurer : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. LA SAIGNEE : les suppressions en masse depuis la pose, ANNONCE PAR ANNONCE
# ─────────────────────────────────────────────────────────────────────────────
print("\n3. LA SAIGNEE : les travaux documents depuis la pose, et ce qu'ils ont supprime")
try:
    travaux = lire(
        "app_console_job?job_type=eq.sync_console_documents"
        f"&finished_at=gte.{q(POSE)}"
        "&select=id,hektor_annonce_id,status,result_json,finished_at"
        "&order=finished_at.desc&limit=400")
    if not travaux:
        print("   (aucun travail documents fini depuis la pose -- rien a juger encore)")
        print("   ⏰ Le balayage pose ~330 travaux par nuit : revenir apres 22:00.")
    else:
        gros = []
        total_pruned = 0
        for t in travaux:
            r = t.get("result_json") or {}
            pruned = int(r.get("pruned") or 0)
            total_pruned += pruned
            indexed = int(r.get("indexed") or 0)
            if pruned >= 2 and pruned * 2 >= max(indexed, 1):
                gros.append((t.get("hektor_annonce_id"), pruned, indexed,
                             (t.get("finished_at") or "")[:19]))
        print(f"   travaux finis depuis la pose : {len(travaux)}")
        print(f"   fiches supprimees en tout    : {total_pruned}")
        if gros:
            rouges.append(f"{len(gros)} travaux ont encore supprime en bloc apres la pose")
            print("   ⛔ DES SUPPRESSIONS EN BLOC SONT PASSEES -- une ligne par annonce :")
            for annonce, pruned, indexed, quand in gros[:20]:
                print(f"      annonce {annonce:<9} supprimees {pruned:<4} deposees {indexed:<4} {quand}")
        else:
            print("   ✅ AUCUNE suppression en bloc depuis la pose.")
except Exception as exc:
    rouges.append(f"saignee impossible a mesurer : {exc}")
    print(f"   ⛔ impossible a mesurer : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. LES DEUX GARDE-FOUS ONT-ILS PARLE ? (le journal des travaux)
# ─────────────────────────────────────────────────────────────────────────────
print("\n4. CE QUE LES GARDE-FOUS ONT ECRIT AU JOURNAL")
for libelle, motif in (("re-clages par le CHEMIN", "reconnus par leur chemin"),
                       ("refus de suppression EN BLOC", "SUPPRESSION EN BLOC REFUSEE")):
    try:
        lignes = lire("app_console_job_log?"
                      # ⚠ ilike, PAS like : le message ecrit « CHEMIN » en majuscules et
                      #   un `like` distingue la casse -- ce controle a rendu un FAUX 0
                      #   le 21/10 alors que le journal portait bien sa ligne.
                      f"message=ilike.*{q(motif)}*&created_at=gte.{q(POSE)}"
                      "&select=job_id,message,payload_preview,created_at"
                      "&order=created_at.desc&limit=12")
        print(f"   {libelle:<32} {len(lignes)} ligne(s)")
        for l in lignes[:6]:
            apercu = (l.get("payload_preview") or "")[:92]
            print(f"      {(l.get('created_at') or '')[:19]}  {apercu}")
    except Exception as exc:
        oranges.append(f"journal « {libelle} » illisible : {exc}")
        print(f"   ⚠ illisible : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. ⚠⚠ LE TEMOIN INVERSE : une VRAIE suppression passe-t-elle TOUJOURS ?
#    Un garde-fou qui bloque tout protege de tout, y compris de ce qu'on veut.
# ─────────────────────────────────────────────────────────────────────────────
print("\n5. ⚠⚠ TEMOIN INVERSE : les suppressions LEGITIMES passent-elles encore ?")
try:
    travaux = lire("app_console_job?job_type=eq.sync_console_documents"
                   f"&finished_at=gte.{q(POSE)}"
                   "&select=hektor_annonce_id,result_json&order=finished_at.desc&limit=400")
    isolees = [(t.get("hektor_annonce_id"), int((t.get("result_json") or {}).get("pruned") or 0))
               for t in travaux
               if 0 < int((t.get("result_json") or {}).get("pruned") or 0) < 2]
    if not travaux:
        print("   (rien a juger encore -- revenir apres le balayage de 22:00)")
    elif isolees:
        print(f"   ✅ {len(isolees)} suppression(s) isolee(s) sont passees -- le garde-fou")
        print("      ne bloque pas tout. Les annonces concernees :")
        for annonce, n in isolees[:8]:
            print(f"      annonce {annonce:<9} {n} fiche(s) retiree(s)")
    else:
        print("   ⚠ aucune suppression isolee depuis la pose. Ce n'est PAS un rouge en soi")
        print("     (elles sont rares : 20 fiches en 2 mois avant le bug), mais si ca dure")
        print("     plusieurs semaines, verifier que le niveau 2 ne bloque pas tout.")
except Exception as exc:
    oranges.append(f"temoin inverse impossible a mesurer : {exc}")
    print(f"   ⚠ impossible a mesurer : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. ⚠ LE COUT HEKTOR : les fichiers reellement RETELECHARGES depuis la pose
# ─────────────────────────────────────────────────────────────────────────────
print("\n6. ⚠ LE COUT HEKTOR : fiches NEUVES creees depuis la pose")
print("   (le mur de Hektor est un quota de VOLUME, et notre IP a ete bannie les 19-20/08)")
try:
    neuves = compter("app_console_document?source=like.hektor_console*"
                     f"&created_at=gte.{q(POSE)}")
    print(f"   fiches creees depuis la pose : {neuves:>7}")
    print(f"   pour memoire, le bug en avait recree {REF['fiches_remplacees']} en 25 jours")
    print("   ➡ une fiche re-clee ne compte PAS ici : c'est tout l'objet du correctif.")
except Exception as exc:
    oranges.append(f"cout Hektor impossible a mesurer : {exc}")
    print(f"   ⚠ impossible a mesurer : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. AUCUN REFUS DE HEKTOR
# ─────────────────────────────────────────────────────────────────────────────
print("\n7. AUCUN REFUS DE HEKTOR sur les travaux documents")
try:
    echecs = lire("app_console_job?job_type=eq.sync_console_documents"
                  f"&status=eq.error&finished_at=gte.{q(POSE)}"
                  "&select=hektor_annonce_id,error_message,finished_at"
                  "&order=finished_at.desc&limit=12")
    if not echecs:
        print("   ✅ aucun echec depuis la pose.")
    else:
        rouges.append(f"{len(echecs)} travaux documents en erreur depuis la pose")
        print(f"   ⛔ {len(echecs)} en erreur -- une ligne par annonce :")
        for e in echecs:
            msg = (e.get("error_message") or "")[:84]
            print(f"      annonce {e.get('hektor_annonce_id'):<9} {msg}")
        print("   ⛔ SI C'EST UN 403 OU UN 429 : NE RIEN REJOUER. Hektor nous rejette.")
except Exception as exc:
    rouges.append(f"refus Hektor impossible a mesurer : {exc}")
    print(f"   ⛔ impossible a mesurer : {exc}")

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 78)
if rouges:
    print(f"⛔ {len(rouges)} POINT(S) ROUGE(S) :")
    for r in rouges:
        print(f"   · {r}")
if oranges:
    print(f"⚠ {len(oranges)} point(s) a surveiller :")
    for o in oranges:
        print(f"   · {o}")
if not rouges and not oranges:
    print("✅ TOUT EST VERT.")
print("=" * 78)
sys.exit(1 if rouges else 0)
