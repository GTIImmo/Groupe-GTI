-- ═══════════════════════════════════════════════════════════════════════════
-- COUPLES · P2 — LA PREMIÈRE FICHE CONNAÎT SON CONJOINT              31/10/2026
-- ═══════════════════════════════════════════════════════════════════════════
-- A APPLIQUER PAR FREDERIC dans l'éditeur SQL Supabase, APRES la répétition.
-- Note : notice/COUPLES_ERGONOMIE_ET_ECRITURE_PROPOSITION_2026-10-30.md §21 et §23.
--
-- CE QUE FAIT CE PATCH — ADDITIF :
--   1. une colonne NEUVE app_contact_current.couple_json (jsonb, vide) : le résumé
--      du conjoint, posé sur la première fiche d'un couple par la nuit
--      (phase2/contacts/conjoints_des_couples.py) :
--        {"etat": "nomme"|"vide"|"aucun", "autres": n,
--         "conjoint": {"id","hektor_id","civilite","prenom","nom","telephone",
--                      "email","archive","envoye"}}
--   2. la clé de battement de l'étape de nuit « phase2 conjoints des couples »
--      (une clé sans ligne part dans le vide, leçon du 13/10) ;
--   3. app_contact_creer_conjoint (pièce A du 31/10) pose LA MÊME CHOSE TOUT DE
--      SUITE quand un couple naît dans l'app : couple_json sur la personne 1,
--      couple_role 'conjoint' sur la personne 2. La nuit confirme.
--
-- CE QU'IL NE FAIT PAS : la vue app_contacts_current n'est PAS touchée (l'écran
-- lira la colonne en P3) ; rien chez Hektor ; aucune ligne existante modifiée.
--
-- ⛔ ORDRE DES GESTES :
--   a. coller ce patch ;
--   b. SEULEMENT APRES : APP_COUPLE_CONJOINT=1 dans C:\Hektor\Projet\.env
--      (sans la colonne, le push des contacts échouerait) ;
--   c. la nuit suivante pose les résumés et les envoie (~26 000 lignes une fois).
-- ⛔ GARDES : la fonction n'est modifiée que si son empreinte est celle relevée le
--    31/10 (2523f1f0…), si le bloc n'y est pas déjà, et si l'ancre y est UNE fois.
-- RETOUR ARRIÈRE : supabase/patch_couple_p2_conjoint_connu_2026-10-31_INVERSE.sql
--    (éteindre APP_COUPLE_CONJOINT D'ABORD).
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- 1. LA COLONNE
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

COMMIT;

-- CONTROLE (lecture seule)
select
  (select count(*) from information_schema.columns
    where table_schema = 'public' and table_name = 'app_contact_current' and column_name = 'couple_json') as colonne,
  (select count(*) from public.app_worker_registry where worker_key = 'phase2.conjoints_couples') as battement,
  position('COUPLES · P2' in pg_get_functiondef('public.app_contact_creer_conjoint(jsonb,text,text,text)'::regprocedure)) > 0 as bloc_pose,
  (select count(*) from public.app_contact_current where couple_json is not null) as resumes_avant_la_nuit;
