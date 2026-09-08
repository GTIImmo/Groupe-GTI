"""VÉRIFICATION DES TROIS COPIES DE LA RÈGLE DE CHAÎNAGE — 08/09/2026

Demandée par Frédéric avant d'ouvrir la modale aux offres mortes :
    « avant de décider je te demande d'écrire une vérification des règles
      chaînage etc. pour être sûr — consulte bien mon code actuel, ne te base
      pas que sur les notes. »

⚠ CE SCRIPT NE LIT QUE. Aucune écriture, ni chez Hektor, ni dans le registre.

═══ POURQUOI TROIS COPIES, ET POURQUOI IL FAUT LES CONFRONTER ═══
La règle de chaînage est écrite TROIS FOIS, dans trois langages :

  ① phase2/sync/affaire_ledger.py   recalculer_les_chaines()
       reconstruit TOUTES les chaînes à chaque run de nuit
  ② Supabase                        app_chaine_pour(annonce, acquereur, kind, id)
       choisit la chaîne d'un bloc créé DEPUIS L'APP, en optimiste
  ③ apps/hektor-v1/src/App.tsx      affaireEstVivante + dossiersOuvertsDuBien
       recalculé À CHAQUE AFFICHAGE de la modale et de la rubrique Affaires

« Deux copies d'une formule divergent tôt ou tard » — règle du projet. Ce script
les transcrit depuis LE CODE (chaque fonction cite sa source) et les fait juger
la même donnée, ligne par ligne.

   python phase2/checks/verifier_regle_chainage.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[2])
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from phase2.sync.push_upgrade_to_supabase import load_env_files  # noqa: E402

load_env_files([Path(".env"), Path("apps/hektor-v1/.env")])
URL = os.environ.get("SUPABASE_URL") or os.environ["VITE_SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

MORTS_OFFRE = {"refused", "refusee"}
MORTS_COMPROMIS = {"cancelled", "annule"}
ACCEPTEE = {"accepted", "acceptee"}


def lire_registre() -> list[dict]:
    """Le registre entier, par pages -- lecture seule."""
    champs = ("app_affaire_id,app_chaine_id,hektor_annonce_id,kind,state,"
              "hektor_affaire_id,present_in_hektor,date,hektor_acquereur_id")
    lignes, page = [], 0
    while True:
        q = urllib.parse.urlencode({
            "select": champs, "order": "app_affaire_id.asc",
            "limit": 1000, "offset": page * 1000})
        r = urllib.request.Request(f"{URL}/rest/v1/app_affaire_ledger?{q}",
                                   headers={"apikey": KEY, "Authorization": "Bearer " + KEY})
        lot = json.loads(urllib.request.urlopen(r).read().decode())
        lignes.extend(lot)
        if len(lot) < 1000:
            return lignes
        page += 1


def etat(l: dict) -> str:
    return str(l.get("state") or "").strip().lower()


def effacee_chez_hektor(l: dict) -> bool:
    """③ App.tsx, dossiersOuvertsDuBien :
       `Boolean(String(a.hektor_affaire_id ?? '').trim()) && a.present_in_hektor === false`
       ② Supabase, app_chaine_pour, les trois branches :
       `not (btrim(coalesce(hektor_affaire_id::text,'')) <> '' and present_in_hektor is false)`
       Les deux disent la même chose."""
    return bool(str(l.get("hektor_affaire_id") or "").strip()) and l.get("present_in_hektor") is False


# ═══════════════════════════════════════════════════════════════════════════════
# ③ LE FRONT — transcription littérale de dossiersOuvertsDuBien (App.tsx)
# ═══════════════════════════════════════════════════════════════════════════════
def ouvert_selon_le_front(membres: list[dict]) -> bool:
    """App.tsx :
           const ouvert = !vente
             && (!aCompromis || compromisVivant)
             && (aCompromis || !aOffre || offreVivante)
       avec compromisVivant = state ∉ {cancelled, annule}
            offreVivante    = state ∉ {refused, refusee}
       et les lignes effacées chez Hektor écartées AVANT le regroupement."""
    vente = False
    a_compromis = compromis_vivant = a_offre = offre_vivante = False
    for m in membres:
        k = str(m.get("kind"))
        if k == "vente":
            vente = True
        elif k == "compromis":
            a_compromis = True
            if etat(m) not in MORTS_COMPROMIS:
                compromis_vivant = True
        elif k == "offre":
            a_offre = True
            if etat(m) not in MORTS_OFFRE:
                offre_vivante = True
    return (not vente) and (not a_compromis or compromis_vivant) \
        and (a_compromis or not a_offre or offre_vivante)


# ═══════════════════════════════════════════════════════════════════════════════
# ① LE RUN DE NUIT — la règle telle que la docstring de recalculer_les_chaines
#    l'énonce, et telle que le code l'applique.
# ═══════════════════════════════════════════════════════════════════════════════
def fermee_selon_le_run(membres: list[dict]) -> bool:
    """phase2/sync/affaire_ledger.py, recalculer_les_chaines :
           FERME   la VENTE            -- l'affaire a abouti
                   l'offre REFUSEE     -- l'affaire est morte
                   le compromis ANNULE -- l'affaire est morte
           Une chaine fermee ne recoit plus jamais rien.
       ⚠ « l'offre REFUSEE ferme » ne vaut QUE tant que la chaîne n'a pas de
         compromis : une chaîne offre→compromis reste ouverte même si l'offre a
         été refusée après coup. C'est ce que le front exprime par
         `(aCompromis || !aOffre || offreVivante)`."""
    vente = any(str(m.get("kind")) == "vente" for m in membres)
    compromis = [m for m in membres if str(m.get("kind")) == "compromis"]
    offres = [m for m in membres if str(m.get("kind")) == "offre"]
    if vente:
        return True
    if compromis and all(etat(m) in MORTS_COMPROMIS for m in compromis):
        return True
    if not compromis and offres and all(etat(m) in MORTS_OFFRE for m in offres):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# ② SUPABASE — app_chaine_pour : « cette chaîne peut-elle recevoir un bloc ? »
#    Ce n'est PAS le même prédicat que ① et ③ : c'est plus strict, par genre.
#    Ce qu'on vérifie ici : qu'il ne CONTREDIT jamais les deux autres, c'est-à-dire
#    qu'une chaîne FERMÉE n'est candidate pour AUCUN genre.
# ═══════════════════════════════════════════════════════════════════════════════
def candidate_selon_supabase(membres: list[dict], genre: str) -> bool:
    a_vente = any(str(m.get("kind")) == "vente" for m in membres)
    a_compromis = any(str(m.get("kind")) == "compromis" for m in membres)
    compromis_vivant = any(str(m.get("kind")) == "compromis"
                           and etat(m) not in MORTS_COMPROMIS for m in membres)
    a_offre = any(str(m.get("kind")) == "offre" for m in membres)
    offre_vivante = any(str(m.get("kind")) == "offre"
                        and etat(m) not in MORTS_OFFRE for m in membres)
    offre_acceptee = any(str(m.get("kind")) == "offre" and etat(m) in ACCEPTEE for m in membres)
    if genre == "offre":
        return (not a_vente) and (not a_compromis) and (not a_offre or offre_vivante)
    if genre == "compromis":
        return (not a_vente) and (not a_compromis) and offre_acceptee \
            and (not a_offre or offre_vivante)
    if genre == "vente":
        return (not a_vente) and a_compromis and compromis_vivant
    return False


def main() -> int:
    lignes = [l for l in lire_registre() if not effacee_chez_hektor(l)]
    print(f"registre lu : {len(lignes)} lignes vivantes (effacées chez Hektor écartées)")

    chaines: dict[tuple, list[dict]] = defaultdict(list)
    for l in lignes:
        cle = (l.get("hektor_annonce_id"),
               l.get("app_chaine_id") if l.get("app_chaine_id") is not None
               else f"seule-{l.get('app_affaire_id')}")
        chaines[cle].append(l)
    print(f"chaînes            : {len(chaines)}")
    print("")

    # ── 1. ① CONTRE ③ : les deux prédicats de FERMETURE doivent coïncider ──
    divergences = []
    ouvertes = fermees = 0
    for cle, membres in chaines.items():
        front_ouvert = ouvert_selon_le_front(membres)
        run_fermee = fermee_selon_le_run(membres)
        if front_ouvert == run_fermee:          # ils devraient être opposés
            divergences.append((cle, membres, front_ouvert, run_fermee))
        if front_ouvert:
            ouvertes += 1
        else:
            fermees += 1
    print("--- ① LE RUN (Python) CONTRE ③ LE FRONT (TypeScript) ---")
    print(f"   chaînes ouvertes   {ouvertes}")
    print(f"   chaînes fermées    {fermees}")
    print(f"   DIVERGENCES        {len(divergences)}"
          + ("   <<< les deux copies ne disent pas la même chose" if divergences else "   (aucune)"))
    for cle, membres, fo, rf in divergences[:8]:
        detail = " · ".join(f"{m['kind']}={etat(m) or '—'}" for m in membres)
        print(f"      annonce {cle[0]} chaîne {cle[1]} : front_ouvert={fo} run_fermée={rf}  [{detail}]")
    print("")

    # ── 2. ② NE DOIT JAMAIS CONTREDIRE : une chaîne FERMÉE n'accueille rien ──
    contredit = []
    for cle, membres in chaines.items():
        if ouvert_selon_le_front(membres):
            continue
        for genre in ("offre", "compromis", "vente"):
            if candidate_selon_supabase(membres, genre):
                contredit.append((cle, membres, genre))
    print("--- ② SUPABASE : une chaîne FERMÉE peut-elle encore recevoir un bloc ? ---")
    print(f"   cas contradictoires {len(contredit)}"
          + ("   <<< app_chaine_pour rattacherait à une chaîne close" if contredit
             else "   (aucun : app_chaine_pour est bien plus strict, jamais plus permissif)"))
    for cle, membres, genre in contredit[:8]:
        detail = " · ".join(f"{m['kind']}={etat(m) or '—'}" for m in membres)
        print(f"      annonce {cle[0]} chaîne {cle[1]} accueillerait un(e) {genre}  [{detail}]")
    print("")

    # ── 3. LA VÉRIFICATION EMPIRIQUE : une chaîne fermée a-t-elle reçu un bloc APRÈS ? ──
    #    C'est le seul test qui ne dépende d'aucune transcription : il regarde ce
    #    qui EST dans le registre, pas ce que les formules disent.
    apres_fermeture = []
    for cle, membres in chaines.items():
        vente = next((m for m in membres if str(m.get("kind")) == "vente"), None)
        if not vente or not vente.get("date"):
            continue
        for m in membres:
            if m is vente or not m.get("date"):
                continue
            if str(m["date"])[:10] > str(vente["date"])[:10]:
                apres_fermeture.append((cle, vente, m))
    print("--- ③ EMPIRIQUE : un bloc daté APRÈS la vente qui ferme sa chaîne ---")
    print(f"   cas trouvés {len(apres_fermeture)}"
          + ("   <<< une chaîne close a reçu quelque chose" if apres_fermeture
             else "   (aucun : « une chaîne fermée ne reçoit plus jamais rien » tient)"))
    for cle, v, m in apres_fermeture[:10]:
        print(f"      annonce {cle[0]} chaîne {cle[1]} : vente du {str(v['date'])[:10]}"
              f" puis {m['kind']} du {str(m['date'])[:10]} ({etat(m) or '—'})")
    print("")

    # ── 4. CE QUE LA NOUVELLE RÈGLE BLOQUERAIT, chiffré avant de l'écrire ──
    engages = libres = revendus_libres = 0
    for annonce, groupes in _par_annonce(chaines).items():
        engage = any(ouvert_selon_le_front(m)
                     and (any(str(x.get("kind")) == "compromis" for x in m)
                          or any(str(x.get("kind")) == "offre" and etat(x) in ACCEPTEE for x in m))
                     for m in groupes)
        if engage:
            engages += 1
        else:
            libres += 1
            if any(any(str(x.get("kind")) == "vente" for x in m) for m in groupes):
                revendus_libres += 1
    print("--- ④ CE QUE LA RÈGLE PROPOSÉE FERAIT, sur le parc entier ---")
    print("   « un bien est ENGAGÉ s'il a un dossier OUVERT portant")
    print("     un compromis ou une offre acceptée » — la vente n'entre jamais en compte")
    print(f"   biens ENGAGÉS (reprise d'offre morte bloquée) : {engages}")
    print(f"   biens LIBRES  (reprise autorisée)             : {libres}")
    print(f"      dont vendus autrefois et redevenus libres  : {revendus_libres}")
    print("      ⚠ ce sont EUX que la règle ne doit pas bloquer -- scénario de Frédéric,")
    print("        « on revend la maison des années plus tard ».")
    return 0 if not divergences and not contredit and not apres_fermeture else 1


def _par_annonce(chaines: dict) -> dict:
    out: dict = defaultdict(list)
    for (annonce, _), membres in chaines.items():
        out[annonce].append(membres)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
