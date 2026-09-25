-- MATTERPORT GAGNE SON NUMERO D'APP
--                                                                     25/09/2026
-- app_matterport_group (4 466 lignes) rattachait ses visites virtuelles aux annonces
-- par le SEUL numero Hektor, et la table ne figure pas dans REPOINT_TABLES.
--
-- ⚠ MATTERPORT NE PARLE JAMAIS A HEKTOR (verifie le 25/09) : le run n'appelle que
--   api.matterport.com. Le numero Hektor n'y est qu'un moyen de designer l'annonce --
--   c'est justement pour ca qu'il peut etre double par le notre sans rien casser.
--
-- ⚠⚠ ON NE TOUCHE PAS A LA COLONNE `id`. C'est la cle de conflit du run nocturne
--    (upsert on_conflict=id) et les 5 047 lignes de app_matterport_group_model y
--    pendent par group_id. La changer creerait 4 466 lignes neuves, supprimerait les
--    anciennes, et les 5 047 scans tomberaient avec elles.
--    Geler l'identifiant fige L'ADRESSE, pas le contenu : libelle, etat, visibilite,
--    validation et scans continuent d'etre mis a jour chaque nuit.
--
-- Mesure prealable (25/09) : 58 140 numeros Hektor, chacun vers UN SEUL numero d'app,
-- 0 collision sur les 4 index. La correspondance est sans ambiguite.
--
-- Reversible :
--   alter table public.app_matterport_group drop column app_dossier_id;

begin;

alter table public.app_matterport_group
    add column if not exists app_dossier_id bigint;

comment on column public.app_matterport_group.app_dossier_id is
    'Notre numero de bien (25/09/2026). ADDITIF : la cle `id` reste inchangee -- c''est '
    'la cle de conflit du run et le point d''accroche des 5 047 scans. Le run renseigne '
    'cette colonne a chaque passage, donc elle se repare seule si une annonce est reindexee.';

-- Remplissage depuis les QUATRE index : une visite peut porter sur une annonce
-- archivee ou historique, pas seulement sur une annonce vivante.
update public.app_matterport_group g
   set app_dossier_id = p.id
  from (
        select hektor_annonce_id::text as h, app_dossier_id   as id from public.app_dossier_current
  union select hektor_annonce_id::text,      app_archive_id        from public.app_archive_annonce_index_current
  union select hektor_annonce_id::text,      app_historical_id     from public.app_historical_annonce_index_current
  union select hektor_annonce_id::text,      app_brouillon_id      from public.app_brouillon_annonce_index_current
       ) p
 where p.h = g.hektor_annonce_id::text
   and g.app_dossier_id is distinct from p.id;

create index if not exists idx_app_matterport_group_dossier
    on public.app_matterport_group (app_dossier_id);

-- COMPTE RENDU, sans blocage. Contrairement a l'empreinte documentaire, on n'exige
-- PAS 100 % : une visite peut pointer une annonce que l'app ne connait pas (les 583
-- annonces « Mandat clos » du miroir, hors des 4 index). On les compte, on les nomme,
-- et le run les renseignera si elles entrent un jour dans un index.
do $$
declare
    v_total bigint;
    v_sans  bigint;
begin
    select count(*), count(*) filter (where app_dossier_id is null)
      into v_total, v_sans
      from public.app_matterport_group;
    raise notice 'groupes Matterport = %, avec notre numero = %, sans = %',
        v_total, v_total - v_sans, v_sans;
end $$;

commit;
