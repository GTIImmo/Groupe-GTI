#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPREUVE du filtre pose le 14/10/2026 sur `data.travaux_en_erreur`.

LE DEFAUT. L'ecran montre les gestes abandonnes avec deux boutons (« J'ai
refait » / « Abandonner ce geste »). Le RPC app_action_resolve ecrit une trace
dans app_pending_resolution ET RIEN D'AUTRE : le travail reste en `error` pour
toujours. Donc le bandeau se taisait, data.geste_abandonne se taisait, et le
ROUGE continuait -- or c'est le SEUL qui envoie un e-mail. Frederic recevait
donc chaque matin une alerte pour un probleme qu'il avait deja traite.

⚠ LE PIEGE QUE LA MESURE A REVELE (epreuve 5, la plus importante). Le 14/10,
  app_console_job portait 2 travaux en erreur et app_pending_resolution 2
  resolutions -- mais les deux resolutions visaient des travaux QUI N'EXISTENT
  PLUS. « 2 moins 2 = 0 » aurait donc efface une vraie alerte. On croise sur
  les IDENTIFIANTS, jamais sur les nombres.

AUCUN APPEL RESEAU : le client Supabase est imite ici.
    python monitoring/test_travaux_en_erreur_resolus.py
"""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_gti_health as cgh  # noqa: E402

SENTINELLE = [s for s in cgh.DATA_SENTINELS if s["key"] == "data.travaux_en_erreur"][0]


class FauxSupabase:
    """Imite les deux seules lectures que fait `_retirer_resolus`."""

    def __init__(self, travaux, resolus, jette=False, forme_cassee=False):
        self.travaux = travaux
        self.resolus = resolus
        self.jette = jette
        self.forme_cassee = forme_cassee

    def get(self, path, params=None):
        if self.jette:
            raise RuntimeError("Supabase injoignable")
        if self.forme_cassee:
            return {"pas": "une liste"}
        return self.resolus if path == "app_pending_resolution" else self.travaux


def _travail(ident: str, jours: int = 0) -> dict:
    """Un travail en erreur, demande il y a `jours` jours."""
    return {"id": ident, "requested_at": cgh.iso_utc(cgh.utc_now() - timedelta(days=jours))}


def _resolu(ident: str) -> dict:
    return {"payload_json": {"job_id": ident}}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    a, b, c = "job-aaa", "job-bbb", "job-ccc"

    cas = [
        ("1. 2 travaux, aucun tranche            -> ca sonne, comme avant",
         [_travail(a), _travail(b)], [], 2, 2, {"tranches_par_un_humain": 0}),
        ("2. 2 travaux, 1 tranche a l'ecran      -> il n'en reste qu'un",
         [_travail(a), _travail(b)], [_resolu(a)], 2, 1, {"tranches_par_un_humain": 1}),
        ("3. 2 travaux, les 2 tranches           -> LE CLIC ETEINT L'ALERTE",
         [_travail(a), _travail(b)], [_resolu(a), _resolu(b)], 2, 0,
         {"tranches_par_un_humain": 2}),
        ("4. 1 recent + 1 vieux de 40 jours      -> le vieux compte a part",
         [_travail(a), _travail(b, jours=40)], [], 2, 1,
         {"trop_vieux_pour_l_ecran": 1}),
        ("5. ⭐ 2 travaux, 2 resolutions QUI VISENT AILLEURS -> on NE soustrait PAS",
         [_travail(a), _travail(b)], [_resolu("disparu-1"), _resolu("disparu-2")], 2, 2,
         {"tranches_par_un_humain": 0}),
        ("6. liste de travaux tronquee           -> on ne filtre pas, on rend le brut",
         [_travail(a)], [_resolu(a)], 2, 2, {"non_filtre_cause": "liste tronquee"}),
        ("7. plus de 200 travaux                 -> on ne liste meme pas",
         [], [], 201, 201, {"non_filtre_cause": "plus de 200 travaux"}),
        ("8. Supabase injoignable                -> on rend le brut, et on le dit",
         [_travail(a)], [], 1, 1, {"non_filtre_cause": "lecture impossible (RuntimeError)"}),
        ("9. reponse de forme inconnue           -> on ne devine pas",
         [_travail(a)], [], 1, 1, {"non_filtre_cause": "reponse de forme inconnue"}),
        ("10. une resolution sans job_id         -> elle ne tranche rien",
         [_travail(a)], [{"payload_json": {}}, {"payload_json": None}], 1, 1,
         {"tranches_par_un_humain": 0}),
    ]

    rates = 0
    for i, (titre, travaux, resolus, brut, voulu, attendus) in enumerate(cas, start=1):
        moniteur = cgh.Monitor(argparse.Namespace(project_root="."), None)
        moniteur.supabase = FauxSupabase(travaux, resolus,
                                         jette=(i == 8), forme_cassee=(i == 9))
        obtenu, detail = moniteur._retirer_resolus(SENTINELLE, brut)
        ecarts = []
        if obtenu != voulu:
            ecarts.append("compte %r, attendu %r" % (obtenu, voulu))
        for cle, val in attendus.items():
            if detail.get(cle) != val:
                ecarts.append("%s = %r, attendu %r" % (cle, detail.get(cle), val))
        if ecarts:
            rates += 1
            print("  ECHEC  " + titre)
            for e in ecarts:
                print("         " + e)
        else:
            print("  ok     %s  [%d]" % (titre, obtenu))

    # --- ce que Frederic LIT dans l'e-mail -----------------------------------
    print()
    print("-- le message, quand le clic a tout eteint --")
    moniteur = cgh.Monitor(argparse.Namespace(project_root="."), None)
    moniteur.supabase = FauxSupabase([_travail(a), _travail(b, jours=40)], [_resolu(a)])
    obtenu, detail = moniteur._retirer_resolus(SENTINELLE, 2)
    statut, message, _ = moniteur._evaluate_sentinel(SENTINELLE, obtenu)
    print("   compte retenu : %d  -> statut %s" % (obtenu, statut))
    print("   tranches %d, trop vieux %d" % (detail["tranches_par_un_humain"],
                                             detail["trop_vieux_pour_l_ecran"]))
    if statut != "ok":
        print("   ECHEC : ca sonne encore alors que tout est traite")
        rates += 1
    else:
        print("   ok : ca ne sonne plus, et le detail garde les deux nombres")

    print()
    if rates:
        print("%d epreuve(s) en ECHEC." % rates)
        return 1
    print("Les %d epreuves passent : le clic eteint l'alerte, et en cas de doute "
          "on crie comme avant." % len(cas))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
