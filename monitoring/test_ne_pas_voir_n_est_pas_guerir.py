#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPREUVE de la REGLE 5 (27/11/2026) : ne pas voir n'est pas guerir.

LE DEFAUT. Quand la lecture des taches planifiees depasse ses 15 s, la sonde n'emet que
`scheduledtasks` en « unknown ». La reconciliation de write_results prenait alors chaque
tache en anomalie pour guerie (« Retour a la normale »), envoyait un retablissement, et la
passe suivante re-criait le meme incident comme neuf. Mesure au serveur : 20 lectures
ratees depuis le 07/09, 24 faux retours ; le 26/11, la descente en code 1 a fait TROIS
alertes et DEUX faux retablissements pour une seule cause.

ON JOUE LES VRAIES FONCTIONS : check_scheduled_tasks (PowerShell imite : sa reponse, ou
son depassement de 15 s), check_worker_heartbeat, write_results et dispatch_alerts. Seuls
Supabase et l'expediteur sont imites. AUCUN e-mail, AUCUNE ecriture, AUCUN PowerShell.

LE TEMOIN INVERSE : la meme histoire, interrupteur eteint, doit reproduire A L'IDENTIQUE
les six evenements que le serveur garde pour `scheduledtasks:gti_descente` (26-27/11).

    python -X utf8 -u monitoring/test_ne_pas_voir_n_est_pas_guerir.py
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_gti_health as cgh  # noqa: E402

TACHES = "GTI Descente,GTI Recrutement,GTI Menage Temporaires,GTI Sauvegarde"
D, R, M, S = ("scheduledtasks:gti_descente", "scheduledtasks:gti_recrutement",
              "scheduledtasks:gti_menage_temporaires", "scheduledtasks:gti_sauvegarde")
VUE_T, VUE_W, W1 = "scheduledtasks", "workers.heartbeat", "workers.heartbeat:worker_un"

rates = 0
faits = 0


def verifier(titre: str, obtenu, attendu) -> None:
    global rates, faits
    faits += 1
    if obtenu == attendu:
        print("  ok     " + titre)
    else:
        rates += 1
        print("  ECHEC  " + titre)
        print("         obtenu  : %r" % (obtenu,))
        print("         attendu : %r" % (attendu,))


class FauxSupabase:
    """app_monitor_status en memoire ; app_worker_registry lisible ou non."""

    def __init__(self, statuts: dict[str, str] | None = None, etat_lisible: bool = True):
        self.lignes = {k: {"status_key": k, "status": v, "message": "(d'avant)"}
                       for k, v in (statuts or {}).items()}
        self.evenements: list[dict] = []
        self.etat_lisible = etat_lisible
        self.workers: list[dict] | None = []   # None = illisible

    def get(self, table, params=None):
        if table == "app_monitor_status":
            if not self.etat_lisible:
                raise RuntimeError("Supabase injoignable (imite)")
            return [{"status_key": l["status_key"], "status": l["status"]} for l in self.lignes.values()]
        if table == "app_worker_registry":
            if self.workers is None:
                raise RuntimeError("HTTP 503 (imite)")
            return self.workers
        raise AssertionError("table inattendue : " + table)

    def upsert_status(self, rows):
        for row in rows:
            self.lignes[row["status_key"]] = dict(row)

    def insert_events(self, rows):
        self.evenements.extend(rows)

    def purge_stale_status(self, cutoff):
        pass

    def statut(self, cle):
        ligne = self.lignes.get(cle)
        return None if ligne is None else ligne["status"]


class FauxAlerter:
    def __init__(self):
        self.envois: list[tuple[str, list[str]]] = []

    def dispatch(self, resultats, kind="critical", dry_run=False):
        self.envois.append((kind, sorted(r.status_key for r in resultats)))


class FauxProcessus:
    def __init__(self, sortie: str):
        self.stdout = sortie
        self.returncode = 0


def imiter_powershell(taches: dict[str, int] | None):
    """None = PowerShell depasse ses 15 s (la panne mesuree 20 fois)."""
    def run(cmd, **kw):
        if taches is None:
            raise subprocess.TimeoutExpired(cmd, kw.get("timeout", 15))
        rows = [{"Name": n, "State": "Running" if r == 267009 else "Ready", "LastResult": r, "AgeMin": 60}
                for n, r in taches.items()]
        return FauxProcessus(json.dumps(rows))
    return run


@contextlib.contextmanager
def interrupteurs(regle5: bool, en_cours: bool):
    avant = (cgh.NE_PAS_VOIR_N_EST_PAS_GUERIR, cgh.GARDER_LES_TACHES_EN_COURS)
    cgh.NE_PAS_VOIR_N_EST_PAS_GUERIR, cgh.GARDER_LES_TACHES_EN_COURS = regle5, en_cours
    try:
        yield
    finally:
        cgh.NE_PAS_VOIR_N_EST_PAS_GUERIR, cgh.GARDER_LES_TACHES_EN_COURS = avant


def sonde(sb: FauxSupabase, taches, avec_battement: bool = False, en_cours: bool = True) -> list:
    """Une vraie passe des deux sondes concernees, PowerShell imite."""
    args = argparse.Namespace(scheduled_tasks=TACHES, timeout_seconds=15, project_root=".",
                              worker_stale_default_minutes=180)
    mon = cgh.Monitor(args, sb)
    vrai_run = cgh.subprocess.run
    cgh.subprocess.run = imiter_powershell(taches)
    try:
        with interrupteurs(cgh.NE_PAS_VOIR_N_EST_PAS_GUERIR, en_cours):
            if avec_battement:
                mon.safe_check("worker_heartbeat", mon.check_worker_heartbeat)
            mon.safe_check("scheduled_tasks", mon.check_scheduled_tasks)
    finally:
        cgh.subprocess.run = vrai_run
    return mon.results


def ecrire(sb: FauxSupabase, resultats: list, regle: bool, en_cours: bool | None = None):
    """write_results reel ; rend (envois, sortie d'erreur). `regle` = regle 5 ;
    `en_cours` = la regle des taches en cours (par defaut : comme la regle 5)."""
    alerte = FauxAlerter()
    tampon = io.StringIO()
    with interrupteurs(regle, regle if en_cours is None else en_cours):
        with contextlib.redirect_stderr(tampon):
            cgh.write_results(sb, resultats, False, 24.0, alerte)
    return alerte.envois, tampon.getvalue()


def retours(resultats) -> list[str]:
    return sorted(r.status_key for r in resultats if r.message.startswith("Retour a la normale"))


TOUT_VA = {"GTI Descente": 0, "GTI Recrutement": 0, "GTI Menage Temporaires": 0, "GTI Sauvegarde": 0}
DESCENTE_EN_1 = dict(TOUT_VA, **{"GTI Descente": 1})


def cas_unitaires() -> None:
    print("Les cas, un par un (regle ALLUMEE sauf mention) :")

    # 5a -- la guerison VUE reste annoncee : on n'a rien casse.
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    res = sonde(sb, TOUT_VA)
    envois, err = ecrire(sb, res, True)
    verifier("5a  taches LUES et descente remise : « Retour a la normale » et retablissement",
             (retours(res), envois, sb.statut(D)), ([D], [("recovery", [])], "ok"))

    # 5b -- la panne mesuree : PowerShell depasse 15 s.
    sb = FauxSupabase({D: "critical", R: "warning", VUE_T: "critical"})
    res = sonde(sb, None)
    envois, err = ecrire(sb, res, True)
    verifier("5b  lecture ratee (15 s) : aucun « Retour », aucun envoi, etats gardes",
             (retours(res), envois, sb.statut(D), sb.statut(R), sb.lignes[D]["message"], sb.statut(VUE_T)),
             ([], [], "critical", "warning", "(d'avant)", "unknown"))
    verifier("5b' le journal dit PAR QUOI (message du mecanisme)",
             ("[regle 5]" in err and "scheduledtasks:gti_descente=critical" in err
              and "scheduledtasks:gti_recrutement=warning" in err), True)

    # 5b-inverse : interrupteur eteint, la panne d'avant revient.
    sb = FauxSupabase({D: "critical", R: "warning", VUE_T: "critical"})
    res = sonde(sb, None)
    envois, err = ecrire(sb, res, False)
    verifier("5b-INVERSE  eteinte : faux « Retour » pour les deux et faux retablissement",
             (retours(res), envois, sb.statut(D), "[regle 5]" in err),
             ([D, R], [("recovery", [])], "ok", False))

    # 5c -- apres la passe aveugle, la descente toujours en 1 : PAS de nouvel e-mail.
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    ecrire(sb, sonde(sb, None), True)
    res = sonde(sb, DESCENTE_EN_1)
    envois, err = ecrire(sb, res, True)
    verifier("5c  aveugle puis relue en 1 : la vue d'ensemble seule ne re-crie pas",
             (envois, sb.statut(D), sb.statut(VUE_T)), ([], "critical", "critical"))
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    ecrire(sb, sonde(sb, None), False)
    res = sonde(sb, DESCENTE_EN_1)
    envois, err = ecrire(sb, res, False)
    verifier("5c-INVERSE  eteinte : le meme incident repart comme neuf",
             envois, [("critical", [VUE_T, D])])

    # 5d -- un VRAI nouveau rouge apres une passe aveugle part, comme avant.
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    ecrire(sb, sonde(sb, None), True)
    res = sonde(sb, dict(DESCENTE_EN_1, **{"GTI Sauvegarde": 1}))
    envois, err = ecrire(sb, res, True)
    verifier("5d  vrai nouveau rouge (sauvegarde) apres aveuglement : l'e-mail part, vue comprise",
             envois, [("critical", [VUE_T, S])])

    # 5e -- la sonde PLANTE (valeur illisible) : pas de vue d'ensemble du tout.
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    res = sonde(sb, {"GTI Descente": "abc"})
    envois, err = ecrire(sb, res, True)
    verifier("5e  sonde plantee (monitor.scheduled_tasks) : etat garde, rien envoye",
             (retours(res), envois, sb.statut(D), sb.statut("monitor.scheduled_tasks")),
             ([], [], "critical", "unknown"))

    # 5f -- battement illisible, taches LUES : chaque famille pour elle-meme.
    sb = FauxSupabase({W1: "critical", VUE_W: "critical", R: "warning", VUE_T: "warning"})
    sb.workers = None
    res = sonde(sb, TOUT_VA, avec_battement=True)
    envois, err = ecrire(sb, res, True)
    verifier("5f  battement illisible : le worker garde son rouge, la tache vue est reconciliee,"
             " pas de retablissement",
             (retours(res), envois, sb.statut(W1), sb.statut(R)), ([R], [], "critical", "ok"))
    sb = FauxSupabase({W1: "critical", VUE_W: "critical", R: "warning", VUE_T: "warning"})
    sb.workers = None
    res = sonde(sb, TOUT_VA, avec_battement=True)
    envois, err = ecrire(sb, res, False)
    verifier("5f-INVERSE  eteinte : le worker aveugle est declare gueri",
             (retours(res), envois, sb.statut(W1)), ([R, W1], [("recovery", [])], "ok"))

    # 5g -- battement LU et worker revenu : la guerison vue reste annoncee.
    sb = FauxSupabase({W1: "critical", VUE_W: "critical"})
    sb.workers = [{"worker_key": "worker_un", "frequency": "", "status": "active",
                   "last_success_at": cgh.iso_utc(), "criticality": "critical"}]
    res = sonde(sb, TOUT_VA, avec_battement=True)
    envois, err = ecrire(sb, res, True)
    verifier("5g  battement LU et worker revenu : « Retour » et retablissement",
             (retours(res), envois), ([W1], [("recovery", [])]))

    # 5h -- hors Windows (sautee) : on n'a pas regarde.
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    res = [cgh.CheckResult("scheduledtasks", "system", "scheduledtasks", "windows_tasks", "ok", "info",
                           "Verification taches planifiees ignoree (hors Windows)", {"skipped": True})]
    envois, err = ecrire(sb, res, True)
    verifier("5h  sonde sautee (hors Windows) : etat garde", (retours(res), envois, sb.statut(D)),
             ([], [], "critical"))

    # 5i -- etat precedent ILLISIBLE : la regle ne change rien (C.17 inchange).
    sb = FauxSupabase({D: "critical"}, etat_lisible=False)
    res = sonde(sb, DESCENTE_EN_1)
    envois, err = ecrire(sb, res, True)
    verifier("5i  etat precedent illisible : envoi sans deduplication, comme avant",
             envois, [("critical", [VUE_T, D])])


EN_COURS = 267009


def cas_des_taches_en_cours() -> None:
    """La tache « en cours » (27/11) : pas encore de verdict, l'etat precedent est garde."""
    print()
    print("La tache « en cours » (267009), regle 5 allumee :")

    # 5m -- la descente en anomalie redemarre : la panne mesuree (06:50-06:51).
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    res = sonde(sb, dict(TOUT_VA, **{"GTI Descente": EN_COURS}))
    envois, err = ecrire(sb, res, True)
    vue = [r for r in res if r.status_key == VUE_T][0]
    verifier("5m  descente rouge qui redemarre : etat garde, aucun « Retour », aucun envoi",
             (retours(res), envois, sb.statut(D), sb.lignes[D]["message"]), ([], [], "critical", "(d'avant)"))
    verifier("5m' le journal et la vue d'ensemble disent PAR QUOI",
             ("[en cours]" in err and "scheduledtasks:gti_descente=critical" in err, "[regle 5]" in err,
              "1 en cours (etat precedent garde)" in vue.message, vue.details.get("en_cours_cles")),
             (True, False, True, [D]))
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    res = sonde(sb, dict(TOUT_VA, **{"GTI Descente": EN_COURS}), en_cours=False)
    envois, err = ecrire(sb, res, True, en_cours=False)
    vue = [r for r in res if r.status_key == VUE_T][0]
    verifier("5m-INVERSE  eteinte : declaree guerie avant d'avoir fini (le defaut du 15/11)",
             (retours(res), envois, sb.statut(D), "en cours" in vue.message, "en_cours" in vue.details),
             ([D], [("recovery", [])], "ok", False, False))

    # 5n -- une tache SAINE qui tourne : rien a garder, rien ne change.
    sb = FauxSupabase({VUE_T: "ok"})
    res = sonde(sb, dict(TOUT_VA, **{"GTI Descente": EN_COURS}))
    envois, err = ecrire(sb, res, True)
    verifier("5n  tache saine qui tourne : aucune cle, aucun envoi, rien au journal",
             (retours(res), envois, sb.statut(D), "[en cours]" in err), ([], [], None, False))

    # 5o / 5p -- la passe d'apres lit le VRAI resultat.
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    ecrire(sb, sonde(sb, dict(TOUT_VA, **{"GTI Descente": EN_COURS})), True)
    res = sonde(sb, DESCENTE_EN_1)
    envois, err = ecrire(sb, res, True)
    verifier("5o  puis elle finit en 1 : toujours rouge, et PAS de nouvel e-mail (meme incident)",
             (envois, sb.statut(D)), ([], "critical"))
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    ecrire(sb, sonde(sb, dict(TOUT_VA, **{"GTI Descente": EN_COURS})), True)
    res = sonde(sb, TOUT_VA)
    envois, err = ecrire(sb, res, True)
    verifier("5p  puis elle finit en 0 : « Retour a la normale » et retablissement, a ce moment-la",
             (retours(res), envois, sb.statut(D)), ([D], [("recovery", [])], "ok"))

    # 5q -- « jamais lancee » (267011) n'est PAS couvert, expres (tache re-enregistree).
    sb = FauxSupabase({D: "critical", VUE_T: "critical"})
    res = sonde(sb, dict(TOUT_VA, **{"GTI Descente": 267011}))
    envois, err = ecrire(sb, res, True)
    verifier("5q  « jamais lancee » (267011) reste une guerison, comme avant (non couvert, voulu)",
             (retours(res), envois), ([D], [("recovery", [])]))


def cas_du_delai() -> None:
    """La cause (27/11) : la lecture des taches a son propre delai, 60 s."""
    print()
    print("Le delai de la lecture des taches (le VRAI parseur, la VRAIE sonde) :")

    def lire(argv: list[str], duree: float):
        """PowerShell imite qui met `duree` secondes ; rend (delai recu, vue d'ensemble)."""
        args = cgh.build_parser().parse_args(argv)
        args.scheduled_tasks = TACHES
        recu = []

        def run(cmd, **kw):
            recu.append(kw.get("timeout"))
            if duree > kw.get("timeout"):
                raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))
            rows = [{"Name": n, "State": "Ready", "LastResult": 0, "AgeMin": 60} for n in TOUT_VA]
            return FauxProcessus(json.dumps(rows))

        mon = cgh.Monitor(args, None)
        vrai_run = cgh.subprocess.run
        cgh.subprocess.run = run
        try:
            mon.check_scheduled_tasks()
        finally:
            cgh.subprocess.run = vrai_run
        vue = [r for r in mon.results if r.status_key == VUE_T][0]
        return recu, vue

    recu, vue = lire([], 9.9)
    verifier("5j  par defaut, la lecture recoit 60 s, et le delai global reste 15 s",
             (recu, cgh.build_parser().parse_args([]).timeout_seconds), ([60], 15))
    verifier("5j' la vue d'ensemble garde le delai et une duree de lecture",
             (vue.status, vue.details.get("delai_s"), isinstance(vue.details.get("duree_lecture_s"), float)),
             ("ok", 60, True))
    recu, vue = lire([], 20.0)
    verifier("5k  une lecture de 20 s (au-dela des 15 s d'avant) est VUE", (recu, vue.status), ([60], "ok"))
    recu, vue = lire(["--scheduled-tasks-timeout-seconds", "15"], 20.0)
    verifier("5k-INVERSE  delai remis a 15 s : la meme lecture redevient aveugle",
             (recu, vue.status, "timed out after 15 seconds" in vue.message, vue.details.get("delai_s")),
             ([15], "unknown", True, 15))
    recu, vue = lire([], 61.0)
    verifier("5l  au-dela de 60 s : aveugle, et la regle 5 prend le relais (statut unknown)",
             (recu, vue.status), ([60], "unknown"))


def histoire_du_26_11(regle: bool, en_cours: bool):
    """Les passes reelles du 26/11 08:49 au 27/11 08:49 (heures mesurees au serveur)."""
    def lue(descente: int) -> dict[str, int]:
        # recrutement et menage en orange depuis le 24/11 (mesure au serveur)
        return dict(TOUT_VA, **{"GTI Descente": descente, "GTI Recrutement": 1,
                                "GTI Menage Temporaires": 1})

    passes = [
        ("26/11 08:49", None),
        ("26/11 10:49", lue(1)), ("26/11 12:49", lue(1)),
        ("26/11 14:49", None),
        ("26/11 16:49", lue(1)),
        ("26/11 18:49", None),
        ("26/11 20:49", lue(1)), ("26/11 22:49", lue(1)),
        ("27/11 00:49", lue(1)), ("27/11 02:49", lue(1)), ("27/11 04:49", lue(1)),
        ("27/11 06:49", lue(267009)),  # la descente du jour est en cours
        ("27/11 08:49", lue(0)),       # finie en 0 a 07:19 (lue ici, comme avec 60 s)
    ]
    sb = FauxSupabase({R: "warning", M: "warning", VUE_T: "warning"})
    journal_d, envois_tous, retours_tous = [], [], 0
    for heure, taches in passes:
        deja = len(sb.evenements)
        res = sonde(sb, taches, en_cours=en_cours)
        envois, _ = ecrire(sb, res, regle, en_cours=en_cours)
        journal_d += [(heure, ev["status"]) for ev in sb.evenements[deja:] if ev["event_key"] == D]
        retours_tous += len(retours(res))
        envois_tous += [(heure, k) for k, cles in envois]  # TOUS les envois, quels qu'ils soient
    return journal_d, envois_tous, retours_tous


def histoire() -> None:
    print()
    print("L'histoire reelle du 26/11 (descente en code 1, 3 lectures ratees), rejouee :")
    serveur = [("26/11 10:49", "critical"), ("26/11 14:49", "ok"), ("26/11 16:49", "critical"),
               ("26/11 18:49", "ok"), ("26/11 20:49", "critical"), ("27/11 06:49", "ok")]
    journal, envois, nb_retours = histoire_du_26_11(False, False)
    verifier("H-INVERSE  tout eteint : les 6 evenements gti_descente DU SERVEUR, a l'identique",
             journal, serveur)
    verifier("H-INVERSE  tout eteint : 3 alertes descente et 3 retablissements",
             envois, [("26/11 10:49", "critical"), ("26/11 14:49", "recovery"),
                      ("26/11 16:49", "critical"), ("26/11 18:49", "recovery"),
                      ("26/11 20:49", "critical"), ("27/11 06:49", "recovery")])
    verifier("H-INVERSE  tout eteint : 9 « Retour a la normale » (8 faux, comme au serveur, + 1)",
             nb_retours, 9)
    journal, envois, nb_retours = histoire_du_26_11(True, False)
    verifier("H5  regle 5 seule : 2 evenements gti_descente (le rouge, puis la fin LUE EN COURS a 06:49)",
             journal, [("26/11 10:49", "critical"), ("27/11 06:49", "ok")])
    verifier("H5  regle 5 seule : UNE alerte, UN retablissement (a 06:49, sans verdict)",
             envois, [("26/11 10:49", "critical"), ("27/11 06:49", "recovery")])
    verifier("H5  regle 5 seule : 1 seul « Retour a la normale »", nb_retours, 1)
    journal, envois, nb_retours = histoire_du_26_11(True, True)
    verifier("H  tout allume : 2 evenements gti_descente (le rouge, puis le VRAI resultat a 08:49)",
             journal, [("26/11 10:49", "critical"), ("27/11 08:49", "ok")])
    verifier("H  tout allume : UNE alerte, UN retablissement, quand le 0 est lu",
             envois, [("26/11 10:49", "critical"), ("27/11 08:49", "recovery")])
    verifier("H  tout allume : 1 seul « Retour a la normale » (le vrai)", nb_retours, 1)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not cgh.NE_PAS_VOIR_N_EST_PAS_GUERIR:
        print("⚠ l'interrupteur NE_PAS_VOIR_N_EST_PAS_GUERIR est eteint dans le code")
    if not cgh.GARDER_LES_TACHES_EN_COURS:
        print("⚠ l'interrupteur GARDER_LES_TACHES_EN_COURS est eteint dans le code")
    cas_unitaires()
    cas_des_taches_en_cours()
    cas_du_delai()
    histoire()
    print()
    if rates:
        print("%d epreuve(s) sur %d en ECHEC." % (rates, faits))
        return 1
    print("Les %d epreuves passent." % faits)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
