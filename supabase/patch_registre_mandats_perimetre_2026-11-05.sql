-- REGISTRE DES MANDATS : LA VUE APPLIQUE LE RÉGLAGE « JUSQU'OÙ IL VOIT » (05/11/2026).
-- Audit : notice/AUDIT_REGISTRE_NEGOCIATEURS_2026-11-04.md §31. Frédéric : « Oui, audite et corrige ».
-- LE DÉFAUT : la vue `app_registre_mandats_current` n'était pas en security_invoker -- elle lisait sa table
--   (`app_mandat_register_current`, règle : admin et manager seulement) avec les droits de son PROPRIÉTAIRE. Mesuré avec le
--   compte de Mélanie LEGRAND : 24 577 lignes par la vue, 0 par la table. Un compte réglé sur « Ses biens seulement » lisait
--   donc tout le registre.
-- POURQUOI PAS « FERMER » : les négociateurs lisent cette vue tous les jours par la fiche de LEURS biens (cycle des
--   affaires : date de clôture du mandat, charge des honoraires, offre / compromis / vente) et par la recherche globale.
-- LE REMÈDE : la table reçoit une 2e règle de lecture, COPIE de celle des biens (`app_dossier_current`) -- réseau = tout,
--   agence = son agence, portefeuille = ses biens -- et la vue passe en security_invoker. Additif : la règle admin/manager
--   reste.
-- Éprouvé dans une transaction annulée : Mélanie « réseau » 24 577 (inchangé) ; Mélanie « ses biens seulement » 346 (les
--   siennes) ; admin 24 577 ; catalogue des filtres 93 (inchangé).
-- Retour arrière : patch_registre_mandats_perimetre_2026-11-05_INVERSE.sql

do $garde$
begin
    if exists (select 1 from pg_policy where polname = 'app_mandat_register_current_select_perimetre') then
        raise exception '%', 'ARRET : la règle existe déjà -- le patch a déjà été posé. Rien n''est changé.';
    end if;
end
$garde$;

create policy app_mandat_register_current_select_perimetre on public.app_mandat_register_current for select to authenticated
using ((select public.is_app_global_reader()) or (select public.app_perimetre_courant()) = 'reseau'
       or ((select public.app_perimetre_courant()) = 'agence' and nullif(trim(coalesce(agence_nom, '')), '') is not null
           and lower(trim(agence_nom)) = (select lower(trim(coalesce(public.app_mon_agence(), '##aucune##')))))
       or (nullif(trim(coalesce(negociateur_email, '')), '') is not null
           and lower(trim(negociateur_email)) = (select lower(trim(coalesce(p.email, '##aucun##'))) from public.app_user_profile p
                                                  where p.id = auth.uid() and p.is_active = true and p.role::text = 'commercial' limit 1)));
comment on policy app_mandat_register_current_select_perimetre on public.app_mandat_register_current is
  'Lecture selon le périmètre du compte (même règle que app_dossier_current). 05/11/2026, audit registre négociateurs §31.';

alter view public.app_registre_mandats_current set (security_invoker = true);
