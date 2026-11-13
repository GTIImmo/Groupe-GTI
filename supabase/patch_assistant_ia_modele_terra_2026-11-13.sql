-- Assistant IA : le modèle passe de gpt-4.1-mini à gpt-6.1-terra (13/11/2026).
-- Décision de Frédéric le 13/11 : « Assistant. Ta reco », puis « non garde un seul model pour assistant ».
-- ⚠ À poser APRÈS la mise en ligne du code qui connaît le tarif de gpt-6.1-terra (agent_tarifs.py) :
--   l'ancien code refuse un modèle sans tarif (503), l'assistant serait coupé.
-- La GED n'a pas de fiche ici et garde gpt-6-luna : on n'y touche pas (« ni touché pas »).
-- Retour arrière : patch_assistant_ia_modele_terra_2026-11-13_INVERSE.sql
begin;

do $$
declare m text;
begin
  select model into m from public.app_agent_prompt where agent_key = 'assistant';
  if m is distinct from 'gpt-4.1-mini' then
    raise exception 'garde : la fiche assistant porte % (attendu gpt-4.1-mini) -- quelqu''un est passé avant', coalesce(m, 'rien');
  end if;
end $$;

update public.app_agent_prompt set model = 'gpt-6.1-terra', updated_at = now() where agent_key = 'assistant';

do $$
begin
  if (select count(*) from public.app_agent_prompt where agent_key = 'assistant' and model = 'gpt-6.1-terra') <> 1 then
    raise exception 'vérification : la fiche assistant n''est pas sur gpt-6.1-terra';
  end if;
  if exists (select 1 from public.app_agent_prompt where agent_key <> 'assistant' and model = 'gpt-6.1-terra') then
    raise exception 'vérification : une autre fiche a été touchée';
  end if;
end $$;

commit;
