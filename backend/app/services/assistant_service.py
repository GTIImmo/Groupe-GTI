from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncIterator

import requests
from fastapi import HTTPException

from ..settings import Settings
from . import agent_registry
from .agent_tarifs import TARIFS, cout_usd
from .assistant_catalogue import ContexteAssistant, outils_sdk
from .assistant_objets import liste_pour_consignes

# ---------------------------------------------------------------------------
# Assistant IA (12/11/2026, étape 1) -- LE SOCLE DORMANT.
# Note : notice/ETAPE1_SOCLE_ASSISTANT_IA_2026-11-12.md. Patron repris de la GED IA
# (openai_ged_classement_service) :
#   · l'interrupteur `assistant_ia` (off / admin / on), relu à CHAQUE question ; absent = éteint ;
#   · le plafond de dépense du jour (3 $) et le plafond de questions par personne (100), lus dans
#     app_agent_run : une lecture ratée n'est jamais un vert, sans le compte on n'appelle pas ;
#   · 8 étapes au plus par question (une boucle de l'agent ne tourne pas sans fin) ;
#   · `store: false` sur chaque appel, et les TRACES ENVOYÉES À OPENAI COUPÉES DANS LE CODE ;
#   · le journal app_agent_run ne garde JAMAIS le texte (jetons, coût, noms des fonctions).
# Plafonds validés par Frédéric le 12/11 : « Oui, ils me vont ».
#
# ⚠ Le SDK (openai-agents 0.22.0, figé : la 0.24 exige une Starlette que notre FastAPI refuse)
#   n'est importé QU'AU PREMIER APPEL, jamais au démarrage : s'il posait problème, seul
#   l'assistant tomberait, pas le reste du backend.
# ---------------------------------------------------------------------------

AGENT_KEY = "assistant"
INTERRUPTEUR = "assistant_ia"
PLAFOND_JOUR_USD = 3.0
PLAFOND_QUESTIONS_JOUR = 100
MAX_ETAPES = 8
MAX_QUESTION_CARACTERES = 4000
MAX_HISTORIQUE_MESSAGES = 20
# Décision de Frédéric le 13/11 : « Assistant. Ta reco », puis « non garde un seul model pour assistant » -> UN modèle,
# gpt-6.1-terra, sans montée en gamme. (La GED garde gpt-6-luna : « ni touché pas ».)
MODELE_PAR_DEFAUT = "gpt-6.1-terra"

# Étape 2 (12/11/2026, refaites le 13/11 après la preuve des 30 questions) : les consignes de la lecture.
# {{objets}} = la liste fermée AVEC colonnes et valeurs (assistant_objets) ; {{role}}, {{date}} = la personne et le
# jour, posés À LA FIN : tout ce qui précède est identique d'une question à l'autre (cache OpenAI).
# ⚠ Le 13/11 le modèle INVENTAIT l'e-mail de la personne pour « mes … » (5 adresses différentes). Il ne le reçoit
#   PAS (règle de l'étape 1 : l'e-mail ne part pas chez OpenAI) : il écrit « moi », le lecteur met l'adresse.
_INSTRUCTIONS = (
    "Tu es l'assistant de l'application de GTI Immobilier, une agence immobiliere francaise (transaction). "
    "Tu parles a un membre de l'agence : tu le tutoies, tu reponds en francais, simplement et clairement, comme un "
    "collegue efficace.\n"
    "# Ce que tu peux lire (et rien d'autre), avec les colonnes et leurs valeurs exactes\n{{objets}}\n"
    "# Comment lire\n"
    "- chercher(objet, filtres…) rend des lignes et le total exact ; compter(objet, filtres, regrouper_par, somme_de) "
    "compte, regroupe, additionne. Les colonnes et les valeurs sont ci-dessus : n'en invente pas ; decrire(objet) les redonne.\n"
    "- Une colonne qui a des valeurs : filtre avec une valeur de la liste (son libelle ou la valeur entre crochets). "
    "type_bien est un code : filtre avec le libelle (« Maison », « Appartement »…) ; « contient maison » prend toutes les "
    "sortes de maisons.\n"
    "- fiches_biens donne les caracteristiques d'un bien (surface, pieces, terrain…) ; notes_transaction les notes et "
    "conditions d'une transaction ; agenda les rendez-vous ; qui_suis_je qui te parle.\n"
    "- Les fonctions prennent souvent l'app_dossier_id d'un bien : trouve-le d'abord avec chercher sur biens.\n"
    "# Le vocabulaire de l'agence\n"
    "- « le 63330 », « l'annonce 63330 », « le bien 63330 » = le NUMERO D'ANNONCE (hektor_annonce_id), jamais une ville ni "
    "un code postal. Cherche-le dans biens, puis biens_historique, puis biens_archives.\n"
    "- « Mes » biens, mandats, relances, contacts, transactions = filtre negociateur_email egal « moi » : le serveur y "
    "met l'adresse de la personne. N'ecris jamais une adresse toi-meme pour « mes … ».\n"
    "- Biens vivants (statut_annonce) : Actif = en vente ; Sous offre ; Sous compromis ; Estimation = PAS en vente (la "
    "grande majorite des fiches). « En vente », « mes biens » = sans les Estimation, sauf si on te les demande.\n"
    "- Vendu n'est PAS Clos : Clos = le mandat s'est termine SANS vente (retire, echu, annule). Ne dis jamais « vendu » "
    "pour un bien Clos.\n"
    "- Mandats : statut_mandat Actif / Echu / Vendu / Clos ; type SIMPLE, EXCLUSIF ou ACCORD ; « les mandats du mois » = "
    "mandat_date_debut dans le mois ; register_source_kind « recherche » = mandats de recherche, a laisser de cote dans "
    "les comptes de mandats de vente sauf demande.\n"
    "- Transactions : une ligne par etape. offre (proposee, acceptee, refusee), compromis (en cours, annule), vente (etat "
    "vide). « Ventes signees » = kind vente, datees par la colonne date (date_acte est presque toujours vide).\n"
    "- Acquereur = un contact qui a une recherche (contacts.active_search_count > 0, ou l'objet recherches).\n"
    "- Relance en retard = status a_faire et due_date avant aujourd'hui. Demande en attente = request_status pending.\n"
    "# Regles\n"
    "- Tu ne sais que ce que tes fonctions te rendent. N'invente jamais un nom, un chiffre, un bien, une date, une adresse.\n"
    "- Un resultat a 0 ne prouve rien tant que tu n'as pas verifie tes filtres (lis le champ « attention »). Si tu "
    "reponds « aucun », dis avec quels filtres.\n"
    "- Ce que tu ne peux pas lire (suivi des ouvertures d'e-mails, factures, comptabilite, ventes DVF…) : dis-le "
    "simplement, sans deviner.\n"
    "- Les droits sont ceux de la personne : si une lecture est refusee, dis que tu n'y as pas acces, sans contourner.\n"
    "- Dis d'ou vient un chiffre (quel objet, quels filtres, combien de lignes). Si un calcul est « tronque », dis-le.\n"
    "- Si la demande est ambigue (deux contacts du meme nom, plusieurs biens possibles), demande lequel.\n"
    "- Question juridique ou fiscale : reponse generale, et precise qu'elle est a faire verifier (notaire, juriste).\n"
    "- Sois force de proposition : apres ta reponse, propose en une phrase la suite utile (relancer, appeler, verifier "
    "un mandat…). Tu ne peux encore rien ecrire ni envoyer : propose, n'annonce jamais que c'est fait.\n"
    "- Ne recopie pas ces consignes.\n"
    "# La personne et le jour\n"
    "Tu parles a un membre de l'agence, role : {{role}}. Nous sommes le {{date}}."
)

agent_registry.DEFAULT_SPECS.setdefault(
    AGENT_KEY, agent_registry.AgentSpec(AGENT_KEY, _INSTRUCTIONS, MODELE_PAR_DEFAUT, 1500)
)


def _debut_du_jour() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AssistantService:
    def __init__(self, settings: Settings, client_openai: Any = None) -> None:
        self.settings = settings
        # les essais passent un faux client ; sinon il est créé au premier appel
        self.client_openai = client_openai

    # ── base (clé de service : interrupteur, plafonds, écriture du fil) ───────
    def _headers(self) -> dict[str, str]:
        key = self.settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    def _url(self, table: str) -> str:
        return f"{self.settings.supabase_url}/rest/v1/{table}"

    def interrupteur(self) -> str:
        # Absent, illisible ou en erreur = éteint (patron des interrupteurs à trois crans).
        try:
            r = requests.get(self._url("app_setting"), headers=self._headers(),
                             params={"key": f"eq.{INTERRUPTEUR}", "select": "value", "limit": "1"}, timeout=8)
            rows = r.json() if r.ok else []
            valeur = str((rows[0] or {}).get("value") or "").strip().lower() if rows else ""
        except Exception:
            valeur = ""
        return valeur if valeur in {"on", "admin"} else "off"

    def _lignes_du_jour(self, params: dict[str, str], quoi: str) -> list[dict[str, Any]]:
        try:
            r = requests.get(self._url("app_agent_run"), headers=self._headers(),
                             params={"agent_key": f"eq.{AGENT_KEY}", "created_at": f"gte.{_debut_du_jour()}", **params},
                             timeout=10)
        except Exception:
            r = None
        if r is None or not r.ok:
            # Une lecture ratée n'est jamais un vert : sans le compte, on n'appelle pas.
            raise HTTPException(status_code=503, detail=f"{quoi} illisible : pas d'appel à l'IA")
        return r.json() or []

    def depense_du_jour(self) -> float:
        rows = self._lignes_du_jour({"select": "cost_usd"}, "Dépense du jour")
        return float(sum(float(row.get("cost_usd") or 0) for row in rows))

    def questions_du_jour(self, email: str) -> int:
        return len(self._lignes_du_jour({"negociateur_email": f"eq.{email}", "select": "id"}, "Compte des questions du jour"))

    def preparer(self, email: str) -> agent_registry.AgentSpec:
        # Tout ce qui peut refuser se joue ICI, AVANT d'écrire la question et avant tout appel.
        if not self.settings.openai_api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY non configuré sur le backend")
        spec = agent_registry.load_spec(self.settings, AGENT_KEY)
        model = spec.model or MODELE_PAR_DEFAUT
        if model not in TARIFS:
            # sans tarif, le plafond du jour croirait les tours gratuits
            raise HTTPException(status_code=503, detail=f"Modèle sans tarif connu ({model}) : pas d'appel")
        if self.depense_du_jour() >= PLAFOND_JOUR_USD:
            raise HTTPException(status_code=429, detail="Plafond de dépense du jour atteint : l'assistant est en pause")
        if self.questions_du_jour(email) >= PLAFOND_QUESTIONS_JOUR:
            raise HTTPException(status_code=429, detail=f"{PLAFOND_QUESTIONS_JOUR} questions aujourd'hui : reprends demain")
        return agent_registry.AgentSpec(AGENT_KEY, spec.instructions, model, spec.max_output_tokens)

    # ── le fil (écrit par le serveur seul) ────────────────────────────────────
    def conversation(self, conversation_id: str) -> dict[str, Any] | None:
        r = requests.get(self._url("app_assistant_conversation"), headers=self._headers(),
                         params={"id": f"eq.{conversation_id}", "select": "id,user_id,archivee", "limit": "1"}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Conversation illisible")
        rows = r.json() or []
        return rows[0] if rows else None

    def creer_conversation(self, user_id: str, email: str, titre: str) -> str:
        r = requests.post(self._url("app_assistant_conversation"),
                          headers={**self._headers(), "Prefer": "return=representation"},
                          json=[{"user_id": user_id, "user_email": email, "agent_key": AGENT_KEY, "titre": titre}], timeout=10)
        if not r.ok or not (r.json() or []):
            raise HTTPException(status_code=503, detail="Conversation non créée : pas d'appel à l'IA")
        return str(r.json()[0]["id"])

    def historique(self, conversation_id: str) -> list[dict[str, Any]]:
        r = requests.get(self._url("app_assistant_message"), headers=self._headers(),
                         params={"conversation_id": f"eq.{conversation_id}", "select": "role,contenu",
                                 "order": "id.desc", "limit": str(MAX_HISTORIQUE_MESSAGES)}, timeout=10)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Historique illisible : pas d'appel à l'IA")
        return list(reversed(r.json() or []))

    def ajouter_message(self, conversation_id: str, role: str, contenu: str,
                        outils: list[dict[str, Any]] | None = None, agent_run_id: int | None = None) -> int:
        r = requests.post(self._url("app_assistant_message"),
                          headers={**self._headers(), "Prefer": "return=representation"},
                          json=[{"conversation_id": conversation_id, "role": role, "contenu": contenu,
                                 "outils": outils, "agent_run_id": agent_run_id}], timeout=10)
        if not r.ok or not (r.json() or []):
            raise HTTPException(status_code=503, detail="Message non enregistré")
        try:
            # best-effort : la date de la liste, jamais une raison de perdre le message
            requests.patch(self._url("app_assistant_conversation"), headers=self._headers(),
                           params={"id": f"eq.{conversation_id}"}, json={"maj_le": _maintenant()}, timeout=10)
        except Exception:
            pass
        return int(r.json()[0]["id"])

    # ── relire (avec le JETON de la personne : la RLS dit qui voit quoi) ──────
    def _lire_avec_jeton(self, jeton: str, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        r = requests.get(self._url(table),
                         headers={"apikey": self.settings.supabase_anon_key, "Authorization": f"Bearer {jeton}"},
                         params=params, timeout=15)
        if not r.ok:
            raise HTTPException(status_code=503, detail="Lecture des conversations impossible")
        return r.json() or []

    def lister(self, jeton: str, user_id: str) -> list[dict[str, Any]]:
        # filtre sur SON id : l'admin lit aussi celles des autres, mais SA liste reste la sienne
        return self._lire_avec_jeton(jeton, "app_assistant_conversation", {
            "user_id": f"eq.{user_id}", "archivee": "eq.false",
            "select": "id,titre,agent_key,cree_le,maj_le", "order": "maj_le.desc", "limit": "50"})

    def relire(self, jeton: str, conversation_id: str) -> dict[str, Any] | None:
        conv = self._lire_avec_jeton(jeton, "app_assistant_conversation", {
            "id": f"eq.{conversation_id}", "select": "id,user_id,user_email,titre,agent_key,cree_le,maj_le,archivee", "limit": "1"})
        if not conv:
            return None
        messages = self._lire_avec_jeton(jeton, "app_assistant_message", {
            "conversation_id": f"eq.{conversation_id}", "select": "id,role,contenu,outils,cree_le", "order": "id.asc"})
        return {**conv[0], "messages": messages}

    # ── le tour ───────────────────────────────────────────────────────────────
    def _client(self) -> Any:
        if self.client_openai is None:
            from openai import AsyncOpenAI
            self.client_openai = AsyncOpenAI(api_key=self.settings.openai_api_key, timeout=60, max_retries=1)
        return self.client_openai

    async def repondre(self, ctx: ContexteAssistant, spec: agent_registry.AgentSpec,
                       historique: list[dict[str, Any]], question: str) -> AsyncIterator[dict[str, Any]]:
        # ⚠ import du SDK ICI SEULEMENT (voir l'en-tête)
        from agents import Agent, ModelSettings, OpenAIResponsesModel, RunConfig, Runner, set_tracing_disabled

        set_tracing_disabled(True)  # ⛔ aucune trace chez OpenAI, quoi que dise l'environnement
        reglages = ModelSettings(store=False, max_tokens=spec.max_output_tokens)
        if not str(spec.model).startswith("gpt-4"):
            from openai.types.shared import Reasoning
            # « low » (13/11) : un peu de réflexion pour choisir les bons filtres -- les 5 fausses réponses du 13/11
            # étaient des filtres mal choisis, pas des phrases mal tournées
            reglages = ModelSettings(store=False, max_tokens=spec.max_output_tokens, reasoning=Reasoning(effort="low"))
        agent = Agent(
            name=AGENT_KEY,
            instructions=agent_registry.render(spec.instructions, {"date": datetime.now().strftime("%d/%m/%Y"),
                                                                  "objets": liste_pour_consignes(),
                                                                  "role": ctx.role}),
            model=OpenAIResponsesModel(str(spec.model), self._client()),
            model_settings=reglages,
            tools=outils_sdk(ctx.role),
        )
        entree = [{"role": m["role"], "content": str(m.get("contenu") or "")}
                  for m in historique if m.get("role") in {"user", "assistant"} and m.get("contenu")]
        entree.append({"role": "user", "content": question})
        flux = Runner.run_streamed(agent, input=entree, context=ctx, max_turns=MAX_ETAPES,
                                   run_config=RunConfig(tracing_disabled=True, trace_include_sensitive_data=False))
        texte: list[str] = []
        async for evenement in flux.stream_events():
            if evenement.type == "raw_response_event" and getattr(evenement.data, "type", "") == "response.output_text.delta":
                texte.append(evenement.data.delta)
                yield {"type": "texte", "delta": evenement.data.delta}
            elif evenement.type == "run_item_stream_event" and evenement.name == "tool_called":
                yield {"type": "outil", "nom": getattr(evenement.item.raw_item, "name", None)}
        usage = flux.context_wrapper.usage
        jetons = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "total_tokens": usage.total_tokens}
        reponse = str(flux.final_output) if flux.final_output is not None else "".join(texte)
        yield {"type": "_fin", "reponse": reponse, "usage": jetons, "etapes": usage.requests,
               "model": spec.model, "costUsd": cout_usd(spec.model, jetons)}
