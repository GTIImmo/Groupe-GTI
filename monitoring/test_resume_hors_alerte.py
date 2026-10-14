#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPREUVE : le RESUME ne declenche plus d'e-mail (14/10/2026).

LE DEFAUT. `monitor.summary` dit « N critical, M warning » : c'est le compte rendu
du passage, pas un incident. Mais il porte le statut `critical` des qu'un autre
l'est, donc il entrait dans `newly_critical` et DOUBLAIT l'e-mail. Mesure sur un
mois (318 passages) : 33 bascules vers le rouge, dont SEPT etaient le resume --
21 % des e-mails pour une ligne qui ne dit rien de neuf.

CE QU'IL FAUT PROUVER, et c'est le plus important : qu'on n'a PAS perdu d'alerte.
Les trois usages de `criticals` sont eprouves : l'envoi normal, l'envoi sans
deduplication (etat precedent illisible), et le message de RETABLISSEMENT.

AUCUN E-MAIL N'EST ENVOYE : l'expediteur est imite ici.
    python monitoring/test_resume_hors_alerte.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_gti_health as cgh  # noqa: E402

RESUME = "monitor.summary"


class FauxAlerter:
    """Note ce qui aurait ete envoye, sans rien envoyer."""

    def __init__(self):
        self.envois = []

    def dispatch(self, resultats, kind="critical", dry_run=False):
        self.envois.append((kind, [r.status_key for r in resultats]))


def _res(cle: str, statut: str) -> cgh.CheckResult:
    return cgh.CheckResult(
        status_key=cle, domain="system", component="x", check_name="y",
        status=statut, severity=statut, message=cle, details={},
    )


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    cas = [
        # titre, resultats du passage, etat precedent, etat lu ?, envois attendus
        ("1. un VRAI nouveau rouge + le resume -> l'e-mail part, SANS le resume",
         [_res("data.travaux_en_erreur", "critical"), _res(RESUME, "critical")],
         {"data.travaux_en_erreur": "ok", RESUME: "ok"}, True,
         [("critical", ["data.travaux_en_erreur"])]),

        ("2. le resume SEUL bascule -> plus d'e-mail (c'etait les 21 %)",
         [_res(RESUME, "critical")],
         {RESUME: "ok"}, True,
         []),

        ("3. un rouge DEJA rouge -> pas d'e-mail (deduplication inchangee)",
         [_res("data.travaux_en_erreur", "critical"), _res(RESUME, "critical")],
         {"data.travaux_en_erreur": "critical", RESUME: "critical"}, True,
         []),

        ("4. RETABLISSEMENT : il y avait du rouge, tout est vert -> le message part",
         [_res("data.travaux_en_erreur", "ok"), _res(RESUME, "ok")],
         {"data.travaux_en_erreur": "critical", RESUME: "critical"}, True,
         [("recovery", [])]),

        ("5. etat precedent ILLISIBLE + vrai rouge -> envoi sans dedup, sans le resume",
         [_res("data.mandat_disparu", "critical"), _res(RESUME, "critical")],
         {}, False,
         [("critical", ["data.mandat_disparu"])]),

        ("6. etat precedent ILLISIBLE + le resume seul -> rien (pas de faux cri)",
         [_res(RESUME, "critical")],
         {}, False,
         []),

        ("7. DEUX vrais rouges + le resume -> les deux partent, pas trois",
         [_res("data.a", "critical"), _res("data.b", "critical"), _res(RESUME, "critical")],
         {"data.a": "ok", "data.b": "ok", RESUME: "warning"}, True,
         [("critical", ["data.a", "data.b"])]),

        ("8. que des orange -> aucun e-mail (seuls les rouges envoient)",
         [_res("data.notif_non_lues", "warning"), _res(RESUME, "warning")],
         {"data.notif_non_lues": "ok", RESUME: "ok"}, True,
         []),
    ]

    rates = 0
    for titre, resultats, precedent, lu, attendu in cas:
        faux = FauxAlerter()
        cgh.dispatch_alerts(faux, resultats, precedent, lu)
        if faux.envois != attendu:
            rates += 1
            print("  ECHEC  " + titre)
            print("         envoye  : %r" % (faux.envois,))
            print("         attendu : %r" % (attendu,))
        else:
            quoi = "rien" if not faux.envois else ", ".join(
                "%s(%s)" % (k, "+".join(v) or "-") for k, v in faux.envois)
            print("  ok     %-72s  -> %s" % (titre, quoi))

    print()
    if rates:
        print("%d epreuve(s) sur %d en ECHEC." % (rates, len(cas)))
        return 1
    print("Les %d epreuves passent : le resume ne double plus l'e-mail, et AUCUNE "
          "vraie alerte n'est perdue (envoi, envoi sans dedup, retablissement)." % len(cas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
