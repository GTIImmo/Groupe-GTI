from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# GED (12/11/2026, morceau 4) -- LA GARDE RIB DU SERVEUR, deuxieme verrou.
#
# Decision de Frederic du 12/11 : « NON IL FAUT EXCLURE LES RIB ! ». Un RIB n'est JAMAIS
# envoye a l'IA. Le premier verrou est dans le navigateur (src/lib/gedClassementIa.ts) :
# il ne demande rien au serveur si le nom dit « RIB » ou si le texte du PDF porte un IBAN.
# Celui-ci revérifie ce que le navigateur a quand meme envoye : un nom « RIB » ou un IBAN
# dans le texte -> refus, AVANT tout appel. Les deux gardes suivent les MEMES regles
# (test_ged_classer.py et test_ged_classement_ia.cjs portent les memes exemples).
# ---------------------------------------------------------------------------

# Un IBAN commence par 2 lettres et 2 chiffres, puis 11 a 30 caracteres, en blocs separes ou non.
_DEBUT_IBAN = re.compile(r"\b[A-Z]{2}\d{2}")
_PHRASES_RIB = ("releve d'identite bancaire", "releve d identite bancaire")


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def iban_valide(candidat: str) -> bool:
    # La cle de controle (modulo 97) ecarte les suites qui ressemblent a un IBAN sans en etre un.
    brut = candidat.replace(" ", "").upper()
    if not 15 <= len(brut) <= 34 or not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", brut):
        return False
    tourne = brut[4:] + brut[:4]
    chiffres = "".join(str(int(c, 36)) for c in tourne)
    return int(chiffres) % 97 == 1


def texte_porte_un_rib(texte: str | None) -> bool:
    if not texte:
        return False
    plat = _sans_accents(texte).lower().replace("’", "'")
    if any(p in plat for p in _PHRASES_RIB):
        return True
    majuscules = _sans_accents(texte).upper()
    for m in _DEBUT_IBAN.finditer(majuscules):
        # On ramasse les caracteres qui suivent (espaces simples sautes), puis on essaie chaque
        # longueur possible : un IBAN suivi de « BIC … » ne doit pas etre manque.
        suite = re.match(r"(?:[ ]?[A-Z0-9]){11,40}", majuscules[m.end():])
        brut = (m.group(0) + (suite.group(0) if suite else "")).replace(" ", "")
        if any(iban_valide(brut[:n]) for n in range(15, min(len(brut), 34) + 1)):
            return True
    return False


def nom_dit_rib(nom: str | None) -> bool:
    if not nom:
        return False
    plat = re.sub(r"[^a-z0-9]+", " ", _sans_accents(nom).lower())
    return bool(re.search(r"(^| )(rib|iban)( |$)", plat)) or "identite bancaire" in plat
