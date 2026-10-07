"""SONDE -- QUE FABRIQUE HEKTOR QUAND ON LUI DONNE UN MENAGE ?      07/10/2026

C.9-couple, premier pas. Le plan le dit : « son premier pas est une MESURE »,
et « a ecrire PENDANT QUE HEKTOR VIT : c'est le seul moment ou l'on peut comparer
notre paire a la sienne ».

CE QU'ELLE REPOND, et c'est la specification de notre future fabrique :
    · combien de fiches Hektor cree pour UN menage, et avec quels identifiants
    · dans QUEL SENS le lien de couple est ecrit (qui pointe vers qui)
    · quels champs il remplit lui-meme sur la seconde fiche
    · ce que `ContactById` rend de CHACUNE des deux
    · ce que NOTRE miroir et NOTRE couche en font

⚠ LECTURE SEULE, ET C'EST STRICT. Elle n'appelle que `ContactById`, qui LIT.
  Elle ne cree rien, ne modifie rien, n'enfile aucun travail. La creation du
  menage d'essai est un geste HUMAIN, fait depuis l'app, avec l'accord de
  Frederic et sur une cible d'essai choisie par lui.

    python phase2/checks/sonde_paire_de_menage.py 603953
    python phase2/checks/sonde_paire_de_menage.py 10871 10872     # une paire connue

⚠ CE QU'ELLE NE PEUT PAS VOIR, et il faut le savoir : le bloc conjoint
  (`nom_m2`, `prenom_m2`, `adresse_m2`...) vit dans le FORMULAIRE web, pas dans
  l'API -- mesure du 11/09. Pour lui, la sonde qui existe est
  `Console/sonde_conjoint.js`, a lancer avec les memes identifiants.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
RACINE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RACINE))

from hektor_pipeline.common import HektorClient, Settings  # noqa: E402

# Les cles qui portent le menage. On les nomme pour pouvoir dire « absente »
# plutot que de les chercher dans un mur de JSON.
CLES_MENAGE = ("id", "civilite", "nom", "prenom", "refCouple", "ref_couple",
               "dateenr", "typologie")


def _plat(valeur: object, taille: int = 58) -> str:
    if valeur is None:
        return "(absente)"
    if isinstance(valeur, (dict, list)):
        return json.dumps(valeur, ensure_ascii=False)[:taille]
    texte = str(valeur)
    return repr(texte) if texte.strip() else "''"


def lire(client: HektorClient, identifiant: str) -> dict | None:
    paquet = client.get_json("/Api/Contact/ContactById/", params={"id": identifiant})
    if not isinstance(paquet, dict):
        return None
    contact = paquet.get("contact")
    return contact if isinstance(contact, dict) else paquet


def decrire(identifiant: str, contact: dict | None) -> str | None:
    """Imprime la fiche et rend son refCouple, pour chainer."""
    print("   ── FICHE %s " % identifiant + "─" * 44)
    if contact is None:
        print("      HEKTOR NE REND RIEN -- fiche inconnue ou supprimee")
        return None
    for cle in CLES_MENAGE:
        if cle in contact:
            print("      %-12s %s" % (cle, _plat(contact.get(cle))))
    autres = [k for k in contact if k not in CLES_MENAGE]
    print("      %-12s %d : %s" % ("autres cles", len(autres), ", ".join(sorted(autres))[:92]))
    muette = not str(contact.get("nom") or "").strip() and not str(contact.get("prenom") or "").strip()
    print("      %-12s %s" % ("verdict", "MUETTE (aucun nom, aucun prenom)" if muette
                              else "NOMMEE"))
    ref = contact.get("refCouple") or contact.get("ref_couple")
    return str(ref).strip() if ref not in (None, "") else None


def ce_que_nous_en_faisons(identifiants: list[str]) -> None:
    """Notre miroir et notre couche, sur les memes fiches. Lecture seule."""
    import sqlite3
    print()
    print("   ── CE QUE NOUS EN FAISONS " + "─" * 34)
    mir = sqlite3.connect("file:%s?mode=ro" % (RACINE / "data" / "hektor.sqlite").as_posix(),
                          uri=True, timeout=30)
    loc = sqlite3.connect("file:%s?mode=ro" % (RACINE / "phase2" / "phase2.sqlite").as_posix(),
                          uri=True, timeout=30)
    try:
        for ident in identifiants:
            r = mir.execute(
                "SELECT nom, prenom, civilite, hektor_couple_contact_id"
                " FROM hektor_contact WHERE CAST(hektor_contact_id AS TEXT)=?", (ident,)).fetchone()
            print("      miroir  %-9s %s" % (ident,
                  "absente -- la descente ne l'a pas encore vue" if r is None else
                  "nom=%s prenom=%s civilite=%s lien_couple=%s"
                  % (_plat(r[0], 24), _plat(r[1], 24), _plat(r[2], 16), _plat(r[3], 12))))
            # ⚠ `app_couple_contact_id` N'EXISTE PAS EN LOCAL, et c'est VOULU : le
            #   patch du 21/09 l'a posee cote Postgres pour ne pas changer les
            #   200 000 empreintes du push (ce qui avait sature Supabase le 22/08).
            #   Elle se lit donc dans Supabase, pas ici.
            c = loc.execute(
                "SELECT display_name, couple_role, hektor_contact_id"
                " FROM app_contact_current WHERE CAST(hektor_target_id AS TEXT)=?", (ident,)).fetchone()
            if c is None:
                print("      couche  %-9s absente -- pas encore dans app_contact_current" % ident)
            else:
                print("      couche  %-9s display=%s role=%s notre_numero=%s"
                      % (ident, _plat(c[0], 30), c[1] or "(aucun)", c[2]))
    finally:
        mir.close()
        loc.close()


def main() -> int:
    identifiants = [a.strip() for a in sys.argv[1:] if a.strip().isdigit()]
    if not identifiants:
        print(__doc__)
        print("⛔ donner au moins un identifiant de contact Hektor")
        return 2

    print("SONDE -- la paire de menage, telle que HEKTOR la fabrique")
    print("   (lecture seule : seul ContactById est appele, il LIT)")
    print()
    client = HektorClient(Settings.from_env())

    vus: dict[str, str | None] = {}
    a_lire = list(identifiants)
    while a_lire:
        ident = a_lire.pop(0)
        if ident in vus:
            continue
        vus[ident] = decrire(ident, lire(client, ident))
        # ⭐ ON SUIT LE LIEN : si la fiche designe une autre fiche, on la lit aussi.
        #   C'est ainsi qu'on voit la PAIRE sans l'avoir devinee.
        ref = vus[ident]
        if ref and ref not in vus and ref not in a_lire:
            print("      ➡ elle designe la fiche %s : je la lis aussi" % ref)
            a_lire.append(ref)
        print()

    print("   ── LA PAIRE, TELLE QU'ELLE SE LIT " + "─" * 26)
    for ident, ref in vus.items():
        if ref is None:
            print("      %s ne designe personne" % ident)
        elif ref == ident:
            print("      %s se designe ELLE-MEME -> c'est la PORTEUSE du menage" % ident)
        else:
            print("      %s designe %s" % (ident, ref))
    print("      ⚠ la regle du projet : la porteuse est celle dont id == refCouple")

    ce_que_nous_en_faisons(list(vus))
    print()
    print("   ⚠ LE LIEN EN NUMERO D'APP (`app_couple_contact_id`) VIT DANS SUPABASE,")
    print("     pas en local -- decision du 21/09, pour ne pas changer les 200 000")
    print("     empreintes du push. Le lire la-bas si besoin.")
    print()
    print("   ⚠ LE BLOC CONJOINT N'EST PAS DANS L'API. Pour le voir :")
    print("        node Console/sonde_conjoint.js      (lecture seule aussi)")
    print("      en ayant mis ces identifiants dans sa liste FICHES.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
