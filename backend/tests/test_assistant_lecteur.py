"""Assistant IA, étape 2 (12/11/2026) — le lecteur sur la liste fermée.

Lancer depuis backend/ :  <python> tests/test_assistant_lecteur.py     (sans réseau, sans le SDK)
requests.get est remplacé par un faux qui enregistre l'adresse, les en-têtes et les paramètres.
Vérifie : la liste fermée (objet, colonne, opérateur), la traduction des filtres et leurs pièges (texte comparé,
joker, guillemets), le JETON de la personne et jamais la clé de service, les filtres IMPOSÉS (notifications,
fiches de ménage), le total exact, le plafond qui DIT qu'il a coupé, la fiche sans les coordonnées des
propriétaires, les notes lues seulement APRÈS la transaction, l'agenda par la route de l'écran.
"""
import asyncio, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from app.services import assistant_catalogue as cat
from app.services import assistant_lecteur as lec
from app.services import assistant_objets as obj
from app.services import assistant_service as svc

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


JETON = "jeton.de.paul"
EMAIL = "paul@gti-immobilier.fr"
ctx = cat.ContexteAssistant(Settings(), "u-1", EMAIL, "commercial", JETON)


class Reponse:
    def __init__(self, data, status=200, plage=None):
        self.status_code, self._data, self.ok = status, data, status < 400
        self.headers = {"Content-Range": plage} if plage else {}

    def json(self):
        return self._data


appels = []
regles = {}  # source -> fonction(params, en-têtes) -> Reponse


def faux_get(url, headers=None, params=None, timeout=None):
    source = url.rsplit("/", 1)[1]
    appels.append({"source": source, "entetes": dict(headers or {}), "params": list(params or [])})
    if source in regles:
        return regles[source](list(params or []), dict(headers or {}))
    return Reponse([], plage="*/0")


requests.get = faux_get


def params_de(n=-1):
    return appels[n]["params"]


print("1) la liste fermée")
voir(all(set(o.par_defaut) <= {c.nom for c in o.colonnes} and o.colonne(o.cle) for o in obj.OBJETS),
     "chaque objet : colonnes par défaut et clé déclarées dans ses colonnes")
interdites = {"app_affaire_note", "app_affaire_condition", "app_proposition", "app_bien_acquereur_statut", "app_alert_state",
              "app_setting", "app_agent_run", "app_console_job", "app_user_profile"}
voir(not ({o.source for o in obj.OBJETS} & interdites), "aucune table « lisible par tous » ni technique n'est un objet")
voir(not any("avant" in o.source or "sauvegarde" in o.source for o in obj.OBJETS), "aucune sauvegarde datée")
notif = obj.PAR_NOM["notifications"]
voir(notif.filtres_imposes(EMAIL) == [("negociateur_email", f"eq.{EMAIL}")] and not notif.colonne("negociateur_email"),
     "notifications : filtre IMPOSÉ sur l'e-mail, et la colonne n'est même pas offerte au modèle")
voir(refuse(lambda: lec.decrire(ctx, {"objet": "app_user_profile"}), "Objet inconnu"), "un objet hors liste est refusé")
voir(lec.decrire(ctx, {"objet": "mandats"})["colonnes"][-3]["nom"] == "statut_mandat", "decrire rend les colonnes et leur sens")
voir(refuse(lambda: lec.chercher(ctx, {"objet": "documents", "colonnes": ["storage_path"]}), "Colonne inconnue"),
     "une colonne hors liste est refusée (chemin de stockage d'un document)")
voir(refuse(lambda: lec.chercher(ctx, {"objet": "contacts", "filtres": [{"colonne": "couple_role", "operateur": "egal", "valeur": "x"}]})),
     "on ne filtre pas sur une colonne cachée (rôle de couple)")

print("2) la traduction des filtres")
biens, rech = obj.PAR_NOM["biens"], obj.PAR_NOM["recherches"]
voir(lec.traduire_filtres(biens, [{"colonne": "prix", "operateur": "inferieur_ou_egal", "valeur": "250 000"}]) == [("prix", "lte.250000")],
     "prix ≤ 250 000 → lte.250000 (espaces retirés)")
voir(refuse(lambda: lec.traduire_filtres(rech, [{"colonne": "prix_max", "operateur": "superieur", "valeur": "200000"}]), "impossible"),
     "un montant stocké en TEXTE ne se compare pas (« 90000 » > « 200000 » en texte)")
voir(refuse(lambda: lec.traduire_filtres(biens, [{"colonne": "prix", "operateur": "egal", "valeur": "beaucoup"}]), "pas un nombre"),
     "une valeur illisible est refusée avant toute lecture")
voir(lec.traduire_filtres(biens, [{"colonne": "mandat_date_fin", "operateur": "inferieur", "valeur": "2026-11-30"}]) == [("mandat_date_fin", "lt.2026-11-30")],
     "date < 2026-11-30 (texte AAAA-MM-JJ, comparable dans l'ordre)")
voir(lec.traduire_filtres(biens, [{"colonne": "ville", "operateur": "contient", "valeur": "*Fir%miny*"}]) == [("ville", "ilike.*Firminy*")],
     "« contient » : les jokers glissés par le modèle sont retirés")
voir(lec.traduire_filtres(biens, [{"colonne": "statut_annonce", "operateur": "parmi", "valeur": 'Actif|Sous offre|a",b)'}])
     == [("statut_annonce", 'in.("Actif","Sous offre","a\\",b)")')], "« parmi » : chaque valeur entre guillemets, guillemets échappés")
voir(lec.traduire_filtres(obj.PAR_NOM["contacts"], [{"colonne": "relation_roles_json", "operateur": "json_contient", "valeur": "mandant"}])
     == [("relation_roles_json", 'cs.["mandant"]')], "rôle « mandant » dans la liste des rôles")
voir(lec.traduire_filtres(obj.PAR_NOM["contacts"], [{"colonne": "archive", "operateur": "egal", "valeur": "non"}]) == [("archive", "eq.false")],
     "booléen : « non » → false")
voir(lec.traduire_filtres(biens, [{"colonne": "photo_url_listing", "operateur": "est_vide", "valeur": ""}]) == [("photo_url_listing", "is.null")],
     "« est vide » → is.null (les biens sans photo)")

print("3) chercher : le jeton, le total, la limite")
regles["app_dossiers_current"] = lambda p, h: Reponse([{"hektor_annonce_id": 63330, "titre_bien": "x" * 500}], plage="0-0/37")
r = lec.chercher(ctx, {"objet": "biens", "filtres": [{"colonne": "ville", "operateur": "egal", "valeur": "Unieux"}],
                       "colonnes": [], "tri": "", "ordre": "desc", "limite": 500})
a = appels[-1]
voir(a["entetes"]["Authorization"] == "Bearer " + JETON and a["entetes"]["apikey"] == "cle-publique", "la lecture part avec le JETON de la personne")
voir("cle-de-service" not in json.dumps(appels), "et jamais avec la clé de service")
voir(a["entetes"]["Prefer"] == "count=exact" and r["total"] == 37, "le total exact vient de la base (37), pas des lignes rendues")
voir(a["entetes"]["Range"] == f"0-{lec.MAX_LIGNES_RENDUES - 1}", f"une limite de 500 est ramenée à {lec.MAX_LIGNES_RENDUES}")
voir(("ville", "eq.Unieux") in a["params"] and ("order", "app_dossier_id.desc.nullslast") in a["params"], "filtre et tri par défaut")
voir(dict(a["params"])["select"].split(",") == list(biens.par_defaut), "colonnes par défaut")
voir(len(r["lignes"][0]["titre_bien"]) == lec.MAX_CARACTERES_VALEUR + 1, "une valeur trop longue est coupée")
lec.chercher(ctx, {"objet": "notifications", "filtres": [], "colonnes": [], "tri": "", "ordre": "desc", "limite": 5})
voir(("negociateur_email", f"eq.{EMAIL}") in params_de(), "notifications : le filtre imposé part bien")
lec.chercher(ctx, {"objet": "contacts", "filtres": [], "colonnes": [], "tri": "", "ordre": "desc", "limite": 5})
voir(("or", "(couple_role.is.null,couple_role.neq.menage_resolu)") in params_de(), "contacts : les fiches de ménage masquées comme à l'écran")
regles["app_v_mandat_statut"] = lambda p, h: Reponse({"message": "not found"}, status=404)
voir(refuse(lambda: lec.chercher(ctx, {"objet": "mandats"}), "pas encore disponible"),
     "la vue des mandats pas encore posée : refus en clair, pas une panne")

print("4) compter : total, regroupement, plafond")
regles["app_relance_rapprochement"] = lambda p, h: Reponse([], plage="*/12")
voir(lec.compter(ctx, {"objet": "relances", "filtres": [], "regrouper_par": "", "somme_de": ""}) == {"objet": "relances", "total": 12},
     "compter sans regroupement = le total exact de la base")


def pages(p, h):
    debut, fin = map(int, h["Range"].split("-"))
    return Reponse([{"commercial_nom": "A" if i % 3 else "B", "prix": 100} for i in range(debut, min(fin + 1, 12000))],
                   plage=f"{debut}-{fin}/12000")


regles["app_dossiers_current"] = pages
r = lec.compter(ctx, {"objet": "biens", "filtres": [], "regrouper_par": "commercial_nom", "somme_de": "prix"})
voir(r["lignes_lues"] == lec.PLAFOND_LIGNES_CALCUL and r["tronque"] is True and r["total"] == 12000,
     f"12 000 lignes : on en lit {lec.PLAFOND_LIGNES_CALCUL} et la réponse DIT « tronqué »")
voir(sum(g["nombre"] for g in r["groupes"]) == lec.PLAFOND_LIGNES_CALCUL and r["groupes"][0]["somme"] > 0, "regroupement et somme sur les lignes lues")
voir(refuse(lambda: lec.compter(ctx, {"objet": "biens", "filtres": [], "regrouper_par": "", "somme_de": "ville"}), "nombre"),
     "on n'additionne pas une colonne texte")

print("5) les fonctions métier")
payload = {"surface_habitable_detail": "120", "nb_pieces": "5", "proprietaires_contacts": "0674586469 · vendeur@exemple.fr",
           "proprietaires_json": '[{"nom": "VENDEUR"}]', "texte_principal_html": "<p>Belle maison &amp; jardin</p>",
           "terrain_json": json.dumps({"props": {"surf": {"label": "Surface <b>terrain</b>", "value": "800"}, "vide": {"label": "x", "value": "0"}}})}
regles["app_dossier_details_current"] = lambda p, h: Reponse([{"app_dossier_id": 7, "hektor_annonce_id": 63330, "detail_payload_json": json.dumps(payload)}])
r = lec.fiches_biens(ctx, {"app_dossier_ids": list(range(1, 20)) + [7]})
fiche = json.dumps(r, ensure_ascii=False)
voir(r["fiches"][0]["surface_habitable_detail"] == "120" and "Surface terrain : 800" in r["fiches"][0]["caracteristiques"],
     "la fiche rend surfaces, pièces et caractéristiques lisibles")
voir("0674586469" not in fiche and "vendeur@exemple.fr" not in fiche and "VENDEUR" not in fiche,
     "⛔ ni le téléphone, ni l'e-mail, ni le nom des propriétaires")
voir(r["fiches"][0]["texte_annonce"] == "Belle maison & jardin", "le texte de l'annonce, sans HTML")
voir(dict(params_de())["app_dossier_id"].count(",") == lec.MAX_FICHES - 1, f"{lec.MAX_FICHES} fiches au plus par appel")

regles["app_affaire_ledger"] = lambda p, h: Reponse([])
appels.clear()
voir(refuse(lambda: lec.notes_transaction(ctx, {"app_affaire_id": 5}), "hors de tes droits"), "transaction invisible : refus")
voir([a["source"] for a in appels] == ["app_affaire_ledger"], "⛔ et ses notes ne sont PAS lues (elles sont lisibles par tous en base)")
regles["app_affaire_ledger"] = lambda p, h: Reponse([{"app_affaire_id": 5, "kind": "compromis", "state": "en_cours", "app_dossier_id": 7}])
regles["app_affaire_note"] = lambda p, h: Reponse([{"texte": "note", "ecrit_le": "2026-11-01", "origine": "app"}])
r = lec.notes_transaction(ctx, {"app_affaire_id": 5})
voir([a["source"] for a in appels[-3:]] == ["app_affaire_ledger", "app_affaire_note", "app_affaire_condition"] and r["notes"][0]["texte"] == "note",
     "transaction visible : la transaction D'ABORD, puis ses notes et conditions, avec le jeton")

vu = {}


def fausse_route(**k):
    vu.update(k)
    return {"ok": True, "events": [{"summary": "Visite 63330", "starts_at": "2026-11-13T14:00:00", "status": "confirmed"},
                                   {"summary": "annulé", "starts_at": "2026-11-13T15:00:00", "status": "deleted"}]}


from app.routers import google_workspace as gw  # noqa: E402
gw.list_google_calendar_event_links = fausse_route
r = lec.agenda(ctx, {"debut": "2026-11-13", "fin": "2026-11-14", "app_dossier_id": 0, "hektor_contact_id": ""})
voir(vu["authorization"] == "Bearer " + JETON and vu["calendarEmail"] is None and vu["limit"] == 50,
     "l'agenda passe par la route de l'écran, avec le jeton : sa garde décide de l'agenda lu")
voir(r["nombre"] == 1 and r["evenements"][0]["summary"] == "Visite 63330", "les rendez-vous supprimés sont retirés, comme l'écran")

print("6) le modèle reçoit un refus en clair")
trace_ctx = cat.ContexteAssistant(Settings(), "u-1", EMAIL, "commercial", JETON)
chercher = next(f for f in cat.CATALOGUE if f.nom == "chercher")
texte = asyncio.run(cat.appeler(trace_ctx, chercher, json.dumps({"objet": "salaires"})))
voir(texte.startswith("Refusé : Objet inconnu") and trace_ctx.appels[0]["erreur"] == "refus", "un refus part au modèle tel quel, et se trace")
consignes = svc.agent_registry.render(svc._INSTRUCTIONS, {"date": "12/11/2026", "objets": obj.liste_pour_consignes()})
voir(all(o.nom in consignes for o in obj.OBJETS) and "{{" not in consignes, "les consignes listent les 14 objets, rien n'est laissé en gabarit")
voir(len(obj.OBJETS) == 14, "14 objets dans la liste fermée")

print(f"\n{ok} contrôles verts")
