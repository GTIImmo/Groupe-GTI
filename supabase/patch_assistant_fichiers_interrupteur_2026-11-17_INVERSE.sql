-- RETOUR ARRIÈRE de patch_assistant_fichiers_interrupteur_2026-11-17.sql : le trombone redevient éteint pour tous
-- (absent = éteint). Les fichiers déjà déposés restent sous temp/assistant/ jusqu'à la purge (2 jours).
delete from public.app_setting where key = 'assistant_fichiers';

do $$
begin
  if exists (select 1 from public.app_setting where key = 'assistant_fichiers') then
    raise exception 'INVERSE INCOMPLET : assistant_fichiers est encore la';
  end if;
end $$;
