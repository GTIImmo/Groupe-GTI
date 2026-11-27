"""LE PATCH DES 42 (24/11, son 4e mot : « LE GO PORTE SUR R26 ET LES 42 REVISES ») -- fabrique les fichiers SQL.

SON MOT : « Sauvegarde datee avant le geste . l'ancienne place au journal pour chacun des 42 . l'inverse pret (garde ton
empreinte 0038d306, elle doit revenir). » -- « ta regle "chaque ecriture garde SA LIGNE D'ORIGINE" n'est pas portee par ton
fichier des 42 : il donne l'ancienne PLACE (la transaction), pas la LIGNE du classeur. Au geste reel je veux LES DEUX
ecrites. » -- « les 4 qui restent (11138, 4496, 3701, 21551) : tes lectures me vont, mais elles restent NOMMEES au journal. »

ENTREE : le journal complet du temps 1 avec R26 (protocole_realignement_temps1_a_blanc_2026-11-24.py --r26 --csv, dans le
dossier de travail, jamais en notice) + le fichier des anomalies (la classe et la raison de chaque ecriture).
SORTIE (supabase/) : le PATCH, son A_BLANC (le meme corps, sans commit, qui finit par une erreur voulue), l'INVERSE, l'INVERSE
A BLANC, la REPETITION.

⛔ AUCUN TEXTE DE NOTE N'ENTRE DANS UN FICHIER : une note se designe par sa piece et l'empreinte md5 de son texte (le texte
peut porter un nom qui ne doit jamais etre ecrit sur un document).

USAGE : python -X utf8 phase2/checks/realignement_42_generer_patch_2026-11-24.py [--avant <md5>] [--apres <md5>]
  --avant / --apres : l'empreinte SQL des lignes touchees, mesuree en lecture seule (avant) et rendue par l'A_BLANC (apres) ;
  le patch les EXIGE (sinon il s'arrete) -- sans elles, il ne les exige pas et le dit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path


class T(str):
    """Un gabarit SQL : `%(nom)s` / `%(nom)d` remplaces par nom, et `%s` (une seule valeur) ; les `%` NUS du SQL (les
    messages de `raise`) restent tels quels ; `%%` -> `%`."""

    def __mod__(self, m):
        if isinstance(m, dict):
            out = re.sub(r"%\((\w+)\)([sd])", lambda mo: str(m[mo.group(1)]) if mo.group(2) == "s" else "%d" % m[mo.group(1)],
                         str(self))
        else:
            out = str(self).replace("%s", str(m), 1)
        return out.replace("%%", "%")

RACINE = Path(r"C:\Hektor\Projet")
JOURNAL = Path(r"C:\Hektor\chantier_classeur_q6_cache\protocole\realignement_temps1_journal_passage_79_avec_r26_2026-11-24.json")
ANOMALIES = RACINE / "notice" / "PROTOCOLE_REALIGNEMENT_TEMPS1_LES_ANOMALIES_PASSAGE_79_AVEC_R26_2026-11-24.csv"
SORTIE = RACINE / "supabase"
NOM = "patch_realignement_42_ecritures_2026-11-24"
LOT = "realignement_42_2026-11-24"
NOMS = {"vente_reglee_app": "Vente Reglee", "numero_facture_app": "Numero de facture", "date_annulation_app": "Annulee",
        "motif_annulation_app": "le motif (F)", "honoraires_entree_app": "Commission TTC (honoraires_entree_app)",
        "note": "les notes (F / G)"}      # les noms du temps 1 (son fichier des anomalies)

ap = argparse.ArgumentParser()
ap.add_argument("--avant")
ap.add_argument("--apres")
a = ap.parse_args()

J = json.loads(JOURNAL.read_text(encoding="utf-8"))
assert J["r26"] and J["passage"] == 79 and len(J["gestes"]) == 42 and len(J["nommees"]) == 4, "journal inattendu"
assert J["empreintes"][0][:8] == "0038d306" and J["empreintes"][2] == J["empreintes"][0], "empreinte inattendue"
ANO = {}
for x in csv.DictReader(open(ANOMALIES, encoding="utf-8-sig"), delimiter=";"):
    ANO[(x["colonne"], x["cle (piece / ligne / mandat)"])] = x
loc = sqlite3.connect("file:C:/Hektor/Projet/phase2/phase2.sqlite?mode=ro", uri=True)
NOTE = {int(r[0]): (r[1], hashlib.md5((r[2] or "").encode("utf-8")).hexdigest(), len(r[2] or ""))
        for r in loc.execute("select app_affaire_id, origine, texte from app_affaire_note")}


def q(s):
    return "null" if s is None else "'" + str(s).replace("'", "''") + "'"


G = J["gestes"]
N = J["nommees"]
LEDGER = [g for g in G if g["famille"] != "note"]
NOTES = [g for g in G if g["famille"] == "note"]
ids_ledger = sorted({g["de"] for g in LEDGER} | {g["vers"] for g in LEDGER if g["vers"]})
ids_notes = sorted({g["de"] for g in NOTES} | {g["vers"] for g in NOTES})
ids_nommees = sorted({n["de"] for n in N})
TOUS = sorted(set(ids_ledger) | set(ids_notes) | set(ids_nommees))
SRC_N = {g["de"] for g in NOTES}
assert len(SRC_N) == len(NOTES) and len({g["vers"] for g in NOTES}) == len(NOTES), "deux notes vers une meme piece"
for g in NOTES:     # chaque cible est libre, ou liberee par le meme geste (l'echange 27195 <-> 27196, la suite 27141 -> 27134)
    assert g["vers"] not in NOTE or g["vers"] in SRC_N, "la note %d marcherait sur %d" % (g["de"], g["vers"])
    assert NOTE[g["de"]][0] == g["valeur"][0], "origine de la note %d" % g["de"]


def ligne_journal(n, g, geste, pourquoi):
    fam = g["famille"]
    col = "texte (app_affaire_note)" if fam == "note" else fam
    val = None if fam == "note" else g["valeur"]
    return "(%d, %s, %s, %s, %d, %s, %s, %s, %s, %s, %s)" % (
        n, q(fam), q(col), q(geste), g["de"], "null" if not g.get("vers") else str(g["vers"]), q(val), q(g["ligne"]),
        "null" if g.get("num") is None else str(int(g["num"])), q(g["lot"]), q(pourquoi))


rows_j = []
for k, g in enumerate(G, 1):
    x = ANO[(NOMS[g["famille"]], str(g["de"]))]
    assert x["decision proposee"] == g["geste"], "decision du fichier des anomalies pour %s %s" % (g["famille"], g["de"])
    pq = "%s ; %s" % (x["classe"], x["raison"])
    rows_j.append(ligne_journal(k, g, g["geste"], pq[:900]))
for k, n_ in enumerate(N, len(G) + 1):
    g = {"famille": n_["famille"], "de": n_["de"], "vers": None,
         "valeur": n_["valeur"] if n_["famille"] != "note" else None, "ligne": n_["ligne"], "num": n_["num"],
         "lot": n_["lot"]}
    rows_j.append(ligne_journal(k, g, "NOMMEE (laissee en place)", ("%s ; %s ; %s" % (
        n_["classe"], n_["decision"], n_["raison"]))[:900]))

ID_TOUS = ", ".join(map(str, TOUS))
EMPREINTE = """(select md5(coalesce((select string_agg(concat_ws('|', l.app_affaire_id, l.vente_reglee_app, l.numero_facture_app,
         l.date_annulation_app, l.motif_annulation_app, l.honoraires_entree_app), ';' order by l.app_affaire_id)
    from public.app_affaire_ledger l where l.app_affaire_id in (%s)), '') || '#' ||
  coalesce((select string_agg(concat_ws('|', n.app_affaire_id, n.origine, md5(n.texte), n.app_dossier_id, n.app_chaine_id,
         n.ecrit_par), ';' order by n.app_affaire_id)
    from public.app_affaire_note n where abs(n.app_affaire_id) in (%s)), '')))""" % (ID_TOUS, ID_TOUS)

# ── LES GARDES : chaque source porte EXACTEMENT ce qu'on a mesure, chaque cible est libre ──────────────────────────────
v_ledger_src = ",\n    ".join("(%d, %s, %s)" % (g["de"], q(g["famille"]), q(g["valeur"])) for g in LEDGER)
v_ledger_cib = ",\n    ".join("(%d, %s)" % (g["vers"], q(g["famille"])) for g in LEDGER if g["vers"])
v_notes = ",\n    ".join("(%d, %d, %s, %s)" % (g["de"], g["vers"], q(NOTE[g["de"]][0]), q(NOTE[g["de"]][1])) for g in NOTES)
v_nommees = ",\n    ".join("(%d, %s, %s)" % (n_["de"], q(n_["famille"]),
                                            q(NOTE[n_["de"]][1] if n_["famille"] == "note" else n_["valeur"])) for n_ in N)
n_src = len(LEDGER)
n_cib = sum(1 for g in LEDGER if g["vers"])
n_cote = sum(1 for g in LEDGER if g["geste"] == "METTRE DE COTE")
COLS = ("date_annulation_app", "motif_annulation_app", "honoraires_entree_app", "vente_reglee_app", "numero_facture_app")


def val_col(alias="l"):
    return "case v.famille %s end" % " ".join("when '%s' then %s.%s" % (c, alias, c) for c in COLS)


GARDES = T("""
-- ─── ① LES GARDES : l'etat d'avant, EXIGE ecriture par ecriture -- sinon RIEN n'est ecrit ─────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_ledger_avant_realignement_20261124') is not null
     or to_regclass('public.app_affaire_note_avant_realignement_20261124') is not null then
    raise exception '⛔ garde : la sauvegarde datee existe deja -- ce patch ne se rejoue pas';
  end if;
  if to_regclass('public.app_classeur_realignement_journal') is not null then
    execute 'select count(*) from public.app_classeur_realignement_journal where lot = $1' into n using '%(lot)s';
    if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal -- ce patch ne se rejoue pas', n; end if;
  end if;
  -- les %(n_src)d ecritures du registre qui partent : chacune porte EXACTEMENT sa valeur mesuree
  select count(*) into n from public.app_affaire_ledger l
    join (values
    %(v_ledger_src)s) v(id, famille, valeur) on l.app_affaire_id = v.id
   where %(val_col)s = v.valeur;
  if n <> %(n_src)d then raise exception '⛔ garde : % ecriture(s) du registre a leur place mesuree sur %(n_src)d', n; end if;
  -- leurs %(n_cib)d cibles : la case est VIDE
  select count(*) into n from public.app_affaire_ledger l
    join (values
    %(v_ledger_cib)s) v(id, famille) on l.app_affaire_id = v.id
   where %(val_col)s is null;
  if n <> %(n_cib)d then raise exception '⛔ garde : % cible(s) vide(s) sur %(n_cib)d', n; end if;
  -- les %(n_notes)d notes qui partent : leur origine et l'empreinte de leur texte ; leurs cibles : libres, ou liberees par le
  --   meme geste (l'echange 27195 <-> 27196, la suite 27141 -> 27134 -> 27140)
  select count(*) into n from public.app_affaire_note t
    join (values
    %(v_notes)s) v(de, vers, origine, empreinte) on t.app_affaire_id = v.de
   where t.origine = v.origine and md5(t.texte) = v.empreinte;
  if n <> %(n_notes)d then raise exception '⛔ garde : % note(s) telles que mesurees sur %(n_notes)d', n; end if;
  select count(*) into n from public.app_affaire_note t
   where t.app_affaire_id in (%(cib_notes)s) and t.app_affaire_id not in (%(src_notes)s);
  if n <> 0 then raise exception '⛔ garde : % cible(s) de note deja occupee(s)', n; end if;
  select count(*) into n from public.app_affaire_note t where t.app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ garde : % note(s) a un numero negatif (un geste interrompu ?)', n; end if;
  -- les 4 NOMMEES : a leur place, telles que mesurees (elles ne bougent pas, elles sont ecrites au journal)
  select count(*) into n from (values
    %(v_nommees)s) v(id, famille, valeur)
   where (v.famille = 'note' and exists (select 1 from public.app_affaire_note t where t.app_affaire_id = v.id
                                          and md5(t.texte) = v.valeur))
      or (v.famille <> 'note' and exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = v.id
                                          and %(val_col)s = v.valeur));
  if n <> 4 then raise exception '⛔ garde : % nommee(s) a leur place sur 4', n; end if;
  e := %(empreinte)s;
  %(garde_avant)s
  raise notice '✅ gardes : %(n_src)d ecritures du registre, %(n_cib)d cibles vides, %(n_notes)d notes, 4 nommees ; empreinte des lignes touchees %%', e;
end $$;
""") % {"lot": LOT, "n_src": n_src, "v_ledger_src": v_ledger_src, "val_col": val_col("l"), "n_cib": n_cib,
       "v_ledger_cib": v_ledger_cib, "n_notes": len(NOTES), "v_notes": v_notes,
       "cib_notes": ", ".join(str(g["vers"]) for g in NOTES), "src_notes": ", ".join(str(g["de"]) for g in NOTES),
       "v_nommees": v_nommees, "empreinte": EMPREINTE,
       "garde_avant": ("if e <> '%s' then raise exception '⛔ garde : empreinte des lignes touchees %% au lieu de %s "
                       "(mesuree en lecture seule)', e; end if;" % (a.avant, a.avant)) if a.avant else
       "-- (empreinte d'avant non exigee : fichier fabrique sans --avant)"}

CORPS = GARDES + T("""
-- ─── ② LA SAUVEGARDE DATEE : les lignes ENTIERES, sources, cibles et nommees (%(n_tous)d pieces) ──────────────────────
create table public.app_affaire_ledger_avant_realignement_20261124 as
  select * from public.app_affaire_ledger where app_affaire_id in (%(ids)s);
create table public.app_affaire_note_avant_realignement_20261124 as
  select * from public.app_affaire_note where app_affaire_id in (%(ids)s);
revoke all on public.app_affaire_ledger_avant_realignement_20261124 from public, anon, authenticated;
revoke all on public.app_affaire_note_avant_realignement_20261124 from public, anon, authenticated;

-- ─── ③ LE JOURNAL (permanent) : pour chaque ecriture, SES DEUX CLES -- l'ancienne PLACE (la transaction, sa chaine, son
--   dossier) ET la LIGNE D'ORIGINE (id_unique, son numero au Sheet, son lot). C'est aussi LA que vivent les 5 dates MISES
--   DE COTE (regle 6 : on ne supprime pas, on met de cote avec son ancienne place). Les 4 nommees y sont, sans geste. ────
create table if not exists public.app_classeur_realignement_journal (
  lot                   text   not null,
  n                     int    not null,
  famille               text   not null,
  colonne               text   not null,
  geste                 text   not null,
  de_app_affaire_id     bigint not null,
  de_kind               text,
  de_app_chaine_id      bigint,
  de_dossier_numero     text,
  de_dossier_uuid       uuid,
  vers_app_affaire_id   bigint,
  vers_kind             text,
  vers_app_chaine_id    bigint,
  vers_dossier_numero   text,
  valeur                text,
  note_origine          text,
  note_md5              text,
  note_longueur         int,
  note_app_dossier_id   bigint,
  note_app_chaine_id    bigint,
  ligne_origine         text,
  ligne_origine_num     int,
  lot_origine           text,
  pourquoi              text   not null,
  ecrit_le              timestamptz not null default now(),
  ecrit_par             text   not null,
  primary key (lot, n)
);
revoke all on public.app_classeur_realignement_journal from public, anon, authenticated;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, note_origine, note_md5, note_longueur,
   note_app_dossier_id, note_app_chaine_id, ligne_origine, ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, v.famille, v.colonne, v.geste, v.de, d.kind, d.app_chaine_id, d.app_dossier_numero, d.app_dossier_uuid,
       v.vers, c.kind, c.app_chaine_id, c.app_dossier_numero, v.valeur, t.origine, md5(t.texte), length(t.texte),
       t.app_dossier_id, t.app_chaine_id, v.ligne, v.num, v.lot_origine, v.pourquoi, '%(nom)s'
  from (values
    %(rows_j)s
  ) v(n, famille, colonne, geste, de, vers, valeur, ligne, num, lot_origine, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.de
  left join public.app_affaire_ledger c on c.app_affaire_id = v.vers
  left join public.app_affaire_note t on t.app_affaire_id = v.de and v.famille = 'note';

-- ─── ④ LE GESTE, SIMULTANE : toutes les ecritures qui partent sont retirees, PUIS posees ───────────────────────────────
-- le registre : on vide d'abord les %(n_src)d sources (dont les %(n_cote)d dates MISES DE COTE, qui vivent au journal)...
%(vider)s
-- ... puis on pose les %(n_cib)d cibles, la valeur LUE AU JOURNAL (jamais retapee)
%(poser)s
-- les notes : la cle (app_affaire_id) est primaire -> deux temps, pour l'echange : un numero NEGATIF de passage, puis la
--   cible ; le reflet (app_dossier_id, app_chaine_id) suit la transaction qui recoit la note
update public.app_affaire_note set app_affaire_id = -app_affaire_id where app_affaire_id in (%(src_notes)s);
update public.app_affaire_note t
   set app_affaire_id = j.vers_app_affaire_id, app_dossier_id = c.app_dossier_id, app_chaine_id = c.app_chaine_id
  from public.app_classeur_realignement_journal j
  join public.app_affaire_ledger c on c.app_affaire_id = j.vers_app_affaire_id
 where j.lot = '%(lot)s' and j.famille = 'note' and j.geste = 'DEPLACER' and t.app_affaire_id = -j.de_app_affaire_id;

-- ─── ⑤ LES CONTROLES, DANS LA MEME TRANSACTION -- ils jugent LEUR part, et ils ARRETENT ────────────────────────────────
do $$
declare n int; m int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> %(n_j)d then raise exception '⛔ controle : % ligne(s) au journal au lieu de %(n_j)d', n; end if;
  -- ⭐ SA RESERVE : les DEUX cles ecrites pour chacune des 42 (la place ET la ligne d'origine)
  select count(*) into n from public.app_classeur_realignement_journal
   where lot = '%(lot)s' and geste <> 'NOMMEE (laissee en place)'
     and de_app_chaine_id is not null and ligne_origine is not null and ligne_origine_num is not null and lot_origine is not null;
  if n <> 42 then raise exception '⛔ controle : % des 42 portent leurs deux cles', n; end if;
  -- les notes : chacune sur sa cible, meme texte (md5), meme origine, reflet de la cible ; aucune a un numero negatif
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_affaire_note t on t.app_affaire_id = j.vers_app_affaire_id
    join public.app_affaire_ledger c on c.app_affaire_id = j.vers_app_affaire_id
   where j.lot = '%(lot)s' and j.famille = 'note' and md5(t.texte) = j.note_md5 and t.origine = j.note_origine
     and t.app_chaine_id is not distinct from c.app_chaine_id and t.app_dossier_id is not distinct from c.app_dossier_id;
  if n <> %(n_notes)d then raise exception '⛔ controle : % note(s) sur leur cible sur %(n_notes)d', n; end if;
  select count(*) into n from public.app_affaire_note where app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ controle : % note(s) restee(s) a un numero negatif', n; end if;
  select count(*) into n from public.app_affaire_note
   where app_affaire_id in (%(src_seules)s);
  if n <> 0 then raise exception '⛔ controle : % source(s) de note encore occupee(s)', n; end if;
  -- le registre : chaque cible porte la valeur du journal ; chaque source qui n'est pas une cible est vide
  select count(*) into n from public.app_classeur_realignement_journal v
    join public.app_affaire_ledger x on x.app_affaire_id = v.vers_app_affaire_id
   where v.lot = '%(lot)s' and v.famille <> 'note' and v.geste = 'DEPLACER' and %(val_col)s = v.valeur;
  if n <> %(n_cib)d then raise exception '⛔ controle : % cible(s) du registre posee(s) sur %(n_cib)d', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal v
    join public.app_affaire_ledger x on x.app_affaire_id = v.de_app_affaire_id
   where v.lot = '%(lot)s' and v.famille <> 'note' and v.geste in ('DEPLACER', 'METTRE DE COTE') and %(val_col)s is null;
  if n <> %(n_src)d then raise exception '⛔ controle : % source(s) du registre videe(s) sur %(n_src)d', n; end if;
  -- ⭐ LES 5 MISES DE COTE : leur valeur et leur ancienne place vivent au journal
  select count(*) into n from public.app_classeur_realignement_journal
   where lot = '%(lot)s' and geste = 'METTRE DE COTE' and valeur is not null and vers_app_affaire_id is null
     and de_app_chaine_id is not null;
  if n <> %(n_cote)d then raise exception '⛔ controle : % mise(s) de cote gardee(s) sur %(n_cote)d', n; end if;
  -- les 4 NOMMEES : intactes
  select count(*) into n from (values
    %(v_nommees)s) v(id, famille, valeur)
   where (v.famille = 'note' and exists (select 1 from public.app_affaire_note t where t.app_affaire_id = v.id
                                          and md5(t.texte) = v.valeur))
      or (v.famille <> 'note' and exists (select 1 from public.app_affaire_ledger l where l.app_affaire_id = v.id
                                          and %(val_col_l)s = v.valeur));
  if n <> 4 then raise exception '⛔ controle : % nommee(s) intacte(s) sur 4', n; end if;
  -- la conservation : rien ne se perd -- les notes ne changent pas de nombre, les dates d'annulation perdent les 5 mises de
  --   cote (elles sont au journal), le reste ne change pas de nombre
  select count(*) into n from public.app_affaire_note_avant_realignement_20261124;
  select count(*) into m from public.app_affaire_note where app_affaire_id in (%(ids)s);
  if n <> m then raise exception '⛔ controle : notes des pieces touchees % avant, % apres', n, m; end if;
  select count(*) into n from public.app_affaire_ledger_avant_realignement_20261124 where date_annulation_app is not null;
  select count(*) into m from public.app_affaire_ledger where app_affaire_id in (%(ids)s) and date_annulation_app is not null;
  if n - %(n_cote)d <> m then raise exception '⛔ controle : dates d''annulation % avant, % apres (attendu -%(n_cote)d)', n, m; end if;
  e := %(empreinte)s;
  %(garde_apres)s
  raise notice '✅ %(n_j)d lignes au journal (42 gestes + 4 nommees, les deux cles) . %(n_notes)d notes sur leur cible . '
    '%(n_cib)d cibles du registre posees . %(n_src)d sources videes dont %(n_cote)d mises de cote au journal . 4 nommees intactes . '
    'conservation BOUCLE . empreinte apres %%', e;
end $$;
""") % {"n_tous": len(TOUS), "ids": ID_TOUS, "lot": LOT, "nom": NOM, "rows_j": ",\n    ".join(rows_j),
       "n_src": n_src, "n_cote": n_cote, "n_cib": n_cib, "n_notes": len(NOTES), "n_j": len(rows_j),
       "src_notes": ", ".join(str(g["de"]) for g in NOTES),
       "src_seules": ", ".join(str(g["de"]) for g in NOTES if g["de"] not in {h["vers"] for h in NOTES}),
       "vider": "\n".join("update public.app_affaire_ledger set %s = null where app_affaire_id = %d and %s = %s;" % (
           g["famille"], g["de"], g["famille"], q(g["valeur"])) for g in LEDGER),
       "poser": "\n".join(
           "update public.app_affaire_ledger set %(f)s = (select valeur from public.app_classeur_realignement_journal "
           "where lot = '%(lot)s' and n = %(n)d) where app_affaire_id = %(v)d and %(f)s is null;" % {
               "f": g["famille"], "lot": LOT, "n": G.index(g) + 1, "v": g["vers"]} for g in LEDGER if g["vers"]),
       "val_col": val_col("x"), "val_col_l": val_col("l"), "v_nommees": v_nommees,
       "empreinte": EMPREINTE,
       "garde_apres": ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s (celle de "
                       "l''A_BLANC)', e; end if;" % (a.apres, a.apres)) if a.apres else
       "-- (empreinte d'apres non exigee : fichier fabrique sans --apres)"}

ENTETE = """-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- LE REALIGNEMENT DES ECRITURES RAPATRIEES -- LES 42 GESTES DU TEMPS 1 (passage 79, AVEC R26)              24/11/2026
-- Genere par phase2/checks/realignement_42_generer_patch_2026-11-24.py
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- SON GO (24/11, 4e mot) : « LE GO PORTE SUR R26 ET LES 42 REVISES, dans TON ordre : R26 -> les 42 -> A2 -> le retrait des
--   exclusions de E dans la MEME nuit que la vague. Sauvegarde datee avant le geste . l'ancienne place au journal pour
--   chacun des 42 . l'inverse pret (garde ton empreinte 0038d306, elle doit revenir). »
--   ⭐ « Au geste reel je veux LES DEUX ecrites » (la place ET la ligne d'origine) ; « les 4 qui restent (11138, 4496, 3701,
--   21551) [...] restent NOMMEES au journal ».
--
-- CE QUE CE PATCH FAIT (%(n_notes)d notes, %(n_src)d ecritures du registre) :
--   . DEPLACER : 31 notes, 4 motifs, la date 16377 -> 16378, la commission 28568 -> 28569 = 37 deplacements ;
--   . METTRE DE COTE : 5 dates d'annulation (4385, 17387, 24450, 27134, 27195) -- SA REGLE du 24/11 : la bonne piece
--     n'existe pas (leur ligne n'a qu'une offre) ; « je ne veux pas qu'une date d'annulation reste affichee sur le
--     compromis d'une autre affaire : a l'ecran, ca ment ». Leur valeur et leur ancienne place vivent au JOURNAL ;
--   . les 4 NOMMEES : ecrites au journal, sans geste.
--
-- ⛔ CE QUE CE PATCH NE FAIT PAS : aucune piece creee ni supprimee, aucune chaine ni etiquette touchee, aucune part de
--   repartition (c'est A2, plus tard), RIEN chez Hektor : date_annulation_app, motif_annulation_app, honoraires_entree_app
--   sont dans COLONNES_QUE_LE_PUSH_N_ENVOIE_PAS (phase2/sync/affaire_ledger.py) -- le push ne les envoie pas, le run ne les
--   ecrase pas ; app_affaire_note n'est ecrite que par l'app (app_affaire_note_ecrire) et par nos lots, jamais par la nuit.
--   Aucun declencheur : sur le registre, le seul declencheur de mise a jour (app_affaire_partie_apres_update) ne regarde
--   aucune de ces colonnes ; sur les notes, aucun (mesure du 24/11).
--
-- ⭐ L'ETAT D'AVANT EST CELUI DU CONTROLE : le temps 1 rejoue CHEZ SUPABASE (lecture seule, 24/11 apres-midi) rend
--   l'empreinte 0038d306, la meme que la copie locale ; avec le geste, 46 mal placees -> 4, toutes nommees.
--
-- Retour arriere : %(nom)s_INVERSE.sql      Controle : %(nom)s_REPETITION.sql
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
""" % {"n_notes": len(NOTES), "n_src": n_src, "nom": NOM}

(SORTIE / (NOM + ".sql")).write_text(ENTETE + "\nbegin;\n" + CORPS + "\ncommit;\n", encoding="utf-8")
(SORTIE / (NOM + "_A_BLANC.sql")).write_text(
    ENTETE.replace("LES 42 GESTES DU TEMPS 1", "A BLANC -- LES 42 GESTES DU TEMPS 1") +
    "-- ⛔ A BLANC : LE MEME CORPS, SANS AUCUN COMMIT ; IL FINIT PAR UNE ERREUR VOULUE -> TOUT EST ANNULE.\n\nbegin;\n" + CORPS +
    T("""
do $$
declare e text;
begin
  e := %s;
  raise exception 'A BLANC VERT : toutes les gardes et tous les controles sont passes ; empreinte apres = % -- RIEN N''EST ECRIT (erreur voulue)', e;
end $$;
""") % EMPREINTE, encoding="utf-8")

# ── L'INVERSE : il repose chaque ecriture a son ancienne place, depuis la SAUVEGARDE (la valeur et le reflet d'origine) ──
INV = T("""
-- ─── ① LES GARDES : le geste est la, entier ─────────────────────────────────────────────────────────────────────────────
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> %(n_j)d then raise exception '⛔ garde : % ligne(s) du lot au journal au lieu de %(n_j)d', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_affaire_note t on t.app_affaire_id = j.vers_app_affaire_id
   where j.lot = '%(lot)s' and j.famille = 'note' and md5(t.texte) = j.note_md5;
  if n <> %(n_notes)d then raise exception '⛔ garde : % note(s) deplacee(s) retrouvee(s) sur %(n_notes)d', n; end if;
  select count(*) into n from public.app_affaire_note where app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ garde : % note(s) a un numero negatif', n; end if;
end $$;

-- ─── ② LE RETOUR, SIMULTANE ────────────────────────────────────────────────────────────────────────────────────────────
-- le registre : vider les cibles (seulement si elles portent ENCORE la valeur posee), puis reposer chaque source
update public.app_affaire_ledger x set %(set_null)s
  from public.app_classeur_realignement_journal v
 where v.lot = '%(lot)s' and v.famille <> 'note' and v.geste = 'DEPLACER' and x.app_affaire_id = v.vers_app_affaire_id
   and %(val_col)s = v.valeur;
%(reposer)s
-- les notes : numero negatif de passage, puis l'ancienne place, avec le reflet d'ORIGINE (lu dans la sauvegarde)
update public.app_affaire_note t set app_affaire_id = -t.app_affaire_id
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.famille = 'note' and t.app_affaire_id = j.vers_app_affaire_id and md5(t.texte) = j.note_md5;
update public.app_affaire_note t
   set app_affaire_id = s.app_affaire_id, app_dossier_id = s.app_dossier_id, app_chaine_id = s.app_chaine_id
  from public.app_classeur_realignement_journal j
  join public.app_affaire_note_avant_realignement_20261124 s on s.app_affaire_id = j.de_app_affaire_id
 where j.lot = '%(lot)s' and j.famille = 'note' and t.app_affaire_id = -j.vers_app_affaire_id;

-- ─── ③ LE CONTROLE : chaque piece touchee redevient EXACTEMENT sa sauvegarde (registre ET notes) ──────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_ledger_avant_realignement_20261124 s
    join public.app_affaire_ledger x using (app_affaire_id)
   where (x.date_annulation_app, x.motif_annulation_app, x.honoraires_entree_app, x.vente_reglee_app, x.numero_facture_app)
         is distinct from
         (s.date_annulation_app, s.motif_annulation_app, s.honoraires_entree_app, s.vente_reglee_app, s.numero_facture_app);
  if n <> 0 then raise exception '⛔ controle : % ligne(s) du registre differente(s) de leur sauvegarde', n; end if;
  select count(*) into n from (
    (select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note_avant_realignement_20261124
     except select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note
     where app_affaire_id in (%(ids)s))
    union all
    (select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note
     where app_affaire_id in (%(ids)s)
     except select app_affaire_id, origine, md5(texte), app_dossier_id, app_chaine_id from public.app_affaire_note_avant_realignement_20261124)) d;
  if n <> 0 then raise exception '⛔ controle : % note(s) differente(s) de leur sauvegarde', n; end if;
  select count(*) into n from public.app_affaire_note where app_affaire_id < 0;
  if n <> 0 then raise exception '⛔ controle : % note(s) restee(s) a un numero negatif', n; end if;
  e := %(empreinte)s;
  %(garde_avant)s
  raise notice '✅ chaque piece touchee est revenue a sa sauvegarde ; empreinte %%', e;
end $$;
""") % {"lot": LOT, "n_j": len(rows_j), "n_notes": len(NOTES), "ids": ID_TOUS, "empreinte": EMPREINTE,
       "set_null": ", ".join("%s = case when v.famille = '%s' then null else x.%s end" % (c, c, c) for c in COLS[:3]),
       "val_col": val_col("x"),
       "reposer": "\n".join("update public.app_affaire_ledger set %s = s.%s from public.app_affaire_ledger_avant_realignement_20261124 s "
                            "where s.app_affaire_id = %d and public.app_affaire_ledger.app_affaire_id = %d and "
                            "public.app_affaire_ledger.%s is null;" % (g["famille"], g["famille"], g["de"], g["de"], g["famille"])
                            for g in LEDGER),
       "garde_avant": ("if e <> '%s' then raise exception '⛔ controle : empreinte %% au lieu de %s (celle d''AVANT le "
                       "geste)', e; end if;" % (a.avant, a.avant)) if a.avant else "-- (empreinte d'avant non exigee)"}

ENTETE_INV = """-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- RETOUR ARRIERE DE %(nom)s.sql
-- Il repose chaque ecriture a son ancienne place depuis la SAUVEGARDE DATEE (valeur ET reflet d'origine), et EXIGE que
--   chaque piece touchee redevienne exactement sa sauvegarde, et l'empreinte des lignes touchees celle d'AVANT le geste.
-- ⭐ « un retour arriere ne juge que SA part » : il ne touche que les %(n_tous)d pieces du lot.
-- Il NE retire PAS le journal ni les sauvegardes : ils restent la trace (le journal porte le lot ; un nouveau geste du
--   meme lot est refuse par la garde du patch tant qu'on n'a pas vide le journal du lot, a la main, sur decision).
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
""" % {"nom": NOM, "n_tous": len(TOUS)}
(SORTIE / (NOM + "_INVERSE.sql")).write_text(ENTETE_INV + "\nbegin;\n" + INV + "\ncommit;\n", encoding="utf-8")
(SORTIE / (NOM + "_INVERSE_A_BLANC.sql")).write_text(
    ENTETE_INV + "-- ⛔ A BLANC : SANS COMMIT ; IL FINIT PAR UNE ERREUR VOULUE -> TOUT EST ANNULE.\n\nbegin;\n" + INV + T("""
do $$
declare e text;
begin
  e := %s;
  raise exception 'INVERSE A BLANC VERT : chaque piece touchee revient a sa sauvegarde ; empreinte = % -- RIEN N''EST ECRIT (erreur voulue)', e;
end $$;
""") % EMPREINTE, encoding="utf-8")

REP = T("""-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
-- %(nom)s -- LES CONTROLES, REJOUABLES. AUCUNE ECRITURE.
-- ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
select 'lignes au journal (42 gestes + 4 nommees)' as controle, count(*)::text as mesure, '%(n_j)d' as attendu
  from public.app_classeur_realignement_journal where lot = '%(lot)s'
union all
select 'les 42 portent LEURS DEUX CLES (place + ligne d''origine)', count(*)::text, '42'
  from public.app_classeur_realignement_journal where lot = '%(lot)s' and geste <> 'NOMMEE (laissee en place)'
   and de_app_chaine_id is not null and ligne_origine is not null and ligne_origine_num is not null
union all
select 'par geste : ' || geste, count(*)::text, case geste when 'DEPLACER' then '37' when 'METTRE DE COTE' then '5' else '4' end
  from public.app_classeur_realignement_journal where lot = '%(lot)s' group by geste
union all
select 'notes sur leur cible (meme texte)', count(*)::text, '%(n_notes)d'
  from public.app_classeur_realignement_journal j join public.app_affaire_note t on t.app_affaire_id = j.vers_app_affaire_id
 where j.lot = '%(lot)s' and j.famille = 'note' and md5(t.texte) = j.note_md5
union all
select 'notes a un numero negatif', count(*)::text, '0' from public.app_affaire_note where app_affaire_id < 0
union all
select 'cibles du registre posees', count(*)::text, '%(n_cib)d'
  from public.app_classeur_realignement_journal v join public.app_affaire_ledger x on x.app_affaire_id = v.vers_app_affaire_id
 where v.lot = '%(lot)s' and v.famille <> 'note' and v.geste = 'DEPLACER' and %(val_col)s = v.valeur
union all
select 'sources du registre videes (dont 5 mises de cote)', count(*)::text, '%(n_src)d'
  from public.app_classeur_realignement_journal v join public.app_affaire_ledger x on x.app_affaire_id = v.de_app_affaire_id
 where v.lot = '%(lot)s' and v.famille <> 'note' and v.geste in ('DEPLACER', 'METTRE DE COTE') and %(val_col)s is null
union all
select 'les sauvegardes datees existent (registre, notes)',
       ((to_regclass('public.app_affaire_ledger_avant_realignement_20261124') is not null)::int
        + (to_regclass('public.app_affaire_note_avant_realignement_20261124') is not null)::int)::text, '2'
union all
select 'empreinte des lignes touchees', %(empreinte)s, '%(apres)s'
order by 1;
""") % {"nom": NOM, "n_j": len(rows_j), "lot": LOT, "n_notes": len(NOTES), "n_cib": n_cib, "n_src": n_src,
       "val_col": val_col("x"), "empreinte": EMPREINTE, "apres": a.apres or "(celle de l'A_BLANC)"}
(SORTIE / (NOM + "_REPETITION.sql")).write_text(REP, encoding="utf-8")
(SORTIE / (NOM + "_EMPREINTE_LECTURE.sql")).write_text("select %s as empreinte_des_lignes_touchees;\n" % EMPREINTE,
                                                       encoding="utf-8")
for f in sorted(SORTIE.glob(NOM + "*.sql")):
    t = f.read_text(encoding="utf-8")
    print("%-80s %6d octets ; commit %d" % (f.name, len(t.encode()), t.count("\ncommit;")))
print("%d pieces touchees : %s" % (len(TOUS), ID_TOUS))
