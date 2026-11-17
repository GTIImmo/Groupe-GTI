-- 17/11/2026 -- LE TROMBONE DE L'ASSISTANT : l'interrupteur `assistant_fichiers`, ouvert aux ADMINS (accord de Frédéric).
-- Note : notice/ETAPE4_ECRAN_ACCUEIL_ASSISTANT_AUDIT_2026-11-16.md §52. Trois crans : off / admin / on (absent = éteint).
-- N'écrase JAMAIS une valeur déjà posée (quelqu'un a pu le régler entre-temps).
-- Retour arrière : patch_assistant_fichiers_interrupteur_2026-11-17_INVERSE.sql.
insert into public.app_setting (key, value, description)
values ('assistant_fichiers', 'admin',
        'Assistant IA : joindre des fichiers de l''ordinateur a une question (le trombone, 17/11). off / admin / on ; absent = eteint.')
on conflict (key) do nothing;

do $$
begin
  if (select value from public.app_setting where key = 'assistant_fichiers') is distinct from 'admin' then
    raise notice 'ATTENTION : assistant_fichiers existait deja avec une autre valeur -- non modifie.';
  end if;
end $$;
