#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C5 / LOT B -- LES 98 OFFRES « ANNULEE » DU CLASSEUR.            16/11/2026

    python -X utf8 phase2/checks/poser_offres_annulees_classeur_2026-11-16.py

⛔ CE SCRIPT N'ECRIT RIEN. Il MESURE et il GENERE le SQL -- c'est le patch qui
  ecrit. Patron du projet : poser_charge_classeur_2026-11-04.py.

═══════════════════════════════════════════════════════════════════════════════
POURQUOI CES 98, ET PAS LES 242
═══════════════════════════════════════════════════════════════════════════════
Decision de Frederic du 16/11, apres mesure. Creer une transaction exige de lui
donner un ETAT, et l'etat decide si LES 4 REGLES DE CHAINAGE se declenchent
(en service depuis le 10/11) :

    offre     « Annulee »             104  -> state 'refused'  : AUCUNE regle ne joue
    offre     « Vente reglee »         69  -> 'accepted'       : declenche [B]
    compromis « Annulee »              38  -> 'cancelled'      : declenche [A]
    compromis « Compromis en attente » 24
    les 7 autres                        7

⭐ C'est l'essai A2 du 15/11 qui l'a appris : il avait choisi 'refused' EXPRES,
  « une offre REFUSEE ne declenche aucune des 4 regles de chainage (une offre
  ACCEPTEE orpheline, elle, en declenche) ». Ces 98 reproduisent donc EXACTEMENT
  un cas deja eprouve en reel sur une nuit complete.

⭐ LA GARDE DU PROJET EST APPLIQUEE : « 1re passe : confiance "sure" SEULEMENT »
  -> 104 moins 6 (« bonne » / « a valider ») = 98. Et 0 chainage douteux.

═══════════════════════════════════════════════════════════════════════════════
L'ACQUEREUR VA EN NOTE -- L'IDEE DE FREDERIC, ET ELLE EST SURE
═══════════════════════════════════════════════════════════════════════════════
Le classeur donne un acquereur pour les 242, mais sous forme de NOM, pas
d'identifiant de contact. Le poser dans `acquereurs_json` aurait deux effets :

    le declencheur app_affaire_partie_suivre CREERAIT des parties
      (il ne lit QUE acquereurs_json, mandants_json et le notaire -- mesure du 16/11)
    et la regle [D] du chainage, qui croise LES NOMS d'acquereurs, pourrait
      REUNIR DES DOSSIERS -- un geste structurel, sur 98 lignes, sans qu'un
      humain l'ait decide

⭐ Sa proposition : « on peut peut-etre le noter ailleurs, une note ». Et SON PLAN
  LE PREVOYAIT DEJA (C4 : « G -> app_affaire_note, origine classeur »).
  ⭐ app_affaire_note n'est mentionnee NULLE PART dans phase2/sync ni dans
    run_full_pipeline.ps1 : la nuit ne la touche pas, la note survit.

═══════════════════════════════════════════════════════════════════════════════
CE QUE CHAQUE LIGNE PORTE, ET D'OU CA VIENT
═══════════════════════════════════════════════════════════════════════════════
    app_affaire_id      nextval('app_affaire_id_app_seq')  <- SUPABASE FRAPPE LE
                        NUMERO. « Le sens n'est pas negociable : Supabase d'abord,
                        la machine ensuite » (affaire_ledger.py:2772).
    kind / state        'offre' / 'refused'
    date                la date « Offre Achat » du classeur (colonne TEXT)
    hektor_affaire_id   NULL        present_in_hektor  false
    transaction_origine 'classeur'  ⛔ DANS LE MEME INSERT, jamais apres : la
                        fenetre entre les deux serait un faux positif (piece 1)
    chaine / dossier    pris sur la transaction DEJA reliee par le gel a cette
                        meme ligne du classeur -- on ne devine aucun rattachement
    acquereurs_json     ⛔ RIEN. mandants_json ⛔ RIEN.
    payload_json        le marqueur, l'ID Unique, et de quoi defaire

LECTURE SEULE : un CSV + des GET chez Supabase. Trois fichiers ecrits dans
supabase/ : le patch, son INVERSE, sa REPETITION.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "monitoring"))
import check_gti_health as cgh                                      # noqa: E402

RAPPORT = RACINE / "notice" / "A4_RAPPORT_GEL_TOUS_LES_CHAMPS_2026-11-16.csv"
SORTIE = RACINE / "supabase"
BASE = "patch_offres_annulees_classeur_2026-11-16"
MARQUE = "classeur"
LOT_API = 60


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


def par_lots(cl, table, select, colonne, valeurs, citer=False):
    """Un `in.(...)` par paquets, pour ne pas fabriquer une URL demesuree."""
    out = []
    valeurs = sorted(set(valeurs))
    for i in range(0, len(valeurs), LOT_API):
        lot = valeurs[i:i + LOT_API]
        rendu = ",".join(('"%s"' % v) if citer else str(v) for v in lot)
        r = cl.get(table, {"select": select, colonne: "in.(%s)" % rendu})
        out.extend(r or [])
    return out


def txt(v):
    """Une chaine pour SQL, entre quotes simples, jamais une concatenation nue."""
    return "'" + str(v).replace("'", "''") + "'"


def main() -> int:
    if not RAPPORT.exists():
        print("⛔ le rapport du gel du 16/11 manque : %s" % RAPPORT)
        print("   le produire d'abord : .venv\\Scripts\\python.exe -X utf8 "
              "phase2\\checks\\rapport_gel_tous_les_champs.py")
        return 2

    with RAPPORT.open(encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))

    # ── ① LA SELECTION, et chaque filtre est DIT ─────────────────────────────
    etape = Counter()
    cibles = []
    for l in lignes:
        if not (l.get("v_Offre Achat") or "").strip().lower().startswith("classeur seul"):
            continue
        etape["① le classeur a une date d'offre, nous rien"] += 1
        if "offre" in (l.get("roles geles") or "").lower():
            etape["   ecartee : une offre est DEJA reliee a cette ligne"] += 1
            continue
        etape["② et le role « offre » manque vraiment"] += 1
        if (l.get("c_Etat Actuel") or "").strip() != "Annulée":
            etape["   ecartee : l'etat du classeur n'est pas « Annulee »"] += 1
            continue
        etape["③ etat « Annulee » -> state 'refused', aucune regle de chainage"] += 1
        if (l.get("chainage douteux") or "").strip().lower() not in ("", "0", "non", "false"):
            etape["   ecartee : chainage DOUTEUX (decouverte 7 du rapport)"] += 1
            continue
        etape["④ et le chainage n'est pas douteux"] += 1
        cibles.append({"id_unique": l["ID Unique"],
                       "date": (l.get("c_Offre Achat") or "").strip(),
                       "acquereur": (l.get("c_Acquereur") or "").strip(),
                       "mandat": (l.get("Mandat classeur") or "").strip()})

    print("=== ① LA SELECTION, FILTRE PAR FILTRE ===")
    for k, v in etape.items():
        print("   %-62s %4d" % (k, v))
    print()

    cl = client()

    # ── ② LA CONFIANCE DU GEL : la garde du projet ───────────────────────────
    liens = par_lots(cl, "app_classeur_lien", "id_unique,app_affaire_id,role,confiance",
                     "id_unique", [c["id_unique"] for c in cibles], citer=True)
    par_id: dict[str, list[dict]] = {}
    for r in liens:
        par_id.setdefault(r["id_unique"], []).append(r)

    gardees, refusees = [], Counter()
    for c in cibles:
        niveaux = {str(x.get("confiance") or "?") for x in par_id.get(c["id_unique"], [])}
        if niveaux != {"sûre"}:
            refusees["confiance " + ("+".join(sorted(niveaux)) or "(aucun lien)")] += 1
            continue
        gardees.append(c)
    print("=== ② LA GARDE DU PROJET : « 1re passe, confiance SURE seulement » ===")
    print("   gardees %d" % len(gardees))
    for k, v in refusees.items():
        print("   ecartees : %-40s %4d" % (k, v))
    print()

    # ── ③ LE RATTACHEMENT, pris sur ce que le gel a DEJA relie ───────────────
    aff = [x["app_affaire_id"] for c in gardees for x in par_id[c["id_unique"]]]
    rows = par_lots(cl, "app_affaire_ledger",
                    "app_affaire_id,app_chaine_id,app_dossier_id,app_dossier_uuid,"
                    "app_dossier_numero,hektor_annonce_id,kind", "app_affaire_id", aff)
    par_aff = {str(r["app_affaire_id"]): r for r in rows}

    pretes, ecartees = [], Counter()
    for c in gardees:
        vus = [par_aff.get(str(x["app_affaire_id"])) for x in par_id[c["id_unique"]]]
        vus = [v for v in vus if v]
        ch = {v["app_chaine_id"] for v in vus if v.get("app_chaine_id")}
        do = {v["app_dossier_id"] for v in vus if v.get("app_dossier_id")}
        an = {v["hektor_annonce_id"] for v in vus if v.get("hektor_annonce_id")}
        uu = {v["app_dossier_uuid"] for v in vus if v.get("app_dossier_uuid")}
        nu = {v["app_dossier_numero"] for v in vus if v.get("app_dossier_numero")}
        if len(ch) != 1 or len(an) != 1:
            ecartees["rattachement ambigu (%d chaine(s), %d annonce(s))"
                     % (len(ch), len(an))] += 1
            continue
        if not c["date"]:
            ecartees["pas de date d'offre au classeur"] += 1
            continue
        c.update(chaine=ch.pop(), annonce=an.pop(),
                 dossier=(do.pop() if len(do) == 1 else None),
                 uuid=(uu.pop() if len(uu) == 1 else None),
                 numero=(nu.pop() if len(nu) == 1 else None))
        pretes.append(c)
    print("=== ③ LE RATTACHEMENT, PRIS SUR LE GEL (jamais devine) ===")
    print("   pretes %d" % len(pretes))
    for k, v in ecartees.items():
        print("   ecartees : %-40s %4d" % (k, v))
    print()

    # ── ④ LA GARDE QUI COMPTE : une seule offre neuve par chaine ─────────────
    vu = Counter(c["chaine"] for c in pretes)
    doubles = {k for k, v in vu.items() if v > 1}
    if doubles:
        print("=== ④ ⛔ DEUX LIGNES DU CLASSEUR VISENT LA MEME CHAINE ===")
        for ch in sorted(doubles):
            ids = [c["id_unique"] for c in pretes if c["chaine"] == ch]
            print("   chaine %-10s : %s" % (ch, ", ".join(ids)))
        pretes = [c for c in pretes if c["chaine"] not in doubles]
        print("   -> ECARTEES : on ne pose pas deux offres sur une meme chaine")
        print("      sans avoir decide laquelle. Elles reviendront a la 2e passe.")
    else:
        print("=== ④ une seule offre neuve par chaine : OK, aucun doublon ===")
    print()

    # ── ⑤ UNE OFFRE EXISTE-T-ELLE DEJA A LA MEME DATE ? ─────────────────────
    # ⛔⛔ LA PREMIERE VERSION DE CETTE GARDE ECARTAIT « la chaine porte deja une
    #   offre » -- ET C'ETAIT TROP STRICT : elle retirait 16 lignes, dont 15 sont
    #   de VRAIES offres CONCURRENTES (un bien recoit plusieurs offres, une est
    #   acceptee, les autres annulees ; nous n'avons garde que celle qui a abouti,
    #   le classeur garde la trace des autres). La garde ecartait donc exactement
    #   ce qu'on cherche a recuperer. Corrige sur la demande de Frederic du 16/11 :
    #   « il faut controler les 16 avant ».
    #
    # ⭐ LE SEUL VRAI DOUBLON SE RECONNAIT A LA DATE, ET L'AUDIT DE 60CLRO51 DIT
    #   POURQUOI : sur la chaine 17387, TOUTES les transactions portent le MEME
    #   acquereur (NICOUD, id 322158), parce que le classeur a DEUX lignes pour ce
    #   dossier -- la tentative annulee et celle qui a abouti. Comparer les NOMS ne
    #   protege donc de rien ; c'est la DATE qui departage.
    #
    # ⚠ ET LE GEL LAISSE DES OFFRES SANS LIEN : 63 sur 4 583 (1,4 %), dont 55
    #   'refused'. Mesure du 16/11. Une seule touche nos cibles -- 60CLRO51 --
    #   mais la garde doit tenir pour les autres le jour ou le lot s'elargira.
    deja = par_lots(cl, "app_affaire_ledger", "app_chaine_id,kind,date",
                    "app_chaine_id", [c["chaine"] for c in pretes])
    dates_par_chaine: dict[str, set[str]] = {}
    for r in deja:
        if str(r.get("kind")) == "offre":
            dates_par_chaine.setdefault(str(r["app_chaine_id"]), set()).add(
                str(r.get("date") or "")[:10])
    avant, ecartees_date = len(pretes), []
    gardees_5 = []
    for c in pretes:
        if c["date"] in dates_par_chaine.get(str(c["chaine"]), set()):
            ecartees_date.append(c)
        else:
            gardees_5.append(c)
    pretes = gardees_5
    print("=== ⑤ UNE OFFRE EXISTE-T-ELLE DEJA A LA MEME DATE ? ===")
    print("   ecartees (doublon reel) : %d   ->  RESTENT %d"
          % (avant - len(pretes), len(pretes)))
    for c in ecartees_date:
        print("     %-10s mandat %-8s date %s -- nous l avons DEJA"
              % (c["id_unique"], c["mandat"], c["date"]))
    print()

    if not pretes:
        print("⛔ aucune ligne ne passe toutes les gardes -- rien n'est genere.")
        return 1

    # ── ⑥ LE PATCH ───────────────────────────────────────────────────────────
    valeurs = []
    for c in pretes:
        valeurs.append(
            "    (%s, %s, %s, %s, %s, %s, %s)"
            % (txt(c["id_unique"]), c["chaine"],
               c["dossier"] if c["dossier"] else "null",
               c["annonce"],
               txt(c["uuid"]) + "::uuid" if c["uuid"] else "null",
               txt(c["numero"]) if c["numero"] else "null",
               txt(c["date"])))
    acquereurs = {c["id_unique"]: c["acquereur"] for c in pretes}
    notes = []
    for c in pretes:
        texte = ("Acquereur au classeur : %s. Reprise de l historique (ligne %s, "
                 "mandat %s) -- non resolu en contact, pose en note pour ne pas "
                 "reveiller le calcul des parties ni la regle [D] du chainage."
                 % (c["acquereur"] or "(vide)", c["id_unique"], c["mandat"] or "-"))
        notes.append("    (%s, %s)" % (txt(c["id_unique"]), txt(texte)))

    patch = """-- ════════════════════════════════════════════════════════════════════════════
-- C5 / LOT B -- LES %(n)d OFFRES « ANNULEE » DU CLASSEUR
-- 16/11/2026 . chantier classeur, tache 3.3 lot B . genere par
-- phase2/checks/poser_offres_annulees_classeur_2026-11-16.py
-- ════════════════════════════════════════════════════════════════════════════
--
-- CE QU'ON POSE : %(n)d offres que le classeur porte et que nous n'avons pas, dont
--   l'etat au classeur est « Annulee ». Elles entrent en `state = 'refused'`, donc
--   AUCUNE des 4 regles de chainage ne se declenche -- c'est exactement le cas
--   eprouve en reel par l'essai A2 dans la nuit du 15 au 16/11.
--
-- ⛔ LA MARQUE EST DANS LE MEME INSERT (piece 1) : `transaction_origine = 'classeur'`.
--   Une ligne du classeur DEMARQUEE, meme une seconde, et le filet du worker lui
--   collerait le numero d'une transaction Hektor EXISTANTE.
--
-- ⛔ NI acquereurs_json NI mandants_json : le nom de l'acquereur va dans
--   app_affaire_note (origine 'classeur'), decision de Frederic du 16/11. Sans eux,
--   le declencheur app_affaire_partie_suivre ne cree aucune partie, et la regle [D]
--   « meme acheteur -> dossiers reunis » ne peut pas jouer.
--
-- LE NUMERO EST FRAPPE PAR SUPABASE : nextval('app_affaire_id_app_seq').
-- LE RATTACHEMENT (chaine, dossier, annonce) est PRIS sur la transaction que le gel
--   relie deja a la meme ligne du classeur -- rien n'est devine.
--
-- RETOUR ARRIERE : %(base)s_INVERSE.sql
-- CONTROLES      : %(base)s_REPETITION.sql
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── LES GARDES : le patch S'ARRETE plutot que d'ecrire a moitie
do $$
declare
  deja integer;
begin
  if not exists (select 1 from information_schema.columns
                  where table_schema = 'public' and table_name = 'app_affaire_ledger'
                    and column_name = 'transaction_origine') then
    raise exception 'ARRET : la colonne transaction_origine manque -- poser la piece 1 d abord';
  end if;

  select count(*) into deja from app_affaire_ledger where transaction_origine = 'classeur';
  if deja <> 0 then
    raise exception 'ARRET : %%s ligne(s) sont deja marquees classeur -- ce patch est le PREMIER, il ne doit pas etre rejoue', deja;
  end if;

  if not exists (select 1 from pg_class where relname = 'app_affaire_id_app_seq') then
    raise exception 'ARRET : la sequence app_affaire_id_app_seq est introuvable';
  end if;
end $$;

-- ── LES %(n)d OFFRES, ET LEUR NOTE, DANS UNE SEULE INSTRUCTION
with donnees (id_unique, chaine, dossier, annonce, dossier_uuid, dossier_numero, dt) as (
  values
%(valeurs)s
),
notes (id_unique, texte) as (
  values
%(notes)s
),
posees as (
  insert into app_affaire_ledger (
    app_affaire_id, app_chaine_id, app_dossier_id,
    kind, state, date,
    hektor_annonce_id, hektor_affaire_id, present_in_hektor,
    app_dossier_uuid, app_dossier_numero,
    transaction_origine,
    payload_json, first_seen_at, last_seen_at)
  select nextval('app_affaire_id_app_seq'), d.chaine, d.dossier,
         'offre', 'refused', d.dt,
         d.annonce, null, false,
         d.dossier_uuid, d.dossier_numero,
         '%(marque)s',
         jsonb_build_object(
           'classeur_id_unique', d.id_unique,
           'classeur_lot', 'C5 lot B -- offres annulees',
           'classeur_pose_le', '2026-11-16',
           'etat_au_classeur', 'Annulee'),
         now(), now()
    from donnees d
  returning app_affaire_id, app_chaine_id, (payload_json ->> 'classeur_id_unique') as id_unique
)
insert into app_affaire_note (app_affaire_id, texte, app_dossier_id, app_chaine_id, origine)
select p.app_affaire_id, n.texte, d.dossier, d.chaine, '%(marque)s'
  from posees p
  join notes   n on n.id_unique = p.id_unique
  join donnees d on d.id_unique = p.id_unique;

-- ── LES CONTROLES, AVANT LE COMMIT : ils annulent tout si un compte ne tombe pas
do $$
declare
  posees integer;
  notees integer;
  sans_marque integer;
  avec_numero integer;
  avec_parties integer;
begin
  select count(*) into posees from app_affaire_ledger where transaction_origine = '%(marque)s';
  if posees <> %(n)d then
    raise exception 'ARRET : %%s ligne(s) marquees classeur au lieu de %(n)d', posees;
  end if;

  select count(*) into notees from app_affaire_note where origine = '%(marque)s';
  if notees < %(n)d then
    raise exception 'ARRET : %%s note(s) seulement pour %(n)d offres', notees;
  end if;

  select count(*) into sans_marque from app_affaire_ledger
   where transaction_origine = '%(marque)s'
     and (kind <> 'offre' or state <> 'refused' or present_in_hektor
          or hektor_affaire_id is not null or app_chaine_id is null);
  if sans_marque <> 0 then
    raise exception 'ARRET : %%s ligne(s) posees ne respectent pas la forme attendue', sans_marque;
  end if;

  select count(*) into avec_numero from app_affaire_ledger
   where transaction_origine = '%(marque)s' and app_affaire_id < 1000000;
  if avec_numero <> 0 then
    raise exception 'ARRET : %%s ligne(s) hors de la plage app (>= 1 000 000)', avec_numero;
  end if;

  -- ⭐ LE TEMOIN DE L'ACQUEREUR : sans acquereurs_json, le declencheur ne doit
  --   avoir cree AUCUNE partie pour ces lignes.
  select count(*) into avec_parties from app_affaire_partie p
    join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
   where l.transaction_origine = '%(marque)s';
  if avec_parties <> 0 then
    raise exception 'ARRET : %%s partie(s) creees alors qu aucun acquereur n a ete pose', avec_parties;
  end if;

  raise notice 'OK : %(n)d offres posees, %%s notes, 0 partie creee, toutes dans la plage app', notees;
end $$;

-- ── CE QUI VIENT D'ETRE POSE, a lire dans la sortie
select kind, state, present_in_hektor, transaction_origine,
       count(*) as lignes, min(app_affaire_id) as premier, max(app_affaire_id) as dernier
  from app_affaire_ledger
 where transaction_origine = '%(marque)s'
 group by 1,2,3,4;

commit;
""" % {"n": len(pretes), "valeurs": ",\n".join(valeurs), "notes": ",\n".join(notes),
       "marque": MARQUE, "base": BASE}

    inverse = """-- ════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DES %(n)d OFFRES « ANNULEE » DU CLASSEUR -- 16/11/2026
-- ════════════════════════════════════════════════════════════════════════════
--
-- ⛔ IL NE JUGE QUE SA PART (regle n0 31) : il retire les lignes marquees
--   `transaction_origine = 'classeur'` ET nees de CE lot (payload_json le dit),
--   puis il VERIFIE qu'il ne reste aucune trace et que les voisines sont intactes.
--
-- ⚠ ON NE VISE PAS « la plage app » : ce serait emporter les 340 lignes legitimes.
--   On vise LE MARQUEUR DU LOT, comme l'inverse de l'essai A2 visait le sien.
-- ════════════════════════════════════════════════════════════════════════════

begin;

-- ── a lire AVANT
select count(*) as a_retirer
  from app_affaire_ledger
 where transaction_origine = '%(marque)s'
   and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees';

-- ── les notes d'abord (elles pointent les lignes)
delete from app_affaire_note
 where origine = '%(marque)s'
   and app_affaire_id in (select app_affaire_id from app_affaire_ledger
                           where transaction_origine = '%(marque)s'
                             and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees');

delete from app_affaire_ledger
 where transaction_origine = '%(marque)s'
   and (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees';

-- ── LES CONTROLES DU RETOUR ARRIERE
do $$
declare
  reste integer;
  plage_avec_numero integer;
  hors_plage integer;
begin
  select count(*) into reste from app_affaire_ledger
   where (payload_json ->> 'classeur_lot') = 'C5 lot B -- offres annulees';
  if reste <> 0 then
    raise exception 'ARRET : il reste %%s ligne(s) du lot -- le retour est INCOMPLET', reste;
  end if;

  select count(*) into plage_avec_numero from app_affaire_ledger
   where app_affaire_id >= 1000000
     and hektor_affaire_id is not null and btrim(hektor_affaire_id) <> '';
  if plage_avec_numero <> 340 then
    raise exception 'ARRET : la plage app AVEC numero vaut %%s au lieu de 340 -- NE PAS VALIDER', plage_avec_numero;
  end if;

  select count(*) into hors_plage from app_affaire_ledger where app_affaire_id < 1000000;
  if hors_plage <> 30817 then
    raise exception 'ARRET : le hors-plage vaut %%s au lieu de 30 817 -- NE PAS VALIDER', hors_plage;
  end if;

  raise notice 'retour arriere OK : 0 trace du lot, voisines intactes (340 + 30 817)';
end $$;

commit;
""" % {"n": len(pretes), "marque": MARQUE}

    repetition = """-- ════════════════════════════════════════════════════════════════════════════
-- CONTROLES DES %(n)d OFFRES « ANNULEE » -- 16/11/2026 . A REJOUER QUAND ON VEUT
-- ⛔ AUCUNE ECRITURE. Tout est en select.
-- ════════════════════════════════════════════════════════════════════════════

-- ① le compte, la forme, et la plage
select 'posees' as controle, count(*) as valeur, '%(n)d attendues' as attendu
  from app_affaire_ledger where transaction_origine = '%(marque)s'
union all
select 'toutes en offre/refused', count(*), '%(n)d'
  from app_affaire_ledger
 where transaction_origine = '%(marque)s' and kind = 'offre' and state = 'refused'
union all
select 'toutes sans numero Hektor', count(*), '%(n)d'
  from app_affaire_ledger
 where transaction_origine = '%(marque)s' and hektor_affaire_id is null
   and present_in_hektor = false
union all
select 'toutes dans la plage app', count(*), '%(n)d'
  from app_affaire_ledger
 where transaction_origine = '%(marque)s' and app_affaire_id >= 1000000
union all
select 'toutes rattachees a une chaine', count(*), '%(n)d'
  from app_affaire_ledger
 where transaction_origine = '%(marque)s' and app_chaine_id is not null
union all
select 'leurs notes', count(*), 'au moins %(n)d'
  from app_affaire_note where origine = '%(marque)s'
union all
-- ② ⭐ LE TEMOIN DE L'ACQUEREUR : aucune partie ne doit avoir ete creee
select 'parties creees (doit etre 0)', count(*), '0'
  from app_affaire_partie p
  join app_affaire_ledger l on l.app_affaire_id = p.app_affaire_id
 where l.transaction_origine = '%(marque)s'
union all
-- ③ ⭐ LE TEMOIN INVERSE : les voisines n'ont pas bouge
select 'plage app AVEC numero (voisines)', count(*), '340'
  from app_affaire_ledger
 where app_affaire_id >= 1000000 and hektor_affaire_id is not null
   and btrim(hektor_affaire_id) <> ''
union all
select 'hors plage (voisines)', count(*), '30817'
  from app_affaire_ledger where app_affaire_id < 1000000
union all
-- ④ ⛔ ET LA SENTINELLE NE DOIT PAS CRIER : la garde de l'origine joue
select 'ce que voit data.transaction_disparue', count(*), '0'
  from app_affaire_ledger
 where present_in_hektor = false
   and last_seen_at >= now() - interval '48 hours'
   and transaction_origine is null
union all
select 'ce que voit data.affaire_sans_numero_hektor', count(*), '0'
  from app_affaires_sans_numero_hektor
order by 1;
""" % {"n": len(pretes), "marque": MARQUE}

    (SORTIE / (BASE + ".sql")).write_text(patch, encoding="utf-8")
    (SORTIE / (BASE + "_INVERSE.sql")).write_text(inverse, encoding="utf-8")
    (SORTIE / (BASE + "_REPETITION.sql")).write_text(repetition, encoding="utf-8")

    print("=== ⑥ LES TROIS FICHIERS SONT ECRITS (rien n'est pose en base) ===")
    for suffixe in ("", "_INVERSE", "_REPETITION"):
        p = SORTIE / (BASE + suffixe + ".sql")
        print("   %-78s %7d octets" % (p, p.stat().st_size))
    print()
    print("=== LE LOT FINAL : %d offres ===" % len(pretes))
    print("   les 5 premieres :")
    for c in pretes[:5]:
        print("     %-10s date %-12s chaine %-8s dossier %-10s annonce %s"
              % (c["id_unique"], c["date"], c["chaine"], c["dossier"], c["annonce"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
