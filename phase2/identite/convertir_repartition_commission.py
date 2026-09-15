#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CE QUE HEKTOR PORTE DEVIENT LA REPARTITION DE L'APP.          14/09/2026

Chantier C.19-d, tache 3.2e, lot 5 -- la derniere piece du rattrapage.

CE QU'IL FAIT, ET RIEN D'AUTRE
------------------------------
Il lit `app_affaire_console.intervenants_json` -- ce que la console a releve chez
Hektor -- et en fabrique des lignes de `app_affaire_repartition`, la table de
l'app. Il n'appelle JAMAIS Hektor : tout est deja en base.

⚠ IL N'ECRASE JAMAIS UNE SAISIE HUMAINE. Si un dossier porte deja une ligne
  d'origine `saisie`, on ne touche a rien et on le compte a part. C'est la regle
  du projet partout ailleurs -- ici elle touche a de l'argent, donc elle n'a pas
  d'exception.

⚠ LA REPARTITION APPARTIENT AU DOSSIER, PAS A LA TRANSACTION. Un dossier porte
  souvent un compromis ET sa vente, et les deux disent la meme chose : mesure du
  14/09, 16 biens sur 16. Quand ils different, on prend LA VENTE -- elle est la
  plus avancee, et c'est elle qui paie.

LE CALCUL, ET IL NE DEVINE RIEN
-------------------------------
Hektor coupe la commission en deux moities (`unites_entree_percent` /
`unites_sortie_percent`, 50/50 partout ou il les rend), puis donne a chaque
personne sa part DE SA MOITIE (`percent`, 100 quand elle est seule).
Notre table, elle, stocke la part DU TOTAL -- decision de Frederic : « sur les
deux lignes entree donc 25 % + 25 % », quatre lignes a 25 font 100.

    part du total = (unites du cote / 100) x (part de la personne / 100) x 100

⚠ ET QUAND LE PARTAGE MANQUE. Mesure du 14/09 sur la vente 8004 (2022) : deux
  intervenants nommes, leurs montants presents, et AUCUN pourcentage de partage.
  On retombe alors sur 50/50 -- la valeur que Hektor rend PARTOUT ailleurs -- mais
  on ne le cache pas : ces lignes portent `origine = 'hektor_partage_suppose'`,
  pour qu'une relecture sache qu'une hypothese a ete faite. Une supposition tue
  est un mensonge ; une supposition nommee est une donnee.

⚠ PLUS DE DEUX PERSONNES D'UN COTE : ON NE CONVERTIT PAS. Notre table n'a que
  deux emplacements par cote. Garder les deux premieres, ce serait effacer de
  l'argent en silence. On compte ces dossiers et on les nomme.

IDEMPOTENT : rejouer ne change rien, la cle est (dossier, cote, rang).
RETOUR ARRIERE : supprimer les lignes d'origine `hektor%` -- elles sont
reconnaissables, et aucune saisie humaine n'en porte l'etiquette.

    python phase2/identite/convertir_repartition_commission.py --dry-run
    python phase2/identite/convertir_repartition_commission.py --appliquer
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))

from push_contacts_to_supabase import (  # noqa: E402
    DEFAULT_ENV_FILES,
    SupabaseRestClient,
    load_env_file,
)

CONSOLE = "app_affaire_console"
LEDGER = "app_affaire_ledger"
CIBLE = "app_affaire_repartition"
# Le plus avance gagne quand deux transactions d'un meme dossier se contredisent.
RANG_GENRE = {"offre": 0, "compromis": 1, "vente": 2}


def client() -> SupabaseRestClient | None:
    for f in DEFAULT_ENV_FILES:
        load_env_file(f)
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not cle:
        print("REFUS : SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.")
        return None
    return SupabaseRestClient(base_url=url, service_role_key=cle)


def lire_tout(cl: SupabaseRestClient, table: str, champs: str, cle: str,
              unique: bool = True) -> list[dict]:
    """⚠ PostgREST plafonne TOUTE reponse a 1 000 lignes, silencieusement. Sans
    pagination on conclurait sur un bout en croyant avoir tout lu.

    ⚠ ET LA CLE DE PARCOURS DOIT ETRE UNIQUE PAR LIGNE. « Les lignes apres la
      derniere valeur lue » ne saute rien tant qu'aucune valeur ne se repete.
      Sur `app_affaire_repartition` la cle primaire est COMPOSITE
      (app_chaine_id, cote, rang) : avancer sur `app_chaine_id` seul saute les
      lignes restantes de la chaine coupee au bord d'une page.
      MESURE DU 15/09 : 4 lignes sur 13 309 invisibles.

    ⚠ ET CE N'ETAIT PAS QU'UN FAUX COMPTE. Cette lecture sert a construire
      l'ensemble des dossiers QU'ON NE DOIT PAS TOUCHER. Une ligne humaine tombee
      au bord d'une page serait sortie de la protection, donc ECRASEE. Les deux
      saisies du 14/09 etaient visibles -- par chance, pas par construction.

    `unique=False` bascule sur un parcours PAR RANG avec un ordre TOTAL : plus
    aucune ligne ne peut etre a egalite, donc « les 1 000 suivantes » ne peut
    plus rien omettre. Meme remede que `pull_from_supabase.page_par_rang`.
    """
    out: list[dict] = []
    if not unique:
        ordre = ",".join(c.strip() + ".asc" for c in champs.split(",") if c.strip())
        while True:
            page = cl.request(method="GET", path=(
                f"{table}?select={champs}&order={ordre}&limit=1000&offset={len(out)}"))
            if not isinstance(page, list) or not page:
                break
            out.extend(page)
            if len(page) < 1000:
                break
        return out
    curseur = -1
    while True:
        page = cl.request(method="GET", path=(
            f"{table}?select={champs}&{cle}=gt.{curseur}&order={cle}.asc&limit=1000"))
        if not isinstance(page, list) or not page:
            break
        out.extend(page)
        suivant = int(page[-1][cle])
        if suivant == curseur:
            raise RuntimeError(
                f"{table} : la cle « {cle} » ne progresse plus -- elle se repete. "
                "Passer unique=False.")
        curseur = suivant
    return out


def nombre(v) -> Decimal | None:
    t = str(v if v is not None else "").strip().replace(",", ".")
    if not t:
        return None
    try:
        return Decimal(t)
    except Exception:
        return None


def deux_decimales(v: Decimal) -> str:
    return str(v.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def main() -> int:
    ap = argparse.ArgumentParser()
    # `--dry-run` existe pour la main qui le tape par reflexe : c'est deja le
    # defaut, mais un outil qui refuse un argument inoffensif fait perdre du temps.
    ap.add_argument("--dry-run", action="store_true", help="Le defaut. Ne rien ecrire.")
    ap.add_argument("--appliquer", action="store_true",
                    help="Ecrire pour de bon. Sans lui, on montre et on ne touche a rien.")
    ap.add_argument("--limite", type=int, default=0,
                    help="S'arreter apres N dossiers -- pour un premier essai.")
    args = ap.parse_args()

    cl = client()
    if cl is None:
        return 1

    # ── 1. CE QUE LA CONSOLE A RELEVE ──
    lu = lire_tout(cl, CONSOLE, "app_affaire_id,kind,hektor_affaire_id,intervenants_json,"
                                "unites_entree_percent,unites_sortie_percent", "app_affaire_id")
    avec = [x for x in lu if x.get("intervenants_json")]
    print("lignes relevees par la console    %6d" % len(lu))
    print("   dont avec des intervenants     %6d" % len(avec))

    # ── 2. LE DOSSIER DE CHAQUE TRANSACTION ──
    ledger = lire_tout(cl, LEDGER, "app_affaire_id,app_chaine_id,app_dossier_id,kind,"
                                   "hektor_affaire_id,present_in_hektor", "app_affaire_id")
    par_affaire = {int(x["app_affaire_id"]): x for x in ledger}

    # ── 3. UN DOSSIER, UNE SOURCE : LA PLUS AVANCEE ──
    meilleure: dict[int, dict] = {}
    sans_dossier = 0
    efface = 0
    for x in avec:
        info = par_affaire.get(int(x["app_affaire_id"]))
        if not info or info.get("app_chaine_id") is None:
            sans_dossier += 1
            continue
        # ⚠ CE QUE HEKTOR N'A PLUS NE PRODUIT PAS DE REPARTITION. Une transaction
        #   supprimee garde son releve chez nous -- le registre est delete-never --
        #   mais en tirer une commission serait crediter quelqu'un pour une vente
        #   qui n'existe plus. Meme regle que partout ailleurs (`effaceeChezHektor`),
        #   et c'est la QUATRIEME fois qu'elle doit etre posee quelque part.
        if (str(info.get("hektor_affaire_id") or "").strip()
                and info.get("present_in_hektor") is False):
            efface += 1
            continue
        chaine = int(info["app_chaine_id"])
        rang = RANG_GENRE.get(str(x.get("kind") or ""), -1)
        courant = meilleure.get(chaine)
        if courant is None or rang > courant["_rang"]:
            meilleure[chaine] = {**x, "_rang": rang,
                                 "_dossier": info.get("app_dossier_id")}
    print("   dossiers a convertir           %6d" % len(meilleure))
    if sans_dossier:
        print("   sans dossier rattachable       %6d   (ignores)" % sans_dossier)
    if efface:
        print("   effacees chez Hektor           %6d   (ignorees)" % efface)

    # ── 4. CE QUI EST DEJA LA, ET QU'ON NE TOUCHE PAS ──
    # ⚠ `unique=False` : la cle primaire est composite, voir lire_tout.
    deja = lire_tout(cl, CIBLE, "app_chaine_id,cote,rang,origine", "app_chaine_id",
                     unique=False)
    # ⚠ ON PROTEGE TOUT CE QUI VIENT DE L'APP, PAS SEULEMENT « saisie ».
    #   La modale inscrit `origine = 'defaut'` quand quelqu'un ACCEPTE les noms
    #   proposes (App.tsx:15398/15404), et `api.ts:5323` renvoie cette origine
    #   telle quelle. Une repartition VALIDEE par un humain porte donc `defaut`.
    #   Ne proteger que `saisie`, c'etait effacer ces validations-la.
    #   ➡ Regle : tout ce qui ne vient pas de Hektor appartient a l'app.
    #     'hektor', 'hektor_partage_suppose'  -> a nous de les rafraichir
    #     'saisie', 'defaut', ou tout futur    -> on n'y touche pas
    humains = {int(r["app_chaine_id"]) for r in deja
               if not str(r.get("origine") or "").startswith("hektor")}
    print("   dossiers poses par l'APP       %6d   (jamais ecrases)" % len(humains))

    # ── 5. LA CONVERSION ──
    a_ecrire: list[dict] = []
    compte = defaultdict(int)
    exemples: list[str] = []
    plafonnes: list[str] = []
    for chaine, src in sorted(meilleure.items()):
        if chaine in humains:
            compte["pose par l'app -- respecte"] += 1
            continue
        gens = src.get("intervenants_json") or []
        if isinstance(gens, str):
            try:
                gens = json.loads(gens)
            except Exception:
                gens = []
        par_cote: dict[str, list[dict]] = defaultdict(list)
        for g in gens:
            sens = str((g or {}).get("sens") or "").strip().lower()
            if sens in ("entree", "sortie") and str((g or {}).get("id") or "").strip():
                par_cote[sens].append(g)
        if not par_cote:
            compte["releve vide"] += 1
            continue
        if any(len(v) > 2 for v in par_cote.values()):
            # ⚠ ON NE GARDE PAS « LES DEUX PREMIERES » : ce serait effacer de
            #   l'argent en silence. On nomme le dossier et on passe.
            compte["plus de deux personnes d'un cote -- NON CONVERTI"] += 1
            if len(exemples) < 5:
                exemples.append(f"dossier {chaine} : "
                                + " · ".join(f"{k}={len(v)}" for k, v in par_cote.items()))
            continue

        suppose = False
        lignes_dossier: list[dict] = []
        for cote, gens_du_cote in par_cote.items():
            unites = nombre(src.get(f"unites_{cote}_percent"))
            if unites is None:
                unites = Decimal("50")
                suppose = True
            for rang, g in enumerate(sorted(gens_du_cote, key=lambda z: str(z.get("id"))), 1):
                part = nombre(g.get("percent"))
                if part is None:
                    part = Decimal("100")
                    suppose = True
                # ── LE PLAFOND, ET POURQUOI IL EXISTE ──          15/09/2026
                # Mesure du jour : 1 ligne sur 13 313 depasse 100, de 5 dix
                # millemes. Elle vient de HEKTOR, qui ecrit `percent = 200.001`
                # la ou il veut dire 200 -- sa facon d'exprimer « cette personne
                # prend tout, y compris la part de l'autre cote » (vente 23208,
                # Marion BILLIG DURAND, montant sortie a 0). 50 x 200,001 / 100
                # fait 100,0005, et la contrainte de la table refuse.
                # ⚠ ON PLAFONNE, MAIS ON NE SE TAIT PAS. Un plafonnement muet
                #   masquerait le jour ou un vrai 150 % arriverait. Le compteur
                #   `plafonnee a 100` et la liste nommee sont la pour ca.
                valeur = unites * part / Decimal("100")
                if valeur > Decimal("100"):
                    compte["plafonnee a 100 (arrondi de Hektor)"] += 1
                    if len(plafonnes) < 5:
                        plafonnes.append("dossier %s : %s %s = %s %%"
                                         % (chaine, cote, (g.get("nom") or "?"), valeur))
                    valeur = Decimal("100")
                elif valeur < 0:
                    compte["negative -- NON CONVERTIE"] += 1
                    continue
                lignes_dossier.append({
                    "app_chaine_id": chaine,
                    "app_dossier_id": src.get("_dossier"),
                    "cote": cote,
                    "rang": rang,
                    "hektor_user_id": str(g.get("id")).strip(),
                    "nom_au_moment": (str(g.get("nom") or "").strip() or None),
                    "pourcentage": deux_decimales(valeur),
                })
        etiquette = "hektor_partage_suppose" if suppose else "hektor"
        for l in lignes_dossier:
            l["origine"] = etiquette
        a_ecrire.extend(lignes_dossier)
        compte[etiquette] += 1
        if args.limite and compte["hektor"] + compte["hektor_partage_suppose"] >= args.limite:
            break

    print("")
    print("-- CE QUI SERAIT ECRIT --")
    for k, v in sorted(compte.items(), key=lambda x: -x[1]):
        print("   %-42s %6d" % (k, v))
    print("   %-42s %6d" % ("LIGNES au total", len(a_ecrire)))
    if plafonnes:
        print("")
        print("-- LES LIGNES PLAFONNEES A 100, NOMMEES --")
        for e in plafonnes:
            print("   " + e)
    if exemples:
        print("")
        print("-- LES DOSSIERS NON CONVERTIS, NOMMES --")
        for e in exemples:
            print("   " + e)
    if a_ecrire:
        print("")
        print("-- UN APERCU --")
        for l in a_ecrire[:6]:
            print("   dossier %-9s %-7s rang %s  user %-5s %-24s %s %%  (%s)" % (
                l["app_chaine_id"], l["cote"], l["rang"], l["hektor_user_id"],
                (l["nom_au_moment"] or "")[:24], l["pourcentage"], l["origine"]))

    if not args.appliquer:
        print("")
        print("--dry-run (defaut) : RIEN n'a ete ecrit. Ajouter --appliquer.")
        return 0

    # ── 6. L'ECRITURE, par paquets ──
    # ⚠ La cle est (dossier, cote, rang) : rejouer ecrase la ligne precedente de
    #   MEME rang, et n'en cree jamais une seconde.
    ecrites = 0
    for i in range(0, len(a_ecrire), 200):
        paquet = a_ecrire[i:i + 200]
        cl.request(method="POST", path=CIBLE, payload=paquet,
                   prefer="resolution=merge-duplicates,return=minimal")
        ecrites += len(paquet)
    reste = lire_tout(cl, CIBLE, "app_chaine_id,cote,rang,origine", "app_chaine_id")
    print("")
    print("lignes ecrites                    %6d" % ecrites)
    print("table apres                       %6d lignes" % len(reste))
    print("   dont saisies humaines          %6d" % sum(
        1 for r in reste if str(r.get("origine") or "") == "saisie"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
