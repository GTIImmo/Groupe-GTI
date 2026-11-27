-- patch_famille2_parts_et_ventes_2026-11-27 -- genere par phase2/checks/famille2_parts_et_ventes_generer_patch_2026-11-27.py (son mot du 27/11)
-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql

begin;

-- ─── ① LES GARDES : les 4 chaines et leurs deux suppositions, les 6 ventes et leurs cases vides, tels que lus ──────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_repartition_avant_famille2_20261127') is not null or to_regclass('public.app_affaire_ledger_avant_ventes_reglees_f2_20261127') is not null then
    raise exception '⛔ garde : une sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot in ('parts_famille2_2026-11-27', 'ventes_reglees_famille2_2026-11-27');
  if n <> 0 then raise exception '⛔ garde : % ligne(s) des lots deja au journal', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781);
  if n <> 8 then raise exception '⛔ garde : les 4 chaines portent % part(s) au lieu de 8', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781) and rang = 1
     and cote in ('entree', 'sortie') and pourcentage = 50 and origine = 'hektor_partage_suppose' and ecrit_par = 'conversion';
  if n <> 8 then raise exception '⛔ garde : % supposition(s) telles que mesurees sur 8', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition);
  if e <> '113c064e257b5c366fa2bfc2848bb9fe' then raise exception '⛔ garde : le registre des parts a bouge depuis la mesure (%)', e; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (19133, 27714, 1029, 24620, 4783, 17770) and kind = 'vente'
     and coalesce(vente_reglee_app, '') = '' and coalesce(numero_facture_app, '') = '';
  if n <> 6 then raise exception '⛔ garde : % vente(s) sur 6 ont leurs deux cases vides', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (19133, 27714, 1029, 24620, 4783, 17770));
  if e <> '7b5153748bd259243ee774ca95f57bd4' then raise exception '⛔ garde : les 6 ventes ont change depuis la fabrication (%)', e; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') <> 3738 then
    raise exception '⛔ garde : le nombre de ventes reglees a change depuis la fabrication'; end if;
  raise notice '✅ gardes : 4 chaines a deux suppositions, 6 ventes aux cases vides, le registre tel que mesure';
end $$;

-- ─── ② LES SAUVEGARDES DATEES, AVEC cle primaire et RLS ─────────────────────────────────────────────────────────────────
create table public.app_affaire_repartition_avant_famille2_20261127 (like public.app_affaire_repartition including defaults including constraints including indexes);
insert into public.app_affaire_repartition_avant_famille2_20261127 select * from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781);
revoke all on public.app_affaire_repartition_avant_famille2_20261127 from public, anon, authenticated;
alter table public.app_affaire_repartition_avant_famille2_20261127 enable row level security;
create table public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 as select * from public.app_affaire_ledger where app_affaire_id in (19133, 27714, 1029, 24620, 4783, 17770);
alter table public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 add primary key (app_affaire_id);
revoke all on public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 from public, anon, authenticated;
alter table public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 enable row level security;

-- ─── ③ TEMPS 1, LES PARTS : le journal, la regle 6 (mises de cote entieres), la part du classeur ───────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'parts_famille2_2026-11-27', v.n, 'repartition', 'app_affaire_repartition (' || v.cote || ', rang ' || v.rang || ')',
       'REMPLACER (le classeur fait foi ; l''ancienne mise de cote)', v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero,
       d.app_dossier_uuid, v.ch, d.kind, d.app_chaine_id, d.app_dossier_numero, v.uid || ' ' || v.nom || ' ' || v.pct,
       v.ancienne, v.ligne, v.num, 'Sheet (Negociateurs / Pourcentages, regles du 13/11), image 2026-11-26_094931 = le Sheet du 27/11',
       v.pourquoi, 'patch_famille2_2026-11-27'
  from (values
    (1, 'EJN79TJ1', 2485, 27712, 'entree', 1, '80', 'CHRISTINE BRAVARD', '50', '80 Mme. Christine BRAVARD 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)'),
    (2, 'EJN79TJ1', 2485, 27712, 'sortie', 1, '80', 'CHRISTINE BRAVARD', '50', '80 Mme. Christine BRAVARD 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)'),
    (3, '2U5QPKRC', 3323, 17769, 'entree', 1, '235', 'JEAN VALLA', '50', '235 Jean VALLA 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)'),
    (4, '2U5QPKRC', 3323, 17769, 'sortie', 1, '235', 'JEAN VALLA', '50', '235 Jean VALLA 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)'),
    (5, 'I3TFR2KG', 2665, 24618, 'entree', 1, '77', 'MARION BILLIG BILLIGDURAND DURAND', '50', '77 Marion BILLIG DURAND 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)'),
    (6, 'I3TFR2KG', 2665, 24618, 'sortie', 1, '77', 'MARION BILLIG BILLIGDURAND DURAND', '50', '77 Marion BILLIG DURAND 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)'),
    (7, '91IHSGNC', 2780, 4781, 'entree', 1, '238', 'Joel CHAMPAGNAC', '50', '238 Joel CHAMPAGNAC 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)'),
    (8, '91IHSGNC', 2780, 4781, 'sortie', 1, '238', 'Joel CHAMPAGNAC', '50', '238 Joel CHAMPAGNAC 50 (hektor_partage_suppose)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : sa vente sera posee reglee ; le classeur fait foi, une supposition de Hektor n''est pas une donnee ; l''origine est le verrou (24/11)')
  ) v(n, ligne, num, ch, cote, rang, uid, nom, pct, ancienne, pourquoi)
  left join public.app_affaire_ledger d on d.app_affaire_id = v.ch;
insert into public.app_affaire_repartition_mise_de_cote
  (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment,
   pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, r.app_chaine_id, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'patch_famille2_2026-11-27',
       j.pourquoi || ' -- remplacee par ' || j.valeur || ' (ligne ' || j.ligne_origine || ', n° ' || j.ligne_origine_num || ')'
  from public.app_affaire_repartition r
  join public.app_classeur_realignement_journal j
    on j.lot = 'parts_famille2_2026-11-27' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
delete from public.app_affaire_repartition r using public.app_classeur_realignement_journal j
 where j.lot = 'parts_famille2_2026-11-27' and j.de_app_affaire_id = r.app_chaine_id and j.colonne = 'app_affaire_repartition (' || r.cote || ', rang ' || r.rang || ')';
insert into public.app_affaire_repartition
  (app_chaine_id, app_dossier_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par)
select m.app_chaine_id, m.app_dossier_id, m.cote, m.rang, v.uid, v.nom, v.pct::numeric, 'classeur_reconstitue', now(), v.par
  from (values
    (27712, 'entree', 1, '80', 'CHRISTINE BRAVARD', '50', 'classeur:EJN79TJ1'),
    (27712, 'sortie', 1, '80', 'CHRISTINE BRAVARD', '50', 'classeur:EJN79TJ1'),
    (17769, 'entree', 1, '235', 'JEAN VALLA', '50', 'classeur:2U5QPKRC'),
    (17769, 'sortie', 1, '235', 'JEAN VALLA', '50', 'classeur:2U5QPKRC'),
    (24618, 'entree', 1, '77', 'MARION BILLIG BILLIGDURAND DURAND', '50', 'classeur:I3TFR2KG'),
    (24618, 'sortie', 1, '77', 'MARION BILLIG BILLIGDURAND DURAND', '50', 'classeur:I3TFR2KG'),
    (4781, 'entree', 1, '238', 'Joel CHAMPAGNAC', '50', 'classeur:91IHSGNC'),
    (4781, 'sortie', 1, '238', 'Joel CHAMPAGNAC', '50', 'classeur:91IHSGNC')
  ) v(ch, cote, rang, uid, nom, pct, par)
  join public.app_affaire_repartition_mise_de_cote m
    on m.mise_de_cote_par = 'patch_famille2_2026-11-27' and m.app_chaine_id = v.ch and m.cote = v.cote and m.rang = v.rang;

-- ─── ④ TEMPS 2, LES VENTES : le journal, puis seulement des cases VIDES ────────────────────────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'ventes_reglees_famille2_2026-11-27', v.n, 'vente_reglee_facture', v.colonne, 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, 'VIDE',
       v.ligne, v.num, 'Sheet, image 2026-11-26_094931 (passage 82) = le Sheet du 27/11, mot pour mot comme C8 le 16/11', v.pourquoi,
       'patch_famille2_2026-11-27'
  from (values
    (1, '6FQO29C8', 589, 19133, 'vente_reglee_app', '11/06/2024', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (2, '6FQO29C8', 589, 19133, 'numero_facture_app', 'GGTI00003625 (2250 €) / GGTI00003664 (3750 €)', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (3, 'EJN79TJ1', 2485, 27714, 'vente_reglee_app', '08/09/2020', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (4, 'EJN79TJ1', 2485, 27714, 'numero_facture_app', 'GGTI00000441>AVR00000098/GGTI00000601', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (5, 'QXDW8EQA', 2559, 1029, 'vente_reglee_app', '06/11/2020', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (6, 'QXDW8EQA', 2559, 1029, 'numero_facture_app', 'GGTI00000726', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (7, 'I3TFR2KG', 2665, 24620, 'vente_reglee_app', '27/04/2020', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (8, 'I3TFR2KG', 2665, 24620, 'numero_facture_app', 'GGTI00000234', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (9, '91IHSGNC', 2780, 4783, 'vente_reglee_app', '02/01/2020', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (10, '91IHSGNC', 2780, 4783, 'numero_facture_app', 'GTI6300000264 / 30.12 relance fermée jusqu''au 3 janvier', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (11, '2U5QPKRC', 3323, 17770, 'vente_reglee_app', '19 décembre18', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas'),
    (12, '2U5QPKRC', 3323, 17770, 'numero_facture_app', 'GTI43000066 /18.12 relance', 'SON MOT du 27/11 (« Fini ce qui etait prevu », « Fais les deux ») -- la famille 2 des 47 : une vraie vente reglee dont seul le Prix du Sheet est faux (honoraires, facture et dates concordent), jamais posee : le gel ne la reliait pas')
  ) v(n, ligne, num, piece, colonne, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;
update public.app_affaire_ledger l set vente_reglee_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = 'ventes_reglees_famille2_2026-11-27' and j.colonne = 'vente_reglee_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.vente_reglee_app, '') = '';
update public.app_affaire_ledger l set numero_facture_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = 'ventes_reglees_famille2_2026-11-27' and j.colonne = 'numero_facture_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.numero_facture_app, '') = '';

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  -- temps 1 : chaque chaine porte EXACTEMENT la part du classeur, plus aucune part hektor, la somme a 100
  select count(*) into n from public.app_affaire_repartition r join (values
    (27712, 'entree', 1, '80', 'CHRISTINE BRAVARD', '50', 'classeur:EJN79TJ1'),
    (27712, 'sortie', 1, '80', 'CHRISTINE BRAVARD', '50', 'classeur:EJN79TJ1'),
    (17769, 'entree', 1, '235', 'JEAN VALLA', '50', 'classeur:2U5QPKRC'),
    (17769, 'sortie', 1, '235', 'JEAN VALLA', '50', 'classeur:2U5QPKRC'),
    (24618, 'entree', 1, '77', 'MARION BILLIG BILLIGDURAND DURAND', '50', 'classeur:I3TFR2KG'),
    (24618, 'sortie', 1, '77', 'MARION BILLIG BILLIGDURAND DURAND', '50', 'classeur:I3TFR2KG'),
    (4781, 'entree', 1, '238', 'Joel CHAMPAGNAC', '50', 'classeur:91IHSGNC'),
    (4781, 'sortie', 1, '238', 'Joel CHAMPAGNAC', '50', 'classeur:91IHSGNC')
  ) v(ch, cote, rang, uid, nom, pct, par) on r.app_chaine_id = v.ch and r.cote = v.cote and r.rang = v.rang
   where r.hektor_user_id = v.uid and r.nom_au_moment = v.nom and r.pourcentage = v.pct::numeric
     and r.origine = 'classeur_reconstitue' and r.ecrit_par = v.par;
  if n <> 8 or (select count(*) from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781)) <> 8 then
    raise exception '⛔ controle : les 4 chaines ne portent pas exactement la part du classeur (% sur 8)', n; end if;
  select count(*) into n from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781) and coalesce(origine, '') like 'hektor%';
  if n <> 0 then raise exception '⛔ controle : % part(s) hektor encore sur les 4 chaines', n; end if;
  select count(*) into n from (select app_chaine_id from public.app_affaire_repartition where app_chaine_id in (27712, 17769, 24618, 4781)
                                group by 1 having sum(pourcentage) <> 100) x;
  if n <> 0 then raise exception '⛔ controle : % chaine(s) dont la somme n''est pas 100', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition where app_chaine_id not in (27712, 17769, 24618, 4781));
  if e <> '0f210da5ad0d16e930a2e025fecc0588' then raise exception '⛔ controle : une part HORS des 4 chaines a bouge (%)', e; end if;
  if (select count(*) from public.app_affaire_repartition) <> 17970 then raise exception '⛔ controle : le nombre de parts a change'; end if;
  select count(*) into n from public.app_affaire_repartition_mise_de_cote m join public.app_affaire_repartition_avant_famille2_20261127 s
    on s.app_chaine_id = m.ancien_app_chaine_id and s.cote = m.cote and s.rang = m.rang and s.hektor_user_id = m.hektor_user_id
   and s.pourcentage = m.pourcentage and s.origine is not distinct from m.origine and s.ecrit_le = m.ecrit_le
   and s.ecrit_par is not distinct from m.ecrit_par and s.nom_au_moment is not distinct from m.nom_au_moment
   and s.app_dossier_id is not distinct from m.app_dossier_id
   where m.mise_de_cote_par = 'patch_famille2_2026-11-27';
  if n <> 8 or (select count(*) from public.app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'patch_famille2_2026-11-27') <> 8 then
    raise exception '⛔ controle : % supposition(s) mise(s) de cote entiere(s) sur 8', n; end if;
  -- temps 2 : les 12 cases, rien d'autre
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l on l.app_affaire_id = j.de_app_affaire_id
   where j.lot = 'ventes_reglees_famille2_2026-11-27' and j.ligne_origine is not null
     and ((j.colonne = 'vente_reglee_app' and l.vente_reglee_app = j.valeur) or (j.colonne = 'numero_facture_app' and l.numero_facture_app = j.valeur));
  if n <> 12 then raise exception '⛔ controle : % case(s) posee(s) sur 12', n; end if;
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_ventes_reglees_f2_20261127 s using (app_affaire_id)
   where (l.kind, l.state, l.app_chaine_id, l.app_dossier_numero, l.date_annulation_app, l.motif_annulation_app,
          l.honoraires_entree_app, l.montant, l.honoraires_entree)
         is distinct from (s.kind, s.state, s.app_chaine_id, s.app_dossier_numero, s.date_annulation_app, s.motif_annulation_app,
                           s.honoraires_entree_app, s.montant, s.honoraires_entree);
  if n <> 0 then raise exception '⛔ controle : % vente(s) ont bouge hors de leurs deux cases', n; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') <> 3738 + 6 then
    raise exception '⛔ controle : le nombre de ventes reglees n''est pas 3738 + 6'; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(numero_facture_app, '') <> '') <> 3680 + 6 then
    raise exception '⛔ controle : le nombre de factures n''est pas 3680 + 6'; end if;
  if (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  if (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id) and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id and coalesce(r.origine, '') not like 'hektor%')) <> 20 then raise exception '⛔ controle : une vente reglee de plus sur des parts supposees seulement'; end if;
  if (select count(*) from public.app_affaire_repartition r where not exists (select 1 from public.app_affaire_ledger l where l.app_chaine_id = r.app_chaine_id)) <> 0 then raise exception '⛔ controle : des parts orphelines'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot in ('parts_famille2_2026-11-27', 'ventes_reglees_famille2_2026-11-27');
  if n <> 8 + 12 then raise exception '⛔ controle : % ligne(s) au journal sur 8 + 12', n; end if;
  e := md5((select md5(coalesce(string_agg(concat_ws('|', app_chaine_id, cote, rang, hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_par), ';' order by app_chaine_id, cote, rang), '')) from public.app_affaire_repartition) || (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (19133, 27714, 1029, 24620, 4783, 17770)));
  if e <> 'c2477fa31eb028a4dbae1dc422f3d86b' then raise exception '⛔ controle : empreinte apres % au lieu de c2477fa31eb028a4dbae1dc422f3d86b', e; end if;
  raise notice '✅ famille 2 : 4 chaines a la part du classeur (8 suppositions mises de cote), 6 ventes reglees et leurs factures ; empreinte apres %', e;
end $$;

commit;
