-- Retour arrière de patch_rdv_telephone_negociateur_2026-11-04.sql : remet les téléphones d'avant sur les liens touchés,
-- depuis la sauvegarde datée. ⚠ Il remet aussi les MAUVAIS numéros (ceux d'une autre personne) : à n'utiliser qu'en cas
-- de dégât de la réparation elle-même.
update public.app_appointment_public_link l
   set negociateur_phone = s.negociateur_phone, negociateur_mobile = s.negociateur_mobile, updated_at = s.updated_at
  from public.app_appointment_public_link_avant_tel_20261104 s
 where l.id = s.id;
select count(*) as lignes_remises from public.app_appointment_public_link_avant_tel_20261104;
-- puis, quand on est sûr : drop table public.app_appointment_public_link_avant_tel_20261104;
