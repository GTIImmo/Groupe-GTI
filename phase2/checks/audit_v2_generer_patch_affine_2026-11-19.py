# -*- coding: utf-8 -*-
"""AUDIT V2, TEMPS 3 -- LE PATCH AFFINE DE CORRECTION DU GEL (DORMANT). 19/11/2026.

    .venv\\Scripts\\python.exe -X utf8 phase2\\checks\\audit_v2_generer_patch_affine_2026-11-19.py

⛔ LECTURE SEULE : il ECRIT des fichiers (le patch, son inverse, sa repetition, la liste des
  operations), il ne JOUE rien. Le patch produit porte son `commit;` : il ne se joue
  JAMAIS « pour voir ».

PART DU PATCH DE L'AUTRE SESSION (notice/AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv)
ET LUI APPORTE :
  ① CORRECTION 1 (dossier V2, § 8) -- `etage` recoit un LIBELLE COURT ET CONSTANT, et
    `preuves` le COMPTE REEL des familles de preuve du lien (mesure par mon apparieur, pas
    0 : 0 veut deja dire « cree par C5, aucune preuve »). La phrase du juge reste dans le CSV.
  ② CORRECTION 2 -- les 18 lignes a question sortent, avec QJQ9M4OF (indivisible de
    D9MMB7OU), puis EN CASCADE tout ajout ou deplacement dont la cible resterait tenue par
    une ligne sortie. Un retrait seul ne casse jamais l'exclusivite : il reste.
  ③ CORRECTION 3 -- la suite est ENCHAINEE : la liste des valeurs posees par nous sur les
    transactions que le patch detache est produite ici, et la repetition les compte.
  ④ ET CE QUE MON AUDIT AJOUTE : chaque operation gardee est SOUTENUE par mon calcul
    independant (sinon le script s'arrete) ; la garde lit L'EMPREINTE du gel, pas seulement
    son compte (le 19/11, la copie locale avait le bon compte et une autre empreinte).
"""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

RACINE = Path(r"C:\Hektor\Projet")
CK = RACINE / "phase2" / "checks"
N = RACINE / "notice"
T = RACINE / ".tmp" / "audit_v2_2026-11-19"
_spec = importlib.util.spec_from_file_location("apparieur_v2", CK / "audit_v2_apparier_2026-11-19.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

ETIQUETTE = "audit_independant_v2_2026-11-19"        # gele_par : UNIQUE a ce patch (l'inverse s'en sert)
ETAGE = "audits independants 18-19/11"               # ① court et constant
SAUVEGARDE = "app_classeur_lien_avant_audit_v2_20261119"
EMPREINTE = "8084e535f51ba904a839bfe0bcc88a55"        # le gel de Supabase, relu le 19/11
COMPTE = 12787

Q18 = {"D9MMB7OU", "E9GL6MUS", "1D7EIYKW", "5a956cad",                       # le patch tranchait deja
       "EJN79TJ1", "V3FO5NDA", "ZZ5WKMWM", "ea6a28a7",                       # « deja tranchees » par lui
       "9Q0FHAKK", "QXDW8EQA", "I3TFR2KG", "91IHSGNC", "2U5QPKRC", "MQ6H8TVQ",  # « tient quelle que
       "3308P0UX", "87QOXR64", "4G2UHO35", "Z6P7KE5R"}                       #   soit la reponse »
INDIVISIBLES = {"QJQ9M4OF": "indivisible de D9MMB7OU (le retrait de 17366 prejuge la reponse)"}
INCERTAINES = {"5QE9107L", "O6R10ZQA", "RGCEC677", "SHN6RKDI", "T2GZOY5O", "XC761R8Z", "YRUF0S9H", "ZW7MKTWH"}
assert len(Q18) == 18

OPS = list(csv.DictReader(open(N / "AUDIT_INDEPENDANT_CLASSEUR_OPERATIONS_GEL_2026-11-18.csv", encoding="utf-8-sig"), delimiter=";"))
GEL = json.loads((T / "gel_supabase_19-11.json").read_text(encoding="utf-8"))
MOI = {r["id_unique"]: r for r in csv.DictReader(open(N / "AUDIT_INDEPENDANT_V2_MON_APPARIEMENT_2026-11-19.csv", encoding="utf-8-sig"), delimiter=";")}
assert len(OPS) == 141 and len(GEL) == COMPTE

# ── ② LA SORTIE DES LIGNES A QUESTION, PUIS LA CASCADE
gardees, exclues = [], []
for o in OPS:
    if o["id_unique"] in INCERTAINES:
        raise SystemExit("ARRET : le patch d'origine touchait une ligne INCERTAINE (%s)" % o["id_unique"])
    if o["id_unique"] in Q18:
        exclues.append((o, "ligne a question ouverte (sa decision)"))
    elif o["id_unique"] in INDIVISIBLES:
        exclues.append((o, INDIVISIBLES[o["id_unique"]]))
    else:
        gardees.append(o)
while True:
    tenu = {g["app_affaire_id"]: g["id_unique"] for g in GEL}
    for o in gardees:
        if o["de"]:
            tenu.pop(int(o["de"]), None)
    sortir = [(o, "cible %s encore tenue par %s, qui sort du patch" % (o["vers"], tenu[int(o["vers"])]))
              for o in gardees if o["vers"] and int(o["vers"]) in tenu and tenu[int(o["vers"])] != o["id_unique"]]
    if not sortir:
        break
    for o, r in sortir:
        gardees.remove(o)
        exclues.append((o, r))

# ── ④ CHAQUE OPERATION GARDEE DOIT ETRE SOUTENUE PAR MON CALCUL INDEPENDANT
for o in gardees:
    m = MOI[o["id_unique"]][o["role"]]
    m = int(m) if m else None
    if o["de"] and m == int(o["de"]):
        raise SystemExit("ARRET : mon calcul GARDE %s pour %s, le patch le retire" % (o["de"], o["id_unique"]))
    if o["vers"] and m != int(o["vers"]):
        raise SystemExit("ARRET : mon calcul ne donne pas %s a %s" % (o["vers"], o["id_unique"]))

retraits = [(o["id_unique"], int(o["de"]), o["role"]) for o in gardees if o["de"]]
ajouts = [o for o in gardees if o["vers"]]
assert len(set(retraits)) == len(retraits) and len({(o["id_unique"], o["vers"]) for o in ajouts}) == len(ajouts)

# ── ① LE VRAI COMPTE DES FAMILLES DE PREUVE, LIEN PAR LIEN
BIEN = {"LIEN", "MODELO", "MANDAT", "VEND", "VILLE"}


def familles(iu, tid):
    L = A.LIGNE_DE[iu]
    t = A.TX[tid]
    cands = A.candidats_annonces(L)
    r = A.juger_annonce(L, t["annonce"], cands.get(t["annonce"], set()), frozenset())
    f = {x for x in r["fam"] if x in BIEN}
    sc, pr = A.juger_tx(L, t)
    if any("au jour pres" in p or "au jour de l'annulation" in p for p in pr):
        f.add("DATES")
    if any((p.startswith("acquereur ") and "different" not in p) or p.startswith("NOM VOISIN") for p in pr):
        f.add("ACQ")
    if "prix" in pr:
        f.add("PRIX")
    return f


# le rang ACTUEL de la ligne au Sheet (photo du 19/11) -- verifie contre celui du patch
RANG = {L["iu"]: L["rang"] for L in A.LIGNES}
lignes_sql, csv_out, ecarts_rang = [], [], []
for o in ajouts:
    iu, tid = o["id_unique"], int(o["vers"])
    t_kind = A.TX[tid]["k"] if tid in A.TX else None
    if t_kind != o["role"]:
        raise SystemExit("ARRET : la cible %s n'est pas un(e) %s" % (tid, o["role"]))
    f = familles(iu, tid)
    if len(f) < 2:
        raise SystemExit("ARRET : le lien %s -> %s n'a que %d famille(s) de preuve" % (iu, tid, len(f)))
    conf = "sûre" if (o["confiance"] == "certaine" and MOI[iu]["certitude"] == "CERTAINE") else "bonne"
    if o["confiance"] not in ("certaine", "forte"):
        conf = "à valider"
    rang = RANG[iu]
    if str(rang) != str(o["ligne_classeur"]):
        ecarts_rang.append((iu, o["ligne_classeur"], rang))
    lignes_sql.append("    (%d, %d, '%s', '%s', %d, '%s', now(), '%s', '%s')"
                      % (rang, tid, o["role"], conf, len(f), ETAGE, ETIQUETTE, iu))
    csv_out.append({**o, "decision_v2": "GARDEE", "confiance_ecrite": conf, "preuves_ecrites": len(f),
                    "familles": " ".join(sorted(f)), "rang_actuel": rang, "motif_exclusion": ""})
for o in gardees:
    if not o["vers"]:
        csv_out.append({**o, "decision_v2": "GARDEE", "confiance_ecrite": "", "preuves_ecrites": "",
                        "familles": "", "rang_actuel": RANG.get(o["id_unique"], ""), "motif_exclusion": ""})
for o, motif in exclues:
    csv_out.append({**o, "decision_v2": "SORTIE", "confiance_ecrite": "", "preuves_ecrites": "",
                    "familles": "", "rang_actuel": RANG.get(o["id_unique"], ""), "motif_exclusion": motif})

# ── l'etat attendu APRES, calcule ici (et relu par la repetition)
apres = {(g["id_unique"], g["app_affaire_id"]) for g in GEL}
for iu, tid, _ in retraits:
    apres.discard((iu, tid))
for o in ajouts:
    apres.add((o["id_unique"], int(o["vers"])))
connues = {L["iu"] for L in A.LIGNES} - {"54376c72", "ffcf30e6"}    # les 2 lignes NEES ne sont pas dans app_classeur_ligne_id
avant_sans = connues - {g["id_unique"] for g in GEL}
apres_sans = connues - {iu for iu, _ in apres}
attendu = COMPTE - len(retraits) + len(ajouts)
assert len(apres) == attendu
print("operations gardees %d (retraits %d, ajouts %d) . sorties %d" % (len(gardees), len(retraits), len(ajouts), len(exclues)))
print("gel %d -> %d . lignes sans lien %d -> %d" % (COMPTE, attendu, len(avant_sans), len(apres_sans)))
print("ecarts de rang (patch d'origine contre le Sheet du 19/11) : %d %s" % (len(ecarts_rang), ecarts_rang[:5]))
print("confiances ecrites :", Counter(x.split("'")[3] for x in lignes_sql))
print("preuves ecrites    :", Counter(int(x.split(", ")[4]) for x in lignes_sql))

with open(N / "AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(csv_out[0].keys()), delimiter=";")
    w.writeheader()
    w.writerows(csv_out)

paires_retrait = ",\n".join("    ('%s', %d, '%s')" % r for r in sorted(retraits))
paires_ajout = ",\n".join("    ('%s', %s, '%s')" % (o["id_unique"], o["vers"], o["role"]) for o in sorted(ajouts, key=lambda o: (o["id_unique"], o["role"])))
NR, NA = len(retraits), len(ajouts)

patch = f"""-- ═══════════════════════════════════════════════════════════════════════════════
-- LA CORRECTION DU GEL, AFFINEE PAR LE SECOND AUDIT INDEPENDANT           19/11/2026
-- ═══════════════════════════════════════════════════════════════════════════════
-- ⛔ DORMANT : il ne se joue qu'avec l'accord explicite de Frederic.
-- ⛔⛔ IL PORTE SON `commit;` : joue « pour voir », IL SE COMMITE. Ne jamais le jouer a blanc.
-- SOURCE : le patch de l'autre session (supabase/patch_correction_gel_audit_independant_2026-11-18.sql)
--   et notice/AUDIT_INDEPENDANT_V2_2026-11-19.md (§ 8). Genere par
--   phase2/checks/audit_v2_generer_patch_affine_2026-11-19.py -- ne pas le retoucher a la main.
-- CE QU'IL FAIT : {NR} liens RETIRES . {NA} liens AJOUTES . le gel passe de {COMPTE} a {attendu}.
--   Chaque operation est SOUTENUE par les deux audits independants (18/11 et 19/11).
-- CE QUI A CHANGE PAR RAPPORT AU PATCH DU 18/11 :
--   ① `etage` = un libelle court et constant ; `preuves` = le vrai compte de familles (2 a 8),
--     jamais 0 (0 veut deja dire « cree par C5, aucune preuve »).
--   ② les 18 lignes a question ouverte SORTENT (sa decision), avec QJQ9M4OF (indivisible de
--     D9MMB7OU) et, en cascade, 4 operations dont la cible resterait tenue (6FQO29C8 x2,
--     H6CTRVR6, 9WQ204HP) : {len(exclues)} operations sorties en tout, listees dans
--     notice/AUDIT_INDEPENDANT_V2_OPERATIONS_AFFINEES_2026-11-19.csv.
--   ③ la garde lit l'EMPREINTE du gel (pas seulement son compte), et un controle en tete
--     verifie que chaque cible existe, porte le bon genre et sera libre.
-- CE QU'IL NE FAIT PAS : il ne touche NI les transactions (les copies de C5 se retirent APRES,
--   des DEUX cotes), NI les valeurs posees par C2/C3/C4 sur une mauvaise transaction (geste
--   suivant, a ENCHAINER : la repetition les compte), NI Hektor, NI les 8 lignes incertaines.
-- RETOUR ARRIERE : patch_correction_gel_audit_v2_2026-11-19_INVERSE.sql
-- CONTROLE       : patch_correction_gel_audit_v2_2026-11-19_REPETITION.sql (lecture seule)
-- ═══════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LA GARDE : le gel est EXACTEMENT celui que les deux audits ont lu ──────────
do $$
declare n int; emp text; manque int; cible_ko int; deja int;
begin
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id))
    into n, emp from app_classeur_lien;
  if n <> {COMPTE} or emp <> '{EMPREINTE}' then
    raise exception '⛔ garde : le gel a bouge (% liens, empreinte %) -- rien n''est ecrit', n, emp;
  end if;
  if to_regclass('public.{SAUVEGARDE}') is not null then
    raise exception '⛔ garde : la sauvegarde {SAUVEGARDE} existe deja -- ce patch a-t-il deja ete joue ?';
  end if;
  -- chaque lien a retirer existe, avec son role
  select count(*) into manque from (values
{paires_retrait}
  ) v(id_unique, app_affaire_id, role)
  where not exists (select 1 from app_classeur_lien l where l.id_unique = v.id_unique
                       and l.app_affaire_id = v.app_affaire_id and l.role = v.role);
  if manque <> 0 then raise exception '⛔ garde : % lien(s) a retirer introuvable(s)', manque; end if;
  -- chaque cible a ajouter existe au registre et porte le genre de son role
  select count(*) into cible_ko from (values
{paires_ajout}
  ) v(id_unique, app_affaire_id, role)
  left join app_affaire_ledger a on a.app_affaire_id = v.app_affaire_id
  where a.app_affaire_id is null or a.kind <> v.role;
  if cible_ko <> 0 then raise exception '⛔ garde : % cible(s) absente(s) ou d''un autre genre', cible_ko; end if;
end $$;

-- ── ② LA SAUVEGARDE DATEE, FERMEE DES SA NAISSANCE ─────────────────────────────
create table {SAUVEGARDE} as select * from app_classeur_lien;
revoke all on {SAUVEGARDE} from public, anon, authenticated;
alter table {SAUVEGARDE} enable row level security;

-- ── ③ RETIRER ({NR}) ──────────────────────────────────────────────────────────────
delete from app_classeur_lien l
 using (values
{paires_retrait}
 ) v(id_unique, app_affaire_id, role)
 where l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id and l.role = v.role;

-- ── ④ AJOUTER ({NA}) ─────────────────────────────────────────────────────────────
insert into app_classeur_lien
  (ligne_classeur, app_affaire_id, role, confiance, preuves, etage, gele_le, gele_par, id_unique)
values
{(","+chr(10)).join(lignes_sql)};

-- ── ⑤ LE CONTROLE, DANS LA MEME TRANSACTION ─────────────────────────────────────
do $$
declare n int; doubles int; deux_roles int; poses int; mal int; garde int; temoin int; restes int;
begin
  select count(*) into n from app_classeur_lien;
  if n <> {attendu} then raise exception '⛔ le gel porte % liens, attendu {attendu}', n; end if;
  -- ⭐ L'EXCLUSIVITE : aucune transaction prise par deux lignes (la base ne la garantit pas)
  select count(*) into doubles from (select app_affaire_id from app_classeur_lien
                                      group by 1 having count(distinct id_unique) > 1) x;
  if doubles <> 0 then raise exception '⛔ % transaction(s) prises par deux lignes', doubles; end if;
  -- ⭐ et aucune ligne a deux liens pour un MEME role parmi celles que le patch touche
  select count(*) into deux_roles from (select id_unique, role from app_classeur_lien
     where id_unique in (select distinct id_unique from app_classeur_lien where gele_par = '{ETIQUETTE}')
     group by 1, 2 having count(*) > 1) x;
  if deux_roles <> 0 then raise exception '⛔ % ligne(s) a deux liens pour un meme role', deux_roles; end if;
  -- ⭐ TEMOIN POSITIF : les {NA} liens poses sont la, chacun vers le bon genre
  select count(*) into poses from app_classeur_lien where gele_par = '{ETIQUETTE}';
  if poses <> {NA} then raise exception '⛔ % lien(s) poses, attendu {NA}', poses; end if;
  select count(*) into mal from app_classeur_lien l
    left join app_affaire_ledger a on a.app_affaire_id = l.app_affaire_id
   where l.gele_par = '{ETIQUETTE}' and (a.app_affaire_id is null or a.kind <> l.role
                                          or l.preuves < 2 or l.etage <> '{ETAGE}');
  if mal <> 0 then raise exception '⛔ % lien(s) pose(s) mal formes', mal; end if;
  -- ⭐ et les {NR} retires sont partis
  select count(*) into restes from app_classeur_lien l join (values
{paires_retrait}
  ) v(id_unique, app_affaire_id, role) on l.id_unique = v.id_unique and l.app_affaire_id = v.app_affaire_id;
  if restes <> 0 then raise exception '⛔ % lien(s) a retirer encore presents', restes; end if;
  select count(*) into garde from {SAUVEGARDE};
  if garde <> {COMPTE} then raise exception '⛔ sauvegarde : % au lieu de {COMPTE}', garde; end if;
  -- ⭐ TEMOIN INVERSE : les liens que le patch ne touche pas sont IDENTIQUES, colonne par colonne
  select count(*) into temoin from app_classeur_lien l
    join {SAUVEGARDE} s using (id_unique, app_affaire_id)
   where (l.role, l.confiance, l.preuves, l.etage, l.gele_par, l.ligne_classeur, l.gele_le)
         is distinct from (s.role, s.confiance, s.preuves, s.etage, s.gele_par, s.ligne_classeur, s.gele_le);
  if temoin <> 0 then raise exception '⛔ temoin inverse : % lien(s) non vise(s) ont change', temoin; end if;
  raise notice '✅ gel corrige : -{NR} +{NA} = {attendu} liens, exclusivite tenue, voisins intacts.';
  raise notice '➡ A ENCHAINER (correction 3) : les valeurs posees par nous sur les transactions detachees -- voir la repetition.';
end $$;

commit;
"""
inverse = f"""-- RETOUR ARRIERE de patch_correction_gel_audit_v2_2026-11-19.sql -- 19/11/2026
-- ⭐ LECON 31 : un retour arriere ne juge que SA part. Il retire les {NA} liens que le patch
--   a poses (gele_par = '{ETIQUETTE}') et remet les {NR} liens qu'il avait retires, A
--   L'IDENTIQUE, depuis la sauvegarde. Il ne refuse PAS de tourner si d'autres liens ont
--   change depuis pour une autre raison : il le DIT (notice), il ne l'efface pas.
--   ⚠ Corrige le 19/11 : l'inverse du patch du 18/11 exigeait un gel ENTIER identique a la
--   sauvegarde, et aurait donc refuse de defaire apres n'importe quel autre geste legitime.
-- ⛔ Il porte son `commit;`. Il ne supprime PAS la sauvegarde.
begin;
do $$ begin
  if to_regclass('public.{SAUVEGARDE}') is null then
    raise exception '⛔ pas de sauvegarde : le patch n''a jamais ete joue, rien a defaire';
  end if;
end $$;
-- ① retirer SES poses
delete from app_classeur_lien where gele_par = '{ETIQUETTE}';
-- ② remettre SES retraits, a l'identique (toutes colonnes, depuis la sauvegarde)
insert into app_classeur_lien
  select s.* from {SAUVEGARDE} s
    join (values
{paires_retrait}
    ) v(id_unique, app_affaire_id, role)
      on s.id_unique = v.id_unique and s.app_affaire_id = v.app_affaire_id and s.role = v.role
   where not exists (select 1 from app_classeur_lien l
                      where l.id_unique = s.id_unique and l.app_affaire_id = s.app_affaire_id);
do $$
declare restes int; revenus int; doubles int; n int; emp text; ecart int;
begin
  -- ⭐ SA PART : plus aucune de ses poses, et ses {NR} retraits revenus tels qu'ils etaient
  select count(*) into restes from app_classeur_lien where gele_par = '{ETIQUETTE}';
  if restes <> 0 then raise exception '⛔ % pose(s) du patch encore presente(s)', restes; end if;
  select count(*) into revenus from app_classeur_lien l
    join {SAUVEGARDE} s using (id_unique, app_affaire_id)
    join (values
{paires_retrait}
    ) v(id_unique, app_affaire_id, role) on v.id_unique = l.id_unique and v.app_affaire_id = l.app_affaire_id
   where (l.role, l.confiance, l.preuves, l.etage, l.gele_par, l.gele_le)
         is not distinct from (s.role, s.confiance, s.preuves, s.etage, s.gele_par, s.gele_le);
  if revenus <> {NR} then raise exception '⛔ % lien(s) revenu(s) a l''identique sur {NR}', revenus; end if;
  select count(*) into doubles from (select app_affaire_id from app_classeur_lien
                                      group by 1 having count(distinct id_unique) > 1) x;
  if doubles <> 0 then raise exception '⛔ % transaction(s) prises par deux lignes apres le retour', doubles; end if;
  -- ⓘ LE RESTE DU GEL : une information, pas une condition (lecon 31)
  select count(*), md5(string_agg(id_unique||':'||app_affaire_id||':'||role, ','
                                  order by id_unique collate "C", app_affaire_id))
    into n, emp from app_classeur_lien;
  select count(*) into ecart from (
    (select id_unique, app_affaire_id, role from app_classeur_lien
     except select id_unique, app_affaire_id, role from {SAUVEGARDE})
    union all
    (select id_unique, app_affaire_id, role from {SAUVEGARDE}
     except select id_unique, app_affaire_id, role from app_classeur_lien)) x;
  raise notice '✅ sa part est defaite : 0 pose restante, {NR} retraits revenus a l''identique.';
  raise notice 'ⓘ le gel entier : % liens (sauvegarde {COMPTE}), % ecart(s) avec la sauvegarde, empreinte % (avant : {EMPREINTE}). Un ecart ici vient d''un AUTRE geste, posterieur.', n, ecart, emp;
end $$;
commit;
"""
detaches = sorted({tid for _, tid, _ in retraits if tid not in A.C5})
repetition = f"""-- REPETITION de patch_correction_gel_audit_v2_2026-11-19.sql -- LECTURE SEULE, a jouer APRES le patch.
-- Chaque compte a sa valeur attendue a cote. Une lecture qui echoue n'est JAMAIS un vert.
select json_build_object(
  'liens', (select count(*) from app_classeur_lien), 'attendu', {attendu},
  'poses_par_le_patch', (select count(*) from app_classeur_lien where gele_par = '{ETIQUETTE}'), 'attendu_poses', {NA},
  'preuves_des_poses', (select json_object_agg(p, c) from (select preuves p, count(*) c from app_classeur_lien
                         where gele_par = '{ETIQUETTE}' group by 1) x),
  'transactions_prises_deux_fois', (select count(*) from (select app_affaire_id from app_classeur_lien
                                     group by 1 having count(distinct id_unique) > 1) x), 'attendu_deux_fois', 0,
  'lignes_sans_lien', (select count(*) from app_v_classeur_ligne_sans_lien), 'attendu_sans_lien', {len(apres_sans)},
  'liens_casses_disparue', (select count(*) from app_v_classeur_lien_casse where gravite = 'DISPARUE'), 'attendu_disparue', 0,
  'sauvegarde', (select count(*) from {SAUVEGARDE}), 'attendu_sauvegarde', {COMPTE},
  -- ➡ CORRECTION 3 : ce qui reste a ENCHAINER -- les valeurs posees par NOUS sur les {len(detaches)}
  --   transactions de Hektor que le patch detache d'une ligne (les copies de C5 se retirent entieres)
  --   ⓘ MESURE DU 19/11 AVANT LE PATCH (le patch ne les touche pas) : 10 transactions portent une
  --     valeur, 15 portent une note du Sheet. Le geste suivant doit les faire DESCENDRE.
  'attendu_traces_avant_nettoyage', 10, 'attendu_notes_avant_nettoyage', 15,
  'traces_sur_transactions_detachees', (select count(*) from app_affaire_ledger
     where app_affaire_id in ({", ".join(str(x) for x in detaches)})
       and (honoraires_entree_app is not null or honoraires_sortie_app is not null
            or charge_commission_app is not null or date_annulation_app is not null
            or motif_annulation_app is not null or numero_facture_app is not null
            or vente_reglee_app is not null)),
  'notes_classeur_sur_transactions_detachees', (select count(*) from app_affaire_note
     where app_affaire_id in ({", ".join(str(x) for x in detaches)}) and origine like 'classeur%')
) r;
"""
(RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19.sql").write_text(patch, encoding="utf-8", newline="\n")
(RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19_INVERSE.sql").write_text(inverse, encoding="utf-8", newline="\n")
(RACINE / "supabase" / "patch_correction_gel_audit_v2_2026-11-19_REPETITION.sql").write_text(repetition, encoding="utf-8", newline="\n")
(T / "transactions_detachees.json").write_text(json.dumps(detaches), encoding="utf-8")
print("ecrit : supabase/patch_correction_gel_audit_v2_2026-11-19.sql (+ _INVERSE, _REPETITION)")
print("transactions de Hektor detachees (hors C5) : %d" % len(detaches))
