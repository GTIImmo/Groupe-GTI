-- =====================================================================
-- LA SENTINELLE REGARDE LES 18 TABLES, PLUS SEULEMENT LA FICHE
-- Date : 2026-08-31
--
-- CE QU'ELLE N'A PAS VU. La sonde posée le 25/08 (`data.contact_sans_numero`)
-- ne surveille qu'**une** table : `app_contact_current`. Cette table-là est
-- entretenue chaque nuit par `registre_contacts.py` + `pousser_numeros_contact.py`,
-- et elle affiche **0 manquant**. La sentinelle est donc au vert.
--
-- Pendant ce temps, dans les **18 autres** tables, le trou se creuse :
--
--     25/08     161 lignes nouvelles sans numero
--     26/08   1 301
--     27/08   3 216
--     28/08      29
--     29/08     226
--     30/08      20
--     31/08     335
--     ----------------
--     7 jours 5 288
--
-- POURQUOI. Le 25/08, une migration a rempli les 19 tables d'un coup
-- (144 985 lignes). Depuis, la couche contacts LOCALE est refaite chaque nuit
-- (`replace_table_rows` = DELETE + INSERT) et **elle ne porte pas la colonne** :
-- le numero de l'app ne vit localement que dans la table de correspondance
-- `app_contact`. Le push envoie donc des lignes sans ce numero. Les lignes que
-- Supabase connait deja gardent le leur (l'upsert ne mentionne pas la colonne,
-- il n'y touche pas) ; les lignes NOUVELLES naissent vides.
--
-- Rien ne s'efface : c'est le neuf qui arrive vide.
--
-- ─────────────────────────────────────────────────────────────────────
-- CE QUE LA VUE COMPTE, ET CE QU'ELLE ECARTE VOLONTAIREMENT
--
-- Elle ne retient que le RATTRAPABLE : une ligne dont le contact existe et
-- porte un numero, mais qui ne le porte pas elle-meme. Sont donc exclus :
--
--   * les lignes SANS contact rattache -- `app_email_envoi` en a 58, ce sont
--     des envois qui ne visent personne. Autre sujet.
--   * les ORPHELINES -- 35 dans `app_search_count_high_water`, des compteurs
--     qui pointent un contact disparu. DEJA SIGNALEES le 25/08 et laissees
--     telles quelles : « signale, pas corrige : table de compteurs ».
--
-- Une sentinelle qui melange le rattrapable et l'irrattrapable ne redescend
-- jamais a zero, et on cesse de la lire.
-- ─────────────────────────────────────────────────────────────────────
--
-- SEUIL 150, ET NON 0 -- meme raison qu'au 25/08, et elle est bonne : un
-- contact cree dans la journee arrive dans Supabase AVANT d'entrer en local.
-- Ses lignes n'ont leur numero que le lendemain. Un seuil a 0 sonnerait chaque
-- matin pour un decalage normal.
--
-- ⚠ ELLE SONNERA DES SA POSE : 5 288 aujourd'hui. C'est voulu -- c'est la
-- mesure d'avant. Elle doit redescendre sous 150 quand la colonne sera portee
-- par la couche locale.
-- =====================================================================

create or replace view public.app_contacts_sans_numero as
with numerote as (
  select hektor_contact_id::text as h, app_contact_id
    from public.app_contact_current
   where app_contact_id is not null
),
lignes as (
  select 'app_contact_relation_current'   as source, hektor_contact_id::text as h from public.app_contact_relation_current   where app_contact_id is null
  union all select 'app_rapprochement',              hektor_contact_id::text from public.app_rapprochement                   where app_contact_id is null
  union all select 'app_contact_search_current',     hektor_contact_id::text from public.app_contact_search_current          where app_contact_id is null
  union all select 'app_search_count_high_water',    hektor_contact_id::text from public.app_search_count_high_water         where app_contact_id is null
  union all select 'app_email_envoi',                hektor_contact_id::text from public.app_email_envoi                     where app_contact_id is null
  union all select 'app_proposition',                hektor_contact_id::text from public.app_proposition                     where app_contact_id is null
  union all select 'app_google_calendar_event_link', hektor_contact_id::text from public.app_google_calendar_event_link      where app_contact_id is null
  union all select 'app_relance_rapprochement',      hektor_contact_id::text from public.app_relance_rapprochement           where app_contact_id is null
  union all select 'app_bien_acquereur_statut',      hektor_contact_id::text from public.app_bien_acquereur_statut           where app_contact_id is null
  union all select 'app_espace_visite_request',      hektor_contact_id::text from public.app_espace_visite_request           where app_contact_id is null
  union all select 'app_console_deleted_contact_log',hektor_contact_id::text from public.app_console_deleted_contact_log     where app_contact_id is null
  union all select 'app_contact_consent',            hektor_contact_id::text from public.app_contact_consent                 where app_contact_id is null
  union all select 'app_contact_override',           hektor_contact_id::text from public.app_contact_override                where app_contact_id is null
  union all select 'app_contact_pending',            hektor_contact_id::text from public.app_contact_pending                 where app_contact_id is null
  union all select 'app_contact_duplicate_member_current', hektor_contact_id::text from public.app_contact_duplicate_member_current where app_contact_id is null
  union all select 'app_espace_message',             hektor_contact_id::text from public.app_espace_message                  where app_contact_id is null
  union all select 'app_search_pending',             hektor_contact_id::text from public.app_search_pending                  where app_contact_id is null
  union all select 'app_pending_resolution',         hektor_contact_id::text from public.app_pending_resolution              where app_contact_id is null
)
select l.source,
       l.h as hektor_contact_id,
       n.app_contact_id as numero_disponible
  from lignes l
  join numerote n on n.h = l.h            -- jointure : ecarte orphelines ET lignes sans contact
 where l.h is not null and trim(l.h) <> '';

comment on view public.app_contacts_sans_numero is
  'Lignes qui POURRAIENT porter le numero de contact de l''app et ne le portent pas '
  '(le contact existe et son numero est connu). Ecarte volontairement les orphelines '
  'et les lignes sans contact rattache : une sentinelle qui melange le rattrapable et '
  'l''irrattrapable ne redescend jamais a zero. Posee le 31/08 -- la sonde du 25/08 ne '
  'regardait que app_contact_current, la seule table entretenue, donc la seule au vert.';

revoke all on public.app_contacts_sans_numero from public, anon;
grant select on public.app_contacts_sans_numero to service_role;
