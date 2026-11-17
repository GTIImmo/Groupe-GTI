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
voir(all(f.nom.startswith("proposer_") for f in ges.FONCTIONS_GESTES) and len(ges.FONCTIONS_GESTES) == 38,
     "37 gestes (le brouillon retiré le 15/11, 3 du lot 2c, 3 du lot 3c, 1 de la vague C, le numéro de mandat, la relance "
     "et l'annulation d'une signature le 16/11, puis les 8 cartes directes de l'audit §35, et le prix pour la direction le 17/11), "
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

print(f"\n{ok} contrôles verts")
