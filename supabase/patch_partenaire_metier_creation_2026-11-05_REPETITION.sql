-- ═══════════════════════════════════════════════════════════════════════════
-- RÉPÉTITION DE D-1 — le métier choisi à la création entre au registre — TOUT EST ANNULÉ      05/11/2026
-- Se termine VOLONTAIREMENT par « ESSAI ANNULE -- … ».
-- Elle pose LE VRAI PATCH, joue les essais sur de faux travaux (statut « error », numéros 2999990x / 2999993x qui
-- n'existent pas), puis LE VRAI RETOUR ARRIÈRE. Rien ne reste : ni objet, ni interrupteur, ni travail, ni ligne.
-- Fichier GÉNÉRÉ depuis le patch et l'inverse (gen_repetition_d1.py) : ne pas le retoucher à la main.
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

DO $garde$
BEGIN
    IF to_regclass('public.app_partenaire_metier') IS NULL OR to_regclass('public.app_console_job') IS NULL THEN
        RAISE EXCEPTION '%', 'ARRET : app_partenaire_metier ou app_console_job absente. Rien n''est ecrit.';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_partenaire_metier_a_la_creation_trg') THEN
        RAISE EXCEPTION '%', 'ARRET : le declencheur app_partenaire_metier_a_la_creation_trg existe deja. Rien n''est ecrit.';
    END IF;
    IF to_regprocedure('public.app_partenaire_metier_a_la_creation_trg()') IS NOT NULL THEN
        RAISE EXCEPTION '%', 'ARRET : la fonction app_partenaire_metier_a_la_creation_trg existe deja. Rien n''est ecrit.';
    END IF;
    -- Les deux contrôles du registre doivent être ceux du 04/11 soir (notaire et transactions acceptés) :
    -- tous les métiers de la correspondance y sont, et la source « ecran » aussi.
    IF md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'public.app_partenaire_metier'::regclass
             AND conname = 'app_partenaire_metier_metier_check')) <> '0d785740173b478f5379c2f396e2f458'
       OR md5((SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'public.app_partenaire_metier'::regclass
             AND conname = 'app_partenaire_metier_source_check')) <> 'e322ef89ef8f343fe0eae8079d500f9c' THEN
        RAISE EXCEPTION '%', 'ARRET : les controles de app_partenaire_metier ont change depuis le 05/11. Rien n''est ecrit.';
    END IF;
END
$garde$;

-- 0. L'INTERRUPTEUR, ÉTEINT
insert into public.app_setting (key, value, description, updated_at)
values ('partenaire_metier_a_la_creation', 'off',
        'Chantier partenaires D-1 05/11/2026 : on = le metier choisi a la creation d''un partenaire dans l''app entre au registre app_partenaire_metier (source ecran), dans la meme transaction (voir supabase/patch_partenaire_metier_creation_2026-11-05.sql). off = comportement d''avant (le metier n''arrive nulle part chez nous).',
        now())
on conflict (key) do nothing;

-- 1. LA FONCTION DU DÉCLENCHEUR
create function public.app_partenaire_metier_a_la_creation_trg()
returns trigger
language plpgsql
security definer
set search_path to 'public'
as $fonction$
declare
  v_on      boolean;
  v_code    text;
  v_contact text;
  v_metier  text;
begin
  select lower(trim(coalesce(st.value, ''))) in ('on', '1', 'true', 'oui') into v_on
    from public.app_setting st where st.key = 'partenaire_metier_a_la_creation';
  if not coalesce(v_on, false) then return null; end if;
  begin
    if lower(trim(coalesce(new.payload_json->>'contact_kind', ''))) <> 'partenaire' then return null; end if;
    v_code := nullif(trim(coalesce(new.payload_json->>'partner_job_id', '')), '');
    v_contact := nullif(trim(coalesce(new.payload_json->>'app_identite', '')), '');
    if v_code is null or v_contact is null then return null; end if;
    -- La correspondance de la nuit (METIER_HEKTOR) + 2 notaire, 6 autre. 7 et 16 : rien.
    v_metier := case v_code
      when '1' then 'promoteur'      when '2' then 'notaire'        when '3' then 'agent_immobilier'
      when '4' then 'diagnostiqueur' when '5' then 'syndic'         when '6' then 'autre'
      when '8' then 'societe'        when '15' then 'apporteur'     when '17' then 'administration'
      when '18' then 'societe'       when '19' then 'banque'        when '20' then 'mandataire'
      when '21' then 'autre'         when '22' then 'agent_immobilier' when '23' then 'technicien'
      else null end;
    if v_metier is null then return null; end if;
    insert into public.app_partenaire_metier (contact_id, metier, source, confirme_le, confirme_par, ecrit_par)
    select v_contact, v_metier, 'ecran', now(), new.requested_by, new.requested_by
     where not exists (select 1 from public.app_partenaire_metier m
                        where m.contact_id = v_contact and m.metier = v_metier and m.retire_le is null);
  exception when others then
    raise warning 'partenaire_metier_a_la_creation : metier non ecrit pour le travail % (%)', new.id, sqlerrm;
  end;
  return null;
end
$fonction$;

revoke all on function public.app_partenaire_metier_a_la_creation_trg() from public, anon, authenticated;

-- 2. LE DÉCLENCHEUR : seulement à l'insertion d'un travail de création de contact
create trigger app_partenaire_metier_a_la_creation_trg
  after insert on public.app_console_job
  for each row
  when (new.job_type = 'create_hektor_contact')
  execute function public.app_partenaire_metier_a_la_creation_trg();

-- ═══ LES ESSAIS (faux travaux au statut « error » : aucun worker ne les prend, et tout est annulé) ═══
create temp table _m (n int, nom text, ok boolean, detail text) on commit drop;

create or replace function pg_temp.travail(p_type text, p_kind text, p_code text, p_ident text) returns void
language sql as $f$
  insert into public.app_console_job (job_type, status, payload_json)
  values (p_type, 'error', jsonb_strip_nulls(jsonb_build_object('contact_kind', p_kind, 'partner_job_id', p_code, 'app_identite', p_ident)));
$f$;
create or replace function pg_temp.metiers(p_ident text) returns text language sql as $f$
  select coalesce(string_agg(metier || '/' || source, ',' order by metier), '') from public.app_partenaire_metier
   where contact_id = p_ident and retire_le is null;
$f$;

DO $e$
DECLARE r text; n_jobs_avant bigint; n_jobs_apres bigint; c record;
BEGIN
  SELECT count(*) INTO n_jobs_avant FROM public.app_console_job;
  -- 1. ÉTEINT : rien n'est écrit
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '5', '29999901');
  r := pg_temp.metiers('29999901');
  INSERT INTO _m VALUES (1, 'TEMOIN eteint : rien au registre', r = '', r);

  UPDATE public.app_setting SET value = 'on' WHERE key = 'partenaire_metier_a_la_creation';

  -- 2. ALLUMÉ : un syndic
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '5', '29999902');
  r := pg_temp.metiers('29999902');
  INSERT INTO _m VALUES (2, 'allume : code 5 = syndic, source ecran', r = 'syndic/ecran', r);
  -- 3. pas de doublon
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '5', '29999902');
  r := pg_temp.metiers('29999902');
  INSERT INTO _m VALUES (3, 'le meme metier une 2e fois : pas de doublon', r = 'syndic/ecran', r);
  -- 4. un second métier pour le même contact
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '4', '29999902');
  r := pg_temp.metiers('29999902');
  INSERT INTO _m VALUES (4, 'un 2e metier s''ajoute', r = 'diagnostiqueur/ecran,syndic/ecran', r);
  -- 5. Collaborateur, À supprimer, code inconnu : rien
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '7', '29999903');
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '16', '29999903');
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '99', '29999903');
  r := pg_temp.metiers('29999903');
  INSERT INTO _m VALUES (5, '7, 16 et un code inconnu : rien', r = '', r);
  -- 6. pas un partenaire : rien
  PERFORM pg_temp.travail('create_hektor_contact', 'acquereur', '5', '29999904');
  PERFORM pg_temp.travail('create_hektor_contact', NULL, '5', '29999904');
  r := pg_temp.metiers('29999904');
  INSERT INTO _m VALUES (6, 'acquereur ou sans type : rien', r = '', r);
  -- 7. une MODIFICATION ne déclenche rien
  PERFORM pg_temp.travail('update_hektor_contact', 'partenaire', '5', '29999905');
  r := pg_temp.metiers('29999905');
  INSERT INTO _m VALUES (7, 'un travail update_hektor_contact : rien', r = '', r);
  -- 8. sans notre numéro ou sans métier : rien
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '5', NULL);
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', NULL, '29999906');
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '', '29999906');
  r := pg_temp.metiers('29999906');
  INSERT INTO _m VALUES (8, 'sans numero ou sans metier : rien', r = '', r);
  -- 9. toute la correspondance, code par code
  FOR c IN SELECT * FROM (VALUES ('1','promoteur'),('2','notaire'),('3','agent_immobilier'),('6','autre'),('8','societe'),
           ('15','apporteur'),('17','administration'),('18','societe'),('19','banque'),('20','mandataire'),('21','autre'),
           ('22','agent_immobilier'),('23','technicien')) v(code, metier) LOOP
    PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', c.code, '2999993' || c.code);
    r := pg_temp.metiers('2999993' || c.code);
    INSERT INTO _m VALUES (9, 'code ' || c.code || ' = ' || c.metier, r = c.metier || '/ecran', r);
  END LOOP;
  -- 10. le travail lui-même est toujours créé (le déclencheur ne bloque jamais)
  SELECT count(*) INTO n_jobs_apres FROM public.app_console_job;
  INSERT INTO _m VALUES (10, 'tous les travaux sont crees (26)', n_jobs_apres - n_jobs_avant = 26, (n_jobs_apres - n_jobs_avant)::text);
  -- 11. une erreur dans le déclencheur ne bloque pas la création (registre forcé à refuser ce numéro)
  ALTER TABLE public.app_partenaire_metier ADD CONSTRAINT _essai_refus CHECK (contact_id <> '29999907') NOT VALID;
  PERFORM pg_temp.travail('create_hektor_contact', 'partenaire', '5', '29999907');
  r := pg_temp.metiers('29999907');
  SELECT count(*) INTO n_jobs_apres FROM public.app_console_job;
  INSERT INTO _m VALUES (11, 'registre qui refuse : le travail est cree quand meme', r = '' AND n_jobs_apres - n_jobs_avant = 27, r || ' / ' || (n_jobs_apres - n_jobs_avant));
  ALTER TABLE public.app_partenaire_metier DROP CONSTRAINT _essai_refus;
  -- 12. la grosse fonction de création n'est pas touchée
  INSERT INTO _m VALUES (12, 'app_create_contact_optimistic intacte',
    (SELECT md5(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
      WHERE n.nspname = 'public' AND p.proname = 'app_create_contact_optimistic') = '278d5570a49ad377880d08773b7bc216', NULL);
  -- 13. la fonction n'est pas appelable par les clés de l'app
  INSERT INTO _m VALUES (13, 'fonction fermee a anon et authenticated',
    NOT has_function_privilege('anon', 'public.app_partenaire_metier_a_la_creation_trg()', 'EXECUTE')
    AND NOT has_function_privilege('authenticated', 'public.app_partenaire_metier_a_la_creation_trg()', 'EXECUTE'), NULL);
END
$e$;

-- ═══ LE VRAI RETOUR ARRIÈRE ═══

drop trigger if exists app_partenaire_metier_a_la_creation_trg on public.app_console_job;
drop function if exists public.app_partenaire_metier_a_la_creation_trg();
delete from public.app_setting where key = 'partenaire_metier_a_la_creation';

DO $verif$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_partenaire_metier_a_la_creation_trg')
       OR to_regprocedure('public.app_partenaire_metier_a_la_creation_trg()') IS NOT NULL
       OR EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'partenaire_metier_a_la_creation') THEN
        RAISE EXCEPTION '%', 'ARRET : une trace du patch reste ; tout est annule.';
    END IF;
    IF (SELECT count(*) FROM pg_trigger WHERE tgrelid = 'public.app_console_job'::regclass
         AND tgname IN ('app_annonce_saisie_modif_job_trg', 'app_contact_saisie_modif_job_trg')) <> 2 THEN
        RAISE EXCEPTION '%', 'ARRET : un declencheur voisin de app_console_job a disparu ; tout est annule.';
    END IF;
    RAISE NOTICE '%', 'Retour fait : declencheur, fonction et interrupteur retires ; les lignes du registre deja ecrites restent.';
END
$verif$;

-- ═══ APRÈS LE RETOUR ARRIÈRE ═══
DO $f$
DECLARE echecs text; total int; verts int;
BEGIN
  INSERT INTO _m VALUES (14, 'retour arriere : plus de declencheur, de fonction ni d''interrupteur',
    NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'app_partenaire_metier_a_la_creation_trg')
    AND to_regprocedure('public.app_partenaire_metier_a_la_creation_trg()') IS NULL
    AND NOT EXISTS (SELECT 1 FROM public.app_setting WHERE key = 'partenaire_metier_a_la_creation'), NULL);
  SELECT count(*), count(*) FILTER (WHERE ok),
         string_agg(n || ' ' || nom || ' [' || coalesce(detail, '') || ']', ' | ' ORDER BY n) FILTER (WHERE NOT coalesce(ok, false))
    INTO total, verts, echecs FROM _m;
  IF echecs IS NOT NULL THEN
    RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s / %s verts. ECHECS : %s', verts, total, echecs);
  END IF;
  RAISE EXCEPTION '%', format('ESSAI ANNULE -- %s / %s essais verts, rien n''est garde.', verts, total);
END
$f$;

ROLLBACK;
