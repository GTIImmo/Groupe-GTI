-- ═══════════════════════════════════════════════════════════════════════════
-- C-13  23/09/2026 — LA BASCULE : LE CONTACT PREND SON NUMERO A NOUS
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ⚠ CE FICHIER NE SE JOUE PAS TOUT SEUL. Il pose une FONCTION, qui sait
--   compter avant d'agir. On l'appelle d'abord a blanc, on lit les comptes,
--   ON LES MONTRE, et seulement ensuite on applique.
--       select public.app_bascule_identite_contact(false);   -- compter
--       select public.app_bascule_identite_contact(true);    -- appliquer
--
-- CE QUE LA BASCULE VEUT DIRE : `hektor_contact_id` cesse d'etre le numero que
-- Hektor a donne pour devenir LE NOTRE (`app_contact_id`, >= 10 000 000). Le
-- numero de Hektor ne disparait pas : il vit dans `hektor_target_id`, pose
-- depuis L4-c ④, et c'est lui qu'on envoie a Hektor.
--
-- ═══ TROIS FAMILLES, TROIS TRAITEMENTS -- et c'est tout le sujet ═══════════
--
-- ① TRADUIRE EN PLACE. Leur cle ne bouge pas.
--       app_contact_current        PK = hektor_contact_id, et les deux plages
--                                  sont DISJOINTES (< 10 M / >= 10 M) : aucune
--                                  collision possible pendant la mise a jour.
--       app_contact_search_current PK = contact_search_key, qui est FIGE par
--                                  app_search_registry et retrouve par les DEUX
--                                  numeros. C'est ce qui protege les 456 000
--                                  lignes qui pendent dessous.
--
-- ② VIDER, ET LAISSER LE BUILD REFAIRE. Leur cle est une EMPREINTE calculee
--    SUR le numero du contact : elle change forcement, et aucun UPDATE SQL ne
--    peut la recalculer (c'est un sha1 Python sur un JSON).
--       app_contact_relation_current        PK = relation_key
--       app_contact_duplicate_group_current PK = duplicate_group_id
--       app_contact_duplicate_member_current PK = (group, contact)
--    ⚠ NE PAS LES TRADUIRE : on obtiendrait les ANCIENNES lignes sous leur
--      ancienne cle PLUS les nouvelles sous la nouvelle -- des doublons, pas
--      une traduction.
--    ⚠ VERIFIE LE 23/09 : RIEN ne pend sur ces deux empreintes. Aucune cle
--      etrangere, et les deux seuls objets qui les citent sont les vues
--      homonymes au pluriel. Les vider n'orpheline rien.
--
-- ③ TRADUIRE LES TABLES QUI NE SE RECONSTRUISENT JAMAIS. Sans cela, elles
--    restent sur l'ancien numero et les 35 fonctions et vues qui cousent le
--    reconstruit au fige ne joignent plus rien -- SANS LEVER D'ERREUR, en
--    rendant zero ligne.
--
-- ═══ CE QU'ON NE TRADUIT PAS, ET POURQUOI ═════════════════════════════════
--       app_console_deleted_contact_log   C'EST UN JOURNAL. Il dit sous quel
--                                         numero une fiche a ete supprimee.
--                                         Une trace qu'on reecrit ne trace plus.
--       app_contact_consent               trace RGPD datee, meme raison.
--       app_affaire_ledger                `hektor_acquereur_id` EST la trace de
--                                         ce que Hektor a dit ; sa doublure
--                                         `app_contact_id` est deja posee.
--       app_affaire_personne_ecart        2 lignes, pas de doublure, objet
--                                         transitoire. Mesure, assume, ecrit.
--
-- ⚠ L'ORDRE EST IMPOSE : ce patch d'abord, PUIS la descente de correspondance,
--   PUIS le build, PUIS le push avec --reset-push-state. Voir la procedure
--   complete dans notice/AUDIT_COMPLET_AVANT_BASCULE_2026-09-23.md.
--
-- RETOUR ARRIERE : la fonction inverse est ecrite dessous
--   (app_bascule_identite_contact_annuler). Elle se sert de hektor_target_id,
--   qui n'est jamais touche. Plus la sauvegarde locale VACUUM INTO.
-- ═══════════════════════════════════════════════════════════════════════════

create or replace function public.app_bascule_identite_contact(p_appliquer boolean default false)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  n       integer;
  detail  jsonb := '{}'::jsonb;
  cible   text;
  figees  constant text[] := array[
    'app_rapprochement',
    'app_search_count_high_water',
    'app_email_envoi',
    'app_proposition',
    'app_relance_rapprochement',
    'app_google_calendar_event_link',
    'app_bien_acquereur_statut',
    'app_espace_visite_request',
    'app_espace_message',
    'app_pending_resolution',
    'app_contact_pending',
    'app_contact_override',
    'app_search_pending'
  ];
  restants integer;
  deja     integer;
begin
  -- ── LES DEUX REFUS, AVANT TOUTE ECRITURE ────────────────────────────────
  -- (a) une fiche sans doublure ne peut pas basculer : elle perdrait son
  --     identite au lieu d'en changer.
  select count(*) into restants
    from app_contact_current
   where app_contact_id is null;
  if restants > 0 then
    -- ⚠ LE MESSAGE CORRIGE LE 23/09, APRES L'AVOIR VECU. Il nommait
    --   app_contact_id_propager seul -- or propager RECOPIE app_contact_id
    --   depuis app_contact_current, et pour ces contacts-la cette colonne est
    --   justement vide. C'est pousser_numeros_contact.py qui la remplit, depuis
    --   le registre local. DEUX gestes, dans cet ordre.
    return jsonb_build_object('refus', format(
      '%s contact(s) sans app_contact_id. DEUX gestes, dans cet ordre : '
      '(1) python phase2\identite\pousser_numeros_contact.py  -- fait monter les '
      'numeros du registre local ; (2) rpc/app_contact_id_propager -- les recopie '
      'dans les tables satellites.', restants));
  end if;

  -- (b) une fiche sans case cible perdrait son numero de Hektor pour toujours.
  select count(*) into restants
    from app_contact_current
   where coalesce(hektor_target_id, '') = ''
     and hektor_contact_id ~ '^[0-9]+$'
     and hektor_contact_id::bigint < 10000000;
  if restants > 0 then
    return jsonb_build_object('refus', format(
      '%s contact(s) sans hektor_target_id : le numero de Hektor serait PERDU.', restants));
  end if;

  select count(*) into deja
    from app_contact_current
   where hektor_contact_id ~ '^[0-9]+$'
     and hektor_contact_id::bigint >= 10000000;
  detail := detail || jsonb_build_object('_deja_bascules', deja);

  if not p_appliquer then
    -- ── MODE A BLANC : on compte ce qui bougerait, on n'ecrit rien ─────────
    select count(*) into n from app_contact_current
     where hektor_contact_id ~ '^[0-9]+$' and hektor_contact_id::bigint < 10000000;
    detail := detail || jsonb_build_object('a_traduire_app_contact_current', n);
    select count(*) into n from app_contact_search_current
     where hektor_contact_id ~ '^[0-9]+$' and hektor_contact_id::bigint < 10000000;
    detail := detail || jsonb_build_object('a_traduire_app_contact_search_current', n);
    select count(*) into n from app_contact_relation_current;
    detail := detail || jsonb_build_object('a_vider_app_contact_relation_current', n);
    select count(*) into n from app_contact_duplicate_group_current;
    detail := detail || jsonb_build_object('a_vider_app_contact_duplicate_group_current', n);
    select count(*) into n from app_contact_duplicate_member_current;
    detail := detail || jsonb_build_object('a_vider_app_contact_duplicate_member_current', n);
    foreach cible in array figees loop
      execute format(
        'select count(*) from public.%I where app_contact_id is not null
           and hektor_contact_id is not null
           and hektor_contact_id <> app_contact_id::text', cible) into n;
      if n > 0 then detail := detail || jsonb_build_object(cible, n); end if;
    end loop;
    return jsonb_build_object('mode', 'a_blanc', 'detail', detail);
  end if;

  -- ── ① TRADUIRE EN PLACE ─────────────────────────────────────────────────
  -- Les recherches D'ABORD : leur cle est figee, elles ne dependent de rien.
  update app_contact_search_current
     set hektor_contact_id = app_contact_id::text
   where app_contact_id is not null
     and hektor_contact_id ~ '^[0-9]+$'
     and hektor_contact_id::bigint < 10000000;
  get diagnostics n = row_count;
  detail := detail || jsonb_build_object('app_contact_search_current', n);

  update app_contact_current
     set hektor_contact_id = app_contact_id::text
   where app_contact_id is not null
     and hektor_contact_id ~ '^[0-9]+$'
     and hektor_contact_id::bigint < 10000000;
  get diagnostics n = row_count;
  detail := detail || jsonb_build_object('app_contact_current', n);

  -- ── ② VIDER CE QUE LE BUILD REFERA ──────────────────────────────────────
  select count(*) into n from app_contact_duplicate_member_current;
  delete from app_contact_duplicate_member_current;
  detail := detail || jsonb_build_object('_vide_duplicate_member', n);
  select count(*) into n from app_contact_duplicate_group_current;
  delete from app_contact_duplicate_group_current;
  detail := detail || jsonb_build_object('_vide_duplicate_group', n);
  select count(*) into n from app_contact_relation_current;
  delete from app_contact_relation_current;
  detail := detail || jsonb_build_object('_vide_relation', n);

  -- ── ③ LES TABLES QUI NE SE RECONSTRUISENT JAMAIS ────────────────────────
  foreach cible in array figees loop
    execute format(
      'update public.%I
          set hektor_contact_id = app_contact_id::text
        where app_contact_id is not null
          and hektor_contact_id is not null
          and hektor_contact_id <> app_contact_id::text', cible);
    get diagnostics n = row_count;
    if n > 0 then detail := detail || jsonb_build_object(cible, n); end if;
  end loop;

  return jsonb_build_object('mode', 'applique', 'detail', detail);
end
$function$;

comment on function public.app_bascule_identite_contact(boolean) is
  'C-13 23/09/2026 : fait passer hektor_contact_id a NOTRE numero (app_contact_id). Traduit en place ce dont la cle ne bouge pas (contacts, recherches -- nom fige), VIDE ce dont la cle est une empreinte calculee sur le numero (relations, doublons : le build les refait), traduit les 13 tables jamais reconstruites, et NE TOUCHE PAS aux journaux. Refuse tant qu''un contact n''a pas sa doublure ou sa case cible. A blanc par defaut.';

grant execute on function public.app_bascule_identite_contact(boolean) to service_role;


-- ═══════════════════════════════════════════════════════════════════════════
-- LE RETOUR ARRIERE — il se sert de hektor_target_id, jamais touche
-- ═══════════════════════════════════════════════════════════════════════════
-- ⚠ Il ne rend PAS les relations et les doublons : ceux-la, c'est le build qui
--   les refait, dans un sens comme dans l'autre. C'est voulu -- ils sont
--   reconstructibles par definition, et les recalculer est plus sur que les
--   ressusciter.
create or replace function public.app_bascule_identite_contact_annuler(p_appliquer boolean default false)
returns jsonb
language plpgsql
security definer
set search_path to 'public'
as $function$
declare
  n      integer;
  detail jsonb := '{}'::jsonb;
  cible  text;
  figees constant text[] := array[
    'app_rapprochement','app_search_count_high_water','app_email_envoi',
    'app_proposition','app_relance_rapprochement','app_google_calendar_event_link',
    'app_bien_acquereur_statut','app_espace_visite_request','app_espace_message',
    'app_pending_resolution','app_contact_pending','app_contact_override','app_search_pending'
  ];
begin
  if not p_appliquer then
    select count(*) into n from app_contact_current
     where hektor_contact_id ~ '^[0-9]+$' and hektor_contact_id::bigint >= 10000000
       and coalesce(hektor_target_id,'') <> '';
    return jsonb_build_object('mode','a_blanc','a_ramener', n);
  end if;

  -- Les tables figees d'abord : on les ramene au numero de Hektor en passant
  -- par la couche, qui porte encore les deux.
  foreach cible in array figees loop
    execute format(
      'update public.%I t
          set hektor_contact_id = c.hektor_target_id
         from public.app_contact_current c
        where c.app_contact_id::text = t.hektor_contact_id
          and coalesce(c.hektor_target_id, '''') <> ''''', cible);
    get diagnostics n = row_count;
    if n > 0 then detail := detail || jsonb_build_object(cible, n); end if;
  end loop;

  update app_contact_search_current s
     set hektor_contact_id = c.hektor_target_id
    from app_contact_current c
   where c.hektor_contact_id = s.hektor_contact_id
     and coalesce(c.hektor_target_id,'') <> '';
  get diagnostics n = row_count;
  detail := detail || jsonb_build_object('app_contact_search_current', n);

  update app_contact_current
     set hektor_contact_id = hektor_target_id
   where coalesce(hektor_target_id,'') <> ''
     and hektor_contact_id ~ '^[0-9]+$'
     and hektor_contact_id::bigint >= 10000000;
  get diagnostics n = row_count;
  detail := detail || jsonb_build_object('app_contact_current', n);

  delete from app_contact_duplicate_member_current;
  delete from app_contact_duplicate_group_current;
  delete from app_contact_relation_current;
  detail := detail || jsonb_build_object('_vide', 'relations et doublons : le build les refait');

  return jsonb_build_object('mode','applique','detail', detail);
end
$function$;

comment on function public.app_bascule_identite_contact_annuler(boolean) is
  'C-13 23/09/2026 : defait la bascule en se servant de hektor_target_id, qui n''est jamais touche. Ne ressuscite pas les relations ni les doublons -- le build les refait, c''est plus sur que de les recreer. A blanc par defaut.';

grant execute on function public.app_bascule_identite_contact_annuler(boolean) to service_role;
