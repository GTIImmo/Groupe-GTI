-- ═══════════════════════════════════════════════════════════════════════════
-- 26bis-COUPLES — LE LIEN DE MENAGE SE MAINTIENT CHAQUE NUIT      21/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Le patch du meme jour a pose le lien dans notre serie pour les 37 398 lignes
-- traduisibles. Sans entretien, il se viderait tout seul : chaque nuit, la
-- couche des contacts est refaite depuis le miroir, et les fiches neuves
-- arriveraient sans lui.
--
-- ⚠ LA LECON DU 31/08, MOT POUR MOT : « une migration a rempli les 19 tables EN
--   UNE FOIS ; l'entretien mis en place ensuite ne couvrait qu'UNE table. Les 18
--   autres n'ont plus jamais ete alimentees -- 5 288 lignes nees vides en 7
--   jours. Rien ne s'effacait : c'est le NEUF qui arrivait vide. » On ne repose
--   donc pas une migration sans son entretien, le meme jour.
--
-- Il rejoint la propagation nocturne qui existe deja (etape « phase2 propager
-- numeros de contact »), avec son carnet : on saura combien elle a eu a faire.
--
-- RETOUR ARRIERE : la definition d'avant est dans le commit de ce patch.
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.app_contact_id_propager()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
declare
  cible  text;
  n      integer;
  total  integer := 0;
  detail jsonb := '{}'::jsonb;
  cibles constant text[] := array[
    'app_contact_relation_current',
    'app_rapprochement',
    'app_contact_search_current',
    'app_search_count_high_water',
    'app_email_envoi',
    'app_proposition',
    'app_google_calendar_event_link',
    'app_relance_rapprochement',
    'app_bien_acquereur_statut',
    'app_espace_visite_request',
    'app_console_deleted_contact_log',
    'app_contact_consent',
    'app_contact_override',
    'app_contact_pending',
    'app_contact_duplicate_member_current',
    'app_espace_message',
    'app_search_pending',
    'app_pending_resolution'
  ];
begin
  foreach cible in array cibles loop
    execute format(
      'update public.%I t
          set app_contact_id = c.app_contact_id
         from public.app_contact_current c
        where c.hektor_contact_id = t.hektor_contact_id
          and c.app_contact_id is not null
          and t.app_contact_id is null
          and t.hektor_contact_id is not null', cible);
    get diagnostics n = row_count;
    if n > 0 then
      detail := detail || jsonb_build_object(cible, n);
    end if;
    total := total + n;
  end loop;

  -- ── 26bis-COUPLES, 21/09/2026 : LE LIEN DE MENAGE, DANS NOTRE SERIE ────
  -- Meme geste, autre colonne : le lien pointe vers un CONTACT, donc il se
  -- traduit par la meme auto-jointure. Ici la source et la cible sont la meme
  -- table -- c'est le conjoint qu'on va chercher.
  -- Il reste des liens intraduisibles (conjoint hors perimetre de l'app, ou
  -- fiche supprimee chez Hektor) : ils gardent leur lien Hektor et attendent.
  -- La vue app_v_couples_non_traduits les compte.
  update public.app_contact_current c
     set app_couple_contact_id = p.app_contact_id
    from public.app_contact_current p
   where coalesce(c.hektor_couple_contact_id, '') <> ''
     and p.hektor_contact_id = c.hektor_couple_contact_id
     and p.app_contact_id is not null
     and c.app_couple_contact_id is null;
  get diagnostics n = row_count;
  if n > 0 then
    detail := detail || jsonb_build_object('app_contact_current.couple', n);
  end if;
  total := total + n;

  -- LE CARNET. La sentinelle lit l'etat APRES cette reparation : elle affichera
  -- 0 que le flux soit sain ou non. Ce qui se mesure vraiment, c'est COMBIEN la
  -- reparation a eu a faire -- et sans trace, la valeur de retour se perd.
  -- Meme lecon que le balayage des recherches, apprise le 21/08.
  insert into public.app_contact_id_propagation_log(run_at, total, detail)
  values (now(), total, detail)
  on conflict (run_at) do nothing;

  return jsonb_build_object('total', total, 'detail', detail);
end
$function$
;
