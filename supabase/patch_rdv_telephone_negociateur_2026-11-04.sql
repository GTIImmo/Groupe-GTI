-- RENDEZ-VOUS : LES 178 LIENS PUBLICS QUI PORTENT LE TÉLÉPHONE D'UNE AUTRE PERSONNE (04/11/2026).
-- Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §3 bis et §16. Frédéric : « Oui, enchaîne ».
-- La cause (corrigée dans backend/app/services/appointment_service.py, même jour) : à défaut de l'e-mail, le service
-- cherchait `id_user = commercial_id` — un n° de NÉGOCIATEUR pris pour un n° de COMPTE (Aline VALETTE n° 42 → le compte 42
-- de Dylan JOURGET). Le téléphone trouvé était recopié dans app_appointment_public_link, et n'était plus jamais relu.
-- ⛔ À POSER APRÈS la mise en ligne du nouveau code (Render) : l'ancien code réécrirait un lien dont une case est vide.
-- LE REMÈDE : pour ces liens SEULEMENT, le téléphone du négociateur du lien, lu dans le REGISTRE (sa fiche, à défaut une
-- autre fiche de la même personne, les actives d'abord) — la même règle que le nouveau code.
-- Sauvegarde datée : app_appointment_public_link_avant_tel_20261104 (les lignes touchées, entières).
-- Retour arrière : patch_rdv_telephone_negociateur_2026-11-04_INVERSE.sql

do $garde$
begin
    if to_regclass('public.app_appointment_public_link_avant_tel_20261104') is not null then
        raise exception '%', 'ARRET : la sauvegarde existe déjà -- la réparation a déjà été posée. Rien n''est changé.';
    end if;
    if to_regclass('public.app_negociateur_fiche') is null then
        raise exception '%', 'ARRET : le registre des négociateurs n''est pas posé.';
    end if;
end
$garde$;

-- les liens faux : leur téléphone est celui du COMPTE dont l'id_user vaut le n° de négociateur du lien, et ce compte n'est
-- pas la personne du lien (autre e-mail)
create temp table _faux on commit drop as
select l.id
  from public.app_appointment_public_link l
  join public.app_user_directory u on u.id_user::text = l.commercial_id::text
 where nullif(trim(coalesce(l.negociateur_phone, '') || coalesce(l.negociateur_mobile, '')), '') is not null
   and lower(coalesce(u.email, '')) <> lower(coalesce(l.negociateur_email, ''))
   and ((regexp_replace(coalesce(u.portable, ''), '\D', '', 'g') = regexp_replace(coalesce(l.negociateur_mobile, ''), '\D', '', 'g') and nullif(u.portable, '') is not null)
     or (regexp_replace(coalesce(u.tel, ''), '\D', '', 'g') = regexp_replace(coalesce(l.negociateur_phone, ''), '\D', '', 'g') and nullif(u.tel, '') is not null));

create table public.app_appointment_public_link_avant_tel_20261104 as
select * from public.app_appointment_public_link where id in (select id from _faux);
alter table public.app_appointment_public_link_avant_tel_20261104 enable row level security;
revoke all on public.app_appointment_public_link_avant_tel_20261104 from anon, authenticated, public;
comment on table public.app_appointment_public_link_avant_tel_20261104 is
  'Sauvegarde du 04/11/2026 avant la réparation des téléphones des liens de rendez-vous (patch_rdv_telephone_negociateur_2026-11-04.sql).';

-- le téléphone juste : celui du registre, par le n° de négociateur du lien
create temp table _juste on commit drop as
select l.id,
       (select coalesce(nullif(trim(f.telephone), ''), nullif(trim(f.portable), '')) from public.app_negociateur_fiche f
         where f.app_personne_id = f0.app_personne_id and f.sorte = 'fiche_negociateur'
           and coalesce(nullif(trim(f.telephone), ''), nullif(trim(f.portable), '')) is not null
         order by (f.hektor_negociateur_id = f0.hektor_negociateur_id) desc, f.actif_chez_hektor desc, f.app_fiche_id limit 1) as tel,
       (select nullif(trim(f.portable), '') from public.app_negociateur_fiche f
         where f.app_personne_id = f0.app_personne_id and f.sorte = 'fiche_negociateur'
           and coalesce(nullif(trim(f.telephone), ''), nullif(trim(f.portable), '')) is not null
         order by (f.hektor_negociateur_id = f0.hektor_negociateur_id) desc, f.actif_chez_hektor desc, f.app_fiche_id limit 1) as portable
  from public.app_appointment_public_link l
  join public.app_negociateur_fiche f0 on f0.sorte = 'fiche_negociateur' and f0.hektor_negociateur_id = l.commercial_id::text
 where l.id in (select id from _faux);

update public.app_appointment_public_link l
   set negociateur_phone = j.tel, negociateur_mobile = j.portable, updated_at = now()
  from _juste j
 where l.id = j.id;

do $controle$
declare v_faux int; v_sauves int; v_restent int;
begin
    select count(*) into v_faux from _faux;
    select count(*) into v_sauves from public.app_appointment_public_link_avant_tel_20261104;
    if v_sauves <> v_faux then raise exception 'ARRET : % lignes sauvées pour % liens faux', v_sauves, v_faux; end if;
    -- plus aucun lien ne porte le téléphone du compte qui a son n° de négociateur pour id_user
    select count(*) into v_restent
      from public.app_appointment_public_link l join public.app_user_directory u on u.id_user::text = l.commercial_id::text
     where lower(coalesce(u.email, '')) <> lower(coalesce(l.negociateur_email, ''))
       and ((regexp_replace(coalesce(u.portable, ''), '\D', '', 'g') = regexp_replace(coalesce(l.negociateur_mobile, ''), '\D', '', 'g') and nullif(u.portable, '') is not null)
         or (regexp_replace(coalesce(u.tel, ''), '\D', '', 'g') = regexp_replace(coalesce(l.negociateur_phone, ''), '\D', '', 'g') and nullif(u.tel, '') is not null));
    if v_restent <> 0 then raise exception 'ARRET : % liens portent encore le téléphone d''une autre personne', v_restent; end if;
end
$controle$;
