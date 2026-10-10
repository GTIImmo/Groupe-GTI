# -*- coding: utf-8 -*-
"""LE TRI DU CARNET DES LIENS — 10/10/2026.   DÉJÀ EXÉCUTÉ, accord de Frédéric.

POURQUOI CE SCRIPT A EXISTÉ
═══════════════════════════
Dans la nuit du 09 au 10/10, le garde-fou de sortie de C.9-f s'est déclenché
(6 308 identifiants menacés, seuil 1 000) et **son repli était cassé** :
`load_relations(substituer=False)` met `_CLES_FIGEES = {}`, mais le test de la
l. 1166 était `_CLES_FIGEES is not None` — **qu'un dict vide passe**. Le repli a
donc écrit NOTRE numéro au lieu de celui de Hektor, c'est-à-dire **exactement la
bascule qu'il devait empêcher**, sur tout le parc : 167 483 badges refaits en une
nuit (la mesure du 25/09 en redoutait 167 487).

AUCUNE DONNÉE PERDUE — 34 liens d'écart sur 167 703. Mais le carnet s'est retrouvé
avec **DEUX badges par ancre**, et `charger_cles_figees()` ne reprend RIEN pour une
ancre ambiguë :

    liens que le carnet protégeait encore     6 456 sur 167 660   =  3,9 %

⚠ LA CAUSE RACINE EST STRUCTURELLE, et elle reste ouverte : `app_relation_registry`
  a pour clé primaire `relation_key` — **le badge lui-même**. Un nouveau badge est
  donc forcément une NOUVELLE LIGNE : ce carnet est construit pour doubler. Le
  carnet des recherches, lui, a pour clé `app_search_id` (un numéro FRAPPÉ) et
  garde sa clé calculée dans une simple COLONNE : il ne peut pas doubler.
  ➡ C'est le point ⑥.1 du chantier « le registre des relations devient autonome » :
    « un numéro de lien FRAPPÉ par une séquence, jamais calculé ». NON FAIT.

CE QUE CE SCRIPT A FAIT
═══════════════════════
Le patron du projet, appliqué cinq fois avant (app_search_registry_avant_c2b,
app_contact_avant_reparation_20260924, app_affaire_ledger_avant_identite_20260820,
app_contact_search_current__sb_avant_reprise_20260917, app_securite_droits_avant_20261008) :
**on sauvegarde dans une table datée, puis on nettoie.** Ni « marquer » (qui aurait
demandé une colonne ET une condition dans le lecteur, à retenir pour toujours), ni
« garder » (qui laissait le filet débranché).

    1. app_relation_registry_avant_tri_20261010  <-  LE CARNET ENTIER, 335 249 lignes
    2. suppression des badges REMPLACÉS : barré ET une autre ligne VIVANTE porte la
       MÊME ancre (contact, notre n° de bien, rôle, source, type et n° de transaction)
    3. trois contrôles, et ROLLBACK si l'un échoue — rien n'est écrit à moitié

LES BADGES SORTIS, PAR RÔLE — les acquéreurs étaient les plus touchés après les
propriétaires, ce que la première lecture (« des bascules mandant ») masquait :

    proprietaire          126 084
    acquereur_compromis    13 259
    acquereur_offre        11 139
    acquereur_vente        10 507      -> 34 905 badges d'ACQUEREURS
    mandant                   215

CE QUI EST RESTÉ DANS LE CARNET, et c'est voulu : les 6 376 lignes barrées dont
aucune ligne vivante ne partage l'ancre — 6 284 rôles basculés (le lien vit sous un
autre rôle ; s'il rebascule, il doit retrouver SON badge) et 92 vraies disparitions.
Elles ne créent aucune ambiguïté : c'est précisément pour elles que la règle « le
carnet n'efface jamais » a été écrite.

LE RÉSULTAT, MESURÉ SUR LA VRAIE BASE
═════════════════════════════════════
    AVANT   ancres 174 036 | ambigues 161 204 | vivants 167 660 | PROTEGES   6 456 ( 3,9 %)
    APRES   ancres 174 036 | ambigues       0 | vivants 167 660 | PROTEGES 167 660 (100,0 %)

    sauvegarde 335 249 · supprimées 161 204 · reste 174 045
    aucun badge vivant supprimé · tout le supprimé est retrouvable · le compte boucle

ET L'ÉPREUVE QUI COMPTE — la VRAIE fonction du build, pas une imitation :

    charger_cles_figees()  ->  {'statut': 'ok', 'notes': 174036, 'ancres': 174036,
                                'ambigues': 0}
    ancres qui FIGENT un numéro  174 036   ·   ancres qui ne figent RIEN  0
    garde-fou d'entrée : 174 036 ancres pour 167 669 liens écrits -> il substituera

AUCUN CHANGEMENT DE CODE. Le build relit le carnet exactement comme avant ; il y
trouve désormais UNE réponse au lieu de deux.

RETOUR ARRIÈRE
══════════════
    DELETE FROM app_relation_registry;
    INSERT INTO app_relation_registry
        SELECT * FROM app_relation_registry_avant_tri_20261010;

REJOUER : refusé si la table de sauvegarde existe déjà (sortie 2).
⚠ JAMAIS pendant le run (05:00–07:18), la sauvegarde (08:00), la descente (08:15)
  ni le rattrapage documents (21:00) : le verrou d'écriture s'est déjà bloqué 8 min 30.
"""
from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
BASE = RACINE / "phase2" / "phase2.sqlite"
SAUV = "app_relation_registry_avant_tri_20261010"

ANCRE_SQL = (
    "SELECT contact_id, app_dossier_id, role, source,"
    " json_extract(recette_json,'$.transaction_type'),"
    " json_extract(recette_json,'$.transaction_id'),"
    " json_extract(recette_json,'$.annonce_id'), absent_depuis, relation_key"
    " FROM app_relation_registry WHERE app_dossier_id IS NOT NULL"
)


def lire_ancres(con: sqlite3.Connection) -> dict:
    """L'ancre telle que `charger_cles_figees` la fabrique : tout SAUF le n° de bien."""
    anc: dict = defaultdict(lambda: {"vals": set(), "viv": 0, "barr": []})
    for c, d, role, src, tt, ti, val, absd, cle in con.execute(ANCRE_SQL):
        k = (str(c), str(d), str(role or ""), str(src or ""), str(tt or ""), str(ti or ""))
        e = anc[k]
        e["vals"].add(str(val))
        if absd is None:
            e["viv"] += 1
        else:
            e["barr"].append(cle)
    return anc


def etat(anc: dict) -> tuple[int, int, int, int]:
    amb = sum(1 for e in anc.values() if len(e["vals"]) > 1)
    viv = sum(e["viv"] for e in anc.values())
    prot = sum(e["viv"] for e in anc.values() if len(e["vals"]) <= 1)
    return len(anc), amb, viv, prot


def main() -> int:
    con = sqlite3.connect(str(BASE), timeout=120)
    con.execute("PRAGMA busy_timeout=120000")   # obligatoire : plusieurs ecrivains

    anc = lire_ancres(con)
    remplacees = [cle for e in anc.values() if e["barr"] and e["viv"] for cle in e["barr"]]
    total_avant = con.execute("SELECT COUNT(*) FROM app_relation_registry").fetchone()[0]
    n_anc, amb, viv, prot = etat(anc)
    print("AVANT  carnet %d | ancres %d | ambigues %d | vivants %d | proteges %d (%.1f %%)"
          % (total_avant, n_anc, amb, viv, prot, 100.0 * prot / max(viv, 1)))
    print("       badges remplaces a sortir : %d" % len(remplacees))

    if con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                   (SAUV,)).fetchone()[0]:
        print("ARRET : la sauvegarde %s existe deja. Rien n'est ecrit." % SAUV)
        return 2
    if not remplacees:
        print("RIEN A FAIRE : aucun badge remplace. Rien n'est ecrit.")
        return 0

    con.execute("BEGIN IMMEDIATE")
    try:
        if con.execute("SELECT COUNT(*) FROM app_relation_registry").fetchone()[0] != total_avant:
            raise RuntimeError("le carnet a change entre la mesure et le geste")
        con.execute("CREATE TABLE %s AS SELECT * FROM app_relation_registry" % SAUV)
        n_sauv = con.execute("SELECT COUNT(*) FROM %s" % SAUV).fetchone()[0]
        if n_sauv != total_avant:
            raise RuntimeError("sauvegarde incomplete : %d sur %d" % (n_sauv, total_avant))

        con.execute("CREATE TEMP TABLE a_sortir (relation_key TEXT PRIMARY KEY)")
        con.executemany("INSERT OR IGNORE INTO a_sortir VALUES (?)", [(r,) for r in remplacees])
        n_cible = con.execute("SELECT COUNT(*) FROM a_sortir").fetchone()[0]
        supp = con.execute("DELETE FROM app_relation_registry WHERE relation_key IN"
                           " (SELECT relation_key FROM a_sortir)").rowcount
        reste = con.execute("SELECT COUNT(*) FROM app_relation_registry").fetchone()[0]

        c1 = con.execute("SELECT COUNT(*) FROM %s s WHERE s.absent_depuis IS NULL AND"
                         " s.relation_key NOT IN (SELECT relation_key FROM"
                         " app_relation_registry)" % SAUV).fetchone()[0] == 0
        c2 = con.execute("SELECT COUNT(*) FROM a_sortir x WHERE x.relation_key NOT IN"
                         " (SELECT relation_key FROM %s)" % SAUV).fetchone()[0] == 0
        c3 = (n_sauv == reste + supp) and (supp == n_cible)
        print("GESTE  sauvegarde %d | supprimees %d | reste %d" % (n_sauv, supp, reste))
        print("       aucun vivant supprime %s | tout retrouvable %s | compte boucle %s"
              % (c1, c2, c3))
        if not (c1 and c2 and c3):
            raise RuntimeError("un controle a echoue")
        con.execute("COMMIT")
    except Exception as exc:                                            # noqa: BLE001
        con.execute("ROLLBACK")
        print("ANNULE (ROLLBACK) : %s -- la base est intacte." % exc)
        return 3

    n_anc, amb, viv, prot = etat(lire_ancres(con))
    print("APRES  ancres %d | ambigues %d | vivants %d | proteges %d (%.1f %%)"
          % (n_anc, amb, viv, prot, 100.0 * prot / max(viv, 1)))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
