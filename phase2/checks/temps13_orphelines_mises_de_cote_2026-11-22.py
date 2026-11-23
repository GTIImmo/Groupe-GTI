"""Chantier classeur, ⑲ (22/11/2026) -- LES REPARTITIONS ORPHELINES MISES DE COTE : SA REGLE. FABRIQUE, JAMAIS JOUE.

SA REGLE (son mot du 22/11, point 4), devenue REGLE GENERALE DU PROJET :
  « ON NE SUPPRIME PAS UNE PART, ON LA MET DE COTE AVEC SON ANCIEN NUMERO DE DOSSIER. »
    . deux parts IDENTIQUES (le dossier disparu et celui ou sa transaction vit portent les memes parts) -> la part du
      dossier disparu passe dans une TABLE DE GARDE DATEE, qui conserve l'ancien numero de dossier ;
    . deux parts DIFFERENTES -> elles lui REMONTENT, il tranche (ce script n'y touche pas) ;
    . RIEN NE S'APPLIQUE AVANT LA V3 et sa nuit de stabilite.
  POURQUOI PAS LA SUPPRESSION (mon objection du 22/11, qu'il a retenue) : un dossier disparu peut REVENIR -- 4 des 13 de
  ce matin reviennent avec la V3 (14034, 19070, 20089, 27135). Des parts supprimees ne se recalculent jamais ; des parts
  mises de cote se REPOSENT, parce que la table garde leur ancien numero.

« IDENTIQUES » : pour chaque part non Hektor, le meme (cote, rang, numero du negociateur, nom, pourcentage, ORIGINE) des
  deux cotes -- la meme liste, ligne pour ligne.
  ⭐ LA MEME ORIGINE (saisie / classeur_reconstitue / defaut) : ajoutee par Frederic le 23/11 (carnet § 20.21). Avant, elle
  etait montree sans etre comparee -- l'angle mort : une VRAIE SAISIE humaine face a une de nos copies du classeur, aux
  memes negociateur et pourcentage, aurait ete mise de cote A LA PLACE de la copie. Desormais elle lui REMONTE. Le 23/11
  ca ne change rien (les 26 et leurs vis-a-vis sont tous « classeur_reconstitue ») : c'est gratuit aujourd'hui.
  La comparaison est faite DEUX fois, et les deux portent l'origine : en Python (cle) pour fabriquer la liste, et en SQL
  dans la garde du patch, qui la refait au moment de jouer.
LIRE (lecture seule, aucun fichier ecrit) : la meme classification sur l'etat vivant. ESSAIS (hors ligne) : la regle sur
  des cas fabriques, dont le temoin inverse de l'angle mort.
⚠ CE QUE LA NUIT FAIT DEJA, ET QUE CE PATCH NE CHANGE PAS : la purge (app_repartition_purger_orphelines) ne supprime que
  les parts DERIVEES de Hektor (origine « hektor% »), que la meme etape recalcule et repousse le meme matin depuis
  intervenants_json ; elle ne supprime JAMAIS une saisie, une part « defaut » ni une part reconstituee du Sheet.

DEUX ETAPES (un appel = une etape, lecture seule sauf la repetition a blanc, qui finit par ROLLBACK) :
  fabriquer --etiquette X   lit l'etat VIVANT (pooler, read only), FIGE la liste dans le patch (chaque part par son
                            numero), et ecrit supabase/patch_repartitions_orphelines_mises_de_cote_<X>.sql
                            + _A_BLANC (rollback) + _INVERSE + _REPETITION
  blanc --etiquette X       joue le corps du _A_BLANC dans UNE transaction, puis ROLLBACK ; temoin : apres, les
                            orphelines, l'empreinte des repartitions et l'absence de la table de garde sont celles d'avant
⛔ Le patch d'aujourd'hui (etiquette « essai_avant_v3 ») ne sert QU'A EPROUVER le mecanisme sur les 26 de ce matin. Il ne
  se joue JAMAIS : celui qui se jouera sera refabrique APRES la V3 et sa nuit de stabilite, sur l'etat de ce jour-la, et
  repete a blanc a nouveau -- puis son « vas-y ».
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

GARDE = "app_affaire_repartition_mise_de_cote"
SUPA = RACINE / "supabase"
EMPREINTE = ("md5(coalesce(string_agg(app_chaine_id||':'||cote||':'||rang||':'||hektor_user_id||':'||coalesce(nom_au_moment,'')"
             "||':'||pourcentage||':'||coalesce(origine,''), ',' order by app_chaine_id, cote, rang), ''))")


def connexion():
    import psycopg2
    from phase2.sync import push_upgrade_to_supabase as PU
    PU.load_env_files(PU.DEFAULT_ENV_FILES)
    u = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    return psycopg2.connect(host=os.environ["SUPABASE_POOLER_HOST"], port=5432, dbname="postgres",
                            user="postgres.dwaqxfrinihnychuoptk", password=urllib.parse.unquote(u.password),
                            connect_timeout=15, sslmode="require")


def q(s) -> str:
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"


def lire_etat() -> dict:
    cn = connexion()
    cu = cn.cursor()
    cu.execute("set transaction read only")
    cu.execute("""select r.app_chaine_id, l.app_chaine_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
                         r.pourcentage, r.origine
                    from app_affaire_repartition r
                    left join app_affaire_ledger l on l.app_affaire_id = r.app_chaine_id
                   where coalesce(r.origine, '') not like 'hektor%%'
                     and not exists (select 1 from app_affaire_ledger x where x.app_chaine_id = r.app_chaine_id)""")
    orph = cu.fetchall()
    nouveaux = sorted({n for _a, n, *_ in orph if n is not None})
    cu.execute("""select app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine
                    from app_affaire_repartition where coalesce(origine, '') not like 'hektor%%'
                     and app_chaine_id = any(%s)""", (nouveaux,))
    arrivee = defaultdict(list)
    for c, *r in cu.fetchall():
        arrivee[c].append(tuple(r))
    cu.execute("select count(*) from app_v_repartition_orpheline")
    n_vue = cu.fetchone()[0]
    cu.execute("select count(*), %s from app_affaire_repartition" % EMPREINTE)
    n_rep, emp = cu.fetchone()
    cu.execute("select to_regclass('public.%s') is null" % GARDE)
    absente = cu.fetchone()[0]
    cn.rollback()
    cn.close()
    par = defaultdict(list)
    for a, n, *r in orph:
        par[(a, n)].append(tuple(r))
    return {"par": par, "arrivee": arrivee, "n_vue": n_vue, "n_rep": n_rep, "emp": emp, "garde_absente": absente}


def cle(r) -> tuple:
    """(cote, rang, negociateur, nom, pourcentage, ORIGINE) -- l'origine compte depuis le 23/11 (sa regle 6, § 20.21)."""
    cote, rang, uid, nom, pct, orig = r
    return (cote, int(rang), str(uid), (nom or "").strip().upper(), float(pct or 0), (orig or "").strip())


def classer(par: dict, arrivee: dict) -> tuple:
    """SA REGLE 6, pure : (identiques, differentes, sans_tx). par : {(disparu, arrivee): [parts]} ; arrivee : {dossier:
    [parts]}. Une part = (cote, rang, negociateur, nom, pourcentage, origine)."""
    identiques, differentes, sans_tx = [], [], []
    for (a, n), rows in sorted(par.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        if n is None:
            sans_tx.append((a, rows))
        elif sorted(map(cle, rows)) == sorted(map(cle, arrivee.get(n, []))):
            identiques.append((a, n, rows))
        else:
            differentes.append((a, n, rows, arrivee.get(n, [])))
    return identiques, differentes, sans_tx


def essais() -> int:
    """HORS LIGNE : la regle 6 avec « meme origine », et le temoin inverse de l'angle mort."""
    ko = []

    def exige(nom, ok, detail=""):
        print("   %s %s%s" % ("OUI" if ok else "NON", nom, (" (%s)" % detail) if detail else ""))
        if not ok:
            ko.append(nom)

    copie = [("entree", 1, "32", "CHRISTELE GENTES", 50, "classeur_reconstitue"),
             ("sortie", 1, "32", "CHRISTELE GENTES", 50, "classeur_reconstitue")]
    saisie = [("entree", 1, "32", "CHRISTELE GENTES", 50, "saisie"),
              ("sortie", 1, "32", "CHRISTELE GENTES", 50, "saisie")]
    i, d, s = classer({(3670, 3669): copie}, {3669: list(copie)})
    exige("deux copies du classeur, memes parts, meme origine -> IDENTIQUES (mises de cote)", len(i) == 1 and not d)
    i, d, s = classer({(3670, 3669): saisie}, {3669: list(copie)})
    exige("TEMOIN INVERSE DE L'ANGLE MORT : une VRAIE SAISIE (orpheline) face a notre copie (en place) -> elle LUI "
          "REMONTE, elle n'est PAS mise de cote", not i and len(d) == 1)
    i, d, s = classer({(3670, 3669): copie}, {3669: list(saisie)})
    exige("TEMOIN INVERSE : notre copie (orpheline) face a une vraie saisie (en place) -> elle lui remonte aussi", not i
          and len(d) == 1)
    mixte = [copie[0], ("sortie", 1, "32", "CHRISTELE GENTES", 50, "saisie")]
    i, d, s = classer({(3670, 3669): mixte}, {3669: list(copie)})
    exige("TEMOIN INVERSE : UNE seule part d'une autre origine sur deux -> le dossier entier lui remonte", not i
          and len(d) == 1)
    i, d, s = classer({(3670, 3669): copie}, {3669: [copie[0], ("sortie", 1, "82", "CELINE HERITIER", 50,
                                                                 "classeur_reconstitue")]})
    exige("un autre negociateur, meme origine -> lui remonte (inchange)", not i and len(d) == 1)
    i, d, s = classer({(3670, None): copie}, {})
    exige("une transaction disparue -> sans transaction, un humain tranche (inchange)", not i and not d and len(s) == 1)
    i, d, s = classer({(3670, 3669): [("entree", 1, "32", " christele gentes ", 50.0, " classeur_reconstitue ")]},
                      {3669: [("entree", 1, 32, "CHRISTELE GENTES", 50, "classeur_reconstitue")]})
    exige("les blancs et la casse ne font pas une autre origine ni un autre nom", len(i) == 1)
    print("%s" % ("⭐ ESSAIS : tout est vert" if not ko else "⛔ ESSAIS : %d NON -- %s" % (len(ko), ko)))
    return 1 if ko else 0


def lire() -> int:
    """LECTURE SEULE, aucun fichier ecrit : la classification de sa regle 6 (meme origine comprise) sur l'etat vivant."""
    E = lire_etat()
    identiques, differentes, sans_tx = classer(E["par"], E["arrivee"])
    origines = defaultdict(int)
    for rows in E["par"].values():
        for r in rows:
            origines[r[5]] += 1
    for rows in E["arrivee"].values():
        for r in rows:
            origines["(en place) %s" % r[5]] += 1
    print("ETAT VIVANT (lecture seule) : %d orphelines (la vue %d) sur %d dossiers disparus ; origines %s" % (
        sum(len(r) for r in E["par"].values()), E["n_vue"], len(E["par"]), dict(origines)))
    print("   IDENTIQUES, MEME ORIGINE COMPRISE -> se mettraient de cote : %d dossiers, %d parts : %s" % (
        len(identiques), sum(len(r) for _a, _n, r in identiques), [a for a, _n, _r in identiques]))
    print("   DIFFERENTES -> LUI REMONTENT : %d %s" % (len(differentes), [(a, n) for a, n, *_ in differentes]))
    print("   SANS TRANSACTION : %d %s" % (len(sans_tx), [a for a, _r in sans_tx]))
    return 0


def fabriquer(etiquette: str) -> int:
    E = lire_etat()
    identiques, differentes, sans_tx = classer(E["par"], E["arrivee"])
    n_mis = sum(len(r) for _a, _n, r in identiques)
    print("ETAT VIVANT : %d orphelines (la vue en compte %d) sur %d dossiers disparus ; repartitions %d, empreinte %s ; "
          "table de garde absente : %s" % (sum(len(r) for r in E["par"].values()), E["n_vue"], len(E["par"]), E["n_rep"],
                                          E["emp"], E["garde_absente"]))
    print("   IDENTIQUES -> mises de cote : %d dossiers, %d parts : %s" % (len(identiques), n_mis,
                                                                         [(a, n) for a, n, _r in identiques]))
    print("   DIFFERENTES -> LUI REMONTENT : %d %s" % (len(differentes), [(a, n) for a, n, *_ in differentes]))
    for a, n, rows, arr in differentes:
        print("      %d (disparu) : %s" % (a, sorted(map(cle, rows))))
        print("      %d (vivant)  : %s" % (n, sorted(map(cle, arr))))
    print("   SANS TRANSACTION (un humain tranche) : %d %s" % (len(sans_tx), [a for a, _r in sans_tx]))
    if not identiques:
        print("rien a mettre de cote : pas de patch")
        return 0
    stem = "patch_repartitions_orphelines_mises_de_cote_%s" % etiquette
    par_ = "orphelines_mises_de_cote_%s" % etiquette
    liste = ",\n".join("    (%d, %d, %s, %d)" % (a, n, q(r[0]), int(r[1])) for a, n, rows in identiques for r in sorted(rows))
    temoin_a, temoin_n, _r = identiques[0]
    entete = """-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- LES REPARTITIONS ORPHELINES MISES DE COTE -- SA REGLE DU 22/11 (« on ne supprime pas une part »)     %(quand)s
-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- ⛔ DORMANT : il ne se joue qu'avec le « vas-y » explicite de Frederic, dans la conversation, APRES la V3 et sa nuit
--   de stabilite. ⛔⛔ IL PORTE SON `commit;`. La repetition a blanc est ..._A_BLANC.sql (rollback).
-- SOURCE : phase2/checks/temps13_orphelines_mises_de_cote_2026-11-22.py fabriquer --etiquette %(etiq)s -- ne pas le
--   retoucher a la main. ETAT LU : %(n_orph)d orphelines sur %(n_dos)d dossiers disparus ; repartitions %(n_rep)d.
-- CE QU'IL FAIT : %(n_id)d dossiers disparus dont les parts sont IDENTIQUES a celles du dossier ou leur transaction vit
--   -> leurs %(n_mis)d parts passent dans %(garde)s, AVEC LEUR ANCIEN NUMERO DE DOSSIER, puis
--   quittent app_affaire_repartition. Rien n'est perdu : l'INVERSE les repose a l'identique.
-- CE QU'IL NE FAIT PAS : les %(n_diff)d dossiers aux parts DIFFERENTES (%(diff)s) lui remontent, intacts ; il ne
--   touche ni une part derivee de Hektor, ni le chainage, ni le gel, ni Hektor.
-- RETOUR ARRIERE : %(stem)s_INVERSE.sql . CONTROLE : %(stem)s_REPETITION.sql (lecture seule)
-- ════════════════════════════════════════════════════════════════════════════════════════════════
""" % {"quand": datetime.now().strftime("%d/%m/%Y %H:%M"), "etiq": etiquette,
       "n_orph": sum(len(r) for r in E["par"].values()), "n_dos": len(E["par"]), "n_rep": E["n_rep"],
       "n_id": len(identiques), "n_mis": n_mis, "garde": GARDE, "n_diff": len(differentes),
       "diff": " ".join("%d->%d" % (a, n) for a, n, *_ in differentes) or "aucun", "stem": stem}
    corps = """begin;

-- ── ① LA GARDE : l'etat est EXACTEMENT celui que la fabrication a lu ───────────────────────────
do $$
declare n int; emp text; ko int;
begin
  select count(*), %(emp_sql)s into n, emp from app_affaire_repartition;
  if n <> %(n_rep)d or emp <> %(emp)s then
    raise exception '⛔ garde : les repartitions ont bouge (%% lignes, empreinte %%) -- rien n''est ecrit', n, emp;
  end if;
  -- chaque part de la liste est encore orpheline, et son dossier d'arrivee vit
  select count(*) into ko from (values
%(liste)s
  ) v(ancien, nouveau, cote, rang)
  where exists (select 1 from app_affaire_ledger x where x.app_chaine_id = v.ancien)
     or not exists (select 1 from app_affaire_ledger x where x.app_chaine_id = v.nouveau)
     or not exists (select 1 from app_affaire_repartition r where r.app_chaine_id = v.ancien
                       and r.cote = v.cote and r.rang = v.rang and coalesce(r.origine, '') not like 'hektor%%');
  if ko <> 0 then raise exception '⛔ garde : %% part(s) ne sont plus orphelines ou leur dossier d''arrivee manque', ko; end if;
  -- et chaque dossier disparu porte EXACTEMENT les memes parts que son dossier d'arrivee (la regle : identiques,
  --   MEME ORIGINE comprise -- sa regle 6, completee le 23/11)
  select count(*) into ko from (select distinct ancien, nouveau from (values
%(liste)s
  ) v(ancien, nouveau, cote, rang)) p
  where (select string_agg(cote||':'||rang||':'||hektor_user_id||':'||upper(trim(coalesce(nom_au_moment,'')))||':'||pourcentage::numeric(9,3)||':'||trim(coalesce(origine,'')),
                           ',' order by cote, rang)
           from app_affaire_repartition where app_chaine_id = p.ancien and coalesce(origine, '') not like 'hektor%%')
        is distinct from
        (select string_agg(cote||':'||rang||':'||hektor_user_id||':'||upper(trim(coalesce(nom_au_moment,'')))||':'||pourcentage::numeric(9,3)||':'||trim(coalesce(origine,'')),
                           ',' order by cote, rang)
           from app_affaire_repartition where app_chaine_id = p.nouveau and coalesce(origine, '') not like 'hektor%%');
  if ko <> 0 then raise exception '⛔ garde : %% dossier(s) n''ont plus des parts IDENTIQUES -- ils lui remontent', ko; end if;
end $$;

-- ── ② LA TABLE DE GARDE (une fois pour le projet ; fermee des sa naissance) ─────────────────────
create table if not exists %(garde)s (
  id                     bigint generated always as identity primary key,
  ancien_app_chaine_id   bigint      not null,      -- LE NUMERO DU DOSSIER DISPARU (sa regle : on le garde)
  dossier_ou_elle_vit    bigint,                    -- le dossier qui porte les memes parts au moment du geste
  app_chaine_id          bigint      not null,      -- la ligne telle qu'elle etait, colonne pour colonne
  app_dossier_id         bigint,
  cote                   text        not null,
  rang                   smallint    not null,
  hektor_user_id         text        not null,
  nom_au_moment          text,
  pourcentage            numeric     not null,
  origine                text,
  ecrit_le               timestamptz not null,
  ecrit_par              text,
  mise_de_cote_le        timestamptz not null default now(),
  mise_de_cote_par       text        not null,
  pourquoi               text        not null
);
revoke all on %(garde)s from public, anon, authenticated;
alter table %(garde)s enable row level security;

-- ── ③ METTRE DE COTE (%(n_mis)d parts), PUIS RETIRER ──────────────────────────────────────────────────
insert into %(garde)s (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang,
                       hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, v.nouveau, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, %(par)s,
       'dossier disparu ; parts IDENTIQUES a celles du dossier ' || v.nouveau || ' (sa regle du 22/11)'
  from (values
%(liste)s
  ) v(ancien, nouveau, cote, rang)
  join app_affaire_repartition r on r.app_chaine_id = v.ancien and r.cote = v.cote and r.rang = v.rang;
delete from app_affaire_repartition r
 using (values
%(liste)s
 ) v(ancien, nouveau, cote, rang)
 where r.app_chaine_id = v.ancien and r.cote = v.cote and r.rang = v.rang;

-- ── ④ LE CONTROLE, DANS LA MEME TRANSACTION ─────────────────────────────────────────────────────
do $$
declare n int; g int; t int;
begin
  select count(*) into n from app_affaire_repartition;
  if n <> %(n_rep_apres)d then raise exception '⛔ repartitions : %% au lieu de %(n_rep_apres)d', n; end if;
  select count(*) into g from %(garde)s where mise_de_cote_par = %(par)s;
  if g <> %(n_mis)d then raise exception '⛔ table de garde : %% part(s) de ce geste au lieu de %(n_mis)d', g; end if;
  -- TEMOIN POSITIF NOMME : le dossier disparu %(ta)d est dans la garde avec son ancien numero, et plus dans les parts
  select count(*) into t from %(garde)s where mise_de_cote_par = %(par)s and ancien_app_chaine_id = %(ta)d
                                             and dossier_ou_elle_vit = %(tn)d;
  if t = 0 then raise exception '⛔ temoin : le dossier %(ta)d n''est pas dans la garde'; end if;
  select count(*) into t from app_affaire_repartition where app_chaine_id = %(ta)d;
  if t <> 0 then raise exception '⛔ temoin : le dossier %(ta)d porte encore %% part(s)', t; end if;
  -- TEMOIN INVERSE : le dossier d'arrivee %(tn)d garde ses parts
  select count(*) into t from app_affaire_repartition where app_chaine_id = %(tn)d;
  if t = 0 then raise exception '⛔ temoin inverse : le dossier %(tn)d a perdu ses parts'; end if;
  raise notice '✅ %(n_mis)d parts mises de cote avec leur ancien numero ; repartitions %(n_rep)d -> %(n_rep_apres)d ; temoins verts.';
end $$;
""" % {"emp_sql": EMPREINTE, "n_rep": E["n_rep"], "emp": q(E["emp"]), "liste": liste, "garde": GARDE, "n_mis": n_mis,
       "par": q(par_), "n_rep_apres": E["n_rep"] - n_mis, "ta": temoin_a, "tn": temoin_n}
    (SUPA / (stem + ".sql")).write_text(entete + corps + "\ncommit;\n", encoding="utf-8", newline="\n")
    (SUPA / (stem + "_A_BLANC.sql")).write_text(
        entete.replace("-- ⛔ DORMANT", "-- ⭐ REPETITION A BLANC : le patch ENTIER, puis ROLLBACK -- il ne laisse rien.\n-- ⛔ DORMANT")
        + corps + "\nrollback;\n", encoding="utf-8", newline="\n")
    inverse = """-- RETOUR ARRIERE DES ORPHELINES MISES DE COTE (%(etiq)s) -- il ne juge que SA part (lecon 31) : il repose les parts
-- de CE geste, a l'identique, sous leur ancien numero, et ne touche rien d'autre. La table de garde reste (elle est au projet).
begin;
do $$
declare n int;
begin
  select count(*) into n from %(garde)s where mise_de_cote_par = %(par)s;
  if n <> %(n_mis)d then raise exception '⛔ %% part(s) de ce geste dans la garde, attendu %(n_mis)d', n; end if;
  select count(*) into n from %(garde)s g join app_affaire_repartition r
      on r.app_chaine_id = g.app_chaine_id and r.cote = g.cote and r.rang = g.rang where g.mise_de_cote_par = %(par)s;
  if n <> 0 then raise exception '⛔ %% emplacement(s) deja repris -- quelqu''un est passe apres', n; end if;
end $$;
insert into app_affaire_repartition (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage,
                                     origine, ecrit_le, ecrit_par)
select app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par
  from %(garde)s where mise_de_cote_par = %(par)s;
delete from %(garde)s where mise_de_cote_par = %(par)s;
do $$
declare n int; emp text;
begin
  select count(*), %(emp_sql)s into n, emp from app_affaire_repartition;
  if n <> %(n_rep)d or emp <> %(emp)s then raise exception '⛔ inverse : les repartitions ne reviennent pas a l''etat d''avant (%% %%)', n, emp; end if;
  raise notice '✅ %(n_mis)d parts reposees ; repartitions revenues a %(n_rep)d, empreinte d''avant.';
end $$;
commit;
""" % {"etiq": etiquette, "garde": GARDE, "par": q(par_), "n_mis": n_mis, "emp_sql": EMPREINTE, "n_rep": E["n_rep"],
       "emp": q(E["emp"])}
    (SUPA / (stem + "_INVERSE.sql")).write_text(inverse, encoding="utf-8", newline="\n")
    repet = """-- CONTROLE (lecture seule) -- a coller APRES le patch. Chaque ligne doit dire OK.
select 'repartitions' controle, count(*)::text valeur, case when count(*) = %(n_rep_apres)d then 'OK' else 'ROUGE' end from app_affaire_repartition
union all select 'mises de cote par ce geste', count(*)::text, case when count(*) = %(n_mis)d then 'OK' else 'ROUGE' end
  from %(garde)s where mise_de_cote_par = %(par)s
union all select 'orphelines restantes (la vue)', count(*)::text, case when count(*) = %(reste)d then 'OK' else 'ROUGE' end
  from app_v_repartition_orpheline
union all select 'temoin : ' || %(ta)s || ' garde son ancien numero', count(*)::text, case when count(*) > 0 then 'OK' else 'ROUGE' end
  from %(garde)s where mise_de_cote_par = %(par)s and ancien_app_chaine_id = %(ta)s;
""" % {"n_rep_apres": E["n_rep"] - n_mis, "n_mis": n_mis, "garde": GARDE, "par": q(par_),
       "reste": E["n_vue"] - n_mis, "ta": temoin_a}
    (SUPA / (stem + "_REPETITION.sql")).write_text(repet, encoding="utf-8", newline="\n")
    print("PATCH : supabase/%s.sql (+ _A_BLANC, _INVERSE, _REPETITION) -- %d parts mises de cote, %d dossiers remontent"
          % (stem, n_mis, len(differentes)))
    return 0


def blanc(etiquette: str) -> int:
    stem = "patch_repartitions_orphelines_mises_de_cote_%s" % etiquette
    texte = (SUPA / (stem + "_A_BLANC.sql")).read_text(encoding="utf-8")
    assert texte.rstrip().endswith("rollback;") and "\ncommit;" not in texte, "le fichier a blanc porte un commit"
    corps = texte.split("begin;", 1)[1].rsplit("rollback;", 1)[0]
    avant = lire_etat()
    cn = connexion()
    cn.autocommit = False
    cu = cn.cursor()
    try:
        cu.execute(corps)
        verdict = "le patch est passe JUSQU'AU BOUT (garde, table de garde, mise de cote, controle) ; %s" % [
            x.strip() for x in cn.notices][-1:]
    except Exception as e:  # noqa: BLE001
        verdict = "⛔ le patch S'EST ARRETE : %s" % str(e).splitlines()[0]
    finally:
        cn.rollback()
        cn.close()
    apres = lire_etat()
    intact = (apres["n_vue"], apres["n_rep"], apres["emp"], apres["garde_absente"]) == (
        avant["n_vue"], avant["n_rep"], avant["emp"], True)
    print("A BLANC : %s" % verdict)
    print("   ⭐ TEMOIN : apres le rollback, orphelines %d, repartitions %d, empreinte %s, table de garde absente %s -> %s"
          % (apres["n_vue"], apres["n_rep"], apres["emp"], apres["garde_absente"],
             "RIEN N'EST RESTE" if intact else "⛔ QUELQUE CHOSE EST RESTE"))
    return 0 if intact and "JUSQU'AU BOUT" in verdict else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("etape", choices=["fabriquer", "blanc", "lire", "essais"])
    ap.add_argument("--etiquette")
    a = ap.parse_args()
    if a.etape == "essais":
        sys.exit(essais())
    if a.etape == "lire":
        sys.exit(lire())
    if not a.etiquette:
        ap.error("--etiquette est exige pour fabriquer et blanc")
    sys.exit(fabriquer(a.etiquette) if a.etape == "fabriquer" else blanc(a.etiquette))
