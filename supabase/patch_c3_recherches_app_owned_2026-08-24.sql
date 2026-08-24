-- =====================================================================
-- Tache C.3 -- les recherches ne remontent plus a Hektor
-- Date : 2026-08-24
-- Appliquee via la migration `c3_fermer_la_porte_sortante_des_recherches`
--
-- LA DECISION est de Frederic, prise le 20/08 : « une recherche saisie dans l'app n'a pas a
-- remonter a Hektor, uniquement dans le serveur et Supabase ». Elle prolonge celle du
-- 19/06 -- l'affinage Supabase-first -- que l'etude du 21/08 a retrouvee dans quatre
-- commits (6f6fd4d, b516877, b505771, 4f8c4c1).
--
-- POURQUOI. La modale n'exprime que 7 criteres sur 12. Renvoyer une recherche a Hektor
-- l'APPAUVRIT, et le garde-fou du worker s'en apercoit : il compare l'empreinte du contenu,
-- constate une difference, conclut a tort que « quelqu'un a modifie dans Hektor », et
-- bloque. C'est ce qui a bloque le contact 602197 -- personne n'avait rien modifie chez
-- Hektor, l'app ne savait simplement pas tout dire.
--
-- LE GESTE tient en un mot : dans les deux fonctions d'edition, la valeur ecrite dans
-- app_search_pending.push_search devient NULL.
--
-- ET LE MECANISME FAIT LE RESTE TOUT SEUL -- rien d'autre n'est touche :
--   la ligne est toujours creee      -> la protection joue, le run de nuit ne l'ecrase pas
--   push_search est vide             -> la boucle d'enfilage l'ignore
--                                       (etape 1 : « and push_search is not null »)
--   aucune suppression ne l'atteint  -> (0a) exige un push_job_id, (0a-bis) un conflit,
--                                       (0b) et (0c) un push_job_id
--   => la ligne survit indefiniment. LE REGISTRE NAIT TOUT SEUL.
--
-- Pas de table neuve, pas de colonne neuve, pas de cron touche. Le discriminant existait
-- deja dans le code : il n'avait jamais ete utilise dans ce sens.
--
-- LES DEUX CHEMINS SONT FERMES : app_edit_search_optimistic (le negociateur) ET
-- app_espace_edit_search_optimistic (l'espace client). Un acquereur qui affine sa recherche
-- depuis son espace ne la renvoie plus chez Hektor non plus.
--
-- ⚠ CONSEQUENCE POUR TES CLIENTS, a savoir : un acquereur qui affine sa recherche dans son
-- espace croira peut-etre que son negociateur la verra dans Hektor. Ce n'est plus le cas.
--
-- VOLUME CONCERNE, mesure sur 90 jours : 24 modifications, 2 ajouts, 2 suppressions.
-- 28 envois, 0 erreur. Ce geste n'arrete presque rien AUJOURD'HUI -- il compte pour
-- l'etape 2, quand les negociateurs affineront vraiment.
--
-- SIGNATURE INCHANGEE -> create or replace, donc AUCUN droit perdu.
--
-- VERIFIE : une ligne de registre (push_search vide) survit a DEUX passages de la mise en
-- file, push_job_id reste vide, push_attempts reste a 0, et 0 travail est cree. Essai fait
-- sur un identifiant inexistant (999999999) puis retire ; etat final 0/0/0 sur les trois
-- tables d'attente.
--
-- NON VERIFIE, et assume : le chemin de bout en bout par la fonction elle-meme. Elle exige
-- que le contact existe dans app_contact_current, et je n'ai pas voulu editer la recherche
-- d'un vrai client pour un essai. Le changement textuel est verifie sur les deux fonctions.
--
-- L'ALARME EST ADAPTEE EN MEME TEMPS (monitoring/check_gti_health.py). Sans quoi
-- data.recherche_divergente passerait en CRITICAL des la premiere recherche affinee --
-- alors que sa divergence est desormais VOULUE. Une sentinelle qui sonne quand tout va bien
-- cesse d'etre lue. Les recherches du registre en sortent ; elles se comptent dans
-- app_doublure_journal. Le registre etant descendu dans le MEME instantane que la doublure,
-- la ligne de registre et la valeur divergente arrivent ensemble : pas de fausse alerte.
--
-- RETOUR ARRIERE : remettre v_search. ⚠ Les affinages accumules partiraient alors chez
-- Hektor D'UN COUP. Plus on attend, plus le retour arriere est brutal.
-- =====================================================================

do $$
declare
  r record;
  src text;
  nouveau text;
  n int := 0;
begin
  for r in
    select p.oid, p.proname
      from pg_proc p join pg_namespace ns on ns.oid = p.pronamespace
     where ns.nspname = 'public'
       and p.proname in ('app_edit_search_optimistic', 'app_espace_edit_search_optimistic')
  loop
    src := pg_get_functiondef(r.oid);

    -- Motif verifie, pas devine : il doit apparaitre exactement une fois.
    if (length(src) - length(replace(src, 'v_base, v_search,', ''))) / length('v_base, v_search,') <> 1 then
      raise exception 'MOTIF ABSENT OU MULTIPLE dans % -- rien modifie', r.proname;
    end if;

    nouveau := replace(src, 'v_base, v_search,',
                            'v_base, null /* C.3 24/08 : plus d''envoi vers Hektor */,');
    if nouveau = src then
      raise exception 'REMPLACEMENT SANS EFFET dans %', r.proname;
    end if;

    execute nouveau;
    n := n + 1;
  end loop;

  if n <> 2 then
    raise exception 'attendu 2 fonctions, % corrigee(s)', n;
  end if;
  raise notice 'porte sortante des recherches fermee sur % fonctions', n;
end $$;
