"""Assistant IA, étape 4 chap. 6, P1 (19/11/2026) — le parcours guidé : les questions SANS modèle.

Lancer depuis backend/ :  <python> tests/test_assistant_parcours.py     (sans réseau)
Vérifie : l'ordre des 19 questions et leurs conditions par type de bien (piscine cochée, terrain, appartement,
construction de moins de 10 ans) ; une réponse ne touche QUE les cases de sa question ; les coordonnées d'un nouveau
mandant sont refusées ; « je ne sais pas » et « plus tard » font avancer ; un parcours complet finit, pour chaque type ;
la table : création, relecture avec le JETON de la personne, écriture CONDITIONNELLE (deux onglets, un seul passe) ;
les routes : l'interrupteur, la conversation d'un autre, le parcours d'un autre, la question non posée, le parcours fini.
Aucun appel au modèle : le module ne connaît pas OpenAI.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from fastapi import HTTPException

from app.services import assistant_parcours as moteur

ok = 0


def voir(vrai, libelle):
    global ok
    assert vrai, libelle
    ok += 1
    print("  VERT  " + libelle)


def refuse(fonction, morceau=""):
    try:
        fonction()
    except moteur.RefusParcours as exc:
        return morceau in str(exc)
    return False


ANNEE = 2026
APPARTEMENT, MAISON, TERRAIN, GARAGE, IMMEUBLE, AUTRE = "2", "1", "5", "15", "21", "7"


def ids(reponses):
    return [q["id"] for q in moteur.questions_posees(reponses, ANNEE)]


print("1) les questions et leurs conditions")
voir(len(moteur.QUESTIONS) == 19, "19 questions en données (§88)")
voir(moteur.suivante({}, ANNEE)["id"] == "bien", "la première question est « le bien »")
voir(moteur.profil({}) == "apartment", "avant que le type soit dit : le type par défaut de la fenêtre (appartement)")
a = ids({"type": APPARTEMENT})
voir("appartement" in a and "copropriete" in a and "piscine" not in a and "terrain" not in a,
     "un appartement : l'étage et la copropriété, ni piscine ni terrain à bâtir")
m = ids({"type": MAISON})
voir("piscine" not in m and "copropriete" not in m and "appartement" not in m, "une maison sans piscine cochée : pas de question piscine")
voir("piscine" in ids({"type": MAISON, "PISCINE-": "OUI"}), "une maison, piscine cochée : la question piscine arrive")
voir("piscine" not in ids({"type": APPARTEMENT, "PISCINE-": "OUI"}), "un appartement ne pose jamais la piscine (la fenêtre ne la montre pas)")
t = ids({"type": TERRAIN})
voir("terrain" in t and "interieur" not in t and "confort" not in t, "un terrain : le terrain à bâtir, ni intérieur ni confort")
voir("copropriete" in ids({"type": IMMEUBLE}), "un immeuble : la copropriété (oubli du §88 trouvé par l'essai de couverture)")
voir("diagnostics" not in ids({"type": GARAGE}), "un garage : pas de diagnostics (la fenêtre n'en montre aucun)")
voir("construction_recente" in ids({"type": MAISON}), "année inconnue : on demande la construction récente")
voir("construction_recente" in ids({"type": MAISON, "ANNEE_CONS": "2023"}), "construit en 2023 : moins de 10 ans, on demande")
voir("construction_recente" not in ids({"type": MAISON, "ANNEE_CONS": "1975"}), "construit en 1975 : on ne demande pas")
voir("construction_recente" not in ids({"type": MAISON, "ANNEE_CONS": "2016"}), "construit en 2016 (10 ans pile) : on ne demande pas")

print("2) une réponse ne touche que SA question")
r = moteur.enregistrer({}, "bien", {"type": MAISON, "cp": " 42700 ", "ville": "Firminy"}, "repondre")
voir(r["type"] == MAISON and r["cp"] == "42700" and r["_questions"] == {"bien": "faite"}, "la réponse est gardée, nettoyée, la question notée « faite »")
voir(moteur.suivante(r, ANNEE)["id"] == "quartier", "la suivante est « le quartier »")
voir(refuse(lambda: moteur.enregistrer({}, "bien", {"surfappart": "80"}, "repondre"), "n'appartient pas"),
     "une case d'une AUTRE question : refusée")
voir(refuse(lambda: moteur.enregistrer({}, "mandant", {"email": "x@exemple.invalid"}, "repondre"), "cases protégées"),
     "un e-mail de mandant dans une réponse : refusé (règle du 18/11)")
voir(refuse(lambda: moteur.enregistrer({}, "mandant", {"telephone": "0600000000"}, "repondre"), "cases protégées"),
     "un téléphone de mandant : refusé")
voir(refuse(lambda: moteur.enregistrer({}, "bien", {"_questions": {}}, "repondre"), "cases protégées"),
     "le suivi interne ne s'écrit pas depuis l'écran")
voir(refuse(lambda: moteur.enregistrer({}, "inconnue", {"x": "1"}, "repondre"), "inconnue"), "une question inconnue : refusée")
voir(refuse(lambda: moteur.enregistrer({}, "bien", {}, "repondre"), "Réponse vide"), "une réponse vide : refusée (dire « je ne sais pas »)")
voir(refuse(lambda: moteur.enregistrer({}, "mandant", {"mandant_choix": "peut-être"}, "repondre"), "existant"),
     "un choix de mandant hors liste : refusé")
voir(refuse(lambda: moteur.enregistrer({}, "texte", {"corps": "x" * 4001}, "repondre"), "trop longue"), "un texte trop long : refusé")
voir(refuse(lambda: moteur.enregistrer({}, "bien", {"cp": {"a": 1}}, "repondre"), "texte ou un nombre"), "une valeur qui n'est pas un texte : refusée")
voir(refuse(lambda: moteur.enregistrer({}, "bien", {"cp": "1"}, "effacer"), "Geste inconnu"), "un geste inconnu : refusé")
r2 = moteur.enregistrer(r, "bien", {"ville": ""}, "repondre")
voir("ville" not in r2 and r2["cp"] == "42700", "vider une case la retire, les autres restent (« Modifier »)")
p = moteur.enregistrer({}, "composition", {"composition": [
    {"idTypePiece": "3", "typeLabel": "Chambre", "surfacePiece": "12", "etagePiece": ""}, {"detailPiece": ""}]}, "repondre")
voir(p["composition"] == [{"idTypePiece": "3", "typeLabel": "Chambre", "surfacePiece": "12"}],
     "la composition : les pièces gardées sans leurs cases vides, une pièce vide est retirée")
voir(refuse(lambda: moteur.enregistrer({}, "composition", {"composition": [{"prix": "1"}]}, "repondre"), "inconnue"),
     "une case de pièce inconnue : refusée")
f = moteur.enregistrer({}, "photos", {"photos": ["12", "", "13"]}, "repondre")
voir(f["photos"] == ["12", "13"], "les photos : des numéros de fichiers")

print("3) « je ne sais pas » et « plus tard » font avancer")
n = moteur.enregistrer(r, "quartier", {}, "nsp")
voir(n["_questions"]["quartier"] == "nsp" and moteur.suivante(n, ANNEE)["id"] != "quartier", "« je ne sais pas » : notée, on passe")
n = moteur.enregistrer(n, "interieur", None, "passer")
voir(n["_questions"]["interieur"] == "passee", "« je complète plus tard » : notée « passée », rien d'écrit")

print("4) un parcours complet finit, pour chaque type de bien")
for type_id, nom in ((MAISON, "maison"), (APPARTEMENT, "appartement"), (TERRAIN, "terrain"), (GARAGE, "garage"),
                     (IMMEUBLE, "immeuble"), (AUTRE, "autre")):
    rep, tours = {}, 0
    while (q := moteur.suivante(rep, ANNEE)) and tours < 40:
        tours += 1
        rep = moteur.enregistrer(rep, q["id"], {"type": type_id} if q["id"] == "bien" else None,
                                 "repondre" if q["id"] == "bien" else "nsp")
    v = moteur.vue({"id": "p", "genre": "creation_estimation", "etat": "en_cours", "reponses": rep}, ANNEE)
    voir(v["fin"] and v["question"] is None and v["repere"]["faites"] == v["repere"]["total"] == tours,
         f"{nom} : {tours} questions posées, toutes vues, le parcours finit")
v = moteur.vue({"id": "p", "reponses": r}, ANNEE)
voir("_questions" not in v["reponses"] and v["repere"]["rang"] == 2 and v["question"]["id"] == "quartier",
     "la vue : le repère « 2 sur N », la question, les réponses SANS le suivi interne")

print("5) la table (clé de service pour écrire, jeton de la personne pour relire)")


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_anon_key = "cle-publique"
    supabase_service_role_key = "cle-de-service"


class Reponse:
    def __init__(self, data, status=200):
        self.status_code, self._data, self.ok = status, data, status < 400

    def json(self):
        return self._data


appels = []
table = {}


def faux(methode, url, **kw):
    params, corps, ent = kw.get("params") or {}, kw.get("json"), kw.get("headers") or {}
    appels.append({"methode": methode, "url": url, "params": params, "corps": corps, "entetes": ent})
    if "app_setting" in url:
        return Reponse([{"value": interrupteur["valeur"]}] if interrupteur["valeur"] else [])
    if "app_assistant_parcours" not in url:
        raise AssertionError("requête non prévue : " + url)
    if methode == "POST":
        ligne = {**corps[0], "id": "p" * 36, "etat": "en_cours", "app_dossier_id": None, "maj_le": "t1"}
        table[ligne["id"]] = ligne
        return Reponse([ligne])
    if methode == "GET" and "conversation_id" in params:
        conv = params["conversation_id"].removeprefix("eq.")
        return Reponse([json.loads(json.dumps(x)) for x in table.values() if x.get("conversation_id") == conv])
    pid = params.get("id", "").removeprefix("eq.")
    ligne = table.get(pid)
    if methode == "GET":
        # une COPIE, comme la vraie base : une lecture ne bouge pas quand la table bouge ensuite
        return Reponse([json.loads(json.dumps(ligne))] if ligne else [])
    if methode == "PATCH":
        conditions_ok = ligne and all(str(ligne.get(k)) == v.removeprefix("eq.") if v.startswith("eq.")
                                      else (ligne.get(k) is None) for k, v in params.items() if k != "id")
        if not conditions_ok:
            return Reponse([])
        ligne.update(corps)
        ligne["maj_le"] = "t" + str(int(ligne["maj_le"][1:]) + 1)
        return Reponse([dict(ligne)])
    raise AssertionError(methode)


interrupteur = {"valeur": "on"}
requests.get = lambda url, **kw: faux("GET", url, **kw)
requests.post = lambda url, **kw: faux("POST", url, **kw)
requests.patch = lambda url, **kw: faux("PATCH", url, **kw)

store = moteur.ParcoursStore(Settings())
ligne = store.creer("u1", None, "creation_estimation", "bien")
voir(appels[-1]["entetes"]["Authorization"] == "Bearer cle-de-service" and appels[-1]["corps"][0]["reponses"] == {},
     "créer : par la clé de service, réponses vides")
store.lire_avec_jeton("jeton-de-paul", ligne["id"])
voir(appels[-1]["entetes"]["Authorization"] == "Bearer jeton-de-paul" and appels[-1]["entetes"]["apikey"] == "cle-publique",
     "relire pour l'écran : avec le JETON de la personne (la règle de lecture de la base décide)")
lu = store.lire_service(ligne["id"])
e = store.ecrire_reponses(lu, {"type": "1"}, "quartier")
pa = appels[-1]["params"]
voir(e and pa["maj_le"] == "eq.t1" and pa["etat"] == "eq.en_cours" and pa["app_dossier_id"] == "is.null"
     and pa["user_id"] == "eq.u1", "écrire : CONDITIONNEL (même maj_le, à lui, en cours, avant la création)")
voir(store.ecrire_reponses(lu, {"type": "2"}, "quartier") is None and table[ligne["id"]]["reponses"] == {"type": "1"},
     "deux onglets : la seconde écriture sur une lecture périmée ne passe pas, rien n'est écrasé")

print("6) les routes")
from app.routers import assistant as route  # noqa: E402

UID, AUTRE_UID = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"


class User:
    def __init__(self, uid):
        self.id, self.email = uid, "paul@exemple.invalid"


class Service:
    def __init__(self):
        self.conv = {"id": "c" * 36, "user_id": UID}

    def interrupteur(self, cle=None):
        return interrupteur["valeur"] if cle == route.INTERRUPTEUR_PARCOURS else "on"

    def conversation(self, conversation_id):
        return self.conv if conversation_id == self.conv["id"] else None


def appeler(fonction, *args, uid=UID, role="commercial"):
    route._ouvrir = lambda *a: (User(uid), {"role": role, "is_active": True})
    try:
        return fonction(*args)
    except HTTPException as exc:
        return exc.status_code, exc.detail


table.clear()
S, ST = Service(), moteur.ParcoursStore(Settings())
depart = route.ParcoursDepartPayload(genre="creation_estimation", conversationId="c" * 36)
interrupteur["valeur"] = ""
r = appeler(route.parcours_commencer, depart, "Bearer j", Settings(), None, S, ST)
voir(r[0] == 403 and not table, "interrupteur absent : refusé, rien n'est créé")
interrupteur["valeur"] = "admin"
r = appeler(route.parcours_commencer, depart, "Bearer j", Settings(), None, S, ST)
voir(r[0] == 403 and not table, "interrupteur « admin » : un commercial est refusé")
r = appeler(route.parcours_commencer, depart, "Bearer j", Settings(), None, S, ST, role="admin")
voir(r["ok"] and r["parcours"]["question"]["id"] == "bien", "interrupteur « admin » : l'admin commence, première question « le bien »")
interrupteur["valeur"] = "on"
table.clear()
r = appeler(route.parcours_commencer, route.ParcoursDepartPayload(genre="creation_estimation", conversationId="d" * 36),
            "Bearer j", Settings(), None, S, ST)
voir(r[0] == 404 and not table, "la conversation d'un autre (ou inconnue) : introuvable, rien n'est créé")
r = appeler(route.parcours_commencer, depart, "Bearer j", Settings(), None, S, ST)
pid = r["parcours"]["id"]
voir(table[pid]["conversation_id"] == "c" * 36 and table[pid]["etape"] == "bien", "commencé dans SA conversation, étape « bien »")

rep = route.ParcoursReponsePayload(question="bien", geste="repondre", valeurs={"type": "1", "ville": "Firminy"})
r = appeler(route.parcours_repondre, pid, rep, "Bearer j", Settings(), None, S, ST)
voir(r["ok"] and r["parcours"]["question"]["id"] == "quartier" and table[pid]["etape"] == "quartier"
     and table[pid]["reponses"]["ville"] == "Firminy", "répondre : gardé en base, la question suivante revient (sans modèle)")
r = appeler(route.parcours_repondre, pid, rep, "Bearer j", Settings(), None, S, ST, uid=AUTRE_UID, role="admin")
voir(r[0] == 404, "le parcours d'un AUTRE : introuvable, même pour l'admin (il relit, il ne répond pas)")
r = appeler(route.parcours_repondre, pid, route.ParcoursReponsePayload(question="copropriete", geste="nsp"),
            "Bearer j", Settings(), None, S, ST)
voir(r[0] == 400 and "pas posée" in r[1], "une question non posée pour ce bien (copropriété d'une maison) : refusée")
r = appeler(route.parcours_repondre, pid, route.ParcoursReponsePayload(question="mandant", geste="repondre",
            valeurs={"email": "x@exemple.invalid"}), "Bearer j", Settings(), None, S, ST)
voir(r[0] == 400 and "x@exemple" not in json.dumps(table[pid]), "un e-mail envoyé en réponse : refusé, rien n'est gardé")
table[pid]["maj_le"] = "t9"   # quelqu'un a écrit entre la lecture et l'écriture
lu_avant = dict(table[pid])
orig = ST.lire_service
ST.lire_service = lambda i: {**lu_avant, "maj_le": "t8"}
r = appeler(route.parcours_repondre, pid, route.ParcoursReponsePayload(question="quartier", geste="nsp"),
            "Bearer j", Settings(), None, S, ST)
ST.lire_service = orig
voir(r[0] == 409 and "quartier" not in table[pid]["reponses"].get("_questions", {}), "écriture concurrente : 409, rien n'est écrasé")
table[pid]["app_dossier_id"] = 10000042
r = appeler(route.parcours_repondre, pid, route.ParcoursReponsePayload(question="quartier", geste="nsp"),
            "Bearer j", Settings(), None, S, ST)
voir(r[0] == 409 and "terminé" in r[1], "la fiche est créée : le parcours ne se modifie plus")
r = appeler(route.parcours_relire, pid, "Bearer jeton-de-paul", Settings(), None, S, ST)
voir(r["ok"] and appels[-1]["entetes"]["Authorization"] == "Bearer jeton-de-paul", "relire : avec SON jeton")
r = appeler(route.parcours_relire, "court", "Bearer j", Settings(), None, S, ST)
voir(r[0] == 404, "un numéro mal formé : introuvable")

print("6 bis) P2 : retrouver les parcours d'une conversation, noter la fiche créée")
table.clear()
r1 = appeler(route.parcours_commencer, depart, "Bearer j", Settings(), None, S, ST)
p1 = r1["parcours"]["id"]
r = appeler(route.parcours_de_la_conversation, "c" * 36, "Bearer jeton-de-paul", Settings(), None, S, ST)
voir(r["ok"] and [x["id"] for x in r["parcours"]] == [p1] and appels[-1]["entetes"]["Authorization"] == "Bearer jeton-de-paul"
     and appels[-1]["params"]["conversation_id"] == "eq." + "c" * 36,
     "la conversation rouverte retrouve SON parcours, relu avec le jeton de la personne")
r = appeler(route.parcours_de_la_conversation, "d" * 36, "Bearer j", Settings(), None, S, ST)
voir(r["ok"] and r["parcours"] == [], "une autre conversation : aucun parcours")
interrupteur["valeur"] = ""
r = appeler(route.parcours_de_la_conversation, "c" * 36, "Bearer j", Settings(), None, S, ST)
voir(r[0] == 403, "interrupteur absent : la liste est refusée aussi")
r = appeler(route.parcours_cree, p1, route.ParcoursCreePayload(app_dossier_id=10000077), "Bearer j", Settings(), None, S, ST)
voir(r[0] == 403 and table[p1]["etat"] == "en_cours", "interrupteur absent : la fin est refusée, rien ne bouge")
interrupteur["valeur"] = "on"
r = appeler(route.parcours_cree, p1, route.ParcoursCreePayload(app_dossier_id=10000077), "Bearer j", Settings(), None, S, ST,
            uid=AUTRE_UID, role="admin")
voir(r[0] == 404 and table[p1]["etat"] == "en_cours", "noter la fin du parcours d'un AUTRE : introuvable, même pour l'admin")
r = appeler(route.parcours_cree, p1, route.ParcoursCreePayload(app_dossier_id=10000077), "Bearer j", Settings(), None, S, ST)
pa = appels[-1]["params"]
voir(r["ok"] and table[p1]["etat"] == "termine" and table[p1]["app_dossier_id"] == 10000077 and table[p1]["termine_le"]
     and pa["etat"] == "eq.en_cours" and pa["app_dossier_id"] == "is.null" and pa["user_id"] == "eq." + UID,
     "la fiche créée : le parcours est TERMINÉ, avec son bien, par une écriture CONDITIONNELLE")
r = appeler(route.parcours_cree, p1, route.ParcoursCreePayload(app_dossier_id=10000099), "Bearer j", Settings(), None, S, ST)
voir(r[0] == 409 and table[p1]["app_dossier_id"] == 10000077, "noter une seconde fois : 409, le premier bien reste")
table.clear()
r2 = appeler(route.parcours_commencer, depart, "Bearer j", Settings(), None, S, ST)
p2 = r2["parcours"]["id"]
r = appeler(route.parcours_cree, p2, route.ParcoursCreePayload(), "Bearer j", Settings(), None, S, ST)
voir(r["ok"] and table[p2]["etat"] == "termine" and table[p2]["app_dossier_id"] is None,
     "créée sans numéro encore connu : terminé quand même (l'auteur garde la lecture)")
r = appeler(route.parcours_cree, "court", route.ParcoursCreePayload(), "Bearer j", Settings(), None, S, ST)
voir(r[0] == 404, "noter la fin d'un numéro mal formé : introuvable")

print("7) aucun appel au modèle")
src = open(moteur.__file__, encoding="utf-8").read()
voir("openai" not in src.lower().replace("ne connaît pas openai", ""), "le moteur ne connaît pas OpenAI")
voir(not any("openai" in a["url"] for a in appels), "aucune requête vers OpenAI pendant tout l'essai")

print(f"\nTOUT EST VERT ({ok} contrôles)")
