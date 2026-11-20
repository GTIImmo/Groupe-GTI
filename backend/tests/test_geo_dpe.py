"""La route du DPE ADEME (/geo/dpe) -- correctif du 20/11/2026 (§98.2) : la bonne clé d'adresse.

Lancer depuis backend/ :  <python> tests/test_geo_dpe.py     (sans réseau : le RNB et l'ADEME sont simulés)
Le défaut : le RNB rend pour chaque adresse `id` = « 42095_2120_00013 » (la forme de l'ADEME) ET `ban_id` d'une autre
forme ; la route lisait `ban_id` d'abord -> 0 DPE à l'adresse -> « proximité » toujours. Vérifie l'ordre : l'adresse
exacte (donnée ou 1re du bâtiment) -> « adresse » ; les autres numéros du bâtiment -> « batiment » ; sinon « proximite » ;
l'ancienne forme du RNB (`ban_id` seul, à la bonne forme) marche encore ; un identifiant mal formé n'est jamais envoyé.
Témoin inverse : l'ANCIEN code (git HEAD~ de cette ligne) rate le cas de la forme actuelle du RNB.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routers import geo  # noqa: E402

ok = 0


def voir(vrai, libelle):
    global ok
    assert vrai, libelle
    ok += 1
    print("  VERT  " + libelle)


ADEME = {  # identifiant_ban -> les DPE publiés à cette adresse
    "42095_2120_00013": [{"identifiant_ban": "42095_2120_00013", "surface_habitable_logement": 87, "etiquette_dpe": "E",
                          "date_etablissement_dpe": "2023-12-07", "conso_5_usages_par_m2_ep": 240.8},
                         {"identifiant_ban": "42095_2120_00013", "surface_habitable_logement": 55, "etiquette_dpe": "D",
                          "date_etablissement_dpe": "2023-12-07", "conso_5_usages_par_m2_ep": 195.7}],
    "38185_4820_00026": [{"identifiant_ban": "38185_4820_00026", "surface_habitable_logement": 40, "etiquette_dpe": "C"}],
}
VOISIN = [{"identifiant_ban": "42095_2120_00011", "surface_habitable_logement": 70, "etiquette_dpe": "D",
           "date_etablissement_dpe": "2026-11-06"}]
demandes = []


def faux_lignes(params):
    demandes.append(params)
    if "qs" in params:
        return list(ADEME.get(params["qs"].split('"')[1], []))
    return list(VOISIN)  # le repli de proximité


batiment = {"valeur": None}
geo._rnb_closest = lambda lat, lon, radius=40: batiment["valeur"]
geo._dpe_lines = faux_lignes
geo.get_authenticated_user = lambda settings, authorization: None


def appel(**kw):
    demandes.clear()
    return geo.dpe(lat=45.3875, lon=4.2826, surface=kw.get("surface"), ban=kw.get("ban"), authorization="Bearer j", settings=None)


def adr(id_=None, ban_id=None):
    return {k: v for k, v in (("id", id_), ("ban_id", ban_id)) if v is not None}


print("1) la forme ACTUELLE du RNB (id = clé BAN, ban_id = autre forme)")
batiment["valeur"] = {"addresses": [adr("42095_2120_00013", "0e9ec990-ce5e-46db-8fee-139d20c06b9e")]}
r = appel()
voir(r["matched_by"] == "adresse" and r["nb_adresse"] == 2 and demandes[0]["qs"] == 'identifiant_ban:"42095_2120_00013"',
     "le DPE est trouvé À L'ADRESSE (c'était « proximité » avant le correctif)")
voir(not any("0e9ec990" in str(d) for d in demandes), "l'identifiant d'une autre forme n'est jamais envoyé à l'ADEME")
r = appel(surface=87)
voir(r["surface"] == 87 and r["etiquette_dpe"] == "E", "la surface départage toujours les DPE de l'immeuble (87 m² -> le bon)")

print("2) l'ANCIENNE forme du RNB (ban_id à la bonne forme, pas d'id) marche encore")
batiment["valeur"] = {"addresses": [adr(None, "42095_2120_00013")]}
voir(appel()["matched_by"] == "adresse", "ban_id seul, à la forme BAN : trouvé à l'adresse")

print("3) l'adresse EXACTE donnée (le géocodage du parcours) passe avant le bâtiment")
batiment["valeur"] = {"addresses": [adr("38185_4820_00032", "bece9a20-33a6-4b9b-93a6-128bfd11bc79")]}
r = appel(ban="38185_4820_00026")
voir(r["matched_by"] == "adresse" and demandes[0]["qs"] == 'identifiant_ban:"38185_4820_00026"',
     "l'adresse tapée (n° 26) est cherchée d'abord, pas le 1er numéro du bâtiment (n° 32)")
r = appel(ban="pas une clé")
voir(r["matched_by"] == "proximite" and not any("pas une" in str(d) for d in demandes),
     "un identifiant mal formé n'est pas envoyé : on retombe sur le bâtiment, puis la proximité")

print("4) un AUTRE numéro du même bâtiment -> « batiment », pas « adresse »")
batiment["valeur"] = {"addresses": [adr("42095_2120_00015", "x"), adr("42095_2120_00013", "y")]}
r = appel()
voir(r["matched_by"] == "batiment" and r["nb_adresse"] == 2, "trouvé au n° 13 du même immeuble : « batiment » (l'écran dit « à vérifier »)")
r = appel(ban="42095_2120_00015")
voir(r["matched_by"] == "batiment" and [d.get("qs") for d in demandes][:2] == ['identifiant_ban:"42095_2120_00015"', 'identifiant_ban:"42095_2120_00013"'],
     "l'adresse exacte d'abord (rien), puis les autres numéros, sans redemander la même")
batiment["valeur"] = {"addresses": [adr(f"42095_2120_000{n:02d}", "x") for n in range(20, 40)]}
appel()
voir(sum(1 for d in demandes if "qs" in d) == 6, "un grand bâtiment : l'adresse + 5 autres numéros au plus, puis la proximité")

print("5) rien à l'adresse ni au bâtiment -> la proximité, comme avant")
batiment["valeur"] = None
r = appel()
voir(r["matched_by"] == "proximite" and r["nb_adresse"] is None and r["found"], "pas de bâtiment : le DPE le plus proche, « à vérifier »")

print("6) témoin inverse : l'ANCIEN code rate la forme actuelle du RNB")
import subprocess  # noqa: E402
import types  # noqa: E402

ancien_src = subprocess.run(["git", "show", "f515ba9:backend/app/routers/geo.py"], capture_output=True, text=True,
                            encoding="utf-8", cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))).stdout
ancien = types.ModuleType("app.routers.geo_ancien")
ancien.__package__ = "app.routers"
exec(compile(ancien_src, "geo_ancien", "exec"), ancien.__dict__)
ancien._rnb_closest = lambda lat, lon, radius=40: {"addresses": [adr("42095_2120_00013", "0e9ec990-ce5e-46db-8fee-139d20c06b9e")]}
ancien._dpe_lines = faux_lignes
ancien.get_authenticated_user = lambda settings, authorization: None
r = ancien.dpe(lat=45.3875, lon=4.2826, surface=None, authorization="Bearer j", settings=None)
voir(r["matched_by"] == "proximite", "l'ancien code : « proximité » sur la même adresse -- le correctif mord")

print(f"\nTOUT EST VERT ({ok} contrôles)")
