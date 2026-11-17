#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C2 -- LES COMMISSIONS DU CLASSEUR QUE NOUS N'AVONS PAS.            17/11/2026

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\c2_generer_commissions_2026-11-17.py

⛔ CE SCRIPT N'ECRIT RIEN EN BASE. Il MESURE et il GENERE trois fichiers SQL.

⭐⭐⭐ L'AUDIT QUE FREDERIC A DEMANDE LE 17/11 (« C2 avant audit pour savoir si il n'y
  avait quelque chose qui bloquait sinon oui tu as mon accord mais 303 montants me
  semble peu ? ») -- ET SON DOUTE ETAIT JUSTE, DANS L'AUTRE SENS :

```
   4 782 lignes du classeur portent une commission > 0   (34 280 276 EUR)
   NOUS AVONS DEJA                      4 363   91 %
   ⛔ TROU : rien chez nous               332   (le plan disait 303, au 31/10)
   aucune transaction reliee                87   (les trous du pont, A6)
```
  303 n'etait donc pas « peu » : c'etait LE TROU, pas le total. Hektor calcule deja
  91 % des commissions.

⛔⛔ ET LE BLOCAGE EXISTAIT BIEN -- le plan le nomme « LA CASE EXISTE, MAIS LE ROBINET
  EST FERME » : `CHAMPS_APP_AFFAIRE = ()` est VIDE, l'etape n'est pas au run, et
  « une valeur ecrite au carnet et non reposee serait INVISIBLE LE LENDEMAIN ».
  ⭐ MAIS IL NE CONCERNE QUE LE CARNET (`app_affaire_champ_app` -> `honoraires_entree`,
    de CLASSE C). Nous ecrivons dans `honoraires_entree_app`, de CLASSE A, creee le
    16/10 : elle est dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (l. 3108) ET dans la liste
    des colonnes du local (l. 620). Le commentaire du code le dit lui-meme a la
    l. 375 : « exactement le trou que honoraires_entree_app comble depuis le lot 1 ».
    ➡ La section du plan est ANTERIEURE a cette colonne : son avertissement est
      PERIME pour ce chemin.

⛔⛔⛔ LE VRAI BLOCAGE N'EST PAS TECHNIQUE, IL EST COMPTABLE. Sur les 332 trous :
```
   Annulée                270   81 %   <- commission PREVUE, JAMAIS PERCUE
   Compromis en attente    24
   Vente réglée            16
   Offre d'achat           11
   Vente prevue             7
   Vente fixée              4
```
  Une affaire annulee n'a JAMAIS genere de commission. Et la colonne dit « les
  honoraires VENDEUR saisis dans l'app » : y mettre 270 montants jamais encaisses
  fausserait tout calcul de chiffre d'affaires -- une erreur qui ne se voit qu'au
  moment ou quelqu'un additionne.
  ➡ FREDERIC, 17/11 : « Les 62 seules. » Les 270 annulees ne sont PAS posees.

⚠ RESERVE DECLAREE, et elle vient de SA PROPRE REGLE DU CHANTIER : parmi les 62,
  **42 sont des affaires EN COURS** (24 compromis en attente, 11 offres, 7 ventes
  prevues). Sa regle dit « on ne reprend que ce que Hektor ne rendra plus », et Hektor
  calculera leur commission a la vente. Les **20** autres (16 reglees, 4 fixees) sont
  de l'historique pur. Le patch SEPARE les deux lots pour qu'il puisse s'arreter aux 20.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "phase2" / "checks"))
sys.path.insert(0, str(RACINE / "monitoring"))

import apparier_classeur as ap                                      # noqa: E402
import check_gti_health as cgh                                      # noqa: E402

BASE = RACINE / "supabase" / "patch_c2_commissions_2026-11-17"
RAPPORT = RACINE / "notice" / "C2_LES_COMMISSIONS_A_POSER_2026-11-17.csv"
MARQUE = "classeur:C2:2026-11-17"
LOT_API = 60

#: Les etats qui disent que l'affaire est ABOUTIE -- donc de l'historique.
ABOUTIES = {"Vente réglée", "Vente reglee", "Vente fixée", "Vente fixee"}
#: Les etats qui disent qu'elle est MORTE -- commission PREVUE, jamais percue.
MORTES = {"Annulée", "Annulee"}


def client():
    for f in (RACINE / ".env", RACINE / "backend" / ".env",
              RACINE / "apps" / "hektor-v1" / ".env"):
        if f.exists():
            cgh.load_env_file(f)
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
    cle = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and cle):
        raise SystemExit("⛔ pas d'identifiants Supabase -- rien n'est genere.")
    return cgh.SupabaseClient(url, cle, timeout_seconds=30)


def tout_lire(cl, table, select, ordre):
    out, debut = [], 0
    while True:
        r = cl.get(table, {"select": select, "limit": "1000",
                           "offset": str(debut), "order": ordre}) or []
        out.extend(r)
        if len(r) < 1000:
            return out
        debut += 1000


def index_de(lettre: str) -> int:
    n = 0
    for c in lettre:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def num(v):
    s = re.sub(r"[^0-9,.\-]", "", str(v or "")).replace(",", ".")
    try:
        return float(s) if s else None
    except ValueError:
        return None


def porte_une_commission(t) -> bool:
    for c in ("honoraires_entree", "honoraires_entree_app", "commission_agence"):
        v = num(t.get(c))
        if v and v > 0:
            return True
    return False


#: ⭐ LA CIBLE : la transaction la PLUS AVANCEE de la chaine. `honoraires_entree_app`
#:   est decrite comme « les honoraires VENDEUR saisis dans l'app, DES L'OFFRE »,
#:   donc elle accepte les trois types. On vise la plus avancee pour que la valeur
#:   soit la ou l'affaire en est.
RANG = {"vente": 3, "compromis": 2, "offre": 1}


def main() -> int:
    ap.load_env_file(RACINE / ".env")
    print("=== C2 -- LES COMMISSIONS DU CLASSEUR (lecture seule) ===")
    print()

    entetes_bruts, lignes = ap.lire_classeur()
    entetes = [str(c or "").strip() for c in entetes_bruts]
    if len(lignes) < 3000:
        print("⛔ LECTURE RATEE : %d lignes. ON NE CONCLUT RIEN." % len(lignes))
        return 2
    i_p, i_r = index_de("P"), entetes.index("Etat Actuel")
    i_id = entetes.index("ID Unique")
    print("le Sheet : %d lignes . P = %r" % (len(lignes), entetes[i_p]))

    classeur = {}
    for _rang, l in lignes:
        p = num(str(l[i_p] if i_p < len(l) else ""))
        ident = str(l[i_id] if i_id < len(l) else "").strip()
        if p and p > 0 and ident:
            classeur[ident] = {"montant": p,
                               "etat": str(l[i_r] if i_r < len(l) else "").strip()}
    print("lignes avec une commission > 0 et un identifiant : %d" % len(classeur))

    #: ⛔ LE TEMOIN POSITIF : A1 et la mesure du 17/11 en comptent 4 782.
    if len(classeur) < 4000:
        print("⛔ TEMOIN POSITIF EN ECHEC : %d, attendu ~4 782. La colonne a bouge."
              % len(classeur))
        return 2

    cl = client()
    liens = tout_lire(cl, "app_classeur_lien", "id_unique,app_affaire_id", "ligne_classeur")
    par_id: dict[str, list[int]] = {}
    for r in liens:
        par_id.setdefault(str(r["id_unique"]).strip(), []).append(r["app_affaire_id"])
    besoin = sorted({a for i in classeur for a in par_id.get(i, [])})
    rows = []
    for i in range(0, len(besoin), LOT_API):
        lot = besoin[i:i + LOT_API]
        rows.extend(cl.get("app_affaire_ledger",
                           {"select": "app_affaire_id,kind,state,hektor_annonce_id,"
                                      "honoraires_entree,honoraires_entree_app,"
                                      "commission_agence",
                            "app_affaire_id": "in.(%s)" % ",".join(map(str, lot))}) or [])
    ledger = {str(r["app_affaire_id"]): r for r in rows}

    deja, sans_lien, mortes, vivantes, abouties = 0, 0, [], [], []
    for ident, v in sorted(classeur.items()):
        trs = [ledger[str(a)] for a in par_id.get(ident, []) if str(a) in ledger]
        if not trs:
            sans_lien += 1
            continue
        if any(porte_une_commission(t) for t in trs):
            deja += 1
            continue
        cible = max(trs, key=lambda t: RANG.get(str(t.get("kind")), 0))
        ligne = {"id_unique": ident, "montant": v["montant"], "etat": v["etat"],
                 "app_affaire_id": cible["app_affaire_id"],
                 "annonce": cible.get("hektor_annonce_id"), "type": cible.get("kind")}
        if v["etat"] in MORTES:
            mortes.append(ligne)
        elif v["etat"] in ABOUTIES:
            abouties.append(ligne)
        else:
            vivantes.append(ligne)

    print()
    print("=== LE TRI ===")
    print("·  NOUS AVONS DEJA une commission       : %5d" % deja)
    print("⛔ aucune transaction reliee            : %5d  (les trous du pont, A6)" % sans_lien)
    print("⛔ affaire ANNULEE -- PREVUE, non percue: %5d  ⬜ SA DECISION : NON POSEES" % len(mortes))
    print("✅ affaire ABOUTIE -- historique pur    : %5d  -> LOT 1" % len(abouties))
    print("⚠  affaire EN COURS                     : %5d  -> LOT 2, sa regle les ecarte" % len(vivantes))
    total = deja + sans_lien + len(mortes) + len(abouties) + len(vivantes)
    print()
    print("partition : %d = %d" % (total, len(classeur)))
    if total != len(classeur):
        print("⛔ LA PARTITION NE BOUCLE PAS -- ne rien poser.")
        return 2

    for nom, lot in (("LOT 1 -- ABOUTIES", abouties), ("LOT 2 -- EN COURS", vivantes)):
        if not lot:
            continue
        print()
        print("=== %s : %d lignes, %s EUR ===" % (nom, len(lot),
              format(round(sum(x["montant"] for x in lot)), ",").replace(",", " ")))
        for k, n in Counter(x["etat"] for x in lot).most_common():
            print("      %-26s %4d" % (k[:26], n))
        print("      par type de transaction visee : %s"
              % dict(Counter(x["type"] for x in lot)))

    with RAPPORT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";", fieldnames=[
            "lot", "id_unique", "montant", "etat", "app_affaire_id", "annonce", "type"])
        w.writeheader()
        for nom, lot in (("1_aboutie", abouties), ("2_en_cours", vivantes),
                         ("non_posee_annulee", mortes)):
            for x in lot:
                w.writerow({"lot": nom, **x})
    print()
    print("ecrit : %s" % RAPPORT)

    # ─── LE PATCH ────────────────────────────────────────────────────────────
    def valeurs(lot):
        return ",\n    ".join("(%d, '%s')" % (x["app_affaire_id"],
                                              ("%.2f" % x["montant"]).rstrip("0").rstrip("."))
                              for x in lot)

    def ids(lot):
        return ", ".join(str(x["app_affaire_id"]) for x in lot)

    n1, n2 = len(abouties), len(vivantes)
    s1 = format(round(sum(x["montant"] for x in abouties)), ",").replace(",", " ")
    s2 = format(round(sum(x["montant"] for x in vivantes)), ",").replace(",", " ")
    tous = abouties + vivantes

    patch = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C2 -- LES COMMISSIONS DU CLASSEUR QUE NOUS N'AVONS PAS
-- Genere le {date.today().isoformat()} par phase2/checks/c2_generer_commissions_2026-11-17.py
--
-- FREDERIC, 17/11 : « Les 62 seules. » -> {n1 + n2} lignes posees, les {len(mortes)}
-- affaires ANNULEES ne sont PAS posees.
--
-- ⛔⛔ POURQUOI LES ANNULEES SONT ECARTEES, ET C'EST COMPTABLE, PAS TECHNIQUE :
--   une affaire annulee n'a JAMAIS genere de commission. Le montant du classeur
--   etait PREVU, pas perçu. Et `honoraires_entree_app` dit « les honoraires VENDEUR
--   saisis dans l'app » : y mettre {len(mortes)} montants jamais encaisses fausserait
--   tout calcul de chiffre d'affaires -- une erreur qui ne se voit qu'au moment ou
--   quelqu'un additionne. Il n'existe aucune colonne pour « commission prevue non
--   perçue » : la creer serait une decision a part.
--
-- ⭐ LE BLOCAGE DU PLAN EST PERIME POUR CE CHEMIN. Le plan dit « LA CASE EXISTE,
--   MAIS LE ROBINET EST FERME » (`CHAMPS_APP_AFFAIRE = ()`, etape absente du run,
--   « une valeur ecrite au carnet et non reposee serait INVISIBLE LE LENDEMAIN »).
--   Mais ca ne concerne QUE le carnet, qui ecrit `honoraires_entree`, de CLASSE C.
--   Nous ecrivons `honoraires_entree_app`, de CLASSE A : dans
--   COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (affaire_ledger.py l. 3108) ET dans la liste
--   des colonnes du local (l. 620). Le code le dit lui-meme l. 375 : « exactement le
--   trou que honoraires_entree_app comble depuis le lot 1 ».
--
-- ⚠⚠ RESERVE DECLAREE, ET ELLE VIENT DE SA PROPRE REGLE DU CHANTIER :
--   LOT 1  {n1} affaires ABOUTIES ({s1} EUR) -- historique pur, aucune reserve
--   LOT 2  {n2} affaires EN COURS ({s2} EUR) -- sa regle dit « on ne reprend que ce
--          que Hektor ne rendra plus », et Hektor calculera leur commission A LA
--          VENTE. ➡ POUR S'ARRETER AUX {n1} : ne jouer que le bloc 3a, et sauter 3b.
--
-- LA CIBLE : la transaction la PLUS AVANCEE de la chaine (vente > compromis > offre),
--   parce que la colonne accepte les trois « des l'offre » et qu'on pose la valeur la
--   ou l'affaire en est.
--
-- Retour arriere : patch_c2_commissions_2026-11-17_INVERSE.sql
-- Controle       : patch_c2_commissions_2026-11-17_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════

begin;

-- ─── 1. L'ETAT D'AVANT, EXIGE ──────────────────────────────────────────────
do $$
declare deja integer; cibles integer;
begin
  select count(*) into deja from public.app_affaire_ledger
   where app_affaire_id in ({ids(tous)}) and honoraires_entree_app is not null;
  if deja <> 0 then
    raise exception '⛔ ARRET : % cible(s) portent deja une valeur.', deja;
  end if;
  select count(*) into cibles from public.app_affaire_ledger
   where app_affaire_id in ({ids(tous)});
  if cibles <> {n1 + n2} then
    raise exception '⛔ ARRET : % cibles sur les {n1 + n2} attendues.', cibles;
  end if;
  raise notice '✅ etat d''avant : 0 valeur posee, {n1 + n2} cibles retrouvees.';
end $$;

-- ─── 2. LA SAUVEGARDE, ET ELLE NAIT FERMEE (la lecon du 16/11) ─────────────
create table if not exists public.app_affaire_avant_c2_20261117 as
  select app_affaire_id, kind, hektor_annonce_id, honoraires_entree,
         honoraires_entree_app, commission_agence, now() as photographie_le
    from public.app_affaire_ledger
   where app_affaire_id in ({ids(tous)});
revoke all on public.app_affaire_avant_c2_20261117 from authenticated, anon;

-- ─── 3a. LOT 1 : LES {n1} AFFAIRES ABOUTIES ({s1} EUR) ─────────────────────
with poser(app_affaire_id, montant) as (values
    {valeurs(abouties)}
)
update public.app_affaire_ledger l
   set honoraires_entree_app = p.montant
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.honoraires_entree_app is null;

-- ─── 3b. LOT 2 : LES {n2} AFFAIRES EN COURS ({s2} EUR) ─────────────────────
-- ⚠ SA REGLE DU CHANTIER LES ECARTERAIT. Pour s'arreter au lot 1, NE PAS jouer
--   ce bloc -- et ajuster les comptes du controle 4 en consequence.
with poser(app_affaire_id, montant) as (values
    {valeurs(vivantes)}
)
update public.app_affaire_ledger l
   set honoraires_entree_app = p.montant
  from poser p
 where l.app_affaire_id = p.app_affaire_id
   and l.honoraires_entree_app is null;

-- ─── 4. LES CONTROLES, ET ILS ARRETENT ─────────────────────────────────────
do $$
declare
  posees   integer;
  ailleurs integer;
  mauvais  integer;
  ferme    integer;
begin
  select count(*) into posees from public.app_affaire_ledger
   where app_affaire_id in ({ids(tous)}) and honoraires_entree_app is not null;
  if posees <> {n1 + n2} then
    raise exception '⛔ {n1 + n2} attendues, % posees.', posees;
  end if;

  -- ⭐ TEMOIN INVERSE : aucune AUTRE ligne n'a recu de valeur. On compte les lignes
  --   hors du lot : il y en avait 4 au 17/11 (des saisies de l'app), pas 0.
  select count(*) into ailleurs from public.app_affaire_ledger
   where honoraires_entree_app is not null
     and app_affaire_id not in ({ids(tous)});
  if ailleurs <> 4 then
    raise exception '⛔ % ligne(s) hors du lot portent une valeur, 4 attendues '
      '(les saisies de l''app). Le patch a debordé, ou une saisie est arrivee.', ailleurs;
  end if;

  -- ⭐ AUCUN MONTANT ABSURDE : ni zero, ni negatif, ni non-numerique
  select count(*) into mauvais from public.app_affaire_ledger
   where honoraires_entree_app is not null
     and (honoraires_entree_app !~ '^[0-9]+(\\.[0-9]+)?$'
          or honoraires_entree_app::numeric <= 0);
  if mauvais <> 0 then
    raise exception '⛔ % montant(s) absurde(s) (zero, negatif ou illisible).', mauvais;
  end if;

  select count(*) into ferme from information_schema.role_table_grants
   where table_schema='public' and table_name='app_affaire_avant_c2_20261117'
     and grantee in ('authenticated','anon');
  if ferme <> 0 then
    raise exception '⛔ la sauvegarde porte encore % droit(s).', ferme;
  end if;

  raise notice '✅ {n1 + n2} commissions posees ({n1} abouties + {n2} en cours) . '
    '4 saisies de l''app intactes . 0 montant absurde . sauvegarde FERMEE.';
end $$;

commit;
"""

    inverse = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C2 -- RETOUR ARRIERE
-- ⭐ Il ne vide que les {n1 + n2} cibles de ce lot, et REFUSE de se jouer si une
--   valeur a change depuis la pose.
-- ⚠ Il NE TOUCHE PAS aux 4 saisies de l'app qui existaient avant le 17/11.
-- ═══════════════════════════════════════════════════════════════════════════

begin;

do $$
declare changees integer;
begin
  with attendu(app_affaire_id, montant) as (values
      {valeurs(tous)}
  )
  select count(*) into changees
    from attendu a join public.app_affaire_ledger l using (app_affaire_id)
   where coalesce(l.honoraires_entree_app, '') <> a.montant;
  if changees <> 0 then
    raise exception '⛔ ARRET : % ligne(s) ne portent plus la valeur de C2.', changees;
  end if;
  raise notice '✅ les {n1 + n2} cibles portent bien les valeurs de C2.';
end $$;

update public.app_affaire_ledger
   set honoraires_entree_app = null
 where app_affaire_id in ({ids(tous)});

do $$
declare reste integer; autres integer;
begin
  select count(*) into reste from public.app_affaire_ledger
   where app_affaire_id in ({ids(tous)}) and honoraires_entree_app is not null;
  if reste <> 0 then
    raise exception '⛔ il reste % ligne(s) du lot.', reste;
  end if;
  select count(*) into autres from public.app_affaire_ledger
   where honoraires_entree_app is not null;
  if autres <> 4 then
    raise exception '⛔⛔ % saisies de l''app au lieu de 4 : le retour arriere a '
      'deborde sur des saisies humaines. GRAVE.', autres;
  end if;
  raise notice '✅ {n1 + n2} retirees . LES 4 SAISIES DE L''APP SONT INTACTES.';
end $$;

commit;
"""

    repetition = f"""-- ═══════════════════════════════════════════════════════════════════════════
-- C2 -- LES CONTROLES, REJOUABLES. Aucune ecriture.
-- ═══════════════════════════════════════════════════════════════════════════

select 'commissions posees par C2' as controle, count(*)::text as mesure,
       '{n1 + n2}' as attendu
  from public.app_affaire_ledger
 where app_affaire_id in ({ids(tous)}) and honoraires_entree_app is not null
union all
select 'les 4 saisies de l app, INTACTES', count(*)::text, '4'
  from public.app_affaire_ledger
 where honoraires_entree_app is not null and app_affaire_id not in ({ids(tous)})
union all
select 'aucun montant zero, negatif ou illisible', count(*)::text, '0'
  from public.app_affaire_ledger
 where honoraires_entree_app is not null
   and (honoraires_entree_app !~ '^[0-9]+(\\.[0-9]+)?$'
        or honoraires_entree_app::numeric <= 0)
union all
select 'la somme posee', to_char(sum(honoraires_entree_app::numeric), 'FM999G999G999'),
       '{s1} + {s2} EUR'
  from public.app_affaire_ledger
 where app_affaire_id in ({ids(tous)}) and honoraires_entree_app is not null
union all
-- ⭐⭐ LE CONTROLE QUI COMPTE VRAIMENT : les {len(mortes)} cibles des affaires ANNULEES
--   doivent rester VIDES. C'est la decision de Frederic du 17/11, et c'est la seule
--   chose que ce patch pourrait abimer sans qu'on le voie.
-- ⛔ Ma premiere version de ce controle portait « and false » : il rendait 0 PAR
--   CONSTRUCTION et ne verifiait RIEN. Un controle vide est pire qu'aucun controle.
select 'les {len(mortes)} annulees sont restees VIDES', count(*)::text,
       '0 -- decision du 17/11'
  from public.app_affaire_ledger
 where honoraires_entree_app is not null
   and app_affaire_id in ({ids(mortes)})
union all
select 'la sauvegarde est FERMEE', count(*)::text, '0'
  from information_schema.role_table_grants
 where table_schema='public' and table_name='app_affaire_avant_c2_20261117'
   and grantee in ('authenticated','anon')
union all
select 'VOISINES -- les 450 dates de C3', count(*)::text, '450'
  from public.app_affaire_ledger where date_annulation_app is not null
union all
select 'VOISINES -- vente_reglee_app', count(*)::text, '3729'
  from public.app_affaire_ledger where vente_reglee_app is not null
order by 1;
"""

    for suffixe, contenu in ((".sql", patch), ("_INVERSE.sql", inverse),
                             ("_REPETITION.sql", repetition)):
        f = Path(str(BASE) + suffixe)
        f.write_bytes(contenu.encode("utf-8"))
        print("ecrit : %-56s %7d octets" % (f.name, len(f.read_bytes())))

    print()
    print("⛔ RIEN N'A ETE JOUE. Ces trois fichiers attendent un « colle ».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
