-- Assistant IA : RETOUR ARRIÈRE -- le modèle revient de gpt-6.1-terra à gpt-4.1-mini (13/11/2026).
-- Décision de Frédéric le 13/11 : « Assistant. Ta reco », puis « non garde un seul model pour assistant ».
-- Effet : l'assistant répond de nouveau avec gpt-4.1-mini (les consignes et le lecteur du 13/11 restent).
-- La GED n'a pas de fiche ici et garde gpt-6-luna : on n'y touche pas (« ni touché pas »).
-- Le code garde le tarif de gpt-4.1-mini : ce retour arrière se pose sans redéployer.
begin;

do $$
declare m text;
begin
  select model into m from public.app_agent_prompt where agent_key = 'assistant';
  if m is distinct from 'gpt-6.1-terra' then
    raise exception 'garde : la fiche assistant porte % (attendu gpt-6.1-terra) -- quelqu''un est passé avant', coalesce(m, 'rien');
  end if;
end $$;

update public.app_agent_prompt set model = 'gpt-4.1-mini', updated_at = now() where agent_key = 'assistant';

do $$
begin
  if (select count(*) from public.app_agent_prompt where agent_key = 'assistant' and model = 'gpt-4.1-mini') <> 1 then
    raise exception 'vérification : la fiche assistant n''est pas revenue sur gpt-4.1-mini';
  end if;
end $$;

commit;
