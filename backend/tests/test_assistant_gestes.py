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
                                                          "écrire à durand@exemple.fr\n[Voir ce bien](https://gti-backend"
                                                          ".onrender.com/espace/eyJhIjoiZXNwYyJ9.cle_secrete)"}


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
voir("cle_secrete" not in r["texte"] and "/espace/" not in r["texte"] and "[Voir ce bien]([lien])" in r["texte"],
     "⛔ aucun LIEN non plus : ils portent une clé d'accès à l'espace du client (trouvé en réel le 13/11)")
voir(next(a for a in appels if a["chemin"] == "app_dossiers_current")["entetes"]["Authorization"] == "Bearer " + JETON,
     "chaque bien est lu avec le JETON avant le rendu")
reset(bien=[])
voir(refuse(lambda: ges.apercu_rapprochement(nouveau_ctx(), {"contact_search_key": "606202:0", "annonces": "63289", "mot": ""}),
            "biens vivants"), "un bien invisible : pas d'aperçu")

reset()
resume, pm = ges.preparer_email_interne(nouveau_ctx(), {"destinataires": "moi", "objet": "Récap", "texte": "Mes visites."})
voir(pm["destinataires"] == ["moi"] and "à toi" in resume and EMAIL not in resume,
     "« moi » : la carte dit « toi », et SON adresse ne part pas au modèle (règle de l'étape 1)")
google.clear()
ges.executer_email_interne(nouveau_ctx(), pm)
voir(next(g for g in google if g["quoi"] == "envoyer")["to"] == [EMAIL], "au clic, « moi » devient SON adresse, posée par le serveur")

print("9bis) LOT 4a : le bien -- champs en liste fermée, rédacteur, photos, brouillon")
import types  # noqa: E402

pont, redac = [], []  # chaque appel au pont Hektor et au rédacteur (faux)


class FauxAdmin4(FauxAdmin):
    def assert_can_apply_portals(self, user, authorization, app_dossier_id):
        pont.append({"quoi": "garde", "user": user.id, "auth": authorization, "dossier": app_dossier_id})
        if etat.get("portail_refuse"):
            raise HTTPException(status_code=403, detail="Annonce pas encore diffusable")
        return {"role": "commercial"}, False

    def insert_agent_run(self, row):
        redac.append({"quoi": "trace", **row})
        return 1


class FauxPont:
    def __init__(self, settings):
        pass

    def _load_agency_targets(self, agence):
        pont.append({"quoi": "agence", "agence": agence})
        return [{"portal_key": "bienicidirect", "hektor_broadcast_id": "77"}, {"portal_key": "leboncoinDirect", "hektor_broadcast_id": "78"}]

    def apply(self, app_dossier_id, dry_run, ensure_diffusable, requested_by=None):
        pont.append({"quoi": "apply", "dossier": app_dossier_id, "dry_run": dry_run, "ensure": ensure_diffusable})
        return {"failed": etat.get("apply_echecs", [])}

    def persist_state(self, app_dossier_id, **k):
        pont.append({"quoi": "report", "dossier": app_dossier_id, **k})
        return {}


class FauxRedacteur:
    def __init__(self, settings):
        pass

    def generate(self, faits, photo_urls=None, custom_intro=None):
        redac.append({"quoi": "generer", "faits": faits, "photos": photo_urls, "consigne": custom_intro})
        return {"title": "Maison de caractère", "accroche": "Au calme.", "description": "Belle maison.",
                "highlights": ["Jardin", "Garage"], "model": "m", "usage": {"input_tokens": 1, "output_tokens": 2}}


ges.SupabaseAdminService = FauxAdmin4
sys.modules["app.services.hektor_bridge"] = types.SimpleNamespace(HektorBridgeService=FauxPont)
sys.modules["app.services.openai_listing_writer_service"] = types.SimpleNamespace(OpenAIListingWriterService=FauxRedacteur)
_faux_lot3 = faux_lot3


def faux_lot4(methode, url, **kw):
    chemin = url.split("/rest/v1/", 1)[1]
    enregistrer = lambda: appels.append({"methode": methode, "chemin": chemin, "entetes": dict(kw.get("headers") or {}),  # noqa: E731
                                         "params": dict(kw.get("params") or {}), "corps": kw.get("json")})
    if methode == "GET" and chemin in {"app_brouillon_annonce_index_current", "app_dossier_detail_current", "app_console_photo"}:
        enregistrer()
        if chemin == "app_dossier_detail_current":
            return Reponse([{"detail_payload_json": json.dumps(etat.get("fiche", {}))}])
        return Reponse(etat.get({"app_brouillon_annonce_index_current": "brouillons", "app_console_photo": "photos"}[chemin], []))
    if methode == "POST" and chemin in {"rpc/app_edit_annonce_optimistic", "rpc/app_console_photo_couverture_optimistic",
                                        "rpc/app_console_photo_visibilite_optimistic", "rpc/app_console_photos_reordonner_optimistic"}:
        enregistrer()
        return Reponse(etat.get("rep_rpc", {"ok": True, "job_id": "j1"}))
    if chemin in {"app_console_job", "app_diffusion_target"} and methode in {"POST", "DELETE"}:
        enregistrer()
        return Reponse([{"id": "job1"}]) if methode == "POST" else Reponse(None, status=204)
    return _faux_lot3(methode, url, **kw)


requests.get = lambda url, **kw: faux_lot4("GET", url, **kw)
requests.post = lambda url, **kw: faux_lot4("POST", url, **kw)
requests.patch = lambda url, **kw: faux_lot4("PATCH", url, **kw)
requests.request = lambda methode, url, **kw: faux_lot4(methode, url, **kw)

VIDE = {cle: "" for cle in ges.CHAMPS_BIEN}
reset(fiche={"texte_principal_titre": "Maison ancienne", "nb_pieces": "4", "app_optimistic_overlay": {"NB_CHAMBRES": "3"}})
resume, pm = ges.preparer_modifier_bien(nouveau_ctx(), {**VIDE, "hektor_annonce_id": 63289, "title": "Maison de caractère",
                                                        "roomCount": "5", "bedroomCount": "4"})
voir(pm["champs"] == {"title": "Maison de caractère", "roomCount": "5", "bedroomCount": "4"},
     "seuls les champs donnés partent (vide = inchangé)")
voir("« Maison ancienne » → « Maison de caractère »" in resume and "« 4 » → « 5 »" in resume and "« 3 » → « 4 »" in resume,
     "la carte montre l'AVANT (calque de l'app d'abord, puis la fiche) et l'APRÈS")
voir(not ecritures_metier(), "PROPOSER n'écrit rien")
voir(refuse(lambda: ges.preparer_modifier_bien(nouveau_ctx(), {**VIDE, "hektor_annonce_id": 63289, "price": "99000"}), "prix"),
     "⛔ le PRIX n'est pas dans la liste : rien à modifier, et la phrase renvoie à la demande de baisse")
voir(refuse(lambda: ges.preparer_modifier_bien(nouveau_ctx(), {**VIDE, "hektor_annonce_id": 63289, "roomCount": "cinq"}), "entier"),
     "un nombre de pièces en lettres : refusé")
voir(refuse(lambda: ges.preparer_modifier_bien(nouveau_ctx(), {**VIDE, "hektor_annonce_id": 63289, "constructionYear": "3000"}), "année"),
     "une année impossible : refusée")
voir(ges.preparer_modifier_bien(nouveau_ctx(), {**VIDE, "hektor_annonce_id": 63289, "surface": "92,5"})[1]["champs"] == {"surface": "92.5"},
     "une surface à virgule devient un nombre à point")
reset(bien=[], brouillons=[{"hektor_annonce_id": 63500}])
voir(refuse(lambda: ges.preparer_modifier_bien(nouveau_ctx(), {**VIDE, "hektor_annonce_id": 63500, "title": "x"}), "BROUILLON"),
     "⛔ un brouillon ne se modifie pas : la phrase dit de l'activer (décision ⑦-10 ③)")
reset()
appels.clear()
ges.executer_modifier_bien(nouveau_ctx(), pm)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_edit_annonce_optimistic")
voir(rpc["entetes"]["Authorization"] == "Bearer " + JETON and rpc["corps"] == {"target_dossier_id": 77, "edit_fields": pm["champs"],
                                                                              "debounce_seconds": 600},
     "au clic : la fonction de l'écran, avec SON jeton, 10 min avant Hektor")
voir(refuse(lambda: ges.executer_modifier_bien(nouveau_ctx(), {"hektor_annonce_id": 63289, "champs": {"price": "1"}}), "aucun champ"),
     "TÉMOIN : une carte trafiquée avec le prix est refusée AU CLIC")

redac.clear()
appels.clear()
reset(fiche={"surface_habitable_detail": "120", "nb_pieces": "5"})
r = ges.rediger_annonce(nouveau_ctx(), {"hektor_annonce_id": 63289, "consigne": "le jardin"})
gen = next(x for x in redac if x["quoi"] == "generer")
voir(r["rien_n_est_ecrit"] and r["titre"] == "Maison de caractère" and "Points forts :\n- Jardin" in r["texte"]
     and r["texte"].startswith("Au calme."), "le rédacteur PROPOSE titre + texte, assemblés comme l'écran (accroche, texte, points forts)")
voir(not ecritures_metier() and gen["consigne"] == "le jardin" and gen["photos"] == [] and gen["faits"]["surface"] == "120",
     "rien n'est écrit sur l'annonce ; les faits viennent de la fiche, sans photo")
voir("@" not in json.dumps(gen["faits"]), "⛔ aucune adresse e-mail dans ce qui part au rédacteur")
voir(any(x["quoi"] == "trace" and x["agent_key"] == "redacteur" for x in redac), "la même trace que l'écran (app_agent_run)")

PHOTOS = [{"hektor_photo_id": "A", "visible": True, "sort_order": 1}, {"hektor_photo_id": "B", "visible": True, "sort_order": 2},
          {"hektor_photo_id": "C", "visible": True, "sort_order": 3}, {"hektor_photo_id": "D", "visible": False, "sort_order": 4}]
reset(photos=[dict(x) for x in PHOTOS])
r = ges.lire_photos_bien(nouveau_ctx(), {"hektor_annonce_id": 63289})
voir([(x["photo"], x["rang"], x["couverture"]) for x in r["photos"]] == [("A", 1, True), ("B", 2, False), ("C", 3, False), ("D", None, False)]
     and r["masquees"] == 1, "la galerie : rang des visibles, la 1re est la couverture, la masquée sans rang")
voir(next(a for a in appels if a["chemin"] == "app_console_photo")["params"]["present_in_hektor"] == "is.true",
     "seulement les photos encore chez Hektor (comme l'écran)")
voir(refuse(lambda: ges.preparer_couverture(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "A"}), "déjà"), "déjà en couverture : refusé")
voir(refuse(lambda: ges.preparer_couverture(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "D"}), "masquée"), "une masquée en couverture : refusé")
voir(refuse(lambda: ges.preparer_couverture(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "Z"}), "pas sur cette annonce"),
     "une photo d'une autre annonce : refusée")
appels.clear()
ges.executer_couverture(nouveau_ctx(), ges.preparer_couverture(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "B"})[1])
rpc = next(a for a in appels if a["chemin"] == "rpc/app_console_photo_couverture_optimistic")
voir(rpc["corps"] == {"p_app_dossier_id": 77, "p_hektor_annonce_id": "63289", "p_hektor_photo_id": "B"}
     and rpc["entetes"]["Authorization"] == "Bearer " + JETON, "couverture : la fonction de l'écran, avec SON jeton")
reset(photos=[dict(PHOTOS[0]), dict(PHOTOS[3])])
voir(refuse(lambda: ges.preparer_visibilite_photo(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "A", "visible": False}), "dernière"),
     "⛔ masquer la DERNIÈRE photo visible : refusé")
_, pv = ges.preparer_visibilite_photo(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "D", "visible": True})
reset(photos=[dict(x) for x in PHOTOS])
_, pm_ = ges.preparer_visibilite_photo(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "A", "visible": False})
reset(photos=[dict(PHOTOS[0]), dict(PHOTOS[3])])
appels.clear()
voir(refuse(lambda: ges.executer_visibilite_photo(nouveau_ctx(), pm_), "dernière")
     and not [a for a in appels if a["chemin"].startswith("rpc/")], "TÉMOIN : devenue la dernière entre la carte et le clic -> refusé AU CLIC")
appels.clear()
ges.executer_visibilite_photo(nouveau_ctx(), pv)
voir(next(a for a in appels if a["chemin"] == "rpc/app_console_photo_visibilite_optimistic")["corps"]["p_visible"] is True,
     "afficher : la fonction de l'écran")
reset(photos=[dict(x) for x in PHOTOS])
resume, pd = ges.preparer_deplacer_photo(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "C", "rang": 1})
voir("COUVERTURE" in resume, "placer au rang 1 : la carte prévient qu'elle devient la couverture")
voir(refuse(lambda: ges.preparer_deplacer_photo(nouveau_ctx(), {"hektor_annonce_id": 63289, "photo": "C", "rang": 4}), "entre 1 et 3"),
     "un rang au-delà des visibles : refusé")
appels.clear()
ges.executer_deplacer_photo(nouveau_ctx(), pd)
voir(next(a for a in appels if a["chemin"] == "rpc/app_console_photos_reordonner_optimistic")["corps"]["p_ordre"] == ["C", "A", "B"],
     "au clic : l'ordre COMPLET des visibles, relu au clic (la fonction l'exige)")
reset(photos=[dict(x) for x in PHOTOS], rep_rpc={"ok": False, "erreur": "droits_insuffisants"})
voir(refuse(lambda: ges.executer_deplacer_photo(nouveau_ctx(), pd), "droits"), "un refus de la base (ok = false) devient un refus, jamais un succès")

voir("activer_brouillon" not in ges.GESTES and not hasattr(ges, "preparer_activer_brouillon")
     and not any("exit_hektor_draft_annonce" in str(g) for g in ges.GESTES.values()),
     "⛔ activer un brouillon : RETIRÉ de l'assistant le 15/11 (décision « B ») -- aucune carte ne peut le proposer")

print("9ter) LOT 4b : UN portail, sur un bien diffusable -- le geste de la case de la vue Publicité")
BIEN_DIF = {**BIEN, "agence_nom": "Firminy", "diffusable": "1", "portails_resume": "leboncoinDirect", "nb_portails_actifs": 1}
reset(bien=[dict(BIEN_DIF)])
r = ges.lire_portails_bien(nouveau_ctx(), {"hektor_annonce_id": 63289})
voir(r["diffusable"] and [x["portail"] for x in r["portails"] if x["en_ligne"]] == ["leboncoinDirect"] and len(r["portails"]) == 5,
     "les 5 portails de la vue Publicité, et ce qui est en ligne")
voir(refuse(lambda: ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "portail": "leboncoinDirect", "publier": True}),
            "déjà en ligne"), "publier un portail déjà en ligne : refusé")
reset(bien=[{**BIEN_DIF, "diffusable": "0"}])
voir(refuse(lambda: ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "portail": "paper", "publier": True}),
            "pas encore diffusable"), "⛔ un bien pas diffusable : refusé (c'est la direction)")
reset(bien=[dict(BIEN_DIF)])
resume, pp = ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "portail": "bienicidirect", "publier": True})
voir("Bien'ici" in resume and "ne bougent pas" in resume and not ecritures_metier() and not pont,
     "la carte dit le portail, et que les autres ne bougent pas ; rien d'écrit, Hektor pas appelé")
appels.clear()
pont.clear()
ges.executer_portail(nouveau_ctx(), pp)
voir(pont[0]["quoi"] == "garde" and pont[0]["auth"] == "Bearer " + JETON and pont[0]["dossier"] == 77,
     "au clic : la garde de la route /apply, jugée avec SON jeton, AVANT toute écriture")
cibles = [a for a in appels if a["chemin"] == "app_diffusion_target"]
voir([a["methode"] for a in cibles] == ["DELETE", "POST"] and len(cibles[1]["corps"]) == 1
     and cibles[1]["corps"][0]["hektor_broadcast_id"] == "77" and cibles[1]["corps"][0]["target_state"] == "enabled"
     and all(a["entetes"]["Authorization"] == "Bearer " + JETON for a in cibles),
     "⭐ UNE SEULE cible enregistrée (comme la case de la vue Publicité), numéro de passerelle de l'agence")
app = next(x for x in pont if x["quoi"] == "apply")
voir(app["dry_run"] is False and app["ensure"] is False, "⛔ l'envoi ne touche JAMAIS « diffusable »")
voir(next(x for x in pont if x["quoi"] == "report")["portails_resume"] == "leboncoinDirect, bienicidirect",
     "Hektor a confirmé : le résumé est reporté (Leboncoin reste, Bien'ici s'ajoute)")
pont.clear()
appels.clear()
_, pp2 = ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "portail": "paper", "publier": True})
ges.executer_portail(nouveau_ctx(), pp2)
voir(not [x for x in pont if x["quoi"] == "agence"]
     and next(a for a in appels if a["methode"] == "POST" and a["chemin"] == "app_diffusion_target")["corps"][0]["hektor_broadcast_id"] == "20",
     "Paper : le numéro commun à toutes les agences (20), sans lire l'agence")
reset(bien=[dict(BIEN_DIF)], portail_refuse=True)
pont.clear()
appels.clear()
voir(refuse(lambda: ges.executer_portail(nouveau_ctx(), pp), "refusé") and not [a for a in appels if a["chemin"] == "app_diffusion_target"]
     and not [x for x in pont if x["quoi"] == "apply"], "TÉMOIN : la garde refuse -> aucune écriture, rien envoyé")
reset(bien=[dict(BIEN_DIF)], apply_echecs=[{"action": "add", "error": "passerelle fermée"}])
pont.clear()
voir(refuse(lambda: ges.executer_portail(nouveau_ctx(), pp), "passerelle fermée") and not [x for x in pont if x["quoi"] == "report"],
     "Hektor refuse : on le DIT, et le résumé n'est pas reporté")

print("9ter-bis) 17/11 (§44-45) : PLUSIEURS portails d'un coup, sur un bien DÉJÀ diffusable -- la fenêtre « Diffusion »")
reset(bien=[{**BIEN_DIF, "portails_resume": "leboncoinDirect, bienicidirect"}])
pont.clear()
resume_m, pm = ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "publier": "Paper | bienici", "retirer": "le bon coin"})
voir("PUBLIER sur Paper" in resume_m and "RETIRER de Leboncoin" in resume_m
     and "en ligne : Leboncoin, Bien'ici → Bien'ici, Paper" in resume_m and "déjà dans l'état voulu : Bien'ici" in resume_m
     and pm == {"hektor_annonce_id": 63289, "choix": {"paper": True, "leboncoinDirect": False}}
     and not ecritures_metier() and not pont,
     "une liste : les noms reconnus (« bienici », « le bon coin »), l'avant -> après, ce qui est déjà en place est écarté ; rien d'écrit")
voir(refuse(lambda: ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "publier": "Paper", "retirer": "paper"}), "ET à retirer")
     and refuse(lambda: ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "publier": "SeLoger", "retirer": ""}), "n'est pas un portail")
     and refuse(lambda: ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "publier": "", "retirer": ""}), "au moins un portail")
     and refuse(lambda: ges.preparer_portail(nouveau_ctx(), {"hektor_annonce_id": 63289, "publier": "leboncoin|bienici", "retirer": ""}), "Rien ne change"),
     "⛔ le même portail des deux côtés, un portail inconnu, rien de nommé, rien qui change : refusés")
appels.clear()
pont.clear()
r_m = ges.executer_portail(nouveau_ctx(), pm)
cibles = [a for a in appels if a["chemin"] == "app_diffusion_target"]
poses = {c["portal_key"]: (c["hektor_broadcast_id"], c["target_state"]) for c in cibles[1]["corps"]} if len(cibles) == 2 else {}
voir([a["methode"] for a in cibles] == ["DELETE", "POST"] and poses == {"paper": ("20", "enabled"), "leboncoinDirect": ("78", "disabled")}
     and [x["quoi"] for x in pont].count("apply") == 1 and [x["quoi"] for x in pont].count("agence") == 1,
     "au CLIC : les SEULS portails nommés enregistrés (Paper numéro commun, Leboncoin numéro de l'agence lu UNE fois), UN SEUL envoi")
voir(next(x for x in pont if x["quoi"] == "apply")["ensure"] is False
     and next(x for x in pont if x["quoi"] == "report")["portails_resume"] == "bienicidirect, paper"
     and r_m["en_ligne_apres"] == ["bienicidirect", "paper"],
     "⛔ jamais « diffusable » au passage ; le résumé reporté : Bien'ici reste, Leboncoin sort, Paper entre")
reset(bien=[{**BIEN_DIF, "portails_resume": "leboncoinDirect, bienicidirect"}],
      apply_echecs=[{"action": "add", "portal_key": "paper", "error": "passerelle fermée"}])
pont.clear()
voir(refuse(lambda: ges.executer_portail(nouveau_ctx(), pm), "Paper (passerelle fermée)")
     and not [x for x in pont if x["quoi"] == "report"],
     "un refus de Hektor est dit PORTAIL PAR PORTAIL, et rien n'est reporté (la nuit remettra l'app d'accord)")
reset(bien=[{**BIEN_DIF, "diffusable": "0"}])
appels.clear()
pont.clear()
voir(refuse(lambda: ges.executer_portail(nouveau_ctx("admin"), pm), "pas encore diffusable")
     and not [a for a in appels if a["chemin"] == "app_diffusion_target"] and not pont,
     "⛔ TÉMOIN : le bien n'est plus diffusable au clic -> refusé MÊME pour l'admin (sa règle), rien d'écrit, Hektor pas appelé")
reset(bien=[dict(BIEN_DIF)])

print("9quater) LOT 2c : créer un contact, ajouter / modifier une recherche -- les fonctions de l'écran")
_faux_lot4 = faux_lot4
COMMUNES_API = {"42700": ["Firminy"], "43000": ["Le Puy-en-Velay", "Aiguilhe", "Espaly-Saint-Marcel"]}


def faux_lot2c(methode, url, **kw):
    if "geo.api.gouv.fr" in url:
        appels.append({"methode": methode, "chemin": "geo", "params": dict(kw.get("params") or {}), "entetes": {}, "corps": None})
        if etat.get("geo_panne"):
            raise requests.ConnectionError("injoignable")
        return Reponse([{"nom": n} for n in COMMUNES_API.get(kw["params"]["codePostal"], [])])
    chemin = url.split("/rest/v1/", 1)[1]
    if methode == "GET" and chemin == "app_contacts_current" and "or" in (kw.get("params") or {}):
        appels.append({"methode": methode, "chemin": "doublons", "params": dict(kw["params"]), "entetes": dict(kw.get("headers") or {}),
                       "corps": None})
        return Reponse(etat.get("doublons", []))
    if methode == "POST" and chemin in {"rpc/app_create_contact_optimistic", "rpc/app_create_search_optimistic",
                                        "rpc/app_edit_search_optimistic"}:
        appels.append({"methode": methode, "chemin": chemin, "entetes": dict(kw.get("headers") or {}), "params": {},
                       "corps": kw.get("json")})
        return Reponse({"ok": True} if "edit" in chemin else {"id": "job-2c", "status": "pending"})
    return _faux_lot4(methode, url, **kw)


requests.get = lambda url, **kw: faux_lot2c("GET", url, **kw)
requests.post = lambda url, **kw: faux_lot2c("POST", url, **kw)
requests.patch = lambda url, **kw: faux_lot2c("PATCH", url, **kw)
requests.request = lambda methode, url, **kw: faux_lot2c(methode, url, **kw)

VIDE_C = {cle: "" for cle in ges.GESTES["creer_contact"].parametres["properties"]}
NOUVEAU = {**VIDE_C, "genre": "acquereur", "civilite": "M.", "nom": "Essai", "prenom": "Jean", "telephone": "06 11 22 33 44",
           "email": "", "code_postal": "42700", "ville": "firminy", "email_rgpd": False, "doublon_accepte": False,
           "avec_recherche": True, "types": "Maison|appartement", "communes": "42700 Firminy|43000 le puy en velay",
           "budget_min": "150000", "budget_max": "250 000 €", "pieces_min": "4"}
reset(doublons=[])
resume, pc = ges.preparer_creer_contact(nouveau_ctx(), NOUVEAU)
contact = pc["contact"]
voir(not ecritures_metier() and "M. Jean ESSAI, acquéreur" in resume and "à ton nom" in resume and "sans e-mail RGPD" in resume,
     "PROPOSER n'écrit rien ; la carte dit qui, le genre, à qui il appartiendra, et l'e-mail RGPD")
voir(contact["phone"] == "0611223344" and contact["city"] == "Firminy" and contact["postal_code"] == "42700"
     and contact["contact_kind"] == "acquereur" and contact["person_type"] == "personne_seule" and contact["civilite"] == "M.",
     "la fiche dans la forme de l'écran : téléphone nettoyé, commune ÉCRITE COMME HEKTOR LA CONNAÎT (firminy → Firminy)")
suite = contact["contact_next_step"]
voir(suite["propertyTypeIds"] == ["1", "2"] and suite["priceMax"] == "250000" and suite["priceMin"] == "150000"
     and suite["roomsMin"] == "4" and suite["localities"] == [{"city": "Firminy", "postalCode": "42700"},
                                                             {"city": "Le Puy-en-Velay", "postalCode": "43000"}],
     "sa recherche suit, dans la forme de l'écran (types en codes, communes vérifiées, budget en chiffres)")
voir("hektor_user_email" not in contact, "⛔ le compte qui portera le contact n'est PAS dans la carte : posé au clic par le serveur")
doublon_appel = next(a for a in appels if a["chemin"] == "doublons")
voir(doublon_appel["params"]["or"] == '(phone_primary.eq."0611223344",phone_secondary.eq."0611223344")'
     and doublon_appel["entetes"]["Authorization"] == "Bearer " + JETON, "les doublons cherchés comme l'écran (même téléphone), avec SON jeton")

reset(doublons=[{"hektor_contact_id": "601", "display_name": "M. ESSAI Jean", "archive": False}])
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), NOUVEAU), "déjà présente"), "⛔ un doublon trouvé : pas de carte, il est montré")
resume, pd2 = ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "doublon_accepte": True})
voir("doublon possible, accepté : M. ESSAI Jean (n° 601)" in resume and pd2["doublon_accepte"],
     "redemandé avec l'accord : la carte garde le doublon sous les yeux (« Continuer malgré doublon » de l'écran)")
reset(doublons=[])
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "communes": "42700 Saint-Étienne"}), "Firminy"),
     "⛔ une commune qui n'est pas du code postal : refusée, avec les communes du code postal (sinon Hektor perd la ville)")
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "code_postal": "", "ville": "", "adresse": "3 rue Haute"}),
            "perdue"), "une adresse sans code postal ni ville : refusée")
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "telephone": "", "email": ""}), "téléphone ou un e-mail"),
     "ni téléphone ni e-mail : refusé (comme l'écran)")
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "genre": "proprietaire"}), "acquéreur"),
     "une recherche sur un propriétaire : refusée")
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "genre": "partenaire"}), "partenaires"),
     "⛔ un partenaire : refusé (le catalogue des métiers, décision du 06/11)")
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "budget_max": ""}), "budget maximum"),
     "une recherche sans budget maximum : refusée (comme l'écran)")
voir(refuse(lambda: ges.preparer_creer_contact(nouveau_ctx(), {**NOUVEAU, "types": "Yourte"}), "Type de bien inconnu"),
     "un type de bien inconnu : refusé, avec la liste")
reset(doublons=[], geo_panne=True)
resume, _ = ges.preparer_creer_contact(nouveau_ctx(), NOUVEAU)
voir("commune non vérifiée" in resume, "service des communes en panne : on ne bloque pas (l'écran non plus), la carte le DIT")

reset(doublons=[])
appels.clear()
r = ges.executer_creer_contact(nouveau_ctx(), {**pc, "contact": {**pc["contact"], "hektor_user_email": "autre@gti-immobilier.fr"}})
rpc = next(a for a in appels if a["chemin"] == "rpc/app_create_contact_optimistic")
voir(rpc["entetes"]["Authorization"] == "Bearer " + JETON and rpc["corps"]["job_priority"] == 18
     and rpc["corps"]["contact_payload"]["last_name"] == "Essai", "au clic : la fonction de l'écran, avec SON jeton, priorité de l'écran")
voir(rpc["corps"]["contact_payload"]["hektor_user_email"] == EMAIL and rpc["corps"]["contact_payload"]["target_hektor_user_email"] == EMAIL,
     "TÉMOIN : une carte trafiquée avec le compte d'un autre -> le serveur remet celui de la personne")
voir(r["travail"] == "job-2c" and r["avec_recherche"], "le numéro du travail revient (et la recherche suit)")
reset(doublons=[{"hektor_contact_id": "602", "display_name": "J. ESSAI", "archive": False}])
appels.clear()
voir(refuse(lambda: ges.executer_creer_contact(nouveau_ctx(), pc), "apparue") and not [a for a in appels if a["chemin"].startswith("rpc/")],
     "TÉMOIN : un doublon né entre la carte et le clic -> refusé AU CLIC, rien envoyé")

VIDE_R = {cle: "" for cle in ges.GESTES["ajouter_recherche"].parametres["properties"]}
reset(contact=[{"hektor_contact_id": "606202", "display_name": "M. DURAND", "archive": False, "ville": "Firminy", "code_postal": "42700"}])
voir(refuse(lambda: ges.preparer_ajouter_recherche(nouveau_ctx(), {**VIDE_R, "hektor_contact_id": "606202", "types": "Maison",
                                                                    "communes": "42700 Firminy"}), "budget maximum"),
     "ajouter une recherche sans budget maximum : refusé")
resume, pr = ges.preparer_ajouter_recherche(nouveau_ctx(), {**VIDE_R, "hektor_contact_id": "606202", "types": "Maison",
                                                            "communes": "42700 Firminy", "budget_max": "200000", "surface_min": "90"})
voir(not ecritures_metier() and "après la nuit" in resume and "Firminy (42700)" in resume and "90 m² min" in resume,
     "la carte dit les critères, et que la recherche n'entre dans les rapprochements qu'après la nuit")
appels.clear()
ges.executer_ajouter_recherche(nouveau_ctx(), pr)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_create_search_optimistic")
c = rpc["corps"]
voir(c["p_fields"]["villes_json"] == ["42700 Firminy"] and c["p_fields"]["types_json"] == {"Maison": "1"}
     and c["p_fields"]["prix_max"] == "200000" and c["p_fields"]["surface_min"] == "90",
     "la ligne provisoire dans les formes de l'écran (types en libellés, villes « code ville »)")
voir(c["search_payload"]["search"]["propertyTypeIds"] == ["1"] and c["search_payload"]["city"] == "Firminy"
     and c["target_contact_id"] == "606202" and c["job_priority"] == 17 and len(c["p_token"]) == 36
     and rpc["entetes"]["Authorization"] == "Bearer " + JETON, "le travail : la recherche, le contexte du contact, un jeton, SON jeton")
reset(contact=[{"hektor_contact_id": "606202", "display_name": "M. DURAND", "archive": True}])
voir(refuse(lambda: ges.preparer_ajouter_recherche(nouveau_ctx(), {**VIDE_R, "hektor_contact_id": "606202", "types": "Maison",
                                                                    "communes": "42700 Firminy", "budget_max": "1"}), "archivé"),
     "un contact archivé : refusé (réactiver d'abord)")

VIDE_M = {cle: "" for cle in ges.GESTES["modifier_recherche"].parametres["properties"]}
RECH = {"contact_search_key": "606202:1", "hektor_contact_id": "606202", "search_index": 1, "archive": False, "is_active": True,
        "offre": "0", "villes_json": ["Firminy 42700"], "types_json": {"1": "Maison", "49": "viager maison"},
        "criteres_json": [{"cle": "ITEM_TERRASSE", "valeur": "1"}, {"cle": "ITEM_DPE_CONS_LETTER", "valeur": "C"}],
        "prix_min": "150000", "prix_max": "250000", "surface_min": "80", "surface_terrain_min": None, "pieces_min": "4",
        "chambre_min": None}
reset(recherche=[dict(RECH)])
resume, pm2 = ges.preparer_modifier_recherche(nouveau_ctx(), {**VIDE_M, "contact_search_key": "606202:1", "budget_max": "280000"})
voir("budget max : 250 000 € → 280 000 €" in resume and "recherche n° 2 de M. DURAND" in resume and not ecritures_metier(),
     "la carte montre l'AVANT et l'APRÈS du seul critère donné")
voir("ne repart plus chez Hektor" in resume and "10 min" not in resume,
     "⛔ la carte ne promet PAS d'envoi à Hektor : une recherche modifiée reste chez nous (C.3 du 24/08, prouvé le 16/11)")
voir(refuse(lambda: ges.preparer_modifier_recherche(nouveau_ctx(), {**VIDE_M, "contact_search_key": "606202:1", "budget_max": "250000"}),
            "Rien ne change"), "rien ne change : refusé")
voir(refuse(lambda: ges.preparer_modifier_recherche(nouveau_ctx(), {**VIDE_M, "contact_search_key": "606202:1", "rayon_km": "50"}),
            "40"), "un rayon au-delà de 40 km : refusé (le curseur de l'écran)")
appels.clear()
ges.executer_modifier_recherche(nouveau_ctx(), pm2)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_edit_search_optimistic")
s = rpc["corps"]["search_payload"]
voir(s["search"]["priceMax"] == "280000" and s["search"]["priceMin"] == "150000" and s["search"]["surfaceMin"] == "80"
     and s["search"]["equipments"] == ["terrasse"] and s["search"]["dpeLetter"] == "C" and s["search"]["propertyTypeIds"] == ["1", "49"],
     "⭐ le RESTE de la recherche est renvoyé tel quel (types, surface, terrasse, DPE) : rien ne se perd")
voir(s["search_index"] == 1 and s["type_labels"] == ["Maison", "viager maison"] and "rayon_km" not in s
     and rpc["corps"]["debounce_seconds"] == 600 and rpc["corps"]["target_contact_id"] == "606202",
     "le rang relu, les libellés des types (même ceux que l'écran ne connaît pas), pas de rayon si non demandé, Hektor 10 min après")
reset(recherche=[{**RECH, "prix_max": "260000"}])
appels.clear()
voir(refuse(lambda: ges.executer_modifier_recherche(nouveau_ctx(), pm2), "a changé") and not [a for a in appels if a["chemin"].startswith("rpc/")],
     "TÉMOIN : la recherche modifiée par quelqu'un d'autre entre la carte et le clic -> refusé, rien n'est écrasé")
reset(recherche=[{**RECH, "archive": True}])
voir(refuse(lambda: ges.preparer_modifier_recherche(nouveau_ctx(), {**VIDE_M, "contact_search_key": "606202:1", "budget_max": "1"}), "archivée"),
     "une recherche archivée : refusée")

print("9quinquies) LOT 3c : VERS LE CLIENT -- e-mail, rapprochement réel, invitation")
Settings.email_real_send_enabled, Settings.email_daily_send_cap = True, 80


class FauxSuivi:
    def __init__(self, settings):
        pass

    def is_opted_out(self, adresse):
        return adresse in etat.get("desinscrits", [])

    def count_real_sends_today(self):
        return etat.get("envois_jour", 0)


class FauxEnvoyeur:
    def __init__(self, settings):
        pass

    def _fresh_filter(self, biens, contact):
        return [b for b in biens if b["annonce_id"] not in etat.get("deja_vus", [])]

    def send_grouped(self, **k):
        google.append({"quoi": "rapprochement", **k})
        return etat.get("rep_envoi") or {"ok": True, "dryRun": False, "sentCount": 1, "sentAnnonceIds": k["annonce_ids"],
                                         "groups": [{"ok": True, "annonceIds": k["annonce_ids"], "messageId": "m9"}]}


ges.EmailTrackingService, ges.RapprochementSender = FauxSuivi, FauxEnvoyeur
CLIENT = "durand@exemple.fr"

reset()
google.clear()
resume, pe = ges.preparer_email_client(nouveau_ctx(), {"hektor_contact_id": "606202", "objet": "Votre visite",
                                                       "texte": "Bonjour,\nje vous confirme la visite.\nPaul"})
voir("M. DURAND" in resume and "adresse de sa fiche" in resume and "je vous confirme la visite" in resume and "VRAIMENT" in resume,
     "la carte dit à qui, que c'est l'adresse de sa fiche, le texte entier, et que ça part VRAIMENT")
voir(CLIENT not in resume and CLIENT not in json.dumps(pe), "⛔ l'adresse du client ne part PAS au modèle (ni dans la carte)")
voir(not [g for g in google if g["quoi"] == "envoyer"] and not ecritures_metier(), "PROPOSER n'envoie rien")
reset(desinscrits=[CLIENT])
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {"hektor_contact_id": "606202", "objet": "o", "texte": "t"}), "DÉSINSCRIT"),
     "⛔ un contact désinscrit : refusé")
reset(contact=[{"hektor_contact_id": "606202", "display_name": "M. DURAND", "email": "", "archive": False}])
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {"hektor_contact_id": "606202", "objet": "o", "texte": "t"}), "pas d'adresse"),
     "un contact sans e-mail : refusé")
reset(contact=[{"hektor_contact_id": "606202", "display_name": "M. DURAND", "email": CLIENT, "archive": True}])
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {"hektor_contact_id": "606202", "objet": "o", "texte": "t"}), "archivé"),
     "un contact archivé : refusé")
reset()
google.clear()
ges.executer_email_client(nouveau_ctx(), pe)
envoi = next(g for g in google if g["quoi"] == "envoyer")
voir(envoi["to"] == [CLIENT] and envoi["subject_email"] == EMAIL and not envoi["attachments"] and envoi["dry_run"] is False
     and google[0]["quoi"] == "garde_gmail", "au clic : l'adresse RELUE sur la fiche, depuis SA boîte, sans pièce jointe")
reset(desinscrits=[CLIENT])
google.clear()
voir(refuse(lambda: ges.executer_email_client(nouveau_ctx(), pe), "DÉSINSCRIT") and not [g for g in google if g["quoi"] == "envoyer"],
     "TÉMOIN : désinscrit entre la carte et le clic -> refusé AU CLIC, rien envoyé")

reset()
resume, pr2 = ges.preparer_envoyer_rapprochement(nouveau_ctx(), {"contact_search_key": "606202:0", "annonces": "63289", "mot": "Je pense à vous"})
voir("VRAIMENT" in resume and "annonce 63289" in resume and "désinscription" in resume and "« proposé »" in resume
     and CLIENT not in resume, "la carte : réel, les biens, la désinscription, « proposé » ensuite, et pas l'adresse")
voir(pr2["annonces"] == [63289] and not [g for g in google if g["quoi"] == "rapprochement"], "PROPOSER n'envoie rien")
reset(deja_vus=[63289])
voir(refuse(lambda: ges.preparer_envoyer_rapprochement(nouveau_ctx(), {"contact_search_key": "606202:0", "annonces": "63289", "mot": ""}),
            "déjà été proposés"), "des biens déjà proposés / vus / écartés : rien de neuf, refusé (comme l'écran)")
reset(envois_jour=80)
voir(refuse(lambda: ges.preparer_envoyer_rapprochement(nouveau_ctx(), {"contact_search_key": "606202:0", "annonces": "63289", "mot": ""}),
            "plafond"), "le plafond du jour atteint : refusé")
Settings.email_real_send_enabled = False
reset()
voir(refuse(lambda: ges.preparer_envoyer_rapprochement(nouveau_ctx(), {"contact_search_key": "606202:0", "annonces": "63289", "mot": ""}),
            "coupé"), "l'envoi réel coupé sur le serveur : refusé (pas de faux envoi)")
Settings.email_real_send_enabled = True
reset()
google.clear()
appels.clear()
r = ges.executer_envoyer_rapprochement(nouveau_ctx(), pr2)
envoi = next(g for g in google if g["quoi"] == "rapprochement")
voir(envoi["recipient_email"] == CLIENT and envoi["dry_run"] is False and envoi["variante"] == "pull" and envoi["annonce_ids"] == [63289]
     and envoi["fallback_sender_email"] == EMAIL and envoi["custom_intro"] == "Je pense à vous",
     "au clic : le point d'envoi de l'écran (côté acquéreur), adresse relue, repli = la personne posé par le serveur")
prop = next(a for a in appels if a["chemin"] == "rpc/app_record_proposition")
voir(prop["corps"]["p_channel"] == "email" and prop["corps"]["p_gmail_message_id"] == "m9" and prop["corps"]["p_dossier_id"] == 77
     and prop["entetes"]["Authorization"] == "Bearer " + JETON and r["biens_marques_proposes"] == 1,
     "le bien envoyé passe « proposé » par e-mail, avec SON jeton (= propose(sentRefs, 'email') de l'écran)")
reset(rep_envoi={"ok": False, "skipped": "opt_out", "groups": []})
appels.clear()
voir(refuse(lambda: ges.executer_envoyer_rapprochement(nouveau_ctx(), pr2), "désinscrit")
     and not [a for a in appels if a["chemin"] == "rpc/app_record_proposition"],
     "TÉMOIN : le serveur d'envoi refuse (désinscrit) -> on le DIT, aucun bien marqué proposé")
reset(rep_envoi={"ok": True, "dryRun": True, "groups": [{"ok": True, "annonceIds": [63289], "messageId": None}]})
appels.clear()
voir(refuse(lambda: ges.executer_envoyer_rapprochement(nouveau_ctx(), pr2), "MODE TEST")
     and not [a for a in appels if a["chemin"] == "rpc/app_record_proposition"],
     "TÉMOIN : un envoi parti en mode test n'est PAS annoncé comme envoyé, rien marqué")

reset()
google.clear()
resume, prd = ges.preparer_rdv_client(nouveau_ctx(), {"type": "visite", "titre": "Visite — M. DURAND", "debut": demain,
                                                      "duree_minutes": 60, "lieu": "", "hektor_annonce_id": "63289",
                                                      "hektor_contact_id": "606202", "contact_search_key": "", "note": ""})
voir("VRAIE invitation" in resume and "Aucune invitation" not in resume and CLIENT not in resume and "depuis l'écran" in resume,
     "la carte dit qu'une VRAIE invitation part, sans l'adresse, et que la suite se fait depuis l'écran")
voir(refuse(lambda: ges.preparer_rdv_client(nouveau_ctx(), {"type": "autre", "titre": "x", "debut": demain, "duree_minutes": 30, "lieu": "",
                                                            "hektor_annonce_id": "", "hektor_contact_id": "", "contact_search_key": "",
                                                            "note": ""}), "contact à inviter"), "sans contact à inviter : refusé")
google.clear()
r = ges.executer_rdv_client(nouveau_ctx(), prd)
creer = next(g for g in google if g["quoi"] == "creer")
lien = next(g for g in google if g["quoi"] == "lien_creer")
voir(creer["attendees"] == [CLIENT] and creer["send_updates"] == "all" and creer["subject_email"] == EMAIL
     and lien["attendees"] == [CLIENT] and lien["metadata_json"]["send_updates"] == "all" and r["invitation_envoyee"],
     "au clic : dans SON agenda, le client invité (adresse relue), Google le prévient ; notre copie le note")
google.clear()
ges.executer_rdv(nouveau_ctx(), prd)
voir(next(g for g in google if g["quoi"] == "creer")["attendees"] == [] and next(g for g in google if g["quoi"] == "creer")["send_updates"] == "none",
     "TÉMOIN : le rendez-vous du lot 3a, lui, reste SANS invité ni notification")

print("9sexies) VAGUE C : la DIRECTION sur une transaction -- la fonction de la base de l'écran")
_faux_2c = faux_lot2c


def faux_vague_c(methode, url, **kw):
    chemin = url.split("/rest/v1/", 1)[1] if "/rest/v1/" in url else ""
    p_ = kw.get("params") or {}
    if methode == "GET" and chemin == "app_affaire_ledger" and "kind" in str(p_.get("select")):
        appels.append({"methode": "GET", "chemin": chemin, "params": dict(p_), "entetes": dict(kw.get("headers") or {}), "corps": None})
        lignes = etat.get("affaires", [])
        if "app_affaire_id" in p_ and str(p_["app_affaire_id"]).startswith("eq."):
            return Reponse([l for l in lignes if str(l["app_affaire_id"]) == p_["app_affaire_id"][3:]])
        chaine = str(p_.get("app_chaine_id", ""))[3:]
        exclu = str(p_.get("app_affaire_id", ""))[4:]
        return Reponse([l for l in lignes if str(l.get("app_chaine_id")) == chaine and str(l["app_affaire_id"]) != exclu])
    if methode == "POST" and chemin == "rpc/app_geste_affaire_optimistic":
        appels.append({"methode": "POST", "chemin": chemin, "params": {}, "entetes": dict(kw.get("headers") or {}), "corps": kw.get("json")})
        return Reponse(etat.get("rep_geste") or {"ok": True, "job_id": "j-c", "etat_avant": "proposed", "etat_apres": "accepted",
                                                 "offres_refusees_en_cascade": 0})
    return _faux_2c(methode, url, **kw)


requests.get = lambda url, **kw: faux_vague_c("GET", url, **kw)
requests.post = lambda url, **kw: faux_vague_c("POST", url, **kw)
requests.patch = lambda url, **kw: faux_vague_c("PATCH", url, **kw)
requests.request = lambda methode, url, **kw: faux_vague_c(methode, url, **kw)

OFFRE = {"app_affaire_id": 701, "kind": "offre", "state": "proposed", "hektor_affaire_id": 33100, "hektor_annonce_id": 63289,
         "app_dossier_id": 77, "app_chaine_id": 9, "montant": 150000, "date": "2026-11-10", "present_in_hektor": True}
COMPROMIS = {"app_affaire_id": 702, "kind": "compromis", "state": "active", "hektor_affaire_id": 50200, "hektor_annonce_id": 63289,
             "app_dossier_id": 77, "app_chaine_id": 9, "montant": 150000, "date": "2026-11-12", "present_in_hektor": True}
VENTE = {"app_affaire_id": 703, "kind": "vente", "state": None, "hektor_affaire_id": 60300, "hektor_annonce_id": 63289,
         "app_dossier_id": 77, "app_chaine_id": 9, "montant": 150000, "date": "2026-11-14", "present_in_hektor": True}
noms_commercial = [f.nom for f in cat.fonctions_du_role("commercial")]
voir("proposer_transaction" not in noms_commercial and "proposer_transaction" in [f.nom for f in cat.fonctions_du_role("manager")]
     and "proposer_transaction" in [f.nom for f in cat.fonctions_du_role("admin")],
     "⛔ DROITS : un négociateur n'a PAS la carte ; la direction (admin, manager) l'a -- comme l'écran et la base")
reset(affaires=[dict(OFFRE)])
resume, pt = ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 701, "geste": "accepter"})
voir("Accepter l'offre n° 33100" in resume and "150 000 €" in resume and "l'état d'avant est remis" in resume and not ecritures_metier(),
     "la carte : quel geste, quelle offre, le montant, et que Hektor peut refuser ; PROPOSER n'écrit rien")
voir(refuse(lambda: ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 701, "geste": "annuler"}), "compromis"),
     "un geste qui ne va pas avec le type (annuler une offre) : refusé")
voir(refuse(lambda: ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 701, "geste": "supprimer"}), "à l'écran"),
     "⛔ supprimer : pas ouvert à l'assistant (décision « sans »)")
reset(affaires=[{**OFFRE, "state": "accepted"}])
voir(refuse(lambda: ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 701, "geste": "accepter"}), "déjà"),
     "déjà dans cet état : refusé")
reset(affaires=[{**OFFRE, "hektor_affaire_id": None}])
voir(refuse(lambda: ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 701, "geste": "refuser"}), "numéro Hektor"),
     "sans numéro Hektor : refusé (comme l'écran)")
reset(affaires=[dict(OFFRE), dict(COMPROMIS)])
voir(refuse(lambda: ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 701, "geste": "refuser"}), "compromis en cours"),
     "⛔ une offre verrouillée par son compromis en cours : refusé, avec la raison (règle du 16/09)")
reset(affaires=[dict(OFFRE), {**COMPROMIS, "state": "cancelled"}])
voir(ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 701, "geste": "refuser"})[1]["geste"] == "refuser",
     "le compromis annulé ne verrouille plus l'offre")
reset(affaires=[dict(COMPROMIS), dict(VENTE)])
voir(refuse(lambda: ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 702, "geste": "annuler"}), "supprimer la vente"),
     "⛔ un compromis verrouillé par sa vente : refusé (décision du 23/10)")
reset(affaires=[dict(COMPROMIS), {**VENTE, "present_in_hektor": False}])
resume, pa = ges.preparer_transaction(nouveau_ctx("admin"), {"app_affaire_id": 702, "geste": "annuler"})
voir("cascade" in resume, "une vente supprimée chez Hektor ne verrouille plus ; la carte prévient de la cascade sur l'offre")
reset(affaires=[dict(OFFRE)])
appels.clear()
r = ges.executer_transaction(nouveau_ctx("admin"), pt)
rpc = next(a for a in appels if a["chemin"] == "rpc/app_geste_affaire_optimistic")
voir(rpc["corps"] == {"target_affaire_id": 701, "geste": "accepte", "job_priority": 7} and rpc["entetes"]["Authorization"] == "Bearer " + JETON
     and r["travail"] == "j-c", "au clic : LA fonction de l'écran (même verbe, même priorité), avec SON jeton")
reset(affaires=[dict(OFFRE)], rep_geste={"ok": True, "deja_dans_cet_etat": True})
voir(refuse(lambda: ges.executer_transaction(nouveau_ctx("admin"), pt), "déjà"), "la base dit « déjà dans cet état » : on le DIT, pas de faux succès")
reset(affaires=[])
appels.clear()
voir(refuse(lambda: ges.executer_transaction(nouveau_ctx("admin"), pt), "pas parmi")
     and not [a for a in appels if a["chemin"] == "rpc/app_geste_affaire_optimistic"],
     "TÉMOIN : la transaction devenue invisible (droits) entre la carte et le clic -> refusé, rien envoyé")
print("  (au clic, la route refuse aussi un rôle hors de geste.roles : DIRECTION pour cette carte)")
voir(ges.GESTES["transaction"].roles == ges.DIRECTION, "la carte est déclarée DIRECTION : la route de validation la refuse à un négociateur")

print("10) aucune fonction de geste ne fait autre chose que proposer")
voir(all(f.nom.startswith("proposer_") for f in ges.FONCTIONS_GESTES) and len(ges.FONCTIONS_GESTES) == 42,
     "42 gestes (le brouillon retiré le 15/11, 3 du lot 2c, 3 du lot 3c, 1 de la vague C, le numéro de mandat, la relance "
     "et l'annulation d'une signature le 16/11, puis les 8 cartes directes de l'audit §35, le prix et le Pilotage pour la direction, ajouter une photo et déposer des documents le 17/11, "
     "ouvrir la création le 18/11), "
     "tous « proposer_ » : le "
     "modèle n'a AUCUNE fonction qui exécute")
voir(not any(f.nom.startswith("proposer_") for f in ges.FONCTIONS_LECTURE_LOT3), "les 2 lectures du lot 3 ne proposent rien")
voir(not any(f.nom.startswith("proposer_") for f in ges.FONCTIONS_LECTURE_LOT4), "les 3 lectures du lot 4 ne proposent rien")
voir([f.nom for f in cat.fonctions_du_role("commercial") if f.nom == "proposer_note_transaction"] == [],
     "un commercial n'a PAS la note de transaction (double verrou : non proposée, et refusée au clic)")

print("11) ÉTAPE 4 LOT 3 : la cible d'une carte (le lien « Ouvrir la fiche » de l'écran)")
voir(ges.cibles_carte({"hektor_contact_id": "10354641", "app_dossier_id": 61398, "libelle": "x", "echeance": "2026-11-17"})
     == [{"type": "contact", "id": "10354641"}, {"type": "bien", "id": "61398"}],
     "une relance : le contact d'abord, puis le bien par son app_dossier_id (pas de numéro d'annonce)")
voir(ges.cibles_carte({"hektor_annonce_id": 63330, "champs": {"pieces": 6}}) == [{"type": "annonce", "numero": "63330"}],
     "un bien modifié : le numéro d'annonce ; les champs ne sortent pas")
voir(ges.cibles_carte({"hektor_annonce_id": 0, "app_dossier_id": 10000006}) == [{"type": "bien", "id": "10000006"}],
     "un numéro d'annonce à 0 (bien né dans l'app) : repli sur l'app_dossier_id")
voir(ges.cibles_carte({"hektor_contact_id": "10354641", "objet": "Bonjour", "texte": "secret du courriel"})
     == [{"type": "contact", "id": "10354641"}], "un e-mail au client : le contact seul, JAMAIS l'objet ni le texte")
voir(ges.cibles_carte({"destinataires": ["a@gti-immobilier.fr"], "texte": "x"}) == [] and ges.cibles_carte({"notification_ids": [1, 2]}) == []
     and ges.cibles_carte({"rdv_id": "abc"}) == [] and ges.cibles_carte(None) == [],
     "e-mail interne, notifications, rendez-vous supprimé (sans date), rien : aucune cible (pas de lien inventé)")
print("11bis) LOT 3b : transaction, recherche, rendez-vous, demande")
voir(ges.cibles_carte({"app_affaire_id": 1001409, "geste": "accepte"}, "transaction") == [{"type": "transaction", "id": "1001409"}],
     "une transaction : son app_affaire_id")
voir(ges.cibles_carte({"contact_search_key": "344a6bbc6068564a4e2bd9df"}, "archiver_recherche") == [{"type": "recherche", "cle": "344a6bbc6068564a4e2bd9df"}],
     "une recherche seule : sa clé")
voir(ges.cibles_carte({"contact_search_key": "k", "hektor_contact_id": "10354641", "hektor_annonce_id": 63330, "debut": "2026-11-18T20:30:00+01:00"}, "rdv_client")
     == [{"type": "contact", "id": "10354641"}, {"type": "annonce", "numero": "63330"}, {"type": "rdv", "date": "2026-11-18"}],
     "un rendez-vous client : le contact (pas la recherche en double), le bien, et le JOUR du rendez-vous")
voir(ges.cibles_carte({"type": "baisse_prix", "hektor_annonce_id": 63289, "nouveau_prix": 149000}, "demande_direction")
     == [{"type": "annonce", "numero": "63289"}, {"type": "demande", "numero": "63289"}]
     and ges.cibles_carte({"hektor_annonce_id": 63289}, "modifier_bien") == [{"type": "annonce", "numero": "63289"}],
     "une demande à la direction : le bien ET la demande ; un autre geste sur le même bien : pas de « demande »")
voir(ges.cibles_carte({"debut": "demain"}, "deplacer_rdv") == [], "un début illisible : pas de jour inventé")
_post = requests.post
requests.post = lambda url, **kw: type("R", (), {"ok": True, "status_code": 201, "json": lambda self: [{"id": "c-lot3", "expire_le": "2026-11-16T13:00:00Z"}]})()
_ctx3 = cat.ContexteAssistant(settings=Settings(), user_id=UID, email="moi@gti-immobilier.fr", role="admin", jeton="jeton", conversation_id="conv")
_carte = ges.ranger_carte(_ctx3, ges.GESTES["modifier_bien"], "résumé", {"hektor_annonce_id": 63330, "champs": {"pieces": 6}})
requests.post = _post
voir(_carte["cibles"] == [{"type": "annonce", "numero": "63330"}] and _ctx3.cartes[-1]["cibles"] == _carte["cibles"],
     "la carte rangée porte sa cible, et c'est elle qui part dans le flux (ctx.cartes)")
from app.services.assistant_service import AssistantService  # noqa: E402
_get = requests.get
_vu = {}
def _faux_get(url, **kw):
    _vu.update(kw.get("params") or {})
    return type("R", (), {"ok": True, "json": lambda self: [{"id": "c1", "geste": "email_client", "resume": "r", "etat": "proposee",
                                                              "parametres": {"hektor_contact_id": "10354641", "texte": "secret du courriel"}}]})()
requests.get = _faux_get
_relues = AssistantService(Settings()).lister_cartes("jeton", "conv")
requests.get = _get
voir("parametres" in _vu.get("select", "") and _relues == [{"id": "c1", "geste": "email_client", "resume": "r", "etat": "proposee",
     "cibles": [{"type": "contact", "id": "10354641"}]}],
     "relire les cartes : la cible est jointe, les paramètres (le texte de l'e-mail) ne sortent PAS")

print("12) LE NUMÉRO DE MANDAT (16/11) : les gardes de l'écran, la carte qui dit « ne se défait pas », la fonction de la base")
etat12 = {}
appels12 = []


def faux12(methode, url, **kw):
    chemin = url.split("/rest/v1/", 1)[1]
    appels12.append({"methode": methode, "chemin": chemin, "entetes": dict(kw.get("headers") or {}),
                     "params": dict(kw.get("params") or {}), "corps": kw.get("json")})
    if methode == "GET" and chemin == "app_dossiers_current":
        if "negociateur_email" in str((kw.get("params") or {}).get("select")):
            return Reponse([{"negociateur_email": etat12.get("nego", "pereira@gti-immobilier.fr"), "commercial_id": None}])
        return Reponse(etat12.get("bien", [{"app_dossier_id": 10000006, "hektor_annonce_id": 63330, "numero_mandat": None,
                                             "titre_bien": "ESSAI 8A2B", "statut_annonce": "Estimation"}]))
    if methode == "GET" and chemin == "app_contact_relations_current":
        return Reponse(etat12.get("mandants", [{"hektor_contact_id": "10354641"}]))
    if methode == "GET" and chemin == "app_contacts_current":
        return Reponse([{"display_name": "Mme CLAUDE TESTCLAUDE"}])
    if methode == "GET":
        return Reponse([])
    if chemin == "rpc/app_console_create_mandat_auto_number_job":
        return Reponse({"id": "travail-mandat", "status": "pending"})
    return Reponse(None, status=500)


requests.get = lambda url, **kw: faux12("GET", url, **kw)
requests.post = lambda url, **kw: faux12("POST", url, **kw)
requests.request = lambda methode, url, **kw: faux12(methode, url, **kw)
P12 = {"hektor_annonce_id": "63330", "sous_type": "", "date_debut": "", "duree_mois": "", "tacite_reconduction": ""}
resume12, p12 = ges.preparer_numero_mandat(nouveau_ctx(), P12)
voir("NE SE DÉFAIT PAS" in resume12 and "Mme CLAUDE TESTCLAUDE" in resume12 and "12 mois" in resume12 and "avec tacite" in resume12,
     "la carte dit l'irréversible, NOMME les mandants, et les valeurs par défaut de l'écran (12 mois, tacite reconduction)")
voir(p12["sous_type"] == "Mandat de vente" and p12["duree_mois"] == "12" and p12["tacite"] is True,
     "vide = Mandat de vente, 12 mois, tacite : comme l'écran")
voir(not [a for a in appels12 if a["methode"] != "GET"], "PROPOSER n'écrit rien (que des lectures)")
voir([a["params"].get("role_contact") for a in appels12 if a["chemin"] == "app_contact_relations_current"] == ["in.(mandant,proprietaire)"],
     "les vendeurs d'un bien SANS numéro sont « proprietaire » (« mandant » = déjà numéroté) : les deux rôles comptent")
etat12["bien"] = [{"app_dossier_id": 1352134, "hektor_annonce_id": 24935, "numero_mandat": "11964", "titre_bien": "x"}]
voir(refuse(lambda: ges.preparer_numero_mandat(nouveau_ctx(), {**P12, "hektor_annonce_id": "24935"}), "déjà le mandat 11964"),
     "⛔ un bien qui A DÉJÀ un numéro : refusé (le « nouveau mandat » reste à l'écran)")
etat12.pop("bien")
etat12["mandants"] = []
voir(refuse(lambda: ges.preparer_numero_mandat(nouveau_ctx(), P12), "aucun mandant"), "⛔ sans mandant : refusé, comme l'écran")
etat12.pop("mandants")
etat12["nego"] = ""
voir(refuse(lambda: ges.preparer_numero_mandat(nouveau_ctx(), P12), "négociateur"), "⛔ sans négociateur : refusé, comme l'écran")
etat12.pop("nego")
voir(refuse(lambda: ges.preparer_numero_mandat(nouveau_ctx(), {**P12, "sous_type": "Mandat de location-bailleur"}), "Sous-type")
     and refuse(lambda: ges.preparer_numero_mandat(nouveau_ctx(), {**P12, "duree_mois": "200"}), "durée")
     and refuse(lambda: ges.preparer_numero_mandat(nouveau_ctx(), {**P12, "date_debut": "16/11/2026"}), "AAAA-MM-JJ"),
     "un sous-type hors mandat de vente, une durée de 200 mois, une date mal écrite : refusés")
appels12.clear()
r12 = ges.executer_numero_mandat(nouveau_ctx(), {**p12, "date_debut": "2026-11-16"})
rpc12 = [a for a in appels12 if a["chemin"] == "rpc/app_console_create_mandat_auto_number_job"]
voir(len(rpc12) == 1 and rpc12[0]["entetes"].get("Authorization") == f"Bearer {JETON}"
     and rpc12[0]["corps"]["target_app_dossier_id"] == 10000006 and rpc12[0]["corps"]["target_hektor_annonce_id"] == "63330"
     and rpc12[0]["corps"]["mandat_payload"]["date_debut"] == "16/11/2026"
     and rpc12[0]["corps"]["mandat_payload"]["sub_type_mandat"] == "Mandat de vente"
     and rpc12[0]["corps"]["mandat_payload"]["mandant_contact_ids"] == []
     and rpc12[0]["corps"]["mandat_payload"]["hektor_user_email"] == "pereira@gti-immobilier.fr"
     and r12["travail"] == "travail-mandat",
     "au CLIC : la fonction de la base de l'écran, avec le JETON de la personne, la date en JJ/MM/AAAA, les mandants laissés "
     "au worker, le négociateur du bien ; le numéro du travail revient (l'écran se relit à sa fin)")
appels12.clear()
etat12["bien"] = [{"app_dossier_id": 10000006, "hektor_annonce_id": 63330, "numero_mandat": "19001", "titre_bien": "x"}]
voir(refuse(lambda: ges.executer_numero_mandat(nouveau_ctx(), {**p12, "date_debut": "2026-11-16"}), "déjà le mandat 19001")
     and not [a for a in appels12 if a["methode"] != "GET"],
     "TÉMOIN : un numéro apparu entre la carte et le clic -> refusé, RIEN envoyé (pas de second numéro officiel)")
etat12.pop("bien")
voir(ges.GESTES["numero_mandat"].roles == frozenset({"admin", "manager", "commercial"}),
     "ouvert à tous les rôles, comme l'écran : la base contrôle le bien de la personne (app_console_can_request_job)")

print("13) LA SIGNATURE YOUTRUST EN COURS (16/11) : relancer un signataire, annuler -- les règles de lib/suiviSignataires")
etat13 = {}
appels13 = []
SIGNERS = [{"prenom": "Pauline", "nom": "GIRINON", "role": "mandant", "email": "pauline@client.fr", "status": "signed",
            "provider_signer_id": "s1"},
           {"prenom": "Delphine", "nom": "TEST GTI", "role": "mandant", "email": "delphine@client.fr", "status": "notified",
            "provider_signer_id": "s2"},
           {"prenom": "Frédéric", "nom": "GERPHAGNON", "role": "mandataire", "email": "f@gti-immobilier.fr",
            "status": "initiated", "provider_signer_id": "s3"}]


def faux13(methode, url, **kw):
    chemin = url.split("/rest/v1/", 1)[1]
    appels13.append({"methode": methode, "chemin": chemin, "entetes": dict(kw.get("headers") or {}), "corps": kw.get("json")})
    if methode == "GET" and chemin == "app_setting":
        return Reponse([{"value": etat13.get("cran", "admin")}])
    if methode == "GET" and chemin == "app_dossiers_current":
        return Reponse([{"app_dossier_id": 1387336, "hektor_annonce_id": 61398, "numero_mandat": "18420", "titre_bien": "x"}])
    if methode == "GET" and chemin == "app_console_document":
        return Reponse(etat13.get("documents", [
            {"id": "doc-1", "app_dossier_id": 1387336, "hektor_annonce_id": "61398", "document_name": "Mandat de vente - 18420.pdf",
             "metadata_json": {"signature": {"provider": "youtrust", "signature_request_id": "dem-1", "status": "pending"}}},
            {"id": "doc-0", "app_dossier_id": 1387336, "hektor_annonce_id": "61398", "document_name": "Ancien.pdf",
             "metadata_json": {"signature": {"provider": "immosign"}}}]))
    if methode == "GET" and chemin == "app_signature_request":
        return Reponse([{"id": "dem-1", "status": etat13.get("statut", "ongoing"), "signers": etat13.get("signers", SIGNERS)}])
    if methode == "GET":
        return Reponse([])
    if methode == "POST" and chemin == "app_console_job":
        return Reponse([{"id": "job-yt", "status": "pending"}])
    return Reponse(None, status=500)


requests.get = lambda url, **kw: faux13("GET", url, **kw)
requests.post = lambda url, **kw: faux13("POST", url, **kw)
requests.request = lambda methode, url, **kw: faux13(methode, url, **kw)
R13 = {"hektor_annonce_id": "61398", "document": "", "signataire": ""}
voir(refuse(lambda: ges.preparer_relance_signature(nouveau_ctx("commercial"), R13), "pas ouverte"),
     "⛔ interrupteur `signature_youtrust` = admin : un négociateur est refusé (comme l'écran, où les boutons n'existent pas)")
resume13, p13 = ges.preparer_relance_signature(nouveau_ctx("admin"), R13)
voir("Delphine TEST GTI" in resume13 and "@" not in resume13 and p13["provider_signer_id"] == "s2"
     and p13["signature_request_id"] == "dem-1" and p13["document_id"] == "doc-1",
     "la relance vise LE signataire invité qui n'a pas signé (pas celle qui a signé, pas le mandataire « pas son tour ») ; "
     "son e-mail n'est JAMAIS dans la carte (le résumé repart au modèle)")
voir(not [a for a in appels13 if a["methode"] != "GET"], "PROPOSER n'écrit rien")
etat13["signers"] = [dict(SIGNERS[1]), {**SIGNERS[0], "status": "notified"}]
voir(refuse(lambda: ges.preparer_relance_signature(nouveau_ctx("admin"), R13), "précise lequel")
     and ges.preparer_relance_signature(nouveau_ctx("admin"), {**R13, "signataire": "girinon"})[1]["provider_signer_id"] == "s1",
     "deux personnes attendent : la carte demande laquelle ; un morceau du nom départage")
etat13.pop("signers")
etat13["statut"] = "approval"
voir(refuse(lambda: ges.preparer_relance_signature(nouveau_ctx("admin"), R13), "Personne à relancer")
     and "Annuler la signature" in ges.preparer_annulation_signature(nouveau_ctx("admin"), {"hektor_annonce_id": "61398", "document": ""})[0],
     "une demande en `approval` : PAS de relance (Youtrust la refuserait), mais l'annulation, oui")
etat13["statut"] = "done"
voir(refuse(lambda: ges.preparer_annulation_signature(nouveau_ctx("admin"), {"hektor_annonce_id": "61398", "document": ""}), "Aucune signature"),
     "une signature finie (signée) : rien à annuler")
etat13.pop("statut")
appels13.clear()
r13 = ges.executer_relance_signature(nouveau_ctx("admin"), p13)
poses = [a for a in appels13 if a["methode"] == "POST"]
voir(len(poses) == 1 and poses[0]["chemin"] == "app_console_job" and poses[0]["entetes"].get("Authorization") == f"Bearer {JETON}"
     and poses[0]["corps"]["job_type"] == "youtrust_remind_signer" and poses[0]["corps"]["requested_by"] == UID
     and poses[0]["corps"]["payload_json"] == {"signature_request_id": "dem-1", "app_console_document_id": "doc-1",
                                                "document_name": "Mandat de vente - 18420.pdf", "provider_signer_id": "s2"}
     and r13["travail"] == "job-yt",
     "au CLIC : le travail de l'écran (poserTravailYoutrust), avec le JETON et la personne comme demandeur")
appels13.clear()
etat13["signers"] = [{**SIGNERS[1], "status": "signed"}]
voir(refuse(lambda: ges.executer_relance_signature(nouveau_ctx("admin"), p13), "plus à relancer")
     and not [a for a in appels13 if a["methode"] == "POST"],
     "TÉMOIN : le signataire a signé entre la carte et le clic -> refusé, RIEN envoyé")
etat13.pop("signers")
appels13.clear()
_, pa13 = ges.preparer_annulation_signature(nouveau_ctx("admin"), {"hektor_annonce_id": "61398", "document": "18420"})
ra13 = ges.executer_annulation_signature(nouveau_ctx("admin"), pa13)
poses = [a for a in appels13 if a["methode"] == "POST"]
voir(len(poses) == 1 and poses[0]["corps"]["job_type"] == "youtrust_cancel_signature"
     and "provider_signer_id" not in poses[0]["corps"]["payload_json"] and ra13["travail"] == "job-yt",
     "annuler : le travail d'annulation de l'écran, sur la DEMANDE (pas un signataire)")
etat13["cran"] = "on"
voir(ges.preparer_relance_signature(nouveau_ctx("commercial"), R13)[1]["provider_signer_id"] == "s2",
     "interrupteur `on` : ouvert à tous les rôles, comme l'écran")
etat13.pop("cran")

print("14) LES CARTES DIRECTES (16/11, audit §35) : mandants, adresse, conjoint, négociateur, archivage, statut")
etat14 = {}
appels14 = []
C14 = {  # NOTRE numéro (>= 10 000 000) et le numéro HEKTOR (hektor_target_id) sont TOUJOURS différents
    "10354641": {"hektor_contact_id": "10354641", "hektor_target_id": "605717", "display_name": "Mme CLAUDE TESTCLAUDE",
                 "nom": "TESTCLAUDE", "archive": False, "negociateur_email": "pereira@gti-immobilier.fr",
                 "commercial_nom": "PEREIRA", "couple_role": None, "nature_fiche": "personne_seule", "couple_json": None,
                 "hektor_couple_contact_id": None, "relation_roles_json": ["acquereur"], "adresse": "1 rue Haute",
                 "code_postal": "42000", "ville": "Saint-Étienne"},
    "10354642": {"hektor_contact_id": "10354642", "hektor_target_id": "605718", "display_name": "M. JEAN TESTJEAN",
                 "nom": "TESTJEAN", "archive": False, "negociateur_email": "pereira@gti-immobilier.fr",
                 "commercial_nom": "PEREIRA", "couple_role": None, "nature_fiche": "personne_seule", "couple_json": None,
                 "hektor_couple_contact_id": None, "relation_roles_json": [], "adresse": None, "code_postal": None,
                 "ville": None},
}
B14 = {"app_dossier_id": 10000006, "hektor_annonce_id": 63330, "numero_dossier": "VA9", "numero_mandat": None,
       "titre_bien": "ESSAI 8A2B", "commercial_nom": "PEREIRA", "validation_diffusion_state": "", "statut_annonce": "Estimation",
       "prix": 100000}
T14 = {"negociateur_email": "pereira@gti-immobilier.fr", "commercial_id": "45", "commercial_nom": "PEREIRA",
       "statut_annonce": "Estimation", "archive": "0", "diffusable": "0", "numero_dossier": "VA9", "numero_mandat": None,
       "offre_id": None, "offre_state": None, "compromis_id": None, "compromis_state": None, "vente_id": None,
       "titre_bien": "ESSAI 8A2B"}
NEGOS14 = [{"hektor_negociateur_id": "114", "hektor_user_id": "201", "hektor_agence_id": "7", "agence_id_user": "70",
            "agence_nom": "GTI Firminy", "nom_vu": "Delphine BLANCHARD", "email_vu": "delphine@gti-immobilier.fr"},
           {"hektor_negociateur_id": "45", "hektor_user_id": "202", "hektor_agence_id": "8", "agence_id_user": "80",
            "agence_nom": "GTI Yssingeaux", "nom_vu": "Delphine BLANCHARD", "email_vu": "delphine@gti-immobilier.fr"},
           {"hektor_negociateur_id": "12", "hektor_user_id": "203", "hektor_agence_id": "7", "agence_id_user": "70",
            "agence_nom": "GTI Firminy", "nom_vu": "Paulo PEREIRA", "email_vu": "pereira@gti-immobilier.fr"}]


def faux14(methode, url, **kw):
    params = dict(kw.get("params") or {})
    if "geo.api.gouv.fr" in url:
        return Reponse([{"nom": "Firminy"}] if params.get("codePostal") == "42700" else [{"nom": "Saint-Étienne"}])
    chemin = url.split("/rest/v1/", 1)[1]
    appels14.append({"methode": methode, "chemin": chemin, "entetes": dict(kw.get("headers") or {}), "params": params,
                     "corps": kw.get("json")})
    if methode == "GET" and chemin == "app_dossiers_current":
        if "app_dossier_id" in params:
            return Reponse([{**T14, **etat14.get("tete", {})}])
        return Reponse([] if etat14.get("sans_bien") else [{**B14, **etat14.get("bien", {})}])
    if methode == "GET" and chemin == "app_contacts_current":
        numero = params["hektor_contact_id"].split(".", 1)[1]
        return Reponse([{**C14[numero], **etat14.get("contact", {}).get(numero, {})}] if numero in C14 else [])
    if methode == "GET" and chemin == "app_contact_relations_current":
        return Reponse([{"hektor_contact_id": x} for x in etat14.get("mandants", ["10354641"])])
    if methode == "GET" and chemin == "app_setting":
        return Reponse([{"value": etat14.get("cran", "on")}])
    if methode == "GET" and chemin == "app_negociateur_fiche":
        return Reponse(etat14.get("negos", NEGOS14))
    if methode == "GET" and chemin == "app_console_job":
        return Reponse(etat14.get("en_cours", []))
    if methode == "GET" and chemin == "app_archive_annonce_index_current":
        return Reponse(etat14.get("archives", []))
    if methode == "GET":
        return Reponse([])
    if chemin.startswith("rpc/"):
        if chemin in etat14.get("refus", {}):
            return Reponse({"message": etat14["refus"][chemin]}, status=400)
        return Reponse(etat14.get("reponses", {}).get(chemin, {"id": "travail-14", "status": "pending", "job_id": "travail-14",
                                                                "ok": True}))
    return Reponse(None, status=500)


requests.get = lambda url, **kw: faux14("GET", url, **kw)
requests.post = lambda url, **kw: faux14("POST", url, **kw)
requests.request = lambda methode, url, **kw: faux14(methode, url, **kw)


def ecrits14():
    return [a for a in appels14 if a["methode"] != "GET"]


def rpc14(nom):
    return [a for a in appels14 if a["chemin"] == f"rpc/{nom}"]


# 14a — rattacher un mandant existant
RM = {"hektor_annonce_id": "63330", "hektor_contact_id": "10354642"}
appels14.clear()
resume_rm, p_rm = ges.preparer_rattacher_mandant(nouveau_ctx(), RM)
voir("M. JEAN TESTJEAN" in resume_rm and "MANDANT" in resume_rm and "ne se retire plus" in resume_rm and not ecrits14()
     and p_rm == {"hektor_annonce_id": 63330, "hektor_contact_id": "10354642"},
     "rattacher : la carte nomme le contact et prévient (un mandat numéroté fige les mandants) ; PROPOSER n'écrit rien")
voir(refuse(lambda: ges.preparer_rattacher_mandant(nouveau_ctx(), {**RM, "hektor_contact_id": "10354641"}), "déjà mandant"),
     "⛔ un contact déjà mandant (ou propriétaire) du bien : refusé")
etat14["contact"] = {"10354642": {"negociateur_email": "autre@gti-immobilier.fr", "commercial_nom": "AUTRE"}}
voir(refuse(lambda: ges.preparer_rattacher_mandant(nouveau_ctx(), RM), "négociateur du bien"),
     "⛔ un contact d'un autre négociateur : refusé, comme le sélecteur de l'écran (ses contacts seulement)")
etat14["contact"] = {"10354642": {"archive": True}}
voir(refuse(lambda: ges.preparer_rattacher_mandant(nouveau_ctx(), RM), "archivé"), "⛔ un contact archivé : refusé")
etat14["contact"] = {"10354642": {"couple_role": "menage_resolu"}}
voir(refuse(lambda: ges.preparer_rattacher_mandant(nouveau_ctx(), RM), "MÉNAGE"), "⛔ la fiche du ménage : refusée (une personne)")
etat14.pop("contact")
etat14["tete"] = {"negociateur_email": "", "commercial_id": ""}
voir(refuse(lambda: ges.preparer_rattacher_mandant(nouveau_ctx(), RM), "pas de négociateur"),
     "⛔ un bien sans négociateur : refusé (le worker ne saurait pas sous quelle identité écrire)")
etat14.pop("tete")
appels14.clear()
r_rm = ges.executer_rattacher_mandant(nouveau_ctx(), p_rm)
c = rpc14("app_link_mandant_optimistic")
voir(len(c) == 1 and c[0]["entetes"].get("Authorization") == f"Bearer {JETON}"
     and c[0]["corps"] == {"target_app_dossier_id": 10000006, "target_hektor_annonce_id": "63330", "target_contact_id": "10354642",
                           "contact_label": "M. JEAN TESTJEAN", "job_priority": 18} and r_rm["travail"] == "travail-14",
     "au CLIC : la fonction de l'écran, avec le JETON, NOTRE numéro (comme le sélecteur ; le worker traduit), le libellé, priorité 18")
appels14.clear()
etat14["mandants"] = ["10354641", "10354642"]
voir(refuse(lambda: ges.executer_rattacher_mandant(nouveau_ctx(), p_rm), "déjà mandant") and not ecrits14(),
     "TÉMOIN : rattaché entre la carte et le clic (par l'écran) -> refusé, RIEN envoyé (pas de doublon)")
etat14.pop("mandants")

# 14b — retirer un mandant
RT = {"hektor_annonce_id": "63330", "hektor_contact_id": "10354641"}
appels14.clear()
resume_rt, p_rt = ges.preparer_retirer_mandant(nouveau_ctx(), RT)
voir("Retirer Mme CLAUDE TESTCLAUDE" in resume_rt and "réapparaît" in resume_rt and not ecrits14(),
     "retirer : la carte dit que le lien disparaît tout de suite et revient si Hektor refuse ; rien écrit")
voir(refuse(lambda: ges.preparer_retirer_mandant(nouveau_ctx(), {**RT, "hektor_contact_id": "10354642"}), "n'est pas mandant"),
     "⛔ un contact qui n'est pas mandant du bien : refusé")
etat14["bien"] = {"numero_mandat": "18912"}
voir(refuse(lambda: ges.preparer_retirer_mandant(nouveau_ctx(), RT), "mandat n° 18912"),
     "⛔ LA RÈGLE DE FRÉDÉRIC : mandat numéroté -> refusé, AVEC le numéro (un refus s'explique)")
etat14.pop("bien")
appels14.clear()
ges.executer_retirer_mandant(nouveau_ctx(), p_rt)
c = rpc14("app_unlink_mandant_optimistic")
voir(len(c) == 1 and c[0]["corps"]["target_contact_id"] == "605717" and c[0]["corps"]["target_contact_id"] != "10354641"
     and c[0]["entetes"].get("Authorization") == f"Bearer {JETON}",
     "⛔ au CLIC : le numéro HEKTOR (605717, celui que degroupproprio exige), JAMAIS le nôtre (10354641)")
etat14["refus"] = {"rpc/app_unlink_mandant_optimistic": "mandat_numerote_19001"}
voir(refuse(lambda: ges.executer_retirer_mandant(nouveau_ctx(), p_rt), "le mandat n° 19001 a été généré"),
     "la base refuse « mandat_numerote_19001 » (numéro paru entre-temps dans app_mandat) : traduit en clair, numéro compris")
etat14.pop("refus")
etat14["contact"] = {"10354641": {"hektor_target_id": None}}
voir(refuse(lambda: ges.preparer_retirer_mandant(nouveau_ctx(), RT), "pas encore de numéro chez Hektor"),
     "⛔ un contact sans numéro Hektor : refusé (le retrait ne peut pas lui être envoyé)")
etat14.pop("contact")

# 14c — l'adresse d'un contact
AD = {"hektor_contact_id": "10354641", "adresse": "3 place du Breuil", "code_postal": "42700", "ville": "firminy"}
appels14.clear()
resume_ad, p_ad = ges.preparer_adresse_contact(nouveau_ctx(), AD)
voir("« 1 rue Haute, 42000 Saint-Étienne » → « 3 place du Breuil, 42700 Firminy »" in resume_ad and not ecrits14()
     and p_ad["ville"] == "Firminy",
     "l'adresse : avant → après, la ville écrite par la personne (« firminy ») remplacée par la commune OFFICIELLE")
voir(refuse(lambda: ges.preparer_adresse_contact(nouveau_ctx(), {**AD, "ville": "Unieux"}), "n'est pas une commune du 42700"),
     "⛔ une ville hors du code postal : refusée, avec les communes du code postal (sinon Hektor la perd)")
voir(refuse(lambda: ges.preparer_adresse_contact(nouveau_ctx(), {**AD, "code_postal": ""}), "code postal"),
     "⛔ sans code postal : refusé")
voir(refuse(lambda: ges.preparer_adresse_contact(nouveau_ctx(), {"hektor_contact_id": "10354641", "adresse": "",
                                                                  "code_postal": "42000", "ville": "Saint-Étienne"}), "Rien ne change"),
     "⛔ la même adresse : refusée (rien ne change)")
appels14.clear()
ges.executer_adresse_contact(nouveau_ctx(), p_ad)
c = rpc14("app_edit_contact_optimistic")
voir(len(c) == 1 and c[0]["corps"]["edit_fields"] == {"last_name": "TESTCLAUDE", "address": "3 place du Breuil",
                                                       "postal_code": "42700", "city": "Firminy"}
     and c[0]["corps"]["target_contact_id"] == "10354641" and c[0]["corps"]["debounce_seconds"] == 600,
     "au CLIC : la modification de contact de l'écran, le NOM actuel avec (le worker l'exige), la commune officielle")

# 14d — ajouter un conjoint existant
CJ = {"hektor_contact_id": "10354641", "conjoint_contact_id": "10354642"}
appels14.clear()
resume_cj, p_cj = ges.preparer_ajouter_conjoint(nouveau_ctx(), CJ)
voir("rattaché" not in resume_cj and "rejoint aussi les biens" in resume_cj
     and "(le lien disparaît" in resume_rt and "(il disparaît" not in resume_rt,
     "17/11 : les cartes ne s'accordent plus au masculin (« Mme … est aussi rattaché », « il disparaît » vus en réel) : "
     "phrases neutres, sans deviner le genre")
voir("M. JEAN TESTJEAN le CONJOINT de Mme CLAUDE TESTCLAUDE" in resume_cj and "biens" in resume_cj and not ecrits14(),
     "le conjoint : la carte dit le couple ET le rattachement aux biens de la personne ; rien écrit")
voir(refuse(lambda: ges.preparer_ajouter_conjoint(nouveau_ctx(), {**CJ, "conjoint_contact_id": "10354641"}), "même fiche"),
     "⛔ la même fiche : refusée")
etat14["contact"] = {"10354642": {"couple_json": {"etat": "nomme"}}}
voir(refuse(lambda: ges.preparer_ajouter_conjoint(nouveau_ctx(), CJ), "pas une personne seule"),
     "⛔ une fiche déjà en couple : refusée (les couples existants se travaillent sur la fiche)")
etat14["contact"] = {"10354642": {"nature_fiche": "notaire"}}
voir(refuse(lambda: ges.preparer_ajouter_conjoint(nouveau_ctx(), CJ), "notaire"), "⛔ une fiche notaire : refusée")
etat14.pop("contact")
etat14["cran"] = "admin"
voir(refuse(lambda: ges.preparer_ajouter_conjoint(nouveau_ctx("commercial"), CJ), "pas encore ouvert")
     and ges.preparer_ajouter_conjoint(nouveau_ctx("admin"), CJ)[1] == p_cj,
     "interrupteur `contacts_couples_ajout` = admin : refusé au négociateur, ouvert à l'admin (comme la base)")
etat14.pop("cran")
appels14.clear()
r_cj = ges.executer_ajouter_conjoint(nouveau_ctx(), p_cj)
c = rpc14("app_ajouter_conjoint_optimistic")
voir(len(c) == 1 and c[0]["corps"] == {"target_contact_id": "10354641", "conjoint_contact_id": "10354642"}
     and r_cj["travail"] == "travail-14",
     "au CLIC : la fonction de l'écran, NOS deux numéros")
etat14["reponses"] = {"rpc/app_ajouter_conjoint_optimistic": {"ok": False, "raison": "deja_en_cours"}}
voir(refuse(lambda: ges.executer_ajouter_conjoint(nouveau_ctx(), p_cj), "déjà en cours"),
     "la base refuse SANS lever (ok = false) : la raison est dite en clair, jamais un succès")
etat14.pop("reponses")

# 14e — réaffecter le négociateur [direction]
NG = {"hektor_annonce_id": "63330", "negociateur": "blanchard", "agence": ""}
voir(ges.GESTES["reaffecter_negociateur"].roles == ges.DIRECTION and ges.GESTES["archiver_annonce"].roles == ges.DIRECTION
     and ges.GESTES["activer_estimation"].roles == ges.DIRECTION,
     "réaffecter, archiver, passer en Actif : DIRECTION (la règle de la base : absents de la liste du négociateur)")
voir(refuse(lambda: ges.preparer_reaffecter_negociateur(nouveau_ctx("admin"), NG), "Plusieurs fiches"),
     "deux fiches du même nom (deux agences) : la carte demande laquelle")
appels14.clear()
resume_ng, p_ng = ges.preparer_reaffecter_negociateur(nouveau_ctx("admin"), {**NG, "agence": "yssingeaux"})
voir("Delphine BLANCHARD (GTI Yssingeaux)" in resume_ng and "PEREIRA" in resume_ng and "@" not in resume_ng
     and p_ng["hektor_negociateur_id"] == "45" and not ecrits14(),
     "l'agence départage ; la carte dit l'ancien et le nouveau, sans aucune adresse e-mail")
voir(refuse(lambda: ges.preparer_reaffecter_negociateur(nouveau_ctx("admin"), {**NG, "negociateur": "pereira"}), "déjà confiée à"),
     "⛔ le négociateur actuel : refusé")
voir(refuse(lambda: ges.preparer_reaffecter_negociateur(nouveau_ctx("admin"), {**NG, "negociateur": "inconnu"}), "ACTIF"),
     "⛔ un nom qui n'est pas un négociateur actif chez Hektor : refusé")
appels14.clear()
ges.executer_reaffecter_negociateur(nouveau_ctx("admin"), p_ng)
c = rpc14("app_assign_negotiator_optimistic")
voir(len(c) == 1 and c[0]["corps"]["target_user_id"] == "202" and c[0]["corps"]["job_priority"] == 9
     and c[0]["corps"]["job_payload"] == {"target_hektor_user_label": "Delphine BLANCHARD",
                                          "target_hektor_user_email": "delphine@gti-immobilier.fr",
                                          "target_hektor_negociateur_id": "45", "target_hektor_agence_id": "8",
                                          "target_agency_id_user": "80", "target_agency_label": "GTI Yssingeaux"},
     "au CLIC : le compte Hektor (hektor_user_id) et la charge EXACTE de l'écran")
appels14.clear()
etat14["negos"] = NEGOS14[:1] + NEGOS14[2:]
voir(refuse(lambda: ges.executer_reaffecter_negociateur(nouveau_ctx("admin"), p_ng), "plus actif") and not ecrits14(),
     "TÉMOIN : la fiche n'est plus active chez Hektor au clic -> refusé, RIEN envoyé")
etat14.pop("negos")

# 14f — archiver [direction] / désarchiver
AR = {"hektor_annonce_id": "63330", "cause": "confrere", "precision": "", "prix": "180 000", "confrere": "Agence du Pilat"}
appels14.clear()
resume_ar, p_ar = ges.preparer_archiver_annonce(nouveau_ctx("admin"), AR)
voir("ARCHIVER" in resume_ar and "Vendu par un confrère" in resume_ar and "180 000 €" in resume_ar and "COUPE SA DIFFUSION" in resume_ar
     and not ecrits14(), "archiver : la cause, le prix, et la diffusion coupée sont dits ; rien écrit")
voir(refuse(lambda: ges.preparer_archiver_annonce(nouveau_ctx("admin"), {**AR, "cause": "fatigue"}), "cause")
     and refuse(lambda: ges.preparer_archiver_annonce(nouveau_ctx("admin"), {**AR, "cause": "autre"}), "précision est obligatoire"),
     "⛔ une cause hors de la modale, « autre » sans précision : refusés (comme l'écran)")
etat14["en_cours"] = [{"id": "j"}]
voir(refuse(lambda: ges.preparer_archiver_annonce(nouveau_ctx("admin"), AR), "déjà en cours"),
     "⛔ une action Hektor déjà en cours sur l'annonce : refusé (la garde de l'écran)")
etat14.pop("en_cours")
appels14.clear()
ges.executer_archiver_annonce(nouveau_ctx("admin"), p_ar)
c = rpc14("app_archive_annonce_optimistic")
voir(len(c) == 1 and c[0]["corps"] == {"target_dossier_id": 10000006, "job_priority": 8, "job_payload": {
        "archive_main_choice": "choiceVendu", "archive_sub_choice": "confrere", "archive_other_text": None,
        "archive_price": "180000", "archive_confrere": "Agence du Pilat"}},
     "au CLIC : la charge EXACTE de la modale (motif principal déduit de la cause)")
_, p_ar2 = ges.preparer_archiver_annonce(nouveau_ctx("admin"), {**AR, "cause": "non_renouvele"})
voir(p_ar2["prix"] == "" and p_ar2["confrere"] == "", "un motif « autre » : le prix et le confrère ne partent pas")
voir(refuse(lambda: ges.preparer_desarchiver_annonce(nouveau_ctx(), {"hektor_annonce_id": "63330"}), "n'est pas archivée"),
     "désarchiver un bien vivant : « n'est pas archivée »")
etat14["archives"] = [{"app_archive_id": 1352134, "hektor_annonce_id": 24935, "titre_bien": "Maison archivée"}]
appels14.clear()
resume_da, p_da = ges.preparer_desarchiver_annonce(nouveau_ctx(), {"hektor_annonce_id": "24935"})
ges.executer_desarchiver_annonce(nouveau_ctx(), p_da)
c = rpc14("app_restore_annonce_optimistic")
voir("DÉSARCHIVER" in resume_da and len(c) == 1 and c[0]["corps"] == {"target_dossier_id": 1352134, "job_payload": {}, "job_priority": 8},
     "désarchiver : le numéro de l'INDEX DES ARCHIVES (notre app_dossier_id renommé), charge vide, comme l'écran")
etat14.pop("archives")

# 14g — Estimation -> Actif [direction]
appels14.clear()
resume_ac, p_ac = ges.preparer_activer_estimation(nouveau_ctx("admin"), {"hektor_annonce_id": "63330"})
voir("ESTIMATION à ACTIF" in resume_ac and "DIFFUSABLE" in resume_ac and "n'existe pas" in resume_ac and not ecrits14(),
     "Estimation -> Actif : la carte DIT que Hektor la rend diffusable, et que le retour n'existe pas")
etat14["tete"] = {"statut_annonce": "Actif"}
voir(refuse(lambda: ges.preparer_activer_estimation(nouveau_ctx("admin"), {"hektor_annonce_id": "63330"}), "seul le passage"),
     "⛔ un bien déjà Actif (ou sous offre…) : refusé, seul Estimation -> Actif est offert")
etat14.pop("tete")
appels14.clear()
ges.executer_activer_estimation(nouveau_ctx("admin"), p_ac)
c = rpc14("app_change_annonce_status_optimistic")
charge = c[0]["corps"]["job_payload"] if c else {}
voir(len(c) == 1 and c[0]["corps"]["target_status"] == "active" and charge["target_status"] == "active"
     and charge["numero_dossier"] == "VA9" and charge["apres_vente"] == "actif" and charge["amount"] is None
     and charge["buyer_contact_id"] is None and charge["close_date"] is None and len(charge["transaction_date"]) == 10,
     "au CLIC : la fonction de l'écran, cible « active », la charge de la modale (dossier, date du jour, le reste vide)")
appels14.clear()
etat14["tete"] = {"statut_annonce": "Actif"}
voir(refuse(lambda: ges.executer_activer_estimation(nouveau_ctx("admin"), p_ac), "seul le passage") and not ecrits14(),
     "TÉMOIN : passé en Actif entre la carte et le clic -> refusé, RIEN envoyé")
etat14.pop("tete")

print("15) LE PRIX (17/11, §38) : la direction le CHANGE, le négociateur le DEMANDE")
etat15 = {"demandes": []}


def faux15(methode, url, **kw):
    if methode == "GET" and "/rest/v1/app_diffusion_requests_current" in url:
        appels14.append({"methode": "GET", "chemin": "app_diffusion_requests_current", "entetes": {},
                         "params": dict(kw.get("params") or {}), "corps": None})
        return Reponse(etat15["demandes"])
    return faux14(methode, url, **kw)


requests.get = lambda url, **kw: faux15("GET", url, **kw)
requests.post = lambda url, **kw: faux15("POST", url, **kw)
requests.request = lambda methode, url, **kw: faux15(methode, url, **kw)
PX = {"hektor_annonce_id": "63330", "prix": "95 000"}
voir(ges.GESTES["changer_prix"].roles == ges.DIRECTION
     and "proposer_changer_prix" not in [f.nom for f in cat.fonctions_du_role("commercial")]
     and "proposer_changer_prix" in [f.nom for f in cat.fonctions_du_role("admin")]
     and "proposer_changer_prix" in [f.nom for f in cat.fonctions_du_role("manager")],
     "la carte prix : montrée à l'admin et au manager, JAMAIS au négociateur (lui garde la demande de baisse)")
voir("proposer_demande_direction" in [f.nom for f in cat.fonctions_du_role("commercial")],
     "le négociateur garde la demande de baisse (le chemin de l'écran pour lui)")
appels14.clear()
resume_px, p_px = ges.preparer_changer_prix(nouveau_ctx("admin"), PX)
voir("100 000 € → 95 000 €" in resume_px and "⚠" not in resume_px and "demande de baisse" not in resume_px
     and p_px == {"hektor_annonce_id": 63330, "prix": "95000"} and not ecrits14(),
     "la carte dit l'ancien et le nouveau prix ; rien écrit ; pas d'alerte pour un écart de 5 %")
voir("⚠ écart de 85 %" in ges.preparer_changer_prix(nouveau_ctx("admin"), {**PX, "prix": "15000"})[0],
     "un écart de plus de 30 % (un zéro oublié ?) est SIGNALÉ sur la carte, pas refusé")
voir(refuse(lambda: ges.preparer_changer_prix(nouveau_ctx("admin"), {**PX, "prix": "100000"}), "déjà à")
     and refuse(lambda: ges.preparer_changer_prix(nouveau_ctx("admin"), {**PX, "prix": "cent mille"}), "montant")
     and refuse(lambda: ges.preparer_changer_prix(nouveau_ctx("admin"), {**PX, "prix": "0"}), "montant"),
     "⛔ le même prix, un prix illisible, zéro : refusés")
etat15["demandes"] = [{"id": "dem-baisse"}]
voir("l'accepter ensuite dans Suivi" in ges.preparer_changer_prix(nouveau_ctx("admin"), PX)[0],
     "une demande de baisse en cours : la carte le dit (accepter ne change pas le prix ; ce geste ne traite pas la demande)")
etat15["demandes"] = []
appels14.clear()
ges.executer_changer_prix(nouveau_ctx("admin"), p_px)
c = rpc14("app_edit_annonce_optimistic")
voir(len(c) == 1 and c[0]["entetes"].get("Authorization") == f"Bearer {JETON}"
     and c[0]["corps"] == {"target_dossier_id": 10000006, "edit_fields": {"price": "95000"}, "debounce_seconds": 600},
     "au CLIC : la fonction de l'écran, la clé « price » de l'écran, avec le JETON (la base juge le rôle)")
appels14.clear()
voir(refuse(lambda: ges.executer_changer_prix(nouveau_ctx("commercial"), p_px), "demande de baisse") and not ecrits14(),
     "⛔ TÉMOIN : une carte prix cliquée par un négociateur -> refusée par le serveur, RIEN envoyé (3e verrou)")
etat14["refus"] = {"rpc/app_edit_annonce_optimistic": "prix_sur_demande"}
voir(refuse(lambda: ges.executer_changer_prix(nouveau_ctx("manager"), p_px), "prix_sur_demande"),
     "et si la base refuse quand même (prix_sur_demande), le refus remonte, jamais un succès")
etat14.pop("refus")
etat14["bien"] = {"prix": 95000}
appels14.clear()
voir(refuse(lambda: ges.executer_changer_prix(nouveau_ctx("admin"), p_px), "déjà à") and not ecrits14(),
     "TÉMOIN : le prix posé entre la carte et le clic (par l'écran) -> refusé, RIEN envoyé")
etat14.pop("bien")

print("16) LE PILOTAGE (17/11, §41-42) : Validation et Diffusable, la direction seulement, Hektor doit CONFIRMER")
etat16 = {}
pont16 = []


class FauxPont16:
    def __init__(self, settings):
        pass

    def set_validation(self, app_dossier_id, state, dry_run):
        pont16.append(("validation", app_dossier_id, state, dry_run))
        return {"observed_validation": etat16.get("vue_validation", "oui" if state else "non"),
                "observed_diffusable": etat16.get("diffusable_apres_validation"), "error": etat16.get("erreur_validation")}

    def set_diffusable(self, app_dossier_id, diffusable, dry_run):
        pont16.append(("diffusable", app_dossier_id, diffusable, dry_run))
        return {"observed_diffusable": etat16.get("vue_diffusable", "1" if diffusable else "0")}

    def persist_state(self, app_dossier_id, **k):
        pont16.append(("report", app_dossier_id, k))
        return {}


class FauxAdmin16(FauxAdmin4):
    def assert_admin(self, user):
        pont16.append(("garde", user.id))
        if etat16.get("admin_refuse"):
            raise HTTPException(status_code=403, detail="Acces admin refuse")
        return {"role": "admin"}


ges.SupabaseAdminService = FauxAdmin16
sys.modules["app.services.hektor_bridge"] = types.SimpleNamespace(HektorBridgeService=FauxPont16)
PI = {"hektor_annonce_id": "63330", "validation": "oui", "diffusable": "oui"}
voir(ges.GESTES["pilotage"].roles == ges.DIRECTION
     and "proposer_pilotage" not in [f.nom for f in cat.fonctions_du_role("commercial")]
     and "proposer_pilotage" in [f.nom for f in cat.fonctions_du_role("manager")],
     "le Pilotage : montré à l'admin et au manager, JAMAIS au négociateur (lui garde la demande de validation)")
appels14.clear()
resume_pi, p_pi = ges.preparer_pilotage(nouveau_ctx("admin"), PI)
voir("Validation NON → OUI ; Diffusable NON → OUI" in resume_pi and "DIRECTEMENT chez Hektor" in resume_pi
     and "repartir sur les portails déjà cochés" in resume_pi and "sans validation" not in resume_pi and not ecrits14()
     and p_pi == {"hektor_annonce_id": 63330, "validation": "oui", "diffusable": "oui"},
     "la carte dit avant -> après pour chaque case, que c'est écrit chez Hektor au clic, et que les portails cochés repartent")
voir("sans validation" in ges.preparer_pilotage(nouveau_ctx("admin"), {**PI, "validation": ""})[0],
     "Diffusable OUI sans validation : la carte PRÉVIENT (3 biens sur 13 556 le 17/11), sans refuser")
voir(refuse(lambda: ges.preparer_pilotage(nouveau_ctx("admin"), {**PI, "validation": "", "diffusable": ""}), "Rien à changer")
     and refuse(lambda: ges.preparer_pilotage(nouveau_ctx("admin"), {**PI, "validation": "non", "diffusable": "non"}), "déjà dans cet état")
     and refuse(lambda: ges.preparer_pilotage(nouveau_ctx("admin"), {**PI, "validation": "peut-être"}), "oui, non"),
     "⛔ rien demandé, déjà dans cet état, un choix illisible : refusés")
etat15["demandes"] = [{"id": "dem-val"}]
voir("reste à traiter dans Suivi" in ges.preparer_pilotage(nouveau_ctx("admin"), PI)[0],
     "une demande de validation en cours : la carte dit qu'elle reste à traiter dans Suivi")
etat15["demandes"] = []
pont16.clear()
r_pi = ges.executer_pilotage(nouveau_ctx("admin"), p_pi)
voir(pont16 == [("garde", UID), ("validation", 10000006, 1, False), ("diffusable", 10000006, True, False),
                ("report", 10000006, {"validation_diffusion_state": "oui", "diffusable": True})]
     and r_pi["fait"] == ["validation", "diffusable"],
     "au CLIC : la garde des routes (admin / manager), la validation PUIS le diffusable par le pont de l'écran (jamais à blanc), "
     "puis la recopie chez nous de ce que Hektor montre")
etat16["diffusable_apres_validation"] = "1"
pont16.clear()
ges.executer_pilotage(nouveau_ctx("admin"), p_pi)
voir([x[0] for x in pont16] == ["garde", "validation", "report"],
     "si Hektor rend déjà le bien diffusable en le validant : pas de second appel (rien d'inutile chez Hektor)")
etat16.clear()
etat16["vue_diffusable"] = "0"
pont16.clear()
voir(refuse(lambda: ges.executer_pilotage(nouveau_ctx("admin"), p_pi), "n'a pas confirmé Diffusable")
     and ("report", 10000006, {"validation_diffusion_state": "oui", "diffusable": False}) in pont16,
     "⛔ Hektor ne confirme pas Diffusable : la carte le DIT (jamais un succès), et l'app recopie ce que Hektor montre")
etat16.clear()
etat16["vue_validation"] = None
voir(refuse(lambda: ges.executer_pilotage(nouveau_ctx("admin"), {**p_pi, "diffusable": ""}), "pas pu être relue"),
     "⛔ la validation partie mais la fiche Hektor pas relue : refusé (une relecture ratée n'est jamais un vert)")
etat16.clear()
etat16["erreur_validation"] = "Annonce verrouillee"
pont16.clear()
voir(refuse(lambda: ges.executer_pilotage(nouveau_ctx("admin"), p_pi), "Annonce verrouillee")
     and "diffusable" not in [x[0] for x in pont16],
     "Hektor refuse la validation : on s'arrête là, le diffusable n'est pas tenté")
etat16.clear()
pont16.clear()
voir(refuse(lambda: ges.executer_pilotage(nouveau_ctx("commercial"), p_pi), "réservé à la direction") and pont16 == [],
     "⛔ TÉMOIN : une carte Pilotage cliquée par un négociateur -> refusée, RIEN chez Hektor (3e verrou)")
etat16["admin_refuse"] = True
voir(refuse(lambda: ges.executer_pilotage(nouveau_ctx("manager"), p_pi), "Acces admin refuse")
     and [x[0] for x in pont16] == ["garde"],
     "la garde des routes refuse (profil inactif…) : RIEN chez Hektor")
etat16.clear()
etat14["tete"] = {"diffusable": "1"}
etat14["bien"] = {"validation_diffusion_state": "valide"}
pont16.clear()
voir(refuse(lambda: ges.executer_pilotage(nouveau_ctx("admin"), p_pi), "déjà dans cet état") and pont16 == [],
     "TÉMOIN : validé et diffusable entre la carte et le clic (par l'écran) -> refusé, RIEN chez Hektor")
etat14.pop("tete")
etat14.pop("bien")

print("18) AJOUTER UNE PHOTO avec des fichiers du TROMBONE (17/11, §54-55) : le chemin de l'écran, copie au coffre")
JOINTS = {
    "a" * 32: {"id": "a" * 32, "nom": "facade.jpg", "type": "image/jpeg", "libelle": "photo JPEG", "taille": 2400000,
               "chemin": f"temp/assistant/{UID}/{'a' * 32}/facade.jpg"},
    "b" * 32: {"id": "b" * 32, "nom": "jardin.png", "type": "image/png", "libelle": "image PNG", "taille": 900000,
               "chemin": f"temp/assistant/{UID}/{'b' * 32}/jardin.png"},
    "c" * 32: {"id": "c" * 32, "nom": "plan.pdf", "type": "application/pdf", "libelle": "PDF", "taille": 50000,
               "chemin": f"temp/assistant/{UID}/{'c' * 32}/plan.pdf"},
    "d" * 32: {"id": "d" * 32, "nom": "vue.webp", "type": "image/webp", "libelle": "image WebP", "taille": 50000,
               "chemin": f"temp/assistant/{UID}/{'d' * 32}/vue.webp"},
}
etat18 = {"copie_refus": set()}
copies18 = []


def faux_decrire(settings, user_id, numero):
    if user_id != UID or numero not in JOINTS or numero in etat18.get("disparus", set()):
        raise ges.fichiers_service.RefusFichier("Ce fichier n'est pas (ou plus) dans la conversation : joins-le à nouveau.")
    return dict(JOINTS[numero])


def faux_copier(settings, source, destination):
    if source in etat18["copie_refus"]:
        raise ges.fichiers_service.RefusFichier("Le coffre n'a pas copié le fichier (500).")
    copies18.append((source, destination))


ges.fichiers_service.decrire = faux_decrire
ges.fichiers_service.copier = faux_copier


def faux18(methode, url, **kw):
    if methode == "POST" and url.endswith("/rest/v1/app_console_job"):
        appels14.append({"methode": "POST", "chemin": "app_console_job", "entetes": dict(kw.get("headers") or {}),
                         "params": {}, "corps": kw.get("json")})
        return Reponse(kw.get("json"))
    return faux15(methode, url, **kw)


requests.get = lambda url, **kw: faux18("GET", url, **kw)
requests.post = lambda url, **kw: faux18("POST", url, **kw)
requests.request = lambda methode, url, **kw: faux18(methode, url, **kw)
PH = {"hektor_annonce_id": "63330", "fichiers": f"fichier:{'a' * 32} | {'b' * 32}"}
voir("proposer_ajouter_photo" in [f.nom for f in cat.fonctions_du_role("commercial")],
     "la carte est ouverte à tous les rôles (la base juge : le négociateur sur SES biens)")
appels14.clear()
resume_ph, p_ph = ges.preparer_ajouter_photo(nouveau_ctx(), PH)
voir("Ajouter 2 photos à l'annonce 63330" in resume_ph and "« facade.jpg », « jardin.png »" in resume_ph
     and "VISIBLES" in resume_ph and "en dernier" in resume_ph and "traitement de nuit" in resume_ph and not ecrits14()
     and p_ph == {"hektor_annonce_id": 63330, "fichiers": ["a" * 32, "b" * 32]},
     "la carte nomme les photos, dit visibles / en dernier / la nuit ; rien écrit ; « fichier: » toléré")
voir(refuse(lambda: ges.preparer_ajouter_photo(nouveau_ctx(), {**PH, "fichiers": f"{'a' * 32}|{'c' * 32}"}), "plan.pdf")
     and refuse(lambda: ges.preparer_ajouter_photo(nouveau_ctx(), {**PH, "fichiers": "d" * 32}), "vue.webp"),
     "⛔ un PDF ou un WebP : refusés, en les nommant (JPEG / PNG seulement)")
voir(refuse(lambda: ges.preparer_ajouter_photo(nouveau_ctx(), {**PH, "fichiers": "e" * 32}), "joins-le à nouveau")
     and refuse(lambda: ges.preparer_ajouter_photo(nouveau_ctx(), {**PH, "fichiers": ""}), "numéro des fichiers"),
     "⛔ un fichier qui n'est pas (ou plus) dans SON trombone, ou aucun : refusés")
voir(refuse(lambda: ges.preparer_ajouter_photo(nouveau_ctx(), {**PH, "fichiers": "|".join(f"{i:032x}" for i in range(21))}), "20 photos"),
     "⛔ plus de 20 photos : refusé (le plafond d'une sélection à l'écran)")
etat14["tete"] = {"negociateur_email": "", "commercial_id": ""}
voir(refuse(lambda: ges.preparer_ajouter_photo(nouveau_ctx(), PH), "pas de négociateur"),
     "⛔ un bien sans négociateur : refusé (le worker ne saurait pas sous quelle identité écrire)")
etat14.pop("tete")
appels14.clear()
copies18.clear()
r_ph = ges.executer_ajouter_photo(nouveau_ctx(), p_ph)
travaux = [a for a in appels14 if a["chemin"] == "app_console_job"]
lignes = rpc14("app_console_creer_photo_optimistic")
voir(len(travaux) == 2 and all(t["entetes"].get("Authorization") == f"Bearer {JETON}" for t in travaux)
     and travaux[0]["corps"][0]["job_type"] == "upload_hektor_photo" and travaux[0]["corps"][0]["requested_by"] == UID
     and travaux[0]["corps"][0]["payload_json"]["visible"] is True
     and travaux[0]["corps"][0]["payload_json"]["temp_storage_path"] == f"temp/photos/{travaux[0]['corps'][0]['id']}/facade.jpg",
     "au CLIC : UN travail par photo, avec le JETON (la règle d'insertion juge les droits), VISIBLE, à la place de l'écran")
voir(copies18 == [(JOINTS["a" * 32]["chemin"], travaux[0]["corps"][0]["payload_json"]["temp_storage_path"]),
                  (JOINTS["b" * 32]["chemin"], travaux[1]["corps"][0]["payload_json"]["temp_storage_path"])],
     "le fichier est COPIÉ au coffre du trombone vers la place du travail (pas renvoyé de l'ordinateur)")
ordre = [a["chemin"] for a in appels14 if a["methode"] == "POST"]
voir(len(lignes) == 2 and lignes[0]["corps"]["target_job_id"] == travaux[0]["corps"][0]["id"] and lignes[0]["corps"]["legende"] is None
     and ordre.index("app_console_job") < ordre.index("rpc/app_console_creer_photo_optimistic")
     and r_ph["travaux"] == [t["corps"][0]["id"] for t in travaux] and r_ph["envoi"] == "en cours",
     "l'ordre de l'écran : le travail, la copie, PUIS notre ligne ; le résultat dit « envoi en cours »")
appels14.clear()
copies18.clear()
etat18["copie_refus"] = {JOINTS["a" * 32]["chemin"]}
r_ph2 = ges.executer_ajouter_photo(nouveau_ctx(), p_ph)
solde = rpc14("app_console_fail_own_pending_job")
voir(len(solde) == 1 and r_ph2["echecs"] and "facade.jpg" in r_ph2["echecs"][0] and len(r_ph2["travaux"]) == 1
     and len(rpc14("app_console_creer_photo_optimistic")) == 1,
     "une copie ratée : SON travail est soldé en échec (comme l'écran), pas de ligne pour elle, l'autre photo part")
etat18["copie_refus"] = {JOINTS["a" * 32]["chemin"], JOINTS["b" * 32]["chemin"]}
voir(refuse(lambda: ges.executer_ajouter_photo(nouveau_ctx(), p_ph), "Aucune photo"),
     "toutes les copies ratées : refusé, jamais un succès")
etat18["copie_refus"] = set()
appels14.clear()
etat18["disparus"] = {"a" * 32}
voir(refuse(lambda: ges.executer_ajouter_photo(nouveau_ctx(), p_ph), "joins-le à nouveau") and not ecrits14(),
     "TÉMOIN : un fichier retiré du trombone entre la carte et le clic -> refusé, RIEN posé")
etat18.pop("disparus")

print("19) DÉPOSER DES DOCUMENTS = ouvrir la FENÊTRE GED garnie (17/11, §57-59, chemin A) : rien n'est écrit ici")
liens19 = []


def faux_lien(settings, chemin):
    if chemin in etat18.get("lien_refus", set()):
        raise ges.fichiers_service.RefusFichier("Le coffre n'a pas donné de lien (500).")
    liens19.append(chemin)
    return f"https://coffre.test/signe/{chemin}?t=10min"


ges.fichiers_service.lien_lecture = faux_lien
DD = {"hektor_annonce_id": "63330", "fichiers": f"fichier:{'c' * 32} | {'a' * 32}"}
voir("proposer_deposer_documents" in [f.nom for f in cat.fonctions_du_role("commercial")],
     "la carte est ouverte à tous les rôles (c'est la fenêtre qui envoie, avec les droits de la personne)")
etat14["cran"] = "on"
appels14.clear()
resume_dd, p_dd = ges.preparer_deposer_documents(nouveau_ctx(), DD)
voir("fenêtre de dépôt GED de l'annonce 63330" in resume_dd and "« plan.pdf », « facade.jpg »" in resume_dd
     and "« Envoyer » DANS la fenêtre" in resume_dd and not ecrits14()
     and p_dd == {"hektor_annonce_id": 63330, "fichiers": ["c" * 32, "a" * 32]},
     "la carte nomme les fichiers, dit que RIEN ne part avant « Envoyer » dans la fenêtre ; rien écrit ; PDF et photo admis")
etat14["cran"] = "admin"
voir(refuse(lambda: ges.preparer_deposer_documents(nouveau_ctx(), DD), "pas encore ouverte")
     and ges.preparer_deposer_documents(nouveau_ctx("admin"), DD)[1] == p_dd,
     "⛔ fenêtre GED au cran admin : refusée au négociateur, ouverte à l'admin (la même règle que l'écran)")
etat14["cran"] = "off"
voir(refuse(lambda: ges.preparer_deposer_documents(nouveau_ctx("admin"), DD), "pas encore ouverte"),
     "⛔ fenêtre GED éteinte : refusée à tous, même l'admin (on n'ouvre rien)")
etat14["cran"] = "on"
voir(refuse(lambda: ges.preparer_deposer_documents(nouveau_ctx(), {**DD, "fichiers": "e" * 32}), "joins-le à nouveau")
     and refuse(lambda: ges.preparer_deposer_documents(nouveau_ctx(), {**DD, "fichiers": ""}), "numéro des fichiers"),
     "⛔ un fichier qui n'est pas (ou plus) dans SON trombone, ou aucun : refusés")
etat14["tete"] = {"negociateur_email": "", "commercial_id": ""}
voir(refuse(lambda: ges.preparer_deposer_documents(nouveau_ctx(), DD), "pas de négociateur"),
     "⛔ un bien sans négociateur : refusé")
etat14.pop("tete")
appels14.clear()
liens19.clear()
r_dd = ges.executer_deposer_documents(nouveau_ctx(), p_dd)
voir(r_dd["ouvrir"] == "depot_ged" and r_dd["hektor_annonce_id"] == 63330 and r_dd["app_dossier_id"] == B14["app_dossier_id"]
     and [f["nom"] for f in r_dd["fichiers"]] == ["plan.pdf", "facade.jpg"]
     and [f["type"] for f in r_dd["fichiers"]] == ["application/pdf", "image/jpeg"]
     and liens19 == [JOINTS["c" * 32]["chemin"], JOINTS["a" * 32]["chemin"]] and not ecrits14(),
     "au CLIC : des liens de LECTURE courts vers le trombone, le bien et ses fichiers -- et RIEN d'écrit (ni travail, ni ligne)")
etat18["lien_refus"] = {JOINTS["a" * 32]["chemin"]}
voir(refuse(lambda: ges.executer_deposer_documents(nouveau_ctx(), p_dd), "pas donné de lien"),
     "un lien refusé par le coffre : la carte échoue, jamais une fenêtre à moitié garnie")
etat18.pop("lien_refus")
etat14["cran"] = "admin"
voir(refuse(lambda: ges.executer_deposer_documents(nouveau_ctx(), p_dd), "pas encore ouverte"),
     "TÉMOIN : la fenêtre GED refermée au négociateur entre la carte et le clic -> refusé au clic")
etat14["cran"] = "on"
etat18["disparus"] = {"c" * 32}
voir(refuse(lambda: ges.executer_deposer_documents(nouveau_ctx(), p_dd), "joins-le à nouveau"),
     "TÉMOIN : un fichier retiré du trombone entre la carte et le clic -> refusé")
etat18.pop("disparus")
etat14.pop("cran")

print("20) LES PIÈCES JOINTES de l'e-mail au client (18/11, §61-62) : les pièces des biens liés, le trombone, les sensibles marquées")
ges.SupabaseAdminService, ges.GoogleWorkspaceService, ges.EmailTrackingService = FauxAdmin, FauxGoogle, FauxSuivi
DOC_CNI, DOC_PRET, DOC_DPE, DOC_MAL = "d1" * 18, "d2" * 18, "d3" * 18, "d4" * 18
etat20: dict = {}
appels20: list = []


def reset20(**kw):
    etat20.clear()
    etat20.update({
        "relations": [{"app_dossier_id": 88, "hektor_annonce_id": 50001, "titre_bien": "Ancien bien vendu", "is_active_annonce": False},
                      {"app_dossier_id": 77, "hektor_annonce_id": 63289, "titre_bien": "Maison La Chaise-Dieu", "is_active_annonce": True},
                      {"app_dossier_id": 77, "hektor_annonce_id": 63289, "titre_bien": "Maison La Chaise-Dieu", "is_active_annonce": True}],
        "documents": [
            {"id": DOC_CNI, "app_dossier_id": 77, "hektor_annonce_id": "63289", "document_name": "scan 12.pdf",
             "mime_type": "application/pdf", "file_size": 800000, "storage_bucket": "hektor-console-documents", "storage_path": "77/scan12.pdf"},
            {"id": DOC_PRET, "app_dossier_id": 77, "hektor_annonce_id": "63289", "document_name": "Offre de prêt durand@exemple.fr.pdf",
             "mime_type": "application/pdf", "file_size": 1200000, "storage_bucket": "hektor-console-documents", "storage_path": "77/pret.pdf"},
            {"id": DOC_DPE, "app_dossier_id": 77, "hektor_annonce_id": "63289", "document_name": "identite du bien - DPE.pdf",
             "mime_type": "application/pdf", "file_size": 300000, "storage_bucket": "hektor-console-documents", "storage_path": "77/dpe.pdf"},
            {"id": DOC_MAL, "app_dossier_id": 88, "hektor_annonce_id": "50001", "document_name": "Plan.pdf",
             "mime_type": "application/pdf", "file_size": 9000000, "storage_bucket": "hektor-console-documents", "storage_path": "88/plan.pdf"}],
        "photos": [
            {"app_dossier_id": 77, "hektor_annonce_id": "63289", "hektor_photo_id": "5001", "filename": "facade", "legend": "",
             "url_hd": "https://hektor.test/facade.jpg", "url_preview": "", "visible": True,
             "derives_json": {"w1600": {"chemin": "63289/x/w1600.jpg", "octets": 400000}}},
            {"app_dossier_id": 77, "hektor_annonce_id": "63289", "hektor_photo_id": "5002", "filename": "cave.png", "legend": "",
             "url_hd": "https://hektor.test/cave.png", "url_preview": "", "visible": False, "derives_json": None}],
        "classement": [{"app_console_document_id": DOC_CNI, "type_code": "justif.identite"},
                       {"app_console_document_id": DOC_DPE, "type_code": "diag.dpe"}],
        "types_sensibles": [{"code": "justif.identite"}, {"code": "justif.rib"}, {"code": "transaction.financement"}],
        "signe_refus": set()})
    etat20.update(kw)


def faux20(methode, url, headers=None, params=None, json=None, **_):
    appels20.append({"methode": methode, "url": url, "entetes": dict(headers or {}), "params": dict(params or {}), "corps": json})
    if "/storage/v1/object/sign/" in url:
        chemin = url.split("/storage/v1/object/sign/hektor-console-documents/", 1)[1]
        if chemin in etat20["signe_refus"]:
            return Reponse({"message": "Object not found"}, status=400)
        return Reponse({"signedURL": f"/object/sign/hektor-console-documents/{chemin}?token=t15"})
    chemin = url.split("/rest/v1/", 1)[1]
    p_ = params or {}
    if methode == "GET" and chemin == "app_contacts_current":
        return Reponse(etat["contact"])
    if methode == "GET" and chemin == "app_contact_relations_current":
        return Reponse(etat20["relations"])
    if methode == "GET" and chemin in {"app_console_document", "app_console_photo"}:
        voulus = p_["app_dossier_id"][4:-1].split(",")
        lignes = etat20["documents" if chemin == "app_console_document" else "photos"]
        return Reponse([x for x in lignes if str(x["app_dossier_id"]) in voulus])
    if methode == "GET" and chemin == "app_ged_classement":
        return Reponse(etat20["classement"])
    if methode == "GET" and chemin == "app_ged_type":
        return Reponse(etat20["types_sensibles"])
    if methode == "POST" and chemin == "rpc/app_console_touch_document":
        return Reponse(None, status=204)
    return Reponse([], status=404)


def faux_lien20(settings, chemin, secondes=600):
    appels20.append({"methode": "LIEN", "url": chemin, "secondes": secondes})
    return f"https://coffre.test/signe/{chemin}?t={secondes}"


requests.get = lambda url, **kw: faux20("GET", url, **kw)
requests.post = lambda url, **kw: faux20("POST", url, **kw)
requests.request = lambda methode, url, **kw: faux20(methode, url, **kw)
ges.fichiers_service.lien_lecture = faux_lien20
EM = {"hektor_contact_id": "606202", "objet": "Les documents", "texte": "Bonjour,\nvoici les pièces.\nPaul"}

voir(all(ges._sensible_par_nom(n) for n in ("CNI recto.jpg", "Carte d'identité M. Durand.pdf", "Livret de famille.pdf", "RIB.pdf",
                                            "Offre de prêt CA.pdf", "fiche renseignements acquéreur.pdf", "Passeport.jpg"))
     and not any(ges._sensible_par_nom(n) for n in ("DPE.pdf", "Plan maison.pdf", "Compromis signé.pdf", "Mandat de vente.pdf",
                                                    "Taxe foncière 2025.pdf", "facade.jpg")),
     "le NOM dit sensible pour identité, état civil, RIB, financement, renseignements ; pas pour un DPE, un plan, un compromis")
voir("lire_pieces_jointes" in [f.nom for f in cat.fonctions_du_role("commercial")]
     and "pieces" in ges.GESTES["email_client"].parametres["properties"],
     "la lecture des pièces est ouverte à tous les rôles ; la carte e-mail au client prend des pièces")
reset()
reset20()
appels20.clear()
lu = ges.lire_pieces_jointes(nouveau_ctx(), {"hektor_contact_id": "606202"})
docs = {d["piece"]: d for d in lu["biens"][0]["documents"]}
voir([b["annonce"] for b in lu["biens"]] == [63289, 50001] and len(lu["biens"]) == 2,
     "les biens LIÉS au contact, un par dossier, les biens actifs d'abord (comme la fenêtre de l'écran)")
voir(docs[f"doc:{DOC_CNI}"]["sensible"] and docs[f"doc:{DOC_PRET}"]["sensible"] and not docs[f"doc:{DOC_DPE}"]["sensible"],
     "⭐ sensible : le TYPE GED quand il existe (un « scan 12 » classé identité est sensible, un DPE nommé « identité… » ne l'est "
     "pas), sinon le NOM (une offre de prêt)")
voir([p["masquee"] for p in lu["biens"][0]["photos"]] == [False, True] and CLIENT not in json.dumps(lu),
     "la photo masquée est marquée ; ⛔ l'adresse e-mail d'un client dans un nom de document ne part pas au modèle")
voir(not [a for a in appels20 if a["methode"] != "GET"], "LIRE n'écrit rien et ne signe rien")

appels20.clear()
resume20, p20 = ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": f"doc:{DOC_CNI} | photo:5001 | photo:5002 | fichier:{'c' * 32}"})
voir("4 pièces jointes" in resume20 and "« scan 12.pdf » (document, 781 Ko, ⚠ PIÈCE SENSIBLE)" in resume20
     and "« facade.jpg » (photo, 391 Ko)" in resume20 and "« cave.png » (photo, photo masquée)" in resume20
     and "« plan.pdf » (fichier joint, 49 Ko)" in resume20 and "Une pièce SENSIBLE part chez le client" in resume20,
     "la carte NOMME chaque pièce, avec sa taille, la photo masquée et la pièce SENSIBLE marquées, et un avertissement")
voir(p20["pieces"] == [f"doc:{DOC_CNI}", "photo:5001", "photo:5002", f"fichier:{'c' * 32}"] and CLIENT not in resume20 + json.dumps(p20)
     and not [a for a in appels20 if a["methode"] != "GET"],
     "la carte garde les numéros ; PROPOSER ne signe rien, n'écrit rien, et l'adresse du client n'y est pas")
_, p_sans = ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": ""})
voir("pieces" not in p_sans and "jointe" not in ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": ""})[0],
     "sans pièce : la carte est celle d'avant, à l'identique")
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": "doc:inconnu"}), "biens liés à ce contact")
     and refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": "photo:9999"}), "biens liés à ce contact"),
     "⛔ une pièce qui n'est pas sur un bien lié à CE contact : refusée")
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": DOC_CNI}), "doc:…")
     and refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": f"fichier:{'e' * 32}"}), "joins-le à nouveau"),
     "⛔ un numéro sans genre, ou un fichier qui n'est pas dans SON trombone : refusés")
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": "|".join(f"photo:{i}" for i in range(11))}), "10 pièces"),
     "⛔ plus de 10 pièces : refusé (le plafond de l'envoi)")
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": f"doc:{DOC_MAL}"}), "plus de 8 Mo"),
     "⛔ une pièce de plus de 8 Mo : refusée (le plafond de l'envoi)")
reset20(documents=[{**d, "file_size": 7000000} for d in etat20["documents"]])
voir(refuse(lambda: ges.preparer_email_client(nouveau_ctx(), {**EM, "pieces": f"doc:{DOC_CNI}|doc:{DOC_PRET}|doc:{DOC_DPE}"}), "18 Mo"),
     "⛔ plus de 18 Mo en tout : refusé")

reset20()
google.clear()
appels20.clear()
r20 = ges.executer_email_client(nouveau_ctx(), p20)
envoi = next(g for g in google if g["quoi"] == "envoyer")
pj = envoi["attachments"]
signe = [a for a in appels20 if "/storage/v1/object/sign/" in a["url"]]
voir(envoi["to"] == [CLIENT] and [a["filename"] for a in pj] == ["scan 12.pdf", "facade.jpg", "cave.png", "plan.pdf"]
     and pj[0]["url"] == "https://x.supabase.co/storage/v1/object/sign/hektor-console-documents/77/scan12.pdf?token=t15"
     and pj[1]["url"] == "https://x.supabase.co/storage/v1/object/public/gti-photo/63289/x/w1600.jpg"
     and pj[2]["url"] == "https://hektor.test/cave.png" and pj[2]["mimeType"] == "image/png"
     and pj[3]["url"] == f"https://coffre.test/signe/{JOINTS['c' * 32]['chemin']}?t=900",
     "au CLIC : de VRAIS fichiers joints (le serveur les télécharge) -- le document signé, notre grande photo, la masquée, le trombone")
voir(len(signe) == 1 and signe[0]["entetes"]["Authorization"] == "Bearer " + JETON and signe[0]["corps"] == {"expiresIn": 900}
     and [a["corps"] for a in appels20 if a["url"].endswith("rpc/app_console_touch_document")] == [{"document_id": DOC_CNI}],
     "⛔ le document est signé avec le JETON de la personne (la règle du coffre juge), 15 min, puis marqué lu -- comme l'écran")
voir(r20["pieces_jointes"] == [{"piece": f"doc:{DOC_CNI}", "nom": "scan 12.pdf", "sensible": True, "masquee": False},
                               {"piece": "photo:5001", "nom": "facade.jpg", "sensible": False, "masquee": False},
                               {"piece": "photo:5002", "nom": "cave.png", "sensible": False, "masquee": True},
                               {"piece": f"fichier:{'c' * 32}", "nom": "plan.pdf", "sensible": False, "masquee": False}]
     and CLIENT not in json.dumps(r20) and not any("url" in x for x in r20["pieces_jointes"]),
     "⭐ LA TRACE (comme le journal de la GED) : ce qui est parti, sensible ou masqué -- sans adresse ni lien")
reset20(documents=[d for d in etat20["documents"] if d["id"] != DOC_CNI])
google.clear()
voir(refuse(lambda: ges.executer_email_client(nouveau_ctx(), p20), "biens liés à ce contact") and not google[1:],
     "TÉMOIN : un document retiré entre la carte et le clic -> refusé AU CLIC, rien envoyé")
reset20(relations=[])
google.clear()
voir(refuse(lambda: ges.executer_email_client(nouveau_ctx(), p20), "biens liés à ce contact")
     and not [g for g in google if g["quoi"] == "envoyer"],
     "TÉMOIN : le contact délié du bien entre la carte et le clic -> refusé, rien envoyé")
reset20(signe_refus={"77/scan12.pdf"})
google.clear()
voir(refuse(lambda: ges.executer_email_client(nouveau_ctx(), p20), "pas laissé lire")
     and not [g for g in google if g["quoi"] == "envoyer"],
     "⛔ le coffre refuse de signer pour CETTE personne -> refusé, jamais un e-mail à moitié joint")
reset20()
google.clear()
ges.executer_email_client(nouveau_ctx(), p_sans)
voir(next(g for g in google if g["quoi"] == "envoyer")["attachments"] is None,
     "TÉMOIN : une carte sans pièce (et les cartes d'avant) part sans pièce jointe, comme avant")

print("21) CRÉER UNE ESTIMATION / UNE ANNONCE = ouvrir la FENÊTRE DE CRÉATION pré-remplie (18/11, §65-66, marche 6a)")
requests.get = lambda url, **kw: faux14("GET", url, **kw)
requests.post = lambda url, **kw: faux14("POST", url, **kw)
requests.request = lambda methode, url, **kw: faux14(methode, url, **kw)
ges.fichiers_service.lien_lecture = faux_lien
CR = {"genre": "estimation",
      "cases": [{"cle": "propertyType", "valeur": "maison"}, {"cle": "price", "valeur": "245 000 €"},
                {"cle": "surface", "valeur": "125 m²"}, {"cle": "roomCount", "valeur": "5"},
                {"cle": "bedroomCount", "valeur": "3"}, {"cle": "landSurface", "valeur": "900"},
                {"cle": "address", "valeur": "12 rue des Tilleuls"}, {"cle": "postalCode", "valeur": "42 700"},
                {"cle": "city", "valeur": "Firminy"}, {"cle": "garden", "valeur": "Oui"}, {"cle": "dpeValue", "valeur": "D"},
                {"cle": "note", "valeur": ""}],
      "composition": [{"type": "séjour", "surface": "35,5 m²", "etage": "RDC", "detail": ""}],
      "hektor_contact_id": "10354641", "negociateur": "", "fichiers": f"fichier:{'a' * 32}|{'d' * 32}"}
voir(ges.GESTES["ouvrir_creation_annonce"].roles == cat.TOUS_LES_ROLES
     and "proposer_ouvrir_creation_annonce" in [f.nom for f in cat.fonctions_du_role("commercial")],
     "ouverte aux rôles qui ont le bouton « Nouvelle annonce » à l'écran (admin, manager, commercial)")
voir(not [c for c in ges.CASES_CREATION if c.startswith("mandant")] and "agency" not in ges.CASES_CREATION
     and len(ges.CASES_CREATION) == len(ges._CASES_DU_SCAN) - 18 and set(ges.CASES_CREATION) <= set(ges.LIBELLES_CASES),
     "⛔ les cases = celles du SCAN, SANS les 16 cases du mandant (coordonnées) ni agence / négociateur ; chacune a son libellé")
appels14.clear()
resume_cr, p_cr = ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), CR)
voir("création d'une estimation" in resume_cr and "Prix 245 000 €" in resume_cr and "Surface habitable 125 m²" in resume_cr
     and "Mme CLAUDE TESTCLAUDE (contact existant)" in resume_cr and "« facade.jpg », « vue.webp »" in resume_cr
     and "« Créer » DANS la fenêtre" in resume_cr and not ecrits14(),
     "la carte dit chaque valeur, le mandant existant, la fiche scannée, et que RIEN n'est créé avant « Créer » ; rien écrit")
voir(p_cr["cases"] == {"propertyType": "maison", "price": "245000", "surface": "125", "roomCount": "5", "bedroomCount": "3",
                       "landSurface": "900", "address": "12 rue des Tilleuls", "postalCode": "42700", "city": "Firminy",
                       "garden": "oui", "dpeValue": "D"}
     and p_cr["composition"] == [{"type": "séjour", "surface": "35.5", "etage": "RDC", "detail": ""}]
     and p_cr["hektor_contact_id"] == "10354641" and p_cr["fichiers"] == ["a" * 32, "d" * 32] and "negociateur" not in p_cr,
     "les valeurs RANGÉES : nombres nus, oui/non, code postal sans espace ; une case vide n'est pas rangée")
voir("@" not in resume_cr and "@" not in json.dumps(p_cr) and "pereira" not in json.dumps(p_cr).lower(),
     "⛔ aucune adresse e-mail ni dans la carte ni dans ses paramètres (le mandant par son numéro et son nom)")
for mauvais, morceau, quoi in (
        ({"cle": "mandantEmail", "valeur": "x@y.fr"}, "n'est pas une case", "l'e-mail d'un mandant"),
        ({"cle": "mandantPhone", "valeur": "0601020304"}, "n'est pas une case", "le téléphone d'un mandant"),
        ({"cle": "note", "valeur": "écrire à jean@exemple.fr"}, "adresse e-mail", "une adresse glissée dans une note"),
        ({"cle": "postalCode", "valeur": "427"}, "5 chiffres", "un code postal faux"),
        ({"cle": "price", "valeur": "vers deux cent mille"}, "pas un nombre", "un prix en lettres (le modèle doit mettre 200000)"),
        ({"cle": "pool", "valeur": "peut-être"}, "oui ou non", "un oui/non flou")):
    voir(refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), {**CR, "cases": [mauvais]}), morceau),
         f"⛔ refusé : {quoi}")
voir(refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), {**CR, "genre": "vente"}), "estimation ou d'une annonce")
     and refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), {"genre": "annonce", "cases": [], "composition": [],
                                                                               "hektor_contact_id": "", "negociateur": "",
                                                                               "fichiers": ""}), "Rien à pré-remplir"),
     "⛔ ni estimation ni annonce : demander ; une carte vide : refusée")
voir(refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), {**CR, "hektor_contact_id": "99"}), "pas parmi"),
     "⛔ un mandant que la personne ne peut pas voir (relu avec SON jeton) : refusé")
etat14["contact"] = {"10354641": {"archive": True}}
voir(refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), CR), "archivé"), "⛔ un mandant archivé : refusé")
etat14.pop("contact")
voir(refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), {**CR, "fichiers": f"{'a' * 32}|{'c' * 32}"}), "JPEG, PNG ou WebP"),
     "⛔ un PDF n'est pas une photo de fiche : refusé (le scan ne lit que des images)")
ges.MAX_PAGES_SCAN = 1
voir(refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), CR), "photos au plus"), "⛔ trop de pages pour le scan : refusé")
ges.MAX_PAGES_SCAN = 5
voir(refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx(), {**CR, "negociateur": "pereira"}), "c'est toi"),
     "⛔ un COMMERCIAL ne choisit pas le négociateur : c'est lui (la fenêtre le pose)")
_, p_dir = ges.preparer_ouvrir_creation_annonce(nouveau_ctx("admin"), {**CR, "negociateur": "pereira"})
voir(p_dir["negociateur"] == {"hektor_negociateur_id": "12", "nom": "Paulo PEREIRA"}
     and refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx("admin"), {**CR, "negociateur": "blanchard"}), "Plusieurs")
     and refuse(lambda: ges.preparer_ouvrir_creation_annonce(nouveau_ctx("admin"), {**CR, "negociateur": "inconnu"}), "ACTIF"),
     "la DIRECTION nomme un négociateur ACTIF chez Hektor (deux homonymes : demander lequel)")
f_cr = ges.fiche_carte(p_cr, "ouvrir_creation_annonce")
voir(f_cr["titre"] == "Maison de 125 m² à Firminy" and f_cr["genre"] == "estimation"
     and [c["libelle"] for c in f_cr["chiffres"]] == ["Prix", "Surface habitable", "Pièces", "Terrain"]
     and f_cr["chiffres"][2].get("complement") == "dont 3 chambres"
     and f_cr["lignes"][0] == {"libelle": "Adresse", "valeur": "12 rue des Tilleuls, 42700 Firminy"}
     and f_cr["lignes"][1] == {"libelle": "Mandant", "valeur": "Mme CLAUDE TESTCLAUDE", "contact": True}
     and {"libelle": "DPE", "valeur": "D"} in f_cr["lignes"] and f_cr["photos"] == 2 and f_cr["composition"] == 1
     and f_cr["a_remplir"] == ["Photos"] and ges.fiche_carte(p_cr, "creer_relance") is None,
     "la FICHE de l'écran (planche 1) : titre, quatre chiffres, adresse, mandant, le reste, ce qui reste à remplir")
appels14.clear()
liens19.clear()
r_cr = ges.executer_ouvrir_creation_annonce(nouveau_ctx(), p_cr)
voir(r_cr["ouvrir"] == "creation_annonce" and r_cr["genre"] == "estimation" and r_cr["cases"] == p_cr["cases"]
     and r_cr["mandant"] == {"hektor_contact_id": "10354641", "nom": "Mme CLAUDE TESTCLAUDE"} and r_cr["negociateur"] is None
     and [f["nom"] for f in r_cr["photos"]] == ["facade.jpg", "vue.webp"] and all(f["url"].startswith("https://") for f in r_cr["photos"])
     and not ecrits14(),
     "au CLIC : l'ordre d'ouverture, les valeurs re-vérifiées, des liens COURTS vers les photos -- et RIEN d'écrit")
etat14["contact"] = {"10354641": {"archive": True}}
voir(refuse(lambda: ges.executer_ouvrir_creation_annonce(nouveau_ctx(), p_cr), "archivé"),
     "TÉMOIN : le mandant archivé entre la carte et le clic -> refusé au clic")
etat14.pop("contact")
etat18["disparus"] = {"d" * 32}
voir(refuse(lambda: ges.executer_ouvrir_creation_annonce(nouveau_ctx(), p_cr), "joins-le à nouveau"),
     "TÉMOIN : une photo de la fiche retirée du trombone -> refusé au clic")
etat18.pop("disparus")
voir(refuse(lambda: ges.executer_ouvrir_creation_annonce(nouveau_ctx(), {**p_cr, "cases": {**p_cr["cases"], "mandantEmail": "x@y.fr"}}),
            "n'est pas une case"),
     "TÉMOIN : une case interdite glissée dans les paramètres rangés -> refusée AU CLIC aussi")
_, p_dir2 = ges.preparer_ouvrir_creation_annonce(nouveau_ctx("admin"), {**CR, "negociateur": "pereira"})
r_dir = ges.executer_ouvrir_creation_annonce(nouveau_ctx("admin"), p_dir2)
voir(r_dir["negociateur"]["hektor_user_id"] == "203" and r_dir["negociateur"]["agence"] == "GTI Firminy",
     "au clic, la direction reçoit le COMPTE Hektor du négociateur (la valeur du menu de la fenêtre) et son agence")
voir(refuse(lambda: ges.executer_ouvrir_creation_annonce(nouveau_ctx(), p_dir2), "c'est toi"),
     "TÉMOIN : une carte de direction cliquée par un commercial -> refusée")


class Service21(Service):
    def __init__(self, carte):
        super().__init__(carte)
        self.suites = []

    def noter_suite(self, action_id, user_id, resultat):
        self.suites.append(resultat)
        return True


def route21(fonction, carte, role="commercial", **kw):
    service = Service21(carte)
    route._ouvrir = lambda *a: (User(UID), {"role": role, "display_name": "Paul NEGO"})
    try:
        return fonction("a" * 36, *kw.values(), "Bearer " + JETON, Settings(), None, service), service
    except HTTPException as exc:
        return exc.status_code, service


carte_cr = {"id": "a" * 36, "user_id": UID, "geste": "ouvrir_creation_annonce", "etat": "executee", "parametres": p_cr,
            "conversation_id": "c" * 36, "resultat": {**r_cr}}
appels14.clear()
r, s = route21(route.assistant_rouvrir, carte_cr)
voir(r["ok"] and r["resultat"]["ouvrir"] == "creation_annonce" and r["resultat"]["photos"] and not s.fins and not ecrits14(),
     "ROUVRIR : re-vérifié comme au clic, liens frais, la carte ne change PAS d'état, rien d'écrit")
r, s = route21(route.assistant_rouvrir, {**carte_cr, "etat": "proposee"})
voir(r == 409, "⛔ rouvrir une carte pas encore validée : refusé (il faut cliquer « Ouvrir la création »)")
r, s = route21(route.assistant_rouvrir, {**carte_cr, "geste": "creer_relance"})
voir(r == 409, "⛔ rouvrir une autre sorte de carte : refusé")
r, s = route21(route.assistant_suite, carte_cr, payload=route.SuiteCreationPayload(app_dossier_id=10000123, genre="estimation"))
voir(r["ok"] and s.suites and s.suites[0]["cree"]["app_dossier_id"] == 10000123 and "photos" not in s.suites[0]
     and s.suites[0]["cases"] == p_cr["cases"],
     "SUITE : la carte garde « créée » (et ce qu'elle a pré-rempli), sans les liens expirés des photos")
r, s = route21(route.assistant_suite, {**carte_cr, "user_id": "u-autre"},
               payload=route.SuiteCreationPayload(app_dossier_id=1, genre="annonce"))
voir(r == 404 and not s.suites, "⛔ la carte d'un AUTRE : introuvable, rien noté")

print(f"\n{ok} contrôles verts")
