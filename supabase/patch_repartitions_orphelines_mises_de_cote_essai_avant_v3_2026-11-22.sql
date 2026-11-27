-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- LES REPARTITIONS ORPHELINES MISES DE COTE -- SA REGLE DU 22/11 (« on ne supprime pas une part »)     22/11/2026 07:26
-- ════════════════════════════════════════════════════════════════════════════════════════════════
-- ⛔ DORMANT : il ne se joue qu'avec le « vas-y » explicite de Frederic, dans la conversation, APRES la V3 et sa nuit
--   de stabilite. ⛔⛔ IL PORTE SON `commit;`. La repetition a blanc est ..._A_BLANC.sql (rollback).
-- SOURCE : phase2/checks/temps13_orphelines_mises_de_cote_2026-11-22.py fabriquer --etiquette essai_avant_v3_2026-11-22 -- ne pas le
--   retoucher a la main. ETAT LU : 26 orphelines sur 13 dossiers disparus ; repartitions 17907.
-- CE QU'IL FAIT : 12 dossiers disparus dont les parts sont IDENTIQUES a celles du dossier ou leur transaction vit
--   -> leurs 24 parts passent dans app_affaire_repartition_mise_de_cote, AVEC LEUR ANCIEN NUMERO DE DOSSIER, puis
--   quittent app_affaire_repartition. Rien n'est perdu : l'INVERSE les repose a l'identique.
-- CE QU'IL NE FAIT PAS : les 1 dossiers aux parts DIFFERENTES (27135->27133) lui remontent, intacts ; il ne
--   touche ni une part derivee de Hektor, ni le chainage, ni le gel, ni Hektor.
-- RETOUR ARRIERE : patch_repartitions_orphelines_mises_de_cote_essai_avant_v3_2026-11-22_INVERSE.sql . CONTROLE : patch_repartitions_orphelines_mises_de_cote_essai_avant_v3_2026-11-22_REPETITION.sql (lecture seule)
-- ════════════════════════════════════════════════════════════════════════════════════════════════
begin;

-- ── ① LA GARDE : l'etat est EXACTEMENT celui que la fabrication a lu ───────────────────────────
do $$
declare n int; emp text; ko int;
begin
  select count(*), md5(coalesce(string_agg(app_chaine_id||':'||cote||':'||rang||':'||hektor_user_id||':'||coalesce(nom_au_moment,'')||':'||pourcentage||':'||coalesce(origine,''), ',' order by app_chaine_id, cote, rang), '')) into n, emp from app_affaire_repartition;
  if n <> 17907 or emp <> 'b4ab8dc88f54a8cc69116db7a55a166a' then
    raise exception '⛔ garde : les repartitions ont bouge (% lignes, empreinte %) -- rien n''est ecrit', n, emp;
  end if;
  -- chaque part de la liste est encore orpheline, et son dossier d'arrivee vit
  select count(*) into ko from (values
    (3670, 3669, 'entree', 1),
    (3670, 3669, 'sortie', 1),
    (11709, 11708, 'entree', 1),
    (11709, 11708, 'sortie', 1),
    (14034, 14033, 'entree', 1),
    (14034, 14033, 'sortie', 1),
    (14052, 14051, 'entree', 1),
    (14052, 14051, 'sortie', 1),
    (14913, 14912, 'entree', 1),
    (14913, 14912, 'sortie', 1),
    (19070, 19069, 'entree', 1),
    (19070, 19069, 'sortie', 1),
    (19576, 19575, 'entree', 1),
    (19576, 19575, 'sortie', 1),
    (19737, 19736, 'entree', 1),
    (19737, 19736, 'sortie', 1),
    (20089, 20088, 'entree', 1),
    (20089, 20088, 'sortie', 1),
    (24011, 24010, 'entree', 1),
    (24011, 24010, 'sortie', 1),
    (28179, 28178, 'entree', 1),
    (28179, 28178, 'sortie', 1),
    (28547, 28546, 'entree', 1),
    (28547, 28546, 'sortie', 1)
  ) v(ancien, nouveau, cote, rang)
  where exists (select 1 from app_affaire_ledger x where x.app_chaine_id = v.ancien)
     or not exists (select 1 from app_affaire_ledger x where x.app_chaine_id = v.nouveau)
     or not exists (select 1 from app_affaire_repartition r where r.app_chaine_id = v.ancien
                       and r.cote = v.cote and r.rang = v.rang and coalesce(r.origine, '') not like 'hektor%');
  if ko <> 0 then raise exception '⛔ garde : % part(s) ne sont plus orphelines ou leur dossier d''arrivee manque', ko; end if;
  -- et chaque dossier disparu porte EXACTEMENT les memes parts que son dossier d'arrivee (la regle : identiques)
  select count(*) into ko from (select distinct ancien, nouveau from (values
    (3670, 3669, 'entree', 1),
    (3670, 3669, 'sortie', 1),
    (11709, 11708, 'entree', 1),
    (11709, 11708, 'sortie', 1),
    (14034, 14033, 'entree', 1),
    (14034, 14033, 'sortie', 1),
    (14052, 14051, 'entree', 1),
    (14052, 14051, 'sortie', 1),
    (14913, 14912, 'entree', 1),
    (14913, 14912, 'sortie', 1),
    (19070, 19069, 'entree', 1),
    (19070, 19069, 'sortie', 1),
    (19576, 19575, 'entree', 1),
    (19576, 19575, 'sortie', 1),
    (19737, 19736, 'entree', 1),
    (19737, 19736, 'sortie', 1),
    (20089, 20088, 'entree', 1),
    (20089, 20088, 'sortie', 1),
    (24011, 24010, 'entree', 1),
    (24011, 24010, 'sortie', 1),
    (28179, 28178, 'entree', 1),
    (28179, 28178, 'sortie', 1),
    (28547, 28546, 'entree', 1),
    (28547, 28546, 'sortie', 1)
  ) v(ancien, nouveau, cote, rang)) p
  where (select string_agg(cote||':'||rang||':'||hektor_user_id||':'||upper(trim(coalesce(nom_au_moment,'')))||':'||pourcentage::numeric(9,3),
                           ',' order by cote, rang)
           from app_affaire_repartition where app_chaine_id = p.ancien and coalesce(origine, '') not like 'hektor%')
        is distinct from
        (select string_agg(cote||':'||rang||':'||hektor_user_id||':'||upper(trim(coalesce(nom_au_moment,'')))||':'||pourcentage::numeric(9,3),
                           ',' order by cote, rang)
           from app_affaire_repartition where app_chaine_id = p.nouveau and coalesce(origine, '') not like 'hektor%');
  if ko <> 0 then raise exception '⛔ garde : % dossier(s) n''ont plus des parts IDENTIQUES -- ils lui remontent', ko; end if;
end $$;

-- ── ② LA TABLE DE GARDE (une fois pour le projet ; fermee des sa naissance) ─────────────────────
create table if not exists app_affaire_repartition_mise_de_cote (
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
revoke all on app_affaire_repartition_mise_de_cote from public, anon, authenticated;
alter table app_affaire_repartition_mise_de_cote enable row level security;

-- ── ③ METTRE DE COTE (24 parts), PUIS RETIRER ──────────────────────────────────────────────────
insert into app_affaire_repartition_mise_de_cote (ancien_app_chaine_id, dossier_ou_elle_vit, app_chaine_id, app_dossier_id, cote, rang,
                       hektor_user_id, nom_au_moment, pourcentage, origine, ecrit_le, ecrit_par, mise_de_cote_par, pourquoi)
select r.app_chaine_id, v.nouveau, r.app_chaine_id, r.app_dossier_id, r.cote, r.rang, r.hektor_user_id, r.nom_au_moment,
       r.pourcentage, r.origine, r.ecrit_le, r.ecrit_par, 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22',
       'dossier disparu ; parts IDENTIQUES a celles du dossier ' || v.nouveau || ' (sa regle du 22/11)'
  from (values
    (3670, 3669, 'entree', 1),
    (3670, 3669, 'sortie', 1),
    (11709, 11708, 'entree', 1),
    (11709, 11708, 'sortie', 1),
    (14034, 14033, 'entree', 1),
    (14034, 14033, 'sortie', 1),
    (14052, 14051, 'entree', 1),
    (14052, 14051, 'sortie', 1),
    (14913, 14912, 'entree', 1),
    (14913, 14912, 'sortie', 1),
    (19070, 19069, 'entree', 1),
    (19070, 19069, 'sortie', 1),
    (19576, 19575, 'entree', 1),
    (19576, 19575, 'sortie', 1),
    (19737, 19736, 'entree', 1),
    (19737, 19736, 'sortie', 1),
    (20089, 20088, 'entree', 1),
    (20089, 20088, 'sortie', 1),
    (24011, 24010, 'entree', 1),
    (24011, 24010, 'sortie', 1),
    (28179, 28178, 'entree', 1),
    (28179, 28178, 'sortie', 1),
    (28547, 28546, 'entree', 1),
    (28547, 28546, 'sortie', 1)
  ) v(ancien, nouveau, cote, rang)
  join app_affaire_repartition r on r.app_chaine_id = v.ancien and r.cote = v.cote and r.rang = v.rang;
delete from app_affaire_repartition r
 using (values
    (3670, 3669, 'entree', 1),
    (3670, 3669, 'sortie', 1),
    (11709, 11708, 'entree', 1),
    (11709, 11708, 'sortie', 1),
    (14034, 14033, 'entree', 1),
    (14034, 14033, 'sortie', 1),
    (14052, 14051, 'entree', 1),
    (14052, 14051, 'sortie', 1),
    (14913, 14912, 'entree', 1),
    (14913, 14912, 'sortie', 1),
    (19070, 19069, 'entree', 1),
    (19070, 19069, 'sortie', 1),
    (19576, 19575, 'entree', 1),
    (19576, 19575, 'sortie', 1),
    (19737, 19736, 'entree', 1),
    (19737, 19736, 'sortie', 1),
    (20089, 20088, 'entree', 1),
    (20089, 20088, 'sortie', 1),
    (24011, 24010, 'entree', 1),
    (24011, 24010, 'sortie', 1),
    (28179, 28178, 'entree', 1),
    (28179, 28178, 'sortie', 1),
    (28547, 28546, 'entree', 1),
    (28547, 28546, 'sortie', 1)
 ) v(ancien, nouveau, cote, rang)
 where r.app_chaine_id = v.ancien and r.cote = v.cote and r.rang = v.rang;

-- ── ④ LE CONTROLE, DANS LA MEME TRANSACTION ─────────────────────────────────────────────────────
do $$
declare n int; g int; t int;
begin
  select count(*) into n from app_affaire_repartition;
  if n <> 17883 then raise exception '⛔ repartitions : % au lieu de 17883', n; end if;
  select count(*) into g from app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22';
  if g <> 24 then raise exception '⛔ table de garde : % part(s) de ce geste au lieu de 24', g; end if;
  -- TEMOIN POSITIF NOMME : le dossier disparu 3670 est dans la garde avec son ancien numero, et plus dans les parts
  select count(*) into t from app_affaire_repartition_mise_de_cote where mise_de_cote_par = 'orphelines_mises_de_cote_essai_avant_v3_2026-11-22' and ancien_app_chaine_id = 3670
                                             and dossier_ou_elle_vit = 3669;
  if t = 0 then raise exception '⛔ temoin : le dossier 3670 n''est pas dans la garde'; end if;
  select count(*) into t from app_affaire_repartition where app_chaine_id = 3670;
  if t <> 0 then raise exception '⛔ temoin : le dossier 3670 porte encore % part(s)', t; end if;
  -- TEMOIN INVERSE : le dossier d'arrivee 3669 garde ses parts
  select count(*) into t from app_affaire_repartition where app_chaine_id = 3669;
  if t = 0 then raise exception '⛔ temoin inverse : le dossier 3669 a perdu ses parts'; end if;
  raise notice '✅ 24 parts mises de cote avec leur ancien numero ; repartitions 17907 -> 17883 ; temoins verts.';
end $$;

commit;
