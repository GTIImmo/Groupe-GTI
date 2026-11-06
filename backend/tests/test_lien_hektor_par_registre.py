"""Le lien « compte de l'app -> compte Hektor » par le REGISTRE (05/11/2026, audit §41).

Hors ligne : les tables sont des listes en mémoire, copiées de la base le 05/11 (comptes de Frédéric, Franck, Pauline,
Mélanie LEGRAND, Emmanuelle PEREIRA). Rien n'est lu ni écrit en production.
Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_lien_hektor_par_registre.py   (sortie 0 = tout vert)
"""
from __future__ import annotations

import copy
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import supabase_admin as module
from app.services.supabase_admin import SupabaseAdminService

USERS = [  # app_user_directory (extrait)
    {"id_user": "2", "user_type": "NEGO", "display_name": "FRANCK GERPHAGNON", "email": "franck.gerphagnon@gmail.com"},
    {"id_user": "3", "user_type": "SECRETAIRE", "display_name": "Pauline GIRINON", "email": "sashagerphagnon@gmail.com"},
    {"id_user": "7", "user_type": "SECRETAIRE", "display_name": "Franck GERPHAGNON", "email": "franck.gerphagnon@gmail.com"},
    {"id_user": "8", "user_type": "SECRETAIRE", "display_name": "Pauline GIRINON", "email": "p.girinon@gti-immobilier.fr"},
    {"id_user": "30", "user_type": "NEGO", "display_name": "Mélanie LEGRAND", "email": "legrand@gti-immobilier.fr"},
    {"id_user": "51", "user_type": "NEGO", "display_name": "Emmanuelle PEREIRA", "email": "pereira@gti-immobilier.fr"},
]
ANNUAIRE = [  # app_hektor_negotiator_agency_directory (extrait)
    {"hektor_negociateur_id": "1", "hektor_user_id": "2", "agence_nom": "Compte formation", "email": "franck.gerphagnon@gmail.com", "is_active": True},
    {"hektor_negociateur_id": "19", "hektor_user_id": "44", "agence_nom": "Groupe GTI Firminy", "email": "franck.gerphagnon@gmail.com", "is_active": False},
    {"hektor_negociateur_id": "5", "hektor_user_id": "30", "agence_nom": "Groupe GTI Saint-Etienne", "email": "legrand@gti-immobilier.fr", "is_active": True},
    {"hektor_negociateur_id": "26", "hektor_user_id": "51", "agence_nom": "Groupe GTI Firminy", "email": "pereira@gti-immobilier.fr", "is_active": True},
]


def fiche(personne, sorte, nego, user, actif, email, user_type=None, agence=None):
    return {"app_personne_id": personne, "sorte": sorte, "hektor_negociateur_id": nego, "hektor_user_id": user,
            "actif_chez_hektor": actif, "email_vu": email, "user_type": user_type, "agence_nom": agence}


FICHES = [  # app_negociateur_fiche (extrait)
    fiche(1000001, "compte_utilisateur", None, "4", True, None, "ADMIN"),
    fiche(1000001, "fiche_negociateur", "20", "46", False, "frederic.gerphagnon@gti-immobilier.fr", agence="Groupe GTI Firminy"),
    fiche(1000036, "compte_utilisateur", None, "7", True, "franck.gerphagnon@gmail.com", "SECRETAIRE"),
    fiche(1000036, "fiche_negociateur", "1", "2", True, "franck.gerphagnon@gmail.com", agence="Compte formation"),
    fiche(1000036, "fiche_negociateur", "19", "44", False, "franck.gerphagnon@gmail.com", agence="Groupe GTI Firminy"),
    fiche(1000048, "compte_utilisateur", None, "8", True, "p.girinon@gti-immobilier.fr", "SECRETAIRE"),
    fiche(1000048, "compte_utilisateur", None, "3", True, "sashagerphagnon@gmail.com", "SECRETAIRE"),
    fiche(1000048, "fiche_negociateur", "22", "47", False, "p.girinon@gti-immobilier.fr", agence="Groupe GTI Firminy"),
    fiche(1000042, "fiche_negociateur", "5", "30", True, "legrand@gti-immobilier.fr", agence="Groupe GTI Saint-Etienne"),
    fiche(1000035, "fiche_negociateur", "26", "51", True, "pereira@gti-immobilier.fr", agence="Groupe GTI Firminy"),
]


def correspond(valeur, filtre: str) -> bool:
    op, _, attendu = filtre.partition(".")
    texte = "" if valeur is None else str(valeur).lower() if isinstance(valeur, bool) else str(valeur)  # PostgREST : true/false
    if op == "eq":
        return texte == attendu
    if op == "neq":
        return texte != attendu
    if op == "ilike":
        return texte.lower() == attendu.lower()
    raise AssertionError(f"filtre inconnu {filtre}")


class Faux(SupabaseAdminService):
    def __init__(self, tables):
        super().__init__(SimpleNamespace(supabase_url="http://faux", google_workspace_domain="gti-immobilier.fr",
                                         supabase_service_role_key="x"))
        self.tables = tables
        self.lus: list[str] = []

    def _rest_rows(self, table, params, fallback):
        self.lus.append(table)
        filtres = {k: v for k, v in params.items() if k not in ("select", "limit", "order")}
        lignes = [r for r in self.tables[table] if all(correspond(r.get(k), v) for k, v in filtres.items())]
        return copy.deepcopy(lignes[: int(params.get("limit", 1000))])


def faux(fiches=None, users=None, annuaire=None):
    return Faux({"app_user_directory": users or USERS, "app_hektor_negotiator_agency_directory": annuaire or ANNUAIRE,
                 "app_negociateur_fiche": fiches or FICHES})


# --- les vrais comptes -------------------------------------------------------------------------------------------

def test_franck_admin_jamais_relie_a_sa_fiche_negociateur():
    """06/11 (§54) : Franck est ADMIN dans l'app -> jamais relié à sa fiche « Compte formation » (règle de Frédéric)."""
    r = faux()._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "admin", 1000036)
    assert (r["link_status"], r["hektor_user_id"], r["hektor_negociateur_id"], r["negociateur_email"]) == ("linked", None, None, None)
    assert r["metadata_json"]["match_source"] == "compte_non_negociateur"
    # son compte secrétaire reste NOTÉ, pas envoyé
    assert {"hektor_user_id": "7", "type": "SECRETAIRE", "actif": True} in r["metadata_json"]["comptes_hektor"]


def test_negociateur_relie_a_sa_fiche_active_par_le_registre():
    """Le chemin du §41 reste vrai pour un NÉGOCIATEUR (même cas que Franck, compte « commercial »)."""
    r = faux()._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "commercial", 1000036)
    assert (r["link_status"], r["hektor_user_id"], r["hektor_negociateur_id"]) == ("linked", "2", "1")
    assert r["negociateur_email"] == "franck.gerphagnon@gmail.com"
    assert r["metadata_json"]["match_source"] == "registre_fiche_active"


def test_admin_jamais_relie_meme_par_son_email():
    """Un admin dont l'e-mail est celui d'un NÉGOCIATEUR actif n'est pas relié non plus (manager et lecture pareil)."""
    for role in ("admin", "manager", "lecture"):
        r = faux()._resolve_hektor_google_identity("pereira@gti-immobilier.fr", role, 1000035)
        assert (r["hektor_user_id"], r["hektor_negociateur_id"], r["negociateur_email"]) == (None, None, None), role
        assert r["metadata_json"]["match_source"] == "compte_non_negociateur", role


def test_franck_sans_registre_reste_comme_avant():
    """Témoin : sans la personne du registre, rien ne change (c'est bien le registre qui relie)."""
    r = faux()._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "admin", None)
    assert (r["link_status"], r["hektor_user_id"], r["metadata_json"]["match_source"]) == ("linked", None, "compte_non_negociateur")
    assert "comptes_hektor" not in r["metadata_json"]


def test_frederic_compte_admin_note_jamais_envoye():
    r = faux()._resolve_hektor_google_identity("frederic.gerphagnon@gti-immobilier.fr", "admin", 1000001)
    assert (r["hektor_user_id"], r["hektor_negociateur_id"], r["metadata_json"]["match_source"]) == (None, None, "compte_non_negociateur")
    assert r["metadata_json"]["comptes_hektor"] == [{"hektor_user_id": "4", "type": "ADMIN", "actif": True}]


def test_pauline_deux_comptes_secretaires_notes_aucun_envoye():
    r = faux()._resolve_hektor_google_identity("p.girinon@gti-immobilier.fr", "admin", 1000048)
    assert r["hektor_user_id"] is None
    assert sorted(c["hektor_user_id"] for c in r["metadata_json"]["comptes_hektor"]) == ["3", "8"]


def test_negociateurs_par_email_inchanges():
    for email, personne, user, nego in (("legrand@gti-immobilier.fr", 1000042, "30", "5"),
                                        ("pereira@gti-immobilier.fr", 1000035, "51", "26")):
        for p in (personne, None):
            r = faux()._resolve_hektor_google_identity(email, "commercial", p)
            assert (r["hektor_user_id"], r["hektor_negociateur_id"]) == (user, nego)
            assert r["metadata_json"]["match_source"] == "app_hektor_negotiator_agency_directory"


def test_commercial_sans_rien_reste_en_attente():
    r = faux()._resolve_hektor_google_identity("inconnu@gti-immobilier.fr", "commercial", 1000001)
    assert (r["link_status"], r["hektor_user_id"]) == ("pending", None)


# --- les garde-fous, chacun avec son témoin positif ------------------------------------------------------------

def test_deux_fiches_actives_rien_n_est_devine():
    fiches = FICHES + [fiche(1000036, "fiche_negociateur", "99", "999", True, "franck.gerphagnon@gmail.com")]
    r = faux(fiches=fiches)._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "commercial", 1000036)
    assert r["hektor_user_id"] is None and r["metadata_json"]["registre_fiches_negociateur_actives"] == 2


def test_fiche_active_inconnue_du_worker_refusee():
    users = [u for u in USERS if u["id_user"] != "2"]  # le worker refuserait ce numéro (loadHektorDirectoryUserById)
    r = faux(users=users)._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "commercial", 1000036)
    assert r["hektor_user_id"] is None
    assert r["metadata_json"]["registre_refus"] == "fiche_active_absente_des_annuaires_du_worker"


def test_fiche_active_eteinte_dans_l_annuaire_refusee():
    annuaire = [dict(a, is_active=False) if a["hektor_user_id"] == "2" else a for a in ANNUAIRE]
    r = faux(annuaire=annuaire)._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "commercial", 1000036)
    assert r["hektor_user_id"] is None


def test_fiche_eteinte_jamais_prise():
    fiches = [dict(f, actif_chez_hektor=False) if f["hektor_user_id"] == "2" else f for f in FICHES]
    r = faux(fiches=fiches)._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "commercial", 1000036)
    assert r["hektor_user_id"] is None  # la fiche 19 (éteinte) n'est pas prise à sa place


def test_boite_partagee_pas_reprise_comme_email():
    fiches = FICHES + [fiche(1000008, "fiche_negociateur", "25", "50", False, "franck.gerphagnon@gmail.com")]
    r = faux(fiches=fiches)._resolve_hektor_google_identity("franck.gerphagnon@gti-immobilier.fr", "commercial", 1000036)
    assert r["hektor_user_id"] == "2" and r["negociateur_email"] is None
    assert r["metadata_json"]["registre_email_partage"] == "franck.gerphagnon@gmail.com"


# --- l'ordre : le registre AVANT le compte Hektor ------------------------------------------------------------

def test_personne_reliee():
    for etat, attendu in (("relie", 1000036), ("deja", 1000036), ("cree", 1000036),
                          ("a_choisir", None), ("conflit", None), ("erreur", None), ("non_relie", None)):
        assert SupabaseAdminService._personne_reliee({"etat": etat, "personne": 1000036}) == attendu, etat
    assert SupabaseAdminService._personne_reliee(None) is None


def test_update_user_relie_le_registre_avant_le_compte_hektor():
    service = faux()
    ordre: list[str] = []
    vrai_patch = module.requests.patch
    module.requests.patch = lambda *a, **k: SimpleNamespace(ok=True)  # aucun appel réseau
    try:
        service._lier_registre_sans_echec = lambda **k: ordre.append("registre") or {"etat": "deja", "personne": 1000036}
        service._sync_google_workspace_identity = lambda **k: ordre.append(f"hektor:{k['personne']}") or {}
        service.update_user({"id": "u", "email": "franck.gerphagnon@gti-immobilier.fr", "role": "admin", "isActive": True})
    finally:
        module.requests.patch = vrai_patch
    assert ordre == ["registre", "hektor:1000036"]


if __name__ == "__main__":
    essais = [(nom, f) for nom, f in sorted(globals().items()) if nom.startswith("test_") and callable(f)]
    rates = 0
    for nom, f in essais:
        try:
            f()
            print(f"  vert   {nom}")
        except Exception as erreur:  # noqa: BLE001
            rates += 1
            print(f"  ROUGE  {nom} : {type(erreur).__name__} {erreur}")
    print(f"{len(essais) - rates}/{len(essais)} verts")
    raise SystemExit(1 if rates else 0)
