-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · P2 — RÉPÉTITION (rien ne reste)                          31/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- Joue le patch EN ENTIER dans une transaction, crée un couple d'essai par la
-- fonction (personne 1 fictive 29999999), mesure, puis LÈVE « ESSAI ANNULE » :
-- tout est annulé. ⚠ Un seul effet survit : un numéro de la séquence
-- app_contact_identite_seq est consommé (un trou, comme le 21/10).
-- Attendu : toutes les cases à « ok ».
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;


-- 1. LA COLONNE (patch joue a l'identique)
alter table public.app_contact_current add column if not exists couple_json jsonb;
comment on column public.app_contact_current.couple_json is
  'COUPLES P2 (31/10/2026) : resume du conjoint, pose sur la PREMIERE fiche d''un couple par la nuit (conjoints_des_couples.py) et par app_contact_creer_conjoint.';

-- 2. LA CLE DE BATTEMENT
insert into public.app_worker_registry
  (worker_key, worker_name, worker_role, worker_type, criticality, frequency,
   status, owner, script_path, expected_max_runtime_minutes, monitoring_domain,
   source_notes)
values
  ('phase2.conjoints_couples',
   'Conjoints des couples (resume sur la premiere fiche)',
   'Pose couple_json sur chaque premiere fiche d''un couple et marque « conjoint » la seconde '
   'fiche nommee, qui part alors vers l''app. Sans lui, l''ecran ne voit pas le conjoint. '
   'Interrupteur APP_COUPLE_CONJOINT (.env).',
   'python_worker', 'medium', 'optional_pipeline_step',
   'active', 'frederic',
   'phase2\contacts\conjoints_des_couples.py',
   5, 'business',
   'Ajoutee le 31/10/2026 (couples, P2). Ne lit et n''ecrit que la couche locale ; aucune '
   'requete chez Hektor. Mesure sur copie : ~8 s.')
on conflict (worker_key) do nothing;

-- 3. LA PAIRE NÉE DANS L'APP : LE RÉSUMÉ TOUT DE SUITE
-- L'ancre est sur UNE ligne (leçon 30).
DO $patch$
DECLARE
    fonction  text := 'public.app_contact_creer_conjoint(jsonb,text,text,text)';
    empreinte text := '2523f1f03c8b9c7485749d4cb7c787f2';
    marque    text := 'COUPLES · P2 (31/10/2026)';
    ancre     text := $a$  return v_m2;
$a$;
    bloc      text := $b$  -- === COUPLES · P2 (31/10/2026) : LA PERSONNE 1 CONNAIT SON CONJOINT ===
  -- Meme forme que la nuit (phase2/contacts/conjoints_des_couples.py), qui confirme.
  update public.app_contact_current p1
     set couple_json = jsonb_build_object(
           'etat', 'nomme', 'autres', 0,
           'conjoint', jsonb_build_object(
              'id', p2.hektor_contact_id, 'hektor_id', p2.hektor_target_id,
              'civilite', p2.civilite, 'prenom', p2.prenom, 'nom', p2.nom,
              'telephone', p2.phone_primary, 'email', p2.email,
              'archive', false, 'envoye', true))
    from public.app_contact_current p2
   where p1.hektor_contact_id = p_identite
     and p2.hektor_contact_id = v_m2;
  update public.app_contact_current
     set couple_role = 'conjoint'
   where hektor_contact_id = v_m2;
  -- === fin couples P2 ===
$b$;
    src     text;
    combien int;
BEGIN
    src   := replace(pg_get_functiondef(fonction::regprocedure), chr(13), '');
    ancre := replace(ancre, chr(13), '');
    bloc  := replace(bloc,  chr(13), '');

    IF position(marque in src) > 0 THEN
        RAISE EXCEPTION '%', format('ARRET : le bloc P2 est DEJA dans %s. Rien n''est ecrit.', fonction);
    END IF;
    IF md5(src) <> empreinte THEN
        RAISE EXCEPTION '%', format('ARRET : %s a change depuis le 31/10 (empreinte %s, attendue %s). Rien n''est ecrit.',
                                    fonction, md5(src), empreinte);
    END IF;
    combien := (length(src) - length(replace(src, ancre, ''))) / length(ancre);
    IF combien <> 1 THEN
        RAISE EXCEPTION '%', format('ARRET : l''ancre apparait %s fois (1 attendue). Rien n''est ecrit.', combien);
    END IF;

    EXECUTE replace(src, ancre, bloc || ancre);
END
$patch$;

-- create or replace garde les droits ; on les reverifie quand meme (lecon du 13/10).
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from public;
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from anon;
revoke all on function public.app_contact_creer_conjoint(jsonb, text, text, text) from authenticated;
grant execute on function public.app_contact_creer_conjoint(jsonb, text, text, text) to service_role;


-- L'ESSAI
DO $essai$
DECLARE
  m2 text;
  r1 record;
  r2 record;
  t  text := '';
BEGIN
  insert into public.app_contact_current(hektor_contact_id, app_contact_id, nom, prenom, display_name,
      archive, typologies_json, source_hash, refreshed_at)
  values ('29999999', 29999999, 'ESSAI P2', 'Repetition', 'Repetition ESSAI P2',
      false, '[]'::jsonb, 'essai_p2', now());
  m2 := public.app_contact_creer_conjoint(
      '{"person_type":"couple","spouse_last_name":"ESSAI P2","spouse_first_name":"Conjointe","spouse_phone":"0600000000","spouse_email":"essai.p2@exemple.test"}'::jsonb,
      '29999999', null, null);
  select * into r1 from public.app_contact_current where hektor_contact_id = '29999999';
  select * into r2 from public.app_contact_current where hektor_contact_id = m2;
  t := t || ' | 01 colonne=' || (select count(*) from information_schema.columns
        where table_schema='public' and table_name='app_contact_current' and column_name='couple_json');
  t := t || ' | 02 battement=' || (select count(*) from public.app_worker_registry where worker_key='phase2.conjoints_couples');
  t := t || ' | 03 personne2=' || coalesce(m2, 'AUCUNE');
  t := t || ' | 04 etat=' || coalesce(r1.couple_json->>'etat', 'VIDE');
  t := t || ' | 05 conjoint_id=' || case when r1.couple_json->'conjoint'->>'id' = m2 then 'ok' else 'FAUX' end;
  t := t || ' | 06 prenom=' || coalesce(r1.couple_json->'conjoint'->>'prenom', 'VIDE');
  t := t || ' | 07 telephone=' || coalesce(r1.couple_json->'conjoint'->>'telephone', 'VIDE');
  t := t || ' | 08 email=' || coalesce(r1.couple_json->'conjoint'->>'email', 'VIDE');
  t := t || ' | 09 role_p2=' || coalesce(r2.couple_role, 'VIDE');
  t := t || ' | 10 lien_p1=' || case when r1.hektor_couple_contact_id = '29999999' then 'ok' else 'FAUX' end;
  t := t || ' | 11 lien_p2=' || case when r2.hektor_couple_contact_id = '29999999' then 'ok' else 'FAUX' end;
  t := t || ' | 12 droits=' || case when not has_function_privilege('anon', 'public.app_contact_creer_conjoint(jsonb,text,text,text)', 'EXECUTE')
                                     and not has_function_privilege('authenticated', 'public.app_contact_creer_conjoint(jsonb,text,text,text)', 'EXECUTE')
                                    then 'ok' else 'OUVERTS' end;
  t := t || ' | 13 autres_resumes=' || (select count(*) from public.app_contact_current
                                        where couple_json is not null and hektor_contact_id <> '29999999');
  RAISE EXCEPTION 'ESSAI ANNULE --%', t;
END
$essai$;

ROLLBACK;
