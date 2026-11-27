"""LES 47 (+2), FAMILLE 1 : LES VENTES REGLEES OU TOUT CONCORDE -- LE PATCH, SON A BLANC, SON INVERSE, SA REPETITION (27/11).

SON MOT DU 27/11 : « Fini ce qui etait prevu ». Le prevu (procedure, 25/11 « ④ La methode des 47 (+2) ») : 1) les 8 ventes
reglees qui concordent ; 2) les 7 dont seul le Prix du Sheet est fautif ; 3) les 23 dates posables -- chacune a son accord.

LA MESURE DU 27/11 (les_47_valeurs_jamais_posees_2026-11-25.py au passage 82, image 2026-11-26_094931 ;
notice/CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-27_PASSAGE_82.csv) : les 47 du 25/11, inchangees, + 9Q0FHAKK (vente 3650,
tout concorde : ses « +2 », vente reglee et facture). FAMILLE 1 = 9 ventes : les 8 du 25/11 + 9Q0FHAKK. Toutes sur une chaine
dont les parts sont du classeur (protegees), aucune sur un dossier deja regle.

LE JUGE NE LIT PAS CES DEUX COLONNES (protocole_classeur.py : « jamais nos recopies de son Sheet (vente_reglee_app,
numero_facture_app : circulaires) ») -- les poser ne nourrit pas sa preuve (la regle du 25/11).

LA VALEUR, MOT POUR MOT, comme C8 le 16/11 : la case « Vente Réglée » et la case « Numéro de facture », sans les espaces du bord,
lues dans l'image du 82 ET exigees identiques dans le Sheet du jour (un GET).

LE GESTE : seulement sur des cases VIDES ; la sauvegarde datee des 9 lignes (cle primaire, RLS) ; le journal (2 lignes par vente,
la ligne d'origine et son numero) ; les autres colonnes INTACTES ; l'empreinte d'apres exigee.
USAGE : python -X utf8 phase2/checks/ventes_reglees_famille1_generer_patch_2026-11-27.py [--empreinte-apres MD5]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parents[1]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(RACINE))
sys.stdout.reconfigure(encoding="utf-8")
import protocole_classeur as P  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--empreinte-apres", default="")
arg = ap.parse_args()
LOT, TAB = "ventes_reglees_famille1_2026-11-27", "app_affaire_ledger_avant_ventes_reglees_f1_20261127"
OUT = RACINE / "supabase"
MESURE = RACINE / "notice" / "CLASSEUR_LES_47_VALEURS_JAMAIS_POSEES_2026-11-27_PASSAGE_82.csv"
IMAGE = "2026-11-26_094931"
FAMILLE1 = ["9Q0FHAKK", "a6d41ca1", "8f3a4326", "a56ce827", "84c91bb8", "AYIHPHF5", "d9a0630c", "ef08b63a", "LWZL8V5M"]

# ─── 1. LA MESURE DU JOUR : les 9 sont « VRAIE VENTE REGLEE (tout concorde) », et ce sont les seules ─────────────────────
with MESURE.open(encoding="utf-8") as h:
    m = [r for r in csv.DictReader(h, delimiter=";") if r["quoi"] == "VENTE_REGLEE"]
concordent = [r for r in m if r["verdict"] == "VRAIE VENTE REGLEE (tout concorde)"]
assert sorted(r["id_unique"] for r in concordent) == sorted(FAMILLE1), sorted(r["id_unique"] for r in concordent)
LIGNES = sorted(((r["id_unique"], int(r["ligne"]), int(r["piece"]), r["dossier"]) for r in concordent), key=lambda x: x[1])

# ─── 2. LES VALEURS, MOT POUR MOT : l'image du 82, puis le Sheet du jour (un GET) qui doit dire la meme chose ────────────
I = P.Image(P.IMAGES / IMAGE)
D = I.D
VAL = {}
for i, num, piece, dossier in LIGNES:
    VAL[i] = (D.case(i, "Vente Réglée").strip(), D.case(i, "Numéro de facture").strip())
    assert VAL[i][0] and VAL[i][1], (i, VAL[i])
import apparier_classeur as ac  # noqa: E402

ac.load_env_file(RACINE / ".env")
entete, lignes = ac.lire_classeur()
k = {c: entete.index(c) for c in ("Etat Actuel", "Vente Réglée", "Numéro de facture")}
du_jour = {}
for num, l in lignes:
    l = [("" if x is None else str(x)) for x in list(l)] + [""] * 40
    if l[37].strip() in VAL:
        du_jour.setdefault(l[37].strip(), []).append((num, l[k["Etat Actuel"]].strip(), l[k["Vente Réglée"]].strip(),
                                                      l[k["Numéro de facture"]].strip()))
for i, num, piece, dossier in LIGNES:
    assert len(du_jour.get(i, [])) == 1, (i, du_jour.get(i))
    n_, etat_, reg_, fac_ = du_jour[i][0]
    assert (n_, etat_, reg_, fac_) == (num, "Vente réglée", VAL[i][0], VAL[i][1]), (i, du_jour[i], num, VAL[i])
print("les 9 valeurs : l'image du 82 = le Sheet du jour, ligne et etat compris")
for i, num, piece, dossier in LIGNES:
    print("  %-9s ligne %-5d piece %-6d %-11s reglee %r ; facture %r" % (i, num, piece, dossier, VAL[i][0], VAL[i][1]))

# ─── 3. SUPABASE, LECTURE SEULE : l'etat exact que les gardes exigeront ───────────────────────────────────────────────
ids = ", ".join(str(x[2]) for x in LIGNES)
EMP = ("md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, "
       "coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(date_annulation_app, '-'), "
       "coalesce(motif_annulation_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) "
       "from public.app_affaire_ledger where app_affaire_id in (%s)" % ids)
N_VR = "(select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '')"
N_NF = "(select count(*) from public.app_affaire_ledger where coalesce(numero_facture_app, '') <> '')"
VR_SANS_PART = ("(select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
                "coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from "
                "public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id))")
VR_SUPPOSEES = ("(select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and "
                "coalesce(l.vente_reglee_app, '') <> '' and exists (select 1 from public.app_affaire_repartition r where "
                "r.app_chaine_id = l.app_chaine_id) and not exists (select 1 from public.app_affaire_repartition r where "
                "r.app_chaine_id = l.app_chaine_id and coalesce(r.origine, '') not like 'hektor%%'))")
cn, cu = P.pooler()
cu.execute("select app_affaire_id, kind, app_dossier_numero, app_chaine_id, coalesce(vente_reglee_app, ''), "
           "coalesce(numero_facture_app, '') from public.app_affaire_ledger where app_affaire_id in (%s)" % ids)
etat = {r[0]: r[1:] for r in cu.fetchall()}
cu.execute("select app_chaine_id, count(*), count(*) filter (where coalesce(origine, '') like 'hektor%%') from "
           "public.app_affaire_repartition where app_chaine_id in (select app_chaine_id from public.app_affaire_ledger where "
           "app_affaire_id in (%s)) group by 1" % ids)
parts = {r[0]: r[1:] for r in cu.fetchall()}
cu.execute("select app_chaine_id from public.app_affaire_ledger where kind = 'vente' and coalesce(vente_reglee_app, '') <> '' "
           "and app_chaine_id in (select app_chaine_id from public.app_affaire_ledger where app_affaire_id in (%s))" % ids)
deja = [r[0] for r in cu.fetchall()]
cu.execute("select %s, %s, %s, %s, (select %s)" % (N_VR, N_NF, VR_SANS_PART, VR_SUPPOSEES.replace("%%", "%"), EMP))
n_vr, n_nf, vr_sans_part, vr_supposees, e_avant = cu.fetchone()
cu.execute("select count(*) from public.app_classeur_realignement_journal where lot = %s", (LOT,))
au_journal = cu.fetchone()[0]
cu.execute("select to_regclass(%s) is not null", ("public." + TAB,))
tab_existe = cu.fetchone()[0]
cn.rollback()
cn.close()
for i, num, piece, dossier in LIGNES:
    kind, numero, ch, vr, nf = etat[piece]
    assert (kind, numero, vr, nf) == ("vente", dossier, "", ""), (i, piece, etat[piece])
    assert ch in parts and parts[ch][1] == 0, (i, piece, ch, parts.get(ch))
assert not deja, deja
assert au_journal == 0 and not tab_existe and vr_sans_part == 0, (au_journal, tab_existe, vr_sans_part)
print("registre : %d ventes reglees, %d factures ; vente reglee sans part %d ; reglees sur supposition seule %d ; 9 lignes %s" % (
    n_vr, n_nf, vr_sans_part, vr_supposees, e_avant))


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


POURQUOI = ("SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son "
            "classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne")
val = []
n = 0
for i, num, piece, dossier in LIGNES:
    for col, v in (("vente_reglee_app", VAL[i][0]), ("numero_facture_app", VAL[i][1])):
        n += 1
        val.append("(%d, %s, %d, %d, %s, %s, %s)" % (n, q(i), num, piece, q(col), q(v), q(POURQUOI)))
VALEURS = ",\n    ".join(val)
D_ = {"lot": LOT, "tab": TAB, "ids": ids, "emp": EMP, "e_avant": e_avant, "valeurs": VALEURS, "n_vr": n_vr, "n_nf": n_nf,
      "vr_sans_part": VR_SANS_PART, "vr_supposees": VR_SUPPOSEES.replace("%%", "%"), "n_sup": vr_supposees,
      "image": IMAGE, "nl": n}

CORPS = """
-- ─── ① LES GARDES : les 9 ventes telles que lues, leurs deux cases VIDES ──────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.%(tab)s') is not null then raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> 0 then raise exception '⛔ garde : %% ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (%(ids)s) and kind = 'vente'
     and coalesce(vente_reglee_app, '') = '' and coalesce(numero_facture_app, '') = '';
  if n <> 9 then raise exception '⛔ garde : %% vente(s) sur 9 ont leurs deux cases vides', n; end if;
  e := (select %(emp)s);
  if e <> '%(e_avant)s' then raise exception '⛔ garde : les 9 lignes ont change depuis la fabrication (%%)', e; end if;
  if %(n_vr)s <> (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') then
    raise exception '⛔ garde : le nombre de ventes reglees a change depuis la fabrication'; end if;
  raise notice '✅ gardes : 9 ventes, leurs deux cases vides, telles que lues';
end $$;

-- ─── ② LA SAUVEGARDE DATEE des 9 lignes, AVEC la cle primaire et la RLS ───────────────────────────────────────────────
create table public.%(tab)s as select * from public.app_affaire_ledger where app_affaire_id in (%(ids)s);
alter table public.%(tab)s add primary key (app_affaire_id);
revoke all on public.%(tab)s from public, anon, authenticated;
alter table public.%(tab)s enable row level security;

-- ─── ③ LE JOURNAL : chaque case, sa valeur MOT POUR MOT, sa ligne d'origine et son numero ─────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select '%(lot)s', v.n, 'vente_reglee_facture', v.colonne, 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, 'VIDE',
       v.ligne, v.num, 'Sheet, image %(image)s (passage 82) = le Sheet du 27/11, mot pour mot comme C8 le 16/11', v.pourquoi,
       'patch_ventes_reglees_famille1'
  from (values
    %(valeurs)s
  ) v(n, ligne, num, piece, colonne, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : seulement des cases VIDES ───────────────────────────────────────────────────────────────────────────
update public.app_affaire_ledger l set vente_reglee_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.colonne = 'vente_reglee_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.vente_reglee_app, '') = '';
update public.app_affaire_ledger l set numero_facture_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = '%(lot)s' and j.colonne = 'numero_facture_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.numero_facture_app, '') = '';

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l
    on l.app_affaire_id = j.de_app_affaire_id
   where j.lot = '%(lot)s' and j.ligne_origine is not null
     and ((j.colonne = 'vente_reglee_app' and l.vente_reglee_app = j.valeur)
       or (j.colonne = 'numero_facture_app' and l.numero_facture_app = j.valeur));
  if n <> %(nl)s then raise exception '⛔ controle : %% case(s) posee(s) sur %(nl)s', n; end if;
  -- aucune autre colonne des 9 lignes n'a bouge
  select count(*) into n from public.app_affaire_ledger l join public.%(tab)s s using (app_affaire_id)
   where (l.kind, l.state, l.app_chaine_id, l.app_dossier_numero, l.date_annulation_app, l.motif_annulation_app,
          l.honoraires_entree_app, l.montant, l.honoraires_entree)
         is distinct from (s.kind, s.state, s.app_chaine_id, s.app_dossier_numero, s.date_annulation_app, s.motif_annulation_app,
                           s.honoraires_entree_app, s.montant, s.honoraires_entree);
  if n <> 0 then raise exception '⛔ controle : %% ligne(s) ont bouge hors de leurs deux cases', n; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') <> %(n_vr)s + 9 then
    raise exception '⛔ controle : le nombre de ventes reglees n''est pas %(n_vr)s + 9'; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(numero_facture_app, '') <> '') <> %(n_nf)s + 9 then
    raise exception '⛔ controle : le nombre de factures n''est pas %(n_nf)s + 9'; end if;
  if %(vr_sans_part)s <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  if %(vr_supposees)s <> %(n_sup)s then raise exception '⛔ controle : une vente reglee de plus sur des parts supposees seulement'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = '%(lot)s';
  if n <> %(nl)s then raise exception '⛔ controle : %% ligne(s) au journal sur %(nl)s', n; end if;
  e := (select %(emp)s);
  %(apres)s
  raise notice '✅ 9 ventes reglees et leurs 9 factures posees sur des cases vides ; le reste des lignes intact ; empreinte apres %%', e;
end $$;
"""
INVERSE = """
-- ─── L'INVERSE : les 18 cases remises a vide (seulement si elles portent encore la valeur du lot), le journal retire ───
update public.app_affaire_ledger l set vente_reglee_app = s.vente_reglee_app
  from public.%(tab)s s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = '%(lot)s' and j.colonne = 'vente_reglee_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.vente_reglee_app = j.valeur;
update public.app_affaire_ledger l set numero_facture_app = s.numero_facture_app
  from public.%(tab)s s, public.app_classeur_realignement_journal j
 where s.app_affaire_id = l.app_affaire_id and j.lot = '%(lot)s' and j.colonne = 'numero_facture_app'
   and j.de_app_affaire_id = l.app_affaire_id and l.numero_facture_app = j.valeur;
delete from public.app_classeur_realignement_journal where lot = '%(lot)s';
do $$
begin
  if (select %(emp)s) <> '%(e_avant)s' then raise exception '⛔ inverse : les 9 lignes ne sont pas revenues a la sauvegarde'; end if;
  raise notice '✅ inverse : les 18 cases revenues a la sauvegarde, le journal du lot vide';
end $$;
"""
reel = ("if e <> '%s' then raise exception '⛔ controle : empreinte apres %% au lieu de %s', e; end if;" % (
    arg.empreinte_apres, arg.empreinte_apres) if arg.empreinte_apres else
    "raise exception '⛔ le patch reel exige l''empreinte d''apres rendue par l''essai a blanc (--empreinte-apres)';")
ent = "-- %s -- genere par phase2/checks/ventes_reglees_famille1_generer_patch_2026-11-27.py (son mot du 27/11)\n"
DETAIL = ("(select string_agg(app_affaire_id || '=' || coalesce(vente_reglee_app, '-') || ' / ' || coalesce(numero_facture_app, "
          "'-'), ' ; ' order by app_affaire_id) from public.app_affaire_ledger where app_affaire_id in (%s))" % ids)
F = {
    "patch_ventes_reglees_famille1_2026-11-27.sql": ent % "patch_ventes_reglees_famille1_2026-11-27"
    + "-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql\n\nbegin;\n" + CORPS % dict(D_, apres=reel)
    + "\ncommit;\n",
    "patch_ventes_reglees_famille1_2026-11-27_A_BLANC.sql": ent % "A BLANC -- ⛔ aucun commit, une erreur VOULUE annule tout"
    + "\nbegin;\n" + CORPS % dict(D_, apres="null;")
    + "\ncreate temporary table v_milieu on commit drop as select (select %s) e, %s d, %s nvr;\n" % (EMP, DETAIL, N_VR)
    + INVERSE % D_ + """
do $$
declare m record;
begin
  select * into m from v_milieu;
  raise exception 'A BLANC VENTES REGLEES F1 VERT -- RIEN N''EST ECRIT. Apres le geste : %%%% ventes reglees ; %%%% ; empreinte apres %%%%. Apres l''inverse : = avant (%s).', m.nvr, m.d, m.e;
end $$;
""".replace("%%%%", "%%") % e_avant[:8],
    "patch_ventes_reglees_famille1_2026-11-27_INVERSE.sql": ent % "INVERSE" + "\nbegin;\n" + INVERSE % D_ + "\ncommit;\n",
    "patch_ventes_reglees_famille1_2026-11-27_REPETITION.sql": ent % "REPETITION (lecture seule)" + (
        "select %s as les_9_ventes,\n"
        "  (select count(*) from public.app_classeur_realignement_journal where lot = '%s') as journal_attendu_%d,\n"
        "  %s as ventes_reglees_sans_part_attendu_0,\n  %s as reglees_sur_supposition_seule_attendu_%d,\n"
        "  (select %s) as empreinte_apres;\n" % (DETAIL, LOT, n, VR_SANS_PART, VR_SUPPOSEES.replace("%%", "%"), vr_supposees, EMP)),
}
for nom, txt in F.items():
    p_ = OUT / nom
    p_.write_bytes(txt.encode("utf-8"))
    print("-> supabase/%s (%d octets, md5 %s)" % (nom, p_.stat().st_size, hashlib.md5(p_.read_bytes()).hexdigest()[:8]))
print("empreinte d'avant des 9 lignes : %s ; ventes reglees %d, factures %d" % (e_avant, n_vr, n_nf))
