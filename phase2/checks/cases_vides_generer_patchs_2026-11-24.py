"""LES CASES VIDES (24/11, son 5e mot) -- fabrique les patchs de la famille ① (la Charge) et des 6 dates d'annulation.

SON MOT : « ① LES 20 CHARGES QUE NOTRE CARNET N'A PAS -> ON PREND LE SHEET, LES 20. Case vide = pas d'ecrasement [...] Parmi
elles 5 VENTES REGLEES, 32 000 EUR de commission : celles-la d'abord. Elles s'ecrivent sur le MANDAT (app_mandat_champ_app),
pas sur l'affaire. » -- « les 6 dates d'annulation dont l'etrangere est partie ce matin : POSE LA LEUR sur LEUR compromis quand
il n'en a pas. » -- « A chaque famille : a blanc, puis le geste avec ses empreintes, puis la repetition, puis l'inverse joue a
blanc. Sauvegarde datee. Et la ligne d'origine sur chaque ecriture. » -- « Rien ne s'ecrit sans mon accord sur le patch. »

⛔ CE QUE LA MESURE A TROUVE, ET QUI N'EST PAS DANS CES PATCHS (nomme, a lui) : deux mandats portent DEUX lignes du Sheet qui se
CONTREDISENT (46338/17322 : cc33cc38 « Vendeur », vente reglee, contre afd672fa « Acquereur », annulee ; 47174/17639 :
df0ce30c « Acquereur », vente reglee, contre 2c2566d7 « Vendeur », annulee). La charge vit sur le MANDAT : une seule valeur. On
ne choisit pas a sa place -> 16 mandats ecrits, 2 nommes.

SORTIES (supabase/) : pour chaque lot, le PATCH, son ALLER_RETOUR_A_BLANC (le patch puis son inverse dans la MEME transaction,
qui exige le retour a l'empreinte d'avant et finit par une erreur voulue : rien n'est ecrit), l'INVERSE, la REPETITION, et
l'EMPREINTE_LECTURE.
USAGE : python -X utf8 phase2/checks/cases_vides_generer_patchs_2026-11-24.py [--avant LOT=md5 ...] [--apres LOT=md5 ...]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

SORTIE = Path(r"C:\Hektor\Projet\supabase")
JOURNAL = "public.app_classeur_realignement_journal"


class T(str):
    def __mod__(self, m):
        out = re.sub(r"%\((\w+)\)([sd])", lambda mo: str(m[mo.group(1)]) if mo.group(2) == "s" else "%d" % m[mo.group(1)],
                     str(self))
        return out.replace("%%", "%")


def q(s):
    return "null" if s is None else "'" + str(s).replace("'", "''") + "'"


ap = argparse.ArgumentParser()
ap.add_argument("--avant", nargs="*", default=[])
ap.add_argument("--apres", nargs="*", default=[])
a = ap.parse_args()
AVANT = dict(x.split("=") for x in a.avant)
APRES = dict(x.split("=") for x in a.apres)

# ── ① LA CHARGE : (ligne, n° au Sheet, piece qui porte le mandat, annonce, mandat, valeur, etat de la ligne, commission) ──
#   mesure du 24/11 (image du passage 79, carnet et registre lus CHEZ SUPABASE : carnet VIDE, reflet VIDE, 1 mandat par annonce)
CHARGE_1A = [  # les 3 VENTES REGLEES sans contradiction (les 2 autres reglees sont sur les mandats contredits)
    ("125888d3", 4211, 23986, "47542", "17840", "acquereur", "Vente reglee", 9000),
    ("5YUGE9KA", 3, 11134, "23297", "17564", "acquereur", "Vente reglee", 5000),
    ("78004641", 4550, 30778, "17548", "17481", "acquereur", "Vente reglee", 7000),
]
CHARGE_1B = [
    ("1eec6575", 4799, 30825, "63490", "18999", "vendeur", "Compromis en attente", 3500),
    ("2b924f5f", 4498, 28633, "59164", "18127", "vendeur", "Annulee", 3000),
    ("4cbc128d", 4492, 28687, "59339", "18143", "vendeur", "Annulee", 6790),
    ("54376c72", 4801, 30830, "54734", "18053", "acquereur", "Offre d'achat", 1800),
    ("55b49232", 4804, 30837, "17597", "18973", "vendeur", "Offre d'achat", 5699),
    ("5e4c8881", 4797, 30820, "62336", "18648", "vendeur", "Compromis en attente", 6900),
    ("70740f2f", 4800, 30824, "62766", "18773", "vendeur", "Offre d'achat", 4800),
    ("729ba8dc", 4306, 6103, "11695", "17296", "vendeur", "Annulee", 6130),
    ("b43e76f5", 4798, 30826, "59637", "18286", "acquereur", "Offre d'achat", 10000),
    ("b72db9d5", 4803, 30836, "62934", "18950", "vendeur", "Offre d'achat", 4000),
    ("b7439331", 4791, 30809, "63299", "18942", "vendeur", "Offre d'achat", 1000),
    ("f90b0418", 4455, 19049, "39684", "17987", "acquereur", "Annulee", 7000),
    ("ffcf30e6", 4802, 30829, "61893", "18996", "vendeur", "Offre d'achat", 8500),
]
# ── LES 6 DATES : (ligne, n° au Sheet, son compromis, la date de son Sheet, la date du compromis chez Hektor) ──────────
DATES = [
    ("TR42PT5H", 173, 27195, "2025-05-20", "2025-01-24"),
    ("U0GQ3KTO", 3713, 4385, "2022-11-22", "0000-00-00"),
    ("IEYXREWQ", 3530, 27134, "2024-02-01", "0000-00-00"),
    ("R0JRVFDC", 4014, 16377, "2021-01-21", "2020-10-27"),
    ("S3HOG6UL", 3864, 17387, "2021-10-21", "2021-11-03"),   # ⚠ ANTERIEURE au compromis (la regle de C3 l'ecarterait)
    ("6U5DQQ4J", 3865, 24450, "2021-10-21", "2021-10-28"),   # ⚠ ANTERIEURE au compromis (la regle de C3 l'ecarterait)
]


def lot_charge(nom, lignes, titre):
    keys = ", ".join("(%s, %s)" % (q(x[3]), q(x[4])) for x in lignes)
    annonces = sorted({x[3] for x in lignes})
    empreinte = ("(select md5(coalesce(string_agg(concat_ws('|', m.annonce, m.numero, coalesce(k.valeur_app, '-'), "
                 "coalesce(k.origine, '-'), coalesce(k.ecrit_par, '-'), coalesce(r.mandat_charge_honoraires_app, '-')), ';' "
                 "order by m.annonce, m.numero), '')) from (values %s) m(annonce, numero) "
                 "left join public.app_mandat_champ_app k on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero "
                 "and k.champ = 'charge_commission' left join public.app_mandat_register_current r "
                 "on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero)" % keys)
    valeurs = ",\n    ".join("(%d, %s, %d, %s, %s, %s, %s, %s)" % (
        k, q(x[0]), x[1], "null" if x[2] is None else str(x[2]), q(x[3]), q(x[4]), q(x[5]),
        q("%s ; etat au Sheet : %s ; Commission TTC %s EUR" % (titre, x[6], x[7]))) for k, x in enumerate(lignes, 1))
    n = len(lignes)
    m = {"lot": nom, "tab": nom.replace("-", ""), "n": n, "keys": keys, "valeurs": valeurs, "empreinte": empreinte, "nom": "patch_" + nom,
         "annonces": ", ".join(q(x) for x in annonces),
         "repose": "\n".join("select public.app_reposer_charge_mandat_app(%s, 10000);" % q(x) for x in annonces),
         "garde_avant": ("if e <> '%s' then raise exception '⛔ garde : empreinte %% au lieu de %s', e; end if;" % (
             AVANT[nom], AVANT[nom])) if nom in AVANT else "-- (empreinte d'avant non exigee)",
         "garde_apres": ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
             APRES[nom], APRES[nom])) if nom in APRES else "-- (empreinte d'apres non exigee)"}
    gardes = T("""
-- ─── ① LES GARDES : chaque mandat est VIDE au carnet et au reflet, et il existe au registre ────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_mandat_register_current_avant_%(tab)s') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  if to_regclass('public.app_classeur_realignement_journal') is null then
    raise exception '⛔ garde : le journal du realignement n''existe pas (patch des 42 d''abord)';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_mandat_champ_app k join (values %(keys)s) m(annonce, numero)
      on k.hektor_annonce_id = m.annonce and k.numero_mandat = m.numero and k.champ = 'charge_commission';
  if n <> 0 then raise exception '⛔ garde : % mandat(s) portent DEJA une charge au carnet -- on n''ecrase jamais', n; end if;
  select count(*) into n from public.app_mandat_register_current r join (values %(keys)s) m(annonce, numero)
      on r.hektor_annonce_id::text = m.annonce and r.numero_mandat::text = m.numero
   where nullif(btrim(coalesce(r.mandat_charge_honoraires_app, '')), '') is null;
  if n <> %(n)d then raise exception '⛔ garde : % mandat(s) au registre avec un reflet vide sur %(n)d', n; end if;
  select count(*) into n from public.app_mandat_register_current r where r.hektor_annonce_id::text in (%(annonces)s);
  if n <> %(n)d then raise exception '⛔ garde : les annonces portent % mandat(s) au registre au lieu de %(n)d', n; end if;
  e := %(empreinte)s;
  %(garde_avant)s
  raise notice '✅ gardes : %(n)d mandats vides au carnet et au reflet ; empreinte %%', e;
end $$;
""") % m
    aller = T("""
-- ─── ② LA SAUVEGARDE DATEE : les lignes du registre des mandats de ces annonces (le reflet) ──────────────────────────────
create table public.app_mandat_register_current_avant_%(tab)s as
  select * from public.app_mandat_register_current where hektor_annonce_id::text in (%(annonces)s);
revoke all on public.app_mandat_register_current_avant_%(tab)s from public, anon, authenticated;

-- ─── ③ LE JOURNAL : chaque ecriture avec SA LIGNE D'ORIGINE (id_unique, n° au Sheet) et SA PLACE (le mandat) ──────────
alter table public.app_classeur_realignement_journal add column if not exists mandat_annonce text;
alter table public.app_classeur_realignement_journal add column if not exists mandat_numero text;
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, valeur, ligne_origine, ligne_origine_num, lot_origine, pourquoi, ecrit_par, mandat_annonce, mandat_numero)
select '%(lot)s', v.n, 'charge_commission', 'app_mandat_champ_app.valeur_app (charge_commission)', 'POSER (case vide)',
       v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, d.app_dossier_uuid, null, v.valeur, v.ligne, v.num,
       'Sheet (colonne Charge Commission) -- son 5e mot du 24/11', v.pourquoi, '%(nom)s', v.annonce, v.numero
  from (values
    %(valeurs)s
  ) v(n, ligne, num, piece, annonce, numero, valeur, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : le carnet (la valeur LUE AU JOURNAL), puis le reflet, annonce par annonce (jamais tout le registre) ────
insert into public.app_mandat_champ_app (hektor_annonce_id, numero_mandat, champ, valeur_app, origine, ecrit_par, ecrit_le)
select j.mandat_annonce, j.mandat_numero, 'charge_commission', j.valeur, 'classeur', 'classeur:' || j.ligne_origine, now()
  from public.app_classeur_realignement_journal j where j.lot = '%(lot)s'
on conflict (hektor_annonce_id, numero_mandat, champ) do nothing;
%(repose)s

-- ─── ⑤ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_champ_app k on k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
     and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur'
     and k.ecrit_par = 'classeur:' || j.ligne_origine
   where j.lot = '%(lot)s';
  if n <> %(n)d then raise exception '⛔ controle : % charge(s) au carnet sur %(n)d', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_register_current r on r.hektor_annonce_id::text = j.mandat_annonce and r.numero_mandat::text = j.mandat_numero
     and r.mandat_charge_honoraires_app = j.valeur
   where j.lot = '%(lot)s';
  if n <> %(n)d then raise exception '⛔ controle : % reflet(s) pose(s) sur %(n)d', n; end if;
  -- rien d'autre n'a bouge dans le registre de ces annonces
  select count(*) into n from public.app_mandat_register_current r
    join public.app_mandat_register_current_avant_%(tab)s s
      on s.hektor_annonce_id = r.hektor_annonce_id and s.numero_mandat = r.numero_mandat
   where r.mandat_charge_honoraires_app is distinct from s.mandat_charge_honoraires_app
     and (r.hektor_annonce_id::text, r.numero_mandat::text) not in (select mandat_annonce, mandat_numero
                                                                   from public.app_classeur_realignement_journal where lot = '%(lot)s');
  if n <> 0 then raise exception '⛔ controle : % autre(s) reflet(s) ont bouge', n; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s' and ligne_origine is not null and ligne_origine_num is not null;
  if n <> %(n)d then raise exception '⛔ controle : % ligne(s) d''origine au journal sur %(n)d', n; end if;
  e := %(empreinte)s;
  %(garde_apres)s
  raise notice '✅ %(n)d charges au carnet, %(n)d reflets, 0 autre reflet, ligne d''origine au journal ; empreinte apres %%', e;
end $$;
""") % m
    retour = T("""
-- ─── LE RETOUR : retirer du carnet CE QUE CE LOT A POSE (et seulement cela), reposer le reflet ; le journal et la sauvegarde restent
do $$
declare n int;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_mandat_champ_app k on k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
     and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur' and k.ecrit_par = 'classeur:' || j.ligne_origine
   where j.lot = '%(lot)s';
  if n <> %(n)d then raise exception '⛔ garde du retour : % charge(s) du lot retrouvee(s) sur %(n)d (une saisie est passee ?)', n; end if;
end $$;
delete from public.app_mandat_champ_app k using public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and k.hektor_annonce_id = j.mandat_annonce and k.numero_mandat = j.mandat_numero
   and k.champ = 'charge_commission' and k.valeur_app = j.valeur and k.origine = 'classeur' and k.ecrit_par = 'classeur:' || j.ligne_origine;
%(repose)s
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_mandat_register_current r
    join public.app_mandat_register_current_avant_%(tab)s s on s.hektor_annonce_id = r.hektor_annonce_id and s.numero_mandat = r.numero_mandat
   where r.mandat_charge_honoraires_app is distinct from s.mandat_charge_honoraires_app;
  if n <> 0 then raise exception '⛔ controle du retour : % reflet(s) differents de la sauvegarde', n; end if;
  e := %(empreinte)s;
  %(garde_avant_retour)s
end $$;
""") % dict(m, garde_avant_retour=("if e <> '%s' then raise exception '⛔ controle du retour : empreinte %% au lieu de %s "
                                    "(celle d''AVANT)', e; end if;" % (AVANT[nom], AVANT[nom])) if nom in AVANT
                                   else "raise notice 'empreinte du retour %', e;")
    return gardes, aller, retour, empreinte, m


def lot_dates(nom):
    ids = ", ".join(str(x[2]) for x in DATES)
    empreinte = ("(select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, coalesce(date_annulation_app, '-')), "
                 "';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (%s))" % ids)
    valeurs = ",\n    ".join("(%d, %s, %d, %d, %s, %s)" % (
        k, q(x[0]), x[1], x[2], q(x[3]), q("sa regle du 24/11 (5e mot) : « POSE LA LEUR sur LEUR compromis quand il n'en a "
                                            "pas » ; la date etrangere en est partie le 24/11 (geste des 42) ; compromis du %s%s"
                                            % (x[4], " -- ⚠ la date du Sheet est ANTERIEURE au compromis (la regle de C3 "
                                               "l'ecarterait)" if x[4][:4] != "0000" and x[3] < x[4] else "")))
        for k, x in enumerate(DATES, 1))
    n = len(DATES)
    m = {"lot": nom, "tab": nom.replace("-", ""), "n": n, "ids": ids, "valeurs": valeurs, "empreinte": empreinte, "nom": "patch_" + nom,
         "garde_avant": ("if e <> '%s' then raise exception '⛔ garde : empreinte %% au lieu de %s', e; end if;" % (
             AVANT[nom], AVANT[nom])) if nom in AVANT else "-- (empreinte d'avant non exigee)",
         "garde_apres": ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
             APRES[nom], APRES[nom])) if nom in APRES else "-- (empreinte d'apres non exigee)",
         "garde_avant_retour": ("if e <> '%s' then raise exception '⛔ controle du retour : empreinte %% au lieu de %s', e; "
                                "end if;" % (AVANT[nom], AVANT[nom])) if nom in AVANT else "raise notice 'retour %', e;"}
    gardes = T("""
-- ─── ① LES GARDES : 6 compromis ANNULES, sans date d'annulation ──────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_ledger_avant_%(tab)s') is not null then
    raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas';
  end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger
   where app_affaire_id in (%(ids)s) and kind = 'compromis' and state = 'cancelled' and date_annulation_app is null;
  if n <> %(n)d then raise exception '⛔ garde : % compromis annule(s) sans date sur %(n)d', n; end if;
  e := %(empreinte)s;
  %(garde_avant)s
  raise notice '✅ gardes : %(n)d compromis annules, sans date ; empreinte %%', e;
end $$;
""") % m
    aller = T("""
-- ─── ② LA SAUVEGARDE DATEE : les 6 lignes entieres ────────────────────────────────────────────────────────────────────────
create table public.app_affaire_ledger_avant_%(tab)s as
  select * from public.app_affaire_ledger where app_affaire_id in (%(ids)s);
revoke all on public.app_affaire_ledger_avant_%(tab)s from public, anon, authenticated;

-- ─── ③ LE JOURNAL : la place (le compromis) ET la ligne d'origine (id_unique, n° au Sheet) ──────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ligne_origine, ligne_origine_num,
   lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, 'date_annulation_app', 'date_annulation_app', 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, v.ligne,
       v.num, 'Sheet (colonne Annulee) -- son 5e mot du 24/11', v.pourquoi, '%(nom)s'
  from (values
    %(valeurs)s
  ) v(n, ligne, num, piece, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : la valeur LUE AU JOURNAL, seulement sur une case VIDE ───────────────────────────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app is null;

-- ─── ⑤ LES CONTROLES ─────────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j
    join public.app_affaire_ledger l on l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur
   where j.lot = '%(lot)s' and j.ligne_origine is not null and j.ligne_origine_num is not null;
  if n <> %(n)d then raise exception '⛔ controle : % date(s) posee(s), avec leur ligne d''origine, sur %(n)d', n; end if;
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_%(tab)s s using (app_affaire_id)
   where (l.vente_reglee_app, l.numero_facture_app, l.motif_annulation_app, l.honoraires_entree_app)
         is distinct from (s.vente_reglee_app, s.numero_facture_app, s.motif_annulation_app, s.honoraires_entree_app);
  if n <> 0 then raise exception '⛔ controle : % autre(s) colonne(s) ont bouge', n; end if;
  e := %(empreinte)s;
  %(garde_apres)s
  raise notice '✅ %(n)d dates posees sur leur compromis, ligne d''origine au journal ; empreinte apres %%', e;
end $$;
""") % m
    retour = T("""
-- ─── LE RETOUR : vider ce que ce lot a pose (seulement si la valeur est TOUJOURS la sienne) ──────────────────────────────
update public.app_affaire_ledger l set date_annulation_app = null
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and l.app_affaire_id = j.de_app_affaire_id and l.date_annulation_app = j.valeur;
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_%(tab)s s using (app_affaire_id)
   where l.date_annulation_app is distinct from s.date_annulation_app;
  if n <> 0 then raise exception '⛔ controle du retour : % ligne(s) differente(s) de la sauvegarde', n; end if;
  e := %(empreinte)s;
  %(garde_avant_retour)s
end $$;
""") % m
    return gardes, aller, retour, empreinte, m


ECRITS = []
for nom, (gardes, aller, retour, empreinte, m) in (
        ("charge_1a_reglees_2026-11-24", lot_charge("charge_1a_reglees_2026-11-24", CHARGE_1A,
                                                    "① LES VENTES REGLEES D'ABORD (son 5e mot du 24/11)")),
        ("charge_1b_2026-11-24", lot_charge("charge_1b_2026-11-24", CHARGE_1B, "① les 13 autres (son 5e mot du 24/11)")),
        ("dates_a_l_unite_2026-11-24", lot_dates("dates_a_l_unite_2026-11-24"))):
    base = "patch_" + nom
    entete = ("-- %s -- genere par phase2/checks/cases_vides_generer_patchs_2026-11-24.py (son 5e mot du 24/11 : « rien ne "
              "s'ecrit sans mon accord sur le patch »)\n-- Retour arriere : %s_INVERSE.sql . Controle : %s_REPETITION.sql\n"
              % (base, base, base))
    (SORTIE / (base + ".sql")).write_text(entete + "\nbegin;\n" + gardes + aller + "\ncommit;\n", encoding="utf-8")
    (SORTIE / (base + "_ALLER_RETOUR_A_BLANC.sql")).write_text(
        entete + "-- ⛔ A BLANC : le patch PUIS son inverse, dans la MEME transaction ; aucun commit ; erreur voulue a la fin.\n"
        "\nbegin;\n" + gardes + aller + "\ndo $$ declare e text; begin e := " + empreinte + "; raise notice 'APRES %', e; "
        "perform set_config('ar.apres', e, true); end $$;\n" + retour +
        "\ndo $$ declare e text; begin e := " + empreinte + "; raise exception 'ALLER-RETOUR A BLANC VERT : apres = % ; "
        "retour = % -- RIEN N''EST ECRIT (erreur voulue)', current_setting('ar.apres'), e; end $$;\n", encoding="utf-8")
    (SORTIE / (base + "_INVERSE.sql")).write_text(
        entete + "-- L'INVERSE : il retire ce que le lot a pose, et EXIGE le retour a l'empreinte d'avant. Le journal et la "
        "sauvegarde restent (la trace).\n\nbegin;\n" + retour + "\ncommit;\n", encoding="utf-8")
    (SORTIE / (base + "_EMPREINTE_LECTURE.sql")).write_text("select %s as empreinte;\n" % empreinte, encoding="utf-8")
    (SORTIE / (base + "_REPETITION.sql")).write_text(
        "-- %s -- les controles, rejouables. AUCUNE ECRITURE.\nselect '%s' as lot, (select count(*) from %s where lot = '%s') "
        "as au_journal, %s as empreinte, '%s' as attendue;\n" % (base, nom, JOURNAL, nom, empreinte, APRES.get(nom, "?")),
        encoding="utf-8")
    ECRITS.append(base)
for f in sorted(SORTIE.glob("patch_charge_1*_2026-11-24*.sql")) + sorted(SORTIE.glob("patch_dates_a_l_unite_2026-11-24*.sql")):
    t = f.read_text(encoding="utf-8")
    print("%-75s %6d octets ; commit %d ; jetons non remplaces %d" % (f.name, len(t.encode()), t.count("\ncommit;"),
                                                                     t.count("%(")))
