"""Assistant IA, étape 1 (12/11/2026) — le socle dormant.

Lancer depuis backend/, avec un Python qui a les dépendances de requirements.txt (dont openai-agents==0.22.0) :
    <python> tests/test_assistant_ia.py
Sans le SDK, la partie 1 tourne seule et la partie 2 est dite SAUTÉE (jamais comptée verte).
Aucun appel réseau : requests.get / post / patch sont remplacés par des faux, et OpenAI par un faux serveur HTTP
(httpx.MockTransport) qui rend de vrais flux de l'API Responses. Toute requête httpx non prévue fait échouer l'essai.
Vérifie : l'interrupteur et ses crans, les deux plafonds et le refus AVANT tout appel, la lecture ratée qui n'est
jamais un vert, store:false, aucune trace chez OpenAI, le jeton de la personne pour lire la base (jamais la clé de
service), le jeton et l'e-mail jamais envoyés au modèle, le journal sans texte, les 8 étapes au plus, le SDK chargé
seulement au premier appel.
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import HTTPException

import requests

ok = 0


def voir(vrai, libelle):
    global ok
    assert vrai, libelle
    ok += 1
    print("  VERT  " + libelle)


print("0) le SDK n'est pas chargé au démarrage du serveur")
import app.main  # noqa: E402,F401
voir("agents" not in sys.modules, "importer app.main ne charge pas le SDK d'agents")
voir(any(getattr(r, "path", "") == "/assistant/message" for r in app.main.app.routes), "la route /assistant/message est branchée")

from app.routers.ged import autorise  # noqa: E402
from app.routers import assistant as route  # noqa: E402
from app.services import assistant_service as svc  # noqa: E402
from app.services import assistant_catalogue as cat  # noqa: E402
from app.services.agent_tarifs import cout_usd  # noqa: E402
from app.services import agent_registry  # noqa: E402


class Faux:
    def __init__(self, ok=True, data=None, status=200):
        self.ok, self._data, self.status_code, self.text = ok, data, status if ok else 500, ""

    def json(self):
        return self._data


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_anon_key = "cle-publique"
    supabase_service_role_key = "cle-de-service"
    openai_api_key = "sk-test"
    openai_vision_model = "gpt-4.1-mini"


JETON = "jeton.de.pauline"
USER_ID = "11111111-1111-1111-1111-111111111111"
EMAIL = "pauline@gti-immobilier.fr"
CONV = "22222222-2222-2222-2222-222222222222"

etat = {"cran": "admin", "role": "admin", "depense": 0.0, "questions": 0, "run_illisible": False, "conv_user": USER_ID}
appels = []  # (methode, url, en-têtes, params, corps)


def faux_get(url, headers=None, params=None, timeout=None):
    appels.append(("GET", url, headers or {}, params or {}, None))
    if url.endswith("/auth/v1/user"):
        return Faux(data={"id": USER_ID, "email": EMAIL})
    if url.endswith("/app_user_profile"):
        if (headers or {}).get("apikey") == "cle-publique":  # la fonction qui_suis_je
            return Faux(data=[{"display_name": "Pauline Martin", "first_name": "Pauline", "last_name": "Martin",
                               "role": etat["role"], "is_active": True}])
        return Faux(data=[{"id": USER_ID, "email": EMAIL, "role": etat["role"], "is_active": True}])
    if url.endswith("/app_setting"):
        return Faux(data=[{"value": etat["cran"]}] if etat["cran"] is not None else [])
    if url.endswith("/app_agent_prompt"):
        return Faux(data=[])
    if url.endswith("/app_agent_run"):
        if etat["run_illisible"]:
            return Faux(ok=False)
        if "cost_usd" in params["select"]:
            return Faux(data=[{"cost_usd": etat["depense"]}])
        return Faux(data=[{"id": i} for i in range(etat["questions"])])
    if url.endswith("/app_assistant_conversation"):
        return Faux(data=[{"id": CONV, "user_id": etat["conv_user"], "archivee": False}])
    if url.endswith("/app_assistant_message"):
        return Faux(data=[{"role": "assistant", "contenu": "Bonjour."}, {"role": "user", "contenu": "Salut"}])
    raise AssertionError("GET inattendu " + url)


def faux_post(url, headers=None, json=None, timeout=None, **_):
    appels.append(("POST", url, headers or {}, {}, json))
    if url.endswith("/app_assistant_conversation"):
        return Faux(data=[{"id": CONV}])
    if url.endswith("/app_assistant_message"):
        return Faux(data=[{"id": 7}])
    if url.endswith("/app_agent_run"):
        return Faux(data=[{"id": 99}])
    raise AssertionError("POST inattendu " + url)


def faux_patch(url, headers=None, params=None, json=None, timeout=None):
    appels.append(("PATCH", url, headers or {}, params or {}, json))
    return Faux(data=[])


requests.get, requests.post, requests.patch = faux_get, faux_post, faux_patch
for module in ("app.auth", "app.services.supabase_admin", "app.services.agent_registry"):
    sys.modules[module].requests.get = faux_get

print("1) l'interrupteur")
voir(autorise("admin", "admin", True) and not autorise("admin", "commercial", True), "cran admin : l'admin oui, le négociateur non")
voir(autorise("on", "commercial", True) and not autorise("on", "commercial", False), "cran on : tout actif, jamais un inactif")
s = svc.AssistantService(Settings())
etat["cran"] = None
voir(s.interrupteur() == "off", "interrupteur absent = éteint")
etat["cran"] = " ADMIN "
voir(s.interrupteur() == "admin", "« ADMIN » avec espaces = admin")
etat["cran"] = "oui"
voir(s.interrupteur() == "off", "une valeur inconnue = éteint")
etat["cran"] = "admin"

print("2) les plafonds, AVANT tout appel")
voir(cout_usd("gpt-4.1-mini", {"input_tokens": 1000, "output_tokens": 1000}) == 0.002, "tarif gpt-4.1-mini : 1 000 + 1 000 jetons = 0,002 $")
voir(cout_usd("modele-inconnu", {"input_tokens": 1, "output_tokens": 1}) is None, "modèle inconnu : coût inconnu, jamais zéro")
spec = s.preparer(EMAIL)
voir(spec.model == "gpt-4.1-mini" and spec.max_output_tokens == 1500, "fiche par défaut : gpt-4.1-mini, 1 500 jetons de sortie")


def refuse(fonction, code):
    try:
        fonction()
    except HTTPException as exc:
        return exc.status_code == code
    return False


etat["depense"] = 3.0
voir(refuse(lambda: s.preparer(EMAIL), 429), "3 $ dépensés aujourd'hui : refus 429")
etat["depense"], etat["questions"] = 2.99, 100
voir(refuse(lambda: s.preparer(EMAIL), 429), "100 questions aujourd'hui : refus 429")
etat["questions"] = 99
voir(s.preparer(EMAIL).model == "gpt-4.1-mini", "TÉMOIN : 2,99 $ et 99 questions passent")
etat["run_illisible"] = True
voir(refuse(lambda: s.preparer(EMAIL), 503), "journal illisible : refus 503, une lecture ratée n'est jamais un vert")
etat["run_illisible"], etat["depense"], etat["questions"] = False, 0.0, 0
agent_registry.DEFAULT_SPECS["assistant"] = agent_registry.AgentSpec("assistant", "x", "gpt-9-inconnu", 100)
agent_registry._CACHE.clear()
voir(refuse(lambda: s.preparer(EMAIL), 503), "un modèle sans tarif n'est pas appelé")
agent_registry.DEFAULT_SPECS["assistant"] = agent_registry.AgentSpec("assistant", svc._INSTRUCTIONS, "gpt-4.1-mini", 1500)
agent_registry._CACHE.clear()


class SansCle(Settings):
    openai_api_key = None


voir(refuse(lambda: svc.AssistantService(SansCle()).preparer(EMAIL), 503), "sans clé OpenAI : refus 503")

print("3) le catalogue et ses droits")
voir([f.nom for f in cat.fonctions_du_role("commercial")] == ["qui_suis_je"], "un négociateur a la fonction témoin")
voir(cat.fonctions_du_role("inconnu") == [], "un rôle inconnu n'a aucune fonction")
voir(not any("utilisateur" in f.nom or "user" in f.nom for f in cat.CATALOGUE), "aucune gestion des utilisateurs (Q5 du 29/10)")
ctx = cat.ContexteAssistant(Settings(), USER_ID, EMAIL, "commercial", JETON)
appels.clear()
reponse = json.loads(asyncio.run(cat.appeler(ctx, cat.CATALOGUE[0], "{}")))
lecture = [a for a in appels if a[1].endswith("/app_user_profile")][0]
voir(reponse["nom_affiche"] == "Pauline Martin", "qui_suis_je rend le nom lu")
voir(lecture[2]["Authorization"] == "Bearer " + JETON and lecture[2]["apikey"] == "cle-publique",
     "qui_suis_je lit avec le JETON de la personne et la clé publique (la RLS fait le tri)")
voir("cle-de-service" not in json.dumps(lecture[2]), "et JAMAIS avec la clé de service")
voir(lecture[3]["id"] == "eq." + USER_ID, "filtrée sur SON id (un admin lit tous les profils)")
ctx_intrus = cat.ContexteAssistant(Settings(), USER_ID, EMAIL, "inconnu", JETON)
voir(asyncio.run(cat.appeler(ctx_intrus, cat.CATALOGUE[0], "{}")).startswith("Refusé")
     and ctx_intrus.appels[0]["erreur"] == "role", "2e verrou : appelée hors de son rôle, la fonction refuse")

print("4) le journal ne garde jamais le texte")
ctx.appels[:] = [{"nom": "qui_suis_je", "parametres": {}}]
ligne = route._ligne_journal(ctx, spec, CONV, "QUESTION-SECRETE", {"reponse": "REPONSE-SECRETE", "usage": {"input_tokens": 5},
                                                                    "costUsd": 0.001, "etapes": 2}, status="proposed")
voir("SECRETE" not in json.dumps(ligne, ensure_ascii=False), "ni la question ni la réponse dans app_agent_run")
voir(ligne["proposal_json"]["fonctions"] == ["qui_suis_je"] and ligne["agent_key"] == "assistant", "les noms des fonctions, l'agent")
voir(ligne["status"] in {"proposed", "error"}, "un statut admis par la contrainte de app_agent_run")

print("5) le tour complet, en flux (SDK réel, faux OpenAI)")
try:
    import httpx
    import agents  # noqa: F401
except ImportError:
    print("  SAUTÉ  le SDK openai-agents n'est pas installé dans ce Python : partie 5 NON vérifiée")
    print(f"\n{ok} contrôles verts (partie 5 SAUTÉE)")
    sys.exit(0)

from fastapi.testclient import TestClient  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402

# comme sur Render : la clé est dans l'environnement, l'exportateur de traces du SDK pourrait donc envoyer
os.environ["OPENAI_API_KEY"] = "sk-test"
corps_openai = []


def sse(evenements):
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in evenements).encode()


def reponse_complete(rid, sortie, entree, sortie_jetons):
    return {"id": rid, "object": "response", "created_at": 1, "model": "gpt-4.1-mini", "status": "completed",
            "output": sortie, "parallel_tool_calls": True, "tool_choice": "auto", "tools": [],
            "usage": {"input_tokens": entree, "output_tokens": sortie_jetons, "total_tokens": entree + sortie_jetons,
                      "input_tokens_details": {"cached_tokens": 0}, "output_tokens_details": {"reasoning_tokens": 0}}}


def flux_outil(n):
    item = {"type": "function_call", "id": f"fc_{n}", "call_id": f"call_{n}", "name": "qui_suis_je", "arguments": "{}",
            "status": "completed"}
    return sse([
        {"type": "response.created", "sequence_number": 0, "response": {**reponse_complete(f"r{n}", [], 0, 0), "status": "in_progress"}},
        {"type": "response.output_item.added", "sequence_number": 1, "output_index": 0, "item": item},
        {"type": "response.output_item.done", "sequence_number": 2, "output_index": 0, "item": item},
        {"type": "response.completed", "sequence_number": 3, "response": reponse_complete(f"r{n}", [item], 100, 10)},
    ])


def flux_texte(n, morceaux):
    texte = "".join(morceaux)
    message = {"type": "message", "id": f"m{n}", "role": "assistant", "status": "completed",
               "content": [{"type": "output_text", "text": texte, "annotations": []}]}
    evenements = [{"type": "response.created", "sequence_number": 0, "response": {**reponse_complete(f"r{n}", [], 0, 0), "status": "in_progress"}},
                  {"type": "response.output_item.added", "sequence_number": 1, "output_index": 0,
                   "item": {**message, "status": "in_progress", "content": []}}]
    for i, m in enumerate(morceaux):
        evenements.append({"type": "response.output_text.delta", "sequence_number": 2 + i, "item_id": f"m{n}",
                           "output_index": 0, "content_index": 0, "delta": m, "logprobs": []})
    evenements += [{"type": "response.output_item.done", "sequence_number": 90, "output_index": 0, "item": message},
                   {"type": "response.completed", "sequence_number": 91, "response": reponse_complete(f"r{n}", [message], 200, 20)}]
    return sse(evenements)


scenario = {"boucle": False}


def faux_openai(requete: httpx.Request) -> httpx.Response:
    assert requete.url.path == "/v1/responses", "requête OpenAI inattendue : " + requete.url.path
    corps = json.loads(requete.content)
    corps_openai.append(corps)
    deja_un_outil = any(isinstance(i, dict) and i.get("type") == "function_call_output" for i in corps.get("input", []))
    contenu = flux_outil(len(corps_openai)) if scenario["boucle"] or not deja_un_outil \
        else flux_texte(len(corps_openai), ["Tu es ", "Pauline Martin, ", "admin."])
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=contenu)


envois_httpx = []
_send_origine = httpx.Client.send


def garde_httpx(self, requete, *a, **k):
    # ⛔ tout envoi httpx SYNCHRONE (l'exportateur de traces du SDK en est un) est relevé et refusé ;
    # seul passe le client d'essai de FastAPI, qui parle à l'application en mémoire
    if requete.url.host == "testserver":
        return _send_origine(self, requete, *a, **k)
    envois_httpx.append(str(requete.url))
    raise AssertionError("envoi réseau inattendu : " + str(requete.url))


httpx.Client.send = garde_httpx
try:
    # ⚠ le SDK exporte ses traces par un paquet À PART, httpx2 (trouvé le 12/11 : sans cette ligne, le contrôle
    # « aucune trace » restait vert même traces rallumées -- le témoin inverse l'a montré)
    import httpx2
    _send_origine2 = httpx2.Client.send
    httpx2.Client.send = garde_httpx
except ImportError:
    httpx2 = None


class ServiceDEssai(svc.AssistantService):
    def __init__(self, settings):
        super().__init__(settings, AsyncOpenAI(api_key="sk-test", http_client=httpx.AsyncClient(transport=httpx.MockTransport(faux_openai))))


client = TestClient(app.main.app)
app.main.app.dependency_overrides[route.get_settings] = lambda: Settings()
app.main.app.dependency_overrides[route.get_assistant_service] = lambda: ServiceDEssai(Settings())
ENTETE = {"Authorization": "Bearer " + JETON}


def poser(question, conversation=None):
    corps = {"question": question}
    if conversation:
        corps["conversationId"] = conversation
    r = client.post("/assistant/message", json=corps, headers=ENTETE)
    lignes = [json.loads(l) for l in r.text.splitlines() if l.strip()] if r.status_code == 200 else []
    return r, lignes


etat["cran"] = "off"
appels.clear()
r, _ = poser("qui suis-je ?")
voir(r.status_code == 403 and not corps_openai and not [a for a in appels if a[0] == "POST"],
     "éteint : 403, rien écrit, aucun appel à OpenAI")
etat["cran"], etat["role"] = "admin", "commercial"
r, _ = poser("qui suis-je ?")
voir(r.status_code == 403 and not corps_openai, "cran admin : un négociateur reçoit 403")
etat["role"], etat["depense"] = "admin", 5.0
appels.clear()
r, _ = poser("qui suis-je ?")
voir(r.status_code == 429 and not corps_openai and not [a for a in appels if a[0] == "POST"],
     "plafond atteint : 429 AVANT d'écrire la question, aucun appel")
etat["depense"] = 0.0

appels.clear()
r, lignes = poser("qui suis-je ?")
types = [l["type"] for l in lignes]
voir(r.status_code == 200 and r.headers["content-type"].startswith("application/x-ndjson"), "200, réponse en flux (une ligne JSON par événement)")
voir(types[0] == "debut" and lignes[0]["conversationId"] == CONV and types[-1] == "fin", "le flux s'ouvre sur la conversation et se ferme sur « fin »")
voir({"type": "outil", "nom": "qui_suis_je"} in lignes, "l'agent a appelé la fonction témoin")
voir("".join(l["delta"] for l in lignes if l["type"] == "texte") == "Tu es Pauline Martin, admin.", "les mots arrivent au fur et à mesure")
voir(len(corps_openai) == 2, "deux appels au modèle : la fonction, puis la réponse")
voir(all(c.get("store") is False for c in corps_openai), "store:false sur CHAQUE appel")
tout_openai = json.dumps(corps_openai, ensure_ascii=False)
voir(JETON not in tout_openai and EMAIL not in tout_openai and USER_ID not in tout_openai and "cle-" not in tout_openai,
     "ni le jeton, ni l'e-mail, ni l'identifiant, ni une clé ne partent chez OpenAI")
voir([t.get("name") for t in corps_openai[0].get("tools", [])] == ["qui_suis_je"], "le modèle ne voit que les fonctions du rôle")
voir(corps_openai[0]["model"] == "gpt-4.1-mini" and corps_openai[0].get("max_output_tokens") == 1500, "gpt-4.1-mini, 1 500 jetons de sortie")
import agents.tracing as tr  # noqa: E402
tr.get_trace_provider().force_flush()
voir(not envois_httpx, "aucune trace envoyée chez OpenAI (rien n'est parti, même après vidage)")
posts = [a for a in appels if a[0] == "POST"]
messages = [a[4][0] for a in posts if a[1].endswith("/app_assistant_message")]
voir([m["role"] for m in messages] == ["user", "assistant"], "la question est écrite AVANT l'appel, la réponse après")
voir(messages[1]["contenu"] == "Tu es Pauline Martin, admin." and messages[1]["outils"] == [{"nom": "qui_suis_je", "parametres": {}}]
     and messages[1]["agent_run_id"] == 99, "la réponse garde ses fonctions et son lien vers le journal")
run = [a[4][0] for a in posts if a[1].endswith("/app_agent_run")]
voir(len(run) == 1 and run[0]["status"] == "proposed" and run[0]["proposal_json"]["fonctions"] == ["qui_suis_je"]
     and run[0]["input_tokens"] == 300 and run[0]["output_tokens"] == 30, "une ligne de journal : jetons des deux appels cumulés")
voir(run[0]["cost_usd"] == cout_usd("gpt-4.1-mini", {"input_tokens": 300, "output_tokens": 30}) and run[0]["proposal_json"]["etapes"] == 2,
     "le coût du tour et ses 2 étapes")
voir("qui suis-je" not in json.dumps(run, ensure_ascii=False) and "Pauline" not in json.dumps(run, ensure_ascii=False),
     "le journal ne porte ni la question ni la réponse")
lecture = [a for a in appels if a[1].endswith("/app_user_profile") and a[2].get("apikey") == "cle-publique"]
voir(len(lecture) == 1 and lecture[0][2]["Authorization"] == "Bearer " + JETON, "la fonction a lu la base avec le jeton de la personne")

etat["conv_user"] = "33333333-3333-3333-3333-333333333333"
corps_openai.clear()
appels.clear()
r, _ = poser("et moi ?", CONV)
voir(r.status_code == 404 and not corps_openai and not [a for a in appels if a[0] == "POST"],
     "la conversation d'un autre : 404, même pour l'admin, rien écrit")
etat["conv_user"] = USER_ID
r, _ = poser("et moi ?", CONV)
voir(r.status_code == 200 and corps_openai[0]["input"][0]["content"] == "Salut" and corps_openai[0]["input"][1]["content"] == "Bonjour.",
     "SA conversation : l'historique repart dans l'ordre")

scenario["boucle"] = True
corps_openai.clear()
appels.clear()
r, lignes = poser("boucle sans fin")
run = [a[4][0] for a in appels if a[0] == "POST" and a[1].endswith("/app_agent_run")]
voir(len(corps_openai) == svc.MAX_ETAPES, f"un agent qui boucle s'arrête à {svc.MAX_ETAPES} appels")
voir(lignes[-1]["type"] == "erreur" and "étapes" in lignes[-1]["detail"], "et la personne le lit, en clair")
voir(len(run) == 1 and run[0]["status"] == "error" and run[0]["error_text"].startswith("MaxTurnsExceeded"), "l'échec est écrit au journal")
scenario["boucle"] = False

r = client.get("/assistant/conversations", headers=ENTETE)
liste = [a for a in appels if a[0] == "GET" and a[1].endswith("/app_assistant_conversation") and a[2].get("apikey") == "cle-publique"]
voir(r.status_code == 200 and liste and liste[-1][2]["Authorization"] == "Bearer " + JETON and liste[-1][3]["user_id"] == "eq." + USER_ID,
     "la liste se lit avec le jeton, filtrée sur SES conversations")
r = client.get(f"/assistant/conversations/{CONV}", headers=ENTETE)
voir(r.status_code == 200 and len(r.json()["conversation"]["messages"]) == 2, "relire une conversation (la RLS dit qui peut)")

httpx.Client.send = _send_origine
if httpx2 is not None:
    httpx2.Client.send = _send_origine2
print(f"\n{ok} contrôles verts")
