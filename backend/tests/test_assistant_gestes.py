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
                 "demandes": [], "contact": [{"hektor_contact_id": "606202", "display_name": "M. DURAND",
                                              "nom": "DURAND", "phone_primary": "0601020304", "email": "durand@exemple.fr",
                                              "commentaires": None, "archive": False, "active_search_count": 2}],
                 "relance": [{"id": 9, "label": "Rappeler", "due_date": "2026-11-20", "status": "a_faire"}],
                 "refus_demande": False,
                 "recherche": [{"contact_search_key": "606202:0", "hektor_contact_id": "606202", "search_index": 1,
                                "archive": False, "is_active": True}],
                 "notifs": [{"id": 1, "type": "nouveau_rapprochement", "title": "a", "read_at": None, "negociateur_email": EMAIL},
                            {"id": 2, "type": "mandat_echu", "title": "b", "read_at": None, "negociateur_email": EMAIL},
                            {"id": 3, "type": "nouveau_rapprochement", "title": "c", "read_at": None,
                             "negociateur_email": "collegue@gti-immobilier.fr"}],
                 "affaire": [{"app_affaire_id": 501}], "note": [{"texte": "Acquéreurs pressés"}]})
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
        if chemin == "app_contact_searches_current":
            return Reponse(etat["recherche"])
        if chemin == "app_notification":
            p_ = params or {}
            lignes = [n for n in etat["notifs"] if n["negociateur_email"] == p_.get("negociateur_email", "")[3:]]
            if p_.get("id"):
                voulus = p_["id"][4:-1].split(",")
                lignes = [n for n in lignes if str(n["id"]) in voulus]
            if p_.get("type"):
                lignes = [n for n in lignes if n["type"] == p_["type"][3:]]
            return Reponse([n for n in lignes if n["read_at"] is None])
        if chemin == "app_affaire_ledger":
            return Reponse(etat["affaire"])
        if chemin == "app_affaire_note":
            return Reponse(etat["note"])
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
        if chemin == "rpc/app_mark_notification_read":
            for n in etat["notifs"]:
                if n["id"] == json["p_id"]:
                    n["read_at"] = "maintenant"
            return Reponse(None, status=204)
        if chemin in {"rpc/app_record_proposition", "rpc/app_set_bien_statut", "rpc/app_console_archiver_contact_optimistic",
                      "rpc/app_console_create_delete_contact_search_job", "rpc/app_affaire_note_ecrire",
                      "rpc/app_edit_contact_optimistic"}:
            return Reponse({"ok": True})
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

print("6) LOT 2a : chez nous seulement")
reset()
resume, pp = ges.preparer_proposition(nouveau_ctx(), {"contact_search_key": "606202:0", "hektor_annonce_id": 63289, "note": "intéressé"})
voir("TÉLÉPHONE" in resume and "M. DURAND" in resume and "relance de suivi" in resume, "le résumé dit le canal, l'acquéreur et la relance posée")
appels.clear()
ges.executer_proposition(nouveau_ctx(), pp)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_record_proposition")
voir(rpc["corps"]["p_channel"] == "telephone" and rpc["corps"]["p_nego"] == EMAIL and rpc["corps"]["p_dossier_id"] == 77,
     "téléphone seulement ; le négociateur posé par le SERVEUR ; le bien par son identifiant")
voir([a["chemin"] for a in appels][:2] == ["app_contact_searches_current", "app_dossiers_current"],
     "la recherche et le bien sont RELUS avec le jeton avant la fonction sans contrôle")
reset(recherche=[])
voir(refuse(lambda: ges.preparer_proposition(nouveau_ctx(), {"contact_search_key": "x", "hektor_annonce_id": 63289}), "peux voir"),
     "une recherche invisible : refusée")
reset()
_, ps = ges.preparer_statut_bien(nouveau_ctx(), {"contact_search_key": "606202:0", "hektor_annonce_id": 63289, "statut": "retabli", "motif": "x"})
appels.clear()
ges.executer_statut_bien(nouveau_ctx(), ps)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_set_bien_statut")
voir(rpc["corps"]["p_status"] == "jamais_vu" and rpc["corps"]["p_reason"] is None, "rétablir = « jamais vu », comme l'écran, sans motif")
voir(refuse(lambda: ges.preparer_statut_bien(nouveau_ctx(), {"contact_search_key": "606202:0", "hektor_annonce_id": 63289, "statut": "offre"}),
            "ecarte"), "un statut hors liste (ex. offre) : refusé")
reset()
resume, pn = ges.preparer_notifications(nouveau_ctx(), {"notification_ids": "", "type": "nouveau_rapprochement"})
voir(pn["notification_ids"] == [1] and "1 de tes notifications" in resume,
     "par type : seulement les SIENNES (celle du collègue, même type, n'est pas prise)")
r = ges.executer_notifications(nouveau_ctx(), {"notification_ids": [1, 3]})
voir(r["marquees"] == 1 and etat["notifs"][2]["read_at"] is None,
     "TÉMOIN : même si on glisse le numéro d'un collègue dans la carte, il n'est PAS marqué (re-vérifié au clic)")
voir(refuse(lambda: ges.preparer_notifications(nouveau_ctx(), {"notification_ids": "abc", "type": ""}), "nombres"),
     "des numéros illisibles : refusés")
reset()
resume, pt = ges.preparer_note(nouveau_ctx("manager"), {"app_affaire_id": 501, "texte": "Signature le 2 décembre"})
voir("REMPLACE la note actuelle" in resume and "Acquéreurs pressés" in resume, "la carte montre l'ancienne note qu'elle remplace")
voir(next(f for f in ges.FONCTIONS_GESTES if f.nom == "proposer_note_transaction").roles == ges.DIRECTION,
     "la note de transaction est réservée à la direction, comme l'écran")
voir(refuse(lambda: ges.preparer_note(nouveau_ctx(), {"app_affaire_id": "x", "texte": "t"}), "app_affaire_id"), "une transaction illisible : refusée")
reset(affaire=[])
voir(refuse(lambda: ges.preparer_note(nouveau_ctx("admin"), {"app_affaire_id": 9, "texte": "t"}), "peux voir")
     and not any(a["chemin"] == "app_affaire_note" for a in appels),
     "transaction invisible : refusée, et la note (lisible par tous) n'est JAMAIS lue avant elle")

print("7) LOT 2b : vers Hektor")
reset()
resume, pc = ges.preparer_modif_contact(nouveau_ctx(), {"hektor_contact_id": "606202", "telephone": "0611223344",
                                                        "email": "durand@exemple.fr", "commentaire": ""})
voir(pc["champs"] == {"phone": "0611223344"} and "0601020304" in resume and "0611223344" in resume,
     "seul le champ qui CHANGE part (l'e-mail identique n'est pas renvoyé) ; la carte montre avant -> après")
appels.clear()
ges.executer_modif_contact(nouveau_ctx(), pc)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_edit_contact_optimistic")
voir(rpc["corps"]["edit_fields"] == {"last_name": "DURAND", "phone": "0611223344"} and rpc["entetes"]["Authorization"] == "Bearer " + JETON,
     "la fonction de l'écran, avec le jeton : le champ changé + le NOM ACTUEL (le worker l'exige, prouvé en réel le 13/11)")
reset(contact=[{"hektor_contact_id": "606202", "display_name": "?", "nom": None, "phone_primary": None, "email": None,
                "commentaires": None, "archive": False, "active_search_count": 0}])
voir(refuse(lambda: ges.executer_modif_contact(nouveau_ctx(), {"hektor_contact_id": "606202", "champs": {"phone": "06"}}), "pas de nom")
     and not any(a["chemin"] == "rpc/app_edit_contact_optimistic" for a in appels),
     "un contact sans nom : rien n'est lancé (Hektor refuserait, et la fiche resterait fausse chez nous)")
reset()
voir(refuse(lambda: ges.preparer_modif_contact(nouveau_ctx(), {"hektor_contact_id": "606202", "telephone": "0601020304", "email": "",
                                                               "commentaire": ""}), "Rien ne change"), "rien ne change : pas de carte")
voir(refuse(lambda: ges.preparer_modif_contact(nouveau_ctx(), {"hektor_contact_id": "606202", "telephone": "", "email": "pas-un-mail",
                                                               "commentaire": ""}), "adresse e-mail"), "un e-mail illisible : refusé")
voir("address" not in {c[1] for c in ges._CHAMPS_CONTACT}, "l'adresse n'est PAS modifiable par l'assistant (identifiants de commune)")
resume, pa = ges.preparer_archivage_contact(nouveau_ctx(), {"hektor_contact_id": "606202", "archiver": True})
voir("2 recherche(s) active(s) seront archivées aussi" in resume, "archiver prévient que ses recherches partent avec")
voir(refuse(lambda: ges.preparer_archivage_contact(nouveau_ctx(), {"hektor_contact_id": "606202", "archiver": False}), "pas archivé"),
     "réactiver un contact actif : refusé")
resume, pr = ges.preparer_archivage_recherche(nouveau_ctx(), {"contact_search_key": "606202:0"})
voir("recherche n° 2" in resume, "le rang de la recherche est dit (index 1 = la 2e)")
appels.clear()
ges.executer_archivage_recherche(nouveau_ctx(), pr)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_console_create_delete_contact_search_job")
voir(rpc["corps"]["search_index"] == 1 and rpc["corps"]["target_contact_id"] == "606202", "le rang est RELU au clic et envoyé")
reset(recherche=[{"contact_search_key": "606202:0", "hektor_contact_id": "606202", "search_index": 1, "archive": True, "is_active": False}])
voir(refuse(lambda: ges.preparer_archivage_recherche(nouveau_ctx(), {"contact_search_key": "606202:0"}), "déjà archivée"),
     "une recherche déjà archivée : refusée")

print("8) LOT 3a : l'agenda DE LA PERSONNE, sans invitation")
from datetime import datetime, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

google = []  # chaque appel à Google (faux)


class FauxAdmin:
    def __init__(self, settings):
        pass

    def _garde(self, user, sujet, quoi):
        google.append({"quoi": quoi, "user": user.id, "sujet": sujet})
        if etat.get("google_refuse"):
            raise HTTPException(status_code=403, detail="Agenda Google non autorise pour cet utilisateur")
        return {"role": "commercial"}

    def assert_calendar_subject_allowed(self, user, sujet):
        return self._garde(user, sujet, "garde_agenda")

    def assert_gmail_subject_allowed(self, user, sujet):
        return self._garde(user, sujet, "garde_gmail")


class FauxGoogle:
    def __init__(self, settings):
        pass

    def list_calendar_events(self, **k):
        google.append({"quoi": "lister", **k})
        return {"ok": True, "events": etat.get("evenements", []), "hasMore": False}

    def check_calendar_availability(self, **k):
        google.append({"quoi": "dispo", **k})
        return {"ok": True, "busyCount": etat.get("occupe", 0)}

    def create_calendar_event(self, **k):
        google.append({"quoi": "creer", **k})
        return {"ok": True, "eventId": "g123", "htmlLink": "https://calendar", "event": {
            "start": {"dateTime": k["start_at"]}, "end": {"dateTime": k["end_at"]}}}

    def update_calendar_event(self, **k):
        google.append({"quoi": "modifier", **k})
        return {"ok": True}

    def delete_calendar_event(self, **k):
        google.append({"quoi": "supprimer", **k})
        return {"ok": True}

    def send_gmail_message(self, **k):
        google.append({"quoi": "envoyer", **k})
        return {"ok": True, "messageId": "m1"}


class FauxLiens:
    def __init__(self, settings):
        pass

    def create_link(self, **k):
        google.append({"quoi": "lien_creer", **k})
        return {"id": "b" * 8 + "-bbbb-bbbb-bbbb-" + "b" * 12}

    def update_link(self, **k):
        google.append({"quoi": "lien_modifier", **k})
        return {}

    def mark_deleted(self, **k):
        google.append({"quoi": "lien_supprimer", **k})
        return {}


class FauxRendu:
    def __init__(self, settings):
        pass

    def render_preview(self, **k):
        google.append({"quoi": "rendu", **k})
        return {"subject": "Des biens pour vous", "text": "Bonjour Monsieur,\nvotre conseiller : paul@gti-immobilier.fr\n"
                                                          "écrire à durand@exemple.fr"}


ges.SupabaseAdminService, ges.GoogleWorkspaceService = FauxAdmin, FauxGoogle
ges.GoogleCalendarEventLinkService, ges.RapprochementEmailService = FauxLiens, FauxRendu
Settings.google_workspace_domain = "gti-immobilier.fr"
_faux_avant = faux


def faux_lot3(methode, url, **kw):
    if methode == "GET" and url.endswith("/rest/v1/app_google_calendar_event_link"):
        appels.append({"methode": "GET", "chemin": "app_google_calendar_event_link", "entetes": dict(kw.get("headers") or {}),
                       "params": dict(kw.get("params") or {}), "corps": None})
        return Reponse(etat.get("liens", []))
    return _faux_avant(methode, url, **kw)


requests.get = lambda url, **kw: faux_lot3("GET", url, **kw)
requests.post = lambda url, **kw: faux_lot3("POST", url, **kw)
requests.patch = lambda url, **kw: faux_lot3("PATCH", url, **kw)
requests.request = lambda methode, url, **kw: faux_lot3(methode, url, **kw)

LIEN = "b" * 8 + "-bbbb-bbbb-bbbb-" + "b" * 12
reset(evenements=[
    {"id": "g1", "summary": "Visite 63289", "start": {"dateTime": "2026-11-20T10:00:00+01:00"},
     "end": {"dateTime": "2026-11-20T11:00:00+01:00"}, "location": "La Chaise-Dieu",
     "attendees": [{"email": EMAIL, "self": True}, {"email": "client@gmail.com"}, {"email": "pauline@gti-immobilier.fr"}]},
    {"id": "g2", "summary": "annulé", "status": "cancelled", "start": {"dateTime": "2026-11-20T12:00:00+01:00"},
     "end": {"dateTime": "2026-11-20T13:00:00+01:00"}},
    {"id": "g3", "summary": "Salon", "start": {"date": "2026-11-21"}, "end": {"date": "2026-11-22"}}],
    liens=[{"id": LIEN, "google_event_id": "g1", "event_type": "visite", "hektor_annonce_id": 63289, "hektor_contact_id": "606202"}])
google.clear()
r = ges.lire_mon_agenda(nouveau_ctx(), {"debut": "2026-11-20", "fin": "2026-11-21"})
lister = next(g for g in google if g["quoi"] == "lister")
voir(lister["subject_email"] == EMAIL and google[0]["quoi"] == "garde_agenda" and google[0]["sujet"] == EMAIL,
     "TOUJOURS l'agenda de la personne, derrière la garde de l'écran (compte Google relié)")
voir(r["nombre"] == 2 and [x["titre"] for x in r["rendez_vous"]] == ["Visite 63289", "Salon"],
     "un rendez-vous annulé est retiré ; une journée entière est gardée")
voir(r["rendez_vous"][0]["invites"] == 2 and r["rendez_vous"][0]["invites_exterieurs"] == 1 and r["rendez_vous"][0]["rdv_app"] == LIEN,
     "le nombre d'invités (et d'extérieurs), et le numéro du RDV posé par l'app")
texte = json.dumps(r, ensure_ascii=False)
voir(EMAIL not in texte and "client@gmail.com" not in texte and "pauline@" not in texte,
     "⛔ AUCUNE adresse ne part au modèle (ni la sienne, ni celles des invités)")
lien_lu = next(a for a in appels if a["chemin"] == "app_google_calendar_event_link")
voir(lien_lu["entetes"]["Authorization"] == "Bearer " + JETON, "les liens de l'app sont lus avec le JETON")
voir(refuse(lambda: ges.lire_mon_agenda(nouveau_ctx(), {"debut": "2026-11-01", "fin": "2026-12-31"}), "31 jours"),
     "plus de 31 jours à la fois : refusé")
reset(google_refuse=True)
voir(refuse(lambda: ges.lire_mon_agenda(nouveau_ctx(), {"debut": "", "fin": ""}), "pas ouvert"),
     "un agenda Google non relié : refusé en clair")

PARIS = ZoneInfo("Europe/Paris")
demain = (datetime.now(PARIS) + timedelta(days=2)).strftime("%Y-%m-%dT10:00")
reset(occupe=1)
google.clear()
resume, pr = ges.preparer_rdv(nouveau_ctx(), {"type": "visite", "titre": "Visite Maison — M. DURAND", "debut": demain,
                                              "duree_minutes": 60, "lieu": "", "hektor_annonce_id": "63289", "hektor_contact_id": "",
                                              "contact_search_key": "606202:0", "note": ""})
voir("TON agenda" in resume and "Aucune invitation" in resume and "M. DURAND" in resume and "« visite »" in resume,
     "la carte dit : ton agenda, aucune invitation, le contact, et le bien qui passe « visite »")
voir("déjà pris" in resume, "un créneau occupé est signalé sur la carte (sans bloquer)")
voir(not [g for g in google if g["quoi"] == "creer"] and not ecritures_metier(), "PROPOSER ne crée rien chez Google ni chez nous")
voir(pr["hektor_contact_id"] == "606202", "le contact est déduit de la recherche")
reset()
voir(refuse(lambda: ges.preparer_rdv(nouveau_ctx(), {"type": "visite", "titre": "V", "debut": demain, "duree_minutes": 60, "lieu": "",
                                                     "hektor_annonce_id": "", "hektor_contact_id": "", "contact_search_key": "606202:0",
                                                     "note": ""}), "numéro d'annonce"),
     "une visite liée à une recherche sans le bien : refusée")
voir(refuse(lambda: ges.preparer_rdv(nouveau_ctx(), {"type": "autre", "titre": "V", "debut": "2020-01-01T10:00", "duree_minutes": 60,
                                                     "lieu": "", "hektor_annonce_id": "", "hektor_contact_id": "",
                                                     "contact_search_key": "", "note": ""}), "passé"),
     "un créneau passé : refusé")
voir(refuse(lambda: ges.preparer_rdv(nouveau_ctx(), {"type": "autre", "titre": "V", "debut": "2026-11-20", "duree_minutes": 60,
                                                     "lieu": "", "hektor_annonce_id": "", "hektor_contact_id": "",
                                                     "contact_search_key": "", "note": ""}), "l'heure"),
     "une date sans heure : refusée")
reset()
google.clear()
appels.clear()
res = ges.executer_rdv(nouveau_ctx(), pr)
creer = next(g for g in google if g["quoi"] == "creer")
voir(creer["subject_email"] == EMAIL and creer["attendees"] == [] and creer["send_updates"] == "none" and creer["dry_run"] is False,
     "au CLIC : dans SON agenda, AUCUN invité, AUCUNE notification (sendUpdates none)")
lien = next(g for g in google if g["quoi"] == "lien_creer")
voir(lien["calendar_email"] == EMAIL and lien["event_type"] == "visite" and lien["app_dossier_id"] == 77
     and lien["metadata_json"]["source"] == "assistant" and lien["metadata_json"]["contact_search_key"] == "606202:0",
     "le RDV est relié à l'app comme à l'écran (bien, contact, recherche), marqué « assistant »")
statut = next(a for a in appels if a["chemin"] == "rpc/app_set_bien_statut")
voir(statut["corps"]["p_status"] == "visite" and statut["entetes"]["Authorization"] == "Bearer " + JETON and res["statut_visite"] is True,
     "une visite met le bien « visite » pour la recherche, avec le jeton (= onCreated de l'écran)")
voir(res["rdv_app"] == LIEN and EMAIL not in json.dumps(res), "le résultat donne le numéro du RDV, jamais l'adresse")

reset(liens=[{"id": LIEN, "google_calendar_email": "pauline@gti-immobilier.fr", "google_event_id": "g1", "event_type": "visite",
              "summary": "V", "location": None, "starts_at": "2026-11-20T09:00:00+00:00", "ends_at": "2026-11-20T10:00:00+00:00",
              "attendees_json": [], "status": "active", "metadata_json": {}}])
voir(refuse(lambda: ges.preparer_supprimer_rdv(nouveau_ctx(), {"rdv_id": LIEN}), "collègue"),
     "le RDV d'un collègue (même visible par la direction) : refusé")
UN_RDV = {"id": LIEN, "google_calendar_email": EMAIL, "google_event_id": "g1", "event_type": "visite", "summary": "Visite 63289",
          "location": None, "starts_at": "2099-11-20T09:00:00+00:00", "ends_at": "2099-11-20T10:00:00+00:00", "attendees_json": [],
          "status": "active", "metadata_json": {"contact_search_key": "606202:0"}}
reset(liens=[{**UN_RDV, "attendees_json": ["client@gmail.com"]}])
voir(refuse(lambda: ges.preparer_deplacer_rdv(nouveau_ctx(), {"rdv_id": LIEN, "debut": "2099-11-21T10:00", "duree_minutes": 0,
                                                              "titre": "", "lieu": ""}), "invités"),
     "un RDV avec des invités : refusé (le changer les toucherait sans les prévenir)")
reset(liens=[{**UN_RDV, "status": "deleted"}])
voir(refuse(lambda: ges.preparer_supprimer_rdv(nouveau_ctx(), {"rdv_id": LIEN}), "déjà été supprimé"), "un RDV déjà supprimé : refusé")
voir(refuse(lambda: ges.preparer_supprimer_rdv(nouveau_ctx(), {"rdv_id": "pas-un-numero"}), "rdv_app"), "un numéro illisible : refusé")
reset(liens=[dict(UN_RDV)])
resume, pd = ges.preparer_deplacer_rdv(nouveau_ctx(), {"rdv_id": LIEN, "debut": "2099-11-21T10:00", "duree_minutes": 0, "titre": "",
                                                       "lieu": ""})
voir("→" in resume and "11:00" in resume and "Personne n'est prévenu" in resume,
     "déplacer : avant → après, la durée gardée (1 h), personne n'est prévenu")
google.clear()
ges.executer_deplacer_rdv(nouveau_ctx(), pd)
modif = next(g for g in google if g["quoi"] == "modifier")
voir(modif["send_updates"] == "none" and modif["attendees"] is None and modif["subject_email"] == EMAIL
     and any(g["quoi"] == "lien_modifier" for g in google), "au clic : Google modifié sans notification, et notre copie suivie")
voir(refuse(lambda: ges.preparer_deplacer_rdv(nouveau_ctx(), {"rdv_id": LIEN, "debut": "", "duree_minutes": 0, "titre": "",
                                                              "lieu": ""}), "Rien ne change"), "rien ne change : pas de carte")
resume, ps = ges.preparer_supprimer_rdv(nouveau_ctx(), {"rdv_id": LIEN})
voir("reste « visite »" in resume, "supprimer une visite : la carte dit que le bien n'est PAS remis à « jamais vu »")
google.clear()
appels.clear()
ges.executer_supprimer_rdv(nouveau_ctx(), ps)
voir(next(g for g in google if g["quoi"] == "supprimer")["send_updates"] == "none" and any(g["quoi"] == "lien_supprimer" for g in google)
     and not [a for a in appels if a["chemin"] == "rpc/app_set_bien_statut"],
     "au clic : supprimé sans notification, lien marqué supprimé, et le statut du bien NON touché (défaut n° 3 évité)")
reset(liens=[{**UN_RDV, "attendees_json": ["client@gmail.com"]}])
google.clear()
voir(refuse(lambda: ges.executer_supprimer_rdv(nouveau_ctx(), ps), "invités") and not [g for g in google if g["quoi"] == "supprimer"],
     "TÉMOIN : un invité ajouté depuis l'écran entre la carte et le clic -> refusé au clic, rien supprimé")

print("9) LOT 3b : les e-mails EN INTERNE seulement, et l'aperçu du rapprochement")
reset()
voir(refuse(lambda: ges.preparer_email_interne(nouveau_ctx(), {"destinataires": "client@gmail.com", "objet": "o", "texte": "t"}),
            "EN INTERNE"), "un destinataire hors du domaine : refusé")
voir(refuse(lambda: ges.preparer_email_interne(nouveau_ctx(), {"destinataires": "pauline@gti-immobilier.fr|x@gti-immobilier.fr.pirate.com",
                                                               "objet": "o", "texte": "t"}), "EN INTERNE"),
     "un faux domaine glissé parmi des vrais : refusé")
voir(refuse(lambda: ges.preparer_email_interne(nouveau_ctx(), {"destinataires": "pauline@gti-immobilier.fr", "objet": "o",
                                                               "texte": "x" * 3001}), "3000"), "un texte trop long (la carte doit tout montrer) : refusé")
google.clear()
resume, pm = ges.preparer_email_interne(nouveau_ctx(), {"destinataires": "Pauline@gti-immobilier.fr ; julien@gti-immobilier.fr",
                                                        "objet": "Visite jeudi", "texte": "Bonjour,\nje fais la visite jeudi.\nPaul"})
voir(pm["destinataires"] == ["pauline@gti-immobilier.fr", "julien@gti-immobilier.fr"] and "je fais la visite jeudi" in resume,
     "la carte montre les destinataires ET le texte entier")
voir(not [g for g in google if g["quoi"] == "envoyer"], "PROPOSER n'envoie rien")
google.clear()
ges.executer_email_interne(nouveau_ctx(), pm)
envoi = next(g for g in google if g["quoi"] == "envoyer")
voir(envoi["subject_email"] == EMAIL and envoi["to"] == pm["destinataires"] and not envoi["attachments"] and envoi["dry_run"] is False
     and google[0]["quoi"] == "garde_gmail", "au clic : depuis SA boîte (garde de l'écran), sans pièce jointe")
google.clear()
voir(refuse(lambda: ges.executer_email_interne(nouveau_ctx(), {**pm, "destinataires": ["client@gmail.com"]}), "EN INTERNE")
     and not [g for g in google if g["quoi"] == "envoyer"], "TÉMOIN : une carte trafiquée vers l'extérieur est refusée AU CLIC")
reset()
google.clear()
appels.clear()
r = ges.apercu_rapprochement(nouveau_ctx(), {"contact_search_key": "606202:0", "annonces": "63289", "mot": ""})
voir(r["rien_n_est_parti"] and not [g for g in google if g["quoi"] == "envoyer"] and not ecritures_metier(),
     "l'aperçu n'envoie rien et n'écrit rien")
voir("@" not in r["texte"] and "[adresse]" in r["texte"], "⛔ aucune adresse e-mail dans l'aperçu (ni la sienne, ni celle du client)")
voir(next(a for a in appels if a["chemin"] == "app_dossiers_current")["entetes"]["Authorization"] == "Bearer " + JETON,
     "chaque bien est lu avec le JETON avant le rendu")
reset(bien=[])
voir(refuse(lambda: ges.apercu_rapprochement(nouveau_ctx(), {"contact_search_key": "606202:0", "annonces": "63289", "mot": ""}),
            "biens vivants"), "un bien invisible : pas d'aperçu")

print("10) aucune fonction de geste ne fait autre chose que proposer")
voir(all(f.nom.startswith("proposer_") for f in ges.FONCTIONS_GESTES) and len(ges.FONCTIONS_GESTES) == 14,
     "14 gestes, tous « proposer_ » : le modèle n'a AUCUNE fonction qui exécute")
voir(not any(f.nom.startswith("proposer_") for f in ges.FONCTIONS_LECTURE_LOT3), "les 2 lectures du lot 3 ne proposent rien")
voir([f.nom for f in cat.fonctions_du_role("commercial") if f.nom == "proposer_note_transaction"] == [],
     "un commercial n'a PAS la note de transaction (double verrou : non proposée, et refusée au clic)")

print(f"\n{ok} contrôles verts")
