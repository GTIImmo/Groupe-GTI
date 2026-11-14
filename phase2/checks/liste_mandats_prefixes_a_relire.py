#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LES LIGNES DU CLASSEUR DONT LE BIEN EST INCERTAIN -- A RELIRE PAR FREDERIC.
                                                                   14/11/2026
POURQUOI CE DOCUMENT EXISTE
  Frederic, le 14/11 : « certains numeros de mandat sur les lignes du Sheet
  avaient un chiffre ajoute devant, car une autre ligne du registre existait
  deja avec ce numero, donc l'utilisateur ajoutait un chiffre devant ».

  ⭐ SA REGLE EST JUSTE, ET MESUREE : sur les trois formes possibles, seule
    « retirer UN chiffre DEVANT » retrouve un mandat du bien reellement
    trouve (3 fois) ; « deux chiffres devant » et « un chiffre a la fin »
    ne marchent JAMAIS (0 fois). La forme est donc etablie.

  ⛔⛔ MAIS ELLE NE SE GENERALISE PAS, et le temoin inverse dit pourquoi :
    un nombre de 4 chiffres pris AU HASARD existe deja dans notre annuaire
    de mandats dans 95 % des cas (mesure du 14/11 sur 2 000 tirages).
    « Le numero de-prefixe existe » ne prouve donc RIEN a lui seul -- il
    pourrait designer le mandat d'un AUTRE bien.
      3 chiffres : 100 % . 4 chiffres : 95 % . 5 chiffres : 8,8 %
    Seul 218611 -> 18611 est concluant par les chiffres (5 chiffres restants).

  ⛔ ET 25 DES 33 LIGNES PORTENT « NON TROUVE » dans leur colonne Ville :
    l'auteur de la ligne ne savait DEJA pas de quel bien il parlait. Aucune
    regle de calcul ne rattrape ca.

  ➡ D'OU CE DOCUMENT : la seule information qui manque est HUMAINE --
    reconnaitre le bien. 226 729 EUR de commission, et 31 lignes SEULES a
    dire qui a gagne leur dossier.

CE QU'IL FAUT REGARDER, POUR CHAQUE LIGNE
  . ce que dit LE CLASSEUR          (acheteur, vendeur, ville, prix)
  . le bien QUE NOUS AVONS RETENU   (trouve par les NOMS, faute de mandat)
  . l'autre candidat                (le bien du mandat de-prefixe)
  -> si le bien retenu est le bon, rien a faire ; sinon, le dire.

⛔ LECTURE SEULE. N'ecrit qu'un document dans notice/.

    python phase2/checks/liste_mandats_prefixes_a_relire.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "sync"))
sys.path.insert(0, str(RACINE / "phase2" / "checks"))

import rapport_gel_tous_les_champs as RAP  # noqa: E402
from rapport_gel_tous_les_champs import charger_classeur, client, lire_tout  # noqa: E402

SORTIE = RACINE / "notice" / ("A6_BIENS_INCERTAINS_A_RELIRE_%s.md" % date.today())


def noms(blob) -> str:
    """acquereur_json / mandants_json -> les noms, en clair."""
    try:
        charge = json.loads(blob) if isinstance(blob, str) else blob
    except Exception:
        return ""
    gens = charge if isinstance(charge, list) else [charge] if isinstance(charge, dict) else []
    out = []
    for g in gens:
        if not isinstance(g, dict):
            continue
        n = " ".join(str(g.get(k) or "").strip()
                     for k in ("civilite", "prenom", "nom") if g.get(k))
        n = n.strip() or str(g.get("raisonSociale") or "").strip()
        if n:
            out.append(n)
    return " / ".join(out[:3])


def nombre(v):
    """Le prix du classeur ou le montant d'une transaction -> un reel."""
    t = str(v or "").replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return float(t)
    except Exception:
        return None


def verdict_du_prix(prix_classeur, montants: set) -> tuple[str, str]:
    """⭐⭐ LE PRIX EST LE SEUL TEMOIN NON CIRCULAIRE dont je dispose.

    ⛔ Comparer les NOMS serait circulaire : le gel a justement trouve ce bien
      PAR les noms (etage 9, « sans mandat : acquereur + vendeur »). Verifier
      ce qui a servi a choisir ne prouve rien -- c'est la faute que j'ai
      commise le matin du 14/11 sur la charge, et qui a failli passer.

    ⭐ Le prix, lui, n'entre PAS dans cet etage : s'il concorde, c'est une
      confirmation INDEPENDANTE.
    ⚠ Et un ecart de quelques pour cent n'est PAS un desaccord : le classeur
      porte le prix affiche, la transaction le prix NEGOCIE. Mesure du 14/11 :
      les ecarts observes vont de -2,8 % a -7,8 %, ce qui est une negociation
      ordinaire. On distingue donc TROIS verdicts, et on ne confond pas
      « non verifiable » avec « faux ».
    """
    if prix_classeur is None or prix_classeur < 1000:
        return ("", "")
    montants = {m for m in montants if m}
    if not montants:
        return ("", "")
    for m in montants:
        if abs(prix_classeur - m) <= max(500.0, 0.01 * max(prix_classeur, m)):
            return ("CONFIRME", "le prix du classeur est **celui de la transaction**"
                                " (%.0f €)" % m)
    proche = min(montants, key=lambda m: abs(prix_classeur - m))
    ecart = 100.0 * (proche - prix_classeur) / prix_classeur
    if abs(ecart) <= 12.0:
        return ("COMPATIBLE", "prix affiché %.0f € contre %.0f € vendu (%+.1f %%)"
                              " — une négociation ordinaire" % (prix_classeur, proche, ecart))
    return ("ECART", "prix affiché %.0f € contre %.0f € vendu (%+.1f %%)"
                     " — l'écart est **gros**" % (prix_classeur, proche, ecart))


def case(ligne, idx: dict, nom: str) -> str:
    """La case du classeur, nettoyee de ses marqueurs d'absence.

    ⚠ Le classeur ecrit « nan VIVIER VASSY » quand la civilite manque : le
      lecteur du Sheet rend un NaN que la concatenation a garde. On le retire
      -- ce document est lu par un humain, et « nan » lui coute une seconde
      de doute a chaque ligne.
    """
    v = str(ligne[idx[nom]] or "").strip() if nom in idx else ""
    if v.lower() in ("nan", "none"):
        return ""
    while v.lower().startswith("nan "):
        v = v[4:].lstrip()
    return v.replace(" nan ", " ").strip()


def main() -> int:
    for f in RAP.DEFAULT_ENV_FILES:
        RAP.load_env_file(f)

    entetes, lignes = charger_classeur()
    idx = {n: i for i, n in enumerate(entetes)}
    cl = client()

    # ── les mandats, par numero ET par annonce
    mandats_par_num: dict[str, list] = defaultdict(list)
    ville_annonce: dict[str, str] = {}
    connus: set[str] = set()
    for t in ("app_mandat_register_current", "app_mandat"):
        colonnes = "numero_mandat,hektor_annonce_id"
        if t == "app_mandat_register_current":
            colonnes += ",ville"
        for r in lire_tout(cl, t, colonnes, "numero_mandat.asc"):
            num = str(r.get("numero_mandat") or "").strip()
            ann = str(r.get("hektor_annonce_id") or "").strip()
            connus.add(num)
            if num:
                mandats_par_num[num].append(r)
            if ann and r.get("ville"):
                ville_annonce[ann] = str(r["ville"])

    liens: dict[str, list] = defaultdict(list)
    for L in lire_tout(cl, "app_classeur_lien", "id_unique,app_affaire_id,confiance,etage",
                       "id_unique.asc"):
        liens[str(L["id_unique"]).strip()].append(L)

    led = {str(r["app_affaire_id"]): r for r in lire_tout(
        cl, "app_affaire_ledger",
        "app_affaire_id,app_chaine_id,hektor_annonce_id,numero_mandat,kind,state,date,"
        "montant,acquereurs_json,mandants_json", "app_affaire_id.asc")}

    repart: dict[str, list] = defaultdict(list)
    for r in lire_tout(cl, "app_affaire_repartition",
                       "app_chaine_id,cote,nom_au_moment,pourcentage,origine",
                       "app_chaine_id.asc"):
        repart[str(r["app_chaine_id"])].append(r)

    # ── les lignes a relire
    a_relire = []
    for ligne in lignes:
        m = case(ligne, idx, "Mandat")
        if not m or m in connus:
            continue
        a_relire.append((m, ligne))

    # ── le document
    out: list[str] = []
    A = out.append
    A("# LES BIENS INCERTAINS DU CLASSEUR — à relire")
    A("")
    A("> **%d lignes.** Produit le %s par `phase2/checks/liste_mandats_prefixes_a_relire.py`."
      % (len(a_relire), date.today().strftime("%d/%m/%Y")))
    A("")
    A("## Pourquoi je te demande de les relire")
    A("")
    A("Le numéro de mandat écrit sur ces lignes **n'existe pas chez nous** — c'est le")
    A("chiffre ajouté devant. Faute de mandat, notre programme a cherché le bien")
    A("**par les noms de l'acheteur et du vendeur**, ce qui est moins sûr.")
    A("")
    A("Or ces lignes disent **qui a gagné la commission**. Si le bien retenu n'est pas")
    A("le bon, c'est le mauvais négociateur qui est crédité.")
    A("")
    A("J'ai épuisé les mesures : enlever le chiffre de devant donne un numéro à")
    A("4 chiffres, et **95 % des numéros à 4 chiffres existent déjà** chez nous. Donc")
    A("« ce numéro existe » ne prouve pas que c'est le bon bien. L'information qui")
    A("manque est **humaine** : reconnaître le bien.")
    A("")
    A("## Comment répondre")
    A("")
    A("Pour chaque ligne, une seule question : **le bien retenu est-il le bon ?**")
    A("")
    A("- **oui** → il n'y a rien à faire, la commission est bien attribuée ;")
    A("- **non** → dis-moi lequel est le bon (l'autre candidat est proposé quand il existe) ;")
    A("- **je ne sais pas** → je retire la répartition de ce dossier, et personne n'est")
    A("  crédité à tort.")
    A("")
    A("Tu peux répondre en vrac, par numéro de ligne : « 3 oui, 7 non, 12 sais pas ».")
    A("")

    # ── le verdict du prix, calcule une fois pour chaque ligne
    def montants_de(iu: str) -> set:
        return {nombre(led.get(str(x["app_affaire_id"]), {}).get("montant"))
                for x in liens.get(iu, [])}

    verdicts: dict[str, tuple] = {}
    for m, ligne in a_relire:
        iu = case(ligne, idx, "ID Unique")
        verdicts[iu] = verdict_du_prix(nombre(case(ligne, idx, "Prix")), montants_de(iu))

    # ⭐⭐ ON NE FAIT RELIRE QUE CE QUI N'EST PAS DEJA TRANCHE. Lecon du 13/11 :
    #   « avant de faire trancher une pile, mesurer combien de cas se tranchent
    #   seuls » -- elle avait ramene 205 conflits a 32.
    def groupe(m, ligne):
        iu = case(ligne, idx, "ID Unique")
        etat = verdicts.get(iu, ("", ""))[0]
        if etat == "CONFIRME":
            return 1
        if etat in ("COMPATIBLE", "ECART"):
            return 2
        return 3

    a_relire.sort(key=lambda x: (groupe(*x), x[0]))

    compte = {1: 0, 2: 0, 3: 0}
    for m, ligne in a_relire:
        compte[groupe(m, ligne)] += 1
    A("## Ce que j'ai déjà pu trancher sans toi")
    A("")
    A("```")
    A("  %2d ligne(s)  CONFIRMEES par le prix -- rien a verifier" % compte[1])
    A("  %2d ligne(s)  prix comparable, a confirmer d un coup d oeil" % compte[2])
    A("  %2d ligne(s)  AUCUNE verification possible -- c est la que j ai besoin de toi"
      % compte[3])
    A("```")
    A("")
    A("Le prix est ma seule vérification **indépendante** : notre programme a")
    A("choisi le bien par les noms, donc revérifier les noms ne prouverait rien.")
    A("Le prix, lui, n'entre pas dans ce choix — s'il correspond, c'est une")
    A("confirmation qui vient d'ailleurs.")
    A("")
    titre_pose = set()
    n = 0
    for m, ligne in a_relire:
        g = groupe(m, ligne)
        if g not in titre_pose:
            titre_pose.add(g)
            A("")
            if g == 1:
                A("## ✅ Déjà confirmées par le prix — tu peux les survoler")
                A("")
                A("*Le prix du classeur est exactement celui de la transaction retenue.*")
            elif g == 2:
                A("## Prix comparable — un coup d'œil suffit")
                A("")
                A("*L'écart de prix correspond à une négociation ordinaire. Si l'acheteur")
                A("et le vendeur te parlent, c'est bon.*")
            else:
                A("## ⚠ Ici j'ai besoin de toi — aucune vérification possible")
                A("")
                A("*Ces lignes n'ont pas de prix exploitable (leur auteur a écrit")
                A("« NON TROUVÉ »), donc je n'ai aucun moyen de confirmer le bien.*")
            A("")

        n += 1
        iu = case(ligne, idx, "ID Unique")
        reste = m[1:].lstrip("0") if m.isdigit() and len(m) > 1 else ""

        ls = liens.get(iu, [])
        chaines, annonces, trs = set(), set(), []
        for x in ls:
            t = led.get(str(x["app_affaire_id"]))
            if not t:
                continue
            trs.append(t)
            if t.get("app_chaine_id"):
                chaines.add(str(t["app_chaine_id"]))
            if t.get("hektor_annonce_id"):
                annonces.add(str(t["hektor_annonce_id"]))

        A("### %d. mandat écrit **%s**%s" % (n, m, ("  →  sans le chiffre : **%s**" % reste) if reste else ""))
        A("")
        A("**Le classeur dit :**")
        A("")
        A("```")
        A("  acheteur  %s" % (case(ligne, idx, "Acquéreur") or "—"))
        A("  vendeur   %s" % (case(ligne, idx, "Vendeur") or "—"))
        A("  ville     %s" % (case(ligne, idx, "Ville") or "—"))
        A("  prix      %-14s commission  %s"
          % (case(ligne, idx, "Prix") or "—", case(ligne, idx, "Commission TTC") or "—"))
        A("  etat      %-14s offre       %s"
          % (case(ligne, idx, "Etat Actuel") or "—", case(ligne, idx, "Offre Achat") or "—"))
        A("```")
        A("")

        if trs:
            A("**Le bien que nous avons retenu** *(trouvé par les noms)* **:**")
            A("")
            A("```")
            for t in trs[:3]:
                ann = str(t.get("hektor_annonce_id") or "")
                A("  annonce %-8s mandat %-8s %s"
                  % (ann or "—", str(t.get("numero_mandat") or "—"),
                     ville_annonce.get(ann, "")))
                A("     %s %s   acheteur : %s"
                  % (str(t.get("kind") or "?"), str(t.get("date") or "")[:10],
                     noms(t.get("acquereurs_json")) or "—"))
                vend = noms(t.get("mandants_json"))
                if vend:
                    A("     vendeur : %s" % vend)
            A("```")
            A("")
        else:
            A("**Nous n'avons retenu aucun bien pour cette ligne.**")
            A("")

        # l'autre candidat : le bien du mandat de-prefixe
        autres = mandats_par_num.get(reste, []) if reste else []
        if autres:
            A("**L'autre candidat** *(le mandat %s, une fois le chiffre enlevé)* **:**" % reste)
            A("")
            A("```")
            for r in autres[:3]:
                ann = str(r.get("hektor_annonce_id") or "")
                A("  annonce %-8s %s" % (ann or "—", r.get("ville") or ville_annonce.get(ann, "")))
            A("```")
            A("")

        # qui est credite aujourd'hui
        credits = []
        for c in chaines:
            for r in repart.get(c, []):
                if str(r.get("origine")) == "classeur_reconstitue":
                    credits.append("%s %s%%" % (r.get("nom_au_moment"), r.get("pourcentage")))
        etat, phrase = verdicts.get(iu, ("", ""))
        if phrase:
            marque = {"CONFIRME": "✅ **Le prix confirme** : ",
                      "COMPATIBLE": "Prix comparable : ",
                      "ECART": "⚠ **Attention** : "}.get(etat, "")
            A("%s%s" % (marque, phrase))
            A("")
        if credits:
            A("**Crédité aujourd'hui :** %s" % " · ".join(sorted(set(credits))[:6]))
            A("")
        A("**→ le bien retenu est-il le bon ?**  ⬜ oui   ⬜ non   ⬜ je ne sais pas")
        A("")
        A("---")

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print()
    print("  %d ligne(s) a relire" % len(a_relire))
    print("  document : %s" % SORTIE)
    print()
    print("  ⛔ LECTURE SEULE : rien n'a ete ecrit en base.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
