"""Tests Lot A — template email de rapprochement (purs, sans DB).

Lancer depuis backend/ :  ../.venv/Scripts/python.exe tests/test_rapprochement_email.py
Couvre : signature/expiration des tokens, mapping honoraires (loi Hoguet) sur
biens réels, arbitrage d'ambiguïté de charge, build HTML (bulletproof/dark/poids)
et version texte.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services import email_tokens as T
from app.services.rapprochement_email import (
    format_honoraires, build_email_html, build_email_text, build_bien_view,
)

SECRET = "test-secret"

# 1) Tokens : round-trip + détection d'altération
tok = T.make_feedback_token(envoi_id="E1", bien_id=3137, action=T.ACTION_LIKE, secret=SECRET)
p = T.verify_token(tok, SECRET)
assert p and p["a"] == "like" and p["b"] == "3137", p
assert T.verify_token(tok, "wrong-secret") is None, "signature non vérifiée !"
assert T.verify_token(tok[:-2] + "xx", SECRET) is None, "altération non détectée !"
unsub = T.verify_token(T.make_unsub_token(envoi_id="E1", secret=SECRET), SECRET)
assert unsub and unsub["x"] is None, "unsub doit être sans expiration"
print("1) tokens OK")

# 2) Honoraires sur 3 biens réels
h1 = format_honoraires("74900.0", '[{"id":"1","taux":"7000","charge":"Acheteur"},{"id":"2","taux":"7000","charge":"Acheteur"}]')
h2 = format_honoraires("449000.0", '[{"id":"1","taux":"19000","charge":"acheteur"}]')
h3 = format_honoraires("76600.0", '[{"id":"1","taux":"6600","charge":"vendeur"}]')
print("  3137 :", h1["price_main"], "|", h1["sub"], "|", h1.get("net"))
print("  18503:", h2["price_main"], "|", h2["sub"], "|", h2.get("net"))
print("  107427:", h3["price_main"], "|", h3["sub"])
assert h1["price_main"] == "74 900 € FAI" and "10,3 %" in h1["sub"] and "67 900" in h1["net"]
assert h2["price_main"] == "449 000 € FAI" and "4,4 %" in h2["sub"] and "430 000" in h2["net"]
assert h3["price_main"] == "76 600 €" and "vendeur" in h3["sub"]
# Ambiguïté : 2 charges → on privilégie acquéreur
hamb = format_honoraires("49600", '[{"taux":"4600","charge":"acheteur"},{"taux":"5100","charge":"vendeur"}]')
assert hamb["charge"] == "acquereur", hamb
print("2) honoraires OK (dont arbitrage ambiguïté)")

# 3) Build HTML + texte (multi-biens)
def fake_view(dossier_id, titre, prix, hono_raw, photo):
    d = {"app_dossier_id": dossier_id, "hektor_annonce_id": dossier_id, "titre_bien": titre,
         "numero_mandat": f"M{dossier_id}", "ville": "Firminy", "code_postal": "42700",
         "prix": prix, "photo_url_listing": photo}
    det = {"surface": "92", "nb_pieces": "4", "nb_chambres": "3", "honoraires_json": hono_raw}
    v = build_bien_view(d, det)
    v["_links"] = {"like": "https://x/r/feedback/like", "pass": "https://x/r/feedback/pass",
                   "visite": "https://x/rdv/tok"}
    return v

biens = [
    fake_view(3137, "Maison en pierres avec terrain", "74900", '[{"taux":"7000","charge":"Acheteur"}]',
              "https://groupe-gti-immobilier.staticlbi.com/original/images/biens/1/x/photo.jpg"),
    fake_view(107427, "Appartement lumineux centre-ville", "76600", '[{"taux":"6600","charge":"vendeur"}]', ""),
]
ctx = {
    "subject": "2 biens pour votre recherche", "preheader": "Deux biens pour vous",
    "greeting": "Bonjour Mme Dupont,", "accroche": "Voici une sélection pour votre recherche maison · Firminy · 80 000 €.",
    "biens": biens,
    "signature": {"nom": "Frédéric Gerphagnon", "agence": "Groupe GTI", "tel": "04 77 00 00 00", "email": "accueil@gti-immobilier.fr"},
    "pixel_url": "https://x/r/o/tok.png", "unsubscribe_url": "https://x/r/u/tok",
}
html = build_email_html(ctx)
text = build_email_text(ctx)
size_kb = len(html.encode("utf-8")) / 1024
assert "❤" in html and "intéresse" in html and "✕ Pas pour moi" in html  # apostrophe HTML-échappée
assert "v:roundrect" in html and "prefers-color-scheme:dark" in html
assert "staticlbi.com" in html and "CPI 42022019" in html
assert "Se désinscrire" in html
assert "74 900 € FAI" in html and "Honoraires à la charge du vendeur" in html
assert "Réserver une visite" in html
assert "Ça m'intéresse :" in text and "Réserver une visite :" in text
print(f"3) HTML build OK — taille {size_kb:.1f} Ko (limite 100), version texte {len(text)} car.")
assert size_kb < 100, "email trop lourd"
print("\nTOUS LES TESTS PASSENT ✅")
