"""Assistant IA, le TROMBONE (17/11/2026) — déposer des fichiers de l'ordinateur dans la conversation.

Lancer depuis backend/ :  <python> tests/test_assistant_fichiers.py     (sans réseau)
requests.post / delete sont remplacés par un faux coffre qui enregistre chaque appel.
Vérifie : les règles AVANT l'envoi (types du coffre, .odt expliqué, 50 Mo) ; l'adresse signée vise UN fichier sous
temp/assistant/<la personne>/<numéro>/ ; la RELECTURE après dépôt (ce qui est vraiment au coffre) et la SUPPRESSION
d'un fichier hors règles ; le retrait ne touche que le dossier de la personne ; le modèle ne voit que nom, type, taille.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from app.services import assistant_fichiers as af

ok = 0


def voir(vrai, libelle):
    global ok
    assert vrai, libelle
    ok += 1
    print("  VERT  " + libelle)


def refuse(fonction, morceau=""):
    try:
        fonction()
    except af.RefusFichier as exc:
        return morceau in str(exc)
    return False


class Settings:
    supabase_url = "https://x.supabase.co"
    supabase_anon_key = "cle-publique"
    supabase_service_role_key = "cle-de-service"


class Reponse:
    def __init__(self, data, status=200):
        self.status_code, self._data, self.ok = status, data, status < 400
        self.text = json.dumps(data)

    def json(self):
        return self._data


UID = "d4b1685f-948b-4ce8-af15-671b94a725e6"
AUTRE = "11111111-2222-3333-4444-555555555555"
appels = []
coffre = {}  # chemin -> {"size", "mimetype"}


def faux(methode, url, **kw):
    appels.append({"methode": methode, "url": url, "corps": kw.get("json"), "entetes": kw.get("headers") or {}})
    if "/object/upload/sign/" in url:
        chemin = url.split("/object/upload/sign/hektor-console-documents/", 1)[1]
        return Reponse({"url": f"/object/upload/sign/hektor-console-documents/{chemin}?token=jeton-signe"})
    if "/object/list/" in url:
        prefixe = kw["json"]["prefix"]
        return Reponse([{"name": c[len(prefixe):], "id": "o1", "metadata": m} for c, m in coffre.items() if c.startswith(prefixe)])
    if methode == "DELETE":
        for c in kw["json"]["prefixes"]:
            coffre.pop(c, None)
        return Reponse([{"name": c} for c in kw["json"]["prefixes"]])
    return Reponse({}, 500)


requests.post = lambda url, **kw: faux("POST", url, **kw)
requests.delete = lambda url, **kw: faux("DELETE", url, **kw)
S = Settings()

print("1) les règles AVANT l'envoi -- celles du coffre, dites en clair")
voir(af.controler_annonce("Mandat.pdf", "application/pdf", 1200) == "application/pdf", "un PDF : accepté")
voir(refuse(lambda: af.controler_annonce("estimation.odt", "application/vnd.oasis.opendocument.text", 1000), "LibreOffice")
     and refuse(lambda: af.controler_annonce("IMG.HEIC", "image/heic", 1000), "JPEG"),
     "un .odt et une photo HEIC : refusés AVEC la raison (le coffre les refusait en silence)")
voir(refuse(lambda: af.controler_annonce("x.exe", "application/x-msdownload", 1000), "pas accepté"),
     "un type inconnu du coffre : refusé")
voir(refuse(lambda: af.controler_annonce("gros.pdf", "application/pdf", 50 * 1024 * 1024 + 1), "50 Mo")
     and refuse(lambda: af.controler_annonce("vide.pdf", "application/pdf", 0), "vide"),
     "plus de 50 Mo, ou vide : refusés")
voir(set(af.TYPES_ACCEPTES) == {"application/pdf", "image/jpeg", "image/png", "image/webp", "application/msword",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                "application/vnd.ms-excel",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/plain",
                                "application/zip"},
     "la liste = celle du coffre hektor-console-documents (storage.buckets, lue le 17/11)")

print("2) l'adresse signée : UN fichier, sous le dossier de la personne, par la clé de service du SERVEUR")
appels.clear()
d = af.preparer_depot(S, UID, "Mandat signé Dupont.pdf", "application/pdf", 1200)
voir(d["chemin"] == f"temp/assistant/{UID}/{d['id']}/Mandat_signe_Dupont.pdf" and d["jeton"] == "jeton-signe"
     and len(d["id"]) == 32 and d["bucket"] == "hektor-console-documents",
     "le chemin porte la PERSONNE (son jeton) et un numéro neuf ; le nom sans accents ; le jeton d'envoi rendu")
voir(appels[0]["entetes"].get("Authorization") == "Bearer cle-de-service" and "/object/upload/sign/" in appels[0]["url"],
     "l'adresse est fabriquée par le serveur (la règle du coffre refuserait un dépôt libre avec le jeton de la personne)")
appels.clear()
voir(refuse(lambda: af.preparer_depot(S, UID, "e.odt", "application/vnd.oasis.opendocument.text", 10), "LibreOffice")
     and not appels, "un type refusé : AUCUNE adresse n'est fabriquée")
voir(refuse(lambda: af.preparer_depot(S, "pas-un-compte", "a.pdf", "application/pdf", 10), "Compte"),
     "un compte illisible : refusé")

print("3) la relecture après le dépôt : ce qui est VRAIMENT au coffre")
coffre[d["chemin"]] = {"size": 1200, "mimetype": "application/pdf"}
f = af.decrire(S, UID, d["id"])
voir(f["nom"] == "Mandat_signe_Dupont.pdf" and f["taille"] == 1200 and f["libelle"] == "PDF", "relu : nom, taille, type réels")
voir(refuse(lambda: af.decrire(S, AUTRE, d["id"]), "pas (ou plus)"),
     "⛔ une autre personne ne voit pas ce fichier (le dossier porte l'identifiant pris dans le jeton)")
truque = af.preparer_depot(S, UID, "photo.jpg", "image/jpeg", 2000)
coffre[truque["chemin"]] = {"size": 2000, "mimetype": "application/x-msdownload"}
voir(refuse(lambda: af.decrire(S, UID, truque["id"]), "pas accepté") and truque["chemin"] not in coffre,
     "⛔ TÉMOIN : un fichier annoncé photo mais déposé autre chose -> refusé ET SUPPRIMÉ du coffre")
voir(refuse(lambda: af.decrire(S, UID, "deadbeef"), "illisible"), "un numéro illisible : refusé")

print("4) le retrait ne touche que le dossier de la personne")
coffre[f"temp/assistant/{AUTRE}/{d['id']}/autre.pdf"] = {"size": 9, "mimetype": "application/pdf"}
voir(af.retirer(S, UID, d["id"]) == 1 and d["chemin"] not in coffre and f"temp/assistant/{AUTRE}/{d['id']}/autre.pdf" in coffre,
     "retirer : SON fichier part, celui d'une autre personne au même numéro reste")

print("5) ce que le modèle voit : nom, type, taille -- jamais le contenu")
texte = af.decrire_pour_le_modele([{"id": "a" * 32, "nom": "Mandat.pdf", "libelle": "PDF", "taille": 1258291},
                                   {"id": "b" * 32, "nom": "photo.jpg", "libelle": "photo JPEG", "taille": 300000}])
voir(texte.startswith("\n\n[Fichiers joints par la personne") and f"fichier:{'a' * 32} « Mandat.pdf » (PDF, 1,2 Mo)" in texte
     and "JAMAIS leur contenu" in texte and af.decrire_pour_le_modele([]) == "",
     "la marque que l'écran sait retirer (separerFichiersJoints) ; rien si aucun fichier")

print("6) la copie au coffre (carte « ajouter une photo ») : seulement DEPUIS le trombone")
appels.clear()
voir(refuse(lambda: af.copier(S, "annonces/62963/documents/x/mandat.pdf", "temp/photos/j/x.pdf"), "pas un fichier joint")
     and refuse(lambda: af.copier(S, f"temp/assistant/{UID}/../../annonces/x.pdf", "temp/photos/j/x.pdf"), "pas un fichier joint")
     and not appels,
     "⛔ une source hors de temp/assistant/ (ou qui en remonte) : refusée, le coffre n'est même pas appelé")
requests.post = lambda url, **kw: (appels.append({"url": url, "corps": kw.get("json")}) or Reponse({"Key": "ok"}))
af.copier(S, f"temp/assistant/{UID}/{'a' * 32}/facade.jpg", "temp/photos/j1/facade.jpg")
voir(appels[-1]["url"].endswith("/storage/v1/object/copy") and appels[-1]["corps"] == {
        "bucketId": "hektor-console-documents", "sourceKey": f"temp/assistant/{UID}/{'a' * 32}/facade.jpg",
        "destinationKey": "temp/photos/j1/facade.jpg"},
     "la copie : du trombone vers la place du travail, dans le même coffre")

print(f"\n{ok} contrôles verts")
