"""Assistant IA, étape 3 lot 1 (13/11/2026) — les gestes par carte de validation.

Lancer depuis backend/ :  <python> tests/test_assistant_gestes.py     (sans réseau, sans le SDK)
requests.get / post / patch / request sont remplacés par un faux serveur qui enregistre chaque appel.
Vérifie : PROPOSER n'écrit RIEN de métier (seulement la carte, par la clé de service) ; les conditions de l'écran
(mandat, validation, une demande à la fois, prix) ; le texte de la demande identique à l'écran ; au CLIC, l'écriture
part avec le JETON de la personne, re-vérifiée ; l'e-mail du négociateur posé par le serveur ; la route : la carte
d'un autre, un rôle non ouvert, un second clic, une carte expirée, un refus de la base.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from fastapi import HTTPException

from app.services import assistant_catalogue as cat
from app.services import assistant_gestes as ges

ok = 0


def voir(vrai, libelle):
    global ok
    assert vrai, libelle
    ok += 1
    print("  VERT  " + libelle)


def refuse(fonction, morceau=""):
    try:
        fonction()
    except cat.Refus as exc:
        return morceau in str(exc)
    return False


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_anon_key = "cle-publique"
    supabase_service_role_key = "cle-de-service"


JETON, EMAIL, UID = "jeton.de.paul", "paul@gti-immobilier.fr", "u-paul"


def nouveau_ctx(role="commercial"):
    return cat.ContexteAssistant(Settings(), UID, EMAIL, role, JETON, conversation_id="c" * 36, nom="Paul NEGO")


class Reponse:
    def __init__(self, data, status=200):
        self.status_code, self._data, self.ok = status, data, status < 400
        self.text = json.dumps(data) if data is not None else ""
        self.headers = {}

    def json(self):
        return self._data


appels = []
etat = {}


BIEN = {"app_dossier_id": 77, "hektor_annonce_id": 63289, "numero_dossier": "VA1", "numero_mandat": "18902",
        "titre_bien": "Maison La Chaise-Dieu", "commercial_nom": "Paul", "validation_diffusion_state": "valide",
        "statut_annonce": "Actif", "prix": 154500.0}


def reset(**kw):
    appels.clear()
    etat.clear()
    etat.update({"bien": [dict(BIEN)],
                 "demandes": [], "contact": [{"hektor_contact_id": "606202", "display_name": "M. DURAND"}],
                 "relance": [{"id": 9, "label": "Rappeler", "due_date": "2026-11-20", "status": "a_faire"}],
                 "refus_demande": False})
    etat.update(kw)


def faux(methode, url, headers=None, params=None, json=None, timeout=None, **_):
    chemin = url.split("/rest/v1/", 1)[1]
    appels.append({"methode": methode, "chemin": chemin, "entetes": dict(headers or {}), "params": dict(params or {}), "corps": json})
    if methode == "GET":
        if chemin == "app_dossiers_current":
            return Reponse(etat["bien"])
        if chemin == "app_diffusion_requests_current":
            return Reponse(etat["demandes"])
        if chemin == "app_contacts_current":
            return Reponse(etat["contact"])
        if chemin == "app_relance_rapprochement":
            return Reponse(etat["relance"])
    if methode == "POST":
        if chemin == "app_assistant_action":
            return Reponse([{"id": "a" * 36, "expire_le": "2026-11-13T12:00:00+00:00"}])
        if chemin == "app_diffusion_request":
            if etat["refus_demande"]:
                return Reponse({"message": "new row violates row-level security policy"}, status=403)
            return Reponse([{"id": "d" * 36}])
        if chemin == "app_diffusion_request_event":
            return Reponse([{"id": "e"}])
        if chemin == "rpc/app_create_relance_for_contact":
            return Reponse([{"id": 12, "due_date": json["p_due_date"]}])
        if chemin == "rpc/app_relance_set_status":
            etat["relance"] = [{**etat["relance"][0], "status": json["p_status"]}]
            return Reponse(None, status=204)
    return Reponse([], status=404)


requests.get = lambda url, **kw: faux("GET", url, **kw)
requests.post = lambda url, **kw: faux("POST", url, **kw)
requests.patch = lambda url, **kw: faux("PATCH", url, **kw)
requests.request = lambda methode, url, **kw: faux(methode, url, **kw)


def ecritures_metier():
    return [a for a in appels if a["methode"] != "GET" and a["chemin"] != "app_assistant_action"]


print("1) proposer ne fait RIEN de métier : une carte, par le serveur")
reset()
ctx = nouveau_ctx()
proposer = next(f for f in cat.CATALOGUE if f.nom == "proposer_demande_direction")
r = proposer.executer(ctx, {"type": "baisse_prix", "hektor_annonce_id": 63289, "nouveau_prix": "185 000 €", "commentaire": "4 mois sans offre"})
voir(r["carte_proposee"] and "Ne dis jamais que c'est fait" in r["a_dire"], "le modèle apprend qu'une carte attend le clic, rien de fait")
voir(ecritures_metier() == [], "AUCUNE écriture métier à la proposition (ni demande, ni événement)")
carte = next(a for a in appels if a["chemin"] == "app_assistant_action")
voir(carte["entetes"]["Authorization"] == "Bearer cle-de-service", "la carte est rangée par le SERVEUR (la table n'est pas écrite par l'écran)")
voir(carte["corps"][0]["user_id"] == UID and carte["corps"][0]["conversation_id"] == "c" * 36, "la carte est à la personne et à sa conversation")
voir("185 000 €" in carte["corps"][0]["resume"] and "154 500 €" in carte["corps"][0]["resume"], "le résumé dit le nouveau prix ET l'ancien")
voir(carte["corps"][0]["parametres"]["nouveau_prix"] == "185000", "prix normalisé comme l'écran (« 185 000 € » → 185000)")
voir(len(ctx.cartes) == 1 and ctx.cartes[0]["geste"] == "demande_direction", "la carte part dans le flux vers l'écran")
lecture = next(a for a in appels if a["chemin"] == "app_dossiers_current")
voir(lecture["entetes"]["Authorization"] == "Bearer " + JETON, "le bien est lu avec le JETON de la personne")

print("2) les conditions de l'écran (App.tsx:20375)")
reset(bien=[{**BIEN, "numero_mandat": None}])
voir(refuse(lambda: ges.preparer_demande(nouveau_ctx(), {"type": "annulation_mandat", "hektor_annonce_id": 63289}), "numéro de mandat"),
     "sans numéro de mandat : refusée")
reset(bien=[{**BIEN, "validation_diffusion_state": "a_controler"}])
voir(refuse(lambda: ges.preparer_demande(nouveau_ctx(), {"type": "baisse_prix", "hektor_annonce_id": 63289, "nouveau_prix": "1"}), "validation = oui"),
     "baisse sur un mandat non validé : refusée (règle de l'écran)")
voir(ges.preparer_demande(nouveau_ctx(), {"type": "diffusion", "hektor_annonce_id": 63289, "nouveau_prix": "", "commentaire": ""})[1]["type"] == "diffusion",
     "TÉMOIN : la demande de validation passe justement quand le mandat n'est pas validé")
reset()
voir(refuse(lambda: ges.preparer_demande(nouveau_ctx(), {"type": "diffusion", "hektor_annonce_id": 63289}), "déjà validé"),
     "demande de validation sur un mandat déjà validé : refusée")
reset(demandes=[{"id": "x", "request_status": "pending"}])
voir(refuse(lambda: ges.preparer_demande(nouveau_ctx(), {"type": "annulation_mandat", "hektor_annonce_id": 63289}), "déjà en cours"),
     "une demande du même type déjà en cours : refusée")
reset()
voir(refuse(lambda: ges.preparer_demande(nouveau_ctx(), {"type": "baisse_prix", "hektor_annonce_id": 63289, "nouveau_prix": "beaucoup moins"}), "montant"),
     "un prix illisible est refusé")
reset(bien=[])
voir(refuse(lambda: ges.preparer_demande(nouveau_ctx(), {"type": "baisse_prix", "hektor_annonce_id": 63289}), "biens vivants"),
     "un bien invisible pour la personne : refusé")

print("3) au CLIC : l'écriture de l'écran, avec le jeton, re-vérifiée")
reset()
p = ges.preparer_demande(nouveau_ctx(), {"type": "baisse_prix", "hektor_annonce_id": 63289, "nouveau_prix": "185000", "commentaire": "4 mois sans offre"})[1]
appels.clear()
res = ges.executer_demande(nouveau_ctx(), p)
insert = next(a for a in appels if a["chemin"] == "app_diffusion_request")
voir(insert["entetes"]["Authorization"] == "Bearer " + JETON, "la demande part avec le JETON (la règle d'écriture de la base s'applique)")
voir(insert["corps"]["requested_by"] == UID and insert["corps"]["requested_by_label"] == "Paul NEGO", "demandée par la personne, à son nom")
voir(insert["corps"]["request_comment"] == "Demande de baisse de prix\nNouveau prix demande : 185000\nCommentaire : 4 mois sans offre",
     "le texte est celui de l'écran, que Pauline relit (et d'où l'écran extrait le prix)")
voir(insert["corps"]["request_type"] == "demande_baisse_prix" and insert["corps"]["numero_mandat"] == "18902", "type et mandat")
voir(any(a["chemin"] == "app_diffusion_request_event" and a["corps"]["event_type"] == "request_created" for a in appels)
     and res["historique_ecrit"], "l'événement « demande envoyée » est écrit, comme à l'écran")
reset(demandes=[{"id": "y", "request_status": "pending"}])
appels.clear()
voir(refuse(lambda: ges.executer_demande(nouveau_ctx(), p), "déjà en cours") and ecritures_metier() == [],
     "une demande créée ENTRE la carte et le clic : rien n'est écrit (re-vérifié au clic)")
reset(refus_demande=True)
voir(refuse(lambda: ges.executer_demande(nouveau_ctx(), p), "la base a refusé"), "un refus de la base est dit en clair, jamais un faux succès")

print("4) les relances (fonctions de la base SANS contrôle : lecture avec le jeton d'abord)")
reset()
resume, pr = ges.preparer_relance(nouveau_ctx(), {"hektor_contact_id": "606202", "libelle": "Rappeler pour la visite",
                                                  "echeance": "2026-11-20", "detail": "", "hektor_annonce_id": ""})
voir("M. DURAND" in resume and "20/11/2026" in resume, "le résumé nomme le contact et la date")
appels.clear()
ges.executer_relance(nouveau_ctx(), pr)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_create_relance_for_contact")
voir(rpc["corps"]["p_negociateur_email"] == EMAIL and rpc["entetes"]["Authorization"] == "Bearer " + JETON,
     "la relance revient à la personne : e-mail posé par le SERVEUR, écriture avec son jeton")
voir(appels[0]["chemin"] == "app_contacts_current", "le contact est relu AVANT l'écriture (la fonction ne contrôle pas l'appelant)")
reset(contact=[])
voir(refuse(lambda: ges.preparer_relance(nouveau_ctx(), {"hektor_contact_id": "1", "libelle": "x", "echeance": "2026-11-20"}), "peux voir"),
     "un contact invisible : refusé")
reset()
voir(refuse(lambda: ges.preparer_relance(nouveau_ctx(), {"hektor_contact_id": "606202", "libelle": "x", "echeance": "jeudi"}), "AAAA-MM-JJ"),
     "une date illisible est refusée")
resume, ps = ges.preparer_statut_relance(nouveau_ctx(), {"relance_id": 9, "statut": "reporte"})
voir("Reporter de 3 jours" in resume, "reporter = +3 jours, comme l'écran")
r = ges.executer_statut_relance(nouveau_ctx(), ps)
voir(r["statut"] == "reporte", "l'état est RELU après l'écriture")
reset(relance=[{"id": 9, "label": "Rappeler", "due_date": None, "status": "fait"}])
voir(refuse(lambda: ges.preparer_statut_relance(nouveau_ctx(), {"relance_id": 9, "statut": "fait"}), "déjà faite"), "une relance déjà faite : refusée")

print("5) la route du clic")
from app.routers import assistant as route


class User:
    def __init__(self, uid):
        self.id, self.email = uid, EMAIL


class Service:
    def __init__(self, carte, prise=True):
        self._carte, self._prise, self.fins = carte, prise, []

    def carte(self, action_id):
        return self._carte

    def prendre_carte(self, action_id, user_id, etat_):
        return {**self._carte, "etat": etat_} if self._prise else None

    def terminer_carte(self, action_id, etat_, resultat):
        self.fins.append((etat_, resultat))


def cliquer(carte, role="commercial", uid=UID, prise=True):
    service = Service(carte, prise)
    route._ouvrir = lambda *a: (User(uid), {"role": role, "display_name": "Paul NEGO"})
    try:
        return route.assistant_valider("a" * 36, "Bearer " + JETON, Settings(), None, service), service
    except HTTPException as exc:
        return exc.status_code, service


reset()
c = {"id": "a" * 36, "user_id": UID, "geste": "statut_relance", "etat": "proposee", "parametres": {"relance_id": 9, "statut": "fait"},
     "conversation_id": "c" * 36}
r, s = cliquer(c)
voir(r["ok"] and r["etat"] == "executee" and s.fins[-1][0] == "executee", "le clic exécute le geste et le note sur la carte")
reset()
r, s = cliquer(c, uid="u-autre")
voir(r == 404 and not ecritures_metier(), "la carte d'un AUTRE : introuvable, rien n'est fait (même l'admin ne valide pas à la place)")
r, s = cliquer({**c, "geste": "geste_inconnu"})
voir(r == 403, "un geste inconnu ou non ouvert au rôle : refusé")
reset()
r, s = cliquer(c, prise=False)
voir(r == 409 and not ecritures_metier() and s.fins[-1][0] == "expiree", "second clic ou carte expirée : 409, rien n'est fait")
reset(relance=[{"id": 9, "label": "Rappeler", "due_date": None, "status": "fait"}])
r, s = cliquer(c)
voir(r["ok"] is False and r["etat"] == "echec" and "faite entre-temps" in r["detail"], "le monde a changé avant le clic : échec dit en clair")

print("6) aucune fonction de geste ne fait autre chose que proposer")
voir(all(f.nom.startswith("proposer_") for f in ges.FONCTIONS_GESTES) and len(ges.FONCTIONS_GESTES) == 3,
     "3 gestes, tous « proposer_ » : le modèle n'a AUCUNE fonction qui exécute")

print(f"\n{ok} contrôles verts")
