# -*- coding: utf-8 -*-
"""La connexion du ROBOT du recrutement a la base (R4, 24/11/2026).

Le robot est le role Postgres « recrutement_robot » (patch_recrutement_schema_2026-11-24.sql) : il n'a de
droits QUE sur le schema « recrutement ». Un defaut de la montee ou de la descente ne peut donc toucher
aucune autre table de l'app -- c'est la difference avec la cle de service du .env, qui ouvre tout.

Il se connecte par le « pooler » de Supabase (le meme chemin que Console/sauvegarde_plan_supabase.js),
avec l'utilisateur « recrutement_robot.<projet> ».

SES REGLAGES vivent dans C:\\Hektor\\recrutement_donnees\\robot.env, ecrit par Frederic avec
recrutement/poser_mot_de_passe_robot.ps1 (le mot de passe ne passe JAMAIS sous les yeux de Claude, et
ce fichier ne lit JAMAIS le .env du projet) :
    RECRUTEMENT_ROBOT_HOTE=...pooler.supabase.com
    RECRUTEMENT_ROBOT_PORT=5432
    RECRUTEMENT_ROBOT_UTILISATEUR=recrutement_robot.<projet>
    RECRUTEMENT_ROBOT_MOT_DE_PASSE=...

Interprete : le Python SYSTEME (psycopg2 y est ; le .venv du projet ne l'a pas). Le lanceur le dit.
"""
import os
import sys
from pathlib import Path

DOSSIER = Path(os.environ.get("RECRUTEMENT_DONNEES", r"C:\Hektor\recrutement_donnees"))
FICHIER = DOSSIER / "robot.env"
CLES = ("RECRUTEMENT_ROBOT_HOTE", "RECRUTEMENT_ROBOT_PORT", "RECRUTEMENT_ROBOT_UTILISATEUR",
        "RECRUTEMENT_ROBOT_MOT_DE_PASSE")


class RobotIndisponible(Exception):
    """Le robot ne peut pas se connecter : reglages absents, pilote absent, ou base injoignable."""


def reglages() -> dict:
    if not FICHIER.exists():
        raise RobotIndisponible(f"{FICHIER} absent : Frederic doit lancer recrutement/poser_mot_de_passe_robot.ps1")
    valeurs = {}
    for ligne in FICHIER.read_text(encoding="utf-8-sig").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        k, v = ligne.split("=", 1)
        valeurs[k.strip()] = v.strip()
    manquantes = [k for k in CLES if not valeurs.get(k)]
    if manquantes:
        raise RobotIndisponible(f"{FICHIER} incomplet : {', '.join(manquantes)}")
    return valeurs


def connexion():
    """Une connexion psycopg2 du robot, en UTF-8, SSL exige. Ne rend jamais le mot de passe."""
    try:
        import psycopg2
    except ImportError as e:
        raise RobotIndisponible(f"psycopg2 absent de cet interprete ({sys.executable}) : {e}") from None
    r = reglages()
    try:
        con = psycopg2.connect(host=r["RECRUTEMENT_ROBOT_HOTE"], port=int(r["RECRUTEMENT_ROBOT_PORT"]),
                               user=r["RECRUTEMENT_ROBOT_UTILISATEUR"], password=r["RECRUTEMENT_ROBOT_MOT_DE_PASSE"],
                               dbname="postgres", sslmode="require", connect_timeout=20,
                               application_name="recrutement_robot")
    except Exception as e:  # le message de psycopg2 ne contient pas le mot de passe
        raise RobotIndisponible(f"connexion refusee ou base injoignable : {str(e).strip()[:300]}") from None
    con.set_client_encoding("UTF8")
    return con
