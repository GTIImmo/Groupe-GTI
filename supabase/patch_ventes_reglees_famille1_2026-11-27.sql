-- patch_ventes_reglees_famille1_2026-11-27 -- genere par phase2/checks/ventes_reglees_famille1_generer_patch_2026-11-27.py (son mot du 27/11)
-- Retour arriere : ..._INVERSE.sql . Controle : ..._REPETITION.sql

begin;

-- ─── ① LES GARDES : les 9 ventes telles que lues, leurs deux cases VIDES ──────────────────────────────────────────────
do $$
declare n int; e text;
begin
  if to_regclass('public.app_affaire_ledger_avant_ventes_reglees_f1_20261127') is not null then raise exception '⛔ garde : la sauvegarde existe deja -- ce patch ne se rejoue pas'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'ventes_reglees_famille1_2026-11-27';
  if n <> 0 then raise exception '⛔ garde : % ligne(s) du lot deja au journal', n; end if;
  select count(*) into n from public.app_affaire_ledger where app_affaire_id in (3650, 14115, 20674, 30835, 30828, 30844, 30834, 30846, 30847) and kind = 'vente'
     and coalesce(vente_reglee_app, '') = '' and coalesce(numero_facture_app, '') = '';
  if n <> 9 then raise exception '⛔ garde : % vente(s) sur 9 ont leurs deux cases vides', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (3650, 14115, 20674, 30835, 30828, 30844, 30834, 30846, 30847));
  if e <> 'fe8ded18db7a56241042231833c0f217' then raise exception '⛔ garde : les 9 lignes ont change depuis la fabrication (%)', e; end if;
  if 3729 <> (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') then
    raise exception '⛔ garde : le nombre de ventes reglees a change depuis la fabrication'; end if;
  raise notice '✅ gardes : 9 ventes, leurs deux cases vides, telles que lues';
end $$;

-- ─── ② LA SAUVEGARDE DATEE des 9 lignes, AVEC la cle primaire et la RLS ───────────────────────────────────────────────
create table public.app_affaire_ledger_avant_ventes_reglees_f1_20261127 as select * from public.app_affaire_ledger where app_affaire_id in (3650, 14115, 20674, 30835, 30828, 30844, 30834, 30846, 30847);
alter table public.app_affaire_ledger_avant_ventes_reglees_f1_20261127 add primary key (app_affaire_id);
revoke all on public.app_affaire_ledger_avant_ventes_reglees_f1_20261127 from public, anon, authenticated;
alter table public.app_affaire_ledger_avant_ventes_reglees_f1_20261127 enable row level security;

-- ─── ③ LE JOURNAL : chaque case, sa valeur MOT POUR MOT, sa ligne d'origine et son numero ─────────────────────────────
insert into public.app_classeur_realignement_journal
  (lot, n, famille, colonne, geste, de_app_affaire_id, de_kind, de_app_chaine_id, de_dossier_numero, de_dossier_uuid,
   vers_app_affaire_id, vers_kind, vers_app_chaine_id, vers_dossier_numero, valeur, ancienne_valeur, ligne_origine,
   ligne_origine_num, lot_origine, pourquoi, ecrit_par)
select 'ventes_reglees_famille1_2026-11-27', v.n, 'vente_reglee_facture', v.colonne, 'POSER (case vide)', v.piece, d.kind, d.app_chaine_id,
       d.app_dossier_numero, d.app_dossier_uuid, v.piece, d.kind, d.app_chaine_id, d.app_dossier_numero, v.valeur, 'VIDE',
       v.ligne, v.num, 'Sheet, image 2026-11-26_094931 (passage 82) = le Sheet du 27/11, mot pour mot comme C8 le 16/11', v.pourquoi,
       'patch_ventes_reglees_famille1'
  from (values
    (1, '9Q0FHAKK', 286, 3650, 'vente_reglee_app', '24/01/2025', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (2, '9Q0FHAKK', 286, 3650, 'numero_facture_app', 'GGTI00003842', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (3, 'AYIHPHF5', 1932, 14115, 'vente_reglee_app', '02/03/2022', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (4, 'AYIHPHF5', 1932, 14115, 'numero_facture_app', 'GGTI00002112', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (5, 'LWZL8V5M', 2239, 20674, 'vente_reglee_app', '05/11/2020', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (6, 'LWZL8V5M', 2239, 20674, 'numero_facture_app', 'GGTI00000783 >AVR00000129>GGTI00000784 notaire vendeur Me FERAUD marseille ?', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (7, '84c91bb8', 4643, 30835, 'vente_reglee_app', '19/11/2026', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (8, '84c91bb8', 4643, 30835, 'numero_facture_app', 'GGTI00004555', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (9, 'a56ce827', 4645, 30828, 'vente_reglee_app', '16/11/2026', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (10, 'a56ce827', 4645, 30828, 'numero_facture_app', 'GGTI00004550', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (11, 'ef08b63a', 4655, 30844, 'vente_reglee_app', '23/11/2026', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (12, 'ef08b63a', 4655, 30844, 'numero_facture_app', 'GGTI00004516 / 19.11 relance', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (13, 'd9a0630c', 4662, 30834, 'vente_reglee_app', '17/11/2026', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (14, 'd9a0630c', 4662, 30834, 'numero_facture_app', 'GGTI00004551', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (15, 'a6d41ca1', 4672, 30846, 'vente_reglee_app', '24/11/2026', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (16, 'a6d41ca1', 4672, 30846, 'numero_facture_app', 'GGTI00004549', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (17, '8f3a4326', 4687, 30847, 'vente_reglee_app', '24/11/2026', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne'),
    (18, '8f3a4326', 4687, 30847, 'numero_facture_app', 'GGTI00004538', 'SON MOT du 27/11 (« Fini ce qui etait prevu ») -- la methode des 47 (+2), famille 1 : une vraie vente reglee de son classeur ou tout concorde (Sheet et Hektor), jamais posee parce que le gel ne reliait pas la piece a sa ligne')
  ) v(n, ligne, num, piece, colonne, valeur, pourquoi)
  join public.app_affaire_ledger d on d.app_affaire_id = v.piece;

-- ─── ④ LE GESTE : seulement des cases VIDES ───────────────────────────────────────────────────────────────────────────
update public.app_affaire_ledger l set vente_reglee_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = 'ventes_reglees_famille1_2026-11-27' and j.colonne = 'vente_reglee_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.vente_reglee_app, '') = '';
update public.app_affaire_ledger l set numero_facture_app = j.valeur
  from public.app_classeur_realignement_journal j
 where j.lot = 'ventes_reglees_famille1_2026-11-27' and j.colonne = 'numero_facture_app' and l.app_affaire_id = j.de_app_affaire_id
   and coalesce(l.numero_facture_app, '') = '';

-- ─── ⑤ LES CONTROLES ───────────────────────────────────────────────────────────────────────────────────────────────────
do $$
declare n int; e text;
begin
  select count(*) into n from public.app_classeur_realignement_journal j join public.app_affaire_ledger l
    on l.app_affaire_id = j.de_app_affaire_id
   where j.lot = 'ventes_reglees_famille1_2026-11-27' and j.ligne_origine is not null
     and ((j.colonne = 'vente_reglee_app' and l.vente_reglee_app = j.valeur)
       or (j.colonne = 'numero_facture_app' and l.numero_facture_app = j.valeur));
  if n <> 18 then raise exception '⛔ controle : % case(s) posee(s) sur 18', n; end if;
  -- aucune autre colonne des 9 lignes n'a bouge
  select count(*) into n from public.app_affaire_ledger l join public.app_affaire_ledger_avant_ventes_reglees_f1_20261127 s using (app_affaire_id)
   where (l.kind, l.state, l.app_chaine_id, l.app_dossier_numero, l.date_annulation_app, l.motif_annulation_app,
          l.honoraires_entree_app, l.montant, l.honoraires_entree)
         is distinct from (s.kind, s.state, s.app_chaine_id, s.app_dossier_numero, s.date_annulation_app, s.motif_annulation_app,
                           s.honoraires_entree_app, s.montant, s.honoraires_entree);
  if n <> 0 then raise exception '⛔ controle : % ligne(s) ont bouge hors de leurs deux cases', n; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(vente_reglee_app, '') <> '') <> 3729 + 9 then
    raise exception '⛔ controle : le nombre de ventes reglees n''est pas 3729 + 9'; end if;
  if (select count(*) from public.app_affaire_ledger where coalesce(numero_facture_app, '') <> '') <> 3671 + 9 then
    raise exception '⛔ controle : le nombre de factures n''est pas 3671 + 9'; end if;
  if (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and l.app_chaine_id is not null and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id)) <> 0 then raise exception '⛔ controle : une vente reglee sans part'; end if;
  if (select count(distinct l.app_chaine_id) from public.app_affaire_ledger l where l.kind = 'vente' and coalesce(l.vente_reglee_app, '') <> '' and exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id) and not exists (select 1 from public.app_affaire_repartition r where r.app_chaine_id = l.app_chaine_id and coalesce(r.origine, '') not like 'hektor%')) <> 20 then raise exception '⛔ controle : une vente reglee de plus sur des parts supposees seulement'; end if;
  select count(*) into n from public.app_classeur_realignement_journal where lot = 'ventes_reglees_famille1_2026-11-27';
  if n <> 18 then raise exception '⛔ controle : % ligne(s) au journal sur 18', n; end if;
  e := (select md5(coalesce(string_agg(concat_ws('|', app_affaire_id, kind, state, app_chaine_id, app_dossier_numero, coalesce(vente_reglee_app, '-'), coalesce(numero_facture_app, '-'), coalesce(date_annulation_app, '-'), coalesce(motif_annulation_app, '-'), coalesce(honoraires_entree_app::text, '-')), ';' order by app_affaire_id), '')) from public.app_affaire_ledger where app_affaire_id in (3650, 14115, 20674, 30835, 30828, 30844, 30834, 30846, 30847));
  if e <> 'c283c736b2850a010a619e04ce0b7810' then raise exception '⛔ controle : empreinte apres % au lieu de c283c736b2850a010a619e04ce0b7810', e; end if;
  raise notice '✅ 9 ventes reglees et leurs 9 factures posees sur des cases vides ; le reste des lignes intact ; empreinte apres %', e;
end $$;

commit;
