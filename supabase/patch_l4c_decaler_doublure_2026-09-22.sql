-- ═══════════════════════════════════════════════════════════════════════════
-- L4-c ⓪ — LA MOITIE SUPABASE DU DECALAGE                        22/09/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Jumelle de `phase2/identite/decaler_doublure_contacts.py`, qui fait la moitie
-- LOCALE. Les deux doivent tomber dans la MEME fenetre : une moitie decalee et
-- l'autre non, c'est exactement la fracture qu'on cherche a empecher.
--
-- POURQUOI DEUX MOITIES. Mesure du 22/09 : sur les 26 tables locales qui
-- portent la doublure, 20 sont des COPIES descendues de Supabase
-- (`sb_pull_state`). Ecrire dedans est interdit -- la descente de 7 h 30 les
-- refait et effacerait le travail en silence. Pour celles-la, c'est Supabase
-- qu'il faut decaler ; la descente rapportera les nouvelles valeurs.
--
-- LE PROBLEME QU'ON FERME : les deux series de numeros de contact se
-- recouvrent. 194 683 numeros existent dans les deux et designent des
-- personnes DIFFERENTES (mesure confirmee par deux chemins independants).
-- Apres ce decalage :
--     < 10 000 000   c'est un numero de Hektor
--     >= 10 000 000  c'est le notre
-- et un numero dit enfin d'ou il vient.
--
-- ⛔ GARDE-FOU DE COLLISION, GLOBAL. Il regarde les 20 tables ENSEMBLE, pas une
--   par une : un numero designe la meme personne partout, l'espace des numeros
--   est commun. La premiere version du script local se trompait la-dessus et
--   n'aurait rien vu -- alors que le contact n°1 serait tombe sur 10 000 001,
--   numero d'un contact d'essai vivant dans une AUTRE table.
--
-- IDEMPOTENT : les valeurs deja >= 10 000 000 ne sont pas touchees. Rejouer
-- n'ecrit rien.
--
-- USAGE :
--     select * from public.app_decaler_doublure(false);   -- montre, n'ecrit pas
--     select * from public.app_decaler_doublure(true);    -- ecrit
--     select * from public.app_decaler_doublure(true, -1); -- RETOUR ARRIERE
-- ═══════════════════════════════════════════════════════════════════════════

create or replace function public.app_decaler_doublure(
  p_appliquer boolean default false,
  p_sens integer default 1
)
returns table(objet text, detail text)
language plpgsql
as $function$
declare
  v_decalage constant bigint := 10000000;
  v_tables text[] := array[
    'app_affaire_ledger','app_bien_acquereur_statut','app_console_deleted_contact_log',
    'app_contact_consent','app_contact_current','app_contact_duplicate_member_current',
    'app_contact_override','app_contact_pending','app_contact_relation_current',
    'app_contact_search_current','app_email_envoi','app_espace_message',
    'app_espace_visite_request','app_google_calendar_event_link','app_pending_resolution',
    'app_proposition','app_rapprochement','app_relance_rapprochement',
    'app_search_count_high_water','app_search_pending'];
  v_table text;
  v_occupes bigint[] := '{}';
  v_a_bouger bigint[] := '{}';
  v_collisions bigint[];
  v_n bigint;
  v_total bigint := 0;
begin
  if p_sens not in (1, -1) then
    raise exception 'p_sens vaut 1 (monter) ou -1 (redescendre), pas %', p_sens;
  end if;

  -- ── 1. LE GARDE-FOU, GLOBAL, AVANT TOUTE ECRITURE ────────────────────────
  foreach v_table in array v_tables loop
    if p_sens = 1 then
      execute format(
        'select coalesce(array_agg(distinct app_contact_id), ''{}'') from public.%I where app_contact_id >= $1',
        v_table) into v_collisions using v_decalage;
      v_occupes := v_occupes || v_collisions;
      execute format(
        'select coalesce(array_agg(distinct app_contact_id), ''{}'') from public.%I where app_contact_id is not null and app_contact_id < $1',
        v_table) into v_collisions using v_decalage;
      v_a_bouger := v_a_bouger || v_collisions;
    else
      execute format(
        'select coalesce(array_agg(distinct app_contact_id), ''{}'') from public.%I where app_contact_id is not null and app_contact_id < $1',
        v_table) into v_collisions using v_decalage;
      v_occupes := v_occupes || v_collisions;
      execute format(
        'select coalesce(array_agg(distinct app_contact_id), ''{}'') from public.%I where app_contact_id >= $1',
        v_table) into v_collisions using v_decalage;
      v_a_bouger := v_a_bouger || v_collisions;
    end if;
  end loop;

  select coalesce(array_agg(x), '{}') into v_collisions
    from unnest(v_a_bouger) as x
   where (x + p_sens * v_decalage) = any(v_occupes);

  if array_length(v_collisions, 1) > 0 then
    raise exception
      'REFUS : % numero(s) tomberaient sur un numero deja pris (ex. % -> %). Les liberer d''abord.',
      array_length(v_collisions, 1), v_collisions[1], v_collisions[1] + p_sens * v_decalage;
  end if;

  -- ── 2. LE COMPTE, PUIS L'ECRITURE ────────────────────────────────────────
  foreach v_table in array v_tables loop
    if p_sens = 1 then
      execute format('select count(*) from public.%I where app_contact_id is not null and app_contact_id < $1', v_table)
        into v_n using v_decalage;
    else
      execute format('select count(*) from public.%I where app_contact_id >= $1', v_table)
        into v_n using v_decalage;
    end if;
    v_total := v_total + v_n;
    if v_n > 0 then
      objet := v_table; detail := v_n::text || ' ligne(s)'; return next;
      if p_appliquer then
        if p_sens = 1 then
          execute format('update public.%I set app_contact_id = app_contact_id + $1 where app_contact_id is not null and app_contact_id < $1', v_table)
            using v_decalage;
        else
          execute format('update public.%I set app_contact_id = app_contact_id - $1 where app_contact_id >= $1', v_table)
            using v_decalage;
        end if;
      end if;
    end if;
  end loop;

  objet := 'TOTAL';
  detail := v_total::text || ' ligne(s) ' ||
            case when p_sens = 1 then 'a monter' else 'a redescendre' end ||
            case when p_appliquer then ' -- ECRIT' else ' -- dry-run, rien ecrit' end;
  return next;
end
$function$;

comment on function public.app_decaler_doublure(boolean, integer) is
  'L4-c 22/09/2026 : deplace app_contact_id de 10 000 000 pour que la doublure sorte de la plage de Hektor. Garde-fou de collision GLOBAL (les 20 tables ensemble). Idempotent. p_sens = -1 pour le retour arriere. A jouer dans la MEME fenetre que phase2/identite/decaler_doublure_contacts.py.';

revoke all on function public.app_decaler_doublure(boolean, integer) from public, anon, authenticated;
grant execute on function public.app_decaler_doublure(boolean, integer) to service_role;
